import tkinter as tk
from tkinter import ttk

class STPSimulator(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Spanning Tree Protocol (STP) GUI Simulator")
        self.geometry("800x650")
        self.configure(padx=20, pady=20)

        # Base node data
        self.macs = {'A': 1000, 'B': 2000, 'C': 3000, 'D': 4000}
        
        # UI Variables
        self.prio_vars = {
            'A': tk.IntVar(value=32768),
            'B': tk.IntVar(value=32768),
            'C': tk.IntVar(value=32768),
            'D': tk.IntVar(value=32768)
        }
        
        self.cost_vars = {
            ('A', 'B'): tk.IntVar(value=19),
            ('A', 'C'): tk.IntVar(value=19),
            ('C', 'B'): tk.IntVar(value=19),
            ('B', 'D'): tk.IntVar(value=19),
            ('C', 'D'): tk.IntVar(value=19)
        }

        self.setup_ui()
        self.update_simulation()

    def setup_ui(self):
        # Top Frame for Status
        self.status_label = tk.Label(self, text="Root Bridge: Calculating...", font=("Helvetica", 14, "bold"))
        self.status_label.pack(pady=10)

        # Canvas for Drawing Topology
        self.canvas = tk.Canvas(self, width=600, height=350, bg="white", highlightthickness=1, highlightbackground="black")
        self.canvas.pack(pady=10)
        
        # Node Coordinates
        self.coords = {
            'A': (300, 50),
            'C': (150, 175),
            'B': (450, 175),
            'D': (300, 300)
        }

        # Bottom Frame for Controls
        control_frame = tk.Frame(self)
        control_frame.pack(fill=tk.X, pady=10)

        # Priority Controls
        prio_frame = tk.LabelFrame(control_frame, text="Bridge Priorities (0 - 61440, Step 4096)")
        prio_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=5)
        
        for idx, node in enumerate(['A', 'C', 'B', 'D']):
            f = tk.Frame(prio_frame)
            f.pack(fill=tk.X, pady=2)
            tk.Label(f, text=f"Switch {node}:", width=8).pack(side=tk.LEFT)
            s = tk.Scale(f, from_=0, to=61440, resolution=4096, orient=tk.HORIZONTAL, 
                         variable=self.prio_vars[node], command=self.on_change)
            s.pack(side=tk.LEFT, fill=tk.X, expand=True)

        # Cost Controls
        cost_frame = tk.LabelFrame(control_frame, text="Link Path Costs")
        cost_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True, padx=5)
        
        for idx, link in enumerate(self.cost_vars.keys()):
            f = tk.Frame(cost_frame)
            f.pack(fill=tk.X, pady=2)
            tk.Label(f, text=f"Link {link[0]}-{link[1]}:", width=10).pack(side=tk.LEFT)
            e = tk.Entry(f, textvariable=self.cost_vars[link], width=10)
            e.pack(side=tk.LEFT)
            e.bind('<KeyRelease>', self.on_change)

    def on_change(self, *args):
        self.update_simulation()

    def run_stp_logic(self):
        # 1. Build Switch Data
        switches = {n: {'priority': self.prio_vars[n].get(), 'mac': self.macs[n]} for n in ['A', 'B', 'C', 'D']}
        
        # Validate costs, default to 19 if empty/invalid
        links = []
        for (u, v), var in self.cost_vars.items():
            try:
                cost = var.get()
                if cost < 1: cost = 1
            except tk.TclError:
                cost = 19 
            links.append((u, v, cost))

        # 2. Elect Root Bridge (Lowest Priority, then Lowest MAC)
        root_bridge = min(switches.keys(), key=lambda k: (switches[k]['priority'], switches[k]['mac']))
        
        # 3. Calculate Shortest Paths
        root_path_cost = {s: float('inf') for s in switches}
        root_path_cost[root_bridge] = 0
        upstream_switch = {s: None for s in switches}

        for _ in range(len(switches) - 1):
            for u, v, cost in links:
                # Check u -> v
                if root_path_cost[u] + cost < root_path_cost[v]:
                    root_path_cost[v] = root_path_cost[u] + cost
                    upstream_switch[v] = u
                elif root_path_cost[u] + cost == root_path_cost[v] and u != upstream_switch[v]:
                    curr_up = upstream_switch[v]
                    if curr_up:
                        if (switches[u]['priority'], switches[u]['mac']) < (switches[curr_up]['priority'], switches[curr_up]['mac']):
                            upstream_switch[v] = u
                
                # Check v -> u
                if root_path_cost[v] + cost < root_path_cost[u]:
                    root_path_cost[u] = root_path_cost[v] + cost
                    upstream_switch[u] = v
                elif root_path_cost[v] + cost == root_path_cost[u] and v != upstream_switch[u]:
                    curr_up = upstream_switch[u]
                    if curr_up:
                        if (switches[v]['priority'], switches[v]['mac']) < (switches[curr_up]['priority'], switches[curr_up]['mac']):
                            upstream_switch[u] = v

        # 4. Assign Port Roles
        port_roles = {}
        for u, v, cost in links:
            port_roles[(u, v)] = {}
            u_claim = (root_path_cost[u], switches[u]['priority'], switches[u]['mac'])
            v_claim = (root_path_cost[v], switches[v]['priority'], switches[v]['mac'])
            
            if u_claim < v_claim:
                designated, other = u, v
            else:
                designated, other = v, u
                
            port_roles[(u, v)][designated] = 'DP'
            
            if upstream_switch[other] == designated:
                port_roles[(u, v)][other] = 'RP'
            else:
                port_roles[(u, v)][other] = 'BLK'

        return root_bridge, switches, root_path_cost, port_roles, links

    def update_simulation(self):
        try:
            root_bridge, switches, root_path_cost, port_roles, links = self.run_stp_logic()
        except Exception as e:
            return # Ignore errors mid-typing in cost boxes

        self.canvas.delete("all")

        # Update Header
        self.status_label.config(text=f"Root Bridge: Switch {root_bridge}  (Priority: {switches[root_bridge]['priority']}, MAC: {switches[root_bridge]['mac']})")

        # Draw Links and Labels
        for u, v, cost in links:
            x1, y1 = self.coords[u]
            x2, y2 = self.coords[v]
            
            role_u = port_roles[(u, v)][u]
            role_v = port_roles[(u, v)][v]
            
            # Determine line color (Gray dashed if blocked, green solid if forwarding)
            if role_u == 'BLK' or role_v == 'BLK':
                line_color = "#ff9999"
                dash = (5, 5)
                width = 2
            else:
                line_color = "#32CD32"
                dash = None
                width = 4
                
            self.canvas.create_line(x1, y1, x2, y2, fill=line_color, width=width, dash=dash)
            
            # Draw Cost in middle of line
            mx, my = (x1 + x2) / 2, (y1 + y2) / 2
            self.canvas.create_oval(mx-15, my-10, mx+15, my+10, fill="white", outline="gray")
            self.canvas.create_text(mx, my, text=str(cost), font=("Arial", 9))

            # Draw Port Roles near nodes
            self.draw_port_label(x1, y1, x2, y2, role_u)
            self.draw_port_label(x2, y2, x1, y1, role_v)

        # Draw Nodes
        for node, (x, y) in self.coords.items():
            color = "#87CEFA" if node == root_bridge else "#E6E6FA"
            self.canvas.create_oval(x-35, y-35, x+35, y+35, fill=color, outline="black", width=2)
            self.canvas.create_text(x, y-10, text=f"Switch {node}", font=("Arial", 10, "bold"))
            self.canvas.create_text(x, y+5, text=f"{switches[node]['priority']}", font=("Arial", 8))
            self.canvas.create_text(x, y+20, text=f"Cost: {root_path_cost[node]}", font=("Arial", 8))

    def draw_port_label(self, x1, y1, x2, y2, role):
        # Calculate position 25% down the line from the node
        px = x1 + (x2 - x1) * 0.25
        py = y1 + (y2 - y1) * 0.25
        
        color = "red" if role == 'BLK' else "black"
        bg_color = "#ffcccc" if role == 'BLK' else "#e6ffe6"
        
        self.canvas.create_rectangle(px-12, py-8, px+12, py+8, fill=bg_color, outline=color)
        self.canvas.create_text(px, py, text=role, font=("Arial", 8, "bold"), fill=color)

if __name__ == "__main__":
    app = STPSimulator()
    app.mainloop()