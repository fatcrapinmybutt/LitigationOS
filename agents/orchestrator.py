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
import logging
import os

from agents.agent_base import write_jsonl
from agents.evidence_agent import build_atoms
from agents.chronology_agent import build_events
from agents.filing_agent import build_packet

logger = logging.getLogger(__name__)


def run(case_id: str, root: Path, out_dir: Path) -> Path:
    ts = datetime.datetime.now(datetime.timezone.utc).astimezone().strftime("%Y%m%d_%H%M%S")
    run_dir = out_dir / ts
    run_dir.mkdir(parents=True, exist_ok=True)
    errors = []

    # Stage 1: Build evidence atoms
    try:
        atoms = build_atoms(case_id=case_id, root=root)
    except Exception as e:
        logger.error("EvidenceAgent failed: %s", e, exc_info=True)
        errors.append({"stage": "build_atoms", "error": str(e)})
        atoms = []

    # Stage 2: Build chronological events
    try:
        events = build_events(atoms)
    except Exception as e:
        logger.error("ChronologyAgent failed: %s", e, exc_info=True)
        errors.append({"stage": "build_events", "error": str(e)})
        events = []

    # Pick predominant track for packet shell (mode of atom tracks)
    track_counts: Dict[str, int] = {}
    for a in atoms:
        track_counts[a.meek_track] = track_counts.get(a.meek_track, 0) + 1
    meek_track = max(track_counts, key=lambda k: track_counts[k]) if track_counts else "MEEK5"

    # Stage 3: Build packet shell
    try:
        packet = build_packet(case_id=case_id, meek_track=meek_track, atoms=atoms, events=events)
    except Exception as e:
        logger.error("FilingAgent failed: %s", e, exc_info=True)
        errors.append({"stage": "build_packet", "error": str(e)})
        packet = {"artifact_id": None, "error": str(e)}

    # Stage 4: Write outputs
    try:
        evidence_path = run_dir / "evidence_atoms.jsonl"
        chrono_path = run_dir / "chrono_events.jsonl"
        packet_path = run_dir / "packet_shell.json"

        write_jsonl(evidence_path, [a.__dict__ for a in atoms])
        write_jsonl(chrono_path, [e.__dict__ for e in events])
        packet_path.write_text(json.dumps(packet, indent=2, ensure_ascii=False), encoding="utf-8")

        status = "SUCCESS" if not errors else "PARTIAL"
        manifest = {
            "run_timestamp": ts,
            "case_id": case_id,
            "root_scanned": str(root),
            "status": status,
            "counts": {"atoms": len(atoms), "events": len(events)},
            "errors": errors,
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
            f.write(json.dumps({"t": "start", "case_id": case_id, "root": str(root)}, ensure_ascii=False) + "\n")
            f.write(json.dumps({"t": "atoms_built", "count": len(atoms)}, ensure_ascii=False) + "\n")
            f.write(json.dumps({"t": "events_built", "count": len(events)}, ensure_ascii=False) + "\n")
            f.write(json.dumps({"t": "packet_built", "artifact_id": packet.get("artifact_id")}, ensure_ascii=False) + "\n")
            if errors:
                f.write(json.dumps({"t": "errors", "count": len(errors), "details": errors}, ensure_ascii=False) + "\n")
            f.write(json.dumps({"t": "end", "status": status, "run_dir": str(run_dir)}, ensure_ascii=False) + "\n")
    except Exception as e:
        logger.error("Output write failed: %s", e, exc_info=True)
        # Last resort: write error to run_dir if possible
        try:
            (run_dir / "CRASH.txt").write_text(f"Output write failed: {e}", encoding="utf-8")
        except Exception:
            pass

    if errors:
        logger.warning("Orchestrator completed with %d error(s) for case %s", len(errors), case_id)

    return run_dir
