#!/usr/bin/env python3
"""
mifile_lint.py — basic, local-only MiFILE preflight checks for PDFs.

Checks implemented (best-effort):
- file size <= 25MB (warn if larger)
- PDF not encrypted/password protected
- page size is Letter (8.5x11) for all pages (warn otherwise)
- text-searchable heuristic: extracted text chars/page above threshold (warn if too low)
- orientation check: page rotation multiples of 90 (warn otherwise)

NOTE:
- This does NOT detect "text in margins" reliably (needs layout rendering).
- This does NOT strip metadata; it can only warn on presence of XMP streams in a coarse way.
"""

from __future__ import annotations
import argparse, json, sys
from pathlib import Path

try:
    from pypdf import PdfReader
except Exception as ex:
    print("ERROR: pypdf is required for this linter.", file=sys.stderr)
    raise

BYTES_25MB = 25 * 1024 * 1024
LETTER_W, LETTER_H = 612, 792  # points (8.5*72, 11*72)

def is_letter(w: float, h: float, tol: float=3.0) -> bool:
    # tolerate small differences / rounding
    return (abs(w - LETTER_W) <= tol and abs(h - LETTER_H) <= tol) or (abs(w - LETTER_H) <= tol and abs(h - LETTER_W) <= tol)

def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("pdf", help="Path to PDF")
    ap.add_argument("--min-chars-per-page", type=int, default=80)
    ap.add_argument("--out", default=None, help="Write JSON report to this path")
    args = ap.parse_args()

    pdf_path = Path(args.pdf)
    if not pdf_path.exists():
        raise SystemExit(f"Missing file: {pdf_path}")

    report = {
        "file": str(pdf_path),
        "size_bytes": pdf_path.stat().st_size,
        "checks": [],
        "ok": True,
    }

    if report["size_bytes"] > BYTES_25MB:
        report["checks"].append({"id":"FILE_SIZE", "severity":"ERROR", "ok": False, "detail":"File exceeds 25MB; split into parts."})
        report["ok"] = False
    else:
        report["checks"].append({"id":"FILE_SIZE", "severity":"OK", "ok": True, "detail":"<=25MB"})

    reader = PdfReader(str(pdf_path))
    if reader.is_encrypted:
        report["checks"].append({"id":"ENCRYPTION", "severity":"ERROR", "ok": False, "detail":"PDF is encrypted/password-protected."})
        report["ok"] = False
    else:
        report["checks"].append({"id":"ENCRYPTION", "severity":"OK", "ok": True, "detail":"Not encrypted"})

    page_warnings = 0
    text_warnings = 0
    rotation_warnings = 0
    text_counts = []

    for i, page in enumerate(reader.pages):
        mb = page.mediabox
        w = float(mb.width)
        h = float(mb.height)
        if not is_letter(w, h):
            page_warnings += 1
        rot = page.get("/Rotate", 0) or 0
        if int(rot) % 90 != 0:
            rotation_warnings += 1
        try:
            t = page.extract_text() or ""
        except Exception:
            t = ""
        cc = len(t.strip())
        text_counts.append(cc)
        if cc < args.min_chars_per_page:
            text_warnings += 1

    if page_warnings:
        report["checks"].append({"id":"PAGE_SIZE", "severity":"WARN", "ok": False, "detail":f"{page_warnings} pages not Letter size (8.5x11)."})
        # warn, not fail
    else:
        report["checks"].append({"id":"PAGE_SIZE", "severity":"OK", "ok": True, "detail":"All pages Letter size."})

    if rotation_warnings:
        report["checks"].append({"id":"ROTATION", "severity":"WARN", "ok": False, "detail":f"{rotation_warnings} pages have non-90-degree rotation values."})
    else:
        report["checks"].append({"id":"ROTATION", "severity":"OK", "ok": True, "detail":"Rotation OK."})

    total = len(text_counts) or 1
    low_ratio = text_warnings / total
    if low_ratio > 0.5:
        report["checks"].append({"id":"TEXT_SEARCHABLE", "severity":"WARN", "ok": False, "detail":f"Low text on {text_warnings}/{total} pages; likely needs OCR."})
    else:
        report["checks"].append({"id":"TEXT_SEARCHABLE", "severity":"OK", "ok": True, "detail":"Text density suggests searchable PDF."})

    report["stats"] = {
        "pages": len(text_counts),
        "min_chars": min(text_counts) if text_counts else 0,
        "median_chars": sorted(text_counts)[len(text_counts)//2] if text_counts else 0,
        "avg_chars": (sum(text_counts)/len(text_counts)) if text_counts else 0,
        "low_text_pages": text_warnings,
    }

    out = json.dumps(report, indent=2)
    if args.out:
        Path(args.out).parent.mkdir(parents=True, exist_ok=True)
        Path(args.out).write_text(out, encoding="utf-8")
    else:
        print(out)
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
