"""
Train optimized DQN targeting sub-25 turn performance
Features: 25 (6 dice + 12 progress + 2 hard flags + 5 strategic)
Network: 25 → 128 → 128 → 64 → 13 (deeper with batch norm)
Target: <25 turns average (match human expert performance)
"""
import sys
sys.path.insert(0, 'src')

import argparse
from src.game.dqn_agent_simple import SimpleDQNAgent
from src.game.ml_engine import MLGameEngine
import time
import numpy as np


def train_simple_dqn(episodes: int = 100000):
    """Train optimized DQN with enhanced features and rewards"""
    
    print("="*70)
    print("TRAINING OPTIMIZED DQN - TARGET: SUB-25 TURNS")
    print("="*70)
    print(f"Episodes: {episodes:,}")
    print(f"Features: 25 (enhanced with strategic info)")
    print(f"Network: 25 → 128 → 128 → 64 → 13 (deeper!)")
    print(f"Rewards: Optimized for hard numbers, efficiency, and completion")
    print(f"Target: <25 turns (human expert level)")
    print(f"Baseline: 28.1 turns (current DQN)")
    print("="*70)
    
    # Use optimized hyperparameters from SimpleDQNAgent defaults
    agent = SimpleDQNAgent()
    
    engine = MLGameEngine()
    
    start_time = time.time()
    turns_history = []
    rewards_history = []
    skip_counts = []
    total_updates = 0
    best_avg_turns = float('inf')  # Track best performance
    
    for episode in range(1, episodes + 1):
        engine.reset()
        engine.start_new_turn()
        
        total_reward = 0
        steps = 0
        skips = 0
        max_steps = 200
        
        while not engine.is_game_over() and steps < max_steps:
            state = engine.get_state_representation()
            legal_actions = engine.get_legal_actions()
            
            if not legal_actions:
                break
            
            action = agent.get_action(state, legal_actions, training=True)
            
            # Track skip turns
            if action['type'] == 'skip_turn':
                skips += 1
            
            result = engine.execute_action(action)
            
            reward = result['reward']
            total_reward += reward
            
            next_state = engine.get_state_representation()
            done = result['state'] == 'won'
            
            agent.remember(state, action, reward, next_state, done)
            
            if done:
                break
            
            steps += 1
        
        # Train after each episode (not every step!)
        if len(agent.memory) >= agent.batch_size:
            # Do multiple training updates per episode
            for _ in range(5):
                loss = agent.replay()
                total_updates += 1
        
        game_info = engine.get_game_info()
        turns_history.append(game_info['turns'])
        rewards_history.append(total_reward)
        skip_counts.append(skips)
        
        if episode % 100 == 0:
            avg_turns = sum(turns_history[-100:]) / min(100, len(turns_history))
            avg_reward = sum(rewards_history[-100:]) / min(100, len(rewards_history))
            avg_skips = sum(skip_counts[-100:]) / min(100, len(skip_counts))
            elapsed = time.time() - start_time
            eps = episode / elapsed
            
            print(f"Episode {episode:5d} | Turns: {avg_turns:5.1f} | "
                  f"Reward: {avg_reward:7.1f} | Skips: {avg_skips:4.1f} | "
                  f"ε: {agent.epsilon:.4f} | Updates: {total_updates:6d} | "
                  f"{eps:.1f} games/s")
        
        if episode % 1000 == 0:
            # Evaluation
            eval_turns = []
            eval_skips = []
            
            print(f"\nEvaluating at episode {episode:,}...")
            for _ in range(100):
                engine.reset()
                engine.start_new_turn()
                
                game_skips = 0
                eval_steps = 0
                while not engine.is_game_over() and eval_steps < 200:
                    state = engine.get_state_representation()
                    legal_actions = engine.get_legal_actions()
                    if not legal_actions:
                        break
                    action = agent.get_action(state, legal_actions, training=False)
                    if action['type'] == 'skip_turn':
                        game_skips += 1
                    result = engine.execute_action(action)
                    if result['state'] == 'won':
                        break
                    eval_steps += 1
                
                eval_turns.append(engine.get_game_info()['turns'])
                eval_skips.append(game_skips)
            
            avg_eval_turns = sum(eval_turns) / len(eval_turns)
            avg_eval_skips = sum(eval_skips) / len(eval_skips)
            med_eval_turns = sorted(eval_turns)[len(eval_turns)//2]
            std_eval_turns = np.std(eval_turns)
            
            print(f"\n{'='*70}")
            print(f"Evaluation at episode {episode:,} (100 games):")
            print(f"  Average Turns: {avg_eval_turns:.2f}")
            print(f"  Median Turns:  {med_eval_turns}")
            print(f"  Std Dev:       {std_eval_turns:.2f}")
            print(f"  Average Skips: {avg_eval_skips:.2f}")
            print(f"  Current Best:  {best_avg_turns:.2f}")
            print(f"  Target:        <25 turns")
            
            # Check if this is the best model so far
            if avg_eval_turns < best_avg_turns:
                best_avg_turns = avg_eval_turns
                agent.save('models/simple_dqn_agent_best.pth')
                print(f"  ⭐ NEW BEST! Saved to simple_dqn_agent_best.pth")
            
            if avg_eval_turns < 25:
                print(f"  🎉 TARGET ACHIEVED! {avg_eval_turns:.2f} < 25 turns!")
            elif avg_eval_turns < 28.1:
                improvement = ((28.1 - avg_eval_turns) / 28.1) * 100
                print(f"  🚀 Beating previous DQN by {improvement:.1f}%!")
            else:
                gap = avg_eval_turns - 25
                print(f"  Gap to target: +{gap:.2f} turns")
            
            print(f"{'='*70}\n")
            
            agent.save('models/simple_dqn_agent.pth')
    
    elapsed = time.time() - start_time
    
    # Final evaluation
    print("\n" + "="*70)
    print("FINAL EVALUATION (1000 games)")
    print("="*70)
    
    final_turns = []
    final_skips = []
    
    for i in range(1000):
        if i % 100 == 0:
            print(f"  Progress: {i}/1000 games")
        
        engine.reset()
        engine.start_new_turn()
        
        game_skips = 0
        eval_steps = 0
        while not engine.is_game_over() and eval_steps < 200:
            state = engine.get_state_representation()
            legal_actions = engine.get_legal_actions()
            if not legal_actions:
                break
            action = agent.get_action(state, legal_actions, training=False)
            if action['type'] == 'skip_turn':
                game_skips += 1
            result = engine.execute_action(action)
            if result['state'] == 'won':
                break
            eval_steps += 1
        
        final_turns.append(engine.get_game_info()['turns'])
        final_skips.append(game_skips)
    
    avg_final = sum(final_turns) / len(final_turns)
    med_final = sorted(final_turns)[len(final_turns)//2]
    std_final = np.std(final_turns)
    avg_skip = sum(final_skips) / len(final_skips)
    
    print(f"\nAverage Turns:    {avg_final:.2f}")
    print(f"Median Turns:     {med_final}")
    print(f"Std Dev:          {std_final:.2f}")
    print(f"Average Skips:    {avg_skip:.2f}")
    print(f"Best during training: {best_avg_turns:.2f}")
    print(f"Target:           <25 turns (human expert)")
    print(f"Previous DQN:     28.1 turns")
    
    if avg_final < 25:
        improvement = ((25 - avg_final) / 25) * 100
        print(f"\n🏆 EXCELLENT! Target achieved: {avg_final:.2f} < 25 turns!")
        print(f"    {improvement:.1f}% better than target!")
    elif avg_final < 28.1:
        improvement = ((28.1 - avg_final) / 28.1) * 100
        gap_to_target = avg_final - 25
        print(f"\n🚀 IMPROVEMENT! Beating previous DQN by {improvement:.1f}%")
        print(f"    Gap to target: +{gap_to_target:.2f} turns")
    else:
        gap = avg_final - 25
        print(f"\nGap to target: +{gap:.2f} turns")
        print(f"    Need more training or reward tuning")
    
    print(f"\nTraining time: {elapsed:.1f}s ({elapsed/60:.1f} minutes)")
    print(f"Model saved to: models/simple_dqn_agent.pth")
    print("="*70)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('--episodes', type=int, default=100000, 
                        help='Number of episodes to train (default: 100,000 for sub-25 target)')
    args = parser.parse_args()
    
    train_simple_dqn(args.episodes)
