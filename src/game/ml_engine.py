"""
ML Training Engine - Enforces game rules for ML agent training
"""
from src.models.game_state import GameState
from src.models.player import Player
from src.game.rules import GameRules
from src.utils.helpers import roll_dice
import random
import math


class MLGameEngine:
    """
    Game engine specifically designed for ML training.
    Enforces all rules and only provides legal actions.
    """
    
    def __init__(self, num_dice: int = None, roll_fn=None):
        self._num_dice = num_dice if num_dice is not None else GameRules.NUM_DICE
        self._roll_fn = roll_fn if roll_fn is not None else roll_dice
        self.state = GameState()
        self.player = Player("ML_Agent")
        self.state.players = [self.player]
        self.state.current_player_index = 0
        self.turn_number = 0
        self.total_rolls = 0

    def reset(self):
        """Reset for new game"""
        self.player = Player("ML_Agent")
        self.state = GameState()
        self.state.players = [self.player]
        self.state.current_player_index = 0
        self.turn_number = 0
        self.total_rolls = 0
        self.start_new_turn()

    def start_new_turn(self):
        """Start a new turn with fresh dice"""
        self.state.selected_number = None
        self.state.collected_this_turn = 0
        self.state.num_dice_in_hand = self._num_dice
        self.state.dice_values = self._roll_fn(self._num_dice)
        self.turn_number += 1
        self.total_rolls += 1
    
    def get_legal_actions(self) -> list:
        """
        Get all legal actions from current state.
        ML agent can ONLY choose from these.
        """
        legal_actions = []
        
        # If no number selected yet, can choose any makeable number
        if self.state.selected_number is None:
            for target in range(GameRules.MIN_NUMBER, GameRules.MAX_NUMBER + 1):
                # Check if we can make this number
                if self._can_make_number(self.state.dice_values, target):
                    # Check if not completed yet
                    current_count = self.player.progress.get(target, 0)
                    if current_count < GameRules.TARGET_PER_NUMBER:
                        collectible = self._count_collectible(self.state.dice_values, target)
                        legal_actions.append({
                            'type': 'select',
                            'number': target,
                            'collectible': collectible,
                            'progress': current_count,
                            'remaining_needed': GameRules.TARGET_PER_NUMBER - current_count
                        })
            
            # If NO legal actions (bad dice roll), allow "skip" action to end turn
            if not legal_actions:
                legal_actions.append({
                    'type': 'skip_turn',
                    'reason': 'no_valid_numbers'
                })
        else:
            # Number already selected - must continue collecting it
            target = self.state.selected_number
            if self._can_make_number(self.state.dice_values, target):
                collectible = self._count_collectible(self.state.dice_values, target)
                legal_actions.append({
                    'type': 'collect',
                    'number': target,
                    'collectible': collectible,
                    'progress': self.player.progress.get(target, 0),
                    'remaining_needed': GameRules.TARGET_PER_NUMBER - self.player.progress.get(target, 0)
                })
            # If can't continue with selected number, turn automatically ends (handled in execute_action)
        
        return legal_actions
    
    def execute_action(self, action: dict) -> dict:
        """
        Execute an action and return result.
        
        Returns dict with:
            - success: bool
            - reward: float
            - state: str ('continue', 'completed_number', 'turn_end', 'won')
            - info: dict with additional info
        """
        if action['type'] == 'select':
            return self._execute_select_and_collect(action['number'])
        elif action['type'] == 'collect':
            # Continue collecting already selected number
            return self._execute_select_and_collect(action['number'])
        elif action['type'] == 'skip_turn':
            # No valid actions - forced turn end
            # Penalty for wasting a turn (constant, not scaled)
            self.start_new_turn()
            return {
                'success': True,
                'reward': -10.0,  # Moderate penalty for wasted turn
                'state': 'turn_end',
                'info': {'reason': 'forced_skip', 'message': 'No valid numbers to collect'}
            }
        else:
            return {
                'success': False,
                'reward': -1000,
                'state': 'illegal',
                'info': {'error': 'Invalid action type'}
            }
    
    def _execute_select_and_collect(self, target: int) -> dict:
        """Select number and automatically collect all matches"""
        # Validate
        if not self._can_make_number(self.state.dice_values, target):
            return {
                'success': False,
                'reward': -100,
                'state': 'illegal',
                'info': {'error': f'Cannot make {target} from dice'}
            }
        
        if self.player.progress.get(target, 0) >= GameRules.TARGET_PER_NUMBER:
            return {
                'success': False,
                'reward': -100,
                'state': 'illegal',
                'info': {'error': f'{target} already completed'}
            }
        
        # Set selected number (if not already set)
        if self.state.selected_number is None:
            self.state.selected_number = target
        
        # Count how many we can collect
        collectible_count = self._count_collectible(self.state.dice_values, target)
        
        # === SIMPLE REWARD STRUCTURE (Original - Proven to Work) ===
        # Keep it simple: no conflicting bonuses, clear signals
        
        # Collect all matches
        collected, remaining_dice = self._collect_all_matches(target)
        
        if collected == 0:
            # Shouldn't happen if validation correct
            return {
                'success': False,
                'reward': -50,
                'state': 'error',
                'info': {'error': 'No matches found'}
            }
        
        # Calculate reward - simple and clear
        reward = collected * 10  # Base reward: 10 points per die collected
        
        # Update state
        self.state.collected_this_turn += collected
        self.state.dice_values = remaining_dice
        self.state.num_dice_in_hand = len(remaining_dice)
        
        # Update player progress
        was_completed = self.player.add_collected(target, collected)
        
        if was_completed:
            # Completed this number! Big bonus
            reward += 100
            
            # Check if won
            if self.player.is_winner():
                # Simple linear efficiency bonus - rewards faster wins
                efficiency_bonus = max(0, (100 - self.turn_number) * 5)
                
                return {
                    'success': True,
                    'reward': reward + 1000 + efficiency_bonus,
                    'state': 'won',
                    'info': {
                        'collected': collected,
                        'completed': target,
                        'total_turns': self.turn_number,
                        'total_rolls': self.total_rolls
                    }
                }
            
            # Number completed, can select new number with all dice back
            self.state.selected_number = None
            self.state.collected_this_turn = 0
            self.state.num_dice_in_hand = self._num_dice
            self.state.dice_values = self._roll_fn(self._num_dice)
            self.total_rolls += 1
            
            return {
                'success': True,
                'reward': reward,
                'state': 'completed_number',
                'info': {
                    'collected': collected,
                    'completed': target,
                    'new_dice': self.state.dice_values
                }
            }
        
        # Continue with remaining dice
        if self.state.num_dice_in_hand > 0:
            # Roll remaining dice
            self.state.dice_values = self._roll_fn(self.state.num_dice_in_hand)
            self.total_rolls += 1
            
            # Check if can continue
            if self._can_make_number(self.state.dice_values, target):
                # Can continue collecting same number
                return {
                    'success': True,
                    'reward': reward,
                    'state': 'continue',
                    'info': {
                        'collected': collected,
                        'remaining_dice': self.state.num_dice_in_hand,
                        'can_continue': True
                    }
                }
            else:
                # No more matches - turn ends without completing number
                # Capture the failed dice BEFORE resetting so the frontend can show them
                failed_dice = list(self.state.dice_values)
                self.start_new_turn()
                return {
                    'success': True,
                    'reward': reward - 2.0,
                    'state': 'turn_end',
                    'info': {
                        'collected': collected,
                        'reason': 'no_matches',
                        'failed_dice': failed_dice,  # dice that were rolled but didn't match
                    }
                }
        else:
            # Used all dice without completing - bonus turn!
            reward += 50
            self.start_new_turn()
            return {
                'success': True,
                'reward': reward,
                'state': 'bonus_turn',
                'info': {
                    'collected': collected,
                    'all_dice_used': True
                }
            }
    
    def _can_make_number(self, dice: list, target: int) -> bool:
        """Check if target can be made from dice"""
        # Singles: any die showing exactly target
        if target in dice:
            return True
        # Combinations (pairs that sum to target)
        return len(GameRules.find_valid_combinations(dice, target)) > 0
    
    def _count_collectible(self, dice: list, target: int) -> int:
        """Count how many dice can be collected for target"""
        # Singles: dice showing exactly target
        count = dice.count(target)

        # Combinations (pairs that sum to target, using remaining dice)
        remaining = list(dice)
        for _ in range(count):
            remaining.remove(target)
        combos = GameRules.find_valid_combinations(remaining, target)
        count += len(combos)

        return count
    
    def _collect_all_matches(self, target: int) -> tuple:
        """
        Collect all matching dice for target.
        Returns (count_collected, remaining_dice)
        """
        collected = 0
        remaining_dice = list(self.state.dice_values)
        
        # Collect singles first
        single_count = remaining_dice.count(target)
        if single_count > 0:
            collected += single_count
            remaining_dice = [d for d in remaining_dice if d != target]
        
        # Collect combinations
        combinations = GameRules.find_valid_combinations(remaining_dice, target)
        if combinations:
            collected += len(combinations)
            # Remove used dice
            for combo in combinations:
                for die_value in combo:
                    remaining_dice.remove(die_value)
        
        return collected, remaining_dice
    
    def _binomial_prob(self, n: int, k: int, p: float) -> float:
        """Calculate binomial probability P(X = k)"""
        if k > n or k < 0:
            return 0.0
        if k == 0:
            return (1 - p) ** n
        if k == n:
            return p ** n
        
        coeff = math.factorial(n) // (math.factorial(k) * math.factorial(n - k))
        return coeff * (p ** k) * ((1 - p) ** (n - k))
    
    def _calculate_rarity_score(self, target: int, count: int, dice_count: int) -> float:
        """
        Calculate how rare/valuable this combination is (mimics probability strategy).
        Higher score = rarer = more valuable.
        """
        if count == 0:
            return 0.0
        
        # Calculate probability of getting this combination
        if target <= 6:
            # Singles: probability of getting 'count' of target in current dice
            prob = self._binomial_prob(dice_count, count, 1/6)
        else:
            # Pairs: approximate probability (each specific pair ~27% chance)
            prob = (0.27 ** count)
        
        # Rarity = inverse probability (capped for numerical stability)
        rarity = 1.0 / (prob + 0.001)
        
        return min(rarity, 1000.0)
    
    def _calculate_completion_urgency(self, target: int) -> float:
        """
        Calculate how urgent it is to complete this number.
        Returns multiplier (1.0-2.5) based on progress.
        """
        current = self.player.progress.get(target, 0)
        
        if current == 0:
            return 1.0  # Normal priority
        elif current >= 5:
            return 2.5  # Very close! High priority to complete
        elif current >= 3:
            return 1.8  # Good progress, prioritize
        elif current >= 1:
            return 1.3  # Some progress
        else:
            return 1.0
    
    def _calculate_endgame_bonus(self) -> float:
        """
        Calculate multiplier for being close to winning.
        Encourages finishing the game efficiently.
        """
        completed = sum(1 for count in self.player.progress.values() if count >= 6)
        
        if completed >= 10:
            return 3.0  # 2 numbers left - huge urgency!
        elif completed >= 8:
            return 2.0  # 4 numbers left - high urgency
        elif completed >= 6:
            return 1.5  # Half done - moderate urgency
        else:
            return 1.0  # Early game
    
    def get_state_representation(self) -> tuple:
        """
        Get hashable state representation for Q-learning.
        Returns tuple that can be used as dictionary key.
        """
        # Dice values (sorted for consistency)
        dice_tuple = tuple(sorted(self.state.dice_values))

        # Progress (which numbers completed/partial)
        progress_tuple = tuple(
            self.player.progress.get(i, 0)
            for i in range(GameRules.MIN_NUMBER, GameRules.MAX_NUMBER + 1)
        )

        # Selected number (if any)
        selected = self.state.selected_number if self.state.selected_number else 0

        # Number of dice in hand
        num_dice = self.state.num_dice_in_hand

        return (dice_tuple, progress_tuple, selected, num_dice)

    def get_rich_state(self) -> dict:
        """
        Get decision-ready state for DQN v2.

        Instead of raw dice values, pre-computes how many dice can be
        collected for each number right now. This is the information a
        human expert actually reasons about, so the network skips the
        arithmetic and goes straight to strategy.

        Returns:
            dict with keys:
                collectibles : list[int], len 12 — dice collectable per number
                progress     : list[int], len 12 — current progress per number
                selected     : int — locked-in number (0 = free to choose)
                num_dice     : int — dice remaining in hand this turn
        """
        collectibles = []
        for n in range(GameRules.MIN_NUMBER, GameRules.MAX_NUMBER + 1):
            if self.player.progress.get(n, 0) >= GameRules.TARGET_PER_NUMBER:
                collectibles.append(0)  # already completed, not a valid target
            else:
                collectibles.append(self._count_collectible(self.state.dice_values, n))

        progress = [
            self.player.progress.get(n, 0)
            for n in range(GameRules.MIN_NUMBER, GameRules.MAX_NUMBER + 1)
        ]

        return {
            'collectibles': collectibles,
            'progress': progress,
            'selected': self.state.selected_number or 0,
            'num_dice': self.state.num_dice_in_hand,
            'turn_number': self.turn_number,
        }
    
    def get_game_info(self) -> dict:
        """Get current game information"""
        return {
            'turns': self.turn_number,
            'rolls': self.total_rolls,
            'progress': dict(self.player.progress),
            'completed': [n for n in range(1, 13) if self.player.progress.get(n, 0) >= 6],
            'is_won': self.player.is_winner()
        }
    
    def is_game_over(self) -> bool:
        """Check if game is won"""
        return self.player.is_winner()
