import sys
import time
import requests
import os
from PyQt6.QtWidgets import (
    QApplication, QWidget, QLabel, QPushButton, QVBoxLayout, QHBoxLayout, QFrame
)
from PyQt6.QtCore import Qt, QTimer, QThread, pyqtSignal, QPropertyAnimation, QEasingCurve
from PyQt6.QtWidgets import QGraphicsDropShadowEffect
from PyQt6.QtGui import QColor
from http.server import BaseHTTPRequestHandler, HTTPServer

TEST_URL = "https://speed.cloudflare.com/__down?bytes=200000000"  # 200 MB
UPLOAD_URL = "http://127.0.0.1:8000/"  # Local endpoint for upload test (use IP to avoid DNS issues)
CHUNK_SIZE_DOWNLOAD = 35 * 1024 * 1024  # 35 MB
CHUNK_SIZE_UPLOAD = 2 * 1024 * 1024    # 2 MB
UPLOAD_TOTAL = 200 * 1024 * 1024  # 200 MB

class DownloadWorker(QThread):
    progress = pyqtSignal(float, float, float)  # mbps, mbps_byte, downloaded_mb
    finished = pyqtSignal()
    error = pyqtSignal(str)
    def __init__(self):
        super().__init__()
        self.running = True
        self.total_bytes = 0
    def run(self):
        try:
            while self.running:
                try:
                    with requests.get(TEST_URL, stream=True, timeout=2) as r:
                        total_bytes = 0
                        start_time = time.perf_counter()
                        last_update = start_time
                        for chunk in r.iter_content(chunk_size=CHUNK_SIZE_DOWNLOAD):
                            if not self.running:
                                break
                            total_bytes += len(chunk)
                            self.total_bytes += len(chunk)
                            now = time.perf_counter()
                            if now - last_update >= 0.5:
                                elapsed = now - start_time
                                bits = total_bytes * 8
                                mbps = bits / elapsed / 1_000_000
                                mbps_byte = mbps / 8
                                downloaded_mb = self.total_bytes / (1024 * 1024)
                                self.progress.emit(mbps, mbps_byte, downloaded_mb)
                                last_update = now
                            del chunk  # Free memory
                            if not self.running:
                                break
                except Exception:
                    break
                downloaded_mb = self.total_bytes / (1024 * 1024)
                self.progress.emit(-1, -1, downloaded_mb)  # Signal completion
        except Exception as e:
            self.error.emit(str(e))
        self.finished.emit()
    def stop(self):
        self.running = False

class UploadWorker(QThread):
    progress = pyqtSignal(float, float, float)  # mbps, mbps_byte, uploaded_mb
    finished = pyqtSignal()
    error = pyqtSignal(str)
    def __init__(self):
        super().__init__()
        self.running = True
        self.total_bytes = 0
    def run(self):
        try:
            sent_bytes = 0
            start_time = time.perf_counter()
            last_update = start_time
            first_chunk = True
            retry_count = 0
            while self.running and sent_bytes < UPLOAD_TOTAL:
                chunk = os.urandom(CHUNK_SIZE_UPLOAD)
                try:
                    # POST a single chunk each time
                    print(f"[UploadWorker] Sending chunk {sent_bytes // CHUNK_SIZE_UPLOAD + 1} ({len(chunk)} bytes)...")
                    r = requests.post(UPLOAD_URL, data=chunk, headers={'Content-Type': 'application/octet-stream'}, timeout=5)
                    print(f"[UploadWorker] Chunk sent, response: {r.status_code}")
                    first_chunk = False
                    retry_count = 0
                except Exception as e:
                    print(f"[UploadWorker] POST failed: {e}")
                    if first_chunk and retry_count < 3:
                        retry_count += 1
                        print(f"[UploadWorker] Retrying first chunk (attempt {retry_count+1}/3)...")
                        time.sleep(1)
                        continue
                    self.error.emit("Upload server not reachable. Is upload_sink_server.py running?")
                    return
                sent_bytes += len(chunk)
                self.total_bytes += len(chunk)
                now = time.perf_counter()
                if now - last_update >= 0.5:
                    elapsed = now - start_time
                    bits = sent_bytes * 8
                    mbps = bits / elapsed / 1_000_000 if elapsed > 0 else 0
                    mbps_byte = mbps / 8
                    uploaded_mb = self.total_bytes / (1024 * 1024)
                    print(f"[UploadWorker] Progress: {uploaded_mb:.2f} MB uploaded, {mbps:.2f} Mbps")
                    self.progress.emit(mbps, mbps_byte, uploaded_mb)
                    last_update = now
                del chunk  # Free memory
                time.sleep(0.01)  # Reduce CPU usage
            uploaded_mb = self.total_bytes / (1024 * 1024)
            self.progress.emit(-1, -1, uploaded_mb)  # Signal completion
            print("[UploadWorker] Upload finished or stopped.")
        except Exception as e:
            print(f"[UploadWorker] Exception: {e}")
            self.error.emit(str(e))
        self.finished.emit()
    def stop(self):
        self.running = False

class SinkHandler(BaseHTTPRequestHandler):
    def do_POST(self):
        self.send_response(200)
        self.end_headers()
        self.connection.settimeout(0.1)  # Don't block forever
        total = 0
        try:
            while True:
                chunk = self.rfile.read(1024 * 1024)
                if not chunk:
                    break
                total += len(chunk)
        except Exception:
            pass
        print(f"[Server] Received POST: {total} bytes")

class RealTimeSpeedMonitorPyQt(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Live Speed Monitor (Streaming 200 MB)")
        self.setGeometry(200, 200, 600, 230)
        self.setMinimumSize(600, 230)
        self.setMaximumSize(600, 230)
        self.download_worker = None
        self.upload_worker = None
        self.active_workers = 0
        self._is_fading_out = False
        self._fade_anim = None

        # Main layout
        main_layout = QVBoxLayout()
        main_layout.setContentsMargins(10, 8, 10, 2)  # Even tighter bottom margin
        main_layout.setSpacing(6)  # Reduce vertical spacing between sections

        # Side-by-side layout for download/upload
        h_layout = QHBoxLayout()
        h_layout.setSpacing(10)  # Reduce space between download/upload sections
        # Download section
        download_frame = QFrame()
        download_vbox = QVBoxLayout()
        download_icon = QLabel("⬇️", alignment=Qt.AlignmentFlag.AlignCenter)
        download_icon.setStyleSheet("font-size: 28px; margin-bottom: 2px;")
        download_vbox.addWidget(download_icon)
        self.download_icon = download_icon  # Save for animation
        self.download_icon_glow = QGraphicsDropShadowEffect()
        self.download_icon_glow.setColor(QColor('#1e90ff'))
        self.download_icon_glow.setBlurRadius(0)
        self.download_icon_glow.setOffset(0, 0)
        self.download_icon.setGraphicsEffect(self.download_icon_glow)
        self.download_label = QLabel("Download: -- Mbps | -- MBps", alignment=Qt.AlignmentFlag.AlignCenter)
        self.download_label.setStyleSheet("font-size: 15px;")
        download_vbox.addWidget(self.download_label)
        self.total_downloaded_label = QLabel("Downloaded: 0.00 MB", alignment=Qt.AlignmentFlag.AlignCenter)
        self.total_downloaded_label.setStyleSheet("font-size: 15px;")
        download_vbox.addWidget(self.total_downloaded_label)
        download_frame.setLayout(download_vbox)
        download_frame.setStyleSheet("""
            QFrame {
                border: 2px solid #1e90ff;
                border-radius: 18px;
                background: rgba(30, 144, 255, 0.07);
            }
        """)
        h_layout.addWidget(download_frame)
        # Upload section
        upload_frame = QFrame()
        upload_vbox = QVBoxLayout()
        upload_icon = QLabel("⬆️", alignment=Qt.AlignmentFlag.AlignCenter)
        upload_icon.setStyleSheet("font-size: 28px; margin-bottom: 2px;")
        upload_vbox.addWidget(upload_icon)
        self.upload_icon = upload_icon  # Save for animation
        self.upload_icon_glow = QGraphicsDropShadowEffect()
        self.upload_icon_glow.setColor(QColor('orange'))
        self.upload_icon_glow.setBlurRadius(0)
        self.upload_icon_glow.setOffset(0, 0)
        self.upload_icon.setGraphicsEffect(self.upload_icon_glow)
        self.upload_label = QLabel("Upload: -- Mbps | -- MBps", alignment=Qt.AlignmentFlag.AlignCenter)
        self.upload_label.setStyleSheet("font-size: 15px;")
        upload_vbox.addWidget(self.upload_label)
        self.total_uploaded_label = QLabel("Uploaded: 0.00 MB", alignment=Qt.AlignmentFlag.AlignCenter)
        self.total_uploaded_label.setStyleSheet("font-size: 15px;")
        upload_vbox.addWidget(self.total_uploaded_label)
        upload_frame.setLayout(upload_vbox)
        upload_frame.setStyleSheet("""
            QFrame {
                border: 2px solid orange;
                border-radius: 18px;
                background: rgba(255, 165, 0, 0.07);
            }
        """)
        h_layout.addWidget(upload_frame)
        main_layout.addLayout(h_layout)

        # Status
        self.status_label = QLabel("Status: Idle", alignment=Qt.AlignmentFlag.AlignCenter)
        self.status_label.setStyleSheet("color: white;")
        main_layout.addWidget(self.status_label)

        # Buttons
        btn_layout = QHBoxLayout()
        self.start_btn = QPushButton("Start")
        self.start_btn.setStyleSheet("background: green; color: white; font-weight: bold; font-size: 16px;")
        self.start_btn.setFixedHeight(40)
        self.start_btn.clicked.connect(self.start_monitor)
        btn_layout.addWidget(self.start_btn)
        self.stop_btn = QPushButton("Stop")
        self.stop_btn.setStyleSheet("background: #ff8000; color: white; font-weight: bold; font-size: 16px;")
        self.stop_btn.setFixedHeight(40)
        self.stop_btn.clicked.connect(self.stop_monitor)
        btn_layout.addWidget(self.stop_btn)
        main_layout.addLayout(btn_layout)

        self.setLayout(main_layout)

        # Animation objects
        self.download_anim = None
        self.upload_anim = None
        self.download_glow_anim = None
        self.upload_glow_anim = None

    def showEvent(self, event):
        super().showEvent(event)
        self.setWindowOpacity(0.0)
        self._fade_anim = QPropertyAnimation(self, b"windowOpacity")
        self._fade_anim.setDuration(250)
        self._fade_anim.setStartValue(0.0)
        self._fade_anim.setEndValue(1.0)
        self._fade_anim.setEasingCurve(QEasingCurve.Type.InOutQuad)
        self._fade_anim.start()

    def closeEvent(self, event):
        if self._is_fading_out:
            event.accept()
            return
        event.ignore()
        self._is_fading_out = True
        self._fade_anim = QPropertyAnimation(self, b"windowOpacity")
        self._fade_anim.setDuration(250)
        self._fade_anim.setStartValue(self.windowOpacity())
        self._fade_anim.setEndValue(0.0)
        self._fade_anim.setEasingCurve(QEasingCurve.Type.InOutQuad)
        self._fade_anim.finished.connect(self._final_close)
        self._fade_anim.start()

    def _final_close(self):
        self._is_fading_out = False
        super().close()
        app = QApplication.instance()
        if app is not None:
            QTimer.singleShot(0, app.quit)

    def start_monitor(self):
        self.start_btn.setEnabled(False)
        self.download_label.setText("Download: -- Mbps | -- MBps")
        self.total_downloaded_label.setText("Downloaded: 0.00 MB")
        self.upload_label.setText("Upload: -- Mbps | -- MBps")
        self.total_uploaded_label.setText("Uploaded: 0.00 MB")
        self.status_label.setText("Status: Running...")
        self.status_label.setStyleSheet("color: green;")
        self.active_workers = 2
        # Start pulsing glow animations
        self.start_glow_animation(self.download_icon_glow, 'download')
        self.start_glow_animation(self.upload_icon_glow, 'upload')
        # Download worker
        self.download_worker = DownloadWorker()
        self.download_worker.progress.connect(self.update_labels_download)
        self.download_worker.finished.connect(self.worker_finished)
        self.download_worker.error.connect(self.worker_error_download)
        self.download_worker.start()
        # Upload worker
        self.upload_worker = UploadWorker()
        self.upload_worker.progress.connect(self.update_labels_upload)
        self.upload_worker.finished.connect(self.worker_finished)
        self.upload_worker.error.connect(self.worker_error_upload)
        self.upload_worker.start()

    def stop_monitor(self):
        if self.download_worker:
            self.download_worker.stop()
            self.download_worker.wait()
        if self.upload_worker:
            self.upload_worker.stop()
            self.upload_worker.wait()
        self.status_label.setText("Status: Stopping...")
        self.status_label.setStyleSheet("color: orange;")

    def update_labels_download(self, mbps, mbps_byte, downloaded_mb):
        if mbps == -1:
            self.download_label.setText("Download: -- Mbps | -- MBps")
        elif mbps is not None and mbps_byte is not None:
            self.download_label.setText(f"Download: {mbps:.2f} Mbps | {mbps_byte:.2f} MBps")
        if downloaded_mb is not None:
            self.total_downloaded_label.setText(f"Downloaded: {downloaded_mb:.2f} MB")

    def update_labels_upload(self, mbps, mbps_byte, uploaded_mb):
        if mbps == -1:
            # Keep the last speed visible, only update the total uploaded label
            pass
        elif mbps is not None and mbps_byte is not None:
            self.upload_label.setText(f"Upload: {mbps:.2f} Mbps | {mbps_byte:.2f} MBps")
        if uploaded_mb is not None:
            self.total_uploaded_label.setText(f"Uploaded: {uploaded_mb:.2f} MB")

    def worker_finished(self):
        self.active_workers -= 1
        if self.active_workers <= 0:
            self.status_label.setText("Status: Stopped")
            self.status_label.setStyleSheet("color: orange;")
            self.start_btn.setEnabled(True)
            self.download_worker = None
            self.upload_worker = None
            # Stop pulsing glow animations
            self.stop_glow_animation(self.download_icon_glow, 'download')
            self.stop_glow_animation(self.upload_icon_glow, 'upload')

    def worker_error_download(self, msg):
        self.download_label.setText("Error")
        self.status_label.setText(f"Download Error: {msg}")
        self.status_label.setStyleSheet("color: red;")
        self.worker_finished()

    def worker_error_upload(self, msg):
        self.upload_label.setText("Error")
        self.status_label.setText(f"Upload Error: {msg}")
        self.status_label.setStyleSheet("color: red;")
        self.worker_finished()

    def start_glow_animation(self, effect, which):
        anim = QPropertyAnimation(effect, b"blurRadius")
        anim.setStartValue(0)
        anim.setKeyValueAt(0.5, 32)
        anim.setEndValue(0)
        anim.setDuration(900)
        anim.setLoopCount(-1)
        anim.setEasingCurve(QEasingCurve.Type.InOutQuad)
        anim.start()
        if which == 'download':
            self.download_glow_anim = anim
        else:
            self.upload_glow_anim = anim

    def stop_glow_animation(self, effect, which):
        if which == 'download' and self.download_glow_anim:
            self.download_glow_anim.stop()
            self.download_glow_anim = None
        elif which == 'upload' and self.upload_glow_anim:
            self.upload_glow_anim.stop()
            self.upload_glow_anim = None
        effect.setBlurRadius(0)

if __name__ == "__main__":
    if '--server' in sys.argv:
        server = HTTPServer(('localhost', 8000), SinkHandler)
        print('Listening on http://localhost:8000 ...')
        server.serve_forever()
    else:
        app = QApplication(sys.argv)
        win = RealTimeSpeedMonitorPyQt()
        win.show()
        sys.exit(app.exec()) 