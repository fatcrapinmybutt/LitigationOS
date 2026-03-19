#!/usr/bin/env python3
"""
deep_evidence_scan.py — LitigationOS Evidence Deep Scanner
Walks target directories, catalogs files, extracts key content from
CSV/JSON/TXT/MD files, and saves everything to evidence_file_index in
litigation_context.db.

Pigors v. Watson consolidated litigation support.
"""

import os
import sys
import json
import csv
import sqlite3
import hashlib
import re
from pathlib import Path
from datetime import datetime

DB_PATH = r"C:\Users\andre\litigation_context.db"

SCAN_DIRS = [
    (r"C:\Users\andre\Downloads", "downloads"),
    (r"C:\Users\andre\Scans\discovery", "scans_discovery"),
    (r"C:\Users\andre\Documents\WATSONS", "documents_watsons"),
    (r"C:\Users\andre\Documents\!!!!!!!SHADYOAKS", "documents_shadyoaks"),
    (r"C:\Users\andre\LitigationOS\03_EVIDENCE", "litigation_evidence"),
]

# Lane classification keywords
LANE_KEYWORDS = {
    "A": ["custody", "parenting", "visitation", "child", "mcl 722", "best interest",
           "factor", "custodial", "parenting time", "friend of court", "foc",
           "guardian", "gal", "mcneill", "2024-001507"],
    "B": ["shady oaks", "shadyoaks", "housing", "landlord", "tenant", "lease",
           "eviction", "rent", "habitability", "maintenance"],
    "C": ["convergence", "consolidated", "cross-lane", "multi-case"],
    "D": ["ppo", "protection order", "stalking", "harassment", "2023-5907",
           "domestic violence", "restraining"],
    "E": ["judicial misconduct", "jtc", "canon", "bias", "prejudice",
           "disqualification", "mcr 2.003", "recusal"],
    "F": ["appeal", "coa", "366810", "appellate", "claim of appeal",
           "mcr 7.204", "mcr 7.205", "brief on appeal", "court of appeals"],
}

# Priority files in Downloads to extract content from
PRIORITY_FILES = {
    "Global_Chronology.csv.json": "json_timeline",
    "Narcissistic_Manipulation_and_Parental_Alienation_Tactics": "csv_tactics",
    "Verified Chronology of Procedural Violations": "pdf_chronology",
    "Comprehensive Overview of MEEK": "docx_meek",
    "EMAIL EXHIBITS PERFECT": "txt_exhibits",
    "MEEK234_HIGHSIGNAL": "txt_meek_manifest",
    "Motion_-_Civil_Rights_Complaint": "txt_motion",
}


def create_tables(conn):
    conn.execute("""
        CREATE TABLE IF NOT EXISTS evidence_file_index (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            file_path TEXT UNIQUE,
            file_name TEXT,
            file_type TEXT,
            file_size INTEGER,
            directory TEXT,
            keywords TEXT,
            relevance_lane TEXT,
            ingested INTEGER DEFAULT 0,
            created_at TEXT DEFAULT (datetime('now'))
        )
    """)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS evidence_content_extracts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            file_path TEXT,
            extract_type TEXT,
            content TEXT,
            row_count INTEGER,
            created_at TEXT DEFAULT (datetime('now')),
            FOREIGN KEY (file_path) REFERENCES evidence_file_index(file_path)
        )
    """)
    conn.execute("""
        CREATE INDEX IF NOT EXISTS idx_efi_directory ON evidence_file_index(directory)
    """)
    conn.execute("""
        CREATE INDEX IF NOT EXISTS idx_efi_file_type ON evidence_file_index(file_type)
    """)
    conn.execute("""
        CREATE INDEX IF NOT EXISTS idx_efi_lane ON evidence_file_index(relevance_lane)
    """)
    conn.commit()


def classify_lane(file_path, file_name, content_snippet=""):
    """Classify which litigation lane(s) a file belongs to."""
    search_text = (file_path + " " + file_name + " " + content_snippet).lower()
    matched_lanes = []
    for lane, keywords in LANE_KEYWORDS.items():
        for kw in keywords:
            if kw in search_text:
                matched_lanes.append(lane)
                break

    # Directory-based fallbacks
    path_lower = file_path.lower()
    if "shadyoaks" in path_lower and "B" not in matched_lanes:
        matched_lanes.append("B")
    if "watsons" in path_lower and "A" not in matched_lanes:
        matched_lanes.append("A")
    if "discovery" in path_lower and not matched_lanes:
        matched_lanes.append("A")
    if "emails" in path_lower and not matched_lanes:
        matched_lanes.append("A")

    return ",".join(sorted(set(matched_lanes))) if matched_lanes else "UNCLASSIFIED"


def extract_keywords(file_name, content_snippet=""):
    """Extract keywords from filename and content."""
    text = file_name + " " + content_snippet
    # Remove common extensions and split
    text = re.sub(r'\.(pdf|docx|csv|json|txt|md|xlsx|eml|msg|jpg|png|tif|tiff)$', '', text, flags=re.I)
    text = re.sub(r'[_\-\.\(\)\[\]\{\}]', ' ', text)
    words = [w.strip().lower() for w in text.split() if len(w.strip()) > 2]
    # Dedupe preserving order
    seen = set()
    unique = []
    for w in words:
        if w not in seen:
            seen.add(w)
            unique.append(w)
    return ",".join(unique[:20])


def read_json_file(fpath):
    """Read and parse a JSON file, return content summary."""
    try:
        with open(fpath, "r", encoding="utf-8", errors="replace") as f:
            data = json.load(f)
        if isinstance(data, list):
            return json.dumps(data[:50], indent=2, default=str), len(data)
        elif isinstance(data, dict):
            return json.dumps(data, indent=2, default=str)[:10000], 1
        return str(data)[:10000], 1
    except Exception as e:
        return f"[JSON parse error: {e}]", 0


def read_csv_file(fpath):
    """Read and parse a CSV file, return content summary."""
    try:
        rows = []
        with open(fpath, "r", encoding="utf-8", errors="replace") as f:
            reader = csv.DictReader(f)
            for i, row in enumerate(reader):
                rows.append(dict(row))
                if i >= 200:
                    break
        if rows:
            return json.dumps(rows, indent=2, default=str), len(rows)
        return "[Empty CSV]", 0
    except Exception as e:
        return f"[CSV parse error: {e}]", 0


def read_text_file(fpath, max_chars=15000):
    """Read a text/markdown file."""
    try:
        with open(fpath, "r", encoding="utf-8", errors="replace") as f:
            content = f.read(max_chars)
        lines = content.count('\n')
        return content, lines
    except Exception as e:
        return f"[Read error: {e}]", 0


def process_priority_file(fpath, file_name, conn):
    """Extract content from priority files in Downloads."""
    for key, ftype in PRIORITY_FILES.items():
        if key.lower() in file_name.lower():
            content = ""
            row_count = 0

            if ftype == "json_timeline":
                content, row_count = read_json_file(fpath)
            elif ftype == "csv_tactics":
                content, row_count = read_csv_file(fpath)
            elif ftype.startswith("txt_"):
                content, row_count = read_text_file(fpath)
            elif ftype == "pdf_chronology":
                content = f"[PDF indexed: {file_name}, size={os.path.getsize(fpath)} bytes. Requires PDF text extraction for full content.]"
                row_count = 0
            elif ftype == "docx_meek":
                content = f"[DOCX indexed: {file_name}, size={os.path.getsize(fpath)} bytes. Requires python-docx for full content extraction.]"
                row_count = 0

            if content:
                try:
                    conn.execute("""
                        INSERT OR REPLACE INTO evidence_content_extracts
                        (file_path, extract_type, content, row_count)
                        VALUES (?, ?, ?, ?)
                    """, (fpath, ftype, content, row_count))
                except Exception as e:
                    print(f"  [!] Content extract error for {file_name}: {e}")

            return True
    return False


def extract_content_for_indexable(fpath, ext):
    """For CSV/JSON/TXT/MD files, extract a snippet for keyword extraction."""
    try:
        if ext == ".json":
            with open(fpath, "r", encoding="utf-8", errors="replace") as f:
                return f.read(2000)
        elif ext == ".csv":
            with open(fpath, "r", encoding="utf-8", errors="replace") as f:
                return f.read(2000)
        elif ext in (".txt", ".md", ".log"):
            with open(fpath, "r", encoding="utf-8", errors="replace") as f:
                return f.read(2000)
    except:
        pass
    return ""


def scan_directory(dir_path, dir_label, conn, stats):
    """Walk a directory and catalog all files."""
    if not os.path.exists(dir_path):
        print(f"\n[SKIP] Directory not found: {dir_path}")
        return

    print(f"\n{'='*70}")
    print(f"SCANNING: {dir_path}")
    print(f"Label: {dir_label}")
    print(f"{'='*70}")

    file_count = 0
    new_count = 0
    skip_count = 0
    type_counts = {}
    batch = []
    batch_size = 500

    for root, dirs, files in os.walk(dir_path):
        for fname in files:
            fpath = os.path.join(root, fname)
            try:
                fsize = os.path.getsize(fpath)
            except OSError:
                continue

            file_count += 1
            ext = os.path.splitext(fname)[1].lower()
            type_counts[ext] = type_counts.get(ext, 0) + 1

            # Extract content snippet for indexable files
            content_snippet = ""
            if ext in (".csv", ".json", ".txt", ".md", ".log") and fsize < 5_000_000:
                content_snippet = extract_content_for_indexable(fpath, ext)

            keywords = extract_keywords(fname, content_snippet[:500])
            lane = classify_lane(fpath, fname, content_snippet[:500])

            batch.append((
                fpath, fname, ext, fsize, dir_label, keywords, lane, 0
            ))

            # Process priority files (Downloads)
            if dir_label == "downloads":
                process_priority_file(fpath, fname, conn)

            # For CSV/JSON/TXT in evidence directories, extract content
            if dir_label in ("litigation_evidence", "documents_watsons", "documents_shadyoaks"):
                if ext == ".csv" and fsize < 5_000_000:
                    content, row_count = read_csv_file(fpath)
                    if row_count > 0:
                        try:
                            conn.execute("""
                                INSERT OR REPLACE INTO evidence_content_extracts
                                (file_path, extract_type, content, row_count)
                                VALUES (?, ?, ?, ?)
                            """, (fpath, "csv_data", content, row_count))
                        except:
                            pass
                elif ext == ".json" and fsize < 5_000_000:
                    content, row_count = read_json_file(fpath)
                    if row_count > 0:
                        try:
                            conn.execute("""
                                INSERT OR REPLACE INTO evidence_content_extracts
                                (file_path, extract_type, content, row_count)
                                VALUES (?, ?, ?, ?)
                            """, (fpath, "json_data", content, row_count))
                        except:
                            pass
                elif ext in (".txt", ".md") and fsize < 2_000_000:
                    content, line_count = read_text_file(fpath)
                    if line_count > 0:
                        try:
                            conn.execute("""
                                INSERT OR REPLACE INTO evidence_content_extracts
                                (file_path, extract_type, content, row_count)
                                VALUES (?, ?, ?, ?)
                            """, (fpath, "text_content", content, line_count))
                        except:
                            pass

            # Flush batch
            if len(batch) >= batch_size:
                inserted = flush_batch(conn, batch)
                new_count += inserted
                skip_count += len(batch) - inserted
                batch = []

            # Progress indicator for large directories
            if file_count % 10000 == 0:
                print(f"  ... processed {file_count} files ...")

    # Flush remaining
    if batch:
        inserted = flush_batch(conn, batch)
        new_count += inserted
        skip_count += len(batch) - inserted

    conn.commit()

    # Print summary
    print(f"\n  Total files found: {file_count}")
    print(f"  New files indexed: {new_count}")
    print(f"  Already indexed:   {skip_count}")
    print(f"\n  File types:")
    for ext, count in sorted(type_counts.items(), key=lambda x: -x[1])[:15]:
        print(f"    {ext or '(no ext)':12s} : {count}")

    stats[dir_label] = {
        "total": file_count,
        "new": new_count,
        "skipped": skip_count,
        "types": type_counts,
    }


def flush_batch(conn, batch):
    """Insert a batch of file records, return count of new inserts."""
    inserted = 0
    for row in batch:
        try:
            conn.execute("""
                INSERT OR IGNORE INTO evidence_file_index
                (file_path, file_name, file_type, file_size, directory, keywords, relevance_lane, ingested)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, row)
            if conn.total_changes:
                inserted += 1
        except sqlite3.IntegrityError:
            pass
        except Exception as e:
            pass
    return inserted


def print_final_summary(conn, stats):
    """Print the final summary report."""
    print(f"\n{'='*70}")
    print(f"DEEP EVIDENCE SCAN — FINAL SUMMARY")
    print(f"{'='*70}")
    print(f"Scan completed: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"Database: {DB_PATH}")

    total_files = sum(s["total"] for s in stats.values())
    total_new = sum(s["new"] for s in stats.values())
    print(f"\nTotal files scanned: {total_files}")
    print(f"Total new indexed:  {total_new}")

    print(f"\n--- Per Directory ---")
    for label, s in stats.items():
        print(f"  {label:25s}: {s['total']:>7,} files ({s['new']:,} new)")

    # DB stats
    cur = conn.cursor()
    cur.execute("SELECT COUNT(*) FROM evidence_file_index")
    total_indexed = cur.fetchone()[0]
    print(f"\n--- Database Totals ---")
    print(f"  evidence_file_index rows: {total_indexed:,}")

    cur.execute("SELECT COUNT(*) FROM evidence_content_extracts")
    total_extracts = cur.fetchone()[0]
    print(f"  evidence_content_extracts rows: {total_extracts:,}")

    # Lane distribution
    print(f"\n--- Lane Distribution ---")
    cur.execute("""
        SELECT relevance_lane, COUNT(*) as cnt
        FROM evidence_file_index
        GROUP BY relevance_lane
        ORDER BY cnt DESC
    """)
    for row in cur.fetchall():
        print(f"  Lane {row[0]:20s}: {row[1]:>7,} files")

    # File type distribution
    print(f"\n--- Top File Types ---")
    cur.execute("""
        SELECT file_type, COUNT(*) as cnt
        FROM evidence_file_index
        GROUP BY file_type
        ORDER BY cnt DESC
        LIMIT 15
    """)
    for row in cur.fetchall():
        print(f"  {row[0] or '(none)':12s}: {row[1]:>7,}")

    # Content extracts by type
    print(f"\n--- Content Extracts ---")
    cur.execute("""
        SELECT extract_type, COUNT(*), SUM(row_count)
        FROM evidence_content_extracts
        GROUP BY extract_type
    """)
    for row in cur.fetchall():
        print(f"  {row[0]:20s}: {row[1]:>5} files, {row[2] or 0:>7,} rows extracted")


def main():
    print(f"LitigationOS Deep Evidence Scanner")
    print(f"Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"Database: {DB_PATH}")

    conn = sqlite3.connect(DB_PATH, timeout=30)
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA synchronous=NORMAL")
    conn.execute("PRAGMA cache_size=-64000")  # 64MB cache

    create_tables(conn)

    stats = {}
    for dir_path, dir_label in SCAN_DIRS:
        scan_directory(dir_path, dir_label, conn, stats)

    conn.commit()
    print_final_summary(conn, stats)
    conn.close()

    print(f"\n{'='*70}")
    print(f"SCAN COMPLETE — All evidence indexed in litigation_context.db")
    print(f"{'='*70}")


if __name__ == "__main__":
    main()
