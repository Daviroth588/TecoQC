"""
TecoQC - Paso 13: Prueba de almacenamiento (discos, SMART, velocidad)
"""

import tkinter as tk
from ui.steps.base_step import BaseStep
from ui.components import Card, InfoRow, Spinner
from ui import theme
from config import (STATUS_PASSED, STATUS_FAILED,
                    DISK_SPEED_HDD_MIN_MB_S, DISK_SPEED_SSD_MIN_MB_S, DISK_IOPS_4K_MIN)


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
        tk.Label(self._main, text="Prueba de Velocidad y E/S Aleatorio",
                 bg=theme.BG_BASE, fg=theme.TEXT_PRIMARY,
                 font=theme.FONT_H3).pack(anchor="w", pady=(12, 8))

        speed_card = Card(self._main)
        speed_card.pack(fill=tk.X, pady=(0, 8))

        inner = tk.Frame(speed_card, bg=theme.BG_SURFACE0)
        inner.pack(fill=tk.X, padx=16, pady=12)

        # Disk type selector
        type_row = tk.Frame(inner, bg=theme.BG_SURFACE0)
        type_row.pack(anchor="w", pady=(0, 8))
        tk.Label(type_row, text="Tipo de disco:",
                 bg=theme.BG_SURFACE0, fg=theme.TEXT_SECONDARY,
                 font=theme.FONT_BODY).pack(side=tk.LEFT, padx=(0, 10))

        self._disk_type_var = tk.StringVar(value="SSD")
        for dtype in ["HDD", "SSD", "NVMe"]:
            tk.Radiobutton(
                type_row, text=dtype,
                variable=self._disk_type_var, value=dtype,
                bg=theme.BG_SURFACE0, fg=theme.TEXT_PRIMARY,
                selectcolor=theme.BG_SURFACE1,
                font=theme.FONT_BODY,
                activebackground=theme.BG_SURFACE0,
                indicatoron=0, relief="flat", padx=10, pady=4, cursor="hand2",
            ).pack(side=tk.LEFT, padx=3)

        self._threshold_lbl = tk.Label(
            inner, text="",
            bg=theme.BG_SURFACE0, fg=theme.TEXT_MUTED, font=theme.FONT_SMALL)
        self._threshold_lbl.pack(anchor="w", pady=(0, 8))
        self._disk_type_var.trace_add("write", self._update_threshold_label)
        self._update_threshold_label()

        tk.Label(inner,
                 text="Escribe 64 MB secuencial + 4 MB aleatorio (4 KB bloques) para medir rendimiento.",
                 bg=theme.BG_SURFACE0, fg=theme.TEXT_SECONDARY,
                 font=theme.FONT_BODY).pack(anchor="w", pady=(0, 10))

        btn_row = tk.Frame(inner, bg=theme.BG_SURFACE0)
        btn_row.pack(anchor="w")

        self._speed_btn = tk.Button(btn_row, text="▶  Iniciar prueba completa",
                                     command=self._run_speed_test, **theme.BTN_SECONDARY)
        self._speed_btn.pack(side=tk.LEFT, padx=(0, 12))

        self._speed_lbl = tk.Label(inner, text="",
                                    bg=theme.BG_SURFACE0, fg=theme.TEXT_SECONDARY,
                                    font=theme.FONT_BODY)
        self._speed_lbl.pack(anchor="w", pady=(8, 0))

        self._iops_lbl = tk.Label(inner, text="",
                               bg=theme.BG_SURFACE0, fg=theme.TEXT_SECONDARY,
                               font=theme.FONT_SMALL)
        self._iops_lbl.pack(anchor="w", pady=(2, 0))

    def _update_threshold_label(self, *args):
        dtype = self._disk_type_var.get()
        if dtype == "HDD":
            threshold = DISK_SPEED_HDD_MIN_MB_S
        else:
            threshold = DISK_SPEED_SSD_MIN_MB_S
        self._threshold_lbl.configure(
            text=f"Umbral mínimo para {dtype}: {threshold} MB/s escritura | {DISK_IOPS_4K_MIN} IOPS (4K)")

    def _run_speed_test(self):
        self._speed_btn.configure(state=tk.DISABLED)
        self._speed_lbl.configure(text="⏳ Ejecutando prueba secuencial...",
                                   fg=theme.ACCENT_BLUE)
        self._iops_lbl.configure(text="")
        self.run_in_thread(self._do_speed_test, on_done=self._show_speed,
                            on_error=lambda e: self._speed_error(e))

    def _do_speed_test(self):
        from hardware.storage import run_disk_speed_test
        seq = run_disk_speed_test(size_mb=64)
        iops_result = self._run_iops_test()
        return {"sequential": seq, "iops": iops_result}

    def _run_iops_test(self):
        import os, random, time, tempfile
        block_size = 4096
        num_blocks = 1024  # 4 MB total
        results = {"iops": 0, "error": None}
        tmp_path = None
        try:
            tmp_dir = os.path.expanduser("~")
            tmp_path = os.path.join(tmp_dir, "_tecoqc_iops_test.tmp")
            data = os.urandom(block_size * num_blocks)
            with open(tmp_path, "wb") as f:
                f.write(data)
            rng = random.Random(12345)
            offsets = [rng.randint(0, num_blocks - 1) * block_size
                       for _ in range(num_blocks)]
            t0 = time.time()
            with open(tmp_path, "rb") as f:
                for offset in offsets:
                    f.seek(offset)
                    f.read(block_size)
            elapsed = time.time() - t0
            results["iops"] = round(num_blocks / elapsed) if elapsed > 0 else 0
        except Exception as e:
            results["error"] = str(e)
        finally:
            if tmp_path and os.path.exists(tmp_path):
                try:
                    os.remove(tmp_path)
                except Exception:
                    pass
        return results

    def _show_speed(self, result):
        self._speed_btn.configure(state=tk.NORMAL)
        seq = result.get("sequential", {})
        iops_data = result.get("iops", {})

        if seq.get("error"):
            self._speed_lbl.configure(text=f"✗ Error: {seq['error']}", fg=theme.ERROR)
            return

        wr = seq.get("write_mb_s", 0)
        rd = seq.get("read_mb_s", 0)
        iops = iops_data.get("iops", 0)

        dtype = self._disk_type_var.get()
        threshold = DISK_SPEED_HDD_MIN_MB_S if dtype == "HDD" else DISK_SPEED_SSD_MIN_MB_S

        speed_ok = wr >= threshold
        iops_ok = iops >= DISK_IOPS_4K_MIN if iops > 0 else True  # skip if iops test failed

        speed_fg = theme.SUCCESS if speed_ok else theme.WARNING
        iops_fg = theme.SUCCESS if iops_ok else theme.WARNING

        self._speed_lbl.configure(
            text=f"{'✓' if speed_ok else '⚠'} Escritura: {wr:.1f} MB/s  |  Lectura: {rd:.1f} MB/s  "
                 f"(umbral {dtype}: {threshold} MB/s)",
            fg=speed_fg)

        if iops > 0:
            self._iops_lbl.configure(
                text=f"{'✓' if iops_ok else '⚠'} E/S aleatoria (4K): {iops:,} IOPS  "
                     f"(umbral: {DISK_IOPS_4K_MIN:,} IOPS)",
                fg=iops_fg)

        self._set_detail(f"Write: {wr:.1f} MB/s | Read: {rd:.1f} MB/s | {iops:,} IOPS")

        if speed_ok and iops_ok:
            self.set_status(STATUS_PASSED,
                             f"{dtype}: {wr:.1f} MB/s wr | {iops:,} IOPS")
        else:
            issues = []
            if not speed_ok:
                issues.append(f"velocidad {wr:.1f} MB/s < {threshold} MB/s")
            if not iops_ok and iops > 0:
                issues.append(f"IOPS {iops:,} < {DISK_IOPS_4K_MIN:,}")
            self.set_status(STATUS_FAILED, " | ".join(issues))

    def _speed_error(self, error):
        self._speed_btn.configure(state=tk.NORMAL)
        self._speed_lbl.configure(text=f"Error: {error}", fg=theme.ERROR)

    def _show_error(self, error):
        self._spinner.stop(f"Error: {error}")
        self.set_status(STATUS_FAILED, str(error))
