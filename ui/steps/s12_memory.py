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

        tk.Label(test_card, text="Prueba de Asignación de Memoria",
                 bg=theme.BG_SURFACE0, fg=theme.ACCENT_BLUE,
                 font=theme.FONT_H3).pack(anchor="w", padx=16, pady=(12, 6))
        tk.Frame(test_card, height=1, bg=theme.BG_SURFACE2).pack(fill=tk.X, padx=16)

        test_inner = tk.Frame(test_card, bg=theme.BG_SURFACE0)
        test_inner.pack(fill=tk.X, padx=16, pady=10)

        tk.Label(test_inner,
                 text="Asigna 256 MB de memoria, escribe un patrón y verifica que sea correcto.\n"
                      "Esta es una prueba básica — no reemplaza pruebas completas (MemTest86).",
                 bg=theme.BG_SURFACE0, fg=theme.TEXT_SECONDARY,
                 font=theme.FONT_BODY, justify="left").pack(anchor="w", pady=(0, 10))

        btn_row = tk.Frame(test_inner, bg=theme.BG_SURFACE0)
        btn_row.pack(anchor="w")

        self._test_btn = tk.Button(btn_row, text="▶  Iniciar prueba de memoria",
                                    command=self._run_mem_test, **theme.BTN_PRIMARY)
        self._test_btn.pack(side=tk.LEFT, padx=(0, 12))

        self._test_lbl = tk.Label(test_inner, text="",
                                   bg=theme.BG_SURFACE0, fg=theme.TEXT_SECONDARY,
                                   font=theme.FONT_BODY)
        self._test_lbl.pack(anchor="w", pady=(8, 0))

        # Load data
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

        # Summary fields
        fields = [
            ("Total", f"{summary.get('total_gb', 0):.2f} GB"),
            ("Disponible", f"{summary.get('available_gb', 0):.2f} GB"),
            ("En uso", f"{summary.get('used_gb', 0):.2f} GB"),
            ("Ranuras totales", str(array.get("memory_devices", "N/D"))),
            ("Ranuras usadas", str(len(slots))),
            ("Cap. máxima", f"{array.get('max_capacity_gb', 0):.0f} GB"),
        ]
        for label, val in fields:
            InfoRow(self._sum_inner, label, val,
                    label_width=16, bg=theme.BG_SURFACE0).pack(fill=tk.X, pady=2)

        # Slot details
        if slots:
            for slot in slots:
                if "error" in slot:
                    continue
                slot_card = tk.Frame(self._slot_inner, bg=theme.BG_MANTLE,
                                      highlightthickness=1,
                                      highlightbackground=theme.BG_SURFACE2)
                slot_card.pack(fill=tk.X, pady=4)

                hdr_bg = theme.BG_SURFACE1
                hdr = tk.Frame(slot_card, bg=hdr_bg)
                hdr.pack(fill=tk.X)
                tk.Label(hdr,
                          text=f"Ranura: {slot.get('device_locator', 'N/D')}  "
                               f"({slot.get('bank_label', '')})",
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
            tk.Label(self._slot_inner,
                     text="No se pudo obtener información detallada\nde los módulos via WMI.",
                     bg=theme.BG_SURFACE0, fg=theme.WARNING,
                     font=theme.FONT_BODY).pack(anchor="w")

        total = summary.get("total_gb", 0)
        type_str = slots[0].get("memory_type", "N/D") if slots else "N/D"
        speed_str = f"{slots[0].get('speed_mhz', 0)} MHz" if slots else "N/D"
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
        self._test_btn.configure(state=tk.DISABLED)
        self._test_lbl.configure(text="⏳ Ejecutando prueba... (puede tardar unos segundos)",
                                   fg=theme.ACCENT_BLUE)
        self.run_in_thread(self._do_mem_test, on_done=self._show_mem_result,
                            on_error=lambda e: self._mem_error(e))

    def _do_mem_test(self):
        from hardware.memory import run_memory_test
        return run_memory_test()

    def _show_mem_result(self, result):
        self._test_btn.configure(state=tk.NORMAL)
        if result.get("passed"):
            mb = result.get("allocated_mb", 0)
            ms = result.get("time_ms", 0)
            self._test_lbl.configure(
                text=f"✓ Prueba exitosa — {mb} MB asignados y verificados en {ms} ms",
                fg=theme.SUCCESS)
            self.set_status(STATUS_PASSED, f"RAM OK: prueba {mb}MB en {ms}ms")
        else:
            err = result.get("error", "Error desconocido")
            self._test_lbl.configure(text=f"✗ Prueba fallida: {err}", fg=theme.ERROR)
            self.set_status(STATUS_FAILED, f"Fallo en prueba de RAM: {err}")

    def _mem_error(self, error):
        self._test_btn.configure(state=tk.NORMAL)
        self._test_lbl.configure(text=f"Error: {error}", fg=theme.ERROR)
