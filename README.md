# Internet Speed Monitor

A real-time internet download speed monitor with a graphical interface, available in both **Tkinter** and **PyQt6** versions. Instantly see your download speed, total data transferred, and status updates in a modern, user-friendly window.

---

## Features

| Feature                | Tkinter Version (`active_speed_monitor.py`) | PyQt6 Version (`active_speed_monitor_pyqt.py`) |
|------------------------|:------------------------------------------:|:----------------------------------------------:|
| Download Speed         | ✅                                          | ✅                                              |
| Upload Speed           | ❌                                          | ❌                                              |
| Real-Time Updates      | ✅ (every 0.5s)                             | ✅ (every 0.5s)                                 |
| Total Data Counter     | ✅                                          | ✅                                              |
| Start/Stop Controls    | ✅                                          | ✅                                              |
| Threaded/Async         | ✅ (threaded)                               | ✅ (QThread)                                    |
| Modern UI/Animations   | ❌                                          | ✅ (glow, fade, icons)                          |
| Status Display         | ✅                                          | ✅                                              |
| Error Handling         | ✅                                          | ✅                                              |
| Cross-Platform         | ✅                                          | ✅                                              |

---

## Screenshots

**PyQt6 Version:**

![PyQt6 Version](./pyqt_screenshot.png)

*Screenshot updated to reflect the latest UI changes.*

**Tkinter Version:**

![Tkinter Version](./tkinter_screenshot.png)

---

## How It Works

- **Download Test:** Both versions download a 200 MB test file from Cloudflare in chunks, measuring speed in real time.
- **Live GUI:** See your current speed (Mbps/MBps), total MB transferred, and status (Idle, Downloading, Completed, Stopped, Error).
- **Start/Stop:** Begin or halt the test at any time. The UI remains responsive throughout.

---

## Requirements

- **Python 3.x**
- **requests** library (`pip install requests`)
- **PyQt6** (`pip install PyQt6`) — *for the PyQt version only*

---

## Usage

### Tkinter Version

1. **Install dependencies:**
   ```bash
   pip install requests
   ```
2. **Run:**
   ```bash
   python active_speed_monitor.py
   ```
3. Click **Start** to begin the download speed test. Click **Stop** to halt and reset.

---

### PyQt6 Version

1. **Install dependencies:**
   ```bash
   pip install requests PyQt6
   ```
2. **Run:**
   ```bash
   python active_speed_monitor_pyqt.py
   ```
3. Click **Start** to begin the download speed test. Click **Stop** to halt and reset.

---

## File Overview

- `active_speed_monitor.py` — Tkinter-based, download speed only, simple UI.
- `active_speed_monitor_pyqt.py` — PyQt6-based, download speed only, modern UI with animations.
- `Speed Monitor PyQt.exe` / `Speed Monitor Tkinter.exe` — Pre-built executables (if provided).
- `net works.txt` — Development notes.
- `active_speed_monitor.spec` — PyInstaller spec for building executables.

---

## Limitations

- **Data Usage:** Each test downloads up to 200 MB per file (and continues for as long as you let it run).
- **Speed Variability:** Results depend on your ISP, network, and server conditions.
- **No Upload Test:** This app only measures download speed.

---

## Author

Created by FAiTH 