"""
Quick Reference for ML System

## Files Created:
1. src/game/ml_engine.py - Game engine with rule enforcement for ML training
2. src/game/ml_agent.py - Q-Learning agent implementation
3. src/game/ml_trainer.py - Training system
4. src/game/ml_strategy.py - ML-based AI strategy for gameplay
5. src/game/benchmark_metrics.py - Enhanced benchmarking with all requested metrics
6. train_ml.py - Training script
7. benchmark_strategies.py - Comparison script

## Quick Start:

### 1. Train a new ML agent:
```bash
python train_ml.py --mode quick
```
or
```bash
python train_ml.py --mode full
```

### 2. Benchmark strategies:
```bash
python benchmark_strategies.py --games 1000
```

### 3. Use in game:
ML options added to main menu (option 5)

## Training Modes:
- quick: 5,000 episodes (~5 minutes)
- full: 50,000 episodes (~30-60 minutes)  
- extended: 100,000 episodes (~1-2 hours)
- continue: Continue training existing model

## Benchmark Metrics (as requested):
✓ Median rounds/turns
✓ Average rounds/turns  
✓ Spread metrics (range from best to worst)
✓ Standard deviation
✓ Consistency index
✓ Coefficient of variation
✓ Percentiles (Q1, Q3, P10, P90)

## How ML Agent Works:
- Uses Q-Learning to learn optimal strategy
- State: (dice, progress, selected_number, num_dice)
- Actions: Select which number to collect
- Reward: Points per die + bonuses for completing numbers
- Cannot break rules - only legal actions available

## Expected Performance:
Initial training may show ~60-80 turns average.
After full training, should improve to 40-50 turns.
Compare with Probability Strategy baseline.
