"""
TecoQC - Paso 2: Información del sistema (recopilación automática)
"""

import tkinter as tk
import threading

from ui.steps.base_step import BaseStep
from ui.components import Card, InfoRow, Spinner
from ui import theme
from config import STATUS_PASSED, STATUS_FAILED


class Step(BaseStep):
    TITLE = "Información del Sistema"
    DESCRIPTION = "Recopilación automática de información del hardware y sistema operativo."
    STEP_NUM = 2

    def build_ui(self, parent):
        self._parent = parent

        self._spinner = Spinner(parent, text="Recopilando información del sistema...",
                                 bg=theme.BG_BASE)
        self._spinner.pack(pady=40)

        self._cards_frame = tk.Frame(parent, bg=theme.BG_BASE)
        self._cards_frame.pack(fill=tk.BOTH, expand=True)

    def on_enter(self):
        self._spinner.start()
        self.run_in_thread(self._collect, on_done=self._show_info,
                            on_error=self._show_error)

    def _collect(self):
        import platform
        info = {"os": {}, "motherboard": {}, "bios": {}, "cpu": {}, "memory": {}, "gpu": [],
                "secure_boot": None, "tpm": {}}
        try:
            from hardware.system_info import get_all_system_info
            sys_data = get_all_system_info()
            info.update(sys_data)
        except Exception:
            pass
        try:
            from hardware.cpu import get_cpu_info
            info["cpu"] = get_cpu_info()
        except Exception:
            pass
        try:
            from hardware.memory import get_memory_info
            info["memory"] = get_memory_info()
        except Exception:
            pass
        try:
            from hardware.gpu import get_wmi_gpu_info
            info["gpu"] = get_wmi_gpu_info()
        except Exception:
            pass

        # Secure Boot via registry
        try:
            import subprocess
            result = subprocess.run(
                ["reg", "query",
                 r"HKLM\SYSTEM\CurrentControlSet\Control\SecureBoot\State",
                 "/v", "UEFISecureBootEnabled"],
                capture_output=True, text=True, timeout=5
            )
            if "0x1" in result.stdout:
                info["secure_boot"] = True
            elif "0x0" in result.stdout:
                info["secure_boot"] = False
        except Exception:
            pass

        # TPM via WMI
        try:
            import wmi
            c = wmi.WMI(namespace=r"root\CIMv2\Security\MicrosoftTpm")
            tpms = c.Win32_Tpm()
            if tpms:
                t = tpms[0]
                info["tpm"] = {
                    "present": True,
                    "activated": bool(getattr(t, "IsActivated_InitialValue", False)),
                    "enabled": bool(getattr(t, "IsEnabled_InitialValue", False)),
                    "spec_version": getattr(t, "SpecVersion", "N/D") or "N/D",
                }
            else:
                info["tpm"] = {"present": False}
        except Exception:
            info["tpm"] = {"present": None}

        info.setdefault("os", {})
        info["os"].setdefault("os_full", f"{platform.system()} {platform.release()}")
        info["os"].setdefault("architecture", platform.machine())
        info["os"].setdefault("hostname", platform.node())
        return info

    def _show_info(self, info):
        self._spinner.stop()
        self._spinner.pack_forget()

        self._state["system_info"] = info

        os_data = info.get("os", {})
        mb_data = info.get("motherboard", {})
        bios_data = info.get("bios", {})
        cpu_data = info.get("cpu", {})
        mem_data = info.get("memory", {})
        gpu_list = info.get("gpu", [])
        secure_boot = info.get("secure_boot")
        tpm = info.get("tpm", {})

        grid = tk.Frame(self._cards_frame, bg=theme.BG_BASE)
        grid.pack(fill=tk.BOTH, expand=True)
        grid.columnconfigure(0, weight=1)
        grid.columnconfigure(1, weight=1)

        # OS Card
        sb_text = ("Activo ✓" if secure_boot is True
                   else "Inactivo ⚠" if secure_boot is False
                   else "N/D")
        sb_color = theme.SUCCESS if secure_boot else theme.WARNING if secure_boot is False else theme.TEXT_MUTED
        self._make_card(grid, "Sistema Operativo", [
            ("OS", os_data.get("product_name", os_data.get("os_full", "N/D"))),
            ("Versión", str(os_data.get("os_version", "N/D"))[:60]),
            ("Edición", os_data.get("os_edition", "N/D")),
            ("Build", os_data.get("build_number", "N/D")),
            ("Arquitectura", os_data.get("architecture", "N/D")),
            ("Hostname", os_data.get("hostname", "N/D")),
        ], row=0, col=0)

        # Motherboard / Hardware card with Secure Boot + TPM
        tpm_present = tpm.get("present")
        tpm_ver = tpm.get("spec_version", "N/D")
        tpm_text = (f"TPM {tpm_ver} ✓" if tpm_present
                    else "No detectado ⚠" if tpm_present is False
                    else "N/D")
        bios_serial = bios_data.get("serial_number", "N/D") or "N/D"
        self._make_card(grid, "Placa Base y Seguridad", [
            ("Fabricante", mb_data.get("make", mb_data.get("manufacturer", "N/D"))),
            ("Modelo", mb_data.get("model", mb_data.get("product", "N/D"))),
            ("S/N Placa", mb_data.get("serial", "N/D")),
            ("BIOS S/N", bios_serial),
            ("BIOS Versión", bios_data.get("version", "N/D")),
            ("Secure Boot", sb_text),
            ("TPM", tpm_text),
        ], row=0, col=1)

        # CPU Card
        freq_max = cpu_data.get("freq_max_mhz", 0)
        freq_str = f"{freq_max:.0f} MHz" if freq_max else "N/D"
        self._make_card(grid, "Procesador (CPU)", [
            ("Nombre", cpu_data.get("name", "N/D")),
            ("Fabricante", cpu_data.get("manufacturer", "N/D")),
            ("Núcleos físicos", str(cpu_data.get("cores_physical", "N/D"))),
            ("Núcleos lógicos", str(cpu_data.get("cores_logical", "N/D"))),
            ("Vel. máxima", freq_str),
            ("Socket", cpu_data.get("socket", "N/D")),
        ], row=1, col=0)

        # RAM Card
        self._make_card(grid, "Memoria RAM", [
            ("Total", f"{mem_data.get('total_gb', 0):.2f} GB"),
            ("Disponible", f"{mem_data.get('available_gb', 0):.2f} GB"),
            ("En uso", f"{mem_data.get('used_gb', 0):.2f} GB"),
            ("Uso", f"{mem_data.get('percent', 0):.1f}%"),
        ], row=1, col=1)

        # GPU Card
        gpu_rows = []
        if gpu_list:
            for i, g in enumerate(gpu_list[:2]):
                prefix = f"GPU {i+1}" if len(gpu_list) > 1 else ""
                n = g.get("name", "N/D")
                gpu_rows.append((f"{prefix} Nombre".strip(), n))
                vram = g.get("vram_total_mb", 0)
                gpu_rows.append((f"{prefix} VRAM".strip(),
                                  f"{vram} MB" if vram else "N/D"))
                gpu_rows.append((f"{prefix} Driver".strip(),
                                  g.get("driver_version", "N/D")))
        else:
            gpu_rows = [("Estado", "No detectada")]

        self._make_card(grid, "Tarjeta Gráfica (GPU)", gpu_rows, row=2, col=0)

        # Peripherals card (placeholder — filled by background thread)
        periph_card = Card(grid)
        periph_card.grid(row=2, column=1, padx=6, pady=6, sticky="nsew")

        tk.Label(periph_card, text="Periféricos Especiales",
                 bg=theme.BG_SURFACE0, fg=theme.ACCENT_BLUE,
                 font=theme.FONT_H3).pack(anchor="w", padx=16, pady=(12, 6))
        tk.Frame(periph_card, height=1, bg=theme.BG_SURFACE2).pack(fill=tk.X, padx=16)

        self._periph_spinner = Spinner(periph_card, text="Detectando periféricos...",
                                        bg=theme.BG_SURFACE0)
        self._periph_spinner.pack(padx=16, pady=8)
        self._periph_spinner.start()

        self._periph_frame = tk.Frame(periph_card, bg=theme.BG_SURFACE0)
        self._periph_frame.pack(fill=tk.X, padx=16, pady=(0, 10))

        self.run_in_thread(self._check_peripherals, on_done=self._show_peripherals,
                            on_error=self._periph_error)

        # Cross-check serial number vs. Step 1 input
        cross_card = Card(self._cards_frame)
        cross_card.pack(fill=tk.X, pady=(12, 0))
        inner = tk.Frame(cross_card, bg=theme.BG_SURFACE0)
        inner.pack(fill=tk.X, padx=16, pady=10)

        entered_serial = self._state.get("device_serial", "")
        bios_sn = bios_serial.strip()
        mb_sn = mb_data.get("serial", "").strip()

        if entered_serial:
            match = (entered_serial.lower() == bios_sn.lower() or
                     entered_serial.lower() == mb_sn.lower())
            if match:
                serial_txt = f"✓  S/N coincide con hardware: {entered_serial}"
                serial_fg = theme.SUCCESS
            else:
                serial_txt = (f"⚠  S/N ingresado '{entered_serial}' ≠ BIOS '{bios_sn}' "
                               f"— Verifique la etiqueta física")
                serial_fg = theme.WARNING
        else:
            serial_txt = "✓  Información del sistema recopilada correctamente."
            serial_fg = theme.SUCCESS

        tk.Label(inner, text=serial_txt,
                 bg=theme.BG_SURFACE0, fg=serial_fg,
                 font=theme.FONT_BODY_BOLD).pack(anchor="w")

        # Secure Boot / TPM warnings
        if secure_boot is False:
            tk.Label(inner,
                     text="⚠  Secure Boot desactivado — verificar configuración UEFI",
                     bg=theme.BG_SURFACE0, fg=theme.WARNING,
                     font=theme.FONT_SMALL).pack(anchor="w", pady=(4, 0))
        if tpm_present is False:
            tk.Label(inner,
                     text="⚠  TPM no detectado — puede ser requerido para Windows 11",
                     bg=theme.BG_SURFACE0, fg=theme.WARNING,
                     font=theme.FONT_SMALL).pack(anchor="w", pady=(2, 0))

        # Launch background checks for Event Log and Drivers
        self.run_in_thread(self._check_eventlog_drivers,
                            on_done=self._show_eventlog_drivers)

        self.set_status(STATUS_PASSED, "Sistema analizado")
        self._set_detail(
            f"{os_data.get('product_name', os_data.get('os_full', 'N/D'))} | "
            f"{cpu_data.get('name', 'CPU N/D')} | "
            f"{mem_data.get('total_gb', 0):.1f} GB RAM"
        )

    def _show_error(self, error):
        self._spinner.stop()
        self._spinner.configure(text=f"Error al recopilar información: {error}",
                                  fg=theme.ERROR)
        self.set_status(STATUS_FAILED, str(error))

    def _check_eventlog_drivers(self):
        from hardware.eventlog import scan_hardware_events, get_driver_errors_wmi
        events = scan_hardware_events(days=30)
        drivers = get_driver_errors_wmi()
        return {"events": events, "drivers": drivers}

    def _show_eventlog_drivers(self, data):
        events = data.get("events", {})
        drivers = data.get("drivers", [])
        summary = events.get("summary", {})
        total_issues = summary.get("total_issues", 0)
        driver_errors = [d for d in drivers if "error" not in d]

        # Find or create the diagnostic card
        diag_card = Card(self._cards_frame)
        diag_card.pack(fill=tk.X, pady=(8, 0))

        tk.Label(diag_card, text="Diagnóstico del Sistema",
                 bg=theme.BG_SURFACE0, fg=theme.ACCENT_BLUE,
                 font=theme.FONT_H3).pack(anchor="w", padx=16, pady=(12, 6))
        tk.Frame(diag_card, height=1, bg=theme.BG_SURFACE2).pack(fill=tk.X, padx=16)

        inner = tk.Frame(diag_card, bg=theme.BG_SURFACE0)
        inner.pack(fill=tk.X, padx=16, pady=10)

        # Event log summary
        if total_issues == 0:
            tk.Label(inner,
                     text=f"✓ Event Log: sin errores de hardware en los últimos 30 días",
                     bg=theme.BG_SURFACE0, fg=theme.SUCCESS,
                     font=theme.FONT_BODY).pack(anchor="w")
        else:
            disk_c   = summary.get("disk_error_count", 0)
            mem_c    = summary.get("memory_error_count", 0)
            drv_c    = summary.get("driver_error_count", 0)
            crit_c   = summary.get("critical_error_count", 0)
            msg = f"⚠ Event Log ({summary.get('days_scanned', 30)} días): "
            parts = []
            if disk_c:   parts.append(f"{disk_c} errores de disco")
            if mem_c:    parts.append(f"{mem_c} errores de memoria")
            if drv_c:    parts.append(f"{drv_c} errores de driver")
            if crit_c:   parts.append(f"{crit_c} críticos")
            tk.Label(inner,
                     text=msg + " | ".join(parts),
                     bg=theme.BG_SURFACE0, fg=theme.WARNING,
                     font=theme.FONT_BODY).pack(anchor="w")

            # Show first few events
            all_ev = (events.get("disk_errors", []) +
                      events.get("memory_errors", []) +
                      events.get("driver_errors", []) +
                      events.get("critical_errors", []))
            for ev in all_ev[:3]:
                msg_short = ev.get("message", "")[:80]
                t = ev.get("time", "")[:16]
                tk.Label(inner,
                         text=f"  [{t}] {msg_short}",
                         bg=theme.BG_SURFACE0, fg=theme.TEXT_MUTED,
                         font=theme.FONT_SMALL).pack(anchor="w")

        # Driver errors
        if not driver_errors:
            tk.Label(inner,
                     text="✓ Controladores: todos los dispositivos funcionan correctamente",
                     bg=theme.BG_SURFACE0, fg=theme.SUCCESS,
                     font=theme.FONT_BODY).pack(anchor="w", pady=(4, 0))
        else:
            tk.Label(inner,
                     text=f"⚠ Controladores con error: {len(driver_errors)} dispositivo(s)",
                     bg=theme.BG_SURFACE0, fg=theme.ERROR,
                     font=theme.FONT_BODY).pack(anchor="w", pady=(4, 0))
            for d in driver_errors[:4]:
                tk.Label(inner,
                         text=f"  ✗ {d.get('name', '?')[:45]} — {d.get('description', '')[:50]}",
                         bg=theme.BG_SURFACE0, fg=theme.WARNING,
                         font=theme.FONT_SMALL).pack(anchor="w")

        # Update step status if issues found
        if total_issues > 0 or driver_errors:
            issue_count = total_issues + len(driver_errors)
            self._state.setdefault("system_issues", [])
            if total_issues:
                self._state["system_issues"].append(f"{total_issues} errores en Event Log")
            if driver_errors:
                self._state["system_issues"].append(f"{len(driver_errors)} drivers con error")

    def _check_peripherals(self):
        from hardware.peripherals import get_all_peripherals
        return get_all_peripherals()

    def _show_peripherals(self, data):
        self._periph_spinner.stop()
        self._periph_spinner.pack_forget()

        for w in self._periph_frame.winfo_children():
            w.destroy()

        sd = data.get("sd_reader", {})
        touch = data.get("touchscreen", {})
        fp = data.get("fingerprint", {})
        ir = data.get("ir_camera", {})

        def _periph_row(parent, label, found, name=""):
            row = tk.Frame(parent, bg=theme.BG_SURFACE0)
            row.pack(fill=tk.X, pady=2)
            icon = "✓" if found else "✗"
            fg = theme.SUCCESS if found else theme.TEXT_MUTED
            tk.Label(row, text=label + ":", bg=theme.BG_SURFACE0,
                     fg=theme.TEXT_SECONDARY, font=theme.FONT_BODY,
                     width=18, anchor="w").pack(side=tk.LEFT)
            display = f"{icon}  {name}" if (found and name) else icon
            tk.Label(row, text=display, bg=theme.BG_SURFACE0,
                     fg=fg, font=theme.FONT_BODY_BOLD,
                     anchor="w").pack(side=tk.LEFT, fill=tk.X, expand=True)

        _periph_row(self._periph_frame, "Lector SD",
                    sd.get("found", False), sd.get("name", ""))

        touch_found = touch.get("found", False)
        touch_name = touch.get("devices", [""])[0] if touch_found else ""
        _periph_row(self._periph_frame, "Pantalla táctil",
                    touch_found, touch_name)

        _periph_row(self._periph_frame, "Lector de huellas",
                    fp.get("found", False), fp.get("name", ""))

        _periph_row(self._periph_frame, "Cámara IR",
                    ir.get("found", False), ir.get("name", ""))

    def _periph_error(self, error):
        try:
            self._periph_spinner.stop()
            self._periph_spinner.pack_forget()
            tk.Label(self._periph_frame,
                     text=f"Error al detectar periféricos: {error}",
                     bg=theme.BG_SURFACE0, fg=theme.WARNING,
                     font=theme.FONT_SMALL).pack(anchor="w")
        except Exception:
            pass

    def _make_card(self, grid, title, rows, row, col):
        card = Card(grid)
        card.grid(row=row, column=col, padx=6, pady=6, sticky="nsew")

        tk.Label(card, text=title,
                 bg=theme.BG_SURFACE0,
                 fg=theme.ACCENT_BLUE,
                 font=theme.FONT_H3).pack(anchor="w", padx=16, pady=(12, 6))

        sep = tk.Frame(card, height=1, bg=theme.BG_SURFACE2)
        sep.pack(fill=tk.X, padx=16)

        for label, value in rows:
            InfoRow(card, label=label, value=str(value),
                    label_width=18, bg=theme.BG_SURFACE0).pack(
                fill=tk.X, padx=16, pady=3
            )

        tk.Frame(card, height=8, bg=theme.BG_SURFACE0).pack()
