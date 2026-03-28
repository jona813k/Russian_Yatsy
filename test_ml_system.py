"""
Test ML system installation and basic functionality
"""
import sys
from pathlib import Path

print("="*70)
print("ML SYSTEM TEST")
print("="*70)

# Test 1: Check imports
print("\n[1/5] Testing imports...")
try:
    import numpy as np
    print("  ✓ numpy installed")
except ImportError:
    print("  ✗ numpy not found - run: pip install numpy")
    sys.exit(1)

try:
    import scipy
    print("  ✓ scipy installed")
except ImportError:
    print("  ✗ scipy not found - run: pip install scipy")
    sys.exit(1)

sys.path.insert(0, str(Path(__file__).parent / 'src'))

try:
    from game.ml_agent import QLearningAgent
    print("  ✓ ml_agent module loaded")
except ImportError as e:
    print(f"  ✗ ml_agent import failed: {e}")
    sys.exit(1)

try:
    from game.ml_engine import MLGameEngine
    print("  ✓ ml_engine module loaded")
except ImportError as e:
    print(f"  ✗ ml_engine import failed: {e}")
    sys.exit(1)

try:
    from game.ml_trainer import MLTrainer
    print("  ✓ ml_trainer module loaded")
except ImportError as e:
    print(f"  ✗ ml_trainer import failed: {e}")
    sys.exit(1)

try:
    from game.benchmark_metrics import BenchmarkMetrics
    print("  ✓ benchmark_metrics module loaded")
except ImportError as e:
    print(f"  ✗ benchmark_metrics import failed: {e}")
    sys.exit(1)

# Test 2: Create agent
print("\n[2/5] Creating Q-Learning agent...")
try:
    agent = QLearningAgent()
    print(f"  ✓ Agent created (epsilon={agent.epsilon}, lr={agent.lr})")
except Exception as e:
    print(f"  ✗ Failed to create agent: {e}")
    sys.exit(1)

# Test 3: Create game engine
print("\n[3/5] Creating ML game engine...")
try:
    engine = MLGameEngine()
    engine.reset()
    print(f"  ✓ Engine created and reset")
    print(f"    Dice: {engine.state.dice_values}")
    print(f"    Legal actions: {len(engine.get_legal_actions())}")
except Exception as e:
    print(f"  ✗ Failed to create engine: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

# Test 4: Play a few turns
print("\n[4/5] Testing game play...")
try:
    for i in range(5):
        legal_actions = engine.get_legal_actions()
        if not legal_actions:
            engine.reset()
            legal_actions = engine.get_legal_actions()
        
        action = agent.get_action(engine.get_state_representation(), legal_actions, training=False)
        result = engine.execute_action(action)
        
        if not result['success']:
            print(f"  ✗ Action failed: {result}")
            break
    
    print(f"  ✓ Played 5 turns successfully")
    print(f"    Current progress: {sum(engine.player.progress.values())}/72 dice collected")
except Exception as e:
    print(f"  ✗ Game play failed: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

# Test 5: Test training (just 10 episodes)
print("\n[5/5] Testing training loop (10 episodes)...")
try:
    trainer = MLTrainer(agent, verbose=False)
    
    for episode in range(10):
        trainer.play_episode()
    
    print(f"  ✓ Training loop works")
    print(f"    Episodes: {len(trainer.episode_turns)}")
    print(f"    Avg turns: {np.mean(trainer.episode_turns):.1f}")
    print(f"    States learned: {len(agent.q_table)}")
except Exception as e:
    print(f"  ✗ Training failed: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

# Test 6: Benchmark metrics
print("\n[6/6] Testing benchmark metrics...")
try:
    benchmark = BenchmarkMetrics("Test")
    for turn, roll in zip(trainer.episode_turns, trainer.episode_rolls):
        benchmark.add_game(turn, roll, True)
    
    metrics = benchmark.calculate_metrics()
    
    print(f"  ✓ Benchmark metrics calculated")
    print(f"    Median turns: {metrics['median_turns']:.1f}")
    print(f"    Range: {metrics['range_turns']}")
    print(f"    CV: {metrics['cv_turns']:.2f}%")
except Exception as e:
    print(f"  ✗ Benchmark failed: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

# All tests passed!
print("\n" + "="*70)
print("✓ ALL TESTS PASSED!")
print("="*70)
print("\nYou're ready to use the ML system!")
print("\nNext steps:")
print("  1. Train an agent:     python train_ml.py --mode quick")
print("  2. Benchmark:          python benchmark_strategies.py --games 100")
print("  3. Read guide:         Open QUICKSTART.md")
print("="*70)
