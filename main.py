# main.py — Entry point for Blast Design Calculator
import tkinter as tk
from gui_app import BlastCalculatorApp


def main():
    root = tk.Tk()
    root.resizable(True, True)
    try:
        root.iconbitmap(default="")   # suppress icon error on some systems
    except Exception:
        pass
    BlastCalculatorApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()