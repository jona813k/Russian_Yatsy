"""
DQN Strategy wrapper for gameplay
Wraps the SimpleDQNAgent to work with the game's AI strategy interface
"""
from game.rules import GameRules
from game.dqn_agent_simple import SimpleDQNAgent
import os


class DQNStrategy:
    """
    Strategy using trained DQN agent
    """
    
    def __init__(self, agent: SimpleDQNAgent = None):
        """
        Initialize DQN strategy
        
        Args:
            agent: Pre-loaded SimpleDQNAgent. If None, will try to load from default path
        """
        self.agent = agent
        if self.agent is None:
            # Try to load from default path
            model_path = 'models/simple_dqn_agent.pth'
            if os.path.exists(model_path):
                self.agent = SimpleDQNAgent()
                self.agent.load(model_path)
                print(f"Loaded DQN model from {model_path}")
            else:
                raise FileNotFoundError(f"No DQN model found at {model_path}. Train a model first!")
    
    def select_number(self, dice_values: list, player_progress: dict) -> int:
        """
        Select which number to collect based on DQN strategy
        
        Args:
            dice_values: List of dice values
            player_progress: Dictionary of progress (number -> count collected)
            
        Returns:
            Selected number (1-12)
        """
        # Convert game state to DQN format
        state = self._convert_to_dqn_state(dice_values, player_progress)
        
        # Get legal actions
        legal_actions = self._get_legal_actions(dice_values, player_progress)
        
        if not legal_actions:
            # No valid moves - shouldn't happen but fallback to random
            for target in range(1, 13):
                if player_progress.get(target, 0) < 6:
                    return target
            return 1
        
        # Get action from DQN agent
        action = self.agent.get_action(state, legal_actions, training=False)
        
        return action['number']
    
    def _convert_to_dqn_state(self, dice_values: list, player_progress: dict) -> tuple:
        """
        Convert game state to DQN state format
        
        DQN expects: (dice_tuple, progress_bins, completed_bin, dice_count_bin)
        """
        # Dice tuple (sorted)
        dice_tuple = tuple(sorted(dice_values))
        
        # Progress bins (0-6 for each number 1-12)
        progress_bins = tuple(
            player_progress.get(i, 0) 
            for i in range(1, 13)
        )
        
        # Completed count (not used by simplified DQN but part of state format)
        completed_bin = sum(1 for count in progress_bins if count >= 6)
        
        # Dice count
        dice_count_bin = len(dice_values)
        
        return (dice_tuple, progress_bins, completed_bin, dice_count_bin)
    
    def _get_legal_actions(self, dice_values: list, player_progress: dict) -> list:
        """
        Get list of legal actions in DQN format
        
        Returns list of action dicts: {'type': 'select', 'number': X}
        """
        legal_actions = []
        
        # Check all possible numbers 1-12
        for target in range(1, 13):
            current = player_progress.get(target, 0)
            
            # Skip if already completed
            if current >= 6:
                continue
            
            # Check if we can make this number with current dice
            count = 0
            
            # Count singles (only for 1-6)
            if target <= 6:
                count += dice_values.count(target)
            
            # Count combinations
            combos = GameRules.find_valid_combinations(dice_values, target)
            count += len(combos)
            
            if count > 0:
                legal_actions.append({
                    'type': 'select',
                    'number': target,
                    'collectible': count,
                    'progress': current,
                    'remaining_needed': 6 - current
                })
        
        return legal_actions
