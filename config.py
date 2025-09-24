import os
import csv

# ---------------------------
# Config & Defaults
# ---------------------------
BEEP_FILE = "assets/beep.mp3"     
LOG_FILE = "reminder_log.csv"
DEFAULT_INTERVAL_MIN = 20         
DEFAULT_BLINK_THRESHOLD = 8       
DEFAULT_EAR_THRESHOLD = 0.21      
POPUP_AUTO_CLOSE_S = 20           
CONSEC_FRAMES = 3

if not os.path.exists(LOG_FILE):
    with open(LOG_FILE, mode="w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["timestamp", "trigger", "ack", "blinks_in_last_min"])
import sys, os

def resource_path(relative_path):
    try:
        base_path = sys._MEIPASS  
    except Exception:
        base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)


BEEP_FILE = resource_path("assets/beep.mp3")
