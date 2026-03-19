#!/usr/bin/env python3
"""
Tool #222 — D: Drive Evidence Ingester
========================================
Catalogs and summarizes D:\\ drive evidence for integration into litigation_context.db.

Scans:
  - D:\\LitigationOS_Extracted\\ — HealthWest files
  - D:\\LitigationOS_Extracted\\evidence_zips\\ — 6,783 files
  - D:\\LITIGATIONOS_DATA\\ — legal strategy docs
  - D:\\LitigationOS_DB_Archive\\ — archived databases

For each directory: file counts by extension, total size, key files.
Reads CSV headers from known files.
Identifies high-priority files not yet in litigation_context.db.
Creates integration manifest.

Output: D_DRIVE_EVIDENCE_CATALOG.md + d_drive_evidence_catalog.json
"""
import sys
import os
import json
import sqlite3
import csv
from datetime import datetime
from collections import defaultdict

sys.stdout = open(sys.stdout.fileno(), mode='w', encoding='utf-8', errors='replace')

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.normpath(os.path.join(SCRIPT_DIR, '..', '..'))
DB_PATH = os.path.join(REPO, 'litigation_context.db')
REPORTS_DIR = os.path.join(REPO, '00_SYSTEM', 'reports')

SCAN_PATHS = [
    r"D:\LitigationOS_Extracted",
    r"D:\LitigationOS_Extracted\evidence_zips",
    r"D:\LITIGATIONOS_DATA",
    r"D:\LitigationOS_DB_Archive",
]

# CSVs to inspect headers
CSV_TARGETS = [
    "REBUTTAL_PACK.csv",
    "CIP.csv",
    "COE.csv",
]

# High-priority file patterns (evidence, filings, court docs)
HIGH_PRIORITY_EXTENSIONS = {'.pdf', '.docx', '.doc', '.txt', '.csv', '.xlsx', '.db', '.sqlite'}
HIGH_PRIORITY_KEYWORDS = [
    'healthwest', 'delusional', 'eval', 'custody', 'parenting', 'ppo',
    'motion', 'brief', 'affidavit', 'order', 'subpoena', 'evidence',
    'mcneill', 'watson', 'pigors', 'rusco', 'barnes', 'berry',
    'rebuttal', 'exhibit', 'docket', 'complaint', 'appeal',
]


def get_connection():
    conn = sqlite3.connect(DB_PATH, timeout=120)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA busy_timeout=60000")
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA cache_size=-32000")
    conn.execute("PRAGMA temp_store=MEMORY")
    conn.execute("PRAGMA synchronous=NORMAL")
    return conn


def safe_query(conn, sql, params=()):
    try:
        rows = conn.execute(sql, params).fetchall()
        return [dict(r) for r in rows]
    except Exception:
        return []


def format_size(size_bytes):
    """Format bytes into human-readable string."""
    for unit in ['B', 'KB', 'MB', 'GB']:
        if size_bytes < 1024:
            return f"{size_bytes:.1f} {unit}"
        size_bytes /= 1024
    return f"{size_bytes:.1f} TB"


def scan_directory(dirpath):
    """Scan a directory and return detailed stats."""
    result = {
        "path": dirpath,
        "exists": os.path.exists(dirpath),
        "total_files": 0,
        "total_size_bytes": 0,
        "total_size_human": "0 B",
        "subdirectories": 0,
        "extensions": {},
        "key_files": [],
        "high_priority_files": [],
    }

    if not result["exists"]:
        return result

    ext_counts = defaultdict(lambda: {"count": 0, "size": 0})
    all_files = []

    try:
        for root, dirs, files in os.walk(dirpath):
            result["subdirectories"] += len(dirs)
            for fname in files:
                fpath = os.path.join(root, fname)
                try:
                    fsize = os.path.getsize(fpath)
                except OSError:
                    fsize = 0

                result["total_files"] += 1
                result["total_size_bytes"] += fsize

                ext = os.path.splitext(fname)[1].lower() or '(no ext)'
                ext_counts[ext]["count"] += 1
                ext_counts[ext]["size"] += fsize

                all_files.append({
                    "name": fname,
                    "path": fpath,
                    "size": fsize,
                    "ext": ext,
                })

                # Check high priority
                fname_lower = fname.lower()
                is_hp_ext = ext in HIGH_PRIORITY_EXTENSIONS
                is_hp_keyword = any(kw in fname_lower for kw in HIGH_PRIORITY_KEYWORDS)

                if is_hp_ext and (is_hp_keyword or fsize > 100_000):
                    result["high_priority_files"].append({
                        "name": fname,
                        "path": fpath,
                        "size": fsize,
                        "size_human": format_size(fsize),
                        "keyword_match": is_hp_keyword,
                    })
    except PermissionError as e:
        result["error"] = f"Permission denied: {e}"
    except Exception as e:
        result["error"] = f"Scan error: {e}"

    result["total_size_human"] = format_size(result["total_size_bytes"])
    result["extensions"] = {
        ext: {"count": d["count"], "size": d["size"], "size_human": format_size(d["size"])}
        for ext, d in sorted(ext_counts.items(), key=lambda x: x[1]["count"], reverse=True)
    }

    # Top 20 key files by size
    all_files.sort(key=lambda x: x['size'], reverse=True)
    result["key_files"] = [
        {"name": f["name"], "size": f["size"], "size_human": format_size(f["size"]), "path": f["path"]}
        for f in all_files[:20]
    ]

    # Limit high priority to top 50
    result["high_priority_files"] = sorted(
        result["high_priority_files"], key=lambda x: x['size'], reverse=True
    )[:50]

    return result


def read_csv_headers(base_dirs):
    """Find and read headers from target CSVs."""
    csv_results = {}
    for csv_name in CSV_TARGETS:
        csv_results[csv_name] = {"found": False, "path": None, "headers": [], "row_count": 0}
        for base in base_dirs:
            if not os.path.exists(base):
                continue
            for root, _, files in os.walk(base):
                if csv_name in files:
                    fpath = os.path.join(root, csv_name)
                    csv_results[csv_name]["found"] = True
                    csv_results[csv_name]["path"] = fpath
                    try:
                        with open(fpath, 'r', encoding='utf-8', errors='replace') as f:
                            reader = csv.reader(f)
                            headers = next(reader, [])
                            csv_results[csv_name]["headers"] = headers
                            row_count = sum(1 for _ in reader)
                            csv_results[csv_name]["row_count"] = row_count
                    except Exception as e:
                        csv_results[csv_name]["error"] = str(e)
                    break
            if csv_results[csv_name]["found"]:
                break
    return csv_results


def check_already_ingested(conn, file_list):
    """Check which files are already in the DB."""
    already_in_db = set()
    not_in_db = []

    # Get known file paths from various evidence tables
    known_paths = set()
    for table in ['drive_evidence', 'evidence_file_index', 'scanned_evidence_catalog',
                   'desktop_evidence_index', 'evidence_extract_inventory']:
        schema_rows = safe_query(conn, f"PRAGMA table_info([{table}])")
        if not schema_rows:
            continue
        cols = [r['name'] for r in schema_rows]
        path_cols = [c for c in cols if any(k in c.lower() for k in ['path', 'file', 'source', 'location'])]
        for pc in path_cols:
            rows = safe_query(conn, f"SELECT [{pc}] FROM [{table}] WHERE [{pc}] LIKE 'D:%' LIMIT 10000")
            for r in rows:
                val = r.get(pc)
                if val:
                    known_paths.add(os.path.normpath(str(val)).lower())

    for finfo in file_list:
        norm = os.path.normpath(finfo['path']).lower()
        if norm in known_paths or os.path.basename(norm) in {os.path.basename(p) for p in known_paths}:
            already_in_db.add(finfo['path'])
        else:
            not_in_db.append(finfo)

    return already_in_db, not_in_db


def build_integration_manifest(scan_results, not_in_db_files):
    """Create a manifest of what should be imported."""
    manifest = {
        "total_new_files": len(not_in_db_files),
        "priority_tiers": {
            "P0_critical": [],
            "P1_high": [],
            "P2_medium": [],
            "P3_low": [],
        },
    }

    for f in not_in_db_files:
        name_lower = f['name'].lower()
        ext = os.path.splitext(name_lower)[1]

        # P0: HealthWest, court orders, sworn documents
        if any(kw in name_lower for kw in ['healthwest', 'delusional', 'subpoena', 'order',
                                            'affidavit', 'custody', 'ppo']):
            tier = "P0_critical"
        # P1: Evidence, motions, briefs
        elif any(kw in name_lower for kw in ['evidence', 'motion', 'brief', 'exhibit',
                                              'rebuttal', 'complaint', 'appeal']):
            tier = "P1_high"
        # P2: DBs, CSVs, structured data
        elif ext in {'.db', '.sqlite', '.csv', '.xlsx', '.json'}:
            tier = "P2_medium"
        # P3: Everything else
        else:
            tier = "P3_low"

        entry = {
            "name": f['name'],
            "path": f['path'],
            "size": f.get('size', 0),
            "size_human": f.get('size_human', format_size(f.get('size', 0))),
            "suggested_table": suggest_target_table(f),
        }
        manifest["priority_tiers"][tier].append(entry)

    for tier in manifest["priority_tiers"]:
        manifest["priority_tiers"][tier] = sorted(
            manifest["priority_tiers"][tier], key=lambda x: x['size'], reverse=True
        )[:25]

    return manifest


def suggest_target_table(finfo):
    """Suggest which DB table a file should be ingested into."""
    name = finfo['name'].lower()
    ext = os.path.splitext(name)[1]

    if ext == '.db':
        return "drive_evidence (DB merge)"
    elif ext == '.csv':
        return "evidence_quotes or claims (CSV import)"
    elif ext == '.pdf':
        return "scanned_evidence_catalog (PDF extract)"
    elif ext in {'.docx', '.doc'}:
        return "evidence_extract_inventory (DOCX extract)"
    elif any(kw in name for kw in ['health', 'eval', 'clinical']):
        return "medical_records_needed (HealthWest)"
    elif any(kw in name for kw in ['motion', 'brief', 'order']):
        return "filing_documents"
    else:
        return "drive_evidence (general catalog)"


def build_catalog(conn):
    print("=" * 70)
    print("  Tool #222 — D: Drive Evidence Ingester")
    print("=" * 70)

    # 1. Scan directories
    print("\n[1/5] Scanning D:\\ drive directories...")
    scans = {}
    for dirpath in SCAN_PATHS:
        print(f"  Scanning: {dirpath}")
        result = scan_directory(dirpath)
        scans[dirpath] = result
        if result['exists']:
            print(f"    → {result['total_files']} files, {result['total_size_human']}, "
                  f"{result['subdirectories']} subdirs")
        else:
            print(f"    → DOES NOT EXIST")

    # 2. Read CSV headers
    print("\n[2/5] Reading CSV headers...")
    base_dirs = [r"D:\LitigationOS_Extracted", r"D:\LITIGATIONOS_DATA"]
    csv_results = read_csv_headers(base_dirs)
    for name, info in csv_results.items():
        if info['found']:
            print(f"  {name}: {len(info['headers'])} columns, {info['row_count']} rows")
            if info['headers']:
                print(f"    Headers: {', '.join(info['headers'][:8])}{'...' if len(info['headers']) > 8 else ''}")
        else:
            print(f"  {name}: NOT FOUND on D:\\")

    # 3. Collect all high-priority files
    print("\n[3/5] Collecting high-priority files...")
    all_hp_files = []
    for dirpath, result in scans.items():
        all_hp_files.extend(result.get('high_priority_files', []))
    print(f"  Total high-priority files: {len(all_hp_files)}")

    # 4. Check which are already in DB
    print("\n[4/5] Checking ingestion status against litigation_context.db...")
    already_ingested, not_ingested = check_already_ingested(conn, all_hp_files)
    print(f"  Already in DB: {len(already_ingested)}")
    print(f"  NOT in DB (need ingestion): {len(not_ingested)}")

    # 5. Build integration manifest
    print("\n[5/5] Building integration manifest...")
    manifest = build_integration_manifest(scans, not_ingested)
    for tier, files in manifest['priority_tiers'].items():
        print(f"  {tier}: {len(files)} files")

    # Totals
    total_files = sum(s['total_files'] for s in scans.values())
    total_size = sum(s['total_size_bytes'] for s in scans.values())

    catalog = {
        "tool": "Tool #222 — D: Drive Evidence Ingester",
        "generated": datetime.now().isoformat(),
        "summary": {
            "directories_scanned": len(SCAN_PATHS),
            "directories_found": sum(1 for s in scans.values() if s['exists']),
            "total_files": total_files,
            "total_size_bytes": total_size,
            "total_size_human": format_size(total_size),
            "high_priority_files": len(all_hp_files),
            "already_ingested": len(already_ingested),
            "needs_ingestion": len(not_ingested),
        },
        "directory_scans": scans,
        "csv_inspection": csv_results,
        "integration_manifest": manifest,
    }

    return catalog


def write_markdown(catalog, path):
    c = catalog
    s = c['summary']
    lines = [
        "# D: Drive Evidence Catalog",
        f"*Generated: {c['generated']}*\n",
        "## Summary\n",
        "| Metric | Value |",
        "|--------|-------|",
        f"| Directories Scanned | {s['directories_scanned']} |",
        f"| Directories Found | {s['directories_found']} |",
        f"| Total Files | {s['total_files']:,} |",
        f"| Total Size | {s['total_size_human']} |",
        f"| High-Priority Files | {s['high_priority_files']} |",
        f"| Already Ingested | {s['already_ingested']} |",
        f"| **Needs Ingestion** | **{s['needs_ingestion']}** |",
        "",
    ]

    # Directory details
    lines.append("## Directory Scans\n")
    for dirpath, scan in c['directory_scans'].items():
        lines.append(f"### `{dirpath}`")
        if not scan['exists']:
            lines.append("**Status:** ❌ Does not exist\n")
            continue
        lines.append(f"**Files:** {scan['total_files']:,} | "
                     f"**Size:** {scan['total_size_human']} | "
                     f"**Subdirs:** {scan['subdirectories']}\n")

        if scan.get('error'):
            lines.append(f"⚠️ Error: {scan['error']}\n")

        # Extensions table
        if scan['extensions']:
            lines.append("| Extension | Count | Size |")
            lines.append("|-----------|-------|------|")
            for ext, info in list(scan['extensions'].items())[:15]:
                lines.append(f"| {ext} | {info['count']:,} | {info['size_human']} |")
            lines.append("")

        # Key files
        if scan['key_files']:
            lines.append("**Largest Files:**")
            for kf in scan['key_files'][:10]:
                lines.append(f"- `{kf['name']}` — {kf['size_human']}")
            lines.append("")

    # CSV inspection
    lines.append("## CSV Inspection\n")
    for name, info in c['csv_inspection'].items():
        lines.append(f"### {name}")
        if not info['found']:
            lines.append("**Status:** Not found on D:\\\n")
            continue
        lines.append(f"**Path:** `{info['path']}`  ")
        lines.append(f"**Rows:** {info['row_count']:,} | **Columns:** {len(info['headers'])}\n")
        if info['headers']:
            lines.append("**Headers:**")
            lines.append(f"```\n{', '.join(info['headers'])}\n```\n")

    # Integration manifest
    m = c['integration_manifest']
    lines.append("## Integration Manifest\n")
    lines.append(f"**Total new files to ingest:** {m['total_new_files']}\n")

    tier_names = {
        "P0_critical": "🔴 P0 — Critical (court orders, HealthWest, sworn docs)",
        "P1_high": "🟠 P1 — High (evidence, motions, briefs)",
        "P2_medium": "🟡 P2 — Medium (databases, CSVs, structured data)",
        "P3_low": "🟢 P3 — Low (general documents)",
    }

    for tier, label in tier_names.items():
        files = m['priority_tiers'].get(tier, [])
        lines.append(f"### {label}")
        lines.append(f"**Files:** {len(files)}\n")
        if files:
            lines.append("| File | Size | Suggested Target |")
            lines.append("|------|------|-----------------|")
            for f in files[:15]:
                lines.append(f"| `{f['name']}` | {f['size_human']} | {f['suggested_table']} |")
            lines.append("")

    lines.append("---")
    lines.append("*Tool #222 — D: Drive Evidence Ingester — LitigationOS*")

    with open(path, 'w', encoding='utf-8') as f:
        f.write('\n'.join(lines))


def main():
    os.makedirs(REPORTS_DIR, exist_ok=True)

    if not os.path.exists(DB_PATH):
        print(f"[ERROR] Database not found: {DB_PATH}")
        sys.exit(1)

    conn = get_connection()
    try:
        catalog = build_catalog(conn)

        json_path = os.path.join(REPORTS_DIR, 'd_drive_evidence_catalog.json')
        with open(json_path, 'w', encoding='utf-8') as f:
            json.dump(catalog, f, indent=2, default=str, ensure_ascii=False)
        print(f"\n[OK] JSON → {json_path}")

        md_path = os.path.join(REPORTS_DIR, 'D_DRIVE_EVIDENCE_CATALOG.md')
        write_markdown(catalog, md_path)
        print(f"[OK] MD   → {md_path}")

        s = catalog['summary']
        print(f"\n{'=' * 70}")
        print(f"  D: DRIVE EVIDENCE CATALOG COMPLETE")
        print(f"  Files: {s['total_files']:,} | Size: {s['total_size_human']} | "
              f"New to ingest: {s['needs_ingestion']}")
        print(f"{'=' * 70}")
    finally:
        conn.close()


if __name__ == '__main__':
    main()
