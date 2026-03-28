# Quick Start Guide - ML for Russian Yatzy

## What's Been Implemented:

### 1. **Machine Learning Agent** 🤖
- Q-Learning agent that learns optimal strategy through self-play
- Learns which numbers to prioritize based on dice and progress
- **Rule-safe**: Can only make legal moves (enforced by game engine)
- Saves/loads trained models for reuse

### 2. **Enhanced Benchmarking** 📊
As you requested:
- ✅ **Median rounds** - Shows typical performance
- ✅ **Average rounds** - Overall performance
- ✅ **Spread metrics** - Range from best to worst game
- ✅ **Consistency metrics** - How stable the strategy is
- Plus: Standard deviation, percentiles, IQR, coefficient of variation

### 3. **Comparison System** ⚖️
- Compare ML agent vs Probability strategy
- Side-by-side statistics
- Rankings by different metrics

## How to Use:

### Step 1: Train ML Agent

**Quick training (5K episodes, ~5 min):**
```powershell
python train_ml.py --mode quick
```

**Full training (50K episodes, ~30-60 min):**
```powershell
python train_ml.py --mode full
```

The agent will:
- Play 5,000 or 50,000 games against itself
- Learn from each decision (good or bad)
- Save the trained model to `models/ml_agent.pkl`

### Step 2: Benchmark & Compare

**Compare ML vs Probability over 1000 games:**
```powershell
python benchmark_strategies.py --games 1000
```

You'll get detailed reports showing:
```
--- TURN STATISTICS ---
Mean Turns:         45.23
Median Turns:       44.00
Range:              58 (best to worst)
Std Deviation:      8.12

--- CONSISTENCY METRICS ---
CV Turns:           17.95% (lower = more consistent)
Consistency Index:  0.876 (higher = more consistent)
```

### Step 3: Play with ML Agent

**Option A: Through main game:**
```powershell
python src/main.py
```
Then select option 5 (ML Training & Benchmarking) → option 5 (Test ML Agent)

**Option B: See it in action:**
```powershell
python benchmark_strategies.py --ml-only --games 100
```

## Architecture

### How ML Agent Learns Strategy (NOT Rules):

```
┌─────────────────────────────────────────┐
│  ML Agent                               │
│  "I want to select number 7"            │
└───────────────┬─────────────────────────┘
                │
                ↓
┌─────────────────────────────────────────┐
│  ML Game Engine (Rule Enforcer)         │
│  ✓ Can you make 7 from [2,3,4,5,6,6]?  │
│  ✓ Is 7 already completed?              │
│  → YES, legal action list: [5,7,8,10,11]│
└───────────────┬─────────────────────────┘
                │
                ↓
┌─────────────────────────────────────────┐
│  Action Executed                        │
│  → Collected 2 pairs for 7              │
│  → Reward: +20 points                   │
│  → Learn: "Selecting 7 here was good"   │
└─────────────────────────────────────────┘
```

**Agent learns:**
- Which numbers to prioritize when
- Risk vs reward tradeoffs
- Strategic completion order

**Agent CANNOT:**
- Select impossible numbers ❌
- Select completed numbers ❌
- Break any game rules ❌

## Files Created:

```
src/game/
├── ml_engine.py          - Rule-enforcing game engine for training
├── ml_agent.py           - Q-Learning implementation
├── ml_trainer.py         - Training loop & evaluation
├── ml_strategy.py        - ML agent as playable strategy
└── benchmark_metrics.py  - Enhanced benchmarking system

train_ml.py               - Training script
benchmark_strategies.py   - Comparison script
ML_README.md             - This file
```

## Expected Results:

### Probability Strategy (Baseline):
- Median Turns: ~50-60
- Consistent but not optimal
- No learning or adaptation

### ML Strategy (After Training):
- Median Turns: ~40-50 (should improve with more training)
- Learns optimal patterns
- Adapts strategy based on game state

### Improvement Areas:
- Early games: Agent explores randomly (~100+ turns)
- Mid training: Strategy emerges (~50-70 turns)
- Late training: Optimized play (~40-50 turns)
- Extended training (100K+ episodes): Further refinement

## Advanced Usage:

### Continue Training:
```powershell
python train_ml.py --mode continue --episodes 10000
```

### Custom Training:
```powershell
python train_ml.py --episodes 20000 --save models/my_agent.pkl
```

### Benchmark Custom Model:
```powershell
python benchmark_strategies.py --ml-model models/my_agent.pkl --games 1000
```

## Troubleshooting:

**"ModuleNotFoundError: No module named 'numpy'"**
```powershell
pip install numpy scipy
```

**"No trained model found"**
- Train a model first: `python train_ml.py --mode quick`

**"Training too slow"**
- Use --mode quick for faster results
- Training on 50K episodes takes time but learns better

## Next Steps:

1. **Train quick model** to see it working
2. **Benchmark** against probability strategy
3. **Analyze results** - which metrics improved?
4. **Train longer** if initial results are promising
5. **Experiment** with different training parameters in ml_agent.py

Have fun! 🎲🤖
