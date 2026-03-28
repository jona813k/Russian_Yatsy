# ML System Cheat Sheet

## Installation (One Time)
```powershell
pip install numpy scipy
python test_ml_system.py
```

## Training

### Quick Test (5 min)
```powershell
python train_ml.py --mode quick
```

### Full Training (30-60 min) - Recommended
```powershell
python train_ml.py --mode full
```

### Continue Training
```powershell
python train_ml.py --mode continue --episodes 10000
```

## Benchmarking

### Compare ML vs Probability (1000 games)
```powershell
python benchmark_strategies.py --games 1000
```

### Benchmark ML Only
```powershell
python benchmark_strategies.py --ml-only --games 100
```

## What to Look For in Results

### Good Signs:
- ✓ Lower median turns than Probability strategy
- ✓ Smaller range (more consistent)
- ✓ Lower CV% (more predictable)

### Example Success:
```
Probability:  Median = 55 turns, Range = 68
ML Strategy:  Median = 44 turns, Range = 42
→ ML is 20% faster and more consistent!
```

## Key Metrics Explained

| Metric | Meaning | Good Value |
|--------|---------|------------|
| **Median Turns** | Typical performance | Lower is better |
| **Range** | Best to worst spread | Smaller is better |
| **CV%** | Consistency | Lower is better |
| **Std Dev** | Variation | Lower is better |

## Files You Care About

- `models/ml_agent.pkl` - Your trained AI
- `benchmarks/*.json` - Saved results
- `QUICKSTART.md` - Full guide

## Troubleshooting

**"No trained model found"**
→ Run: `python train_ml.py --mode quick`

**"ModuleNotFoundError: numpy"**
→ Run: `pip install numpy scipy`

**Training too slow**
→ Use `--mode quick` first (5K episodes)

## Commands in Order

1. Install: `pip install numpy scipy`
2. Test: `python test_ml_system.py`
3. Train: `python train_ml.py --mode quick`
4. Benchmark: `python benchmark_strategies.py --games 100`
5. Analyze results!

## That's It!

Read QUICKSTART.md for details.
