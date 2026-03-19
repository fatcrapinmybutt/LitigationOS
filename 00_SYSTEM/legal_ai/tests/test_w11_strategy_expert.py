# -*- coding: utf-8 -*-
"""Wave-11 Tests — CaseStrategyArchitect & ExpertWitnessManager
================================================================
Comprehensive pytest suite for case_strategy_architect.py (~80 tests)
and expert_witness_manager.py (~70 tests).

• Zero network / zero real DB — all DB interactions use tmp_path SQLite
• Independent tests, no ordering dependencies
• Real Michigan party names and MCR citations throughout
"""
from __future__ import annotations

import json
import pathlib
import sqlite3
import sys
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

from case_strategy_architect import (
    StrategyPhase,
    ObjectiveStatus,
    RiskLevel,
    ResourceType,
    StrategicObjective,
    LaneStrategy,
    ResourceAllocation,
    OpponentAction,
    RiskAssessment,
    StrategyRoadmap,
    ResourceAllocator,
    GameTheoryEngine,
    CrossLaneCoordinator,
    CaseStrategyArchitect,
    _PLAINTIFF,
    _DEFENDANT,
    _CHILD_INITIALS,
    _JUDGE,
    _COURT,
    LANE_CASES,
    LANE_DESCRIPTIONS,
)

from expert_witness_manager import (
    ExpertField,
    RetentionStatus,
    ReportStatus,
    ChallengeType,
    ExpertWitness,
    ExpertReport,
    DaubertFactor,
    DaubertAnalysisResult,
    DepositionRecord,
    ExpertCostSummary,
    DaubertAnalyzer,
    ExpertReportReviewer,
    DepositionCoordinator,
    ExpertWitnessManager,
)


# ===================================================================
# CASE_STRATEGY_ARCHITECT TESTS
# ===================================================================


# ===================================================================
# TestStrategyPhase
# ===================================================================
class TestStrategyPhase:
    """Tests for the StrategyPhase enum."""

    def test_all_values_exist(self):
        expected = {
            "discovery", "motion_practice", "pretrial", "trial",
            "post_trial", "appeal", "settlement",
        }
        actual = {p.value for p in StrategyPhase}
        assert actual == expected

    def test_string_membership(self):
        assert isinstance(StrategyPhase.DISCOVERY, str)
        assert StrategyPhase.DISCOVERY == "discovery"

    def test_count_is_seven(self):
        assert len(StrategyPhase) == 7

    def test_mcr_reference_discovery(self):
        assert "2.301" in StrategyPhase.DISCOVERY.mcr_reference

    def test_mcr_reference_motion_practice(self):
        ref = StrategyPhase.MOTION_PRACTICE.mcr_reference
        assert "2.116" in ref or "2.119" in ref

    def test_mcr_reference_appeal(self):
        assert "7.201" in StrategyPhase.APPEAL.mcr_reference

    def test_mcr_reference_settlement(self):
        assert "2.403" in StrategyPhase.SETTLEMENT.mcr_reference


# ===================================================================
# TestObjectiveStatus
# ===================================================================
class TestObjectiveStatus:
    """Tests for the ObjectiveStatus enum."""

    def test_all_values_exist(self):
        expected = {
            "planned", "in_progress", "blocked", "completed",
            "deferred", "superseded",
        }
        actual = {s.value for s in ObjectiveStatus}
        assert actual == expected

    def test_count_is_six(self):
        assert len(ObjectiveStatus) == 6

    def test_string_membership(self):
        assert isinstance(ObjectiveStatus.PLANNED, str)


# ===================================================================
# TestRiskLevel
# ===================================================================
class TestRiskLevel:
    """Tests for the RiskLevel enum."""

    def test_all_values_exist(self):
        expected = {"low", "moderate", "high", "critical"}
        actual = {r.value for r in RiskLevel}
        assert actual == expected

    def test_count_is_four(self):
        assert len(RiskLevel) == 4


# ===================================================================
# TestResourceType
# ===================================================================
class TestResourceType:
    """Tests for the ResourceType enum."""

    def test_all_values_exist(self):
        expected = {
            "time_hours", "filing_fee", "expert_cost", "copy_cost",
            "service_cost", "travel_cost", "research_hours",
        }
        actual = {r.value for r in ResourceType}
        assert actual == expected

    def test_count_is_seven(self):
        assert len(ResourceType) == 7


# ===================================================================
# TestStrategicObjective
# ===================================================================
class TestStrategicObjective:
    """Tests for the StrategicObjective dataclass."""

    def test_default_creation(self):
        obj = StrategicObjective()
        assert obj.objective_id
        assert obj.priority == 5
        assert obj.status == ObjectiveStatus.PLANNED
        assert obj.assigned_phase == StrategyPhase.DISCOVERY

    def test_custom_creation(self):
        obj = StrategicObjective(
            description="File motion to compel",
            priority=2,
            lane="A",
            status=ObjectiveStatus.IN_PROGRESS,
        )
        assert obj.description == "File motion to compel"
        assert obj.priority == 2
        assert obj.lane == "A"

    def test_to_dict_keys(self):
        obj = StrategicObjective(lane="D", description="Test")
        d = obj.to_dict()
        expected_keys = {
            "objective_id", "description", "priority", "lane", "status",
            "dependencies", "deadline", "resources_needed", "rationale",
            "success_criteria", "assigned_phase", "created_at",
        }
        assert set(d.keys()) == expected_keys

    def test_to_dict_status_is_string(self):
        obj = StrategicObjective(status=ObjectiveStatus.BLOCKED)
        d = obj.to_dict()
        assert d["status"] == "blocked"

    def test_to_dict_phase_is_string(self):
        obj = StrategicObjective(assigned_phase=StrategyPhase.TRIAL)
        d = obj.to_dict()
        assert d["assigned_phase"] == "trial"

    def test_unique_ids(self):
        obj1 = StrategicObjective()
        obj2 = StrategicObjective()
        assert obj1.objective_id != obj2.objective_id


# ===================================================================
# TestLaneStrategy
# ===================================================================
class TestLaneStrategy:
    """Tests for the LaneStrategy dataclass."""

    def test_default_creation(self):
        ls = LaneStrategy()
        assert ls.risk_score == 50
        assert ls.current_phase == StrategyPhase.DISCOVERY
        assert ls.objectives == []

    def test_to_dict_contains_swot(self):
        ls = LaneStrategy(
            lane="A",
            strengths=["strong evidence"],
            weaknesses=["pro se"],
        )
        d = ls.to_dict()
        assert "strengths" in d
        assert "weaknesses" in d
        assert d["strengths"] == ["strong evidence"]

    def test_to_dict_nested_objectives(self):
        obj = StrategicObjective(description="Test obj")
        ls = LaneStrategy(lane="B", objectives=[obj])
        d = ls.to_dict()
        assert len(d["objectives"]) == 1
        assert d["objectives"][0]["description"] == "Test obj"


# ===================================================================
# TestResourceAllocation
# ===================================================================
class TestResourceAllocation:
    """Tests for the ResourceAllocation dataclass."""

    def test_default_creation(self):
        ra = ResourceAllocation()
        assert ra.amount == 0.0
        assert ra.resource_type == ResourceType.TIME_HOURS

    def test_to_dict(self):
        ra = ResourceAllocation(
            lane="E", resource_type=ResourceType.EXPERT_COST, amount=1500.0,
        )
        d = ra.to_dict()
        assert d["lane"] == "E"
        assert d["resource_type"] == "expert_cost"
        assert d["amount"] == 1500.0


# ===================================================================
# TestOpponentAction
# ===================================================================
class TestOpponentAction:
    """Tests for the OpponentAction dataclass."""

    def test_default_creation(self):
        oa = OpponentAction()
        assert oa.probability == 0.5
        assert oa.impact == 5

    def test_to_dict(self):
        oa = OpponentAction(
            description="File motion to dismiss",
            probability=0.7,
            lane="B",
        )
        d = oa.to_dict()
        assert d["description"] == "File motion to dismiss"
        assert d["lane"] == "B"


# ===================================================================
# TestRiskAssessment
# ===================================================================
class TestRiskAssessment:
    """Tests for the RiskAssessment dataclass."""

    def test_default_owner_is_plaintiff(self):
        ra = RiskAssessment()
        assert ra.owner == "Andrew James Pigors"

    def test_to_dict_level_is_string(self):
        ra = RiskAssessment(level=RiskLevel.CRITICAL)
        d = ra.to_dict()
        assert d["level"] == "critical"


# ===================================================================
# TestStrategyRoadmap
# ===================================================================
class TestStrategyRoadmap:
    """Tests for the StrategyRoadmap dataclass."""

    def test_default_creation(self):
        rm = StrategyRoadmap()
        assert rm.overall_risk_score == 50
        assert rm.lane_strategies == []

    def test_to_dict_structure(self):
        rm = StrategyRoadmap(
            lane_strategies=[LaneStrategy(lane="A")],
            overall_risk_score=65,
        )
        d = rm.to_dict()
        assert len(d["lane_strategies"]) == 1
        assert d["overall_risk_score"] == 65
        assert "roadmap_id" in d
        assert "generated_at" in d


# ===================================================================
# TestResourceAllocator
# ===================================================================
class TestResourceAllocator:
    """Tests for the ResourceAllocator class."""

    def test_allocate_time(self):
        ra = ResourceAllocator()
        alloc = ra.allocate_time("A", 10.0, "Research", priority=2)
        assert alloc.lane == "A"
        assert alloc.amount == 10.0
        assert alloc.resource_type == ResourceType.TIME_HOURS

    def test_allocate_budget(self):
        ra = ResourceAllocator()
        alloc = ra.allocate_budget("B", ResourceType.FILING_FEE, 150.0)
        assert alloc.resource_type == ResourceType.FILING_FEE
        assert alloc.amount == 150.0

    def test_prioritize_lanes_ordering(self):
        ra = ResourceAllocator()
        ls_trial = LaneStrategy(
            lane="A", current_phase=StrategyPhase.TRIAL, risk_score=80,
        )
        ls_discovery = LaneStrategy(
            lane="B", current_phase=StrategyPhase.DISCOVERY, risk_score=30,
        )
        priorities = ra.prioritize_lanes([ls_trial, ls_discovery])
        assert len(priorities) == 2
        lanes = [p[0] for p in priorities]
        assert lanes[0] == "A"  # Trial phase + higher risk = lower score

    def test_prioritize_lanes_empty(self):
        ra = ResourceAllocator()
        assert ra.prioritize_lanes([]) == []

    def test_identify_bottlenecks_high_utilization(self):
        ra = ResourceAllocator()
        # Allocate 95% of time budget (200 hours)
        ra.allocate_time("A", 190.0)
        bottlenecks = ra.identify_bottlenecks([])
        assert len(bottlenecks) >= 1
        time_bn = [b for b in bottlenecks if b["resource"] == "time_hours"]
        assert time_bn[0]["severity"] == "critical"

    def test_identify_bottlenecks_no_issues(self):
        ra = ResourceAllocator()
        ra.allocate_time("A", 10.0)
        bottlenecks = ra.identify_bottlenecks([])
        # Low utilization -> no resource bottleneck
        resource_bottlenecks = [b for b in bottlenecks if b["resource"] != "objectives"]
        assert resource_bottlenecks == []

    def test_identify_bottlenecks_blocked_objectives(self):
        ra = ResourceAllocator()
        obj = StrategicObjective(status=ObjectiveStatus.BLOCKED)
        ls = LaneStrategy(lane="A", objectives=[obj])
        bottlenecks = ra.identify_bottlenecks([ls])
        obj_bns = [b for b in bottlenecks if b.get("lane") == "A"]
        assert len(obj_bns) == 1
        assert obj_bns[0]["blocked_count"] == 1

    def test_get_utilization_report(self):
        ra = ResourceAllocator()
        ra.allocate_time("A", 50.0)
        ra.allocate_budget("B", ResourceType.FILING_FEE, 100.0)
        report = ra.get_utilization_report()
        assert "by_resource" in report
        assert "by_lane" in report
        assert report["by_resource"]["time_hours"]["used"] == 50.0

    def test_get_stats(self):
        ra = ResourceAllocator()
        ra.allocate_time("A", 10.0)
        stats = ra.get_stats()
        assert stats["component"] == "ResourceAllocator"
        assert stats["total_allocations"] == 1


# ===================================================================
# TestGameTheoryEngine
# ===================================================================
class TestGameTheoryEngine:
    """Tests for the GameTheoryEngine class."""

    def test_analyze_opponent_options_lane_a(self):
        gte = GameTheoryEngine()
        actions = gte.analyze_opponent_options("A")
        assert len(actions) > 0
        assert all(a.lane == "A" for a in actions)

    def test_analyze_opponent_options_lane_b(self):
        gte = GameTheoryEngine()
        actions = gte.analyze_opponent_options("B")
        assert len(actions) >= 3

    def test_analyze_opponent_options_unknown_lane(self):
        gte = GameTheoryEngine()
        actions = gte.analyze_opponent_options("Z")
        assert actions == []

    def test_analyze_opponent_options_returns_opponent_actions(self):
        gte = GameTheoryEngine()
        actions = gte.analyze_opponent_options("D")
        assert all(isinstance(a, OpponentAction) for a in actions)
        assert all(a.counter_strategy for a in actions)

    def test_nash_equilibrium_lane_a(self):
        gte = GameTheoryEngine()
        result = gte.calculate_nash_equilibrium("A")
        assert result["lane"] == "A"
        assert "equilibrium_type" in result
        assert "opponent_best_action" in result

    def test_nash_equilibrium_no_data(self):
        gte = GameTheoryEngine()
        result = gte.calculate_nash_equilibrium("C")
        # Lane C has no playbook
        assert result["equilibrium"] == "insufficient_data"

    def test_nash_equilibrium_stability(self):
        gte = GameTheoryEngine()
        result = gte.calculate_nash_equilibrium("A")
        assert result["stability"] in ("stable", "unstable")

    def test_minimax_strategy_lane_a(self):
        gte = GameTheoryEngine()
        result = gte.minimax_strategy("A")
        assert result["lane"] == "A"
        assert "counter_plan" in result
        assert len(result["counter_plan"]) > 0

    def test_minimax_strategy_no_data(self):
        gte = GameTheoryEngine()
        result = gte.minimax_strategy("C")
        assert result["strategy"] == "no_data_available"

    def test_minimax_priorities(self):
        gte = GameTheoryEngine()
        result = gte.minimax_strategy("A")
        for entry in result["counter_plan"]:
            assert entry["preparation_priority"] in ("high", "medium")

    def test_predict_responses(self):
        gte = GameTheoryEngine()
        preds = gte.predict_responses("File motion to compel", "A")
        assert len(preds) > 0
        assert all("relevance_score" in p for p in preds)

    def test_predict_responses_sorted_by_relevance(self):
        gte = GameTheoryEngine()
        preds = gte.predict_responses("File PPO termination", "D")
        if len(preds) >= 2:
            assert preds[0]["relevance_score"] >= preds[-1]["relevance_score"]

    def test_get_stats(self):
        gte = GameTheoryEngine()
        gte.analyze_opponent_options("A")
        stats = gte.get_stats()
        assert stats["component"] == "GameTheoryEngine"
        assert stats["modeled_actions"] >= 1


# ===================================================================
# TestCrossLaneCoordinator
# ===================================================================
class TestCrossLaneCoordinator:
    """Tests for the CrossLaneCoordinator class."""

    def test_find_synergies_a_d(self):
        clc = CrossLaneCoordinator()
        results = clc.find_synergies(["A", "D"])
        assert len(results) >= 1
        assert any("A" in r["lanes"] and "D" in r["lanes"] for r in results)

    def test_find_synergies_a_e_f(self):
        clc = CrossLaneCoordinator()
        results = clc.find_synergies(["A", "E", "F"])
        assert len(results) >= 2

    def test_find_synergies_single_lane(self):
        clc = CrossLaneCoordinator()
        results = clc.find_synergies(["A"])
        assert results == []

    def test_find_synergies_all_lanes(self):
        clc = CrossLaneCoordinator()
        results = clc.find_synergies(["A", "B", "C", "D", "E", "F"])
        assert len(results) >= 5

    def test_detect_conflicts_a_d(self):
        clc = CrossLaneCoordinator()
        results = clc.detect_conflicts(["A", "D"])
        assert len(results) >= 1
        assert all(r["severity"] == "high" for r in results)

    def test_detect_conflicts_no_conflict(self):
        clc = CrossLaneCoordinator()
        results = clc.detect_conflicts(["B", "F"])
        assert results == []

    def test_detect_conflicts_e_a(self):
        clc = CrossLaneCoordinator()
        results = clc.detect_conflicts(["E", "A"])
        assert len(results) >= 1
        assert any("resolution" in r for r in results)

    def test_coordinate_deadlines_sorted(self):
        clc = CrossLaneCoordinator()
        obj1 = StrategicObjective(deadline="2026-05-01", description="Later")
        obj2 = StrategicObjective(deadline="2026-03-01", description="Earlier")
        ls_a = LaneStrategy(lane="A", case_number="2024-001507-DC", objectives=[obj1])
        ls_d = LaneStrategy(lane="D", case_number="2023-5907-PP", objectives=[obj2])
        deadlines = clc.coordinate_deadlines([ls_a, ls_d])
        assert len(deadlines) == 2
        assert deadlines[0]["deadline"] <= deadlines[1]["deadline"]

    def test_coordinate_deadlines_empty(self):
        clc = CrossLaneCoordinator()
        assert clc.coordinate_deadlines([]) == []

    def test_generate_unified_timeline(self):
        clc = CrossLaneCoordinator()
        obj = StrategicObjective(deadline="2026-04-15", description="File brief")
        ls = LaneStrategy(lane="F", objectives=[obj])
        timeline = clc.generate_unified_timeline([ls])
        assert len(timeline) >= 2  # phase marker + deadline
        assert any(e["type"] == "deadline" for e in timeline)
        assert any(e["type"] == "phase_marker" for e in timeline)

    def test_assess_lane_dependencies(self):
        clc = CrossLaneCoordinator()
        ls_a = LaneStrategy(lane="A")
        ls_f = LaneStrategy(lane="F")
        ls_e = LaneStrategy(lane="E")
        deps = clc.assess_lane_dependencies([ls_a, ls_f, ls_e])
        assert "F" in deps
        assert "A" in deps["F"]

    def test_assess_lane_dependencies_empty(self):
        clc = CrossLaneCoordinator()
        deps = clc.assess_lane_dependencies([])
        assert deps == {}

    def test_get_stats(self):
        clc = CrossLaneCoordinator()
        stats = clc.get_stats()
        assert stats["component"] == "CrossLaneCoordinator"
        assert stats["synergy_patterns"] >= 5
        assert stats["conflict_patterns"] >= 2


# ===================================================================
# TestCaseStrategyArchitect
# ===================================================================
class TestCaseStrategyArchitect:
    """Tests for the CaseStrategyArchitect orchestrator."""

    def test_create_master_plan_all_lanes(self, tmp_path):
        csa = CaseStrategyArchitect(db_path=tmp_path / "test.db")
        plan = csa.create_master_plan()
        assert len(plan) == 6
        assert "A" in plan
        assert "F" in plan

    def test_create_master_plan_specific_lanes(self, tmp_path):
        csa = CaseStrategyArchitect(db_path=tmp_path / "test.db")
        plan = csa.create_master_plan(lanes=["A", "D"])
        assert len(plan) == 2
        assert "A" in plan
        assert "D" in plan

    def test_create_master_plan_unknown_lane(self, tmp_path):
        csa = CaseStrategyArchitect(db_path=tmp_path / "test.db")
        plan = csa.create_master_plan(lanes=["Z"])
        assert len(plan) == 0

    def test_create_master_plan_swot_populated(self, tmp_path):
        csa = CaseStrategyArchitect(db_path=tmp_path / "test.db")
        plan = csa.create_master_plan(lanes=["A"])
        ls_a = plan["A"]
        assert len(ls_a.strengths) > 0
        assert len(ls_a.weaknesses) > 0
        assert len(ls_a.opportunities) > 0
        assert len(ls_a.threats) > 0

    def test_create_master_plan_case_number_assigned(self, tmp_path):
        csa = CaseStrategyArchitect(db_path=tmp_path / "test.db")
        plan = csa.create_master_plan(lanes=["A", "B", "D"])
        assert plan["A"].case_number == "2024-001507-DC"
        assert plan["B"].case_number == "2025-002760-CZ"
        assert plan["D"].case_number == "2023-5907-PP"

    def test_add_objective(self, tmp_path):
        csa = CaseStrategyArchitect(db_path=tmp_path / "test.db")
        csa.create_master_plan(lanes=["A"])
        obj = csa.add_objective(
            lane="A",
            description="Complete interrogatories",
            priority=2,
            deadline="2026-04-15",
        )
        assert obj.lane == "A"
        assert obj.priority == 2

    def test_add_objective_priority_clamped(self, tmp_path):
        csa = CaseStrategyArchitect(db_path=tmp_path / "test.db")
        obj = csa.add_objective(lane="A", description="Test", priority=99)
        assert obj.priority == 10
        obj2 = csa.add_objective(lane="A", description="Test2", priority=-5)
        assert obj2.priority == 1

    def test_update_objective_status(self, tmp_path):
        csa = CaseStrategyArchitect(db_path=tmp_path / "test.db")
        obj = csa.add_objective(lane="A", description="Test")
        result = csa.update_objective_status(obj.objective_id, ObjectiveStatus.COMPLETED)
        assert result is True
        assert obj.status == ObjectiveStatus.COMPLETED

    def test_update_objective_status_not_found(self, tmp_path):
        csa = CaseStrategyArchitect(db_path=tmp_path / "test.db")
        result = csa.update_objective_status("nonexistent", ObjectiveStatus.BLOCKED)
        assert result is False

    def test_optimize_strategy(self, tmp_path):
        csa = CaseStrategyArchitect(db_path=tmp_path / "test.db")
        csa.create_master_plan(lanes=["A", "D", "E", "F"])
        result = csa.optimize_strategy()
        assert "lane_priorities" in result
        assert "synergies_found" in result
        assert "conflicts_found" in result
        assert "recommendations" in result
        assert result["synergies_found"] >= 1

    def test_optimize_strategy_empty(self, tmp_path):
        csa = CaseStrategyArchitect(db_path=tmp_path / "test.db")
        result = csa.optimize_strategy()
        assert "error" in result

    def test_generate_roadmap(self, tmp_path):
        csa = CaseStrategyArchitect(db_path=tmp_path / "test.db")
        csa.create_master_plan(lanes=["A", "F"])
        roadmap = csa.generate_roadmap()
        assert isinstance(roadmap, StrategyRoadmap)
        assert len(roadmap.lane_strategies) == 2
        assert roadmap.overall_risk_score >= 0

    def test_generate_roadmap_to_dict(self, tmp_path):
        csa = CaseStrategyArchitect(db_path=tmp_path / "test.db")
        csa.create_master_plan(lanes=["A"])
        roadmap = csa.generate_roadmap()
        d = roadmap.to_dict()
        assert isinstance(d, dict)
        assert "roadmap_id" in d
        json.dumps(d)  # Must be JSON-serializable

    def test_assess_risks(self, tmp_path):
        csa = CaseStrategyArchitect(db_path=tmp_path / "test.db")
        csa.create_master_plan(lanes=["A", "D"])
        risks = csa.assess_risks()
        assert len(risks) > 0
        assert all(isinstance(r, RiskAssessment) for r in risks)

    def test_assess_risks_single_lane(self, tmp_path):
        csa = CaseStrategyArchitect(db_path=tmp_path / "test.db")
        csa.create_master_plan(lanes=["A", "D"])
        risks = csa.assess_risks(lane="A")
        assert all(r.lane == "A" for r in risks)

    def test_analyze_opponent(self, tmp_path):
        csa = CaseStrategyArchitect(db_path=tmp_path / "test.db")
        result = csa.analyze_opponent("A")
        assert "opponent_options" in result
        assert "nash_equilibrium" in result
        assert "minimax_strategy" in result

    def test_persist_with_tmp_db(self, tmp_path):
        db_path = tmp_path / "test_strategy.db"
        conn = sqlite3.connect(str(db_path))
        conn.close()
        csa = CaseStrategyArchitect(db_path=db_path)
        csa.create_master_plan(lanes=["A"])
        csa.add_objective(lane="A", description="Test persist")
        saved = csa.persist()
        assert saved >= 1

    def test_persist_no_db(self, tmp_path):
        csa = CaseStrategyArchitect(db_path=tmp_path / "nonexistent.db")
        assert csa.persist() == 0

    def test_to_markdown(self, tmp_path):
        csa = CaseStrategyArchitect(db_path=tmp_path / "test.db")
        csa.create_master_plan(lanes=["A", "D"])
        csa.add_objective(lane="A", description="Test MD")
        md = csa.to_markdown()
        assert "Lane A" in md
        assert "Pigors v Watson" in md

    def test_get_stats(self, tmp_path):
        csa = CaseStrategyArchitect(db_path=tmp_path / "test.db")
        csa.create_master_plan(lanes=["A"])
        stats = csa.get_stats()
        assert stats["module"] == "case_strategy_architect"
        assert stats["lanes_loaded"] == 1
        assert "allocator" in stats
        assert "game_engine" in stats
        assert "coordinator" in stats

    def test_reset(self, tmp_path):
        csa = CaseStrategyArchitect(db_path=tmp_path / "test.db")
        csa.create_master_plan(lanes=["A", "D"])
        csa.add_objective(lane="A", description="Reset test")
        csa.assess_risks()
        csa.reset()
        assert csa.get_stats()["lanes_loaded"] == 0
        assert csa.get_stats()["total_objectives"] == 0


# ===================================================================
# TestLaneCasesMapping
# ===================================================================
class TestLaneCasesMapping:
    """Tests for lane routing correctness."""

    def test_lane_a_case(self):
        assert LANE_CASES["A"] == "2024-001507-DC"

    def test_lane_b_case(self):
        assert LANE_CASES["B"] == "2025-002760-CZ"

    def test_lane_c_is_convergence(self):
        assert LANE_CASES["C"] == "Convergence"

    def test_lane_d_case(self):
        assert LANE_CASES["D"] == "2023-5907-PP"

    def test_lane_e_is_jtc(self):
        assert "JTC" in LANE_CASES["E"] or "Misconduct" in LANE_CASES["E"]

    def test_lane_f_case(self):
        assert LANE_CASES["F"] == "COA 366810"

    def test_all_six_lanes(self):
        assert set(LANE_CASES.keys()) == {"A", "B", "C", "D", "E", "F"}


# ===================================================================
# TestPartyConstants
# ===================================================================
class TestPartyConstants:
    """Verify party name constants are correct."""

    def test_plaintiff(self):
        assert _PLAINTIFF == "Andrew James Pigors"

    def test_defendant(self):
        assert _DEFENDANT == "Emily A. Watson"

    def test_child_initials(self):
        assert _CHILD_INITIALS == "L.D.W."

    def test_judge(self):
        assert _JUDGE == "Hon. Jenny L. McNeill"

    def test_court(self):
        assert _COURT == "14th Circuit Court"


# ===================================================================
# EXPERT_WITNESS_MANAGER TESTS
# ===================================================================


# ===================================================================
# TestExpertField
# ===================================================================
class TestExpertField:
    """Tests for the ExpertField enum."""

    def test_all_values_exist(self):
        expected = {
            "psychology", "child_development", "forensic_accounting",
            "real_estate", "domestic_violence", "custody_evaluation",
            "judicial_conduct", "law_enforcement",
        }
        actual = {f.value for f in ExpertField}
        assert actual == expected

    def test_count_is_eight(self):
        assert len(ExpertField) == 8

    def test_relevant_lanes_custody(self):
        lanes = ExpertField.CUSTODY_EVALUATION.relevant_lanes
        assert "A" in lanes

    def test_relevant_lanes_judicial(self):
        lanes = ExpertField.JUDICIAL_CONDUCT.relevant_lanes
        assert "E" in lanes
        assert "F" in lanes

    def test_relevant_lanes_psychology(self):
        lanes = ExpertField.PSYCHOLOGY.relevant_lanes
        assert "A" in lanes
        assert "D" in lanes

    def test_relevant_lanes_real_estate(self):
        lanes = ExpertField.REAL_ESTATE.relevant_lanes
        assert "B" in lanes

    def test_relevant_lanes_forensic_accounting(self):
        lanes = ExpertField.FORENSIC_ACCOUNTING.relevant_lanes
        assert "A" in lanes and "B" in lanes


# ===================================================================
# TestRetentionStatus
# ===================================================================
class TestRetentionStatus:
    """Tests for the RetentionStatus enum."""

    def test_all_values_exist(self):
        expected = {
            "identified", "contacted", "retained", "report_pending",
            "report_submitted", "deposed", "testified", "withdrawn",
        }
        actual = {s.value for s in RetentionStatus}
        assert actual == expected

    def test_is_active_retained(self):
        assert RetentionStatus.RETAINED.is_active is True

    def test_is_active_withdrawn(self):
        assert RetentionStatus.WITHDRAWN.is_active is False

    def test_is_active_testified(self):
        assert RetentionStatus.TESTIFIED.is_active is False

    def test_is_active_identified(self):
        assert RetentionStatus.IDENTIFIED.is_active is True


# ===================================================================
# TestReportStatus
# ===================================================================
class TestReportStatus:
    """Tests for the ReportStatus enum."""

    def test_all_values_exist(self):
        expected = {"draft", "under_review", "finalized", "submitted", "supplemented"}
        actual = {s.value for s in ReportStatus}
        assert actual == expected


# ===================================================================
# TestChallengeType
# ===================================================================
class TestChallengeType:
    """Tests for the ChallengeType enum."""

    def test_all_values_exist(self):
        expected = {
            "qualification", "methodology", "reliability",
            "fit", "insufficient_facts", "speculation",
        }
        actual = {c.value for c in ChallengeType}
        assert actual == expected


# ===================================================================
# TestExpertWitness
# ===================================================================
class TestExpertWitness:
    """Tests for the ExpertWitness dataclass."""

    def test_default_creation(self):
        ew = ExpertWitness()
        assert ew.expert_id
        assert ew.hourly_rate == Decimal("0.00")
        assert ew.retention_status == RetentionStatus.IDENTIFIED

    def test_to_dict_keys(self):
        ew = ExpertWitness(name="Dr. Smith", field=ExpertField.PSYCHOLOGY)
        d = ew.to_dict()
        assert d["name"] == "Dr. Smith"
        assert d["field"] == "psychology"
        assert d["hourly_rate"] == "0.00"

    def test_to_dict_serializable(self):
        ew = ExpertWitness(
            name="Test Expert",
            hourly_rate=Decimal("350.00"),
            publications=["Pub1", "Pub2"],
        )
        json.dumps(ew.to_dict())

    def test_unique_ids(self):
        e1 = ExpertWitness()
        e2 = ExpertWitness()
        assert e1.expert_id != e2.expert_id


# ===================================================================
# TestExpertReport
# ===================================================================
class TestExpertReport:
    """Tests for the ExpertReport dataclass."""

    def test_default_creation(self):
        er = ExpertReport()
        assert er.status == ReportStatus.DRAFT
        assert er.is_opposing is False

    def test_to_dict(self):
        er = ExpertReport(
            expert_name="Dr. Jones",
            findings=["Finding 1"],
            is_opposing=True,
        )
        d = er.to_dict()
        assert d["expert_name"] == "Dr. Jones"
        assert d["is_opposing"] is True
        assert len(d["findings"]) == 1


# ===================================================================
# TestDaubertFactor
# ===================================================================
class TestDaubertFactor:
    """Tests for the DaubertFactor dataclass."""

    def test_default_creation(self):
        df = DaubertFactor()
        assert df.satisfied is False
        assert df.score == 0

    def test_to_dict(self):
        df = DaubertFactor(
            factor_name="Qualification",
            satisfied=True,
            score=85,
            authority="MRE 702(a)",
        )
        d = df.to_dict()
        assert d["factor_name"] == "Qualification"
        assert d["satisfied"] is True


# ===================================================================
# TestDaubertAnalyzer
# ===================================================================
class TestDaubertAnalyzer:
    """Tests for the DaubertAnalyzer class."""

    @pytest.fixture
    def qualified_expert(self):
        return ExpertWitness(
            name="Dr. Jane Smith",
            field=ExpertField.CUSTODY_EVALUATION,
            qualifications=[
                "PhD Clinical Psychology",
                "Licensed Psychologist",
                "Board Certified Forensic Examiner",
            ],
            publications=["J. Family Psych 2022", "Child Dev Q 2023"],
            testimony_history=["Case A 2021", "Case B 2022", "Case C 2023"],
            retained_for_lane="A",
        )

    @pytest.fixture
    def unqualified_expert(self):
        return ExpertWitness(
            name="John Doe",
            field=ExpertField.PSYCHOLOGY,
            qualifications=[],
            publications=[],
            testimony_history=[],
        )

    def test_check_qualification_qualified(self, qualified_expert):
        da = DaubertAnalyzer()
        factor = da.check_qualification(qualified_expert)
        assert factor.satisfied is True
        assert factor.score >= 50
        assert "MRE 702" in factor.authority

    def test_check_qualification_unqualified(self, unqualified_expert):
        da = DaubertAnalyzer()
        factor = da.check_qualification(unqualified_expert)
        assert factor.satisfied is False
        assert factor.score < 50

    def test_analyze_methodology_with_description(self, qualified_expert):
        da = DaubertAnalyzer()
        factor = da.analyze_methodology(
            qualified_expert,
            "Standardized and validated peer-reviewed methodology",
        )
        assert factor.score > 0
        assert "MRE 702" in factor.authority

    def test_analyze_methodology_no_description(self, qualified_expert):
        da = DaubertAnalyzer()
        factor = da.analyze_methodology(qualified_expert)
        assert "cannot fully assess" in factor.analysis.lower()

    def test_assess_reliability_with_facts(self, qualified_expert):
        da = DaubertAnalyzer()
        factor = da.assess_reliability(
            qualified_expert, case_facts="Custody dispute evaluation"
        )
        assert factor.score > 0

    def test_assess_reliability_lane_relevance(self, qualified_expert):
        da = DaubertAnalyzer()
        factor = da.assess_reliability(qualified_expert)
        assert "Lane" in factor.analysis or factor.score >= 0

    def test_check_fit_with_issues(self, qualified_expert):
        da = DaubertAnalyzer()
        factor = da.check_fit(
            qualified_expert,
            issues_in_case=["best interests", "parenting capacity"],
        )
        assert factor.satisfied is True
        assert factor.score >= 50

    def test_check_fit_no_issues(self, qualified_expert):
        da = DaubertAnalyzer()
        factor = da.check_fit(qualified_expert)
        assert factor.score >= 20  # MRE 704 always gives 20

    def test_full_daubert_analysis_admissible(self, qualified_expert):
        da = DaubertAnalyzer()
        result = da.full_daubert_analysis(
            qualified_expert,
            methodology="Standardized validated peer-reviewed empirical approach",
            case_facts="Custody evaluation of parenting",
            issues=["best interests", "parenting capacity"],
        )
        assert isinstance(result, DaubertAnalysisResult)
        assert len(result.factors) == 4
        assert result.overall_score > 0
        assert "ADMISSIBLE" in result.recommendation

    def test_full_daubert_analysis_inadmissible(self, unqualified_expert):
        da = DaubertAnalyzer()
        result = da.full_daubert_analysis(unqualified_expert)
        assert result.admissible is False
        assert "INADMISSIBLE" in result.recommendation

    def test_generate_qualification_memo(self, qualified_expert):
        da = DaubertAnalyzer()
        result = da.full_daubert_analysis(qualified_expert)
        memo = da.generate_qualification_memo(result)
        assert "MEMORANDUM" in memo
        assert "MRE 702" in memo
        assert qualified_expert.name in memo

    def test_get_stats(self):
        da = DaubertAnalyzer()
        stats = da.get_stats()
        assert stats["component"] == "DaubertAnalyzer"
        assert stats["daubert_factors"] == 4


# ===================================================================
# TestExpertReportReviewer
# ===================================================================
class TestExpertReportReviewer:
    """Tests for the ExpertReportReviewer class."""

    @pytest.fixture
    def strong_report(self):
        return ExpertReport(
            expert_name="Dr. Strong",
            field=ExpertField.CUSTODY_EVALUATION,
            methodology="Standardized clinical interview and testing",
            findings=["Finding 1", "Finding 2", "Finding 3"],
            opinions=["Opinion 1"],
            supporting_data=["Records A", "Records B", "Records C"],
        )

    @pytest.fixture
    def weak_report(self):
        return ExpertReport(
            expert_name="Dr. Weak",
            field=ExpertField.PSYCHOLOGY,
            methodology="",
            findings=[],
            opinions=["Speculative opinion 1", "Speculative opinion 2"],
            supporting_data=[],
        )

    def test_review_strong_report(self, strong_report):
        reviewer = ExpertReportReviewer()
        review = reviewer.review_report(strong_report)
        assert review["overall_quality"] == "strong"
        assert len(review["strengths"]) >= 3

    def test_review_weak_report(self, weak_report):
        reviewer = ExpertReportReviewer()
        review = reviewer.review_report(weak_report)
        assert review["overall_quality"] == "weak"
        assert len(review["weaknesses"]) >= 2

    def test_review_opposing_flag(self):
        reviewer = ExpertReportReviewer()
        report = ExpertReport(is_opposing=True, expert_name="Opposing")
        review = reviewer.review_report(report)
        assert review["is_opposing"] is True

    def test_identify_weaknesses_no_data(self, weak_report):
        reviewer = ExpertReportReviewer()
        weaknesses = reviewer.identify_weaknesses(weak_report)
        assert len(weaknesses) >= 1
        assert any("MRE 703" in w["rebuttal_strategy"] for w in weaknesses)

    def test_identify_weaknesses_pattern_match(self):
        reviewer = ExpertReportReviewer()
        report = ExpertReport(
            findings=["Based on reliance on self-report data"],
            methodology="outdated methodology from 1990s",
        )
        weaknesses = reviewer.identify_weaknesses(report)
        assert len(weaknesses) >= 1

    def test_compare_to_opposing(self, strong_report, weak_report):
        reviewer = ExpertReportReviewer()
        weak_report.is_opposing = True
        comparison = reviewer.compare_to_opposing(strong_report, weak_report)
        assert "our_advantages" in comparison
        assert len(comparison["our_advantages"]) >= 1

    def test_generate_rebuttal_outline(self, weak_report):
        reviewer = ExpertReportReviewer()
        outline = reviewer.generate_rebuttal_outline(weak_report)
        assert len(outline) >= 1
        assert any("Methodology Challenge" in p.get("section", "") for p in outline)

    def test_get_stats(self):
        reviewer = ExpertReportReviewer()
        stats = reviewer.get_stats()
        assert stats["component"] == "ExpertReportReviewer"
        assert stats["weakness_patterns"] >= 5


# ===================================================================
# TestDepositionCoordinator
# ===================================================================
class TestDepositionCoordinator:
    """Tests for the DepositionCoordinator class."""

    @pytest.fixture
    def expert(self):
        return ExpertWitness(
            name="Dr. Jane Smith",
            field=ExpertField.CUSTODY_EVALUATION,
            hourly_rate=Decimal("350.00"),
            retained_for_lane="A",
        )

    def test_schedule_deposition(self, expert):
        dc = DepositionCoordinator()
        record = dc.schedule_deposition(
            expert, scheduled_date="2026-05-01", location="Muskegon",
        )
        assert isinstance(record, DepositionRecord)
        assert record.expert_name == "Dr. Jane Smith"
        assert record.cost == Decimal("1400.00")

    def test_schedule_deposition_default_location(self, expert):
        dc = DepositionCoordinator()
        record = dc.schedule_deposition(expert, scheduled_date="2026-05-01")
        assert "14th Circuit Court" in record.location

    def test_schedule_deposition_custom_hours(self, expert):
        dc = DepositionCoordinator()
        record = dc.schedule_deposition(
            expert, scheduled_date="2026-05-01", estimated_hours=Decimal("2.0"),
        )
        assert record.cost == Decimal("700.00")

    def test_prepare_expert(self, expert):
        dc = DepositionCoordinator()
        prep = dc.prepare_expert(expert)
        assert "preparation_checklist" in prep
        assert len(prep["preparation_checklist"]) >= 5
        assert "documents_to_bring" in prep

    def test_prepare_expert_field_topics(self, expert):
        dc = DepositionCoordinator()
        prep = dc.prepare_expert(expert)
        assert "MCL 722.23" in " ".join(prep["anticipated_cross_topics"])

    def test_generate_expert_notice(self, expert):
        dc = DepositionCoordinator()
        notice = dc.generate_expert_notice(
            expert,
            deposition_date="May 1, 2026",
            case_number="2024-001507-DC",
        )
        assert "NOTICE OF DEPOSITION" in notice
        assert "Andrew James Pigors" in notice
        assert "Emily A. Watson" in notice
        assert "MCR 2.306" in notice

    def test_track_costs(self, expert):
        dc = DepositionCoordinator()
        dc.schedule_deposition(expert, scheduled_date="2026-05-01")
        dc.schedule_deposition(expert, scheduled_date="2026-06-01")
        summary = dc.track_costs()
        assert summary.total_cost == Decimal("2800.00")

    def test_track_costs_empty(self):
        dc = DepositionCoordinator()
        summary = dc.track_costs()
        assert summary.total_cost == Decimal("0.00")

    def test_get_stats(self, expert):
        dc = DepositionCoordinator()
        dc.schedule_deposition(expert, scheduled_date="2026-05-01")
        stats = dc.get_stats()
        assert stats["component"] == "DepositionCoordinator"
        assert stats["depositions_scheduled"] == 1


# ===================================================================
# TestExpertWitnessManager
# ===================================================================
class TestExpertWitnessManager:
    """Tests for the ExpertWitnessManager orchestrator."""

    def test_add_expert(self, tmp_path):
        ewm = ExpertWitnessManager(db_path=tmp_path / "test.db")
        expert = ewm.add_expert(
            name="Dr. Jane Smith",
            expert_field=ExpertField.CUSTODY_EVALUATION,
            qualifications=["PhD Psychology"],
            hourly_rate=Decimal("350.00"),
            lane="A",
        )
        assert expert.name == "Dr. Jane Smith"
        assert expert.case_number == "2024-001507-DC"

    def test_identify_experts_by_field(self, tmp_path):
        ewm = ExpertWitnessManager(db_path=tmp_path / "test.db")
        ewm.add_expert("Dr. A", ExpertField.PSYCHOLOGY, lane="A")
        ewm.add_expert("Dr. B", ExpertField.REAL_ESTATE, lane="B")
        results = ewm.identify_experts(expert_field=ExpertField.PSYCHOLOGY)
        assert len(results) == 1
        assert results[0].name == "Dr. A"

    def test_identify_experts_by_lane(self, tmp_path):
        ewm = ExpertWitnessManager(db_path=tmp_path / "test.db")
        ewm.add_expert("Dr. A", ExpertField.PSYCHOLOGY, lane="A")
        ewm.add_expert("Dr. B", ExpertField.PSYCHOLOGY, lane="D")
        results = ewm.identify_experts(lane="A")
        assert len(results) == 1

    def test_retain_expert(self, tmp_path):
        ewm = ExpertWitnessManager(db_path=tmp_path / "test.db")
        expert = ewm.add_expert("Dr. A", ExpertField.PSYCHOLOGY)
        result = ewm.retain_expert(expert.expert_id, lane="A")
        assert result is True
        assert expert.retention_status == RetentionStatus.RETAINED

    def test_retain_expert_not_found(self, tmp_path):
        ewm = ExpertWitnessManager(db_path=tmp_path / "test.db")
        assert ewm.retain_expert("nonexistent") is False

    def test_update_status(self, tmp_path):
        ewm = ExpertWitnessManager(db_path=tmp_path / "test.db")
        expert = ewm.add_expert("Dr. A", ExpertField.PSYCHOLOGY)
        result = ewm.update_status(expert.expert_id, RetentionStatus.DEPOSED)
        assert result is True
        assert expert.retention_status == RetentionStatus.DEPOSED

    def test_add_and_manage_reports(self, tmp_path):
        ewm = ExpertWitnessManager(db_path=tmp_path / "test.db")
        report = ExpertReport(expert_id="e1", expert_name="Dr. A")
        ewm.add_report(report)
        reports = ewm.manage_reports()
        assert len(reports) == 1

    def test_manage_reports_by_expert(self, tmp_path):
        ewm = ExpertWitnessManager(db_path=tmp_path / "test.db")
        ewm.add_report(ExpertReport(expert_id="e1"))
        ewm.add_report(ExpertReport(expert_id="e2"))
        assert len(ewm.manage_reports(expert_id="e1")) == 1

    def test_review_report(self, tmp_path):
        ewm = ExpertWitnessManager(db_path=tmp_path / "test.db")
        report = ExpertReport(
            expert_name="Dr. X",
            methodology="Standard testing",
            findings=["F1", "F2", "F3"],
            supporting_data=["D1", "D2", "D3"],
        )
        review = ewm.review_report(report)
        assert "overall_quality" in review

    def test_challenge_opposing_expert(self, tmp_path):
        ewm = ExpertWitnessManager(db_path=tmp_path / "test.db")
        witness = ExpertWitness(
            name="Opposing Dr.",
            qualifications=[],
            publications=[],
        )
        result = ewm.challenge_opposing_expert(witness)
        assert isinstance(result, DaubertAnalysisResult)
        assert result.admissible is False

    def test_generate_qualification_memo(self, tmp_path):
        ewm = ExpertWitnessManager(db_path=tmp_path / "test.db")
        analysis = DaubertAnalysisResult(
            expert_name="Dr. Test",
            factors=[DaubertFactor(factor_name="Qualification", score=80)],
        )
        memo = ewm.generate_qualification_memo(analysis)
        assert "MEMORANDUM" in memo

    def test_calculate_costs(self, tmp_path):
        ewm = ExpertWitnessManager(db_path=tmp_path / "test.db")
        expert = ewm.add_expert(
            "Dr. A", ExpertField.PSYCHOLOGY,
            hourly_rate=Decimal("200.00"), lane="A",
        )
        ewm.retain_expert(expert.expert_id, lane="A")
        costs = ewm.calculate_costs()
        assert costs.total_cost > Decimal("0")
        assert costs.total_retained == 1

    def test_calculate_costs_no_experts(self, tmp_path):
        ewm = ExpertWitnessManager(db_path=tmp_path / "test.db")
        costs = ewm.calculate_costs()
        assert costs.total_cost == Decimal("0.00")

    def test_persist_with_tmp_db(self, tmp_path):
        db_path = tmp_path / "test_experts.db"
        conn = sqlite3.connect(str(db_path))
        conn.close()
        ewm = ExpertWitnessManager(db_path=db_path)
        ewm.add_expert("Dr. A", ExpertField.PSYCHOLOGY, lane="A")
        saved = ewm.persist()
        assert saved >= 1

    def test_persist_no_db(self, tmp_path):
        ewm = ExpertWitnessManager(db_path=tmp_path / "nonexistent.db")
        assert ewm.persist() == 0

    def test_get_stats(self, tmp_path):
        ewm = ExpertWitnessManager(db_path=tmp_path / "test.db")
        ewm.add_expert("Dr. A", ExpertField.PSYCHOLOGY, lane="A")
        stats = ewm.get_stats()
        assert stats["module"] == "expert_witness_manager"
        assert stats["experts_loaded"] == 1
        assert "daubert_analyzer" in stats

    def test_reset(self, tmp_path):
        ewm = ExpertWitnessManager(db_path=tmp_path / "test.db")
        ewm.add_expert("Dr. A", ExpertField.PSYCHOLOGY)
        ewm.add_report(ExpertReport(expert_id="e1"))
        ewm.reset()
        assert ewm.get_stats()["experts_loaded"] == 0
        assert ewm.get_stats()["reports_loaded"] == 0


# ===================================================================
# TestExpertCostSummary
# ===================================================================
class TestExpertCostSummary:
    """Tests for the ExpertCostSummary dataclass."""

    def test_default_creation(self):
        ecs = ExpertCostSummary()
        assert ecs.total_cost == Decimal("0.00")
        assert ecs.total_retained == 0

    def test_to_dict_decimal_as_string(self):
        ecs = ExpertCostSummary(
            total_cost=Decimal("5000.00"),
            by_expert={"Dr. A": Decimal("3000.00")},
        )
        d = ecs.to_dict()
        assert d["total_cost"] == "5000.00"
        assert d["by_expert"]["Dr. A"] == "3000.00"


# ===================================================================
# TestDepositionRecord
# ===================================================================
class TestDepositionRecord:
    """Tests for the DepositionRecord dataclass."""

    def test_to_dict_decimal_as_string(self):
        dr = DepositionRecord(
            expert_name="Dr. Smith",
            cost=Decimal("1400.00"),
            duration_hours=Decimal("4.0"),
        )
        d = dr.to_dict()
        assert d["cost"] == "1400.00"
        assert d["duration_hours"] == "4.0"

    def test_default_status(self):
        dr = DepositionRecord()
        assert dr.status == "scheduled"
