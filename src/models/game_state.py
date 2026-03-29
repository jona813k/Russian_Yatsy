"""
Game state model - tracks current state of an ongoing game
"""


class GameState:
    """
    Represents the current state of the game.
    Tracks players, current turn, dice, and turn-specific state.
    """
    
    def __init__(self):
        """Initialize a new game state"""
        # Player management
        self.players = []
        self.current_player_index = 0  # Keep this name for backward compatibility
        
        # Dice state
        self.dice_values = []
        self.num_dice_in_hand = 6  # Always start with 6 dice
        
        # Turn-specific state
        self.selected_number = None  # Which number is being collected this turn
        self.collected_this_turn = 0  # How many collected in current turn
        
        # Winner tracking
        self.potential_winners = []  # Players who have completed the game
        self.winning_player_index = None  # Index of first player to complete
    
    def start_turn(self):
        """
        Reset turn-specific state for a new turn.
        Called at the beginning of each player's turn.
        """
        self.dice_values = []
        self.num_dice_in_hand = 6
        self.selected_number = None
        self.collected_this_turn = 0
    
    def next_player(self):
        """
        Advance to the next player.
        Wraps around to first player after last player.
        """
        self.current_player_index = (self.current_player_index + 1) % len(self.players)
    
    def get_current_player(self):
        """
        Get the currently active player.
        
        Returns:
            Player object for current player, or None if no players
        """
        return self.players[self.current_player_index] if self.players else None
    
    def is_turn_complete(self) -> bool:
        """
        Check if current turn is complete (all dice used or no valid moves).
        
        Returns:
            True if turn should end, False otherwise
        """
        return self.num_dice_in_hand == 0
    
    def get_player_by_name(self, name: str):
        """
        Find a player by name.
        
        Args:
            name: Player name to search for
            
        Returns:
            Player object if found, None otherwise
        """
        for player in self.players:
            if player.name == name:
                return player
        return None
