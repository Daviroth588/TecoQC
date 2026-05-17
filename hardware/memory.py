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


def run_memory_test(size_mb=256, progress_cb=None, stop_event=None):
    """
    Prueba completa de RAM con múltiples patrones.

    Patrones ejecutados (cada uno escribe toda la región y verifica):
      1. Ceros     (0x00) — detecta bits pegados en 1
      2. Unos      (0xFF) — detecta bits pegados en 0
      3. Alternado (0xAA) — detecta acoplamiento entre bits
      4. Inverso   (0x55) — complemento del anterior
      5. Aleatorio         — detecta errores de datos no predecibles
      6. Dirección         — cada byte contiene su dirección (mod 256)

    progress_cb(phase_name, phase_index, total_phases, phase_pct, errors_so_far)
    stop_event: threading.Event — si se activa, cancela la prueba.
    """
    import time, random, struct

    PATTERNS = [
        ("Ceros (0x00)",      bytes([0x00])),
        ("Unos (0xFF)",       bytes([0xFF])),
        ("Alternado (0xAA)",  bytes([0xAA])),
        ("Inverso (0x55)",    bytes([0x55])),
        ("Aleatorio",         None),          # None → generado dinámicamente
        ("Dirección",         None),          # None → i % 256 por chunk
    ]

    total_phases = len(PATTERNS)
    size_bytes   = size_mb * 1024 * 1024
    chunk        = 4096          # bytes por verificación granular
    total_errors = 0
    phase_results = []

    result = {
        "passed":        False,
        "error":         None,
        "allocated_mb":  size_mb,
        "time_ms":       0,
        "total_errors":  0,
        "phases":        [],
        "cancelled":     False,
    }

    def _cb(name, idx, pct, errs):
        if progress_cb:
            try:
                progress_cb(name, idx, total_phases, pct, errs)
            except Exception:
                pass

    def _stopped():
        return stop_event is not None and stop_event.is_set()

    start_all = time.time()

    try:
        buf = bytearray(size_bytes)
    except MemoryError:
        # If full size fails, try half
        try:
            size_mb  = size_mb // 2
            size_bytes = size_mb * 1024 * 1024
            buf = bytearray(size_bytes)
            result["allocated_mb"] = size_mb
        except MemoryError as e:
            result["error"] = f"Memoria insuficiente para la prueba: {e}"
            return result

    try:
        for phase_idx, (name, pattern) in enumerate(PATTERNS):
            if _stopped():
                result["cancelled"] = True
                break

            phase_errors = 0
            phase_start  = time.time()

            # ── Build write data ──────────────────────────────────────
            if pattern is not None:
                # Repeat fixed byte
                fill_byte = pattern[0]
                for i in range(size_bytes):
                    buf[i] = fill_byte
            elif name.startswith("Aleat"):
                # Random fill (use struct for speed on large buffers)
                rng = random.Random(0xDEADBEEF)
                rand_chunk = 65536
                for off in range(0, size_bytes, rand_chunk):
                    end = min(off + rand_chunk, size_bytes)
                    length = end - off
                    rand_bytes = bytes(rng.getrandbits(8) for _ in range(length))
                    buf[off:end] = rand_bytes
            else:
                # Address pattern: buf[i] = i % 256
                for i in range(size_bytes):
                    buf[i] = i & 0xFF

            _cb(name, phase_idx, 0.0, total_errors)

            # ── Verify ────────────────────────────────────────────────
            if pattern is not None:
                expected = pattern[0]
                for off in range(0, size_bytes, chunk):
                    if _stopped():
                        break
                    end = min(off + chunk, size_bytes)
                    for i in range(off, end):
                        if buf[i] != expected:
                            phase_errors += 1
                    pct = (off + chunk) / size_bytes
                    _cb(name, phase_idx, min(pct, 1.0), total_errors + phase_errors)

            elif name.startswith("Aleat"):
                rng2 = random.Random(0xDEADBEEF)
                rand_chunk = 65536
                for off in range(0, size_bytes, rand_chunk):
                    if _stopped():
                        break
                    end = min(off + rand_chunk, size_bytes)
                    length = end - off
                    expected_bytes = bytes(rng2.getrandbits(8) for _ in range(length))
                    for j, (got, exp) in enumerate(zip(buf[off:end], expected_bytes)):
                        if got != exp:
                            phase_errors += 1
                    pct = (off + rand_chunk) / size_bytes
                    _cb(name, phase_idx, min(pct, 1.0), total_errors + phase_errors)

            else:  # Address
                for off in range(0, size_bytes, chunk):
                    if _stopped():
                        break
                    end = min(off + chunk, size_bytes)
                    for i in range(off, end):
                        if buf[i] != (i & 0xFF):
                            phase_errors += 1
                    pct = (off + chunk) / size_bytes
                    _cb(name, phase_idx, min(pct, 1.0), total_errors + phase_errors)

            phase_ms = round((time.time() - phase_start) * 1000)
            total_errors += phase_errors
            phase_results.append({
                "name":    name,
                "errors":  phase_errors,
                "time_ms": phase_ms,
                "passed":  phase_errors == 0,
            })

            _cb(name, phase_idx, 1.0, total_errors)

    except Exception as e:
        result["error"] = str(e)
    finally:
        del buf

    elapsed_ms = round((time.time() - start_all) * 1000)
    result["time_ms"]      = elapsed_ms
    result["total_errors"] = total_errors
    result["phases"]       = phase_results
    result["passed"]       = (total_errors == 0 and not result["cancelled"]
                               and result["error"] is None)
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
