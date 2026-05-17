"""
TecoQC - Administrador del asistente (sidebar + área de contenido + navegación)
"""

import tkinter as tk
from tkinter import messagebox
import importlib

from config import STEPS, STATUS_PENDING, STATUS_CURRENT, STATUS_PASSED, \
    STATUS_FAILED, STATUS_SKIPPED, STATUS_ICONS, SIDEBAR_WIDTH
from ui import theme


class WizardManager(tk.Frame):
    """Marco principal que contiene el sidebar, el área de contenido y la barra de navegación."""

    def __init__(self, master):
        super().__init__(master, bg=theme.BG_BASE)

        self._steps = STEPS          # list of (num, title, module)
        self._current_idx = 0        # index into _steps
        self._step_statuses = {s[0]: STATUS_PENDING for s in STEPS}
        self._step_frames = {}       # cache of loaded step frames
        self._state = {}             # shared state dict passed to steps

        self._build_layout()
        self._goto_step(0)

    # ── Layout ─────────────────────────────────────────────────────────

    def _build_layout(self):
        """Construye la estructura principal: sidebar | contenido."""
        # Outer: sidebar on left, content on right
        self._sidebar = _Sidebar(self, self._steps, self._step_statuses,
                                  on_click=self._sidebar_click)
        self._sidebar.pack(side=tk.LEFT, fill=tk.Y)

        right = tk.Frame(self, bg=theme.BG_BASE)
        right.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        # Content area (step fills this)
        self._content_area = tk.Frame(right, bg=theme.BG_BASE)
        self._content_area.pack(fill=tk.BOTH, expand=True)

        # Navigation bar at bottom
        self._nav = _NavBar(right, on_prev=self._go_prev,
                             on_skip=self._go_skip,
                             on_next=self._go_next)
        self._nav.pack(fill=tk.X, side=tk.BOTTOM)

        # Progress label in nav
        self._update_nav_buttons()

    # ── Step loading ────────────────────────────────────────────────────

    def _load_step(self, idx):
        """Carga o recupera el frame del paso en el índice dado."""
        step_num, title, module_name = self._steps[idx]

        if step_num not in self._step_frames:
            try:
                mod = importlib.import_module(f"ui.steps.{module_name}")
                step_cls = getattr(mod, "Step")
                frame = step_cls(
                    self._content_area,
                    wizard=self,
                    state=self._state,
                    step_num=step_num,
                )
                self._step_frames[step_num] = frame
            except Exception as e:
                frame = _ErrorStep(self._content_area, module_name, e)
                self._step_frames[step_num] = frame

        return self._step_frames[step_num]

    # ── Navigation ──────────────────────────────────────────────────────

    def _goto_step(self, idx, force=False):
        """Navega al paso en el índice dado."""
        if not (0 <= idx < len(self._steps)):
            return

        # Hide current step
        for frame in self._step_frames.values():
            frame.pack_forget()

        # Update statuses
        prev_idx = self._current_idx
        if not force and prev_idx != idx:
            prev_num = self._steps[prev_idx][0]
            if self._step_statuses[prev_num] == STATUS_CURRENT:
                self._step_statuses[prev_num] = STATUS_PENDING

        self._current_idx = idx
        step_num = self._steps[idx][0]
        self._step_statuses[step_num] = STATUS_CURRENT

        # Load and show step
        frame = self._load_step(idx)
        frame.pack(fill=tk.BOTH, expand=True)

        # Notify step
        try:
            frame.on_enter()
        except Exception:
            pass

        self._sidebar.refresh(self._step_statuses, self._current_idx)
        self._update_nav_buttons()

    def _go_next(self):
        """Avanza al siguiente paso."""
        current_num = self._steps[self._current_idx][0]
        frame = self._step_frames.get(current_num)

        # Let step finalize before moving
        if frame:
            try:
                frame.on_leave()
            except Exception:
                pass

        # Mark as passed if still current/pending
        if self._step_statuses[current_num] in (STATUS_CURRENT, STATUS_PENDING):
            self._step_statuses[current_num] = STATUS_PASSED

        next_idx = self._current_idx + 1
        if next_idx < len(self._steps):
            self._goto_step(next_idx)

    def _go_prev(self):
        """Retrocede al paso anterior."""
        if self._current_idx > 0:
            current_num = self._steps[self._current_idx][0]
            if self._step_statuses[current_num] == STATUS_CURRENT:
                self._step_statuses[current_num] = STATUS_PENDING
            self._goto_step(self._current_idx - 1, force=True)

    def _go_skip(self):
        """Omite el paso actual."""
        current_num = self._steps[self._current_idx][0]
        frame = self._step_frames.get(current_num)
        if frame:
            try:
                frame.on_leave()
            except Exception:
                pass
        self._step_statuses[current_num] = STATUS_SKIPPED
        next_idx = self._current_idx + 1
        if next_idx < len(self._steps):
            self._goto_step(next_idx)

    def _sidebar_click(self, idx):
        """Maneja clic en el sidebar para navegar directamente."""
        self._goto_step(idx)

    def _update_nav_buttons(self):
        """Actualiza los botones de navegación según el paso actual."""
        idx = self._current_idx
        total = len(self._steps)
        is_first = idx == 0
        is_last = idx == total - 1

        self._nav.set_state(
            prev_enabled=not is_first,
            skip_enabled=not is_last,
            next_label="Finalizar" if is_last else "Siguiente ►",
            progress_text=f"Paso {idx + 1} de {total}",
        )

    # ── Public API for steps ────────────────────────────────────────────

    def set_step_status(self, step_num: int, status: str):
        """Permite que un paso actualice su propio estado."""
        self._step_statuses[step_num] = status
        self._sidebar.refresh(self._step_statuses, self._current_idx)

    def get_state(self) -> dict:
        return self._state

    def navigate_next(self):
        self._go_next()

    def navigate_prev(self):
        self._go_prev()


# ── Sidebar ─────────────────────────────────────────────────────────────


class _Sidebar(tk.Frame):
    """Panel lateral con lista de pasos y estado."""

    def __init__(self, parent, steps, statuses, on_click=None):
        super().__init__(parent, bg=theme.SIDEBAR_BG,
                          width=SIDEBAR_WIDTH)
        self.pack_propagate(False)

        self._steps = steps
        self._on_click = on_click
        self._item_frames = {}

        self._build_header()
        self._build_step_list(statuses, 0)
        self._build_footer()

    def _build_header(self):
        hdr = tk.Frame(self, bg=theme.SIDEBAR_HEADER_BG)
        hdr.pack(fill=tk.X)

        tk.Label(
            hdr, text="TECOLOGY",
            bg=theme.SIDEBAR_HEADER_BG,
            fg=theme.ACCENT_BLUE,
            font=(theme.FONT_FAMILY, 13, "bold"),
            pady=10,
        ).pack()

        tk.Label(
            hdr, text="TecoQC",
            bg=theme.SIDEBAR_HEADER_BG,
            fg=theme.TEXT_SECONDARY,
            font=(theme.FONT_FAMILY, 10),
            pady=0,
        ).pack()

        tk.Frame(hdr, height=1, bg=theme.BG_SURFACE2).pack(fill=tk.X, pady=8)

    def _build_step_list(self, statuses, current_idx):
        scroll_frame = tk.Frame(self, bg=theme.SIDEBAR_BG)
        scroll_frame.pack(fill=tk.BOTH, expand=True)

        canvas = tk.Canvas(scroll_frame, bg=theme.SIDEBAR_BG,
                            highlightthickness=0, bd=0)
        scrollbar = tk.Scrollbar(scroll_frame, orient="vertical",
                                  command=canvas.yview)
        self._list_inner = tk.Frame(canvas, bg=theme.SIDEBAR_BG)
        self._list_inner.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )
        canvas.create_window((0, 0), window=self._list_inner, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        canvas.bind_all(
            "<MouseWheel>",
            lambda e: canvas.yview_scroll(int(-1 * (e.delta / 120)), "units")
        )

        self._canvas = canvas
        self._build_items(statuses, current_idx)

    def _build_items(self, statuses, current_idx):
        for widget in self._list_inner.winfo_children():
            widget.destroy()
        self._item_frames = {}

        for idx, (step_num, title, _) in enumerate(self._steps):
            status = statuses.get(step_num, STATUS_PENDING)
            is_current = idx == current_idx
            self._add_step_item(idx, step_num, title, status, is_current)

    def _add_step_item(self, idx, step_num, title, status, is_current):
        bg = theme.SIDEBAR_CURRENT_BG if is_current else theme.SIDEBAR_ITEM_BG
        status_color = theme.STATUS_COLORS.get(status, theme.TEXT_MUTED)
        icon = STATUS_ICONS.get(status, "●")

        frame = tk.Frame(self._list_inner, bg=bg, cursor="hand2")
        frame.pack(fill=tk.X, pady=1, padx=4)

        inner = tk.Frame(frame, bg=bg)
        inner.pack(fill=tk.X, padx=8, pady=6)

        # Step number + icon
        num_frame = tk.Frame(inner, bg=bg)
        num_frame.pack(side=tk.LEFT)

        tk.Label(num_frame, text=f"{step_num:02d}",
                 bg=bg, fg=theme.TEXT_MUTED,
                 font=(theme.FONT_FAMILY, 9)).pack(side=tk.LEFT)

        tk.Label(num_frame, text=f" {icon}",
                 bg=bg, fg=status_color,
                 font=(theme.FONT_FAMILY, 10, "bold")).pack(side=tk.LEFT)

        # Title
        title_lbl = tk.Label(inner, text=title,
                              bg=bg,
                              fg=theme.TEXT_PRIMARY if is_current else theme.TEXT_SECONDARY,
                              font=theme.FONT_SIDEBAR,
                              anchor="w")
        title_lbl.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(6, 0))

        # Bind clicks
        for w in (frame, inner, num_frame, title_lbl):
            w.bind("<Button-1>", lambda e, i=idx: self._on_click(i) if self._on_click else None)
            w.bind("<Enter>", lambda e, f=frame, b=bg: f.configure(bg=theme.SIDEBAR_ITEM_HOVER)
                   if not is_current else None)
            w.bind("<Leave>", lambda e, f=frame, b=bg: f.configure(bg=b))

        self._item_frames[step_num] = frame

    def _build_footer(self):
        tk.Frame(self, height=1, bg=theme.BG_SURFACE2).pack(fill=tk.X)
        footer = tk.Frame(self, bg=theme.SIDEBAR_HEADER_BG)
        footer.pack(fill=tk.X, side=tk.BOTTOM)
        tk.Label(footer, text="v1.0.0 • Tecology",
                 bg=theme.SIDEBAR_HEADER_BG,
                 fg=theme.TEXT_MUTED,
                 font=(theme.FONT_FAMILY, 9),
                 pady=8).pack()

    def refresh(self, statuses, current_idx):
        """Reconstruye la lista de pasos con estados actualizados."""
        self._build_items(statuses, current_idx)


# ── Navigation bar ───────────────────────────────────────────────────────


class _NavBar(tk.Frame):
    """Barra de navegación inferior con botones Anterior / Omitir / Siguiente."""

    def __init__(self, parent, on_prev=None, on_skip=None, on_next=None):
        super().__init__(parent, bg=theme.BG_MANTLE,
                          highlightthickness=1,
                          highlightbackground=theme.BG_SURFACE2)

        self._on_prev = on_prev
        self._on_skip = on_skip
        self._on_next = on_next

        # Progress text
        self._progress_lbl = tk.Label(
            self, text="",
            bg=theme.BG_MANTLE,
            fg=theme.TEXT_MUTED,
            font=theme.FONT_SMALL,
        )
        self._progress_lbl.pack(side=tk.LEFT, padx=16, pady=10)

        # Right buttons
        btn_frame = tk.Frame(self, bg=theme.BG_MANTLE)
        btn_frame.pack(side=tk.RIGHT, padx=16, pady=8)

        self._prev_btn = tk.Button(
            btn_frame, text="◄ Anterior",
            command=lambda: on_prev() if on_prev else None,
            **theme.BTN_SECONDARY,
        )
        self._prev_btn.pack(side=tk.LEFT, padx=(0, 6))

        self._skip_btn = tk.Button(
            btn_frame, text="Omitir",
            command=lambda: on_skip() if on_skip else None,
            **theme.BTN_WARNING,
        )
        self._skip_btn.pack(side=tk.LEFT, padx=(0, 6))

        self._next_btn = tk.Button(
            btn_frame, text="Siguiente ►",
            command=lambda: on_next() if on_next else None,
            **theme.BTN_PRIMARY,
        )
        self._next_btn.pack(side=tk.LEFT)

    def set_state(self, prev_enabled=True, skip_enabled=True,
                  next_label="Siguiente ►", progress_text=""):
        self._prev_btn.configure(state=tk.NORMAL if prev_enabled else tk.DISABLED)
        self._skip_btn.configure(state=tk.NORMAL if skip_enabled else tk.DISABLED)
        self._next_btn.configure(text=next_label)
        self._progress_lbl.configure(text=progress_text)


# ── Error placeholder ────────────────────────────────────────────────────


class _ErrorStep(tk.Frame):
    def __init__(self, parent, module_name, error):
        super().__init__(parent, bg=theme.BG_BASE)
        tk.Label(
            self,
            text=f"Error al cargar módulo: {module_name}\n\n{error}",
            bg=theme.BG_BASE,
            fg=theme.ERROR,
            font=theme.FONT_BODY,
            wraplength=600,
            justify="left",
        ).pack(expand=True)

    def on_enter(self):
        pass

    def on_leave(self):
        pass
