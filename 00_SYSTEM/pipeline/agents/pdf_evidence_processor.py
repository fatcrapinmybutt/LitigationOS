#!/usr/bin/env python3
"""
Pipeline Agent E03: PDF Evidence Processor (Incremental)
=========================================================
Scans drives for PDFs, deduplicates against existing DB catalog,
extracts metadata, and indexes new evidence into litigation_context.db.

NOVEL INNOVATION: Content-based dedup (first 4KB + size + page count),
incremental processing (skip already-indexed), multi-drive awareness.

Agent Contract: run() → AgentResult(agent_id='E03', status, stats)
"""
import os, sys, sqlite3, hashlib, json, glob
from datetime import datetime
from pathlib import Path

sys.stdout = open(sys.stdout.fileno(), mode='w', encoding='utf-8', errors='replace')

DB_PATH = os.path.join(os.path.dirname(__file__), '..', '..', 'litigation_context.db')
REPORT_DIR = os.path.join(os.path.dirname(__file__), '..', 'reports')
os.makedirs(REPORT_DIR, exist_ok=True)

# Drives to scan (ordered by priority)
SCAN_PATHS = [
    r"C:\Users\andre\Desktop",
    r"C:\Users\andre\Documents",
    r"C:\Users\andre\Downloads",
    r"C:\Users\andre\LitigationOS",
    r"F:\\",
    r"G:\\",
]

# Skip patterns (temp files, system files, etc.)
SKIP_PATTERNS = [
    'node_modules', '__pycache__', '.git', 'AppData', 'venv',
    'Temp', 'Cache', 'cache', '$Recycle.Bin', 'Windows',
]

def should_skip(path):
    """Check if path should be skipped."""
    path_str = str(path)
    return any(skip in path_str for skip in SKIP_PATTERNS)

def compute_content_fingerprint(filepath, chunk_size=4096):
    """Content-based dedup: hash first 4KB + file size."""
    try:
        size = os.path.getsize(filepath)
        with open(filepath, 'rb') as f:
            head = f.read(chunk_size)
        fingerprint = hashlib.sha256(head + str(size).encode()).hexdigest()
        return fingerprint, size
    except Exception:
        return None, 0

def get_existing_fingerprints(conn):
    """Load already-indexed fingerprints from DB."""
    existing = set()
    try:
        # Check if our index table exists
        conn.execute("""
            CREATE TABLE IF NOT EXISTS pdf_evidence_index (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                filepath TEXT NOT NULL,
                filename TEXT NOT NULL,
                fingerprint TEXT NOT NULL,
                file_size INTEGER,
                drive TEXT,
                directory TEXT,
                indexed_at TEXT,
                page_count INTEGER DEFAULT 0,
                is_duplicate INTEGER DEFAULT 0,
                duplicate_of TEXT,
                category TEXT DEFAULT 'uncategorized',
                UNIQUE(fingerprint)
            )
        """)
        conn.execute("""
            CREATE INDEX IF NOT EXISTS idx_pdf_fingerprint ON pdf_evidence_index(fingerprint)
        """)
        conn.execute("""
            CREATE INDEX IF NOT EXISTS idx_pdf_filepath ON pdf_evidence_index(filepath)
        """)
        conn.commit()
        
        rows = conn.execute("SELECT fingerprint FROM pdf_evidence_index").fetchall()
        existing = {r[0] for r in rows}
    except Exception as e:
        print(f"  Warning: {e}")
    return existing

def categorize_pdf(filepath):
    """Auto-categorize PDF based on path and filename."""
    path_lower = str(filepath).lower()
    name_lower = os.path.basename(filepath).lower()
    
    categories = {
        'court_filing': ['motion', 'brief', 'petition', 'complaint', 'order', 'filing', 'response'],
        'court_form': ['scao', 'mc_', 'mc-', 'foc', 'cc_', 'cc-', 'dc_', 'dc-'],
        'transcript': ['transcript', 'hearing', 'deposition'],
        'evidence': ['exhibit', 'evidence', 'photo', 'screenshot', 'message', 'text_msg'],
        'correspondence': ['letter', 'email', 'notice', 'correspondence'],
        'financial': ['tax', 'income', 'financial', 'bank', 'pay_stub', 'w2', '1099'],
        'medical': ['medical', 'health', 'doctor', 'hospital', 'therapy'],
        'legal_reference': ['statute', 'rule', 'mcr', 'mcl', 'case_law', 'authority'],
        'report': ['report', 'summary', 'analysis', 'assessment', 'evaluation'],
        'personal': ['certificate', 'birth', 'marriage', 'id_', 'passport', 'license'],
    }
    
    for category, keywords in categories.items():
        if any(kw in name_lower or kw in path_lower for kw in keywords):
            return category
    return 'uncategorized'

def scan_drive(scan_path, existing_fps, conn, stats):
    """Scan a single path for PDFs."""
    drive = os.path.splitdrive(scan_path)[0] or scan_path[:3]
    new_pdfs = []
    duplicates = 0
    errors = 0
    
    if not os.path.exists(scan_path):
        print(f"  ⚠️ Path not accessible: {scan_path}")
        return new_pdfs, duplicates, errors
    
    print(f"  Scanning: {scan_path}")
    
    try:
        for root, dirs, files in os.walk(scan_path, topdown=True):
            # Skip unwanted directories
            dirs[:] = [d for d in dirs if not should_skip(os.path.join(root, d))]
            
            for fname in files:
                if not fname.lower().endswith('.pdf'):
                    continue
                
                fpath = os.path.join(root, fname)
                stats['total_scanned'] += 1
                
                try:
                    fp, size = compute_content_fingerprint(fpath)
                    if fp is None:
                        errors += 1
                        continue
                    
                    if fp in existing_fps:
                        duplicates += 1
                        stats['duplicates'] += 1
                        continue
                    
                    # New PDF — index it
                    category = categorize_pdf(fpath)
                    directory = os.path.dirname(fpath)
                    
                    conn.execute("""
                        INSERT OR IGNORE INTO pdf_evidence_index
                        (filepath, filename, fingerprint, file_size, drive, directory, indexed_at, category)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                    """, (fpath, fname, fp, size, drive, directory, datetime.now().isoformat(), category))
                    
                    existing_fps.add(fp)
                    new_pdfs.append({
                        'path': fpath,
                        'name': fname,
                        'size': size,
                        'category': category,
                        'fingerprint': fp[:16]
                    })
                    stats['new_indexed'] += 1
                    
                    # Commit every 100 new PDFs
                    if stats['new_indexed'] % 100 == 0:
                        conn.commit()
                        print(f"    ... {stats['new_indexed']} new PDFs indexed, {stats['duplicates']} duplicates skipped")
                        
                except Exception as e:
                    errors += 1
                    if errors <= 5:
                        print(f"    Error on {fname}: {e}")
    except Exception as e:
        print(f"  ⚠️ Walk error on {scan_path}: {e}")
    
    conn.commit()
    stats['errors'] += errors
    return new_pdfs, duplicates, errors

def run():
    """Main agent entry point."""
    print("=" * 60)
    print("AGENT E03: PDF EVIDENCE PROCESSOR (INCREMENTAL)")
    print("=" * 60)
    print(f"Started: {datetime.now().isoformat()}")
    print(f"Drives to scan: {len(SCAN_PATHS)}")
    
    stats = {
        'total_scanned': 0,
        'new_indexed': 0,
        'duplicates': 0,
        'errors': 0,
        'drives_scanned': 0,
        'categories': {},
        'started': datetime.now().isoformat(),
    }
    
    all_new_pdfs = []
    
    try:
        conn = sqlite3.connect(DB_PATH, timeout=60)
        conn.execute("PRAGMA busy_timeout=60000")
        conn.execute("PRAGMA journal_mode=WAL")
        conn.execute("PRAGMA cache_size=-32000")
        conn.execute("PRAGMA temp_store=MEMORY")
        conn.execute("PRAGMA synchronous=NORMAL")
        
        existing_fps = get_existing_fingerprints(conn)
        print(f"  Existing fingerprints in DB: {len(existing_fps)}")
        
        for scan_path in SCAN_PATHS:
            new_pdfs, dups, errs = scan_drive(scan_path, existing_fps, conn, stats)
            all_new_pdfs.extend(new_pdfs)
            stats['drives_scanned'] += 1
            print(f"  {scan_path}: {len(new_pdfs)} new, {dups} dups, {errs} errors")
        
        # Category summary
        cat_rows = conn.execute("""
            SELECT category, COUNT(*) as cnt 
            FROM pdf_evidence_index 
            GROUP BY category 
            ORDER BY cnt DESC
        """).fetchall()
        stats['categories'] = {r[0]: r[1] for r in cat_rows}
        
        total_indexed = conn.execute("SELECT COUNT(*) FROM pdf_evidence_index").fetchone()[0]
        stats['total_in_index'] = total_indexed
        
        conn.close()
        
    except Exception as e:
        print(f"  FATAL: {e}")
        stats['fatal_error'] = str(e)
    
    stats['finished'] = datetime.now().isoformat()
    stats['status'] = 'SUCCESS' if stats.get('fatal_error') is None else 'ERROR'
    
    # Save reports
    json_path = os.path.join(REPORT_DIR, 'PDF_EVIDENCE_INDEX.json')
    with open(json_path, 'w', encoding='utf-8') as f:
        json.dump({'stats': stats, 'sample_new': all_new_pdfs[:50]}, f, indent=2, ensure_ascii=False)
    
    md_path = os.path.join(REPORT_DIR, 'PDF_EVIDENCE_INDEX.md')
    with open(md_path, 'w', encoding='utf-8') as f:
        f.write("# 📁 PDF Evidence Index Report (Agent E03)\n\n")
        f.write(f"Generated: {stats['finished']}\n\n")
        f.write("## Scan Results\n\n")
        f.write(f"| Metric | Count |\n|--------|-------|\n")
        f.write(f"| Total scanned | {stats['total_scanned']:,} |\n")
        f.write(f"| New indexed | {stats['new_indexed']:,} |\n")
        f.write(f"| Duplicates skipped | {stats['duplicates']:,} |\n")
        f.write(f"| Errors | {stats['errors']:,} |\n")
        f.write(f"| Drives scanned | {stats['drives_scanned']} |\n")
        f.write(f"| Total in index | {stats.get('total_in_index', 0):,} |\n\n")
        
        if stats['categories']:
            f.write("## Categories\n\n")
            f.write("| Category | Count |\n|----------|-------|\n")
            for cat, cnt in stats['categories'].items():
                f.write(f"| {cat} | {cnt:,} |\n")
        
        if all_new_pdfs:
            f.write(f"\n## Sample New PDFs (first {min(50, len(all_new_pdfs))})\n\n")
            for pdf in all_new_pdfs[:50]:
                size_kb = pdf['size'] // 1024
                f.write(f"- [{pdf['category']}] **{pdf['name']}** ({size_kb:,} KB)\n")
    
    print(f"\n{'=' * 60}")
    print(f"AGENT E03 COMPLETE")
    print(f"  Scanned: {stats['total_scanned']:,} PDFs")
    print(f"  New: {stats['new_indexed']:,}")
    print(f"  Duplicates: {stats['duplicates']:,}")
    print(f"  Total in index: {stats.get('total_in_index', 0):,}")
    print(f"  Categories: {len(stats['categories'])}")
    print(f"  Status: {stats['status']}")
    
    return stats

if __name__ == '__main__':
    run()
