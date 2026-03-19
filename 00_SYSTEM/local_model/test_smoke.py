#!/usr/bin/env python
"""
Smoke-test suite for LitigationOS MLLM (39K-line codebase).

Validates that all engines initialise and return valid results using
only the Python standard library (unittest).

Run:  python test_smoke.py
"""

import functools
import os
import re
import signal
import sqlite3
import sys
import time
import unittest

# ── Ensure the local_model directory is on sys.path ──────────────────
_THIS_DIR = os.path.dirname(os.path.abspath(__file__))
if _THIS_DIR not in sys.path:
    sys.path.insert(0, _THIS_DIR)

DB_PATH = os.environ.get(
    "LITIGATION_DB_PATH",
    r"C:\Users\andre\LitigationOS\litigation_context.db",
)


# ── 30-second timeout decorator (cross-platform) ────────────────────
def timeout(seconds=30):
    """Fail the test if it exceeds *seconds* wall-clock time."""
    def decorator(fn):
        if sys.platform != "win32":
            # POSIX: use SIGALRM
            @functools.wraps(fn)
            def wrapper(*args, **kwargs):
                def _handler(signum, frame):
                    raise TimeoutError(f"{fn.__name__} exceeded {seconds}s timeout")
                old = signal.signal(signal.SIGALRM, _handler)
                signal.alarm(seconds)
                try:
                    return fn(*args, **kwargs)
                finally:
                    signal.alarm(0)
                    signal.signal(signal.SIGALRM, old)
            return wrapper
        else:
            # Windows: use a watchdog thread
            import threading
            @functools.wraps(fn)
            def wrapper(*args, **kwargs):
                result = [None]
                exc = [None]

                def target():
                    try:
                        result[0] = fn(*args, **kwargs)
                    except Exception as e:
                        exc[0] = e

                t = threading.Thread(target=target, daemon=True)
                t.start()
                t.join(timeout=seconds)
                if t.is_alive():
                    raise TimeoutError(f"{fn.__name__} exceeded {seconds}s timeout")
                if exc[0] is not None:
                    raise exc[0]
                return result[0]
            return wrapper
    return decorator


# ======================================================================
# 1. DB Connection
# ======================================================================
class TestDBConnection(unittest.TestCase):
    """Verify connection to litigation_context.db and key tables."""

    @timeout(30)
    def test_db_exists(self):
        self.assertTrue(os.path.isfile(DB_PATH), f"DB not found at {DB_PATH}")

    @timeout(30)
    def test_db_connects(self):
        conn = sqlite3.connect(DB_PATH)
        try:
            cur = conn.execute("SELECT 1")
            self.assertEqual(cur.fetchone()[0], 1)
        finally:
            conn.close()

    @timeout(30)
    def test_key_tables_exist(self):
        expected_tables = [
            "auth_rules", "evidence_quotes", "documents",
            "deadlines", "docket_events", "claims",
            "master_citations", "pages", "md_sections",
        ]
        conn = sqlite3.connect(DB_PATH)
        try:
            cur = conn.execute(
                "SELECT name FROM sqlite_master WHERE type='table'"
            )
            tables = {row[0] for row in cur.fetchall()}
            for tbl in expected_tables:
                with self.subTest(table=tbl):
                    self.assertIn(tbl, tables, f"Missing table: {tbl}")
        finally:
            conn.close()


# ======================================================================
# 2–5. Inference Engine core
# ======================================================================
class TestInferenceEngine(unittest.TestCase):
    """MichiganLegalModel init, status, query, cache, error logger."""

    _model = None

    @classmethod
    def setUpClass(cls):
        from inference_engine import MichiganLegalModel
        cls._model = MichiganLegalModel()

    # 2. Model initializes, status() returns expected shape
    @timeout(30)
    def test_model_initialised(self):
        self.assertIsNotNone(self._model)

    @timeout(30)
    def test_status_returns_dict(self):
        st = self._model.status()
        self.assertIsInstance(st, dict)
        self.assertIn("db_connected", st)
        self.assertTrue(st["db_connected"], "DB should be connected")

    @timeout(30)
    def test_status_has_expected_keys(self):
        st = self._model.status()
        for key in ("loaded", "model_name", "corpus_size", "cache_size"):
            with self.subTest(key=key):
                self.assertIn(key, st)

    # 3. Query pipeline
    @timeout(30)
    def test_query_parenting_time(self):
        result = self._model.query("parenting time")
        self.assertIsInstance(result, dict)
        self.assertIn("response", result, "query() must return dict with 'response' key")

    # 4. Engine cache identity
    @timeout(30)
    def test_get_engine_cache_identity(self):
        """_get_engine() returns the same object on second call."""
        from hybrid_retriever import HybridRetriever
        eng1 = self._model._get_engine("_smoke_test", HybridRetriever)
        eng2 = self._model._get_engine("_smoke_test", HybridRetriever)
        self.assertIs(eng1, eng2, "Cached engine must be the same object")


# ======================================================================
# 5. Error Logger
# ======================================================================
class TestErrorLogger(unittest.TestCase):
    """error_logger module functions don't crash."""

    @timeout(30)
    def test_log_exception(self):
        from error_logger import log_exception
        # Should not raise
        log_exception("smoke_test", "test_method", extra={"note": "smoke"})

    @timeout(30)
    def test_get_recent_errors(self):
        from error_logger import get_recent_errors
        errors = get_recent_errors(limit=5)
        self.assertIsInstance(errors, list)


# ======================================================================
# 6. EPOCH v5 — hybrid_search, bm25_search
# ======================================================================
class TestEpochV5(unittest.TestCase):
    """HybridRetriever.search and BM25Engine.search return results."""

    @timeout(30)
    def test_hybrid_search(self):
        from hybrid_retriever import HybridRetriever
        eng = HybridRetriever()
        hits = eng.search("parenting time", top_k=5)
        self.assertIsInstance(hits, list)

    @timeout(30)
    def test_bm25_search(self):
        from bm25_engine import BM25Engine
        eng = BM25Engine()
        hits = eng.search("parenting time", top_k=5)
        self.assertIsInstance(hits, list)


# ======================================================================
# 7. EPOCH v6 — impeachment, judicial violations, citation gaps
# ======================================================================
class TestEpochV6(unittest.TestCase):
    """EPOCH v6 engines return without crashing (results may be empty)."""

    _model = None

    @classmethod
    def setUpClass(cls):
        from inference_engine import MichiganLegalModel
        cls._model = MichiganLegalModel()

    @timeout(30)
    def test_impeachment_outline(self):
        from impeachment_generator import ImpeachmentGenerator
        ig = self._model._get_engine("impeachment", ImpeachmentGenerator, DB_PATH)
        result = ig.generate_cross_exam_outline("Tiffany Watson")
        self.assertIsInstance(result, (dict, list))

    @timeout(30)
    def test_judicial_violations(self):
        from judicial_violation_analyzer import JudicialViolationAnalyzer
        jva = self._model._get_engine(
            "judicial_violations", JudicialViolationAnalyzer, DB_PATH
        )
        result = jva.analyze_violation_patterns("Jenny L. McNeill")
        self.assertIsInstance(result, (dict, list))

    @timeout(30)
    def test_citation_gaps(self):
        from citation_gap_finder import CitationGapFinder
        cgf = self._model._get_engine("citation_gaps", CitationGapFinder, DB_PATH)
        # validate_citations on a short snippet keeps within 30s
        result = cgf.validate_citations(
            "The court must consider MCL 722.23(a) and MCR 2.003(C)."
        )
        self.assertIsInstance(result, (dict, list))


# ======================================================================
# 8. EPOCH v7 — memory_stats, scan_stats, system_status
# ======================================================================
class TestEpochV7(unittest.TestCase):
    """EPOCH v7 autonomous-layer engines return without crashing."""

    _model = None

    @classmethod
    def setUpClass(cls):
        from inference_engine import MichiganLegalModel
        cls._model = MichiganLegalModel()

    @timeout(30)
    def test_memory_stats(self):
        from persistent_memory import PersistentMemory
        pm = self._model._get_engine("memory", PersistentMemory, DB_PATH)
        result = pm.get_memory_stats()
        self.assertIsInstance(result, dict)

    @timeout(30)
    def test_scan_stats(self):
        from scan_ingester import ScanIngester
        si = self._model._get_engine(
            "scan_ingester", ScanIngester, DB_PATH, r"C:\Users\andre\scans"
        )
        result = si.get_ingestion_stats()
        self.assertIsInstance(result, dict)

    @timeout(30)
    def test_system_status(self):
        from orchestrator import Orchestrator
        orch = self._model._get_engine("orchestrator", Orchestrator, DB_PATH)
        result = orch.get_system_status()
        self.assertIsInstance(result, dict)


# ======================================================================
# 9. TUI Dashboard
# ======================================================================
class TestTUIDashboard(unittest.TestCase):
    """get_dashboard_data() returns dict with expected keys."""

    @timeout(30)
    def test_dashboard_data_keys(self):
        from tui_dashboard import get_dashboard_data
        data = get_dashboard_data()
        self.assertIsInstance(data, dict)
        expected_keys = [
            "system_health",
            "deadlines",
            "filing_readiness",
            "evidence_stats",
            "separation_days",
            "epoch_version",
        ]
        for key in expected_keys:
            with self.subTest(key=key):
                self.assertIn(key, data)


# ======================================================================
# 10. Citation Formats — regex patterns
# ======================================================================
class TestCitationFormats(unittest.TestCase):
    """Standard Michigan citation patterns are matched by regex."""

    MCR_PAT = re.compile(r"MCR\s+\d+\.\d+(?:\([A-Za-z0-9]+\))*")
    MCL_PAT = re.compile(r"MCL\s+\d+\.\d+[a-z]?(?:\([a-z0-9]+\))*", re.IGNORECASE)
    MRE_PAT = re.compile(r"MRE\s+\d+(?:\([a-z0-9]+\))*", re.IGNORECASE)
    CASE_PAT = re.compile(
        r"[A-Z][A-Za-z]+\s+v\s+[A-Z][A-Za-z]+,?\s+\d+\s+Mich(?:\s+App)?\s+\d+",
    )

    @timeout(30)
    def test_mcr_citation(self):
        self.assertIsNotNone(self.MCR_PAT.search("See MCR 2.003(C)(1)(b)"))
        self.assertIsNotNone(self.MCR_PAT.search("Per MCR 7.204(A)"))

    @timeout(30)
    def test_mcl_citation(self):
        self.assertIsNotNone(self.MCL_PAT.search("Under MCL 722.23(a)"))
        self.assertIsNotNone(self.MCL_PAT.search("MCL 600.2950"))

    @timeout(30)
    def test_mre_citation(self):
        self.assertIsNotNone(self.MRE_PAT.search("Governed by MRE 801(d)(2)"))
        self.assertIsNotNone(self.MRE_PAT.search("MRE 403"))

    @timeout(30)
    def test_case_citation(self):
        self.assertIsNotNone(
            self.CASE_PAT.search("Vodvarka v Grasher, 259 Mich App 499")
        )
        self.assertIsNotNone(
            self.CASE_PAT.search("Fletcher v Fletcher, 447 Mich 871")
        )

    @timeout(30)
    def test_no_false_positive(self):
        self.assertIsNone(self.MCR_PAT.search("The quick brown fox"))
        self.assertIsNone(self.MCL_PAT.search("Nothing legal here"))


# ======================================================================
# Runner with summary
# ======================================================================
class _SummaryResult(unittest.TextTestResult):
    """Track passed/failed/skipped counts for the final summary."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.passed = 0

    def addSuccess(self, test):
        super().addSuccess(test)
        self.passed += 1


def main():
    start = time.perf_counter()

    loader = unittest.TestLoader()
    suite = unittest.TestSuite()

    # Deterministic order: DB → Engine → ErrorLogger → v5 → v6 → v7 → TUI → Citations
    for cls in (
        TestDBConnection,
        TestInferenceEngine,
        TestErrorLogger,
        TestEpochV5,
        TestEpochV6,
        TestEpochV7,
        TestTUIDashboard,
        TestCitationFormats,
    ):
        suite.addTests(loader.loadTestsFromTestCase(cls))

    runner = unittest.TextTestRunner(
        verbosity=2,
        resultclass=_SummaryResult,
    )
    result = runner.run(suite)

    elapsed = time.perf_counter() - start
    passed = result.passed
    failed = len(result.failures) + len(result.errors)
    skipped = len(result.skipped)
    total = passed + failed + skipped

    print("\n" + "=" * 60)
    print(f"SMOKE TEST SUMMARY  ({elapsed:.1f}s)")
    print(f"  {passed} passed, {failed} failed, {skipped} skipped  (total {total})")
    print("=" * 60)

    sys.exit(0 if failed == 0 else 1)


if __name__ == "__main__":
    main()
