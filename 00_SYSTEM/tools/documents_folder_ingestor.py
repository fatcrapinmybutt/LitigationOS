#!/usr/bin/env python3
"""Tool #267: Documents Folder Ingestor
Ingests key evidence files from C:\\Users\\andre\\Documents\\ into litigation_context.db.
Targets: D000xxx.txt docket entries, CSV structured data, federal complaint draft,
Watson context trail.
"""
import sys, os, json, sqlite3, csv, re, glob
from datetime import datetime

sys.stdout = open(sys.stdout.fileno(), mode='w', encoding='utf-8', errors='replace')

def s(v):
    return (v or "").lower()

def safe_query(conn, sql, params=()):
    try:
        return conn.execute(sql, params).fetchall()
    except:
        return []

DOCS_DIR = r"C:\Users\andre\Documents"

DATE_RE = re.compile(r'(\d{1,2}[/-]\d{1,2}[/-]\d{2,4})')
CASE_RE = re.compile(r'(\d{4}-\d{6}-[A-Z]{2})')


def parse_date_from_text(text):
    m = DATE_RE.search(text)
    return m.group(1) if m else None


def parse_case_number(text):
    m = CASE_RE.search(text)
    return m.group(1) if m else None


def classify_entry_type(text):
    tl = s(text)
    if "order" in tl:
        return "order"
    if "motion" in tl:
        return "motion"
    if "hearing" in tl:
        return "hearing"
    if "judgment" in tl:
        return "judgment"
    if "petition" in tl:
        return "petition"
    if "affidavit" in tl:
        return "affidavit"
    if "notice" in tl:
        return "notice"
    if "stipulation" in tl:
        return "stipulation"
    return "docket_entry"


def create_table_from_csv(conn, table_name, headers):
    cols = []
    for h in headers:
        col = re.sub(r'[^a-zA-Z0-9_]', '_', h.strip()).strip('_').lower()
        if not col:
            col = f"col_{len(cols)}"
        cols.append(col)
    col_defs = ", ".join(f'"{c}" TEXT' for c in cols)
    conn.execute(f"""CREATE TABLE IF NOT EXISTS "{table_name}" (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        {col_defs},
        source_file TEXT,
        scan_date TEXT
    )""")
    return cols


def ingest_csv_file(conn, filepath, table_name, scan_date):
    rows_added = 0
    try:
        with open(filepath, 'r', encoding='utf-8', errors='replace') as f:
            reader = csv.reader(f)
            headers = next(reader, None)
            if not headers:
                return 0, "No headers found"
            cols = create_table_from_csv(conn, table_name, headers)
            placeholders = ", ".join(["?"] * (len(cols) + 2))
            col_names = ", ".join(f'"{c}"' for c in cols) + ", source_file, scan_date"
            batch = []
            for row in reader:
                padded = list(row) + [""] * max(0, len(cols) - len(row))
                padded = padded[:len(cols)]
                padded.extend([os.path.basename(filepath), scan_date])
                batch.append(tuple(padded))
                if len(batch) >= 500:
                    conn.executemany(f'INSERT INTO "{table_name}" ({col_names}) VALUES ({placeholders})', batch)
                    rows_added += len(batch)
                    batch = []
            if batch:
                conn.executemany(f'INSERT INTO "{table_name}" ({col_names}) VALUES ({placeholders})', batch)
                rows_added += len(batch)
            conn.commit()
            return rows_added, None
    except Exception as e:
        return rows_added, str(e)


def main():
    db_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', 'litigation_context.db')
    report_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'reports')
    os.makedirs(report_dir, exist_ok=True)

    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA busy_timeout=60000")
    conn.execute("PRAGMA cache_size=-32000")

    print("=" * 70)
    print("TOOL #267: DOCUMENTS FOLDER INGESTOR")
    print("=" * 70)

    scan_date = datetime.now().isoformat()
    results = {
        "tool": "#267 Documents Folder Ingestor",
        "generated": scan_date,
        "source_dir": DOCS_DIR,
        "sections": {}
    }
    total_rows = 0

    # ── 1. D000xxx.txt docket entries ──
    print("\n[1/4] Ingesting D000xxx.txt docket entries...")
    conn.execute("""CREATE TABLE IF NOT EXISTS documents_docket_entries (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        filename TEXT,
        file_path TEXT,
        docket_number TEXT,
        entry_text TEXT,
        entry_date TEXT,
        case_number TEXT,
        entry_type TEXT,
        scan_date TEXT
    )""")

    docket_files = sorted(glob.glob(os.path.join(DOCS_DIR, "D000*.txt")))
    docket_count = 0
    docket_errors = []
    docket_samples = []
    for fp in docket_files:
        try:
            with open(fp, 'r', encoding='utf-8', errors='replace') as f:
                text = f.read()
            fname = os.path.basename(fp)
            docket_num_match = re.match(r'(D\d+)', fname)
            docket_num = docket_num_match.group(1) if docket_num_match else fname.replace('.txt', '')
            entry_date = parse_date_from_text(text)
            case_number = parse_case_number(text)
            entry_type = classify_entry_type(text)

            conn.execute("""INSERT INTO documents_docket_entries
                (filename, file_path, docket_number, entry_text, entry_date, case_number, entry_type, scan_date)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
                (fname, fp, docket_num, text, entry_date, case_number, entry_type, scan_date))
            docket_count += 1
            if len(docket_samples) < 3:
                docket_samples.append({
                    "file": fname, "docket_number": docket_num,
                    "entry_type": entry_type, "case_number": case_number,
                    "text_preview": text[:200]
                })
        except Exception as e:
            docket_errors.append(f"{os.path.basename(fp)}: {e}")
    conn.commit()
    total_rows += docket_count
    results["sections"]["docket_entries"] = {
        "files_found": len(docket_files),
        "rows_ingested": docket_count,
        "errors": docket_errors,
        "samples": docket_samples
    }
    print(f"  Found {len(docket_files)} D000*.txt files, ingested {docket_count} entries")

    # ── 2. CSV files ──
    print("\n[2/4] Ingesting CSV files...")
    csv_targets = {
        "ACCUSATION_CANDIDATES_ALL.csv": "accusation_candidates",
        "Benchbook_Violation_Findings(1).csv": "benchbook_violations_import",
        "CONTRADICTION_MAP_PERMAFIX9R12.csv": "contradiction_map_import",
        "CLAIM_CLUSTERS_v2.csv": "claim_clusters_import",
    }
    csv_results = {}
    for csv_name, table_name in csv_targets.items():
        csv_path = os.path.join(DOCS_DIR, csv_name)
        if os.path.exists(csv_path):
            rows, err = ingest_csv_file(conn, csv_path, table_name, scan_date)
            total_rows += rows
            csv_results[csv_name] = {"table": table_name, "rows": rows, "error": err}
            status = f"{rows} rows" + (f" (ERROR: {err})" if err else "")
            print(f"  {csv_name} → {table_name}: {status}")
        else:
            csv_results[csv_name] = {"table": table_name, "rows": 0, "error": "File not found"}
            print(f"  {csv_name}: NOT FOUND")
    results["sections"]["csv_files"] = csv_results

    # ── 3. Federal complaint draft ──
    print("\n[3/4] Ingesting 07_USDC_Section_1983_Complaint.txt...")
    conn.execute("""CREATE TABLE IF NOT EXISTS federal_complaint_drafts (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        title TEXT,
        file_path TEXT,
        full_text TEXT,
        version TEXT,
        parties TEXT,
        claims TEXT,
        scan_date TEXT
    )""")

    complaint_path = os.path.join(DOCS_DIR, "07_USDC_Section_1983_Complaint.txt")
    complaint_result = {}
    if os.path.exists(complaint_path):
        try:
            with open(complaint_path, 'r', encoding='utf-8', errors='replace') as f:
                text = f.read()
            parties = "Pigors v. Watson" if "pigors" in s(text) or "watson" in s(text) else "[UNKNOWN — VERIFY]"
            claims_found = []
            for pat in [r'§\s*1983', r'section 1983', r'due process', r'equal protection',
                        r'14th amendment', r'42 U\.S\.C']:
                if re.search(pat, text, re.IGNORECASE):
                    claims_found.append(pat.replace(r'\s*', ' ').replace('\\', ''))
            conn.execute("""INSERT INTO federal_complaint_drafts
                (title, file_path, full_text, version, parties, claims, scan_date)
                VALUES (?, ?, ?, ?, ?, ?, ?)""",
                ("USDC Section 1983 Complaint", complaint_path, text,
                 "v1_documents_import", parties, ", ".join(claims_found), scan_date))
            conn.commit()
            total_rows += 1
            complaint_result = {
                "status": "ingested", "size": len(text),
                "parties": parties, "claims": claims_found
            }
            print(f"  Ingested: {len(text):,} chars, parties={parties}, claims={len(claims_found)}")
        except Exception as e:
            complaint_result = {"status": "error", "error": str(e)}
            print(f"  ERROR: {e}")
    else:
        complaint_result = {"status": "not_found"}
        print("  NOT FOUND")
    results["sections"]["federal_complaint"] = complaint_result

    # ── 4. Watson Context Trail ──
    print("\n[4/4] Ingesting WATSON_CONTEXT_TRAIL(5).txt...")
    conn.execute("""CREATE TABLE IF NOT EXISTS case_context_documents (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        title TEXT,
        file_path TEXT,
        full_text TEXT,
        document_type TEXT,
        version TEXT,
        scan_date TEXT
    )""")

    context_trail_path = os.path.join(DOCS_DIR, "WATSON_CONTEXT_TRAIL(5).txt")
    context_result = {}
    if os.path.exists(context_trail_path):
        try:
            with open(context_trail_path, 'r', encoding='utf-8', errors='replace') as f:
                text = f.read()
            conn.execute("""INSERT INTO case_context_documents
                (title, file_path, full_text, document_type, version, scan_date)
                VALUES (?, ?, ?, ?, ?, ?)""",
                ("Watson Context Trail", context_trail_path, text,
                 "context_trail", "v5", scan_date))
            conn.commit()
            total_rows += 1
            context_result = {"status": "ingested", "size": len(text)}
            print(f"  Ingested: {len(text):,} chars")
        except Exception as e:
            context_result = {"status": "error", "error": str(e)}
            print(f"  ERROR: {e}")
    else:
        context_result = {"status": "not_found"}
        print("  NOT FOUND")
    results["sections"]["watson_context_trail"] = context_result

    # ── Summary ──
    results["total_rows_added"] = total_rows
    print("\n" + "=" * 70)
    print(f"TOTAL ROWS ADDED: {total_rows}")
    print("=" * 70)

    # ── Write reports ──
    md_lines = [
        "# Tool #267: Documents Folder Ingestor Report",
        f"**Generated:** {scan_date}",
        f"**Source:** `{DOCS_DIR}`",
        f"**Total Rows Added:** {total_rows}",
        "",
        "## Docket Entries (D000xxx.txt)",
        f"- Files found: {results['sections']['docket_entries']['files_found']}",
        f"- Rows ingested: {results['sections']['docket_entries']['rows_ingested']}",
    ]
    if docket_errors:
        md_lines.append(f"- Errors: {len(docket_errors)}")
    for samp in docket_samples:
        md_lines.append(f"  - `{samp['file']}`: {samp['entry_type']} | case={samp['case_number']} | {samp['text_preview'][:80]}...")

    md_lines.append("\n## CSV Files")
    for csv_name, info in csv_results.items():
        status = f"{info['rows']} rows" if info['rows'] else info.get('error', 'skipped')
        md_lines.append(f"- **{csv_name}** → `{info['table']}`: {status}")

    md_lines.append("\n## Federal Complaint Draft")
    md_lines.append(f"- Status: {complaint_result.get('status', 'unknown')}")
    if complaint_result.get('size'):
        md_lines.append(f"- Size: {complaint_result['size']:,} chars")

    md_lines.append("\n## Watson Context Trail")
    md_lines.append(f"- Status: {context_result.get('status', 'unknown')}")
    if context_result.get('size'):
        md_lines.append(f"- Size: {context_result['size']:,} chars")

    md_path = os.path.join(report_dir, "tool_267_documents_folder_ingest.md")
    json_path = os.path.join(report_dir, "tool_267_documents_folder_ingest.json")
    with open(md_path, 'w', encoding='utf-8') as f:
        f.write("\n".join(md_lines))
    with open(json_path, 'w', encoding='utf-8') as f:
        json.dump(results, f, indent=2, default=str)
    print(f"\nReports: {md_path}")
    print(f"         {json_path}")

    conn.close()


if __name__ == "__main__":
    main()
