"""
Smart Document Classifier for LitigationOS.

Fallback classifier that calls the Claude API when the local TF-IDF / Naive
Bayes model returns a confidence score below the configured threshold (default
0.7).  This module is **never** the primary classifier — it exists solely to
resolve ambiguous documents that the local model cannot confidently assign to
one of the six litigation lanes.

Usage::

    from claude_api.classifier import classify_document, classify_batch

    result = classify_document(
        text=doc_text,
        metadata={"filename": "motion.pdf", "source": "F:\\Inbox"},
        local_confidence=0.45,
    )
    if result.available and result.confidence >= 0.7:
        assign_to_lane(result.lane)

The six case lanes are:

    A (lane_A) — Watson custody (MEEK2)
    B (lane_B) — Shady Oaks housing (MEEK1)
    C (lane_C) — Convergence / cross-lane
    D (lane_D) — PPO / Protection Orders (MEEK3)
    E (lane_E) — Judicial Misconduct / JTC (MEEK4)
    F (lane_F) — Appellate COA/MSC (MEEK5)
"""

from __future__ import annotations

import json
import logging
from dataclasses import dataclass, field
from typing import Any

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

MAX_TEXT_CHARS = 8_000
LOCAL_CONFIDENCE_THRESHOLD = 0.7

LANE_DEFINITIONS: list[dict[str, str]] = [
    {
        "code": "lane_A",
        "name": "Watson Custody",
        "meek": "MEEK2",
        "description": (
            "Documents related to the Watson custody dispute — parenting "
            "time, best-interest factors, FOC recommendations, child support, "
            "custody evaluations, and domestic relations proceedings in case "
            "2024-001507-DC / 2023-5907-PP."
        ),
    },
    {
        "code": "lane_B",
        "name": "Shady Oaks Housing",
        "meek": "MEEK1",
        "description": (
            "Documents related to the Shady Oaks housing / civil claim — "
            "landlord-tenant disputes, lease agreements, housing code "
            "violations, property conditions, and the civil suit "
            "2025-002760-CZ."
        ),
    },
    {
        "code": "lane_C",
        "name": "Convergence (Cross-Lane)",
        "meek": "—",
        "description": (
            "Documents that span multiple lanes or cannot be neatly assigned "
            "to a single lane.  Use this lane ONLY when a document genuinely "
            "addresses two or more lanes with roughly equal relevance."
        ),
    },
    {
        "code": "lane_D",
        "name": "PPO / Protection Orders",
        "meek": "MEEK3",
        "description": (
            "Documents related to Personal Protection Orders — PPO petitions, "
            "violations, bond conditions, stalking, harassment, or domestic "
            "violence protective orders in cases 2024-001507-DC / 2023-5907-PP."
        ),
    },
    {
        "code": "lane_E",
        "name": "Judicial Misconduct / JTC",
        "meek": "MEEK4",
        "description": (
            "Documents related to judicial misconduct or Judicial Tenure "
            "Commission complaints — bias evidence, ex-parte communications, "
            "procedural violations by the bench, and JTC filings in case "
            "2024-001507-DC."
        ),
    },
    {
        "code": "lane_F",
        "name": "Appellate (COA/MSC)",
        "meek": "MEEK5",
        "description": (
            "Documents related to appellate proceedings — Court of Appeals "
            "applications, Michigan Supreme Court filings, claims of appeal, "
            "appellate briefs, leave applications, and interlocutory appeals."
        ),
    },
]

_VALID_LANE_CODES: set[str] = {d["code"] for d in LANE_DEFINITIONS}

# ---------------------------------------------------------------------------
# System prompt
# ---------------------------------------------------------------------------

_SYSTEM_PROMPT = """\
You are a Michigan family-law litigation document classifier.  Your sole task
is to assign an incoming document to the single most appropriate litigation
lane from the list below.

## Lanes

{lane_block}

## Instructions

1. Read the document text and any metadata provided.
2. Determine which lane best fits the document.  If the document genuinely
   covers multiple lanes with near-equal relevance, choose "lane_C"
   (Convergence).
3. Return your answer as a single JSON object with exactly these keys:
   - "lane"            (string) — one of: {valid_codes}
   - "confidence"      (float 0-1) — your confidence in the primary lane
   - "reasoning"       (string) — 1-3 sentences explaining why
   - "secondary_lanes" (array of objects) — other plausible lanes, each with
     "lane" (string) and "confidence" (float 0-1).  May be empty.

Do NOT include markdown fences or any text outside the JSON object.
""".format(
    lane_block="\n".join(
        "- **{code}** ({name}, {meek}): {description}".format(**d)
        for d in LANE_DEFINITIONS
    ),
    valid_codes=", ".join(sorted(_VALID_LANE_CODES)),
)


# ---------------------------------------------------------------------------
# Result dataclass
# ---------------------------------------------------------------------------

@dataclass
class ClassificationResult:
    """Outcome of a single document classification attempt."""

    lane: str = ""
    confidence: float = 0.0
    reasoning: str = ""
    secondary_lanes: list[dict[str, Any]] = field(default_factory=list)
    available: bool = True
    cost_usd: float = 0.0


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _unavailable_result(reason: str = "Claude API not available") -> ClassificationResult:
    """Return a neutral result indicating the classifier could not run."""
    return ClassificationResult(
        lane="",
        confidence=0.0,
        reasoning=reason,
        secondary_lanes=[],
        available=False,
        cost_usd=0.0,
    )


def _build_user_message(text: str, metadata: dict[str, Any] | None) -> str:
    """Assemble the user-turn content from document text and metadata."""
    parts: list[str] = []

    if metadata:
        meta_lines = [f"- {k}: {v}" for k, v in metadata.items() if v]
        if meta_lines:
            parts.append("## Document Metadata\n" + "\n".join(meta_lines))

    truncated = text[:MAX_TEXT_CHARS]
    if len(text) > MAX_TEXT_CHARS:
        truncated += f"\n\n[… truncated — {len(text):,} chars total, showing first {MAX_TEXT_CHARS:,}]"

    parts.append("## Document Text\n" + truncated)

    return "\n\n".join(parts)


def _parse_response(parsed: dict[str, Any] | None, cost_usd: float) -> ClassificationResult:
    """Convert the raw parsed JSON into a validated ClassificationResult."""
    if parsed is None:
        return ClassificationResult(
            lane="",
            confidence=0.0,
            reasoning="Failed to parse JSON from Claude response",
            available=True,
            cost_usd=cost_usd,
        )

    lane = str(parsed.get("lane", "")).strip()
    if lane and lane not in _VALID_LANE_CODES:
        # Try to recover: "A" → "lane_A"
        candidate = f"lane_{lane}"
        if candidate in _VALID_LANE_CODES:
            lane = candidate
        else:
            logger.warning("Claude returned unknown lane %r; clearing", lane)
            lane = ""

    confidence = 0.0
    try:
        confidence = float(parsed.get("confidence", 0.0))
        confidence = max(0.0, min(1.0, confidence))
    except (TypeError, ValueError):
        pass

    reasoning = str(parsed.get("reasoning", ""))

    secondary_raw = parsed.get("secondary_lanes") or []
    secondary_lanes: list[dict[str, Any]] = []
    for entry in secondary_raw:
        if isinstance(entry, dict) and "lane" in entry:
            s_lane = str(entry["lane"]).strip()
            if s_lane not in _VALID_LANE_CODES:
                candidate = f"lane_{s_lane}"
                s_lane = candidate if candidate in _VALID_LANE_CODES else s_lane
            try:
                s_conf = float(entry.get("confidence", 0.0))
                s_conf = max(0.0, min(1.0, s_conf))
            except (TypeError, ValueError):
                s_conf = 0.0
            secondary_lanes.append({"lane": s_lane, "confidence": s_conf})

    return ClassificationResult(
        lane=lane,
        confidence=confidence,
        reasoning=reasoning,
        secondary_lanes=secondary_lanes,
        available=True,
        cost_usd=cost_usd,
    )


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def classify_document(
    text: str,
    metadata: dict[str, Any] | None = None,
    local_confidence: float = 0.0,
) -> ClassificationResult:
    """
    Classify a single document into a litigation lane via the Claude API.

    Parameters
    ----------
    text:
        The document's full text.  Truncated to *MAX_TEXT_CHARS* before
        sending.
    metadata:
        Optional dict with keys like ``filename``, ``path``, ``date``,
        ``source`` — included in the prompt to aid classification.
    local_confidence:
        The confidence score already produced by the local model.  If it
        meets or exceeds *LOCAL_CONFIDENCE_THRESHOLD* this function returns
        early with an ``available=False`` result so the caller knows no API
        call was made.

    Returns
    -------
    ClassificationResult
        Always returns a result — never raises.
    """
    # Import client lazily to avoid circular-import issues at module level
    from claude_api.client import create_json_message, get_config, is_available

    if local_confidence >= LOCAL_CONFIDENCE_THRESHOLD:
        return _unavailable_result(
            f"Local model confidence ({local_confidence:.2f}) meets threshold; "
            f"Claude API call skipped"
        )

    if not is_available():
        return _unavailable_result("No Anthropic API key configured")

    if not text or not text.strip():
        return _unavailable_result("Empty document text — nothing to classify")

    try:
        config = get_config()
        user_content = _build_user_message(text, metadata)

        response = create_json_message(
            system=_SYSTEM_PROMPT,
            messages=[{"role": "user", "content": user_content}],
            model=config.model,
            max_tokens=1024,
        )

        cost_usd = float(response.get("cost_usd", 0.0))
        parsed = response.get("parsed")

        if parsed is None:
            logger.warning(
                "Claude classifier: JSON parse failed — %s",
                response.get("parse_error", "unknown error"),
            )

        result = _parse_response(parsed, cost_usd)

        logger.info(
            "Classified document → %s (conf=%.2f, cost=$%.4f): %s",
            result.lane or "(none)",
            result.confidence,
            result.cost_usd,
            result.reasoning[:120],
        )
        return result

    except Exception:
        logger.exception("Claude classifier failed")
        return _unavailable_result("Claude API call failed — see logs for details")


def classify_batch(
    documents: list[dict[str, Any]],
) -> list[ClassificationResult]:
    """
    Classify multiple documents, skipping those whose local model confidence
    already meets the threshold.

    Parameters
    ----------
    documents:
        List of dicts each containing:
        - ``text`` (str): document text
        - ``metadata`` (dict | None): optional metadata
        - ``local_confidence`` (float): local model's confidence

    Returns
    -------
    list[ClassificationResult]
        One result per input document, in the same order.  Documents that
        were skipped will have ``available=False``.
    """
    results: list[ClassificationResult] = []
    total = len(documents)

    for idx, doc in enumerate(documents, 1):
        text = doc.get("text", "")
        metadata = doc.get("metadata")
        local_conf = float(doc.get("local_confidence", 0.0))

        logger.debug("Batch classify %d/%d (local_conf=%.2f)", idx, total, local_conf)

        result = classify_document(
            text=text,
            metadata=metadata,
            local_confidence=local_conf,
        )
        results.append(result)

    skipped = sum(1 for r in results if not r.available)
    classified = total - skipped
    logger.info(
        "Batch classification complete: %d total, %d classified, %d skipped",
        total, classified, skipped,
    )
    return results
