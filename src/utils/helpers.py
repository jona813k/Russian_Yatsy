"""
Helper utility functions
"""
import random


def roll_dice(num_dice: int = 1) -> list:
    """Roll dice and return their values"""
    return [random.randint(1, 6) for _ in range(num_dice)]


def validate_input(user_input: str, valid_options: list) -> bool:
    """Validate user input against valid options"""
    return user_input in valid_options
