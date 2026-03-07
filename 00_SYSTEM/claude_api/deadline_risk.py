"""
Deadline Risk Assessor for LitigationOS.

Evaluates filing deadline risk across all six case lanes using Claude for
intelligent analysis, with a pure-Python heuristic fallback that guarantees
useful output even when no API key is configured.

Usage::

    from claude_api.deadline_risk import assess_risks, Deadline, FilingReadiness

    deadlines = [
        Deadline(
            deadline_id="DL-001",
            description="Response to Motion for Summary Disposition",
            due_date="2026-03-15",
            case_lane="A",
            filing_type="response",
            status="pending",
        ),
    ]
    report = assess_risks(deadlines)
    print(report.overall_risk, report.top_priority)
"""

from __future__ import annotations

import json
import logging
from dataclasses import dataclass, field
from datetime import date, datetime, timezone
from typing import Any

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Data classes
# ---------------------------------------------------------------------------

VALID_STATUSES = ("pending", "in_progress", "filed", "overdue")
VALID_SEVERITIES = ("critical", "major", "minor")
VALID_RISK_LEVELS = ("critical", "high", "medium", "low")

LANE_LABELS: dict[str, str] = {
    "A": "Watson custody (MEEK2)",
    "B": "Shady Oaks housing (MEEK1)",
    "C": "Convergence (cross-lane)",
    "D": "PPO / Protection Orders (MEEK3)",
    "E": "Judicial Misconduct / JTC (MEEK4)",
    "F": "Appellate COA/MSC (MEEK5)",
}


@dataclass
class Deadline:
    """A single filing deadline."""

    deadline_id: str
    description: str
    due_date: str  # ISO 8601 date (YYYY-MM-DD)
    case_lane: str
    filing_type: str
    status: str  # pending | in_progress | filed | overdue

    def days_remaining(self) -> int:
        """Calendar days until due_date from today (negative = overdue)."""
        try:
            target = date.fromisoformat(self.due_date)
        except ValueError:
            return -999
        return (target - date.today()).days


@dataclass
class FilingReadiness:
    """Readiness assessment tied to a specific deadline."""

    deadline_id: str
    readiness_score: float  # 0.0 (nothing ready) – 1.0 (fully ready)
    missing_items: list[str] = field(default_factory=list)
    completed_items: list[str] = field(default_factory=list)


@dataclass
class EvidenceGap:
    """A gap in the evidence record relevant to a claim."""

    claim_id: str
    description: str
    severity: str  # critical | major | minor
    related_deadline_id: str | None = None


@dataclass
class DeadlineRisk:
    """Risk assessment result for a single deadline."""

    deadline_id: str
    risk_score: float  # 0.0 (safe) – 1.0 (highest risk)
    risk_level: str  # critical | high | medium | low
    days_remaining: int
    action_items: list[str] = field(default_factory=list)
    reasoning: str = ""
    dependencies: list[str] = field(default_factory=list)


@dataclass
class RiskReport:
    """Aggregate risk report across all assessed deadlines."""

    risks: list[DeadlineRisk] = field(default_factory=list)
    overall_risk: str = "unknown"
    top_priority: str = ""
    summary: str = ""
    available: bool = False  # True when Claude API was used
    cost_usd: float = 0.0
    assessed_at: str = ""


# ---------------------------------------------------------------------------
# System prompt
# ---------------------------------------------------------------------------

_SYSTEM_PROMPT = """\
You are a Michigan litigation deadline risk analyst embedded in LitigationOS.

You evaluate filing deadlines across six case lanes:
- Lane A: Watson custody (2024-001507-DC, 2023-5907-PP)
- Lane B: Shady Oaks housing (2025-002760-CZ)
- Lane C: Convergence (cross-lane matters)
- Lane D: PPO / Protection Orders
- Lane E: Judicial Misconduct / JTC complaints
- Lane F: Appellate (COA/MSC)

Michigan Court Rules (MCR) govern filing windows. Key rules:
- MCR 2.108: Service timing requirements
- MCR 2.116(C)(10): Summary disposition response deadlines
- MCR 2.119: Motion practice timing (21-day notice, 7-day response)
- MCR 7.205 / 7.305: Appellate filing windows (21-day claim of appeal)
- MCR 3.206: Domestic relations motion timing

For each deadline, evaluate:
1. Risk score (0.0 = safe, 1.0 = highest risk) based on days remaining, \
filing readiness, evidence gaps, and cross-lane dependencies.
2. Risk level: "critical" (immediate jeopardy), "high" (urgent action needed), \
"medium" (monitor closely), "low" (on track).
3. Concrete, actionable items — not vague advice. Specify exact documents, \
forms, or steps needed.
4. Dependencies on other deadlines or filings that affect this one.
5. Brief reasoning explaining the risk assessment.

Respond with a JSON object (no markdown, no explanation outside JSON).
"""


# ---------------------------------------------------------------------------
# Claude-powered assessment
# ---------------------------------------------------------------------------

def _build_user_prompt(
    deadlines: list[Deadline],
    readiness: list[FilingReadiness] | None,
    gaps: list[EvidenceGap] | None,
) -> str:
    """Assemble the user message with all deadline data."""
    readiness_map: dict[str, FilingReadiness] = {}
    if readiness:
        readiness_map = {r.deadline_id: r for r in readiness}

    gap_by_deadline: dict[str, list[dict[str, Any]]] = {}
    if gaps:
        for g in gaps:
            key = g.related_deadline_id or "__unlinked__"
            gap_by_deadline.setdefault(key, []).append({
                "claim_id": g.claim_id,
                "description": g.description,
                "severity": g.severity,
            })

    deadline_entries: list[dict[str, Any]] = []
    for dl in deadlines:
        entry: dict[str, Any] = {
            "deadline_id": dl.deadline_id,
            "description": dl.description,
            "due_date": dl.due_date,
            "days_remaining": dl.days_remaining(),
            "case_lane": dl.case_lane,
            "lane_label": LANE_LABELS.get(dl.case_lane, "Unknown"),
            "filing_type": dl.filing_type,
            "status": dl.status,
        }
        r = readiness_map.get(dl.deadline_id)
        if r:
            entry["readiness"] = {
                "score": r.readiness_score,
                "missing_items": r.missing_items,
                "completed_items": r.completed_items,
            }
        dl_gaps = gap_by_deadline.get(dl.deadline_id, [])
        if dl_gaps:
            entry["evidence_gaps"] = dl_gaps
        deadline_entries.append(entry)

    unlinked = gap_by_deadline.get("__unlinked__", [])

    payload: dict[str, Any] = {
        "deadlines": deadline_entries,
        "today": date.today().isoformat(),
    }
    if unlinked:
        payload["unlinked_evidence_gaps"] = unlinked

    prompt = (
        "Assess the risk for each deadline below and provide an overall analysis.\n\n"
        f"{json.dumps(payload, indent=2)}\n\n"
        "Return JSON with this exact schema:\n"
        "{\n"
        '  "risks": [\n'
        "    {\n"
        '      "deadline_id": "...",\n'
        '      "risk_score": 0.0-1.0,\n'
        '      "risk_level": "critical|high|medium|low",\n'
        '      "days_remaining": int,\n'
        '      "action_items": ["..."],\n'
        '      "reasoning": "...",\n'
        '      "dependencies": ["..."]\n'
        "    }\n"
        "  ],\n"
        '  "overall_risk": "critical|high|medium|low",\n'
        '  "top_priority": "single most urgent action sentence",\n'
        '  "summary": "2-3 sentence overall assessment"\n'
        "}\n"
    )
    return prompt


def _parse_claude_response(
    parsed: dict[str, Any],
    deadlines: list[Deadline],
    cost_usd: float,
) -> RiskReport:
    """Convert parsed Claude JSON into a RiskReport."""
    deadline_map = {dl.deadline_id: dl for dl in deadlines}
    risks: list[DeadlineRisk] = []

    for item in parsed.get("risks", []):
        did = item.get("deadline_id", "")
        dl = deadline_map.get(did)
        days_rem = item.get("days_remaining", dl.days_remaining() if dl else 0)
        risks.append(DeadlineRisk(
            deadline_id=did,
            risk_score=max(0.0, min(1.0, float(item.get("risk_score", 0.5)))),
            risk_level=item.get("risk_level", "medium"),
            days_remaining=int(days_rem),
            action_items=item.get("action_items", []),
            reasoning=item.get("reasoning", ""),
            dependencies=item.get("dependencies", []),
        ))

    return RiskReport(
        risks=risks,
        overall_risk=parsed.get("overall_risk", "unknown"),
        top_priority=parsed.get("top_priority", ""),
        summary=parsed.get("summary", ""),
        available=True,
        cost_usd=cost_usd,
        assessed_at=datetime.now(timezone.utc).isoformat(),
    )


# ---------------------------------------------------------------------------
# Heuristic fallback (pure-Python, zero dependencies)
# ---------------------------------------------------------------------------

def _risk_level_from_score(score: float) -> str:
    if score >= 0.8:
        return "critical"
    if score >= 0.6:
        return "high"
    if score >= 0.4:
        return "medium"
    return "low"


def _heuristic_assess_single(
    dl: Deadline,
    readiness: FilingReadiness | None,
    gaps: list[EvidenceGap] | None,
) -> DeadlineRisk:
    """Pure-Python risk scoring for a single deadline."""
    days = dl.days_remaining()

    # Days-remaining weight
    if days <= 0:
        days_weight = 1.0
    elif days <= 3:
        days_weight = 1.0
    elif days <= 7:
        days_weight = 0.8
    elif days <= 14:
        days_weight = 0.6
    elif days <= 30:
        days_weight = 0.4
    else:
        days_weight = 0.2

    # Readiness weight
    readiness_weight = 0.0
    if readiness:
        readiness_weight = (1.0 - readiness.readiness_score) * 0.5

    # Gap penalty
    gap_penalty = 0.0
    if gaps:
        for g in gaps:
            if g.related_deadline_id == dl.deadline_id or g.related_deadline_id is None:
                if g.severity == "critical":
                    gap_penalty += 0.1
                elif g.severity == "major":
                    gap_penalty += 0.05

    raw_score = days_weight + readiness_weight + gap_penalty
    score = max(0.0, min(1.0, raw_score))
    level = _risk_level_from_score(score)

    # Generate basic action items
    action_items: list[str] = []
    if dl.status == "overdue":
        action_items.append(f"OVERDUE: File {dl.filing_type} for {dl.description} immediately")
    elif days <= 3:
        action_items.append(f"URGENT: {dl.filing_type} due in {days} day(s) — finalize now")
    elif days <= 7:
        action_items.append(f"Complete {dl.filing_type} draft and begin review cycle")

    if readiness and readiness.missing_items:
        for item in readiness.missing_items[:3]:
            action_items.append(f"Obtain: {item}")

    if gaps:
        crit_gaps = [g for g in gaps
                     if g.severity == "critical"
                     and (g.related_deadline_id == dl.deadline_id
                          or g.related_deadline_id is None)]
        for g in crit_gaps[:2]:
            action_items.append(f"Fill evidence gap: {g.description}")

    reasoning = (
        f"{days} days remaining | "
        f"readiness={readiness.readiness_score:.0%} "
        if readiness else f"{days} days remaining | readiness=unknown "
    )
    reasoning += f"| status={dl.status} | lane={dl.case_lane}"

    return DeadlineRisk(
        deadline_id=dl.deadline_id,
        risk_score=round(score, 3),
        risk_level=level,
        days_remaining=days,
        action_items=action_items,
        reasoning=reasoning,
        dependencies=[],
    )


def _heuristic_report(
    deadlines: list[Deadline],
    readiness: list[FilingReadiness] | None,
    gaps: list[EvidenceGap] | None,
) -> RiskReport:
    """Build a full risk report using heuristic scoring (no API)."""
    readiness_map: dict[str, FilingReadiness] = {}
    if readiness:
        readiness_map = {r.deadline_id: r for r in readiness}

    risks: list[DeadlineRisk] = []
    for dl in deadlines:
        r = readiness_map.get(dl.deadline_id)
        dl_gaps = [
            g for g in (gaps or [])
            if g.related_deadline_id == dl.deadline_id or g.related_deadline_id is None
        ]
        risks.append(_heuristic_assess_single(dl, r, dl_gaps or None))

    risks.sort(key=lambda r: (-r.risk_score, r.days_remaining))

    if not risks:
        overall = "low"
        top_priority = "No deadlines to assess."
    else:
        worst = risks[0]
        overall = worst.risk_level
        top_priority = worst.action_items[0] if worst.action_items else (
            f"Review deadline {worst.deadline_id}: {worst.days_remaining} days remaining"
        )

    crit_count = sum(1 for r in risks if r.risk_level == "critical")
    high_count = sum(1 for r in risks if r.risk_level == "high")
    summary = (
        f"Heuristic assessment of {len(risks)} deadline(s): "
        f"{crit_count} critical, {high_count} high risk. "
        f"(Claude API unavailable — using local scoring.)"
    )

    return RiskReport(
        risks=risks,
        overall_risk=overall,
        top_priority=top_priority,
        summary=summary,
        available=False,
        cost_usd=0.0,
        assessed_at=datetime.now(timezone.utc).isoformat(),
    )


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def assess_risks(
    deadlines: list[Deadline],
    readiness: list[FilingReadiness] | None = None,
    gaps: list[EvidenceGap] | None = None,
) -> RiskReport:
    """
    Assess risk across all provided deadlines.

    Uses Claude for intelligent analysis when available; falls back to
    deterministic heuristic scoring otherwise.  Always returns a valid
    ``RiskReport`` — never raises on missing API key.
    """
    if not deadlines:
        return RiskReport(
            overall_risk="low",
            top_priority="No deadlines provided.",
            summary="Nothing to assess.",
            assessed_at=datetime.now(timezone.utc).isoformat(),
        )

    from . import client  # local import to avoid circular at module level

    if not client.is_available():
        logger.info("Claude API unavailable — using heuristic deadline risk assessment")
        return _heuristic_report(deadlines, readiness, gaps)

    # --- Claude-powered path ---
    user_prompt = _build_user_prompt(deadlines, readiness, gaps)

    try:
        result = client.create_json_message(
            system=_SYSTEM_PROMPT,
            messages=[{"role": "user", "content": user_prompt}],
            max_tokens=4096,
        )
    except Exception as exc:
        logger.warning("Claude API call failed (%s) — falling back to heuristics", exc)
        return _heuristic_report(deadlines, readiness, gaps)

    parsed = result.get("parsed")
    if parsed is None:
        logger.warning(
            "Failed to parse Claude response — falling back to heuristics: %s",
            result.get("parse_error", "unknown"),
        )
        return _heuristic_report(deadlines, readiness, gaps)

    cost = result.get("cost_usd", 0.0)
    logger.info(
        "Claude deadline risk assessment complete (cost=$%.4f, deadlines=%d)",
        cost,
        len(deadlines),
    )
    return _parse_claude_response(parsed, deadlines, cost)


def assess_single_deadline(
    deadline: Deadline,
    readiness: FilingReadiness | None = None,
    gaps: list[EvidenceGap] | None = None,
) -> DeadlineRisk:
    """
    Quick risk assessment for a single deadline.

    Delegates to :func:`assess_risks` and extracts the single result.
    """
    readiness_list = [readiness] if readiness else None
    report = assess_risks([deadline], readiness_list, gaps)
    if report.risks:
        return report.risks[0]
    # Should not happen, but be defensive
    return _heuristic_assess_single(deadline, readiness, gaps)
