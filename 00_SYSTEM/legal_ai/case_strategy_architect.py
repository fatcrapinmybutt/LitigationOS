# -*- coding: utf-8 -*-
"""
Case Strategy Architect — LitigationOS Legal AI Subsystem
==========================================================
Multi-lane case strategy coordinator for the Pigors v Watson
litigation.  Manages strategic objectives across all six case
lanes (A–F), performs game-theoretic opponent modeling, allocates
resources, and coordinates cross-lane synergies.

Case Context
------------
    Plaintiff:  Andrew James Pigors (Pro Se)
    Defendant:  Emily A. Watson
    Child:      L.D.W. (per MCR 8.119(H)) — Male
    Judge:      Hon. Jenny L. McNeill — 14th Circuit Court
    Cases:      2024-001507-DC, 2025-002760-CZ, 2023-5907-PP, COA 366810
    Lanes:      ALL (A through F)

Michigan Rules
--------------
    MCR 2.111 – General Pleading Rules
    MCR 2.116 – Summary Disposition
    MCR 2.401 – Pretrial Procedures
    MCR 2.403 – Case Evaluation
    MCR 3.206 – Initiating a Family Law Case
    MCR 7.205 – Application for Leave to Appeal
    MCL 722.23 – Best Interests of the Child (Child Custody Act)
    MCL 722.27 – Custody Modification

Usage::

    from legal_ai.case_strategy_architect import CaseStrategyArchitect

    csa = CaseStrategyArchitect()
    plan = csa.create_master_plan(lanes=["A", "D", "E"])
    roadmap = csa.generate_roadmap()

Zero external dependencies.  CPU-first.  Local-only.
"""
from __future__ import annotations

import hashlib
import json
import logging
import sqlite3
import sys
import textwrap
import uuid
from collections import defaultdict
from dataclasses import asdict, dataclass, field
from datetime import date, datetime, timedelta, timezone
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional, Sequence, Set, Tuple

logger = logging.getLogger("legal_ai.case_strategy_architect")

# ---------------------------------------------------------------------------
# Path resolution  (never set CWD to repo root — shadow-module risk)
# ---------------------------------------------------------------------------
_HERE = Path(__file__).resolve().parent
_REPO = _HERE.parents[1]
_DB_PATH = _REPO / "litigation_context.db"

# ---------------------------------------------------------------------------
# Case constants
# ---------------------------------------------------------------------------
_PLAINTIFF = "Andrew James Pigors"
_DEFENDANT = "Emily A. Watson"
_CHILD_INITIALS = "L.D.W."
_JUDGE = "Hon. Jenny L. McNeill"
_COURT = "14th Circuit Court"

LANE_CASES: Dict[str, str] = {
    "A": "2024-001507-DC",
    "B": "2025-002760-CZ",
    "C": "Convergence",
    "D": "2023-5907-PP",
    "E": "JTC / Misconduct",
    "F": "COA 366810",
}

LANE_DESCRIPTIONS: Dict[str, str] = {
    "A": "Custody — Watson v Pigors",
    "B": "Housing — Shady Oaks",
    "C": "Convergence — Cross-lane coordination",
    "D": "PPO — Protection Orders",
    "E": "Judicial Misconduct — JTC / McNeill",
    "F": "Appellate — COA / MSC",
}


# ---------------------------------------------------------------------------
# Enumerations
# ---------------------------------------------------------------------------


class StrategyPhase(str, Enum):
    """Litigation lifecycle phases."""

    DISCOVERY = "discovery"
    MOTION_PRACTICE = "motion_practice"
    PRETRIAL = "pretrial"
    TRIAL = "trial"
    POST_TRIAL = "post_trial"
    APPEAL = "appeal"
    SETTLEMENT = "settlement"

    @property
    def mcr_reference(self) -> str:
        _refs = {
            "discovery": "MCR 2.301–2.314",
            "motion_practice": "MCR 2.116, MCR 2.119",
            "pretrial": "MCR 2.401",
            "trial": "MCR 2.501–2.516",
            "post_trial": "MCR 2.611–2.612",
            "appeal": "MCR 7.201–7.215",
            "settlement": "MCR 2.403",
        }
        return _refs.get(self.value, "MCR 2.001")


class ObjectiveStatus(str, Enum):
    """Status of a strategic objective."""

    PLANNED = "planned"
    IN_PROGRESS = "in_progress"
    BLOCKED = "blocked"
    COMPLETED = "completed"
    DEFERRED = "deferred"
    SUPERSEDED = "superseded"


class RiskLevel(str, Enum):
    """Risk severity categories."""

    LOW = "low"
    MODERATE = "moderate"
    HIGH = "high"
    CRITICAL = "critical"


class ResourceType(str, Enum):
    """Types of litigation resources."""

    TIME_HOURS = "time_hours"
    FILING_FEE = "filing_fee"
    EXPERT_COST = "expert_cost"
    COPY_COST = "copy_cost"
    SERVICE_COST = "service_cost"
    TRAVEL_COST = "travel_cost"
    RESEARCH_HOURS = "research_hours"


# ---------------------------------------------------------------------------
# Dataclasses
# ---------------------------------------------------------------------------


@dataclass
class StrategicObjective:
    """A single strategic objective within a case lane."""

    objective_id: str = field(default_factory=lambda: uuid.uuid4().hex[:12])
    description: str = ""
    priority: int = 5  # 1 (highest) to 10 (lowest)
    lane: str = ""
    status: ObjectiveStatus = ObjectiveStatus.PLANNED
    dependencies: List[str] = field(default_factory=list)
    deadline: str = ""
    resources_needed: Dict[str, float] = field(default_factory=dict)
    rationale: str = ""
    success_criteria: str = ""
    assigned_phase: StrategyPhase = StrategyPhase.DISCOVERY
    created_at: str = field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )

    def to_dict(self) -> Dict[str, Any]:
        return {
            "objective_id": self.objective_id,
            "description": self.description,
            "priority": self.priority,
            "lane": self.lane,
            "status": self.status.value,
            "dependencies": self.dependencies,
            "deadline": self.deadline,
            "resources_needed": self.resources_needed,
            "rationale": self.rationale,
            "success_criteria": self.success_criteria,
            "assigned_phase": self.assigned_phase.value,
            "created_at": self.created_at,
        }


@dataclass
class LaneStrategy:
    """Full SWOT-scored strategy for one case lane."""

    lane: str = ""
    objectives: List[StrategicObjective] = field(default_factory=list)
    current_phase: StrategyPhase = StrategyPhase.DISCOVERY
    strengths: List[str] = field(default_factory=list)
    weaknesses: List[str] = field(default_factory=list)
    opportunities: List[str] = field(default_factory=list)
    threats: List[str] = field(default_factory=list)
    risk_score: int = 50  # 0 (safe) to 100 (critical)
    case_number: str = ""
    notes: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return {
            "lane": self.lane,
            "objectives": [o.to_dict() for o in self.objectives],
            "current_phase": self.current_phase.value,
            "strengths": self.strengths,
            "weaknesses": self.weaknesses,
            "opportunities": self.opportunities,
            "threats": self.threats,
            "risk_score": self.risk_score,
            "case_number": self.case_number,
            "notes": self.notes,
        }


@dataclass
class ResourceAllocation:
    """A single resource allocation entry."""

    allocation_id: str = field(default_factory=lambda: uuid.uuid4().hex[:10])
    lane: str = ""
    resource_type: ResourceType = ResourceType.TIME_HOURS
    amount: float = 0.0
    description: str = ""
    priority: int = 5

    def to_dict(self) -> Dict[str, Any]:
        return {
            "allocation_id": self.allocation_id,
            "lane": self.lane,
            "resource_type": self.resource_type.value,
            "amount": self.amount,
            "description": self.description,
            "priority": self.priority,
        }


@dataclass
class OpponentAction:
    """A modeled opponent action with probability."""

    action_id: str = field(default_factory=lambda: uuid.uuid4().hex[:10])
    description: str = ""
    probability: float = 0.5
    impact: int = 5  # 1-10
    lane: str = ""
    counter_strategy: str = ""
    legal_basis: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return {
            "action_id": self.action_id,
            "description": self.description,
            "probability": self.probability,
            "impact": self.impact,
            "lane": self.lane,
            "counter_strategy": self.counter_strategy,
            "legal_basis": self.legal_basis,
        }


@dataclass
class RiskAssessment:
    """Structured risk assessment for a lane or objective."""

    risk_id: str = field(default_factory=lambda: uuid.uuid4().hex[:10])
    description: str = ""
    level: RiskLevel = RiskLevel.MODERATE
    probability: float = 0.5
    impact: int = 5
    mitigation: str = ""
    lane: str = ""
    owner: str = _PLAINTIFF

    def to_dict(self) -> Dict[str, Any]:
        return {
            "risk_id": self.risk_id,
            "description": self.description,
            "level": self.level.value,
            "probability": self.probability,
            "impact": self.impact,
            "mitigation": self.mitigation,
            "lane": self.lane,
            "owner": self.owner,
        }


@dataclass
class StrategyRoadmap:
    """Top-level roadmap output — the deliverable."""

    roadmap_id: str = field(default_factory=lambda: uuid.uuid4().hex[:12])
    generated_at: str = field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )
    lane_strategies: List[LaneStrategy] = field(default_factory=list)
    cross_lane_synergies: List[Dict[str, Any]] = field(default_factory=list)
    risk_assessments: List[RiskAssessment] = field(default_factory=list)
    resource_allocations: List[ResourceAllocation] = field(default_factory=list)
    timeline: List[Dict[str, str]] = field(default_factory=list)
    overall_risk_score: int = 50

    def to_dict(self) -> Dict[str, Any]:
        return {
            "roadmap_id": self.roadmap_id,
            "generated_at": self.generated_at,
            "lane_strategies": [ls.to_dict() for ls in self.lane_strategies],
            "cross_lane_synergies": self.cross_lane_synergies,
            "risk_assessments": [r.to_dict() for r in self.risk_assessments],
            "resource_allocations": [a.to_dict() for a in self.resource_allocations],
            "timeline": self.timeline,
            "overall_risk_score": self.overall_risk_score,
        }


# ---------------------------------------------------------------------------
# ResourceAllocator
# ---------------------------------------------------------------------------


class ResourceAllocator:
    """Allocates limited litigation resources across lanes and phases."""

    def __init__(self) -> None:
        self._allocations: List[ResourceAllocation] = []
        self._total_budget: Dict[str, float] = {
            ResourceType.TIME_HOURS.value: 200.0,
            ResourceType.FILING_FEE.value: 500.0,
            ResourceType.EXPERT_COST.value: 5000.0,
            ResourceType.COPY_COST.value: 200.0,
            ResourceType.SERVICE_COST.value: 300.0,
            ResourceType.TRAVEL_COST.value: 400.0,
            ResourceType.RESEARCH_HOURS.value: 150.0,
        }

    def allocate_time(
        self, lane: str, hours: float, description: str = "", priority: int = 5,
    ) -> ResourceAllocation:
        """Allocate time hours to a lane."""
        alloc = ResourceAllocation(
            lane=lane,
            resource_type=ResourceType.TIME_HOURS,
            amount=hours,
            description=description or f"Time allocation for Lane {lane}",
            priority=priority,
        )
        self._allocations.append(alloc)
        return alloc

    def allocate_budget(
        self, lane: str, resource_type: ResourceType,
        amount: float, description: str = "", priority: int = 5,
    ) -> ResourceAllocation:
        """Allocate a monetary budget item to a lane."""
        alloc = ResourceAllocation(
            lane=lane,
            resource_type=resource_type,
            amount=amount,
            description=description or f"{resource_type.value} for Lane {lane}",
            priority=priority,
        )
        self._allocations.append(alloc)
        return alloc

    def prioritize_lanes(
        self, lane_strategies: Sequence[LaneStrategy],
    ) -> List[Tuple[str, int]]:
        """Rank lanes by priority score (lower = more urgent).

        Scoring: risk_score * 0.5 + active_objectives * 10 + phase_weight
        """
        phase_weights = {
            StrategyPhase.TRIAL: 0,
            StrategyPhase.PRETRIAL: 10,
            StrategyPhase.MOTION_PRACTICE: 20,
            StrategyPhase.DISCOVERY: 30,
            StrategyPhase.APPEAL: 15,
            StrategyPhase.POST_TRIAL: 25,
            StrategyPhase.SETTLEMENT: 35,
        }
        scored: List[Tuple[str, int]] = []
        for ls in lane_strategies:
            active = sum(
                1 for o in ls.objectives
                if o.status == ObjectiveStatus.IN_PROGRESS
            )
            pw = phase_weights.get(ls.current_phase, 30)
            score = int(ls.risk_score * 0.5 + active * 10 + pw)
            scored.append((ls.lane, score))
        scored.sort(key=lambda x: x[1])
        return scored

    def identify_bottlenecks(
        self, lane_strategies: Sequence[LaneStrategy],
    ) -> List[Dict[str, Any]]:
        """Identify resource bottlenecks across all lanes."""
        bottlenecks: List[Dict[str, Any]] = []
        used: Dict[str, float] = defaultdict(float)
        for alloc in self._allocations:
            used[alloc.resource_type.value] += alloc.amount

        for rtype, total in self._total_budget.items():
            utilization = used.get(rtype, 0.0) / total if total > 0 else 0
            if utilization > 0.80:
                bottlenecks.append({
                    "resource": rtype,
                    "used": round(used.get(rtype, 0.0), 2),
                    "total": total,
                    "utilization_pct": round(utilization * 100, 1),
                    "severity": "critical" if utilization > 0.95 else "warning",
                })

        # Check for blocked objectives across lanes
        for ls in lane_strategies:
            blocked = [
                o for o in ls.objectives
                if o.status == ObjectiveStatus.BLOCKED
            ]
            if blocked:
                bottlenecks.append({
                    "resource": "objectives",
                    "lane": ls.lane,
                    "blocked_count": len(blocked),
                    "blocked_ids": [o.objective_id for o in blocked],
                    "severity": "high",
                })

        return bottlenecks

    def get_utilization_report(self) -> Dict[str, Any]:
        """Report current resource utilization."""
        used: Dict[str, float] = defaultdict(float)
        by_lane: Dict[str, Dict[str, float]] = defaultdict(lambda: defaultdict(float))
        for alloc in self._allocations:
            used[alloc.resource_type.value] += alloc.amount
            by_lane[alloc.lane][alloc.resource_type.value] += alloc.amount

        report: Dict[str, Any] = {"by_resource": {}, "by_lane": {}}
        for rtype, total in self._total_budget.items():
            report["by_resource"][rtype] = {
                "used": round(used.get(rtype, 0.0), 2),
                "total": total,
                "remaining": round(total - used.get(rtype, 0.0), 2),
            }
        for lane, resources in by_lane.items():
            report["by_lane"][lane] = dict(resources)
        return report

    def get_stats(self) -> Dict[str, Any]:
        return {
            "component": "ResourceAllocator",
            "total_allocations": len(self._allocations),
            "budget_categories": len(self._total_budget),
        }


# ---------------------------------------------------------------------------
# GameTheoryEngine
# ---------------------------------------------------------------------------


class GameTheoryEngine:
    """Game-theoretic opponent modeling for litigation strategy.

    Models opposing counsel actions as a two-player sequential game.
    Uses minimax scoring for risk assessment — NOT statistical
    prediction.  All analysis is deterministic and rules-based.
    """

    # Common opposing actions by lane
    _OPPONENT_PLAYBOOK: Dict[str, List[Dict[str, Any]]] = {
        "A": [
            {"action": "File motion for sole custody", "prob": 0.7, "impact": 9,
             "counter": "Rebut with best-interest evidence (MCL 722.23 factors)"},
            {"action": "Allege parental unfitness", "prob": 0.5, "impact": 8,
             "counter": "Present evidence of active parenting, school involvement"},
            {"action": "Request supervised visitation", "prob": 0.4, "impact": 7,
             "counter": "Demonstrate safe home environment, character witnesses"},
            {"action": "File for change of domicile", "prob": 0.3, "impact": 8,
             "counter": "Oppose under MCL 722.31 established custodial environment"},
            {"action": "Delay discovery responses", "prob": 0.6, "impact": 5,
             "counter": "File motion to compel under MCR 2.313"},
        ],
        "B": [
            {"action": "File motion to dismiss housing claim", "prob": 0.6, "impact": 7,
             "counter": "Demonstrate standing and damages per MCL 600.3801"},
            {"action": "Assert statute of limitations", "prob": 0.4, "impact": 8,
             "counter": "Argue discovery rule, continuing violation"},
            {"action": "Move for summary disposition", "prob": 0.5, "impact": 9,
             "counter": "Present genuine issues of material fact per MCR 2.116(C)(10)"},
        ],
        "D": [
            {"action": "Seek PPO extension", "prob": 0.5, "impact": 7,
             "counter": "Challenge factual basis under MCL 600.2950"},
            {"action": "Allege PPO violation", "prob": 0.4, "impact": 9,
             "counter": "Document compliance, present alibi evidence"},
            {"action": "File counter-PPO", "prob": 0.3, "impact": 6,
             "counter": "Demonstrate no reasonable apprehension of harm"},
        ],
        "E": [
            {"action": "Judicial denial of misconduct complaints", "prob": 0.7, "impact": 6,
             "counter": "Escalate to JTC with documented pattern evidence"},
            {"action": "Sanction plaintiff for misconduct claims", "prob": 0.3, "impact": 8,
             "counter": "Document good-faith basis per MCR 1.109(E)"},
        ],
        "F": [
            {"action": "Move to dismiss appeal as untimely", "prob": 0.3, "impact": 9,
             "counter": "Demonstrate timely filing per MCR 7.204(A)"},
            {"action": "Argue harmless error", "prob": 0.6, "impact": 7,
             "counter": "Show prejudice and outcome-determinative nature of error"},
            {"action": "Request oral argument denial", "prob": 0.4, "impact": 5,
             "counter": "Demonstrate case complexity warrants argument"},
        ],
    }

    def __init__(self) -> None:
        self._modeled_actions: List[OpponentAction] = []

    def analyze_opponent_options(
        self, lane: str,
    ) -> List[OpponentAction]:
        """Enumerate likely opponent actions for a given lane."""
        playbook = self._OPPONENT_PLAYBOOK.get(lane, [])
        actions: List[OpponentAction] = []
        for entry in playbook:
            action = OpponentAction(
                description=entry["action"],
                probability=entry["prob"],
                impact=entry["impact"],
                lane=lane,
                counter_strategy=entry["counter"],
            )
            actions.append(action)
        self._modeled_actions.extend(actions)
        return actions

    def calculate_nash_equilibrium(
        self, lane: str,
    ) -> Dict[str, Any]:
        """Approximate Nash equilibrium via minimax for a lane.

        Returns the strategy pair where neither side benefits from
        unilateral deviation.  In litigation this identifies the
        most stable outcome path.
        """
        actions = [a for a in self._modeled_actions if a.lane == lane]
        if not actions:
            actions = self.analyze_opponent_options(lane)

        if not actions:
            return {"lane": lane, "equilibrium": "insufficient_data"}

        # Opponent's best response: highest expected value (prob * impact)
        opp_best = max(actions, key=lambda a: a.probability * a.impact)

        # Our best counter to their best play
        our_response = opp_best.counter_strategy

        # Expected utility for each side (simplified two-player model)
        opp_utility = round(opp_best.probability * opp_best.impact, 2)
        # Our utility inversely correlates when we have a strong counter
        our_utility = round(10.0 - opp_utility, 2)

        return {
            "lane": lane,
            "opponent_best_action": opp_best.description,
            "opponent_expected_utility": opp_utility,
            "our_best_response": our_response,
            "our_expected_utility": our_utility,
            "equilibrium_type": "minimax_approximation",
            "stability": "stable" if abs(our_utility - opp_utility) < 3 else "unstable",
        }

    def minimax_strategy(
        self, lane: str,
    ) -> Dict[str, Any]:
        """Compute minimax strategy — minimize opponent's maximum gain."""
        actions = [a for a in self._modeled_actions if a.lane == lane]
        if not actions:
            actions = self.analyze_opponent_options(lane)

        if not actions:
            return {"lane": lane, "strategy": "no_data_available"}

        # For each opponent action, compute expected damage
        scored: List[Tuple[OpponentAction, float]] = []
        for a in actions:
            expected_damage = a.probability * a.impact
            scored.append((a, expected_damage))

        scored.sort(key=lambda x: x[1], reverse=True)

        # Minimax: prepare counters for the highest-damage actions first
        counter_plan: List[Dict[str, Any]] = []
        for action, damage in scored[:5]:
            counter_plan.append({
                "threat": action.description,
                "expected_damage": round(damage, 2),
                "counter": action.counter_strategy,
                "preparation_priority": "high" if damage > 5 else "medium",
            })

        worst_case = scored[0][1] if scored else 0
        return {
            "lane": lane,
            "worst_case_damage": round(worst_case, 2),
            "counter_plan": counter_plan,
            "total_threats_modeled": len(actions),
        }

    def predict_responses(
        self, our_action: str, lane: str,
    ) -> List[Dict[str, Any]]:
        """Predict likely opponent responses to a planned action."""
        actions = [a for a in self._modeled_actions if a.lane == lane]
        if not actions:
            actions = self.analyze_opponent_options(lane)

        predictions: List[Dict[str, Any]] = []
        for a in actions:
            # Heuristic: actions with higher probability are more likely responses
            relevance = a.probability * 0.7 + (a.impact / 10.0) * 0.3
            predictions.append({
                "opponent_response": a.description,
                "relevance_score": round(relevance, 2),
                "our_counter": a.counter_strategy,
                "impact_if_uncountered": a.impact,
            })

        predictions.sort(key=lambda p: p["relevance_score"], reverse=True)
        return predictions

    def get_stats(self) -> Dict[str, Any]:
        return {
            "component": "GameTheoryEngine",
            "modeled_actions": len(self._modeled_actions),
            "playbook_lanes": len(self._OPPONENT_PLAYBOOK),
        }


# ---------------------------------------------------------------------------
# CrossLaneCoordinator
# ---------------------------------------------------------------------------


class CrossLaneCoordinator:
    """Coordinates strategy across all six case lanes.

    Detects synergies (shared evidence, overlapping deadlines),
    conflicts (contradictory positions), and generates a unified
    timeline across lanes.
    """

    # Known cross-lane synergies (evidence in one lane supports another)
    _SYNERGY_MAP: List[Dict[str, Any]] = [
        {
            "lanes": ["A", "D"],
            "description": "Custody evidence supports PPO defense — "
                           "parenting fitness rebuts protection-order claims",
            "evidence_types": ["parenting records", "school communications",
                               "child welfare reports"],
        },
        {
            "lanes": ["A", "E"],
            "description": "Judicial misconduct evidence in custody case "
                           "supports JTC complaint and appellate claims",
            "evidence_types": ["hearing transcripts", "order inconsistencies",
                               "ex parte communication records"],
        },
        {
            "lanes": ["D", "E"],
            "description": "PPO procedural errors demonstrate judicial "
                           "misconduct pattern for JTC proceedings",
            "evidence_types": ["PPO hearing transcripts", "due process violations"],
        },
        {
            "lanes": ["A", "F"],
            "description": "Trial court errors in custody case form the "
                           "basis for appellate arguments",
            "evidence_types": ["trial court orders", "objection records",
                               "issue preservation documents"],
        },
        {
            "lanes": ["E", "F"],
            "description": "JTC misconduct findings strengthen appellate "
                           "claims of structural error",
            "evidence_types": ["JTC complaint filings", "misconduct patterns"],
        },
        {
            "lanes": ["A", "B"],
            "description": "Housing instability evidence relevant to custody "
                           "best-interest factor (MCL 722.23(d) — home environment)",
            "evidence_types": ["housing inspection reports", "lease documents",
                               "maintenance records"],
        },
    ]

    # Known conflicts (positions that could undermine each other)
    _CONFLICT_MAP: List[Dict[str, Any]] = [
        {
            "lanes": ["A", "D"],
            "description": "Aggressive PPO defense tactics may conflict "
                           "with cooperative co-parenting narrative in custody",
            "resolution": "Frame PPO defense as protecting parental rights "
                          "rather than adversarial stance toward co-parent",
        },
        {
            "lanes": ["E", "A"],
            "description": "Judicial misconduct claims may antagonize the "
                           "presiding judge in ongoing custody proceedings",
            "resolution": "File JTC complaints separately from active custody "
                          "motions; recusal motion (MCR 2.003) should precede "
                          "any misconduct allegations in the custody case",
        },
    ]

    def find_synergies(
        self, active_lanes: Sequence[str],
    ) -> List[Dict[str, Any]]:
        """Identify cross-lane synergies for active lanes."""
        active_set = set(active_lanes)
        results: List[Dict[str, Any]] = []
        for syn in self._SYNERGY_MAP:
            if set(syn["lanes"]).issubset(active_set):
                results.append({
                    "lanes": syn["lanes"],
                    "description": syn["description"],
                    "evidence_types": syn["evidence_types"],
                    "actionable": True,
                })
        return results

    def detect_conflicts(
        self, active_lanes: Sequence[str],
    ) -> List[Dict[str, Any]]:
        """Detect strategic conflicts between active lanes."""
        active_set = set(active_lanes)
        results: List[Dict[str, Any]] = []
        for conf in self._CONFLICT_MAP:
            if set(conf["lanes"]).issubset(active_set):
                results.append({
                    "lanes": conf["lanes"],
                    "conflict": conf["description"],
                    "resolution": conf["resolution"],
                    "severity": "high",
                })
        return results

    def coordinate_deadlines(
        self, lane_strategies: Sequence[LaneStrategy],
    ) -> List[Dict[str, Any]]:
        """Aggregate and order deadlines from all lanes."""
        all_deadlines: List[Dict[str, Any]] = []
        for ls in lane_strategies:
            for obj in ls.objectives:
                if obj.deadline:
                    all_deadlines.append({
                        "lane": ls.lane,
                        "case_number": ls.case_number,
                        "objective": obj.description,
                        "deadline": obj.deadline,
                        "priority": obj.priority,
                        "status": obj.status.value,
                    })
        all_deadlines.sort(key=lambda d: d["deadline"])
        return all_deadlines

    def generate_unified_timeline(
        self, lane_strategies: Sequence[LaneStrategy],
    ) -> List[Dict[str, str]]:
        """Generate a unified timeline across all lanes.

        Produces a chronological list of milestones combining all
        lane deadlines and phase transitions.
        """
        events: List[Dict[str, str]] = []
        today = date.today().isoformat()

        for ls in lane_strategies:
            # Phase milestone
            events.append({
                "date": today,
                "lane": ls.lane,
                "event": f"Current phase: {ls.current_phase.value}",
                "type": "phase_marker",
            })
            for obj in ls.objectives:
                if obj.deadline:
                    events.append({
                        "date": obj.deadline,
                        "lane": ls.lane,
                        "event": obj.description,
                        "type": "deadline",
                    })

        events.sort(key=lambda e: e["date"])
        return events

    def assess_lane_dependencies(
        self, lane_strategies: Sequence[LaneStrategy],
    ) -> Dict[str, List[str]]:
        """Map dependencies between lanes.

        Returns a dict where keys are lanes and values are lanes
        they depend on (e.g., F depends on A for issue preservation).
        """
        deps: Dict[str, List[str]] = defaultdict(list)
        # Hardcoded structural dependencies
        dep_rules = [
            ("F", "A", "Appellate requires preserved issues from custody trial"),
            ("F", "E", "Appellate strengthened by documented misconduct"),
            ("C", "A", "Convergence requires active custody posture"),
            ("C", "D", "Convergence requires PPO status resolution"),
            ("E", "A", "JTC requires custody hearing transcript evidence"),
        ]
        active = {ls.lane for ls in lane_strategies}
        for target, source, _reason in dep_rules:
            if target in active and source in active:
                deps[target].append(source)
        return dict(deps)

    def get_stats(self) -> Dict[str, Any]:
        return {
            "component": "CrossLaneCoordinator",
            "synergy_patterns": len(self._SYNERGY_MAP),
            "conflict_patterns": len(self._CONFLICT_MAP),
        }


# ---------------------------------------------------------------------------
# SWOT analysis helpers
# ---------------------------------------------------------------------------

# Pre-built SWOT data for each lane (from case analysis)
_LANE_SWOT: Dict[str, Dict[str, List[str]]] = {
    "A": {
        "strengths": [
            "Documented history of active parenting",
            "School and medical records showing involvement",
            "Evidence of stable home environment",
            "Child's expressed preference (MCL 722.23(i))",
        ],
        "weaknesses": [
            "Pro se status limits procedural advantages",
            "Opposing counsel resource asymmetry",
            "Potential bias in current judicial assignment",
        ],
        "opportunities": [
            "MCL 722.23 best-interest factors favor plaintiff",
            "Opposing party discovery non-compliance creates MTC leverage",
            "Guardian ad litem appointment may support plaintiff position",
        ],
        "threats": [
            "Judicial bias risk from presiding judge",
            "Potential false allegations to influence custody",
            "Procedural default risk as pro se litigant",
        ],
    },
    "B": {
        "strengths": [
            "Documented housing code violations",
            "Photographic and inspection evidence",
            "Multiple witness statements available",
        ],
        "weaknesses": [
            "Statute of limitations may limit some claims",
            "Damages quantification complexity",
        ],
        "opportunities": [
            "Pattern of violations supports punitive damages argument",
            "Local housing authority records available for subpoena",
        ],
        "threats": [
            "Motion to dismiss risk on standing grounds",
            "Summary disposition on evidence sufficiency",
        ],
    },
    "D": {
        "strengths": [
            "Evidence contradicts PPO factual basis",
            "Documented compliance with all existing orders",
            "No prior history of violence or threats",
        ],
        "weaknesses": [
            "PPO hearing procedures limit evidentiary presentation",
            "Burden shifting under MCL 600.2950",
        ],
        "opportunities": [
            "PPO modification or termination hearing available",
            "Due process violations in PPO issuance support appeal",
        ],
        "threats": [
            "PPO violation allegations (even if baseless)",
            "Extension requests creating indefinite restriction",
        ],
    },
    "E": {
        "strengths": [
            "Documented pattern of procedural irregularities",
            "Transcript evidence of bias indicators",
            "Multiple incidents creating pattern evidence",
        ],
        "weaknesses": [
            "JTC complaint process is lengthy and opaque",
            "Judicial immunity limits direct remedies",
        ],
        "opportunities": [
            "JTC findings strengthen all other lane positions",
            "Public accountability creates settlement leverage",
        ],
        "threats": [
            "Retaliation risk in ongoing proceedings",
            "Complaint may be screened out without investigation",
        ],
    },
    "F": {
        "strengths": [
            "Clear error preservation in trial record",
            "Multiple preserved legal issues for review",
            "Strong factual record supporting reversal",
        ],
        "weaknesses": [
            "Appellate standards of review favor trial court",
            "Limited record on appeal — no new evidence",
            "Pro se appellate briefing challenges",
        ],
        "opportunities": [
            "Reversal would reset multiple downstream issues",
            "Published opinion could establish favorable precedent",
        ],
        "threats": [
            "Harmless error doctrine may defeat meritorious claims",
            "Mootness if trial court issues supersede on remand",
        ],
    },
}


# ---------------------------------------------------------------------------
# Database layer
# ---------------------------------------------------------------------------

_PRAGMAS = textwrap.dedent("""\
    PRAGMA busy_timeout = 60000;
    PRAGMA journal_mode = WAL;
    PRAGMA cache_size = -32000;
    PRAGMA temp_store = MEMORY;
    PRAGMA synchronous = NORMAL;
""")

_CREATE_OBJECTIVES_SQL = textwrap.dedent("""\
    CREATE TABLE IF NOT EXISTS strategy_objectives (
        objective_id    TEXT PRIMARY KEY,
        description     TEXT NOT NULL,
        priority        INTEGER DEFAULT 5,
        lane            TEXT,
        status          TEXT DEFAULT 'planned',
        dependencies    TEXT,
        deadline        TEXT,
        resources_json  TEXT,
        rationale       TEXT,
        success_criteria TEXT,
        assigned_phase  TEXT DEFAULT 'discovery',
        created_at      TEXT DEFAULT (datetime('now')),
        updated_at      TEXT DEFAULT (datetime('now'))
    )
""")

_CREATE_LANE_STRATEGIES_SQL = textwrap.dedent("""\
    CREATE TABLE IF NOT EXISTS lane_strategies (
        lane            TEXT PRIMARY KEY,
        case_number     TEXT,
        current_phase   TEXT DEFAULT 'discovery',
        strengths_json  TEXT,
        weaknesses_json TEXT,
        opportunities_json TEXT,
        threats_json    TEXT,
        risk_score      INTEGER DEFAULT 50,
        notes           TEXT,
        updated_at      TEXT DEFAULT (datetime('now'))
    )
""")

_CREATE_INDEXES_SQL = [
    "CREATE INDEX IF NOT EXISTS idx_strat_obj_lane "
    "ON strategy_objectives(lane, status)",
    "CREATE INDEX IF NOT EXISTS idx_strat_obj_deadline "
    "ON strategy_objectives(deadline, priority)",
]


def _ensure_tables(conn: sqlite3.Connection) -> None:
    conn.execute(_CREATE_OBJECTIVES_SQL)
    conn.execute(_CREATE_LANE_STRATEGIES_SQL)
    for idx in _CREATE_INDEXES_SQL:
        conn.execute(idx)
    conn.commit()


# ---------------------------------------------------------------------------
# CaseStrategyArchitect — orchestrator
# ---------------------------------------------------------------------------


class CaseStrategyArchitect:
    """Top-level orchestrator for multi-lane case strategy.

    Combines :class:`ResourceAllocator`, :class:`GameTheoryEngine`,
    and :class:`CrossLaneCoordinator` into a unified strategic
    planning system for the Pigors v Watson litigation.
    """

    def __init__(self, db_path: Optional[Path] = None) -> None:
        self._db_path = db_path or _DB_PATH
        self._allocator = ResourceAllocator()
        self._game_engine = GameTheoryEngine()
        self._coordinator = CrossLaneCoordinator()
        self._lane_strategies: Dict[str, LaneStrategy] = {}
        self._objectives: List[StrategicObjective] = []
        self._risks: List[RiskAssessment] = []

    # -- lane strategy management --

    def _build_lane_strategy(self, lane: str) -> LaneStrategy:
        """Build a LaneStrategy with SWOT data for a lane."""
        swot = _LANE_SWOT.get(lane, {})
        case_number = LANE_CASES.get(lane, "")
        ls = LaneStrategy(
            lane=lane,
            case_number=case_number,
            strengths=swot.get("strengths", []),
            weaknesses=swot.get("weaknesses", []),
            opportunities=swot.get("opportunities", []),
            threats=swot.get("threats", []),
        )
        # Risk score from SWOT balance
        s_count = len(ls.strengths)
        w_count = len(ls.weaknesses)
        t_count = len(ls.threats)
        o_count = len(ls.opportunities)
        # Higher risk when weaknesses+threats outweigh strengths+opportunities
        total = max(s_count + w_count + t_count + o_count, 1)
        negative = w_count + t_count
        ls.risk_score = min(100, max(0, int((negative / total) * 100)))
        return ls

    def create_master_plan(
        self, lanes: Optional[List[str]] = None,
    ) -> Dict[str, LaneStrategy]:
        """Create a master strategic plan for specified lanes.

        Parameters
        ----------
        lanes : list of lane letters, or None for all lanes

        Returns
        -------
        dict mapping lane letter to :class:`LaneStrategy`
        """
        target_lanes = lanes or list(LANE_CASES.keys())
        for lane in target_lanes:
            if lane not in LANE_CASES:
                logger.warning("Unknown lane: %s — skipping", lane)
                continue
            ls = self._build_lane_strategy(lane)
            self._lane_strategies[lane] = ls
            logger.info("Built strategy for Lane %s (%s)", lane, LANE_CASES[lane])

        return dict(self._lane_strategies)

    def add_objective(
        self,
        lane: str,
        description: str,
        priority: int = 5,
        deadline: str = "",
        phase: StrategyPhase = StrategyPhase.DISCOVERY,
        dependencies: Optional[List[str]] = None,
        resources: Optional[Dict[str, float]] = None,
    ) -> StrategicObjective:
        """Add a strategic objective to a lane."""
        obj = StrategicObjective(
            description=description,
            priority=max(1, min(10, priority)),
            lane=lane,
            deadline=deadline,
            assigned_phase=phase,
            dependencies=dependencies or [],
            resources_needed=resources or {},
        )
        self._objectives.append(obj)

        if lane in self._lane_strategies:
            self._lane_strategies[lane].objectives.append(obj)

        return obj

    def update_objective_status(
        self, objective_id: str, status: ObjectiveStatus,
    ) -> bool:
        """Update the status of a strategic objective."""
        for obj in self._objectives:
            if obj.objective_id == objective_id:
                obj.status = status
                return True
        return False

    # -- strategy optimization --

    def optimize_strategy(self) -> Dict[str, Any]:
        """Optimize strategy across all lanes.

        Returns
        -------
        dict with optimization recommendations including lane
        priorities, synergies, conflicts, and resource rebalancing.
        """
        strategies = list(self._lane_strategies.values())
        if not strategies:
            return {"error": "No lane strategies loaded — call create_master_plan() first"}

        lane_priorities = self._allocator.prioritize_lanes(strategies)
        synergies = self._coordinator.find_synergies(
            [ls.lane for ls in strategies]
        )
        conflicts = self._coordinator.detect_conflicts(
            [ls.lane for ls in strategies]
        )
        bottlenecks = self._allocator.identify_bottlenecks(strategies)
        dependencies = self._coordinator.assess_lane_dependencies(strategies)

        # Generate optimization recommendations
        recommendations: List[str] = []

        if lane_priorities:
            top_lane = lane_priorities[0][0]
            recommendations.append(
                f"Prioritize Lane {top_lane} ({LANE_DESCRIPTIONS.get(top_lane, '')}) — "
                f"highest urgency score"
            )

        for syn in synergies[:3]:
            recommendations.append(
                f"Leverage synergy between Lanes {'/'.join(syn['lanes'])}: "
                f"{syn['description'][:80]}"
            )

        for conf in conflicts:
            recommendations.append(
                f"CONFLICT: Lanes {'/'.join(conf['lanes'])} — "
                f"resolution: {conf['resolution'][:80]}"
            )

        return {
            "lane_priorities": lane_priorities,
            "synergies_found": len(synergies),
            "conflicts_found": len(conflicts),
            "bottlenecks": bottlenecks,
            "dependencies": dependencies,
            "recommendations": recommendations,
        }

    # -- roadmap generation --

    def generate_roadmap(self) -> StrategyRoadmap:
        """Generate a comprehensive strategy roadmap."""
        strategies = list(self._lane_strategies.values())
        roadmap = StrategyRoadmap(
            lane_strategies=strategies,
            cross_lane_synergies=self._coordinator.find_synergies(
                [ls.lane for ls in strategies]
            ),
            risk_assessments=self._risks,
            timeline=self._coordinator.generate_unified_timeline(strategies),
        )

        # Calculate overall risk score (weighted average by lane priority)
        if strategies:
            total_risk = sum(ls.risk_score for ls in strategies)
            roadmap.overall_risk_score = total_risk // len(strategies)

        roadmap.resource_allocations = self._allocator._allocations[:]
        return roadmap

    # -- risk assessment --

    def assess_risks(
        self, lane: Optional[str] = None,
    ) -> List[RiskAssessment]:
        """Assess risks for a specific lane or all lanes."""
        target_strategies = (
            [self._lane_strategies[lane]]
            if lane and lane in self._lane_strategies
            else list(self._lane_strategies.values())
        )

        assessments: List[RiskAssessment] = []

        for ls in target_strategies:
            # Risk from threats
            for threat in ls.threats:
                assessment = RiskAssessment(
                    description=threat,
                    lane=ls.lane,
                    level=RiskLevel.HIGH if ls.risk_score > 60 else RiskLevel.MODERATE,
                    probability=0.5,
                    impact=7,
                    mitigation="See lane-specific counter-strategies",
                )
                assessments.append(assessment)

            # Risk from game theory
            minimax = self._game_engine.minimax_strategy(ls.lane)
            if minimax.get("counter_plan"):
                for cp in minimax["counter_plan"][:2]:
                    level = (
                        RiskLevel.CRITICAL if cp["expected_damage"] > 6
                        else RiskLevel.HIGH if cp["expected_damage"] > 4
                        else RiskLevel.MODERATE
                    )
                    assessment = RiskAssessment(
                        description=f"Opponent: {cp['threat']}",
                        lane=ls.lane,
                        level=level,
                        probability=cp["expected_damage"] / 10.0,
                        impact=int(cp["expected_damage"]),
                        mitigation=cp["counter"],
                    )
                    assessments.append(assessment)

        self._risks = assessments
        return assessments

    # -- game theory delegation --

    def analyze_opponent(self, lane: str) -> Dict[str, Any]:
        """Run full opponent analysis for a lane."""
        options = self._game_engine.analyze_opponent_options(lane)
        nash = self._game_engine.calculate_nash_equilibrium(lane)
        minimax = self._game_engine.minimax_strategy(lane)
        return {
            "lane": lane,
            "opponent_options": [o.to_dict() for o in options],
            "nash_equilibrium": nash,
            "minimax_strategy": minimax,
        }

    # -- persistence --

    def persist(self) -> int:
        """Write strategies and objectives to the database."""
        if not self._db_path.exists():
            logger.warning("Database not found — cannot persist")
            return 0

        try:
            conn = sqlite3.connect(str(self._db_path), timeout=60)
            conn.executescript(_PRAGMAS)
        except sqlite3.Error as exc:
            logger.error("DB connection failed: %s", exc)
            return 0

        try:
            _ensure_tables(conn)
            saved = 0

            # Persist objectives
            obj_rows: List[Tuple[Any, ...]] = []
            for obj in self._objectives:
                obj_rows.append((
                    obj.objective_id,
                    obj.description,
                    obj.priority,
                    obj.lane,
                    obj.status.value,
                    json.dumps(obj.dependencies),
                    obj.deadline,
                    json.dumps(obj.resources_needed),
                    obj.rationale,
                    obj.success_criteria,
                    obj.assigned_phase.value,
                ))
            if obj_rows:
                conn.executemany(
                    "INSERT OR REPLACE INTO strategy_objectives "
                    "(objective_id, description, priority, lane, status, "
                    "dependencies, deadline, resources_json, rationale, "
                    "success_criteria, assigned_phase) "
                    "VALUES (?,?,?,?,?,?,?,?,?,?,?)",
                    obj_rows,
                )
                saved += len(obj_rows)

            # Persist lane strategies
            ls_rows: List[Tuple[Any, ...]] = []
            for ls in self._lane_strategies.values():
                ls_rows.append((
                    ls.lane,
                    ls.case_number,
                    ls.current_phase.value,
                    json.dumps(ls.strengths),
                    json.dumps(ls.weaknesses),
                    json.dumps(ls.opportunities),
                    json.dumps(ls.threats),
                    ls.risk_score,
                    ls.notes,
                ))
            if ls_rows:
                conn.executemany(
                    "INSERT OR REPLACE INTO lane_strategies "
                    "(lane, case_number, current_phase, strengths_json, "
                    "weaknesses_json, opportunities_json, threats_json, "
                    "risk_score, notes) "
                    "VALUES (?,?,?,?,?,?,?,?,?)",
                    ls_rows,
                )
                saved += len(ls_rows)

            conn.commit()
            return saved
        except sqlite3.Error as exc:
            logger.error("Persist failed: %s", exc)
            return 0
        finally:
            conn.close()

    # -- rendering --

    def to_markdown(self) -> str:
        """Render the current strategy as Markdown."""
        lines = [
            "# Case Strategy Roadmap — Pigors v Watson",
            f"Generated: {datetime.now(timezone.utc).isoformat()[:10]}",
            "",
        ]
        for lane, ls in sorted(self._lane_strategies.items()):
            lines.append(f"## Lane {lane}: {LANE_DESCRIPTIONS.get(lane, '')}")
            lines.append(f"Case: {ls.case_number} | Phase: {ls.current_phase.value} "
                         f"| Risk: {ls.risk_score}/100")
            lines.append("")

            if ls.strengths:
                lines.append("### Strengths")
                for s in ls.strengths:
                    lines.append(f"- {s}")
                lines.append("")

            if ls.weaknesses:
                lines.append("### Weaknesses")
                for w in ls.weaknesses:
                    lines.append(f"- {w}")
                lines.append("")

            if ls.objectives:
                lines.append("### Objectives")
                for obj in ls.objectives:
                    lines.append(
                        f"- [{obj.status.value}] P{obj.priority}: {obj.description}"
                    )
                lines.append("")

        return "\n".join(lines)

    # -- stats --

    def get_stats(self) -> Dict[str, Any]:
        """Return runtime statistics."""
        return {
            "module": "case_strategy_architect",
            "lanes_loaded": len(self._lane_strategies),
            "total_objectives": len(self._objectives),
            "total_risks": len(self._risks),
            "db_path": str(self._db_path),
            "allocator": self._allocator.get_stats(),
            "game_engine": self._game_engine.get_stats(),
            "coordinator": self._coordinator.get_stats(),
        }

    def reset(self) -> None:
        """Clear all loaded strategies."""
        self._lane_strategies.clear()
        self._objectives.clear()
        self._risks.clear()


# ---------------------------------------------------------------------------
# CLI demo
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    sys.stdout = open(  # noqa: SIM115
        sys.stdout.fileno(), mode="w", encoding="utf-8", errors="replace"
    )
    logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")

    print("=" * 60)
    print("  Case Strategy Architect — LitigationOS")
    print("=" * 60)
    print()

    csa = CaseStrategyArchitect()
    plan = csa.create_master_plan(lanes=["A", "D", "E", "F"])

    csa.add_objective(
        lane="A",
        description="Complete discovery responses — interrogatories set 1",
        priority=2,
        phase=StrategyPhase.DISCOVERY,
        deadline="2026-04-15",
    )
    csa.add_objective(
        lane="E",
        description="File JTC complaint with pattern evidence",
        priority=1,
        phase=StrategyPhase.MOTION_PRACTICE,
        deadline="2026-03-30",
    )
    csa.add_objective(
        lane="F",
        description="File appellate brief — COA 366810",
        priority=1,
        phase=StrategyPhase.APPEAL,
        deadline="2026-04-01",
    )

    optimization = csa.optimize_strategy()
    print("Optimization Results:")
    print(f"  Lane priorities: {optimization['lane_priorities']}")
    print(f"  Synergies: {optimization['synergies_found']}")
    print(f"  Conflicts: {optimization['conflicts_found']}")
    print(f"  Recommendations: {len(optimization['recommendations'])}")
    for rec in optimization["recommendations"]:
        print(f"    → {rec}")
    print()

    risks = csa.assess_risks()
    print(f"Risk Assessments: {len(risks)}")
    for risk in risks[:5]:
        print(f"  [{risk.level.value}] Lane {risk.lane}: {risk.description[:60]}")
    print()

    roadmap = csa.generate_roadmap()
    print(f"Roadmap: {len(roadmap.lane_strategies)} lanes, "
          f"risk score {roadmap.overall_risk_score}/100")
    print()

    stats = csa.get_stats()
    print(f"Stats: {json.dumps(stats, indent=2)}")
