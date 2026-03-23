"""OMEGA-FLATTEN classifier — extension + content-based file classification.

LitigationOS Event Horizon Δ∞
"""
from __future__ import annotations

import os
import re
from typing import Dict, List, Optional

from .config import (
    CONTENT_PREVIEW_SIZE,
    EXTENSION_MAP,
    MAGIC_BYTES,
    MAGIC_READ_SIZE,
    MEEK_PATTERNS,
    MEEK_PRIORITY,
)

# ---------------------------------------------------------------------------
# Compiled regex patterns for legal-content detection
# ---------------------------------------------------------------------------

_LEGAL_PATTERNS: List[re.Pattern[str]] = [
    re.compile(r"\bMCL\s+\d+\.\d+", re.IGNORECASE),
    re.compile(r"\bMCR\s+\d+\.\d+", re.IGNORECASE),
    re.compile(r"\b\d{4}-\d{4,6}-[A-Z]{2}\b"),          # MI case numbers
    re.compile(r"\bCircuit\s+Court\b", re.IGNORECASE),
    re.compile(r"\bDistrict\s+Court\b", re.IGNORECASE),
    re.compile(r"\bProbate\s+Court\b", re.IGNORECASE),
    re.compile(r"\bCourt\s+of\s+Appeals\b", re.IGNORECASE),
    re.compile(r"\bSupreme\s+Court\b", re.IGNORECASE),
    re.compile(r"\bPlaintiff\b", re.IGNORECASE),
    re.compile(r"\bDefendant\b", re.IGNORECASE),
    re.compile(r"\bPetitioner\b", re.IGNORECASE),
    re.compile(r"\bRespondent\b", re.IGNORECASE),
    re.compile(r"\bMotion\s+(?:to|for)\b", re.IGNORECASE),
    re.compile(r"\bAffidavit\b", re.IGNORECASE),
    re.compile(r"\bORDER\b"),
    re.compile(r"\bJUDGMENT\b"),
    re.compile(r"\bSUBPOENA\b"),
]

_LEGAL_THRESHOLD = 3  # need ≥3 pattern matches to classify as LEGAL

# Pre-compile MEEK keyword patterns for speed
_MEEK_COMPILED: Dict[str, List[re.Pattern[str]]] = {}
for _mk, _mv in MEEK_PATTERNS.items():
    patterns: List[re.Pattern[str]] = []
    for kw in _mv["keywords"]:  # type: ignore[union-attr]
        patterns.append(re.compile(re.escape(kw), re.IGNORECASE))
    for cn in _mv["case_numbers"]:  # type: ignore[union-attr]
        patterns.append(re.compile(re.escape(cn)))
    _MEEK_COMPILED[_mk] = patterns


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def classify_file(filepath: str, extension: str) -> str:
    """Classify a file into one of the 30 taxonomy folders.

    Fast path: use the extension map.
    Slow path: peek at content for extensionless or ambiguous files.
    """
    # Fast path — known extension
    ext_lower = extension.lower()
    if ext_lower in EXTENSION_MAP:
        return EXTENSION_MAP[ext_lower]

    # Handle compound extensions like .tar.gz
    basename = os.path.basename(filepath).lower()
    if basename.endswith(".tar.gz") or basename.endswith(".tgz"):
        return "ARCHIVE"
    if basename.endswith(".tar.bz2"):
        return "ARCHIVE"
    if basename.endswith(".tar.xz"):
        return "ARCHIVE"

    # No extension or unknown extension — peek at content
    folder = _classify_by_content(filepath)
    if folder is not None:
        return folder

    return "_UNKNOWN"


def _classify_by_content(filepath: str) -> Optional[str]:
    """Peek at file content (magic bytes + text patterns) to classify."""
    try:
        with open(filepath, "rb") as fh:
            header = fh.read(max(MAGIC_READ_SIZE, 512))
    except (PermissionError, OSError):
        return None

    if not header:
        return None

    # Magic bytes check
    for magic, folder in MAGIC_BYTES.items():
        if header.startswith(magic):
            # Refine ZIP-based formats (DOCX/XLSX/PPTX are ZIP archives)
            if magic in (b"PK\x03\x04", b"PK\x05\x06"):
                return _refine_zip_type(header, filepath)
            return folder

    # Text heuristic — try to decode as UTF-8
    try:
        text = header.decode("utf-8", errors="strict")
    except UnicodeDecodeError:
        try:
            text = header.decode("latin-1", errors="replace")
        except Exception:
            return None

    # Check for legal content
    if _is_legal_content(text):
        return "LEGAL"

    # JSON heuristic
    stripped = text.lstrip()
    if stripped.startswith("{") or stripped.startswith("["):
        return "JSON"

    # XML/HTML heuristic
    if stripped.startswith("<?xml") or stripped.startswith("<"):
        if "<html" in stripped.lower():
            return "HTML"
        return "XML"

    # Markdown heuristic
    if stripped.startswith("# ") or stripped.startswith("---\n"):
        return "MD"

    # Config/YAML heuristic
    if re.match(r"^[a-zA-Z_][a-zA-Z0-9_]*\s*[:=]", stripped):
        return "CONFIG"

    # Python heuristic
    if stripped.startswith("#!/usr/bin/env python") or stripped.startswith("#!/usr/bin/python"):
        return "PY"
    if "import " in stripped[:200] and "def " in stripped[:500]:
        return "PY"

    # Shell heuristic
    if stripped.startswith("#!/bin/") or stripped.startswith("#!/usr/bin/env"):
        return "CODE"

    # Plain text fallback (if mostly printable)
    printable_ratio = sum(1 for c in text[:200] if c.isprintable() or c in "\n\r\t") / max(len(text[:200]), 1)
    if printable_ratio > 0.90:
        return "TXT"

    return None


def _refine_zip_type(header: bytes, filepath: str) -> str:
    """Distinguish DOCX/XLSX/PPTX from plain ZIP by checking internal paths."""
    # Read more if needed
    try:
        with open(filepath, "rb") as fh:
            data = fh.read(4096)
    except (PermissionError, OSError):
        return "ARCHIVE"

    data_str = data.decode("latin-1", errors="replace")

    if "word/" in data_str or "word/document.xml" in data_str:
        return "DOCX"
    if "xl/" in data_str or "xl/workbook.xml" in data_str:
        return "CSV"  # XLSX → tabular data folder
    if "ppt/" in data_str or "ppt/presentation.xml" in data_str:
        return "PPTX"
    if "[Content_Types].xml" in data_str:
        # Generic Office Open XML — default to DOCX
        return "DOCX"

    return "ARCHIVE"


def _is_legal_content(text: str) -> bool:
    """Return ``True`` if *text* contains enough legal-document indicators."""
    hits = sum(1 for pat in _LEGAL_PATTERNS if pat.search(text))
    return hits >= _LEGAL_THRESHOLD


# ---------------------------------------------------------------------------
# MEEK lane detection
# ---------------------------------------------------------------------------

def detect_meek_lane(filepath: str, content_preview: Optional[str] = None) -> Optional[str]:
    """Detect the MEEK litigation lane for a file.

    Scans *content_preview* (and optionally the filename/path) against
    compiled MEEK keyword patterns.  Returns the lane letter (``"A"``–``"F"``)
    for the highest-priority match, or ``None``.
    """
    text = ""
    if content_preview:
        text = content_preview
    # Always include the filepath itself
    text = text + " " + filepath

    text_lower = text.lower()

    # Scan in priority order: E → D → F → A → B
    for meek_key in MEEK_PRIORITY:
        patterns = _MEEK_COMPILED[meek_key]
        hit_count = sum(1 for pat in patterns if pat.search(text_lower))
        if hit_count >= 2:
            return MEEK_PATTERNS[meek_key]["lane"]  # type: ignore[return-value]

    # Single-hit pass (weaker signal — still useful)
    for meek_key in MEEK_PRIORITY:
        patterns = _MEEK_COMPILED[meek_key]
        for pat in patterns:
            if pat.search(text_lower):
                return MEEK_PATTERNS[meek_key]["lane"]  # type: ignore[return-value]

    return None


def read_content_preview(filepath: str, max_bytes: int = CONTENT_PREVIEW_SIZE) -> Optional[str]:
    """Read the first *max_bytes* of a text file and return as string.

    Returns ``None`` if the file can't be read or is binary.
    """
    try:
        size = os.path.getsize(filepath)
    except (PermissionError, OSError):
        return None

    if size == 0:
        return ""

    try:
        with open(filepath, "rb") as fh:
            raw = fh.read(max_bytes)
    except (PermissionError, OSError):
        return None

    # Detect binary — if >10% of bytes are non-text, treat as binary
    non_text = sum(1 for b in raw[:512] if b < 8 or (14 <= b < 32 and b != 27))
    if len(raw[:512]) > 0 and non_text / len(raw[:512]) > 0.10:
        return None

    for encoding in ("utf-8", "utf-16", "latin-1"):
        try:
            return raw.decode(encoding, errors="replace")
        except Exception:
            continue

    return None
