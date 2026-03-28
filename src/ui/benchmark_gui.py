"""
Benchmark GUI for comparing AI strategies
"""
import tkinter as tk
from tkinter import ttk
import threading


class BenchmarkGUI:
    """GUI for running and displaying AI benchmark results"""
    
    def __init__(self, run_callback, show_cached_callback):
        """
        Args:
            run_callback: Function that runs the benchmark and yields progress updates
            show_cached_callback: Function that shows cached results and yields updates
        """
        self.root = tk.Tk()
        self.root.title("AI Strategi Sammenligning")
        self.root.geometry("800x600")
        self.root.configure(bg='#f0f0f0')
        
        self.run_callback = run_callback
        self.show_cached_callback = show_cached_callback
        self.is_running = False
        
        self.create_ui()
        
        # Automatically load stats on startup
        self.root.after(100, self.show_cached_stats)
    
    def create_ui(self):
        """Create the benchmark UI"""
        # Header
        header_frame = tk.Frame(self.root, bg='#003366', pady=15)
        header_frame.pack(fill=tk.X)
        
        tk.Label(header_frame, 
                text="🎯 SAMMENLIGNING AF AI STRATEGIER - 1000 SPIL", 
                font=('Arial', 18, 'bold'),
                bg='#003366', fg='white').pack()
        
        # Close button at top
        button_frame = tk.Frame(self.root, bg='#f0f0f0', pady=15)
        button_frame.pack(fill=tk.X)
        
        # Center the button
        button_inner_frame = tk.Frame(button_frame, bg='#f0f0f0')
        button_inner_frame.pack(expand=True)
        
        self.close_button = tk.Button(button_inner_frame, 
                                      text="❌ Luk", 
                                      font=('Arial', 14, 'bold'),
                                      bg='#f44336', fg='white',
                                      command=self.close,
                                      width=20, height=2)
        self.close_button.pack()
        
        # Content area
        content_frame = tk.Frame(self.root, bg='#f0f0f0')
        content_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)
        
        # Progress section
        progress_frame = tk.Frame(content_frame, bg='white', relief=tk.RIDGE, borderwidth=2)
        progress_frame.pack(fill=tk.X, pady=(0, 20), padx=15, ipady=15, ipadx=15)
        
        self.status_label = tk.Label(progress_frame, 
                                     text="Vælg en handling...", 
                                     font=('Arial', 12, 'bold'),
                                     bg='white')
        self.status_label.pack(pady=(0, 10))
        
        self.progress_bar = ttk.Progressbar(progress_frame, 
                                           length=700, 
                                           mode='determinate')
        self.progress_bar.pack(pady=(0, 5))
        
        self.progress_label = tk.Label(progress_frame, 
                                       text="", 
                                       font=('Arial', 10),
                                       bg='white')
        self.progress_label.pack()
        
        # Results section
        results_frame = tk.Frame(content_frame, bg='white', relief=tk.RIDGE, borderwidth=2)
        results_frame.pack(fill=tk.BOTH, expand=True, padx=15, ipady=15, ipadx=15)
        
        tk.Label(results_frame, 
                text="Resultater:", 
                font=('Arial', 14, 'bold'),
                bg='white').pack(anchor='w', pady=(0, 10))
        
        # Table for results - simplified to show only turns
        table_frame = tk.Frame(results_frame, bg='white')
        table_frame.pack(fill=tk.BOTH, expand=True)
        
        # Create Treeview (table) with only 2 columns
        columns = ('strategy', 'avg_turns')
        self.results_table = ttk.Treeview(table_frame, columns=columns, show='headings', height=10)
        
        # Define headings
        self.results_table.heading('strategy', text='AI Strategi')
        self.results_table.heading('avg_turns', text='Gennemsnitlige Ture')
        
        # Define column widths
        self.results_table.column('strategy', width=400, anchor='w')
        self.results_table.column('avg_turns', width=250, anchor='center')
        
        # Add scrollbar
        scrollbar = ttk.Scrollbar(table_frame, orient=tk.VERTICAL, command=self.results_table.yview)
        self.results_table.configure(yscroll=scrollbar.set)
        
        self.results_table.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Style for alternating row colors
        style = ttk.Style()
        style.configure('Treeview', rowheight=35, font=('Arial', 12))
        style.configure('Treeview.Heading', font=('Arial', 13, 'bold'))
    
    def show_cached_stats(self):
        """Show cached statistics"""
        if self.is_running:
            return
        
        self.is_running = True
        self.clear_results()
        self.progress_bar['value'] = 0
        self.progress_label.config(text="")
        
        # Run in separate thread
        thread = threading.Thread(target=self.show_cached_thread)
        thread.daemon = True
        thread.start()
    
    def show_cached_thread(self):
        """Show cached results thread"""
        try:
            for update in self.show_cached_callback():
                if 'status' in update:
                    self.root.after(0, lambda s=update['status']: self.update_status(s))
                
                if 'result' in update:
                    result = update['result']
                    self.root.after(0, lambda r=result: self.add_result(r))
                
                if 'complete' in update:
                    self.root.after(0, self.operation_complete)
                
                if 'error' in update:
                    self.root.after(0, lambda e=update['error']: self.show_error(e))
        except Exception as e:
            self.root.after(0, lambda: self.show_error(str(e)))
    
    def update_status(self, status):
        """Update status label"""
        self.status_label.config(text=status)
    
    def update_progress(self, progress):
        """Update progress bar"""
        current, total = progress
        percentage = (current / total * 100) if total > 0 else 0
        self.progress_bar['value'] = percentage
        self.progress_label.config(text=f"{current} / {total} spil gennemført")
    
    def add_result(self, result_data):
        """Add result to table - simplified to show only turns"""
        if isinstance(result_data, dict):
            # Extract data from dict
            strategy = result_data.get('strategy', '')
            avg_turns = result_data.get('avg_turns', 0)
            
            # Format values - just strategy name and turns
            values = (
                strategy,
                f"{avg_turns:.1f} ture"
            )
            
            self.results_table.insert('', tk.END, values=values)
    
    def clear_results(self):
        """Clear all results from table"""
        for item in self.results_table.get_children():
            self.results_table.delete(item)
    
    def operation_complete(self):
        """Called when operation is complete"""
        self.is_running = False
        self.enable_buttons()
        self.status_label.config(text="✅ Færdig!")
        self.progress_label.config(text="")
    
    def show_error(self, error):
        """Show error message"""
        self.is_running = False
        self.status_label.config(text=f"❌ Fejl: {error}")
        self.progress_label.config(text="")
    
    def close(self):
        """Close the window"""
        self.root.destroy()
    
    def run(self):
        """Start the GUI"""
        self.root.mainloop()
