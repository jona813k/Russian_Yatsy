"""
GameState — tracks all mutable state for a single game session.
Used by MLGameEngine during ML training.
"""
from __future__ import annotations
from typing import List, Optional, TYPE_CHECKING

if TYPE_CHECKING:
    from src.models.player import Player


class GameState:
    """
    Holds the complete mutable state of a game in progress.

    Attributes:
        selected_number:      The number the current player has locked in
                              for this turn, or None if not yet chosen.
        collected_this_turn:  Running count of dice collected so far this turn.
        num_dice_in_hand:     How many dice the current player still holds.
        dice_values:          The face-up values of the dice currently in hand.
        players:              Ordered list of Player objects in the game.
        current_player_index: Index into `players` for whose turn it is.
    """

    def __init__(self) -> None:
        self.selected_number: Optional[int] = None
        self.collected_this_turn: int = 0
        self.num_dice_in_hand: int = 0
        self.dice_values: List[int] = []
        self.players: List["Player"] = []
        self.current_player_index: int = 0

    def __repr__(self) -> str:  # pragma: no cover
        return (
            f"GameState(selected={self.selected_number}, "
            f"dice={self.dice_values}, "
            f"collected_this_turn={self.collected_this_turn}, "
            f"num_dice_in_hand={self.num_dice_in_hand})"
        )
