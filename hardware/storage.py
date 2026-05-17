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
