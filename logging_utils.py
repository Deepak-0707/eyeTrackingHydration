import csv
from datetime import datetime
import os

def log_event(trigger, ack, blinks_last_min, stress_level=0, heart_rate=0, drowsiness_score=0):
    """Log event with enhanced metrics"""
    ts = datetime.now().isoformat(timespec='seconds')
    file_exists = os.path.exists("reminder_log.csv")
    
    with open("reminder_log.csv", mode="a", newline="") as f:
        writer = csv.writer(f)
        if not file_exists:
            # Write header once
            writer.writerow(["timestamp", "trigger", "ack", "blinks_last_min", "stress_level", "heart_rate", "drowsiness_score"])
        writer.writerow([ts, trigger, ack, blinks_last_min, stress_level, heart_rate, drowsiness_score])
