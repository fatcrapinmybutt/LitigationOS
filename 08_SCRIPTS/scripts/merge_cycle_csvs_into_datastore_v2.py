#!/usr/bin/env python3
"""Merge Cycle CSVs into Authority Graph Datastore

Inputs:
- Existing datastore folder containing:
  * neo4j/*.csv (nodes/edges)
  * fts/authority_shards_fts.sqlite
- New cycle CSVs:
  * authority_index.csv, pro_citations_index.csv, nodes_authorities.csv, authorities_edges.csv, edges_authorities_xref.csv, etc.

Behavior:
- Append new nodes/edges with deterministic IDs.
- De-duplicate by (id) where present, else by (sha256-ish fields).
- Optionally rebuild FTS if you provide a shards CSV.

This is a wiring tool; run locally where your full stores exist.

"""
from __future__ import annotations
import argparse, csv, hashlib
from pathlib import Path

def sha_row(row: dict) -> str:
    h=hashlib.sha256()
    for k in sorted(row.keys()):
        h.update(str(row.get(k,"")).encode("utf-8", errors="ignore"))
        h.update(b"\0")
    return h.hexdigest()

def load_csv(p: Path):
    rows=[]
    with p.open("r", encoding="utf-8", errors="replace", newline="") as f:
        r=csv.DictReader(f)
        for row in r:
            rows.append(row)
    return rows

def write_csv(p: Path, rows):
    p.parent.mkdir(parents=True, exist_ok=True)
    if not rows:
        return
    fields=sorted({k for r in rows for k in r.keys()})
    with p.open("w", encoding="utf-8", newline="") as f:
        w=csv.DictWriter(f, fieldnames=fields)
        w.writeheader(); w.writerows(rows)

def merge_rows(existing, incoming, id_field="id"):
    seen=set()
    out=[]
    for r in existing:
        key=r.get(id_field) or sha_row(r)
        if key in seen: 
            continue
        seen.add(key); out.append(r)
    for r in incoming:
        key=r.get(id_field) or sha_row(r)
        if key in seen:
            continue
        seen.add(key); out.append(r)
    return out

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--datastore", required=True, help="Existing datastore root (has neo4j/ and fts/).")
    ap.add_argument("--cycle_csv_dir", required=True, help="Folder containing new cycle CSVs to merge.")
    ap.add_argument("--out", required=True, help="Output merged datastore root.")
    args=ap.parse_args()

    ds=Path(args.datastore)
    cyc=Path(args.cycle_csv_dir)
    out=Path(args.out)
    (out/"neo4j").mkdir(parents=True, exist_ok=True)

    # example merges: authority nodes/edges if present
    pairs=[
        ("neo4j/nodes_authority_merged.csv", "nodes_authorities.csv", "authority_id"),
        ("neo4j/nodes_authority_shard_merged.csv", "authority_shards.csv", "shard_id"),
        ("neo4j/edges_authority_merged.csv", "authorities_edges.csv", "edge_id"),
        ("neo4j/edges_authorities_xref.csv", "edges_authorities_xref.csv", "edge_id"),
    ]

    for dst_rel, src_name, idf in pairs:
        dst_existing=ds/dst_rel
        src_new=cyc/src_name
        if not src_new.exists():
            continue
        existing=load_csv(dst_existing) if dst_existing.exists() else []
        incoming=load_csv(src_new)
        merged=merge_rows(existing, incoming, id_field=idf)
        write_csv(out/dst_rel, merged)

    print("Merge complete:", out)

if __name__=="__main__":
    main()
