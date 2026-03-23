"""Comprehensive test suite for the MotionFormLibrary engine.

Covers motion type listing, all generation methods (motion / response / reply /
order), validation, template access, required forms, edge cases, and Pydantic
model behaviour.  At least 20 tests.
"""

from __future__ import annotations

import pytest

from litigationos.engines.motion_forms import (
    BEST_INTEREST_FACTORS,
    MOTION_TYPES,
    PARTIES,
    CaseInfo,
    MotionDocument,
    MotionFormLibrary,
    MotionType,
    MotionValidation,
    _build_caption,
    _build_certificate_of_service,
    _build_signature_block,
)


# -- Fixtures ----------------------------------------------------------------


@pytest.fixture
def lib() -> MotionFormLibrary:
    """Return a MotionFormLibrary with default case info."""
    return MotionFormLibrary()


@pytest.fixture
def custom_case() -> CaseInfo:
    """Return a custom CaseInfo for override tests."""
    return CaseInfo(
        case_number="2025-999999-FC",
        plaintiff="Andrew James Pigors",
        defendant="Emily A. Watson",
        judge="Hon. Jenny L. McNeill",
    )


# -- 1. Listing motion types ------------------------------------------------


def test_list_motion_types_returns_all(lib: MotionFormLibrary) -> None:
    types = lib.list_motion_types()
    assert len(types) == len(MOTION_TYPES)
    keys = {t["key"] for t in types}
    assert keys == set(MOTION_TYPES.keys())


def test_list_motion_types_has_required_fields(lib: MotionFormLibrary) -> None:
    for entry in lib.list_motion_types():
        for field in ("key", "name", "mcr_rule", "description", "required_sections", "scao_forms", "filing_fee"):
            assert field in entry, f"Missing field '{field}' in {entry['key']}"


def test_list_motion_types_thirteen_entries(lib: MotionFormLibrary) -> None:
    assert len(lib.list_motion_types()) == 13


# -- 2. get_motion_template --------------------------------------------------


def test_get_template_returns_motion_type(lib: MotionFormLibrary) -> None:
    mt = lib.get_motion_template("motion_to_show_cause")
    assert isinstance(mt, MotionType)
    assert mt.mcr_rule == "MCR 3.208"


def test_get_template_unknown_raises(lib: MotionFormLibrary) -> None:
    with pytest.raises(KeyError, match="Unknown motion type"):
        lib.get_motion_template("nonexistent_motion")


# -- 3. get_required_forms ---------------------------------------------------


def test_get_required_forms_show_cause(lib: MotionFormLibrary) -> None:
    forms = lib.get_required_forms("motion_to_show_cause")
    assert "FOC 1" in forms
    assert isinstance(forms, list)


def test_get_required_forms_empty_for_some(lib: MotionFormLibrary) -> None:
    # All motion types should have at least MC 416
    for key in MOTION_TYPES:
        forms = lib.get_required_forms(key)
        assert isinstance(forms, list)


# -- 4. generate_motion — basic structure ------------------------------------


def test_generate_motion_returns_document(lib: MotionFormLibrary) -> None:
    doc = lib.generate_motion("motion_to_show_cause")
    assert isinstance(doc, MotionDocument)
    assert doc.motion_type == "motion_to_show_cause"


def test_generate_motion_has_caption(lib: MotionFormLibrary) -> None:
    doc = lib.generate_motion("motion_to_show_cause")
    assert "STATE OF MICHIGAN" in doc.caption
    assert "2024-001507-DC" in doc.caption


def test_generate_motion_has_plaintiff_defendant(lib: MotionFormLibrary) -> None:
    doc = lib.generate_motion("motion_to_show_cause")
    text = doc.body_text
    assert "ANDREW JAMES PIGORS" in text
    assert "EMILY A. WATSON" in text


def test_generate_motion_has_signature_block(lib: MotionFormLibrary) -> None:
    doc = lib.generate_motion("motion_to_show_cause")
    assert "Pro Se Plaintiff" in doc.signature_block
    assert "(231) 903-5690" in doc.signature_block
    assert "andrewjpigors@gmail.com" in doc.signature_block


def test_generate_motion_has_certificate_of_service(lib: MotionFormLibrary) -> None:
    doc = lib.generate_motion("motion_to_show_cause")
    assert "CERTIFICATE OF SERVICE" in doc.certificate_of_service
    assert "Emily A. Watson" in doc.certificate_of_service
    assert "MCR 2.107" in doc.certificate_of_service


def test_generate_motion_with_arguments(lib: MotionFormLibrary) -> None:
    doc = lib.generate_motion(
        "motion_to_show_cause",
        arguments=["Defendant denied parenting time on March 15, 2024."],
        relief_requested=["Hold Defendant in contempt of court."],
    )
    text = doc.body_text
    assert "March 15, 2024" in text
    assert "contempt" in text.lower()


# -- 5. generate_motion — specific motion types ------------------------------


def test_generate_custody_has_best_interest(lib: MotionFormLibrary) -> None:
    doc = lib.generate_motion("motion_to_change_custody")
    text = doc.body_text
    assert "MCL 722.23" in text
    assert "best interest" in text.lower()


def test_generate_discovery_has_good_faith(lib: MotionFormLibrary) -> None:
    doc = lib.generate_motion("motion_to_compel_discovery")
    text = doc.body_text
    assert "good faith" in text.lower()
    assert "MCR 2.313" in text


def test_generate_emergency_has_verification(lib: MotionFormLibrary) -> None:
    doc = lib.generate_motion("emergency_motion")
    assert "Verification" in doc.body_sections
    assert "penalties of perjury" in doc.body_sections["Verification"]


def test_generate_disqualification_has_affidavit(lib: MotionFormLibrary) -> None:
    doc = lib.generate_motion("motion_for_disqualification")
    assert "Affidavit of Bias" in doc.body_sections
    assert "MCR 2.003" in doc.body_text


def test_generate_stay_has_irreparable_harm(lib: MotionFormLibrary) -> None:
    doc = lib.generate_motion("motion_for_stay")
    assert "Irreparable Harm" in doc.body_sections
    assert "Likelihood of Success on Appeal" in doc.body_sections


# -- 6. generate_response ---------------------------------------------------


def test_generate_response_opposition(lib: MotionFormLibrary) -> None:
    doc = lib.generate_response(
        "motion_for_sanctions",
        counter_arguments=["Plaintiff's filings were not frivolous."],
    )
    assert isinstance(doc, MotionDocument)
    assert "RESPONSE TO DEFENDANT'S" in doc.caption.upper()
    assert "Deny Defendant's" in doc.relief_requested[0]


def test_generate_response_has_standard_structure(lib: MotionFormLibrary) -> None:
    doc = lib.generate_response("motion_to_show_cause")
    text = doc.body_text
    assert "CERTIFICATE OF SERVICE" in text
    assert "Respectfully submitted" in text


# -- 7. generate_reply ------------------------------------------------------


def test_generate_reply_brief(lib: MotionFormLibrary) -> None:
    doc = lib.generate_reply(
        "motion_to_compel_discovery",
        reply_points=["Defendant's objections are meritless."],
    )
    assert isinstance(doc, MotionDocument)
    assert "REPLY BRIEF" in doc.caption.upper()
    assert "meritless" in doc.body_text


# -- 8. generate_order ------------------------------------------------------


def test_generate_order_has_judge_signature(lib: MotionFormLibrary) -> None:
    doc = lib.generate_order("motion_to_show_cause")
    assert "IT IS SO ORDERED" in doc.signature_block
    assert "Jenny L. McNeill" in doc.signature_block


def test_generate_order_custom_ruling(lib: MotionFormLibrary) -> None:
    ruling = "Defendant is held in contempt.  Defendant shall pay $500 in sanctions."
    doc = lib.generate_order("motion_to_show_cause", ruling=ruling)
    assert "contempt" in doc.body_text.lower()
    assert "$500" in doc.body_text


# -- 9. validate_motion -----------------------------------------------------


def test_validate_complete_motion(lib: MotionFormLibrary) -> None:
    doc = lib.generate_motion(
        "motion_to_show_cause",
        arguments=["Defendant violated the custody order."],
        relief_requested=["Hold Defendant in contempt."],
    )
    result = lib.validate_motion(doc.body_text)
    assert isinstance(result, MotionValidation)
    assert result.is_valid is True
    assert result.mcr_compliance_score > 70.0
    assert len(result.missing_sections) == 0


def test_validate_empty_text(lib: MotionFormLibrary) -> None:
    result = lib.validate_motion("")
    assert result.is_valid is False
    assert len(result.missing_sections) > 0
    assert result.mcr_compliance_score == 0.0


def test_validate_partial_document(lib: MotionFormLibrary) -> None:
    partial = "STATE OF MICHIGAN\nCase No. 2024-001507-DC\nANDREW JAMES PIGORS"
    result = lib.validate_motion(partial)
    assert result.is_valid is False
    assert result.mcr_compliance_score > 0.0


# -- 10. Custom case_info override -------------------------------------------


def test_custom_case_info_in_caption(
    lib: MotionFormLibrary, custom_case: CaseInfo
) -> None:
    doc = lib.generate_motion("motion_to_show_cause", case_info=custom_case)
    assert "2025-999999-FC" in doc.caption


# -- 11. Pydantic model tests -----------------------------------------------


def test_case_info_defaults() -> None:
    ci = CaseInfo()
    assert ci.case_number == "2024-001507-DC"
    assert ci.plaintiff == "Andrew James Pigors"
    assert ci.defendant == "Emily A. Watson"


def test_motion_type_frozen() -> None:
    mt = MOTION_TYPES["motion_to_show_cause"]
    with pytest.raises(Exception):
        mt.name = "Something Else"  # type: ignore[misc]


def test_motion_document_body_text() -> None:
    doc = MotionDocument(
        motion_type="test",
        case_info=CaseInfo(),
        caption="# TEST CAPTION",
        body_sections={"Section One": "Content here."},
        relief_requested=["Grant relief."],
        signature_block="Signed",
        certificate_of_service="Cert",
    )
    text = doc.body_text
    assert "TEST CAPTION" in text
    assert "SECTION ONE" in text
    assert "RELIEF REQUESTED" in text
    assert "Signed" in text
    assert "Cert" in text


def test_motion_validation_model() -> None:
    v = MotionValidation(
        is_valid=False,
        missing_sections=["Caption"],
        warnings=["No date"],
        mcr_compliance_score=50.0,
    )
    assert not v.is_valid
    assert v.mcr_compliance_score == 50.0


# -- 12. Helper function tests -----------------------------------------------


def test_build_caption_has_court_info() -> None:
    ci = CaseInfo()
    caption = _build_caption(ci)
    assert "14TH CIRCUIT COURT" in caption
    assert "MUSKEGON COUNTY" in caption
    assert "FAMILY DIVISION" in caption


def test_build_signature_block_has_party_info() -> None:
    sig = _build_signature_block("January 1, 2025")
    assert "Andrew James Pigors" in sig
    assert "January 1, 2025" in sig


def test_build_certificate_has_defendant() -> None:
    cert = _build_certificate_of_service()
    assert "Emily A. Watson" in cert
    assert "Pamela Rusco" in cert


# -- 13. All motion types generate without error -----------------------------


@pytest.mark.parametrize("motion_key", list(MOTION_TYPES.keys()))
def test_generate_every_motion_type(
    lib: MotionFormLibrary, motion_key: str
) -> None:
    """Every registered motion type generates a valid MotionDocument."""
    doc = lib.generate_motion(motion_key)
    assert isinstance(doc, MotionDocument)
    assert doc.motion_type == motion_key
    assert "STATE OF MICHIGAN" in doc.caption
    # Validate it
    result = lib.validate_motion(doc.body_text)
    assert result.mcr_compliance_score >= 50.0


# -- 14. Identity safety — never fabricate names ----------------------------


def test_no_fabricated_names() -> None:
    """Verify no hallucinated names appear in constants."""
    lib = MotionFormLibrary()
    for key in MOTION_TYPES:
        doc = lib.generate_motion(key)
        text = doc.body_text
        assert "Jane Berry" not in text
        assert "Patricia Berry" not in text
        assert "Tiffany" not in text
        assert "Amy McNeill" not in text


def test_child_initials_only() -> None:
    """Child must be referenced by initials only (MCR 8.119(H))."""
    ci = CaseInfo()
    assert ci.child_initials == "L.D.W."
