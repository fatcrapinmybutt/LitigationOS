#!/usr/bin/env python
from __future__ import annotations
import argparse, csv, os
from pathlib import Path

def validate(plan: Path) -> dict:
    issues = []
    dst_seen = set()
    rows = 0
    missing_src = 0
    dup_dst = 0
    same_src_dst = 0

    with open(plan, "r", encoding="utf-8") as f:
        rdr = csv.DictReader(f)
        for r in rdr:
            rows += 1
            src = Path(r.get("src",""))
            dst = Path(r.get("dst",""))
            if not src.exists():
                missing_src += 1
            if str(dst) in dst_seen:
                dup_dst += 1
            else:
                dst_seen.add(str(dst))
            if str(src) == str(dst):
                same_src_dst += 1

    if missing_src:
        issues.append(f"{missing_src} sources missing")
    if dup_dst:
        issues.append(f"{dup_dst} duplicate destinations")
    if same_src_dst:
        issues.append(f"{same_src_dst} src==dst rows")

    ok = (missing_src == 0 and dup_dst == 0 and same_src_dst == 0)

    return {
        "plan": str(plan),
        "rows": rows,
        "ok": ok,
        "missing_src": missing_src,
        "duplicate_dst": dup_dst,
        "same_src_dst": same_src_dst,
        "issues": issues,
    }

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--plan", required=True)
    args = ap.parse_args()
    plan = Path(args.plan)
    if not plan.exists():
        raise SystemExit(f"Plan not found: {plan}")
    res = validate(plan)
    print("PLAN:", res["plan"])
    print("ROWS:", res["rows"])
    print("OK:", res["ok"])
    if res["issues"]:
        print("ISSUES:")
        for i in res["issues"]:
            print(" -", i)
    raise SystemExit(0 if res["ok"] else 2)


def run(argv: list[str]) -> int:
    """Programmatic entrypoint for GUI and tests."""
    import sys as _sys
    old = _sys.argv
    _sys.argv = [old[0]] + list(argv)
    try:
        main()
        return 0
    except SystemExit as e:
        try:
            return int(e.code or 0)
        except Exception:
            return 1
    finally:
        _sys.argv = old


if __name__ == "__main__":
    main()
