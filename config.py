import os
import csv

# Basic Config
BEEP_FILE = "assets/beep.mp3"
LOG_FILE = "reminder_log.csv"
MUSIC_FOLDER = "assets/music"

# Detection Thresholds
DEFAULT_INTERVAL_MIN = 20
DEFAULT_BLINK_THRESHOLD = 8
DEFAULT_EAR_THRESHOLD = 0.21
CONSEC_FRAMES = 3

# NEW: Drowsiness Detection
DROWSY_EYE_CLOSED_SECONDS = 2.0  # Eyes closed for 2+ seconds = drowsy
SLEEP_EYE_CLOSED_SECONDS = 4.0   # Eyes closed for 4+ seconds = sleeping
DROWSY_BEEP_INTERVAL = 3.0       # Beep every 3 seconds when drowsy

# NEW: Stress Detection
STRESS_WINDOW_SECONDS = 10       # Analyze last 10 seconds
STRESS_HIGH_THRESHOLD = 70       # 70+ = High stress
STRESS_MEDIUM_THRESHOLD = 40     # 40-70 = Medium stress

# NEW: Heart Rate
HR_BUFFER_SECONDS = 15           # Need 15 seconds of data
HR_UPDATE_INTERVAL = 5           # Update every 5 seconds

# Popup
POPUP_AUTO_CLOSE_S = 20

# Initialize log file
if not os.path.exists(LOG_FILE):
    with open(LOG_FILE, mode="w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["timestamp", "trigger", "ack", "blinks_in_last_min", 
                        "stress_level", "heart_rate", "drowsiness_score"])

# Create music folder
os.makedirs(MUSIC_FOLDER, exist_ok=True)


