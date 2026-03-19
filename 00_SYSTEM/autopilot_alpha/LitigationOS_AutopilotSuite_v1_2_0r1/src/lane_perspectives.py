\
from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, List

def infer_lane(text: str, lane_rules: Dict[str, List[str]]) -> str:
    t = (text or "").lower()
    best = ("UNASSIGNED", 0)
    for lane, kws in lane_rules.items():
        hit = 0
        for kw in kws:
            if kw.lower() in t:
                hit += 1
        if hit > best[1]:
            best = (lane, hit)
    return best[0]

def build_lane_perspectives(nodes: List[Dict[str, Any]], lane_rules: Dict[str, List[str]]) -> Dict[str, Any]:
    lane_buckets: Dict[str, List[str]] = {}
    for n in nodes:
        uid = n.get("uid")
        props = n.get("props", {}) or {}
        blob = " ".join([str(props.get(k,"")) for k in ["lane","group","tags_raw","name","kind","tokens_raw","source"]])
        lane = str(props.get("lane") or "").strip() or infer_lane(blob, lane_rules)
        lane_buckets.setdefault(lane, []).append(uid)

    lanes = []
    for lane, uids in sorted(lane_buckets.items()):
        lanes.append({"lane": lane, "node_count": len(uids), "sample_uids": uids[:25]})
    return {"version":"1.2.0","kind":"BloomLanePerspectives","lanes":lanes}

def write_lane_perspectives_json(path: Path, payload: Dict[str, Any]) -> None:
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True), encoding="utf-8")

def write_lane_queries_cypher(path: Path, lane_rules: Dict[str, List[str]]) -> None:
    lines = ["// Bloom lane queries (starter pack)"]
    for lane, kws in sorted(lane_rules.items()):
        ors = " OR ".join([f'toLower(coalesce(n.props_json,"")) CONTAINS "{kw.lower()}"' for kw in kws[:12]]) or "false"
        lines.append(f"\n// {lane}\nMATCH (n) WHERE {ors} RETURN n LIMIT 1000;")
    lines.append("\n// UNASSIGNED\nMATCH (n) RETURN n LIMIT 1000;")
    path.write_text("\n".join(lines), encoding="utf-8")
