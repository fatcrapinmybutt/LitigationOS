"""Filing model — represents a court filing (motion, brief, complaint, etc.).

Maps to the `filings` table. Filings track status from draft through filed/served,
with compliance scoring against court rules.
"""

from __future__ import annotations

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field


class Filing(BaseModel):
    """A court filing."""

    id: Optional[int] = None
    case_id: int
    title: str
    filing_type: Optional[str] = None  # 'complaint', 'motion', 'brief', 'response', 'reply', 'order', 'notice'
    status: str = "draft"  # 'draft', 'review', 'ready', 'filed', 'served'
    file_path: Optional[str] = None
    filed_date: Optional[str] = None
    served_date: Optional[str] = None
    compliance_score: Optional[float] = None
    word_count: Optional[int] = None
    notes: Optional[str] = None
    created_at: Optional[datetime] = Field(default_factory=datetime.now)

    model_config = ConfigDict(from_attributes=True)
