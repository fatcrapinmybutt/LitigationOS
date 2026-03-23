#!/usr/bin/env python3
"""Tool #269: I Drive PDF Ingestor
Catalogs and extracts text from PDFs in I:\\01_PDF\\ and other I:\\ directories.
Uses PyMuPDF (fitz) for text extraction when available, otherwise catalogs metadata only.
"""
import sys, os, json, sqlite3, re, glob
from datetime import datetime

sys.stdout = open(sys.stdout.fileno(), mode='w', encoding='utf-8', errors='replace')

try:
    import fitz  # PyMuPDF
    HAS_PYMUPDF = True
except ImportError:
    HAS_PYMUPDF = False

def s(v):
    return (v or "").lower()

def safe_query(conn, sql, params=()):
    try:
        return conn.execute(sql, params).fetchall()
    except:
        return []

CASE_RE = re.compile(r'(\d{4}-\d{6}-[A-Z]{2})')
MAX_FULL_TEXT = 100 * 1024  # 100KB cap for full_text column


def classify_pdf(filename, text_preview=""):
    """Classify document type and case lane from filename and text."""
    fn = s(filename)
    tp = s(text_preview)

    doc_type = "unknown"
    case_lane = ""
    evidence_value = "medium"
    case_number = ""

    # Case number extraction
    case_match = CASE_RE.search(filename) or CASE_RE.search(text_preview[:500] if text_preview else "")
    if case_match:
        case_number = case_match.group(1)

    # Document type classification
    if "order" in fn:
        doc_type = "order"
        evidence_value = "high"
    elif "motion" in fn:
        doc_type = "motion"
        evidence_value = "high"
    elif "judgment" in fn or "judgement" in fn:
        doc_type = "judgment"
        evidence_value = "high"
    elif "petition" in fn:
        doc_type = "petition"
    elif "exhibit" in fn or "jtc_exhibit" in fn:
        doc_type = "exhibit"
        evidence_value = "high"
    elif "jtc" in fn:
        doc_type = "exhibit"
        evidence_value = "critical"
    elif "federal-rules" in fn or "appellate-procedure" in fn or "appellate" in fn:
        doc_type = "rules"
        evidence_value = "reference"
    elif "brief" in fn:
        doc_type = "brief"
    elif "affidavit" in fn:
        doc_type = "affidavit"
        evidence_value = "high"
    elif "subpoena" in fn:
        doc_type = "subpoena"
    elif "transcript" in fn:
        doc_type = "transcript"
        evidence_value = "high"
    elif "complaint" in fn:
        doc_type = "complaint"
        evidence_value = "high"
    elif "paper" in fn:
        doc_type = "document"
        evidence_value = "low"

    # Case lane assignment
    if "2024-001507-dc" in fn or "custody" in fn or "parenting" in fn:
        case_lane = "A"
    elif "2025-002760-cz" in fn or "housing" in fn or "shady" in fn:
        case_lane = "B"
    elif "ppo" in fn or "protection" in fn or "2023-5907-pp" in fn:
        case_lane = "D"
    elif "jtc" in fn or "misconduct" in fn or "judicial" in fn:
        case_lane = "E"
    elif "federal" in fn or "appellate" in fn or "coa" in fn or "msc" in fn:
        case_lane = "F"
    elif case_number:
        if "001507" in case_number:
            case_lane = "A"
        elif "002760" in case_number:
            case_lane = "B"
        elif "5907" in case_number:
            case_lane = "D"

    return doc_type, case_lane, evidence_value, case_number


def extract_pdf_info(filepath):
    """Extract text and metadata from a PDF file."""
    info = {
        "page_count": 0,
        "text_preview": "",
        "full_text": "",
    }
    if not HAS_PYMUPDF:
        return info
    try:
        doc = fitz.open(filepath)
        info["page_count"] = len(doc)
        all_text = []
        for page in doc:
            all_text.append(page.get_text())
        doc.close()
        full = "\n".join(all_text)
        info["text_preview"] = full[:2000]
        if len(full.encode('utf-8', errors='replace')) <= MAX_FULL_TEXT:
            info["full_text"] = full
        else:
            info["full_text"] = full[:MAX_FULL_TEXT] + "\n[TRUNCATED]"
    except Exception:
        pass
    return info


def connect_with_retry(db_path, max_retries=5, base_wait=5):
    """Connect to DB with exponential backoff retries."""
    import time
    for attempt in range(max_retries):
        try:
            conn = sqlite3.connect(db_path, timeout=120)
            conn.row_factory = sqlite3.Row
            conn.execute("PRAGMA journal_mode=WAL")
            conn.execute("PRAGMA busy_timeout=120000")
            conn.execute("PRAGMA cache_size=-32000")
            conn.execute("SELECT 1")  # test the connection
            return conn
        except sqlite3.OperationalError as e:
            if attempt < max_retries - 1:
                wait = base_wait * (2 ** attempt)
                print(f"  DB locked (attempt {attempt+1}/{max_retries}), waiting {wait}s...")
                time.sleep(wait)
            else:
                raise


def main():
    db_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', 'litigation_context.db')
    report_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'reports')
    os.makedirs(report_dir, exist_ok=True)

    print("=" * 70)
    print("TOOL #269: I DRIVE PDF INGESTOR")
    print(f"PyMuPDF available: {HAS_PYMUPDF}")
    print("=" * 70)

    scan_date = datetime.now().isoformat()
    results = {
        "tool": "#269 I Drive PDF Ingestor",
        "generated": scan_date,
        "pymupdf_available": HAS_PYMUPDF,
        "pdfs": []
    }
    all_errors = []

    # ── Phase 1: Discover PDFs (no DB needed) ──
    print("\n[1/4] Discovering PDFs...")
    pdf_paths = set()

    primary_pdfs = glob.glob(r"I:\01_PDF\*.pdf")
    for p in primary_pdfs:
        pdf_paths.add(os.path.normpath(p))
    print(f"  I:\\01_PDF\\: {len(primary_pdfs)} PDFs")

    scan_subdirs = [r"I:\01_PDF", r"I:\02_EVIDENCE", r"I:\filings", r"I:\exhibits"]
    try:
        for subdir in scan_subdirs:
            if os.path.isdir(subdir):
                for root, dirs, files in os.walk(subdir):
                    for f in files:
                        if f.lower().endswith('.pdf'):
                            pdf_paths.add(os.path.normpath(os.path.join(root, f)))
                    depth = root.replace(subdir, '').count(os.sep)
                    if depth >= 3:
                        dirs.clear()
        extra = len(pdf_paths) - len(primary_pdfs)
        if extra > 0:
            print(f"  Subdirectory scan: {extra} additional PDFs")
    except Exception as e:
        all_errors.append(f"Subdirectory scan: {e}")
        print(f"  Subdirectory scan error: {e}")

    pdf_list = sorted(pdf_paths)
    print(f"  Total unique PDFs: {len(pdf_list)}")

    # ── Phase 2: Extract text from PDFs (no DB needed) ──
    print(f"\n[2/4] Extracting text from {len(pdf_list)} PDFs...")
    pdf_records = []
    for i, fp in enumerate(pdf_list, 1):
        fname = os.path.basename(fp)
        try:
            size = os.path.getsize(fp)
            info = extract_pdf_info(fp)
            text_for_classify = info["text_preview"] or ""
            doc_type, case_lane, evidence_value, case_number = classify_pdf(fname, text_for_classify)

            record = (fp, fname, size, info["page_count"], info["text_preview"],
                      info["full_text"], case_number, doc_type, case_lane, evidence_value, scan_date)
            pdf_records.append(record)

            results["pdfs"].append({
                "file": fname, "path": fp, "size": size,
                "pages": info["page_count"], "type": doc_type,
                "lane": case_lane, "value": evidence_value,
                "case_number": case_number,
                "text_preview_len": len(info["text_preview"]),
            })
            print(f"  [{i}/{len(pdf_list)}] {fname}: {doc_type}, lane={case_lane or '?'}, "
                  f"{size:,}B, {info['page_count']}pp")
        except Exception as e:
            all_errors.append(f"{fname}: {e}")
            print(f"  [{i}] {fname}: ERROR — {e}")

    # ── Phase 3: Write to DB in one short transaction with retry ──
    print(f"\n[3/4] Writing {len(pdf_records)} records to DB...")
    ingested = 0
    try:
        conn = connect_with_retry(db_path)
        conn.execute("""CREATE TABLE IF NOT EXISTS i_drive_pdfs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            file_path TEXT UNIQUE,
            filename TEXT,
            size_bytes INTEGER,
            page_count INTEGER,
            text_preview TEXT,
            full_text TEXT,
            case_number TEXT,
            document_type TEXT,
            case_lane TEXT,
            evidence_value TEXT,
            scan_date TEXT
        )""")
        conn.executemany("""INSERT OR IGNORE INTO i_drive_pdfs
            (file_path, filename, size_bytes, page_count, text_preview,
             full_text, case_number, document_type, case_lane, evidence_value, scan_date)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""", pdf_records)
        conn.commit()
        ingested = len(pdf_records)
        print(f"  Inserted {ingested} records")
    except Exception as e:
        all_errors.append(f"DB write: {e}")
        print(f"  DB write ERROR: {e}")

    # ── Phase 4: Summary ──
    print(f"\n[4/4] Summary...")
    total_count = ingested
    try:
        total_in_db = safe_query(conn, "SELECT COUNT(*) FROM i_drive_pdfs")
        total_count = total_in_db[0][0] if total_in_db else ingested
    except:
        pass

    results["summary"] = {
        "pdfs_discovered": len(pdf_list),
        "ingested_this_run": ingested,
        "errors": len(all_errors),
        "total_in_db": total_count,
        "pymupdf": HAS_PYMUPDF,
    }

    # Type breakdown
    type_counts = {}
    lane_counts = {}
    for pdf in results["pdfs"]:
        type_counts[pdf["type"]] = type_counts.get(pdf["type"], 0) + 1
        if pdf["lane"]:
            lane_counts[pdf["lane"]] = lane_counts.get(pdf["lane"], 0) + 1
    results["summary"]["by_type"] = type_counts
    results["summary"]["by_lane"] = lane_counts

    print(f"\n{'=' * 70}")
    print(f"PDFs discovered: {len(pdf_list)}")
    print(f"Ingested this run: {ingested}")
    print(f"Total in DB: {total_count}")
    if type_counts:
        print(f"By type: {type_counts}")
    if lane_counts:
        print(f"By lane: {lane_counts}")
    if all_errors:
        print(f"Errors: {len(all_errors)}")
    print("=" * 70)

    # ── Reports ──
    md_lines = [
        "# Tool #269: I Drive PDF Ingestor Report",
        f"**Generated:** {scan_date}",
        f"**PyMuPDF:** {'Available' if HAS_PYMUPDF else 'NOT AVAILABLE — metadata only'}",
        f"**PDFs Discovered:** {len(pdf_list)}",
        f"**Ingested This Run:** {ingested}",
        f"**Total in DB:** {total_count}",
        "",
    ]

    if type_counts:
        md_lines.append("## By Document Type")
        for t, c in sorted(type_counts.items(), key=lambda x: -x[1]):
            md_lines.append(f"- **{t}**: {c}")

    if lane_counts:
        md_lines.append("\n## By Case Lane")
        lane_names = {"A": "Custody", "B": "Housing", "D": "PPO", "E": "Misconduct", "F": "Appellate"}
        for ln, c in sorted(lane_counts.items()):
            md_lines.append(f"- **Lane {ln}** ({lane_names.get(ln, '')}): {c}")

    md_lines.append("\n## All PDFs")
    for pdf in results["pdfs"]:
        md_lines.append(
            f"- `{pdf['file']}` — {pdf['type']}, lane={pdf['lane'] or '?'}, "
            f"{pdf['size']:,}B, {pdf['pages']}pp, value={pdf['value']}"
        )

    if all_errors:
        md_lines.append(f"\n## Errors ({len(all_errors)})")
        for e in all_errors[:20]:
            md_lines.append(f"- {e}")

    md_path = os.path.join(report_dir, "tool_269_i_drive_pdf_ingest.md")
    json_path = os.path.join(report_dir, "tool_269_i_drive_pdf_ingest.json")
    with open(md_path, 'w', encoding='utf-8') as f:
        f.write("\n".join(md_lines))
    with open(json_path, 'w', encoding='utf-8') as f:
        json.dump(results, f, indent=2, default=str)
    print(f"\nReports: {md_path}")
    print(f"         {json_path}")

    try:
        conn.close()
    except:
        pass


if __name__ == "__main__":
    main()
