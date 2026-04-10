"""
Data models for the Chronological Narrative Engine.

Provides typed representations of narrative events, severity levels,
and utility helpers for JSON field serialization.
"""

import json
import logging
from dataclasses import dataclass, field
from datetime import date, datetime
from enum import Enum
from typing import List, Optional

logger = logging.getLogger(__name__)

SEPARATION_DATE = date(2025, 7, 29)


class SeverityLevel(Enum):
    """Severity classification for narrative events."""
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"

    @classmethod
    def at_least(cls, minimum: str) -> list:
        """Return severity values at or above the given minimum."""
        order = [cls.CRITICAL, cls.HIGH, cls.MEDIUM, cls.LOW]
        names = [s.value for s in order]
        try:
            idx = names.index(minimum.lower())
        except ValueError:
            idx = len(names) - 1
        return names[: idx + 1]


def _parse_json_field(raw: Optional[str]) -> list:
    """Safely parse a JSON array field, returning [] on failure."""
    if not raw:
        return []
    try:
        parsed = json.loads(raw)
        return parsed if isinstance(parsed, list) else [parsed]
    except (json.JSONDecodeError, TypeError):
        return []


def _dump_json_field(items: Optional[list]) -> str:
    """Serialize a list to a JSON string for DB storage."""
    if items is None:
        return "[]"
    return json.dumps(items, ensure_ascii=False)


@dataclass
class NarrativeEvent:
    """A single event in the chronological narrative, linked to evidence
    and legal claims."""

    id: Optional[int] = None
    event_date: str = ""
    event_summary: str = ""
    detailed_narrative: Optional[str] = None
    lane: Optional[str] = None
    claim_elements: List[str] = field(default_factory=list)
    evidence_refs: List[str] = field(default_factory=list)
    timeline_event_ids: List[str] = field(default_factory=list)
    exhibit_refs: List[str] = field(default_factory=list)
    legal_significance: Optional[str] = None
    actors: List[str] = field(default_factory=list)
    severity: str = "medium"
    narrative_order: Optional[int] = None
    created_at: Optional[str] = None
    tags: List[str] = field(default_factory=list)

    @classmethod
    def from_row(cls, row: tuple, columns: list) -> "NarrativeEvent":
        """Construct from a DB row and column-name list."""
        data = dict(zip(columns, row))
        json_fields = [
            "claim_elements", "evidence_refs", "timeline_event_ids",
            "exhibit_refs", "actors", "tags",
        ]
        for fld in json_fields:
            if fld in data:
                data[fld] = _parse_json_field(data.get(fld))
        return cls(**data)

    def to_insert_tuple(self) -> tuple:
        """Return a tuple suitable for INSERT into narrative_events."""
        return (
            self.event_date,
            self.event_summary,
            self.detailed_narrative,
            self.lane,
            _dump_json_field(self.claim_elements),
            _dump_json_field(self.evidence_refs),
            _dump_json_field(self.timeline_event_ids),
            _dump_json_field(self.exhibit_refs),
            self.legal_significance,
            _dump_json_field(self.actors),
            self.severity,
            self.narrative_order,
            _dump_json_field(self.tags),
        )

    @staticmethod
    def separation_days() -> int:
        """Days since last contact with L.D.W. (July 29, 2025). Always dynamic."""
        return (date.today() - SEPARATION_DATE).days

    def date_obj(self) -> Optional[date]:
        """Parse event_date to a date object."""
        try:
            return datetime.strptime(self.event_date[:10], "%Y-%m-%d").date()
        except (ValueError, TypeError):
            return None
