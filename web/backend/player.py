"""
Player stats dataclass and upgrade application logic.
"""
from dataclasses import dataclass, asdict

from .data import STAT_DEFS, ATTACK_SPEED_CAP


@dataclass
class PlayerStats:
    max_hp: int         = 100
    current_hp: int     = 100
    attack_dmg: int     = 8
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
    # Forge dice pool
    extra_d12: int        = 0      # extra d12 dice added to pool
    extra_d3: int         = 0      # extra d3 dice added to pool
    removed_dice: int     = 0      # d6 dice removed from pool
    has_risky_die: bool   = False  # one die shows 1/2/3/10/11/12
    loaded_high: bool     = False  # all d6s weighted 3× toward 4/5/6
    has_free_reroll: bool = False  # free reroll on first roll of each upgrade turn
    dice_plus_one: bool   = False  # all d6s roll +1 higher (2–7)
    has_2_5_die: bool     = False  # extra die that only shows 2 or 5
    has_retry_die: bool   = False  # extra die with one reroll per turn
    has_logic_die: bool   = False  # extra die rolling 1→2→3→4→5→6→1→… in sequence
    logic_die_pos: int    = 0      # next value index in the logic die sequence (0–5)
    loaded_low: bool      = False  # all d6s weighted 3× toward 1/2/3
    has_mirror_die: bool  = False  # extra die that copies the highest rolled value
    has_bomb_die: bool    = False  # extra die that auto-stashes its value at turn end
    # Gladiator key
    has_gladiator_key: bool = False  # purchased from shop; required to enter the showdown
    # Item passive flags
    has_shop_free_reroll: bool = False  # each future shop/forge gets 1 free reroll
    has_item_discount: bool    = False  # items cost 20% less
    has_crit_to_aspeed: bool   = False  # crit upgrades convert to atk speed
    has_armor_gives_hp: bool   = False  # armor upgrades also give HP (1% → 2 HP)
    has_gold_level_bonus: bool = False  # gold upgrades give +10 extra gold
    has_summon_upgrade: bool   = False  # summon heals for 10% of damage dealt

    def to_dict(self) -> dict:
        return asdict(self)


def apply_upgrades(player: PlayerStats, collections: dict,
                   stat_targets: dict = None, stat_removed: list = None) -> list:
    """
    Apply upgrade phase collections to player stats.
    collections:  {1: count, 2: count, ..., 12: count}
    stat_targets: optional override of the collection cap per stat (default 6).
    stat_removed: stat numbers disabled for this run.
    Returns a list of human-readable upgrade events for the UI.
    """
    events = []
    _targets = stat_targets or {}
    _removed = set(stat_removed or [])

    for num in range(1, 13):
        count = collections.get(num, 0)
        if count == 0:
            continue
        if num in _removed:
            continue

        target = _targets.get(num, 6)
        count = min(count, target)
        if count == 0:
            continue

        defn = STAT_DEFS[num]
        attr = defn['attr']

        # Special case: research (number 7)
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

        per_die = defn['per_die']

        # Crit-to-speed: if player has this item, crit upgrades become atk speed
        if attr == 'crit_chance' and getattr(player, 'has_crit_to_aspeed', False):
            attr = 'attack_speed'
            per_die = STAT_DEFS[1]['per_die']

        gained = per_die * count
        threshold_bonus = False

        base_threshold = 3 if num >= 10 else 4
        threshold_at = max(1, int(base_threshold * target / 6 + 0.5)) if target != 6 else base_threshold
        if defn['has_threshold'] and count >= threshold_at:
            gained += STAT_DEFS[1]['threshold'] if attr == 'attack_speed' and defn['attr'] == 'crit_chance' else defn['threshold']
            threshold_bonus = True

        current = getattr(player, attr)
        new_val = current + gained

        if attr == 'attack_speed':
            new_val = min(ATTACK_SPEED_CAP, new_val)
            new_val = round(new_val, 4)

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

        # Armor gives HP bonus (item: armor_hp_ratio)
        if attr == 'armor' and getattr(player, 'has_armor_gives_hp', False):
            hp_gain = int(gained * 100)
            if hp_gain > 0:
                player.max_hp += hp_gain
                player.current_hp = min(player.max_hp, player.current_hp + hp_gain)
                events.append({
                    'number': num, 'stat': 'max_hp', 'gained': hp_gain,
                    'threshold_bonus': False,
                    'desc': f'+{hp_gain} max HP (armor bonus)',
                })

        # Gold level bonus (item: gold_level_bonus)
        if attr == 'gold' and getattr(player, 'has_gold_level_bonus', False):
            player.gold += 10
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
