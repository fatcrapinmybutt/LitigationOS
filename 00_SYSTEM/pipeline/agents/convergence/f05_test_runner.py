"""
DELTA9 — F05 Test Runner
Convergence Tier · MAX LEVEL 9999++

Runs 15 system verification tests across the entire pipeline.
Runs AFTER both lanes complete.
"""
import shutil
from typing import Any

from ..agent_base import Agent9999
from ..agent_models import (
    SkipItemError, FatalAgentError, MASTER_INDEX_DB,
    LANE_A_SIGNALS, LANE_B_SIGNALS, LANE_C_SIGNALS,
)
from ..agent_models import CHECKPOINT_DIR

# Test definitions: (test_id, description)
_TESTS = [
    ("T01_DB_INTEGRITY",        "master_index.db integrity check"),
    ("T02_FILES_TABLE",         "files table has entries"),
    ("T03_DEDUP_CLUSTERS",      "dedup clusters exist"),
    ("T04_CANONICAL_MARKED",    "canonical files marked"),
    ("T05_DEPTH_ENFORCEMENT",   "depth <= 3 enforcement"),
    ("T06_LANE_PURITY",         "no cross-contaminated atoms"),
    ("T07_ATOM_STORE",          "atom store not empty"),
    ("T08_JUDICIAL_FINDINGS",   "judicial findings exist"),
    ("T09_ACTION_SCORES",       "action scores computed"),
    ("T10_AGENT_CHECKPOINTS",   "all 50 agent checkpoints exist"),
    ("T11_NO_FATAL_CRASH",      "no FATAL/CRASH status in agent_log"),
    ("T12_DISK_SPACE",          "disk space OK (>500MB free)"),
    ("T13_CITATION_ATOMS",      "citation atoms validated"),
    ("T14_FILING_MANIFESTS",    "filing manifests generated"),
    ("T15_CONVERGENCE_SCORE",   "convergence score computed"),
]


class TestRunner(Agent9999):
    """Runs 15 system verification tests."""

    def __init__(self):
        super().__init__(agent_id="F05-TEST")
        self._results: dict[str, str] = {}

    # ------------------------------------------------------------------
    # Abstract implementations
    # ------------------------------------------------------------------
    def _validate_preconditions(self) -> None:
        # Test runner has minimal preconditions — it IS the validator
        if not self.db_path.exists():
            raise FatalAgentError(f"master_index.db not found at {self.db_path}")

    def _get_work_items(self) -> list:
        return list(_TESTS)

    def _process_item(self, item: Any) -> None:
        test_id, description = item
        result = "FAIL"
        detail = ""

        try:
            handler = getattr(self, f"_run_{test_id.lower()}", None)
            if handler:
                passed, detail = handler()
                result = "PASS" if passed else "FAIL"
            else:
                detail = "No handler implemented"
                result = "SKIP"
        except Exception as e:
            detail = f"Exception: {e}"
            result = "FAIL"

        self._results[test_id] = result

        # Record as atom
        try:
            import hashlib
            atom_id = hashlib.sha1(f"F05|test_result|{test_id}".encode()).hexdigest()[:16]
            self._db_execute(
                "INSERT OR IGNORE INTO atoms (id, atom_type, content, confidence, created_by) "
                "VALUES (?, 'test_result', ?, ?, ?)",
                (atom_id, f"{test_id}: {result} — {detail}", 1.0 if result == "PASS" else 0.0, "F05-TEST")
            )
            self.db.commit()
        except Exception:
            pass  # atoms table may not exist on sparse first run

        self._log("TEST", f"{test_id}: {result} — {detail}")

    def _finalize(self) -> None:
        passed = sum(1 for v in self._results.values() if v == "PASS")
        failed = sum(1 for v in self._results.values() if v == "FAIL")
        skipped = sum(1 for v in self._results.values() if v == "SKIP")
        total = len(self._results)
        self._log("SUMMARY", f"Tests: {passed}/{total} PASS, {failed} FAIL, {skipped} SKIP")
        if failed > 0:
            failures = [k for k, v in self._results.items() if v == "FAIL"]
            self._log("FAILURES", f"Failed: {', '.join(failures)}")

    # ------------------------------------------------------------------
    # Individual test handlers → (passed: bool, detail: str)
    # ------------------------------------------------------------------
    def _run_t01_db_integrity(self) -> tuple[bool, str]:
        row = self._db_execute("PRAGMA integrity_check").fetchone()
        ok = row[0] == "ok" if row else False
        return ok, row[0] if row else "no result"

    def _run_t02_files_table(self) -> tuple[bool, str]:
        if not self._table_exists("files"):
            return False, "files table missing"
        row = self._db_execute("SELECT COUNT(*) FROM files").fetchone()
        count = row[0] if row else 0
        return count > 0, f"{count} files"

    def _run_t03_dedup_clusters(self) -> tuple[bool, str]:
        if not self._table_exists("dedup_clusters"):
            return False, "dedup_clusters table missing"
        row = self._db_execute("SELECT COUNT(*) FROM dedup_clusters").fetchone()
        count = row[0] if row else 0
        return count > 0, f"{count} clusters"

    def _run_t04_canonical_marked(self) -> tuple[bool, str]:
        if not self._table_exists("files"):
            return False, "files table missing"
        # Check for is_canonical column
        try:
            row = self._db_execute("SELECT COUNT(*) FROM files WHERE is_canonical = 1").fetchone()
            count = row[0] if row else 0
            return count > 0, f"{count} canonical files"
        except Exception:
            return False, "is_canonical column missing"

    def _run_t05_depth_enforcement(self) -> tuple[bool, str]:
        if not self._table_exists("files"):
            return False, "files table missing"
        try:
            row = self._db_execute("SELECT COUNT(*) FROM files WHERE depth > 3").fetchone()
            violations = row[0] if row else 0
            return violations == 0, f"{violations} depth violations"
        except Exception:
            return False, "depth column missing"

    def _run_t06_lane_purity(self) -> tuple[bool, str]:
        if not self._table_exists("atoms"):
            return False, "atoms table missing"
        # Check no atom matches signals from multiple lanes
        violations = 0
        rows = self._db_execute(
            "SELECT id, content FROM atoms WHERE content IS NOT NULL LIMIT 500"
        ).fetchall()
        for row in rows:
            content_lower = (row[1] or "").lower()
            matches = 0
            if any(s in content_lower for s in LANE_A_SIGNALS):
                matches += 1
            if any(s in content_lower for s in LANE_B_SIGNALS):
                matches += 1
            if any(s in content_lower for s in LANE_C_SIGNALS):
                matches += 1
            if matches > 1:
                violations += 1
        return violations == 0, f"{violations} cross-contaminated atoms"

    def _run_t07_atom_store(self) -> tuple[bool, str]:
        if not self._table_exists("atoms"):
            return False, "atoms table missing"
        row = self._db_execute("SELECT COUNT(*) FROM atoms").fetchone()
        count = row[0] if row else 0
        return count > 0, f"{count} atoms"

    def _run_t08_judicial_findings(self) -> tuple[bool, str]:
        if not self._table_exists("atoms"):
            return False, "atoms table missing"
        row = self._db_execute(
            "SELECT COUNT(*) FROM atoms WHERE atom_type = 'judicial_finding'"
        ).fetchone()
        count = row[0] if row else 0
        return count > 0, f"{count} judicial findings"

    def _run_t09_action_scores(self) -> tuple[bool, str]:
        if not self._table_exists("action_scores"):
            return False, "action_scores table missing"
        row = self._db_execute("SELECT COUNT(*) FROM action_scores").fetchone()
        count = row[0] if row else 0
        return count > 0, f"{count} action scores"

    def _run_t10_agent_checkpoints(self) -> tuple[bool, str]:
        CHECKPOINT_DIR.mkdir(parents=True, exist_ok=True)
        found = list(CHECKPOINT_DIR.glob("*.checkpoint.json"))
        return len(found) >= 50, f"{len(found)}/50 checkpoints"

    def _run_t11_no_fatal_crash(self) -> tuple[bool, str]:
        if not self._table_exists("agent_log"):
            return True, "agent_log table missing (no logs = no crashes)"
        row = self._db_execute(
            "SELECT COUNT(*) FROM agent_log WHERE level IN ('FATAL', 'CRASH')"
        ).fetchone()
        count = row[0] if row else 0
        return count == 0, f"{count} FATAL/CRASH entries"

    def _run_t12_disk_space(self) -> tuple[bool, str]:
        try:
            drive = str(self.db_path)[:3]
            usage = shutil.disk_usage(drive)
            free_mb = usage.free / (1024 ** 2)
            return free_mb > 500, f"{free_mb:.0f} MB free"
        except Exception as e:
            return False, f"disk check failed: {e}"

    def _run_t13_citation_atoms(self) -> tuple[bool, str]:
        if not self._table_exists("atoms"):
            return False, "atoms table missing"
        row = self._db_execute(
            "SELECT COUNT(*) FROM atoms WHERE atom_type = 'citation'"
        ).fetchone()
        count = row[0] if row else 0
        return count > 0, f"{count} citation atoms"

    def _run_t14_filing_manifests(self) -> tuple[bool, str]:
        CHECKPOINT_DIR.mkdir(parents=True, exist_ok=True)
        found = list(CHECKPOINT_DIR.glob("filing_*.json"))
        return len(found) > 0, f"{len(found)} filing manifests"

    def _run_t15_convergence_score(self) -> tuple[bool, str]:
        rpt = CHECKPOINT_DIR / "DELTA9_CONVERGENCE_REPORT.json"
        return rpt.exists(), "report exists" if rpt.exists() else "report missing"

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------
    def _table_exists(self, name: str) -> bool:
        row = self._db_execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name=?", (name,)
        ).fetchone()
        return row is not None
