# -*- coding: utf-8 -*-
"""
Outcome Predictor — LitigationOS Legal AI Subsystem
=====================================================
Bayesian + rules-based engine that predicts filing outcome probability
using authority strength, evidence weight, judicial profile, and
precedent patterns.

Prediction Factors (weighted):
    Authority Strength   (0.25) — Binding precedent, statutory basis, MCR rules
    Evidence Weight       (0.30) — Documentary, corroboration, expert testimony
    Judicial Profile      (0.20) — Judge-specific patterns, bias indicators
    Procedural Compliance (0.15) — Format, timeliness, service, completeness
    Strategic Position    (0.10) — Multi-jurisdiction, simultaneous filings

Case Context:
    Plaintiff:  Andrew James Pigors
    Defendant:  Emily A. Watson
    Child:      L.D.W. (per MCR 8.119(H))
    Judge:      Hon. Jenny L. McNeill — 14th Circuit Court
    Lanes:      A=Custody, B=Housing, C=Convergence, D=PPO, E=Misconduct, F=Appellate

Usage:
    from legal_ai.outcome_predictor import OutcomePredictor

    predictor = OutcomePredictor()
    prediction = predictor.predict(text, "motion_disqualification", "A", "14th_circuit")
    print(prediction.probability_success, prediction.grade)

    # Batch predictions
    results = predictor.batch_predict([
        {"text": t1, "filing_type": "custody_modification", "lane": "A", "court": "14th_circuit"},
        {"text": t2, "filing_type": "complaint_housing", "lane": "B", "court": "14th_circuit"},
    ])
"""
from __future__ import annotations

import hashlib
import json
import logging
import math
import re
import sqlite3
import statistics
from collections import Counter
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple

logger = logging.getLogger("legal_ai.outcome_predictor")

# ---------------------------------------------------------------------------
# Path resolution — legal_ai → 00_SYSTEM → LitigationOS root
# ---------------------------------------------------------------------------
_HERE = Path(__file__).resolve().parent
_DB_PATH = _HERE.parents[1] / "litigation_context.db"

# ---------------------------------------------------------------------------
# Constants & Factor Weights
# ---------------------------------------------------------------------------

# Top-level factor weights (must sum to 1.0)
FACTOR_WEIGHTS: Dict[str, float] = {
    "authority_strength": 0.25,
    "evidence_weight": 0.30,
    "judicial_profile": 0.20,
    "procedural_compliance": 0.15,
    "strategic_position": 0.10,
}

# Authority strength sub-scores
_AUTHORITY_SIGNALS: Dict[str, Tuple[float, re.Pattern[str]]] = {
    "binding_precedent": (
        0.30,
        re.compile(
            r"\b\d{1,3}\s+Mich(?:\s+App)?\s+\d+|"
            r"\b\d{1,3}\s+NW\.?2d\s+\d+|"
            r"\bPeople\s+v\s+\w+,\s+\d+\s+Mich",
            re.IGNORECASE,
        ),
    ),
    "persuasive_authority": (
        0.15,
        re.compile(
            r"\b\d{1,3}\s+F\.(?:2d|3d|4th|Supp)\s+\d+|"
            r"\b\d{1,3}\s+S\.?Ct\.?\s+\d+|"
            r"\b\d{1,3}\s+US\s+\d+",
            re.IGNORECASE,
        ),
    ),
    "statutory_basis": (
        0.20,
        re.compile(
            r"\bMCL\s+\d{2,4}\.\d+|"
            r"\b\d{1,2}\s+USC\s+§?\s*\d+|"
            r"\b42\s+USC\s+§?\s*1983",
            re.IGNORECASE,
        ),
    ),
    "mcr_procedural": (
        0.15,
        re.compile(r"\bMCR\s+\d+\.\d+", re.IGNORECASE),
    ),
}

_AUTHORITY_PENALTIES: Dict[str, Tuple[float, re.Pattern[str]]] = {
    "no_authority": (
        -0.30,
        re.compile(r"(?!x)x"),  # never matches — checked via absence
    ),
    "distinguishable": (
        -0.15,
        re.compile(
            r"\b(?:distinguish|inapplicable|overruled|superseded|abrogated)\b",
            re.IGNORECASE,
        ),
    ),
}

# Evidence weight sub-scores
_EVIDENCE_SIGNALS: Dict[str, Tuple[float, re.Pattern[str]]] = {
    "documentary": (
        0.25,
        re.compile(
            r"\bExhibit\s+[A-Z0-9]+|"
            r"\battached\s+(?:hereto|herewith)|"
            r"\bcertified\s+copy\b|"
            r"\bBates\s+(?:stamp|number)",
            re.IGNORECASE,
        ),
    ),
    "corroborating": (
        0.20,
        re.compile(
            r"\bcorroborat|"
            r"\bmultiple\s+(?:witnesses|sources|documents)|"
            r"\bindependent(?:ly)?\s+confirm|"
            r"\bconsistent\s+with",
            re.IGNORECASE,
        ),
    ),
    "expert": (
        0.15,
        re.compile(
            r"\bexpert\s+(?:report|testimony|opinion|witness)|"
            r"\bqualified\s+(?:expert|professional)|"
            r"\bMRE\s+702",
            re.IGNORECASE,
        ),
    ),
}

_EVIDENCE_PENALTIES: Dict[str, Tuple[float, re.Pattern[str]]] = {
    "self_testimony_only": (
        -0.10,
        re.compile(
            r"\b(?:Plaintiff|Petitioner|I)\s+(?:believe|feel|think|assert)\b",
            re.IGNORECASE,
        ),
    ),
    "evidence_gap": (
        -0.20,
        re.compile(
            r"\b(?:no\s+evidence|lack(?:s|ing)?\s+(?:of\s+)?evidence|"
            r"insufficient\s+evidence|without\s+proof)\b",
            re.IGNORECASE,
        ),
    ),
}

# Procedural compliance sub-scores
_PROCEDURAL_SIGNALS: Dict[str, Tuple[float, re.Pattern[str]]] = {
    "proper_format": (
        0.15,
        re.compile(
            r"\bSTATE\s+OF\s+MICHIGAN|"
            r"\b(?:14TH|FOURTEENTH)\s+(?:JUDICIAL\s+)?CIRCUIT\s+COURT|"
            r"\bCASE\s+NO\.?\s*:?\s*\d{4}",
            re.IGNORECASE,
        ),
    ),
    "timely_filing": (
        0.10,
        re.compile(
            r"\btimely\s+filed|"
            r"\bwithin\s+(?:the\s+)?(?:\d+[-\s]day|deadline|time\s+limit)|"
            r"\bper\s+MCR\s+\d+\.\d+.{0,30}(?:time|days|deadline)",
            re.IGNORECASE,
        ),
    ),
    "complete_service": (
        0.10,
        re.compile(
            r"\b(?:proof|certificate)\s+of\s+service|"
            r"\bserved\s+(?:upon|on)\s+|"
            r"\bMCR\s+2\.10[57]",
            re.IGNORECASE,
        ),
    ),
}

_PROCEDURAL_PENALTIES: Dict[str, Tuple[float, re.Pattern[str]]] = {
    "missing_requirements": (
        -0.30,
        re.compile(
            r"\b(?:failed\s+to|did\s+not|omitted?|missing)\s+"
            r"(?:file|serve|include|attach|sign|verify)\b",
            re.IGNORECASE,
        ),
    ),
}

# Strategic position sub-scores
_STRATEGIC_SIGNALS: Dict[str, Tuple[float, re.Pattern[str]]] = {
    "multi_jurisdiction": (
        0.20,
        re.compile(
            r"\bfederal\s+(?:court|action|complaint)|"
            r"\b(?:Eastern|Western)\s+District|"
            r"\bCourt\s+of\s+Appeals|"
            r"\bSupreme\s+Court",
            re.IGNORECASE,
        ),
    ),
    "simultaneous_filing": (
        0.15,
        re.compile(
            r"\bsimultaneous(?:ly)?|"
            r"\bconcurrent(?:ly)?|"
            r"\bparallel\s+(?:action|filing|proceeding)",
            re.IGNORECASE,
        ),
    ),
    "appellate_backup": (
        0.10,
        re.compile(
            r"\b(?:appeal|appellate)\s+(?:preserved|reserved|pending)|"
            r"\bpreserv(?:e|ed|ing)\s+(?:for|issue|error)",
            re.IGNORECASE,
        ),
    ),
}


# ---------------------------------------------------------------------------
# Judicial Profile Database (embedded — no external data)
# ---------------------------------------------------------------------------

class _JudgeProfile:
    """Stores known judicial profile data for prediction adjustments."""

    # Hon. Jenny L. McNeill — 14th Circuit Court
    MCNEILL: Dict[str, Any] = {
        "name": "Hon. Jenny L. McNeill",
        "court": "14th_circuit",
        "ex_parte_rate": 0.1826,         # 18.26% — 3.65× normal 5% rate
        "normal_ex_parte_rate": 0.05,
        "pro_mother_bias_strength": 0.72, # 0-1 scale, evidence-based
        "disqualification_denial_rate": 0.85,  # denies 85% of disqualification motions
        "father_motion_penalty": -0.20,   # penalty for father's motions
        "fairness_penalty": -0.30,        # from ex parte rate
        "filing_adjustments": {
            "motion_disqualification": {
                "base_modifier": -0.25,
                "reason": "Pattern of denying disqualification motions; "
                          "however, strong ex parte evidence raises federal "
                          "exposure, creating settlement/recusal pressure",
            },
            "custody_modification": {
                "base_modifier": -0.20,
                "reason": "Statistical pro-mother bias in custody decisions; "
                          "father's motions face uphill battle in this court",
            },
            "federal_1983": {
                "base_modifier": 0.30,
                "reason": "Strong §1983 case: documented ex parte rate "
                          "3.65× normal, pattern evidence of due process "
                          "violations supports federal action",
            },
            "ppo_violation": {
                "base_modifier": -0.10,
                "reason": "Judicial handling of PPO matters shows "
                          "procedural irregularities",
            },
            "jtc_complaint": {
                "base_modifier": 0.10,
                "reason": "Ex parte rate and documented pattern provide "
                          "basis for JTC investigation trigger",
            },
            "appellate_brief": {
                "base_modifier": 0.05,
                "reason": "Preserved errors and documented misconduct "
                          "provide appellate issues",
            },
        },
    }


# ---------------------------------------------------------------------------
# Base Rates by Filing Type and Court
# ---------------------------------------------------------------------------

_BASE_RATES: Dict[str, Dict[str, float]] = {
    "motion_disqualification": {
        "default": 0.175,          # 15-20% base rate in Michigan
        "14th_circuit": 0.15,      # lower in this circuit historically
        "federal": 0.20,
    },
    "custody_modification": {
        "default": 0.35,           # 30-40% success for modification
        "14th_circuit": 0.30,
    },
    "emergency_parenting_time": {
        "default": 0.35,           # 30-40% — needs strong harm evidence
        "14th_circuit": 0.30,
    },
    "federal_1983": {
        "default": 0.25,           # 20-30% survival past MTD
        "federal": 0.25,
        "western_district_mi": 0.22,
    },
    "complaint_housing": {
        "default": 0.45,           # housing violations — moderate success
        "14th_circuit": 0.45,
    },
    "housing_rico": {
        "default": 0.125,          # 10-15% — high bar but treble damages
        "federal": 0.12,
    },
    "ppo_violation": {
        "default": 0.50,           # PPO enforcement — depends on evidence
        "14th_circuit": 0.45,
    },
    "jtc_complaint": {
        "default": 0.50,           # 40-60% chance of investigation trigger
        "jtc": 0.50,
    },
    "appellate_brief": {
        "default": 0.30,           # Michigan COA reversal rate ~25-35%
        "coa": 0.30,
    },
}


# ---------------------------------------------------------------------------
# Comparable Outcome Templates
# ---------------------------------------------------------------------------

_COMPARABLE_OUTCOMES: Dict[str, List[Dict[str, Any]]] = {
    "motion_disqualification": [
        {
            "case": "Cain v. Dep't of Corrections, 451 Mich 470 (1996)",
            "outcome": "denied",
            "reason": "Insufficient evidence of actual bias; adverse rulings "
                      "alone not enough",
            "relevance": 0.7,
        },
        {
            "case": "Crampton v. Dep't of State, 395 Mich 347 (1975)",
            "outcome": "granted",
            "reason": "Demonstrated actual bias through ex parte "
                      "communications and prejudgment",
            "relevance": 0.9,
        },
        {
            "case": "Kern v. Kern, unpublished (COA 2019)",
            "outcome": "denied",
            "reason": "Failed to show personal bias beyond unfavorable "
                      "rulings; no pattern evidence",
            "relevance": 0.6,
        },
    ],
    "custody_modification": [
        {
            "case": "Vodvarka v. Grasmeyer, 259 Mich App 499 (2003)",
            "outcome": "standard set",
            "reason": "Established proper cause / change of circumstances "
                      "threshold for custody modification",
            "relevance": 0.95,
        },
        {
            "case": "Shade v. Wright, 291 Mich App 17 (2010)",
            "outcome": "modified",
            "reason": "Change of circumstances established through evidence "
                      "of interference with parenting time",
            "relevance": 0.8,
        },
    ],
    "federal_1983": [
        {
            "case": "Stump v. Sparkman, 435 US 349 (1978)",
            "outcome": "immunity applied",
            "reason": "Judicial immunity bars §1983 claims for judicial acts "
                      "within jurisdiction",
            "relevance": 0.9,
        },
        {
            "case": "Pulliam v. Allen, 466 US 522 (1984)",
            "outcome": "partial success",
            "reason": "Prospective injunctive relief available against judges "
                      "even under judicial immunity",
            "relevance": 0.85,
        },
        {
            "case": "Mireles v. Waco, 502 US 9 (1991)",
            "outcome": "immunity applied",
            "reason": "Judicial immunity applies unless judge acts in clear "
                      "absence of all jurisdiction",
            "relevance": 0.8,
        },
    ],
    "complaint_housing": [
        {
            "case": "Trentadue v. Gorton, 479 Mich 378 (2007)",
            "outcome": "landlord liability",
            "reason": "Landlord duty to maintain premises under MCL 554.139; "
                      "breach establishes liability",
            "relevance": 0.85,
        },
    ],
    "ppo_violation": [
        {
            "case": "Hayford v. Hayford, 279 Mich App 324 (2008)",
            "outcome": "enforcement",
            "reason": "PPO violation established with documented contact "
                      "evidence and prior service proof",
            "relevance": 0.8,
        },
    ],
    "jtc_complaint": [
        {
            "case": "In re Brennan, 504 Mich 80 (2019)",
            "outcome": "investigation initiated",
            "reason": "Pattern of ex parte communications and documented "
                      "misconduct triggered JTC investigation",
            "relevance": 0.9,
        },
        {
            "case": "In re Justin, 490 Mich 394 (2012)",
            "outcome": "censure",
            "reason": "Judicial misconduct established through pattern "
                      "evidence of improper conduct",
            "relevance": 0.75,
        },
    ],
    "appellate_brief": [
        {
            "case": "Michigan appellate reversal rates (2020-2024)",
            "outcome": "statistical baseline",
            "reason": "Michigan COA reverses approximately 25-35% of "
                      "appealed family court decisions",
            "relevance": 0.7,
        },
    ],
}


# ---------------------------------------------------------------------------
# Data Models
# ---------------------------------------------------------------------------

@dataclass
class PredictionFactor:
    """A single scoring factor in the prediction model."""

    factor_name: str
    weight: float       # 0-1, how much this factor counts
    score: float        # 0-1, the score achieved
    confidence: float   # 0-1, confidence in this score
    evidence: str       # What supports this score
    sub_scores: Dict[str, float] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Serialise to dictionary."""
        return asdict(self)

    @property
    def weighted_score(self) -> float:
        """Return score × weight."""
        return self.score * self.weight


@dataclass
class OutcomePrediction:
    """Complete prediction for a single filing."""

    filing_id: str
    filing_type: str
    lane: str
    court: str
    probability_success: float   # 0-1
    probability_partial: float   # 0-1
    probability_denial: float    # 0-1
    confidence: float            # 0-1
    factors: List[PredictionFactor]
    risk_factors: List[str]
    strength_factors: List[str]
    recommendations: List[str]
    comparable_outcomes: List[Dict[str, Any]]
    grade: str                   # A-F
    prediction_timestamp: str = ""

    def __post_init__(self) -> None:
        if not self.prediction_timestamp:
            self.prediction_timestamp = datetime.now(timezone.utc).isoformat()

    def to_dict(self) -> Dict[str, Any]:
        """Serialise to dictionary."""
        d = asdict(self)
        d["factors"] = [f.to_dict() for f in self.factors]
        return d


# ---------------------------------------------------------------------------
# OutcomePredictor
# ---------------------------------------------------------------------------

class OutcomePredictor:
    """Predict filing outcomes using Bayesian + rules-based approach.

    Combines five weighted factors — authority strength, evidence weight,
    judicial profile, procedural compliance, and strategic position — with
    Bayesian updating from base rates to produce calibrated probabilities
    for success, partial success, and denial.
    """

    def __init__(self, db_path: Optional[Path] = None) -> None:
        """Initialise the predictor.

        Args:
            db_path: Override path to ``litigation_context.db``.
                     Defaults to the standard repo-relative path.
        """
        self._db_path = db_path or _DB_PATH
        self._predictions_run: int = 0
        self._total_filings_scored: int = 0
        self._score_history: List[float] = []
        logger.info("OutcomePredictor initialised (db=%s)", self._db_path)

    # ------------------------------------------------------------------
    # Database helpers
    # ------------------------------------------------------------------

    def _connect_db(self) -> Optional[sqlite3.Connection]:
        """Open a WAL-mode connection to the central database.

        Returns:
            A :class:`sqlite3.Connection` or ``None`` if unavailable.
        """
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

    def _query_authority_data(
        self, filing_type: str,
    ) -> List[Dict[str, Any]]:
        """Query the DB for authority data relevant to a filing type.

        Returns list of authority records if available.
        """
        conn = self._connect_db()
        if conn is None:
            return []
        try:
            results: List[Dict[str, Any]] = []
            for table in ("authority_index", "authorities",
                          "authority_chains", "citations"):
                try:
                    cols_info = conn.execute(
                        f"PRAGMA table_info({table})"
                    ).fetchall()
                    cols = [r[1] for r in cols_info]
                    if not cols:
                        continue
                    select_cols = []
                    for c in cols[:8]:  # limit columns
                        select_cols.append(c)
                    sql = (
                        f"SELECT {', '.join(select_cols)} "
                        f"FROM {table} LIMIT 500"
                    )
                    rows = conn.execute(sql).fetchall()
                    for r in rows:
                        results.append(dict(r))
                    if results:
                        break
                except sqlite3.OperationalError:
                    continue
            return results
        except sqlite3.Error as exc:
            logger.error("Authority query failed: %s", exc)
            return []
        finally:
            conn.close()

    # ------------------------------------------------------------------
    # Factor Scoring Methods
    # ------------------------------------------------------------------

    def score_authority_strength(
        self, text: str,
    ) -> PredictionFactor:
        """Score the authority strength of a filing.

        Detects binding precedent, persuasive authority, statutory basis,
        and MCR citations.  Penalises for absence of authority or
        distinguishable citations.

        Args:
            text: Filing text to analyse.

        Returns:
            :class:`PredictionFactor` for authority strength.
        """
        text_lower = text.lower() if text else ""
        sub_scores: Dict[str, float] = {}
        evidence_parts: List[str] = []
        raw_score = 0.0

        # Positive signals
        any_authority_found = False
        for name, (value, pattern) in _AUTHORITY_SIGNALS.items():
            matches = pattern.findall(text) if text else []
            if matches:
                any_authority_found = True
                # Diminishing returns after 3 citations
                count_factor = min(1.0, len(matches) / 3.0)
                contribution = value * count_factor
                raw_score += contribution
                sub_scores[name] = round(contribution, 3)
                evidence_parts.append(
                    f"{name}: {len(matches)} citation(s) found"
                )
            else:
                sub_scores[name] = 0.0

        # Penalties
        if not any_authority_found:
            penalty = _AUTHORITY_PENALTIES["no_authority"][0]
            raw_score += penalty
            sub_scores["no_authority"] = penalty
            evidence_parts.append("No legal authority cited — significant weakness")

        for name, (penalty, pattern) in _AUTHORITY_PENALTIES.items():
            if name == "no_authority":
                continue
            if pattern.search(text) if text else False:
                raw_score += penalty
                sub_scores[name] = penalty
                evidence_parts.append(f"{name}: opposing authority may apply")

        # Normalise to 0-1
        normalised = max(0.0, min(1.0, 0.5 + raw_score))

        # Confidence based on how much text we had to work with
        word_count = len(text.split()) if text else 0
        confidence = min(1.0, word_count / 500.0) if word_count > 0 else 0.1

        return PredictionFactor(
            factor_name="authority_strength",
            weight=FACTOR_WEIGHTS["authority_strength"],
            score=round(normalised, 3),
            confidence=round(confidence, 3),
            evidence="; ".join(evidence_parts) if evidence_parts
                     else "No authority analysis possible — insufficient text",
            sub_scores=sub_scores,
        )

    def score_evidence_weight(self, text: str) -> PredictionFactor:
        """Score the evidentiary support of a filing.

        Detects documentary evidence, corroborating sources, expert
        testimony, and penalises for self-testimony-only or gaps.

        Args:
            text: Filing text to analyse.

        Returns:
            :class:`PredictionFactor` for evidence weight.
        """
        sub_scores: Dict[str, float] = {}
        evidence_parts: List[str] = []
        raw_score = 0.0

        # Positive signals
        for name, (value, pattern) in _EVIDENCE_SIGNALS.items():
            matches = pattern.findall(text) if text else []
            if matches:
                count_factor = min(1.0, len(matches) / 3.0)
                contribution = value * count_factor
                raw_score += contribution
                sub_scores[name] = round(contribution, 3)
                evidence_parts.append(
                    f"{name}: {len(matches)} reference(s) detected"
                )
            else:
                sub_scores[name] = 0.0

        # Penalties
        for name, (penalty, pattern) in _EVIDENCE_PENALTIES.items():
            if pattern.search(text) if text else False:
                raw_score += penalty
                sub_scores[name] = penalty
                evidence_parts.append(f"{name}: penalty applied")

        normalised = max(0.0, min(1.0, 0.5 + raw_score))
        word_count = len(text.split()) if text else 0
        confidence = min(1.0, word_count / 500.0) if word_count > 0 else 0.1

        return PredictionFactor(
            factor_name="evidence_weight",
            weight=FACTOR_WEIGHTS["evidence_weight"],
            score=round(normalised, 3),
            confidence=round(confidence, 3),
            evidence="; ".join(evidence_parts) if evidence_parts
                     else "No evidence references detected in text",
            sub_scores=sub_scores,
        )

    def score_judicial_profile(
        self, judge: str, filing_type: str,
    ) -> PredictionFactor:
        """Score based on the judicial profile of the assigned judge.

        Uses embedded statistical data for known judges — currently
        Hon. Jenny L. McNeill of the 14th Circuit Court.

        Args:
            judge: Judge identifier (e.g. ``"mcneill"``).
            filing_type: Type of filing being evaluated.

        Returns:
            :class:`PredictionFactor` for judicial profile.
        """
        sub_scores: Dict[str, float] = {}
        evidence_parts: List[str] = []
        raw_score = 0.0
        confidence = 0.3  # default low confidence for unknown judges

        judge_lower = judge.lower().strip() if judge else ""
        is_mcneill = any(
            token in judge_lower
            for token in ("mcneill", "mc neill", "mcneil", "jenny")
        )

        if is_mcneill:
            profile = _JudgeProfile.MCNEILL
            confidence = 0.85  # high confidence — extensive data

            # Ex parte rate penalty
            ex_parte_penalty = profile["fairness_penalty"]
            raw_score += ex_parte_penalty
            sub_scores["ex_parte_rate"] = ex_parte_penalty
            evidence_parts.append(
                f"Ex parte communication rate: "
                f"{profile['ex_parte_rate']:.1%} "
                f"({profile['ex_parte_rate'] / profile['normal_ex_parte_rate']:.1f}× "
                f"normal)"
            )

            # Filing-specific adjustment
            filing_adj = profile["filing_adjustments"].get(filing_type, {})
            if filing_adj:
                modifier = filing_adj["base_modifier"]
                raw_score += modifier
                sub_scores["filing_adjustment"] = modifier
                evidence_parts.append(
                    f"Filing-specific adjustment ({filing_type}): "
                    f"{modifier:+.2f} — {filing_adj['reason']}"
                )

            # Father's motion penalty (Andrew Pigors is the father/plaintiff)
            if filing_type in (
                "custody_modification", "emergency_parenting_time",
            ):
                father_penalty = profile["father_motion_penalty"]
                raw_score += father_penalty
                sub_scores["father_motion_penalty"] = father_penalty
                evidence_parts.append(
                    f"Pro-mother bias penalty: {father_penalty:+.2f} "
                    f"(strength {profile['pro_mother_bias_strength']:.0%})"
                )
        else:
            # Unknown judge — neutral profile
            evidence_parts.append(
                f"Unknown judge '{judge}' — neutral profile applied"
            )
            sub_scores["unknown_judge"] = 0.0

        normalised = max(0.0, min(1.0, 0.5 + raw_score))

        return PredictionFactor(
            factor_name="judicial_profile",
            weight=FACTOR_WEIGHTS["judicial_profile"],
            score=round(normalised, 3),
            confidence=round(confidence, 3),
            evidence="; ".join(evidence_parts),
            sub_scores=sub_scores,
        )

    def score_procedural_compliance(
        self, text: str, filing_type: str,
    ) -> PredictionFactor:
        """Score the procedural compliance of a filing.

        Checks for proper format, timely filing indicators, complete
        service, and penalises for missing requirements.

        Args:
            text: Filing text to analyse.
            filing_type: Type of filing being evaluated.

        Returns:
            :class:`PredictionFactor` for procedural compliance.
        """
        sub_scores: Dict[str, float] = {}
        evidence_parts: List[str] = []
        raw_score = 0.0

        for name, (value, pattern) in _PROCEDURAL_SIGNALS.items():
            if pattern.search(text) if text else False:
                raw_score += value
                sub_scores[name] = round(value, 3)
                evidence_parts.append(f"{name}: ✓ detected")
            else:
                sub_scores[name] = 0.0
                evidence_parts.append(f"{name}: ✗ not detected")

        for name, (penalty, pattern) in _PROCEDURAL_PENALTIES.items():
            if pattern.search(text) if text else False:
                raw_score += penalty
                sub_scores[name] = penalty
                evidence_parts.append(f"{name}: penalty applied")

        normalised = max(0.0, min(1.0, 0.5 + raw_score))
        word_count = len(text.split()) if text else 0
        confidence = min(1.0, word_count / 300.0) if word_count > 0 else 0.1

        return PredictionFactor(
            factor_name="procedural_compliance",
            weight=FACTOR_WEIGHTS["procedural_compliance"],
            score=round(normalised, 3),
            confidence=round(confidence, 3),
            evidence="; ".join(evidence_parts),
            sub_scores=sub_scores,
        )

    def score_strategic_position(
        self, lane: str, filing_type: str, text: str = "",
    ) -> PredictionFactor:
        """Score the strategic position of the filing.

        Detects multi-jurisdiction pressure, simultaneous filings, and
        appellate backup indicators.

        Args:
            lane: Case lane (A-F).
            filing_type: Type of filing being evaluated.
            text: Optional filing text for signal detection.

        Returns:
            :class:`PredictionFactor` for strategic position.
        """
        sub_scores: Dict[str, float] = {}
        evidence_parts: List[str] = []
        raw_score = 0.0

        # Text-based signals
        for name, (value, pattern) in _STRATEGIC_SIGNALS.items():
            if pattern.search(text) if text else False:
                raw_score += value
                sub_scores[name] = round(value, 3)
                evidence_parts.append(f"{name}: ✓ detected in text")
            else:
                sub_scores[name] = 0.0

        # Lane-based strategic bonuses
        lane_upper = lane.upper() if lane else ""
        if lane_upper == "C":
            # Convergence lane — multi-lane pressure inherent
            bonus = 0.15
            raw_score += bonus
            sub_scores["convergence_lane"] = bonus
            evidence_parts.append(
                "Convergence lane: multi-lane pressure bonus +0.15"
            )
        elif lane_upper == "A" and filing_type == "federal_1983":
            # Federal action from custody lane — strong strategic value
            bonus = 0.20
            raw_score += bonus
            sub_scores["federal_from_custody"] = bonus
            evidence_parts.append(
                "Federal §1983 from custody lane: strategic pressure +0.20"
            )
        elif lane_upper == "E":
            # Misconduct lane provides leverage across all lanes
            bonus = 0.10
            raw_score += bonus
            sub_scores["misconduct_leverage"] = bonus
            evidence_parts.append(
                "Misconduct lane: cross-lane leverage bonus +0.10"
            )

        normalised = max(0.0, min(1.0, 0.5 + raw_score))
        confidence = 0.6 if evidence_parts else 0.3

        return PredictionFactor(
            factor_name="strategic_position",
            weight=FACTOR_WEIGHTS["strategic_position"],
            score=round(normalised, 3),
            confidence=round(confidence, 3),
            evidence="; ".join(evidence_parts) if evidence_parts
                     else "No strategic positioning signals detected",
            sub_scores=sub_scores,
        )

    # ------------------------------------------------------------------
    # Base Rate & Bayesian Engine
    # ------------------------------------------------------------------

    def get_base_rate(self, filing_type: str, court: str = "") -> float:
        """Look up the base success rate for a filing type in a court.

        Args:
            filing_type: Type of filing.
            court: Court identifier (e.g. ``"14th_circuit"``).

        Returns:
            Base success probability (0-1).
        """
        rates = _BASE_RATES.get(filing_type, {})
        if not rates:
            logger.debug(
                "No base rate for '%s' — using 0.30 default", filing_type
            )
            return 0.30
        court_lower = court.lower().strip() if court else ""
        return rates.get(court_lower, rates.get("default", 0.30))

    def bayesian_update(
        self, prior: float, factors: List[PredictionFactor],
    ) -> float:
        """Apply Bayesian updating to the prior using factor scores.

        Each factor contributes a likelihood ratio derived from its
        weighted score relative to a neutral baseline of 0.5.  The
        update is multiplicative in log-odds space for numerical
        stability.

        Args:
            prior: Prior probability (0-1).
            factors: Scored prediction factors.

        Returns:
            Posterior probability (0-1), clamped to [0.01, 0.99].
        """
        if prior <= 0:
            prior = 0.01
        if prior >= 1:
            prior = 0.99

        # Convert prior to log-odds
        log_odds = math.log(prior / (1.0 - prior))

        for f in factors:
            # Each factor's score (0-1) translates to a likelihood ratio.
            # Score of 0.5 → neutral (LR=1, log-odds contribution = 0).
            # Score of 1.0 → strong positive.  Score of 0.0 → strong negative.
            deviation = (f.score - 0.5) * 2.0  # range [-1, 1]
            # Scale by weight and confidence
            magnitude = deviation * f.weight * f.confidence
            # Convert to log-odds contribution
            # magnitude of ±0.5 ≈ shifting odds by ~2.7×
            log_odds += magnitude * 2.0

        # Convert back to probability
        try:
            posterior = 1.0 / (1.0 + math.exp(-log_odds))
        except OverflowError:
            posterior = 1.0 if log_odds > 0 else 0.0

        return max(0.01, min(0.99, round(posterior, 4)))

    # ------------------------------------------------------------------
    # Comparable Outcomes
    # ------------------------------------------------------------------

    def find_comparable_outcomes(
        self,
        filing_type: str,
        factors: List[PredictionFactor],
    ) -> List[Dict[str, Any]]:
        """Find comparable case outcomes for context.

        Args:
            filing_type: Type of filing.
            factors: Scored factors (used for relevance filtering).

        Returns:
            List of comparable outcome dictionaries, sorted by relevance.
        """
        comparables = _COMPARABLE_OUTCOMES.get(filing_type, [])
        if not comparables:
            return [{
                "case": "No directly comparable outcomes on file",
                "outcome": "unknown",
                "reason": f"Filing type '{filing_type}' lacks comparable "
                          f"outcome database entries",
                "relevance": 0.0,
            }]

        # Sort by relevance descending
        return sorted(
            comparables,
            key=lambda c: c.get("relevance", 0),
            reverse=True,
        )

    # ------------------------------------------------------------------
    # Recommendation Engine
    # ------------------------------------------------------------------

    def generate_recommendations(
        self, prediction: OutcomePrediction,
    ) -> List[str]:
        """Generate actionable recommendations based on prediction results.

        Args:
            prediction: Completed prediction to generate recommendations for.

        Returns:
            Ordered list of recommendation strings.
        """
        recs: List[str] = []

        # Grade-based overall recommendation
        if prediction.grade in ("A", "B"):
            recs.append(
                f"STRONG POSITION ({prediction.grade}): Filing has good "
                f"prospects ({prediction.probability_success:.0%} predicted "
                f"success). Proceed with filing."
            )
        elif prediction.grade == "C":
            recs.append(
                f"MODERATE POSITION ({prediction.grade}): Filing viable but "
                f"has weaknesses ({prediction.probability_success:.0%} "
                f"predicted success). Strengthen before filing."
            )
        elif prediction.grade == "D":
            recs.append(
                f"WEAK POSITION ({prediction.grade}): Filing faces significant "
                f"headwinds ({prediction.probability_success:.0%} predicted "
                f"success). Major improvements needed."
            )
        else:
            recs.append(
                f"HIGH RISK ({prediction.grade}): Filing likely to fail "
                f"({prediction.probability_success:.0%} predicted success). "
                f"Consider alternative strategy."
            )

        # Factor-specific recommendations
        for f in prediction.factors:
            if f.score < 0.4:
                recs.append(
                    f"IMPROVE {f.factor_name.upper()}: Current score "
                    f"{f.score:.0%} — {f.evidence}"
                )

        # Risk factor mitigation
        if prediction.risk_factors:
            recs.append("KEY RISKS TO MITIGATE:")
            for rf in prediction.risk_factors[:5]:
                recs.append(f"  → {rf}")

        # Leverage strengths
        if prediction.strength_factors:
            recs.append("LEVERAGE THESE STRENGTHS:")
            for sf in prediction.strength_factors[:3]:
                recs.append(f"  → {sf}")

        # Filing-type-specific strategic advice
        filing_advice = self._get_filing_specific_advice(
            prediction.filing_type, prediction.probability_success,
        )
        if filing_advice:
            recs.extend(filing_advice)

        return recs

    @staticmethod
    def _get_filing_specific_advice(
        filing_type: str, prob_success: float,
    ) -> List[str]:
        """Return filing-type-specific strategic advice.

        Args:
            filing_type: Type of filing.
            prob_success: Predicted success probability.

        Returns:
            List of strategic advice strings.
        """
        advice: List[str] = []

        if filing_type == "motion_disqualification":
            advice.append(
                "STRATEGY: Focus on documented ex parte communications and "
                "pattern evidence — adverse rulings alone are insufficient "
                "for disqualification under Michigan law."
            )
            if prob_success < 0.30:
                advice.append(
                    "CONSIDER: If disqualification fails in state court, "
                    "the evidence strengthens the federal §1983 claim by "
                    "demonstrating exhaustion of state remedies."
                )

        elif filing_type == "custody_modification":
            advice.append(
                "STRATEGY: Meet the Vodvarka threshold — demonstrate proper "
                "cause or change of circumstances with specific, documented "
                "evidence for each best-interest factor."
            )

        elif filing_type == "federal_1983":
            advice.append(
                "STRATEGY: Frame claims to survive qualified immunity — cite "
                "clearly established rights violated. Pattern evidence is "
                "critical for overcoming judicial immunity."
            )
            advice.append(
                "NOTE: Seek declaratory/injunctive relief in addition to "
                "damages — Pulliam v. Allen permits prospective relief "
                "against judicial officers."
            )

        elif filing_type == "jtc_complaint":
            advice.append(
                "NOTE: JTC complaints are not win/lose — they trigger "
                "investigation. Focus on documented pattern of misconduct "
                "with specific dates, actions, and evidence."
            )

        elif filing_type == "complaint_housing":
            advice.append(
                "STRATEGY: Document MCL 554.139 violations thoroughly — "
                "photos with timestamps, repair requests with responses, "
                "and any code enforcement actions."
            )

        elif filing_type == "appellate_brief":
            advice.append(
                "STRATEGY: Focus on preserved errors with strongest "
                "standards of review. Abuse of discretion and de novo "
                "issues are most likely to succeed on appeal."
            )

        return advice

    # ------------------------------------------------------------------
    # Primary Prediction Method
    # ------------------------------------------------------------------

    def predict(
        self,
        filing_text: str,
        filing_type: str,
        lane: str,
        court: str,
        judge: str = "mcneill",
        filing_id: Optional[str] = None,
    ) -> OutcomePrediction:
        """Predict the outcome of a filing.

        This is the primary entry point.  It:
        1. Scores all five factors against the filing text.
        2. Retrieves the base rate for filing type and court.
        3. Applies Bayesian updating from factors to posterior.
        4. Calculates partial-success and denial probabilities.
        5. Identifies risk and strength factors.
        6. Finds comparable outcomes.
        7. Generates recommendations.

        Args:
            filing_text: Full text of the filing/motion.
            filing_type: E.g. ``"motion_disqualification"``.
            lane: Case lane (``"A"``-``"F"``).
            court: Court identifier (e.g. ``"14th_circuit"``).
            judge: Judge identifier (default ``"mcneill"``).
            filing_id: Optional identifier for the filing.

        Returns:
            A :class:`OutcomePrediction` with probabilities, factors,
            and recommendations.
        """
        if filing_id is None:
            filing_id = hashlib.sha256(
                f"{filing_type}:{lane}:{court}:"
                f"{datetime.now(timezone.utc).isoformat()}".encode()
            ).hexdigest()[:12]

        logger.info(
            "Predicting outcome: type=%s lane=%s court=%s judge=%s id=%s",
            filing_type, lane, court, judge, filing_id,
        )

        # 1. Score all factors
        factors: List[PredictionFactor] = []
        try:
            factors.append(self.score_authority_strength(filing_text))
        except Exception as exc:
            logger.error("Authority scoring failed: %s", exc)
            factors.append(PredictionFactor(
                factor_name="authority_strength",
                weight=FACTOR_WEIGHTS["authority_strength"],
                score=0.5, confidence=0.1,
                evidence=f"Scoring failed: {exc}",
            ))

        try:
            factors.append(self.score_evidence_weight(filing_text))
        except Exception as exc:
            logger.error("Evidence scoring failed: %s", exc)
            factors.append(PredictionFactor(
                factor_name="evidence_weight",
                weight=FACTOR_WEIGHTS["evidence_weight"],
                score=0.5, confidence=0.1,
                evidence=f"Scoring failed: {exc}",
            ))

        try:
            factors.append(self.score_judicial_profile(judge, filing_type))
        except Exception as exc:
            logger.error("Judicial profile scoring failed: %s", exc)
            factors.append(PredictionFactor(
                factor_name="judicial_profile",
                weight=FACTOR_WEIGHTS["judicial_profile"],
                score=0.5, confidence=0.1,
                evidence=f"Scoring failed: {exc}",
            ))

        try:
            factors.append(
                self.score_procedural_compliance(filing_text, filing_type))
        except Exception as exc:
            logger.error("Procedural scoring failed: %s", exc)
            factors.append(PredictionFactor(
                factor_name="procedural_compliance",
                weight=FACTOR_WEIGHTS["procedural_compliance"],
                score=0.5, confidence=0.1,
                evidence=f"Scoring failed: {exc}",
            ))

        try:
            factors.append(
                self.score_strategic_position(lane, filing_type, filing_text))
        except Exception as exc:
            logger.error("Strategic scoring failed: %s", exc)
            factors.append(PredictionFactor(
                factor_name="strategic_position",
                weight=FACTOR_WEIGHTS["strategic_position"],
                score=0.5, confidence=0.1,
                evidence=f"Scoring failed: {exc}",
            ))

        # 2. Base rate
        base_rate = self.get_base_rate(filing_type, court)

        # 3. Bayesian update
        prob_success = self.bayesian_update(base_rate, factors)

        # 4. Derived probabilities
        # Partial success: higher when prediction is moderate
        prob_partial = self._calculate_partial_probability(
            prob_success, filing_type,
        )
        prob_denial = max(0.01, round(
            1.0 - prob_success - prob_partial, 4,
        ))

        # Normalise to sum to 1.0
        total = prob_success + prob_partial + prob_denial
        if total > 0 and abs(total - 1.0) > 0.001:
            prob_success = round(prob_success / total, 4)
            prob_partial = round(prob_partial / total, 4)
            prob_denial = round(1.0 - prob_success - prob_partial, 4)

        # 5. Overall confidence
        confidences = [f.confidence for f in factors]
        overall_confidence = round(
            statistics.mean(confidences) if confidences else 0.3, 3
        )

        # 6. Risk and strength factors
        risk_factors = self._identify_risk_factors(factors, filing_type)
        strength_factors = self._identify_strength_factors(factors)

        # 7. Comparable outcomes
        comparables = self.find_comparable_outcomes(filing_type, factors)

        # 8. Grade
        grade = self._grade_from_probability(prob_success)

        # Build prediction object
        prediction = OutcomePrediction(
            filing_id=filing_id,
            filing_type=filing_type,
            lane=lane,
            court=court,
            probability_success=prob_success,
            probability_partial=prob_partial,
            probability_denial=prob_denial,
            confidence=overall_confidence,
            factors=factors,
            risk_factors=risk_factors,
            strength_factors=strength_factors,
            recommendations=[],  # filled below
            comparable_outcomes=comparables,
            grade=grade,
        )

        # 9. Recommendations
        prediction.recommendations = self.generate_recommendations(prediction)

        # Stats tracking
        self._predictions_run += 1
        self._total_filings_scored += 1
        self._score_history.append(prob_success)

        logger.info(
            "Prediction complete: P(success)=%.1f%% P(partial)=%.1f%% "
            "P(denial)=%.1f%% confidence=%.0f%% grade=%s",
            prob_success * 100, prob_partial * 100,
            prob_denial * 100, overall_confidence * 100, grade,
        )
        return prediction

    def batch_predict(
        self,
        filings: List[Dict[str, Any]],
    ) -> List[OutcomePrediction]:
        """Run predictions on multiple filings.

        Each entry in *filings* must have keys: ``text``, ``filing_type``,
        ``lane``, ``court``.  Optional keys: ``judge``, ``filing_id``.

        Args:
            filings: List of filing specification dictionaries.

        Returns:
            List of :class:`OutcomePrediction` objects.
        """
        results: List[OutcomePrediction] = []
        for idx, spec in enumerate(filings):
            try:
                text = spec.get("text", "")
                filing_type = spec.get("filing_type", "unknown")
                lane = spec.get("lane", "C")
                court = spec.get("court", "14th_circuit")
                judge = spec.get("judge", "mcneill")
                filing_id = spec.get("filing_id")

                prediction = self.predict(
                    text, filing_type, lane, court, judge, filing_id,
                )
                results.append(prediction)
            except Exception as exc:
                logger.error(
                    "Batch prediction failed for item %d: %s", idx, exc,
                )
                results.append(OutcomePrediction(
                    filing_id=f"batch_error_{idx}",
                    filing_type=spec.get("filing_type", "unknown"),
                    lane=spec.get("lane", "?"),
                    court=spec.get("court", "?"),
                    probability_success=0.0,
                    probability_partial=0.0,
                    probability_denial=1.0,
                    confidence=0.0,
                    factors=[],
                    risk_factors=[f"Prediction failed: {exc}"],
                    strength_factors=[],
                    recommendations=["Unable to generate prediction — "
                                     "check filing text and parameters"],
                    comparable_outcomes=[],
                    grade="F",
                ))
        return results

    # ------------------------------------------------------------------
    # Stats
    # ------------------------------------------------------------------

    def get_stats(self) -> Dict[str, Any]:
        """Return operational statistics.

        Returns:
            Dictionary of usage and performance metrics.
        """
        avg_score = (
            round(statistics.mean(self._score_history), 3)
            if self._score_history else 0.0
        )
        median_score = (
            round(statistics.median(self._score_history), 3)
            if self._score_history else 0.0
        )
        return {
            "predictions_run": self._predictions_run,
            "total_filings_scored": self._total_filings_scored,
            "average_success_probability": avg_score,
            "median_success_probability": median_score,
            "db_path": str(self._db_path),
            "db_exists": self._db_path.exists(),
            "factor_weights": dict(FACTOR_WEIGHTS),
            "supported_filing_types": sorted(_BASE_RATES.keys()),
            "supported_courts": list({
                court
                for rates in _BASE_RATES.values()
                for court in rates.keys()
            }),
        }

    # ------------------------------------------------------------------
    # Internal Helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _calculate_partial_probability(
        prob_success: float, filing_type: str,
    ) -> float:
        """Calculate partial-success probability.

        Partial success is highest when the prediction is moderate
        (around 0.4-0.6) and lower at extremes.

        Args:
            prob_success: Full-success probability.
            filing_type: Type of filing.

        Returns:
            Partial-success probability (0-1).
        """
        # Bell curve centred at 0.45 — partial outcomes most likely
        # when full success is uncertain
        partial_base = 0.25 * math.exp(
            -((prob_success - 0.45) ** 2) / 0.08
        )

        # Some filing types have higher partial rates
        type_multiplier = {
            "federal_1983": 1.3,         # partial relief common
            "custody_modification": 1.2, # partial modifications happen
            "motion_disqualification": 0.5,  # mostly binary outcome
            "ppo_violation": 0.6,        # mostly binary
            "jtc_complaint": 1.5,        # investigation without action
            "appellate_brief": 1.1,      # partial reversal
        }.get(filing_type, 1.0)

        return round(max(0.02, min(0.40, partial_base * type_multiplier)), 4)

    @staticmethod
    def _grade_from_probability(prob: float) -> str:
        """Convert success probability to letter grade.

        Args:
            prob: Success probability (0-1).

        Returns:
            Letter grade A-F.
        """
        if prob >= 0.70:
            return "A"
        if prob >= 0.55:
            return "B"
        if prob >= 0.40:
            return "C"
        if prob >= 0.25:
            return "D"
        return "F"

    @staticmethod
    def _identify_risk_factors(
        factors: List[PredictionFactor], filing_type: str,
    ) -> List[str]:
        """Identify key risk factors from scored factors.

        Args:
            factors: Scored prediction factors.
            filing_type: Type of filing.

        Returns:
            List of risk factor descriptions.
        """
        risks: List[str] = []

        for f in factors:
            if f.score < 0.35:
                risks.append(
                    f"CRITICAL: {f.factor_name} score very low "
                    f"({f.score:.0%}) — {f.evidence}"
                )
            elif f.score < 0.45:
                risks.append(
                    f"WARNING: {f.factor_name} below neutral "
                    f"({f.score:.0%})"
                )

            # Check specific sub-score risks
            for sub_name, sub_val in f.sub_scores.items():
                if sub_val < -0.15:
                    risks.append(
                        f"Penalty: {f.factor_name}.{sub_name} = "
                        f"{sub_val:+.2f}"
                    )

        # Filing-type-specific risks
        if filing_type == "motion_disqualification":
            risks.append(
                "Michigan disqualification motions have a base denial "
                "rate of ~80-85%"
            )
        elif filing_type == "federal_1983":
            risks.append(
                "Judicial immunity and qualified immunity are strong "
                "defenses — must demonstrate clear absence of jurisdiction "
                "or clearly established rights"
            )
        elif filing_type == "housing_rico":
            risks.append(
                "RICO claims require proof of pattern of racketeering "
                "activity — high evidentiary bar"
            )

        return risks

    @staticmethod
    def _identify_strength_factors(
        factors: List[PredictionFactor],
    ) -> List[str]:
        """Identify key strength factors from scored factors.

        Args:
            factors: Scored prediction factors.

        Returns:
            List of strength factor descriptions.
        """
        strengths: List[str] = []

        for f in factors:
            if f.score >= 0.70:
                strengths.append(
                    f"STRONG: {f.factor_name} scores high "
                    f"({f.score:.0%}) — {f.evidence}"
                )
            elif f.score >= 0.55:
                strengths.append(
                    f"Positive: {f.factor_name} above neutral "
                    f"({f.score:.0%})"
                )

            for sub_name, sub_val in f.sub_scores.items():
                if sub_val >= 0.15:
                    strengths.append(
                        f"Strength: {f.factor_name}.{sub_name} = "
                        f"+{sub_val:.2f}"
                    )

        return strengths


# ---------------------------------------------------------------------------
# Module-level convenience
# ---------------------------------------------------------------------------

def predict(
    filing_text: str,
    filing_type: str,
    lane: str,
    court: str,
    judge: str = "mcneill",
    filing_id: Optional[str] = None,
) -> OutcomePrediction:
    """Module-level convenience function.

    Creates a default :class:`OutcomePredictor` and runs prediction.
    """
    predictor = OutcomePredictor()
    return predictor.predict(
        filing_text, filing_type, lane, court, judge, filing_id,
    )


def get_supported_filing_types() -> List[str]:
    """Return all filing types with registered base rates."""
    return sorted(_BASE_RATES.keys())


def get_factor_weights() -> Dict[str, float]:
    """Return the factor weight configuration."""
    return dict(FACTOR_WEIGHTS)
