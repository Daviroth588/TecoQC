"""
TecoQC - Paso 5: Prueba de pantalla (píxeles muertos, colores)
"""

import tkinter as tk
from ui.steps.base_step import BaseStep
from ui import theme
from config import STATUS_PASSED


# Color tests: (name, hex_color, text_color)
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


class Step(BaseStep):
    TITLE = "Prueba de Pantalla"
    DESCRIPTION = ("Muestre cada color en pantalla completa para detectar píxeles muertos, "
                   "manchas o problemas de iluminación. Presione ESC para salir de cada color.")
    STEP_NUM = 5

    def build_ui(self, parent):
        self._color_states = {name: "pending" for name, _, _ in COLOR_TESTS}
        self._fullscreen_win = None

        # Instructions
        instr = tk.Frame(parent, bg=theme.BG_SURFACE0,
                          highlightthickness=1, highlightbackground=theme.ACCENT_BLUE)
        instr.pack(fill=tk.X, pady=(0, 16))
        tk.Label(
            instr,
            text="💡  Haga clic en cada color para mostrarlo en pantalla completa. "
                 "Presione ESC o haga clic para cerrar.",
            bg=theme.BG_SURFACE0, fg=theme.ACCENT_BLUE,
            font=theme.FONT_BODY, pady=10, padx=14,
        ).pack(anchor="w")

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

            # Color preview
            preview = tk.Frame(card, bg=color, height=80)
            preview.pack(fill=tk.X)
            preview.pack_propagate(False)

            tk.Label(
                preview,
                text=name,
                bg=color,
                fg=text_color,
                font=theme.FONT_H3,
            ).pack(expand=True)

            # Bottom bar
            bottom = tk.Frame(card, bg=theme.BG_SURFACE0)
            bottom.pack(fill=tk.X, padx=8, pady=6)

            status_lbl = tk.Label(
                bottom, text="● Pendiente",
                bg=theme.BG_SURFACE0,
                fg=theme.TEXT_MUTED,
                font=theme.FONT_SMALL,
            )
            status_lbl.pack(side=tk.LEFT)

            self._color_status_labels[name] = status_lbl

            # Buttons
            btn_row = tk.Frame(bottom, bg=theme.BG_SURFACE0)
            btn_row.pack(side=tk.RIGHT)

            tk.Button(
                btn_row, text="▶ Ver",
                command=lambda n=name, c=color, t=text_color: self._show_fullscreen(n, c, t),
                bg=color, fg=text_color if text_color == "#000000" else "#FFFFFF",
                font=(theme.FONT_FAMILY, 9, "bold"),
                relief="flat", cursor="hand2",
                padx=8, pady=3,
            ).pack(side=tk.LEFT, padx=(0, 4))

            tk.Button(
                btn_row, text="✓",
                command=lambda n=name: self._mark_color(n, "passed"),
                bg=theme.SUCCESS, fg=theme.BG_BASE,
                font=(theme.FONT_FAMILY, 9, "bold"),
                relief="flat", cursor="hand2",
                padx=6, pady=3,
            ).pack(side=tk.LEFT, padx=(0, 2))

            tk.Button(
                btn_row, text="✗",
                command=lambda n=name: self._mark_color(n, "failed"),
                bg=theme.ERROR, fg=theme.BG_BASE,
                font=(theme.FONT_FAMILY, 9, "bold"),
                relief="flat", cursor="hand2",
                padx=6, pady=3,
            ).pack(side=tk.LEFT)

            # Bind click on preview for fullscreen
            for w in (card, preview):
                w.bind("<Button-1>",
                        lambda e, n=name, c=color, t=text_color:
                        self._show_fullscreen(n, c, t))

            self._color_frames[name] = card

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

        # Instructions overlay
        lbl = tk.Label(
            win,
            text=f"{name}\n\nPresione ESC o haga clic para cerrar",
            bg=color,
            fg=text_color,
            font=(theme.FONT_FAMILY, 28, "bold"),
        )
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

        if failed > 0:
            self.set_status("failed",
                             f"{failed} colores con problemas")
        elif passed == total:
            self.set_status(STATUS_PASSED,
                             "Todos los colores aprobados")
        else:
            self._set_detail(f"{passed}/{total} colores verificados")
