"""LitigationOS Elite Branding Configuration.

Centralized branding constants for the LitigationOS desktop application.
Import from here for consistent colors, fonts, and identity across all UI screens.

Supports multiple themes via THEMES dict and get_theme() accessor.
"""

from pathlib import Path

APP_NAME = "LitigationOS"
APP_VERSION = "2.0.0-elite"
APP_SUBTITLE = "Litigation Intelligence System"
APP_AUTHOR = "Andrew James Pigors"
APP_DESCRIPTION = "Local-first litigation intelligence for Michigan family law."
APP_COPYRIGHT = "2024-2026 Andrew James Pigors. All rights reserved."

# --- MBP LLC Branding ---
MBP_NAME = "MBP LLC"
MBP_TAGLINE = "ManBearPig — Litigation Intelligence"

# Color Scheme (dark professional — default theme)
COLORS = {
    "primary": "#1a1a2e",       # Deep navy
    "secondary": "#16213e",     # Dark blue
    "accent": "#0f3460",        # Royal blue
    "highlight": "#e94560",     # Action red
    "success": "#00b894",       # Green
    "warning": "#fdcb6e",       # Gold
    "error": "#d63031",         # Error red
    "info": "#74b9ff",          # Info blue
    "text": "#ffffff",          # White
    "text_dim": "#a0a0a0",     # Gray
    "bg": "#0d1117",           # GitHub dark
    "surface": "#161b22",       # Card bg
    "border": "#30363d",        # Border
}

# MBP LLC color scheme (pink + black)
MBP_COLORS = {
    "primary": "#0d1117",       # Black base
    "secondary": "#161b22",     # Dark surface
    "accent": "#e94560",        # MBP pink
    "highlight": "#ff6b81",     # Bright pink hover
    "success": "#00b894",       # Green
    "warning": "#fdcb6e",       # Gold
    "error": "#d63031",         # Error red
    "info": "#ff9ff3",          # Pink info
    "text": "#ffffff",          # White
    "text_dim": "#b0b0b0",     # Light gray
    "bg": "#0d1117",           # Black background
    "surface": "#1a1a2e",       # Dark card bg
    "border": "#e94560",        # Pink border
}

# Theme registry — add new themes here
THEMES = {
    "default": {
        "name": "LitigationOS Dark",
        "colors": COLORS,
        "description": "Professional dark theme with navy and blue accents.",
    },
    "mbp": {
        "name": "MBP LLC",
        "colors": MBP_COLORS,
        "description": "MBP LLC branding — pink (#e94560) and black (#0d1117).",
    },
}

# Typography
FONTS = {
    "heading": ("Segoe UI", 24, "bold"),
    "subheading": ("Segoe UI", 16, "bold"),
    "body": ("Segoe UI", 12),
    "mono": ("Cascadia Code", 11),
    "small": ("Segoe UI", 10),
    "label": ("Segoe UI", 11, "bold"),
}

# Asset paths (relative to this file's parent package directory)
_ASSETS_DIR = Path(__file__).parent / "assets"
ICON_PATH = str(_ASSETS_DIR / "mbp_pig_logo.ico")
LOGO_PATH = str(_ASSETS_DIR / "mbp_pig_logo.ico")

# Lane color coding (matches the 6 case lanes)
LANE_COLORS = {
    "A": "#3498db",  # Custody — blue
    "B": "#e67e22",  # Housing — orange
    "C": "#9b59b6",  # Convergence — purple
    "D": "#e74c3c",  # PPO — red
    "E": "#f39c12",  # Misconduct — gold
    "F": "#2ecc71",  # Appellate — green
}

# Urgency levels for deadline display
URGENCY_COLORS = {
    "critical": "#e94560",   # < 3 days
    "high": "#fdcb6e",       # < 7 days
    "medium": "#74b9ff",     # < 14 days
    "low": "#00b894",        # > 14 days
}


def get_theme(name: str = "default") -> dict:
    """Return a theme's color set by name.

    Args:
        name: Theme key — 'default' or 'mbp'. Falls back to 'default'.

    Returns:
        Dict of color name → hex value.
    """
    theme = THEMES.get(name, THEMES["default"])
    return dict(theme["colors"])


def get_ctk_theme(theme_name: str = "default") -> dict:
    """Return a CustomTkinter-compatible color theme dict.

    Args:
        theme_name: Theme key — 'default' or 'mbp'.
    """
    colors = get_theme(theme_name)
    return {
        "CTk": {
            "fg_color": [colors["bg"], colors["bg"]],
        },
        "CTkFrame": {
            "fg_color": [colors["surface"], colors["surface"]],
            "border_color": [colors["border"], colors["border"]],
        },
        "CTkButton": {
            "fg_color": [colors["accent"], colors["accent"]],
            "hover_color": [colors["highlight"], colors["highlight"]],
            "text_color": [colors["text"], colors["text"]],
        },
        "CTkLabel": {
            "text_color": [colors["text"], colors["text"]],
        },
        "CTkEntry": {
            "fg_color": [colors["surface"], colors["surface"]],
            "border_color": [colors["border"], colors["border"]],
            "text_color": [colors["text"], colors["text"]],
        },
    }
