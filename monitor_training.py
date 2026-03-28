"""
Monitor ML training progress - test every 10K episodes
"""
import sys
import time
sys.path.insert(0, 'src')

from game.ml_agent import QLearningAgent  
from game.ml_engine import MLGameEngine
import statistics

def test_agent(num_games=200):
    """Quick test of current agent"""
    try:
        agent = QLearningAgent()
        agent.load('models/ml_agent.pkl')
    except:
        print("No agent found yet")
        return None
    
    engine = MLGameEngine()
    turns_list = []
    
    for _ in range(num_games):
        engine.reset()
        steps = 0
        
        while not engine.is_game_over() and steps < 50000:
            state = engine.get_state_representation()
            legal_actions = engine.get_legal_actions()
            if not legal_actions:
                break
            action = agent.get_action(state, legal_actions, training=False)
            result = engine.execute_action(action)
            if result['state'] == 'won':
                break
            steps += 1
        
        turns_list.append(engine.get_game_info()['turns'])
    
    return {
        'episodes': agent.episodes_trained,
        'avg': statistics.mean(turns_list),
        'median': statistics.median(turns_list),
        'best': min(turns_list),
        'worst': max(turns_list)
    }

print("ML Training Monitor")
print("Target: Beat 31.85 avg turns (probability strategy)")
print("=" * 60)

last_episodes = 0
while True:
    time.sleep(30)  # Check every 30 seconds
    
    result = test_agent(100)
    if result is None:
        continue
    
    # Only print if episodes increased significantly
    if result['episodes'] - last_episodes >= 2000:
        last_episodes = result['episodes']
        
        # Color code based on performance
        avg = result['avg']
        if avg <= 31.85:
            status = "✓✓✓ BEATING BASELINE!"
        elif avg <= 33:
            status = "✓✓ Close!"
        elif avg <= 35:
            status = "✓ Improving"
        else:
            status = "Training..."
        
        print(f"Ep {result['episodes']:6d} | "
              f"Avg: {result['avg']:5.2f} | "
              f"Med: {result['median']:5.1f} | "
              f"Range: {result['best']:2d}-{result['worst']:2d} | "
              f"{status}")
