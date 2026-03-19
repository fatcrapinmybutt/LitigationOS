# -*- coding: utf-8 -*-
"""Wave-13 Tests — SummaryJudgmentEngine
==========================================
Comprehensive pytest suite for summary_judgment_engine.py (~110 tests).

• Zero network / zero real DB — all DB interactions use tmp_path SQLite
• Independent tests, no ordering dependencies
• Real Michigan party names and MCR citations throughout
"""
from __future__ import annotations

import json
import pathlib
import sqlite3
import sys
from datetime import date, timedelta
from decimal import Decimal
from typing import List

import pytest

# ---------------------------------------------------------------------------
# Path bootstrap — let us import from the parent legal_ai package
# ---------------------------------------------------------------------------
_THIS_DIR = pathlib.Path(__file__).resolve().parent
_LEGAL_AI_DIR = _THIS_DIR.parent
if str(_LEGAL_AI_DIR) not in sys.path:
    sys.path.insert(0, str(_LEGAL_AI_DIR))

from summary_judgment_engine import (
    SJGrounds,
    SJRole,
    SJStatus,
    SJMotion,
    BurdenAnalysis,
    SJBrief,
    BurdenShiftAnalyzer,
    EvidenceOrganizer,
    ResponseDrafter,
    OralArgumentPreparer,
    SummaryJudgmentEngine,
    _PLAINTIFF,
    _DEFENDANT,
    _CHILD_INITIALS,
    _JUDGE,
    _COURT,
    LANE_CASES,
    _RESPONSE_PERIOD_DAYS,
    _REPLY_PERIOD_DAYS,
    _GROUNDS_INFO,
    _AUTHORITY_REFS,
)


# ===================================================================
# SUMMARY JUDGMENT ENGINE TESTS (~110)
# ===================================================================


# -------------------------------------------------------------------
# TestSJGrounds
# -------------------------------------------------------------------
class TestSJGrounds:
    """Tests for SJGrounds enum."""

    def test_all_values_exist(self):
        expected = {
            "C1_JURISDICTION", "C4_PRIOR_ACTION", "C5_GOVERNMENTAL_IMMUNITY",
            "C7_FAILURE_TO_STATE_CLAIM", "C8_AFFIRMATIVE_DEFENSE",
            "C9_NO_GENUINE_ISSUE_DIRECTED", "C10_NO_GENUINE_ISSUE",
        }
        actual = {g.value for g in SJGrounds}
        assert actual == expected

    def test_count_is_seven(self):
        assert len(SJGrounds) == 7

    def test_c10_mcr_reference(self):
        assert SJGrounds.C10_NO_GENUINE_ISSUE.mcr_reference == "MCR 2.116(C)(10)"

    def test_c8_mcr_reference(self):
        assert SJGrounds.C8_AFFIRMATIVE_DEFENSE.mcr_reference == "MCR 2.116(C)(8)"

    def test_c1_mcr_reference(self):
        assert SJGrounds.C1_JURISDICTION.mcr_reference == "MCR 2.116(C)(1)"

    def test_c7_mcr_reference(self):
        assert SJGrounds.C7_FAILURE_TO_STATE_CLAIM.mcr_reference == "MCR 2.116(C)(7)"

    def test_description_nonempty(self):
        for g in SJGrounds:
            assert g.description

    def test_standard_nonempty(self):
        for g in SJGrounds:
            assert g.standard

    def test_c10_requires_factual_support(self):
        assert SJGrounds.C10_NO_GENUINE_ISSUE.requires_factual_support is True

    def test_c8_no_factual_support(self):
        assert SJGrounds.C8_AFFIRMATIVE_DEFENSE.requires_factual_support is False

    def test_c9_requires_factual_support(self):
        assert SJGrounds.C9_NO_GENUINE_ISSUE_DIRECTED.requires_factual_support is True

    def test_c1_no_factual_support(self):
        assert SJGrounds.C1_JURISDICTION.requires_factual_support is False

    def test_str_enum(self):
        assert SJGrounds.C10_NO_GENUINE_ISSUE == "C10_NO_GENUINE_ISSUE"


# -------------------------------------------------------------------
# TestSJRole
# -------------------------------------------------------------------
class TestSJRole:
    """Tests for SJRole enum."""

    def test_all_values(self):
        assert {r.value for r in SJRole} == {"movant", "respondent"}

    def test_count_is_two(self):
        assert len(SJRole) == 2

    def test_movant_description(self):
        assert "moving" in SJRole.MOVANT.description.lower()

    def test_respondent_description(self):
        assert "responding" in SJRole.RESPONDENT.description.lower()


# -------------------------------------------------------------------
# TestSJStatus
# -------------------------------------------------------------------
class TestSJStatus:
    """Tests for SJStatus enum."""

    def test_all_values(self):
        expected = {
            "drafting", "filed", "response_period", "reply_period",
            "submitted", "hearing_scheduled", "granted", "denied", "partial",
        }
        actual = {s.value for s in SJStatus}
        assert actual == expected

    def test_count_is_nine(self):
        assert len(SJStatus) == 9

    def test_granted_is_terminal(self):
        assert SJStatus.GRANTED.is_terminal is True

    def test_denied_is_terminal(self):
        assert SJStatus.DENIED.is_terminal is True

    def test_partial_is_terminal(self):
        assert SJStatus.PARTIAL.is_terminal is True

    def test_drafting_not_terminal(self):
        assert SJStatus.DRAFTING.is_terminal is False

    def test_filed_not_terminal(self):
        assert SJStatus.FILED.is_terminal is False


# -------------------------------------------------------------------
# TestSJMotion
# -------------------------------------------------------------------
class TestSJMotion:
    """Tests for SJMotion dataclass."""

    def test_default_creation(self):
        m = SJMotion()
        assert m.motion_id
        assert m.status == SJStatus.DRAFTING

    def test_to_dict(self):
        m = SJMotion(
            grounds=[SJGrounds.C10_NO_GENUINE_ISSUE],
            movant=_PLAINTIFF,
            respondent=_DEFENDANT,
            claims_targeted=["negligence"],
        )
        d = m.to_dict()
        assert d["grounds"] == ["C10_NO_GENUINE_ISSUE"]
        assert d["movant"] == _PLAINTIFF

    def test_custom_case_number(self):
        m = SJMotion(case_number="2025-002760-CZ")
        assert m.case_number == "2025-002760-CZ"


# -------------------------------------------------------------------
# TestBurdenAnalysis
# -------------------------------------------------------------------
class TestBurdenAnalysis:
    """Tests for BurdenAnalysis dataclass."""

    def test_default(self):
        ba = BurdenAnalysis()
        assert ba.initial_burden_met is False
        assert ba.burden_shifted is False

    def test_to_dict(self):
        ba = BurdenAnalysis(
            ground="C10",
            initial_burden_met=True,
            recommendation="Grant motion",
        )
        d = ba.to_dict()
        assert d["ground"] == "C10"
        assert d["initial_burden_met"] is True


# -------------------------------------------------------------------
# TestBurdenShiftAnalyzer
# -------------------------------------------------------------------
class TestBurdenShiftAnalyzer:
    """Tests for BurdenShiftAnalyzer."""

    def test_initial_burden_c10_with_evidence(self):
        analyzer = BurdenShiftAnalyzer()
        result = analyzer.analyze_initial_burden(
            [SJGrounds.C10_NO_GENUINE_ISSUE],
            evidence_offered=["Affidavit"],
            elements_addressed={"duty": True, "breach": True},
        )
        assert result["overall_burden_met"] is True

    def test_initial_burden_c10_no_evidence(self):
        analyzer = BurdenShiftAnalyzer()
        result = analyzer.analyze_initial_burden(
            [SJGrounds.C10_NO_GENUINE_ISSUE],
            evidence_offered=[],
        )
        assert result["overall_burden_met"] is False

    def test_initial_burden_c8(self):
        analyzer = BurdenShiftAnalyzer()
        result = analyzer.analyze_initial_burden(
            [SJGrounds.C8_AFFIRMATIVE_DEFENSE],
        )
        assert result["overall_burden_met"] is True

    def test_initial_burden_c7(self):
        analyzer = BurdenShiftAnalyzer()
        result = analyzer.analyze_initial_burden(
            [SJGrounds.C7_FAILURE_TO_STATE_CLAIM],
        )
        assert result["overall_burden_met"] is True

    def test_shifted_burden_not_met(self):
        analyzer = BurdenShiftAnalyzer()
        result = analyzer.analyze_shifted_burden(
            {"overall_burden_met": False},
        )
        assert result["burden_shifted"] is False

    def test_shifted_burden_with_rebuttal(self):
        analyzer = BurdenShiftAnalyzer()
        result = analyzer.analyze_shifted_burden(
            {"overall_burden_met": True},
            nonmovant_evidence=["Counter-affidavit"],
        )
        assert result["burden_shifted"] is True
        assert result["rebuttal_sufficient"] is True

    def test_shifted_burden_no_rebuttal(self):
        analyzer = BurdenShiftAnalyzer()
        result = analyzer.analyze_shifted_burden(
            {"overall_burden_met": True},
        )
        assert result["rebuttal_sufficient"] is False

    def test_quinto_compliant(self):
        analyzer = BurdenShiftAnalyzer()
        affidavits = [
            {"affiant": "Pigors", "personal_knowledge": True,
             "specific_facts": True, "admissible": True},
        ]
        result = analyzer.apply_quinto_framework(affidavits)
        assert result["valid_count"] == 1
        assert result["deficient_count"] == 0

    def test_quinto_deficient(self):
        analyzer = BurdenShiftAnalyzer()
        affidavits = [
            {"affiant": "Unknown", "personal_knowledge": False,
             "specific_facts": False, "admissible": False},
        ]
        result = analyzer.apply_quinto_framework(affidavits)
        assert result["deficient_count"] == 1
        assert "Quinto" in result["authority"]

    def test_maiden_framework_grant(self):
        analyzer = BurdenShiftAnalyzer()
        result = analyzer.apply_maiden_framework(
            ground=SJGrounds.C10_NO_GENUINE_ISSUE,
            movant_evidence=["Affidavit", "Report"],
            nonmovant_evidence=[],
            elements={"duty": True, "breach": True},
        )
        assert result["genuine_issue_exists"] is False
        assert "GRANTED" in result["recommendation"]

    def test_maiden_framework_deny(self):
        analyzer = BurdenShiftAnalyzer()
        result = analyzer.apply_maiden_framework(
            ground=SJGrounds.C10_NO_GENUINE_ISSUE,
            movant_evidence=["Affidavit"],
            nonmovant_evidence=["Counter-evidence"],
            elements={"duty": True},
        )
        assert result["genuine_issue_exists"] is True
        assert "DENIED" in result["recommendation"]

    def test_stats(self):
        analyzer = BurdenShiftAnalyzer()
        s = analyzer.get_stats()
        assert s["component"] == "BurdenShiftAnalyzer"


# -------------------------------------------------------------------
# TestEvidenceOrganizer
# -------------------------------------------------------------------
class TestEvidenceOrganizer:
    """Tests for EvidenceOrganizer."""

    def test_organize_by_element(self):
        org = EvidenceOrganizer()
        result = org.organize_by_element(
            elements=["duty", "breach", "causation"],
            evidence_map={"duty": ["Affidavit A"], "breach": ["Report B"]},
        )
        assert result["supported_count"] == 2
        assert result["gap_count"] == 1
        assert "causation" in result["gaps"]

    def test_organize_no_evidence(self):
        org = EvidenceOrganizer()
        result = org.organize_by_element(elements=["duty"])
        assert result["gap_count"] == 1

    def test_identify_gaps(self):
        org = EvidenceOrganizer()
        gaps = org.identify_gaps(
            elements=["duty", "breach"],
            available_evidence=["duty met — affidavit"],
        )
        assert len(gaps) == 1
        assert gaps[0]["element"] == "breach"

    def test_prepare_affidavits(self):
        org = EvidenceOrganizer()
        affidavits = org.prepare_affidavits([
            {"affiant": _PLAINTIFF, "facts": ["Fact 1"], "subject": "Duty"},
        ])
        assert len(affidavits) == 1
        assert affidavits[0]["quinto_compliant"] is True

    def test_compile_exhibits(self):
        org = EvidenceOrganizer()
        exhibits = org.compile_exhibits_for_brief(
            ["Affidavit A", "Report B", "Photo C"],
        )
        assert len(exhibits) == 3
        assert exhibits[0]["exhibit_label"] == "A"
        assert exhibits[2]["exhibit_label"] == "C"

    def test_stats(self):
        org = EvidenceOrganizer()
        s = org.get_stats()
        assert s["component"] == "EvidenceOrganizer"


# -------------------------------------------------------------------
# TestResponseDrafter (SJ)
# -------------------------------------------------------------------
class TestSJResponseDrafter:
    """Tests for SJ ResponseDrafter."""

    def test_draft_response_brief(self):
        drafter = ResponseDrafter()
        motion = SJMotion(
            movant=_DEFENDANT,
            respondent=_PLAINTIFF,
            case_number="2025-002760-CZ",
            claims_targeted=["negligence"],
        )
        brief = drafter.draft_response_brief(motion)
        assert brief.brief_type == "response"
        assert brief.case_number == "2025-002760-CZ"

    def test_identify_genuine_issues(self):
        drafter = ResponseDrafter()
        motion = SJMotion(claims_targeted=["negligence", "breach"])
        issues = drafter.identify_genuine_issues(
            motion, disputed_facts=["Roof condition disputed"],
        )
        # 1 disputed fact + 2 per-claim issues
        assert len(issues) >= 3

    def test_prepare_counter_affidavits(self):
        drafter = ResponseDrafter()
        affidavits = drafter.prepare_counter_affidavits([
            {"affiant": _PLAINTIFF, "facts": ["I observed the defect"]},
        ])
        assert len(affidavits) == 1
        assert affidavits[0]["personal_knowledge"] is True

    def test_request_56f_continuance(self):
        drafter = ResponseDrafter()
        motion = SJMotion(case_number="2025-002760-CZ")
        result = drafter.request_56f_continuance(
            motion,
            reasons=["Discovery incomplete"],
            discovery_needed=["Deposition of property manager"],
        )
        assert result["document_type"] == "Motion for Continuance / MCR 2.116(H)"
        assert len(result["discovery_needed"]) == 1

    def test_stats(self):
        drafter = ResponseDrafter()
        s = drafter.get_stats()
        assert s["component"] == "ResponseDrafter"


# -------------------------------------------------------------------
# TestOralArgumentPreparer
# -------------------------------------------------------------------
class TestOralArgumentPreparer:
    """Tests for OralArgumentPreparer."""

    def test_prepare_respondent_outline(self):
        prep = OralArgumentPreparer()
        motion = SJMotion()
        outline = prep.prepare_argument_outline(motion, role=SJRole.RESPONDENT)
        assert outline["role"] == "respondent"
        assert outline["total_time_minutes"] > 0
        sections = [s["section"] for s in outline["structure"]]
        assert "Opening" in sections

    def test_prepare_movant_outline(self):
        prep = OralArgumentPreparer()
        motion = SJMotion()
        outline = prep.prepare_argument_outline(motion, role=SJRole.MOVANT)
        assert outline["role"] == "movant"

    def test_anticipate_questions(self):
        prep = OralArgumentPreparer()
        motion = SJMotion(claims_targeted=["negligence"])
        questions = prep.anticipate_questions(motion)
        assert len(questions) >= 3
        assert any("genuine issue" in q["question"].lower() for q in questions)

    def test_anticipate_questions_movant(self):
        prep = OralArgumentPreparer()
        motion = SJMotion()
        questions = prep.anticipate_questions(motion, role=SJRole.MOVANT)
        assert any("specifically identified" in q["question"].lower() for q in questions)

    def test_prepare_authorities(self):
        prep = OralArgumentPreparer()
        authorities = prep.prepare_authorities_for_bench([SJGrounds.C10_NO_GENUINE_ISSUE])
        citations = [a["citation"] for a in authorities]
        assert any("Maiden" in c for c in citations)
        assert any("Quinto" in c for c in citations)
        assert any("Skinner" in c for c in citations)

    def test_authorities_include_ground(self):
        prep = OralArgumentPreparer()
        authorities = prep.prepare_authorities_for_bench(
            [SJGrounds.C10_NO_GENUINE_ISSUE, SJGrounds.C8_AFFIRMATIVE_DEFENSE],
        )
        assert len(authorities) >= 5  # 3 base + 2 grounds

    def test_stats(self):
        prep = OralArgumentPreparer()
        s = prep.get_stats()
        assert s["component"] == "OralArgumentPreparer"


# -------------------------------------------------------------------
# TestSummaryJudgmentEngine
# -------------------------------------------------------------------
class TestSummaryJudgmentEngine:
    """Tests for SummaryJudgmentEngine orchestrator."""

    def test_init(self, tmp_path):
        db = tmp_path / "test.db"
        engine = SummaryJudgmentEngine(db_path=db)
        assert engine._db_path == db

    def test_prepare_motion_c10(self):
        engine = SummaryJudgmentEngine()
        result = engine.prepare_motion(
            grounds=["C10_NO_GENUINE_ISSUE"],
            claims_targeted=["negligence"],
            supporting_evidence=["Affidavit"],
        )
        assert "motion_id" in result
        assert result["motion"]["grounds"] == ["C10_NO_GENUINE_ISSUE"]

    def test_prepare_motion_multiple_grounds(self):
        engine = SummaryJudgmentEngine()
        result = engine.prepare_motion(
            grounds=["C7_FAILURE_TO_STATE_CLAIM", "C10_NO_GENUINE_ISSUE"],
        )
        assert len(result["brief_sections"]) == 2

    def test_prepare_motion_default_case(self):
        engine = SummaryJudgmentEngine()
        result = engine.prepare_motion()
        assert result["motion"]["case_number"] == LANE_CASES["B"]

    def test_prepare_response(self):
        engine = SummaryJudgmentEngine()
        m = engine.prepare_motion(claims_targeted=["negligence"])
        resp = engine.prepare_response(
            m["motion_id"],
            counter_evidence=["Counter-affidavit"],
            disputed_facts=["Condition of property"],
        )
        assert "brief" in resp
        assert resp["issue_count"] >= 1

    def test_prepare_response_not_found(self):
        engine = SummaryJudgmentEngine()
        result = engine.prepare_response("nonexistent")
        assert "error" in result

    def test_analyze_odds(self):
        engine = SummaryJudgmentEngine()
        m = engine.prepare_motion(grounds=["C10_NO_GENUINE_ISSUE"])
        odds = engine.analyze_odds(m["motion_id"])
        assert 0.0 < odds["overall_probability"] < 1.0

    def test_analyze_odds_strong_movant(self):
        engine = SummaryJudgmentEngine()
        m = engine.prepare_motion(grounds=["C10_NO_GENUINE_ISSUE"])
        odds = engine.analyze_odds(
            m["motion_id"],
            movant_evidence_strength=90,
            nonmovant_evidence_strength=10,
        )
        assert odds["overall_probability"] > 0.5

    def test_analyze_odds_not_found(self):
        engine = SummaryJudgmentEngine()
        result = engine.analyze_odds("nonexistent")
        assert "error" in result

    def test_generate_brief_outline_movant(self):
        engine = SummaryJudgmentEngine()
        m = engine.prepare_motion(grounds=["C10_NO_GENUINE_ISSUE"])
        outline = engine.generate_brief_outline(m["motion_id"], role=SJRole.MOVANT)
        assert "INTRODUCTION" in outline["sections"][0]

    def test_generate_brief_outline_respondent(self):
        engine = SummaryJudgmentEngine()
        m = engine.prepare_motion()
        outline = engine.generate_brief_outline(m["motion_id"], role=SJRole.RESPONDENT)
        assert any("COUNTER" in s for s in outline["sections"])

    def test_generate_brief_not_found(self):
        engine = SummaryJudgmentEngine()
        result = engine.generate_brief_outline("nonexistent")
        assert "error" in result

    def test_get_motion(self):
        engine = SummaryJudgmentEngine()
        m = engine.prepare_motion()
        motion = engine.get_motion(m["motion_id"])
        assert motion is not None
        assert motion.motion_id == m["motion_id"]

    def test_get_motion_not_found(self):
        engine = SummaryJudgmentEngine()
        assert engine.get_motion("nonexistent") is None

    def test_list_motions(self):
        engine = SummaryJudgmentEngine()
        engine.prepare_motion()
        engine.prepare_motion()
        assert len(engine.list_motions()) == 2

    def test_list_motions_filtered(self):
        engine = SummaryJudgmentEngine()
        engine.prepare_motion()
        assert len(engine.list_motions(status=SJStatus.DRAFTING)) == 1
        assert len(engine.list_motions(status=SJStatus.GRANTED)) == 0

    def test_update_status(self):
        engine = SummaryJudgmentEngine()
        m = engine.prepare_motion()
        updated = engine.update_status(m["motion_id"], SJStatus.FILED)
        assert updated.status == SJStatus.FILED

    def test_update_status_not_found(self):
        engine = SummaryJudgmentEngine()
        assert engine.update_status("nonexistent", SJStatus.FILED) is None

    def test_get_stats(self):
        engine = SummaryJudgmentEngine()
        engine.prepare_motion(grounds=["C10_NO_GENUINE_ISSUE"])
        stats = engine.get_stats()
        assert stats["module"] == "summary_judgment_engine"
        assert stats["total_motions"] == 1
        assert "C10_NO_GENUINE_ISSUE" in stats["by_ground"]

    def test_reset(self):
        engine = SummaryJudgmentEngine()
        engine.prepare_motion()
        engine.reset()
        assert len(engine.list_motions()) == 0

    def test_response_period_constant(self):
        assert _RESPONSE_PERIOD_DAYS == 21

    def test_reply_period_constant(self):
        assert _REPLY_PERIOD_DAYS == 7

    def test_grounds_info_complete(self):
        for g in SJGrounds:
            assert g.value in _GROUNDS_INFO
            assert "mcr" in _GROUNDS_INFO[g.value]
            assert "description" in _GROUNDS_INFO[g.value]

    def test_authority_refs_has_maiden(self):
        assert "maiden" in _AUTHORITY_REFS
        assert "461 Mich 109" in _AUTHORITY_REFS["maiden"]

    def test_authority_refs_has_quinto(self):
        assert "quinto" in _AUTHORITY_REFS
        assert "451 Mich 358" in _AUTHORITY_REFS["quinto"]
