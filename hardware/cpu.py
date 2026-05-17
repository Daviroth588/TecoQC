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


def _find_lhm_dll() -> str:
    """Busca LibreHardwareMonitorLib.dll en assets/ relativo al proyecto."""
    import sys
    # El archivo real dentro del zip de LHM se llama LibreHardwareMonitorLib.dll
    dll_names = ["LibreHardwareMonitorLib.dll", "LibreHardwareMonitor.dll"]
    candidates = []
    if getattr(sys, "frozen", False):
        base = os.path.dirname(sys.executable)
        for name in dll_names:
            candidates.append(os.path.join(base, "assets", name))
            candidates.append(os.path.join(base, name))
    else:
        here = os.path.dirname(os.path.abspath(__file__))
        root = os.path.dirname(here)
        for name in dll_names:
            candidates.append(os.path.join(root, "assets", name))
            candidates.append(os.path.join(here, name))
    for path in candidates:
        if os.path.exists(path):
            return path
    return ""


def _get_temperature_lhm() -> dict:
    """
    Lee temperaturas usando LibreHardwareMonitor.dll via pythonnet (clr).
    Requiere: assets/LibreHardwareMonitor.dll + pip install pythonnet
    Requiere: ejecutar como Administrador (driver WinRing0).
    """
    temps = {}
    dll_path = _find_lhm_dll()
    if not dll_path:
        return temps
    try:
        import clr  # pythonnet
        clr.AddReference(dll_path)
        from LibreHardwareMonitor import Hardware  # type: ignore

        computer = Hardware.Computer()
        computer.IsCpuEnabled = True
        computer.Open()

        for hw in computer.Hardware:
            hw.Update()
            for sensor in hw.Sensors:
                if sensor.SensorType == Hardware.SensorType.Temperature:
                    val = sensor.Value
                    if val is not None:
                        name = str(sensor.Name)
                        temps[name] = round(float(val), 1)
            # Sub-hardware (e.g. CPU cores inside package)
            for sub in hw.SubHardware:
                sub.Update()
                for sensor in sub.Sensors:
                    if sensor.SensorType == Hardware.SensorType.Temperature:
                        val = sensor.Value
                        if val is not None:
                            temps[str(sensor.Name)] = round(float(val), 1)

        computer.Close()
    except Exception:
        pass
    return temps


def get_cpu_temperature() -> dict:
    """
    Retorna dict {nombre_sensor: temperatura_celsius}.
    Prioridad: LibreHardwareMonitor.dll → MSAcpi → OpenHardwareMonitor → psutil
    """
    # 1. LibreHardwareMonitor (más completo, igual que HWMonitor)
    temps = _get_temperature_lhm()
    if temps:
        return temps

    # 2. WMI MSAcpi_ThermalZoneTemperature (ACPI, funciona en algunos equipos)
    try:
        import wmi
        c = wmi.WMI(namespace="root/wmi")
        thermal = c.MSAcpi_ThermalZoneTemperature()
        if thermal:
            for i, t in enumerate(thermal):
                celsius = round(t.CurrentTemperature / 10.0 - 273.15, 1)
                temps[f"Zona Térmica {i+1}"] = celsius
    except Exception:
        pass
    if temps:
        return temps

    # 3. Open Hardware Monitor WMI (si el usuario lo tiene corriendo)
    try:
        import wmi
        c = wmi.WMI(namespace="root/OpenHardwareMonitor")
        for s in c.Sensor():
            if s.SensorType == "Temperature" and "CPU" in (s.Name or ""):
                temps[s.Name] = s.Value
    except Exception:
        pass
    if temps:
        return temps

    # 4. psutil (Linux/Mac; rara vez funciona en Windows)
    try:
        import psutil
        sensors = psutil.sensors_temperatures()
        if sensors:
            for key, entries in sensors.items():
                for entry in entries:
                    temps[entry.label or key] = entry.current
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
