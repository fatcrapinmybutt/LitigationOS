# -*- coding: utf-8 -*-
"""Wave-13 Tests — ContemptEngine + InterrogatoryEngine
=========================================================
Comprehensive pytest suite for contempt_engine.py and
interrogatory_engine.py (~140 tests).

• Zero network / zero real DB — all DB interactions use tmp_path SQLite
• Independent tests, no ordering dependencies
• Decimal precision validated explicitly
• Real Michigan party names and MCR citations throughout
"""
from __future__ import annotations

import json
import pathlib
import sqlite3
import sys
from datetime import date, timedelta
from decimal import Decimal, ROUND_HALF_UP
from typing import List

import pytest

# ---------------------------------------------------------------------------
# Path bootstrap — let us import from the parent legal_ai package
# ---------------------------------------------------------------------------
_THIS_DIR = pathlib.Path(__file__).resolve().parent
_LEGAL_AI_DIR = _THIS_DIR.parent
if str(_LEGAL_AI_DIR) not in sys.path:
    sys.path.insert(0, str(_LEGAL_AI_DIR))

from contempt_engine import (
    ContemptType,
    ContemptStatus,
    ContemptViolation,
    ShowCauseOrder,
    ContemptSanction,
    PurgeCondition,
    ShowCauseGenerator,
    PurgeConditionAnalyzer,
    ContemptSanctionCalculator,
    ContemptDocumenter,
    ContemptEngine,
    _PLAINTIFF,
    _DEFENDANT,
    _CHILD_INITIALS,
    _JUDGE,
    _COURT,
    LANE_CASES,
    _SHOW_CAUSE_RESPONSE_DAYS,
    _CRIMINAL_CONTEMPT_MAX_JAIL,
    _CLEAR_AND_CONVINCING,
    _BEYOND_REASONABLE_DOUBT,
    _AUTHORITY_REFS,
)

from interrogatory_engine import (
    InterrogatoryType,
    InterrogatoryStatus,
    Interrogatory,
    InterrogatorySet,
    MotionToCompel,
    InterrogatoryDrafter,
    ObjectionHandler,
    ResponseDrafter as IResponseDrafter,
    InterrogatoryAnalyzer,
    InterrogatoryEngine,
    _PLAINTIFF as I_PLAINTIFF,
    _DEFENDANT as I_DEFENDANT,
    LANE_CASES as I_LANE_CASES,
    _STANDARD_LIMIT,
    _LIMITED_LIMIT,
    _RESPONSE_DAYS,
    _OBJECTION_BASES,
    _AUTHORITY_REFS as I_AUTHORITY_REFS,
)


# ===================================================================
# CONTEMPT ENGINE TESTS (~70)
# ===================================================================


# -------------------------------------------------------------------
# TestContemptType
# -------------------------------------------------------------------
class TestContemptType:
    """Tests for ContemptType enum."""

    def test_all_values_exist(self):
        expected = {"civil_direct", "civil_constructive", "criminal_direct", "criminal_constructive"}
        actual = {t.value for t in ContemptType}
        assert actual == expected

    def test_count_is_four(self):
        assert len(ContemptType) == 4

    def test_civil_direct_is_civil(self):
        assert ContemptType.CIVIL_DIRECT.is_civil is True

    def test_civil_constructive_is_civil(self):
        assert ContemptType.CIVIL_CONSTRUCTIVE.is_civil is True

    def test_criminal_direct_is_criminal(self):
        assert ContemptType.CRIMINAL_DIRECT.is_criminal is True

    def test_criminal_constructive_is_criminal(self):
        assert ContemptType.CRIMINAL_CONSTRUCTIVE.is_criminal is True

    def test_civil_not_criminal(self):
        assert ContemptType.CIVIL_DIRECT.is_criminal is False

    def test_criminal_not_civil(self):
        assert ContemptType.CRIMINAL_DIRECT.is_civil is False

    def test_direct_flag(self):
        assert ContemptType.CIVIL_DIRECT.is_direct is True
        assert ContemptType.CRIMINAL_DIRECT.is_direct is True
        assert ContemptType.CIVIL_CONSTRUCTIVE.is_direct is False

    def test_civil_standard_of_proof(self):
        assert ContemptType.CIVIL_DIRECT.standard_of_proof == "clear and convincing evidence"

    def test_criminal_standard_of_proof(self):
        assert ContemptType.CRIMINAL_DIRECT.standard_of_proof == "beyond a reasonable doubt"

    def test_civil_mcl_reference(self):
        ref = ContemptType.CIVIL_DIRECT.mcl_reference
        assert "MCL 600.1701" in ref
        assert "MCL 600.1745" in ref

    def test_criminal_mcl_reference(self):
        ref = ContemptType.CRIMINAL_DIRECT.mcl_reference
        assert "MCL 600.1715" in ref

    def test_str_enum(self):
        assert ContemptType.CIVIL_DIRECT == "civil_direct"


# -------------------------------------------------------------------
# TestContemptStatus
# -------------------------------------------------------------------
class TestContemptStatus:
    """Tests for ContemptStatus enum."""

    def test_all_values_exist(self):
        expected = {
            "identified", "documented", "motion_filed", "show_cause_issued",
            "hearing_scheduled", "found_in_contempt", "purged", "dismissed",
        }
        actual = {s.value for s in ContemptStatus}
        assert actual == expected

    def test_count_is_eight(self):
        assert len(ContemptStatus) == 8

    def test_terminal_found_in_contempt(self):
        assert ContemptStatus.FOUND_IN_CONTEMPT.is_terminal is True

    def test_terminal_purged(self):
        assert ContemptStatus.PURGED.is_terminal is True

    def test_terminal_dismissed(self):
        assert ContemptStatus.DISMISSED.is_terminal is True

    def test_not_terminal_identified(self):
        assert ContemptStatus.IDENTIFIED.is_terminal is False

    def test_next_statuses_identified(self):
        nexts = ContemptStatus.IDENTIFIED.next_statuses
        assert "documented" in nexts
        assert "dismissed" in nexts

    def test_next_statuses_purged_empty(self):
        assert ContemptStatus.PURGED.next_statuses == []


# -------------------------------------------------------------------
# TestContemptViolation
# -------------------------------------------------------------------
class TestContemptViolation:
    """Tests for ContemptViolation dataclass."""

    def test_default_creation(self):
        v = ContemptViolation()
        assert v.violation_id
        assert v.status == ContemptStatus.IDENTIFIED

    def test_to_dict(self):
        v = ContemptViolation(
            order_violated="Order ¶ 12",
            violation_date="2025-07-04",
            violation_description="Denied parenting time",
            evidence_refs=["Exhibit A"],
            contempt_type=ContemptType.CIVIL_CONSTRUCTIVE,
        )
        d = v.to_dict()
        assert d["order_violated"] == "Order ¶ 12"
        assert d["contempt_type"] == "civil_constructive"
        assert len(d["evidence_refs"]) == 1

    def test_custom_fields(self):
        v = ContemptViolation(willfulness_score=85)
        assert v.willfulness_score == 85


# -------------------------------------------------------------------
# TestShowCauseGenerator
# -------------------------------------------------------------------
class TestShowCauseGenerator:
    """Tests for ShowCauseGenerator."""

    def test_draft_motion_returns_dict(self):
        gen = ShowCauseGenerator()
        v = ContemptViolation(
            order_violated="Custody Order ¶ 12",
            violation_date="2025-07-04",
            violation_description="Denied holiday parenting time",
            evidence_refs=["text messages"],
        )
        motion = gen.draft_motion(v)
        assert motion["document_type"] == "Motion and Order to Show Cause"
        assert motion["movant"] == _PLAINTIFF
        assert motion["respondent"] == _DEFENDANT

    def test_draft_motion_has_sections(self):
        gen = ShowCauseGenerator()
        v = ContemptViolation(order_violated="Order")
        motion = gen.draft_motion(v)
        headings = [s["heading"] for s in motion["sections"]]
        assert "I. INTRODUCTION" in headings
        assert "VI. RELIEF REQUESTED" in headings

    def test_cite_violations_order(self):
        gen = ShowCauseGenerator()
        violations = [
            ContemptViolation(violation_date="2025-07-04", violation_description="First"),
            ContemptViolation(violation_date="2025-08-01", violation_description="Second"),
        ]
        citations = gen.cite_specific_violations(violations)
        assert len(citations) == 2
        assert citations[0]["number"] == 1

    def test_calculate_purge_conditions(self):
        gen = ShowCauseGenerator()
        v = ContemptViolation(
            order_violated="Order",
            violation_date="2025-07-04",
        )
        conditions = gen.calculate_purge_conditions(v)
        assert len(conditions) >= 3
        for c in conditions:
            assert c.is_achievable is True

    def test_draft_proposed_order(self):
        gen = ShowCauseGenerator()
        v = ContemptViolation(violation_date="2025-07-04")
        order = gen.draft_proposed_order(v, case_number="2024-001507-DC")
        assert order.case_number == "2024-001507-DC"
        assert order.respondent == _DEFENDANT

    def test_stats(self):
        gen = ShowCauseGenerator()
        s = gen.get_stats()
        assert s["component"] == "ShowCauseGenerator"


# -------------------------------------------------------------------
# TestPurgeConditionAnalyzer
# -------------------------------------------------------------------
class TestPurgeConditionAnalyzer:
    """Tests for PurgeConditionAnalyzer."""

    def test_ability_to_comply_achievable(self):
        analyzer = PurgeConditionAnalyzer()
        cond = PurgeCondition(description="Pay $500")
        result = analyzer.analyze_ability_to_comply(
            cond, financial_capacity=Decimal("10000"),
        )
        assert result["is_achievable"] is True

    def test_ability_to_comply_no_money(self):
        analyzer = PurgeConditionAnalyzer()
        cond = PurgeCondition(description="Pay $500")
        result = analyzer.analyze_ability_to_comply(
            cond, financial_capacity=Decimal("0"),
        )
        assert result["is_achievable"] is False
        assert "Dougherty" in result["authority"]

    def test_propose_conditions(self):
        analyzer = PurgeConditionAnalyzer()
        v = ContemptViolation(order_violated="Order")
        conditions = analyzer.propose_conditions(v, monetary_relief=Decimal("1000"))
        assert len(conditions) >= 2

    def test_check_reasonableness_all_ok(self):
        analyzer = PurgeConditionAnalyzer()
        conditions = [PurgeCondition(is_achievable=True) for _ in range(3)]
        result = analyzer.check_reasonableness(conditions)
        assert result["all_reasonable"] is True

    def test_check_reasonableness_one_bad(self):
        analyzer = PurgeConditionAnalyzer()
        conditions = [
            PurgeCondition(is_achievable=True),
            PurgeCondition(is_achievable=False, description="Impossible task"),
        ]
        result = analyzer.check_reasonableness(conditions)
        assert result["all_reasonable"] is False
        assert result["achievable_count"] == 1

    def test_document_willfulness_high(self):
        analyzer = PurgeConditionAnalyzer()
        v = ContemptViolation(contempt_type=ContemptType.CIVIL_CONSTRUCTIVE)
        result = analyzer.document_willfulness(
            v, knowledge_of_order=True, ability_to_comply=True,
            prior_violations=2,
        )
        assert result["willfulness_score"] > 50
        assert "Sword" in result["authority"]

    def test_document_willfulness_low(self):
        analyzer = PurgeConditionAnalyzer()
        v = ContemptViolation(contempt_type=ContemptType.CIVIL_CONSTRUCTIVE)
        result = analyzer.document_willfulness(
            v, knowledge_of_order=False, ability_to_comply=False,
        )
        assert result["willfulness_score"] == 0


# -------------------------------------------------------------------
# TestContemptSanctionCalculator
# -------------------------------------------------------------------
class TestContemptSanctionCalculator:
    """Tests for ContemptSanctionCalculator."""

    def test_compensatory_damages(self):
        calc = ContemptSanctionCalculator()
        v = ContemptViolation()
        result = calc.calculate_compensatory_damages(
            v, direct_costs=Decimal("500"), childcare_costs=Decimal("200"),
        )
        assert result["total"] == "700.00"

    def test_attorney_fees_pro_se(self):
        calc = ContemptSanctionCalculator()
        result = calc.calculate_attorney_fees(
            filing_fees=Decimal("20"), is_pro_se=True,
        )
        assert result["attorney_fees"] == "0.00"
        assert result["total"] == "20.00"

    def test_attorney_fees_represented(self):
        calc = ContemptSanctionCalculator()
        result = calc.calculate_attorney_fees(
            hours_spent=Decimal("10"), hourly_rate=Decimal("300"),
            filing_fees=Decimal("50"), is_pro_se=False,
        )
        assert Decimal(result["attorney_fees"]) == Decimal("3000.00")

    def test_incarceration_civil(self):
        calc = ContemptSanctionCalculator()
        result = calc.recommend_incarceration_period(
            ContemptType.CIVIL_CONSTRUCTIVE,
        )
        assert result["type"] == "coercive"
        assert result["fixed_term"] is False
        assert result["max_days"] is None

    def test_incarceration_criminal(self):
        calc = ContemptSanctionCalculator()
        result = calc.recommend_incarceration_period(
            ContemptType.CRIMINAL_DIRECT, severity=50,
        )
        assert result["type"] == "punitive"
        assert result["fixed_term"] is True
        assert result["recommended_days"] <= _CRIMINAL_CONTEMPT_MAX_JAIL

    def test_incarceration_max_cap(self):
        calc = ContemptSanctionCalculator()
        result = calc.recommend_incarceration_period(
            ContemptType.CRIMINAL_DIRECT, severity=100, prior_contempts=5,
        )
        assert result["recommended_days"] <= _CRIMINAL_CONTEMPT_MAX_JAIL

    def test_coercive_vs_punitive_civil(self):
        calc = ContemptSanctionCalculator()
        result = calc.assess_coercive_vs_punitive(ContemptType.CIVIL_DIRECT)
        assert result["sanction_character"] == "coercive"
        assert "DeGeorge" in result["legal_basis"]

    def test_coercive_vs_punitive_criminal(self):
        calc = ContemptSanctionCalculator()
        result = calc.assess_coercive_vs_punitive(ContemptType.CRIMINAL_DIRECT)
        assert result["sanction_character"] == "punitive"


# -------------------------------------------------------------------
# TestContemptDocumenter
# -------------------------------------------------------------------
class TestContemptDocumenter:
    """Tests for ContemptDocumenter."""

    def test_build_timeline(self):
        doc = ContemptDocumenter()
        violations = [
            ContemptViolation(violation_date="2025-08-01", violation_description="Second"),
            ContemptViolation(violation_date="2025-07-04", violation_description="First"),
        ]
        timeline = doc.build_violation_timeline(violations)
        assert timeline[0]["date"] == "2025-07-04"  # Sorted chronologically

    def test_catalog_evidence(self):
        doc = ContemptDocumenter()
        violations = [
            ContemptViolation(evidence_refs=["A", "B"]),
            ContemptViolation(evidence_refs=["B", "C"]),
        ]
        catalog = doc.catalog_evidence(violations)
        assert catalog["total_evidence_refs"] == 4
        assert len(catalog["unique_exhibits"]) == 3

    def test_generate_exhibit_list(self):
        doc = ContemptDocumenter()
        violations = [
            ContemptViolation(evidence_refs=["Photo 1", "Photo 2"]),
        ]
        exhibits = doc.generate_exhibit_list(violations, starting_number=1)
        assert len(exhibits) == 2
        assert exhibits[0]["exhibit_number"] == 1

    def test_create_brief(self):
        doc = ContemptDocumenter()
        violations = [
            ContemptViolation(
                violation_date="2025-07-04",
                violation_description="Denied parenting time",
                evidence_refs=["Exhibit A"],
            ),
        ]
        brief = doc.create_contempt_brief(violations, case_number="2024-001507-DC")
        assert brief["document_type"] == "Brief in Support of Motion for Contempt"
        assert brief["total_violations"] == 1
        assert "sha256" in brief


# -------------------------------------------------------------------
# TestContemptEngine
# -------------------------------------------------------------------
class TestContemptEngine:
    """Tests for ContemptEngine orchestrator."""

    def test_init(self, tmp_path):
        db = tmp_path / "test.db"
        engine = ContemptEngine(db_path=db)
        assert engine._db_path == db

    def test_identify_violations(self):
        engine = ContemptEngine()
        v = engine.identify_violations(
            order_violated="Order ¶ 12",
            violation_date="2025-07-04",
            violation_description="Denied parenting time",
            evidence_refs=["Exhibit A"],
        )
        assert v.status == ContemptStatus.IDENTIFIED
        assert v.order_violated == "Order ¶ 12"

    def test_file_contempt(self):
        engine = ContemptEngine()
        v = engine.identify_violations(
            order_violated="Order",
            violation_description="test violation",
        )
        result = engine.file_contempt(v.violation_id)
        assert result["status"] == "motion_filed"
        assert "motion" in result
        assert "purge_conditions" in result

    def test_file_contempt_not_found(self):
        engine = ContemptEngine()
        result = engine.file_contempt("nonexistent")
        assert "error" in result

    def test_track_proceedings(self):
        engine = ContemptEngine()
        v = engine.identify_violations(order_violated="Order")
        engine.file_contempt(v.violation_id)
        tracked = engine.track_proceedings(v.violation_id)
        assert tracked["current_status"] == "motion_filed"

    def test_update_status_valid(self):
        engine = ContemptEngine()
        v = engine.identify_violations(order_violated="Order")
        updated = engine.update_status(v.violation_id, ContemptStatus.DOCUMENTED)
        assert updated.status == ContemptStatus.DOCUMENTED

    def test_update_status_invalid_transition(self):
        engine = ContemptEngine()
        v = engine.identify_violations(order_violated="Order")
        engine.update_status(v.violation_id, ContemptStatus.PURGED)
        assert v.status == ContemptStatus.IDENTIFIED  # Unchanged

    def test_monitor_purge(self):
        engine = ContemptEngine()
        v = engine.identify_violations(order_violated="Order")
        engine.file_contempt(v.violation_id)
        result = engine.monitor_purge(v.violation_id)
        assert result["total_conditions"] >= 0

    def test_list_violations(self):
        engine = ContemptEngine()
        engine.identify_violations(order_violated="Order1")
        engine.identify_violations(order_violated="Order2")
        assert len(engine.list_violations()) == 2

    def test_list_violations_filtered(self):
        engine = ContemptEngine()
        engine.identify_violations(order_violated="Order1")
        assert len(engine.list_violations(status=ContemptStatus.IDENTIFIED)) == 1
        assert len(engine.list_violations(status=ContemptStatus.DISMISSED)) == 0

    def test_get_stats(self):
        engine = ContemptEngine()
        engine.identify_violations(order_violated="Order")
        stats = engine.get_stats()
        assert stats["module"] == "contempt_engine"
        assert stats["total_violations"] == 1

    def test_reset(self):
        engine = ContemptEngine()
        engine.identify_violations(order_violated="Order")
        engine.reset()
        assert len(engine.list_violations()) == 0


# ===================================================================
# INTERROGATORY ENGINE TESTS (~70)
# ===================================================================


# -------------------------------------------------------------------
# TestInterrogatoryType
# -------------------------------------------------------------------
class TestInterrogatoryType:
    """Tests for InterrogatoryType enum."""

    def test_all_values_exist(self):
        expected = {"standard", "contention", "identification", "expert", "supplemental"}
        actual = {t.value for t in InterrogatoryType}
        assert actual == expected

    def test_count_is_five(self):
        assert len(InterrogatoryType) == 5

    def test_description_nonempty(self):
        for t in InterrogatoryType:
            assert t.description

    def test_str_enum(self):
        assert InterrogatoryType.STANDARD == "standard"


# -------------------------------------------------------------------
# TestInterrogatoryStatus
# -------------------------------------------------------------------
class TestInterrogatoryStatus:
    """Tests for InterrogatoryStatus enum."""

    def test_all_values_exist(self):
        expected = {
            "drafted", "served", "response_due", "answered",
            "objected", "overdue", "motion_to_compel",
        }
        actual = {s.value for s in InterrogatoryStatus}
        assert actual == expected

    def test_count_is_seven(self):
        assert len(InterrogatoryStatus) == 7

    def test_terminal_answered(self):
        assert InterrogatoryStatus.ANSWERED.is_terminal is True

    def test_not_terminal_served(self):
        assert InterrogatoryStatus.SERVED.is_terminal is False

    def test_requires_action_overdue(self):
        assert InterrogatoryStatus.OVERDUE.requires_action is True

    def test_requires_action_motion(self):
        assert InterrogatoryStatus.MOTION_TO_COMPEL.requires_action is True

    def test_no_action_drafted(self):
        assert InterrogatoryStatus.DRAFTED.requires_action is False


# -------------------------------------------------------------------
# TestInterrogatory
# -------------------------------------------------------------------
class TestInterrogatory:
    """Tests for Interrogatory dataclass."""

    def test_default_creation(self):
        rog = Interrogatory()
        assert rog.number == 0
        assert rog.status == InterrogatoryStatus.DRAFTED

    def test_to_dict(self):
        rog = Interrogatory(
            number=1,
            text="State your name.",
            interrogatory_type=InterrogatoryType.IDENTIFICATION,
            target_info="party ID",
        )
        d = rog.to_dict()
        assert d["number"] == 1
        assert d["interrogatory_type"] == "identification"

    def test_subparts(self):
        rog = Interrogatory(number=5, subparts=3)
        assert rog.subparts == 3


# -------------------------------------------------------------------
# TestInterrogatoryDrafter
# -------------------------------------------------------------------
class TestInterrogatoryDrafter:
    """Tests for InterrogatoryDrafter."""

    def test_draft_custody_set(self):
        drafter = InterrogatoryDrafter()
        rogs = drafter.draft_standard_set(case_type="custody")
        assert len(rogs) > 0
        assert len(rogs) <= _STANDARD_LIMIT

    def test_draft_housing_set(self):
        drafter = InterrogatoryDrafter()
        rogs = drafter.draft_standard_set(case_type="housing")
        assert len(rogs) > 0

    def test_draft_with_limit(self):
        drafter = InterrogatoryDrafter()
        rogs = drafter.draft_standard_set(case_type="custody", limit=5)
        assert len(rogs) <= 5

    def test_contention_interrogatories(self):
        drafter = InterrogatoryDrafter()
        rogs = drafter.draft_contention_interrogatories(
            claims=["negligence", "breach"],
            defenses=["statute of limitations"],
        )
        assert len(rogs) == 3
        assert all(r.interrogatory_type == InterrogatoryType.CONTENTION for r in rogs)

    def test_identification_requests(self):
        drafter = InterrogatoryDrafter()
        rogs = drafter.draft_identification_requests()
        assert len(rogs) >= 4
        assert all(r.interrogatory_type == InterrogatoryType.IDENTIFICATION for r in rogs)

    def test_enforce_limits_within(self):
        drafter = InterrogatoryDrafter()
        rogs = [Interrogatory(number=i) for i in range(10)]
        result = drafter.enforce_limits(rogs)
        assert result["exceeds_limit"] is False
        assert "MCR 2.309(A)(2)" in result["authority"]

    def test_enforce_limits_over(self):
        drafter = InterrogatoryDrafter()
        rogs = [Interrogatory(number=i) for i in range(40)]
        result = drafter.enforce_limits(rogs, limit=35)
        assert result["exceeds_limit"] is True
        assert result["overage"] == 5


# -------------------------------------------------------------------
# TestObjectionHandler
# -------------------------------------------------------------------
class TestObjectionHandler:
    """Tests for ObjectionHandler."""

    def test_generate_objections(self):
        handler = ObjectionHandler()
        rog = Interrogatory(number=1, text="State everything ever.")
        objs = handler.generate_objections(rog, grounds=["overbroad", "relevance"])
        assert len(objs) == 2

    def test_check_overbroad_positive(self):
        handler = ObjectionHandler()
        rog = Interrogatory(number=1, text="List any and all documents ever created.")
        result = handler.check_overbroad(rog)
        assert result["is_overbroad"] is True

    def test_check_overbroad_negative(self):
        handler = ObjectionHandler()
        rog = Interrogatory(number=1, text="State your current address.")
        result = handler.check_overbroad(rog)
        assert result["is_overbroad"] is False

    def test_check_unduly_burdensome(self):
        handler = ObjectionHandler()
        rog = Interrogatory(number=1)
        result = handler.check_unduly_burdensome(rog, estimated_hours=Decimal("20"))
        assert result["is_unduly_burdensome"] is True

    def test_check_not_burdensome(self):
        handler = ObjectionHandler()
        rog = Interrogatory(number=1)
        result = handler.check_unduly_burdensome(rog, estimated_hours=Decimal("2"))
        assert result["is_unduly_burdensome"] is False

    def test_check_privilege_detected(self):
        handler = ObjectionHandler()
        rog = Interrogatory(number=1, text="What did your attorney advise?")
        result = handler.check_privilege(rog)
        assert result["privilege_implicated"] is True
        assert "attorney_client" in result["privilege_types"]

    def test_check_privilege_none(self):
        handler = ObjectionHandler()
        rog = Interrogatory(number=1, text="State your current employer.")
        result = handler.check_privilege(rog)
        assert result["privilege_implicated"] is False

    def test_check_relevance_with_claims(self):
        handler = ObjectionHandler()
        rog = Interrogatory(number=1, text="Describe the custody arrangement.")
        result = handler.check_relevance(rog, claims_at_issue=["custody"])
        assert result["is_relevant"] is True

    def test_check_relevance_no_claims(self):
        handler = ObjectionHandler()
        rog = Interrogatory(number=1, text="Anything.")
        result = handler.check_relevance(rog)
        assert result["is_relevant"] is True  # Default when no claims given


# -------------------------------------------------------------------
# TestResponseDrafter (Interrogatory)
# -------------------------------------------------------------------
class TestIResponseDrafter:
    """Tests for interrogatory ResponseDrafter."""

    def test_draft_response_facts_only(self):
        drafter = IResponseDrafter()
        rog = Interrogatory(number=1, text="State your name.")
        response = drafter.draft_response(rog, facts=["Andrew James Pigors"])
        assert "Andrew James Pigors" in response

    def test_draft_response_with_objection(self):
        drafter = IResponseDrafter()
        rog = Interrogatory(number=1, text="State everything.")
        response = drafter.draft_response(
            rog, facts=["Partial response"], objections=["overbroad"],
        )
        assert "OBJECTION" in response
        assert "without waiving" in response

    def test_supplement_response(self):
        drafter = IResponseDrafter()
        rog = Interrogatory(number=1)
        supp = drafter.supplement_response(
            rog, new_facts=["New fact discovered"],
            original_response="Original answer",
        )
        assert "SUPPLEMENTAL" in supp
        assert "MCR 2.302(E)" in supp

    def test_calculate_deadline_personal(self):
        drafter = IResponseDrafter()
        result = drafter.calculate_response_deadline("2025-06-01", "personal")
        expected = (date(2025, 6, 1) + timedelta(days=28)).isoformat()
        assert result["deadline"] == expected

    def test_calculate_deadline_mail(self):
        drafter = IResponseDrafter()
        result = drafter.calculate_response_deadline("2025-06-01", "mail")
        expected = (date(2025, 6, 1) + timedelta(days=31)).isoformat()
        assert result["deadline"] == expected

    def test_calculate_deadline_invalid_date(self):
        drafter = IResponseDrafter()
        result = drafter.calculate_response_deadline("bad-date")
        assert "error" in result


# -------------------------------------------------------------------
# TestInterrogatoryAnalyzer
# -------------------------------------------------------------------
class TestInterrogatoryAnalyzer:
    """Tests for InterrogatoryAnalyzer."""

    def test_analyze_all_answered(self):
        analyzer = InterrogatoryAnalyzer()
        rogs = [Interrogatory(number=1, answer="Done")]
        result = analyzer.analyze_opposing_responses(rogs)
        assert result["answered"] == 1
        assert result["motion_to_compel_warranted"] is False

    def test_analyze_with_objections(self):
        analyzer = InterrogatoryAnalyzer()
        rogs = [Interrogatory(number=1, objection_basis=["overbroad"])]
        result = analyzer.analyze_opposing_responses(rogs)
        assert result["objected_only"] == 1
        assert result["motion_to_compel_warranted"] is True

    def test_identify_evasive(self):
        analyzer = InterrogatoryAnalyzer()
        rogs = [Interrogatory(
            number=1,
            answer="I don't recall.",
            interrogatory_type=InterrogatoryType.CONTENTION,
        )]
        evasive = analyzer.identify_evasive_answers(rogs)
        assert len(evasive) == 1
        assert "Domako" in evasive[0]["authority"]

    def test_identify_not_evasive(self):
        analyzer = InterrogatoryAnalyzer()
        rogs = [Interrogatory(number=1, answer="My name is Emily A. Watson.")]
        evasive = analyzer.identify_evasive_answers(rogs)
        assert len(evasive) == 0

    def test_prepare_motion_to_compel(self):
        analyzer = InterrogatoryAnalyzer()
        iset = InterrogatorySet(
            set_id="test",
            case_number="2024-001507-DC",
            interrogatories=[Interrogatory(number=1)],
        )
        motion = analyzer.prepare_motion_to_compel(iset, [1])
        assert motion.case_number == "2024-001507-DC"
        assert 1 in motion.deficient_interrogatories

    def test_supplementation_tracking(self):
        analyzer = InterrogatoryAnalyzer()
        rogs = [Interrogatory(number=1, answer="Original answer")]
        result = analyzer.track_supplementation_duty(rogs, new_information_available=True)
        assert result["supplementation_count"] == 1
        assert "MCR 2.302(E)" in result["authority"]


# -------------------------------------------------------------------
# TestInterrogatoryEngine
# -------------------------------------------------------------------
class TestInterrogatoryEngine:
    """Tests for InterrogatoryEngine orchestrator."""

    def test_init(self, tmp_path):
        db = tmp_path / "test.db"
        engine = InterrogatoryEngine(db_path=db)
        assert engine._db_path == db

    def test_create_interrogatories(self):
        engine = InterrogatoryEngine()
        rogs = engine.create_interrogatories(case_type="custody")
        assert len(rogs) > 0

    def test_create_housing_interrogatories(self):
        engine = InterrogatoryEngine()
        rogs = engine.create_interrogatories(case_type="housing")
        assert len(rogs) > 0

    def test_serve(self):
        engine = InterrogatoryEngine()
        rogs = engine.create_interrogatories()
        sets = engine.list_sets()
        assert len(sets) == 1
        result = engine.serve(sets[0].set_id, service_date="2025-06-01")
        assert result["status"] == "served"
        assert result["response_deadline"]

    def test_serve_not_found(self):
        engine = InterrogatoryEngine()
        result = engine.serve("nonexistent")
        assert "error" in result

    def test_track_responses(self):
        engine = InterrogatoryEngine()
        rogs = engine.create_interrogatories()
        sets = engine.list_sets()
        set_id = sets[0].set_id
        result = engine.track_responses(set_id, responses={1: "Answer"})
        assert result["updated_count"] == 1

    def test_analyze_answers(self):
        engine = InterrogatoryEngine()
        engine.create_interrogatories()
        sets = engine.list_sets()
        set_id = sets[0].set_id
        engine.track_responses(set_id, responses={1: "Answer"})
        result = engine.analyze_answers(set_id)
        assert "analysis" in result

    def test_get_stats(self):
        engine = InterrogatoryEngine()
        engine.create_interrogatories()
        stats = engine.get_stats()
        assert stats["module"] == "interrogatory_engine"
        assert stats["total_sets"] == 1

    def test_reset(self):
        engine = InterrogatoryEngine()
        engine.create_interrogatories()
        engine.reset()
        assert len(engine.list_sets()) == 0
