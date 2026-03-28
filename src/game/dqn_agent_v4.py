"""
DQN Agent v4 — targeting ≤25 median turns.

Root cause of v3 collapse (diagnosed):
  tau=0.01 with 5 replays/episode = 5 target-net soft updates per episode.
  After 15k episodes × 5 = 75k updates at τ=0.01, the target net tracked
  the policy net almost perfectly → unstable bootstrapping → policy collapse.
  LR 0.0003 was also too high for stable fine-tuning.

Fixes applied:
  tau:        0.01  → 0.005    target net moves half as fast per step
  LR:         0.0003 → 0.0001  slower, more stable gradient updates
  grad clip:  1.0   → 0.5      tighter control
  Replays:    5/ep  → 3/ep     fewer target-net disturbances per episode
  Buffer:     uniform deque → Prioritized Experience Replay (PER)
                               high-TD-error transitions resampled more often
                               and survive buffer turnover longer
  N-step:     1-step TD → 3-step returns
                               better credit assignment across sequential turns;
                               win signal propagates faster through the buffer

Architecture: unchanged from v3 (28 features, 512/512 dueling network).

State encoding (28 features):
  [0..11]  collectibles[0..11] / 6   — dice collectable per number right now
  [12..23] progress[0..11] / 6       — collected so far per number
  [24]     selected / 12             — locked-in number (0 = free)
  [25]     num_dice / 6              — dice remaining in hand
  [26]     turn_number / 100         — urgency signal (capped at 2.0)
  [27]     num_completed / 12        — fraction of numbers fully done
"""

import numpy as np
import torch
import torch.nn as nn
import torch.nn.functional as F
import torch.optim as optim
import random
from collections import deque
from pathlib import Path


# ---------------------------------------------------------------------------
# Sum Tree
# ---------------------------------------------------------------------------

class SumTree:
    """
    Binary sum-tree for O(log N) priority-weighted sampling.

    Leaf i (0-indexed) lives at tree[capacity - 1 + i].
    Internal nodes hold the sum of their subtree.
    """

    def __init__(self, capacity: int):
        self.capacity = capacity
        self.tree = np.zeros(2 * capacity - 1, dtype=np.float64)
        self.data: list = [None] * capacity
        self._write = 0
        self.size = 0

    @property
    def total(self) -> float:
        return float(self.tree[0])

    def add(self, priority: float, data) -> int:
        """Store data with given priority. Returns tree index of the leaf."""
        tree_idx = self._write + self.capacity - 1
        self.data[self._write] = data
        self.update(tree_idx, priority)
        self._write = (self._write + 1) % self.capacity
        self.size = min(self.size + 1, self.capacity)
        return tree_idx

    def update(self, tree_idx: int, priority: float):
        """Set leaf priority and propagate the delta upward."""
        delta = priority - self.tree[tree_idx]
        self.tree[tree_idx] = priority
        idx = tree_idx
        while idx > 0:
            idx = (idx - 1) // 2
            self.tree[idx] += delta

    def get(self, s: float) -> tuple:
        """
        Walk the tree to find the leaf whose cumulative range contains s.
        Returns (tree_idx, priority, data).
        """
        idx = 0
        while True:
            left = 2 * idx + 1
            right = left + 1
            if left >= len(self.tree):
                break
            if s <= self.tree[left]:
                idx = left
            else:
                s -= self.tree[left]
                idx = right
        data_idx = idx - self.capacity + 1
        return idx, float(self.tree[idx]), self.data[data_idx]


# ---------------------------------------------------------------------------
# Prioritized Replay Buffer
# ---------------------------------------------------------------------------

class PrioritizedReplayBuffer:
    """
    Replay buffer with proportional prioritization (Schaul et al., 2015).

    Sampling probability: P(i) ∝ priority(i)^alpha
    Importance-sampling weights correct the non-uniform bias.
    beta anneals from beta_start → 1.0 over beta_steps gradient steps.
    """

    _EPS = 1e-6   # prevents zero priority

    def __init__(
        self,
        capacity: int,
        alpha: float = 0.6,
        beta_start: float = 0.4,
        beta_end: float = 1.0,
        beta_steps: int = 800_000,
    ):
        self.tree = SumTree(capacity)
        self.alpha = alpha
        self.beta = beta_start
        self._beta_increment = (beta_end - beta_start) / beta_steps
        self._max_priority = 1.0

    def __len__(self) -> int:
        return self.tree.size

    def add(self, transition) -> None:
        """Add with max seen priority so every new transition gets trained on."""
        self.tree.add(self._max_priority, transition)

    def sample(self, batch_size: int) -> tuple:
        """
        Stratified sampling over [0, total_priority].
        Returns (transitions, IS_weights, tree_indices).
        IS weights are normalized so max weight in the batch = 1.
        """
        transitions = []
        tree_indices = []
        priorities = []

        segment = self.tree.total / batch_size
        self.beta = min(1.0, self.beta + self._beta_increment)

        for i in range(batch_size):
            s = random.uniform(segment * i, segment * (i + 1))
            idx, priority, data = self.tree.get(s)
            tree_indices.append(idx)
            priorities.append(priority)
            transitions.append(data)

        probs = np.array(priorities, dtype=np.float64) / self.tree.total
        weights = (self.tree.size * probs) ** (-self.beta)
        weights = (weights / weights.max()).astype(np.float32)

        return transitions, weights, tree_indices

    def update_priorities(self, tree_indices: list, td_errors: np.ndarray) -> None:
        for idx, err in zip(tree_indices, td_errors):
            priority = (float(abs(err)) + self._EPS) ** self.alpha
            self.tree.update(idx, priority)
            self._max_priority = max(self._max_priority, priority)


# ---------------------------------------------------------------------------
# Network (unchanged from v3)
# ---------------------------------------------------------------------------

class DuelingDQNNetworkV4(nn.Module):
    """Dueling DQN: 28-feature input, 512/512 shared trunk, split value/advantage heads."""

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
        value     = self.value_stream(shared)
        advantage = self.advantage_stream(shared)
        return value + advantage - advantage.mean(dim=1, keepdim=True)


# ---------------------------------------------------------------------------
# Agent
# ---------------------------------------------------------------------------

class DQNAgentV4:
    """
    Dueling Double DQN with Prioritized Experience Replay and 3-step returns.

    Public API (drop-in replacement for v2/v3):
      encode_state(rich_state)               → np.ndarray (28,)
      get_action(rich_state, legal)          → action dict
      get_action_rankings(rich_state, legal) → ranked list
      remember(s, a, r, ns, done)            → buffer transition (n-step handled internally)
      flush_nstep()                          → flush n-step buffer at episode end
      replay()                               → one gradient step, returns loss
      save(filepath) / load(filepath)
    """

    def __init__(
        self,
        learning_rate: float = 0.0001,
        discount_factor: float = 0.99,
        epsilon: float = 1.0,
        epsilon_min: float = 0.05,
        epsilon_decay: float = 0.999995,
        memory_size: int = 200_000,
        batch_size: int = 256,
        tau: float = 0.005,
        n_step: int = 3,
        per_alpha: float = 0.6,
        per_beta_start: float = 0.4,
    ):
        self.lr = learning_rate
        self.gamma = discount_factor
        self.epsilon = epsilon
        self.epsilon_min = epsilon_min
        self.epsilon_decay = epsilon_decay
        self.batch_size = batch_size
        self.tau = tau
        self.n_step = n_step

        self.per_buffer = PrioritizedReplayBuffer(
            capacity=memory_size,
            alpha=per_alpha,
            beta_start=per_beta_start,
        )
        self._nstep_buf: deque = deque()

        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        self.policy_net = DuelingDQNNetworkV4(input_size=28, output_size=13).to(self.device)
        self.target_net = DuelingDQNNetworkV4(input_size=28, output_size=13).to(self.device)
        self.target_net.load_state_dict(self.policy_net.state_dict())
        self.target_net.eval()

        self.optimizer = optim.Adam(self.policy_net.parameters(), lr=learning_rate)
        self.training_steps = 0

    # ------------------------------------------------------------------
    # State encoding
    # ------------------------------------------------------------------

    def encode_state(self, rich_state: dict) -> np.ndarray:
        c = rich_state['collectibles']
        p = rich_state['progress']
        s = rich_state['selected']
        d = rich_state['num_dice']
        t = rich_state.get('turn_number', 0)
        num_completed = sum(1 for v in p if v >= 6)

        features = (
            [v / 6.0 for v in c]
            + [v / 6.0 for v in p]
            + [s / 12.0]
            + [d / 6.0]
            + [min(t, 200) / 100.0]
            + [num_completed / 12.0]
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
                'action':      action,
                'number':      action.get('number', 0),
                'q_value':     float(q[idx]),
                'collectible': action.get('collectible', 0),
            })
        ranked.sort(key=lambda x: x['q_value'], reverse=True)
        for i, item in enumerate(ranked):
            item['rank'] = i + 1
        return ranked

    # ------------------------------------------------------------------
    # N-step return buffering
    # ------------------------------------------------------------------

    def remember(self, rich_state, action, reward, next_rich_state, done):
        """
        Buffer a raw transition. Once n transitions are buffered the oldest
        is converted to an n-step return and stored in PER. When done=True
        all remaining partial returns are also flushed.
        """
        self._nstep_buf.append((rich_state, action, reward, next_rich_state, done))

        if len(self._nstep_buf) == self.n_step:
            self._flush_oldest()

        if done:
            while self._nstep_buf:
                self._flush_oldest()

    def flush_nstep(self):
        """
        Flush any buffered transitions at episode end.
        No-op if already flushed (e.g. when done=True was seen).
        Call this when an episode exits via max_steps rather than done=True.
        """
        while self._nstep_buf:
            self._flush_oldest()

    def _flush_oldest(self):
        """
        Compute the n-step return for the oldest buffered transition and
        push it into the PER buffer.

        G = r_0 + γ·r_1 + γ²·r_2 + ...  (stops at first done)
        done_n=True  → G is the full return; no bootstrap needed
        done_n=False → replay() will add γ^n · V(s_n)
        """
        if not self._nstep_buf:
            return
        s0, a0 = self._nstep_buf[0][0], self._nstep_buf[0][1]
        G = 0.0
        sn = self._nstep_buf[-1][3]
        done_n = False

        for k, (_, _, r_k, ns_k, d_k) in enumerate(self._nstep_buf):
            G += (self.gamma ** k) * r_k
            if d_k:
                done_n = True
                sn = ns_k
                break

        self.per_buffer.add((s0, a0, G, sn, done_n))
        self._nstep_buf.popleft()

    # ------------------------------------------------------------------
    # Training
    # ------------------------------------------------------------------

    def replay(self) -> float:
        """
        Sample a prioritized batch, compute n-step Double-DQN targets,
        apply IS-weighted Huber loss, update PER priorities, soft-update
        the target network.
        """
        if len(self.per_buffer) < self.batch_size:
            return 0.0

        batch, weights, tree_indices = self.per_buffer.sample(self.batch_size)

        states_np = np.array([self.encode_state(s) for s, *_ in batch])
        next_np   = np.array([self.encode_state(ns) for _, _, _, ns, _ in batch])

        states_t  = torch.FloatTensor(states_np).to(self.device)
        next_t    = torch.FloatTensor(next_np).to(self.device)
        weights_t = torch.FloatTensor(weights).to(self.device)

        current_q = self.policy_net(states_t)   # (B, 13)

        with torch.no_grad():
            next_q_target = self.target_net(next_t)   # (B, 13)
            next_q_policy = self.policy_net(next_t)   # (B, 13) — Double DQN

        action_indices = []
        target_vals = []
        td_errors = np.zeros(self.batch_size, dtype=np.float32)

        for i, (_, action, G, _, done_n) in enumerate(batch):
            idx = self._action_index(action)
            action_indices.append(idx)
            if done_n:
                target = G
            else:
                best_next = int(next_q_policy[i].argmax().item())
                target = G + (self.gamma ** self.n_step) * next_q_target[i, best_next].item()
            target_vals.append(target)
            td_errors[i] = abs(target - current_q[i, idx].item())

        action_idx_t = torch.tensor(action_indices, dtype=torch.long).to(self.device)
        target_t     = torch.tensor(target_vals, dtype=torch.float32).to(self.device)

        # Q-values for the actions that were actually taken — (B,)
        q_taken = current_q.gather(1, action_idx_t.unsqueeze(1)).squeeze(1)

        # IS-weighted Huber loss
        elementwise = F.smooth_l1_loss(q_taken, target_t, reduction='none')
        loss = (weights_t * elementwise).mean()

        self.optimizer.zero_grad()
        loss.backward()
        nn.utils.clip_grad_norm_(self.policy_net.parameters(), max_norm=0.5)
        self.optimizer.step()

        self.per_buffer.update_priorities(tree_indices, td_errors)

        self.training_steps += 1

        if self.epsilon > self.epsilon_min:
            self.epsilon *= self.epsilon_decay

        # Soft Polyak target update — τ=0.005 is 2× gentler than v3's 0.01
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
            'per_beta':       self.per_buffer.beta,
        }, filepath)

    def load(self, filepath: str):
        checkpoint = torch.load(filepath, map_location=self.device, weights_only=True)
        self.policy_net.load_state_dict(checkpoint['policy_net'])
        self.target_net.load_state_dict(checkpoint['target_net'])
        self.optimizer.load_state_dict(checkpoint['optimizer'])
        self.epsilon        = checkpoint.get('epsilon', self.epsilon_min)
        self.training_steps = checkpoint.get('training_steps', 0)
        if 'per_beta' in checkpoint:
            self.per_buffer.beta = checkpoint['per_beta']
