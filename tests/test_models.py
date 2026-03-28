"""
Tests for game models
"""
import unittest
import sys
from pathlib import Path

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from player import Player
from game_state import GameState


class TestPlayer(unittest.TestCase):
    """Test cases for Player model"""
    
    def test_player_creation(self):
        """Test creating a player"""
        player = Player("Test Player")
        self.assertEqual(player.name, "Test Player")
        self.assertEqual(player.score, 0)
    
    def test_add_score(self):
        """Test adding score to player"""
        player = Player("Test")
        player.add_score(10)
        self.assertEqual(player.score, 10)


class TestGameState(unittest.TestCase):
    """Test cases for GameState model"""
    
    def test_game_state_creation(self):
        """Test creating a game state"""
        state = GameState()
        self.assertEqual(state.round_number, 1)
        self.assertEqual(len(state.players), 0)


if __name__ == "__main__":
    unittest.main()
