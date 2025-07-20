import tkinter as tk
from threading import Thread
import time
import requests

TEST_URL = "https://speed.cloudflare.com/__down?bytes=200000000"  # 200 MB
CHUNK_SIZE = 256 * 1024  # 256 KB

class RealTimeSpeedMonitor:
    def __init__(self, root):
        self.root = root
        self.root.title("Live Speed Monitor (Streaming 200 MB)")
        self.root.geometry("500x270")
        self.running = False
        self.total_bytes_all = 0  # Cumulative download counter

        tk.Label(root, text="Streaming 200 MB (estimates every 500ms)", font=("Arial", 12)).pack(pady=10)
        self.download_label = tk.Label(root, text="Download: -- Mbps | -- MBps", font=("Arial", 12))
        self.download_label.pack(pady=5)
        self.total_downloaded_label = tk.Label(root, text="Downloaded: 0.00 MB", font=("Arial", 12))
        self.total_downloaded_label.pack(pady=5)
        self.status_label = tk.Label(root, text="Status: Idle", font=("Arial", 10), fg="gray")
        self.status_label.pack(pady=5)

        tk.Button(root, text="Start", command=self.start_monitor, bg="green", fg="white", width=10).pack(pady=5)
        tk.Button(root, text="Stop", command=self.stop_monitor, bg="red", fg="white", width=10).pack()

    def stream_download_speed(self):
        try:
            while self.running:
                r = requests.get(TEST_URL, stream=True, timeout=10)
                total_bytes = 0
                start_time = time.perf_counter()
                last_update = start_time

                for chunk in r.iter_content(chunk_size=CHUNK_SIZE):
                    if not self.running:
                        break
                    total_bytes += len(chunk)
                    self.total_bytes_all += len(chunk)
                    now = time.perf_counter()
                    if now - last_update >= 0.5:
                        elapsed = now - start_time
                        bits = total_bytes * 8
                        mbps = bits / elapsed / 1_000_000
                        mbps_byte = mbps / 8
                        downloaded_mb = self.total_bytes_all / (1024 * 1024)
                        self.download_label.config(text=f"Download: {mbps:.2f} Mbps | {mbps_byte:.2f} MBps")
                        self.total_downloaded_label.config(text=f"Downloaded: {downloaded_mb:.2f} MB")
                        self.status_label.config(text="Status: Downloading...", fg="blue")
                        last_update = now

                downloaded_mb = self.total_bytes_all / (1024 * 1024)
                self.total_downloaded_label.config(text=f"Downloaded: {downloaded_mb:.2f} MB")
                self.status_label.config(text="Status: Completed one file", fg="green")
        except Exception as e:
            self.download_label.config(text="Error")
            self.status_label.config(text=f"Status: {e}", fg="red")

    def start_monitor(self):
        if not self.running:
            self.running = True
            Thread(target=self.stream_download_speed, daemon=True).start()

    def stop_monitor(self):
        self.running = False
        self.download_label.config(text="Download: -- Mbps | -- MBps")
        self.total_downloaded_label.config(text="Downloaded: 0.00 MB")
        self.total_bytes_all = 0  # Reset total counter on stop
        self.status_label.config(text="Status: Stopped", fg="gray")

if __name__ == "__main__":
    root = tk.Tk()
    RealTimeSpeedMonitor(root)
    root.mainloop()
