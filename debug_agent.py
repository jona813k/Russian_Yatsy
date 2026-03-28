"""
Debug script to understand why ML agent doesn't complete games
"""
import sys
sys.path.insert(0, 'src')

from game.ml_agent import QLearningAgent
from game.ml_engine import MLGameEngine

# Load trained agent
print("Loading trained agent...")
agent = QLearningAgent()
agent.load('models/ml_agent.pkl')
print(f"Loaded agent with {len(agent.q_table)} states")

# Create engine
engine = MLGameEngine()

# Play one detailed game
print("\n" + "="*70)
print("PLAYING ONE GAME WITH DETAILED DEBUG OUTPUT")
print("="*70)

engine.reset()
step_count = 0
turn_count = 0
max_steps = 50000

while not engine.is_game_over() and step_count < max_steps:
    state = engine.get_state_representation()
    legal_actions = engine.get_legal_actions()
    
    if not legal_actions:
        print(f"\n*** NO LEGAL ACTIONS AT STEP {step_count} ***")
        game_info = engine.get_game_info()
        print(f"Current state:")
        print(f"  Selected number: {engine.state.selected_number}")
        print(f"  Dice in hand: {engine.state.num_dice_in_hand}")
        print(f"  Dice values: {engine.state.dice_values}")
        print(f"  Turn: {game_info['turns']}")
        print(f"  Progress: {game_info['progress']}")
        
        # Check which numbers can be made
        print(f"\nChecking all numbers:")
        for num in range(1, 13):
            can_make = engine._can_make_number(engine.state.dice_values, num)
            progress = game_info['progress'][num]
            print(f"  Number {num:2d}: can_make={can_make}, progress={progress}/6")
        
        break
    
    action = agent.get_action(state, legal_actions, training=False)
    result = engine.execute_action(action)
    
    # Print progress every 10 steps
    if step_count % 10 == 0:
        game_info = engine.get_game_info()
        progress = game_info['progress']
        total_collected = sum(progress.values())
        
        print(f"\nStep {step_count:5d} | Turn {game_info['turns']:2d} | "
              f"Collected: {total_collected:2d}/72")
        
        # Show which numbers are completed
        completed = [num for num, count in progress.items() if count >= 6]
        if completed:
            print(f"  Completed numbers: {completed}")
        
        # Show progress on each number
        progress_str = " ".join([f"{num}:{count}" for num, count in sorted(progress.items())])
        print(f"  Progress: {progress_str}")
    
    if result['state'] == 'won':
        print("\n*** GAME WON! ***")
        break
    
    step_count += 1

print(f"\n{'='*70}")
print("GAME ENDED")
print(f"{'='*70}")
print(f"Total steps: {step_count}")
print(f"Hit step limit: {step_count >= max_steps}")

game_info = engine.get_game_info()
print(f"Turns: {game_info['turns']}")
print(f"Rolls: {game_info['rolls']}")
progress = game_info['progress']
total_collected = sum(progress.values())
print(f"Total collected: {total_collected}/72")

# Show final progress
print("\nFinal Progress:")
for num in range(1, 13):
    count = progress[num]
    status = "OK" if count >= 6 else "  "
    print(f"  {status} Number {num:2d}: {count}/6")

completed_numbers = sum(1 for count in progress.values() if count >= 6)
print(f"\nCompleted numbers: {completed_numbers}/12")
print(f"Win condition met: {engine.player.is_winner()}")
