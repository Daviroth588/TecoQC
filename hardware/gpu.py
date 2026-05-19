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


_VIRTUAL_GPU_KEYWORDS = [
    "parsec", "virtual", "remote desktop", "microsoft basic display",
    "teamviewer", "virtualbox", "vmware", "citrix", "indirect display",
    "generic pnp", "display only", "moonlight", "sunshine",
]


def _is_virtual_adapter(name: str) -> bool:
    n = name.lower()
    return any(kw in n for kw in _VIRTUAL_GPU_KEYWORDS)


def _gpu_priority(gpu: dict) -> int:
    """Lower number = higher priority. Discrete > iGPU > virtual."""
    if _is_virtual_adapter(gpu.get("name", "")):
        return 99
    v = gpu.get("vendor", "")
    if v in ("NVIDIA", "AMD"):
        return 0
    if v == "Intel":
        return 1
    return 2


def get_wmi_gpu_info():
    """Obtiene info de GPU via WMI, filtrando adaptadores virtuales."""
    gpus = []
    try:
        import wmi
        c = wmi.WMI()
        adapters = c.Win32_VideoController()
        for a in adapters:
            name = (a.Name or "Desconocido").strip()
            gpu = {
                "name": name,
                "driver_version": (a.DriverVersion or "").strip(),
                "vendor": _detect_vendor(name),
                "vram_total_mb": _bytes_to_mb(a.AdapterRAM),
                "status": (a.Status or "").strip(),
                "video_mode": f"{a.CurrentHorizontalResolution or 0}x"
                              f"{a.CurrentVerticalResolution or 0} "
                              f"@{a.CurrentRefreshRate or 0}Hz",
                "is_virtual": _is_virtual_adapter(name),
            }
            gpus.append(gpu)
    except Exception as e:
        gpus.append({"name": "Error", "error": str(e)})
        return gpus

    # Sort: discrete first, iGPU second, virtual last
    gpus.sort(key=_gpu_priority)
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


def get_gpu_utilization():
    """
    Retorna dict {gpu_name: utilization_pct} para cada GPU.
    Fuentes: nvidia-smi → Win32_PerfFormattedData (Windows 10+) → N/D
    """
    result = {}

    # 1. NVIDIA via nvidia-smi (más confiable)
    try:
        proc = subprocess.run(
            ["nvidia-smi",
             "--query-gpu=name,utilization.gpu,utilization.memory",
             "--format=csv,noheader,nounits"],
            capture_output=True, text=True, timeout=5,
        )
        if proc.returncode == 0:
            for line in proc.stdout.strip().splitlines():
                parts = [p.strip() for p in line.split(",")]
                if len(parts) >= 2:
                    name = parts[0]
                    util = _safe_float(parts[1])
                    result[name] = {"gpu_pct": util,
                                    "mem_pct": _safe_float(parts[2]) if len(parts) > 2 else 0}
    except Exception:
        pass

    # 2. Windows Performance Counters (AMD + Intel, Windows 10+)
    if not result:
        try:
            import wmi
            c = wmi.WMI()
            perf = c.Win32_PerfFormattedData_GPUPerformanceCounters_GPUEngine()
            totals = {}
            for item in perf:
                name = item.Name or ""
                # Name: "pid_XXX_luid_0xXXX_phys_0_eng_0_engtype_3D"
                if "engtype_3D" in name or "engtype_Graphics" in name:
                    util = item.UtilizationPercentage
                    if util is not None:
                        # Extract physical adapter index from name
                        phys = "0"
                        for part in name.split("_"):
                            if part.isdigit():
                                phys = part
                                break
                        key = f"GPU {phys}"
                        totals[key] = totals.get(key, 0) + float(util)
            for key, val in totals.items():
                result[key] = {"gpu_pct": min(100.0, val), "mem_pct": 0}
        except Exception:
            pass

    return result


def get_gpu_live_stats():
    """
    Retorna stats en tiempo real: utilización, temperatura, VRAM.
    Usado para el monitor en tiempo real del panel GPU.
    """
    stats = {"entries": []}
    util = get_gpu_utilization()

    # NVIDIA: usa nvidia-smi para datos completos en un solo call
    try:
        proc = subprocess.run(
            ["nvidia-smi",
             "--query-gpu=name,utilization.gpu,utilization.memory,"
             "memory.used,memory.total,temperature.gpu",
             "--format=csv,noheader,nounits"],
            capture_output=True, text=True, timeout=5,
        )
        if proc.returncode == 0:
            for line in proc.stdout.strip().splitlines():
                parts = [p.strip() for p in line.split(",")]
                if len(parts) >= 6:
                    stats["entries"].append({
                        "name": parts[0],
                        "gpu_pct": _safe_float(parts[1]),
                        "mem_pct": _safe_float(parts[2]),
                        "vram_used_mb": _safe_int(parts[3]),
                        "vram_total_mb": _safe_int(parts[4]),
                        "temp_c": _safe_float(parts[5]),
                        "source": "nvidia-smi",
                    })
    except Exception:
        pass

    # AMD/Intel: combinar WMI VideoController + utilización de Performance Counters
    if not stats["entries"]:
        try:
            import wmi
            c = wmi.WMI()
            for a in c.Win32_VideoController():
                name = (a.Name or "GPU").strip()
                if _is_virtual_adapter(name):
                    continue
                entry = {
                    "name": name,
                    "gpu_pct": 0.0,
                    "mem_pct": 0.0,
                    "vram_used_mb": 0,
                    "vram_total_mb": _bytes_to_mb(a.AdapterRAM),
                    "temp_c": None,
                    "source": "wmi",
                }
                # Look up utilization from Performance Counters
                for key, val in util.items():
                    entry["gpu_pct"] = val.get("gpu_pct", 0)
                    break
                stats["entries"].append(entry)
        except Exception:
            pass

        # Temperature from OHM if available
        temps = get_gpu_temperature_wmi()
        if temps and stats["entries"]:
            for key, val in temps.items():
                stats["entries"][0]["temp_c"] = val
                break

    return stats


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
