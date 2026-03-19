# -*- coding: utf-8 -*-
"""
Deposition Strategist — LitigationOS Legal AI Subsystem
========================================================
Comprehensive deposition preparation and analysis engine for the
Pigors v. Watson litigation.  Handles witness profiling, question
generation (direct, cross, impeachment), deposition planning,
transcript analysis, and strategic orchestration across all six
case lanes.

Case Lanes:
    Lane A — Custody (2024-001507-DC)
    Lane B — Housing (2025-002760-CZ)
    Lane C — Convergence (cross-lane)
    Lane D — PPO (2023-5907-PP)
    Lane E — Misconduct / JTC (Judge McNeill)
    Lane F — Appellate (COA 366810)

Michigan Court Rules Encoded:
    MCR 2.306(A)  — Deposition by oral examination (any party may take)
    MCR 2.306(B)  — Notice requirements (reasonable written notice)
    MCR 2.307     — Subpoena for deposition
    MCR 2.308     — Use of depositions at trial
    MRE 613       — Prior inconsistent statements
    MRE 611       — Mode and order of examination

Case Context:
    Plaintiff:  Andrew James Pigors (Pro Se)
    Defendant:  Emily A. Watson
    Child:      L.D.W. (per MCR 8.119(H)) — Male
    Judge:      Hon. Jenny L. McNeill — 14th Circuit Court

Usage:
    from legal_ai.deposition_strategist import DepositionStrategist

    engine = DepositionStrategist()
    plan = engine.prepare_full_deposition("Emily A. Watson", "A")
    stats = engine.get_stats()

Zero external dependencies.  CPU-first.  Local-only.
"""
from __future__ import annotations

import hashlib
import json
import logging
import re
import sqlite3
import textwrap
import uuid
from collections import Counter, defaultdict
from dataclasses import asdict, dataclass, field
from datetime import date, datetime, timedelta, timezone
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple

logger = logging.getLogger("legal_ai.deposition_strategist")

# ---------------------------------------------------------------------------
# Path resolution — legal_ai → 00_SYSTEM → LitigationOS root
# ---------------------------------------------------------------------------
_HERE = Path(__file__).resolve().parent
_DB_PATH = _HERE.parents[1] / "litigation_context.db"

# ---------------------------------------------------------------------------
# Case Constants
# ---------------------------------------------------------------------------
_PLAINTIFF = "Andrew James Pigors"
_DEFENDANT = "Emily A. Watson"
_CHILD_INITIALS = "L.D.W."
_CHILD_NAME = "Lincoln David Watson"
_JUDGE = "Hon. Jenny L. McNeill"

LANE_LABELS: Dict[str, str] = {
    "A": "Custody (2024-001507-DC)",
    "B": "Housing (2025-002760-CZ)",
    "C": "Convergence (cross-lane)",
    "D": "PPO (2023-5907-PP)",
    "E": "Misconduct / JTC",
    "F": "Appellate (COA 366810)",
}

LANE_CASE_NUMBERS: Dict[str, str] = {
    "A": "2024-001507-DC",
    "B": "2025-002760-CZ",
    "C": "Multi-lane",
    "D": "2023-5907-PP",
    "E": "Judge McNeill",
    "F": "COA 366810",
}


# ---------------------------------------------------------------------------
# Enumerations
# ---------------------------------------------------------------------------

class WitnessRole(str, Enum):
    """Role of a witness in the litigation."""
    PARTY = "party"
    EXPERT = "expert"
    FACT = "fact"
    CHARACTER = "character"


class QuestionCategory(str, Enum):
    """Categories for deposition questions."""
    FOUNDATIONAL = "foundational"
    IMPEACHMENT = "impeachment"
    ADMISSION_SEEKING = "admission_seeking"
    TIMELINE = "timeline"
    CREDIBILITY = "credibility"
    DAMAGE_PROOF = "damage_proof"


class QuestionStyle(str, Enum):
    """Question style for examination."""
    OPEN = "open"           # Direct examination — open-ended
    LEADING = "leading"     # Cross examination — leading
    COMPOUND = "compound"   # Follow-up sequences
    HYPOTHETICAL = "hypothetical"


class ObjectionType(str, Enum):
    """Common deposition objection types."""
    RELEVANCE = "relevance"
    FORM = "form"
    COMPOUND = "compound"
    ASSUMES_FACTS = "assumes_facts"
    CALLS_FOR_SPECULATION = "calls_for_speculation"
    CALLS_FOR_LEGAL_CONCLUSION = "calls_for_legal_conclusion"
    VAGUE = "vague"
    PRIVILEGE = "privilege"
    ASKED_AND_ANSWERED = "asked_and_answered"
    BEYOND_SCOPE = "beyond_scope"


class DepositionStatus(str, Enum):
    """Status of deposition preparation."""
    DRAFT = "draft"
    PLANNED = "planned"
    NOTICE_SENT = "notice_sent"
    COMPLETED = "completed"
    ANALYZED = "analyzed"


class PerformanceRating(str, Enum):
    """Witness performance rating."""
    EXCELLENT = "excellent"
    GOOD = "good"
    NEUTRAL = "neutral"
    POOR = "poor"
    DEVASTATING = "devastating"


# ---------------------------------------------------------------------------
# Michigan-Specific Rules
# ---------------------------------------------------------------------------

MCR_RULES: Dict[str, Dict[str, str]] = {
    "MCR 2.306(A)": {
        "title": "Deposition by Oral Examination",
        "summary": "Any party may take the deposition of any person, "
                   "including a party, by oral examination.",
        "key_points": "No leave of court required after commencement of action.",
    },
    "MCR 2.306(B)": {
        "title": "Notice of Examination",
        "summary": "Reasonable written notice must be given to every other party. "
                   "Notice must state time, place, and name/address of deponent.",
        "key_points": "Must allow reasonable time; 30 days before trial cutoff.",
    },
    "MCR 2.306(D)": {
        "title": "Duration",
        "summary": "A deposition is limited to 1 day of 7 hours unless "
                   "the court orders otherwise or parties stipulate.",
        "key_points": "7-hour limit; breaks do not count against time.",
    },
    "MCR 2.307": {
        "title": "Subpoena for Deposition",
        "summary": "A subpoena may command attendance at a deposition. "
                   "Must be served at least 14 days before the deposition.",
        "key_points": "Non-party witnesses require subpoena; 14-day service.",
    },
    "MCR 2.308": {
        "title": "Use of Depositions at Trial",
        "summary": "Depositions may be used for impeachment (any witness), "
                   "admission (adverse party), or substantively (unavailable).",
        "key_points": "Impeachment per MRE 613; adverse party admissions; "
                      "unavailability allows full reading.",
    },
    "MRE 611": {
        "title": "Mode and Order of Examination",
        "summary": "Court exercises control over mode/order of interrogation "
                   "to make effective for truth, avoid waste, protect witnesses.",
        "key_points": "Leading questions on cross; court controls scope.",
    },
    "MRE 613": {
        "title": "Prior Inconsistent Statements",
        "summary": "Witness must be given opportunity to explain or deny "
                   "a prior inconsistent statement before extrinsic evidence.",
        "key_points": "Commit → Confront → Contrast pattern; opportunity "
                      "to explain required.",
    },
}


# ---------------------------------------------------------------------------
# Question Templates
# ---------------------------------------------------------------------------

_FOUNDATIONAL_TEMPLATES: List[str] = [
    "Please state your full legal name for the record.",
    "What is your current home address?",
    "Are you currently employed? If so, where and in what capacity?",
    "What is your relationship to {party}?",
    "How long have you known {party}?",
    "Have you ever been deposed before? If so, when and in what case?",
    "Do you understand that you are under oath today?",
    "Have you reviewed any documents in preparation for today's deposition?",
    "Have you spoken with anyone about your testimony today?",
    "Are you taking any medications that might affect your ability to testify?",
]

_IMPEACHMENT_COMMIT: List[str] = [
    "You testified today that {current_claim}, correct?",
    "And that is your testimony under oath?",
    "You're not going to change that testimony, are you?",
    "Is there any reason your memory about this would be inaccurate?",
]

_IMPEACHMENT_CONFRONT: List[str] = [
    "I'd like to direct your attention to {exhibit_ref}, which is your "
    "{source_type} dated {date}.",
    "Do you recognize this document?",
    "Please read the highlighted portion aloud for the record.",
    "In this {source_type}, you stated {prior_statement}, didn't you?",
]

_IMPEACHMENT_CONTRAST: List[str] = [
    "So today you say {current_claim}, but on {date} you said "
    "{prior_statement}. Which is true?",
    "Can you explain the difference between what you said then and "
    "what you're saying now?",
    "Were you lying then, or are you lying now?",
]

_TIMELINE_TEMPLATES: List[str] = [
    "Let's establish a timeline. What happened first regarding {topic}?",
    "When did you first become aware of {event}?",
    "What was the date, to the best of your recollection?",
    "What happened immediately after {event}?",
    "Were there any witnesses present when {event} occurred?",
    "Did you make any notes or records at the time of {event}?",
    "How much time elapsed between {event_a} and {event_b}?",
]

_ADMISSION_SEEKING_TEMPLATES: List[str] = [
    "Isn't it true that {assertion}?",
    "You would agree that {fact}, wouldn't you?",
    "You're not disputing that {fact}, are you?",
    "Would you agree that a reasonable person would {action} in that situation?",
    "So it's fair to say that {conclusion}?",
]

_CREDIBILITY_TEMPLATES: List[str] = [
    "Have you ever been convicted of a crime?",
    "Have you ever made a false statement under oath?",
    "Do you have any financial interest in the outcome of this case?",
    "Has anyone promised you anything in exchange for your testimony?",
    "Have you discussed what you would testify about with {party}?",
    "How many times have you met with opposing counsel?",
]

_DAMAGE_PROOF_TEMPLATES: List[str] = [
    "Can you describe the harm you personally observed?",
    "What financial losses resulted from {event}?",
    "Do you have documentation of those losses?",
    "How has {event} affected {person}'s daily life?",
    "Can you quantify the cost of {damage_item}?",
    "When did the harm first begin?",
    "Is the harm ongoing?",
]

# ---------------------------------------------------------------------------
# Topic-Specific Question Banks (per lane)
# ---------------------------------------------------------------------------

_LANE_TOPICS: Dict[str, Dict[str, List[str]]] = {
    "A": {
        "custody_interference": [
            "Describe the custody arrangement ordered by the court.",
            "How many times has {defendant} failed to comply with the parenting time order?",
            "Did {defendant} provide advance notice when denying parenting time?",
            "What was the effect on {child} when parenting time was denied?",
            "Did you contact law enforcement regarding any denied parenting time?",
        ],
        "best_interest_factors": [
            "Describe {child}'s relationship with his father.",
            "How would you characterize {child}'s emotional well-being?",
            "What is {child}'s current school situation?",
            "Who primarily handles {child}'s medical appointments?",
            "Describe {child}'s daily routine when with his father.",
        ],
        "ex_parte_contacts": [
            "Have you had any communications with Judge McNeill outside of court?",
            "Has anyone communicated with the judge on your behalf without the other party present?",
            "Were all filings properly served on the opposing party?",
        ],
    },
    "B": {
        "habitability": [
            "Describe the condition of the dwelling at {address}.",
            "When did you first notice the habitability issues?",
            "Did you report these issues to management?",
            "What was management's response to your complaint?",
            "Were repairs ever made? If so, when and by whom?",
        ],
        "discrimination": [
            "Were you treated differently from other tenants? How so?",
            "Did anyone make comments about your familial status?",
            "Were families with children treated differently than other tenants?",
        ],
    },
    "D": {
        "ppo_basis": [
            "What specific conduct formed the basis for the PPO petition?",
            "Did you personally witness the alleged conduct?",
            "Were there any witnesses to the events described in the petition?",
            "Did you report these incidents to law enforcement at the time?",
        ],
        "ppo_impact": [
            "How has the PPO affected {plaintiff}'s ability to see {child}?",
            "Were any of the PPO conditions impossible to comply with?",
        ],
    },
    "E": {
        "judicial_conduct": [
            "Describe any interactions you observed between Judge McNeill and any party.",
            "Were all hearings conducted on the record?",
            "Did Judge McNeill disclose any potential conflicts of interest?",
            "Were any rulings made without giving both parties opportunity to be heard?",
        ],
    },
    "F": {
        "appellate_issues": [
            "What errors do you believe occurred in the lower court proceedings?",
            "Were objections made on the record regarding the issues being appealed?",
        ],
    },
}


# ---------------------------------------------------------------------------
# Database Helpers
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


_DEPOSITION_PREP_DDL = """\
CREATE TABLE IF NOT EXISTS deposition_prep (
    id              TEXT PRIMARY KEY,
    witness_name    TEXT NOT NULL,
    witness_role    TEXT NOT NULL DEFAULT 'fact',
    case_lane       TEXT NOT NULL,
    case_number     TEXT,
    status          TEXT NOT NULL DEFAULT 'draft',
    objectives_json TEXT,
    questions_json  TEXT,
    plan_json       TEXT,
    analysis_json   TEXT,
    question_count  INTEGER DEFAULT 0,
    created_at      TEXT NOT NULL,
    updated_at      TEXT NOT NULL
)
"""

_WITNESS_PROFILES_DDL = """\
CREATE TABLE IF NOT EXISTS witness_profiles (
    id                TEXT PRIMARY KEY,
    name              TEXT NOT NULL,
    role              TEXT NOT NULL DEFAULT 'fact',
    relationship      TEXT,
    lane              TEXT,
    credibility_score REAL DEFAULT 50.0,
    known_biases_json TEXT,
    prior_statements_json TEXT,
    deposition_count  INTEGER DEFAULT 0,
    notes             TEXT,
    created_at        TEXT NOT NULL,
    updated_at        TEXT NOT NULL
)
"""

_STATEMENT_RECORDS_DDL = """\
CREATE TABLE IF NOT EXISTS statement_records (
    id                TEXT PRIMARY KEY,
    witness_id        TEXT NOT NULL,
    source_type       TEXT NOT NULL,
    statement_date    TEXT,
    content           TEXT NOT NULL,
    page_ref          TEXT,
    exhibit_ref       TEXT,
    consistency_score REAL DEFAULT 100.0,
    contradicts_json  TEXT,
    created_at        TEXT NOT NULL,
    FOREIGN KEY (witness_id) REFERENCES witness_profiles(id)
)
"""


def _ensure_tables(conn: sqlite3.Connection) -> None:
    """Create all required tables if they don't exist."""
    conn.execute(_DEPOSITION_PREP_DDL)
    conn.execute(_WITNESS_PROFILES_DDL)
    conn.execute(_STATEMENT_RECORDS_DDL)
    conn.commit()


# ---------------------------------------------------------------------------
# Data Models
# ---------------------------------------------------------------------------

@dataclass
class StatementRecord:
    """A single recorded statement by a witness."""

    statement_id: str = ""
    witness_id: str = ""
    source_type: str = "filing"  # transcript, filing, affidavit, social_media
    statement_date: str = ""
    content: str = ""
    page_ref: str = ""
    exhibit_ref: str = ""
    consistency_score: float = 100.0
    contradicts: List[str] = field(default_factory=list)

    def __post_init__(self) -> None:
        if not self.statement_id:
            self.statement_id = str(uuid.uuid4())[:12]

    def to_dict(self) -> Dict[str, Any]:
        """Serialise to dictionary."""
        return asdict(self)

    def check_consistency(self, other_statements: List[StatementRecord]) -> float:
        """Check consistency against other statements. Returns score 0-100."""
        if not other_statements or not self.content:
            return self.consistency_score

        content_lower = self.content.lower()
        contradiction_count = 0
        total_compared = 0

        negation_pairs = [
            ("did", "did not"), ("was", "was not"), ("never", "always"),
            ("denied", "allowed"), ("present", "absent"),
            ("before", "after"), ("true", "false"), ("yes", "no"),
        ]

        for other in other_statements:
            if other.statement_id == self.statement_id:
                continue
            other_lower = other.content.lower()
            total_compared += 1

            for pos, neg in negation_pairs:
                if (pos in content_lower and neg in other_lower) or \
                   (neg in content_lower and pos in other_lower):
                    contradiction_count += 1
                    if other.statement_id not in self.contradicts:
                        self.contradicts.append(other.statement_id)
                    break

        if total_compared == 0:
            return self.consistency_score

        self.consistency_score = max(
            0.0, 100.0 - (contradiction_count / total_compared * 100.0)
        )
        return self.consistency_score


@dataclass
class WitnessProfile:
    """Complete profile of a deposition witness."""

    witness_id: str = ""
    name: str = ""
    role: str = "fact"
    relationship_to_case: str = ""
    known_biases: List[str] = field(default_factory=list)
    credibility_score: float = 50.0
    prior_statements: List[StatementRecord] = field(default_factory=list)
    deposition_history: List[Dict[str, Any]] = field(default_factory=list)
    lane: str = "A"
    notes: str = ""

    def __post_init__(self) -> None:
        if not self.witness_id:
            self.witness_id = hashlib.sha256(
                self.name.lower().encode("utf-8")
            ).hexdigest()[:12]

    def to_dict(self) -> Dict[str, Any]:
        """Serialise to dictionary."""
        d = asdict(self)
        d["prior_statements"] = [s.to_dict() for s in self.prior_statements]
        return d

    @classmethod
    def from_db(cls, row: sqlite3.Row) -> WitnessProfile:
        """Construct a WitnessProfile from a database row."""
        biases = []
        statements: List[StatementRecord] = []
        keys = row.keys() if hasattr(row, "keys") else []

        if "known_biases_json" in keys:
            try:
                biases = json.loads(row["known_biases_json"] or "[]")
            except (json.JSONDecodeError, KeyError):
                pass
        if "prior_statements_json" in keys:
            try:
                raw_stmts = json.loads(row["prior_statements_json"] or "[]")
                for s in raw_stmts:
                    statements.append(StatementRecord(**s))
            except (json.JSONDecodeError, KeyError, TypeError):
                pass

        def _get(key: str, default: Any = "") -> Any:
            try:
                return row[key] if key in keys else default
            except (IndexError, KeyError):
                return default

        return cls(
            witness_id=_get("id", ""),
            name=_get("name", ""),
            role=_get("role", "fact"),
            relationship_to_case=_get("relationship", "") or "",
            known_biases=biases,
            credibility_score=float(_get("credibility_score", 50.0) or 50.0),
            prior_statements=statements,
            deposition_history=[],
            lane=_get("lane", "A") or "A",
            notes=_get("notes", "") or "",
        )

    def update_credibility(self, adjustment: float, reason: str = "") -> float:
        """Adjust credibility score within 0-100 bounds."""
        old = self.credibility_score
        self.credibility_score = max(0.0, min(100.0, self.credibility_score + adjustment))
        logger.info(
            "Credibility for %s: %.1f → %.1f (%s)",
            self.name, old, self.credibility_score, reason or "adjustment",
        )
        return self.credibility_score

    def add_statement(self, stmt: StatementRecord) -> None:
        """Add a statement record and recheck consistency."""
        stmt.witness_id = self.witness_id
        self.prior_statements.append(stmt)
        stmt.check_consistency(self.prior_statements)

    def get_contradiction_count(self) -> int:
        """Count total contradictions across all statements."""
        return sum(len(s.contradicts) for s in self.prior_statements)


@dataclass
class DepositionQuestion:
    """A single deposition question with metadata."""

    question_id: str = ""
    text: str = ""
    category: str = "foundational"
    style: str = "open"
    target_topic: str = ""
    priority: int = 5  # 1 (highest) to 10 (lowest)
    estimated_minutes: float = 2.0
    follow_ups: List[str] = field(default_factory=list)
    objection_risk: str = ""
    objection_type: str = ""
    mcr_basis: str = ""
    exhibit_needed: str = ""
    notes: str = ""

    def __post_init__(self) -> None:
        if not self.question_id:
            self.question_id = str(uuid.uuid4())[:8]

    def to_dict(self) -> Dict[str, Any]:
        """Serialise to dictionary."""
        return asdict(self)


@dataclass
class DepositionPlan:
    """Complete deposition plan for a witness."""

    plan_id: str = ""
    witness: Optional[WitnessProfile] = None
    case_lane: str = "A"
    objectives: List[str] = field(default_factory=list)
    questions: List[DepositionQuestion] = field(default_factory=list)
    exhibit_list: List[Dict[str, str]] = field(default_factory=list)
    estimated_duration_minutes: float = 120.0
    notice_text: str = ""
    status: str = "draft"
    mcr_compliance: Dict[str, bool] = field(default_factory=dict)
    created_at: str = ""

    def __post_init__(self) -> None:
        if not self.plan_id:
            self.plan_id = str(uuid.uuid4())[:12]
        if not self.created_at:
            self.created_at = datetime.now(timezone.utc).isoformat()

    def to_dict(self) -> Dict[str, Any]:
        """Serialise to dictionary."""
        d: Dict[str, Any] = {
            "plan_id": self.plan_id,
            "case_lane": self.case_lane,
            "objectives": self.objectives,
            "questions": [q.to_dict() for q in self.questions],
            "exhibit_list": self.exhibit_list,
            "estimated_duration_minutes": self.estimated_duration_minutes,
            "notice_text": self.notice_text,
            "status": self.status,
            "mcr_compliance": self.mcr_compliance,
            "created_at": self.created_at,
        }
        if self.witness:
            d["witness"] = self.witness.to_dict()
        return d

    @property
    def question_count(self) -> int:
        return len(self.questions)


@dataclass
class TranscriptAnalysis:
    """Analysis results from a deposition transcript."""

    transcript_id: str = ""
    witness_name: str = ""
    key_admissions: List[Dict[str, str]] = field(default_factory=list)
    evasions: List[Dict[str, str]] = field(default_factory=list)
    contradictions: List[Dict[str, str]] = field(default_factory=list)
    impeachment_material: List[Dict[str, str]] = field(default_factory=list)
    trial_clips: List[Dict[str, str]] = field(default_factory=list)
    performance_rating: str = "neutral"
    credibility_impact: float = 0.0
    summary: str = ""
    page_count: int = 0
    analyzed_at: str = ""

    def __post_init__(self) -> None:
        if not self.transcript_id:
            self.transcript_id = str(uuid.uuid4())[:12]
        if not self.analyzed_at:
            self.analyzed_at = datetime.now(timezone.utc).isoformat()

    def to_dict(self) -> Dict[str, Any]:
        """Serialise to dictionary."""
        return asdict(self)


# ---------------------------------------------------------------------------
# QuestionBank
# ---------------------------------------------------------------------------

class QuestionBank:
    """Generate and manage deposition questions by category."""

    def __init__(self) -> None:
        self._questions_generated: int = 0

    def generate_direct_questions(
        self,
        witness: WitnessProfile,
        topic: str,
        lane: str = "A",
    ) -> List[DepositionQuestion]:
        """Generate open-ended questions for friendly / fact witnesses."""
        questions: List[DepositionQuestion] = []

        for tmpl in _FOUNDATIONAL_TEMPLATES:
            text = tmpl.format(
                party=_DEFENDANT, child=_CHILD_INITIALS,
                plaintiff=_PLAINTIFF, defendant=_DEFENDANT,
            )
            questions.append(DepositionQuestion(
                text=text,
                category=QuestionCategory.FOUNDATIONAL.value,
                style=QuestionStyle.OPEN.value,
                target_topic="foundational",
                priority=3,
                estimated_minutes=1.0,
            ))

        lane_topics = _LANE_TOPICS.get(lane, {})
        if topic in lane_topics:
            for tmpl in lane_topics[topic]:
                text = tmpl.format(
                    party=_DEFENDANT, defendant=_DEFENDANT,
                    plaintiff=_PLAINTIFF, child=_CHILD_INITIALS,
                    address="1977 Whitehall Road, Lot 17",
                )
                questions.append(DepositionQuestion(
                    text=text,
                    category=QuestionCategory.TIMELINE.value,
                    style=QuestionStyle.OPEN.value,
                    target_topic=topic,
                    priority=5,
                    estimated_minutes=2.0,
                ))

        for tmpl in _DAMAGE_PROOF_TEMPLATES:
            text = tmpl.format(
                event=topic, person=witness.name,
                damage_item="documented losses",
            )
            questions.append(DepositionQuestion(
                text=text,
                category=QuestionCategory.DAMAGE_PROOF.value,
                style=QuestionStyle.OPEN.value,
                target_topic=topic,
                priority=6,
                estimated_minutes=2.5,
            ))

        self._questions_generated += len(questions)
        return questions

    def generate_cross_questions(
        self,
        witness: WitnessProfile,
        topic: str,
        lane: str = "A",
    ) -> List[DepositionQuestion]:
        """Generate leading questions for adverse / hostile witnesses."""
        questions: List[DepositionQuestion] = []

        for tmpl in _ADMISSION_SEEKING_TEMPLATES:
            text = tmpl.format(
                assertion=f"{witness.name} was aware of {topic}",
                fact=f"the {topic} occurred as documented",
                conclusion=f"the evidence supports the {topic} claims",
                action="report such conduct",
            )
            questions.append(DepositionQuestion(
                text=text,
                category=QuestionCategory.ADMISSION_SEEKING.value,
                style=QuestionStyle.LEADING.value,
                target_topic=topic,
                priority=4,
                estimated_minutes=1.5,
            ))

        for tmpl in _CREDIBILITY_TEMPLATES:
            text = tmpl.format(party=_DEFENDANT)
            questions.append(DepositionQuestion(
                text=text,
                category=QuestionCategory.CREDIBILITY.value,
                style=QuestionStyle.LEADING.value,
                target_topic="credibility",
                priority=5,
                estimated_minutes=1.5,
            ))

        lane_topics = _LANE_TOPICS.get(lane, {})
        if topic in lane_topics:
            for tmpl in lane_topics[topic]:
                text = tmpl.format(
                    party=_DEFENDANT, defendant=_DEFENDANT,
                    plaintiff=_PLAINTIFF, child=_CHILD_INITIALS,
                    address="1977 Whitehall Road, Lot 17",
                )
                leading = text.rstrip(".")
                if not leading.endswith("?"):
                    leading = f"Isn't it true that {leading[0].lower()}{leading[1:]}?"
                questions.append(DepositionQuestion(
                    text=leading,
                    category=QuestionCategory.ADMISSION_SEEKING.value,
                    style=QuestionStyle.LEADING.value,
                    target_topic=topic,
                    priority=4,
                    estimated_minutes=1.5,
                ))

        self._questions_generated += len(questions)
        return questions

    def generate_impeachment_sequence(
        self,
        witness: WitnessProfile,
        contradicting_statements: List[Tuple[StatementRecord, StatementRecord]],
    ) -> List[DepositionQuestion]:
        """
        Generate commit → confront → contrast impeachment sequences.

        Per MRE 613, the witness must be given opportunity to explain or deny
        a prior inconsistent statement before extrinsic evidence is offered.
        """
        questions: List[DepositionQuestion] = []

        for current, prior in contradicting_statements:
            seq_id = str(uuid.uuid4())[:6]

            for i, tmpl in enumerate(_IMPEACHMENT_COMMIT):
                text = tmpl.format(current_claim=current.content)
                questions.append(DepositionQuestion(
                    text=text,
                    category=QuestionCategory.IMPEACHMENT.value,
                    style=QuestionStyle.LEADING.value,
                    target_topic="impeachment",
                    priority=2,
                    estimated_minutes=1.0,
                    mcr_basis="MRE 613",
                    notes=f"Commit phase {i+1}/4 (seq {seq_id})",
                ))

            for i, tmpl in enumerate(_IMPEACHMENT_CONFRONT):
                text = tmpl.format(
                    exhibit_ref=prior.exhibit_ref or "the document",
                    source_type=prior.source_type,
                    date=prior.statement_date or "a prior date",
                    prior_statement=prior.content,
                )
                questions.append(DepositionQuestion(
                    text=text,
                    category=QuestionCategory.IMPEACHMENT.value,
                    style=QuestionStyle.LEADING.value,
                    target_topic="impeachment",
                    priority=1,
                    estimated_minutes=1.5,
                    exhibit_needed=prior.exhibit_ref or "",
                    mcr_basis="MRE 613",
                    notes=f"Confront phase {i+1}/4 (seq {seq_id})",
                ))

            for i, tmpl in enumerate(_IMPEACHMENT_CONTRAST):
                text = tmpl.format(
                    current_claim=current.content,
                    prior_statement=prior.content,
                    date=prior.statement_date or "a prior date",
                )
                questions.append(DepositionQuestion(
                    text=text,
                    category=QuestionCategory.IMPEACHMENT.value,
                    style=QuestionStyle.LEADING.value,
                    target_topic="impeachment",
                    priority=1,
                    estimated_minutes=2.0,
                    mcr_basis="MRE 613",
                    notes=f"Contrast phase {i+1}/3 (seq {seq_id})",
                ))

        self._questions_generated += len(questions)
        return questions

    def prioritize_questions(
        self,
        questions: List[DepositionQuestion],
        time_limit_minutes: float = 420.0,  # MCR 2.306(D): 7 hours
    ) -> List[DepositionQuestion]:
        """Rank questions by priority and fit within time limit."""
        sorted_qs = sorted(questions, key=lambda q: (q.priority, -q.estimated_minutes))
        selected: List[DepositionQuestion] = []
        remaining = time_limit_minutes

        for q in sorted_qs:
            if remaining >= q.estimated_minutes:
                selected.append(q)
                remaining -= q.estimated_minutes
            elif remaining > 0:
                selected.append(q)
                remaining = 0

        return selected

    def check_mcr_compliance(
        self, questions: List[DepositionQuestion]
    ) -> Dict[str, Any]:
        """Check question list for MCR 2.306 compliance."""
        total_time = sum(q.estimated_minutes for q in questions)
        has_foundational = any(
            q.category == QuestionCategory.FOUNDATIONAL.value for q in questions
        )
        compound_qs = [
            q for q in questions if q.style == QuestionStyle.COMPOUND.value
        ]
        return {
            "total_estimated_minutes": round(total_time, 1),
            "within_7_hour_limit": total_time <= 420.0,
            "has_foundational_questions": has_foundational,
            "compound_question_count": len(compound_qs),
            "compound_risk": len(compound_qs) > 5,
            "question_count": len(questions),
            "mcr_2_306_d_compliant": total_time <= 420.0,
        }

    @property
    def total_generated(self) -> int:
        return self._questions_generated


# ---------------------------------------------------------------------------
# DepositionPlanner
# ---------------------------------------------------------------------------

class DepositionPlanner:
    """Plan and prepare for depositions."""

    def __init__(self, db_path: Optional[Path] = None) -> None:
        self._db_path = db_path or _DB_PATH
        self._plans_created: int = 0

    def plan_deposition(
        self,
        witness: WitnessProfile,
        case_lane: str,
        objectives: Optional[List[str]] = None,
    ) -> DepositionPlan:
        """Create a full deposition plan for a witness."""
        if objectives is None:
            objectives = self._default_objectives(witness, case_lane)

        qbank = QuestionBank()
        questions: List[DepositionQuestion] = []

        is_adverse = witness.role == WitnessRole.PARTY.value or \
            witness.name == _DEFENDANT

        if is_adverse:
            for topic in _LANE_TOPICS.get(case_lane, {}):
                questions.extend(qbank.generate_cross_questions(witness, topic, case_lane))
        else:
            for topic in _LANE_TOPICS.get(case_lane, {}):
                questions.extend(qbank.generate_direct_questions(witness, topic, case_lane))

        contradictions = self._find_contradictions(witness)
        if contradictions:
            questions.extend(qbank.generate_impeachment_sequence(witness, contradictions))

        questions = qbank.prioritize_questions(questions, 420.0)
        compliance = qbank.check_mcr_compliance(questions)
        duration = self.estimate_duration(len(questions), witness.role)

        plan = DepositionPlan(
            witness=witness,
            case_lane=case_lane,
            objectives=objectives,
            questions=questions,
            estimated_duration_minutes=duration,
            mcr_compliance=compliance,
            status=DepositionStatus.PLANNED.value,
        )

        self._plans_created += 1
        return plan

    def estimate_duration(
        self, question_count: int, witness_type: str = "fact"
    ) -> float:
        """Estimate deposition duration in minutes."""
        base_per_question: Dict[str, float] = {
            WitnessRole.PARTY.value: 3.0,
            WitnessRole.EXPERT.value: 4.0,
            WitnessRole.FACT.value: 2.5,
            WitnessRole.CHARACTER.value: 2.0,
        }
        rate = base_per_question.get(witness_type, 2.5)
        raw = question_count * rate
        # Add 15% for breaks, objections, sidebar
        with_overhead = raw * 1.15
        # Cap at 7 hours per MCR 2.306(D)
        return min(with_overhead, 420.0)

    def generate_notice(
        self,
        witness: WitnessProfile,
        depo_date: date,
        location: str = "14th Circuit Court, Muskegon County, MI",
    ) -> str:
        """Generate MCR 2.306(B) compliant deposition notice."""
        case_lane = witness.lane
        case_number = LANE_CASE_NUMBERS.get(case_lane, "2024-001507-DC")
        lane_label = LANE_LABELS.get(case_lane, "Custody")

        notice = textwrap.dedent(f"""\
        NOTICE OF TAKING DEPOSITION BY ORAL EXAMINATION
        (MCR 2.306)

        STATE OF MICHIGAN
        IN THE 14TH CIRCUIT COURT FOR THE COUNTY OF MUSKEGON

        Case No.: {case_number}
        {lane_label}

        ANDREW JAMES PIGORS,
            Plaintiff (Pro Se),
        v.
        EMILY A. WATSON, et al.,
            Defendant(s).
        ____________________________________________/

        TO: {witness.name}
            c/o [Attorney / Address]

        PLEASE TAKE NOTICE that the Plaintiff, Andrew James Pigors,
        acting Pro Se, will take the deposition by oral examination of
        {witness.name} on:

            Date:     {depo_date.strftime("%B %d, %Y")}
            Time:     10:00 AM
            Location: {location}

        The deposition will be taken before a notary public or other
        officer authorized to administer oaths, and will continue from
        day to day until completed.  The deposition is being taken for
        purposes of discovery, for use at trial, or for such other
        purposes as are permitted under the Michigan Court Rules.

        This deposition is noticed pursuant to MCR 2.306.  The
        examination will be recorded by stenographic means.

        Respectfully submitted,

        ________________________________
        Andrew James Pigors, Pro Se
        [Address]
        [Phone]
        [Email]

        Date: {datetime.now().strftime("%B %d, %Y")}

        CERTIFICATE OF SERVICE

        I certify that on {datetime.now().strftime("%B %d, %Y")}, I served
        a copy of this Notice of Taking Deposition on all parties of record
        by [first-class mail / personal service / e-filing].

        ________________________________
        Andrew James Pigors
        """)
        return notice

    def prepare_exhibits(
        self,
        witness: WitnessProfile,
        relevant_docs: Optional[List[Dict[str, str]]] = None,
    ) -> List[Dict[str, str]]:
        """Compile exhibit list for the deposition."""
        exhibits: List[Dict[str, str]] = []
        exhibit_num = 1

        for stmt in witness.prior_statements:
            if stmt.exhibit_ref or stmt.source_type in ("filing", "affidavit"):
                exhibits.append({
                    "number": str(exhibit_num),
                    "description": f"{stmt.source_type.title()} dated {stmt.statement_date}",
                    "source_ref": stmt.exhibit_ref or stmt.page_ref or "",
                    "purpose": "Impeachment / Prior statement",
                })
                exhibit_num += 1

        if relevant_docs:
            for doc in relevant_docs:
                exhibits.append({
                    "number": str(exhibit_num),
                    "description": doc.get("description", "Document"),
                    "source_ref": doc.get("path", ""),
                    "purpose": doc.get("purpose", "Reference"),
                })
                exhibit_num += 1

        return exhibits

    def identify_objection_risks(
        self, questions: List[DepositionQuestion]
    ) -> List[Dict[str, Any]]:
        """Flag questions likely to draw objections."""
        risks: List[Dict[str, Any]] = []

        compound_pattern = re.compile(r"\band\b.*\?.*\band\b", re.IGNORECASE)
        speculation_pattern = re.compile(
            r"\b(would|could|might|think|believe|feel|speculate)\b", re.IGNORECASE
        )
        legal_conclusion_pattern = re.compile(
            r"\b(legal|liable|negligent|violated|unconstitutional)\b", re.IGNORECASE
        )

        for q in questions:
            risk_types: List[str] = []

            if compound_pattern.search(q.text):
                risk_types.append(ObjectionType.COMPOUND.value)
            if speculation_pattern.search(q.text) and q.style == QuestionStyle.OPEN.value:
                risk_types.append(ObjectionType.CALLS_FOR_SPECULATION.value)
            if legal_conclusion_pattern.search(q.text):
                risk_types.append(ObjectionType.CALLS_FOR_LEGAL_CONCLUSION.value)
            if q.text.count("?") > 1:
                risk_types.append(ObjectionType.COMPOUND.value)
            if len(q.text) > 300:
                risk_types.append(ObjectionType.VAGUE.value)

            if risk_types:
                risks.append({
                    "question_id": q.question_id,
                    "question_text": q.text[:200],
                    "risk_types": list(set(risk_types)),
                    "severity": "high" if len(risk_types) > 1 else "moderate",
                    "suggestion": self._suggest_fix(risk_types),
                })

        return risks

    def _default_objectives(
        self, witness: WitnessProfile, lane: str
    ) -> List[str]:
        """Generate default deposition objectives based on lane."""
        base = [
            "Establish factual foundation for claims",
            "Lock in testimony for trial",
            "Identify documents and evidence",
        ]
        lane_objectives: Dict[str, List[str]] = {
            "A": [
                "Document custody interference incidents",
                "Establish best-interest-of-child factors (MCL 722.23)",
                "Identify ex parte contacts with court",
            ],
            "B": [
                "Document habitability deficiencies",
                "Establish discriminatory treatment",
                "Identify responsible parties",
            ],
            "D": [
                "Challenge factual basis of PPO petition",
                "Document impact on parenting time",
                "Establish lack of credible threat",
            ],
            "E": [
                "Document judicial bias indicators",
                "Identify ex parte communications",
                "Establish pattern of due process violations",
            ],
            "F": [
                "Preserve trial court errors for appeal",
                "Document prejudice from lower court rulings",
            ],
        }
        return base + lane_objectives.get(lane, [])

    def _find_contradictions(
        self, witness: WitnessProfile
    ) -> List[Tuple[StatementRecord, StatementRecord]]:
        """Find contradicting statement pairs for a witness."""
        pairs: List[Tuple[StatementRecord, StatementRecord]] = []
        statements = witness.prior_statements

        for i, s1 in enumerate(statements):
            for s2 in statements[i + 1:]:
                if s2.statement_id in s1.contradicts or \
                   s1.statement_id in s2.contradicts:
                    pairs.append((s1, s2))

        return pairs

    @staticmethod
    def _suggest_fix(risk_types: List[str]) -> str:
        """Suggest how to fix an objectionable question."""
        fixes = []
        if ObjectionType.COMPOUND.value in risk_types:
            fixes.append("Break into separate single-fact questions.")
        if ObjectionType.CALLS_FOR_SPECULATION.value in risk_types:
            fixes.append("Ask about personal knowledge only.")
        if ObjectionType.CALLS_FOR_LEGAL_CONCLUSION.value in risk_types:
            fixes.append("Reframe to ask about facts, not legal conclusions.")
        if ObjectionType.VAGUE.value in risk_types:
            fixes.append("Shorten and clarify the question.")
        return " ".join(fixes) if fixes else "Review for form issues."


# ---------------------------------------------------------------------------
# DepositionAnalyzer
# ---------------------------------------------------------------------------

class DepositionAnalyzer:
    """Analyze deposition transcripts for key testimony and contradictions."""

    _ADMISSION_PATTERNS: List[re.Pattern[str]] = [
        re.compile(r"\b(yes|correct|that's right|I agree|I admit|I acknowledge)\b", re.I),
    ]
    _EVASION_PATTERNS: List[re.Pattern[str]] = [
        re.compile(r"\b(I don't recall|I don't remember|I'm not sure|I can't say)\b", re.I),
        re.compile(r"\b(I don't know|possibly|maybe|it depends)\b", re.I),
        re.compile(r"\b(I'd have to check|I need to look|that's not how I'd put it)\b", re.I),
    ]
    _OBJECTION_PATTERN = re.compile(
        r"^(MR\.|MS\.|MRS\.|COUNSEL).*:\s*Objection", re.MULTILINE | re.IGNORECASE
    )

    def __init__(self) -> None:
        self._analyses_completed: int = 0

    def analyze_transcript(
        self, transcript_text: str
    ) -> TranscriptAnalysis:
        """Extract key testimony, admissions, and evasions from transcript."""
        analysis = TranscriptAnalysis(
            page_count=self._estimate_pages(transcript_text),
        )

        lines = transcript_text.split("\n")
        current_speaker = ""
        current_block: List[str] = []

        for line_num, line in enumerate(lines, 1):
            speaker_match = re.match(r"^([A-Z][A-Z\s.]+):\s*(.*)", line.strip())
            if speaker_match:
                if current_speaker and current_block:
                    self._analyze_block(
                        analysis, current_speaker, " ".join(current_block),
                        line_num - len(current_block),
                    )
                current_speaker = speaker_match.group(1).strip()
                current_block = [speaker_match.group(2)]
            elif line.strip():
                current_block.append(line.strip())

        if current_speaker and current_block:
            self._analyze_block(
                analysis, current_speaker, " ".join(current_block),
                len(lines),
            )

        self._analyses_completed += 1
        return analysis

    def score_witness_performance(
        self, analysis: TranscriptAnalysis
    ) -> Dict[str, Any]:
        """Assess credibility impact of witness performance."""
        admission_count = len(analysis.key_admissions)
        evasion_count = len(analysis.evasions)
        contradiction_count = len(analysis.contradictions)

        score = 50.0  # Neutral baseline
        score -= admission_count * 5.0
        score -= evasion_count * 3.0
        score -= contradiction_count * 10.0

        if admission_count == 0 and evasion_count < 3:
            score += 15.0

        score = max(0.0, min(100.0, score))

        if score >= 80:
            rating = PerformanceRating.EXCELLENT.value
        elif score >= 60:
            rating = PerformanceRating.GOOD.value
        elif score >= 40:
            rating = PerformanceRating.NEUTRAL.value
        elif score >= 20:
            rating = PerformanceRating.POOR.value
        else:
            rating = PerformanceRating.DEVASTATING.value

        analysis.performance_rating = rating
        analysis.credibility_impact = score - 50.0

        return {
            "score": round(score, 1),
            "rating": rating,
            "credibility_impact": round(score - 50.0, 1),
            "admissions": admission_count,
            "evasions": evasion_count,
            "contradictions": contradiction_count,
        }

    def extract_impeachment_material(
        self, analysis: TranscriptAnalysis
    ) -> List[Dict[str, str]]:
        """Extract statements usable for impeachment at trial per MCR 2.308."""
        material: List[Dict[str, str]] = []

        for admission in analysis.key_admissions:
            material.append({
                "type": "admission",
                "content": admission.get("content", ""),
                "page_ref": admission.get("page_ref", ""),
                "trial_use": "MCR 2.308(A)(2) — Admission by party-opponent",
                "impeachment_value": "high",
            })

        for contradiction in analysis.contradictions:
            material.append({
                "type": "contradiction",
                "content": contradiction.get("content", ""),
                "page_ref": contradiction.get("page_ref", ""),
                "trial_use": "MRE 613 — Prior inconsistent statement",
                "impeachment_value": "critical",
            })

        analysis.impeachment_material = material
        return material

    def compare_to_prior_statements(
        self,
        transcript_text: str,
        prior_statements: List[StatementRecord],
    ) -> List[Dict[str, Any]]:
        """Detect contradictions between transcript and prior statements."""
        contradictions: List[Dict[str, Any]] = []
        transcript_lower = transcript_text.lower()

        for stmt in prior_statements:
            content_lower = stmt.content.lower()
            key_phrases = [
                p.strip() for p in content_lower.split(".")
                if len(p.strip()) > 20
            ]

            for phrase in key_phrases:
                negated = self._negate_phrase(phrase)
                if negated and negated in transcript_lower:
                    idx = transcript_lower.index(negated)
                    context_start = max(0, idx - 100)
                    context_end = min(len(transcript_text), idx + len(negated) + 100)

                    contradictions.append({
                        "prior_statement_id": stmt.statement_id,
                        "prior_content": stmt.content[:200],
                        "prior_source": stmt.source_type,
                        "prior_date": stmt.statement_date,
                        "transcript_context": transcript_text[context_start:context_end],
                        "severity": "high",
                        "impeachment_ready": True,
                    })

        return contradictions

    def generate_summary(
        self,
        analysis: TranscriptAnalysis,
        key_topics: Optional[List[str]] = None,
    ) -> str:
        """Generate structured summary with page references."""
        sections: List[str] = []
        sections.append(f"DEPOSITION SUMMARY — {analysis.witness_name}")
        sections.append(f"{'=' * 60}")
        sections.append(f"Date Analyzed: {analysis.analyzed_at}")
        sections.append(f"Pages: {analysis.page_count}")
        sections.append(f"Performance: {analysis.performance_rating}")
        sections.append("")

        if analysis.key_admissions:
            sections.append("KEY ADMISSIONS:")
            for i, adm in enumerate(analysis.key_admissions, 1):
                sections.append(
                    f"  {i}. {adm.get('content', '')[:150]} "
                    f"(p. {adm.get('page_ref', '?')})"
                )
            sections.append("")

        if analysis.evasions:
            sections.append("EVASIONS / NON-ANSWERS:")
            for i, ev in enumerate(analysis.evasions, 1):
                sections.append(
                    f"  {i}. {ev.get('content', '')[:150]} "
                    f"(p. {ev.get('page_ref', '?')})"
                )
            sections.append("")

        if analysis.contradictions:
            sections.append("CONTRADICTIONS:")
            for i, ct in enumerate(analysis.contradictions, 1):
                sections.append(
                    f"  {i}. {ct.get('content', '')[:150]} "
                    f"(p. {ct.get('page_ref', '?')})"
                )
            sections.append("")

        if analysis.impeachment_material:
            sections.append(f"IMPEACHMENT MATERIAL: {len(analysis.impeachment_material)} items")
            sections.append("")

        if key_topics:
            sections.append("TOPIC COVERAGE:")
            for topic in key_topics:
                sections.append(f"  • {topic}")
            sections.append("")

        return "\n".join(sections)

    def identify_trial_clips(
        self, transcript_text: str, analysis: TranscriptAnalysis
    ) -> List[Dict[str, str]]:
        """Identify best segments for trial presentation per MCR 2.308."""
        clips: List[Dict[str, str]] = []

        for admission in analysis.key_admissions:
            clips.append({
                "type": "admission_clip",
                "content": admission.get("content", ""),
                "page_ref": admission.get("page_ref", ""),
                "trial_rule": "MCR 2.308(A)(2)",
                "purpose": "Party admission — admissible as substantive evidence",
                "priority": "high",
            })

        for contradiction in analysis.contradictions:
            clips.append({
                "type": "impeachment_clip",
                "content": contradiction.get("content", ""),
                "page_ref": contradiction.get("page_ref", ""),
                "trial_rule": "MCR 2.308(A)(1) / MRE 613",
                "purpose": "Impeachment — prior inconsistent statement",
                "priority": "critical",
            })

        analysis.trial_clips = clips
        return clips

    def _analyze_block(
        self,
        analysis: TranscriptAnalysis,
        speaker: str,
        content: str,
        approx_line: int,
    ) -> None:
        """Analyze a speaker block for admissions, evasions, etc."""
        page_ref = str(max(1, approx_line // 25))

        for pattern in self._ADMISSION_PATTERNS:
            if pattern.search(content):
                analysis.key_admissions.append({
                    "speaker": speaker,
                    "content": content[:300],
                    "page_ref": page_ref,
                    "type": "admission",
                })
                break

        for pattern in self._EVASION_PATTERNS:
            if pattern.search(content):
                analysis.evasions.append({
                    "speaker": speaker,
                    "content": content[:300],
                    "page_ref": page_ref,
                    "type": "evasion",
                })
                break

    @staticmethod
    def _estimate_pages(text: str) -> int:
        """Estimate transcript pages (25 lines per page standard)."""
        line_count = text.count("\n") + 1
        return max(1, line_count // 25)

    @staticmethod
    def _negate_phrase(phrase: str) -> Optional[str]:
        """Simple negation of a phrase for contradiction detection."""
        replacements = [
            ("did ", "did not "), ("was ", "was not "),
            ("is ", "is not "), ("has ", "has not "),
            ("can ", "cannot "), ("will ", "will not "),
            ("are ", "are not "), ("were ", "were not "),
        ]
        for pos, neg in replacements:
            if pos in phrase and neg not in phrase:
                return phrase.replace(pos, neg, 1)
        return None


# ---------------------------------------------------------------------------
# DepositionStrategist (Main Orchestrator)
# ---------------------------------------------------------------------------

class DepositionStrategist:
    """
    Main orchestrator for deposition preparation and analysis.

    Integrates WitnessProfile, QuestionBank, DepositionPlanner,
    and DepositionAnalyzer into a unified workflow.
    """

    VERSION = "1.0.0"

    def __init__(self, db_path: Optional[Path] = None) -> None:
        self._db_path = db_path or _DB_PATH
        self._question_bank = QuestionBank()
        self._planner = DepositionPlanner(db_path=self._db_path)
        self._analyzer = DepositionAnalyzer()
        self._witnesses: Dict[str, WitnessProfile] = {}
        self._plans: Dict[str, DepositionPlan] = {}
        self._analyses: Dict[str, TranscriptAnalysis] = {}
        self._initialized = False

    def _ensure_db(self) -> None:
        """Initialise database tables on first use."""
        if self._initialized:
            return
        if not self._db_path.exists():
            logger.warning("DB not found at %s — running in memory-only mode", self._db_path)
            self._initialized = True
            return
        try:
            conn = _connect(self._db_path)
            _ensure_tables(conn)
            conn.close()
            self._initialized = True
        except sqlite3.Error as exc:
            logger.error("DB init failed: %s", exc)
            self._initialized = True

    # -- Witness Management ------------------------------------------------

    def build_witness_database(self) -> Dict[str, Any]:
        """Scan DB for all known witnesses and build profiles."""
        self._ensure_db()
        loaded = 0

        known_witnesses = [
            (_DEFENDANT, WitnessRole.PARTY.value, "Defendant / opposing party", "A"),
            ("Pamela Rusco", WitnessRole.EXPERT.value, "Court-appointed mediator", "A"),
            (_JUDGE, WitnessRole.FACT.value, "Presiding judge — misconduct target", "E"),
            ("Friend of Court Officer", WitnessRole.FACT.value, "FOC representative", "A"),
            ("CPS Investigator", WitnessRole.FACT.value, "CPS case worker", "A"),
        ]

        for name, role, relationship, lane in known_witnesses:
            wp = WitnessProfile(
                name=name, role=role,
                relationship_to_case=relationship, lane=lane,
            )
            self._witnesses[wp.witness_id] = wp
            loaded += 1

        if self._db_path.exists():
            try:
                conn = _connect(self._db_path)
                if _table_exists(conn, "witness_profiles"):
                    rows = conn.execute(
                        "SELECT * FROM witness_profiles"
                    ).fetchall()
                    for row in rows:
                        wp = WitnessProfile.from_db(row)
                        self._witnesses[wp.witness_id] = wp
                        loaded += 1
                conn.close()
            except sqlite3.Error as exc:
                logger.error("Error loading witnesses from DB: %s", exc)

        return {
            "witnesses_loaded": loaded,
            "total_witnesses": len(self._witnesses),
        }

    def get_witness(self, name: str) -> Optional[WitnessProfile]:
        """Look up a witness by name (case-insensitive partial match)."""
        name_lower = name.lower()
        for wp in self._witnesses.values():
            if name_lower in wp.name.lower():
                return wp
        return None

    def add_witness(self, profile: WitnessProfile) -> str:
        """Add a witness profile to the database."""
        self._ensure_db()
        self._witnesses[profile.witness_id] = profile

        if self._db_path.exists():
            try:
                conn = _connect(self._db_path)
                _ensure_tables(conn)
                now = datetime.now(timezone.utc).isoformat()
                conn.execute(
                    "INSERT OR REPLACE INTO witness_profiles "
                    "(id, name, role, relationship, lane, credibility_score, "
                    "known_biases_json, prior_statements_json, deposition_count, "
                    "notes, created_at, updated_at) "
                    "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
                    (
                        profile.witness_id, profile.name, profile.role,
                        profile.relationship_to_case, profile.lane,
                        profile.credibility_score,
                        json.dumps(profile.known_biases),
                        json.dumps([s.to_dict() for s in profile.prior_statements]),
                        len(profile.deposition_history),
                        profile.notes, now, now,
                    ),
                )
                conn.commit()
                conn.close()
            except sqlite3.Error as exc:
                logger.error("Error saving witness: %s", exc)

        return profile.witness_id

    # -- Deposition Preparation --------------------------------------------

    def prepare_full_deposition(
        self,
        witness_name: str,
        case_lane: str,
        objectives: Optional[List[str]] = None,
    ) -> DepositionPlan:
        """End-to-end deposition preparation for a named witness."""
        self._ensure_db()

        if not self._witnesses:
            self.build_witness_database()

        witness = self.get_witness(witness_name)
        if witness is None:
            witness = WitnessProfile(
                name=witness_name,
                role=WitnessRole.FACT.value,
                lane=case_lane,
            )
            self._witnesses[witness.witness_id] = witness

        plan = self._planner.plan_deposition(witness, case_lane, objectives)
        plan.exhibit_list = self._planner.prepare_exhibits(witness)

        objection_risks = self._planner.identify_objection_risks(plan.questions)
        if objection_risks:
            plan.mcr_compliance["objection_risks"] = len(objection_risks)  # type: ignore[assignment]

        self._plans[plan.plan_id] = plan
        self._save_plan(plan)

        return plan

    def analyze_deposition_transcript(
        self,
        witness_name: str,
        transcript_text: str,
        key_topics: Optional[List[str]] = None,
    ) -> TranscriptAnalysis:
        """Analyze a completed deposition transcript."""
        analysis = self._analyzer.analyze_transcript(transcript_text)
        analysis.witness_name = witness_name

        self._analyzer.score_witness_performance(analysis)
        self._analyzer.extract_impeachment_material(analysis)
        self._analyzer.identify_trial_clips(transcript_text, analysis)

        witness = self.get_witness(witness_name)
        if witness:
            prior_contradictions = self._analyzer.compare_to_prior_statements(
                transcript_text, witness.prior_statements,
            )
            for pc in prior_contradictions:
                analysis.contradictions.append({
                    "content": pc.get("transcript_context", "")[:200],
                    "page_ref": "cross-ref",
                    "type": "prior_statement_contradiction",
                    "prior_source": pc.get("prior_source", ""),
                })

        analysis.summary = self._analyzer.generate_summary(analysis, key_topics)

        self._analyses[analysis.transcript_id] = analysis
        self._save_analysis(analysis)

        return analysis

    # -- Persistence -------------------------------------------------------

    def _save_plan(self, plan: DepositionPlan) -> None:
        """Persist a deposition plan to the database."""
        if not self._db_path.exists():
            return
        try:
            conn = _connect(self._db_path)
            _ensure_tables(conn)
            now = datetime.now(timezone.utc).isoformat()
            witness_name = plan.witness.name if plan.witness else "Unknown"
            witness_role = plan.witness.role if plan.witness else "fact"
            conn.execute(
                "INSERT OR REPLACE INTO deposition_prep "
                "(id, witness_name, witness_role, case_lane, case_number, "
                "status, objectives_json, questions_json, plan_json, "
                "question_count, created_at, updated_at) "
                "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
                (
                    plan.plan_id, witness_name, witness_role,
                    plan.case_lane,
                    LANE_CASE_NUMBERS.get(plan.case_lane, ""),
                    plan.status,
                    json.dumps(plan.objectives),
                    json.dumps([q.to_dict() for q in plan.questions]),
                    json.dumps(plan.to_dict()),
                    plan.question_count,
                    plan.created_at, now,
                ),
            )
            conn.commit()
            conn.close()
        except sqlite3.Error as exc:
            logger.error("Error saving plan: %s", exc)

    def _save_analysis(self, analysis: TranscriptAnalysis) -> None:
        """Persist transcript analysis to the database."""
        if not self._db_path.exists():
            return
        try:
            conn = _connect(self._db_path)
            _ensure_tables(conn)
            now = datetime.now(timezone.utc).isoformat()
            conn.execute(
                "INSERT OR REPLACE INTO deposition_prep "
                "(id, witness_name, witness_role, case_lane, status, "
                "analysis_json, created_at, updated_at) "
                "VALUES (?, ?, 'fact', 'A', 'analyzed', ?, ?, ?)",
                (
                    f"analysis_{analysis.transcript_id}",
                    analysis.witness_name,
                    json.dumps(analysis.to_dict()),
                    now, now,
                ),
            )
            conn.commit()
            conn.close()
        except sqlite3.Error as exc:
            logger.error("Error saving analysis: %s", exc)

    # -- Statistics ---------------------------------------------------------

    def get_stats(self) -> Dict[str, Any]:
        """Return engine statistics."""
        return {
            "engine": "DepositionStrategist",
            "version": self.VERSION,
            "db_path": str(self._db_path),
            "db_exists": self._db_path.exists(),
            "witness_count": len(self._witnesses),
            "plans_created": len(self._plans),
            "analyses_completed": len(self._analyses),
            "questions_generated": self._question_bank.total_generated,
            "total_contradictions": sum(
                w.get_contradiction_count() for w in self._witnesses.values()
            ),
            "lanes_covered": list({
                p.case_lane for p in self._plans.values()
            }),
            "case_context": {
                "plaintiff": _PLAINTIFF,
                "defendant": _DEFENDANT,
                "child": _CHILD_INITIALS,
                "judge": _JUDGE,
            },
        }

    def generate_status_report(self) -> str:
        """Generate a human-readable status report."""
        stats = self.get_stats()
        lines = [
            "DEPOSITION STRATEGIST — STATUS REPORT",
            "=" * 50,
            f"Witnesses tracked:    {stats['witness_count']}",
            f"Plans created:        {stats['plans_created']}",
            f"Analyses completed:   {stats['analyses_completed']}",
            f"Questions generated:  {stats['questions_generated']}",
            f"Total contradictions: {stats['total_contradictions']}",
            f"Lanes covered:        {', '.join(stats['lanes_covered']) or 'none'}",
            "",
            "WITNESSES:",
        ]
        for wp in self._witnesses.values():
            lines.append(
                f"  • {wp.name} ({wp.role}) — Lane {wp.lane}, "
                f"credibility: {wp.credibility_score:.0f}/100"
            )
        return "\n".join(lines)


# ---------------------------------------------------------------------------
# __main__ demo
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    import sys
    sys.stdout = open(sys.stdout.fileno(), mode="w", encoding="utf-8", errors="replace")

    logging.basicConfig(level=logging.INFO, format="%(name)s %(levelname)s: %(message)s")

    print("=" * 60)
    print("DepositionStrategist — Demo")
    print("=" * 60)

    engine = DepositionStrategist()

    # Build witness database
    result = engine.build_witness_database()
    print(f"\nWitnesses loaded: {result['witnesses_loaded']}")

    # Prepare deposition for defendant
    plan = engine.prepare_full_deposition(_DEFENDANT, "A")
    print(f"\nDeposition Plan for {_DEFENDANT}:")
    print(f"  Questions:  {plan.question_count}")
    print(f"  Duration:   {plan.estimated_duration_minutes:.0f} min")
    print(f"  Status:     {plan.status}")
    print(f"  Lane:       {plan.case_lane} ({LANE_LABELS.get(plan.case_lane, '')})")
    print(f"  Compliant:  {plan.mcr_compliance.get('mcr_2_306_d_compliant', 'N/A')}")

    # Demo transcript analysis
    sample_transcript = textwrap.dedent("""\
    Q: Please state your name for the record.
    A: Emily Watson.
    Q: Ms. Watson, did you deny Mr. Pigors parenting time on March 15, 2024?
    A: I don't recall the specific date.
    Q: Isn't it true that you refused to allow the child to go with his father?
    A: I had concerns about safety.
    Q: What safety concerns specifically?
    A: I'm not sure I can say exactly.
    Q: Do you recall filing the PPO petition?
    A: Yes, I do.
    Q: And in that petition you stated the child was in danger, correct?
    A: Yes, that's right.
    """)

    analysis = engine.analyze_deposition_transcript(
        _DEFENDANT, sample_transcript,
        key_topics=["custody_interference", "ppo_basis"],
    )
    print(f"\nTranscript Analysis:")
    print(f"  Admissions:  {len(analysis.key_admissions)}")
    print(f"  Evasions:    {len(analysis.evasions)}")
    print(f"  Performance: {analysis.performance_rating}")
    print(f"  Impeachment: {len(analysis.impeachment_material)} items")

    # Print stats
    print(f"\n{'-' * 40}")
    stats = engine.get_stats()
    for key, val in stats.items():
        if key != "case_context":
            print(f"  {key}: {val}")

    print(f"\n{engine.generate_status_report()}")
    print("\nDone.")
