"""
TecoQC - Paso 3: Prueba de teclado interactiva con layout visual
Soporta teclados en Inglés (QWERTY) y Español (QWERTY-ES)
"""

import tkinter as tk
from ui.steps.base_step import BaseStep
from ui import theme
from config import STATUS_PASSED, STATUS_FAILED

KEY_W   = 36
KEY_H   = 36
KEY_PAD = 3

# ── Layouts ────────────────────────────────────────────────────────────────
LAYOUTS = {
    "EN": {
        "label": "Inglés (QWERTY)",
        "rows": [
            # Function row
            [("Esc","Escape",1.0),("F1","F1",1.0),("F2","F2",1.0),("F3","F3",1.0),
             ("F4","F4",1.0),("F5","F5",1.0),("F6","F6",1.0),("F7","F7",1.0),
             ("F8","F8",1.0),("F9","F9",1.0),("F10","F10",1.0),("F11","F11",1.0),
             ("F12","F12",1.0)],
            # Number row
            [("`","grave",1.0),("1","1",1.0),("2","2",1.0),("3","3",1.0),
             ("4","4",1.0),("5","5",1.0),("6","6",1.0),("7","7",1.0),
             ("8","8",1.0),("9","9",1.0),("0","0",1.0),("-","minus",1.0),
             ("=","equal",1.0),("⌫ Back","BackSpace",2.0)],
            # Tab row
            [("Tab","Tab",1.5),("Q","q",1.0),("W","w",1.0),("E","e",1.0),
             ("R","r",1.0),("T","t",1.0),("Y","y",1.0),("U","u",1.0),
             ("I","i",1.0),("O","o",1.0),("P","p",1.0),("[","bracketleft",1.0),
             ("]","bracketright",1.0),("\\","backslash",1.5)],
            # Caps row
            [("Caps","Caps_Lock",1.75),("A","a",1.0),("S","s",1.0),("D","d",1.0),
             ("F","f",1.0),("G","g",1.0),("H","h",1.0),("J","j",1.0),
             ("K","k",1.0),("L","l",1.0),(";","semicolon",1.0),
             ("'","apostrophe",1.0),("Enter","Return",2.25)],
            # Shift row
            [("Shift","Shift_L",2.25),("Z","z",1.0),("X","x",1.0),("C","c",1.0),
             ("V","v",1.0),("B","b",1.0),("N","n",1.0),("M","m",1.0),
             (",","comma",1.0),(".","period",1.0),("/","slash",1.0),
             ("Shift ►","Shift_R",2.75)],
            # Bottom row
            [("Ctrl","Control_L",1.5),("Win","super_l",1.25),("Alt","Alt_L",1.25),
             ("Espacio","space",6.25),("Alt ►","Alt_R",1.25),("Fn",None,1.25),
             ("Ctrl ►","Control_R",1.5),("◄","Left",1.0),
             ("▲","Up",1.0),("▼","Down",1.0),("►","Right",1.0)],
        ],
    },
    "ES": {
        "label": "Español (QWERTY-ES)",
        "rows": [
            # Function row
            [("Esc","Escape",1.0),("F1","F1",1.0),("F2","F2",1.0),("F3","F3",1.0),
             ("F4","F4",1.0),("F5","F5",1.0),("F6","F6",1.0),("F7","F7",1.0),
             ("F8","F8",1.0),("F9","F9",1.0),("F10","F10",1.0),("F11","F11",1.0),
             ("F12","F12",1.0)],
            # Number row  (º ¡ ¿ son específicos del teclado ES)
            [("º/ª","masculine",1.0),("1","1",1.0),("2","2",1.0),("3","3",1.0),
             ("4","4",1.0),("5","5",1.0),("6","6",1.0),("7","7",1.0),
             ("8","8",1.0),("9","9",1.0),("0","0",1.0),("'/?","minus",1.0),
             ("¡/¿","equal",1.0),("⌫ Back","BackSpace",2.0)],
            # Tab row
            [("Tab","Tab",1.5),("Q","q",1.0),("W","w",1.0),("E","e",1.0),
             ("R","r",1.0),("T","t",1.0),("Y","y",1.0),("U","u",1.0),
             ("I","i",1.0),("O","o",1.0),("P","p",1.0),("`/^","dead_grave",1.0),
             ("+/*","bracketright",1.0),("Enter","Return",1.75)],
            # Caps row  → Ñ en lugar de ; y ´ en lugar de '
            [("Caps","Caps_Lock",1.75),("A","a",1.0),("S","s",1.0),("D","d",1.0),
             ("F","f",1.0),("G","g",1.0),("H","h",1.0),("J","j",1.0),
             ("K","k",1.0),("L","l",1.0),("Ñ","ntilde",1.0),
             ("´/¨","dead_acute",1.0),("Ç/}","backslash",1.25)],
            # Shift row  → tecla extra <> entre Shift y Z
            [("Shift","Shift_L",1.75),("</>","less",1.0),("Z","z",1.0),
             ("X","x",1.0),("C","c",1.0),("V","v",1.0),("B","b",1.0),
             ("N","n",1.0),("M","m",1.0),(",/;","comma",1.0),("./:","period",1.0),
             ("-/_","slash",1.0),("Shift ►","Shift_R",2.75)],
            # Bottom row  → AltGr en lugar de Alt derecho
            [("Ctrl","Control_L",1.5),("Win","super_l",1.25),("Alt","Alt_L",1.25),
             ("Espacio","space",6.25),("AltGr","Alt_R",1.25),("Fn",None,1.25),
             ("Ctrl ►","Control_R",1.5),("◄","Left",1.0),
             ("▲","Up",1.0),("▼","Down",1.0),("►","Right",1.0)],
        ],
    },
}

# Keysyms alternativos que tkinter puede reportar para teclas especiales ES
KEYSYM_ALIASES = {
    # Español
    "ntilde":     ["ntilde", "Ntilde"],
    "dead_acute": ["dead_acute", "apostrophe", "acute"],
    "dead_grave": ["dead_grave", "grave", "asciicircum", "dead_circumflex"],
    "masculine":  ["masculine", "ordfeminine", "grave", "asciitilde"],
    "less":       ["less", "greater", "bar"],
    # Inglés
    "super_l":    ["super_l", "Super_L"],
}


class Step(BaseStep):
    TITLE = "Prueba de Teclado"
    DESCRIPTION = ("Seleccione el idioma del teclado, luego presione todas las teclas. "
                   "Cada tecla se iluminará en verde al ser detectada.")
    STEP_NUM = 3

    def build_ui(self, parent):
        self._pressed_keys = set()
        self._key_buttons  = {}   # keysym -> button widget
        self._total_keys   = 0
        self._current_layout = "ES"   # default

        # ── Selector de idioma ─────────────────────────────────────────
        selector_frame = tk.Frame(parent, bg=theme.BG_SURFACE0,
                                   highlightthickness=1,
                                   highlightbackground=theme.BG_SURFACE2)
        selector_frame.pack(fill=tk.X, pady=(0, 10))

        tk.Label(selector_frame, text="Idioma del teclado:",
                 bg=theme.BG_SURFACE0, fg=theme.TEXT_SECONDARY,
                 font=theme.FONT_BODY).pack(side=tk.LEFT, padx=(12, 8), pady=8)

        self._layout_var = tk.StringVar(value="ES")
        for code, data in LAYOUTS.items():
            rb = tk.Radiobutton(
                selector_frame,
                text=data["label"],
                variable=self._layout_var,
                value=code,
                command=self._switch_layout,
                bg=theme.BG_SURFACE0,
                fg=theme.TEXT_PRIMARY,
                selectcolor=theme.BG_SURFACE1,
                activebackground=theme.BG_SURFACE0,
                font=theme.FONT_BODY,
                indicatoron=0,
                relief="flat",
                padx=14, pady=6,
                cursor="hand2",
            )
            rb.pack(side=tk.LEFT, padx=4, pady=4)

        # ── Barra de estadísticas ──────────────────────────────────────
        stats_row = tk.Frame(parent, bg=theme.BG_BASE)
        stats_row.pack(fill=tk.X, pady=(0, 8))

        self._pressed_lbl = tk.Label(
            stats_row, text="Presionadas: 0",
            bg=theme.BG_BASE, fg=theme.SUCCESS, font=theme.FONT_BODY_BOLD)
        self._pressed_lbl.pack(side=tk.LEFT, padx=(0, 16))

        self._remaining_lbl = tk.Label(
            stats_row, text="",
            bg=theme.BG_BASE, fg=theme.WARNING, font=theme.FONT_BODY)
        self._remaining_lbl.pack(side=tk.LEFT)

        tk.Button(stats_row, text="↺ Reiniciar",
                  command=self._reset,
                  **theme.BTN_SECONDARY).pack(side=tk.RIGHT)

        # ── Canvas del teclado ─────────────────────────────────────────
        self._kbd_frame = tk.Frame(parent, bg=theme.BG_MANTLE,
                                    highlightthickness=1,
                                    highlightbackground=theme.BG_SURFACE2)
        self._kbd_frame.pack(anchor="center", pady=4)

        # ── Leyenda de teclas especiales ES ───────────────────────────
        self._legend_frame = tk.Frame(parent, bg=theme.BG_BASE)
        self._legend_frame.pack(fill=tk.X, pady=(6, 0))

        self._build_keyboard()
        self._update_stats()

    # ── Layout ────────────────────────────────────────────────────────
    def _switch_layout(self):
        self._current_layout = self._layout_var.get()
        self._reset()
        self._build_keyboard()
        self._build_legend()
        self._update_stats()

    def _build_keyboard(self):
        for w in self._kbd_frame.winfo_children():
            w.destroy()
        self._key_buttons = {}
        self._total_keys  = 0

        rows = LAYOUTS[self._current_layout]["rows"]
        for row_idx, row in enumerate(rows):
            row_frame = tk.Frame(self._kbd_frame, bg=theme.BG_MANTLE)
            row_frame.pack(
                padx=8,
                pady=(8 if row_idx == 0 else 2,
                      8 if row_idx == len(rows) - 1 else 0))

            for label, keysym, width_factor in row:
                btn_w = int(KEY_W * width_factor + KEY_PAD * (width_factor - 1))
                btn = tk.Label(
                    row_frame, text=label,
                    width=0,
                    bg=theme.BG_SURFACE1, fg=theme.TEXT_SECONDARY,
                    font=(theme.FONT_MONO, 8),
                    relief="raised", bd=1,
                    highlightthickness=0, cursor="arrow",
                )
                btn.pack(side=tk.LEFT, padx=2, pady=2,
                          ipadx=max(0, btn_w - 20), ipady=5)

                if keysym:
                    # Register primary keysym
                    self._key_buttons[keysym] = btn
                    # Register aliases so we catch the key regardless of driver
                    for alias in KEYSYM_ALIASES.get(keysym, []):
                        if alias not in self._key_buttons:
                            self._key_buttons[alias] = btn
                    self._total_keys += 1

    def _build_legend(self):
        for w in self._legend_frame.winfo_children():
            w.destroy()
        if self._current_layout == "ES":
            tk.Label(self._legend_frame,
                     text="Teclas especiales ES:  Ñ · º/ª · ´/¨ · ¡/¿ · </>  — "
                          "Algunas pueden registrarse como la tecla física equivalente.",
                     bg=theme.BG_BASE, fg=theme.TEXT_MUTED,
                     font=theme.FONT_SMALL).pack(anchor="w")

    # ── Eventos de teclado ─────────────────────────────────────────────
    def on_enter(self):
        self._root().bind("<KeyPress>",   self._on_key_press)
        self._root().bind("<KeyRelease>", self._on_key_release)
        self._build_legend()

    def on_leave(self):
        super().on_leave()
        try:
            self._root().unbind("<KeyPress>")
            self._root().unbind("<KeyRelease>")
        except Exception:
            pass

    def _root(self):
        w = self
        while w.master:
            w = w.master
        return w

    def _on_key_press(self, event):
        keysym = event.keysym
        self._pressed_keys.add(keysym)

        btn = self._key_buttons.get(keysym)
        if btn:
            btn.configure(bg=theme.SUCCESS, fg=theme.BG_BASE, relief="sunken")
        self._update_stats()

    def _on_key_release(self, event):
        keysym = event.keysym
        btn = self._key_buttons.get(keysym)
        if btn and keysym in self._pressed_keys:
            btn.configure(bg=theme.SUCCESS, fg=theme.BG_BASE, relief="raised")

    def _reset(self):
        self._pressed_keys.clear()
        for btn in self._key_buttons.values():
            btn.configure(bg=theme.BG_SURFACE1,
                           fg=theme.TEXT_SECONDARY, relief="raised")
        self._update_stats()
        self.set_status("pending")

    def _update_stats(self):
        # Count unique buttons hit (aliases share the same widget)
        hit_buttons = set()
        for ks in self._pressed_keys:
            btn = self._key_buttons.get(ks)
            if btn:
                hit_buttons.add(id(btn))

        unique_btns = set(id(b) for b in self._key_buttons.values())
        pressed  = len(hit_buttons)
        total    = len(unique_btns)
        remaining = total - pressed

        self._pressed_lbl.configure(text=f"Presionadas: {pressed} / {total}")
        if remaining > 0:
            self._remaining_lbl.configure(
                text=f"Faltan: {remaining} teclas", fg=theme.WARNING)
        else:
            self._remaining_lbl.configure(
                text="¡Todas las teclas probadas!", fg=theme.SUCCESS)
            lang = LAYOUTS[self._current_layout]["label"]
            self.set_status(STATUS_PASSED,
                             f"Todas las teclas verificadas ({total}) — {lang}")

        self._set_detail(f"{pressed}/{total} teclas presionadas")
