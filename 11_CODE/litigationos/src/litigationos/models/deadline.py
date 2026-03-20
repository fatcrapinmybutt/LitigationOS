"""Deadline model — represents a case deadline with rule basis.

Maps to the `deadlines` table. Deadlines are auto-calculated from court rules
and tracked with priority levels and reminder settings.
"""

from __future__ import annotations

from typing import Optional

from pydantic import BaseModel, ConfigDict


class Deadline(BaseModel):
    """A case deadline."""

    id: Optional[int] = None
    case_id: int
    filing_id: Optional[int] = None
    title: str
    due_date: str
    rule_basis: Optional[str] = None  # e.g., 'MCR 7.212(A)(1)(a) - 56 days from claim of appeal'
    status: str = "pending"  # 'pending', 'extended', 'met', 'missed'
    priority: str = "normal"  # 'critical', 'high', 'normal', 'low'
    reminder_days: int = 7
    notes: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)
