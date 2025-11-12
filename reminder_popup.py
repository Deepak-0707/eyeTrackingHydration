import os
import tkinter as tk
from tkinter import ttk
from datetime import datetime, timedelta
import pygame

class ReminderPopup(tk.Toplevel):
    def __init__(self, master, trigger_type, blinks_count, stress_level=0, heart_rate=0, sound_on=True):
        super().__init__(master)
        self.title("⚠ Health Alert")
        self.geometry("400x280")
        self.attributes("-topmost", True)
        self.resizable(False, False)
        
        self.acknowledged = False
        self.trigger_type = trigger_type
        
        # Alert icon and title based on trigger
        if "Drowsy" in trigger_type or "Sleep" in trigger_type:
            icon = "😴"
            title_text = "DROWSINESS DETECTED!"
            bg_color = "#ffebee"
        elif "Stress" in trigger_type:
            icon = "😰"
            title_text = "HIGH STRESS DETECTED!"
            bg_color = "#fff3e0"
        else:
            icon = "⚠"
            title_text = "Health Reminder"
            bg_color = "#e3f2fd"
        
        self.configure(bg=bg_color)
        
        # Title
        title_frame = tk.Frame(self, bg=bg_color)
        title_frame.pack(pady=(15,10), fill="x")
        
        label = tk.Label(title_frame, text=f"{icon} {title_text}", 
                        font=("Segoe UI", 14, "bold"),
                        bg=bg_color, fg="#d32f2f" if "Drowsy" in trigger_type else "#f57c00")
        label.pack()
        
        # Details
        details_frame = tk.Frame(self, bg=bg_color)
        details_frame.pack(pady=10, padx=20, fill="both", expand=True)
        
        detail_font = ("Segoe UI", 10)
        
        tk.Label(details_frame, text=f"Trigger: {trigger_type}", 
                font=detail_font, bg=bg_color, anchor="w").pack(fill="x", pady=2)
        tk.Label(details_frame, text=f"Blinks/min: {blinks_count}", 
                font=detail_font, bg=bg_color, anchor="w").pack(fill="x", pady=2)
        
        if stress_level > 0:
            tk.Label(details_frame, text=f"Stress Level: {stress_level}/100", 
                    font=detail_font, bg=bg_color, anchor="w").pack(fill="x", pady=2)
        
        if heart_rate > 0:
            tk.Label(details_frame, text=f"Heart Rate: {heart_rate} BPM", 
                    font=detail_font, bg=bg_color, anchor="w").pack(fill="x", pady=2)
        
        # Recommendations
        rec_frame = tk.Frame(self, bg=bg_color)
        rec_frame.pack(pady=10, padx=20, fill="x")
        
        if "Drowsy" in trigger_type:
            rec_text = "💡 Take a break! Stand up, stretch, splash water on face."
        elif "Stress" in trigger_type:
            rec_text = "💡 Deep breathing exercise: Inhale 4s, Hold 4s, Exhale 4s."
        else:
            rec_text = "💡 Remember: Blink regularly and stay hydrated!"
        
        tk.Label(rec_frame, text=rec_text, font=("Segoe UI", 9, "italic"),
                bg=bg_color, wraplength=350, justify="left").pack()
        
        # Buttons
        btn_frame = tk.Frame(self, bg=bg_color)
        btn_frame.pack(pady=15)
        
        tk.Button(btn_frame, text="✓ Got it", command=self.on_ack,
                 bg="#4caf50", fg="white", font=("Segoe UI", 10, "bold"),
                 padx=20, pady=8, relief="flat", cursor="hand2").grid(row=0, column=0, padx=8)
        
        tk.Button(btn_frame, text="⏰ Snooze 2 min", command=self.on_snooze,
                 bg="#ff9800", fg="white", font=("Segoe UI", 10),
                 padx=15, pady=8, relief="flat", cursor="hand2").grid(row=0, column=1, padx=8)
        
        # Auto-close timer
        self.after(20000, self.auto_close)
        
        # Play sound
        if sound_on:
            try:
                beep_file = "assets/beep.mp3"
                if os.path.exists(beep_file) and not pygame.mixer.music.get_busy():
                    pygame.mixer.music.load(beep_file)
                    # Play multiple times for drowsiness
                    if "Drowsy" in trigger_type:
                        pygame.mixer.music.play(3)  # Play 3 times
                    else:
                        pygame.mixer.music.play()
            except Exception as e:
                print(f"Sound error: {e}")
    
    def on_ack(self):
        self.acknowledged = True
        self.destroy()
    
    def on_snooze(self):
        self.acknowledged = False
        self.master.snooze_until = datetime.now() + timedelta(minutes=2)
        self.destroy()
    
    def auto_close(self):
        if self.winfo_exists():
            self.acknowledged = False
            self.destroy()

