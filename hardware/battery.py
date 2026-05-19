"""
TecoQC - Información de batería (WMI + powercfg)
"""

import subprocess
import re
import os


def get_battery_psutil():
    """Obtiene info básica de batería via psutil."""
    info = {}
    try:
        import psutil
        bat = psutil.sensors_battery()
        if bat is None:
            info["present"] = False
            return info
        info["present"] = True
        info["percent"] = bat.percent
        info["power_plugged"] = bat.power_plugged
        info["secsleft"] = bat.secsleft
        if bat.secsleft > 0 and not bat.power_plugged:
            hours = bat.secsleft // 3600
            mins = (bat.secsleft % 3600) // 60
            info["time_remaining"] = f"{hours}h {mins}m"
        else:
            info["time_remaining"] = "Cargando" if bat.power_plugged else "N/D"
    except Exception as e:
        info["error"] = str(e)
    return info


def get_battery_wmi():
    """Obtiene información detallada de batería via WMI."""
    info = {}
    try:
        import wmi
        c = wmi.WMI()
        batteries = c.Win32_Battery()
        if not batteries:
            info["present"] = False
            return info
        b = batteries[0]
        info["present"] = True
        info["name"] = (b.Name or "").strip()
        info["status"] = _battery_status(b.BatteryStatus)
        info["estimated_charge_remaining"] = b.EstimatedChargeRemaining
        info["estimated_run_time"] = b.EstimatedRunTime
        info["design_capacity"] = b.DesignCapacity
        info["full_charge_capacity"] = b.FullChargeCapacity
        if b.DesignCapacity and b.FullChargeCapacity and b.DesignCapacity > 0:
            wear = 100 - round(
                (b.FullChargeCapacity / b.DesignCapacity) * 100, 1
            )
            info["wear_level_pct"] = max(0, wear)
            info["health_pct"] = round(
                (b.FullChargeCapacity / b.DesignCapacity) * 100, 1
            )
        info["chemistry"] = _battery_chemistry(b.Chemistry)
    except Exception as e:
        info["error"] = str(e)

    # Also get from Win32_PortableBattery for more details
    try:
        import wmi
        c = wmi.WMI()
        port_bats = c.Win32_PortableBattery()
        if port_bats:
            pb = port_bats[0]
            info["design_capacity_mwh"] = pb.DesignCapacity
            info["manufacturer"] = (pb.Manufacturer or "").strip()
            info["manufacture_date"] = (pb.ManufactureDate or "").strip()
            info["cycle_count"] = pb.CycleCount
    except Exception:
        pass

    return info


def run_battery_report():
    """Ejecuta powercfg /batteryreport y retorna la ruta del archivo."""
    result = {"path": None, "error": None, "available": False}
    try:
        from config import get_data_dir
        output_path = os.path.join(get_data_dir(), "battery_report.html")
        proc = subprocess.run(
            ["powercfg", "/batteryreport",
             "/output", output_path, "/xml"],
            capture_output=True,
            text=True,
            timeout=30,
        )
        if proc.returncode == 0 and os.path.exists(output_path):
            result["path"] = output_path
            result["available"] = True
        else:
            result["error"] = proc.stderr or "No se pudo generar reporte"
    except FileNotFoundError:
        result["error"] = "powercfg no disponible"
    except subprocess.TimeoutExpired:
        result["error"] = "Tiempo de espera agotado"
    except Exception as e:
        result["error"] = str(e)
    return result


def get_battery_health_powercfg():
    """
    Extrae capacidad de diseño, capacidad real y ciclos via powercfg /batteryreport /xml.
    Retorna dict con design_capacity, full_charge_capacity, cycle_count (en mWh).
    """
    result = {}
    try:
        import tempfile
        xml_path = os.path.join(tempfile.gettempdir(), "_tecoqc_battery.xml")
        proc = subprocess.run(
            ["powercfg", "/batteryreport", "/output", xml_path, "/xml"],
            capture_output=True, text=True, timeout=20,
        )
        if proc.returncode != 0 or not os.path.exists(xml_path):
            return result
        import xml.etree.ElementTree as ET
        tree = ET.parse(xml_path)
        root = tree.getroot()
        ns = {"b": root.tag.split("}")[0].lstrip("{") if "}" in root.tag else ""}
        ns_prefix = f"{{{ns['b']}}}" if ns["b"] else ""

        def find_text(node, tag):
            el = node.find(f".//{ns_prefix}{tag}")
            return el.text.strip() if el is not None and el.text else None

        design = find_text(root, "DesignCapacity")
        full = find_text(root, "FullChargeCapacity")
        cycles = find_text(root, "CycleCount")

        if design:
            result["design_capacity"] = int(design)
        if full:
            result["full_charge_capacity"] = int(full)
        if cycles:
            result["cycle_count"] = int(cycles)
        if design and full and int(design) > 0:
            health = round(int(full) / int(design) * 100, 1)
            result["health_pct"] = health
            result["wear_level_pct"] = round(100 - health, 1)
        try:
            os.remove(xml_path)
        except Exception:
            pass
    except Exception:
        pass
    return result


def get_all_battery_info():
    """Recopila toda la información de batería disponible."""
    wmi_data = get_battery_wmi()

    # Supplement WMI data with powercfg XML if WMI is missing health info
    if not wmi_data.get("health_pct"):
        pcfg = get_battery_health_powercfg()
        for key in ("design_capacity", "full_charge_capacity", "cycle_count",
                    "health_pct", "wear_level_pct"):
            if key in pcfg:
                wmi_data[key] = pcfg[key]

    return {
        "psutil": get_battery_psutil(),
        "wmi": wmi_data,
    }


def _battery_status(code):
    statuses = {
        1: "Descargando", 2: "CA conectado", 3: "Cargando completo",
        4: "Bajo", 5: "Crítico", 6: "Cargando",
        7: "Cargando y alto", 8: "Cargando y bajo",
        9: "Cargando y crítico", 10: "Sin definir",
        11: "Parcialmente cargado",
    }
    return statuses.get(code, f"Estado {code}")


def _battery_chemistry(code):
    chem = {
        1: "Otro", 2: "Desconocido", 3: "Plomo-ácido",
        4: "Níquel-cadmio", 5: "Níquel-metalhidruro",
        6: "Litio-ion", 7: "Zinc-aire", 8: "Litio-polímero",
    }
    return chem.get(code, f"Química {code}")
