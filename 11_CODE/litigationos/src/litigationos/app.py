"""LitigationOS — Pro Se Litigation Management System.

Entry point for both GUI and CLI modes.  Handles frozen (PyInstaller)
vs. development execution, database initialisation, and argument parsing.
"""

from __future__ import annotations

import os
import sys
from pathlib import Path

from litigationos import __version__, __app_name__
from litigationos.db.connection import DatabaseManager


def get_data_dir() -> Path:
    """Return the application data directory.

    * Frozen (PyInstaller): ``<exe_dir>/data``
    * Development:          prefer the real litigation database location
    * Fallback:             ``~/LitigationOS/data``
    """
    if getattr(sys, "frozen", False):
        return Path(sys.executable).parent / "data"
    # Development: prefer the real litigation database location
    lit_dir = Path(r"C:\Users\andre\LitigationOS")
    if (lit_dir / "litigation_context.db").exists():
        return lit_dir
    return Path.home() / "LitigationOS" / "data"


def _fixup_frozen_paths() -> None:
    """When running as a PyInstaller bundle, ensure the bundled data
    directory is on ``sys.path`` so relative imports still work."""
    if getattr(sys, "frozen", False):
        bundle_dir = Path(sys._MEIPASS)  # type: ignore[attr-defined]
        if str(bundle_dir) not in sys.path:
            sys.path.insert(0, str(bundle_dir))


def create_app(data_dir: Path | None = None) -> App:
    """Initialize and return the application instance."""
    data_dir = data_dir or get_data_dir()
    data_dir.mkdir(parents=True, exist_ok=True)

    db_path = (
        data_dir / "litigation_context.db"
        if (data_dir / "litigation_context.db").exists()
        else data_dir / "litigationos.db"
    )
    db = DatabaseManager(db_path)
    db.initialize()

    try:
        from litigationos.config import Settings
        settings = Settings(db)
    except ImportError:
        settings = None  # type: ignore[assignment]

    return App(db=db, settings=settings, data_dir=data_dir)


class App:
    """Core application container holding shared resources."""

    def __init__(self, db: DatabaseManager, settings, data_dir: Path):
        self.db = db
        self.settings = settings
        self.data_dir = data_dir
        self.version = __version__
        self.name = __app_name__

    def run_gui(self):
        """Launch the CustomTkinter GUI."""
        from litigationos.gui.app import LitigationOSApp

        db_path = (
            self.data_dir / "litigation_context.db"
            if (self.data_dir / "litigation_context.db").exists()
            else self.data_dir / "litigationos.db"
        )
        window = LitigationOSApp(db_path=db_path)
        window.mainloop()

    def run_cli(self):
        """Launch the Typer CLI."""
        from litigationos.cli.main import app as cli_app

        cli_app()


def main():
    """Entry point — parses CLI flags, initialises DB, launches GUI."""
    _fixup_frozen_paths()

    import argparse

    parser = argparse.ArgumentParser(
        prog="LitigationOS",
        description="Pro Se Litigation Management System",
    )
    parser.add_argument("--db-path", help="Path to SQLite database file")
    parser.add_argument(
        "--init-only",
        action="store_true",
        help="Initialize the database and exit",
    )
    parser.add_argument(
        "--version",
        action="store_true",
        help="Print version and exit",
    )
    args = parser.parse_args()

    if args.version:
        print(f"LitigationOS v{__version__}")
        return

    # Resolve data directory and database path
    data_dir = get_data_dir()
    data_dir.mkdir(parents=True, exist_ok=True)

    db_path = Path(args.db_path) if args.db_path else (
        data_dir / "litigation_context.db"
        if (data_dir / "litigation_context.db").exists()
        else data_dir / "litigationos.db"
    )
    db_path.parent.mkdir(parents=True, exist_ok=True)

    db = DatabaseManager(db_path)
    db.initialize()

    if args.init_only:
        print(f"Database initialized at {db_path}")
        return

    from litigationos.gui.app import LitigationOSApp

    window = LitigationOSApp(db_path=db_path)
    window.mainloop()


if __name__ == "__main__":
    main()
