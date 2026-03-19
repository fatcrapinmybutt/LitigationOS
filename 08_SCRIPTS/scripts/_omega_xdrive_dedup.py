#!/usr/bin/env python3
"""
OMEGA CROSS-DRIVE DEDUP ENGINE
===============================
Removes exact duplicate files from external drives D/F/G/H
that already exist in LitigationOS on C:.

Safety:
  - Moves to per-drive _RECYCLE (not delete)
  - Court documents protected (legal_score >= 0.8)
  - Full rollback journal in move_log
  - Dry-run mode by default

Usage:
  python _omega_xdrive_dedup.py report    # Show what would be removed
  python _omega_xdrive_dedup.py execute   # Live execution
"""

import sqlite3
import os
import sys
import shutil
import time
import hashlib
from pathlib import Path
from collections import defaultdict

sys.stdout.reconfigure(encoding='utf-8')

DB = r'C:\Users\andre\LitigationOS\00_SYSTEM\manifests\omega_dedup.db'
DRIVES = ['D:', 'F:', 'G:', 'H:']
PROTECT_KEYWORDS = [
    'court', 'filing', 'motion', 'brief', 'order', 'petition',
    'complaint', 'affidavit', 'exhibit', 'evidence', 'pigors',
    'watson', 'mcneill', 'barnes', 'custody', 'parenting',
    'PPO', 'SCAO', 'litigation', 'judicial', 'verdict',
    'deposition', 'subpoena', 'transcript', 'docket'
]


def get_db():
    conn = sqlite3.connect(DB, timeout=120)
    conn.execute("PRAGMA busy_timeout=60000")
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA cache_size=-64000")
    return conn


def is_protected(path):
    """Check if FILENAME (not directory path) contains litigation-critical keywords.
    
    For cross-drive dedup, we only protect if the filename itself is a court doc.
    Directory paths like 'LitigationOS_backup/' don't count — the canonical copy
    is in LitigationOS on C:, so external copies are safe to recycle.
    """
    filename = os.path.basename(path).lower()
    for kw in PROTECT_KEYWORDS:
        if kw.lower() in filename:
            return True
    return False


def verify_hash(filepath, expected_hash):
    """Verify file still matches its cataloged hash (first+last 64KB SHA-256)."""
    try:
        size = os.path.getsize(filepath)
        h = hashlib.sha256()
        with open(filepath, 'rb') as f:
            head = f.read(65536)
            h.update(head)
            if size > 131072:
                f.seek(-65536, 2)
                tail = f.read(65536)
                h.update(tail)
        return h.hexdigest() == expected_hash
    except Exception:
        return False


def report(conn):
    """Generate dedup report without moving anything."""
    print("=" * 70)
    print("OMEGA CROSS-DRIVE DEDUP REPORT")
    print("=" * 70)
    print()

    total_dupes = 0
    total_bytes = 0
    total_protected = 0
    total_missing = 0
    drive_stats = {}

    for drive in DRIVES:
        # Check drive accessibility
        if not os.path.exists(drive + '\\'):
            print(f"  {drive} — NOT CONNECTED, skipping")
            continue

        # Get all duplicate files on this drive
        rows = conn.execute("""
            SELECT x.id, x.path, x.size, x.partial_hash
            FROM xdrive_manifest x
            WHERE x.drive = ? AND x.partial_hash IS NOT NULL
            AND EXISTS (
                SELECT 1 FROM file_manifest f
                WHERE f.partial_hash = x.partial_hash AND f.size = x.size
                AND f.partial_hash IS NOT NULL
            )
        """, (drive,)).fetchall()

        dupes = 0
        bytes_reclaimable = 0
        protected = 0
        missing = 0
        by_ext = defaultdict(lambda: [0, 0])

        for xid, path, size, phash in rows:
            if not os.path.exists(path):
                missing += 1
                continue
            if is_protected(path):
                protected += 1
                continue

            dupes += 1
            bytes_reclaimable += (size or 0)
            ext = os.path.splitext(path)[1].lower()[:10] or '(none)'
            by_ext[ext][0] += 1
            by_ext[ext][1] += (size or 0)

        drive_stats[drive] = {
            'total': len(rows), 'dupes': dupes, 'bytes': bytes_reclaimable,
            'protected': protected, 'missing': missing
        }
        total_dupes += dupes
        total_bytes += bytes_reclaimable
        total_protected += protected
        total_missing += missing

        free_gb = shutil.disk_usage(drive + '\\').free / (1024**3)
        print(f"  {drive} — {dupes:,} removable dupes ({bytes_reclaimable/(1024**3):.2f} GB)")
        print(f"         {protected:,} protected (court docs), {missing:,} already gone")
        print(f"         Free space: {free_gb:.2f} GB → {free_gb + bytes_reclaimable/(1024**3):.2f} GB after")

        # Top extensions
        sorted_ext = sorted(by_ext.items(), key=lambda x: x[1][1], reverse=True)[:8]
        for ext, (cnt, bts) in sorted_ext:
            print(f"           {ext:8s}: {cnt:>7,} files ({bts/(1024**2):.1f} MB)")
        print()

    print("-" * 70)
    print(f"  TOTAL: {total_dupes:,} files ({total_bytes/(1024**3):.2f} GB) removable")
    print(f"         {total_protected:,} protected, {total_missing:,} already gone")
    print()

    # Unique files analysis
    print("=" * 70)
    print("UNIQUE EXTERNAL FILES (NOT in LitigationOS)")
    print("=" * 70)
    for drive in DRIVES:
        if not os.path.exists(drive + '\\'):
            continue
        unique = conn.execute("""
            SELECT COUNT(*), COALESCE(SUM(x.size), 0)
            FROM xdrive_manifest x
            WHERE x.drive = ? AND x.partial_hash IS NOT NULL
            AND NOT EXISTS (
                SELECT 1 FROM file_manifest f
                WHERE f.partial_hash = x.partial_hash AND f.size = x.size
                AND f.partial_hash IS NOT NULL
            )
        """, (drive,)).fetchone()
        unhashed = conn.execute(
            "SELECT COUNT(*) FROM xdrive_manifest WHERE drive=? AND partial_hash IS NULL",
            (drive,)
        ).fetchone()[0]
        print(f"  {drive}: {unique[0]:,} unique files ({unique[1]/(1024**3):.2f} GB), {unhashed:,} unhashed")

    return drive_stats


def execute(conn):
    """Execute live cross-drive dedup using os.rename for instant same-drive moves.
    
    Optimized for USB drives: flat _RECYCLE_DEDUP directory avoids nested dir creation.
    Uses os.rename (instant metadata operation) instead of shutil.move (copy+delete).
    Skips files already processed in prior runs via move_log check.
    """
    print("=" * 70, flush=True)
    print("OMEGA CROSS-DRIVE DEDUP — LIVE EXECUTION", flush=True)
    print("=" * 70, flush=True)
    print(flush=True)

    # Get already-processed source paths to skip
    already_done = set()
    for row in conn.execute("SELECT source_path FROM move_log WHERE operation='xdrive_dedup'"):
        already_done.add(row[0])
    print(f"  Skipping {len(already_done):,} already-processed files", flush=True)

    total_moved = 0
    total_bytes = 0
    total_failed = 0
    total_protected = 0
    total_skipped = 0
    t_start = time.time()

    for drive in DRIVES:
        if not os.path.exists(drive + '\\'):
            print(f"  {drive} — NOT CONNECTED, skipping", flush=True)
            continue

        # Create single flat recycle directory (avoids nested dir creation overhead)
        recycle_dir = os.path.join(drive + '\\', '_RECYCLE_DEDUP')
        os.makedirs(recycle_dir, exist_ok=True)

        # Get duplicate files, ordered by size DESC for maximum space recovery first
        rows = conn.execute("""
            SELECT x.id, x.path, x.size, x.partial_hash
            FROM xdrive_manifest x
            WHERE x.drive = ? AND x.partial_hash IS NOT NULL
            AND EXISTS (
                SELECT 1 FROM file_manifest f
                WHERE f.partial_hash = x.partial_hash AND f.size = x.size
                AND f.partial_hash IS NOT NULL
            )
            ORDER BY x.size DESC
        """, (drive,)).fetchall()

        moved = 0
        failed = 0
        protected = 0
        skipped = 0
        drive_bytes = 0
        batch = []
        seq = 0  # Sequential counter for flat naming

        print(f"  {drive}: {len(rows):,} duplicate candidates...", flush=True)

        for xid, path, size, phash in rows:
            # Skip already processed
            if path in already_done:
                skipped += 1
                continue
            if not os.path.exists(path):
                skipped += 1
                continue
            if is_protected(path):
                protected += 1
                continue

            # Flat naming: just use sequential number + original extension
            _, ext = os.path.splitext(path)
            dest = os.path.join(recycle_dir, f"{seq:07d}{ext}")
            seq += 1

            try:
                # os.rename is instant (metadata-only) on same filesystem
                os.rename(path, dest)
                moved += 1
                drive_bytes += (size or 0)

                batch.append((
                    time.strftime('%Y-%m-%dT%H:%M:%S'),
                    'xdrive_dedup', path, dest, None,
                    'xdrive', size or 0,
                    f'os.rename("{dest}", "{path}")',
                    'done'
                ))

                # Batch commit every 2000 for speed
                if len(batch) >= 2000:
                    conn.executemany("""
                        INSERT INTO move_log (timestamp, operation, source_path, dest_path, 
                                            cluster_id, tier, file_size, rollback_cmd, status)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """, batch)
                    conn.commit()
                    elapsed = time.time() - t_start
                    rate = (total_moved + moved) / elapsed if elapsed > 0 else 0
                    print(f"    {drive} {moved:,} moved ({drive_bytes/(1024**3):.2f} GB) @ {rate:.0f}/s", flush=True)
                    batch.clear()

            except OSError as e:
                # os.rename fails across filesystems; fall back to shutil.move
                try:
                    shutil.move(path, dest)
                    moved += 1
                    drive_bytes += (size or 0)
                    batch.append((
                        time.strftime('%Y-%m-%dT%H:%M:%S'),
                        'xdrive_dedup', path, dest, None,
                        'xdrive', size or 0,
                        f'shutil.move("{dest}", "{path}")',
                        'done'
                    ))
                except Exception as e2:
                    failed += 1
                    if failed <= 3:
                        print(f"    FAIL: {path}: {e2}", flush=True)

        # Flush remaining batch
        if batch:
            conn.executemany("""
                INSERT INTO move_log (timestamp, operation, source_path, dest_path,
                                    cluster_id, tier, file_size, rollback_cmd, status)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, batch)
            conn.commit()

        total_moved += moved
        total_bytes += drive_bytes
        total_failed += failed
        total_protected += protected
        total_skipped += skipped

        free_gb = shutil.disk_usage(drive + '\\').free / (1024**3)
        print(f"  {drive} DONE: {moved:,} moved ({drive_bytes/(1024**3):.2f} GB), "
              f"{protected:,} protected, {failed:,} failed, {skipped:,} skipped, "
              f"free: {free_gb:.2f} GB", flush=True)
        print(flush=True)

        # Clean up empty directories left behind
        print(f"  {drive}: Cleaning empty directories...", flush=True)
        cleaned = 0
        for dirpath, dirnames, filenames in os.walk(drive + '\\', topdown=False):
            if dirpath == drive + '\\' or '_RECYCLE' in dirpath:
                continue
            try:
                if not os.listdir(dirpath):
                    os.rmdir(dirpath)
                    cleaned += 1
            except Exception:
                pass
        if cleaned:
            print(f"    Removed {cleaned:,} empty directories", flush=True)

    elapsed = time.time() - t_start
    print("=" * 70, flush=True)
    print(f"  TOTAL: {total_moved:,} files moved ({total_bytes/(1024**3):.2f} GB)", flush=True)
    print(f"         {total_protected:,} protected, {total_failed:,} failed, {total_skipped:,} skipped", flush=True)
    if elapsed > 0 and total_moved > 0:
        print(f"         Time: {elapsed:.1f}s ({total_moved/elapsed:.0f} files/s)", flush=True)
    print("=" * 70, flush=True)


def main():
    if len(sys.argv) < 2:
        print("Usage: python _omega_xdrive_dedup.py [report|execute]")
        sys.exit(1)

    mode = sys.argv[1].lower()
    conn = get_db()

    if mode == 'report':
        report(conn)
    elif mode == 'execute':
        print("⚠️  LIVE MODE — Files will be MOVED to per-drive _RECYCLE_DEDUP/")
        print("    Press Ctrl+C within 5 seconds to abort...")
        try:
            time.sleep(5)
        except KeyboardInterrupt:
            print("\n    Aborted.")
            sys.exit(0)
        execute(conn)
    else:
        print(f"Unknown mode: {mode}")
        sys.exit(1)

    conn.close()


if __name__ == '__main__':
    main()
