"""
Benchmark and compare different AI strategies
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent / 'src'))

from game.ml_agent import QLearningAgent
from game.ml_strategy import MLStrategy
from game.ai_strategy import ProbabilityStrategy
from game.solo_simulation import SoloSimulation
from game.benchmark_metrics import BenchmarkMetrics, AIComparison


def benchmark_strategy(strategy, strategy_name, num_games=1000, verbose=True):
    """
    Benchmark a strategy over multiple games.
    
    Returns:
        BenchmarkMetrics object with results
    """
    if verbose:
        print(f"\nBenchmarking {strategy_name}...")
        print(f"Running {num_games} games...")
    
    benchmark = BenchmarkMetrics(strategy_name)
    
    for game_num in range(num_games):
        sim = SoloSimulation(strategy)
        result = sim.simulate()
        
        turns = result.get('turns', 0)
        rolls = result.get('total_rolls', 0)
        completed = result.get('completed', False)
        
        benchmark.add_game(turns, rolls, completed)
        
        if verbose and (game_num + 1) % 100 == 0:
            print(f"  Progress: {game_num + 1}/{num_games} games")
    
    if verbose:
        benchmark.print_report()
    
    return benchmark


def compare_all_strategies(num_games=1000, ml_model_path='models/ml_agent.pkl'):
    """
    Compare all available strategies.
    """
    print("\n" + "="*100)
    print("AI STRATEGY BENCHMARK COMPARISON")
    print("="*100)
    print(f"\nRunning {num_games} games per strategy...")
    
    comparison = AIComparison()
    
    # 1. Probability Strategy (existing)
    print("\n[1/2] Benchmarking Probability Strategy...")
    prob_strategy = ProbabilityStrategy()
    prob_benchmark = benchmark_strategy(prob_strategy, "Probability Strategy", num_games)
    comparison.add_benchmark("Probability", prob_benchmark)
    
    # Save results
    prob_benchmark.save_json('benchmarks/probability_strategy.json')
    
    # 2. ML Strategy (if model exists)
    ml_path = Path(ml_model_path)
    if ml_path.exists():
        print(f"\n[2/2] Benchmarking ML Strategy (loaded from {ml_model_path})...")
        
        agent = QLearningAgent()
        agent.load(str(ml_path))
        
        ml_strategy = MLStrategy(agent)
        ml_benchmark = benchmark_strategy(ml_strategy, "ML Strategy", num_games)
        comparison.add_benchmark("ML Strategy", ml_benchmark)
        
        # Save results
        ml_benchmark.save_json('benchmarks/ml_strategy.json')
    else:
        print(f"\n[2/2] ML model not found at {ml_model_path}")
        print("      Train a model first using: python train_ml.py")
        print("      Skipping ML strategy benchmark...")
    
    # Print comparison
    print("\n" + "="*100)
    comparison.print_comparison()
    
    return comparison


def benchmark_ml_only(num_games=1000, ml_model_path='models/ml_agent.pkl'):
    """Benchmark only the ML strategy"""
    ml_path = Path(ml_model_path)
    if not ml_path.exists():
        print(f"Error: ML model not found at {ml_model_path}")
        print("Train a model first using: python train_ml.py")
        return None
    
    print(f"\nLoading ML agent from {ml_model_path}...")
    agent = QLearningAgent()
    agent.load(str(ml_path))
    
    print(f"\nAgent Stats:")
    stats = agent.get_stats()
    for key, value in stats.items():
        print(f"  {key}: {value}")
    
    ml_strategy = MLStrategy(agent)
    benchmark = benchmark_strategy(ml_strategy, "ML Strategy", num_games)
    
    benchmark.save_json('benchmarks/ml_strategy.json')
    
    return benchmark


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description='Benchmark AI strategies')
    parser.add_argument('--games', type=int, default=1000,
                        help='Number of games to simulate per strategy')
    parser.add_argument('--ml-only', action='store_true',
                        help='Only benchmark ML strategy')
    parser.add_argument('--ml-model', type=str, default='models/ml_agent.pkl',
                        help='Path to ML model file')
    parser.add_argument('--compare', action='store_true',
                        help='Compare all strategies')
    
    args = parser.parse_args()
    
    # Create directories
    Path('benchmarks').mkdir(exist_ok=True)
    
    if args.ml_only:
        benchmark_ml_only(args.games, args.ml_model)
    else:
        compare_all_strategies(args.games, args.ml_model)
