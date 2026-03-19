"""Unit tests for the MCP server database layer (litigation_context_mcp.db).

Tests the core functions against a temporary SQLite database so we never
touch the production 10 GB database.
"""

import os
import sys
import sqlite3
import tempfile
import unittest

# UTF-8 stdout for Windows — only when running standalone (not under pytest)
if "pytest" not in sys.modules:
    sys.stdout = open(sys.stdout.fileno(), mode="w", encoding="utf-8", errors="replace")

# Add the MCP server package to sys.path so we can import it
# Parent dir is the mcp_server package root
MCP_PKG = os.path.normpath(os.path.join(os.path.dirname(__file__), os.pardir))
sys.path.insert(0, MCP_PKG)


class TestMCPImport(unittest.TestCase):
    """Verify the db module can be imported without side-effects."""

    def test_import_db_module(self):
        import litigation_context_mcp.db as db
        self.assertTrue(hasattr(db, "get_stats"))
        self.assertTrue(hasattr(db, "safe_fts_search"))
        self.assertTrue(hasattr(db, "get_connection"))

    def test_create_sql_exists(self):
        import litigation_context_mcp.db as db
        self.assertIsInstance(db._CREATE_SQL, str)
        self.assertIn("CREATE TABLE", db._CREATE_SQL)

    def test_db_path_is_string(self):
        import litigation_context_mcp.db as db
        self.assertIsInstance(db.DB_PATH, str)
        self.assertTrue(db.DB_PATH.endswith(".db"))


class _TempDBMixin:
    """Mixin that creates a temporary DB with the MCP schema for each test."""

    def setUp(self):
        import litigation_context_mcp.db as db
        self._db_mod = db
        self._tmpdir = tempfile.mkdtemp()
        self._db_path = os.path.join(self._tmpdir, "test_mcp.db")
        self.conn = sqlite3.connect(self._db_path)
        self.conn.row_factory = sqlite3.Row
        self.conn.execute("PRAGMA journal_mode=WAL")
        self.conn.execute("PRAGMA busy_timeout=60000")
        self.conn.execute("PRAGMA foreign_keys=ON")
        # Create the full MCP schema
        self.conn.executescript(db._CREATE_SQL)
        self.conn.executescript(db._ERROR_TELEMETRY_SQL)
        self.conn.commit()

    def tearDown(self):
        self.conn.close()
        try:
            os.remove(self._db_path)
            os.rmdir(self._tmpdir)
        except OSError:
            pass


class TestGetStats(_TempDBMixin, unittest.TestCase):
    """Test get_stats() against an empty and populated DB."""

    def test_get_stats_returns_dict(self):
        result = self._db_mod.get_stats(self.conn)
        self.assertIsInstance(result, dict)

    def test_get_stats_expected_keys(self):
        result = self._db_mod.get_stats(self.conn)
        expected_keys = {
            "total_documents",
            "total_pages",
            "total_size_bytes",
            "total_size_mb",
            "graph_nodes",
            "court_rules_indexed",
            "rules_text_entries",
            "risk_events",
            "graphs_loaded",
            "database_path",
            "last_ingested_at",
        }
        self.assertEqual(set(result.keys()), expected_keys)

    def test_get_stats_empty_db_zeros(self):
        result = self._db_mod.get_stats(self.conn)
        self.assertEqual(result["total_documents"], 0)
        self.assertEqual(result["total_pages"], 0)
        self.assertEqual(result["total_size_bytes"], 0)
        self.assertEqual(result["total_size_mb"], 0.0)
        self.assertEqual(result["graph_nodes"], 0)
        self.assertEqual(result["court_rules_indexed"], 0)
        self.assertEqual(result["rules_text_entries"], 0)
        self.assertEqual(result["risk_events"], 0)
        self.assertIsInstance(result["graphs_loaded"], list)
        self.assertEqual(len(result["graphs_loaded"]), 0)
        self.assertIsNone(result["last_ingested_at"])

    def test_get_stats_after_insert(self):
        """Insert a document and verify counts update."""
        self.conn.execute(
            "INSERT INTO documents (file_path, file_name, file_size_bytes, ingested_at) "
            "VALUES (?, ?, ?, ?)",
            ("/tmp/test.pdf", "test.pdf", 1024, "2025-01-01T00:00:00"),
        )
        self.conn.commit()
        result = self._db_mod.get_stats(self.conn)
        self.assertEqual(result["total_documents"], 1)
        self.assertEqual(result["total_size_bytes"], 1024)
        self.assertEqual(result["last_ingested_at"], "2025-01-01T00:00:00")


class TestFTS5Search(_TempDBMixin, unittest.TestCase):
    """Test FTS5 search functionality via safe_fts_search."""

    def _insert_page(self, doc_id, page_num, text):
        self.conn.execute(
            "INSERT INTO pages (document_id, page_number, text_content) VALUES (?, ?, ?)",
            (doc_id, page_num, text),
        )
        self.conn.commit()

    def _insert_doc(self, path, name):
        cur = self.conn.execute(
            "INSERT INTO documents (file_path, file_name, file_size_bytes, ingested_at) "
            "VALUES (?, ?, ?, ?)",
            (path, name, 100, "2025-01-01T00:00:00"),
        )
        self.conn.commit()
        return cur.lastrowid

    def test_fts_search_empty_result(self):
        """Search on empty pages table returns empty list."""
        results, total = self._db_mod.safe_fts_search(
            self.conn,
            fts_table="pages_fts",
            match_col="text_content",
            query="nonexistent",
            select_sql="SELECT p.id, p.text_content FROM pages_fts f JOIN pages p ON f.rowid = p.id",
        )
        self.assertIsInstance(results, list)
        self.assertEqual(len(results), 0)
        self.assertEqual(total, 0)

    def test_fts_search_finds_content(self):
        """Insert text and verify FTS5 finds it."""
        doc_id = self._insert_doc("/test/custody.pdf", "custody.pdf")
        self._insert_page(doc_id, 1, "Michigan custody agreement between parents")
        self._insert_page(doc_id, 2, "Financial records and bank statements")

        results, total = self._db_mod.safe_fts_search(
            self.conn,
            fts_table="pages_fts",
            match_col="text_content",
            query="custody",
            select_sql="SELECT p.id, p.text_content FROM pages_fts f JOIN pages p ON f.rowid = p.id",
        )
        self.assertGreaterEqual(total, 1)
        self.assertTrue(any("custody" in r["text_content"].lower() for r in results))

    def test_fts_search_bad_syntax_graceful(self):
        """Malformed FTS5 queries should not raise — safe_fts_search handles them."""
        results, total = self._db_mod.safe_fts_search(
            self.conn,
            fts_table="pages_fts",
            match_col="text_content",
            query="AND OR NOT",
            select_sql="SELECT p.id, p.text_content FROM pages_fts f JOIN pages p ON f.rowid = p.id",
        )
        self.assertIsInstance(results, list)


class TestCircuitBreaker(unittest.TestCase):
    """Test the CircuitBreaker class."""

    def test_circuit_breaker_initial_state(self):
        from litigation_context_mcp.db import CircuitBreaker
        cb = CircuitBreaker(failure_threshold=3, reset_timeout=60.0)
        self.assertFalse(cb.is_open)
        self.assertEqual(cb.status["state"], "closed")

    def test_circuit_breaker_opens_after_threshold(self):
        from litigation_context_mcp.db import CircuitBreaker
        cb = CircuitBreaker(failure_threshold=2, reset_timeout=60.0)
        cb.record_failure()
        self.assertFalse(cb.is_open)
        cb.record_failure()
        self.assertTrue(cb.is_open)

    def test_circuit_breaker_reset(self):
        from litigation_context_mcp.db import CircuitBreaker
        cb = CircuitBreaker(failure_threshold=2, reset_timeout=60.0)
        cb.record_failure()
        cb.record_failure()
        self.assertTrue(cb.is_open)
        cb.reset()
        self.assertFalse(cb.is_open)
        self.assertEqual(cb.status["state"], "closed")

    def test_circuit_breaker_success_resets_count(self):
        from litigation_context_mcp.db import CircuitBreaker
        cb = CircuitBreaker(failure_threshold=3)
        cb.record_failure()
        cb.record_failure()
        cb.record_success()
        self.assertFalse(cb.is_open)
        self.assertEqual(cb.status["failure_count"], 0)


class TestErrorCodes(unittest.TestCase):
    """Test ErrorCode enum and StructuredError."""

    def test_error_codes_exist(self):
        from litigation_context_mcp.db import ErrorCode
        self.assertTrue(hasattr(ErrorCode, "ERR_DB_CONNECT"))
        self.assertTrue(hasattr(ErrorCode, "ERR_DB_LOCKED"))
        self.assertTrue(hasattr(ErrorCode, "ERR_CIRCUIT_OPEN"))

    def test_structured_error_to_dict(self):
        from litigation_context_mcp.db import StructuredError, ErrorCode
        err = StructuredError(ErrorCode.ERR_DB_CONNECT, "test failure")
        d = err.to_dict()
        self.assertIn("error_code", d)
        self.assertIn("message", d)
        self.assertIn("recovery_hint", d)
        self.assertEqual(d["message"], "test failure")


if __name__ == "__main__":
    unittest.main(verbosity=2)
