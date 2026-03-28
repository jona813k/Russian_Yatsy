"""
Continue training existing SimpleDQN model (28.1 turns baseline)
Loads the existing model and trains for additional episodes
"""
import sys
sys.path.insert(0, 'src')

import argparse
from src.game.dqn_agent_simple import SimpleDQNAgent
from src.game.ml_engine import MLGameEngine
import time
import numpy as np
from pathlib import Path


def continue_training(episodes: int = 20000, model_path: str = 'models/simple_dqn_agent.pth'):
    """Continue training from existing model"""
    
    print("="*70)
    print("CONTINUING DQN TRAINING FROM EXISTING MODEL")
    print("="*70)
    print(f"Loading model from: {model_path}")
    print(f"Additional episodes: {episodes:,}")
    print(f"Current performance: 28.1 turns (baseline)")
    print(f"Target: <25 turns")
    print("="*70)
    
    # Create agent with same config as original
    agent = SimpleDQNAgent(
        learning_rate=0.0005,
        discount_factor=0.95,
        epsilon=0.05,  # Start with low exploration (already trained)
        epsilon_min=0.01,  # Even lower minimum
        epsilon_decay=0.9998,  # Slower decay
        memory_size=20000,
        batch_size=64
    )
    
    # Load existing model
    if Path(model_path).exists():
        agent.load(model_path)
        print(f"✓ Model loaded successfully!")
        print(f"  Starting epsilon: {agent.epsilon:.4f}")
    else:
        print(f"✗ Model not found at {model_path}")
        print(f"  Training from scratch instead...")
    
    engine = MLGameEngine()
    
    start_time = time.time()
    turns_history = []
    rewards_history = []
    total_updates = 0
    best_avg_turns = 28.1  # Current baseline
    
    for episode in range(1, episodes + 1):
        engine.reset()
        engine.start_new_turn()
        
        total_reward = 0
        steps = 0
        max_steps = 200
        
        while not engine.is_game_over() and steps < max_steps:
            state = engine.get_state_representation()
            legal_actions = engine.get_legal_actions()
            
            if not legal_actions:
                break
            
            action = agent.get_action(state, legal_actions, training=True)
            result = engine.execute_action(action)
            
            reward = result['reward']
            total_reward += reward
            
            next_state = engine.get_state_representation()
            done = result['state'] == 'won'
            
            agent.remember(state, action, reward, next_state, done)
            
            if done:
                break
            
            steps += 1
        
        # Train after each episode
        if len(agent.memory) >= agent.batch_size:
            for _ in range(5):
                loss = agent.replay()
                total_updates += 1
        
        game_info = engine.get_game_info()
        turns_history.append(game_info['turns'])
        rewards_history.append(total_reward)
        
        if episode % 100 == 0:
            avg_turns = sum(turns_history[-100:]) / min(100, len(turns_history))
            avg_reward = sum(rewards_history[-100:]) / min(100, len(rewards_history))
            elapsed = time.time() - start_time
            eps = episode / elapsed
            
            print(f"Episode {episode:5d} | Turns: {avg_turns:5.1f} | "
                  f"Reward: {avg_reward:7.1f} | ε: {agent.epsilon:.4f} | "
                  f"Updates: {total_updates:6d} | {eps:.1f} games/s")
        
        if episode % 1000 == 0:
            # Evaluation
            eval_turns = []
            
            print(f"\nEvaluating at episode {episode:,}...")
            for _ in range(100):
                engine.reset()
                engine.start_new_turn()
                
                eval_steps = 0
                while not engine.is_game_over() and eval_steps < 200:
                    state = engine.get_state_representation()
                    legal_actions = engine.get_legal_actions()
                    if not legal_actions:
                        break
                    action = agent.get_action(state, legal_actions, training=False)
                    result = engine.execute_action(action)
                    if result['state'] == 'won':
                        break
                    eval_steps += 1
                
                eval_turns.append(engine.get_game_info()['turns'])
            
            avg_eval_turns = sum(eval_turns) / len(eval_turns)
            med_eval_turns = sorted(eval_turns)[len(eval_turns)//2]
            std_eval_turns = np.std(eval_turns)
            
            print(f"\n{'='*70}")
            print(f"Evaluation at episode {episode:,} (100 games):")
            print(f"  Average Turns: {avg_eval_turns:.2f}")
            print(f"  Median Turns:  {med_eval_turns}")
            print(f"  Std Dev:       {std_eval_turns:.2f}")
            print(f"  Best so far:   {best_avg_turns:.2f}")
            print(f"  Target:        <25 turns")
            
            # Check if improved
            if avg_eval_turns < best_avg_turns:
                improvement = best_avg_turns - avg_eval_turns
                best_avg_turns = avg_eval_turns
                agent.save('models/simple_dqn_agent_improved.pth')
                print(f"  ⭐ NEW BEST! Improved by {improvement:.2f} turns")
                print(f"     Saved to: simple_dqn_agent_improved.pth")
            
            if avg_eval_turns < 25:
                print(f"  🏆 TARGET ACHIEVED! {avg_eval_turns:.2f} < 25 turns!")
            else:
                gap = avg_eval_turns - 25
                print(f"  Gap to target: +{gap:.2f} turns")
            
            print(f"{'='*70}\n")
            
            # Save checkpoint
            agent.save('models/simple_dqn_agent_checkpoint.pth')
    
    # Final evaluation
    print("\n" + "="*70)
    print("FINAL EVALUATION (1000 games)")
    print("="*70)
    
    final_turns = []
    
    for i in range(1000):
        if i % 100 == 0:
            print(f"  Progress: {i}/1000 games")
        
        engine.reset()
        engine.start_new_turn()
        
        eval_steps = 0
        while not engine.is_game_over() and eval_steps < 200:
            state = engine.get_state_representation()
            legal_actions = engine.get_legal_actions()
            if not legal_actions:
                break
            action = agent.get_action(state, legal_actions, training=False)
            result = engine.execute_action(action)
            if result['state'] == 'won':
                break
            eval_steps += 1
        
        final_turns.append(engine.get_game_info()['turns'])
    
    avg_final = sum(final_turns) / len(final_turns)
    med_final = sorted(final_turns)[len(final_turns)//2]
    std_final = np.std(final_turns)
    
    print(f"\nStarting performance: 28.1 turns")
    print(f"Final performance:    {avg_final:.2f} turns")
    print(f"Median Turns:         {med_final}")
    print(f"Std Dev:              {std_final:.2f}")
    print(f"Best during training: {best_avg_turns:.2f}")
    
    if avg_final < 28.1:
        improvement = 28.1 - avg_final
        pct = (improvement / 28.1) * 100
        print(f"\n✓ IMPROVEMENT! {improvement:.2f} turns better ({pct:.1f}% improvement)")
    
    if avg_final < 25:
        print(f"🏆 TARGET ACHIEVED! Sub-25 turns!")
    else:
        gap = avg_final - 25
        print(f"\nGap to target: +{gap:.2f} turns")
    
    elapsed = time.time() - start_time
    print(f"\nTraining time: {elapsed:.1f}s ({elapsed/60:.1f} minutes)")
    print(f"Final model saved to: models/simple_dqn_agent_checkpoint.pth")
    print("="*70)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('--episodes', type=int, default=20000, 
                        help='Number of additional episodes to train (default: 20,000)')
    parser.add_argument('--model', type=str, default='models/simple_dqn_agent.pth',
                        help='Path to existing model to continue from')
    args = parser.parse_args()
    
    continue_training(args.episodes, args.model)
