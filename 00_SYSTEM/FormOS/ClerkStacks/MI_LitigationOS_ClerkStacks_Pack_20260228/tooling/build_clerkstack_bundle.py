#!/usr/bin/env python3
"""
build_clerkstack_bundle.py
Offline (no-network) builder for LitigationOS Michigan clerk stacks.

- Creates a folder structure for a given manifest.
- Writes a human-readable checklist stub.
- Runs basic validations (schema presence, doc ordering, filename rules).
- DOES NOT generate PDFs; it creates a place to put them.

Usage:
  python build_clerkstack_bundle.py --manifest manifests/examples/manifest_example_foc65.json --out ./OUT_FOC65

Exit codes:
  0 = success
  2 = validation error
  3 = runtime error
"""
from __future__ import annotations

import argparse
import json
import os
import re
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Tuple

SAFE_NAME_RE = re.compile(r"^[A-Za-z0-9._\- ]+$")

def eprint(*a: Any) -> None:
    print(*a, file=sys.stderr)

def load_json(path: Path) -> Dict[str, Any]:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception as ex:
        raise RuntimeError(f"Failed to read JSON: {path}: {ex}") from ex

def validate_manifest_shape(m: Dict[str, Any]) -> List[str]:
    errs: List[str] = []
    for key in ["schemaVersion", "jurisdiction", "package", "case", "documents"]:
        if key not in m:
            errs.append(f"Missing required top-level key: {key}")
    if "documents" in m and not isinstance(m["documents"], list):
        errs.append("documents must be a list")
    # basic doc order uniqueness
    orders = []
    for d in m.get("documents", []):
        if not isinstance(d, dict):
            errs.append("documents entries must be objects")
            continue
        if "filingOrder" not in d:
            errs.append("Each document must have filingOrder")
        else:
            orders.append(d["filingOrder"])
        fn = d.get("filename")
        if fn:
            if len(fn) > 100:
                errs.append(f"filename too long (>100 chars): {fn}")
            if not SAFE_NAME_RE.match(fn):
                errs.append(f"filename contains unsafe characters: {fn}")
    if len(set(orders)) != len(orders):
        errs.append("filingOrder values must be unique")
    return errs

def build_bundle(m: Dict[str, Any], out_dir: Path) -> None:
    out_dir.mkdir(parents=True, exist_ok=True)
    (out_dir / "LEAD").mkdir(exist_ok=True)
    (out_dir / "ATTACHMENTS").mkdir(exist_ok=True)
    (out_dir / "SERVICE").mkdir(exist_ok=True)
    (out_dir / "META").mkdir(exist_ok=True)

    # Write manifest copy
    (out_dir / "META" / "manifest.json").write_text(json.dumps(m, indent=2), encoding="utf-8")

    # Build checklist stub
    pkg = m.get("package", {})
    case = m.get("case", {})
    docs = sorted(m.get("documents", []), key=lambda x: x.get("filingOrder", 9999))
    lines: List[str] = []
    lines.append(f"PACKAGE: {pkg.get('packageId')} — {pkg.get('title')}")
    lines.append(f"GOAL: {pkg.get('goal')}")
    lines.append("")
    lines.append(f"CASE: {case.get('caption')} ({case.get('caseNumber')})")
    lines.append(f"COURT: {case.get('courtName')} — {case.get('county')}")
    lines.append("")
    lines.append("PRECONDITIONS:")
    for p in pkg.get("preconditions", []) or []:
        lines.append(f"  - [ ] {p}")
    lines.append("")
    lines.append("DOCUMENTS IN FILING ORDER:")
    for d in docs:
        fo = d.get("filingOrder")
        fn = d.get("filename") or ""
        dt = d.get("docType")
        title = d.get("title")
        checks = d.get("formatChecks", [])
        lines.append(f"  {fo}. {title} ({dt})")
        if fn:
            lines.append(f"     filename: {fn}")
        if checks:
            lines.append(f"     checks: {', '.join(checks)}")
    (out_dir / "CHECKLIST.md").write_text("\n".join(lines) + "\n", encoding="utf-8")

    # Create placeholder files
    for d in docs:
        fn = d.get("filename")
        if not fn:
            continue
        doc_type = (d.get("docType") or "").lower()
        if "service" in doc_type:
            target = out_dir / "SERVICE" / fn
        elif "attachment" in doc_type:
            target = out_dir / "ATTACHMENTS" / fn
        else:
            target = out_dir / "LEAD" / fn
        if not target.exists():
            target.write_text("PLACEHOLDER: Put the final, OCR'd PDF here.\n", encoding="utf-8")

def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--manifest", required=True, help="Path to clerk-stack manifest JSON")
    ap.add_argument("--out", required=True, help="Output folder to materialize bundle")
    args = ap.parse_args()

    try:
        mpath = Path(args.manifest).expanduser().resolve()
        out_dir = Path(args.out).expanduser().resolve()
        m = load_json(mpath)
        errs = validate_manifest_shape(m)
        if errs:
            eprint("MANIFEST VALIDATION FAILED:")
            for e in errs:
                eprint(" -", e)
            return 2
        build_bundle(m, out_dir)
        print(f"OK: built clerk stack at {out_dir}")
        return 0
    except Exception as ex:
        eprint(f"ERROR: {ex}")
        return 3

if __name__ == "__main__":
    raise SystemExit(main())
