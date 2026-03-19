#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from __future__ import annotations
import argparse, csv, json
from pathlib import Path

def read_jsonl(p: Path, max_lines=None):
    n=0; bad=0; keys=set()
    with p.open("r", encoding="utf-8", errors="replace") as f:
        for line in f:
            line=line.strip()
            if not line:
                continue
            try:
                obj=json.loads(line)
                if isinstance(obj, dict):
                    keys |= set(obj.keys())
                n += 1
            except Exception:
                bad += 1
            if max_lines and n>=max_lines:
                break
    return n, bad, sorted(list(keys))

def csv_header(p: Path):
    with p.open("r", encoding="utf-8", errors="replace", newline="") as f:
        reader = csv.reader(f)
        return next(reader, [])

def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--root", required=True)
    args = ap.parse_args()
    root = Path(args.root).expanduser().resolve()
    store = root/"state"/"mi"/"authority_store"
    reports = root/"reports"
    reports.mkdir(parents=True, exist_ok=True)

    out = {"store": str(store), "checks": {}}

    ai = store/"authorities_index.jsonl"
    if ai.exists():
        n,bad,keys = read_jsonl(ai)
        out["checks"]["authorities_index.jsonl"] = {"records": n, "bad": bad, "keys": keys[:100]}
    else:
        out["checks"]["authorities_index.jsonl"] = {"missing": True}

    for name in ["nodes_authorities.csv","authorities_edges.csv","edges_authorities_xref.csv"]:
        p = store/name
        out["checks"][name] = {"present": p.exists(), "header": csv_header(p) if p.exists() else None}

    (reports/"authority_store_report.json").write_text(json.dumps(out, indent=2), encoding="utf-8")
    print("Wrote reports/authority_store_report.json")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
