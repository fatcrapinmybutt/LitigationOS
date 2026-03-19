#!/usr/bin/env python3
"""
LitigationOS Multi-Drive PDF Ingestion Engine
Scans H:\, G:\, F:\, I:\, Desktop for all PDFs not yet in litigation_context.db
Uses existing MCP server pdf_extractor + db modules
"""
import sys, os, time, hashlib, json, sqlite3, traceback
from pathlib import Path
from datetime import datetime

# UTF-8 safety
sys.stdout = open(sys.stdout.fileno(), mode='w', encoding='utf-8', errors='replace')
sys.stderr = open(sys.stderr.fileno(), mode='w', encoding='utf-8', errors='replace')

# Add MCP server to path
MCP_PATH = r"C:\Users\andre\LitigationOS\00_SYSTEM\mcp_server"
sys.path.insert(0, MCP_PATH)

DB_PATH = r"C:\Users\andre\LitigationOS\litigation_context.db"
CHECKPOINT_PATH = r"C:\Users\andre\LitigationOS\temp\drive_ingest_checkpoint.json"
REPORT_PATH = r"C:\Users\andre\Desktop\DRIVE_INGESTION_REPORT.md"

# Drives to scan (order: smallest first for quick wins)
SCAN_TARGETS = [
    (r"G:\\", "G_drive"),
    (r"F:\\", "F_drive"),
    (r"H:\\", "H_drive"),
    (r"C:\Users\andre\Desktop", "Desktop"),
    (r"I:\\", "I_drive"),
]

PRAGMAS = """
PRAGMA busy_timeout = 120000;
PRAGMA journal_mode = WAL;
PRAGMA cache_size = -64000;
PRAGMA temp_store = MEMORY;
PRAGMA synchronous = NORMAL;
PRAGMA mmap_size = 4294967296;
"""

def get_db():
    conn = sqlite3.connect(DB_PATH, timeout=120)
    conn.row_factory = sqlite3.Row
    for pragma in PRAGMAS.strip().split('\n'):
        conn.execute(pragma.strip())
    return conn

def ensure_tables(conn):
    """Ensure ingestion tracking tables exist"""
    conn.executescript("""
        CREATE TABLE IF NOT EXISTS documents (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            file_path TEXT UNIQUE,
            file_name TEXT,
            file_size_bytes INTEGER,
            modified_date TEXT,
            page_count INTEGER DEFAULT 0,
            sha256_hash TEXT,
            ingested_at TEXT DEFAULT (datetime('now'))
        );
        CREATE TABLE IF NOT EXISTS pages (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            document_id INTEGER,
            page_number INTEGER,
            text_content TEXT,
            FOREIGN KEY (document_id) REFERENCES documents(id)
        );
        CREATE TABLE IF NOT EXISTS drive_ingest_log (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            drive TEXT,
            file_path TEXT,
            status TEXT,
            page_count INTEGER DEFAULT 0,
            char_count INTEGER DEFAULT 0,
            error_msg TEXT,
            processed_at TEXT DEFAULT (datetime('now'))
        );
        CREATE INDEX IF NOT EXISTS idx_documents_file_path ON documents(file_path);
        CREATE INDEX IF NOT EXISTS idx_documents_sha256 ON documents(sha256_hash);
        CREATE INDEX IF NOT EXISTS idx_pages_document_id ON pages(document_id);
        CREATE INDEX IF NOT EXISTS idx_drive_ingest_log_drive ON drive_ingest_log(drive);
    """)
    # FTS5 table (may already exist)
    try:
        conn.execute("""
            CREATE VIRTUAL TABLE IF NOT EXISTS pages_fts USING fts5(
                text_content, document_id UNINDEXED, page_number UNINDEXED,
                content=pages, content_rowid=id
            );
        """)
    except:
        pass  # Already exists or FTS5 not available
    conn.commit()

def get_existing_paths(conn):
    """Get set of already-ingested file paths"""
    rows = conn.execute("SELECT file_path FROM documents").fetchall()
    return {r[0].replace('/', '\\').lower() for r in rows}

def get_existing_hashes(conn):
    """Get set of already-ingested SHA256 hashes"""
    rows = conn.execute("SELECT sha256_hash FROM documents WHERE sha256_hash IS NOT NULL").fetchall()
    return {r[0] for r in rows}

def sha256_file(path, max_bytes=50*1024*1024):
    """Fast SHA256 — read first 50MB for large files"""
    h = hashlib.sha256()
    try:
        with open(path, 'rb') as f:
            while True:
                chunk = f.read(65536)
                if not chunk:
                    break
                h.update(chunk)
                if f.tell() > max_bytes:
                    break
    except:
        return None
    return h.hexdigest()

def _long_path(p):
    """Convert to Windows long path (\\\\?\\) to handle >260 char paths"""
    p = str(p)
    if not p.startswith("\\\\?\\") and os.name == 'nt':
        p = "\\\\?\\" + os.path.abspath(p)
    return p

def extract_pdf_text(pdf_path, timeout_sec=120):
    """Extract text from PDF using PyMuPDF with timeout and error resilience"""
    try:
        import fitz  # PyMuPDF
    except ImportError:
        try:
            import pymupdf as fitz
        except ImportError:
            return None, "PyMuPDF not installed"
    
    pages = []
    lp = _long_path(pdf_path)
    try:
        doc = fitz.open(lp)
        page_count = len(doc)
        if page_count > 2000:
            doc.close()
            return None, f"Too many pages: {page_count}"
        
        start = time.time()
        for i in range(page_count):
            if time.time() - start > timeout_sec:
                break
            try:
                page = doc[i]
                text = page.get_text("text")
                if text and text.strip():
                    pages.append({"page_number": i + 1, "text_content": text.strip()})
                else:
                    # Mark as scanned/image page for future OCR
                    pix = page.get_pixmap(dpi=72)
                    if pix.width > 100 and pix.height > 100:
                        pages.append({"page_number": i + 1, "text_content": "[SCANNED_PAGE - OCR_NEEDED]"})
            except Exception as e:
                pages.append({"page_number": i + 1, "text_content": f"[EXTRACTION ERROR: {str(e)[:100]}]"})
        doc.close()
        if not pages:
            return None, "no_extractable_text"
        return pages, None
    except Exception as e:
        return None, str(e)[:200]

def scan_drive_pdfs(root_path):
    """Generator yielding all PDF paths under root"""
    root = Path(root_path)
    if not root.exists():
        return
    for pdf in root.rglob("*.pdf"):
        try:
            if pdf.stat().st_size > 0:
                yield str(pdf)
        except (PermissionError, OSError):
            continue

def load_checkpoint():
    if os.path.exists(CHECKPOINT_PATH):
        with open(CHECKPOINT_PATH, 'r') as f:
            return json.load(f)
    return {"processed": {}, "stats": {}}

def save_checkpoint(data):
    os.makedirs(os.path.dirname(CHECKPOINT_PATH), exist_ok=True)
    with open(CHECKPOINT_PATH, 'w') as f:
        json.dump(data, f, indent=2)

def ingest_drive(conn, drive_path, drive_label, existing_paths, existing_hashes, checkpoint, batch_size=25):
    """Ingest all PDFs from a drive into litigation_context.db"""
    stats = {"scanned": 0, "ingested": 0, "skipped_existing": 0, "skipped_hash": 0, 
             "errors": 0, "total_pages": 0, "total_chars": 0}
    
    print(f"\n{'='*60}")
    print(f"SCANNING: {drive_path} ({drive_label})")
    print(f"{'='*60}")
    
    # Collect all PDFs first
    pdf_paths = []
    for p in scan_drive_pdfs(drive_path):
        pdf_paths.append(p)
        if len(pdf_paths) % 500 == 0:
            print(f"  Found {len(pdf_paths)} PDFs so far...")
    
    print(f"  Total PDFs found: {len(pdf_paths)}")
    
    batch_pages = []
    batch_docs = []
    
    for idx, pdf_path in enumerate(pdf_paths):
        stats["scanned"] += 1
        norm_path = pdf_path.replace('/', '\\').lower()
        
        # Skip if already in checkpoint
        if norm_path in checkpoint.get("processed", {}):
            stats["skipped_existing"] += 1
            continue
        
        # Skip if path already in DB
        if norm_path in existing_paths:
            stats["skipped_existing"] += 1
            checkpoint.setdefault("processed", {})[norm_path] = "exists"
            continue
        
        # Get file info
        try:
            file_stat = os.stat(pdf_path)
            file_size = file_stat.st_size
            modified = datetime.fromtimestamp(file_stat.st_mtime).isoformat()
        except:
            stats["errors"] += 1
            continue
        
        # Skip files > 500MB
        if file_size > 500 * 1024 * 1024:
            stats["errors"] += 1
            conn.execute("INSERT INTO drive_ingest_log (drive, file_path, status, error_msg) VALUES (?,?,?,?)",
                        (drive_label, pdf_path, "skipped_large", f"File too large: {file_size}"))
            continue
        
        # SHA256 check for content dedup
        file_hash = sha256_file(pdf_path)
        if file_hash and file_hash in existing_hashes:
            stats["skipped_hash"] += 1
            checkpoint.setdefault("processed", {})[norm_path] = "hash_dup"
            continue
        
        # Extract text
        pages, error = extract_pdf_text(pdf_path)
        
        if error:
            stats["errors"] += 1
            conn.execute("INSERT INTO drive_ingest_log (drive, file_path, status, error_msg) VALUES (?,?,?,?)",
                        (drive_label, pdf_path, "error", error))
            checkpoint.setdefault("processed", {})[norm_path] = f"error:{error[:50]}"
            continue
        
        if not pages:
            stats["errors"] += 1
            conn.execute("INSERT INTO drive_ingest_log (drive, file_path, status, error_msg) VALUES (?,?,?,?)",
                        (drive_label, pdf_path, "no_text", "No extractable text"))
            checkpoint.setdefault("processed", {})[norm_path] = "no_text"
            continue
        
        # Insert document
        file_name = os.path.basename(pdf_path)
        page_count = len(pages)
        char_count = sum(len(p["text_content"]) for p in pages)
        
        try:
            cursor = conn.execute(
                """INSERT OR IGNORE INTO documents 
                   (file_path, file_name, file_size_bytes, modified_date, page_count, sha256_hash)
                   VALUES (?, ?, ?, ?, ?, ?)""",
                (pdf_path, file_name, file_size, modified, page_count, file_hash)
            )
            doc_id = cursor.lastrowid
            
            if doc_id and doc_id > 0:
                # Insert pages
                page_rows = [(doc_id, p["page_number"], p["text_content"]) for p in pages]
                conn.executemany(
                    "INSERT INTO pages (document_id, page_number, text_content) VALUES (?, ?, ?)",
                    page_rows
                )
                
                # Update FTS index
                try:
                    for p in pages:
                        conn.execute(
                            "INSERT INTO pages_fts (rowid, text_content, document_id, page_number) VALUES ((SELECT id FROM pages WHERE document_id=? AND page_number=?), ?, ?, ?)",
                            (doc_id, p["page_number"], p["text_content"], doc_id, p["page_number"])
                        )
                except:
                    pass  # FTS update failure is non-fatal
                
                stats["ingested"] += 1
                stats["total_pages"] += page_count
                stats["total_chars"] += char_count
                
                if file_hash:
                    existing_hashes.add(file_hash)
                existing_paths.add(norm_path)
                
                conn.execute("INSERT INTO drive_ingest_log (drive, file_path, status, page_count, char_count) VALUES (?,?,?,?,?)",
                            (drive_label, pdf_path, "success", page_count, char_count))
            else:
                stats["skipped_existing"] += 1
                
        except sqlite3.IntegrityError:
            stats["skipped_existing"] += 1
        except Exception as e:
            stats["errors"] += 1
            conn.execute("INSERT INTO drive_ingest_log (drive, file_path, status, error_msg) VALUES (?,?,?,?)",
                        (drive_label, pdf_path, "db_error", str(e)[:200]))
        
        checkpoint.setdefault("processed", {})[norm_path] = "ingested"
        
        # Commit and checkpoint every batch_size files
        if stats["ingested"] % batch_size == 0 and stats["ingested"] > 0:
            conn.commit()
            checkpoint["stats"] = checkpoint.get("stats", {})
            checkpoint["stats"][drive_label] = stats.copy()
            save_checkpoint(checkpoint)
            print(f"  [{drive_label}] Progress: {idx+1}/{len(pdf_paths)} scanned, "
                  f"{stats['ingested']} ingested, {stats['skipped_existing']} skipped, "
                  f"{stats['errors']} errors, {stats['total_pages']} pages")
    
    # Final commit
    conn.commit()
    checkpoint["stats"] = checkpoint.get("stats", {})
    checkpoint["stats"][drive_label] = stats
    save_checkpoint(checkpoint)
    
    print(f"\n  [{drive_label}] COMPLETE:")
    print(f"    Scanned:  {stats['scanned']}")
    print(f"    Ingested: {stats['ingested']}")
    print(f"    Skipped:  {stats['skipped_existing']} (path) + {stats['skipped_hash']} (hash)")
    print(f"    Errors:   {stats['errors']}")
    print(f"    Pages:    {stats['total_pages']}")
    print(f"    Chars:    {stats['total_chars']:,}")
    
    return stats

def generate_report(all_stats):
    """Generate a markdown report on Desktop"""
    lines = [
        "# LitigationOS Multi-Drive PDF Ingestion Report",
        f"## Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
        "",
        "| Drive | Scanned | Ingested | Skipped (path) | Skipped (hash) | Errors | Pages | Characters |",
        "|-------|---------|----------|----------------|----------------|--------|-------|------------|",
    ]
    
    totals = {"scanned": 0, "ingested": 0, "skipped_existing": 0, "skipped_hash": 0, 
              "errors": 0, "total_pages": 0, "total_chars": 0}
    
    for drive_label, stats in all_stats.items():
        lines.append(f"| {drive_label} | {stats['scanned']} | {stats['ingested']} | "
                     f"{stats['skipped_existing']} | {stats['skipped_hash']} | {stats['errors']} | "
                     f"{stats['total_pages']} | {stats['total_chars']:,} |")
        for k in totals:
            totals[k] += stats.get(k, 0)
    
    lines.append(f"| **TOTAL** | **{totals['scanned']}** | **{totals['ingested']}** | "
                 f"**{totals['skipped_existing']}** | **{totals['skipped_hash']}** | **{totals['errors']}** | "
                 f"**{totals['total_pages']}** | **{totals['total_chars']:,}** |")
    lines.append("")
    lines.append(f"## Database After Ingestion")
    
    try:
        conn = get_db()
        doc_count = conn.execute("SELECT COUNT(*) FROM documents").fetchone()[0]
        page_count = conn.execute("SELECT COUNT(*) FROM pages").fetchone()[0]
        lines.append(f"- Total documents: **{doc_count:,}**")
        lines.append(f"- Total pages: **{page_count:,}**")
        
        # Drive breakdown
        lines.append("")
        lines.append("### Coverage by Drive")
        lines.append("| Drive | Documents | Pages |")
        lines.append("|-------|-----------|-------|")
        
        drive_stats = conn.execute("""
            SELECT 
                CASE 
                    WHEN file_path LIKE 'C:%' THEN 'C:'
                    WHEN file_path LIKE 'D:%' THEN 'D:'
                    WHEN file_path LIKE 'F:%' THEN 'F:'
                    WHEN file_path LIKE 'G:%' THEN 'G:'
                    WHEN file_path LIKE 'H:%' THEN 'H:'
                    WHEN file_path LIKE 'I:%' THEN 'I:'
                    ELSE 'OTHER'
                END as drive,
                COUNT(*) as docs
            FROM documents GROUP BY drive ORDER BY docs DESC
        """).fetchall()
        for row in drive_stats:
            lines.append(f"| {row[0]} | {row[1]:,} | — |")
        
        conn.close()
    except Exception as e:
        lines.append(f"- Error reading DB stats: {e}")
    
    with open(REPORT_PATH, 'w', encoding='utf-8') as f:
        f.write('\n'.join(lines))
    
    print(f"\nReport saved: {REPORT_PATH}")

def main():
    print("=" * 60)
    print("LitigationOS Multi-Drive PDF Ingestion Engine")
    print(f"Database: {DB_PATH}")
    print(f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 60)
    
    # Handle command line args
    target_drive = None
    if len(sys.argv) > 1:
        target_drive = sys.argv[1].upper()
        print(f"Target drive filter: {target_drive}")
    
    conn = get_db()
    ensure_tables(conn)
    
    print("\nLoading existing document index...")
    existing_paths = get_existing_paths(conn)
    existing_hashes = get_existing_hashes(conn)
    print(f"  Existing documents: {len(existing_paths):,}")
    print(f"  Existing hashes: {len(existing_hashes):,}")
    
    checkpoint = load_checkpoint()
    all_stats = {}
    
    for drive_path, drive_label in SCAN_TARGETS:
        # Filter by target if specified
        if target_drive and not drive_label.upper().startswith(target_drive):
            continue
        
        # Check drive exists
        if not os.path.exists(drive_path):
            print(f"\n[SKIP] {drive_path} not accessible")
            continue
        
        try:
            stats = ingest_drive(conn, drive_path, drive_label, existing_paths, existing_hashes, checkpoint)
            all_stats[drive_label] = stats
        except KeyboardInterrupt:
            print("\n\n[INTERRUPTED] Saving checkpoint...")
            conn.commit()
            save_checkpoint(checkpoint)
            break
        except Exception as e:
            print(f"\n[ERROR] {drive_label}: {e}")
            traceback.print_exc()
            conn.commit()
            all_stats[drive_label] = {"scanned": 0, "ingested": 0, "skipped_existing": 0,
                                       "skipped_hash": 0, "errors": 1, "total_pages": 0, "total_chars": 0}
    
    # Generate report
    generate_report(all_stats)
    
    conn.close()
    print("\n" + "=" * 60)
    print("INGESTION COMPLETE")
    print("=" * 60)

if __name__ == "__main__":
    main()
