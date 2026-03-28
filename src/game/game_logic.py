"""
Core game logic implementation
"""
from models.game_state import GameState
from models.player import Player
from game.rules import GameRules
from utils.helpers import roll_dice


class GameEngine:
    """Handles the core game logic and turn management"""
    
    def __init__(self):
        self.state = GameState()
    
    def setup_game(self, player_names: list):
        """Initialize a new game with players"""
        self.state.players = [Player(name) for name in player_names]
        self.state.current_player_index = 0
        self.state.round_number = 1
    
    def start_turn(self):
        """Initialize state for a new turn"""
        self.state.start_turn()
        # Roll all 6 dice to start
        self.state.dice_values = roll_dice(GameRules.NUM_DICE)
        return self.state.dice_values
    
    def select_dice(self, selected_number: int) -> tuple:
        """
        Select dice matching the target number.
        Automatically collects ALL matching dice (singles + combinations).
        
        For numbers 1-6: Can use exact matches OR combinations
        For numbers 7-12: Must use combinations (pairs)
        
        Returns:
            (success: bool, count: int, message: str, completed: bool)
        """
        # Validate or set selected number for turn
        if not self._validate_selected_number(selected_number):
            return False, 0, f"Skal vælge {self.state.selected_number}!", False
        
        # Collect all matching dice
        collected, messages, remaining = self._collect_all_matches(
            self.state.dice_values, selected_number
        )
        
        if collected == 0:
            return False, 0, f"Ingen {selected_number}'ere fundet!", False
        
        # Update game state
        self._update_turn_state(collected, remaining)
        
        # Check if number was completed
        current_player = self.state.get_current_player()
        completed = current_player.add_collected(selected_number, collected)
        
        message = f"Samlede {' + '.join(messages)} = {collected} × {selected_number}!"
        return True, collected, message, completed
    
    def _validate_selected_number(self, selected_number: int) -> bool:
        """Validate that selected number matches previously selected (if any)"""
        if self.state.selected_number is None:
            self.state.selected_number = selected_number
            return True
        return self.state.selected_number == selected_number
    
    def _collect_all_matches(self, dice_values: list, target: int) -> tuple:
        """
        Collect ALL matching dice (singles and combinations).
        
        Args:
            dice_values: Current dice values
            target: Target number to match
        
        Returns:
            (collected_count, messages, remaining_dice)
        """
        total_collected = 0
        messages = []
        remaining_dice = list(dice_values)
        
        # Collect singles (only for 1-6)
        if target <= 6:
            single_count = GameRules.count_single_matches(remaining_dice, target)
            if single_count > 0:
                total_collected += single_count
                messages.append(f"{single_count} enkelt")
                remaining_dice = [d for d in remaining_dice if d != target]
        
        # Collect combinations
        combinations = GameRules.find_valid_combinations(remaining_dice, target)
        if combinations:
            total_collected += len(combinations)
            messages.append(f"{len(combinations)} kombination(er)")
            
            # Remove dice used in combinations
            for combo in combinations:
                for die_value in combo:
                    remaining_dice.remove(die_value)
        
        return total_collected, messages, remaining_dice
    
    def _update_turn_state(self, collected: int, remaining_dice: list):
        """Update game state after collecting dice"""
        self.state.dice_values = remaining_dice
        self.state.collected_this_turn += collected
        self.state.num_dice_in_hand = len(remaining_dice)
    
    def continue_rolling(self) -> tuple:
        """
        Roll remaining dice and check for matches.
        
        Returns:
            (can_continue: bool, dice_values: list, message: str)
        """
        if self.state.num_dice_in_hand == 0:
            return False, [], "Ingen terninger tilbage!"
        
        # Roll remaining dice
        self.state.dice_values = roll_dice(self.state.num_dice_in_hand)
        
        # Check if we can continue with selected number
        can_continue = self._can_make_number(
            self.state.dice_values, self.state.selected_number
        )
        
        if not can_continue:
            return False, self.state.dice_values, f"Ingen {self.state.selected_number}'ere! Tur slut."
        
        return True, self.state.dice_values, "Slå igen!"
    
    def _can_make_number(self, dice_values: list, target: int) -> bool:
        """Check if target can be made with dice (singles OR combinations)"""
        # Check singles (only 1-6)
        if target <= 6 and target in dice_values:
            return True
        
        # Check combinations
        combinations = GameRules.find_valid_combinations(dice_values, target)
        return len(combinations) > 0
    
    def end_turn(self):
        """End current turn and update player progress"""
        current_player = self.state.get_current_player()
        
        # Check if current player has won
        if current_player.is_winner():
            # Add to potential winners if not already there
            if current_player not in self.state.potential_winners:
                self.state.potential_winners.append(current_player)
                # Track the first player to win (for round completion)
                if self.state.winning_player_index is None:
                    self.state.winning_player_index = self.state.current_player_index
        
        # Check if player used all dice (would normally get bonus turn)
        all_dice_used = self.state.num_dice_in_hand == 0
        
        # Don't give bonus turn if player has won - this prevents the extra turn bug
        should_get_bonus = all_dice_used and not current_player.is_winner()
        
        # Move to next player if they didn't get a bonus turn
        if not should_get_bonus:
            self.state.next_player()
            
            # Check if we've completed a full round after someone won
            if self.state.winning_player_index is not None:
                # If we're back to the player after the winner, the round is complete
                next_after_winner = (self.state.winning_player_index + 1) % len(self.state.players)
                if self.state.current_player_index == next_after_winner:
                    # Round complete - return the winner(s)
                    return self.determine_winner(), False
        
        return None, should_get_bonus
    
    def get_winner(self):
        """Check if any player has won"""
        for player in self.state.players:
            if player.is_winner():
                return player
        return None
    
    def determine_winner(self):
        """Determine final winner(s) after round completion"""
        if not self.state.potential_winners:
            return None
        
        # If only one winner, return that player
        if len(self.state.potential_winners) == 1:
            return self.state.potential_winners[0]
        
        # Multiple players won - return list for tie
        return self.state.potential_winners
