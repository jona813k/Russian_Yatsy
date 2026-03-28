# System Architecture Visualization

## Overview: How ML Learns to Play Russian Yatzy

```
┌──────────────────────────────────────────────────────────────────┐
│                      TRAINING PHASE                              │
│                  (50,000 self-play games)                        │
└──────────────────────────────────────────────────────────────────┘

Game 1:
  State: Dice=[1,2,3,4,5,6], Progress=[0,0,0,0,0,0,0,0,0,0,0,0]
    ↓
  Agent: "I'll try selecting 5" (random exploration)
    ↓
  Result: Collected 1 die, reward=+10
    ↓
  Learning: Q(state, action_5) += 0.1 × 10 = 1.0
           (This action has some value)

Game 100:
  Similar State: Dice=[1,2,3,4,5,6], Progress=[0,0,0,0,0,0,0,0,0,0,0,0]
    ↓
  Agent: "I remember action_5=1.0, action_7=3.5, I'll select 7!"
    ↓
  Result: Collected 2 dice (pair), reward=+20
    ↓
  Learning: Q(state, action_7) += 0.1 × 20 = 5.5
           (This action is even better!)

Game 50,000:
  State: Dice=[1,2,3,4,5,6], Progress=[0,0,0,5,6,6,4,3,0,0,0,0]
    ↓
  Agent: "I've seen this 1000 times, optimal action is 10"
    ↓
  Result: Collected 1 die, completed number 10, reward=+110
    ↓
  Learning: Q(state, action_10) = 52.3 (highly optimized)

┌──────────────────────────────────────────────────────────────────┐
│                      GAMEPLAY PHASE                              │
│                  (Using trained agent)                           │
└──────────────────────────────────────────────────────────────────┘

Turn 1:
  Dice: [1, 2, 4, 5, 6, 6]
  Progress: All zeros
    ↓
  ┌─────────────────────────────────────────┐
  │ ML Agent (Brain)                        │
  │ State: (1,2,4,5,6,6), (0,0,0,0,0,...)  │
  │ Q-values:                               │
  │   Select 1: Q = 8.2                     │
  │   Select 2: Q = 7.5                     │
  │   Select 4: Q = 6.8                     │
  │   Select 5: Q = 9.1                     │
  │   Select 6: Q = 12.3  ← BEST!           │
  │   Select 7: Q = 5.2                     │
  │   Select 10: Q = 11.4                   │
  │   Select 11: Q = 15.7                   │
  │                                         │
  │ Decision: Select 11 (highest Q-value)  │
  └────────────┬────────────────────────────┘
               │
               ↓
  ┌─────────────────────────────────────────┐
  │ ML Engine (Rule Enforcer)               │
  │ Checking: Can make 11 from dice?        │
  │   Singles: None                         │
  │   Pairs: (5,6) → 11 ✓                   │
  │ Legal Actions:                          │
  │   [1, 2, 4, 5, 6, 10, 11] ✓             │
  │                                         │
  │ Execute: Collect pair (5,6) for 11     │
  └────────────┬────────────────────────────┘
               │
               ↓
  Result: Collected 1 unit of 11
  Remaining dice: [1, 2, 4, 6]
  Roll again...
```

## State Space Visualization

```
┌────────────────────────────────────────────────────────────┐
│                  GAME STATE                                │
└────────────────────────────────────────────────────────────┘
                         │
         ┌───────────────┼───────────────┐
         ↓               ↓               ↓
    ┌────────┐     ┌──────────┐    ┌──────────┐
    │ Dice   │     │ Progress │    │ Context  │
    │        │     │          │    │          │
    │ [1,2,  │     │ 1: ████  │    │ Selected:│
    │  3,4,  │     │ 2: ██    │    │   7      │
    │  5,6]  │     │ 3: ██████│    │ Dice:    │
    │        │     │ 4: ██    │    │   4      │
    └────────┘     │ 5: ████  │    └──────────┘
                   │ 6: ██████│
                   │ 7: ██    │
                   │ 8:       │
                   │ 9: ████  │
                   │10: ██████│
                   │11:       │
                   │12:       │
                   └──────────┘
```

## Decision Flow

```
                    START TURN
                         │
                         ↓
              ┌──────────────────────┐
              │   Roll All Dice      │
              │   Result: [2,3,5,6,  │
              │            6,6]      │
              └──────────┬───────────┘
                         │
                         ↓
              ┌──────────────────────┐
              │ Generate Legal       │
              │ Actions:             │
              │  - Select 2 (1 die)  │
              │  - Select 3 (1 die)  │
              │  - Select 5 (1 die)  │
              │  - Select 6 (3 dice) │
              │  - Select 8 (1 pair) │
              │  - Select 9 (1 pair) │
              │  - Select 11 (2 pair)│
              │  - Select 12 (2 pair)│
              └──────────┬───────────┘
                         │
                         ↓
              ┌──────────────────────┐
              │ ML Agent Evaluates:  │
              │                      │
              │ Q(state, select_2)   │
              │ Q(state, select_3)   │
              │ Q(state, select_5)   │
              │ Q(state, select_6)   │
              │ Q(state, select_8)   │
              │ Q(state, select_9)   │
              │ Q(state, select_11)  │
              │ Q(state, select_12)  │
              │                      │
              │ Best: select_11      │
              │ (Q-value = 47.3)     │
              └──────────┬───────────┘
                         │
                         ↓
              ┌──────────────────────┐
              │ Execute Action:      │
              │ Collect 2 pairs      │
              │ (5+6=11, 6+6=12)     │
              │ Wait... can only do  │
              │ 11 (selected number) │
              │ → Collect 2 dice     │
              └──────────┬───────────┘
                         │
                         ↓
              ┌──────────────────────┐
              │ Remaining: [2,3]     │
              │ Roll again...        │
              └──────────────────────┘
```

## Learning Process

```
Before Training (Episode 1):
┌──────────────────────────────────────┐
│ Q-Table (empty)                      │
│                                      │
│ state_1 -> action_5 : 0.0            │
│ state_1 -> action_7 : 0.0            │
│ state_1 -> action_11: 0.0            │
│ ...                                  │
└──────────────────────────────────────┘

After 1,000 Episodes:
┌──────────────────────────────────────┐
│ Q-Table (learning patterns)          │
│                                      │
│ state_1 -> action_5 : 3.2            │
│ state_1 -> action_7 : 5.8            │
│ state_1 -> action_11: 8.1 ← Best!    │
│ ...                                  │
│ 1,423 states explored                │
└──────────────────────────────────────┘

After 50,000 Episodes:
┌──────────────────────────────────────┐
│ Q-Table (optimized)                  │
│                                      │
│ state_1 -> action_5 : 12.4           │
│ state_1 -> action_7 : 18.2           │
│ state_1 -> action_11: 34.7 ← Optimal!│
│ ...                                  │
│ 28,432 states explored               │
│ Convergence achieved                 │
└──────────────────────────────────────┘
```

## Benchmarking Process

```
┌────────────────────────────────────────────────────────────┐
│              RUN 1000 SIMULATIONS                          │
└────────────────────────────────────────────────────────────┘

Game 1:   42 turns, 156 rolls  ←─┐
Game 2:   55 turns, 198 rolls    │
Game 3:   38 turns, 142 rolls    │
Game 4:   61 turns, 221 rolls    │
...                               ├── Collect Data
Game 998: 44 turns, 167 rolls    │
Game 999: 50 turns, 185 rolls    │
Game 1000:39 turns, 148 rolls  ←─┘

                 ↓

┌────────────────────────────────────────────────────────────┐
│              STATISTICAL ANALYSIS                          │
└────────────────────────────────────────────────────────────┘

Sort all turns: [38, 39, 42, 44, ..., 55, 61]
                      ↑              ↑      ↑
                     Min          Median   Max

Calculate:
├─ Mean:    45.23 turns
├─ Median:  44.00 turns  ← YOU ASKED FOR THIS!
├─ Min:     38 turns
├─ Max:     61 turns
├─ Range:   23 (best to worst)  ← SPREAD METRIC!
├─ Std Dev: 6.12 turns
├─ CV:      13.5% (consistency)
└─ IQR:     39-50 (middle 50%)

                 ↓

┌────────────────────────────────────────────────────────────┐
│              VISUAL DISTRIBUTION                           │
└────────────────────────────────────────────────────────────┘

Turns Distribution:
30   │
     │
25   │     ██
     │    ████
20   │   ██████
     │  ████████
15   │ ██████████
     │████████████
10   │████████████
     │████████████
 5   │████████████
     │████████████
     └────────────────────────
      38 40 42 44 46 48 50 52 54 56 58 60
         ↑        ↑           ↑
        Min    Median       Max

Most games cluster around median (44 turns)
Small spread = consistent strategy
```

## Comparison Example

```
┌─────────────────────────────────────────────────────────┐
│        PROBABILITY vs ML STRATEGY                       │
└─────────────────────────────────────────────────────────┘

Metric              Probability    ML Strategy    Winner
─────────────────────────────────────────────────────────
Median Turns             55.0          44.0      ML! ✓
Mean Turns               56.3          45.2      ML! ✓
Range (Spread)           42            23        ML! ✓
Std Deviation            8.5           6.1       ML! ✓
CV% (Consistency)        15.1%         13.5%     ML! ✓
Min Turns                38            38        Tie
Max Turns                80            61        ML! ✓

Conclusion: ML Strategy is 20% faster and more consistent!
```

## File Structure

```
Russian_Yatsy/
│
├── src/
│   └── game/
│       ├── ml_engine.py       ←─── Rule Enforcer
│       ├── ml_agent.py        ←─── Q-Learning Brain
│       ├── ml_trainer.py      ←─── Training Loop
│       ├── ml_strategy.py     ←─── Gameplay Wrapper
│       └── benchmark_metrics.py ←─ Statistics
│
├── train_ml.py                ←─── Train models
├── benchmark_strategies.py    ←─── Compare AIs
├── test_ml_system.py         ←─── Verify installation
│
├── models/                    ←─── Trained agents saved here
│   ├── ml_agent_quick.pkl
│   ├── ml_agent.pkl
│   └── ml_agent_extended.pkl
│
├── benchmarks/                ←─── Results saved here
│   ├── probability_strategy.json
│   └── ml_strategy.json
│
└── Documentation:
    ├── QUICKSTART.md
    ├── ML_README.md
    └── ML_IMPLEMENTATION_SUMMARY.md
```

## Usage Flow

```
┌──────────────┐
│ 1. INSTALL   │
│ pip install  │
│ numpy scipy  │
└──────┬───────┘
       │
       ↓
┌──────────────┐
│ 2. TEST      │
│ python       │
│ test_ml_     │
│ system.py    │
└──────┬───────┘
       │
       ↓
┌──────────────┐
│ 3. TRAIN     │
│ python       │
│ train_ml.py  │
│ --mode quick │
└──────┬───────┘
       │
       ↓
┌──────────────┐
│ 4. BENCHMARK │
│ python       │
│ benchmark_   │
│ strategies.py│
└──────┬───────┘
       │
       ↓
┌──────────────┐
│ 5. ANALYZE   │
│ Compare:     │
│ - Median ✓   │
│ - Spread ✓   │
│ - Consistency│
└──────┬───────┘
       │
       ↓
┌──────────────┐
│ 6. IMPROVE   │
│ Train longer │
│ or adjust    │
│ parameters   │
└──────────────┘
```

All diagrams are conceptual representations of the ML system!
