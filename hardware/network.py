"""
TecoQC - Información de red (Ethernet, WiFi, ping)
"""

import subprocess
import re


def get_network_adapters():
    """Lista todos los adaptadores de red via psutil."""
    adapters = []
    try:
        import psutil
        stats = psutil.net_if_stats()
        addrs = psutil.net_if_addrs()

        for name, stat in stats.items():
            adapter = {
                "name": name,
                "is_up": stat.isup,
                "speed_mbps": stat.speed,
                "mtu": stat.mtu,
                "addresses": [],
            }
            if name in addrs:
                for addr in addrs[name]:
                    adapter["addresses"].append({
                        "family": str(addr.family),
                        "address": addr.address,
                        "netmask": addr.netmask or "",
                    })
            adapters.append(adapter)
    except Exception as e:
        adapters.append({"error": str(e)})
    return adapters


def get_ethernet_adapters_wmi():
    """Obtiene adaptadores Ethernet via WMI."""
    adapters = []
    try:
        import wmi
        c = wmi.WMI()
        nics = c.Win32_NetworkAdapter(
            PhysicalAdapter=True
        )
        for nic in nics:
            adapter = {
                "name": (nic.Name or "").strip(),
                "manufacturer": (nic.Manufacturer or "").strip(),
                "mac_address": (nic.MACAddress or "").strip(),
                "adapter_type": (nic.AdapterType or "").strip(),
                "net_connection_id": (nic.NetConnectionID or "").strip(),
                "net_enabled": nic.NetEnabled,
                "speed": nic.Speed,
            }
            adapters.append(adapter)
    except Exception as e:
        adapters.append({"error": str(e)})
    return adapters


def scan_wifi_networks():
    """Escanea redes WiFi usando netsh."""
    networks = []
    try:
        result = subprocess.run(
            ["netsh", "wlan", "show", "networks", "mode=bssid"],
            capture_output=True,
            text=True,
            timeout=15,
            encoding="cp1252",
            errors="replace",
        )
        if result.returncode == 0:
            networks = _parse_netsh_networks(result.stdout)
    except FileNotFoundError:
        networks = [{"error": "netsh no disponible"}]
    except subprocess.TimeoutExpired:
        networks = [{"error": "Tiempo de espera agotado al escanear WiFi"}]
    except Exception as e:
        networks = [{"error": str(e)}]
    return networks


def get_wifi_interface_status():
    """Obtiene el estado actual de la interfaz WiFi."""
    info = {}
    try:
        result = subprocess.run(
            ["netsh", "wlan", "show", "interfaces"],
            capture_output=True,
            text=True,
            timeout=10,
            encoding="cp1252",
            errors="replace",
        )
        if result.returncode == 0:
            text = result.stdout
            info["raw"] = text
            # Parse key fields
            for line in text.splitlines():
                line = line.strip()
                if ":" in line:
                    key, _, val = line.partition(":")
                    key = key.strip().lower()
                    val = val.strip()
                    if "nombre" in key or "name" in key:
                        info["interface_name"] = val
                    elif "ssid" in key and "bssid" not in key:
                        info["ssid"] = val
                    elif "estado" in key or "state" in key:
                        info["state"] = val
                    elif "señal" in key or "signal" in key:
                        info["signal"] = val
                    elif "velocidad" in key or "receive rate" in key:
                        info["speed"] = val
    except Exception as e:
        info["error"] = str(e)
    return info


def get_connected_wifi_detail():
    """Llama a get_wifi_interface_status() y enriquece con interpretación de protocolo/banda."""
    base = get_wifi_interface_status()
    detail = dict(base)

    # Parse signal percentage
    raw_signal = detail.get("signal", "")
    try:
        detail["signal_pct"] = int(str(raw_signal).replace("%", "").strip())
    except (ValueError, TypeError):
        detail["signal_pct"] = None

    # Parse channel and infer band
    raw_channel = ""
    radio_type = ""
    raw_text = detail.get("raw", "")
    for line in raw_text.splitlines():
        line_s = line.strip()
        if ":" in line_s:
            key, _, val = line_s.partition(":")
            key_l = key.strip().lower()
            if "canal" in key_l or "channel" in key_l:
                raw_channel = val.strip()
            elif "tipo de radio" in key_l or "radio type" in key_l:
                radio_type = val.strip()
            elif "velocidad de recepción" in key_l or "receive rate" in key_l:
                detail["speed"] = val.strip()
            elif "protocolo" in key_l or "protocol" in key_l:
                if not radio_type:
                    radio_type = val.strip()

    detail["channel"] = raw_channel
    detail["radio_type"] = radio_type

    # Infer band from channel number
    try:
        ch_num = int(raw_channel)
        detail["band"] = "5 GHz" if ch_num > 14 else "2.4 GHz"
    except (ValueError, TypeError):
        # Fallback: infer from radio_type
        rt_lower = radio_type.lower()
        if "802.11a" in rt_lower and "802.11ax" not in rt_lower:
            detail["band"] = "5 GHz"
        elif "802.11ac" in rt_lower or "802.11ax" in rt_lower:
            detail["band"] = "5 GHz"
        else:
            detail["band"] = "N/D"

    # Interpret protocol name
    rt_lower = radio_type.lower()
    if "802.11ax" in rt_lower:
        detail["protocol_name"] = "WiFi 6 (802.11ax)"
    elif "802.11ac" in rt_lower:
        detail["protocol_name"] = "WiFi 5 (802.11ac)"
    elif "802.11n" in rt_lower:
        detail["protocol_name"] = "WiFi 4 (802.11n)"
    elif "802.11a" in rt_lower:
        detail["protocol_name"] = "802.11a"
    elif "802.11g" in rt_lower:
        detail["protocol_name"] = "802.11g"
    elif "802.11b" in rt_lower:
        detail["protocol_name"] = "802.11b"
    elif radio_type:
        detail["protocol_name"] = radio_type
    else:
        detail["protocol_name"] = "N/D"

    return detail


def ping_host(host="8.8.8.8", count=4):
    """Realiza ping a un host y retorna el resultado."""
    result = {
        "host": host,
        "reachable": False,
        "avg_ms": None,
        "packets_sent": count,
        "packets_received": 0,
        "output": "",
        "error": None,
    }
    try:
        cmd = ["ping", "-n", str(count), host]
        proc = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=30,
            encoding="cp1252",
            errors="replace",
        )
        result["output"] = proc.stdout
        if proc.returncode == 0:
            result["reachable"] = True
            # Parse average RTT
            match = re.search(r"Media\s*=\s*(\d+)ms|Average\s*=\s*(\d+)ms",
                               proc.stdout)
            if match:
                val = match.group(1) or match.group(2)
                result["avg_ms"] = int(val)
            # Parse packets received
            match2 = re.search(r"Recibidos\s*=\s*(\d+)|Received\s*=\s*(\d+)",
                                proc.stdout)
            if match2:
                val2 = match2.group(1) or match2.group(2)
                result["packets_received"] = int(val2)
        else:
            result["error"] = "Host inalcanzable"
    except subprocess.TimeoutExpired:
        result["error"] = "Tiempo de espera agotado"
    except Exception as e:
        result["error"] = str(e)
    return result


def _parse_netsh_networks(output):
    networks = []
    current = {}
    for line in output.splitlines():
        line = line.strip()
        if line.startswith("SSID") and "BSSID" not in line:
            if current and current.get("ssid"):
                networks.append(current)
            current = {}
            _, _, val = line.partition(":")
            current["ssid"] = val.strip()
        elif "Autenticación" in line or "Authentication" in line:
            _, _, val = line.partition(":")
            current["auth"] = val.strip()
        elif "Cifrado" in line or "Cipher" in line:
            _, _, val = line.partition(":")
            current["cipher"] = val.strip()
        elif "BSSID" in line:
            _, _, val = line.partition(":")
            if "bssid" not in current:
                current["bssid"] = val.strip()
        elif "Señal" in line or "Signal" in line:
            _, _, val = line.partition(":")
            current["signal"] = val.strip()
        elif "Tipo de radio" in line or "Radio type" in line:
            _, _, val = line.partition(":")
            current["radio_type"] = val.strip()
        elif "Canal" in line or "Channel" in line:
            _, _, val = line.partition(":")
            current["channel"] = val.strip()
    if current and current.get("ssid"):
        networks.append(current)
    return networks
