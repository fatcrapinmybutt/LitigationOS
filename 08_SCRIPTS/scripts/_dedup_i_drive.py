"""
I:\ Drive Content-Based Deduplicator
Strategy:
  Phase 1: Group by file size (instant, eliminates 99% of non-dupes)
  Phase 2: For same-size groups, SHA-256 hash (confirms duplicates)
  Phase 3: For same-hash groups, binary compare first+last 8KB (paranoia check)
  Phase 4: Keep shallowest path, delete deeper copies

Tracking: SQLite manifest DB at I:\dedup_manifest.db
"""
import sys, os, hashlib, sqlite3, time
from pathlib import Path
from collections import defaultdict

sys.stdout = open(sys.stdout.fileno(), mode='w', encoding='utf-8', errors='replace')

DRIVE = Path("I:/")
MANIFEST_DB = Path("I:/dedup_manifest.db")
MIN_FILE_SIZE = 1024  # Skip files < 1KB (not worth deduping)
BATCH_REPORT_EVERY = 500  # Print progress every N groups

def init_db():
    conn = sqlite3.connect(str(MANIFEST_DB))
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA busy_timeout=30000")
    conn.executescript("""
        CREATE TABLE IF NOT EXISTS dedup_log (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            kept_path TEXT,
            deleted_path TEXT,
            file_size INTEGER,
            sha256 TEXT,
            action TEXT DEFAULT 'deleted',
            timestamp TEXT DEFAULT (datetime('now'))
        );
        CREATE TABLE IF NOT EXISTS scan_stats (
            key TEXT PRIMARY KEY,
            value TEXT
        );
    """)
    conn.commit()
    return conn

def sha256_file(path, chunk_size=65536):
    """Hash file contents."""
    h = hashlib.sha256()
    try:
        with open(path, 'rb') as f:
            while True:
                chunk = f.read(chunk_size)
                if not chunk:
                    break
                h.update(chunk)
        return h.hexdigest()
    except (OSError, PermissionError):
        return None

def content_verify(path1, path2):
    """Binary compare first 8KB + last 8KB. Returns True if identical."""
    try:
        size1 = os.path.getsize(path1)
        size2 = os.path.getsize(path2)
        if size1 != size2:
            return False

        with open(path1, 'rb') as f1, open(path2, 'rb') as f2:
            # Compare first 8KB
            if f1.read(8192) != f2.read(8192):
                return False
            # Compare last 8KB
            if size1 > 8192:
                f1.seek(max(0, size1 - 8192))
                f2.seek(max(0, size2 - 8192))
                if f1.read() != f2.read():
                    return False
        return True
    except (OSError, PermissionError):
        return False

def path_depth(p):
    """Return nesting depth - prefer keeping shallower files."""
    return str(p).count(os.sep)

def scan_drive():
    """Phase 1: Build size-grouped inventory."""
    print(f"[Phase 1] Scanning I:\\ for files >= {MIN_FILE_SIZE} bytes...")
    size_groups = defaultdict(list)
    total_files = 0
    skipped = 0
    errors = 0

    for root, dirs, files in os.walk(str(DRIVE)):
        for fname in files:
            fpath = os.path.join(root, fname)
            # Skip manifest DB and its WAL/SHM files
            if fpath == str(MANIFEST_DB) or fpath.endswith('-wal') or fpath.endswith('-shm'):
                continue
            try:
                size = os.path.getsize(fpath)
                total_files += 1
                if size < MIN_FILE_SIZE:
                    skipped += 1
                    continue
                size_groups[size].append(fpath)
            except (OSError, PermissionError):
                errors += 1

            if total_files % 50000 == 0:
                print(f"  Scanned {total_files:,} files, {len(size_groups):,} size groups...")

    # Filter to only groups with duplicates
    dupe_groups = {s: paths for s, paths in size_groups.items() if len(paths) > 1}

    potential_dupes = sum(len(p) - 1 for p in dupe_groups.values())
    potential_savings = sum(s * (len(p) - 1) for s, p in dupe_groups.items())

    print(f"  Total files scanned: {total_files:,}")
    print(f"  Skipped (< {MIN_FILE_SIZE}B): {skipped:,}")
    print(f"  Errors: {errors:,}")
    print(f"  Size groups with potential dupes: {len(dupe_groups):,}")
    print(f"  Potential duplicate files: {potential_dupes:,}")
    print(f"  Potential savings: {potential_savings / (1024**3):.2f} GB")

    return dupe_groups

def hash_and_verify(dupe_groups, conn):
    """Phase 2+3: Hash same-size files, then content-verify."""
    print(f"\n[Phase 2] Hashing {len(dupe_groups):,} duplicate size groups...")

    confirmed_dupes = []  # [(keep_path, delete_paths, size, sha256)]
    total_hashed = 0
    group_num = 0

    # Sort by size descending - dedup biggest files first for max space savings
    sorted_groups = sorted(dupe_groups.items(), key=lambda x: x[0] * len(x[1]), reverse=True)

    for file_size, paths in sorted_groups:
        group_num += 1
        if group_num % BATCH_REPORT_EVERY == 0:
            print(f"  Processing group {group_num:,}/{len(sorted_groups):,} (hashed {total_hashed:,} files)...")

        # Hash all files in this size group
        hash_groups = defaultdict(list)
        for p in paths:
            h = sha256_file(p)
            if h:
                hash_groups[h].append(p)
                total_hashed += 1

        # For each hash group with dupes, content-verify
        for sha, hash_paths in hash_groups.items():
            if len(hash_paths) < 2:
                continue

            # Sort by path depth (shallowest first = keep)
            hash_paths.sort(key=path_depth)
            keep = hash_paths[0]
            candidates = hash_paths[1:]

            # Phase 3: Content verify each candidate against keeper
            verified_deletes = []
            for candidate in candidates:
                if content_verify(keep, candidate):
                    verified_deletes.append(candidate)

            if verified_deletes:
                confirmed_dupes.append((keep, verified_deletes, file_size, sha))

    total_deletable = sum(len(d) for _, d, _, _ in confirmed_dupes)
    total_savings = sum(s * len(d) for _, d, s, _ in confirmed_dupes)

    print(f"\n[Phase 2+3 Complete]")
    print(f"  Files hashed: {total_hashed:,}")
    print(f"  Confirmed duplicate clusters: {len(confirmed_dupes):,}")
    print(f"  Files to delete: {total_deletable:,}")
    print(f"  Space to reclaim: {total_savings / (1024**3):.2f} GB")

    return confirmed_dupes

def execute_dedup(confirmed_dupes, conn):
    """Phase 4: Delete confirmed duplicates, log everything."""
    total_to_delete = sum(len(d) for _, d, _, _ in confirmed_dupes)
    print(f"\n[Phase 4] Deleting {total_to_delete:,} confirmed duplicates...")

    deleted_count = 0
    deleted_bytes = 0
    errors = 0

    for keep, delete_paths, file_size, sha in confirmed_dupes:
        for dpath in delete_paths:
            try:
                os.remove(dpath)
                conn.execute(
                    "INSERT INTO dedup_log (kept_path, deleted_path, file_size, sha256) VALUES (?,?,?,?)",
                    (keep, dpath, file_size, sha)
                )
                deleted_count += 1
                deleted_bytes += file_size

                if deleted_count % 1000 == 0:
                    conn.commit()
                    print(f"  Deleted {deleted_count:,} files, freed {deleted_bytes/(1024**3):.2f} GB...")

            except (OSError, PermissionError) as e:
                errors += 1
                conn.execute(
                    "INSERT INTO dedup_log (kept_path, deleted_path, file_size, sha256, action) VALUES (?,?,?,?,'error')",
                    (keep, dpath, file_size, sha)
                )

    conn.commit()

    # Save stats
    conn.execute("INSERT OR REPLACE INTO scan_stats (key, value) VALUES ('last_run', datetime('now'))")
    conn.execute("INSERT OR REPLACE INTO scan_stats (key, value) VALUES ('deleted_count', ?)", (str(deleted_count),))
    conn.execute("INSERT OR REPLACE INTO scan_stats (key, value) VALUES ('deleted_bytes', ?)", (str(deleted_bytes),))
    conn.execute("INSERT OR REPLACE INTO scan_stats (key, value) VALUES ('errors', ?)", (str(errors),))
    conn.commit()

    print(f"\n{'='*60}")
    print(f"  DEDUP COMPLETE")
    print(f"  Files deleted: {deleted_count:,}")
    print(f"  Space freed: {deleted_bytes / (1024**3):.2f} GB")
    print(f"  Errors: {errors:,}")
    print(f"  Manifest: {MANIFEST_DB}")
    print(f"{'='*60}")

def main():
    start = time.time()
    conn = init_db()

    # Phase 1: Scan
    dupe_groups = scan_drive()

    if not dupe_groups:
        print("No potential duplicates found.")
        conn.close()
        return

    # Phase 2+3: Hash + verify
    confirmed = hash_and_verify(dupe_groups, conn)

    if not confirmed:
        print("No confirmed duplicates after content verification.")
        conn.close()
        return

    # Phase 4: Delete
    execute_dedup(confirmed, conn)

    elapsed = time.time() - start
    print(f"\nTotal time: {elapsed/60:.1f} minutes")
    conn.close()

if __name__ == '__main__':
    main()
