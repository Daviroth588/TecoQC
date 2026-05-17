"""
TecoQC - Paso 12: Información de memoria RAM y prueba de asignación
"""

import tkinter as tk
import threading
import time

from ui.steps.base_step import BaseStep
from ui.components import Card, InfoRow, Spinner
from ui import theme
from config import STATUS_PASSED, STATUS_FAILED


class Step(BaseStep):
    TITLE = "Memoria RAM"
    DESCRIPTION = ("Información detallada de módulos RAM: ranuras, velocidad, tipo "
                   "y prueba básica de asignación de memoria.")
    STEP_NUM = 12

    def build_ui(self, parent):
        self._monitoring = False

        cols = tk.Frame(parent, bg=theme.BG_BASE)
        cols.pack(fill=tk.BOTH, expand=True)
        cols.columnconfigure(0, weight=1)
        cols.columnconfigure(1, weight=1)

        # ── Summary card ───────────────────────────────────────────────
        sum_card = Card(cols)
        sum_card.grid(row=0, column=0, padx=(0, 8), pady=0, sticky="nsew")

        tk.Label(sum_card, text="Resumen de Memoria",
                 bg=theme.BG_SURFACE0, fg=theme.ACCENT_BLUE,
                 font=theme.FONT_H3).pack(anchor="w", padx=16, pady=(12, 6))
        tk.Frame(sum_card, height=1, bg=theme.BG_SURFACE2).pack(fill=tk.X, padx=16)

        self._sum_inner = tk.Frame(sum_card, bg=theme.BG_SURFACE0)
        self._sum_inner.pack(fill=tk.X, padx=16, pady=10)

        self._sum_spinner = Spinner(self._sum_inner, text="Obteniendo info RAM...",
                                     bg=theme.BG_SURFACE0)
        self._sum_spinner.pack(pady=12)
        self._sum_spinner.start()

        # Usage bar
        usage_frame = tk.Frame(sum_card, bg=theme.BG_SURFACE0)
        usage_frame.pack(fill=tk.X, padx=16, pady=(8, 10))

        tk.Label(usage_frame, text="Uso actual:",
                 bg=theme.BG_SURFACE0, fg=theme.TEXT_SECONDARY,
                 font=theme.FONT_BODY).pack(anchor="w", pady=(0, 4))

        self._ram_bar = tk.Canvas(usage_frame, height=24, bg=theme.BG_SURFACE1,
                                   highlightthickness=1,
                                   highlightbackground=theme.BG_SURFACE2)
        self._ram_bar.pack(fill=tk.X)
        self._ram_pct_lbl = tk.Label(usage_frame, text="",
                                      bg=theme.BG_SURFACE0, fg=theme.TEXT_PRIMARY,
                                      font=theme.FONT_BODY)
        self._ram_pct_lbl.pack(anchor="e", pady=(2, 0))

        # ── Slot info card ─────────────────────────────────────────────
        slot_card = Card(cols)
        slot_card.grid(row=0, column=1, padx=(8, 0), pady=0, sticky="nsew")

        tk.Label(slot_card, text="Módulos de Memoria (Ranuras)",
                 bg=theme.BG_SURFACE0, fg=theme.ACCENT_BLUE,
                 font=theme.FONT_H3).pack(anchor="w", padx=16, pady=(12, 6))
        tk.Frame(slot_card, height=1, bg=theme.BG_SURFACE2).pack(fill=tk.X, padx=16)

        self._slot_inner = tk.Frame(slot_card, bg=theme.BG_SURFACE0)
        self._slot_inner.pack(fill=tk.BOTH, expand=True, padx=16, pady=10)

        self._slot_spinner = Spinner(self._slot_inner, text="Consultando WMI...",
                                      bg=theme.BG_SURFACE0)
        self._slot_spinner.pack(pady=12)
        self._slot_spinner.start()

        # ── Memory test ────────────────────────────────────────────────
        test_card = Card(parent)
        test_card.pack(fill=tk.X, pady=(8, 0))

        tk.Label(test_card, text="Prueba de Integridad de Memoria",
                 bg=theme.BG_SURFACE0, fg=theme.ACCENT_BLUE,
                 font=theme.FONT_H3).pack(anchor="w", padx=16, pady=(12, 6))
        tk.Frame(test_card, height=1, bg=theme.BG_SURFACE2).pack(fill=tk.X, padx=16)

        test_inner = tk.Frame(test_card, bg=theme.BG_SURFACE0)
        test_inner.pack(fill=tk.X, padx=16, pady=10)

        tk.Label(test_inner,
                 text="Escribe 6 patrones distintos en memoria y verifica que los datos leídos "
                      "coincidan exactamente. Detecta bits pegados, errores de datos y fallas de "
                      "direccionamiento.",
                 bg=theme.BG_SURFACE0, fg=theme.TEXT_SECONDARY,
                 font=theme.FONT_BODY, wraplength=700, justify="left").pack(anchor="w", pady=(0, 8))

        # Size selector
        size_row = tk.Frame(test_inner, bg=theme.BG_SURFACE0)
        size_row.pack(anchor="w", pady=(0, 8))

        tk.Label(size_row, text="Tamaño:", bg=theme.BG_SURFACE0,
                 fg=theme.TEXT_SECONDARY, font=theme.FONT_BODY).pack(side=tk.LEFT, padx=(0, 10))

        self._test_size_var = tk.IntVar(value=256)
        for label, mb in [("64 MB", 64), ("128 MB", 128), ("256 MB", 256), ("512 MB", 512)]:
            tk.Radiobutton(
                size_row, text=label, variable=self._test_size_var, value=mb,
                bg=theme.BG_SURFACE0, fg=theme.TEXT_PRIMARY,
                selectcolor=theme.BG_SURFACE1,
                activebackground=theme.BG_SURFACE0,
                font=theme.FONT_BODY, indicatoron=0,
                relief="flat", padx=10, pady=4, cursor="hand2",
            ).pack(side=tk.LEFT, padx=3)

        btn_row = tk.Frame(test_inner, bg=theme.BG_SURFACE0)
        btn_row.pack(anchor="w", pady=(0, 8))

        self._test_btn = tk.Button(btn_row, text="▶  Iniciar prueba de memoria",
                                    command=self._run_mem_test, **theme.BTN_PRIMARY)
        self._test_btn.pack(side=tk.LEFT, padx=(0, 12))

        self._stop_btn = tk.Button(btn_row, text="■  Detener",
                                    command=self._stop_mem_test, **theme.BTN_SECONDARY,
                                    state=tk.DISABLED)
        self._stop_btn.pack(side=tk.LEFT)

        # Current phase label
        self._phase_lbl = tk.Label(test_inner, text="",
                                    bg=theme.BG_SURFACE0, fg=theme.ACCENT_BLUE,
                                    font=theme.FONT_BODY_BOLD)
        self._phase_lbl.pack(anchor="w")

        # Overall progress bar
        prog_wrap = tk.Frame(test_inner, bg=theme.BG_SURFACE1,
                              highlightthickness=1, highlightbackground=theme.BG_SURFACE2)
        prog_wrap.pack(fill=tk.X, pady=(4, 8))
        self._prog_canvas = tk.Canvas(prog_wrap, height=18, bg=theme.BG_SURFACE1,
                                       highlightthickness=0)
        self._prog_canvas.pack(fill=tk.X)

        # Phase results table (shown after test)
        self._results_frame = tk.Frame(test_inner, bg=theme.BG_SURFACE0)
        self._results_frame.pack(fill=tk.X)

        self._test_lbl = tk.Label(test_inner, text="",
                                   bg=theme.BG_SURFACE0, fg=theme.TEXT_SECONDARY,
                                   font=theme.FONT_BODY)
        self._test_lbl.pack(anchor="w", pady=(4, 0))

        # Internal state
        self._stop_event = None
        self._test_running = False

        # Load hardware data
        self.run_in_thread(self._collect, on_done=self._show_info,
                            on_error=self._show_error)

    def on_enter(self):
        self._monitoring = True
        self._start_usage_monitor()

    def on_leave(self):
        super().on_leave()
        self._monitoring = False

    def _collect(self):
        from hardware.memory import get_memory_info, get_ram_slots_info, get_physical_memory_array
        return {
            "summary": get_memory_info(),
            "slots": get_ram_slots_info(),
            "array": get_physical_memory_array(),
        }

    def _show_info(self, data):
        self._sum_spinner.stop()
        self._sum_spinner.pack_forget()
        self._slot_spinner.stop()
        self._slot_spinner.pack_forget()

        summary = data.get("summary", {})
        slots = data.get("slots", [])
        array = data.get("array", {})

        # Separate valid slots from error entries up front
        real_slots = [s for s in slots if "error" not in s]
        error_slots = [s for s in slots if "error" in s]

        # Summary fields
        fields = [
            ("Total", f"{summary.get('total_gb', 0):.2f} GB"),
            ("Disponible", f"{summary.get('available_gb', 0):.2f} GB"),
            ("En uso", f"{summary.get('used_gb', 0):.2f} GB"),
            ("Ranuras totales", str(array.get("memory_devices", "N/D"))),
            ("Ranuras usadas", str(len(real_slots))),
            ("Cap. máxima", f"{array.get('max_capacity_gb', 0):.0f} GB"),
        ]
        for label, val in fields:
            InfoRow(self._sum_inner, label, val,
                    label_width=16, bg=theme.BG_SURFACE0).pack(fill=tk.X, pady=2)

        # Slot details

        if real_slots:
            for slot in real_slots:
                source_tag = " (PowerShell)" if slot.get("source") == "powershell" else ""
                slot_card = tk.Frame(self._slot_inner, bg=theme.BG_MANTLE,
                                      highlightthickness=1,
                                      highlightbackground=theme.BG_SURFACE2)
                slot_card.pack(fill=tk.X, pady=4)

                hdr_bg = theme.BG_SURFACE1
                hdr = tk.Frame(slot_card, bg=hdr_bg)
                hdr.pack(fill=tk.X)
                tk.Label(hdr,
                          text=f"Ranura: {slot.get('device_locator', 'N/D')}  "
                               f"({slot.get('bank_label', '')}){source_tag}",
                          bg=hdr_bg, fg=theme.TEXT_PRIMARY,
                          font=theme.FONT_BODY_BOLD, padx=10, pady=4).pack(anchor="w")

                inner = tk.Frame(slot_card, bg=theme.BG_MANTLE)
                inner.pack(fill=tk.X, padx=10, pady=6)

                slot_fields = [
                    ("Capacidad", f"{slot.get('capacity_gb', 0):.0f} GB"),
                    ("Velocidad", f"{slot.get('speed_mhz', 0)} MHz"),
                    ("Tipo", slot.get("memory_type", "N/D")),
                    ("Factor forma", slot.get("form_factor", "N/D")),
                    ("Fabricante", slot.get("manufacturer", "N/D")),
                    ("Parte", slot.get("part_number", "N/D")),
                ]
                for lbl, val in slot_fields:
                    InfoRow(inner, lbl, val, label_width=14,
                             bg=theme.BG_MANTLE).pack(fill=tk.X, pady=1)
        else:
            # Determine best error message to show
            if error_slots:
                err_msg = error_slots[-1].get("error", "")
            else:
                err_msg = ""

            if err_msg and ("soldada" in err_msg or "LPDDR" in err_msg
                            or "restricciones" in err_msg or "PowerShell" in err_msg):
                display_msg = err_msg
                fg_color = theme.TEXT_SECONDARY
            else:
                display_msg = (
                    "No se pudo obtener información de módulos.\n"
                    "El equipo puede tener RAM soldada (LPDDR) o "
                    "restricciones de seguridad WMI."
                )
                fg_color = theme.WARNING

            tk.Label(self._slot_inner,
                     text=display_msg,
                     bg=theme.BG_SURFACE0, fg=fg_color,
                     font=theme.FONT_BODY, wraplength=320, justify="left").pack(anchor="w")

        total = summary.get("total_gb", 0)
        type_str = real_slots[0].get("memory_type", "N/D") if real_slots else "N/D"
        speed_str = f"{real_slots[0].get('speed_mhz', 0)} MHz" if real_slots else "N/D"
        self._set_detail(f"{total:.1f} GB {type_str} {speed_str}")

    def _show_error(self, error):
        self._sum_spinner.stop(f"Error: {error}")
        self._slot_spinner.stop(f"Error: {error}")

    def _start_usage_monitor(self):
        threading.Thread(target=self._monitor_loop, daemon=True).start()

    def _monitor_loop(self):
        while self._monitoring:
            try:
                from hardware.memory import get_memory_info
                mem = get_memory_info()
                pct = mem.get("percent", 0)
                used_gb = mem.get("used_gb", 0)
                total_gb = mem.get("total_gb", 0)

                def upd(p=pct, u=used_gb, t=total_gb):
                    if not self._monitoring:
                        return
                    self._update_ram_bar(p)
                    self._ram_pct_lbl.configure(
                        text=f"{u:.2f} GB / {t:.2f} GB ({p:.1f}%)")

                self.after(0, upd)
            except Exception:
                pass
            time.sleep(2)

    def _update_ram_bar(self, pct):
        w = self._ram_bar.winfo_width() or 300
        self._ram_bar.delete("all")
        self._ram_bar.create_rectangle(0, 0, w, 24,
                                        fill=theme.BG_SURFACE1, outline="")
        fw = int(w * pct / 100)
        if fw > 0:
            color = (theme.SUCCESS if pct < 60
                      else theme.WARNING if pct < 85
                      else theme.ERROR)
            self._ram_bar.create_rectangle(0, 0, fw, 24, fill=color, outline="")
        self._ram_bar.create_text(w//2, 12, text=f"{pct:.1f}%",
                                   fill=theme.BG_BASE, font=theme.FONT_SMALL)

    def _run_mem_test(self):
        import threading
        self._test_btn.configure(state=tk.DISABLED)
        self._stop_btn.configure(state=tk.NORMAL)
        self._test_lbl.configure(text="")
        # Clear previous results
        for w in self._results_frame.winfo_children():
            w.destroy()
        self._draw_progress(0, "")
        self._phase_lbl.configure(text="⏳ Iniciando prueba...")
        self._test_running = True
        self._stop_event = threading.Event()
        threading.Thread(target=self._do_mem_test, daemon=True).start()

    def _stop_mem_test(self):
        if self._stop_event:
            self._stop_event.set()
        self._stop_btn.configure(state=tk.DISABLED)
        self._phase_lbl.configure(text="⏹ Deteniendo...", fg=theme.WARNING)

    def _do_mem_test(self):
        from hardware.memory import run_memory_test
        size_mb = self._test_size_var.get()

        def on_progress(phase_name, phase_idx, total_phases, phase_pct, errors_so_far):
            # overall fraction: finished phases + current phase progress
            overall = (phase_idx + phase_pct) / total_phases
            error_txt = f"  —  Errores: {errors_so_far}" if errors_so_far else ""
            label = f"Patrón {phase_idx + 1}/{total_phases}: {phase_name}{error_txt}"
            self.after(0, lambda l=label, p=overall: self._update_progress(l, p))

        result = run_memory_test(
            size_mb=size_mb,
            progress_cb=on_progress,
            stop_event=self._stop_event,
        )
        self.after(0, lambda r=result: self._show_mem_result(r))

    def _update_progress(self, label, fraction):
        self._phase_lbl.configure(text=label, fg=theme.ACCENT_BLUE)
        self._draw_progress(fraction, label)

    def _draw_progress(self, fraction, label):
        canvas = self._prog_canvas
        w = canvas.winfo_width() or 500
        h = 18
        canvas.delete("all")
        canvas.create_rectangle(0, 0, w, h, fill=theme.BG_SURFACE1, outline="")
        fw = int(w * fraction)
        if fw > 0:
            color = theme.SUCCESS if fraction >= 1.0 else theme.ACCENT_BLUE
            canvas.create_rectangle(0, 0, fw, h, fill=color, outline="")
        pct_txt = f"{int(fraction * 100)}%"
        canvas.create_text(w // 2, h // 2, text=pct_txt,
                            fill=theme.BG_BASE, font=theme.FONT_SMALL)

    def _show_mem_result(self, result):
        self._test_running = False
        self._test_btn.configure(state=tk.NORMAL)
        self._stop_btn.configure(state=tk.DISABLED)

        if result.get("cancelled"):
            self._phase_lbl.configure(text="⏹ Prueba cancelada por el usuario",
                                       fg=theme.WARNING)
            self._draw_progress(0, "")
            return

        if result.get("error"):
            self._phase_lbl.configure(text=f"✗ Error: {result['error']}", fg=theme.ERROR)
            self.set_status(STATUS_FAILED, f"Error en prueba RAM: {result['error']}")
            return

        phases      = result.get("phases", [])
        total_errs  = result.get("total_errors", 0)
        elapsed_ms  = result.get("time_ms", 0)
        size_mb     = result.get("allocated_mb", 0)
        passed      = result.get("passed", False)

        # Draw final full bar
        self._draw_progress(1.0, "")

        # Header label
        if passed:
            self._phase_lbl.configure(
                text=f"✓ Sin errores — {size_mb} MB probados en "
                     f"{elapsed_ms/1000:.1f} s — 6/6 patrones OK",
                fg=theme.SUCCESS)
        else:
            self._phase_lbl.configure(
                text=f"✗ Se encontraron {total_errs} error(es) en la memoria",
                fg=theme.ERROR)

        # Phase results table
        for w in self._results_frame.winfo_children():
            w.destroy()

        # Table header
        hdr = tk.Frame(self._results_frame, bg=theme.BG_SURFACE1)
        hdr.pack(fill=tk.X, pady=(6, 0))
        for txt, w_ in [("Patrón", 200), ("Errores", 80), ("Tiempo", 90), ("Estado", 80)]:
            tk.Label(hdr, text=txt, bg=theme.BG_SURFACE1, fg=theme.TEXT_MUTED,
                     font=theme.FONT_SMALL, width=w_//7, anchor="w",
                     padx=8, pady=4).pack(side=tk.LEFT)

        # Table rows
        for i, ph in enumerate(phases):
            row_bg = theme.BG_MANTLE if i % 2 == 0 else theme.BG_SURFACE0
            row = tk.Frame(self._results_frame, bg=row_bg)
            row.pack(fill=tk.X)
            errs  = ph["errors"]
            ok    = ph["passed"]
            color = theme.SUCCESS if ok else theme.ERROR
            icon  = "✓" if ok else "✗"
            for txt, w_ in [
                (ph["name"],          200),
                (str(errs),            80),
                (f"{ph['time_ms']} ms", 90),
                (f"{icon} {'OK' if ok else 'FALLO'}", 80),
            ]:
                tk.Label(row, text=txt, bg=row_bg,
                         fg=color if txt.startswith(icon) else theme.TEXT_PRIMARY,
                         font=theme.FONT_SMALL, width=w_//7, anchor="w",
                         padx=8, pady=3).pack(side=tk.LEFT)

        # Summary label
        if passed:
            self.set_status(STATUS_PASSED,
                             f"RAM OK — {size_mb} MB, 6 patrones, 0 errores, {elapsed_ms/1000:.1f}s")
            self._test_lbl.configure(
                text="La memoria no presenta errores en ninguno de los 6 patrones de prueba.",
                fg=theme.SUCCESS)
        else:
            self.set_status(STATUS_FAILED,
                             f"RAM: {total_errs} error(es) detectados en {size_mb} MB")
            self._test_lbl.configure(
                text=f"⚠ Se detectaron {total_errs} error(es). "
                     "Recomendado: reemplazar módulo o ejecutar MemTest86 para confirmación.",
                fg=theme.ERROR)

    def _mem_error(self, error):
        self._test_btn.configure(state=tk.NORMAL)
        self._stop_btn.configure(state=tk.DISABLED)
        self._test_lbl.configure(text=f"Error: {error}", fg=theme.ERROR)
