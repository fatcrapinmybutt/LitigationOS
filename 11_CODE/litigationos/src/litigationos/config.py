"""Settings manager — reads and writes the DB settings table.

Settings are stored as key-value pairs in the `settings` table with a category
column for organization. This module provides typed access with defaults.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from litigationos.db.connection import DatabaseManager


# Default settings applied if not present in the DB
DEFAULTS = {
    "default_jurisdiction": ("MI", "jurisdiction"),
    "theme": ("dark", "display"),
    "bates_prefix": ("EXHIBIT", "general"),
    "auto_save": ("1", "general"),
    "ai_enabled": ("1", "ai"),
    "ai_engine": ("manbearpig", "ai"),
    "ai_engine_path": (r"00_SYSTEM\local_model\inference_engine.py", "ai"),
    "ai_mode": ("offline", "ai"),
}


class Settings:
    """Read/write interface to the settings table."""

    def __init__(self, db: DatabaseManager):
        self._db = db

    def get(self, key: str, default: str | None = None) -> str | None:
        """Retrieve a setting value by key."""
        conn = self._db.connect()
        try:
            row = conn.execute(
                "SELECT value FROM settings WHERE key = ?", (key,)
            ).fetchone()
            if row:
                return row[0]
            # Fall back to built-in defaults
            if key in DEFAULTS:
                return DEFAULTS[key][0]
            return default
        finally:
            conn.close()

    def set(self, key: str, value: str, category: str | None = None) -> None:
        """Write a setting value. Creates the key if it doesn't exist."""
        cat = category or DEFAULTS.get(key, (None, "general"))[1]
        conn = self._db.connect()
        try:
            conn.execute(
                "INSERT OR REPLACE INTO settings (key, value, category) VALUES (?, ?, ?)",
                (key, value, cat),
            )
            conn.commit()
        finally:
            conn.close()

    def get_bool(self, key: str) -> bool:
        """Retrieve a setting as a boolean (truthy: '1', 'true', 'yes')."""
        val = self.get(key, "0")
        return val.lower() in ("1", "true", "yes") if val else False

    def all(self, category: str | None = None) -> dict[str, str]:
        """Return all settings, optionally filtered by category."""
        conn = self._db.connect()
        try:
            if category:
                rows = conn.execute(
                    "SELECT key, value FROM settings WHERE category = ?", (category,)
                ).fetchall()
            else:
                rows = conn.execute("SELECT key, value FROM settings").fetchall()
            return {k: v for k, v in rows}
        finally:
            conn.close()
