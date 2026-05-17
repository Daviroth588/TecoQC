"""
TecoQC - Paso 4: Prueba de trackpad (dibujo, clics, scroll)
"""

import tkinter as tk
from ui.steps.base_step import BaseStep
from ui import theme
from config import STATUS_PASSED


class Step(BaseStep):
    TITLE = "Prueba de Trackpad"
    DESCRIPTION = ("Dibuje en el lienzo, pruebe los clics y el desplazamiento para verificar "
                   "que el trackpad funcione correctamente.")
    STEP_NUM = 4

    def build_ui(self, parent):
        self._click_tests = {"left": False, "right": False, "middle": False}
        self._scroll_test = False
        self._last_x = None
        self._last_y = None
        self._draw_count = 0

        # Two columns: canvas on left, tests on right
        cols = tk.Frame(parent, bg=theme.BG_BASE)
        cols.pack(fill=tk.BOTH, expand=True)

        # ── Drawing canvas ─────────────────────────────────────────────
        canvas_frame = tk.Frame(cols, bg=theme.BG_BASE)
        canvas_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 12))

        tk.Label(canvas_frame, text="Área de dibujo — mueva el dedo por la superficie",
                 bg=theme.BG_BASE, fg=theme.TEXT_SECONDARY,
                 font=theme.FONT_BODY).pack(anchor="w", pady=(0, 6))

        canvas_wrapper = tk.Frame(canvas_frame, bg=theme.BG_SURFACE0,
                                   highlightthickness=2,
                                   highlightbackground=theme.BG_SURFACE2)
        canvas_wrapper.pack(fill=tk.BOTH, expand=True)

        self._canvas = tk.Canvas(
            canvas_wrapper,
            bg=theme.BG_CRUST,
            highlightthickness=0,
            cursor="crosshair",
        )
        self._canvas.pack(fill=tk.BOTH, expand=True, padx=2, pady=2)

        self._canvas.bind("<B1-Motion>", self._on_draw)
        self._canvas.bind("<ButtonRelease-1>", self._on_release)
        self._canvas.bind("<Button-1>", self._on_left_click)
        self._canvas.bind("<Button-2>", self._on_middle_click)
        self._canvas.bind("<Button-3>", self._on_right_click)
        self._canvas.bind("<MouseWheel>", self._on_scroll)

        # Clear button
        tk.Button(
            canvas_frame, text="🗑 Limpiar lienzo",
            command=self._clear_canvas,
            **theme.BTN_SECONDARY,
        ).pack(anchor="e", pady=(6, 0))

        # Prompt text on canvas
        self._canvas_hint = self._canvas.create_text(
            200, 140,
            text="Dibuje aquí con el trackpad",
            fill=theme.TEXT_MUTED,
            font=theme.FONT_H3,
        )

        # ── Click / Scroll tests ───────────────────────────────────────
        right_col = tk.Frame(cols, bg=theme.BG_BASE, width=240)
        right_col.pack(side=tk.LEFT, fill=tk.Y)
        right_col.pack_propagate(False)

        # Click tests
        tk.Label(right_col, text="Prueba de Clics",
                 bg=theme.BG_BASE, fg=theme.TEXT_PRIMARY,
                 font=theme.FONT_H3).pack(anchor="w", pady=(0, 8))

        click_configs = [
            ("left",   "Click Izquierdo",  "Haga clic izquierdo en el lienzo"),
            ("right",  "Click Derecho",    "Haga clic derecho en el lienzo"),
            ("middle", "Click Central",    "Haga clic con rueda/medio en el lienzo"),
        ]

        self._click_labels = {}
        self._click_icons = {}

        for key, title, hint in click_configs:
            card = tk.Frame(right_col, bg=theme.BG_SURFACE0,
                             highlightthickness=1,
                             highlightbackground=theme.BG_SURFACE1)
            card.pack(fill=tk.X, pady=4)

            inner = tk.Frame(card, bg=theme.BG_SURFACE0)
            inner.pack(fill=tk.X, padx=12, pady=10)

            icon_lbl = tk.Label(inner, text="●", bg=theme.BG_SURFACE0,
                                 fg=theme.TEXT_MUTED, font=theme.FONT_H3)
            icon_lbl.pack(side=tk.LEFT, padx=(0, 10))

            text_col = tk.Frame(inner, bg=theme.BG_SURFACE0)
            text_col.pack(side=tk.LEFT, fill=tk.X, expand=True)

            tk.Label(text_col, text=title, bg=theme.BG_SURFACE0,
                     fg=theme.TEXT_PRIMARY, font=theme.FONT_BODY_BOLD,
                     anchor="w").pack(anchor="w")
            tk.Label(text_col, text=hint, bg=theme.BG_SURFACE0,
                     fg=theme.TEXT_MUTED, font=theme.FONT_SMALL,
                     anchor="w").pack(anchor="w")

            self._click_icons[key] = icon_lbl
            self._click_labels[key] = tk.Label(inner, text="Pendiente",
                                                bg=theme.BG_SURFACE0,
                                                fg=theme.TEXT_MUTED,
                                                font=theme.FONT_SMALL)
            self._click_labels[key].pack(side=tk.RIGHT)

        # Scroll test
        tk.Label(right_col, text="Prueba de Desplazamiento",
                 bg=theme.BG_BASE, fg=theme.TEXT_PRIMARY,
                 font=theme.FONT_H3).pack(anchor="w", pady=(16, 8))

        scroll_card = tk.Frame(right_col, bg=theme.BG_SURFACE0,
                                highlightthickness=1,
                                highlightbackground=theme.BG_SURFACE1)
        scroll_card.pack(fill=tk.X)

        scroll_inner = tk.Frame(scroll_card, bg=theme.BG_SURFACE0)
        scroll_inner.pack(fill=tk.X, padx=12, pady=10)

        self._scroll_icon = tk.Label(scroll_inner, text="●",
                                      bg=theme.BG_SURFACE0,
                                      fg=theme.TEXT_MUTED,
                                      font=theme.FONT_H3)
        self._scroll_icon.pack(side=tk.LEFT, padx=(0, 10))

        tk.Label(scroll_inner, text="Desplace la rueda\nsobre el lienzo",
                 bg=theme.BG_SURFACE0, fg=theme.TEXT_SECONDARY,
                 font=theme.FONT_BODY, anchor="w").pack(side=tk.LEFT)

        self._scroll_lbl = tk.Label(scroll_inner, text="Pendiente",
                                     bg=theme.BG_SURFACE0,
                                     fg=theme.TEXT_MUTED,
                                     font=theme.FONT_SMALL)
        self._scroll_lbl.pack(side=tk.RIGHT)

        # Drawing status
        tk.Label(right_col, text="Prueba de Movimiento",
                 bg=theme.BG_BASE, fg=theme.TEXT_PRIMARY,
                 font=theme.FONT_H3).pack(anchor="w", pady=(16, 8))

        draw_card = tk.Frame(right_col, bg=theme.BG_SURFACE0,
                              highlightthickness=1,
                              highlightbackground=theme.BG_SURFACE1)
        draw_card.pack(fill=tk.X)
        draw_inner = tk.Frame(draw_card, bg=theme.BG_SURFACE0)
        draw_inner.pack(fill=tk.X, padx=12, pady=10)

        self._draw_icon = tk.Label(draw_inner, text="●",
                                    bg=theme.BG_SURFACE0,
                                    fg=theme.TEXT_MUTED,
                                    font=theme.FONT_H3)
        self._draw_icon.pack(side=tk.LEFT, padx=(0, 10))

        tk.Label(draw_inner, text="Dibuje en el lienzo\npara verificar movimiento",
                 bg=theme.BG_SURFACE0, fg=theme.TEXT_SECONDARY,
                 font=theme.FONT_BODY, anchor="w").pack(side=tk.LEFT)

        self._draw_lbl = tk.Label(draw_inner, text="Pendiente",
                                   bg=theme.BG_SURFACE0,
                                   fg=theme.TEXT_MUTED,
                                   font=theme.FONT_SMALL)
        self._draw_lbl.pack(side=tk.RIGHT)

    def _on_left_click(self, event):
        self._register_click("left")

    def _on_right_click(self, event):
        self._register_click("right")

    def _on_middle_click(self, event):
        self._register_click("middle")

    def _register_click(self, which):
        self._click_tests[which] = True
        self._click_icons[which].configure(fg=theme.SUCCESS, text="✓")
        self._click_labels[which].configure(text="Detectado", fg=theme.SUCCESS)
        self._check_complete()

    def _on_scroll(self, event):
        self._scroll_test = True
        direction = "▲" if event.delta > 0 else "▼"
        self._scroll_icon.configure(fg=theme.SUCCESS, text="✓")
        self._scroll_lbl.configure(text=f"Detectado {direction}", fg=theme.SUCCESS)
        self._check_complete()

    def _on_draw(self, event):
        if self._last_x is not None and self._last_y is not None:
            # Remove hint text
            try:
                self._canvas.delete(self._canvas_hint)
            except Exception:
                pass
            # Draw line
            self._canvas.create_line(
                self._last_x, self._last_y, event.x, event.y,
                fill=theme.ACCENT_BLUE, width=3, smooth=True, capstyle="round",
            )
            self._draw_count += 1
            if self._draw_count > 20:
                self._draw_icon.configure(fg=theme.SUCCESS, text="✓")
                self._draw_lbl.configure(text="Detectado", fg=theme.SUCCESS)
                self._check_complete()

        self._last_x = event.x
        self._last_y = event.y

    def _on_release(self, event):
        self._last_x = None
        self._last_y = None

    def _clear_canvas(self):
        self._canvas.delete("all")
        self._canvas_hint = self._canvas.create_text(
            200, 140,
            text="Dibuje aquí con el trackpad",
            fill=theme.TEXT_MUTED,
            font=theme.FONT_H3,
        )
        self._draw_count = 0
        self._draw_icon.configure(fg=theme.TEXT_MUTED, text="●")
        self._draw_lbl.configure(text="Pendiente", fg=theme.TEXT_MUTED)

    def _check_complete(self):
        all_clicks = all(self._click_tests.values())
        all_done = all_clicks and self._scroll_test and self._draw_count > 20
        if all_done:
            self.set_status(STATUS_PASSED,
                             "Click izq/der/central + scroll + movimiento verificados")
        else:
            done = sum([
                self._click_tests["left"],
                self._click_tests["right"],
                self._click_tests["middle"],
                self._scroll_test,
                self._draw_count > 20,
            ])
            self._set_detail(f"{done}/5 pruebas completadas")
