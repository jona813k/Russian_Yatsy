# Russian Yatzy AI Strategies

This project implements multiple AI strategies for playing Russian Yatzy, from hand-crafted mathematical approaches to deep reinforcement learning.

## Available Strategies

### 1. Probability Strategy (AI1 - Baseline) ⭐
**Location:** `src/game/ai_strategy.py`

**Performance:** 31.49 avg turns (current best)

**Approach:** 
- Uses inverse probability as value: `value = (1/probability) * count`
- Opportunistically takes rarest dice combinations
- No learning required - pure mathematics

**Pros:**
- Fast and consistent
- Mathematically optimal for myopic decisions
- No training needed

**Cons:**
- Doesn't consider long-term planning
- No awareness of completion progress
- Can't adapt to rule changes

### 2. Q-Learning Agent (Tabular)
**Location:** `src/game/ml_agent.py`, `train_ml.py`

**Performance:** 37-38 avg turns

**Approach:**
- Tabular Q-learning with epsilon-greedy exploration
- State space: (dice, progress, selected_number, num_dice)
- Learns through trial and error

**Training:**
```bash
python train_ml.py --mode quick    # 5K episodes
python train_ml.py --mode normal   # 10K episodes
python train_ml.py --mode extended # 100K episodes
```

**Pros:**
- Learns without domain knowledge
- 100% game completion rate
- Can discover long-term patterns

**Cons:**
- Slow convergence (millions of states)
- Requires extensive training
- Still slower than probability strategy

### 3. Rarity-Aware Q-Learning
**Location:** `src/game/ml_engine.py` (enhanced rewards)

**Performance:** ~37 avg turns

**Approach:**
- Combines Q-learning with probability-inspired rewards
- Rarity score: inverse probability bonus
- Completion urgency: prioritizes nearly-complete numbers
- Endgame multipliers: increases urgency near victory

**Training:** Same as Q-Learning (uses enhanced ml_engine)

**Pros:**
- Incorporates domain knowledge
- Slightly faster than basic Q-learning
- Learns both rarity and planning

**Cons:**
- Still requires extensive training
- Not yet beating probability strategy

### 4. Deep Q-Network (DQN) 🚀
**Location:** `src/game/dqn_agent.py`, `train_dqn.py`

**Performance:** Testing in progress

**Approach:**
- Neural network approximates Q-values
- Generalizes across similar states
- Experience replay for sample efficiency
- Target network for stability

**Requirements:**
```bash
pip install torch
```

**Training:**
```bash
python train_dqn.py --mode quick    # 5K episodes
python train_dqn.py --mode normal   # 10K episodes
python train_dqn.py --mode extended # 50K episodes
```

**Pros:**
- Better generalization than tabular Q-learning
- Handles large state spaces efficiently
- Faster convergence expected

**Cons:**
- Requires PyTorch
- More computationally intensive
- Still in testing phase

### 5. Hybrid Strategy
**Location:** `src/game/hybrid_strategy.py`

**Status:** Implementation ready, not yet trained

**Approach:**
- Starts with probability strategy as base
- Learns adjustments based on game state
- Combines mathematical certainty with ML refinement

**Potential:**
- Best of both worlds: math + learning
- Fast convergence (warm start)
- Could surpass pure probability strategy

## Benchmarking

Compare strategies head-to-head:

```bash
python benchmark_strategies.py --games 1000
```

This runs 1000 games for each strategy and generates detailed statistics.

## Current Leaderboard

| Rank | Strategy | Avg Turns | Median | Completion |
|------|----------|-----------|---------|------------|
| 🥇 | **Probability** | **31.49** | 30.00 | 100% |
| 🥈 | Rarity Q-Learning | 37.00 | 36.00 | 100% |
| 🥉 | Basic Q-Learning | 37.01 | 36.00 | 100% |
| 🔬 | DQN | Testing | Testing | Testing |

## Key Insights

**Why Probability Strategy Wins:**
- Mathematical certainty beats trial-and-error learning
- Domain knowledge encoded directly
- No exploration cost

**Why ML Struggles:**
- Massive state space (millions of unique states)
- Tabular Q-learning doesn't generalize well
- Must discover what math "knows" innately

**Where ML Could Win:**
- Long-term planning (probability is myopic)
- Completion awareness (prioritize nearly-done numbers)
- Endgame strategy (urgency near victory)
- DQN's generalization may unlock this potential

## Next Steps

1. **Complete DQN Training:** Neural network may match/beat probability
2. **Train Hybrid Strategy:** Combine math + learning for best results
3. **Imitation Learning:** Learn from probability strategy demonstrations
4. **Multi-Agent Competition:** Pit strategies against each other

## Documentation

- [AI Benchmark Summary](AI_BENCHMARK_SUMMARY.md) - Detailed performance analysis
- [ML README](ML_README.md) - ML system architecture
- [Architecture Diagrams](ARCHITECTURE_DIAGRAMS.md) - System design

## Quick Start

**Play against AI:**
```bash
python src/main.py
```

**Train new agent:**
```bash
python train_ml.py --mode quick
```

**Benchmark all strategies:**
```bash
python benchmark_strategies.py --games 1000
```

**Test DQN:**
```bash
pip install torch
python train_dqn.py --mode quick
```
