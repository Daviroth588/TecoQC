"""
TecoQC - Paso 8: Prueba de red (Ethernet + WiFi + Ping + DNS + Descarga)
"""

import tkinter as tk
from ui.steps.base_step import BaseStep
from ui.components import Card, Spinner, InfoRow
from ui import theme
from config import (STATUS_PASSED, STATUS_FAILED, PING_HOST,
                    PING_FALLBACK_HOST, PING_MAX_MS, NET_DOWNLOAD_MIN_MB_S)


class Step(BaseStep):
    TITLE = "Prueba de Red"
    DESCRIPTION = "Verificación de Ethernet, WiFi, conectividad (ping), DNS y velocidad de descarga."
    STEP_NUM = 8

    def build_ui(self, parent):
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

        # ── Connected WiFi detail card ─────────────────────────────────
        self._wifi_detail_card = Card(parent)
        self._wifi_detail_card.pack(fill=tk.X, pady=(0, 8))

        wifi_detail_hdr = tk.Frame(self._wifi_detail_card, bg=theme.BG_SURFACE0)
        wifi_detail_hdr.pack(fill=tk.X, padx=16, pady=(10, 6))
        tk.Label(wifi_detail_hdr, text="Conexión WiFi Actual",
                 bg=theme.BG_SURFACE0, fg=theme.ACCENT_BLUE,
                 font=theme.FONT_H3).pack(side=tk.LEFT)

        tk.Frame(self._wifi_detail_card, height=1, bg=theme.BG_SURFACE2).pack(fill=tk.X, padx=16)

        self._wifi_detail_spinner = Spinner(self._wifi_detail_card,
                                             text="Leyendo interfaz WiFi...",
                                             bg=theme.BG_SURFACE0)
        self._wifi_detail_spinner.pack(padx=16, pady=8)

        self._wifi_detail_frame = tk.Frame(self._wifi_detail_card, bg=theme.BG_SURFACE0)
        self._wifi_detail_frame.pack(fill=tk.X, padx=16, pady=(0, 10))

        # ── Connectivity tests row ─────────────────────────────────────
        conn_frame = tk.Frame(parent, bg=theme.BG_BASE)
        conn_frame.pack(fill=tk.X, pady=(0, 8))
        conn_frame.columnconfigure(0, weight=1)
        conn_frame.columnconfigure(1, weight=1)
        conn_frame.columnconfigure(2, weight=1)

        # Ping card
        ping_card = Card(conn_frame)
        ping_card.grid(row=0, column=0, padx=(0, 6), sticky="nsew")

        ping_hdr = tk.Frame(ping_card, bg=theme.BG_SURFACE0)
        ping_hdr.pack(fill=tk.X, padx=12, pady=(10, 6))
        tk.Label(ping_hdr, text=f"Ping ({PING_HOST})",
                 bg=theme.BG_SURFACE0, fg=theme.ACCENT_BLUE,
                 font=theme.FONT_BODY_BOLD).pack(side=tk.LEFT)
        tk.Button(ping_hdr, text="▶",
                   command=self._run_ping, **theme.BTN_PRIMARY).pack(side=tk.RIGHT)

        self._ping_result_lbl = tk.Label(
            ping_card,
            text="Haga clic ▶ para probar.",
            bg=theme.BG_SURFACE0, fg=theme.TEXT_SECONDARY,
            font=theme.FONT_SMALL, padx=12, pady=6, anchor="w", justify="left",
        )
        self._ping_result_lbl.pack(fill=tk.X)
        self._ping_spinner = Spinner(ping_card, text="Ejecutando...", bg=theme.BG_SURFACE0)

        # DNS card
        dns_card = Card(conn_frame)
        dns_card.grid(row=0, column=1, padx=6, sticky="nsew")

        dns_hdr = tk.Frame(dns_card, bg=theme.BG_SURFACE0)
        dns_hdr.pack(fill=tk.X, padx=12, pady=(10, 6))
        tk.Label(dns_hdr, text="Resolución DNS",
                 bg=theme.BG_SURFACE0, fg=theme.ACCENT_BLUE,
                 font=theme.FONT_BODY_BOLD).pack(side=tk.LEFT)
        tk.Button(dns_hdr, text="▶",
                   command=self._run_dns, **theme.BTN_PRIMARY).pack(side=tk.RIGHT)

        self._dns_result_lbl = tk.Label(
            dns_card, text="Haga clic ▶ para probar.",
            bg=theme.BG_SURFACE0, fg=theme.TEXT_SECONDARY,
            font=theme.FONT_SMALL, padx=12, pady=6, anchor="w", justify="left",
        )
        self._dns_result_lbl.pack(fill=tk.X)
        self._dns_spinner = Spinner(dns_card, text="Resolviendo...", bg=theme.BG_SURFACE0)

        # Download card
        dl_card = Card(conn_frame)
        dl_card.grid(row=0, column=2, padx=(6, 0), sticky="nsew")

        dl_hdr = tk.Frame(dl_card, bg=theme.BG_SURFACE0)
        dl_hdr.pack(fill=tk.X, padx=12, pady=(10, 6))
        tk.Label(dl_hdr, text="Velocidad descarga",
                 bg=theme.BG_SURFACE0, fg=theme.ACCENT_BLUE,
                 font=theme.FONT_BODY_BOLD).pack(side=tk.LEFT)
        tk.Button(dl_hdr, text="▶",
                   command=self._run_download, **theme.BTN_PRIMARY).pack(side=tk.RIGHT)

        self._dl_result_lbl = tk.Label(
            dl_card, text="Haga clic ▶ para probar.",
            bg=theme.BG_SURFACE0, fg=theme.TEXT_SECONDARY,
            font=theme.FONT_SMALL, padx=12, pady=6, anchor="w", justify="left",
        )
        self._dl_result_lbl.pack(fill=tk.X)
        self._dl_spinner = Spinner(dl_card, text="Descargando...", bg=theme.BG_SURFACE0)

        # Start loading ethernet
        self._eth_spinner.start()
        self.run_in_thread(self._get_eth, on_done=self._show_eth,
                            on_error=lambda e: self._eth_err(e))

        # Results tracking
        self._ping_ok = None
        self._dns_ok = None
        self._dl_ok = None

        # ── Bluetooth section ──────────────────────────────────────────
        bt_card = Card(parent)
        bt_card.pack(fill=tk.X, pady=(0, 8))

        bt_hdr = tk.Frame(bt_card, bg=theme.BG_SURFACE0)
        bt_hdr.pack(fill=tk.X, padx=16, pady=(10, 6))
        tk.Label(bt_hdr, text="Bluetooth",
                 bg=theme.BG_SURFACE0, fg=theme.ACCENT_BLUE,
                 font=theme.FONT_H3).pack(side=tk.LEFT)
        tk.Button(bt_hdr, text="🔍 Detectar",
                   command=self._detect_bluetooth, **theme.BTN_NEUTRAL).pack(side=tk.RIGHT)

        self._bt_spinner = Spinner(bt_card, text="Detectando Bluetooth...",
                                    bg=theme.BG_SURFACE0)

        self._bt_frame = tk.Frame(bt_card, bg=theme.BG_SURFACE0)
        self._bt_frame.pack(fill=tk.X, padx=16, pady=(0, 10))

        tk.Label(self._bt_frame,
                 text="Haga clic en 'Detectar' para escanear el adaptador Bluetooth.",
                 bg=theme.BG_SURFACE0, fg=theme.TEXT_MUTED,
                 font=theme.FONT_SMALL).pack(anchor="w")

    def on_enter(self):
        self._scan_wifi()
        self._load_wifi_detail()

    def _load_wifi_detail(self):
        for w in self._wifi_detail_frame.winfo_children():
            w.destroy()
        self._wifi_detail_spinner.pack(padx=16, pady=8)
        self._wifi_detail_spinner.start()
        self.run_in_thread(self._get_wifi_detail, on_done=self._show_wifi_detail,
                            on_error=lambda e: self._wifi_detail_err(e))

    def _get_wifi_detail(self):
        from hardware.network import get_connected_wifi_detail
        return get_connected_wifi_detail()

    def _show_wifi_detail(self, detail):
        self._wifi_detail_spinner.stop()
        self._wifi_detail_spinner.pack_forget()

        for w in self._wifi_detail_frame.winfo_children():
            w.destroy()

        ssid = detail.get("ssid", "")
        if not ssid:
            tk.Label(self._wifi_detail_frame,
                     text="No conectado a ninguna red WiFi.",
                     bg=theme.BG_SURFACE0, fg=theme.TEXT_MUTED,
                     font=theme.FONT_BODY).pack(anchor="w", pady=4)
            return

        # Signal color
        sig_pct = detail.get("signal_pct")
        if sig_pct is not None:
            sig_color = (theme.SUCCESS if sig_pct >= 70
                         else theme.WARNING if sig_pct >= 40
                         else theme.ERROR)
            sig_text = f"{sig_pct}%"
        else:
            sig_color = theme.TEXT_MUTED
            sig_text = detail.get("signal", "N/D")

        rows_left = [
            ("SSID", ssid, theme.TEXT_PRIMARY),
            ("Señal", sig_text, sig_color),
            ("Vel. recepción", detail.get("speed", "N/D"), theme.TEXT_PRIMARY),
        ]
        rows_right = [
            ("Estado", detail.get("state", "N/D"), theme.TEXT_PRIMARY),
            ("Protocolo", detail.get("protocol_name", "N/D"), theme.TEXT_PRIMARY),
            ("Banda", detail.get("band", "N/D"), theme.ACCENT_BLUE),
        ]

        two_col = tk.Frame(self._wifi_detail_frame, bg=theme.BG_SURFACE0)
        two_col.pack(fill=tk.X)
        left_col = tk.Frame(two_col, bg=theme.BG_SURFACE0)
        left_col.pack(side=tk.LEFT, fill=tk.X, expand=True)
        right_col = tk.Frame(two_col, bg=theme.BG_SURFACE0)
        right_col.pack(side=tk.LEFT, fill=tk.X, expand=True)

        for lbl, val, fg in rows_left:
            row = tk.Frame(left_col, bg=theme.BG_SURFACE0)
            row.pack(fill=tk.X, pady=2)
            tk.Label(row, text=lbl + ":", bg=theme.BG_SURFACE0,
                     fg=theme.TEXT_SECONDARY, font=theme.FONT_BODY,
                     width=18, anchor="w").pack(side=tk.LEFT)
            tk.Label(row, text=val, bg=theme.BG_SURFACE0,
                     fg=fg, font=theme.FONT_BODY_BOLD,
                     anchor="w").pack(side=tk.LEFT)

        for lbl, val, fg in rows_right:
            row = tk.Frame(right_col, bg=theme.BG_SURFACE0)
            row.pack(fill=tk.X, pady=2)
            tk.Label(row, text=lbl + ":", bg=theme.BG_SURFACE0,
                     fg=theme.TEXT_SECONDARY, font=theme.FONT_BODY,
                     width=14, anchor="w").pack(side=tk.LEFT)
            tk.Label(row, text=val, bg=theme.BG_SURFACE0,
                     fg=fg, font=theme.FONT_BODY_BOLD,
                     anchor="w").pack(side=tk.LEFT)

    def _wifi_detail_err(self, error):
        self._wifi_detail_spinner.stop()
        self._wifi_detail_spinner.pack_forget()
        tk.Label(self._wifi_detail_frame,
                 text=f"Error al leer interfaz WiFi: {error}",
                 bg=theme.BG_SURFACE0, fg=theme.WARNING,
                 font=theme.FONT_SMALL).pack(anchor="w")

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
        for widget in self._eth_frame.winfo_children():
            widget.destroy()

        if not wmi_adapters:
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

        hdr = tk.Frame(self._wifi_frame, bg=theme.BG_SURFACE1)
        hdr.pack(fill=tk.X)
        for col, w in [("SSID", 200), ("Señal", 70), ("Auth", 90), ("Canal", 60), ("Banda", 65)]:
            tk.Label(hdr, text=col, bg=theme.BG_SURFACE1,
                     fg=theme.TEXT_MUTED, font=theme.FONT_SMALL,
                     width=w//7, anchor="w", pady=4, padx=6).pack(side=tk.LEFT)

        for i, net in enumerate(networks[:20]):
            if "error" in net:
                continue
            bg = theme.BG_SURFACE0 if i % 2 == 0 else theme.BG_MANTLE
            row = tk.Frame(self._wifi_frame, bg=bg)
            row.pack(fill=tk.X)

            signal = net.get("signal", "N/D")
            try:
                sig_pct = int(str(signal).replace("%", ""))
                sig_color = (theme.SUCCESS if sig_pct >= 70
                              else theme.WARNING if sig_pct >= 40
                              else theme.ERROR)
            except Exception:
                sig_color = theme.TEXT_MUTED

            # Infer band from channel or radio_type
            try:
                ch_num = int(net.get("channel", "0"))
                band = "5 GHz" if ch_num > 14 else "2.4 GHz"
            except (ValueError, TypeError):
                rt = net.get("radio_type", "").lower()
                if "802.11ac" in rt or "802.11ax" in rt or ("802.11a" in rt and "802.11ax" not in rt):
                    band = "5 GHz"
                elif "802.11n" in rt or "802.11g" in rt or "802.11b" in rt:
                    band = "2.4 GHz"
                else:
                    band = "N/D"

            for text, fg, ww in [
                (net.get("ssid", "N/D")[:30], theme.TEXT_PRIMARY, 200),
                (signal, sig_color, 70),
                (net.get("auth", "N/D")[:15], theme.TEXT_SECONDARY, 90),
                (net.get("channel", "N/D"), theme.TEXT_MUTED, 60),
                (band, theme.ACCENT_BLUE if band != "N/D" else theme.TEXT_MUTED, 65),
            ]:
                tk.Label(row, text=text, bg=bg, fg=fg,
                          font=theme.FONT_SMALL, width=ww//7,
                          anchor="w", padx=6, pady=4).pack(side=tk.LEFT)

        self._wifi_count_lbl.configure(text=f"{len(networks)} redes encontradas")
        self._set_detail(f"WiFi: {len(networks)} redes detectadas")

    def _wifi_err(self, error):
        self._wifi_spinner.stop()
        self._wifi_spinner.pack_forget()
        tk.Label(self._wifi_frame, text=f"Error WiFi: {error}",
                 bg=theme.BG_SURFACE0, fg=theme.WARNING,
                 font=theme.FONT_SMALL).pack(anchor="w")

    # ── Ping ───────────────────────────────────────────────────────────
    def _run_ping(self):
        self._ping_result_lbl.configure(text="Ejecutando ping...", fg=theme.TEXT_MUTED)
        self._ping_spinner.pack(padx=12, pady=4)
        self._ping_spinner.start()
        self.run_in_thread(self._do_ping, on_done=self._show_ping,
                            on_error=lambda e: self._ping_error(e))

    def _do_ping(self):
        from hardware.network import ping_host
        result = ping_host(PING_HOST, count=4)
        if not result.get("reachable"):
            result2 = ping_host(PING_FALLBACK_HOST, count=4)
            if result2.get("reachable"):
                result2["used_host"] = PING_FALLBACK_HOST
                return result2
        result["used_host"] = PING_HOST
        return result

    def _show_ping(self, result):
        self._ping_spinner.stop()
        self._ping_spinner.pack_forget()
        host = result.get("used_host", PING_HOST)

        if result.get("reachable"):
            avg = result.get("avg_ms", 0) or 0
            recv = result.get("packets_received", 0)
            ok = int(avg) <= PING_MAX_MS if avg else True
            fg = theme.SUCCESS if ok else theme.WARNING
            self._ping_result_lbl.configure(
                text=f"✓ {host}\n{recv}/4 paquetes | {avg} ms",
                fg=fg)
            self._ping_ok = True
        else:
            self._ping_result_lbl.configure(
                text=f"✗ Sin conectividad\n{result.get('error', '')}",
                fg=theme.ERROR)
            self._ping_ok = False
        self._evaluate_overall()

    def _ping_error(self, error):
        self._ping_spinner.stop()
        self._ping_spinner.pack_forget()
        self._ping_result_lbl.configure(text=f"Error: {error}", fg=theme.ERROR)
        self._ping_ok = False
        self._evaluate_overall()

    # ── DNS ────────────────────────────────────────────────────────────
    def _run_dns(self):
        self._dns_result_lbl.configure(text="Resolviendo DNS...", fg=theme.TEXT_MUTED)
        self._dns_spinner.pack(padx=12, pady=4)
        self._dns_spinner.start()
        self.run_in_thread(self._do_dns, on_done=self._show_dns,
                            on_error=lambda e: self._dns_error(e))

    def _do_dns(self):
        import socket, time
        hosts = ["google.com", "microsoft.com", "cloudflare.com"]
        results = []
        for host in hosts:
            t0 = time.time()
            try:
                ip = socket.getaddrinfo(host, None)[0][4][0]
                ms = round((time.time() - t0) * 1000)
                results.append({"host": host, "ip": ip, "ms": ms, "ok": True})
            except Exception as e:
                results.append({"host": host, "error": str(e), "ok": False})
        return results

    def _show_dns(self, results):
        self._dns_spinner.stop()
        self._dns_spinner.pack_forget()
        ok_count = sum(1 for r in results if r.get("ok"))
        if ok_count >= 2:
            avg_ms = sum(r.get("ms", 0) for r in results if r.get("ok")) // max(ok_count, 1)
            self._dns_result_lbl.configure(
                text=f"✓ DNS OK ({ok_count}/3 hosts)\nLatencia: {avg_ms} ms",
                fg=theme.SUCCESS)
            self._dns_ok = True
        else:
            failed = [r["host"] for r in results if not r.get("ok")]
            self._dns_result_lbl.configure(
                text=f"✗ DNS fallido\n{', '.join(failed)}",
                fg=theme.ERROR)
            self._dns_ok = False
        self._evaluate_overall()

    def _dns_error(self, error):
        self._dns_spinner.stop()
        self._dns_spinner.pack_forget()
        self._dns_result_lbl.configure(text=f"Error: {error}", fg=theme.ERROR)
        self._dns_ok = False
        self._evaluate_overall()

    # ── Download speed ─────────────────────────────────────────────────
    def _run_download(self):
        self._dl_result_lbl.configure(text="Descargando prueba...", fg=theme.TEXT_MUTED)
        self._dl_spinner.pack(padx=12, pady=4)
        self._dl_spinner.start()
        self.run_in_thread(self._do_download, on_done=self._show_download,
                            on_error=lambda e: self._dl_error(e))

    def _do_download(self):
        import urllib.request, time
        # Use Cloudflare CDN — low latency, reliable for speed tests
        candidates = [
            ("https://speed.cloudflare.com/__down?bytes=5242880", 5.0),   # 5 MB
            ("http://cachefly.cachefly.net/5mb.zip", 5.0),                 # 5 MB fallback
            ("http://speedtest.tele2.net/1MB.zip", 1.0),                   # 1 MB last resort
        ]
        for url, expected_mb in candidates:
            try:
                t0 = time.time()
                req = urllib.request.Request(url, headers={"User-Agent": "TecoQC/1.0"})
                with urllib.request.urlopen(req, timeout=20) as resp:
                    data = resp.read()
                elapsed = time.time() - t0
                if elapsed < 0.1:
                    continue
                size_mb = len(data) / (1024 * 1024)
                speed_mb_s = size_mb / elapsed
                return {"ok": True, "speed_mb_s": speed_mb_s, "size_mb": size_mb}
            except Exception:
                continue
        return {"ok": False, "error": "No se pudo conectar a ningún servidor de prueba"}

    def _show_download(self, result):
        self._dl_spinner.stop()
        self._dl_spinner.pack_forget()
        if result.get("ok"):
            speed = result.get("speed_mb_s", 0)
            ok = speed >= NET_DOWNLOAD_MIN_MB_S
            fg = theme.SUCCESS if ok else theme.WARNING
            self._dl_result_lbl.configure(
                text=f"{'✓' if ok else '⚠'} {speed:.2f} MB/s\nMínimo: {NET_DOWNLOAD_MIN_MB_S} MB/s",
                fg=fg)
            self._dl_ok = ok
        else:
            self._dl_result_lbl.configure(
                text=f"✗ Error descarga\n{result.get('error', '')[:40]}",
                fg=theme.ERROR)
            self._dl_ok = False
        self._evaluate_overall()

    def _dl_error(self, error):
        self._dl_spinner.stop()
        self._dl_spinner.pack_forget()
        self._dl_result_lbl.configure(text=f"Error: {error}", fg=theme.ERROR)
        self._dl_ok = False
        self._evaluate_overall()

    # ── Overall evaluation ─────────────────────────────────────────────
    def _evaluate_overall(self):
        done = [x for x in (self._ping_ok, self._dns_ok, self._dl_ok) if x is not None]
        failed = [x for x in done if x is False]
        if len(done) == 3:
            if not failed:
                self.set_status(STATUS_PASSED, "Ping ✓  DNS ✓  Descarga ✓")
            else:
                fail_count = len(failed)
                self.set_status(STATUS_FAILED,
                                 f"{fail_count} prueba(s) de red fallidas")
        elif len(done) > 0:
            passed_cnt = sum(1 for x in done if x)
            self._set_detail(f"{passed_cnt}/{len(done)} pruebas OK")

    # ── Bluetooth ──────────────────────────────────────────────────────
    def _detect_bluetooth(self):
        for w in self._bt_frame.winfo_children():
            w.destroy()
        self._bt_spinner.pack(padx=16, pady=4)
        self._bt_spinner.start()
        self.run_in_thread(self._do_bluetooth, on_done=self._show_bluetooth,
                            on_error=lambda e: self._bt_error(e))

    def _do_bluetooth(self):
        from hardware.bluetooth import get_bluetooth_info
        return get_bluetooth_info()

    def _show_bluetooth(self, data):
        self._bt_spinner.stop()
        self._bt_spinner.pack_forget()

        for w in self._bt_frame.winfo_children():
            w.destroy()

        adapters = data.get("adapters", [])
        enabled = data.get("enabled", False)
        error = data.get("error")

        if error and not adapters:
            tk.Label(self._bt_frame, text=f"⚠ Error WMI: {error}",
                     bg=theme.BG_SURFACE0, fg=theme.WARNING,
                     font=theme.FONT_SMALL).pack(anchor="w")
            return

        if not adapters:
            tk.Label(self._bt_frame,
                     text="⚠ No se detectaron adaptadores Bluetooth.\n"
                          "Verifique que el controlador esté instalado.",
                     bg=theme.BG_SURFACE0, fg=theme.WARNING,
                     font=theme.FONT_BODY).pack(anchor="w")
            return

        # Status row
        status_txt = "✓ Bluetooth activo" if enabled else "⚠ Bluetooth detectado pero inactivo"
        status_fg = theme.SUCCESS if enabled else theme.WARNING
        tk.Label(self._bt_frame, text=status_txt,
                 bg=theme.BG_SURFACE0, fg=status_fg,
                 font=theme.FONT_BODY_BOLD).pack(anchor="w", pady=(0, 6))

        # Adapter list
        for a in adapters[:3]:
            row = tk.Frame(self._bt_frame, bg=theme.BG_SURFACE0)
            row.pack(fill=tk.X, pady=1)
            status = a.get("status", "")
            fg = theme.SUCCESS if status.upper() == "OK" else theme.WARNING
            tk.Label(row, text=f"● {a.get('name', 'N/D')[:50]}",
                     bg=theme.BG_SURFACE0, fg=theme.TEXT_PRIMARY,
                     font=theme.FONT_SMALL).pack(side=tk.LEFT)
            tk.Label(row, text=f" [{status}]",
                     bg=theme.BG_SURFACE0, fg=fg,
                     font=theme.FONT_SMALL).pack(side=tk.LEFT, padx=4)
            mfg = a.get("manufacturer", "")
            if mfg:
                tk.Label(row, text=f"— {mfg[:30]}",
                         bg=theme.BG_SURFACE0, fg=theme.TEXT_MUTED,
                         font=theme.FONT_SMALL).pack(side=tk.LEFT)

        paired = data.get("paired_devices", [])
        if paired:
            tk.Label(self._bt_frame,
                     text=f"Dispositivos emparejados: {len(paired)}",
                     bg=theme.BG_SURFACE0, fg=theme.TEXT_SECONDARY,
                     font=theme.FONT_SMALL).pack(anchor="w", pady=(4, 0))

    def _bt_error(self, error):
        self._bt_spinner.stop()
        self._bt_spinner.pack_forget()
        for w in self._bt_frame.winfo_children():
            w.destroy()
        tk.Label(self._bt_frame, text=f"Error Bluetooth: {error}",
                 bg=theme.BG_SURFACE0, fg=theme.WARNING,
                 font=theme.FONT_SMALL).pack(anchor="w")
