"""
TecoQC - Paso 13: Prueba de almacenamiento (discos, SMART, velocidad)
"""

import tkinter as tk
from ui.steps.base_step import BaseStep
from ui.components import Card, InfoRow, Spinner
from ui import theme
from config import STATUS_PASSED, STATUS_FAILED


class Step(BaseStep):
    TITLE = "Almacenamiento"
    DESCRIPTION = ("Listado de unidades, estado SMART y prueba de velocidad de "
                   "lectura/escritura.")
    STEP_NUM = 13

    def build_ui(self, parent):
        self._spinner = Spinner(parent, text="Analizando discos...", bg=theme.BG_BASE)
        self._spinner.pack(pady=20)
        self._spinner.start()

        self._main = tk.Frame(parent, bg=theme.BG_BASE)
        self._main.pack(fill=tk.BOTH, expand=True)

    def on_enter(self):
        self.run_in_thread(self._collect, on_done=self._show,
                            on_error=self._show_error)

    def _collect(self):
        from hardware.storage import get_drives_info, get_physical_drives_wmi, get_smart_status
        return {
            "logical": get_drives_info(),
            "physical": get_physical_drives_wmi(),
            "smart": get_smart_status(),
        }

    def _show(self, data):
        self._spinner.stop()
        self._spinner.pack_forget()

        for w in self._main.winfo_children():
            w.destroy()

        logical = data.get("logical", [])
        physical = data.get("physical", [])
        smart = data.get("smart", [])

        # Physical drives
        if physical:
            tk.Label(self._main, text="Discos Físicos",
                     bg=theme.BG_BASE, fg=theme.TEXT_PRIMARY,
                     font=theme.FONT_H3).pack(anchor="w", pady=(0, 8))

            for disk in physical:
                if "error" in disk:
                    continue
                self._make_disk_card(disk)

        # Logical drives
        tk.Label(self._main, text="Unidades Lógicas (Particiones)",
                 bg=theme.BG_BASE, fg=theme.TEXT_PRIMARY,
                 font=theme.FONT_H3).pack(anchor="w", pady=(12, 8))

        if logical:
            drives_frame = tk.Frame(self._main, bg=theme.BG_BASE)
            drives_frame.pack(fill=tk.X)
            col_count = min(len(logical), 3)
            for i in range(col_count):
                drives_frame.columnconfigure(i, weight=1)

            for i, drive in enumerate(logical):
                if "error" in drive:
                    continue
                col = i % 3
                row = i // 3
                self._make_drive_card(drives_frame, drive, row, col)
        else:
            tk.Label(self._main, text="No se encontraron unidades.",
                     bg=theme.BG_BASE, fg=theme.WARNING,
                     font=theme.FONT_BODY).pack(anchor="w")

        # SMART status
        tk.Label(self._main, text="Estado SMART (via wmic)",
                 bg=theme.BG_BASE, fg=theme.TEXT_PRIMARY,
                 font=theme.FONT_H3).pack(anchor="w", pady=(12, 8))

        smart_frame = Card(self._main)
        smart_frame.pack(fill=tk.X)

        if smart:
            for item in smart:
                if "error" in item:
                    tk.Label(smart_frame, text=f"Error SMART: {item['error']}",
                             bg=theme.BG_SURFACE0, fg=theme.WARNING,
                             font=theme.FONT_SMALL, padx=16, pady=4).pack(anchor="w")
                    continue
                status = item.get("status", "N/D")
                fg = theme.SUCCESS if status.lower() == "ok" else theme.WARNING
                row = tk.Frame(smart_frame, bg=theme.BG_SURFACE0)
                row.pack(fill=tk.X, padx=16, pady=4)
                tk.Label(row, text=item.get("model", "N/D")[:40],
                          bg=theme.BG_SURFACE0, fg=theme.TEXT_PRIMARY,
                          font=theme.FONT_BODY, width=35, anchor="w").pack(side=tk.LEFT)
                tk.Label(row, text=f"Estado: {status}",
                          bg=theme.BG_SURFACE0, fg=fg,
                          font=theme.FONT_BODY_BOLD).pack(side=tk.LEFT, padx=16)
                size_gb = round(item.get("size_bytes", 0) / (1024**3), 1)
                tk.Label(row, text=f"{size_gb} GB",
                          bg=theme.BG_SURFACE0, fg=theme.TEXT_MUTED,
                          font=theme.FONT_SMALL).pack(side=tk.RIGHT)
        else:
            tk.Label(smart_frame, text="No se pudo obtener estado SMART via wmic.",
                     bg=theme.BG_SURFACE0, fg=theme.WARNING,
                     font=theme.FONT_BODY, padx=16, pady=10).pack(anchor="w")

        # Speed test
        self._build_speed_test()

        # Summary
        phys_count = len([d for d in physical if "error" not in d])
        log_count = len([d for d in logical if "error" not in d])
        self.set_status(STATUS_PASSED,
                         f"{phys_count} disco(s) físico(s), {log_count} unidad(es) lógica(s)")
        self._set_detail(f"{phys_count} discos | {log_count} particiones")

    def _make_disk_card(self, disk):
        card = Card(self._main)
        card.pack(fill=tk.X, pady=(0, 8))

        hdr = tk.Frame(card, bg=theme.BG_SURFACE1)
        hdr.pack(fill=tk.X)
        tk.Label(hdr, text=f"💽  {disk.get('model', 'Disco desconocido')}",
                 bg=theme.BG_SURFACE1, fg=theme.TEXT_PRIMARY,
                 font=theme.FONT_H3, padx=16, pady=8).pack(side=tk.LEFT)

        status = disk.get("status", "N/D")
        status_color = theme.SUCCESS if status.lower() == "ok" else theme.WARNING
        tk.Label(hdr, text=status,
                 bg=theme.BG_SURFACE1, fg=status_color,
                 font=theme.FONT_BODY_BOLD, padx=16).pack(side=tk.RIGHT)

        inner = tk.Frame(card, bg=theme.BG_SURFACE0)
        inner.pack(fill=tk.X, padx=16, pady=8)

        grid = tk.Frame(inner, bg=theme.BG_SURFACE0)
        grid.pack(fill=tk.X)
        grid.columnconfigure(0, weight=1)
        grid.columnconfigure(1, weight=1)

        fields = [
            ("Tamaño", f"{disk.get('size_gb', 0):.1f} GB"),
            ("Interfaz", disk.get("interface", "N/D")),
            ("Tipo de medio", disk.get("media_type", "N/D")),
            ("Particiones", str(disk.get("partitions", 0))),
            ("N/S", disk.get("serial", "N/D")),
        ]
        for i, (lbl, val) in enumerate(fields):
            InfoRow(grid, lbl, val, label_width=14,
                    bg=theme.BG_SURFACE0).grid(row=i//2, column=i%2,
                                                sticky="ew", padx=4, pady=2)

    def _make_drive_card(self, parent, drive, row, col):
        card = Card(parent)
        card.grid(row=row, column=col, padx=4, pady=4, sticky="nsew")

        inner = tk.Frame(card, bg=theme.BG_SURFACE0)
        inner.pack(fill=tk.X, padx=12, pady=10)

        device = drive.get("device", "N/D")
        mount = drive.get("mountpoint", "")
        fs = drive.get("fstype", "N/D")
        total = drive.get("total_gb", 0)
        used = drive.get("used_gb", 0)
        free = drive.get("free_gb", 0)
        pct = drive.get("percent", 0)

        # Drive label
        tk.Label(inner, text=f"💾  {device} ({mount})",
                 bg=theme.BG_SURFACE0, fg=theme.TEXT_PRIMARY,
                 font=theme.FONT_BODY_BOLD).pack(anchor="w", pady=(0, 6))

        # Usage bar
        bar = tk.Canvas(inner, height=14, bg=theme.BG_SURFACE1, highlightthickness=0)
        bar.pack(fill=tk.X, pady=(0, 4))
        bar.update_idletasks()
        w = bar.winfo_width() or 200
        color = (theme.SUCCESS if pct < 70
                  else theme.WARNING if pct < 90
                  else theme.ERROR)
        bar.create_rectangle(0, 0, int(w * pct / 100), 14, fill=color, outline="")
        bar.create_text(w//2, 7, text=f"{pct:.1f}%",
                         fill=theme.BG_BASE, font=(theme.FONT_FAMILY, 7))

        tk.Label(inner, text=f"Usado: {used:.1f} GB / Total: {total:.1f} GB  ({fs})",
                 bg=theme.BG_SURFACE0, fg=theme.TEXT_SECONDARY,
                 font=theme.FONT_SMALL).pack(anchor="w")
        tk.Label(inner, text=f"Libre: {free:.1f} GB",
                 bg=theme.BG_SURFACE0, fg=theme.TEXT_MUTED,
                 font=theme.FONT_SMALL).pack(anchor="w")

    def _build_speed_test(self):
        tk.Label(self._main, text="Prueba de Velocidad de Disco",
                 bg=theme.BG_BASE, fg=theme.TEXT_PRIMARY,
                 font=theme.FONT_H3).pack(anchor="w", pady=(12, 8))

        speed_card = Card(self._main)
        speed_card.pack(fill=tk.X, pady=(0, 8))

        inner = tk.Frame(speed_card, bg=theme.BG_SURFACE0)
        inner.pack(fill=tk.X, padx=16, pady=12)

        tk.Label(inner,
                 text="Escribe y lee 64 MB en el directorio del usuario para medir la velocidad del disco.",
                 bg=theme.BG_SURFACE0, fg=theme.TEXT_SECONDARY,
                 font=theme.FONT_BODY).pack(anchor="w", pady=(0, 10))

        btn_row = tk.Frame(inner, bg=theme.BG_SURFACE0)
        btn_row.pack(anchor="w")

        self._speed_btn = tk.Button(btn_row, text="▶  Iniciar prueba de velocidad (64 MB)",
                                     command=self._run_speed_test, **theme.BTN_SECONDARY)
        self._speed_btn.pack(side=tk.LEFT, padx=(0, 12))

        self._speed_lbl = tk.Label(inner, text="",
                                    bg=theme.BG_SURFACE0, fg=theme.TEXT_SECONDARY,
                                    font=theme.FONT_BODY)
        self._speed_lbl.pack(anchor="w", pady=(8, 0))

    def _run_speed_test(self):
        self._speed_btn.configure(state=tk.DISABLED)
        self._speed_lbl.configure(text="⏳ Ejecutando... (puede tardar 10-30s)",
                                   fg=theme.ACCENT_BLUE)
        self.run_in_thread(self._do_speed_test, on_done=self._show_speed,
                            on_error=lambda e: self._speed_error(e))

    def _do_speed_test(self):
        from hardware.storage import run_disk_speed_test
        return run_disk_speed_test(size_mb=64)

    def _show_speed(self, result):
        self._speed_btn.configure(state=tk.NORMAL)
        if result.get("error"):
            self._speed_lbl.configure(
                text=f"✗ Error: {result['error']}", fg=theme.ERROR)
            return
        wr = result.get("write_mb_s", 0)
        rd = result.get("read_mb_s", 0)
        self._speed_lbl.configure(
            text=f"✓  Escritura: {wr:.1f} MB/s  |  Lectura: {rd:.1f} MB/s",
            fg=theme.SUCCESS)
        self._set_detail(f"Escritura: {wr:.1f} MB/s | Lectura: {rd:.1f} MB/s")

    def _speed_error(self, error):
        self._speed_btn.configure(state=tk.NORMAL)
        self._speed_lbl.configure(text=f"Error: {error}", fg=theme.ERROR)

    def _show_error(self, error):
        self._spinner.stop(f"Error: {error}")
        self.set_status(STATUS_FAILED, str(error))
