#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
docket_tag_summary.py

Summarize tag frequencies in reports/docket_events_all_tagged.csv.

Usage:
  python scripts/docket_tag_summary.py --root .
"""
from __future__ import annotations
import argparse, csv, json
from pathlib import Path
from collections import Counter

def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--root", required=True)
    args = ap.parse_args()

    root = Path(args.root).expanduser().resolve()
    p = root/"reports"/"docket_events_all_tagged.csv"
    if not p.exists():
        print("Missing:", p); return 2

    c = Counter()
    rows = 0
    with p.open("r", encoding="utf-8", newline="") as f:
        r = csv.DictReader(f)
        for row in r:
            rows += 1
            for t in (row.get("tags") or "").split("|"):
                t = t.strip()
                if t: c[t] += 1

    out = {"rows": rows, "tag_counts": dict(c.most_common())}
    (root/"reports"/"docket_tag_counts.json").write_text(json.dumps(out, indent=2), encoding="utf-8")
    print("Wrote reports/docket_tag_counts.json")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
