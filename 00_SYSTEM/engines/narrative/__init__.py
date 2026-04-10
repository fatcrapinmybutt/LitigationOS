"""
Chronological Narrative Engine for LitigationOS.

Connects timeline events to evidence and legal significance so court filings
can tell the story in order. Supports circuit court, appellate, federal, and
emergency motion output formats.
"""

from .models import NarrativeEvent, SeverityLevel
from .builder import NarrativeBuilder
from .formatter import NarrativeFormatter

__all__ = [
    "NarrativeEvent",
    "SeverityLevel",
    "NarrativeBuilder",
    "NarrativeFormatter",
]
