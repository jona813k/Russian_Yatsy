"""
Train DQN agent for Russian Yatzy.
"""

import argparse
import time
from pathlib import Path
import torch
import sys
sys.path.append('.')

from src.game.dqn_agent import DQNAgent
from src.game.ml_engine import MLGameEngine


def train_dqn(
    episodes: int = 10000,
    target_update_freq: int = 100,
    eval_freq: int = 1000,
    eval_games: int = 100,
    save_freq: int = 5000,
    model_path: str = "models/dqn_agent.pth"
):
    """
    Train DQN agent.
    
    Args:
        episodes: Number of episodes to train
        target_update_freq: How often to update target network
        eval_freq: How often to evaluate
        eval_games: Number of games for evaluation
        save_freq: How often to save model
        model_path: Where to save model
    """
    print("Initializing DQN Agent...")
    agent = DQNAgent(
        state_dim=37,
        action_dim=13,
        learning_rate=0.0001,  # Lower LR for stability
        gamma=0.99,
        epsilon_start=1.0,
        epsilon_end=0.01,
        epsilon_decay=0.9995,
        batch_size=64,
        buffer_capacity=50000
    )
    
    print(f"\nTraining for {episodes} episodes...")
    print("="*70)
    print(f"Starting DQN Training - {episodes} episodes")
    print("="*70)
    print()
    
    start_time = time.time()
    
    # Training loop
    total_rewards = []
    total_turns = []
    losses = []
    
    for episode in range(1, episodes + 1):
        # Initialize game
        engine = MLGameEngine()
        episode_reward = 0
        episode_loss = []
        done = False
        step = 0
        max_steps = 200  # Reasonable limit for Russian Yatzy
        
        while not done and step < max_steps:
            # Get current state
            current_state_dict = {
                'dice': engine.state.dice_values,
                'progress': dict(engine.player.progress),
                'selected_number': engine.state.selected_number,
                'turns': engine.turn_number
            }
            current_state = agent.encode_state(current_state_dict)
            
            # Get legal actions
            legal_actions = engine.get_legal_actions()
            if not legal_actions:
                legal_actions = [{'type': 'skip_turn', 'number': None}]
            
            # Convert to action indices (0-11 for numbers 1-12, 12 for skip_turn)
            legal_indices = []
            for action in legal_actions:
                if action['type'] in ['select', 'collect']:
                    legal_indices.append(action['number'] - 1)
                elif action['type'] == 'skip_turn':
                    legal_indices.append(12)
            
            # Ensure we have at least one action
            if not legal_indices:
                legal_indices = [12]
            
            # Select action
            action_idx = agent.get_action(current_state, legal_indices, explore=True)
            
            # Convert back to game action
            if action_idx == 12:
                game_action = {'type': 'skip_turn', 'number': None}
            else:
                # Determine if this is a select or collect based on legal actions
                action_type = 'select'
                for act in legal_actions:
                    if act.get('number') == action_idx + 1:
                        action_type = act['type']
                        break
                game_action = {'type': action_type, 'number': action_idx + 1}
            
            # Execute action
            result = engine.execute_action(game_action)
            reward = result['reward']
            episode_reward += reward
            
            # Check if done
            done = engine.is_game_over() or result['state'] == 'won'
            
            # Get next state
            next_state_dict = {
                'dice': engine.state.dice_values,
                'progress': dict(engine.player.progress),
                'selected_number': engine.state.selected_number,
                'turns': engine.turn_number
            }
            next_state = agent.encode_state(next_state_dict)
            
            # Store transition
            agent.store_transition(current_state, action_idx, reward, next_state, done)
            
            # Train
            loss = agent.train_step()
            if loss is not None:
                episode_loss.append(loss)
            
            step += 1
            agent.steps += 1
        
        # Episode complete
        total_rewards.append(episode_reward)
        total_turns.append(engine.turn_number)
        if episode_loss:
            losses.append(sum(episode_loss) / len(episode_loss))
        
        # Decay epsilon
        agent.decay_epsilon()
        
        # Update target network
        if episode % target_update_freq == 0:
            agent.update_target_network()
        
        # Logging
        if episode % 100 == 0:
            avg_reward = sum(total_rewards[-100:]) / min(100, len(total_rewards))
            avg_turns = sum(total_turns[-100:]) / min(100, len(total_turns))
            avg_loss = sum(losses[-100:]) / min(100, len(losses)) if losses else 0
            
            elapsed = time.time() - start_time
            games_per_sec = episode / elapsed
            
            print(f"Episode {episode:5d} | "
                  f"Turns: {avg_turns:6.1f} | "
                  f"Reward: {avg_reward:7.1f} | "
                  f"Loss: {avg_loss:7.4f} | "
                  f"ε: {agent.epsilon:.4f} | "
                  f"Buffer: {len(agent.replay_buffer):6d} | "
                  f"{games_per_sec:.1f} games/s")
        
        # Evaluation
        if episode % eval_freq == 0:
            print("\nEvaluating agent...")
            eval_results = evaluate_agent(agent, eval_games)
            print(f"\nEvaluation ({eval_games} games):")
            print(f"  Completion Rate:  {eval_results['completion_rate']:.1f}%")
            print(f"  Average Turns:    {eval_results['avg_turns']:.2f}")
            print(f"  Median Turns:     {eval_results['median_turns']:.0f}")
            print(f"  Std Turns:        {eval_results['std_turns']:.2f}")
            print(f"  Range:            {eval_results['min_turns']} - {eval_results['max_turns']}")
            print()
        
        # Save model
        if episode % save_freq == 0:
            Path(model_path).parent.mkdir(parents=True, exist_ok=True)
            agent.save(model_path)
            print(f"Saved model to {model_path}")
    
    # Final save
    agent.save(model_path)
    
    elapsed = time.time() - start_time
    print("\n" + "="*70)
    print("Training Complete!")
    print("="*70)
    print(f"Total time: {elapsed:.1f}s ({elapsed/60:.1f} minutes)")
    print(f"Episodes: {episodes}")
    print(f"Updates: {agent.updates}")
    print(f"Final epsilon: {agent.epsilon:.4f}")
    print(f"Average turns (last 1000): {sum(total_turns[-1000:])/min(1000, len(total_turns)):.1f}")
    print(f"Average reward (last 1000): {sum(total_rewards[-1000:])/min(1000, len(total_rewards)):.1f}")
    print("="*70)
    print()
    
    # Final evaluation
    print("="*70)
    print("Final Evaluation...")
    print("="*70)
    eval_results = evaluate_agent(agent, 1000)
    print(f"\nEvaluation Results (1000 games):")
    print(f"  Completion Rate:  {eval_results['completion_rate']:.1f}%")
    print(f"  Average Turns:    {eval_results['avg_turns']:.2f}")
    print(f"  Median Turns:     {eval_results['median_turns']:.0f}")
    print(f"  Std Turns:        {eval_results['std_turns']:.2f}")
    print(f"  Range:            {eval_results['min_turns']} - {eval_results['max_turns']}")
    
    print(f"\n✓ Training complete!")
    print(f"Agent saved to: {model_path}")


def evaluate_agent(agent: DQNAgent, num_games: int = 100) -> dict:
    """Evaluate agent performance"""
    turns_list = []
    completed = 0
    
    for _ in range(num_games):
        engine = MLGameEngine()
        done = False
        step = 0
        max_steps = 200
        
        while not done and step < max_steps:
            # Get state
            state_dict = {
                'dice': engine.state.dice_values,
                'progress': dict(engine.player.progress),
                'selected_number': engine.state.selected_number,
                'turns': engine.turn_number
            }
            state = agent.encode_state(state_dict)
            
            # Get legal actions
            legal_actions = engine.get_legal_actions()
            if not legal_actions:
                legal_actions = [{'type': 'skip_turn', 'number': None}]
            
            legal_indices = []
            for action in legal_actions:
                if action['type'] in ['select', 'collect']:
                    legal_indices.append(action['number'] - 1)
                elif action['type'] == 'skip_turn':
                    legal_indices.append(12)
            
            # Ensure we have at least one action
            if not legal_indices:
                legal_indices = [12]
            
            # Select action (no exploration)
            action_idx = agent.get_action(state, legal_indices, explore=False)
            
            # Convert to game action
            if action_idx == 12:
                game_action = {'type': 'skip_turn', 'number': None}
            else:
                # Determine if this is a select or collect based on legal actions
                action_type = 'select'
                for act in legal_actions:
                    if act.get('number') == action_idx + 1:
                        action_type = act['type']
                        break
                game_action = {'type': action_type, 'number': action_idx + 1}
            
            # Execute
            result = engine.execute_action(game_action)
            done = engine.is_game_over()
            step += 1
        
        if engine.is_game_over():
            completed += 1
            turns_list.append(engine.turn_number)
        else:
            turns_list.append(500)  # Failed
    
    if turns_list:
        import numpy as np
        return {
            'completion_rate': (completed / num_games) * 100,
            'avg_turns': np.mean(turns_list),
            'median_turns': np.median(turns_list),
            'std_turns': np.std(turns_list),
            'min_turns': np.min(turns_list),
            'max_turns': np.max(turns_list)
        }
    else:
        return {
            'completion_rate': 0,
            'avg_turns': 0,
            'median_turns': 0,
            'std_turns': 0,
            'min_turns': 0,
            'max_turns': 0
        }


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Train DQN agent for Russian Yatzy")
    parser.add_argument("--episodes", type=int, default=10000, help="Number of episodes")
    parser.add_argument("--mode", type=str, default="normal", choices=["quick", "normal", "extended"],
                        help="Training mode (quick=5K, normal=10K, extended=50K)")
    
    args = parser.parse_args()
    
    if args.mode == "quick":
        episodes = 5000
    elif args.mode == "extended":
        episodes = 50000
    else:
        episodes = args.episodes
    
    train_dqn(episodes=episodes)
