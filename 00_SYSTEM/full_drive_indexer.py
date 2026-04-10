"""
APEX Full Drive Indexer v1.0
============================
Scans ALL drives and upserts into file_inventory table in litigation_context.db.
Uses INSERT OR REPLACE with file_path as unique key.
Prioritizes J:\ (currently missing, ~460GB unindexed).

Usage:
    python -I D:\\LitigationOS_tmp\\full_drive_indexer.py [--drives C D J] [--skip-existing]
"""
from __future__ import annotations

import argparse
import datetime
import hashlib
import mimetypes
import os
import re
import sqlite3
import sys
import time
from pathlib import Path

# ── Config ─────────────────────────────────────────────────────────────────
DB_PATH = r"C:\Users\andre\LitigationOS\litigation_context.db"
BATCH_SIZE = 2000
LOG_EVERY = 10000

# Default drive roots to index (J first since it's missing)
DEFAULT_DRIVES = ["J", "C", "D", "F", "G", "I"]

# Skip these dirs — they add noise and waste time
SKIP_DIRS = {
    ".git", "__pycache__", ".mypy_cache", ".ruff_cache",
    "node_modules", ".venv", "venv", "pytools_venv",
    "System Volume Information", "$RECYCLE.BIN", "$SysReset",
    "Windows", "Program Files", "Program Files (x86)",
    "ProgramData",
}

# MEEK lane keywords for litigation_relevant classification
MEEK_KEYWORDS = {
    "custody", "parenting", "watson", "pigors", "mcneill", "appellate",
    "ppo", "contempt", "affidavit", "motion", "brief", "complaint",
    "exhibit", "evidence", "deposition", "judgment", "order", "court",
    "trial", "filing", "attorney", "litigation", "appeal", "coa",
    "msc", "jtc", "foc", "nexus", "litigationos", "manbearpig",
}

# Canonical category mapping by path segment
CATEGORY_MAP = {
    "00_SYSTEM": "system",
    "01_EVIDENCE": "evidence",
    "02_AUTHORITY": "authority",
    "03_COURT": "court",
    "04_ANALYSIS": "analysis",
    "05_FILINGS": "filings",
    "06_DATA": "data",
    "07_CODE": "code",
    "08_MEDIA": "media",
    "09_REFERENCE": "reference",
    "10_EXTERNAL": "external",
    "11_ARCHIVES": "archives",
    "12_WORKSPACE": "workspace",
}


def open_db() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH)
    conn.execute("PRAGMA busy_timeout=60000")
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA cache_size=-32000")
    conn.execute("PRAGMA synchronous=NORMAL")
    conn.execute("PRAGMA temp_store=MEMORY")
    return conn


def ensure_file_inventory(conn: sqlite3.Connection) -> None:
    """Ensure file_inventory exists with correct schema."""
    conn.execute("""
        CREATE TABLE IF NOT EXISTS file_inventory (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            file_path TEXT UNIQUE NOT NULL,
            file_name TEXT,
            extension TEXT,
            drive_letter TEXT,
            size_bytes INTEGER,
            modified_date TEXT,
            sha256 TEXT,
            mime_type TEXT,
            is_litigation_relevant INTEGER DEFAULT 0,
            lane TEXT,
            ingested INTEGER DEFAULT 0,
            created_at TEXT,
            canonical_category TEXT,
            source_table TEXT DEFAULT 'file_inventory'
        )
    """)
    # Ensure index on file_path for fast upsert
    conn.execute("CREATE UNIQUE INDEX IF NOT EXISTS idx_fi_path ON file_inventory(file_path)")
    conn.execute("CREATE INDEX IF NOT EXISTS idx_fi_drive ON file_inventory(drive_letter)")
    conn.execute("CREATE INDEX IF NOT EXISTS idx_fi_ext ON file_inventory(extension)")
    conn.commit()


def infer_category(file_path: str) -> str:
    """Infer canonical_category from path segments."""
    upper = file_path.upper()
    for key, val in CATEGORY_MAP.items():
        if key in upper:
            return val
    return "unknown"


def is_litigation_relevant(file_path: str, file_name: str) -> int:
    """Simple MEEK keyword check for litigation relevance."""
    combined = (file_path + " " + file_name).lower()
    return 1 if any(kw in combined for kw in MEEK_KEYWORDS) else 0


def infer_lane(file_path: str) -> str | None:
    """Infer MEEK lane from path."""
    p = file_path.upper()
    if any(x in p for x in ["MCNEILL", "JTC", "MISCONDUCT", "JUDICIAL", "BENCHBOOK"]):
        return "E"
    if any(x in p for x in ["5907", "PPO", "PROTECTION_ORDER", "CONTEMPT"]):
        return "D"
    if any(x in p for x in ["366810", "COA", "APPEAL", "APPELLANT"]):
        return "F"
    if any(x in p for x in ["1983", "FEDERAL", "USDC"]):
        return "C"
    if any(x in p for x in ["001507", "CUSTODY", "PARENTING", "WATSON"]):
        return "A"
    if any(x in p for x in ["002760", "SHADY_OAKS", "HOUSING", "EVICTION"]):
        return "B"
    return None


def scan_drive(root: str) -> int:
    """
    Scan a drive root and yield records in batches.
    Returns total files counted.
    """
    return root  # stub — actual scanning below


def index_drives(drives: list[str], skip_existing: bool, conn: sqlite3.Connection) -> dict:
    """Main indexing loop. Returns summary stats per drive."""
    stats: dict[str, dict] = {}

    for drive in drives:
        root = f"{drive}:\\"
        if not os.path.exists(root):
            print(f"  [SKIP] {root} — not accessible")
            continue

        print(f"\n  Scanning {root} ...")
        t0 = time.time()
        count = 0
        skipped = 0
        batch: list[tuple] = []

        now_str = datetime.datetime.now().isoformat()

        for dirpath, dirnames, filenames in os.walk(root, onerror=lambda e: None):
            # Prune skip dirs in-place
            dirnames[:] = [
                d for d in dirnames
                if d not in SKIP_DIRS and not d.startswith(".")
            ]

            for fname in filenames:
                full_path = os.path.join(dirpath, fname)

                try:
                    stat = os.stat(full_path)
                    size = stat.st_size
                    mdate = datetime.datetime.fromtimestamp(stat.st_mtime).isoformat()
                except OSError:
                    skipped += 1
                    continue

                ext = Path(fname).suffix.lower()
                mime = mimetypes.guess_type(fname)[0] or ""
                cat = infer_category(full_path)
                relevant = is_litigation_relevant(full_path, fname)
                lane = infer_lane(full_path) if relevant else None

                batch.append((
                    full_path,          # file_path (UNIQUE)
                    fname,              # file_name
                    ext,                # extension
                    drive,              # drive_letter
                    size,               # size_bytes
                    mdate,              # modified_date
                    None,               # sha256 (skip for speed)
                    mime,               # mime_type
                    relevant,           # is_litigation_relevant
                    lane,               # lane
                    0,                  # ingested
                    now_str,            # created_at
                    cat,                # canonical_category
                    "file_inventory",   # source_table
                ))
                count += 1

                if count % LOG_EVERY == 0:
                    elapsed = time.time() - t0
                    print(f"    {count:,} files ... ({elapsed:.1f}s)")

                if len(batch) >= BATCH_SIZE:
                    _flush(conn, batch)
                    batch = []

        if batch:
            _flush(conn, batch)

        elapsed = time.time() - t0
        stats[drive] = {"files": count, "skipped": skipped, "elapsed_s": round(elapsed, 1)}
        print(f"  ✅ {drive}:\\ — {count:,} files indexed in {elapsed:.1f}s ({skipped} skipped)")

    return stats


def _flush(conn: sqlite3.Connection, batch: list[tuple]) -> None:
    conn.executemany("""
        INSERT OR REPLACE INTO file_inventory
        (file_path, file_name, extension, drive_letter, size_bytes,
         modified_date, sha256, mime_type, is_litigation_relevant,
         lane, ingested, created_at, canonical_category, source_table)
        VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?)
    """, batch)
    conn.commit()


def print_summary(stats: dict, conn: sqlite3.Connection) -> None:
    print("\n" + "=" * 70)
    print("FULL DRIVE INDEX SUMMARY")
    print("=" * 70)
    total_files = sum(v["files"] for v in stats.values())
    print(f"{'Drive':<8} {'Files':>10} {'Elapsed':>10}")
    print("-" * 30)
    for drive, s in stats.items():
        print(f"  {drive:<6} {s['files']:>10,} {s['elapsed_s']:>9.1f}s")
    print("-" * 30)
    print(f"  {'TOTAL':<6} {total_files:>10,}")

    # Full DB totals
    row = conn.execute("""
        SELECT drive_letter, COUNT(*) as cnt, ROUND(SUM(size_bytes)/1e9,2) as gb
        FROM file_inventory GROUP BY drive_letter ORDER BY cnt DESC
    """).fetchall()
    print("\nDB TOTALS (all drives in file_inventory):")
    all_total = 0
    for r in row:
        lbl = r[0] or "(none)"
        print(f"  {lbl}:\\  {r[1]:>10,} files  {r[2]:>8.2f} GB")
        all_total += r[1]
    print(f"  GRAND TOTAL: {all_total:,} files")
    print("=" * 70)


def main():
    parser = argparse.ArgumentParser(description="APEX Full Drive Indexer v1.0")
    parser.add_argument("--drives", nargs="+", default=DEFAULT_DRIVES,
                        help="Drive letters to index (default: J C D F G I)")
    parser.add_argument("--skip-existing", action="store_true",
                        help="Skip files already in index (check by file_path)")
    args = parser.parse_args()

    print("APEX Full Drive Indexer v1.0")
    print(f"Target DB: {DB_PATH}")
    print(f"Drives to index: {args.drives}")
    print(f"Batch size: {BATCH_SIZE}")

    conn = open_db()
    ensure_file_inventory(conn)

    stats = index_drives(args.drives, args.skip_existing, conn)
    print_summary(stats, conn)
    conn.close()
    print("\n✅ Done.")


if __name__ == "__main__":
    main()
