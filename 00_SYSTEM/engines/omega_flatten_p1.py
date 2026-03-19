#!/usr/bin/env python3
"""
OMEGA FLATTEN PIPELINE - PHASE 1: ABSORB + EXTRACT + INVENTORY
================================================================
1. Absorb 26+ straggler root folders into proper locations
2. Extract ALL archives (zip, rar, 7z, tar, gz) in-place
3. Build complete file inventory in DB table 'file_inventory'

Protected folders (untouched): 00_SYSTEM, .copilot, .agents, .github, .vscode
"""
import os, sys, shutil, sqlite3, zipfile, tarfile, gzip, hashlib, time
from datetime import datetime
from pathlib import Path
from collections import defaultdict

LOS = r'C:\Users\andre\LitigationOS'
DB = os.path.join(LOS, 'litigation_context.db')

PROTECTED = {'.copilot', '.agents', '.github', '.vscode', '00_SYSTEM'}

conn = sqlite3.connect(DB)
conn.execute("PRAGMA journal_mode=WAL")
conn.execute("PRAGMA synchronous=NORMAL")
cur = conn.cursor()

log_lines = []
stats = defaultdict(int)

def log(msg):
    ts = datetime.now().strftime('%H:%M:%S')
    line = f"[{ts}] {msg}"
    print(line)
    log_lines.append(line)

def save_log():
    log_path = os.path.join(LOS, '00_SYSTEM', 'OMEGA_FLATTEN_P1_LOG.txt')
    with open(log_path, 'w', encoding='utf-8') as f:
        f.write('\n'.join(log_lines))

# ============================================================
# STEP 1: ABSORB STRAGGLER FOLDERS
# ============================================================
log("=" * 70)
log("  OMEGA FLATTEN PHASE 1 - ABSORB + EXTRACT + INVENTORY")
log("=" * 70)

log("\n[STEP 1] Absorbing straggler root folders...")

# Map stragglers to their target locations
straggler_targets = {
    # Archive/unpacked content → 10_ARCHIVES/_STRAGGLERS
    '20260302_014913_v3_1_SCAO_LIVE_DISCOVERY_EXPANSION': '10_ARCHIVES/_STRAGGLERS',
    '20260302_1959_LITIGATIONOS_PIPERUNNER_EXECUTION_BUNDLE': '10_ARCHIVES/_STRAGGLERS',
    '20260302_2110_MI_SCAO_LIVE_DISCOVERY_CONTINUATION_v4_1': '10_ARCHIVES/_STRAGGLERS',
    '20260303_0129_SCAO_LIVE_DISCOVERY_MEEK2_MEEK3_WINPACK': '10_ARCHIVES/_STRAGGLERS',
    'CYCLEPACK_06_ADVERSARY_20260303_011222': '10_ARCHIVES/_STRAGGLERS',
    'CYCLEPACK_07_DATABASES_20260303_013443': '10_ARCHIVES/_STRAGGLERS',
    'CYCLEPACK_07_DATABASES_ADV2_20260303_015325': '10_ARCHIVES/_STRAGGLERS',
    'INGEST_LitigationOS_20260302_run2': '10_ARCHIVES/_STRAGGLERS',
    'INGEST_LitigationOS_20260303_run3': '10_ARCHIVES/_STRAGGLERS',
    'LitigationOS_ChatGPTExport_PartialParse_20260302_195853': '10_ARCHIVES/_STRAGGLERS',
    'LitigationOS_CourtInjection_v7_Pack_20260302_210825': '10_ARCHIVES/_STRAGGLERS',
    'LitigationOS_Execution_Run_EXEC_20260302_192501': '10_ARCHIVES/_STRAGGLERS',
    'LitigationOS_FactLedger_v2_20260302_201424': '10_ARCHIVES/_STRAGGLERS',
    'LitigationOS_FactLedger_v3_Convergence_20260302_202520': '10_ARCHIVES/_STRAGGLERS',
    'LitigationOS_FactLedger_v6_VerifiedPins_20260302_204913': '10_ARCHIVES/_STRAGGLERS',
    'LitigationOS_SCHEM_EXEC_20260302_193827': '10_ARCHIVES/_STRAGGLERS',
    'LitigationOS_USER_CANON_MERGE_v5_20260302_203743': '10_ARCHIVES/_STRAGGLERS',
    'MI_SCAO_LOCAL_INGEST_VECTOR_CASCADE_20260302_run1': '10_ARCHIVES/_STRAGGLERS',
    'MI_WEB_PIN_FOOTERS_TOP_FORMS_v20260302': '10_ARCHIVES/_STRAGGLERS',
    'QUOTELOCK_DEEP_07_DATABASES_20260303_020332': '10_ARCHIVES/_STRAGGLERS',
    'RUN6_INGEST_ALL_v20260302': '10_ARCHIVES/_STRAGGLERS',
    'WORKPACK_07_DATABASES_20260303_022353': '10_ARCHIVES/_STRAGGLERS',
    # Code/config stragglers
    'code': '11_CONFIG/_code',
    'inputs': '11_CONFIG/_inputs',
    'runs': '11_CONFIG/_runs',
    'yaml': '11_CONFIG/_yaml',
    # Ghost folder
    '16_DOCUMENTS': '09_DOCUMENTS/_ghost',
}

for folder_name, target_rel in straggler_targets.items():
    src = os.path.join(LOS, folder_name)
    if not os.path.exists(src):
        continue
    dest_parent = os.path.join(LOS, target_rel)
    dest = os.path.join(dest_parent, folder_name)
    os.makedirs(dest_parent, exist_ok=True)
    try:
        if os.path.exists(dest):
            # Merge into existing
            for item in os.listdir(src):
                s = os.path.join(src, item)
                d = os.path.join(dest, item)
                if not os.path.exists(d):
                    shutil.move(s, d)
                    stats['straggler_moved'] += 1
            try: os.rmdir(src)
            except: pass
        else:
            shutil.move(src, dest)
            stats['straggler_moved'] += 1
        log(f"  [OK] {folder_name} → {target_rel}")
    except Exception as e:
        log(f"  [FAIL] {folder_name}: {e}")
        stats['straggler_fail'] += 1

log(f"  Stragglers absorbed: {stats['straggler_moved']}")

# ============================================================
# STEP 2: BUILD FILE INVENTORY
# ============================================================
log("\n[STEP 2] Building complete file inventory...")

cur.execute("DROP TABLE IF EXISTS file_inventory")
cur.execute("""CREATE TABLE file_inventory (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    file_path TEXT,
    file_name TEXT,
    extension TEXT,
    file_size INTEGER,
    parent_folder TEXT,
    top_folder TEXT,
    is_archive INTEGER DEFAULT 0,
    is_duplicate INTEGER DEFAULT 0,
    is_protected INTEGER DEFAULT 0,
    target_folder TEXT,
    classification TEXT,
    processed INTEGER DEFAULT 0
)""")
conn.commit()

batch = []
total_files = 0
total_size = 0
archive_exts = {'.zip', '.rar', '.7z', '.tar', '.gz', '.tgz', '.tar.gz', '.bz2'}

for root, dirs, files in os.walk(LOS):
    # Skip hidden system folders
    dirs[:] = [d for d in dirs if not d.startswith('.')]
    rel = os.path.relpath(root, LOS)
    top = rel.split(os.sep)[0] if rel != '.' else '_ROOT'

    is_prot = 1 if top in PROTECTED else 0

    for fname in files:
        fpath = os.path.join(root, fname)
        try:
            fsize = os.path.getsize(fpath)
        except:
            fsize = 0
        ext = os.path.splitext(fname)[1].lower()
        is_arch = 1 if ext in archive_exts else 0

        batch.append((fpath, fname, ext, fsize, os.path.basename(root), top, is_arch, is_prot))
        total_files += 1
        total_size += fsize

        if len(batch) >= 5000:
            cur.executemany(
                "INSERT INTO file_inventory (file_path, file_name, extension, file_size, parent_folder, top_folder, is_archive, is_protected) VALUES (?,?,?,?,?,?,?,?)",
                batch)
            conn.commit()
            batch = []

    if total_files % 50000 == 0:
        log(f"  Inventoried: {total_files:,} files ({total_size/1e9:.1f} GB)...")

if batch:
    cur.executemany(
        "INSERT INTO file_inventory (file_path, file_name, extension, file_size, parent_folder, top_folder, is_archive, is_protected) VALUES (?,?,?,?,?,?,?,?)",
        batch)
    conn.commit()

log(f"  INVENTORY COMPLETE: {total_files:,} files, {total_size/1e9:.2f} GB")

# Extension breakdown
cur.execute("SELECT extension, COUNT(*), SUM(file_size) FROM file_inventory GROUP BY extension ORDER BY COUNT(*) DESC LIMIT 25")
log("\n  TOP 25 EXTENSIONS:")
for ext, cnt, sz in cur.fetchall():
    log(f"    {ext or '(none)':12s} {cnt:>8,} files  {(sz or 0)/1e6:>10,.1f} MB")

# Archive breakdown
cur.execute("SELECT extension, COUNT(*), SUM(file_size) FROM file_inventory WHERE is_archive=1 GROUP BY extension ORDER BY COUNT(*) DESC")
log("\n  ARCHIVES TO EXTRACT:")
for ext, cnt, sz in cur.fetchall():
    log(f"    {ext:8s} {cnt:>6,} files  {(sz or 0)/1e6:>10,.1f} MB")

# ============================================================
# STEP 3: EXTRACT ALL ARCHIVES
# ============================================================
log("\n[STEP 3] Extracting archives...")

cur.execute("SELECT id, file_path, extension, file_size FROM file_inventory WHERE is_archive=1 AND is_protected=0 ORDER BY file_size ASC")
archives = cur.fetchall()
log(f"  Found {len(archives)} archives to process")

extracted = 0
extract_failed = 0
new_files = 0

for idx, (fid, fpath, ext, fsize) in enumerate(archives):
    if not os.path.exists(fpath):
        continue

    # Extract directory = same dir as archive + _extracted suffix
    extract_dir = fpath + '_extracted'

    try:
        if ext == '.zip':
            try:
                with zipfile.ZipFile(fpath, 'r') as zf:
                    # Check if extractable
                    if len(zf.namelist()) == 0:
                        continue
                    os.makedirs(extract_dir, exist_ok=True)
                    zf.extractall(extract_dir)
                    new_count = len(zf.namelist())
            except (zipfile.BadZipFile, NotImplementedError, RuntimeError):
                continue

        elif ext in ('.tar', '.tgz'):
            try:
                with tarfile.open(fpath, 'r:*') as tf:
                    members = tf.getmembers()
                    if not members:
                        continue
                    os.makedirs(extract_dir, exist_ok=True)
                    tf.extractall(extract_dir, filter='data')
                    new_count = len(members)
            except (tarfile.TarError, EOFError):
                continue

        elif ext == '.gz' and not fpath.endswith('.tar.gz'):
            try:
                out_path = fpath[:-3]  # Remove .gz
                if os.path.exists(out_path):
                    continue
                with gzip.open(fpath, 'rb') as gz:
                    content = gz.read(50 * 1024 * 1024)  # Cap at 50MB per file
                with open(out_path, 'wb') as out:
                    out.write(content)
                new_count = 1
                extract_dir = None  # No directory created
            except (gzip.BadGzipFile, EOFError, OSError):
                continue

        elif ext == '.7z':
            # Try py7zr if available, otherwise skip
            try:
                import py7zr
                with py7zr.SevenZipFile(fpath, 'r') as z:
                    os.makedirs(extract_dir, exist_ok=True)
                    z.extractall(extract_dir)
                    new_count = len(z.getnames())
            except ImportError:
                log(f"  [SKIP] .7z - py7zr not installed: {os.path.basename(fpath)}")
                continue
            except Exception:
                continue

        elif ext == '.rar':
            # Try rarfile if available
            try:
                import rarfile
                with rarfile.RarFile(fpath, 'r') as rf:
                    os.makedirs(extract_dir, exist_ok=True)
                    rf.extractall(extract_dir)
                    new_count = len(rf.namelist())
            except ImportError:
                log(f"  [SKIP] .rar - rarfile not installed: {os.path.basename(fpath)}")
                continue
            except Exception:
                continue
        else:
            continue

        extracted += 1
        new_files += new_count
        if extracted % 50 == 0:
            log(f"  Extracted: {extracted}/{len(archives)} archives, {new_files:,} new files")

    except Exception as e:
        extract_failed += 1
        if extract_failed <= 10:
            log(f"  [FAIL] {os.path.basename(fpath)}: {e}")

log(f"  EXTRACTION COMPLETE: {extracted} archives → {new_files:,} new files | {extract_failed} failed")

# ============================================================
# STEP 4: RE-INVENTORY (pick up extracted files)
# ============================================================
log("\n[STEP 4] Re-inventorying extracted files...")

# Get current file paths for dedup
cur.execute("SELECT file_path FROM file_inventory")
known_paths = set(r[0] for r in cur.fetchall())

new_batch = []
new_found = 0

for root, dirs, files in os.walk(LOS):
    dirs[:] = [d for d in dirs if not d.startswith('.')]
    rel = os.path.relpath(root, LOS)
    top = rel.split(os.sep)[0] if rel != '.' else '_ROOT'
    is_prot = 1 if top in PROTECTED else 0

    for fname in files:
        fpath = os.path.join(root, fname)
        if fpath in known_paths:
            continue
        try:
            fsize = os.path.getsize(fpath)
        except:
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

log(f"  New files from extraction: {new_found:,}")

# ============================================================
# STEP 5: DEDUP ANALYSIS
# ============================================================
log("\n[STEP 5] Deduplication analysis...")

# Find exact name+size duplicates
cur.execute("""
    SELECT file_name, file_size, COUNT(*) as cnt
    FROM file_inventory
    WHERE is_protected = 0 AND file_size > 0
    GROUP BY file_name, file_size
    HAVING cnt > 1
    ORDER BY cnt DESC
""")
dup_groups = cur.fetchall()

total_dupes = 0
total_dup_size = 0
for fname, fsize, cnt in dup_groups:
    # Mark all but the first as duplicate
    cur.execute("""
        SELECT id, file_path FROM file_inventory
        WHERE file_name = ? AND file_size = ? AND is_protected = 0
        ORDER BY LENGTH(file_path) ASC
    """, (fname, fsize))
    rows = cur.fetchall()
    # Keep the one with shortest path (most likely in the right place)
    for row_id, fpath in rows[1:]:
        cur.execute("UPDATE file_inventory SET is_duplicate = 1 WHERE id = ?", (row_id,))
        total_dupes += 1
        total_dup_size += fsize

conn.commit()

log(f"  Duplicate files: {total_dupes:,}")
log(f"  Duplicate size: {total_dup_size/1e9:.2f} GB (reclaimable)")

# Summary
cur.execute("SELECT COUNT(*), SUM(file_size) FROM file_inventory")
total_cnt, total_sz = cur.fetchone()
cur.execute("SELECT COUNT(*), SUM(file_size) FROM file_inventory WHERE is_duplicate=1")
dup_cnt, dup_sz = cur.fetchone()
cur.execute("SELECT COUNT(*), SUM(file_size) FROM file_inventory WHERE is_protected=1")
prot_cnt, prot_sz = cur.fetchone()
cur.execute("SELECT COUNT(*), SUM(file_size) FROM file_inventory WHERE is_archive=1")
arch_cnt, arch_sz = cur.fetchone()

log(f"\n{'='*70}")
log(f"  PHASE 1 SUMMARY")
log(f"  Total files: {total_cnt:,} ({(total_sz or 0)/1e9:.2f} GB)")
log(f"  Protected:   {prot_cnt:,} ({(prot_sz or 0)/1e9:.2f} GB)")
log(f"  Archives:    {arch_cnt:,} ({(arch_sz or 0)/1e9:.2f} GB)")
log(f"  Duplicates:  {dup_cnt:,} ({(dup_sz or 0)/1e9:.2f} GB)")
log(f"  Unique movable: {total_cnt - (dup_cnt or 0) - (prot_cnt or 0):,}")
log(f"{'='*70}")

save_log()
conn.close()
print("\nPhase 1 complete. Log: 00_SYSTEM/OMEGA_FLATTEN_P1_LOG.txt")
