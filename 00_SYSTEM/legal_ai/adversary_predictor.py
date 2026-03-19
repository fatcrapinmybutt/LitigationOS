# -*- coding: utf-8 -*-
"""
Adversary Predictor — LitigationOS Legal AI Subsystem
=======================================================
Predicts opposing-counsel strategy, likely objections, motion responses,
and judicial tendencies based on documented behavioural patterns from the
Pigors v. Watson litigation across all six case lanes.

The engine embeds known adversary profiles derived from court records and
uses pattern matching against filing types to generate probabilistic
predictions with pre-built counter-strategies.

Adversary Profiles:
    Emily A. Watson / counsel — Emergency PPO filer, ex-parte seeker
    Hon. Jenny L. McNeill      — Ex parte grant bias, status-quo favourer
    Friend of Court (FOC)      — Rubber-stamp pattern, investigation delays
    Shady Oaks / Housing       — Ignore-and-delay, jurisdictional MTD

Case Context:
    Plaintiff:  Andrew James Pigors (Pro Se)
    Defendant:  Emily A. Watson
    Child:      L.D.W. (per MCR 8.119(H)) — Male
    Judge:      Hon. Jenny L. McNeill — 14th Circuit Court
    Lanes:      A=Custody, B=Housing, C=Convergence, D=PPO,
                E=Misconduct, F=Appellate (COA 366810)

CRITICAL FABRICATION WARNING:
    "9 CPS investigations" is FABRICATED.  Andrew called CPS ONCE about
    bruising and filed police reports.  This engine flags that fabrication
    whenever the opposing side is predicted to use it.

Usage:
    from legal_ai.adversary_predictor import AdversaryPredictor

    predictor = AdversaryPredictor()
    report = predictor.predict_response("custody_modification", "14th_circuit", "A")
    for pred in report.predictions:
        print(pred.filing_type, pred.risk_assessment)

    profile = predictor.get_adversary_profile("judge")
    print(profile.predicted_strategy)

Zero external dependencies.  CPU-first.  Local-only.
"""
from __future__ import annotations

import hashlib
import logging
import re
import sqlite3
from collections import defaultdict
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple

logger = logging.getLogger("legal_ai.adversary_predictor")

# ---------------------------------------------------------------------------
# Path resolution — legal_ai → 00_SYSTEM → LitigationOS root
# ---------------------------------------------------------------------------
_HERE = Path(__file__).resolve().parent
_DB_PATH = _HERE.parents[1] / "litigation_context.db"

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

LANE_LABELS: Dict[str, str] = {
    "A": "Custody (2024-001507-DC)",
    "B": "Housing (2025-002760-CZ)",
    "C": "Convergence (cross-lane)",
    "D": "PPO (2023-5907-PP)",
    "E": "Misconduct / JTC",
    "F": "Appellate (COA 366810)",
}

RISK_LEVELS: Tuple[str, ...] = ("critical", "high", "medium", "low")

# ---------------------------------------------------------------------------
# Adversary pattern data (derived from case records)
# ---------------------------------------------------------------------------

_WATSON_PATTERNS: List[Dict[str, Any]] = [
    {
        "id": "watson_emergency_ppo",
        "pattern": "File emergency PPO motions when Andrew exercises parental rights",
        "frequency": "recurring",
        "lanes": ["A", "D"],
        "trigger_filings": [
            "custody_modification",
            "parenting_time_enforcement",
            "contempt_motion",
        ],
        "probability": 0.75,
    },
    {
        "id": "watson_harassment_claim",
        "pattern": "Allege 'harassment' when Andrew contacts CPS about child safety",
        "frequency": "documented",
        "lanes": ["A", "D"],
        "trigger_filings": ["custody_modification", "ppo_defense"],
        "probability": 0.65,
        "fabrication_warning": (
            "Opposing side may claim '9 CPS investigations' — this is FABRICATED. "
            "Andrew called CPS ONCE about bruising and filed police reports."
        ),
    },
    {
        "id": "watson_ex_parte",
        "pattern": "Seek ex parte orders without notice to Andrew",
        "frequency": "recurring",
        "lanes": ["A", "D"],
        "trigger_filings": [
            "custody_modification",
            "motion_disqualification",
            "contempt_motion",
        ],
        "probability": 0.60,
    },
    {
        "id": "watson_noncompliance",
        "pattern": "Refuse to follow custody/parenting time orders",
        "frequency": "305 documented incidents",
        "lanes": ["A"],
        "trigger_filings": [
            "parenting_time_enforcement",
            "contempt_motion",
            "custody_modification",
        ],
        "probability": 0.85,
    },
    {
        "id": "watson_delay",
        "pattern": "Delay proceedings through continuances and discovery obstruction",
        "frequency": "recurring",
        "lanes": ["A", "D"],
        "trigger_filings": ["discovery_request", "interrogatory"],
        "probability": 0.55,
    },
]

_MCNEILL_PATTERNS: List[Dict[str, Any]] = [
    {
        "id": "mcneill_ex_parte_bias",
        "pattern": "Grant ex parte motions without hearing (18.26% rate = 3.65x normal 5%)",
        "frequency": "statistical",
        "lanes": ["A", "D"],
        "trigger_filings": [
            "custody_modification",
            "contempt_motion",
            "parenting_time_enforcement",
        ],
        "probability": 0.70,
    },
    {
        "id": "mcneill_deny_disqualification",
        "pattern": "Deny disqualification motions under MCR 2.003",
        "frequency": "expected",
        "lanes": ["A", "E"],
        "trigger_filings": ["motion_disqualification"],
        "probability": 0.85,
    },
    {
        "id": "mcneill_status_quo",
        "pattern": "Favour status quo and custodial parent",
        "frequency": "pattern",
        "lanes": ["A"],
        "trigger_filings": [
            "custody_modification",
            "parenting_time_enforcement",
        ],
        "probability": 0.70,
    },
    {
        "id": "mcneill_limit_pro_se",
        "pattern": "Apply stricter procedural requirements to pro se litigants",
        "frequency": "observed",
        "lanes": ["A", "D"],
        "trigger_filings": ["motion_disqualification", "contempt_motion"],
        "probability": 0.50,
    },
]

_FOC_PATTERNS: List[Dict[str, Any]] = [
    {
        "id": "foc_rubber_stamp",
        "pattern": "Rubber-stamp judge recommendations without independent investigation",
        "frequency": "pattern",
        "lanes": ["A"],
        "trigger_filings": ["custody_modification", "parenting_time_enforcement"],
        "probability": 0.60,
    },
    {
        "id": "foc_delay_investigation",
        "pattern": "Delay investigations beyond statutory timelines",
        "frequency": "documented",
        "lanes": ["A"],
        "trigger_filings": ["foc_objection", "custody_modification"],
        "probability": 0.55,
    },
    {
        "id": "foc_ignore_evidence",
        "pattern": "Fail to consider submitted evidence in reports",
        "frequency": "documented",
        "lanes": ["A"],
        "trigger_filings": ["custody_modification"],
        "probability": 0.45,
    },
]

_HOUSING_PATTERNS: List[Dict[str, Any]] = [
    {
        "id": "housing_ignore",
        "pattern": "Ignore complaints and delay responses past deadlines",
        "frequency": "documented",
        "lanes": ["B"],
        "trigger_filings": ["housing_complaint", "demand_letter"],
        "probability": 0.75,
    },
    {
        "id": "housing_service_challenge",
        "pattern": "Claim not properly served to delay proceedings",
        "frequency": "expected",
        "lanes": ["B"],
        "trigger_filings": ["housing_complaint", "rico_complaint"],
        "probability": 0.65,
    },
    {
        "id": "housing_mtd_jurisdiction",
        "pattern": "File MTD on jurisdictional grounds",
        "frequency": "expected",
        "lanes": ["B"],
        "trigger_filings": [
            "housing_complaint",
            "rico_complaint",
            "fha_complaint",
        ],
        "probability": 0.70,
    },
    {
        "id": "housing_corporate_veil",
        "pattern": "Use multiple LLCs to obscure responsible parties",
        "frequency": "documented",
        "lanes": ["B"],
        "trigger_filings": ["rico_complaint", "housing_complaint"],
        "probability": 0.50,
    },
]

# Compiled adversary profile index
_PROFILE_INDEX: Dict[str, Dict[str, Any]] = {
    "watson": {
        "name": "Emily A. Watson",
        "role": "opposing_party",
        "patterns": _WATSON_PATTERNS,
        "strategy": (
            "Defensive/aggressive: uses PPO filings as offensive weapons, "
            "seeks ex parte orders to create fait accompli, obstructs "
            "parenting time while claiming harassment."
        ),
    },
    "opposing_counsel": {
        "name": "Emily A. Watson / Counsel",
        "role": "opposing_counsel",
        "patterns": _WATSON_PATTERNS,
        "strategy": (
            "Delay-and-deny with emergency motions. Will seek ex parte "
            "orders, file PPO motions reactively, and obstruct discovery."
        ),
    },
    "judge": {
        "name": "Hon. Jenny L. McNeill",
        "role": "judge",
        "patterns": _MCNEILL_PATTERNS,
        "strategy": (
            "Status-quo preservation with ex parte bias. Grants emergency "
            "motions at 18.26% (3.65× the normal 5% rate). Denies "
            "disqualification. Favours custodial parent."
        ),
    },
    "foc": {
        "name": "Muskegon County Friend of Court",
        "role": "foc",
        "patterns": _FOC_PATTERNS,
        "strategy": (
            "Rubber-stamp approach: adopt judicial recommendations without "
            "independent investigation. Delay statutory investigations."
        ),
    },
    "gal": {
        "name": "Guardian ad Litem (if appointed)",
        "role": "gal",
        "patterns": _FOC_PATTERNS,  # similar pattern
        "strategy": (
            "Likely follows FOC/judicial lead. May not conduct independent "
            "investigation. Counter: demand specific investigation tasks."
        ),
    },
    "housing": {
        "name": "Shady Oaks MHP / Management",
        "role": "housing_defendant",
        "patterns": _HOUSING_PATTERNS,
        "strategy": (
            "Ignore-delay-challenge: ignore complaints, delay responses, "
            "then challenge service and jurisdiction when sued."
        ),
    },
}

# ---------------------------------------------------------------------------
# Objection & counter-motion templates per filing type
# ---------------------------------------------------------------------------

_OBJECTION_TEMPLATES: Dict[str, List[Dict[str, Any]]] = {
    "custody_modification": [
        {
            "objection": "No material change in circumstances",
            "probability": 0.80,
            "counter": (
                "Document 305 parenting-time interference incidents, "
                "false PPO filings, and changed living conditions as "
                "material change under MCL 722.27(1)(c)."
            ),
        },
        {
            "objection": "Best interest of child favours status quo",
            "probability": 0.75,
            "counter": (
                "Present evidence that status quo includes systematic "
                "interference with father-child relationship (MCL 722.23 "
                "factor (j): willingness to facilitate relationship)."
            ),
        },
        {
            "objection": "Father has history of CPS involvement",
            "probability": 0.60,
            "counter": (
                "REBUTTAL: Andrew called CPS ONCE about bruising on L.D.W. "
                "and filed police reports. '9 CPS investigations' is "
                "FABRICATED. Demand opposing party produce evidence."
            ),
        },
        {
            "objection": "Father is harassing/stalking",
            "probability": 0.55,
            "counter": (
                "Present communication records showing lawful parenting "
                "inquiries, not harassment. Cross-reference with custody "
                "order provisions."
            ),
        },
    ],
    "motion_disqualification": [
        {
            "objection": "Insufficient showing of bias under MCR 2.003",
            "probability": 0.85,
            "counter": (
                "Present statistical analysis: 18.26% ex parte grant rate "
                "vs 5% norm (3.65× deviation). Cite specific rulings "
                "demonstrating actual bias."
            ),
        },
        {
            "objection": "Adverse rulings alone do not show bias",
            "probability": 0.75,
            "counter": (
                "Argument is not based on adverse rulings alone but on "
                "statistical pattern of procedural bias, ex parte grants "
                "without hearing, and denial of due process."
            ),
        },
        {
            "objection": "Untimely — should have been raised earlier",
            "probability": 0.50,
            "counter": (
                "Pattern of bias was not apparent until statistical "
                "analysis was complete. MCR 2.003(D) permits filing "
                "when grounds become known."
            ),
        },
    ],
    "contempt_motion": [
        {
            "objection": "Respondent substantially complied",
            "probability": 0.65,
            "counter": (
                "Present log of 305 documented interference incidents "
                "showing pattern of wilful noncompliance, not substantial "
                "compliance."
            ),
        },
        {
            "objection": "Changed circumstances made compliance impossible",
            "probability": 0.50,
            "counter": (
                "Demand specifics: which circumstances, when, and what "
                "efforts were made to comply. 305 incidents over extended "
                "period negates impossibility defense."
            ),
        },
    ],
    "housing_complaint": [
        {
            "objection": "Improper service",
            "probability": 0.70,
            "counter": (
                "Document all service attempts with dates, methods, and "
                "affidavits. Use alternative service (posting/publication) "
                "under MCR 2.105(I) if personal service fails."
            ),
        },
        {
            "objection": "Lack of personal jurisdiction",
            "probability": 0.65,
            "counter": (
                "Defendants transact business in Michigan and the cause "
                "of action arises from Michigan property. Long-arm statute "
                "MCL 600.705 and 600.715 apply."
            ),
        },
        {
            "objection": "Failure to state a claim (12(b)(6))",
            "probability": 0.55,
            "counter": (
                "Complaint alleges specific facts: utility overcharges, "
                "habitability violations, code violations, and fraud "
                "pattern. Satisfies notice pleading under MCR 2.111."
            ),
        },
    ],
    "rico_complaint": [
        {
            "objection": "No pattern of racketeering activity",
            "probability": 0.70,
            "counter": (
                "Document at least two predicate acts: mail/wire fraud "
                "in utility billing, fraud in lease representations. "
                "Pattern established across multiple tenants/time periods."
            ),
        },
        {
            "objection": "No enterprise",
            "probability": 0.55,
            "counter": (
                "Multiple LLCs operating as single enterprise under "
                "common control. Use discovery to establish ownership "
                "chain and shared management."
            ),
        },
    ],
    "ppo_defense": [
        {
            "objection": "Petitioner has reasonable fear",
            "probability": 0.60,
            "counter": (
                "Present evidence of no threatening conduct, lawful "
                "parenting activities, and that PPO was filed in "
                "retaliation for custody enforcement."
            ),
        },
        {
            "objection": "Prior incidents establish pattern",
            "probability": 0.50,
            "counter": (
                "Challenge each alleged incident with documentation. "
                "Many 'incidents' are lawful parenting activities or "
                "child-safety reports reframed as harassment."
            ),
        },
    ],
    "section_1983": [
        {
            "objection": "Judicial immunity (Stump v. Sparkman)",
            "probability": 0.80,
            "counter": (
                "Argue acts were administrative, not judicial. Ex parte "
                "grants without statutory authority are not protected "
                "judicial acts. Cite Mireles v. Waco exceptions."
            ),
        },
        {
            "objection": "Younger abstention — federal court should abstain",
            "probability": 0.65,
            "counter": (
                "Younger does not apply when state proceedings violate "
                "due process or are conducted in bad faith. Document "
                "specific due-process violations."
            ),
        },
        {
            "objection": "Rooker-Feldman — cannot appeal state judgment in federal court",
            "probability": 0.60,
            "counter": (
                "Claim challenges the process (due process violation), "
                "not the outcome. Rooker-Feldman bars only de facto "
                "appeals, not independent constitutional claims."
            ),
        },
    ],
    "jtc_complaint": [
        {
            "objection": "Conduct is within judicial discretion",
            "probability": 0.65,
            "counter": (
                "Ex parte orders at 3.65× normal rate exceed any "
                "reasonable exercise of discretion. Statistical evidence "
                "of bias is not mere disagreement with rulings."
            ),
        },
    ],
    "appellate_brief": [
        {
            "objection": "Issue not preserved for appeal",
            "probability": 0.70,
            "counter": (
                "Demonstrate contemporaneous objection in trial-court "
                "record. For unpreserved issues, argue plain error "
                "affecting substantial rights."
            ),
        },
        {
            "objection": "Abuse of discretion standard not met",
            "probability": 0.60,
            "counter": (
                "Present de novo issues separately. For abuse-of-discretion "
                "issues, show outcome falls outside range of reasonable "
                "outcomes."
            ),
        },
    ],
    "malicious_prosecution": [
        {
            "objection": "PPO filing was made in good faith",
            "probability": 0.65,
            "counter": (
                "Timeline shows PPO filings are retaliatory — filed "
                "immediately after Andrew exercises parental rights. "
                "Lack of independent corroboration undermines good faith."
            ),
        },
    ],
}

# Counter-motion predictions per filing type
_COUNTER_MOTION_TEMPLATES: Dict[str, List[Dict[str, Any]]] = {
    "custody_modification": [
        {
            "motion": "Emergency motion for temporary custody",
            "probability": 0.55,
            "defense": (
                "Prepare response showing no emergency exists and "
                "that motion is retaliatory. File within 7 days."
            ),
        },
        {
            "motion": "Motion to dismiss for failure to show changed circumstances",
            "probability": 0.45,
            "defense": (
                "Pre-file affidavit documenting 305 interference incidents "
                "as material change in circumstances."
            ),
        },
    ],
    "motion_disqualification": [
        {
            "motion": "Motion to strike disqualification motion as untimely",
            "probability": 0.50,
            "defense": (
                "File declaration explaining when statistical pattern "
                "became apparent and why filing was timely."
            ),
        },
    ],
    "contempt_motion": [
        {
            "motion": "Cross-motion for contempt against Andrew",
            "probability": 0.40,
            "defense": (
                "Maintain meticulous compliance records. Any cross-motion "
                "must allege specific violations — prepare point-by-point "
                "rebuttal."
            ),
        },
        {
            "motion": "Motion to modify custody/parenting time",
            "probability": 0.35,
            "defense": (
                "Argue any modification requires proper motion and "
                "best-interest analysis, not reactive filing."
            ),
        },
    ],
    "housing_complaint": [
        {
            "motion": "Motion to dismiss under MCR 2.116(C)(8)",
            "probability": 0.70,
            "defense": (
                "Ensure complaint satisfies all elements of each claim. "
                "Pre-draft response to MTD citing specific factual "
                "allegations."
            ),
        },
        {
            "motion": "Motion to quash service",
            "probability": 0.50,
            "defense": (
                "Use certified mail, personal service, and process server "
                "with detailed affidavit to preclude service challenges."
            ),
        },
    ],
    "section_1983": [
        {
            "motion": "Motion to dismiss on immunity grounds",
            "probability": 0.80,
            "defense": (
                "Brief should pre-emptively address both absolute and "
                "qualified immunity with circuit-specific case law."
            ),
        },
        {
            "motion": "Motion to abstain under Younger",
            "probability": 0.60,
            "defense": (
                "Include bad-faith exception argument in original "
                "complaint. Document specific due-process violations."
            ),
        },
    ],
    "rico_complaint": [
        {
            "motion": "Motion to dismiss RICO for failure to plead with particularity",
            "probability": 0.75,
            "defense": (
                "Plead predicate acts with specificity required by "
                "Rule 9(b): who, what, when, where, how for each "
                "fraudulent act."
            ),
        },
    ],
    "ppo_defense": [
        {
            "motion": "Motion for extension of PPO",
            "probability": 0.45,
            "defense": (
                "Challenge each allegation. Request evidentiary hearing "
                "under MCL 600.2950(12). Document absence of qualifying "
                "conduct."
            ),
        },
    ],
}

# Timeline estimates for adversary responses
_RESPONSE_TIMELINES: Dict[str, str] = {
    "custody_modification": "14-28 days (answer period under MCR 2.108)",
    "motion_disqualification": "7-14 days (MCR 2.003 expedited)",
    "contempt_motion": "14-21 days (motion response period)",
    "housing_complaint": "21-28 days (answer period under MCR 2.108)",
    "rico_complaint": "21-28 days (answer period)",
    "ppo_defense": "Immediate — ex parte possible within 24 hours",
    "section_1983": "21-60 days (federal answer period FRCP 12)",
    "jtc_complaint": "60-90 days (JTC investigation timeline)",
    "appellate_brief": "28-56 days (appellee brief period MCR 7.212)",
    "malicious_prosecution": "21-28 days (answer period)",
    "fha_complaint": "21-60 days (federal answer period)",
}


# ---------------------------------------------------------------------------
# Data Classes
# ---------------------------------------------------------------------------

@dataclass
class AdversaryProfile:
    """Profile of a known adversary with behavioural patterns."""

    name: str
    role: str
    known_patterns: List[str] = field(default_factory=list)
    predicted_strategy: str = ""
    confidence: float = 0.0

    def to_dict(self) -> dict:
        """Serialize to plain dictionary."""
        return asdict(self)


@dataclass
class PredictedResponse:
    """Prediction for a single filing type."""

    filing_type: str
    likely_objections: List[Dict[str, Any]] = field(default_factory=list)
    likely_motions: List[Dict[str, Any]] = field(default_factory=list)
    timeline_estimate: str = "unknown"
    risk_assessment: str = "medium"
    recommended_preemptive: List[str] = field(default_factory=list)

    def to_dict(self) -> dict:
        """Serialize to plain dictionary."""
        return asdict(self)


@dataclass
class AdversaryReport:
    """Full adversary prediction report for a filing."""

    filing_id: str
    generated_at: str = field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )
    predictions: List[PredictedResponse] = field(default_factory=list)
    overall_risk: str = "medium"
    strategic_recommendations: List[str] = field(default_factory=list)

    def to_dict(self) -> dict:
        """Serialize to plain dictionary."""
        return asdict(self)


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


def _make_id(*parts: str) -> str:
    """Deterministic report ID from content parts."""
    raw = "|".join(str(p) for p in parts)
    return hashlib.sha256(raw.encode()).hexdigest()[:12]


# ---------------------------------------------------------------------------
# AdversaryPredictor
# ---------------------------------------------------------------------------

class AdversaryPredictor:
    """Predict opposing counsel strategies and likely responses.

    Analyses known adversary behavioural patterns from the Pigors v. Watson
    litigation and generates probabilistic predictions for likely objections,
    counter-motions, and recommended preemptive actions for any given
    filing type.
    """

    def __init__(self, db_path: Optional[Path] = None) -> None:
        self._db_path = db_path or _DB_PATH
        self._prediction_count: int = 0
        self._last_report: Optional[AdversaryReport] = None
        logger.info("AdversaryPredictor initialized (db=%s)", self._db_path)

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def predict_response(
        self,
        filing_type: str,
        court: str = "14th_circuit",
        lane: str = "A",
    ) -> AdversaryReport:
        """Generate a full adversary prediction report for a filing.

        Parameters
        ----------
        filing_type : str
            The type of filing being prepared (e.g. ``custody_modification``).
        court : str
            Court identifier (e.g. ``14th_circuit``, ``coa``, ``federal``).
        lane : str
            Case lane A–F.

        Returns
        -------
        AdversaryReport
            Report containing predictions, risk assessment, and
            strategic recommendations.
        """
        lane = lane.upper()
        filing_id = _make_id(filing_type, court, lane)

        predictions: List[PredictedResponse] = []

        # Build primary prediction for the filing type
        primary = self._build_prediction(filing_type, court, lane)
        predictions.append(primary)

        # Also predict for related filing types
        related = self._get_related_filings(filing_type, lane)
        for related_ft in related:
            pred = self._build_prediction(related_ft, court, lane)
            predictions.append(pred)

        # Overall risk
        risk_scores = [self._risk_to_score(p.risk_assessment) for p in predictions]
        avg_risk = sum(risk_scores) / max(len(risk_scores), 1)
        overall_risk = self._score_to_risk(avg_risk)

        # Strategic recommendations
        recommendations = self._build_recommendations(filing_type, lane, predictions)

        report = AdversaryReport(
            filing_id=filing_id,
            predictions=predictions,
            overall_risk=overall_risk,
            strategic_recommendations=recommendations,
        )
        self._prediction_count += 1
        self._last_report = report
        return report

    def get_adversary_profile(self, name_or_role: str) -> AdversaryProfile:
        """Look up an adversary profile by name fragment or role keyword.

        Parameters
        ----------
        name_or_role : str
            A name (e.g. ``"Watson"``), role (e.g. ``"judge"``), or
            key (e.g. ``"foc"``).

        Returns
        -------
        AdversaryProfile
            The matching profile with patterns and strategy.
        """
        key = name_or_role.lower().strip()

        # Direct key match
        if key in _PROFILE_INDEX:
            return self._profile_from_data(_PROFILE_INDEX[key])

        # Fuzzy match on name or role
        for pkey, pdata in _PROFILE_INDEX.items():
            if key in pdata["name"].lower() or key in pdata["role"].lower():
                return self._profile_from_data(pdata)

        logger.warning("No adversary profile found for %r", name_or_role)
        return AdversaryProfile(
            name=name_or_role,
            role="unknown",
            known_patterns=[],
            predicted_strategy="No pattern data available for this adversary.",
            confidence=0.0,
        )

    def predict_objections(self, filing_type: str) -> List[Dict[str, Any]]:
        """Return likely objections for a filing type.

        Parameters
        ----------
        filing_type : str
            Filing type key.

        Returns
        -------
        list of dict
            Each dict has ``objection``, ``probability``, and ``counter``.
        """
        templates = _OBJECTION_TEMPLATES.get(filing_type, [])
        if not templates:
            logger.info("No objection templates for %s", filing_type)
        # Return copies sorted by probability descending
        return sorted(
            [dict(t) for t in templates],
            key=lambda x: x.get("probability", 0),
            reverse=True,
        )

    def predict_counter_motions(self, filing_type: str) -> List[Dict[str, Any]]:
        """Return likely counter-motions for a filing type.

        Parameters
        ----------
        filing_type : str
            Filing type key.

        Returns
        -------
        list of dict
            Each dict has ``motion``, ``probability``, and ``defense``.
        """
        templates = _COUNTER_MOTION_TEMPLATES.get(filing_type, [])
        if not templates:
            logger.info("No counter-motion templates for %s", filing_type)
        return sorted(
            [dict(t) for t in templates],
            key=lambda x: x.get("probability", 0),
            reverse=True,
        )

    def generate_preemptive_strategy(self, filing_type: str) -> List[str]:
        """Generate preemptive actions to take before filing.

        Parameters
        ----------
        filing_type : str
            Filing type key.

        Returns
        -------
        list of str
            Ordered list of preemptive steps.
        """
        strategies: List[str] = []

        # General preemptive steps
        strategies.append(
            "Verify all service requirements before filing (MCR 2.105/2.107)."
        )
        strategies.append(
            "Run pre-filing QA sweep (completeness scorer + brief compliance)."
        )

        # Filing-specific preemptive steps
        objections = self.predict_objections(filing_type)
        for obj in objections:
            if obj.get("probability", 0) >= 0.60:
                strategies.append(
                    f"Pre-address likely objection: '{obj['objection']}' — "
                    f"{obj.get('counter', 'prepare counter-argument')}"
                )

        counter_motions = self.predict_counter_motions(filing_type)
        for cm in counter_motions:
            if cm.get("probability", 0) >= 0.50:
                strategies.append(
                    f"Prepare defense for likely counter-motion: '{cm['motion']}' — "
                    f"{cm.get('defense', 'prepare response brief')}"
                )

        # Adversary-specific steps
        _FILING_ADVERSARY_MAP: Dict[str, List[str]] = {
            "custody_modification": ["watson", "judge", "foc"],
            "motion_disqualification": ["judge"],
            "contempt_motion": ["watson", "judge"],
            "housing_complaint": ["housing"],
            "rico_complaint": ["housing"],
            "ppo_defense": ["watson", "judge"],
            "section_1983": ["judge"],
            "jtc_complaint": ["judge"],
            "appellate_brief": ["watson", "judge"],
            "malicious_prosecution": ["watson"],
        }
        adversaries = _FILING_ADVERSARY_MAP.get(filing_type, [])
        for adv_key in adversaries:
            profile = _PROFILE_INDEX.get(adv_key)
            if not profile:
                continue
            for p in profile["patterns"]:
                if filing_type in p.get("trigger_filings", []):
                    if p.get("probability", 0) >= 0.55:
                        strategies.append(
                            f"Anticipate {profile['name']}: {p['pattern']}"
                        )
                    if p.get("fabrication_warning"):
                        strategies.append(
                            f"⚠ FABRICATION ALERT: {p['fabrication_warning']}"
                        )

        # Deduplicate while preserving order
        seen: Set[str] = set()
        unique: List[str] = []
        for s in strategies:
            if s not in seen:
                seen.add(s)
                unique.append(s)
        return unique

    def assess_risk(self, filing_type: str, lane: str = "A") -> str:
        """Assess overall risk level for a filing type in a lane.

        Parameters
        ----------
        filing_type : str
            Filing type key.
        lane : str
            Case lane A–F.

        Returns
        -------
        str
            Risk level: ``"critical"``, ``"high"``, ``"medium"``, or ``"low"``.
        """
        lane = lane.upper()
        risk_score = 0.0
        count = 0

        # Factor in objection probabilities
        for obj in _OBJECTION_TEMPLATES.get(filing_type, []):
            risk_score += obj.get("probability", 0.5)
            count += 1

        # Factor in counter-motion probabilities
        for cm in _COUNTER_MOTION_TEMPLATES.get(filing_type, []):
            risk_score += cm.get("probability", 0.5)
            count += 1

        # Factor in adversary pattern activation
        for profile_data in _PROFILE_INDEX.values():
            for p in profile_data["patterns"]:
                if filing_type in p.get("trigger_filings", []):
                    if lane in p.get("lanes", []):
                        risk_score += p.get("probability", 0.5)
                        count += 1

        # Factor in judicial bias for relevant lanes
        if lane in ("A", "D", "E"):
            for p in _MCNEILL_PATTERNS:
                if filing_type in p.get("trigger_filings", []):
                    risk_score += p.get("probability", 0.5) * 1.2  # weight judicial bias higher
                    count += 1

        avg = risk_score / max(count, 1)
        return self._score_to_risk(avg)

    def get_stats(self) -> Dict[str, Any]:
        """Return engine statistics."""
        return {
            "engine": "AdversaryPredictor",
            "version": "1.0.0",
            "db_path": str(self._db_path),
            "db_exists": self._db_path.exists(),
            "prediction_count": self._prediction_count,
            "last_report_at": (
                self._last_report.generated_at if self._last_report else None
            ),
            "profiles_loaded": len(_PROFILE_INDEX),
            "profile_names": [p["name"] for p in _PROFILE_INDEX.values()],
            "objection_templates": {
                ft: len(objs) for ft, objs in _OBJECTION_TEMPLATES.items()
            },
            "counter_motion_templates": {
                ft: len(cms) for ft, cms in _COUNTER_MOTION_TEMPLATES.items()
            },
            "filing_types_covered": sorted(
                set(_OBJECTION_TEMPLATES.keys()) | set(_COUNTER_MOTION_TEMPLATES.keys())
            ),
        }

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _build_prediction(
        self, filing_type: str, court: str, lane: str
    ) -> PredictedResponse:
        """Build a single PredictedResponse for a filing type."""
        objections = self.predict_objections(filing_type)
        counter_motions = self.predict_counter_motions(filing_type)
        preemptive = self.generate_preemptive_strategy(filing_type)
        timeline = _RESPONSE_TIMELINES.get(filing_type, "21-28 days (default answer period)")
        risk = self.assess_risk(filing_type, lane)

        return PredictedResponse(
            filing_type=filing_type,
            likely_objections=objections,
            likely_motions=counter_motions,
            timeline_estimate=timeline,
            risk_assessment=risk,
            recommended_preemptive=preemptive,
        )

    def _get_related_filings(self, filing_type: str, lane: str) -> List[str]:
        """Return filing types that are likely to be triggered by the given filing.

        For example, filing a custody_modification may trigger a
        retaliatory PPO filing.
        """
        _TRIGGER_MAP: Dict[str, List[str]] = {
            "custody_modification": ["ppo_defense"],
            "contempt_motion": ["ppo_defense"],
            "parenting_time_enforcement": ["ppo_defense"],
            "motion_disqualification": ["section_1983"],
            "housing_complaint": ["rico_complaint"],
        }
        related = _TRIGGER_MAP.get(filing_type, [])
        # Filter to only include related types that have templates
        return [
            r for r in related
            if r in _OBJECTION_TEMPLATES or r in _COUNTER_MOTION_TEMPLATES
        ]

    def _profile_from_data(self, data: Dict[str, Any]) -> AdversaryProfile:
        """Convert profile data dict to AdversaryProfile dataclass."""
        patterns = data.get("patterns", [])
        pattern_strs = [p["pattern"] for p in patterns]
        avg_prob = (
            sum(p.get("probability", 0.5) for p in patterns) / max(len(patterns), 1)
        )
        return AdversaryProfile(
            name=data["name"],
            role=data["role"],
            known_patterns=pattern_strs,
            predicted_strategy=data.get("strategy", ""),
            confidence=round(avg_prob, 3),
        )

    def _build_recommendations(
        self,
        filing_type: str,
        lane: str,
        predictions: List[PredictedResponse],
    ) -> List[str]:
        """Build strategic recommendations from predictions."""
        recs: List[str] = []

        # High-probability objection prep
        for pred in predictions:
            for obj in pred.likely_objections:
                if obj.get("probability", 0) >= 0.70:
                    recs.append(
                        f"Address '{obj['objection']}' proactively in your {pred.filing_type}."
                    )

        # Counter-motion preparation
        for pred in predictions:
            for cm in pred.likely_motions:
                if cm.get("probability", 0) >= 0.50:
                    recs.append(
                        f"Pre-draft response to anticipated {cm['motion']}."
                    )

        # Lane-specific recommendations
        if lane == "A":
            recs.append(
                "Keep parenting-time interference log current (305+ incidents documented)."
            )
            recs.append(
                "Maintain proof of all lawful conduct to rebut harassment claims."
            )
        elif lane == "B":
            recs.append(
                "Use multiple service methods (personal + certified mail + process server)."
            )
            recs.append(
                "Document all utility overcharges with billing records."
            )
        elif lane == "D":
            recs.append(
                "CRITICAL: If opposing party claims '9 CPS investigations', "
                "rebut immediately — this is FABRICATED. Single CPS call + police reports."
            )
        elif lane == "E":
            recs.append(
                "File JTC complaint before or simultaneously with disqualification "
                "to create independent record of misconduct."
            )
        elif lane == "F":
            recs.append(
                "Verify every appellate issue was preserved in the trial court record."
            )

        # General recommendations
        recs.append(
            "File proof of service simultaneously with every filing."
        )
        recs.append(
            "Calendar all response deadlines immediately upon filing."
        )

        # Deduplicate
        seen: Set[str] = set()
        unique: List[str] = []
        for r in recs:
            if r not in seen:
                seen.add(r)
                unique.append(r)
        return unique

    @staticmethod
    def _risk_to_score(risk: str) -> float:
        """Convert risk label to numeric score."""
        return {
            "critical": 0.90,
            "high": 0.70,
            "medium": 0.50,
            "low": 0.25,
        }.get(risk, 0.50)

    @staticmethod
    def _score_to_risk(score: float) -> str:
        """Convert numeric score to risk label."""
        if score >= 0.75:
            return "critical"
        if score >= 0.60:
            return "high"
        if score >= 0.40:
            return "medium"
        return "low"
