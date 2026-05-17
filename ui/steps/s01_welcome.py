"""
TecoQC - Paso 1: Bienvenida e información del técnico
"""

import tkinter as tk
import datetime

from ui.steps.base_step import BaseStep
from ui.components import LabeledEntry, Card
from ui import theme
from config import STATUS_PASSED


class Step(BaseStep):
    TITLE = "Bienvenido al Sistema de Control de Calidad"
    DESCRIPTION = ("Complete la información del técnico y del dispositivo antes de comenzar "
                   "la inspección.")
    STEP_NUM = 1

    def build_ui(self, parent):
        # Welcome banner
        banner = tk.Frame(parent, bg=theme.BG_SURFACE0,
                           highlightthickness=1,
                           highlightbackground=theme.ACCENT_BLUE)
        banner.pack(fill=tk.X, pady=(0, 20))

        tk.Label(
            banner,
            text="🔍  TecoQC — Sistema de Verificación de Hardware",
            bg=theme.BG_SURFACE0,
            fg=theme.ACCENT_BLUE,
            font=theme.FONT_H1,
            pady=20,
        ).pack()

        tk.Label(
            banner,
            text="Este asistente le guiará paso a paso en la verificación completa "
                 "de todos los componentes del equipo.\n"
                 "Complete el formulario a continuación para comenzar.",
            bg=theme.BG_SURFACE0,
            fg=theme.TEXT_SECONDARY,
            font=theme.FONT_BODY,
            wraplength=680,
            justify="center",
        ).pack(pady=(0, 16))

        # Form card
        form_card = Card(parent)
        form_card.pack(fill=tk.X, pady=(0, 16))

        inner = tk.Frame(form_card, bg=theme.BG_SURFACE0)
        inner.pack(fill=tk.X, padx=24, pady=20)

        tk.Label(
            inner,
            text="Información del Técnico y Dispositivo",
            bg=theme.BG_SURFACE0,
            fg=theme.TEXT_PRIMARY,
            font=theme.FONT_H3,
        ).grid(row=0, column=0, columnspan=2, sticky="w", pady=(0, 16))

        # Technician name
        self._tech_entry = LabeledEntry(
            inner, "Nombre del Técnico", placeholder="Ej. Juan García",
            bg=theme.BG_SURFACE0, width=35,
        )
        self._tech_entry.grid(row=1, column=0, padx=(0, 24), pady=8, sticky="ew")

        # Date
        date_frame = tk.Frame(inner, bg=theme.BG_SURFACE0)
        date_frame.grid(row=1, column=1, pady=8, sticky="ew")

        tk.Label(date_frame, text="Fecha de Inspección",
                 bg=theme.BG_SURFACE0, fg=theme.TEXT_SECONDARY,
                 font=theme.FONT_BODY).pack(anchor="w")

        entry_wrap = tk.Frame(date_frame, bg=theme.BG_SURFACE0,
                               highlightthickness=1,
                               highlightbackground=theme.BG_SURFACE1)
        entry_wrap.pack(fill=tk.X, pady=(2, 0))

        self._date_var = tk.StringVar(value=datetime.date.today().isoformat())
        tk.Entry(
            entry_wrap,
            textvariable=self._date_var,
            bg=theme.BG_SURFACE0,
            fg=theme.TEXT_PRIMARY,
            font=theme.FONT_BODY,
            relief="flat",
            bd=6,
            insertbackground=theme.TEXT_PRIMARY,
        ).pack(fill=tk.X)

        # Device serial / Teco Tag
        self._serial_entry = LabeledEntry(
            inner, "Teco Tag",
            placeholder="Ej. TT-2024-001",
            bg=theme.BG_SURFACE0, width=35,
        )
        self._serial_entry.grid(row=2, column=0, padx=(0, 24), pady=8, sticky="ew")

        # Device model
        self._model_entry = LabeledEntry(
            inner, "Modelo del Equipo",
            placeholder="Ej. HP ProBook 450 G9",
            bg=theme.BG_SURFACE0, width=35,
        )
        self._model_entry.grid(row=2, column=1, pady=8, sticky="ew")

        inner.columnconfigure(0, weight=1)
        inner.columnconfigure(1, weight=1)

        # Instructions card
        instr_card = Card(parent)
        instr_card.pack(fill=tk.X, pady=(0, 16))

        instr_inner = tk.Frame(instr_card, bg=theme.BG_SURFACE0)
        instr_inner.pack(fill=tk.X, padx=24, pady=16)

        tk.Label(instr_inner, text="Instrucciones de uso",
                 bg=theme.BG_SURFACE0, fg=theme.TEXT_PRIMARY,
                 font=theme.FONT_H3).pack(anchor="w", pady=(0, 10))

        instructions = [
            ("►", "Navegue usando los botones Anterior / Siguiente en la parte inferior."),
            ("⊘", "Use 'Omitir' para saltar una prueba que no aplique."),
            ("✓", "Marque 'Aprobado' cuando el componente funcione correctamente."),
            ("✗", "Marque 'Fallido' si el componente presenta problemas."),
            ("📝", "Agregue notas en el campo de texto al pie de cada paso."),
            ("📋", "El reporte final se generará automáticamente al finalizar."),
        ]

        for icon, text in instructions:
            row = tk.Frame(instr_inner, bg=theme.BG_SURFACE0)
            row.pack(fill=tk.X, pady=3)
            tk.Label(row, text=icon, bg=theme.BG_SURFACE0,
                     fg=theme.ACCENT_BLUE, font=theme.FONT_BODY,
                     width=3).pack(side=tk.LEFT)
            tk.Label(row, text=text, bg=theme.BG_SURFACE0,
                     fg=theme.TEXT_SECONDARY, font=theme.FONT_BODY,
                     anchor="w").pack(side=tk.LEFT, fill=tk.X)

        # Start button
        tk.Button(
            parent,
            text="▶  Iniciar Inspección",
            command=self._start,
            **theme.BTN_PRIMARY,
        ).pack(anchor="center", pady=10)

        # Restore values if already entered
        if self._state.get("technician_name"):
            self._tech_entry.set(self._state["technician_name"])
        if self._state.get("device_serial"):
            self._serial_entry.set(self._state["device_serial"])
        if self._state.get("device_model"):
            self._model_entry.set(self._state["device_model"])
        if self._state.get("report_date"):
            self._date_var.set(self._state["report_date"])

    def _start(self):
        tech = self._tech_entry.get().strip()
        serial = self._serial_entry.get().strip()
        model = self._model_entry.get().strip()
        date = self._date_var.get().strip()

        if not tech:
            tk.messagebox.showwarning(
                "Campos requeridos",
                "Por favor ingrese el nombre del técnico.",
            )
            return

        if not serial:
            tk.messagebox.showwarning(
                "Campos requeridos",
                "Por favor ingrese el Teco Tag del equipo.",
            )
            return

        self._state["technician_name"] = tech
        self._state["device_serial"] = serial
        self._state["device_model"] = model
        self._state["report_date"] = date
        self._state["company"] = "Tecology"

        self.set_status(STATUS_PASSED,
                        f"Técnico: {tech} | Teco Tag: {serial}")
        if self._wizard:
            self._wizard.navigate_next()

    def on_leave(self):
        super().on_leave()
        # Auto-save fields on leave
        tech = self._tech_entry.get().strip() if hasattr(self, "_tech_entry") else ""
        if tech:
            self._state["technician_name"] = tech
        serial = self._serial_entry.get().strip() if hasattr(self, "_serial_entry") else ""
        if serial:
            self._state["device_serial"] = serial
        model = self._model_entry.get().strip() if hasattr(self, "_model_entry") else ""
        if model:
            self._state["device_model"] = model
