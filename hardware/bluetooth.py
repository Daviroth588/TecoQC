"""
TecoQC - Detección de Bluetooth
"""

import subprocess


def get_bluetooth_info():
    """Detecta adaptadores Bluetooth y dispositivos emparejados via WMI."""
    result = {
        "adapters": [],
        "paired_devices": [],
        "enabled": False,
        "error": None,
    }

    # Detect Bluetooth adapters via WMI
    try:
        import wmi
        c = wmi.WMI()
        entities = c.Win32_PnPEntity()
        for e in entities:
            name = (e.Name or "").lower()
            pnp_class = (e.PNPClass or "").upper()
            if "bluetooth" in name or pnp_class == "BLUETOOTH":
                is_adapter = any(k in name for k in
                                  ("radio", "adapter", "controller", "host"))
                entry = {
                    "name": (e.Name or "").strip(),
                    "manufacturer": (e.Manufacturer or "").strip(),
                    "status": (e.Status or "").strip(),
                    "device_id": (e.DeviceID or "")[:60],
                    "is_adapter": is_adapter,
                    "enabled": (e.Status or "").upper() == "OK",
                }
                if is_adapter:
                    result["adapters"].append(entry)
                    if entry["enabled"]:
                        result["enabled"] = True
                else:
                    result["paired_devices"].append(entry)
    except Exception as e:
        result["error"] = str(e)

    # Try PowerShell for more detailed BT adapter info
    try:
        ps_cmd = (
            "Get-PnpDevice -Class Bluetooth -ErrorAction SilentlyContinue | "
            "Select-Object FriendlyName,Status,InstanceId | "
            "ConvertTo-Json -Depth 2"
        )
        proc = subprocess.run(
            ["powershell", "-NoProfile", "-NonInteractive", "-Command", ps_cmd],
            capture_output=True, text=True, timeout=10,
        )
        if proc.returncode == 0 and proc.stdout.strip():
            import json
            raw = proc.stdout.strip()
            if raw.startswith("{"):
                raw = f"[{raw}]"
            devices = json.loads(raw)
            if isinstance(devices, dict):
                devices = [devices]
            for d in devices:
                name = str(d.get("FriendlyName", ""))
                status = str(d.get("Status", ""))
                already = any(a["name"] == name for a in result["adapters"])
                if not already and name:
                    result["adapters"].append({
                        "name": name,
                        "manufacturer": "",
                        "status": status,
                        "device_id": str(d.get("InstanceId", ""))[:60],
                        "is_adapter": True,
                        "enabled": status.upper() == "OK",
                    })
                    if status.upper() == "OK":
                        result["enabled"] = True
    except Exception:
        pass

    return result


def scan_bluetooth_devices():
    """Intenta un escaneo activo de dispositivos BT cercanos via PowerShell."""
    devices = []
    try:
        ps_cmd = (
            "[Windows.Devices.Enumeration.DeviceInformation,Windows.Devices.Enumeration,"
            "ContentType=WindowsRuntime] | Out-Null; "
            "$selector = [Windows.Devices.Bluetooth.BluetoothDevice]"
            "::GetDeviceSelectorFromPairingState($false); "
            "$task = [Windows.Devices.Enumeration.DeviceInformation]"
            "::FindAllAsync($selector); "
            "Start-Sleep -Seconds 3; "
            "$result = $task.GetAwaiter().GetResult(); "
            "$result | Select-Object Name,Id | ConvertTo-Json -Depth 2"
        )
        proc = subprocess.run(
            ["powershell", "-NoProfile", "-NonInteractive", "-Command", ps_cmd],
            capture_output=True, text=True, timeout=15,
        )
        if proc.returncode == 0 and proc.stdout.strip():
            import json
            raw = proc.stdout.strip()
            if raw.startswith("{"):
                raw = f"[{raw}]"
            devs = json.loads(raw)
            if isinstance(devs, dict):
                devs = [devs]
            for d in devs:
                if d.get("Name"):
                    devices.append({
                        "name": str(d.get("Name", "")),
                        "id": str(d.get("Id", ""))[:60],
                    })
    except Exception:
        pass
    return devices
