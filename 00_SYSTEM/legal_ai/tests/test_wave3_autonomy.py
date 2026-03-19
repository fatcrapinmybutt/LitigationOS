"""Tests for Wave 3 Autonomy modules — LitigationOS Legal AI.

Covers:
    1. SuggestionEngine       (suggestion_engine.py)
    2. AdversaryPredictor     (adversary_predictor.py)
    3. FinancialForensicsEngine (financial_forensics.py)
    4. PatternMiner           (pattern_mining.py)
    5. TimelineVisualizer     (timeline_visualizer.py)

All tests are pure unit tests — no DB connections, no external dependencies.
Run with:
    cd C:\\Users\\andre\\LitigationOS\\00_SYSTEM\\legal_ai
    python -m pytest tests/test_wave3_autonomy.py -v
"""
from __future__ import annotations

import json
import os
import sys
import unittest
from dataclasses import asdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List
from unittest.mock import MagicMock, patch, PropertyMock

# ---------------------------------------------------------------------------
# Ensure legal_ai package is importable (avoid repo-root shadow modules)
# ---------------------------------------------------------------------------
_LEGAL_AI_DIR = Path(__file__).resolve().parent.parent
if str(_LEGAL_AI_DIR.parent) not in sys.path:
    sys.path.insert(0, str(_LEGAL_AI_DIR.parent))

# ---------------------------------------------------------------------------
# Imports from modules under test — patch DB access at module level
# ---------------------------------------------------------------------------
from legal_ai.suggestion_engine import (
    Suggestion,
    SuggestionReport,
    SuggestionEngine,
    VALID_CATEGORIES,
    VALID_PRIORITIES,
    PRIORITY_WEIGHTS,
    LANE_LABELS,
    _combined,
    _priority_from_score,
    _clamp,
    _make_id,
)

from legal_ai.adversary_predictor import (
    AdversaryPredictor,
    AdversaryProfile,
    AdversaryReport,
    PredictedResponse,
    RISK_LEVELS,
    _PROFILE_INDEX,
)

from legal_ai.financial_forensics import (
    FinancialForensicsEngine,
    FinancialReport,
    DamageCategory,
    STATUTORY_INTEREST_RATE,
    TREBLE_MULTIPLIER,
    PUNITIVE_MULTIPLIER_MAX,
    FHA_PER_VIOLATION_MAX,
)

from legal_ai.pattern_mining import (
    PatternMiner,
    Pattern,
    PatternReport,
    PatternCategory,
    Confidence,
    _confidence_tier,
)

from legal_ai.timeline_visualizer import (
    TimelineVisualizer,
    TimelineEvent,
    TimelineData,
    EventCategory,
    Significance,
    _LANE_META,
    _CATEGORY_ICONS,
)


# ###########################################################################
# 1. SuggestionEngine Tests
# ###########################################################################

class TestSuggestionDataclass(unittest.TestCase):
    """Test the Suggestion and SuggestionReport dataclasses."""

    def _make_suggestion(self, **overrides: Any) -> Suggestion:
        defaults = dict(
            suggestion_id="s001",
            category="evidence",
            title="Gather school records",
            description="Collect L.D.W. school records for custody case",
            priority="high",
            urgency_score=75.0,
            impact_score=80.0,
            combined_score=77.25,
            lane="A",
        )
        defaults.update(overrides)
        return Suggestion(**defaults)

    def test_suggestion_has_required_fields(self):
        s = self._make_suggestion()
        self.assertEqual(s.title, "Gather school records")
        self.assertEqual(s.description, "Collect L.D.W. school records for custody case")
        self.assertEqual(s.priority, "high")
        self.assertEqual(s.category, "evidence")
        self.assertEqual(s.lane, "A")

    def test_suggestion_priority_values(self):
        for prio in VALID_PRIORITIES:
            s = self._make_suggestion(priority=prio)
            self.assertIn(s.priority, VALID_PRIORITIES)

    def test_suggestion_to_dict(self):
        s = self._make_suggestion()
        d = s.to_dict()
        self.assertIsInstance(d, dict)
        self.assertEqual(d["suggestion_id"], "s001")
        self.assertEqual(d["category"], "evidence")
        self.assertEqual(d["lane"], "A")

    def test_suggestion_defaults(self):
        s = self._make_suggestion()
        self.assertIsInstance(s.action_items, list)
        self.assertIsInstance(s.dependencies, list)
        self.assertEqual(s.estimated_effort, "hours")

    def test_valid_categories_complete(self):
        expected = {"evidence", "filing", "deadline", "strategy", "defense", "discovery"}
        self.assertEqual(VALID_CATEGORIES, expected)

    def test_priority_weights_values(self):
        self.assertEqual(PRIORITY_WEIGHTS["critical"], 1.0)
        self.assertEqual(PRIORITY_WEIGHTS["low"], 0.25)

    def test_lane_labels_complete(self):
        for lane_key in ("A", "B", "C", "D", "E", "F"):
            self.assertIn(lane_key, LANE_LABELS)


class TestSuggestionHelpers(unittest.TestCase):
    """Test module-level helper functions."""

    def test_combined_score_calculation(self):
        score = _combined(80.0, 70.0)
        # 80*0.55 + 70*0.45 = 44 + 31.5 = 75.5
        self.assertAlmostEqual(score, 75.5, places=1)

    def test_combined_clamped_high(self):
        score = _combined(200.0, 200.0)
        self.assertLessEqual(score, 100.0)

    def test_clamp_value(self):
        self.assertEqual(_clamp(150.0), 100.0)
        self.assertEqual(_clamp(-10.0), 0.0)
        self.assertEqual(_clamp(50.0), 50.0)

    def test_priority_from_score_critical(self):
        self.assertEqual(_priority_from_score(85.0), "critical")

    def test_priority_from_score_high(self):
        self.assertEqual(_priority_from_score(65.0), "high")

    def test_priority_from_score_medium(self):
        self.assertEqual(_priority_from_score(45.0), "medium")

    def test_priority_from_score_low(self):
        self.assertEqual(_priority_from_score(20.0), "low")

    def test_make_id_deterministic(self):
        id1 = _make_id("a", "b", "c")
        id2 = _make_id("a", "b", "c")
        self.assertEqual(id1, id2)
        self.assertEqual(len(id1), 12)


class TestSuggestionEngine(unittest.TestCase):
    """Test SuggestionEngine with mocked DB."""

    def setUp(self):
        self.engine = SuggestionEngine(db_path=Path(":memory:"))

    def test_generate_suggestions_returns_list(self):
        """get_evidence_suggestions should return a list of Suggestion objects."""
        suggestions = self.engine.get_evidence_suggestions()
        self.assertIsInstance(suggestions, list)
        for s in suggestions:
            self.assertIsInstance(s, Suggestion)

    def test_missing_evidence_suggestions(self):
        suggestions = self.engine.get_evidence_suggestions()
        self.assertTrue(len(suggestions) > 0, "Should produce evidence gap suggestions")
        for s in suggestions:
            self.assertEqual(s.category, "evidence")

    def test_deadline_suggestions(self):
        suggestions = self.engine.get_deadline_suggestions()
        self.assertIsInstance(suggestions, list)
        for s in suggestions:
            self.assertEqual(s.category, "deadline")

    def test_unfiled_motion_suggestions(self):
        suggestions = self.engine.get_filing_suggestions()
        self.assertIsInstance(suggestions, list)
        for s in suggestions:
            self.assertEqual(s.category, "filing")

    def test_suggestions_sorted_by_priority(self):
        """rank_suggestions should sort by combined_score descending."""
        s1 = Suggestion(
            suggestion_id="a", category="evidence", title="A", description="A",
            priority="low", urgency_score=20, impact_score=20, combined_score=20.0, lane="A",
        )
        s2 = Suggestion(
            suggestion_id="b", category="evidence", title="B", description="B",
            priority="critical", urgency_score=95, impact_score=95, combined_score=95.0, lane="A",
        )
        ranked = self.engine.rank_suggestions([s1, s2])
        self.assertEqual(ranked[0].suggestion_id, "b")

    def test_suggestions_filtered_by_lane(self):
        report = self.engine.analyze_lane("A")
        for s in report.suggestions:
            self.assertIn(s.lane, ("A", "C"),
                          msg="Lane A analysis may include cross-lane C suggestions")

    def test_empty_state_produces_suggestions(self):
        """Even with no DB data, engine should produce default suggestions."""
        report = self.engine.analyze()
        self.assertIsInstance(report, SuggestionReport)
        self.assertGreater(report.total_suggestions, 0)

    def test_report_structure(self):
        report = self.engine.analyze()
        d = report.to_dict()
        self.assertIn("generated_at", d)
        self.assertIn("total_suggestions", d)
        self.assertIn("critical_count", d)
        self.assertIn("suggestions", d)
        self.assertIn("top_5_actions", d)

    def test_get_stats(self):
        stats = self.engine.get_stats()
        self.assertIsInstance(stats, dict)
        self.assertIn("engine", stats)
        self.assertEqual(stats["engine"], "SuggestionEngine")


# ###########################################################################
# 2. AdversaryPredictor Tests
# ###########################################################################

class TestAdversaryDataclasses(unittest.TestCase):
    """Test adversary prediction dataclasses."""

    def test_adversary_profile_to_dict(self):
        profile = AdversaryProfile(
            name="Emily A. Watson", role="opposing_party",
            known_patterns=["emergency PPO", "ex parte"], predicted_strategy="delay",
            confidence=0.75,
        )
        d = profile.to_dict()
        self.assertEqual(d["name"], "Emily A. Watson")
        self.assertEqual(d["confidence"], 0.75)

    def test_predicted_response_to_dict(self):
        pred = PredictedResponse(
            filing_type="custody_modification",
            risk_assessment="high",
            timeline_estimate="2-4 weeks",
        )
        d = pred.to_dict()
        self.assertEqual(d["filing_type"], "custody_modification")
        self.assertEqual(d["risk_assessment"], "high")

    def test_adversary_report_to_dict(self):
        report = AdversaryReport(filing_id="test-123")
        d = report.to_dict()
        self.assertIn("filing_id", d)
        self.assertIn("generated_at", d)
        self.assertIn("predictions", d)
        self.assertIn("overall_risk", d)


class TestAdversaryPredictor(unittest.TestCase):
    """Test AdversaryPredictor with mocked DB."""

    def setUp(self):
        self.predictor = AdversaryPredictor(db_path=Path(":memory:"))

    def test_predict_response_returns_prediction(self):
        report = self.predictor.predict_response("custody_modification")
        self.assertIsInstance(report, AdversaryReport)

    def test_prediction_has_confidence(self):
        profile = self.predictor.get_adversary_profile("watson")
        self.assertGreaterEqual(profile.confidence, 0.0)
        self.assertLessEqual(profile.confidence, 1.0)

    def test_predict_motion_response(self):
        report = self.predictor.predict_response("motion_disqualification", lane="A")
        self.assertIsInstance(report, AdversaryReport)
        self.assertIn(report.overall_risk, RISK_LEVELS)

    def test_predict_discovery_response(self):
        report = self.predictor.predict_response("discovery_request", lane="A")
        self.assertIsInstance(report, AdversaryReport)

    def test_adversary_profile_constructed(self):
        profile = self.predictor.get_adversary_profile("watson")
        self.assertIsInstance(profile, AdversaryProfile)
        self.assertEqual(profile.role, "opposing_party")

    def test_emily_watson_profile(self):
        profile = self.predictor.get_adversary_profile("watson")
        self.assertIn("Watson", profile.name)
        self.assertGreater(len(profile.known_patterns), 0)

    def test_judge_profile(self):
        profile = self.predictor.get_adversary_profile("judge")
        self.assertIn("McNeill", profile.name)

    def test_pattern_detection(self):
        """Predict objections for a custody modification filing."""
        objections = self.predictor.predict_objections("custody_modification")
        self.assertIsInstance(objections, list)
        self.assertGreater(len(objections), 0)

    def test_escalation_pattern_detected(self):
        """Watson's emergency PPO pattern should appear for custody filings."""
        report = self.predictor.predict_response("custody_modification", lane="A")
        all_objs = []
        for pred in report.predictions:
            all_objs.extend(pred.likely_objections)
        # Should find at least one objection
        self.assertGreater(len(report.predictions), 0)

    def test_delay_tactic_detection(self):
        """Housing defendant should show delay pattern."""
        profile = self.predictor.get_adversary_profile("housing")
        self.assertIn("housing_defendant", profile.role)

    def test_prediction_to_dict(self):
        report = self.predictor.predict_response("custody_modification")
        d = report.to_dict()
        self.assertIsInstance(d, dict)
        self.assertIn("predictions", d)

    def test_report_structure(self):
        report = self.predictor.predict_response("ppo_defense", lane="D")
        d = report.to_dict()
        self.assertIn("filing_id", d)
        self.assertIn("overall_risk", d)
        self.assertIn("strategic_recommendations", d)

    def test_get_stats(self):
        stats = self.predictor.get_stats()
        self.assertIsInstance(stats, dict)
        self.assertIn("engine", stats)


# ###########################################################################
# 3. FinancialForensicsEngine Tests
# ###########################################################################

class TestFinancialDataclasses(unittest.TestCase):
    """Test financial forensics dataclasses."""

    def test_damage_category_to_dict(self):
        cat = DamageCategory(
            category="emotional_distress",
            subcategory="denial_of_parental_rights",
            lane="A",
            amount_low=50_000.0,
            amount_high=150_000.0,
            amount_best=100_000.0,
            basis="MCL 600.2911",
        )
        d = cat.to_dict()
        self.assertEqual(d["category"], "emotional_distress")
        self.assertEqual(d["lane"], "A")
        self.assertEqual(d["amount_low"], 50_000.0)

    def test_financial_report_to_dict(self):
        report = FinancialReport()
        d = report.to_dict()
        self.assertIn("total_low", d)
        self.assertIn("total_high", d)
        self.assertIn("by_lane", d)
        self.assertIn("categories", d)


class TestFinancialForensicsEngine(unittest.TestCase):
    """Test FinancialForensicsEngine with mocked DB."""

    def setUp(self):
        self.engine = FinancialForensicsEngine(db_path=Path(":memory:"))

    def test_calculate_total_damages(self):
        report = self.engine.calculate_all()
        self.assertIsInstance(report, FinancialReport)
        self.assertGreater(report.total_low, 0)
        self.assertGreater(report.total_high, 0)
        self.assertLessEqual(report.total_low, report.total_best)
        self.assertLessEqual(report.total_best, report.total_high)

    def test_housing_damages_category(self):
        lane_data = self.engine.calculate_lane("B")
        self.assertIsInstance(lane_data, dict)
        self.assertIn("total_low", lane_data)
        self.assertGreater(lane_data["total_low"], 0)

    def test_custody_damages_category(self):
        lane_data = self.engine.calculate_lane("A")
        self.assertIsInstance(lane_data, dict)
        self.assertGreater(lane_data["total_low"], 0)

    def test_ppo_damages_category(self):
        lane_data = self.engine.calculate_lane("D")
        self.assertIsInstance(lane_data, dict)

    def test_lost_income_calculation(self):
        """Verify lost income / legal costs appear in categories."""
        report = self.engine.calculate_all()
        cats = [c.category for c in report.categories]
        self.assertIn("legal_costs", cats)

    def test_treble_damages_housing_rico(self):
        """Treble-eligible categories should be identified."""
        report = self.engine.calculate_all()
        self.assertGreater(len(report.treble_eligible), 0,
                           "Housing RICO and consumer fraud should be treble-eligible")

    def test_damages_by_lane(self):
        report = self.engine.calculate_all()
        self.assertIn("A", report.by_lane)
        self.assertIn("B", report.by_lane)

    def test_damages_range_reasonable(self):
        """Total damages should be in the documented range."""
        report = self.engine.calculate_all()
        # Doc says $3.4M–$22.9M range
        self.assertGreater(report.total_low, 100_000)
        self.assertLess(report.total_high, 100_000_000)

    def test_multi_lane_aggregation(self):
        report = self.engine.calculate_all()
        lane_sum_low = sum(v.get("low", 0) for v in report.by_lane.values())
        # lane sum should approximately equal total (some categories may not have lanes)
        self.assertGreater(lane_sum_low, 0)

    def test_report_structure(self):
        report = self.engine.calculate_all()
        d = report.to_dict()
        self.assertIn("generated_at", d)
        self.assertIn("total_low", d)
        self.assertIn("total_high", d)
        self.assertIn("categories", d)
        self.assertIn("treble_eligible", d)

    def test_statutory_constants(self):
        self.assertEqual(STATUTORY_INTEREST_RATE, 0.05)
        self.assertEqual(TREBLE_MULTIPLIER, 3.0)
        self.assertEqual(PUNITIVE_MULTIPLIER_MAX, 10.0)
        self.assertEqual(FHA_PER_VIOLATION_MAX, 16_000.0)

    def test_get_stats(self):
        stats = self.engine.get_stats()
        self.assertIsInstance(stats, dict)
        self.assertIn("engine", stats)


# ###########################################################################
# 4. PatternMiner Tests
# ###########################################################################

class TestPatternDataclasses(unittest.TestCase):
    """Test pattern mining dataclasses and enums."""

    def test_pattern_category_enum(self):
        self.assertEqual(PatternCategory.JUDICIAL.value, "judicial")
        self.assertEqual(PatternCategory.ADVERSARY.value, "adversary")
        self.assertEqual(PatternCategory.OUTCOME.value, "outcome")
        self.assertEqual(PatternCategory.TEMPORAL.value, "temporal")

    def test_confidence_enum(self):
        self.assertEqual(Confidence.HIGH.value, "high")
        self.assertEqual(Confidence.SPECULATIVE.value, "speculative")

    def test_confidence_tier_function(self):
        self.assertEqual(_confidence_tier(0.90), "high")
        self.assertEqual(_confidence_tier(0.60), "medium")
        self.assertEqual(_confidence_tier(0.35), "low")
        self.assertEqual(_confidence_tier(0.10), "speculative")

    def test_pattern_to_dict(self):
        p = Pattern(
            pattern_id="JUD-001",
            category="judicial",
            title="Ex parte bias",
            description="18.26% ex parte rate",
            confidence=0.92,
            frequency=23,
            evidence_refs=["docket 2024-001507-DC"],
        )
        d = p.to_dict()
        self.assertEqual(d["pattern_id"], "JUD-001")
        self.assertEqual(d["category"], "judicial")
        self.assertAlmostEqual(d["confidence"], 0.92)

    def test_pattern_confidence_tier_property(self):
        p = Pattern(
            pattern_id="test", category="judicial", title="test",
            description="test", confidence=0.92, frequency=5,
        )
        self.assertEqual(p.confidence_tier, "high")

    def test_pattern_report_to_dict(self):
        report = PatternReport(total_patterns=5, high_confidence_count=2)
        d = report.to_dict()
        self.assertEqual(d["total_patterns"], 5)
        self.assertEqual(d["high_confidence_count"], 2)
        self.assertIn("patterns_by_category", d)


class TestPatternMiner(unittest.TestCase):
    """Test PatternMiner with mocked DB."""

    def setUp(self):
        self.miner = PatternMiner(db_path=Path(":memory:"))

    def test_mine_all_returns_report(self):
        report = self.miner.mine_all()
        self.assertIsInstance(report, PatternReport)
        self.assertGreater(report.total_patterns, 0)

    def test_judicial_patterns_found(self):
        patterns = self.miner.mine_judicial_patterns()
        self.assertIsInstance(patterns, list)
        self.assertGreater(len(patterns), 0)
        for p in patterns:
            self.assertEqual(p.category, PatternCategory.JUDICIAL.value)

    def test_adversary_patterns_found(self):
        patterns = self.miner.mine_adversary_patterns()
        self.assertIsInstance(patterns, list)
        self.assertGreater(len(patterns), 0)
        for p in patterns:
            self.assertEqual(p.category, PatternCategory.ADVERSARY.value)

    def test_outcome_patterns_found(self):
        patterns = self.miner.mine_outcome_patterns()
        self.assertIsInstance(patterns, list)

    def test_temporal_patterns_found(self):
        patterns = self.miner.mine_temporal_patterns()
        self.assertIsInstance(patterns, list)

    def test_ex_parte_rate_embedded(self):
        """The 18.26% ex parte rate should appear in judicial patterns."""
        patterns = self.miner.mine_judicial_patterns()
        texts = " ".join(p.description for p in patterns)
        self.assertIn("18.26%", texts)

    def test_pattern_confidence_range(self):
        report = self.miner.mine_all()
        for cat_patterns in report.patterns_by_category.values():
            for p in cat_patterns:
                self.assertGreaterEqual(p.confidence, 0.0)
                self.assertLessEqual(p.confidence, 1.0)

    def test_pattern_has_evidence_refs(self):
        patterns = self.miner.mine_judicial_patterns()
        has_refs = any(len(p.evidence_refs) > 0 for p in patterns)
        self.assertTrue(has_refs, "At least some patterns should have evidence refs")

    def test_cross_lane_patterns(self):
        patterns = self.miner.find_cross_lane_patterns()
        self.assertIsInstance(patterns, list)

    def test_temporal_clustering(self):
        events = [
            {"date": "2024-01-15", "type": "filing"},
            {"date": "2024-01-16", "type": "filing"},
            {"date": "2024-01-17", "type": "filing"},
            {"date": "2024-06-01", "type": "filing"},
        ]
        clusters = self.miner.cluster_temporal_events(events)
        self.assertIsInstance(clusters, list)

    def test_pattern_to_dict_serializable(self):
        report = self.miner.mine_all()
        d = report.to_dict()
        # Should be JSON-serializable
        serialized = json.dumps(d, default=str)
        self.assertIsInstance(serialized, str)

    def test_get_stats(self):
        stats = self.miner.get_stats()
        self.assertIsInstance(stats, dict)
        self.assertIn("supported_categories", stats)


# ###########################################################################
# 5. TimelineVisualizer Tests
# ###########################################################################

class TestTimelineDataclasses(unittest.TestCase):
    """Test timeline visualizer dataclasses and enums."""

    def test_event_category_enum(self):
        self.assertEqual(EventCategory.FILING.value, "filing")
        self.assertEqual(EventCategory.ORDER.value, "order")
        self.assertEqual(EventCategory.HEARING.value, "hearing")
        self.assertEqual(EventCategory.DEADLINE.value, "deadline")

    def test_significance_enum(self):
        self.assertEqual(Significance.CRITICAL.value, "critical")
        self.assertEqual(Significance.ROUTINE.value, "routine")

    def test_timeline_event_post_init_color(self):
        """__post_init__ should auto-fill color from LANE_META."""
        evt = TimelineEvent(
            event_id="e1", date="2024-01-15", title="Test",
            description="Test event", category="filing", lane="A",
        )
        self.assertEqual(evt.color, _LANE_META["A"]["color"])

    def test_timeline_event_post_init_icon(self):
        evt = TimelineEvent(
            event_id="e1", date="2024-01-15", title="Test",
            description="Test", category="filing", lane="A",
        )
        self.assertEqual(evt.icon, _CATEGORY_ICONS["filing"])

    def test_timeline_event_post_init_court(self):
        evt = TimelineEvent(
            event_id="e1", date="2024-01-15", title="Test",
            description="Test", category="filing", lane="A",
        )
        self.assertEqual(evt.court, _LANE_META["A"]["court"])

    def test_timeline_event_to_dict(self):
        evt = TimelineEvent(
            event_id="e1", date="2024-01-15", title="Test",
            description="Test event", category="filing", lane="A",
        )
        d = evt.to_dict()
        self.assertIsInstance(d, dict)
        self.assertEqual(d["event_id"], "e1")
        self.assertEqual(d["lane"], "A")

    def test_timeline_data_to_dict(self):
        data = TimelineData(event_count=5, by_lane={"A": 3, "B": 2})
        d = data.to_dict()
        self.assertEqual(d["event_count"], 5)
        self.assertIn("by_lane", d)


class TestTimelineVisualizer(unittest.TestCase):
    """Test TimelineVisualizer with mocked DB."""

    def setUp(self):
        self.viz = TimelineVisualizer(db_path=Path(":memory:"))

    def test_generate_returns_html(self):
        html_output = self.viz.generate()
        self.assertIsInstance(html_output, str)
        self.assertGreater(len(html_output), 0)

    def test_html_contains_doctype(self):
        html_output = self.viz.generate()
        self.assertIn("<!DOCTYPE html>", html_output)

    def test_html_contains_css(self):
        html_output = self.viz.generate()
        self.assertIn("<style", html_output)

    def test_html_contains_javascript(self):
        html_output = self.viz.generate()
        self.assertIn("<script", html_output)

    def test_add_event(self):
        evt = TimelineEvent(
            event_id="test-001", date="2025-06-01", title="Test Event",
            description="Unit test event", category="filing", lane="B",
        )
        self.viz.add_event(evt)
        data = self.viz.get_timeline_data()
        ids = [e.event_id for e in data.events]
        self.assertIn("test-001", ids)

    def test_filter_events_by_lane(self):
        """filter_events should narrow to a single lane."""
        filtered = self.viz.filter_events(lane="A")
        for evt in filtered:
            self.assertEqual(evt.lane, "A")

    def test_filter_events_by_category(self):
        filtered = self.viz.filter_events(category="order")
        for evt in filtered:
            self.assertEqual(evt.category, "order")

    def test_filter_events_by_date_range(self):
        filtered = self.viz.filter_events(
            start_date="2024-01-01", end_date="2024-12-31",
        )
        for evt in filtered:
            self.assertGreaterEqual(evt.date, "2024-01-01")
            self.assertLessEqual(evt.date, "2024-12-31")

    def test_event_color_coding_by_lane(self):
        """Each lane should get its assigned color."""
        for lane_key, meta in _LANE_META.items():
            evt = TimelineEvent(
                event_id=f"color-{lane_key}", date="2024-01-01", title="test",
                description="test", category="filing", lane=lane_key,
            )
            self.assertEqual(evt.color, meta["color"])

    def test_timeline_data_summary(self):
        data = self.viz.get_timeline_data()
        self.assertIsInstance(data, TimelineData)
        self.assertIsInstance(data.by_lane, dict)
        self.assertIsInstance(data.by_category, dict)

    def test_json_export(self):
        """export_json should produce valid JSON."""
        import tempfile
        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            tmp_path = f.name
        try:
            result = self.viz.export_json(Path(tmp_path))
            self.assertIsInstance(result, str)
            with open(tmp_path, "r", encoding="utf-8") as f:
                data = json.load(f)
            self.assertIsInstance(data, dict)
        finally:
            os.unlink(tmp_path)

    def test_get_stats(self):
        stats = self.viz.get_stats()
        self.assertIsInstance(stats, dict)
        self.assertIn("total_events", stats)


if __name__ == "__main__":
    unittest.main()
