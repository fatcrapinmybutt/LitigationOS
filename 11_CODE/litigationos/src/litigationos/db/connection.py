"""SQLite connection manager with WAL mode, busy timeout, and schema initialization.

Usage:
    db = DatabaseManager("path/to/litigationos.db")
    db.initialize()         # Creates schema if needed
    conn = db.connect()     # Get a connection with proper PRAGMAs
"""

from __future__ import annotations

import sqlite3
from pathlib import Path


class DatabaseManager:
    """Manages SQLite connections with performance-tuned PRAGMAs."""

    def __init__(self, db_path: str | Path):
        self.db_path = Path(db_path)

    def connect(self) -> sqlite3.Connection:
        """Open a new connection with WAL mode, foreign keys, and busy timeout."""
        conn = sqlite3.connect(str(self.db_path), timeout=120)
        conn.execute("PRAGMA busy_timeout=60000")
        conn.execute("PRAGMA journal_mode=WAL")
        conn.execute("PRAGMA foreign_keys=ON")
        conn.execute("PRAGMA cache_size=-32000")
        conn.row_factory = sqlite3.Row
        return conn

    def initialize(self) -> None:
        """Create the database schema if tables don't exist yet."""
        schema_path = Path(__file__).parent / "schema.sql"
        if not schema_path.exists():
            raise FileNotFoundError(f"Schema file not found: {schema_path}")

        conn = self.connect()
        try:
            # Check if already initialized
            tables = conn.execute(
                "SELECT name FROM sqlite_master WHERE type='table' AND name='cases'"
            ).fetchone()
            if tables is None:
                schema_sql = schema_path.read_text(encoding="utf-8")
                conn.executescript(schema_sql)
            conn.commit()
        finally:
            conn.close()

        # Seed default data (idempotent — checks before inserting)
        from litigationos.db.seed import seed_michigan, seed_default_settings
        seed_michigan(self)
        seed_default_settings(self)

    def execute(self, sql: str, params: tuple = ()) -> sqlite3.Cursor:
        """Execute a single SQL statement and return the cursor."""
        conn = self.connect()
        try:
            cursor = conn.execute(sql, params)
            conn.commit()
            return cursor
        finally:
            conn.close()

    def fetchone(self, sql: str, params: tuple = ()) -> sqlite3.Row | None:
        """Execute and fetch a single row."""
        conn = self.connect()
        try:
            return conn.execute(sql, params).fetchone()
        finally:
            conn.close()

    def fetchall(self, sql: str, params: tuple = ()) -> list[sqlite3.Row]:
        """Execute and fetch all rows."""
        conn = self.connect()
        try:
            return conn.execute(sql, params).fetchall()
        finally:
            conn.close()
