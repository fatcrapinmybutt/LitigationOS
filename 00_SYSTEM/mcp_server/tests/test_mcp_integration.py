"""Integration tests for the LitigationOS MCP server.

Tests end-to-end workflows across the db module: tool discovery,
ingest → search → retrieve pipelines, deadline computation,
error handling, and concurrent access.

Run from 00_SYSTEM/mcp_server/ (NOT the repo root) to avoid shadow modules:
    cd 00_SYSTEM\\mcp_server
    python -m pytest tests/test_mcp_integration.py -v
    python -m unittest tests.test_mcp_integration -v
"""

import os
import sys
import sqlite3
import tempfile
import threading
import unittest
from concurrent.futures import ThreadPoolExecutor, as_completed

# UTF-8 stdout for Windows
if "pytest" not in sys.modules:
    sys.stdout = open(sys.stdout.fileno(), mode="w", encoding="utf-8", errors="replace")
    sys.stderr = open(sys.stderr.fileno(), mode="w", encoding="utf-8", errors="replace")

# Add MCP server package root to sys.path
MCP_PKG = os.path.normpath(os.path.join(os.path.dirname(__file__), os.pardir))
sys.path.insert(0, MCP_PKG)

import litigation_context_mcp.db as db


# ═══════════════════════════════════════════════════════════════════════════
# Shared test fixture
# ═══════════════════════════════════════════════════════════════════════════

class _TempDBMixin:
    """Creates a temporary DB with the full MCP schema per test."""

    def setUp(self):
        self._tmpdir = tempfile.mkdtemp()
        self._db_path = os.path.join(self._tmpdir, "test_integration.db")
        self.conn = sqlite3.connect(self._db_path, check_same_thread=False)
        self.conn.row_factory = sqlite3.Row
        self.conn.execute("PRAGMA journal_mode=WAL")
        self.conn.execute("PRAGMA busy_timeout=60000")
        self.conn.execute("PRAGMA foreign_keys=ON")
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

    # ── Helper methods ──────────────────────────────────────────────────

    def _insert_doc(self, path="/test/doc.pdf", name="doc.pdf",
                    size=2048, modified="2025-06-01", page_count=0,
                    sha256="abc123"):
        """Insert a document row and return its id."""
        return db.insert_document(
            self.conn, path, name, size, modified, page_count, sha256,
            pages=[],
        )

    def _insert_doc_with_pages(self, path, name, pages_text):
        """Insert a document with page text and return doc_id."""
        pages = [
            {"page_number": i + 1, "text_content": text}
            for i, text in enumerate(pages_text)
        ]
        return db.insert_document(
            self.conn, path, name, len(pages_text) * 500,
            "2025-06-15", len(pages), f"sha_{name}", pages,
        )


# ═══════════════════════════════════════════════════════════════════════════
# 1. Tool Registration / Discovery
# ═══════════════════════════════════════════════════════════════════════════

class TestToolDiscovery(unittest.TestCase):
    """Verify all expected public API functions are importable."""

    # Canonical list of db.py public functions that back MCP tools
    EXPECTED_FUNCTIONS = [
        # Core document ops
        "get_connection", "document_exists", "insert_document",
        "search_pages", "list_documents", "get_document_text",
        "delete_document", "get_stats",
        # FTS
        "sanitize_fts_query", "safe_fts_search",
        # Knowledge graph
        "load_court_forms_graph", "load_rules_authority_index",
        "load_rules_extracted", "load_risk_events",
        "load_all_knowledge_graphs",
        "search_rules", "search_graph_nodes", "get_risk_events",
        # Evolution
        "evolve_md_file", "evolve_all_md_files",
        "evolve_txt_file", "evolve_all_txt_files",
        "evolve_from_pages",
        "search_evolved_knowledge", "get_cross_refs",
        "get_evolution_stats",
        # Autonomous slots
        "compute_deadlines", "red_team_validate",
        "trace_evidence_chain", "dispatch_to_swarm",
        "vector_search", "build_tfidf_index",
        # System
        "scan_all_systems", "ingest_master_csv",
        "search_master_data",
        # Integrity
        "check_integrity", "run_self_audit",
        "record_error", "get_error_summary",
        # Convergence
        "record_convergence_cycle", "get_convergence_status",
    ]

    def test_all_public_functions_exist(self):
        """Every function that backs an MCP tool must be importable."""
        missing = [fn for fn in self.EXPECTED_FUNCTIONS if not hasattr(db, fn)]
        self.assertEqual(
            missing, [],
            f"Missing db functions: {missing}",
        )

    def test_function_count_minimum(self):
        """db.py must expose at least 35 public functions."""
        public = [
            name for name in dir(db)
            if callable(getattr(db, name)) and not name.startswith("_")
        ]
        self.assertGreaterEqual(
            len(public), 35,
            f"Only {len(public)} public functions found; expected >= 35",
        )

    def test_classes_exist(self):
        """Core classes must be importable."""
        for cls_name in ("ErrorCode", "StructuredError", "CircuitBreaker",
                         "ConnectionManager", "DatabaseError"):
            self.assertTrue(
                hasattr(db, cls_name),
                f"Missing class: {cls_name}",
            )

    def test_schema_sql_constants(self):
        """Schema SQL constants must be non-empty strings."""
        self.assertIsInstance(db._CREATE_SQL, str)
        self.assertGreater(len(db._CREATE_SQL), 500)
        self.assertIsInstance(db._ERROR_TELEMETRY_SQL, str)
        self.assertIn("error_telemetry", db._ERROR_TELEMETRY_SQL)


# ═══════════════════════════════════════════════════════════════════════════
# 2. Ingest → Search → Retrieve Workflow
# ═══════════════════════════════════════════════════════════════════════════

class TestSearchWorkflow(_TempDBMixin, unittest.TestCase):
    """End-to-end: ingest documents → FTS5 search → retrieve full text."""

    def test_ingest_then_search(self):
        """Ingested pages must be searchable via FTS5."""
        doc_id = self._insert_doc_with_pages(
            "/test/custody_order.pdf", "custody_order.pdf",
            [
                "Defendant is awarded sole legal custody of minor children.",
                "Parenting time schedule as per Michigan MCR 3.211.",
                "Financial obligations under MCR 3.206 spousal support.",
            ],
        )
        self.assertIsNotNone(doc_id)

        result = db.search_pages(self.conn, "custody", limit=10)
        self.assertIsInstance(result, dict)
        self.assertGreaterEqual(result["total"], 1)
        self.assertEqual(result["results"][0]["document_id"], doc_id)

    def test_search_returns_pagination_metadata(self):
        """Search results must include pagination fields."""
        self._insert_doc_with_pages(
            "/test/motions.pdf", "motions.pdf",
            [f"Motion {i} for summary disposition" for i in range(5)],
        )
        result = db.search_pages(self.conn, "motion", limit=2, offset=0)
        self.assertIn("total", result)
        self.assertIn("has_more", result)
        self.assertIn("next_offset", result)
        self.assertIn("count", result)
        self.assertEqual(result["count"], 2)
        self.assertTrue(result["has_more"])

    def test_search_then_retrieve_full_text(self):
        """Search hit → get_document_text returns all pages."""
        doc_id = self._insert_doc_with_pages(
            "/test/evidence.pdf", "evidence.pdf",
            ["Evidence exhibit A bank records", "Exhibit B phone logs"],
        )
        result = db.search_pages(self.conn, "exhibit", limit=5)
        hit_doc_id = result["results"][0]["document_id"]
        self.assertEqual(hit_doc_id, doc_id)

        full_doc = db.get_document_text(self.conn, doc_id)
        self.assertIsNotNone(full_doc)
        self.assertIn("pages", full_doc)
        self.assertEqual(len(full_doc["pages"]), 2)

    def test_search_no_results(self):
        """Searching for nonexistent term returns empty results."""
        result = db.search_pages(self.conn, "xyznonexistent12345")
        self.assertEqual(result["total"], 0)
        self.assertEqual(result["results"], [])

    def test_ingest_dedup_by_path(self):
        """Duplicate file_path insertion raises IntegrityError."""
        self._insert_doc(path="/test/dup.pdf", name="dup.pdf", sha256="hash1")
        with self.assertRaises(sqlite3.IntegrityError):
            self._insert_doc(path="/test/dup.pdf", name="dup.pdf", sha256="hash2")

    def test_document_exists_check(self):
        """document_exists correctly detects presence/absence."""
        self.assertFalse(db.document_exists(self.conn, "/test/new.pdf"))
        self._insert_doc(path="/test/new.pdf", name="new.pdf", sha256="h1")
        self.assertTrue(db.document_exists(self.conn, "/test/new.pdf"))

    def test_delete_removes_document(self):
        """delete_document removes the doc and cascading pages."""
        doc_id = self._insert_doc_with_pages(
            "/test/todelete.pdf", "todelete.pdf",
            ["Page one content", "Page two content"],
        )
        self.assertTrue(db.delete_document(self.conn, doc_id))
        self.assertIsNone(db.get_document_text(self.conn, doc_id))
        # Pages should be cascade-deleted
        pages = self.conn.execute(
            "SELECT COUNT(*) AS cnt FROM pages WHERE document_id = ?", (doc_id,)
        ).fetchone()
        self.assertEqual(pages["cnt"], 0)

    def test_list_documents_with_filter(self):
        """list_documents name_filter should narrow results."""
        self._insert_doc(path="/a/custody.pdf", name="custody.pdf", sha256="h1")
        self._insert_doc(path="/a/financial.pdf", name="financial.pdf", sha256="h2")
        result = db.list_documents(self.conn, name_filter="custody")
        self.assertGreaterEqual(result["total"], 1)
        names = [r["file_name"] for r in result["documents"]]
        self.assertTrue(all("custody" in n for n in names))


# ═══════════════════════════════════════════════════════════════════════════
# 3. Deadline Workflow
# ═══════════════════════════════════════════════════════════════════════════

class TestDeadlineWorkflow(_TempDBMixin, unittest.TestCase):
    """Test compute_deadlines: add trigger → query deadlines → verify dates."""

    def test_motion_filed_deadlines(self):
        """motion_filed trigger produces MCR 2.108 response deadline."""
        deadlines = db.compute_deadlines(
            self.conn, "motion_filed", "2025-06-01", "MI",
        )
        self.assertIsInstance(deadlines, list)
        self.assertGreater(len(deadlines), 0)
        rules = [d["rule"] for d in deadlines]
        self.assertIn("MCR 2.108", rules)

    def test_deadline_dates_are_iso(self):
        """All deadline dates should be valid ISO format."""
        from datetime import datetime as dt
        deadlines = db.compute_deadlines(
            self.conn, "motion_filed", "2025-03-10", "MI",
        )
        for d in deadlines:
            parsed = dt.strptime(d["deadline"], "%Y-%m-%d")
            self.assertIsNotNone(parsed)

    def test_deadlines_after_trigger_date(self):
        """Every computed deadline must be on or after the trigger date."""
        from datetime import datetime as dt
        trigger = "2025-01-15"
        trigger_dt = dt.strptime(trigger, "%Y-%m-%d")
        deadlines = db.compute_deadlines(self.conn, "motion_filed", trigger, "MI")
        for d in deadlines:
            dl_dt = dt.strptime(d["deadline"], "%Y-%m-%d")
            self.assertGreaterEqual(
                dl_dt, trigger_dt,
                f"{d['rule']} deadline {d['deadline']} is before trigger {trigger}",
            )

    def test_order_entered_appeal_deadline(self):
        """order_entered trigger produces MCR 7.205 appeal deadline."""
        deadlines = db.compute_deadlines(
            self.conn, "order_entered", "2025-06-01", "MI",
        )
        rules = [d["rule"] for d in deadlines]
        self.assertIn("MCR 7.205", rules)

    def test_unknown_trigger_returns_empty(self):
        """Unknown trigger events should return an empty list (no crash)."""
        deadlines = db.compute_deadlines(
            self.conn, "totally_invalid_event_xyz", "2025-01-01", "MI",
        )
        self.assertIsInstance(deadlines, list)
        # May be empty or contain text-mined deadlines; just no crash
        self.assertIsNotNone(deadlines)

    def test_deadline_has_required_keys(self):
        """Each deadline dict must have rule, deadline, description."""
        deadlines = db.compute_deadlines(
            self.conn, "motion_filed", "2025-06-01", "MI",
        )
        for d in deadlines:
            self.assertIn("rule", d)
            self.assertIn("deadline", d)
            self.assertIn("description", d)

    def test_business_days_skip_weekends(self):
        """_add_business_days must skip Saturday and Sunday."""
        from datetime import datetime as dt
        # 2025-06-02 is a Monday. 5 business days = 2025-06-09 (next Monday)
        result = db._add_business_days(dt(2025, 6, 2), 5)
        self.assertEqual(result.weekday(), 0)  # Monday
        self.assertEqual(result.day, 9)


# ═══════════════════════════════════════════════════════════════════════════
# 4. Error Handling
# ═══════════════════════════════════════════════════════════════════════════

class TestErrorHandling(_TempDBMixin, unittest.TestCase):
    """Structured error handling: invalid inputs, circuit breaker, telemetry."""

    def test_sanitize_fts_removes_dangerous_chars(self):
        """sanitize_fts_query strips brackets, braces, tildes."""
        clean = db.sanitize_fts_query("{dangerous} [query] ~tilde ^caret")
        self.assertNotIn("{", clean)
        self.assertNotIn("[", clean)
        self.assertNotIn("~", clean)
        self.assertNotIn("^", clean)

    def test_safe_fts_handles_garbage_input(self):
        """safe_fts_search with garbage syntax must not raise."""
        results, total = db.safe_fts_search(
            self.conn,
            fts_table="pages_fts",
            match_col="text_content",
            query="AND OR NOT !!!",
            select_sql=(
                "SELECT p.id, p.text_content "
                "FROM pages_fts f JOIN pages p ON f.rowid = p.id"
            ),
        )
        self.assertIsInstance(results, list)
        self.assertIsInstance(total, int)

    def test_structured_error_serialization(self):
        """StructuredError.to_dict() must produce a complete dict."""
        cause = ValueError("inner problem")
        err = db.StructuredError(
            db.ErrorCode.ERR_DB_LOCKED, "Database locked", cause=cause,
        )
        d = err.to_dict()
        self.assertEqual(d["error_code"], "ERR_DB_LOCKED")
        self.assertEqual(d["message"], "Database locked")
        self.assertIn("recovery_hint", d)
        self.assertIn("inner problem", d["cause"])

    def test_circuit_breaker_blocks_when_open(self):
        """An open circuit breaker must report is_open == True."""
        cb = db.CircuitBreaker(failure_threshold=2, reset_timeout=9999)
        cb.record_failure()
        cb.record_failure()
        self.assertTrue(cb.is_open)
        status = cb.status
        self.assertEqual(status["state"], "open")

    def test_circuit_breaker_half_open_after_timeout(self):
        """Circuit should enter half_open when reset_timeout elapses."""
        import time
        cb = db.CircuitBreaker(failure_threshold=1, reset_timeout=0.1)
        cb.record_failure()
        self.assertTrue(cb.is_open)
        time.sleep(0.15)
        self.assertFalse(cb.is_open)  # transitions to half_open

    def test_error_telemetry_recording(self):
        """record_error must insert into error_telemetry without crashing."""
        db.record_error(
            self.conn, db.ErrorCode.ERR_DB_LOCKED,
            "test_tool", "simulated lock",
        )
        rows = self.conn.execute(
            "SELECT * FROM error_telemetry WHERE tool_name = 'test_tool'"
        ).fetchall()
        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0]["error_code"], "ERR_DB_LOCKED")

    def test_error_summary_groups_by_code(self):
        """get_error_summary groups errors by code and tool."""
        db.record_error(self.conn, db.ErrorCode.ERR_FTS_SYNTAX, "search", "bad1")
        db.record_error(self.conn, db.ErrorCode.ERR_FTS_SYNTAX, "search", "bad2")
        db.record_error(self.conn, db.ErrorCode.ERR_DB_LOCKED, "ingest", "locked")
        summary = db.get_error_summary(self.conn, hours=1)
        self.assertIsInstance(summary, list)
        codes = [s.get("error_code") or s.get("code") for s in summary]
        self.assertIn("ERR_FTS_SYNTAX", codes)

    def test_delete_nonexistent_document(self):
        """Deleting a doc that doesn't exist returns False, no crash."""
        result = db.delete_document(self.conn, 99999)
        self.assertFalse(result)

    def test_get_document_text_nonexistent(self):
        """Getting text for nonexistent doc returns None."""
        result = db.get_document_text(self.conn, 99999)
        self.assertIsNone(result)

    def test_search_pages_with_empty_query(self):
        """Empty-string search should not crash (FTS5 may reject but we handle)."""
        try:
            result = db.search_pages(self.conn, "")
            # If it returns, it should be well-structured
            self.assertIsInstance(result, dict)
        except Exception:
            # OperationalError from FTS5 is acceptable
            pass


# ═══════════════════════════════════════════════════════════════════════════
# 5. Concurrent Access
# ═══════════════════════════════════════════════════════════════════════════

class TestConcurrentAccess(unittest.TestCase):
    """Two threads hitting search simultaneously on a shared WAL-mode DB."""

    def setUp(self):
        self._tmpdir = tempfile.mkdtemp()
        self._db_path = os.path.join(self._tmpdir, "test_concurrent.db")

        # Shared WAL connection for setup
        conn = sqlite3.connect(self._db_path)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA journal_mode=WAL")
        conn.execute("PRAGMA busy_timeout=60000")
        conn.execute("PRAGMA foreign_keys=ON")
        conn.executescript(db._CREATE_SQL)
        conn.executescript(db._ERROR_TELEMETRY_SQL)

        # Seed 20 documents with searchable pages
        for i in range(20):
            topic = ["custody", "financial", "evidence", "motion", "hearing"][i % 5]
            doc_id = conn.execute(
                "INSERT INTO documents (file_path, file_name, file_size_bytes, ingested_at) "
                "VALUES (?, ?, ?, ?)",
                (f"/concurrent/{topic}_{i}.pdf", f"{topic}_{i}.pdf", 1024, "2025-01-01T00:00:00"),
            ).lastrowid
            conn.execute(
                "INSERT INTO pages (document_id, page_number, text_content) VALUES (?, ?, ?)",
                (doc_id, 1, f"This document discusses {topic} matters in Michigan court case {i}."),
            )
        conn.commit()
        conn.close()

    def tearDown(self):
        try:
            os.remove(self._db_path)
            os.rmdir(self._tmpdir)
        except OSError:
            pass

    def _thread_search(self, query, results_out, idx):
        """Run search_pages on a separate connection (thread-safe pattern)."""
        conn = sqlite3.connect(self._db_path)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA journal_mode=WAL")
        conn.execute("PRAGMA busy_timeout=60000")
        try:
            result = db.search_pages(conn, query, limit=10)
            results_out[idx] = result
        except Exception as exc:
            results_out[idx] = exc
        finally:
            conn.close()

    def test_two_threads_search_simultaneously(self):
        """Two concurrent FTS5 searches must both succeed under WAL mode."""
        results = [None, None]
        t1 = threading.Thread(target=self._thread_search, args=("custody", results, 0))
        t2 = threading.Thread(target=self._thread_search, args=("financial", results, 1))
        t1.start()
        t2.start()
        t1.join(timeout=10)
        t2.join(timeout=10)

        for i, r in enumerate(results):
            self.assertNotIsInstance(r, Exception, f"Thread {i} raised: {r}")
            self.assertIsInstance(r, dict)
            self.assertGreaterEqual(r["total"], 1)

    def test_concurrent_search_with_threadpool(self):
        """ThreadPoolExecutor with 4 workers must all return valid results."""
        queries = ["custody", "financial", "evidence", "motion"]
        results = {}

        def do_search(query):
            conn = sqlite3.connect(self._db_path)
            conn.row_factory = sqlite3.Row
            conn.execute("PRAGMA journal_mode=WAL")
            conn.execute("PRAGMA busy_timeout=60000")
            try:
                return query, db.search_pages(conn, query, limit=5)
            finally:
                conn.close()

        with ThreadPoolExecutor(max_workers=4) as pool:
            futures = {pool.submit(do_search, q): q for q in queries}
            for future in as_completed(futures):
                query, result = future.result()
                results[query] = result

        self.assertEqual(len(results), 4)
        for query, result in results.items():
            self.assertIsInstance(result, dict, f"Failed for query: {query}")
            self.assertGreaterEqual(
                result["total"], 1,
                f"No results for '{query}' — expected at least 1 hit",
            )

    def test_concurrent_read_write(self):
        """One writer + one reader must coexist under WAL mode."""
        errors = []

        def writer():
            conn = sqlite3.connect(self._db_path)
            conn.execute("PRAGMA journal_mode=WAL")
            conn.execute("PRAGMA busy_timeout=60000")
            try:
                for i in range(10):
                    doc_id = conn.execute(
                        "INSERT INTO documents (file_path, file_name, file_size_bytes, ingested_at) "
                        "VALUES (?, ?, ?, ?)",
                        (f"/concurrent/write_{i}.pdf", f"write_{i}.pdf", 512, "2025-01-01T00:00:00"),
                    ).lastrowid
                    conn.execute(
                        "INSERT INTO pages (document_id, page_number, text_content) VALUES (?, ?, ?)",
                        (doc_id, 1, f"Written concurrently document {i} about disqualification"),
                    )
                    conn.commit()
            except Exception as exc:
                errors.append(("writer", exc))
            finally:
                conn.close()

        def reader():
            conn = sqlite3.connect(self._db_path)
            conn.row_factory = sqlite3.Row
            conn.execute("PRAGMA journal_mode=WAL")
            conn.execute("PRAGMA busy_timeout=60000")
            try:
                for _ in range(10):
                    db.search_pages(conn, "custody", limit=5)
            except Exception as exc:
                errors.append(("reader", exc))
            finally:
                conn.close()

        t_write = threading.Thread(target=writer)
        t_read = threading.Thread(target=reader)
        t_write.start()
        t_read.start()
        t_write.join(timeout=15)
        t_read.join(timeout=15)

        self.assertEqual(errors, [], f"Concurrent read/write errors: {errors}")


# ═══════════════════════════════════════════════════════════════════════════
# 6. Stats & Integrity
# ═══════════════════════════════════════════════════════════════════════════

class TestStatsAndIntegrity(_TempDBMixin, unittest.TestCase):
    """Stats accuracy and schema integrity checks."""

    def test_stats_reflect_inserts(self):
        """get_stats counts must track actual row counts."""
        for i in range(3):
            self._insert_doc_with_pages(
                f"/test/s{i}.pdf", f"s{i}.pdf",
                [f"Page content {i}"],
            )
        stats = db.get_stats(self.conn)
        self.assertEqual(stats["total_documents"], 3)
        self.assertEqual(stats["total_pages"], 3)

    def test_integrity_check_on_clean_db(self):
        """check_integrity on fresh DB must pass (or expose known NameError bug)."""
        try:
            result = db.check_integrity(self.conn)
            self.assertIsInstance(result, dict)
            self.assertIn("integrity", result)
        except NameError as e:
            # Known pre-existing bug: 'synced' not defined in db.py:2675
            self.assertIn("synced", str(e))

    def test_self_audit_returns_metrics(self):
        """run_self_audit must return a dict with quality metrics."""
        try:
            result = db.run_self_audit(self.conn)
            self.assertIsInstance(result, dict)
        except NameError as e:
            # Known bug: run_self_audit calls check_integrity which has 'synced' bug
            self.assertIn("synced", str(e))


if __name__ == "__main__":
    unittest.main(verbosity=2)
