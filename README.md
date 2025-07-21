# Active Speed Monitor

A simple, real-time internet download speed monitor with a graphical interface.

---
[ There are two versions, one is Tkinter version the other one is PyQt version(which shows upload speed also) ]

[ To run the file just download any of the two files mentioned above and run it on your pc ]

## What is this?

**Active Speed Monitor** is a Python program that measures your internet download speed in real time. It downloads a large file from the internet and shows your current speed (in Mbps and MBps), total data downloaded, and status updates in a user-friendly window.

---

## How does it work?
- **Real-Time Measurement:**
  - Downloads a 200 MB test file from Cloudflare in chunks.
  - Every 0.5 seconds, it calculates and displays your current download speed.
- **Live GUI:**
  - Built with Tkinter for a simple, responsive interface.
  - Shows download speed, total MB downloaded, and status (Idle, Downloading, Completed, Stopped, or Error).
- **Start/Stop Control:**
  - You can start or stop the test at any time.
- **Threaded Download:**
  - Uses a background thread for downloading, so the interface never freezes.

---

## How does it help you?
- **See your real download speed as it happens.**
- **Get both Mbps (megabits/sec) and MBps (megabytes/sec) readings.**
- **Know how much data was downloaded during the test.**
- **Easy to use:** No command line needed—just click Start/Stop.

---

## Usage

1. **Install requirements:**
   - Python 3.x
   - `requests` library (`pip install requests`)

2. **Run the program:**
   ```bash
   python active_speed_monitor.py
   ```

3. **Click "Start"** to begin the speed test. Watch the speed and data counters update live.

4. **Click "Stop"** to halt the test and reset the counters.

---

## How it works (in detail)
- Downloads a 200 MB file from Cloudflare in 256 KB chunks.
- Every 0.5 seconds, calculates:
  - Elapsed time
  - Downloaded bytes (converted to bits)
  - Speed in Mbps and MBps
  - Total MB downloaded
- Updates the GUI labels with these values.
- Handles errors and shows status messages.

---

## Limitations
- Measures **download speed only** (not upload).
- Uses real data—each test downloads up to 200 MB.
- Speed may vary depending on server, ISP, or network conditions.

---

## Example Screenshot

*(Add a screenshot of the running program here if you like!)*

---

## Summary Table

| Feature         | How it works / helps you know speed         |
|-----------------|--------------------------------------------|
| Real-time speed | Updates every 0.5s, shows Mbps/MBps        |
| Total downloaded| Shows MB downloaded so far                  |
| Status display  | Shows Idle, Downloading, Completed, Error   |
| Start/Stop      | Lets you control when to test               |
| GUI             | Easy to use, no command line needed         |

---

## Author
Created by FAiTH 
