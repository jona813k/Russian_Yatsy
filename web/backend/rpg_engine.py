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
    1:  {'attr': 'attack_speed',  'per_die': 0.025, 'threshold': 0.025,  'has_threshold': True},
    2:  {'attr': 'attack_dmg',    'per_die':  1,    'threshold':  1,     'has_threshold': True},
    3:  {'attr': 'crit_chance',   'per_die':  0.01, 'threshold':  0.01,  'has_threshold': True},
    4:  {'attr': 'armor',         'per_die':  0.02, 'threshold':  0.02,  'has_threshold': True},
    5:  {'attr': 'max_hp',        'per_die':  5,    'threshold':  5,     'has_threshold': True},
    6:  {'attr': 'item_slots',    'per_die':  0,    'threshold':  None,  'has_threshold': False, 'special': 'research'},
    7:  {'attr': 'gold',          'per_die':  20,   'threshold':  20,    'has_threshold': True},
    8:  {'attr': 'summon_level',  'per_die':  1,    'threshold':  1,     'has_threshold': True},
    9:  {'attr': 'spell_level',   'per_die':  1,    'threshold':  1,     'has_threshold': True},
    10: {'attr': 'block_chance',  'per_die':  0.02, 'threshold':  0.02,  'has_threshold': True},
    11: {'attr': 'lifesteal',     'per_die':  0.02, 'threshold':  0.02,  'has_threshold': True},
    12: {'attr': 'dark_level',    'per_die':  1,    'threshold':  1,     'has_threshold': True},
}

SUMMON_TIERS = [
    {'min_level':  1, 'name': 'Imp',      'attack':  1, 'speed': 2.0, 'hp':  10},
    {'min_level':  5, 'name': 'Wolf',     'attack':  3, 'speed': 2.0, 'hp':  25},
    {'min_level': 10, 'name': 'Orc',      'attack':  6, 'speed': 2.0, 'hp':  50, 'enrage_below': 0.25},
    {'min_level': 15, 'name': 'Skeleton', 'attack': 11, 'speed': 2.0, 'hp': 100, 'spell_vamp': 0.10, 'enrage_below': 0.25},
    {'min_level': 20, 'name': 'Dragon',   'attack': 18, 'speed': 2.0, 'hp': 200, 'spell_vamp': 0.10, 'dragon_aura': 0.05, 'enrage_below': 0.25},
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
            {'name': 'Orc Warrior',   'hp': 350,  'attack': 14, 'speed': 2.0, 'armor': 0.10, 'is_boss': False},
            {'name': 'Orc Berserker', 'hp': 300,  'attack': 18, 'speed': 1.5, 'armor': 0.10, 'regen': 3, 'is_boss': False},
            {'name': 'Orc Warchief',  'hp': 1200, 'attack': 16, 'speed': 2.0, 'is_boss': True},
        ],
    },
    {
        'level': 3,
        'upgrade_turns': 4,
        'enemies': [
            {'name': 'Dark Knight',  'hp': 600,  'attack': 26, 'speed': 2.0, 'armor': 0.20, 'is_boss': False},
            {'name': 'Shadow Mage',  'hp': 500,  'attack': 28, 'speed': 1.5, 'armor': 0.20, 'lifesteal': 0.6, 'is_boss': False},
            {'name': 'Demon Lord',   'hp': 2000, 'attack': 30, 'speed': 1.8, 'is_boss': True},
        ],
    },
]

SHOP_ITEMS = [
    # ── Tier 1 — first pre-boss shop ──────────────────────────────────────
    # Attack DMG
    {'id': 'atk_flat',         'name': 'Whetstone',           'tier': 1, 'cost': 100,
     'desc': '+5 permanent attack damage.'},
    {'id': 'triple_hit',       'name': 'Fury Talisman',       'tier': 1, 'cost': 100,
     'desc': 'Every 3rd attack deals an additional 20 damage.'},
    # Attack Speed
    {'id': 'crit_125',         'name': 'Sharpshooter Lens',   'tier': 1, 'cost': 100,
     'desc': 'Crits now deal 2.25× damage instead of 2×.'},
    # Crit
    {'id': 'armor_flat',       'name': 'Iron Plate',          'tier': 1, 'cost': 100,
     'desc': '+10% permanent armor.'},
    # Health
    {'id': 'armor_hp_ratio',   'name': 'Bulwark Rune',        'tier': 1, 'cost': 100,
     'desc': 'Gaining armor upgrades also gives HP (1% armor → 2 HP).'},
    # Research
    {'id': 'shop_free_reroll', 'name': 'Oracle Lens',         'tier': 1, 'cost': 100,
     'desc': 'Future shops and forges each have 1 free reroll.'},
    # Gold
    {'id': 'item_discount',    'name': 'Merchant Badge',      'tier': 1, 'cost': 100,
     'desc': 'Item costs are reduced by 20%.'},
    {'id': 'gold_level_bonus', 'name': 'Gold Vein',           'tier': 1, 'cost': 100,
     'desc': 'Gold upgrades give 5 extra gold per upgrade.'},
    {'id': 'bounty_50g',       'name': 'Bounty Token',        'tier': 1, 'cost': 100,
     'desc': 'Gain 50 gold each time you kill an enemy.'},
    # Summon
    {'id': 'summon_survive',   'name': 'Soul Tether',         'tier': 1, 'cost': 100,
     'desc': 'Your summon survives fights and gains 1 level per fight won.'},
    # Block
    {'id': 'block_reflect',    'name': 'Thorned Buckler',     'tier': 1, 'cost': 100,
     'desc': 'Blocked damage is returned to the attacker.'},
    {'id': 'block_atk_buff',   'name': "Guardian's Edge",     'tier': 1, 'cost': 100,
     'desc': 'Blocking an enemy attack increases your attack damage by 5 for 2s.'},
    # Life Steal
    {'id': 'lifesteal_spell',  'name': 'Siphon Stone',        'tier': 1, 'cost': 100,
     'desc': 'Lifesteal now also applies to spell damage.'},
    {'id': 'lifesteal_5pct',   'name': 'Vampiric Pendant',    'tier': 1, 'cost': 100,
     'desc': '+5% permanent lifesteal.'},
    {'id': 'heal_on_attack',   'name': 'Bloodbond Hilt',      'tier': 1, 'cost': 100,
     'desc': 'Heal 3 HP on every attack hit.'},

    # ── Tier 2 — second and third pre-boss shops ───────────────────────────
    # Attack DMG
    {'id': 'atk_execute',      'name': 'Finishing Blade',     'tier': 2, 'cost': 100,
     'desc': '+15 attack damage when the enemy is below 20% HP.'},
    {'id': 'armor_pen',        'name': 'Armor Shredder',      'tier': 2, 'cost': 100,
     'desc': 'Your attacks ignore all enemy armor.'},
    # Attack Speed
    {'id': 'berserker',        'name': 'Berserker Band',      'tier': 2, 'cost': 100,
     'desc': 'Gain 20% attack speed when below 50% HP.'},
    {'id': 'crit_to_aspeed',   'name': 'Swiftcrit Rune',      'tier': 2, 'cost': 100,
     'desc': 'Future crit upgrades convert to attack speed instead.'},
    # Crit
    {'id': 'crit_freeze',      'name': 'Frostcrit Gem',       'tier': 2, 'cost': 100,
     'desc': 'Crits freeze the enemy, slowing their attack speed by 50% for 2s.'},
    {'id': 'crit_lifesteal',   'name': 'Crimson Fang',        'tier': 2, 'cost': 100,
     'desc': 'Crits heal for the bonus crit damage. Disables normal lifesteal.'},
    # Armor
    {'id': 'armor_to_spell',   'name': 'Arcane Dissolution',  'tier': 2, 'cost': 100,
     'desc': 'Remove all your armor and gain that much as spell levels (5% → 1 level).'},
    # Health
    {'id': 'hp_to_atk',        'name': 'Bloodprice Sigil',    'tier': 2, 'cost': 100,
     'desc': 'Gain attack equal to 5% of your max HP.'},
    {'id': 'hp_double_armor',  'name': 'Ironflesh Pact',      'tier': 2, 'cost': 100,
     'desc': 'Double your max HP and gain -30% armor.'},
    # Research
    {'id': 'research_2slots',  'name': "Scholar's Tome",      'tier': 2, 'cost': 100,
     'desc': 'Gain 2 item slots and 2 free item credits.'},
    # Summon
    {'id': 'summon_upgrade',   'name': "Summoner's Codex",    'tier': 2, 'cost': 100,
     'desc': 'Upgrade summon abilities: enrage at 35% HP, spell vamp 15%, dragon aura 10%.'},
    # Spell
    {'id': 'spell_fire',       'name': 'Flame Rune',          'tier': 2, 'cost': 100,
     'desc': 'Your spell burns enemies for 10% of spell damage per second over 3s.'},
    {'id': 'spell_frost',      'name': 'Frost Staff',         'tier': 2, 'cost': 100,
     'desc': 'Your spell slows enemy attack speed by 50% for 3s.'},
    {'id': 'spell_heal_summon','name': 'Life Conduit',        'tier': 2, 'cost': 100,
     'desc': 'Your spell heals your summon instead of damaging (1 heal per 2 spell dmg).'},
    # Block
    {'id': 'armor_to_block',   'name': 'Shield Conversion',   'tier': 2, 'cost': 100,
     'desc': 'Convert all armor to block (1% armor → 0.5% block).'},
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
        'name': 'Standard',
        'desc': 'No changes. All stats upgrade normally.',
        'icon': '⚖️',
        'stat_targets': {},
        'stat_removed': [],
    },
    {
        'id':   'spec_b',
        'name': 'Aggressor',
        'desc': (
            'Attack Speed, Damage, and Crit max out at 4 stacks — they come online fast. '
            'HP and Armor require 7 stacks instead.'
        ),
        'icon': '⚔️',
        'stat_targets': {1: 4, 2: 4, 3: 4, 4: 7, 5: 7},
        'stat_removed': [],
    },
    {
        'id':   'spec_c',
        'name': 'Mage',
        'desc': (
            'Spell and Summon max out at 5 stacks. '
            'Attack Speed, Damage, and Crit require 7 stacks instead.'
        ),
        'icon': '🔮',
        'stat_targets': {1: 7, 2: 7, 3: 7, 8: 5, 9: 5},
        'stat_removed': [],
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
    # Item passive flags
    has_shop_free_reroll: bool = False  # each future shop/forge gets 1 free reroll
    has_item_discount: bool    = False  # items cost 20% less
    has_crit_to_aspeed: bool   = False  # crit upgrades convert to atk speed
    has_armor_gives_hp: bool   = False  # armor upgrades also give HP (1% → 2 HP)
    has_gold_level_bonus: bool = False  # gold upgrades give +5 extra gold

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
    tier2 = max(3, 15 - dark_level)
    tier3 = max(8, 30 - dark_level * 2)
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

        # Crit-to-speed: if player has this item, crit upgrades become atk speed
        if attr == 'crit_chance' and getattr(player, 'has_crit_to_aspeed', False):
            attr = 'attack_speed'
            per_die = STAT_DEFS[1]['per_die']   # use atk_speed per_die

        gained = per_die * count
        threshold_bonus = False

        base_threshold = 3 if num >= 10 else 4
        threshold_at = max(1, int(base_threshold * target / 6 + 0.5)) if target != 6 else base_threshold
        if defn['has_threshold'] and count >= threshold_at:
            gained += STAT_DEFS[1]['threshold'] if attr == 'attack_speed' and defn['attr'] == 'crit_chance' else defn['threshold']
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

        # Armor gives HP bonus (item: armor_hp_ratio — 1% armor → 2 HP)
        if attr == 'armor' and getattr(player, 'has_armor_gives_hp', False):
            hp_gain = int(gained * 200)   # 0.01 armor = 2 HP → 0.01 * 200 = 2
            if hp_gain > 0:
                player.max_hp += hp_gain
                player.current_hp = min(player.max_hp, player.current_hp + hp_gain)
                events.append({
                    'number': num, 'stat': 'max_hp', 'gained': hp_gain,
                    'threshold_bonus': False,
                    'desc': f'+{hp_gain} max HP (armor bonus)',
                })

        # Gold level bonus (item: gold_level_bonus — +5 extra gold per upgrade)
        if attr == 'gold' and getattr(player, 'has_gold_level_bonus', False):
            player.gold += 5
            events.append({
                'number': num, 'stat': 'gold', 'gained': 5,
                'threshold_bonus': False,
                'desc': '+5 gold (level bonus)',
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

def simulate_combat(player: PlayerStats, enemy: dict, owned_items: list,
                    summon_hp_start: int = None) -> dict:
    """
    Event-driven combat simulation. Returns:
        result:              'win' | 'lose'
        player_hp_remaining: int
        summon_hp_remaining: int
        events:              list of timed events for frontend animation
    """
    rng = random.Random()

    # Item flags
    item_ids = {i['id'] for i in owned_items}
    # Tier 1 combat items
    has_triple_hit       = 'triple_hit'      in item_ids
    has_crit_125         = 'crit_125'        in item_ids
    has_block_reflect    = 'block_reflect'   in item_ids
    has_block_atk_buff   = 'block_atk_buff'  in item_ids
    has_lifesteal_spell  = 'lifesteal_spell' in item_ids
    has_heal_on_attack   = 'heal_on_attack'  in item_ids
    has_bounty_50g       = 'bounty_50g'      in item_ids
    # Tier 2 combat items
    has_atk_execute      = 'atk_execute'     in item_ids
    has_armor_pen        = 'armor_pen'       in item_ids
    has_berserker        = 'berserker'       in item_ids
    has_crit_freeze      = 'crit_freeze'     in item_ids
    has_crit_lifesteal   = 'crit_lifesteal'  in item_ids
    has_summon_upgrade   = 'summon_upgrade'  in item_ids
    has_spell_fire       = 'spell_fire'      in item_ids
    has_spell_frost      = 'spell_frost'     in item_ids
    has_spell_heal_summon= 'spell_heal_summon' in item_ids

    spell_cooldown = 4.0

    # Enemy special properties
    enemy_armor    = enemy.get('armor',    0.0)
    enemy_regen    = enemy.get('regen',    0)
    enemy_lifesteal= enemy.get('lifesteal',0.0)
    # Armor Pen: ignore all enemy armor
    eff_enemy_armor = 0.0 if has_armor_pen else enemy_armor

    # Combat stats
    eff_crit    = player.crit_chance
    eff_dmg     = player.attack_dmg
    eff_armor   = min(0.90, player.armor)
    eff_aspeed  = min(ATTACK_SPEED_CAP, player.attack_speed)   # attacks/s
    atk_cd      = round(1.0 / eff_aspeed, 4)   # cooldown derived from attacks/s

    # Summon upgrade item modifies summon special abilities
    if has_summon_upgrade and summon:
        summon = dict(summon)
        if summon.get('enrage_below') is not None:
            summon['enrage_below'] = 0.35
        if summon.get('spell_vamp') is not None:
            summon['spell_vamp'] = 0.15
        if summon.get('dragon_aura') is not None:
            summon['dragon_aura'] = 0.10

    # Mutable state (use lists to allow mutation inside nested functions)
    player_hp  = [player.current_hp]
    enemy_hp   = [enemy['hp']]

    summon     = get_summon_stats(player.summon_level)
    start_hp   = summon['hp'] if summon else 0
    if summon_hp_start is not None and summon:
        start_hp = min(summon_hp_start, summon['hp'])
    summon_hp  = [start_hp]
    summon_alive = [summon is not None]

    hit_count       = [0]    # player hits landed (for dark vulnerability)
    atk_consecutive = [0]   # attack streak counter (triple_strike)
    frost_until     = [0.0] # enemy slowed until this time (frost_staff / ice_strike)
    guard_buff_until= [0.0] # player guard buff until this time (guard_oath)

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
    if enemy_regen > 0:
        push(1.0, 'enemy_regen')

    MAX_TIME = 300.0  # safety cap — 5 minutes

    while queue and player_hp[0] > 0 and enemy_hp[0] > 0:
        t, _, etype, _data = heapq.heappop(queue)
        if t > MAX_TIME:
            break

        aura_mult = (1 + summon['dragon_aura']) if (summon_alive[0] and summon and summon.get('dragon_aura')) else 1.0

        if etype == 'player_attack':
            # Berserker: +20% attack speed when below 50% HP
            if has_berserker and player_hp[0] < player.max_hp * 0.5:
                effective_aspeed = min(ATTACK_SPEED_CAP, eff_aspeed * 1.20)
                current_atk_cd = round(1.0 / effective_aspeed, 4)
            else:
                current_atk_cd = atk_cd

            # Block atk buff: +5 dmg for 2s after blocking
            guard_bonus = 5 if (has_block_atk_buff and t <= guard_buff_until[0]) else 0
            dmg = eff_dmg + guard_bonus
            # Execute: +15 dmg when enemy below 20% HP
            is_execute = has_atk_execute and enemy_hp[0] < enemy['hp'] * 0.20
            if is_execute:
                dmg += 15

            crit = rng.random() < eff_crit
            crit_mult = 2.25 if has_crit_125 else 2.0
            if crit:
                dmg = int(dmg * crit_mult)

            dark_mult = get_dark_multiplier(hit_count[0], player.dark_level)
            dmg = max(1, int(dmg * dark_mult * aura_mult * (1 - eff_enemy_armor)))
            hit_count[0] += 1
            atk_consecutive[0] += 1

            heal = 0
            if crit and has_crit_lifesteal:
                # Crit lifesteal: heal for the bonus crit damage; disables normal lifesteal
                base_dmg = max(1, int((eff_dmg + guard_bonus + (15 if is_execute else 0))
                                      * dark_mult * aura_mult * (1 - eff_enemy_armor)))
                crit_bonus = dmg - base_dmg
                crit_ls_heal = min(crit_bonus, player.max_hp - player_hp[0])
                if crit_ls_heal > 0:
                    player_hp[0] += crit_ls_heal
                    heal += crit_ls_heal
            elif player.lifesteal > 0:
                ls_heal = min(round(dmg * player.lifesteal), player.max_hp - player_hp[0])
                player_hp[0] += ls_heal
                heal += ls_heal
            if has_heal_on_attack:
                atk_heal = min(3, player.max_hp - player_hp[0])
                player_hp[0] += atk_heal
                heal += atk_heal

            enemy_hp[0] = max(0, enemy_hp[0] - dmg)
            ev = {
                'time': t, 'type': 'player_attack',
                'dmg': dmg, 'crit': crit, 'heal': heal,
                'dark_mult': round(dark_mult, 2),
                'hit_count': hit_count[0],
                'enemy_hp': enemy_hp[0], 'player_hp': player_hp[0],
            }
            if is_execute:
                ev['execute'] = True
            events.append(ev)

            # Crit freeze: slow enemy 50% for 2s on crit
            if crit and has_crit_freeze and enemy_hp[0] > 0:
                frost_until[0] = max(frost_until[0], t + 2.0)

            # Triple hit: every 3rd attack deals additional 20 dmg
            if has_triple_hit and atk_consecutive[0] % 3 == 0 and enemy_hp[0] > 0:
                bonus_dmg = 20
                enemy_hp[0] = max(0, enemy_hp[0] - bonus_dmg)
                events.append({
                    'time': t, 'type': 'player_attack',
                    'dmg': bonus_dmg, 'crit': False, 'heal': 0,
                    'dark_mult': round(dark_mult, 2),
                    'hit_count': hit_count[0],
                    'enemy_hp': enemy_hp[0], 'player_hp': player_hp[0],
                    'triple_hit': True,
                })

            if enemy_hp[0] > 0:
                push(t + current_atk_cd, 'player_attack')

        elif etype == 'spell':
            base_spell_dmg = 17 + 3 * player.spell_level
            dark_mult = get_dark_multiplier(hit_count[0], player.dark_level)

            heal = 0
            if has_spell_heal_summon and summon_alive[0] and summon:
                # Spell heals summon instead of damaging enemy (1 heal per 2 spell dmg)
                summon_heal = int(base_spell_dmg / 2)
                summon_hp[0] = min(summon['hp'], summon_hp[0] + summon_heal)
                ev = {
                    'time': t, 'type': 'spell',
                    'dmg': 0, 'heal': 0, 'dark_mult': 1.0,
                    'enemy_hp': enemy_hp[0], 'player_hp': player_hp[0],
                    'summon_heal': summon_heal, 'summon_hp': summon_hp[0],
                }
                events.append(ev)
                if enemy_hp[0] > 0:
                    push(t + spell_cooldown, 'spell')
                continue

            dmg = max(1, int(base_spell_dmg * dark_mult * aura_mult))
            # Spell vamp from Skeleton/Dragon
            if summon_alive[0] and summon and summon.get('spell_vamp', 0) > 0:
                sv = min(int(dmg * summon['spell_vamp']), player.max_hp - player_hp[0])
                if sv > 0:
                    player_hp[0] += sv
                    heal += sv
            # Lifesteal spell item: lifesteal applies to spell damage
            if has_lifesteal_spell and player.lifesteal > 0:
                siphon_heal = min(round(dmg * player.lifesteal), player.max_hp - player_hp[0])
                if siphon_heal > 0:
                    player_hp[0] += siphon_heal
                    heal += siphon_heal

            enemy_hp[0] = max(0, enemy_hp[0] - dmg)
            ev = {
                'time': t, 'type': 'spell',
                'dmg': dmg, 'heal': heal, 'dark_mult': round(dark_mult, 2),
                'enemy_hp': enemy_hp[0], 'player_hp': player_hp[0],
            }
            # Spell Frost: slow enemy 50% for 3s
            if has_spell_frost and enemy_hp[0] > 0:
                frost_until[0] = max(frost_until[0], t + 3.0)
                ev['frost'] = True
            # Spell Fire: burn for 10% spell dmg/s over 3s
            if has_spell_fire and enemy_hp[0] > 0:
                burn_dmg = max(1, int(base_spell_dmg * 0.10))
                for tick in range(1, 4):
                    push(t + tick, 'burn_tick', {'dmg': burn_dmg})
                ev['burn_applied'] = True
            events.append(ev)
            if enemy_hp[0] > 0:
                push(t + spell_cooldown, 'spell')

        elif etype == 'burn_tick':
            if enemy_hp[0] > 0:
                bdmg = _data.get('dmg', 5)
                enemy_hp[0] = max(0, enemy_hp[0] - bdmg)
                events.append({
                    'time': t, 'type': 'burn_tick',
                    'dmg': bdmg, 'enemy_hp': enemy_hp[0],
                })

        elif etype == 'summon_attack':
            if summon_alive[0]:
                dmg = summon['attack']
                dark_mult = get_dark_multiplier(hit_count[0], player.dark_level)
                dmg = max(1, int(dmg * dark_mult))
                enemy_hp[0] = max(0, enemy_hp[0] - dmg)
                enraged = (summon.get('enrage_below') is not None and
                           summon_hp[0] < summon['hp'] * summon['enrage_below'])
                next_speed = 1.0 if enraged else summon['speed']
                events.append({
                    'time': t, 'type': 'summon_attack',
                    'dmg': dmg, 'dark_mult': round(dark_mult, 2),
                    'enemy_hp': enemy_hp[0], 'enraged': enraged,
                })
                if enemy_hp[0] > 0:
                    push(t + next_speed, 'summon_attack')

        elif etype == 'enemy_regen':
            heal = min(enemy_regen, enemy['hp'] - enemy_hp[0])
            if heal > 0:
                enemy_hp[0] += heal
                events.append({
                    'time': t, 'type': 'enemy_regen',
                    'heal': heal, 'enemy_hp': enemy_hp[0],
                })
            if enemy_hp[0] > 0:
                push(t + 1.0, 'enemy_regen')

        elif etype == 'enemy_attack':
            blocked = rng.random() < player.block_chance
            ev = {'time': t, 'type': 'enemy_attack', 'blocked': blocked}

            if blocked:
                ev['player_hp'] = player_hp[0]
                # Block reflect: return blocked damage to attacker
                if has_block_reflect and enemy_hp[0] > 0:
                    thorns = enemy['attack']
                    enemy_hp[0] = max(0, enemy_hp[0] - thorns)
                    ev['thorns'] = thorns
                    ev['enemy_hp'] = enemy_hp[0]
                # Block atk buff: +5 dmg for 2s
                if has_block_atk_buff:
                    guard_buff_until[0] = t + 2.0
            elif summon_alive[0]:
                # Summon tanks all damage — player takes nothing
                raw = enemy['attack']
                summon_hp[0] = max(0, summon_hp[0] - raw)
                ev['summon_dmg'] = raw
                ev['summon_hp']  = summon_hp[0]
                ev['player_hp']  = player_hp[0]
                if summon_hp[0] <= 0:
                    summon_alive[0] = False
                    ev['summon_died'] = True
            else:
                raw  = enemy['attack']
                dmg_to_player = max(1, int(raw * (1 - eff_armor)))
                new_hp = player_hp[0] - dmg_to_player
                player_hp[0] = max(0, new_hp)
                ev['dmg']       = dmg_to_player
                ev['player_hp'] = player_hp[0]

                # Enemy lifesteal — heals enemy when it hits
                if enemy_lifesteal > 0 and enemy_hp[0] > 0:
                    ls_heal = min(int(dmg_to_player * enemy_lifesteal), enemy['hp'] - enemy_hp[0])
                    if ls_heal > 0:
                        enemy_hp[0] += ls_heal
                        ev['enemy_lifesteal_heal'] = ls_heal
                        ev['enemy_hp'] = enemy_hp[0]

            events.append(ev)
            if player_hp[0] > 0 and enemy_hp[0] > 0:
                # Frost slow: extend enemy attack interval if slowed
                next_atk_delay = enemy['speed']
                if frost_until[0] > t:
                    next_atk_delay = round(enemy['speed'] / 0.7, 4)  # 30% slower
                push(t + next_atk_delay, 'enemy_attack')

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
        'summon_hp_remaining': summon_hp[0] if summon_alive[0] else 0,
        'events': events,
    }


HEAL_POTION = {
    'id':   'heal_potion',
    'name': 'Heal Potion',
    'desc': 'Restore 50% of your missing HP.',
    'cost': 50,
    'icon': '🧪',
}


def generate_shop_items(level_idx: int = 0, discount: bool = False) -> list:
    """Return 3 random tier-appropriate items + the always-available Heal Potion."""
    tier = 1 if level_idx == 0 else 2
    pool = [i for i in SHOP_ITEMS if i['tier'] == tier]
    items = random.sample(pool, min(3, len(pool)))
    if discount:
        items = [{**i, 'cost': int(i['cost'] * 0.8)} for i in items]
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
        self._summon_hp_carry: int = None   # summon_survive carry-over
        self._shop_reroll_used: bool = False  # shop_free_reroll used this shop
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
        item_ids = {i['id'] for i in self.owned_items}
        has_bounty_50g  = 'bounty_50g'      in item_ids
        has_summon_survive = 'summon_survive' in item_ids

        summon_hp_start = None
        if has_summon_survive and getattr(self, '_summon_hp_carry', None):
            summon_hp_start = self._summon_hp_carry

        combat = simulate_combat(self.player, self.current_enemy, self.owned_items, summon_hp_start)
        self.last_combat = combat

        # Bounty Token: gain 50 gold on kill
        if has_bounty_50g and combat['result'] == 'win':
            self.player.gold += 50

        # Summon survive: carry summon HP and gain 1 level on win
        if has_summon_survive:
            remaining = combat.get('summon_hp_remaining', 0)
            if remaining > 0 and combat['result'] == 'win':
                self._summon_hp_carry = remaining
                self.player.summon_level += 1
            else:
                self._summon_hp_carry = None
        else:
            self._summon_hp_carry = None

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
                    self.shop_items = generate_shop_items(self.level_idx, self.player.has_item_discount)
                    self._shop_reroll_used = False
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

        # Apply immediate stat effects on purchase
        iid = item['id']
        p = self.player
        if iid == 'atk_flat':
            p.attack_dmg += 5
        elif iid == 'armor_flat':
            p.armor = round(min(0.90, p.armor + 0.10), 4)
        elif iid == 'lifesteal_5pct':
            p.lifesteal = round(p.lifesteal + 0.05, 4)
        elif iid == 'shop_free_reroll':
            p.has_shop_free_reroll = True
            self._shop_reroll_used = False
        elif iid == 'item_discount':
            p.has_item_discount = True
        elif iid == 'armor_hp_ratio':
            p.has_armor_gives_hp = True
        elif iid == 'gold_level_bonus':
            p.has_gold_level_bonus = True
        elif iid == 'crit_to_aspeed':
            p.has_crit_to_aspeed = True
        elif iid == 'research_2slots':
            p.item_slots += 2
            p.free_items += 2
        elif iid == 'armor_to_spell':
            spell_gain = int(p.armor / 0.05)
            p.armor = 0.0
            p.spell_level += spell_gain
        elif iid == 'hp_to_atk':
            p.attack_dmg += int(p.max_hp * 0.05)
        elif iid == 'hp_double_armor':
            gain = p.max_hp
            p.max_hp *= 2
            p.current_hp = min(p.max_hp, p.current_hp + gain)
            p.armor = round(max(0.0, p.armor - 0.30), 4)
        elif iid == 'armor_to_block':
            block_gain = round(p.armor * 0.5, 4)
            p.block_chance = round(min(0.95, p.block_chance + block_gain), 4)
            p.armor = 0.0

        self.owned_items.append(item)
        self.shop_items = [i for i in self.shop_items if i['id'] != item_id]
        return True, 'ok'

    def reroll_shop(self) -> tuple[bool, str]:
        """Spend gold to refresh the 3 non-potion shop items. Cost: 30g."""
        REROLL_COST = 30
        # Free reroll if player has oracle lens and hasn't used it this shop
        use_free = self.player.has_shop_free_reroll and not self._shop_reroll_used
        if not use_free:
            if self.player.gold < REROLL_COST:
                return False, 'not enough gold'
            self.player.gold -= REROLL_COST
        self._shop_reroll_used = True
        self.shop_items = generate_shop_items(self.level_idx, self.player.has_item_discount)
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
