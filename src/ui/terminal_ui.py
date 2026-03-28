"""
Terminal-based user interface
"""
from ui.renderer import DiceRenderer


class TerminalUI:
    """Handles terminal input/output"""
    
    def __init__(self):
        self.renderer = DiceRenderer()
    
    def display_welcome(self):
        """Display welcome message"""
        print("\n" + "="*50)
        print("   RUSSIAN YATSY")
        print("="*50)
        print("\nMål: Samle 6 af hvert tal (1-12)")
        print("\nRegler:")
        print("  - Vælg et tal (1-12)")
        print("  - Tag alle terninger der matcher (enkelt + kombinationer)")
        print("  - Fortsæt med at slå resterende terninger")
        print("  - Få 6 af et tal: Alle terninger returneres!")
        print("  - Brug alle 6 terninger: Få en ekstra tur!")
        print("  - Skriv 'q' for at afslutte spillet")
        print("="*50)
    
    def display_menu(self):
        """Display main menu"""
        print("\n=== Menu ===")
        print("1. Start Nyt Spil (Terminal)")
        print("2. Start Nyt Spil (GUI)")
        print("3. Sammenlign AI strategier (1000 spil)")
        print("4. Afslut")
    
    def get_player_names(self) -> list:
        """Get player names from input"""
        num_players = self.get_number_input("Antal spillere (2-4): ", 2, 4)
        names = []
        for i in range(num_players):
            name = input(f"Spiller {i+1} navn: ").strip()
            names.append(name if name else f"Spiller {i+1}")
        return names
    
    def display_dice(self, dice_values: list):
        """Display dice using ASCII art"""
        print("\n" + self.renderer.render_dice(dice_values))
    
    def display_player_progress(self, players: list):
        """Display all players' progress with green background for completed numbers"""
        GREEN_BG = "\033[42m\033[30m"  # Green background, black text
        RESET = "\033[0m"
        
        print("\n" + "="*70)
        print("STILLING:")
        print("="*70)
        for i, player in enumerate(players):
            print(f"\n{player.name}:")
            # Display 1-6
            progress_str = "  1-6:  "
            for num in range(1, 7):
                count = player.progress[num]
                if count >= 6:
                    progress_str += f"{GREEN_BG}{num}:6/6{RESET}  "
                else:
                    progress_str += f"{num}:{count}/6  "
            print(progress_str)
            # Display 7-12
            progress_str = "  7-12: "
            for num in range(7, 13):
                count = player.progress[num]
                if count >= 6:
                    progress_str += f"{GREEN_BG}{num}:6/6{RESET}  "
                else:
                    progress_str += f"{num}:{count}/6  "
            print(progress_str)
            print(f"  Total: {player.get_total_collected()}/72")
            # Add separator between players (but not after the last one)
            if i < len(players) - 1:
                print("  " + "-"*66)
        print("="*70)
    
    def get_number_input(self, prompt: str, min_val: int = 1, max_val: int = 12):
        """Get a number input from user. Returns int or 'quit' string"""
        while True:
            user_input = input(prompt).strip().lower()
            if user_input == 'q':
                return 'quit'
            try:
                value = int(user_input)
                if min_val <= value <= max_val:
                    return value
                print(f"Indtast et tal mellem {min_val} og {max_val}")
            except ValueError:
                print("Ugyldigt input. Indtast et tal eller 'q' for at afslutte.")
    
    def get_yes_no(self, prompt: str):
        """Get yes/no input from user. Returns bool or 'quit' string"""
        while True:
            response = input(prompt + " (j/n): ").lower().strip()
            if response == 'q':
                return 'quit'
            if response in ['j', 'ja', 'y', 'yes']:
                return True
            elif response in ['n', 'nej', 'no']:
                return False
            print("Indtast 'j' eller 'n' (eller 'q' for at afslutte)")
    
    def display_message(self, message: str):
        """Display a message to the player"""
        print(message)
    
    def display_turn_header(self, player_name: str):
        """Display turn header"""
        print("\n" + "="*50)
        print(f"   {player_name}'s tur")
        print("="*50)
