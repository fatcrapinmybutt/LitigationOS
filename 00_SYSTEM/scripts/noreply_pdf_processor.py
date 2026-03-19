#!/usr/bin/env python3
"""
NoReply PDF Processor — Extract, classify, and index 347+ court documents.

Critical path: This script unblocks 5 downstream todos by getting court
documents into the knowledge graph with full-text search.

Reads NoReply PDFs from 07_PDF/ and other directories, extracts text
via PyMuPDF, classifies by case number/lane, and inserts into the
central litigation_context.db (documents + pages + pages_fts tables).

Usage:
    python noreply_pdf_processor.py              # Process all unprocessed
    python noreply_pdf_processor.py --dry-run    # Preview without DB writes
    python noreply_pdf_processor.py --reprocess  # Force reprocess all
    python noreply_pdf_processor.py --limit 50   # Process first 50 only
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
from pathlib import Path
from datetime import datetime, timezone
from typing import Optional, Dict, List, Tuple

# UTF-8 safety
sys.stdout = open(sys.stdout.fileno(), mode='w', encoding='utf-8', errors='replace')
sys.stderr = open(sys.stderr.fileno(), mode='w', encoding='utf-8', errors='replace')

# ── Configuration ──────────────────────────────────────────────────────
LITIGOS_ROOT = Path(r"C:\Users\andre\LitigationOS")
DB_PATH = LITIGOS_ROOT / "litigation_context.db"
CHECKPOINT_PATH = LITIGOS_ROOT / "00_SYSTEM" / "scripts" / "_noreply_checkpoint.json"

SEARCH_DIRS = [
    LITIGOS_ROOT / "07_PDF",
    LITIGOS_ROOT / "01_FILINGS",
    LITIGOS_ROOT / "COURT_PACKETS_v3",
    LITIGOS_ROOT / "JUDICIAL_PACKET_v2026-02-10_R2",
    LITIGOS_ROOT / "Dockets",
    LITIGOS_ROOT / "LITIGATION_FILES",
    LITIGOS_ROOT / "By_Case",
    LITIGOS_ROOT / "NoReply_20250613_161251 conv",
]

# Case number patterns → lane assignment
CASE_PATTERNS = {
    'A': [
        re.compile(r'2024[-\s]?001507[-\s]?DC', re.IGNORECASE),
        re.compile(r'001507', re.IGNORECASE),
    ],
    'B': [
        re.compile(r'2025[-\s]?002760[-\s]?CZ', re.IGNORECASE),
        re.compile(r'002760', re.IGNORECASE),
        re.compile(r'[Ss]hady\s*[Oo]aks', re.IGNORECASE),
    ],
    'D': [
        re.compile(r'2023[-\s]?005?907[-\s]?PP', re.IGNORECASE),
        re.compile(r'5907', re.IGNORECASE),
        re.compile(r'PPO|[Pp]rotect(?:ive|ion)\s*[Oo]rder', re.IGNORECASE),
    ],
    'E': [
        re.compile(r'JTC|[Jj]udicial\s*[Tt]enure', re.IGNORECASE),
        re.compile(r'[Mm]c[Nn]eill', re.IGNORECASE),
        re.compile(r'[Dd]isqualif', re.IGNORECASE),
    ],
    'F': [
        re.compile(r'COA|[Cc]ourt\s*of\s*[Aa]ppeals', re.IGNORECASE),
        re.compile(r'366810', re.IGNORECASE),
        re.compile(r'MSC|[Ss]upreme\s*[Cc]ourt', re.IGNORECASE),
        re.compile(r'MCR\s*7\.\d', re.IGNORECASE),
    ],
    'LT': [
        re.compile(r'2025[-\s]?25061626[-\s]?LT', re.IGNORECASE),
        re.compile(r'25061626', re.IGNORECASE),
        re.compile(r'60th\s*[Dd]istrict', re.IGNORECASE),
        re.compile(r'[Ll]andlord|[Ee]viction', re.IGNORECASE),
    ],
}

# Document type detection from content
DOCTYPE_PATTERNS = {
    'order': re.compile(r'\bORDER\b.*\bCOURT\b|\bIT IS (?:HEREBY )?ORDERED\b', re.IGNORECASE),
    'motion': re.compile(r'\bMOTION\b.*(?:TO|FOR)\b', re.IGNORECASE),
    'brief': re.compile(r'\bBRIEF\b|\bARGUMENT\b.*\bAUTHORIT', re.IGNORECASE),
    'notice': re.compile(r'\bNOTICE\b.*(?:HEARING|FILING|APPEAR)', re.IGNORECASE),
    'affidavit': re.compile(r'\bAFFIDAVIT\b|\bSWORN\b.*\bSTATEMENT\b', re.IGNORECASE),
    'complaint': re.compile(r'\bCOMPLAINT\b|\bVERIFIED COMPLAINT\b', re.IGNORECASE),
    'response': re.compile(r'\bRESPONSE\b|\bANSWER\b.*\bCOMPLAINT\b', re.IGNORECASE),
    'proof_of_service': re.compile(r'\bPROOF OF SERVICE\b|\bCERTIFICATE OF SERVICE\b', re.IGNORECASE),
    'transcript': re.compile(r'\bTRANSCRIPT\b|\bPROCEEDINGS\b', re.IGNORECASE),
    'judgment': re.compile(r'\bJUDGMENT\b|\bVERDICT\b', re.IGNORECASE),
    'stipulation': re.compile(r'\bSTIPULAT', re.IGNORECASE),
    'subpoena': re.compile(r'\bSUBPOENA\b', re.IGNORECASE),
}

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    datefmt='%H:%M:%S'
)
log = logging.getLogger("noreply_processor")


# ── Database Setup ─────────────────────────────────────────────────────

def get_db() -> sqlite3.Connection:
    """Open DB with proper PRAGMAs for WAL mode + performance."""
    conn = sqlite3.connect(str(DB_PATH), timeout=120)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode = WAL")
    conn.execute("PRAGMA busy_timeout = 60000")
    conn.execute("PRAGMA cache_size = -32000")
    conn.execute("PRAGMA temp_store = MEMORY")
    conn.execute("PRAGMA synchronous = NORMAL")
    return conn


def ensure_tables(conn: sqlite3.Connection):
    """Ensure documents + pages + FTS tables exist."""
    conn.executescript("""
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

        -- Processor tracking table
        CREATE TABLE IF NOT EXISTS noreply_processing_log (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            file_path TEXT UNIQUE NOT NULL,
            sha256_hash TEXT,
            status TEXT DEFAULT 'pending',
            lane TEXT,
            doc_type TEXT,
            case_numbers TEXT,
            page_count INTEGER DEFAULT 0,
            document_id INTEGER,
            error_msg TEXT,
            processed_at TEXT,
            processing_time_ms INTEGER
        );
    """)

    # Check if pages_fts exists; create only if missing
    fts_exists = conn.execute(
        "SELECT name FROM sqlite_master WHERE type='table' AND name='pages_fts'"
    ).fetchone()
    if not fts_exists:
        conn.executescript("""
            CREATE VIRTUAL TABLE pages_fts USING fts5(
                text_content,
                content='pages',
                content_rowid='id',
                tokenize='porter unicode61'
            );

            CREATE TRIGGER IF NOT EXISTS pages_ai AFTER INSERT ON pages BEGIN
                INSERT INTO pages_fts(rowid, text_content) VALUES (new.id, new.text_content);
            END;
            CREATE TRIGGER IF NOT EXISTS pages_ad AFTER DELETE ON pages BEGIN
                INSERT INTO pages_fts(pages_fts, rowid, text_content)
                VALUES('delete', old.id, old.text_content);
            END;
            CREATE TRIGGER IF NOT EXISTS pages_au AFTER UPDATE ON pages BEGIN
                INSERT INTO pages_fts(pages_fts, rowid, text_content)
                VALUES('delete', old.id, old.text_content);
                INSERT INTO pages_fts(rowid, text_content) VALUES (new.id, new.text_content);
            END;
        """)
    conn.commit()


# ── File Discovery ─────────────────────────────────────────────────────

def find_noreply_pdfs() -> List[Path]:
    """Find all NoReply PDF files across search directories."""
    found = set()
    for search_dir in SEARCH_DIRS:
        if not search_dir.exists():
            continue
        for root, dirs, files in os.walk(search_dir):
            dirs[:] = [d for d in dirs if d not in ('.git', 'node_modules', '__pycache__')]
            for f in files:
                if f.lower().startswith('noreply') and f.lower().endswith('.pdf'):
                    found.add(Path(root) / f)

    # Also do a broad search for any we missed
    for root, dirs, files in os.walk(LITIGOS_ROOT):
        dirs[:] = [d for d in dirs if d not in (
            '.git', 'node_modules', '__pycache__', '.agents',
            'pip_cache', 'pytools_venv', 'java-1.8.0-openjdk-1.8.0.392-1.b08.redhat.windows.x86_64'
        )]
        for f in files:
            if f.lower().startswith('noreply') and f.lower().endswith('.pdf'):
                found.add(Path(root) / f)

    return sorted(found)


def compute_sha256(file_path: Path) -> str:
    """Compute SHA-256 hash of file."""
    h = hashlib.sha256()
    with open(file_path, 'rb') as f:
        for chunk in iter(lambda: f.read(65536), b''):
            h.update(chunk)
    return h.hexdigest()


# ── PDF Text Extraction ────────────────────────────────────────────────

def extract_pdf_text(file_path: Path) -> List[Dict]:
    """Extract text from PDF using PyMuPDF. Returns list of page dicts."""
    try:
        import fitz  # PyMuPDF
    except ImportError:
        log.error("PyMuPDF not installed. Run: pip install pymupdf")
        return []

    pages = []
    try:
        doc = fitz.open(str(file_path))
        for page_num in range(len(doc)):
            page = doc[page_num]
            text = page.get_text("text")
            if text and text.strip():
                pages.append({
                    "page_number": page_num + 1,
                    "text_content": text.strip()
                })
        doc.close()
    except Exception as e:
        log.error(f"  PyMuPDF extraction failed for {file_path.name}: {e}")
    return pages


# ── Classification ─────────────────────────────────────────────────────

def classify_document(file_name: str, full_text: str) -> Dict:
    """Classify document by case number, lane, and document type."""
    result = {
        'lanes': [],
        'case_numbers': [],
        'doc_type': 'unknown',
    }

    # Check filename + content against case patterns
    combined = file_name + "\n" + full_text[:5000]  # First 5000 chars for speed
    for lane, patterns in CASE_PATTERNS.items():
        for pat in patterns:
            if pat.search(combined):
                if lane not in result['lanes']:
                    result['lanes'].append(lane)
                # Extract actual case number if found
                match = pat.search(combined)
                if match:
                    cn = match.group(0)
                    if cn not in result['case_numbers']:
                        result['case_numbers'].append(cn)

    # Detect document type
    for dtype, pat in DOCTYPE_PATTERNS.items():
        if pat.search(combined):
            result['doc_type'] = dtype
            break

    # Default lane if none detected
    if not result['lanes']:
        result['lanes'] = ['UNCLASSIFIED']

    return result


# ── Processing ─────────────────────────────────────────────────────────

def process_single_pdf(
    conn: sqlite3.Connection,
    file_path: Path,
    dry_run: bool = False
) -> Dict:
    """Process a single NoReply PDF. Returns status dict."""
    start_ms = time.time() * 1000
    result = {
        'file': file_path.name,
        'status': 'error',
        'pages': 0,
        'lane': '',
        'doc_type': '',
    }

    try:
        # 1. Compute hash
        sha256 = compute_sha256(file_path)

        # 2. Check if already processed (by hash or path)
        existing = conn.execute(
            "SELECT id, file_path FROM documents WHERE sha256_hash = ? OR file_path = ?",
            (sha256, str(file_path))
        ).fetchone()

        if existing:
            result['status'] = 'skipped_exists'
            result['doc_id'] = existing['id']
            return result

        # 3. Extract text
        pages = extract_pdf_text(file_path)
        if not pages:
            result['status'] = 'no_text'
            # Log even empty extractions
            if not dry_run:
                conn.execute(
                    """INSERT OR REPLACE INTO noreply_processing_log 
                       (file_path, sha256_hash, status, page_count, processed_at, processing_time_ms)
                       VALUES (?, ?, 'no_text', 0, ?, ?)""",
                    (str(file_path), sha256, datetime.now(timezone.utc).isoformat(),
                     int(time.time() * 1000 - start_ms))
                )
                conn.commit()
            return result

        # 4. Classify
        full_text = "\n".join(p['text_content'] for p in pages)
        classification = classify_document(file_path.name, full_text)

        result['pages'] = len(pages)
        result['lane'] = ','.join(classification['lanes'])
        result['doc_type'] = classification['doc_type']
        result['case_numbers'] = ','.join(classification['case_numbers'])

        if dry_run:
            result['status'] = 'dry_run'
            return result

        # 5. Insert into documents table
        stat = file_path.stat()
        mod_date = datetime.fromtimestamp(stat.st_mtime).isoformat()
        now = datetime.now(timezone.utc).isoformat()

        cur = conn.execute(
            """INSERT INTO documents
               (file_path, file_name, file_size_bytes, modified_date, page_count, sha256_hash, ingested_at)
               VALUES (?, ?, ?, ?, ?, ?, ?)""",
            (str(file_path), file_path.name, stat.st_size, mod_date, len(pages), sha256, now)
        )
        doc_id = cur.lastrowid

        # 6. Insert pages (batch)
        conn.executemany(
            "INSERT INTO pages (document_id, page_number, text_content) VALUES (?, ?, ?)",
            [(doc_id, p['page_number'], p['text_content']) for p in pages]
        )

        # 7. Log processing
        elapsed_ms = int(time.time() * 1000 - start_ms)
        conn.execute(
            """INSERT OR REPLACE INTO noreply_processing_log
               (file_path, sha256_hash, status, lane, doc_type, case_numbers,
                page_count, document_id, processed_at, processing_time_ms)
               VALUES (?, ?, 'success', ?, ?, ?, ?, ?, ?, ?)""",
            (str(file_path), sha256, result['lane'], result['doc_type'],
             result['case_numbers'], len(pages), doc_id, now, elapsed_ms)
        )

        conn.commit()
        result['status'] = 'success'
        result['doc_id'] = doc_id

    except Exception as e:
        result['status'] = 'error'
        result['error'] = str(e)
        log.error(f"  Error processing {file_path.name}: {e}")
        try:
            conn.execute(
                """INSERT OR REPLACE INTO noreply_processing_log
                   (file_path, status, error_msg, processed_at)
                   VALUES (?, 'error', ?, ?)""",
                (str(file_path), str(e), datetime.now(timezone.utc).isoformat())
            )
            conn.commit()
        except Exception:
            pass

    return result


def save_checkpoint(stats: Dict):
    """Save processing checkpoint for crash resume."""
    try:
        with open(CHECKPOINT_PATH, 'w') as f:
            json.dump(stats, f, indent=2, default=str)
    except Exception as e:
        log.warning(f"Checkpoint save failed: {e}")


def run(dry_run=False, reprocess=False, limit=None):
    """Main processing loop."""
    log.info("=" * 60)
    log.info("NoReply PDF Processor — LitigationOS")
    log.info("=" * 60)

    # 1. Find all PDFs
    log.info("Scanning for NoReply PDFs...")
    all_pdfs = find_noreply_pdfs()
    log.info(f"Found {len(all_pdfs)} NoReply PDFs")

    if limit:
        all_pdfs = all_pdfs[:limit]
        log.info(f"Limited to first {limit} files")

    # 2. Connect to DB
    conn = get_db()
    ensure_tables(conn)

    # 3. Filter already-processed (unless reprocess)
    if not reprocess:
        already = set()
        try:
            rows = conn.execute(
                "SELECT file_path FROM noreply_processing_log WHERE status = 'success'"
            ).fetchall()
            already = {r['file_path'] for r in rows}
        except Exception:
            pass
        before = len(all_pdfs)
        all_pdfs = [p for p in all_pdfs if str(p) not in already]
        log.info(f"Filtered: {before - len(all_pdfs)} already processed, {len(all_pdfs)} remaining")

    # 4. Process each PDF
    stats = {
        'total': len(all_pdfs),
        'success': 0,
        'skipped': 0,
        'no_text': 0,
        'errors': 0,
        'total_pages': 0,
        'lanes': {},
        'doc_types': {},
        'started_at': datetime.now().isoformat(),
    }

    for i, pdf_path in enumerate(all_pdfs, 1):
        log.info(f"[{i}/{len(all_pdfs)}] Processing: {pdf_path.name}")

        result = process_single_pdf(conn, pdf_path, dry_run)

        # Update stats
        if result['status'] == 'success' or result['status'] == 'dry_run':
            stats['success'] += 1
            stats['total_pages'] += result['pages']
            lane = result.get('lane', 'UNCLASSIFIED')
            stats['lanes'][lane] = stats['lanes'].get(lane, 0) + 1
            dtype = result.get('doc_type', 'unknown')
            stats['doc_types'][dtype] = stats['doc_types'].get(dtype, 0) + 1
            log.info(f"  ✓ {result['pages']} pages | Lane: {result.get('lane')} | Type: {result.get('doc_type')}")
        elif result['status'] == 'skipped_exists':
            stats['skipped'] += 1
            log.info(f"  ⊘ Already indexed (doc_id={result.get('doc_id')})")
        elif result['status'] == 'no_text':
            stats['no_text'] += 1
            log.info(f"  ⚠ No text extracted (may need OCR)")
        else:
            stats['errors'] += 1
            log.error(f"  ✗ Error: {result.get('error', 'unknown')}")

        # Checkpoint every 25 files
        if i % 25 == 0:
            save_checkpoint(stats)
            log.info(f"  📋 Checkpoint saved ({stats['success']}/{i} success)")

    # 5. Final stats
    stats['finished_at'] = datetime.now().isoformat()
    save_checkpoint(stats)

    log.info("\n" + "=" * 60)
    log.info("PROCESSING COMPLETE")
    log.info("=" * 60)
    log.info(f"  Total files:    {stats['total']}")
    log.info(f"  Successful:     {stats['success']}")
    log.info(f"  Skipped (dup):  {stats['skipped']}")
    log.info(f"  No text (OCR):  {stats['no_text']}")
    log.info(f"  Errors:         {stats['errors']}")
    log.info(f"  Total pages:    {stats['total_pages']}")
    log.info(f"\n  By Lane:")
    for lane, count in sorted(stats['lanes'].items()):
        log.info(f"    {lane}: {count}")
    log.info(f"\n  By Document Type:")
    for dtype, count in sorted(stats['doc_types'].items()):
        log.info(f"    {dtype}: {count}")

    conn.close()
    return stats


# ── CLI Entry Point ────────────────────────────────────────────────────

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="NoReply PDF Processor")
    parser.add_argument('--dry-run', action='store_true', help='Preview without DB writes')
    parser.add_argument('--reprocess', action='store_true', help='Force reprocess all files')
    parser.add_argument('--limit', type=int, help='Process only first N files')
    args = parser.parse_args()

    run(dry_run=args.dry_run, reprocess=args.reprocess, limit=args.limit)
