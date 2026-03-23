"""Comprehensive test suite for the IRACEngine.

Tests cover instantiation, IRAC analysis, rule lookup, argument building,
strength evaluation, memo generation, edge cases, and helper functions.
"""

from __future__ import annotations

import sqlite3
import textwrap
from pathlib import Path

import pytest

from litigationos.engines.irac_engine import (
    CLAIM_TYPES,
    IRACEngine,
    PARTIES,
    _pick_column,
    _truncate,
)


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def tmp_db_path(tmp_path: Path) -> str:
    """Create a minimal SQLite database and return its path as a string."""
    db_path = tmp_path / "test_irac.db"
    conn = sqlite3.connect(str(db_path))
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute(
        "CREATE TABLE IF NOT EXISTS evidence_quotes ("
        "  id INTEGER PRIMARY KEY,"
        "  claim_type TEXT,"
        "  vehicle_name TEXT,"
        "  quote_text TEXT,"
        "  source_file TEXT"
        ")"
    )
    conn.execute(
        "CREATE TABLE IF NOT EXISTS michigan_court_rules ("
        "  id INTEGER PRIMARY KEY,"
        "  rule_id TEXT,"
        "  title TEXT,"
        "  text TEXT"
        ")"
    )
    conn.commit()
    conn.close()
    return str(db_path)


@pytest.fixture
def engine(tmp_db_path: str) -> IRACEngine:
    """Return an IRACEngine backed by the temporary database."""
    return IRACEngine(db_path=tmp_db_path)


@pytest.fixture
def seeded_engine(tmp_db_path: str) -> IRACEngine:
    """IRACEngine with evidence and rules pre-loaded in the temp DB."""
    conn = sqlite3.connect(tmp_db_path)
    conn.executemany(
        "INSERT INTO evidence_quotes (claim_type, vehicle_name, quote_text, source_file) "
        "VALUES (?, ?, ?, ?)",
        [
            ("custody modification", "A", "Mother denied parenting time on 5 occasions", "texts_jan2024.pdf"),
            ("custody modification", "A", "Child expressed desire to see father", "foc_report.pdf"),
            ("custody modification", "A", "School records show declining grades", "school_records.pdf"),
        ],
    )
    conn.executemany(
        "INSERT INTO michigan_court_rules (rule_id, title, text) VALUES (?, ?, ?)",
        [
            ("MCR 3.210", "Change of Custody", "A court may modify a custody order if proper cause or change of circumstances is established."),
            ("MCR 2.003", "Disqualification of Judge", "A judge is disqualified when the judge cannot impartially hear a case."),
            ("MCR 3.606", "Contempt", "A court may hold a party in contempt for wilful disobedience of a court order."),
        ],
    )
    conn.commit()
    conn.close()
    return IRACEngine(db_path=tmp_db_path)


# ===================================================================
# Basic Functionality (5 tests)
# ===================================================================

class TestBasicFunctionality:
    """Core instantiation and return-type contracts."""

    def test_irac_engine_instantiation(self, engine: IRACEngine):
        """Engine can be created with a temp DB path."""
        assert engine is not None
        assert engine._conn is not None

    def test_analyze_claim_returns_dict(self, engine: IRACEngine):
        """analyze_claim always returns a dict."""
        result = engine.analyze_claim("custody_modification", ["Fact one"])
        assert isinstance(result, dict)

    def test_analyze_claim_has_required_fields(self, engine: IRACEngine):
        """Result must contain all seven IRAC fields."""
        result = engine.analyze_claim("contempt", ["Order was violated"])
        required_keys = {
            "issue", "rule", "application", "conclusion",
            "strength_score", "authorities", "evidence_gaps",
        }
        assert required_keys.issubset(result.keys())

    def test_strength_score_range(self, engine: IRACEngine):
        """Strength score must be 0–10 inclusive."""
        for claim_type in CLAIM_TYPES:
            result = engine.analyze_claim(claim_type, ["Sample fact"])
            score = result["strength_score"]
            assert 0 <= score <= 10, f"{claim_type}: score {score} out of range"

    def test_all_claim_types_accepted(self, engine: IRACEngine):
        """Engine handles every registered claim type without error."""
        assert len(CLAIM_TYPES) == 14, "Expected 14 claim types"
        for claim_type in CLAIM_TYPES:
            result = engine.analyze_claim(claim_type, ["Generic fact"])
            assert "issue" in result
            assert "conclusion" in result


# ===================================================================
# Rule Lookup Integration (3 tests)
# ===================================================================

class TestRuleLookup:
    """Rule retrieval from DB and static fallback."""

    def test_get_applicable_rules_returns_list(self, engine: IRACEngine):
        """get_applicable_rules always returns a list."""
        rules = engine.get_applicable_rules("custody_modification")
        assert isinstance(rules, list)

    def test_rules_from_db_contain_expected_fields(self, seeded_engine: IRACEngine):
        """DB-sourced rules should have rule_id, title, text, source_table, relevance."""
        rules = seeded_engine.get_applicable_rules("custody_modification")
        assert len(rules) > 0, "Expected rules from seeded DB"
        for rule in rules:
            assert "rule_id" in rule
            assert "source_table" in rule
            assert "relevance" in rule

    def test_static_data_fallback(self, tmp_path: Path):
        """When DB has no matching rule tables, engine falls back to rule_lookup.py."""
        bare_db = tmp_path / "bare.db"
        conn = sqlite3.connect(str(bare_db))
        conn.execute("CREATE TABLE dummy (id INTEGER)")
        conn.commit()
        conn.close()

        engine = IRACEngine(db_path=str(bare_db))
        rules = engine.get_applicable_rules("custody_modification")
        # Static fallback from rule_lookup.py should still provide results
        assert isinstance(rules, list)


# ===================================================================
# Analysis Quality (4 tests)
# ===================================================================

class TestAnalysisQuality:
    """Content-level checks on generated IRAC output."""

    def test_custody_claim_cites_mcl_722(self, engine: IRACEngine):
        """Custody analysis must reference MCL 722.23 or MCL 722.27."""
        result = engine.analyze_claim(
            "custody_modification",
            ["Changed circumstances since original order"],
        )
        combined = result["issue"] + result["rule"]
        assert "MCL 722" in combined or "722.23" in combined or "722.27" in combined

    def test_due_process_claim_cites_constitution(self, engine: IRACEngine):
        """Due-process analysis must reference 14th Amendment or § 1983."""
        result = engine.analyze_claim(
            "due_process_violation",
            ["Court entered order without notice"],
        )
        combined = result["issue"] + result["rule"]
        assert "XIV" in combined or "1983" in combined or "14" in combined

    def test_analysis_includes_evidence_gaps(self, engine: IRACEngine):
        """When no DB evidence exists, evidence_gaps should be populated."""
        result = engine.analyze_claim("contempt", ["Order was violated"])
        assert isinstance(result["evidence_gaps"], list)
        assert len(result["evidence_gaps"]) > 0

    def test_seeded_evidence_reduces_gaps(self, seeded_engine: IRACEngine):
        """With evidence in the DB, fewer gaps should be reported."""
        result = seeded_engine.analyze_claim(
            "custody_modification",
            [
                "Proper cause established by denied parenting time",
                "Best interest factors weigh in favour of modification",
                "Established custodial environment analysis",
            ],
            lane="A",
        )
        gap_text = " ".join(result["evidence_gaps"])
        # Should NOT complain about missing evidence_quotes since we seeded them
        assert "No matching evidence in evidence_quotes" not in gap_text


# ===================================================================
# Edge Cases (4 tests)
# ===================================================================

class TestEdgeCases:
    """Boundary conditions and error handling."""

    def test_unknown_claim_type_handled(self, engine: IRACEngine):
        """Invalid claim type returns graceful result, not an exception."""
        result = engine.analyze_claim("totally_bogus_claim", ["fact"])
        assert result["strength_score"] == 0
        assert "Unknown claim type" in result["issue"]
        assert len(result["evidence_gaps"]) > 0

    def test_empty_evidence_still_analyzes(self, engine: IRACEngine):
        """analyze_claim with no facts should still return complete structure."""
        result = engine.analyze_claim("contempt", [])
        assert "issue" in result
        assert "rule" in result
        assert "application" in result
        assert "conclusion" in result

    def test_multiple_claims_independent(self, engine: IRACEngine):
        """Analysing different claims should not cross-contaminate results."""
        custody = engine.analyze_claim("custody_modification", ["Fact A"])
        contempt = engine.analyze_claim("contempt", ["Fact B"])

        assert "custody" in custody["issue"].lower() or "MCL 722" in custody["issue"]
        assert "contempt" in contempt["issue"].lower() or "MCR 3.606" in contempt["issue"]
        # Verify they are genuinely different
        assert custody["issue"] != contempt["issue"]

    def test_no_db_connection_graceful(self, tmp_path: Path):
        """Engine still works when pointed at a non-existent DB path."""
        engine = IRACEngine(db_path=str(tmp_path / "nonexistent.db"))
        # Connection auto-creates the file, but tables won't exist
        result = engine.analyze_claim("contempt", ["Order was violated"])
        assert isinstance(result, dict)
        assert "issue" in result


# ===================================================================
# Evaluate Strength (3 tests)
# ===================================================================

class TestEvaluateStrength:
    """Strength scoring heuristic tests."""

    def test_zero_evidence_zero_authority_weak(self, engine: IRACEngine):
        """Zero evidence + zero authority → WEAK rating."""
        result = engine.evaluate_strength("contempt", evidence_count=0, authority_count=0)
        assert result["score"] == 0
        assert result["rating"] == "WEAK"
        assert len(result["missing_elements"]) > 0

    def test_max_evidence_max_authority_strong(self, engine: IRACEngine):
        """5+ evidence + 5+ authority → STRONG rating (score 10)."""
        result = engine.evaluate_strength("contempt", evidence_count=10, authority_count=10)
        assert result["score"] == 10
        assert result["rating"] == "STRONG"

    def test_moderate_score_range(self, engine: IRACEngine):
        """Moderate input should yield MODERATE rating (score 4-6)."""
        result = engine.evaluate_strength("contempt", evidence_count=2, authority_count=2)
        assert 4 <= result["score"] <= 6
        assert result["rating"] == "MODERATE"


# ===================================================================
# Build Argument (3 tests)
# ===================================================================

class TestBuildArgument:
    """Tests for the build_argument() method."""

    def test_build_argument_returns_required_keys(self, engine: IRACEngine):
        """build_argument must return all five structural keys."""
        result = engine.build_argument("contempt", position="plaintiff", facts=["Order violated"])
        expected_keys = {
            "opening_statement", "legal_standard", "factual_basis",
            "authorities", "prayer_for_relief",
        }
        assert expected_keys.issubset(result.keys())

    def test_build_argument_uses_correct_party(self, engine: IRACEngine):
        """Opening statement should reference the correct party name."""
        result = engine.build_argument("contempt", position="plaintiff")
        assert PARTIES["plaintiff"] in result["opening_statement"]

    def test_build_argument_no_facts_flagged(self, engine: IRACEngine):
        """When no facts are supplied, factual_basis should flag the gap."""
        result = engine.build_argument("sanctions", position="plaintiff")
        assert "no factual basis" in result["factual_basis"].lower() or \
               "supply" in result["factual_basis"].lower()


# ===================================================================
# Generate IRAC Memo (2 tests)
# ===================================================================

class TestGenerateIRACMemo:
    """Tests for Markdown memorandum generation."""

    def test_memo_contains_irac_sections(self, engine: IRACEngine):
        """Generated memo must have all four IRAC section headers."""
        memo = engine.generate_irac_memo("contempt", ["Order violated"])
        assert "## I. ISSUE" in memo
        assert "## II. RULE" in memo
        assert "## III. APPLICATION" in memo
        assert "## IV. CONCLUSION" in memo

    def test_memo_header_has_parties(self, engine: IRACEngine):
        """Memo header must include plaintiff and defendant names."""
        memo = engine.generate_irac_memo("custody_modification", ["Changed circumstances"])
        assert PARTIES["plaintiff"] in memo
        assert PARTIES["defendant"] in memo


# ===================================================================
# get_claim_types (1 test)
# ===================================================================

class TestGetClaimTypes:
    """Tests for the get_claim_types() catalogue method."""

    def test_get_claim_types_returns_all(self, engine: IRACEngine):
        """Should return one entry per CLAIM_TYPES constant."""
        types = engine.get_claim_types()
        assert len(types) == len(CLAIM_TYPES)
        names = {t["claim_type"] for t in types}
        assert names == set(CLAIM_TYPES.keys())
        for entry in types:
            assert "description" in entry
            assert "required_elements" in entry
            assert "applicable_rules" in entry


# ===================================================================
# Module-Level Helpers (2 tests)
# ===================================================================

class TestHelpers:
    """Tests for _pick_column and _truncate helpers."""

    def test_pick_column_returns_first_match(self):
        """_pick_column returns the first preference found in available."""
        available = {"title", "name", "id"}
        assert _pick_column(available, ["rule_id", "title", "name"]) == "title"

    def test_pick_column_returns_none_when_no_match(self):
        """_pick_column returns None when nothing matches."""
        assert _pick_column({"a", "b"}, ["x", "y"]) is None

    def test_truncate_short_text(self):
        """Short text is returned unchanged."""
        assert _truncate("hello", 10) == "hello"

    def test_truncate_long_text(self):
        """Long text is truncated with an ellipsis."""
        result = _truncate("a" * 400, 300)
        assert len(result) == 300
        assert result.endswith("…")

    def test_truncate_none(self):
        """None input returns empty string."""
        assert _truncate(None) == ""
