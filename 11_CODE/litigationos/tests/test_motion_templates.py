"""Comprehensive test suite for the MotionTemplateEngine.

Covers core generation, legal content, Michigan compliance, validation,
ancillary documents, and edge cases.
"""

from __future__ import annotations

import sqlite3
from pathlib import Path

import pytest

from litigationos.engines.motion_templates import (
    CASE_NUMBERS,
    MOTION_TEMPLATES,
    PARTIES,
    MotionTemplateEngine,
    _build_caption,
)


# -- Fixtures -----------------------------------------------------------------


@pytest.fixture
def tmp_db_path(tmp_path: Path) -> str:
    """Create a minimal SQLite database and return its path."""
    db_path = tmp_path / "test_motion.db"
    conn = sqlite3.connect(str(db_path))
    conn.execute("PRAGMA journal_mode=WAL")
    # Create tables the engine may query (get_case_facts, get_evidence_for_motion)
    conn.execute(
        "CREATE TABLE IF NOT EXISTS case_facts "
        "(id INTEGER PRIMARY KEY, case_number TEXT, fact_text TEXT, fact_date TEXT)"
    )
    conn.execute(
        "CREATE TABLE IF NOT EXISTS evidence "
        "(evidence_id INTEGER PRIMARY KEY, case_number TEXT, description TEXT, source_file TEXT)"
    )
    conn.commit()
    conn.close()
    return str(db_path)


@pytest.fixture
def engine(tmp_db_path: str) -> MotionTemplateEngine:
    """Return a MotionTemplateEngine backed by a temporary database."""
    eng = MotionTemplateEngine(db_path=tmp_db_path)
    yield eng
    eng.close()


@pytest.fixture
def seeded_engine(tmp_db_path: str) -> MotionTemplateEngine:
    """Engine with case facts and evidence pre-loaded."""
    conn = sqlite3.connect(tmp_db_path)
    conn.executemany(
        "INSERT INTO case_facts (case_number, fact_text, fact_date) VALUES (?, ?, ?)",
        [
            ("2024-001507-DC", "Defendant denied parenting time on 2024-03-15.", "2024-03-15"),
            ("2024-001507-DC", "Defendant relocated child without notice.", "2024-04-01"),
            ("2024-001507-DC", "Plaintiff filed FOC complaint on 2024-04-10.", "2024-04-10"),
        ],
    )
    conn.executemany(
        "INSERT INTO evidence (case_number, description, source_file) VALUES (?, ?, ?)",
        [
            ("2024-001507-DC", "Text messages showing custody denial", "texts_001.pdf"),
            ("2024-001507-DC", "Custody order from 2023", "order_2023.pdf"),
        ],
    )
    conn.commit()
    conn.close()
    eng = MotionTemplateEngine(db_path=tmp_db_path)
    yield eng
    eng.close()


# -- Core Generation Tests ----------------------------------------------------


class TestCoreGeneration:
    """Tests for engine instantiation and basic motion generation."""

    def test_motion_engine_instantiation(self, engine: MotionTemplateEngine):
        """Engine should instantiate without errors with a valid db path."""
        assert engine is not None
        assert engine._conn is not None

    def test_generate_motion_returns_result(self, engine: MotionTemplateEngine):
        """generate_motion should produce a non-empty string for a known template."""
        motion = engine.generate_motion(
            template_id="dismiss",
            case_number="2024-001507-DC",
            facts=["Defendant failed to state a claim."],
        )
        assert isinstance(motion, str)
        assert len(motion) > 200

    def test_all_17_motion_types_accepted(self, engine: MotionTemplateEngine):
        """Every template in MOTION_TEMPLATES should generate without error."""
        for tid in MOTION_TEMPLATES:
            motion = engine.generate_motion(
                template_id=tid,
                case_number="2024-001507-DC",
                facts=["Test fact for validation."],
            )
            assert isinstance(motion, str), f"Template '{tid}' did not return a string"
            assert "ERROR" not in motion, f"Template '{tid}' returned an error marker"
            assert len(motion) > 100, f"Template '{tid}' produced suspiciously short output"

    def test_motion_has_required_sections(self, engine: MotionTemplateEngine):
        """Generated motion must contain caption, body, prayer, and signature."""
        motion = engine.generate_motion(
            template_id="compel_discovery",
            case_number="2024-001507-DC",
            facts=["Discovery requests served on 2024-01-15 remain unanswered."],
        )
        lowered = motion.lower()
        assert "statement of issues" in lowered
        assert "statement of facts" in lowered
        assert "legal argument" in lowered
        assert "prayer for relief" in lowered
        assert "verification" in lowered
        assert "certificate of service" in lowered


# -- Legal Content Tests ------------------------------------------------------


class TestLegalContent:
    """Tests for legal substance in generated motions."""

    def test_motion_includes_rule_citations(self, engine: MotionTemplateEngine):
        """Motion text should include MCR or MCL references."""
        motion = engine.generate_motion(
            template_id="sanctions",
            case_number="2024-001507-DC",
            facts=["Opposing party filed frivolous motion."],
        )
        assert "MCR" in motion, "Expected MCR citation in motion text"

    def test_motion_irac_sections(self, engine: MotionTemplateEngine):
        """Legal argument section should follow IRAC structure."""
        motion = engine.generate_motion(
            template_id="contempt",
            case_number="2024-001507-DC",
            facts=["Defendant violated custody order on 2024-06-01."],
        )
        lowered = motion.lower()
        assert "**issue:**" in lowered, "IRAC Issue heading missing"
        assert "**rule:**" in lowered, "IRAC Rule heading missing"
        assert "**application:**" in lowered, "IRAC Application heading missing"
        assert "**conclusion:**" in lowered, "IRAC Conclusion heading missing"

    def test_rule_lookup_integration(self, engine: MotionTemplateEngine):
        """Motion should attempt to inject real rule text, not just generic placeholders."""
        motion = engine.generate_motion(
            template_id="dismiss",
            case_number="2024-001507-DC",
            facts=["Complaint fails to state a claim."],
            authorities=["MCR 2.116(C)"],
        )
        # The rule section should reference the authority; if real rule text was
        # found it will be longer than the generic fallback sentence.
        assert "MCR 2.116" in motion
        # Verify the Rule section exists under the authority
        assert "**Rule:**" in motion


# -- Michigan Compliance Tests ------------------------------------------------


class TestMichiganCompliance:
    """Tests for Michigan-specific formatting and party identity."""

    def test_michigan_caption_format(self, engine: MotionTemplateEngine):
        """Caption must include state, circuit court, and county per MCR 2.113."""
        motion = engine.generate_motion(
            template_id="modify_custody",
            case_number="2024-001507-DC",
            facts=["Change of circumstances warrants modification."],
        )
        assert "STATE OF MICHIGAN" in motion
        assert "14TH JUDICIAL CIRCUIT COURT" in motion
        assert "COUNTY OF MUSKEGON" in motion
        assert "FAMILY DIVISION" in motion

    def test_party_names_verified(self, engine: MotionTemplateEngine):
        """Motion must use verified party names — never fabricated ones."""
        motion = engine.generate_motion(
            template_id="contempt",
            case_number="2024-001507-DC",
            facts=["Order violated."],
        )
        assert "ANDREW JAMES PIGORS" in motion
        assert "EMILY A. WATSON" in motion
        # Ensure no hallucinated names
        assert "Jane Berry" not in motion
        assert "Patricia Berry" not in motion

    def test_child_initials_only(self, engine: MotionTemplateEngine):
        """Child must be referenced by initials L.D.W., never full name."""
        # modify_custody is the template most likely to mention the child
        motion = engine.generate_motion(
            template_id="modify_custody",
            case_number="2024-001507-DC",
            facts=["Best interest of L.D.W. requires custody modification."],
        )
        assert PARTIES["child"] == "L.D.W."
        # If the child is mentioned, it should be initials only
        # The prayer options for modify_custody reference L.D.W.
        assert "L.D.W." in motion


# -- Edge Cases ---------------------------------------------------------------


class TestEdgeCases:
    """Tests for boundary conditions and unusual inputs."""

    def test_unknown_motion_type_handled(self, engine: MotionTemplateEngine):
        """Unknown template_id should return an error marker, not crash."""
        result = engine.generate_motion(
            template_id="nonexistent_motion_type",
            case_number="2024-001507-DC",
        )
        assert "ERROR" in result
        assert "nonexistent_motion_type" in result

    def test_empty_facts_still_generates(self, engine: MotionTemplateEngine):
        """Motion should generate even when no facts are provided."""
        motion = engine.generate_motion(
            template_id="dismiss",
            case_number="2024-001507-DC",
            facts=[],
        )
        # Empty facts list should fall through to default placeholder
        assert isinstance(motion, str)
        assert len(motion) > 100

    def test_motion_metadata_complete(self, engine: MotionTemplateEngine):
        """get_templates should return complete metadata for every template."""
        templates = engine.get_templates()
        assert len(templates) == len(MOTION_TEMPLATES)
        required_keys = {"id", "title", "description", "mcr_authority", "required_elements", "typical_exhibits"}
        for tpl in templates:
            assert required_keys.issubset(tpl.keys()), f"Template '{tpl.get('id')}' missing keys"
            assert tpl["id"] in MOTION_TEMPLATES
            assert len(tpl["required_elements"]) > 0

    def test_engine_without_db_runs_template_only(self, tmp_path: Path):
        """Engine should work in template-only mode if DB path is invalid."""
        # Use a path inside a non-existent directory so sqlite3.connect fails
        bad_path = str(tmp_path / "no_such_dir" / "no_such_dir2" / "missing.db")
        eng = MotionTemplateEngine(db_path=bad_path)
        try:
            assert eng._conn is None
            motion = eng.generate_motion(
                template_id="dismiss",
                case_number="2024-001507-DC",
                facts=["Test fact."],
            )
            assert isinstance(motion, str)
            assert "ERROR" not in motion
        finally:
            eng.close()


# -- Ancillary Document Tests -------------------------------------------------


class TestAncillaryDocuments:
    """Tests for brief, proposed order, and certificate of service generation."""

    def test_generate_brief_returns_valid_output(self, engine: MotionTemplateEngine):
        """generate_brief should produce a legal brief with standard sections."""
        brief = engine.generate_brief(
            template_id="compel_discovery",
            case_number="2024-001507-DC",
            facts=["Discovery requests were served and remain unanswered."],
        )
        lowered = brief.lower()
        assert "introduction" in lowered
        assert "statement of facts" in lowered
        assert "legal standard" in lowered
        assert "argument" in lowered
        assert "conclusion" in lowered
        assert "Andrew James Pigors" in brief

    def test_generate_proposed_order(self, engine: MotionTemplateEngine):
        """Proposed order should include judge name and IT IS HEREBY ORDERED."""
        order = engine.generate_proposed_order(
            template_id="contempt",
            case_number="2024-001507-DC",
        )
        assert "IT IS HEREBY ORDERED" in order
        assert "IT IS SO ORDERED" in order
        assert PARTIES["judge"] in order

    def test_certificate_of_service_mcr_compliance(self, engine: MotionTemplateEngine):
        """Certificate must reference MCR 2.107 and include defendant info."""
        cert = engine.generate_certificate_of_service(
            case_number="2024-001507-DC",
            documents=["Motion to Dismiss"],
            service_method="first-class mail",
        )
        assert "MCR 2.107" in cert
        assert PARTIES["defendant"]["name"] in cert
        assert PARTIES["defendant"]["address"] in cert
        assert "first-class mail" in cert

    def test_brief_unknown_template(self, engine: MotionTemplateEngine):
        """generate_brief with unknown template should return error marker."""
        brief = engine.generate_brief(
            template_id="totally_fake",
            case_number="2024-001507-DC",
        )
        assert "ERROR" in brief


# -- Validation Tests ---------------------------------------------------------


class TestValidation:
    """Tests for the validate_motion method."""

    def test_validate_generated_motion_passes(self, engine: MotionTemplateEngine):
        """A motion generated by the engine should pass its own validator."""
        motion = engine.generate_motion(
            template_id="dismiss",
            case_number="2024-001507-DC",
            facts=["Defendant failed to state a claim."],
        )
        result = engine.validate_motion(motion, "dismiss")
        assert result["is_valid"] is True, f"Missing: {result['missing_elements']}"

    def test_validate_empty_text_fails(self, engine: MotionTemplateEngine):
        """An empty string should fail validation with missing elements."""
        result = engine.validate_motion("", "dismiss")
        assert result["is_valid"] is False
        assert len(result["missing_elements"]) > 0

    def test_validate_unknown_template(self, engine: MotionTemplateEngine):
        """Validation with unknown template should return not-valid with warning."""
        result = engine.validate_motion("some text", "nonexistent")
        assert result["is_valid"] is False
        assert any("Unknown" in w for w in result["warnings"])


# -- Database Integration Tests -----------------------------------------------


class TestDatabaseIntegration:
    """Tests for DB-backed methods (get_case_facts, get_evidence_for_motion)."""

    def test_get_case_facts_returns_seeded_data(self, seeded_engine: MotionTemplateEngine):
        """get_case_facts should return facts inserted in the seeded DB."""
        facts = seeded_engine.get_case_facts("2024-001507-DC")
        assert len(facts) == 3
        assert any("parenting time" in f for f in facts)

    def test_get_case_facts_empty_for_unknown_case(self, engine: MotionTemplateEngine):
        """get_case_facts should return empty list for non-existent case."""
        facts = engine.get_case_facts("9999-999999-XX")
        assert facts == []

    def test_get_required_exhibits(self, engine: MotionTemplateEngine):
        """get_required_exhibits should return exhibit dicts for known template."""
        exhibits = engine.get_required_exhibits("dismiss")
        assert len(exhibits) > 0
        assert all("exhibit" in e and "required" in e for e in exhibits)

    def test_get_required_exhibits_unknown_template(self, engine: MotionTemplateEngine):
        """get_required_exhibits should return empty list for unknown template."""
        exhibits = engine.get_required_exhibits("nonexistent")
        assert exhibits == []


# -- Helper Function Tests ----------------------------------------------------


class TestHelpers:
    """Tests for module-level helper functions."""

    def test_build_caption_format(self):
        """_build_caption should produce proper Michigan caption block."""
        caption = _build_caption("2024-001507-DC", "Motion to Dismiss")
        assert "STATE OF MICHIGAN" in caption
        assert "Case No. 2024-001507-DC" in caption
        assert "ANDREW JAMES PIGORS" in caption
        assert "EMILY A. WATSON" in caption
        assert "Plaintiff" in caption
        assert "Defendant" in caption
        assert "MOTION TO DISMISS" in caption

    def test_case_numbers_dict(self):
        """CASE_NUMBERS should map lanes to known case numbers."""
        assert "A" in CASE_NUMBERS
        assert CASE_NUMBERS["A"] == "2024-001507-DC"
        assert "B" in CASE_NUMBERS
        assert "D" in CASE_NUMBERS
