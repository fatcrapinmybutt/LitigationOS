"""Template model — represents a Jinja2 document template.

Maps to the `templates` table. Templates are jurisdiction-aware and
define the structure of court filings with variable placeholders.
"""

from __future__ import annotations

from typing import Optional

from pydantic import BaseModel, ConfigDict


class Template(BaseModel):
    """A document template."""

    id: Optional[int] = None
    jurisdiction_id: Optional[str] = None
    name: str
    template_type: Optional[str] = None  # 'motion', 'brief', 'complaint', 'order', 'service', 'affidavit'
    content: str  # Jinja2 template content
    variables: Optional[str] = None  # JSON schema of required variables
    court_rule: Optional[str] = None  # MCR/FRCP rule this template follows
    notes: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)
