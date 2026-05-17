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
