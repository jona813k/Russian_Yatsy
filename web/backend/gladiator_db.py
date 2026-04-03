"""
Gladiator Showdown — SQLite persistence layer.

Tables:
  characters  — one row per eligible run (victory + gladiator key).
                wins_achieved is NULL while the showdown is in progress,
                and is set to the final win count when the run ends.

The leaderboard is simply: SELECT * FROM characters WHERE wins_achieved IS NOT NULL
ordered by wins DESC.
"""
import json
import os
import random
import sqlite3
from pathlib import Path

_DATA_DIR = Path(os.environ.get('DATA_DIR', Path(__file__).parent))
DB_PATH = _DATA_DIR / 'gladiator.db'

MIN_POOL_SIZE = 10   # showdown is locked until this many characters are in the DB


def _connect() -> sqlite3.Connection:
    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    with _connect() as conn:
        conn.execute('''
            CREATE TABLE IF NOT EXISTS characters (
                id              INTEGER PRIMARY KEY AUTOINCREMENT,
                name            TEXT    NOT NULL,
                run_id          TEXT    UNIQUE NOT NULL,
                timestamp       TEXT    NOT NULL,
                stats_json      TEXT    NOT NULL,
                items_json      TEXT    NOT NULL,
                wins_achieved   INTEGER
            )
        ''')
        conn.commit()


# ---------------------------------------------------------------------------
# Write helpers
# ---------------------------------------------------------------------------

def save_character(name: str, run_id: str, timestamp: str,
                   stats: dict, items: list) -> int:
    """
    Insert a character row (wins_achieved = NULL = showdown in progress).
    Returns the row id, or the existing id if run_id already exists.
    """
    with _connect() as conn:
        cur = conn.execute(
            '''INSERT OR IGNORE INTO characters
               (name, run_id, timestamp, stats_json, items_json, wins_achieved)
               VALUES (?, ?, ?, ?, ?, NULL)''',
            (name, run_id, timestamp, json.dumps(stats), json.dumps(items)),
        )
        conn.commit()
        if cur.lastrowid:
            return cur.lastrowid
        row = conn.execute(
            'SELECT id FROM characters WHERE run_id = ?', (run_id,)
        ).fetchone()
        return row['id'] if row else None


def save_character_to_pool(name: str, run_id: str, timestamp: str,
                           stats: dict, items: list) -> int:
    """
    Insert a character with wins_achieved = 0 so they immediately count
    toward the showdown pool and are available as tier-0 opponents.
    Uses INSERT OR IGNORE so calling this twice for the same run_id is safe.
    Returns the row id.
    """
    with _connect() as conn:
        cur = conn.execute(
            '''INSERT OR IGNORE INTO characters
               (name, run_id, timestamp, stats_json, items_json, wins_achieved)
               VALUES (?, ?, ?, ?, ?, 0)''',
            (name, run_id, timestamp, json.dumps(stats), json.dumps(items)),
        )
        conn.commit()
        if cur.lastrowid:
            return cur.lastrowid
        row = conn.execute(
            'SELECT id FROM characters WHERE run_id = ?', (run_id,)
        ).fetchone()
        return row['id'] if row else None


def update_wins(character_id: int, wins: int):
    """Record the final win count once the showdown is complete."""
    with _connect() as conn:
        conn.execute(
            'UPDATE characters SET wins_achieved = ? WHERE id = ?',
            (wins, character_id),
        )
        conn.commit()


# ---------------------------------------------------------------------------
# Read helpers
# ---------------------------------------------------------------------------

def completed_character_count() -> int:
    """Number of characters whose showdown has fully resolved."""
    with _connect() as conn:
        row = conn.execute(
            'SELECT COUNT(*) AS c FROM characters WHERE wins_achieved IS NOT NULL'
        ).fetchone()
        return row['c']


def is_showdown_active() -> bool:
    return completed_character_count() >= MIN_POOL_SIZE


def get_opponents_for_tier(tier: int, exclude_run_id: str,
                           already_used_ids: list[int]) -> list[dict]:
    """
    Return exactly 3 opponent character dicts for the given tier
    (wins_achieved == tier), excluding the current player's own run.

    Preference order:
      1. Characters not yet used this gauntlet run
      2. If the preferred pool has < 3, re-use opponents (random pick with replacement)

    Returns [] only if there are zero eligible opponents at this tier.
    """
    with _connect() as conn:
        rows = conn.execute(
            '''SELECT * FROM characters
               WHERE wins_achieved = ? AND run_id != ?''',
            (tier, exclude_run_id),
        ).fetchall()

    pool = [dict(r) for r in rows]
    if not pool:
        return []

    preferred = [c for c in pool if c['id'] not in already_used_ids]
    draw_from = preferred if preferred else pool

    result: list[dict] = []
    while len(result) < 3:
        remaining_unused = [c for c in draw_from if c not in result]
        if remaining_unused:
            result.append(random.choice(remaining_unused))
        else:
            # Must allow a repeat
            result.append(random.choice(draw_from))

    return result


def get_leaderboard() -> list[dict]:
    with _connect() as conn:
        rows = conn.execute(
            '''SELECT name, wins_achieved, timestamp
               FROM characters
               WHERE wins_achieved IS NOT NULL
               ORDER BY wins_achieved DESC, timestamp ASC'''
        ).fetchall()
    return [dict(r) for r in rows]


# ---------------------------------------------------------------------------
# Combat adapter
# ---------------------------------------------------------------------------

def player_stats_to_enemy(stats: dict, name: str) -> dict:
    """
    Convert a stored PlayerStats dict to the enemy dict format that
    simulate_combat() expects.

    Note: block_chance, crit_chance, dark_level, spell_level, and summon_level
    are not supported on the enemy side of simulate_combat — the opponent's
    final stat values (hp, atk, speed, armor, lifesteal) represent the net
    result of those investments.
    """
    speed = round(1.0 / max(0.05, stats.get('attack_speed', 0.5)), 4)
    return {
        'name':      name,
        'hp':        stats.get('max_hp', 100),
        'speed':     speed,
        'attack':    stats.get('attack_dmg', 8),
        'armor':     stats.get('armor', 0.05),
        'lifesteal': stats.get('lifesteal', 0.0),
        'regen':     0,
        'is_boss':   False,
    }


# Initialise on import
init_db()
