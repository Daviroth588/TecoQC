"""
TecoQC - Escáner del Registro de Eventos de Windows (últimos 30 días)
"""

import subprocess
import datetime


def scan_hardware_events(days=30):
    """
    Escanea el Event Log de Windows por errores de hardware críticos.
    Retorna lista de eventos agrupados por categoría.
    """
    results = {
        "disk_errors": [],
        "memory_errors": [],
        "driver_errors": [],
        "critical_errors": [],
        "summary": {},
        "error": None,
    }

    since = (datetime.datetime.now() - datetime.timedelta(days=days)).strftime(
        "%Y-%m-%dT%H:%M:%S"
    )

    queries = [
        ("disk_errors",    "System",      "7",   "disk"),
        ("driver_errors",  "System",      "7",   "driver"),
        ("critical_errors","System",      "1",   None),
        ("memory_errors",  "System",      "7",   "memory"),
    ]

    # Try PowerShell Get-EventLog approach
    try:
        for category, log_name, level, keyword in queries:
            ps_cmd = (
                f"Get-WinEvent -FilterHashtable @{{LogName='{log_name}';"
                f"Level={level};StartTime='{since}'}} "
                f"-MaxEvents 20 -ErrorAction SilentlyContinue | "
                f"Select-Object TimeCreated,Id,LevelDisplayName,Message | "
                f"ConvertTo-Json -Depth 2"
            )
            proc = subprocess.run(
                ["powershell", "-NoProfile", "-NonInteractive",
                 "-Command", ps_cmd],
                capture_output=True, text=True, timeout=15,
            )
            if proc.returncode == 0 and proc.stdout.strip():
                import json
                raw = proc.stdout.strip()
                if raw.startswith("{"):
                    raw = f"[{raw}]"
                events = json.loads(raw)
                if isinstance(events, dict):
                    events = [events]
                for ev in events[:10]:
                    msg = str(ev.get("Message", ""))[:120]
                    if keyword and keyword.lower() not in msg.lower():
                        continue
                    results[category].append({
                        "time": str(ev.get("TimeCreated", ""))[:19],
                        "event_id": ev.get("Id", 0),
                        "level": str(ev.get("LevelDisplayName", "")),
                        "message": msg,
                    })
    except Exception as e:
        results["error"] = str(e)

    # Fallback: use wevtutil for basic counts
    if results["error"]:
        try:
            for log_name, level in [("System", "2"), ("Application", "2")]:
                cmd = [
                    "wevtutil", "qe", log_name,
                    f"/q:*[System[(Level<={level}) and TimeCreated[timediff(@SystemTime) <= {days * 86400000}]]]",
                    "/c:20", "/f:text",
                ]
                proc = subprocess.run(cmd, capture_output=True, text=True, timeout=10)
                if proc.returncode == 0:
                    lines = proc.stdout.split("\n")
                    count = sum(1 for l in lines if "Level:" in l and "Error" in l)
                    if count > 0:
                        results["critical_errors"].append({
                            "time": "",
                            "event_id": 0,
                            "level": "Error",
                            "message": f"{count} errores en {log_name} (últimos {days} días)",
                        })
            results["error"] = None
        except Exception as e2:
            results["error"] = str(e2)

    results["summary"] = {
        "disk_error_count":    len(results["disk_errors"]),
        "memory_error_count":  len(results["memory_errors"]),
        "driver_error_count":  len(results["driver_errors"]),
        "critical_error_count": len(results["critical_errors"]),
        "total_issues":        (len(results["disk_errors"]) +
                                len(results["memory_errors"]) +
                                len(results["driver_errors"]) +
                                len(results["critical_errors"])),
        "days_scanned": days,
    }
    return results


def get_driver_errors_wmi():
    """Detecta controladores con error en Device Manager via WMI."""
    errors = []
    try:
        import wmi
        c = wmi.WMI()
        devices = c.Win32_PnPEntity()
        for d in devices:
            code = getattr(d, "ConfigManagerErrorCode", 0) or 0
            if code != 0:
                errors.append({
                    "name": (d.Name or "Desconocido").strip(),
                    "error_code": code,
                    "description": _error_code_desc(code),
                    "device_id": (d.DeviceID or "")[:60],
                    "manufacturer": (d.Manufacturer or "").strip(),
                })
    except Exception as e:
        errors.append({"error": str(e)})
    return errors


def _error_code_desc(code):
    codes = {
        1:  "Este dispositivo no está configurado correctamente",
        3:  "El controlador de este dispositivo puede estar dañado",
        10: "Este dispositivo no puede iniciar",
        12: "Este dispositivo no puede encontrar suficientes recursos libres",
        14: "Este dispositivo no puede funcionar correctamente hasta reiniciar",
        16: "Windows no puede identificar todos los recursos que usa este dispositivo",
        18: "Reinstale los controladores para este dispositivo",
        19: "Windows no puede iniciar este dispositivo (código 19)",
        21: "Windows está eliminando este dispositivo",
        22: "Este dispositivo está deshabilitado",
        24: "Este dispositivo no está presente, no funciona correctamente",
        28: "Los controladores no están instalados",
        29: "El dispositivo está deshabilitado (no hay configuración de firmware)",
        31: "Este dispositivo no funciona correctamente",
        32: "Un controlador de servicio para este dispositivo ha sido deshabilitado",
        33: "Windows no puede determinar qué recursos requiere este dispositivo",
        34: "Windows no puede determinar la configuración para este dispositivo",
        35: "El firmware del sistema del equipo no incluye información suficiente",
        36: "Este dispositivo solicita una interrupción PCI pero está configurado para ISA",
        37: "Windows no puede inicializar el controlador del dispositivo para el hardware",
        38: "Windows no puede cargar el controlador porque una versión anterior aún está en memoria",
        39: "Windows no puede cargar el controlador del dispositivo",
        40: "Windows no puede acceder a esta clave de registro de hardware",
        41: "Windows cargó el controlador del dispositivo, pero no puede encontrar el dispositivo",
        43: "Windows ha detenido este dispositivo porque ha reportado problemas",
        44: "Una aplicación o servicio ha cerrado este dispositivo",
        45: "Actualmente no está conectado al equipo",
        46: "Windows no puede acceder a este hardware porque el sistema operativo está terminando",
        47: "Windows no puede usar este dispositivo de hardware (memoria agotada)",
        48: "El software del controlador de este dispositivo ha sido bloqueado",
        49: "Windows no puede iniciar nuevos dispositivos de hardware",
        52: "Windows no puede verificar la firma digital de los controladores",
    }
    return codes.get(code, f"Código de error {code}")
