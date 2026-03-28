# Russian Yatzy - Dice Game with Machine Learning AI

A Python-based Russian Yatzy implementation featuring **Machine Learning AI** and advanced benchmarking.

## 🎯 NEW Features

### Machine Learning AI
- **Q-Learning agent** that learns optimal strategy through self-play
- Trains on 50,000+ games to discover winning patterns
- Considers all missing numbers for strategic decisions
- **Rule-safe**: Cannot break game rules (enforced by engine)

### Enhanced Benchmarking
✅ **Median rounds/turns** - Typical performance  
✅ **Average rounds/turns** - Overall average  
✅ **Spread metrics** - Range from best to worst game  
✅ **Consistency metrics** - How stable the strategy is

## 🚀 Quick Start

### 1. Install Dependencies
```powershell
pip install numpy scipy
```

### 2. Test Installation
```powershell
python test_ml_system.py
```

### 3. Train ML Agent
```powershell
# Quick training (5K episodes, ~5 min)
python train_ml.py --mode quick

# Full training (50K episodes, ~30-60 min)
python train_ml.py --mode full
```

### 4. Benchmark Performance
```powershell
python benchmark_strategies.py --games 1000
```

### 5. Play!
```powershell
python src/main.py
```

## 📊 Example Output

```
--- TURN STATISTICS ---
Mean Turns:         45.23
Median Turns:       44.00    ← Typical performance
Range:              58       ← Spread from best to worst
Std Deviation:      8.12

--- CONSISTENCY METRICS ---
CV Turns:           17.95%   ← Lower = more consistent
Consistency Index:  0.876    ← Higher = more reliable
```

## 📚 Documentation

- **[QUICKSTART.md](QUICKSTART.md)** - Complete getting started guide
- **[ML_IMPLEMENTATION_SUMMARY.md](ML_IMPLEMENTATION_SUMMARY.md)** - Technical details
- **[ARCHITECTURE_DIAGRAMS.md](ARCHITECTURE_DIAGRAMS.md)** - Visual explanations

## Project Structure

```
src/
  ├── main.py           # Entry point
  ├── game/             
  │   ├── ml_engine.py      # ML training engine
  │   ├── ml_agent.py       # Q-Learning agent
  │   ├── ml_trainer.py     # Training system
  │   ├── ml_strategy.py    # ML gameplay wrapper
  │   └── benchmark_metrics.py  # Statistics & comparison
  ├── models/           # Data models
  ├── ui/               # User interfaces
  └── utils/            # Utilities

train_ml.py              # Train ML agents
benchmark_strategies.py  # Compare strategies
test_ml_system.py       # Verify installation
```

## How to Run Tests

```bash
python -m unittest discover tests
```

## Requirements

- Python 3.8+
- numpy
- scipy
