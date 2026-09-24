import tkinter as tk
from tkinter import ttk, messagebox
import docker
import psutil
import threading
import time
from PIL import Image, ImageTk
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg

class DockerMicroserviceGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("MicroMesh Vizier - Docker Microservice Manager")
        self.root.geometry("1200x800")
        self.root.configure(bg='#2e2e2e')
        
        # Docker client
        self.docker_client = docker.from_env()
        self.running_containers = []
        self.update_interval = 5  # seconds
        
        # Dark mode aesthetics
        self.bg_color = '#2e2e2e'
        self.fg_color = '#ffffff'
        self.accent_color = '#4e8cff'
        self.error_color = '#ff6b6b'
        self.success_color = '#6bff6b'
        
        # Main frame
        self.main_frame = tk.Frame(root, bg=self.bg_color)
        self.main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Header
        self.header_frame = tk.Frame(self.main_frame, bg=self.bg_color)
        self.header_frame.pack(fill=tk.X, padx=10, pady=10)
        
        self.title_label = tk.Label(self.header_frame, text="MicroMesh Vizier", 
                                  font=('Helvetica', 24, 'bold'), 
                                  fg=self.accent_color, bg=self.bg_color)
        self.title_label.pack(side=tk.LEFT)
        
        self.status_label = tk.Label(self.header_frame, text="Connected to Docker", 
                                    font=('Helvetica', 10), 
                                    fg=self.success_color, bg=self.bg_color)
        self.status_label.pack(side=tk.RIGHT)
        
        # Split view
        self.split_frame = tk.Frame(self.main_frame, bg=self.bg_color)
        self.split_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
        
        # Left panel - Service List
        self.list_frame = tk.Frame(self.split_frame, bg=self.bg_color, width=300, 
                                  relief=tk.RAISED, borderwidth=1)
        self.list_frame.pack(side=tk.LEFT, fill=tk.Y, padx=(0, 5))
        self.list_frame.pack_propagate(False)
        
        self.list_header = tk.Label(self.list_frame, text="Running Services", 
                                   font=('Helvetica', 12, 'bold'), 
                                   fg=self.fg_color, bg=self.bg_color)
        self.list_header.pack(fill=tk.X, pady=(0, 10))
        
        self.tree = ttk.Treeview(self.list_frame, columns=('status', 'name', 'id'), 
                               show='headings', selectmode='browse')
        self.tree.heading('status', text='Status')
        self.tree.heading('name', text='Name')
        self.tree.heading('id', text='ID')
        self.tree.column('status', width=80, anchor=tk.CENTER)
        self.tree.column('name', width=150)
        self.tree.column('id', width=120)
        self.tree.pack(fill=tk.BOTH, expand=True)
        
        # Control buttons
        self.control_frame = tk.Frame(self.list_frame, bg=self.bg_color)
        self.control_frame.pack(fill=tk.X, pady=(10, 0))
        
        self.start_btn = tk.Button(self.control_frame, text="Start", bg=self.accent_color, 
                                 fg=self.fg_color, command=self.start_container)
        self.start_btn.pack(side=tk.LEFT, expand=True, fill=tk.X, padx=2)
        
        self.stop_btn = tk.Button(self.control_frame, text="Stop", bg=self.error_color, 
                                fg=self.fg_color, command=self.stop_container)
        self.stop_btn.pack(side=tk.LEFT, expand=True, fill=tk.X, padx=2)
        
        self.restart_btn = tk.Button(self.control_frame, text="Restart", bg=self.accent_color, 
                                   fg=self.fg_color, command=self.restart_container)
        self.restart_btn.pack(side=tk.LEFT, expand=True, fill=tk.X, padx=2)
        
        # Right panel - Details and Visualizations
        self.detail_frame = tk.Frame(self.split_frame, bg=self.bg_color, 
                                    relief=tk.RAISED, borderwidth=1)
        self.detail_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        # Service details
        self.detail_header = tk.Label(self.detail_frame, text="Service Details", 
                                    font=('Helvetica', 12, 'bold'), 
                                    fg=self.fg_color, bg=self.bg_color)
        self.detail_header.pack(fill=tk.X, pady=(0, 10))
        
        self.detail_text = tk.Text(self.detail_frame, bg='#3e3e3e', fg=self.fg_color, 
                                  insertbackground=self.fg_color, wrap=tk.WORD)
        self.detail_text.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Tabbed view for metrics and logs
        self.tab_parent = ttk.Notebook(self.detail_frame)
        
        # Metrics tab
        self.metrics_tab = ttk.Frame(self.tab_parent)
        self.tab_parent.add(self.metrics_tab, text='Metrics')
        
        self.cpu_frame = tk.Frame(self.metrics_tab, bg=self.bg_color)
        self.cpu_frame.pack(fill=tk.BOTH, expand=True, pady=5)
        
        self.cpu_label = tk.Label(self.cpu_frame, text="CPU Usage", 
                                 font=('Helvetica', 10, 'bold'), 
                                 fg=self.fg_color, bg=self.bg_color)
        self.cpu_label.pack()
        
        self.fig_cpu = plt.Figure(figsize=(5, 2), dpi=100)
        self.ax_cpu = self.fig_cpu.add_subplot(111)
        self.canvas_cpu = FigureCanvasTkAgg(self.fig_cpu, master=self.cpu_frame)
        self.canvas_cpu.draw()
        self.canvas_cpu.get_tk_widget().pack(fill=tk.BOTH, expand=True)
        
        self.mem_frame = tk.Frame(self.metrics_tab, bg=self.bg_color)
        self.mem_frame.pack(fill=tk.BOTH, expand=True, pady=5)
        
        self.mem_label = tk.Label(self.mem_frame, text="Memory Usage", 
                                 font=('Helvetica', 10, 'bold'), 
                                 fg=self.fg_color, bg=self.bg_color)
        self.mem_label.pack()
        
        self.fig_mem = plt.Figure(figsize=(5, 2), dpi=100)
        self.ax_mem = self.fig_mem.add_subplot(111)
        self.canvas_mem = FigureCanvasTkAgg(self.fig_mem, master=self.mem_frame)
        self.canvas_mem.draw()
        self.canvas_mem.get_tk_widget().pack(fill=tk.BOTH, expand=True)
        
        # Logs tab
        self.logs_tab = ttk.Frame(self.tab_parent)
        self.tab_parent.add(self.logs_tab, text='Logs')
        
        self.logs_text = tk.Text(self.logs_tab, bg='#3e3e3e', fg=self.fg_color, 
                                insertbackground=self.fg_color, wrap=tk.WORD)
        self.logs_text.pack(fill=tk.BOTH, expand=True)
        
        self.tab_parent.pack(fill=tk.BOTH, expand=True)
        
        # Footer with refresh control
        self.footer_frame = tk.Frame(self.main_frame, bg=self.bg_color, height=40)
        self.footer_frame.pack(fill=tk.X, pady=(5, 10))
        
        self.refresh_btn = tk.Button(self.footer_frame, text="Refresh", 
                                   bg=self.accent_color, fg=self.fg_color, 
                                   command=self.refresh_containers)
        self.refresh_btn.pack(side=tk.LEFT, padx=10)
        
        self.auto_refresh = tk.BooleanVar(value=True)
        self.auto_chk = tk.Checkbutton(self.footer_frame, text="Auto-refresh every 5s", 
                                      variable=self.auto_refresh, 
                                      bg=self.bg_color, fg=self.fg_color, 
                                      selectcolor=self.bg_color)
        self.auto_chk.pack(side=tk.LEFT)
        
        # Initialize and start monitoring
        self.refresh_containers()
        self.monitor_thread = threading.Thread(target=self.monitor_resources, daemon=True)
        self.monitor_thread.start()
        
        # Bind tree selection event
        self.tree.bind('<<TreeviewSelect>>', self.show_container_details)
    
    def refresh_containers(self):
        try:
            current_selection = None
            if self.tree.selection():
                current_selection = self.tree.item(self.tree.selection())['values'][1]
            
            self.tree.delete(*self.tree.get_children())
            self.running_containers = self.docker_client.containers.list(all=True)
            
            for container in self.running_containers:
                status = container.status
                status_color = self.success_color if status == 'running' else self.error_color
                
                self.tree.insert('', 'end', values=(status, container.name, container.short_id))
                
                if current_selection and container.name == current_selection:
                    self.tree.selection_set(self.tree.get_children()[-1])
            
            if not self.tree.selection() and self.running_containers:
                self.tree.selection_set(self.tree.get_children()[0])
                self.show_container_details()
            
            self.status_label.config(text="Connected to Docker", fg=self.success_color)
        except Exception as e:
            self.status_label.config(text=f"Error: {str(e)}", fg=self.error_color)
    
    def show_container_details(self, event=None):
        if not self.tree.selection():
            return
            
        selected_item = self.tree.item(self.tree.selection())
        container_name = selected_item['values'][1]
        
        for container in self.running_containers:
            if container.name == container_name:
                details = f"Name: {container.name}\n"
                details += f"ID: {container.id}\n"
                details += f"Status: {container.status}\n"
                details += f"Image: {container.image.tags[0] if container.image.tags else 'N/A'}\n"
                details += f"Created: {container.attrs['Created']}\n"
                details += f"Ports: {', '.join(container.ports) if container.ports else 'None'}\n"
                
                # Try to get environment variables
                try:
                    env_vars = container.attrs['Config']['Env']
                    details += "\nEnvironment Variables:\n"
                    details += "\n".join([f"  {var}" for var in env_vars[:5]])
                    if len(env_vars) > 5:
                        details += f"\n  ... and {len(env_vars)-5} more"
                except:
                    pass
                
                self.detail_text.configure(state='normal')
                self.detail_text.delete(1.0, tk.END)
                self.detail_text.insert(tk.END, details)
                self.detail_text.configure(state='disabled')
                
                # Update logs
                self.update_container_logs(container)
                break
    
    def update_container_logs(self, container):
        try:
            logs = container.logs(tail=50).decode('utf-8')
            self.logs_text.configure(state='normal')
            self.logs_text.delete(1.0, tk.END)
            self.logs_text.insert(tk.END, logs)
            self.logs_text.configure(state='disabled')
        except Exception as e:
            self.logs_text.configure(state='normal')
            self.logs_text.delete(1.0, tk.END)
            self.logs_text.insert(tk.END, f"Error fetching logs: {str(e)}")
            self.logs_text.configure(state='disabled')
    
    def start_container(self):
        if not self.tree.selection():
            return
        
        selected_item = self.tree.item(self.tree.selection())
        container_name = selected_item['values'][1]
        
        try:
            for container in self.running_containers:
                if container.name == container_name:
                    if container.status == 'running':
                        messagebox.showinfo("Info", f"Container {container_name} is already running")
                        return
                    
                    container.start()
                    messagebox.showinfo("Success", f"Container {container_name} started successfully")
                    self.refresh_containers()
                    return
            
            messagebox.showerror("Error", f"Container {container_name} not found")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to start container: {str(e)}")
    
    def stop_container(self):
        if not self.tree.selection():
            return
        
        selected_item = self.tree.item(self.tree.selection())
        container_name = selected_item['values'][1]
        
        try:
            for container in self.running_containers:
                if container.name == container_name:
                    if container.status != 'running':
                        messagebox.showinfo("Info", f"Container {container_name} is not running")
                        return
                    
                    container.stop()
                    messagebox.showinfo("Success", f"Container {container_name} stopped successfully")
                    self.refresh_containers()
                    return
            
            messagebox.showerror("Error", f"Container {container_name} not found")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to stop container: {str(e)}")
    
    def restart_container(self):
        if not self.tree.selection():
            return
        
        selected_item = self.tree.item(self.tree.selection())
        container_name = selected_item['values'][1]
        
        try:
            for container in self.running_containers:
                if container.name == container_name:
                    if container.status != 'running':
                        messagebox.showinfo("Info", f"Container {container_name} is not running. Starting it instead.")
                        container.start()
                    else:
                        container.restart()
                    
                    messagebox.showinfo("Success", f"Container {container_name} restarted successfully")
                    self.refresh_containers()
                    return
            
            messagebox.showerror("Error", f"Container {container_name} not found")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to restart container: {str(e)}")
    
    def monitor_resources(self):
        self.cpu_data = [0] * 30
        self.mem_data = [0] * 30
        
        while True:
            if not self.auto_refresh.get():
                time.sleep(1)
                continue
                
            try:
                if not self.running_containers:
                    self.ax_cpu.clear()
                    self.ax_mem.clear()
                    self.canvas_cpu.draw()
                    self.canvas_mem.draw()
                    time.sleep(self.update_interval)
                    continue
                
                if self.tree.selection():
                    selected_item = self.tree.item(self.tree.selection())
                    container_name = selected_item['values'][1]
                    
                    for container in self.running_containers:
                        if container.name == container_name:
                            stats = container.stats(stream=False)
                            
                            # CPU usage
                            cpu_delta = stats['cpu_stats']['cpu_usage']['total_usage'] - stats['precpu_stats']['cpu_usage']['total_usage']
                            system_delta = stats['cpu_stats']['system_cpu_usage'] - stats['precpu_stats']['system_cpu_usage']
                            cpu_usage = (cpu_delta / system_delta) * stats['cpu_stats']['online_cpus'] * 100
                            
                            # Memory usage
                            mem_usage = stats['memory_stats']['usage'] / (1024 * 1024)  # MB
                            
                            # Update data
                            self.cpu_data.pop(0)
                            self.cpu_data.append(cpu_usage)
                            
                            self.mem_data.pop(0)
                            self.mem_data.append(mem_usage)
                            
                            # Update CPU chart
                            self.ax_cpu.clear()
                            self.ax_cpu.plot(range(len(self.cpu_data)), self.cpu_data, color=self.accent_color)
                            self.ax_cpu.set_ylim(0, 100)
                            self.ax_cpu.set_ylabel('CPU %')
                            self.ax_cpu.grid(True, alpha=0.3)
                            self.fig_cpu.set_facecolor('#3e3e3e')
                            self.ax_cpu.set_facecolor('#3e3e3e')
                            self.ax_cpu.tick_params(colors=self.fg_color)
                            self.ax_cpu.xaxis.label.set_color(self.fg_color)
                            self.ax_cpu.yaxis.label.set_color(self.fg_color)
                            
                            # Update memory chart
                            self.ax_mem.clear()
                            self.ax_mem.plot(range(len(self.mem_data)), self.mem_data, color=self.accent_color)
                            self.ax_mem.set_ylim(0, max(self.mem_data) * 1.2 if max(self.mem_data) > 0 else 100)
                            self.ax_mem.set_ylabel('Memory (MB)')
                            self.ax_mem.grid(True, alpha=0.3)
                            self.fig_mem.set_facecolor('#3e3e3e')
                            self.ax_mem.set_facecolor('#3e3e3e')
                            self.ax_mem.tick_params(colors=self.fg_color)
                            self.ax_mem.xaxis.label.set_color(self.fg_color)
                            self.ax_mem.yaxis.label.set_color(self.fg_color)
                            
                            # Redraw
                            self.canvas_cpu.draw()
                            self.canvas_mem.draw()
                            break
                
                if self.auto_refresh.get():
                    self.refresh_containers()
                
                time.sleep(self.update_interval)
            except Exception as e:
                print(f"Monitoring error: {str(e)}")
                time.sleep(self.update_interval)

if __name__ == "__main__":
    try:
        root = tk.Tk()
        style = ttk.Style(root)
        style.theme_use('clam')
        
        # Configure style for dark mode
        style.configure('.', background='#3e3e3e', foreground='white', fieldbackground='#3e3e3e')
        style.map('Treeview', background=[('selected', '#4e8cff')])
        style.map('TNotebook.Tab', background=[('selected', '#3e3e3e')], foreground=[('selected', 'white')])
        
        app = DockerMicroserviceGUI(root)
        root.mainloop()
    except Exception as e:
        print(f"Application error: {str(e)}")