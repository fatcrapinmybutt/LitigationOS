"""
agent_base: Shared data contracts and utilities for the LitigationOS agent fleet.

Provides:
  - EvidenceAtom — immutable record of a single evidence file
  - ChronoEvent  — a dated event derived from one or more atoms
  - guess_media_type — MIME helper
  - sha256_file       — file integrity hash
  - uuid_str          — random UUID as string
  - write_jsonl       — append-only JSONL writer
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional

import hashlib
import json
import logging
import mimetypes
import uuid

logger = logging.getLogger(__name__)


# ── Utilities ────────────────────────────────────────────────────────────────

def uuid_str() -> str:
    """Return a random UUID as a lower-case hex string."""
    return str(uuid.uuid4())


def sha256_file(path: Path) -> str:
    """Return the hex SHA-256 digest of *path*; empty string on any error."""
    h = hashlib.sha256()
    try:
        with open(path, "rb") as fh:
            for chunk in iter(lambda: fh.read(65536), b""):
                h.update(chunk)
        return h.hexdigest()
    except Exception as exc:
        logger.warning("sha256_file(%s): %s", path, exc)
        return ""


def guess_media_type(path: Path) -> str:
    """Return a MIME type string for *path*; falls back to 'application/octet-stream'."""
    mt, _ = mimetypes.guess_type(str(path))
    return mt or "application/octet-stream"


def write_jsonl(path: Path, rows: List[Dict[str, Any]]) -> None:
    """Write *rows* to a JSONL file at *path*, creating parent directories as needed."""
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as fh:
        for row in rows:
            fh.write(json.dumps(row, ensure_ascii=False, default=str) + "\n")


# ── Core data contracts ───────────────────────────────────────────────────────

@dataclass
class EvidenceAtom:
    """An immutable record representing a single piece of evidence (file).

    Fields
    ------
    atom_id           : Unique identifier (UUID string).
    case_id           : Lane/case identifier (e.g. '2024-001507-DC').
    meek_track        : MEEK lane classification (MEEK1–MEEK5).
    atom_type         : High-level type: Document | Photo | Audio | Video | Other.
    source_path       : Absolute path to the evidence file.
    source_media_type : MIME type (e.g. 'application/pdf').
    recorded_time     : ISO-8601 timestamp when the file was last modified.
    sha256            : Hex SHA-256 digest for integrity verification.
    occurrence_time   : ISO-8601 timestamp of when the underlying event occurred
                        (may be extracted from filename/metadata; None if unknown).
    notes             : Free-text annotations.
    """

    atom_id: str
    case_id: str
    meek_track: str
    atom_type: str
    source_path: str
    source_media_type: str
    recorded_time: str
    sha256: str
    occurrence_time: Optional[str] = None
    notes: Optional[str] = None


@dataclass
class ChronoEvent:
    """A dated event derived from one or more EvidenceAtoms.

    Fields
    ------
    event_id        : Unique identifier (UUID string).
    case_id         : Lane/case identifier.
    meek_track      : MEEK lane classification.
    event_type      : Order | Hearing | Filing | Service | Notice |
                      Violation | Payment | Other.
    recorded_time   : ISO-8601 file-system timestamp.
    occurrence_time : ISO-8601 best estimate of when the event occurred.
    title           : Short human-readable title (often the filename).
    description     : Longer description or derivation note.
    linked_atoms    : List of atom_id values that produced this event.
    """

    event_id: str
    case_id: str
    meek_track: str
    event_type: str
    recorded_time: str
    occurrence_time: str
    title: str
    description: str
    linked_atoms: List[str] = field(default_factory=list)
