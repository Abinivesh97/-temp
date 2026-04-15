import tkinter as tk
import math

class STP_Simulation:
    def __init__(self, root):
        self.root = root
        self.root.title("Spanning Tree Protocol (STP) Simulator")
        self.canvas = tk.Canvas(root, width=600, height=500, bg="#1e1e2e")
        self.canvas.pack(pady=10)

        # Simulation State
        self.stp_on = False
        self.packets = []
        self.packet_speed = 3.0
        self.max_packets = 300  # Safety limit to prevent Python from freezing
        self.crashed = False

        # Node coordinates (Switch 1, 2, 3, 4)
        self.nodes = {
            1: (150, 100),
            2: (450, 100),
            3: (450, 400),
            4: (150, 400)
        }
        
        # Connections between nodes (Ring Topology)
        self.adjacency = {
            1: [2, 4],
            2: [1, 3],
            3: [2, 4],
            4: [1, 3]
        }
        
        # The link that STP will block (between Switch 3 and 4)
        self.blocked_link = (3, 4)

        self.setup_ui()
        self.draw_network()
        self.update_loop()

    def setup_ui(self):
        control_frame = tk.Frame(self.root)
        control_frame.pack(fill=tk.X, padx=20)

        self.btn_stp = tk.Button(control_frame, text="STP Status: OFF", width=15, font=("Arial", 10, "bold"), bg="#ff4c4c", fg="white", command=self.toggle_stp)
        self.btn_stp.pack(side=tk.LEFT, padx=10)

        self.btn_send = tk.Button(control_frame, text="Send Broadcast Frame", font=("Arial", 10), command=self.send_broadcast)
        self.btn_send.pack(side=tk.LEFT, padx=10)

        self.btn_reset = tk.Button(control_frame, text="Reset Network", font=("Arial", 10), command=self.reset_network)
        self.btn_reset.pack(side=tk.LEFT, padx=10)

        self.lbl_status = tk.Label(control_frame, text="Active Frames: 0", font=("Arial", 12, "bold"))
        self.lbl_status.pack(side=tk.RIGHT, padx=10)

    def draw_network(self):
        self.canvas.delete("network")
        
        # Draw Links (Cables)
        for node, neighbors in self.adjacency.items():
            for neighbor in neighbors:
                # Don't draw twice
                if node < neighbor:
                    x1, y1 = self.nodes[node]
                    x2, y2 = self.nodes[neighbor]
                    
                    # Check if this is the STP blocked link
                    is_blocked_link = (node == self.blocked_link[0] and neighbor == self.blocked_link[1]) or \
                                      (node == self.blocked_link[1] and neighbor == self.blocked_link[0])
                    
                    if self.stp_on and is_blocked_link:
                        # Draw blocked link (dashed red line)
                        self.canvas.create_line(x1, y1, x2, y2, fill="#ff4c4c", width=3, dash=(5, 5), tags="network")
                        self.canvas.create_text((x1+x2)/2, (y1+y2)/2, text="BLOCKED (STP)", fill="#ff4c4c", font=("Arial", 10, "bold"), tags="network")
                    else:
                        # Draw active link (solid green line)
                        self.canvas.create_line(x1, y1, x2, y2, fill="#4caf50", width=3, tags="network")

        # Draw Switches
        for node_id, (x, y) in self.nodes.items():
            self.canvas.create_rectangle(x-30, y-20, x+30, y+20, fill="#3b82f6", outline="white", tags="network")
            self.canvas.create_text(x, y, text=f"SW {node_id}", fill="white", font=("Arial", 10, "bold"), tags="network")

    def toggle_stp(self):
        self.stp_on = not self.stp_on
        if self.stp_on:
            self.btn_stp.config(text="STP Status: ON", bg="#4caf50")
        else:
            self.btn_stp.config(text="STP Status: OFF", bg="#ff4c4c")
        self.draw_network()

    def send_broadcast(self):
        if self.crashed: return
        # Originate a broadcast frame at Switch 1 (source = None, so it goes out all ports)
        self.spawn_packets(current_node=1, source_node=None)

    def spawn_packets(self, current_node, source_node):
        neighbors = self.adjacency[current_node]
        for neighbor in neighbors:
            # Rule 1: A switch never forwards a broadcast out the same port it received it on
            if neighbor == source_node:
                continue
            
            # Rule 2: If STP is on, do not send traffic across the blocked link
            is_blocked_link = (current_node == self.blocked_link[0] and neighbor == self.blocked_link[1]) or \
                              (current_node == self.blocked_link[1] and neighbor == self.blocked_link[0])
            
            if self.stp_on and is_blocked_link:
                continue

            # Create packet UI element
            x, y = self.nodes[current_node]
            pkt_id = self.canvas.create_oval(x-5, y-5, x+5, y+5, fill="#ffb86c", outline="white")
            
            self.packets.append({
                "id": pkt_id,
                "x": x,
                "y": y,
                "target": neighbor,
                "source": current_node
            })

    def reset_network(self):
        for p in self.packets:
            self.canvas.delete(p["id"])
        self.packets = []
        self.crashed = False
        self.canvas.delete("crash_text")
        self.lbl_status.config(text="Active Frames: 0", fg="black")

    def update_loop(self):
        if not self.crashed:
            new_packets = []
            packets_to_spawn = []

            for p in self.packets:
                tx, ty = self.nodes[p["target"]]
                
                # Calculate direction
                dx = tx - p["x"]
                dy = ty - p["y"]
                distance = math.hypot(dx, dy)

                # Move packet
                if distance > self.packet_speed:
                    move_x = (dx / distance) * self.packet_speed
                    move_y = (dy / distance) * self.packet_speed
                    p["x"] += move_x
                    p["y"] += move_y
                    self.canvas.move(p["id"], move_x, move_y)
                    new_packets.append(p)
                else:
                    # Packet has arrived at the next switch!
                    self.canvas.delete(p["id"])
                    # Prepare to duplicate it out of all other ports
                    packets_to_spawn.append((p["target"], p["source"]))

            self.packets = new_packets

            # Spawn new packets for the ones that arrived
            for target_node, source_node in packets_to_spawn:
                self.spawn_packets(target_node, source_node)

            # Update Label and Check for Storm
            count = len(self.packets)
            self.lbl_status.config(text=f"Active Frames: {count}")

            if count > self.max_packets:
                self.crashed = True
                self.lbl_status.config(text="BROADCAST STORM DETECTED", fg="red")
                self.canvas.create_text(300, 250, text="NETWORK CRASHED\nMAC Table Overloaded", fill="#ff4c4c", font=("Arial", 24, "bold"), justify="center", tags="crash_text")

        # Run loop at ~60 FPS (16ms)
        self.root.after(16, self.update_loop)

if __name__ == "__main__":
    root = tk.Tk()
    app = STP_Simulation(root)
    root.mainloop()