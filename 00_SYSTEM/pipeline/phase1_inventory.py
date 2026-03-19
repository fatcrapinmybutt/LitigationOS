"""
OMEGA Phase 1: SQLite-Backed Recursive Inventory
Catalogs every file in scans/ into an indexed SQLite database.
"""
import json as _json
import os
import sqlite3
import sys
import time
from pathlib import Path

from config import (
    SCANS_ROOT, SKIP_DIRS, SKIP_EXTENSIONS, SKIP_PREFIXES,
    LEGAL_EXTENSIONS, sha256_file, get_cyclepack_dir,
    report_progress,
)
from safety import write_phase_checkpoint, is_phase_done


DB_SCHEMA = """
CREATE TABLE IF NOT EXISTS files (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    file_path TEXT NOT NULL UNIQUE,
    file_name TEXT NOT NULL,
    extension TEXT,
    size_bytes INTEGER,
    modified_time TEXT,
    sha256 TEXT,
    depth INTEGER,
    parent_dir TEXT,
    top_bucket TEXT,
    is_legal_content INTEGER DEFAULT 0,
    is_canonical INTEGER DEFAULT 0,
    canonical_sha256 TEXT,
    category TEXT,
    priority TEXT,
    meek_lanes TEXT,
    content_score REAL DEFAULT 0.0,
    macro_buckets TEXT,
    signal_summary TEXT
);
CREATE INDEX IF NOT EXISTS idx_sha256 ON files(sha256);
CREATE INDEX IF NOT EXISTS idx_extension ON files(extension);
CREATE INDEX IF NOT EXISTS idx_top_bucket ON files(top_bucket);
CREATE INDEX IF NOT EXISTS idx_priority ON files(priority);
CREATE INDEX IF NOT EXISTS idx_canonical ON files(is_canonical);
"""


def should_skip_dir(name: str) -> bool:
    if name in SKIP_DIRS:
        return True
    for prefix in SKIP_PREFIXES:
        if name.startswith(prefix):
            return True
    return False


def get_top_bucket(path: Path) -> str:
    try:
        rel = path.relative_to(SCANS_ROOT)
        parts = rel.parts
        return parts[0] if parts else "root"
    except ValueError:
        return "unknown"


def run_inventory(cycle_dir: Path, dry_run: bool = False) -> Path:
    db_path = cycle_dir / "inventory.db"
    cycle_dir.mkdir(parents=True, exist_ok=True)

    if is_phase_done(cycle_dir, "phase1"):
        print("[PHASE1] Already complete, skipping", file=sys.stderr)
        return db_path

    conn = sqlite3.connect(str(db_path))
    try:
        conn.execute("PRAGMA journal_mode=WAL")
        conn.execute("PRAGMA synchronous=NORMAL")
        conn.executescript(DB_SCHEMA)

        start = time.time()
        total = 0
        skipped = 0
        errors = 0
        batch = []
        BATCH_SIZE = 5000
        RESUME_INTERVAL = 50000
        resume_marker_path = cycle_dir / "phase1_resume.json"

        # Load resume state if available
        resumed_from = None
        resume_skip_dirs: set[str] = set()
        if resume_marker_path.exists():
            try:
                rdata = _json.loads(resume_marker_path.read_text(encoding="utf-8"))
                resumed_from = rdata.get("last_dir")
                total = rdata.get("files_so_far", 0)
                if resumed_from:
                    resume_skip_dirs = {resumed_from}
                    print(f"[PHASE1] Resuming after dir: {resumed_from} ({total:,} files so far)", file=sys.stderr)
            except Exception:
                pass

        print(f"[PHASE1] Scanning {SCANS_ROOT}...", file=sys.stderr)

        # Dry-run: sample first 500 files to validate logic, then extrapolate
        DRY_RUN_LIMIT = 500
        last_dir_processed = None
        still_skipping = resumed_from is not None

        for dirpath, dirnames, filenames in os.walk(str(SCANS_ROOT)):
            # Prune skip dirs in-place
            dirnames[:] = [d for d in dirnames if not should_skip_dir(d)]

            dp = Path(dirpath)

            # Resume logic: skip directories already processed in a prior run
            if still_skipping:
                if str(dp) == resumed_from:
                    still_skipping = False
                else:
                    continue

            last_dir_processed = str(dp)

            try:
                depth = len(dp.relative_to(SCANS_ROOT).parts)
            except ValueError:
                depth = 0

            for fname in filenames:
                if dry_run and total >= DRY_RUN_LIMIT:
                    break

                fpath = dp / fname
                ext = fpath.suffix.lower()

                if ext in SKIP_EXTENSIONS:
                    skipped += 1
                    continue

                try:
                    stat = fpath.stat()
                    file_hash = None
                    is_legal = 1 if ext in LEGAL_EXTENSIONS else 0

                    # Only hash files under 500MB; skip hashing entirely in dry-run
                    if not dry_run and stat.st_size < 500_000_000:
                        try:
                            file_hash = sha256_file(fpath)
                        except (PermissionError, OSError):
                            file_hash = None

                    batch.append((
                        str(fpath),
                        fname,
                        ext if ext else None,
                        stat.st_size,
                        time.strftime("%Y-%m-%dT%H:%M:%S", time.localtime(stat.st_mtime)),
                        file_hash,
                        depth,
                        str(dp),
                        get_top_bucket(fpath),
                        is_legal,
                    ))
                    total += 1

                    if len(batch) >= BATCH_SIZE:
                        if not dry_run:
                            conn.executemany(
                                "INSERT OR IGNORE INTO files (file_path, file_name, extension, size_bytes, modified_time, sha256, depth, parent_dir, top_bucket, is_legal_content) VALUES (?,?,?,?,?,?,?,?,?,?)",
                                batch,
                            )
                            conn.commit()
                        batch = []
                        report_progress("phase1", total, 430000)
                        # Write resume marker every RESUME_INTERVAL files
                        if not dry_run and total % RESUME_INTERVAL < BATCH_SIZE and last_dir_processed:
                            resume_marker_path.write_text(_json.dumps({
                                "last_dir": last_dir_processed,
                                "files_so_far": total,
                            }), encoding="utf-8")

                except (PermissionError, OSError) as e:
                    errors += 1
                    continue

            if dry_run and total >= DRY_RUN_LIMIT:
                break

        # Flush remaining batch
        if batch and not dry_run:
            conn.executemany(
                "INSERT OR IGNORE INTO files (file_path, file_name, extension, size_bytes, modified_time, sha256, depth, parent_dir, top_bucket, is_legal_content) VALUES (?,?,?,?,?,?,?,?,?,?)",
                batch,
            )
            conn.commit()

        elapsed = time.time() - start

        # Stats
        stats = {
            "total_files": total,
            "skipped": skipped,
            "errors": errors,
            "elapsed_seconds": round(elapsed, 1),
            "db_path": str(db_path),
        }

        if dry_run:
            print(f"[PHASE1] DRY RUN: sampled {total:,} files, {skipped:,} skipped, {errors} errors in {elapsed:.0f}s", file=sys.stderr)
        else:
            import json
            (cycle_dir / "inventory_stats.json").write_text(json.dumps(stats, indent=2), encoding="utf-8")
            write_phase_checkpoint(cycle_dir, "phase1", {"status": "done", "rows": total, "elapsed": f"{elapsed:.0f}s"})
            # Clean up resume marker on successful completion
            if resume_marker_path.exists():
                resume_marker_path.unlink()
            print(f"[PHASE1] Done: {total:,} files cataloged, {skipped:,} skipped, {errors} errors in {elapsed:.0f}s", file=sys.stderr)
    finally:
        conn.close()
    return db_path


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Phase 1: Inventory")
    parser.add_argument("--cycle-ts", default=None)
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    from config import CYCLE_TS
    ts = args.cycle_ts or CYCLE_TS
    cycle_dir = get_cyclepack_dir(ts)
    run_inventory(cycle_dir, args.dry_run)
