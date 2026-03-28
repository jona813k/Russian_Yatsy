"""Debug script to see what's happening in head-to-head"""
from game.simulation import GameSimulation
from game.ai_strategy import ProbabilityStrategy
from game.dqn_strategy import DQNStrategy

# Load strategies
prob_strategy = ProbabilityStrategy()

# Try to load DQN
try:
    dqn_strategy = DQNStrategy()
    dqn_strategy.load_model('models/simple_dqn_agent.pth')
    print("✅ DQN loaded\n")
except Exception as e:
    print(f"❌ Failed to load DQN: {e}")
    exit(1)

# Run one verbose game
sim = GameSimulation()
print("="*60)
print("   DEBUG: AI1 (Probability) vs AI2 (DQN) - VERBOSE")
print("="*60)

result = sim.simulate_game('AI1', 'AI2', prob_strategy, dqn_strategy, verbose=True)

print("\n" + "="*60)
print("   FINAL RESULTS")
print("="*60)
print(f"First winner: {result['first_winner']}")
print(f"AI1 turns: {result['player1_turns']}")
print(f"AI2 turns: {result['player2_turns']}")
print(f"AI1 rolls: {result['player1_rolls']}")
print(f"AI2 rolls: {result['player2_rolls']}")
print(f"Total rounds: {result['total_rounds']}")
print(f"\nAI1 Progress: {result['player1_progress']}")
print(f"AI2 Progress: {result['player2_progress']}")
