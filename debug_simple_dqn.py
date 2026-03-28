"""
Debug script to test simplified DQN
"""
import sys
sys.path.insert(0, 'src')

from src.game.dqn_agent_simple import SimpleDQNAgent
from src.game.ml_engine import MLGameEngine

print("Creating agent...")
agent = SimpleDQNAgent()

print("Creating engine...")
engine = MLGameEngine()

print("\nResetting game...")
engine.reset()

print("Starting new turn...")
engine.start_new_turn()

print("\nChecking game state...")
print(f"Is game over? {engine.is_game_over()}")

print("\nGetting state representation...")
state = engine.get_state_representation()
print(f"State type: {type(state)}")
print(f"State length: {len(state)}")
print(f"State: {state}")

print("\nEncoding state...")
encoded = agent.encode_state(state)
print(f"Encoded shape: {encoded.shape}")
print(f"Encoded values: {encoded}")

print("\nGetting legal actions...")
legal_actions = engine.get_legal_actions()
print(f"Number of legal actions: {len(legal_actions)}")
print(f"Legal actions: {legal_actions[:3]}...")  # Show first 3

print("\nGetting action from agent...")
action = agent.get_action(state, legal_actions, training=True)
print(f"Selected action: {action}")

print("\nExecuting action...")
result = engine.execute_action(action)
print(f"Result: {result}")

print("\n✓ All basic operations work!")

print("\n" + "="*70)
print("Testing one full game...")
print("="*70)

engine.reset()
engine.start_new_turn()

steps = 0
max_steps = 200

while not engine.is_game_over() and steps < max_steps:
    state = engine.get_state_representation()
    legal_actions = engine.get_legal_actions()
    
    if not legal_actions:
        print(f"Step {steps}: No legal actions!")
        break
    
    action = agent.get_action(state, legal_actions, training=True)
    result = engine.execute_action(action)
    
    steps += 1
    
    if steps % 10 == 0:
        print(f"Step {steps}: {result['state']}")
    
    if result['state'] == 'won':
        print(f"\n✓ Game completed in {steps} steps!")
        break

if steps >= max_steps:
    print(f"\n✗ Game hit max steps ({max_steps})")
else:
    game_info = engine.get_game_info()
    print(f"Turns: {game_info['turns']}")
    print(f"Rolls: {game_info['rolls']}")
