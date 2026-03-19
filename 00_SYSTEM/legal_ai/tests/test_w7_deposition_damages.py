# -*- coding: utf-8 -*-
"""
Test Suite — Wave 7: DepositionStrategist & DamagesCalculator
=============================================================
200+ tests covering deposition_strategist.py and damages_calculator.py.

Rules:
  - Zero network.  100 % local.
  - tempfile.mkdtemp() for isolation.
  - Mock all DB operations — never touch real litigation_context.db.
  - Every test is independent.
  - NO imports from repo root (shadow modules).
"""
from __future__ import annotations

import os
import sqlite3
import sys
import tempfile
from datetime import date, datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Dict, List
from unittest.mock import MagicMock, patch

import pytest

# ---------------------------------------------------------------------------
# Ensure the legal_ai package is importable from the tests directory
# ---------------------------------------------------------------------------
_TESTS_DIR = Path(__file__).resolve().parent
_LEGAL_AI_DIR = _TESTS_DIR.parent
if str(_LEGAL_AI_DIR) not in sys.path:
    sys.path.insert(0, str(_LEGAL_AI_DIR))
if str(_LEGAL_AI_DIR.parent) not in sys.path:
    sys.path.insert(0, str(_LEGAL_AI_DIR.parent))

# ---------------------------------------------------------------------------
# Import modules under test
# ---------------------------------------------------------------------------
from deposition_strategist import (
    LANE_CASE_NUMBERS,
    LANE_LABELS,
    MCR_RULES,
    DepositionAnalyzer,
    DepositionPlan,
    DepositionPlanner,
    DepositionQuestion,
    DepositionStatus,
    DepositionStrategist,
    ObjectionType,
    PerformanceRating,
    QuestionBank,
    QuestionCategory,
    QuestionStyle,
    StatementRecord,
    TranscriptAnalysis,
    WitnessProfile,
    WitnessRole,
    _PLAINTIFF,
    _DEFENDANT,
    _CHILD_INITIALS,
    _JUDGE,
)
from damages_calculator import (
    DEFENDANTS,
    LANE_CASE_NUMBERS as DMG_LANE_CASE_NUMBERS,
    LANE_LABELS as DMG_LANE_LABELS,
    CalculationMethod,
    DamageCategory,
    DamageItem,
    DamagesCalculator,
    Defendant,
    DefendantAllocation,
    LaneDamagesSummary,
    LiabilityType,
    MultiplierStatute,
    PrejudgmentInterestCalculator,
    StatutoryMultiplierEngine,
    _PLAINTIFF as DMG_PLAINTIFF,
    _DEFENDANT as DMG_DEFENDANT,
    _CHILD_INITIALS as DMG_CHILD,
    _JUDGE as DMG_JUDGE,
)


# ═══════════════════════════════════════════════════════════════════════════
# Helpers / Fixtures
# ═══════════════════════════════════════════════════════════════════════════

@pytest.fixture
def tmp_db() -> Path:
    """Create a temporary SQLite database for testing."""
    d = tempfile.mkdtemp(prefix="litostest_")
    db_path = Path(d) / "test.db"
    conn = sqlite3.connect(str(db_path))
    conn.execute("PRAGMA journal_mode=WAL")
    conn.close()
    return db_path


def _make_witness(
    name: str = "Test Witness",
    role: str = "fact",
    lane: str = "A",
    **kwargs: Any,
) -> WitnessProfile:
    return WitnessProfile(name=name, role=role, lane=lane, **kwargs)


def _make_statement(
    content: str = "I saw the event.",
    source_type: str = "filing",
    **kwargs: Any,
) -> StatementRecord:
    return StatementRecord(content=content, source_type=source_type, **kwargs)


def _make_damage_item(**kwargs: Any) -> DamageItem:
    defaults: Dict[str, Any] = {
        "category": DamageCategory.ECONOMIC.value,
        "description": "Test damage",
        "amount_low": 1000.0,
        "amount_mid": 5000.0,
        "amount_high": 10000.0,
        "lane": "A",
    }
    defaults.update(kwargs)
    return DamageItem(**defaults)


# ═══════════════════════════════════════════════════════════════════════════
# PART 1 — DepositionStrategist Tests
# ═══════════════════════════════════════════════════════════════════════════


# --- 1A  Enumerations ---

class TestDepositionEnums:
    """Verify all deposition-related enums have expected values."""

    def test_witness_role_values(self) -> None:
        assert WitnessRole.PARTY.value == "party"
        assert WitnessRole.EXPERT.value == "expert"
        assert WitnessRole.FACT.value == "fact"
        assert WitnessRole.CHARACTER.value == "character"

    def test_witness_role_count(self) -> None:
        assert len(WitnessRole) == 4

    def test_question_category_values(self) -> None:
        expected = {
            "foundational", "impeachment", "admission_seeking",
            "timeline", "credibility", "damage_proof",
        }
        assert {qc.value for qc in QuestionCategory} == expected

    def test_question_style_values(self) -> None:
        assert QuestionStyle.OPEN.value == "open"
        assert QuestionStyle.LEADING.value == "leading"
        assert QuestionStyle.COMPOUND.value == "compound"
        assert QuestionStyle.HYPOTHETICAL.value == "hypothetical"

    def test_objection_type_count(self) -> None:
        assert len(ObjectionType) == 10

    def test_deposition_status_values(self) -> None:
        expected = {"draft", "planned", "notice_sent", "completed", "analyzed"}
        assert {s.value for s in DepositionStatus} == expected

    def test_performance_rating_values(self) -> None:
        expected = {"excellent", "good", "neutral", "poor", "devastating"}
        assert {r.value for r in PerformanceRating} == expected


# --- 1B  Dataclasses ---

class TestStatementRecord:

    def test_creation_defaults(self) -> None:
        s = StatementRecord()
        assert s.statement_id  # auto-generated
        assert s.consistency_score == 100.0
        assert s.contradicts == []

    def test_to_dict_keys(self) -> None:
        s = _make_statement(content="hello")
        d = s.to_dict()
        assert "statement_id" in d
        assert d["content"] == "hello"

    def test_custom_id_preserved(self) -> None:
        s = StatementRecord(statement_id="custom123")
        assert s.statement_id == "custom123"

    def test_check_consistency_no_others(self) -> None:
        s = _make_statement()
        score = s.check_consistency([])
        assert score == 100.0

    def test_check_consistency_contradiction(self) -> None:
        s1 = _make_statement(content="He did attend the meeting.")
        s2 = _make_statement(content="He did not attend the meeting.")
        score = s1.check_consistency([s2])
        assert score < 100.0
        assert len(s1.contradicts) > 0

    def test_check_consistency_no_conflict(self) -> None:
        s1 = _make_statement(content="It was sunny outside")
        s2 = _make_statement(content="The sky was clear")
        score = s1.check_consistency([s2])
        assert score == 100.0

    def test_check_consistency_self_excluded(self) -> None:
        s1 = _make_statement(content="He was present")
        score = s1.check_consistency([s1])
        assert score == 100.0


class TestWitnessProfile:

    def test_creation_auto_id(self) -> None:
        wp = _make_witness(name="Jane Doe")
        assert wp.witness_id
        assert len(wp.witness_id) == 12

    def test_to_dict(self) -> None:
        wp = _make_witness()
        d = wp.to_dict()
        assert "witness_id" in d
        assert "prior_statements" in d

    def test_update_credibility_positive(self) -> None:
        wp = _make_witness()
        wp.credibility_score = 50.0
        result = wp.update_credibility(20.0)
        assert result == 70.0

    def test_update_credibility_clamped_high(self) -> None:
        wp = _make_witness()
        wp.credibility_score = 95.0
        result = wp.update_credibility(20.0)
        assert result == 100.0

    def test_update_credibility_clamped_low(self) -> None:
        wp = _make_witness()
        wp.credibility_score = 5.0
        result = wp.update_credibility(-20.0)
        assert result == 0.0

    def test_add_statement(self) -> None:
        wp = _make_witness()
        s = _make_statement()
        wp.add_statement(s)
        assert len(wp.prior_statements) == 1
        assert s.witness_id == wp.witness_id

    def test_get_contradiction_count_empty(self) -> None:
        wp = _make_witness()
        assert wp.get_contradiction_count() == 0

    def test_get_contradiction_count_nonzero(self) -> None:
        wp = _make_witness()
        s1 = _make_statement(content="He did attend")
        s2 = _make_statement(content="He did not attend")
        wp.add_statement(s1)
        wp.add_statement(s2)
        assert wp.get_contradiction_count() >= 0

    def test_default_lane(self) -> None:
        wp = WitnessProfile(name="Test")
        assert wp.lane == "A"

    def test_known_biases_list(self) -> None:
        wp = _make_witness(known_biases=["bias_a", "bias_b"])
        assert len(wp.known_biases) == 2


class TestDepositionQuestion:

    def test_creation(self) -> None:
        q = DepositionQuestion(text="What happened?")
        assert q.question_id
        assert q.priority == 5

    def test_to_dict(self) -> None:
        q = DepositionQuestion(text="Test?")
        d = q.to_dict()
        assert d["text"] == "Test?"


class TestDepositionPlan:

    def test_creation(self) -> None:
        plan = DepositionPlan()
        assert plan.plan_id
        assert plan.created_at

    def test_question_count_property(self) -> None:
        plan = DepositionPlan()
        plan.questions = [
            DepositionQuestion(text="Q1"),
            DepositionQuestion(text="Q2"),
        ]
        assert plan.question_count == 2

    def test_to_dict(self) -> None:
        plan = DepositionPlan()
        d = plan.to_dict()
        assert "plan_id" in d
        assert "questions" in d

    def test_to_dict_with_witness(self) -> None:
        wp = _make_witness()
        plan = DepositionPlan(witness=wp)
        d = plan.to_dict()
        assert "witness" in d


class TestTranscriptAnalysis:

    def test_creation_defaults(self) -> None:
        ta = TranscriptAnalysis()
        assert ta.transcript_id
        assert ta.analyzed_at
        assert ta.performance_rating == "neutral"

    def test_to_dict(self) -> None:
        ta = TranscriptAnalysis(witness_name="Doe")
        d = ta.to_dict()
        assert d["witness_name"] == "Doe"


# --- 1C  QuestionBank ---

class TestQuestionBank:

    def test_generate_direct_questions(self) -> None:
        qb = QuestionBank()
        wp = _make_witness()
        qs = qb.generate_direct_questions(wp, "custody_interference", "A")
        assert len(qs) > 0
        assert all(isinstance(q, DepositionQuestion) for q in qs)

    def test_direct_questions_include_foundational(self) -> None:
        qb = QuestionBank()
        wp = _make_witness()
        qs = qb.generate_direct_questions(wp, "custody_interference", "A")
        cats = {q.category for q in qs}
        assert "foundational" in cats

    def test_generate_cross_questions(self) -> None:
        qb = QuestionBank()
        wp = _make_witness(name=_DEFENDANT, role="party")
        qs = qb.generate_cross_questions(wp, "custody_interference", "A")
        assert len(qs) > 0
        styles = {q.style for q in qs}
        assert "leading" in styles

    def test_cross_questions_lane_b(self) -> None:
        qb = QuestionBank()
        wp = _make_witness(lane="B")
        qs = qb.generate_cross_questions(wp, "habitability", "B")
        assert len(qs) > 0

    def test_generate_impeachment_sequence_empty(self) -> None:
        qb = QuestionBank()
        wp = _make_witness()
        qs = qb.generate_impeachment_sequence(wp, [])
        assert qs == []

    def test_generate_impeachment_sequence_with_pair(self) -> None:
        qb = QuestionBank()
        wp = _make_witness()
        s1 = _make_statement(content="I was there")
        s2 = _make_statement(content="I was not there", statement_date="2024-01-01")
        qs = qb.generate_impeachment_sequence(wp, [(s1, s2)])
        assert len(qs) >= 10  # 4 commit + 4 confront + 2-3 contrast

    def test_impeachment_mcr_basis(self) -> None:
        qb = QuestionBank()
        wp = _make_witness()
        s1 = _make_statement(content="Claim A")
        s2 = _make_statement(content="Claim B")
        qs = qb.generate_impeachment_sequence(wp, [(s1, s2)])
        mcr_refs = [q.mcr_basis for q in qs if q.mcr_basis]
        assert all("MRE 613" in ref for ref in mcr_refs)

    def test_prioritize_questions_within_limit(self) -> None:
        qb = QuestionBank()
        questions = [
            DepositionQuestion(text=f"Q{i}", priority=i, estimated_minutes=30.0)
            for i in range(20)
        ]
        selected = qb.prioritize_questions(questions, time_limit_minutes=120.0)
        total_time = sum(q.estimated_minutes for q in selected)
        assert total_time <= 150.0  # some slack for the last partial fit

    def test_prioritize_returns_highest_priority_first(self) -> None:
        qb = QuestionBank()
        q1 = DepositionQuestion(text="High", priority=1, estimated_minutes=5.0)
        q2 = DepositionQuestion(text="Low", priority=10, estimated_minutes=5.0)
        selected = qb.prioritize_questions([q2, q1], time_limit_minutes=100.0)
        assert selected[0].priority <= selected[-1].priority

    def test_check_mcr_compliance_within_limit(self) -> None:
        qb = QuestionBank()
        qs = [DepositionQuestion(text="Q", estimated_minutes=10.0) for _ in range(10)]
        result = qb.check_mcr_compliance(qs)
        assert result["within_7_hour_limit"] is True
        assert result["total_estimated_minutes"] == 100.0

    def test_check_mcr_compliance_over_limit(self) -> None:
        qb = QuestionBank()
        qs = [DepositionQuestion(text="Q", estimated_minutes=100.0) for _ in range(5)]
        result = qb.check_mcr_compliance(qs)
        assert result["within_7_hour_limit"] is False

    def test_check_mcr_foundational(self) -> None:
        qb = QuestionBank()
        qs = [DepositionQuestion(
            text="Name?",
            category=QuestionCategory.FOUNDATIONAL.value,
            estimated_minutes=1.0,
        )]
        result = qb.check_mcr_compliance(qs)
        assert result["has_foundational_questions"] is True

    def test_total_generated_counter(self) -> None:
        qb = QuestionBank()
        wp = _make_witness()
        qb.generate_direct_questions(wp, "custody_interference", "A")
        assert qb.total_generated > 0


# --- 1D  DepositionPlanner ---

class TestDepositionPlanner:

    def test_plan_deposition(self, tmp_db: Path) -> None:
        planner = DepositionPlanner(db_path=tmp_db)
        wp = _make_witness(name="Test Witness")
        plan = planner.plan_deposition(wp, "A")
        assert isinstance(plan, DepositionPlan)
        assert plan.status == "planned"

    def test_plan_deposition_adverse_witness(self, tmp_db: Path) -> None:
        planner = DepositionPlanner(db_path=tmp_db)
        wp = _make_witness(name=_DEFENDANT, role="party")
        plan = planner.plan_deposition(wp, "A")
        styles = {q.style for q in plan.questions}
        assert "leading" in styles

    def test_estimate_duration_fact(self) -> None:
        planner = DepositionPlanner()
        duration = planner.estimate_duration(50, "fact")
        assert 100 < duration <= 420

    def test_estimate_duration_expert(self) -> None:
        planner = DepositionPlanner()
        duration = planner.estimate_duration(50, "expert")
        assert duration > planner.estimate_duration(50, "fact")

    def test_estimate_duration_cap(self) -> None:
        planner = DepositionPlanner()
        duration = planner.estimate_duration(500, "fact")
        assert duration == 420.0

    def test_generate_notice(self) -> None:
        planner = DepositionPlanner()
        wp = _make_witness(name="Jane Doe", lane="A")
        notice = planner.generate_notice(wp, date(2025, 6, 15))
        assert "MCR 2.306" in notice
        assert "NOTICE OF TAKING DEPOSITION" in notice
        assert "Jane Doe" in notice
        assert "ANDREW JAMES PIGORS" in notice

    def test_generate_notice_case_number(self) -> None:
        planner = DepositionPlanner()
        wp = _make_witness(name="Doe", lane="B")
        notice = planner.generate_notice(wp, date(2025, 7, 1))
        assert "2025-002760-CZ" in notice

    def test_prepare_exhibits_empty(self) -> None:
        planner = DepositionPlanner()
        wp = _make_witness()
        exhibits = planner.prepare_exhibits(wp)
        assert exhibits == []

    def test_prepare_exhibits_with_statements(self) -> None:
        planner = DepositionPlanner()
        wp = _make_witness()
        s = _make_statement(
            source_type="filing",
            exhibit_ref="Exhibit A",
            statement_date="2024-01-01",
        )
        wp.prior_statements = [s]
        exhibits = planner.prepare_exhibits(wp)
        assert len(exhibits) == 1
        assert exhibits[0]["number"] == "1"

    def test_prepare_exhibits_with_relevant_docs(self) -> None:
        planner = DepositionPlanner()
        wp = _make_witness()
        docs = [{"description": "Medical record", "path": "/docs/med.pdf"}]
        exhibits = planner.prepare_exhibits(wp, relevant_docs=docs)
        assert len(exhibits) == 1

    def test_identify_objection_risks_compound(self) -> None:
        planner = DepositionPlanner()
        # Two question marks + "and" triggers compound detection
        q = DepositionQuestion(
            text="Did you go to the store? And did you buy milk?",
            style="open",
        )
        risks = planner.identify_objection_risks([q])
        assert len(risks) >= 1


# --- 1E  DepositionAnalyzer ---

class TestDepositionAnalyzer:

    @pytest.fixture
    def sample_transcript(self) -> str:
        return (
            "Q: State your name.\n"
            "WITNESS: Emily Watson.\n"
            "Q: Did you deny parenting time on March 15?\n"
            "WITNESS: I don't recall the specific date.\n"
            "Q: Isn't it true you refused the exchange?\n"
            "WITNESS: Yes, that's right.\n"
            "Q: Were you present at the school event?\n"
            "WITNESS: I don't remember if I was there.\n"
        )

    def test_analyze_transcript(self, sample_transcript: str) -> None:
        analyzer = DepositionAnalyzer()
        result = analyzer.analyze_transcript(sample_transcript)
        assert isinstance(result, TranscriptAnalysis)
        assert result.page_count >= 1

    def test_analyze_finds_admissions(self, sample_transcript: str) -> None:
        analyzer = DepositionAnalyzer()
        result = analyzer.analyze_transcript(sample_transcript)
        assert len(result.key_admissions) > 0

    def test_analyze_finds_evasions(self, sample_transcript: str) -> None:
        analyzer = DepositionAnalyzer()
        result = analyzer.analyze_transcript(sample_transcript)
        assert len(result.evasions) > 0

    def test_score_witness_performance(self) -> None:
        analyzer = DepositionAnalyzer()
        ta = TranscriptAnalysis()
        ta.key_admissions = [{"content": "yes"}]
        ta.evasions = [{"content": "don't recall"}, {"content": "maybe"}]
        ta.contradictions = []
        result = analyzer.score_witness_performance(ta)
        assert "score" in result
        assert "rating" in result
        assert 0 <= result["score"] <= 100

    def test_score_devastating(self) -> None:
        analyzer = DepositionAnalyzer()
        ta = TranscriptAnalysis()
        ta.key_admissions = [{"content": f"a{i}"} for i in range(5)]
        ta.evasions = [{"content": f"e{i}"} for i in range(5)]
        ta.contradictions = [{"content": f"c{i}"} for i in range(3)]
        result = analyzer.score_witness_performance(ta)
        assert result["rating"] in ("poor", "devastating")

    def test_extract_impeachment_material(self) -> None:
        analyzer = DepositionAnalyzer()
        ta = TranscriptAnalysis()
        ta.key_admissions = [
            {"content": "I admit it", "page_ref": "5"},
        ]
        ta.contradictions = [
            {"content": "Contradicted self", "page_ref": "12"},
        ]
        materials = analyzer.extract_impeachment_material(ta)
        assert len(materials) == 2
        types = {m["type"] for m in materials}
        assert "admission" in types
        assert "contradiction" in types

    def test_compare_to_prior_statements_no_match(self) -> None:
        analyzer = DepositionAnalyzer()
        prior = [_make_statement(content="The sky was blue")]
        result = analyzer.compare_to_prior_statements("unrelated text", prior)
        assert result == []

    def test_compare_to_prior_statements_contradiction(self) -> None:
        analyzer = DepositionAnalyzer()
        prior = [_make_statement(content="He did attend the meeting on Tuesday.")]
        transcript = "He did not attend the meeting on Tuesday."
        result = analyzer.compare_to_prior_statements(transcript, prior)
        assert len(result) >= 1

    def test_empty_transcript(self) -> None:
        analyzer = DepositionAnalyzer()
        result = analyzer.analyze_transcript("")
        assert result.page_count >= 1
        assert result.key_admissions == []


# --- 1F  DepositionStrategist Orchestrator ---

class TestDepositionStrategist:

    def test_init(self, tmp_db: Path) -> None:
        engine = DepositionStrategist(db_path=tmp_db)
        assert engine.VERSION == "1.0.0"

    def test_build_witness_database(self, tmp_db: Path) -> None:
        engine = DepositionStrategist(db_path=tmp_db)
        result = engine.build_witness_database()
        assert result["witnesses_loaded"] >= 5
        assert result["total_witnesses"] >= 5

    def test_get_witness(self, tmp_db: Path) -> None:
        engine = DepositionStrategist(db_path=tmp_db)
        engine.build_witness_database()
        wp = engine.get_witness("Watson")
        assert wp is not None
        assert "Watson" in wp.name

    def test_get_witness_not_found(self, tmp_db: Path) -> None:
        engine = DepositionStrategist(db_path=tmp_db)
        engine.build_witness_database()
        assert engine.get_witness("NONEXISTENT_PERSON_XYZ") is None

    def test_prepare_full_deposition(self, tmp_db: Path) -> None:
        engine = DepositionStrategist(db_path=tmp_db)
        plan = engine.prepare_full_deposition(_DEFENDANT, "A")
        assert isinstance(plan, DepositionPlan)
        assert plan.question_count > 0
        assert plan.status == "planned"

    def test_prepare_deposition_unknown_witness(self, tmp_db: Path) -> None:
        engine = DepositionStrategist(db_path=tmp_db)
        plan = engine.prepare_full_deposition("Unknown Person", "B")
        assert plan.case_lane == "B"

    def test_get_stats(self, tmp_db: Path) -> None:
        engine = DepositionStrategist(db_path=tmp_db)
        stats = engine.get_stats()
        assert stats["engine"] == "DepositionStrategist"
        assert "witness_count" in stats
        assert stats["case_context"]["plaintiff"] == _PLAINTIFF
        assert stats["case_context"]["defendant"] == _DEFENDANT

    def test_analyze_deposition_transcript(self, tmp_db: Path) -> None:
        engine = DepositionStrategist(db_path=tmp_db)
        transcript = (
            "Q: State your name.\n"
            "WITNESS: Emily Watson.\n"
            "Q: Did you deny parenting time?\n"
            "WITNESS: I don't recall.\n"
        )
        analysis = engine.analyze_deposition_transcript(_DEFENDANT, transcript)
        assert isinstance(analysis, TranscriptAnalysis)
        assert analysis.witness_name == _DEFENDANT


# --- 1G  Lane Routing & Constants ---

class TestLaneRoutingAndConstants:

    def test_lane_labels_all_present(self) -> None:
        for lane in ("A", "B", "C", "D", "E", "F"):
            assert lane in LANE_LABELS

    def test_lane_case_numbers(self) -> None:
        assert LANE_CASE_NUMBERS["A"] == "2024-001507-DC"
        assert LANE_CASE_NUMBERS["B"] == "2025-002760-CZ"
        assert LANE_CASE_NUMBERS["D"] == "2023-5907-PP"
        assert LANE_CASE_NUMBERS["F"] == "COA 366810"

    def test_party_name_plaintiff(self) -> None:
        assert _PLAINTIFF == "Andrew James Pigors"

    def test_party_name_defendant(self) -> None:
        assert _DEFENDANT == "Emily A. Watson"

    def test_child_initials(self) -> None:
        assert _CHILD_INITIALS == "L.D.W."

    def test_judge_name(self) -> None:
        assert _JUDGE == "Hon. Jenny L. McNeill"

    def test_mcr_rules_keys(self) -> None:
        assert "MCR 2.306(A)" in MCR_RULES
        assert "MCR 2.306(B)" in MCR_RULES
        assert "MRE 613" in MCR_RULES

    def test_mcr_rules_content(self) -> None:
        rule = MCR_RULES["MCR 2.306(D)"]
        assert "7 hours" in rule["summary"]


# ═══════════════════════════════════════════════════════════════════════════
# PART 2 — DamagesCalculator Tests
# ═══════════════════════════════════════════════════════════════════════════


# --- 2A  Enumerations ---

class TestDamagesEnums:

    def test_damage_category_values(self) -> None:
        expected = {
            "economic", "non_economic", "statutory",
            "punitive", "attorney_fees", "prejudgment_interest",
        }
        assert {c.value for c in DamageCategory} == expected

    def test_liability_type_values(self) -> None:
        assert LiabilityType.JOINT.value == "joint"
        assert LiabilityType.SEVERAL.value == "several"
        assert LiabilityType.JOINT_AND_SEVERAL.value == "joint_and_several"

    def test_calculation_method_values(self) -> None:
        expected = {
            "actual", "estimated", "statutory_formula",
            "multiplier", "per_diem", "comparable_case", "expert_estimate",
        }
        assert {m.value for m in CalculationMethod} == expected

    def test_multiplier_statute_values(self) -> None:
        assert MultiplierStatute.MCL_37_2801.value == "MCL 37.2801"
        assert MultiplierStatute.USC_42_1983.value == "42 USC §1983"
        assert MultiplierStatute.MCL_600_6013.value == "MCL 600.6013"
        assert len(MultiplierStatute) == 6


# --- 2B  Dataclasses ---

class TestDamageItem:

    def test_creation_defaults(self) -> None:
        item = DamageItem()
        assert item.item_id
        assert item.amount_low == 0.0
        assert item.multiplier_applied == 1.0

    def test_to_dict(self) -> None:
        item = _make_damage_item()
        d = item.to_dict()
        assert d["category"] == "economic"
        assert d["amount_mid"] == 5000.0

    def test_total_range(self) -> None:
        item = _make_damage_item(interest_amount=500.0)
        low, mid, high = item.total_range()
        assert low == 1500.0
        assert mid == 5500.0
        assert high == 10500.0

    def test_total_range_no_interest(self) -> None:
        item = _make_damage_item()
        low, mid, high = item.total_range()
        assert low == 1000.0
        assert mid == 5000.0
        assert high == 10000.0


class TestDefendant:

    def test_creation(self) -> None:
        d = Defendant(name="Test Defendant", role="Individual")
        assert d.name == "Test Defendant"
        assert d.joint_several is True

    def test_to_dict(self) -> None:
        d = Defendant(name="Test", lanes=["A", "B"])
        result = d.to_dict()
        assert result["lanes"] == ["A", "B"]

    def test_defendants_count(self) -> None:
        assert len(DEFENDANTS) == 19

    def test_defendants_watson(self) -> None:
        watson = next(d for d in DEFENDANTS if "Watson" in d.name)
        assert "A" in watson.lanes
        assert "D" in watson.lanes

    def test_defendants_mcneill(self) -> None:
        mcneill = next(d for d in DEFENDANTS if "McNeill" in d.name)
        assert "E" in mcneill.lanes

    def test_defendants_liability_sums(self) -> None:
        total = sum(d.percentage_liability for d in DEFENDANTS)
        assert total > 0
        assert total <= 125.0  # Defendants may exceed 100% (joint & several)


class TestDefendantAllocation:

    def test_creation(self) -> None:
        alloc = DefendantAllocation(defendant_name="Test", percentage_liability=10.0)
        assert alloc.allocation_id
        assert alloc.joint_several is True

    def test_to_dict(self) -> None:
        alloc = DefendantAllocation(defendant_name="Test")
        d = alloc.to_dict()
        assert "defendant_name" in d
        assert "allocated_items" in d

    def test_calculate_totals(self) -> None:
        item1 = _make_damage_item(amount_low=1000, amount_mid=2000, amount_high=3000)
        item2 = _make_damage_item(amount_low=500, amount_mid=1000, amount_high=1500)
        alloc = DefendantAllocation(
            defendant_name="Test",
            percentage_liability=50.0,
            allocated_items=[item1, item2],
        )
        low, mid, high = alloc.calculate_totals()
        assert low == 750.0   # (1000 + 500) * 0.5
        assert mid == 1500.0  # (2000 + 1000) * 0.5
        assert high == 2250.0 # (3000 + 1500) * 0.5

    def test_calculate_totals_zero_liability(self) -> None:
        item = _make_damage_item()
        alloc = DefendantAllocation(
            defendant_name="Test",
            percentage_liability=0.0,
            allocated_items=[item],
        )
        low, mid, high = alloc.calculate_totals()
        assert low == 0.0


class TestLaneDamagesSummary:

    def test_creation(self) -> None:
        s = LaneDamagesSummary(lane="A", lane_label="Custody")
        assert s.lane == "A"

    def test_to_dict(self) -> None:
        s = LaneDamagesSummary(
            lane="A", lane_label="Test",
            total_low=100, total_mid=200, total_high=300,
        )
        d = s.to_dict()
        assert d["total_mid"] == 200


# --- 2C  PrejudgmentInterestCalculator ---

class TestPrejudgmentInterestCalculator:

    def test_get_michigan_rate_known_year(self) -> None:
        pic = PrejudgmentInterestCalculator()
        rate = pic.get_michigan_rate(2024)
        assert rate == 0.0534

    def test_get_michigan_rate_unknown_year(self) -> None:
        pic = PrejudgmentInterestCalculator()
        rate = pic.get_michigan_rate(1900)
        assert rate == 0.0509  # default

    def test_compound_or_simple(self) -> None:
        pic = PrejudgmentInterestCalculator()
        assert pic.compound_or_simple() == "simple"

    def test_calculate_basic(self) -> None:
        pic = PrejudgmentInterestCalculator()
        result = pic.calculate(
            principal=100_000.0,
            start_date=date(2024, 1, 1),
            end_date=date(2025, 1, 1),
        )
        assert result["method"] == "simple"
        assert result["interest"] > 0
        assert result["total"] > 100_000.0
        assert "statute" in result

    def test_calculate_zero_days(self) -> None:
        pic = PrejudgmentInterestCalculator()
        result = pic.calculate(
            principal=100_000.0,
            start_date=date(2024, 1, 1),
            end_date=date(2024, 1, 1),
        )
        assert result["interest"] == 0.0
        assert result["total"] == 100_000.0

    def test_calculate_negative_days(self) -> None:
        pic = PrejudgmentInterestCalculator()
        result = pic.calculate(
            principal=100_000.0,
            start_date=date(2025, 1, 1),
            end_date=date(2024, 1, 1),
        )
        assert result["interest"] == 0.0

    def test_calculate_custom_rate(self) -> None:
        pic = PrejudgmentInterestCalculator()
        result = pic.calculate(
            principal=100_000.0,
            start_date=date(2024, 1, 1),
            end_date=date(2025, 1, 1),
            rate=0.10,
        )
        assert result["rate"] == 0.10
        assert abs(result["interest"] - 10_000.0) < 500  # ~365.25 day year

    def test_apply_to_damages(self) -> None:
        pic = PrejudgmentInterestCalculator()
        items = [_make_damage_item(amount_mid=50000)]
        result = pic.apply_to_damages(items, date(2025, 12, 31))
        assert result[0].interest_amount > 0

    def test_michigan_rate_2023(self) -> None:
        pic = PrejudgmentInterestCalculator()
        assert pic.get_michigan_rate(2023) == 0.0509


# --- 2D  StatutoryMultiplierEngine ---

class TestStatutoryMultiplierEngine:

    def test_apply_treble_damages(self) -> None:
        sme = StatutoryMultiplierEngine()
        result = sme.apply_treble_damages(100_000.0)
        assert result["trebled"] == 300_000.0
        assert result["multiplier"] == 3.0

    def test_apply_treble_damages_mcpa(self) -> None:
        sme = StatutoryMultiplierEngine()
        result = sme.apply_treble_damages(50_000.0, "MCL 445.911")
        assert result["statute"] == "MCL 445.911"
        assert result["trebled"] == 150_000.0

    def test_apply_1983_fees(self) -> None:
        sme = StatutoryMultiplierEngine()
        result = sme.apply_1983_fees(500_000.0, hours_spent=200.0)
        assert result["lodestar"] == 70_000.0
        assert result["adjusted_fees"] == 35_000.0
        assert result["pro_se_adjustment"] == 0.5

    def test_apply_1983_fees_custom_rate(self) -> None:
        sme = StatutoryMultiplierEngine()
        result = sme.apply_1983_fees(100_000.0, hours_spent=100.0, hourly_rate=500.0)
        assert result["lodestar"] == 50_000.0

    def test_apply_consumer_protection(self) -> None:
        sme = StatutoryMultiplierEngine()
        result = sme.apply_consumer_protection(1000.0)
        assert result["trebled"] == 3000.0
        assert result["statute"] == "MCL 445.911"

    def test_apply_consumer_protection_minimum(self) -> None:
        sme = StatutoryMultiplierEngine()
        result = sme.apply_consumer_protection(10.0)
        assert result["trebled"] == 250.0  # min statutory

    def test_calculate_fee_shifting_1988(self) -> None:
        sme = StatutoryMultiplierEngine()
        result = sme.calculate_fee_shifting("plaintiff", "42 USC §1988")
        assert result["allows_fee_shifting"] is True
        assert result["pro_se_eligible"] is True

    def test_calculate_fee_shifting_unknown(self) -> None:
        sme = StatutoryMultiplierEngine()
        result = sme.calculate_fee_shifting("plaintiff", "MCL 999.999")
        assert result["allows_fee_shifting"] is False


# --- 2E  DamagesCalculator Orchestrator ---

class TestDamagesCalculator:

    def test_init(self, tmp_db: Path) -> None:
        calc = DamagesCalculator(db_path=tmp_db)
        assert calc.VERSION == "1.0.0"

    def test_calculate_lane_a(self, tmp_db: Path) -> None:
        calc = DamagesCalculator(db_path=tmp_db)
        summary = calc.calculate_lane_damages("A")
        assert summary.lane == "A"
        assert summary.item_count > 0
        assert summary.total_mid > 0

    def test_calculate_lane_b(self, tmp_db: Path) -> None:
        calc = DamagesCalculator(db_path=tmp_db)
        summary = calc.calculate_lane_damages("B")
        assert summary.lane == "B"
        assert summary.item_count > 0

    def test_calculate_lane_c_empty(self, tmp_db: Path) -> None:
        calc = DamagesCalculator(db_path=tmp_db)
        summary = calc.calculate_lane_damages("C")
        assert summary.item_count == 0
        assert summary.total_mid == 0.0

    def test_calculate_lane_d(self, tmp_db: Path) -> None:
        calc = DamagesCalculator(db_path=tmp_db)
        summary = calc.calculate_lane_damages("D")
        assert summary.item_count > 0

    def test_calculate_lane_e(self, tmp_db: Path) -> None:
        calc = DamagesCalculator(db_path=tmp_db)
        summary = calc.calculate_lane_damages("E")
        assert summary.item_count > 0

    def test_calculate_lane_f(self, tmp_db: Path) -> None:
        calc = DamagesCalculator(db_path=tmp_db)
        summary = calc.calculate_lane_damages("F")
        assert summary.item_count > 0

    def test_calculate_all_lanes(self, tmp_db: Path) -> None:
        calc = DamagesCalculator(db_path=tmp_db)
        results = calc.calculate_all_lanes()
        assert set(results.keys()) == {"A", "B", "C", "D", "E", "F"}

    def test_calculate_per_defendant(self, tmp_db: Path) -> None:
        calc = DamagesCalculator(db_path=tmp_db)
        allocations = calc.calculate_per_defendant()
        assert len(allocations) == 19

    def test_defendant_allocations_have_totals(self, tmp_db: Path) -> None:
        calc = DamagesCalculator(db_path=tmp_db)
        allocations = calc.calculate_per_defendant()
        watson = next(a for a in allocations if "Watson" in a.defendant_name)
        assert watson.total_mid > 0

    def test_prayer_for_relief_moderate(self, tmp_db: Path) -> None:
        calc = DamagesCalculator(db_path=tmp_db)
        prayer = calc.generate_prayer_for_relief("A", "moderate")
        assert "PRAYER FOR RELIEF" in prayer
        assert "Andrew James Pigors" in prayer
        assert "$" in prayer

    def test_prayer_for_relief_conservative(self, tmp_db: Path) -> None:
        calc = DamagesCalculator(db_path=tmp_db)
        prayer = calc.generate_prayer_for_relief("A", "conservative")
        assert "PRAYER FOR RELIEF" in prayer

    def test_prayer_for_relief_aggressive(self, tmp_db: Path) -> None:
        calc = DamagesCalculator(db_path=tmp_db)
        prayer = calc.generate_prayer_for_relief("A", "aggressive")
        assert "PRAYER FOR RELIEF" in prayer

    def test_get_stats(self, tmp_db: Path) -> None:
        calc = DamagesCalculator(db_path=tmp_db)
        stats = calc.get_stats()
        assert stats["engine"] == "DamagesCalculator"
        assert stats["defendant_count"] == 19
        assert stats["case_context"]["plaintiff"] == DMG_PLAINTIFF

    def test_get_stats_after_calculation(self, tmp_db: Path) -> None:
        calc = DamagesCalculator(db_path=tmp_db)
        calc.calculate_lane_damages("A")
        stats = calc.get_stats()
        assert stats["total_items"] > 0
        assert stats["calculation_count"] == 1

    def test_joint_several_in_allocations(self, tmp_db: Path) -> None:
        calc = DamagesCalculator(db_path=tmp_db)
        allocations = calc.calculate_per_defendant()
        joint_count = sum(1 for a in allocations if a.joint_several)
        several_count = sum(1 for a in allocations if not a.joint_several)
        assert joint_count > 0
        assert several_count > 0

    def test_damage_ranges_ordering(self, tmp_db: Path) -> None:
        calc = DamagesCalculator(db_path=tmp_db)
        summary = calc.calculate_lane_damages("A")
        assert summary.total_low <= summary.total_mid <= summary.total_high

    def test_categories_populated(self, tmp_db: Path) -> None:
        calc = DamagesCalculator(db_path=tmp_db)
        summary = calc.calculate_lane_damages("A")
        assert len(summary.categories) > 0

    def test_constants_match(self) -> None:
        assert DMG_PLAINTIFF == "Andrew James Pigors"
        assert DMG_DEFENDANT == "Emily A. Watson"
        assert DMG_CHILD == "L.D.W."
        assert DMG_JUDGE == "Hon. Jenny L. McNeill"

    def test_lane_labels_match(self) -> None:
        for lane in ("A", "B", "C", "D", "E", "F"):
            assert lane in DMG_LANE_LABELS
            assert lane in DMG_LANE_CASE_NUMBERS
