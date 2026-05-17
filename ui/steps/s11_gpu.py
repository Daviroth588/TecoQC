"""
TecoQC - Paso 11: Información de GPU + test de renderizado 2D
"""

import tkinter as tk
import time
import threading
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
        self._spinner = Spinner(parent, text="Detectando GPUs...", bg=theme.BG_BASE)
        self._spinner.pack(pady=30)
        self._spinner.start()

        self._content = tk.Frame(parent, bg=theme.BG_BASE)
        self._content.pack(fill=tk.BOTH, expand=True)

    def on_enter(self):
        self.run_in_thread(self._collect, on_done=self._show,
                            on_error=self._show_error)

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

        # Build 2D rendering test section
        self._build_render_test()

        count = len([g for g in wmi_gpus if "error" not in g]) if wmi_gpus else len(nvidia.get("gpus", []))
        self._set_detail(f"{count} GPU(s) detectada(s) — ejecute test de renderizado")

    def _build_render_test(self):
        render_card = Card(self._content)
        render_card.pack(fill=tk.X, pady=(8, 0))

        hdr = tk.Frame(render_card, bg=theme.BG_SURFACE1)
        hdr.pack(fill=tk.X)
        tk.Label(hdr, text="Test de Renderizado 2D",
                 bg=theme.BG_SURFACE1, fg=theme.TEXT_PRIMARY,
                 font=theme.FONT_H3, padx=16, pady=8).pack(side=tk.LEFT)

        inner = tk.Frame(render_card, bg=theme.BG_SURFACE0)
        inner.pack(fill=tk.X, padx=16, pady=10)

        tk.Label(inner,
                 text=f"Dibuja {RENDER_SHAPES} formas en canvas y mide el tiempo. "
                      f"Aprobado si completa en < {RENDER_MAX_MS} ms.",
                 bg=theme.BG_SURFACE0, fg=theme.TEXT_SECONDARY,
                 font=theme.FONT_BODY).pack(anchor="w", pady=(0, 8))

        btn_row = tk.Frame(inner, bg=theme.BG_SURFACE0)
        btn_row.pack(anchor="w")

        self._render_btn = tk.Button(btn_row, text="▶  Ejecutar test de renderizado",
                                      command=self._run_render_test,
                                      **theme.BTN_PRIMARY)
        self._render_btn.pack(side=tk.LEFT, padx=(0, 12))

        self._render_lbl = tk.Label(inner, text="",
                                     bg=theme.BG_SURFACE0, fg=theme.TEXT_SECONDARY,
                                     font=theme.FONT_BODY)
        self._render_lbl.pack(anchor="w", pady=(8, 0))

        # Hidden canvas for benchmark (small, offscreen-ish)
        self._bench_canvas = tk.Canvas(inner, width=400, height=100,
                                        bg=theme.BG_CRUST, highlightthickness=0)
        self._bench_canvas.pack(fill=tk.X, pady=(8, 0))

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
