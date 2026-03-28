"""
Simplified DQN Agent with minimal state representation
Features: 6 dice + 12 progress + 2 hard number flags = 20 total
Much simpler than the original 68-feature version
"""
import numpy as np
import torch
import torch.nn as nn
import torch.optim as optim
import random
from collections import deque
from pathlib import Path


class SimpleDQNNetwork(nn.Module):
    """Neural network for DQN (matches the 28.1 turn model)"""
    
    def __init__(self, input_size: int = 25, output_size: int = 13):
        super(SimpleDQNNetwork, self).__init__()
        
        # Architecture that achieved 28.1 turns
        self.network = nn.Sequential(
            nn.Linear(input_size, 128),      # 25 → 128
            nn.ReLU(),
            nn.Dropout(0.2),
            nn.Linear(128, 128),             # 128 → 128
            nn.ReLU(),
            nn.Dropout(0.2),
            nn.Linear(128, 64),              # 128 → 64
            nn.ReLU(),
            nn.Linear(64, output_size)       # 64 → 13
        )
    
    def forward(self, x):
        return self.network(x)


class SimpleDQNAgent:
    """
    DQN agent with 25 features (matches the 28.1 turn model)
    Features: 6 dice + 12 progress + 2 hard flags + 5 strategic = 25 total
    """
    
    def __init__(
        self,
        learning_rate: float = 0.0005,
        discount_factor: float = 0.95,
        epsilon: float = 1.0,
        epsilon_min: float = 0.05,
        epsilon_decay: float = 0.9995,
        memory_size: int = 20000,
        batch_size: int = 64
    ):
        self.lr = learning_rate
        self.gamma = discount_factor
        self.epsilon = epsilon
        self.epsilon_min = epsilon_min
        self.epsilon_decay = epsilon_decay
        self.batch_size = batch_size
        
        # Experience replay
        self.memory = deque(maxlen=memory_size)
        
        # Neural networks
        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        self.policy_net = SimpleDQNNetwork(input_size=25).to(self.device)
        self.target_net = SimpleDQNNetwork(input_size=25).to(self.device)
        self.target_net.load_state_dict(self.policy_net.state_dict())
        self.target_net.eval()
        
        self.optimizer = optim.Adam(self.policy_net.parameters(), lr=learning_rate)
        self.criterion = nn.MSELoss()
        
        self.training_steps = 0
    
    def encode_state(self, state: tuple) -> np.ndarray:
        """
        Convert game state to 25-feature vector (matches 28.1 model)
        
        Total: 25 features
        - 6 dice values
        - 12 progress values
        - 2 hard number flags
        - 5 strategic features
        """
        features = []
        
        # ===== DICE VALUES (6 features) =====
        dice_tuple = state[0]
        dice_features = [d / 6.0 for d in dice_tuple[:6]]
        while len(dice_features) < 6:
            dice_features.append(0.0)
        features.extend(dice_features)
        
        # ===== PROGRESS (12 features) =====
        progress_bins = state[1]
        progress_features = [p / 6.0 for p in progress_bins]
        features.extend(progress_features)
        
        # ===== HARD NUMBERS (2 features) =====
        hard_11_incomplete = 1.0 if progress_bins[10] < 6 else 0.0
        hard_12_incomplete = 1.0 if progress_bins[11] < 6 else 0.0
        features.extend([hard_11_incomplete, hard_12_incomplete])
        
        # ===== STRATEGIC FEATURES (5 features) =====
        total_collected = sum(progress_bins)
        completion_pct = total_collected / 72.0
        
        nearly_complete_count = sum(1 for p in progress_bins if p == 5)
        nearly_complete_norm = nearly_complete_count / 12.0
        
        good_progress_count = sum(1 for p in progress_bins if 3 <= p < 6)
        good_progress_norm = good_progress_count / 12.0
        
        completed_count = sum(1 for p in progress_bins if p >= 6)
        completed_norm = completed_count / 12.0
        
        hard_remaining = (1.0 if progress_bins[10] < 6 else 0.0) + (1.0 if progress_bins[11] < 6 else 0.0)
        hard_remaining_norm = hard_remaining / 2.0
        
        features.extend([
            completion_pct,
            nearly_complete_norm,
            good_progress_norm,
            completed_norm,
            hard_remaining_norm
        ])
        
        return np.array(features, dtype=np.float32)
        hard_11_incomplete = 1.0 if progress_bins[10] < 6 else 0.0  # Index 10 = number 11
        hard_12_incomplete = 1.0 if progress_bins[11] < 6 else 0.0  # Index 11 = number 12
        features.extend([hard_11_incomplete, hard_12_incomplete])
        
        return np.array(features, dtype=np.float32)
    
    def get_action(self, state: tuple, legal_actions: list, training: bool = True) -> dict:
        """Epsilon-greedy action selection"""
        
        if training and random.random() < self.epsilon:
            return random.choice(legal_actions)
        
        # Convert state to feature vector
        state_vector = self.encode_state(state)
        state_tensor = torch.FloatTensor(state_vector).unsqueeze(0).to(self.device)
        
        # Get Q-values
        with torch.no_grad():
            q_values = self.policy_net(state_tensor).cpu().numpy()[0]
        
        # Find best legal action
        best_action = None
        best_q = float('-inf')
        
        for action in legal_actions:
            if action['type'] == 'select':
                action_idx = action['number']
            elif action['type'] == 'skip_turn':
                action_idx = 0
            else:  # collect
                action_idx = action['number']
            
            if q_values[action_idx] > best_q:
                best_q = q_values[action_idx]
                best_action = action
        
        return best_action if best_action else legal_actions[0]
    
    def remember(self, state, action, reward, next_state, done):
        """Store experience"""
        self.memory.append((state, action, reward, next_state, done))
    
    def replay(self):
        """Train on batch of experiences"""
        if len(self.memory) < self.batch_size:
            return 0.0
        
        batch = random.sample(self.memory, self.batch_size)
        
        states = []
        targets = []
        
        for state, action, reward, next_state, done in batch:
            state_vector = self.encode_state(state)
            states.append(state_vector)
            
            state_tensor = torch.FloatTensor(state_vector).unsqueeze(0).to(self.device)
            current_q = self.policy_net(state_tensor).cpu().detach().numpy()[0]
            
            if done:
                target_q = reward
            else:
                next_vector = self.encode_state(next_state)
                next_tensor = torch.FloatTensor(next_vector).unsqueeze(0).to(self.device)
                next_q = self.target_net(next_tensor).cpu().detach().numpy()[0]
                target_q = reward + self.gamma * np.max(next_q)
            
            action_idx = action['number'] if action['type'] != 'skip_turn' else 0
            current_q[action_idx] = target_q
            targets.append(current_q)
        
        # Train
        states_tensor = torch.FloatTensor(np.array(states)).to(self.device)
        targets_tensor = torch.FloatTensor(np.array(targets)).to(self.device)
        
        self.optimizer.zero_grad()
        predictions = self.policy_net(states_tensor)
        loss = self.criterion(predictions, targets_tensor)
        loss.backward()
        self.optimizer.step()
        
        self.training_steps += 1
        
        # Decay epsilon
        if self.epsilon > self.epsilon_min:
            self.epsilon *= self.epsilon_decay
        
        # Update target network
        if self.training_steps % 100 == 0:
            self.target_net.load_state_dict(self.policy_net.state_dict())
        
        return loss.item()
    
    def save(self, filepath: str):
        """Save model"""
        Path(filepath).parent.mkdir(parents=True, exist_ok=True)
        torch.save({
            'policy_net': self.policy_net.state_dict(),
            'target_net': self.target_net.state_dict(),
            'optimizer': self.optimizer.state_dict(),
            'epsilon': self.epsilon,
            'training_steps': self.training_steps
        }, filepath)
    
    def load(self, filepath: str):
        """Load model"""
        checkpoint = torch.load(filepath, map_location=self.device)
        self.policy_net.load_state_dict(checkpoint['policy_net'])
        self.target_net.load_state_dict(checkpoint['target_net'])
        self.optimizer.load_state_dict(checkpoint['optimizer'])
        self.epsilon = checkpoint.get('epsilon', self.epsilon_min)
        self.training_steps = checkpoint.get('training_steps', 0)
