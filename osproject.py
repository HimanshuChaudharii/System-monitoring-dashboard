
import tkinter as tk
from tkinter import ttk, messagebox
import psutil
import platform
from datetime import datetime
from matplotlib.figure import Figure
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import GPUtil
import time
import threading

class LoadingScreen:
    def __init__(self, root):
        self.root = root
        self.root.title("System Monitor - Loading")
        self.label = ttk.Label(root, text="Loading System Monitor...", font=("Arial", 14))
        self.label.pack(pady=20)

root = tk.Tk()
app = LoadingScreen(root)
root.mainloop()
        
        # Center window
        window_width = 400
        window_height = 200
        screen_width = root.winfo_screenwidth()
        screen_height = root.winfo_screenheight()
        x = (screen_width - window_width) // 2
        y = (screen_height - window_height) // 2
        self.loading_window.geometry(f"{window_width}x{window_height}+{x}+{y}")
        
        # Styling
        self.loading_window.configure(bg='#1F1F1F')
        
        # App title
        self.loading_label = tk.Label(
            self.loading_window,
            text="System Monitor",
            font=('Segoe UI', 18, 'bold'),
            fg='white',
            bg='#1F1F1F'
        )
        self.loading_label.pack(pady=(40, 10))
        
        # Status message
        self.message_label = tk.Label(
            self.loading_window,
            text="Initializing...",
            font=('Segoe UI', 10),
            fg='lightgray',
            bg='#1F1F1F'
        )
        self.message_label.pack()
        
        # Custom progress bar
        self.style = ttk.Style()
        self.style.theme_use('clam')
        self.style.configure("Custom.Horizontal.TProgressbar",
                           background='#3C3C3C',
                           troughcolor='#252526')
        
        self.progress = ttk.Progressbar(
            self.loading_window,
            orient='horizontal',
            length=300,
            mode='determinate',
            style="Custom.Horizontal.TProgressbar"
        )
        self.progress.pack(pady=20)
        
        # Percentage
        self.percent_label = tk.Label(
            self.loading_window,
            text="0%",
            font=('Segoe UI', 10),
            fg='white',
            bg='#1F1F1F'
        )
        self.percent_label.pack()
        
        self.loading_window.attributes('-topmost', True)
        
    def update_progress(self, value, message):
        self.progress['value'] = value
        self.percent_label.config(text=f"{int(value)}%")
        self.message_label.config(text=message)
        self.loading_window.update_idletasks()
        
    def close(self):
        for i in range(5, 0, -1):
            self.loading_window.attributes('-alpha', i/5)
            time.sleep(0.05)
        self.loading_window.destroy()

class TaskManagerStyleMonitor:
    def __init__(self, root: tk.Tk):
        self.root = root
        self.root.withdraw()
        
        self.loading_screen = LoadingScreen(root)
        self.initialization_complete = False
        threading.Thread(target=self.initialize_app, daemon=True).start()
        self.check_initialization()
    
    def check_initialization(self):
        if self.initialization_complete:
            self.loading_screen.close()
            self.setup_main_app()
            self.root.deiconify()
        else:
            self.root.after(100, self.check_initialization)
    
    def initialize_app(self):
        tasks = [
            (10, "Loading system modules..."),
            (25, "Analyzing hardware..."),
            (40, "Initializing monitors..."),
            (60, "Scanning network..."),
            (75, "Preparing process manager..."),
            (90, "Finalizing UI..."),
            (100, "Ready!")
        ]
        
        for progress, message in tasks:
            time.sleep(0.3)
            self.loading_screen.update_progress(progress, message)
        
        self.initialization_complete = True

    def setup_main_app(self):
        self.root.title("System Monitor")
        self.setup_style()
        self.setup_main_window()
        self.running = True
        self.process_update_interval = 2000
        self.perf_update_interval = 1000
        self.init_data_structures()
        self.root.protocol("WM_DELETE_WINDOW", self.on_close)
        self.root.minsize(800, 600)
        self.sort_column = None
        self.sort_reverse = False

        self.cpu_percent = 0
        self.mem = psutil.virtual_memory()
        self.disk = psutil.disk_usage('/')
        self.net_up = 0
        self.net_down = 0
        
        self.root.after(1000, self.update_data)

    def setup_style(self):
        self.style = ttk.Style()
        self.style.theme_use('clam')
        self.style.configure(".", background='#1F1F1F', foreground='white')
        self.style.configure("TNotebook", background='#1F1F1F')
        self.style.configure("TNotebook.Tab", 
                           background='#2D2D2D', 
                           foreground='white',
                           padding=[12, 4],
                           font=('Segoe UI', 9, 'bold'))
        self.style.map("TNotebook.Tab", 
                     background=[("selected", '#3C3C3C'), ("active", '#373737')])
        self.style.configure("Treeview", 
                           background="#252526", 
                           fieldbackground="#252526", 
                           foreground="white",
                           rowheight=28,
                           borderwidth=0,
                           font=('Segoe UI', 9))
        self.style.configure("Treeview.Heading", 
                           background="#2D2D2D", 
                           foreground="white",
                           font=('Segoe UI', 9, 'bold'),
                           relief='flat')
        self.style.map("Treeview", 
                      background=[('selected', '#094771')],
                      foreground=[('selected', 'white')])

    def setup_main_window(self):
        self.notebook = ttk.Notebook(self.root)
        self.notebook.pack(fill=tk.BOTH, expand=True)

        # Processes Tab
        self.process_tab = ttk.Frame(self.notebook)
        self.setup_processes_tab()
        
        # Performance Tab
        self.perf_tab = ttk.Frame(self.notebook)
        self.setup_performance_tab()
        
        # System Details Tab
        self.sys_tab = ttk.Frame(self.notebook)
        self.setup_system_details_tab()
        
        self.notebook.add(self.process_tab, text="Processes")
        self.notebook.add(self.perf_tab, text="Performance")
        self.notebook.add(self.sys_tab, text="System Details")

    def setup_processes_tab(self):
        columns = {
            'name': ('Name', 280),
            'pid': ('PID', 80),
            'status': ('Status', 120),
            'cpu': ('CPU', 80),
            'memory': ('Memory', 100),
            'disk': ('Disk', 80),
            'network': ('Network', 100)
        }

        self.process_tree = ttk.Treeview(
            self.process_tab, 
            columns=tuple(columns.keys()),
            show='headings',
            selectmode='browse'
        )

        for col, (text, width) in columns.items():
            self.process_tree.heading(col, text=text, 
                                    command=lambda c=col: self.sort_processes(c))
            self.process_tree.column(col, width=width, 
                                    anchor=tk.CENTER if col != 'name' else tk.W)

        vsb = ttk.Scrollbar(self.process_tab, orient="vertical", 
                           command=self.process_tree.yview)
        hsb = ttk.Scrollbar(self.process_tab, orient="horizontal", 
                           command=self.process_tree.xview)
        self.process_tree.configure(yscrollcommand=vsb.set, xscrollcommand=hsb.set)

        self.process_tree.grid(row=0, column=0, sticky='nsew')
        vsb.grid(row=0, column=1, sticky='ns')
        hsb.grid(row=1, column=0, sticky='ew')
        self.process_tab.grid_columnconfigure(0, weight=1)
        self.process_tab.grid_rowconfigure(0, weight=1)

        self.context_menu = tk.Menu(self.root, tearoff=0, 
                                  bg='#252526', fg='white',
                                  activebackground='#094771',
                                  activeforeground='white')
        self.context_menu.add_command(label="End Task", command=self.end_process)
        self.process_tree.bind("<Button-3>", self.show_context_menu)

    def setup_performance_tab(self):
        self.perf_cards = {
            'CPU': self.create_perf_card(self.perf_tab, "CPU", '#1F77B4'),
            'Memory': self.create_perf_card(self.perf_tab, "Memory", '#2CA02C'),
            'Disk': self.create_perf_card(self.perf_tab, "Disk", '#9467BD'),
            'Network': self.create_perf_card(self.perf_tab, "Network", '#FF7F0E')
        }

        for i, card in enumerate(self.perf_cards.values()):
            card.grid(row=i//2, column=i%2, sticky='nsew', padx=10, pady=10)
            
        self.perf_tab.grid_columnconfigure(0, weight=1)
        self.perf_tab.grid_columnconfigure(1, weight=1)
        self.perf_tab.grid_rowconfigure(0, weight=1)
        self.perf_tab.grid_rowconfigure(1, weight=1)

    def setup_system_details_tab(self):
        main_frame = ttk.Frame(self.sys_tab)
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        canvas = tk.Canvas(main_frame, bg='#252526', highlightthickness=0)
        scrollbar = ttk.Scrollbar(main_frame, orient="vertical", command=canvas.yview)
        scrollable_frame = ttk.Frame(canvas)
        
        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(
                scrollregion=canvas.bbox("all")
            )
        )
        
        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        
        sys_info = self.get_system_info()
        
        for category, details in sys_info.items():
            header_frame = ttk.Frame(scrollable_frame)
            header_frame.pack(fill=tk.X, padx=10, pady=(10, 5))
            
            ttk.Label(
                header_frame, 
                text=category, 
                font=('Segoe UI', 10, 'bold'), 
                foreground='#4EC9B0',
                background='#252526'
            ).pack(side=tk.LEFT)
            
            details_frame = ttk.Frame(scrollable_frame)
            details_frame.pack(fill=tk.X, padx=10, pady=(0, 10))
            
            for i, (key, value) in enumerate(details.items()):
                ttk.Label(
                    details_frame,
                    text=f"{key}:",
                    font=('Segoe UI', 9),
                    foreground='#9CDCFE',
                    background='#252526'
                ).grid(row=i, column=0, sticky='e', padx=(0, 5), pady=2)
                
                ttk.Label(
                    details_frame,
                    text=value,
                    font=('Segoe UI', 9),
                    foreground='white',
                    background='#252526',
                    wraplength=400
                ).grid(row=i, column=1, sticky='w', padx=(0, 10), pady=2)
            
            details_frame.columnconfigure(0, weight=0)
            details_frame.columnconfigure(1, weight=1)

    def get_system_info(self):
        gpu_info = "Not detected"
        try:
            gpus = GPUtil.getGPUs()
            if gpus:
                gpu_info = f"{gpus[0].name} ({gpus[0].driver})"
        except:
            pass

        net_info = psutil.net_if_addrs()
        net_interfaces = []
        for interface, addrs in net_info.items():
            for addr in addrs:
                if addr.family == 2:  # AF_INET
                    net_interfaces.append(f"{interface}: {addr.address}")

        return {
            "Operating System": {
                "System": platform.system(),
                "Node Name": platform.node(),
                "Release": platform.release(),
                "Version": platform.version(),
                "Machine": platform.machine(),
                "Processor": platform.processor()
            },
            "Hardware Information": {
                "Physical Cores": str(psutil.cpu_count(logical=False)),
                "Total Cores": str(psutil.cpu_count(logical=True)),
                "Max Frequency": f"{psutil.cpu_freq().max:.2f} MHz",
                "Total RAM": f"{psutil.virtual_memory().total / (1024**3):.2f} GB",
                "GPU": gpu_info
            },
            "Boot Information": {
                "Boot Time": datetime.fromtimestamp(psutil.boot_time()).strftime("%Y-%m-%d %H:%M:%S"),
                "Up Time": str(datetime.now() - datetime.fromtimestamp(psutil.boot_time()))
            },
            "Network Information": {
                "Hostname": platform.node(),
                "IP Addresses": "\n".join(net_interfaces) if net_interfaces else "Not connected",
                "DNS": "\n".join([f"{conn.laddr.ip}:{conn.laddr.port}" for conn in psutil.net_connections(kind='inet') if conn.status == 'LISTEN'])
            },
            "Disk Information": {
                "Partitions": "\n".join([f"{part.device} ({part.mountpoint})" 
                                       for part in psutil.disk_partitions()]),
                "Total Space": f"{psutil.disk_usage('/').total / (1024**3):.2f} GB",
                "Used Space": f"{psutil.disk_usage('/').used / (1024**3):.2f} GB",
                "Free Space": f"{psutil.disk_usage('/').free / (1024**3):.2f} GB"
            }
        }

    def create_perf_card(self, parent, title, color):
        frame = ttk.Frame(parent)
        
        header = ttk.Frame(frame)
        header.pack(fill=tk.X, pady=(0, 5))
        ttk.Label(header, 
                 text=title, 
                 font=('Segoe UI', 10, 'bold'), 
                 foreground=color).pack(side=tk.LEFT)
        
        usage_frame = ttk.Frame(frame)
        usage_frame.pack(fill=tk.X, pady=(5, 0))
        
        frame.stats_label = ttk.Label(usage_frame, 
                                    text="0.0%", 
                                    font=('Segoe UI', 16, 'bold'),
                                    foreground=color)
        frame.stats_label.pack(side=tk.LEFT)
        
        fig = Figure(figsize=(5, 2), dpi=100, facecolor='#1F1F1F')
        ax = fig.add_subplot(111)
        ax.set_facecolor('#1F1F1F')
        ax.tick_params(axis='both', colors='white')
        [spine.set_color('#404040') for spine in ax.spines.values()]
        
        canvas = FigureCanvasTkAgg(fig, master=frame)
        canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)
        
        frame.detail_label = ttk.Label(frame, 
                                     text="", 
                                     font=('Segoe UI', 9),
                                     foreground='lightgray')
        frame.detail_label.pack(fill=tk.X, pady=(5, 0))
        
        frame._fig = fig
        frame._ax = ax
        frame._canvas = canvas
        frame._color = color
        
        return frame

    def init_data_structures(self):
        self.history = {
            'CPU': [],
            'Memory': [],
            'Disk': [],
            'Network_Up': [],
            'Network_Down': []
        }
        self.process_data = []
        self.net_io_last = psutil.net_io_counters()

    def update_data(self):
        if not self.running:
            return

        try:
            self.cpu_percent = psutil.cpu_percent()
            self.mem = psutil.virtual_memory()
            self.disk = psutil.disk_usage('/')
            net_io = psutil.net_io_counters()
            
            self.history['CPU'].append(self.cpu_percent)
            self.history['Memory'].append(self.mem.percent)
            self.history['Disk'].append(self.disk.percent)
            
            self.net_up = (net_io.bytes_sent - self.net_io_last.bytes_sent) / 1024
            self.net_down = (net_io.bytes_recv - self.net_io_last.bytes_recv) / 1024
            self.net_io_last = net_io
            self.history['Network_Up'].append(self.net_up)
            self.history['Network_Down'].append(self.net_down)

            for key in self.history:
                if len(self.history[key]) > 60:
                    self.history[key].pop(0)

            self.update_perf_graphs()
            
            if len(self.history['CPU']) % 5 == 0:
                self.update_process_list()

        except Exception as e:
            messagebox.showerror("Update Error", str(e))

        finally:
            self.root.after(self.perf_update_interval, self.update_data)

    def update_perf_graphs(self):
        for card_name, card in self.perf_cards.items():
            ax = card._ax
            ax.clear()
            
            if card_name == 'CPU':
                values = self.history['CPU']
                current_value = self.cpu_percent
                unit = '%'
                detail_text = f"Cores: {psutil.cpu_count()} | Usage: {current_value:.1f}%"
            elif card_name == 'Memory':
                values = self.history['Memory']
                current_value = self.mem.percent
                unit = '%'
                detail_text = f"Used: {self.mem.used//(1024**3)}GB / {self.mem.total//(1024**3)}GB | {current_value:.1f}%"
            elif card_name == 'Disk':
                values = self.history['Disk']
                current_value = self.disk.percent
                unit = '%'
                detail_text = f"Used: {self.disk.used//(1024**3)}GB / {self.disk.total//(1024**3)}GB | {current_value:.1f}%"
            elif card_name == 'Network':
                values = self.history['Network_Up']
                current_value = self.net_up
                unit = ' KB/s'
                detail_text = f"↑ {self.net_up:.1f} KB/s | ↓ {self.net_down:.1f} KB/s"
            
            color = card._color
            
            if values:
                ax.plot(values, color=color, linewidth=1.5, alpha=0.8)
                ax.fill_between(range(len(values)), values, color=color, alpha=0.2)
                
                ax.set_ylim(0, max(values) * 1.2 if max(values) > 0 else 100)
                ax.set_xticks([])
                ax.set_yticks([])
                
                card.stats_label.config(text=f"{current_value:.1f}{unit}")
                card.detail_label.config(text=detail_text)
            
            card._canvas.draw()

    def sort_processes(self, column):
        if self.sort_column == column:
            self.sort_reverse = not self.sort_reverse
        else:
            self.sort_column = column
            self.sort_reverse = False
            
        items = [(self.process_tree.set(child, column), child) 
                for child in self.process_tree.get_children('')]
        
        if column in ['cpu', 'memory', 'pid']:
            items.sort(key=lambda x: float(x[0].strip('%')) if '%' in x[0] else int(x[0]),
                      reverse=self.sort_reverse)
        else:
            items.sort(key=lambda x: x[0].lower(), reverse=self.sort_reverse)
        
        for col in self.process_tree['columns']:
            self.process_tree.heading(col, text=self.process_tree.heading(col)['text'].rstrip(' ↑↓'))
        self.process_tree.heading(column, 
                                text=f"{self.process_tree.heading(column)['text']} {'↓' if self.sort_reverse else '↑'}")
        
        for index, (_, child) in enumerate(items):
            self.process_tree.move(child, '', index)

    def update_process_list(self):
        current_processes = {}
        for proc in psutil.process_iter(['pid', 'name', 'status', 'cpu_percent', 'memory_percent']):
            try:
                current_processes[proc.info['pid']] = proc.info
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                continue

        for child in self.process_tree.get_children():
            pid = int(self.process_tree.item(child)['values'][1])
            if pid in current_processes:
                proc = current_processes[pid]
                self.process_tree.item(child, values=(
                    proc['name'], 
                    proc['pid'], 
                    proc['status'], 
                    f"{proc['cpu_percent']:.1f}%",
                    f"{proc['memory_percent']:.1f}%",
                    "0.0",
                    "0.0"
                ))
                del current_processes[pid]

        for pid, proc in current_processes.items():
            self.process_tree.insert('', 'end', values=(
                proc['name'], 
                proc['pid'], 
                proc['status'], 
                f"{proc['cpu_percent']:.1f}%",
                f"{proc['memory_percent']:.1f}%",
                "0.0", 
                "0.0"
            ))

    def show_context_menu(self, event):
        item = self.process_tree.identify_row(event.y)
        if item:
            self.process_tree.selection_set(item)
            self.context_menu.tk_popup(event.x_root, event.y_root)

    def end_process(self):
        selected = self.process_tree.selection()
        if selected:
            pid = int(self.process_tree.item(selected[0], 'values')[1])
            try:
                p = psutil.Process(pid)
                p.terminate()
            except Exception as e:
                messagebox.showerror("Error", f"Could not terminate process: {e}")

    def on_close(self):
        self.running = False
        self.root.destroy()

if __name__ == "__main__":
    root = tk.Tk()
    app = TaskManagerStyleMonitor(root)
    root.mainloop()