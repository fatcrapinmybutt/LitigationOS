"""
ChronologyAgent: derive ChronoEvents from EvidenceAtoms using filename/title heuristics.
This is deterministic and append-only; it never edits existing events, only emits new ones.
"""

from __future__ import annotations
from pathlib import Path
from typing import List
import datetime
import logging
import re

from agents.agent_base import ChronoEvent, EvidenceAtom, uuid_str

logger = logging.getLogger(__name__)

# Heuristics for event type
KEYWORDS = [
    ("Order", ["order after hearing", "order", "judgment"]),
    ("Hearing", ["hearing", "show cause", "osc"]),
    ("Filing", ["motion", "petition", "complaint", "affidavit", "brief"]),
    ("Service", ["proof of service", "return of service", "served"]),
    ("Notice", ["notice"]),
    ("Violation", ["violation", "contempt"]),
    ("Payment", ["fine", "payment"]),
]

def infer_event_type(path_str: str) -> str:
    s = path_str.lower()
    for evt, kws in KEYWORDS:
        for k in kws:
            if k in s:
                return evt
    return "Other"

DATE_RE = re.compile(r"(20\d{2})[-_/\.](0[1-9]|1[0-2])[-_/\.]([0-2]\d|3[01])")

def infer_occurrence_time(atom: EvidenceAtom) -> str:
    # Use embedded YYYY-MM-DD patterns in path if present; else recorded_time.
    m = DATE_RE.search(atom.source_path)
    if m:
        y, mo, d = m.group(1), m.group(2), m.group(3)
        dt = datetime.datetime(int(y), int(mo), int(d), 12, 0, tzinfo=datetime.timezone.utc).astimezone()
        return dt.isoformat()
    return atom.recorded_time

def build_events(atoms: List[EvidenceAtom]) -> List[ChronoEvent]:
    events: List[ChronoEvent] = []
    skipped = 0
    for a in atoms:
        try:
            t = infer_occurrence_time(a)
            ev = ChronoEvent(
                event_id=uuid_str(),
                case_id=a.case_id,
                meek_track=a.meek_track,
                event_type=infer_event_type(a.source_path),
                recorded_time=a.recorded_time,
                occurrence_time=t,
                title=Path(a.source_path).name,
                description=f"Derived from EvidenceAtom {a.atom_id}",
                linked_atoms=[a.atom_id],
            )
            events.append(ev)
        except Exception as e:
            skipped += 1
            logger.warning("Skipping atom %s: %s", a.atom_id, e)
            continue
    if skipped:
        logger.info("ChronologyAgent: built %d events, skipped %d atoms", len(events), skipped)
    events.sort(key=lambda e: e.occurrence_time)
    return events
