# -*- coding: utf-8 -*-
"""
Suggestion Engine — LitigationOS Legal AI Subsystem
=====================================================
Analyzes current litigation state across all six case lanes and suggests
prioritized next actions.  Each suggestion is scored on urgency (time
pressure) and impact (strategic value), then ranked by a weighted
combination so the most valuable, most time-sensitive items surface first.

Suggestion Categories:
    evidence   — Missing or weak evidence for pending filings
    filing     — Unfiled motions, incomplete filings, service gaps
    deadline   — Approaching or overdue deadlines
    strategy   — Filing sequences, pressure points, cross-lane synergy
    defense    — Anticipated opposing responses that need preparation
    discovery  — Interrogatories, document requests, subpoenas

Case Context:
    Plaintiff:  Andrew James Pigors (Pro Se)
    Defendant:  Emily A. Watson
    Child:      L.D.W. (per MCR 8.119(H)) — Male
    Judge:      Hon. Jenny L. McNeill — 14th Circuit Court
    Lanes:      A=Custody, B=Housing, C=Convergence, D=PPO,
                E=Misconduct, F=Appellate (COA 366810)

Usage:
    from legal_ai.suggestion_engine import SuggestionEngine

    engine = SuggestionEngine()
    report = engine.analyze()
    for s in report.suggestions[:5]:
        print(f"[{s.priority}] {s.title}  score={s.combined_score:.1f}")

    # Single lane focus
    lane_report = engine.analyze_lane("A")

Zero external dependencies.  CPU-first.  Local-only.
"""
from __future__ import annotations

import hashlib
import logging
import math
import re
import sqlite3
from collections import defaultdict
from dataclasses import asdict, dataclass, field
from datetime import date, datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Sequence, Set, Tuple

logger = logging.getLogger("legal_ai.suggestion_engine")

# ---------------------------------------------------------------------------
# Path resolution — legal_ai → 00_SYSTEM → LitigationOS root
# ---------------------------------------------------------------------------
_HERE = Path(__file__).resolve().parent
_DB_PATH = _HERE.parents[1] / "litigation_context.db"

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

VALID_CATEGORIES: Set[str] = {
    "evidence", "filing", "deadline", "strategy", "defense", "discovery",
}

VALID_PRIORITIES: Tuple[str, ...] = ("critical", "high", "medium", "low")

PRIORITY_WEIGHTS: Dict[str, float] = {
    "critical": 1.0,
    "high": 0.75,
    "medium": 0.50,
    "low": 0.25,
}

URGENCY_WEIGHT: float = 0.55
IMPACT_WEIGHT: float = 0.45

LANE_LABELS: Dict[str, str] = {
    "A": "Custody (2024-001507-DC)",
    "B": "Housing (2025-002760-CZ)",
    "C": "Convergence (cross-lane)",
    "D": "PPO (2023-5907-PP)",
    "E": "Misconduct / JTC",
    "F": "Appellate (COA 366810)",
}

# Minimum evidence requirements per filing type
_EVIDENCE_REQUIREMENTS: Dict[str, Dict[str, List[str]]] = {
    "custody_modification": {
        "A": [
            "Parenting time interference log (305 incidents)",
            "Communication records (text/email)",
            "School records for L.D.W.",
            "Medical records for L.D.W.",
            "Police reports (bruising / welfare checks)",
            "CPS call documentation (single call — NOT 9)",
            "Witness declarations (family / friends)",
            "Financial records (child support)",
        ],
    },
    "motion_disqualification": {
        "A": [
            "Ex parte order log (18.26% grant rate)",
            "Hearing transcripts showing bias",
            "MCR 2.003 authority chain",
            "Comparison to normal ex parte rates (5%)",
            "Timeline of adverse rulings",
            "Prior disqualification motion + denial",
        ],
        "E": [
            "Judicial conduct records",
            "JTC complaint documentation",
            "Pattern-of-bias statistical analysis",
        ],
    },
    "housing_complaint": {
        "B": [
            "Lease agreement",
            "Utility billing records (overcharges)",
            "Habitability inspection reports",
            "Photos of sewage / structural issues",
            "Code violation notices",
            "Complaint correspondence to landlord",
            "Relocation cost documentation",
        ],
    },
    "ppo_defense": {
        "D": [
            "False PPO filing evidence",
            "Timeline of events contradicting PPO claims",
            "Communication records showing no harassment",
            "Witness statements",
            "Prior court orders (custody/parenting time)",
        ],
    },
    "section_1983": {
        "A": [
            "Constitutional violation documentation",
            "Due process denial evidence",
            "Equal protection violation evidence",
            "Pattern-or-practice evidence",
            "Qualified immunity analysis",
        ],
        "E": [
            "Judicial immunity exceptions analysis",
            "Administrative vs. judicial function evidence",
        ],
    },
    "jtc_complaint": {
        "E": [
            "Judicial conduct code violation evidence",
            "Statistical bias analysis",
            "Hearing transcript excerpts",
            "Comparison to peer judges",
            "Administrative misconduct evidence",
        ],
    },
    "appellate_brief": {
        "F": [
            "Lower court record (complete)",
            "Transcript of proceedings",
            "Preserved error documentation",
            "Issue preservation log",
            "Standard-of-review analysis per issue",
            "Authority chain per issue",
        ],
    },
    "contempt_motion": {
        "A": [
            "Order being violated",
            "Evidence of specific violations (dates/details)",
            "Proof of service of original order",
            "Good-faith efforts to comply documentation",
            "Communication showing wilful noncompliance",
        ],
    },
}

# Filing types expected per lane
_EXPECTED_FILINGS: Dict[str, List[str]] = {
    "A": [
        "custody_modification",
        "contempt_motion",
        "motion_disqualification",
        "motion_change_venue",
        "parenting_time_enforcement",
        "motion_sanctions",
    ],
    "B": [
        "housing_complaint",
        "demand_letter",
        "rico_complaint",
        "fha_complaint",
    ],
    "C": [
        "convergence_brief",
        "cross_lane_motion",
    ],
    "D": [
        "ppo_defense",
        "motion_dismiss_ppo",
        "malicious_prosecution",
    ],
    "E": [
        "jtc_complaint",
        "agc_complaint",
        "motion_disqualification",
        "section_1983",
    ],
    "F": [
        "appellate_brief",
        "application_leave_appeal",
        "motion_stay",
        "msc_complaint",
    ],
}

# Strategic filing sequences (order matters for pressure)
_STRATEGIC_SEQUENCES: List[Dict[str, Any]] = [
    {
        "name": "Disqualification Pressure",
        "sequence": ["jtc_complaint", "motion_disqualification", "section_1983"],
        "lanes": ["E", "A", "E"],
        "rationale": (
            "File JTC complaint first to establish judicial misconduct record, "
            "then seek disqualification under MCR 2.003 citing the JTC filing, "
            "then leverage both for federal §1983 due-process claim."
        ),
        "impact": 90.0,
    },
    {
        "name": "Custody Enforcement Cascade",
        "sequence": [
            "contempt_motion",
            "parenting_time_enforcement",
            "custody_modification",
        ],
        "lanes": ["A", "A", "A"],
        "rationale": (
            "File contempt to establish pattern of noncompliance, enforce "
            "existing parenting time order, then modify custody based on "
            "documented interference (305 incidents)."
        ),
        "impact": 85.0,
    },
    {
        "name": "Housing RICO Escalation",
        "sequence": ["demand_letter", "housing_complaint", "rico_complaint"],
        "lanes": ["B", "B", "B"],
        "rationale": (
            "Demand letter preserves good-faith requirement, complaint "
            "establishes claims, RICO trebles damages if fraud pattern proven."
        ),
        "impact": 80.0,
    },
    {
        "name": "Appellate Record Preservation",
        "sequence": [
            "motion_reconsideration",
            "application_leave_appeal",
            "appellate_brief",
        ],
        "lanes": ["A", "F", "F"],
        "rationale": (
            "Motion for reconsideration preserves error in the trial court, "
            "application for leave preserves appellate jurisdiction, "
            "brief on the merits argues reversal."
        ),
        "impact": 75.0,
    },
    {
        "name": "PPO Counter-Attack",
        "sequence": ["ppo_defense", "malicious_prosecution", "motion_sanctions"],
        "lanes": ["D", "D", "A"],
        "rationale": (
            "Defend against false PPO first, then file malicious prosecution "
            "for the false filing, then seek sanctions in the custody case."
        ),
        "impact": 70.0,
    },
]

# Cross-lane synergy map
_CROSS_LANE_SYNERGY: List[Dict[str, Any]] = [
    {
        "source_lane": "E",
        "target_lane": "A",
        "description": "Judicial misconduct evidence strengthens disqualification in custody",
        "evidence_types": ["bias_statistics", "ex_parte_orders", "hearing_transcripts"],
    },
    {
        "source_lane": "A",
        "target_lane": "D",
        "description": "Custody interference evidence rebuts PPO allegations",
        "evidence_types": ["parenting_time_logs", "communication_records"],
    },
    {
        "source_lane": "D",
        "target_lane": "A",
        "description": "False PPO evidence supports custody modification (bad faith)",
        "evidence_types": ["ppo_filing_records", "timeline_contradictions"],
    },
    {
        "source_lane": "B",
        "target_lane": "A",
        "description": "Housing instability evidence supports custody arguments",
        "evidence_types": ["habitability_reports", "relocation_records"],
    },
    {
        "source_lane": "A",
        "target_lane": "E",
        "description": "Pattern of biased rulings in custody feeds JTC complaint",
        "evidence_types": ["ruling_log", "denial_statistics"],
    },
    {
        "source_lane": "A",
        "target_lane": "F",
        "description": "Preserved trial-court errors form basis for appeal",
        "evidence_types": ["objection_log", "error_preservation_records"],
    },
]

# Defendants and service status tracking
_KNOWN_DEFENDANTS: List[Dict[str, str]] = [
    {"name": "Emily A. Watson", "lane": "A", "role": "defendant_custody"},
    {"name": "Emily A. Watson", "lane": "D", "role": "respondent_ppo"},
    {"name": "Shady Oaks MHP", "lane": "B", "role": "defendant_housing"},
    {"name": "Shady Oaks Management", "lane": "B", "role": "defendant_housing"},
    {"name": "Hon. Jenny L. McNeill", "lane": "E", "role": "respondent_misconduct"},
    {"name": "Muskegon County FOC", "lane": "A", "role": "party_interest"},
]


# ---------------------------------------------------------------------------
# Data Classes
# ---------------------------------------------------------------------------

@dataclass
class Suggestion:
    """A single prioritized litigation action suggestion."""

    suggestion_id: str
    category: str
    title: str
    description: str
    priority: str
    urgency_score: float
    impact_score: float
    combined_score: float
    lane: str
    action_items: List[str] = field(default_factory=list)
    dependencies: List[str] = field(default_factory=list)
    estimated_effort: str = "hours"

    def to_dict(self) -> dict:
        """Serialize to plain dictionary."""
        return asdict(self)


@dataclass
class SuggestionReport:
    """Aggregated suggestion report with system health summary."""

    generated_at: str = field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )
    total_suggestions: int = 0
    critical_count: int = 0
    suggestions: List[Suggestion] = field(default_factory=list)
    top_5_actions: List[str] = field(default_factory=list)
    system_health: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict:
        """Serialize to plain dictionary."""
        d = asdict(self)
        return d


# ---------------------------------------------------------------------------
# Helper: DB connection
# ---------------------------------------------------------------------------

def _connect(db_path: Optional[Path] = None) -> sqlite3.Connection:
    """Open a WAL-mode connection with safe PRAGMAs."""
    path = db_path or _DB_PATH
    conn = sqlite3.connect(str(path), timeout=60)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA busy_timeout = 60000")
    conn.execute("PRAGMA journal_mode = WAL")
    conn.execute("PRAGMA cache_size = -32000")
    conn.execute("PRAGMA temp_store = MEMORY")
    conn.execute("PRAGMA synchronous = NORMAL")
    return conn


def _table_exists(conn: sqlite3.Connection, name: str) -> bool:
    """Check if a table exists in the database."""
    row = conn.execute(
        "SELECT 1 FROM sqlite_master WHERE type='table' AND name=?", (name,)
    ).fetchone()
    return row is not None


def _safe_count(conn: sqlite3.Connection, table: str, where: str = "", params: tuple = ()) -> int:
    """Safely count rows, returning 0 if table is missing."""
    if not _table_exists(conn, table):
        return 0
    sql = f"SELECT COUNT(*) FROM [{table}]"
    if where:
        sql += f" WHERE {where}"
    try:
        row = conn.execute(sql, params).fetchone()
        return row[0] if row else 0
    except sqlite3.Error as exc:
        logger.warning("COUNT on %s failed: %s", table, exc)
        return 0


def _make_id(*parts: str) -> str:
    """Deterministic suggestion ID from content parts."""
    raw = "|".join(str(p) for p in parts)
    return hashlib.sha256(raw.encode()).hexdigest()[:12]


def _clamp(value: float, lo: float = 0.0, hi: float = 100.0) -> float:
    """Clamp a value to [lo, hi]."""
    return max(lo, min(hi, value))


def _combined(urgency: float, impact: float) -> float:
    """Weighted combination of urgency and impact scores."""
    return _clamp(urgency * URGENCY_WEIGHT + impact * IMPACT_WEIGHT)


def _priority_from_score(score: float) -> str:
    """Derive priority label from combined score."""
    if score >= 80:
        return "critical"
    if score >= 60:
        return "high"
    if score >= 40:
        return "medium"
    return "low"


# ---------------------------------------------------------------------------
# SuggestionEngine
# ---------------------------------------------------------------------------

class SuggestionEngine:
    """Analyze litigation state and suggest prioritized next actions.

    Scans the litigation database for evidence gaps, approaching deadlines,
    unfiled motions, weak arguments, service gaps, discovery opportunities,
    strategic filing windows, defense preparation needs, cross-lane synergies,
    and appellate readiness — then ranks every suggestion by a combined
    urgency × impact score.
    """

    def __init__(self, db_path: Optional[Path] = None) -> None:
        self._db_path = db_path or _DB_PATH
        self._generation_count: int = 0
        self._last_report: Optional[SuggestionReport] = None
        logger.info("SuggestionEngine initialized (db=%s)", self._db_path)

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def analyze(self) -> SuggestionReport:
        """Full system analysis across all lanes.

        Returns a :class:`SuggestionReport` containing every suggestion found,
        ranked by combined score, plus a system-health summary.
        """
        all_suggestions: List[Suggestion] = []
        all_suggestions.extend(self.get_evidence_suggestions())
        all_suggestions.extend(self.get_deadline_suggestions())
        all_suggestions.extend(self.get_filing_suggestions())
        all_suggestions.extend(self.get_strategy_suggestions())
        all_suggestions.extend(self.get_discovery_suggestions())
        all_suggestions.extend(self._get_defense_suggestions())
        all_suggestions.extend(self._get_cross_lane_suggestions())
        all_suggestions.extend(self._get_appellate_suggestions())

        ranked = self.rank_suggestions(all_suggestions)
        report = self._build_report(ranked)
        self._generation_count += 1
        self._last_report = report
        return report

    def analyze_lane(self, lane: str) -> SuggestionReport:
        """Analyze a single lane and return lane-specific suggestions.

        Parameters
        ----------
        lane : str
            One of A–F.
        """
        lane = lane.upper()
        if lane not in LANE_LABELS:
            logger.warning("Unknown lane %r — returning empty report", lane)
            return SuggestionReport()

        full = self.analyze()
        filtered = [s for s in full.suggestions if s.lane == lane]
        return self._build_report(filtered)

    def get_evidence_suggestions(self) -> List[Suggestion]:
        """Check evidence requirements vs available evidence for each filing type."""
        suggestions: List[Suggestion] = []
        try:
            conn = _connect(self._db_path)
            try:
                available = self._get_available_evidence(conn)
                for filing_type, lane_reqs in _EVIDENCE_REQUIREMENTS.items():
                    for lane, required in lane_reqs.items():
                        missing = self._find_missing_evidence(
                            required, available, lane
                        )
                        if missing:
                            pct_missing = len(missing) / max(len(required), 1)
                            urgency = _clamp(pct_missing * 80 + 10)
                            impact = _clamp(70 + pct_missing * 20)
                            score = _combined(urgency, impact)
                            suggestions.append(
                                Suggestion(
                                    suggestion_id=_make_id(
                                        "evidence", filing_type, lane
                                    ),
                                    category="evidence",
                                    title=f"Missing evidence for {filing_type} (Lane {lane})",
                                    description=(
                                        f"{len(missing)} of {len(required)} required "
                                        f"evidence items are missing or unconfirmed for "
                                        f"{filing_type} in Lane {lane}."
                                    ),
                                    priority=_priority_from_score(score),
                                    urgency_score=urgency,
                                    impact_score=impact,
                                    combined_score=score,
                                    lane=lane,
                                    action_items=[
                                        f"Locate or obtain: {m}" for m in missing
                                    ],
                                    dependencies=[],
                                    estimated_effort="hours"
                                    if len(missing) < 3
                                    else "days",
                                )
                            )
            finally:
                conn.close()
        except sqlite3.Error as exc:
            logger.error("Evidence suggestion scan failed: %s", exc)
        except Exception as exc:
            logger.error("Unexpected error in evidence suggestions: %s", exc)
        return suggestions

    def get_deadline_suggestions(self) -> List[Suggestion]:
        """Scan deadlines table and flag items within 7/14/30 day windows."""
        suggestions: List[Suggestion] = []
        try:
            conn = _connect(self._db_path)
            try:
                deadlines = self._fetch_deadlines(conn)
                today = date.today()
                for dl in deadlines:
                    due_str = dl.get("due_date") or dl.get("due_date_iso") or ""
                    if not due_str:
                        continue
                    try:
                        due = date.fromisoformat(due_str[:10])
                    except ValueError:
                        continue
                    days_left = (due - today).days
                    if days_left > 30:
                        continue

                    if days_left < 0:
                        urgency = 100.0
                        priority = "critical"
                        label = f"OVERDUE by {abs(days_left)} days"
                    elif days_left <= 3:
                        urgency = 95.0
                        priority = "critical"
                        label = f"{days_left} days remaining — IMMINENT"
                    elif days_left <= 7:
                        urgency = 85.0
                        priority = "critical"
                        label = f"{days_left} days remaining"
                    elif days_left <= 14:
                        urgency = 70.0
                        priority = "high"
                        label = f"{days_left} days remaining"
                    else:
                        urgency = 50.0
                        priority = "medium"
                        label = f"{days_left} days remaining"

                    filing = dl.get("filing_type", "unknown")
                    lane = dl.get("lane", dl.get("vehicle_name", "?"))[:1].upper()
                    impact = 80.0 if priority == "critical" else 60.0
                    score = _combined(urgency, impact)
                    action = dl.get("description", f"Complete {filing}")

                    suggestions.append(
                        Suggestion(
                            suggestion_id=_make_id("deadline", due_str, filing),
                            category="deadline",
                            title=f"Deadline: {filing} — {label}",
                            description=(
                                f"{filing} is due {due_str} ({label}). "
                                f"Lane {lane}."
                            ),
                            priority=priority,
                            urgency_score=urgency,
                            impact_score=impact,
                            combined_score=score,
                            lane=lane if lane in LANE_LABELS else "C",
                            action_items=[action, f"File by {due_str}"],
                            dependencies=[],
                            estimated_effort="hours",
                        )
                    )
            finally:
                conn.close()
        except sqlite3.Error as exc:
            logger.error("Deadline suggestion scan failed: %s", exc)
        except Exception as exc:
            logger.error("Unexpected error in deadline suggestions: %s", exc)
        return suggestions

    def get_filing_suggestions(self) -> List[Suggestion]:
        """Compare expected filings per lane vs filed status and service gaps."""
        suggestions: List[Suggestion] = []
        try:
            conn = _connect(self._db_path)
            try:
                filed = self._get_filed_items(conn)
                served = self._get_served_defendants(conn)

                # Unfiled motions
                for lane, expected in _EXPECTED_FILINGS.items():
                    for ft in expected:
                        if ft not in filed.get(lane, set()):
                            urgency = 60.0
                            impact = 70.0
                            score = _combined(urgency, impact)
                            suggestions.append(
                                Suggestion(
                                    suggestion_id=_make_id("filing", ft, lane),
                                    category="filing",
                                    title=f"Unfiled: {ft} (Lane {lane})",
                                    description=(
                                        f"{ft} has not been filed in Lane {lane} "
                                        f"({LANE_LABELS.get(lane, lane)}). "
                                        f"Consider preparing and filing."
                                    ),
                                    priority=_priority_from_score(score),
                                    urgency_score=urgency,
                                    impact_score=impact,
                                    combined_score=score,
                                    lane=lane,
                                    action_items=[
                                        f"Draft {ft}",
                                        "Run completeness scorer",
                                        "Run pre-filing QA",
                                        "File and serve",
                                    ],
                                    dependencies=[],
                                    estimated_effort="days",
                                )
                            )

                # Service gaps
                for defendant in _KNOWN_DEFENDANTS:
                    dname = defendant["name"]
                    dlane = defendant["lane"]
                    if dname not in served:
                        urgency = 55.0
                        impact = 65.0
                        score = _combined(urgency, impact)
                        suggestions.append(
                            Suggestion(
                                suggestion_id=_make_id("service", dname, dlane),
                                category="filing",
                                title=f"Service gap: {dname} (Lane {dlane})",
                                description=(
                                    f"{dname} may not have been served in "
                                    f"Lane {dlane}. Verify proof of service."
                                ),
                                priority="high",
                                urgency_score=urgency,
                                impact_score=impact,
                                combined_score=score,
                                lane=dlane,
                                action_items=[
                                    f"Verify service on {dname}",
                                    "Obtain proof of service if missing",
                                    "Consider alternative service if needed",
                                ],
                                dependencies=[],
                                estimated_effort="hours",
                            )
                        )
            finally:
                conn.close()
        except sqlite3.Error as exc:
            logger.error("Filing suggestion scan failed: %s", exc)
        except Exception as exc:
            logger.error("Unexpected error in filing suggestions: %s", exc)
        return suggestions

    def get_strategy_suggestions(self) -> List[Suggestion]:
        """Identify strategic filing sequences that create pressure."""
        suggestions: List[Suggestion] = []
        try:
            conn = _connect(self._db_path)
            try:
                filed = self._get_filed_items(conn)
                for seq in _STRATEGIC_SEQUENCES:
                    filed_steps: List[bool] = []
                    for ft, lane in zip(seq["sequence"], seq["lanes"]):
                        filed_steps.append(ft in filed.get(lane, set()))

                    # Find the first unfiled step
                    next_idx = None
                    for i, done in enumerate(filed_steps):
                        if not done:
                            next_idx = i
                            break
                    if next_idx is None:
                        continue  # sequence fully filed

                    # Check if previous steps are done (dependencies met)
                    deps_met = all(filed_steps[:next_idx])
                    next_ft = seq["sequence"][next_idx]
                    next_lane = seq["lanes"][next_idx]
                    pct_done = sum(filed_steps) / max(len(filed_steps), 1)

                    urgency = 50.0 + pct_done * 30
                    impact = seq["impact"]
                    score = _combined(urgency, impact)

                    dep_list: List[str] = []
                    if not deps_met:
                        for j in range(next_idx):
                            if not filed_steps[j]:
                                dep_list.append(
                                    f"File {seq['sequence'][j]} in Lane {seq['lanes'][j]}"
                                )

                    suggestions.append(
                        Suggestion(
                            suggestion_id=_make_id(
                                "strategy", seq["name"], next_ft
                            ),
                            category="strategy",
                            title=f"Strategy: {seq['name']} — next: {next_ft}",
                            description=(
                                f"{seq['rationale']} "
                                f"Progress: {sum(filed_steps)}/{len(filed_steps)} steps filed. "
                                f"Next action: file {next_ft} in Lane {next_lane}."
                            ),
                            priority=_priority_from_score(score),
                            urgency_score=urgency,
                            impact_score=impact,
                            combined_score=score,
                            lane=next_lane,
                            action_items=[
                                f"Draft {next_ft}",
                                f"File in Lane {next_lane}",
                            ],
                            dependencies=dep_list,
                            estimated_effort="days",
                        )
                    )
            finally:
                conn.close()
        except sqlite3.Error as exc:
            logger.error("Strategy suggestion scan failed: %s", exc)
        except Exception as exc:
            logger.error("Unexpected error in strategy suggestions: %s", exc)
        return suggestions

    def get_discovery_suggestions(self) -> List[Suggestion]:
        """Suggest interrogatories, document requests, and subpoenas based on evidence gaps."""
        suggestions: List[Suggestion] = []

        _DISCOVERY_MAP: Dict[str, List[Dict[str, str]]] = {
            "A": [
                {
                    "type": "interrogatory",
                    "target": "Emily A. Watson",
                    "topic": "Parenting time interference details",
                    "basis": "MCR 2.309",
                },
                {
                    "type": "document_request",
                    "target": "Emily A. Watson",
                    "topic": "Communication records re: L.D.W.",
                    "basis": "MCR 2.310",
                },
                {
                    "type": "subpoena",
                    "target": "L.D.W. school records custodian",
                    "topic": "School attendance and performance records",
                    "basis": "MCR 2.305",
                },
                {
                    "type": "subpoena",
                    "target": "L.D.W. medical provider",
                    "topic": "Medical records (bruising, wellness)",
                    "basis": "MCR 2.305",
                },
                {
                    "type": "interrogatory",
                    "target": "Friend of Court",
                    "topic": "Investigation notes and recommendations",
                    "basis": "MCR 2.309",
                },
            ],
            "B": [
                {
                    "type": "document_request",
                    "target": "Shady Oaks MHP",
                    "topic": "Utility billing records, all tenants",
                    "basis": "MCR 2.310",
                },
                {
                    "type": "document_request",
                    "target": "Shady Oaks MHP",
                    "topic": "Code inspection reports and maintenance logs",
                    "basis": "MCR 2.310",
                },
                {
                    "type": "interrogatory",
                    "target": "Shady Oaks Management",
                    "topic": "Ownership structure and responsible parties",
                    "basis": "MCR 2.309",
                },
            ],
            "D": [
                {
                    "type": "interrogatory",
                    "target": "Emily A. Watson",
                    "topic": "Basis for PPO allegations — specific incidents",
                    "basis": "MCR 2.309",
                },
                {
                    "type": "document_request",
                    "target": "Emily A. Watson",
                    "topic": "All communications cited in PPO petition",
                    "basis": "MCR 2.310",
                },
            ],
        }

        for lane, items in _DISCOVERY_MAP.items():
            for item in items:
                urgency = 45.0
                impact = 55.0
                score = _combined(urgency, impact)
                suggestions.append(
                    Suggestion(
                        suggestion_id=_make_id(
                            "discovery", item["type"], item["target"], lane
                        ),
                        category="discovery",
                        title=(
                            f"Discovery: {item['type'].replace('_', ' ').title()} — "
                            f"{item['target']}"
                        ),
                        description=(
                            f"Serve {item['type'].replace('_', ' ')} on {item['target']} "
                            f"regarding {item['topic']}. Authority: {item['basis']}."
                        ),
                        priority=_priority_from_score(score),
                        urgency_score=urgency,
                        impact_score=impact,
                        combined_score=score,
                        lane=lane,
                        action_items=[
                            f"Draft {item['type'].replace('_', ' ')} under {item['basis']}",
                            f"Serve on {item['target']}",
                            "Calendar response deadline (28 days)",
                        ],
                        dependencies=[],
                        estimated_effort="hours",
                    )
                )
        return suggestions

    def rank_suggestions(self, suggestions: List[Suggestion]) -> List[Suggestion]:
        """Sort suggestions by combined_score descending, then by priority weight."""
        return sorted(
            suggestions,
            key=lambda s: (
                s.combined_score,
                PRIORITY_WEIGHTS.get(s.priority, 0),
            ),
            reverse=True,
        )

    def get_stats(self) -> Dict[str, Any]:
        """Return engine statistics."""
        return {
            "engine": "SuggestionEngine",
            "version": "1.0.0",
            "db_path": str(self._db_path),
            "db_exists": self._db_path.exists(),
            "generation_count": self._generation_count,
            "last_report_at": (
                self._last_report.generated_at if self._last_report else None
            ),
            "last_suggestion_count": (
                self._last_report.total_suggestions if self._last_report else 0
            ),
            "lanes_tracked": list(LANE_LABELS.keys()),
            "evidence_filing_types": list(_EVIDENCE_REQUIREMENTS.keys()),
            "strategic_sequences": len(_STRATEGIC_SEQUENCES),
            "cross_lane_synergies": len(_CROSS_LANE_SYNERGY),
        }

    # ------------------------------------------------------------------
    # Internal generators
    # ------------------------------------------------------------------

    def _get_defense_suggestions(self) -> List[Suggestion]:
        """Anticipate opposing responses and prepare rebuttals."""
        suggestions: List[Suggestion] = []

        _DEFENSE_SCENARIOS: List[Dict[str, Any]] = [
            {
                "lane": "A",
                "title": "Prepare for emergency PPO filing",
                "description": (
                    "Emily A. Watson has a pattern of filing emergency PPO "
                    "motions when Andrew exercises parental rights. Prepare "
                    "a response brief with timeline evidence."
                ),
                "action_items": [
                    "Pre-draft PPO response template",
                    "Maintain current timeline of interactions",
                    "Keep proof of lawful conduct readily accessible",
                    "Document any contact initiated by opposing party",
                ],
                "urgency": 65.0,
                "impact": 70.0,
            },
            {
                "lane": "A",
                "title": "Counter ex parte motion likelihood",
                "description": (
                    "Judge McNeill grants ex parte motions at 18.26% "
                    "(3.65× normal 5% rate). Prepare objection template "
                    "and motion to set aside."
                ),
                "action_items": [
                    "Pre-draft motion to set aside ex parte order",
                    "Prepare due-process objection citing MCR 2.119(B)",
                    "Document statistical bias in ex parte grants",
                    "Prepare emergency appellate filing if needed",
                ],
                "urgency": 70.0,
                "impact": 75.0,
            },
            {
                "lane": "D",
                "title": "Prepare for false harassment allegations",
                "description": (
                    "Pattern: CPS reports reframed as harassment. "
                    "Andrew called CPS ONCE about bruising plus filed "
                    "police reports. Prepare rebuttal documentation."
                ),
                "action_items": [
                    "Compile CPS call record (single call)",
                    "Gather police reports filed",
                    "Prepare declaration regarding child-safety motivation",
                    "WARN: '9 CPS investigations' is FABRICATED — rebut if raised",
                ],
                "urgency": 60.0,
                "impact": 70.0,
            },
            {
                "lane": "B",
                "title": "Anticipate MTD on jurisdictional grounds",
                "description": (
                    "Shady Oaks defendants pattern: file MTD claiming "
                    "improper service or lack of jurisdiction. Prepare "
                    "proof of proper service and jurisdictional analysis."
                ),
                "action_items": [
                    "Document all service attempts with dates and method",
                    "Prepare jurisdictional brief citing MCL 600.701",
                    "Have backup service methods ready (publication, posting)",
                    "Pre-draft response to MTD",
                ],
                "urgency": 50.0,
                "impact": 60.0,
            },
            {
                "lane": "E",
                "title": "Prepare for disqualification denial",
                "description": (
                    "Judge McNeill will likely deny disqualification motion. "
                    "Prepare immediate appellate filing and federal §1983."
                ),
                "action_items": [
                    "Pre-draft application for leave to appeal denial",
                    "Prepare §1983 complaint referencing denial",
                    "Document all grounds for MCR 2.003 disqualification",
                    "Prepare MSC supervisory control application",
                ],
                "urgency": 55.0,
                "impact": 80.0,
            },
        ]

        for scenario in _DEFENSE_SCENARIOS:
            urgency = scenario["urgency"]
            impact = scenario["impact"]
            score = _combined(urgency, impact)
            suggestions.append(
                Suggestion(
                    suggestion_id=_make_id(
                        "defense", scenario["title"], scenario["lane"]
                    ),
                    category="defense",
                    title=f"Defense: {scenario['title']}",
                    description=scenario["description"],
                    priority=_priority_from_score(score),
                    urgency_score=urgency,
                    impact_score=impact,
                    combined_score=score,
                    lane=scenario["lane"],
                    action_items=scenario["action_items"],
                    dependencies=[],
                    estimated_effort="hours",
                )
            )
        return suggestions

    def _get_cross_lane_suggestions(self) -> List[Suggestion]:
        """Identify cross-lane evidence synergies."""
        suggestions: List[Suggestion] = []
        for synergy in _CROSS_LANE_SYNERGY:
            urgency = 40.0
            impact = 65.0
            score = _combined(urgency, impact)
            src = synergy["source_lane"]
            tgt = synergy["target_lane"]
            suggestions.append(
                Suggestion(
                    suggestion_id=_make_id("synergy", src, tgt),
                    category="strategy",
                    title=f"Cross-lane: Lane {src} → Lane {tgt}",
                    description=synergy["description"],
                    priority=_priority_from_score(score),
                    urgency_score=urgency,
                    impact_score=impact,
                    combined_score=score,
                    lane=tgt,
                    action_items=[
                        f"Review {et} evidence in Lane {src} for use in Lane {tgt}"
                        for et in synergy["evidence_types"]
                    ],
                    dependencies=[],
                    estimated_effort="hours",
                )
            )
        return suggestions

    def _get_appellate_suggestions(self) -> List[Suggestion]:
        """Check appellate readiness — record preservation and issue raising."""
        suggestions: List[Suggestion] = []

        _APPELLATE_CHECKS: List[Dict[str, Any]] = [
            {
                "title": "Verify complete lower-court record",
                "description": (
                    "Ensure all transcripts, orders, and filings are "
                    "included in the appellate record. Missing items "
                    "waive issues on appeal."
                ),
                "action_items": [
                    "Request all hearing transcripts",
                    "Compile docket sheet from trial court",
                    "Verify all orders are in the record",
                    "File any missing items via motion to supplement",
                ],
                "urgency": 60.0,
                "impact": 85.0,
            },
            {
                "title": "Confirm issue preservation",
                "description": (
                    "Every issue raised on appeal must have been "
                    "preserved via contemporaneous objection or motion "
                    "in the trial court. Unpreserved issues are reviewed "
                    "only for plain error."
                ),
                "action_items": [
                    "Cross-reference appellate issues with trial objections",
                    "Identify any unpreserved issues",
                    "Draft plain-error argument for unpreserved issues",
                    "File motion for reconsideration to preserve if possible",
                ],
                "urgency": 65.0,
                "impact": 90.0,
            },
            {
                "title": "Prepare standard-of-review analysis",
                "description": (
                    "Each appellate issue requires identification of the "
                    "correct standard of review: de novo, clear error, "
                    "or abuse of discretion."
                ),
                "action_items": [
                    "Map each issue to its standard of review",
                    "Research Michigan precedent for each standard",
                    "Draft standard-of-review section for brief",
                ],
                "urgency": 45.0,
                "impact": 75.0,
            },
        ]

        for check in _APPELLATE_CHECKS:
            urgency = check["urgency"]
            impact = check["impact"]
            score = _combined(urgency, impact)
            suggestions.append(
                Suggestion(
                    suggestion_id=_make_id("appellate", check["title"]),
                    category="filing",
                    title=f"Appellate: {check['title']}",
                    description=check["description"],
                    priority=_priority_from_score(score),
                    urgency_score=urgency,
                    impact_score=impact,
                    combined_score=score,
                    lane="F",
                    action_items=check["action_items"],
                    dependencies=[],
                    estimated_effort="days",
                )
            )
        return suggestions

    # ------------------------------------------------------------------
    # DB query helpers
    # ------------------------------------------------------------------

    def _get_available_evidence(
        self, conn: sqlite3.Connection
    ) -> Dict[str, Set[str]]:
        """Return available evidence keyed by lane.

        Tries multiple table names that may hold evidence metadata.
        """
        available: Dict[str, Set[str]] = defaultdict(set)
        for table in ("evidence", "evidence_items", "documents", "files"):
            if not _table_exists(conn, table):
                continue
            cols = {
                r[1]
                for r in conn.execute(f"PRAGMA table_info([{table}])").fetchall()
            }
            lane_col = (
                "lane"
                if "lane" in cols
                else "vehicle_name"
                if "vehicle_name" in cols
                else None
            )
            desc_col = (
                "description"
                if "description" in cols
                else "title"
                if "title" in cols
                else "filename"
                if "filename" in cols
                else "name"
                if "name" in cols
                else None
            )
            if not desc_col:
                continue
            sql = f"SELECT [{desc_col}]"
            if lane_col:
                sql += f", [{lane_col}]"
            sql += f" FROM [{table}] LIMIT 5000"
            try:
                for row in conn.execute(sql).fetchall():
                    desc_val = str(row[0] or "")
                    lane_val = str(row[1] or "C") if lane_col else "C"
                    lane_key = lane_val[:1].upper() if lane_val else "C"
                    if lane_key not in LANE_LABELS:
                        lane_key = "C"
                    available[lane_key].add(desc_val.lower())
            except sqlite3.Error as exc:
                logger.debug("Evidence query on %s failed: %s", table, exc)
        return available

    def _find_missing_evidence(
        self,
        required: List[str],
        available: Dict[str, Set[str]],
        lane: str,
    ) -> List[str]:
        """Return required items not fuzzy-matched in available evidence."""
        lane_evidence = available.get(lane, set())
        all_evidence = set()
        for v in available.values():
            all_evidence.update(v)

        missing: List[str] = []
        for req in required:
            req_lower = req.lower()
            # Check for keyword overlap
            keywords = set(re.findall(r"\w{4,}", req_lower))
            matched = False
            for ev in lane_evidence | all_evidence:
                ev_words = set(re.findall(r"\w{4,}", ev))
                if len(keywords & ev_words) >= max(1, len(keywords) // 3):
                    matched = True
                    break
            if not matched:
                missing.append(req)
        return missing

    def _fetch_deadlines(self, conn: sqlite3.Connection) -> List[Dict[str, Any]]:
        """Fetch deadline rows from the database."""
        for table in ("deadlines", "deadline_items", "filing_deadlines"):
            if not _table_exists(conn, table):
                continue
            cols = {
                r[1]
                for r in conn.execute(f"PRAGMA table_info([{table}])").fetchall()
            }
            date_col = (
                "due_date"
                if "due_date" in cols
                else "due_date_iso"
                if "due_date_iso" in cols
                else "deadline_date"
                if "deadline_date" in cols
                else None
            )
            if not date_col:
                continue
            try:
                rows = conn.execute(
                    f"SELECT * FROM [{table}] ORDER BY [{date_col}] ASC LIMIT 500"
                ).fetchall()
                return [dict(r) for r in rows]
            except sqlite3.Error as exc:
                logger.debug("Deadline fetch from %s failed: %s", table, exc)
        return []

    def _get_filed_items(
        self, conn: sqlite3.Connection
    ) -> Dict[str, Set[str]]:
        """Return set of filed item types per lane."""
        filed: Dict[str, Set[str]] = defaultdict(set)
        for table in ("filings", "filed_items", "filing_status", "filing_readiness"):
            if not _table_exists(conn, table):
                continue
            cols = {
                r[1]
                for r in conn.execute(f"PRAGMA table_info([{table}])").fetchall()
            }
            type_col = (
                "filing_type"
                if "filing_type" in cols
                else "type"
                if "type" in cols
                else "name"
                if "name" in cols
                else None
            )
            lane_col = (
                "lane"
                if "lane" in cols
                else "vehicle_name"
                if "vehicle_name" in cols
                else None
            )
            status_col = (
                "status"
                if "status" in cols
                else "filed"
                if "filed" in cols
                else None
            )
            if not type_col:
                continue
            sql = f"SELECT [{type_col}]"
            if lane_col:
                sql += f", [{lane_col}]"
            if status_col:
                sql += f", [{status_col}]"
            sql += f" FROM [{table}] LIMIT 2000"
            try:
                for row in conn.execute(sql).fetchall():
                    ft = str(row[0] or "").lower().replace(" ", "_")
                    lane_val = str(row[1] or "C") if lane_col else "C"
                    status_val = str(row[2] or "").lower() if status_col else "filed"
                    if status_val in ("filed", "complete", "done", "1", "true", "yes"):
                        lane_key = lane_val[:1].upper()
                        if lane_key not in LANE_LABELS:
                            lane_key = "C"
                        filed[lane_key].add(ft)
            except sqlite3.Error as exc:
                logger.debug("Filed-items query on %s failed: %s", table, exc)
        return filed

    def _get_served_defendants(self, conn: sqlite3.Connection) -> Set[str]:
        """Return set of defendant names that have been served."""
        served: Set[str] = set()
        for table in ("service_records", "proof_of_service", "service_log"):
            if not _table_exists(conn, table):
                continue
            cols = {
                r[1]
                for r in conn.execute(f"PRAGMA table_info([{table}])").fetchall()
            }
            name_col = (
                "defendant"
                if "defendant" in cols
                else "party_name"
                if "party_name" in cols
                else "name"
                if "name" in cols
                else None
            )
            if not name_col:
                continue
            try:
                for row in conn.execute(
                    f"SELECT [{name_col}] FROM [{table}] LIMIT 500"
                ).fetchall():
                    val = str(row[0] or "")
                    if val:
                        served.add(val)
            except sqlite3.Error as exc:
                logger.debug("Service query on %s failed: %s", table, exc)
        return served

    # ------------------------------------------------------------------
    # Report builder
    # ------------------------------------------------------------------

    def _build_report(self, suggestions: List[Suggestion]) -> SuggestionReport:
        """Assemble a SuggestionReport from ranked suggestions."""
        critical = [s for s in suggestions if s.priority == "critical"]
        top5 = [s.title for s in suggestions[:5]]

        # System health snapshot
        health: Dict[str, Any] = {
            "total_lanes": len(LANE_LABELS),
            "suggestions_by_lane": {},
            "suggestions_by_category": {},
            "suggestions_by_priority": {},
        }
        for lane in LANE_LABELS:
            health["suggestions_by_lane"][lane] = sum(
                1 for s in suggestions if s.lane == lane
            )
        for cat in VALID_CATEGORIES:
            health["suggestions_by_category"][cat] = sum(
                1 for s in suggestions if s.category == cat
            )
        for pri in VALID_PRIORITIES:
            health["suggestions_by_priority"][pri] = sum(
                1 for s in suggestions if s.priority == pri
            )

        return SuggestionReport(
            total_suggestions=len(suggestions),
            critical_count=len(critical),
            suggestions=suggestions,
            top_5_actions=top5,
            system_health=health,
        )
