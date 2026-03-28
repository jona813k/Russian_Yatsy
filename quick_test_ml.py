"""
Quick test to see ML agent performance during training
"""
import sys
sys.path.insert(0, 'src')

from game.ml_agent import QLearningAgent
from game.ml_engine import MLGameEngine

# Load latest agent
print("Loading agent...")
agent = QLearningAgent()
try:
    agent.load('models/ml_agent.pkl')
    print(f"Loaded agent with {len(agent.q_table)} states")
    print(f"Episodes trained: {agent.episodes_trained}")
except:
    print("No saved agent found")
    sys.exit(1)

# Test on 100 games
engine = MLGameEngine()
turns_list = []

print("\nTesting on 100 games...")
for i in range(100):
    engine.reset()
    steps = 0
    max_steps = 50000
    
    while not engine.is_game_over() and steps < max_steps:
        state = engine.get_state_representation()
        legal_actions = engine.get_legal_actions()
        if not legal_actions:
            break
        action = agent.get_action(state, legal_actions, training=False)
        result = engine.execute_action(action)
        if result['state'] == 'won':
            break
        steps += 1
    
    game_info = engine.get_game_info()
    turns_list.append(game_info['turns'])

# Stats
import statistics
print(f"\nResults (100 games):")
print(f"  Average turns: {statistics.mean(turns_list):.2f}")
print(f"  Median turns:  {statistics.median(turns_list):.2f}")
print(f"  Best:          {min(turns_list)}")
print(f"  Worst:         {max(turns_list)}")
