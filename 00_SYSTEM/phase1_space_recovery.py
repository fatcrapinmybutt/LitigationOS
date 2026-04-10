"""
Phase 1: C:\ Space Recovery — Move duplicates to J:\, clean __pycache__
Uses FULL_INVENTORY.parquet via DuckDB for instant queries.
Rule 1 compliance: MOVE only, never delete user content.
"""
import duckdb, os, shutil, time, ctypes
from datetime import datetime

PARQUET = r'J:\LitigationOS_CENTRAL\FULL_INVENTORY.parquet'
ARCHIVE = r'J:\LitigationOS_CENTRAL\DEDUP_FROM_C'
REPORT_PATH = r'J:\LitigationOS_CENTRAL\PHASE1_RECOVERY_REPORT.md'

# Files we must NEVER move (active/system)
NEVER_MOVE = {
    'litigation_context.db', 'litigation_context.db-wal', 'litigation_context.db-shm',
    'hiberfil.sys', 'pagefile.sys', 'swapfile.sys',
    'claim_evidence_links.db', 'claim_evidence_links.db-wal', 'claim_evidence_links.db-shm',
    'lit_ctx_snapshot.db',
}

con = duckdb.connect()
report = []
t0 = time.time()

def log(msg):
    print(msg)
    report.append(msg)

def get_free_gb(drive='C:\\'):
    free = ctypes.c_ulonglong(0)
    ctypes.windll.kernel32.GetDiskFreeSpaceExW(drive, None, None, ctypes.byref(free))
    return free.value / (1024**3)

log("=" * 70)
log(f"PHASE 1: C:\\ SPACE RECOVERY — {datetime.now():%Y-%m-%d %H:%M}")
log(f"C:\\ free before: {get_free_gb():.2f} GB")
log("=" * 70)

# ══════════════════════════════════════════════════════════════
# PART A: Find C:\ duplicates (same filename + size, >1 MB)
# ══════════════════════════════════════════════════════════════
log("\n## PART A: C:\\ Internal Duplicates (>1 MB)")

dupes = con.execute(f"""
    SELECT file_name,
           ROUND(size_bytes / 1048576.0, 1) as mb,
           COUNT(*) as n,
           LIST(file_path ORDER BY
               CASE WHEN file_path LIKE '%LitigationOS%00_SYSTEM%' THEN 0
                    WHEN file_path LIKE '%LitigationOS%' THEN 1
                    ELSE 2
               END,
               LENGTH(file_path)
           ) as paths
    FROM read_parquet('{PARQUET}')
    WHERE drive_letter = 'C' AND size_bytes > 1048576
    GROUP BY file_name, size_bytes
    HAVING COUNT(*) > 1
    ORDER BY size_bytes * (COUNT(*) - 1) DESC
""").fetchall()

moves = []
total_waste_mb = 0.0

for name, mb, n, paths in dupes:
    if name in NEVER_MOVE:
        log(f"  SKIP (protected): {name} ({mb:.1f} MB × {n})")
        continue
    waste = mb * (n - 1)
    total_waste_mb += waste
    keep_path = paths[0]
    for extra in paths[1:]:
        moves.append((extra, mb, name))
    keep_dir = os.path.basename(os.path.dirname(keep_path))
    log(f"  {name}: {mb:.1f} MB × {n} = {waste:.1f} MB waste → keep in {keep_dir}/")

log(f"\n  Total duplicate waste: {total_waste_mb:.0f} MB ({total_waste_mb/1024:.1f} GB)")
log(f"  Files to move: {len(moves)}")

# ══════════════════════════════════════════════════════════════
# PART B: Execute moves (copy to J:\, verify, remove source)
# ══════════════════════════════════════════════════════════════
log(f"\n## PART B: Moving {len(moves)} duplicates to {ARCHIVE}")
os.makedirs(ARCHIVE, exist_ok=True)

moved_ct = 0
moved_mb = 0.0
skipped = 0
errors = []

for src, mb, fname in moves:
    if not os.path.exists(src):
        skipped += 1
        continue
    try:
        rel = os.path.relpath(src, 'C:\\')
        dst = os.path.join(ARCHIVE, rel)
        os.makedirs(os.path.dirname(dst), exist_ok=True)

        src_sz = os.path.getsize(src)
        if mb > 50:
            log(f"  ⏳ Copying {fname} ({mb:.0f} MB)...")
        shutil.copy2(src, dst)

        if os.path.getsize(dst) == src_sz:
            os.remove(src)
            moved_ct += 1
            moved_mb += mb
            log(f"  ✓ {fname} ({mb:.1f} MB)")
        else:
            os.remove(dst)
            errors.append(f"size mismatch after copy: {fname}")
    except PermissionError:
        skipped += 1
        log(f"  ⊘ LOCKED: {fname}")
    except Exception as e:
        errors.append(f"{fname}: {e}")

log(f"\n  Moved: {moved_ct} files = {moved_mb:.0f} MB freed")
log(f"  Skipped: {skipped}")
if errors:
    log(f"  Errors ({len(errors)}):")
    for e in errors[:10]:
        log(f"    ✗ {e}")

# ══════════════════════════════════════════════════════════════
# PART C: __pycache__ / .pyc cleanup on C:\
# ══════════════════════════════════════════════════════════════
log("\n## PART C: __pycache__ Cleanup (C:\\ only)")

pyc_paths = con.execute(f"""
    SELECT file_path, size_bytes
    FROM read_parquet('{PARQUET}')
    WHERE drive_letter = 'C' AND extension = 'pyc'
""").fetchall()

pyc_ct = 0
pyc_bytes = 0
for fpath, sz in pyc_paths:
    try:
        if os.path.exists(fpath):
            os.remove(fpath)
            pyc_ct += 1
            pyc_bytes += sz
    except:
        pass

# Remove empty __pycache__ dirs
pycache_dirs_removed = 0
for root, dirs, files in os.walk(r'C:\Users\andre\LitigationOS', topdown=False):
    if os.path.basename(root) == '__pycache__' and not os.listdir(root):
        try:
            os.rmdir(root)
            pycache_dirs_removed += 1
        except:
            pass

log(f"  .pyc files removed: {pyc_ct} ({pyc_bytes/1048576:.1f} MB)")
log(f"  Empty __pycache__ dirs removed: {pycache_dirs_removed}")

# ══════════════════════════════════════════════════════════════
# PART D: Cross-drive duplicate report (info only, no moves)
# ══════════════════════════════════════════════════════════════
log("\n## PART D: Cross-Drive Duplicates (C:\\ ↔ other drives, >10 MB)")

xdupes = con.execute(f"""
    WITH c_files AS (
        SELECT file_name, size_bytes, file_path
        FROM read_parquet('{PARQUET}')
        WHERE drive_letter = 'C' AND size_bytes > 10485760
    ),
    other AS (
        SELECT file_name, size_bytes, file_path, drive_letter
        FROM read_parquet('{PARQUET}')
        WHERE drive_letter != 'C' AND size_bytes > 10485760
    )
    SELECT c.file_name,
           ROUND(c.size_bytes / 1048576.0, 1) as mb,
           c.file_path as c_path,
           o.drive_letter as other_drive,
           o.file_path as other_path
    FROM c_files c JOIN other o
        ON c.file_name = o.file_name AND c.size_bytes = o.size_bytes
    ORDER BY c.size_bytes DESC
    LIMIT 20
""").fetchall()

xdupe_mb = 0.0
for name, mb, c_path, other_drive, other_path in xdupes:
    xdupe_mb += mb
    c_dir = os.path.basename(os.path.dirname(c_path))
    log(f"  {name} ({mb:.1f} MB): C:\\{c_dir}/ ↔ {other_drive}:\\")

log(f"\n  Cross-drive duplicate total on C:\\: {xdupe_mb:.0f} MB")
log(f"  (These are candidates for future consolidation)")

# ══════════════════════════════════════════════════════════════
# SUMMARY
# ══════════════════════════════════════════════════════════════
total_freed = moved_mb + pyc_bytes / 1048576
elapsed = time.time() - t0
free_after = get_free_gb()

log(f"\n{'=' * 70}")
log(f"PHASE 1 COMPLETE — {elapsed:.1f}s")
log(f"  Duplicates moved:  {moved_ct} files = {moved_mb:.0f} MB")
log(f"  __pycache__ cleaned: {pyc_ct} files = {pyc_bytes/1048576:.1f} MB")
log(f"  TOTAL FREED: {total_freed:.0f} MB ({total_freed/1024:.1f} GB)")
log(f"  C:\\ free space: {free_after:.2f} GB")
log(f"  Future opportunity: {xdupe_mb:.0f} MB cross-drive dedup")
log("=" * 70)

# Write report
with open(REPORT_PATH, 'w', encoding='utf-8') as f:
    f.write('\n'.join(report))
# Also copy to LitigationOS
with open(r'C:\Users\andre\LitigationOS\04_ANALYSIS\PHASE1_RECOVERY_REPORT.md', 'w', encoding='utf-8') as f:
    f.write('\n'.join(report))
log(f"\nReports saved.")

con.close()
