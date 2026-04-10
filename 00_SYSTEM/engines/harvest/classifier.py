"""Harvest Engine — MEEK lane classification + actor/authority/document-type detection.

Single-pass analysis using compiled regex patterns from config.py.
Zero API dependency — all pattern matching is local.
"""

import logging
import re
from collections import Counter
from typing import Optional

try:
    from . import config
except ImportError:
    import config

logger = logging.getLogger(__name__)


class ClassificationResult:
    """Result of classifying extracted text."""
    __slots__ = (
        "primary_lane", "lane_scores", "actors", "doc_type",
        "authorities", "dates", "quotes", "has_child_name",
    )

    def __init__(self):
        self.primary_lane = "A"  # default to custody
        self.lane_scores = {}    # {lane: match_count}
        self.actors = []         # [(actor_name, match_count)]
        self.doc_type = "unknown"
        self.authorities = []    # [(type, citation_text)]
        self.dates = []          # [date_string, ...]
        self.quotes = []         # [quote_text, ...]
        self.has_child_name = False


def classify_text(text: str, file_path: str = "") -> ClassificationResult:
    """Classify text content — single pass through all patterns.

    Detection priority: E → D → F → C → A → B (matches MEEK spec).
    """
    result = ClassificationResult()
    if not text or len(text) < 10:
        return result

    # ── Lane classification ──────────────────────────────────────────────
    for lane, pattern in config.LANE_PATTERNS.items():
        matches = pattern.findall(text)
        if matches:
            result.lane_scores[lane] = len(matches)

    # Determine primary lane by priority order (E > D > F > C > A > B)
    priority = ["E", "D", "F", "C", "A", "B"]
    for lane in priority:
        if result.lane_scores.get(lane, 0) >= 2:
            result.primary_lane = lane
            break
    else:
        # If no lane got 2+ hits, pick highest scoring
        if result.lane_scores:
            result.primary_lane = max(result.lane_scores, key=result.lane_scores.get)

    # Also try to classify by filename
    fp_lower = file_path.lower()
    if "jtc" in fp_lower or "judicial" in fp_lower:
        result.primary_lane = "E"
    elif "ppo" in fp_lower or "protection" in fp_lower:
        result.primary_lane = "D"
    elif "appeal" in fp_lower or "coa" in fp_lower or "366810" in fp_lower:
        result.primary_lane = "F"
    elif "custody" in fp_lower or "watson" in fp_lower or "001507" in fp_lower:
        result.primary_lane = "A"
    elif "emily" in fp_lower and "filing" in fp_lower:
        result.primary_lane = "A"
    elif "judge" in fp_lower and "order" in fp_lower:
        if result.lane_scores.get("E", 0) > 0:
            result.primary_lane = "E"
        else:
            result.primary_lane = "A"
    elif "rusco" in fp_lower or "martini" in fp_lower:
        result.primary_lane = "A"  # FOC is primarily custody lane
    elif "docket" in fp_lower or "notice" in fp_lower:
        result.primary_lane = "A"
    elif "shady" in fp_lower or "eviction" in fp_lower or "housing" in fp_lower:
        result.primary_lane = "B"

    # ── Actor detection ──────────────────────────────────────────────────
    actor_counts = {}
    for name, pattern in config.ADVERSARIES.items():
        matches = pattern.findall(text)
        if matches:
            actor_counts[name] = len(matches)
    result.actors = sorted(actor_counts.items(), key=lambda x: -x[1])

    # ── Document type detection ──────────────────────────────────────────
    doc_scores = {}
    for dtype, pattern in config.DOC_TYPES.items():
        matches = pattern.findall(text)
        if matches:
            doc_scores[dtype] = len(matches)
    if doc_scores:
        result.doc_type = max(doc_scores, key=doc_scores.get)

    # ── Authority extraction ─────────────────────────────────────────────
    for auth_type, pattern in config.AUTHORITY_PATTERNS.items():
        for match in pattern.finditer(text):
            if auth_type == "USC":
                citation = f"{match.group(1)} USC § {match.group(2)}"
            elif auth_type == "case_law":
                citation = match.group(0).strip()
                if len(citation) > 200:
                    citation = citation[:200]
            else:
                citation = f"{auth_type} {match.group(1)}"
            result.authorities.append((auth_type, citation))

    # Deduplicate authorities
    seen = set()
    unique_auths = []
    for auth in result.authorities:
        key = auth[1].lower().strip()
        if key not in seen:
            seen.add(key)
            unique_auths.append(auth)
    result.authorities = unique_auths[:100]  # cap at 100

    # ── Date extraction ──────────────────────────────────────────────────
    date_matches = config.DATE_PATTERN.findall(text)
    result.dates = list(dict.fromkeys(date_matches))[:50]  # dedupe, cap

    # ── Quote extraction ─────────────────────────────────────────────────
    for pattern in config.QUOTE_PATTERNS:
        for match in pattern.finditer(text):
            quote = match.group(1).strip()
            if 20 <= len(quote) <= 500:
                result.quotes.append(quote)
    result.quotes = list(dict.fromkeys(result.quotes))[:50]  # dedupe, cap

    # ── Child name check (MCR 8.119(H)) ──────────────────────────────────
    result.has_child_name = bool(config.CHILD_NAME_PATTERN.search(text))

    return result


def classify_file_by_path(file_path: str) -> Optional[str]:
    """Quick lane classification from filename alone (no text needed)."""
    fp = file_path.lower()

    path_lane_map = [
        ("jtc", "E"),
        ("judicial", "E"),
        ("mcneill", "E"),
        ("ppo", "D"),
        ("protection", "D"),
        ("appeal", "F"),
        ("coa", "F"),
        ("366810", "F"),
        ("emily", "A"),
        ("custody", "A"),
        ("watson", "A"),
        ("001507", "A"),
        ("parenting", "A"),
        ("foc", "A"),
        ("rusco", "A"),
        ("judge order", "E"),
        ("court doc", "A"),
        ("docket", "A"),
        ("notice", "A"),
        ("shady", "B"),
        ("eviction", "B"),
        ("housing", "B"),
    ]

    for keyword, lane in path_lane_map:
        if keyword in fp:
            return lane
    return None
