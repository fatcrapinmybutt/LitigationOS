"""Comprehensive tests for the JTCComplaintGenerator engine."""

from __future__ import annotations

from datetime import date

import pytest

from litigationos.engines.jtc_complaint import (
    CANON_MAP,
    CASE_INFO,
    COMPLAINANT_INFO,
    JTC_ADDRESS,
    JTCComplaint,
    JTCComplaintGenerator,
    JTCViolation,
    ExhibitEntry,
    PatternAnalysis,
    REQUIRED_SECTIONS,
    SEVERITY_WEIGHTS,
    SUBJECT_JUDGE_INFO,
    SeverityResult,
    ValidationResult,
    VIOLATION_CATEGORIES,
)


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def generator() -> JTCComplaintGenerator:
    """JTCComplaintGenerator instance."""
    return JTCComplaintGenerator()


@pytest.fixture
def conflict_violation() -> JTCViolation:
    """The primary Berry-McNeill undisclosed conflict violation."""
    return JTCViolation(
        violation_type="undisclosed_conflict",
        canon_violated="Canon 3(C)(1)",
        description=(
            "Judge McNeill failed to disclose that her husband, Cavan Berry, "
            "is related to Ronald Berry, the domestic partner of defendant "
            "Emily A. Watson. This familial nexus creates a mandatory "
            "disqualification under MCR 2.003(C)(1)(b)."
        ),
        date="2024-01-15",
        evidence_refs=["Exhibit A — Public Records", "Exhibit B — Court Docket"],
        severity=10,
    )


@pytest.fixture
def bias_violation() -> JTCViolation:
    """A bias pattern violation."""
    return JTCViolation(
        violation_type="bias_pattern",
        canon_violated="Canon 3(A)(5)",
        description=(
            "Judge McNeill systematically ruled in favor of defendant Watson "
            "on every contested motion despite controlling legal authority "
            "supporting plaintiff's position."
        ),
        date="2024-06-01",
        evidence_refs=["Exhibit C — Docket Analysis"],
        severity=8,
    )


@pytest.fixture
def retaliation_violation() -> JTCViolation:
    """A retaliation violation."""
    return JTCViolation(
        violation_type="retaliation",
        canon_violated="Canon 2(A)",
        description=(
            "After plaintiff filed a motion to disqualify, Judge McNeill "
            "issued adverse rulings within 48 hours as apparent retaliation."
        ),
        date="2024-07-15",
        evidence_refs=["Exhibit D — Timeline"],
        severity=9,
    )


@pytest.fixture
def sample_violations(
    conflict_violation: JTCViolation,
    bias_violation: JTCViolation,
    retaliation_violation: JTCViolation,
) -> list[JTCViolation]:
    """Three representative violations."""
    return [conflict_violation, bias_violation, retaliation_violation]


@pytest.fixture
def sample_evidence_refs() -> list[dict[str, str]]:
    """Sample evidence reference dicts for exhibit generation."""
    return [
        {
            "title": "Berry-McNeill Family Connection Records",
            "description": "Public records establishing familial relationship",
            "bates_range": "PIGORS-0001 to PIGORS-0015",
        },
        {
            "title": "Court Docket and Ruling History",
            "description": "Complete docket showing pattern of one-sided rulings",
            "bates_range": "PIGORS-0016 to PIGORS-0045",
        },
        {
            "title": "Timeline of Retaliatory Actions",
            "description": "Chronological log of adverse rulings post-recusal motion",
        },
    ]


# ---------------------------------------------------------------------------
# Constants & Model Validation
# ---------------------------------------------------------------------------

class TestConstants:
    """Validate module-level constants and verified party information."""

    def test_violation_categories_count(self) -> None:
        assert len(VIOLATION_CATEGORIES) == 8

    def test_all_categories_have_canon_map(self) -> None:
        for cat in VIOLATION_CATEGORIES:
            assert cat in CANON_MAP, f"Missing CANON_MAP entry for {cat}"

    def test_all_categories_have_severity_weight(self) -> None:
        for cat in VIOLATION_CATEGORIES:
            assert cat in SEVERITY_WEIGHTS, f"Missing weight for {cat}"

    def test_complainant_name_verified(self) -> None:
        assert COMPLAINANT_INFO["name"] == "Andrew James Pigors"

    def test_subject_judge_verified(self) -> None:
        assert SUBJECT_JUDGE_INFO["name"] == "Hon. Jenny L. McNeill"
        assert "14th Circuit" in SUBJECT_JUDGE_INFO["court"]

    def test_case_number_verified(self) -> None:
        assert CASE_INFO["case_number"] == "2024-001507-DC"

    def test_defendant_verified(self) -> None:
        assert CASE_INFO["defendant"] == "Emily A. Watson"

    def test_jtc_address_present(self) -> None:
        assert "3034 W. Grand Blvd." in JTC_ADDRESS
        assert "Detroit, MI 48202" in JTC_ADDRESS

    def test_undisclosed_conflict_is_highest_weight(self) -> None:
        max_cat = max(SEVERITY_WEIGHTS, key=SEVERITY_WEIGHTS.get)  # type: ignore[arg-type]
        assert max_cat == "undisclosed_conflict"


# ---------------------------------------------------------------------------
# Pydantic Models
# ---------------------------------------------------------------------------

class TestJTCViolationModel:
    """Validate the JTCViolation Pydantic model."""

    def test_valid_violation_creates(self, conflict_violation: JTCViolation) -> None:
        assert conflict_violation.violation_type == "undisclosed_conflict"
        assert conflict_violation.severity == 10

    def test_invalid_violation_type_raises(self) -> None:
        with pytest.raises(ValueError, match="Invalid violation_type"):
            JTCViolation(
                violation_type="nonexistent_type",
                canon_violated="Canon 0",
                description="Bad type",
            )

    def test_severity_below_range_raises(self) -> None:
        with pytest.raises(ValueError):
            JTCViolation(
                violation_type="bias_pattern",
                canon_violated="Canon 3(A)(5)",
                description="Test",
                severity=0,
            )

    def test_severity_above_range_raises(self) -> None:
        with pytest.raises(ValueError):
            JTCViolation(
                violation_type="bias_pattern",
                canon_violated="Canon 3(A)(5)",
                description="Test",
                severity=11,
            )

    def test_default_severity_is_five(self) -> None:
        v = JTCViolation(
            violation_type="demeanor_violations",
            canon_violated="Canon 3(A)(3)",
            description="Default severity test",
        )
        assert v.severity == 5

    def test_evidence_refs_default_empty(self) -> None:
        v = JTCViolation(
            violation_type="bias_pattern",
            canon_violated="Canon 3(A)(5)",
            description="No evidence",
        )
        assert v.evidence_refs == []


class TestExhibitEntryModel:
    def test_exhibit_entry_creates(self) -> None:
        ex = ExhibitEntry(exhibit_id="Exhibit A", title="Test Doc")
        assert ex.exhibit_id == "Exhibit A"
        assert ex.description is None


class TestPatternAnalysisModel:
    def test_pattern_defaults(self) -> None:
        p = PatternAnalysis()
        assert p.violation_count == 0
        assert p.severity_score == 0.0
        assert p.escalation_timeline == []


class TestJTCComplaintModel:
    def test_complaint_creates_empty(self) -> None:
        c = JTCComplaint()
        assert c.violations == []
        assert c.exhibits == []


# ---------------------------------------------------------------------------
# list_violation_categories
# ---------------------------------------------------------------------------

class TestListViolationCategories:
    def test_returns_all_categories(self, generator: JTCComplaintGenerator) -> None:
        cats = generator.list_violation_categories()
        assert len(cats) == 8

    def test_each_category_has_required_keys(self, generator: JTCComplaintGenerator) -> None:
        for cat in generator.list_violation_categories():
            assert "type" in cat
            assert "canon" in cat
            assert "title" in cat
            assert "description" in cat

    def test_undisclosed_conflict_first(self, generator: JTCComplaintGenerator) -> None:
        cats = generator.list_violation_categories()
        assert cats[0]["type"] == "undisclosed_conflict"


# ---------------------------------------------------------------------------
# build_violation_section
# ---------------------------------------------------------------------------

class TestBuildViolationSection:
    def test_builds_valid_section(self, generator: JTCComplaintGenerator) -> None:
        section = generator.build_violation_section(
            "undisclosed_conflict",
            "Judge failed to disclose family connection.",
            ["Exhibit A"],
        )
        assert "Canon 3(C)(1)" in section
        assert "MCR 2.003(C)(1)(b)" in section
        assert "Judge failed to disclose" in section
        assert "Exhibit A" in section

    def test_invalid_type_raises(self, generator: JTCComplaintGenerator) -> None:
        with pytest.raises(ValueError, match="Invalid violation_type"):
            generator.build_violation_section("fake_type", "irrelevant")

    def test_section_without_evidence(self, generator: JTCComplaintGenerator) -> None:
        section = generator.build_violation_section(
            "bias_pattern",
            "Systematic favoritism in rulings.",
        )
        assert "bias" in section.lower() or "Impartiality" in section
        assert "Supporting Evidence" not in section

    def test_section_with_multiple_evidence(self, generator: JTCComplaintGenerator) -> None:
        section = generator.build_violation_section(
            "denial_of_due_process",
            "No hearing provided.",
            ["Exhibit A", "Exhibit B", "Exhibit C"],
        )
        assert "1. Exhibit A" in section
        assert "3. Exhibit C" in section


# ---------------------------------------------------------------------------
# generate_exhibit_list
# ---------------------------------------------------------------------------

class TestGenerateExhibitList:
    def test_generates_sequential_ids(
        self,
        generator: JTCComplaintGenerator,
        sample_evidence_refs: list[dict[str, str]],
    ) -> None:
        exhibits = generator.generate_exhibit_list(sample_evidence_refs)
        assert len(exhibits) == 3
        assert exhibits[0].exhibit_id == "Exhibit A"
        assert exhibits[1].exhibit_id == "Exhibit B"
        assert exhibits[2].exhibit_id == "Exhibit C"

    def test_preserves_metadata(
        self,
        generator: JTCComplaintGenerator,
        sample_evidence_refs: list[dict[str, str]],
    ) -> None:
        exhibits = generator.generate_exhibit_list(sample_evidence_refs)
        assert "Berry-McNeill" in exhibits[0].title
        assert exhibits[0].bates_range == "PIGORS-0001 to PIGORS-0015"

    def test_empty_refs_returns_empty(self, generator: JTCComplaintGenerator) -> None:
        assert generator.generate_exhibit_list([]) == []

    def test_handles_minimal_refs(self, generator: JTCComplaintGenerator) -> None:
        exhibits = generator.generate_exhibit_list([{"title": "Minimal"}])
        assert len(exhibits) == 1
        assert exhibits[0].description is None


# ---------------------------------------------------------------------------
# generate_cover_letter
# ---------------------------------------------------------------------------

class TestGenerateCoverLetter:
    def test_contains_complainant_info(self, generator: JTCComplaintGenerator) -> None:
        letter = generator.generate_cover_letter(violation_count=3)
        assert COMPLAINANT_INFO["name"] in letter
        assert COMPLAINANT_INFO["phone"] in letter

    def test_contains_jtc_address(self, generator: JTCComplaintGenerator) -> None:
        letter = generator.generate_cover_letter()
        assert "3034 W. Grand Blvd." in letter

    def test_contains_judge_name(self, generator: JTCComplaintGenerator) -> None:
        letter = generator.generate_cover_letter()
        assert SUBJECT_JUDGE_INFO["name"] in letter

    def test_contains_case_number(self, generator: JTCComplaintGenerator) -> None:
        letter = generator.generate_cover_letter()
        assert CASE_INFO["case_number"] in letter

    def test_violation_count_appears(self, generator: JTCComplaintGenerator) -> None:
        letter = generator.generate_cover_letter(violation_count=5)
        assert "5 violation(s)" in letter

    def test_contains_today_date(self, generator: JTCComplaintGenerator) -> None:
        letter = generator.generate_cover_letter()
        today = date.today().strftime("%B %d, %Y")
        assert today in letter


# ---------------------------------------------------------------------------
# analyze_pattern
# ---------------------------------------------------------------------------

class TestAnalyzePattern:
    def test_empty_violations(self, generator: JTCComplaintGenerator) -> None:
        result = generator.analyze_pattern([])
        assert result.violation_count == 0
        assert result.severity_score == 0.0

    def test_returns_correct_count(
        self,
        generator: JTCComplaintGenerator,
        sample_violations: list[JTCViolation],
    ) -> None:
        result = generator.analyze_pattern(sample_violations)
        assert result.violation_count == 3

    def test_date_range_computed(
        self,
        generator: JTCComplaintGenerator,
        sample_violations: list[JTCViolation],
    ) -> None:
        result = generator.analyze_pattern(sample_violations)
        assert "2024-01-15" in result.date_range
        assert "2024-07-15" in result.date_range

    def test_conflict_mentioned_in_pattern(
        self,
        generator: JTCComplaintGenerator,
        sample_violations: list[JTCViolation],
    ) -> None:
        result = generator.analyze_pattern(sample_violations)
        assert "Berry-McNeill" in result.pattern_description

    def test_escalation_timeline_ordered(
        self,
        generator: JTCComplaintGenerator,
        sample_violations: list[JTCViolation],
    ) -> None:
        result = generator.analyze_pattern(sample_violations)
        assert len(result.escalation_timeline) == 3
        assert result.escalation_timeline[0].startswith("2024-01-15")

    def test_single_violation_no_range(
        self,
        generator: JTCComplaintGenerator,
        conflict_violation: JTCViolation,
    ) -> None:
        result = generator.analyze_pattern([conflict_violation])
        assert result.violation_count == 1
        assert "2024-01-15" in result.date_range


# ---------------------------------------------------------------------------
# calculate_severity
# ---------------------------------------------------------------------------

class TestCalculateSeverity:
    def test_empty_returns_zero(self, generator: JTCComplaintGenerator) -> None:
        result = generator.calculate_severity([])
        assert result.total_score == 0.0
        assert result.risk_level == "low"

    def test_conflict_weighted_highest(
        self,
        generator: JTCComplaintGenerator,
        conflict_violation: JTCViolation,
    ) -> None:
        result = generator.calculate_severity([conflict_violation])
        expected = 10 * SEVERITY_WEIGHTS["undisclosed_conflict"]
        assert result.total_score == expected
        assert result.max_individual == 10

    def test_multiple_violations_sum(
        self,
        generator: JTCComplaintGenerator,
        sample_violations: list[JTCViolation],
    ) -> None:
        result = generator.calculate_severity(sample_violations)
        assert result.total_score > 0
        assert len(result.category_scores) == 3

    def test_critical_risk_level(
        self,
        generator: JTCComplaintGenerator,
        sample_violations: list[JTCViolation],
    ) -> None:
        result = generator.calculate_severity(sample_violations)
        # 10*1.5 + 8*1.2 + 9*1.3 = 15 + 9.6 + 11.7 = 36.3 → critical
        assert result.risk_level == "critical"

    def test_low_risk_level(self, generator: JTCComplaintGenerator) -> None:
        v = JTCViolation(
            violation_type="demeanor_violations",
            canon_violated="Canon 3(A)(3)",
            description="Minor",
            severity=1,
        )
        result = generator.calculate_severity([v])
        # 1 * 0.8 = 0.8
        assert result.risk_level == "low"


# ---------------------------------------------------------------------------
# validate_complaint
# ---------------------------------------------------------------------------

class TestValidateComplaint:
    def test_empty_text_invalid(self, generator: JTCComplaintGenerator) -> None:
        result = generator.validate_complaint("")
        assert result.is_valid is False
        assert "empty" in result.errors[0].lower()

    def test_valid_complaint_passes(
        self,
        generator: JTCComplaintGenerator,
        sample_violations: list[JTCViolation],
        sample_evidence_refs: list[dict[str, str]],
    ) -> None:
        complaint = generator.generate_complaint(
            sample_violations, sample_evidence_refs
        )
        result = generator.validate_complaint(complaint)
        assert result.is_valid is True
        assert len(result.errors) == 0

    def test_missing_sections_detected(self, generator: JTCComplaintGenerator) -> None:
        result = generator.validate_complaint("Some random text without structure")
        assert result.is_valid is False
        assert len(result.sections_missing) > 0

    def test_missing_case_number_error(self, generator: JTCComplaintGenerator) -> None:
        text = "COVER PAGE\nCOMPLAINANT INFORMATION\nSUBJECT JUDGE\n"
        result = generator.validate_complaint(text)
        assert any("Case number" in e for e in result.errors)


# ---------------------------------------------------------------------------
# get_jtc_contact_info
# ---------------------------------------------------------------------------

class TestGetJTCContactInfo:
    def test_returns_required_keys(self) -> None:
        info = JTCComplaintGenerator.get_jtc_contact_info()
        assert "address" in info
        assert "phone" in info
        assert "filing_method" in info
        assert "instructions" in info

    def test_address_correct(self) -> None:
        info = JTCComplaintGenerator.get_jtc_contact_info()
        assert "3034 W. Grand Blvd." in info["address"]
        assert "Detroit, MI 48202" in info["address"]


# ---------------------------------------------------------------------------
# generate_complaint (integration)
# ---------------------------------------------------------------------------

class TestGenerateComplaint:
    def test_requires_violations(self, generator: JTCComplaintGenerator) -> None:
        with pytest.raises(ValueError, match="At least one violation"):
            generator.generate_complaint([])

    def test_generates_complete_document(
        self,
        generator: JTCComplaintGenerator,
        sample_violations: list[JTCViolation],
        sample_evidence_refs: list[dict[str, str]],
    ) -> None:
        complaint = generator.generate_complaint(
            sample_violations, sample_evidence_refs
        )
        assert "COVER PAGE" in complaint
        assert "COMPLAINANT INFORMATION" in complaint
        assert "SUBJECT JUDGE" in complaint
        assert "FACTUAL ALLEGATIONS" in complaint
        assert "VIOLATIONS" in complaint
        assert "PRAYER FOR RELIEF" in complaint
        assert "VERIFICATION" in complaint

    def test_conflict_promoted_to_lead(
        self,
        generator: JTCComplaintGenerator,
        sample_violations: list[JTCViolation],
    ) -> None:
        complaint = generator.generate_complaint(sample_violations)
        # The undisclosed conflict description appears before bias/retaliation
        conflict_pos = complaint.find("Cavan Berry")
        bias_pos = complaint.find("systematically ruled")
        assert conflict_pos < bias_pos, (
            "Undisclosed conflict should be the lead violation"
        )

    def test_contains_verified_party_names(
        self,
        generator: JTCComplaintGenerator,
        sample_violations: list[JTCViolation],
    ) -> None:
        complaint = generator.generate_complaint(sample_violations)
        assert "Andrew James Pigors" in complaint
        assert "Hon. Jenny L. McNeill" in complaint
        assert "Emily A. Watson" in complaint

    def test_contains_penalty_of_perjury(
        self,
        generator: JTCComplaintGenerator,
        sample_violations: list[JTCViolation],
    ) -> None:
        complaint = generator.generate_complaint(sample_violations)
        assert "penalty of perjury" in complaint.lower()

    def test_contains_canon_citations(
        self,
        generator: JTCComplaintGenerator,
        sample_violations: list[JTCViolation],
    ) -> None:
        complaint = generator.generate_complaint(sample_violations)
        assert "Canon 3(C)(1)" in complaint
        assert "Canon 3(A)(5)" in complaint
        assert "Canon 2(A)" in complaint

    def test_contains_michigan_constitution_reference(
        self,
        generator: JTCComplaintGenerator,
        sample_violations: list[JTCViolation],
    ) -> None:
        complaint = generator.generate_complaint(sample_violations)
        assert "Michigan Constitution Art. 6" in complaint

    def test_contains_exhibit_list(
        self,
        generator: JTCComplaintGenerator,
        sample_violations: list[JTCViolation],
        sample_evidence_refs: list[dict[str, str]],
    ) -> None:
        complaint = generator.generate_complaint(
            sample_violations, sample_evidence_refs
        )
        assert "EXHIBIT LIST" in complaint
        assert "Exhibit A" in complaint

    def test_no_exhibits_when_no_refs(
        self,
        generator: JTCComplaintGenerator,
        sample_violations: list[JTCViolation],
    ) -> None:
        complaint = generator.generate_complaint(sample_violations)
        assert "EXHIBIT LIST" not in complaint

    def test_prayer_requests_disqualification(
        self,
        generator: JTCComplaintGenerator,
        sample_violations: list[JTCViolation],
    ) -> None:
        complaint = generator.generate_complaint(sample_violations)
        assert "disqualify" in complaint.lower()
        assert CASE_INFO["case_number"] in complaint

    def test_no_fabricated_names(
        self,
        generator: JTCComplaintGenerator,
        sample_violations: list[JTCViolation],
    ) -> None:
        """Verify no hallucinated names appear in generated output."""
        complaint = generator.generate_complaint(sample_violations)
        assert "Jane Berry" not in complaint
        assert "Patricia Berry" not in complaint
        assert "Amy McNeill" not in complaint
        assert "Tiffany" not in complaint
