"""
Game engine — enforces rules and exposes legal actions for each turn.
"""
from src.models.game_state import GameState
from src.models.player import Player
from src.game.rules import GameRules
from src.utils.helpers import roll_dice


class GameEngine:
    """
    Single-player game engine.  The frontend drives play by calling:
      - get_legal_actions()   → list of legal moves
      - execute_action(action) → result dict + auto-rolls remaining dice
    """

    def __init__(self, num_dice: int = None, roll_fn=None):
        self._num_dice = num_dice if num_dice is not None else GameRules.NUM_DICE
        self._roll_fn = roll_fn if roll_fn is not None else roll_dice
        self.state = GameState()
        self.player = Player("Player")
        self.state.players = [self.player]
        self.state.current_player_index = 0
        self.turn_number = 0
        self.total_rolls = 0

    def reset(self):
        """Reset for a new game."""
        self.player = Player("Player")
        self.state = GameState()
        self.state.players = [self.player]
        self.state.current_player_index = 0
        self.turn_number = 0
        self.total_rolls = 0
        self.start_new_turn()

    def start_new_turn(self):
        """Roll all dice and begin a new turn."""
        self.state.selected_number = None
        self.state.collected_this_turn = 0
        self.state.num_dice_in_hand = self._num_dice
        self.state.dice_values = self._roll_fn(self._num_dice)
        self.turn_number += 1
        self.total_rolls += 1

    # ------------------------------------------------------------------
    # Legal-action helpers
    # ------------------------------------------------------------------

    def get_legal_actions(self) -> list:
        """Return all moves the player may make right now."""
        legal_actions = []

        if self.state.selected_number is None:
            # Free to choose any makeable, incomplete number
            for target in range(GameRules.MIN_NUMBER, GameRules.MAX_NUMBER + 1):
                if self._can_make_number(self.state.dice_values, target):
                    current_count = self.player.progress.get(target, 0)
                    if current_count < GameRules.TARGET_PER_NUMBER:
                        collectible = self._count_collectible(self.state.dice_values, target)
                        legal_actions.append({
                            'type': 'select',
                            'number': target,
                            'collectible': collectible,
                            'progress': current_count,
                            'remaining_needed': GameRules.TARGET_PER_NUMBER - current_count,
                        })

            if not legal_actions:
                legal_actions.append({
                    'type': 'skip_turn',
                    'reason': 'no_valid_numbers',
                })
        else:
            # Number locked-in — must keep collecting it
            target = self.state.selected_number
            if self._can_make_number(self.state.dice_values, target):
                collectible = self._count_collectible(self.state.dice_values, target)
                legal_actions.append({
                    'type': 'collect',
                    'number': target,
                    'collectible': collectible,
                    'progress': self.player.progress.get(target, 0),
                    'remaining_needed': GameRules.TARGET_PER_NUMBER - self.player.progress.get(target, 0),
                })

        return legal_actions

    # ------------------------------------------------------------------
    # Action execution
    # ------------------------------------------------------------------

    def execute_action(self, action: dict) -> dict:
        """
        Execute a legal action and return a result dict:
            state   : 'continue' | 'completed_number' | 'turn_end' | 'bonus_turn' | 'won'
            success : bool
            info    : dict with collected count, reason, etc.
        """
        if action['type'] in ('select', 'collect'):
            return self._execute_collect(action['number'])
        elif action['type'] == 'skip_turn':
            self.start_new_turn()
            return {
                'success': True,
                'state': 'turn_end',
                'info': {'reason': 'forced_skip', 'message': 'No valid numbers to collect'},
            }
        else:
            return {
                'success': False,
                'state': 'illegal',
                'info': {'error': 'Invalid action type'},
            }

    def _execute_collect(self, target: int) -> dict:
        """Collect all matching dice for *target* and advance game state."""
        if not self._can_make_number(self.state.dice_values, target):
            return {
                'success': False,
                'state': 'illegal',
                'info': {'error': f'Cannot make {target} from dice'},
            }

        if self.player.progress.get(target, 0) >= GameRules.TARGET_PER_NUMBER:
            return {
                'success': False,
                'state': 'illegal',
                'info': {'error': f'{target} already completed'},
            }

        if self.state.selected_number is None:
            self.state.selected_number = target

        collected, remaining_dice = self._collect_all_matches(target)

        if collected == 0:
            return {
                'success': False,
                'state': 'error',
                'info': {'error': 'No matches found'},
            }

        self.state.collected_this_turn += collected
        self.state.dice_values = remaining_dice
        self.state.num_dice_in_hand = len(remaining_dice)

        was_completed = self.player.add_collected(target, collected)

        if was_completed:
            if self.player.is_winner():
                return {
                    'success': True,
                    'state': 'won',
                    'info': {
                        'collected': collected,
                        'completed': target,
                        'total_turns': self.turn_number,
                        'total_rolls': self.total_rolls,
                    },
                }

            # Number completed → fresh roll with all dice
            self.state.selected_number = None
            self.state.collected_this_turn = 0
            self.state.num_dice_in_hand = self._num_dice
            self.state.dice_values = self._roll_fn(self._num_dice)
            self.total_rolls += 1

            return {
                'success': True,
                'state': 'completed_number',
                'info': {
                    'collected': collected,
                    'completed': target,
                    'new_dice': self.state.dice_values,
                },
            }

        if self.state.num_dice_in_hand > 0:
            self.state.dice_values = self._roll_fn(self.state.num_dice_in_hand)
            self.total_rolls += 1

            if self._can_make_number(self.state.dice_values, target):
                return {
                    'success': True,
                    'state': 'continue',
                    'info': {
                        'collected': collected,
                        'remaining_dice': self.state.num_dice_in_hand,
                    },
                }
            else:
                failed_dice = list(self.state.dice_values)
                self.start_new_turn()
                return {
                    'success': True,
                    'state': 'turn_end',
                    'info': {
                        'collected': collected,
                        'reason': 'no_matches',
                        'failed_dice': failed_dice,
                    },
                }
        else:
            # All dice used without completing — bonus turn
            self.start_new_turn()
            return {
                'success': True,
                'state': 'bonus_turn',
                'info': {
                    'collected': collected,
                    'all_dice_used': True,
                },
            }

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _can_make_number(self, dice: list, target: int) -> bool:
        if target in dice:
            return True
        return len(GameRules.find_valid_combinations(dice, target)) > 0

    def _count_collectible(self, dice: list, target: int) -> int:
        count = dice.count(target)
        remaining = list(dice)
        for _ in range(count):
            remaining.remove(target)
        combos = GameRules.find_valid_combinations(remaining, target)
        return count + len(combos)

    def _collect_all_matches(self, target: int) -> tuple:
        """Return (count_collected, remaining_dice)."""
        collected = 0
        remaining_dice = list(self.state.dice_values)

        single_count = remaining_dice.count(target)
        if single_count > 0:
            collected += single_count
            remaining_dice = [d for d in remaining_dice if d != target]

        combinations = GameRules.find_valid_combinations(remaining_dice, target)
        if combinations:
            collected += len(combinations)
            for combo in combinations:
                for die_value in combo:
                    remaining_dice.remove(die_value)

        return collected, remaining_dice

    # ------------------------------------------------------------------
    # State queries
    # ------------------------------------------------------------------

    def get_game_info(self) -> dict:
        return {
            'turns': self.turn_number,
            'rolls': self.total_rolls,
            'progress': dict(self.player.progress),
            'completed': [n for n in range(1, 13) if self.player.progress.get(n, 0) >= 6],
            'is_won': self.player.is_winner(),
        }

    def is_game_over(self) -> bool:
        return self.player.is_winner()
