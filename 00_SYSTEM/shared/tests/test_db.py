"""
Contract tests for shared.internal.db — Database connection factory.

These tests lock the PUBLIC behavior of get_db() and get_db_path()
so that engine migration can proceed safely.
"""

import os
import sqlite3
import pytest
from pathlib import Path

# Add 00_SYSTEM to path for import resolution
import sys
_system_dir = str(Path(__file__).resolve().parent.parent.parent)
if _system_dir not in sys.path:
    sys.path.insert(0, _system_dir)

from shared import get_db, get_db_path, STANDARD_PRAGMAS, LitigationDBError


class TestGetDbPath:
    """Contract: get_db_path() resolves logical names to filesystem paths."""

    def test_default_is_litigation(self):
        """Default name maps to litigation_context.db."""
        path = get_db_path()
        assert path.name == "litigation_context.db"

    def test_litigation_explicit(self):
        """Explicit 'litigation' maps to litigation_context.db."""
        path = get_db_path("litigation")
        assert path.name == "litigation_context.db"

    def test_brain_database(self):
        """Brain names map to 00_SYSTEM/brains/*.db."""
        path = get_db_path("authority_brain")
        assert "brains" in str(path)
        assert path.name == "authority_brain.db"

    def test_unknown_name_raises(self):
        """Unknown database names raise LitigationDBError."""
        with pytest.raises(LitigationDBError, match="Unknown database"):
            get_db_path("nonexistent_db_that_will_never_exist")

    def test_env_override_litigation(self, tmp_path, monkeypatch):
        """LITIGATION_DB_PATH env var overrides default path."""
        fake_db = tmp_path / "test.db"
        fake_db.touch()
        monkeypatch.setenv("LITIGATION_DB_PATH", str(fake_db))
        path = get_db_path("litigation")
        assert path == fake_db

    def test_returns_path_object(self):
        """Always returns a Path, not a string."""
        path = get_db_path()
        assert isinstance(path, Path)


class TestGetDb:
    """Contract: get_db() returns a properly configured connection."""

    def test_returns_connection(self):
        """Returns a sqlite3.Connection for the default DB."""
        conn = get_db()
        try:
            assert isinstance(conn, sqlite3.Connection)
        finally:
            conn.close()

    def test_wal_mode(self):
        """Connection uses WAL journal mode."""
        conn = get_db()
        try:
            mode = conn.execute("PRAGMA journal_mode").fetchone()[0]
            assert mode.lower() == "wal"
        finally:
            conn.close()

    def test_row_factory_is_row(self):
        """Connection has row_factory = sqlite3.Row."""
        conn = get_db()
        try:
            assert conn.row_factory is sqlite3.Row
        finally:
            conn.close()

    def test_busy_timeout_set(self):
        """busy_timeout is set to a reasonable value (>= 30s)."""
        conn = get_db()
        try:
            timeout = conn.execute("PRAGMA busy_timeout").fetchone()[0]
            assert timeout >= 30000
        finally:
            conn.close()

    def test_cache_size_set(self):
        """cache_size is set (non-default)."""
        conn = get_db()
        try:
            cache = conn.execute("PRAGMA cache_size").fetchone()[0]
            # Standard PRAGMAs set -32000 (32MB), verify it's negative (KB mode)
            assert cache < 0 or cache > 2000
        finally:
            conn.close()

    def test_temp_store_memory(self):
        """temp_store is set to MEMORY (2)."""
        conn = get_db()
        try:
            temp = conn.execute("PRAGMA temp_store").fetchone()[0]
            assert temp == 2
        finally:
            conn.close()

    def test_unknown_db_raises(self):
        """Unknown DB name raises LitigationDBError."""
        with pytest.raises(LitigationDBError, match="Unknown database"):
            get_db("this_db_does_not_exist_at_all")

    def test_readonly_mode(self):
        """readonly=True sets query_only pragma."""
        conn = get_db(readonly=True)
        try:
            qo = conn.execute("PRAGMA query_only").fetchone()[0]
            assert qo == 1
        finally:
            conn.close()

    def test_brain_db_connection(self):
        """Can connect to a brain database."""
        brain_path = get_db_path("authority_brain")
        if brain_path.exists():
            conn = get_db("authority_brain")
            try:
                assert isinstance(conn, sqlite3.Connection)
            finally:
                conn.close()
        else:
            pytest.skip("authority_brain.db not found")


class TestStandardPragmas:
    """Contract: STANDARD_PRAGMAS has the expected keys and types."""

    def test_has_required_keys(self):
        """STANDARD_PRAGMAS includes the critical performance settings."""
        required = {"busy_timeout", "journal_mode", "cache_size", "temp_store"}
        assert required.issubset(set(STANDARD_PRAGMAS.keys()))

    def test_busy_timeout_value(self):
        """busy_timeout is at least 30 seconds."""
        assert STANDARD_PRAGMAS["busy_timeout"] >= 30000

    def test_journal_mode_is_wal(self):
        """journal_mode is WAL."""
        assert STANDARD_PRAGMAS["journal_mode"] == "WAL"
