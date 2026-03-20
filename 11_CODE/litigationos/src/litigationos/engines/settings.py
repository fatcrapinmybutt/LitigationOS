"""Settings / configuration engine.

Reads and writes application settings from the ``settings`` table, with
typed helpers for jurisdiction, paths, and LLM configuration.  Provides
sensible Michigan-focused defaults that are auto-seeded on first access.
"""

from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import TYPE_CHECKING, Any, Optional

if TYPE_CHECKING:
    from litigationos.db.connection import DatabaseManager

logger = logging.getLogger(__name__)

# -- Default settings ---------------------------------------------------------

_DEFAULTS: dict[str, tuple[str, str]] = {
    # key → (value, category)
    "jurisdiction.state": ("MI", "jurisdiction"),
    "jurisdiction.county": ("Muskegon", "jurisdiction"),
    "jurisdiction.court": ("14th Circuit", "jurisdiction"),
    "paths.data_dir": ("", "paths"),          # auto-detected at runtime
    "paths.output_dir": ("", "paths"),
    "paths.template_dir": ("", "paths"),
    "paths.model_dir": ("", "paths"),
    "llm.model": ("qwen2.5:7b", "ai"),
    "llm.embedding_model": ("nomic-embed-text", "ai"),
    "app.theme": ("dark", "display"),
    "app.font_size": ("12", "display"),
}


def _auto_data_dir() -> str:
    """Best-effort auto-detection of the project data directory."""
    candidates = [
        Path.home() / "LitigationOS" / "data",
        Path.home() / ".litigationos" / "data",
        Path.cwd() / "data",
    ]
    for p in candidates:
        if p.exists():
            return str(p)
    # Fall back to a reasonable default
    default = Path.home() / "LitigationOS" / "data"
    return str(default)


# -- Engine -------------------------------------------------------------------

class SettingsEngine:
    """Read and write application settings backed by the ``settings`` table."""

    def __init__(self, db: "DatabaseManager"):
        self._db = db
        self._ensure_defaults()

    # -- Core CRUD ------------------------------------------------------------

    def get(self, key: str, default: Optional[str] = None) -> Optional[str]:
        """Retrieve a setting value by key.

        Args:
            key: The setting key (e.g. ``'jurisdiction.state'``).
            default: Value returned when the key does not exist.

        Returns:
            The stored string value, or *default*.
        """
        row = self._db.fetchone(
            "SELECT value FROM settings WHERE key = ?", (key,),
        )
        if row is None:
            return default
        return row["value"]

    def set(self, key: str, value: Any, *, category: Optional[str] = None) -> None:
        """Create or update a setting.

        Args:
            key: The setting key.
            value: The value to store (converted to string).
            category: Optional category tag.  If the key already exists the
                      category is only updated when explicitly provided.
        """
        str_value = str(value)
        existing = self._db.fetchone(
            "SELECT key FROM settings WHERE key = ?", (key,),
        )

        if existing:
            if category is not None:
                self._db.execute(
                    "UPDATE settings SET value = ?, category = ? WHERE key = ?",
                    (str_value, category, key),
                )
            else:
                self._db.execute(
                    "UPDATE settings SET value = ? WHERE key = ?",
                    (str_value, key),
                )
        else:
            cat = category or self._infer_category(key)
            self._db.execute(
                "INSERT INTO settings (key, value, category) VALUES (?, ?, ?)",
                (key, str_value, cat),
            )
        logger.debug("Setting %s = %s", key, str_value)

    def get_all(self) -> dict[str, str]:
        """Return every setting as a ``{key: value}`` dict."""
        rows = self._db.fetchall("SELECT key, value FROM settings ORDER BY key")
        return {r["key"]: r["value"] for r in rows}

    # -- Jurisdiction helpers -------------------------------------------------

    def get_jurisdiction(self) -> dict[str, Optional[str]]:
        """Return the current jurisdiction configuration.

        Returns:
            Dict with ``state``, ``county``, and ``court`` keys.
        """
        return {
            "state": self.get("jurisdiction.state"),
            "county": self.get("jurisdiction.county"),
            "court": self.get("jurisdiction.court"),
        }

    def set_jurisdiction(self, state: str, county: str, court_type: str) -> None:
        """Set the jurisdiction configuration.

        Args:
            state: State abbreviation (e.g. ``'MI'``).
            county: County name.
            court_type: Court name / circuit (e.g. ``'14th Circuit'``).
        """
        self.set("jurisdiction.state", state, category="jurisdiction")
        self.set("jurisdiction.county", county, category="jurisdiction")
        self.set("jurisdiction.court", court_type, category="jurisdiction")
        logger.info("Jurisdiction set to %s, %s -- %s", state, county, court_type)

    # -- Path helpers ---------------------------------------------------------

    def get_paths(self) -> dict[str, str]:
        """Return all configured directory paths.

        Returns:
            Dict with ``data_dir``, ``output_dir``, ``template_dir``, and
            ``model_dir`` keys.
        """
        return {
            "data_dir": self.get("paths.data_dir") or _auto_data_dir(),
            "output_dir": self.get("paths.output_dir") or "",
            "template_dir": self.get("paths.template_dir") or "",
            "model_dir": self.get("paths.model_dir") or "",
        }

    def set_path(self, name: str, path: str) -> None:
        """Set a specific path setting.

        Args:
            name: One of ``data_dir``, ``output_dir``, ``template_dir``,
                  ``model_dir``.
            path: The directory path to store.

        Raises:
            ValueError: If *name* is not a recognised path setting.
        """
        valid_names = ("data_dir", "output_dir", "template_dir", "model_dir")
        if name not in valid_names:
            raise ValueError(
                f"Invalid path name '{name}'. Must be one of {valid_names}"
            )
        self.set(f"paths.{name}", path, category="paths")
        logger.info("Path %s set to %s", name, path)

    # -- Internal helpers -----------------------------------------------------

    def _ensure_defaults(self) -> None:
        """Seed any missing default settings into the database."""
        conn = self._db.connect()
        try:
            for key, (value, category) in _DEFAULTS.items():
                existing = conn.execute(
                    "SELECT key FROM settings WHERE key = ?", (key,),
                ).fetchone()
                if existing is None:
                    # Auto-detect data_dir at seed time
                    if key == "paths.data_dir" and not value:
                        value = _auto_data_dir()
                    conn.execute(
                        "INSERT INTO settings (key, value, category) VALUES (?, ?, ?)",
                        (key, value, category),
                    )
            conn.commit()
            logger.debug("Default settings ensured.")
        except Exception:
            conn.rollback()
            logger.exception("Failed to seed default settings")
            raise
        finally:
            conn.close()

    @staticmethod
    def _infer_category(key: str) -> str:
        """Infer a category from the dotted key prefix."""
        prefix = key.split(".")[0] if "." in key else key
        mapping = {
            "jurisdiction": "jurisdiction",
            "paths": "paths",
            "llm": "ai",
            "app": "display",
            "ai": "ai",
        }
        return mapping.get(prefix, "general")
