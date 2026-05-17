"""
TecoQC - Detección e información de GPU (NVIDIA / AMD / Intel)
"""

import subprocess
import re


def get_nvidia_info():
    """Obtiene info de GPU NVIDIA via nvidia-smi."""
    info = {}
    try:
        result = subprocess.run(
            [
                "nvidia-smi",
                "--query-gpu=name,memory.total,memory.used,memory.free,"
                "temperature.gpu,utilization.gpu,driver_version",
                "--format=csv,noheader,nounits",
            ],
            capture_output=True,
            text=True,
            timeout=10,
        )
        if result.returncode == 0 and result.stdout.strip():
            lines = result.stdout.strip().splitlines()
            gpus = []
            for line in lines:
                parts = [p.strip() for p in line.split(",")]
                if len(parts) >= 7:
                    gpus.append({
                        "name": parts[0],
                        "vram_total_mb": _safe_int(parts[1]),
                        "vram_used_mb": _safe_int(parts[2]),
                        "vram_free_mb": _safe_int(parts[3]),
                        "temperature": _safe_float(parts[4]),
                        "utilization_pct": _safe_float(parts[5]),
                        "driver_version": parts[6],
                        "vendor": "NVIDIA",
                    })
            info["gpus"] = gpus
            info["available"] = True
    except FileNotFoundError:
        info["available"] = False
        info["error"] = "nvidia-smi no encontrado"
    except subprocess.TimeoutExpired:
        info["available"] = False
        info["error"] = "Tiempo de espera agotado"
    except Exception as e:
        info["available"] = False
        info["error"] = str(e)
    return info


def get_wmi_gpu_info():
    """Obtiene info de GPU via WMI (funciona para AMD, Intel, NVIDIA)."""
    gpus = []
    try:
        import wmi
        c = wmi.WMI()
        adapters = c.Win32_VideoController()
        for a in adapters:
            gpu = {
                "name": (a.Name or "Desconocido").strip(),
                "driver_version": (a.DriverVersion or "").strip(),
                "vendor": _detect_vendor((a.Name or "")),
                "vram_total_mb": _bytes_to_mb(a.AdapterRAM),
                "status": (a.Status or "").strip(),
                "video_mode": f"{a.CurrentHorizontalResolution or 0}x"
                              f"{a.CurrentVerticalResolution or 0} "
                              f"@{a.CurrentRefreshRate or 0}Hz",
            }
            gpus.append(gpu)
    except Exception as e:
        gpus.append({"name": "Error", "error": str(e)})
    return gpus


def get_gpu_temperature_wmi():
    """Intenta obtener temperatura de GPU via Open Hardware Monitor WMI."""
    temps = {}
    try:
        import wmi
        c = wmi.WMI(namespace="root/OpenHardwareMonitor")
        sensors = c.Sensor()
        for s in sensors:
            if s.SensorType == "Temperature" and "GPU" in (s.Name or ""):
                temps[s.Name] = s.Value
    except Exception:
        pass
    return temps


def get_all_gpu_info():
    """Recopila toda la información de GPU disponible."""
    result = {
        "wmi_gpus": get_wmi_gpu_info(),
        "nvidia": get_nvidia_info(),
        "temperatures": get_gpu_temperature_wmi(),
    }
    return result


def _safe_int(val):
    try:
        return int(str(val).strip())
    except Exception:
        return 0


def _safe_float(val):
    try:
        return float(str(val).strip())
    except Exception:
        return 0.0


def _bytes_to_mb(val):
    try:
        if val is None:
            return 0
        return round(int(val) / (1024 * 1024))
    except Exception:
        return 0


def _detect_vendor(name):
    name_lower = name.lower()
    if "nvidia" in name_lower or "geforce" in name_lower or "quadro" in name_lower:
        return "NVIDIA"
    if "amd" in name_lower or "radeon" in name_lower or "rx " in name_lower:
        return "AMD"
    if "intel" in name_lower or "iris" in name_lower or "uhd" in name_lower:
        return "Intel"
    return "Desconocido"
