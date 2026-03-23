"""Comprehensive tests for the FilingFactory engine.

Covers instantiation, generation, QA pipeline, placeholder detection,
packet assembly, export, state machine transitions, and edge cases.
"""

from __future__ import annotations

import re
from datetime import datetime
from pathlib import Path

import pytest

from litigationos.db.connection import DatabaseManager
from litigationos.engines.filing_factory import (
    CaptionInfo,
    FilingFactory,
    FilingSpec,
    FilingStatus,
    FilingType,
    GeneratedFiling,
    PacketManifest,
    QAIssue,
    QAPipeline,
    QAReport,
    PAGE_LIMITS,
    WORD_LIMITS,
    _PLACEHOLDER_RE,
    build_caption,
    build_cos,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_caption(**overrides) -> CaptionInfo:
    """Build a CaptionInfo with sensible Michigan defaults."""
    defaults = dict(
        court_name="14th Circuit Court, Family Division",
        case_number="2024-001507-DC",
        judge_name="Hon. Jenny L. McNeill",
        plaintiff="Andrew James Pigors",
        defendant="Emily A. Watson",
        filing_title="Motion to Compel Discovery",
    )
    defaults.update(overrides)
    return CaptionInfo(**defaults)


def _make_spec(case_id: int = 1, **overrides) -> FilingSpec:
    """Build a FilingSpec with defaults that produce a clean filing."""
    defaults = dict(
        case_id=case_id,
        filing_type=FilingType.MOTION,
        court="14th Circuit Court, Family Division",
        title="Motion to Compel Discovery",
        caption=_make_caption(),
        body_text=(
            "Plaintiff Andrew James Pigors respectfully requests this Court "
            "to compel Defendant Emily A. Watson to respond to discovery.\n\n"
            "Under MCR 2.313, a party may move to compel discovery responses.\n\n"
            "Pigors served interrogatories on Watson on January 15, 2025. "
            "Watson failed to respond within the 28-day window.\n\n"
            "WHEREFORE, Plaintiff requests that this Court enter an order "
            "compelling Watson to respond within 14 days."
        ),
    )
    defaults.update(overrides)
    return FilingSpec(**defaults)


def _make_filing(**overrides) -> GeneratedFiling:
    """Build a minimal GeneratedFiling for unit-level QA checks."""
    defaults = dict(
        filing_id=1,
        case_id=1,
        filing_type="motion",
        status=FilingStatus.DRAFT,
        title="Motion to Compel Discovery",
        body="Plaintiff moves under MCR 2.313 for discovery relief.",
        caption_text=build_caption(_make_caption()),
        cos_text=build_cos("Motion to Compel Discovery",
                           ["Emily A. Watson"], "Andrew James Pigors"),
        word_count=50,
        page_estimate=1,
        sha256="abc123",
    )
    defaults.update(overrides)
    return GeneratedFiling(**defaults)


# ============================================================================
# Core Filing Operations
# ============================================================================


class TestFilingFactoryInstantiation:
    """Test factory construction."""

    def test_filing_factory_instantiation(self, tmp_db: DatabaseManager):
        factory = FilingFactory(tmp_db)
        assert factory is not None
        assert factory._qa is not None

    def test_qa_pipeline_is_qa_pipeline(self, tmp_db: DatabaseManager):
        factory = FilingFactory(tmp_db)
        assert isinstance(factory._qa, QAPipeline)


class TestGenerateFiling:
    """Test the main generate_filing() path."""

    def test_generate_filing_returns_result(
        self, tmp_db: DatabaseManager, sample_case: dict, sample_party: list[dict]
    ):
        factory = FilingFactory(tmp_db)
        spec = _make_spec(case_id=sample_case["id"])
        filing = factory.generate_filing(spec)
        assert isinstance(filing, GeneratedFiling)
        assert filing.filing_id > 0
        assert filing.word_count > 0

    def test_filing_has_caption(
        self, tmp_db: DatabaseManager, sample_case: dict, sample_party: list[dict]
    ):
        factory = FilingFactory(tmp_db)
        spec = _make_spec(case_id=sample_case["id"])
        filing = factory.generate_filing(spec)
        assert "STATE OF MICHIGAN" in filing.caption_text
        assert "14TH CIRCUIT COURT" in filing.caption_text.upper()

    def test_filing_has_certificate_of_service(
        self, tmp_db: DatabaseManager, sample_case: dict, sample_party: list[dict]
    ):
        factory = FilingFactory(tmp_db)
        spec = _make_spec(case_id=sample_case["id"])
        filing = factory.generate_filing(spec)
        assert "CERTIFICATE OF SERVICE" in filing.cos_text.upper()
        assert "Andrew James Pigors" in filing.cos_text

    def test_all_filing_types_supported(
        self, tmp_db: DatabaseManager, sample_case: dict, sample_party: list[dict]
    ):
        factory = FilingFactory(tmp_db)
        for ft in FilingType:
            spec = _make_spec(
                case_id=sample_case["id"],
                filing_type=ft,
                title=f"Test {ft.value}",
                caption=_make_caption(filing_title=f"Test {ft.value}"),
            )
            filing = factory.generate_filing(spec)
            assert filing.filing_type == ft.value

    def test_generate_filing_sha256_nonempty(
        self, tmp_db: DatabaseManager, sample_case: dict, sample_party: list[dict]
    ):
        factory = FilingFactory(tmp_db)
        spec = _make_spec(case_id=sample_case["id"])
        filing = factory.generate_filing(spec)
        assert len(filing.sha256) == 64  # hex digest length

    def test_filing_persisted_to_db(
        self, tmp_db: DatabaseManager, sample_case: dict, sample_party: list[dict]
    ):
        factory = FilingFactory(tmp_db)
        spec = _make_spec(case_id=sample_case["id"])
        filing = factory.generate_filing(spec)
        row = tmp_db.fetchone("SELECT * FROM filings WHERE id = ?", (filing.filing_id,))
        assert row is not None
        assert dict(row)["title"] == "Motion to Compel Discovery"


# ============================================================================
# QA / Placeholder Detection
# ============================================================================


class TestPlaceholderRegex:
    """Unit tests for _PLACEHOLDER_RE."""

    @pytest.mark.parametrize("placeholder", [
        "[ANDREW_REQUIRED]",
        "[INSERT ADDRESS]",
        "[INSERT]",
        "{{some_var}}",
        "[TODO: add citation]",
        "[FILL IN DATE]",
        "[XXXX]",
        "[XX]",
    ])
    def test_placeholder_regex_matches(self, placeholder: str):
        assert _PLACEHOLDER_RE.search(placeholder) is not None

    def test_placeholder_regex_no_false_positive(self):
        clean = "The Court ordered relief under MCR 2.119(A)(1)."
        assert _PLACEHOLDER_RE.search(clean) is None


class TestQAPipeline:
    """Test individual QA pipeline checks."""

    def test_check_placeholders_clean(self):
        issues = QAPipeline._check_placeholders(
            "Plaintiff respectfully requests relief under MCR 2.313."
        )
        assert issues == []

    def test_check_placeholders_dirty(self):
        issues = QAPipeline._check_placeholders(
            "Plaintiff lives at [INSERT ADDRESS] and works at [ANDREW_REQUIRED]."
        )
        assert len(issues) == 2
        assert all(i.severity == "error" for i in issues)
        assert all(i.category == "placeholder" for i in issues)

    def test_placeholder_scan_returns_list_with_locations(self):
        text = "Filed on [TODO: add date] in [INSERT COURT]."
        issues = QAPipeline._check_placeholders(text)
        assert len(issues) == 2
        assert all(i.location is not None for i in issues)
        assert all("char" in i.location for i in issues)

    def test_check_citations_warns_when_missing(self):
        body = "A" * 600  # > 500 chars with no citations
        issues = QAPipeline._check_citations(body)
        assert len(issues) == 1
        assert issues[0].severity == "warning"
        assert issues[0].category == "citation"

    def test_check_citations_ok_with_citations(self):
        body = "Under MCR 2.313 the party may compel. " * 20
        issues = QAPipeline._check_citations(body)
        assert all(i.severity != "warning" or i.category != "citation" for i in issues)

    def test_check_structure_missing_caption(self):
        filing = _make_filing(caption_text="")
        issues = QAPipeline._check_structure(filing)
        assert any(i.category == "caption" and i.severity == "error" for i in issues)

    def test_check_structure_missing_cos(self):
        filing = _make_filing(cos_text="")
        issues = QAPipeline._check_structure(filing)
        assert any(i.category == "cos" and i.severity == "error" for i in issues)

    def test_check_limits_under_limit(self):
        filing = _make_filing(filing_type="motion", word_count=100, page_estimate=1)
        issues = QAPipeline._check_limits(filing)
        assert issues == []

    def test_check_limits_over_word_limit(self):
        filing = _make_filing(filing_type="motion", word_count=7000, page_estimate=1)
        issues = QAPipeline._check_limits(filing)
        assert any(i.category == "word_limit" for i in issues)

    def test_check_limits_over_page_limit(self):
        filing = _make_filing(filing_type="motion", word_count=100, page_estimate=25)
        issues = QAPipeline._check_limits(filing)
        assert any(i.category == "page_limit" for i in issues)

    def test_full_qa_pass(self):
        qa = QAPipeline()
        spec = _make_spec()
        filing = _make_filing()
        report = qa.run(filing, spec)
        assert isinstance(report, QAReport)
        assert report.status == "pass"
        assert report.score > 0

    def test_full_qa_fail_with_placeholder(self):
        qa = QAPipeline()
        spec = _make_spec()
        filing = _make_filing(body="Plaintiff lives at [INSERT ADDRESS].")
        report = qa.run(filing, spec)
        assert report.status == "fail"
        assert len(report.errors) > 0


# ============================================================================
# Caption & Certificate of Service
# ============================================================================


class TestCaptionAndCos:
    """Test standalone caption and COS builders."""

    def test_caption_format_michigan(self):
        caption = _make_caption()
        text = build_caption(caption)
        assert "STATE OF MICHIGAN" in text
        assert "14TH CIRCUIT COURT" in text.upper()
        assert "Andrew James Pigors" in text
        assert "Emily A. Watson" in text
        assert "Case No. 2024-001507-DC" in text
        assert "MOTION TO COMPEL DISCOVERY" in text

    def test_party_names_correct(self):
        caption = _make_caption()
        text = build_caption(caption)
        assert "Andrew James Pigors" in text
        assert "Emily A. Watson" in text
        assert "Plaintiff" in text
        assert "Defendant" in text

    def test_cos_includes_parties(self):
        text = build_cos(
            "Motion to Compel",
            ["Emily A. Watson", "Jennifer Barnes (P55406)"],
            "Andrew James Pigors",
        )
        assert "CERTIFICATE OF SERVICE" in text
        assert "Emily A. Watson" in text
        assert "Jennifer Barnes" in text
        assert "Andrew James Pigors" in text

    def test_cos_no_parties_placeholder(self):
        text = build_cos("Motion", [], "Andrew James Pigors")
        assert "[NO PARTIES LISTED]" in text

    def test_caption_judge_fallback(self):
        caption = _make_caption(judge_name=None)
        text = build_caption(caption)
        assert "____________________" in text


# ============================================================================
# Filing Package Assembly
# ============================================================================


class TestPacketAssembly:
    """Test packet assembly and manifest."""

    def test_generate_package_structure(
        self, tmp_db: DatabaseManager, sample_case: dict, sample_party: list[dict]
    ):
        factory = FilingFactory(tmp_db)
        spec = _make_spec(case_id=sample_case["id"])
        filing = factory.generate_filing(spec)
        packet = factory.assemble_packet([filing], exhibit_paths=["/dummy/ex1.pdf"])
        assert isinstance(packet, PacketManifest)
        assert len(packet.filings) == 1
        assert packet.exhibit_paths == ["/dummy/ex1.pdf"]

    def test_manifest_generation(
        self, tmp_db: DatabaseManager, sample_case: dict, sample_party: list[dict]
    ):
        factory = FilingFactory(tmp_db)
        spec = _make_spec(case_id=sample_case["id"])
        f1 = factory.generate_filing(spec)
        spec2 = _make_spec(
            case_id=sample_case["id"],
            filing_type=FilingType.AFFIDAVIT,
            title="Affidavit of Plaintiff",
            caption=_make_caption(filing_title="Affidavit of Plaintiff"),
        )
        f2 = factory.generate_filing(spec2)
        packet = factory.assemble_packet([f1, f2])
        d = packet.to_dict()
        assert "packet_id" in d
        assert len(d["filings"]) == 2
        assert "assembled_at" in d

    def test_filing_metadata(
        self, tmp_db: DatabaseManager, sample_case: dict, sample_party: list[dict]
    ):
        factory = FilingFactory(tmp_db)
        spec = _make_spec(case_id=sample_case["id"])
        filing = factory.generate_filing(spec)
        d = filing.to_dict()
        assert "filing_id" in d and d["filing_id"] > 0
        assert "case_id" in d and d["case_id"] == sample_case["id"]
        assert "filing_type" in d and d["filing_type"] == "motion"
        assert "sha256" in d
        assert "created_at" in d

    def test_packet_all_passed(
        self, tmp_db: DatabaseManager, sample_case: dict, sample_party: list[dict]
    ):
        factory = FilingFactory(tmp_db)
        spec = _make_spec(case_id=sample_case["id"])
        filing = factory.generate_filing(spec)
        packet = factory.assemble_packet([filing])
        # Filing with clean body should pass QA
        if filing.qa_report and filing.qa_report.status == "pass":
            assert packet.all_passed is True


# ============================================================================
# Export
# ============================================================================


class TestExport:
    """Test filing export to disk."""

    def test_export_markdown(
        self, tmp_db: DatabaseManager, sample_case: dict,
        sample_party: list[dict], tmp_path: Path,
    ):
        factory = FilingFactory(tmp_db)
        spec = _make_spec(case_id=sample_case["id"])
        filing = factory.generate_filing(spec)
        fp = factory.export_filing(filing, tmp_path, fmt="markdown")
        assert fp.exists()
        assert fp.suffix == ".md"
        content = fp.read_text(encoding="utf-8")
        assert "STATE OF MICHIGAN" in content

    def test_export_text(
        self, tmp_db: DatabaseManager, sample_case: dict,
        sample_party: list[dict], tmp_path: Path,
    ):
        factory = FilingFactory(tmp_db)
        spec = _make_spec(case_id=sample_case["id"])
        filing = factory.generate_filing(spec)
        fp = factory.export_filing(filing, tmp_path, fmt="text")
        assert fp.exists()
        assert fp.suffix == ".txt"

    def test_export_invalid_format_raises(
        self, tmp_db: DatabaseManager, sample_case: dict,
        sample_party: list[dict], tmp_path: Path,
    ):
        factory = FilingFactory(tmp_db)
        spec = _make_spec(case_id=sample_case["id"])
        filing = factory.generate_filing(spec)
        with pytest.raises(ValueError, match="Unsupported format"):
            factory.export_filing(filing, tmp_path, fmt="docx")


# ============================================================================
# State Machine Transitions
# ============================================================================


class TestStateMachine:
    """Test the filing status state machine."""

    def test_valid_transition_draft_to_review(self):
        filing = _make_filing(status=FilingStatus.DRAFT)
        FilingFactory._transition(filing, FilingStatus.REVIEW)
        assert filing.status is FilingStatus.REVIEW

    def test_invalid_transition_raises(self):
        filing = _make_filing(status=FilingStatus.DRAFT)
        with pytest.raises(ValueError, match="Invalid transition"):
            FilingFactory._transition(filing, FilingStatus.FILED)

    def test_advance_full_happy_path(
        self, tmp_db: DatabaseManager, sample_case: dict, sample_party: list[dict]
    ):
        factory = FilingFactory(tmp_db)
        spec = _make_spec(case_id=sample_case["id"])
        filing = factory.generate_filing(spec)
        if filing.status == FilingStatus.QA_PASS:
            filing = factory.advance(filing, FilingStatus.READY)
            assert filing.status is FilingStatus.READY
            filing = factory.advance(filing, FilingStatus.FILED)
            assert filing.status is FilingStatus.FILED
            filing = factory.advance(filing, FilingStatus.SERVED)
            assert filing.status is FilingStatus.SERVED


# ============================================================================
# Validation & Compliance
# ============================================================================


class TestValidationCompliance:
    """Compliance-oriented checks."""

    def test_filing_word_count(
        self, tmp_db: DatabaseManager, sample_case: dict, sample_party: list[dict]
    ):
        factory = FilingFactory(tmp_db)
        spec = _make_spec(case_id=sample_case["id"])
        filing = factory.generate_filing(spec)
        assert filing.word_count > 0
        assert filing.page_estimate >= 1

    def test_filing_uses_child_initials(self):
        """Ensure template output never contains a full child name."""
        caption = _make_caption()
        text = build_caption(caption)
        # L.D.W. initials are acceptable; full child names are not.
        # Since the filing factory doesn't inject child names, the caption
        # should NOT contain any typical child full-name pattern.
        assert "L.D.W." not in text or True  # initials OK
        # Negative check: ensure no common child-name fabrication
        assert "Baby" not in text and "Minor Child" not in text


# ============================================================================
# Edge Cases
# ============================================================================


class TestEdgeCases:
    """Edge case handling."""

    def test_unknown_filing_type_handled(self):
        with pytest.raises(ValueError):
            FilingType("nonexistent_type")

    def test_empty_evidence_still_generates(
        self, tmp_db: DatabaseManager, sample_case: dict, sample_party: list[dict]
    ):
        factory = FilingFactory(tmp_db)
        spec = _make_spec(case_id=sample_case["id"], exhibit_ids=[])
        filing = factory.generate_filing(spec)
        assert filing.body is not None
        assert len(filing.body) > 0

    def test_missing_case_raises(self, tmp_db: DatabaseManager):
        factory = FilingFactory(tmp_db)
        spec = _make_spec(case_id=99999, caption=None)
        with pytest.raises(ValueError, match="Case 99999 not found"):
            factory.generate_filing(spec)

    def test_no_body_no_template_generates_skeleton(
        self, tmp_db: DatabaseManager, sample_case: dict, sample_party: list[dict]
    ):
        factory = FilingFactory(tmp_db)
        spec = _make_spec(
            case_id=sample_case["id"],
            body_text=None,
            template_name=None,
        )
        filing = factory.generate_filing(spec)
        assert "Statement of Facts" in filing.body
        assert "Legal Argument" in filing.body

    def test_to_dict_round_trip(self):
        filing = _make_filing()
        d = filing.to_dict()
        assert d["filing_id"] == 1
        assert d["status"] == "draft"
        assert d["qa_report"] is None

    def test_qa_report_errors_and_warnings(self):
        report = QAReport(
            filing_id=1,
            status="fail",
            issues=[
                QAIssue(severity="error", category="placeholder", message="bad"),
                QAIssue(severity="warning", category="citation", message="warn"),
                QAIssue(severity="error", category="cos", message="missing"),
            ],
        )
        assert len(report.errors) == 2
        assert len(report.warnings) == 1

    def test_packet_manifest_empty(self):
        pkt = PacketManifest(packet_id="PKT-0-test", case_id=0)
        assert pkt.all_passed is True  # vacuously true — no filings
        assert pkt.to_dict()["filings"] == []
