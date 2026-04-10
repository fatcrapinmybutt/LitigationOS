#!/usr/bin/env python3
"""
Phase C ONLY — Copy 93K+ canonical files → J:\CONSOLIDATED\
Runs standalone, resumable, with progress reporting.
Designed for long-running USB copy (hours).
"""
import sqlite3, shutil, os, sys, time
from datetime import datetime

STATE_DB = r"D:\LitigationOS_tmp\consolidation_state.db"
TARGET_ROOT = r"J:\CONSOLIDATED"
LOG_FILE = r"D:\LitigationOS_tmp\phase_c_execution.log"

DRIVE_MAP = {'D:': 'D_DRIVE', 'F:': 'F_DRIVE', 'G:': 'G_DRIVE', 'I:': 'I_DRIVE'}
DRIVE_ORDER = ['F:', 'D:', 'G:', 'I:']  # smallest → largest

_log_fh = None

def log(msg, level='INFO'):
    global _log_fh
    if _log_fh is None:
        _log_fh = open(LOG_FILE, 'a', encoding='utf-8', buffering=1)
    ts = datetime.now().strftime('%H:%M:%S')
    line = f"[{ts}] [{level}] {msg}"
    print(line, flush=True)
    _log_fh.write(line + '\n')

def fmt_bytes(b):
    if b < 1024: return f"{b} B"
    if b < 1048576: return f"{b/1024:.1f} KB"
    if b < 1073741824: return f"{b/1048576:.1f} MB"
    return f"{b/1073741824:.2f} GB"

def fmt_dur(s):
    if s < 60: return f"{s:.0f}s"
    if s < 3600: return f"{s//60:.0f}m {s%60:.0f}s"
    return f"{s//3600:.0f}h {(s%3600)//60:.0f}m"

def get_db():
    db = sqlite3.connect(STATE_DB)
    db.row_factory = sqlite3.Row
    db.execute("PRAGMA busy_timeout = 60000")
    db.execute("PRAGMA journal_mode = WAL")
    db.execute("PRAGMA cache_size = -32000")
    return db

def main():
    log("=" * 70)
    log("PHASE C: COPY CANONICAL FILES → J:\\CONSOLIDATED\\")
    log(f"Started: {datetime.now().isoformat()}")
    log("=" * 70)

    db = get_db()
    t0 = time.time()

    # Stats
    to_copy = db.execute("""
        SELECT source_drive, COUNT(*) as cnt, COALESCE(SUM(file_size), 0) as bytes
        FROM file_inventory
        WHERE copy_status = 'CANONICAL'
        GROUP BY source_drive
        ORDER BY COALESCE(SUM(file_size), 0) ASC
    """).fetchall()

    total_files = sum(r['cnt'] for r in to_copy)
    total_bytes = sum(r['bytes'] for r in to_copy)

    already = db.execute(
        "SELECT COUNT(*) FROM file_inventory WHERE copy_status IN ('COPIED','VERIFIED')"
    ).fetchone()[0]

    log(f"  Canonical to copy: {total_files:,} files ({fmt_bytes(total_bytes)})")
    log(f"  Already copied/verified: {already:,}")
    for r in to_copy:
        log(f"    {r['source_drive']}: {r['cnt']:,} files ({fmt_bytes(r['bytes'])})")

    if total_files == 0:
        log("Nothing to copy — all files already processed!")
        db.close()
        return

    # Ensure target dirs exist
    for drive_dir in DRIVE_MAP.values():
        os.makedirs(os.path.join(TARGET_ROOT, drive_dir), exist_ok=True)

    global_copied = 0
    global_existed = 0
    global_errors = 0
    global_missing = 0
    global_bytes_copied = 0
    last_report = time.time()

    for drive in DRIVE_ORDER:
        drive_dir = DRIVE_MAP.get(drive)
        if not drive_dir:
            continue

        files = db.execute("""
            SELECT id, source_path, file_name, file_size
            FROM file_inventory
            WHERE source_drive = ? AND copy_status = 'CANONICAL'
            ORDER BY source_path
        """, (drive,)).fetchall()

        if not files:
            log(f"  {drive}: No canonical files to copy")
            continue

        drive_total = len(files)
        log(f"  {drive}: Starting {drive_total:,} files...")
        drive_copied = 0
        drive_existed = 0
        drive_errors = 0
        drive_missing = 0

        for idx, f in enumerate(files):
            src = f['source_path']

            # Build target path preserving directory structure
            rel_path = src[len(drive):]  # Strip "X:" → "\path\to\file"
            if rel_path.startswith('\\') or rel_path.startswith('/'):
                rel_path = rel_path[1:]
            dst = os.path.join(TARGET_ROOT, drive_dir, rel_path)

            # Already exists at target?
            if os.path.isfile(dst):
                db.execute("""
                    UPDATE file_inventory
                    SET copy_status='COPIED', target_path=?, copied_at=datetime('now')
                    WHERE id=?
                """, (dst, f['id']))
                drive_existed += 1
                global_existed += 1
                global_bytes_copied += (f['file_size'] or 0)
                continue

            # Source still exists?
            if not os.path.isfile(src):
                db.execute("UPDATE file_inventory SET copy_status='SOURCE_MISSING' WHERE id=?", (f['id'],))
                drive_missing += 1
                global_missing += 1
                continue

            # Copy file
            try:
                os.makedirs(os.path.dirname(dst), exist_ok=True)
                shutil.copy2(src, dst)
                db.execute("""
                    UPDATE file_inventory
                    SET copy_status='COPIED', target_path=?, copied_at=datetime('now')
                    WHERE id=?
                """, (dst, f['id']))
                drive_copied += 1
                global_copied += 1
                global_bytes_copied += (f['file_size'] or 0)

            except Exception as e:
                db.execute("UPDATE file_inventory SET copy_status='COPY_ERROR' WHERE id=?", (f['id'],))
                drive_errors += 1
                global_errors += 1
                if drive_errors <= 10:
                    log(f"    ERROR [{drive}]: {src}: {e}", 'ERROR')

            # Progress report every 30 seconds
            now = time.time()
            if now - last_report > 30:
                elapsed = now - t0
                total_done = global_copied + global_existed
                pct = total_done / total_files * 100 if total_files > 0 else 0
                rate = global_bytes_copied / elapsed if elapsed > 0 else 0
                remaining_bytes = total_bytes - global_bytes_copied
                eta = remaining_bytes / rate if rate > 0 else 0
                log(f"  PROGRESS: {total_done:,}/{total_files:,} ({pct:.1f}%) | "
                    f"{fmt_bytes(global_bytes_copied)}/{fmt_bytes(total_bytes)} | "
                    f"{fmt_bytes(rate)}/s | ETA {fmt_dur(eta)} | "
                    f"Drive {drive} {idx+1}/{drive_total}")
                last_report = now
                db.commit()

        db.commit()
        log(f"  {drive} DONE: {drive_copied:,} copied, {drive_existed:,} existed, "
            f"{drive_errors} errors, {drive_missing} missing")

    elapsed = time.time() - t0
    log("")
    log("═" * 70)
    log(f"PHASE C COMPLETE in {fmt_dur(elapsed)}")
    log(f"  New copies:      {global_copied:,}")
    log(f"  Already existed:  {global_existed:,}")
    log(f"  Errors:          {global_errors:,}")
    log(f"  Source missing:   {global_missing:,}")
    log(f"  Bytes processed: {fmt_bytes(global_bytes_copied)}")
    log("═" * 70)

    # Final status
    for status in ('CANONICAL', 'COPIED', 'VERIFIED', 'DUPLICATE_SKIP', 'EMPTY_SKIP', 'COPY_ERROR', 'SOURCE_MISSING'):
        cnt = db.execute("SELECT COUNT(*) FROM file_inventory WHERE copy_status = ?", (status,)).fetchone()[0]
        log(f"  {status:20s}: {cnt:>10,}")

    db.close()
    if _log_fh:
        _log_fh.close()

if __name__ == '__main__':
    main()
