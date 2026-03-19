#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
rules_lookup.py

Regex search in state/mi/rules_store/rules_authority_shards.jsonl.

Usage:
  python scripts/rules_lookup.py --root . --query "MCR 3.207" --max 25
"""
from __future__ import annotations
import argparse, re
from pathlib import Path

def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--root", required=True)
    ap.add_argument("--query", required=True)
    ap.add_argument("--max", type=int, default=25)
    args = ap.parse_args()

    root = Path(args.root).expanduser().resolve()
    shards = root/"state"/"mi"/"rules_store"/"rules_authority_shards.jsonl"
    if not shards.exists():
        print("Missing:", shards); return 2

    rx = re.compile(args.query, re.I)
    hits = 0
    with shards.open("r", encoding="utf-8", errors="replace") as f:
        for line in f:
            if rx.search(line):
                print(line.rstrip())
                hits += 1
                if hits >= args.max:
                    break
    print(f"\nHITS: {hits} (capped at {args.max})")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
