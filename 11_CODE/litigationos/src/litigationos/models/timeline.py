"""Timeline event model — represents a chronological event in a case.

Maps to the `timeline_events` table. Timeline events link filings,
evidence, and key dates into a visual case chronology.
"""

from __future__ import annotations

from typing import Optional

from pydantic import BaseModel, ConfigDict


class TimelineEvent(BaseModel):
    """A timeline event in a case."""

    id: Optional[int] = None
    case_id: int
    event_date: str
    title: str
    description: Optional[str] = None
    event_type: Optional[str] = None  # 'filing', 'hearing', 'order', 'communication', 'incident', 'deadline'
    evidence_ids: Optional[str] = None  # JSON array of evidence IDs
    filing_id: Optional[int] = None
    importance: str = "normal"  # 'critical', 'high', 'normal', 'low'

    model_config = ConfigDict(from_attributes=True)
