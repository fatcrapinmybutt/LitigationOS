"""
EvidenceAgent: scan folders, build EvidenceAtoms, optionally extract light text metadata.

- By default, recorded_time is file mtime (ISO).
- occurrence_time is left None unless heuristics identify an embedded date.
"""

from __future__ import annotations
from pathlib import Path
from typing import Dict, List, Optional, Tuple
import datetime
import os
import re

from agents.agent_base import EvidenceAtom, guess_media_type, sha256_file, uuid_str

DATE_RE = re.compile(r"(20\d{2})[-_/\.](0[1-9]|1[0-2])[-_/\.]([0-2]\d|3[01])")

def iso_from_mtime(p: Path) -> str:
    mtime = datetime.datetime.fromtimestamp(p.stat().st_mtime, tz=datetime.timezone.utc).astimezone()
    return mtime.isoformat()

def infer_meek_track(case_id: str, path: Path) -> str:
    s = (case_id + " " + str(path)).lower()
    if "lt" in s or "landlord" in s or "shady" in s or "homes of america" in s:
        return "MEEK1"
    if "dc" in s or "custody" in s or "foc" in s or "parenting" in s:
        return "MEEK2"
    if "pp" in s or "ppo" in s or "contempt" in s:
        return "MEEK3"
    if "jtc" in s or "canon" in s or "disqual" in s:
        return "MEEK4"
    return "MEEK5"

def infer_atom_type(path: Path) -> str:
    ext = path.suffix.lower()
    if ext in {".jpg",".jpeg",".png"}:
        return "Photo"
    if ext in {".pdf",".doc",".docx",".txt",".md"}:
        return "Document"
    return "Other"

def scan_files(root: Path, include_ext: Optional[List[str]] = None) -> List[Path]:
    include = set([e.lower() for e in (include_ext or [".pdf",".docx",".txt",".md",".jpg",".jpeg",".png"])])
    out: List[Path] = []
    for p in root.rglob("*"):
        if p.is_file() and p.suffix.lower() in include:
            out.append(p)
    return sorted(out)

def build_atoms(case_id: str, root: Path) -> List[EvidenceAtom]:
    atoms: List[EvidenceAtom] = []
    for p in scan_files(root):
        meek = infer_meek_track(case_id, p)
        atom = EvidenceAtom(
            atom_id=uuid_str(),
            case_id=case_id,
            meek_track=meek,
            atom_type=infer_atom_type(p),
            source_path=str(p),
            source_media_type=guess_media_type(p),
            recorded_time=iso_from_mtime(p),
            sha256=sha256_file(p),
            notes=None,
        )
        atoms.append(atom)
    return atoms
