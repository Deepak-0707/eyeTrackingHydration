import os, time, threading
import cv2
import pygame
import pandas as pd
import tkinter as tk
from tkinter import ttk, messagebox, DoubleVar, IntVar, StringVar
from datetime import datetime
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import matplotlib.pyplot as plt

# Import modules (assume all above classes are imported)
from eye_tracking import face_mesh, calculate_EAR, extract_stress_features, LEFT_EYE, RIGHT_EYE
from stress_detector import StressDetector
from heart_rate_monitor import HeartRateMonitor
from music_therapy import MusicTherapy
from logging_utils import log_event
from reminder_popup import ReminderPopup

try:
    from plyer import notification
    PLYER_AVAILABLE = True
except Exception:
    PLYER_AVAILABLE = False

pygame.mixer.init()

class EnhancedWellnessApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Enhanced Eye Health & Wellness Monitor")
        self.root.geometry("650x600")
        self.root.resizable(False, False)
        
        # Basic settings
        self.interval_minutes = 20
        self.sound_on = True
        self.blink_threshold = 8
        self.ear_threshold = 0.21
        self.snooze_until = None
        self.consec_frames = 3
        
        # NEW: Adjustable alert timing (in UI)
        self.eye_closure_alert_time = 20.0  # seconds
        self.stress_sustained_time = 20.0   # seconds
        
        # Blink tracking
        self.frame_counter = 0
        self.blink_count = 0
        self.blinks_timestamps = []
        self.last_reminder_time = datetime.now()
        
        # Drowsiness tracking
        self.eyes_closed_start = None
        self.eyes_open_start = None
        self.drowsy_state = False
        self.drowsiness_score = 0
        self.last_drowsy_beep = 0
        
        # Stress tracking with sustained timer
        self.high_stress_start = None
        self.last_stress_alert = 0
        
        # Advanced modules
        self.stress_detector = StressDetector()
        self.hr_monitor = HeartRateMonitor()
        self.music_therapy = MusicTherapy()
        
        # Current metrics
        self.current_stress = 0
        self.current_hr = 0
        
        # Camera
        self.camera_thread = None
        self.cam_running = False
        
        self._build_ui()
    
    def _build_ui(self):
        """Build enhanced UI"""
        main_frame = ttk.Frame(self.root, padding=15)
        main_frame.pack(fill="both", expand=True)
        
        # Title
        title = ttk.Label(main_frame, text="🏥 Enhanced Wellness Monitor", 
                         font=("Segoe UI", 16, "bold"))
        title.pack(pady=(0, 15))
        
        # Settings Frame
        settings_frame = ttk.LabelFrame(main_frame, text="⚙ Settings", padding=10)
        settings_frame.pack(fill="x", pady=5)
        
        # Row 1
        row1 = ttk.Frame(settings_frame)
        row1.pack(fill="x", pady=3)
        
        self.interval_var = DoubleVar(value=20)
        ttk.Label(row1, text="Reminder interval (min):").pack(side="left")
        ttk.Entry(row1, textvariable=self.interval_var, width=8).pack(side="left", padx=5)
        
        self.sound_var = IntVar(value=1)
        ttk.Checkbutton(row1, text="🔊 Sound alerts", 
                       variable=self.sound_var).pack(side="left", padx=20)
        
        # Row 2
        row2 = ttk.Frame(settings_frame)
        row2.pack(fill="x", pady=3)
        
        self.blink_thresh_var = IntVar(value=8)
        ttk.Label(row2, text="Blink threshold:").pack(side="left")
        ttk.Entry(row2, textvariable=self.blink_thresh_var, width=8).pack(side="left", padx=5)
        
        self.ear_thresh_var = DoubleVar(value=0.21)
        ttk.Label(row2, text="EAR threshold:").pack(side="left", padx=(20, 5))
        ttk.Entry(row2, textvariable=self.ear_thresh_var, width=8).pack(side="left", padx=5)
        
        # Row 3 - NEW: Alert timing controls
        row3 = ttk.Frame(settings_frame)
        row3.pack(fill="x", pady=3)
        
        self.eye_alert_var = DoubleVar(value=20)
        ttk.Label(row3, text="Eye closure alert (sec):").pack(side="left")
        ttk.Entry(row3, textvariable=self.eye_alert_var, width=8).pack(side="left", padx=5)
        
        self.stress_alert_var = DoubleVar(value=20)
        ttk.Label(row3, text="Stress alert (sec):").pack(side="left", padx=(20, 5))
        ttk.Entry(row3, textvariable=self.stress_alert_var, width=8).pack(side="left", padx=5)
        
        # Control Buttons
        btn_frame = ttk.Frame(main_frame)
        btn_frame.pack(pady=15)
        
        self.start_btn = ttk.Button(btn_frame, text="▶ Start Monitoring", 
                                    command=self.start_camera, width=15)
        self.start_btn.grid(row=0, column=0, padx=5)
        
        self.stop_btn = ttk.Button(btn_frame, text="⏹ Stop", 
                                   command=self.stop_camera, width=15, state="disabled")
        self.stop_btn.grid(row=0, column=1, padx=5)
        
        ttk.Button(btn_frame, text="📊 Statistics", 
                  command=self.show_stats, width=15).grid(row=0, column=2, padx=5)
        
        # Real-time Metrics Dashboard
        metrics_frame = ttk.LabelFrame(main_frame, text="📈 Real-time Metrics", padding=10)
        metrics_frame.pack(fill="both", expand=True, pady=5)
        
        # Create grid for metrics
        # Column 1: Eye Health
        col1 = ttk.Frame(metrics_frame)
        col1.grid(row=0, column=0, padx=10, sticky="n")
        
        ttk.Label(col1, text="👁️ Eye Health", font=("Segoe UI", 10, "bold")).pack()
        self.ear_label = ttk.Label(col1, text="EAR: N/A", font=("Segoe UI", 9))
        self.ear_label.pack(anchor="w", pady=2)
        self.blinks_label = ttk.Label(col1, text="Blinks: 0", font=("Segoe UI", 9))
        self.blinks_label.pack(anchor="w", pady=2)
        self.blink_rate_label = ttk.Label(col1, text="Rate: 0/min", font=("Segoe UI", 9))
        self.blink_rate_label.pack(anchor="w", pady=2)
        
        # Column 2: Drowsiness
        col2 = ttk.Frame(metrics_frame)
        col2.grid(row=0, column=1, padx=10, sticky="n")
        
        ttk.Label(col2, text="😴 Drowsiness", font=("Segoe UI", 10, "bold")).pack()
        self.drowsy_label = ttk.Label(col2, text="State: Alert", 
                                     font=("Segoe UI", 9), foreground="green")
        self.drowsy_label.pack(anchor="w", pady=2)
        self.drowsy_score_label = ttk.Label(col2, text="Score: 0/100", font=("Segoe UI", 9))
        self.drowsy_score_label.pack(anchor="w", pady=2)
        self.eye_closure_label = ttk.Label(col2, text="Closure: 0.0s", font=("Segoe UI", 9))
        self.eye_closure_label.pack(anchor="w", pady=2)
        
        # Column 3: Stress
        col3 = ttk.Frame(metrics_frame)
        col3.grid(row=0, column=2, padx=10, sticky="n")
        
        ttk.Label(col3, text="😰 Stress Level", font=("Segoe UI", 10, "bold")).pack()
        self.stress_label = ttk.Label(col3, text="Level: Low", 
                                     font=("Segoe UI", 9), foreground="green")
        self.stress_label.pack(anchor="w", pady=2)
        self.stress_score_label = ttk.Label(col3, text="Score: 0/100", font=("Segoe UI", 9))
        self.stress_score_label.pack(anchor="w", pady=2)
        self.music_label = ttk.Label(col3, text="🎵 Music: Off", font=("Segoe UI", 9))
        self.music_label.pack(anchor="w", pady=2)
        
        # Column 4: Heart Rate
        col4 = ttk.Frame(metrics_frame)
        col4.grid(row=0, column=3, padx=10, sticky="n")
        
        ttk.Label(col4, text="💓 Heart Rate", font=("Segoe UI", 10, "bold")).pack()
        self.hr_label = ttk.Label(col4, text="HR: -- BPM", font=("Segoe UI", 9))
        self.hr_label.pack(anchor="w", pady=2)
        self.hrv_label = ttk.Label(col4, text="HRV: -- ms", font=("Segoe UI", 9))
        self.hrv_label.pack(anchor="w", pady=2)
        self.hr_status_label = ttk.Label(col4, text="Status: Measuring", font=("Segoe UI", 9))
        self.hr_status_label.pack(anchor="w", pady=2)
        
        # Overall Status
        status_frame = ttk.Frame(main_frame)
        status_frame.pack(fill="x", pady=10)
        
        self.status_label = ttk.Label(status_frame, text="Status: Idle", 
                                     font=("Segoe UI", 11, "bold"), 
                                     foreground="blue")
        self.status_label.pack()
    
    def start_camera(self):
        """Start camera and monitoring"""
        try:
            self.interval_minutes = float(self.interval_var.get())
            self.blink_threshold = int(self.blink_thresh_var.get())
            self.ear_threshold = float(self.ear_thresh_var.get())
            self.sound_on = bool(self.sound_var.get())
            self.eye_closure_alert_time = float(self.eye_alert_var.get())
            self.stress_sustained_time = float(self.stress_alert_var.get())
        except Exception:
            messagebox.showerror("Invalid settings", "Please enter valid numbers.")
            return
        
        self.cam_running = True
        self.start_btn.config(state="disabled")
        self.stop_btn.config(state="normal")
        self.status_label.config(text="Status: 🟢 Monitoring Active", foreground="green")
        
        self.camera_thread = threading.Thread(target=self._camera_loop, daemon=True)
        self.camera_thread.start()
    
    def stop_camera(self):
        """Stop camera and monitoring"""
        self.cam_running = False
        self.start_btn.config(state="normal")
        self.stop_btn.config(state="disabled")
        self.status_label.config(text="Status: 🔴 Stopped", foreground="red")
        self.music_therapy.stop_music()
    
    def _camera_loop(self):
        """Main camera processing loop with all features"""
        cap = cv2.VideoCapture(0)
        
        if not cap.isOpened():
            messagebox.showerror("Camera error", "Could not open webcam.")
            self.stop_camera()
            return
        
        frame_count = 0
        last_hr_update = time.time()
        
        while self.cam_running:
            ret, frame = cap.read()
            if not ret:
                break
            
            frame_count += 1
            frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            results = face_mesh.process(frame_rgb)
            
            h, w = frame.shape[:2]
            avg_ear = None
            stress_features = None
            
            if results.multi_face_landmarks:
                for face_landmarks in results.multi_face_landmarks:
                    # 1. EYE TRACKING & BLINK DETECTION
                    left_ear = calculate_EAR(LEFT_EYE, face_landmarks.landmark, w, h)
                    right_ear = calculate_EAR(RIGHT_EYE, face_landmarks.landmark, w, h)
                    avg_ear = (left_ear + right_ear) / 2.0
                    
                    # Blink detection
                    if avg_ear < self.ear_threshold:
                        self.frame_counter += 1
                    else:
                        if self.frame_counter >= self.consec_frames:
                            self.blink_count += 1
                            self.blinks_timestamps.append(time.time())
                        self.frame_counter = 0
                    
                    # 2. DROWSINESS DETECTION (FIXED)
                    self._detect_drowsiness(avg_ear)
                    
                    # 3. STRESS DETECTION (FIXED)
                    stress_features = extract_stress_features(face_landmarks.landmark, w, h)
                    self.current_stress = self.stress_detector.calculate_stress(stress_features)
                    
                    # Track sustained high stress
                    self._track_sustained_stress()
                    
                    # 4. HEART RATE MONITORING (FIXED)
                    self.hr_monitor.add_frame(frame, face_landmarks, w, h)
                    
                    # Update heart rate every 5 seconds
                    if time.time() - last_hr_update > 5:
                        self.current_hr = self.hr_monitor.calculate_heart_rate()
                        last_hr_update = time.time()
            
            # Clean old blink timestamps
            now = time.time()
            self.blinks_timestamps = [t for t in self.blinks_timestamps if now - t <= 60.0]
            blinks_last_min = len(self.blinks_timestamps)
            
            # Update UI
            self._update_ui(avg_ear, blinks_last_min)
            
            # Update music therapy (FIXED - only plays after 20 seconds)
            self._update_music_therapy()
            
            # Draw on frame
            self._draw_on_frame(frame, avg_ear, blinks_last_min)
            
            cv2.imshow("Wellness Monitor", frame)
            
            # Check for alerts
            self._check_alerts(blinks_last_min)
            
            if cv2.waitKey(1) & 0xFF == ord('q'):
                self.cam_running = False
                break
        
        cap.release()
        cv2.destroyAllWindows()
        self.root.after(0, self.stop_camera)
    
    def _track_sustained_stress(self):
        """Track sustained high stress levels"""
        current_time = time.time()
        
        if self.current_stress >= 70:
            if self.high_stress_start is None:
                self.high_stress_start = current_time
        else:
            self.high_stress_start = None
    
    def _update_music_therapy(self):
        """Update music - only play after sustained high stress"""
        current_time = time.time()
        stress_text = self.stress_detector.get_stress_level_text(self.current_stress)
        
        # Only play music if stress has been high for sustained time
        if self.high_stress_start is not None:
            stress_duration = current_time - self.high_stress_start
            
            if stress_duration >= self.stress_sustained_time:
                # Play music
                if not self.music_therapy.is_playing:
                    self.music_therapy.update_stress_level(self.current_stress, stress_text)
            else:
                # Not sustained long enough yet
                self.music_therapy.stop_music()
        else:
            # Stress not high anymore
            self.music_therapy.stop_music()
    
    def _detect_drowsiness(self, avg_ear):
        """Detect drowsiness based on eye closure duration (FIXED)"""
        if avg_ear is None:
            return
        
        current_time = time.time()
        
        # Eyes closed
        if avg_ear < self.ear_threshold:
            if self.eyes_closed_start is None:
                self.eyes_closed_start = current_time
            
            self.eyes_open_start = None  # Reset open timer
            
            closed_duration = current_time - self.eyes_closed_start
            
            # Calculate drowsiness score (0-100)
            self.drowsiness_score = min(100, int((closed_duration / 4.0) * 100))
            
            # Alert when eyes closed for configured time
            if closed_duration >= self.eye_closure_alert_time:
                if current_time - self.last_drowsy_beep >= 3.0:
                    self.last_drowsy_beep = current_time
                    self._play_beep_sound()  # FIXED: Audible beep
                    
                    if not self.drowsy_state:
                        self.drowsy_state = True
                        self._trigger_reminder("Drowsiness Detected", 0)
        
        else:
            # Eyes open
            if self.eyes_open_start is None:
                self.eyes_open_start = current_time
            
            self.eyes_closed_start = None  # Reset closed timer
            self.drowsy_state = False
            self.drowsiness_score = max(0, self.drowsiness_score - 5)  # Decay score
            
            # Alert if eyes open for too long (staring)
            open_duration = current_time - self.eyes_open_start
            if open_duration >= self.eye_closure_alert_time:
                if current_time - self.last_drowsy_beep >= 10.0:
                    self.last_drowsy_beep = current_time
                    self._play_beep_sound()  # FIXED: Audible beep
    
    def _play_beep_sound(self):
        """Play beep sound (FIXED - audible)"""
        try:
            beep_file = "assets/beep.mp3"
            if os.path.exists(beep_file) and self.sound_on:
                # Stop music temporarily
                music_was_playing = self.music_therapy.is_playing
                if music_was_playing:
                    pygame.mixer.music.pause()
                
                # Play beep using a separate channel
                beep_sound = pygame.mixer.Sound(beep_file)
                beep_sound.set_volume(1.0)  # Full volume
                beep_sound.play()
                
                # Resume music after beep
                if music_was_playing:
                    time.sleep(0.5)  # Wait for beep
                    pygame.mixer.music.unpause()
        except Exception as e:
            print(f"Beep error: {e}")
    
    def _update_ui(self, avg_ear, blinks_last_min):
        """Update all UI elements"""
        # Eye metrics
        ear_text = f"EAR: {avg_ear:.3f}" if avg_ear else "EAR: N/A"
        self.root.after(0, self.ear_label.config, {"text": ear_text})
        
        self.root.after(0, self.blinks_label.config, 
                       {"text": f"Blinks: {self.blink_count}"})
        
        self.root.after(0, self.blink_rate_label.config, 
                       {"text": f"Rate: {blinks_last_min}/min"})
        
        # Drowsiness
        if self.drowsiness_score > 70:
            drowsy_state = "😴 SLEEPING"
            drowsy_color = "red"
        elif self.drowsiness_score > 40:
            drowsy_state = "😪 Drowsy"
            drowsy_color = "orange"
        else:
            drowsy_state = "✅ Alert"
            drowsy_color = "green"
        
        self.root.after(0, self.drowsy_label.config, 
                       {"text": f"State: {drowsy_state}", "foreground": drowsy_color})
        
        self.root.after(0, self.drowsy_score_label.config, 
                       {"text": f"Score: {self.drowsiness_score}/100"})
        
        closure_time = 0
        if self.eyes_closed_start:
            closure_time = time.time() - self.eyes_closed_start
        
        self.root.after(0, self.eye_closure_label.config, 
                       {"text": f"Closure: {closure_time:.1f}s"})
        
        # Stress
        stress_text = self.stress_detector.get_stress_level_text(self.current_stress)
        stress_color = "green" if self.current_stress < 40 else \
                      "orange" if self.current_stress < 70 else "red"
        
        self.root.after(0, self.stress_label.config, 
                       {"text": f"Level: {stress_text}", "foreground": stress_color})
        
        self.root.after(0, self.stress_score_label.config, 
                       {"text": f"Score: {self.current_stress}/100"})
        
        music_status = "🎵 Playing" if self.music_therapy.is_playing else "🎵 Off"
        self.root.after(0, self.music_label.config, {"text": music_status})
        
        # Heart rate (FIXED - better calibration)
        if self.current_hr > 0:
            hr_text = f"HR: {self.current_hr} BPM"
            hrv = self.hr_monitor.get_hr_variability()
            hrv_text = f"HRV: {hrv} ms"
            
            if self.current_hr < 60:
                hr_status = "Low"
            elif self.current_hr > 100:
                hr_status = "High"
            else:
                hr_status = "Normal"
        else:
            hr_text = "HR: Measuring..."
            hrv_text = "HRV: --"
            hr_status = "Buffering"
        
        self.root.after(0, self.hr_label.config, {"text": hr_text})
        self.root.after(0, self.hrv_label.config, {"text": hrv_text})
        self.root.after(0, self.hr_status_label.config, {"text": f"Status: {hr_status}"})
    
    def _draw_on_frame(self, frame, avg_ear, blinks_last_min):
        """Draw metrics on video frame"""
        # EAR
        if avg_ear:
            color = (0, 255, 0) if avg_ear > self.ear_threshold else (0, 0, 255)
            cv2.putText(frame, f"EAR: {avg_ear:.2f}", (30, 40),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.7, color, 2)
        
        # Blinks
        cv2.putText(frame, f"Blinks: {self.blink_count} ({blinks_last_min}/min)", 
                   (30, 70), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 0, 0), 2)
        
        # Drowsiness warning
        if self.drowsiness_score > 40:
            warning_text = "DROWSY!" if self.drowsiness_score < 70 else "SLEEPING!"
            cv2.putText(frame, warning_text, (30, 110),
                       cv2.FONT_HERSHEY_SIMPLEX, 1.0, (0, 0, 255), 3)
        
        # Stress level
        stress_text = self.stress_detector.get_stress_level_text(self.current_stress)
        stress_color = (0, 255, 0) if self.current_stress < 30 else \
                      (0, 165, 255) if self.current_stress < 50 else (0, 0, 255)
        
        cv2.putText(frame, f"Stress: {stress_text} ({self.current_stress})", 
                   (30, 140), cv2.FONT_HERSHEY_SIMPLEX, 0.7, stress_color, 2)
        
        # Heart rate
        if self.current_hr > 0:
            cv2.putText(frame, f"HR: {self.current_hr} BPM", 
                       (30, 170), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 0, 255), 2)
    
    def _check_alerts(self, blinks_last_min):
        """Check all alert conditions"""
        current_time = datetime.now()
        
        # Skip if snoozed
        if self.snooze_until and current_time < self.snooze_until:
            return
        
        # 1. Low blink rate alert
        if blinks_last_min < self.blink_threshold:
            if (current_time - self.last_reminder_time).total_seconds() > 30:
                self.last_reminder_time = current_time
                self._trigger_reminder("Low Blink Rate", blinks_last_min)
        
        # 2. High stress alert (FIXED - only after sustained time)
        if self.high_stress_start is not None:
            stress_duration = time.time() - self.high_stress_start
            
            if stress_duration >= self.stress_sustained_time:
                if (current_time - self.last_reminder_time).total_seconds() > 60:
                    self.last_reminder_time = current_time
                    self._trigger_reminder("High Stress Level", blinks_last_min)
        
        # 3. Regular interval reminder
        interval_seconds = self.interval_minutes * 60.0
        if (current_time - self.last_reminder_time).total_seconds() >= interval_seconds:
            self.last_reminder_time = current_time
            self._trigger_reminder("Scheduled Reminder", blinks_last_min)
    
    def _trigger_reminder(self, trigger_type, blinks_last_min):
        """Trigger reminder popup"""
        if PLYER_AVAILABLE:
            try:
                notification.notify(
                    title="Wellness Alert",
                    message=f"{trigger_type}",
                    timeout=5
                )
            except Exception:
                pass
        
        popup_result = {}
        
        def show_popup():
            popup = ReminderPopup(
                self.root, 
                trigger_type, 
                blinks_last_min,
                self.current_stress,
                self.current_hr,
                sound_on=self.sound_on
            )
            self.root.wait_window(popup)
            popup_result['ack'] = getattr(popup, "acknowledged", False)
        
        self.root.after(0, show_popup)
        
        # Wait for acknowledgment
        start_wait = time.time()
        while 'ack' not in popup_result and (time.time() - start_wait) < 25:
            time.sleep(0.2)
        
        ack = popup_result.get('ack', False)
        
        # Log event
        log_event(trigger_type, "ack" if ack else "ignored", 
                 blinks_last_min, self.current_stress, 
                 self.current_hr, self.drowsiness_score)
    
    def show_stats(self):
        """Show enhanced statistics (FIXED)"""
        log_file = "reminder_log.csv"
        
        if not os.path.exists(log_file):
            messagebox.showinfo("No data", "No log data available yet.")
            return
        
        try:
            # Read CSV with flexible parsing
            df = pd.read_csv(log_file)
            
            # Convert timestamp column
            if 'timestamp' in df.columns:
                df['timestamp'] = pd.to_datetime(df['timestamp'], errors='coerce')
            else:
                messagebox.showerror("Error", "Missing 'timestamp' column in log file.")
                return
        except Exception as e:
            messagebox.showerror("Error", f"Could not load data: {e}")
            return
        
        if df.empty:
            messagebox.showinfo("No data", "No log data available yet.")
            return
        
        # Prepare data
        df['date'] = df['timestamp'].dt.date
        
        # Daily summary
        daily = df.groupby('date').agg({
            'timestamp': 'count',
            'ack': lambda x: (x == 'ack').sum(),
            'stress_level': 'mean',
            'heart_rate': 'mean',
            'drowsiness_score': 'mean'
        }).rename(columns={'timestamp': 'total', 'ack': 'acknowledged'})
        
        daily['ack_rate'] = (daily['acknowledged'] / daily['total']) * 100
        
        # Create statistics window
        win = tk.Toplevel(self.root)
        win.title("📊 Wellness Statistics")
        win.geometry("900x600")
        
        # Create plots
        fig, axs = plt.subplots(2, 2, figsize=(12, 8))
        
        dates = [str(d) for d in daily.index]
        
        # Plot 1: Reminders per day
        axs[0, 0].bar(dates, daily['total'], color='#2196F3')
        axs[0, 0].set_title('Reminders per Day')
        axs[0, 0].set_ylabel('Count')
        axs[0, 0].tick_params(axis='x', rotation=45)
        
        # Plot 2: Acknowledgment rate
        axs[0, 1].plot(dates, daily['ack_rate'], marker='o', color='#4CAF50')
        axs[0, 1].set_title('Acknowledgment Rate')
        axs[0, 1].set_ylabel('% Acknowledged')
        axs[0, 1].tick_params(axis='x', rotation=45)
        axs[0, 1].set_ylim([0, 105])
        
        # Plot 3: Average stress level
        axs[1, 0].plot(dates, daily['stress_level'], marker='s', color='#FF9800')
        axs[1, 0].set_title('Average Stress Level')
        axs[1, 0].set_ylabel('Stress (0-100)')
        axs[1, 0].tick_params(axis='x', rotation=45)
        axs[1, 0].axhline(y=70, color='r', linestyle='--', alpha=0.5, label='High')
        axs[1, 0].axhline(y=40, color='y', linestyle='--', alpha=0.5, label='Medium')
        axs[1, 0].legend()
        
        # Plot 4: Average heart rate
        axs[1, 1].plot(dates, daily['heart_rate'], marker='^', color='#E91E63')
        axs[1, 1].set_title('Average Heart Rate')
        axs[1, 1].set_ylabel('BPM')
        axs[1, 1].tick_params(axis='x', rotation=45)
        axs[1, 1].axhline(y=100, color='r', linestyle='--', alpha=0.5, label='High')
        axs[1, 1].axhline(y=60, color='g', linestyle='--', alpha=0.5, label='Normal')
        axs[1, 1].legend()
        
        plt.tight_layout()
        
        canvas = FigureCanvasTkAgg(fig, master=win)
        canvas.draw()
        canvas.get_tk_widget().pack(fill="both", expand=True)