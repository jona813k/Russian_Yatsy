"""
DQN Agent v3 — targeting ~25 median turns.

What changed vs v2 (best: 31.0 turns, but regressed to 36 by ep 60k):

Problem diagnosed in v2:
  - 50k replay buffer turned over every ~3,500 episodes — good memories evicted fast
  - ε-decay 0.99999 hit 0.35 (optimal) at ep 35k then kept shrinking → locked into
    a suboptimal greedy policy, no recovery
  - Win efficiency signal was only (100 - turn)*5 → ~50pt gap between turn-25 and
    turn-35 wins out of ~3,200 total reward → agent barely cared about speed

Fixes:
  Buffer:     50k → 200k       — good experiences survive ~4x longer
  ε-decay:    0.99999 → 0.999995 — exploration stays meaningful 2x longer
  ε-min:      0.02 → 0.05      — never go fully greedy
  Network:    256/256 → 512/512 — more capacity for richer state
  State:      26 → 28 features  — add turns_taken/100 + num_completed/12
  Target net: hard update/1000 → soft Polyak τ=0.01 every step — more stable
  LR:         0.0005 → 0.0003   — lower LR for fine-grained learning
  Batch:      128 → 256         — more stable gradient estimates

State encoding (28 features):
  [0..11]  collectibles[0..11] / 6   — dice collectable per number right now
  [12..23] progress[0..11] / 6       — collected so far per number
  [24]     selected / 12             — locked-in number (0 = free)
  [25]     num_dice / 6              — dice remaining in hand
  [26]     turn_number / 100         — how far into the game we are (urgency)
  [27]     num_completed / 12        — fraction of numbers fully done

Network: 28 → [512 → 512] → value head (256→1) + advantage head (256→13)
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

class DuelingDQNNetworkV3(nn.Module):
    """Dueling DQN with wider trunk for richer 28-feature state."""

    def __init__(self, input_size: int = 28, output_size: int = 13):
        super().__init__()

        self.trunk = nn.Sequential(
            nn.Linear(input_size, 512),
            nn.LayerNorm(512),
            nn.ReLU(),
            nn.Linear(512, 512),
            nn.LayerNorm(512),
            nn.ReLU(),
        )

        self.value_stream = nn.Sequential(
            nn.Linear(512, 256),
            nn.ReLU(),
            nn.Linear(256, 1),
        )

        self.advantage_stream = nn.Sequential(
            nn.Linear(512, 256),
            nn.ReLU(),
            nn.Linear(256, output_size),
        )

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        shared = self.trunk(x)
        value = self.value_stream(shared)                      # (B, 1)
        advantage = self.advantage_stream(shared)              # (B, 13)
        q = value + advantage - advantage.mean(dim=1, keepdim=True)
        return q


# ---------------------------------------------------------------------------
# Agent
# ---------------------------------------------------------------------------

class DQNAgentV3:
    """
    Dueling DQN agent v3. Drop-in replacement for DQNAgentV2 with the same
    public API, but uses the richer 28-feature state from get_rich_state()
    (which now includes turn_number).

    Public API:
      encode_state(rich_state)               → np.ndarray (28,)
      get_action(rich_state, legal)          → action dict
      get_action_rankings(rich_state, legal) → ranked list
      remember(...)                          → store experience
      replay()                               → one training step, returns loss
      save(filepath) / load(filepath)
    """

    def __init__(
        self,
        learning_rate: float = 0.0003,
        discount_factor: float = 0.99,
        epsilon: float = 1.0,
        epsilon_min: float = 0.05,
        epsilon_decay: float = 0.999995,   # 2× slower than v2
        memory_size: int = 200_000,        # 4× larger than v2
        batch_size: int = 256,             # 2× larger than v2
        tau: float = 0.01,                 # soft target-net update factor
    ):
        self.lr = learning_rate
        self.gamma = discount_factor
        self.epsilon = epsilon
        self.epsilon_min = epsilon_min
        self.epsilon_decay = epsilon_decay
        self.batch_size = batch_size
        self.tau = tau

        self.memory = deque(maxlen=memory_size)

        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        self.policy_net = DuelingDQNNetworkV3(input_size=28, output_size=13).to(self.device)
        self.target_net = DuelingDQNNetworkV3(input_size=28, output_size=13).to(self.device)
        self.target_net.load_state_dict(self.policy_net.state_dict())
        self.target_net.eval()

        self.optimizer = optim.Adam(self.policy_net.parameters(), lr=learning_rate)
        self.criterion = nn.SmoothL1Loss()

        self.training_steps = 0

    # ------------------------------------------------------------------
    # State encoding
    # ------------------------------------------------------------------

    def encode_state(self, rich_state: dict) -> np.ndarray:
        """
        Convert rich_state dict to a 28-element float32 feature vector.

        Features:
          [0..11]  collectibles[0..11] / 6   — dice collectable right now
          [12..23] progress[0..11] / 6       — progress per number
          [24]     selected / 12             — locked-in number (0 = free)
          [25]     num_dice / 6              — dice remaining
          [26]     turn_number / 100         — urgency signal
          [27]     num_completed / 12        — fraction of numbers fully done
        """
        c = rich_state['collectibles']    # list of 12
        p = rich_state['progress']        # list of 12
        s = rich_state['selected']        # int 0-12
        d = rich_state['num_dice']        # int 0-6
        t = rich_state.get('turn_number', 0)  # int, 0 if old engine

        num_completed = sum(1 for v in p if v >= 6)

        features = (
            [v / 6.0 for v in c]          # 12 features
            + [v / 6.0 for v in p]        # 12 features
            + [s / 12.0]                  #  1 feature
            + [d / 6.0]                   #  1 feature
            + [min(t, 200) / 100.0]       #  1 feature (capped at 200 for outliers)
            + [num_completed / 12.0]      #  1 feature
        )
        return np.array(features, dtype=np.float32)

    # ------------------------------------------------------------------
    # Action selection
    # ------------------------------------------------------------------

    def _q_values(self, rich_state: dict) -> np.ndarray:
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
        return max(legal_actions, key=lambda a: q[self._action_index(a)])

    def get_action_rankings(self, rich_state: dict, legal_actions: list) -> list:
        """Return legal actions ranked best→worst by Q-value (coaching API)."""
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
        """Sample a batch, do one gradient step, soft-update target net."""
        if len(self.memory) < self.batch_size:
            return 0.0

        batch = random.sample(self.memory, self.batch_size)

        states_np = np.array([self.encode_state(s) for s, *_ in batch])
        next_np   = np.array([self.encode_state(ns) for _, _, _, ns, _ in batch])

        states_t = torch.FloatTensor(states_np).to(self.device)
        next_t   = torch.FloatTensor(next_np).to(self.device)

        current_q = self.policy_net(states_t)   # (B, 13)

        with torch.no_grad():
            next_q_target = self.target_net(next_t)   # (B, 13)
            next_q_policy = self.policy_net(next_t)   # (B, 13) — Double DQN

        targets = current_q.clone()
        for i, (_, action, reward, _, done) in enumerate(batch):
            idx = self._action_index(action)
            if done:
                targets[i, idx] = reward
            else:
                best_next = int(next_q_policy[i].argmax().item())
                targets[i, idx] = reward + self.gamma * next_q_target[i, best_next].item()

        self.optimizer.zero_grad()
        loss = self.criterion(current_q, targets)
        loss.backward()
        nn.utils.clip_grad_norm_(self.policy_net.parameters(), max_norm=1.0)
        self.optimizer.step()

        self.training_steps += 1

        if self.epsilon > self.epsilon_min:
            self.epsilon *= self.epsilon_decay

        # Soft Polyak update every step (τ=0.01 is gentle but continuous)
        with torch.no_grad():
            for tp, pp in zip(self.target_net.parameters(), self.policy_net.parameters()):
                tp.data.copy_(self.tau * pp.data + (1.0 - self.tau) * tp.data)

        return loss.item()

    # ------------------------------------------------------------------
    # Persistence
    # ------------------------------------------------------------------

    def save(self, filepath: str):
        Path(filepath).parent.mkdir(parents=True, exist_ok=True)
        torch.save({
            'policy_net':     self.policy_net.state_dict(),
            'target_net':     self.target_net.state_dict(),
            'optimizer':      self.optimizer.state_dict(),
            'epsilon':        self.epsilon,
            'training_steps': self.training_steps,
        }, filepath)

    def load(self, filepath: str):
        checkpoint = torch.load(filepath, map_location=self.device, weights_only=True)
        self.policy_net.load_state_dict(checkpoint['policy_net'])
        self.target_net.load_state_dict(checkpoint['target_net'])
        self.optimizer.load_state_dict(checkpoint['optimizer'])
        self.epsilon        = checkpoint.get('epsilon', self.epsilon_min)
        self.training_steps = checkpoint.get('training_steps', 0)
