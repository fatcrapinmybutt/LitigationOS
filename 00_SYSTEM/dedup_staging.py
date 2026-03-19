import sys
sys.stdout.reconfigure(encoding='utf-8')
sys.stdout = open(sys.stdout.fileno(), mode='w', encoding='utf-8', buffering=1)

import os
import hashlib
import json
import shutil
import time
from collections import defaultdict
from pathlib import Path

LOG_FILE = r"C:\Users\andre\dedup_output.log"
_logf = open(LOG_FILE, 'w', encoding='utf-8')

def log(msg=""):
    sys.stdout.write(msg + "\n")
    sys.stdout.flush()
    _logf.write(msg + "\n")
    _logf.flush()

STAGING_DIR = r"F:\LitOS_Unpack_Staging"
REPORT_PATH = os.path.join(STAGING_DIR, "_DEDUP_REPORT.json")
BUFFER_SIZE = 8192  # 8KB read buffer

# Junk file definitions
JUNK_EXTENSIONS = {'.exe', '.dll', '.vim'}
JUNK_FILENAMES = {'thumbs.db', '.ds_store', 'desktop.ini'}
JUNK_DIRNAMES = {'__pycache__', '.git'}
LICENSE_NAMES = {'license', 'license.md', 'license.txt'}


def sha256_file(filepath):
    """Compute SHA-256 hash of a file using 8KB buffer."""
    h = hashlib.sha256()
    try:
        with open(filepath, 'rb') as f:
            while True:
                chunk = f.read(BUFFER_SIZE)
                if not chunk:
                    break
                h.update(chunk)
        return h.hexdigest()
    except (PermissionError, OSError) as e:
        log(f"  [WARN] Cannot read: {filepath} — {e}")
        return None


def is_junk_file(filepath):
    """Check if a file is junk that should be deleted."""
    name = os.path.basename(filepath).lower()
    ext = os.path.splitext(filepath)[1].lower()

    if ext in JUNK_EXTENSIONS:
        return True
    if name in JUNK_FILENAMES:
        return True

    # License files — only delete if NOT in a root-level dir
    if name in LICENSE_NAMES:
        rel = os.path.relpath(filepath, STAGING_DIR)
        parts = Path(rel).parts
        # Keep if file is directly in staging root or one level deep
        if len(parts) <= 2:
            return False
        return True

    return False


def is_empty_file(filepath):
    """Check if file is 0 bytes."""
    try:
        return os.path.getsize(filepath) == 0
    except OSError:
        return False


def delete_file(filepath, stats):
    """Delete a file and track freed space."""
    try:
        size = os.path.getsize(filepath)
        os.remove(filepath)
        stats['junk_deleted'] += 1
        stats['junk_freed'] += size
        return True
    except (PermissionError, OSError) as e:
        log(f"  [WARN] Cannot delete: {filepath} — {e}")
        return False


def delete_junk_dirs(staging_dir, stats):
    """Delete __pycache__ and .git directories."""
    for root, dirs, files in os.walk(staging_dir, topdown=False):
        for d in dirs:
            if d.lower() in JUNK_DIRNAMES:
                dirpath = os.path.join(root, d)
                try:
                    dir_size = 0
                    dir_count = 0
                    for r, dd, ff in os.walk(dirpath):
                        for f in ff:
                            fp = os.path.join(r, f)
                            try:
                                dir_size += os.path.getsize(fp)
                                dir_count += 1
                            except OSError:
                                pass
                    shutil.rmtree(dirpath, ignore_errors=True)
                    stats['junk_deleted'] += dir_count
                    stats['junk_freed'] += dir_size
                    log(f"  [JUNK DIR] Deleted: {dirpath} ({dir_count} files, {dir_size:,} bytes)")
                except (PermissionError, OSError) as e:
                    log(f"  [WARN] Cannot delete dir: {dirpath} — {e}")


def main():
    start_time = time.time()
    log("=" * 70)
    log("SHA-256 DEDUPLICATION — F:\\LitOS_Unpack_Staging")
    log("=" * 70)

    stats = {
        'junk_deleted': 0,
        'junk_freed': 0,
    }

    # ── Phase 1: Delete junk directories ──
    log("\n[Phase 1] Removing junk directories (__pycache__, .git)...")
    delete_junk_dirs(STAGING_DIR, stats)
    log(f"  Junk dirs cleaned: {stats['junk_deleted']} files, {stats['junk_freed']:,} bytes freed")

    # ── Phase 2: Scan all files, delete junk files, hash the rest ──
    log("\n[Phase 2] Scanning files, removing junk, computing SHA-256 hashes...")
    hash_map = defaultdict(list)  # hash -> [filepaths]
    total_scanned = 0
    junk_phase2_start = stats['junk_deleted']

    for root, dirs, files in os.walk(STAGING_DIR):
        for filename in files:
            filepath = os.path.join(root, filename)
            total_scanned += 1

            if total_scanned % 1000 == 0:
                log(f"  ... scanned {total_scanned:,} files")

            # Skip our own report
            if os.path.normpath(filepath) == os.path.normpath(REPORT_PATH):
                continue

            # Delete junk files
            if is_junk_file(filepath):
                delete_file(filepath, stats)
                continue

            # Delete empty files
            if is_empty_file(filepath):
                delete_file(filepath, stats)
                continue

            # Hash the file
            file_hash = sha256_file(filepath)
            if file_hash:
                hash_map[file_hash].append(filepath)

    junk_phase2 = stats['junk_deleted'] - junk_phase2_start
    log(f"  Total scanned: {total_scanned:,}")
    log(f"  Junk/empty files deleted in phase 2: {junk_phase2:,}")
    log(f"  Files hashed: {sum(len(v) for v in hash_map.values()):,}")

    # ── Phase 3: Deduplicate ──
    log("\n[Phase 3] Deduplicating (keeping shortest path per group)...")
    duplicate_groups = []
    dup_deleted = 0
    dup_freed = 0

    for file_hash, paths in hash_map.items():
        if len(paths) < 2:
            continue

        # Keep file with shortest path
        paths_sorted = sorted(paths, key=lambda p: len(p))
        keep = paths_sorted[0]
        delete_list = paths_sorted[1:]

        group = {
            'hash': file_hash,
            'kept': keep,
            'deleted': []
        }

        for dup_path in delete_list:
            try:
                size = os.path.getsize(dup_path)
                os.remove(dup_path)
                dup_deleted += 1
                dup_freed += size
                group['deleted'].append(dup_path)
            except (PermissionError, OSError) as e:
                log(f"  [WARN] Cannot delete dup: {dup_path} — {e}")

        if group['deleted']:
            duplicate_groups.append(group)

    unique_files = len(hash_map)
    total_files_hashed = sum(len(v) for v in hash_map.values())

    # ── Phase 4: Write report ──
    log("\n[Phase 4] Writing report...")
    report = {
        'summary': {
            'total_files_scanned': total_scanned,
            'total_files_hashed': total_files_hashed,
            'unique_files': unique_files,
            'duplicate_files_deleted': dup_deleted,
            'duplicate_space_freed_bytes': dup_freed,
            'junk_files_deleted': stats['junk_deleted'],
            'junk_space_freed_bytes': stats['junk_freed'],
            'total_deleted': dup_deleted + stats['junk_deleted'],
            'total_freed_bytes': dup_freed + stats['junk_freed'],
            'duration_seconds': round(time.time() - start_time, 2)
        },
        'duplicate_groups': duplicate_groups
    }

    try:
        with open(REPORT_PATH, 'w', encoding='utf-8') as f:
            json.dump(report, f, indent=2, ensure_ascii=False)
        log(f"  Report written to: {REPORT_PATH}")
    except (PermissionError, OSError) as e:
        log(f"  [ERROR] Cannot write report: {e}")

    # ── Summary ──
    elapsed = time.time() - start_time
    log("\n" + "=" * 70)
    log("DEDUPLICATION COMPLETE")
    log("=" * 70)
    s = report['summary']
    log(f"  Total files scanned:       {s['total_files_scanned']:>10,}")
    log(f"  Files hashed:              {s['total_files_hashed']:>10,}")
    log(f"  Unique files:              {s['unique_files']:>10,}")
    log(f"  Duplicate files deleted:   {s['duplicate_files_deleted']:>10,}")
    log(f"  Duplicate space freed:     {s['duplicate_space_freed_bytes']:>10,} bytes ({s['duplicate_space_freed_bytes'] / (1024**3):.2f} GB)")
    log(f"  Junk files deleted:        {s['junk_files_deleted']:>10,}")
    log(f"  Junk space freed:          {s['junk_space_freed_bytes']:>10,} bytes ({s['junk_space_freed_bytes'] / (1024**3):.2f} GB)")
    log(f"  ────────────────────────────────────")
    log(f"  TOTAL deleted:             {s['total_deleted']:>10,}")
    log(f"  TOTAL freed:               {s['total_freed_bytes']:>10,} bytes ({s['total_freed_bytes'] / (1024**3):.2f} GB)")
    log(f"  Duration:                  {elapsed:>10.1f} seconds")
    log("=" * 70)


if __name__ == '__main__':
    main()

