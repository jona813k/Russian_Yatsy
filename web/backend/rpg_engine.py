"""
RPG run orchestration — manages the full run lifecycle:
  pre_game_forge → upgrade → combat → shop/forge → ... → victory | game_over

Also contains the dice-roller and engine subclasses that make the upgrade phase
work with per-stat targets and the forge dice pool.
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / 'src'))

import uuid
import random
from datetime import datetime, timezone
from typing import Optional

from src.game.engine import GameEngine
from src.game.rules import GameRules
from src.models.player import Player
from src.models.game_state import GameState

from .data import LEVELS, SHOP_ITEMS, FORGE_LEVELS
from .player import PlayerStats, apply_upgrades
from .combat import simulate_combat, get_summon_stats


# ---------------------------------------------------------------------------
# Shop helpers
# ---------------------------------------------------------------------------

HEAL_POTION = {
    'id':   'heal_potion',
    'name': 'Heal Potion',
    'desc': 'Restore 50% of your missing HP.',
    'cost': 50,
    'icon': '🧪',
}


_STAT_NAMES = {
    1:'Speed', 2:'Damage', 3:'Crit', 4:'Armor', 5:'HP',
    8:'Summon', 9:'Spell', 10:'Block', 11:'Life Steal',
}

def generate_pre_game_forge() -> list:
    """
    Randomly generate 3 pre-game forge options: No Change + 2 randomly picked
    from the pool of Split Focus, Specialist, Drop X, Drop A.
      x, z, y, w  — 4 distinct stats from 1-5
      a, b        — 2 distinct stats from 8-11
    Stats 6 (Research), 7 (Gold), 12 (Dark) are excluded.
    """
    low  = random.sample([1, 2, 3, 4, 5], 4)   # x, z, y, w
    high = random.sample([8, 9, 10, 11],  2)    # a, b
    x, z, y, w = low
    a, b        = high

    def n(s): return _STAT_NAMES[s]

    pool = [
        {
            'id': 'opt_2', 'icon': '🔀',
            'name': 'Split Focus',
            'desc': f'{n(z)} & {n(x)}: cap at 5. {n(y)} & {n(w)}: cap at 7.',
            'stat_targets': {z: 5, x: 5, y: 7, w: 7},
            'stat_removed': [],
        },
        {
            'id': 'opt_3', 'icon': '🎯',
            'name': 'Specialist',
            'desc': f'{n(a)} & {n(b)}: cap at 5. {n(z)}, {n(y)} & {n(x)}: cap at 7.',
            'stat_targets': {a: 5, b: 5, z: 7, y: 7, x: 7},
            'stat_removed': [],
        },
        {
            'id': 'opt_4', 'icon': '❌',
            'name': f'Drop {n(x)}',
            'desc': f'{n(x)} removed. {n(a)}: cap at 4.',
            'stat_targets': {a: 4},
            'stat_removed': [x],
        },
        {
            'id': 'opt_5', 'icon': '🗑️',
            'name': f'Drop {n(a)}',
            'desc': f'{n(a)} removed. {n(x)} & {n(y)}: cap at 5.',
            'stat_targets': {x: 5, y: 5},
            'stat_removed': [a],
        },
    ]

    return [
        {
            'id': 'opt_1', 'icon': '⚖️',
            'name': 'No Change',
            'desc': 'All stats use the default target of 6.',
            'stat_targets': {}, 'stat_removed': [],
        },
        *random.sample(pool, 2),
    ]


def generate_shop_items(level_idx: int = 0, discount: bool = False) -> list:
    """Return 3 random tier-appropriate items + the always-available Heal Potion.
    The Gladiator Key is always included as a guaranteed slot."""
    tier = 1 if level_idx == 0 else 2
    key = next((i for i in SHOP_ITEMS if i['id'] == 'gladiator_key' and i['tier'] == tier), None)
    pool = [i for i in SHOP_ITEMS if i['tier'] == tier and i['id'] != 'gladiator_key']
    items = random.sample(pool, min(3, len(pool)))
    if key:
        items = [key] + items
    if discount:
        items = [{**i, 'cost': int(i['cost'] * 0.8)} for i in items]
    return [HEAL_POTION] + items


# ---------------------------------------------------------------------------
# Stateful dice roller
# ---------------------------------------------------------------------------

class StatefulDiceRoller:
    """
    Tracks which die types are in hand so that when dice are collected and the
    remainder is re-rolled, special dice (d12, d3, risky) are only included if
    they weren't part of the collection.

    Call prepare_for_collection(dice_values, target) BEFORE execute_action so
    the roller knows which types survive.
    """

    def __init__(self, player: PlayerStats):
        self._player   = player
        has_risky      = player.has_risky_die
        extra_12       = player.extra_d12
        extra_3        = player.extra_d3
        self._weighted = player.loaded_high
        self._plus_one = player.dice_plus_one
        base_d6 = max(0, 6 - player.removed_dice - (1 if has_risky else 0))

        self._full_pool: list[str] = (
            (['risky']  if has_risky               else []) +
            (['retry']  if player.has_retry_die    else []) +
            (['logic']  if player.has_logic_die    else []) +
            (['2_5']    if player.has_2_5_die      else []) +
            (['mirror'] if player.has_mirror_die   else []) +
            (['bomb']   if player.has_bomb_die     else []) +
            ['d12'] * extra_12 +
            ['d3']  * extra_3  +
            ['d6']  * base_d6
        )
        self._loaded_low = player.loaded_low
        self.total: int = len(self._full_pool)
        self._types_in_hand: list[str] = self._full_pool[:]

    def _roll_one(self, t: str) -> int:
        if t == 'risky': return random.choice([1, 2, 3, 10, 11, 12])
        if t == 'd12':   return random.randint(1, 12)
        if t == 'd3':    return random.randint(1, 3)
        if t == 'retry': return random.randint(1, 6)
        if t == 'bomb':  return random.randint(1, 6)
        if t == '2_5':   return random.choice([2, 5])
        if t == 'logic':
            val = (self._player.logic_die_pos % 6) + 1
            self._player.logic_die_pos += 1
            return val
        # Regular d6 (possibly weighted or +1)
        if self._weighted:
            # 2:1 ratio — high faces (4,5,6) each at 2/9 ≈ 22%, low faces (1,2,3) at 1/9 ≈ 11%
            r = random.randint(1, 9)
            if r <= 1:   v = 1
            elif r <= 2: v = 2
            elif r <= 3: v = 3
            elif r <= 5: v = 4
            elif r <= 7: v = 5
            else:        v = 6
        elif self._loaded_low:
            # 2:1 ratio — low faces (1,2,3) each at 2/9 ≈ 22%, high faces (4,5,6) at 1/9 ≈ 11%
            r = random.randint(1, 9)
            if r <= 2:   v = 1
            elif r <= 4: v = 2
            elif r <= 6: v = 3
            elif r <= 7: v = 4
            elif r <= 8: v = 5
            else:        v = 6
        else:
            v = random.randint(1, 6)
        return v + (1 if self._plus_one else 0)

    def prepare_for_collection(self, dice_values: list, target: int):
        """
        Called BEFORE the engine collects target from dice_values.
        Updates which types remain in hand after the collection.
        """
        pairs = list(zip(dice_values, self._types_in_hand))
        remaining = list(pairs)

        remaining = [(v, t) for (v, t) in remaining if v != target]

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
            self._types_in_hand = self._full_pool[:]
        # Roll all non-mirror dice first, then set mirror = max of others
        mirror_indices = [i for i, t in enumerate(self._types_in_hand) if t == 'mirror']
        if not mirror_indices:
            return [self._roll_one(t) for t in self._types_in_hand]
        values = [None if t == 'mirror' else self._roll_one(t) for t in self._types_in_hand]
        others = [v for v in values if v is not None]
        mirror_val = max(others) if others else 1
        for i in mirror_indices:
            values[i] = mirror_val
        return values

    @property
    def types_in_hand(self) -> list[str]:
        return list(self._types_in_hand)


# ---------------------------------------------------------------------------
# RPG-aware engine subclasses
# ---------------------------------------------------------------------------

class RPGPlayer(Player):
    """
    Player subclass with per-stat collection targets (set by the pre-game forge).
    Removed stats are pre-filled to 6 so the engine never offers them.
    """
    def __init__(self, name: str, stat_targets: dict, stat_removed: list):
        super().__init__(name)
        self._stat_targets = stat_targets
        for n in stat_removed:
            self.progress[n] = 6

    def target_for(self, number: int) -> int:
        return self._stat_targets.get(number, 6)

    def add_collected(self, number: int, count: int) -> bool:
        target = self.target_for(number)
        current = self.progress.get(number, 0)
        new_total = min(current + count, target)
        self.progress[number] = new_total
        return new_total >= target and current < target

    def is_winner(self) -> bool:
        # Never signal "won" — the RPG uses turn-based upgrade_done instead
        return False


class RPGUpgradeEngine(GameEngine):
    """
    GameEngine subclass that uses RPGPlayer so per-stat targets are respected
    in legal-action checks and completion detection.
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
            current_count = self.player.progress.get(target, 0)
            if current_count < stat_target and self._can_make_number(self.state.dice_values, target):
                collectible = self._count_collectible(self.state.dice_values, target)
                legal_actions.append({
                    'type': 'collect',
                    'number': target,
                    'collectible': collectible,
                    'progress': current_count,
                    'remaining_needed': stat_target - current_count,
                })
        return legal_actions

    def _execute_collect(self, target: int) -> dict:
        # Guard against collecting a stat that's already at its custom target
        if self.player.progress.get(target, 0) >= self._target_for(target):
            return {
                'success': False,
                'state': 'illegal',
                'info': {'error': f'{target} already completed'},
            }
        return super()._execute_collect(target)


# ---------------------------------------------------------------------------
# Run state
# ---------------------------------------------------------------------------

class RPGRun:
    def __init__(self, name: str = 'Anonymous'):
        self.run_id           = str(uuid.uuid4())
        self.name             = name
        self.player           = PlayerStats()
        self.level_idx        = 0
        self.fight_idx        = 0
        self.phase            = 'pre_game_forge'
        self.pre_game_forge_choices = generate_pre_game_forge()
        self.upgrade_engine   = None
        self.stat_targets: dict = {}
        self.stat_removed: list = []
        self.upgrade_turns_used  = 0
        self.upgrade_done        = False
        self.last_combat         = None
        self.last_upgrades       = []
        self.shop_items          = []
        self.owned_items         = []
        self.forge_choices       = []
        self.free_reroll_available  = False
        self.retry_die_available    = False
        self._bomb_stash_pending: int | None = None  # bomb die value captured before turn-ending action
        self._summon_hp_carry: int  = None
        self._shop_reroll_used: bool = False
        self.total_collections: dict = {n: 0 for n in range(1, 13)}
        self.forge_history: list     = []
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
        p = self.player
        return max(1, 6 - p.removed_dice + p.extra_d12 + p.extra_d3
                   + (1 if p.has_retry_die  else 0)
                   + (1 if p.has_logic_die  else 0)
                   + (1 if p.has_2_5_die    else 0)
                   + (1 if p.has_mirror_die else 0)
                   + (1 if p.has_bomb_die   else 0))

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
        self.retry_die_available   = self.player.has_retry_die

    def handle_action_result(self, result: dict):
        """Call after every upgrade action to track turn usage."""
        state = result.get('state')
        if state == 'turn_end':
            # Bomb die auto-stash: if bomb die wasn't collected, stash its value now
            if self._bomb_stash_pending is not None:
                self._auto_collect_bomb_value(self._bomb_stash_pending)
                self._bomb_stash_pending = None
            self.upgrade_turns_used += 1
            if self.upgrade_turns_used >= self.upgrade_turns_max:
                self.upgrade_done = True
            self.free_reroll_available = self.player.has_free_reroll
            self.retry_die_available   = self.player.has_retry_die
        elif state == 'completed_number':
            self._bomb_stash_pending = None
            self.free_reroll_available = self.player.has_free_reroll
            self.retry_die_available   = self.player.has_retry_die

    def finish_upgrade(self) -> list:
        """Apply stat upgrades and advance to combat phase."""
        collections = {n: self.upgrade_engine.player.progress.get(n, 0) for n in range(1, 13)}
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
        has_bounty_50g = 'bounty_50g' in item_ids

        combat = simulate_combat(self.player, self.current_enemy, self.owned_items)
        self.last_combat = combat

        if has_bounty_50g and combat['result'] == 'win':
            self.player.gold += 50

        self._summon_hp_carry = None

        if combat['result'] == 'lose':
            self.phase = 'game_over'
        else:
            self.player.current_hp = combat['player_hp_remaining']
            if self.current_enemy['is_boss']:
                if self.level_idx >= 2:
                    self.phase = 'victory'
                else:
                    self._init_forge()
                    self.phase = 'forge'
            else:
                self.fight_idx += 1
                next_enemy = LEVELS[self.level_idx]['enemies'][self.fight_idx]
                if next_enemy['is_boss']:
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
        item = next((i for i in self.shop_items if i['id'] == item_id), None)
        if not item:
            return False, 'item not found'

        if item_id == 'heal_potion':
            if self.player.gold < item['cost']:
                return False, 'not enough gold'
            heal = (self.player.max_hp - self.player.current_hp) // 2
            self.player.current_hp += heal
            self.player.gold -= item['cost']
            return True, 'ok'

        if item_id == 'gladiator_key':
            if self.player.has_gladiator_key:
                return False, 'already have the Gladiator Key'
            if self.player.gold < item['cost']:
                return False, 'not enough gold'
            self.player.gold -= item['cost']
            self.player.has_gladiator_key = True
            self.shop_items = [i for i in self.shop_items if i['id'] != item_id]
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
        elif iid == 'gladiator_key':
            p.has_gladiator_key = True

        self.owned_items.append(item)
        self.shop_items = [i for i in self.shop_items if i['id'] != item_id]
        return True, 'ok'

    def reroll_shop(self) -> tuple[bool, str]:
        REROLL_COST = 30
        use_free = self.player.has_shop_free_reroll and not self._shop_reroll_used
        if not use_free:
            if self.player.gold < REROLL_COST:
                return False, 'not enough gold'
            self.player.gold -= REROLL_COST
        self._shop_reroll_used = True
        self.shop_items = generate_shop_items(self.level_idx, self.player.has_item_discount)
        return True, 'ok'

    def close_shop(self):
        if self.phase == 'pre_boss_shop':
            self.phase = 'combat'
        else:
            self.level_idx += 1
            self.fight_idx = 0
            self.phase = 'upgrade'
            self._init_upgrade_phase()

    # ------------------------------------------------------------------
    # Pre-game forge
    # ------------------------------------------------------------------

    def pick_pre_game_forge(self, choice_id: str) -> tuple[bool, str]:
        choice = next((c for c in self.pre_game_forge_choices if c['id'] == choice_id), None)
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
        forge_idx = self.level_idx
        if forge_idx < len(FORGE_LEVELS):
            pool = FORGE_LEVELS[forge_idx]
            # Both forges have a pool of 6 — randomly pick 3 each run
            if len(pool) > 3:
                self.forge_choices = random.sample(pool, 3)
            else:
                self.forge_choices = pool
        else:
            self.forge_choices = []

    def pick_forge(self, choice_id: str) -> tuple[bool, str]:
        choice = next((c for c in self.forge_choices if c['id'] == choice_id), None)
        if not choice:
            return False, 'invalid choice'

        p = self.player
        effect = choice['id']
        if effect == 'add_d12':
            p.extra_d12 += 1
        elif effect == 'add_d3':
            p.extra_d3 += 1
        elif effect == 'remove_die':
            p.removed_dice = min(p.removed_dice + 1, 5)
        elif effect == 'loaded_high':
            p.loaded_high = True
        elif effect == 'free_reroll':
            p.has_free_reroll = True
        elif effect == 'risky_die':
            p.has_risky_die = True
        elif effect == 'dice_plus_one':
            p.dice_plus_one = True
        elif effect == 'add_2_5_die':
            p.has_2_5_die = True
        elif effect == 'add_retry_die':
            p.has_retry_die = True
        elif effect == 'add_logic_die':
            p.has_logic_die = True
        elif effect == 'loaded_low':
            p.loaded_low = True
        elif effect == 'add_mirror_die':
            p.has_mirror_die = True
        elif effect == 'add_bomb_die':
            p.has_bomb_die = True

        self.forge_history.append(choice['id'])
        self.level_idx += 1
        self.fight_idx = 0
        self.forge_choices = []
        self.phase = 'upgrade'
        self._init_upgrade_phase()
        return True, 'ok'

    def use_free_reroll(self) -> bool:
        if not self.free_reroll_available:
            return False
        if self.upgrade_engine.state.selected_number is not None:
            return False
        self.free_reroll_available = False
        n = self.upgrade_engine._num_dice
        self.upgrade_engine.state.dice_values = self.upgrade_engine._roll_fn(n)
        self.upgrade_engine.state.num_dice_in_hand = n
        self.upgrade_engine.total_rolls += 1
        return True

    def use_retry_die_reroll(self) -> bool:
        """Reroll only the retry die. Available once per turn, requires retry die selected alone."""
        if not self.retry_die_available:
            return False
        if self.upgrade_engine.state.selected_number is not None:
            return False
        types = self._dice_roller.types_in_hand
        retry_idx = next((i for i, t in enumerate(types) if t == 'retry'), None)
        if retry_idx is None:
            return False  # retry die was already collected this turn
        new_value = self._dice_roller._roll_one('retry')
        self.upgrade_engine.state.dice_values[retry_idx] = new_value
        self.retry_die_available = False
        self.upgrade_engine.total_rolls += 1
        return True

    def note_bomb_die_value(self):
        """
        Capture the bomb die's current value BEFORE prepare_for_collection / execute_action.
        If the bomb die is later consumed by the collection, the caller should clear this.
        """
        if not self.player.has_bomb_die:
            self._bomb_stash_pending = None
            return
        types = self._dice_roller.types_in_hand
        bomb_idx = next((i for i, t in enumerate(types) if t == 'bomb'), None)
        self._bomb_stash_pending = (
            self.upgrade_engine.state.dice_values[bomb_idx]
            if bomb_idx is not None else None
        )

    def _auto_collect_bomb_value(self, val: int):
        """Add 1 to the bomb die's value in upgrade progress (respects targets and removals)."""
        if val not in range(1, 13) or val in self.stat_removed:
            return
        target = self.stat_targets.get(val, 6)
        current = self.upgrade_engine.player.progress.get(val, 0)
        if current < target:
            self.upgrade_engine.player.progress[val] = current + 1

    # ------------------------------------------------------------------
    # History / serialisation
    # ------------------------------------------------------------------

    def to_summary(self) -> dict:
        outcome = 'win' if self.phase == 'victory' else 'lose'
        return {
            'run_id':        self.run_id,
            'name':          self.name,
            'timestamp':     self.started_at or datetime.now(timezone.utc).isoformat(),
            'outcome':       outcome,
            'level_reached': self.level_idx + 1 if outcome == 'lose' else 3,
            'fight_reached': self.fight_idx + 1 if outcome == 'lose' else 3,
            'end_stats':     self.player.to_dict(),
            'collections':   {str(n): self.total_collections.get(n, 0) for n in range(1, 13)},
            'forges':        list(self.forge_history),
            'items':         [i['id']   for i in self.owned_items],
            'item_names':    [i['name'] for i in self.owned_items],
        }

    def _upgrade_status(self, li, fi):
        if li < self.level_idx: return 'done'
        if li > self.level_idx: return 'upcoming'
        if fi < self.fight_idx: return 'done'
        if fi > self.fight_idx: return 'upcoming'
        if self.phase == 'pre_game_forge': return 'upcoming'
        if self.phase == 'upgrade' and not self.upgrade_done: return 'current'
        return 'done'

    def _fight_status(self, li, fi):
        if li < self.level_idx: return 'done'
        if li > self.level_idx: return 'upcoming'
        if fi < self.fight_idx: return 'done'
        if fi > self.fight_idx: return 'upcoming'
        if self.phase == 'combat': return 'current'
        if self.phase in ('forge', 'game_over', 'victory'): return 'done'
        return 'upcoming'

    def _pre_boss_shop_status(self, li):
        if li < self.level_idx: return 'done'
        if li > self.level_idx: return 'upcoming'
        if self.phase == 'pre_boss_shop': return 'current'
        boss_fi = next(i for i, e in enumerate(LEVELS[li]['enemies']) if e['is_boss'])
        if self.fight_idx >= boss_fi and self.phase not in ('upgrade',): return 'done'
        return 'upcoming'

    def _forge_status(self, li):
        if li < self.level_idx: return 'done'
        if li > self.level_idx: return 'upcoming'
        if self.phase == 'forge': return 'current'
        return 'upcoming'

    def _build_path(self) -> list:
        nodes = []
        for li, lvl in enumerate(LEVELS):
            for fi, enemy in enumerate(lvl['enemies']):
                if enemy['is_boss']:
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
            'run_id':                 self.run_id,
            'name':                   self.name,
            'phase':                  'upgrade_done' if (self.phase == 'upgrade' and self.upgrade_done) else self.phase,
            'stat_targets':           self.stat_targets,
            'stat_removed':           self.stat_removed,
            'pre_game_forge_choices': self.pre_game_forge_choices if self.phase == 'pre_game_forge' else [],
            'level':                  self.level_idx + 1,
            'fight_index':            self.fight_idx,
            'is_boss':                enemy['is_boss'] if enemy else False,
            'enemy':                  enemy,
            'upgrade_turns_used':     self.upgrade_turns_used,
            'upgrade_turns_max':      self.upgrade_turns_max,
            'upgrade_pool_size':      self.upgrade_pool_size,
            'upgrade_done':           self.upgrade_done,
            'free_reroll_available':  self.free_reroll_available,
            'retry_die_available':    self.retry_die_available,
            'player':                 self.player.to_dict(),
            'summon_stats':           get_summon_stats(self.player.summon_level),
            'yatzy':                  yatzy_state,
            'last_combat':            self.last_combat,
            'last_upgrades':          self.last_upgrades,
            'shop_items':             self.shop_items if self.phase in shop_phases else [],
            'owned_items':            self.owned_items,
            'forge_choices':          self.forge_choices if self.phase == 'forge' else [],
            'path':                   self._build_path(),
        }
