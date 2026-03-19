#!/usr/bin/env python3
"""
MBP LitigationOS — Unprocessed Document Scanner (d38)
=======================================================
Catalog files in LitigationOS directory tree NOT yet in
scan_inventory or evidence_file_index DB tables.

Stores results in `unprocessed_docs` table and generates
a markdown inventory report.

Usage:
    python scan_unprocessed_docs.py
"""

from __future__ import annotations

import io
import json
import os
import sqlite3
import sys
from collections import Counter
from datetime import datetime
from pathlib import Path
from typing import Set

if sys.stdout and hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
elif sys.stdout is None or not hasattr(sys.stdout, "encoding") or sys.stdout.encoding != "utf-8":
    sys.stdout = io.TextIOWrapper(
        sys.stdout.buffer if sys.stdout else open(os.devnull, "w"), encoding="utf-8"
    )

DB_PATH = r"C:\Users\andre\LitigationOS\litigation_context.db"
ROOT_DIR = r"C:\Users\andre\LitigationOS"
REPORT_PATH = r"C:\Users\andre\LitigationOS\00_SYSTEM\UNPROCESSED_DOCS_INVENTORY.md"

# File extensions to scan (legal/evidence relevant)
RELEVANT_EXTENSIONS = {
    ".pdf", ".docx", ".doc", ".txt", ".md", ".rtf",
    ".xlsx", ".xls", ".csv",
    ".png", ".jpg", ".jpeg", ".tiff", ".bmp", ".gif",
    ".eml", ".msg",
    ".html", ".htm",
    ".json", ".xml",
    ".zip", ".rar", ".7z",
}

# Directories to skip
SKIP_DIRS = {
    "__pycache__", ".git", "node_modules", ".vscode",
    "venv", ".env", ".mypy_cache", ".pytest_cache",
}

# Priority rules
HIGH_PRIORITY_KEYWORDS = ["court", "order", "motion", "brief", "filing", "evidence", "exhibit"]
MEDIUM_PRIORITY_KEYWORDS = ["letter", "email", "report", "statement", "affidavit", "transcript"]


def classify_priority(file_path: str, file_name: str) -> str:
    """Classify file priority based on name and location."""
    lower_name = file_name.lower()
    lower_path = file_path.lower()
    if any(kw in lower_name or kw in lower_path for kw in HIGH_PRIORITY_KEYWORDS):
        return "HIGH"
    if any(kw in lower_name or kw in lower_path for kw in MEDIUM_PRIORITY_KEYWORDS):
        return "MEDIUM"
    return "LOW"


def main():
    print("=" * 72)
    print("UNPROCESSED DOCUMENT SCANNER (d38)")
    print("=" * 72)
    print(f"\nDB: {DB_PATH}")
    print(f"Root: {ROOT_DIR}")
    print(f"Time: {datetime.now().isoformat()}")

    # Connect to DB
    conn = sqlite3.connect(DB_PATH, timeout=60)
    conn.execute("PRAGMA journal_mode=WAL")

    # Step 1: Get existing indexed paths
    print("\n--- Loading indexed paths from DB ---")

    indexed_paths: Set[str] = set()

    # scan_inventory
    try:
        conn.execute("PRAGMA table_info(scan_inventory)")
        rows = conn.execute("SELECT file_path FROM scan_inventory WHERE file_path IS NOT NULL").fetchall()
        scan_count = len(rows)
        for r in rows:
            indexed_paths.add(os.path.normpath(r[0]).lower())
        print(f"  scan_inventory: {scan_count:,} paths loaded")
    except Exception as e:
        print(f"  scan_inventory: ERROR - {e}")
        scan_count = 0

    # evidence_file_index
    try:
        conn.execute("PRAGMA table_info(evidence_file_index)")
        rows = conn.execute("SELECT file_path FROM evidence_file_index WHERE file_path IS NOT NULL").fetchall()
        efi_count = len(rows)
        for r in rows:
            indexed_paths.add(os.path.normpath(r[0]).lower())
        print(f"  evidence_file_index: {efi_count:,} paths loaded")
    except Exception as e:
        print(f"  evidence_file_index: ERROR - {e}")
        efi_count = 0

    print(f"  Total unique indexed: {len(indexed_paths):,}")

    # Step 2: Walk filesystem under LitigationOS
    print("\n--- Scanning filesystem ---")
    unprocessed = []
    total_scanned = 0
    ext_counter = Counter()
    dir_counter = Counter()

    for dirpath, dirnames, filenames in os.walk(ROOT_DIR):
        # Skip excluded directories
        dirnames[:] = [d for d in dirnames if d not in SKIP_DIRS]

        for fname in filenames:
            total_scanned += 1
            fpath = os.path.join(dirpath, fname)
            ext = os.path.splitext(fname)[1].lower()

            # Only check relevant file types
            if ext not in RELEVANT_EXTENSIONS:
                continue

            normalized = os.path.normpath(fpath).lower()
            if normalized not in indexed_paths:
                try:
                    size_kb = os.path.getsize(fpath) / 1024.0
                except OSError:
                    size_kb = 0.0

                parent = os.path.basename(dirpath)
                priority = classify_priority(fpath, fname)

                unprocessed.append({
                    "file_path": fpath,
                    "file_type": ext,
                    "size_kb": round(size_kb, 2),
                    "directory": parent,
                    "priority": priority,
                })
                ext_counter[ext] += 1
                dir_counter[parent] += 1

        if total_scanned % 10000 == 0:
            print(f"  Scanned {total_scanned:,} files, found {len(unprocessed):,} unprocessed...")

    print(f"\n  Total files scanned: {total_scanned:,}")
    print(f"  Unprocessed found: {len(unprocessed):,}")

    # Step 3: Store in DB
    print("\n--- Storing in unprocessed_docs table ---")
    try:
        conn.execute("DROP TABLE IF EXISTS unprocessed_docs")
        conn.execute("""
            CREATE TABLE unprocessed_docs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                file_path TEXT NOT NULL,
                file_type TEXT,
                size_kb REAL,
                directory TEXT,
                priority TEXT,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
        """)
        conn.executemany(
            "INSERT INTO unprocessed_docs (file_path, file_type, size_kb, directory, priority) "
            "VALUES (?, ?, ?, ?, ?)",
            [(d["file_path"], d["file_type"], d["size_kb"], d["directory"], d["priority"])
             for d in unprocessed],
        )
        conn.commit()
        final_count = conn.execute("SELECT COUNT(*) FROM unprocessed_docs").fetchone()[0]
        print(f"  Stored {final_count:,} rows in unprocessed_docs")
    except Exception as e:
        print(f"  ERROR storing: {e}")

    # Step 4: Stats
    high = sum(1 for d in unprocessed if d["priority"] == "HIGH")
    medium = sum(1 for d in unprocessed if d["priority"] == "MEDIUM")
    low = sum(1 for d in unprocessed if d["priority"] == "LOW")
    total_size_mb = sum(d["size_kb"] for d in unprocessed) / 1024.0

    print(f"\n--- Priority Breakdown ---")
    print(f"  HIGH:   {high:,}")
    print(f"  MEDIUM: {medium:,}")
    print(f"  LOW:    {low:,}")
    print(f"  Total size: {total_size_mb:,.1f} MB")

    print(f"\n--- Top 10 Extensions ---")
    for ext, count in ext_counter.most_common(10):
        print(f"  {ext}: {count:,}")

    print(f"\n--- Top 10 Directories ---")
    for d, count in dir_counter.most_common(10):
        print(f"  {d}: {count:,}")

    # Step 5: Generate report
    print(f"\n--- Generating report ---")
    report_lines = [
        f"# Unprocessed Documents Inventory",
        f"",
        f"**Generated:** {datetime.now().isoformat()}",
        f"**Root scanned:** `{ROOT_DIR}`",
        f"**DB:** `{DB_PATH}`",
        f"",
        f"## Summary",
        f"",
        f"| Metric | Count |",
        f"|--------|-------|",
        f"| Total files scanned | {total_scanned:,} |",
        f"| Already indexed (scan_inventory) | {scan_count:,} |",
        f"| Already indexed (evidence_file_index) | {efi_count:,} |",
        f"| Unique indexed paths | {len(indexed_paths):,} |",
        f"| **Unprocessed found** | **{len(unprocessed):,}** |",
        f"| Total unprocessed size | {total_size_mb:,.1f} MB |",
        f"",
        f"## Priority Breakdown",
        f"",
        f"| Priority | Count | Action |",
        f"|----------|-------|--------|",
        f"| HIGH | {high:,} | Court/evidence docs — ingest immediately |",
        f"| MEDIUM | {medium:,} | Supporting docs — ingest next |",
        f"| LOW | {low:,} | Background docs — batch process |",
        f"",
        f"## By File Type",
        f"",
        f"| Extension | Count |",
        f"|-----------|-------|",
    ]
    for ext, count in ext_counter.most_common(20):
        report_lines.append(f"| {ext} | {count:,} |")

    report_lines.extend([
        f"",
        f"## By Directory (Top 20)",
        f"",
        f"| Directory | Count |",
        f"|-----------|-------|",
    ])
    for d, count in dir_counter.most_common(20):
        report_lines.append(f"| {d} | {count:,} |")

    # HIGH priority samples
    report_lines.extend([
        f"",
        f"## HIGH Priority Samples (first 30)",
        f"",
    ])
    high_items = [d for d in unprocessed if d["priority"] == "HIGH"][:30]
    for item in high_items:
        report_lines.append(f"- `{item['file_path']}` ({item['size_kb']:.1f} KB)")

    report_lines.extend([
        f"",
        f"---",
        f"*Report generated by scan_unprocessed_docs.py (d38)*",
    ])

    report_text = "\n".join(report_lines)
    with open(REPORT_PATH, "w", encoding="utf-8") as f:
        f.write(report_text)
    print(f"  Report saved: {REPORT_PATH} ({len(report_text):,} chars)")

    conn.close()
    print(f"\n{'=' * 72}")
    print(f"SCAN COMPLETE — {len(unprocessed):,} unprocessed documents cataloged")
    print(f"{'=' * 72}")


if __name__ == "__main__":
    main()
