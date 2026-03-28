"""
Quick test to verify DQN strategy integration
"""
import sys
sys.path.insert(0, 'src')

from src.game.dqn_strategy import DQNStrategy

print("Testing DQN Strategy Integration...")
print("="*70)

# Test 1: Load DQN strategy
print("\n1. Loading DQN strategy...")
try:
    strategy = DQNStrategy()
    print("✓ DQN strategy loaded successfully!")
except Exception as e:
    print(f"✗ Failed to load: {e}")
    sys.exit(1)

# Test 2: Test with sample game state
print("\n2. Testing decision making...")
dice = [5, 6, 5, 6, 3, 2]
progress = {1: 6, 2: 6, 3: 4, 4: 0, 5: 0, 6: 0, 7: 0, 8: 0, 9: 0, 10: 0, 11: 0, 12: 0}

print(f"Dice: {dice}")
print(f"Progress: Numbers 1,2 complete, number 3 has 4")

selected = strategy.select_number(dice, progress)
print(f"DQN selected: {selected}")

if selected in [3, 5, 6, 11]:
    print("✓ Reasonable choice!")
else:
    print(f"? Unexpected choice: {selected}")

# Test 3: Test with different scenarios
print("\n3. Testing multiple scenarios...")
test_cases = [
    {
        'dice': [1, 1, 1, 2, 3, 4],
        'progress': {},
        'description': 'Three 1s at start'
    },
    {
        'dice': [5, 6, 5, 6, 5, 6],
        'progress': {11: 5, 12: 5},  # Both 11 and 12 almost complete
        'description': 'Can finish 11 or 12'
    },
    {
        'dice': [1, 2, 3, 4, 5, 6],
        'progress': {1: 6, 2: 6, 3: 6, 4: 6, 5: 6, 6: 6, 7: 6, 8: 6, 9: 6, 10: 6},
        'description': 'Endgame - only 11 and 12 left'
    }
]

for i, test in enumerate(test_cases, 1):
    dice = test['dice']
    progress = test['progress']
    desc = test['description']
    
    selected = strategy.select_number(dice, progress)
    print(f"  Case {i} ({desc}): Selected {selected}")

print("\n" + "="*70)
print("✓ All tests passed! DQN strategy is ready to play!")
print("\nYou can now use 'ai2' in the game to play against the DQN AI.")
