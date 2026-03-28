"""
Train ML agent for Russian Yatzy
"""
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / 'src'))

from game.ml_agent import QLearningAgent
from game.ml_trainer import MLTrainer
from game.benchmark_metrics import BenchmarkMetrics


def train_agent(episodes=50000, save_path='models/ml_agent.pkl'):
    """Train a new ML agent from scratch"""
    print("Initializing Q-Learning Agent...")
    
    # Create agent with tuned parameters
    agent = QLearningAgent(
        learning_rate=0.1,
        discount_factor=0.95,
        epsilon=0.3,  # Start with more exploration
        epsilon_decay=0.9995,
        epsilon_min=0.01
    )
    
    # Create trainer
    trainer = MLTrainer(agent, verbose=True)
    
    # Train
    print(f"\nTraining for {episodes} episodes...")
    training_data = trainer.train(
        episodes=episodes,
        save_every=5000,
        save_path=save_path
    )
    
    # Evaluate
    print("\n" + "="*70)
    print("Evaluating trained agent...")
    print("="*70)
    
    eval_results = trainer.evaluate(num_games=1000)
    
    print(f"\nEvaluation Results (1000 games):")
    print(f"  Completion Rate:  {eval_results['completion_rate']:.1f}%")
    print(f"  Average Turns:    {eval_results['avg_turns']:.2f}")
    print(f"  Median Turns:     {eval_results['median_turns']:.2f}")
    print(f"  Std Turns:        {eval_results['std_turns']:.2f}")
    print(f"  Range:            {eval_results['min_turns']} - {eval_results['max_turns']}")
    print(f"  Average Rolls:    {eval_results['avg_rolls']:.2f}")
    print(f"  Median Rolls:     {eval_results['median_rolls']:.2f}")
    
    return agent, training_data


def continue_training(load_path='models/ml_agent.pkl', episodes=10000):
    """Continue training an existing agent"""
    print(f"Loading agent from {load_path}...")
    
    agent = QLearningAgent()
    agent.load(load_path)
    
    print(f"\nContinuing training for {episodes} more episodes...")
    
    trainer = MLTrainer(agent, verbose=True)
    training_data = trainer.train(
        episodes=episodes,
        save_every=2000,
        save_path=load_path
    )
    
    return agent, training_data


def quick_train():
    """Quick training for testing (5000 episodes)"""
    print("Quick training mode - 5000 episodes")
    return train_agent(episodes=5000, save_path='models/ml_agent_quick.pkl')


def full_train():
    """Full training (50000 episodes)"""
    print("Full training mode - 50000 episodes")
    return train_agent(episodes=50000, save_path='models/ml_agent_full.pkl')


def extended_train():
    """Extended training (100000 episodes)"""
    print("Extended training mode - 100000 episodes")
    return train_agent(episodes=100000, save_path='models/ml_agent_extended.pkl')


def ultimate_train():
    """Ultimate training (200000 episodes)"""
    print("Ultimate training mode - 200000 episodes")
    return train_agent(episodes=200000, save_path='models/ml_agent_ultimate.pkl')


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description='Train ML agent for Russian Yatzy')
    parser.add_argument('--mode', choices=['quick', 'full', 'extended', 'ultimate', 'continue'],
                        default='full', help='Training mode')
    parser.add_argument('--episodes', type=int, help='Number of episodes (overrides mode)')
    parser.add_argument('--load', type=str, help='Path to load existing agent')
    parser.add_argument('--save', type=str, default='models/ml_agent.pkl',
                        help='Path to save trained agent')
    
    args = parser.parse_args()
    
    if args.mode == 'continue' or args.load:
        load_path = args.load or 'models/ml_agent.pkl'
        episodes = args.episodes or 10000
        agent, data = continue_training(load_path, episodes)
    else:
        if args.mode == 'quick':
            episodes = args.episodes or 5000
        elif args.mode == 'full':
            episodes = args.episodes or 50000
        elif args.mode == 'extended':
            episodes = args.episodes or 100000
        elif args.mode == 'ultimate':
            episodes = args.episodes or 200000
        else:
            episodes = args.episodes or 50000
        
        agent, data = train_agent(episodes, args.save)
    
    print("\n✓ Training complete!")
    print(f"Agent saved to: {args.save}")
