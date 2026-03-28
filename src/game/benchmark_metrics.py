"""
Enhanced Benchmark Metrics for AI Strategy Comparison
"""
import numpy as np
from typing import List, Dict
import json
from pathlib import Path


class BenchmarkMetrics:
    """
    Comprehensive benchmark metrics for comparing AI strategies.
    Tracks turns, rolls, and provides detailed statistical analysis.
    """
    
    def __init__(self, strategy_name: str = "Unknown"):
        self.strategy_name = strategy_name
        self.game_turns = []  # Number of turns per game
        self.game_rolls = []  # Number of rolls per game
        self.completed_games = 0
        self.failed_games = 0
    
    def add_game(self, turns: int, rolls: int, completed: bool = True):
        """Add a completed game's statistics"""
        self.game_turns.append(turns)
        self.game_rolls.append(rolls)
        if completed:
            self.completed_games += 1
        else:
            self.failed_games += 1
    
    def calculate_metrics(self) -> Dict:
        """Calculate comprehensive statistical metrics"""
        if not self.game_turns:
            return {'error': 'No games recorded'}
        
        turns = np.array(self.game_turns)
        rolls = np.array(self.game_rolls)
        
        return {
            # Game completion
            'total_games': len(self.game_turns),
            'completed_games': self.completed_games,
            'failed_games': self.failed_games,
            'completion_rate': self.completed_games / len(self.game_turns) * 100,
            
            # Turn statistics
            'mean_turns': float(np.mean(turns)),
            'median_turns': float(np.median(turns)),
            'std_turns': float(np.std(turns)),
            'min_turns': int(np.min(turns)),
            'max_turns': int(np.max(turns)),
            'range_turns': int(np.max(turns) - np.min(turns)),
            'q1_turns': float(np.percentile(turns, 25)),
            'q3_turns': float(np.percentile(turns, 75)),
            'iqr_turns': float(np.percentile(turns, 75) - np.percentile(turns, 25)),
            
            # Roll statistics
            'mean_rolls': float(np.mean(rolls)),
            'median_rolls': float(np.median(rolls)),
            'std_rolls': float(np.std(rolls)),
            'min_rolls': int(np.min(rolls)),
            'max_rolls': int(np.max(rolls)),
            'range_rolls': int(np.max(rolls) - np.min(rolls)),
            'q1_rolls': float(np.percentile(rolls, 25)),
            'q3_rolls': float(np.percentile(rolls, 75)),
            'iqr_rolls': float(np.percentile(rolls, 75) - np.percentile(rolls, 25)),
            
            # Efficiency metrics
            'rolls_per_turn': float(np.mean(rolls / turns)),
            
            # Consistency metrics (lower is more consistent)
            'cv_turns': float((np.std(turns) / np.mean(turns)) * 100),  # Coefficient of variation
            'cv_rolls': float((np.std(rolls) / np.mean(rolls)) * 100),
            'consistency_index_turns': float(1 - (np.std(turns) / np.max(turns))),
            'consistency_index_rolls': float(1 - (np.std(rolls) / np.max(rolls))),
            
            # Percentile analysis
            'p10_turns': float(np.percentile(turns, 10)),
            'p90_turns': float(np.percentile(turns, 90)),
            'p10_rolls': float(np.percentile(rolls, 10)),
            'p90_rolls': float(np.percentile(rolls, 90)),
        }
    
    def print_report(self):
        """Print formatted benchmark report"""
        metrics = self.calculate_metrics()
        
        if 'error' in metrics:
            print(f"\nError: {metrics['error']}")
            return
        
        print(f"\n{'='*80}")
        print(f"BENCHMARK REPORT: {self.strategy_name}")
        print(f"{'='*80}")
        
        print(f"\n--- GAME COMPLETION ---")
        print(f"Total Games:        {metrics['total_games']}")
        print(f"Completed:          {metrics['completed_games']} ({metrics['completion_rate']:.1f}%)")
        print(f"Failed:             {metrics['failed_games']}")
        
        print(f"\n--- TURN STATISTICS ---")
        print(f"Mean Turns:         {metrics['mean_turns']:.2f}")
        print(f"Median Turns:       {metrics['median_turns']:.2f}")
        print(f"Std Deviation:      {metrics['std_turns']:.2f}")
        print(f"Min Turns:          {metrics['min_turns']}")
        print(f"Max Turns:          {metrics['max_turns']}")
        print(f"Range:              {metrics['range_turns']} (best to worst)")
        print(f"IQR (Q1-Q3):        {metrics['q1_turns']:.1f} - {metrics['q3_turns']:.1f}")
        print(f"10th-90th %ile:     {metrics['p10_turns']:.1f} - {metrics['p90_turns']:.1f}")
        
        print(f"\n--- ROLL STATISTICS ---")
        print(f"Mean Rolls:         {metrics['mean_rolls']:.2f}")
        print(f"Median Rolls:       {metrics['median_rolls']:.2f}")
        print(f"Std Deviation:      {metrics['std_rolls']:.2f}")
        print(f"Min Rolls:          {metrics['min_rolls']}")
        print(f"Max Rolls:          {metrics['max_rolls']}")
        print(f"Range:              {metrics['range_rolls']} (best to worst)")
        print(f"IQR (Q1-Q3):        {metrics['q1_rolls']:.1f} - {metrics['q3_rolls']:.1f}")
        print(f"10th-90th %ile:     {metrics['p10_rolls']:.1f} - {metrics['p90_rolls']:.1f}")
        
        print(f"\n--- EFFICIENCY ---")
        print(f"Rolls per Turn:     {metrics['rolls_per_turn']:.2f}")
        
        print(f"\n--- CONSISTENCY METRICS ---")
        print(f"CV Turns:           {metrics['cv_turns']:.2f}% (lower = more consistent)")
        print(f"CV Rolls:           {metrics['cv_rolls']:.2f}% (lower = more consistent)")
        print(f"Consistency Index:  {metrics['consistency_index_turns']:.3f} (higher = more consistent)")
        print(f"Turn Spread:        {metrics['range_turns']} between best and worst")
        print(f"Roll Spread:        {metrics['range_rolls']} between best and worst")
        
        print(f"{'='*80}\n")
    
    def save_json(self, filepath: str):
        """Save metrics to JSON file"""
        metrics = self.calculate_metrics()
        metrics['strategy_name'] = self.strategy_name
        metrics['raw_turns'] = self.game_turns
        metrics['raw_rolls'] = self.game_rolls
        
        path = Path(filepath)
        path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(filepath, 'w') as f:
            json.dump(metrics, f, indent=2)
        
        print(f"Saved benchmark metrics to {filepath}")
    
    def load_json(self, filepath: str):
        """Load metrics from JSON file"""
        with open(filepath, 'r') as f:
            data = json.load(f)
        
        self.strategy_name = data.get('strategy_name', 'Unknown')
        self.game_turns = data.get('raw_turns', [])
        self.game_rolls = data.get('raw_rolls', [])
        self.completed_games = data.get('completed_games', 0)
        self.failed_games = data.get('failed_games', 0)


class AIComparison:
    """Compare multiple AI strategies"""
    
    def __init__(self):
        self.benchmarks: Dict[str, BenchmarkMetrics] = {}
    
    def add_benchmark(self, name: str, benchmark: BenchmarkMetrics):
        """Add a benchmark for comparison"""
        self.benchmarks[name] = benchmark
    
    def load_benchmark(self, name: str, filepath: str):
        """Load benchmark from file"""
        benchmark = BenchmarkMetrics(name)
        benchmark.load_json(filepath)
        self.benchmarks[name] = benchmark
    
    def compare(self) -> Dict:
        """Compare all benchmarks"""
        comparison = {}
        for name, benchmark in self.benchmarks.items():
            comparison[name] = benchmark.calculate_metrics()
        return comparison
    
    def print_comparison(self):
        """Print side-by-side comparison"""
        if not self.benchmarks:
            print("No benchmarks to compare")
            return
        
        comparison = self.compare()
        
        print(f"\n{'='*100}")
        print(f"AI STRATEGY COMPARISON")
        print(f"{'='*100}")
        
        # Header
        header = f"{'Metric':<30}"
        for name in self.benchmarks.keys():
            header += f"{name:>20}"
        print(header)
        print('-' * 100)
        
        # Key metrics
        metrics_to_show = [
            ('Games', 'total_games', '{:.0f}'),
            ('Completion Rate', 'completion_rate', '{:.1f}%'),
            ('Mean Turns', 'mean_turns', '{:.2f}'),
            ('Median Turns', 'median_turns', '{:.2f}'),
            ('Std Turns', 'std_turns', '{:.2f}'),
            ('Range Turns', 'range_turns', '{:.0f}'),
            ('Mean Rolls', 'mean_rolls', '{:.2f}'),
            ('Median Rolls', 'median_rolls', '{:.2f}'),
            ('Std Rolls', 'std_rolls', '{:.2f}'),
            ('Range Rolls', 'range_rolls', '{:.0f}'),
            ('Rolls/Turn', 'rolls_per_turn', '{:.2f}'),
            ('CV Turns %', 'cv_turns', '{:.2f}'),
            ('Consistency Index', 'consistency_index_turns', '{:.3f}'),
        ]
        
        for label, key, fmt in metrics_to_show:
            row = f"{label:<30}"
            for name in self.benchmarks.keys():
                value = comparison[name].get(key, 0)
                if '%' in fmt:
                    row += f"{fmt.format(value):>20}"
                else:
                    row += f"{fmt.format(value):>20}"
            print(row)
        
        print('=' * 100)
        
        # Determine winner
        print("\n--- RANKING ---")
        
        # Rank by median turns (lower is better)
        rankings = sorted(
            [(name, comparison[name]['median_turns']) for name in self.benchmarks.keys()],
            key=lambda x: x[1]
        )
        
        print("By Median Turns (lower is better):")
        for i, (name, value) in enumerate(rankings, 1):
            print(f"  {i}. {name}: {value:.2f} turns")
        
        # Rank by consistency (higher is better)
        rankings_consistency = sorted(
            [(name, comparison[name]['consistency_index_turns']) for name in self.benchmarks.keys()],
            key=lambda x: x[1],
            reverse=True
        )
        
        print("\nBy Consistency (higher is better):")
        for i, (name, value) in enumerate(rankings_consistency, 1):
            print(f"  {i}. {name}: {value:.3f} consistency index")
        
        print()
