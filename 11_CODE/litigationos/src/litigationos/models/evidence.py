"""Evidence model — represents a piece of evidence with Bates numbering.

Maps to the `evidence` table. Evidence items are tracked with authentication
methods, relevance scoring, and full-text search via FTS5.
"""

from __future__ import annotations

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field


class Evidence(BaseModel):
    """A piece of case evidence."""

    id: Optional[int] = None
    case_id: int
    bates_number: Optional[str] = None  # e.g., 'PIGORS-0001'
    title: str
    description: Optional[str] = None
    file_path: Optional[str] = None
    file_type: Optional[str] = None  # 'pdf', 'image', 'text', 'email', 'screenshot', 'document'
    source: Optional[str] = None
    date_created: Optional[str] = None
    date_imported: Optional[datetime] = Field(default_factory=datetime.now)
    authentication_method: Optional[str] = None  # 'self_auth_902', 'witness_901', 'certification', 'stipulation'
    foundation_witness: Optional[str] = None
    relevance_score: Optional[float] = None
    tags: Optional[str] = None  # JSON array of tags
    notes: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)
