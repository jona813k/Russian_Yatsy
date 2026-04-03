"""
Russian Yatzy — FastAPI backend

Endpoints (all JSON):
  POST /api/game/new          Start a new game session
  POST /api/game/{id}/roll    Roll dice (start of turn)
  POST /api/game/{id}/select  Select a number to collect
  GET  /api/game/{id}/state   Get current game state
Run locally:
    pip install fastapi uvicorn
    uvicorn web.backend.main:app --reload --port 8000
"""

import sys
from pathlib import Path

# Make src importable
sys.path.insert(0, str(Path(__file__).parent.parent.parent / 'src'))

import os
import uuid
import json
import logging
import asyncio
from datetime import datetime, timezone, timedelta

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)

from src.game.engine import GameEngine
from web.backend.rpg_engine import RPGRun
from web.backend.gladiator_db import (
    save_character, save_character_to_pool, update_wins, is_showdown_active,
    get_opponents_for_tier, get_leaderboard, get_all_characters, player_stats_to_enemy,
    completed_character_count,
)
from web.backend.combat import simulate_combat

# ---------------------------------------------------------------------------
# Run history — persisted to JSON so it survives server restarts
# ---------------------------------------------------------------------------

_DATA_DIR = Path(os.environ.get('DATA_DIR', Path(__file__).parent))
_DATA_DIR.mkdir(parents=True, exist_ok=True)
HISTORY_FILE = _DATA_DIR / 'run_history.json'

def load_history() -> list:
    if HISTORY_FILE.exists():
        try:
            return json.loads(HISTORY_FILE.read_text(encoding='utf-8'))
        except json.JSONDecodeError as e:
            logger.error(f"Corrupted history file: {e}")
            return []
        except OSError as e:
            logger.error(f"Could not read history file: {e}")
            return []
    return []

def save_to_history(summary: dict):
    history = load_history()
    history.insert(0, summary)   # newest first
    HISTORY_FILE.write_text(json.dumps(history, indent=2), encoding='utf-8')

app = FastAPI(title="Russian Yatzy API", version="1.0")

# CORS: in production set ALLOWED_ORIGINS to your frontend domain.
# In development the default "*" keeps things frictionless.
_raw_origins = os.environ.get("ALLOWED_ORIGINS", "*")
allowed_origins = [o.strip() for o in _raw_origins.split(",")] if _raw_origins != "*" else ["*"]

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_methods=["GET", "POST", "DELETE"],
    allow_headers=["Content-Type"],
)

@app.on_event("startup")
async def startup():
    asyncio.create_task(_cleanup_loop())

# ---------------------------------------------------------------------------
# In-memory session store with timestamps for expiry cleanup
# ---------------------------------------------------------------------------

SESSION_TTL = timedelta(hours=2)   # idle sessions expire after 2 hours

sessions:       dict[str, tuple[GameEngine, datetime]] = {}
rpg_runs:       dict[str, tuple[RPGRun,       datetime]] = {}
gauntlet_sessions: dict[str, dict] = {}   # gauntlet_id → gauntlet state dict


async def _cleanup_loop():
    """Background task: remove sessions/runs idle longer than SESSION_TTL."""
    while True:
        await asyncio.sleep(300)  # run every 5 minutes
        cutoff = datetime.now(timezone.utc) - SESSION_TTL
        expired_s = [k for k, (_, t) in sessions.items() if t < cutoff]
        expired_r = [k for k, (_, t) in rpg_runs.items()  if t < cutoff]
        for k in expired_s:
            del sessions[k]
        for k in expired_r:
            del rpg_runs[k]
        if expired_s or expired_r:
            logger.info(f"Cleaned up {len(expired_s)} sessions, {len(expired_r)} runs")

def _now() -> datetime:
    return datetime.now(timezone.utc)

def get_session(session_id: str) -> GameEngine:
    if session_id not in sessions:
        raise HTTPException(status_code=404, detail="Session not found")
    engine, _ = sessions[session_id]
    sessions[session_id] = (engine, _now())  # refresh TTL on access
    return engine

def compute_dice_groups(engine: GameEngine) -> dict:
    """
    For each legal number, return ALL die indices that could potentially
    contribute to collecting that number.

    A die is included if:
      - Its face value equals the number (single, 1-6 only), OR
      - It can form a pair with ANY other die that sums to the number

    Deliberately NOT greedy: all three 3s are candidates for number 4 (via 3+1)
    even though only one 3+1 pair can actually be collected. This prevents valid
    dice from being wrongly greyed out in the UI.
    """
    dice = list(engine.state.dice_values)
    groups = {}

    for action in engine.get_legal_actions():
        if action['type'] == 'skip_turn':
            continue
        n = action['number']
        candidates = set()

        # Singles: all dice showing face value n (any die type, including d12)
        for i, d in enumerate(dice):
            if d == n:
                candidates.add(i)

        # Pairs: include BOTH dice from every valid pair, not just first match
        for i in range(len(dice)):
            for j in range(i + 1, len(dice)):
                if dice[i] + dice[j] == n:
                    candidates.add(i)
                    candidates.add(j)

        groups[str(n)] = sorted(candidates)

    return groups


def engine_to_state(engine: GameEngine) -> dict:
    """Serialise engine state to a JSON-safe dict the frontend can render."""
    info = engine.get_game_info()
    return {
        "session_id": None,
        "dice": list(engine.state.dice_values),
        "num_dice_in_hand": engine.state.num_dice_in_hand,
        "selected_number": engine.state.selected_number,
        "collected_this_turn": engine.state.collected_this_turn,
        "progress": {str(k): v for k, v in engine.player.progress.items()},
        "completed": info["completed"],
        "turns": info["turns"],
        "is_won": info["is_won"],
        "legal_actions": engine.get_legal_actions(),
        "dice_groups": compute_dice_groups(engine),  # die index → legal numbers mapping
    }

# ---------------------------------------------------------------------------
# Request / response models
# ---------------------------------------------------------------------------

class SelectRequest(BaseModel):
    number: int = Field(..., ge=1, le=12)

# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------

@app.post("/api/game/new")
def new_game():
    """Create a new game session and return the initial state."""
    session_id = str(uuid.uuid4())
    engine = GameEngine()
    engine.reset()
    sessions[session_id] = (engine, _now())

    state = engine_to_state(engine)
    state["session_id"] = session_id
    return state


@app.get("/api/health")
def health():
    return {"status": "ok"}



@app.get("/api/game/{session_id}/state")
def get_state(session_id: str):
    engine = get_session(session_id)
    state = engine_to_state(engine)
    state["session_id"] = session_id
    return state


@app.post("/api/game/{session_id}/select")
def select_number(session_id: str, body: SelectRequest):
    """
    Player selects which number to collect on this roll.
    The engine automatically collects all matching dice and rolls the rest.
    """
    engine = get_session(session_id)

    legal = engine.get_legal_actions()
    legal_numbers = [a["number"] for a in legal if a["type"] in ("select", "collect")]
    if body.number not in legal_numbers:
        raise HTTPException(status_code=400, detail=f"{body.number} is not a legal move right now")

    action = next(a for a in legal if a.get("number") == body.number)
    result = engine.execute_action(action)

    state = engine_to_state(engine)
    state["session_id"] = session_id
    state["result"] = result  # includes reward, state label (continue/won/turn_end…)
    return state


@app.post("/api/game/{session_id}/skip")
def skip_turn(session_id: str):
    """
    Execute a skip_turn action — used when the current dice have no valid
    combinations for any legal number. The engine re-rolls all 6 dice.
    """
    engine = get_session(session_id)
    legal = engine.get_legal_actions()
    skip_action = next((a for a in legal if a['type'] == 'skip_turn'), None)
    if not skip_action:
        raise HTTPException(status_code=400, detail="No skip available right now")
    result = engine.execute_action(skip_action)
    state = engine_to_state(engine)
    state["session_id"] = session_id
    state["result"] = result
    return state


# ---------------------------------------------------------------------------
# RPG helpers
# ---------------------------------------------------------------------------

def get_run(run_id: str) -> RPGRun:
    if run_id not in rpg_runs:
        raise HTTPException(status_code=404, detail="Run not found")
    run, _ = rpg_runs[run_id]
    rpg_runs[run_id] = (run, _now())  # refresh TTL on access
    return run


def build_dice_types(run) -> list:
    """Return die-type strings for the current dice in hand from the roller's tracked state."""
    return run._dice_roller.types_in_hand


def build_rpg_state(run: RPGRun) -> dict:
    """Serialise RPGRun to a JSON-safe response, including yatzy state if in upgrade phase."""
    yatzy = None
    if run.phase == 'upgrade' and not run.upgrade_done:
        yatzy = engine_to_state(run.upgrade_engine)
        yatzy['session_id'] = run.run_id
        yatzy['turns_remaining'] = run.upgrade_turns_max - run.upgrade_turns_used
        yatzy['dice_types'] = build_dice_types(run)
    return run.to_dict(yatzy_state=yatzy)


class ItemRequest(BaseModel):
    item_id: str
    use_free: bool = False

class NewRunRequest(BaseModel):
    name: str = 'Anonymous'

class PreGameForgeRequest(BaseModel):
    choice_id: str

class GladiatorFightRequest(BaseModel):
    skip: bool = False


# ---------------------------------------------------------------------------
# RPG routes
# ---------------------------------------------------------------------------

@app.post("/api/rpg/new")
def rpg_new(body: NewRunRequest = None):
    """Start a new RPG run and return the initial state."""
    name = (body.name.strip() or 'Anonymous') if body else 'Anonymous'
    run = RPGRun(name=name)
    run.started_at = datetime.now(timezone.utc).isoformat()
    rpg_runs[run.run_id] = (run, _now())
    return build_rpg_state(run)


@app.get("/api/rpg/{run_id}/state")
def rpg_state(run_id: str):
    return build_rpg_state(get_run(run_id))


@app.post("/api/rpg/{run_id}/upgrade/select")
def rpg_upgrade_select(run_id: str, body: SelectRequest):
    """Select a number to collect during the upgrade phase."""
    run = get_run(run_id)
    if run.phase != 'upgrade' or run.upgrade_done:
        raise HTTPException(status_code=400, detail="Not in upgrade phase")

    engine = run.upgrade_engine
    legal = engine.get_legal_actions()
    if body.number in run.stat_removed:
        raise HTTPException(status_code=400, detail=f"Stat {body.number} has been removed by your specialisation")
    legal_numbers = [a['number'] for a in legal if a['type'] in ('select', 'collect')]
    if body.number not in legal_numbers:
        raise HTTPException(status_code=400, detail=f"{body.number} is not a legal move")

    action = next(a for a in legal if a.get('number') == body.number)
    # Capture bomb die value before collection/re-roll (for auto-stash on turn_end)
    run.note_bomb_die_value()
    # Notify the roller which types survive this collection before the engine re-rolls
    run._dice_roller.prepare_for_collection(engine.state.dice_values, body.number)
    # If the bomb die was consumed by this collection, cancel the pending stash
    if 'bomb' not in run._dice_roller.types_in_hand:
        run._bomb_stash_pending = None
    result = engine.execute_action(action)
    run.handle_action_result(result)

    state = build_rpg_state(run)
    state['action_result'] = result
    return state


@app.post("/api/rpg/{run_id}/upgrade/skip")
def rpg_upgrade_skip(run_id: str):
    """Skip when no valid combinations exist during upgrade phase."""
    run = get_run(run_id)
    if run.phase != 'upgrade' or run.upgrade_done:
        raise HTTPException(status_code=400, detail="Not in upgrade phase")

    engine = run.upgrade_engine
    legal = engine.get_legal_actions()
    skip = next((a for a in legal if a['type'] == 'skip_turn'), None)
    if not skip:
        raise HTTPException(status_code=400, detail="No skip available")

    # Capture bomb die value before the turn ends (skip always causes turn_end)
    run.note_bomb_die_value()
    result = engine.execute_action(skip)
    run.handle_action_result(result)

    state = build_rpg_state(run)
    state['action_result'] = result
    return state


@app.post("/api/rpg/{run_id}/upgrade/reroll")
def rpg_upgrade_reroll(run_id: str):
    """Free reroll — re-rolls all dice without costing a turn. Requires free_reroll forge."""
    run = get_run(run_id)
    if run.phase != 'upgrade':
        raise HTTPException(status_code=400, detail="Not in upgrade phase")
    if not run.use_free_reroll():
        raise HTTPException(status_code=400, detail="Free reroll not available")
    state = build_rpg_state(run)
    return state


@app.post("/api/rpg/{run_id}/upgrade/retry-reroll")
def rpg_upgrade_retry_reroll(run_id: str):
    """Retry die reroll — rerolls only the retry die without costing a turn. Once per turn."""
    run = get_run(run_id)
    if run.phase != 'upgrade':
        raise HTTPException(status_code=400, detail="Not in upgrade phase")
    if not run.use_retry_die_reroll():
        raise HTTPException(status_code=400, detail="Retry die reroll not available")
    state = build_rpg_state(run)
    return state


@app.post("/api/rpg/{run_id}/upgrade/finish")
def rpg_upgrade_finish(run_id: str):
    """Apply upgrades and move to combat phase. Only valid when upgrade_done is True."""
    run = get_run(run_id)
    if run.phase != 'upgrade' or not run.upgrade_done:
        raise HTTPException(status_code=400, detail="Upgrade phase not done yet")

    upgrades = run.finish_upgrade()
    state = build_rpg_state(run)
    state['upgrades_applied'] = upgrades
    return state


@app.post("/api/rpg/{run_id}/combat/start")
def rpg_combat_start(run_id: str):
    """Simulate the combat and return events for animation. Idempotent — safe to call twice."""
    run = get_run(run_id)
    if run.phase == 'combat':
        combat = run.run_combat()
        # Save history when the run reaches a terminal state
        if run.phase in ('game_over', 'victory'):
            save_to_history(run.to_summary())
            if run.phase == 'victory':
                timestamp = run.started_at or datetime.now(timezone.utc).isoformat()
                save_character_to_pool(
                    name=run.name,
                    run_id=run_id,
                    timestamp=timestamp,
                    stats=run.player.to_dict(),
                    items=[i['id'] for i in run.owned_items],
                )
    elif run.last_combat is not None:
        combat = run.last_combat
    else:
        raise HTTPException(status_code=400, detail="Not in combat phase")

    state = build_rpg_state(run)
    state['combat'] = combat
    return state


@app.post("/api/rpg/{run_id}/shop/buy")
def rpg_shop_buy(run_id: str, body: ItemRequest):
    """Buy an item from the shop (regular or pre-boss)."""
    run = get_run(run_id)
    if run.phase not in ('shop', 'pre_boss_shop'):
        raise HTTPException(status_code=400, detail="Not in shop phase")

    ok, reason = run.buy_item(body.item_id, use_free=body.use_free)
    if not ok:
        raise HTTPException(status_code=400, detail=reason)
    return build_rpg_state(run)


@app.post("/api/rpg/{run_id}/shop/reroll")
def rpg_shop_reroll(run_id: str):
    """Spend 30g to refresh the shop items."""
    run = get_run(run_id)
    if run.phase not in ('shop', 'pre_boss_shop'):
        raise HTTPException(status_code=400, detail="Not in shop phase")
    ok, reason = run.reroll_shop()
    if not ok:
        raise HTTPException(status_code=400, detail=reason)
    return build_rpg_state(run)


@app.post("/api/rpg/{run_id}/shop/close")
def rpg_shop_close(run_id: str):
    """Leave the shop."""
    run = get_run(run_id)
    if run.phase not in ('shop', 'pre_boss_shop'):
        raise HTTPException(status_code=400, detail="Not in shop phase")
    run.close_shop()
    return build_rpg_state(run)


class ForgeRequest(BaseModel):
    choice_id: str


@app.post("/api/rpg/{run_id}/pre_game_forge/pick")
def rpg_pre_game_forge_pick(run_id: str, body: PreGameForgeRequest):
    """Pick a pre-game forge specialisation before the first enemy."""
    run = get_run(run_id)
    if run.phase != 'pre_game_forge':
        raise HTTPException(status_code=400, detail="Not in pre-game forge phase")
    ok, reason = run.pick_pre_game_forge(body.choice_id)
    if not ok:
        raise HTTPException(status_code=400, detail=reason)
    return build_rpg_state(run)


@app.post("/api/rpg/{run_id}/forge/pick")
def rpg_forge_pick(run_id: str, body: ForgeRequest):
    """Pick a forge upgrade after defeating a boss."""
    run = get_run(run_id)
    if run.phase != 'forge':
        raise HTTPException(status_code=400, detail="Not in forge phase")
    ok, reason = run.pick_forge(body.choice_id)
    if not ok:
        raise HTTPException(status_code=400, detail=reason)
    return build_rpg_state(run)


@app.get("/api/rpg/history")
def rpg_history():
    """Return all saved run summaries, newest first."""
    return load_history()


@app.delete("/api/rpg/history")
def rpg_history_clear():
    """Wipe all run history."""
    HISTORY_FILE.write_text('[]', encoding='utf-8')
    return {'cleared': True}


# ---------------------------------------------------------------------------
# Gladiator Showdown routes
# ---------------------------------------------------------------------------

def _build_gauntlet_response(g: dict, combat: dict | None = None) -> dict:
    """Serialise gauntlet session to a JSON-safe dict."""
    next_opp = None
    if g['status'] == 'active' and g['fight_in_tier'] < 3:
        opp = g['opponents'][g['fight_in_tier']]
        next_opp = {
            'name':  opp['name'],
            'stats': _safe_stats(opp),
        }
    resp = {
        'gauntlet_id':    g['gauntlet_id'],
        'player_name':    g['player_name'],
        'current_wins':   g['current_wins'],
        'fight_in_tier':  g['fight_in_tier'],
        'wins_in_tier':   g['wins_in_tier'],
        'status':         g['status'],
        'final_wins':     g['final_wins'],
        'next_opponent':  next_opp,
    }
    if combat is not None:
        resp['combat'] = combat
    return resp


def _safe_stats(char: dict) -> dict:
    """Return a summary of the opponent's key stats for display."""
    import json as _json
    stats = _json.loads(char['stats_json'])
    return {
        'max_hp':       stats.get('max_hp', 0),
        'attack_dmg':   stats.get('attack_dmg', 0),
        'attack_speed': round(stats.get('attack_speed', 0.5), 2),
        'armor':        round(stats.get('armor', 0) * 100),
        'crit_chance':  round(stats.get('crit_chance', 0) * 100),
        'lifesteal':    round(stats.get('lifesteal', 0) * 100),
        'dark_level':   stats.get('dark_level', 0),
        'summon_level': stats.get('summon_level', 0),
        'spell_level':  stats.get('spell_level', 0),
    }


@app.get("/api/gladiator/status")
def gladiator_status():
    """Return whether the showdown is open and how many characters are in the pool."""
    return {
        'active':          is_showdown_active(),
        'character_count': completed_character_count(),
        'required':        10,
    }


@app.get("/api/gladiator/characters")
def gladiator_characters():
    return get_all_characters()


@app.get("/api/gladiator/leaderboard")
def gladiator_leaderboard():
    """Return all leaderboard entries, best wins first."""
    return get_leaderboard()


@app.post("/api/rpg/{run_id}/gladiator/enter")
def gladiator_enter(run_id: str):
    """
    Called when a victorious run with a Gladiator Key wants to enter the showdown.
    Saves the character to the DB, creates a gauntlet session, and returns the first
    opponent.
    """
    run = get_run(run_id)
    if run.phase != 'victory':
        raise HTTPException(status_code=400, detail='Run is not in victory phase')
    if not run.player.has_gladiator_key:
        raise HTTPException(status_code=400, detail='No Gladiator Key')
    if not is_showdown_active():
        raise HTTPException(status_code=400, detail='Showdown not yet active — need 10 completed characters in the pool')

    import json as _json
    timestamp = run.started_at or datetime.now(timezone.utc).isoformat()
    char_id = save_character(
        name=run.name,
        run_id=run_id,
        timestamp=timestamp,
        stats=run.player.to_dict(),
        items=[i['id'] for i in run.owned_items],
    )
    if char_id is None:
        raise HTTPException(status_code=500, detail='Failed to save character')

    opponents = get_opponents_for_tier(tier=0, exclude_run_id=run_id, already_used_ids=[])
    if not opponents:
        raise HTTPException(status_code=400, detail='No opponents available at tier 0')

    gauntlet_id = str(uuid.uuid4())
    g = {
        'gauntlet_id':       gauntlet_id,
        'run_id':            run_id,
        'character_db_id':   char_id,
        'player_stats':      run.player.to_dict(),
        'player_items':      run.owned_items,
        'player_name':       run.name,
        'current_wins':      0,
        'fight_in_tier':     0,
        'wins_in_tier':      0,
        'opponents':         opponents,
        'used_opponent_ids': [o['id'] for o in opponents],
        'status':            'active',
        'final_wins':        None,
    }
    gauntlet_sessions[gauntlet_id] = g
    return _build_gauntlet_response(g)


@app.post("/api/gladiator/{gauntlet_id}/fight")
def gladiator_fight(gauntlet_id: str, body: GladiatorFightRequest = None):
    """
    Simulate the next gladiator fight (or skip it).
    Returns the combat result and updated gauntlet state.
    """
    g = gauntlet_sessions.get(gauntlet_id)
    if g is None:
        raise HTTPException(status_code=404, detail='Gauntlet session not found')
    if g['status'] != 'active':
        raise HTTPException(status_code=400, detail='Gauntlet already complete')
    if g['fight_in_tier'] >= 3:
        raise HTTPException(status_code=400, detail='Tier already complete — call /advance')

    # Build player and opponent
    import json as _json
    from .player import PlayerStats

    raw = g['player_stats']
    player = PlayerStats(**{k: v for k, v in raw.items() if hasattr(PlayerStats, k)})
    player.current_hp = player.max_hp   # full HP each fight

    opponent = g['opponents'][g['fight_in_tier']]
    opp_stats = _json.loads(opponent['stats_json'])
    enemy_dict = player_stats_to_enemy(opp_stats, opponent['name'])

    combat = simulate_combat(player, enemy_dict, g['player_items'])
    if body and body.skip:
        combat['events'] = []   # strip events so frontend skips animation

    # Record result
    won = combat['result'] == 'win'
    g['fight_in_tier'] += 1
    if won:
        g['wins_in_tier'] += 1

    tier_done = g['fight_in_tier'] >= 3
    advancing = tier_done and g['wins_in_tier'] >= 2
    eliminated = tier_done and not advancing

    if tier_done:
        if advancing:
            g['current_wins'] += 1
            new_tier = g['current_wins']
            new_opponents = get_opponents_for_tier(
                tier=new_tier,
                exclude_run_id=g['run_id'],
                already_used_ids=g['used_opponent_ids'],
            )
            if not new_opponents:
                # No opponents at this tier — player wins by default, showdown ends
                g['status'] = 'complete'
                g['final_wins'] = g['current_wins']
                update_wins(g['character_db_id'], g['final_wins'])
            else:
                g['opponents'] = new_opponents
                g['used_opponent_ids'] += [o['id'] for o in new_opponents]
                g['fight_in_tier'] = 0
                g['wins_in_tier'] = 0
        else:
            g['status'] = 'complete'
            g['final_wins'] = g['current_wins']
            update_wins(g['character_db_id'], g['final_wins'])

    resp = _build_gauntlet_response(g, combat=combat)
    resp['tier_done'] = tier_done
    resp['advancing'] = advancing
    resp['eliminated'] = eliminated
    resp['fight_result'] = combat['result']
    resp['opponent_name'] = opponent['name']
    resp['opponent_stats'] = _safe_stats(opponent)
    return resp


# ---------------------------------------------------------------------------
# Serve frontend — must come AFTER all API routes
# ---------------------------------------------------------------------------
_DIST = Path(__file__).parent.parent / 'frontend' / 'dist'

if _DIST.exists():
    app.mount("/assets", StaticFiles(directory=str(_DIST / "assets")), name="assets")

    @app.get("/{full_path:path}")
    def serve_frontend(full_path: str):
        return FileResponse(str(_DIST / "index.html"))
