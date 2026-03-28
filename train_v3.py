"""
Training script for DQN Agent v3 — targeting ~25 median turns.

Usage:
    python train_v3.py                        # 300,000 episodes (default)
    python train_v3.py --episodes 500000      # longer run
    python train_v3.py --resume               # continue from last checkpoint
    python train_v3.py --eval-only            # benchmark existing model

Key changes vs train_v2.py:
  - Uses DQNAgentV3 (28-feature state, 512/512 network, 200k buffer)
  - Reward shaping: quadratic win-efficiency bonus instead of linear
      v2: 1000 + max(0, (100-turn)*5)          → 50pt gap turn-25 vs turn-35
      v3: 1000 + max(0, (100-turn)^2 * 2)      → 2,800pt gap turn-25 vs turn-35
  - Stronger turn-end penalty: reward−2 → reward−30
      Failed turns now hurt proportionally to how deep into the game we are
  - 5 replays/episode (was 3) — more learning per game
  - Eval every 5k episodes, final eval over 500 games

Models saved to: models/dqn_v3.pth
Best model:      models/dqn_v3_best.pth
"""

import sys
sys.path.insert(0, 'src')

import argparse
import time
import numpy as np
from pathlib import Path

from src.game.dqn_agent_v3 import DQNAgentV3
from src.game.ml_engine import MLGameEngine


# ---------------------------------------------------------------------------
# Reward shaping
# ---------------------------------------------------------------------------

def shape_reward(result: dict, turn_number: int) -> float:
    """
    Augment engine rewards to give much stronger speed signal.

    Why:
      In v2 the efficiency bonus at win was (100-turn)*5 — only a 50-point gap
      between winning in 25 vs 35 turns, out of ~3,200 total reward (~1.5%).
      The agent had almost no incentive to be faster.

      Here we use (100-turn)^2 * 2 for the bonus, giving a 2,800-point gap.
      The turn-end penalty goes from -2 to -30 — failed turns hurt meaningfully.
    """
    reward = result['reward']
    state  = result['state']

    if state == 'won':
        # Replace v2 linear efficiency bonus with quadratic one.
        # Engine already added: max(0, (100 - turn_number) * 5)
        # We subtract that and substitute our quadratic version.
        old_bonus = max(0, (100 - turn_number) * 5)
        new_bonus = max(0, (100 - turn_number) ** 2 * 2)
        reward = reward - old_bonus + new_bonus

    elif state == 'turn_end':
        # Engine already subtracted 2; add another -28 so total is -30.
        # A failed turn deep into the game is a bigger setback than early on.
        reward -= 28

    return reward


# ---------------------------------------------------------------------------
# Episode runner
# ---------------------------------------------------------------------------

def play_episode(agent: DQNAgentV3, engine: MLGameEngine, training: bool) -> dict:
    """Play one complete game. Returns {'turns', 'won', 'reward'}."""
    engine.reset()

    total_reward = 0.0
    steps = 0
    max_steps = 2000

    while not engine.is_game_over() and steps < max_steps:
        rich_state   = engine.get_rich_state()
        legal_actions = engine.get_legal_actions()

        if not legal_actions:
            break

        action = agent.get_action(rich_state, legal_actions, training=training)
        result = engine.execute_action(action)

        reward = shape_reward(result, engine.turn_number)
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
        'turns':  info['turns'],
        'won':    info['is_won'],
        'reward': total_reward,
    }


# ---------------------------------------------------------------------------
# Evaluation
# ---------------------------------------------------------------------------

def evaluate(agent: DQNAgentV3, engine: MLGameEngine, n_games: int = 200) -> dict:
    """Run n_games greedy (ε=0) and return statistics."""
    saved_epsilon = agent.epsilon
    agent.epsilon = 0.0

    turns_list = []
    for _ in range(n_games):
        result = play_episode(agent, engine, training=False)
        turns_list.append(result['turns'])

    agent.epsilon = saved_epsilon

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
    agent  = DQNAgentV3(
        learning_rate  = 0.0003,
        discount_factor= 0.99,
        epsilon        = 1.0,
        epsilon_min    = 0.05,
        epsilon_decay  = 0.999995,
        memory_size    = 200_000,
        batch_size     = 256,
        tau            = 0.01,
    )
    engine = MLGameEngine()

    if resume and Path(model_path).exists():
        agent.load(model_path)
        print(f"Resumed from {model_path}  (ε={agent.epsilon:.4f})")
    elif resume:
        print(f"No checkpoint found at {model_path}, starting fresh.")

    print(f"\n{'='*60}")
    print(f"  DQN v3 Training — {episodes:,} episodes")
    print(f"  Device : {agent.device}")
    print(f"  gamma  : {agent.gamma}   ε-decay: {agent.epsilon_decay}")
    print(f"  buffer : {200_000:,}   batch: {256}")
    print(f"{'='*60}\n")

    turns_window   = []
    rewards_window = []
    best_median    = float('inf')
    start_time     = time.time()

    for ep in range(1, episodes + 1):
        result = play_episode(agent, engine, training=True)
        turns_window.append(result['turns'])
        rewards_window.append(result['reward'])

        # 5 gradient steps per episode (was 3 in v2)
        if len(agent.memory) >= agent.batch_size:
            for _ in range(5):
                agent.replay()

        # Progress log every 500 episodes
        if ep % 500 == 0:
            w          = min(500, len(turns_window))
            avg_turns  = np.mean(turns_window[-w:])
            avg_reward = np.mean(rewards_window[-w:])
            elapsed    = time.time() - start_time
            rate       = ep / elapsed
            print(
                f"Ep {ep:6d}/{episodes} | "
                f"Turns(avg500): {avg_turns:5.1f} | "
                f"Reward: {avg_reward:8.1f} | "
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

            if stats['median'] <= 25:
                print(f"  ★★★ SUB-26 ACHIEVED: {stats['median']:.1f} turns ★★★")
            if stats['median'] <= 20:
                print(f"  ★★★ SUB-21 ACHIEVED: {stats['median']:.1f} turns ★★★")

            agent.save(model_path)

    agent.save(model_path)

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
    agent  = DQNAgentV3()
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
    parser = argparse.ArgumentParser(description='Train DQN v3 agent for Russian Yatzy')
    parser.add_argument('--episodes', type=int, default=300_000,
                        help='Number of training episodes (default: 300,000)')
    parser.add_argument('--resume', action='store_true',
                        help='Continue from existing checkpoint')
    parser.add_argument('--eval-only', action='store_true',
                        help='Skip training, just benchmark the saved model')
    parser.add_argument('--model', type=str, default='models/dqn_v3.pth',
                        help='Path to save/load model checkpoint')
    parser.add_argument('--best', type=str, default='models/dqn_v3_best.pth',
                        help='Path to save best model found during training')
    args = parser.parse_args()

    if args.eval_only:
        eval_only(args.model)
    else:
        train(args.episodes, args.resume, args.model, args.best)
