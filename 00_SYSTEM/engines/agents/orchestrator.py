"""
Orchestrator: end-to-end deterministic run.

Pipeline:
1) EvidenceAgent => EvidenceAtoms
2) ChronologyAgent => ChronoEvents
3) FilingAgent => Packet Shell artifact
4) Emit manifest + run ledger

Outputs are append-only under out_dir/<timestamp>/...
"""

from __future__ import annotations
from pathlib import Path
from typing import Dict, Any
import datetime
import json
import os

from agents.agent_base import write_jsonl
from agents.evidence_agent import build_atoms
from agents.chronology_agent import build_events
from agents.filing_agent import build_packet

def run(case_id: str, root: Path, out_dir: Path) -> Path:
    ts = datetime.datetime.now(datetime.timezone.utc).astimezone().strftime("%Y%m%d_%H%M%S")
    run_dir = out_dir / ts
    run_dir.mkdir(parents=True, exist_ok=True)

    atoms = build_atoms(case_id=case_id, root=root)
    events = build_events(atoms)

    # Pick predominant track for packet shell (mode of atom tracks)
    track_counts = {}
    for a in atoms:
        track_counts[a.meek_track] = track_counts.get(a.meek_track, 0) + 1
    meek_track = max(track_counts, key=lambda k: track_counts[k]) if track_counts else "MEEK5"

    packet = build_packet(case_id=case_id, meek_track=meek_track, atoms=atoms, events=events)

    evidence_path = run_dir / "evidence_atoms.jsonl"
    chrono_path = run_dir / "chrono_events.jsonl"
    packet_path = run_dir / "packet_shell.json"

    write_jsonl(evidence_path, [a.__dict__ for a in atoms])
    write_jsonl(chrono_path, [e.__dict__ for e in events])
    packet_path.write_text(json.dumps(packet, indent=2, ensure_ascii=False), encoding="utf-8")

    manifest = {
        "run_timestamp": ts,
        "case_id": case_id,
        "root_scanned": str(root),
        "counts": {"atoms": len(atoms), "events": len(events)},
        "outputs": {
            "evidence_atoms_jsonl": str(evidence_path),
            "chrono_events_jsonl": str(chrono_path),
            "packet_shell_json": str(packet_path),
        }
    }
    (run_dir / "manifest.json").write_text(json.dumps(manifest, indent=2, ensure_ascii=False), encoding="utf-8")

    # minimal run ledger (append-only jsonl)
    ledger_path = run_dir / "run_ledger.jsonl"
    with ledger_path.open("w", encoding="utf-8") as f:
        f.write(json.dumps({"t":"start","case_id":case_id,"root":str(root)}, ensure_ascii=False) + "\n")
        f.write(json.dumps({"t":"atoms_built","count":len(atoms)}, ensure_ascii=False) + "\n")
        f.write(json.dumps({"t":"events_built","count":len(events)}, ensure_ascii=False) + "\n")
        f.write(json.dumps({"t":"packet_built","artifact_id":packet.get("artifact_id")}, ensure_ascii=False) + "\n")
        f.write(json.dumps({"t":"end","run_dir":str(run_dir)}, ensure_ascii=False) + "\n")

    return run_dir
