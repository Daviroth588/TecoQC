"""
TecoQC - Información de memoria RAM (slots, velocidad, tipo)
"""


def get_memory_info():
    """Retorna información de uso de RAM via psutil."""
    info = {}
    try:
        import psutil
        vm = psutil.virtual_memory()
        info["total_bytes"] = vm.total
        info["available_bytes"] = vm.available
        info["used_bytes"] = vm.used
        info["percent"] = vm.percent
        info["total_gb"] = round(vm.total / (1024**3), 2)
        info["available_gb"] = round(vm.available / (1024**3), 2)
        info["used_gb"] = round(vm.used / (1024**3), 2)
    except Exception as e:
        info["error"] = str(e)
    return info


def get_ram_slots_info():
    """Retorna información detallada de los slots de RAM via WMI."""
    slots = []
    try:
        import wmi
        c = wmi.WMI()
        modules = c.Win32_PhysicalMemory()
        for m in modules:
            slot = {
                "bank_label": (m.BankLabel or "").strip(),
                "device_locator": (m.DeviceLocator or "").strip(),
                "capacity_bytes": m.Capacity or 0,
                "capacity_gb": round((m.Capacity or 0) / (1024**3), 2),
                "speed_mhz": m.Speed or 0,
                "manufacturer": (m.Manufacturer or "").strip(),
                "part_number": (m.PartNumber or "").strip(),
                "serial_number": (m.SerialNumber or "").strip(),
                "memory_type": _memory_type_name(m.MemoryType),
                "form_factor": _form_factor_name(m.FormFactor),
            }
            slots.append(slot)
    except Exception as e:
        slots.append({"error": str(e)})
    return slots


def get_physical_memory_array():
    """Retorna info del array de memoria física (slots totales)."""
    info = {}
    try:
        import wmi
        c = wmi.WMI()
        arrays = c.Win32_PhysicalMemoryArray()
        if arrays:
            a = arrays[0]
            info["max_capacity_kb"] = a.MaxCapacity or 0
            info["max_capacity_gb"] = round((a.MaxCapacity or 0) / (1024**2), 2)
            info["memory_devices"] = a.MemoryDevices or 0
    except Exception as e:
        info["error"] = str(e)
    return info


def run_memory_test():
    """Prueba básica de asignación de memoria."""
    import time
    result = {"passed": False, "error": None, "allocated_mb": 0, "time_ms": 0}
    try:
        test_size = 256 * 1024 * 1024  # 256 MB
        start = time.time()
        data = bytearray(test_size)
        # Write pattern
        for i in range(0, test_size, 4096):
            data[i] = 0xAA
        # Read/verify pattern
        for i in range(0, test_size, 4096):
            if data[i] != 0xAA:
                result["error"] = f"Error de verificación en offset {i}"
                return result
        del data
        elapsed_ms = round((time.time() - start) * 1000)
        result["passed"] = True
        result["allocated_mb"] = test_size // (1024 * 1024)
        result["time_ms"] = elapsed_ms
    except MemoryError as e:
        result["error"] = f"Sin memoria suficiente: {e}"
    except Exception as e:
        result["error"] = str(e)
    return result


def _memory_type_name(code):
    types = {
        0: "Desconocido", 1: "Otro", 2: "DRAM", 3: "SDRAM",
        4: "SGRAM", 5: "RDRAM", 6: "DDR", 7: "DDR2",
        8: "DDR2 FB-DIMM", 20: "DDR3", 21: "FBD2",
        24: "DDR4", 26: "LPDDR", 27: "LPDDR2",
        28: "LPDDR3", 29: "LPDDR4", 34: "DDR5", 35: "LPDDR5",
    }
    return types.get(code, f"Tipo {code}")


def _form_factor_name(code):
    factors = {
        0: "Desconocido", 1: "Otro", 2: "SIP", 3: "DIP",
        4: "ZIP", 5: "SOJ", 6: "Propietario", 7: "SIMM",
        8: "DIMM", 9: "TSOP", 10: "PGA", 11: "RIMM",
        12: "SODIMM", 13: "SRIMM", 14: "SMD", 15: "SSMP",
        16: "QFP", 17: "TQFP", 18: "SOIC", 19: "LCC",
        20: "PLCC", 21: "BGA", 22: "FPBGA", 23: "LGA",
    }
    return factors.get(code, f"Factor {code}")
