# Russian Yatzy AI Benchmark Summary

## Goal
Beat the hand-crafted Probability Strategy (AI1) which averages **31.49 turns** per game.

## Strategies Tested

### 1. Probability Strategy (Baseline - AI1)
**Performance:** 31.49 avg turns, 30 median
- **Approach:** Uses inverse probability as value: `value = (1/probability) * count`
- **Strategy:** "Opportunistically greedy" - immediately takes rarest dice combinations
- **Strengths:**
  - Mathematical certainty - no learning required
  - Fast and consistent decisions
  - Exploits statistical rarity effectively
- **Weaknesses:**
  - Myopic - only looks at current roll
  - Doesn't consider completion progress
  - No long-term planning (doesn't know which numbers are closer to completion)
  - Doesn't factor in wasted turns

### 2. Basic Q-Learning ML Agent (Attempt #1)
**Performance:** 38-39 avg turns (21% slower than baseline)
- **Training:** 100K episodes, 4.4M states explored
- **Hyperparameters:**
  - Learning rate: 0.3
  - Discount factor: 0.98
  - Epsilon decay: 0.9998
- **Reward Structure:**
  - Base: dice_collected * 10
  - Penalties: -3.0 per action, -5.0 per failed turn
  - Completion bonus: 1000 + efficiency_bonus
  - Efficiency bonus: (100 - turns) * 10
- **Result:** ❌ Underperformed despite extensive training
- **Issue:** Tabular Q-learning struggles with massive state space (~4M+ unique states)

### 3. Rarity-Aware Q-Learning (Attempt #2)
**Performance:** 37 avg turns (17.5% slower than baseline)
- **Training:** 35K episodes (interrupted), 1.6M states
- **Enhancement:** Added probability-strategy-inspired rewards
  - Rarity score: `min(1.0 / (probability + 0.001), 1000.0)`
  - Completion urgency multiplier: 1.0-2.5x based on progress
  - Endgame bonus multiplier: 1.0-3.0x based on numbers completed
  - Strategic bonus: `(rarity * 0.5) * urgency * endgame` (capped at 300)
- **Result:** ❌ Slight improvement but still significantly slower
- **Issue:** Even with domain knowledge, tabular Q-learning convergence too slow

## Key Insights

### Why Probability Strategy Works
1. **Domain Knowledge**: Uses mathematical probability directly - no guessing
2. **Rarity Awareness**: Automatically prioritizes rare combinations (high value = low probability)
3. **Instant Decisions**: No exploration needed, uses exact calculations
4. **Consistency**: Always makes the mathematically optimal myopic choice

### Why ML Agents Struggle
1. **State Space Explosion**: Russian Yatzy has millions of possible states
   - 12 progress values (0-6 each) = 7^12 ≈ 13.8 billion possible progress states
   - Combined with dice values, selected number, etc. = massive state space
2. **Exploration Cost**: Tabular Q-learning must visit states many times to learn
3. **Generalization Problem**: Each unique state learned separately, no transfer
4. **Learning vs. Mathematics**: ML discovers through trial/error what probability knows by calculation

### Probability Strategy's Hidden Weakness
Despite being optimal for myopic decisions, it has exploitable weaknesses:
- **No Completion Awareness**: Doesn't prioritize numbers close to completion (e.g., 5/6 collected)
- **No Endgame Planning**: Treats all stages of game equally
- **Wasted Turn Blindness**: Doesn't consider that incomplete numbers require more turns

**Potential for Improvement:** An ML agent that learns long-term planning COULD theoretically beat probability strategy by:
- Prioritizing nearly-complete numbers to reduce total turns
- Learning which number combinations finish games faster
- Understanding endgame urgency (when close to winning)

However, current tabular Q-learning approaches can't exploit this because:
- Convergence takes too long
- State space too large
- Generalization insufficient

## Recommendations for Future Work

### 1. Deep Q-Network (DQN)
**Why:** Neural networks can generalize across similar states
- **Approach:** Use PyTorch/TensorFlow to build DQN
- **Benefits:** 
  - Function approximation instead of table lookup
  - Generalization across similar game states
  - Faster convergence with experience replay
- **Requirements:** `pip install torch`
- **Implementation:** Already created in `src/game/dqn_agent.py` and `train_dqn.py`

### 2. Hybrid Approach
**Why:** Combine probability strategy's domain knowledge with ML refinement
- **Approach:** Start with probability-based action selection, learn adjustments
- **Implementation:** Already created in `src/game/hybrid_strategy.py`
- **Benefits:**
  - Warm start with good baseline strategy
  - ML only needs to learn refinements, not basics
  - Faster convergence

### 3. Imitation Learning
**Why:** Learn from probability strategy demonstrations
- **Approach:** Supervised learning on probability strategy games
- **Benefits:** 
  - Learn the probability strategy's patterns quickly
  - Then use reinforcement learning for improvements
  - Addresses cold-start problem

### 4. Accept Probability Strategy as "Good Enough"
**Why:** 31.49 turns is strong performance
- Hand-crafted strategies with domain expertise are hard to beat
- ML's advantage would be in:
  - Adapting to rule changes automatically
  - Discovering non-obvious long-term patterns
  - But for this game, the math is straightforward

## Benchmarking Results (1000 games each)

| Strategy | Mean Turns | Median Turns | Completion Rate | Consistency Index |
|----------|------------|--------------|-----------------|-------------------|
| **Probability** | **31.49** | **30.00** | 100.0% | 0.879 |
| ML Basic | 37.01 | 36.00 | 100.0% | 0.888 |
| ML Rarity-Aware | 37.00* | ~36.00* | 100.0% | ~0.88* |

*Estimated from partial training (35K episodes)

## Conclusion

**Current Winner: Probability Strategy (AI1)**

The hand-crafted probability strategy remains unbeaten, averaging **31.49 turns** per game. While ML agents complete 100% of games (a success after fixing the initial bugs), they take 17-21% longer to win.

**Key Lesson:** When domain knowledge is strong and the optimal myopic strategy is mathematically definable, hand-crafted approaches can outperform reinforcement learning - especially tabular Q-learning in large state spaces.

**Path Forward:** To beat the probability strategy, we'd need:
1. **Deep Q-Network** for better generalization, OR
2. **Hybrid approach** starting with probability knowledge, OR
3. **Different game formulation** where long-term planning matters more

The current ML implementation is fully functional and learns successfully, but can't match hand-crafted mathematical optimization within reasonable training time.
