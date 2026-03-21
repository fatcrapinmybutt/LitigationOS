"""
Tests for Agent9999 v3.0 OMEGA upgrades.

Covers: lane detection, anti-hallucination, evidence scoring, traceable statistics,
output validation, health reporting, batch operations, provenance chain, and all
v3.0 data classes (HealthReport, EvidenceScore, LaneDetection, FleetStatus,
ValidationResult, ProvenanceEntry).

All tests run offline with in-memory SQLite — no real DB or network required.
"""
from __future__ import annotations

import sqlite3
import sys
import time
from pathlib import Path
from unittest.mock import patch, MagicMock, PropertyMock

import pytest

# Add pipeline directory so we can import the agents package directly.
# Use a unique sys.path entry to avoid collisions with other 'agents' packages.
_PIPELINE_DIR = Path(__file__).resolve().parents[3] / "00_SYSTEM" / "pipeline"
_PIPELINE_STR = str(_PIPELINE_DIR)
if _PIPELINE_STR not in sys.path:
    sys.path.insert(0, _PIPELINE_STR)

# Import with explicit module reload to avoid stale cached packages
import importlib
_agent_models = importlib.import_module("agents.agent_models")
_agent_base = importlib.import_module("agents.agent_base")

AgentResult = _agent_models.AgentResult
AgentStats = _agent_models.AgentStats
QualityScore = _agent_models.QualityScore
PlanStep = _agent_models.PlanStep
AgentMessage = _agent_models.AgentMessage
HealthReport = _agent_models.HealthReport
ProvenanceEntry = _agent_models.ProvenanceEntry
EvidenceScore = _agent_models.EvidenceScore
LaneDetection = _agent_models.LaneDetection
FleetStatus = _agent_models.FleetStatus
ValidationResult = _agent_models.ValidationResult
LaneCrossContaminationError = _agent_models.LaneCrossContaminationError
SkipItemError = _agent_models.SkipItemError
FatalAgentError = _agent_models.FatalAgentError
RetryableError = _agent_models.RetryableError
LANE_A_SIGNALS = _agent_models.LANE_A_SIGNALS
LANE_B_SIGNALS = _agent_models.LANE_B_SIGNALS
LANE_C_SIGNALS = _agent_models.LANE_C_SIGNALS
LANE_D_SIGNALS = _agent_models.LANE_D_SIGNALS
LANE_E_SIGNALS = _agent_models.LANE_E_SIGNALS
LANE_F_SIGNALS = _agent_models.LANE_F_SIGNALS
Agent9999 = _agent_base.Agent9999


# ═══════════════════════════════════════════
# CONCRETE TEST AGENT SUBCLASS
# ═══════════════════════════════════════════

class ConcreteTestAgent(Agent9999):
    """Minimal concrete agent for testing v3.0 features."""

    def _get_work_items(self):
        return []

    def _process_item(self, item):
        pass

    def _ensure_tables(self):
        pass

    def _validate_preconditions(self):
        pass

    def _self_heal(self):
        pass


# ═══════════════════════════════════════════
# FIXTURES
# ═══════════════════════════════════════════

@pytest.fixture
def mem_db(tmp_path: Path) -> sqlite3.Connection:
    """In-memory SQLite connection with WAL pragmas and agent_log table."""
    db_path = tmp_path / "master_index.db"
    conn = sqlite3.connect(str(db_path), check_same_thread=False)
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA busy_timeout=60000")
    conn.row_factory = sqlite3.Row
    conn.execute("""
        CREATE TABLE IF NOT EXISTS agent_log (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            agent_id TEXT, level TEXT, action TEXT, detail TEXT,
            items_processed INTEGER DEFAULT 0,
            items_errored INTEGER DEFAULT 0,
            created_at TEXT DEFAULT (datetime('now'))
        )
    """)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS agent_checkpoints (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            agent_id TEXT NOT NULL,
            checkpoint_data TEXT NOT NULL,
            created_at TEXT DEFAULT (datetime('now'))
        )
    """)
    conn.commit()
    return conn


@pytest.fixture
def central_db() -> sqlite3.Connection:
    """In-memory connection simulating litigation_context.db."""
    conn = sqlite3.connect(":memory:", check_same_thread=False)
    conn.execute("PRAGMA journal_mode=WAL")
    conn.row_factory = sqlite3.Row
    return conn


@pytest.fixture
def agent(tmp_path: Path, mem_db: sqlite3.Connection, central_db: sqlite3.Connection):
    """A ConcreteTestAgent wired to in-memory databases."""
    db_path = tmp_path / "master_index.db"
    ag = ConcreteTestAgent(agent_id="TEST01", db_path=db_path)
    # Wire the pre-built master_index connection
    ag._main_db = mem_db
    # Wire the central DB mock so _get_central_db returns our in-memory conn
    ag._central_db = central_db
    return ag


# ═══════════════════════════════════════════
# LANE DETECTION
# ═══════════════════════════════════════════

class TestLaneDetection:
    """Tests for detect_lane() and require_lane()."""

    def test_detect_lane_custody(self, agent: ConcreteTestAgent):
        text = "The custody arrangement under MCL 722 best interest factors"
        assert agent.detect_lane(text) == "A"

    def test_detect_lane_housing(self, agent: ConcreteTestAgent):
        text = "Shady Oaks mobile home park habitability complaint MCL 554 landlord tenant"
        assert agent.detect_lane(text) == "B"

    def test_detect_lane_convergence(self, agent: ConcreteTestAgent):
        text = "42 USC 1983 1985 Monell civil rights Muskegon County 14th circuit"
        assert agent.detect_lane(text) == "C"

    def test_detect_lane_ppo(self, agent: ConcreteTestAgent):
        text = "personal protection order PPO bond violation stalking domestic violence threat intimidation"
        assert agent.detect_lane(text) == "D"

    def test_detect_lane_misconduct(self, agent: ConcreteTestAgent):
        text = "judicial misconduct JTC canon disqualification mcr 2.003 mcr 9.200 recusal pattern of bias"
        assert agent.detect_lane(text) == "E"

    def test_detect_lane_appellate(self, agent: ConcreteTestAgent):
        text = "appeal court of appeals COA MCR 7.201 brief on appeal standard of review de novo"
        assert agent.detect_lane(text) == "F"

    def test_detect_lane_unclassified(self, agent: ConcreteTestAgent):
        text = "The weather is nice today, here is a random sentence."
        assert agent.detect_lane(text) == "U"

    def test_detect_lane_empty(self, agent: ConcreteTestAgent):
        assert agent.detect_lane("") == "U"

    def test_detect_lane_none_like(self, agent: ConcreteTestAgent):
        """Empty/whitespace text should be unclassified."""
        assert agent.detect_lane("   ") == "U"

    def test_detect_lane_case_insensitive(self, agent: ConcreteTestAgent):
        text = "APPEAL COURT OF APPEALS COA MCR 7.201"
        assert agent.detect_lane(text) == "F"

    def test_require_lane_matching(self, agent: ConcreteTestAgent):
        text = "Shady Oaks mobile home park habitability MCL 554 landlord tenant"
        agent.require_lane(text, "B")  # Should not raise

    def test_require_lane_mismatch(self, agent: ConcreteTestAgent):
        text = "judicial misconduct JTC canon disqualification mcr 2.003 mcr 9.200 recusal pattern of bias"
        with pytest.raises(LaneCrossContaminationError, match="Lane contamination"):
            agent.require_lane(text, "B")

    def test_require_lane_unclassified_passes(self, agent: ConcreteTestAgent):
        """Unclassified text never triggers cross-contamination."""
        agent.require_lane("random generic text", "A")  # Should not raise

    def test_lane_cross_contamination_is_skip_item(self):
        """LaneCrossContaminationError inherits from SkipItemError (non-fatal)."""
        assert issubclass(LaneCrossContaminationError, SkipItemError)


# ═══════════════════════════════════════════
# ANTI-HALLUCINATION GUARD
# ═══════════════════════════════════════════

class TestAntiHallucination:
    """Tests for validate_party_name(), get_verified_party(), guard_output()."""

    def test_validate_party_name_correct_plaintiff(self, agent: ConcreteTestAgent):
        assert agent.validate_party_name("Andrew James Pigors") is True

    def test_validate_party_name_correct_defendant(self, agent: ConcreteTestAgent):
        assert agent.validate_party_name("Emily A. Watson") is True

    def test_validate_party_name_correct_judge(self, agent: ConcreteTestAgent):
        assert agent.validate_party_name("Hon. Jenny L. McNeill") is True

    def test_validate_party_name_hallucinated_jane(self, agent: ConcreteTestAgent):
        assert agent.validate_party_name("Jane Berry") is False

    def test_validate_party_name_hallucinated_patricia(self, agent: ConcreteTestAgent):
        assert agent.validate_party_name("Patricia Berry (SBN P35878)") is False

    def test_validate_party_name_wrong_emily(self, agent: ConcreteTestAgent):
        assert agent.validate_party_name("Emily Ann Watson") is False

    def test_validate_party_name_wrong_emily_m(self, agent: ConcreteTestAgent):
        assert agent.validate_party_name("Emily M. Watson") is False

    def test_validate_party_name_tiffany(self, agent: ConcreteTestAgent):
        assert agent.validate_party_name("Tiffany Watson") is False

    def test_validate_party_name_amy_mcneill(self, agent: ConcreteTestAgent):
        assert agent.validate_party_name("Amy McNeill") is False

    def test_validate_party_name_ronald_esq(self, agent: ConcreteTestAgent):
        """Ronald Berry is not an attorney — Esq. is a hallucination."""
        assert agent.validate_party_name("Ronald Berry, Esq") is False

    def test_get_verified_party_plaintiff(self, agent: ConcreteTestAgent):
        assert agent.get_verified_party("plaintiff") == "Andrew James Pigors"

    def test_get_verified_party_defendant(self, agent: ConcreteTestAgent):
        assert agent.get_verified_party("defendant") == "Emily A. Watson"

    def test_get_verified_party_child(self, agent: ConcreteTestAgent):
        assert agent.get_verified_party("child") == "L.D.W."

    def test_get_verified_party_judge(self, agent: ConcreteTestAgent):
        assert agent.get_verified_party("judge") == "Hon. Jenny L. McNeill"

    def test_get_verified_party_foc(self, agent: ConcreteTestAgent):
        assert agent.get_verified_party("foc") == "Pamela Rusco"

    def test_get_verified_party_unknown_role(self, agent: ConcreteTestAgent):
        assert agent.get_verified_party("witness") == "[UNKNOWN — VERIFY]"

    def test_get_verified_party_case_insensitive(self, agent: ConcreteTestAgent):
        assert agent.get_verified_party("PLAINTIFF") == "Andrew James Pigors"

    def test_guard_output_clean(self, agent: ConcreteTestAgent):
        text = "Andrew James Pigors filed a motion."
        assert agent.guard_output(text) == text

    def test_guard_output_replaces_jane_berry(self, agent: ConcreteTestAgent):
        text = "Jane Berry testified on Tuesday."
        result = agent.guard_output(text)
        assert "Jane Berry" not in result
        assert "[HALLUCINATION REMOVED]" in result

    def test_guard_output_replaces_patricia_berry(self, agent: ConcreteTestAgent):
        text = "Patricia Berry was the attorney."
        result = agent.guard_output(text)
        assert "Patricia Berry" not in result
        assert "[HALLUCINATION REMOVED]" in result

    def test_guard_output_corrects_amy_mcneill(self, agent: ConcreteTestAgent):
        text = "Judge Amy McNeill ruled against the motion."
        result = agent.guard_output(text)
        assert "Amy McNeill" not in result
        assert "Hon. Jenny L. McNeill" in result

    def test_guard_output_corrects_emily_ann(self, agent: ConcreteTestAgent):
        text = "Emily Ann Watson filed the response."
        result = agent.guard_output(text)
        assert "Emily Ann Watson" not in result
        assert "Emily A. Watson" in result

    def test_guard_output_corrects_emily_m(self, agent: ConcreteTestAgent):
        text = "Emily M. Watson is the defendant."
        result = agent.guard_output(text)
        assert "Emily M. Watson" not in result
        assert "Emily A. Watson" in result

    def test_guard_output_multiple_replacements(self, agent: ConcreteTestAgent):
        text = "Jane Berry and Amy McNeill discussed the case."
        result = agent.guard_output(text)
        assert "Jane Berry" not in result
        assert "Amy McNeill" not in result
        assert "[HALLUCINATION REMOVED]" in result
        assert "Hon. Jenny L. McNeill" in result


# ═══════════════════════════════════════════
# EVIDENCE SCORING
# ═══════════════════════════════════════════

class TestEvidenceScoring:
    """Tests for score_evidence()."""

    def test_score_court_order_high_admissibility(self, agent: ConcreteTestAgent):
        result = agent.score_evidence(
            "Court order regarding custody of the child",
            evidence_type="court_order",
        )
        assert result["admissibility"] == 1.0
        assert "MRE 902" in result["mre_rules"][0]

    def test_score_hearsay_low_weight(self, agent: ConcreteTestAgent):
        result = agent.score_evidence(
            "Someone told me that she said that he was there.",
            evidence_type="hearsay",
        )
        # base 0.2 * 0.5 hearsay penalty = 0.1
        assert result["admissibility"] == 0.1
        assert any("MRE 802" in r for r in result["mre_rules"])

    def test_score_relevant_text(self, agent: ConcreteTestAgent):
        """Text with many case-specific terms scores high relevance."""
        text = "custody parenting child MCL MCR court Watson Pigors"
        result = agent.score_evidence(text, evidence_type="unknown")
        # 8 hits / 5.0 = 1.6, capped at 1.0
        assert result["relevance"] == 1.0

    def test_score_irrelevant_text(self, agent: ConcreteTestAgent):
        text = "The quick brown fox jumped over the lazy dog."
        result = agent.score_evidence(text, evidence_type="unknown")
        assert result["relevance"] == 0.0

    def test_score_combined_formula(self, agent: ConcreteTestAgent):
        """combined_score = relevance * 0.6 + admissibility * 0.4."""
        text = "custody parenting child MCL MCR court"  # 6 hits → relevance 1.0
        result = agent.score_evidence(text, evidence_type="court_order")
        expected = round(1.0 * 0.6 + 1.0 * 0.4, 3)
        assert result["combined_score"] == expected

    def test_score_evidence_types_different_weights(self, agent: ConcreteTestAgent):
        """Different evidence types should have different admissibility."""
        court = agent.score_evidence("test", evidence_type="court_order")
        photo = agent.score_evidence("test", evidence_type="photograph")
        self_rep = agent.score_evidence("test", evidence_type="self_report")
        assert court["admissibility"] > photo["admissibility"] > self_rep["admissibility"]

    def test_score_unknown_type_default(self, agent: ConcreteTestAgent):
        result = agent.score_evidence("test", evidence_type="unknown")
        assert result["admissibility"] == 0.5

    def test_score_communication_mre_rule(self, agent: ConcreteTestAgent):
        result = agent.score_evidence("email exchange", evidence_type="communication")
        assert any("MRE 901(b)(4)" in r for r in result["mre_rules"])

    def test_score_sworn_testimony_mre_rule(self, agent: ConcreteTestAgent):
        result = agent.score_evidence("deposition", evidence_type="sworn_testimony")
        assert any("MRE 901(b)(1)" in r for r in result["mre_rules"])

    def test_score_claim_type_passthrough(self, agent: ConcreteTestAgent):
        result = agent.score_evidence("test", claim_type="custody")
        assert result["claim_type"] == "custody"

    def test_score_agent_id_included(self, agent: ConcreteTestAgent):
        result = agent.score_evidence("test")
        assert result["agent_id"] == "TEST01"

    def test_score_empty_text(self, agent: ConcreteTestAgent):
        result = agent.score_evidence("", evidence_type="court_order")
        assert result["relevance"] == 0.0
        assert result["admissibility"] == 1.0

    def test_score_hearsay_keywords_penalize(self, agent: ConcreteTestAgent):
        """Text containing 'told me' triggers hearsay penalty regardless of type."""
        result = agent.score_evidence(
            "She told me about custody",
            evidence_type="witness_statement",
        )
        # base 0.6 * 0.5 = 0.3
        assert result["admissibility"] == 0.3
        assert any("MRE 802" in r for r in result["mre_rules"])


# ═══════════════════════════════════════════
# TRACEABLE STATISTICS
# ═══════════════════════════════════════════

class TestTraceableStatistics:
    """Tests for traceable_count() and traceable_aggregate()."""

    def test_traceable_count_returns_provenance(self, agent: ConcreteTestAgent, mem_db):
        mem_db.execute("CREATE TABLE test_items (id INTEGER, name TEXT)")
        mem_db.executemany(
            "INSERT INTO test_items VALUES (?, ?)",
            [(1, "a"), (2, "b"), (3, "c")],
        )
        mem_db.commit()

        result = agent.traceable_count("test_items")
        assert result["count"] == 3
        assert result["table"] == "test_items"
        assert "query" in result
        assert result["agent_id"] == "TEST01"
        assert "ts" in result

    def test_traceable_count_with_where(self, agent: ConcreteTestAgent, mem_db):
        mem_db.execute("CREATE TABLE scored (id INTEGER, score INTEGER)")
        mem_db.executemany(
            "INSERT INTO scored VALUES (?, ?)",
            [(1, 80), (2, 90), (3, 50)],
        )
        mem_db.commit()

        result = agent.traceable_count("scored", "score > ?", (70,))
        assert result["count"] == 2
        assert "WHERE" in result["query"]

    def test_traceable_count_no_db(self, tmp_path: Path):
        """Handles missing DB gracefully with error key."""
        ag = ConcreteTestAgent(agent_id="TEST_NO_DB", db_path=tmp_path / "nonexistent.db")
        # No DB connected — _main_db is None, so _db_execute will raise
        result = ag.traceable_count("some_table")
        assert result["count"] == 0
        assert "error" in result

    def test_traceable_aggregate(self, agent: ConcreteTestAgent, mem_db):
        mem_db.execute("CREATE TABLE alpha (id INTEGER)")
        mem_db.execute("CREATE TABLE beta (id INTEGER, status TEXT)")
        mem_db.executemany("INSERT INTO alpha VALUES (?)", [(1,), (2,)])
        mem_db.executemany(
            "INSERT INTO beta VALUES (?, ?)",
            [(1, "active"), (2, "inactive"), (3, "active")],
        )
        mem_db.commit()

        queries = {
            "total_alpha": ("alpha",),
            "active_beta": ("beta", "status = ?", ("active",)),
        }
        results = agent.traceable_aggregate(queries)
        assert results["total_alpha"]["count"] == 2
        assert results["active_beta"]["count"] == 2

    def test_traceable_count_empty_table(self, agent: ConcreteTestAgent, mem_db):
        mem_db.execute("CREATE TABLE empty_tbl (id INTEGER)")
        mem_db.commit()
        result = agent.traceable_count("empty_tbl")
        assert result["count"] == 0


# ═══════════════════════════════════════════
# OUTPUT VALIDATION
# ═══════════════════════════════════════════

class TestOutputValidation:
    """Tests for validate_output()."""

    def test_validate_output_clean(self, agent: ConcreteTestAgent):
        output = {"name": "Andrew James Pigors", "status": "active"}
        result = agent.validate_output(output)
        assert result["passed"] is True
        assert result["issues"] == []

    def test_validate_output_hallucinated_name(self, agent: ConcreteTestAgent):
        output = {"attorney": "Jane Berry represented the plaintiff."}
        result = agent.validate_output(output)
        assert result["passed"] is False
        assert len(result["issues"]) >= 1
        assert result["issues"][0]["type"] == "hallucination"

    def test_validate_output_nested_dict(self, agent: ConcreteTestAgent):
        output = {
            "case": {
                "parties": {
                    "judge": "Judge Amy McNeill presided."
                }
            }
        }
        result = agent.validate_output(output)
        assert result["passed"] is False
        assert ".case.parties.judge" in result["issues"][0]["path"]

    def test_validate_output_list_values(self, agent: ConcreteTestAgent):
        output = {"names": ["Andrew Pigors", "Patricia Berry"]}
        result = agent.validate_output(output)
        assert result["passed"] is False
        assert "[1]" in result["issues"][0]["path"]

    def test_validate_output_multiple_hallucinations(self, agent: ConcreteTestAgent):
        output = {
            "a": "Jane Berry filed it",
            "b": "Emily Ann Watson responded",
        }
        result = agent.validate_output(output)
        assert result["passed"] is False
        assert len(result["issues"]) >= 2

    def test_validate_output_has_checked_at(self, agent: ConcreteTestAgent):
        result = agent.validate_output({"x": "clean"})
        assert "checked_at" in result
        assert isinstance(result["checked_at"], float)


# ═══════════════════════════════════════════
# HEALTH REPORT
# ═══════════════════════════════════════════

class TestHealthReport:
    """Tests for health_report() method and HealthReport dataclass."""

    def test_health_report_healthy(self, agent: ConcreteTestAgent):
        agent.stats.total = 100
        agent.stats.processed = 95
        agent.stats.errored = 2
        agent.stats.skipped = 3
        report = agent.health_report()
        assert report["status"] == "healthy"

    def test_health_report_degraded(self, agent: ConcreteTestAgent):
        agent.stats.total = 100
        agent.stats.processed = 5
        agent.stats.errored = 90
        agent.stats.skipped = 5
        report = agent.health_report()
        assert report["status"] == "degraded"

    def test_health_report_structure(self, agent: ConcreteTestAgent):
        report = agent.health_report()
        assert "agent_id" in report
        assert "status" in report
        assert "stats" in report
        assert "quality" in report
        assert "profile" in report
        assert "findings_count" in report
        assert "messages_sent" in report
        assert "messages_received" in report
        assert "known_error_patterns" in report
        assert "quality_trend" in report
        assert "ts" in report

    def test_health_report_stats_fields(self, agent: ConcreteTestAgent):
        agent.stats.total = 50
        agent.stats.processed = 40
        agent.stats.errored = 5
        agent.stats.skipped = 5
        report = agent.health_report()
        stats = report["stats"]
        assert stats["total"] == 50
        assert stats["processed"] == 40
        assert stats["errored"] == 5
        assert stats["skipped"] == 5
        assert 0 <= stats["error_rate"] <= 1
        assert 0 <= stats["success_rate"] <= 1

    def test_health_report_quality(self, agent: ConcreteTestAgent):
        agent.stats.total = 10
        agent.stats.processed = 10
        report = agent.health_report()
        q = report["quality"]
        assert "overall" in q
        assert "completeness" in q
        assert "accuracy" in q
        assert "throughput" in q
        assert "coverage" in q

    def test_health_report_profile_keys(self, agent: ConcreteTestAgent):
        report = agent.health_report()
        profile = report["profile"]
        assert "setup_time" in profile
        assert "process_time" in profile
        assert "total_time" in profile
        assert "items_per_sec" in profile

    def test_health_report_agent_id(self, agent: ConcreteTestAgent):
        report = agent.health_report()
        assert report["agent_id"] == "TEST01"


# ═══════════════════════════════════════════
# BATCH OPERATIONS
# ═══════════════════════════════════════════

class TestBatchOperations:
    """Tests for batch_insert() and batch_upsert()."""

    def test_batch_insert(self, agent: ConcreteTestAgent, mem_db):
        mem_db.execute("CREATE TABLE items (id INTEGER PRIMARY KEY, name TEXT)")
        mem_db.commit()

        rows = [(1, "alpha"), (2, "beta"), (3, "gamma")]
        count = agent.batch_insert("items", ["id", "name"], rows)
        assert count == 3

        actual = mem_db.execute("SELECT COUNT(*) FROM items").fetchone()[0]
        assert actual == 3

    def test_batch_insert_empty(self, agent: ConcreteTestAgent):
        count = agent.batch_insert("any_table", ["id"], [])
        assert count == 0

    def test_batch_insert_or_ignore(self, agent: ConcreteTestAgent, mem_db):
        mem_db.execute("CREATE TABLE uniq (id INTEGER PRIMARY KEY, val TEXT)")
        mem_db.execute("INSERT INTO uniq VALUES (1, 'original')")
        mem_db.commit()

        rows = [(1, "duplicate"), (2, "new")]
        count = agent.batch_insert("uniq", ["id", "val"], rows, or_ignore=True)
        assert count == 2  # returns len(rows), not actual inserts

        original = mem_db.execute("SELECT val FROM uniq WHERE id = 1").fetchone()[0]
        assert original == "original"  # OR IGNORE preserved original

    def test_batch_upsert(self, agent: ConcreteTestAgent, mem_db):
        mem_db.execute("CREATE TABLE docs (id INTEGER PRIMARY KEY, content TEXT)")
        mem_db.execute("INSERT INTO docs VALUES (1, 'old')")
        mem_db.commit()

        rows = [(1, "updated"), (2, "new")]
        count = agent.batch_upsert("docs", ["id", "content"], rows)
        assert count == 2

        row1 = mem_db.execute("SELECT content FROM docs WHERE id = 1").fetchone()[0]
        assert row1 == "updated"  # REPLACE overwrites

        total = mem_db.execute("SELECT COUNT(*) FROM docs").fetchone()[0]
        assert total == 2

    def test_batch_upsert_empty(self, agent: ConcreteTestAgent):
        count = agent.batch_upsert("any_table", ["id"], [])
        assert count == 0

    def test_batch_insert_bad_table(self, agent: ConcreteTestAgent):
        """Insert into nonexistent table returns 0 (error handled gracefully)."""
        count = agent.batch_insert("nonexistent_table", ["id"], [(1,)])
        assert count == 0


# ═══════════════════════════════════════════
# PROVENANCE CHAIN
# ═══════════════════════════════════════════

class TestProvenanceChain:
    """Tests for _provenance_entry()."""

    def test_provenance_entry_structure(self, agent: ConcreteTestAgent):
        inputs = [{"type": "document", "id": "DOC-001", "source": "drive_f"}]
        entry = agent._provenance_entry("filing", "FIL-001", inputs)
        assert entry["agent_id"] == "TEST01"
        assert entry["output_type"] == "filing"
        assert entry["output_id"] == "FIL-001"
        assert entry["inputs"] == inputs
        assert "ts" in entry

    def test_provenance_written_to_central_db(self, agent: ConcreteTestAgent, central_db):
        inputs = [{"type": "evidence", "id": "EV-001"}]
        agent._provenance_entry("analysis", "AN-001", inputs)

        row = central_db.execute(
            "SELECT * FROM provenance_chain WHERE output_id = 'AN-001'"
        ).fetchone()
        assert row is not None
        assert row["agent_id"] == "TEST01"
        assert row["output_type"] == "analysis"

    def test_provenance_no_central_db(self, tmp_path: Path):
        """Provenance entry still returns dict even without central DB."""
        ag = ConcreteTestAgent(agent_id="TEST_NO_CENTRAL", db_path=tmp_path / "idx.db")
        ag._central_db = None
        entry = ag._provenance_entry("score", "SC-001", [])
        assert entry["output_type"] == "score"


# ═══════════════════════════════════════════
# DATA CLASSES v3.0
# ═══════════════════════════════════════════

class TestHealthReportDataclass:
    """Tests for HealthReport dataclass."""

    def test_health_score_healthy(self):
        hr = HealthReport(agent_id="A01", status="healthy", items_processed=100,
                          error_count=2, db_connected=True)
        assert 0.8 < hr.health_score <= 1.0

    def test_health_score_dead(self):
        hr = HealthReport(agent_id="A01", status="dead")
        assert hr.health_score == 0.0

    def test_health_score_degraded(self):
        hr = HealthReport(agent_id="A01", status="degraded",
                          items_processed=50, error_count=10, db_connected=True)
        # base 0.7 - error_penalty - db_penalty
        assert 0.0 < hr.health_score < 0.8

    def test_health_score_db_penalty(self):
        with_db = HealthReport(agent_id="A01", status="healthy",
                               items_processed=10, db_connected=True)
        without_db = HealthReport(agent_id="A01", status="healthy",
                                  items_processed=10, db_connected=False)
        assert with_db.health_score > without_db.health_score

    def test_health_score_no_items(self):
        hr = HealthReport(agent_id="A01", status="healthy", db_connected=True)
        # 0 items processed, 0 errors → error_penalty = 0
        assert hr.health_score == 1.0

    def test_str_representation(self):
        hr = HealthReport(agent_id="A01", status="healthy", items_processed=42)
        s = str(hr)
        assert "A01" in s
        assert "healthy" in s


class TestEvidenceScoreDataclass:
    """Tests for EvidenceScore dataclass."""

    def test_composite_high_admissibility(self):
        es = EvidenceScore(relevance=0.8, admissibility=0.9, impact=0.7)
        expected = 0.8 * 0.35 + 0.9 * 0.35 + 0.7 * 0.30
        assert abs(es.composite - expected) < 0.001

    def test_composite_low_admissibility_gate(self):
        """When admissibility < 0.3, composite is heavily penalized."""
        es = EvidenceScore(relevance=1.0, admissibility=0.2, impact=1.0)
        assert es.composite == 0.2 * 0.5  # 0.1

    def test_composite_boundary_at_030(self):
        """At exactly 0.3 admissibility, use the normal formula."""
        es = EvidenceScore(relevance=0.5, admissibility=0.3, impact=0.5)
        expected = 0.5 * 0.35 + 0.3 * 0.35 + 0.5 * 0.30
        assert abs(es.composite - expected) < 0.001

    def test_str_representation(self):
        es = EvidenceScore(relevance=0.8, admissibility=0.9, impact=0.7,
                           evidence_type="photo", claim_type="custody")
        s = str(es)
        assert "photo" in s
        assert "custody" in s

    def test_default_values(self):
        es = EvidenceScore()
        assert es.relevance == 0.0
        assert es.admissibility == 0.0
        assert es.impact == 0.0
        assert es.mre_issues == []


class TestLaneDetectionDataclass:
    """Tests for LaneDetection dataclass."""

    def test_is_confident_above_threshold(self):
        ld = LaneDetection(lane="A", confidence=0.8)
        assert ld.is_confident is True

    def test_is_confident_at_threshold(self):
        ld = LaneDetection(lane="B", confidence=0.6)
        assert ld.is_confident is True

    def test_is_not_confident_below_threshold(self):
        ld = LaneDetection(lane="U", confidence=0.5)
        assert ld.is_confident is False

    def test_default_lane(self):
        ld = LaneDetection()
        assert ld.lane == "U"
        assert ld.confidence == 0.0
        assert ld.is_confident is False


class TestFleetStatusDataclass:
    """Tests for FleetStatus dataclass."""

    def test_fleet_health_with_reports(self):
        reports = [
            HealthReport(agent_id="A01", status="healthy",
                         items_processed=100, db_connected=True),
            HealthReport(agent_id="A02", status="degraded",
                         items_processed=50, error_count=20, db_connected=True),
        ]
        fs = FleetStatus(total_agents=2, healthy=1, degraded=1, reports=reports)
        assert 0.0 < fs.fleet_health < 1.0

    def test_fleet_health_no_agents(self):
        fs = FleetStatus(total_agents=0)
        assert fs.fleet_health == 0.0

    def test_fleet_health_all_healthy(self):
        reports = [
            HealthReport(agent_id=f"A{i:02d}", status="healthy",
                         items_processed=100, db_connected=True)
            for i in range(3)
        ]
        fs = FleetStatus(total_agents=3, healthy=3, reports=reports)
        assert fs.fleet_health > 0.9

    def test_fleet_health_all_dead(self):
        reports = [
            HealthReport(agent_id="A01", status="dead"),
            HealthReport(agent_id="A02", status="dead"),
        ]
        fs = FleetStatus(total_agents=2, dead=2, reports=reports)
        assert fs.fleet_health == 0.0


class TestValidationResultDataclass:
    """Tests for ValidationResult dataclass."""

    def test_valid_default(self):
        vr = ValidationResult()
        assert vr.is_valid is True
        assert vr.issues == []
        assert vr.corrections_made == 0
        assert vr.hallucinations_caught == 0

    def test_invalid_with_issues(self):
        vr = ValidationResult(
            is_valid=False,
            issues=["Jane Berry detected", "Amy McNeill detected"],
            hallucinations_caught=2,
            corrections_made=2,
            original_text="Jane Berry and Amy McNeill",
            corrected_text="[REMOVED] and Hon. Jenny L. McNeill",
        )
        assert not vr.is_valid
        assert len(vr.issues) == 2
        assert vr.hallucinations_caught == 2

    def test_str_valid(self):
        vr = ValidationResult()
        assert "VALID" in str(vr)

    def test_str_invalid(self):
        vr = ValidationResult(is_valid=False, issues=["bad"])
        assert "INVALID" in str(vr)


class TestProvenanceEntryDataclass:
    """Tests for ProvenanceEntry dataclass."""

    def test_creation(self):
        pe = ProvenanceEntry(
            output_type="filing",
            output_id="FIL-001",
            inputs=[{"type": "doc", "id": "D1"}],
            agent_id="J01",
        )
        assert pe.output_type == "filing"
        assert pe.output_id == "FIL-001"
        assert len(pe.inputs) == 1
        assert pe.agent_id == "J01"
        assert pe.timestamp > 0

    def test_default_values(self):
        pe = ProvenanceEntry(output_type="score", output_id="S1")
        assert pe.inputs == []
        assert pe.agent_id == ""

    def test_str_representation(self):
        pe = ProvenanceEntry(output_type="analysis", output_id="AN-01",
                             inputs=[{"type": "a"}, {"type": "b"}])
        s = str(pe)
        assert "analysis" in s
        assert "2 inputs" in s


# ═══════════════════════════════════════════
# AGENT STATS & AGENT RESULT
# ═══════════════════════════════════════════

class TestAgentStatsProperties:
    """Tests for AgentStats computed properties."""

    def test_error_rate_zero(self):
        s = AgentStats(processed=10, errored=0)
        assert s.error_rate == 0.0

    def test_error_rate_calculation(self):
        s = AgentStats(processed=8, errored=2)
        assert s.error_rate == pytest.approx(0.2)

    def test_success_rate_calculation(self):
        s = AgentStats(processed=8, errored=2)
        assert s.success_rate == pytest.approx(0.8)

    def test_rate_items_per_sec(self):
        s = AgentStats(processed=100)
        # elapsed is time.time() - start_time; just verify it's positive
        assert s.rate > 0

    def test_elapsed_positive(self):
        s = AgentStats()
        assert s.elapsed >= 0


class TestAgentResult:
    """Tests for AgentResult dataclass."""

    def test_basic_creation(self):
        stats = AgentStats(total=10, processed=10)
        result = AgentResult(agent_id="TEST01", status="SUCCESS", stats=stats)
        assert result.agent_id == "TEST01"
        assert result.status == "SUCCESS"
        assert result.error is None

    def test_str_representation(self):
        stats = AgentStats(total=10, processed=10)
        result = AgentResult(agent_id="T01", status="FATAL", stats=stats,
                             error="DB connection lost")
        s = str(result)
        assert "T01" in s
        assert "FATAL" in s


# ═══════════════════════════════════════════
# EXCEPTION TYPES
# ═══════════════════════════════════════════

class TestExceptionTypes:
    """Tests for v3.0 exception hierarchy."""

    def test_lane_contamination_is_skip_item(self):
        err = LaneCrossContaminationError("wrong lane")
        assert isinstance(err, SkipItemError)

    def test_retryable_error_defaults(self):
        err = RetryableError("temporary failure")
        assert err.suggested_wait == 2.0
        assert err.max_retries == 3

    def test_retryable_error_custom(self):
        err = RetryableError("slow", suggested_wait=5.0, max_retries=10)
        assert err.suggested_wait == 5.0
        assert err.max_retries == 10

    def test_fatal_agent_error(self):
        err = FatalAgentError("unrecoverable")
        assert str(err) == "unrecoverable"


# ═══════════════════════════════════════════
# QUALITY SCORE
# ═══════════════════════════════════════════

class TestQualityScore:
    """Tests for QualityScore dataclass and its overall property."""

    def test_overall_weighted(self):
        q = QualityScore(completeness=1.0, accuracy=1.0, throughput=1.0, coverage=1.0)
        assert q.overall == pytest.approx(1.0)

    def test_overall_zero(self):
        q = QualityScore()
        assert q.overall == 0.0

    def test_overall_partial(self):
        q = QualityScore(completeness=0.5, accuracy=0.5, throughput=0.5, coverage=0.5)
        assert q.overall == pytest.approx(0.5)

    def test_str_representation(self):
        q = QualityScore(completeness=0.9, accuracy=0.8, throughput=0.7, coverage=0.6)
        s = str(q)
        assert "Q=" in s
        assert "comp=" in s


# ═══════════════════════════════════════════
# LANE SIGNAL SETS (IMMUTABILITY)
# ═══════════════════════════════════════════

class TestLaneSignalSets:
    """Verify the lane signal constant sets contain expected values."""

    def test_lane_a_has_custody(self):
        assert "custody" in LANE_A_SIGNALS
        assert "parenting" in LANE_A_SIGNALS

    def test_lane_b_has_housing(self):
        assert "shady oaks" in LANE_B_SIGNALS
        assert "habitability" in LANE_B_SIGNALS

    def test_lane_d_has_ppo(self):
        assert "ppo" in LANE_D_SIGNALS
        assert "protection order" in LANE_D_SIGNALS

    def test_lane_e_has_misconduct(self):
        assert "judicial misconduct" in LANE_E_SIGNALS
        assert "jtc" in LANE_E_SIGNALS

    def test_lane_f_has_appeal(self):
        assert "appeal" in LANE_F_SIGNALS
        assert "court of appeals" in LANE_F_SIGNALS

    def test_lanes_are_sets(self):
        for signals in [LANE_A_SIGNALS, LANE_B_SIGNALS, LANE_C_SIGNALS,
                        LANE_D_SIGNALS, LANE_E_SIGNALS, LANE_F_SIGNALS]:
            assert isinstance(signals, set)
