"""
Main entry point for the dice game simulation
"""
from game.game_logic import GameEngine
from game.simulation import GameSimulation
from game.solo_simulation import SoloSimulation
from game.ai_strategy import ProbabilityStrategy
from ui.terminal_ui import TerminalUI
from ui.gui import DiceGameGUI
from ui.start_menu import StartMenuGUI
from ui.benchmark_gui import BenchmarkGUI
import json
import os
from pathlib import Path


# AI strategy mapping
AI_STRATEGIES = {
    'ai1': ('Den Akademiske', ProbabilityStrategy())
}


def load_dqn_strategy():
    """Load DQN strategy if available"""
    try:
        from game.dqn_strategy import DQNStrategy
        
        model_path = 'models/simple_dqn_agent.pth'
        if os.path.exists(model_path):
            strategy = DQNStrategy()
            return strategy
        else:
            return None
    except (ImportError, FileNotFoundError) as e:
        print(f"DQN strategy not available: {e}")
        return None


def load_ml_strategy():
    """Load ML strategy if available"""
    try:
        from game.ml_agent import QLearningAgent
        from game.ml_strategy import MLStrategy
        
        model_path = 'models/ml_agent.pkl'
        if os.path.exists(model_path):
            agent = QLearningAgent()
            agent.load(model_path)
            return MLStrategy(agent)
        else:
            return None
    except ImportError:
        return None


def is_ai_player(player_name: str) -> bool:
    """Check if player name is an AI"""
    return player_name.lower() in AI_STRATEGIES


def get_ai_strategy(player_name: str):
    """Get AI strategy for player name"""
    return AI_STRATEGIES.get(player_name.lower(), (None, None))[1]


def play_ai_turn(engine: GameEngine, ui: TerminalUI, strategy) -> tuple:
    """Play a turn for an AI player"""
    current_player = engine.state.get_current_player()
    ui.display_turn_header(current_player.name)
    
    # Initial roll
    dice = engine.start_turn()
    
    # AI selects number
    selected_number = strategy.select_number(dice, current_player.progress)
    ui.display_message(f"{current_player.name} vælger: {selected_number}")
    
    success, count, message, completed = engine.select_dice(selected_number)
    ui.display_message(message)
    
    if not success:
        winner, bonus = engine.end_turn()
        return winner, bonus
    
    # Check if number was completed
    if completed:
        ui.display_message(f"\n🎉 {current_player.name} har samlet 6 × {selected_number}! Alle terninger returneres! 🎉")
        engine.state.num_dice_in_hand = 6
        engine.state.selected_number = None
        engine.state.collected_this_turn = 0
        return play_ai_turn_continuation(engine, ui, strategy)
    
    # Continue rolling automatically
    while engine.state.num_dice_in_hand > 0:
        can_continue, new_dice, msg = engine.continue_rolling()
        ui.display_message(msg)
        
        if not can_continue:
            break
        
        success, count, message, completed = engine.select_dice(selected_number)
        ui.display_message(message)
        
        if completed:
            ui.display_message(f"\n🎉 {current_player.name} har samlet 6 × {selected_number}! Alle terninger returneres! 🎉")
            engine.state.num_dice_in_hand = 6
            engine.state.selected_number = None
            engine.state.collected_this_turn = 0
            return play_ai_turn_continuation(engine, ui, strategy)
    
    ui.display_message(f"\nTur slut for {current_player.name}!")
    winner, bonus_turn = engine.end_turn()
    
    if bonus_turn:
        ui.display_message(f"\n🎉 {current_player.name} brugte alle terninger! Ekstra tur! 🎉")
    
    return winner, bonus_turn


def play_ai_turn_continuation(engine: GameEngine, ui: TerminalUI, strategy) -> tuple:
    """Continue AI turn after completing a number"""
    current_player = engine.state.get_current_player()
    
    dice = engine.start_turn()
    ui.display_message(f"\n{current_player.name} slår igen med alle terninger!")
    
    # AI selects new number
    selected_number = strategy.select_number(dice, current_player.progress)
    ui.display_message(f"{current_player.name} vælger: {selected_number}")
    
    success, count, message, completed = engine.select_dice(selected_number)
    ui.display_message(message)
    
    if not success:
        winner, bonus = engine.end_turn()
        return winner, bonus
    
    if completed:
        ui.display_message(f"\n🎉 {current_player.name} har samlet 6 × {selected_number}! Alle terninger returneres! 🎉")
        engine.state.num_dice_in_hand = 6
        engine.state.selected_number = None
        engine.state.collected_this_turn = 0
        return play_ai_turn_continuation(engine, ui, strategy)
    
    # Continue with remaining dice
    while engine.state.num_dice_in_hand > 0:
        can_continue, new_dice, msg = engine.continue_rolling()
        ui.display_message(msg)
        
        if not can_continue:
            break
        
        success, count, message, completed = engine.select_dice(selected_number)
        ui.display_message(message)
        
        if completed:
            ui.display_message(f"\n🎉 {current_player.name} har samlet 6 × {selected_number}! Alle terninger returneres! 🎉")
            engine.state.num_dice_in_hand = 6
            engine.state.selected_number = None
            engine.state.collected_this_turn = 0
            return play_ai_turn_continuation(engine, ui, strategy)
    
    ui.display_message(f"\nTur slut for {current_player.name}!")
    winner, bonus_turn = engine.end_turn()
    
    if bonus_turn:
        ui.display_message(f"\n🎉 {current_player.name} brugte alle terninger! Ekstra tur! 🎉")
    
    return winner, bonus_turn


def play_turn(engine: GameEngine, ui: TerminalUI, ai_strategies: dict = None):
    """Play a single player's turn"""
    current_player = engine.state.get_current_player()
    
    # Check if current player is AI
    if ai_strategies and current_player.name in ai_strategies:
        return play_ai_turn(engine, ui, ai_strategies[current_player.name])
    
    ui.display_turn_header(current_player.name)
    
    # Initial roll
    dice = engine.start_turn()
    ui.display_dice(dice)
    
    # Select a number
    selected_number = ui.get_number_input("Vælg et tal at samle (1-12): ", 1, 12)
    
    if selected_number == 'quit':
        return ('quit', False)
    
    success, count, message, completed = engine.select_dice(selected_number)
    ui.display_message(message)
    
    if not success:
        # No matching dice, turn ends immediately
        winner, bonus = engine.end_turn()
        return winner, bonus
    
    # Check if number was completed
    if completed:
        ui.display_message(f"\n🎉 Du har samlet 6 × {selected_number}! Alle terninger returneres! 🎉")
        # Reset for new round with all dice
        engine.state.num_dice_in_hand = 6
        engine.state.selected_number = None
        engine.state.collected_this_turn = 0
        
        # Continue with new selection
        return play_turn_continuation(engine, ui, ai_strategies)
    
    # Continue rolling automatically while player has dice
    while engine.state.num_dice_in_hand > 0:
        ui.display_message(f"\nDu har {engine.state.num_dice_in_hand} terninger tilbage...")
        
        can_continue, new_dice, msg = engine.continue_rolling()
        
        if new_dice:
            ui.display_dice(new_dice)
        ui.display_message(msg)
        
        if not can_continue:
            break
        
        # Automatically select matching dice from new roll
        success, count, message, completed = engine.select_dice(selected_number)
        ui.display_message(message)
        
        # Check if number was completed mid-turn
        if completed:
            ui.display_message(f"\n🎉 Du har samlet 6 × {selected_number}! Alle terninger returneres! 🎉")
            # Reset for new round with all dice
            engine.state.num_dice_in_hand = 6
            engine.state.selected_number = None
            engine.state.collected_this_turn = 0
            
            # Continue with new selection
            return play_turn_continuation(engine, ui, ai_strategies)
    
    # End turn and check for winner
    ui.display_message(f"\nTur slut! Du samlede i alt denne tur.")
    winner, bonus_turn = engine.end_turn()
    
    if bonus_turn:
        ui.display_message("\n🎉 Alle terninger brugt! Du får en ekstra tur! 🎉")
    
    return winner, bonus_turn


def play_turn_continuation(engine: GameEngine, ui: TerminalUI, ai_strategies: dict = None):
    """Continue playing after completing a number"""
    current_player = engine.state.get_current_player()
    
    # Check if current player is AI
    if ai_strategies and current_player.name in ai_strategies:
        return play_ai_turn_continuation(engine, ui, ai_strategies[current_player.name])
    
    # Roll all 6 dice again
    dice = engine.start_turn()
    ui.display_message(f"\n{current_player.name} slår igen med alle terninger!")
    ui.display_dice(dice)
    
    # Select a new number
    selected_number = ui.get_number_input("Vælg et nyt tal at samle (1-12): ", 1, 12)
    
    if selected_number == 'quit':
        return ('quit', False)
    
    success, count, message, completed = engine.select_dice(selected_number)
    ui.display_message(message)
    
    if not success:
        winner, bonus = engine.end_turn()
        return winner, bonus
    
    # Check if this number was also completed
    if completed:
        ui.display_message(f"\n🎉 Du har samlet 6 × {selected_number}! Alle terninger returneres! 🎉")
        engine.state.num_dice_in_hand = 6
        engine.state.selected_number = None
        engine.state.collected_this_turn = 0
        return play_turn_continuation(engine, ui, ai_strategies)
    
    # Continue with remaining dice
    while engine.state.num_dice_in_hand > 0:
        ui.display_message(f"\nDu har {engine.state.num_dice_in_hand} terninger tilbage...")
        
        can_continue, new_dice, msg = engine.continue_rolling()
        
        if new_dice:
            ui.display_dice(new_dice)
        ui.display_message(msg)
        
        if not can_continue:
            break
        
        success, count, message, completed = engine.select_dice(selected_number)
        ui.display_message(message)
        
        if completed:
            ui.display_message(f"\n🎉 Du har samlet 6 × {selected_number}! Alle terninger returneres! 🎉")
            engine.state.num_dice_in_hand = 6
            engine.state.selected_number = None
            engine.state.collected_this_turn = 0
            return play_turn_continuation(engine, ui, ai_strategies)
    
    ui.display_message(f"\nTur slut!")
    winner, bonus_turn = engine.end_turn()
    
    if bonus_turn:
        ui.display_message("\n🎉 Alle terninger brugt! Du får en ekstra tur! 🎉")
    
    return winner, bonus_turn


def main():
    """Main game loop"""
    # Try to load DQN strategy as ai2
    dqn_strategy = load_dqn_strategy()
    if dqn_strategy:
        AI_STRATEGIES['ai2'] = ('ML Master (DQN)', dqn_strategy)
    
    while True:
        # Show start menu GUI
        menu = StartMenuGUI()
        choice, player_names = menu.run()
        
        if choice == 'quit' or choice is None:
            break
        
        if choice == 'gui_game' and player_names:
            # Start GUI game with selected players
            # Check for AI players and create strategy mapping
            ai_strategies = {}
            for name in player_names:
                strategy = get_ai_strategy(name)
                if strategy:
                    ai_strategies[name] = strategy
            
            engine = GameEngine()
            engine.setup_game(player_names)
            
            # Start GUI
            gui = DiceGameGUI(engine, ai_strategies)
            gui.run()
        
        elif choice == 'benchmark':
            # Run benchmark with GUI
            run_benchmark_in_gui()


def run_simulation(ui: TerminalUI):
    """Run AI vs AI simulation"""
    ui.display_message("\n" + "="*50)
    ui.display_message("   AI SIMULATION")
    ui.display_message("="*50)
    ui.display_message("\nSpiller 1: Sandsynlighedsstrategi (vælger sjældne kombinationer)")
    ui.display_message("Spiller 2: Afslutningsstrategi (afslutter tal hurtigt)")
    ui.display_message("="*50)
    
    # Ask for verbose mode
    verbose = ui.get_yes_no("\nVis detaljeret information under spillet?")
    if verbose == 'quit':
        return
    
    # Run simulation
    sim = GameSimulation()
    strategy1 = ProbabilityStrategy()
    strategy2 = CompletionStrategy()
    
    ui.display_message("\nSpillet starter...\n")
    
    stats = sim.simulate_game(
        "AI-Sandsynlighed",
        "AI-Afslutning",
        strategy1,
        strategy2,
        verbose=verbose
    )
    
    # Display results
    ui.display_message("\n" + "="*50)
    ui.display_message("   RESULTAT")
    ui.display_message("="*50)
    ui.display_message(f"\n🏆 Første vinder: {stats['first_winner']}")
    ui.display_message(f"  - Runder for at vinde: {stats['first_winner_rounds']}")
    ui.display_message(f"  - Slag for at vinde: {stats['first_winner_rolls']}")
    
    ui.display_message(f"\nTotal (begge spillere færdige):")
    ui.display_message(f"  - Antal runder: {stats['total_rounds']}")
    ui.display_message(f"  - Antal slag: {stats['total_rolls']}")
    
    ui.display_message(f"\nAI-Sandsynlighed:")
    ui.display_message(f"  - Antal slag: {stats['player1_rolls']}")
    ui.display_message(f"  - Antal ture: {stats['player1_turns']}")
    
    ui.display_message(f"\nAI-Afslutning:")
    ui.display_message(f"  - Antal slag: {stats['player2_rolls']}")
    ui.display_message(f"  - Antal ture: {stats['player2_turns']}")
    
    # Show difference
    roll_diff = abs(stats['player1_rolls'] - stats['player2_rolls'])
    turn_diff = abs(stats['player1_turns'] - stats['player2_turns'])
    ui.display_message(f"\nForskel:")
    ui.display_message(f"  - Slag forskel: {roll_diff}")
    ui.display_message(f"  - Ture forskel: {turn_diff}")
    
    input("\nTryk Enter for at fortsætte...")


def run_benchmark_in_gui():
    """Run benchmark simulation with GUI progress display"""
    def show_cached_generator():
        """Generator that shows cached results"""
        cache_file = Path('simulation_cache.json')
        
        yield {'status': 'Indlæser gemte resultater...'}
        
        cached_data = load_cache(cache_file)
        
        # Check if we have cached data
        if not cached_data or 'probability_1000' not in cached_data:
            yield {'error': 'Ingen gemte resultater fundet. Kør en ny test først.'}
            return
        
        # Collect results
        all_results = {}
        
        # Load probability results
        if 'probability_1000' in cached_data:
            all_results['AI1 - Sandsynlighedsstrategi'] = cached_data['probability_1000']
        
        # Load DQN results if available
        if 'dqn_1000' in cached_data:
            all_results['AI2 - DQN Neural Network'] = cached_data['dqn_1000']
        
        yield {'status': 'Viser resultater...'}
        
        # Sort by average turns (best first)
        sorted_results = sorted(all_results.items(), key=lambda x: x[1]['avg_turns'])
        
        for rank, (name, data) in enumerate(sorted_results, 1):
            # Send each result as a dict for table display
            yield {'result': {
                'strategy': name,
                'avg_score': data['avg_turns'],
                'win_rate': 100.0 / rank,
                'avg_turns': data['avg_turns']
            }}
        
        yield {'complete': True}
        
        yield {'result': f'\n{"="*60}'}
        yield {'result': '\n💡 Antal ture er den vigtigste metric!'}
        yield {'result': '   Median viser typisk performance uden ekstreme heldiggreb.'}
        yield {'result': f'\n{"="*60}'}
        
        yield {'complete': True}
    
    def benchmark_generator():
        """Generator that yields progress updates"""
        cache_file = Path('simulation_cache.json')
        
        # Load DQN strategy
        yield {'status': 'Indlæser AI strategier...'}
        dqn_strategy = load_dqn_strategy()
        
        strategies_to_test = [
            ('AI1 - Sandsynlighedsstrategi', 'probability', ProbabilityStrategy()),
            ('AI2 - DQN Neural Network', 'dqn', dqn_strategy if dqn_strategy else None)
        ]
        
        # Filter out None strategies
        strategies_to_test = [(name, key, strat) for name, key, strat in strategies_to_test if strat is not None]
        
        all_results = {}
        cached_data = load_cache(cache_file)
        
        # Test each strategy
        for strategy_name, cache_key, strategy_obj in strategies_to_test:
            yield {'status': f'Tester {strategy_name}...'}
            yield {'result': f'\n{"="*60}'}
            yield {'result': f'   {strategy_name.upper()}'}
            yield {'result': f'{"="*60}'}
            
            # Check for cached results
            cache_key_1000 = f"{cache_key}_1000"
            
            if cache_key_1000 in cached_data:
                yield {'result': f'\n💾 Bruger gemte resultater for {strategy_name}'}
                all_results[strategy_name] = cached_data[cache_key_1000]
            else:
                yield {'result': f'\nKører 1000 simuleringer...'}
                
                # Run 1000 simulations
                results = []
                for i in range(1000):
                    if (i + 1) % 100 == 0:
                        yield {'progress': (i + 1, 1000)}
                    
                    sim = SoloSimulation(strategy_obj)
                    stats = sim.simulate_solo_game(f"Test-{cache_key}", strategy_obj, verbose=False)
                    results.append(stats)
                
                # Calculate statistics
                total_rolls = [r['rolls'] for r in results]
                total_turns = [r['turns'] for r in results]
                
                # Sort for median calculation
                sorted_rolls = sorted(total_rolls)
                sorted_turns = sorted(total_turns)
                median_idx = len(sorted_turns) // 2
                
                result_data = {
                    'avg_rolls': sum(total_rolls) / len(total_rolls),
                    'median_rolls': sorted_rolls[median_idx],
                    'min_rolls': min(total_rolls),
                    'max_rolls': max(total_rolls),
                    'avg_turns': sum(total_turns) / len(total_turns),
                    'median_turns': sorted_turns[median_idx],
                    'min_turns': min(total_turns),
                    'max_turns': max(total_turns),
                    'std_turns': sum((x - (sum(total_turns)/len(total_turns)))**2 for x in total_turns) ** 0.5 / len(total_turns),
                    'strategy_name': strategy_name
                }
                
                all_results[strategy_name] = result_data
                
                # Save to cache
                cached_data[cache_key_1000] = result_data
                save_cache(cache_file, cached_data)
                
                yield {'result': f'✅ {strategy_name} færdig!'}
        
        # Display comparison results
        yield {'status': 'Genererer resultater...'}
        
        # Sort by average turns (best first)
        sorted_results = sorted(all_results.items(), key=lambda x: x[1]['avg_turns'])
        
        for rank, (name, data) in enumerate(sorted_results, 1):
            # Send each result as a dict for table display
            yield {'result': {
                'strategy': name,
                'avg_score': data['avg_turns'],  # Using turns as "score" (lower is better)
                'win_rate': 100.0 / rank,  # Simple ranking-based "win rate"
                'avg_turns': data['avg_turns']
            }}
        
        yield {'complete': True}
    
    # Create and run benchmark GUI with both callbacks
    gui = BenchmarkGUI(benchmark_generator, show_cached_generator)
    gui.run()


def load_cache(cache_file: Path) -> dict:
    """Load cached simulation results"""
    if cache_file.exists():
        try:
            with open(cache_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except:
            return {}
    return {}


def save_cache(cache_file: Path, data: dict):
    """Save simulation results to cache"""
    try:
        with open(cache_file, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2)
    except:
        pass


def start_gui_game(ui: TerminalUI):
    """Start a new game with GUI"""
    ui.display_message("\n💡 Tips: Skriv 'ai1' eller 'ai2' som spillernavn for at spille mot AI")
    ui.display_message("   ai1 = Den Akademiske (probability strategi)")
    if 'ai2' in AI_STRATEGIES:
        ui.display_message("   ai2 = ML Master (DQN neural network)\n")
    else:
        ui.display_message("   ai2 = Not available (train DQN first)\n")
    
    player_names = ui.get_player_names()
    
    # Check for AI players and create strategy mapping
    ai_strategies = {}
    for name in player_names:
        strategy = get_ai_strategy(name)
        if strategy:
            ai_strategies[name] = strategy
    
    engine = GameEngine()
    engine.setup_game(player_names)
    
    # Start GUI
    gui = DiceGameGUI(engine, ai_strategies)
    gui.run()

def display_cached_results(ui: TerminalUI, data: dict, strategy_name: str):
    """Display cached or new simulation results"""
    ui.display_message("\n" + "="*50)
    ui.display_message("   RESULTAT AF 100 SIMULERINGER")
    ui.display_message("="*50)
    ui.display_message(f"\nStrategi: {strategy_name}")
    ui.display_message("\nANTAL SLAG:")
    ui.display_message(f"  - Gennemsnit: {data['avg_rolls']:.1f}")
    ui.display_message(f"  - Minimum: {data['min_rolls']}")
    ui.display_message(f"  - Maximum: {data['max_rolls']}")
    ui.display_message("\nANTAL TURE:")
    ui.display_message(f"  - Gennemsnit: {data['avg_turns']:.1f}")
    ui.display_message(f"  - Minimum: {data['min_turns']}")
    ui.display_message(f"  - Maximum: {data['max_turns']}")
    ui.display_message("="*50)


if __name__ == "__main__":
    main()
