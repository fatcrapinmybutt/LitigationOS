#!/usr/bin/env python3
"""
E-Filing PDF Validator — LitigationOS
=======================================
Validates PDF files against court-specific e-filing requirements.

Checks performed:
  - File size within court limits
  - PDF readable / not corrupt
  - Page size correct (letter 8.5×11)
  - Searchable text layer present
  - Bookmarks present (if required)
  - Metadata cleanliness
  - Page count sanity
  - Not encrypted
  - Image resolution (basic)

Usage:
  python efiling_validator.py --court 14th-circuit --file filing.pdf
  python efiling_validator.py --court coa --file brief.pdf --json
  python efiling_validator.py --court usdc-wdmi --dir filing_package/
  python efiling_validator.py --list-courts

Dependencies: PyMuPDF (fitz)
"""
import sys
import os
import argparse
import json
from pathlib import Path
from datetime import datetime

sys.stdout = open(sys.stdout.fileno(), mode='w', encoding='utf-8', errors='replace')

# ---------------------------------------------------------------------------
# Dependency check
# ---------------------------------------------------------------------------
try:
    import fitz  # PyMuPDF
    HAS_FITZ = True
except ImportError:
    HAS_FITZ = False

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------
LETTER_WIDTH = 612
LETTER_HEIGHT = 792

# ---------------------------------------------------------------------------
# Court profiles (self-contained — no cross-imports)
# ---------------------------------------------------------------------------
COURT_PROFILES = {
    "14th-circuit": {
        "name": "14th Circuit Court, Muskegon County",
        "system": "MiFILE/TrueFiling",
        "max_file_size_mb": 25,
        "page_size": (LETTER_WIDTH, LETTER_HEIGHT),
        "page_size_name": "letter",
        "requires_ocr": True,
        "requires_bookmarks": False,
        "margins": {"top": 1.0, "bottom": 1.0, "left": 1.0, "right": 1.0},
    },
    "coa": {
        "name": "Michigan Court of Appeals",
        "system": "MiFILE/TrueFiling",
        "max_file_size_mb": 25,
        "page_size": (LETTER_WIDTH, LETTER_HEIGHT),
        "page_size_name": "letter",
        "requires_ocr": True,
        "requires_bookmarks": True,
        "margins": {"top": 1.0, "bottom": 0.5, "left": 1.0, "right": 0.5},
    },
    "msc": {
        "name": "Michigan Supreme Court",
        "system": "MiFILE/TrueFiling",
        "max_file_size_mb": 25,
        "page_size": (LETTER_WIDTH, LETTER_HEIGHT),
        "page_size_name": "letter",
        "requires_ocr": True,
        "requires_bookmarks": True,
        "margins": {"top": 1.0, "bottom": 0.5, "left": 1.0, "right": 0.5},
    },
    "usdc-wdmi": {
        "name": "U.S. District Court, Western District of Michigan",
        "system": "CM/ECF",
        "max_file_size_mb": 35,
        "page_size": (LETTER_WIDTH, LETTER_HEIGHT),
        "page_size_name": "letter",
        "requires_ocr": True,
        "requires_bookmarks": True,
        "margins": {"top": 1.0, "bottom": 1.0, "left": 1.0, "right": 1.0},
    },
    "60th-district": {
        "name": "60th District Court, Muskegon County",
        "system": "MiFILE/TrueFiling",
        "max_file_size_mb": 25,
        "page_size": (LETTER_WIDTH, LETTER_HEIGHT),
        "page_size_name": "letter",
        "requires_ocr": True,
        "requires_bookmarks": False,
        "margins": {"top": 1.0, "bottom": 1.0, "left": 1.0, "right": 1.0},
    },
}

# ===================================================================
# Validation checks
# ===================================================================

def _file_size_mb(path) -> float:
    return os.path.getsize(path) / (1024 * 1024)


def _page_has_text(page) -> bool:
    return len(page.get_text("text").strip()) > 10


def validate_pdf(filepath: Path, profile: dict) -> tuple:
    """
    Run all validation checks on *filepath* using *profile*.
    Returns (overall_pass: bool, checks: list[dict]).
    Each check dict has keys: check, status (PASS/WARN/FAIL), detail.
    """
    checks = []
    passed = True

    if not filepath.exists():
        return False, [{"check": "File exists", "status": "FAIL",
                        "detail": f"Not found: {filepath}"}]

    # ---- 1. File size ----
    size = _file_size_mb(filepath)
    limit = profile.get("max_file_size_mb", 25)
    if size > limit:
        checks.append({"check": "File size", "status": "FAIL",
                        "detail": f"{size:.2f} MB exceeds {limit} MB limit"})
        passed = False
    elif size > limit * 0.9:
        checks.append({"check": "File size", "status": "WARN",
                        "detail": f"{size:.2f} MB — {size / limit * 100:.0f}% of {limit} MB limit"})
    else:
        checks.append({"check": "File size", "status": "PASS",
                        "detail": f"{size:.2f} MB (limit {limit} MB)"})

    # ---- 2. PDF readable ----
    try:
        doc = fitz.open(str(filepath))
    except Exception as exc:
        checks.append({"check": "PDF readable", "status": "FAIL",
                        "detail": str(exc)})
        return False, checks

    total_pages = len(doc)
    checks.append({"check": "PDF readable", "status": "PASS",
                    "detail": f"{total_pages} pages"})

    # ---- 3. Page size ----
    tw, th = profile.get("page_size", (LETTER_WIDTH, LETTER_HEIGHT))
    tolerance = 5  # points
    bad = []
    for i in range(total_pages):
        w, h = doc[i].rect.width, doc[i].rect.height
        if abs(w - tw) > tolerance or abs(h - th) > tolerance:
            bad.append({"page": i + 1, "width": round(w, 1),
                        "height": round(h, 1)})
    if bad:
        snippet = ", ".join(str(b["page"]) for b in bad[:10])
        if len(bad) > 10:
            snippet += f" (+{len(bad) - 10} more)"
        checks.append({"check": "Page size", "status": "FAIL",
                        "detail": f"{len(bad)} pages wrong size: {snippet}"})
        passed = False
    else:
        checks.append({"check": "Page size", "status": "PASS",
                        "detail": f"All {total_pages} pages letter (8.5×11)"})

    # ---- 4. Searchable text / OCR ----
    if profile.get("requires_ocr", True):
        with_text = sum(1 for i in range(total_pages)
                        if _page_has_text(doc[i]))
        pct = (with_text / total_pages * 100) if total_pages else 0
        image_only = total_pages - with_text
        if pct < 50:
            checks.append({"check": "Searchable text", "status": "FAIL",
                            "detail": (f"{with_text}/{total_pages} pages "
                                       f"({pct:.0f}%) — {image_only} need OCR")})
            passed = False
        elif pct < 90:
            checks.append({"check": "Searchable text", "status": "WARN",
                            "detail": (f"{with_text}/{total_pages} pages "
                                       f"({pct:.0f}%) — {image_only} may need OCR")})
        else:
            checks.append({"check": "Searchable text", "status": "PASS",
                            "detail": f"{with_text}/{total_pages} pages searchable"})

    # ---- 5. Bookmarks ----
    if profile.get("requires_bookmarks", False):
        toc = doc.get_toc()
        if not toc:
            checks.append({"check": "Bookmarks", "status": "FAIL",
                            "detail": "No bookmarks (required by court)"})
            passed = False
        else:
            checks.append({"check": "Bookmarks", "status": "PASS",
                            "detail": f"{len(toc)} bookmarks"})
    else:
        toc = doc.get_toc()
        if toc:
            checks.append({"check": "Bookmarks", "status": "PASS",
                            "detail": f"{len(toc)} bookmarks (optional)"})
        else:
            checks.append({"check": "Bookmarks", "status": "PASS",
                            "detail": "None (not required)"})

    # ---- 6. Metadata ----
    meta = doc.metadata or {}
    issues = []
    for key in ("author", "creator", "producer"):
        val = (meta.get(key) or "").lower()
        for sw in ("microsoft", "adobe", "word", "libreoffice",
                    "openoffice", "google"):
            if sw in val:
                issues.append(f"{key}=\"{meta[key]}\"")
                break
    if issues:
        checks.append({"check": "Metadata", "status": "WARN",
                        "detail": f"Software metadata: {'; '.join(issues)}"})
    else:
        checks.append({"check": "Metadata", "status": "PASS",
                        "detail": "Clean"})

    # ---- 7. Title metadata ----
    title = (meta.get("title") or "").strip()
    if not title:
        checks.append({"check": "Title metadata", "status": "WARN",
                        "detail": "No title set — some courts display this"})
    else:
        checks.append({"check": "Title metadata", "status": "PASS",
                        "detail": f"\"{title}\""})

    # ---- 8. Page count ----
    if total_pages == 0:
        checks.append({"check": "Page count", "status": "FAIL",
                        "detail": "PDF has 0 pages"})
        passed = False
    elif total_pages > 500:
        checks.append({"check": "Page count", "status": "WARN",
                        "detail": f"{total_pages} pages — consider splitting"})
    else:
        checks.append({"check": "Page count", "status": "PASS",
                        "detail": f"{total_pages} pages"})

    # ---- 9. Encryption ----
    if doc.is_encrypted:
        checks.append({"check": "Encryption", "status": "FAIL",
                        "detail": "Encrypted — courts require unencrypted PDFs"})
        passed = False
    else:
        checks.append({"check": "Encryption", "status": "PASS",
                        "detail": "Not encrypted"})

    # ---- 10. Blank pages ----
    blank = []
    for i in range(total_pages):
        text = doc[i].get_text("text").strip()
        images = doc[i].get_images(full=True)
        if not text and not images:
            blank.append(i + 1)
    if blank:
        snippet = ", ".join(str(p) for p in blank[:10])
        if len(blank) > 10:
            snippet += f" (+{len(blank) - 10} more)"
        checks.append({"check": "Blank pages", "status": "WARN",
                        "detail": f"{len(blank)} blank: {snippet}"})
    else:
        checks.append({"check": "Blank pages", "status": "PASS",
                        "detail": "No blank pages detected"})

    # ---- 11. Image resolution spot-check ----
    low_res = 0
    sampled = 0
    sample_pages = min(total_pages, 10)
    for i in range(sample_pages):
        for img_info in doc[i].get_images(full=True):
            sampled += 1
            xref = img_info[0]
            try:
                base = doc.extract_image(xref)
                if base:
                    w = base.get("width", 0)
                    h = base.get("height", 0)
                    # Very rough: if image covers most of the page but is
                    # low-resolution, flag it.
                    if w > 0 and h > 0 and w < 500 and h < 500:
                        low_res += 1
            except Exception:
                pass
    if sampled == 0:
        checks.append({"check": "Image quality", "status": "PASS",
                        "detail": "No images to check"})
    elif low_res > 0:
        checks.append({"check": "Image quality", "status": "WARN",
                        "detail": (f"{low_res}/{sampled} images < 500 px "
                                   "— may be blurry when printed")})
    else:
        checks.append({"check": "Image quality", "status": "PASS",
                        "detail": f"{sampled} images checked — OK"})

    doc.close()
    return passed, checks

# ===================================================================
# Report formatting
# ===================================================================

def print_report(filepath: Path, profile: dict, passed: bool,
                 checks: list):
    """Pretty-print validation results."""
    print(f"{'=' * 65}")
    print(f"  E-FILING VALIDATOR — {profile['name']}")
    print(f"  System: {profile.get('system', 'N/A')}")
    print(f"  File:   {filepath.name}")
    print(f"{'=' * 65}")

    for c in checks:
        sym = {"PASS": "✓", "WARN": "⚠", "FAIL": "✗"}[c["status"]]
        print(f"  {sym} [{c['status']:4s}] {c['check']}: {c['detail']}")

    print(f"{'=' * 65}")
    if passed:
        print(f"  RESULT: PASS — ready for {profile.get('system', 'upload')}")
    else:
        fails = [c for c in checks if c["status"] == "FAIL"]
        print(f"  RESULT: FAIL — {len(fails)} issue(s) must be fixed")
    print()


def save_json_report(filepath: Path, court_key: str, profile: dict,
                     passed: bool, checks: list) -> Path:
    """Write a JSON validation report next to the PDF."""
    report = {
        "file": str(filepath),
        "file_name": filepath.name,
        "court": court_key,
        "court_name": profile["name"],
        "system": profile.get("system", ""),
        "passed": passed,
        "checks": checks,
        "summary": {
            "total": len(checks),
            "pass": sum(1 for c in checks if c["status"] == "PASS"),
            "warn": sum(1 for c in checks if c["status"] == "WARN"),
            "fail": sum(1 for c in checks if c["status"] == "FAIL"),
        },
        "timestamp": datetime.now().isoformat(),
    }
    out = filepath.with_suffix(".validation.json")
    out.write_text(json.dumps(report, indent=2), encoding="utf-8")
    return out

# ===================================================================
# CLI
# ===================================================================

def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="efiling_validator",
        description=(
            "E-Filing PDF Validator — LitigationOS\n"
            "Validates PDF files against court-specific e-filing requirements."
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=(
            "Examples:\n"
            "  # Validate a single file for 14th Circuit\n"
            "  python efiling_validator.py --court 14th-circuit "
            "--file motion.pdf\n\n"
            "  # Validate with JSON report\n"
            "  python efiling_validator.py --court coa "
            "--file brief.pdf --json\n\n"
            "  # Validate all PDFs in a directory\n"
            "  python efiling_validator.py --court usdc-wdmi "
            "--dir filing_package/\n\n"
            "  # List available court profiles\n"
            "  python efiling_validator.py --list-courts\n"
        ),
    )
    parser.add_argument("--court",
                        help="Court profile key "
                             "(e.g. 14th-circuit, coa, msc, usdc-wdmi)")
    parser.add_argument("--file", help="Single PDF file to validate")
    parser.add_argument("--dir",
                        help="Directory of PDFs to validate (all *.pdf)")
    parser.add_argument("--json", action="store_true",
                        help="Save a JSON report alongside each PDF")
    parser.add_argument("--list-courts", action="store_true",
                        help="List available court profiles and exit")
    return parser


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()

    # ---- List courts ----
    if args.list_courts:
        print("Available Court Profiles")
        print("=" * 60)
        for key in sorted(COURT_PROFILES):
            p = COURT_PROFILES[key]
            print(f"\n  {key}")
            print(f"    Name:      {p['name']}")
            print(f"    System:    {p.get('system', 'N/A')}")
            print(f"    Max size:  {p.get('max_file_size_mb', 25)} MB")
            print(f"    OCR:       {'required' if p.get('requires_ocr') else 'not required'}")
            print(f"    Bookmarks: {'required' if p.get('requires_bookmarks') else 'not required'}")
            m = p.get("margins", {})
            if m:
                print(f"    Margins:   T={m.get('top', 1)}\" "
                      f"B={m.get('bottom', 1)}\" "
                      f"L={m.get('left', 1)}\" "
                      f"R={m.get('right', 1)}\"")
        return 0

    # ---- Validate args ----
    if not args.court:
        print("ERROR: --court is required (use --list-courts to see options)")
        return 1

    profile = COURT_PROFILES.get(args.court)
    if not profile:
        print(f"ERROR: Unknown court '{args.court}'")
        print(f"  Available: {', '.join(sorted(COURT_PROFILES))}")
        return 1

    if not args.file and not args.dir:
        print("ERROR: Provide --file or --dir")
        return 1

    # ---- Check dependency ----
    if not HAS_FITZ:
        print("ERROR: PyMuPDF (fitz) is required but not installed.")
        print("       Install with:  pip install PyMuPDF")
        return 1

    # ---- Collect PDFs ----
    pdfs = []
    if args.file:
        p = Path(args.file)
        if not p.exists():
            print(f"ERROR: File not found: {p}")
            return 1
        pdfs.append(p)
    if args.dir:
        d = Path(args.dir)
        if not d.is_dir():
            print(f"ERROR: Directory not found: {d}")
            return 1
        found = sorted(d.glob("*.pdf"))
        if not found:
            print(f"ERROR: No PDFs in {d}")
            return 1
        pdfs.extend(found)

    # ---- Run validation ----
    all_pass = True
    results_summary = []

    for pdf_path in pdfs:
        ok, checks = validate_pdf(pdf_path, profile)
        print_report(pdf_path, profile, ok, checks)

        if args.json:
            jp = save_json_report(pdf_path, args.court, profile, ok, checks)
            print(f"  JSON report: {jp}\n")

        results_summary.append({
            "file": pdf_path.name,
            "passed": ok,
            "fails": sum(1 for c in checks if c["status"] == "FAIL"),
            "warns": sum(1 for c in checks if c["status"] == "WARN"),
        })
        if not ok:
            all_pass = False

    # ---- Summary (when multiple files) ----
    if len(pdfs) > 1:
        print(f"{'=' * 65}")
        print(f"  BATCH SUMMARY — {len(pdfs)} files validated")
        print(f"{'=' * 65}")
        for r in results_summary:
            sym = "✓" if r["passed"] else "✗"
            print(f"  {sym} {r['file']}: "
                  f"{'PASS' if r['passed'] else 'FAIL'} "
                  f"({r['fails']} fails, {r['warns']} warns)")
        passing = sum(1 for r in results_summary if r["passed"])
        print(f"\n  {passing}/{len(pdfs)} files passed")

    return 0 if all_pass else 1


if __name__ == "__main__":
    sys.exit(main() or 0)
