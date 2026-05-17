"""
TecoQC - Tema visual profesional oscuro (Catppuccin Mocha inspired)
"""

# ── Background layers ──────────────────────────────────────────────
BG_BASE      = "#1e1e2e"   # main background
BG_MANTLE    = "#181825"   # sidebar / deeper panels
BG_CRUST     = "#11111b"   # deepest layer
BG_SURFACE0  = "#313244"   # cards / raised surfaces
BG_SURFACE1  = "#45475a"   # slightly elevated
BG_SURFACE2  = "#585b70"   # even more elevated / borders

# ── Text ───────────────────────────────────────────────────────────
TEXT_PRIMARY   = "#cdd6f4"
TEXT_SECONDARY = "#a6adc8"
TEXT_MUTED     = "#6c7086"

# ── Accent colours ─────────────────────────────────────────────────
ACCENT_BLUE    = "#89b4fa"
ACCENT_LAVENDER= "#b4befe"
SUCCESS        = "#a6e3a1"
WARNING        = "#f9e2af"
ERROR          = "#f38ba8"
INFO           = "#89dceb"
PEACH          = "#fab387"

# ── Sidebar ────────────────────────────────────────────────────────
SIDEBAR_BG         = BG_MANTLE
SIDEBAR_HEADER_BG  = BG_CRUST
SIDEBAR_ITEM_BG    = BG_MANTLE
SIDEBAR_ITEM_HOVER = BG_SURFACE0
SIDEBAR_CURRENT_BG = "#2a3f6f"   # blue tint

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
    "fg": BG_BASE,
    "font": FONT_BODY_BOLD,
    "relief": "flat",
    "cursor": "hand2",
    "padx": 18,
    "pady": 8,
    "bd": 0,
    "activebackground": "#7aa2f7",
    "activeforeground": BG_BASE,
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
    "fg": BG_BASE,
    "font": FONT_BODY_BOLD,
    "relief": "flat",
    "cursor": "hand2",
    "padx": 18,
    "pady": 8,
    "bd": 0,
    "activebackground": "#8ed380",
    "activeforeground": BG_BASE,
}

BTN_DANGER = {
    "bg": ERROR,
    "fg": BG_BASE,
    "font": FONT_BODY_BOLD,
    "relief": "flat",
    "cursor": "hand2",
    "padx": 18,
    "pady": 8,
    "bd": 0,
    "activebackground": "#e07a95",
    "activeforeground": BG_BASE,
}

BTN_WARNING = {
    "bg": WARNING,
    "fg": BG_BASE,
    "font": FONT_BODY_BOLD,
    "relief": "flat",
    "cursor": "hand2",
    "padx": 16,
    "pady": 8,
    "bd": 0,
    "activebackground": "#e0cb8a",
    "activeforeground": BG_BASE,
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
