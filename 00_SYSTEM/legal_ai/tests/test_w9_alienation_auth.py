# -*- coding: utf-8 -*-
"""Wave-9 Tests — ParentalAlienationDetector & EvidenceAuthenticator
=====================================================================
Comprehensive pytest suite for parental_alienation_detector.py (~60 tests)
and evidence_authenticator.py (~60 tests).

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
from datetime import date, datetime, timedelta, timezone
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

from parental_alienation_detector import (
    AlienationIndicator,
    Severity,
    FactorJImpact,
    EscalationTrend,
    ReportFormat,
    AlienationEvent,
    AlienationPattern,
    FactorJAssessment,
    TemporalAnalysis,
    AlienationReport,
    BehaviorCataloger,
    PatternAnalyzer,
    AlienationReporter,
    ParentalAlienationDetector,
    _classify_severity,
    _recommended_actions,
    _PLAINTIFF,
    _DEFENDANT,
    _CHILD_INITIALS,
    _JUDGE,
    _CASE_NUMBER,
    _LANE,
)

from evidence_authenticator import (
    AuthenticationMethod,
    EvidenceType,
    HearsayException,
    CustodyStatus,
    AuthStatus,
    BestEvidenceStatus,
    ChainOfCustodyEntry,
    EvidenceItem,
    AuthenticationRequirement,
    AuthenticationReport,
    AuthenticationAnalyzer,
    HearsayAnalyzer,
    FoundationBuilder,
    EvidenceAuthenticator,
    LANE_CASES,
    _DEFAULT_AUTH_METHODS,
    _DEFAULT_HEARSAY,
    _PLAINTIFF as EA_PLAINTIFF,
    _DEFENDANT as EA_DEFENDANT,
)


# ═══════════════════════════════════════════════════════════════════════════
# Fixtures
# ═══════════════════════════════════════════════════════════════════════════

@pytest.fixture
def sample_events() -> List[AlienationEvent]:
    """A diverse set of alienation events for pattern analysis."""
    return [
        AlienationEvent(
            event_date="2024-06-15",
            indicator=AlienationIndicator.CAMPAIGN_OF_DENIGRATION,
            severity=Severity.MODERATE,
            description="Child told targeted parent is 'bad'",
            evidence_refs=["DOC-001"],
        ),
        AlienationEvent(
            event_date="2024-07-20",
            indicator=AlienationIndicator.BORROWED_SCENARIOS,
            severity=Severity.MILD,
            description="Child used coached language",
            evidence_refs=["DOC-002"],
        ),
        AlienationEvent(
            event_date="2024-08-10",
            indicator=AlienationIndicator.SPREAD_TO_EXTENDED_FAMILY,
            severity=Severity.MODERATE,
            description="Child refused to see grandparents",
            evidence_refs=["DOC-003"],
        ),
        AlienationEvent(
            event_date="2024-09-01",
            indicator=AlienationIndicator.CAMPAIGN_OF_DENIGRATION,
            severity=Severity.SEVERE,
            description="Escalated campaign of denigration",
            evidence_refs=["DOC-004"],
        ),
        AlienationEvent(
            event_date="2024-10-05",
            indicator=AlienationIndicator.REFLEXIVE_SUPPORT,
            severity=Severity.MILD,
            description="Child automatically sides with defendant",
            evidence_refs=["DOC-005"],
        ),
    ]


@pytest.fixture
def sample_evidence_item() -> EvidenceItem:
    return EvidenceItem(
        exhibit_number="A-001",
        title="Text messages re: parenting time — June 2024",
        description="Screenshots of text messages between Plaintiff and Defendant",
        evidence_type=EvidenceType.TEXT_MESSAGE,
        lane="A",
        case_number="2024-001507-DC",
        date_obtained="2024-06-20",
        obtained_by="Andrew James Pigors",
        storage_location="C:\\Users\\andre\\LitigationOS\\10_Exhibits",
    )


@pytest.fixture
def tmp_db_path(tmp_path) -> pathlib.Path:
    """Temp database with a documents table for scan tests."""
    db_file = tmp_path / "test_alienation.db"
    conn = sqlite3.connect(str(db_file))
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("""
        CREATE TABLE documents (
            id INTEGER PRIMARY KEY,
            doc_id TEXT,
            title TEXT,
            content_preview TEXT,
            lane TEXT,
            created_at TEXT
        )
    """)
    conn.executemany(
        "INSERT INTO documents (doc_id, title, content_preview, lane, created_at) VALUES (?,?,?,?,?)",
        [
            ("D001", "Text msg 1", "she said he is a horrible parent who doesn't care about you", "A", "2024-06-15"),
            ("D002", "Text msg 2", "child said it was my own decision to not visit", "A", "2024-07-20"),
            ("D003", "Email 1", "nothing relevant here", "A", "2024-08-01"),
            ("D004", "Text msg 3", "hate grandma and your whole family", "A", "2024-09-10"),
            ("D005", "Note", "mom said you were a bad person", "A", "2024-10-01"),
        ],
    )
    conn.commit()
    conn.close()
    return db_file


# ═══════════════════════════════════════════════════════════════════════════
# PART 1 — ParentalAlienationDetector Tests (~60)
# ═══════════════════════════════════════════════════════════════════════════

# --- Enum Tests ---

class TestAlienationIndicator:
    def test_all_eight_indicators_exist(self):
        assert len(AlienationIndicator) == 8

    def test_values_are_1_through_8(self):
        assert [i.value for i in AlienationIndicator] == list(range(1, 9))

    def test_label_property(self):
        assert "denigration" in AlienationIndicator.CAMPAIGN_OF_DENIGRATION.label.lower()

    def test_description_property(self):
        desc = AlienationIndicator.BORROWED_SCENARIOS.description
        assert "coached" in desc.lower() or "phrases" in desc.lower()

    def test_label_for_all_indicators(self):
        for ind in AlienationIndicator:
            assert ind.label, f"Missing label for {ind.name}"

    def test_description_for_all_indicators(self):
        for ind in AlienationIndicator:
            assert ind.description, f"Missing description for {ind.name}"


class TestSeverity:
    def test_all_levels(self):
        assert len(Severity) == 4

    def test_score_property(self):
        assert Severity.NONE.score == 0
        assert Severity.MILD.score == 1
        assert Severity.MODERATE.score == 2
        assert Severity.SEVERE.score == 3

    def test_ordering_by_score(self):
        levels = sorted(Severity, key=lambda s: s.score)
        assert levels == [Severity.NONE, Severity.MILD, Severity.MODERATE, Severity.SEVERE]


class TestFactorJImpact:
    def test_all_values(self):
        expected = {"strongly_favors", "favors", "neutral", "against", "strongly_against"}
        assert {f.value for f in FactorJImpact} == expected


class TestEscalationTrend:
    def test_all_values(self):
        expected = {"escalating", "stable", "de_escalating", "insufficient_data"}
        assert {e.value for e in EscalationTrend} == expected


class TestReportFormat:
    def test_formats(self):
        assert ReportFormat.MARKDOWN.value == "markdown"
        assert ReportFormat.JSON.value == "json"
        assert ReportFormat.TEXT.value == "text"


# --- Dataclass Tests ---

class TestAlienationEvent:
    def test_default_values(self):
        ev = AlienationEvent()
        assert ev.event_date == ""
        assert ev.indicator == AlienationIndicator.CAMPAIGN_OF_DENIGRATION
        assert ev.severity == Severity.NONE
        assert ev.accused_party == _DEFENDANT
        assert ev.child_initials == _CHILD_INITIALS

    def test_to_dict(self):
        ev = AlienationEvent(
            indicator=AlienationIndicator.BORROWED_SCENARIOS,
            severity=Severity.MODERATE,
        )
        d = ev.to_dict()
        assert d["indicator"] == 7
        assert d["severity"] == "moderate"
        assert "event_id" in d

    def test_unique_ids(self):
        e1 = AlienationEvent()
        e2 = AlienationEvent()
        assert e1.event_id != e2.event_id

    def test_evidence_refs_list(self):
        ev = AlienationEvent(evidence_refs=["REF-1", "REF-2"])
        assert len(ev.to_dict()["evidence_refs"]) == 2


class TestAlienationPattern:
    def test_empty_pattern(self):
        pat = AlienationPattern()
        assert pat.score == 0
        assert pat.event_count == 0

    def test_score_uses_peak_severity(self):
        evts = [
            AlienationEvent(severity=Severity.MILD),
            AlienationEvent(severity=Severity.SEVERE),
        ]
        pat = AlienationPattern(events=evts, peak_severity=Severity.SEVERE)
        assert pat.score == 3

    def test_to_dict_structure(self):
        pat = AlienationPattern(indicator=AlienationIndicator.ABSENCE_OF_GUILT)
        d = pat.to_dict()
        assert d["indicator"] == 6
        assert "indicator_label" in d
        assert "events" in d
        assert "trend" in d


class TestFactorJAssessment:
    def test_to_dict(self):
        fj = FactorJAssessment(
            party_name=_PLAINTIFF,
            impact=FactorJImpact.FAVORS,
            narrative="Facilitates relationship",
        )
        d = fj.to_dict()
        assert d["impact"] == "favors"
        assert d["party_name"] == _PLAINTIFF


class TestTemporalAnalysis:
    def test_to_dict(self):
        ta = TemporalAnalysis(
            total_events=5,
            overall_trend=EscalationTrend.ESCALATING,
        )
        d = ta.to_dict()
        assert d["overall_trend"] == "escalating"
        assert d["total_events"] == 5


class TestAlienationReport:
    def test_default_max_possible(self):
        r = AlienationReport()
        assert r.max_possible == 24

    def test_to_dict(self):
        r = AlienationReport(total_score=10, severity_level="Mild Alienation")
        d = r.to_dict()
        assert d["total_score"] == 10
        assert d["max_possible"] == 24
        assert "patterns" in d
        assert "report_id" in d

    def test_case_number_default(self):
        r = AlienationReport()
        assert r.case_number == _CASE_NUMBER

    def test_lane_default(self):
        r = AlienationReport()
        assert r.lane == _LANE


# --- Helper Function Tests ---

class TestClassifySeverity:
    def test_no_significant(self):
        assert _classify_severity(0) == "No Significant Alienation"
        assert _classify_severity(4) == "No Significant Alienation"

    def test_mild(self):
        assert _classify_severity(5) == "Mild Alienation"
        assert _classify_severity(10) == "Mild Alienation"

    def test_moderate(self):
        assert _classify_severity(11) == "Moderate Alienation"
        assert _classify_severity(16) == "Moderate Alienation"

    def test_severe(self):
        assert _classify_severity(17) == "Severe Alienation"
        assert _classify_severity(24) == "Severe Alienation"

    def test_out_of_range(self):
        assert _classify_severity(100) == "Unknown"


class TestRecommendedActions:
    def test_severe_includes_emergency(self):
        actions = _recommended_actions("Severe Alienation")
        assert any("emergency" in a.lower() for a in actions)

    def test_mild_includes_therapy(self):
        actions = _recommended_actions("Mild Alienation")
        assert any("therapy" in a.lower() or "co-parenting" in a.lower() for a in actions)

    def test_unknown_severity(self):
        actions = _recommended_actions("not_real")
        assert len(actions) >= 1


# --- BehaviorCataloger Tests ---

class TestBehaviorCataloger:
    def test_scan_text_denigration(self):
        cat = BehaviorCataloger()
        hits = cat.scan_text("The child says daddy is a horrible parent")
        indicators = [h[0] for h in hits]
        assert AlienationIndicator.CAMPAIGN_OF_DENIGRATION in indicators

    def test_scan_text_borrowed_scenarios(self):
        cat = BehaviorCataloger()
        hits = cat.scan_text("Mom said you were bad to us")
        indicators = [h[0] for h in hits]
        assert AlienationIndicator.BORROWED_SCENARIOS in indicators

    def test_scan_text_no_hits(self):
        cat = BehaviorCataloger()
        hits = cat.scan_text("The weather is nice today.")
        assert hits == []

    def test_scan_text_multiple_indicators(self):
        cat = BehaviorCataloger()
        text = "horrible parent told me that you don't care. hate grandma"
        hits = cat.scan_text(text)
        indicators = {h[0] for h in hits}
        assert len(indicators) >= 2

    def test_scan_text_case_insensitive(self):
        cat = BehaviorCataloger()
        hits = cat.scan_text("HORRIBLE PARENT")
        assert len(hits) >= 1

    def test_scan_evidence_with_db(self, tmp_db_path):
        cat = BehaviorCataloger(db_path=tmp_db_path)
        events = cat.scan_evidence(lane="A")
        assert len(events) > 0
        for ev in events:
            assert isinstance(ev, AlienationEvent)

    def test_scan_evidence_missing_db(self, tmp_path):
        cat = BehaviorCataloger(db_path=tmp_path / "nonexistent.db")
        events = cat.scan_evidence()
        assert events == []

    def test_get_stats(self):
        cat = BehaviorCataloger()
        stats = cat.get_stats()
        assert stats["component"] == "BehaviorCataloger"
        assert stats["keyword_categories"] == 8
        assert stats["total_keywords"] > 0

    def test_scan_text_independent_thinker(self):
        cat = BehaviorCataloger()
        hits = cat.scan_text("It was my own decision not to visit")
        indicators = [h[0] for h in hits]
        assert AlienationIndicator.INDEPENDENT_THINKER_PHENOMENON in indicators

    def test_scan_text_spread_to_family(self):
        cat = BehaviorCataloger()
        hits = cat.scan_text("I hate grandma and your whole family")
        indicators = [h[0] for h in hits]
        assert AlienationIndicator.SPREAD_TO_EXTENDED_FAMILY in indicators


# --- PatternAnalyzer Tests ---

class TestPatternAnalyzer:
    def test_build_patterns_empty(self):
        pa = PatternAnalyzer()
        patterns = pa.build_patterns([])
        assert len(patterns) == 8
        assert all(p.event_count == 0 for p in patterns)

    def test_build_patterns_grouping(self, sample_events):
        pa = PatternAnalyzer()
        patterns = pa.build_patterns(sample_events)
        denigration = [p for p in patterns if p.indicator == AlienationIndicator.CAMPAIGN_OF_DENIGRATION][0]
        assert denigration.event_count == 2

    def test_peak_severity(self, sample_events):
        pa = PatternAnalyzer()
        patterns = pa.build_patterns(sample_events)
        denigration = [p for p in patterns if p.indicator == AlienationIndicator.CAMPAIGN_OF_DENIGRATION][0]
        assert denigration.peak_severity == Severity.SEVERE

    def test_first_last_occurrence(self, sample_events):
        pa = PatternAnalyzer()
        patterns = pa.build_patterns(sample_events)
        denigration = [p for p in patterns if p.indicator == AlienationIndicator.CAMPAIGN_OF_DENIGRATION][0]
        assert denigration.first_occurrence == "2024-06-15"
        assert denigration.last_occurrence == "2024-09-01"

    def test_temporal_analysis_empty(self):
        pa = PatternAnalyzer()
        ta = pa.temporal_analysis([])
        assert ta.total_events == 0
        assert ta.overall_trend == EscalationTrend.INSUFFICIENT_DATA

    def test_temporal_analysis_with_events(self, sample_events):
        pa = PatternAnalyzer()
        ta = pa.temporal_analysis(sample_events)
        assert ta.total_events == 5
        assert ta.date_range_start == "2024-06-15"
        assert ta.date_range_end == "2024-10-05"
        assert ta.months_covered > 0

    def test_detect_trend_insufficient_data(self):
        pa = PatternAnalyzer()
        trend = pa._detect_trend(["2024-01-01", "2024-02-01"])
        assert trend == EscalationTrend.INSUFFICIENT_DATA

    def test_frequency_per_month_single(self):
        pa = PatternAnalyzer()
        freq = pa._freq_per_month(["2024-01-01"])
        assert freq == 1.0

    def test_gardner_scoring_all_8(self):
        """Verify all 8 Gardner indicators get a pattern slot."""
        pa = PatternAnalyzer()
        patterns = pa.build_patterns([])
        indicators = {p.indicator for p in patterns}
        for ind in AlienationIndicator:
            assert ind in indicators

    def test_get_stats(self):
        pa = PatternAnalyzer()
        stats = pa.get_stats()
        assert stats["component"] == "PatternAnalyzer"
        assert stats["manifestations_tracked"] == 8


# --- AlienationReporter Tests ---

class TestAlienationReporter:
    def test_build_report_empty_patterns(self):
        reporter = AlienationReporter()
        patterns = PatternAnalyzer().build_patterns([])
        report = reporter.build_report(patterns)
        assert report.total_score == 0
        assert report.severity_level == "No Significant Alienation"

    def test_build_report_with_events(self, sample_events):
        analyzer = PatternAnalyzer()
        reporter = AlienationReporter()
        patterns = analyzer.build_patterns(sample_events)
        report = reporter.build_report(patterns)
        assert report.total_score > 0
        assert report.factor_j_plaintiff is not None
        assert report.factor_j_defendant is not None

    def test_factor_j_plaintiff_favors(self, sample_events):
        analyzer = PatternAnalyzer()
        reporter = AlienationReporter()
        patterns = analyzer.build_patterns(sample_events)
        report = reporter.build_report(patterns)
        assert report.factor_j_plaintiff.impact == FactorJImpact.FAVORS

    def test_defendant_impact_severe(self):
        reporter = AlienationReporter()
        impact = reporter._defendant_impact(20)
        assert impact == FactorJImpact.STRONGLY_AGAINST

    def test_defendant_impact_moderate(self):
        reporter = AlienationReporter()
        assert reporter._defendant_impact(12) == FactorJImpact.AGAINST

    def test_defendant_impact_mild(self):
        reporter = AlienationReporter()
        assert reporter._defendant_impact(6) == FactorJImpact.NEUTRAL

    def test_defendant_impact_none(self):
        reporter = AlienationReporter()
        assert reporter._defendant_impact(2) == FactorJImpact.FAVORS

    def test_to_markdown_contains_mcl(self, sample_events):
        analyzer = PatternAnalyzer()
        reporter = AlienationReporter()
        patterns = analyzer.build_patterns(sample_events)
        report = reporter.build_report(patterns)
        md = reporter.to_markdown(report)
        assert "722.23(j)" in md

    def test_to_markdown_table(self, sample_events):
        analyzer = PatternAnalyzer()
        reporter = AlienationReporter()
        patterns = analyzer.build_patterns(sample_events)
        report = reporter.build_report(patterns)
        md = reporter.to_markdown(report)
        assert "| # | Manifestation |" in md

    def test_evidence_index_dedup(self):
        events = [
            AlienationEvent(evidence_refs=["D1", "D2"]),
            AlienationEvent(evidence_refs=["D1", "D3"]),
        ]
        analyzer = PatternAnalyzer()
        reporter = AlienationReporter()
        patterns = analyzer.build_patterns(events)
        report = reporter.build_report(patterns)
        assert len(report.evidence_index) == 3

    def test_recommended_actions_populated(self, sample_events):
        analyzer = PatternAnalyzer()
        reporter = AlienationReporter()
        patterns = analyzer.build_patterns(sample_events)
        report = reporter.build_report(patterns)
        assert len(report.recommended_actions) > 0

    def test_get_stats(self):
        reporter = AlienationReporter()
        stats = reporter.get_stats()
        assert stats["component"] == "AlienationReporter"
        assert "severity_levels" in stats


# --- ParentalAlienationDetector Orchestrator Tests ---

class TestParentalAlienationDetector:
    def test_add_event(self):
        pad = ParentalAlienationDetector(db_path=pathlib.Path("fake.db"))
        ev = AlienationEvent()
        pad.add_event(ev)
        stats = pad.get_stats()
        assert stats["events_loaded"] == 1

    def test_add_events(self, sample_events):
        pad = ParentalAlienationDetector(db_path=pathlib.Path("fake.db"))
        pad.add_events(sample_events)
        assert pad.get_stats()["events_loaded"] == 5

    def test_analyse(self, sample_events):
        pad = ParentalAlienationDetector(db_path=pathlib.Path("fake.db"))
        pad.add_events(sample_events)
        report = pad.analyse()
        assert report.total_score > 0
        assert report.severity_level != ""

    def test_generate_report_markdown(self, sample_events):
        pad = ParentalAlienationDetector(db_path=pathlib.Path("fake.db"))
        pad.add_events(sample_events)
        md = pad.generate_report(fmt=ReportFormat.MARKDOWN)
        assert "Parental Alienation" in md

    def test_generate_report_json(self, sample_events):
        pad = ParentalAlienationDetector(db_path=pathlib.Path("fake.db"))
        pad.add_events(sample_events)
        j = pad.generate_report(fmt=ReportFormat.JSON)
        data = json.loads(j)
        assert "total_score" in data

    def test_get_stats_before_analysis(self):
        pad = ParentalAlienationDetector(db_path=pathlib.Path("fake.db"))
        stats = pad.get_stats()
        assert stats["module"] == "parental_alienation_detector"
        assert stats["report_generated"] is False
        assert stats["total_score"] is None

    def test_get_stats_after_analysis(self, sample_events):
        pad = ParentalAlienationDetector(db_path=pathlib.Path("fake.db"))
        pad.add_events(sample_events)
        pad.analyse()
        stats = pad.get_stats()
        assert stats["report_generated"] is True
        assert stats["total_score"] is not None

    def test_reset(self, sample_events):
        pad = ParentalAlienationDetector(db_path=pathlib.Path("fake.db"))
        pad.add_events(sample_events)
        pad.analyse()
        pad.reset()
        assert pad.get_stats()["events_loaded"] == 0
        assert pad.get_stats()["report_generated"] is False

    def test_scan_database_with_temp(self, tmp_db_path):
        pad = ParentalAlienationDetector(db_path=tmp_db_path)
        found = pad.scan_database(lane="A")
        assert found > 0

    def test_scan_database_missing(self, tmp_path):
        pad = ParentalAlienationDetector(db_path=tmp_path / "nonexistent.db")
        found = pad.scan_database()
        assert found == 0

    def test_lane_routing(self):
        assert _LANE == "A"
        assert _CASE_NUMBER == "2024-001507-DC"

    def test_party_names(self):
        assert _PLAINTIFF == "Andrew James Pigors"
        assert _DEFENDANT == "Emily A. Watson"
        assert _CHILD_INITIALS == "L.D.W."
        assert _JUDGE == "Hon. Jenny L. McNeill"


# ═══════════════════════════════════════════════════════════════════════════
# PART 2 — EvidenceAuthenticator Tests (~60)
# ═══════════════════════════════════════════════════════════════════════════

# --- Enum Tests ---

class TestAuthenticationMethod:
    def test_mre_901_methods(self):
        mre_901 = [m for m in AuthenticationMethod if "901" in m.value]
        assert len(mre_901) >= 10

    def test_mre_902_methods(self):
        mre_902 = [m for m in AuthenticationMethod if "902" in m.value]
        assert len(mre_902) >= 10

    def test_all_values_are_strings(self):
        for m in AuthenticationMethod:
            assert isinstance(m.value, str)
            assert m.value.startswith("MRE")


class TestEvidenceType:
    def test_all_types(self):
        assert len(EvidenceType) >= 16

    def test_text_message(self):
        assert EvidenceType.TEXT_MESSAGE.value == "text_message"

    def test_other_type_exists(self):
        assert EvidenceType.OTHER.value == "other"


class TestHearsayException:
    def test_mre_803_exceptions(self):
        mre_803 = [h for h in HearsayException if "803" in h.value]
        assert len(mre_803) >= 8

    def test_mre_804_exceptions(self):
        mre_804 = [h for h in HearsayException if "804" in h.value]
        assert len(mre_804) >= 4

    def test_none_and_not_hearsay(self):
        assert HearsayException.NONE.value == "none"
        assert HearsayException.NOT_HEARSAY.value == "not_hearsay"


class TestCustodyStatus:
    def test_all_values(self):
        expected = {"complete", "minor_gap", "moderate_gap", "critical_gap",
                    "not_documented", "not_applicable"}
        assert {c.value for c in CustodyStatus} == expected


class TestAuthStatus:
    def test_all_values(self):
        expected = {"ready", "needs_foundation", "needs_custody_chain",
                    "needs_hearsay_exception", "at_risk", "excluded", "pending"}
        assert {a.value for a in AuthStatus} == expected


class TestBestEvidenceStatus:
    def test_all_values(self):
        assert len(BestEvidenceStatus) >= 6


# --- Dataclass Tests ---

class TestChainOfCustodyEntry:
    def test_default_values(self):
        entry = ChainOfCustodyEntry()
        assert entry.date == ""
        assert entry.person == ""
        assert entry.hash_sha256 == ""

    def test_to_dict(self):
        entry = ChainOfCustodyEntry(
            date="2024-01-15",
            person="Andrew James Pigors",
            action="Received",
        )
        d = entry.to_dict()
        assert d["date"] == "2024-01-15"
        assert d["person"] == "Andrew James Pigors"

    def test_unique_ids(self):
        e1 = ChainOfCustodyEntry()
        e2 = ChainOfCustodyEntry()
        assert e1.entry_id != e2.entry_id


class TestEvidenceItem:
    def test_default_obtained_by(self):
        item = EvidenceItem()
        assert item.obtained_by == EA_PLAINTIFF

    def test_to_dict_evidence_type(self):
        item = EvidenceItem(evidence_type=EvidenceType.EMAIL)
        d = item.to_dict()
        assert d["evidence_type"] == "email"

    def test_is_original_default(self):
        item = EvidenceItem()
        assert item.is_original is True

    def test_metadata_default_empty(self):
        item = EvidenceItem()
        assert item.metadata == {}


class TestAuthenticationRequirement:
    def test_to_dict_structure(self):
        req = AuthenticationRequirement(
            evidence_type=EvidenceType.TEXT_MESSAGE,
            primary_method=AuthenticationMethod.DISTINCTIVE_CHARACTERISTICS,
            custody_status=CustodyStatus.COMPLETE,
            overall_status=AuthStatus.READY,
        )
        d = req.to_dict()
        assert d["evidence_type"] == "text_message"
        assert d["primary_method"] == "MRE 901(b)(4)"
        assert d["custody_status"] == "complete"
        assert d["overall_status"] == "ready"

    def test_hearsay_issues_serialization(self):
        req = AuthenticationRequirement(
            hearsay_issues=[HearsayException.BUSINESS_RECORDS, HearsayException.PUBLIC_RECORDS],
        )
        d = req.to_dict()
        assert "MRE 803(6)" in d["hearsay_issues"]


class TestAuthenticationReport:
    def test_to_dict(self):
        report = AuthenticationReport(
            total_exhibits=5,
            ready_count=3,
            needs_work_count=1,
            at_risk_count=1,
        )
        d = report.to_dict()
        assert d["total_exhibits"] == 5
        assert d["ready_count"] == 3
        assert "report_id" in d

    def test_default_zeroes(self):
        report = AuthenticationReport()
        assert report.total_exhibits == 0
        assert report.ready_count == 0


# --- AuthenticationAnalyzer Tests ---

class TestAuthenticationAnalyzer:
    def test_analyse_text_message(self, sample_evidence_item):
        aa = AuthenticationAnalyzer()
        req = aa.analyse(sample_evidence_item)
        assert req.primary_method == AuthenticationMethod.DISTINCTIVE_CHARACTERISTICS
        assert req.evidence_type == EvidenceType.TEXT_MESSAGE

    def test_analyse_court_filing(self):
        aa = AuthenticationAnalyzer()
        item = EvidenceItem(
            evidence_type=EvidenceType.COURT_FILING,
            date_obtained="2024-01-01",
            obtained_by="Clerk",
        )
        req = aa.analyse(item)
        assert req.primary_method == AuthenticationMethod.SELF_AUTH_SEAL

    def test_custody_complete(self, sample_evidence_item):
        aa = AuthenticationAnalyzer()
        req = aa.analyse(sample_evidence_item)
        assert req.custody_status == CustodyStatus.COMPLETE

    def test_custody_not_documented(self):
        aa = AuthenticationAnalyzer()
        item = EvidenceItem(evidence_type=EvidenceType.PHOTOGRAPH)
        req = aa.analyse(item)
        assert req.custody_status == CustodyStatus.NOT_DOCUMENTED

    def test_custody_not_applicable_for_govt(self):
        aa = AuthenticationAnalyzer()
        item = EvidenceItem(evidence_type=EvidenceType.GOVERNMENT_RECORD)
        req = aa.analyse(item)
        assert req.custody_status == CustodyStatus.NOT_APPLICABLE

    def test_best_evidence_photo_not_applicable(self):
        aa = AuthenticationAnalyzer()
        item = EvidenceItem(evidence_type=EvidenceType.PHOTOGRAPH)
        req = aa.analyse(item)
        assert req.best_evidence == BestEvidenceStatus.NOT_APPLICABLE

    def test_best_evidence_original(self, sample_evidence_item):
        aa = AuthenticationAnalyzer()
        req = aa.analyse(sample_evidence_item)
        assert req.best_evidence == BestEvidenceStatus.ORIGINAL

    def test_best_evidence_duplicate(self):
        aa = AuthenticationAnalyzer()
        item = EvidenceItem(
            evidence_type=EvidenceType.BUSINESS_RECORD,
            is_original=False,
        )
        req = aa.analyse(item)
        assert req.best_evidence == BestEvidenceStatus.DUPLICATE_OK

    def test_all_evidence_types_have_mapping(self):
        for et in EvidenceType:
            assert et in _DEFAULT_AUTH_METHODS, f"No auth mapping for {et}"

    def test_get_stats(self):
        aa = AuthenticationAnalyzer()
        stats = aa.get_stats()
        assert stats["component"] == "AuthenticationAnalyzer"
        assert stats["evidence_types_mapped"] > 0


# --- HearsayAnalyzer Tests ---

class TestHearsayAnalyzer:
    def test_text_message_defaults(self):
        ha = HearsayAnalyzer()
        item = EvidenceItem(evidence_type=EvidenceType.TEXT_MESSAGE)
        exceptions = ha.analyse(item)
        assert HearsayException.PRESENT_SENSE_IMPRESSION in exceptions

    def test_business_record_defaults(self):
        ha = HearsayAnalyzer()
        item = EvidenceItem(evidence_type=EvidenceType.BUSINESS_RECORD)
        exceptions = ha.analyse(item)
        assert HearsayException.BUSINESS_RECORDS in exceptions

    def test_content_keyword_detection(self):
        ha = HearsayAnalyzer()
        item = EvidenceItem(evidence_type=EvidenceType.OTHER)
        exceptions = ha.analyse(item, "The doctor prescribed medication")
        assert HearsayException.MEDICAL_DIAGNOSIS in exceptions

    def test_no_exceptions_returns_none(self):
        ha = HearsayAnalyzer()
        item = EvidenceItem(evidence_type=EvidenceType.PHYSICAL_DOCUMENT)
        exceptions = ha.analyse(item, "plain text no keywords")
        assert HearsayException.NONE in exceptions

    def test_is_hearsay_risk_text(self):
        ha = HearsayAnalyzer()
        item = EvidenceItem(evidence_type=EvidenceType.TEXT_MESSAGE)
        assert ha.is_hearsay_risk(item) is True

    def test_is_hearsay_risk_photo(self):
        ha = HearsayAnalyzer()
        item = EvidenceItem(evidence_type=EvidenceType.PHOTOGRAPH)
        assert ha.is_hearsay_risk(item) is False

    def test_excited_utterance_keyword(self):
        ha = HearsayAnalyzer()
        item = EvidenceItem(evidence_type=EvidenceType.OTHER)
        exceptions = ha.analyse(item, "Oh my god help me please")
        assert HearsayException.EXCITED_UTTERANCE in exceptions

    def test_state_of_mind_keyword(self):
        ha = HearsayAnalyzer()
        item = EvidenceItem(evidence_type=EvidenceType.OTHER)
        exceptions = ha.analyse(item, "I feel scared about what happened")
        assert HearsayException.STATE_OF_MIND in exceptions

    def test_get_stats(self):
        ha = HearsayAnalyzer()
        stats = ha.get_stats()
        assert stats["component"] == "HearsayAnalyzer"
        assert stats["exceptions_tracked"] > 0


# --- FoundationBuilder Tests ---

class TestFoundationBuilder:
    def test_photograph_template(self):
        fb = FoundationBuilder()
        item = EvidenceItem(
            exhibit_number="A-010",
            evidence_type=EvidenceType.PHOTOGRAPH,
            description="Photo of child's bedroom",
        )
        req = AuthenticationRequirement()
        foundation = fb.build_foundation(item, req)
        assert "Exhibit A-010" in foundation
        assert "photograph" in foundation.lower()

    def test_text_message_template(self, sample_evidence_item):
        fb = FoundationBuilder()
        req = AuthenticationRequirement()
        foundation = fb.build_foundation(sample_evidence_item, req)
        assert "text message" in foundation.lower()

    def test_generic_fallback(self):
        fb = FoundationBuilder()
        item = EvidenceItem(
            exhibit_number="X-001",
            evidence_type=EvidenceType.OTHER,
            description="Unknown document",
        )
        req = AuthenticationRequirement()
        foundation = fb.build_foundation(item, req)
        assert "Exhibit" in foundation
        assert "admit" in foundation.lower()

    def test_email_template(self):
        fb = FoundationBuilder()
        item = EvidenceItem(
            exhibit_number="A-020",
            evidence_type=EvidenceType.EMAIL,
            description="Email about custody schedule",
        )
        req = AuthenticationRequirement()
        foundation = fb.build_foundation(item, req)
        assert "email" in foundation.lower()

    def test_business_record_template(self):
        fb = FoundationBuilder()
        item = EvidenceItem(
            exhibit_number="B-001",
            evidence_type=EvidenceType.BUSINESS_RECORD,
        )
        req = AuthenticationRequirement()
        foundation = fb.build_foundation(item, req)
        assert "MRE 803(6)" in foundation

    def test_get_stats(self):
        fb = FoundationBuilder()
        stats = fb.get_stats()
        assert stats["component"] == "FoundationBuilder"
        assert stats["templates_available"] > 0


# --- EvidenceAuthenticator Orchestrator Tests ---

class TestEvidenceAuthenticator:
    def test_add_item(self, sample_evidence_item):
        ea = EvidenceAuthenticator(db_path=pathlib.Path("fake.db"))
        ea.add_item(sample_evidence_item)
        stats = ea.get_stats()
        assert stats["items_loaded"] == 1

    def test_add_items(self):
        ea = EvidenceAuthenticator(db_path=pathlib.Path("fake.db"))
        items = [
            EvidenceItem(evidence_type=EvidenceType.EMAIL),
            EvidenceItem(evidence_type=EvidenceType.PHOTOGRAPH),
        ]
        ea.add_items(items)
        assert ea.get_stats()["items_loaded"] == 2

    def test_analyse_all(self, sample_evidence_item):
        ea = EvidenceAuthenticator(db_path=pathlib.Path("fake.db"))
        ea.add_item(sample_evidence_item)
        reqs = ea.analyse_all()
        assert len(reqs) == 1
        assert reqs[0].evidence_type == EvidenceType.TEXT_MESSAGE

    def test_generate_report(self, sample_evidence_item):
        ea = EvidenceAuthenticator(db_path=pathlib.Path("fake.db"))
        ea.add_item(sample_evidence_item)
        report = ea.generate_report()
        assert report.total_exhibits == 1
        assert report.ready_count + report.needs_work_count + report.at_risk_count == 1

    def test_determine_status_ready(self):
        req = AuthenticationRequirement(
            custody_status=CustodyStatus.COMPLETE,
            hearsay_resolved=True,
            best_evidence=BestEvidenceStatus.ORIGINAL,
            foundation_witness="Andrew James Pigors",
        )
        status = EvidenceAuthenticator._determine_status(req)
        assert status == AuthStatus.READY

    def test_determine_status_at_risk(self):
        req = AuthenticationRequirement(
            custody_status=CustodyStatus.NOT_DOCUMENTED,
            hearsay_resolved=False,
            best_evidence=BestEvidenceStatus.NON_COMPLIANT,
            foundation_witness="",
        )
        status = EvidenceAuthenticator._determine_status(req)
        assert status == AuthStatus.AT_RISK

    def test_determine_status_needs_custody(self):
        req = AuthenticationRequirement(
            custody_status=CustodyStatus.CRITICAL_GAP,
            hearsay_resolved=True,
            best_evidence=BestEvidenceStatus.ORIGINAL,
            foundation_witness="Someone",
        )
        status = EvidenceAuthenticator._determine_status(req)
        assert status == AuthStatus.NEEDS_CUSTODY_CHAIN

    def test_determine_status_needs_hearsay(self):
        req = AuthenticationRequirement(
            custody_status=CustodyStatus.COMPLETE,
            hearsay_resolved=False,
            best_evidence=BestEvidenceStatus.ORIGINAL,
            foundation_witness="Someone",
        )
        status = EvidenceAuthenticator._determine_status(req)
        assert status == AuthStatus.NEEDS_HEARSAY_EXCEPTION

    def test_to_markdown(self, sample_evidence_item):
        ea = EvidenceAuthenticator(db_path=pathlib.Path("fake.db"))
        ea.add_item(sample_evidence_item)
        md = ea.to_markdown()
        assert "Evidence Authentication Report" in md

    def test_get_stats(self):
        ea = EvidenceAuthenticator(db_path=pathlib.Path("fake.db"))
        stats = ea.get_stats()
        assert stats["module"] == "evidence_authenticator"
        assert stats["items_loaded"] == 0
        assert stats["report_generated"] is False

    def test_reset(self, sample_evidence_item):
        ea = EvidenceAuthenticator(db_path=pathlib.Path("fake.db"))
        ea.add_item(sample_evidence_item)
        ea.analyse_all()
        ea.generate_report()
        ea.reset()
        assert ea.get_stats()["items_loaded"] == 0
        assert ea.get_stats()["report_generated"] is False

    def test_lane_cases_mapping(self):
        assert LANE_CASES["A"] == "2024-001507-DC"
        assert LANE_CASES["B"] == "2025-002760-CZ"
        assert LANE_CASES["D"] == "2023-5907-PP"
        assert LANE_CASES["F"] == "COA 366810"

    def test_digital_evidence_types(self):
        """Digital evidence types should use distinctive characteristics or process auth."""
        aa = AuthenticationAnalyzer()
        for etype in [EvidenceType.TEXT_MESSAGE, EvidenceType.EMAIL, EvidenceType.SOCIAL_MEDIA]:
            item = EvidenceItem(evidence_type=etype)
            req = aa.analyse(item)
            assert req.primary_method in (
                AuthenticationMethod.DISTINCTIVE_CHARACTERISTICS,
                AuthenticationMethod.PROCESS_OR_SYSTEM,
                AuthenticationMethod.WITNESS_TESTIMONY,
            )

    def test_chain_of_custody_entry_tracking(self):
        """Verify chain of custody entries can be added to requirement."""
        entry = ChainOfCustodyEntry(
            date="2024-06-20",
            person="Andrew James Pigors",
            action="Screenshot captured from iPhone",
        )
        req = AuthenticationRequirement(custody_chain=[entry])
        d = req.to_dict()
        assert len(d["custody_chain"]) == 1
        assert d["custody_chain"][0]["person"] == "Andrew James Pigors"

    def test_multiple_items_report(self):
        ea = EvidenceAuthenticator(db_path=pathlib.Path("fake.db"))
        items = [
            EvidenceItem(
                evidence_type=EvidenceType.TEXT_MESSAGE,
                date_obtained="2024-06-20",
                obtained_by="Andrew James Pigors",
                storage_location="/exhibits",
            ),
            EvidenceItem(
                evidence_type=EvidenceType.POLICE_REPORT,
            ),
            EvidenceItem(
                evidence_type=EvidenceType.PHOTOGRAPH,
            ),
        ]
        ea.add_items(items)
        report = ea.generate_report()
        assert report.total_exhibits == 3
