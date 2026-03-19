#!/usr/bin/env python3
"""
pdf_fieldmap_extract.py — extract AcroForm fields from a fillable PDF into a FieldMap JSON.

This is the bridge from “forms as PDFs” to “forms as structured templates.”
If the PDF has no AcroForm fields, you still get a report with empty fields.

Outputs:
- fields.json: [{name, type_guess, value_default, flags, rect, page, raw}...]
- summary.json: counts + sha256 + notes
"""

from __future__ import annotations
import argparse, json, hashlib, sys
from pathlib import Path

try:
    from pypdf import PdfReader
except Exception:
    print("ERROR: pypdf is required.", file=sys.stderr)
    raise

def sha256_file(p: Path) -> str:
    h = hashlib.sha256()
    with p.open("rb") as f:
        for ch in iter(lambda: f.read(1024*1024), b""):
            h.update(ch)
    return h.hexdigest()

def type_guess(field: dict) -> str:
    ft = field.get("/FT")
    if ft == "/Tx":
        return "text"
    if ft == "/Btn":
        # could be checkbox/radio/button
        return "button"
    if ft == "/Ch":
        return "choice"
    if ft == "/Sig":
        return "signature"
    return "unknown"

def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("pdf", help="Path to fillable PDF")
    ap.add_argument("--outdir", required=True, help="Output directory")
    args = ap.parse_args()

    pdf = Path(args.pdf)
    outdir = Path(args.outdir)
    outdir.mkdir(parents=True, exist_ok=True)

    reader = PdfReader(str(pdf))
    fields = []
    try:
        raw_fields = reader.get_fields() or {}
    except Exception:
        raw_fields = {}

    # pypdf returns a dict keyed by field name with values as dicts
    for name, f in raw_fields.items():
        try:
            fields.append({
                "name": name,
                "type_guess": type_guess(f),
                "value_default": f.get("/V"),
                "flags": f.get("/Ff"),
                "raw": {k: str(v) for k, v in f.items()} if hasattr(f, "items") else {}
            })
        except Exception:
            fields.append({"name": name, "type_guess": "unknown", "raw": {}})

    (outdir/"fields.json").write_text(json.dumps(fields, indent=2), encoding="utf-8")
    summary = {
        "pdf": str(pdf),
        "sha256": sha256_file(pdf),
        "field_count": len(fields),
        "notes": "If field_count==0, PDF may be image/flat or fields are not AcroForm."
    }
    (outdir/"summary.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")
    print(json.dumps(summary, indent=2))
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
