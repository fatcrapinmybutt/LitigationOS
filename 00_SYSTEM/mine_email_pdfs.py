"""
mine_email_pdfs.py — Extract text from email PDF attachments, classify by lane/doc_type,
identify high-value evidence, persist to email_pdf_analysis table with FTS5 index.

Uses pypdfium2 for PDF extraction. Handles corrupted PDFs gracefully.
"""
import sqlite3
import os
import re
import time
import sys
from pathlib import Path
from datetime import datetime

DB_PATH = r"C:\Users\andre\LitigationOS\litigation_context.db"
REPORT_PATH = r"C:\Users\andre\LitigationOS\04_ANALYSIS\EMAIL_PDF_ANALYSIS_REPORT.md"

# ---------------------------------------------------------------------------
# pypdfium2 import
# ---------------------------------------------------------------------------
try:
    import pypdfium2 as pdfium
    print(f"[OK] pypdfium2 version: {pdfium.V_PYPDFIUM2}")
except ImportError:
    print("[FATAL] pypdfium2 not installed. Run: pip install pypdfium2")
    sys.exit(1)


# ---------------------------------------------------------------------------
# MEEK lane classification (priority order: E → D → F → A → B)
# ---------------------------------------------------------------------------
LANE_PATTERNS = [
    ("E", re.compile(
        r"mcneill|judicial\s+misconduct|bias|jtc|judicial\s+tenure|canon|"
        r"ex\s*parte|disqualif|benchbook|recus",
        re.IGNORECASE)),
    ("D", re.compile(
        r"personal\s+protection|protection\s+order|ppo|\b5907\b|"
        r"contempt|stalking|harassment|no.contact|restrain",
        re.IGNORECASE)),
    ("F", re.compile(
        r"\bcoa\b|366810|appeal|appellant|appellee|appellate|"
        r"claim\s+of\s+appeal|court\s+of\s+appeals",
        re.IGNORECASE)),
    ("A", re.compile(
        r"custody|parenting\s+time|001507|watson|visitation|"
        r"friend\s+of\s+the?\s+court|\bfoc\b|child\s+support|"
        r"best\s+interest|MCL\s+722|parental|domestic\s+relations",
        re.IGNORECASE)),
    ("B", re.compile(
        r"shady\s+oaks|eviction|housing|trailer|002760|"
        r"landlord|tenant|habitability|lease|rent",
        re.IGNORECASE)),
]


def classify_lane(text: str) -> str:
    """Classify text into a litigation lane. Returns lane letter or 'U' for unknown."""
    for lane, pattern in LANE_PATTERNS:
        if pattern.search(text):
            return lane
    return "U"


# ---------------------------------------------------------------------------
# Document type classification
# ---------------------------------------------------------------------------
DOC_TYPE_PATTERNS = [
    ("court_order", re.compile(
        r"IT\s+IS\s+(HEREBY\s+)?ORDERED|ORDER\s+OF\s+THE\s+COURT|"
        r"COURT\s+ORDER|ENTERED\s+BY\s+THE\s+COURT|"
        r"ORDER\s+(?:REGARDING|GRANTING|DENYING|MODIFYING|SUSPENDING)|"
        r"JUDGMENT|OPINION\s+AND\s+ORDER|INTERIM\s+ORDER|"
        r"TEMPORARY\s+ORDER|CONSENT\s+ORDER|STIPULATED\s+ORDER",
        re.IGNORECASE)),
    ("police_report", re.compile(
        r"INCIDENT\s+REPORT|OFFENSE\s+REPORT|\bNSPD\b|"
        r"POLICE\s+REPORT|LAW\s+ENFORCEMENT|OFFICER\s+REPORT|"
        r"SUPPLEMENTAL\s+REPORT|CASE\s+NUMBER.*(?:NS|SO|CR)\d|"
        r"NORTH\s+SHORES?\s+(?:POLICE|PUBLIC\s+SAFETY)|"
        r"MUSKEGON\s+(?:COUNTY\s+)?SHERIFF",
        re.IGNORECASE)),
    ("foc_report", re.compile(
        r"FRIEND\s+OF\s+(?:THE\s+)?COURT|FOC\s+REPORT|"
        r"FOC\s+RECOMMENDATION|REFEREE\s+RECOMMENDATION|"
        r"CUSTODY\s+RECOMMENDATION|INVESTIGATION\s+REPORT|"
        r"FOC\s+(?:INVESTIGATION|EVALUATION|ASSESSMENT)|"
        r"PAMELA\s+RUSCO",
        re.IGNORECASE)),
    ("expert_eval", re.compile(
        r"PSYCHOLOGICAL\s+EVALUATION|HEALTHWEST|"
        r"PSYCHIATRIC\s+(?:EVALUATION|ASSESSMENT)|MENTAL\s+HEALTH|"
        r"LOCUS\s+SCORE|CLINICAL\s+ASSESSMENT|"
        r"SUBSTANCE\s+ABUSE\s+(?:EVALUATION|ASSESSMENT)|"
        r"PARENTING\s+(?:EVALUATION|ASSESSMENT|CAPACITY)",
        re.IGNORECASE)),
    ("financial", re.compile(
        r"FINANCIAL\s+(?:STATEMENT|REPORT|DISCLOSURE|RECORD)|"
        r"BANK\s+STATEMENT|TAX\s+RETURN|W-2|1099|"
        r"INCOME\s+(?:VERIFICATION|STATEMENT)|PAY\s+STUB|"
        r"UNIFORM\s+CHILD\s+SUPPORT|CHILD\s+SUPPORT\s+ORDER",
        re.IGNORECASE)),
    ("subpoena", re.compile(
        r"SUBPOENA|SUBPOENA\s+DUCES\s+TECUM|"
        r"YOU\s+ARE\s+COMMANDED|WITNESS\s+FEE",
        re.IGNORECASE)),
    ("motion", re.compile(
        r"MOTION\s+(?:TO|FOR|IN)|PLAINTIFF.S\s+MOTION|"
        r"DEFENDANT.S\s+MOTION|EMERGENCY\s+MOTION|"
        r"EX\s+PARTE\s+MOTION|MOTION\s+AND\s+BRIEF",
        re.IGNORECASE)),
    ("brief", re.compile(
        r"BRIEF\s+IN\s+SUPPORT|MEMORANDUM\s+(?:OF\s+LAW|IN\s+SUPPORT)|"
        r"APPELLATE\s+BRIEF|REPLY\s+BRIEF|RESPONSE\s+BRIEF|"
        r"LEGAL\s+MEMORANDUM|POINTS\s+AND\s+AUTHORITIES",
        re.IGNORECASE)),
    ("correspondence", re.compile(
        r"DEAR\s+(?:MR|MS|MRS|JUDGE|YOUR\s+HONOR|SIR|MADAM)|"
        r"SINCERELY|REGARDS|RE:\s+CASE|NOTICE\s+OF\s+(?:HEARING|FILING)|"
        r"LETTER\s+(?:TO|FROM)|PLEASE\s+BE\s+ADVISED",
        re.IGNORECASE)),
]


def classify_doc_type(text: str, filename: str) -> str:
    """Classify document type based on content and filename."""
    combined = text + " " + filename
    for doc_type, pattern in DOC_TYPE_PATTERNS:
        if pattern.search(combined):
            return doc_type
    return "unknown"


# ---------------------------------------------------------------------------
# Entity extraction (case numbers, names)
# ---------------------------------------------------------------------------
ENTITY_PATTERNS = {
    "case_numbers": re.compile(
        r"\b(?:20\d{2}[-/]\d{4,8}[-/]?[A-Z]{0,3})\b|"
        r"\b(?:Case\s+(?:No|Number|#)[:\s]*\S+)\b|"
        r"\bNS\d{7,}\b|\bSO\d{7,}\b",
        re.IGNORECASE),
    "judges": re.compile(
        r"(?:Judge|Hon\.?|Honorable)\s+[A-Z][a-z]+(?:\s+[A-Z]\.?)?\s+[A-Z][a-z]+",
        re.IGNORECASE),
    "attorneys": re.compile(
        r"[A-Z][a-z]+(?:\s+[A-Z]\.?)?\s+[A-Z][a-z]+\s*(?:\(P\d{4,6}\)|P\d{4,6})",
        re.IGNORECASE),
}


def extract_entities(text: str) -> str:
    """Extract key entities from text. Returns pipe-delimited string."""
    entities = []
    for etype, pattern in ENTITY_PATTERNS.items():
        matches = pattern.findall(text[:5000])  # First 5000 chars
        if matches:
            unique = list(dict.fromkeys(m.strip() for m in matches[:10]))
            entities.extend(f"{etype}:{m}" for m in unique)
    return "|".join(entities[:30]) if entities else ""


# ---------------------------------------------------------------------------
# High-value detection
# ---------------------------------------------------------------------------
HIGH_VALUE_PATTERNS = re.compile(
    r"IT\s+IS\s+(HEREBY\s+)?ORDERED|COURT\s+ORDER|"
    r"INCIDENT\s+REPORT|OFFENSE\s+REPORT|NSPD|POLICE\s+REPORT|"
    r"FRIEND\s+OF\s+(?:THE\s+)?COURT|FOC\s+REPORT|FOC\s+RECOMMENDATION|"
    r"PSYCHOLOGICAL\s+EVALUATION|HEALTHWEST|"
    r"SUBPOENA|CONTEMPT|SHOW\s+CAUSE|"
    r"EX\s+PARTE|EMERGENCY|SUSPENSION|"
    r"PERSONAL\s+PROTECTION\s+ORDER|"
    r"JUDGMENT|OPINION\s+AND\s+ORDER|"
    r"PARENTING\s+TIME.*(?:SUSPEND|TERMINAT|DENY|RESTRICT)|"
    r"SOLE\s+(?:LEGAL|PHYSICAL)\s+CUSTODY|"
    r"INCARCERAT|JAIL|ARREST\s+WARRANT|"
    r"ALBERT\s+WATSON|RONALD?\s+BERRY|PAMELA\s+RUSCO",
    re.IGNORECASE
)


def is_high_value(text: str, doc_type: str) -> int:
    """Return 1 if document is high-value evidence, 0 otherwise."""
    if doc_type in ("court_order", "police_report", "foc_report",
                    "expert_eval", "subpoena"):
        return 1
    if HIGH_VALUE_PATTERNS.search(text[:8000]):
        return 1
    return 0


# ---------------------------------------------------------------------------
# PDF text extraction with pypdfium2
# ---------------------------------------------------------------------------
def extract_pdf_text(filepath: str, max_chars: int = 10000) -> tuple:
    """
    Extract text from PDF using pypdfium2.
    Returns (text, page_count, success_bool).
    """
    try:
        doc = pdfium.PdfDocument(filepath)
        page_count = len(doc)
        text_parts = []
        chars_so_far = 0
        for i in range(page_count):
            if chars_so_far >= max_chars:
                break
            try:
                page = doc[i]
                textpage = page.get_textpage()
                page_text = textpage.get_text_bounded()
                text_parts.append(page_text)
                chars_so_far += len(page_text)
                textpage.close()
                page.close()
            except Exception:
                text_parts.append(f"[PAGE {i+1} EXTRACTION ERROR]")
        doc.close()
        full_text = "\n".join(text_parts)
        return full_text[:max_chars], page_count, True
    except Exception as e:
        return f"[EXTRACTION FAILED: {e}]", 0, False


# ---------------------------------------------------------------------------
# Main pipeline
# ---------------------------------------------------------------------------
def main():
    start_time = time.time()
    print("=" * 70)
    print("  EMAIL PDF ATTACHMENT MINING — SINGULARITY EVIDENCE PIPELINE")
    print("=" * 70)

    # ---- Connect to DB ----
    conn = sqlite3.connect(DB_PATH, timeout=120)
    conn.execute("PRAGMA busy_timeout = 60000")
    conn.execute("PRAGMA journal_mode = WAL")
    conn.execute("PRAGMA cache_size = -32000")
    conn.execute("PRAGMA temp_store = MEMORY")
    conn.execute("PRAGMA synchronous = NORMAL")
    conn.row_factory = sqlite3.Row

    # ---- Verify email_attachments schema ----
    cols = {r[1] for r in conn.execute("PRAGMA table_info(email_attachments)")}
    print(f"\n[DB] email_attachments columns: {sorted(cols)}")

    # ---- Get PDF attachments ----
    pdf_rows = conn.execute("""
        SELECT attachment_id, email_id, original_filename, saved_path,
               file_size, mime_type, content_type, extracted_at
        FROM email_attachments
        WHERE (content_type LIKE '%pdf%' OR mime_type LIKE '%pdf%'
               OR saved_path LIKE '%.pdf')
          AND saved_path IS NOT NULL
    """).fetchall()
    total_pdfs = len(pdf_rows)
    print(f"[DB] Found {total_pdfs} PDF attachments to process")

    # ---- Build email metadata lookup (email_evidence table) ----
    # Join using attachment_names contains original_filename
    email_meta = {}
    try:
        ee_cols = {r[1] for r in conn.execute("PRAGMA table_info(email_evidence)")}
        if "attachment_names" in ee_cols:
            emails = conn.execute("""
                SELECT email_id, sender, date_sent, subject, attachment_names, lane
                FROM email_evidence
                WHERE has_attachment = 1
            """).fetchall()
            for em in emails:
                att_names = (em["attachment_names"] or "").split("|")
                for aname in att_names:
                    aname = aname.strip()
                    if aname:
                        key = aname.lower()
                        email_meta[key] = {
                            "sender": em["sender"] or "",
                            "email_date": em["date_sent"] or "",
                            "email_subject": em["subject"] or "",
                            "lane": em["lane"] or "",
                        }
            print(f"[DB] Built email metadata lookup: {len(email_meta)} attachment→email mappings")
    except Exception as e:
        print(f"[WARN] Could not build email metadata lookup: {e}")

    # ---- Create email_pdf_analysis table ----
    conn.execute("DROP TABLE IF EXISTS email_pdf_analysis")
    conn.execute("DROP TABLE IF EXISTS email_pdf_analysis_fts")
    conn.execute("""
        CREATE TABLE email_pdf_analysis (
            pdf_id INTEGER PRIMARY KEY AUTOINCREMENT,
            saved_path TEXT,
            filename TEXT,
            sender TEXT,
            email_subject TEXT,
            email_date TEXT,
            page_count INTEGER,
            file_size INTEGER,
            text_preview TEXT,
            lane TEXT,
            doc_type TEXT,
            high_value INTEGER DEFAULT 0,
            key_entities TEXT,
            created_at TEXT DEFAULT (datetime('now'))
        )
    """)
    conn.execute("""
        CREATE VIRTUAL TABLE IF NOT EXISTS email_pdf_analysis_fts
        USING fts5(
            filename, sender, email_subject, text_preview, lane, doc_type, key_entities,
            content='email_pdf_analysis',
            content_rowid='pdf_id',
            tokenize='porter unicode61'
        )
    """)
    conn.commit()
    print("[DB] Created email_pdf_analysis + FTS5 index")

    # ---- Process PDFs ----
    results = []
    errors = []
    batch_size = 500
    processed = 0
    skipped = 0

    for i, row in enumerate(pdf_rows):
        saved_path = row["saved_path"]
        filename = row["original_filename"] or os.path.basename(saved_path)
        file_size = row["file_size"] or 0

        # Progress
        if (i + 1) % 200 == 0 or i == 0:
            elapsed = time.time() - start_time
            rate = (i + 1) / elapsed if elapsed > 0 else 0
            print(f"  [{i+1}/{total_pdfs}] Processing... ({rate:.0f} PDFs/sec)")

        # Check file exists
        if not os.path.isfile(saved_path):
            skipped += 1
            continue

        # Get actual file size if not in DB
        if not file_size:
            try:
                file_size = os.path.getsize(saved_path)
            except OSError:
                file_size = 0

        # Extract text
        text, page_count, success = extract_pdf_text(saved_path, max_chars=10000)
        if not success:
            errors.append((filename, saved_path, str(text)))
            text_preview = text[:2000]
            lane = "U"
            doc_type = "unknown"
            high_val = 0
            entities = ""
        else:
            text_preview = text[:2000]
            # Classify
            lane = classify_lane(text)
            doc_type = classify_doc_type(text, filename)
            high_val = is_high_value(text, doc_type)
            entities = extract_entities(text)

        # Get email metadata
        fname_key = filename.lower().strip()
        meta = email_meta.get(fname_key, {})
        sender = meta.get("sender", "")
        email_subject = meta.get("email_subject", "")
        email_date = meta.get("email_date", "")

        # If no email meta found, try partial match
        if not sender:
            for mkey, mval in email_meta.items():
                # Strip date prefixes like "2025-10-10_"
                clean_fname = re.sub(r"^\d{4}-\d{2}-\d{2}_", "", fname_key)
                if clean_fname and clean_fname in mkey:
                    sender = mval.get("sender", "")
                    email_subject = mval.get("email_subject", "")
                    email_date = mval.get("email_date", "")
                    break
                elif mkey in fname_key:
                    sender = mval.get("sender", "")
                    email_subject = mval.get("email_subject", "")
                    email_date = mval.get("email_date", "")
                    break

        # If still no sender, try extracting from saved_path directory name
        if not sender:
            parts = Path(saved_path).parts
            for p in parts:
                if p not in ("J:\\", "LitigationOS_CENTRAL", "EMAIL_ATTACHMENTS", ""):
                    sender = p
                    break

        results.append((
            saved_path, filename, sender, email_subject, email_date,
            page_count, file_size, text_preview, lane, doc_type,
            high_val, entities
        ))
        processed += 1

        # Batch insert
        if len(results) >= batch_size:
            conn.executemany("""
                INSERT INTO email_pdf_analysis
                    (saved_path, filename, sender, email_subject, email_date,
                     page_count, file_size, text_preview, lane, doc_type,
                     high_value, key_entities)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, results)
            conn.commit()
            results = []

    # Final batch
    if results:
        conn.executemany("""
            INSERT INTO email_pdf_analysis
                (saved_path, filename, sender, email_subject, email_date,
                 page_count, file_size, text_preview, lane, doc_type,
                 high_value, key_entities)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, results)
        conn.commit()

    # ---- Populate FTS5 ----
    conn.execute("""
        INSERT INTO email_pdf_analysis_fts(rowid, filename, sender, email_subject,
            text_preview, lane, doc_type, key_entities)
        SELECT pdf_id, filename, sender, email_subject,
               text_preview, lane, doc_type, key_entities
        FROM email_pdf_analysis
    """)
    conn.commit()

    # ---- Create useful indexes ----
    conn.execute("CREATE INDEX IF NOT EXISTS idx_epa_lane ON email_pdf_analysis(lane)")
    conn.execute("CREATE INDEX IF NOT EXISTS idx_epa_doc_type ON email_pdf_analysis(doc_type)")
    conn.execute("CREATE INDEX IF NOT EXISTS idx_epa_high_value ON email_pdf_analysis(high_value)")
    conn.commit()

    # ---- Verify writes ----
    total_written = conn.execute("SELECT COUNT(*) FROM email_pdf_analysis").fetchone()[0]
    fts_count = conn.execute(
        "SELECT COUNT(*) FROM email_pdf_analysis_fts"
    ).fetchone()[0]
    print(f"\n[VERIFY] email_pdf_analysis: {total_written} rows")
    print(f"[VERIFY] FTS5 index: {fts_count} rows")

    # ---- Generate statistics ----
    print("\n" + "=" * 70)
    print("  MINING RESULTS SUMMARY")
    print("=" * 70)

    elapsed = time.time() - start_time
    print(f"\n  Total PDFs in DB: {total_pdfs}")
    print(f"  Successfully processed: {processed}")
    print(f"  Skipped (file not found): {skipped}")
    print(f"  Extraction errors: {len(errors)}")
    print(f"  Processing time: {elapsed:.1f}s ({processed/elapsed:.1f} PDFs/sec)")

    # Lane breakdown
    print("\n  --- PDFs per LANE ---")
    lane_stats = conn.execute("""
        SELECT lane, COUNT(*) as cnt,
               SUM(high_value) as hv,
               SUM(file_size) as total_bytes
        FROM email_pdf_analysis
        GROUP BY lane ORDER BY cnt DESC
    """).fetchall()
    lane_names = {"A": "Custody", "B": "Housing", "D": "PPO", "E": "Misconduct",
                  "F": "Appellate", "U": "Unclassified"}
    for r in lane_stats:
        mb = (r["total_bytes"] or 0) / 1048576
        name = lane_names.get(r["lane"], "Other")
        print(f"    Lane {r['lane']} ({name}): {r['cnt']} PDFs, "
              f"{r['hv']} high-value, {mb:.1f} MB")

    # Doc type breakdown
    print("\n  --- PDFs per DOC_TYPE ---")
    dtype_stats = conn.execute("""
        SELECT doc_type, COUNT(*) as cnt, SUM(high_value) as hv
        FROM email_pdf_analysis
        GROUP BY doc_type ORDER BY cnt DESC
    """).fetchall()
    for r in dtype_stats:
        print(f"    {r['doc_type']}: {r['cnt']} ({r['hv']} high-value)")

    # Top 20 high-value
    print("\n  --- TOP 20 HIGH-VALUE DOCUMENTS ---")
    top_hv = conn.execute("""
        SELECT pdf_id, filename, sender, email_subject, lane, doc_type,
               page_count, file_size, saved_path,
               substr(text_preview, 1, 300) as snippet
        FROM email_pdf_analysis
        WHERE high_value = 1
        ORDER BY
            CASE doc_type
                WHEN 'court_order' THEN 1
                WHEN 'police_report' THEN 2
                WHEN 'foc_report' THEN 3
                WHEN 'expert_eval' THEN 4
                WHEN 'subpoena' THEN 5
                ELSE 10
            END,
            file_size DESC
        LIMIT 20
    """).fetchall()
    for j, r in enumerate(top_hv, 1):
        kb = (r["file_size"] or 0) / 1024
        snip = (r["snippet"] or "").replace("\n", " ").strip()[:150]
        print(f"\n    #{j}  [{r['doc_type'].upper()}] Lane {r['lane']}")
        print(f"         File: {r['filename']}")
        print(f"         From: {r['sender']}")
        print(f"         Subj: {r['email_subject']}")
        print(f"         Pages: {r['page_count']}, Size: {kb:.0f} KB")
        print(f"         Path: {r['saved_path']}")
        print(f"         Text: {snip}...")

    # Court orders specifically
    print("\n  --- ALL COURT ORDERS (CRITICAL) ---")
    court_orders = conn.execute("""
        SELECT pdf_id, filename, sender, email_subject, email_date, lane,
               page_count, saved_path,
               substr(text_preview, 1, 400) as snippet
        FROM email_pdf_analysis
        WHERE doc_type = 'court_order'
        ORDER BY email_date DESC
    """).fetchall()
    print(f"    Found {len(court_orders)} court orders")
    for j, r in enumerate(court_orders[:30], 1):
        snip = (r["snippet"] or "").replace("\n", " ").strip()[:200]
        print(f"\n    {j}. [{r['lane']}] {r['filename']}")
        print(f"       Date: {r['email_date']} | From: {r['sender']}")
        print(f"       Subject: {r['email_subject']}")
        print(f"       Path: {r['saved_path']}")
        print(f"       Preview: {snip}")

    # Police reports
    print("\n  --- POLICE REPORTS ---")
    police = conn.execute("""
        SELECT pdf_id, filename, sender, email_subject, email_date, lane,
               saved_path, substr(text_preview, 1, 400) as snippet
        FROM email_pdf_analysis
        WHERE doc_type = 'police_report'
        ORDER BY email_date DESC
    """).fetchall()
    print(f"    Found {len(police)} police reports")
    for j, r in enumerate(police[:20], 1):
        snip = (r["snippet"] or "").replace("\n", " ").strip()[:200]
        print(f"\n    {j}. [{r['lane']}] {r['filename']}")
        print(f"       Date: {r['email_date']} | From: {r['sender']}")
        print(f"       Preview: {snip}")

    # FOC reports
    print("\n  --- FOC REPORTS / RECOMMENDATIONS ---")
    foc = conn.execute("""
        SELECT pdf_id, filename, sender, email_subject, email_date, lane,
               saved_path, substr(text_preview, 1, 400) as snippet
        FROM email_pdf_analysis
        WHERE doc_type = 'foc_report'
        ORDER BY email_date DESC
    """).fetchall()
    print(f"    Found {len(foc)} FOC reports")
    for j, r in enumerate(foc[:15], 1):
        snip = (r["snippet"] or "").replace("\n", " ").strip()[:200]
        print(f"\n    {j}. [{r['lane']}] {r['filename']}")
        print(f"       Date: {r['email_date']} | From: {r['sender']}")
        print(f"       Preview: {snip}")

    # Expert evaluations
    print("\n  --- EXPERT EVALUATIONS ---")
    expert = conn.execute("""
        SELECT pdf_id, filename, sender, email_subject, lane,
               saved_path, substr(text_preview, 1, 400) as snippet
        FROM email_pdf_analysis
        WHERE doc_type = 'expert_eval'
    """).fetchall()
    print(f"    Found {len(expert)} expert evaluations")
    for r in expert:
        snip = (r["snippet"] or "").replace("\n", " ").strip()[:200]
        print(f"    - [{r['lane']}] {r['filename']} (from {r['sender']})")
        print(f"      Preview: {snip}")

    # Motions
    print("\n  --- MOTIONS ---")
    motions_count = conn.execute(
        "SELECT COUNT(*) FROM email_pdf_analysis WHERE doc_type = 'motion'"
    ).fetchone()[0]
    print(f"    Found {motions_count} motions")

    # Subpoenas
    print("\n  --- SUBPOENAS ---")
    subpoenas = conn.execute("""
        SELECT filename, sender, saved_path, substr(text_preview, 1, 200) as snippet
        FROM email_pdf_analysis WHERE doc_type = 'subpoena'
    """).fetchall()
    print(f"    Found {len(subpoenas)} subpoenas")
    for r in subpoenas:
        print(f"    - {r['filename']} (from {r['sender']})")

    # ---- Generate Markdown Report ----
    print("\n\n  Generating report...")
    report_lines = []
    report_lines.append("# EMAIL PDF ATTACHMENT ANALYSIS REPORT")
    report_lines.append(f"\n**Generated:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    report_lines.append(f"**Source:** J:\\LitigationOS_CENTRAL\\EMAIL_ATTACHMENTS\\")
    report_lines.append(f"**Total PDFs Processed:** {processed}")
    report_lines.append(f"**Extraction Errors:** {len(errors)}")
    report_lines.append(f"**Skipped (file not found):** {skipped}")
    report_lines.append(f"**Processing Time:** {elapsed:.1f}s")

    report_lines.append("\n## Lane Distribution\n")
    report_lines.append("| Lane | Name | PDFs | High-Value | Size (MB) |")
    report_lines.append("|------|------|------|-----------|-----------|")
    for r in lane_stats:
        mb = (r["total_bytes"] or 0) / 1048576
        name = lane_names.get(r["lane"], "Other")
        report_lines.append(
            f"| {r['lane']} | {name} | {r['cnt']} | {r['hv']} | {mb:.1f} |")

    report_lines.append("\n## Document Type Distribution\n")
    report_lines.append("| Type | Count | High-Value |")
    report_lines.append("|------|-------|-----------|")
    for r in dtype_stats:
        report_lines.append(f"| {r['doc_type']} | {r['cnt']} | {r['hv']} |")

    report_lines.append("\n## Court Orders (CRITICAL EVIDENCE)\n")
    report_lines.append(f"**Total Court Orders Found: {len(court_orders)}**\n")
    for j, r in enumerate(court_orders[:30], 1):
        snip = (r["snippet"] or "").replace("\n", " ").strip()[:300]
        report_lines.append(f"### {j}. {r['filename']}")
        report_lines.append(f"- **Lane:** {r['lane']} | **Date:** {r['email_date']}")
        report_lines.append(f"- **From:** {r['sender']}")
        report_lines.append(f"- **Subject:** {r['email_subject']}")
        report_lines.append(f"- **Path:** `{r['saved_path']}`")
        report_lines.append(f"- **Preview:** {snip}\n")

    report_lines.append("\n## Police Reports\n")
    report_lines.append(f"**Total Police Reports Found: {len(police)}**\n")
    for j, r in enumerate(police[:20], 1):
        snip = (r["snippet"] or "").replace("\n", " ").strip()[:300]
        report_lines.append(f"### {j}. {r['filename']}")
        report_lines.append(f"- **Lane:** {r['lane']} | **Date:** {r['email_date']}")
        report_lines.append(f"- **From:** {r['sender']}")
        report_lines.append(f"- **Path:** `{r['saved_path']}`")
        report_lines.append(f"- **Preview:** {snip}\n")

    report_lines.append("\n## FOC Reports / Recommendations\n")
    report_lines.append(f"**Total FOC Reports Found: {len(foc)}**\n")
    for j, r in enumerate(foc[:15], 1):
        snip = (r["snippet"] or "").replace("\n", " ").strip()[:300]
        report_lines.append(f"### {j}. {r['filename']}")
        report_lines.append(f"- **Lane:** {r['lane']} | **Date:** {r['email_date']}")
        report_lines.append(f"- **From:** {r['sender']}")
        report_lines.append(f"- **Path:** `{r['saved_path']}`")
        report_lines.append(f"- **Preview:** {snip}\n")

    report_lines.append("\n## Expert Evaluations\n")
    report_lines.append(f"**Total Expert Evaluations Found: {len(expert)}**\n")
    for r in expert:
        snip = (r["snippet"] or "").replace("\n", " ").strip()[:300]
        report_lines.append(f"- **{r['filename']}** (Lane {r['lane']}, from {r['sender']})")
        report_lines.append(f"  - Path: `{r['saved_path']}`")
        report_lines.append(f"  - Preview: {snip}\n")

    report_lines.append("\n## Top 20 High-Value Documents\n")
    report_lines.append("| # | Type | Lane | Filename | Sender | Pages | Size |")
    report_lines.append("|---|------|------|----------|--------|-------|------|")
    for j, r in enumerate(top_hv, 1):
        kb = (r["file_size"] or 0) / 1024
        report_lines.append(
            f"| {j} | {r['doc_type']} | {r['lane']} | "
            f"{r['filename'][:40]} | {r['sender'][:25]} | "
            f"{r['page_count']} | {kb:.0f}KB |")

    if errors:
        report_lines.append(f"\n## Extraction Errors ({len(errors)})\n")
        for fname, path, err in errors[:30]:
            report_lines.append(f"- **{fname}**: {err[:100]}")

    report_lines.append("\n---")
    report_lines.append(f"\n*Report generated by mine_email_pdfs.py at "
                        f"{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}*")

    # Write report
    os.makedirs(os.path.dirname(REPORT_PATH), exist_ok=True)
    with open(REPORT_PATH, "w", encoding="utf-8") as f:
        f.write("\n".join(report_lines))
    print(f"\n  [SAVED] Report: {REPORT_PATH}")

    conn.close()
    print(f"\n  COMPLETE. {processed} PDFs mined in {elapsed:.1f}s.")
    print("=" * 70)


if __name__ == "__main__":
    main()
