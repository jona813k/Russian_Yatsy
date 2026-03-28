"""
ML Training System for Russian Yatzy
"""
import time
from pathlib import Path
from game.ml_engine import MLGameEngine
from game.ml_agent import QLearningAgent
import numpy as np


class MLTrainer:
    """Trains ML agents through self-play"""
    
    def __init__(self, agent: QLearningAgent, verbose=True):
        self.agent = agent
        self.verbose = verbose
        self.engine = MLGameEngine()
        
        # Training statistics
        self.episode_scores = []
        self.episode_turns = []
        self.episode_rolls = []
        self.episode_rewards = []
    
    def train(self, episodes=10000, save_every=1000, save_path='models/ml_agent.pkl'):
        """
        Train agent for specified number of episodes.
        
        Args:
            episodes: Number of games to play
            save_every: Save checkpoint every N episodes
            save_path: Path to save model
        """
        print(f"\n{'='*70}")
        print(f"Starting ML Training - {episodes} episodes")
        print(f"{'='*70}\n")
        
        start_time = time.time()
        
        for episode in range(episodes):
            # Play one game
            total_reward = self.play_episode()
            
            # Decay exploration
            self.agent.decay_epsilon()
            self.agent.episodes_trained += 1
            
            # Log progress
            if self.verbose and (episode + 1) % 100 == 0:
                self._log_progress(episode + 1, start_time)
            
            # Save checkpoint
            if (episode + 1) % save_every == 0:
                self.save_checkpoint(save_path)
        
        # Final save
        self.save_checkpoint(save_path)
        
        # Final statistics
        self._print_final_stats(start_time)
        
        return {
            'turns': self.episode_turns,
            'rolls': self.episode_rolls,
            'rewards': self.episode_rewards
        }
    
    def play_episode(self) -> float:
        """
        Play one complete game and update Q-values.
        Returns total reward accumulated.
        """
        self.engine.reset()
        total_reward = 0
        step_count = 0
        max_steps = 50000  # Safety limit - Russian Yatzy can be long!
        
        while not self.engine.is_game_over() and step_count < max_steps:
            # Get current state
            state = self.engine.get_state_representation()
            
            # Get legal actions
            legal_actions = self.engine.get_legal_actions()
            
            if not legal_actions:
                # No legal actions available (shouldn't happen)
                break
            
            # Agent selects action
            action = self.agent.get_action(state, legal_actions, training=True)
            
            # Execute action
            result = self.engine.execute_action(action)
            
            if not result['success']:
                # Illegal action somehow (shouldn't happen)
                print(f"Warning: Illegal action attempted: {action}")
                break
            
            reward = result['reward']
            total_reward += reward
            
            # Handle different states
            if result['state'] == 'won':
                # Game won!
                self.agent.update(state, action, reward, None, [], done=True)
                break
            
            elif result['state'] in ['continue', 'completed_number', 'bonus_turn']:
                # Game continues - get next state
                next_state = self.engine.get_state_representation()
                next_legal_actions = self.engine.get_legal_actions()
                
                # Aggressive turn penalty to strongly encourage efficiency
                turn_penalty = -3.0
                reward += turn_penalty
                total_reward += turn_penalty
                
                self.agent.update(state, action, reward, next_state, next_legal_actions, done=False)
            
            elif result['state'] == 'turn_end':
                # Turn ended without completing number - harsh penalty
                turn_penalty = -5.0
                reward += turn_penalty
                total_reward += turn_penalty
                
                next_state = self.engine.get_state_representation()
                next_legal_actions = self.engine.get_legal_actions()
                self.agent.update(state, action, reward, next_state, next_legal_actions, done=False)
            
            step_count += 1
        
        # Record episode stats
        game_info = self.engine.get_game_info()
        self.episode_turns.append(game_info['turns'])
        self.episode_rolls.append(game_info['rolls'])
        self.episode_rewards.append(total_reward)
        
        return total_reward
    
    def evaluate(self, num_games=100) -> dict:
        """
        Evaluate agent performance (no training).
        Returns statistics about performance.
        """
        print(f"\nEvaluating agent over {num_games} games...")
        
        turns_list = []
        rolls_list = []
        completed_games = 0
        
        old_epsilon = self.agent.epsilon
        self.agent.epsilon = 0  # No exploration during evaluation
        
        for game in range(num_games):
            self.engine.reset()
            step_count = 0
            max_steps = 50000  # Match training limit
            
            while not self.engine.is_game_over() and step_count < max_steps:
                state = self.engine.get_state_representation()
                legal_actions = self.engine.get_legal_actions()
                
                if not legal_actions:
                    break
                
                action = self.agent.get_action(state, legal_actions, training=False)
                result = self.engine.execute_action(action)
                
                if not result['success'] or result['state'] == 'won':
                    break
                
                step_count += 1
            
            game_info = self.engine.get_game_info()
            turns_list.append(game_info['turns'])
            rolls_list.append(game_info['rolls'])
            
            if game_info['is_won']:
                completed_games += 1
        
        self.agent.epsilon = old_epsilon  # Restore epsilon
        
        return {
            'games_completed': completed_games,
            'completion_rate': completed_games / num_games * 100,
            'avg_turns': np.mean(turns_list),
            'median_turns': np.median(turns_list),
            'avg_rolls': np.mean(rolls_list),
            'median_rolls': np.median(rolls_list),
            'min_turns': np.min(turns_list),
            'max_turns': np.max(turns_list),
            'std_turns': np.std(turns_list),
            'turns_range': np.max(turns_list) - np.min(turns_list)
        }
    
    def _log_progress(self, episode: int, start_time: float):
        """Log training progress"""
        recent_turns = self.episode_turns[-100:] if len(self.episode_turns) >= 100 else self.episode_turns
        recent_rolls = self.episode_rolls[-100:] if len(self.episode_rolls) >= 100 else self.episode_rolls
        recent_rewards = self.episode_rewards[-100:] if len(self.episode_rewards) >= 100 else self.episode_rewards
        
        avg_turns = np.mean(recent_turns)
        avg_rolls = np.mean(recent_rolls)
        avg_reward = np.mean(recent_rewards)
        
        elapsed = time.time() - start_time
        games_per_sec = episode / elapsed
        
        print(f"Episode {episode:6d} | "
              f"Turns: {avg_turns:6.1f} | "
              f"Rolls: {avg_rolls:6.1f} | "
              f"Reward: {avg_reward:7.1f} | "
              f"e: {self.agent.epsilon:.4f} | "
              f"States: {len(self.agent.q_table):7d} | "
              f"{games_per_sec:.1f} games/s")
    
    def _print_final_stats(self, start_time: float):
        """Print final training statistics"""
        elapsed = time.time() - start_time
        
        print(f"\n{'='*70}")
        print(f"Training Complete!")
        print(f"{'='*70}")
        print(f"Total time: {elapsed:.1f}s ({elapsed/60:.1f} minutes)")
        print(f"Episodes: {self.agent.episodes_trained}")
        print(f"States explored: {len(self.agent.q_table)}")
        print(f"Q-value updates: {self.agent.total_updates}")
        print(f"Final epsilon: {self.agent.epsilon:.4f}")
        print(f"Average turns (last 1000): {np.mean(self.episode_turns[-1000:]):.1f}")
        print(f"Average rolls (last 1000): {np.mean(self.episode_rolls[-1000:]):.1f}")
        print(f"{'='*70}\n")
    
    def save_checkpoint(self, path: str):
        """Save agent checkpoint"""
        self.agent.save(path)
