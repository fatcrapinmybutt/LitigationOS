"""Critical Evidence Ingestion — Phase 1: Ingest high-priority PDFs already on C:\.
Uses pypdfium2 for extraction, persists to evidence_quotes + file_inventory.
"""
import sqlite3
import hashlib
import os
import re
from pathlib import Path
from datetime import datetime

DB = r"C:\Users\andre\LitigationOS\litigation_context.db"
REPO = Path(r"C:\Users\andre\LitigationOS")

# Directories with un-ingested court documents on C:\
SCAN_DIRS = [
    REPO / "01_FILINGS",
    REPO / "07_PDF",
    REPO / "01_EVIDENCE",
    REPO / "03_COURT",
    REPO / "10_EXTERNAL",
]

# Lane detection patterns (MEEK)
LANE_PATTERNS = {
    'E': re.compile(r'(?i)(mcneill|judicial|bias|jtc|canon|ex\s*parte|benchbook|misconduct|recus)', re.I),
    'D': re.compile(r'(?i)(ppo|protection\s*order|5907|stalking|harassment)', re.I),
    'F': re.compile(r'(?i)(coa|366810|appeal|appellant|appellee)', re.I),
    'C': re.compile(r'(?i)(federal|§\s*1983|1983|civil\s*rights|conspiracy)', re.I),
    'A': re.compile(r'(?i)(custody|parenting|001507|watson|child|visitation|foc|best\s*interest)', re.I),
    'B': re.compile(r'(?i)(shady\s*oaks|eviction|housing|trailer|002760|habitability)', re.I),
}

def detect_lane(text: str, filename: str) -> str:
    """MEEK lane detection — priority: E > D > F > C > A > B."""
    combined = text[:5000] + " " + filename
    for lane, pattern in LANE_PATTERNS.items():
        if pattern.search(combined):
            return lane
    return 'A'  # Default to custody

def hash_file(path: str) -> str:
    """SHA-256 hash."""
    h = hashlib.sha256()
    with open(path, "rb") as f:
        while chunk := f.read(65536):
            h.update(chunk)
    return h.hexdigest()

def extract_pdf_text(path: str) -> list:
    """Extract text from PDF using pypdfium2. Returns list of (page_num, text)."""
    try:
        import pypdfium2 as pdfium
        doc = pdfium.PdfDocument(path)
        pages = []
        for i in range(len(doc)):
            try:
                page = doc[i]
                textpage = page.get_textpage()
                text = textpage.get_text_bounded()
                pages.append((i + 1, text))
                textpage.close()
                page.close()
            except Exception:
                pages.append((i + 1, ""))
        doc.close()
        return pages
    except ImportError:
        # Fallback to PyMuPDF
        try:
            import fitz
            doc = fitz.open(path)
            pages = []
            for i, page in enumerate(doc):
                pages.append((i + 1, page.get_text()))
            doc.close()
            return pages
        except Exception as e:
            return [(1, f"[EXTRACTION ERROR: {e}]")]
    except Exception as e:
        return [(1, f"[EXTRACTION ERROR: {e}]")]

def ingest_pdf(conn: sqlite3.Connection, file_path: str, file_name: str) -> dict:
    """Ingest a single PDF — extract, classify, persist."""
    result = {"path": file_path, "status": "unknown", "pages": 0, "quotes": 0, "lane": ""}
    
    try:
        # Check if already ingested (by path)
        exists = conn.execute(
            "SELECT COUNT(*) FROM file_inventory WHERE file_path = ?", (file_path,)
        ).fetchone()[0]
        if exists:
            result["status"] = "already_ingested"
            return result
    except:
        pass  # table might not exist
    
    try:
        file_size = os.path.getsize(file_path)
        sha = hash_file(file_path)
        
        # Check dedup by hash
        try:
            hash_exists = conn.execute(
                "SELECT COUNT(*) FROM file_inventory WHERE sha256 = ?", (sha,)
            ).fetchone()[0]
            if hash_exists:
                result["status"] = "duplicate_hash"
                return result
        except:
            pass
        
        # Extract text
        pages = extract_pdf_text(file_path)
        full_text = " ".join(text for _, text in pages if text)
        
        if len(full_text.strip()) < 50:
            result["status"] = "no_text"
            result["pages"] = len(pages)
            return result
        
        # Detect lane
        lane = detect_lane(full_text, file_name)
        result["lane"] = lane
        result["pages"] = len(pages)
        
        # Insert into file_inventory
        try:
            conn.execute("""
                INSERT OR IGNORE INTO file_inventory 
                (file_path, file_name, drive, extension, file_size, sha256, page_count, status)
                VALUES (?, ?, ?, ?, ?, ?, ?, 'extracted')
            """, (file_path, file_name, file_path[0], '.pdf', file_size, sha, len(pages)))
        except Exception as e:
            pass  # table schema might differ
        
        # Extract key quotes — sentences with legal significance
        quote_patterns = [
            re.compile(r'(?:ORDER|JUDGMENT|RULING|FINDING)[:\s](.{50,300})', re.I),
            re.compile(r'(?:the court|this court|judge|mcneill)\s+(?:finds?|orders?|rules?|determines?)\s+(.{30,300})', re.I),
            re.compile(r'(?:custody|parenting\s*time|visitation)\s+(?:is|shall|will|was)\s+(.{30,200})', re.I),
            re.compile(r'(?:the\s+(?:plaintiff|defendant|father|mother|petitioner|respondent))\s+(.{30,200})', re.I),
        ]
        
        quotes_inserted = 0
        for page_num, text in pages:
            if not text or len(text.strip()) < 50:
                continue
            
            for pattern in quote_patterns:
                for match in pattern.finditer(text):
                    quote = match.group(0).strip()[:500]
                    if len(quote) > 50:
                        try:
                            conn.execute("""
                                INSERT INTO evidence_quotes 
                                (quote_text, source_file, page_number, lane, category, is_duplicate)
                                VALUES (?, ?, ?, ?, 'court_document', 0)
                            """, (quote, file_name, page_num, lane))
                            quotes_inserted += 1
                        except:
                            pass
        
        result["quotes"] = quotes_inserted
        result["status"] = "ingested"
        
    except Exception as e:
        result["status"] = f"error: {str(e)[:100]}"
    
    return result

def main():
    print("=" * 60)
    print("CRITICAL EVIDENCE INGESTION — Phase 1")
    print("Scanning C:\\ directories for un-ingested PDFs")
    print("=" * 60)
    
    conn = sqlite3.connect(DB)
    conn.execute("PRAGMA busy_timeout=60000")
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA cache_size=-32000")
    
    # Discover PDFs
    all_pdfs = []
    for scan_dir in SCAN_DIRS:
        if not scan_dir.exists():
            print(f"  ⚠️  Skip (not found): {scan_dir}")
            continue
        for f in scan_dir.rglob("*.pdf"):
            if '.git' in str(f):
                continue
            all_pdfs.append(f)
    
    print(f"\n📄 Found {len(all_pdfs)} PDFs to check across {len(SCAN_DIRS)} directories")
    
    # Process each PDF
    stats = {"ingested": 0, "already_ingested": 0, "duplicate_hash": 0, "no_text": 0, "error": 0}
    total_pages = 0
    total_quotes = 0
    
    for i, pdf in enumerate(all_pdfs):
        if i % 50 == 0 and i > 0:
            conn.commit()
            print(f"  Progress: {i}/{len(all_pdfs)} — ingested: {stats['ingested']}, quotes: {total_quotes}")
        
        result = ingest_pdf(conn, str(pdf), pdf.name)
        
        if result["status"] == "ingested":
            stats["ingested"] += 1
            total_pages += result["pages"]
            total_quotes += result["quotes"]
        elif result["status"] == "already_ingested":
            stats["already_ingested"] += 1
        elif result["status"] == "duplicate_hash":
            stats["duplicate_hash"] += 1
        elif result["status"] == "no_text":
            stats["no_text"] += 1
        else:
            stats["error"] += 1
    
    conn.commit()
    
    # Verify evidence_quotes total
    eq_total = conn.execute("SELECT COUNT(*) FROM evidence_quotes").fetchone()[0]
    
    conn.close()
    
    print(f"\n{'='*60}")
    print(f"INGESTION COMPLETE")
    print(f"{'='*60}")
    print(f"  PDFs scanned: {len(all_pdfs)}")
    print(f"  Newly ingested: {stats['ingested']}")
    print(f"  Already ingested: {stats['already_ingested']}")
    print(f"  Duplicate hash: {stats['duplicate_hash']}")
    print(f"  No extractable text: {stats['no_text']}")
    print(f"  Errors: {stats['error']}")
    print(f"  Total pages processed: {total_pages}")
    print(f"  New quotes extracted: {total_quotes}")
    print(f"  evidence_quotes total: {eq_total:,}")

if __name__ == "__main__":
    main()
