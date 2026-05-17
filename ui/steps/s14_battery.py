"""
TecoQC - Paso 14: Información de batería
"""

import tkinter as tk
from ui.steps.base_step import BaseStep
from ui.components import Card, InfoRow, Spinner
from ui import theme
from config import STATUS_PASSED, STATUS_FAILED


class Step(BaseStep):
    TITLE = "Batería"
    DESCRIPTION = ("Información de salud de la batería: capacidad de diseño, capacidad actual, "
                   "desgaste, ciclos y estado de carga.")
    STEP_NUM = 14

    def build_ui(self, parent):
        self._spinner = Spinner(parent, text="Leyendo información de batería...",
                                 bg=theme.BG_BASE)
        self._spinner.pack(pady=20)
        self._spinner.start()

        self._main = tk.Frame(parent, bg=theme.BG_BASE)
        self._main.pack(fill=tk.BOTH, expand=True)

    def on_enter(self):
        self.run_in_thread(self._collect, on_done=self._show,
                            on_error=self._show_error)

    def _collect(self):
        from hardware.battery import get_all_battery_info
        return get_all_battery_info()

    def _show(self, data):
        self._spinner.stop()
        self._spinner.pack_forget()

        for w in self._main.winfo_children():
            w.destroy()

        psutil_data = data.get("psutil", {})
        wmi_data = data.get("wmi", {})

        # Check if battery present
        if not psutil_data.get("present", True) and not wmi_data.get("present", True):
            no_bat_frame = tk.Frame(self._main, bg=theme.BG_SURFACE0,
                                     highlightthickness=1,
                                     highlightbackground=theme.WARNING)
            no_bat_frame.pack(fill=tk.X, pady=20)
            tk.Label(
                no_bat_frame,
                text="⚠  No se detectó batería en este equipo.\n\n"
                     "Es posible que sea un equipo de escritorio o que la batería\n"
                     "no esté conectada o no sea reconocida.",
                bg=theme.BG_SURFACE0, fg=theme.WARNING,
                font=theme.FONT_BODY, pady=24, justify="center",
            ).pack()
            self._set_detail("Sin batería detectada")
            return

        # ── Main status card ───────────────────────────────────────────
        cols = tk.Frame(self._main, bg=theme.BG_BASE)
        cols.pack(fill=tk.BOTH, expand=True)
        cols.columnconfigure(0, weight=1)
        cols.columnconfigure(1, weight=1)

        # Status card
        status_card = Card(cols)
        status_card.grid(row=0, column=0, padx=(0, 8), pady=0, sticky="nsew")

        tk.Label(status_card, text="Estado Actual",
                 bg=theme.BG_SURFACE0, fg=theme.ACCENT_BLUE,
                 font=theme.FONT_H3).pack(anchor="w", padx=16, pady=(12, 6))
        tk.Frame(status_card, height=1, bg=theme.BG_SURFACE2).pack(fill=tk.X, padx=16)

        stat_inner = tk.Frame(status_card, bg=theme.BG_SURFACE0)
        stat_inner.pack(fill=tk.X, padx=16, pady=10)

        # Charge level bar
        pct = psutil_data.get("percent", 0)
        plugged = psutil_data.get("power_plugged", False)
        time_left = psutil_data.get("time_remaining", "N/D")

        charge_color = (theme.SUCCESS if pct >= 50
                         else theme.WARNING if pct >= 20
                         else theme.ERROR)

        tk.Label(stat_inner, text="Nivel de carga:",
                 bg=theme.BG_SURFACE0, fg=theme.TEXT_SECONDARY,
                 font=theme.FONT_BODY).pack(anchor="w", pady=(0, 4))

        bar = tk.Canvas(stat_inner, height=28, bg=theme.BG_SURFACE1,
                         highlightthickness=1, highlightbackground=theme.BG_SURFACE2)
        bar.pack(fill=tk.X)
        bar.update_idletasks()
        w = bar.winfo_width() or 300
        fw = int(w * pct / 100)
        bar.create_rectangle(0, 0, fw, 28, fill=charge_color, outline="")
        bar.create_text(w//2, 14, text=f"{pct:.0f}%",
                         fill=theme.BG_BASE if fw > 30 else theme.TEXT_PRIMARY,
                         font=theme.FONT_BODY_BOLD)

        stat_fields = [
            ("Estado", "Cargando (CA)" if plugged else "Descargando"),
            ("Tiempo restante", time_left if not plugged else "Conectado a CA"),
            ("Estado WMI", wmi_data.get("status", "N/D")),
            ("Química", wmi_data.get("chemistry", "N/D")),
        ]
        for lbl, val in stat_fields:
            InfoRow(stat_inner, lbl, str(val), label_width=16,
                    bg=theme.BG_SURFACE0).pack(fill=tk.X, pady=3)

        # Health card
        health_card = Card(cols)
        health_card.grid(row=0, column=1, padx=(8, 0), pady=0, sticky="nsew")

        tk.Label(health_card, text="Salud de la Batería",
                 bg=theme.BG_SURFACE0, fg=theme.ACCENT_BLUE,
                 font=theme.FONT_H3).pack(anchor="w", padx=16, pady=(12, 6))
        tk.Frame(health_card, height=1, bg=theme.BG_SURFACE2).pack(fill=tk.X, padx=16)

        health_inner = tk.Frame(health_card, bg=theme.BG_SURFACE0)
        health_inner.pack(fill=tk.X, padx=16, pady=10)

        design = wmi_data.get("design_capacity", 0) or 0
        full = wmi_data.get("full_charge_capacity", 0) or 0
        wear = wmi_data.get("wear_level_pct", None)
        health = wmi_data.get("health_pct", None)
        cycle_count = wmi_data.get("cycle_count", None)

        if health is not None:
            health_color = (theme.SUCCESS if health >= 80
                             else theme.WARNING if health >= 60
                             else theme.ERROR)
            tk.Label(health_inner, text="Salud de batería:",
                     bg=theme.BG_SURFACE0, fg=theme.TEXT_SECONDARY,
                     font=theme.FONT_BODY).pack(anchor="w", pady=(0, 4))

            health_bar = tk.Canvas(health_inner, height=28, bg=theme.BG_SURFACE1,
                                    highlightthickness=1,
                                    highlightbackground=theme.BG_SURFACE2)
            health_bar.pack(fill=tk.X)
            health_bar.update_idletasks()
            hw = health_bar.winfo_width() or 300
            hfw = int(hw * health / 100)
            health_bar.create_rectangle(0, 0, hfw, 28, fill=health_color, outline="")
            health_bar.create_text(hw//2, 14, text=f"{health:.1f}%",
                                    fill=theme.BG_BASE,
                                    font=theme.FONT_BODY_BOLD)

        health_fields = [
            ("Capacidad diseño", f"{design} mWh" if design else "N/D"),
            ("Capacidad total", f"{full} mWh" if full else "N/D"),
            ("Desgaste", f"{wear:.1f}%" if wear is not None else "N/D"),
            ("Salud", f"{health:.1f}%" if health is not None else "N/D"),
            ("Ciclos de carga", str(cycle_count) if cycle_count else "N/D"),
            ("Fabricante", wmi_data.get("manufacturer", "N/D")),
            ("Nombre", wmi_data.get("name", "N/D")),
        ]
        for lbl, val in health_fields:
            InfoRow(health_inner, lbl, str(val), label_width=16,
                    bg=theme.BG_SURFACE0).pack(fill=tk.X, pady=3)

        # Charger detection test
        charger_card = Card(self._main)
        charger_card.pack(fill=tk.X, pady=(12, 0))

        ch_inner = tk.Frame(charger_card, bg=theme.BG_SURFACE0)
        ch_inner.pack(fill=tk.X, padx=16, pady=12)

        tk.Label(ch_inner, text="Prueba de Cargador",
                 bg=theme.BG_SURFACE0, fg=theme.ACCENT_BLUE,
                 font=theme.FONT_H3).pack(anchor="w", pady=(0, 6))

        tk.Label(ch_inner,
                 text="Conecte o desconecte el cargador para verificar que el sistema\n"
                      "lo detecta correctamente (debe cambiar el estado).",
                 bg=theme.BG_SURFACE0, fg=theme.TEXT_SECONDARY,
                 font=theme.FONT_BODY, justify="left").pack(anchor="w", pady=(0, 8))

        ch_btn_row = tk.Frame(ch_inner, bg=theme.BG_SURFACE0)
        ch_btn_row.pack(anchor="w")

        self._charger_btn = tk.Button(
            ch_btn_row, text="🔌  Detectar cambio de cargador (5s)",
            command=self._test_charger, **theme.BTN_SECONDARY)
        self._charger_btn.pack(side=tk.LEFT, padx=(0, 12))

        self._charger_lbl = tk.Label(ch_inner, text="",
                                      bg=theme.BG_SURFACE0,
                                      fg=theme.TEXT_MUTED, font=theme.FONT_BODY)
        self._charger_lbl.pack(anchor="w", pady=(6, 0))

        # Report button
        tk.Frame(self._main, height=12, bg=theme.BG_BASE).pack()

        report_card = Card(self._main)
        report_card.pack(fill=tk.X)
        rep_inner = tk.Frame(report_card, bg=theme.BG_SURFACE0)
        rep_inner.pack(fill=tk.X, padx=16, pady=12)

        tk.Label(rep_inner, text="Reporte detallado de batería (powercfg):",
                 bg=theme.BG_SURFACE0, fg=theme.TEXT_SECONDARY,
                 font=theme.FONT_BODY).pack(anchor="w", pady=(0, 8))

        btn_row = tk.Frame(rep_inner, bg=theme.BG_SURFACE0)
        btn_row.pack(anchor="w")

        self._report_btn = tk.Button(
            btn_row, text="📊  Generar reporte powercfg",
            command=self._gen_powercfg, **theme.BTN_SECONDARY,
        )
        self._report_btn.pack(side=tk.LEFT, padx=(0, 12))

        self._report_lbl = tk.Label(rep_inner, text="",
                                     bg=theme.BG_SURFACE0,
                                     fg=theme.TEXT_SECONDARY, font=theme.FONT_SMALL)
        self._report_lbl.pack(anchor="w", pady=(8, 0))

        # Auto-evaluate health
        if health is not None:
            if health >= 80:
                self.set_status(STATUS_PASSED,
                                 f"Salud: {health:.1f}% | Desgaste: {wear:.1f}%")
            elif health >= 60:
                self.set_status("failed",
                                 f"Salud moderada: {health:.1f}% | Desgaste: {wear:.1f}%")
            else:
                self.set_status(STATUS_FAILED,
                                 f"Salud crítica: {health:.1f}% — Batería requiere reemplazo")
        else:
            self._set_detail(f"Carga: {pct:.0f}% | {'Conectado' if plugged else 'Batería'}")

    def _gen_powercfg(self):
        self._report_btn.configure(state=tk.DISABLED)
        self._report_lbl.configure(text="⏳ Generando reporte...", fg=theme.ACCENT_BLUE)
        self.run_in_thread(self._do_powercfg, on_done=self._show_powercfg,
                            on_error=lambda e: self._powercfg_error(e))

    def _do_powercfg(self):
        from hardware.battery import run_battery_report
        return run_battery_report()

    def _show_powercfg(self, result):
        self._report_btn.configure(state=tk.NORMAL)
        if result.get("available"):
            path = result["path"]
            self._report_lbl.configure(
                text=f"✓ Reporte guardado en: {path}", fg=theme.SUCCESS)
            import os
            try:
                os.startfile(path)
            except Exception:
                pass
        else:
            err = result.get("error", "Error desconocido")
            self._report_lbl.configure(
                text=f"⚠ {err}", fg=theme.WARNING)

    def _powercfg_error(self, error):
        self._report_btn.configure(state=tk.NORMAL)
        self._report_lbl.configure(text=f"Error: {error}", fg=theme.ERROR)

    def _test_charger(self):
        self._charger_btn.configure(state=tk.DISABLED)
        self._charger_lbl.configure(
            text="⏳ Monitoreando cambio de estado durante 5 segundos...\n"
                 "Conecte o desconecte el cargador ahora.",
            fg=theme.ACCENT_BLUE)
        self.run_in_thread(self._do_test_charger, on_done=self._show_charger_result,
                            on_error=lambda e: self._charger_error(e))

    def _do_test_charger(self):
        import psutil, time
        initial = psutil.sensors_battery()
        initial_plugged = initial.power_plugged if initial else None
        initial_pct = initial.percent if initial else 0

        for _ in range(10):
            time.sleep(0.5)
            current = psutil.sensors_battery()
            if current is None:
                continue
            if initial_plugged is not None and current.power_plugged != initial_plugged:
                return {
                    "changed": True,
                    "from": "Conectado" if initial_plugged else "Desconectado",
                    "to": "Conectado" if current.power_plugged else "Desconectado",
                    "charge_pct": current.percent,
                }

        return {
            "changed": False,
            "plugged": initial_plugged,
            "charge_pct": initial_pct,
        }

    def _show_charger_result(self, result):
        self._charger_btn.configure(state=tk.NORMAL)
        if result.get("changed"):
            from_state = result.get("from", "?")
            to_state = result.get("to", "?")
            self._charger_lbl.configure(
                text=f"✓ Cargador detectado: {from_state} → {to_state}  "
                     f"(carga: {result.get('charge_pct', 0):.0f}%)",
                fg=theme.SUCCESS)
        else:
            plugged = result.get("plugged")
            state = "Conectado" if plugged else "Desconectado" if plugged is False else "N/D"
            self._charger_lbl.configure(
                text=f"⚠ No se detectó cambio en 5s — estado actual: {state}\n"
                     f"Pruebe conectar/desconectar más rápido.",
                fg=theme.WARNING)

    def _charger_error(self, error):
        self._charger_btn.configure(state=tk.NORMAL)
        self._charger_lbl.configure(text=f"Error: {error}", fg=theme.ERROR)

    def _show_error(self, error):
        self._spinner.stop()
        self._spinner.pack_forget()
        tk.Label(self._main, text=f"Error al leer batería: {error}",
                 bg=theme.BG_BASE, fg=theme.WARNING,
                 font=theme.FONT_BODY).pack(pady=20)
        self._set_detail(f"Error: {error}")
