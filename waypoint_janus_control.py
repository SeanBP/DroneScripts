#!/usr/bin/env python3

import os
import time
from pymavlink import mavutil
import subprocess

# ==== CONFIGURABLE PARAMETERS ====
DEVICE = "/dev/serial0"
BAUD = 921600

JANUS_PATH = "/home/arratialab/Documents/Janus_5202_4.2.4_20251007_linux/bin/JanusC"
SESSION_NAME = "janus_tlogic"

WAYPOINT_INIT_JANUS = 0        # New waypoint to start Janus and voltage ramp
WAYPOINT_START_RECORD = 3      # Waypoint to start recording
WAYPOINT_STOP_RECORD = 5       # Waypoint to stop recording and shutdown Janus

# === Helper functions ===

def send_tmux_cmd(cmd):
    subprocess.run(["tmux", "send-keys", "-t", SESSION_NAME, cmd, "C-m"])
    time.sleep(0.2)

def janus_startup():
    print("Starting Janus...")
    subprocess.run(["tmux", "new-session", "-d", "-s", SESSION_NAME, f"./JanusC"], cwd=os.path.dirname(JANUS_PATH))
    time.sleep(2)
    for key in ['h', 'H', 'q']:
        send_tmux_cmd(key)
    print("Janus initialized and voltage ramping up.")

def janus_start_recording():
    print("Starting Janus recording...")
    send_tmux_cmd('s')

def janus_stop_recording():
    print("Stopping Janus recording and shutting down...")
    for key in ['S', 'h', 'H', 'm', 'q', 'q']:
        send_tmux_cmd(key)
        time.sleep(0.5)
    time.sleep(2)
    subprocess.run(["tmux", "kill-session", "-t", SESSION_NAME])
    print("Janus stopped.")

# === Main script ===

def main():
    print(f"Connecting to vehicle on {DEVICE}...")
    mav = mavutil.mavlink_connection(DEVICE, baud=BAUD)
    mav.wait_heartbeat()
    print(f"Heartbeat received from system {mav.target_system}")

    print("Listening for waypoint reached messages...")

    janus_started = False

    while True:
        msg = mav.recv_match(type='MISSION_ITEM_REACHED', blocking=True, timeout=5)
        if not msg:
            continue

        wp_seq = msg.seq
        print(f"Reached waypoint {wp_seq}")

        if wp_seq == WAYPOINT_INIT_JANUS and not janus_started:
            janus_startup()
            janus_started = True

        elif wp_seq == WAYPOINT_START_RECORD:
            if not janus_started:
                print("Warning: Janus not started yet! Starting now...")
                janus_startup()
                janus_started = True
            janus_start_recording()

        elif wp_seq == WAYPOINT_STOP_RECORD:
            if janus_started:
                janus_stop_recording()
            else:
                print("Warning: Janus was not running at stop waypoint.")
            break  # End the script after stopping recording

if __name__ == "__main__":
    main()
