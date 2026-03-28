"""
GUI interface using tkinter
"""
import tkinter as tk
from tkinter import messagebox
from game.game_logic import GameEngine
from game.ai_strategy import ProbabilityStrategy
from game.rules import GameRules


class DiceGameGUI:
    """Graphical user interface for the dice game"""
    
    # Player colors - soft pastel colors
    PLAYER_COLORS = [
        '#FFD4A3',  # Soft orange
        '#A3D5FF',  # Light blue
        '#FFB3D9',  # Light pink
        '#FFFACD'   # Light yellow
    ]
    
    def __init__(self, engine: GameEngine, ai_strategies: dict = None):
        self.engine = engine
        self.ai_strategies = ai_strategies or {}
        self.root = tk.Tk()
        self.root.title("Russian Yatsy")
        self.root.geometry("900x600")
        self.root.configure(bg='#f0f0f0')
        
        # Assign colors to players
        self.player_colors = {}
        for i, player in enumerate(self.engine.state.players):
            self.player_colors[player.name] = self.PLAYER_COLORS[i % len(self.PLAYER_COLORS)]
        
        # Game state
        self.current_dice = []
        self.selected_dice = []
        self.dice_buttons = []
        self.selected_number = None
        self.turn_counter = 1  # Start at round 1
        self.turns_in_round = 0  # Track turns within current round (can be removed if not used)
        self.waiting_for_roll_confirm = False  # Flag to know if we're waiting for user to roll again
        self.showing_roll_result = False  # Flag to know if we're showing roll result before collecting
        
        # Store frames for background color updates
        self.main_frame = None
        self.left_frame = None
        self.right_frame = None
        self.collected_dice_frame = None  # Frame to show collected dice
        self.log_frame = None  # Store log frame for show/hide
        self.log_scroll_frame = None  # Store scroll frame for show/hide
        self.log_visible = True  # Track if log is visible
        
        # Game log tracking
        self.game_log = []
        self.log_text = None
        
        # Track all dice used in current turn for a number
        self.turn_dice_used = []  # List of dice values used this turn
        
        # Scoreboard cells for blinking animation
        self.last_progress = {player.name: dict(player.progress) for player in self.engine.state.players}
        
        # Create UI
        self.create_ui()
        self.update_display()
    
    def create_ui(self):
        """Create the user interface"""
        # Main container - more padding to show colored background
        self.main_frame = tk.Frame(self.root, bg='#f0f0f0')
        self.main_frame.pack(fill=tk.BOTH, expand=True, padx=25, pady=20)
        
        # Left side - Game area
        self.left_frame = tk.Frame(self.main_frame, bg='white', relief=tk.RIDGE, borderwidth=2)
        self.left_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 10))
        
        # Round counter at the top
        self.turn_label = tk.Label(self.left_frame, text="Runde: 1", 
                                   font=('Arial', 12, 'bold'), bg='#e0e0e0', fg='#333')
        self.turn_label.pack(fill=tk.X, pady=(0, 3))
        
        # Player info with color indicator
        player_info_frame = tk.Frame(self.left_frame, bg='white')
        player_info_frame.pack(pady=5)
        
        self.player_color_indicator = tk.Label(player_info_frame, text="  ", 
                                               font=('Arial', 14, 'bold'), bg='white',
                                               width=2, relief=tk.RAISED, borderwidth=2)
        self.player_color_indicator.pack(side=tk.LEFT, padx=(0, 8))
        
        self.player_label = tk.Label(player_info_frame, text="Aktiv spiller = Player", 
                                     font=('Arial', 14, 'bold'), bg='white')
        self.player_label.pack(side=tk.LEFT)
        
        # User choice display
        self.choice_label = tk.Label(self.left_frame, text="", 
                                     font=('Arial', 12), bg='white', fg='blue')
        self.choice_label.pack(pady=3)
        
        # Collected dice display section
        collected_section = tk.Frame(self.left_frame, bg='white')
        collected_section.pack(pady=5)
        
        self.collected_label = tk.Label(collected_section, text="Samlede terninger:", 
                                       font=('Arial', 10, 'bold'), bg='white')
        self.collected_label.pack(pady=(0, 3))
        self.collected_label.pack_forget()  # Hide initially
        
        self.collected_dice_frame = tk.Frame(collected_section, bg='#e8f5e9', 
                                            relief=tk.RIDGE, borderwidth=2, padx=5, pady=5)
        self.collected_dice_frame.pack()
        self.collected_dice_frame.pack_forget()  # Hide initially
        
        # Dice area
        dice_section = tk.Frame(self.left_frame, bg='white')
        dice_section.pack(pady=5)
        
        # Current dice label
        tk.Label(dice_section, text="Nuværende terninger:", 
                font=('Arial', 10, 'bold'), bg='white').pack(pady=(0, 3))
        
        self.dice_frame = tk.Frame(dice_section, bg='white')
        self.dice_frame.pack()
        
        # Action button
        self.action_button = tk.Button(self.left_frame, text="VÆLG OG RUL", 
                                       font=('Arial', 12, 'bold'), 
                                       bg='#003366', fg='white',
                                       command=self.handle_action,
                                       state=tk.DISABLED)
        self.action_button.pack(pady=5)
        
        # Status message - with white background box for visibility
        # Only shown when there's a message
        self.status_label = tk.Label(self.left_frame, text="", 
                                     font=('Arial', 11), bg='white', fg='black',
                                     wraplength=400, justify='center',
                                     relief=tk.RIDGE, borderwidth=2, padx=10, pady=8)
        # Don't pack it yet - will be shown when needed
        
        # Bind Enter key to action button
        self.root.bind('<Return>', lambda e: self.handle_action() if self.action_button['state'] == tk.NORMAL else None)
        
        # Middle - Game Log (with toggle button)
        self.log_frame = tk.Frame(self.main_frame, bg='white', relief=tk.RIDGE, borderwidth=2)
        self.log_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 10))
        
        # Log header with toggle button
        log_header_frame = tk.Frame(self.log_frame, bg='#e0e0e0')
        log_header_frame.pack(fill=tk.X)
        
        tk.Label(log_header_frame, text="Spilhistorik", 
                font=('Arial', 11, 'bold'), bg='#e0e0e0', fg='#333').pack(side=tk.LEFT, padx=5)
        
        self.toggle_log_button = tk.Button(log_header_frame, text="Skjul", 
                                          font=('Arial', 9), bg='#cccccc',
                                          command=self.toggle_log_visibility)
        self.toggle_log_button.pack(side=tk.RIGHT, padx=5, pady=2)
        
        # Scrollable text widget for log
        self.log_scroll_frame = tk.Frame(self.log_frame, bg='white')
        self.log_scroll_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        log_scrollbar = tk.Scrollbar(self.log_scroll_frame)
        log_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        self.log_text = tk.Text(self.log_scroll_frame, width=30, height=20, 
                               font=('Arial', 9), bg='#fafafa', 
                               state=tk.DISABLED, wrap=tk.WORD,
                               yscrollcommand=log_scrollbar.set)
        self.log_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        log_scrollbar.config(command=self.log_text.yview)
        
        # Configure text tags for colors
        self.log_text.tag_config('player', foreground='#0066cc', font=('Arial', 9, 'bold'))
        self.log_text.tag_config('number', foreground='#009900', font=('Arial', 9, 'bold'))
        self.log_text.tag_config('dice', foreground='#cc6600')
        self.log_text.tag_config('turn', foreground='#666666', font=('Arial', 9, 'italic'))
        self.log_text.tag_config('count', foreground='#9900cc', font=('Arial', 9, 'bold'))
        self.log_text.tag_config('completion', foreground='#ff6600', font=('Arial', 9, 'bold'))
        
        # Right side - Scoreboard
        self.right_frame = tk.Frame(self.main_frame, bg='white', relief=tk.RIDGE, borderwidth=2)
        self.right_frame.pack(side=tk.RIGHT, fill=tk.BOTH)
        
        # Scoreboard header
        header_frame = tk.Frame(self.right_frame, bg='white')
        header_frame.pack(pady=3)
        
        self.score_title = tk.Label(header_frame, text="Scoreboards", 
                                    font=('Arial', 12, 'bold'), bg='white')
        self.score_title.pack()
        
        self.score_frame = tk.Frame(self.right_frame, bg='white')
        self.score_frame.pack(padx=5, pady=5)
        
        # Create score grids (will be populated in update_scoreboard)
        self.score_cells = {}
    
    def add_log_entry(self, player_name, selected_number, dice_values, collected_count=None):
        """Add an entry to the game log"""
        self.log_text.config(state=tk.NORMAL)
        
        # Format the dice - show combinations for numbers 7-12
        if isinstance(dice_values, list) and len(dice_values) > 0:
            if selected_number > 6:
                # For 7-12, show pairs that sum to the number
                pairs = []
                temp_dice = list(dice_values)
                while len(temp_dice) >= 2:
                    d1 = temp_dice.pop(0)
                    # Find matching pair
                    for i, d2 in enumerate(temp_dice):
                        if d1 + d2 == selected_number:
                            pairs.append(f"{d1}+{d2}")
                            temp_dice.pop(i)
                            break
                dice_str = ', '.join(pairs) if pairs else ', '.join(str(d) for d in dice_values)
            else:
                # For 1-6, just show the values
                dice_str = ', '.join(str(d) for d in dice_values)
        else:
            dice_str = ''
        
        # Create more readable log entry
        self.log_text.insert(tk.END, f"Runde {self.turn_counter}: ", 'turn')
        self.log_text.insert(tk.END, f"{player_name}", 'player')
        self.log_text.insert(tk.END, " valgte tallet ")
        self.log_text.insert(tk.END, f"{selected_number}", 'number')
        
        if dice_str:
            self.log_text.insert(tk.END, " med terninger ")
            self.log_text.insert(tk.END, dice_str, 'dice')
        
        if collected_count is not None:
            self.log_text.insert(tk.END, f" → +{collected_count} samlet", 'count')
        
        self.log_text.insert(tk.END, "\n")
        
        self.log_text.config(state=tk.DISABLED)
        self.log_text.see(tk.END)  # Auto-scroll to bottom
    
    def add_completion_log(self, player_name, number):
        """Add a log entry when a number is completed"""
        self.log_text.config(state=tk.NORMAL)
        
        self.log_text.insert(tk.END, f"🎉 ", 'turn')
        self.log_text.insert(tk.END, f"{player_name}", 'player')
        self.log_text.insert(tk.END, " lukkede tallet ")
        self.log_text.insert(tk.END, f"{number}", 'number')
        self.log_text.insert(tk.END, " og får alle terninger tilbage!\n", 'completion')
        
        self.log_text.config(state=tk.DISABLED)
        self.log_text.see(tk.END)
    
    def toggle_log_visibility(self):
        """Toggle the visibility of the game log"""
        if self.log_visible:
            # Hide log
            self.log_scroll_frame.pack_forget()
            self.toggle_log_button.config(text="Vis")
            self.log_visible = False
        else:
            # Show log
            self.log_scroll_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
            self.toggle_log_button.config(text="Skjul")
            self.log_visible = True
    
    def update_background_color(self, player_name):
        """Update the background color based on current player"""
        color = self.player_colors.get(player_name, '#f0f0f0')
        self.root.configure(bg=color)
        self.main_frame.configure(bg=color)
    
    def update_collected_dice_display(self):
        """Update the display of collected dice"""
        # Clear existing collected dice
        for widget in self.collected_dice_frame.winfo_children():
            widget.destroy()
        
        if not self.turn_dice_used:
            # Hide if no dice collected
            self.collected_label.pack_forget()
            self.collected_dice_frame.pack_forget()
            return
        
        # Show collected dice
        self.collected_label.pack(pady=(0, 3))
        self.collected_dice_frame.pack()
        
        # Create small dice display for collected dice
        dice_row = tk.Frame(self.collected_dice_frame, bg='#e8f5e9')
        dice_row.pack()
        
        for die_val in self.turn_dice_used:
            canvas = tk.Canvas(dice_row, width=40, height=40, 
                             bg='#c8e6c9', highlightthickness=1,
                             highlightbackground='#4caf50')
            canvas.pack(side=tk.LEFT, padx=2)
            
            # Draw small die
            positions = {
                1: [(20, 20)],
                2: [(12, 12), (28, 28)],
                3: [(12, 12), (20, 20), (28, 28)],
                4: [(12, 12), (28, 12), (12, 28), (28, 28)],
                5: [(12, 12), (28, 12), (20, 20), (12, 28), (28, 28)],
                6: [(12, 10), (28, 10), (12, 20), (28, 20), (12, 30), (28, 30)]
            }
            
            for x, y in positions.get(die_val, []):
                canvas.create_oval(x-3, y-3, x+3, y+3, fill='black')
    
    def show_status_message(self, message):
        """Show status message and pack the label"""
        if message:
            self.status_label.config(text=message)
            self.status_label.pack(pady=5)
        else:
            self.status_label.pack_forget()
    
    def create_dice_display(self, dice_values):
        """Create clickable dice display"""
        # Clear existing dice
        for widget in self.dice_frame.winfo_children():
            widget.destroy()
        self.dice_buttons = []
        
        # Create 2 rows of 3 dice
        for row in range(2):
            row_frame = tk.Frame(self.dice_frame, bg='white')
            row_frame.pack()
            
            for col in range(3):
                idx = row * 3 + col
                if idx < len(dice_values):
                    value = dice_values[idx]
                    btn = tk.Canvas(row_frame, width=80, height=80, 
                                   bg='white', highlightthickness=2,
                                   highlightbackground='black')
                    btn.pack(side=tk.LEFT, padx=3, pady=3)
                    
                    # Draw dice
                    self.draw_die(btn, value)
                    
                    # Make clickable
                    btn.bind('<Button-1>', lambda e, i=idx: self.toggle_dice(i))
                    self.dice_buttons.append(btn)
    
    def draw_die(self, canvas, value):
        """Draw a die face on canvas"""
        # Die positions for dots
        positions = {
            1: [(40, 40)],
            2: [(25, 25), (55, 55)],
            3: [(25, 25), (40, 40), (55, 55)],
            4: [(25, 25), (55, 25), (25, 55), (55, 55)],
            5: [(25, 25), (55, 25), (40, 40), (25, 55), (55, 55)],
            6: [(25, 20), (55, 20), (25, 40), (55, 40), (25, 60), (55, 60)]
        }
        
        # Draw dots
        for x, y in positions.get(value, []):
            canvas.create_oval(x-5, y-5, x+5, y+5, fill='black')
    
    def toggle_dice(self, idx):
        """Toggle selection of a die"""
        if idx in self.selected_dice:
            # Deselect
            self.selected_dice.remove(idx)
            self.dice_buttons[idx].config(highlightbackground='black', highlightthickness=2)
        else:
            # Select
            self.selected_dice.append(idx)
            self.dice_buttons[idx].config(highlightbackground='blue', highlightthickness=4)
    
    def blink_updated_cells(self, player_name, number):
        """Blink the updated scoreboard cells green"""
        if (player_name, number) not in self.score_cells:
            return
        
        cells = self.score_cells[(player_name, number)]
        current_count = self.engine.state.players[self.get_player_index(player_name)].progress.get(number, 0)
        
        # Blink only the newly added cells
        if current_count > 0:
            # Determine which cells were just added
            previous_count = self.last_progress[player_name].get(number, 0)
            newly_added = list(range(previous_count, current_count))
            
            # Blink animation: 1 cycle - flash white then back to green
            def blink_cycle(cycle):
                if cycle >= 2:  # Stop after 1 full cycle (white->green)
                    return
                
                if cycle == 0:
                    # First flash - make white
                    color = '#ffffff'
                else:
                    # Second step - back to green
                    color = '#00ff00'
                
                for idx in newly_added:
                    if idx < len(cells):
                        cells[idx].config(bg=color)
                
                # Toggle color after 150ms
                self.root.after(150, lambda: blink_cycle(cycle + 1))
            
            blink_cycle(0)
    
    def get_player_index(self, player_name):
        """Get the index of a player by name"""
        for i, player in enumerate(self.engine.state.players):
            if player.name == player_name:
                return i
        return 0
    
    def update_scoreboard(self, highlight_player=None, highlight_number=None):
        """Update the scoreboard display - show all players"""
        # Clear existing
        for widget in self.score_frame.winfo_children():
            widget.destroy()
        self.score_cells = {}
        
        current_player = self.engine.state.get_current_player()
        players = self.engine.state.players
        
        # Show all players (up to 4)
        for player_idx, player in enumerate(players[:4]):
            # Player name header with highlight if active
            bg_color = '#ffff99' if player == current_player else 'white'
            name_label = tk.Label(self.score_frame, text=player.name, 
                                 font=('Arial', 10, 'bold'), 
                                 bg=bg_color, relief=tk.RAISED if player == current_player else tk.FLAT,
                                 borderwidth=2)
            # Øg afstand mellem spillere - column spacing ændret fra 7 til 8
            col_offset = 1 + player_idx * 8
            name_label.grid(row=0, column=col_offset, columnspan=6, sticky='ew', pady=(0, 5))
            
            # Add vertical separator line after each player (except the last)
            if player_idx < len(players[:4]) - 1:
                separator = tk.Frame(self.score_frame, width=2, bg='#666666')
                separator.grid(row=0, column=col_offset + 7, rowspan=14, sticky='ns', padx=3)
        
        # Create grid (12 rows for numbers)
        for num in range(1, 13):
            # Number label
            tk.Label(self.score_frame, text=str(num), 
                    font=('Arial', 9, 'bold'), 
                    width=2, bg='white').grid(row=num, column=0, sticky='w', padx=(0, 5))
            
            # Show each player's progress for this number
            for player_idx, player in enumerate(players[:4]):
                count = player.progress.get(num, 0)
                col_offset = 1 + player_idx * 8
                # Create exactly 6 boxes for this player and this number
                cells_for_this_num = []
                for box_idx in range(6):
                    color = '#00ff00' if box_idx < count else '#ff0000'
                    cell = tk.Label(self.score_frame, bg=color, 
                                   width=1, height=1, relief=tk.RAISED)
                    cell.grid(row=num, column=col_offset + box_idx, padx=1, pady=1)
                    cells_for_this_num.append(cell)
                
                # Store cells for blinking animation
                self.score_cells[(player.name, num)] = cells_for_this_num
        
        # Add total score under each player
        for player_idx, player in enumerate(players[:4]):
            total_collected = sum(player.progress.values())
            col_offset = 1 + player_idx * 8
            total_label = tk.Label(self.score_frame, text=f"{total_collected}/72", 
                                  font=('Arial', 9, 'bold'), 
                                  bg='white', fg='#0066cc')
            total_label.grid(row=13, column=col_offset, columnspan=6, pady=(5, 0))
        
        # Trigger blinking animation if specified
        if highlight_player and highlight_number:
            self.root.after(100, lambda: self.blink_updated_cells(highlight_player, highlight_number))
    
    def handle_action(self):
        """Handle the action button click"""
        # Check button text first before getting current player
        button_text = self.action_button.cget('text')
        
        # Check if button is in "SEND TUR VIDERE" or "AFSLUT TUR" mode
        if button_text == "AFSLUT TUR" or button_text == "SEND TUR VIDERE":
            self.end_turn()
            return
        
        current_player = self.engine.state.get_current_player()
        
        # Check if this is AI turn
        if current_player.name in self.ai_strategies:
            self.play_ai_turn()
            return
        
        # Check if we're showing roll result and waiting for user to accept
        if self.showing_roll_result:
            self.showing_roll_result = False
            self.collect_matching_dice()
            return
        
        # Check if we're waiting for user to roll again
        if self.waiting_for_roll_confirm:
            self.waiting_for_roll_confirm = False
            self.roll_remaining_dice()
            return
        
        if not self.selected_number:
            # First roll - user needs to select a number
            self.select_number_from_dice()
        else:
            # This shouldn't happen in new flow
            self.continue_turn()
    
    def select_number_from_dice(self):
        """Let user select which number to collect"""
        current_player = self.engine.state.get_current_player()
        
        # Get unique values from selected dice
        if not self.selected_dice:
            messagebox.showwarning("Ingen valg", "Vælg venligst mindst én terning!")
            return
        
        # Prevent selecting more than 2 dice
        if len(self.selected_dice) > 2:
            messagebox.showerror("For mange terninger", 
                               f"Du har valgt {len(self.selected_dice)} terninger!\n\n"
                               "Du kan kun vælge 1 eller 2 terninger ad gangen.\n\n"
                               "Klik på terningerne for at fravælge nogle.")
            return
        
        # Calculate what number the selected dice represent
        selected_values = [self.current_dice[i] for i in self.selected_dice]
        
        # Check if only 1 die selected
        if len(selected_values) == 1:
            target = selected_values[0]
        elif len(selected_values) == 2:
            # Two dice - sum them to make any number 2-12
            # Examples: 2+2=4, 2+3=5, 6+6=12
            target = sum(selected_values)
            
            # Validate that sum is within valid range (2-12)
            if target < 2 or target > 12:
                messagebox.showerror("Ugyldigt valg", 
                                   f"To terninger giver {target}, men kun 2-12 er gyldige tal!")
                return
        else:
            messagebox.showerror("Ugyldigt valg", "Vælg 1 eller 2 terninger!")
            return
        
        # Verify this is valid
        # DON'T call engine.select_dice yet - it would collect ALL matching dice!
        # Just verify the number is valid and set it
        
        # First check: is this number available?
        current_player = self.engine.state.get_current_player()
        if current_player.progress.get(target, 0) >= 6:
            # Check if there are ANY other valid choices with current dice
            can_choose_other = False
            for test_num in range(1, 13):
                if test_num != target and current_player.progress.get(test_num, 0) < 6:
                    if self.can_make_number(self.current_dice, test_num):
                        can_choose_other = True
                        break
            
            if can_choose_other:
                messagebox.showwarning("Ugyldigt valg", 
                    f"Du har allerede samlet 6 × {target}!\n\n"
                    f"Fravælg terningerne og prøv et andet tal.")
            else:
                # No other valid choices - offer to skip turn
                result = messagebox.askyesno("Ingen gyldige valg", 
                    f"Du har allerede samlet 6 × {target}!\n\n"
                    f"Der er ingen andre gyldige valg med disse terninger.\n\n"
                    f"Vil du afslutte din tur?")
                if result:
                    self.end_turn()
            return
        
        # Manually count what was selected
        selected_values = [self.current_dice[i] for i in self.selected_dice]
        
        # Count based on how many dice were selected, not on target value
        # If 1 die selected: it's a single (count = 1)
        # If 2 dice selected: it's a combination (count = 1 if they sum to target)
        if len(selected_values) == 1:
            # Single die - count is always 1
            count = 1
        elif len(selected_values) == 2:
            # Two dice - verify they sum to target, then count = 1
            if selected_values[0] + selected_values[1] == target:
                count = 1
            else:
                count = 0
        else:
            count = 0
        
        if count == 0:
            messagebox.showerror("Ugyldigt valg", f"De valgte terninger kan ikke lave {target}!")
            return
        
        # Set the selected number and let engine collect ALL matching dice
        self.engine.state.selected_number = target
        self.selected_number = target
        self.choice_label.config(text=f"Bruger valg = *{target}*")
        
        # Save current dice to compare after collection
        dice_before = list(self.current_dice)
        
        # Call engine to collect ALL matching dice (both singles and combinations)
        success, total_count, message, completed = self.engine.select_dice(target)
        
        if not success:
            messagebox.showerror("Fejl", message)
            return
        
        # Track which dice were collected by comparing before and after
        if total_count > 0:
            # Calculate which dice were removed
            dice_after = list(self.engine.state.dice_values)
            collected_values = []
            
            # Find dice that were in dice_before but not in dice_after
            remaining = list(dice_after)
            for die in dice_before:
                if die in remaining:
                    remaining.remove(die)
                else:
                    collected_values.append(die)
            
            # Track all dice used in this turn
            self.turn_dice_used.extend(collected_values)
            
            # Log entry with all dice used so far
            self.add_log_entry(current_player.name, target, list(self.turn_dice_used), total_count)
        
        # Update collected dice display
        self.update_collected_dice_display()
        
        self.selected_dice = []
        
        # Update last_progress and trigger blinking
        self.last_progress[current_player.name] = dict(current_player.progress)
        
        # Check if completed
        if completed:
            self.handle_number_completion()
            return
        
        # Update scoreboard
        self.update_scoreboard(current_player.name, target)
        
        # Check if we have more dice to roll
        if self.engine.state.num_dice_in_hand > 0:
            # Automatically roll the remaining dice (don't wait for user)
            self.roll_remaining_dice()
        else:
            # No more dice - end turn
            self.end_turn()
    
    def continue_turn(self):
        """Continue the turn with remaining dice - kept for compatibility"""
        self.roll_remaining_dice()
    
    def roll_remaining_dice(self):
        """Roll the remaining dice and SHOW them to user without collecting yet"""
        if self.engine.state.num_dice_in_hand == 0:
            self.end_turn()
            return
        
        # Roll the dice first (always show them!)
        from game.game_logic import roll_dice
        new_dice = roll_dice(self.engine.state.num_dice_in_hand)
        self.engine.state.dice_values = new_dice
        
        self.current_dice = new_dice
        self.selected_dice = []
        
        # Create dice display
        self.create_dice_display(new_dice)
        
        # Find matching dice but DON'T select them in engine yet
        matching_indices = self.get_matching_dice_indices(new_dice, self.selected_number)
        
        # Check if there are any matches
        if not matching_indices:
            # No matches - end turn
            self.show_status_message(f"Ingen {self.selected_number}'ere! Din tur er slut.")
            self.action_button.config(text="AFSLUT TUR", bg='#cc0000', state=tk.NORMAL)
            self.showing_roll_result = False
            return
        
        # Highlight matching dice with YELLOW border to show what will be collected
        for idx in matching_indices:
            self.dice_buttons[idx].config(highlightbackground='#FFD700', highlightthickness=4)
        
        # Show how many will be collected
        self.show_status_message(f"Du slog {len(matching_indices)} terninger der matcher {self.selected_number}. Klik for at samle dem.")
        
        # Change button to "SAML TERNINGER" and wait for user
        self.action_button.config(text="SAML TERNINGER", bg='#009900', state=tk.NORMAL)
        self.showing_roll_result = True
    
    def collect_matching_dice(self):
        """Collect the matching dice that were shown in roll_remaining_dice"""
        # Find matching dice again
        matching_indices = self.get_matching_dice_indices(self.current_dice, self.selected_number)
        
        # Change highlight to green to show they're being collected
        for idx in matching_indices:
            self.dice_buttons[idx].config(highlightbackground='#00ff00', highlightthickness=4)
        
        # Update the engine state with matches
        success, count, message, completed = self.engine.select_dice(self.selected_number)
        
        # Add to game log for continued roll with actual dice values
        current_player = self.engine.state.get_current_player()
        if count > 0:
            matching_values = [self.current_dice[i] for i in matching_indices]
            
            # Track all dice used in this turn
            self.turn_dice_used.extend(matching_values)
            
            # Log entry with all dice used so far
            self.add_log_entry(current_player.name, self.selected_number, list(self.turn_dice_used), count)
            
            # Update collected dice display
            self.update_collected_dice_display()
        
        # Update scoreboard with blinking
        if count > 0:
            self.update_scoreboard(current_player.name, self.selected_number)
            self.last_progress[current_player.name] = dict(current_player.progress)
        
        self.show_status_message("")
        
        if completed:
            self.handle_number_completion()
            return
        
        # Check if we have more dice
        if self.engine.state.num_dice_in_hand > 0:
            # Automatically roll remaining dice to continue
            self.showing_roll_result = False
            self.roll_remaining_dice()
        else:
            # No more dice - end turn
            self.end_turn()
    
    def can_make_number(self, dice_values, target):
        """Check if target number can be made with current dice (singles OR combinations)"""
        # Use engine's helper method for consistency
        return self.engine._can_make_number(dice_values, target)
    
    def get_matching_dice_indices(self, dice_values, target):
        """Get indices of dice that match the target number (both singles and combinations)"""
        matching = []
        used = set()
        
        # First find all singles (only for 1-6)
        if target <= 6:
            for i, val in enumerate(dice_values):
                if val == target:
                    matching.append(i)
                    used.add(i)
        
        # Then find all combinations (for ALL targets 2-12)
        if target >= 2:
            for i, val1 in enumerate(dice_values):
                if i in used:
                    continue
                for j, val2 in enumerate(dice_values):
                    if j <= i or j in used:
                        continue
                    if val1 + val2 == target:
                        matching.append(i)
                        matching.append(j)
                        used.add(i)
                        used.add(j)
                        break
        
        return matching
    
    def check_for_valid_choices(self, dice_values, player):
        """Check if there are any valid numbers the player can choose from these dice"""
        # Get numbers that player still needs (not completed)
        needed_numbers = [num for num in range(1, 13) if player.progress.get(num, 0) < 6]
        
        # Check if any needed number can be made from the dice
        for number in needed_numbers:
            # Check for singles (only for 1-6)
            if number <= 6 and number in dice_values:
                return True
            
            # Check for combinations using find_valid_combinations (for all numbers)
            from game.rules import GameRules
            combinations = GameRules.find_valid_combinations(dice_values, number)
            if combinations:
                return True
        
        return False
    
    def handle_number_completion(self):
        """Handle when a number is completed"""
        current_player = self.engine.state.get_current_player()
        
        # Add completion log entry
        self.add_completion_log(current_player.name, self.selected_number)
        
        self.show_status_message(f"🎉 Tillykke! Du har samlet 6 × {self.selected_number}! Alle terninger returneres!")
        
        # Reset for new round
        self.engine.state.num_dice_in_hand = 6
        self.engine.state.selected_number = None
        self.engine.state.collected_this_turn = 0
        self.selected_number = None
        self.choice_label.config(text="")
        self.waiting_for_roll_confirm = False
        self.showing_roll_result = False
        
        # Clear turn dice tracking
        self.turn_dice_used = []
        
        # Hide collected dice display
        self.update_collected_dice_display()
        
        # Update scoreboard to show completion
        self.update_scoreboard()
        
        # Clear status after a moment and start new turn
        self.root.after(2000, lambda: self.show_status_message(""))
        self.root.after(2000, self.start_turn)
    
    def handle_game_end(self, winner):
        """Handle game end with winner announcement"""
        # Calculate game stats
        stats = []
        for player in self.engine.state.players:
            total_collected = sum(player.progress.values())
            stats.append(f"{player.name}: {total_collected}/72 tal samlet")
        
        stats_text = "\n".join(stats)
        
        # Create custom dialog with option to continue
        dialog = tk.Toplevel(self.root)
        dialog.title("🎉 SPILLET SLUT! 🎉")
        dialog.geometry("400x300")
        dialog.configure(bg='#f0f0f0')
        dialog.transient(self.root)
        dialog.grab_set()
        
        # Winner message
        message_frame = tk.Frame(dialog, bg='#f0f0f0')
        message_frame.pack(pady=20, padx=20, fill=tk.BOTH, expand=True)
        
        if isinstance(winner, list):
            winner_names = ", ".join([p.name for p in winner])
            title_text = "UAFGJORT!"
            winner_text = f"{winner_names}\nhar alle vundet!"
        else:
            title_text = "SEJR!"
            winner_text = f"{winner.name} har vundet!"
        
        tk.Label(message_frame, text=title_text, font=('Arial', 18, 'bold'), 
                bg='#f0f0f0', fg='#003366').pack(pady=5)
        tk.Label(message_frame, text=winner_text, font=('Arial', 14), 
                bg='#f0f0f0').pack(pady=5)
        tk.Label(message_frame, text="\nFinal status:", font=('Arial', 12, 'bold'), 
                bg='#f0f0f0').pack(pady=5)
        tk.Label(message_frame, text=stats_text, font=('Arial', 10), 
                bg='#f0f0f0', justify=tk.LEFT).pack(pady=5)
        
        # Buttons
        button_frame = tk.Frame(dialog, bg='#f0f0f0')
        button_frame.pack(pady=10)
        
        def continue_playing():
            dialog.destroy()
            # Don't quit - just continue the game
            self.start_turn()
        
        def end_game():
            dialog.destroy()
            self.root.quit()
        
        tk.Button(button_frame, text="Fortsæt spillet", font=('Arial', 11, 'bold'),
                 bg='#00aa00', fg='white', command=continue_playing,
                 padx=10, pady=5).pack(side=tk.LEFT, padx=5)
        
        tk.Button(button_frame, text="Afslut", font=('Arial', 11, 'bold'),
                 bg='#cc0000', fg='white', command=end_game,
                 padx=10, pady=5).pack(side=tk.LEFT, padx=5)
    
    def end_turn(self):
        """End the current turn"""
        # Store previous player index before end_turn changes it
        prev_player_index = self.engine.state.current_player_index
        num_players = len(self.engine.state.players)
        
        winner, bonus_turn = self.engine.end_turn()
        
        if winner:
            self.handle_game_end(winner)
            return
        
        if bonus_turn:
            self.show_status_message("🎉 Bonus! Alle terninger brugt! Du får en ekstra tur!")
            self.root.after(2000, lambda: self.show_status_message(""))
        else:
            self.show_status_message("")
            # Only increment round counter when we complete a full round (all players have played)
            # If we just moved from last player back to first player (and it's not a bonus)
            current_player_index = self.engine.state.current_player_index
            if prev_player_index == num_players - 1 and current_player_index == 0:
                self.turn_counter += 1
        
        self.selected_number = None
        self.choice_label.config(text="")
        self.action_button.config(text="VÆLG OG RUL", bg='#0066cc')
        
        # Don't call next_player here - engine.end_turn() already did it
        self.start_turn()
    
    def start_turn(self):
        """Start a new turn"""
        current_player = self.engine.state.get_current_player()
        self.player_label.config(text=f"Aktiv spiller = {current_player.name}")
        
        # Update color indicator and background
        player_color = self.player_colors[current_player.name]
        self.player_color_indicator.config(bg=player_color)
        self.update_background_color(current_player.name)
        
        # Clear turn dice tracking for new turn
        self.turn_dice_used = []
        self.waiting_for_roll_confirm = False
        self.showing_roll_result = False
        
        # Hide collected dice display
        self.update_collected_dice_display()
        
        self.show_status_message("")
        self.action_button.config(text="VÆLG OG RUL", bg='#003366')
        
        # Update round display
        self.turn_label.config(text=f"Runde: {self.turn_counter}")
        
        # Check if AI player
        if current_player.name in self.ai_strategies:
            self.action_button.config(state=tk.DISABLED)
            self.root.after(500, self.play_ai_turn)
        else:
            # Roll dice
            dice = self.engine.start_turn()
            self.current_dice = dice
            self.selected_dice = []
            
            self.create_dice_display(dice)
            self.update_scoreboard()
            
            # Check if player has any valid choices
            if not self.check_for_valid_choices(dice, current_player):
                # No valid choices - end turn immediately
                self.show_status_message("Øv! Du har ingen terninger der matcher de tal du mangler. Turen går videre.")
                self.action_button.config(text="SEND TUR VIDERE", bg='#003366', state=tk.NORMAL)
                # Disable dice clicking
                for btn in self.dice_buttons:
                    btn.unbind('<Button-1>')
            else:
                self.action_button.config(state=tk.NORMAL)
    
    def play_ai_turn(self):
        """Play a full turn for AI"""
        current_player = self.engine.state.get_current_player()
        strategy = self.ai_strategies[current_player.name]
        
        # Roll and show dice to user
        dice = self.engine.start_turn()
        self.current_dice = dice
        self.create_dice_display(dice)
        self.update_scoreboard()
        self.root.update()
        
        # Wait a bit so user can see the dice
        self.root.after(800, lambda: self.ai_select_and_continue(dice, strategy, current_player))
    
    def ai_select_and_continue(self, dice, strategy, current_player):
        """AI selects number and highlights dice"""
        # Check if AI has any valid choices
        has_valid_choices = self.check_for_valid_choices(dice, current_player)
        if not has_valid_choices:
            # No valid choices - show message and end turn
            self.show_status_message(f"{current_player.name} har ingen gyldige valg - tur slut!")
            self.root.update()
            
            # End turn properly
            winner, bonus_turn = self.engine.end_turn()
            if winner:
                self.root.after(1500, lambda: self.handle_game_end(winner))
                return
            
            # Wait and start next turn
            self.root.after(1500, self.start_turn)
            return
        
        selected_number = strategy.select_number(dice, current_player.progress)
        
        # Verify that the selected number can actually be made with current dice
        if not self.can_make_number(dice, selected_number):
            # AI selected a number it can't make - this shouldn't happen but handle it
            self.show_status_message(f"{current_player.name} kan ikke lave {selected_number} - tur slut!")
            self.root.update()
            
            winner, bonus_turn = self.engine.end_turn()
            if winner:
                self.root.after(1500, lambda: self.handle_game_end(winner))
                return
            
            self.root.after(1500, self.start_turn)
            return
        
        # AI has valid choice - show it
        self.show_status_message(f"{current_player.name} vælger {selected_number}")
        self.choice_label.config(text=f"AI valg = *{selected_number}*")
        
        # Highlight the dice AI is selecting
        matching_indices = self.get_matching_dice_indices(dice, selected_number)
        for idx in matching_indices:
            self.dice_buttons[idx].config(highlightbackground='#00ff00', highlightthickness=4)
        
        self.root.update()
        
        # Wait so user can see what AI selected
        self.root.after(800, lambda: self.ai_execute_selection(selected_number))
    
    def ai_execute_selection(self, selected_number):
        """Execute AI's selection"""
        current_player = self.engine.state.get_current_player()
        success, count, message, completed = self.engine.select_dice(selected_number)
        
        # Add to game log with actual dice values
        if success and count > 0:
            matching_indices = self.get_matching_dice_indices(self.current_dice, selected_number)
            matching_values = [self.current_dice[i] for i in matching_indices]
            
            # Track all dice used in this turn
            self.turn_dice_used.extend(matching_values)
            
            # Log entry with all dice used so far
            self.add_log_entry(current_player.name, selected_number, list(self.turn_dice_used), count)
        
        # Update scoreboard with blinking
        if success and count > 0:
            self.update_scoreboard(current_player.name, selected_number)
            self.last_progress[current_player.name] = dict(current_player.progress)
        else:
            self.update_scoreboard()
        self.root.update()
        
        if not success:
            winner, bonus_turn = self.engine.end_turn()
            if winner:
                self.handle_game_end(winner)
                return
            # Don't call next_player - engine.end_turn() already did it
            self.root.after(1000, self.start_turn)
            return
        
        if completed:
            self.root.after(500, self.ai_handle_completion)
            return
        
        # Continue rolling
        self.root.after(500, lambda: self.ai_continue_turn(selected_number))
    
    def ai_continue_turn(self, selected_number):
        """Continue AI turn"""
        if self.engine.state.num_dice_in_hand == 0:
            self.check_ai_turn_end()
            return
            
        can_continue, new_dice, msg = self.engine.continue_rolling()
        
        if not can_continue:
            self.check_ai_turn_end()
            return
        
        # Show new dice
        self.current_dice = new_dice
        self.create_dice_display(new_dice)
        self.root.update()
        
        # Wait so user can see the dice
        self.root.after(800, lambda: self.ai_continue_select(new_dice, selected_number))
    
    def ai_continue_select(self, dice, selected_number):
        """AI selects from continued roll"""
        # Verify that the selected number can be made with current dice
        if not self.can_make_number(dice, selected_number):
            # No matching dice - end turn
            self.check_ai_turn_end()
            return
        
        # Highlight matching dice
        matching_indices = self.get_matching_dice_indices(dice, selected_number)
        for idx in matching_indices:
            self.dice_buttons[idx].config(highlightbackground='#00ff00', highlightthickness=4)
        
        self.root.update()
        
        # Wait and execute selection
        self.root.after(800, lambda: self.ai_execute_continue(selected_number))
    
    def ai_execute_continue(self, selected_number):
        """Execute AI's continued selection"""
        current_player = self.engine.state.get_current_player()
        success, count, message, completed = self.engine.select_dice(selected_number)
        
        # Add to game log with actual dice values
        if success and count > 0:
            matching_indices = self.get_matching_dice_indices(self.current_dice, selected_number)
            matching_values = [self.current_dice[i] for i in matching_indices]
            
            # Track all dice used in this turn
            self.turn_dice_used.extend(matching_values)
            
            # Log entry with all dice used so far
            self.add_log_entry(current_player.name, selected_number, list(self.turn_dice_used), count)
        
        # Update scoreboard with blinking
        if success and count > 0:
            self.update_scoreboard(current_player.name, selected_number)
            self.last_progress[current_player.name] = dict(current_player.progress)
        else:
            self.update_scoreboard()
        self.root.update()
        
        if completed:
            self.root.after(500, self.ai_handle_completion)
            return
        
        # Continue if more dice
        self.root.after(500, lambda: self.ai_continue_turn(selected_number))
    
    def ai_handle_completion(self):
        """Handle AI completing a number"""
        current_player = self.engine.state.get_current_player()
        
        # Add completion log entry
        self.add_completion_log(current_player.name, self.engine.state.selected_number)
        
        self.engine.state.num_dice_in_hand = 6
        self.engine.state.selected_number = None
        self.engine.state.collected_this_turn = 0
        self.choice_label.config(text="")
        
        # Clear turn dice tracking
        self.turn_dice_used = []
        
        # Continue AI turn
        self.root.after(500, self.play_ai_turn)
    
    def check_ai_turn_end(self):
        """Check if AI turn should end"""
        # Use the main end_turn() method to ensure round counting works
        self.end_turn()
    
    def update_display(self):
        """Update all display elements"""
        self.update_scoreboard()
        self.start_turn()
    
    def run(self):
        """Start the GUI"""
        self.root.mainloop()
