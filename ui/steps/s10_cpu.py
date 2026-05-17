"""
TecoQC - Paso 10: Información de CPU, uso en tiempo real y prueba de estrés
"""

import tkinter as tk
import threading
import time

from ui.steps.base_step import BaseStep
from ui.components import Card, InfoRow, Spinner
from ui import theme
from config import STATUS_PASSED, STATUS_FAILED, TEMP_WARNING, TEMP_CRITICAL


class Step(BaseStep):
    TITLE = "Procesador (CPU)"
    DESCRIPTION = ("Información del procesador, monitoreo de uso en tiempo real, "
                   "temperatura y prueba de estrés opcional.")
    STEP_NUM = 10

    def build_ui(self, parent):
        self._monitoring = False
        self._stress_running = False
        self._stress_flag = None
        self._usage_history = [0.0] * 60   # last 60 readings
        self._graph_job = None
        self._baseline_freq = 0.0

        # Two columns
        cols = tk.Frame(parent, bg=theme.BG_BASE)
        cols.pack(fill=tk.BOTH, expand=True)
        cols.columnconfigure(0, weight=1)
        cols.columnconfigure(1, weight=1)

        # ── CPU Info Card ──────────────────────────────────────────────
        info_card = Card(cols)
        info_card.grid(row=0, column=0, padx=(0, 8), pady=0, sticky="nsew")

        tk.Label(info_card, text="Información del Procesador",
                 bg=theme.BG_SURFACE0, fg=theme.ACCENT_BLUE,
                 font=theme.FONT_H3).pack(anchor="w", padx=16, pady=(12, 6))
        tk.Frame(info_card, height=1, bg=theme.BG_SURFACE2).pack(fill=tk.X, padx=16)

        self._cpu_info_frame = tk.Frame(info_card, bg=theme.BG_SURFACE0)
        self._cpu_info_frame.pack(fill=tk.X, padx=16, pady=10)

        self._cpu_spinner = Spinner(self._cpu_info_frame, text="Obteniendo info CPU...",
                                     bg=theme.BG_SURFACE0)
        self._cpu_spinner.pack(pady=12)
        self._cpu_spinner.start()

        # ── Usage + Temperature Card ───────────────────────────────────
        monitor_card = Card(cols)
        monitor_card.grid(row=0, column=1, padx=(8, 0), pady=0, sticky="nsew")

        tk.Label(monitor_card, text="Monitor en Tiempo Real",
                 bg=theme.BG_SURFACE0, fg=theme.ACCENT_BLUE,
                 font=theme.FONT_H3).pack(anchor="w", padx=16, pady=(12, 6))
        tk.Frame(monitor_card, height=1, bg=theme.BG_SURFACE2).pack(fill=tk.X, padx=16)

        mon_inner = tk.Frame(monitor_card, bg=theme.BG_SURFACE0)
        mon_inner.pack(fill=tk.BOTH, expand=True, padx=16, pady=10)

        # Usage bar
        usage_row = tk.Frame(mon_inner, bg=theme.BG_SURFACE0)
        usage_row.pack(fill=tk.X, pady=4)
        tk.Label(usage_row, text="Uso CPU:", bg=theme.BG_SURFACE0,
                 fg=theme.TEXT_SECONDARY, font=theme.FONT_BODY,
                 width=12, anchor="w").pack(side=tk.LEFT)
        self._usage_bar_bg = tk.Canvas(usage_row, height=20, bg=theme.BG_SURFACE1,
                                        highlightthickness=0)
        self._usage_bar_bg.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=8)
        self._usage_pct_lbl = tk.Label(usage_row, text="0%",
                                        bg=theme.BG_SURFACE0, fg=theme.TEXT_PRIMARY,
                                        font=theme.FONT_BODY_BOLD, width=5)
        self._usage_pct_lbl.pack(side=tk.LEFT)

        # Temperature
        temp_row = tk.Frame(mon_inner, bg=theme.BG_SURFACE0)
        temp_row.pack(fill=tk.X, pady=4)
        tk.Label(temp_row, text="Temperatura:", bg=theme.BG_SURFACE0,
                 fg=theme.TEXT_SECONDARY, font=theme.FONT_BODY,
                 width=12, anchor="w").pack(side=tk.LEFT)
        self._temp_lbl = tk.Label(temp_row, text="N/D",
                                   bg=theme.BG_SURFACE0, fg=theme.TEXT_PRIMARY,
                                   font=theme.FONT_BODY_BOLD)
        self._temp_lbl.pack(side=tk.LEFT, padx=8)

        # Graph
        tk.Label(mon_inner, text="Historial de uso (último minuto):",
                 bg=theme.BG_SURFACE0, fg=theme.TEXT_SECONDARY,
                 font=theme.FONT_SMALL).pack(anchor="w", pady=(12, 4))

        self._graph_canvas = tk.Canvas(
            mon_inner, height=100, bg=theme.BG_CRUST,
            highlightthickness=1, highlightbackground=theme.BG_SURFACE2,
        )
        self._graph_canvas.pack(fill=tk.X)
        self._draw_graph()

        # Per-core usage
        self._core_frame = tk.Frame(mon_inner, bg=theme.BG_SURFACE0)
        self._core_frame.pack(fill=tk.X, pady=(10, 0))

        # ── Stress test ────────────────────────────────────────────────
        stress_card = Card(parent)
        stress_card.pack(fill=tk.X, pady=(8, 0))

        tk.Label(stress_card, text="Prueba de Estrés (Opcional)",
                 bg=theme.BG_SURFACE0, fg=theme.ACCENT_BLUE,
                 font=theme.FONT_H3).pack(anchor="w", padx=16, pady=(12, 6))
        tk.Frame(stress_card, height=1, bg=theme.BG_SURFACE2).pack(fill=tk.X, padx=16)

        stress_inner = tk.Frame(stress_card, bg=theme.BG_SURFACE0)
        stress_inner.pack(fill=tk.X, padx=16, pady=10)

        tk.Label(stress_inner,
                 text="Carga todos los núcleos al 100% durante el tiempo seleccionado "
                      "para verificar estabilidad y refrigeración bajo carga.",
                 bg=theme.BG_SURFACE0, fg=theme.TEXT_SECONDARY,
                 font=theme.FONT_BODY, justify="left").pack(anchor="w", pady=(0, 8))

        # Duration selector
        dur_row = tk.Frame(stress_inner, bg=theme.BG_SURFACE0)
        dur_row.pack(anchor="w", pady=(0, 10))

        tk.Label(dur_row, text="Duración:", bg=theme.BG_SURFACE0,
                 fg=theme.TEXT_SECONDARY, font=theme.FONT_BODY).pack(side=tk.LEFT, padx=(0, 10))

        self._stress_durations = [
            ("10 s",   10),
            ("30 s",   30),
            ("1 min",  60),
            ("2 min",  120),
            ("5 min",  300),
            ("10 min", 600),
        ]
        self._stress_dur_var = tk.IntVar(value=10)

        for label, seconds in self._stress_durations:
            rb = tk.Radiobutton(
                dur_row, text=label,
                variable=self._stress_dur_var, value=seconds,
                bg=theme.BG_SURFACE0, fg=theme.TEXT_PRIMARY,
                selectcolor=theme.BG_SURFACE1,
                activebackground=theme.BG_SURFACE0,
                font=theme.FONT_BODY,
                indicatoron=0,
                relief="flat", padx=10, pady=4,
                cursor="hand2",
            )
            rb.pack(side=tk.LEFT, padx=3)

        stress_btn_row = tk.Frame(stress_inner, bg=theme.BG_SURFACE0)
        stress_btn_row.pack(anchor="w")

        self._stress_btn = tk.Button(
            stress_btn_row, text="🔥  Iniciar prueba de estrés",
            command=self._toggle_stress, **theme.BTN_WARNING,
        )
        self._stress_btn.pack(side=tk.LEFT, padx=(0, 12))

        # Max temp display
        self._max_temp_lbl = tk.Label(
            stress_btn_row, text="",
            bg=theme.BG_SURFACE0, fg=theme.TEXT_MUTED, font=theme.FONT_BODY)
        self._max_temp_lbl.pack(side=tk.LEFT, padx=(4, 0))

        # Progress bar for stress countdown
        prog_wrap = tk.Frame(stress_inner, bg=theme.BG_SURFACE1,
                              highlightthickness=1, highlightbackground=theme.BG_SURFACE2)
        prog_wrap.pack(fill=tk.X, pady=(8, 4))
        self._stress_prog = tk.Canvas(prog_wrap, height=16, bg=theme.BG_SURFACE1,
                                       highlightthickness=0)
        self._stress_prog.pack(fill=tk.X)

        self._stress_lbl = tk.Label(stress_inner, text="",
                                     bg=theme.BG_SURFACE0,
                                     fg=theme.TEXT_SECONDARY, font=theme.FONT_BODY)
        self._stress_lbl.pack(anchor="w")
        self._throttle_lbl = tk.Label(stress_inner, text="",
                                       bg=theme.BG_SURFACE0,
                                       fg=theme.TEXT_MUTED, font=theme.FONT_SMALL)
        self._throttle_lbl.pack(anchor="w")

        # Start data collection
        self.run_in_thread(self._get_cpu_info_data, on_done=self._show_cpu_info)

    def on_enter(self):
        self._monitoring = True
        self._start_monitoring()

    def on_leave(self):
        super().on_leave()
        self._monitoring = False
        if self._stress_flag:
            self._stress_flag.set()

    def _get_cpu_info_data(self):
        from hardware.cpu import get_cpu_info
        return get_cpu_info()

    def _show_cpu_info(self, info):
        self._cpu_spinner.stop()
        self._cpu_spinner.pack_forget()

        fields = [
            ("Nombre", info.get("name", "N/D")),
            ("Fabricante", info.get("manufacturer", "N/D")),
            ("Núcleos físicos", str(info.get("cores_physical", "N/D"))),
            ("Núcleos lógicos", str(info.get("cores_logical", "N/D"))),
            ("Vel. máxima", f"{info.get('freq_max_mhz', 0):.0f} MHz"),
            ("Vel. actual", f"{info.get('freq_current_mhz', 0):.0f} MHz"),
            ("Socket", info.get("socket", "N/D")),
        ]
        for label, val in fields:
            InfoRow(self._cpu_info_frame, label, val,
                    label_width=18, bg=theme.BG_SURFACE0).pack(fill=tk.X, pady=2)

        cpu_name = info.get("name", "CPU")
        self._set_detail(f"{cpu_name} | {info.get('cores_physical', '?')}C/"
                          f"{info.get('cores_logical', '?')}T")

        # Build per-core widgets
        try:
            import psutil
            core_count = psutil.cpu_count(logical=True) or 4
        except Exception:
            core_count = 4

        for i in range(min(core_count, 8)):
            row = tk.Frame(self._core_frame, bg=theme.BG_SURFACE0)
            row.pack(fill=tk.X, pady=1)
            tk.Label(row, text=f"Núcleo {i}:", bg=theme.BG_SURFACE0,
                     fg=theme.TEXT_MUTED, font=theme.FONT_SMALL, width=9,
                     anchor="w").pack(side=tk.LEFT)
            bar = tk.Canvas(row, height=8, bg=theme.BG_SURFACE1,
                             highlightthickness=0)
            bar.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=4)
            lbl = tk.Label(row, text="0%", bg=theme.BG_SURFACE0,
                            fg=theme.TEXT_MUTED, font=theme.FONT_SMALL, width=4)
            lbl.pack(side=tk.LEFT)
            setattr(self, f"_core_bar_{i}", bar)
            setattr(self, f"_core_lbl_{i}", lbl)

    def _start_monitoring(self):
        threading.Thread(target=self._monitor_loop, daemon=True).start()

    def _monitor_loop(self):
        while self._monitoring:
            try:
                import psutil
                usage = psutil.cpu_percent(interval=1)
                per_core = psutil.cpu_percent(interval=None, percpu=True)
                freq = psutil.cpu_freq()
                freq_val = freq.current if freq else 0

                from hardware.cpu import get_cpu_temperature
                temps = get_cpu_temperature()
                temp_str = "N/D"
                if temps:
                    first_temp = list(temps.values())[0]
                    temp_str = f"{first_temp:.1f}°C"
                    if first_temp >= TEMP_CRITICAL:
                        temp_color = theme.ERROR
                    elif first_temp >= TEMP_WARNING:
                        temp_color = theme.WARNING
                    else:
                        temp_color = theme.SUCCESS
                else:
                    temp_color = theme.TEXT_MUTED

                # Update UI in main thread
                def update(u=usage, pc=per_core[:], ts=temp_str, tc=temp_color, fv=freq_val):
                    if not self._monitoring:
                        return
                    self._update_usage_bar(u)
                    self._update_per_core(pc)
                    self._temp_lbl.configure(text=ts, fg=tc)
                    self._update_graph(u)

                self.after(0, update)
            except Exception:
                pass

            time.sleep(1)

    def _update_usage_bar(self, usage):
        self._usage_pct_lbl.configure(text=f"{usage:.1f}%")
        w = self._usage_bar_bg.winfo_width() or 200
        self._usage_bar_bg.delete("all")
        self._usage_bar_bg.create_rectangle(0, 0, w, 20,
                                              fill=theme.BG_SURFACE1, outline="")
        fw = int(w * usage / 100)
        if fw > 0:
            color = (theme.SUCCESS if usage < 60
                      else theme.WARNING if usage < 85
                      else theme.ERROR)
            self._usage_bar_bg.create_rectangle(0, 0, fw, 20, fill=color, outline="")
        # Text
        self._usage_bar_bg.create_text(w//2, 10, text=f"{usage:.1f}%",
                                         fill=theme.BG_BASE, font=theme.FONT_SMALL)

    def _update_per_core(self, per_core):
        for i, usage in enumerate(per_core[:8]):
            bar = getattr(self, f"_core_bar_{i}", None)
            lbl = getattr(self, f"_core_lbl_{i}", None)
            if bar and lbl:
                w = bar.winfo_width() or 100
                bar.delete("all")
                bar.create_rectangle(0, 0, w, 8, fill=theme.BG_SURFACE1, outline="")
                fw = int(w * usage / 100)
                if fw > 0:
                    color = (theme.SUCCESS if usage < 60
                              else theme.WARNING if usage < 85
                              else theme.ERROR)
                    bar.create_rectangle(0, 0, fw, 8, fill=color, outline="")
                lbl.configure(text=f"{usage:.0f}%")

    def _update_graph(self, usage):
        self._usage_history.pop(0)
        self._usage_history.append(usage)
        self._draw_graph()

    def _draw_graph(self):
        canvas = self._graph_canvas
        w = canvas.winfo_width() or 400
        h = 100
        canvas.delete("all")

        # Background grid
        canvas.create_rectangle(0, 0, w, h, fill=theme.BG_CRUST, outline="")
        for pct in [25, 50, 75]:
            y = h - (pct / 100 * h)
            canvas.create_line(0, y, w, y, fill=theme.BG_SURFACE1, dash=(2, 4))
            canvas.create_text(3, y-6, text=f"{pct}%", anchor="nw",
                                fill=theme.TEXT_MUTED, font=(theme.FONT_FAMILY, 7))

        # Line graph
        points = self._usage_history
        step = w / max(len(points) - 1, 1)
        coords = []
        for i, val in enumerate(points):
            x = i * step
            y = h - (val / 100 * h)
            coords.extend([x, y])

        if len(coords) >= 4:
            canvas.create_line(*coords, fill=theme.ACCENT_BLUE, width=2, smooth=True)

    def _toggle_stress(self):
        if self._stress_running:
            if self._stress_flag:
                self._stress_flag.set()
            self._stress_running = False
            self._stress_btn.configure(text="🔥  Iniciar prueba de estrés")
        else:
            self._stress_duration = self._stress_dur_var.get()
            self._stress_max_temp = 0.0
            self._stress_running  = True
            self._stress_btn.configure(text="■  Detener prueba")
            self._max_temp_lbl.configure(text="")
            self._stress_lbl.configure(text="⚡ Iniciando estrés...", fg=theme.WARNING)
            self._draw_stress_progress(0, self._stress_duration)
            try:
                import psutil
                freq = psutil.cpu_freq()
                self._baseline_freq = freq.current if freq else 0.0
            except Exception:
                self._baseline_freq = 0.0
            self._min_stress_freq = self._baseline_freq
            threading.Thread(target=self._run_stress, daemon=True).start()

    def _run_stress(self):
        from hardware.cpu import run_cpu_stress, get_cpu_temperature
        dur = self._stress_duration
        stop_flag, results, threads = run_cpu_stress(duration_seconds=dur)
        self._stress_flag = stop_flag

        start = time.time()
        while not stop_flag.is_set():
            elapsed = time.time() - start
            if elapsed >= dur:
                break
            remaining = int(dur - elapsed)
            mins, secs = divmod(remaining, 60)
            time_str = f"{mins}:{secs:02d}" if mins else f"{secs}s"

            # Track max temperature during stress
            try:
                temps = get_cpu_temperature()
                if temps:
                    cur_temp = max(temps.values())
                    if cur_temp > self._stress_max_temp:
                        self._stress_max_temp = cur_temp
            except Exception:
                pass

            try:
                import psutil
                freq = psutil.cpu_freq()
                if freq and freq.current > 0:
                    if self._min_stress_freq == 0 or freq.current < self._min_stress_freq:
                        self._min_stress_freq = freq.current
            except Exception:
                pass

            def upd(e=elapsed, d=dur, ts=time_str, mt=self._stress_max_temp):
                if not self._stress_running:
                    return
                pct = min(e / d, 1.0) if d > 0 else 1.0
                self._draw_stress_progress(pct, d)
                temp_txt = f"  |  Temp. máx: {mt:.1f}°C" if mt > 0 else ""
                color = theme.ERROR if mt >= 90 else theme.WARNING if mt >= 75 else theme.WARNING
                self._stress_lbl.configure(
                    text=f"⚡ Estrés activo — Tiempo restante: {ts}{temp_txt}",
                    fg=color)
                # Throttle detection
                if self._baseline_freq > 0 and self._min_stress_freq > 0:
                    drop_pct = (self._baseline_freq - self._min_stress_freq) / self._baseline_freq * 100
                    if drop_pct > 20:
                        self._throttle_lbl.configure(
                            text=f"⚠ Throttling detectado: frecuencia cayó {drop_pct:.0f}% "
                                 f"({self._baseline_freq:.0f} → {self._min_stress_freq:.0f} MHz)",
                            fg=theme.ERROR)
                    elif drop_pct > 10:
                        self._throttle_lbl.configure(
                            text=f"⚠ Frecuencia reducida {drop_pct:.0f}% bajo carga",
                            fg=theme.WARNING)

            self.after(0, upd)
            time.sleep(0.5)

        stop_flag.set()
        for t in threads:
            t.join(timeout=2)

        self._stress_running = False
        max_t = self._stress_max_temp

        def done(mt=max_t):
            self._stress_btn.configure(text="🔥  Iniciar prueba de estrés")
            self._draw_stress_progress(1.0, self._stress_duration)

            if mt > 0:
                if mt >= 95:
                    temp_color = theme.ERROR
                    verdict = f"⚠ Temp. máx alcanzada: {mt:.1f}°C — POSIBLE PROBLEMA DE REFRIGERACIÓN"
                elif mt >= 85:
                    temp_color = theme.WARNING
                    verdict = f"⚠ Temp. máx alcanzada: {mt:.1f}°C — Límite alto, monitorear"
                else:
                    temp_color = theme.SUCCESS
                    verdict = f"✓ Temp. máx alcanzada: {mt:.1f}°C — Normal"
                self._max_temp_lbl.configure(
                    text=f"Máx: {mt:.1f}°C", fg=temp_color)
            else:
                verdict = "✓ Prueba de estrés completada"
                temp_color = theme.SUCCESS

            dur_label = next((l for l, s in self._stress_durations
                              if s == self._stress_duration), f"{self._stress_duration}s")
            self._stress_lbl.configure(text=verdict, fg=temp_color)
            throttle_warn = ""
            if self._baseline_freq > 0 and hasattr(self, '_min_stress_freq') and self._min_stress_freq > 0:
                drop_pct = (self._baseline_freq - self._min_stress_freq) / self._baseline_freq * 100
                if drop_pct > 20:
                    throttle_warn = f" | ⚠ Throttling {drop_pct:.0f}%"
                    if temp_color == theme.SUCCESS:
                        temp_color = theme.WARNING
            self.set_status(STATUS_PASSED,
                             f"CPU verificada — Estrés {dur_label}"
                             + (f" | Temp. máx {mt:.1f}°C" if mt > 0 else "")
                             + throttle_warn)

        self.after(0, done)

    def _draw_stress_progress(self, fraction, total_secs):
        canvas = self._stress_prog
        w = canvas.winfo_width() or 400
        h = 16
        canvas.delete("all")
        canvas.create_rectangle(0, 0, w, h, fill=theme.BG_SURFACE1, outline="")
        fw = int(w * fraction)
        if fw > 0:
            color = theme.ERROR if fraction > 0.9 else theme.WARNING
            canvas.create_rectangle(0, 0, fw, h, fill=color, outline="")
        pct_txt = f"{int(fraction * 100)}%"
        canvas.create_text(w // 2, h // 2, text=pct_txt,
                            fill=theme.BG_BASE, font=theme.FONT_SMALL)
