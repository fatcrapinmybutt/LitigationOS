"""Branding & Theme engine — MBP LLC brand identity, themes, and asset management.

Centralizes all brand constants, color themes, logo/icon paths, ASCII art,
and widget theming for the entire LitigationOS application. Pure configuration
with no database dependency.

Usage::

    from litigationos.engines.branding import BrandingEngine

    branding = BrandingEngine()
    theme = branding.get_active_theme()
    logo = branding.get_logo_path()
    branding.apply_theme_to_widget(some_widget)
"""

from __future__ import annotations

import json
import logging
import os
import shutil
from datetime import datetime
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Brand identity
# ---------------------------------------------------------------------------

BRAND: dict[str, str] = {
    "company": "MBP LLC",
    "product": "LitigationOS",
    "tagline": "Level the Playing Field",
    "version": "1.0.0",
    "author": "Andrew Pigors",
    "website": "https://litigationos.com",
    "support_email": "support@litigationos.com",
    "copyright": "\u00a9 2024-2025 MBP LLC. All rights reserved.",
}

# ---------------------------------------------------------------------------
# Theme palettes
# ---------------------------------------------------------------------------
# Each theme maps semantic role names to hex colors.  The "default" theme is
# the canonical MBP Pink + Black palette and MUST stay in sync with
# gui.widgets.COLORS so that widgets built with either dict get identical
# visual results.
# ---------------------------------------------------------------------------

THEMES: dict[str, dict[str, str]] = {
    "default": {  # MBP Pink + Black (canonical)
        "bg": "#0D0D0D",
        "bg_secondary": "#1A1A2E",
        "bg_card": "#16213E",
        "bg_sidebar": "#111111",
        "accent": "#FF1493",
        "accent_hover": "#FF69B4",
        "accent_dim": "#C71585",
        "text": "#E0E0E0",
        "text_muted": "#888888",
        "success": "#00E676",
        "warning": "#FFD600",
        "error": "#FF1744",
        "info": "#00B0FF",
        "border": "#2A2A2A",
        "border_light": "#3A3A3A",
        "purple": "#E040FB",
        "orange": "#FF6D00",
        "gray": "#616161",
    },
    "light": {  # Professional light mode
        "bg": "#F5F5F5",
        "bg_secondary": "#FFFFFF",
        "bg_card": "#FFFFFF",
        "bg_sidebar": "#EEEEEE",
        "accent": "#FF1493",
        "accent_hover": "#C51162",
        "accent_dim": "#AD1457",
        "text": "#212121",
        "text_muted": "#757575",
        "success": "#2E7D32",
        "warning": "#F57F17",
        "error": "#C62828",
        "info": "#1565C0",
        "border": "#E0E0E0",
        "border_light": "#BDBDBD",
        "purple": "#7B1FA2",
        "orange": "#E65100",
        "gray": "#9E9E9E",
    },
    "court": {  # Formal court mode (blue / navy)
        "bg": "#1B2838",
        "bg_secondary": "#2A3F5F",
        "bg_card": "#1E3A5F",
        "bg_sidebar": "#162232",
        "accent": "#4FC3F7",
        "accent_hover": "#81D4FA",
        "accent_dim": "#0288D1",
        "text": "#E0E0E0",
        "text_muted": "#90A4AE",
        "success": "#66BB6A",
        "warning": "#FFA726",
        "error": "#EF5350",
        "info": "#42A5F5",
        "border": "#37474F",
        "border_light": "#546E7A",
        "purple": "#CE93D8",
        "orange": "#FFB74D",
        "gray": "#78909C",
    },
}

# ---------------------------------------------------------------------------
# Logo / icon search paths (ordered by preference)
# ---------------------------------------------------------------------------

_LOGO_SEARCH_PATHS: list[str] = [
    r"C:\Users\andre\Pictures\pig_logo.png",
    r"C:\Users\andre\LitigationOS\assets\logo.png",
    r"C:\Users\andre\LitigationOS\11_CODE\litigationos\assets\logo.png",
]

_ICON_SEARCH_PATHS: list[str] = [
    r"C:\Users\andre\Pictures\LitigationOS-Pig-Icon.ico",
    r"C:\Users\andre\LitigationOS\assets\icon.ico",
    r"C:\Users\andre\LitigationOS\11_CODE\litigationos\assets\icon.ico",
]

# ---------------------------------------------------------------------------
# ASCII art logo variants
# ---------------------------------------------------------------------------

_ASCII_LOGO_LARGE = r"""
     ██████╗ ██╗ ██████╗
     ██╔══██╗██║██╔════╝
     ██████╔╝██║██║  ███╗
     ██╔═══╝ ██║██║   ██║
     ██║     ██║╚██████╔╝
     ╚═╝     ╚═╝ ╚═════╝
          🐷  MBP LLC
       L i t i g a t i o n O S
    "Level the Playing Field"
"""

_ASCII_LOGO_MEDIUM = r"""
      🐷
    MBP LLC
  LitigationOS
"""

_ASCII_LOGO_SMALL = "🐷 MBP LLC — LitigationOS"

_ASCII_LOGOS: dict[str, str] = {
    "large": _ASCII_LOGO_LARGE,
    "medium": _ASCII_LOGO_MEDIUM,
    "small": _ASCII_LOGO_SMALL,
}

# ---------------------------------------------------------------------------
# Font stack
# ---------------------------------------------------------------------------

FONTS: dict[str, tuple[str, int]] = {
    "heading": ("Segoe UI", 24),
    "subheading": ("Segoe UI", 16),
    "body": ("Segoe UI", 13),
    "caption": ("Segoe UI", 11),
    "mono": ("Cascadia Code", 12),
    "mono_small": ("Cascadia Code", 10),
    "brand_title": ("Segoe UI Black", 28),
    "brand_tagline": ("Segoe UI Semilight", 14),
}

# ---------------------------------------------------------------------------
# Screen header registry — (title, subtitle) for each named screen
# ---------------------------------------------------------------------------

_SCREEN_HEADERS: dict[str, tuple[str, str]] = {
    "dashboard": ("Dashboard", "LitigationOS Command Center — MBP LLC"),
    "cases": ("Case Manager", "Track every filing across all lanes"),
    "deadlines": ("Deadline Tracker", "Never miss a court deadline"),
    "evidence": ("Evidence Vault", "Organize, tag, and authenticate exhibits"),
    "filings": ("Filing Factory", "Assemble court-ready documents"),
    "documents": ("Document Library", "All documents across all drives"),
    "settings": ("Settings", "Configure LitigationOS to your workflow"),
    "ai": ("AI Assistant", "Local-only intelligence — zero network"),
    "timeline": ("Timeline", "Chronological view of case events"),
    "research": ("Legal Research", "Authority chains and case law"),
    "analytics": ("Analytics", "Evidence scoring and gap analysis"),
    "discovery": ("Discovery", "Interrogatories, RFPs, and subpoenas"),
    "motions": ("Motion Builder", "Draft motions with template intelligence"),
    "about": ("About LitigationOS", f"v{BRAND['version']} — {BRAND['copyright']}"),
    "onboarding": ("Welcome to LitigationOS", "Let's get you set up"),
    "monetization": ("Revenue Engine", "Autonomous income streams"),
}

# ---------------------------------------------------------------------------
# Splash text lines
# ---------------------------------------------------------------------------

_SPLASH_LINES: list[str] = [
    "🐷  MBP LLC presents",
    "",
    "╔══════════════════════════════════╗",
    "║        L i t i g a t i o n O S   ║",
    "╚══════════════════════════════════╝",
    "",
    f'   "{BRAND["tagline"]}"',
    "",
    f"   v{BRAND['version']}  •  {BRAND['copyright']}",
    "",
    "   Initializing engines ...",
]


# ═══════════════════════════════════════════════════════════════════════════
# BrandingEngine
# ═══════════════════════════════════════════════════════════════════════════


class BrandingEngine:
    """Central brand identity, theme management, and asset loading.

    Provides a single source of truth for:
      • MBP LLC brand constants (name, tagline, version, copyright)
      • Three color themes (default / light / court)
      • Logo and icon asset discovery across known paths
      • ASCII art generation for splash screens and consoles
      • Widget theming helpers for CustomTkinter widgets
      • Brand-kit export for external design use

    No database dependency — this engine is pure configuration.
    """

    def __init__(self) -> None:
        self._active_theme: str = "default"
        self._custom_themes: dict[str, dict[str, str]] = {}
        logger.info("BrandingEngine initialized (theme=%s)", self._active_theme)

    # ------------------------------------------------------------------
    # Brand identity
    # ------------------------------------------------------------------

    @staticmethod
    def get_brand() -> dict[str, str]:
        """Return the full MBP LLC brand constants dictionary."""
        return dict(BRAND)

    @staticmethod
    def get_brand_value(key: str, fallback: str = "") -> str:
        """Return a single brand constant by key with optional fallback."""
        return BRAND.get(key, fallback)

    # ------------------------------------------------------------------
    # Theme management
    # ------------------------------------------------------------------

    def get_theme(self, name: str = "default") -> dict[str, str]:
        """Return a theme palette by name.

        Parameters
        ----------
        name:
            One of ``"default"``, ``"light"``, ``"court"``, or a custom
            theme previously registered via :meth:`register_custom_theme`.

        Returns
        -------
        dict[str, str]
            Mapping of semantic color role → hex value.

        Raises
        ------
        KeyError
            If *name* is not a recognised theme.
        """
        if name in THEMES:
            return dict(THEMES[name])
        if name in self._custom_themes:
            return dict(self._custom_themes[name])
        raise KeyError(
            f"Unknown theme '{name}'. "
            f"Available: {list(THEMES) + list(self._custom_themes)}"
        )

    def set_theme(self, name: str) -> None:
        """Set the active theme by name.

        Raises :class:`KeyError` if the theme does not exist.
        """
        # Validate first
        self.get_theme(name)
        self._active_theme = name
        logger.info("Active theme changed to '%s'", name)

    def get_active_theme(self) -> dict[str, str]:
        """Return the colour palette for the currently active theme."""
        return self.get_theme(self._active_theme)

    @property
    def active_theme_name(self) -> str:
        """Name of the currently active theme."""
        return self._active_theme

    def list_themes(self) -> list[str]:
        """Return names of all available themes (built-in + custom)."""
        return list(THEMES) + list(self._custom_themes)

    def register_custom_theme(
        self,
        name: str,
        colors: dict[str, str],
        *,
        merge_with: str = "default",
    ) -> None:
        """Register a custom theme, optionally inheriting from an existing one.

        Parameters
        ----------
        name:
            Unique name for the new theme.
        colors:
            Colour overrides (keys matching theme roles).
        merge_with:
            Base theme to inherit unset keys from. Pass ``""`` to skip.
        """
        if merge_with and merge_with in THEMES:
            merged = dict(THEMES[merge_with])
            merged.update(colors)
            self._custom_themes[name] = merged
        else:
            self._custom_themes[name] = dict(colors)
        logger.info("Custom theme '%s' registered (%d colors)", name, len(self._custom_themes[name]))

    # ------------------------------------------------------------------
    # Compatibility bridge — map theme keys to COLORS dict keys
    # ------------------------------------------------------------------

    def get_colors_compat(self, theme_name: str = "") -> dict[str, str]:
        """Return a dict compatible with ``gui.widgets.COLORS``.

        This bridges the theme system with widgets that import COLORS
        directly.  Keys from the theme palette are mapped to the legacy
        ``COLORS`` key names so existing widgets work without changes.
        """
        theme = self.get_theme(theme_name or self._active_theme)
        return {
            # Core backgrounds
            "bg_dark": theme.get("bg", "#0D0D0D"),
            "bg_card": theme.get("bg_card", "#1A1A1A"),
            "bg_sidebar": theme.get("bg_sidebar", "#111111"),
            # Brand accent
            "accent": theme["accent"],
            "accent_hover": theme["accent_hover"],
            "accent_dim": theme.get("accent_dim", "#C71585"),
            # Semantic
            "green": theme.get("success", "#00E676"),
            "yellow": theme.get("warning", "#FFD600"),
            "orange": theme.get("orange", "#FF6D00"),
            "red": theme.get("error", "#FF1744"),
            "blue": theme.get("info", "#448AFF"),
            "purple": theme.get("purple", "#E040FB"),
            "gray": theme.get("gray", "#616161"),
            # Text
            "text": theme.get("text", "#F5F5F5"),
            "text_dim": theme.get("text_muted", "#9E9E9E"),
            # Borders
            "border": theme.get("border", "#2A2A2A"),
            "border_light": theme.get("border_light", "#3A3A3A"),
        }

    # ------------------------------------------------------------------
    # Asset discovery
    # ------------------------------------------------------------------

    @staticmethod
    def get_logo_path() -> str:
        """Find the pig logo image across known search locations.

        Returns the first existing file path, or ``""`` if none found.
        """
        for path in _LOGO_SEARCH_PATHS:
            if os.path.isfile(path):
                logger.debug("Logo found: %s", path)
                return path
        logger.warning("No logo image found in search paths")
        return ""

    @staticmethod
    def get_icon_path() -> str:
        """Find the ``.ico`` window icon across known search locations.

        Returns the first existing file path, or ``""`` if none found.
        """
        for path in _ICON_SEARCH_PATHS:
            if os.path.isfile(path):
                logger.debug("Icon found: %s", path)
                return path
        logger.warning("No .ico icon found in search paths")
        return ""

    @staticmethod
    def has_logo() -> bool:
        """Return ``True`` if a logo image exists on disk."""
        return any(os.path.isfile(p) for p in _LOGO_SEARCH_PATHS)

    @staticmethod
    def has_icon() -> bool:
        """Return ``True`` if an .ico icon exists on disk."""
        return any(os.path.isfile(p) for p in _ICON_SEARCH_PATHS)

    # ------------------------------------------------------------------
    # ASCII / text logos
    # ------------------------------------------------------------------

    @staticmethod
    def generate_text_logo(size: str = "large") -> str:
        """Return an ASCII art logo string.

        Parameters
        ----------
        size:
            ``"large"`` (block art), ``"medium"`` (compact), or ``"small"``
            (single-line).
        """
        return _ASCII_LOGOS.get(size, _ASCII_LOGOS["large"])

    @staticmethod
    def get_watermark() -> str:
        """Return the standard watermark line for footers and status bars."""
        return f"Powered by {BRAND['product']} \u2014 {BRAND['company']}"

    # ------------------------------------------------------------------
    # About / splash
    # ------------------------------------------------------------------

    @staticmethod
    def get_about_info() -> dict[str, Any]:
        """Return structured content for the About dialog.

        Keys: brand, license, credits, system, links.
        """
        return {
            "brand": dict(BRAND),
            "license": (
                "Proprietary — All rights reserved.\n"
                "This software is the intellectual property of MBP LLC.\n"
                "Unauthorized distribution is prohibited."
            ),
            "credits": [
                {"role": "Founder & Developer", "name": BRAND["author"]},
                {"role": "AI Engine", "name": "THE MANBEARPIG (local-only)"},
                {"role": "Framework", "name": "Python 3.12 + CustomTkinter"},
            ],
            "system": {
                "python": f"{__import__('sys').version_info.major}."
                          f"{__import__('sys').version_info.minor}."
                          f"{__import__('sys').version_info.micro}",
                "platform": __import__("platform").platform(),
                "db_engine": "SQLite (WAL mode)",
                "ai_provider": "Local-only (zero network)",
            },
            "links": {
                "Website": BRAND["website"],
                "Support": f"mailto:{BRAND['support_email']}",
            },
        }

    @staticmethod
    def get_splash_text() -> list[str]:
        """Return text lines for the animated splash screen."""
        return list(_SPLASH_LINES)

    # ------------------------------------------------------------------
    # Fonts
    # ------------------------------------------------------------------

    @staticmethod
    def get_font(role: str = "body") -> tuple[str, int]:
        """Return ``(family, size)`` for a named font role.

        Roles: heading, subheading, body, caption, mono, mono_small,
        brand_title, brand_tagline.
        """
        return FONTS.get(role, FONTS["body"])

    @staticmethod
    def list_font_roles() -> list[str]:
        """Return all available font role names."""
        return list(FONTS)

    # ------------------------------------------------------------------
    # Widget theming
    # ------------------------------------------------------------------

    def apply_theme_to_widget(self, widget: Any, theme_name: str = "") -> None:
        """Apply theme colours to a CustomTkinter widget.

        Attempts to call ``configure()`` on *widget* with appropriate
        colour keywords.  Silently skips attributes the widget does not
        support.

        Parameters
        ----------
        widget:
            A ``customtkinter`` widget instance.
        theme_name:
            Theme to apply. Defaults to the active theme.
        """
        theme = self.get_theme(theme_name or self._active_theme)

        _try_configure(widget, "fg_color", theme["bg"])
        _try_configure(widget, "bg_color", theme["bg"])
        _try_configure(widget, "text_color", theme["text"])
        _try_configure(widget, "border_color", theme.get("border", theme["bg"]))
        _try_configure(widget, "hover_color", theme["accent_hover"])
        _try_configure(widget, "button_color", theme["accent"])
        _try_configure(widget, "button_hover_color", theme["accent_hover"])
        _try_configure(widget, "progress_color", theme["accent"])

    def apply_theme_to_frame(self, frame: Any, theme_name: str = "") -> None:
        """Recursively apply theme to a frame and all its children."""
        self.apply_theme_to_widget(frame, theme_name)
        children = getattr(frame, "winfo_children", lambda: [])()
        for child in children:
            self.apply_theme_to_widget(child, theme_name)

    # ------------------------------------------------------------------
    # Screen headers
    # ------------------------------------------------------------------

    @staticmethod
    def get_header_text(screen_name: str) -> tuple[str, str]:
        """Return ``(title, subtitle)`` for a named screen.

        Falls back to a capitalised version of *screen_name* if no
        custom header is registered.
        """
        if screen_name in _SCREEN_HEADERS:
            return _SCREEN_HEADERS[screen_name]
        title = screen_name.replace("_", " ").title()
        subtitle = f"{BRAND['product']} — {BRAND['company']}"
        return title, subtitle

    @staticmethod
    def list_screens() -> list[str]:
        """Return all screen names that have registered headers."""
        return list(_SCREEN_HEADERS)

    # ------------------------------------------------------------------
    # Brand-kit export
    # ------------------------------------------------------------------

    def export_brand_kit(self, output_dir: str) -> str:
        """Export brand assets to a folder for external design use.

        Creates::

            <output_dir>/
                brand.json          — brand constants
                themes.json         — all theme palettes
                fonts.json          — font stack
                colors_compat.json  — legacy COLORS mapping
                logo.png / .ico     — copied if found on disk

        Parameters
        ----------
        output_dir:
            Directory to write the kit into (created if missing).

        Returns
        -------
        str
            Absolute path of the exported kit directory.
        """
        kit_dir = Path(output_dir).resolve()
        kit_dir.mkdir(parents=True, exist_ok=True)

        # Brand constants
        (kit_dir / "brand.json").write_text(
            json.dumps(BRAND, indent=2, ensure_ascii=False), encoding="utf-8"
        )

        # Themes (built-in + custom)
        all_themes = {**THEMES, **self._custom_themes}
        (kit_dir / "themes.json").write_text(
            json.dumps(all_themes, indent=2, ensure_ascii=False), encoding="utf-8"
        )

        # Fonts
        fonts_serializable = {k: list(v) for k, v in FONTS.items()}
        (kit_dir / "fonts.json").write_text(
            json.dumps(fonts_serializable, indent=2, ensure_ascii=False),
            encoding="utf-8",
        )

        # Legacy COLORS compat
        (kit_dir / "colors_compat.json").write_text(
            json.dumps(self.get_colors_compat(), indent=2, ensure_ascii=False),
            encoding="utf-8",
        )

        # Copy logo & icon if they exist
        logo = self.get_logo_path()
        if logo:
            shutil.copy2(logo, kit_dir / Path(logo).name)

        icon = self.get_icon_path()
        if icon:
            shutil.copy2(icon, kit_dir / Path(icon).name)

        # README
        readme = (
            f"# {BRAND['product']} Brand Kit\n\n"
            f"**Company:** {BRAND['company']}\n"
            f"**Tagline:** {BRAND['tagline']}\n"
            f"**Version:** {BRAND['version']}\n\n"
            f"Exported: {datetime.now().strftime('%Y-%m-%d %H:%M')}\n\n"
            "## Contents\n\n"
            "- `brand.json` — Brand identity constants\n"
            "- `themes.json` — Color themes (default, light, court)\n"
            "- `fonts.json` — Typography stack\n"
            "- `colors_compat.json` — Legacy COLORS dict mapping\n"
            "- Logo/icon assets (if found on disk)\n"
        )
        (kit_dir / "README.md").write_text(readme, encoding="utf-8")

        exported = str(kit_dir)
        logger.info("Brand kit exported to %s", exported)
        return exported

    # ------------------------------------------------------------------
    # Utility
    # ------------------------------------------------------------------

    def __repr__(self) -> str:
        themes_count = len(THEMES) + len(self._custom_themes)
        return (
            f"<BrandingEngine "
            f"theme='{self._active_theme}' "
            f"themes={themes_count} "
            f"icon={'✓' if self.has_icon() else '✗'} "
            f"logo={'✓' if self.has_logo() else '✗'}>"
        )

    def status(self) -> dict[str, Any]:
        """Return a snapshot of engine state for diagnostics."""
        return {
            "active_theme": self._active_theme,
            "available_themes": self.list_themes(),
            "has_logo": self.has_logo(),
            "has_icon": self.has_icon(),
            "logo_path": self.get_logo_path(),
            "icon_path": self.get_icon_path(),
            "brand": dict(BRAND),
        }


# ---------------------------------------------------------------------------
# Private helpers
# ---------------------------------------------------------------------------


def _try_configure(widget: Any, key: str, value: str) -> None:
    """Call ``widget.configure(**{key: value})`` if the widget supports it."""
    try:
        widget.configure(**{key: value})
    except Exception:  # noqa: BLE001
        pass
