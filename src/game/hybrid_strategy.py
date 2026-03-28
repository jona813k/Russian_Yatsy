"""
Hybrid Strategy: Combines probability-based rarity with ML learning.

This strategy uses probability calculations for action selection (like ProbabilityStrategy)
but wraps it in an ML framework to learn refinements and long-term patterns.
"""

from typing import List, Tuple, Optional
import numpy as np
from game.game_logic import roll_dice, GameRules
from game.ai_strategy import ProbabilityStrategy


class HybridMLStrategy:
    """
    Uses probability strategy as a base but learns to adjust its decisions.
    
    The idea: Start with good domain knowledge (probability), then learn improvements.
    """
    
    def __init__(self, learning_rate=0.1, exploration_rate=0.1):
        self.prob_strategy = ProbabilityStrategy()
        self.learning_rate = learning_rate
        self.exploration_rate = exploration_rate
        
        # Learn adjustment weights for different game states
        # Format: (numbers_completed, avg_progress) -> adjustment_multiplier
        self.state_adjustments = {}
        
    def get_state_key(self, progress: dict) -> tuple:
        """Get simplified state representation"""
        completed = sum(1 for count in progress.values() if count >= 6)
        total_progress = sum(progress.values())
        avg_progress = total_progress / 12.0
        
        # Bucket into discrete states
        completed_bucket = min(completed, 10)  # 0-10
        progress_bucket = int(avg_progress)  # 0-6
        
        return (completed_bucket, progress_bucket)
    
    def get_adjustment(self, progress: dict) -> float:
        """Get learned adjustment for this state"""
        state_key = self.get_state_key(progress)
        return self.state_adjustments.get(state_key, 1.0)
    
    def update_adjustment(self, state_key: tuple, reward: float):
        """Update adjustment based on outcome"""
        current = self.state_adjustments.get(state_key, 1.0)
        
        # If reward is positive (good turn), increase weight
        # If negative (bad turn), decrease weight
        adjustment = self.learning_rate * (reward / 100.0)  # Normalize reward
        new_value = current + adjustment
        
        # Keep in reasonable range [0.5, 2.0]
        new_value = max(0.5, min(2.0, new_value))
        
        self.state_adjustments[state_key] = new_value
    
    def select_number_and_collect(
        self, 
        dice: List[int], 
        progress: dict,
        explore: bool = True
    ) -> Optional[int]:
        """
        Select number using probability strategy + learned adjustments.
        
        Args:
            dice: Current dice values
            progress: Current progress toward each number
            explore: Whether to use exploration
            
        Returns:
            Selected number or None
        """
        # Exploration: occasionally try random number
        if explore and np.random.random() < self.exploration_rate:
            available = [n for n in range(1, 13) if progress.get(n, 0) < 6]
            if available:
                return np.random.choice(available)
        
        # Get probability strategy's evaluation
        prob_choices = self.prob_strategy.evaluate_all_options(dice, progress)
        
        if not prob_choices:
            return None
        
        # Apply learned adjustments
        state_key = self.get_state_key(progress)
        adjustment = self.get_adjustment(progress)
        
        # Adjust scores based on learned state weights
        adjusted_choices = []
        for number, value in prob_choices:
            # Get individual number progress
            num_progress = progress.get(number, 0)
            
            # Bonus for numbers close to completion
            completion_bonus = 1.0
            if num_progress >= 5:
                completion_bonus = 2.0
            elif num_progress >= 3:
                completion_bonus = 1.5
            
            # Apply both learned adjustment and completion bonus
            adjusted_value = value * adjustment * completion_bonus
            adjusted_choices.append((number, adjusted_value))
        
        # Select best adjusted choice
        best_number = max(adjusted_choices, key=lambda x: x[1])[0]
        return best_number


class HybridMLAgent:
    """
    Hybrid agent that uses probability-based selection with ML refinement.
    """
    
    def __init__(self, learning_rate=0.1, exploration_rate=0.1):
        self.strategy = HybridMLStrategy(learning_rate, exploration_rate)
        self.episode_history = []
        
    def select_action(
        self,
        dice: List[int],
        progress: dict,
        selected_number: Optional[int],
        explore: bool = True
    ) -> Tuple[str, Optional[int]]:
        """
        Select action (similar to ML agent interface).
        
        Returns:
            (action_type, number) tuple
        """
        if selected_number is None:
            # Need to select a number
            number = self.strategy.select_number_and_collect(dice, progress, explore)
            if number is not None:
                return ('select_and_collect', number)
            else:
                return ('skip_turn', None)
        else:
            # Already selected, check if can continue
            if GameRules.can_make_number(dice, selected_number):
                return ('select_and_collect', selected_number)
            else:
                # Can't continue, end turn
                return ('skip_turn', None)
    
    def record_step(self, state_key: tuple, action: int, reward: float):
        """Record step for learning"""
        self.episode_history.append((state_key, action, reward))
    
    def update_from_episode(self, total_reward: float):
        """Update strategy based on episode outcome"""
        # If episode was successful (positive reward), reinforce all states
        # If unsuccessful, reduce weights
        
        for state_key, action, reward in self.episode_history:
            self.strategy.update_adjustment(state_key, reward)
        
        self.episode_history = []
    
    def get_name(self) -> str:
        return "Hybrid ML Strategy"
