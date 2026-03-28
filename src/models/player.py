"""
Player — tracks a single player's identity and progress through the game.
Used by MLGameEngine during ML training.
"""
from __future__ import annotations
from typing import Dict


class Player:
    """
    Represents one player in a Russian Yatzy game.

    Attributes:
        name:     Display name for the player.
        progress: Mapping of number (1-12) → count of dice collected so far.
                  A number is "completed" once its count reaches 6.
    """

    TARGET_PER_NUMBER: int = 6
    MIN_NUMBER: int = 1
    MAX_NUMBER: int = 12

    def __init__(self, name: str) -> None:
        self.name: str = name
        self.progress: Dict[int, int] = {}

    # ------------------------------------------------------------------
    # Mutation helpers
    # ------------------------------------------------------------------

    def add_collected(self, number: int, count: int) -> bool:
        """
        Add *count* collected dice for *number*.

        The total is capped at TARGET_PER_NUMBER (6) so the progress dict
        never exceeds the winning threshold.

        Returns:
            True if this call caused the number to reach TARGET_PER_NUMBER
            (i.e. the number was just completed), False otherwise.
        """
        current = self.progress.get(number, 0)
        new_total = min(current + count, self.TARGET_PER_NUMBER)
        self.progress[number] = new_total
        return new_total >= self.TARGET_PER_NUMBER and current < self.TARGET_PER_NUMBER

    # ------------------------------------------------------------------
    # Query helpers
    # ------------------------------------------------------------------

    def is_winner(self) -> bool:
        """
        Return True if every number from 1 to 12 has been completed
        (i.e. has at least TARGET_PER_NUMBER dice collected).
        """
        for n in range(self.MIN_NUMBER, self.MAX_NUMBER + 1):
            if self.progress.get(n, 0) < self.TARGET_PER_NUMBER:
                return False
        return True

    def __repr__(self) -> str:  # pragma: no cover
        completed = sum(
            1 for v in self.progress.values() if v >= self.TARGET_PER_NUMBER
        )
        return f"Player(name={self.name!r}, completed={completed}/12)"
