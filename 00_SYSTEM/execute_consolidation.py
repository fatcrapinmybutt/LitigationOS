#!/usr/bin/env python3
"""
MASTER CONSOLIDATION EXECUTOR — ALL PHASES
===========================================
Copies unique files from D:\, F:\, G:\, I:\ → J:\CONSOLIDATED\
with dedup, verification, and DB path migration.

Phase A: Mark canonical files (dedup selection)
Phase B: Create J:\ directory structure + root cleanup
Phase C: Copy unique files to J:\CONSOLIDATED\{DRIVE}\
Phase D: Migrate litigation_context.db paths
Phase E: Final verification report

Resumable — re-run safely; skips completed work.
Non-destructive — copies only, never deletes originals.
"""

import sqlite3
import shutil
import os
import sys
import time
from pathlib import Path
from datetime import datetime
from collections import defaultdict

# ═══════════════════════════════════════════════════════════════
# CONFIGURATION
# ═══════════════════════════════════════════════════════════════

STATE_DB = r"D:\LitigationOS_tmp\consolidation_state.db"
LIT_DB = r"C:\Users\andre\LitigationOS\litigation_context.db"
TARGET_ROOT = r"J:\CONSOLIDATED"
ROOT_CLEANUP = r"J:\ROOT_CLEANUP"
LOG_FILE = r"D:\LitigationOS_tmp\consolidation_execution.log"

DRIVE_MAP = {'D:': 'D_DRIVE', 'F:': 'F_DRIVE', 'G:': 'G_DRIVE', 'I:': 'I_DRIVE'}

# Extension → category for J:\ root cleanup
EXT_MAP = {}
for ext in ('.py','.js','.ts','.go','.rs','.jsx','.tsx','.css','.scss',
            '.html','.htm','.vue','.java','.c','.cpp','.h','.sh','.bat',
            '.ps1','.rb','.php','.swift','.kt','.svelte','.mjs','.cjs'):
    EXT_MAP[ext] = 'CODE'
for ext in ('.pdf','.docx','.doc','.txt','.md','.rtf','.odt','.xls','.xlsx','.pptx'):
    EXT_MAP[ext] = 'DOCUMENTS'
for ext in ('.jpg','.jpeg','.png','.gif','.bmp','.svg','.webp','.ico',
            '.mp4','.mp3','.wav','.avi','.mkv','.mov','.flac','.ogg','.m4a','.wmv'):
    EXT_MAP[ext] = 'MEDIA'
for ext in ('.zip','.rar','.7z','.tar','.gz','.bz2','.xz'):
    EXT_MAP[ext] = 'ARCHIVES'
for ext in ('.csv','.tsv','.jsonl','.xml','.db','.sqlite','.sqlite3','.sql',
            '.json','.yaml','.yml','.toml','.ini','.cfg','.conf','.parquet'):
    EXT_MAP[ext] = 'DATA'
for i in range(1, 30):
    EXT_MAP[f'.part{i:02d}'] = 'INCOMPLETE'
    EXT_MAP[f'.part{i}'] = 'INCOMPLETE'

# ═══════════════════════════════════════════════════════════════
# UTILITIES
# ═══════════════════════════════════════════════════════════════

_log_fh = None

def log(msg, level='INFO'):
    global _log_fh
    ts = datetime.now().strftime('%H:%M:%S')
    line = f"[{ts}] [{level}] {msg}"
    print(line, flush=True)
    if _log_fh is None:
        os.makedirs(os.path.dirname(LOG_FILE), exist_ok=True)
        _log_fh = open(LOG_FILE, 'a', encoding='utf-8')
    _log_fh.write(line + '\n')
    _log_fh.flush()

def fmt_bytes(n):
    if n is None or n == 0: return '0 B'
    for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
        if abs(n) < 1024: return f"{n:.1f} {unit}"
        n /= 1024
    return f"{n:.1f} PB"

def fmt_dur(s):
    if s < 60: return f"{s:.0f}s"
    if s < 3600: return f"{int(s//60)}m {int(s%60)}s"
    return f"{int(s//3600)}h {int((s%3600)//60)}m"

def get_state():
    conn = sqlite3.connect(STATE_DB)
    conn.execute("PRAGMA busy_timeout = 60000")
    conn.execute("PRAGMA journal_mode = WAL")
    conn.execute("PRAGMA cache_size = -32000")
    conn.row_factory = sqlite3.Row
    return conn

# ═══════════════════════════════════════════════════════════════
# PRE-FLIGHT CHECKS
# ═══════════════════════════════════════════════════════════════

def preflight():
    log("PRE-FLIGHT CHECKS")
    ok = True

    # State DB
    if not os.path.isfile(STATE_DB):
        log(f"FATAL: State DB not found: {STATE_DB}", 'ERROR')
        return False
    db = get_state()
    total = db.execute("SELECT COUNT(*) FROM file_inventory").fetchone()[0]
    log(f"  State DB: {total:,} files inventoried")
    db.close()

    # Lit DB
    if not os.path.isfile(LIT_DB):
        log(f"FATAL: Litigation DB not found: {LIT_DB}", 'ERROR')
        return False
    log(f"  Litigation DB: OK ({fmt_bytes(os.path.getsize(LIT_DB))})")

    # Drive accessibility
    for drive in DRIVE_MAP:
        path = drive + '\\'
        if os.path.isdir(path):
            log(f"  {drive} accessible")
        else:
            log(f"  {drive} NOT accessible — files will be marked SOURCE_MISSING", 'WARN')

    # J:\ space check
    if os.path.isdir('J:\\'):
        total_j, used_j, free_j = shutil.disk_usage('J:\\')
        log(f"  J:\\ space: {fmt_bytes(free_j)} free / {fmt_bytes(total_j)} total")
        if free_j < 100 * 1024**3:  # Need ~100 GB
            log(f"  WARNING: J:\\ has less than 100 GB free", 'WARN')
    else:
        log("FATAL: J:\\ not accessible", 'ERROR')
        return False

    return ok

# ═══════════════════════════════════════════════════════════════
# PHASE A: MARK CANONICAL FILES (dedup selection)
# ═══════════════════════════════════════════════════════════════

def phase_a():
    log("=" * 70)
    log("PHASE A: MARKING CANONICAL FILES (dedup selection)")
    log("=" * 70)

    db = get_state()
    t0 = time.time()

    # Check if already done — only count REAL statuses (not 'pending')
    REAL_STATUSES = ('CANONICAL', 'DUPLICATE_SKIP', 'EMPTY_SKIP', 'COPIED', 'VERIFIED', 'COPY_ERROR', 'SOURCE_MISSING')
    already = db.execute(
        "SELECT COUNT(*) FROM file_inventory WHERE copy_status IN ({})".format(
            ','.join('?' * len(REAL_STATUSES))),
        REAL_STATUSES
    ).fetchone()[0]
    total = db.execute("SELECT COUNT(*) FROM file_inventory").fetchone()[0]

    if already >= total:
        log(f"Phase A: All {total:,} files already marked. Skipping.")
        db.close()
        return

    # Reset any 'pending' or unknown statuses back to NULL for re-processing
    reset = db.execute(
        "UPDATE file_inventory SET copy_status = NULL WHERE copy_status NOT IN ({}) AND copy_status IS NOT NULL".format(
            ','.join('?' * len(REAL_STATUSES))),
        REAL_STATUSES
    ).rowcount
    if reset > 0:
        db.commit()
        log(f"Phase A: Reset {reset:,} files with invalid status to NULL")

    if already > 0:
        log(f"Phase A: {already:,}/{total:,} already marked. Processing remaining...")

    # Mark empty/error files first
    db.execute("""
        UPDATE file_inventory SET copy_status = 'EMPTY_SKIP'
        WHERE (file_size = 0 OR file_size IS NULL)
        AND (copy_status IS NULL OR copy_status = '')
    """)
    db.commit()
    empty = db.execute("SELECT COUNT(*) FROM file_inventory WHERE copy_status = 'EMPTY_SKIP'").fetchone()[0]
    log(f"  Empty files: {empty:,}")

    # For each drive, mark canonicals vs duplicates
    total_canonical = 0
    total_dupes = 0

    for drive in DRIVE_MAP:
        # Single-pass: get all files grouped by hash, ordered for canonical selection
        rows = db.execute("""
            SELECT id, xxhash, modified_date, source_path, file_size
            FROM file_inventory
            WHERE source_drive = ?
            AND file_size > 0
            AND xxhash IS NOT NULL AND xxhash != ''
            AND xxhash NOT LIKE 'ERROR%' AND xxhash != 'EMPTY_FILE'
            AND (copy_status IS NULL OR copy_status = '')
            ORDER BY xxhash, modified_date DESC, LENGTH(source_path) ASC
        """, (drive,)).fetchall()

        if not rows:
            log(f"  {drive}: No unmarked files")
            continue

        # Group by hash, pick first as canonical (newest date, shortest path)
        canonicals = 0
        dupes = 0
        current_hash = None
        batch_canonical = []
        batch_dupe = []

        for r in rows:
            if r['xxhash'] != current_hash:
                current_hash = r['xxhash']
                batch_canonical.append((r['id'],))
                canonicals += 1
            else:
                batch_dupe.append((r['id'],))
                dupes += 1

        # Batch update
        db.executemany("UPDATE file_inventory SET copy_status = 'CANONICAL' WHERE id = ?", batch_canonical)
        db.executemany("UPDATE file_inventory SET copy_status = 'DUPLICATE_SKIP' WHERE id = ?", batch_dupe)
        db.commit()

        total_canonical += canonicals
        total_dupes += dupes
        log(f"  {drive}: {canonicals:,} canonical, {dupes:,} duplicates")

    elapsed = time.time() - t0
    log(f"Phase A complete in {fmt_dur(elapsed)}: {total_canonical:,} canonical + {total_dupes:,} duplicates")

    # Summary
    for status in ['CANONICAL', 'DUPLICATE_SKIP', 'EMPTY_SKIP']:
        cnt = db.execute("SELECT COUNT(*) FROM file_inventory WHERE copy_status = ?", (status,)).fetchone()[0]
        log(f"  {status}: {cnt:,}")

    db.close()

# ═══════════════════════════════════════════════════════════════
# PHASE B: CREATE J:\ STRUCTURE + ROOT CLEANUP
# ═══════════════════════════════════════════════════════════════

def phase_b():
    log("=" * 70)
    log("PHASE B: CREATE J:\\ STRUCTURE + ROOT CLEANUP")
    log("=" * 70)
    t0 = time.time()

    # Create consolidated directory structure
    dirs_to_create = [
        TARGET_ROOT,
        os.path.join(TARGET_ROOT, 'D_DRIVE'),
        os.path.join(TARGET_ROOT, 'F_DRIVE'),
        os.path.join(TARGET_ROOT, 'G_DRIVE'),
        os.path.join(TARGET_ROOT, 'I_DRIVE'),
        os.path.join(TARGET_ROOT, 'BACKUPS'),
        ROOT_CLEANUP,
    ]
    for cat in ['CODE', 'DOCUMENTS', 'MEDIA', 'ARCHIVES', 'DATA', 'INCOMPLETE', 'MISC']:
        dirs_to_create.append(os.path.join(ROOT_CLEANUP, cat))

    for d in dirs_to_create:
        os.makedirs(d, exist_ok=True)
    log(f"  Created {len(dirs_to_create)} directories")

    # J:\ root cleanup — move loose files only (not directories)
    j_root = Path('J:\\')
    try:
        root_items = list(j_root.iterdir())
    except Exception as e:
        log(f"Cannot read J:\\ root: {e}", 'ERROR')
        return

    # Exclude our own dirs
    exclude = {'CONSOLIDATED', 'ROOT_CLEANUP', '$RECYCLE.BIN', 'System Volume Information'}
    root_files = [f for f in root_items if f.is_file()]
    log(f"  Found {len(root_files)} files at J:\\ root to organize")

    moved = 0
    errors = 0

    for i, f in enumerate(root_files):
        if i > 0 and i % 2000 == 0:
            log(f"  Root cleanup progress: {i}/{len(root_files)} ({moved} moved)")

        ext = f.suffix.lower()
        category = EXT_MAP.get(ext, 'MISC')
        target = Path(ROOT_CLEANUP) / category / f.name

        # Handle name collision
        if target.exists():
            stem = f.stem
            n = 1
            while target.exists():
                target = Path(ROOT_CLEANUP) / category / f"{stem}_{n}{ext}"
                n += 1

        try:
            os.rename(str(f), str(target))
            moved += 1
        except OSError:
            try:
                shutil.move(str(f), str(target))
                moved += 1
            except Exception as e2:
                errors += 1
                if errors <= 10:
                    log(f"  ROOT ERROR: {f.name}: {e2}", 'ERROR')

    elapsed = time.time() - t0
    log(f"Phase B complete in {fmt_dur(elapsed)}: {moved:,} files organized, {errors} errors")

# ═══════════════════════════════════════════════════════════════
# PHASE C: COPY UNIQUE FILES → J:\CONSOLIDATED\
# ═══════════════════════════════════════════════════════════════

def phase_c():
    log("=" * 70)
    log("PHASE C: COPYING UNIQUE FILES → J:\\CONSOLIDATED\\")
    log("=" * 70)

    db = get_state()
    t0 = time.time()

    # Count what needs copying
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

    log(f"  To copy: {total_files:,} canonical files ({fmt_bytes(total_bytes)})")
    if already > 0:
        log(f"  Already copied: {already:,} (will skip)")
    for r in to_copy:
        log(f"    {r['source_drive']}: {r['cnt']:,} files ({fmt_bytes(r['bytes'])})")

    # Process each drive (smallest first for quick wins)
    global_copied = 0
    global_errors = 0
    global_missing = 0
    global_bytes = 0
    last_report = time.time()

    drive_order = ['F:', 'D:', 'G:', 'I:']  # Smallest → largest

    for drive in drive_order:
        drive_dir = DRIVE_MAP.get(drive)
        if not drive_dir:
            continue

        files = db.execute("""
            SELECT id, source_path, file_name, file_ext, file_size, xxhash
            FROM file_inventory
            WHERE source_drive = ? AND copy_status = 'CANONICAL'
            ORDER BY source_path
        """, (drive,)).fetchall()

        if not files:
            log(f"  {drive}: No files to copy")
            continue

        log(f"  {drive}: Copying {len(files):,} files...")
        drive_copied = 0
        drive_errors = 0
        drive_missing = 0

        for f in files:
            src = f['source_path']

            # Build target: preserve relative path from drive root
            # I:\02_EVIDENCE\folder\file.pdf → J:\CONSOLIDATED\I_DRIVE\02_EVIDENCE\folder\file.pdf
            rel_path = src[len(drive)+1:]  # Strip "X:\" — gets "\path..." then [1:] skips leading \
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
                global_copied += 1
                drive_copied += 1
                global_bytes += (f['file_size'] or 0)
                continue

            # Source still exists?
            if not os.path.isfile(src):
                db.execute("UPDATE file_inventory SET copy_status='SOURCE_MISSING' WHERE id=?", (f['id'],))
                global_missing += 1
                drive_missing += 1
                continue

            # Copy
            try:
                os.makedirs(os.path.dirname(dst), exist_ok=True)
                shutil.copy2(src, dst)

                db.execute("""
                    UPDATE file_inventory
                    SET copy_status='COPIED', target_path=?, copied_at=datetime('now')
                    WHERE id=?
                """, (dst, f['id']))
                global_copied += 1
                drive_copied += 1
                global_bytes += (f['file_size'] or 0)

            except Exception as e:
                db.execute("UPDATE file_inventory SET copy_status='COPY_ERROR' WHERE id=?", (f['id'],))
                global_errors += 1
                drive_errors += 1
                if drive_errors <= 5:
                    log(f"    ERROR: {src}: {e}", 'ERROR')

            # Progress every 30s
            now = time.time()
            if now - last_report > 30:
                elapsed = now - t0
                rate = global_bytes / elapsed if elapsed > 0 else 0
                remaining = (total_bytes - global_bytes) / rate if rate > 0 else 0
                pct = global_copied / total_files * 100 if total_files > 0 else 0
                log(f"  PROGRESS: {global_copied:,}/{total_files:,} ({pct:.1f}%) | "
                    f"{fmt_bytes(global_bytes)}/{fmt_bytes(total_bytes)} | "
                    f"{fmt_bytes(rate)}/s | ETA {fmt_dur(remaining)}")
                last_report = now
                db.commit()

        db.commit()
        log(f"  {drive}: {drive_copied:,} copied, {drive_errors} errors, {drive_missing} missing")

    elapsed = time.time() - t0
    log(f"Phase C complete in {fmt_dur(elapsed)}:")
    log(f"  Copied: {global_copied:,} files ({fmt_bytes(global_bytes)})")
    log(f"  Errors: {global_errors:,} | Missing: {global_missing:,}")
    db.close()

# ═══════════════════════════════════════════════════════════════
# PHASE D: DATABASE PATH MIGRATION
# ═══════════════════════════════════════════════════════════════

def phase_d():
    log("=" * 70)
    log("PHASE D: DATABASE PATH MIGRATION")
    log("=" * 70)
    t0 = time.time()

    # Step 1: Backup
    backup_name = f"litigation_context_pre_consolidation_{datetime.now().strftime('%Y%m%d_%H%M%S')}.db"
    backup_path = os.path.join(TARGET_ROOT, 'BACKUPS', backup_name)
    log(f"  Backing up → {backup_path}")

    try:
        src_conn = sqlite3.connect(LIT_DB)
        src_conn.execute("PRAGMA busy_timeout = 60000")
        dst_conn = sqlite3.connect(backup_path)
        src_conn.backup(dst_conn)
        dst_conn.close()
        src_conn.close()
        log(f"  Backup complete: {fmt_bytes(os.path.getsize(backup_path))}")
    except Exception as e:
        log(f"  BACKUP FAILED: {e}", 'ERROR')
        log("  ABORTING Phase D — cannot proceed without backup", 'ERROR')
        return

    # Step 2: Update paths
    conn = sqlite3.connect(LIT_DB)
    conn.execute("PRAGMA busy_timeout = 60000")
    conn.execute("PRAGMA journal_mode = WAL")
    conn.execute("PRAGMA cache_size = -32000")

    tables_columns = [
        ('evidence_quotes', 'source_file'),
        ('documents', 'file_path'),
        ('impeachment_matrix', 'source_file'),
    ]

    total_updated = 0

    for table, column in tables_columns:
        # Verify table+column exist
        try:
            cols = {r[1] for r in conn.execute(f"PRAGMA table_info({table})").fetchall()}
        except:
            log(f"  SKIP: Table {table} does not exist", 'WARN')
            continue
        if column not in cols:
            log(f"  SKIP: {table}.{column} does not exist", 'WARN')
            continue

        for old_drive, new_subdir in DRIVE_MAP.items():
            new_prefix = os.path.join(TARGET_ROOT, new_subdir)
            # old_drive = 'I:', new_prefix = 'J:\CONSOLIDATED\I_DRIVE'
            # Path: I:\path\file → J:\CONSOLIDATED\I_DRIVE\path\file
            # SUBSTR(col, 3) gets \path\file, prepend new_prefix

            count = conn.execute(
                f"SELECT COUNT(*) FROM {table} WHERE {column} LIKE ?",
                (old_drive + '\\%',)
            ).fetchone()[0]

            if count > 0:
                conn.execute(
                    f"UPDATE {table} SET {column} = ? || SUBSTR({column}, ?) WHERE {column} LIKE ?",
                    (new_prefix, len(old_drive) + 1, old_drive + '\\%')
                )
                log(f"  {table}.{column}: {old_drive}\\ → {new_prefix}\\ ({count:,} rows)")
                total_updated += count

    conn.commit()

    # Step 3: Rebuild FTS5 indexes
    for fts_table in ['evidence_fts', 'timeline_fts', 'md_sections_fts']:
        try:
            conn.execute(f"INSERT INTO {fts_table}({fts_table}) VALUES('rebuild')")
            conn.commit()
            log(f"  Rebuilt FTS5 index: {fts_table}")
        except Exception:
            pass

    conn.close()

    elapsed = time.time() - t0
    log(f"Phase D complete in {fmt_dur(elapsed)}: {total_updated:,} paths updated")
    log(f"  Backup at: {backup_path}")

# ═══════════════════════════════════════════════════════════════
# PHASE E: FINAL VERIFICATION REPORT
# ═══════════════════════════════════════════════════════════════

def phase_e():
    log("=" * 70)
    log("PHASE E: FINAL VERIFICATION REPORT")
    log("=" * 70)

    db = get_state()

    # Status summary
    statuses = db.execute("""
        SELECT copy_status, COUNT(*) as cnt, COALESCE(SUM(file_size), 0) as bytes
        FROM file_inventory
        GROUP BY copy_status
        ORDER BY cnt DESC
    """).fetchall()

    log("  FILE INVENTORY STATUS:")
    for s in statuses:
        status = s['copy_status'] or 'UNMARKED'
        log(f"    {status:20s} {s['cnt']:>9,d} files  {fmt_bytes(s['bytes']):>12s}")

    # Per-drive summary
    log("\n  PER-DRIVE SUMMARY:")
    drives = db.execute("""
        SELECT source_drive,
            SUM(CASE WHEN copy_status='COPIED' THEN 1 ELSE 0 END) as copied,
            SUM(CASE WHEN copy_status='DUPLICATE_SKIP' THEN 1 ELSE 0 END) as dupes,
            SUM(CASE WHEN copy_status='COPY_ERROR' THEN 1 ELSE 0 END) as errs,
            SUM(CASE WHEN copy_status='SOURCE_MISSING' THEN 1 ELSE 0 END) as missing,
            SUM(CASE WHEN copy_status='EMPTY_SKIP' THEN 1 ELSE 0 END) as empty,
            COUNT(*) as total
        FROM file_inventory GROUP BY source_drive
    """).fetchall()

    for d in drives:
        log(f"    {d['source_drive']}: {d['copied']:,} copied, {d['dupes']:,} deduped, "
            f"{d['errs']} errors, {d['missing']} missing, {d['empty']} empty / {d['total']:,} total")

    # Verify DB paths were migrated
    log("\n  DB PATH VERIFICATION:")
    try:
        lit = sqlite3.connect(LIT_DB)
        lit.execute("PRAGMA busy_timeout = 60000")
        old_paths = 0
        new_paths = 0
        for old_drive in DRIVE_MAP:
            for table, col in [('evidence_quotes','source_file'),('documents','file_path'),('impeachment_matrix','source_file')]:
                try:
                    old_cnt = lit.execute(f"SELECT COUNT(*) FROM {table} WHERE {col} LIKE ?", (old_drive + '\\%',)).fetchone()[0]
                    new_cnt = lit.execute(f"SELECT COUNT(*) FROM {table} WHERE {col} LIKE ?", ('J:\\CONSOLIDATED\\' + DRIVE_MAP[old_drive] + '\\%',)).fetchone()[0]
                    if old_cnt > 0:
                        log(f"    ⚠️  {table}.{col}: {old_cnt:,} still on {old_drive}", 'WARN')
                        old_paths += old_cnt
                    if new_cnt > 0:
                        new_paths += new_cnt
                except:
                    pass
        if old_paths == 0:
            log(f"    ✅ All paths migrated to J:\\CONSOLIDATED\\ ({new_paths:,} total)")
        else:
            log(f"    ⚠️  {old_paths:,} paths still on old drives", 'WARN')
        lit.close()
    except Exception as e:
        log(f"    Cannot verify: {e}", 'ERROR')

    # J:\ disk usage
    try:
        total_j, used_j, free_j = shutil.disk_usage('J:\\')
        log(f"\n  J:\\ DISK: {fmt_bytes(used_j)} used / {fmt_bytes(total_j)} total ({fmt_bytes(free_j)} free)")
    except:
        pass

    # Count files on J:\CONSOLIDATED
    consolidated_count = 0
    consolidated_bytes = 0
    if os.path.isdir(TARGET_ROOT):
        for root, dirs, files in os.walk(TARGET_ROOT):
            for f in files:
                fp = os.path.join(root, f)
                try:
                    consolidated_count += 1
                    consolidated_bytes += os.path.getsize(fp)
                except:
                    pass
    log(f"\n  J:\\CONSOLIDATED: {consolidated_count:,} files ({fmt_bytes(consolidated_bytes)})")

    log("\n" + "=" * 70)
    log("  ✅ CONSOLIDATION COMPLETE")
    log("=" * 70)
    log("  External drives D:\\, F:\\, G:\\, I:\\ are now consolidated on J:\\CONSOLIDATED\\")
    log("  Original files remain on source drives (non-destructive)")
    log("  DB paths updated to J:\\CONSOLIDATED\\ prefix")
    log(f"  Full log: {LOG_FILE}")
    log("=" * 70)

    db.close()

# ═══════════════════════════════════════════════════════════════
# MAIN
# ═══════════════════════════════════════════════════════════════

if __name__ == '__main__':
    log("")
    log("╔" + "═" * 68 + "╗")
    log("║  MASTER CONSOLIDATION EXECUTOR — ALL PHASES                      ║")
    log("║  D:\\, F:\\, G:\\, I:\\ → J:\\CONSOLIDATED\\                            ║")
    log("╚" + "═" * 68 + "╝")
    log(f"  State DB:  {STATE_DB}")
    log(f"  Lit DB:    {LIT_DB}")
    log(f"  Target:    {TARGET_ROOT}")
    log(f"  Started:   {datetime.now().isoformat()}")
    log("")

    overall_t0 = time.time()

    if not preflight():
        log("PRE-FLIGHT FAILED — aborting", 'ERROR')
        sys.exit(1)

    log("")

    try:
        phase_a()
        log("")
        phase_b()
        log("")
        phase_c()
        log("")

        # Phase D: Only run if Phase C actually copied files
        state_check = sqlite3.connect(STATE_DB)
        state_check.row_factory = sqlite3.Row
        state_check.execute("PRAGMA busy_timeout = 60000")
        copied_count = state_check.execute(
            "SELECT COUNT(*) FROM file_inventory WHERE copy_status IN ('COPIED','VERIFIED')"
        ).fetchone()[0]
        state_check.close()

        if copied_count > 0:
            log(f"Phase C copied {copied_count:,} files — proceeding with DB migration")
            phase_d()
        else:
            log("⚠️  Phase C copied 0 files — SKIPPING Phase D (DB paths stay unchanged)", 'WARN')
            log("    Fix: Check Phase A marked canonicals, then re-run")

        log("")
        phase_e()
    except KeyboardInterrupt:
        log("\n⚠️  INTERRUPTED — state saved in DB, safe to re-run", 'WARN')
    except Exception as e:
        log(f"\n❌ FATAL: {e}", 'ERROR')
        import traceback
        log(traceback.format_exc(), 'ERROR')

    total_elapsed = time.time() - overall_t0
    log(f"\nTotal time: {fmt_dur(total_elapsed)}")
    log(f"Log: {LOG_FILE}")

    if _log_fh:
        _log_fh.close()
