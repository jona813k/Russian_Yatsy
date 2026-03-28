"""
Game simulation for AI vs AI
"""
from game.game_logic import GameEngine
from game.ai_strategy import ProbabilityStrategy, CompletionStrategy
from models.player import Player


class GameSimulation:
    """Simulates a game between two AI players"""
    
    def __init__(self):
        self.engine = GameEngine()
        self.total_rolls = 0
        self.total_rounds = 0  # Count full rounds (both players)
        self.total_turns = 0  # Keep for backward compatibility
        self.player_rolls = {0: 0, 1: 0}  # Rolls per player
        self.player_turns = {0: 0, 1: 0}  # Turns per player
        
    def simulate_game(self, player1_name: str, player2_name: str, 
                     strategy1: 'AIStrategy', strategy2: 'AIStrategy', verbose: bool = True):
        """
        Simulate a complete game
        
        Returns:
            dict with game statistics
        """
        # Setup game
        self.engine.setup_game([player1_name, player2_name])
        strategies = [strategy1, strategy2]
        
        game_winner = None
        winner_turns = 0
        winner_rolls = 0
        
        while True:
            current_player_idx = self.engine.state.current_player_index
            current_player = self.engine.state.get_current_player()
            
            # Increment round counter when first player starts
            if current_player_idx == 0:
                self.total_rounds += 1
            strategy = strategies[current_player_idx]
            
            # Skip if this player has already won
            if current_player.is_winner():
                self.engine.state.next_player()
                continue
            
            if verbose:
                print(f"\n{'='*50}")
                print(f"{current_player.name}'s tur (Turn #{self.player_turns[current_player_idx] + 1})")
                print(f"{'='*50}")
            
            # Play turn
            winner, bonus = self._simulate_turn(current_player, strategy, verbose)
            
            # Track turns (only count when moving to next player)
            if not bonus and winner is None:
                self.player_turns[current_player_idx] += 1
                self.total_turns += 1
            
            # Check if someone won - STOP THE GAME HERE!
            if winner:
                # Handle both single winner and list of winners (ties)
                if isinstance(winner, list):
                    game_winner = winner[0]  # Take first winner from list
                else:
                    game_winner = winner
                winner_turns = self.player_turns[current_player_idx]
                winner_rolls = self.player_rolls[current_player_idx]
                
                if verbose:
                    winner_name = game_winner.name if not isinstance(winner, list) else f"{winner[0].name} (tie)"
                    print(f"\n🏆 {winner_name} HAR VUNDET!")
                    print(f"Det tog {winner_turns} ture og {winner_rolls} slag")
                
                # STOP - don't continue playing!
                break
        
        # Final statistics
        return {
            'first_winner': game_winner.name,
            'first_winner_rounds': self.total_rounds,
            'first_winner_turns': winner_turns,
            'first_winner_rolls': winner_rolls,
            'total_rounds': self.total_rounds,
            'total_rolls': self.total_rolls,
            'total_turns': self.total_turns,
            'player1_rolls': self.player_rolls[0],
            'player2_rolls': self.player_rolls[1],
            'player1_turns': self.player_turns[0],
            'player2_turns': self.player_turns[1],
            'player1_progress': self.engine.state.players[0].progress,
            'player2_progress': self.engine.state.players[1].progress
        }
    
    def _simulate_turn(self, player: Player, strategy: 'AIStrategy', verbose: bool):
        """Simulate a single turn for a player"""
        current_player_idx = self.engine.state.current_player_index
        
        # Initial roll
        dice = self.engine.start_turn()
        self.total_rolls += 1
        self.player_rolls[current_player_idx] += 1
        
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
            winner, bonus = self.engine.end_turn()
            return winner, bonus
        
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
            self.player_rolls[current_player_idx] += 1
            
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
        
        winner, bonus = self.engine.end_turn()
        
        if bonus and verbose:
            print("🎉 Alle terninger brugt! Ekstra tur!")
        
        return winner, bonus
    
    def _simulate_continuation(self, player: Player, strategy: 'AIStrategy', verbose: bool):
        """Continue after completing a number"""
        current_player_idx = self.engine.state.current_player_index
        
        # Reset and roll again
        self.engine.state.num_dice_in_hand = 6
        self.engine.state.selected_number = None
        self.engine.state.collected_this_turn = 0
        
        dice = self.engine.start_turn()
        self.total_rolls += 1
        self.player_rolls[current_player_idx] += 1
        
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
            winner, bonus = self.engine.end_turn()
            return winner, bonus
        
        if completed:
            if verbose:
                print(f"🎉 Afsluttede {selected_number} igen! Alle terninger returneres!")
            return self._simulate_continuation(player, strategy, verbose)
        
        # Continue rolling
        while self.engine.state.num_dice_in_hand > 0:
            can_continue, new_dice, msg = self.engine.continue_rolling()
            self.total_rolls += 1
            self.player_rolls[current_player_idx] += 1
            
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
        
        winner, bonus = self.engine.end_turn()
        
        if bonus and verbose:
            print("🎉 Alle terninger brugt! Ekstra tur!")
        
        return winner, bonus
