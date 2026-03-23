"""Tests for the 42 U.S.C. § 1983 Civil Rights Complaint Generator."""

from __future__ import annotations

from datetime import date, timedelta

import pytest

from litigationos.engines.section1983_generator import (
    CLAIM_DEFINITIONS,
    CONSTITUTIONAL_BASES,
    FEDERAL_COURT,
    MICHIGAN_SOL_YEARS,
    PARTIES,
    ClaimType,
    ComplaintDocument,
    DamagesCalculation,
    DomesticRelationsAnalysis,
    QualifiedImmunityAnalysis,
    SOLResult,
    Section1983Claim,
    Section1983Generator,
    _roman,
)


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def gen() -> Section1983Generator:
    """Create a generator instance without a DB connection."""
    return Section1983Generator(db=None)


@pytest.fixture
def sample_claim() -> Section1983Claim:
    return Section1983Claim(
        claim_type="due_process_substantive",
        constitutional_basis="fourteenth_due_process_substantive",
        elements=CLAIM_DEFINITIONS["due_process_substantive"]["elements"],
        facts=[
            "The court terminated parenting time without a hearing.",
            "Plaintiff was not provided notice of the modification.",
        ],
        defendants=["Hon. Jenny L. McNeill"],
        key_authority=CLAIM_DEFINITIONS["due_process_substantive"]["key_authority"],
    )


@pytest.fixture
def sample_defendants() -> list[str]:
    return ["Hon. Jenny L. McNeill", "Pamela Rusco"]


@pytest.fixture
def sample_facts() -> list[str]:
    return [
        "Plaintiff is the biological father of L.D.W.",
        "On or about January 15, 2024, Plaintiff filed a motion for "
        "parenting time modification.",
        "The court denied the motion without a hearing.",
        "Plaintiff was not provided notice of the denial.",
    ]


# ---------------------------------------------------------------------------
# 1. Verified party identity
# ---------------------------------------------------------------------------

class TestPartyIdentity:
    def test_plaintiff_name(self) -> None:
        assert PARTIES["plaintiff"] == "Andrew James Pigors"

    def test_defendant_name(self) -> None:
        assert PARTIES["defendant_watson"] == "Emily A. Watson"

    def test_judge_name(self) -> None:
        assert PARTIES["judge"] == "Hon. Jenny L. McNeill"

    def test_child_initials_only(self) -> None:
        assert PARTIES["child"] == "L.D.W."

    def test_state_case_number(self) -> None:
        assert PARTIES["state_case_number"] == "2024-001507-DC"


# ---------------------------------------------------------------------------
# 2. Claim definitions
# ---------------------------------------------------------------------------

class TestClaimDefinitions:
    def test_all_six_claim_types_defined(self) -> None:
        expected = {
            "due_process_substantive",
            "due_process_procedural",
            "first_amendment_retaliation",
            "equal_protection",
            "conspiracy_1983",
            "failure_to_intervene",
        }
        assert set(CLAIM_DEFINITIONS.keys()) == expected

    def test_each_claim_has_elements(self) -> None:
        for key, defn in CLAIM_DEFINITIONS.items():
            assert "elements" in defn, f"{key} missing elements"
            assert len(defn["elements"]) >= 2, f"{key} needs ≥2 elements"

    def test_each_claim_has_authority(self) -> None:
        for key, defn in CLAIM_DEFINITIONS.items():
            assert "key_authority" in defn, f"{key} missing authority"
            assert len(defn["key_authority"]) >= 1, f"{key} needs ≥1 authority"

    def test_claim_type_enum_matches_definitions(self) -> None:
        for ct in ClaimType:
            assert ct.value in CLAIM_DEFINITIONS


# ---------------------------------------------------------------------------
# 3. generate_complaint
# ---------------------------------------------------------------------------

class TestGenerateComplaint:
    def test_returns_complaint_document(
        self, gen: Section1983Generator, sample_claim: Section1983Claim,
        sample_defendants: list[str], sample_facts: list[str],
    ) -> None:
        doc = gen.generate_complaint([sample_claim], sample_defendants, sample_facts)
        assert isinstance(doc, ComplaintDocument)

    def test_caption_contains_court(
        self, gen: Section1983Generator, sample_claim: Section1983Claim,
        sample_defendants: list[str], sample_facts: list[str],
    ) -> None:
        doc = gen.generate_complaint([sample_claim], sample_defendants, sample_facts)
        assert "WESTERN DISTRICT OF MICHIGAN" in doc.caption

    def test_caption_contains_1983(
        self, gen: Section1983Generator, sample_claim: Section1983Claim,
        sample_defendants: list[str], sample_facts: list[str],
    ) -> None:
        doc = gen.generate_complaint([sample_claim], sample_defendants, sample_facts)
        assert "42 U.S.C. § 1983" in doc.caption

    def test_full_text_contains_all_sections(
        self, gen: Section1983Generator, sample_claim: Section1983Claim,
        sample_defendants: list[str], sample_facts: list[str],
    ) -> None:
        doc = gen.generate_complaint([sample_claim], sample_defendants, sample_facts)
        full = doc.full_text
        assert "JURISDICTION AND VENUE" in full
        assert "PARTIES" in full
        assert "FACTUAL BACKGROUND" in full
        assert "COUNT I" in full
        assert "PRAYER FOR RELIEF" in full
        assert "28 U.S.C. § 1746" in full

    def test_numbered_paragraphs(
        self, gen: Section1983Generator, sample_claim: Section1983Claim,
        sample_defendants: list[str], sample_facts: list[str],
    ) -> None:
        doc = gen.generate_complaint([sample_claim], sample_defendants, sample_facts)
        assert "1." in doc.full_text
        assert "2." in doc.full_text

    def test_plaintiff_name_in_text(
        self, gen: Section1983Generator, sample_claim: Section1983Claim,
        sample_defendants: list[str], sample_facts: list[str],
    ) -> None:
        doc = gen.generate_complaint([sample_claim], sample_defendants, sample_facts)
        assert PARTIES["plaintiff"] in doc.full_text


# ---------------------------------------------------------------------------
# 4. generate_cause_of_action
# ---------------------------------------------------------------------------

class TestGenerateCauseOfAction:
    def test_valid_claim_type(self, gen: Section1983Generator) -> None:
        text = gen.generate_cause_of_action(
            "due_process_substantive",
            ["Court acted without notice."],
        )
        assert "COUNT I" in text
        assert "SUBSTANTIVE DUE PROCESS" in text

    def test_invalid_claim_type_raises(self, gen: Section1983Generator) -> None:
        with pytest.raises(ValueError, match="Unknown claim type"):
            gen.generate_cause_of_action("made_up_claim", ["fact"])

    def test_contains_elements(self, gen: Section1983Generator) -> None:
        text = gen.generate_cause_of_action(
            "first_amendment_retaliation",
            ["Plaintiff was sanctioned after filing a motion."],
        )
        assert "constitutionally protected conduct" in text

    def test_contains_authority(self, gen: Section1983Generator) -> None:
        text = gen.generate_cause_of_action(
            "conspiracy_1983",
            ["Private party conspired with judge."],
        )
        assert "Dennis v. Sparks" in text


# ---------------------------------------------------------------------------
# 5. analyze_qualified_immunity
# ---------------------------------------------------------------------------

class TestQualifiedImmunity:
    def test_returns_model(self, gen: Section1983Generator) -> None:
        result = gen.analyze_qualified_immunity(
            "Hon. Jenny L. McNeill",
            ["Denied parenting time without a hearing."],
        )
        assert isinstance(result, QualifiedImmunityAnalysis)

    def test_parental_rights_clearly_established(
        self, gen: Section1983Generator,
    ) -> None:
        result = gen.analyze_qualified_immunity(
            "Hon. Jenny L. McNeill",
            ["Terminated custody without due process."],
        )
        assert result.clearly_established is True
        assert any("Troxel" in c for c in result.case_law)

    def test_recommendation_mentions_harlow(
        self, gen: Section1983Generator,
    ) -> None:
        result = gen.analyze_qualified_immunity(
            "Pamela Rusco",
            ["FOC failed to provide notice of hearing."],
        )
        assert "Harlow" in result.recommendation


# ---------------------------------------------------------------------------
# 6. generate_damages_section
# ---------------------------------------------------------------------------

class TestDamages:
    def test_returns_model(
        self, gen: Section1983Generator, sample_claim: Section1983Claim,
    ) -> None:
        dmg = gen.generate_damages_section([sample_claim])
        assert isinstance(dmg, DamagesCalculation)

    def test_includes_compensatory(
        self, gen: Section1983Generator, sample_claim: Section1983Claim,
    ) -> None:
        dmg = gen.generate_damages_section([sample_claim])
        assert "compensatory" in dmg.compensatory.lower()

    def test_includes_1988_fees(
        self, gen: Section1983Generator, sample_claim: Section1983Claim,
    ) -> None:
        dmg = gen.generate_damages_section([sample_claim])
        assert "42 U.S.C. § 1988" in dmg.attorneys_fees

    def test_includes_declaratory(
        self, gen: Section1983Generator, sample_claim: Section1983Claim,
    ) -> None:
        dmg = gen.generate_damages_section([sample_claim])
        assert "declaratory" in dmg.declaratory.lower()


# ---------------------------------------------------------------------------
# 7. check_statute_of_limitations
# ---------------------------------------------------------------------------

class TestStatuteOfLimitations:
    def test_timely_date(self, gen: Section1983Generator) -> None:
        future_date = (date.today() - timedelta(days=365)).isoformat()
        results = gen.check_statute_of_limitations([future_date])
        assert len(results) == 1
        assert results[0].is_timely is True

    def test_expired_date(self, gen: Section1983Generator) -> None:
        old_date = (date.today() - timedelta(days=365 * 4)).isoformat()
        results = gen.check_statute_of_limitations([old_date])
        assert len(results) == 1
        assert results[0].is_timely is False
        assert "WARNING" in results[0].notes

    def test_urgent_date(self, gen: Section1983Generator) -> None:
        almost_expired = date.today() - timedelta(days=365 * 3 - 30)
        results = gen.check_statute_of_limitations([almost_expired])
        assert results[0].is_timely is True
        assert "URGENT" in results[0].notes

    def test_multiple_dates(self, gen: Section1983Generator) -> None:
        dates = [
            date.today().isoformat(),
            (date.today() - timedelta(days=365 * 4)).isoformat(),
        ]
        results = gen.check_statute_of_limitations(dates)
        assert len(results) == 2
        assert results[0].is_timely is True
        assert results[1].is_timely is False

    def test_sol_is_three_years(self) -> None:
        assert MICHIGAN_SOL_YEARS == 3


# ---------------------------------------------------------------------------
# 8. generate_jurisdiction_section
# ---------------------------------------------------------------------------

class TestJurisdiction:
    def test_contains_1331(self, gen: Section1983Generator) -> None:
        text = gen.generate_jurisdiction_section()
        assert "28 U.S.C. § 1331" in text

    def test_contains_1343(self, gen: Section1983Generator) -> None:
        text = gen.generate_jurisdiction_section()
        assert "28 U.S.C. § 1343" in text

    def test_contains_venue(self, gen: Section1983Generator) -> None:
        text = gen.generate_jurisdiction_section()
        assert "28 U.S.C. § 1391" in text

    def test_domestic_relations_preemptive(
        self, gen: Section1983Generator,
    ) -> None:
        text = gen.generate_jurisdiction_section()
        assert "Catz v. Chalker" in text


# ---------------------------------------------------------------------------
# 9. analyze_domestic_relations_exception
# ---------------------------------------------------------------------------

class TestDomesticRelationsException:
    def test_procedural_challenge_not_barred(
        self, gen: Section1983Generator,
    ) -> None:
        result = gen.analyze_domestic_relations_exception(
            ["Court denied due process in custody hearing."]
        )
        assert isinstance(result, DomesticRelationsAnalysis)
        assert result.applies is False
        assert result.rebutted is True

    def test_catz_cited(self, gen: Section1983Generator) -> None:
        result = gen.analyze_domestic_relations_exception(
            ["Plaintiff challenges unconstitutional procedures."]
        )
        assert any("Catz" in a for a in result.key_authority)

    def test_pure_modification_flagged(
        self, gen: Section1983Generator,
    ) -> None:
        result = gen.analyze_domestic_relations_exception(
            ["Plaintiff asks federal court to modify custody and grant custody to father."]
        )
        assert result.applies is True
        assert result.rebutted is False


# ---------------------------------------------------------------------------
# 10. list_available_claims
# ---------------------------------------------------------------------------

class TestListAvailableClaims:
    def test_returns_all_six(self, gen: Section1983Generator) -> None:
        claims = gen.list_available_claims()
        assert len(claims) == 6

    def test_returns_copies(self, gen: Section1983Generator) -> None:
        claims = gen.list_available_claims()
        claims["due_process_substantive"]["title"] = "MUTATED"
        assert CLAIM_DEFINITIONS["due_process_substantive"]["title"] != "MUTATED"


# ---------------------------------------------------------------------------
# 11. validate_complaint
# ---------------------------------------------------------------------------

class TestValidateComplaint:
    def test_valid_complaint_passes(
        self, gen: Section1983Generator, sample_claim: Section1983Claim,
        sample_defendants: list[str], sample_facts: list[str],
    ) -> None:
        doc = gen.generate_complaint([sample_claim], sample_defendants, sample_facts)
        result = gen.validate_complaint(doc.full_text)
        assert result["valid"] is True
        assert result["score"] >= 80

    def test_empty_string_fails(self, gen: Section1983Generator) -> None:
        result = gen.validate_complaint("")
        assert result["valid"] is False
        assert result["score"] < 50

    def test_partial_complaint_has_issues(
        self, gen: Section1983Generator,
    ) -> None:
        partial = (
            "UNITED STATES DISTRICT COURT\n"
            "WESTERN DISTRICT OF MICHIGAN\n"
            "42 U.S.C. § 1983\n"
            "Plaintiff v. Defendant\n"
        )
        result = gen.validate_complaint(partial)
        assert len(result["issues"]) > 0


# ---------------------------------------------------------------------------
# 12. Pydantic model validation
# ---------------------------------------------------------------------------

class TestModels:
    def test_section1983_claim_creation(self) -> None:
        claim = Section1983Claim(
            claim_type="due_process_substantive",
            constitutional_basis="fourteenth_due_process_substantive",
        )
        assert claim.claim_type == "due_process_substantive"
        assert claim.elements == []
        assert claim.facts == []

    def test_qualified_immunity_defaults(self) -> None:
        qi = QualifiedImmunityAnalysis(defendant="Test Defendant")
        assert qi.clearly_established is False
        assert qi.case_law == []

    def test_damages_calculation_defaults(self) -> None:
        dmg = DamagesCalculation()
        assert dmg.compensatory == ""
        assert dmg.total_range == ""

    def test_complaint_document_has_timestamp(self) -> None:
        doc = ComplaintDocument()
        assert doc.generated_at is not None

    def test_sol_result_fields(self) -> None:
        sol = SOLResult(
            violation_date="2024-01-01",
            deadline_date="2027-01-01",
            days_remaining=365,
            is_timely=True,
        )
        assert sol.is_timely is True


# ---------------------------------------------------------------------------
# 13. Roman numeral utility
# ---------------------------------------------------------------------------

class TestRomanNumerals:
    def test_one(self) -> None:
        assert _roman(1) == "I"

    def test_four(self) -> None:
        assert _roman(4) == "IV"

    def test_ten(self) -> None:
        assert _roman(10) == "X"

    def test_fourteen(self) -> None:
        assert _roman(14) == "XIV"

    def test_zero_returns_string(self) -> None:
        assert _roman(0) == "0"


# ---------------------------------------------------------------------------
# 14. Federal court constants
# ---------------------------------------------------------------------------

class TestFederalCourtConstants:
    def test_district(self) -> None:
        assert FEDERAL_COURT["district"] == "WESTERN DISTRICT OF MICHIGAN"

    def test_division(self) -> None:
        assert FEDERAL_COURT["division"] == "SOUTHERN DIVISION"


# ---------------------------------------------------------------------------
# 15. Constitutional bases
# ---------------------------------------------------------------------------

class TestConstitutionalBases:
    def test_four_bases_defined(self) -> None:
        assert len(CONSTITUTIONAL_BASES) == 4

    def test_each_has_key_cases(self) -> None:
        for key, basis in CONSTITUTIONAL_BASES.items():
            assert "key_cases" in basis, f"{key} missing key_cases"
            assert len(basis["key_cases"]) >= 1


# ---------------------------------------------------------------------------
# 16. Multi-claim complaint
# ---------------------------------------------------------------------------

class TestMultiClaimComplaint:
    def test_two_counts(self, gen: Section1983Generator) -> None:
        claim1 = Section1983Claim(
            claim_type="due_process_substantive",
            constitutional_basis="fourteenth_due_process_substantive",
            elements=CLAIM_DEFINITIONS["due_process_substantive"]["elements"],
            facts=["Denied parenting time without hearing."],
            defendants=["Hon. Jenny L. McNeill"],
            key_authority=["Troxel v. Granville, 530 U.S. 57 (2000)"],
        )
        claim2 = Section1983Claim(
            claim_type="first_amendment_retaliation",
            constitutional_basis="first_amendment_retaliation",
            elements=CLAIM_DEFINITIONS["first_amendment_retaliation"]["elements"],
            facts=["After filing a motion, plaintiff was sanctioned."],
            defendants=["Hon. Jenny L. McNeill"],
            key_authority=["Thaddeus-X v. Blatter, 175 F.3d 378 (6th Cir. 1999)"],
        )
        doc = gen.generate_complaint(
            [claim1, claim2],
            ["Hon. Jenny L. McNeill"],
            ["Plaintiff filed motions."],
        )
        assert "COUNT I" in doc.full_text
        assert "COUNT II" in doc.full_text


# ---------------------------------------------------------------------------
# 17. Generator initializes without DB
# ---------------------------------------------------------------------------

class TestInitialization:
    def test_init_no_db(self) -> None:
        gen = Section1983Generator()
        assert gen._db is None

    def test_init_with_none(self) -> None:
        gen = Section1983Generator(db=None)
        assert gen._db is None


# ---------------------------------------------------------------------------
# 18. Verification section
# ---------------------------------------------------------------------------

class TestVerification:
    def test_verification_contains_1746(
        self, gen: Section1983Generator, sample_claim: Section1983Claim,
        sample_defendants: list[str], sample_facts: list[str],
    ) -> None:
        doc = gen.generate_complaint([sample_claim], sample_defendants, sample_facts)
        assert "28 U.S.C. § 1746" in doc.verification

    def test_verification_contains_plaintiff(
        self, gen: Section1983Generator, sample_claim: Section1983Claim,
        sample_defendants: list[str], sample_facts: list[str],
    ) -> None:
        doc = gen.generate_complaint([sample_claim], sample_defendants, sample_facts)
        assert PARTIES["plaintiff"] in doc.verification


# ---------------------------------------------------------------------------
# 19. Prayer for relief
# ---------------------------------------------------------------------------

class TestPrayerForRelief:
    def test_prayer_mentions_wherefore(
        self, gen: Section1983Generator, sample_claim: Section1983Claim,
        sample_defendants: list[str], sample_facts: list[str],
    ) -> None:
        doc = gen.generate_complaint([sample_claim], sample_defendants, sample_facts)
        assert "WHEREFORE" in doc.prayer_for_relief

    def test_prayer_mentions_1988(
        self, gen: Section1983Generator, sample_claim: Section1983Claim,
        sample_defendants: list[str], sample_facts: list[str],
    ) -> None:
        doc = gen.generate_complaint([sample_claim], sample_defendants, sample_facts)
        assert "42 U.S.C. § 1988" in doc.prayer_for_relief


# ---------------------------------------------------------------------------
# 20. Conspiracy claim — Dennis v. Sparks
# ---------------------------------------------------------------------------

class TestConspiracyClaim:
    def test_conspiracy_elements(self, gen: Section1983Generator) -> None:
        text = gen.generate_cause_of_action(
            "conspiracy_1983",
            [
                "Private party coordinated with state actor to deny rights.",
            ],
        )
        assert "agreement" in text.lower()
        assert "Dennis v. Sparks" in text

    def test_conspiracy_definition_has_overt_act(self) -> None:
        defn = CLAIM_DEFINITIONS["conspiracy_1983"]
        elements_text = " ".join(defn["elements"]).lower()
        assert "overt act" in elements_text


# ---------------------------------------------------------------------------
# 21. Equal protection claim
# ---------------------------------------------------------------------------

class TestEqualProtection:
    def test_intermediate_scrutiny(self, gen: Section1983Generator) -> None:
        text = gen.generate_cause_of_action(
            "equal_protection",
            ["Father treated differently from mother in custody."],
        )
        assert "Craig v. Boren" in text

    def test_gender_element(self) -> None:
        defn = CLAIM_DEFINITIONS["equal_protection"]
        elements_text = " ".join(defn["elements"]).lower()
        assert "gender" in elements_text


# ---------------------------------------------------------------------------
# 22. Failure to intervene
# ---------------------------------------------------------------------------

class TestFailureToIntervene:
    def test_elements_include_knowledge(self) -> None:
        defn = CLAIM_DEFINITIONS["failure_to_intervene"]
        elements_text = " ".join(defn["elements"]).lower()
        assert "knowledge" in elements_text

    def test_generate_cause(self, gen: Section1983Generator) -> None:
        text = gen.generate_cause_of_action(
            "failure_to_intervene",
            ["FOC knew of violation but took no action."],
        )
        assert "COUNT I" in text
