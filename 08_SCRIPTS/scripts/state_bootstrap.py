from __future__ import annotations
from pathlib import Path
import json
from datetime import datetime

ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = ROOT / "data"
MANIFESTS_DIR = ROOT / "manifests"
LOGS_DIR = ROOT / "logs"

SAMPLE_TO_LIVE = {
    "case_state.sample.json": "case_state.json",
    "deadlines.sample.json": "deadlines.json",
    "vehicle_map.sample.json": "vehicle_map.json",
    "authority_triples.sample.json": "authority_triples.json",
    "contradiction_map.sample.json": "contradiction_map.json",
    "gui_state.sample.json": "gui_state.json",
}

def ensure_dirs() -> None:
    for p in [DATA_DIR, MANIFESTS_DIR, LOGS_DIR]:
        p.mkdir(parents=True, exist_ok=True)

def ensure_live_data_from_samples() -> list[str]:
    created = []
    for src_name, dst_name in SAMPLE_TO_LIVE.items():
        src = DATA_DIR / src_name
        dst = DATA_DIR / dst_name
        if src.exists() and not dst.exists():
            dst.write_text(src.read_text(encoding="utf-8"), encoding="utf-8")
            created.append(dst_name)
    return created

def ensure_cycle_state() -> None:
    cycle_path = MANIFESTS_DIR / "cycle_state.json"
    if cycle_path.exists():
        return
    payload = {
        "directive_name":"EVENTHORIZON_CMDCTR_EXECUTOR_v2_2026-02-22",
        "cycle_index":10,
        "delta_level":10,
        "convergence_score":0.93,
        "emergence_score":0.90,
        "runtime_target":"Hybrid",
        "artifacts_emitted":["ui/index.html","ui/panels.js","data/desktop_corpus_inventory.json","data/desktop_canonical_lineage_map.json"],
        "top_next_actions":["Wire real docket ingestion into orders panel","Add evidence coverage scoring from ExhibitMatrix","Promote lineage graph to interactive force view"],
        "resolution_targets":["Map order supersession from actual orders","Attach service proofs to order chain","Integrate transcript pinpoints into timeline"],
        "discovery_targets":["Latest docket exports","Order PDFs/text","Transcript pinpoints"],
        "validation_findings":["Main UI integration append complete"],
        "adversarial_improvement_findings":["Lineage graph is SVG summary view; can upgrade to interactive canvas"],
        "next_cycle_targets":["DELTA10+ evidence matrix panel","Order chain supersession graph","Ops replay overlay filters"]
    }
    cycle_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")

def bootstrap() -> dict:
    ensure_dirs()
    created_data = ensure_live_data_from_samples()
    ensure_cycle_state()
    overlay = None
    try:
        from provenance_overlay import build_overlay  # type: ignore
        overlay = build_overlay()
    except Exception as exc:
        overlay = {"error": str(exc)}
    return {
        "timestamp": datetime.now().isoformat(timespec="seconds"),
        "created_data_files": created_data,
        "root": str(ROOT),
        "provenance_overlay": overlay,
    }

if __name__ == "__main__":
    print(json.dumps(bootstrap(), indent=2))
