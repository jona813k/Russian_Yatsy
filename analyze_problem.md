# Deep Dive: Why DQN Training is Failing

## The Problem

**Starting point:** 28.1 turns (good performance)  
**After continued training:** 44.13 turns (57% worse!)  
**Expected:** Should improve toward <25 turns

## Root Cause Analysis

### Issue #1: **Catastrophic Forgetting**

When we continue training an already-trained model with the SAME reward structure, it's experiencing **catastrophic forgetting** - the neural network is overwriting what it learned.

**Why this happens:**
- The model was trained to convergence (28.1 turns)
- Continuing training with low exploration (ε=0.05→0.01) causes it to:
  - Exploit only what it currently knows
  - Get stuck in local optima
  - Overfit to recent bad experiences
  - Forget the good strategies it learned

**Evidence:**
- Performance degraded consistently (28.1 → 44.13)
- No improvement at any checkpoint
- Model is "unlearning" its good behavior

### Issue #2: **Reward Structure Mismatch**

The 28.1 model was trained with THESE massive bonuses:
```python
# Hard number bonus: +400 early game
# Nearly-complete bonus: +500 for 5/6 numbers
# Strategic order bonus: +100
# Rarity bonus: +200 (scaled)
# Total possible: ~1200 per action

# Victory bonuses:
# 20 turns: +3000
# 25 turns: +2000
# 30 turns: +1000
```

**Problem:** These rewards are **too large and conflicting**:

1. **Hard number bonus (+400)** says "always prioritize 11, 12"
2. **Nearly-complete bonus (+500)** says "always finish 5/6 numbers"  
3. **Strategic order bonus (+100)** says "follow this specific sequence"
4. **Rarity bonus (+200)** says "take rare combinations"

**When these conflict, the agent gets confused:**
- Has 5/6 of number 3 (easy number, +500 bonus)
- Rolls show number 11 available (hard number, +400 bonus)
- Also has rare combination (+200 rarity)
- **Which should it choose?**

The agent learns to **game the rewards** rather than win efficiently:
- Chases bonuses instead of winning
- Gets stuck collecting dice for bonuses
- Takes 44+ turns because it's optimizing for reward, not victory

### Issue #3: **Scaled Penalties Creating Perverse Incentives**

```python
# Turn-end penalties:
numbers_completed >= 10: -40  # Late game
numbers_completed >= 8: -30
numbers_completed >= 6: -20
numbers_completed < 6: -10    # Early game
```

**Problem:** Agent learns to **avoid progressing** to avoid higher penalties:
- Stays in early game (lower penalties)
- Doesn't complete numbers (to keep penalty low)
- Takes forever to finish (44 turns!)

### Issue #4: **Massive Victory Bonuses Unreachable**

```python
if turns <= 20: +3000
elif turns <= 25: +2000
```

**Problem:** Model averaging 44 turns gets **zero** of these bonuses:
- Never experiences the +3000 reward (too far away)
- Can't learn that 20-turn games are good
- Only learns from the small per-action rewards
- Victory at 44 turns gives same reward as 50 turns!

## What Actually Works (The Original 28.1 Model)

Looking at the older documentation, the ORIGINAL reward structure was **simpler**:

```python
# Basic rewards:
- Base: collected_dice * 10
- Completion bonus: +100
- Victory bonus: +1000 + (100 - turns) * 5
- Turn penalty: -1.0 (small, constant)
- Failed turn: -2.0 (also small)
```

**Why this worked:**
- Simple, consistent signals
- No conflicting bonuses
- Victory bonus scales linearly (not stepped)
- Penalties don't escalate dramatically
- Agent learns: "collect dice → complete numbers → win fast"

## The Fix

### Option 1: Revert to Original Simple Rewards ✅

**Restore this structure:**
```python
# Per action:
reward = collected * 10
if completed_number:
    reward += 100
if won:
    reward += 1000 + max(0, (100 - turns) * 5)

# Penalties:
turn_continues: -1.0
turn_ends: -2.0
skip_turn: -10.0
```

**Why this works:**
- Clear signal: more dice = good
- Complete numbers = bonus
- Win fast = bigger bonus
- Simple, no conflicts

### Option 2: Start Fresh with Better Rewards 🔄

Train a **NEW** model from scratch with:
```python
# Simplified strategic rewards:
reward = collected * 10

# SINGLE priority system (not multiple):
if current_progress[target] == 5:
    reward += 200  # Almost done - finish it!
elif target in [11, 12] and numbers_completed < 3:
    reward += 100  # Hard numbers early
    
# Victory - linear scaling:
if won:
    efficiency_reward = max(0, (40 - turns) * 100)
    reward += 1000 + efficiency_reward
    
# Penalties - constant, not scaled:
if turn_ends_without_completion:
    reward -= 5.0
if skip_turn:
    reward -= 15.0
```

### Option 3: Fine-tune the 28.1 Model (Advanced) 🎯

**Don't continue training** - instead:
1. Load the 28.1 model (frozen)
2. Analyze its Q-values on 1000 games
3. Find where it makes suboptimal choices
4. Create targeted training data for those scenarios
5. Fine-tune with very small learning rate (0.0001)

## Recommendation

**Immediate action:** Revert to simple rewards (Option 1)
- Restores the 28.1 baseline
- Proven to work
- Can iterate from there

**Next step:** Train fresh model with Option 2 rewards
- Test with 5K episodes
- If it reaches 35-40 turns, continue to 50K
- If not, simplify further

**Long term:** If we want sub-25 turns:
- The current 28.1 model is probably near its limit
- Need to understand YOUR strategy (20-25 turns)
- Build imitation learning: learn from human expert play
- Or analyze what YOU do differently

## Key Insight

**The 28.1 model isn't bad - it's already beating the probability strategy (31.4 turns).** The problem is we're trying to push it further with the wrong tools:

- Complex rewards → Confusion
- Continued training → Forgetting
- Scaled penalties → Perverse incentives

**Better approach:**
1. Accept 28.1 as good baseline
2. Build new model with lessons learned
3. Train fresh (not continue)
4. Keep it simple
5. Test frequently (5K episodes, not 100K)
