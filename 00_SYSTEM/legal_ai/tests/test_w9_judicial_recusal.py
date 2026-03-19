# -*- coding: utf-8 -*-
"""Wave-9 Tests — JudicialRecusalEngine
========================================
Comprehensive pytest suite for judicial_recusal_engine.py.

80+ tests covering enums (BiasIndicatorType, RecusalGround, MotionType,
MotionOutcome, CanonViolation, DocumentationLevel, PatternLevel,
RecommendedAction), dataclasses (BiasIndicator, RecusalMotion,
JTCComplaint, RecusalReport), BiasScorer, RecusalAnalyzer,
JTCComplaintBuilder, and the JudicialRecusalEngine orchestrator.

• Zero network / zero real DB — all DB interactions use temp SQLite
• tempfile + tmp_path for filesystem isolation
• unittest.mock.patch for isolation
• Independent tests, no ordering dependencies
"""
from __future__ import annotations

import json
import pathlib
import sqlite3
import sys
import uuid
from datetime import datetime, timezone
from typing import Any, Dict, List
from unittest.mock import MagicMock, patch

import pytest

# ---------------------------------------------------------------------------
# Import targets
# ---------------------------------------------------------------------------
_THIS_DIR = pathlib.Path(__file__).resolve().parent
_LEGAL_AI_DIR = _THIS_DIR.parent
if str(_LEGAL_AI_DIR) not in sys.path:
    sys.path.insert(0, str(_LEGAL_AI_DIR))

from judicial_recusal_engine import (
    BiasIndicatorType,
    RecusalGround,
    MotionType,
    MotionOutcome,
    CanonViolation,
    DocumentationLevel,
    PatternLevel,
    RecommendedAction,
    BiasIndicator,
    RecusalMotion,
    JTCComplaint,
    RecusalReport,
    BiasScorer,
    RecusalAnalyzer,
    JTCComplaintBuilder,
    JudicialRecusalEngine,
    _classify_score,
    _recommend_action,
    _PLAINTIFF,
    _PLAINTIFF_ADDRESS,
    _DEFENDANT,
    _CHILD_INITIALS,
    _JUDGE,
    _COURT,
    _CASE_NUMBER,
    _LANE,
    _JTC_ADDRESS,
    _SCORE_THRESHOLDS,
)


# ═══════════════════════════════════════════════════════════════════════════
# Fixtures
# ═══════════════════════════════════════════════════════════════════════════

@pytest.fixture
def sample_indicators() -> List[BiasIndicator]:
    """A diverse set of bias indicators for scoring tests."""
    return [
        BiasIndicator(
            incident_date="2024-07-15",
            category=BiasIndicatorType.VERBAL,
            description="Dismissive comment about pro se filings",
            mcr_ground=RecusalGround.PERSONAL_BIAS,
            canon_violated=CanonViolation.CANON_3A_4,
            severity=2,
            documentation=DocumentationLevel.TRANSCRIPT_CONFIRMED,
            pattern=PatternLevel.RECURRING,
            transcript_ref="Tr. 7/15/2024 p.12:5-15",
        ),
        BiasIndicator(
            incident_date="2024-08-20",
            category=BiasIndicatorType.EX_PARTE,
            description="Unscheduled meeting between judge and opposing counsel",
            mcr_ground=RecusalGround.APPEARANCE_OF_IMPROPRIETY,
            canon_violated=CanonViolation.CANON_3A_7,
            severity=3,
            documentation=DocumentationLevel.WITNESS_CORROBORATED,
            pattern=PatternLevel.ISOLATED,
            evidence_refs=["WITNESS-001"],
        ),
        BiasIndicator(
            incident_date="2024-09-05",
            category=BiasIndicatorType.PROCEDURAL,
            description="Denied plaintiff motion without reading it",
            mcr_ground=RecusalGround.PERSONAL_BIAS,
            canon_violated=CanonViolation.CANON_3A_1,
            severity=2,
            documentation=DocumentationLevel.TRANSCRIPT_CONFIRMED,
            pattern=PatternLevel.SYSTEMATIC,
            transcript_ref="Tr. 9/5/2024 p.45:10-20",
        ),
        BiasIndicator(
            incident_date="2024-10-01",
            category=BiasIndicatorType.EVIDENTIARY,
            description="Excluded plaintiff exhibit without basis",
            severity=2,
            documentation=DocumentationLevel.TRANSCRIPT_CONFIRMED,
            pattern=PatternLevel.RECURRING,
        ),
        BiasIndicator(
            incident_date="2024-10-15",
            category=BiasIndicatorType.DEMEANOR,
            description="Eye-rolling and visible irritation during testimony",
            severity=1,
            documentation=DocumentationLevel.SELF_REPORTED,
            pattern=PatternLevel.RECURRING,
        ),
    ]


@pytest.fixture
def single_indicator() -> BiasIndicator:
    return BiasIndicator(
        incident_date="2024-07-15",
        category=BiasIndicatorType.VERBAL,
        description="Dismissive comment",
        severity=1,
        documentation=DocumentationLevel.SELF_REPORTED,
        pattern=PatternLevel.ISOLATED,
    )


@pytest.fixture
def tmp_db_with_indicators(tmp_path) -> pathlib.Path:
    """Temp database with judicial_bias_indicators table."""
    db_file = tmp_path / "test_recusal.db"
    conn = sqlite3.connect(str(db_file))
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("""
        CREATE TABLE judicial_bias_indicators (
            indicator_id    TEXT PRIMARY KEY,
            judge_name      TEXT,
            court           TEXT,
            incident_date   TEXT NOT NULL,
            category        TEXT NOT NULL,
            description     TEXT NOT NULL,
            mcr_ground      TEXT,
            canon_violated  TEXT,
            severity        INTEGER,
            documentation   TEXT DEFAULT 'self_reported',
            pattern_level   TEXT DEFAULT 'isolated',
            evidence_refs   TEXT,
            witnesses       TEXT,
            transcript_ref  TEXT,
            lane            TEXT DEFAULT 'E',
            case_number     TEXT DEFAULT '2024-001507-DC',
            created_at      TEXT DEFAULT (datetime('now'))
        )
    """)
    conn.executemany(
        "INSERT INTO judicial_bias_indicators "
        "(indicator_id, judge_name, court, incident_date, category, description, "
        "mcr_ground, severity, documentation, pattern_level, transcript_ref) "
        "VALUES (?,?,?,?,?,?,?,?,?,?,?)",
        [
            ("IND001", "Hon. Jenny L. McNeill", "14th Circuit Court",
             "2024-07-15", "verbal", "Dismissive comment",
             "MCR 2.003(C)(1)(a)", 2, "transcript_confirmed", "recurring",
             "Tr. 7/15/2024 p.12"),
            ("IND002", "Hon. Jenny L. McNeill", "14th Circuit Court",
             "2024-08-20", "ex_parte", "Unscheduled meeting",
             "MCR 2.003(C)(1)(g)", 3, "witness_corroborated", "isolated",
             ""),
        ],
    )
    conn.commit()
    conn.close()
    return db_file


# ═══════════════════════════════════════════════════════════════════════════
# Enum Tests
# ═══════════════════════════════════════════════════════════════════════════

class TestBiasIndicatorType:
    def test_all_categories(self):
        expected = {"verbal", "procedural", "evidentiary", "ex_parte",
                    "temporal", "outcome", "demeanor"}
        assert {b.value for b in BiasIndicatorType} == expected

    def test_label_property(self):
        label = BiasIndicatorType.VERBAL.label
        assert "verbal" in label.lower() or "Verbal" in label

    def test_label_for_all(self):
        for bt in BiasIndicatorType:
            assert bt.label, f"No label for {bt.name}"

    def test_ex_parte_label(self):
        assert "ex parte" in BiasIndicatorType.EX_PARTE.label.lower()


class TestRecusalGround:
    def test_all_grounds(self):
        assert len(RecusalGround) == 7

    def test_mcr_2003_prefix(self):
        for g in RecusalGround:
            assert g.value.startswith("MCR 2.003(C)(1)")

    def test_label_property(self):
        label = RecusalGround.PERSONAL_BIAS.label
        assert "bias" in label.lower() or "prejudice" in label.lower()

    def test_label_for_all(self):
        for g in RecusalGround:
            assert g.label, f"No label for {g.name}"

    def test_appearance_of_impropriety(self):
        assert RecusalGround.APPEARANCE_OF_IMPROPRIETY.value == "MCR 2.003(C)(1)(g)"


class TestMotionType:
    def test_values(self):
        assert MotionType.PEREMPTORY.value == "peremptory"
        assert MotionType.FOR_CAUSE.value == "for_cause"


class TestMotionOutcome:
    def test_values(self):
        expected = {"granted", "denied", "pending", "withdrawn"}
        assert {o.value for o in MotionOutcome} == expected


class TestCanonViolation:
    def test_all_canons(self):
        assert len(CanonViolation) == 8

    def test_subject_property(self):
        subj = CanonViolation.CANON_3A_7.subject
        assert "ex parte" in subj.lower()

    def test_subject_for_all(self):
        for c in CanonViolation:
            assert c.subject, f"No subject for {c.name}"

    def test_canon_2a(self):
        assert CanonViolation.CANON_2A.subject
        assert "impropriety" in CanonViolation.CANON_2A.subject.lower()


class TestDocumentationLevel:
    def test_multiplier_transcript(self):
        assert DocumentationLevel.TRANSCRIPT_CONFIRMED.multiplier == 3

    def test_multiplier_witness(self):
        assert DocumentationLevel.WITNESS_CORROBORATED.multiplier == 2

    def test_multiplier_self(self):
        assert DocumentationLevel.SELF_REPORTED.multiplier == 1


class TestPatternLevel:
    def test_multiplier_isolated(self):
        assert PatternLevel.ISOLATED.multiplier == 1

    def test_multiplier_recurring(self):
        assert PatternLevel.RECURRING.multiplier == 2

    def test_multiplier_systematic(self):
        assert PatternLevel.SYSTEMATIC.multiplier == 3


class TestRecommendedAction:
    def test_values(self):
        expected = {"document_only", "for_cause_motion", "motion_plus_jtc", "emergency_all"}
        assert {a.value for a in RecommendedAction} == expected


# ═══════════════════════════════════════════════════════════════════════════
# Dataclass Tests
# ═══════════════════════════════════════════════════════════════════════════

class TestBiasIndicator:
    def test_default_values(self):
        ind = BiasIndicator()
        assert ind.judge_name == _JUDGE
        assert ind.court == _COURT
        assert ind.severity == 1
        assert ind.documentation == DocumentationLevel.SELF_REPORTED
        assert ind.pattern == PatternLevel.ISOLATED
        assert ind.case_number == _CASE_NUMBER
        assert ind.lane == _LANE

    def test_weighted_score(self):
        ind = BiasIndicator(
            severity=2,
            documentation=DocumentationLevel.TRANSCRIPT_CONFIRMED,
            pattern=PatternLevel.RECURRING,
        )
        # 2 * 3 * 2 = 12
        assert ind.weighted_score == 12

    def test_weighted_score_minimum(self):
        ind = BiasIndicator(
            severity=1,
            documentation=DocumentationLevel.SELF_REPORTED,
            pattern=PatternLevel.ISOLATED,
        )
        assert ind.weighted_score == 1

    def test_weighted_score_maximum(self):
        ind = BiasIndicator(
            severity=3,
            documentation=DocumentationLevel.TRANSCRIPT_CONFIRMED,
            pattern=PatternLevel.SYSTEMATIC,
        )
        assert ind.weighted_score == 27

    def test_to_dict(self):
        ind = BiasIndicator(
            category=BiasIndicatorType.EX_PARTE,
            mcr_ground=RecusalGround.APPEARANCE_OF_IMPROPRIETY,
            canon_violated=CanonViolation.CANON_3A_7,
        )
        d = ind.to_dict()
        assert d["category"] == "ex_parte"
        assert d["mcr_ground"] == "MCR 2.003(C)(1)(g)"
        assert d["canon_violated"] == "Canon 3A(7)"
        assert "weighted_score" in d

    def test_to_dict_none_optional(self):
        ind = BiasIndicator()
        d = ind.to_dict()
        assert d["mcr_ground"] is None
        assert d["canon_violated"] is None

    def test_unique_ids(self):
        i1 = BiasIndicator()
        i2 = BiasIndicator()
        assert i1.indicator_id != i2.indicator_id


class TestRecusalMotion:
    def test_default_values(self):
        m = RecusalMotion()
        assert m.judge_name == _JUDGE
        assert m.motion_type == MotionType.FOR_CAUSE
        assert m.outcome == MotionOutcome.PENDING
        assert m.appealed is False
        assert m.case_number == _CASE_NUMBER

    def test_to_dict(self):
        m = RecusalMotion(
            motion_type=MotionType.PEREMPTORY,
            mcr_grounds=[RecusalGround.PERSONAL_BIAS, RecusalGround.APPEARANCE_OF_IMPROPRIETY],
            outcome=MotionOutcome.DENIED,
        )
        d = m.to_dict()
        assert d["motion_type"] == "peremptory"
        assert "MCR 2.003(C)(1)(a)" in d["mcr_grounds"]
        assert d["outcome"] == "denied"

    def test_to_dict_empty_grounds(self):
        m = RecusalMotion()
        d = m.to_dict()
        assert d["mcr_grounds"] == []


class TestJTCComplaint:
    def test_default_values(self):
        c = JTCComplaint()
        assert c.judge_name == _JUDGE
        assert c.court == _COURT
        assert c.complainant == _PLAINTIFF
        assert c.complainant_address == _PLAINTIFF_ADDRESS

    def test_to_dict(self):
        c = JTCComplaint(
            canon_violations=[CanonViolation.CANON_2A, CanonViolation.CANON_3A_7],
        )
        d = c.to_dict()
        assert "Canon 2A" in d["canon_violations"]
        assert "Canon 3A(7)" in d["canon_violations"]

    def test_prepared_date_format(self):
        c = JTCComplaint()
        # Should be YYYY-MM-DD
        assert len(c.prepared_date) == 10
        assert c.prepared_date[4] == "-"


class TestRecusalReport:
    def test_default_values(self):
        r = RecusalReport()
        assert r.judge_name == _JUDGE
        assert r.court == _COURT
        assert r.case_number == _CASE_NUMBER
        assert r.peremptory_available is True

    def test_to_dict(self):
        r = RecusalReport(
            total_indicators=5,
            composite_score=30,
            score_classification="Severe Bias",
        )
        d = r.to_dict()
        assert d["total_indicators"] == 5
        assert d["composite_score"] == 30
        assert "report_id" in d
        assert "indicators" in d
        assert "motions" in d


# ═══════════════════════════════════════════════════════════════════════════
# Helper Function Tests
# ═══════════════════════════════════════════════════════════════════════════

class TestClassifyScore:
    def test_within_discretion(self):
        assert _classify_score(0) == "Within Discretion"
        assert _classify_score(10) == "Within Discretion"

    def test_moderate_bias(self):
        assert _classify_score(11) == "Moderate Bias"
        assert _classify_score(25) == "Moderate Bias"

    def test_severe_bias(self):
        assert _classify_score(26) == "Severe Bias"
        assert _classify_score(50) == "Severe Bias"

    def test_extreme_bias(self):
        assert _classify_score(51) == "Extreme Bias"
        assert _classify_score(100) == "Extreme Bias"


class TestRecommendActionFunc:
    def test_document_only(self):
        assert _recommend_action(5) == RecommendedAction.DOCUMENT_ONLY
        assert _recommend_action(10) == RecommendedAction.DOCUMENT_ONLY

    def test_for_cause_motion(self):
        assert _recommend_action(15) == RecommendedAction.FOR_CAUSE_MOTION
        assert _recommend_action(25) == RecommendedAction.FOR_CAUSE_MOTION

    def test_motion_plus_jtc(self):
        assert _recommend_action(30) == RecommendedAction.MOTION_PLUS_JTC
        assert _recommend_action(50) == RecommendedAction.MOTION_PLUS_JTC

    def test_emergency_all(self):
        assert _recommend_action(51) == RecommendedAction.EMERGENCY_ALL
        assert _recommend_action(200) == RecommendedAction.EMERGENCY_ALL


# ═══════════════════════════════════════════════════════════════════════════
# BiasScorer Tests
# ═══════════════════════════════════════════════════════════════════════════

class TestBiasScorer:
    def test_compute_score_empty(self):
        scorer = BiasScorer()
        assert scorer.compute_score([]) == 0

    def test_compute_score(self, sample_indicators):
        scorer = BiasScorer()
        score = scorer.compute_score(sample_indicators)
        assert score > 0

    def test_compute_score_matches_sum(self, sample_indicators):
        scorer = BiasScorer()
        expected = sum(ind.weighted_score for ind in sample_indicators)
        assert scorer.compute_score(sample_indicators) == expected

    def test_category_breakdown(self, sample_indicators):
        scorer = BiasScorer()
        breakdown = scorer.category_breakdown(sample_indicators)
        assert "verbal" in breakdown
        assert "ex_parte" in breakdown

    def test_category_breakdown_empty(self):
        scorer = BiasScorer()
        assert scorer.category_breakdown([]) == {}

    def test_ground_breakdown(self, sample_indicators):
        scorer = BiasScorer()
        breakdown = scorer.ground_breakdown(sample_indicators)
        assert isinstance(breakdown, dict)

    def test_ground_breakdown_skips_none(self, single_indicator):
        """Indicator with no mcr_ground should not appear in ground breakdown."""
        scorer = BiasScorer()
        breakdown = scorer.ground_breakdown([single_indicator])
        assert breakdown == {}

    def test_detect_patterns_systematic(self):
        scorer = BiasScorer()
        indicators = [
            BiasIndicator(category=BiasIndicatorType.PROCEDURAL)
            for _ in range(5)
        ]
        patterns = scorer.detect_patterns(indicators)
        assert patterns["procedural"] == PatternLevel.SYSTEMATIC

    def test_detect_patterns_recurring(self):
        scorer = BiasScorer()
        indicators = [
            BiasIndicator(category=BiasIndicatorType.VERBAL)
            for _ in range(3)
        ]
        patterns = scorer.detect_patterns(indicators)
        assert patterns["verbal"] == PatternLevel.RECURRING

    def test_detect_patterns_isolated(self):
        scorer = BiasScorer()
        indicators = [BiasIndicator(category=BiasIndicatorType.DEMEANOR)]
        patterns = scorer.detect_patterns(indicators)
        assert patterns["demeanor"] == PatternLevel.ISOLATED

    def test_get_stats(self):
        scorer = BiasScorer()
        stats = scorer.get_stats()
        assert stats["component"] == "BiasScorer"
        assert stats["bias_categories"] == len(BiasIndicatorType)
        assert stats["recusal_grounds"] == len(RecusalGround)


# ═══════════════════════════════════════════════════════════════════════════
# RecusalAnalyzer Tests
# ═══════════════════════════════════════════════════════════════════════════

class TestRecusalAnalyzer:
    def test_map_grounds_explicit(self, sample_indicators):
        analyzer = RecusalAnalyzer()
        mapping = analyzer.map_grounds(sample_indicators)
        assert RecusalGround.PERSONAL_BIAS in mapping
        assert RecusalGround.APPEARANCE_OF_IMPROPRIETY in mapping

    def test_map_grounds_fallback(self):
        """Indicator without explicit mcr_ground uses category-based mapping."""
        analyzer = RecusalAnalyzer()
        ind = BiasIndicator(category=BiasIndicatorType.EX_PARTE)
        mapping = analyzer.map_grounds([ind])
        assert RecusalGround.PERSONAL_KNOWLEDGE in mapping or \
               RecusalGround.APPEARANCE_OF_IMPROPRIETY in mapping

    def test_map_grounds_empty(self):
        analyzer = RecusalAnalyzer()
        mapping = analyzer.map_grounds([])
        assert mapping == {}

    def test_prepare_motion_for_cause(self, sample_indicators):
        analyzer = RecusalAnalyzer()
        motion = analyzer.prepare_motion(sample_indicators, MotionType.FOR_CAUSE)
        assert motion.motion_type == MotionType.FOR_CAUSE
        assert len(motion.mcr_grounds) > 0
        assert len(motion.supporting_indicators) == len(sample_indicators)
        assert motion.affidavit_text != ""

    def test_prepare_motion_peremptory(self, sample_indicators):
        analyzer = RecusalAnalyzer()
        motion = analyzer.prepare_motion(sample_indicators, MotionType.PEREMPTORY)
        assert motion.motion_type == MotionType.PEREMPTORY
        assert motion.affidavit_text == ""

    def test_affidavit_contains_case_number(self, sample_indicators):
        analyzer = RecusalAnalyzer()
        motion = analyzer.prepare_motion(sample_indicators, MotionType.FOR_CAUSE)
        assert _CASE_NUMBER in motion.affidavit_text

    def test_affidavit_contains_plaintiff(self, sample_indicators):
        analyzer = RecusalAnalyzer()
        motion = analyzer.prepare_motion(sample_indicators, MotionType.FOR_CAUSE)
        assert _PLAINTIFF in motion.affidavit_text

    def test_affidavit_contains_judge(self, sample_indicators):
        analyzer = RecusalAnalyzer()
        motion = analyzer.prepare_motion(sample_indicators, MotionType.FOR_CAUSE)
        assert _JUDGE in motion.affidavit_text

    def test_affidavit_references_transcript(self, sample_indicators):
        analyzer = RecusalAnalyzer()
        motion = analyzer.prepare_motion(sample_indicators, MotionType.FOR_CAUSE)
        assert "Tr." in motion.affidavit_text

    def test_affidavit_references_witnesses(self):
        analyzer = RecusalAnalyzer()
        ind = BiasIndicator(
            description="Saw something",
            witnesses=["John Doe", "Jane Doe"],
        )
        motion = analyzer.prepare_motion([ind], MotionType.FOR_CAUSE)
        assert "John Doe" in motion.affidavit_text

    def test_get_stats(self):
        analyzer = RecusalAnalyzer()
        stats = analyzer.get_stats()
        assert stats["component"] == "RecusalAnalyzer"
        assert stats["ground_mappings"] > 0


# ═══════════════════════════════════════════════════════════════════════════
# JTCComplaintBuilder Tests
# ═══════════════════════════════════════════════════════════════════════════

class TestJTCComplaintBuilder:
    def test_build_complaint(self, sample_indicators):
        builder = JTCComplaintBuilder()
        complaint = builder.build_complaint(sample_indicators)
        assert len(complaint.factual_allegations) == len(sample_indicators)
        assert len(complaint.canon_violations) > 0
        assert complaint.judge_name == _JUDGE

    def test_build_complaint_extracts_canons(self, sample_indicators):
        builder = JTCComplaintBuilder()
        complaint = builder.build_complaint(sample_indicators)
        canon_values = {c.value for c in complaint.canon_violations}
        assert "Canon 3A(4)" in canon_values or "Canon 3A(7)" in canon_values

    def test_build_complaint_default_canons(self):
        """If no explicit canons, derive from category."""
        builder = JTCComplaintBuilder()
        indicators = [
            BiasIndicator(
                category=BiasIndicatorType.EX_PARTE,
                description="Ex parte contact",
            ),
        ]
        complaint = builder.build_complaint(indicators)
        canon_values = {c.value for c in complaint.canon_violations}
        assert "Canon 3A(7)" in canon_values

    def test_build_complaint_demeanor_default(self):
        builder = JTCComplaintBuilder()
        indicators = [
            BiasIndicator(
                category=BiasIndicatorType.DEMEANOR,
                description="Eye rolling",
            ),
        ]
        complaint = builder.build_complaint(indicators)
        canon_values = {c.value for c in complaint.canon_violations}
        assert "Canon 3A(4)" in canon_values

    def test_to_text_contains_jtc_address(self, sample_indicators):
        builder = JTCComplaintBuilder()
        complaint = builder.build_complaint(sample_indicators)
        text = builder.to_text(complaint)
        assert "Judicial Tenure Commission" in text
        assert "Detroit" in text

    def test_to_text_contains_mcr_9104(self, sample_indicators):
        builder = JTCComplaintBuilder()
        complaint = builder.build_complaint(sample_indicators)
        text = builder.to_text(complaint)
        assert "MCR 9.104" in text

    def test_to_text_contains_complainant(self, sample_indicators):
        builder = JTCComplaintBuilder()
        complaint = builder.build_complaint(sample_indicators)
        text = builder.to_text(complaint)
        assert _PLAINTIFF in text

    def test_to_text_perjury_affirmation(self, sample_indicators):
        builder = JTCComplaintBuilder()
        complaint = builder.build_complaint(sample_indicators)
        text = builder.to_text(complaint)
        assert "perjury" in text.lower()

    def test_get_stats(self):
        builder = JTCComplaintBuilder()
        stats = builder.get_stats()
        assert stats["component"] == "JTCComplaintBuilder"
        assert stats["canon_violations_tracked"] == len(CanonViolation)


# ═══════════════════════════════════════════════════════════════════════════
# JudicialRecusalEngine Orchestrator Tests
# ═══════════════════════════════════════════════════════════════════════════

class TestJudicialRecusalEngine:
    def test_add_indicator(self, single_indicator):
        engine = JudicialRecusalEngine(db_path=pathlib.Path("fake.db"))
        engine.add_indicator(single_indicator)
        stats = engine.get_stats()
        assert stats["indicators_loaded"] == 1

    def test_add_indicators(self, sample_indicators):
        engine = JudicialRecusalEngine(db_path=pathlib.Path("fake.db"))
        engine.add_indicators(sample_indicators)
        assert engine.get_stats()["indicators_loaded"] == 5

    def test_set_peremptory_used(self):
        engine = JudicialRecusalEngine(db_path=pathlib.Path("fake.db"))
        assert engine.get_stats()["peremptory_available"] is True
        engine.set_peremptory_used()
        assert engine.get_stats()["peremptory_available"] is False

    def test_analyse_low_score(self, single_indicator):
        engine = JudicialRecusalEngine(db_path=pathlib.Path("fake.db"))
        engine.add_indicator(single_indicator)
        report = engine.analyse()
        assert report.composite_score == single_indicator.weighted_score
        assert report.score_classification == "Within Discretion"
        assert report.recommended_action == "document_only"

    def test_analyse_high_score(self, sample_indicators):
        engine = JudicialRecusalEngine(db_path=pathlib.Path("fake.db"))
        engine.add_indicators(sample_indicators)
        report = engine.analyse()
        assert report.composite_score > 0
        assert report.total_indicators == 5

    def test_analyse_auto_motion(self, sample_indicators):
        """High enough score should auto-prepare a motion."""
        engine = JudicialRecusalEngine(db_path=pathlib.Path("fake.db"))
        engine.add_indicators(sample_indicators)
        report = engine.analyse()
        # With high-severity indicators the score should trigger motion preparation
        if report.composite_score > 10:
            assert len(report.motions) > 0

    def test_analyse_auto_jtc(self, sample_indicators):
        """Score above JTC threshold should auto-prepare complaint."""
        engine = JudicialRecusalEngine(db_path=pathlib.Path("fake.db"))
        engine.add_indicators(sample_indicators)
        report = engine.analyse()
        if report.composite_score > 25:
            assert report.jtc_complaint is not None

    def test_generate_report_markdown(self, sample_indicators):
        engine = JudicialRecusalEngine(db_path=pathlib.Path("fake.db"))
        engine.add_indicators(sample_indicators)
        md = engine.generate_report(fmt="markdown")
        assert "Judicial Disqualification" in md
        assert _JUDGE in md

    def test_generate_report_json(self, sample_indicators):
        engine = JudicialRecusalEngine(db_path=pathlib.Path("fake.db"))
        engine.add_indicators(sample_indicators)
        j = engine.generate_report(fmt="json")
        data = json.loads(j)
        assert "composite_score" in data
        assert "indicators" in data

    def test_scan_records_with_db(self, tmp_db_with_indicators):
        engine = JudicialRecusalEngine(db_path=tmp_db_with_indicators)
        count = engine.scan_records()
        assert count >= 2

    def test_scan_records_missing_db(self, tmp_path):
        engine = JudicialRecusalEngine(db_path=tmp_path / "nonexistent.db")
        count = engine.scan_records()
        assert count == 0

    def test_get_stats_before_analysis(self):
        engine = JudicialRecusalEngine(db_path=pathlib.Path("fake.db"))
        stats = engine.get_stats()
        assert stats["module"] == "judicial_recusal_engine"
        assert stats["report_generated"] is False
        assert stats["composite_score"] is None

    def test_get_stats_after_analysis(self, sample_indicators):
        engine = JudicialRecusalEngine(db_path=pathlib.Path("fake.db"))
        engine.add_indicators(sample_indicators)
        engine.analyse()
        stats = engine.get_stats()
        assert stats["report_generated"] is True
        assert stats["composite_score"] is not None

    def test_reset(self, sample_indicators):
        engine = JudicialRecusalEngine(db_path=pathlib.Path("fake.db"))
        engine.add_indicators(sample_indicators)
        engine.analyse()
        engine.reset()
        assert engine.get_stats()["indicators_loaded"] == 0
        assert engine.get_stats()["report_generated"] is False

    def test_lane_e_routing(self):
        assert _LANE == "E"

    def test_judge_mcneill_constants(self):
        assert _JUDGE == "Hon. Jenny L. McNeill"
        assert _COURT == "14th Circuit Court"
        assert _CASE_NUMBER == "2024-001507-DC"

    def test_party_names(self):
        assert _PLAINTIFF == "Andrew James Pigors"
        assert _DEFENDANT == "Emily A. Watson"
        assert _CHILD_INITIALS == "L.D.W."

    def test_jtc_address(self):
        assert "Judicial Tenure Commission" in _JTC_ADDRESS
        assert "Detroit" in _JTC_ADDRESS


# ═══════════════════════════════════════════════════════════════════════════
# Edge Cases
# ═══════════════════════════════════════════════════════════════════════════

class TestEdgeCases:
    def test_no_indicators_analysis(self):
        engine = JudicialRecusalEngine(db_path=pathlib.Path("fake.db"))
        report = engine.analyse()
        assert report.composite_score == 0
        assert report.score_classification == "Within Discretion"
        assert report.recommended_action == "document_only"
        assert len(report.motions) == 0
        assert report.jtc_complaint is None

    def test_single_indicator_score(self, single_indicator):
        engine = JudicialRecusalEngine(db_path=pathlib.Path("fake.db"))
        engine.add_indicator(single_indicator)
        report = engine.analyse()
        assert report.composite_score == 1
        assert report.total_indicators == 1

    def test_overwhelming_bias(self):
        """Many high-severity indicators should produce extreme classification."""
        indicators = [
            BiasIndicator(
                severity=3,
                documentation=DocumentationLevel.TRANSCRIPT_CONFIRMED,
                pattern=PatternLevel.SYSTEMATIC,
                description=f"Severe incident {i}",
                category=BiasIndicatorType.PROCEDURAL,
            )
            for i in range(10)
        ]
        engine = JudicialRecusalEngine(db_path=pathlib.Path("fake.db"))
        engine.add_indicators(indicators)
        report = engine.analyse()
        assert report.composite_score >= 270  # 10 * 3 * 3 * 3
        assert report.score_classification == "Extreme Bias"
        assert report.recommended_action == "emergency_all"
        assert report.jtc_complaint is not None
        assert len(report.motions) > 0

    def test_mixed_documentation_levels(self):
        indicators = [
            BiasIndicator(severity=2, documentation=DocumentationLevel.TRANSCRIPT_CONFIRMED),
            BiasIndicator(severity=2, documentation=DocumentationLevel.WITNESS_CORROBORATED),
            BiasIndicator(severity=2, documentation=DocumentationLevel.SELF_REPORTED),
        ]
        scorer = BiasScorer()
        # 2*3*1 + 2*2*1 + 2*1*1 = 6 + 4 + 2 = 12
        assert scorer.compute_score(indicators) == 12

    def test_report_to_dict_roundtrip(self, sample_indicators):
        engine = JudicialRecusalEngine(db_path=pathlib.Path("fake.db"))
        engine.add_indicators(sample_indicators)
        report = engine.analyse()
        d = report.to_dict()
        j = json.dumps(d, default=str)
        parsed = json.loads(j)
        assert parsed["composite_score"] == report.composite_score
        assert len(parsed["indicators"]) == len(report.indicators)

    def test_score_thresholds_cover_range(self):
        """Ensure thresholds are contiguous and cover 0 to high."""
        all_ranges = sorted(_SCORE_THRESHOLDS.values())
        assert all_ranges[0][0] == 0
        # Last upper bound is 9999 (effectively infinite)
        assert all_ranges[-1][1] >= 9999

    def test_category_breakdown_sums_to_total(self, sample_indicators):
        scorer = BiasScorer()
        total = scorer.compute_score(sample_indicators)
        breakdown = scorer.category_breakdown(sample_indicators)
        assert sum(breakdown.values()) == total

    def test_motion_has_all_indicator_ids(self, sample_indicators):
        analyzer = RecusalAnalyzer()
        motion = analyzer.prepare_motion(sample_indicators)
        for ind in sample_indicators:
            assert ind.indicator_id in motion.supporting_indicators
