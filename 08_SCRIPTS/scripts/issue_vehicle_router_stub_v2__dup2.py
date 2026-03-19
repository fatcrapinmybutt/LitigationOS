#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
issue_vehicle_router_stub_v2.py — outputs Issue → Vehicle → Authority candidate sets (Michigan-first), using your shard index.

This is still a "stub" by design (no invented law). It selects candidate vehicles and pulls supporting authority shards
from your datastore (FTS + BM25 + neighbor expansion). You can progressively harden the vehicle map by providing a YAML/JSON map.

Inputs:
- FTS sqlite (authority_shards_fts.sqlite)
- Neighbors json (authority_neighbors_adj.json)
Optional:
- vehicle_map.json (operator-maintained) describing Issue keywords -> vehicle candidates, prerequisites, required exhibits

Outputs:
- issue_vehicle_candidates.json: issue -> vehicles -> authority shard hits
- issue_vehicle_candidates.md: human-readable compact map with pinpoints

USAGE:
  python issue_vehicle_router_stub_v2.py --issue "judge disqualification" --fts authority_shards_fts.sqlite --neighbors authority_neighbors_adj.json --out out.json --out-md out.md
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Dict, Any, List

from graphrag_query_v2 import fts_candidates, load_neighbors, expand_authorities, bm25_scores

try:
    from litigationos_common import ensure_dir, atomic_write_text
except Exception:
    def ensure_dir(p: Path) -> Path:
        p.mkdir(parents=True, exist_ok=True); return p
    def atomic_write_text(path: Path, text: str, encoding: str="utf-8") -> None:
        ensure_dir(path.parent); path.write_text(text, encoding=encoding)

DEFAULT_VEHICLE_HINTS = [
  # NOTE: These are NOT legal propositions. They are *labels* for your router output,
  # to be validated later against MCR/MCL/benchbook/forms.
  {"issue_keywords": ["judge disqualification","recusal","bias","2.003"], "vehicles": ["MCR_2_003_Disqualification", "Motion_Disqualify_Judge", "Appeal_Record_Preservation"]},
  {"issue_keywords": ["parenting time","suspension","endangerment","722.27a"], "vehicles": ["Parenting_Time_Restoration", "Emergency_Parenting_Time", "Modification_Or_Enforcement"]},
  {"issue_keywords": ["contempt","show cause","sanctions","jail"], "vehicles": ["Contempt_Defense", "Motion_To_Vacate", "Due_Process_Defect_Attack"]},
  {"issue_keywords": ["superintending control","original action","extraordinary"], "vehicles": ["MCR_3_302_Superintending_Control", "COA_Original_Action", "MSC_Original_Action_Posture_Check"]},
]

def pick_vehicle_candidates(issue: str, vehicle_map: List[Dict[str, Any]]) -> List[str]:
    issue_l = issue.lower()
    out = []
    for block in vehicle_map:
        if any(k.lower() in issue_l for k in block.get("issue_keywords", [])):
            out.extend(block.get("vehicles", []))
    # fallback if nothing matched: return generic labels
    return list(dict.fromkeys(out)) or ["Unmapped_Issue_Needs_Vehicle_Map"]

def rank_shards_for_vehicle(vehicle_label: str, issue: str, fts_rows: List[Dict[str, Any]], limit: int = 50) -> List[Dict[str, Any]]:
    # Score shards by BM25 over combined query: issue + vehicle_label
    q = f"{issue} {vehicle_label}".strip()
    docs = [r.get("text","") for r in fts_rows]
    scores = bm25_scores(docs, q)
    for r, s in zip(fts_rows, scores):
        r["_bm25_vehicle"] = float(s)
    rows = sorted(fts_rows, key=lambda r: r.get("_bm25_vehicle", 0.0), reverse=True)
    # Keep small payload
    out = []
    for r in rows[:limit]:
        out.append({
            "shard_id": r.get("shard_id"),
            "authority_id": r.get("authority_id"),
            "source": r.get("source"),
            "pinpoint": r.get("pinpoint"),
            "bm25": r.get("_bm25_vehicle"),
            "text": (r.get("text","") or "")[:900]
        })
    return out

def to_md(issue: str, out_obj: Dict[str, Any]) -> str:
    md = []
    md.append(f"# Issue → Vehicle → Authority Candidates\n\n**Issue:** {issue}\n")
    for v in out_obj.get("vehicles", []):
        md.append(f"\n## Vehicle label: {v.get('vehicle_label')}\n")
        md.append(f"- Seed authority_ids: {len(v.get('seed_authority_ids', []))}\n- Expanded authority_ids: {len(v.get('expanded_authority_ids', []))}\n")
        hits = v.get("shards", [])
        for i, h in enumerate(hits[:25], 1):
            md.append(f"### {i}. {h.get('authority_id')}\n- Source: {h.get('source')}\n- Pinpoint: {h.get('pinpoint')}\n- BM25: {h.get('bm25'):.4f}\n\n{h.get('text')}\n")
    return "\n".join(md)

def main() -> None:
    ap = argparse.ArgumentParser(description="Issue/Vehicle router stub — candidate sets only.")
    ap.add_argument("--issue", required=True, help="Issue description (free text).")
    ap.add_argument("--fts", required=True, help="FTS sqlite path (authority_shards_fts.sqlite).")
    ap.add_argument("--neighbors", help="Neighbors json path.")
    ap.add_argument("--vehicle-map", help="Optional JSON file overriding DEFAULT_VEHICLE_HINTS.")
    ap.add_argument("--fts-limit", type=int, default=300)
    ap.add_argument("--neighbor-depth", type=int, default=1)
    ap.add_argument("--neighbor-max", type=int, default=5000)
    ap.add_argument("--out", required=True, help="Output json path.")
    ap.add_argument("--out-md", help="Optional output md path.")
    args = ap.parse_args()

    vehicle_map = DEFAULT_VEHICLE_HINTS
    if args.vehicle_map:
        vehicle_map = json.loads(Path(args.vehicle_map).read_text(encoding="utf-8"))

    vehicles = pick_vehicle_candidates(args.issue, vehicle_map)

    fts_rows = fts_candidates(Path(args.fts), args.issue, limit=args.fts_limit)
    neighbors = load_neighbors(Path(args.neighbors) if args.neighbors else None)

    # authority seeds from fts rows
    seed = []
    for r in fts_rows:
        a = (r.get("authority_id") or "").strip()
        if a:
            seed.append(a)
    seed = list(dict.fromkeys(seed))

    expanded = expand_authorities(seed, neighbors, depth=args.neighbor_depth, max_nodes=args.neighbor_max) if neighbors else seed

    out_obj: Dict[str, Any] = {
        "issue": args.issue,
        "vehicles": []
    }

    for v in vehicles:
        shards = rank_shards_for_vehicle(v, args.issue, fts_rows, limit=60)
        out_obj["vehicles"].append({
            "vehicle_label": v,
            "seed_authority_ids": seed,
            "expanded_authority_ids": expanded,
            "shards": shards
        })

    out_path = Path(args.out)
    ensure_dir(out_path.parent)
    atomic_write_text(out_path, json.dumps(out_obj, ensure_ascii=False, indent=2))

    if args.out_md:
        md_path = Path(args.out_md)
        ensure_dir(md_path.parent)
        atomic_write_text(md_path, to_md(args.issue, out_obj))

    print(f"Wrote {out_path}")
    if args.out_md:
        print(f"Wrote {args.out_md}")

if __name__ == "__main__":
    main()
