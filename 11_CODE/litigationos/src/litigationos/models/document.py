"""Document model — represents a generated document (from a template).

Maps to the `documents` table. Documents are generated from Jinja2 templates
and output as DOCX or PDF files.
"""

from __future__ import annotations

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field


class Document(BaseModel):
    """A generated document."""

    id: Optional[int] = None
    filing_id: Optional[int] = None
    template_id: Optional[int] = None
    title: str
    content: Optional[str] = None  # Markdown content
    output_path: Optional[str] = None  # Generated DOCX/PDF path
    format: str = "md"  # 'md', 'docx', 'pdf'
    variables: Optional[str] = None  # JSON of template variables used
    created_at: Optional[datetime] = Field(default_factory=datetime.now)

    model_config = ConfigDict(from_attributes=True)
