from __future__ import annotations
from pathlib import Path
import json
from datetime import datetime

ROOT = Path(__file__).resolve().parents[1]
CYCLE_PATH = ROOT / "manifests" / "cycle_state.json"

def bump(delta_up: int = 1, convergence_inc: float = 0.07, emergence_inc: float = 0.08) -> dict:
    state = json.loads(CYCLE_PATH.read_text(encoding="utf-8"))
    state["cycle_index"] = int(state.get("cycle_index", 0)) + 1
    state["delta_level"] = int(state.get("delta_level", 0)) + delta_up
    state["convergence_score"] = round(min(1.0, float(state.get("convergence_score", 0.0)) + convergence_inc), 3)
    state["emergence_score"] = round(min(1.0, float(state.get("emergence_score", 0.0)) + emergence_inc), 3)
    state["updated_at_iso"] = datetime.now().isoformat(timespec="seconds")
    state.setdefault("top_next_actions", [])
    state["top_next_actions"] = [
        "Replace sample data with live extracts",
        "Expand order supersession graph rendering",
        "Advance readiness scoring from seeded values to computed values"
    ]
    CYCLE_PATH.write_text(json.dumps(state, indent=2), encoding="utf-8")
    return state

if __name__ == "__main__":
    print(json.dumps(bump(delta_up=0, convergence_inc=0.0, emergence_inc=0.0), indent=2))
