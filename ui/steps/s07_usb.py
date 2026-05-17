"""
TecoQC - Paso 7: Prueba de puertos USB
"""

import tkinter as tk
from ui.steps.base_step import BaseStep
from ui.components import Card, Spinner
from ui import theme
from config import STATUS_PASSED, STATUS_FAILED


class Step(BaseStep):
    TITLE = "Prueba de Puertos USB"
    DESCRIPTION = ("Conecte un dispositivo USB en cada puerto del equipo. "
                   "La lista se actualizará automáticamente. "
                   "Marque cada puerto como aprobado o fallido.")
    STEP_NUM = 7

    def build_ui(self, parent):
        self._port_status = {}

        # Instructions
        instr = tk.Frame(parent, bg=theme.BG_SURFACE0,
                          highlightthickness=1, highlightbackground=theme.ACCENT_BLUE)
        instr.pack(fill=tk.X, pady=(0, 12))
        tk.Label(
            instr,
            text="💡  Conecte un dispositivo USB (memoria, ratón, etc.) en cada puerto.\n"
                 "     Haga clic en 'Actualizar lista' para detectar los dispositivos conectados.",
            bg=theme.BG_SURFACE0, fg=theme.ACCENT_BLUE,
            font=theme.FONT_BODY, pady=10, padx=14, justify="left",
        ).pack(anchor="w")

        # Toolbar
        toolbar = tk.Frame(parent, bg=theme.BG_BASE)
        toolbar.pack(fill=tk.X, pady=(0, 10))

        tk.Button(
            toolbar, text="🔄  Actualizar lista de dispositivos USB",
            command=self._refresh, **theme.BTN_PRIMARY,
        ).pack(side=tk.LEFT, padx=(0, 10))

        self._spinner = Spinner(toolbar, text="Escaneando...", bg=theme.BG_BASE)
        self._spinner.pack(side=tk.LEFT)
        self._spinner.configure(fg=theme.BG_BASE)  # hidden initially

        self._device_count_lbl = tk.Label(
            toolbar, text="",
            bg=theme.BG_BASE, fg=theme.TEXT_SECONDARY, font=theme.FONT_BODY,
        )
        self._device_count_lbl.pack(side=tk.RIGHT)

        # Device list area
        list_wrapper = tk.Frame(parent, bg=theme.BG_SURFACE0,
                                 highlightthickness=1,
                                 highlightbackground=theme.BG_SURFACE1)
        list_wrapper.pack(fill=tk.BOTH, expand=True)

        # Header
        header = tk.Frame(list_wrapper, bg=theme.BG_SURFACE1)
        header.pack(fill=tk.X)
        cols = [("Dispositivo", 0.4), ("Fabricante", 0.25),
                ("Tipo", 0.15), ("Estado", 0.1), ("Acción", 0.1)]
        for label, weight in cols:
            tk.Label(header, text=label, bg=theme.BG_SURFACE1,
                     fg=theme.TEXT_SECONDARY, font=theme.FONT_SMALL,
                     padx=10, pady=6, anchor="w").pack(side=tk.LEFT, fill=tk.X,
                                                       expand=True)

        # Scrollable device list
        from ui.components import ScrollableFrame
        self._list_scroll = ScrollableFrame(list_wrapper, bg=theme.BG_SURFACE0)
        self._list_scroll.pack(fill=tk.BOTH, expand=True)
        self._list_container = self._list_scroll.inner

        # Port test section
        port_section = tk.Frame(parent, bg=theme.BG_BASE)
        port_section.pack(fill=tk.X, pady=(12, 0))

        tk.Label(port_section, text="Registro de prueba de puertos físicos:",
                 bg=theme.BG_BASE, fg=theme.TEXT_PRIMARY,
                 font=theme.FONT_H3).pack(anchor="w", pady=(0, 8))

        self._port_cards_frame = tk.Frame(port_section, bg=theme.BG_BASE)
        self._port_cards_frame.pack(fill=tk.X)

        # Create default port slots
        self._build_port_slots()

        # Initial scan
        self._refresh()

    def _build_port_slots(self, count=6):
        for widget in self._port_cards_frame.winfo_children():
            widget.destroy()

        port_types = ["USB 3.0", "USB 3.0", "USB 2.0", "USB 2.0", "USB-C", "USB-C"]
        self._port_widgets = {}

        for i in range(count):
            label = f"Puerto {i+1}"
            ptype = port_types[i] if i < len(port_types) else "USB"
            self._port_status[label] = "pending"

            card = tk.Frame(self._port_cards_frame, bg=theme.BG_SURFACE0,
                             highlightthickness=1, highlightbackground=theme.BG_SURFACE1)
            card.grid(row=0, column=i, padx=4, pady=0, sticky="nsew")
            self._port_cards_frame.columnconfigure(i, weight=1)

            inner = tk.Frame(card, bg=theme.BG_SURFACE0)
            inner.pack(fill=tk.X, padx=8, pady=6)

            tk.Label(inner, text=label, bg=theme.BG_SURFACE0,
                     fg=theme.TEXT_PRIMARY, font=theme.FONT_BODY_BOLD).pack()
            tk.Label(inner, text=ptype, bg=theme.BG_SURFACE0,
                     fg=theme.TEXT_MUTED, font=theme.FONT_SMALL).pack()

            status_lbl = tk.Label(inner, text="●",
                                   bg=theme.BG_SURFACE0,
                                   fg=theme.TEXT_MUTED, font=theme.FONT_H3)
            status_lbl.pack(pady=4)

            btn_row = tk.Frame(inner, bg=theme.BG_SURFACE0)
            btn_row.pack()

            tk.Button(btn_row, text="✓",
                       command=lambda lbl=label, sl=status_lbl: self._mark_port(lbl, "passed", sl),
                       bg=theme.SUCCESS, fg=theme.BG_BASE,
                       font=theme.FONT_BODY_BOLD, relief="flat",
                       cursor="hand2", padx=8, pady=4,
                       ).pack(side=tk.LEFT, padx=2)
            tk.Button(btn_row, text="✗",
                       command=lambda lbl=label, sl=status_lbl: self._mark_port(lbl, "failed", sl),
                       bg=theme.ERROR, fg=theme.BG_BASE,
                       font=theme.FONT_BODY_BOLD, relief="flat",
                       cursor="hand2", padx=8, pady=4,
                       ).pack(side=tk.LEFT, padx=2)

            self._port_widgets[label] = status_lbl

    def _mark_port(self, label, status, status_lbl):
        self._port_status[label] = status
        if status == "passed":
            status_lbl.configure(text="✓", fg=theme.SUCCESS)
        else:
            status_lbl.configure(text="✗", fg=theme.ERROR)
        self._check_overall()

    def _check_overall(self):
        statuses = list(self._port_status.values())
        if "failed" in statuses:
            self.set_status("failed", f"{statuses.count('failed')} puertos con fallo")
        elif all(s in ("passed", "skipped") for s in statuses):
            self.set_status(STATUS_PASSED,
                             f"{statuses.count('passed')} puertos aprobados")
        else:
            done = sum(1 for s in statuses if s != "pending")
            self._set_detail(f"{done}/{len(statuses)} puertos verificados")

    def _refresh(self):
        self._spinner.configure(fg=theme.ACCENT_BLUE)
        self._spinner.start()
        self.run_in_thread(self._get_usb_devices, on_done=self._show_devices,
                            on_error=self._show_error)

    def _get_usb_devices(self):
        devices = []
        try:
            import wmi
            c = wmi.WMI()
            usb_hubs = c.Win32_USBHub()
            for hub in usb_hubs:
                devices.append({
                    "name": (hub.Name or "USB Hub").strip(),
                    "manufacturer": (hub.Manufacturer or "").strip(),
                    "device_id": (hub.DeviceID or "").strip(),
                    "status": (hub.Status or "").strip(),
                    "type": "Hub USB",
                })
        except Exception:
            pass

        try:
            import wmi
            c = wmi.WMI()
            controllers = c.Win32_USBController()
            for ctrl in controllers:
                devices.append({
                    "name": (ctrl.Name or "Controlador USB").strip(),
                    "manufacturer": (ctrl.Manufacturer or "").strip(),
                    "device_id": (ctrl.DeviceID or "").strip(),
                    "status": (ctrl.Status or "").strip(),
                    "type": "Controlador",
                })
        except Exception:
            pass

        try:
            import wmi
            c = wmi.WMI()
            entities = c.Win32_PnPEntity()
            for e in entities:
                if e.PNPClass and e.PNPClass.upper() in ("USB", "HIDCLASS"):
                    devices.append({
                        "name": (e.Name or "Dispositivo USB").strip(),
                        "manufacturer": (e.Manufacturer or "").strip(),
                        "device_id": (e.DeviceID or "")[:50],
                        "status": (e.Status or "").strip(),
                        "type": e.PNPClass or "USB",
                    })
        except Exception:
            pass

        return devices

    def _show_devices(self, devices):
        self._spinner.stop()
        self._spinner.configure(fg=theme.BG_BASE)

        for widget in self._list_container.winfo_children():
            widget.destroy()

        if not devices:
            tk.Label(self._list_container,
                     text="No se detectaron dispositivos USB. Conecte un dispositivo.",
                     bg=theme.BG_SURFACE0, fg=theme.WARNING,
                     font=theme.FONT_BODY, pady=16).pack()
        else:
            for i, dev in enumerate(devices):
                bg = theme.BG_SURFACE0 if i % 2 == 0 else theme.BG_MANTLE
                row = tk.Frame(self._list_container, bg=bg)
                row.pack(fill=tk.X)

                fields = [
                    (dev.get("name", "N/D")[:50], 0.4),
                    (dev.get("manufacturer", "N/D")[:30], 0.25),
                    (dev.get("type", "N/D"), 0.15),
                    (dev.get("status", "N/D"), 0.1),
                ]
                for text, _ in fields:
                    tk.Label(row, text=text, bg=bg, fg=theme.TEXT_SECONDARY,
                             font=theme.FONT_SMALL, padx=10, pady=5,
                             anchor="w").pack(side=tk.LEFT, fill=tk.X, expand=True)

        self._device_count_lbl.configure(
            text=f"Total dispositivos: {len(devices)}"
        )

    def _show_error(self, error):
        self._spinner.stop()
        self._spinner.configure(fg=theme.BG_BASE)
        for widget in self._list_container.winfo_children():
            widget.destroy()
        tk.Label(self._list_container,
                 text=f"Error al escanear USB: {error}",
                 bg=theme.BG_SURFACE0, fg=theme.ERROR,
                 font=theme.FONT_BODY, pady=16).pack()
