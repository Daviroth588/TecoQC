"""
TecoQC - Paso 15: Reporte final de control de calidad
"""

import tkinter as tk
import os
import datetime

from ui.steps.base_step import BaseStep
from ui.components import Card
from ui import theme
from config import STATUS_PASSED, STATUS_FAILED, STATUS_SKIPPED, STATUS_PENDING, STATUS_LABELS


STEP_NAMES = {
    1: "Bienvenida", 2: "Sistema", 3: "Teclado", 4: "Trackpad",
    5: "Pantalla", 6: "Cámara", 7: "Puertos USB", 8: "Red",
    9: "Audio", 10: "CPU", 11: "GPU", 12: "Memoria RAM",
    13: "Almacenamiento", 14: "Batería",
}

STATUS_FG = {
    STATUS_PASSED:  theme.SUCCESS,
    STATUS_FAILED:  theme.ERROR,
    STATUS_SKIPPED: theme.WARNING,
    STATUS_PENDING: theme.TEXT_MUTED,
}

STATUS_ICON = {
    STATUS_PASSED:  "✓",
    STATUS_FAILED:  "✗",
    STATUS_SKIPPED: "⊘",
    STATUS_PENDING: "●",
}


class Step(BaseStep):
    TITLE = "Reporte Final de Control de Calidad"
    DESCRIPTION = "Resumen completo de todos los resultados. Genere el reporte HTML."
    STEP_NUM = 15

    def build_ui(self, parent):
        self._report_path = None

        # Top summary bar
        self._summary_bar = tk.Frame(parent, bg=theme.BG_BASE)
        self._summary_bar.pack(fill=tk.X, pady=(0, 16))

        self._summary_cards = {}
        for key, label, color in [
            ("passed",  "Aprobados",  theme.SUCCESS),
            ("failed",  "Fallidos",   theme.ERROR),
            ("skipped", "Omitidos",   theme.WARNING),
            ("pending", "Pendientes", theme.TEXT_MUTED),
        ]:
            c = tk.Frame(self._summary_bar, bg=color, width=140)
            c.pack(side=tk.LEFT, padx=(0, 8), fill=tk.Y)
            c.pack_propagate(False)
            num_lbl = tk.Label(c, text="0", bg=color, fg=theme.BG_BASE,
                                font=(theme.FONT_FAMILY, 28, "bold"), pady=10)
            num_lbl.pack()
            tk.Label(c, text=label, bg=color, fg=theme.BG_BASE,
                      font=theme.FONT_BODY_BOLD, pady=(0, 8)).pack()
            self._summary_cards[key] = num_lbl

        # Overall result
        self._overall_frame = tk.Frame(self._summary_bar, bg=theme.BG_BASE)
        self._overall_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=16)

        self._overall_lbl = tk.Label(
            self._overall_frame,
            text="RESULTADO GENERAL",
            bg=theme.BG_BASE, fg=theme.TEXT_MUTED,
            font=(theme.FONT_FAMILY, 11, "bold"),
        )
        self._overall_lbl.pack(anchor="w")

        self._overall_status_lbl = tk.Label(
            self._overall_frame,
            text="—",
            bg=theme.BG_BASE, fg=theme.TEXT_MUTED,
            font=(theme.FONT_FAMILY, 32, "bold"),
        )
        self._overall_status_lbl.pack(anchor="w")

        # Results table
        tk.Label(parent, text="Resultados por Componente",
                 bg=theme.BG_BASE, fg=theme.TEXT_PRIMARY,
                 font=theme.FONT_H3).pack(anchor="w", pady=(0, 8))

        table_card = Card(parent)
        table_card.pack(fill=tk.X, pady=(0, 12))

        # Table header
        hdr = tk.Frame(table_card, bg=theme.BG_SURFACE1)
        hdr.pack(fill=tk.X)
        for col, w in [("#", 30), ("Componente", 180), ("Estado", 110),
                        ("Detalles", 300), ("Notas", 200)]:
            tk.Label(hdr, text=col, bg=theme.BG_SURFACE1, fg=theme.TEXT_MUTED,
                     font=theme.FONT_SMALL, width=w//7, anchor="w",
                     padx=8, pady=6).pack(side=tk.LEFT)

        # Table rows
        self._table_rows_frame = tk.Frame(table_card, bg=theme.BG_SURFACE0)
        self._table_rows_frame.pack(fill=tk.X)

        # ── Report generation ──────────────────────────────────────────
        gen_card = Card(parent)
        gen_card.pack(fill=tk.X, pady=(0, 8))

        gen_inner = tk.Frame(gen_card, bg=theme.BG_SURFACE0)
        gen_inner.pack(fill=tk.X, padx=16, pady=14)

        tk.Label(gen_inner, text="Generar Reporte",
                 bg=theme.BG_SURFACE0, fg=theme.ACCENT_BLUE,
                 font=theme.FONT_H3).pack(anchor="w", pady=(0, 10))

        btn_row = tk.Frame(gen_inner, bg=theme.BG_SURFACE0)
        btn_row.pack(anchor="w")

        self._gen_btn = tk.Button(
            btn_row, text="📋  Generar Reporte HTML",
            command=self._generate_report, **theme.BTN_PRIMARY,
        )
        self._gen_btn.pack(side=tk.LEFT, padx=(0, 12))

        self._open_btn = tk.Button(
            btn_row, text="🌐  Abrir en navegador",
            command=self._open_report,
            state=tk.DISABLED, **theme.BTN_SECONDARY,
        )
        self._open_btn.pack(side=tk.LEFT)

        self._report_status_lbl = tk.Label(
            gen_inner, text="",
            bg=theme.BG_SURFACE0, fg=theme.TEXT_SECONDARY, font=theme.FONT_BODY,
        )
        self._report_status_lbl.pack(anchor="w", pady=(10, 0))

        # Technician info display
        self._tech_info_lbl = tk.Label(
            gen_inner, text="",
            bg=theme.BG_SURFACE0, fg=theme.TEXT_MUTED, font=theme.FONT_SMALL,
        )
        self._tech_info_lbl.pack(anchor="w")

    def on_enter(self):
        """Refresh the summary each time this step is shown."""
        self._refresh_table()
        self._update_summary()

        # Show tech info
        tech = self._state.get("technician_name", "N/D")
        serial = self._state.get("device_serial", "N/D")
        model = self._state.get("device_model", "N/D")
        date = self._state.get("report_date", datetime.date.today().isoformat())
        self._tech_info_lbl.configure(
            text=f"Técnico: {tech}  |  S/N: {serial}  |  Modelo: {model}  |  Fecha: {date}"
        )

    def _refresh_table(self):
        for w in self._table_rows_frame.winfo_children():
            w.destroy()

        step_results = self._state.get("step_results", {})

        for step_num in range(1, 15):
            name = STEP_NAMES.get(step_num, f"Paso {step_num}")
            result = step_results.get(step_num, {})
            status = result.get("status", STATUS_PENDING)
            details = result.get("details", "") or ""
            notes = result.get("notes", "") or ""

            bg = theme.BG_SURFACE0 if step_num % 2 == 1 else theme.BG_MANTLE
            row = tk.Frame(self._table_rows_frame, bg=bg)
            row.pack(fill=tk.X)

            fg = STATUS_FG.get(status, theme.TEXT_MUTED)
            icon = STATUS_ICON.get(status, "●")
            label_text = STATUS_LABELS.get(status, status)

            # Number
            tk.Label(row, text=f"{step_num:02d}", bg=bg,
                     fg=theme.TEXT_MUTED, font=theme.FONT_SMALL,
                     width=4, padx=8, pady=5).pack(side=tk.LEFT)

            # Name
            tk.Label(row, text=name, bg=bg,
                     fg=theme.TEXT_PRIMARY, font=theme.FONT_BODY,
                     width=25, anchor="w", padx=4).pack(side=tk.LEFT)

            # Status badge
            badge_frame = tk.Frame(row, bg=bg)
            badge_frame.pack(side=tk.LEFT, padx=4)
            tk.Label(badge_frame, text=f"{icon} {label_text}",
                     bg=bg, fg=fg, font=theme.FONT_BODY_BOLD,
                     width=14, anchor="w").pack()

            # Details
            tk.Label(row, text=details[:40] if details else "—",
                     bg=bg, fg=theme.TEXT_SECONDARY, font=theme.FONT_SMALL,
                     width=42, anchor="w", padx=4).pack(side=tk.LEFT)

            # Notes
            tk.Label(row, text=notes[:30] if notes else "—",
                     bg=bg, fg=theme.TEXT_MUTED, font=theme.FONT_SMALL,
                     width=28, anchor="w", padx=4).pack(side=tk.LEFT)

    def _update_summary(self):
        step_results = self._state.get("step_results", {})
        counts = {s: 0 for s in (STATUS_PASSED, STATUS_FAILED, STATUS_SKIPPED, STATUS_PENDING)}

        for step_num in range(1, 15):
            result = step_results.get(step_num, {})
            status = result.get("status", STATUS_PENDING)
            if status in counts:
                counts[status] += 1

        for key, lbl in self._summary_cards.items():
            lbl.configure(text=str(counts.get(key, 0)))

        failed = counts[STATUS_FAILED]
        passed = counts[STATUS_PASSED]
        total = 14

        if failed == 0 and passed + counts[STATUS_SKIPPED] == total:
            self._overall_status_lbl.configure(
                text="✓ APROBADO", fg=theme.SUCCESS)
        elif failed > 0:
            self._overall_status_lbl.configure(
                text=f"✗ FALLIDO ({failed} fallo{'s' if failed > 1 else ''})",
                fg=theme.ERROR)
        else:
            pending = counts[STATUS_PENDING]
            self._overall_status_lbl.configure(
                text=f"● INCOMPLETO ({pending} pendiente{'s' if pending > 1 else ''})",
                fg=theme.WARNING)

    def _generate_report(self):
        self._gen_btn.configure(state=tk.DISABLED)
        self._report_status_lbl.configure(
            text="⏳ Generando reporte HTML...", fg=theme.ACCENT_BLUE)
        self.run_in_thread(self._do_generate, on_done=self._show_report_result,
                            on_error=self._report_error)

    def _do_generate(self):
        from report.generator import generate_html_report
        return generate_html_report(self._state)

    def _show_report_result(self, path):
        self._gen_btn.configure(state=tk.NORMAL)
        self._report_path = path
        self._open_btn.configure(state=tk.NORMAL)
        self._report_status_lbl.configure(
            text=f"✓ Reporte guardado:\n{path}", fg=theme.SUCCESS)
        self.set_status(STATUS_PASSED, f"Reporte generado: {os.path.basename(path)}")

    def _report_error(self, error):
        self._gen_btn.configure(state=tk.NORMAL)
        self._report_status_lbl.configure(
            text=f"✗ Error al generar reporte: {error}", fg=theme.ERROR)

    def _open_report(self):
        if self._report_path and os.path.exists(self._report_path):
            try:
                os.startfile(self._report_path)
            except Exception as e:
                import subprocess
                try:
                    subprocess.Popen(["start", self._report_path], shell=True)
                except Exception:
                    self._report_status_lbl.configure(
                        text=f"Error al abrir: {e}", fg=theme.ERROR)
