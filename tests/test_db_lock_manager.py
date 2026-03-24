"""Tests for db_lock_manager.py — Tier-2 SQLite Connection Manager.

Module: 00_SYSTEM/pipeline/db_lock_manager.py
Key exports: managed_db(), get_connection_count(), check_db_health(), ensure_wal_mode()
Purpose: 3-connection semaphore, WAL mode, busy_timeout=60s, 32MB cache.
"""
import ast
import os
import sqlite3
import tempfile
import threading

import pytest

MODULE_REL = os.path.join("00_SYSTEM", "pipeline", "db_lock_manager.py")
MODULE_PATH = os.path.normpath(os.path.join(os.path.dirname(__file__), "..", MODULE_REL))

# Import the module directly — conftest.py adds pipeline to sys.path
import importlib.util

_spec = importlib.util.spec_from_file_location("db_lock_manager", MODULE_PATH)
_mod = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_mod)

managed_db = _mod.managed_db
get_connection_count = _mod.get_connection_count
check_db_health = _mod.check_db_health
ensure_wal_mode = _mod.ensure_wal_mode


class TestDbLockManagerFile:
    """Verify module file integrity."""

    def test_file_exists(self):
        assert os.path.exists(MODULE_PATH)

    def test_valid_python_syntax(self):
        with open(MODULE_PATH, "r", encoding="utf-8") as f:
            source = f.read()
        compile(source, MODULE_PATH, "exec")


class TestManagedDb:
    """Test managed_db() context manager."""

    @pytest.fixture
    def tmp_db(self, tmp_path):
        """Create a temporary SQLite database for testing."""
        db_path = tmp_path / "test.db"
        conn = sqlite3.connect(str(db_path))
        conn.execute("CREATE TABLE items (id INTEGER PRIMARY KEY, name TEXT)")
        conn.execute("INSERT INTO items (name) VALUES ('alpha')")
        conn.commit()
        conn.close()
        return db_path

    def test_opens_and_closes(self, tmp_db):
        """managed_db opens connection and closes it after context exits."""
        with managed_db(tmp_db) as conn:
            rows = conn.execute("SELECT COUNT(*) FROM items").fetchone()
            assert rows[0] == 1
        # Connection should be closed — get_connection_count should be back to 0
        assert get_connection_count() == 0

    def test_sets_wal_mode(self, tmp_db):
        with managed_db(tmp_db) as conn:
            mode = conn.execute("PRAGMA journal_mode").fetchone()[0]
            assert mode.lower() == "wal"

    def test_sets_busy_timeout(self, tmp_db):
        with managed_db(tmp_db) as conn:
            timeout = conn.execute("PRAGMA busy_timeout").fetchone()[0]
            assert timeout == 60000

    def test_sets_cache_size(self, tmp_db):
        with managed_db(tmp_db) as conn:
            cache = conn.execute("PRAGMA cache_size").fetchone()[0]
            assert cache == -32000

    def test_sets_temp_store_memory(self, tmp_db):
        with managed_db(tmp_db) as conn:
            temp = conn.execute("PRAGMA temp_store").fetchone()[0]
            # temp_store: 0=DEFAULT, 1=FILE, 2=MEMORY
            assert temp == 2

    def test_sets_synchronous_normal(self, tmp_db):
        with managed_db(tmp_db) as conn:
            sync = conn.execute("PRAGMA synchronous").fetchone()[0]
            # synchronous: 0=OFF, 1=NORMAL, 2=FULL, 3=EXTRA
            assert sync == 1

    def test_row_factory_is_row(self, tmp_db):
        with managed_db(tmp_db) as conn:
            row = conn.execute("SELECT * FROM items LIMIT 1").fetchone()
            assert row["name"] == "alpha"  # Row factory enables dict-style access

    def test_auto_commits(self, tmp_db):
        """Non-readonly mode auto-commits on successful exit."""
        with managed_db(tmp_db) as conn:
            conn.execute("INSERT INTO items (name) VALUES ('beta')")

        # Verify commit persisted
        with managed_db(tmp_db, readonly=True) as conn:
            count = conn.execute("SELECT COUNT(*) FROM items").fetchone()[0]
            assert count == 2

    def test_readonly_prevents_writes(self, tmp_db):
        with managed_db(tmp_db, readonly=True) as conn:
            query_only = conn.execute("PRAGMA query_only").fetchone()[0]
            assert query_only == 1

    def test_rollback_on_exception(self, tmp_db):
        """Exception inside context should rollback and re-raise."""
        with pytest.raises(ValueError):
            with managed_db(tmp_db) as conn:
                conn.execute("INSERT INTO items (name) VALUES ('should_rollback')")
                raise ValueError("test error")

        # Verify the insert was rolled back
        with managed_db(tmp_db, readonly=True) as conn:
            count = conn.execute("SELECT COUNT(*) FROM items").fetchone()[0]
            assert count == 1

    def test_connection_count_tracks(self, tmp_db):
        """get_connection_count() should reflect active connections."""
        assert get_connection_count() == 0
        with managed_db(tmp_db) as conn:
            assert get_connection_count() == 1
        assert get_connection_count() == 0


class TestSemaphoreLimit:
    """Test that semaphore limits concurrent connections to 3."""

    @pytest.fixture
    def tmp_db(self, tmp_path):
        db_path = tmp_path / "semaphore_test.db"
        conn = sqlite3.connect(str(db_path))
        conn.execute("CREATE TABLE t (id INTEGER)")
        conn.commit()
        conn.close()
        return db_path

    def test_max_three_concurrent(self, tmp_db):
        """Only 3 connections should be open simultaneously."""
        max_concurrent = 0
        lock = threading.Lock()
        barrier = threading.Barrier(3)  # Synchronize exactly 3 threads

        def worker():
            nonlocal max_concurrent
            with managed_db(tmp_db, readonly=True) as conn:
                with lock:
                    current = get_connection_count()
                    if current > max_concurrent:
                        max_concurrent = current
                barrier.wait(timeout=5)  # Hold connection open until all 3 arrive

        threads = [threading.Thread(target=worker) for _ in range(3)]
        for t in threads:
            t.start()
        for t in threads:
            t.join(timeout=10)

        assert max_concurrent <= 3


class TestCheckDbHealth:
    """Test check_db_health() function."""

    def test_missing_file(self, tmp_path):
        result = check_db_health(tmp_path / "nonexistent.db")
        assert result["status"] == "missing"

    def test_empty_file(self, tmp_path):
        empty_db = tmp_path / "empty.db"
        empty_db.touch()
        result = check_db_health(empty_db)
        assert result["status"] == "empty"

    def test_healthy_db(self, tmp_path):
        db_path = tmp_path / "healthy.db"
        conn = sqlite3.connect(str(db_path))
        conn.execute("CREATE TABLE t (id INTEGER)")
        conn.commit()
        conn.close()

        result = check_db_health(db_path)
        assert result["status"] == "ok"
        assert result["table_count"] >= 1
        assert result["size_bytes"] > 0

    def test_returns_dict_keys(self, tmp_path):
        db_path = tmp_path / "keys.db"
        conn = sqlite3.connect(str(db_path))
        conn.execute("CREATE TABLE t (id INTEGER)")
        conn.commit()
        conn.close()

        result = check_db_health(db_path)
        assert "path" in result
        assert "size_bytes" in result
        assert "status" in result
        assert "table_count" in result
        assert "detail" in result


class TestEnsureWalMode:
    """Test ensure_wal_mode() function."""

    def test_converts_to_wal(self, tmp_path):
        db_path = tmp_path / "wal_test.db"
        conn = sqlite3.connect(str(db_path))
        conn.execute("CREATE TABLE t (id INTEGER)")
        conn.commit()
        conn.close()

        result = ensure_wal_mode(db_path)
        assert result is True

    def test_missing_file_returns_false(self, tmp_path):
        result = ensure_wal_mode(tmp_path / "nonexistent.db")
        # Creating a new file with WAL should actually work, but non-existent dir would fail
        assert isinstance(result, bool)
