"""
ML-based AI Strategy using trained Q-Learning agent
"""
from game.ml_agent import QLearningAgent
from game.rules import GameRules


class MLStrategy:
    """
    AI Strategy that uses trained ML agent to make decisions.
    Wraps the Q-Learning agent for use in normal gameplay.
    """
    
    def __init__(self, agent: QLearningAgent):
        self.agent = agent
        self.agent.epsilon = 0  # No exploration during gameplay
    
    def select_number(self, dice: list, progress: dict) -> int:
        """
        Select which number to collect based on ML agent's learned policy.
        
        Args:
            dice: Current dice values
            progress: Player's current progress
        
        Returns:
            Selected number (1-12)
        """
        # Build state representation (similar to ml_engine)
        state = self._build_state(dice, progress)
        
        # Get legal actions
        legal_actions = self._get_legal_actions(dice, progress)
        
        if not legal_actions:
            # Fallback - shouldn't happen
            return self._fallback_selection(dice, progress)
        
        # Agent selects action
        action = self.agent.get_action(state, legal_actions, training=False)
        
        return action['number']
    
    def _build_state(self, dice: list, progress: dict) -> tuple:
        """Build state representation matching ml_engine format"""
        dice_tuple = tuple(sorted(dice))
        progress_tuple = tuple(
            progress.get(i, 0) 
            for i in range(GameRules.MIN_NUMBER, GameRules.MAX_NUMBER + 1)
        )
        selected = 0  # Not selected yet
        num_dice = len(dice)
        
        return (dice_tuple, progress_tuple, selected, num_dice)
    
    def _get_legal_actions(self, dice: list, progress: dict) -> list:
        """Get legal number selections from current state"""
        legal_actions = []
        
        for target in range(GameRules.MIN_NUMBER, GameRules.MAX_NUMBER + 1):
            # Check if can make this number
            if not self._can_make_number(dice, target):
                continue
            
            # Check if not completed
            if progress.get(target, 0) >= GameRules.TARGET_PER_NUMBER:
                continue
            
            # Count how many collectible
            collectible = self._count_collectible(dice, target)
            
            legal_actions.append({
                'type': 'select',
                'number': target,
                'collectible': collectible,
                'progress': progress.get(target, 0),
                'remaining_needed': GameRules.TARGET_PER_NUMBER - progress.get(target, 0)
            })
        
        return legal_actions
    
    def _can_make_number(self, dice: list, target: int) -> bool:
        """Check if target can be made from dice"""
        if target <= 6 and target in dice:
            return True
        return len(GameRules.find_valid_combinations(dice, target)) > 0
    
    def _count_collectible(self, dice: list, target: int) -> int:
        """Count collectible dice for target"""
        count = 0
        if target <= 6:
            count += dice.count(target)
        combos = GameRules.find_valid_combinations(dice, target)
        count += len(combos)
        return count
    
    def _fallback_selection(self, dice: list, progress: dict) -> int:
        """Fallback selection if no legal actions (shouldn't happen)"""
        # Try each number
        for target in range(GameRules.MIN_NUMBER, GameRules.MAX_NUMBER + 1):
            if progress.get(target, 0) < GameRules.TARGET_PER_NUMBER:
                if self._can_make_number(dice, target):
                    return target
        
        # Last resort - return lowest incomplete number
        for target in range(GameRules.MIN_NUMBER, GameRules.MAX_NUMBER + 1):
            if progress.get(target, 0) < GameRules.TARGET_PER_NUMBER:
                return target
        
        return 1  # Should never reach here
