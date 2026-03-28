"""
Rendering utilities for game display
"""


class DiceRenderer:
    """Renders dice in ASCII art format"""
    
    DICE_ART = {
        1: [
            "┌─────────┐",
            "│         │",
            "│    ●    │",
            "│         │",
            "└─────────┘"
        ],
        2: [
            "┌─────────┐",
            "│ ●       │",
            "│         │",
            "│       ● │",
            "└─────────┘"
        ],
        3: [
            "┌─────────┐",
            "│ ●       │",
            "│    ●    │",
            "│       ● │",
            "└─────────┘"
        ],
        4: [
            "┌─────────┐",
            "│ ●     ● │",
            "│         │",
            "│ ●     ● │",
            "└─────────┘"
        ],
        5: [
            "┌─────────┐",
            "│ ●     ● │",
            "│    ●    │",
            "│ ●     ● │",
            "└─────────┘"
        ],
        6: [
            "┌─────────┐",
            "│ ●     ● │",
            "│ ●     ● │",
            "│ ●     ● │",
            "└─────────┘"
        ]
    }
    
    @staticmethod
    def render_dice(dice_values: list) -> str:
        """Render multiple dice side by side"""
        if not dice_values:
            return ""
        
        lines = [""] * 5
        for value in dice_values:
            dice = DiceRenderer.DICE_ART[value]
            for i, line in enumerate(dice):
                lines[i] += line + "  "
        return "\n".join(lines)
