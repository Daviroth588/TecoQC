"""
TecoQC - Sistema de Control de Calidad
Tecology
Punto de entrada principal de la aplicación
"""

import sys
import os
import tkinter as tk
from tkinter import messagebox

# Ensure the project root is on the path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from config import APP_TITLE, WINDOW_WIDTH, WINDOW_HEIGHT
from ui.wizard_manager import WizardManager


def main():
    root = tk.Tk()
    root.title(APP_TITLE)
    root.geometry(f"{WINDOW_WIDTH}x{WINDOW_HEIGHT}")
    root.minsize(1000, 650)

    # Center the window on screen
    root.update_idletasks()
    screen_w = root.winfo_screenwidth()
    screen_h = root.winfo_screenheight()
    x = (screen_w - WINDOW_WIDTH) // 2
    y = (screen_h - WINDOW_HEIGHT) // 2
    root.geometry(f"{WINDOW_WIDTH}x{WINDOW_HEIGHT}+{x}+{y}")

    # Set dark background immediately to avoid white flash
    root.configure(bg="#1e1e2e")

    # Try to set icon
    try:
        icon_path = os.path.join(os.path.dirname(__file__), "assets", "logo.ico")
        if os.path.exists(icon_path):
            root.iconbitmap(icon_path)
    except Exception:
        pass

    # Handle close event
    def on_close():
        if messagebox.askyesno(
            "Salir",
            "¿Desea salir de TecoQC?\nSe perderá el progreso no guardado.",
            icon="warning"
        ):
            root.destroy()

    root.protocol("WM_DELETE_WINDOW", on_close)

    # Build the main wizard UI
    app = WizardManager(root)
    app.pack(fill=tk.BOTH, expand=True)

    root.mainloop()


if __name__ == "__main__":
    main()
