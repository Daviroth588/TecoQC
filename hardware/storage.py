"""
TecoQC - Información de almacenamiento, SMART y velocidad de disco
"""

import subprocess
import os
import time


def get_drives_info():
    """Lista todas las unidades lógicas via psutil."""
    drives = []
    try:
        import psutil
        partitions = psutil.disk_partitions(all=False)
        for p in partitions:
            drive = {
                "device": p.device,
                "mountpoint": p.mountpoint,
                "fstype": p.fstype,
                "opts": p.opts,
            }
            try:
                usage = psutil.disk_usage(p.mountpoint)
                drive["total_bytes"] = usage.total
                drive["used_bytes"] = usage.used
                drive["free_bytes"] = usage.free
                drive["percent"] = usage.percent
                drive["total_gb"] = round(usage.total / (1024**3), 2)
                drive["used_gb"] = round(usage.used / (1024**3), 2)
                drive["free_gb"] = round(usage.free / (1024**3), 2)
            except Exception:
                pass
            drives.append(drive)
    except Exception as e:
        drives.append({"error": str(e)})
    return drives


def get_physical_drives_wmi():
    """Obtiene información de discos físicos via WMI."""
    disks = []
    try:
        import wmi
        c = wmi.WMI()
        disk_drives = c.Win32_DiskDrive()
        for d in disk_drives:
            disk = {
                "model": (d.Model or "").strip(),
                "serial": (d.SerialNumber or "").strip(),
                "interface": (d.InterfaceType or "").strip(),
                "media_type": (d.MediaType or "").strip(),
                "size_bytes": int(d.Size or 0),
                "size_gb": round(int(d.Size or 0) / (1024**3), 2),
                "partitions": d.Partitions or 0,
                "status": (d.Status or "").strip(),
                "capabilities": _parse_capabilities(d.Capabilities),
            }
            disks.append(disk)
    except Exception as e:
        disks.append({"error": str(e)})
    return disks


def get_smart_status():
    """Obtiene el estado SMART de los discos via wmic."""
    results = []
    try:
        result = subprocess.run(
            ["wmic", "diskdrive", "get", "Model,Status,Size,InterfaceType",
             "/format:csv"],
            capture_output=True,
            text=True,
            timeout=15,
        )
        if result.returncode == 0:
            lines = [l.strip() for l in result.stdout.strip().splitlines()
                     if l.strip() and not l.startswith("Node")]
            # Skip header line
            header_skipped = False
            for line in lines:
                if not header_skipped:
                    header_skipped = True
                    continue
                parts = line.split(",")
                if len(parts) >= 4:
                    results.append({
                        "interface": parts[1].strip() if len(parts) > 1 else "",
                        "model": parts[2].strip() if len(parts) > 2 else "",
                        "size_bytes": _safe_int(parts[3]) if len(parts) > 3 else 0,
                        "status": parts[4].strip() if len(parts) > 4 else "",
                    })
    except Exception as e:
        results.append({"error": str(e)})
    return results


def run_disk_speed_test(path=None, size_mb=64):
    """Realiza una prueba básica de velocidad de lectura/escritura."""
    result = {
        "write_mb_s": 0,
        "read_mb_s": 0,
        "path": path or os.path.expanduser("~"),
        "size_mb": size_mb,
        "error": None,
    }

    if path is None:
        path = os.path.expanduser("~")

    test_file = os.path.join(path, "_tecoqc_speedtest.tmp")
    data = os.urandom(1024 * 1024)  # 1 MB chunk

    try:
        # Write test
        start = time.time()
        with open(test_file, "wb") as f:
            for _ in range(size_mb):
                f.write(data)
            f.flush()
            os.fsync(f.fileno())
        write_time = time.time() - start
        if write_time > 0:
            result["write_mb_s"] = round(size_mb / write_time, 1)

        # Read test
        start = time.time()
        with open(test_file, "rb") as f:
            while True:
                chunk = f.read(1024 * 1024)
                if not chunk:
                    break
        read_time = time.time() - start
        if read_time > 0:
            result["read_mb_s"] = round(size_mb / read_time, 1)

    except Exception as e:
        result["error"] = str(e)
    finally:
        try:
            if os.path.exists(test_file):
                os.remove(test_file)
        except Exception:
            pass

    return result


def _safe_int(val):
    try:
        return int(str(val).strip())
    except Exception:
        return 0


def _parse_capabilities(caps):
    capability_names = {
        0: "Desconocido", 1: "Otro", 2: "Secuencial",
        3: "Acceso aleatorio", 4: "Soporta escritura",
        5: "Soporta detección de error", 6: "Transferencia FBA",
        7: "Transferencia CHA",
    }
    if not caps:
        return []
    try:
        return [capability_names.get(c, str(c)) for c in caps]
    except Exception:
        return []


def get_smart_detailed():
    """
    Obtiene atributos SMART detallados via wmic y PowerShell.
    Retorna lista de discos con atributos críticos interpretados.
    """
    results = []

    # Try wmic for basic SMART status with more fields
    try:
        proc = subprocess.run(
            ["wmic", "diskdrive", "get",
             "Caption,Status,Size,InterfaceType,Availability,StatusInfo",
             "/format:csv"],
            capture_output=True, text=True, timeout=15,
        )
        if proc.returncode == 0:
            lines = [l.strip() for l in proc.stdout.strip().splitlines()
                     if l.strip() and l.strip() != "Node"]
            header = None
            for line in lines:
                parts = line.split(",")
                if not header:
                    header = [p.strip() for p in parts]
                    continue
                if len(parts) < len(header):
                    continue
                row = dict(zip(header, [p.strip() for p in parts]))
                status = row.get("Status", "")
                availability = row.get("Availability", "0")
                status_info = row.get("StatusInfo", "0")
                size_bytes = int(row.get("Size", 0) or 0)

                health = "OK" if status.upper() == "OK" else status
                issues = []
                if status.upper() not in ("OK", ""):
                    issues.append(f"Estado SMART: {status}")
                try:
                    avail_int = int(availability)
                    if avail_int not in (0, 3):
                        issues.append(f"Disponibilidad: {_availability_desc(avail_int)}")
                except Exception:
                    pass

                results.append({
                    "model": row.get("Caption", "N/D").strip(),
                    "size_gb": round(size_bytes / (1024**3), 1),
                    "interface": row.get("InterfaceType", "N/D").strip(),
                    "smart_status": health,
                    "issues": issues,
                    "overall_ok": len(issues) == 0 and status.upper() == "OK",
                })
    except Exception as e:
        results.append({"error": str(e)})

    # Try PowerShell Get-PhysicalDisk for SSD wear
    try:
        ps_cmd = (
            "Get-PhysicalDisk | Select-Object FriendlyName,MediaType,"
            "HealthStatus,OperationalStatus,Size,"
            "AllocatedSize | ConvertTo-Json -Depth 2"
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
            disks = json.loads(raw)
            if isinstance(disks, dict):
                disks = [disks]
            for d in disks:
                health = str(d.get("HealthStatus", ""))
                media = str(d.get("MediaType", ""))
                name = str(d.get("FriendlyName", "N/D"))
                op_status = str(d.get("OperationalStatus", ""))
                size_b = int(d.get("Size", 0) or 0)

                # Find or update matching result
                matched = next(
                    (r for r in results if name[:20] in r.get("model", "")[:20]), None)
                if matched:
                    matched["media_type_ps"] = media
                    matched["health_ps"] = health
                    if health.lower() not in ("healthy", ""):
                        matched["issues"].append(f"Salud: {health}")
                        matched["overall_ok"] = False
                else:
                    results.append({
                        "model": name,
                        "size_gb": round(size_b / (1024**3), 1),
                        "interface": "N/D",
                        "smart_status": health,
                        "media_type_ps": media,
                        "issues": [] if health.lower() == "healthy" else [f"Salud: {health}"],
                        "overall_ok": health.lower() == "healthy",
                    })
    except Exception:
        pass

    return results


def _availability_desc(code):
    descriptions = {
        1: "Otro", 2: "Desconocido", 3: "Running/Full Power",
        4: "Warning", 5: "In Test", 6: "Not Applicable",
        7: "Power Off", 8: "Off Line", 9: "Off Duty",
        10: "Degraded", 11: "Not Installed",
        12: "Install Error", 13: "Power Save-Unknown",
        14: "Power Save-Low Power", 15: "Power Save-Standby",
        16: "Power Cycle", 17: "Power Save-Warning",
    }
    return descriptions.get(code, f"Código {code}")
