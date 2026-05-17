"""
TecoQC - Paso 5: Prueba de pantalla (píxeles muertos, colores, resolución)
"""

import tkinter as tk
from ui.steps.base_step import BaseStep
from ui import theme
from config import STATUS_PASSED


COLOR_TESTS = [
    ("Blanco",   "#FFFFFF", "#000000"),
    ("Negro",    "#000000", "#FFFFFF"),
    ("Rojo",     "#FF0000", "#FFFFFF"),
    ("Verde",    "#00FF00", "#000000"),
    ("Azul",     "#0000FF", "#FFFFFF"),
    ("Gris",     "#808080", "#FFFFFF"),
    ("Cian",     "#00FFFF", "#000000"),
    ("Magenta",  "#FF00FF", "#FFFFFF"),
]

EXTRA_PATTERNS = [
    ("Cuadrícula (píxeles muertos)", "grid"),
    ("Gradiente B/N (backlight)",    "gradient"),
]


class Step(BaseStep):
    TITLE = "Prueba de Pantalla"
    DESCRIPTION = ("Muestre cada color en pantalla completa para detectar píxeles muertos, "
                   "manchas o problemas de iluminación. Presione ESC para salir de cada color.")
    STEP_NUM = 5

    def build_ui(self, parent):
        self._color_states = {name: "pending" for name, _, _ in COLOR_TESTS}
        self._fullscreen_win = None
        self._monitor_info = {}

        # Monitor info bar
        info_bar = tk.Frame(parent, bg=theme.BG_SURFACE0,
                             highlightthickness=1, highlightbackground=theme.BG_SURFACE1)
        info_bar.pack(fill=tk.X, pady=(0, 8))
        self._monitor_lbl = tk.Label(
            info_bar, text="Detectando monitor...",
            bg=theme.BG_SURFACE0, fg=theme.TEXT_MUTED, font=theme.FONT_SMALL,
            padx=12, pady=6)
        self._monitor_lbl.pack(side=tk.LEFT)

        # Instructions
        instr = tk.Frame(parent, bg=theme.BG_SURFACE0,
                          highlightthickness=1, highlightbackground=theme.ACCENT_BLUE)
        instr.pack(fill=tk.X, pady=(0, 12))
        tk.Label(
            instr,
            text="💡  Haga clic en cada color para mostrarlo en pantalla completa. "
                 "Presione ESC o haga clic para cerrar.",
            bg=theme.BG_SURFACE0, fg=theme.ACCENT_BLUE,
            font=theme.FONT_BODY, pady=10, padx=14,
        ).pack(anchor="w")

        # Extra pattern buttons row
        pat_row = tk.Frame(parent, bg=theme.BG_BASE)
        pat_row.pack(fill=tk.X, pady=(0, 8))
        tk.Label(pat_row, text="Patrones adicionales:",
                 bg=theme.BG_BASE, fg=theme.TEXT_SECONDARY,
                 font=theme.FONT_BODY).pack(side=tk.LEFT, padx=(0, 10))
        for name, ptype in EXTRA_PATTERNS:
            tk.Button(pat_row, text=f"▶ {name}",
                      command=lambda pt=ptype, pn=name: self._show_pattern(pt, pn),
                      **theme.BTN_NEUTRAL).pack(side=tk.LEFT, padx=4)

        # Color grid
        grid = tk.Frame(parent, bg=theme.BG_BASE)
        grid.pack(fill=tk.BOTH, expand=True)

        self._color_frames = {}
        self._color_status_labels = {}

        for idx, (name, color, text_color) in enumerate(COLOR_TESTS):
            row = idx // 4
            col = idx % 4
            grid.columnconfigure(col, weight=1)
            grid.rowconfigure(row, weight=1)

            card = tk.Frame(grid, bg=theme.BG_SURFACE0,
                             highlightthickness=2,
                             highlightbackground=theme.BG_SURFACE1,
                             cursor="hand2")
            card.grid(row=row, column=col, padx=6, pady=6, sticky="nsew")

            preview = tk.Frame(card, bg=color, height=80)
            preview.pack(fill=tk.X)
            preview.pack_propagate(False)
            tk.Label(preview, text=name, bg=color, fg=text_color,
                     font=theme.FONT_H3).pack(expand=True)

            bottom = tk.Frame(card, bg=theme.BG_SURFACE0)
            bottom.pack(fill=tk.X, padx=8, pady=6)

            status_lbl = tk.Label(bottom, text="● Pendiente",
                                   bg=theme.BG_SURFACE0, fg=theme.TEXT_MUTED,
                                   font=theme.FONT_SMALL)
            status_lbl.pack(side=tk.LEFT)
            self._color_status_labels[name] = status_lbl

            btn_row = tk.Frame(bottom, bg=theme.BG_SURFACE0)
            btn_row.pack(side=tk.RIGHT)

            tk.Button(
                btn_row, text="▶ Ver",
                command=lambda n=name, c=color, t=text_color: self._show_fullscreen(n, c, t),
                bg=color, fg=text_color if text_color == "#000000" else "#FFFFFF",
                font=(theme.FONT_FAMILY, 9, "bold"),
                relief="flat", cursor="hand2", padx=8, pady=3,
            ).pack(side=tk.LEFT, padx=(0, 4))

            tk.Button(btn_row, text="✓",
                      command=lambda n=name: self._mark_color(n, "passed"),
                      bg=theme.SUCCESS, fg=theme.BG_BASE,
                      font=(theme.FONT_FAMILY, 9, "bold"),
                      relief="flat", cursor="hand2", padx=6, pady=3,
                      ).pack(side=tk.LEFT, padx=(0, 2))

            tk.Button(btn_row, text="✗",
                      command=lambda n=name: self._mark_color(n, "failed"),
                      bg=theme.ERROR, fg=theme.BG_BASE,
                      font=(theme.FONT_FAMILY, 9, "bold"),
                      relief="flat", cursor="hand2", padx=6, pady=3,
                      ).pack(side=tk.LEFT)

            for w in (card, preview):
                w.bind("<Button-1>",
                        lambda e, n=name, c=color, t=text_color:
                        self._show_fullscreen(n, c, t))

            self._color_frames[name] = card

        # Notes field (required before passing)
        notes_frame = tk.Frame(parent, bg=theme.BG_BASE)
        notes_frame.pack(fill=tk.X, pady=(8, 0))
        tk.Label(notes_frame, text="Observaciones del técnico (requerido para aprobar):",
                 bg=theme.BG_BASE, fg=theme.TEXT_SECONDARY,
                 font=theme.FONT_SMALL).pack(anchor="w")
        self._notes_entry = tk.Entry(notes_frame, **theme.ENTRY_STYLE)
        self._notes_entry.pack(fill=tk.X, pady=(4, 0), ipady=4)
        self._notes_entry.insert(0, "Sin anomalías")
        self._notes_entry.bind("<KeyRelease>", lambda e: self._update_overall())

        # Detect monitor info in background
        self.run_in_thread(self._get_monitor_info, on_done=self._show_monitor_info)

    def _get_monitor_info(self):
        info = {}
        try:
            import wmi
            c = wmi.WMI()
            monitors = c.Win32_DesktopMonitor()
            if monitors:
                m = monitors[0]
                w = getattr(m, "ScreenWidth", None) or getattr(m, "HorizontalResolution", None)
                h = getattr(m, "ScreenHeight", None) or getattr(m, "VerticalResolution", None)
                info["width"] = w
                info["height"] = h
                info["name"] = getattr(m, "Name", None) or getattr(m, "Caption", "N/D")
        except Exception:
            pass
        try:
            import tkinter as tk
            root = tk._default_root
            if root:
                info.setdefault("width", root.winfo_screenwidth())
                info.setdefault("height", root.winfo_screenheight())
        except Exception:
            pass
        return info

    def _show_monitor_info(self, info):
        self._monitor_info = info
        w = info.get("width", "?")
        h = info.get("height", "?")
        name = info.get("name", "")
        parts = [f"Resolución: {w}×{h}"]
        if name and name != "N/D":
            parts.append(f"Monitor: {name}")
        self._monitor_lbl.configure(
            text="  ".join(parts),
            fg=theme.TEXT_SECONDARY)

    def _show_fullscreen(self, name, color, text_color):
        if self._fullscreen_win:
            try:
                self._fullscreen_win.destroy()
            except Exception:
                pass

        win = tk.Toplevel()
        win.configure(bg=color)
        win.attributes("-fullscreen", True)
        win.attributes("-topmost", True)
        self._fullscreen_win = win

        lbl = tk.Label(win, text=f"{name}\n\nPresione ESC o haga clic para cerrar",
                       bg=color, fg=text_color,
                       font=(theme.FONT_FAMILY, 28, "bold"))
        lbl.place(relx=0.5, rely=0.5, anchor="center")

        def close(event=None):
            try:
                win.destroy()
            except Exception:
                pass
            self._fullscreen_win = None

        win.bind("<Escape>", close)
        win.bind("<Button-1>", close)
        win.bind("<Button-3>", close)
        win.focus_force()

    def _show_pattern(self, ptype, name):
        if self._fullscreen_win:
            try:
                self._fullscreen_win.destroy()
            except Exception:
                pass

        win = tk.Toplevel()
        win.configure(bg="#000000")
        win.attributes("-fullscreen", True)
        win.attributes("-topmost", True)
        self._fullscreen_win = win

        canvas = tk.Canvas(win, bg="#000000", highlightthickness=0)
        canvas.pack(fill=tk.BOTH, expand=True)

        def draw(event=None):
            cw = canvas.winfo_width()
            ch = canvas.winfo_height()
            canvas.delete("all")
            if ptype == "grid":
                cols, rows = 32, 18
                cw2 = cw or 1920
                ch2 = ch or 1080
                for i in range(cols + 1):
                    x = int(i * cw2 / cols)
                    canvas.create_line(x, 0, x, ch2, fill="#444444", width=1)
                for j in range(rows + 1):
                    y = int(j * ch2 / rows)
                    canvas.create_line(0, y, cw2, y, fill="#444444", width=1)
                canvas.create_text(cw2 // 2, ch2 // 2,
                                   text="CUADRÍCULA — Busque píxeles faltantes o manchas\nESC para cerrar",
                                   fill="white", font=(theme.FONT_FAMILY, 20, "bold"),
                                   justify="center")
            elif ptype == "gradient":
                steps = 256
                cw2 = cw or 1920
                ch2 = ch or 1080
                for i in range(steps):
                    v = int(i * 255 / (steps - 1))
                    x0 = int(i * cw2 / steps)
                    x1 = int((i + 1) * cw2 / steps)
                    col = f"#{v:02x}{v:02x}{v:02x}"
                    canvas.create_rectangle(x0, 0, x1, ch2, fill=col, outline="")
                canvas.create_text(cw2 // 2, ch2 // 2,
                                   text="GRADIENTE — Verifique uniformidad del backlight\nESC para cerrar",
                                   fill="#ff0000", font=(theme.FONT_FAMILY, 20, "bold"),
                                   justify="center")

        win.after(100, draw)
        canvas.bind("<Configure>", draw)

        def close(event=None):
            try:
                win.destroy()
            except Exception:
                pass
            self._fullscreen_win = None

        win.bind("<Escape>", close)
        win.bind("<Button-1>", close)
        win.focus_force()

    def _mark_color(self, name, status):
        self._color_states[name] = status
        lbl = self._color_status_labels[name]
        card = self._color_frames[name]
        if status == "passed":
            lbl.configure(text="✓ Aprobado", fg=theme.SUCCESS)
            card.configure(highlightbackground=theme.SUCCESS)
        else:
            lbl.configure(text="✗ Fallido", fg=theme.ERROR)
            card.configure(highlightbackground=theme.ERROR)
        self._update_overall()

    def _update_overall(self):
        states = list(self._color_states.values())
        failed = states.count("failed")
        passed = states.count("passed")
        total = len(COLOR_TESTS)
        notes = self._notes_entry.get().strip() if hasattr(self, "_notes_entry") else ""

        if failed > 0:
            self.set_status("failed", f"{failed} colores con problemas")
        elif passed == total:
            if notes:
                self._state.setdefault("step_results", {}).setdefault(5, {})["notes"] = notes
                self.set_status(STATUS_PASSED, "Todos los colores aprobados")
            else:
                self._set_detail(f"{passed}/{total} — agregue observación para aprobar")
        else:
            self._set_detail(f"{passed}/{total} colores verificados")
