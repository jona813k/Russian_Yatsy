"""
DQN Agent v2 — Dueling DQN with decision-ready state encoding.

Key improvements over v1 (28.1 turns):
  - State: collectibles-per-number instead of raw dice values.
    The network sees what a human expert sees: "I can collect 2 eights
    right now" rather than having to infer it from raw die faces.
  - Architecture: Dueling DQN separates V(s) from A(s,a), which is more
    stable when many actions have similar value (common in this game).
  - LayerNorm instead of Dropout: better gradient flow for RL.
  - gamma=0.99 (was 0.95). Over ~300 steps a game can take, 0.95^300
    almost zeroes the win signal. 0.99^300 ≈ 0.05 — still meaningful.
  - Gradient clipping for training stability.
  - get_action_rankings() method: exposes Q-values per legal action,
    which is the foundation of the coaching/feedback feature.

State encoding (26 features):
  - collectibles[0..11] / 6  — dice I'd collect per number right now
  - progress[0..11] / 6      — overall progress per number
  - selected / 12            — which number I'm locked into (0 = free)
  - num_dice / 6             — dice remaining in hand this turn

Network: 26 → [256 → 256] → value head (128→1) + advantage head (128→13)
Q(s,a) = V(s) + A(s,a) − mean(A(s,·))
"""

import numpy as np
import torch
import torch.nn as nn
import torch.optim as optim
import random
from collections import deque
from pathlib import Path


# ---------------------------------------------------------------------------
# Network
# ---------------------------------------------------------------------------

class DuelingDQNNetwork(nn.Module):
    """
    Dueling DQN architecture.

    Shared trunk encodes the state, then splits into:
      - value stream  : how good is this state regardless of action?
      - advantage stream : how much better is each action vs average?

    This separation is especially useful when the choice of action barely
    matters (e.g. only one legal move) — the value estimate stays stable
    while advantage handles the rare situations where the choice is critical.
    """

    def __init__(self, input_size: int = 26, output_size: int = 13):
        super().__init__()

        self.trunk = nn.Sequential(
            nn.Linear(input_size, 256),
            nn.LayerNorm(256),
            nn.ReLU(),
            nn.Linear(256, 256),
            nn.LayerNorm(256),
            nn.ReLU(),
        )

        # Value stream: how good is being in this state at all?
        self.value_stream = nn.Sequential(
            nn.Linear(256, 128),
            nn.ReLU(),
            nn.Linear(128, 1),
        )

        # Advantage stream: how much better is action a than average?
        self.advantage_stream = nn.Sequential(
            nn.Linear(256, 128),
            nn.ReLU(),
            nn.Linear(128, output_size),
        )

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        shared = self.trunk(x)
        value = self.value_stream(shared)                      # (B, 1)
        advantage = self.advantage_stream(shared)              # (B, 13)
        # Q(s,a) = V(s) + A(s,a) - mean(A(s,·))
        q = value + advantage - advantage.mean(dim=1, keepdim=True)
        return q


# ---------------------------------------------------------------------------
# Agent
# ---------------------------------------------------------------------------

class DQNAgentV2:
    """
    Dueling DQN agent using decision-ready state (rich state from ml_engine).

    Public API:
      encode_state(rich_state)         → np.ndarray (26,)
      get_action(rich_state, legal)    → action dict
      get_action_rankings(rich_state, legal) → list of ranked action dicts
      remember(...)                    → store experience
      replay()                         → one training step, returns loss
      save(filepath) / load(filepath)
    """

    def __init__(
        self,
        learning_rate: float = 0.0005,
        discount_factor: float = 0.99,   # high gamma: win signal survives long games
        epsilon: float = 1.0,
        epsilon_min: float = 0.02,
        epsilon_decay: float = 0.99999,
        memory_size: int = 50000,
        batch_size: int = 128,
    ):
        self.lr = learning_rate
        self.gamma = discount_factor
        self.epsilon = epsilon
        self.epsilon_min = epsilon_min
        self.epsilon_decay = epsilon_decay
        self.batch_size = batch_size

        self.memory = deque(maxlen=memory_size)

        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        self.policy_net = DuelingDQNNetwork(input_size=26, output_size=13).to(self.device)
        self.target_net = DuelingDQNNetwork(input_size=26, output_size=13).to(self.device)
        self.target_net.load_state_dict(self.policy_net.state_dict())
        self.target_net.eval()

        self.optimizer = optim.Adam(self.policy_net.parameters(), lr=learning_rate)
        self.criterion = nn.SmoothL1Loss()   # Huber loss — less sensitive to outlier rewards

        self.training_steps = 0

    # ------------------------------------------------------------------
    # State encoding
    # ------------------------------------------------------------------

    def encode_state(self, rich_state: dict) -> np.ndarray:
        """
        Convert rich_state dict (from ml_engine.get_rich_state()) to a
        26-element float32 feature vector.

        Features:
          [0..11]  collectibles[0..11] / 6   — what I can collect right now
          [12..23] progress[0..11] / 6       — how far along each number
          [24]     selected / 12             — locked-in number (0 = free)
          [25]     num_dice / 6             — dice remaining
        """
        c = rich_state['collectibles']   # list of 12
        p = rich_state['progress']       # list of 12
        s = rich_state['selected']       # int 0-12
        d = rich_state['num_dice']       # int 0-6

        features = (
            [v / 6.0 for v in c]         # 12 features
            + [v / 6.0 for v in p]       # 12 features
            + [s / 12.0]                 #  1 feature
            + [d / 6.0]                  #  1 feature
        )
        return np.array(features, dtype=np.float32)

    # ------------------------------------------------------------------
    # Action selection
    # ------------------------------------------------------------------

    def _q_values(self, rich_state: dict) -> np.ndarray:
        """Return raw Q-values for all 13 action slots."""
        vec = self.encode_state(rich_state)
        tensor = torch.FloatTensor(vec).unsqueeze(0).to(self.device)
        with torch.no_grad():
            return self.policy_net(tensor).cpu().numpy()[0]

    @staticmethod
    def _action_index(action: dict) -> int:
        return action['number'] if action['type'] != 'skip_turn' else 0

    def get_action(self, rich_state: dict, legal_actions: list, training: bool = True) -> dict:
        """Epsilon-greedy action selection."""
        if training and random.random() < self.epsilon:
            return random.choice(legal_actions)

        q = self._q_values(rich_state)
        best_action = max(legal_actions, key=lambda a: q[self._action_index(a)])
        return best_action

    def get_action_rankings(self, rich_state: dict, legal_actions: list) -> list:
        """
        Return all legal actions ranked from best to worst by Q-value.

        This is the coaching API: pass in the current game state and all
        legal moves, get back a ranked list so the UI can show the player
        whether their choice was optimal and by how much.

        Returns:
            list of dicts, each with:
              'action'     : the original action dict
              'number'     : target number (0 = skip)
              'q_value'    : raw Q-value (higher = better)
              'rank'       : 1 = best
              'collectible': how many dice this action would collect
        """
        q = self._q_values(rich_state)
        ranked = []
        for action in legal_actions:
            idx = self._action_index(action)
            ranked.append({
                'action': action,
                'number': action.get('number', 0),
                'q_value': float(q[idx]),
                'collectible': action.get('collectible', 0),
            })
        ranked.sort(key=lambda x: x['q_value'], reverse=True)
        for i, item in enumerate(ranked):
            item['rank'] = i + 1
        return ranked

    # ------------------------------------------------------------------
    # Training
    # ------------------------------------------------------------------

    def remember(self, rich_state, action, reward, next_rich_state, done):
        self.memory.append((rich_state, action, reward, next_rich_state, done))

    def replay(self) -> float:
        """Sample a batch from memory and do one gradient step. Returns loss."""
        if len(self.memory) < self.batch_size:
            return 0.0

        batch = random.sample(self.memory, self.batch_size)

        states_np = np.array([self.encode_state(s) for s, *_ in batch])
        next_np = np.array([self.encode_state(ns) for _, _, _, ns, _ in batch])

        states_t = torch.FloatTensor(states_np).to(self.device)
        next_t = torch.FloatTensor(next_np).to(self.device)

        current_q = self.policy_net(states_t)                 # (B, 13)

        with torch.no_grad():
            next_q_target = self.target_net(next_t)           # (B, 13)
            next_q_policy = self.policy_net(next_t)           # (B, 13) — Double DQN

        targets = current_q.clone()

        for i, (_, action, reward, _, done) in enumerate(batch):
            idx = self._action_index(action)
            if done:
                targets[i, idx] = reward
            else:
                # Double DQN: select action with policy net, evaluate with target net
                best_next_action = int(next_q_policy[i].argmax().item())
                targets[i, idx] = reward + self.gamma * next_q_target[i, best_next_action].item()

        self.optimizer.zero_grad()
        loss = self.criterion(current_q, targets)
        loss.backward()
        nn.utils.clip_grad_norm_(self.policy_net.parameters(), max_norm=1.0)
        self.optimizer.step()

        self.training_steps += 1

        if self.epsilon > self.epsilon_min:
            self.epsilon *= self.epsilon_decay

        # Hard target network update every 1000 steps
        if self.training_steps % 1000 == 0:
            self.target_net.load_state_dict(self.policy_net.state_dict())

        return loss.item()

    # ------------------------------------------------------------------
    # Persistence
    # ------------------------------------------------------------------

    def save(self, filepath: str):
        Path(filepath).parent.mkdir(parents=True, exist_ok=True)
        torch.save({
            'policy_net': self.policy_net.state_dict(),
            'target_net': self.target_net.state_dict(),
            'optimizer': self.optimizer.state_dict(),
            'epsilon': self.epsilon,
            'training_steps': self.training_steps,
        }, filepath)

    def load(self, filepath: str):
        checkpoint = torch.load(filepath, map_location=self.device, weights_only=True)
        self.policy_net.load_state_dict(checkpoint['policy_net'])
        self.target_net.load_state_dict(checkpoint['target_net'])
        self.optimizer.load_state_dict(checkpoint['optimizer'])
        self.epsilon = checkpoint.get('epsilon', self.epsilon_min)
        self.training_steps = checkpoint.get('training_steps', 0)
