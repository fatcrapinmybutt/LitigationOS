"""
LitigationOS Agents (MI-only) - reference implementation.

Design goals:
- Deterministic, local-first, append-only outputs.
- Produces EvidenceAtoms and ChronoEvents with stable IDs.
- No network calls by default.
"""

from __future__ import annotations
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional
import json
import uuid
import os
import hashlib
import datetime

def now_iso() -> str:
    return datetime.datetime.now(datetime.timezone.utc).astimezone().isoformat()

def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()

def uuid_str() -> str:
    return str(uuid.uuid4())

@dataclass(frozen=True)
class EvidenceAtom:
    atom_id: str
    case_id: str
    meek_track: str
    atom_type: str
    source_path: str
    source_media_type: str
    recorded_time: str
    occurrence_time: Optional[str] = None
    tags: Optional[List[str]] = None
    reliability_score: Optional[float] = None
    sha256: Optional[str] = None
    notes: Optional[str] = None

@dataclass(frozen=True)
class ChronoEvent:
    event_id: str
    case_id: str
    meek_track: str
    event_type: str
    recorded_time: str
    occurrence_time: str
    title: str
    description: str
    linked_atoms: List[str]

def write_jsonl(path: Path, rows: Iterable[Dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as f:
        for r in rows:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")

def guess_media_type(p: Path) -> str:
    ext = p.suffix.lower()
    return {
        ".pdf": "application/pdf",
        ".docx": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        ".doc": "application/msword",
        ".txt": "text/plain",
        ".md": "text/markdown",
        ".jpg": "image/jpeg",
        ".jpeg": "image/jpeg",
        ".png": "image/png",
    }.get(ext, "application/octet-stream")
