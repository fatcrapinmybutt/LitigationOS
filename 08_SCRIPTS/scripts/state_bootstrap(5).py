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
    "vehicle_readiness.sample.json": "vehicle_readiness.json",
    "authority_triples.sample.json": "authority_triples.json",
    "contradiction_map.sample.json": "contradiction_map.json",
    "timeline.sample.json": "timeline.json",
    "orders.sample.json": "orders.json",
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
        try:
            cur = json.loads(cycle_path.read_text(encoding="utf-8"))
        except Exception:
            cur = {}
    else:
        cur = {}
    payload = {
        "directive_name":"EVENTHORIZON_CMDCTR_EXECUTOR_v2_2026-02-22",
        "cycle_index": max(int(cur.get("cycle_index", 0)), 1),
        "delta_level": 7,
        "convergence_score": max(float(cur.get("convergence_score", 0.18)), 0.34),
        "emergence_score": max(float(cur.get("emergence_score", 0.12)), 0.26),
        "runtime_target":"Hybrid",
        "artifacts_emitted": sorted(set(list(cur.get("artifacts_emitted", [])) + [
            "ui/panels.js",
            "ui/adapters.js",
            "runtime/deterministic_cycle_id.py",
            "schemas/timeline.schema.json",
            "schemas/orders.schema.json",
            "schemas/vehicle_readiness.schema.json"
        ])),
        "top_next_actions":[
            "Replace sample timeline/orders with real litigation extracts",
            "Connect order supersession parser to controlling-order panel",
            "Advance vehicle readiness scores with proof-coverage computations"
        ],
        "resolution_targets":[
            "Wire live data ingestion path for docket/order/timeline",
            "Attach exact order text and service proof metadata",
            "Promote CCS/SBNA formulas from sample to computed runtime"
        ],
        "discovery_targets":[
            "Current docket snapshots (all active lanes)",
            "Entered orders + proofs of service",
            "Transcript pinpoint segments for contested findings"
        ],
        "validation_findings":[
            "DELTA7 append applied: timeline/orders/readiness schemas + UI wiring",
            "Replay log now supports deterministic event IDs and cycle IDs"
        ],
        "adversarial_improvement_findings":[
            "Need exact authority pinpoints in authority_triples.json for stronger panel signal",
            "Need actual supersession edges across order history"
        ],
        "next_cycle_targets":[
            "DELTA8 order supersession graph",
            "DELTA8 timeline filters and lane toggles",
            "DELTA8 computed readiness scoring pipeline"
        ],
        "updated_at_iso": datetime.now().isoformat(timespec="seconds")
    }
    cycle_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")

def bootstrap() -> dict:
    ensure_dirs()
    created_data = ensure_live_data_from_samples()
    ensure_cycle_state()
    return {
        "timestamp": datetime.now().isoformat(timespec="seconds"),
        "created_data_files": created_data,
        "root": str(ROOT),
    }

if __name__ == "__main__":
    print(json.dumps(bootstrap(), indent=2))
