# -*- coding: utf-8 -*-
"""
Judicial Recusal Engine — LitigationOS Legal AI Subsystem
==========================================================
Catalogs judicial bias indicators, scores severity, prepares MCR 2.003
disqualification motions (peremptory and for-cause), documents ex parte
contacts, and integrates with JTC complaint preparation per MCR 9.104.

Case Context
------------
    Plaintiff:  Andrew James Pigors (Pro Se)
    Defendant:  Emily A. Watson
    Child:      L.D.W. (per MCR 8.119(H)) — Male
    Judge:      Hon. Jenny L. McNeill — 14th Circuit Court
    Case No.:   2024-001507-DC (primary)
    Lane:       E (Judicial Misconduct / JTC)

Usage::

    from legal_ai.judicial_recusal_engine import JudicialRecusalEngine

    engine = JudicialRecusalEngine()
    engine.scan_records()
    report = engine.generate_report()

Zero external dependencies.  CPU-first.  Local-only.
"""
from __future__ import annotations

import json
import logging
import sqlite3
import sys
import textwrap
import uuid
from collections import defaultdict
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from enum import Enum, IntEnum
from pathlib import Path
from typing import Any, Dict, List, Optional, Sequence, Set, Tuple

logger = logging.getLogger("legal_ai.judicial_recusal_engine")

# ---------------------------------------------------------------------------
# Path resolution
# ---------------------------------------------------------------------------
_HERE = Path(__file__).resolve().parent
_REPO = _HERE.parents[1]
_DB_PATH = _REPO / "litigation_context.db"

# ---------------------------------------------------------------------------
# Case constants
# ---------------------------------------------------------------------------
_PLAINTIFF = "Andrew James Pigors"
_PLAINTIFF_ADDRESS = "1977 Whitehall Road, Lot 17, North Muskegon, MI 49445"
_DEFENDANT = "Emily A. Watson"
_CHILD_INITIALS = "L.D.W."
_JUDGE = "Hon. Jenny L. McNeill"
_COURT = "14th Circuit Court"
_CASE_NUMBER = "2024-001507-DC"
_LANE = "E"

_JTC_ADDRESS = (
    "Judicial Tenure Commission\n"
    "3034 W. Grand Blvd., Suite 8-450\n"
    "Detroit, MI 48202"
)

# ---------------------------------------------------------------------------
# Enumerations
# ---------------------------------------------------------------------------


class BiasIndicatorType(str, Enum):
    """Categories of judicial bias."""

    VERBAL = "verbal"
    PROCEDURAL = "procedural"
    EVIDENTIARY = "evidentiary"
    EX_PARTE = "ex_parte"
    TEMPORAL = "temporal"
    OUTCOME = "outcome"
    DEMEANOR = "demeanor"

    @property
    def label(self) -> str:
        _labels = {
            "verbal": "Verbal bias — statements revealing prejudgment",
            "procedural": "Procedural bias — differential courtroom treatment",
            "evidentiary": "Evidentiary bias — unfair evidence rulings",
            "ex_parte": "Ex parte bias — unauthorised communications",
            "temporal": "Temporal bias — disproportionate time allocation",
            "outcome": "Outcome bias — pattern of one-sided rulings",
            "demeanor": "Demeanor bias — non-verbal hostile indicators",
        }
        return _labels.get(self.value, self.value)


class RecusalGround(str, Enum):
    """MCR 2.003(C)(1) disqualification grounds."""

    PERSONAL_BIAS = "MCR 2.003(C)(1)(a)"
    PERSONAL_KNOWLEDGE = "MCR 2.003(C)(1)(b)"
    PRIOR_ATTORNEY = "MCR 2.003(C)(1)(c)"
    FINANCIAL_INTEREST = "MCR 2.003(C)(1)(d)"
    RELATED_TO_PARTY = "MCR 2.003(C)(1)(e)"
    FORMER_ASSOCIATE = "MCR 2.003(C)(1)(f)"
    APPEARANCE_OF_IMPROPRIETY = "MCR 2.003(C)(1)(g)"

    @property
    def label(self) -> str:
        _labels = {
            "MCR 2.003(C)(1)(a)": "Personal bias or prejudice concerning a party",
            "MCR 2.003(C)(1)(b)": "Personal knowledge of disputed evidentiary facts",
            "MCR 2.003(C)(1)(c)": "Prior involvement as attorney in the matter",
            "MCR 2.003(C)(1)(d)": "Financial interest in the controversy",
            "MCR 2.003(C)(1)(e)": "Related to party or attorney (3rd degree)",
            "MCR 2.003(C)(1)(f)": "Former associate of attorney in the case",
            "MCR 2.003(C)(1)(g)": "Conduct creating appearance of impropriety",
        }
        return _labels.get(self.value, self.value)


class MotionType(str, Enum):
    """Types of disqualification motions."""

    PEREMPTORY = "peremptory"
    FOR_CAUSE = "for_cause"


class MotionOutcome(str, Enum):
    """Possible outcomes for a recusal motion."""

    GRANTED = "granted"
    DENIED = "denied"
    PENDING = "pending"
    WITHDRAWN = "withdrawn"


class CanonViolation(str, Enum):
    """Michigan Code of Judicial Conduct canons."""

    CANON_1 = "Canon 1"
    CANON_2A = "Canon 2A"
    CANON_2B = "Canon 2B"
    CANON_3A_1 = "Canon 3A(1)"
    CANON_3A_4 = "Canon 3A(4)"
    CANON_3A_7 = "Canon 3A(7)"
    CANON_3C = "Canon 3C"
    CANON_4 = "Canon 4"

    @property
    def subject(self) -> str:
        _subjects = {
            "Canon 1": "Integrity and independence of judiciary",
            "Canon 2A": "Avoid impropriety and appearance thereof",
            "Canon 2B": "Shall not lend prestige of office",
            "Canon 3A(1)": "Faithful performance of judicial duties",
            "Canon 3A(4)": "Patient, dignified, courteous to all",
            "Canon 3A(7)": "Shall not engage in ex parte communications",
            "Canon 3C": "Disqualification when required",
            "Canon 4": "Limits on extra-judicial activities",
        }
        return _subjects.get(self.value, "")


class DocumentationLevel(str, Enum):
    """How well a bias indicator is documented."""

    TRANSCRIPT_CONFIRMED = "transcript_confirmed"
    WITNESS_CORROBORATED = "witness_corroborated"
    SELF_REPORTED = "self_reported"

    @property
    def multiplier(self) -> int:
        return {
            "transcript_confirmed": 3,
            "witness_corroborated": 2,
            "self_reported": 1,
        }[self.value]


class PatternLevel(str, Enum):
    """Frequency pattern of bias incidents."""

    ISOLATED = "isolated"
    RECURRING = "recurring"
    SYSTEMATIC = "systematic"

    @property
    def multiplier(self) -> int:
        return {"isolated": 1, "recurring": 2, "systematic": 3}[self.value]


class RecommendedAction(str, Enum):
    """Recommended actions based on bias score."""

    DOCUMENT_ONLY = "document_only"
    FOR_CAUSE_MOTION = "for_cause_motion"
    MOTION_PLUS_JTC = "motion_plus_jtc"
    EMERGENCY_ALL = "emergency_all"


# ---------------------------------------------------------------------------
# Bias score thresholds
# ---------------------------------------------------------------------------
_SCORE_THRESHOLDS: Dict[str, Tuple[int, int]] = {
    "within_discretion": (0, 10),
    "moderate_bias": (11, 25),
    "severe_bias": (26, 50),
    "extreme_bias": (51, 9999),
}


def _classify_score(total: int) -> str:
    for label, (lo, hi) in _SCORE_THRESHOLDS.items():
        if lo <= total <= hi:
            return label.replace("_", " ").title()
    return "Unknown"


def _recommend_action(total: int) -> RecommendedAction:
    if total <= 10:
        return RecommendedAction.DOCUMENT_ONLY
    if total <= 25:
        return RecommendedAction.FOR_CAUSE_MOTION
    if total <= 50:
        return RecommendedAction.MOTION_PLUS_JTC
    return RecommendedAction.EMERGENCY_ALL


# ---------------------------------------------------------------------------
# Dataclasses
# ---------------------------------------------------------------------------


@dataclass
class BiasIndicator:
    """A single documented incident of judicial bias."""

    indicator_id: str = field(default_factory=lambda: uuid.uuid4().hex[:12])
    judge_name: str = _JUDGE
    court: str = _COURT
    incident_date: str = ""
    category: BiasIndicatorType = BiasIndicatorType.VERBAL
    description: str = ""
    mcr_ground: Optional[RecusalGround] = None
    canon_violated: Optional[CanonViolation] = None
    severity: int = 1
    documentation: DocumentationLevel = DocumentationLevel.SELF_REPORTED
    pattern: PatternLevel = PatternLevel.ISOLATED
    evidence_refs: List[str] = field(default_factory=list)
    witnesses: List[str] = field(default_factory=list)
    transcript_ref: str = ""
    case_number: str = _CASE_NUMBER
    lane: str = _LANE
    notes: str = ""

    @property
    def weighted_score(self) -> int:
        return self.severity * self.documentation.multiplier * self.pattern.multiplier

    def to_dict(self) -> Dict[str, Any]:
        d = asdict(self)
        d["category"] = self.category.value
        d["mcr_ground"] = self.mcr_ground.value if self.mcr_ground else None
        d["canon_violated"] = self.canon_violated.value if self.canon_violated else None
        d["documentation"] = self.documentation.value
        d["pattern"] = self.pattern.value
        d["weighted_score"] = self.weighted_score
        return d


@dataclass
class RecusalMotion:
    """A judicial disqualification motion."""

    motion_id: str = field(default_factory=lambda: uuid.uuid4().hex[:12])
    judge_name: str = _JUDGE
    motion_type: MotionType = MotionType.FOR_CAUSE
    mcr_grounds: List[RecusalGround] = field(default_factory=list)
    supporting_indicators: List[str] = field(default_factory=list)
    filed_date: str = ""
    hearing_date: str = ""
    decided_date: str = ""
    outcome: MotionOutcome = MotionOutcome.PENDING
    appealed: bool = False
    appeal_case: str = ""
    affidavit_text: str = ""
    case_number: str = _CASE_NUMBER
    lane: str = _LANE

    def to_dict(self) -> Dict[str, Any]:
        d = asdict(self)
        d["motion_type"] = self.motion_type.value
        d["mcr_grounds"] = [g.value for g in self.mcr_grounds]
        d["outcome"] = self.outcome.value
        return d


@dataclass
class JTCComplaint:
    """A Judicial Tenure Commission complaint."""

    complaint_id: str = field(default_factory=lambda: uuid.uuid4().hex[:12])
    judge_name: str = _JUDGE
    court: str = _COURT
    complainant: str = _PLAINTIFF
    complainant_address: str = _PLAINTIFF_ADDRESS
    factual_allegations: List[str] = field(default_factory=list)
    canon_violations: List[CanonViolation] = field(default_factory=list)
    supporting_indicators: List[str] = field(default_factory=list)
    supporting_documents: List[str] = field(default_factory=list)
    prepared_date: str = field(
        default_factory=lambda: datetime.now(timezone.utc).strftime("%Y-%m-%d")
    )

    def to_dict(self) -> Dict[str, Any]:
        d = asdict(self)
        d["canon_violations"] = [c.value for c in self.canon_violations]
        return d


@dataclass
class RecusalReport:
    """Complete judicial recusal analysis report."""

    report_id: str = field(default_factory=lambda: uuid.uuid4().hex[:12])
    generated_at: str = field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )
    judge_name: str = _JUDGE
    court: str = _COURT
    case_number: str = _CASE_NUMBER
    total_indicators: int = 0
    composite_score: int = 0
    score_classification: str = ""
    recommended_action: str = ""
    peremptory_available: bool = True
    indicators: List[BiasIndicator] = field(default_factory=list)
    motions: List[RecusalMotion] = field(default_factory=list)
    jtc_complaint: Optional[JTCComplaint] = None
    category_breakdown: Dict[str, int] = field(default_factory=dict)
    ground_breakdown: Dict[str, int] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "report_id": self.report_id,
            "generated_at": self.generated_at,
            "judge_name": self.judge_name,
            "court": self.court,
            "case_number": self.case_number,
            "total_indicators": self.total_indicators,
            "composite_score": self.composite_score,
            "score_classification": self.score_classification,
            "recommended_action": self.recommended_action,
            "peremptory_available": self.peremptory_available,
            "indicators": [i.to_dict() for i in self.indicators],
            "motions": [m.to_dict() for m in self.motions],
            "jtc_complaint": (
                self.jtc_complaint.to_dict() if self.jtc_complaint else None
            ),
            "category_breakdown": self.category_breakdown,
            "ground_breakdown": self.ground_breakdown,
        }


# ---------------------------------------------------------------------------
# BiasScorer
# ---------------------------------------------------------------------------


class BiasScorer:
    """Quantifies judicial bias from a list of indicators."""

    def compute_score(self, indicators: Sequence[BiasIndicator]) -> int:
        return sum(ind.weighted_score for ind in indicators)

    def category_breakdown(
        self, indicators: Sequence[BiasIndicator]
    ) -> Dict[str, int]:
        breakdown: Dict[str, int] = defaultdict(int)
        for ind in indicators:
            breakdown[ind.category.value] += ind.weighted_score
        return dict(breakdown)

    def ground_breakdown(
        self, indicators: Sequence[BiasIndicator]
    ) -> Dict[str, int]:
        breakdown: Dict[str, int] = defaultdict(int)
        for ind in indicators:
            if ind.mcr_ground:
                breakdown[ind.mcr_ground.value] += ind.weighted_score
        return dict(breakdown)

    def detect_patterns(
        self, indicators: Sequence[BiasIndicator]
    ) -> Dict[str, PatternLevel]:
        """Detect pattern levels per category."""
        by_cat: Dict[str, int] = defaultdict(int)
        for ind in indicators:
            by_cat[ind.category.value] += 1

        patterns: Dict[str, PatternLevel] = {}
        for cat, count in by_cat.items():
            if count >= 5:
                patterns[cat] = PatternLevel.SYSTEMATIC
            elif count >= 3:
                patterns[cat] = PatternLevel.RECURRING
            else:
                patterns[cat] = PatternLevel.ISOLATED
        return patterns

    def get_stats(self) -> Dict[str, Any]:
        return {
            "component": "BiasScorer",
            "bias_categories": len(BiasIndicatorType),
            "recusal_grounds": len(RecusalGround),
        }


# ---------------------------------------------------------------------------
# RecusalAnalyzer
# ---------------------------------------------------------------------------


class RecusalAnalyzer:
    """Matches bias indicators to MCR 2.003 grounds and prepares motions."""

    _GROUND_MAP: Dict[BiasIndicatorType, List[RecusalGround]] = {
        BiasIndicatorType.VERBAL: [RecusalGround.PERSONAL_BIAS],
        BiasIndicatorType.PROCEDURAL: [
            RecusalGround.PERSONAL_BIAS,
            RecusalGround.APPEARANCE_OF_IMPROPRIETY,
        ],
        BiasIndicatorType.EVIDENTIARY: [
            RecusalGround.PERSONAL_BIAS,
            RecusalGround.APPEARANCE_OF_IMPROPRIETY,
        ],
        BiasIndicatorType.EX_PARTE: [
            RecusalGround.PERSONAL_KNOWLEDGE,
            RecusalGround.APPEARANCE_OF_IMPROPRIETY,
        ],
        BiasIndicatorType.TEMPORAL: [RecusalGround.APPEARANCE_OF_IMPROPRIETY],
        BiasIndicatorType.OUTCOME: [
            RecusalGround.PERSONAL_BIAS,
            RecusalGround.APPEARANCE_OF_IMPROPRIETY,
        ],
        BiasIndicatorType.DEMEANOR: [RecusalGround.PERSONAL_BIAS],
    }

    def map_grounds(
        self, indicators: Sequence[BiasIndicator]
    ) -> Dict[RecusalGround, List[BiasIndicator]]:
        """Map each indicator to applicable MCR 2.003 grounds."""
        mapping: Dict[RecusalGround, List[BiasIndicator]] = defaultdict(list)
        for ind in indicators:
            if ind.mcr_ground:
                mapping[ind.mcr_ground].append(ind)
            else:
                grounds = self._GROUND_MAP.get(ind.category, [])
                for g in grounds:
                    mapping[g].append(ind)
        return dict(mapping)

    def prepare_motion(
        self,
        indicators: Sequence[BiasIndicator],
        motion_type: MotionType = MotionType.FOR_CAUSE,
    ) -> RecusalMotion:
        """Prepare a disqualification motion from indicators."""
        grounds_map = self.map_grounds(indicators)
        grounds = list(grounds_map.keys())
        indicator_ids = [ind.indicator_id for ind in indicators]

        motion = RecusalMotion(
            motion_type=motion_type,
            mcr_grounds=grounds,
            supporting_indicators=indicator_ids,
        )

        if motion_type == MotionType.FOR_CAUSE:
            motion.affidavit_text = self._build_affidavit(indicators, grounds)

        return motion

    def _build_affidavit(
        self,
        indicators: Sequence[BiasIndicator],
        grounds: List[RecusalGround],
    ) -> str:
        """Generate affidavit text for a for-cause motion."""
        lines: List[str] = [
            "AFFIDAVIT IN SUPPORT OF MOTION FOR DISQUALIFICATION",
            f"Case No.: {_CASE_NUMBER}",
            f"Subject Judge: {_JUDGE}",
            "",
            f"I, {_PLAINTIFF}, being duly sworn, depose and state:",
            "",
        ]
        for i, ind in enumerate(indicators, 1):
            lines.append(
                f"{i}. On {ind.incident_date or '[date]'}, "
                f"{ind.description or '[description of incident]'}"
            )
            if ind.transcript_ref:
                lines.append(f"   (Transcript reference: {ind.transcript_ref})")
            if ind.witnesses:
                lines.append(
                    f"   Witnesses: {', '.join(ind.witnesses)}"
                )
            lines.append("")

        lines.append(
            "The foregoing facts establish grounds for disqualification "
            "under the following provisions of MCR 2.003(C)(1):"
        )
        for g in grounds:
            lines.append(f"  - {g.value}: {g.label}")
        lines.append("")
        lines.append(
            "I declare under penalty of perjury that the foregoing "
            "is true and correct."
        )
        lines.append("")
        lines.append(f"{'_' * 40}")
        lines.append(f"{_PLAINTIFF}")
        lines.append(f"{_PLAINTIFF_ADDRESS}")
        return "\n".join(lines)

    def get_stats(self) -> Dict[str, Any]:
        return {
            "component": "RecusalAnalyzer",
            "ground_mappings": len(self._GROUND_MAP),
        }


# ---------------------------------------------------------------------------
# JTCComplaintBuilder
# ---------------------------------------------------------------------------


class JTCComplaintBuilder:
    """Prepares JTC complaints per MCR 9.104."""

    def build_complaint(
        self,
        indicators: Sequence[BiasIndicator],
    ) -> JTCComplaint:
        """Build a JTC complaint from bias indicators."""
        allegations: List[str] = []
        canons: Set[CanonViolation] = set()
        doc_refs: List[str] = []
        indicator_ids: List[str] = []

        for ind in indicators:
            allegations.append(
                f"On {ind.incident_date or '[date]'}: {ind.description}"
            )
            if ind.canon_violated:
                canons.add(ind.canon_violated)
            doc_refs.extend(ind.evidence_refs)
            indicator_ids.append(ind.indicator_id)

        # Default canons based on category if none specified
        if not canons:
            for ind in indicators:
                if ind.category == BiasIndicatorType.EX_PARTE:
                    canons.add(CanonViolation.CANON_3A_7)
                elif ind.category == BiasIndicatorType.DEMEANOR:
                    canons.add(CanonViolation.CANON_3A_4)
                elif ind.category in (
                    BiasIndicatorType.VERBAL,
                    BiasIndicatorType.PROCEDURAL,
                ):
                    canons.add(CanonViolation.CANON_2A)

        complaint = JTCComplaint(
            factual_allegations=allegations,
            canon_violations=sorted(canons, key=lambda c: c.value),
            supporting_indicators=indicator_ids,
            supporting_documents=sorted(set(doc_refs)),
        )
        return complaint

    def to_text(self, complaint: JTCComplaint) -> str:
        """Render the JTC complaint as text."""
        lines: List[str] = [
            complaint.prepared_date,
            "",
            _JTC_ADDRESS,
            "",
            "RE: Complaint Against Judicial Officer",
            f"    Judge: {complaint.judge_name}",
            f"    Court: {complaint.court}",
            "",
            "Dear Members of the Judicial Tenure Commission:",
            "",
            f"I, {complaint.complainant}, respectfully submit this complaint "
            f"against {complaint.judge_name} pursuant to MCR 9.104.",
            "",
            "FACTUAL ALLEGATIONS:",
            "",
        ]
        for i, allegation in enumerate(complaint.factual_allegations, 1):
            lines.append(f"{i}. {allegation}")
        lines.append("")
        lines.append("CANONS OF JUDICIAL CONDUCT VIOLATED:")
        lines.append("")
        for canon in complaint.canon_violations:
            lines.append(f"  - {canon.value}: {canon.subject}")
        lines.append("")
        if complaint.supporting_documents:
            lines.append("SUPPORTING DOCUMENTS:")
            lines.append("")
            for doc in complaint.supporting_documents:
                lines.append(f"  - {doc}")
            lines.append("")
        lines.append(
            "I affirm under penalty of perjury that the facts stated "
            "herein are true and correct to the best of my knowledge."
        )
        lines.append("")
        lines.append("Respectfully submitted,")
        lines.append("")
        lines.append(f"{'_' * 40}")
        lines.append(complaint.complainant)
        lines.append(complaint.complainant_address)
        return "\n".join(lines)

    def get_stats(self) -> Dict[str, Any]:
        return {
            "component": "JTCComplaintBuilder",
            "canon_violations_tracked": len(CanonViolation),
        }


# ---------------------------------------------------------------------------
# Database layer
# ---------------------------------------------------------------------------

_CREATE_INDICATORS_SQL = textwrap.dedent("""\
    CREATE TABLE IF NOT EXISTS judicial_bias_indicators (
        indicator_id    TEXT PRIMARY KEY,
        judge_name      TEXT DEFAULT 'Hon. Jenny L. McNeill',
        court           TEXT DEFAULT '14th Circuit Court',
        incident_date   TEXT NOT NULL,
        category        TEXT NOT NULL,
        description     TEXT NOT NULL,
        mcr_ground      TEXT,
        canon_violated  TEXT,
        severity        INTEGER CHECK(severity BETWEEN 1 AND 3),
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

_CREATE_MOTIONS_SQL = textwrap.dedent("""\
    CREATE TABLE IF NOT EXISTS recusal_motions (
        motion_id       TEXT PRIMARY KEY,
        judge_name      TEXT DEFAULT 'Hon. Jenny L. McNeill',
        motion_type     TEXT CHECK(motion_type IN ('peremptory','for_cause')),
        mcr_grounds     TEXT,
        filed_date      TEXT,
        hearing_date    TEXT,
        decided_date    TEXT,
        outcome         TEXT CHECK(outcome IN ('granted','denied','pending','withdrawn')),
        appealed        INTEGER DEFAULT 0,
        appeal_case     TEXT,
        indicator_refs  TEXT,
        lane            TEXT DEFAULT 'E',
        created_at      TEXT DEFAULT (datetime('now'))
    )
""")

_CREATE_INDEXES_SQL = [
    "CREATE INDEX IF NOT EXISTS idx_bias_judge "
    "ON judicial_bias_indicators(judge_name, incident_date)",
    "CREATE INDEX IF NOT EXISTS idx_bias_category "
    "ON judicial_bias_indicators(category, severity)",
    "CREATE INDEX IF NOT EXISTS idx_recusal_outcome "
    "ON recusal_motions(outcome, motion_type)",
]


def _ensure_tables(conn: sqlite3.Connection) -> None:
    conn.execute(_CREATE_INDICATORS_SQL)
    conn.execute(_CREATE_MOTIONS_SQL)
    for idx in _CREATE_INDEXES_SQL:
        conn.execute(idx)
    conn.commit()


# ---------------------------------------------------------------------------
# JudicialRecusalEngine — orchestrator
# ---------------------------------------------------------------------------


class JudicialRecusalEngine:
    """Top-level orchestrator for judicial recusal analysis.

    Combines :class:`BiasScorer`, :class:`RecusalAnalyzer`, and
    :class:`JTCComplaintBuilder` into a unified workflow.
    """

    def __init__(self, db_path: Optional[Path] = None) -> None:
        self._db_path = db_path or _DB_PATH
        self._scorer = BiasScorer()
        self._analyzer = RecusalAnalyzer()
        self._jtc_builder = JTCComplaintBuilder()
        self._indicators: List[BiasIndicator] = []
        self._motions: List[RecusalMotion] = []
        self._report: Optional[RecusalReport] = None
        self._peremptory_available: bool = True

    # -- indicator management --

    def add_indicator(self, indicator: BiasIndicator) -> None:
        self._indicators.append(indicator)

    def add_indicators(self, indicators: Sequence[BiasIndicator]) -> None:
        self._indicators.extend(indicators)

    def set_peremptory_used(self) -> None:
        """Mark peremptory disqualification as already used."""
        self._peremptory_available = False

    # -- database scan --

    def scan_records(self, limit: int = 500) -> int:
        """Scan litigation_context.db for judicial bias evidence."""
        if not self._db_path.exists():
            logger.warning("Database not found at %s", self._db_path)
            return 0

        try:
            conn = sqlite3.connect(str(self._db_path), timeout=60)
            conn.execute("PRAGMA busy_timeout=60000")
            conn.execute("PRAGMA journal_mode=WAL")
            conn.execute("PRAGMA cache_size=-32000")
            conn.row_factory = sqlite3.Row
        except sqlite3.Error as exc:
            logger.error("DB connection failed: %s", exc)
            return 0

        count = 0
        try:
            tables = {
                r[0]
                for r in conn.execute(
                    "SELECT name FROM sqlite_master WHERE type='table'"
                ).fetchall()
            }

            # Load existing indicators if table exists
            if "judicial_bias_indicators" in tables:
                cols = [
                    r[1]
                    for r in conn.execute(
                        "PRAGMA table_info(judicial_bias_indicators)"
                    ).fetchall()
                ]
                rows = conn.execute(
                    f"SELECT * FROM judicial_bias_indicators LIMIT {int(limit)}"
                ).fetchall()
                for row in rows:
                    ind = BiasIndicator(
                        indicator_id=str(row["indicator_id"]),
                        incident_date=str(row.get("incident_date", "") or ""),
                        category=BiasIndicatorType(row.get("category", "verbal")),
                        description=str(row.get("description", "") or ""),
                        severity=int(row.get("severity", 1) or 1),
                        transcript_ref=str(row.get("transcript_ref", "") or ""),
                    )
                    if "mcr_ground" in cols and row["mcr_ground"]:
                        try:
                            ind.mcr_ground = RecusalGround(row["mcr_ground"])
                        except ValueError:
                            pass
                    if "canon_violated" in cols and row["canon_violated"]:
                        try:
                            ind.canon_violated = CanonViolation(row["canon_violated"])
                        except ValueError:
                            pass
                    if "evidence_refs" in cols and row["evidence_refs"]:
                        try:
                            ind.evidence_refs = json.loads(row["evidence_refs"])
                        except (json.JSONDecodeError, TypeError):
                            pass
                    if "witnesses" in cols and row["witnesses"]:
                        try:
                            ind.witnesses = json.loads(row["witnesses"])
                        except (json.JSONDecodeError, TypeError):
                            pass
                    self._indicators.append(ind)
                    count += 1

            # Also scan documents for bias keywords
            if "documents" in tables:
                doc_cols = [
                    r[1]
                    for r in conn.execute(
                        "PRAGMA table_info(documents)"
                    ).fetchall()
                ]
                has_preview = "content_preview" in doc_cols
                if has_preview:
                    bias_keywords = [
                        "ex parte", "bias", "prejudg", "hostile",
                        "impartial", "recus", "disqualif",
                    ]
                    conditions = " OR ".join(
                        f"content_preview LIKE '%{kw}%'" for kw in bias_keywords
                    )
                    doc_rows = conn.execute(
                        f"SELECT * FROM documents WHERE ({conditions}) LIMIT 100"
                    ).fetchall()
                    for row in doc_rows:
                        preview = str(row.get("content_preview", "") or "")
                        cat = BiasIndicatorType.VERBAL
                        if "ex parte" in preview.lower():
                            cat = BiasIndicatorType.EX_PARTE
                        ind = BiasIndicator(
                            incident_date=str(row.get("created_at", "") or ""),
                            category=cat,
                            description=f"Bias keyword in document: {preview[:100]}",
                            evidence_refs=[str(row.get("doc_id", "") or row.get("id", ""))],
                        )
                        self._indicators.append(ind)
                        count += 1
        except sqlite3.Error as exc:
            logger.error("Record scan failed: %s", exc)
        finally:
            conn.close()

        return count

    # -- analysis --

    def analyse(self) -> RecusalReport:
        """Run full recusal analysis and generate report."""
        score = self._scorer.compute_score(self._indicators)
        cat_breakdown = self._scorer.category_breakdown(self._indicators)
        gnd_breakdown = self._scorer.ground_breakdown(self._indicators)
        classification = _classify_score(score)
        action = _recommend_action(score)

        # Auto-prepare motion if warranted
        if action in (
            RecommendedAction.FOR_CAUSE_MOTION,
            RecommendedAction.MOTION_PLUS_JTC,
            RecommendedAction.EMERGENCY_ALL,
        ):
            motion = self._analyzer.prepare_motion(
                self._indicators, MotionType.FOR_CAUSE
            )
            self._motions.append(motion)

        # Auto-prepare JTC complaint if warranted
        jtc_complaint = None
        if action in (
            RecommendedAction.MOTION_PLUS_JTC,
            RecommendedAction.EMERGENCY_ALL,
        ):
            jtc_complaint = self._jtc_builder.build_complaint(self._indicators)

        self._report = RecusalReport(
            total_indicators=len(self._indicators),
            composite_score=score,
            score_classification=classification,
            recommended_action=action.value,
            peremptory_available=self._peremptory_available,
            indicators=list(self._indicators),
            motions=list(self._motions),
            jtc_complaint=jtc_complaint,
            category_breakdown=cat_breakdown,
            ground_breakdown=gnd_breakdown,
        )
        return self._report

    # -- report rendering --

    def generate_report(self, fmt: str = "markdown") -> str:
        """Convenience: analyse and render."""
        if not self._report:
            self.analyse()
        assert self._report is not None

        if fmt == "json":
            return json.dumps(self._report.to_dict(), indent=2, default=str)
        return self._to_markdown()

    def _to_markdown(self) -> str:
        assert self._report is not None
        r = self._report
        lines: List[str] = [
            "## Judicial Disqualification Analysis",
            f"### Judge: {r.judge_name} — {r.court}",
            f"### Case: {r.case_number} | Lane: E | Generated: {r.generated_at[:10]}",
            "",
            f"#### Composite Bias Score: {r.composite_score} — {r.score_classification}",
            f"#### Total Indicators: {r.total_indicators}",
            f"#### Peremptory Available: {'Yes' if r.peremptory_available else 'No'}",
            "",
            "| # | Date | Category | Description | MCR Ground | Severity | Weighted |",
            "|---|------|----------|-------------|------------|----------|----------|",
        ]
        for i, ind in enumerate(r.indicators, 1):
            lines.append(
                f"| {i} | {ind.incident_date} | {ind.category.value} | "
                f"{ind.description[:60]} | "
                f"{ind.mcr_ground.value if ind.mcr_ground else 'TBD'} | "
                f"{ind.severity} | {ind.weighted_score} |"
            )
        lines.append("")

        if r.category_breakdown:
            lines.append("#### Category Breakdown")
            for cat, score in sorted(
                r.category_breakdown.items(), key=lambda x: -x[1]
            ):
                lines.append(f"- {cat}: {score} points")
            lines.append("")

        lines.append("#### Recommended Action")
        action_labels = {
            "document_only": "Document only — score within judicial discretion",
            "for_cause_motion": "File for-cause disqualification under MCR 2.003(C)",
            "motion_plus_jtc": "File disqualification motion + JTC complaint",
            "emergency_all": "Emergency motion + JTC + appellate mandamus",
        }
        lines.append(
            f"**{action_labels.get(r.recommended_action, r.recommended_action)}**"
        )
        lines.append("")

        if r.motions:
            lines.append("#### Prepared Motions")
            for m in r.motions:
                lines.append(
                    f"- {m.motion_type.value}: "
                    f"{', '.join(g.value for g in m.mcr_grounds)}"
                )

        return "\n".join(lines)

    # -- persistence --

    def persist(self) -> int:
        """Write indicators and motions to database."""
        if not self._db_path.exists():
            logger.warning("Database not found — cannot persist")
            return 0

        try:
            conn = sqlite3.connect(str(self._db_path), timeout=60)
            conn.execute("PRAGMA busy_timeout=60000")
            conn.execute("PRAGMA journal_mode=WAL")
            conn.execute("PRAGMA cache_size=-32000")
        except sqlite3.Error as exc:
            logger.error("DB connection failed: %s", exc)
            return 0

        written = 0
        try:
            _ensure_tables(conn)

            ind_rows: List[Tuple[Any, ...]] = []
            for ind in self._indicators:
                ind_rows.append((
                    ind.indicator_id,
                    ind.judge_name,
                    ind.court,
                    ind.incident_date,
                    ind.category.value,
                    ind.description,
                    ind.mcr_ground.value if ind.mcr_ground else None,
                    ind.canon_violated.value if ind.canon_violated else None,
                    ind.severity,
                    ind.documentation.value,
                    ind.pattern.value,
                    json.dumps(ind.evidence_refs),
                    json.dumps(ind.witnesses),
                    ind.transcript_ref,
                    ind.lane,
                    ind.case_number,
                ))
            conn.executemany(
                "INSERT OR IGNORE INTO judicial_bias_indicators "
                "(indicator_id, judge_name, court, incident_date, category, "
                "description, mcr_ground, canon_violated, severity, "
                "documentation, pattern_level, evidence_refs, witnesses, "
                "transcript_ref, lane, case_number) "
                "VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
                ind_rows,
            )
            written += len(ind_rows)

            mot_rows: List[Tuple[Any, ...]] = []
            for mot in self._motions:
                mot_rows.append((
                    mot.motion_id,
                    mot.judge_name,
                    mot.motion_type.value,
                    json.dumps([g.value for g in mot.mcr_grounds]),
                    mot.filed_date,
                    mot.hearing_date,
                    mot.decided_date,
                    mot.outcome.value,
                    1 if mot.appealed else 0,
                    mot.appeal_case,
                    json.dumps(mot.supporting_indicators),
                    mot.lane,
                ))
            conn.executemany(
                "INSERT OR IGNORE INTO recusal_motions "
                "(motion_id, judge_name, motion_type, mcr_grounds, "
                "filed_date, hearing_date, decided_date, outcome, "
                "appealed, appeal_case, indicator_refs, lane) "
                "VALUES (?,?,?,?,?,?,?,?,?,?,?,?)",
                mot_rows,
            )
            written += len(mot_rows)
            conn.commit()
        except sqlite3.Error as exc:
            logger.error("Persist failed: %s", exc)
        finally:
            conn.close()

        return written

    # -- stats --

    def get_stats(self) -> Dict[str, Any]:
        return {
            "module": "judicial_recusal_engine",
            "indicators_loaded": len(self._indicators),
            "motions_prepared": len(self._motions),
            "report_generated": self._report is not None,
            "composite_score": (
                self._report.composite_score if self._report else None
            ),
            "classification": (
                self._report.score_classification if self._report else None
            ),
            "peremptory_available": self._peremptory_available,
            "db_path": str(self._db_path),
            "scorer": self._scorer.get_stats(),
            "analyzer": self._analyzer.get_stats(),
            "jtc_builder": self._jtc_builder.get_stats(),
        }

    def reset(self) -> None:
        self._indicators.clear()
        self._motions.clear()
        self._report = None


# ---------------------------------------------------------------------------
# CLI demo
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    sys.stdout = open(  # noqa: SIM115
        sys.stdout.fileno(), mode="w", encoding="utf-8", errors="replace"
    )
    logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")

    print("=" * 60)
    print("  Judicial Recusal Engine — LitigationOS")
    print("=" * 60)
    print()

    demo_indicators = [
        BiasIndicator(
            incident_date="2024-07-15",
            category=BiasIndicatorType.VERBAL,
            description="Judge made dismissive comment about pro se filings",
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
            witnesses=["Court staff member"],
        ),
        BiasIndicator(
            incident_date="2024-09-10",
            category=BiasIndicatorType.PROCEDURAL,
            description="Denied Plaintiff's motion without reading supporting brief",
            mcr_ground=RecusalGround.PERSONAL_BIAS,
            severity=2,
            documentation=DocumentationLevel.TRANSCRIPT_CONFIRMED,
            pattern=PatternLevel.RECURRING,
            transcript_ref="Tr. 9/10/2024 p.5:1-10",
        ),
        BiasIndicator(
            incident_date="2024-10-01",
            category=BiasIndicatorType.OUTCOME,
            description="Ruled against Plaintiff on 8 of 8 contested motions",
            mcr_ground=RecusalGround.PERSONAL_BIAS,
            severity=3,
            documentation=DocumentationLevel.SELF_REPORTED,
            pattern=PatternLevel.SYSTEMATIC,
        ),
    ]

    engine = JudicialRecusalEngine()
    engine.add_indicators(demo_indicators)
    report = engine.analyse()

    print(engine.generate_report())
    print()
    print("--- Stats ---")
    import pprint

    pprint.pprint(engine.get_stats())
