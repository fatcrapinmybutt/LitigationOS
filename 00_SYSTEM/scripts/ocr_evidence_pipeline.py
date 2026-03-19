#!/usr/bin/env python3
"""
OCR Evidence Pipeline — Extract text from scanned images and image-based PDFs.

Processes scanned evidence files (IMG_*, Screenshot_*, scanned_*) through
OCR to unlock text content for the knowledge graph. Falls back to
PyMuPDF image extraction + basic text detection when Tesseract unavailable.

Usage:
    python ocr_evidence_pipeline.py                # Process all
    python ocr_evidence_pipeline.py --check        # Check OCR tools
    python ocr_evidence_pipeline.py --dry-run      # Preview only
    python ocr_evidence_pipeline.py --limit 20     # First 20 files
    python ocr_evidence_pipeline.py --install-ocr  # Install Tesseract
"""

import sys
import os
import re
import json
import sqlite3
import hashlib
import logging
import argparse
import time
import shutil
from pathlib import Path
from datetime import datetime, timezone
from typing import Optional, Dict, List, Tuple

sys.stdout = open(sys.stdout.fileno(), mode='w', encoding='utf-8', errors='replace')
sys.stderr = open(sys.stderr.fileno(), mode='w', encoding='utf-8', errors='replace')

# ── Configuration ──────────────────────────────────────────────────────
LITIGOS_ROOT = Path(r"C:\Users\andre\LitigationOS")
DB_PATH = LITIGOS_ROOT / "litigation_context.db"
CHECKPOINT_PATH = LITIGOS_ROOT / "00_SYSTEM" / "scripts" / "_ocr_checkpoint.json"

SEARCH_DIRS = [
    LITIGOS_ROOT / "10_IMAGES",
    LITIGOS_ROOT / "07_PDF",
    LITIGOS_ROOT / "Evidence",
    LITIGOS_ROOT / "EXHIBITS",
    LITIGOS_ROOT / "Screenshots",
    LITIGOS_ROOT / "PPO 20235907 PP EVIDENCE",
    LITIGOS_ROOT / "10_Exhibits",
]

IMAGE_EXTENSIONS = {'.jpg', '.jpeg', '.png', '.tiff', '.tif', '.bmp', '.gif', '.webp'}
SCANNED_PDF_MIN_PAGES = 1  # PDFs with images but no text

# Case patterns (same as noreply processor)
CASE_PATTERNS = {
    'A': [re.compile(r'001507|custody|parenting', re.IGNORECASE)],
    'B': [re.compile(r'002760|[Ss]hady|housing|evict', re.IGNORECASE)],
    'D': [re.compile(r'5907|PPO|protect', re.IGNORECASE)],
    'E': [re.compile(r'JTC|[Mm]c[Nn]eill|misconduct', re.IGNORECASE)],
    'F': [re.compile(r'COA|366810|appeal', re.IGNORECASE)],
}

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    datefmt='%H:%M:%S'
)
log = logging.getLogger("ocr_pipeline")


# ── Tool Detection ─────────────────────────────────────────────────────

def check_ocr_tools() -> Dict:
    """Check available OCR tools and return capabilities."""
    tools = {
        'tesseract_binary': None,
        'pytesseract': False,
        'pillow': False,
        'pymupdf': False,
        'pdf2image': False,
    }

    # Tesseract binary
    tess = shutil.which("tesseract")
    if not tess:
        # Check common Windows install paths
        common_paths = [
            r"C:\Program Files\Tesseract-OCR\tesseract.exe",
            r"C:\Program Files (x86)\Tesseract-OCR\tesseract.exe",
            r"C:\Users\andre\AppData\Local\Tesseract-OCR\tesseract.exe",
        ]
        for p in common_paths:
            if os.path.exists(p):
                tess = p
                break
    tools['tesseract_binary'] = tess

    try:
        import pytesseract
        tools['pytesseract'] = True
        if tess:
            pytesseract.pytesseract.tesseract_cmd = tess
    except ImportError:
        pass

    try:
        from PIL import Image
        tools['pillow'] = True
    except ImportError:
        pass

    try:
        import fitz
        tools['pymupdf'] = True
    except ImportError:
        pass

    try:
        from pdf2image import convert_from_path
        tools['pdf2image'] = True
    except ImportError:
        pass

    return tools


def print_tool_status(tools: Dict):
    """Print OCR tool availability."""
    print("\n" + "=" * 50)
    print("OCR TOOL STATUS")
    print("=" * 50)
    print(f"  Tesseract binary:  {'✓ ' + tools['tesseract_binary'] if tools['tesseract_binary'] else '✗ NOT FOUND'}")
    print(f"  pytesseract:       {'✓' if tools['pytesseract'] else '✗ pip install pytesseract'}")
    print(f"  Pillow (PIL):      {'✓' if tools['pillow'] else '✗ pip install Pillow'}")
    print(f"  PyMuPDF (fitz):    {'✓' if tools['pymupdf'] else '✗ pip install pymupdf'}")
    print(f"  pdf2image:         {'✓' if tools['pdf2image'] else '✗ pip install pdf2image'}")

    if tools['tesseract_binary'] and tools['pytesseract'] and tools['pillow']:
        print("\n  ✓ FULL OCR CAPABLE — Tesseract + Python bindings ready")
    elif tools['pymupdf']:
        print("\n  ⚠ PARTIAL — PyMuPDF can extract embedded images/text")
        print("    For full OCR, install: pip install pytesseract Pillow")
        print("    And Tesseract: https://github.com/UB-Mannheim/tesseract/wiki")
    else:
        print("\n  ✗ NO OCR CAPABILITY — install PyMuPDF at minimum")


# ── Database ───────────────────────────────────────────────────────────

def get_db() -> sqlite3.Connection:
    conn = sqlite3.connect(str(DB_PATH), timeout=120)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode = WAL")
    conn.execute("PRAGMA busy_timeout = 60000")
    conn.execute("PRAGMA cache_size = -32000")
    conn.execute("PRAGMA temp_store = MEMORY")
    conn.execute("PRAGMA synchronous = NORMAL")
    return conn


def ensure_tables(conn: sqlite3.Connection):
    conn.executescript("""
        CREATE TABLE IF NOT EXISTS ocr_evidence_log (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            file_path TEXT UNIQUE NOT NULL,
            sha256_hash TEXT,
            status TEXT DEFAULT 'pending',
            ocr_method TEXT,
            text_length INTEGER DEFAULT 0,
            lane TEXT,
            case_numbers TEXT,
            confidence REAL,
            document_id INTEGER,
            error_msg TEXT,
            processed_at TEXT,
            processing_time_ms INTEGER
        );

        CREATE TABLE IF NOT EXISTS documents (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            file_path TEXT UNIQUE NOT NULL,
            file_name TEXT NOT NULL,
            file_size_bytes INTEGER,
            modified_date TEXT,
            page_count INTEGER DEFAULT 0,
            sha256_hash TEXT,
            ingested_at TEXT NOT NULL
        );

        CREATE TABLE IF NOT EXISTS pages (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            document_id INTEGER NOT NULL,
            page_number INTEGER NOT NULL,
            text_content TEXT NOT NULL,
            FOREIGN KEY (document_id) REFERENCES documents(id) ON DELETE CASCADE,
            UNIQUE(document_id, page_number)
        );
    """)
    conn.commit()


# ── File Discovery ─────────────────────────────────────────────────────

def find_evidence_images() -> List[Path]:
    """Find scanned evidence images and image-based PDFs."""
    found = set()
    skip_dirs = {'.git', 'node_modules', '__pycache__', '.agents', 'pip_cache', 'pytools_venv'}

    for search_dir in SEARCH_DIRS:
        if not search_dir.exists():
            continue
        for root, dirs, files in os.walk(search_dir):
            dirs[:] = [d for d in dirs if d not in skip_dirs]
            for f in files:
                fl = f.lower()
                ext = os.path.splitext(fl)[1]

                # Match image evidence patterns
                is_evidence_image = (
                    ext in IMAGE_EXTENSIONS and (
                        fl.startswith('img_') or
                        fl.startswith('screenshot') or
                        fl.startswith('scanned') or
                        fl.startswith('scan_') or
                        fl.startswith('photo_') or
                        fl.startswith('evidence_') or
                        'receipt' in fl or
                        'police' in fl or
                        'medical' in fl or
                        'document' in fl
                    )
                )

                if is_evidence_image:
                    found.add(Path(root) / f)

    return sorted(found)


def compute_sha256(file_path: Path) -> str:
    h = hashlib.sha256()
    with open(file_path, 'rb') as f:
        for chunk in iter(lambda: f.read(65536), b''):
            h.update(chunk)
    return h.hexdigest()


# ── OCR Extraction ─────────────────────────────────────────────────────

def ocr_with_tesseract(file_path: Path) -> Tuple[str, float]:
    """OCR using Tesseract. Returns (text, confidence)."""
    try:
        import pytesseract
        from PIL import Image

        img = Image.open(str(file_path))
        # Preprocessing: convert to grayscale, enhance
        if img.mode != 'L':
            img = img.convert('L')

        # Get OCR data with confidence
        data = pytesseract.image_to_data(img, output_type=pytesseract.Output.DICT)
        texts = []
        confidences = []
        for i, text in enumerate(data['text']):
            if text.strip():
                texts.append(text)
                conf = data['conf'][i]
                if isinstance(conf, (int, float)) and conf > 0:
                    confidences.append(conf)

        full_text = ' '.join(texts)
        avg_conf = sum(confidences) / len(confidences) if confidences else 0
        return full_text, avg_conf / 100.0

    except Exception as e:
        log.debug(f"Tesseract OCR failed: {e}")
        return "", 0.0


def ocr_with_pymupdf(file_path: Path) -> Tuple[str, float]:
    """Extract text from image using PyMuPDF (for image-PDFs)."""
    try:
        import fitz
        ext = file_path.suffix.lower()

        if ext == '.pdf':
            doc = fitz.open(str(file_path))
            texts = []
            for page in doc:
                text = page.get_text("text")
                if text.strip():
                    texts.append(text.strip())
            doc.close()
            full_text = "\n".join(texts)
            return full_text, 0.9 if full_text else 0.0
        else:
            # For images: convert to PDF page then extract
            doc = fitz.open()
            img_doc = fitz.open(str(file_path))
            # Get image as pixmap
            if len(img_doc) > 0:
                page = img_doc[0]
                text = page.get_text("text")
                img_doc.close()
                doc.close()
                return text.strip(), 0.5 if text.strip() else 0.0
            img_doc.close()
            doc.close()
            return "", 0.0

    except Exception as e:
        log.debug(f"PyMuPDF extraction failed: {e}")
        return "", 0.0


def extract_text(file_path: Path, tools: Dict) -> Tuple[str, str, float]:
    """
    Extract text using best available method.
    Returns (text, method, confidence).
    """
    # Try Tesseract first (best for scanned images)
    if tools['tesseract_binary'] and tools['pytesseract'] and tools['pillow']:
        text, conf = ocr_with_tesseract(file_path)
        if text.strip():
            return text, 'tesseract', conf

    # Fallback: PyMuPDF (good for PDFs with embedded text)
    if tools['pymupdf']:
        text, conf = ocr_with_pymupdf(file_path)
        if text.strip():
            return text, 'pymupdf', conf

    return "", "none", 0.0


# ── Classification ─────────────────────────────────────────────────────

def classify_evidence(file_name: str, text: str) -> Dict:
    """Classify evidence by case lane."""
    result = {'lanes': [], 'case_numbers': []}
    combined = file_name + "\n" + text[:3000]

    for lane, patterns in CASE_PATTERNS.items():
        for pat in patterns:
            if pat.search(combined):
                if lane not in result['lanes']:
                    result['lanes'].append(lane)

    # Also classify by directory path
    path_lower = file_name.lower()
    if 'ppo' in path_lower or '5907' in path_lower:
        if 'D' not in result['lanes']:
            result['lanes'].append('D')
    if 'shady' in path_lower or 'housing' in path_lower:
        if 'B' not in result['lanes']:
            result['lanes'].append('B')

    if not result['lanes']:
        result['lanes'] = ['UNCLASSIFIED']

    return result


# ── Processing ─────────────────────────────────────────────────────────

def process_single(
    conn: sqlite3.Connection,
    file_path: Path,
    tools: Dict,
    dry_run: bool = False
) -> Dict:
    """Process a single evidence image."""
    start_ms = time.time() * 1000
    result = {'file': file_path.name, 'status': 'error', 'text_len': 0}

    try:
        sha256 = compute_sha256(file_path)

        # Check if already processed
        existing = conn.execute(
            "SELECT id FROM ocr_evidence_log WHERE sha256_hash = ? AND status = 'success'",
            (sha256,)
        ).fetchone()
        if existing:
            result['status'] = 'skipped'
            return result

        # Extract text
        text, method, confidence = extract_text(file_path, tools)
        result['text_len'] = len(text)
        result['method'] = method
        result['confidence'] = confidence

        if not text.strip():
            result['status'] = 'no_text'
            if not dry_run:
                conn.execute(
                    """INSERT OR REPLACE INTO ocr_evidence_log
                       (file_path, sha256_hash, status, ocr_method, processed_at)
                       VALUES (?, ?, 'no_text', ?, ?)""",
                    (str(file_path), sha256, method, datetime.now(timezone.utc).isoformat())
                )
                conn.commit()
            return result

        # Classify
        classification = classify_evidence(str(file_path), text)
        result['lane'] = ','.join(classification['lanes'])

        if dry_run:
            result['status'] = 'dry_run'
            return result

        # Insert into documents + pages
        stat = file_path.stat()
        mod_date = datetime.fromtimestamp(stat.st_mtime).isoformat()
        now = datetime.now(timezone.utc).isoformat()

        cur = conn.execute(
            """INSERT OR IGNORE INTO documents
               (file_path, file_name, file_size_bytes, modified_date, page_count, sha256_hash, ingested_at)
               VALUES (?, ?, ?, ?, ?, ?, ?)""",
            (str(file_path), file_path.name, stat.st_size, mod_date, 1, sha256, now)
        )
        doc_id = cur.lastrowid
        if doc_id == 0:
            # Already exists, get existing ID
            row = conn.execute(
                "SELECT id FROM documents WHERE file_path = ?", (str(file_path),)
            ).fetchone()
            doc_id = row['id'] if row else None

        if doc_id:
            conn.execute(
                "INSERT OR REPLACE INTO pages (document_id, page_number, text_content) VALUES (?, 1, ?)",
                (doc_id, text)
            )

        # Log
        elapsed_ms = int(time.time() * 1000 - start_ms)
        conn.execute(
            """INSERT OR REPLACE INTO ocr_evidence_log
               (file_path, sha256_hash, status, ocr_method, text_length, lane,
                confidence, document_id, processed_at, processing_time_ms)
               VALUES (?, ?, 'success', ?, ?, ?, ?, ?, ?, ?)""",
            (str(file_path), sha256, method, len(text), result['lane'],
             confidence, doc_id, now, elapsed_ms)
        )
        conn.commit()

        result['status'] = 'success'
        result['doc_id'] = doc_id

    except Exception as e:
        result['status'] = 'error'
        result['error'] = str(e)
        log.error(f"  Error: {e}")

    return result


def run(dry_run=False, limit=None):
    """Main OCR processing loop."""
    log.info("=" * 60)
    log.info("OCR Evidence Pipeline — LitigationOS")
    log.info("=" * 60)

    # Check tools
    tools = check_ocr_tools()
    print_tool_status(tools)

    if not tools['pymupdf'] and not (tools['tesseract_binary'] and tools['pytesseract']):
        log.error("\nNo OCR capability available. Install at minimum: pip install pymupdf")
        return

    # Find evidence images
    log.info("\nScanning for evidence images...")
    all_files = find_evidence_images()
    log.info(f"Found {len(all_files)} evidence images")

    if limit:
        all_files = all_files[:limit]

    # Connect
    conn = get_db()
    ensure_tables(conn)

    # Filter already processed
    already = set()
    try:
        rows = conn.execute(
            "SELECT file_path FROM ocr_evidence_log WHERE status = 'success'"
        ).fetchall()
        already = {r['file_path'] for r in rows}
    except Exception:
        pass
    before = len(all_files)
    all_files = [f for f in all_files if str(f) not in already]
    log.info(f"Filtered: {before - len(all_files)} already processed, {len(all_files)} remaining")

    # Process
    stats = {'total': len(all_files), 'success': 0, 'no_text': 0, 'errors': 0, 'skipped': 0}

    for i, fp in enumerate(all_files, 1):
        log.info(f"[{i}/{len(all_files)}] {fp.name}")
        result = process_single(conn, fp, tools, dry_run)

        if result['status'] in ('success', 'dry_run'):
            stats['success'] += 1
            log.info(f"  ✓ {result['text_len']} chars via {result.get('method', '?')} | Lane: {result.get('lane', '?')}")
        elif result['status'] == 'no_text':
            stats['no_text'] += 1
            log.info(f"  ⚠ No text extracted")
        elif result['status'] == 'skipped':
            stats['skipped'] += 1
        else:
            stats['errors'] += 1

        if i % 20 == 0:
            log.info(f"  📋 Progress: {stats['success']}/{i} success")

    log.info(f"\n{'='*60}")
    log.info(f"OCR COMPLETE: {stats['success']} success, {stats['no_text']} no-text, {stats['errors']} errors")
    conn.close()


# ── CLI ────────────────────────────────────────────────────────────────

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="OCR Evidence Pipeline")
    parser.add_argument('--check', action='store_true', help='Check OCR tools only')
    parser.add_argument('--dry-run', action='store_true', help='Preview without DB writes')
    parser.add_argument('--limit', type=int, help='Process first N files only')
    parser.add_argument('--install-ocr', action='store_true', help='Show install instructions')
    args = parser.parse_args()

    if args.check:
        tools = check_ocr_tools()
        print_tool_status(tools)
    elif args.install_ocr:
        print("\nTo install full OCR capability:")
        print("  1. pip install pymupdf pytesseract Pillow")
        print("  2. Download Tesseract: https://github.com/UB-Mannheim/tesseract/wiki")
        print("     Install to: C:\\Program Files\\Tesseract-OCR\\")
        print("  3. Add to PATH or this script will auto-detect common install paths")
    else:
        run(dry_run=args.dry_run, limit=args.limit)
