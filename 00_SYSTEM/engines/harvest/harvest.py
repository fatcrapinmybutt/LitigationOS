#!/usr/bin/env python3
"""Harvest Engine CLI — Permanent, zero-API evidence ingestion pipeline.

Scans drives/directories for PDF/DOCX/TXT/CSV/JSON files, extracts text,
classifies by MEEK litigation lane, detects actors/authorities/dates/quotes,
and persists everything to litigation_context.db.

Usage:
    python harvest.py --drive G:                  # Full drive scan
    python harvest.py --path "G:\\custody scanned_0001.pdf"  # Single file
    python harvest.py --drive C: --mode quick      # Quick mode (skip >50MB)
    python harvest.py --drive G: --lane A          # Only custody lane
    python harvest.py --drive G: --dry-run         # Preview without DB writes
    python harvest.py --audit                      # Show harvest stats

Requires: Python 3.12+, pypdfium2 (PDF), python-docx (DOCX), orjson (JSON)
Optional libs degrade gracefully — TXT/CSV/MD always work.
"""

import argparse
import hashlib
import logging
import os
import re
import sqlite3
import sys
import time
from datetime import datetime
from pathlib import Path
from typing import Optional

# Engine imports (relative — run as module or add parent to path)
try:
    from . import config
    from .extractor import extract_file
    from .classifier import classify_text, classify_file_by_path
except ImportError:
    # Allow direct execution: python harvest.py
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))
    from engines.harvest import config
    from engines.harvest.extractor import extract_file
    from engines.harvest.classifier import classify_text, classify_file_by_path

logger = logging.getLogger("harvest")

# ── DB Schema ────────────────────────────────────────────────────────────────

EVIDENCE_QUOTES_DDL = """
CREATE TABLE IF NOT EXISTS harvest_evidence (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    quote_text TEXT NOT NULL,
    source_file TEXT,
    page_number INTEGER,
    category TEXT,
    lane TEXT,
    actor TEXT,
    doc_type TEXT,
    confidence REAL DEFAULT 0.7,
    harvested_at TEXT DEFAULT (datetime('now')),
    sha256 TEXT,
    UNIQUE(quote_text, source_file)
)
"""

FILE_INVENTORY_DDL = """
CREATE TABLE IF NOT EXISTS harvest_files (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    file_path TEXT UNIQUE NOT NULL,
    file_name TEXT,
    file_size INTEGER,
    file_ext TEXT,
    sha256 TEXT,
    primary_lane TEXT,
    doc_type TEXT,
    actors TEXT,
    authorities TEXT,
    dates TEXT,
    page_count INTEGER DEFAULT 0,
    text_length INTEGER DEFAULT 0,
    has_child_name INTEGER DEFAULT 0,
    status TEXT DEFAULT 'processed',
    harvested_at TEXT DEFAULT (datetime('now')),
    error_msg TEXT
)
"""

HARVEST_RUNS_DDL = """
CREATE TABLE IF NOT EXISTS harvest_runs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    run_id TEXT UNIQUE,
    drive TEXT,
    path TEXT,
    mode TEXT,
    started_at TEXT,
    finished_at TEXT,
    files_scanned INTEGER DEFAULT 0,
    files_processed INTEGER DEFAULT 0,
    files_skipped INTEGER DEFAULT 0,
    files_errored INTEGER DEFAULT 0,
    quotes_found INTEGER DEFAULT 0,
    authorities_found INTEGER DEFAULT 0,
    actors_found INTEGER DEFAULT 0,
    summary TEXT
)
"""

# Also persist to the MAIN evidence_quotes table for cross-system compatibility
EVIDENCE_QUOTES_INSERT = """
INSERT OR IGNORE INTO evidence_quotes
    (quote_text, source_file, page_number, category, lane, confidence, harvested_at)
VALUES (?, ?, ?, ?, ?, ?, datetime('now'))
"""

HARVEST_EVIDENCE_INSERT = """
INSERT OR IGNORE INTO harvest_evidence
    (quote_text, source_file, page_number, category, lane, actor, doc_type, confidence, sha256)
VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
"""

HARVEST_FILE_INSERT = """
INSERT OR REPLACE INTO harvest_files
    (file_path, file_name, file_size, file_ext, sha256, primary_lane, doc_type,
     actors, authorities, dates, page_count, text_length, has_child_name, status, error_msg)
VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
"""


class HarvestStats:
    """Accumulates statistics for a harvest run."""
    __slots__ = (
        "files_scanned", "files_processed", "files_skipped", "files_errored",
        "quotes_found", "authorities_found", "actors_found", "lanes",
        "doc_types", "errors", "start_time",
    )

    def __init__(self):
        self.files_scanned = 0
        self.files_processed = 0
        self.files_skipped = 0
        self.files_errored = 0
        self.quotes_found = 0
        self.authorities_found = 0
        self.actors_found = 0
        self.lanes = {}
        self.doc_types = {}
        self.errors = []
        self.start_time = time.time()

    def record_lane(self, lane: str):
        self.lanes[lane] = self.lanes.get(lane, 0) + 1

    def record_doc_type(self, dt: str):
        self.doc_types[dt] = self.doc_types.get(dt, 0) + 1

    def elapsed(self) -> float:
        return time.time() - self.start_time

    def summary(self) -> str:
        lines = [
            f"\n{'='*60}",
            f"  HARVEST ENGINE — Run Complete",
            f"{'='*60}",
            f"  Duration:       {self.elapsed():.1f}s",
            f"  Files scanned:  {self.files_scanned}",
            f"  Files processed:{self.files_processed}",
            f"  Files skipped:  {self.files_skipped}",
            f"  Files errored:  {self.files_errored}",
            f"  Quotes found:   {self.quotes_found}",
            f"  Authorities:    {self.authorities_found}",
            f"  Actors detected:{self.actors_found}",
            f"  Lane distribution:",
        ]
        for lane, count in sorted(self.lanes.items()):
            lines.append(f"    Lane {lane}: {count} files")
        if self.doc_types:
            lines.append(f"  Document types:")
            for dt, count in sorted(self.doc_types.items(), key=lambda x: -x[1])[:10]:
                lines.append(f"    {dt}: {count}")
        if self.errors:
            lines.append(f"  Errors ({len(self.errors)}):")
            for err in self.errors[:5]:
                lines.append(f"    {err[:120]}")
            if len(self.errors) > 5:
                lines.append(f"    ... and {len(self.errors)-5} more")
        lines.append(f"{'='*60}")
        return "\n".join(lines)


def get_db_connection(db_path: Optional[Path] = None) -> sqlite3.Connection:
    """Open DB with mandatory PRAGMAs (Rule 18)."""
    db = db_path or config.CENTRAL_DB
    conn = sqlite3.connect(str(db), timeout=120)
    conn.execute("PRAGMA busy_timeout = 60000")
    conn.execute("PRAGMA journal_mode = WAL")
    conn.execute("PRAGMA cache_size = -32000")
    conn.execute("PRAGMA temp_store = MEMORY")
    conn.execute("PRAGMA synchronous = NORMAL")
    return conn


def init_harvest_tables(conn: sqlite3.Connection):
    """Create harvest-specific tables if they don't exist."""
    conn.execute(EVIDENCE_QUOTES_DDL)
    conn.execute(FILE_INVENTORY_DDL)
    conn.execute(HARVEST_RUNS_DDL)
    conn.execute("""
        CREATE INDEX IF NOT EXISTS idx_harvest_files_lane
        ON harvest_files(primary_lane)
    """)
    conn.execute("""
        CREATE INDEX IF NOT EXISTS idx_harvest_files_sha
        ON harvest_files(sha256)
    """)
    conn.execute("""
        CREATE INDEX IF NOT EXISTS idx_harvest_evidence_lane
        ON harvest_evidence(lane)
    """)
    conn.commit()


def check_evidence_quotes_schema(conn: sqlite3.Connection) -> bool:
    """Verify evidence_quotes table has the columns we need (Rule 16)."""
    try:
        cols = {row[1] for row in conn.execute("PRAGMA table_info(evidence_quotes)")}
        required = {"quote_text", "source_file", "lane"}
        return required.issubset(cols)
    except Exception:
        return False


def scan_directory(root: Path, mode: str = "deep", lane_filter: Optional[str] = None) -> list:
    """Recursively find extractable files under root."""
    files = []
    all_exts = config.EXTRACTABLE | config.ARCHIVE_EXTS | config.IMAGE_EXTS | config.DB_EXTS

    for dirpath, dirnames, filenames in os.walk(str(root)):
        # Skip hidden dirs, __pycache__, .git, node_modules
        dirnames[:] = [d for d in dirnames if not d.startswith((".", "__")) and d != "node_modules"]

        for fname in filenames:
            fpath = Path(dirpath) / fname
            ext = fpath.suffix.lower()

            if ext not in all_exts:
                continue

            # Quick mode skips large files
            try:
                fsize = fpath.stat().st_size
            except OSError:
                continue

            if mode == "quick" and fsize > 50 * 1024 * 1024:
                continue
            if fsize > config.MAX_FILE_SIZE:
                continue
            if fsize == 0:
                continue

            # Optional: pre-filter by filename lane classification
            if lane_filter:
                pre = classify_file_by_path(str(fpath))
                if pre and pre != lane_filter:
                    continue

            files.append(fpath)

    return files


def process_file(fpath: Path, stats: HarvestStats) -> Optional[dict]:
    """Extract + classify a single file. Returns result dict or None on error."""
    stats.files_scanned += 1
    ext = fpath.suffix.lower()

    # Skip non-extractable (images, archives, DBs handled separately)
    if ext in config.ARCHIVE_EXTS or ext in config.IMAGE_EXTS or ext in config.DB_EXTS:
        stats.files_skipped += 1
        return None

    if ext not in config.EXTRACTABLE:
        stats.files_skipped += 1
        return None

    try:
        extraction = extract_file(str(fpath))
        if extraction is None or not extraction.text or len(extraction.text.strip()) < config.MIN_TEXT_LENGTH:
            stats.files_skipped += 1
            return None

        classification = classify_text(extraction.text, filename=fpath.name)

        stats.files_processed += 1
        stats.quotes_found += len(classification.quotes)
        stats.authorities_found += len(classification.authorities)
        stats.actors_found += len(classification.actors)
        stats.record_lane(classification.primary_lane)
        stats.record_doc_type(classification.doc_type)

        return {
            "path": str(fpath),
            "name": fpath.name,
            "size": fpath.stat().st_size,
            "ext": ext,
            "sha256": extraction.sha256,
            "text": extraction.text,
            "page_count": extraction.page_count,
            "text_length": len(extraction.text),
            "lane": classification.primary_lane,
            "doc_type": classification.doc_type,
            "actors": classification.actors,
            "authorities": classification.authorities,
            "dates": classification.dates,
            "quotes": classification.quotes,
            "has_child_name": classification.has_child_name,
        }

    except Exception as e:
        stats.files_errored += 1
        stats.errors.append(f"{fpath.name}: {e}")
        logger.error("Error processing %s: %s", fpath, e)
        return None


def persist_result(conn: sqlite3.Connection, result: dict, has_eq_table: bool):
    """Persist one processed file's results to DB."""
    # 1. File inventory
    actors_str = "; ".join(f"{a[0]}({a[1]})" for a in result["actors"][:10])
    auth_str = "; ".join(f"{a[0]}:{a[1]}" for a in result["authorities"][:20])
    dates_str = "; ".join(result["dates"][:20])

    conn.execute(HARVEST_FILE_INSERT, (
        result["path"], result["name"], result["size"], result["ext"],
        result["sha256"], result["lane"], result["doc_type"],
        actors_str, auth_str, dates_str,
        result["page_count"], result["text_length"],
        1 if result["has_child_name"] else 0,
        "processed", None,
    ))

    # 2. Quotes → harvest_evidence
    for quote in result["quotes"]:
        primary_actor = result["actors"][0][0] if result["actors"] else None
        conn.execute(HARVEST_EVIDENCE_INSERT, (
            quote, result["path"], 1, result["doc_type"],
            result["lane"], primary_actor, result["doc_type"],
            0.7, result["sha256"],
        ))

    # 3. Also persist to main evidence_quotes table if it exists
    if has_eq_table:
        for quote in result["quotes"]:
            try:
                conn.execute(EVIDENCE_QUOTES_INSERT, (
                    quote, result["path"], 1, result["doc_type"],
                    result["lane"], 0.7,
                ))
            except sqlite3.IntegrityError:
                pass  # duplicate — skip

    # 4. Persist authorities to harvest_evidence as authority citations
    for auth_type, citation in result["authorities"]:
        try:
            conn.execute(HARVEST_EVIDENCE_INSERT, (
                f"[AUTHORITY] {auth_type} {citation}",
                result["path"], 1, "authority",
                result["lane"], None, result["doc_type"],
                0.8, result["sha256"],
            ))
        except sqlite3.IntegrityError:
            pass


def run_harvest(
    root: Path,
    db_path: Optional[Path] = None,
    mode: str = "deep",
    lane_filter: Optional[str] = None,
    batch_size: int = 100,
    dry_run: bool = False,
) -> HarvestStats:
    """Main harvest pipeline: scan → extract → classify → persist."""
    stats = HarvestStats()
    run_id = f"harvest_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{root.drive or root.name}"

    logger.info("Starting harvest: root=%s mode=%s lane=%s dry_run=%s",
                root, mode, lane_filter, dry_run)
    print(f"\n[HARVEST] Scanning {root} (mode={mode})...", file=sys.stderr)

    # Scan for files
    files = scan_directory(root, mode=mode, lane_filter=lane_filter)
    print(f"[HARVEST] Found {len(files)} extractable files", file=sys.stderr)

    if not files:
        print("[HARVEST] No files found. Done.", file=sys.stderr)
        return stats

    conn = None
    has_eq_table = False

    if not dry_run:
        conn = get_db_connection(db_path)
        init_harvest_tables(conn)
        has_eq_table = check_evidence_quotes_schema(conn)

        # Record run start
        conn.execute(
            "INSERT OR IGNORE INTO harvest_runs (run_id, drive, path, mode, started_at) VALUES (?,?,?,?,?)",
            (run_id, str(root.drive or ""), str(root), mode, datetime.now().isoformat()),
        )
        conn.commit()

    batch_count = 0

    for i, fpath in enumerate(files):
        if (i + 1) % 25 == 0 or i == 0:
            pct = ((i + 1) / len(files)) * 100
            print(f"[HARVEST] [{pct:5.1f}%] Processing {i+1}/{len(files)}: {fpath.name}",
                  file=sys.stderr)

        result = process_file(fpath, stats)
        if result is None:
            continue

        if not dry_run and conn:
            try:
                persist_result(conn, result, has_eq_table)
                batch_count += 1

                if batch_count >= batch_size:
                    conn.commit()
                    batch_count = 0
            except Exception as e:
                logger.error("DB persist error for %s: %s", fpath, e)
                stats.errors.append(f"DB: {fpath.name}: {e}")

    # Final commit
    if conn and not dry_run:
        try:
            conn.commit()
            # Record run completion
            conn.execute("""
                UPDATE harvest_runs SET
                    finished_at = ?,
                    files_scanned = ?,
                    files_processed = ?,
                    files_skipped = ?,
                    files_errored = ?,
                    quotes_found = ?,
                    authorities_found = ?,
                    actors_found = ?,
                    summary = ?
                WHERE run_id = ?
            """, (
                datetime.now().isoformat(),
                stats.files_scanned, stats.files_processed,
                stats.files_skipped, stats.files_errored,
                stats.quotes_found, stats.authorities_found,
                stats.actors_found, stats.summary(),
                run_id,
            ))
            conn.commit()
        except Exception as e:
            logger.error("Final commit error: %s", e)
        finally:
            conn.close()

    return stats


def run_single_file(
    fpath: Path,
    db_path: Optional[Path] = None,
    dry_run: bool = False,
) -> HarvestStats:
    """Harvest a single file."""
    stats = HarvestStats()

    if not fpath.exists():
        print(f"[ERROR] File not found: {fpath}", file=sys.stderr)
        return stats

    result = process_file(fpath, stats)

    if result and not dry_run:
        conn = get_db_connection(db_path)
        init_harvest_tables(conn)
        has_eq_table = check_evidence_quotes_schema(conn)
        persist_result(conn, result, has_eq_table)
        conn.commit()
        conn.close()

    if result:
        print(f"\n  File:    {result['name']}", file=sys.stderr)
        print(f"  Lane:    {result['lane']}", file=sys.stderr)
        print(f"  Type:    {result['doc_type']}", file=sys.stderr)
        print(f"  Pages:   {result['page_count']}", file=sys.stderr)
        print(f"  Quotes:  {len(result['quotes'])}", file=sys.stderr)
        print(f"  Actors:  {[a[0] for a in result['actors']]}", file=sys.stderr)
        print(f"  Auth:    {len(result['authorities'])} citations", file=sys.stderr)
        print(f"  Dates:   {result['dates'][:5]}", file=sys.stderr)

    return stats


def run_audit(db_path: Optional[Path] = None):
    """Show harvest statistics from the database."""
    conn = get_db_connection(db_path)

    print(f"\n{'='*60}")
    print(f"  HARVEST ENGINE — Audit Report")
    print(f"{'='*60}")

    # Check if tables exist
    tables = {row[0] for row in conn.execute(
        "SELECT name FROM sqlite_master WHERE type='table'"
    )}

    if "harvest_files" in tables:
        row = conn.execute("SELECT COUNT(*) FROM harvest_files").fetchone()
        print(f"\n  Harvested files: {row[0]}")

        rows = conn.execute("""
            SELECT primary_lane, COUNT(*), SUM(text_length), SUM(page_count)
            FROM harvest_files GROUP BY primary_lane ORDER BY COUNT(*) DESC
        """).fetchall()
        if rows:
            print(f"\n  By Lane:")
            for lane, cnt, tlen, pages in rows:
                print(f"    Lane {lane}: {cnt} files, {tlen or 0:,} chars, {pages or 0} pages")

        rows = conn.execute("""
            SELECT doc_type, COUNT(*) FROM harvest_files
            GROUP BY doc_type ORDER BY COUNT(*) DESC LIMIT 10
        """).fetchall()
        if rows:
            print(f"\n  Top Document Types:")
            for dt, cnt in rows:
                print(f"    {dt}: {cnt}")

    if "harvest_evidence" in tables:
        row = conn.execute("SELECT COUNT(*) FROM harvest_evidence").fetchone()
        print(f"\n  Harvest evidence records: {row[0]}")

        rows = conn.execute("""
            SELECT lane, COUNT(*) FROM harvest_evidence
            GROUP BY lane ORDER BY COUNT(*) DESC
        """).fetchall()
        if rows:
            print(f"\n  Evidence by Lane:")
            for lane, cnt in rows:
                print(f"    Lane {lane}: {cnt}")

    if "harvest_runs" in tables:
        rows = conn.execute("""
            SELECT run_id, started_at, files_processed, quotes_found
            FROM harvest_runs ORDER BY started_at DESC LIMIT 5
        """).fetchall()
        if rows:
            print(f"\n  Recent Runs:")
            for rid, started, fp, qf in rows:
                print(f"    {rid}: {fp} files, {qf} quotes ({started})")

    print(f"\n{'='*60}")
    conn.close()


def main():
    parser = argparse.ArgumentParser(
        description="Harvest Engine — Permanent evidence ingestion pipeline",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python harvest.py --drive G:                   Full drive scan
  python harvest.py --path "G:\\file.pdf"         Single file
  python harvest.py --drive G: --mode quick       Skip large files
  python harvest.py --drive G: --lane A           Only custody lane
  python harvest.py --drive G: --dry-run          Preview, no DB writes
  python harvest.py --audit                       Show harvest stats
        """,
    )

    parser.add_argument("--drive", type=str, help="Drive letter to scan (e.g., G:)")
    parser.add_argument("--path", type=str, help="Specific file or directory path")
    parser.add_argument("--db", type=str, help="Database path (default: litigation_context.db)")
    parser.add_argument("--mode", choices=["quick", "deep"], default="deep",
                        help="Quick skips files >50MB (default: deep)")
    parser.add_argument("--lane", choices=["A", "B", "C", "D", "E", "F"],
                        help="Only process files matching this lane")
    parser.add_argument("--batch-size", type=int, default=100,
                        help="DB commit batch size (default: 100)")
    parser.add_argument("--dry-run", action="store_true",
                        help="Preview without writing to DB")
    parser.add_argument("--audit", action="store_true",
                        help="Show harvest statistics")
    parser.add_argument("--verbose", "-v", action="store_true",
                        help="Enable debug logging")

    args = parser.parse_args()

    # Logging
    level = logging.DEBUG if args.verbose else logging.WARNING
    logging.basicConfig(
        level=level,
        format="%(asctime)s [%(name)s] %(levelname)s: %(message)s",
        handlers=[logging.StreamHandler(sys.stderr)],
    )

    db_path = Path(args.db) if args.db else None

    # Audit mode
    if args.audit:
        run_audit(db_path)
        return

    # Must specify --drive or --path
    if not args.drive and not args.path:
        parser.error("Specify --drive or --path (or --audit for stats)")

    # Single file mode
    if args.path:
        target = Path(args.path)
        if target.is_file():
            stats = run_single_file(target, db_path, args.dry_run)
            print(stats.summary())
            sys.exit(0 if stats.files_errored == 0 else 1)
        elif target.is_dir():
            stats = run_harvest(target, db_path, args.mode, args.lane, args.batch_size, args.dry_run)
            print(stats.summary())
            sys.exit(0 if stats.files_errored == 0 else 1)
        else:
            print(f"[ERROR] Path not found: {target}", file=sys.stderr)
            sys.exit(1)

    # Drive mode
    if args.drive:
        drive = args.drive.rstrip("\\").rstrip("/")
        if not drive.endswith(":"):
            drive += ":"
        root = Path(f"{drive}\\")
        if not root.exists():
            print(f"[ERROR] Drive not accessible: {root}", file=sys.stderr)
            sys.exit(1)

        stats = run_harvest(root, db_path, args.mode, args.lane, args.batch_size, args.dry_run)
        print(stats.summary())
        sys.exit(0 if stats.files_errored == 0 else 1)


if __name__ == "__main__":
    main()
