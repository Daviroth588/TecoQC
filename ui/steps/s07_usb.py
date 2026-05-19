"""
TecoQC - Paso 7: Prueba de puertos USB con hot-plug automático
"""

import tkinter as tk
import threading
import time
from ui.steps.base_step import BaseStep
from ui.components import Card, Spinner
from ui import theme
from config import STATUS_PASSED, STATUS_FAILED


class Step(BaseStep):
    TITLE = "Prueba de Puertos USB"
    DESCRIPTION = ("Conecte un dispositivo USB en cada puerto del equipo. "
                   "La detección es automática al conectar un dispositivo.")
    STEP_NUM = 7

    def build_ui(self, parent):
        self._port_status = {}
        self._hotplug_active = False
        self._last_device_set = set()
        self._baseline_captured = False
        self._new_device_count = 0

        # Instructions
        instr = tk.Frame(parent, bg=theme.BG_SURFACE0,
                          highlightthickness=1, highlightbackground=theme.ACCENT_BLUE)
        instr.pack(fill=tk.X, pady=(0, 12))
        tk.Label(
            instr,
            text="💡 Conecte un dispositivo USB en cada puerto. "
                 "Los nuevos dispositivos aparecerán destacados en verde.",
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

        self._hotplug_lbl = tk.Label(
            toolbar, text="● Monitoreo automático activo",
            bg=theme.BG_BASE, fg=theme.SUCCESS, font=theme.FONT_SMALL)
        self._hotplug_lbl.pack(side=tk.LEFT, padx=8)

        self._spinner = Spinner(toolbar, text="Escaneando...", bg=theme.BG_BASE)
        self._spinner.pack(side=tk.LEFT)
        self._spinner.configure(fg=theme.BG_BASE)

        self._new_device_count_lbl = tk.Label(
            toolbar, text="Nuevos dispositivos: 0",
            bg=theme.BG_BASE, fg=theme.SUCCESS, font=theme.FONT_BODY,
        )
        self._new_device_count_lbl.pack(side=tk.RIGHT, padx=(8, 0))

        self._device_count_lbl = tk.Label(
            toolbar, text="",
            bg=theme.BG_BASE, fg=theme.TEXT_SECONDARY, font=theme.FONT_BODY,
        )
        self._device_count_lbl.pack(side=tk.RIGHT)

        # ── Infrastructure section (collapsible) ──
        infra_wrapper = tk.Frame(parent, bg=theme.BG_SURFACE0,
                                  highlightthickness=1,
                                  highlightbackground=theme.BG_SURFACE1)
        infra_wrapper.pack(fill=tk.X, pady=(0, 6))

        self._infra_visible = tk.BooleanVar(value=False)

        infra_header = tk.Frame(infra_wrapper, bg=theme.BG_SURFACE2, cursor="hand2")
        infra_header.pack(fill=tk.X)

        self._infra_toggle_lbl = tk.Label(
            infra_header, text="▶ Controladores e Infraestructura USB (click para expandir)",
            bg=theme.BG_SURFACE2, fg=theme.TEXT_MUTED,
            font=theme.FONT_SMALL, padx=10, pady=5, anchor="w")
        self._infra_toggle_lbl.pack(side=tk.LEFT)
        infra_header.bind("<Button-1>", lambda e: self._toggle_infra())
        self._infra_toggle_lbl.bind("<Button-1>", lambda e: self._toggle_infra())

        self._infra_container = tk.Frame(infra_wrapper, bg=theme.BG_MANTLE)
        # collapsed by default — only shown after toggle

        # ── Connected devices section (PnP USB/HID — hot-plug relevant) ──
        list_wrapper = tk.Frame(parent, bg=theme.BG_SURFACE0,
                                 highlightthickness=1,
                                 highlightbackground=theme.BG_SURFACE1)
        list_wrapper.pack(fill=tk.BOTH, expand=True)

        header = tk.Frame(list_wrapper, bg=theme.BG_SURFACE1)
        header.pack(fill=tk.X)
        tk.Label(header, text="Dispositivos conectados",
                 bg=theme.BG_SURFACE1, fg=theme.TEXT_PRIMARY,
                 font=theme.FONT_SMALL, padx=10, pady=5, anchor="w").pack(side=tk.LEFT)

        col_header = tk.Frame(list_wrapper, bg=theme.BG_SURFACE1)
        col_header.pack(fill=tk.X)
        cols = [("Dispositivo", 0.4), ("Fabricante", 0.25),
                ("Tipo", 0.15), ("Estado", 0.1), ("Detección", 0.1)]
        for label, weight in cols:
            tk.Label(col_header, text=label, bg=theme.BG_SURFACE1,
                     fg=theme.TEXT_SECONDARY, font=theme.FONT_SMALL,
                     padx=10, pady=4, anchor="w").pack(side=tk.LEFT, fill=tk.X, expand=True)

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

        self._build_port_slots()
        self._refresh()

    def _toggle_infra(self):
        if self._infra_visible.get():
            self._infra_container.pack_forget()
            self._infra_visible.set(False)
            self._infra_toggle_lbl.configure(
                text="▶ Controladores e Infraestructura USB (click para expandir)")
        else:
            self._infra_container.pack(fill=tk.X)
            self._infra_visible.set(True)
            self._infra_toggle_lbl.configure(
                text="▼ Controladores e Infraestructura USB (click para colapsar)")

    def on_enter(self):
        self._hotplug_active = True
        # Ensure baseline is captured before hotplug loop starts
        if not self._baseline_captured:
            baseline = self._get_device_names()
            self._last_device_set = baseline
            self._baseline_captured = True
        threading.Thread(target=self._hotplug_loop, daemon=True).start()

    def on_leave(self):
        super().on_leave()
        self._hotplug_active = False

    def _hotplug_loop(self):
        """Poll for new USB devices every 2 seconds and auto-detect connections."""
        while self._hotplug_active:
            try:
                current_devices = self._get_device_names()
                new_devices = current_devices - self._last_device_set
                removed_devices = self._last_device_set - current_devices

                if new_devices or removed_devices:
                    self._last_device_set = current_devices
                    self.after(0, self._refresh)
                    if new_devices:
                        for name in new_devices:
                            self.after(0, lambda n=name: self._on_new_device(n))
            except Exception:
                pass
            time.sleep(2)

    def _get_device_names(self):
        """Return names of external USB/HID PnP devices only (baseline for hot-plug)."""
        names = set()
        try:
            import wmi
            c = wmi.WMI()
            for e in c.Win32_PnPEntity():
                if e.PNPClass and e.PNPClass.upper() in ("USB", "HIDCLASS"):
                    if e.Name:
                        names.add(e.Name)
        except Exception:
            pass
        return names

    def _on_new_device(self, device_name):
        """Auto-mark next pending port and highlight device when a new device is detected."""
        self._new_device_count += 1
        try:
            self._new_device_count_lbl.configure(
                text=f"Nuevos dispositivos: {self._new_device_count}")
        except Exception:
            pass

        # Highlight the new device row in the list container (green background)
        try:
            row = tk.Frame(self._list_container, bg="#1e4620")
            row.pack(fill=tk.X)

            timestamp = time.strftime("%H:%M:%S")
            fields = [
                (device_name[:50], 0.4),
                ("", 0.25),
                ("USB", 0.15),
                ("OK", 0.1),
                (timestamp, 0.1),
            ]
            for text, _ in fields:
                tk.Label(row, text=text, bg="#1e4620", fg="#a6e3a1",
                         font=theme.FONT_SMALL, padx=10, pady=5,
                         anchor="w").pack(side=tk.LEFT, fill=tk.X, expand=True)
        except Exception:
            pass

        # Auto-mark next pending port
        for label, status in sorted(self._port_status.items()):
            if status == "pending":
                sw = self._port_widgets.get(label)
                if sw:
                    self._mark_port(label, "passed", sw, auto=True,
                                    device=device_name[:25])
                break

    def _build_port_slots(self, count=6):
        for widget in self._port_cards_frame.winfo_children():
            widget.destroy()

        port_types = ["USB 3.0", "USB 3.0", "USB 2.0", "USB 2.0", "USB-C", "USB-C"]
        self._port_widgets = {}
        self._port_device_labels = {}

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

            dev_lbl = tk.Label(inner, text="",
                                bg=theme.BG_SURFACE0, fg=theme.TEXT_MUTED,
                                font=(theme.FONT_FAMILY, 7), wraplength=80)
            dev_lbl.pack()
            self._port_device_labels[label] = dev_lbl

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

    def _mark_port(self, label, status, status_lbl, auto=False, device=""):
        self._port_status[label] = status
        if status == "passed":
            status_lbl.configure(text="✓", fg=theme.SUCCESS)
            if auto and device:
                dev_lbl = self._port_device_labels.get(label)
                if dev_lbl:
                    dev_lbl.configure(text=device, fg=theme.TEXT_MUTED)
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
        """
        Returns dict with two lists:
          'infra'    — Win32_USBHub + Win32_USBController (internal, not hot-plug relevant)
          'external' — Win32_PnPEntity USB/HIDCLASS (what technician plugs in)
        """
        infra = []
        external = []
        seen_infra = set()
        seen_ext = set()

        try:
            import wmi
            c = wmi.WMI()

            for hub in c.Win32_USBHub():
                name = (hub.Name or "USB Hub").strip()
                if name not in seen_infra:
                    seen_infra.add(name)
                    infra.append({
                        "name": name,
                        "manufacturer": (hub.Manufacturer or "").strip(),
                        "device_id": (hub.DeviceID or "").strip(),
                        "status": (hub.Status or "").strip(),
                        "type": "Hub USB",
                    })

            for ctrl in c.Win32_USBController():
                name = (ctrl.Name or "Controlador USB").strip()
                if name not in seen_infra:
                    seen_infra.add(name)
                    infra.append({
                        "name": name,
                        "manufacturer": (ctrl.Manufacturer or "").strip(),
                        "device_id": (ctrl.DeviceID or "").strip(),
                        "status": (ctrl.Status or "").strip(),
                        "type": "Controlador",
                    })

            for e in c.Win32_PnPEntity():
                if e.PNPClass and e.PNPClass.upper() in ("USB", "HIDCLASS"):
                    name = (e.Name or "Dispositivo USB").strip()
                    if name not in seen_ext:
                        seen_ext.add(name)
                        external.append({
                            "name": name,
                            "manufacturer": (e.Manufacturer or "").strip(),
                            "device_id": (e.DeviceID or "")[:50],
                            "status": (e.Status or "").strip(),
                            "type": e.PNPClass or "USB",
                        })
        except Exception:
            pass

        # Capture baseline from external devices only (first time)
        if not self._baseline_captured:
            self._last_device_set = {d["name"] for d in external}
            self._baseline_captured = True

        return {"infra": infra, "external": external}

    def _show_devices(self, devices):
        self._spinner.stop()
        self._spinner.configure(fg=theme.BG_BASE)

        infra = devices.get("infra", [])
        external = devices.get("external", [])

        # ── Infrastructure section ────────────────────────────────────────
        for widget in self._infra_container.winfo_children():
            widget.destroy()

        if infra:
            for i, dev in enumerate(infra):
                bg = theme.BG_MANTLE if i % 2 == 0 else theme.BG_SURFACE1
                row = tk.Frame(self._infra_container, bg=bg)
                row.pack(fill=tk.X)
                fields = [
                    (dev.get("name", "N/D")[:50], 0.4),
                    (dev.get("manufacturer", "N/D")[:30], 0.25),
                    (dev.get("type", "N/D"), 0.15),
                    (dev.get("status", "N/D"), 0.1),
                ]
                for text, _ in fields:
                    tk.Label(row, text=text, bg=bg, fg=theme.TEXT_MUTED,
                             font=theme.FONT_SMALL, padx=10, pady=4,
                             anchor="w").pack(side=tk.LEFT, fill=tk.X, expand=True)
        else:
            tk.Label(self._infra_container,
                     text="No se detectaron controladores USB.",
                     bg=theme.BG_MANTLE, fg=theme.TEXT_MUTED,
                     font=theme.FONT_SMALL, pady=6, padx=10).pack(anchor="w")

        # ── External devices section ──────────────────────────────────────
        # Keep any green (new-device) rows already added by _on_new_device;
        # only rebuild non-highlighted rows.
        existing_new_rows = [
            w for w in self._list_container.winfo_children()
            if isinstance(w, tk.Frame) and w.cget("bg") == "#1e4620"
        ]
        for widget in self._list_container.winfo_children():
            if widget not in existing_new_rows:
                widget.destroy()

        # Get names already shown in green so we don't duplicate
        new_names = set()
        for row in existing_new_rows:
            children = row.winfo_children()
            if children:
                try:
                    new_names.add(children[0].cget("text"))
                except Exception:
                    pass

        # Show external devices not already highlighted
        shown = 0
        for i, dev in enumerate(external):
            name = dev.get("name", "N/D")[:50]
            if name in new_names:
                continue
            bg = theme.BG_SURFACE0 if shown % 2 == 0 else theme.BG_MANTLE
            row = tk.Frame(self._list_container, bg=bg)
            row.pack(fill=tk.X)
            fields = [
                (name, 0.4),
                (dev.get("manufacturer", "N/D")[:30], 0.25),
                (dev.get("type", "N/D"), 0.15),
                (dev.get("status", "N/D"), 0.1),
                ("", 0.1),
            ]
            for text, _ in fields:
                tk.Label(row, text=text, bg=bg, fg=theme.TEXT_SECONDARY,
                         font=theme.FONT_SMALL, padx=10, pady=5,
                         anchor="w").pack(side=tk.LEFT, fill=tk.X, expand=True)
            shown += 1

        if not external and not existing_new_rows:
            tk.Label(self._list_container,
                     text="No se detectaron dispositivos USB externos. Conecte un dispositivo.",
                     bg=theme.BG_SURFACE0, fg=theme.WARNING,
                     font=theme.FONT_BODY, pady=16).pack()

        self._device_count_lbl.configure(
            text=f"Infraestructura: {len(infra)}  |  Externos: {len(external)}   ")

    def _show_error(self, error):
        self._spinner.stop()
        self._spinner.configure(fg=theme.BG_BASE)
        for widget in self._list_container.winfo_children():
            widget.destroy()
        tk.Label(self._list_container,
                 text=f"Error al escanear USB: {error}",
                 bg=theme.BG_SURFACE0, fg=theme.ERROR,
                 font=theme.FONT_BODY, pady=16).pack()
