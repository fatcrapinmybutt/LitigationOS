from __future__ import annotations
from pathlib import Path
import json
from datetime import datetime

ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = ROOT / "data"

def build_overlay() -> dict:
    inv = DATA_DIR / "desktop_corpus_inventory.json"
    lineage = DATA_DIR / "desktop_canonical_lineage_map.json"
    links = DATA_DIR / "replay_provenance_links.json"
    summary = {
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "inventory_present": inv.exists(),
        "lineage_present": lineage.exists(),
        "replay_links_present": links.exists(),
        "inventory_count": 0,
        "lineage_group_count": 0,
        "replay_link_count": 0
    }
    if inv.exists():
        try:
            payload = json.loads(inv.read_text(encoding="utf-8"))
            summary["inventory_count"] = len(payload) if isinstance(payload, list) else len(payload.get("items", []))
        except Exception:
            pass
    if lineage.exists():
        try:
            payload = json.loads(lineage.read_text(encoding="utf-8"))
            if isinstance(payload, list):
                summary["lineage_group_count"] = len(payload)
            elif isinstance(payload, dict):
                summary["lineage_group_count"] = len(payload.get("lineage_groups", payload.get("groups", [])))
        except Exception:
            pass
    if links.exists():
        try:
            payload = json.loads(links.read_text(encoding="utf-8"))
            if isinstance(payload, list):
                summary["replay_link_count"] = len(payload)
            elif isinstance(payload, dict):
                summary["replay_link_count"] = len(payload.get("links", []))
        except Exception:
            pass
    out = DATA_DIR / "cycle_provenance_summary.json"
    out.write_text(json.dumps(summary, indent=2), encoding="utf-8")
    return summary

if __name__ == "__main__":
    print(json.dumps(build_overlay(), indent=2))
