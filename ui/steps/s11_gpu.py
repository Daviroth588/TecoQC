"""
TecoQC - Paso 11: Información de GPU + test de renderizado 2D y 3D
"""

import tkinter as tk
import time
import threading
import math
from ui.steps.base_step import BaseStep
from ui.components import Card, InfoRow, Spinner
from ui import theme
from config import STATUS_PASSED, STATUS_FAILED


RENDER_SHAPES = 1000
RENDER_MAX_MS = 3000


class Step(BaseStep):
    TITLE = "Tarjeta Gráfica (GPU)"
    DESCRIPTION = ("Detección de GPUs NVIDIA/AMD/Intel, VRAM, controlador y "
                   "test de renderizado 2D para validar aceleración gráfica.")
    STEP_NUM = 11

    def build_ui(self, parent):
        self._3d_running = False
        self._monitoring = False

        self._spinner = Spinner(parent, text="Detectando GPUs...", bg=theme.BG_BASE)
        self._spinner.pack(pady=30)
        self._spinner.start()

        self._content = tk.Frame(parent, bg=theme.BG_BASE)
        self._content.pack(fill=tk.BOTH, expand=True)

    def on_enter(self):
        self._3d_running = False
        self.run_in_thread(self._collect, on_done=self._show,
                            on_error=self._show_error)

    def on_leave(self):
        super().on_leave()
        self._3d_running = False
        self._monitoring = False

    def _collect(self):
        from hardware.gpu import get_all_gpu_info
        return get_all_gpu_info()

    def _show(self, data):
        self._spinner.stop()
        self._spinner.pack_forget()

        for widget in self._content.winfo_children():
            widget.destroy()

        wmi_gpus = data.get("wmi_gpus", [])
        nvidia = data.get("nvidia", {})
        temps = data.get("temperatures", {})

        any_found = False

        if nvidia.get("available") and nvidia.get("gpus"):
            for i, gpu in enumerate(nvidia["gpus"]):
                any_found = True
                self._make_gpu_card(
                    self._content,
                    title=f"GPU {i+1} — NVIDIA (nvidia-smi)",
                    vendor_color=theme.SUCCESS,
                    fields=[
                        ("Nombre", gpu.get("name", "N/D")),
                        ("VRAM Total", f"{gpu.get('vram_total_mb', 0)} MB"),
                        ("VRAM Usada", f"{gpu.get('vram_used_mb', 0)} MB"),
                        ("VRAM Libre", f"{gpu.get('vram_free_mb', 0)} MB"),
                        ("Uso GPU", f"{gpu.get('utilization_pct', 0):.1f}%"),
                        ("Temperatura", f"{gpu.get('temperature', 0):.1f}°C"),
                        ("Controlador", gpu.get("driver_version", "N/D")),
                    ]
                )

        if wmi_gpus:
            real_idx = 0
            for gpu in wmi_gpus:
                if "error" in gpu:
                    continue
                is_virtual = gpu.get("is_virtual", False)
                vendor = gpu.get("vendor", "Desconocido")

                if is_virtual:
                    # Show as collapsed info-only row, not a full GPU card
                    virt_row = tk.Frame(self._content, bg=theme.BG_SURFACE0,
                                        highlightthickness=1,
                                        highlightbackground=theme.BG_SURFACE2)
                    virt_row.pack(fill=tk.X, pady=(4, 0))
                    tk.Label(virt_row,
                             text=f"⊘  {gpu.get('name', 'N/D')}  — adaptador virtual (excluido del diagnóstico)",
                             bg=theme.BG_SURFACE0, fg=theme.TEXT_MUTED,
                             font=theme.FONT_SMALL, padx=12, pady=6).pack(anchor="w")
                    continue

                real_idx += 1
                any_found = True
                color = (theme.SUCCESS if vendor == "NVIDIA"
                          else theme.WARNING if vendor == "AMD"
                          else theme.ACCENT_BLUE)

                temp_text = "N/D"
                if temps:
                    for key, val in temps.items():
                        if "GPU" in key.upper():
                            temp_text = f"{val:.1f}°C"
                            break

                self._make_gpu_card(
                    self._content,
                    title=f"GPU {real_idx} — {vendor} (WMI)",
                    vendor_color=color,
                    fields=[
                        ("Nombre", gpu.get("name", "N/D")),
                        ("Fabricante", vendor),
                        ("VRAM", f"{gpu.get('vram_total_mb', 0)} MB"),
                        ("Controlador", gpu.get("driver_version", "N/D")),
                        ("Modo de video", gpu.get("video_mode", "N/D")),
                        ("Estado", gpu.get("status", "N/D")),
                        ("Temperatura", temp_text),
                    ]
                )

        if not any_found:
            tk.Label(
                self._content,
                text="⚠  No se detectaron tarjetas gráficas.\n\n"
                     "Asegúrese de que los controladores estén instalados.",
                bg=theme.BG_BASE, fg=theme.WARNING,
                font=theme.FONT_BODY, justify="center",
            ).pack(expand=True)
            self.set_status(STATUS_FAILED, "No se detectaron GPUs")
            return

        # Real-time monitor card
        self._build_monitor_card()

        # Build rendering test section
        self._build_render_test()

        count = len([g for g in wmi_gpus if "error" not in g]) if wmi_gpus else len(nvidia.get("gpus", []))
        self._set_detail(f"{count} GPU(s) detectada(s) — ejecute test de renderizado")

        # Start real-time monitoring
        self._monitoring = True
        threading.Thread(target=self._monitor_loop, daemon=True).start()

    def _build_monitor_card(self):
        from ui.components import Card
        mon_card = Card(self._content)
        mon_card.pack(fill=tk.X, pady=(0, 8))

        hdr = tk.Frame(mon_card, bg=theme.BG_SURFACE1)
        hdr.pack(fill=tk.X)
        tk.Label(hdr, text="Monitor en Tiempo Real",
                 bg=theme.BG_SURFACE1, fg=theme.TEXT_PRIMARY,
                 font=theme.FONT_H3, padx=16, pady=6).pack(side=tk.LEFT)

        inner = tk.Frame(mon_card, bg=theme.BG_SURFACE0)
        inner.pack(fill=tk.X, padx=16, pady=8)

        # GPU utilization bar
        util_row = tk.Frame(inner, bg=theme.BG_SURFACE0)
        util_row.pack(fill=tk.X, pady=2)
        tk.Label(util_row, text="Uso GPU:", bg=theme.BG_SURFACE0,
                 fg=theme.TEXT_SECONDARY, font=theme.FONT_BODY,
                 width=14, anchor="w").pack(side=tk.LEFT)
        self._gpu_bar = tk.Canvas(util_row, height=20, bg=theme.BG_SURFACE1,
                                   highlightthickness=0)
        self._gpu_bar.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=8)
        self._gpu_pct_lbl = tk.Label(util_row, text="—",
                                      bg=theme.BG_SURFACE0, fg=theme.TEXT_PRIMARY,
                                      font=theme.FONT_BODY_BOLD, width=6)
        self._gpu_pct_lbl.pack(side=tk.LEFT)

        # VRAM bar
        vram_row = tk.Frame(inner, bg=theme.BG_SURFACE0)
        vram_row.pack(fill=tk.X, pady=2)
        tk.Label(vram_row, text="VRAM usada:", bg=theme.BG_SURFACE0,
                 fg=theme.TEXT_SECONDARY, font=theme.FONT_BODY,
                 width=14, anchor="w").pack(side=tk.LEFT)
        self._vram_bar = tk.Canvas(vram_row, height=20, bg=theme.BG_SURFACE1,
                                    highlightthickness=0)
        self._vram_bar.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=8)
        self._vram_lbl = tk.Label(vram_row, text="—",
                                   bg=theme.BG_SURFACE0, fg=theme.TEXT_PRIMARY,
                                   font=theme.FONT_BODY_BOLD, width=10)
        self._vram_lbl.pack(side=tk.LEFT)

        # Temperature
        temp_row = tk.Frame(inner, bg=theme.BG_SURFACE0)
        temp_row.pack(fill=tk.X, pady=2)
        tk.Label(temp_row, text="Temperatura:", bg=theme.BG_SURFACE0,
                 fg=theme.TEXT_SECONDARY, font=theme.FONT_BODY,
                 width=14, anchor="w").pack(side=tk.LEFT)
        self._gpu_temp_lbl = tk.Label(temp_row, text="N/D",
                                       bg=theme.BG_SURFACE0, fg=theme.TEXT_PRIMARY,
                                       font=theme.FONT_BODY_BOLD)
        self._gpu_temp_lbl.pack(side=tk.LEFT, padx=8)

        # Usage graph
        tk.Label(inner, text="Historial de uso GPU (último minuto):",
                 bg=theme.BG_SURFACE0, fg=theme.TEXT_SECONDARY,
                 font=theme.FONT_SMALL).pack(anchor="w", pady=(8, 2))
        self._gpu_graph = tk.Canvas(inner, height=80, bg=theme.BG_CRUST,
                                     highlightthickness=1,
                                     highlightbackground=theme.BG_SURFACE2)
        self._gpu_graph.pack(fill=tk.X)
        self._gpu_history = [0.0] * 60

    def _draw_gpu_bar(self, canvas, pct, label_widget, text):
        w = canvas.winfo_width() or 200
        h = 20
        canvas.delete("all")
        canvas.create_rectangle(0, 0, w, h, fill=theme.BG_SURFACE1, outline="")
        fw = int(w * min(pct, 100) / 100)
        if fw > 0:
            color = (theme.SUCCESS if pct < 60 else theme.WARNING if pct < 85 else theme.ERROR)
            canvas.create_rectangle(0, 0, fw, h, fill=color, outline="")
        canvas.create_text(w // 2, h // 2, text=f"{pct:.1f}%",
                           fill=theme.BG_BASE, font=theme.FONT_SMALL)
        label_widget.configure(text=text)

    def _draw_gpu_graph(self):
        canvas = self._gpu_graph
        w = canvas.winfo_width() or 400
        h = 80
        canvas.delete("all")
        canvas.create_rectangle(0, 0, w, h, fill=theme.BG_CRUST, outline="")
        for pct in [25, 50, 75]:
            y = h - (pct / 100 * h)
            canvas.create_line(0, y, w, y, fill=theme.BG_SURFACE1, dash=(2, 4))
            canvas.create_text(3, y - 6, text=f"{pct}%", anchor="nw",
                               fill=theme.TEXT_MUTED, font=(theme.FONT_FAMILY, 7))
        points = self._gpu_history
        step = w / max(len(points) - 1, 1)
        coords = []
        for i, val in enumerate(points):
            coords.extend([i * step, h - (val / 100 * h)])
        if len(coords) >= 4:
            canvas.create_line(*coords, fill=theme.ACCENT_BLUE, width=2, smooth=True)

    def _monitor_loop(self):
        import time
        while self._monitoring:
            try:
                from hardware.gpu import get_gpu_live_stats
                stats = get_gpu_live_stats()
                entries = stats.get("entries", [])
                if entries:
                    e = entries[0]
                    gpu_pct = e.get("gpu_pct", 0)
                    vram_used = e.get("vram_used_mb", 0)
                    vram_total = e.get("vram_total_mb", 0)
                    temp_c = e.get("temp_c")
                    vram_pct = (vram_used / vram_total * 100) if vram_total > 0 else 0

                    def update(gp=gpu_pct, vp=vram_pct, vu=vram_used, vt=vram_total, tc=temp_c):
                        if not self._monitoring:
                            return
                        try:
                            self._draw_gpu_bar(self._gpu_bar, gp,
                                               self._gpu_pct_lbl, f"{gp:.1f}%")
                            vram_text = (f"{vu} / {vt} MB" if vt > 0 else "N/D")
                            self._draw_gpu_bar(self._vram_bar, vp,
                                               self._vram_lbl, vram_text)
                            if tc is not None:
                                temp_color = (theme.ERROR if tc >= 85 else
                                              theme.WARNING if tc >= 70 else theme.SUCCESS)
                                self._gpu_temp_lbl.configure(
                                    text=f"{tc:.1f}°C", fg=temp_color)
                            else:
                                self._gpu_temp_lbl.configure(text="N/D",
                                                              fg=theme.TEXT_MUTED)
                            self._gpu_history.pop(0)
                            self._gpu_history.append(gp)
                            self._draw_gpu_graph()
                        except Exception:
                            pass

                    self.after(0, update)
            except Exception:
                pass
            time.sleep(2)

    def _build_render_test(self):
        render_card = Card(self._content)
        render_card.pack(fill=tk.X, pady=(8, 0))

        hdr = tk.Frame(render_card, bg=theme.BG_SURFACE1)
        hdr.pack(fill=tk.X)
        tk.Label(hdr, text="Tests de Renderizado",
                 bg=theme.BG_SURFACE1, fg=theme.TEXT_PRIMARY,
                 font=theme.FONT_H3, padx=16, pady=8).pack(side=tk.LEFT)

        inner = tk.Frame(render_card, bg=theme.BG_SURFACE0)
        inner.pack(fill=tk.X, padx=16, pady=10)

        # Two columns: 2D and 3D tests
        test_cols = tk.Frame(inner, bg=theme.BG_SURFACE0)
        test_cols.pack(fill=tk.X)
        test_cols.columnconfigure(0, weight=1)
        test_cols.columnconfigure(1, weight=1)

        # ── 2D Test ───────────────────────────────────────────────────
        col2d = tk.Frame(test_cols, bg=theme.BG_SURFACE0,
                          highlightthickness=1, highlightbackground=theme.BG_SURFACE1)
        col2d.grid(row=0, column=0, padx=(0, 6), sticky="nsew")

        tk.Label(col2d, text="Test 2D — Formas en canvas",
                 bg=theme.BG_SURFACE0, fg=theme.ACCENT_BLUE,
                 font=theme.FONT_BODY_BOLD, padx=10, pady=6).pack(anchor="w")
        tk.Label(col2d,
                 text=f"Dibuja {RENDER_SHAPES} figuras.\nAprobado si < {RENDER_MAX_MS} ms.",
                 bg=theme.BG_SURFACE0, fg=theme.TEXT_SECONDARY,
                 font=theme.FONT_SMALL, padx=10, justify="left").pack(anchor="w")

        self._render_btn = tk.Button(col2d, text="▶  Ejecutar 2D",
                                      command=self._run_render_test,
                                      **theme.BTN_PRIMARY)
        self._render_btn.pack(padx=10, pady=6, anchor="w")

        self._render_lbl = tk.Label(col2d, text="",
                                     bg=theme.BG_SURFACE0, fg=theme.TEXT_SECONDARY,
                                     font=theme.FONT_SMALL, padx=10, justify="left")
        self._render_lbl.pack(anchor="w", pady=(0, 4))

        self._bench_canvas = tk.Canvas(col2d, width=1, height=80,
                                        bg=theme.BG_CRUST, highlightthickness=0)
        self._bench_canvas.pack(fill=tk.X, padx=10, pady=(0, 8))

        # ── 3D Test ───────────────────────────────────────────────────
        col3d = tk.Frame(test_cols, bg=theme.BG_SURFACE0,
                          highlightthickness=1, highlightbackground=theme.BG_SURFACE1)
        col3d.grid(row=0, column=1, padx=(6, 0), sticky="nsew")

        tk.Label(col3d, text="Test 3D — Cubo wireframe",
                 bg=theme.BG_SURFACE0, fg=theme.ACCENT_BLUE,
                 font=theme.FONT_BODY_BOLD, padx=10, pady=6).pack(anchor="w")
        tk.Label(col3d,
                 text="Anima un cubo 3D con proyección perspectiva.\nMide FPS durante 5s.",
                 bg=theme.BG_SURFACE0, fg=theme.TEXT_SECONDARY,
                 font=theme.FONT_SMALL, padx=10, justify="left").pack(anchor="w")

        self._render3d_btn = tk.Button(col3d, text="▶  Ejecutar 3D",
                                        command=self._run_3d_test,
                                        **theme.BTN_SECONDARY)
        self._render3d_btn.pack(padx=10, pady=6, anchor="w")

        self._render3d_lbl = tk.Label(col3d, text="",
                                       bg=theme.BG_SURFACE0, fg=theme.TEXT_SECONDARY,
                                       font=theme.FONT_SMALL, padx=10, justify="left")
        self._render3d_lbl.pack(anchor="w", pady=(0, 4))

        self._canvas3d = tk.Canvas(col3d, width=1, height=180,
                                    bg="#000010", highlightthickness=0)
        self._canvas3d.pack(fill=tk.X, padx=10, pady=(0, 8))

        self._3d_running = False

    def _run_render_test(self):
        self._render_btn.configure(state=tk.DISABLED)
        self._render_lbl.configure(text="⏳ Renderizando...", fg=theme.ACCENT_BLUE)
        threading.Thread(target=self._do_render_test, daemon=True).start()

    def _do_render_test(self):
        import random
        try:
            canvas = self._bench_canvas
            w = canvas.winfo_width() or 400
            h = canvas.winfo_height() or 100

            t0 = time.time()

            def draw():
                canvas.delete("all")
                colors = [theme.ACCENT_BLUE, theme.SUCCESS, theme.WARNING,
                           theme.ERROR, theme.INFO, theme.ACCENT_LAVENDER]
                rnd = random.Random(42)
                for i in range(RENDER_SHAPES):
                    x0 = rnd.randint(0, w - 20)
                    y0 = rnd.randint(0, h - 20)
                    x1 = x0 + rnd.randint(5, 30)
                    y1 = y0 + rnd.randint(5, 20)
                    col = colors[i % len(colors)]
                    if i % 3 == 0:
                        canvas.create_rectangle(x0, y0, x1, y1, fill=col, outline="")
                    elif i % 3 == 1:
                        canvas.create_oval(x0, y0, x1, y1, fill=col, outline="")
                    else:
                        canvas.create_line(x0, y0, x1, y1, fill=col, width=2)
                canvas.update()

            self.after(0, draw)
            # Wait for rendering to complete
            time.sleep(0.2)
            canvas.update_idletasks()
            elapsed_ms = round((time.time() - t0) * 1000)

            def result(ms=elapsed_ms):
                self._render_btn.configure(state=tk.NORMAL)
                ok = ms <= RENDER_MAX_MS
                fg = theme.SUCCESS if ok else theme.WARNING
                verdict = "✓ Renderizado OK" if ok else "⚠ Renderizado lento"
                self._render_lbl.configure(
                    text=f"{verdict} — {ms} ms para {RENDER_SHAPES} formas (máx {RENDER_MAX_MS} ms)",
                    fg=fg)
                if ok:
                    self.set_status(STATUS_PASSED,
                                     f"GPU detectada | Render: {ms} ms")
                else:
                    self.set_status(STATUS_FAILED,
                                     f"Render lento: {ms} ms > {RENDER_MAX_MS} ms")
            self.after(0, result)
        except Exception as e:
            def err(msg=str(e)):
                self._render_btn.configure(state=tk.NORMAL)
                self._render_lbl.configure(text=f"Error: {msg}", fg=theme.ERROR)
            self.after(0, err)

    def _run_3d_test(self):
        if self._3d_running:
            self._3d_running = False
            self._render3d_btn.configure(text="▶  Ejecutar 3D")
            return
        self._3d_running = True
        self._render3d_btn.configure(text="■  Detener 3D")
        self._render3d_lbl.configure(text="⏳ Renderizando cubo 3D...", fg=theme.ACCENT_BLUE)
        threading.Thread(target=self._do_3d_test, daemon=True).start()

    def _do_3d_test(self):
        canvas = self._canvas3d
        start = time.time()
        deadline = start + 5.0   # 5-second test
        frames = 0
        angle = 0.0

        # Unit cube vertices
        verts = [
            (-1, -1, -1), (1, -1, -1), (1, 1, -1), (-1, 1, -1),
            (-1, -1,  1), (1, -1,  1), (1, 1,  1), (-1, 1,  1),
        ]
        # Edges between vertex indices
        edges = [
            (0, 1), (1, 2), (2, 3), (3, 0),  # back face
            (4, 5), (5, 6), (6, 7), (7, 4),  # front face
            (0, 4), (1, 5), (2, 6), (3, 7),  # connecting edges
        ]
        colors = [theme.ACCENT_BLUE, theme.SUCCESS, theme.WARNING,
                  theme.ERROR, theme.INFO, theme.ACCENT_LAVENDER]

        def project(x, y, z, w, h, fov=5.0, dist=4.0):
            z_off = z + dist
            if z_off == 0:
                z_off = 0.001
            scale = fov / z_off
            sx = int(x * scale * (w / 4) + w / 2)
            sy = int(-y * scale * (h / 4) + h / 2)
            return sx, sy

        while self._3d_running and time.time() < deadline:
            t_frame = time.time()
            angle += 0.03

            cx, sx = math.cos(angle), math.sin(angle)
            cy, sy_ = math.cos(angle * 0.7), math.sin(angle * 0.7)

            def rot(x, y, z):
                # Rotate around Y axis
                x2 = x * cx - z * sx
                z2 = x * sx + z * cx
                # Rotate around X axis
                y2 = y * cy - z2 * sy_
                z3 = y * sy_ + z2 * cy
                return x2, y2, z3

            def draw():
                w = canvas.winfo_width() or 200
                h = canvas.winfo_height() or 180
                canvas.delete("all")
                canvas.create_rectangle(0, 0, w, h, fill="#000010", outline="")

                projected = [project(*rot(*v), w, h) for v in verts]

                for i, (i0, i1) in enumerate(edges):
                    x0, y0 = projected[i0]
                    x1, y1 = projected[i1]
                    col = colors[i % len(colors)]
                    canvas.create_line(x0, y0, x1, y1, fill=col, width=2)

                # FPS label
                canvas.create_text(w - 4, 4, text=f"{frames}f", anchor="ne",
                                   fill=theme.TEXT_MUTED,
                                   font=(theme.FONT_FAMILY, 7))

            self.after(0, draw)
            frames += 1
            elapsed_frame = time.time() - t_frame
            sleep_time = max(0, 0.016 - elapsed_frame)   # target 60fps
            time.sleep(sleep_time)

        total_time = time.time() - start
        measured_fps = frames / total_time if total_time > 0 else 0
        self._3d_running = False

        def done(fps=measured_fps):
            self._render3d_btn.configure(text="▶  Ejecutar 3D")
            ok = fps >= 30
            color = theme.SUCCESS if ok else theme.WARNING
            verdict = "✓ 3D OK" if ok else "⚠ 3D lento"
            self._render3d_lbl.configure(
                text=f"{verdict} — {fps:.1f} FPS promedio ({frames} frames / {total_time:.1f}s)",
                fg=color)
        self.after(0, done)

    def _show_error(self, error):
        self._spinner.stop()
        self._spinner.configure(text=f"Error: {error}", fg=theme.ERROR)
        self.set_status(STATUS_FAILED, str(error))

    def _make_gpu_card(self, parent, title, vendor_color, fields):
        card = Card(parent)
        card.pack(fill=tk.X, pady=(0, 12))

        hdr = tk.Frame(card, bg=vendor_color)
        hdr.pack(fill=tk.X)
        tk.Label(hdr, text=title, bg=vendor_color,
                 fg=theme.BG_BASE, font=theme.FONT_H3,
                 padx=16, pady=8).pack(anchor="w")

        inner = tk.Frame(card, bg=theme.BG_SURFACE0)
        inner.pack(fill=tk.X, padx=16, pady=10)

        grid = tk.Frame(inner, bg=theme.BG_SURFACE0)
        grid.pack(fill=tk.X)
        grid.columnconfigure(0, weight=1)
        grid.columnconfigure(1, weight=1)

        for i, (label, val) in enumerate(fields):
            InfoRow(grid, label, str(val), label_width=14,
                    bg=theme.BG_SURFACE0).grid(row=i // 2, column=i % 2,
                                                sticky="ew", padx=4, pady=2)
