"""
Deep Q-Network (DQN) implementation for Russian Yatzy.

Uses neural network to approximate Q-values, which generalizes better
than tabular Q-learning across the massive state space.
"""

import torch
import torch.nn as nn
import torch.optim as optim
import numpy as np
from collections import deque, namedtuple
import random


Transition = namedtuple('Transition', ['state', 'action', 'reward', 'next_state', 'done'])


class DQN(nn.Module):
    """
    Deep Q-Network for Russian Yatzy.
    
    Input: Game state vector
    Output: Q-values for each possible action
    """
    
    def __init__(self, state_dim: int, action_dim: int):
        super(DQN, self).__init__()
        
        # Network architecture
        self.fc1 = nn.Linear(state_dim, 256)
        self.fc2 = nn.Linear(256, 256)
        self.fc3 = nn.Linear(256, 128)
        self.fc4 = nn.Linear(128, action_dim)
        
        # Activation
        self.relu = nn.ReLU()
        
    def forward(self, x):
        """Forward pass"""
        x = self.relu(self.fc1(x))
        x = self.relu(self.fc2(x))
        x = self.relu(self.fc3(x))
        x = self.fc4(x)
        return x


class ReplayBuffer:
    """Experience replay buffer for DQN"""
    
    def __init__(self, capacity: int = 50000):
        self.buffer = deque(maxlen=capacity)
    
    def push(self, transition: Transition):
        """Add transition to buffer"""
        self.buffer.append(transition)
    
    def sample(self, batch_size: int):
        """Sample random batch"""
        return random.sample(self.buffer, batch_size)
    
    def __len__(self):
        return len(self.buffer)


class DQNAgent:
    """
    DQN Agent for Russian Yatzy.
    """
    
    def __init__(
        self,
        state_dim: int = 37,  # 6 dice + 12 progress + 12 rarity scores + 6 features + 1 selected
        action_dim: int = 13,  # 12 numbers + skip_turn
        learning_rate: float = 0.001,
        gamma: float = 0.99,
        epsilon_start: float = 1.0,
        epsilon_end: float = 0.01,
        epsilon_decay: float = 0.995,
        batch_size: int = 64,
        buffer_capacity: int = 50000
    ):
        self.state_dim = state_dim
        self.action_dim = action_dim
        self.gamma = gamma
        self.epsilon = epsilon_start
        self.epsilon_end = epsilon_end
        self.epsilon_decay = epsilon_decay
        self.batch_size = batch_size
        
        # Networks
        self.policy_net = DQN(state_dim, action_dim)
        self.target_net = DQN(state_dim, action_dim)
        self.target_net.load_state_dict(self.policy_net.state_dict())
        self.target_net.eval()
        
        # Optimizer
        self.optimizer = optim.Adam(self.policy_net.parameters(), lr=learning_rate)
        self.loss_fn = nn.SmoothL1Loss()
        
        # Replay buffer
        self.replay_buffer = ReplayBuffer(buffer_capacity)
        
        # Training stats
        self.steps = 0
        self.updates = 0
        
    def encode_state(self, game_state: dict) -> np.ndarray:
        """
        Encode game state as feature vector.
        
        Features:
        - Dice counts (6): count of each die value 1-6
        - Progress (12): count collected for each number
        - Rarity scores (12): inverse probability for each number
        - Game features (6): total_collected, numbers_completed, turns, epsilon, selected, can_continue
        - Selected number (1): current selection or 0
        
        Total: 37 features
        """
        dice = game_state['dice']
        progress = game_state['progress']
        selected = game_state.get('selected_number', 0)
        turns = game_state.get('turns', 0)
        
        # Dice counts (6 features)
        dice_counts = np.zeros(6)
        for d in dice:
            if 1 <= d <= 6:
                dice_counts[d-1] += 1
        
        # Progress (12 features) - normalized to [0, 1]
        progress_vec = np.array([progress.get(i, 0) / 6.0 for i in range(1, 13)])
        
        # Rarity scores (12 features) - how rare is getting this number from current dice
        rarity_vec = np.zeros(12)
        for target in range(1, 13):
            count = self._count_possible(dice, target)
            if count > 0:
                prob = self._calculate_probability(len(dice), count, target)
                rarity_vec[target-1] = min(1.0 / (prob + 0.001), 10.0) / 10.0  # Normalize
        
        # Game features (6 features)
        total_collected = sum(progress.values())
        numbers_completed = sum(1 for v in progress.values() if v >= 6)
        
        # Handle None for selected number
        selected_val = selected if selected is not None else 0
        
        game_features = np.array([
            total_collected / 72.0,  # Progress toward 72 dice
            numbers_completed / 12.0,  # Progress toward 12 numbers
            turns / 100.0,  # Turn number (normalized)
            self.epsilon,  # Current exploration rate
            1.0 if selected_val > 0 else 0.0,  # Have selection
            1.0 if selected_val > 0 and self._can_continue(dice, selected_val, progress) else 0.0  # Can continue
        ])
        
        # Selected number (1 feature) - one-hot style
        selected_vec = np.array([selected_val / 12.0])  # Normalized
        
        # Concatenate all features
        state_vector = np.concatenate([
            dice_counts / 6.0,  # Normalize dice counts
            progress_vec,
            rarity_vec,
            game_features,
            selected_vec
        ])
        
        return state_vector.astype(np.float32)
    
    def _count_possible(self, dice: list, target: int) -> int:
        """Count how many of target can be made from dice"""
        if target <= 6:
            return dice.count(target)
        else:
            # Pairs
            if target == 7:  # (1,1)
                target1, target2 = 1, 1
            elif target == 8:  # (2,2)
                target1, target2 = 2, 2
            elif target == 9:  # (3,3)
                target1, target2 = 3, 3
            elif target == 10:  # (4,4)
                target1, target2 = 4, 4
            elif target == 11:  # (5,6) or (6,5)
                target1, target2 = 5, 6
            elif target == 12:  # (6,6)
                target1, target2 = 6, 6
            else:
                return 0
            
            count = 0
            remaining = list(dice)
            while True:
                if target1 in remaining and target2 in remaining:
                    remaining.remove(target1)
                    if target1 == target2:
                        # For doubles, need to check again
                        if target2 in remaining:
                            remaining.remove(target2)
                            count += 1
                        else:
                            break
                    else:
                        remaining.remove(target2)
                        count += 1
                else:
                    break
            return count
    
    def _calculate_probability(self, n_dice: int, count: int, target: int) -> float:
        """Calculate probability of getting count of target from n_dice"""
        if count == 0 or n_dice == 0:
            return 0.0
        
        if target <= 6:
            # Binomial probability
            p = 1/6
            if count > n_dice:
                return 0.0
            # Simplified binomial
            prob = (p ** count) * ((1-p) ** (n_dice - count))
            return prob
        else:
            # Pairs - approximate
            return (0.27 ** count)
    
    def _can_continue(self, dice: list, selected: int, progress: dict) -> bool:
        """Check if can continue with selected number"""
        if selected == 0 or selected is None:
            return False
        if progress.get(selected, 0) >= 6:
            return False
        return self._count_possible(dice, selected) > 0
    
    def get_action(self, state_vector: np.ndarray, legal_actions: list, explore: bool = True) -> int:
        """
        Select action using epsilon-greedy policy.
        
        Args:
            state_vector: Encoded state
            legal_actions: List of legal action indices
            explore: Whether to use exploration
            
        Returns:
            Action index
        """
        # Exploration
        if explore and random.random() < self.epsilon:
            return random.choice(legal_actions)
        
        # Exploitation
        with torch.no_grad():
            state_tensor = torch.FloatTensor(state_vector).unsqueeze(0)
            q_values = self.policy_net(state_tensor).squeeze()
            
            # Mask illegal actions
            masked_q = q_values.clone()
            for i in range(self.action_dim):
                if i not in legal_actions:
                    masked_q[i] = float('-inf')
            
            return masked_q.argmax().item()
    
    def store_transition(self, state, action, reward, next_state, done):
        """Store transition in replay buffer"""
        transition = Transition(state, action, reward, next_state, done)
        self.replay_buffer.push(transition)
    
    def train_step(self):
        """Perform one training step"""
        if len(self.replay_buffer) < self.batch_size:
            return None
        
        # Sample batch
        batch = self.replay_buffer.sample(self.batch_size)
        
        # Convert to tensors
        states = torch.FloatTensor(np.array([t.state for t in batch]))
        actions = torch.LongTensor([t.action for t in batch])
        rewards = torch.FloatTensor([t.reward for t in batch])
        next_states = torch.FloatTensor(np.array([t.next_state for t in batch]))
        dones = torch.FloatTensor([t.done for t in batch])
        
        # Current Q values
        current_q = self.policy_net(states).gather(1, actions.unsqueeze(1)).squeeze()
        
        # Target Q values
        with torch.no_grad():
            next_q = self.target_net(next_states).max(1)[0]
            target_q = rewards + (1 - dones) * self.gamma * next_q
        
        # Compute loss
        loss = self.loss_fn(current_q, target_q)
        
        # Optimize
        self.optimizer.zero_grad()
        loss.backward()
        # Gradient clipping
        torch.nn.utils.clip_grad_norm_(self.policy_net.parameters(), 1.0)
        self.optimizer.step()
        
        self.updates += 1
        
        return loss.item()
    
    def update_target_network(self):
        """Update target network with policy network weights"""
        self.target_net.load_state_dict(self.policy_net.state_dict())
    
    def decay_epsilon(self):
        """Decay exploration rate"""
        self.epsilon = max(self.epsilon_end, self.epsilon * self.epsilon_decay)
    
    def save(self, filepath: str):
        """Save agent"""
        torch.save({
            'policy_net': self.policy_net.state_dict(),
            'target_net': self.target_net.state_dict(),
            'optimizer': self.optimizer.state_dict(),
            'epsilon': self.epsilon,
            'steps': self.steps,
            'updates': self.updates
        }, filepath)
    
    def load(self, filepath: str):
        """Load agent"""
        checkpoint = torch.load(filepath)
        self.policy_net.load_state_dict(checkpoint['policy_net'])
        self.target_net.load_state_dict(checkpoint['target_net'])
        self.optimizer.load_state_dict(checkpoint['optimizer'])
        self.epsilon = checkpoint['epsilon']
        self.steps = checkpoint['steps']
        self.updates = checkpoint['updates']
