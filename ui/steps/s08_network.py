"""
TecoQC - Paso 8: Prueba de red (Ethernet + WiFi + Ping)
"""

import tkinter as tk
from ui.steps.base_step import BaseStep
from ui.components import Card, Spinner, InfoRow
from ui import theme
from config import STATUS_PASSED, STATUS_FAILED, PING_HOST


class Step(BaseStep):
    TITLE = "Prueba de Red"
    DESCRIPTION = "Verificación de adaptadores Ethernet, redes WiFi disponibles y conectividad."
    STEP_NUM = 8

    def build_ui(self, parent):
        # Two columns: Ethernet (left) + WiFi (right)
        cols = tk.Frame(parent, bg=theme.BG_BASE)
        cols.pack(fill=tk.BOTH, expand=True)
        cols.columnconfigure(0, weight=1)
        cols.columnconfigure(1, weight=1)

        # ── Ethernet panel ─────────────────────────────────────────────
        eth_card = Card(cols)
        eth_card.grid(row=0, column=0, padx=(0, 8), pady=(0, 8), sticky="nsew")

        tk.Label(eth_card, text="Ethernet",
                 bg=theme.BG_SURFACE0, fg=theme.ACCENT_BLUE,
                 font=theme.FONT_H3).pack(anchor="w", padx=16, pady=(12, 6))

        self._eth_spinner = Spinner(eth_card, text="Detectando...", bg=theme.BG_SURFACE0)
        self._eth_spinner.pack(padx=16, pady=8)

        self._eth_frame = tk.Frame(eth_card, bg=theme.BG_SURFACE0)
        self._eth_frame.pack(fill=tk.X, padx=16, pady=(0, 10))

        # ── WiFi panel ─────────────────────────────────────────────────
        wifi_card = Card(cols)
        wifi_card.grid(row=0, column=1, padx=(8, 0), pady=(0, 8), sticky="nsew")

        wifi_hdr = tk.Frame(wifi_card, bg=theme.BG_SURFACE0)
        wifi_hdr.pack(fill=tk.X, padx=16, pady=(12, 6))

        tk.Label(wifi_hdr, text="WiFi",
                 bg=theme.BG_SURFACE0, fg=theme.ACCENT_BLUE,
                 font=theme.FONT_H3).pack(side=tk.LEFT)

        tk.Button(wifi_hdr, text="🔄 Escanear",
                   command=self._scan_wifi, **theme.BTN_NEUTRAL).pack(side=tk.RIGHT)

        self._wifi_spinner = Spinner(wifi_card, text="Escaneando redes...",
                                      bg=theme.BG_SURFACE0)
        self._wifi_spinner.pack(padx=16, pady=4)

        self._wifi_frame = tk.Frame(wifi_card, bg=theme.BG_SURFACE0)
        self._wifi_frame.pack(fill=tk.BOTH, expand=True, padx=16, pady=(0, 10))

        self._wifi_count_lbl = tk.Label(wifi_card, text="",
                                         bg=theme.BG_SURFACE0,
                                         fg=theme.TEXT_MUTED, font=theme.FONT_SMALL)
        self._wifi_count_lbl.pack(anchor="w", padx=16, pady=(0, 8))

        # ── Ping test ──────────────────────────────────────────────────
        ping_card = Card(parent)
        ping_card.pack(fill=tk.X, pady=(0, 8))

        ping_hdr = tk.Frame(ping_card, bg=theme.BG_SURFACE0)
        ping_hdr.pack(fill=tk.X, padx=16, pady=(12, 6))

        tk.Label(ping_hdr, text=f"Prueba de Conectividad (Ping a {PING_HOST})",
                 bg=theme.BG_SURFACE0, fg=theme.ACCENT_BLUE,
                 font=theme.FONT_H3).pack(side=tk.LEFT)

        tk.Button(ping_hdr, text="▶ Ejecutar Ping",
                   command=self._run_ping, **theme.BTN_PRIMARY).pack(side=tk.RIGHT)

        self._ping_result_lbl = tk.Label(
            ping_card, text="Haga clic en 'Ejecutar Ping' para probar la conectividad.",
            bg=theme.BG_SURFACE0, fg=theme.TEXT_SECONDARY,
            font=theme.FONT_BODY, padx=16, pady=8, anchor="w", justify="left",
        )
        self._ping_result_lbl.pack(fill=tk.X)

        self._ping_spinner = Spinner(ping_card, text="Ejecutando ping...",
                                      bg=theme.BG_SURFACE0)

        # Start loading ethernet
        self._eth_spinner.start()
        self.run_in_thread(self._get_eth, on_done=self._show_eth,
                            on_error=lambda e: self._eth_err(e))

    def on_enter(self):
        self._scan_wifi()

    def _get_eth(self):
        from hardware.network import get_ethernet_adapters_wmi, get_network_adapters
        return {
            "wmi": get_ethernet_adapters_wmi(),
            "psutil": get_network_adapters(),
        }

    def _show_eth(self, data):
        self._eth_spinner.stop()
        self._eth_spinner.pack_forget()

        wmi_adapters = data.get("wmi", [])
        psutil_adapters = data.get("psutil", [])

        for widget in self._eth_frame.winfo_children():
            widget.destroy()

        if not wmi_adapters and not psutil_adapters:
            tk.Label(self._eth_frame,
                     text="No se detectaron adaptadores de red.",
                     bg=theme.BG_SURFACE0, fg=theme.WARNING,
                     font=theme.FONT_BODY).pack(anchor="w")
            return

        for adapter in wmi_adapters[:4]:
            if "error" in adapter:
                continue
            sep = tk.Frame(self._eth_frame, height=1, bg=theme.BG_SURFACE2)
            sep.pack(fill=tk.X, pady=4)

            InfoRow(self._eth_frame, "Adaptador",
                    adapter.get("name", "N/D")[:45],
                    bg=theme.BG_SURFACE0).pack(fill=tk.X, pady=1)
            InfoRow(self._eth_frame, "Fabricante",
                    adapter.get("manufacturer", "N/D"),
                    bg=theme.BG_SURFACE0).pack(fill=tk.X, pady=1)
            InfoRow(self._eth_frame, "MAC",
                    adapter.get("mac_address", "N/D"),
                    bg=theme.BG_SURFACE0).pack(fill=tk.X, pady=1)
            InfoRow(self._eth_frame, "Estado",
                    "Habilitado" if adapter.get("net_enabled") else "Deshabilitado",
                    bg=theme.BG_SURFACE0).pack(fill=tk.X, pady=1)
            type_lbl = adapter.get("adapter_type", "N/D")
            if type_lbl:
                InfoRow(self._eth_frame, "Tipo",
                        type_lbl, bg=theme.BG_SURFACE0).pack(fill=tk.X, pady=1)

    def _eth_err(self, error):
        self._eth_spinner.stop(f"Error: {error}")

    def _scan_wifi(self):
        for widget in self._wifi_frame.winfo_children():
            widget.destroy()
        self._wifi_spinner.pack(padx=16, pady=4)
        self._wifi_spinner.start()
        self.run_in_thread(self._get_wifi, on_done=self._show_wifi,
                            on_error=lambda e: self._wifi_err(e))

    def _get_wifi(self):
        from hardware.network import scan_wifi_networks
        return scan_wifi_networks()

    def _show_wifi(self, networks):
        self._wifi_spinner.stop()
        self._wifi_spinner.pack_forget()

        for widget in self._wifi_frame.winfo_children():
            widget.destroy()

        if not networks:
            tk.Label(self._wifi_frame,
                     text="No se encontraron redes WiFi.\nVerifique que el adaptador esté activo.",
                     bg=theme.BG_SURFACE0, fg=theme.WARNING,
                     font=theme.FONT_BODY).pack(anchor="w")
            self._wifi_count_lbl.configure(text="0 redes encontradas")
            return

        # Header
        hdr = tk.Frame(self._wifi_frame, bg=theme.BG_SURFACE1)
        hdr.pack(fill=tk.X)
        for col, w in [("SSID", 200), ("Señal", 70), ("Auth", 90), ("Canal", 60)]:
            tk.Label(hdr, text=col, bg=theme.BG_SURFACE1,
                     fg=theme.TEXT_MUTED, font=theme.FONT_SMALL,
                     width=w//7, anchor="w", pady=4, padx=6).pack(side=tk.LEFT)

        # Network list (first 20)
        for i, net in enumerate(networks[:20]):
            if "error" in net:
                continue
            bg = theme.BG_SURFACE0 if i % 2 == 0 else theme.BG_MANTLE
            row = tk.Frame(self._wifi_frame, bg=bg)
            row.pack(fill=tk.X)

            ssid = net.get("ssid", "N/D")[:30]
            signal = net.get("signal", "N/D")
            auth = net.get("auth", "N/D")[:15]
            channel = net.get("channel", "N/D")

            # Signal strength color
            try:
                sig_pct = int(str(signal).replace("%", ""))
                sig_color = (theme.SUCCESS if sig_pct >= 70
                              else theme.WARNING if sig_pct >= 40
                              else theme.ERROR)
            except Exception:
                sig_color = theme.TEXT_MUTED

            for text, fg, ww in [
                (ssid, theme.TEXT_PRIMARY, 200),
                (signal, sig_color, 70),
                (auth, theme.TEXT_SECONDARY, 90),
                (channel, theme.TEXT_MUTED, 60),
            ]:
                tk.Label(row, text=text, bg=bg, fg=fg,
                          font=theme.FONT_SMALL, width=ww//7,
                          anchor="w", padx=6, pady=4).pack(side=tk.LEFT)

        self._wifi_count_lbl.configure(
            text=f"{len(networks)} redes encontradas"
        )
        self._set_detail(f"WiFi: {len(networks)} redes detectadas")

    def _wifi_err(self, error):
        self._wifi_spinner.stop()
        self._wifi_spinner.pack_forget()
        tk.Label(self._wifi_frame,
                 text=f"Error WiFi: {error}",
                 bg=theme.BG_SURFACE0, fg=theme.WARNING,
                 font=theme.FONT_SMALL).pack(anchor="w")

    def _run_ping(self):
        self._ping_result_lbl.configure(
            text="Ejecutando ping...", fg=theme.TEXT_MUTED)
        self._ping_spinner.pack(padx=16, pady=4)
        self._ping_spinner.start()
        self.run_in_thread(self._do_ping, on_done=self._show_ping,
                            on_error=lambda e: self._ping_error(e))

    def _do_ping(self):
        from hardware.network import ping_host
        return ping_host(PING_HOST, count=4)

    def _show_ping(self, result):
        self._ping_spinner.stop()
        self._ping_spinner.pack_forget()

        if result.get("reachable"):
            avg = result.get("avg_ms", "N/D")
            recv = result.get("packets_received", 0)
            sent = result.get("packets_sent", 4)
            msg = (f"✓  Conectividad OK — {PING_HOST}\n"
                   f"Paquetes: {recv}/{sent} recibidos | "
                   f"Latencia promedio: {avg} ms")
            self._ping_result_lbl.configure(text=msg, fg=theme.SUCCESS)
            self.set_status(STATUS_PASSED, f"Ping OK: {avg}ms a {PING_HOST}")
        else:
            err = result.get("error", "Desconocido")
            msg = (f"✗  Sin conectividad — {PING_HOST}\n"
                   f"Error: {err}")
            self._ping_result_lbl.configure(text=msg, fg=theme.ERROR)
            self.set_status(STATUS_FAILED, f"Ping fallido: {err}")

    def _ping_error(self, error):
        self._ping_spinner.stop()
        self._ping_spinner.pack_forget()
        self._ping_result_lbl.configure(
            text=f"Error al ejecutar ping: {error}", fg=theme.ERROR)
