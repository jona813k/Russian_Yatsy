"""
Russian Yatzy — FastAPI backend

Endpoints (all JSON):
  POST /api/game/new          Start a new game session
  POST /api/game/{id}/roll    Roll dice (start of turn)
  POST /api/game/{id}/select  Select a number to collect
  GET  /api/game/{id}/state   Get current game state
  GET  /api/game/{id}/ai-hint Get AI ranking of all legal moves

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
from typing import Optional

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)

from web.backend.rpg_engine import RPGRun

# MLGameEngine and DQNAgentV2 are only available locally (require src/ and models/).
# Skip gracefully on Railway where neither exists.
try:
    from src.game.ml_engine import MLGameEngine
except ImportError:
    MLGameEngine = None  # type: ignore

_MODEL_PATH = Path(__file__).parent.parent.parent / "models" / "dqn_v2_best.pth"
if _MODEL_PATH.exists():
    try:
        from src.game.dqn_agent_v2 import DQNAgentV2
    except ImportError:
        DQNAgentV2 = None  # type: ignore
else:
    DQNAgentV2 = None  # type: ignore

# ---------------------------------------------------------------------------
# Run history — persisted to JSON so it survives server restarts
# ---------------------------------------------------------------------------

HISTORY_FILE = Path(__file__).parent / 'run_history.json'

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

# ---------------------------------------------------------------------------
# AI model (loaded once at startup)
# ---------------------------------------------------------------------------

ai_agent: Optional[DQNAgentV2] = None

@app.on_event("startup")
async def startup():
    global ai_agent
    if DQNAgentV2 is not None and _MODEL_PATH.exists():
        ai_agent = DQNAgentV2()
        ai_agent.load(str(_MODEL_PATH))
        ai_agent.epsilon = 0.0
        logger.info(f"AI model loaded from {_MODEL_PATH}")
    else:
        logger.info("No AI model found — /ai-hint will return empty.")
    asyncio.create_task(_cleanup_loop())

# ---------------------------------------------------------------------------
# In-memory session store with timestamps for expiry cleanup
# ---------------------------------------------------------------------------

SESSION_TTL = timedelta(hours=2)   # idle sessions expire after 2 hours

sessions:  dict[str, tuple[MLGameEngine, datetime]] = {}
rpg_runs:  dict[str, tuple[RPGRun,       datetime]] = {}


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

def get_session(session_id: str) -> MLGameEngine:
    if session_id not in sessions:
        raise HTTPException(status_code=404, detail="Session not found")
    engine, _ = sessions[session_id]
    sessions[session_id] = (engine, _now())  # refresh TTL on access
    return engine

def compute_dice_groups(engine: MLGameEngine) -> dict:
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


def engine_to_state(engine: MLGameEngine) -> dict:
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
    engine = MLGameEngine()
    engine.reset()
    sessions[session_id] = (engine, _now())

    state = engine_to_state(engine)
    state["session_id"] = session_id
    return state


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


# ---------------------------------------------------------------------------
# RPG routes
# ---------------------------------------------------------------------------

@app.post("/api/rpg/new")
def rpg_new():
    """Start a new RPG run and return the initial state."""
    run = RPGRun()
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
    legal_numbers = [a['number'] for a in legal if a['type'] in ('select', 'collect')]
    if body.number not in legal_numbers:
        raise HTTPException(status_code=400, detail=f"{body.number} is not a legal move")

    action = next(a for a in legal if a.get('number') == body.number)
    # Notify the roller which types survive this collection before the engine re-rolls
    run._dice_roller.prepare_for_collection(engine.state.dice_values, body.number)
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


@app.get("/api/game/{session_id}/ai-hint")
def ai_hint(session_id: str):
    """
    Return all legal moves ranked by the AI's Q-values.

    The frontend uses this to:
      - Show "AI recommends: 8" before the player picks
      - After the player picks, show whether it was optimal
      - Display expected value difference between choices
    """
    engine = get_session(session_id)

    if ai_agent is None:
        return {"available": False, "rankings": []}

    rich_state = engine.get_rich_state()
    legal = engine.get_legal_actions()

    if not legal:
        return {"available": True, "rankings": []}

    rankings = ai_agent.get_action_rankings(rich_state, legal)
    return {
        "available": True,
        "best_number": rankings[0]["number"],
        "rankings": rankings,
    }


# ---------------------------------------------------------------------------
# Health check (used by Railway)
# ---------------------------------------------------------------------------

@app.get("/api/health")
def health():
    return {"status": "ok"}


# ---------------------------------------------------------------------------
# Serve built React frontend (production)
# Mounted last so all /api routes take priority.
# ---------------------------------------------------------------------------

_FRONTEND_DIST = Path(__file__).parent.parent / "frontend" / "dist"

if _FRONTEND_DIST.exists():
    # Serve static assets (JS, CSS, images)
    app.mount("/assets", StaticFiles(directory=_FRONTEND_DIST / "assets"), name="assets")

    # Catch-all: serve index.html for any unmatched route (SPA client-side routing)
    @app.get("/{full_path:path}")
    def spa_fallback(full_path: str):
        return FileResponse(_FRONTEND_DIST / "index.html")
