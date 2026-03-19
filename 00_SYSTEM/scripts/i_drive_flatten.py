#!/usr/bin/env python3
r"""
I:\ Drive Flattener — Move ALL files to I:\ root, zero subfolders, with dedup.

Phase 1: Build manifest (SQLite) of every file on I:\
Phase 2: Deduplicate by (name, size) — keep oldest, mark rest for deletion
Phase 3: Execute moves/deletes, remove empty dirs

Usage:
    python i_drive_flatten.py --manifest-only   # Phase 1 only
    python i_drive_flatten.py --dry-run          # Phase 1+2, stats only
    python i_drive_flatten.py --execute          # Phase 1+2+3, do it
"""

import argparse
import datetime
import os
import shutil
import sqlite3
import sys
import time

# Force UTF-8 stdout for Windows
sys.stdout = open(sys.stdout.fileno(), mode="w", encoding="utf-8", errors="replace")
sys.stderr = open(sys.stderr.fileno(), mode="w", encoding="utf-8", errors="replace")

# ── Constants ────────────────────────────────────────────────────────────────

DRIVE = "I:\\"
MANIFEST_DB = os.path.join(DRIVE, "flatten_manifest.db")
FLATTEN_LOG = os.path.join(DRIVE, "FLATTEN_LOG.txt")

SKIP_DIRS = frozenset({
    "$recycle.bin",
    "system volume information",
    "$recycle.bin".upper(),
    "System Volume Information".upper(),
})

SKIP_FILES = frozenset({
    "flatten_manifest.db",
    "flatten_manifest.db-wal",
    "flatten_manifest.db-shm",
    "flatten_log.txt",
})

BATCH_SIZE = 1000
PROGRESS_INTERVAL = 5000


# ── Logging ──────────────────────────────────────────────────────────────────

def log(msg: str, log_file=None):
    """Print to stdout and optionally append to log file."""
    ts = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    line = f"[{ts}] {msg}"
    print(line, flush=True)
    if log_file:
        try:
            with open(log_file, "a", encoding="utf-8", errors="replace") as f:
                f.write(line + "\n")
        except OSError:
            pass


# ── Database ─────────────────────────────────────────────────────────────────

def get_db() -> sqlite3.Connection:
    """Open the manifest DB with WAL mode and busy timeout."""
    conn = sqlite3.connect(MANIFEST_DB)
    conn.execute("PRAGMA busy_timeout=60000;")
    conn.execute("PRAGMA journal_mode=WAL;")
    conn.execute("PRAGMA cache_size=-32000;")
    conn.execute("PRAGMA synchronous=NORMAL;")
    return conn


def create_schema(conn: sqlite3.Connection):
    conn.execute("""
        CREATE TABLE IF NOT EXISTS files (
            id            INTEGER PRIMARY KEY AUTOINCREMENT,
            file_name     TEXT NOT NULL,
            size_bytes    INTEGER NOT NULL,
            date_created  TEXT NOT NULL,
            full_path     TEXT NOT NULL UNIQUE,
            is_duplicate  INTEGER NOT NULL DEFAULT 0,
            action        TEXT NOT NULL DEFAULT '',
            new_name      TEXT DEFAULT ''
        )
    """)
    conn.execute("CREATE INDEX IF NOT EXISTS idx_name_size ON files(file_name, size_bytes);")
    conn.execute("CREATE INDEX IF NOT EXISTS idx_action ON files(action);")
    conn.execute("CREATE INDEX IF NOT EXISTS idx_full_path ON files(full_path);")
    conn.commit()


# ── Phase 1: Build Manifest ─────────────────────────────────────────────────

def _should_skip_dir(name: str) -> bool:
    return name.upper() in {s.upper() for s in SKIP_DIRS}


def _should_skip_file(name: str) -> bool:
    return name.lower() in {s.lower() for s in SKIP_FILES}


def _get_creation_time_iso(path: str) -> str:
    """Get file creation time as ISO string. Falls back to mtime."""
    try:
        st = os.stat(path)
        # On Windows, st_ctime is creation time
        ctime = st.st_ctime
        return datetime.datetime.fromtimestamp(ctime).isoformat()
    except OSError:
        return "1970-01-01T00:00:00"


def _scandir_recursive(root: str):
    """
    Yield (full_path, file_name, size_bytes, date_created) for every file
    under root, using os.scandir() for speed. Skips system dirs.
    """
    try:
        with os.scandir(root) as it:
            for entry in it:
                try:
                    name = entry.name
                    if entry.is_dir(follow_symlinks=False):
                        if _should_skip_dir(name):
                            continue
                        yield from _scandir_recursive(entry.path)
                    elif entry.is_file(follow_symlinks=False):
                        if _should_skip_file(name):
                            continue
                        try:
                            stat = entry.stat(follow_symlinks=False)
                            size = stat.st_size
                            ctime = datetime.datetime.fromtimestamp(stat.st_ctime).isoformat()
                        except OSError:
                            size = 0
                            ctime = "1970-01-01T00:00:00"
                        yield (entry.path, name, size, ctime)
                except PermissionError:
                    pass
                except OSError:
                    pass
    except PermissionError:
        pass
    except OSError:
        pass


def build_manifest(conn: sqlite3.Connection) -> int:
    r"""Scan I:\ and populate the files table. Returns file count."""
    log("Phase 1: Building manifest — scanning I:\\ ...")

    # Clear previous manifest data
    conn.execute("DELETE FROM files;")
    conn.commit()

    batch = []
    count = 0
    t0 = time.time()

    for full_path, file_name, size_bytes, date_created in _scandir_recursive(DRIVE):
        batch.append((file_name, size_bytes, date_created, full_path))
        count += 1

        if count % BATCH_SIZE == 0:
            conn.executemany(
                "INSERT OR IGNORE INTO files (file_name, size_bytes, date_created, full_path) VALUES (?,?,?,?)",
                batch,
            )
            conn.commit()
            batch.clear()

        if count % PROGRESS_INTERVAL == 0:
            elapsed = time.time() - t0
            rate = count / elapsed if elapsed > 0 else 0
            log(f"  ... scanned {count:,} files ({rate:,.0f} files/sec)")

    # Flush remaining
    if batch:
        conn.executemany(
            "INSERT OR IGNORE INTO files (file_name, size_bytes, date_created, full_path) VALUES (?,?,?,?)",
            batch,
        )
        conn.commit()

    elapsed = time.time() - t0
    log(f"Phase 1 complete: {count:,} files scanned in {elapsed:.1f}s")
    return count


# ── Phase 2: Deduplicate & Plan ─────────────────────────────────────────────

def _is_at_root(path: str) -> bool:
    r"""Check if a file is already at I:\ root."""
    parent = os.path.dirname(path)
    return os.path.normcase(os.path.normpath(parent)) == os.path.normcase(os.path.normpath(DRIVE))


def _parent_folder_name(path: str) -> str:
    """Get the immediate parent folder name."""
    parent = os.path.dirname(path)
    return os.path.basename(parent)


def deduplicate(conn: sqlite3.Connection) -> dict:
    """
    Mark duplicates and plan actions.
    Returns stats dict.
    """
    log("Phase 2: Deduplicating and planning actions ...")
    t0 = time.time()

    stats = {
        "already_at_root": 0,
        "duplicates_to_delete": 0,
        "files_to_flatten": 0,
        "collision_renames": 0,
        "total_dup_space_bytes": 0,
    }

    # Reset all actions
    conn.execute("UPDATE files SET action='', is_duplicate=0, new_name='';")
    conn.commit()

    # Step 1: Mark files already at root as 'keep'
    cursor = conn.execute("SELECT id, full_path FROM files")
    root_updates = []
    for row in cursor:
        fid, fpath = row
        if _is_at_root(fpath):
            root_updates.append((fid,))
    conn.executemany("UPDATE files SET action='keep' WHERE id=?", root_updates)
    conn.commit()
    stats["already_at_root"] = len(root_updates)
    log(f"  {stats['already_at_root']:,} files already at root (action=keep)")

    # Step 2: Find duplicate groups (name + size) among non-root files
    # For each (name, size) group with >1 file, keep the oldest, mark rest as delete
    cursor = conn.execute("""
        SELECT file_name, size_bytes, COUNT(*) as cnt
        FROM files
        WHERE action = ''
        GROUP BY file_name, size_bytes
        HAVING cnt > 1
    """)
    dup_groups = cursor.fetchall()
    log(f"  Found {len(dup_groups):,} duplicate groups (name+size match, non-root)")

    delete_ids = []
    keep_ids = []
    for fname, fsize, cnt in dup_groups:
        # Get all files in this group, ordered by creation time (oldest first)
        rows = conn.execute("""
            SELECT id, full_path, date_created
            FROM files
            WHERE file_name=? AND size_bytes=? AND action=''
            ORDER BY date_created ASC
        """, (fname, fsize)).fetchall()

        if not rows:
            continue

        # Keep the oldest one
        keep_ids.append((rows[0][0],))
        for row in rows[1:]:
            delete_ids.append((row[0],))
            stats["total_dup_space_bytes"] += fsize

    if keep_ids:
        conn.executemany("UPDATE files SET action='flatten' WHERE id=?", keep_ids)
    if delete_ids:
        conn.executemany("UPDATE files SET action='delete', is_duplicate=1 WHERE id=?", delete_ids)
    conn.commit()
    stats["duplicates_to_delete"] = len(delete_ids)
    log(f"  Marked {len(delete_ids):,} duplicates for deletion "
        f"(~{stats['total_dup_space_bytes'] / (1024**3):.2f} GB reclaimable)")

    # Step 3: Mark remaining unmarked files for flattening
    conn.execute("UPDATE files SET action='flatten' WHERE action=''")
    conn.commit()

    # Step 4: Handle name collisions at root
    # A collision: a file marked 'flatten' whose file_name already exists at root
    # with a DIFFERENT size, OR multiple 'flatten' files with same name but different sizes

    # Build a dict of root-level file names → sizes (from 'keep' files)
    root_files = {}
    for row in conn.execute("SELECT file_name, size_bytes FROM files WHERE action='keep'"):
        root_files[row[0].lower()] = row[1]

    # Now process 'flatten' files — group by name, check collisions
    cursor = conn.execute("""
        SELECT file_name, COUNT(DISTINCT size_bytes) as distinct_sizes
        FROM files
        WHERE action='flatten'
        GROUP BY file_name
    """)
    collision_groups = []
    for fname, distinct_sizes in cursor:
        name_lower = fname.lower()
        # Collision if: name exists at root with different size, or multiple different sizes in flatten set
        if name_lower in root_files or distinct_sizes > 1:
            collision_groups.append(fname)

    # For collision groups, we need to rename files that conflict
    used_names = set(root_files.keys())
    # Also collect names of flatten files that won't collide
    for row in conn.execute("SELECT DISTINCT file_name FROM files WHERE action='flatten'"):
        used_names.add(row[0].lower())

    rename_count = 0
    for fname in collision_groups:
        # Get all flatten files with this name
        rows = conn.execute("""
            SELECT id, full_path, size_bytes, date_created
            FROM files
            WHERE file_name=? AND action='flatten'
            ORDER BY date_created ASC
        """, (fname,)).fetchall()

        name_lower = fname.lower()
        root_size = root_files.get(name_lower)

        # Separate into: files that match root size (true dups of root file) and others
        if root_size is not None:
            # Files matching root size → delete as duplicates of the root file
            # Files NOT matching root size → collision rename
            for fid, fpath, fsize, fcreated in rows:
                if fsize == root_size:
                    conn.execute(
                        "UPDATE files SET action='delete', is_duplicate=1 WHERE id=?", (fid,)
                    )
                    stats["duplicates_to_delete"] += 1
                    stats["total_dup_space_bytes"] += fsize
                else:
                    new_name = _make_unique_name(fname, _parent_folder_name(fpath), used_names)
                    used_names.add(new_name.lower())
                    conn.execute(
                        "UPDATE files SET action='collision_rename', new_name=? WHERE id=?",
                        (new_name, fid),
                    )
                    rename_count += 1
        else:
            # No root file — multiple flatten files with same name but different sizes
            # Keep the first (oldest) as-is, rename the rest
            first = True
            seen_sizes = {}
            for fid, fpath, fsize, fcreated in rows:
                if first:
                    # Keep the oldest with its original name
                    first = False
                    seen_sizes[fsize] = True
                    continue
                if fsize in seen_sizes:
                    # Same name AND same size as one we're already keeping → duplicate
                    conn.execute(
                        "UPDATE files SET action='delete', is_duplicate=1 WHERE id=?", (fid,)
                    )
                    stats["duplicates_to_delete"] += 1
                    stats["total_dup_space_bytes"] += fsize
                else:
                    # Different size → collision rename
                    new_name = _make_unique_name(fname, _parent_folder_name(fpath), used_names)
                    used_names.add(new_name.lower())
                    conn.execute(
                        "UPDATE files SET action='collision_rename', new_name=? WHERE id=?",
                        (new_name, fid),
                    )
                    rename_count += 1
                    seen_sizes[fsize] = True

    conn.commit()
    stats["collision_renames"] = rename_count

    # Recount flatten (some may have changed to delete or collision_rename)
    row = conn.execute("SELECT COUNT(*) FROM files WHERE action='flatten'").fetchone()
    stats["files_to_flatten"] = row[0]

    elapsed = time.time() - t0
    log(f"Phase 2 complete in {elapsed:.1f}s")
    log(f"  Already at root:     {stats['already_at_root']:,}")
    log(f"  Duplicates to delete:{stats['duplicates_to_delete']:,} "
        f"(~{stats['total_dup_space_bytes'] / (1024**3):.2f} GB)")
    log(f"  Files to flatten:    {stats['files_to_flatten']:,}")
    log(f"  Collision renames:   {stats['collision_renames']:,}")

    return stats


def _make_unique_name(original_name: str, folder_name: str, used_names: set) -> str:
    """
    Generate a unique filename by prefixing with the parent folder name.
    If still not unique, append incrementing counters.
    """
    base, ext = os.path.splitext(original_name)

    # Sanitize folder name (remove chars illegal in filenames)
    safe_folder = "".join(c for c in folder_name if c not in r'<>:"/\|?*').strip()
    if not safe_folder:
        safe_folder = "UNKNOWN"

    candidate = f"{safe_folder}_{original_name}"
    if candidate.lower() not in used_names:
        return candidate

    # Still collides — add numeric suffix
    counter = 2
    while True:
        candidate = f"{safe_folder}_{base}_{counter}{ext}"
        if candidate.lower() not in used_names:
            return candidate
        counter += 1
        if counter > 99999:
            # Extreme fallback with timestamp
            ts = int(time.time() * 1000)
            return f"{safe_folder}_{base}_{ts}{ext}"


# ── Phase 3: Execute ─────────────────────────────────────────────────────────

def execute(conn: sqlite3.Connection) -> dict:
    """Execute moves and deletes. Returns stats."""
    log("Phase 3: Executing flatten ...", FLATTEN_LOG)
    t0 = time.time()

    exec_stats = {
        "deleted": 0,
        "delete_errors": 0,
        "moved": 0,
        "move_errors": 0,
        "renamed": 0,
        "rename_errors": 0,
        "dirs_removed": 0,
        "delete_bytes_freed": 0,
    }

    # ── Step 1: Delete duplicates ──
    log("  Step 1/3: Deleting duplicates ...", FLATTEN_LOG)
    cursor = conn.execute(
        "SELECT id, full_path, size_bytes FROM files WHERE action='delete' ORDER BY full_path"
    )
    rows = cursor.fetchall()
    for i, (fid, fpath, fsize) in enumerate(rows, 1):
        try:
            os.remove(fpath)
            exec_stats["deleted"] += 1
            exec_stats["delete_bytes_freed"] += fsize
            log(f"  DEL  {fpath}", FLATTEN_LOG)
        except PermissionError:
            exec_stats["delete_errors"] += 1
            log(f"  ERR  Permission denied: {fpath}", FLATTEN_LOG)
        except FileNotFoundError:
            exec_stats["deleted"] += 1  # Already gone, count as success
            log(f"  SKIP (not found): {fpath}", FLATTEN_LOG)
        except OSError as e:
            exec_stats["delete_errors"] += 1
            log(f"  ERR  {e}: {fpath}", FLATTEN_LOG)

        if i % PROGRESS_INTERVAL == 0:
            log(f"    ... deleted {i:,}/{len(rows):,}")

    log(f"  Deleted {exec_stats['deleted']:,} files "
        f"(~{exec_stats['delete_bytes_freed'] / (1024**3):.2f} GB freed), "
        f"{exec_stats['delete_errors']:,} errors", FLATTEN_LOG)

    # ── Step 2: Move 'flatten' files to root ──
    log("  Step 2/3: Moving files to root ...", FLATTEN_LOG)
    cursor = conn.execute(
        "SELECT id, full_path, file_name FROM files WHERE action='flatten' ORDER BY full_path"
    )
    rows = cursor.fetchall()
    for i, (fid, fpath, fname) in enumerate(rows, 1):
        if _is_at_root(fpath):
            # Should not happen (already 'keep'), but be safe
            continue
        dest = os.path.join(DRIVE, fname)
        try:
            # Same-drive move = metadata-only rename, near-instant
            os.rename(fpath, dest)
            exec_stats["moved"] += 1
            log(f"  MOV  {fpath} → {dest}", FLATTEN_LOG)
        except FileExistsError:
            # Edge case: file appeared at dest since planning
            exec_stats["move_errors"] += 1
            log(f"  ERR  Destination exists: {dest} (source: {fpath})", FLATTEN_LOG)
        except PermissionError:
            exec_stats["move_errors"] += 1
            log(f"  ERR  Permission denied: {fpath}", FLATTEN_LOG)
        except FileNotFoundError:
            exec_stats["move_errors"] += 1
            log(f"  ERR  Source not found: {fpath}", FLATTEN_LOG)
        except OSError as e:
            exec_stats["move_errors"] += 1
            log(f"  ERR  {e}: {fpath}", FLATTEN_LOG)

        if i % PROGRESS_INTERVAL == 0:
            log(f"    ... moved {i:,}/{len(rows):,}")

    log(f"  Moved {exec_stats['moved']:,} files, "
        f"{exec_stats['move_errors']:,} errors", FLATTEN_LOG)

    # ── Step 3: Move 'collision_rename' files to root with new names ──
    log("  Step 3/3: Moving collision-renamed files to root ...", FLATTEN_LOG)
    cursor = conn.execute(
        "SELECT id, full_path, new_name FROM files WHERE action='collision_rename' ORDER BY full_path"
    )
    rows = cursor.fetchall()
    for i, (fid, fpath, new_name) in enumerate(rows, 1):
        dest = os.path.join(DRIVE, new_name)
        try:
            os.rename(fpath, dest)
            exec_stats["renamed"] += 1
            log(f"  REN  {fpath} → {dest}", FLATTEN_LOG)
        except FileExistsError:
            exec_stats["rename_errors"] += 1
            log(f"  ERR  Destination exists: {dest} (source: {fpath})", FLATTEN_LOG)
        except PermissionError:
            exec_stats["rename_errors"] += 1
            log(f"  ERR  Permission denied: {fpath}", FLATTEN_LOG)
        except FileNotFoundError:
            exec_stats["rename_errors"] += 1
            log(f"  ERR  Source not found: {fpath}", FLATTEN_LOG)
        except OSError as e:
            exec_stats["rename_errors"] += 1
            log(f"  ERR  {e}: {fpath}", FLATTEN_LOG)

        if i % PROGRESS_INTERVAL == 0:
            log(f"    ... renamed {i:,}/{len(rows):,}")

    log(f"  Renamed+moved {exec_stats['renamed']:,} files, "
        f"{exec_stats['rename_errors']:,} errors", FLATTEN_LOG)

    # ── Step 4: Remove empty directories (bottom-up) ──
    log("  Removing empty directories ...", FLATTEN_LOG)
    exec_stats["dirs_removed"] = _remove_empty_dirs(DRIVE)
    log(f"  Removed {exec_stats['dirs_removed']:,} empty directories", FLATTEN_LOG)

    elapsed = time.time() - t0
    log(f"Phase 3 complete in {elapsed:.1f}s", FLATTEN_LOG)

    return exec_stats


def _remove_empty_dirs(root: str) -> int:
    """Remove empty directories bottom-up. Returns count removed."""
    removed = 0
    # Walk bottom-up so children are removed before parents
    for dirpath, dirnames, filenames in os.walk(root, topdown=False):
        # Don't remove the root itself
        if os.path.normcase(os.path.normpath(dirpath)) == os.path.normcase(os.path.normpath(root)):
            continue
        # Skip system dirs
        basename = os.path.basename(dirpath)
        if _should_skip_dir(basename):
            continue
        try:
            # os.rmdir only removes empty dirs — safe
            os.rmdir(dirpath)
            removed += 1
        except OSError:
            pass  # Not empty or permission denied — skip
    return removed


# ── Summary ──────────────────────────────────────────────────────────────────

def print_summary(scan_count: int, dedup_stats: dict, exec_stats: dict = None):
    log("=" * 70)
    log("FLATTEN SUMMARY")
    log("=" * 70)
    log(f"  Files scanned:         {scan_count:,}")
    log(f"  Already at root:       {dedup_stats['already_at_root']:,}")
    log(f"  Duplicates found:      {dedup_stats['duplicates_to_delete']:,}")
    log(f"  Space reclaimable:     {dedup_stats['total_dup_space_bytes'] / (1024**3):.2f} GB")
    log(f"  Files to flatten:      {dedup_stats['files_to_flatten']:,}")
    log(f"  Collision renames:     {dedup_stats['collision_renames']:,}")

    if exec_stats:
        log("-" * 70)
        log(f"  Files deleted:         {exec_stats['deleted']:,}")
        log(f"  Delete errors:         {exec_stats['delete_errors']:,}")
        log(f"  Space freed:           {exec_stats['delete_bytes_freed'] / (1024**3):.2f} GB")
        log(f"  Files moved to root:   {exec_stats['moved']:,}")
        log(f"  Move errors:           {exec_stats['move_errors']:,}")
        log(f"  Files renamed+moved:   {exec_stats['renamed']:,}")
        log(f"  Rename errors:         {exec_stats['rename_errors']:,}")
        log(f"  Empty dirs removed:    {exec_stats['dirs_removed']:,}")
    log("=" * 70)


# ── Main ─────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(
        description="Flatten I:\\ drive — all files to root, zero subfolders, with dedup."
    )
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--manifest-only", action="store_true",
                       help="Phase 1 only: scan and build manifest DB")
    group.add_argument("--dry-run", action="store_true",
                       help="Phase 1+2: build manifest, plan actions, print stats (no file changes)")
    group.add_argument("--execute", action="store_true",
                       help="Phase 1+2+3: build manifest, plan, and execute moves/deletes")

    args = parser.parse_args()

    # Verify I:\ exists
    if not os.path.isdir(DRIVE):
        log(f"ERROR: Drive {DRIVE} not found or not accessible.")
        sys.exit(1)

    log(f"I:\\ Drive Flattener — started")
    log(f"  Manifest DB: {MANIFEST_DB}")
    log(f"  Log file:    {FLATTEN_LOG}")

    conn = get_db()
    create_schema(conn)

    try:
        # Phase 1: Manifest
        scan_count = build_manifest(conn)

        if args.manifest_only:
            log(f"Done (manifest-only). {scan_count:,} files in {MANIFEST_DB}")
            return

        # Phase 2: Dedup & Plan
        dedup_stats = deduplicate(conn)

        if args.dry_run:
            print_summary(scan_count, dedup_stats)
            log("Done (dry-run). No files were changed.")
            return

        # Phase 3: Execute
        exec_stats = execute(conn)
        print_summary(scan_count, dedup_stats, exec_stats)
        log(f"Done. Full log at {FLATTEN_LOG}")

    finally:
        conn.close()


if __name__ == "__main__":
    main()
