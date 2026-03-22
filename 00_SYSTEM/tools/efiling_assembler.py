#!/usr/bin/env python3
"""
E-Filing PDF Assembler — LitigationOS
=======================================
Assembles court-compliant PDF packages for Michigan e-filing.
Supports: MiFILE (state courts), CM/ECF (federal), COA, MSC

Commands:
  assemble  — Combine documents into a court-compliant filing package
  validate  — Check a PDF against court requirements
  bates     — Add Bates number stamps to exhibit pages
  split     — Split large PDFs to meet court file-size limits
  courts    — List available court profiles

Examples:
  python efiling_assembler.py assemble --court 14th-circuit --type motion \\
      --lead motion.pdf --attachment affidavit.pdf \\
      --exhibits exhibit_a.pdf exhibit_b.pdf \\
      --output FILING_PACKAGE/ --bates-prefix PIGORS-A

  python efiling_assembler.py validate --court coa --file brief.pdf

  python efiling_assembler.py bates --input exhibits/ --prefix PIGORS-A \\
      --start 1 --output bates_exhibits/

  python efiling_assembler.py split --input large_filing.pdf --max-size 25 \\
      --output split_parts/

  python efiling_assembler.py courts

Dependencies: PyMuPDF (fitz), Pillow (optional), pytesseract (optional)
"""
import sys
import os
import io
import argparse
import json
import hashlib
import math
from pathlib import Path
from datetime import datetime

sys.stdout = open(sys.stdout.fileno(), mode='w', encoding='utf-8', errors='replace')

# ---------------------------------------------------------------------------
# Dependency imports with graceful fallback
# ---------------------------------------------------------------------------
try:
    import fitz  # PyMuPDF
    HAS_FITZ = True
except ImportError:
    HAS_FITZ = False

try:
    from PIL import Image
    HAS_PIL = True
except ImportError:
    HAS_PIL = False

try:
    import pytesseract
    HAS_TESSERACT = True
    # Standard Tesseract install path on Windows
    _tess = r"C:\Program Files\Tesseract-OCR\tesseract.exe"
    if os.path.isfile(_tess):
        pytesseract.pytesseract.tesseract_cmd = _tess
except ImportError:
    HAS_TESSERACT = False

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------
LETTER_WIDTH = 612      # 8.5 inches in PDF points
LETTER_HEIGHT = 792     # 11 inches in PDF points
PT_PER_INCH = 72

# ---------------------------------------------------------------------------
# Court Profiles
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
        "font": "Times New Roman or similar serif",
        "font_size": 12,
        "line_spacing": "double",
        "margins": {"top": 1.0, "bottom": 1.0, "left": 1.0, "right": 1.0},
        "notes": "Standard MiFILE filing. Exhibits as separate PDF or combined.",
    },
    "coa": {
        "name": "Michigan Court of Appeals",
        "system": "MiFILE/TrueFiling",
        "max_file_size_mb": 25,
        "page_size": (LETTER_WIDTH, LETTER_HEIGHT),
        "page_size_name": "letter",
        "requires_ocr": True,
        "requires_bookmarks": True,
        "font": "Times New Roman, 12pt min",
        "font_size": 12,
        "line_spacing": "double",
        "margins": {"top": 1.0, "bottom": 0.5, "left": 1.0, "right": 0.5},
        "notes": "MCR 7.212 format. Bookmarks required for briefs. Appendix separate.",
    },
    "msc": {
        "name": "Michigan Supreme Court",
        "system": "MiFILE/TrueFiling",
        "max_file_size_mb": 25,
        "page_size": (LETTER_WIDTH, LETTER_HEIGHT),
        "page_size_name": "letter",
        "requires_ocr": True,
        "requires_bookmarks": True,
        "font": "Times New Roman, 12pt min",
        "font_size": 12,
        "line_spacing": "double",
        "margins": {"top": 1.0, "bottom": 0.5, "left": 1.0, "right": 0.5},
        "notes": "MCR 7.312 format. Similar to COA with additional requirements.",
    },
    "usdc-wdmi": {
        "name": "U.S. District Court, Western District of Michigan",
        "system": "CM/ECF",
        "max_file_size_mb": 35,
        "page_size": (LETTER_WIDTH, LETTER_HEIGHT),
        "page_size_name": "letter",
        "requires_ocr": True,
        "requires_bookmarks": True,
        "font": "Times New Roman or similar, 12pt",
        "font_size": 12,
        "line_spacing": "double",
        "margins": {"top": 1.0, "bottom": 1.0, "left": 1.0, "right": 1.0},
        "notes": "CM/ECF filing. PDF/A preferred. Exhibits as attachments.",
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
        "notes": "Standard MiFILE filing.",
    },
}

DEFAULT_PROFILE = {
    "name": "Unknown Court",
    "system": "MiFILE/TrueFiling",
    "max_file_size_mb": 25,
    "page_size": (LETTER_WIDTH, LETTER_HEIGHT),
    "page_size_name": "letter",
    "requires_ocr": True,
    "requires_bookmarks": False,
    "margins": {"top": 1.0, "bottom": 1.0, "left": 1.0, "right": 1.0},
}

# ===================================================================
# Utility helpers
# ===================================================================

def _require_fitz():
    if not HAS_FITZ:
        print("ERROR: PyMuPDF (fitz) is required but not installed.")
        print("       Install with:  pip install PyMuPDF")
        sys.exit(1)


def get_profile(court_key: str) -> dict:
    """Return the court profile for *court_key*, falling back to defaults."""
    profile = COURT_PROFILES.get(court_key)
    if profile is None:
        print(f"WARNING: Unknown court '{court_key}'. Using default profile.")
        print(f"  Available: {', '.join(sorted(COURT_PROFILES))}")
        profile = {**DEFAULT_PROFILE, "name": court_key}
    return profile


def _exhibit_label(index: int) -> str:
    """0→A, 1→B, … 25→Z, 26→AA, 27→AB, …"""
    if index < 26:
        return chr(ord("A") + index)
    return chr(ord("A") + index // 26 - 1) + chr(ord("A") + index % 26)


def _file_size_mb(path) -> float:
    return os.path.getsize(path) / (1024 * 1024)


def _sha256(path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()

# ===================================================================
# PDF primitives (all require PyMuPDF)
# ===================================================================

def create_separator_page(label: str, subtitle: str = None,
                          case_info: str = None) -> "fitz.Document":
    """Return a single-page fitz.Document with a centred exhibit label."""
    doc = fitz.open()
    page = doc.new_page(width=LETTER_WIDTH, height=LETTER_HEIGHT)

    # Outer border at 1-inch margins
    border = fitz.Rect(72, 72, LETTER_WIDTH - 72, LETTER_HEIGHT - 72)
    page.draw_rect(border, color=(0, 0, 0), width=1.5)

    # Large centred label
    label_rect = fitz.Rect(72, 280, LETTER_WIDTH - 72, 380)
    page.insert_textbox(label_rect, label, fontsize=48,
                        fontname="helv", color=(0, 0, 0),
                        align=fitz.TEXT_ALIGN_CENTER)

    if subtitle:
        sub_rect = fitz.Rect(72, 395, LETTER_WIDTH - 72, 445)
        page.insert_textbox(sub_rect, subtitle, fontsize=14,
                            fontname="helv", color=(0.3, 0.3, 0.3),
                            align=fitz.TEXT_ALIGN_CENTER)

    if case_info:
        info_rect = fitz.Rect(72, LETTER_HEIGHT - 130,
                              LETTER_WIDTH - 72, LETTER_HEIGHT - 90)
        page.insert_textbox(info_rect, case_info, fontsize=10,
                            fontname="helv", color=(0.4, 0.4, 0.4),
                            align=fitz.TEXT_ALIGN_CENTER)
    return doc


def add_bates_to_page(page, stamp_text: str,
                      position: str = "bottom-right",
                      font_size: int = 9):
    """Overlay a Bates number stamp on a single page."""
    rect = page.rect
    margin = 36  # 0.5 inch

    if position == "bottom-right":
        box = fitz.Rect(rect.width - 200 - margin, rect.height - margin - 14,
                        rect.width - margin, rect.height - margin)
        align = fitz.TEXT_ALIGN_RIGHT
    elif position == "bottom-center":
        box = fitz.Rect(rect.width / 2 - 100, rect.height - margin - 14,
                        rect.width / 2 + 100, rect.height - margin)
        align = fitz.TEXT_ALIGN_CENTER
    else:  # bottom-left
        box = fitz.Rect(margin, rect.height - margin - 14,
                        margin + 200, rect.height - margin)
        align = fitz.TEXT_ALIGN_LEFT

    page.insert_textbox(box, stamp_text, fontsize=font_size,
                        fontname="cour", color=(0, 0, 0), align=align)


def page_has_text(page) -> bool:
    """True when the page carries a meaningful text layer."""
    return len(page.get_text("text").strip()) > 10


def check_text_layer(doc) -> tuple:
    """Return (pages_with_text, total_pages)."""
    total = len(doc)
    with_text = sum(1 for i in range(total) if page_has_text(doc[i]))
    return with_text, total


def ocr_page(page, lang: str = "eng") -> bool:
    """
    Add a searchable-text layer to an image-only page via Tesseract.
    Returns True on success, False if OCR is unavailable or fails.
    """
    if not (HAS_TESSERACT and HAS_PIL):
        return False
    try:
        pix = page.get_pixmap(dpi=300)
        img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)

        # pytesseract produces a full searchable PDF from the image
        pdf_bytes = pytesseract.image_to_pdf_or_hocr(img, lang=lang,
                                                      extension="pdf")
        ocr_doc = fitz.open("pdf", pdf_bytes)
        ocr_page_obj = ocr_doc[0]

        # Extract text blocks from OCR result and write them invisibly
        scale_x = page.rect.width / ocr_page_obj.rect.width
        scale_y = page.rect.height / ocr_page_obj.rect.height
        blocks = ocr_page_obj.get_text("dict", flags=fitz.TEXT_PRESERVE_WHITESPACE)["blocks"]
        for blk in blocks:
            for line in blk.get("lines", []):
                for span in line.get("spans", []):
                    txt = span["text"].strip()
                    if not txt:
                        continue
                    ox, oy = span["origin"]
                    pt = fitz.Point(ox * scale_x, oy * scale_y)
                    page.insert_text(pt, txt,
                                     fontsize=max(span["size"] * scale_y, 4),
                                     fontname="helv",
                                     color=(1, 1, 1))  # white = invisible
        ocr_doc.close()
        return True
    except Exception as exc:
        print(f"  WARNING: OCR failed: {exc}")
        return False


def clean_metadata(doc, title: str = None,
                   author: str = "Andrew James Pigors"):
    """Replace document metadata with filing-appropriate values."""
    doc.set_metadata({
        "title": title or "",
        "author": author,
        "subject": "",
        "keywords": "",
        "creator": "LitigationOS E-Filing Assembler",
        "producer": "",
        "creationDate": "",
        "modDate": "",
    })

# ===================================================================
# Validation logic (shared by assemble + validate commands)
# ===================================================================

def validate_pdf(filepath, profile: dict) -> tuple:
    """
    Validate *filepath* against a court *profile*.
    Returns (overall_pass: bool, results: list[dict]).
    """
    results = []
    passed = True
    fp = Path(filepath)

    if not fp.exists():
        return False, [{"check": "File exists", "status": "FAIL",
                        "detail": f"Not found: {fp}"}]

    # 1 — File size
    size = _file_size_mb(fp)
    limit = profile.get("max_file_size_mb", 25)
    if size > limit:
        results.append({"check": "File size", "status": "FAIL",
                        "detail": f"{size:.1f} MB exceeds {limit} MB limit"})
        passed = False
    elif size > limit * 0.9:
        results.append({"check": "File size", "status": "WARN",
                        "detail": f"{size:.1f} MB ({size / limit * 100:.0f}% of {limit} MB)"})
    else:
        results.append({"check": "File size", "status": "PASS",
                        "detail": f"{size:.1f} MB (limit {limit} MB)"})

    # 2 — Readable
    try:
        doc = fitz.open(str(fp))
    except Exception as exc:
        return False, results + [{"check": "PDF readable", "status": "FAIL",
                                  "detail": str(exc)}]
    results.append({"check": "PDF readable", "status": "PASS",
                    "detail": f"{len(doc)} pages"})

    # 3 — Page size
    target_w, target_h = profile.get("page_size", (LETTER_WIDTH, LETTER_HEIGHT))
    bad_pages = []
    for i in range(len(doc)):
        w, h = doc[i].rect.width, doc[i].rect.height
        if abs(w - target_w) > 5 or abs(h - target_h) > 5:
            bad_pages.append(i + 1)
    if bad_pages:
        snippet = str(bad_pages[:10])
        if len(bad_pages) > 10:
            snippet += f" … (+{len(bad_pages) - 10} more)"
        results.append({"check": "Page size", "status": "FAIL",
                        "detail": f"Wrong size on pages: {snippet}"})
        passed = False
    else:
        results.append({"check": "Page size", "status": "PASS",
                        "detail": f"All {len(doc)} pages are letter (8.5×11)"})

    # 4 — Text layer / OCR
    if profile.get("requires_ocr", True):
        wt, tot = check_text_layer(doc)
        pct = (wt / tot * 100) if tot else 0
        if pct < 50:
            results.append({"check": "Searchable text", "status": "FAIL",
                            "detail": f"{wt}/{tot} pages ({pct:.0f}%) have text"})
            passed = False
        elif pct < 90:
            results.append({"check": "Searchable text", "status": "WARN",
                            "detail": f"{wt}/{tot} pages ({pct:.0f}%) have text"})
        else:
            results.append({"check": "Searchable text", "status": "PASS",
                            "detail": f"{wt}/{tot} pages have searchable text"})

    # 5 — Bookmarks
    if profile.get("requires_bookmarks", False):
        toc = doc.get_toc()
        if not toc:
            results.append({"check": "Bookmarks", "status": "FAIL",
                            "detail": "No bookmarks (required by court)"})
            passed = False
        else:
            results.append({"check": "Bookmarks", "status": "PASS",
                            "detail": f"{len(toc)} bookmark entries"})

    # 6 — Metadata cleanliness
    meta = doc.metadata or {}
    suspect = []
    for key in ("author", "creator", "producer"):
        val = (meta.get(key) or "").lower()
        for sw in ("microsoft", "adobe", "word", "libreoffice", "openoffice"):
            if sw in val:
                suspect.append(f"{key}={meta[key]}")
                break
    if suspect:
        results.append({"check": "Metadata", "status": "WARN",
                        "detail": f"Software metadata: {', '.join(suspect)}"})
    else:
        results.append({"check": "Metadata", "status": "PASS",
                        "detail": "No problematic metadata"})

    # 7 — Page count sanity
    n = len(doc)
    if n > 500:
        results.append({"check": "Page count", "status": "WARN",
                        "detail": f"{n} pages — consider splitting"})
    else:
        results.append({"check": "Page count", "status": "PASS",
                        "detail": f"{n} pages"})

    # 8 — Encryption
    if doc.is_encrypted:
        results.append({"check": "Encryption", "status": "FAIL",
                        "detail": "PDF is encrypted — courts require unencrypted"})
        passed = False
    else:
        results.append({"check": "Encryption", "status": "PASS",
                        "detail": "Not encrypted"})

    doc.close()
    return passed, results

# ===================================================================
# Command: assemble
# ===================================================================

def cmd_assemble(args) -> int:
    """Assemble documents into a court-compliant filing package."""
    _require_fitz()

    profile = get_profile(args.court)
    out_dir = Path(args.output)
    dry = getattr(args, "dry_run", False)

    print(f"{'[DRY RUN] ' if dry else ''}E-Filing Assembly")
    print(f"  Court:    {profile['name']}")
    print(f"  System:   {profile.get('system', 'N/A')}")
    print(f"  Type:     {args.type}")
    print(f"  Max size: {profile.get('max_file_size_mb', 25)} MB")
    print()

    # --- Gather & verify inputs -----------------------------------------
    inputs = []  # list of (role, Path, bookmark_title)

    if args.lead:
        p = Path(args.lead)
        if not p.exists():
            print(f"ERROR: Lead document not found: {p}"); return 1
        inputs.append(("lead", p, f"{args.type.title()} — Lead Document"))
        print(f"  Lead:       {p.name} ({_file_size_mb(p):.1f} MB)")

    for att in (args.attachment or []):
        p = Path(att)
        if not p.exists():
            print(f"ERROR: Attachment not found: {p}"); return 1
        title = p.stem.replace("_", " ").replace("-", " ").title()
        inputs.append(("attachment", p, title))
        print(f"  Attachment: {p.name} ({_file_size_mb(p):.1f} MB)")

    exhibit_files = []
    for i, ex in enumerate(args.exhibits or []):
        p = Path(ex)
        if not p.exists():
            print(f"ERROR: Exhibit not found: {p}"); return 1
        label = _exhibit_label(i)
        exhibit_files.append((label, p))
        print(f"  Exhibit {label}: {p.name} ({_file_size_mb(p):.1f} MB)")

    if args.proposed_order:
        p = Path(args.proposed_order)
        if not p.exists():
            print(f"ERROR: Proposed order not found: {p}"); return 1
        inputs.append(("proposed_order", p, "Proposed Order"))
        print(f"  Proposed Order: {p.name}")

    if args.cert_of_service:
        p = Path(args.cert_of_service)
        if not p.exists():
            print(f"ERROR: Certificate of service not found: {p}"); return 1
        inputs.append(("cert_of_service", p, "Certificate of Service"))
        print(f"  Cert of Service: {p.name}")

    if not inputs and not exhibit_files:
        print("ERROR: No input files specified."); return 1

    if dry:
        print(f"\n[DRY RUN] Would create package in: {out_dir}")
        print(f"  Components: {len(inputs)}, Exhibits: {len(exhibit_files)}")
        if profile.get("requires_bookmarks"):
            print("  Bookmarks: would be added")
        if profile.get("requires_ocr") and not getattr(args, "no_ocr", False):
            print("  OCR: would check/add text layer")
        return 0

    out_dir.mkdir(parents=True, exist_ok=True)

    # --- Build combined PDF ---------------------------------------------
    combined = fitz.open()
    toc = []       # [level, title, page_num]  (1-based page)
    cur = 0        # running page count

    # Lead + attachments
    for role, path, bm_title in inputs:
        if role == "lead":
            toc.append([1, bm_title, cur + 1])
        elif role == "attachment":
            toc.append([1, bm_title, cur + 1])
        src = fitz.open(str(path))
        combined.insert_pdf(src)
        cur += len(src)
        src.close()
        print(f"  + {bm_title} ({cur} pp total)")

    # Exhibits
    bates_prefix = getattr(args, "bates_prefix", None) or ""
    bates_num = getattr(args, "bates_start", 1) or 1
    exhibit_index = []

    if exhibit_files:
        toc.append([1, "Exhibits", cur + 1])

        for label, ex_path in exhibit_files:
            # Separator page
            if not getattr(args, "no_separators", False):
                sep = create_separator_page(
                    f"EXHIBIT {label}",
                    subtitle=ex_path.stem.replace("_", " ").title(),
                    case_info=getattr(args, "case_number", "") or "",
                )
                combined.insert_pdf(sep)
                cur += 1
                sep.close()

            toc.append([2, f"Exhibit {label}: {ex_path.stem}", cur + 1])

            src = fitz.open(str(ex_path))
            start_page = cur
            combined.insert_pdf(src)

            # Bates stamps
            if bates_prefix:
                for j in range(len(src)):
                    stamp = f"{bates_prefix}-{bates_num:04d}"
                    add_bates_to_page(combined[start_page + j], stamp)
                    bates_num += 1

            exhibit_index.append({
                "label": label,
                "description": ex_path.stem.replace("_", " ").title(),
                "pages": f"{start_page + 1}-{start_page + len(src)}",
                "bates": (f"{bates_prefix}-{bates_num - len(src):04d} to "
                          f"{bates_prefix}-{bates_num - 1:04d}")
                         if bates_prefix else "N/A",
                "source": ex_path.name,
            })

            cur += len(src)
            src.close()
            print(f"  + Exhibit {label}: {ex_path.name}")

    # Proposed order + cert of service (already added via inputs loop)
    # Re-add trailing bookmarks that were already inserted
    for role, path, bm_title in inputs:
        if role in ("proposed_order", "cert_of_service"):
            pass  # already inserted above in the inputs loop

    # Set bookmarks
    if toc:
        combined.set_toc(toc)
        print(f"  + {len(toc)} bookmarks")

    # OCR check
    if profile.get("requires_ocr") and not getattr(args, "no_ocr", False):
        wt, tot = check_text_layer(combined)
        if wt < tot:
            missing = tot - wt
            if HAS_TESSERACT and HAS_PIL:
                print(f"  OCR: {missing} image-only pages — applying Tesseract …")
                done = 0
                for i in range(tot):
                    if not page_has_text(combined[i]):
                        if ocr_page(combined[i]):
                            done += 1
                print(f"  + OCR applied to {done}/{missing} pages")
            else:
                print(f"  WARNING: {missing} pages lack text layer "
                      "(install pytesseract + Pillow for OCR)")
        else:
            print(f"  + All {tot} pages have searchable text")

    # Metadata
    title = f"{args.type.title()} — {profile['name']}"
    clean_metadata(combined, title=title)
    print("  + Metadata cleaned")

    # Save
    fname = args.type.lower().replace(" ", "_") + "_combined.pdf"
    out_path = out_dir / fname
    combined.save(str(out_path), deflate=True, deflate_images=True,
                  deflate_fonts=True, garbage=4, clean=True)

    final_mb = _file_size_mb(out_path)
    max_mb = profile.get("max_file_size_mb", 25)
    print(f"\n  Saved: {out_path}")
    print(f"  Size:  {final_mb:.1f} MB / {max_mb} MB limit")
    print(f"  Pages: {len(combined)}")

    if final_mb > max_mb:
        print(f"  WARNING: exceeds {max_mb} MB — run the split command")

    # SHA-256 receipt
    receipt = {
        "file": str(out_path),
        "sha256": _sha256(out_path),
        "size_mb": round(final_mb, 2),
        "pages": len(combined),
        "court": profile["name"],
        "system": profile.get("system", ""),
        "generated": datetime.now().isoformat(),
        "components": [str(c[1]) for c in inputs],
        "exhibits": exhibit_index,
        "bookmarks": len(toc),
    }
    rp = out_dir / (args.type.lower().replace(" ", "_") + "_receipt.json")
    rp.write_text(json.dumps(receipt, indent=2), encoding="utf-8")
    print(f"  Receipt: {rp}")

    # Exhibit index file
    if exhibit_index:
        lines = [
            "EXHIBIT INDEX",
            "=" * 70,
            f"Filing: {args.type.title()}",
            f"Court:  {profile['name']}",
            f"Date:   {datetime.now().strftime('%Y-%m-%d %H:%M')}",
            "",
            f"{'Label':<10}{'Description':<35}{'Pages':<15}{'Bates Range'}",
            "-" * 70,
        ]
        for e in exhibit_index:
            lines.append(f"Ex. {e['label']:<6}{e['description']:<35}"
                         f"pp. {e['pages']:<11}{e['bates']}")
        lines.append(f"\nTotal exhibits: {len(exhibit_index)}")
        idx_path = out_dir / "exhibit_index.txt"
        idx_path.write_text("\n".join(lines), encoding="utf-8")
        print(f"  Exhibit Index: {idx_path}")

    combined.close()

    # Post-assembly validation
    print(f"\n  Validating against {args.court} requirements …")
    ok, checks = validate_pdf(out_path, profile)
    for c in checks:
        sym = {"PASS": "✓", "WARN": "⚠", "FAIL": "✗"}[c["status"]]
        print(f"    {sym} {c['check']}: {c['detail']}")

    if ok:
        print(f"\n  PASS — ready for {profile.get('system', 'upload')}")
    else:
        print("\n  FAIL — fix the issues above before filing")
    return 0 if ok else 1

# ===================================================================
# Command: validate
# ===================================================================

def cmd_validate(args) -> int:
    _require_fitz()
    profile = get_profile(args.court)
    fp = Path(args.file)

    if not fp.exists():
        print(f"ERROR: File not found: {fp}"); return 1

    print(f"Validating: {fp.name}")
    print(f"Court:      {profile['name']} ({profile.get('system', '')})")
    print("=" * 60)

    ok, checks = validate_pdf(fp, profile)
    for c in checks:
        sym = {"PASS": "✓", "WARN": "⚠", "FAIL": "✗"}[c["status"]]
        print(f"  {sym} [{c['status']}] {c['check']}: {c['detail']}")

    print("=" * 60)
    if ok:
        print(f"PASS — PDF meets {args.court} requirements")
    else:
        print(f"FAIL — PDF does NOT meet {args.court} requirements")

    if getattr(args, "json", False):
        report = {
            "file": str(fp), "court": args.court,
            "court_name": profile["name"], "passed": ok,
            "checks": checks, "timestamp": datetime.now().isoformat(),
        }
        jp = fp.with_suffix(".validation.json")
        jp.write_text(json.dumps(report, indent=2), encoding="utf-8")
        print(f"Report: {jp}")

    return 0 if ok else 1

# ===================================================================
# Command: bates
# ===================================================================

def cmd_bates(args) -> int:
    _require_fitz()
    inp = Path(args.input)
    out_dir = Path(args.output)
    prefix = args.prefix
    start = args.start
    position = getattr(args, "position", "bottom-right")
    font_size = getattr(args, "font_size", 9)

    if inp.is_dir():
        pdfs = sorted(inp.glob("*.pdf"))
        if not pdfs:
            print(f"ERROR: No PDFs in {inp}"); return 1
        print(f"Found {len(pdfs)} PDFs in {inp}")
    elif inp.is_file() and inp.suffix.lower() == ".pdf":
        pdfs = [inp]
    else:
        print(f"ERROR: {inp} is not a PDF file or directory"); return 1

    if getattr(args, "dry_run", False):
        n = start
        for p in pdfs:
            doc = fitz.open(str(p))
            pages = len(doc)
            print(f"  {p.name}: {pages} pp → "
                  f"{prefix}-{n:04d} to {prefix}-{n + pages - 1:04d}")
            n += pages
            doc.close()
        print(f"\n[DRY RUN] Would stamp {n - start} pages "
              f"starting at {prefix}-{start:04d}")
        return 0

    out_dir.mkdir(parents=True, exist_ok=True)
    cur = start
    total = 0

    for pdf_path in pdfs:
        doc = fitz.open(str(pdf_path))
        pc = len(doc)
        for i in range(pc):
            add_bates_to_page(doc[i], f"{prefix}-{cur:04d}",
                              position=position, font_size=font_size)
            cur += 1
            total += 1
        op = out_dir / pdf_path.name
        doc.save(str(op), deflate=True, garbage=3, clean=True)
        doc.close()
        print(f"  ✓ {pdf_path.name}: {pc} pp "
              f"({prefix}-{cur - pc:04d} to {prefix}-{cur - 1:04d})")

    print(f"\nBates stamped {total} pages across {len(pdfs)} files")
    print(f"  Range:  {prefix}-{start:04d}  to  {prefix}-{cur - 1:04d}")
    print(f"  Output: {out_dir}")

    log = {"prefix": prefix, "start": start, "end": cur - 1,
           "total_pages": total,
           "files": [{"file": p.name} for p in pdfs],
           "timestamp": datetime.now().isoformat()}
    lp = out_dir / "bates_log.json"
    lp.write_text(json.dumps(log, indent=2), encoding="utf-8")
    print(f"  Log:    {lp}")
    return 0

# ===================================================================
# Command: split
# ===================================================================

def cmd_split(args) -> int:
    _require_fitz()
    inp = Path(args.input)
    out_dir = Path(args.output)
    max_mb = args.max_size

    if getattr(args, "court", None):
        max_mb = get_profile(args.court).get("max_file_size_mb", max_mb)

    if not inp.exists():
        print(f"ERROR: File not found: {inp}"); return 1

    cur_mb = _file_size_mb(inp)
    print(f"Input:  {inp.name}")
    print(f"Size:   {cur_mb:.1f} MB")
    print(f"Limit:  {max_mb} MB")

    if cur_mb <= max_mb:
        print(f"\nFile is within {max_mb} MB — no split needed.")
        return 0

    doc = fitz.open(str(inp))
    total = len(doc)
    avg = cur_mb / total
    pp_part = max(1, int((max_mb * 0.85) / avg))  # 85 % safety margin
    num_parts = math.ceil(total / pp_part)

    print(f"Pages:  {total}  (avg {avg:.3f} MB/page)")
    print(f"Plan:   {num_parts} parts (~{pp_part} pp each)")

    if getattr(args, "dry_run", False):
        for i in range(num_parts):
            s = i * pp_part
            e = min(s + pp_part, total)
            print(f"  Part {i + 1}: pages {s + 1}–{e} (~{(e - s) * avg:.1f} MB)")
        doc.close()
        return 0

    out_dir.mkdir(parents=True, exist_ok=True)
    stem = inp.stem
    parts = []
    pn, sp = 1, 0

    while sp < total:
        ep = min(sp + pp_part, total)
        part = fitz.open()
        part.insert_pdf(doc, from_page=sp, to_page=ep - 1)
        name = f"{stem}_part{pn:02d}.pdf"
        pp = out_dir / name
        part.save(str(pp), deflate=True, garbage=4, clean=True)
        part_mb = _file_size_mb(pp)

        # If still too large, shrink the window
        if part_mb > max_mb and ep - sp > 1:
            part.close()
            os.remove(pp)
            pp_part = max(1, int(pp_part * 0.8))
            continue

        parts.append({"file": name, "pages": f"{sp + 1}-{ep}",
                       "size_mb": round(part_mb, 2)})
        print(f"  ✓ {name}: pages {sp + 1}–{ep} ({part_mb:.1f} MB)")
        part.close()
        sp = ep
        pn += 1

    doc.close()
    print(f"\nSplit into {len(parts)} parts in {out_dir}")

    manifest = {"source": str(inp), "source_mb": round(cur_mb, 2),
                "max_mb": max_mb, "total_pages": total, "parts": parts,
                "timestamp": datetime.now().isoformat()}
    mp = out_dir / "split_manifest.json"
    mp.write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    print(f"  Manifest: {mp}")
    return 0

# ===================================================================
# Command: courts
# ===================================================================

def cmd_courts(_args) -> int:
    """List available court profiles."""
    print("Available Court Profiles")
    print("=" * 60)
    for key in sorted(COURT_PROFILES):
        p = COURT_PROFILES[key]
        print(f"\n  {key}")
        print(f"    Name:      {p['name']}")
        print(f"    System:    {p.get('system', 'N/A')}")
        print(f"    Max size:  {p.get('max_file_size_mb', 25)} MB")
        print(f"    OCR req:   {p.get('requires_ocr', True)}")
        print(f"    Bookmarks: {p.get('requires_bookmarks', False)}")
        m = p.get("margins", {})
        if m:
            print(f"    Margins:   T={m.get('top', 1)}\" B={m.get('bottom', 1)}\" "
                  f"L={m.get('left', 1)}\" R={m.get('right', 1)}\"")
        if p.get("notes"):
            print(f"    Notes:     {p['notes']}")
    return 0

# ===================================================================
# CLI parser
# ===================================================================

def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="efiling_assembler",
        description=(
            "E-Filing PDF Assembler — LitigationOS\n"
            "Assembles court-compliant PDF packages for Michigan e-filing."
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=(
            "Examples:\n"
            "  # Assemble a motion for 14th Circuit\n"
            "  python efiling_assembler.py assemble --court 14th-circuit "
            "--type motion \\\n"
            "      --lead motion.pdf --exhibits ex_a.pdf ex_b.pdf "
            "--output PKG/\n\n"
            "  # Validate a brief for the COA\n"
            "  python efiling_assembler.py validate --court coa "
            "--file brief.pdf\n\n"
            "  # Bates-stamp a directory of exhibits\n"
            "  python efiling_assembler.py bates --input exhibits/ "
            "--prefix PIGORS-A --output bates/\n\n"
            "  # Split an oversized filing\n"
            "  python efiling_assembler.py split --input big.pdf "
            "--max-size 25 --output parts/\n\n"
            "  # List court profiles\n"
            "  python efiling_assembler.py courts\n"
        ),
    )

    sub = parser.add_subparsers(dest="command", help="Command to run")

    # ---- assemble ----
    pa = sub.add_parser("assemble", help="Assemble a filing package")
    pa.add_argument("--court", required=True,
                    help="Court profile (e.g. 14th-circuit, coa, usdc-wdmi)")
    pa.add_argument("--type", required=True,
                    help="Filing type (motion, brief, application, complaint …)")
    pa.add_argument("--lead", help="Lead document PDF")
    pa.add_argument("--attachment", nargs="+", help="Attachment PDF(s)")
    pa.add_argument("--exhibits", nargs="+", help="Exhibit PDFs (ordered A, B, …)")
    pa.add_argument("--proposed-order", help="Proposed order PDF")
    pa.add_argument("--cert-of-service", help="Certificate of service PDF")
    pa.add_argument("--output", required=True, help="Output directory")
    pa.add_argument("--case-number", help="Case number for separator pages")
    pa.add_argument("--bates-prefix",
                    help="Bates prefix (e.g. PIGORS-A)")
    pa.add_argument("--bates-start", type=int, default=1,
                    help="Bates start number (default: 1)")
    pa.add_argument("--no-separators", action="store_true",
                    help="Skip exhibit separator pages")
    pa.add_argument("--no-ocr", action="store_true",
                    help="Skip OCR text-layer check")
    pa.add_argument("--dry-run", action="store_true",
                    help="Show plan without creating files")

    # ---- validate ----
    pv = sub.add_parser("validate", help="Validate a PDF against court rules")
    pv.add_argument("--court", required=True, help="Court profile key")
    pv.add_argument("--file", required=True, help="PDF to validate")
    pv.add_argument("--json", action="store_true",
                    help="Save JSON report alongside the PDF")

    # ---- bates ----
    pb = sub.add_parser("bates", help="Add Bates number stamps")
    pb.add_argument("--input", required=True,
                    help="PDF file or directory of PDFs")
    pb.add_argument("--prefix", required=True,
                    help="Bates prefix (e.g. PIGORS-A)")
    pb.add_argument("--start", type=int, default=1,
                    help="Starting number (default: 1)")
    pb.add_argument("--output", required=True, help="Output directory")
    pb.add_argument("--position",
                    choices=["bottom-right", "bottom-center", "bottom-left"],
                    default="bottom-right", help="Stamp position")
    pb.add_argument("--font-size", type=int, default=9,
                    help="Stamp font size (default: 9)")
    pb.add_argument("--dry-run", action="store_true",
                    help="Show plan without creating files")

    # ---- split ----
    ps = sub.add_parser("split", help="Split large PDF for court limits")
    ps.add_argument("--input", required=True, help="PDF to split")
    ps.add_argument("--max-size", type=float, default=25,
                    help="Maximum MB per part (default: 25)")
    ps.add_argument("--output", required=True, help="Output directory")
    ps.add_argument("--court",
                    help="Court profile (overrides --max-size)")
    ps.add_argument("--dry-run", action="store_true",
                    help="Show plan without creating files")

    # ---- courts ----
    sub.add_parser("courts", help="List available court profiles")

    return parser

# ===================================================================
# Main
# ===================================================================

def main() -> int:
    parser = build_parser()
    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        return 1

    dispatch = {
        "assemble": cmd_assemble,
        "validate": cmd_validate,
        "bates": cmd_bates,
        "split": cmd_split,
        "courts": cmd_courts,
    }
    handler = dispatch.get(args.command)
    if not handler:
        parser.print_help()
        return 1

    try:
        return handler(args)
    except KeyboardInterrupt:
        print("\nAborted.")
        return 130
    except Exception as exc:
        print(f"\nERROR: {exc}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main() or 0)
