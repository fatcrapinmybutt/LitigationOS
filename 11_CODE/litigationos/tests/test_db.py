"""Tests for database connection and schema initialization."""

import sqlite3
import threading
from pathlib import Path

import pytest

from litigationos.db.connection import DatabaseManager


# ============================================================================
# Connection & PRAGMA tests
# ============================================================================


class TestDatabaseConnection:
    """Test DatabaseManager connection and PRAGMAs."""

    def test_connect_returns_connection(self, tmp_db: DatabaseManager):
        conn = tmp_db.connect()
        assert isinstance(conn, sqlite3.Connection)
        conn.close()

    def test_wal_mode(self, tmp_db: DatabaseManager):
        conn = tmp_db.connect()
        mode = conn.execute("PRAGMA journal_mode").fetchone()
        conn.close()
        assert mode[0] == "wal"

    def test_foreign_keys_enabled(self, tmp_db: DatabaseManager):
        conn = tmp_db.connect()
        fk = conn.execute("PRAGMA foreign_keys").fetchone()
        conn.close()
        assert fk[0] == 1

    def test_busy_timeout_set(self, tmp_db: DatabaseManager):
        conn = tmp_db.connect()
        timeout = conn.execute("PRAGMA busy_timeout").fetchone()
        conn.close()
        assert timeout[0] == 60000

    def test_cache_size_set(self, tmp_db: DatabaseManager):
        conn = tmp_db.connect()
        cache = conn.execute("PRAGMA cache_size").fetchone()
        conn.close()
        assert cache[0] == -32000

    def test_row_factory_is_row(self, tmp_db: DatabaseManager):
        conn = tmp_db.connect()
        assert conn.row_factory == sqlite3.Row
        conn.close()


# ============================================================================
# Schema initialization tests
# ============================================================================


class TestSchemaInitialization:
    """Test DatabaseManager.initialize() creates all tables."""

    def test_initialize_creates_core_tables(self, tmp_db: DatabaseManager):
        conn = tmp_db.connect()
        tables = conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table' ORDER BY name"
        ).fetchall()
        table_names = [t["name"] for t in tables]
        conn.close()

        expected = [
            "cases", "claims", "court_rules", "courts",
            "deadlines", "documents", "evidence", "filings",
            "jurisdictions", "parties", "scao_forms",
            "settings", "templates", "timeline_events",
        ]
        for tbl in expected:
            assert tbl in table_names, f"Table '{tbl}' missing from schema"

    def test_initialize_creates_fts_tables(self, tmp_db: DatabaseManager):
        conn = tmp_db.connect()
        tables = conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table' ORDER BY name"
        ).fetchall()
        table_names = [t["name"] for t in tables]
        conn.close()

        assert "evidence_fts" in table_names
        assert "court_rules_fts" in table_names

    def test_initialize_creates_indexes(self, tmp_db: DatabaseManager):
        conn = tmp_db.connect()
        indexes = conn.execute(
            "SELECT name FROM sqlite_master WHERE type='index' AND name LIKE 'idx_%'"
        ).fetchall()
        conn.close()
        index_names = [i["name"] for i in indexes]

        assert "idx_cases_status" in index_names
        assert "idx_filings_case" in index_names
        assert "idx_evidence_bates" in index_names
        assert "idx_deadlines_due_date" in index_names

    def test_initialize_seeds_michigan(self, tmp_db: DatabaseManager):
        row = tmp_db.fetchone("SELECT * FROM jurisdictions WHERE id = 'MI'")
        assert row is not None
        assert row["name"] == "Michigan"

    def test_initialize_seeds_default_settings(self, tmp_db: DatabaseManager):
        row = tmp_db.fetchone("SELECT * FROM settings WHERE key = 'default_jurisdiction'")
        assert row is not None
        assert row["value"] == "MI"

    def test_double_initialize_is_safe(self, tmp_db: DatabaseManager):
        tmp_db.initialize()
        conn = tmp_db.connect()
        tables = conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name='cases'"
        ).fetchall()
        conn.close()
        assert len(tables) == 1

    def test_initialize_from_scratch(self, tmp_path: Path):
        db_path = tmp_path / "fresh.db"
        db = DatabaseManager(db_path)
        db.initialize()
        row = db.fetchone("SELECT COUNT(*) AS cnt FROM cases")
        assert row["cnt"] == 0


# ============================================================================
# Helper method tests
# ============================================================================


class TestHelperMethods:
    """Test execute/fetchone/fetchall convenience methods."""

    def test_execute_insert_and_lastrowid(self, tmp_db: DatabaseManager):
        cursor = tmp_db.execute(
            "INSERT INTO cases (title, status) VALUES (?, ?)",
            ("Test Case", "active"),
        )
        assert cursor.lastrowid is not None
        assert cursor.lastrowid > 0

    def test_fetchone_returns_row(self, tmp_db: DatabaseManager, sample_case: dict):
        row = tmp_db.fetchone("SELECT * FROM cases WHERE id = ?", (sample_case["id"],))
        assert row is not None
        assert row["title"] == "Pigors v. Watson"

    def test_fetchone_returns_none(self, tmp_db: DatabaseManager):
        row = tmp_db.fetchone("SELECT * FROM cases WHERE id = ?", (99999,))
        assert row is None

    def test_fetchall_returns_list(self, tmp_db: DatabaseManager, sample_case: dict):
        rows = tmp_db.fetchall("SELECT * FROM cases")
        assert isinstance(rows, list)
        assert len(rows) >= 1

    def test_fetchall_empty(self, tmp_db: DatabaseManager):
        rows = tmp_db.fetchall("SELECT * FROM cases WHERE status = 'nonexistent'")
        assert rows == []

    def test_execute_with_params(self, tmp_db: DatabaseManager, sample_case: dict):
        tmp_db.execute(
            "UPDATE cases SET status = ? WHERE id = ?",
            ("closed", sample_case["id"]),
        )
        row = tmp_db.fetchone("SELECT status FROM cases WHERE id = ?", (sample_case["id"],))
        assert row["status"] == "closed"


# ============================================================================
# Concurrency tests
# ============================================================================


class TestConcurrency:
    """Test that concurrent connections don't deadlock."""

    def test_concurrent_reads(self, tmp_db: DatabaseManager, sample_case: dict):
        results = []
        errors = []

        def reader():
            try:
                row = tmp_db.fetchone("SELECT * FROM cases WHERE id = ?", (sample_case["id"],))
                results.append(row["title"])
            except Exception as e:
                errors.append(str(e))

        threads = [threading.Thread(target=reader) for _ in range(5)]
        for t in threads:
            t.start()
        for t in threads:
            t.join(timeout=10)

        assert not errors, f"Concurrent read errors: {errors}"
        assert len(results) == 5
        assert all(r == "Pigors v. Watson" for r in results)

    def test_concurrent_writes(self, tmp_db: DatabaseManager):
        errors = []

        def writer(n: int):
            try:
                tmp_db.execute(
                    "INSERT INTO cases (title, status) VALUES (?, ?)",
                    (f"Concurrent Case {n}", "active"),
                )
            except Exception as e:
                errors.append(str(e))

        threads = [threading.Thread(target=writer, args=(i,)) for i in range(5)]
        for t in threads:
            t.start()
        for t in threads:
            t.join(timeout=30)

        assert not errors, f"Concurrent write errors: {errors}"
        rows = tmp_db.fetchall("SELECT * FROM cases WHERE title LIKE 'Concurrent Case%'")
        assert len(rows) == 5
