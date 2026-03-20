"""PDF utility functions — reading, text extraction, and basic generation.

Provides helpers for extracting text from PDF files and generating
simple PDF documents using reportlab.
"""

from __future__ import annotations

from pathlib import Path


def extract_text(pdf_path: str | Path) -> str:
    """Extract text content from a PDF file.

    Args:
        pdf_path: Path to the PDF file

    Returns:
        Extracted text as a string
    """
    # TODO: Implement PDF text extraction (PyPDF2 or pdfplumber)
    raise NotImplementedError("PDF text extraction not yet implemented")


def get_page_count(pdf_path: str | Path) -> int:
    """Get the number of pages in a PDF file."""
    # TODO: Implement page counting
    raise NotImplementedError("PDF page counting not yet implemented")


def merge_pdfs(pdf_paths: list[str | Path], output_path: str | Path) -> Path:
    """Merge multiple PDF files into one.

    Args:
        pdf_paths: List of PDF file paths to merge
        output_path: Path for the merged output file

    Returns:
        Path to the merged PDF
    """
    # TODO: Implement PDF merging
    raise NotImplementedError("PDF merging not yet implemented")
