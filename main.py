import warnings
warnings.filterwarnings("ignore", category=UserWarning, module='google.protobuf')

import tkinter as tk
from tkinter import messagebox
from app import EnhancedWellnessApp

def on_close(root, app):
    if messagebox.askokcancel("Quit", "Stop monitoring and exit?"):
        app.cam_running = False
        root.destroy()

def main():
    root = tk.Tk()
    app = EnhancedWellnessApp(root)
    root.protocol("WM_DELETE_WINDOW", lambda: on_close(root, app))
    root.mainloop()

if __name__ == "__main__":
    main()
