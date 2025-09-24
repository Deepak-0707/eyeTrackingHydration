import os, time, threading
import cv2
import pygame
import pandas as pd
import tkinter as tk
from tkinter import ttk, messagebox, DoubleVar, IntVar
from datetime import datetime
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import matplotlib.pyplot as plt

from config import *
from logging_utils import log_event
from reminder_popup import ReminderPopup
from eye_tracking import face_mesh, calculate_EAR, LEFT_EYE, RIGHT_EYE

try:
    from plyer import notification
    PLYER_AVAILABLE = True
except Exception:
    PLYER_AVAILABLE = False

pygame.mixer.init()
if os.path.exists(BEEP_FILE):
    try:
        pygame.mixer.music.load(BEEP_FILE)
    except Exception as e:
        print("Warning: couldn't load beep audio:", e)
else:
    print(f"Warning: {BEEP_FILE} not found. Sound alerts will be disabled.")

class BlinkReminderApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Hydration & Blink Reminder")
        self.root.geometry("480x300")
        self.root.resizable(False, False)

        self.interval_minutes = DEFAULT_INTERVAL_MIN
        self.sound_on = True
        self.blink_threshold = DEFAULT_BLINK_THRESHOLD
        self.ear_threshold = DEFAULT_EAR_THRESHOLD
        self.snooze_until = None

        self.consec_frames = CONSEC_FRAMES
        self.frame_counter = 0
        self.blink_count = 0
        self.blinks_timestamps = []
        self.last_reminder_time = datetime.now()

        self._build_ui()
        self.camera_thread = None
        self.cam_running = False

    def _build_ui(self):
        frm = ttk.Frame(self.root, padding=12)
        frm.pack(fill="both", expand=True)

        ttk.Label(frm, text="Hydration & Blink Reminder", font=("Segoe UI", 14, "bold")).pack(pady=(0,8))

        controls = ttk.Frame(frm)
        controls.pack(pady=6, fill="x")

        self.interval_var = DoubleVar(value=self.interval_minutes)
        ttk.Label(controls, text="Reminder interval (minutes):").grid(row=0, column=0, sticky="w")
        ttk.Entry(controls, textvariable=self.interval_var, width=8).grid(row=0, column=1, sticky="w", padx=(6, 14))

        self.blink_thresh_var = IntVar(value=self.blink_threshold)
        ttk.Label(controls, text="Blink threshold (blinks/min):").grid(row=1, column=0, sticky="w")
        ttk.Entry(controls, textvariable=self.blink_thresh_var, width=8).grid(row=1, column=1, sticky="w", padx=(6,14))

        self.ear_thresh_var = DoubleVar(value=self.ear_threshold)
        ttk.Label(controls, text="EAR threshold:").grid(row=2, column=0, sticky="w")
        ttk.Entry(controls, textvariable=self.ear_thresh_var, width=8).grid(row=2, column=1, sticky="w", padx=(6,14))

        self.sound_var = IntVar(value=1 if self.sound_on else 0)
        ttk.Checkbutton(controls, text="Sound alert", variable=self.sound_var).grid(row=0, column=2, rowspan=3, padx=(10,0), sticky="w")

        btn_frame = ttk.Frame(frm)
        btn_frame.pack(pady=14)
        self.start_btn = ttk.Button(btn_frame, text="Start Camera", command=self.start_camera)
        self.start_btn.grid(row=0, column=0, padx=8)
        self.stop_btn = ttk.Button(btn_frame, text="Stop Camera", command=self.stop_camera, state="disabled")
        self.stop_btn.grid(row=0, column=1, padx=8)
        ttk.Button(btn_frame, text="Show Stats", command=self.show_stats).grid(row=0, column=2, padx=8)

        info_frame = ttk.Frame(frm)
        info_frame.pack(pady=8, fill="x")
        self.ear_label = ttk.Label(info_frame, text="EAR: N/A")
        self.ear_label.pack(anchor="w")
        self.blinks_label = ttk.Label(info_frame, text="Blinks (total): 0")
        self.blinks_label.pack(anchor="w")
        self.status_label = ttk.Label(info_frame, text="Status: Idle", foreground="blue")
        self.status_label.pack(anchor="w")

    def start_camera(self):
        try:
            self.interval_minutes = float(self.interval_var.get())
            self.blink_threshold = int(self.blink_thresh_var.get())
            self.ear_threshold = float(self.ear_thresh_var.get())
            self.sound_on = bool(self.sound_var.get())
        except Exception:
            messagebox.showerror("Invalid settings", "Please enter valid numbers.")
            return

        self.cam_running = True
        self.start_btn.config(state="disabled")
        self.stop_btn.config(state="normal")
        self.status_label.config(text="Status: Camera running", foreground="green")

        self.camera_thread = threading.Thread(target=self._camera_loop, daemon=True)
        self.camera_thread.start()

    def stop_camera(self):
        self.cam_running = False
        self.start_btn.config(state="normal")
        self.stop_btn.config(state="disabled")
        self.status_label.config(text="Status: Stopped", foreground="red")

    def _camera_loop(self):
        cap = cv2.VideoCapture(0)
        if not cap.isOpened():
            messagebox.showerror("Camera error", "Could not open webcam.")
            self.stop_camera()
            return

        while self.cam_running:
            ret, frame = cap.read()
            if not ret:
                break

            frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            results = face_mesh.process(frame_rgb)
            h, w = frame.shape[:2]

            avg_ear = None
            if results.multi_face_landmarks:
                for face_landmarks in results.multi_face_landmarks:
                    left_ear = calculate_EAR(LEFT_EYE, face_landmarks.landmark, w, h)
                    right_ear = calculate_EAR(RIGHT_EYE, face_landmarks.landmark, w, h)
                    avg_ear = (left_ear + right_ear) / 2.0

                    if avg_ear < self.ear_threshold:
                        self.frame_counter += 1
                    else:
                        if self.frame_counter >= self.consec_frames:
                            self.blink_count += 1
                            self.blinks_timestamps.append(time.time())
                        self.frame_counter = 0

            now = time.time()
            self.blinks_timestamps = [t for t in self.blinks_timestamps if now - t <= 60.0]
            blinks_last_min = len(self.blinks_timestamps)

            self.root.after(0, self.ear_label.config, {"text": f"EAR: {avg_ear:.2f}" if avg_ear else "EAR: N/A"})
            self.root.after(0, self.blinks_label.config, {"text": f"Blinks (total): {self.blink_count} - last 60s: {blinks_last_min}"})

            if avg_ear:
                cv2.putText(frame, f"EAR: {avg_ear:.2f}", (30, 40), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0,255,0), 2)
            cv2.putText(frame, f"Blinks: {self.blink_count}", (30, 80), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0,0,255), 2)
            status_text = "Blinking" if self.frame_counter >= self.consec_frames else "Open"
            cv2.putText(frame, f"Status: {status_text}", (30, 120), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (255,0,0), 2)
            cv2.imshow("Blink Monitor", frame)

            if blinks_last_min < self.blink_threshold:
                if (datetime.now() - self.last_reminder_time).total_seconds() > 30:
                    if not self.snooze_until or datetime.now() >= self.snooze_until:
                        self.last_reminder_time = datetime.now()
                        self._trigger_reminder("Blink rate low", blinks_last_min)

            interval_seconds = self.interval_minutes * 60.0
            if (datetime.now() - self.last_reminder_time).total_seconds() >= interval_seconds:
                if not self.snooze_until or datetime.now() >= self.snooze_until:
                    self.last_reminder_time = datetime.now()
                    self._trigger_reminder("Timer", blinks_last_min)

            if cv2.waitKey(1) & 0xFF == ord('q'):
                self.cam_running = False
                break

        cap.release()
        cv2.destroyAllWindows()
        self.root.after(0, self.stop_camera)

    def _trigger_reminder(self, trigger_type, blinks_last_min):
        if PLYER_AVAILABLE:
            try:
                notification.notify(title="Blink Reminder", message=f"{trigger_type}. Blinks/min: {blinks_last_min}", timeout=5)
            except Exception:
                pass

        popup_result = {}
        def show_popup():
            popup = ReminderPopup(self.root, trigger_type, blinks_last_min, sound_on=self.sound_on)
            self.root.wait_window(popup)
            popup_result['ack'] = getattr(popup, "acknowledged", False)
        self.root.after(0, show_popup)

        start_wait = time.time()
        while 'ack' not in popup_result and (time.time() - start_wait) < (POPUP_AUTO_CLOSE_S + 5):
            time.sleep(0.2)

        ack = popup_result.get('ack', False)
        log_event(trigger_type, "ack" if ack else "ignored", blinks_last_min)

    def show_stats(self):
        if not os.path.exists(LOG_FILE):
            messagebox.showinfo("No data", "No log data yet.")
            return

        df = pd.read_csv(LOG_FILE, parse_dates=["timestamp"])
        if df.empty:
            messagebox.showinfo("No data", "No log data yet.")
            return

        df['date'] = df['timestamp'].dt.date
        summary = df.groupby('date').agg(total=('timestamp','count'),
                                         acknowledged=('ack', lambda s: (s=='ack').sum()))
        summary['ack_rate'] = (summary['acknowledged'] / summary['total']) * 100

        win = tk.Toplevel(self.root)
        win.title("Usage Statistics")
        win.geometry("700x420")
        fig, axs = plt.subplots(2, 1, figsize=(7,6))
        dates = list(summary.index.astype(str))
        axs[0].bar(dates, summary['total'])
        axs[0].set_title("Reminders per day")
        axs[0].set_ylabel("Count")
        axs[1].plot(dates, summary['ack_rate'], marker='o')
        axs[1].set_title("Acknowledgement Rate (%)")
        axs[1].set_ylabel("% Ack")
        plt.tight_layout()

        canvas = FigureCanvasTkAgg(fig, master=win)
        canvas.draw()
        canvas.get_tk_widget().pack(fill="both", expand=True)
