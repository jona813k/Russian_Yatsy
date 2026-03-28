"""
Training script for DQN Agent v2.

Usage:
    python train_v2.py                        # 50,000 episodes (default)
    python train_v2.py --episodes 200000      # long run
    python train_v2.py --resume               # continue from last checkpoint
    python train_v2.py --eval-only            # benchmark existing model

What changed vs the original training:
  - Uses DQNAgentV2 with rich state (collectibles per number, not raw dice)
  - Dueling DQN + Double DQN + Huber loss + gradient clipping
  - gamma = 0.99  (was 0.95 — old value nearly zeroed the win signal)
  - max_steps = 2000 per episode  (was 200 — games were being cut short)
  - Replay 3x per episode instead of 5x (less overfitting to early experiences)
  - Saves best model separately so a long run never loses the peak

Model saved to: models/dqn_v2.pth
Best model:     models/dqn_v2_best.pth
"""

import sys
sys.path.insert(0, 'src')

import argparse
import time
import numpy as np
from pathlib import Path

from src.game.dqn_agent_v2 import DQNAgentV2
from src.game.ml_engine import MLGameEngine


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def play_episode(agent: DQNAgentV2, engine: MLGameEngine, training: bool) -> dict:
    """
    Play one complete game.
    Returns {'turns': int, 'won': bool, 'reward': float}.
    """
    engine.reset()
    engine.start_new_turn()

    total_reward = 0.0
    steps = 0
    max_steps = 2000  # safety cap — Russian Yatzy rarely exceeds ~500 steps

    while not engine.is_game_over() and steps < max_steps:
        rich_state = engine.get_rich_state()
        legal_actions = engine.get_legal_actions()

        if not legal_actions:
            break

        action = agent.get_action(rich_state, legal_actions, training=training)
        result = engine.execute_action(action)

        reward = result['reward']
        total_reward += reward
        done = result['state'] == 'won'

        if training:
            next_rich = engine.get_rich_state()
            agent.remember(rich_state, action, reward, next_rich, done)

        if done:
            break

        steps += 1

    info = engine.get_game_info()
    return {
        'turns': info['turns'],
        'won': info['is_won'],
        'reward': total_reward,
    }


def evaluate(agent: DQNAgentV2, engine: MLGameEngine, n_games: int = 200) -> dict:
    """Run n_games without training and return statistics."""
    old_epsilon = agent.epsilon
    agent.epsilon = 0.0

    turns_list = []
    for _ in range(n_games):
        result = play_episode(agent, engine, training=False)
        turns_list.append(result['turns'])

    agent.epsilon = old_epsilon

    turns = np.array(turns_list)
    return {
        'mean':   float(np.mean(turns)),
        'median': float(np.median(turns)),
        'std':    float(np.std(turns)),
        'min':    int(np.min(turns)),
        'max':    int(np.max(turns)),
        'p10':    float(np.percentile(turns, 10)),
        'p90':    float(np.percentile(turns, 90)),
    }


def print_eval(stats: dict, label: str = ''):
    tag = f' ({label})' if label else ''
    print(f"\n{'─'*60}")
    print(f"  Evaluation{tag}")
    print(f"{'─'*60}")
    print(f"  Median turns : {stats['median']:.1f}")
    print(f"  Mean turns   : {stats['mean']:.1f}")
    print(f"  Std dev      : {stats['std']:.1f}")
    print(f"  Best / Worst : {stats['min']} / {stats['max']}")
    print(f"  P10 / P90    : {stats['p10']:.1f} / {stats['p90']:.1f}")
    print(f"{'─'*60}\n")


# ---------------------------------------------------------------------------
# Main training loop
# ---------------------------------------------------------------------------

def train(episodes: int, resume: bool, model_path: str, best_path: str):
    agent = DQNAgentV2(
        learning_rate=0.0005,
        discount_factor=0.99,
        epsilon=1.0,
        epsilon_min=0.02,
        epsilon_decay=0.99999,
        memory_size=50000,
        batch_size=128,
    )
    engine = MLGameEngine()

    if resume and Path(model_path).exists():
        agent.load(model_path)
        print(f"Resumed from {model_path}  (ε={agent.epsilon:.4f})")
    elif resume:
        print(f"No checkpoint found at {model_path}, starting fresh.")

    print(f"\n{'='*60}")
    print(f"  DQN v2 Training — {episodes:,} episodes")
    print(f"  Device : {agent.device}")
    print(f"  gamma  : {agent.gamma}   ε-decay: {agent.epsilon_decay}")
    print(f"{'='*60}\n")

    turns_window = []
    rewards_window = []
    best_median = float('inf')
    start_time = time.time()

    for ep in range(1, episodes + 1):
        result = play_episode(agent, engine, training=True)
        turns_window.append(result['turns'])
        rewards_window.append(result['reward'])

        # Train 3x per episode
        if len(agent.memory) >= agent.batch_size:
            for _ in range(3):
                agent.replay()

        # Progress log every 500 episodes
        if ep % 500 == 0:
            w = min(500, len(turns_window))
            avg_turns = np.mean(turns_window[-w:])
            avg_reward = np.mean(rewards_window[-w:])
            elapsed = time.time() - start_time
            rate = ep / elapsed
            print(
                f"Ep {ep:6d}/{episodes} | "
                f"Turns(avg500): {avg_turns:5.1f} | "
                f"Reward: {avg_reward:7.1f} | "
                f"ε: {agent.epsilon:.4f} | "
                f"{rate:.1f} games/s"
            )

        # Full evaluation every 5,000 episodes
        if ep % 5000 == 0:
            stats = evaluate(agent, engine, n_games=200)
            print_eval(stats, label=f'ep {ep:,}')

            if stats['median'] < best_median:
                best_median = stats['median']
                agent.save(best_path)
                print(f"  ★ New best: {best_median:.1f} turns  → saved to {best_path}")

            if stats['median'] < 20:
                print(f"  ★★★ SUB-20 ACHIEVED: {stats['median']:.1f} turns ★★★")

            # Always save checkpoint too
            agent.save(model_path)

    # Final checkpoint
    agent.save(model_path)

    # Final evaluation over 500 games
    print("\nRunning final evaluation (500 games)...")
    final = evaluate(agent, engine, n_games=500)
    print_eval(final, label='FINAL')
    print(f"Best median during training: {best_median:.1f} turns")
    elapsed = time.time() - start_time
    print(f"Training time: {elapsed/60:.1f} minutes")
    print(f"Checkpoint : {model_path}")
    print(f"Best model : {best_path}")


# ---------------------------------------------------------------------------
# Eval-only mode
# ---------------------------------------------------------------------------

def eval_only(model_path: str):
    agent = DQNAgentV2()
    engine = MLGameEngine()

    if not Path(model_path).exists():
        print(f"No model found at {model_path}")
        return

    agent.load(model_path)
    print(f"Loaded {model_path}")
    print("Running 1,000-game benchmark...\n")

    stats = evaluate(agent, engine, n_games=1000)
    print_eval(stats, label='1000-game benchmark')


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Train DQN v2 agent for Russian Yatzy')
    parser.add_argument('--episodes', type=int, default=50000,
                        help='Number of training episodes (default: 50,000)')
    parser.add_argument('--resume', action='store_true',
                        help='Continue from existing checkpoint')
    parser.add_argument('--eval-only', action='store_true',
                        help='Skip training, just benchmark the saved model')
    parser.add_argument('--model', type=str, default='models/dqn_v2.pth',
                        help='Path to save/load model checkpoint')
    parser.add_argument('--best', type=str, default='models/dqn_v2_best.pth',
                        help='Path to save best model found during training')
    args = parser.parse_args()

    if args.eval_only:
        eval_only(args.model)
    else:
        train(args.episodes, args.resume, args.model, args.best)
