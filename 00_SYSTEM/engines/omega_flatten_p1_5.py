#!/usr/bin/env python3
"""
OMEGA FLATTEN P1.5 - OPTIMIZED DEDUP + RAR EXTRACTION
=====================================================
Phase 1 completed inventory (467K files) and extracted 784 archives.
This script: adds indexes, runs fast dedup, installs rarfile/py7zr, extracts remaining.
"""
import os, sys, sqlite3, subprocess, time
from datetime import datetime
from pathlib import Path

LOS = str(Path(__file__).resolve().parents[2])
DB = os.path.join(LOS, 'litigation_context.db')

conn = sqlite3.connect(DB)
conn.execute("PRAGMA busy_timeout=60000")
conn.execute("PRAGMA journal_mode=WAL")
conn.execute("PRAGMA cache_size=-32000")
conn.execute("PRAGMA synchronous=NORMAL")
cur = conn.cursor()

print(f"[{datetime.now().strftime('%H:%M:%S')}] === OMEGA FLATTEN P1.5 ===")

# Verify inventory exists
cur.execute("SELECT COUNT(*) FROM file_inventory")
total = cur.fetchone()[0]
print(f"  File inventory: {total:,} files")

if total == 0:
    print("  ERROR: No files in inventory. Run omega_flatten_p1.py first.")
    sys.exit(1)

# ============================================================
# STEP 1: ADD INDEXES FOR FAST DEDUP
# ============================================================
print(f"\n[{datetime.now().strftime('%H:%M:%S')}] [STEP 1] Adding indexes...")
cur.execute("CREATE INDEX IF NOT EXISTS idx_fi_name_size ON file_inventory(file_name, file_size)")
cur.execute("CREATE INDEX IF NOT EXISTS idx_fi_ext ON file_inventory(extension)")
cur.execute("CREATE INDEX IF NOT EXISTS idx_fi_dup ON file_inventory(is_duplicate)")
cur.execute("CREATE INDEX IF NOT EXISTS idx_fi_prot ON file_inventory(is_protected)")
conn.commit()
print("  Indexes created.")

# ============================================================
# STEP 2: FAST DEDUP USING WINDOW FUNCTIONS
# ============================================================
print(f"\n[{datetime.now().strftime('%H:%M:%S')}] [STEP 2] Running dedup analysis...")

# Use ROW_NUMBER to mark all but first (shortest path) as duplicate
cur.execute("""
    UPDATE file_inventory SET is_duplicate = 1
    WHERE id IN (
        SELECT id FROM (
            SELECT id,
                   ROW_NUMBER() OVER (
                       PARTITION BY file_name, file_size
                       ORDER BY LENGTH(file_path) ASC
                   ) as rn
            FROM file_inventory
            WHERE is_protected = 0 AND file_size > 0
        ) WHERE rn > 1
    )
""")
conn.commit()

dup_count = cur.execute("SELECT changes()").fetchone()[0]
# Get actual counts
cur.execute("SELECT COUNT(*), COALESCE(SUM(file_size),0) FROM file_inventory WHERE is_duplicate=1")
dup_cnt, dup_sz = cur.fetchone()
print(f"  Duplicates marked: {dup_cnt:,} files ({dup_sz/1e9:.2f} GB)")

# Top duplicate files by count
cur.execute("""
    SELECT file_name, file_size, COUNT(*) as cnt
    FROM file_inventory
    WHERE is_protected = 0 AND file_size > 0
    GROUP BY file_name, file_size
    HAVING cnt > 3
    ORDER BY cnt * file_size DESC
    LIMIT 20
""")
print("\n  TOP 20 DUPLICATED FILES (by wasted space):")
for fname, fsize, cnt in cur.fetchall():
    wasted = fsize * (cnt - 1)
    print(f"    {cnt:>4}x  {wasted/1e6:>10,.1f} MB  {fname[:60]}")

# ============================================================
# STEP 3: INSTALL RARFILE + PY7ZR, EXTRACT REMAINING
# ============================================================
print(f"\n[{datetime.now().strftime('%H:%M:%S')}] [STEP 3] Installing rar/7z support...")

for pkg in ['rarfile', 'py7zr']:
    try:
        __import__(pkg)
        print(f"  {pkg} already installed")
    except ImportError:
        print(f"  Installing {pkg}...")
        subprocess.run([sys.executable, '-m', 'pip', 'install', pkg, '-q'], check=False)

# Try extracting RARs
rar_extracted = 0
try:
    import rarfile
    cur.execute("SELECT id, file_path FROM file_inventory WHERE extension='.rar' AND is_protected=0")
    rars = cur.fetchall()
    print(f"\n  Found {len(rars)} RAR files to extract")
    for fid, fpath in rars:
        if not os.path.exists(fpath):
            continue
        extract_dir = fpath + '_extracted'
        try:
            with rarfile.RarFile(fpath, 'r') as rf:
                if len(rf.namelist()) == 0:
                    continue
                os.makedirs(extract_dir, exist_ok=True)
                rf.extractall(extract_dir)
                rar_extracted += 1
                new_count = len(rf.namelist())
                print(f"    [OK] {os.path.basename(fpath)} → {new_count} files")
        except Exception as e:
            print(f"    [FAIL] {os.path.basename(fpath)}: {e}")
except ImportError:
    print("  WARNING: rarfile installed but unrar tool not found. RAR extraction skipped.")
    print("  (Need unrar.exe in PATH for RAR support)")
except Exception as e:
    print(f"  RAR extraction error: {e}")

# Try extracting 7z
sz_extracted = 0
try:
    import py7zr
    cur.execute("SELECT id, file_path FROM file_inventory WHERE extension='.7z' AND is_protected=0")
    sevenzs = cur.fetchall()
    print(f"\n  Found {len(sevenzs)} 7z files to extract")
    for fid, fpath in sevenzs:
        if not os.path.exists(fpath):
            continue
        extract_dir = fpath + '_extracted'
        try:
            with py7zr.SevenZipFile(fpath, 'r') as zf:
                os.makedirs(extract_dir, exist_ok=True)
                zf.extractall(extract_dir)
                sz_extracted += 1
                print(f"    [OK] {os.path.basename(fpath)}")
        except Exception as e:
            print(f"    [FAIL] {os.path.basename(fpath)}: {e}")
except ImportError:
    print("  py7zr import failed")

# ============================================================
# STEP 4: RE-INVENTORY NEW FILES FROM RAR/7Z
# ============================================================
if rar_extracted + sz_extracted > 0:
    print(f"\n[{datetime.now().strftime('%H:%M:%S')}] [STEP 4] Re-inventorying new files...")
    cur.execute("SELECT file_path FROM file_inventory")
    known_paths = set(r[0] for r in cur.fetchall())

    archive_exts = {'.zip', '.rar', '.7z', '.tar', '.gz', '.tgz', '.bz2'}
    new_batch = []
    new_found = 0

    for root, dirs, files in os.walk(LOS):
        dirs[:] = [d for d in dirs if not d.startswith('.')]
        rel = os.path.relpath(root, LOS)
        top = rel.split(os.sep)[0] if rel != '.' else '_ROOT'
        is_prot = 1 if top in {'00_SYSTEM', '.copilot', '.agents', '.github', '.vscode'} else 0

        for fname in files:
            fpath = os.path.join(root, fname)
            if fpath in known_paths:
                continue
            try:
                fsize = os.path.getsize(fpath)
            except OSError:
                fsize = 0
            ext = os.path.splitext(fname)[1].lower()
            is_arch = 1 if ext in archive_exts else 0
            new_batch.append((fpath, fname, ext, fsize, os.path.basename(root), top, is_arch, is_prot))
            new_found += 1

            if len(new_batch) >= 5000:
                cur.executemany(
                    "INSERT INTO file_inventory (file_path, file_name, extension, file_size, parent_folder, top_folder, is_archive, is_protected) VALUES (?,?,?,?,?,?,?,?)",
                    new_batch)
                conn.commit()
                new_batch = []

    if new_batch:
        cur.executemany(
            "INSERT INTO file_inventory (file_path, file_name, extension, file_size, parent_folder, top_folder, is_archive, is_protected) VALUES (?,?,?,?,?,?,?,?)",
            new_batch)
        conn.commit()

    print(f"  New files from RAR/7z: {new_found:,}")

# ============================================================
# STEP 5: FINAL SUMMARY
# ============================================================
print(f"\n[{datetime.now().strftime('%H:%M:%S')}] === PHASE 1.5 SUMMARY ===")

cur.execute("SELECT COUNT(*), COALESCE(SUM(file_size),0) FROM file_inventory")
total_cnt, total_sz = cur.fetchone()
cur.execute("SELECT COUNT(*), COALESCE(SUM(file_size),0) FROM file_inventory WHERE is_duplicate=1")
dup_cnt, dup_sz = cur.fetchone()
cur.execute("SELECT COUNT(*), COALESCE(SUM(file_size),0) FROM file_inventory WHERE is_protected=1")
prot_cnt, prot_sz = cur.fetchone()
cur.execute("SELECT COUNT(*), COALESCE(SUM(file_size),0) FROM file_inventory WHERE is_duplicate=0 AND is_protected=0")
move_cnt, move_sz = cur.fetchone()

print(f"  Total files:     {total_cnt:,} ({total_sz/1e9:.2f} GB)")
print(f"  Protected:       {prot_cnt:,} ({prot_sz/1e9:.2f} GB)")
print(f"  Duplicates:      {dup_cnt:,} ({dup_sz/1e9:.2f} GB reclaimable)")
print(f"  Unique movable:  {move_cnt:,} ({move_sz/1e9:.2f} GB)")
print(f"  RARs extracted:  {rar_extracted}")
print(f"  7Zs extracted:   {sz_extracted}")

# Extension breakdown for unique movable files
cur.execute("""
    SELECT extension, COUNT(*), SUM(file_size)
    FROM file_inventory
    WHERE is_duplicate=0 AND is_protected=0
    GROUP BY extension
    ORDER BY SUM(file_size) DESC
    LIMIT 20
""")
print(f"\n  TOP 20 EXTENSIONS (unique movable, by size):")
for ext, cnt, sz in cur.fetchall():
    print(f"    {ext or '(none)':12s} {cnt:>8,} files  {(sz or 0)/1e6:>10,.1f} MB")

conn.close()
print(f"\n[{datetime.now().strftime('%H:%M:%S')}] Phase 1.5 complete. Ready for Phase 2 (classify + reorganize).")
