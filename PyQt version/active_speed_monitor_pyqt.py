import sys
import time
import requests
from PyQt6.QtWidgets import (
    QApplication, QWidget, QLabel, QPushButton, QVBoxLayout, QHBoxLayout, QFrame
)
from PyQt6.QtCore import Qt, QThread, pyqtSignal, QPropertyAnimation, QEasingCurve
from PyQt6.QtWidgets import QGraphicsDropShadowEffect
from PyQt6.QtGui import QColor

TEST_URL = "https://speed.cloudflare.com/__down?bytes=200000000"  # 200 MB
CHUNK_SIZE_DOWNLOAD = 35 * 1024 * 1024  # 35 MB

class DownloadWorker(QThread):
    """
    Worker thread for downloading a test file and reporting real-time speed.
    """
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
                    # Use context manager to ensure response is closed
                    with requests.get(TEST_URL, stream=True, timeout=10) as r:
                        total_bytes = 0
                        start_time = time.perf_counter()
                        last_update = start_time
                        last_mbps = last_mbps_byte = last_downloaded_mb = None
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
                                # Only emit if values have changed
                                if (mbps != last_mbps or mbps_byte != last_mbps_byte or downloaded_mb != last_downloaded_mb):
                                    self.progress.emit(mbps, mbps_byte, downloaded_mb)
                                    last_mbps, last_mbps_byte, last_downloaded_mb = mbps, mbps_byte, downloaded_mb
                                last_update = now
                            del chunk  # Free memory
                            if not self.running:
                                break
                        # After finishing one file, continue to next if running
                        if not self.running:
                            break
                        # Optionally, reset per-file counters if you want per-file speed, or keep accumulating for total
                except requests.RequestException as e:
                    # Network or HTTP error
                    self.error.emit(f"Network error: {e}")
                    break
                except Exception as e:
                    self.error.emit(f"Unexpected error: {e}")
                    break
                # Do not emit completion, just continue to next file
                # downloaded_mb = self.total_bytes / (1024 * 1024)
                # self.progress.emit(-1, -1, downloaded_mb)  # Signal completion
        except Exception as e:
            self.error.emit(f"Fatal error: {e}")
        self.finished.emit()
    def stop(self):
        self.running = False

class RealTimeSpeedMonitorPyQt(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Live Speed Monitor (Streaming 200 MB)")
        self.setGeometry(200, 200, 600, 230)
        self.setMinimumSize(600, 230)
        self.setMaximumSize(600, 230)
        self.download_worker = None
        self.active_workers = 0
        self._is_fading_out = False
        self._fade_anim = None
        # No upload server needed for speedtest-cli

        # Main layout
        main_layout = QVBoxLayout()
        main_layout.setContentsMargins(10, 8, 10, 2)  # Even tighter bottom margin
        main_layout.setSpacing(6)  # Reduce vertical spacing between sections

        # Download section only
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
        main_layout.addWidget(download_frame)

        # Status
        self.status_label = QLabel("Status: Idle", alignment=Qt.AlignmentFlag.AlignCenter)
        self.status_label.setStyleSheet("color: white;")
        main_layout.addWidget(self.status_label)

        # Buttons
        btn_layout = QHBoxLayout()
        self.start_btn = QPushButton("Start")
        self.start_btn.setStyleSheet("""
            QPushButton {
                background: green;
                color: white;
                font-weight: bold;
                font-size: 16px;
                border-radius: 6px;
            }
            QPushButton:hover {
                background: #28d14c;
            }
            QPushButton:pressed {
                background: #176d2c;
            }
        """)
        self.start_btn.setFixedHeight(40)
        self.start_btn.clicked.connect(self.start_monitor)
        btn_layout.addWidget(self.start_btn)
        self.stop_btn = QPushButton("Stop")
        self.stop_btn.setStyleSheet("""
            QPushButton {
                background: #ff8000;
                color: white;
                font-weight: bold;
                font-size: 16px;
                border-radius: 6px;
            }
            QPushButton:hover {
                background: #ffb84d;
            }
            QPushButton:pressed {
                background: #b35c00;
            }
        """)
        self.stop_btn.setFixedHeight(40)
        self.stop_btn.clicked.connect(self.stop_monitor)
        self.stop_btn.setEnabled(False)  # Disabled before starting
        btn_layout.addWidget(self.stop_btn)
        main_layout.addLayout(btn_layout)

        self.setLayout(main_layout)

        # Animation objects
        self.download_anim = None
        self.download_glow_anim = None

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
            from PyQt6.QtCore import QTimer
            QTimer.singleShot(0, app.quit)

    def start_monitor(self):
        self.start_btn.setEnabled(False)
        self.stop_btn.setEnabled(True)  # Enable Stop when running
        self.download_label.setText("Download: -- Mbps | -- MBps")
        self.total_downloaded_label.setText("Downloaded: 0.00 MB")
        self.status_label.setText("Status: Running...")
        self.status_label.setStyleSheet("color: green;")
        self.active_workers = 1
        # Start pulsing glow animations
        self.start_glow_animation(self.download_icon_glow, 'download')
        # Download worker
        self.download_worker = DownloadWorker()
        self.download_worker.progress.connect(self.update_labels_download)
        self.download_worker.finished.connect(self.worker_finished)
        self.download_worker.error.connect(self.worker_error_download)
        self.download_worker.start()
        # self.stop_btn.setEnabled(False)  # Do not disable Stop during upload

    def stop_monitor(self):
        if self.download_worker:
            self.download_worker.stop()
            self.download_worker.wait()
        self.status_label.setText("Status: Stopping...")
        self.status_label.setStyleSheet("color: orange;")

    def update_labels_download(self, mbps, mbps_byte, downloaded_mb):
        # Only update UI if values have changed
        if not hasattr(self, '_last_dl_values'):
            self._last_dl_values = (None, None, None)
        if (mbps, mbps_byte, downloaded_mb) == self._last_dl_values:
            return
        self._last_dl_values = (mbps, mbps_byte, downloaded_mb)
        if mbps == -1:
            self.download_label.setText("Download: -- Mbps | -- MBps")
        elif mbps is not None and mbps_byte is not None:
            self.download_label.setText(f"Download: {mbps:.2f} Mbps | {mbps_byte:.2f} MBps")
        if downloaded_mb is not None:
            self.total_downloaded_label.setText(f"Downloaded: {downloaded_mb:.2f} MB")

    def worker_finished(self):
        self.active_workers -= 1
        if self.active_workers <= 0:
            self.status_label.setText("Status: Stopped")
            self.status_label.setStyleSheet("color: orange;")
            self.start_btn.setEnabled(True)
            self.download_worker = None
            # Stop pulsing glow animations
            self.stop_glow_animation(self.download_icon_glow, 'download')
            self.stop_btn.setEnabled(False)  # Disable Stop when done

    def worker_error_download(self, msg):
        self.download_label.setText("Error")
        self.status_label.setText(f"Download Error: {msg}")
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

    def stop_glow_animation(self, effect, which):
        if which == 'download' and self.download_glow_anim:
            self.download_glow_anim.stop()
            self.download_glow_anim = None
        effect.setBlurRadius(0)

if __name__ == "__main__":
    app = QApplication(sys.argv)
    win = RealTimeSpeedMonitorPyQt()
    win.show()
    sys.exit(app.exec()) 

# App Created by FAiTH
