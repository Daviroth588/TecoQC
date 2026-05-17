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

from config import APP_TITLE, WINDOW_WIDTH, WINDOW_HEIGHT, get_data_dir, is_usb_mode
from ui.wizard_manager import WizardManager


def _check_session_recovery(root):
    """Si hay una sesión guardada, ofrece restaurarla."""
    import json
    from tkinter import messagebox
    session_path = os.path.join(get_data_dir(), "session.json")
    if not os.path.exists(session_path):
        return
    try:
        with open(session_path, "r", encoding="utf-8") as f:
            saved = json.load(f)
        if not saved.get("technician_name") and not saved.get("device_serial"):
            os.remove(session_path)
            return
        tech = saved.get("technician_name", "?")
        serial = saved.get("device_serial", "?")
        date = saved.get("report_date", "?")
        if messagebox.askyesno(
            "Sesión anterior encontrada",
            f"Se encontró una sesión guardada:\n\n"
            f"Técnico: {tech}\nS/N: {serial}\nFecha: {date}\n\n"
            "¿Desea continuar desde donde dejó?",
            icon="question"
        ):
            # Session will be loaded after WizardManager init
            root._saved_session = saved
        else:
            os.remove(session_path)
            root._saved_session = None
    except Exception:
        try:
            os.remove(session_path)
        except Exception:
            pass


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

    # Check for unfinished session
    _check_session_recovery(root)

    # Build the main wizard UI
    app = WizardManager(root)
    app.pack(fill=tk.BOTH, expand=True)

    # Show USB mode indicator in title bar
    if is_usb_mode():
        root.title(APP_TITLE + "  [MODO USB — datos guardados en USB]")

    # Auto-save session state every 30s
    def _autosave():
        try:
            import json
            session_path = os.path.join(get_data_dir(), "session.json")
            with open(session_path, "w", encoding="utf-8") as f:
                json.dump(app._state, f, ensure_ascii=False, default=str)
        except Exception:
            pass
        root.after(30000, _autosave)

    root.after(30000, _autosave)

    root.mainloop()


if __name__ == "__main__":
    main()
