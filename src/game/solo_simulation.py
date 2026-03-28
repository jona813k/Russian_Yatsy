"""
Solo game simulation for single AI player
"""
from game.game_logic import GameEngine
from models.player import Player


class SoloSimulation:
    """Simulates a solo game for one AI player"""
    
    def __init__(self, strategy=None):
        """
        Initialize simulation.
        
        Args:
            strategy: Optional AI strategy to use for simulation
        """
        self.engine = GameEngine()
        self.total_rolls = 0
        self.total_turns = 0
        self.total_rounds = 0
        self.strategy = strategy
        
    def simulate_solo_game(self, player_name: str, strategy: 'AIStrategy', verbose: bool = False):
        """
        Simulate a complete solo game
        
        Returns:
            dict with game statistics
        """
        # Setup game with one player
        self.engine.setup_game([player_name])
        self.total_rolls = 0
        self.total_turns = 0
        self.total_rounds = 0
        
        current_player = self.engine.state.get_current_player()
        
        while not current_player.is_winner():
            if verbose:
                print(f"\n{'='*50}")
                print(f"{current_player.name}'s tur {self.total_turns + 1}")
                print(f"{'='*50}")
            
            # Play turn
            bonus = self._simulate_turn(current_player, strategy, verbose)
            
            # Track turns (only count when not getting bonus)
            if not bonus:
                self.total_turns += 1
                self.total_rounds += 1  # In solo mode, each turn is also a round
        
        # Final statistics
        return {
            'total_rolls': self.total_rolls,
            'total_turns': self.total_turns,
            'total_rounds': self.total_rounds,
            'rolls': self.total_rolls,  # Alias for compatibility
            'turns': self.total_turns,  # Alias for compatibility
            'completed': True,
            'player_progress': current_player.progress
        }
    
    def simulate(self, verbose: bool = False):
        """
        Simulate a complete game using stored strategy.
        
        Returns:
            dict with game statistics
        """
        if self.strategy is None:
            raise ValueError("No strategy set. Use simulate_solo_game() or provide strategy in __init__")
        
        return self.simulate_solo_game("AI-Player", self.strategy, verbose)
    
    def _simulate_turn(self, player: Player, strategy: 'AIStrategy', verbose: bool) -> bool:
        """Simulate a single turn for a player. Returns True if bonus turn earned."""
        # Initial roll
        dice = self.engine.start_turn()
        self.total_rolls += 1
        
        if verbose:
            print(f"Slag: {dice}")
        
        # AI selects number
        selected_number = strategy.select_number(dice, player.progress)
        
        if verbose:
            print(f"Vælger: {selected_number}")
        
        success, count, message, completed = self.engine.select_dice(selected_number)
        
        if verbose:
            print(message)
        
        if not success:
            # No matching dice, turn ends
            self.engine.state.next_player()
            return False
        
        # Check if completed
        if completed:
            if verbose:
                print(f"🎉 Afsluttede {selected_number}! Alle terninger returneres!")
            
            # Continue with new round
            return self._simulate_continuation(player, strategy, verbose)
        
        # Continue rolling
        while self.engine.state.num_dice_in_hand > 0:
            can_continue, new_dice, msg = self.engine.continue_rolling()
            self.total_rolls += 1
            
            if verbose:
                print(f"Slag igen: {new_dice}")
                print(msg)
            
            if not can_continue:
                break
            
            success, count, message, completed = self.engine.select_dice(selected_number)
            
            if verbose:
                print(message)
            
            if completed:
                if verbose:
                    print(f"🎉 Afsluttede {selected_number}! Alle terninger returneres!")
                return self._simulate_continuation(player, strategy, verbose)
        
        # Check if all dice used (bonus turn)
        all_dice_used = self.engine.state.num_dice_in_hand == 0
        
        if all_dice_used and verbose:
            print("🎉 Alle terninger brugt! Ekstra tur!")
        
        # Reset for next turn (but same player if bonus)
        self.engine.state.start_turn()
        
        return all_dice_used
    
    def _simulate_continuation(self, player: Player, strategy: 'AIStrategy', verbose: bool) -> bool:
        """Continue after completing a number"""
        # Reset and roll again
        self.engine.state.num_dice_in_hand = 6
        self.engine.state.selected_number = None
        self.engine.state.collected_this_turn = 0
        
        dice = self.engine.start_turn()
        self.total_rolls += 1
        
        if verbose:
            print(f"Ny runde - Slag: {dice}")
        
        # Select new number
        selected_number = strategy.select_number(dice, player.progress)
        
        if verbose:
            print(f"Vælger: {selected_number}")
        
        success, count, message, completed = self.engine.select_dice(selected_number)
        
        if verbose:
            print(message)
        
        if not success:
            self.engine.state.start_turn()
            return False
        
        if completed:
            if verbose:
                print(f"🎉 Afsluttede {selected_number} igen! Alle terninger returneres!")
            return self._simulate_continuation(player, strategy, verbose)
        
        # Continue rolling
        while self.engine.state.num_dice_in_hand > 0:
            can_continue, new_dice, msg = self.engine.continue_rolling()
            self.total_rolls += 1
            
            if verbose:
                print(f"Slag igen: {new_dice}")
                print(msg)
            
            if not can_continue:
                break
            
            success, count, message, completed = self.engine.select_dice(selected_number)
            
            if verbose:
                print(message)
            
            if completed:
                if verbose:
                    print(f"🎉 Afsluttede {selected_number}! Alle terninger returneres!")
                return self._simulate_continuation(player, strategy, verbose)
        
        # Check if all dice used
        all_dice_used = self.engine.state.num_dice_in_hand == 0
        
        if all_dice_used and verbose:
            print("🎉 Alle terninger brugt! Ekstra tur!")
        
        self.engine.state.start_turn()
        
        return all_dice_used
