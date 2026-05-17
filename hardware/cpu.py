"""
TecoQC - Información de CPU, temperatura y uso
"""

import platform
import subprocess


def get_cpu_info():
    """Retorna información estática de la CPU."""
    info = {}
    try:
        import psutil
        info["cores_physical"] = psutil.cpu_count(logical=False) or 0
        info["cores_logical"] = psutil.cpu_count(logical=True) or 0
        freq = psutil.cpu_freq()
        if freq:
            info["freq_max_mhz"] = round(freq.max, 0)
            info["freq_current_mhz"] = round(freq.current, 0)
        else:
            info["freq_max_mhz"] = 0
            info["freq_current_mhz"] = 0
    except Exception as e:
        info["error_psutil"] = str(e)

    # CPU name from WMI
    try:
        import wmi
        c = wmi.WMI()
        cpus = c.Win32_Processor()
        if cpus:
            cpu = cpus[0]
            info["name"] = (cpu.Name or "").strip()
            info["manufacturer"] = (cpu.Manufacturer or "").strip()
            info["max_clock_speed"] = cpu.MaxClockSpeed
            info["number_of_cores"] = cpu.NumberOfCores
            info["number_of_logical_processors"] = cpu.NumberOfLogicalProcessors
            info["architecture"] = cpu.Architecture
            info["socket"] = (cpu.SocketDesignation or "").strip()
    except Exception as e:
        info["error_wmi"] = str(e)

    # Fallback: platform
    if "name" not in info:
        try:
            info["name"] = platform.processor() or "Desconocido"
        except Exception:
            info["name"] = "Desconocido"

    return info


def get_cpu_usage():
    """Retorna el porcentaje de uso actual de la CPU."""
    try:
        import psutil
        return psutil.cpu_percent(interval=0.1)
    except Exception:
        return 0.0


def get_cpu_per_core_usage():
    """Retorna lista de uso por núcleo."""
    try:
        import psutil
        return psutil.cpu_percent(interval=0.1, percpu=True)
    except Exception:
        return []


def get_cpu_temperature():
    """Intenta obtener la temperatura de la CPU."""
    temps = {}

    # Try psutil sensors (works on Linux; limited on Windows)
    try:
        import psutil
        sensors = psutil.sensors_temperatures()
        if sensors:
            for key, entries in sensors.items():
                for entry in entries:
                    label = entry.label or key
                    temps[label] = entry.current
    except Exception:
        pass

    # Try WMI MSAcpi_ThermalZoneTemperature
    try:
        import wmi
        c = wmi.WMI(namespace="root/wmi")
        thermal = c.MSAcpi_ThermalZoneTemperature()
        if thermal:
            for i, t in enumerate(thermal):
                kelvin = t.CurrentTemperature / 10.0
                celsius = kelvin - 273.15
                temps[f"Zona Térmica {i+1}"] = round(celsius, 1)
    except Exception:
        pass

    # Try OHM (Open Hardware Monitor) if available
    try:
        import wmi
        c = wmi.WMI(namespace="root/OpenHardwareMonitor")
        sensors = c.Sensor()
        for s in sensors:
            if s.SensorType == "Temperature" and "CPU" in (s.Name or ""):
                temps[s.Name] = s.Value
    except Exception:
        pass

    return temps


def run_cpu_stress(duration_seconds=10):
    """Ejecuta una prueba de estrés simple de CPU."""
    import threading
    import time

    stop_flag = threading.Event()
    results = {"completed": False, "error": None}

    def worker():
        end_time = time.time() + duration_seconds
        while time.time() < end_time and not stop_flag.is_set():
            # Busy loop
            _ = sum(i * i for i in range(10000))
        results["completed"] = True

    threads = []
    try:
        import psutil
        core_count = psutil.cpu_count(logical=True) or 4
    except Exception:
        core_count = 4

    for _ in range(core_count):
        t = threading.Thread(target=worker, daemon=True)
        t.start()
        threads.append(t)

    return stop_flag, results, threads
