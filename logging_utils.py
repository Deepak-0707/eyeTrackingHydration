import csv
from datetime import datetime
from config import LOG_FILE

def log_event(trigger, ack, blinks_last_min):
    ts = datetime.now().isoformat(timespec='seconds')
    with open(LOG_FILE, mode="a", newline="") as f:
        writer = csv.writer(f)
        writer.writerow([ts, trigger, ack, blinks_last_min])
