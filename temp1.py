import tkinter as tk
import math

class NetworkSlicerVisualizer:
    def __init__(self, root):
        self.root = root
        self.root.title("TCP Segmentation vs IP Fragmentation Visualizer")
        self.root.geometry("1100x700")
        self.root.configure(bg="#2b2b2b")

        # --- Top Control Panel ---
        control_frame = tk.Frame(self.root, bg="#3c3f41", pady=15)
        control_frame.pack(fill=tk.X)

        font_style = ("Consolas", 12)

        tk.Label(control_frame, text="App Data Size (Bytes):", fg="white", bg="#3c3f41", font=font_style).pack(side=tk.LEFT, padx=(20, 5))
        self.data_var = tk.StringVar(value="3000")
        tk.Entry(control_frame, textvariable=self.data_var, width=8, font=font_style).pack(side=tk.LEFT, padx=5)

        tk.Label(control_frame, text="TCP MSS (Bytes):", fg="#50E3C2", bg="#3c3f41", font=font_style).pack(side=tk.LEFT, padx=(20, 5))
        self.mss_var = tk.StringVar(value="1460")
        tk.Entry(control_frame, textvariable=self.mss_var, width=8, font=font_style).pack(side=tk.LEFT, padx=5)

        tk.Label(control_frame, text="Network MTU (Bytes):", fg="#F5A623", bg="#3c3f41", font=font_style).pack(side=tk.LEFT, padx=(20, 5))
        self.mtu_var = tk.StringVar(value="1000")
        tk.Entry(control_frame, textvariable=self.mtu_var, width=8, font=font_style).pack(side=tk.LEFT, padx=5)

        btn = tk.Button(control_frame, text="SIMULATE", command=self.draw_simulation, bg="#4CAF50", fg="white", font=("Consolas", 12, "bold"))
        btn.pack(side=tk.LEFT, padx=30)

        # --- Drawing Canvas ---
        self.canvas = tk.Canvas(self.root, bg="#1e1e1e", highlightthickness=0)
        self.canvas.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)

        # Initial Draw
        self.draw_simulation()

    def draw_simulation(self):
        self.canvas.delete("all")
        
        try:
            data_size = int(self.data_var.get())
            mss = int(self.mss_var.get())
            mtu = int(self.mtu_var.get())
        except ValueError:
            self.canvas.create_text(550, 300, text="Please enter valid integers.", fill="red", font=("Consolas", 16))
            return

        if mss < 20 or mtu < 40 or data_size < 1:
            self.canvas.create_text(550, 300, text="Values too small. MTU must be > 40, MSS > 20.", fill="red", font=("Consolas", 16))
            return

        # -------------------------------------------------------------
        # 1. MATH: SEGMENTATION (Layer 4)
        # -------------------------------------------------------------
        segments = []
        remaining_data = data_size
        while remaining_data > 0:
            chunk = min(remaining_data, mss)
            segments.append({
                'payload': chunk,
                'tcp_hdr': 20,
                'total': chunk + 20
            })
            remaining_data -= chunk

        # -------------------------------------------------------------
        # 2. MATH: FRAGMENTATION (Layer 3)
        # -------------------------------------------------------------
        fragments = []
        # IP payload must be a multiple of 8 bytes
        max_ip_payload = ((mtu - 20) // 8) * 8

        for seg in segments:
            # The entire TCP segment (data + TCP header) becomes the IP payload
            ip_payload_to_send = seg['total']
            seg_frags = []
            
            # Encapsulate into an IP Packet
            initial_ip_packet_size = ip_payload_to_send + 20 

            # Check if it needs fragmentation
            if initial_ip_packet_size <= mtu:
                seg_frags.append({'ip_hdr': 20, 'payload': ip_payload_to_send, 'total': ip_payload_to_send + 20, 'fragmented': False})
            else:
                while ip_payload_to_send > 0:
                    chunk = min(ip_payload_to_send, max_ip_payload)
                    seg_frags.append({'ip_hdr': 20, 'payload': chunk, 'total': chunk + 20, 'fragmented': True})
                    ip_payload_to_send -= chunk
            fragments.append(seg_frags)

        # -------------------------------------------------------------
        # 3. DRAWING LOGIC
        # -------------------------------------------------------------
        # Calculate maximum width to scale everything proportionally
        total_frag_bytes = sum([sum([f['total'] for f in group]) for group in fragments])
        max_bytes = max(data_size, sum([s['total'] for s in segments]), total_frag_bytes)
        
        # 1000 pixels is our max drawing width
        scale = 1000.0 / (max_bytes if max_bytes > 0 else 1)
        start_x = 30

        # --- Draw Tier 1: Application Data ---
        self.canvas.create_text(start_x, 30, text="Layer 7: Original Application Data", fill="white", font=("Consolas", 12, "bold"), anchor="w")
        app_w = data_size * scale
        self.draw_box(start_x, 50, app_w, 60, "#4A90E2", f"Data: {data_size}B")

        # --- Draw Tier 2: TCP Segments ---
        self.canvas.create_text(start_x, 160, text=f"Layer 4: TCP Segmentation (MSS = {mss}B)", fill="#50E3C2", font=("Consolas", 12, "bold"), anchor="w")
        current_x = start_x
        for i, seg in enumerate(segments):
            seg_w = seg['total'] * scale
            # We subtract 2 from width to leave a tiny visual gap between blocks
            self.draw_box(current_x, 180, seg_w - 2, 60, "#2c7a67", f"TCP {i+1}\n{seg['total']}B")
            current_x += seg_w

        # --- Draw Tier 3: IP Fragments ---
        self.canvas.create_text(start_x, 290, text=f"Layer 3: IP Encapsulation & Fragmentation (MTU = {mtu}B)", fill="#F5A623", font=("Consolas", 12, "bold"), anchor="w")
        current_x = start_x
        frag_count = 1
        
        for group in fragments:
            for frag in group:
                frag_w = frag['total'] * scale
                color = "#9c6000" if frag['fragmented'] else "#734a06"
                label = f"Frag {frag_count}\n{frag['total']}B" if frag['fragmented'] else f"Packet\n{frag['total']}B"
                
                self.draw_box(current_x, 310, frag_w - 2, 60, color, label)
                current_x += frag_w
                frag_count += 1

        # --- Draw Summary ---
        summary_y = 420
        self.canvas.create_text(start_x, summary_y, text="--- Journey Summary ---", fill="white", font=("Consolas", 14, "bold"), anchor="w")
        self.canvas.create_text(start_x, summary_y + 30, text=f"1. Started with {data_size} Bytes of Data.", fill="white", font=("Consolas", 12), anchor="w")
        self.canvas.create_text(start_x, summary_y + 55, text=f"2. Segmented into {len(segments)} TCP Segments.", fill="#50E3C2", font=("Consolas", 12), anchor="w")
        
        total_packets = sum([len(group) for group in fragments])
        self.canvas.create_text(start_x, summary_y + 80, text=f"3. Ultimately transmitted as {total_packets} IP Packets/Fragments over the network.", fill="#F5A623", font=("Consolas", 12), anchor="w")


    def draw_box(self, x, y, width, height, color, text):
        """Helper to draw a rectangle with centered text"""
        # Ensure minimum width so it doesn't crash drawing
        width = max(width, 2)
        
        self.canvas.create_rectangle(x, y, x + width, y + height, fill=color, outline="black")
        
        # Only draw text if the box is wide enough to sort of hold it
        if width > 40:
            self.canvas.create_text(x + (width / 2), y + (height / 2), text=text, fill="white", font=("Consolas", 10), justify="center")

if __name__ == "__main__":
    root = tk.Tk()
    app = NetworkSlicerVisualizer(root)
    root.mainloop()