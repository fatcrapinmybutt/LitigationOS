"""
LitigationOS Claude API Integration Package.

Optional Claude-powered augmentations for the litigation pipeline.
Gracefully degrades when no API key is available — all public functions
return a sentinel result with ``available=False`` so callers never crash.

Modules:
    client              Shared Anthropic client, retry, cost tracking
    classifier          Smart lane classification for ambiguous documents
    evidence_linker     Evidence-to-claim linkage with confidence scores
    deadline_risk       Deadline risk assessment with action items
"""

from .client import get_client, ClaudeConfig, is_available  # noqa: F401

__version__ = "0.1.0"
