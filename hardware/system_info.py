"""
TecoQC - Información del sistema (OS, Placa base, BIOS)
"""

import platform
import subprocess
import os


def get_os_info():
    """Retorna información del sistema operativo."""
    info = {}
    try:
        info["os_name"] = platform.system()
        info["os_version"] = platform.version()
        info["os_release"] = platform.release()
        info["os_full"] = f"{platform.system()} {platform.release()}"
        info["architecture"] = platform.machine()
        info["hostname"] = platform.node()
        info["python_version"] = platform.python_version()
    except Exception as e:
        info["error"] = str(e)

    # Try to get Windows edition from registry
    try:
        import winreg
        key = winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE,
                             r"SOFTWARE\Microsoft\Windows NT\CurrentVersion")
        info["os_edition"] = winreg.QueryValueEx(key, "EditionID")[0]
        info["build_number"] = winreg.QueryValueEx(key, "CurrentBuildNumber")[0]
        info["product_name"] = winreg.QueryValueEx(key, "ProductName")[0]
        winreg.CloseKey(key)
    except Exception:
        pass

    return info


def get_motherboard_info():
    """Retorna información de la placa base vía WMI."""
    info = {}
    try:
        import wmi
        c = wmi.WMI()
        boards = c.Win32_BaseBoard()
        if boards:
            b = boards[0]
            info["manufacturer"] = (b.Manufacturer or "").strip()
            info["product"] = (b.Product or "").strip()
            info["serial"] = (b.SerialNumber or "").strip()
            info["version"] = (b.Version or "").strip()
    except Exception as e:
        info["error"] = str(e)

    # Also try Win32_ComputerSystemProduct for model
    try:
        import wmi
        c = wmi.WMI()
        products = c.Win32_ComputerSystemProduct()
        if products:
            p = products[0]
            info["model_name"] = (p.Name or "").strip()
            info["vendor"] = (p.Vendor or "").strip()
            if not info.get("serial"):
                info["serial"] = (p.IdentifyingNumber or "").strip()
    except Exception:
        pass

    # Win32_ComputerSystem for make/model
    try:
        import wmi
        c = wmi.WMI()
        systems = c.Win32_ComputerSystem()
        if systems:
            s = systems[0]
            info["make"] = (s.Manufacturer or "").strip()
            info["model"] = (s.Model or "").strip()
    except Exception:
        pass

    return info


def get_bios_info():
    """Retorna información del BIOS vía WMI."""
    info = {}
    try:
        import wmi
        c = wmi.WMI()
        bioses = c.Win32_BIOS()
        if bioses:
            b = bioses[0]
            info["manufacturer"] = (b.Manufacturer or "").strip()
            info["version"] = (b.SMBIOSBIOSVersion or "").strip()
            info["release_date"] = (b.ReleaseDate or "").strip()
            info["serial_number"] = (b.SerialNumber or "").strip()
    except Exception as e:
        info["error"] = str(e)
    return info


def get_all_system_info():
    """Recopila toda la información del sistema."""
    return {
        "os": get_os_info(),
        "motherboard": get_motherboard_info(),
        "bios": get_bios_info(),
    }
