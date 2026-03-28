"""
Game rules and validation logic
"""


class GameRules:
    """Defines and validates game rules"""
    
    # Constants
    NUM_DICE = 6
    TARGET_PER_NUMBER = 6
    MIN_NUMBER = 1
    MAX_NUMBER = 12
    
    @staticmethod
    def is_game_won(player_progress: dict) -> bool:
        """
        Check if player has won by collecting 6 of each number (1-12).
        
        Args:
            player_progress: Dictionary mapping number -> count collected
            
        Returns:
            True if player has 6 of all numbers, False otherwise
        """
        for number in range(GameRules.MIN_NUMBER, GameRules.MAX_NUMBER + 1):
            if player_progress.get(number, 0) < GameRules.TARGET_PER_NUMBER:
                return False
        return True
    
    @staticmethod
    def find_combinations(dice_roll: list, target_number: int) -> list:
        """
        Find all non-overlapping pairs of dice that sum to target number
        
        Returns:
            List of tuples (index1, index2) representing valid pairs
        """
        pairs = []
        used_indices = set()
        
        for i in range(len(dice_roll)):
            if i in used_indices:
                continue
            for j in range(i + 1, len(dice_roll)):
                if j in used_indices:
                    continue
                if dice_roll[i] + dice_roll[j] == target_number:
                    pairs.append((i, j))
                    used_indices.add(i)
                    used_indices.add(j)
                    break  # Move to next i after finding pair
        
        return pairs
    
    @staticmethod
    def find_valid_combinations(dice: list, target: int) -> list:
        """
        Find all NON-OVERLAPPING pairs that sum to target.
        Only pairs (2 dice) are valid - no triples!
        
        Args:
            dice: List of dice values
            target: Target sum
            
        Returns:
            List of combinations (each is a list of 2 dice values)
            Example: [[6, 6], [5, 7]] means two valid pairs found
        """
        if not dice or target < 2:
            return []
        
        combinations = []
        used_indices = set()
        
        # Try all possible pairs (non-overlapping)
        for i in range(len(dice)):
            if i in used_indices:
                continue
            for j in range(i + 1, len(dice)):
                if j in used_indices:
                    continue
                if dice[i] + dice[j] == target:
                    combinations.append([dice[i], dice[j]])
                    used_indices.add(i)
                    used_indices.add(j)
                    break
        
        return combinations
    
    @staticmethod
    def count_single_matches(dice_roll: list, target_number: int) -> int:
        """
        Count dice that exactly match target.

        Args:
            dice_roll: List of dice values
            target_number: Number to match

        Returns:
            Count of matching dice
        """
        return dice_roll.count(target_number)
    
    @staticmethod
    def update_player_progress(player_progress: dict, number: int, count: int) -> dict:
        """
        Update player's progress, capping at 6 per number.
        
        Args:
            player_progress: Current progress dict
            number: Number being collected
            count: Amount to add
            
        Returns:
            Updated progress dictionary
        """
        current = player_progress.get(number, 0)
        player_progress[number] = min(current + count, GameRules.TARGET_PER_NUMBER)
        return player_progress
