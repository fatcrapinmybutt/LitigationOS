"""PASS 4: Full-Text Intelligence Index from key PDFs."""
import sqlite3, os, json, fitz  # PyMuPDF
from datetime import datetime

INVENTORY_DB = r"I:\DRIVE_ORG\drive_inventory.db"
MAIN_DB = r"C:\Users\andre\LitigationOS\litigation_context.db"
LOG = r"I:\DRIVE_ORG\operations.log"
FTS_OUT = r"I:\DRIVE_ORG\document_fulltext.db"

def log(msg):
    ts = datetime.now().isoformat()
    line = f"[{ts}] {msg}"
    print(line, flush=True)
    with open(LOG, "a", encoding="utf-8") as f:
        f.write(line + "\n")

def extract_pdf_text(path, max_pages=50):
    """Extract text from PDF using PyMuPDF."""
    try:
        doc = fitz.open(path)
        text = ""
        for i, page in enumerate(doc):
            if i >= max_pages:
                break
            text += page.get_text() + "\n"
        doc.close()
        return text.strip()
    except:
        return ""

def run():
    log("=" * 60)
    log("PASS 4: FULL-TEXT INTELLIGENCE INDEX")
    log("=" * 60)
    
    # Create FTS database (separate from main to avoid bloating it)
    fts = sqlite3.connect(FTS_OUT)
    fts.execute("PRAGMA journal_mode=WAL")
    fts.execute("""CREATE TABLE IF NOT EXISTS documents (
        id INTEGER PRIMARY KEY,
        path TEXT UNIQUE,
        filename TEXT,
        drive TEXT,
        classification TEXT,
        text_length INTEGER,
        extracted_at TEXT
    )""")
    fts.execute("""CREATE VIRTUAL TABLE IF NOT EXISTS document_fts USING fts5(
        path, filename, content, 
        content='documents',
        content_rowid='id',
        tokenize='porter unicode61'
    )""")
    fts.commit()
    
    # Get priority PDFs from inventory
    inv = sqlite3.connect(INVENTORY_DB)
    
    # Focus on: authorities, evidence, litigation PDFs from LitigationOS directories
    priority_pdfs = inv.execute("""
        SELECT path, filename, drive, classification, size FROM files
        WHERE extension = '.pdf'
        AND size > 10000 AND size < 100000000
        AND (
            classification IN ('LITIGATION', 'EVIDENCE', 'AUTHORITY')
            OR path LIKE '%LitigationOS%'
            OR path LIKE '%Delta99%'
        )
        AND path NOT LIKE '%DEDUP_ARCHIVE%'
        AND path NOT LIKE '%node_modules%'
        ORDER BY 
            CASE classification
                WHEN 'AUTHORITY' THEN 0
                WHEN 'LITIGATION' THEN 1
                WHEN 'EVIDENCE' THEN 2
                ELSE 3
            END,
            size DESC
        LIMIT 2000
    """).fetchall()
    
    log(f"  Priority PDFs to index: {len(priority_pdfs)}")
    
    # Check already indexed
    already = set(r[0] for r in fts.execute("SELECT path FROM documents").fetchall())
    to_process = [(p, fn, d, c, s) for p, fn, d, c, s in priority_pdfs if p not in already]
    log(f"  Already indexed: {len(already)}, new: {len(to_process)}")
    
    indexed = 0
    errors = 0
    total_chars = 0
    
    for path, fname, drive, classification, size in to_process:
        text = extract_pdf_text(path)
        if text and len(text) > 50:
            fts.execute("""INSERT OR IGNORE INTO documents 
                (path, filename, drive, classification, text_length, extracted_at)
                VALUES (?, ?, ?, ?, ?, ?)""",
                (path, fname, drive, classification, len(text), datetime.now().isoformat()))
            
            rowid = fts.execute("SELECT id FROM documents WHERE path=?", (path,)).fetchone()
            if rowid:
                fts.execute("INSERT INTO document_fts(rowid, path, filename, content) VALUES (?, ?, ?, ?)",
                           (rowid[0], path, fname, text))
            
            indexed += 1
            total_chars += len(text)
        else:
            errors += 1
        
        if indexed % 100 == 0 and indexed > 0:
            fts.commit()
            log(f"    Indexed {indexed} | {total_chars/1024/1024:.1f}MB text | {errors} errors")
    
    fts.commit()
    
    # Create useful search views
    fts.execute("""CREATE VIEW IF NOT EXISTS search_help AS
        SELECT 'Search examples:' as help,
        "SELECT path, snippet(document_fts, 2, '>>>', '<<<', '...', 30) FROM document_fts WHERE document_fts MATCH 'parenting time'" as example1,
        "SELECT path, snippet(document_fts, 2, '>>>', '<<<', '...', 30) FROM document_fts WHERE document_fts MATCH 'MCR 3.206'" as example2
    """)
    fts.commit()
    
    log(f"\n{'='*60}")
    log(f"PASS 4 COMPLETE")
    log(f"  Documents indexed: {indexed}")
    log(f"  Total text extracted: {total_chars/1024/1024:.1f}MB")
    log(f"  Errors: {errors}")
    log(f"  FTS database: {FTS_OUT}")
    log(f"  Search with: SELECT path, snippet(document_fts, 2, '>>>', '<<<', '...', 30) FROM document_fts WHERE document_fts MATCH 'your query'")
    log(f"{'='*60}")
    
    inv.close()
    fts.close()

if __name__ == "__main__":
    run()
