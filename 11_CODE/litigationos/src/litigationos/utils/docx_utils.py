"""DOCX utility functions — document creation and manipulation.

Provides helpers for creating court-formatted DOCX documents
using python-docx with proper styling and margins.
"""

from __future__ import annotations

from pathlib import Path


def create_court_document(
    title: str,
    body: str,
    output_path: str | Path,
    caption: str | None = None,
) -> Path:
    """Create a court-formatted DOCX document.

    Args:
        title: Document title
        body: Document body text (markdown or plain text)
        output_path: Output file path
        caption: Optional case caption block

    Returns:
        Path to the created DOCX file
    """
    # TODO: Use python-docx to create formatted court document
    raise NotImplementedError("DOCX creation not yet implemented")


def extract_text(docx_path: str | Path) -> str:
    """Extract text content from a DOCX file."""
    # TODO: Read DOCX and return plain text
    raise NotImplementedError("DOCX text extraction not yet implemented")


def get_word_count(docx_path: str | Path) -> int:
    """Count words in a DOCX file."""
    text = extract_text(docx_path)
    return len(text.split())
