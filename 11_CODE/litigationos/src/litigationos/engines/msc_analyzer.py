"""MSC Application Strength Analyzer.

Evaluates potential issues for a Michigan Supreme Court application for
leave to appeal or original action under MCR 7.305(B).  Scores each issue
on six dimensions (constitutional significance, conflict with precedent,
statewide importance, factual strength, novelty, practical impact), ranks
them, and recommends a filing strategy.

The MSC grants only ~5 % of applications.  This engine helps prioritise
issues so the strongest are presented first and weak issues are identified
early.  All analysis is local-only — no network calls.
"""

from __future__ import annotations

import logging
from datetime import datetime
from enum import Enum
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Constants — MCR 7.305(B) grant criteria
# ---------------------------------------------------------------------------

MSC_GRANT_CRITERIA: dict[str, str] = {
    "major_legal_principle": (
        "The case involves a legal principle of major significance to the "
        "state's jurisprudence (MCR 7.305(B)(1))."
    ),
    "conflict_with_msc_coa": (
        "The Court of Appeals decision is clearly in conflict with a "
        "prior decision of the Supreme Court or another panel of the "
        "Court of Appeals (MCR 7.305(B)(2))."
    ),
    "conflict_with_federal": (
        "The Court of Appeals decision is in conflict with a ruling of "
        "a federal court on a question of federal law (MCR 7.305(B)(3))."
    ),
    "constitutional_question": (
        "The case involves a constitutional question of major significance "
        "(MCR 7.305(B)(4))."
    ),
    "superintending_control": (
        "The Supreme Court should exercise its superintending-control "
        "authority under Const 1963, art 6, § 4 (MCR 7.305(B)(5))."
    ),
}

# Scoring dimensions and their weights (used in weighted-average total).
SCORING_DIMENSIONS: dict[str, float] = {
    "constitutional_significance": 2.0,
    "conflict_with_precedent": 1.8,
    "statewide_importance": 1.5,
    "factual_strength": 1.3,
    "novelty": 1.0,
    "practical_impact": 1.4,
}

# Thresholds for recommendation tiers.
STRONG_THRESHOLD = 7.0
MODERATE_THRESHOLD = 5.0
WEAK_THRESHOLD = 3.0

# ---------------------------------------------------------------------------
# Pre-loaded issues for Pigors v Watson
# ---------------------------------------------------------------------------

PIGORS_V_WATSON_ISSUES: list[dict] = [
    {
        "name": "Ex parte custody suspension without hearing",
        "description": (
            "Custody/parenting time suspended ex parte without notice or "
            "opportunity to be heard, violating procedural due process "
            "under US Const Amend XIV and Mich Const 1963 art 1, § 17."
        ),
        "mcr_criteria": [
            "constitutional_question",
            "major_legal_principle",
            "superintending_control",
        ],
        "baseline_scores": {
            "constitutional_significance": 9,
            "conflict_with_precedent": 7,
            "statewide_importance": 8,
            "factual_strength": 8,
            "novelty": 6,
            "practical_impact": 9,
        },
    },
    {
        "name": "Berry-McNeill conflict of interest / judicial disqualification",
        "description": (
            "Judge McNeill's prior professional relationship with "
            "Ronald Berry (Emily Watson's domestic partner) creates an "
            "appearance of impropriety requiring disqualification under "
            "MCR 2.003(C)(1)(b)."
        ),
        "mcr_criteria": [
            "major_legal_principle",
            "superintending_control",
        ],
        "baseline_scores": {
            "constitutional_significance": 7,
            "conflict_with_precedent": 6,
            "statewide_importance": 7,
            "factual_strength": 7,
            "novelty": 7,
            "practical_impact": 8,
        },
    },
    {
        "name": "Three-court judicial nexus (Ladas-Hoopes-McNeill)",
        "description": (
            "Three judges from the same former law firm presided over "
            "interconnected proceedings involving the same parties, "
            "raising structural due-process and appearance-of-impropriety "
            "concerns under MCR 2.003 and Caperton v A.T. Massey Coal, "
            "556 US 868 (2009)."
        ),
        "mcr_criteria": [
            "constitutional_question",
            "major_legal_principle",
            "conflict_with_federal",
        ],
        "baseline_scores": {
            "constitutional_significance": 8,
            "conflict_with_precedent": 5,
            "statewide_importance": 8,
            "factual_strength": 6,
            "novelty": 9,
            "practical_impact": 7,
        },
    },
    {
        "name": "Parenting time termination without Vodvarka factors",
        "description": (
            "Parenting time terminated without applying the required "
            "Vodvarka v Grasmeyer, 259 Mich App 499 (2003) factors, "
            "which mandate a showing of proper cause or change in "
            "circumstances before modifying a parenting-time order."
        ),
        "mcr_criteria": [
            "major_legal_principle",
            "conflict_with_msc_coa",
        ],
        "baseline_scores": {
            "constitutional_significance": 6,
            "conflict_with_precedent": 8,
            "statewide_importance": 7,
            "factual_strength": 8,
            "novelty": 4,
            "practical_impact": 9,
        },
    },
    {
        "name": "Forced HealthWest evaluation as condition of parenting time",
        "description": (
            "Court ordered mandatory mental-health evaluation at "
            "HealthWest as a precondition to any parenting time, "
            "implicating substantive due-process rights in the "
            "parent-child relationship and the right to refuse "
            "involuntary mental-health treatment."
        ),
        "mcr_criteria": [
            "constitutional_question",
            "major_legal_principle",
        ],
        "baseline_scores": {
            "constitutional_significance": 8,
            "conflict_with_precedent": 5,
            "statewide_importance": 7,
            "factual_strength": 7,
            "novelty": 7,
            "practical_impact": 8,
        },
    },
    {
        "name": "PPO weaponization / contempt without proper service",
        "description": (
            "Contempt sanctions imposed for alleged PPO violations where "
            "the underlying PPO was not properly served under "
            "MCR 3.706(H)(1), violating procedural due process."
        ),
        "mcr_criteria": [
            "major_legal_principle",
            "conflict_with_msc_coa",
            "superintending_control",
        ],
        "baseline_scores": {
            "constitutional_significance": 7,
            "conflict_with_precedent": 8,
            "statewide_importance": 6,
            "factual_strength": 7,
            "novelty": 5,
            "practical_impact": 8,
        },
    },
]


# ---------------------------------------------------------------------------
# Enums
# ---------------------------------------------------------------------------


class FilingStrategy(str, Enum):
    """Recommended MSC filing vehicle."""

    LEAVE_TO_APPEAL = "Application for Leave to Appeal"
    ORIGINAL_ACTION = "Original Action / Complaint for Superintending Control"
    BOTH = "Dual Filing — Leave to Appeal + Original Action"
    HOLD = "Hold — Strengthen Record Before Filing"


class StrengthTier(str, Enum):
    """Qualitative strength rating."""

    STRONG = "Strong"
    MODERATE = "Moderate"
    WEAK = "Weak"
    INSUFFICIENT = "Insufficient"


# ---------------------------------------------------------------------------
# Pydantic models
# ---------------------------------------------------------------------------


class IssueScore(BaseModel):
    """Scored evaluation of a single MSC issue."""

    model_config = ConfigDict(from_attributes=True)

    issue_name: str
    description: Optional[str] = None
    scores: dict[str, int] = Field(
        default_factory=dict,
        description="Dimension name → 0-10 score.",
    )
    total: float = Field(
        default=0.0,
        description="Weighted average across all dimensions (0-10 scale).",
    )
    tier: StrengthTier = StrengthTier.INSUFFICIENT
    mcr_criteria_met: list[str] = Field(default_factory=list)
    recommendation: str = ""
    questions_presented: Optional[str] = None

    def compute_total(self) -> None:
        """Recompute *total* and *tier* from current dimension scores."""
        if not self.scores:
            self.total = 0.0
            self.tier = StrengthTier.INSUFFICIENT
            return

        weighted_sum = 0.0
        weight_sum = 0.0
        for dim, weight in SCORING_DIMENSIONS.items():
            value = self.scores.get(dim, 0)
            weighted_sum += value * weight
            weight_sum += weight

        self.total = round(weighted_sum / weight_sum, 2) if weight_sum else 0.0
        self.tier = _tier_for_score(self.total)


class OverallAssessment(BaseModel):
    """Aggregate assessment across all scored issues."""

    model_config = ConfigDict(from_attributes=True)

    issues: list[IssueScore] = Field(default_factory=list)
    avg_score: float = 0.0
    top_issues: list[str] = Field(default_factory=list)
    strategy: str = ""
    filing_recommendation: FilingStrategy = FilingStrategy.HOLD
    assessed_at: datetime = Field(default_factory=datetime.now)
    notes: str = ""


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------


def _tier_for_score(score: float) -> StrengthTier:
    if score >= STRONG_THRESHOLD:
        return StrengthTier.STRONG
    if score >= MODERATE_THRESHOLD:
        return StrengthTier.MODERATE
    if score >= WEAK_THRESHOLD:
        return StrengthTier.WEAK
    return StrengthTier.INSUFFICIENT


def _build_recommendation(issue_name: str, total: float, tier: StrengthTier) -> str:
    """Return a brief recommendation string for an issue."""
    if tier == StrengthTier.STRONG:
        return (
            f"LEAD ISSUE — '{issue_name}' scores {total}/10.  Feature "
            "prominently in the application as a primary question presented."
        )
    if tier == StrengthTier.MODERATE:
        return (
            f"SUPPORTING ISSUE — '{issue_name}' scores {total}/10.  "
            "Include as a secondary question; strengthen factual record "
            "where possible."
        )
    if tier == StrengthTier.WEAK:
        return (
            f"BORDERLINE — '{issue_name}' scores {total}/10.  Consider "
            "omitting unless it bolsters a stronger companion issue."
        )
    return (
        f"OMIT — '{issue_name}' scores {total}/10.  Not viable for MSC "
        "review in its current state."
    )


def _draft_question_presented(issue: dict) -> str:
    """Draft a *Question Presented* for MSC review from an issue dict."""
    name = issue.get("name", "Unknown issue")
    desc = issue.get("description", "")
    criteria = issue.get("mcr_criteria", [])

    criteria_labels = {
        "constitutional_question": "constitutional significance",
        "major_legal_principle": "a legal principle of major significance",
        "conflict_with_msc_coa": "conflict with a prior MSC or COA decision",
        "conflict_with_federal": "conflict with federal authority",
        "superintending_control": "superintending-control authority",
    }

    bases = [criteria_labels.get(c, c) for c in criteria]
    basis_str = ", ".join(bases) if bases else "legal significance"

    return (
        f"Whether the lower court erred in {name.lower()}, "
        f"thereby implicating {basis_str}, "
        f"warranting this Court's review."
    )


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------


def get_msc_grant_criteria() -> dict[str, str]:
    """Return MCR 7.305(B) grant criteria as ``{key: description}``."""
    return dict(MSC_GRANT_CRITERIA)


def score_issue(issue: dict) -> IssueScore:
    """Score a single issue for MSC appeal potential.

    Parameters
    ----------
    issue:
        Must contain at minimum ``name`` (str).  Optional keys:
        ``description`` (str), ``mcr_criteria`` (list[str]),
        ``baseline_scores`` (dict[str, int] with dimension → 0-10 values),
        and per-dimension overrides with dimension name keys.

    Returns
    -------
    IssueScore
        Fully scored model with weighted total, tier, and recommendation.
    """
    name: str = issue.get("name", "Unnamed Issue")
    description: str = issue.get("description", "")
    mcr_criteria: list[str] = issue.get("mcr_criteria", [])

    # Start from baseline_scores if provided, else zeros.
    raw_scores: dict[str, int] = {}
    baseline = issue.get("baseline_scores", {})
    for dim in SCORING_DIMENSIONS:
        # Per-dimension override takes priority over baseline.
        value = issue.get(dim, baseline.get(dim, 0))
        raw_scores[dim] = max(0, min(10, int(value)))

    result = IssueScore(
        issue_name=name,
        description=description,
        scores=raw_scores,
        mcr_criteria_met=mcr_criteria,
    )
    result.compute_total()
    result.recommendation = _build_recommendation(name, result.total, result.tier)
    result.questions_presented = _draft_question_presented(issue)

    logger.debug("Scored issue '%s' → %.2f (%s)", name, result.total, result.tier.value)
    return result


def rank_issues(issues: list[dict]) -> list[IssueScore]:
    """Score and rank issues by MSC appeal potential (strongest first).

    Parameters
    ----------
    issues:
        List of issue dicts (see :func:`score_issue` for required keys).

    Returns
    -------
    list[IssueScore]
        Sorted descending by weighted total score.
    """
    scored = [score_issue(i) for i in issues]
    scored.sort(key=lambda s: s.total, reverse=True)
    return scored


def assess_overall_strength(issues: list[dict]) -> OverallAssessment:
    """Produce an aggregate MSC application-strength assessment.

    Parameters
    ----------
    issues:
        List of issue dicts.

    Returns
    -------
    OverallAssessment
        Contains ranked issues, average score, top issues, strategy
        narrative, and filing recommendation.
    """
    ranked = rank_issues(issues)
    if not ranked:
        return OverallAssessment(
            strategy="No issues provided — cannot assess MSC viability.",
            filing_recommendation=FilingStrategy.HOLD,
        )

    avg = round(sum(s.total for s in ranked) / len(ranked), 2)
    top = [s.issue_name for s in ranked if s.tier == StrengthTier.STRONG]
    strategy = _build_strategy_narrative(ranked, avg, top)
    filing_rec = _determine_filing_recommendation(ranked, top)

    return OverallAssessment(
        issues=ranked,
        avg_score=avg,
        top_issues=top,
        strategy=strategy,
        filing_recommendation=filing_rec,
    )


def generate_questions_presented(issues: list[dict]) -> list[str]:
    """Draft *Questions Presented* for MSC review.

    Only issues scoring at *Moderate* or above are included.  Questions are
    ordered by strength (strongest first), matching MSC brief conventions.

    Parameters
    ----------
    issues:
        List of issue dicts.

    Returns
    -------
    list[str]
        Ordered draft questions suitable for the application.
    """
    ranked = rank_issues(issues)
    questions: list[str] = []
    for idx, scored in enumerate(ranked, 1):
        if scored.tier in (StrengthTier.STRONG, StrengthTier.MODERATE):
            q = scored.questions_presented or _draft_question_presented(
                {"name": scored.issue_name, "mcr_criteria": scored.mcr_criteria_met}
            )
            questions.append(f"{idx}. {q}")
    return questions


def recommend_filing_strategy(scores: list[IssueScore]) -> str:
    """Recommend leave to appeal, original action, or both.

    Parameters
    ----------
    scores:
        Pre-scored issues (output of :func:`rank_issues`).

    Returns
    -------
    str
        Human-readable recommendation with reasoning.
    """
    top = [s for s in scores if s.tier == StrengthTier.STRONG]
    has_superintending = any(
        "superintending_control" in s.mcr_criteria_met for s in top
    )
    has_constitutional = any(
        "constitutional_question" in s.mcr_criteria_met for s in top
    )
    has_conflict = any(
        "conflict_with_msc_coa" in s.mcr_criteria_met
        or "conflict_with_federal" in s.mcr_criteria_met
        for s in top
    )

    if not top:
        return (
            "HOLD — No issues currently score in the Strong tier.  "
            "Strengthen the record or develop additional issues before "
            "filing with the MSC."
        )

    parts: list[str] = []

    if has_superintending and has_constitutional:
        rec = FilingStrategy.BOTH.value
        parts.append(
            f"RECOMMENDED: {rec}.  The combination of constitutional "
            "questions and superintending-control issues supports a dual "
            "filing strategy — an application for leave to appeal on the "
            "constitutional issues, plus an original action invoking the "
            "Court's superintending-control authority under Const 1963, "
            "art 6, § 4."
        )
    elif has_superintending:
        rec = FilingStrategy.ORIGINAL_ACTION.value
        parts.append(
            f"RECOMMENDED: {rec}.  The strongest issues implicate the "
            "Court's superintending-control power.  An original complaint "
            "under MCR 3.302 may be the most direct vehicle."
        )
    elif has_conflict or has_constitutional:
        rec = FilingStrategy.LEAVE_TO_APPEAL.value
        parts.append(
            f"RECOMMENDED: {rec}.  Strong conflict-with-precedent or "
            "constitutional issues make a conventional leave application "
            "the best vehicle."
        )
    else:
        rec = FilingStrategy.LEAVE_TO_APPEAL.value
        parts.append(
            f"RECOMMENDED: {rec}.  Strong issues exist but do not "
            "clearly invoke superintending control; proceed with a "
            "standard application for leave."
        )

    strong_names = ", ".join(s.issue_name for s in top)
    parts.append(f"Lead with: {strong_names}.")

    moderate = [s for s in scores if s.tier == StrengthTier.MODERATE]
    if moderate:
        mod_names = ", ".join(s.issue_name for s in moderate)
        parts.append(f"Supporting issues: {mod_names}.")

    weak = [s for s in scores if s.tier in (StrengthTier.WEAK, StrengthTier.INSUFFICIENT)]
    if weak:
        parts.append(
            f"{len(weak)} issue(s) scored below Moderate — consider "
            "omitting to keep the application focused."
        )

    return "  ".join(parts)


# ---------------------------------------------------------------------------
# Internal strategy helpers
# ---------------------------------------------------------------------------


def _build_strategy_narrative(
    ranked: list[IssueScore],
    avg: float,
    top: list[str],
) -> str:
    """Compose a human-readable strategy narrative."""
    total_issues = len(ranked)
    strong_count = sum(1 for s in ranked if s.tier == StrengthTier.STRONG)
    moderate_count = sum(1 for s in ranked if s.tier == StrengthTier.MODERATE)

    lines: list[str] = [
        f"Analyzed {total_issues} potential MSC issues.  "
        f"Average weighted score: {avg}/10.",
    ]

    if strong_count:
        lines.append(
            f"{strong_count} issue(s) rated Strong: {', '.join(top)}.  "
            "These should anchor the application."
        )
    if moderate_count:
        mod_names = [
            s.issue_name for s in ranked if s.tier == StrengthTier.MODERATE
        ]
        lines.append(
            f"{moderate_count} issue(s) rated Moderate: "
            f"{', '.join(mod_names)}.  Include as supporting questions."
        )

    # MSC-specific guidance
    if avg >= STRONG_THRESHOLD:
        lines.append(
            "Overall application strength is HIGH.  The MSC grants ~5% "
            "of applications; this set of issues is competitive."
        )
    elif avg >= MODERATE_THRESHOLD:
        lines.append(
            "Overall application strength is MODERATE.  Consider "
            "focusing on the top-scoring issues and strengthening the "
            "factual record before filing."
        )
    else:
        lines.append(
            "Overall application strength is LOW.  Recommend developing "
            "the record further or pursuing COA remedies before seeking "
            "MSC review."
        )

    return "  ".join(lines)


def _determine_filing_recommendation(
    ranked: list[IssueScore],
    top: list[str],
) -> FilingStrategy:
    """Pick the best filing vehicle based on issue characteristics."""
    has_superintending = any(
        "superintending_control" in s.mcr_criteria_met
        for s in ranked
        if s.tier == StrengthTier.STRONG
    )
    has_constitutional = any(
        "constitutional_question" in s.mcr_criteria_met
        for s in ranked
        if s.tier == StrengthTier.STRONG
    )

    if not top:
        return FilingStrategy.HOLD
    if has_superintending and has_constitutional:
        return FilingStrategy.BOTH
    if has_superintending:
        return FilingStrategy.ORIGINAL_ACTION
    return FilingStrategy.LEAVE_TO_APPEAL


# ---------------------------------------------------------------------------
# Convenience — default Pigors v Watson analysis
# ---------------------------------------------------------------------------


def analyze_pigors_v_watson() -> OverallAssessment:
    """Run the full MSC strength analysis on the pre-loaded Pigors v Watson
    issues.  Convenience wrapper for interactive / CLI use."""
    return assess_overall_strength(PIGORS_V_WATSON_ISSUES)
