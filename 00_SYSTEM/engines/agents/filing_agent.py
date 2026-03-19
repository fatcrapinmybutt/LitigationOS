"""
FilingAgent: builds an Artifact "packet shell" from Case + Events + selected Vehicles.

This does NOT draft legal content here; it produces the *packet structure*:
- cover sheet metadata
- exhibit matrix (from EvidenceAtoms)
- timeline summary (from ChronoEvents)
- authority list (from AuthorityTriples if present)
- run ledger + manifest entry
"""

from __future__ import annotations
from pathlib import Path
from typing import Any, Dict, List
import json
import datetime
import uuid

from agents.agent_base import EvidenceAtom, ChronoEvent, uuid_str

def build_exhibit_matrix(atoms: List[EvidenceAtom]) -> List[Dict[str, Any]]:
    rows = []
    for i, a in enumerate(atoms, start=1):
        rows.append({
            "exhibit_no": i,
            "atom_id": a.atom_id,
            "meek_track": a.meek_track,
            "type": a.atom_type,
            "source_path": a.source_path,
            "sha256": a.sha256,
        })
    return rows

def build_timeline(events: List[ChronoEvent]) -> List[Dict[str, Any]]:
    return [{
        "occurrence_time": e.occurrence_time,
        "event_type": e.event_type,
        "title": e.title,
        "linked_atoms": e.linked_atoms,
    } for e in events]

def build_packet(case_id: str, meek_track: str, atoms: List[EvidenceAtom], events: List[ChronoEvent]) -> Dict[str, Any]:
    artifact_id = uuid_str()
    ts = datetime.datetime.now(datetime.timezone.utc).astimezone().isoformat()
    return {
        "artifact_id": artifact_id,
        "artifact_type": "PACKET_SHELL",
        "production_timestamp": ts,
        "case_id": case_id,
        "meek_track": meek_track,
        "outputs": {
            "exhibit_matrix": build_exhibit_matrix(atoms),
            "timeline": build_timeline(events),
        },
        "linked_atoms": [a.atom_id for a in atoms],
        "authority_refs": [],
        "manifest": {},
    }
