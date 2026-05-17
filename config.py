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
PING_HOST = "8.8.8.8"

# Temperature thresholds (°C)
TEMP_WARNING  = 75
TEMP_CRITICAL = 85

# Audio test tone
AUDIO_FREQUENCY = 440   # Hz
AUDIO_DURATION  = 1000  # ms
