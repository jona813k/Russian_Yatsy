"""
Q-Learning Agent for Russian Yatzy
"""
import random
import pickle
import numpy as np
from collections import defaultdict
from pathlib import Path


class QLearningAgent:
    """
    Q-Learning agent that learns optimal strategy through experience.
    Uses epsilon-greedy exploration and temporal difference learning.
    """
    
    def __init__(self, learning_rate=0.3, discount_factor=0.98, epsilon=0.3, epsilon_decay=0.9998, epsilon_min=0.01):
        """
        Initialize Q-Learning agent.
        
        Args:
            learning_rate: How quickly to update Q-values (alpha)
            discount_factor: Future reward importance (gamma)
            epsilon: Exploration rate (0=exploit, 1=explore)
            epsilon_decay: Decay rate per episode
            epsilon_min: Minimum exploration rate
        """
        self.q_table = defaultdict(lambda: defaultdict(float))
        self.lr = learning_rate
        self.gamma = discount_factor
        self.epsilon = epsilon
        self.epsilon_decay = epsilon_decay
        self.epsilon_min = epsilon_min
        
        # Statistics
        self.episodes_trained = 0
        self.total_updates = 0
    
    def get_action(self, state: tuple, legal_actions: list, training=True) -> dict:
        """
        Select action using epsilon-greedy policy.
        
        Args:
            state: Current game state (hashable tuple)
            legal_actions: List of legal action dicts
            training: If False, always exploit (no exploration)
        
        Returns:
            Selected action dict
        """
        if not legal_actions:
            raise ValueError("No legal actions available!")
        
        # Exploration: random action
        if training and random.random() < self.epsilon:
            return random.choice(legal_actions)
        
        # Exploitation: best known action
        action_values = {}
        for action in legal_actions:
            action_key = self._action_to_key(action)
            action_values[action_key] = self.q_table[state][action_key]
        
        # Get max Q-value
        max_q = max(action_values.values()) if action_values else 0
        
        # Get all actions with max Q-value (handle ties randomly)
        best_action_keys = [k for k, v in action_values.items() if v == max_q]
        selected_key = random.choice(best_action_keys)
        
        # Find corresponding action
        for action in legal_actions:
            if self._action_to_key(action) == selected_key:
                return action
        
        # Fallback (shouldn't reach here)
        return legal_actions[0]
    
    def update(self, state: tuple, action: dict, reward: float, next_state: tuple, next_legal_actions: list, done: bool):
        """
        Update Q-value using TD learning.
        
        Q(s,a) = Q(s,a) + α * [r + γ * max(Q(s',a')) - Q(s,a)]
        """
        action_key = self._action_to_key(action)
        current_q = self.q_table[state][action_key]
        
        # Calculate max Q-value for next state
        if done or not next_legal_actions:
            max_next_q = 0
        else:
            next_q_values = [
                self.q_table[next_state][self._action_to_key(a)] 
                for a in next_legal_actions
            ]
            max_next_q = max(next_q_values) if next_q_values else 0
        
        # TD update
        td_target = reward + self.gamma * max_next_q
        td_error = td_target - current_q
        new_q = current_q + self.lr * td_error
        
        self.q_table[state][action_key] = new_q
        self.total_updates += 1
    
    def decay_epsilon(self):
        """Decay exploration rate"""
        self.epsilon = max(self.epsilon_min, self.epsilon * self.epsilon_decay)
    
    def _action_to_key(self, action: dict) -> tuple:
        """Convert action dict to hashable key"""
        return (action['type'], action.get('number', 0))
    
    def save(self, filepath: str):
        """Save Q-table and parameters to file"""
        data = {
            'q_table': dict(self.q_table),
            'lr': self.lr,
            'gamma': self.gamma,
            'epsilon': self.epsilon,
            'episodes_trained': self.episodes_trained,
            'total_updates': self.total_updates
        }
        
        path = Path(filepath)
        path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(filepath, 'wb') as f:
            pickle.dump(data, f)
        
        print(f"Saved Q-table with {len(self.q_table)} states to {filepath}")
    
    def load(self, filepath: str):
        """Load Q-table and parameters from file"""
        with open(filepath, 'rb') as f:
            data = pickle.load(f)
        
        # Convert back to defaultdict
        loaded_q_table = data['q_table']
        self.q_table = defaultdict(lambda: defaultdict(float))
        for state, actions in loaded_q_table.items():
            for action, value in actions.items():
                self.q_table[state][action] = value
        
        self.lr = data.get('lr', self.lr)
        self.gamma = data.get('gamma', self.gamma)
        self.epsilon = data.get('epsilon', self.epsilon)
        self.episodes_trained = data.get('episodes_trained', 0)
        self.total_updates = data.get('total_updates', 0)
        
        print(f"Loaded Q-table with {len(self.q_table)} states from {filepath}")
        print(f"Episodes trained: {self.episodes_trained}, Updates: {self.total_updates}")
    
    def get_stats(self) -> dict:
        """Get agent statistics"""
        return {
            'states_explored': len(self.q_table),
            'total_updates': self.total_updates,
            'episodes_trained': self.episodes_trained,
            'epsilon': self.epsilon,
            'learning_rate': self.lr,
            'discount_factor': self.gamma
        }


class DeepQLearningAgent:
    """
    Deep Q-Network agent using neural network for large state spaces.
    TODO: Implement when basic Q-Learning is working well.
    """
    
    def __init__(self):
        raise NotImplementedError("Deep Q-Learning not yet implemented. Use QLearningAgent for now.")
