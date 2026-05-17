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


def _ensure_admin():
    """Si no se ejecuta como Administrador, re-lanza el proceso con elevación UAC."""
    try:
        import ctypes
        if ctypes.windll.shell32.IsUserAnAdmin():
            return  # Ya es administrador
    except Exception:
        return  # No es Windows, ignorar

    # No es admin — re-lanzar con ShellExecute runas (dispara UAC)
    try:
        import ctypes
        if getattr(sys, "frozen", False):
            # Ejecutable PyInstaller: re-lanzar el mismo .exe
            exe = sys.executable
            params = " ".join(f'"{a}"' for a in sys.argv[1:])
        else:
            # Script Python: re-lanzar python.exe con el mismo script
            exe = sys.executable
            params = " ".join(f'"{a}"' for a in sys.argv)

        ret = ctypes.windll.shell32.ShellExecuteW(None, "runas", exe, params, None, 1)
        if ret > 32:
            sys.exit(0)  # Re-lanzamiento exitoso, cerrar este proceso
        # Si ret <= 32 el usuario canceló el UAC — continuar de todos modos
    except SystemExit:
        raise
    except Exception:
        pass  # Si falla, continuar sin admin


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
    # Solicitar privilegios de Administrador antes de crear la ventana
    _ensure_admin()

    from ui.wizard_manager import WizardManager

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

    root.configure(bg="#1e1e2e")

    try:
        icon_path = os.path.join(os.path.dirname(__file__), "assets", "logo.ico")
        if os.path.exists(icon_path):
            root.iconbitmap(icon_path)
    except Exception:
        pass

    def on_close():
        if messagebox.askyesno(
            "Salir",
            "¿Desea salir de TecoQC?\nSe perderá el progreso no guardado.",
            icon="warning"
        ):
            root.destroy()

    root.protocol("WM_DELETE_WINDOW", on_close)

    _check_session_recovery(root)

    app = WizardManager(root)
    app.pack(fill=tk.BOTH, expand=True)

    if is_usb_mode():
        root.title(APP_TITLE + "  [MODO USB — datos guardados en USB]")

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
