"""Claim model — represents a legal claim or count within a case.

Maps to the `claims` table. Each claim cites a legal basis (e.g., MCL statute)
and is directed against a specific party.
"""

from __future__ import annotations

from typing import Optional

from pydantic import BaseModel, ConfigDict


class Claim(BaseModel):
    """A legal claim or count in a case."""

    id: Optional[int] = None
    case_id: int
    count_number: Optional[int] = None
    title: str  # e.g., 'Count I: Intentional Infliction of Emotional Distress'
    legal_basis: Optional[str] = None  # e.g., 'MCL 600.2911'
    against_party_id: Optional[int] = None
    status: str = "active"
    damages_sought: Optional[float] = None
    notes: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)
