"""Case model — represents a litigation case.

Maps to the `cases` table. A case is the top-level container linking
parties, claims, filings, deadlines, evidence, and timeline events.
"""

from __future__ import annotations

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field


class Case(BaseModel):
    """A litigation case."""

    id: Optional[int] = None
    case_number: Optional[str] = None
    court_id: Optional[int] = None
    case_type: Optional[str] = None  # 'family', 'civil', 'criminal', 'appellate', 'federal'
    title: str
    filed_date: Optional[str] = None
    status: str = "active"  # 'active', 'closed', 'appealed', 'settled'
    notes: Optional[str] = None
    created_at: Optional[datetime] = Field(default_factory=datetime.now)
    updated_at: Optional[datetime] = Field(default_factory=datetime.now)

    model_config = ConfigDict(from_attributes=True)
