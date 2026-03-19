from __future__ import annotations
import json
from pathlib import Path
from datetime import datetime, timezone

TRUTH_TAG = "PROVEN"

def load_json(p: Path):
    with p.open("r", encoding="utf-8") as f:
        return json.load(f)

def build_provenance_links(root: Path) -> list[dict]:
    artifacts_dir = root / "artifacts"
    manifests_dir = root / "manifests"

    inventory = load_json(artifacts_dir / "desktop_corpus_inventory.json")
    lineages = load_json(artifacts_dir / "desktop_canonical_lineage_map.json")
    cycle_state = load_json(manifests_dir / "cycle_state.json")

    cycle_id = cycle_state.get("cycle_id", "CYCLE-UNKNOWN")
    lineage_lookup = {l["canonical_name"]: l["lineage_id"] for l in lineages}

    links = []
    for item in inventory:
      tags = set(item.get("tags", []))
      if "prompt" in tags or "operator_catalog" in tags or "replay" in tags or "transition_table" in tags:
        links.append({
          "event_id": f"EV-{abs(hash(item['name'])) % 10_000_000:07d}",
          "cycle_id": cycle_id,
          "artifact_path": item["name"],
          "source_items": [item["name"]],
          "lineage_ids": [lineage_lookup[item["name"]]] if item["name"] in lineage_lookup else [],
          "truth_tag": TRUTH_TAG,
          "notes": "Auto-linked during Δ9 Desktop Lineage append cycle."
        })
    return links

def main():
    root = Path(__file__).resolve().parents[1]
    links = build_provenance_links(root)
    out = root / "artifacts" / "replay_provenance_links.json"
    with out.open("w", encoding="utf-8") as f:
      json.dump(links, f, indent=2)
    print(f"Wrote {out} ({len(links)} links)")

if __name__ == "__main__":
    main()
