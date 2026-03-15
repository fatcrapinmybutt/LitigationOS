"""
agent_base — Shared primitives for the LitigationOS agent pipeline.

This module is the single source of truth for:
- Core data models (EvidenceAtom, ChronoEvent)
- Utility helpers (uuid_str, sha256_file, guess_media_type, write_jsonl)

Every agent in the pipeline imports exclusively from this module so that the
data contracts stay consistent across the full evidence → chronology → filing
workflow.

Quick-start example
-------------------
>>> from pathlib import Path
>>> from agents.agent_base import EvidenceAtom, ChronoEvent, uuid_str, sha256_file, guess_media_type, write_jsonl
>>>
>>> # Create an evidence atom for a scanned PDF
>>> atom = EvidenceAtom(
...     atom_id=uuid_str(),
...     case_id="2024-001507-DC",
...     meek_track="MEEK2",
...     atom_type="Document",
...     source_path="/evidence/order_2024_08_08.pdf",
...     source_media_type="application/pdf",
...     recorded_time="2024-08-08T12:00:00+00:00",
...     sha256="abc123",
...     notes="Ex parte order stripping parenting time",
... )
>>>
>>> # Serialize a list of atoms to JSONL for the run ledger
>>> write_jsonl(Path("/tmp/atoms.jsonl"), [atom.__dict__])
"""

from __future__ import annotations

import hashlib
import json
import mimetypes
import uuid
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional

# ---------------------------------------------------------------------------
# Utility helpers
# ---------------------------------------------------------------------------

def uuid_str() -> str:
    """Return a new random UUID as a lowercase hyphenated string.

    Example
    -------
    >>> uid = uuid_str()
    >>> len(uid)
    36
    >>> uid.count("-")
    4
    """
    return str(uuid.uuid4())


def sha256_file(path: Path, chunk_size: int = 1 << 20) -> str:
    """Return the SHA-256 hex digest of *path*.

    Reads the file in *chunk_size* byte chunks so large files do not exhaust
    memory.

    Parameters
    ----------
    path:
        File to hash.  Must exist and be readable.
    chunk_size:
        Read buffer size in bytes (default 1 MiB).

    Returns
    -------
    str
        64-character lowercase hex digest.

    Example
    -------
    >>> import hashlib
    >>> expected = hashlib.sha256(b"hello world").hexdigest()
    >>> import tempfile, pathlib
    >>> with tempfile.NamedTemporaryFile(delete=False) as f:
    ...     _ = f.write(b"hello world")
    ...     tmp = pathlib.Path(f.name)
    >>> sha256_file(tmp) == expected
    True
    """
    h = hashlib.sha256()
    with path.open("rb") as fh:
        while True:
            chunk = fh.read(chunk_size)
            if not chunk:
                break
            h.update(chunk)
    return h.hexdigest()


_EXTENSION_MAP: Dict[str, str] = {
    ".pdf":  "application/pdf",
    ".doc":  "application/msword",
    ".docx": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    ".txt":  "text/plain",
    ".md":   "text/markdown",
    ".jpg":  "image/jpeg",
    ".jpeg": "image/jpeg",
    ".png":  "image/png",
    ".tif":  "image/tiff",
    ".tiff": "image/tiff",
    ".csv":  "text/csv",
    ".json": "application/json",
    ".xml":  "application/xml",
    ".zip":  "application/zip",
    ".mp4":  "video/mp4",
    ".mp3":  "audio/mpeg",
    ".wav":  "audio/wav",
}


def guess_media_type(path: Path) -> str:
    """Return the MIME type for *path* based on its file extension.

    Falls back to ``"application/octet-stream"`` for unknown extensions.

    Parameters
    ----------
    path:
        File whose extension determines the MIME type.

    Returns
    -------
    str
        MIME type string, e.g. ``"application/pdf"``.

    Example
    -------
    >>> from pathlib import Path
    >>> guess_media_type(Path("hearing_transcript.pdf"))
    'application/pdf'
    >>> guess_media_type(Path("photo.jpg"))
    'image/jpeg'
    >>> guess_media_type(Path("unknown.abc123"))
    'application/octet-stream'
    """
    ext = path.suffix.lower()
    if ext in _EXTENSION_MAP:
        return _EXTENSION_MAP[ext]
    # stdlib fallback
    guessed, _ = mimetypes.guess_type(str(path))
    return guessed or "application/octet-stream"


def write_jsonl(path: Path, records: Iterable[Dict[str, Any]]) -> None:
    """Write *records* to *path* in newline-delimited JSON (JSONL) format.

    The parent directory is created automatically if it does not exist.
    Any existing file at *path* is overwritten.

    Parameters
    ----------
    path:
        Destination file.
    records:
        Iterable of JSON-serialisable dicts.

    Example
    -------
    >>> import tempfile, pathlib, json
    >>> tmp = pathlib.Path(tempfile.mktemp(suffix=".jsonl"))
    >>> write_jsonl(tmp, [{"id": 1, "v": "a"}, {"id": 2, "v": "b"}])
    >>> lines = tmp.read_text().splitlines()
    >>> json.loads(lines[0])
    {'id': 1, 'v': 'a'}
    """
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as fh:
        for rec in records:
            fh.write(json.dumps(rec, ensure_ascii=False, default=str) + "\n")


# ---------------------------------------------------------------------------
# Core data models
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class EvidenceAtom:
    """Immutable unit of evidence produced by :mod:`agents.evidence_agent`.

    Each atom represents a single source file discovered during a scan.  The
    atom carries just enough metadata to reconstruct a chain of custody and to
    feed downstream agents — it deliberately stores **no** extracted text so
    that the object stays serialisable and memory-efficient.

    Fields
    ------
    atom_id:
        Globally unique identifier (UUID4 string).
    case_id:
        Docket number or arbitrary case identifier string,
        e.g. ``"2024-001507-DC"``.
    meek_track:
        Case-lane classifier: one of ``MEEK1`` (housing), ``MEEK2``
        (custody), ``MEEK3`` (PPO/contempt), ``MEEK4`` (JTC/judicial
        conduct), ``MEEK5`` (appellate/other).
    atom_type:
        High-level file category: ``"Document"``, ``"Photo"``, or
        ``"Other"``.
    source_path:
        Absolute path (as string) to the source file at the time of
        ingestion.
    source_media_type:
        MIME type, e.g. ``"application/pdf"``.
    recorded_time:
        ISO-8601 timestamp of when the file was recorded by the
        EvidenceAgent (typically the file's ``mtime``).
    sha256:
        SHA-256 hex digest of the file at ingestion time.  Used for
        deduplication and chain-of-custody verification.
    notes:
        Optional free-text annotation.

    Example
    -------
    >>> from agents.agent_base import EvidenceAtom, uuid_str
    >>> atom = EvidenceAtom(
    ...     atom_id=uuid_str(),
    ...     case_id="2024-001507-DC",
    ...     meek_track="MEEK2",
    ...     atom_type="Document",
    ...     source_path="/scans/order_2024_08_08.pdf",
    ...     source_media_type="application/pdf",
    ...     recorded_time="2024-08-08T12:00:00+00:00",
    ...     sha256="abc123def456",
    ...     notes=None,
    ... )
    >>> atom.meek_track
    'MEEK2'
    """

    atom_id: str
    case_id: str
    meek_track: str
    atom_type: str
    source_path: str
    source_media_type: str
    recorded_time: str
    sha256: str
    notes: Optional[str] = None


@dataclass(frozen=True)
class ChronoEvent:
    """Immutable chronological event derived by :mod:`agents.chronology_agent`.

    The ChronologyAgent inspects each :class:`EvidenceAtom` and emits a
    corresponding ``ChronoEvent``.  Events are sorted by
    ``occurrence_time`` to produce the case timeline.

    Fields
    ------
    event_id:
        Globally unique identifier (UUID4 string).
    case_id:
        Docket number or case identifier (mirrors the source atom).
    meek_track:
        Case-lane classifier (mirrors the source atom).
    event_type:
        Inferred category: ``"Order"``, ``"Hearing"``, ``"Filing"``,
        ``"Service"``, ``"Notice"``, ``"Violation"``, ``"Payment"``,
        or ``"Other"``.
    recorded_time:
        ISO-8601 timestamp from the source ``EvidenceAtom``.
    occurrence_time:
        ISO-8601 timestamp representing when the legal event *occurred*,
        either extracted from the filename (``YYYY-MM-DD`` pattern) or
        falling back to ``recorded_time``.
    title:
        Human-readable label (usually the source filename).
    description:
        Free-text summary explaining how the event was derived.
    linked_atoms:
        List of ``atom_id`` values that produced this event.  Almost
        always a single-element list for file-derived events.

    Example
    -------
    >>> from agents.agent_base import ChronoEvent, uuid_str
    >>> ev = ChronoEvent(
    ...     event_id=uuid_str(),
    ...     case_id="2024-001507-DC",
    ...     meek_track="MEEK3",
    ...     event_type="Hearing",
    ...     recorded_time="2024-11-15T12:00:00+00:00",
    ...     occurrence_time="2024-11-15T09:00:00+00:00",
    ...     title="show_cause_hearing_2024_11_15.pdf",
    ...     description="Derived from EvidenceAtom abc-123",
    ...     linked_atoms=["abc-123"],
    ... )
    >>> ev.event_type
    'Hearing'
    """

    event_id: str
    case_id: str
    meek_track: str
    event_type: str
    recorded_time: str
    occurrence_time: str
    title: str
    description: str
    linked_atoms: List[str]
