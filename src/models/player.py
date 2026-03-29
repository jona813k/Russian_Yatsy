"""
Player model
"""


class Player:
    """Represents a player in the game"""
    
    def __init__(self, name: str):
        self.name = name
        # Track how many of each number (1-12) the player has collected
        self.progress = {i: 0 for i in range(1, 13)}
    
    def add_collected(self, number: int, count: int):
        """Add collected dice to player's progress
        
        Returns:
            bool: True if this number was completed (reached 6)
        """
        current = self.progress.get(number, 0)
        new_total = min(current + count, 6)
        self.progress[number] = new_total
        
        # Return True if we just completed this number
        return new_total == 6 and current < 6
    
    def get_total_collected(self) -> int:
        """Get total number of dice collected"""
        return sum(self.progress.values())
    
    def is_winner(self) -> bool:
        """Check if player has won (6 of each number)"""
        return all(count >= 6 for count in self.progress.values())
    
    def __str__(self):
        return f"{self.name}: {self.get_total_collected()}/72 dice"
