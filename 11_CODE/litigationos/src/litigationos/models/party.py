"""Party model — represents a party in a litigation case.

Maps to the `parties` table. Parties include plaintiffs, defendants,
attorneys, judges, and other participants.
"""

from __future__ import annotations

from typing import Optional

from pydantic import BaseModel, ConfigDict


class Party(BaseModel):
    """A party involved in a case."""

    id: Optional[int] = None
    case_id: int
    name: str
    role: str  # 'plaintiff', 'defendant', 'respondent', 'petitioner', 'intervenor', 'judge', 'attorney'
    party_type: Optional[str] = None  # 'individual', 'corporation', 'government', 'organization'
    bar_number: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    address: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)
