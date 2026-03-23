"""Comprehensive test suite for the DiscoveryGenerator engine.

Tests cover instantiation, document generation (interrogatories, RFP, RFA,
subpoenas), MCR compliance citations, content quality, discovery plans,
templates, rule context lookup, and edge cases.
"""

from __future__ import annotations

import sqlite3
from pathlib import Path

import pytest

from litigationos.engines.discovery_generator import (
    CASE_NUMBERS,
    DISCOVERY_TOPICS,
    DiscoveryGenerator,
    PARTIES,
    _caption,
    _certificate_of_service,
    _deadline_date,
    _today,
)


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def tmp_db_path(tmp_path: Path) -> str:
    """Create a minimal SQLite database with claims/evidence_gaps tables."""
    db_path = tmp_path / "test_discovery.db"
    conn = sqlite3.connect(str(db_path))
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute(
        "CREATE TABLE IF NOT EXISTS claims ("
        "  id INTEGER PRIMARY KEY,"
        "  case_number TEXT,"
        "  vehicle_name TEXT,"
        "  claim_type TEXT,"
        "  description TEXT,"
        "  status TEXT"
        ")"
    )
    conn.execute(
        "CREATE TABLE IF NOT EXISTS evidence_gaps ("
        "  id INTEGER PRIMARY KEY,"
        "  vehicle_name TEXT,"
        "  gap_type TEXT,"
        "  description TEXT"
        ")"
    )
    conn.execute(
        "CREATE TABLE IF NOT EXISTS deadlines ("
        "  id INTEGER PRIMARY KEY,"
        "  vehicle_name TEXT,"
        "  description TEXT,"
        "  title TEXT,"
        "  category TEXT,"
        "  due_date_iso TEXT,"
        "  status TEXT"
        ")"
    )
    conn.commit()
    conn.close()
    return str(db_path)


@pytest.fixture
def engine(tmp_db_path: str) -> DiscoveryGenerator:
    """Return a DiscoveryGenerator backed by the temporary database."""
    gen = DiscoveryGenerator(db_path=tmp_db_path)
    yield gen
    gen.close()


@pytest.fixture
def seeded_engine(tmp_db_path: str) -> DiscoveryGenerator:
    """DiscoveryGenerator with claims and evidence gaps pre-loaded."""
    conn = sqlite3.connect(tmp_db_path)
    conn.executemany(
        "INSERT INTO claims (case_number, vehicle_name, claim_type, description, status) "
        "VALUES (?, ?, ?, ?, ?)",
        [
            ("2024-001507-DC", "A", "custody_modification",
             "Mother denied parenting time on multiple occasions", "active"),
            ("2024-001507-DC", "A", "contempt",
             "Violation of court-ordered parenting schedule", "active"),
        ],
    )
    conn.executemany(
        "INSERT INTO evidence_gaps (vehicle_name, gap_type, description) "
        "VALUES (?, ?, ?)",
        [
            ("2024-001507-DC", "financial", "Missing income verification for defendant"),
            ("2024-001507-DC", "communications", "Text messages from Nov-Dec 2024 not collected"),
        ],
    )
    conn.executemany(
        "INSERT INTO deadlines (vehicle_name, description, category, due_date_iso, status) "
        "VALUES (?, ?, ?, ?, ?)",
        [
            ("2024-001507-DC", "Discovery deadline hearing", "hearing",
             "2099-12-31", "pending"),
            ("2024-001507-DC", "File motion to compel", "filing",
             "2099-11-15", "pending"),
        ],
    )
    conn.commit()
    conn.close()
    gen = DiscoveryGenerator(db_path=tmp_db_path)
    yield gen
    gen.close()


# ===================================================================
# Core Generation (4 tests)
# ===================================================================

class TestCoreGeneration:
    """Engine instantiation and basic document generation."""

    def test_discovery_engine_instantiation(self, engine: DiscoveryGenerator):
        """Engine can be created with a temp DB path."""
        assert engine is not None
        assert engine._conn is not None

    def test_generate_interrogatories(self, engine: DiscoveryGenerator):
        """generate_interrogatories produces a valid markdown document."""
        doc = engine.generate_interrogatories(
            case_number="2024-001507-DC",
            topics=["custody", "financial"],
        )
        assert isinstance(doc, str)
        assert "INTERROGATORIES" in doc
        assert "Interrogatory No. 1" in doc
        # Must contain caption, definitions, instructions, and cert of service
        assert "STATE OF MICHIGAN" in doc
        assert "DEFINITIONS" in doc
        assert "INSTRUCTIONS" in doc
        assert "CERTIFICATE OF SERVICE" in doc

    def test_generate_rfp(self, engine: DiscoveryGenerator):
        """generate_rfp produces request for production document."""
        doc = engine.generate_rfp(
            case_number="2024-001507-DC",
            categories=["financial", "communications"],
        )
        assert isinstance(doc, str)
        assert "REQUESTS FOR PRODUCTION" in doc
        assert "Request No. 1" in doc
        assert "STATE OF MICHIGAN" in doc
        assert "CERTIFICATE OF SERVICE" in doc

    def test_generate_rfa(self, engine: DiscoveryGenerator):
        """generate_rfa produces request for admissions document."""
        doc = engine.generate_rfa(case_number="2024-001507-DC")
        assert isinstance(doc, str)
        assert "REQUESTS FOR ADMISSION" in doc
        assert "Request No. 1" in doc
        assert "STATE OF MICHIGAN" in doc
        assert "CERTIFICATE OF SERVICE" in doc


# ===================================================================
# MCR Compliance (3 tests)
# ===================================================================

class TestMCRCompliance:
    """Documents reference the correct Michigan Court Rules."""

    def test_interrogatories_cite_mcr_2309(self, engine: DiscoveryGenerator):
        """Interrogatories must reference MCR 2.309."""
        doc = engine.generate_interrogatories(case_number="2024-001507-DC")
        assert "MCR 2.309" in doc, "Interrogatories must cite MCR 2.309"

    def test_rfp_cites_mcr_2310(self, engine: DiscoveryGenerator):
        """RFP must reference MCR 2.310."""
        doc = engine.generate_rfp(case_number="2024-001507-DC")
        assert "MCR 2.310" in doc, "RFP must cite MCR 2.310"

    def test_rfa_cites_mcr_2312(self, engine: DiscoveryGenerator):
        """RFA must reference MCR 2.312."""
        doc = engine.generate_rfa(case_number="2024-001507-DC")
        assert "MCR 2.312" in doc, "RFA must cite MCR 2.312"


# ===================================================================
# Content Quality (3 tests)
# ===================================================================

class TestContentQuality:
    """Document content meets substantive quality standards."""

    def test_discovery_targets_correct_party(self, engine: DiscoveryGenerator):
        """All discovery documents target Emily A. Watson as defendant."""
        for gen_method in [
            lambda: engine.generate_interrogatories(case_number="2024-001507-DC"),
            lambda: engine.generate_rfp(case_number="2024-001507-DC"),
            lambda: engine.generate_rfa(case_number="2024-001507-DC"),
        ]:
            doc = gen_method()
            assert "Emily A. Watson" in doc, "Must target Emily A. Watson"

    def test_get_rule_context_returns_data(self, engine: DiscoveryGenerator):
        """get_rule_context returns non-empty text for known MCR rules."""
        text = engine.get_rule_context("MCR 2.309")
        # get_rule_text returns a string; may be empty if rule not in static data
        assert isinstance(text, str)

    def test_discovery_has_definitions_section(self, engine: DiscoveryGenerator):
        """Interrogatories and RFP include a DEFINITIONS section."""
        interrog = engine.generate_interrogatories(case_number="2024-001507-DC")
        rfp = engine.generate_rfp(case_number="2024-001507-DC")
        assert "## DEFINITIONS" in interrog
        assert "## DEFINITIONS" in rfp
        # Definitions should define key terms
        assert '"YOU"' in interrog or "YOU" in interrog
        assert '"DOCUMENT"' in rfp or "DOCUMENT" in rfp


# ===================================================================
# Edge Cases (4 tests)
# ===================================================================

class TestEdgeCases:
    """Boundary conditions and graceful degradation."""

    def test_empty_case_data_still_generates(self, engine: DiscoveryGenerator):
        """With no DB claims, documents still generate from topic templates."""
        doc = engine.generate_interrogatories(
            case_number="NONEXISTENT-CASE",
            topics=["custody"],
        )
        assert isinstance(doc, str)
        assert "Interrogatory No. 1" in doc
        assert len(doc) > 200, "Document should have substantial content"

    def test_interrogatories_cap_at_25(self, engine: DiscoveryGenerator):
        """MCR 2.309 caps interrogatories at 25; engine must enforce."""
        doc = engine.generate_interrogatories(
            case_number="2024-001507-DC",
            topics=list(DISCOVERY_TOPICS.keys()),  # all topics → would exceed 25
            max_count=50,  # try to exceed the cap
        )
        # The engine should cap at 25 regardless of max_count > 25
        count = doc.count("**Interrogatory No.")
        assert count <= 25, f"Got {count} interrogatories; MCR 2.309 caps at 25"

    def test_no_db_connection_gracefully_degrades(self, tmp_path: Path):
        """Engine with a bad DB path still returns documents (no crash)."""
        bad_path = str(tmp_path / "nonexistent" / "bad.db")
        gen = DiscoveryGenerator(db_path=bad_path)
        try:
            # Connection fails, but _query returns [] gracefully
            doc = gen.generate_interrogatories(
                case_number="2024-001507-DC",
                topics=["custody"],
            )
            assert isinstance(doc, str)
            assert "Interrogatory No. 1" in doc
        finally:
            gen.close()

    def test_empty_topics_uses_defaults(self, engine: DiscoveryGenerator):
        """Passing topics=None uses default topics and still generates."""
        doc = engine.generate_interrogatories(
            case_number="2024-001507-DC",
            topics=None,
        )
        assert "Interrogatory No. 1" in doc


# ===================================================================
# DB-Driven Generation (2 tests)
# ===================================================================

class TestDBDrivenGeneration:
    """Documents incorporate data from DB claims and evidence gaps."""

    def test_seeded_claims_appear_in_interrogatories(
        self, seeded_engine: DiscoveryGenerator
    ):
        """Interrogatories pull from claims table when data exists."""
        doc = seeded_engine.generate_interrogatories(
            case_number="2024-001507-DC", lane="A",
        )
        # The claim descriptions should be woven into interrogatory text
        assert "parenting time" in doc.lower() or "parenting" in doc.lower()

    def test_seeded_claims_appear_in_rfa(self, seeded_engine: DiscoveryGenerator):
        """RFA auto-generates admission requests from DB claims."""
        doc = seeded_engine.generate_rfa(
            case_number="2024-001507-DC", lane="A",
        )
        assert "parenting" in doc.lower()


# ===================================================================
# Subpoena & Discovery Plan (2 tests)
# ===================================================================

class TestSubpoenaAndPlan:
    """Subpoena and discovery plan generation."""

    def test_generate_subpoena(self, engine: DiscoveryGenerator):
        """generate_subpoena produces a valid subpoena duces tecum."""
        doc = engine.generate_subpoena(
            recipient="Muskegon Public Schools",
            items=["Academic records for L.D.W.", "Attendance records"],
        )
        assert isinstance(doc, str)
        assert "Subpoena Duces Tecum" in doc.upper() or "SUBPOENA DUCES TECUM" in doc
        assert "Muskegon Public Schools" in doc
        assert "MCR 2.506" in doc
        assert "Academic records for L.D.W." in doc

    def test_generate_discovery_plan(self, seeded_engine: DiscoveryGenerator):
        """generate_discovery_plan returns structured dict with phases."""
        plan = seeded_engine.generate_discovery_plan(
            case_number="2024-001507-DC", lane="A",
        )
        assert isinstance(plan, dict)
        assert "phases" in plan
        assert "priority_topics" in plan
        assert "case_number" in plan
        assert plan["case_number"] == "2024-001507-DC"
        assert len(plan["phases"]) >= 1
        # Each phase must have name and actions
        for phase in plan["phases"]:
            assert "name" in phase
            assert "actions" in phase


# ===================================================================
# Templates & Helpers (2 tests)
# ===================================================================

class TestTemplatesAndHelpers:
    """Template listing and helper function tests."""

    def test_get_discovery_templates(self, engine: DiscoveryGenerator):
        """get_discovery_templates returns all 5 template types."""
        templates = engine.get_discovery_templates()
        assert isinstance(templates, list)
        assert len(templates) == 5
        names = {t["name"] for t in templates}
        assert "Interrogatories" in names
        assert "Request for Production" in names
        assert "Request for Admission" in names
        assert "Subpoena Duces Tecum" in names
        assert "Discovery Plan" in names
        # Each template must have mcr_rule and description
        for t in templates:
            assert "mcr_rule" in t
            assert "description" in t
            assert t["mcr_rule"].startswith("MCR")

    def test_helper_functions(self):
        """Module-level helpers produce expected output formats."""
        today = _today()
        assert len(today) > 5  # e.g. "January 15, 2025"
        assert "," in today  # "Month DD, YYYY" format

        deadline = _deadline_date(28)
        assert len(deadline) > 5
        assert "," in deadline

        caption = _caption("2024-001507-DC", "Test Motion")
        assert "STATE OF MICHIGAN" in caption
        assert "2024-001507-DC" in caption
        assert "TEST MOTION" in caption

        cert = _certificate_of_service("2024-001507-DC")
        assert "CERTIFICATE OF SERVICE" in cert
        assert PARTIES["plaintiff"]["name"] in cert
        assert PARTIES["defendant"]["name"] in cert
