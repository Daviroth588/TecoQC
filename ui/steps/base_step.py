"""
TecoQC - Clase base abstracta para todos los pasos del asistente
"""

import tkinter as tk
from ui import theme
from ui.components import NotesFrame, StatusBadge, ScrollableFrame
from config import STATUS_PASSED, STATUS_FAILED, STATUS_SKIPPED, STATUS_PENDING


class BaseStep(tk.Frame):
    """
    Clase base para todos los pasos del asistente.

    Subclases deben implementar:
        - build_ui()  → construir el contenido del paso

    Subclases pueden sobreescribir:
        - on_enter()  → llamado al entrar al paso
        - on_leave()  → llamado al salir del paso
    """

    TITLE = "Paso"
    DESCRIPTION = ""
    STEP_NUM = 0

    def __init__(self, parent, wizard=None, state=None, step_num=None):
        super().__init__(parent, bg=theme.BG_BASE)
        self._wizard = wizard
        self._state = state if state is not None else {}
        self._step_num = step_num or self.STEP_NUM
        self._status = STATUS_PENDING
        self._notes_widget = None

        # Ensure step result dict exists in state
        if "step_results" not in self._state:
            self._state["step_results"] = {}
        if self._step_num not in self._state["step_results"]:
            self._state["step_results"][self._step_num] = {
                "status": STATUS_PENDING,
                "notes": "",
                "details": "",
            }

        self._build_wrapper()

    # ── Wrapper (header + scrollable content + status + notes) ──────────

    def _build_wrapper(self):
        # ── Step header ────────────────────────────────────────────────
        header = tk.Frame(self, bg=theme.BG_MANTLE,
                           highlightthickness=1,
                           highlightbackground=theme.BG_SURFACE2)
        header.pack(fill=tk.X)

        hdr_inner = tk.Frame(header, bg=theme.BG_MANTLE)
        hdr_inner.pack(fill=tk.X, padx=24, pady=14)

        left = tk.Frame(hdr_inner, bg=theme.BG_MANTLE)
        left.pack(side=tk.LEFT, fill=tk.X, expand=True)

        tk.Label(
            left,
            text=self.TITLE,
            bg=theme.BG_MANTLE,
            fg=theme.TEXT_PRIMARY,
            font=theme.FONT_H2,
            anchor="w",
        ).pack(anchor="w")

        if self.DESCRIPTION:
            tk.Label(
                left,
                text=self.DESCRIPTION,
                bg=theme.BG_MANTLE,
                fg=theme.TEXT_SECONDARY,
                font=theme.FONT_BODY,
                anchor="w",
                wraplength=700,
            ).pack(anchor="w", pady=(2, 0))

        # Status badge on the right
        self._status_badge = StatusBadge(hdr_inner, status="pending",
                                          bg=theme.BG_MANTLE)
        self._status_badge.pack(side=tk.RIGHT, padx=(12, 0))

        # ── Scrollable content area ────────────────────────────────────
        self._scroll = ScrollableFrame(self, bg=theme.BG_BASE)
        self._scroll.pack(fill=tk.BOTH, expand=True)

        content_padded = tk.Frame(self._scroll.inner, bg=theme.BG_BASE)
        content_padded.pack(fill=tk.BOTH, expand=True, padx=24, pady=16)

        # Subclass builds here
        self.build_ui(content_padded)

        # ── Notes section ──────────────────────────────────────────────
        sep = tk.Frame(self._scroll.inner, height=1, bg=theme.BG_SURFACE2)
        sep.pack(fill=tk.X, padx=24, pady=(8, 0))

        notes_outer = tk.Frame(self._scroll.inner, bg=theme.BG_BASE)
        notes_outer.pack(fill=tk.X, padx=24, pady=8)

        self._notes_widget = NotesFrame(notes_outer, bg=theme.BG_BASE)
        self._notes_widget.pack(fill=tk.X)

        # ── Pass / Fail buttons ────────────────────────────────────────
        action_frame = tk.Frame(self._scroll.inner, bg=theme.BG_BASE)
        action_frame.pack(fill=tk.X, padx=24, pady=(0, 12))

        tk.Button(
            action_frame,
            text="✓  Marcar Aprobado",
            command=self._mark_passed,
            **theme.BTN_SUCCESS,
        ).pack(side=tk.LEFT, padx=(0, 8))

        tk.Button(
            action_frame,
            text="✗  Marcar Fallido",
            command=self._mark_failed,
            **theme.BTN_DANGER,
        ).pack(side=tk.LEFT)

    # ── Abstract method ─────────────────────────────────────────────────

    def build_ui(self, parent):
        """Subclases implementan aquí el contenido del paso."""
        tk.Label(parent, text="(Sin contenido)", bg=theme.BG_BASE,
                 fg=theme.TEXT_MUTED, font=theme.FONT_BODY).pack()

    # ── Lifecycle hooks ─────────────────────────────────────────────────

    def on_enter(self):
        """Llamado al entrar al paso. Sobreescribir si es necesario."""
        pass

    def on_leave(self):
        """Llamado al salir del paso. Guarda notas en el estado."""
        self._save_notes()

    # ── Status helpers ──────────────────────────────────────────────────

    def _mark_passed(self):
        self.set_status(STATUS_PASSED)

    def _mark_failed(self):
        self.set_status(STATUS_FAILED)

    def set_status(self, status: str, details: str = ""):
        self._status = status
        self._status_badge.set_status(status)
        if self._wizard:
            self._wizard.set_step_status(self._step_num, status)
        result = self._state["step_results"].setdefault(self._step_num, {})
        result["status"] = status
        if details:
            result["details"] = details

    def get_status(self) -> str:
        return self._status

    def _save_notes(self):
        if self._notes_widget:
            notes = self._notes_widget.get()
            result = self._state["step_results"].setdefault(self._step_num, {})
            result["notes"] = notes

    def _set_detail(self, text: str):
        result = self._state["step_results"].setdefault(self._step_num, {})
        result["details"] = text

    # ── Convenience ─────────────────────────────────────────────────────

    def run_in_thread(self, target, on_done=None, on_error=None):
        """Ejecuta `target` en un hilo daemon y llama `on_done` en el hilo principal."""
        import threading

        def _run():
            try:
                result = target()
                if on_done:
                    self.after(0, lambda: on_done(result))
            except Exception as e:
                if on_error:
                    self.after(0, lambda: on_error(e))

        t = threading.Thread(target=_run, daemon=True)
        t.start()
        return t
