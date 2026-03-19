"""Temporal consistency checker for statement timelines."""
from __future__ import annotations

import logging
import re
from collections import defaultdict
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Optional

from . import config
from .normalizer import NormalizedStatement

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Duration extraction helpers
# ---------------------------------------------------------------------------
_DURATION_RE = re.compile(
    r"(?:for|about|approximately|roughly|lasted?|over)\s+"
    r"(\d+)\s+(day|week|month|year|hour|minute)s?",
    re.IGNORECASE,
)

_DURATION_DAYS: dict[str, int] = {
    "minute": 0,
    "hour": 0,
    "day": 1,
    "week": 7,
    "month": 30,
    "year": 365,
}


@dataclass
class TemporalAnomaly:
    """A detected timeline inconsistency."""

    statements_involved: list[NormalizedStatement]
    anomaly_type: str  # IMPOSSIBLE_SEQUENCE | DUPLICATE_EVENT | DURATION_MISMATCH
    description: str = ""
    severity: str = "MINOR"


class TemporalChecker:
    """Verify temporal consistency within groups of topically-related statements."""

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def check_timeline(
        self, statements: list[NormalizedStatement],
    ) -> list[TemporalAnomaly]:
        """Scan *statements* for temporal anomalies.

        Groups statements by shared topic keywords, then checks each
        group for:
        1. Impossible chronological sequences
        2. Same event claimed at two different times
        3. Duration inconsistencies
        """
        groups = self._group_by_topic(statements)
        anomalies: list[TemporalAnomaly] = []

        for topic_key, group in groups.items():
            dated = [s for s in group if s.date_normalized]
            if len(dated) < 2:
                continue

            anomalies.extend(self._check_impossible_sequence(dated))
            anomalies.extend(self._check_duplicate_events(dated))
            anomalies.extend(self._check_duration_mismatch(group))

        logger.info("Temporal check: %d anomalies found", len(anomalies))
        return anomalies

    # ------------------------------------------------------------------
    # Grouping
    # ------------------------------------------------------------------

    @staticmethod
    def _group_by_topic(
        statements: list[NormalizedStatement],
    ) -> dict[str, list[NormalizedStatement]]:
        """Group statements by their top-3 keywords (sorted, deduped)."""
        groups: dict[str, list[NormalizedStatement]] = defaultdict(list)
        for s in statements:
            key = " ".join(sorted(s.topic_keywords[:3]))
            if key:
                groups[key].append(s)
        return groups

    # ------------------------------------------------------------------
    # Anomaly detectors
    # ------------------------------------------------------------------

    def _check_impossible_sequence(
        self, dated: list[NormalizedStatement],
    ) -> list[TemporalAnomaly]:
        """Detect when the same speaker claims events in impossible order.

        Example: Speaker says event X happened before event Y in one
        statement, but after Y in another.
        """
        anomalies: list[TemporalAnomaly] = []
        by_speaker: dict[str, list[NormalizedStatement]] = defaultdict(list)
        for s in dated:
            by_speaker[s.original.speaker].append(s)

        for speaker, stmts in by_speaker.items():
            if len(stmts) < 2 or speaker == "Unknown":
                continue

            sorted_stmts = sorted(stmts, key=lambda s: s.date_normalized or "")
            for i in range(len(sorted_stmts) - 1):
                a, b = sorted_stmts[i], sorted_stmts[i + 1]
                da = self._parse_date(a.date_normalized)
                db = self._parse_date(b.date_normalized)
                if da and db and da > db:
                    anomalies.append(TemporalAnomaly(
                        statements_involved=[a, b],
                        anomaly_type="IMPOSSIBLE_SEQUENCE",
                        description=(
                            f"{speaker} claims event on {a.date_normalized} "
                            f"and a prior event on {b.date_normalized}."
                        ),
                        severity="MAJOR",
                    ))

        return anomalies

    def _check_duplicate_events(
        self, dated: list[NormalizedStatement],
    ) -> list[TemporalAnomaly]:
        """Detect when the same event is claimed at two different times."""
        anomalies: list[TemporalAnomaly] = []
        n = len(dated)
        for i in range(n):
            for j in range(i + 1, n):
                a, b = dated[i], dated[j]
                # Same speaker, very similar text, different dates
                if (
                    a.original.speaker == b.original.speaker
                    and a.original.speaker != "Unknown"
                    and a.date_normalized != b.date_normalized
                    and self._text_overlap(a, b) > 0.7
                ):
                    anomalies.append(TemporalAnomaly(
                        statements_involved=[a, b],
                        anomaly_type="DUPLICATE_EVENT",
                        description=(
                            f"{a.original.speaker} describes same event "
                            f"on {a.date_normalized} and {b.date_normalized}."
                        ),
                        severity="CRITICAL",
                    ))
        return anomalies

    def _check_duration_mismatch(
        self, group: list[NormalizedStatement],
    ) -> list[TemporalAnomaly]:
        """Detect conflicting duration claims about the same topic.

        Example: 'happened for 1 week' vs 'happened for 3 months'.
        """
        anomalies: list[TemporalAnomaly] = []
        durations: list[tuple[NormalizedStatement, int]] = []

        for s in group:
            dur = self._extract_duration(s.original.text)
            if dur is not None:
                durations.append((s, dur))

        for i in range(len(durations)):
            for j in range(i + 1, len(durations)):
                s_a, d_a = durations[i]
                s_b, d_b = durations[j]
                if d_a > 0 and d_b > 0:
                    ratio = max(d_a, d_b) / min(d_a, d_b)
                    if ratio >= 3.0:
                        anomalies.append(TemporalAnomaly(
                            statements_involved=[s_a, s_b],
                            anomaly_type="DURATION_MISMATCH",
                            description=(
                                f"Duration conflict: ~{d_a} days vs ~{d_b} days "
                                f"(ratio {ratio:.1f}x)."
                            ),
                            severity="MAJOR" if ratio >= 5.0 else "MINOR",
                        ))
        return anomalies

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _parse_date(iso: Optional[str]) -> Optional[datetime]:
        """Parse an ISO-8601 date string."""
        if not iso:
            return None
        try:
            return datetime.strptime(iso, "%Y-%m-%d")
        except ValueError:
            return None

    @staticmethod
    def _text_overlap(a: NormalizedStatement, b: NormalizedStatement) -> float:
        """Jaccard similarity of keyword sets."""
        sa = set(a.topic_keywords)
        sb = set(b.topic_keywords)
        union = sa | sb
        if not union:
            return 0.0
        return len(sa & sb) / len(union)

    @staticmethod
    def _extract_duration(text: str) -> Optional[int]:
        """Extract a duration in approximate days from text."""
        m = _DURATION_RE.search(text)
        if not m:
            return None
        amount = int(m.group(1))
        unit = m.group(2).lower()
        days_per = _DURATION_DAYS.get(unit, 0)
        return amount * days_per if days_per else None
