"""
TecoQC - Tema visual Azul/Verde (Tecology Blue-Green)
"""

# ── Background layers ──────────────────────────────────────────────
BG_BASE      = "#0b1f2e"   # fondo principal — azul marino profundo
BG_MANTLE    = "#081828"   # sidebar / paneles más oscuros
BG_CRUST     = "#050f18"   # capa más profunda
BG_SURFACE0  = "#112b3f"   # tarjetas / superficies elevadas
BG_SURFACE1  = "#1a3a52"   # ligeramente elevado
BG_SURFACE2  = "#255570"   # bordes / más elevado

# ── Text ───────────────────────────────────────────────────────────
TEXT_PRIMARY   = "#d0eeff"   # blanco azulado
TEXT_SECONDARY = "#7ab8d4"   # azul medio
TEXT_MUTED     = "#3d7a96"   # azul apagado

# ── Accent colours ─────────────────────────────────────────────────
ACCENT_BLUE    = "#3fa9ff"   # azul vivo
ACCENT_LAVENDER= "#5ccfff"   # cian claro
SUCCESS        = "#27c97a"   # verde vivo
WARNING        = "#f5c542"   # ámbar
ERROR          = "#ff5c6b"   # rojo
INFO           = "#00d4c8"   # verde-cian
PEACH          = "#ff9f5c"   # naranja suave

# ── Sidebar ────────────────────────────────────────────────────────
SIDEBAR_BG         = BG_MANTLE
SIDEBAR_HEADER_BG  = BG_CRUST
SIDEBAR_ITEM_BG    = BG_MANTLE
SIDEBAR_ITEM_HOVER = BG_SURFACE0
SIDEBAR_CURRENT_BG = "#0d3a5c"   # azul seleccionado

# ── Status colours ─────────────────────────────────────────────────
STATUS_COLORS = {
    "pending":  TEXT_MUTED,
    "current":  ACCENT_BLUE,
    "passed":   SUCCESS,
    "failed":   ERROR,
    "skipped":  WARNING,
}

# ── Fonts ──────────────────────────────────────────────────────────
FONT_FAMILY    = "Segoe UI"
FONT_MONO      = "Consolas"

FONT_H1        = (FONT_FAMILY, 22, "bold")
FONT_H2        = (FONT_FAMILY, 16, "bold")
FONT_H3        = (FONT_FAMILY, 13, "bold")
FONT_BODY      = (FONT_FAMILY, 11)
FONT_BODY_BOLD = (FONT_FAMILY, 11, "bold")
FONT_SMALL     = (FONT_FAMILY, 9)
FONT_MONO_SM   = (FONT_MONO,   10)
FONT_SIDEBAR   = (FONT_FAMILY, 10)
FONT_SIDEBAR_H = (FONT_FAMILY, 12, "bold")

# ── Button styles ──────────────────────────────────────────────────
BTN_PRIMARY = {
    "bg": ACCENT_BLUE,
    "fg": BG_CRUST,
    "font": FONT_BODY_BOLD,
    "relief": "flat",
    "cursor": "hand2",
    "padx": 18,
    "pady": 8,
    "bd": 0,
    "activebackground": "#2290e0",
    "activeforeground": BG_CRUST,
}

BTN_SECONDARY = {
    "bg": BG_SURFACE1,
    "fg": TEXT_PRIMARY,
    "font": FONT_BODY,
    "relief": "flat",
    "cursor": "hand2",
    "padx": 18,
    "pady": 8,
    "bd": 0,
    "activebackground": BG_SURFACE2,
    "activeforeground": TEXT_PRIMARY,
}

BTN_SUCCESS = {
    "bg": SUCCESS,
    "fg": BG_CRUST,
    "font": FONT_BODY_BOLD,
    "relief": "flat",
    "cursor": "hand2",
    "padx": 18,
    "pady": 8,
    "bd": 0,
    "activebackground": "#1faa62",
    "activeforeground": BG_CRUST,
}

BTN_DANGER = {
    "bg": ERROR,
    "fg": BG_CRUST,
    "font": FONT_BODY_BOLD,
    "relief": "flat",
    "cursor": "hand2",
    "padx": 18,
    "pady": 8,
    "bd": 0,
    "activebackground": "#e04455",
    "activeforeground": BG_CRUST,
}

BTN_WARNING = {
    "bg": WARNING,
    "fg": BG_CRUST,
    "font": FONT_BODY_BOLD,
    "relief": "flat",
    "cursor": "hand2",
    "padx": 16,
    "pady": 8,
    "bd": 0,
    "activebackground": "#d4aa30",
    "activeforeground": BG_CRUST,
}

BTN_NEUTRAL = {
    "bg": BG_SURFACE0,
    "fg": TEXT_PRIMARY,
    "font": FONT_BODY,
    "relief": "flat",
    "cursor": "hand2",
    "padx": 14,
    "pady": 6,
    "bd": 0,
    "activebackground": BG_SURFACE1,
    "activeforeground": TEXT_PRIMARY,
}

# ── Entry / Text styles ────────────────────────────────────────────
ENTRY_STYLE = {
    "bg": BG_SURFACE0,
    "fg": TEXT_PRIMARY,
    "font": FONT_BODY,
    "relief": "flat",
    "bd": 0,
    "insertbackground": TEXT_PRIMARY,
    "highlightthickness": 1,
    "highlightcolor": ACCENT_BLUE,
    "highlightbackground": BG_SURFACE1,
}

# ── Card style ─────────────────────────────────────────────────────
CARD_STYLE = {
    "bg": BG_SURFACE0,
    "relief": "flat",
    "bd": 0,
    "highlightthickness": 1,
    "highlightbackground": BG_SURFACE1,
}

# ── Progress bar ───────────────────────────────────────────────────
PROGRESS_BG     = BG_SURFACE1
PROGRESS_FILL   = ACCENT_BLUE
PROGRESS_HEIGHT = 4


def apply_dark_title_bar(window):
    """Attempt to apply dark title bar on Windows (requires pywin32)."""
    try:
        import ctypes
        DWMWA_USE_IMMERSIVE_DARK_MODE = 20
        value = ctypes.c_int(1)
        hwnd = ctypes.windll.user32.GetParent(window.winfo_id())
        ctypes.windll.dwmapi.DwmSetWindowAttribute(
            hwnd, DWMWA_USE_IMMERSIVE_DARK_MODE,
            ctypes.byref(value), ctypes.sizeof(value)
        )
    except Exception:
        pass
