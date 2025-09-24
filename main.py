import tkinter as tk
from tkinter import messagebox
from app import BlinkReminderApp

def on_close(root, app):
    if messagebox.askokcancel("Quit", "Do you want to quit?"):
        app.cam_running = False
        root.destroy()

def main():
    root = tk.Tk()
    app = BlinkReminderApp(root)
    root.protocol("WM_DELETE_WINDOW", lambda: on_close(root, app))
    root.mainloop()

if __name__ == "__main__":
    main()
