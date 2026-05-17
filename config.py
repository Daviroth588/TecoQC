"""
TecoQC - Configuración global de la aplicación
Tecology Quality Control System
"""

APP_NAME = "TecoQC"
COMPANY = "Tecology"
VERSION = "1.0.0"
APP_TITLE = f"{COMPANY} {APP_NAME} v{VERSION}"

# Window dimensions
WINDOW_WIDTH = 1200
WINDOW_HEIGHT = 750
SIDEBAR_WIDTH = 220

# Step definitions (id, title, module)
STEPS = [
    (1,  "Bienvenida",      "s01_welcome"),
    (2,  "Sistema",         "s02_sysinfo"),
    (3,  "Teclado",         "s03_keyboard"),
    (4,  "Trackpad",        "s04_trackpad"),
    (5,  "Pantalla",        "s05_display"),
    (6,  "Cámara",          "s06_camera"),
    (7,  "Puertos USB",     "s07_usb"),
    (8,  "Red",             "s08_network"),
    (9,  "Audio",           "s09_audio"),
    (10, "CPU",             "s10_cpu"),
    (11, "GPU",             "s11_gpu"),
    (12, "Memoria RAM",     "s12_memory"),
    (13, "Almacenamiento",  "s13_storage"),
    (14, "Batería",         "s14_battery"),
    (15, "Reporte Final",   "s15_report"),
]

# Status constants
STATUS_PENDING  = "pending"
STATUS_CURRENT  = "current"
STATUS_PASSED   = "passed"
STATUS_FAILED   = "failed"
STATUS_SKIPPED  = "skipped"

STATUS_LABELS = {
    STATUS_PENDING:  "Pendiente",
    STATUS_CURRENT:  "En curso",
    STATUS_PASSED:   "Aprobado",
    STATUS_FAILED:   "Fallido",
    STATUS_SKIPPED:  "Omitido",
}

STATUS_ICONS = {
    STATUS_PENDING:  "●",
    STATUS_CURRENT:  "►",
    STATUS_PASSED:   "✓",
    STATUS_FAILED:   "✗",
    STATUS_SKIPPED:  "⊘",
}

# Ping host for network test
PING_HOST          = "8.8.8.8"
PING_FALLBACK_HOST = "1.1.1.1"
PING_MAX_MS        = 50       # ms — threshold for PASSED

# Temperature thresholds (°C)
TEMP_WARNING  = 75
TEMP_CRITICAL = 85

# Audio test tone
AUDIO_FREQUENCY = 440   # Hz
AUDIO_DURATION  = 1000  # ms

# Camera thresholds
CAMERA_MIN_WIDTH  = 640
CAMERA_MIN_HEIGHT = 480
CAMERA_MIN_FPS    = 15

# Disk speed thresholds (MB/s)
DISK_SPEED_HDD_MIN_MB_S = 50
DISK_SPEED_SSD_MIN_MB_S = 150
DISK_IOPS_4K_MIN        = 500   # IOPS mínimas en bloques de 4 KB

# Network speed threshold
NET_DOWNLOAD_MIN_MB_S = 0.5


import os
import sys


def get_data_dir() -> str:
    """
    Retorna el directorio donde TecoQC guarda sus datos.

    - Si el ejecutable/script está en una unidad removible (USB): usa
      una carpeta 'TecoQC_Data' junto al ejecutable.
    - Si no: usa ~/.tecoqc/ (comportamiento anterior).
    """
    # Determine base path of the running app
    if getattr(sys, "frozen", False):
        # PyInstaller exe
        base = os.path.dirname(sys.executable)
    else:
        base = os.path.dirname(os.path.abspath(__file__))

    # On Windows, check drive type
    try:
        import ctypes
        drive = os.path.splitdrive(base)[0] + "\\"
        if drive and drive != "\\":
            DRIVE_REMOVABLE = 2
            drive_type = ctypes.windll.kernel32.GetDriveTypeW(drive)
            if drive_type == DRIVE_REMOVABLE:
                data_dir = os.path.join(base, "TecoQC_Data")
                os.makedirs(data_dir, exist_ok=True)
                return data_dir
    except Exception:
        pass

    # Default: user home directory
    data_dir = os.path.join(os.path.expanduser("~"), ".tecoqc")
    os.makedirs(data_dir, exist_ok=True)
    return data_dir


def is_usb_mode() -> bool:
    """Retorna True si TecoQC está corriendo desde una unidad USB."""
    try:
        import ctypes
        if getattr(sys, "frozen", False):
            base = os.path.dirname(sys.executable)
        else:
            base = os.path.dirname(os.path.abspath(__file__))
        drive = os.path.splitdrive(base)[0] + "\\"
        if drive and drive != "\\":
            DRIVE_REMOVABLE = 2
            return ctypes.windll.kernel32.GetDriveTypeW(drive) == DRIVE_REMOVABLE
    except Exception:
        pass
    return False
