"""Pattern mining engine for LitigationOS.

Mines litigation patterns from judge behaviour, opposing-counsel tactics,
filing outcomes, evidence effectiveness, and temporal clustering across
all six case lanes (A-F) of Pigors v. Watson.

Stdlib-only.  Zero external dependencies.
"""

from __future__ import annotations

import hashlib
import json
import logging
import math
import re
import sqlite3
import statistics
from collections import Counter, defaultdict
from dataclasses import asdict, dataclass, field
from datetime import datetime, timedelta, timezone
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple

logger = logging.getLogger("legal_ai.pattern_mining")

# ── Path resolution ──────────────────────────────────────────────────
_HERE = Path(__file__).resolve().parent
_DB_PATH = _HERE.parents[1] / "litigation_context.db"

# ── Case constants ───────────────────────────────────────────────────

_PLAINTIFF = "Andrew James Pigors"
_DEFENDANT = "Emily A. Watson"
_CHILD = "L.D.W."
_JUDGE = "Hon. Jenny L. McNeill"

_LANES: Dict[str, Dict[str, str]] = {
    "A": {"name": "Custody", "case": "2024-001507-DC", "court": "14th Circuit"},
    "B": {"name": "Housing", "case": "2025-002760-CZ", "court": "14th Circuit"},
    "C": {"name": "Convergence", "case": "Multi-lane", "court": "Multiple"},
    "D": {"name": "PPO", "case": "2023-5907-PP", "court": "14th Circuit"},
    "E": {"name": "Misconduct/JTC", "case": "2024-001507-DC", "court": "JTC/AGC"},
    "F": {"name": "Appellate", "case": "COA 366810", "court": "Michigan COA"},
}

_LANE_COLOURS: Dict[str, str] = {
    "A": "#3b82f6",   # blue
    "B": "#22c55e",   # green
    "C": "#a855f7",   # purple
    "D": "#f97316",   # orange
    "E": "#ef4444",   # red
    "F": "#06b6d4",   # teal
}


# ── Enumerations ─────────────────────────────────────────────────────

class PatternCategory(str, Enum):
    """Categories of mined patterns."""
    JUDICIAL = "judicial"
    ADVERSARY = "adversary"
    OUTCOME = "outcome"
    EVIDENCE = "evidence"
    PROCEDURAL = "procedural"
    TEMPORAL = "temporal"


class Confidence(str, Enum):
    """Qualitative confidence tiers."""
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    SPECULATIVE = "speculative"


# ── Confidence thresholds ────────────────────────────────────────────
_CONF_HIGH = 0.80
_CONF_MEDIUM = 0.55
_CONF_LOW = 0.30


def _confidence_tier(score: float) -> str:
    """Map a 0-1 float to a qualitative tier label."""
    if score >= _CONF_HIGH:
        return Confidence.HIGH.value
    if score >= _CONF_MEDIUM:
        return Confidence.MEDIUM.value
    if score >= _CONF_LOW:
        return Confidence.LOW.value
    return Confidence.SPECULATIVE.value


# ── Dataclasses ──────────────────────────────────────────────────────

@dataclass
class Pattern:
    """A single mined litigation pattern."""

    pattern_id: str
    category: str       # PatternCategory value
    title: str
    description: str
    confidence: float   # 0-1
    frequency: int      # times observed
    evidence_refs: List[str] = field(default_factory=list)
    implications: List[str] = field(default_factory=list)
    actionable: bool = False
    actions: List[str] = field(default_factory=list)
    lane: str = ""
    detected_at: str = field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )

    def to_dict(self) -> Dict[str, Any]:
        """Serialise to a plain dictionary."""
        return asdict(self)

    @property
    def confidence_tier(self) -> str:
        return _confidence_tier(self.confidence)


@dataclass
class PatternReport:
    """Aggregate report produced by :class:`PatternMiner`."""

    generated_at: str = field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )
    total_patterns: int = 0
    high_confidence_count: int = 0
    patterns_by_category: Dict[str, List[Pattern]] = field(default_factory=dict)
    top_actionable: List[Pattern] = field(default_factory=list)
    cross_lane_patterns: List[Pattern] = field(default_factory=list)
    temporal_clusters: List[Dict[str, Any]] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        d: Dict[str, Any] = {
            "generated_at": self.generated_at,
            "total_patterns": self.total_patterns,
            "high_confidence_count": self.high_confidence_count,
            "patterns_by_category": {
                cat: [p.to_dict() for p in pats]
                for cat, pats in self.patterns_by_category.items()
            },
            "top_actionable": [p.to_dict() for p in self.top_actionable],
            "cross_lane_patterns": [p.to_dict() for p in self.cross_lane_patterns],
            "temporal_clusters": list(self.temporal_clusters),
        }
        return d


# ── Embedded domain knowledge ────────────────────────────────────────
# Hard-coded patterns from case analysis (verified by Andrew).  These
# are the *seed* patterns that mine_* methods augment with DB data.

_SEED_JUDICIAL_PATTERNS: List[Dict[str, Any]] = [
    {
        "id": "JUD-001",
        "title": "Abnormal ex parte order frequency",
        "description": (
            "Judge McNeill issues ex parte orders at 18.26% of filings — "
            "3.65× the Michigan statewide average of ~5%.  This dispropor"
            "tionate rate indicates systematic favouring of emergency "
            "motions filed by the mother over due-process protections."
        ),
        "confidence": 0.92,
        "frequency": 23,
        "evidence": [
            "Case docket 2024-001507-DC",
            "Michigan SCAO ex parte statistics 2023",
            "MCR 3.207(B) emergency motion log",
        ],
        "implications": [
            "Father's due-process rights are systematically curtailed",
            "Supports MCR 2.003 disqualification motion",
            "Supports JTC complaint for pattern of bias",
        ],
        "actionable": True,
        "actions": [
            "Include in MCR 2.003 disqualification brief",
            "Cite in JTC complaint as statistical evidence",
            "Raise at oral argument if hearing granted",
        ],
    },
    {
        "id": "JUD-002",
        "title": "Asymmetric motion processing times",
        "description": (
            "Motions filed by the mother receive rulings in an average of "
            "3.2 days.  Father's motions average 18.7 days to ruling — "
            "5.8× slower.  Several father motions remain pending beyond "
            "the 14-day decision window required by MCR."
        ),
        "confidence": 0.88,
        "frequency": 14,
        "evidence": [
            "Docket timestamps 2024-001507-DC",
            "MCR 2.002(B)(3) timeliness requirement",
        ],
        "implications": [
            "Pattern of delay constitutes de facto denial",
            "MCR timeliness violation supports disqualification",
        ],
        "actionable": True,
        "actions": [
            "Chart filing-to-ruling timelines in brief",
            "File motion to compel timely ruling",
        ],
    },
    {
        "id": "JUD-003",
        "title": "Emergency motions → immediate ex parte orders",
        "description": (
            "When the mother files an emergency motion, Judge McNeill "
            "enters an ex parte order within 24-48 hours in 87% of cases, "
            "often without requiring an affidavit of specific facts as "
            "required by MCR 3.207(B)."
        ),
        "confidence": 0.85,
        "frequency": 8,
        "evidence": [
            "Emergency motion filings vs order dates",
            "MCR 3.207(B) affidavit requirement",
        ],
        "implications": [
            "Mother has learned to weaponise emergency procedure",
            "Father faces custody changes without notice or hearing",
        ],
        "actionable": True,
        "actions": [
            "Document every ex parte order missing affidavit",
            "Raise due-process violation in COA brief",
        ],
    },
    {
        "id": "JUD-004",
        "title": "Father's motions denied after delayed hearing",
        "description": (
            "Father's substantive motions follow a pattern: file → no "
            "timely hearing → delayed scheduling → eventual denial with "
            "minimal reasoning.  Denial rate on father's motions is ~78% "
            "compared to ~22% for mother's motions."
        ),
        "confidence": 0.82,
        "frequency": 11,
        "evidence": [
            "Docket entries 2024-001507-DC",
            "Motion outcome tracker spreadsheet",
        ],
        "implications": [
            "Demonstrates outcome-determinative bias",
            "Supports argument that hearing is futile without recusal",
        ],
        "actionable": True,
        "actions": [
            "Build motion-outcome comparison chart",
            "Include in COA appeal brief as exhibit",
        ],
    },
]

_SEED_ADVERSARY_PATTERNS: List[Dict[str, Any]] = [
    {
        "id": "ADV-001",
        "title": "Strategic holiday/weekend filings",
        "description": (
            "Opposing party files emergency motions on Fridays and before "
            "major holidays (Thanksgiving, Christmas, spring break) when "
            "the court clerk is less available and father has reduced "
            "ability to respond.  8 of 12 emergency filings occurred "
            "within 2 business days of a holiday or weekend."
        ),
        "confidence": 0.79,
        "frequency": 8,
        "evidence": [
            "Filing date correlation with holiday calendar",
            "Court clerk availability records",
        ],
        "implications": [
            "Calculated to maximise ex parte advantage",
            "Pattern of bad-faith litigation conduct",
        ],
        "actionable": True,
        "actions": [
            "Document in sanctions motion under MCR 1.109(E)",
            "Pre-emptively file protective motions before holidays",
        ],
    },
    {
        "id": "ADV-002",
        "title": "PPO weaponisation cycle",
        "description": (
            "Opposing party invokes PPO as leverage during custody "
            "disputes.  Timeline: (1) father files custody motion → "
            "(2) mother alleges PPO violation within 7 days → "
            "(3) police/court intervention disrupts father's motion. "
            "Pattern repeated 5 times."
        ),
        "confidence": 0.84,
        "frequency": 5,
        "evidence": [
            "PPO violation allegations vs custody motion dates",
            "Police report filing dates",
            "Case 2023-5907-PP docket",
        ],
        "implications": [
            "PPO used as tactical weapon, not safety measure",
            "Supports PPO modification or termination motion",
        ],
        "actionable": True,
        "actions": [
            "File motion to terminate/modify PPO with timeline evidence",
            "Include in abuse-of-process argument",
        ],
    },
    {
        "id": "ADV-003",
        "title": "Parenting time interference escalation",
        "description": (
            "305 documented parenting-time interference incidents.  "
            "Interference intensity escalates after father files motions "
            "or seeks court intervention.  AppClose messages document "
            "refusals and unilateral schedule changes."
        ),
        "confidence": 0.91,
        "frequency": 305,
        "evidence": [
            "AppClose communication logs",
            "Parenting time interference log",
            "Police reports",
        ],
        "implications": [
            "Establishes pattern of contempt",
            "Supports custody modification under best-interest factors",
            "MCL 722.23(j) — willingness to facilitate relationship",
        ],
        "actionable": True,
        "actions": [
            "File motion for show cause / contempt",
            "Use in custody modification brief factor (j)",
        ],
    },
    {
        "id": "ADV-004",
        "title": "CPS/police report retaliation",
        "description": (
            "After father reported bruising concerns to CPS, opposing "
            "party filed retaliatory police reports and additional PPO "
            "allegations within 72 hours.  Pattern suggests punitive "
            "response to legitimate welfare concerns."
        ),
        "confidence": 0.76,
        "frequency": 3,
        "evidence": [
            "CPS report dates vs police report dates",
            "PPO modification filings timeline",
        ],
        "implications": [
            "Chilling effect on father's ability to report safety concerns",
            "Supports argument of abusive litigation tactics",
        ],
        "actionable": True,
        "actions": [
            "Document timeline in brief",
            "Argue retaliation in custody factor analysis",
        ],
    },
]

_SEED_OUTCOME_PATTERNS: List[Dict[str, Any]] = [
    {
        "id": "OUT-001",
        "title": "Motion type success rate disparity",
        "description": (
            "Emergency motions filed by mother: ~88% granted.  "
            "Substantive motions by father: ~22% granted.  "
            "Procedural motions (adjournments, extensions) by either: "
            "~65% granted.  Pattern shows outcome depends more on "
            "which party files than on the merit of the motion."
        ),
        "confidence": 0.86,
        "frequency": 30,
        "evidence": [
            "Motion outcome tracker",
            "Docket analysis 2024-001507-DC",
        ],
        "implications": [
            "Statistical evidence of bias in adjudication",
            "Strengthens disqualification and appellate arguments",
        ],
        "actionable": True,
        "actions": [
            "Create comparative outcome chart for brief",
            "Include in COA appeal fact section",
        ],
    },
    {
        "id": "OUT-002",
        "title": "Multi-court filing impact",
        "description": (
            "When filings are pending in multiple courts simultaneously "
            "(e.g. circuit + appellate, or circuit + federal), the trial "
            "court shows increased procedural compliance and faster "
            "response times.  Oversight pressure appears effective."
        ),
        "confidence": 0.68,
        "frequency": 4,
        "evidence": [
            "Timeline correlation multi-court filings vs ruling speed",
        ],
        "implications": [
            "Multi-jurisdiction strategy provides leverage",
            "Appellate oversight is an effective accountability tool",
        ],
        "actionable": True,
        "actions": [
            "Maintain simultaneous filings across jurisdictions",
            "Reference pending appeals in trial court motions",
        ],
    },
]

_SEED_EVIDENCE_PATTERNS: List[Dict[str, Any]] = [
    {
        "id": "EVI-001",
        "title": "Digital communication evidence most effective",
        "description": (
            "AppClose messages and text communications are the most "
            "frequently cited evidence in successful motions.  Courts "
            "treat time-stamped digital communications as highly "
            "credible.  305 documented interference incidents supported "
            "by AppClose records."
        ),
        "confidence": 0.87,
        "frequency": 305,
        "evidence": [
            "AppClose export logs",
            "Prior motion exhibits",
        ],
        "implications": [
            "Continue comprehensive AppClose documentation",
            "Digital evidence > testimonial in contested hearings",
        ],
        "actionable": True,
        "actions": [
            "Export and index all AppClose communications",
            "Include digital evidence exhibits in every motion",
        ],
    },
    {
        "id": "EVI-002",
        "title": "Photo/video evidence underutilised",
        "description": (
            "Physical evidence (photos of bruising, video of child "
            "condition) is available but has been underutilised in "
            "filings.  When included, it shifts burden of proof and "
            "forces opposing party to respond."
        ),
        "confidence": 0.72,
        "frequency": 6,
        "evidence": [
            "Photo/video inventory",
            "Filing exhibit lists",
        ],
        "implications": [
            "Visual evidence creates stronger emotional impact",
            "Underutilisation is a correctable strategic weakness",
        ],
        "actionable": True,
        "actions": [
            "Audit photo/video inventory for admissibility",
            "Include visual evidence in next filing wave",
        ],
    },
]

_SEED_TEMPORAL_PATTERNS: List[Dict[str, Any]] = [
    {
        "id": "TMP-001",
        "title": "Holiday-period filing clusters",
        "description": (
            "Emergency filings cluster around school holidays, "
            "Thanksgiving, Christmas, and summer break.  These periods "
            "account for 67% of all emergency motions despite comprising "
            "only ~25% of the calendar year."
        ),
        "confidence": 0.81,
        "frequency": 12,
        "evidence": [
            "Filing dates vs school calendar",
            "Holiday period analysis",
        ],
        "implications": [
            "Predictable pattern allows pre-emptive protective filings",
            "Supports argument of bad-faith timing",
        ],
        "actionable": True,
        "actions": [
            "File protective motions 2 weeks before each holiday",
            "Document pattern in sanctions motion",
        ],
    },
    {
        "id": "TMP-002",
        "title": "Retaliation response within 72 hours",
        "description": (
            "After father takes any affirmative action (motion, CPS "
            "report, police report, schedule request), opposing party "
            "responds with counter-action within 72 hours in 82% of "
            "cases.  Median response time: 48 hours."
        ),
        "confidence": 0.78,
        "frequency": 18,
        "evidence": [
            "Action-reaction timeline spreadsheet",
            "Communication logs",
        ],
        "implications": [
            "Predictable retaliation enables strategic planning",
            "Document each cycle to build pattern evidence",
        ],
        "actionable": True,
        "actions": [
            "Time filings to account for retaliation window",
            "Pre-document expected counter-actions",
        ],
    },
]


# ── Helper: build Pattern from seed dict ─────────────────────────────

def _seed_to_pattern(seed: Dict[str, Any], category: str) -> Pattern:
    """Convert a seed dictionary to a :class:`Pattern` dataclass."""
    return Pattern(
        pattern_id=seed["id"],
        category=category,
        title=seed["title"],
        description=seed["description"],
        confidence=seed["confidence"],
        frequency=seed["frequency"],
        evidence_refs=seed.get("evidence", []),
        implications=seed.get("implications", []),
        actionable=seed.get("actionable", False),
        actions=seed.get("actions", []),
    )


# ── Main engine ──────────────────────────────────────────────────────

class PatternMiner:
    """Mine litigation patterns from case data and filing history.

    Patterns are sourced from:
    1. Embedded domain knowledge (seed patterns from case analysis)
    2. Database queries against ``litigation_context.db``
    3. Statistical analysis of temporal and outcome data

    Usage::

        miner = PatternMiner()
        report = miner.mine_all()
        miner.export_patterns(Path("patterns.json"))
    """

    def __init__(self, db_path: Optional[Path] = None) -> None:
        self._db_path = db_path or _DB_PATH
        self._patterns: List[Pattern] = []
        self._mines_run: int = 0
        self._total_patterns_found: int = 0
        self._db_queries_executed: int = 0
        logger.info("PatternMiner initialised (db=%s)", self._db_path)

    # ── Database ─────────────────────────────────────────────────────

    def _connect_db(self) -> Optional[sqlite3.Connection]:
        """Open a WAL-mode connection to the central database."""
        if not self._db_path.exists():
            logger.warning("Database not found at %s", self._db_path)
            return None
        try:
            conn = sqlite3.connect(str(self._db_path), timeout=30)
            conn.row_factory = sqlite3.Row
            conn.execute("PRAGMA busy_timeout=60000")
            conn.execute("PRAGMA journal_mode=WAL")
            conn.execute("PRAGMA cache_size=-32000")
            conn.execute("PRAGMA temp_store=MEMORY")
            conn.execute("PRAGMA synchronous=NORMAL")
            return conn
        except sqlite3.Error as exc:
            logger.error("DB connection failed: %s", exc)
            return None

    def _safe_query(
        self,
        conn: sqlite3.Connection,
        sql: str,
        params: Tuple[Any, ...] = (),
    ) -> List[sqlite3.Row]:
        """Execute a query, returning rows or empty list on error."""
        try:
            self._db_queries_executed += 1
            return conn.execute(sql, params).fetchall()
        except sqlite3.Error as exc:
            logger.warning("Query failed: %s — %s", exc, sql[:120])
            return []

    def _table_exists(self, conn: sqlite3.Connection, name: str) -> bool:
        """Check whether a table exists in the database."""
        rows = self._safe_query(
            conn,
            "SELECT 1 FROM sqlite_master WHERE type='table' AND name=?",
            (name,),
        )
        return len(rows) > 0

    # ── Confidence calculation ───────────────────────────────────────

    @staticmethod
    def calculate_pattern_confidence(
        occurrences: int,
        total_observations: int,
        *,
        base_confidence: float = 0.5,
        min_observations: int = 3,
    ) -> float:
        """Calculate Bayesian-adjusted confidence for a pattern.

        Uses a logistic growth curve so that confidence increases
        rapidly with the first few observations, then asymptotes
        toward 1.0 as evidence accumulates.

        Args:
            occurrences: Number of times the pattern was observed.
            total_observations: Total data points examined.
            base_confidence: Prior confidence (default 0.5).
            min_observations: Minimum observations for non-zero confidence.

        Returns:
            Float in [0, 1].
        """
        if total_observations == 0 or occurrences < min_observations:
            return 0.0
        rate = occurrences / total_observations
        # Logistic growth: 2 / (1 + e^{-k*n}) - 1, scaled by rate
        k = 0.3
        growth = 2.0 / (1.0 + math.exp(-k * occurrences)) - 1.0
        raw = base_confidence * (1 - growth) + rate * growth
        return round(min(max(raw, 0.0), 1.0), 4)

    # ── Temporal clustering ──────────────────────────────────────────

    @staticmethod
    def cluster_temporal_events(
        events: List[Dict[str, Any]],
        window_days: int = 7,
    ) -> List[Dict[str, Any]]:
        """Group events into temporal clusters.

        Args:
            events: Each dict must have a ``"date"`` key (ISO date str).
            window_days: Max gap between events in the same cluster.

        Returns:
            List of cluster dicts with ``start``, ``end``, ``count``,
            ``events``, and ``duration_days`` keys.
        """
        if not events:
            return []

        dated: List[Tuple[datetime, Dict[str, Any]]] = []
        for ev in events:
            raw = ev.get("date", "")
            if not raw:
                continue
            try:
                dt = datetime.fromisoformat(raw.replace("Z", "+00:00"))
            except (ValueError, TypeError):
                try:
                    dt = datetime.strptime(raw[:10], "%Y-%m-%d")
                except (ValueError, TypeError):
                    continue
            dated.append((dt, ev))

        if not dated:
            return []

        dated.sort(key=lambda x: x[0])
        clusters: List[Dict[str, Any]] = []
        current: List[Tuple[datetime, Dict[str, Any]]] = [dated[0]]

        for dt, ev in dated[1:]:
            prev_dt = current[-1][0]
            if (dt - prev_dt).days <= window_days:
                current.append((dt, ev))
            else:
                clusters.append(_build_cluster(current))
                current = [(dt, ev)]
        clusters.append(_build_cluster(current))

        return clusters

    # ── Mining methods ───────────────────────────────────────────────

    def mine_judicial_patterns(self) -> List[Pattern]:
        """Mine patterns from Judge McNeill's rulings and behaviour.

        Returns seed patterns augmented with database-sourced data
        on ruling timelines, denial rates, and hearing grants.
        """
        patterns: List[Pattern] = [
            _seed_to_pattern(s, PatternCategory.JUDICIAL.value)
            for s in _SEED_JUDICIAL_PATTERNS
        ]

        conn = self._connect_db()
        if conn is None:
            logger.info(
                "No DB — returning %d seed judicial patterns", len(patterns)
            )
            return patterns

        try:
            # Augment with DB: ruling timeline analysis
            if self._table_exists(conn, "filings"):
                rows = self._safe_query(
                    conn,
                    """
                    SELECT filing_type, filed_date, ruling_date, outcome,
                           filed_by, lane
                    FROM filings
                    WHERE judge LIKE '%McNeill%'
                      AND filed_date IS NOT NULL
                      AND ruling_date IS NOT NULL
                    ORDER BY filed_date
                    """,
                )
                if rows:
                    patterns.extend(
                        self._analyse_ruling_timelines(rows)
                    )

            # Augment with DB: ex parte order frequency
            if self._table_exists(conn, "orders"):
                rows = self._safe_query(
                    conn,
                    """
                    SELECT order_type, order_date, ex_parte, case_number
                    FROM orders
                    WHERE judge LIKE '%McNeill%'
                    """,
                )
                if rows:
                    patterns.extend(
                        self._analyse_ex_parte_frequency(rows)
                    )

            # Denial rate by motion type
            if self._table_exists(conn, "motions"):
                rows = self._safe_query(
                    conn,
                    """
                    SELECT motion_type, filed_by, outcome, hearing_held
                    FROM motions
                    WHERE judge LIKE '%McNeill%'
                    """,
                )
                if rows:
                    patterns.extend(
                        self._analyse_denial_rates(rows)
                    )
        finally:
            conn.close()

        self._mines_run += 1
        return patterns

    def mine_adversary_patterns(self) -> List[Pattern]:
        """Mine opposing-counsel/party tactical patterns."""
        patterns: List[Pattern] = [
            _seed_to_pattern(s, PatternCategory.ADVERSARY.value)
            for s in _SEED_ADVERSARY_PATTERNS
        ]

        conn = self._connect_db()
        if conn is None:
            return patterns

        try:
            # Filing frequency / timing analysis
            if self._table_exists(conn, "filings"):
                rows = self._safe_query(
                    conn,
                    """
                    SELECT filed_date, filing_type, filed_by, lane
                    FROM filings
                    WHERE filed_by NOT LIKE '%Pigors%'
                      AND filed_date IS NOT NULL
                    ORDER BY filed_date
                    """,
                )
                if rows:
                    patterns.extend(
                        self._analyse_filing_timing(rows)
                    )

            # Communication pattern analysis
            if self._table_exists(conn, "communications"):
                rows = self._safe_query(
                    conn,
                    """
                    SELECT sent_date, sender, message_type, content_summary
                    FROM communications
                    ORDER BY sent_date
                    """,
                )
                if rows:
                    patterns.extend(
                        self._analyse_communication_patterns(rows)
                    )
        finally:
            conn.close()

        self._mines_run += 1
        return patterns

    def mine_outcome_patterns(self) -> List[Pattern]:
        """Mine patterns from filing outcomes across courts."""
        patterns: List[Pattern] = [
            _seed_to_pattern(s, PatternCategory.OUTCOME.value)
            for s in _SEED_OUTCOME_PATTERNS
        ]

        conn = self._connect_db()
        if conn is None:
            return patterns

        try:
            if self._table_exists(conn, "filings"):
                rows = self._safe_query(
                    conn,
                    """
                    SELECT filing_type, outcome, filed_by, lane, court,
                           evidence_count, filed_date
                    FROM filings
                    WHERE outcome IS NOT NULL
                    """,
                )
                if rows:
                    patterns.extend(self._analyse_outcomes(rows))
        finally:
            conn.close()

        self._mines_run += 1
        return patterns

    def mine_temporal_patterns(self) -> List[Pattern]:
        """Mine time-based patterns (clusters, seasonality, retaliation)."""
        patterns: List[Pattern] = [
            _seed_to_pattern(s, PatternCategory.TEMPORAL.value)
            for s in _SEED_TEMPORAL_PATTERNS
        ]

        conn = self._connect_db()
        if conn is None:
            return patterns

        try:
            events: List[Dict[str, Any]] = []
            for table in ("filings", "orders", "motions", "incidents"):
                if not self._table_exists(conn, table):
                    continue
                date_col = "filed_date" if table != "orders" else "order_date"
                if table == "incidents":
                    date_col = "incident_date"
                rows = self._safe_query(
                    conn,
                    f"SELECT {date_col} AS date, * FROM {table} "
                    f"WHERE {date_col} IS NOT NULL ORDER BY {date_col}",
                )
                for r in rows:
                    events.append({"date": r["date"], "source": table})

            if events:
                clusters = self.cluster_temporal_events(events, window_days=7)
                hot_clusters = [
                    c for c in clusters if c.get("count", 0) >= 3
                ]
                if hot_clusters:
                    patterns.append(Pattern(
                        pattern_id="TMP-DB-CLUSTERS",
                        category=PatternCategory.TEMPORAL.value,
                        title=f"{len(hot_clusters)} high-activity clusters detected",
                        description=(
                            f"Found {len(hot_clusters)} time periods with 3+ "
                            f"events within 7 days.  Densest cluster has "
                            f"{max(c['count'] for c in hot_clusters)} events."
                        ),
                        confidence=self.calculate_pattern_confidence(
                            len(hot_clusters), len(clusters)
                        ),
                        frequency=len(hot_clusters),
                        evidence_refs=[
                            f"Cluster {i+1}: {c['start']}–{c['end']}"
                            for i, c in enumerate(hot_clusters[:10])
                        ],
                        implications=[
                            "High-activity periods indicate coordinated actions",
                            "Useful for predicting future escalation windows",
                        ],
                        actionable=True,
                        actions=[
                            "Prepare protective filings before predicted hot periods",
                        ],
                    ))
        finally:
            conn.close()

        self._mines_run += 1
        return patterns

    def mine_evidence_patterns(self) -> List[Pattern]:
        """Mine effectiveness patterns from evidence usage."""
        patterns: List[Pattern] = [
            _seed_to_pattern(s, PatternCategory.EVIDENCE.value)
            for s in _SEED_EVIDENCE_PATTERNS
        ]

        conn = self._connect_db()
        if conn is None:
            return patterns

        try:
            if self._table_exists(conn, "evidence"):
                rows = self._safe_query(
                    conn,
                    """
                    SELECT evidence_type, category, cited_in_orders,
                           effectiveness_score, lane
                    FROM evidence
                    WHERE evidence_type IS NOT NULL
                    """,
                )
                if rows:
                    patterns.extend(
                        self._analyse_evidence_effectiveness(rows)
                    )

            if self._table_exists(conn, "exhibits"):
                rows = self._safe_query(
                    conn,
                    """
                    SELECT exhibit_type, outcome_impact, filing_id, lane
                    FROM exhibits
                    WHERE outcome_impact IS NOT NULL
                    """,
                )
                if rows:
                    patterns.extend(
                        self._analyse_exhibit_impact(rows)
                    )
        finally:
            conn.close()

        self._mines_run += 1
        return patterns

    def find_cross_lane_patterns(self) -> List[Pattern]:
        """Identify patterns that span multiple case lanes."""
        all_patterns = list(self._patterns) if self._patterns else []
        if not all_patterns:
            # Mine everything first
            all_patterns = (
                self.mine_judicial_patterns()
                + self.mine_adversary_patterns()
                + self.mine_outcome_patterns()
                + self.mine_temporal_patterns()
                + self.mine_evidence_patterns()
            )

        cross_lane: List[Pattern] = []

        # Patterns that appear across multiple lanes
        lane_counter: Dict[str, Set[str]] = defaultdict(set)
        for p in all_patterns:
            if p.lane:
                lane_counter[p.pattern_id].add(p.lane)

        for pid, lanes in lane_counter.items():
            if len(lanes) >= 2:
                source = next((p for p in all_patterns if p.pattern_id == pid), None)
                if source:
                    cross = Pattern(
                        pattern_id=f"CROSS-{pid}",
                        category=PatternCategory.PROCEDURAL.value,
                        title=f"Cross-lane: {source.title}",
                        description=(
                            f"Pattern '{source.title}' appears in lanes "
                            f"{', '.join(sorted(lanes))}.  Cross-lane "
                            f"patterns strengthen systemic-bias arguments."
                        ),
                        confidence=min(source.confidence + 0.05, 1.0),
                        frequency=source.frequency,
                        evidence_refs=source.evidence_refs,
                        implications=[
                            "Cross-lane pattern strengthens systemic argument",
                            *source.implications,
                        ],
                        actionable=True,
                        actions=[
                            "Reference in convergence (Lane C) filings",
                            *source.actions,
                        ],
                    )
                    cross_lane.append(cross)

        # Hardcoded cross-lane: judicial bias spans A + D + E + F
        cross_lane.append(Pattern(
            pattern_id="CROSS-JUDICIAL-MULTI",
            category=PatternCategory.PROCEDURAL.value,
            title="Judicial bias pattern spans custody, PPO, misconduct, and appellate lanes",
            description=(
                "Judge McNeill's ex parte order pattern (18.26%, 3.65× normal) "
                "affects Lane A (custody orders), Lane D (PPO enforcement), "
                "Lane E (JTC complaint basis), and Lane F (appellate arguments). "
                "This cross-lane convergence is the strongest evidence of "
                "systemic bias."
            ),
            confidence=0.93,
            frequency=23,
            evidence_refs=[
                "Docket 2024-001507-DC", "Docket 2023-5907-PP",
                "COA 366810 brief", "JTC complaint draft",
            ],
            implications=[
                "Convergence argument: same bias → multiple harms",
                "Federal §1983 due-process claim has cross-lane support",
            ],
            actionable=True,
            actions=[
                "Build convergence brief linking all four lanes",
                "Include cross-lane analysis in COA brief",
                "Reference in federal complaint if filed",
            ],
        ))

        self._mines_run += 1
        return cross_lane

    def mine_all(self) -> PatternReport:
        """Run all mining operations and return a comprehensive report."""
        judicial = self.mine_judicial_patterns()
        adversary = self.mine_adversary_patterns()
        outcome = self.mine_outcome_patterns()
        temporal = self.mine_temporal_patterns()
        evidence = self.mine_evidence_patterns()
        cross = self.find_cross_lane_patterns()

        all_patterns = judicial + adversary + outcome + temporal + evidence
        self._patterns = all_patterns

        by_category: Dict[str, List[Pattern]] = defaultdict(list)
        for p in all_patterns:
            by_category[p.category].append(p)

        high_conf = [p for p in all_patterns if p.confidence >= _CONF_HIGH]
        actionable = sorted(
            [p for p in all_patterns if p.actionable],
            key=lambda p: p.confidence,
            reverse=True,
        )

        # Temporal clusters from all events
        event_dicts: List[Dict[str, Any]] = []
        for p in all_patterns:
            if p.detected_at:
                event_dicts.append({"date": p.detected_at, "pattern": p.title})
        clusters = self.cluster_temporal_events(event_dicts, window_days=14)

        self._total_patterns_found = len(all_patterns)

        report = PatternReport(
            total_patterns=len(all_patterns),
            high_confidence_count=len(high_conf),
            patterns_by_category=dict(by_category),
            top_actionable=actionable[:15],
            cross_lane_patterns=cross,
            temporal_clusters=clusters,
        )

        logger.info(
            "Mine complete: %d patterns (%d high confidence, %d actionable)",
            report.total_patterns,
            report.high_confidence_count,
            len(actionable),
        )
        return report

    # ── Export ────────────────────────────────────────────────────────

    def export_patterns(self, output_path: Path) -> None:
        """Export all mined patterns to a JSON file.

        If no patterns have been mined yet, calls :meth:`mine_all` first.
        """
        if not self._patterns:
            self.mine_all()

        data = {
            "exported_at": datetime.now(timezone.utc).isoformat(),
            "total_patterns": len(self._patterns),
            "patterns": [p.to_dict() for p in self._patterns],
        }

        output = Path(output_path)
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(
            json.dumps(data, indent=2, default=str),
            encoding="utf-8",
        )
        logger.info("Exported %d patterns to %s", len(self._patterns), output)

    # ── Stats ────────────────────────────────────────────────────────

    def get_stats(self) -> Dict[str, Any]:
        """Return operational statistics."""
        category_counts: Dict[str, int] = Counter(
            p.category for p in self._patterns
        )
        avg_confidence = (
            round(statistics.mean(p.confidence for p in self._patterns), 3)
            if self._patterns else 0.0
        )
        return {
            "mines_run": self._mines_run,
            "total_patterns_found": self._total_patterns_found,
            "current_pattern_count": len(self._patterns),
            "patterns_by_category": dict(category_counts),
            "average_confidence": avg_confidence,
            "high_confidence_count": sum(
                1 for p in self._patterns if p.confidence >= _CONF_HIGH
            ),
            "actionable_count": sum(
                1 for p in self._patterns if p.actionable
            ),
            "db_queries_executed": self._db_queries_executed,
            "db_path": str(self._db_path),
            "db_exists": self._db_path.exists(),
            "supported_categories": [c.value for c in PatternCategory],
            "supported_lanes": list(_LANES.keys()),
        }

    # ── Internal analysis helpers ────────────────────────────────────

    def _analyse_ruling_timelines(
        self, rows: List[sqlite3.Row]
    ) -> List[Pattern]:
        """Analyse filing-to-ruling time differences."""
        patterns: List[Pattern] = []
        father_days: List[float] = []
        mother_days: List[float] = []

        for r in rows:
            try:
                filed = datetime.strptime(str(r["filed_date"])[:10], "%Y-%m-%d")
                ruled = datetime.strptime(str(r["ruling_date"])[:10], "%Y-%m-%d")
                delta = (ruled - filed).days
                filed_by = str(r["filed_by"]).lower()
                if "pigors" in filed_by or "andrew" in filed_by or "father" in filed_by:
                    father_days.append(delta)
                else:
                    mother_days.append(delta)
            except (ValueError, TypeError, KeyError):
                continue

        if father_days and mother_days:
            f_avg = statistics.mean(father_days)
            m_avg = statistics.mean(mother_days)
            ratio = f_avg / m_avg if m_avg > 0 else float("inf")

            patterns.append(Pattern(
                pattern_id="JUD-DB-TIMELINE",
                category=PatternCategory.JUDICIAL.value,
                title="DB-confirmed ruling timeline asymmetry",
                description=(
                    f"Father's motions: avg {f_avg:.1f} days to ruling "
                    f"(n={len(father_days)}).  Mother's motions: avg "
                    f"{m_avg:.1f} days (n={len(mother_days)}).  Ratio: "
                    f"{ratio:.1f}×."
                ),
                confidence=self.calculate_pattern_confidence(
                    len(father_days) + len(mother_days),
                    len(rows),
                ),
                frequency=len(father_days) + len(mother_days),
                evidence_refs=["litigation_context.db filings table"],
                implications=[
                    f"Father waits {ratio:.1f}× longer for rulings",
                    "Supports asymmetric treatment argument",
                ],
                actionable=True,
                actions=[
                    "Include timeline chart in disqualification brief",
                ],
            ))

        return patterns

    def _analyse_ex_parte_frequency(
        self, rows: List[sqlite3.Row]
    ) -> List[Pattern]:
        """Analyse ex parte order issuance rate."""
        patterns: List[Pattern] = []
        total = len(rows)
        ex_parte_count = sum(
            1 for r in rows
            if str(r["ex_parte"]).lower() in ("1", "true", "yes")
        )

        if total > 0:
            rate = ex_parte_count / total
            michigan_avg = 0.05  # ~5% statewide average
            multiple = rate / michigan_avg if michigan_avg > 0 else 0

            patterns.append(Pattern(
                pattern_id="JUD-DB-EXPARTE",
                category=PatternCategory.JUDICIAL.value,
                title="DB-confirmed ex parte order rate",
                description=(
                    f"Ex parte orders: {ex_parte_count}/{total} "
                    f"({rate:.1%}) — {multiple:.1f}× Michigan average "
                    f"of {michigan_avg:.0%}."
                ),
                confidence=self.calculate_pattern_confidence(
                    ex_parte_count, total
                ),
                frequency=ex_parte_count,
                evidence_refs=["litigation_context.db orders table"],
                implications=[
                    f"Ex parte rate {multiple:.1f}× above statewide norm",
                ],
                actionable=rate > michigan_avg * 2,
                actions=(
                    ["Cite DB statistics in disqualification brief"]
                    if rate > michigan_avg * 2 else []
                ),
            ))

        return patterns

    def _analyse_denial_rates(
        self, rows: List[sqlite3.Row]
    ) -> List[Pattern]:
        """Analyse denial rate by filer and motion type."""
        patterns: List[Pattern] = []
        by_filer: Dict[str, Dict[str, int]] = defaultdict(
            lambda: {"total": 0, "denied": 0, "granted": 0}
        )

        for r in rows:
            filed_by = str(r["filed_by"]).lower()
            filer = "father" if any(
                x in filed_by for x in ("pigors", "andrew", "father")
            ) else "mother"
            outcome = str(r["outcome"]).lower()
            by_filer[filer]["total"] += 1
            if "denied" in outcome or "deny" in outcome:
                by_filer[filer]["denied"] += 1
            elif "granted" in outcome or "grant" in outcome:
                by_filer[filer]["granted"] += 1

        if by_filer["father"]["total"] > 0 and by_filer["mother"]["total"] > 0:
            f_deny = (
                by_filer["father"]["denied"] / by_filer["father"]["total"]
            )
            m_deny = (
                by_filer["mother"]["denied"] / by_filer["mother"]["total"]
            )

            patterns.append(Pattern(
                pattern_id="JUD-DB-DENIAL",
                category=PatternCategory.JUDICIAL.value,
                title="DB-confirmed denial rate disparity",
                description=(
                    f"Father denial rate: {f_deny:.0%} "
                    f"({by_filer['father']['denied']}/"
                    f"{by_filer['father']['total']}).  "
                    f"Mother denial rate: {m_deny:.0%} "
                    f"({by_filer['mother']['denied']}/"
                    f"{by_filer['mother']['total']})."
                ),
                confidence=self.calculate_pattern_confidence(
                    by_filer["father"]["total"] + by_filer["mother"]["total"],
                    len(rows),
                ),
                frequency=len(rows),
                evidence_refs=["litigation_context.db motions table"],
                implications=[
                    "Denial-rate disparity supports bias argument",
                ],
                actionable=f_deny > m_deny + 0.15,
                actions=(
                    ["Include denial-rate comparison in brief"]
                    if f_deny > m_deny + 0.15 else []
                ),
            ))

        return patterns

    def _analyse_filing_timing(
        self, rows: List[sqlite3.Row]
    ) -> List[Pattern]:
        """Analyse opposing party filing timing vs weekends/holidays."""
        patterns: List[Pattern] = []
        weekend_count = 0
        total = 0

        # Major US/MI holidays (month, day) — approximate
        holidays = {
            (1, 1), (1, 2),     # New Year
            (7, 4),              # Independence Day
            (11, 23), (11, 24), (11, 25), (11, 26), (11, 27),  # Thanksgiving week
            (12, 24), (12, 25), (12, 26), (12, 31),            # Christmas/NYE
        }

        holiday_filings = 0
        for r in rows:
            try:
                dt = datetime.strptime(str(r["filed_date"])[:10], "%Y-%m-%d")
                total += 1
                if dt.weekday() >= 4:  # Friday–Sunday
                    weekend_count += 1
                if (dt.month, dt.day) in holidays:
                    holiday_filings += 1
                # Check if within 2 days of a holiday
                for hm, hd in holidays:
                    try:
                        hdate = dt.replace(month=hm, day=hd)
                        if abs((dt - hdate).days) <= 2:
                            holiday_filings += 1
                            break
                    except ValueError:
                        continue
            except (ValueError, TypeError):
                continue

        if total >= 5:
            weekend_rate = weekend_count / total
            # Expected rate for Fri-Sun: ~3/7 = 42.9%
            if weekend_rate > 0.55:
                patterns.append(Pattern(
                    pattern_id="ADV-DB-WEEKEND",
                    category=PatternCategory.ADVERSARY.value,
                    title="DB-confirmed weekend/holiday filing preference",
                    description=(
                        f"Opposing party files on Fri-Sun in {weekend_rate:.0%} "
                        f"of cases ({weekend_count}/{total}).  "
                        f"{holiday_filings} filings within 2 days of a holiday."
                    ),
                    confidence=self.calculate_pattern_confidence(
                        weekend_count, total
                    ),
                    frequency=weekend_count,
                    evidence_refs=["litigation_context.db filings table"],
                    implications=[
                        "Strategic timing reduces father's response window",
                    ],
                    actionable=True,
                    actions=[
                        "Document in sanctions motion",
                        "File protective motions before weekends/holidays",
                    ],
                ))

        return patterns

    def _analyse_communication_patterns(
        self, rows: List[sqlite3.Row]
    ) -> List[Pattern]:
        """Analyse communication patterns from AppClose / message data."""
        patterns: List[Pattern] = []
        refusal_keywords = re.compile(
            r"no|denied|refused|cancel|can'?t|won'?t|not\s+(?:going|happening)",
            re.IGNORECASE,
        )
        refusal_count = 0
        total = len(rows)

        for r in rows:
            summary = str(r["content_summary"]) if r["content_summary"] else ""
            if refusal_keywords.search(summary):
                refusal_count += 1

        if total > 0 and refusal_count > 5:
            patterns.append(Pattern(
                pattern_id="ADV-DB-REFUSAL",
                category=PatternCategory.ADVERSARY.value,
                title="DB-confirmed communication refusal pattern",
                description=(
                    f"{refusal_count}/{total} communications contain "
                    f"refusal/denial language ({refusal_count/total:.0%})."
                ),
                confidence=self.calculate_pattern_confidence(
                    refusal_count, total
                ),
                frequency=refusal_count,
                evidence_refs=["litigation_context.db communications table"],
                implications=[
                    "High refusal rate documents uncooperative co-parenting",
                ],
                actionable=True,
                actions=[
                    "Cite in custody factor (j) argument",
                    "Include communication excerpts as exhibits",
                ],
            ))

        return patterns

    def _analyse_outcomes(
        self, rows: List[sqlite3.Row]
    ) -> List[Pattern]:
        """Analyse filing outcomes by type, court, evidence count."""
        patterns: List[Pattern] = []
        by_type: Dict[str, Dict[str, int]] = defaultdict(
            lambda: {"total": 0, "granted": 0, "denied": 0}
        )

        for r in rows:
            ftype = str(r["filing_type"])
            outcome = str(r["outcome"]).lower()
            by_type[ftype]["total"] += 1
            if "grant" in outcome:
                by_type[ftype]["granted"] += 1
            elif "den" in outcome:
                by_type[ftype]["denied"] += 1

        for ftype, counts in by_type.items():
            if counts["total"] >= 3:
                grant_rate = counts["granted"] / counts["total"]
                patterns.append(Pattern(
                    pattern_id=f"OUT-DB-{ftype[:20].upper().replace(' ', '_')}",
                    category=PatternCategory.OUTCOME.value,
                    title=f"Outcome rate for {ftype}",
                    description=(
                        f"{ftype}: {counts['granted']}/{counts['total']} "
                        f"granted ({grant_rate:.0%}), "
                        f"{counts['denied']} denied."
                    ),
                    confidence=self.calculate_pattern_confidence(
                        counts["total"], len(rows)
                    ),
                    frequency=counts["total"],
                    evidence_refs=["litigation_context.db filings table"],
                    implications=[
                        f"{ftype} grant rate: {grant_rate:.0%}",
                    ],
                    actionable=grant_rate < 0.4,
                    actions=(
                        [f"Consider alternative filing strategy for {ftype}"]
                        if grant_rate < 0.4 else []
                    ),
                ))

        return patterns

    def _analyse_evidence_effectiveness(
        self, rows: List[sqlite3.Row]
    ) -> List[Pattern]:
        """Analyse which evidence types are most effective."""
        patterns: List[Pattern] = []
        by_type: Dict[str, List[float]] = defaultdict(list)

        for r in rows:
            etype = str(r["evidence_type"])
            score = r["effectiveness_score"]
            if score is not None:
                try:
                    by_type[etype].append(float(score))
                except (ValueError, TypeError):
                    continue

        for etype, scores in by_type.items():
            if len(scores) >= 2:
                avg = statistics.mean(scores)
                patterns.append(Pattern(
                    pattern_id=f"EVI-DB-{etype[:20].upper().replace(' ', '_')}",
                    category=PatternCategory.EVIDENCE.value,
                    title=f"Effectiveness of {etype} evidence",
                    description=(
                        f"{etype}: avg effectiveness {avg:.2f} "
                        f"(n={len(scores)})."
                    ),
                    confidence=self.calculate_pattern_confidence(
                        len(scores), len(rows)
                    ),
                    frequency=len(scores),
                    evidence_refs=["litigation_context.db evidence table"],
                    implications=[
                        f"{etype} evidence avg score: {avg:.2f}",
                    ],
                    actionable=avg >= 0.7,
                    actions=(
                        [f"Prioritise {etype} evidence in filings"]
                        if avg >= 0.7 else []
                    ),
                ))

        return patterns

    def _analyse_exhibit_impact(
        self, rows: List[sqlite3.Row]
    ) -> List[Pattern]:
        """Analyse which exhibit types impact outcomes."""
        patterns: List[Pattern] = []
        impact_counts: Dict[str, Dict[str, int]] = defaultdict(
            lambda: {"positive": 0, "neutral": 0, "negative": 0, "total": 0}
        )

        for r in rows:
            etype = str(r["exhibit_type"])
            impact = str(r["outcome_impact"]).lower()
            impact_counts[etype]["total"] += 1
            if "positive" in impact or "favorable" in impact:
                impact_counts[etype]["positive"] += 1
            elif "negative" in impact or "unfavorable" in impact:
                impact_counts[etype]["negative"] += 1
            else:
                impact_counts[etype]["neutral"] += 1

        for etype, counts in impact_counts.items():
            if counts["total"] >= 2:
                pos_rate = counts["positive"] / counts["total"]
                patterns.append(Pattern(
                    pattern_id=f"EVI-DB-EXH-{etype[:15].upper().replace(' ', '_')}",
                    category=PatternCategory.EVIDENCE.value,
                    title=f"Exhibit impact: {etype}",
                    description=(
                        f"{etype} exhibits: {counts['positive']}/"
                        f"{counts['total']} positive impact ({pos_rate:.0%})."
                    ),
                    confidence=self.calculate_pattern_confidence(
                        counts["total"], len(rows)
                    ),
                    frequency=counts["total"],
                    evidence_refs=["litigation_context.db exhibits table"],
                    implications=[
                        f"{etype} exhibits positive rate: {pos_rate:.0%}",
                    ],
                    actionable=pos_rate >= 0.6,
                    actions=(
                        [f"Include more {etype} exhibits in filings"]
                        if pos_rate >= 0.6 else []
                    ),
                ))

        return patterns


# ── Module-level helpers ─────────────────────────────────────────────

def _build_cluster(
    items: List[Tuple[datetime, Dict[str, Any]]]
) -> Dict[str, Any]:
    """Build a cluster dict from a list of (datetime, event) tuples."""
    start = items[0][0]
    end = items[-1][0]
    return {
        "start": start.isoformat(),
        "end": end.isoformat(),
        "count": len(items),
        "duration_days": max((end - start).days, 0),
        "events": [ev for _, ev in items],
    }
