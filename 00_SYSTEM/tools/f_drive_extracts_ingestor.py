#!/usr/bin/env python3
"""Tool #268: F Drive Extracts Ingestor
Ingests high-value extracted evidence from F:\\extracts\\ and key F:\\ root files
into litigation_context.db.
"""
import sys, os, json, sqlite3, csv, glob
from datetime import datetime

sys.stdout = open(sys.stdout.fileno(), mode='w', encoding='utf-8', errors='replace')

def s(v):
    return (v or "").lower()

def safe_query(conn, sql, params=()):
    try:
        return conn.execute(sql, params).fetchall()
    except:
        return []

MAX_TEXT_SIZE = 2 * 1024 * 1024  # 2MB cap for very large text files

EXTRACT_DIRS = [
    "cross_exam_questions",
    "custody_docket",
    "custody_judgment_OCR",
    "emily_exparte_motion",
    "exparte_objection_order",
    "judge_response",
]

EXTRACT_LANE_MAP = {
    "cross_exam_questions": ("A", "cross_examination"),
    "custody_docket": ("A", "docket"),
    "custody_judgment_OCR": ("A", "judgment"),
    "emily_exparte_motion": ("A", "motion"),
    "exparte_objection_order": ("A", "order"),
    "judge_response": ("E", "judicial_response"),
}

# PERMAFIX base files — only ingest the originals, not (1), (2) duplicates
PERMAFIX_TARGETS = {
    "PERMAFIX9R13_20260214_203353_QUOTE_DB.csv": "permafix_quote_db",
    "PERMAFIX9R13_20260214_203353_STATEMENT_CONTRADICTION_GRID.csv": "permafix_contradiction_grid",
    "PERMAFIX9R13_20260214_203353_DOC_RECORDS.csv": "permafix_doc_records",
    "PERMAFIX9R13_20260214_203353_OPERATING_ORDERS_PIN.csv": "permafix_operating_orders",
}


def create_csv_table(conn, table_name, headers):
    import re as _re
    cols = []
    for h in headers:
        col = _re.sub(r'[^a-zA-Z0-9_]', '_', h.strip()).strip('_').lower()
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


def ingest_csv(conn, filepath, table_name, scan_date):
    rows_added = 0
    try:
        with open(filepath, 'r', encoding='utf-8', errors='replace') as f:
            reader = csv.reader(f)
            headers = next(reader, None)
            if not headers:
                return 0, "No headers"
            cols = create_csv_table(conn, table_name, headers)
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


def read_file_capped(filepath, max_size=MAX_TEXT_SIZE):
    size = os.path.getsize(filepath)
    with open(filepath, 'r', encoding='utf-8', errors='replace') as f:
        text = f.read(max_size)
    if size > max_size:
        text += f"\n\n[TRUNCATED — file is {size:,} bytes, read first {max_size:,}]"
    return text, size


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
    print("TOOL #268: F DRIVE EXTRACTS INGESTOR")
    print("=" * 70)

    scan_date = datetime.now().isoformat()
    results = {
        "tool": "#268 F Drive Extracts Ingestor",
        "generated": scan_date,
        "sections": {}
    }
    total_rows = 0
    all_errors = []

    # ── 1. F:\extracts\ directories ──
    print("\n[1/3] Ingesting F:\\extracts\\ directories...")
    conn.execute("""CREATE TABLE IF NOT EXISTS f_drive_extracts (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        extract_folder TEXT,
        filename TEXT,
        file_path TEXT,
        content TEXT,
        content_length INTEGER,
        case_lane TEXT,
        evidence_type TEXT,
        scan_date TEXT
    )""")

    extract_stats = {}
    for folder_name in EXTRACT_DIRS:
        folder_path = os.path.join(r"F:\extracts", folder_name)
        lane, etype = EXTRACT_LANE_MAP.get(folder_name, ("", "unknown"))
        files_found = []
        if os.path.isdir(folder_path):
            for ext in ("*.txt", "*.md", "*.csv", "*.json"):
                files_found.extend(glob.glob(os.path.join(folder_path, ext)))
        count = 0
        for fp in files_found:
            try:
                text, size = read_file_capped(fp)
                conn.execute("""INSERT INTO f_drive_extracts
                    (extract_folder, filename, file_path, content, content_length,
                     case_lane, evidence_type, scan_date)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
                    (folder_name, os.path.basename(fp), fp, text, size,
                     lane, etype, scan_date))
                count += 1
            except Exception as e:
                all_errors.append(f"{folder_name}/{os.path.basename(fp)}: {e}")
        conn.commit()
        total_rows += count
        extract_stats[folder_name] = {"files_found": len(files_found), "ingested": count}
        print(f"  {folder_name}: {len(files_found)} files found, {count} ingested")
    results["sections"]["extracts"] = extract_stats

    # ── 2. F:\ root key files ──
    print("\n[2/3] Ingesting F:\\ root key files...")
    root_stats = {}

    # 2a. CLAIMS.json
    claims_path = r"F:\CLAIMS.json"
    if os.path.exists(claims_path):
        try:
            with open(claims_path, 'r', encoding='utf-8', errors='replace') as f:
                claims_data = json.load(f)
            conn.execute("""CREATE TABLE IF NOT EXISTS f_drive_claims (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                claim_key TEXT,
                claim_data TEXT,
                source_file TEXT,
                scan_date TEXT
            )""")
            if isinstance(claims_data, list):
                batch = [(json.dumps(item), json.dumps(item), claims_path, scan_date) for item in claims_data]
                conn.executemany("INSERT INTO f_drive_claims (claim_key, claim_data, source_file, scan_date) VALUES (?, ?, ?, ?)", batch)
                count = len(batch)
            elif isinstance(claims_data, dict):
                batch = [(k, json.dumps(v), claims_path, scan_date) for k, v in claims_data.items()]
                conn.executemany("INSERT INTO f_drive_claims (claim_key, claim_data, source_file, scan_date) VALUES (?, ?, ?, ?)", batch)
                count = len(batch)
            else:
                conn.execute("INSERT INTO f_drive_claims (claim_key, claim_data, source_file, scan_date) VALUES (?, ?, ?, ?)",
                    ("full_content", json.dumps(claims_data), claims_path, scan_date))
                count = 1
            conn.commit()
            total_rows += count
            root_stats["CLAIMS.json"] = {"rows": count}
            print(f"  CLAIMS.json: {count} entries")
        except Exception as e:
            root_stats["CLAIMS.json"] = {"error": str(e)}
            all_errors.append(f"CLAIMS.json: {e}")
            print(f"  CLAIMS.json: ERROR — {e}")
    else:
        root_stats["CLAIMS.json"] = {"error": "not_found"}
        print("  CLAIMS.json: NOT FOUND")

    # 2b-2d. CSV root files
    csv_root_files = {
        r"F:\REFUTATION_MATRIX.csv": "f_drive_refutation_matrix",
        r"F:\EXHIBIT_MATRIX_FULL.csv": "f_drive_exhibit_matrix",
        r"F:\deadlines.csv": "f_drive_deadlines",
    }
    for csv_path, table_name in csv_root_files.items():
        fname = os.path.basename(csv_path)
        if os.path.exists(csv_path):
            rows, err = ingest_csv(conn, csv_path, table_name, scan_date)
            total_rows += rows
            root_stats[fname] = {"table": table_name, "rows": rows, "error": err}
            status = f"{rows} rows" + (f" (ERROR: {err})" if err else "")
            print(f"  {fname} → {table_name}: {status}")
        else:
            root_stats[fname] = {"error": "not_found"}
            print(f"  {fname}: NOT FOUND")

    # 2e. Circuit court docket text
    docket_txt_path = r"F:\circuit court docket mcneill custody.txt"
    conn.execute("""CREATE TABLE IF NOT EXISTS f_drive_docket_text (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        title TEXT,
        file_path TEXT,
        full_text TEXT,
        case_number TEXT,
        scan_date TEXT
    )""")
    if os.path.exists(docket_txt_path):
        try:
            text, size = read_file_capped(docket_txt_path)
            import re
            case_match = re.search(r'(\d{4}-\d{6}-[A-Z]{2})', text)
            case_num = case_match.group(1) if case_match else "2024-001507-DC"
            conn.execute("""INSERT INTO f_drive_docket_text
                (title, file_path, full_text, case_number, scan_date)
                VALUES (?, ?, ?, ?, ?)""",
                ("Circuit Court Docket — McNeill Custody", docket_txt_path, text, case_num, scan_date))
            conn.commit()
            total_rows += 1
            root_stats["circuit_court_docket.txt"] = {"size": size, "case_number": case_num}
            print(f"  circuit court docket: {size:,} bytes, case={case_num}")
        except Exception as e:
            root_stats["circuit_court_docket.txt"] = {"error": str(e)}
            all_errors.append(f"circuit court docket: {e}")
            print(f"  circuit court docket: ERROR — {e}")
    else:
        root_stats["circuit_court_docket.txt"] = {"error": "not_found"}
        print("  circuit court docket: NOT FOUND")

    # 2f. KNOWLEDGE_ALL.md
    conn.execute("""CREATE TABLE IF NOT EXISTS f_drive_knowledge (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        title TEXT,
        file_path TEXT,
        full_text TEXT,
        content_length INTEGER,
        scan_date TEXT
    )""")
    knowledge_path = r"F:\KNOWLEDGE_ALL.md"
    if os.path.exists(knowledge_path):
        try:
            text, size = read_file_capped(knowledge_path)
            conn.execute("""INSERT INTO f_drive_knowledge
                (title, file_path, full_text, content_length, scan_date)
                VALUES (?, ?, ?, ?, ?)""",
                ("KNOWLEDGE_ALL", knowledge_path, text, size, scan_date))
            conn.commit()
            total_rows += 1
            root_stats["KNOWLEDGE_ALL.md"] = {"size": size}
            print(f"  KNOWLEDGE_ALL.md: {size:,} bytes")
        except Exception as e:
            root_stats["KNOWLEDGE_ALL.md"] = {"error": str(e)}
            all_errors.append(f"KNOWLEDGE_ALL.md: {e}")
            print(f"  KNOWLEDGE_ALL.md: ERROR — {e}")
    else:
        root_stats["KNOWLEDGE_ALL.md"] = {"error": "not_found"}
        print("  KNOWLEDGE_ALL.md: NOT FOUND")

    results["sections"]["root_files"] = root_stats

    # ── 3. PERMAFIX files ──
    print("\n[3/3] Ingesting PERMAFIX files...")
    permafix_stats = {}
    for perma_file, table_name in PERMAFIX_TARGETS.items():
        perma_path = os.path.join("F:\\", perma_file)
        if os.path.exists(perma_path):
            rows, err = ingest_csv(conn, perma_path, table_name, scan_date)
            total_rows += rows
            permafix_stats[perma_file] = {"table": table_name, "rows": rows, "error": err}
            status = f"{rows} rows" + (f" (ERROR: {err})" if err else "")
            print(f"  {perma_file} → {table_name}: {status}")
        else:
            permafix_stats[perma_file] = {"error": "not_found"}
            print(f"  {perma_file}: NOT FOUND")
    results["sections"]["permafix"] = permafix_stats

    # ── Summary ──
    results["total_rows_added"] = total_rows
    results["errors"] = all_errors
    print("\n" + "=" * 70)
    print(f"TOTAL ROWS ADDED: {total_rows}")
    if all_errors:
        print(f"ERRORS: {len(all_errors)}")
    print("=" * 70)

    # ── Reports ──
    md_lines = [
        "# Tool #268: F Drive Extracts Ingestor Report",
        f"**Generated:** {scan_date}",
        f"**Total Rows Added:** {total_rows}",
        "",
        "## Extract Directories (F:\\extracts\\)",
    ]
    for folder, stats in extract_stats.items():
        md_lines.append(f"- **{folder}**: {stats['files_found']} files → {stats['ingested']} ingested")

    md_lines.append("\n## Root Files (F:\\)")
    for fname, info in root_stats.items():
        if "error" in info and info["error"] != "not_found":
            md_lines.append(f"- **{fname}**: ERROR — {info['error']}")
        elif info.get("error") == "not_found":
            md_lines.append(f"- **{fname}**: Not found")
        elif "rows" in info:
            md_lines.append(f"- **{fname}**: {info['rows']} rows → `{info.get('table', '')}`")
        elif "size" in info:
            md_lines.append(f"- **{fname}**: {info['size']:,} bytes")

    md_lines.append("\n## PERMAFIX Files")
    for fname, info in permafix_stats.items():
        if info.get("error") == "not_found":
            md_lines.append(f"- **{fname}**: Not found")
        elif info.get("error"):
            md_lines.append(f"- **{fname}**: ERROR — {info['error']}")
        else:
            md_lines.append(f"- **{fname}** → `{info['table']}`: {info['rows']} rows")

    if all_errors:
        md_lines.append(f"\n## Errors ({len(all_errors)})")
        for e in all_errors[:20]:
            md_lines.append(f"- {e}")

    md_path = os.path.join(report_dir, "tool_268_f_drive_extracts_ingest.md")
    json_path = os.path.join(report_dir, "tool_268_f_drive_extracts_ingest.json")
    with open(md_path, 'w', encoding='utf-8') as f:
        f.write("\n".join(md_lines))
    with open(json_path, 'w', encoding='utf-8') as f:
        json.dump(results, f, indent=2, default=str)
    print(f"\nReports: {md_path}")
    print(f"         {json_path}")

    conn.close()


if __name__ == "__main__":
    main()
