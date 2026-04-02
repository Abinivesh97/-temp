import tkinter as tk
from tkinter import scrolledtext
import socket
import ssl
import threading
import time
from urllib.parse import urlparse
import uuid

class OSIBrowserSimulator:
    def __init__(self, root):
        self.root = root
        self.root.title("Grand OSI 7-Layer Browser Simulator - Wireshark Edition")
        self.root.geometry("1100x800")
        self.root.configure(bg="#2b2b2b")

        # --- Top Bar: URL & Port Input ---
        top_frame = tk.Frame(self.root, bg="#3c3f41", pady=10)
        top_frame.pack(fill=tk.X)

        tk.Label(top_frame, text="URL:", fg="white", bg="#3c3f41", font=("Consolas", 12)).pack(side=tk.LEFT, padx=10)
        self.url_entry = tk.Entry(top_frame, width=50, font=("Consolas", 12))
        self.url_entry.pack(side=tk.LEFT, padx=5)
        self.url_entry.insert(0, "www.google.com")
        self.url_entry.bind('<Return>', lambda event: self.start_request())

        # NEW: Source Port Input for Wireshark Filtering
        tk.Label(top_frame, text="Src Port:", fg="#00ff00", bg="#3c3f41", font=("Consolas", 12)).pack(side=tk.LEFT, padx=(20, 5))
        self.port_entry = tk.Entry(top_frame, width=8, font=("Consolas", 12), bg="#000000", fg="#00ff00")
        self.port_entry.pack(side=tk.LEFT, padx=5)
        self.port_entry.insert(0, "55555") # Default port for filtering
        
        go_btn = tk.Button(top_frame, text="GO", command=self.start_request, bg="#4CAF50", fg="white", font=("Consolas", 10, "bold"))
        go_btn.pack(side=tk.LEFT, padx=20)

        # --- Main Body: Split View ---
        main_frame = tk.Frame(self.root, bg="#2b2b2b")
        main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        # Left: Browser Render Area (Text-based for HTML)
        left_frame = tk.Frame(main_frame, bg="#2b2b2b")
        left_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        tk.Label(left_frame, text="Browser View (HTML Source)", fg="white", bg="#2b2b2b").pack(anchor=tk.W)
        self.browser_view = scrolledtext.ScrolledText(left_frame, bg="#ffffff", fg="#000000", font=("Consolas", 10))
        self.browser_view.pack(fill=tk.BOTH, expand=True, padx=(0, 5))

        # Right: OSI Debug Console
        right_frame = tk.Frame(main_frame, bg="#2b2b2b")
        right_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)
        tk.Label(right_frame, text="OSI 7-Layer Debug Console", fg="#00ff00", bg="#2b2b2b").pack(anchor=tk.W)
        self.console = scrolledtext.ScrolledText(right_frame, bg="#000000", fg="#00ff00", font=("Consolas", 10))
        self.console.pack(fill=tk.BOTH, expand=True, padx=(5, 0))

    def log_console(self, message, delay=0.5):
        self.console.insert(tk.END, message + "\n")
        self.console.see(tk.END)
        self.root.update()
        time.sleep(delay)

    def start_request(self):
        url = self.url_entry.get().strip()
        if not url: return

        if not url.startswith('http://') and not url.startswith('https://'):
            url = 'https://' + url
            self.url_entry.delete(0, tk.END)
            self.url_entry.insert(0, url)

        try:
            source_port = int(self.port_entry.get().strip())
        except ValueError:
            source_port = 55555 # Fallback if user types non-numbers

        self.browser_view.delete(1.0, tk.END)
        self.console.delete(1.0, tk.END)
        
        threading.Thread(target=self.execute_osi_stack, args=(url, source_port), daemon=True).start()

    def execute_osi_stack(self, url, source_port):
        parsed_url = urlparse(url)
        host = parsed_url.netloc
        path = parsed_url.path or "/"
        dest_port = 443 if parsed_url.scheme == "https" else 80

        self.log_console(f"[*] Starting ENCAPSULATION for {url}\n", 1)

        # ---------------------------------------------------------
        # ENCAPSULATION (Top-Down)
        # ---------------------------------------------------------
        self.log_console("↓ === LAYER 7: APPLICATION ===")
        http_request = f"GET {path} HTTP/1.1\r\nHost: {host}\r\nConnection: close\r\n\r\n"
        self.log_console(f"  - Generating HTTP GET Request payload.", 1)

        self.log_console("\n↓ === LAYER 6: PRESENTATION ===")
        if dest_port == 443:
            self.log_console("  - Encrypting stream with TLS (Symmetric AES-GCM cipher).", 1)
        else:
            self.log_console("  - Using Plaintext (No Encryption).", 1)

        self.log_console("\n↓ === LAYER 5: SESSION ===")
        try:
            target_ip = socket.gethostbyname(host)
            self.log_console(f"  - DNS Resolution Success: {target_ip}", 1)
        except socket.gaierror:
            self.log_console(f"[!] DNS Error: Could not resolve {host}. Halting.")
            return

        self.log_console("\n↓ === LAYER 4: TRANSPORT ===")
        self.log_console(f"  - Encapsulating into TCP SEGMENT.")
        # Notice we are now logging the actual bound source port
        self.log_console(f"  - Attaching Transport Header -> Src Port: [ {source_port} ], Dst Port: {dest_port}.", 1)

        self.log_console("\n↓ === LAYER 3: NETWORK ===")
        local_ip = socket.gethostbyname(socket.gethostname())
        self.log_console(f"  - Encapsulating segment into IPv4 PACKET.")
        self.log_console(f"  - Attaching IP Header -> Src IP: {local_ip}, Dst IP: {target_ip}.", 1)

        self.log_console("\n↓ === LAYER 2: DATA LINK ===")
        mac = ':'.join(['{:02x}'.format((uuid.getnode() >> ele) & 0xff) for ele in range(0,8*6,8)][::-1])
        self.log_console(f"  - Encapsulating packet into Ethernet FRAME.")
        self.log_console(f"  - Attaching MAC Header -> Src MAC: {mac}.", 1)

        self.log_console("\n↓ === LAYER 1: PHYSICAL ===")
        self.log_console("  - Translating binary frame into physical signals.", 1)

        self.log_console("\n[>>>] SIGNALS TRANSMITTED. WATCH WIRESHARK NOW! [<<<]\n", 1.5)

        # ---------------------------------------------------------
        # ACTUAL NETWORK EXECUTION
        # ---------------------------------------------------------
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            
            # --- THE MAGIC WIRESHARK CODE ---
            # SO_REUSEADDR prevents "Address already in use" errors if you run it multiple times quickly
            sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            
            # Bind the socket to the specific port the user entered in the GUI
            sock.bind(('0.0.0.0', source_port))
            # --------------------------------
            
            sock.settimeout(5)
            
            if dest_port == 443:
                context = ssl.create_default_context()
                sock = context.wrap_socket(sock, server_hostname=host)
            
            sock.connect((target_ip, dest_port))
            sock.sendall(http_request.encode('utf-8'))

            response = b""
            while True:
                data = sock.recv(4096)
                if not data: break
                response += data
            sock.close()

            response_str = response.decode('utf-8', errors='ignore')
            if "\r\n\r\n" in response_str:
                headers, body = response_str.split("\r\n\r\n", 1)
            else:
                body = response_str

            # ---------------------------------------------------------
            # DECAPSULATION (Bottom-Up)
            # ---------------------------------------------------------
            self.log_console(f"[*] Response received! Starting DECAPSULATION.\n", 1)

            self.log_console("↑ === LAYER 1 & 2: PHYSICAL / DATA LINK ===")
            self.log_console("  - Receiving bitstream, verifying MAC and FCS trailer.", 1)

            self.log_console("\n↑ === LAYER 3: NETWORK ===")
            self.log_console("  - Stripping IP Header. Confirmed TCP payload.", 1)

            self.log_console("\n↑ === LAYER 4: TRANSPORT ===")
            self.log_console(f"  - Verifying Destination Port matches our custom port: [ {source_port} ].", 1)

            self.log_console("\n↑ === LAYER 5 & 6: SESSION / PRESENTATION ===")
            self.log_console("  - Decrypting TLS (if HTTPS) and decoding UTF-8 stream.", 1)

            self.log_console("\n↑ === LAYER 7: APPLICATION ===")
            self.log_console("  - Extracting HTTP HTML Body for Browser.", 1)

            self.log_console("\n[+] DECAPSULATION COMPLETE. RENDERING VIEW.", 0.5)

            self.root.after(0, self.update_browser_view, body)

        except PermissionError:
            self.log_console(f"\n[!] PERMISSION ERROR: Port {source_port} might require Administrator/Root privileges, or is strictly reserved. Try a port above 1024 (like 55555).")
        except Exception as e:
            self.log_console(f"\n[!] Connection failed: {e}")

    def update_browser_view(self, content):
        self.browser_view.insert(tk.END, content)

if __name__ == "__main__":
    root = tk.Tk()
    app = OSIBrowserSimulator(root)
    root.mainloop()