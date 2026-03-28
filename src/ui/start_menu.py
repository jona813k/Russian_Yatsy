"""
Start menu GUI for Russian Yatsy
"""
import tkinter as tk
from tkinter import messagebox, simpledialog


class StartMenuGUI:
    """Start menu with buttons for all main options"""
    
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("Russian Yatsy")
        self.root.geometry("500x400")
        self.root.configure(bg='#f0f0f0')
        
        self.choice = None
        self.player_names = None
        
        self.create_menu()
    
    def create_menu(self):
        """Create the main menu"""
        # Title
        title_frame = tk.Frame(self.root, bg='#003366', pady=20)
        title_frame.pack(fill=tk.X)
        
        tk.Label(title_frame, text="🎲 RUSSIAN YATSY 🎲", 
                font=('Arial', 24, 'bold'), 
                bg='#003366', fg='white').pack()
        
        # Main content
        content_frame = tk.Frame(self.root, bg='#f0f0f0', pady=30)
        content_frame.pack(fill=tk.BOTH, expand=True)
        
        # Info text
        tk.Label(content_frame, 
                text="Vælg en mulighed:", 
                font=('Arial', 14, 'bold'),
                bg='#f0f0f0').pack(pady=(0, 20))
        
        # Buttons
        button_config = {
            'font': ('Arial', 12, 'bold'),
            'width': 30,
            'height': 2,
            'cursor': 'hand2'
        }
        
        tk.Button(content_frame, 
                 text="🎮 Spil i GUI", 
                 bg='#4CAF50', fg='white',
                 command=self.start_gui_game,
                 **button_config).pack(pady=5)
        
        tk.Button(content_frame, 
                 text="📊 Benchmark AI Strategier", 
                 bg='#2196F3', fg='white',
                 command=self.run_benchmark,
                 **button_config).pack(pady=5)
        
        tk.Button(content_frame, 
                 text="❌ Afslut", 
                 bg='#f44336', fg='white',
                 command=self.quit_app,
                 **button_config).pack(pady=5)
        
        # Footer
        footer_frame = tk.Frame(self.root, bg='#e0e0e0', pady=10)
        footer_frame.pack(fill=tk.X, side=tk.BOTTOM)
        
        tk.Label(footer_frame, 
                text="💡 Tip: Brug 'ai1' eller 'ai2' som spillernavn for AI modstandere", 
                font=('Arial', 9, 'italic'),
                bg='#e0e0e0', fg='#666').pack()
    
    def start_gui_game(self):
        """Start a GUI game"""
        self.choice = 'gui_game'
        
        # Get player names
        self.player_names = self.get_player_names_dialog()
        
        if self.player_names:
            self.root.destroy()
    
    def run_benchmark(self):
        """Run AI benchmark"""
        self.choice = 'benchmark'
        self.root.destroy()
    
    def quit_app(self):
        """Quit the application"""
        self.choice = 'quit'
        self.root.destroy()
    
    def get_player_names_dialog(self):
        """Dialog to get player names"""
        # Create dialog
        dialog = tk.Toplevel(self.root)
        dialog.title("Spiller Navne")
        dialog.geometry("400x350")
        dialog.configure(bg='#f0f0f0')
        dialog.transient(self.root)
        dialog.grab_set()
        
        # Center the dialog
        dialog.update_idletasks()
        x = (dialog.winfo_screenwidth() // 2) - (dialog.winfo_width() // 2)
        y = (dialog.winfo_screenheight() // 2) - (dialog.winfo_height() // 2)
        dialog.geometry(f"+{x}+{y}")
        
        tk.Label(dialog, 
                text="Indtast Spiller Navne", 
                font=('Arial', 14, 'bold'),
                bg='#f0f0f0').pack(pady=10)
        
        tk.Label(dialog, 
                text="Brug 'ai1' for Den Akademiske (probability)\nBrug 'ai2' for ML Master (DQN neural network)", 
                font=('Arial', 9, 'italic'),
                bg='#f0f0f0', fg='#666').pack(pady=5)
        
        # Entry fields
        entries = []
        for i in range(4):
            frame = tk.Frame(dialog, bg='#f0f0f0')
            frame.pack(pady=5)
            
            tk.Label(frame, 
                    text=f"Spiller {i+1}:", 
                    font=('Arial', 11),
                    bg='#f0f0f0', width=10).pack(side=tk.LEFT, padx=5)
            
            entry = tk.Entry(frame, font=('Arial', 11), width=20)
            entry.pack(side=tk.LEFT)
            entries.append(entry)
        
        # Focus first entry
        entries[0].focus()
        
        result = {'names': None}
        
        def on_ok():
            names = []
            for entry in entries:
                name = entry.get().strip()
                if name:
                    names.append(name)
            
            if len(names) < 1:
                messagebox.showerror("Fejl", "Du skal indtaste mindst én spiller!")
                return
            
            result['names'] = names
            dialog.destroy()
        
        def on_cancel():
            dialog.destroy()
        
        # Buttons
        button_frame = tk.Frame(dialog, bg='#f0f0f0')
        button_frame.pack(pady=20)
        
        tk.Button(button_frame, 
                 text="Start Spil", 
                 font=('Arial', 11, 'bold'),
                 bg='#4CAF50', fg='white',
                 command=on_ok,
                 width=12).pack(side=tk.LEFT, padx=5)
        
        tk.Button(button_frame, 
                 text="Annuller", 
                 font=('Arial', 11, 'bold'),
                 bg='#f44336', fg='white',
                 command=on_cancel,
                 width=12).pack(side=tk.LEFT, padx=5)
        
        # Bind Enter key
        dialog.bind('<Return>', lambda e: on_ok())
        dialog.bind('<Escape>', lambda e: on_cancel())
        
        # Wait for dialog
        dialog.wait_window()
        
        return result['names']
    
    def run(self):
        """Start the menu"""
        self.root.mainloop()
        return self.choice, self.player_names
