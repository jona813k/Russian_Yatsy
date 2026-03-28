"""
Tests for game logic
"""
import unittest
import sys
import os

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from game.game_logic import GameEngine
from models.player import Player


class TestGameLogic(unittest.TestCase):
    """Test cases for game logic"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.engine = GameEngine()
        self.engine.state.players = [Player("Test1"), Player("Test2")]
    
    def test_start_turn(self):
        """Test starting a turn"""
        dice = self.engine.start_turn()
        self.assertEqual(len(dice), 6)
        self.assertEqual(self.engine.state.num_dice_in_hand, 6)
    
    def test_select_dice_singles(self):
        """Test selecting single dice"""
        self.engine.state.dice_values = [1, 1, 2, 3, 4, 5]
        self.engine.state.num_dice_in_hand = 6
        
        success, count, message, completed = self.engine.select_dice(1)
        self.assertTrue(success)
        self.assertEqual(count, 2)
        self.assertEqual(len(self.engine.state.dice_values), 4)
    
    def test_end_turn_no_bonus(self):
        """Test ending turn without bonus"""
        self.engine.state.num_dice_in_hand = 3  # Not all dice used
        winner, bonus = self.engine.end_turn()
        
        self.assertIsNone(winner)
        self.assertFalse(bonus)
        self.assertEqual(self.engine.state.current_player_index, 1)
    
    def test_end_turn_with_bonus(self):
        """Test ending turn with bonus (all dice used)"""
        self.engine.state.num_dice_in_hand = 0  # All dice used
        current_idx = self.engine.state.current_player_index
        
        winner, bonus = self.engine.end_turn()
        
        self.assertIsNone(winner)
        self.assertTrue(bonus)
        self.assertEqual(self.engine.state.current_player_index, current_idx)
    
    def test_check_winner(self):
        """Test winner detection"""
        player = self.engine.state.players[0]
        # Set all numbers to 6
        for i in range(1, 13):
            player.progress[i] = 6
        
        winner, bonus = self.engine.end_turn()
        self.assertIsNotNone(winner)


if __name__ == "__main__":
    unittest.main()
