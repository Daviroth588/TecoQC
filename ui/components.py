"""
TecoQC - Componentes de UI reutilizables
"""

import tkinter as tk
from tkinter import ttk
import threading
import time
from ui import theme


class StatusBadge(tk.Label):
    """Etiqueta de estado coloreada (Aprobado / Fallido / Omitido / Pendiente)."""

    STATUS_CFG = {
        "passed":  (theme.SUCCESS,  "✓ Aprobado"),
        "failed":  (theme.ERROR,    "✗ Fallido"),
        "skipped": (theme.WARNING,  "⊘ Omitido"),
        "pending": (theme.TEXT_MUTED, "● Pendiente"),
        "running": (theme.ACCENT_BLUE, "► En curso"),
    }

    def __init__(self, parent, status="pending", **kwargs):
        color, label = self.STATUS_CFG.get(status, (theme.TEXT_MUTED, status))
        super().__init__(
            parent,
            text=label,
            fg=color,
            bg=kwargs.pop("bg", theme.BG_SURFACE0),
            font=theme.FONT_BODY_BOLD,
            padx=10,
            pady=4,
            **kwargs,
        )
        self._status = status

    def set_status(self, status):
        if status == self._status:
            return
        color, label = self.STATUS_CFG.get(status, (theme.TEXT_MUTED, status))
        self.configure(text=label, fg=color)
        self._status = status


class SectionTitle(tk.Label):
    """Título de sección con línea inferior decorativa."""

    def __init__(self, parent, text, **kwargs):
        super().__init__(
            parent,
            text=text,
            bg=kwargs.pop("bg", theme.BG_BASE),
            fg=theme.TEXT_PRIMARY,
            font=theme.FONT_H2,
            anchor="w",
            **kwargs,
        )


class Card(tk.Frame):
    """Contenedor tipo tarjeta con borde sutil."""

    def __init__(self, parent, **kwargs):
        super().__init__(
            parent,
            bg=theme.BG_SURFACE0,
            relief="flat",
            highlightthickness=1,
            highlightbackground=theme.BG_SURFACE1,
            **kwargs,
        )


class InfoRow(tk.Frame):
    """Fila de información con etiqueta y valor."""

    def __init__(self, parent, label, value="", label_width=20, **kwargs):
        bg = kwargs.pop("bg", theme.BG_SURFACE0)
        super().__init__(parent, bg=bg, **kwargs)

        tk.Label(
            self,
            text=label + ":",
            bg=bg,
            fg=theme.TEXT_SECONDARY,
            font=theme.FONT_BODY,
            width=label_width,
            anchor="w",
        ).pack(side=tk.LEFT)

        self._val_lbl = tk.Label(
            self,
            text=value,
            bg=bg,
            fg=theme.TEXT_PRIMARY,
            font=theme.FONT_BODY_BOLD,
            anchor="w",
        )
        self._val_lbl.pack(side=tk.LEFT, fill=tk.X, expand=True)

    def set_value(self, value):
        self._val_lbl.configure(text=value)


class ProgressBar(tk.Canvas):
    """Barra de progreso horizontal personalizada."""

    def __init__(self, parent, width=300, height=8, value=0, **kwargs):
        bg = kwargs.pop("bg", theme.BG_BASE)
        super().__init__(
            parent,
            width=width,
            height=height,
            bg=bg,
            highlightthickness=0,
            **kwargs,
        )
        self._w = width
        self._h = height
        self._value = value
        self._draw()

    def _draw(self):
        self.delete("all")
        # Background track
        self.create_rectangle(0, 0, self._w, self._h,
                               fill=theme.BG_SURFACE1, outline="")
        # Fill
        fill_w = int(self._w * max(0, min(1, self._value / 100)))
        if fill_w > 0:
            color = theme.SUCCESS if self._value >= 100 else \
                    theme.ERROR   if self._value == 0  else \
                    theme.ACCENT_BLUE
            self.create_rectangle(0, 0, fill_w, self._h,
                                   fill=color, outline="")

    def set_value(self, value):
        self._value = value
        self._draw()

    def configure(self, **kwargs):
        if "width" in kwargs:
            self._w = kwargs["width"]
        super().configure(**kwargs)
        self._draw()


class UsageBar(tk.Frame):
    """Barra de uso con etiqueta de porcentaje."""

    def __init__(self, parent, label="", value=0, bar_width=250, **kwargs):
        bg = kwargs.pop("bg", theme.BG_SURFACE0)
        super().__init__(parent, bg=bg, **kwargs)

        tk.Label(self, text=label, bg=bg, fg=theme.TEXT_SECONDARY,
                 font=theme.FONT_SMALL, width=18, anchor="w").pack(side=tk.LEFT)

        self._bar = ProgressBar(self, width=bar_width, height=12, value=value, bg=bg)
        self._bar.pack(side=tk.LEFT, padx=(4, 8))

        self._pct_lbl = tk.Label(self, text=f"{value:.1f}%", bg=bg,
                                  fg=theme.TEXT_PRIMARY, font=theme.FONT_SMALL,
                                  width=6, anchor="e")
        self._pct_lbl.pack(side=tk.LEFT)

    def set_value(self, value):
        self._bar.set_value(value)
        self._pct_lbl.configure(text=f"{value:.1f}%")


class Spinner(tk.Label):
    """Indicador de carga animado."""

    FRAMES = ["⠋", "⠙", "⠹", "⠸", "⠼", "⠴", "⠦", "⠧", "⠇", "⠏"]

    def __init__(self, parent, text="Cargando...", **kwargs):
        bg = kwargs.pop("bg", theme.BG_BASE)
        super().__init__(
            parent,
            text=f"{self.FRAMES[0]}  {text}",
            bg=bg,
            fg=theme.ACCENT_BLUE,
            font=theme.FONT_BODY,
            **kwargs,
        )
        self._text = text
        self._idx = 0
        self._running = False
        self._job = None

    def start(self):
        self._running = True
        self._animate()

    def stop(self, final_text=None):
        self._running = False
        if self._job:
            try:
                self.after_cancel(self._job)
            except Exception:
                pass
        if final_text is not None:
            self.configure(text=final_text, fg=theme.TEXT_SECONDARY)

    def _animate(self):
        if not self._running:
            return
        self._idx = (self._idx + 1) % len(self.FRAMES)
        self.configure(text=f"{self.FRAMES[self._idx]}  {self._text}")
        self._job = self.after(80, self._animate)


class NotesFrame(tk.Frame):
    """Campo de notas del técnico."""

    def __init__(self, parent, **kwargs):
        bg = kwargs.pop("bg", theme.BG_BASE)
        super().__init__(parent, bg=bg, **kwargs)

        tk.Label(self, text="Notas del técnico:", bg=bg,
                 fg=theme.TEXT_SECONDARY, font=theme.FONT_BODY).pack(anchor="w")

        text_frame = tk.Frame(self, bg=theme.BG_SURFACE0,
                               highlightthickness=1,
                               highlightbackground=theme.BG_SURFACE1)
        text_frame.pack(fill=tk.X, pady=(4, 0))

        self.text = tk.Text(
            text_frame,
            height=3,
            bg=theme.BG_SURFACE0,
            fg=theme.TEXT_PRIMARY,
            font=theme.FONT_BODY,
            relief="flat",
            bd=6,
            insertbackground=theme.TEXT_PRIMARY,
            wrap=tk.WORD,
        )
        self.text.pack(fill=tk.X)

    def get(self):
        return self.text.get("1.0", tk.END).strip()

    def set(self, value):
        self.text.delete("1.0", tk.END)
        self.text.insert("1.0", value)


class PassFailButtons(tk.Frame):
    """Botones de Aprobado / Fallido."""

    def __init__(self, parent, on_pass=None, on_fail=None, **kwargs):
        bg = kwargs.pop("bg", theme.BG_BASE)
        super().__init__(parent, bg=bg, **kwargs)

        self._on_pass = on_pass
        self._on_fail = on_fail

        self._pass_btn = tk.Button(
            self, text="✓  Aprobado", **theme.BTN_SUCCESS,
            command=self._do_pass,
        )
        self._pass_btn.pack(side=tk.LEFT, padx=(0, 8))

        self._fail_btn = tk.Button(
            self, text="✗  Fallido", **theme.BTN_DANGER,
            command=self._do_fail,
        )
        self._fail_btn.pack(side=tk.LEFT)

    def _do_pass(self):
        self._highlight(self._pass_btn, theme.SUCCESS)
        self._reset(self._fail_btn, theme.ERROR, theme.BG_BASE)
        if self._on_pass:
            self._on_pass()

    def _do_fail(self):
        self._highlight(self._fail_btn, theme.ERROR)
        self._reset(self._pass_btn, theme.SUCCESS, theme.BG_BASE)
        if self._on_fail:
            self._on_fail()

    def _highlight(self, btn, color):
        btn.configure(relief="solid", bd=2, highlightthickness=2,
                       highlightbackground=color)

    def _reset(self, btn, color, bg):
        btn.configure(relief="flat", bd=0, highlightthickness=0)


class ScrollableFrame(tk.Frame):
    """Frame con scrollbar vertical."""

    def __init__(self, parent, **kwargs):
        bg = kwargs.pop("bg", theme.BG_BASE)
        super().__init__(parent, bg=bg, **kwargs)

        canvas = tk.Canvas(self, bg=bg, highlightthickness=0, bd=0)
        scrollbar = tk.Scrollbar(self, orient="vertical",
                                  command=canvas.yview,
                                  bg=theme.BG_SURFACE1,
                                  troughcolor=theme.BG_MANTLE)
        self.inner = tk.Frame(canvas, bg=bg)

        self.inner.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )

        self._window_id = canvas.create_window((0, 0), window=self.inner, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)

        canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        # Resize inner frame when canvas changes width
        canvas.bind("<Configure>", self._on_canvas_resize)

        # Mouse wheel
        canvas.bind_all("<MouseWheel>",
                         lambda e: canvas.yview_scroll(
                             int(-1 * (e.delta / 120)), "units"))
        self._canvas = canvas

    def _on_canvas_resize(self, event):
        self._canvas.itemconfig(self._window_id, width=event.width)


class LabeledEntry(tk.Frame):
    """Entrada de texto con etiqueta encima."""

    def __init__(self, parent, label, placeholder="", width=30, **kwargs):
        bg = kwargs.pop("bg", theme.BG_BASE)
        super().__init__(parent, bg=bg, **kwargs)

        tk.Label(self, text=label, bg=bg, fg=theme.TEXT_SECONDARY,
                 font=theme.FONT_BODY).pack(anchor="w")

        entry_frame = tk.Frame(self, bg=theme.BG_SURFACE0,
                                highlightthickness=1,
                                highlightbackground=theme.BG_SURFACE1)
        entry_frame.pack(fill=tk.X, pady=(2, 0))

        self.var = tk.StringVar()
        self.entry = tk.Entry(
            entry_frame,
            textvariable=self.var,
            bg=theme.BG_SURFACE0,
            fg=theme.TEXT_PRIMARY,
            font=theme.FONT_BODY,
            relief="flat",
            bd=6,
            insertbackground=theme.TEXT_PRIMARY,
            width=width,
        )
        self.entry.pack(fill=tk.X)

        if placeholder:
            self.entry.insert(0, placeholder)
            self.entry.config(fg=theme.TEXT_MUTED)

            def on_focus_in(e):
                if self.entry.get() == placeholder:
                    self.entry.delete(0, tk.END)
                    self.entry.config(fg=theme.TEXT_PRIMARY)

            def on_focus_out(e):
                if not self.entry.get():
                    self.entry.insert(0, placeholder)
                    self.entry.config(fg=theme.TEXT_MUTED)

            self.entry.bind("<FocusIn>", on_focus_in)
            self.entry.bind("<FocusOut>", on_focus_out)
            self._placeholder = placeholder
        else:
            self._placeholder = None

    def get(self):
        val = self.var.get()
        if val == self._placeholder:
            return ""
        return val

    def set(self, value):
        self.var.set(value)
