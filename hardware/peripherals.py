"""
TecoQC - Detección de periféricos especiales (SD, pantalla táctil, biométricos)
"""


def get_sd_card_reader():
    """Detecta lectores de tarjeta SD via WMI Win32_PnPEntity / Win32_DiskDrive.

    Retorna: {"found": bool, "name": str, "status": str}
    """
    result = {"found": False, "name": "", "status": "No detectado"}
    try:
        import wmi
        c = wmi.WMI()

        # Primary: search Win32_PnPEntity by name
        keywords = ["%SD%", "%Memory Card%", "%Card Reader%", "%SD Card%"]
        for kw in keywords:
            try:
                devices = c.query(
                    f"SELECT Name, Status FROM Win32_PnPEntity "
                    f"WHERE Name LIKE '{kw}'"
                )
                if devices:
                    d = devices[0]
                    result["found"] = True
                    result["name"] = (d.Name or "").strip()
                    result["status"] = (d.Status or "OK").strip()
                    return result
            except Exception:
                continue

        # Fallback: Win32_DiskDrive with Removable MediaType
        try:
            drives = c.Win32_DiskDrive()
            for drive in drives:
                media_type = (getattr(drive, "MediaType", "") or "").lower()
                model = (getattr(drive, "Model", "") or "").lower()
                if "removable" in media_type or "sd" in model or "card reader" in model:
                    result["found"] = True
                    result["name"] = (drive.Model or "").strip()
                    result["status"] = "OK"
                    return result
        except Exception:
            pass

    except ImportError:
        pass
    except Exception:
        pass

    return result


def get_touchscreen_info():
    """Detecta pantalla táctil via WMI Win32_PnPEntity.

    Retorna: {"found": bool, "devices": list[str]}
    """
    result = {"found": False, "devices": []}
    try:
        import wmi
        c = wmi.WMI()

        keywords = [
            "%HID-compliant touch screen%",
            "%touch screen%",
            "%touchscreen%",
            "%touch digitizer%",
        ]
        found_names = []
        for kw in keywords:
            try:
                devices = c.query(
                    f"SELECT Name FROM Win32_PnPEntity WHERE Name LIKE '{kw}'"
                )
                for d in devices:
                    name = (d.Name or "").strip()
                    if name and name not in found_names:
                        found_names.append(name)
            except Exception:
                continue

        if found_names:
            result["found"] = True
            result["devices"] = found_names

    except ImportError:
        pass
    except Exception:
        pass

    return result


def get_biometric_devices():
    """Detecta lector de huellas dactilares y cámara IR (Windows Hello) via WMI.

    Retorna:
        {
            "fingerprint": {"found": bool, "name": str},
            "ir_camera":   {"found": bool, "name": str},
        }
    """
    result = {
        "fingerprint": {"found": False, "name": ""},
        "ir_camera":   {"found": False, "name": ""},
    }
    try:
        import wmi
        c = wmi.WMI()

        fingerprint_keywords = [
            "%fingerprint%",
            "%biometric%",
            "%Windows Hello%",
            "%finger%",
        ]
        ir_keywords = [
            "%IR Camera%",
            "%infrared camera%",
            "%Windows Hello Camera%",
            "%IR sensor%",
        ]

        for kw in fingerprint_keywords:
            try:
                devices = c.query(
                    f"SELECT Name FROM Win32_PnPEntity WHERE Name LIKE '{kw}'"
                )
                if devices:
                    result["fingerprint"]["found"] = True
                    result["fingerprint"]["name"] = (devices[0].Name or "").strip()
                    break
            except Exception:
                continue

        for kw in ir_keywords:
            try:
                devices = c.query(
                    f"SELECT Name FROM Win32_PnPEntity WHERE Name LIKE '{kw}'"
                )
                if devices:
                    result["ir_camera"]["found"] = True
                    result["ir_camera"]["name"] = (devices[0].Name or "").strip()
                    break
            except Exception:
                continue

    except ImportError:
        pass
    except Exception:
        pass

    return result


def get_all_peripherals():
    """Llama a las 3 funciones de detección y retorna un dict combinado.

    Retorna:
        {
            "sd_reader":  {"found": bool, "name": str, "status": str},
            "touchscreen": {"found": bool, "devices": list},
            "fingerprint": {"found": bool, "name": str},
            "ir_camera":   {"found": bool, "name": str},
        }
    """
    bio = get_biometric_devices()
    return {
        "sd_reader":   get_sd_card_reader(),
        "touchscreen": get_touchscreen_info(),
        "fingerprint": bio["fingerprint"],
        "ir_camera":   bio["ir_camera"],
    }
