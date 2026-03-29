"""
RPG layer on top of Russian Yatzy.

The Yatzy game becomes the upgrade phase between fights. Stats map directly
to the 12 numbers. Combat is simulated server-side and returned as an event
list so the frontend can animate it.
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / 'src'))

import uuid
import random
import heapq
from dataclasses import dataclass, asdict
from typing import Optional

from src.game.ml_engine import MLGameEngine
from src.game.rules import GameRules
from src.models.player import Player
from src.models.game_state import GameState


# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

STAT_DEFS = {
    1:  {'attr': 'attack_speed',  'per_die': 0.015, 'threshold': 0.015,  'has_threshold': True},
    2:  {'attr': 'attack_dmg',    'per_die':  1,    'threshold':  1,     'has_threshold': True},
    3:  {'attr': 'crit_chance',   'per_die':  0.01, 'threshold':  0.01,  'has_threshold': True},
    4:  {'attr': 'armor',         'per_die':  0.02, 'threshold':  0.02,  'has_threshold': True},
    5:  {'attr': 'max_hp',        'per_die':  5,    'threshold':  5,     'has_threshold': True},
    6:  {'attr': 'item_slots',    'per_die':  0,    'threshold':  None,  'has_threshold': False, 'special': 'research'},
    7:  {'attr': 'gold',          'per_die':  20,   'threshold':  20,    'has_threshold': True},
    8:  {'attr': 'summon_level',  'per_die':  1,    'threshold':  1,     'has_threshold': True},
    9:  {'attr': 'spell_level',   'per_die':  1,    'threshold':  1,     'has_threshold': True},
    10: {'attr': 'block_chance',  'per_die':  0.02, 'threshold':  0.02,  'has_threshold': True},
    11: {'attr': 'lifesteal',     'per_die':  0.01, 'threshold':  0.01,  'has_threshold': True},
    12: {'attr': 'dark_level',    'per_die':  1,    'threshold':  1,     'has_threshold': True},
}

SUMMON_TIERS = [
    {'min_level':  1, 'name': 'Imp',    'attack':  1, 'speed': 2.0, 'hp':  20},
    {'min_level':  5, 'name': 'Wolf',   'attack':  3, 'speed': 2.0, 'hp':  50},
    {'min_level': 10, 'name': 'Orc',    'attack':  6, 'speed': 2.0, 'hp': 150},
    {'min_level': 15, 'name': 'Wyvern', 'attack': 11, 'speed': 2.0, 'hp': 400},
    {'min_level': 20, 'name': 'Dragon', 'attack': 18, 'speed': 2.0, 'hp': 900},
]

LEVELS = [
    {
        'level': 1,
        'upgrade_turns': 6,
        'enemies': [
            {'name': 'Human Soldier',  'hp': 100, 'attack':  4, 'speed': 1.5, 'is_boss': False},
            {'name': 'Human Soldier',  'hp': 100, 'attack':  4, 'speed': 1.5, 'is_boss': False},
            {'name': 'Bandit Captain', 'hp': 600, 'attack':  8, 'speed': 2.0, 'is_boss': True},
        ],
    },
    {
        'level': 2,
        'upgrade_turns': 5,
        'enemies': [
            {'name': 'Orc Warrior',   'hp': 200, 'attack': 10, 'speed': 2.0, 'is_boss': False},
            {'name': 'Orc Berserker', 'hp': 180, 'attack': 14, 'speed': 1.5, 'is_boss': False},
            {'name': 'Orc Warchief',  'hp': 1200, 'attack': 16, 'speed': 2.0, 'is_boss': True},
        ],
    },
    {
        'level': 3,
        'upgrade_turns': 4,
        'enemies': [
            {'name': 'Dark Knight',  'hp':  350, 'attack': 20, 'speed': 2.0, 'is_boss': False},
            {'name': 'Shadow Mage',  'hp':  280, 'attack': 24, 'speed': 1.5, 'is_boss': False},
            {'name': 'Demon Lord',   'hp': 2000, 'attack': 30, 'speed': 1.8, 'is_boss': True},
        ],
    },
]

SHOP_ITEMS = [
    {
        'id': 'vampiric_tome',
        'name': 'Vampiric Tome',
        'cost': 100,
        'desc': 'Your spell heals you for 30% of its damage.',
    },
    {
        'id': 'thorns_vest',
        'name': 'Thorns Vest',
        'cost': 60,
        'desc': 'When hit, deal 3 damage back to the attacker.',
    },
    {
        'id': 'battle_drum',
        'name': 'Battle Drum',
        'cost': 80,
        'desc': 'Your summon attacks 25% faster.',
    },
    {
        'id': 'focusing_lens',
        'name': 'Focusing Lens',
        'cost': 120,
        'desc': 'Your spell cooldown is reduced from 4s to 2.5s.',
    },
    {
        'id': 'lucky_charm',
        'name': 'Lucky Charm',
        'cost': 70,
        'desc': '+5% critical strike chance during combat.',
    },
    {
        'id': 'iron_gauntlets',
        'name': 'Iron Gauntlets',
        'cost': 80,
        'desc': '+8 attack damage during combat.',
    },
    {
        'id': 'mana_surge',
        'name': 'Mana Surge',
        'cost': 90,
        'desc': 'Your spell deals +10 bonus damage per cast.',
    },
    {
        'id': 'ancient_shield',
        'name': 'Ancient Shield',
        'cost': 70,
        'desc': '+10% damage reduction (armor) during combat.',
    },
    {
        'id': 'battle_horn',
        'name': 'Battle Horn',
        'cost': 100,
        'desc': 'Your attack cooldown is reduced by 0.25s.',
    },
    {
        'id': 'phoenix_feather',
        'name': 'Phoenix Feather',
        'cost': 180,
        'desc': 'Once per fight, survive a killing blow at 1 HP.',
    },
]

# Two fixed forge menus — one per boss beaten (level 1 boss → index 0, level 2 boss → index 1).
FORGE_LEVELS = [
    # ── Forge I  (after Level 1 boss) ──────────────────────────────────────
    [
        {
            'id':   'add_d12',
            'name': 'Add d12',
            'desc': 'Add a 12-sided die to your pool permanently. '
                    'Every future upgrade phase you roll 7 dice — '
                    'the d12 can show any value 1-12, opening paths '
                    'to higher numbers like 7, 8, 9, 10, 11 and 12.',
            'icon': '🎲',
        },
        {
            'id':   'add_d3',
            'name': 'Add d3',
            'desc': 'Add a 3-sided die to your pool permanently. '
                    'It always rolls 1, 2, or 3 — reliable fuel for '
                    'Attack Speed, Attack Damage, and Crit upgrades.',
            'icon': '🟢',
        },
        {
            'id':   'remove_die',
            'name': 'Remove a Die',
            'desc': 'Permanently remove one d6 from your pool (5 dice total). '
                    'Fewer dice means less noise and more control over '
                    'which numbers you hit.',
            'icon': '❌',
        },
    ],
    # ── Forge II  (after Level 2 boss) ─────────────────────────────────────
    [
        {
            'id':   'loaded_high',
            'name': 'Load: High Numbers',
            'desc': 'All your dice are loaded toward high faces. '
                    'Each die has 3/12 chance to roll 4, 5, or 6 '
                    'but only 1/12 chance to roll 1, 2, or 3 — '
                    'great for Armor, HP, and Research upgrades.',
            'icon': '⚖️',
        },
        {
            'id':   'free_reroll',
            'name': 'Free Reroll',
            'desc': 'Once per upgrade turn, before selecting a number, '
                    'you may reroll all your dice for free. '
                    'It does not cost a turn.',
            'icon': '🔄',
        },
        {
            'id':   'risky_die',
            'name': 'Risky Die',
            'desc': 'Replace one d6 with a Risky Die whose faces are '
                    '1, 2, 3, 10, 11, 12. High ceiling, high floor — '
                    'great for reaching the hardest numbers.',
            'icon': '🎰',
        },
    ],
]

ATTACK_SPEED_CAP = 5.0  # maximum attacks per second (safety, not a balance cap)

# Pre-game forge — picked before the first enemy, alters the upgrade table.
# stat_targets: override the collection cap (default 6) per stat number.
# stat_removed: these stat numbers are disabled for the entire run.
PRE_GAME_FORGE = [
    {
        'id':   'spec_a',
        'name': 'Dark Pact',
        'desc': (
            'You sacrifice Attack Damage entirely — that stat is removed from '
            'your upgrade board for the whole run. In return, Dark vulnerability '
            'fires after only 5 stacks (instead of 6), and Attack Speed requires '
            '7 stacks to max out (threshold at 5).'
        ),
        'icon': '🌑',
        'stat_targets': {1: 7, 12: 5},
        'stat_removed': [2],
    },
    {
        'id':   'spec_b',
        'name': 'Aggressor',
        'desc': (
            'Attack Speed, Attack Damage, and Crit all fire at 5 stacks instead '
            'of 6, and their threshold bonuses trigger at 3 stacks instead of 4. '
            'Pure offensive build that comes online fast.'
        ),
        'icon': '⚔️',
        'stat_targets': {1: 5, 2: 5, 3: 5},
        'stat_removed': [],
    },
    {
        'id':   'spec_c',
        'name': 'Glasscannon',
        'desc': (
            'Armor and HP are removed from your upgrade board entirely. '
            'Attack Speed and Attack Damage require 7 stacks to max out '
            '(threshold at 5). You live and die by summons, spells, and dark.'
        ),
        'icon': '💀',
        'stat_targets': {1: 7, 2: 7},
        'stat_removed': [4, 5],
    },
]


# ---------------------------------------------------------------------------
# Player stats
# ---------------------------------------------------------------------------

@dataclass
class PlayerStats:
    max_hp: int       = 100
    current_hp: int   = 100
    attack_dmg: int   = 8
    attack_speed: float = 0.5   # attacks per second
    crit_chance: float  = 0.01
    armor: float        = 0.05
    block_chance: float = 0.03
    lifesteal: float    = 0.0
    dark_level: int     = 0
    summon_level: int   = 0
    spell_level: int    = 0
    gold: int           = 0
    item_slots: int     = 0
    free_items: int     = 0
    # Forge dice pool (modified by forge upgrades)
    extra_d12: int       = 0      # extra d12 dice added to pool
    extra_d3: int        = 0      # extra d3 dice added to pool
    removed_dice: int    = 0      # d6 dice removed from pool
    has_risky_die: bool  = False  # one die shows 1/2/3/10/11/12
    loaded_high: bool    = False  # all d6s weighted 3× toward 4/5/6
    has_free_reroll: bool = False # free reroll on first roll of each upgrade turn

    def to_dict(self) -> dict:
        return asdict(self)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def get_summon_stats(level: int) -> Optional[dict]:
    """Return summon stats for a given summon level, or None if level is 0."""
    if level <= 0:
        return None
    tier = None
    for t in SUMMON_TIERS:
        if level >= t['min_level']:
            tier = t
    return dict(tier) if tier else None


def get_dark_multiplier(hit_count: int, dark_level: int) -> float:
    """
    Damage multiplier from dark vulnerability stacks.
    Only applies when the player has dark_level > 0.
    hit_count is the number of hits BEFORE the current attack.

    Each dark level both raises the % bonus by 1 AND lowers the hit thresholds,
    so investing heavily rewards you with earlier and stronger ramp-up.
    Tier 2 threshold: max(3,  20 - dark_level)
    Tier 3 threshold: max(8,  50 - dark_level * 2)
    """
    if dark_level == 0 or hit_count == 0:
        return 1.0
    tier2 = max(3, 20 - dark_level)
    tier3 = max(8, 50 - dark_level * 2)
    if hit_count < tier2:
        bonus_pct = 10 + dark_level
    elif hit_count < tier3:
        bonus_pct = 25 + dark_level
    else:
        bonus_pct = 50 + dark_level
    return 1.0 + bonus_pct / 100.0


def apply_upgrades(player: PlayerStats, collections: dict,
                   stat_targets: dict = None, stat_removed: list = None) -> list:
    """
    Apply upgrade phase collections to player stats.
    collections:  {1: count, 2: count, ..., 12: count}
    stat_targets: optional override of the collection cap per stat (default 6).
                  Also scales the threshold proportionally.
    stat_removed: stat numbers that are disabled and yield no upgrade.
    Returns a list of human-readable upgrade events for the UI.
    """
    events = []
    _targets  = stat_targets or {}
    _removed  = set(stat_removed or [])

    for num in range(1, 13):
        count = collections.get(num, 0)
        if count == 0:
            continue

        # Skip stats removed by the pre-game forge
        if num in _removed:
            continue

        # Cap collections at the stat's target (default 6)
        target = _targets.get(num, 6)
        count = min(count, target)
        if count == 0:
            continue

        defn = STAT_DEFS[num]
        attr = defn['attr']

        # Special case: research (number 6)
        # threshold scales with target: at 4/6 and 6/6 normally
        if defn.get('special') == 'research':
            slot_threshold = max(1, int(4 * target / 6 + 0.5))
            free_threshold = target
            if count >= slot_threshold:
                player.item_slots += 1
                events.append({'number': num, 'stat': 'item_slots', 'gained': 1,
                               'threshold_bonus': False, 'desc': '+1 item slot'})
            if count >= free_threshold:
                player.free_items += 1
                events.append({'number': num, 'stat': 'free_items', 'gained': 1,
                               'threshold_bonus': True, 'desc': '+1 free item pick'})
            continue

        # Normal stats — threshold scales proportionally with target
        per_die = defn['per_die']
        gained = per_die * count
        threshold_bonus = False

        base_threshold = 3 if num >= 10 else 4
        threshold_at = max(1, int(base_threshold * target / 6 + 0.5)) if target != 6 else base_threshold
        if defn['has_threshold'] and count >= threshold_at:
            gained += defn['threshold']
            threshold_bonus = True

        # Apply
        current = getattr(player, attr)
        new_val = current + gained

        # Cap attacks per second
        if attr == 'attack_speed':
            new_val = min(ATTACK_SPEED_CAP, new_val)
            new_val = round(new_val, 4)

        # Heal HP when max_hp increases
        if attr == 'max_hp':
            heal = int(gained)
            player.max_hp = int(new_val)
            player.current_hp = min(player.max_hp, player.current_hp + heal)
        else:
            setattr(player, attr, new_val)

        events.append({
            'number': num,
            'stat': attr,
            'gained': round(gained, 4),
            'threshold_bonus': threshold_bonus,
            'desc': _upgrade_desc(attr, gained, threshold_bonus),
        })

    return events


def _upgrade_desc(attr: str, gained: float, threshold: bool) -> str:
    bonus = ' (+threshold)' if threshold else ''
    labels = {
        'attack_speed':  f'+{gained*100:.1f}% atk speed',
        'attack_dmg':    f'+{gained:.0f} attack damage',
        'crit_chance':   f'+{gained*100:.0f}% crit chance',
        'armor':         f'+{gained*100:.0f}% armor',
        'max_hp':        f'+{gained:.0f} max HP',
        'gold':          f'+{gained:.0f} gold',
        'summon_level':  f'+{gained:.0f} summon level',
        'spell_level':   f'+{gained:.0f} spell level',
        'block_chance':  f'+{gained*100:.0f}% block chance',
        'lifesteal':     f'+{gained*100:.1f}% lifesteal',
        'dark_level':    f'+{gained:.0f} dark level',
    }
    return labels.get(attr, f'+{gained} {attr}') + bonus


# ---------------------------------------------------------------------------
# Combat simulation
# ---------------------------------------------------------------------------

def simulate_combat(player: PlayerStats, enemy: dict, owned_items: list) -> dict:
    """
    Event-driven combat simulation. Returns:
        result:              'win' | 'lose'
        player_hp_remaining: int
        events:              list of timed events for frontend animation
    """
    rng = random.Random()

    # Item flags
    item_ids = {i['id'] for i in owned_items}
    has_vampiric_tome  = 'vampiric_tome'   in item_ids
    has_thorns_vest    = 'thorns_vest'     in item_ids
    has_battle_drum    = 'battle_drum'     in item_ids
    has_focusing_lens  = 'focusing_lens'   in item_ids
    has_lucky_charm    = 'lucky_charm'     in item_ids
    has_iron_gauntlets = 'iron_gauntlets'  in item_ids
    has_mana_surge     = 'mana_surge'      in item_ids
    has_ancient_shield = 'ancient_shield'  in item_ids
    has_battle_horn    = 'battle_horn'     in item_ids
    has_phoenix_feather= 'phoenix_feather' in item_ids

    spell_cooldown = 2.5 if has_focusing_lens else 4.0

    # Item-modified combat stats (applied locally, not mutating player)
    eff_crit    = player.crit_chance + (0.05 if has_lucky_charm    else 0)
    eff_dmg     = player.attack_dmg  + (8    if has_iron_gauntlets else 0)
    eff_armor   = min(0.90, player.armor + (0.10 if has_ancient_shield else 0))
    eff_aspeed  = min(ATTACK_SPEED_CAP, player.attack_speed + (0.1 if has_battle_horn else 0))  # attacks/s
    atk_cd      = round(1.0 / eff_aspeed, 4)   # cooldown derived from attacks/s
    phoenix_used = [False]

    # Mutable state (use lists to allow mutation inside nested functions)
    player_hp  = [player.current_hp]
    enemy_hp   = [enemy['hp']]

    summon     = get_summon_stats(player.summon_level)
    if summon and has_battle_drum:
        summon = dict(summon)
        summon['speed'] = round(summon['speed'] * 0.75, 3)  # 25% faster
    summon_hp  = [summon['hp'] if summon else 0]
    summon_alive = [summon is not None]

    hit_count = [0]   # player hits landed (for dark vulnerability)
    events    = []
    counter   = [0]
    queue     = []

    def push(t, etype, data=None):
        counter[0] += 1
        heapq.heappush(queue, (round(t, 4), counter[0], etype, data or {}))

    # Schedule first events
    push(atk_cd,         'player_attack')
    push(enemy['speed'], 'enemy_attack')
    if player.spell_level > 0:
        push(spell_cooldown, 'spell')
    if summon:
        push(summon['speed'], 'summon_attack')

    MAX_TIME = 300.0  # safety cap — 5 minutes

    while queue and player_hp[0] > 0 and enemy_hp[0] > 0:
        t, _, etype, _data = heapq.heappop(queue)
        if t > MAX_TIME:
            break

        if etype == 'player_attack':
            dmg = eff_dmg
            crit = rng.random() < eff_crit
            if crit:
                dmg = dmg * 2
            dark_mult = get_dark_multiplier(hit_count[0], player.dark_level)
            dmg = max(1, int(dmg * dark_mult))
            hit_count[0] += 1

            heal = 0
            if player.lifesteal > 0:
                heal = min(round(dmg * player.lifesteal), player.max_hp - player_hp[0])
                player_hp[0] += heal

            enemy_hp[0] = max(0, enemy_hp[0] - dmg)
            events.append({
                'time': t, 'type': 'player_attack',
                'dmg': dmg, 'crit': crit, 'heal': heal,
                'dark_mult': round(dark_mult, 2),
                'hit_count': hit_count[0],
                'enemy_hp': enemy_hp[0], 'player_hp': player_hp[0],
            })
            if enemy_hp[0] > 0:
                push(t + atk_cd, 'player_attack')

        elif etype == 'spell':
            dmg = 5 + 3 * player.spell_level + (10 if has_mana_surge else 0)
            dark_mult = get_dark_multiplier(hit_count[0], player.dark_level)
            dmg = max(1, int(dmg * dark_mult))
            heal = 0
            if has_vampiric_tome:
                heal = min(int(dmg * 0.30), player.max_hp - player_hp[0])
                player_hp[0] += heal
            enemy_hp[0] = max(0, enemy_hp[0] - dmg)
            events.append({
                'time': t, 'type': 'spell',
                'dmg': dmg, 'heal': heal, 'dark_mult': round(dark_mult, 2),
                'enemy_hp': enemy_hp[0], 'player_hp': player_hp[0],
            })
            if enemy_hp[0] > 0:
                push(t + spell_cooldown, 'spell')

        elif etype == 'summon_attack':
            if summon_alive[0]:
                dmg = summon['attack']
                dark_mult = get_dark_multiplier(hit_count[0], player.dark_level)
                dmg = max(1, int(dmg * dark_mult))
                enemy_hp[0] = max(0, enemy_hp[0] - dmg)
                events.append({
                    'time': t, 'type': 'summon_attack',
                    'dmg': dmg, 'dark_mult': round(dark_mult, 2), 'enemy_hp': enemy_hp[0],
                })
                if enemy_hp[0] > 0:
                    push(t + summon['speed'], 'summon_attack')

        elif etype == 'enemy_attack':
            blocked = rng.random() < player.block_chance
            ev = {'time': t, 'type': 'enemy_attack', 'blocked': blocked}

            if blocked:
                ev['player_hp'] = player_hp[0]
            else:
                raw  = enemy['attack']
                dmg_to_player = max(1, int(raw * (1 - eff_armor)))
                new_hp = player_hp[0] - dmg_to_player
                if new_hp <= 0 and has_phoenix_feather and not phoenix_used[0]:
                    new_hp = 1
                    phoenix_used[0] = True
                    ev['phoenix'] = True
                player_hp[0] = max(0, new_hp)
                ev['dmg']       = dmg_to_player
                ev['player_hp'] = player_hp[0]

                # Thorns
                if has_thorns_vest and enemy_hp[0] > 0:
                    thorns = 3
                    enemy_hp[0] = max(0, enemy_hp[0] - thorns)
                    ev['thorns'] = thorns
                    ev['enemy_hp'] = enemy_hp[0]

                # Summon also takes damage
                if summon_alive[0]:
                    summon_hp[0] = max(0, summon_hp[0] - raw)
                    ev['summon_dmg'] = raw
                    ev['summon_hp']  = summon_hp[0]
                    if summon_hp[0] <= 0:
                        summon_alive[0] = False
                        ev['summon_died'] = True

            events.append(ev)
            if player_hp[0] > 0 and enemy_hp[0] > 0:
                push(t + enemy['speed'], 'enemy_attack')

    result = 'win' if enemy_hp[0] <= 0 else 'lose'
    events.append({
        'time': events[-1]['time'] if events else 0,
        'type': 'combat_end',
        'result': result,
        'player_hp': player_hp[0],
        'enemy_hp': enemy_hp[0],
    })

    return {
        'result': result,
        'player_hp_remaining': player_hp[0],
        'events': events,
    }


HEAL_POTION = {
    'id':   'heal_potion',
    'name': 'Heal Potion',
    'desc': 'Restore 50% of your missing HP.',
    'cost': 50,
    'icon': '🧪',
}


def generate_shop_items() -> list:
    """Return 3 random items + the always-available Heal Potion."""
    items = random.sample(SHOP_ITEMS, min(3, len(SHOP_ITEMS)))
    return [HEAL_POTION] + items


class StatefulDiceRoller:
    """
    Stateful dice roller for the RPG upgrade phase.

    Tracks which die types are currently in hand so that when dice are
    collected and remaining dice are re-rolled, the special dice (d12, d3,
    risky) are only present if they weren't part of the collection.

    Call prepare_for_collection(dice_values, target) BEFORE execute_action
    so the roller knows which types survive the collection.
    """

    def __init__(self, player: 'PlayerStats'):
        has_risky = player.has_risky_die
        extra_12  = player.extra_d12
        extra_3   = player.extra_d3
        self._weighted = player.loaded_high
        base_d6 = max(0, 6 - player.removed_dice - (1 if has_risky else 0))

        self._full_pool: list[str] = (
            (['risky'] if has_risky else []) +
            ['d12'] * extra_12 +
            ['d3']  * extra_3  +
            ['d6']  * base_d6
        )
        self.total: int = len(self._full_pool)
        self._types_in_hand: list[str] = self._full_pool[:]

    def _roll_one(self, t: str) -> int:
        if t == 'risky': return random.choice([1, 2, 3, 10, 11, 12])
        if t == 'd12':   return random.randint(1, 12)
        if t == 'd3':    return random.randint(1, 3)
        # d6 (possibly weighted toward high faces)
        if self._weighted:
            r = random.randint(1, 12)
            if r <= 1:   return 1
            elif r <= 2: return 2
            elif r <= 3: return 3
            elif r <= 6: return 4
            elif r <= 9: return 5
            else:        return 6
        return random.randint(1, 6)

    def prepare_for_collection(self, dice_values: list, target: int):
        """
        Called BEFORE the engine collects target from dice_values.
        Computes which die types survive the collection so the next
        re-roll only uses those types.
        """
        # Pair each current die value with its type by position
        pairs = list(zip(dice_values, self._types_in_hand))
        remaining = list(pairs)

        # Remove singles (value == target)
        remaining = [(v, t) for (v, t) in remaining if v != target]

        # Remove pair combos
        remaining_values = [v for v, t in remaining]
        combinations = GameRules.find_valid_combinations(remaining_values, target)
        for combo in combinations:
            for die_val in combo:
                for i, (v, t) in enumerate(remaining):
                    if v == die_val:
                        remaining.pop(i)
                        break

        self._types_in_hand = [t for v, t in remaining]

    def __call__(self, num_dice: int) -> list:
        if num_dice >= self.total:
            # New turn (completed number, turn end, or free reroll) — full pool
            self._types_in_hand = self._full_pool[:]
        # Roll whatever types are in hand
        return [self._roll_one(t) for t in self._types_in_hand]

    @property
    def types_in_hand(self) -> list[str]:
        return list(self._types_in_hand)


# ---------------------------------------------------------------------------
# RPG-aware engine subclasses
# ---------------------------------------------------------------------------

class RPGPlayer(Player):
    """
    Player subclass that uses per-stat collection targets instead of the
    hardcoded GameRules.TARGET_PER_NUMBER = 6.

    - stat_targets: {num: target} — overrides the completion threshold per stat.
    - stat_removed: list of stat numbers that are disabled for this run.
      Their progress is pre-filled to 6 so the engine never offers them.
    """
    def __init__(self, name: str, stat_targets: dict, stat_removed: list):
        super().__init__(name)
        self._stat_targets = stat_targets
        for n in stat_removed:
            self.progress[n] = 6   # engine sees them as already complete

    def target_for(self, number: int) -> int:
        return self._stat_targets.get(number, 6)

    def add_collected(self, number: int, count: int) -> bool:
        target = self.target_for(number)
        current = self.progress.get(number, 0)
        new_total = min(current + count, target)
        self.progress[number] = new_total
        return new_total >= target and current < target

    def is_winner(self) -> bool:
        # Never signal "won" to the engine — the RPG uses turn-based upgrade_done
        return False


class RPGUpgradeEngine(MLGameEngine):
    """
    MLGameEngine subclass that delegates legal-action and completion checks
    to RPGPlayer so per-stat targets are respected.
    """
    def __init__(self, stat_targets: dict, stat_removed: list,
                 num_dice: int = None, roll_fn=None):
        self._rpg_stat_targets = stat_targets
        self._rpg_stat_removed = stat_removed
        super().__init__(num_dice=num_dice, roll_fn=roll_fn)
        self._install_rpg_player()

    def _install_rpg_player(self):
        rpg_player = RPGPlayer("RPG_Agent", self._rpg_stat_targets, self._rpg_stat_removed)
        self.player = rpg_player
        self.state.players = [self.player]

    def reset(self):
        """Override reset to keep the RPGPlayer instead of replacing with a plain Player."""
        self._install_rpg_player()
        self.state = GameState()
        self.state.players = [self.player]
        self.state.current_player_index = 0
        self.turn_number = 0
        self.total_rolls = 0
        self.start_new_turn()

    def _target_for(self, number: int) -> int:
        return self.player.target_for(number)

    def get_legal_actions(self) -> list:
        legal_actions = []
        if self.state.selected_number is None:
            for target in range(GameRules.MIN_NUMBER, GameRules.MAX_NUMBER + 1):
                if self._can_make_number(self.state.dice_values, target):
                    current_count = self.player.progress.get(target, 0)
                    stat_target = self._target_for(target)
                    if current_count < stat_target:
                        collectible = self._count_collectible(self.state.dice_values, target)
                        legal_actions.append({
                            'type': 'select',
                            'number': target,
                            'collectible': collectible,
                            'progress': current_count,
                            'remaining_needed': stat_target - current_count,
                        })
            if not legal_actions:
                legal_actions.append({'type': 'skip_turn', 'reason': 'no_valid_numbers'})
        else:
            target = self.state.selected_number
            stat_target = self._target_for(target)
            if self._can_make_number(self.state.dice_values, target):
                collectible = self._count_collectible(self.state.dice_values, target)
                legal_actions.append({
                    'type': 'collect',
                    'number': target,
                    'collectible': collectible,
                    'progress': self.player.progress.get(target, 0),
                    'remaining_needed': stat_target - self.player.progress.get(target, 0),
                })
        return legal_actions

    def _execute_select_and_collect(self, target: int) -> dict:
        # Use per-stat target for the "already completed" guard
        if self.player.progress.get(target, 0) >= self._target_for(target):
            return {
                'success': False,
                'reward': -100,
                'state': 'illegal',
                'info': {'error': f'{target} already completed (custom target)'},
            }
        return super()._execute_select_and_collect(target)


# ---------------------------------------------------------------------------
# Run state
# ---------------------------------------------------------------------------

class RPGRun:
    def __init__(self):
        self.run_id          = str(uuid.uuid4())
        self.player          = PlayerStats()
        self.level_idx       = 0       # 0-indexed
        self.fight_idx       = 0       # 0-indexed within level
        self.phase           = 'pre_game_forge'
        self.upgrade_engine  = None
        # Pre-game forge state
        self.stat_targets: dict = {}   # {num: target} — empty means all default to 6
        self.stat_removed: list = []   # stat numbers disabled for this run
        self.upgrade_turns_used = 0
        self.upgrade_done    = False
        self.last_combat     = None
        self.last_upgrades   = []
        self.shop_items           = []
        self.owned_items          = []
        self.forge_choices        = []
        self.free_reroll_available = False
        # History tracking
        self.total_collections: dict = {n: 0 for n in range(1, 13)}
        self.forge_history: list     = []   # list of chosen forge IDs in order
        self.started_at: str         = ''
        self._init_upgrade_phase()

    # ------------------------------------------------------------------
    # Properties
    # ------------------------------------------------------------------

    @property
    def current_enemy(self) -> dict:
        return LEVELS[self.level_idx]['enemies'][self.fight_idx]

    @property
    def upgrade_turns_max(self) -> int:
        return LEVELS[self.level_idx]['upgrade_turns']

    @property
    def upgrade_pool_size(self) -> int:
        """Total dice in the upgrade phase pool after forge modifications."""
        p = self.player
        return max(1, 6 - p.removed_dice + p.extra_d12 + p.extra_d3)
        # Note: risky die replaces a d6, so it doesn't change the count

    # ------------------------------------------------------------------
    # Upgrade phase
    # ------------------------------------------------------------------

    def _init_upgrade_phase(self):
        self._dice_roller = StatefulDiceRoller(self.player)
        self.upgrade_engine = RPGUpgradeEngine(
            stat_targets=self.stat_targets,
            stat_removed=self.stat_removed,
            num_dice=self._dice_roller.total,
            roll_fn=self._dice_roller,
        )
        self.upgrade_engine.reset()
        self.upgrade_turns_used = 0
        self.upgrade_done = False
        self.last_upgrades = []
        self.free_reroll_available = self.player.has_free_reroll

    def handle_action_result(self, result: dict):
        """Call after every upgrade action to track turn usage."""
        state = result.get('state')
        if state == 'turn_end':
            self.upgrade_turns_used += 1
            if self.upgrade_turns_used >= self.upgrade_turns_max:
                self.upgrade_done = True
            # New turn will begin — re-enable free reroll
            self.free_reroll_available = self.player.has_free_reroll
        elif state == 'completed_number':
            # Engine auto-started a new turn — re-enable free reroll
            self.free_reroll_available = self.player.has_free_reroll

    def finish_upgrade(self) -> list:
        """Apply stat upgrades and advance to combat phase."""
        collections = {n: self.upgrade_engine.player.progress.get(n, 0) for n in range(1, 13)}
        # Accumulate into run-level history
        for n, count in collections.items():
            self.total_collections[n] = self.total_collections.get(n, 0) + count
        upgrades = apply_upgrades(self.player, collections, self.stat_targets, self.stat_removed)
        self.last_upgrades = upgrades
        self.phase = 'combat'
        return upgrades

    # ------------------------------------------------------------------
    # Combat
    # ------------------------------------------------------------------

    def run_combat(self) -> dict:
        """Simulate the fight, update player HP, advance phase."""
        combat = simulate_combat(self.player, self.current_enemy, self.owned_items)
        self.last_combat = combat

        if combat['result'] == 'lose':
            self.phase = 'game_over'
        else:
            self.player.current_hp = combat['player_hp_remaining']
            if self.current_enemy['is_boss']:
                if self.level_idx >= 2:
                    self.phase = 'victory'
                else:
                    # Forge replaces the shop after the boss
                    self._init_forge()
                    self.phase = 'forge'
            else:
                self.fight_idx += 1
                next_enemy = LEVELS[self.level_idx]['enemies'][self.fight_idx]
                if next_enemy['is_boss']:
                    # Pre-boss shop replaces upgrade before the boss
                    self.shop_items = generate_shop_items()
                    self.phase = 'pre_boss_shop'
                else:
                    self.phase = 'upgrade'
                    self._init_upgrade_phase()

        return combat

    # ------------------------------------------------------------------
    # Shop
    # ------------------------------------------------------------------

    def buy_item(self, item_id: str, use_free: bool = False) -> tuple[bool, str]:
        """Returns (success, reason)."""
        item = next((i for i in self.shop_items if i['id'] == item_id), None)
        if not item:
            return False, 'item not found'

        # Heal potion: always gold, never a free pick, not tracked as owned item
        if item_id == 'heal_potion':
            if self.player.gold < item['cost']:
                return False, 'not enough gold'
            missing = self.player.max_hp - self.player.current_hp
            heal = missing // 2
            self.player.current_hp += heal
            self.player.gold -= item['cost']
            self.shop_items = [i for i in self.shop_items if i['id'] != 'heal_potion']
            return True, 'ok'

        if len(self.owned_items) >= max(1, self.player.item_slots):
            return False, 'no item slots'

        if use_free:
            if self.player.free_items <= 0:
                return False, 'no free item picks'
            self.player.free_items -= 1
        else:
            if self.player.gold < item['cost']:
                return False, 'not enough gold'
            self.player.gold -= item['cost']

        self.owned_items.append(item)
        self.shop_items = [i for i in self.shop_items if i['id'] != item_id]
        return True, 'ok'

    def reroll_shop(self) -> tuple[bool, str]:
        """Spend gold to refresh the 3 non-potion shop items. Cost: 30g."""
        REROLL_COST = 30
        if self.player.gold < REROLL_COST:
            return False, 'not enough gold'
        self.player.gold -= REROLL_COST
        self.shop_items = generate_shop_items()
        return True, 'ok'

    def close_shop(self):
        """Close shop. Behaviour depends on which shop phase we're in."""
        if self.phase == 'pre_boss_shop':
            # Proceed directly to the boss fight
            self.phase = 'combat'
        else:
            # Fallback: advance to next level (shouldn't be reached in normal flow)
            self.level_idx += 1
            self.fight_idx = 0
            self.phase = 'upgrade'
            self._init_upgrade_phase()

    # ------------------------------------------------------------------
    # Pre-game forge
    # ------------------------------------------------------------------

    def pick_pre_game_forge(self, choice_id: str) -> tuple[bool, str]:
        """Apply a pre-game forge choice and start the first upgrade phase."""
        choice = next((c for c in PRE_GAME_FORGE if c['id'] == choice_id), None)
        if not choice:
            return False, 'invalid choice'
        self.stat_targets = dict(choice.get('stat_targets', {}))
        self.stat_removed = list(choice.get('stat_removed', []))
        self.forge_history.append(choice_id)
        self.phase = 'upgrade'
        self._init_upgrade_phase()
        return True, 'ok'

    # ------------------------------------------------------------------
    # Forge
    # ------------------------------------------------------------------

    def _init_forge(self):
        """Set forge choices based on which level's boss was just beaten."""
        forge_idx = self.level_idx   # 0 after L1 boss, 1 after L2 boss
        if forge_idx < len(FORGE_LEVELS):
            self.forge_choices = FORGE_LEVELS[forge_idx]
        else:
            self.forge_choices = []

    def pick_forge(self, choice_id: str) -> tuple[bool, str]:
        """Apply a forge upgrade and advance to the next level."""
        choice = next((c for c in self.forge_choices if c['id'] == choice_id), None)
        if not choice:
            return False, 'invalid choice'

        effect = choice['id']
        p = self.player

        if effect == 'add_d12':
            p.extra_d12 += 1
        elif effect == 'add_d3':
            p.extra_d3 += 1
        elif effect == 'remove_die':
            p.removed_dice = min(p.removed_dice + 1, 5)   # keep at least 1 die
        elif effect == 'loaded_high':
            p.loaded_high = True
        elif effect == 'free_reroll':
            p.has_free_reroll = True
        elif effect == 'risky_die':
            p.has_risky_die = True

        # Record forge choice
        self.forge_history.append(choice['id'])

        # Advance to next level
        self.level_idx += 1
        self.fight_idx = 0
        self.forge_choices = []
        self.phase = 'upgrade'
        self._init_upgrade_phase()
        return True, 'ok'

    def use_free_reroll(self) -> bool:
        """
        Re-roll all dice for free — valid only before a number is selected
        and once per turn. Returns False if not available.
        """
        if not self.free_reroll_available:
            return False
        if self.upgrade_engine.state.selected_number is not None:
            return False   # already collecting, too late
        self.free_reroll_available = False
        n = self.upgrade_engine._num_dice
        self.upgrade_engine.state.dice_values = self.upgrade_engine._roll_fn(n)
        self.upgrade_engine.state.num_dice_in_hand = n
        self.upgrade_engine.total_rolls += 1
        return True

    # ------------------------------------------------------------------
    # History summary
    # ------------------------------------------------------------------

    def to_summary(self) -> dict:
        """Return a compact summary suitable for saving to run history."""
        from datetime import datetime, timezone
        outcome = 'win' if self.phase == 'victory' else 'lose'
        return {
            'run_id':       self.run_id,
            'timestamp':    self.started_at or datetime.now(timezone.utc).isoformat(),
            'outcome':      outcome,
            'level_reached': self.level_idx + 1 if outcome == 'lose' else 3,
            'fight_reached': self.fight_idx + 1 if outcome == 'lose' else 3,
            'end_stats':    self.player.to_dict(),
            'collections':  {str(n): self.total_collections.get(n, 0) for n in range(1, 13)},
            'forges':       list(self.forge_history),
            'items':        [i['id'] for i in self.owned_items],
            'item_names':   [i['name'] for i in self.owned_items],
        }

    # ------------------------------------------------------------------
    # Serialisation
    # ------------------------------------------------------------------

    # ------------------------------------------------------------------
    # Path helpers
    # ------------------------------------------------------------------

    def _upgrade_status(self, li: int, fi: int) -> str:
        if li < self.level_idx: return 'done'
        if li > self.level_idx: return 'upcoming'
        if fi < self.fight_idx: return 'done'
        if fi > self.fight_idx: return 'upcoming'
        if self.phase == 'pre_game_forge': return 'upcoming'
        if self.phase == 'upgrade' and not self.upgrade_done: return 'current'
        return 'done'

    def _fight_status(self, li: int, fi: int) -> str:
        if li < self.level_idx: return 'done'
        if li > self.level_idx: return 'upcoming'
        if fi < self.fight_idx: return 'done'
        if fi > self.fight_idx: return 'upcoming'
        if self.phase == 'combat': return 'current'
        if self.phase in ('forge', 'game_over', 'victory'): return 'done'
        return 'upcoming'

    def _pre_boss_shop_status(self, li: int) -> str:
        if li < self.level_idx: return 'done'
        if li > self.level_idx: return 'upcoming'
        if self.phase == 'pre_boss_shop': return 'current'
        # If we've reached combat at fight_idx==boss, shop is done
        boss_fi = next(i for i, e in enumerate(LEVELS[li]['enemies']) if e['is_boss'])
        if self.fight_idx >= boss_fi and self.phase not in ('upgrade',): return 'done'
        return 'upcoming'

    def _forge_status(self, li: int) -> str:
        if li < self.level_idx: return 'done'
        if li > self.level_idx: return 'upcoming'
        if self.phase == 'forge': return 'current'
        return 'upcoming'

    def _build_path(self) -> list:
        nodes = []
        for li, lvl in enumerate(LEVELS):
            enemies = lvl['enemies']
            for fi, enemy in enumerate(enemies):
                if enemy['is_boss']:
                    # Pre-boss shop instead of upgrade
                    nodes.append({
                        'type':   'pre_boss_shop',
                        'level':  li + 1,
                        'fight':  fi,
                        'status': self._pre_boss_shop_status(li),
                    })
                else:
                    nodes.append({
                        'type':      'upgrade',
                        'level':     li + 1,
                        'fight':     fi,
                        'turns':     lvl['upgrade_turns'],
                        'pool_size': self.upgrade_pool_size,
                        'status':    self._upgrade_status(li, fi),
                    })
                nodes.append({
                    'type':       'boss' if enemy['is_boss'] else 'fight',
                    'level':      li + 1,
                    'fight':      fi,
                    'enemy_name': enemy['name'],
                    'enemy_hp':   enemy['hp'],
                    'is_boss':    enemy['is_boss'],
                    'status':     self._fight_status(li, fi),
                })
            # Forge after boss (not after final level)
            if li < len(LEVELS) - 1:
                nodes.append({
                    'type':   'forge',
                    'level':  li + 1,
                    'status': self._forge_status(li),
                })
        return nodes

    def to_dict(self, yatzy_state: Optional[dict] = None) -> dict:
        enemy = self.current_enemy if self.phase in ('upgrade', 'combat', 'pre_boss_shop') else None
        shop_phases = ('shop', 'pre_boss_shop')
        return {
            'run_id':              self.run_id,
            'phase':               'upgrade_done' if (self.phase == 'upgrade' and self.upgrade_done) else self.phase,
            'stat_targets':        self.stat_targets,
            'stat_removed':        self.stat_removed,
            'pre_game_forge_choices': PRE_GAME_FORGE if self.phase == 'pre_game_forge' else [],
            'level':               self.level_idx + 1,
            'fight_index':         self.fight_idx,
            'is_boss':             enemy['is_boss'] if enemy else False,
            'enemy':               enemy,
            'upgrade_turns_used':      self.upgrade_turns_used,
            'upgrade_turns_max':       self.upgrade_turns_max,
            'upgrade_pool_size':       self.upgrade_pool_size,
            'upgrade_done':            self.upgrade_done,
            'free_reroll_available':   self.free_reroll_available,
            'player':              self.player.to_dict(),
            'summon_stats':        get_summon_stats(self.player.summon_level),
            'yatzy':               yatzy_state,
            'last_combat':         self.last_combat,
            'last_upgrades':       self.last_upgrades,
            'shop_items':          self.shop_items if self.phase in shop_phases else [],
            'owned_items':         self.owned_items,
            'forge_choices':       self.forge_choices if self.phase == 'forge' else [],
            'path':                self._build_path(),
        }
