"""Tests for the Michigan Court of Appeals Filing Form Library engine."""

from __future__ import annotations

from datetime import date, timedelta

import pytest

from litigationos.engines.coa_forms import (
    BRIEF_PAGE_LIMIT,
    COA_CASE_NUMBER,
    COA_COURT_NAME,
    COACaseInfo,
    COADeadline,
    COAFormLibrary,
    FILING_TYPES,
    LOWER_COURT_CASE_NUMBER,
    MCR_7212_REQUIRED_SECTIONS,
    PARTIES,
    REQUIRED_APPENDIX_ITEMS,
    STANDARDS_OF_REVIEW,
    BriefSection,
    BriefValidation,
    COABrief,
    COADocument,
    COAFilingType,
    COAMotion,
    AppendixItem,
    _coa_caption,
    _certificate_of_service,
    _is_business_day,
    _next_business_day,
    _signature_block,
)


# ============================================================================
# Fixtures
# ============================================================================


@pytest.fixture
def lib() -> COAFormLibrary:
    """Fresh COAFormLibrary instance."""
    return COAFormLibrary()


@pytest.fixture
def case_info() -> COACaseInfo:
    """Default case info for Pigors v. Watson."""
    return COACaseInfo()


@pytest.fixture
def sample_issues() -> list[str]:
    """Sample appellate issues."""
    return [
        "The trial court abused its discretion in modifying custody",
        "The trial court failed to make adequate best-interest findings",
        "The trial court failed to disclose a conflict of interest",
    ]


@pytest.fixture
def sample_arguments() -> list[dict[str, str]]:
    """Sample brief arguments with standards of review."""
    return [
        {
            "heading": "The Trial Court Abused Its Discretion",
            "content": "The trial court's custody modification lacked evidentiary support.",
            "standard_of_review": "abuse_of_discretion",
        },
        {
            "heading": "Best Interest Findings Were Inadequate",
            "content": "The court failed to address all 12 best-interest factors.",
            "standard_of_review": "great_weight",
        },
    ]


# ============================================================================
# Party identity — verified source of truth
# ============================================================================


class TestPartyIdentity:
    """Verify party identity constants match the single source of truth."""

    def test_appellant_name(self):
        assert PARTIES["appellant"]["name"] == "Andrew James Pigors"

    def test_appellee_name(self):
        assert PARTIES["appellee"]["name"] == "Emily A. Watson"

    def test_lower_court_judge(self):
        assert PARTIES["lower_court_judge"]["name"] == "Hon. Jenny L. McNeill"

    def test_child_initials(self):
        assert PARTIES["child"]["initials"] == "L.D.W."

    def test_case_numbers(self):
        assert LOWER_COURT_CASE_NUMBER == "2024-001507-DC"
        assert COA_CASE_NUMBER == "366810"


# ============================================================================
# Filing type registry
# ============================================================================


class TestFilingTypeRegistry:
    """Test the COA filing type registry."""

    def test_nine_filing_types_registered(self):
        assert len(FILING_TYPES) == 9

    def test_all_types_are_coa_filing_type(self):
        for ft in FILING_TYPES.values():
            assert isinstance(ft, COAFilingType)

    def test_claim_of_appeal_rule(self):
        ft = FILING_TYPES["claim_of_appeal"]
        assert ft.mcr_rule == "MCR 7.204"
        assert ft.deadline_days == 21
        assert ft.scao_form == "MC 229"
        assert ft.filing_fee == "$375.00"

    def test_leave_to_appeal_rule(self):
        ft = FILING_TYPES["leave_to_appeal"]
        assert ft.mcr_rule == "MCR 7.205"
        assert ft.deadline_days == 182
        assert ft.scao_form == "MC 230"

    def test_appellant_brief_rule(self):
        ft = FILING_TYPES["appellant_brief"]
        assert ft.mcr_rule == "MCR 7.212"
        assert ft.deadline_days == 56

    def test_reply_brief_rule(self):
        ft = FILING_TYPES["reply_brief"]
        assert ft.mcr_rule == "MCR 7.212(G)"
        assert ft.deadline_days == 21

    def test_motion_to_stay_rule(self):
        ft = FILING_TYPES["motion_to_stay"]
        assert ft.mcr_rule == "MCR 7.209"
        assert ft.deadline_days is None
        assert ft.filing_fee == "$0.00"

    def test_superintending_control_rule(self):
        ft = FILING_TYPES["superintending_control"]
        assert ft.mcr_rule == "MCR 7.206"
        assert ft.filing_fee == "$375.00"


# ============================================================================
# COAFormLibrary.list_filing_types
# ============================================================================


class TestListFilingTypes:
    """Test listing available filing types."""

    def test_returns_list_of_dicts(self, lib: COAFormLibrary):
        result = lib.list_filing_types()
        assert isinstance(result, list)
        assert len(result) == 9
        for item in result:
            assert isinstance(item, dict)
            assert "key" in item
            assert "name" in item
            assert "mcr_rule" in item

    def test_keys_present(self, lib: COAFormLibrary):
        keys = {item["key"] for item in lib.list_filing_types()}
        assert "claim_of_appeal" in keys
        assert "leave_to_appeal" in keys
        assert "appellant_brief" in keys
        assert "reply_brief" in keys
        assert "motion_to_stay" in keys


# ============================================================================
# Claim of Appeal
# ============================================================================


class TestClaimOfAppeal:
    """Test Claim of Appeal generation."""

    def test_generates_document(self, lib: COAFormLibrary, sample_issues):
        doc = lib.generate_claim_of_appeal(issues=sample_issues)
        assert isinstance(doc, COADocument)
        assert doc.document_type == "claim_of_appeal"
        assert doc.scao_form == "MC 229"

    def test_caption_contains_court_name(self, lib: COAFormLibrary):
        doc = lib.generate_claim_of_appeal()
        assert "MICHIGAN COURT OF APPEALS" in doc.caption

    def test_caption_contains_case_numbers(self, lib: COAFormLibrary):
        doc = lib.generate_claim_of_appeal()
        assert LOWER_COURT_CASE_NUMBER in doc.caption
        assert COA_CASE_NUMBER in doc.caption

    def test_body_has_jurisdiction_section(self, lib: COAFormLibrary):
        doc = lib.generate_claim_of_appeal()
        assert "Basis for Jurisdiction" in doc.body_sections
        assert "MCR 7.203(A)" in doc.body_sections["Basis for Jurisdiction"]

    def test_issues_listed(self, lib: COAFormLibrary, sample_issues):
        doc = lib.generate_claim_of_appeal(issues=sample_issues)
        text = doc.body_sections["Issues on Appeal"]
        for issue in sample_issues:
            assert issue in text

    def test_order_date_included(self, lib: COAFormLibrary):
        doc = lib.generate_claim_of_appeal(order_date="2025-03-15")
        assert "2025-03-15" in doc.body_sections["Order Appealed"]

    def test_has_signature_and_service(self, lib: COAFormLibrary):
        doc = lib.generate_claim_of_appeal()
        assert "Andrew James Pigors" in doc.signature_block
        assert "CERTIFICATE OF SERVICE" in doc.certificate_of_service.upper()

    def test_full_text_property(self, lib: COAFormLibrary, sample_issues):
        doc = lib.generate_claim_of_appeal(issues=sample_issues)
        text = doc.full_text
        assert "MICHIGAN COURT OF APPEALS" in text
        assert "CLAIM OF APPEAL" in text
        assert "Respectfully submitted" in text


# ============================================================================
# Leave to Appeal
# ============================================================================


class TestLeaveApplication:
    """Test Application for Leave to Appeal generation."""

    def test_generates_document(self, lib: COAFormLibrary, sample_issues):
        doc = lib.generate_leave_application(issues=sample_issues)
        assert isinstance(doc, COADocument)
        assert doc.document_type == "leave_to_appeal"
        assert doc.scao_form == "MC 230"

    def test_custom_why_leave(self, lib: COAFormLibrary):
        reason = "The lower court violated MCR 2.003 by failing to disclose."
        doc = lib.generate_leave_application(why_leave=reason)
        assert reason in doc.body_sections["Reasons Leave Should Be Granted"]

    def test_default_why_leave(self, lib: COAFormLibrary):
        doc = lib.generate_leave_application()
        section = doc.body_sections["Reasons Leave Should Be Granted"]
        assert "significant legal errors" in section


# ============================================================================
# Docketing Statement
# ============================================================================


class TestDocketingStatement:
    """Test Docketing Statement generation."""

    def test_generates_document(self, lib: COAFormLibrary):
        doc = lib.generate_docketing_statement()
        assert isinstance(doc, COADocument)
        assert doc.document_type == "docketing_statement"
        assert doc.scao_form == "MC 231"

    def test_contains_party_info(self, lib: COAFormLibrary):
        doc = lib.generate_docketing_statement()
        assert "Andrew James Pigors" in doc.body_sections["Appellant Information"]
        assert "Emily A. Watson" in doc.body_sections["Appellee Information"]

    def test_contains_lower_court_info(self, lib: COAFormLibrary):
        doc = lib.generate_docketing_statement()
        info = doc.body_sections["Lower Court Information"]
        assert "14th Circuit Court" in info
        assert "Jenny L. McNeill" in info
        assert LOWER_COURT_CASE_NUMBER in info


# ============================================================================
# Brief generation
# ============================================================================


class TestBriefGeneration:
    """Test appellate brief generation per MCR 7.212."""

    def test_generates_appellant_brief(
        self, lib: COAFormLibrary, sample_issues, sample_arguments
    ):
        brief = lib.generate_brief(
            "appellant_brief",
            issues=sample_issues,
            arguments=sample_arguments,
        )
        assert isinstance(brief, COABrief)
        assert brief.brief_type == "appellant_brief"

    def test_generates_reply_brief(self, lib: COAFormLibrary):
        brief = lib.generate_brief("reply_brief")
        assert brief.brief_type == "reply_brief"

    def test_invalid_brief_type_raises(self, lib: COAFormLibrary):
        with pytest.raises(ValueError, match="Unknown brief_type"):
            lib.generate_brief("fantasy_brief")

    def test_brief_has_required_sections(
        self, lib: COAFormLibrary, sample_issues, sample_arguments
    ):
        brief = lib.generate_brief(
            "appellant_brief",
            issues=sample_issues,
            arguments=sample_arguments,
        )
        text = brief.full_text
        assert "TABLE OF CONTENTS" in text
        assert "INDEX OF AUTHORITIES" in text
        assert "STATEMENT OF JURISDICTION" in text
        assert "STATEMENT OF QUESTIONS PRESENTED" in text
        assert "STATEMENT OF FACTS" in text
        assert "RELIEF REQUESTED" in text

    def test_arguments_include_standard_of_review(
        self, lib: COAFormLibrary, sample_arguments
    ):
        brief = lib.generate_brief("appellant_brief", arguments=sample_arguments)
        text = brief.full_text
        assert "abuse of discretion" in text.lower()
        assert "great weight" in text.lower()

    def test_authorities_in_index(self, lib: COAFormLibrary):
        authorities = [
            "Vodvarka v Grasmeyer, 259 Mich App 499 (2003)",
            "Maldonado v Ford Motor Co, 476 Mich 372 (2006)",
        ]
        brief = lib.generate_brief(
            "appellant_brief", authorities=authorities
        )
        assert "Maldonado" in brief.index_of_authorities
        assert "Vodvarka" in brief.index_of_authorities

    def test_appendix_contents_populated(self, lib: COAFormLibrary):
        brief = lib.generate_brief("appellant_brief")
        assert len(brief.appendix_contents) == len(REQUIRED_APPENDIX_ITEMS)

    def test_full_text_contains_caption(self, lib: COAFormLibrary):
        brief = lib.generate_brief("appellant_brief")
        assert "MICHIGAN COURT OF APPEALS" in brief.full_text


# ============================================================================
# Motion generation
# ============================================================================


class TestMotionGeneration:
    """Test COA motion generation."""

    def test_generates_motion_to_stay(self, lib: COAFormLibrary):
        motion = lib.generate_motion(
            "motion_to_stay",
            grounds=["Likelihood of success on the merits"],
        )
        assert isinstance(motion, COAMotion)
        assert motion.motion_type == "motion_to_stay"
        assert "MCR 7.209" in motion.full_text

    def test_generates_peremptory_reversal(self, lib: COAFormLibrary):
        motion = lib.generate_motion(
            "motion_for_peremptory_reversal",
            grounds=["Clear legal error in custody modification"],
        )
        assert motion.motion_type == "motion_for_peremptory_reversal"
        assert "MCR 7.211(C)(4)" in motion.full_text

    def test_generates_superintending_control(self, lib: COAFormLibrary):
        motion = lib.generate_motion(
            "superintending_control",
            grounds=["Lower court failed to disclose conflict of interest"],
        )
        assert motion.motion_type == "superintending_control"
        assert "MCR 7.206" in motion.full_text

    def test_invalid_motion_type_raises(self, lib: COAFormLibrary):
        with pytest.raises(ValueError, match="Unknown motion_type"):
            lib.generate_motion("motion_to_dance")

    def test_motion_has_relief(self, lib: COAFormLibrary):
        motion = lib.generate_motion("motion_to_stay")
        assert len(motion.relief_requested) >= 1
        assert "RELIEF REQUESTED" in motion.full_text


# ============================================================================
# Appendix generation
# ============================================================================


class TestAppendixGeneration:
    """Test appendix generation per MCR 7.212(H)."""

    def test_required_items_present(self, lib: COAFormLibrary):
        appendix = lib.generate_appendix()
        assert len(appendix) == len(REQUIRED_APPENDIX_ITEMS)
        labels = [item["label"] for item in appendix]
        assert "a" in labels
        assert "b" in labels

    def test_additional_documents(self, lib: COAFormLibrary):
        extra = [{"description": "Transcript of custody hearing"}]
        appendix = lib.generate_appendix(documents=extra)
        assert len(appendix) == len(REQUIRED_APPENDIX_ITEMS) + 1
        assert appendix[-1]["description"] == "Transcript of custody hearing"


# ============================================================================
# Brief validation
# ============================================================================


class TestBriefValidation:
    """Test brief validation against MCR 7.212."""

    def test_compliant_brief(self, lib: COAFormLibrary, sample_arguments):
        brief = lib.generate_brief(
            "appellant_brief",
            issues=["Issue one"],
            arguments=sample_arguments,
        )
        result = lib.validate_brief(brief.full_text)
        assert isinstance(result, BriefValidation)
        assert result.is_compliant is True
        assert len(result.issues) == 0

    def test_missing_section_flagged(self, lib: COAFormLibrary):
        incomplete = "This brief has no required sections at all."
        result = lib.validate_brief(incomplete)
        assert result.is_compliant is False
        assert len(result.issues) > 0
        assert any("Missing required section" in i for i in result.issues)

    def test_checklist_populated(self, lib: COAFormLibrary):
        result = lib.validate_brief("Nothing here.")
        assert len(result.mcr_7212_checklist) > 0
        for section in MCR_7212_REQUIRED_SECTIONS:
            assert section in result.mcr_7212_checklist

    def test_page_count_estimated(self, lib: COAFormLibrary):
        # ~250 words per page, so 500 words ≈ 2 pages
        text = "word " * 500
        text += "\n".join(
            f"## {s}" for s in MCR_7212_REQUIRED_SECTIONS
        )
        text += "\nRespectfully submitted\nCertificate of Service"
        result = lib.validate_brief(text)
        assert result.page_count >= 1

    def test_overlength_brief_flagged(self, lib: COAFormLibrary):
        # Simulate a 60-page brief (~15000 words)
        text = "word " * 15000
        result = lib.validate_brief(text)
        assert any("page limit" in i.lower() for i in result.issues)


# ============================================================================
# Required documents checklist
# ============================================================================


class TestRequiredDocuments:
    """Test required documents lookup."""

    def test_claim_of_appeal_docs(self, lib: COAFormLibrary):
        docs = lib.get_required_documents("claim_of_appeal")
        assert isinstance(docs, list)
        assert len(docs) >= 4
        assert any("MC 229" in d for d in docs)
        assert any("MC 231" in d for d in docs)

    def test_invalid_filing_type_raises(self, lib: COAFormLibrary):
        with pytest.raises(ValueError, match="Unknown filing_type"):
            lib.get_required_documents("nonexistent_type")

    def test_leave_to_appeal_docs(self, lib: COAFormLibrary):
        docs = lib.get_required_documents("leave_to_appeal")
        assert any("MC 230" in d for d in docs)


# ============================================================================
# Deadline calculation
# ============================================================================


class TestDeadlineCalculation:
    """Test COA deadline calculation."""

    def test_returns_list_of_deadlines(self, lib: COAFormLibrary):
        deadlines = lib.calculate_deadlines(date(2025, 3, 15))
        assert isinstance(deadlines, list)
        assert len(deadlines) >= 4  # at least claim, leave, brief, reply

    def test_deadlines_are_sorted(self, lib: COAFormLibrary):
        deadlines = lib.calculate_deadlines(date(2025, 3, 15))
        dates = [d.deadline_date for d in deadlines]
        assert dates == sorted(dates)

    def test_claim_21_day_deadline(self, lib: COAFormLibrary):
        order_date = date(2025, 6, 2)  # Monday
        deadlines = lib.calculate_deadlines(order_date)
        claim = next(d for d in deadlines if d.filing_type == "claim_of_appeal")
        expected = order_date + timedelta(days=21)
        assert claim.deadline_date == _next_business_day(expected)
        assert claim.mcr_rule == "MCR 7.204"

    def test_leave_182_day_deadline(self, lib: COAFormLibrary):
        order_date = date(2025, 1, 1)
        deadlines = lib.calculate_deadlines(order_date)
        leave = next(d for d in deadlines if d.filing_type == "leave_to_appeal")
        expected = order_date + timedelta(days=182)
        assert leave.deadline_date == _next_business_day(expected)

    def test_expired_deadline_flagged(self, lib: COAFormLibrary):
        old_date = date(2020, 1, 1)
        deadlines = lib.calculate_deadlines(old_date)
        assert all(d.is_expired for d in deadlines)

    def test_string_date_accepted(self, lib: COAFormLibrary):
        deadlines = lib.calculate_deadlines("2025-06-01")
        assert len(deadlines) >= 1

    def test_weekend_adjusted(self, lib: COAFormLibrary):
        # 2025-06-07 is a Saturday; 21 days later = 2025-06-28 (Saturday)
        deadlines = lib.calculate_deadlines(date(2025, 6, 7))
        for d in deadlines:
            assert d.deadline_date.weekday() < 5  # must be weekday


# ============================================================================
# Helper functions
# ============================================================================


class TestHelpers:
    """Test helper functions."""

    def test_is_business_day_weekday(self):
        assert _is_business_day(date(2025, 6, 2)) is True  # Monday

    def test_is_business_day_weekend(self):
        assert _is_business_day(date(2025, 6, 7)) is False  # Saturday
        assert _is_business_day(date(2025, 6, 8)) is False  # Sunday

    def test_next_business_day_already_weekday(self):
        monday = date(2025, 6, 2)
        assert _next_business_day(monday) == monday

    def test_next_business_day_from_saturday(self):
        saturday = date(2025, 6, 7)
        assert _next_business_day(saturday) == date(2025, 6, 9)  # Monday

    def test_caption_format(self):
        ci = COACaseInfo()
        caption = _coa_caption(ci, "Test Document")
        assert "MICHIGAN COURT OF APPEALS" in caption
        assert "Andrew James Pigors" in caption
        assert "Emily A. Watson" in caption
        assert "TEST DOCUMENT" in caption

    def test_signature_block_contents(self):
        sig = _signature_block()
        assert "Andrew James Pigors" in sig
        assert "Pro Se Appellant" in sig
        assert "(231) 903-5690" in sig

    def test_certificate_of_service_contents(self):
        ci = COACaseInfo()
        cos = _certificate_of_service(ci)
        assert "Emily A. Watson" in cos
        assert "Andrew James Pigors" in cos


# ============================================================================
# Pydantic model tests
# ============================================================================


class TestPydanticModels:
    """Test Pydantic model creation and serialization."""

    def test_coa_case_info_defaults(self):
        ci = COACaseInfo()
        assert ci.lower_court_case_number == "2024-001507-DC"
        assert ci.appellant == "Andrew James Pigors"
        assert ci.appellee == "Emily A. Watson"

    def test_coa_filing_type_frozen(self):
        ft = FILING_TYPES["claim_of_appeal"]
        with pytest.raises(Exception):
            ft.name = "Modified"  # type: ignore[misc]

    def test_coa_deadline_model(self):
        d = COADeadline(
            filing_type="claim_of_appeal",
            trigger_date=date(2025, 1, 1),
            deadline_date=date(2025, 1, 22),
            days_remaining=21,
            is_expired=False,
            mcr_rule="MCR 7.204",
        )
        assert d.filing_type == "claim_of_appeal"
        assert d.is_expired is False

    def test_brief_validation_model(self):
        bv = BriefValidation(
            is_compliant=False,
            page_count=55,
            issues=["Too long"],
            mcr_7212_checklist={"Table of Contents": True},
        )
        assert bv.is_compliant is False
        assert bv.page_count == 55

    def test_brief_section_model(self):
        bs = BriefSection(
            heading="Test",
            content="Content here.",
            standard_of_review="De novo",
        )
        assert bs.heading == "Test"

    def test_appendix_item_model(self):
        ai = AppendixItem(label="a", description="Register of actions")
        assert ai.required is True

    def test_coa_document_serialization(self):
        doc = COADocument(
            document_type="claim_of_appeal",
            case_info=COACaseInfo(),
            caption="Test caption",
            body_sections={"Section": "Content"},
            signature_block="Sig",
            certificate_of_service="COS",
        )
        data = doc.model_dump()
        assert data["document_type"] == "claim_of_appeal"


# ============================================================================
# Standards of review
# ============================================================================


class TestStandardsOfReview:
    """Test standards of review constants."""

    def test_four_standards_defined(self):
        assert len(STANDARDS_OF_REVIEW) == 4

    def test_de_novo_present(self):
        assert "de_novo" in STANDARDS_OF_REVIEW
        assert "de novo" in STANDARDS_OF_REVIEW["de_novo"].lower()

    def test_abuse_of_discretion_present(self):
        assert "abuse_of_discretion" in STANDARDS_OF_REVIEW

    def test_clear_error_present(self):
        assert "clear_error" in STANDARDS_OF_REVIEW

    def test_great_weight_present(self):
        assert "great_weight" in STANDARDS_OF_REVIEW
        assert "Vodvarka" in STANDARDS_OF_REVIEW["great_weight"]
