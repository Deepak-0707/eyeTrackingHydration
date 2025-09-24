import os
import tkinter as tk
from tkinter import ttk
from datetime import datetime, timedelta
import pygame
from config import BEEP_FILE, POPUP_AUTO_CLOSE_S

class ReminderPopup(tk.Toplevel):
    def __init__(self, master, trigger_type, blinks_count, sound_on=True):
        super().__init__(master)
        self.title("⚠ Blink Reminder")
        self.geometry("350x160")
        self.attributes("-topmost", True)
        self.resizable(False, False)
        self.acknowledged = False
        self.trigger_type = trigger_type
        self.blinks_count = blinks_count

        label = ttk.Label(self, text="⚠ Time to blink / hydrate!", font=("Segoe UI", 12, "bold"))
        label.pack(pady=(12,6))
        sub = ttk.Label(self, text=f"Triggered by: {trigger_type}\nBlinks last minute: {blinks_count}", font=("Segoe UI", 10))
        sub.pack(pady=(0,12))
        btn_frame = ttk.Frame(self)
        btn_frame.pack(pady=6)
        got_it = ttk.Button(btn_frame, text="Got it", command=self.on_ack)
        got_it.grid(row=0, column=0, padx=8)
        snooze = ttk.Button(btn_frame, text="Snooze 2 min", command=self.on_snooze)
        snooze.grid(row=0, column=1, padx=8)

        
        self.after(POPUP_AUTO_CLOSE_S * 1000, self.auto_close)

        if sound_on and os.path.exists(BEEP_FILE):
            try:
                if not pygame.mixer.music.get_busy():
                    pygame.mixer.music.play()
            except Exception:
                pass

    def on_ack(self):
        self.acknowledged = True
        self.destroy()

    def on_snooze(self):
        self.acknowledged = False
        self.master.snooze_until = datetime.now() + timedelta(minutes=2)
        self.destroy()

    def auto_close(self):
        if not self.winfo_exists():
            return
        self.acknowledged = False
        self.destroy()
