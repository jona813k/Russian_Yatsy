"""
Debug DQN agent to see what it's doing
"""
import sys
sys.path.append('.')

from src.game.dqn_agent import DQNAgent
from src.game.ml_engine import MLGameEngine

# Create agent and engine
agent = DQNAgent()
engine = MLGameEngine()

print("Testing DQN agent for 10 steps...")
print("="*60)

for step in range(10):
    state_dict = {
        'dice': engine.state.dice_values,
        'progress': dict(engine.player.progress),
        'selected_number': engine.state.selected_number,
        'turns': engine.turn_number
    }
    
    print(f"\n--- Step {step+1} ---")
    print(f"Dice: {engine.state.dice_values}")
    print(f"Selected: {engine.state.selected_number}")
    print(f"Progress: {[(n, engine.player.progress.get(n, 0)) for n in range(1, 13) if engine.player.progress.get(n, 0) > 0]}")
    
    # Get legal actions
    legal_actions = engine.get_legal_actions()
    print(f"Legal actions: {len(legal_actions)}")
    for action in legal_actions[:5]:  # Show first 5
        print(f"  - {action}")
    
    if not legal_actions:
        legal_actions = [{'type': 'skip_turn', 'number': None}]
    
    # Convert to indices
    legal_indices = []
    for action in legal_actions:
        if action['type'] == 'select':
            legal_indices.append(action['number'] - 1)
        elif action['type'] == 'skip_turn':
            legal_indices.append(12)
    
    if not legal_indices:
        legal_indices = [12]
    
    # Get state and action
    state = agent.encode_state(state_dict)
    action_idx = agent.get_action(state, legal_indices, explore=True)
    
    # Convert to game action
    if action_idx == 12:
        game_action = {'type': 'skip_turn', 'number': None}
        print(f"Agent chose: SKIP TURN")
    else:
        game_action = {'type': 'select', 'number': action_idx + 1}
        print(f"Agent chose: SELECT {action_idx + 1}")
    
    # Execute
    result = engine.execute_action(game_action)
    print(f"Result: {result['state']}, Reward: {result['reward']}")
    
    if engine.is_game_over():
        print(f"\n🎉 Game won in {engine.turn_number} turns!")
        break

print("\n" + "="*60)
print(f"Final turn: {engine.turn_number}")
print(f"Game over: {engine.is_game_over()}")
