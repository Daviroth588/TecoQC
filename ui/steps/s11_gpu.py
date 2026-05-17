"""
TecoQC - Paso 11: Información de GPU
"""

import tkinter as tk
from ui.steps.base_step import BaseStep
from ui.components import Card, InfoRow, Spinner
from ui import theme
from config import STATUS_PASSED, STATUS_FAILED


class Step(BaseStep):
    TITLE = "Tarjeta Gráfica (GPU)"
    DESCRIPTION = ("Detección de tarjetas gráficas NVIDIA, AMD e Intel. "
                   "Información de VRAM, controlador y temperatura.")
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

        # NVIDIA via nvidia-smi
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

        # WMI adapters
        if wmi_gpus:
            for i, gpu in enumerate(wmi_gpus):
                if "error" in gpu:
                    continue
                any_found = True
                vendor = gpu.get("vendor", "Desconocido")
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
                    title=f"GPU {i+1} — {vendor} (WMI)",
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
                     "Asegúrese de que los controladores estén instalados\n"
                     "y que WMI esté disponible.",
                bg=theme.BG_BASE, fg=theme.WARNING,
                font=theme.FONT_BODY, justify="center",
            ).pack(expand=True)
            self.set_status(STATUS_FAILED, "No se detectaron GPUs")
        else:
            count = len(wmi_gpus) if wmi_gpus else len(nvidia.get("gpus", []))
            self.set_status(STATUS_PASSED,
                             f"{count} GPU(s) detectada(s)")

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
            row = i // 2
            col = i % 2
            InfoRow(grid, label, str(val), label_width=14,
                    bg=theme.BG_SURFACE0).grid(row=row, column=col,
                                                sticky="ew", padx=4, pady=2)
