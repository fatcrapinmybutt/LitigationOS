#!/usr/bin/env python3
"""
OMEGA FLATTEN P5 - CROSS-DRIVE SCAN + MIGRATE
==============================================
Scans D/F/G/H/I drives for litigation-relevant files.
Deduplicates against existing LitigationOS inventory.
Copies unique files into the 15-folder structure.
Respects C: free space constraints (27GB - keep 5GB buffer).
"""
import os, sys, sqlite3, shutil, hashlib
from datetime import datetime
from collections import defaultdict

LOS = r'C:\Users\andre\LitigationOS'
DB  = os.path.join(LOS, 'litigation_context.db')
MAX_COPY_BYTES = 20 * 1024**3  # 20GB max copy (keep 7GB buffer on C:)

DRIVES = ['D:\\', 'F:\\', 'G:\\', 'H:\\', 'I:\\']

# Skip these directory patterns (case-insensitive)
SKIP_DIRS = {
    'node_modules', '.git', '__pycache__', '.next', '.nuxt',
    'dist', 'build', '.cache', '.npm', '.yarn', 'vendor',
    'packages', '.cargo', 'target', 'bin', 'obj',
    'efi', 'boot', 'sources', 'support', '$recycle.bin',
    '_recycle', 'windowsapps', 'system volume information',
    '.trash', '_trash', 'dedup_archive',  # already deduped
}

# High-priority extensions (litigation-relevant content)
PRIORITY_EXTS = {
    '.pdf', '.docx', '.doc', '.txt', '.md', '.rtf',
    '.csv', '.json', '.jsonl', '.xml', '.html', '.htm',
    '.xlsx', '.xls', '.yaml', '.yml', '.toml',
    '.png', '.jpg', '.jpeg', '.gif', '.bmp', '.svg', '.tiff',
    '.py', '.js', '.ts', '.sh', '.bat', '.ps1',
    '.db', '.sqlite', '.sql', '.mbox',
    '.zip', '.rar', '.7z', '.tar', '.gz',
    '.graphml', '.faiss',
}

# Skip these large binary extensions entirely
SKIP_EXTS = {
    '.exe', '.dll', '.msi', '.iso', '.img', '.vmdk', '.vhd',
    '.wasm', '.node', '.so', '.dylib', '.o', '.a',
    '.mp4', '.mkv', '.avi', '.mov', '.flv', '.wmv',
    '.mp3', '.wav', '.flac', '.aac', '.ogg',
    '.psd', '.ai', '.indd', '.sketch',
    '.class', '.jar', '.war', '.pyc', '.pyo',
    '.map', '.bcmap', '.mjs', '.cjs',
}

# Extension → target folder mapping
EXT_MAP = {
    '.pdf': '07_PDF', '.txt': '08_TEXT', '.md': '08_TEXT', '.docx': '08_TEXT',
    '.doc': '08_TEXT', '.rtf': '08_TEXT', '.log': '08_TEXT',
    '.csv': '09_DATA', '.json': '09_DATA', '.jsonl': '09_DATA',
    '.xml': '09_DATA', '.html': '09_DATA', '.htm': '09_DATA',
    '.db': '09_DATA', '.sqlite': '09_DATA', '.sql': '09_DATA',
    '.graphml': '09_DATA', '.mbox': '09_DATA', '.faiss': '09_DATA',
    '.xls': '09_DATA', '.xlsx': '09_DATA', '.yaml': '09_DATA', '.yml': '09_DATA',
    '.toml': '09_DATA', '.ini': '09_DATA', '.cfg': '09_DATA',
    '.jpg': '10_IMAGES', '.jpeg': '10_IMAGES', '.png': '10_IMAGES',
    '.gif': '10_IMAGES', '.bmp': '10_IMAGES', '.svg': '10_IMAGES',
    '.tiff': '10_IMAGES', '.webp': '10_IMAGES',
    '.py': '11_CODE', '.js': '11_CODE', '.ts': '11_CODE',
    '.jsx': '11_CODE', '.tsx': '11_CODE', '.sh': '11_CODE',
    '.bat': '11_CODE', '.ps1': '11_CODE', '.svelte': '11_CODE',
    '.vue': '11_CODE', '.css': '11_CODE', '.scss': '11_CODE',
    '.go': '11_CODE', '.rs': '11_CODE',
    '.zip': '12_ARCHIVES', '.rar': '12_ARCHIVES', '.7z': '12_ARCHIVES',
    '.tar': '12_ARCHIVES', '.gz': '12_ARCHIVES', '.bz2': '12_ARCHIVES',
}

# Court action routing patterns (from P2)
import re
COURT_PATTERNS = [
    (re.compile(r'PKG[_\-]?05|COA|366810|court.of.appeals|appellate', re.I), '01_COA_366810'),
    (re.compile(r'PKG[_\-]?0[1367]|14th.circuit|trial.court|2024.001507|custody|parenting.time|child.support', re.I), '02_TRIAL_14TH'),
    (re.compile(r'PKG[_\-]?08|federal|1983|civil.rights|42.usc', re.I), '03_FEDERAL_1983'),
    (re.compile(r'PKG[_\-]?09|JTC|judicial.tenure|mcneill|jenny', re.I), '04_JTC_MCNEILL'),
    (re.compile(r'PKG[_\-]?10|bar.complaint|barnes|attorney.grievance|P55406', re.I), '05_BAR_BARNES'),
    (re.compile(r'PKG[_\-]?1[12]|emergency|ex.parte|TRO|PPO|immediate', re.I), '06_EMERGENCY'),
]

stats = defaultdict(int)
log_lines = []
copied_bytes = 0

def log(msg):
    ts = datetime.now().strftime('%H:%M:%S')
    line = f"[{ts}] {msg}"
    print(line, flush=True)
    log_lines.append(line)

def classify_file(fname, fpath):
    """Determine target folder for a file."""
    # Check court patterns first
    check_str = fname + ' ' + fpath
    for pattern, target in COURT_PATTERNS:
        if pattern.search(check_str):
            return target
    # Extension-based
    ext = os.path.splitext(fname)[1].lower()
    return EXT_MAP.get(ext, '09_DATA')

def get_subfolder(target, ext):
    """Get subfolder within target."""
    if target == '07_PDF': return 'cross_drive'
    if target == '08_TEXT': return 'cross_drive'
    if target == '09_DATA': return 'cross_drive'
    if target == '10_IMAGES': return 'cross_drive'
    if target == '11_CODE': return 'cross_drive'
    if target == '12_ARCHIVES': return 'cross_drive'
    if target.startswith(('01_','02_','03_','04_','05_','06_')):
        return 'cross_drive'
    return ''

# ============================================================
log("=" * 70)
log("  OMEGA FLATTEN P5 - CROSS-DRIVE SCAN + MIGRATE")
log("=" * 70)

# Connect to DB
conn = sqlite3.connect(DB)
cur = conn.cursor()

# Create external inventory table
cur.execute("""
CREATE TABLE IF NOT EXISTS file_inventory_external (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    drive TEXT,
    file_path TEXT,
    file_name TEXT,
    extension TEXT,
    file_size INTEGER,
    is_duplicate INTEGER DEFAULT 0,
    target_folder TEXT,
    copied INTEGER DEFAULT 0
)
""")
cur.execute("DELETE FROM file_inventory_external")
conn.commit()

# ============================================================
# STEP 1: Scan all external drives
# ============================================================
log("\n[STEP 1] Scanning external drives...")

total_scanned = 0
for drive in DRIVES:
    if not os.path.exists(drive):
        log(f"  {drive} not available, skipping")
        continue

    drive_letter = drive[0]
    drive_files = 0
    batch = []

    log(f"\n  Scanning {drive}...")

    LITIGATION_KW = {'litigation', 'pigors', 'watson', 'court', 'filing',
                     'motion', 'order', 'exhibit', 'evidence', 'custody',
                     'mcneill', 'barnes', 'affidavit', 'brief', 'appeal',
                     'jtc', 'judicial', 'delta', 'pkg'}
    scan_count = 0
    try:
        for root, dirs, files in os.walk(drive, topdown=True):
            # Skip hidden/system/bloat directories
            dirs[:] = [d for d in dirs if d.lower() not in SKIP_DIRS and not d.startswith('.')]

            root_lower = root.lower()
            for fname in files:
                ext = os.path.splitext(fname)[1].lower()

                # Skip binary bloat
                if ext in SKIP_EXTS:
                    stats['skipped_binary'] += 1
                    continue

                fpath = os.path.join(root, fname)
                try:
                    fsize = os.path.getsize(fpath)
                except:
                    continue

                if fsize < 100:
                    stats['skipped_tiny'] += 1
                    continue
                if fsize > 500 * 1024 * 1024:
                    stats['skipped_huge'] += 1
                    continue

                # Only index priority extensions + anything litigation-named
                is_priority = ext in PRIORITY_EXTS
                if not is_priority:
                    fname_lower = fname.lower()
                    is_litigation = any(kw in fname_lower or kw in root_lower for kw in LITIGATION_KW)
                    if not is_litigation:
                        stats['skipped_irrelevant'] += 1
                        continue

                batch.append((drive_letter, fpath, fname, ext, fsize))
                drive_files += 1

                if len(batch) >= 5000:
                    cur.executemany(
                        "INSERT INTO file_inventory_external (drive, file_path, file_name, extension, file_size) VALUES (?,?,?,?,?)",
                        batch)
                    conn.commit()
                    batch = []

                scan_count += 1
                if scan_count % 10000 == 0:
                    log(f"    {drive_letter}: {drive_files:,} indexed so far... ({scan_count:,} checked)")
    except Exception as e:
        log(f"    {drive_letter}: SCAN ERROR: {e}")

    if batch:
        cur.executemany(
            "INSERT INTO file_inventory_external (drive, file_path, file_name, extension, file_size) VALUES (?,?,?,?,?)",
            batch)
        conn.commit()

    total_scanned += drive_files
    log(f"    {drive_letter}: {drive_files:,} relevant files indexed")

log(f"\n  Total external files indexed: {total_scanned:,}")
log(f"  Skipped: {stats['skipped_binary']:,} binary, {stats['skipped_tiny']:,} tiny, {stats['skipped_huge']:,} huge, {stats['skipped_irrelevant']:,} irrelevant")

# ============================================================
# STEP 2: Create indexes and deduplicate against LitigationOS
# ============================================================
log("\n[STEP 2] Deduplicating against LitigationOS inventory...")

cur.execute("CREATE INDEX IF NOT EXISTS idx_fie_name_size ON file_inventory_external (file_name, file_size)")

# Mark duplicates: files that already exist in LitigationOS (same name + size)
cur.execute("""
UPDATE file_inventory_external SET is_duplicate = 1
WHERE EXISTS (
    SELECT 1 FROM file_inventory fi
    WHERE fi.file_name = file_inventory_external.file_name
    AND fi.file_size = file_inventory_external.file_size
)
""")
conn.commit()

# Also mark cross-drive duplicates (keep first occurrence by smallest rowid)
cur.execute("""
UPDATE file_inventory_external SET is_duplicate = 1
WHERE id NOT IN (
    SELECT MIN(id) FROM file_inventory_external
    WHERE is_duplicate = 0
    GROUP BY file_name, file_size
)
AND is_duplicate = 0
""")
conn.commit()

cur.execute("SELECT COUNT(*) FROM file_inventory_external WHERE is_duplicate = 0")
unique_count = cur.fetchone()[0]
cur.execute("SELECT COUNT(*) FROM file_inventory_external WHERE is_duplicate = 1")
dup_count = cur.fetchone()[0]
cur.execute("SELECT SUM(file_size) FROM file_inventory_external WHERE is_duplicate = 0")
unique_size = cur.fetchone()[0] or 0

log(f"  Unique files to migrate: {unique_count:,} ({unique_size/1e9:.2f} GB)")
log(f"  Duplicates (already in LOS): {dup_count:,}")

if unique_size > MAX_COPY_BYTES:
    log(f"  WARNING: {unique_size/1e9:.1f}GB exceeds {MAX_COPY_BYTES/1e9:.0f}GB limit. Will prioritize by extension.")

# ============================================================
# STEP 3: Classify unique files
# ============================================================
log("\n[STEP 3] Classifying unique files...")

cur.execute("SELECT id, file_name, file_path FROM file_inventory_external WHERE is_duplicate = 0")
rows = cur.fetchall()

classify_batch = []
for fid, fname, fpath in rows:
    target = classify_file(fname, fpath)
    classify_batch.append((target, fid))
    if len(classify_batch) >= 5000:
        cur.executemany("UPDATE file_inventory_external SET target_folder = ? WHERE id = ?", classify_batch)
        conn.commit()
        classify_batch = []

if classify_batch:
    cur.executemany("UPDATE file_inventory_external SET target_folder = ? WHERE id = ?", classify_batch)
    conn.commit()

# Show distribution
log("\n  Target distribution:")
cur.execute("""
    SELECT target_folder, COUNT(*), SUM(file_size)
    FROM file_inventory_external WHERE is_duplicate = 0
    GROUP BY target_folder ORDER BY COUNT(*) DESC
""")
for row in cur.fetchall():
    folder, count, size = row
    log(f"    {folder or 'UNKNOWN':25s} {count:>8,} files  {(size or 0)/1e6:>10,.1f} MB")

# ============================================================
# STEP 4: Copy unique files to LitigationOS
# ============================================================
log("\n[STEP 4] Migrating unique files to LitigationOS...")

# Prioritize: court filings first, then content docs, then data, then code/tools
PRIORITY_ORDER = [
    '01_COA_366810', '02_TRIAL_14TH', '03_FEDERAL_1983',
    '04_JTC_MCNEILL', '05_BAR_BARNES', '06_EMERGENCY',
    '07_PDF', '08_TEXT', '09_DATA', '10_IMAGES', '11_CODE', '12_ARCHIVES'
]

for target in PRIORITY_ORDER:
    if copied_bytes >= MAX_COPY_BYTES:
        log(f"  BUDGET EXHAUSTED at {copied_bytes/1e9:.2f}GB")
        break

    cur.execute("""
        SELECT id, file_path, file_name, extension, file_size
        FROM file_inventory_external
        WHERE is_duplicate = 0 AND target_folder = ? AND copied = 0
        ORDER BY file_size DESC
    """, (target,))
    rows = cur.fetchall()
    if not rows:
        continue

    target_copied = 0
    target_skipped = 0
    target_bytes = 0

    for fid, fpath, fname, ext, fsize in rows:
        if copied_bytes + fsize > MAX_COPY_BYTES:
            target_skipped += 1
            continue

        sub = get_subfolder(target, ext)
        dest_dir = os.path.join(LOS, target, sub) if sub else os.path.join(LOS, target)
        os.makedirs(dest_dir, exist_ok=True)
        dest = os.path.join(dest_dir, fname)

        # Handle collision
        if os.path.exists(dest):
            base, ext2 = os.path.splitext(fname)
            counter = 1
            while os.path.exists(dest):
                dest = os.path.join(dest_dir, f"{base}_{counter}{ext2}")
                counter += 1

        try:
            shutil.copy2(fpath, dest)
            copied_bytes += fsize
            target_copied += 1
            target_bytes += fsize
            cur.execute("UPDATE file_inventory_external SET copied = 1 WHERE id = ?", (fid,))
        except Exception as e:
            stats['copy_fail'] += 1

        if target_copied % 1000 == 0 and target_copied > 0:
            conn.commit()

    conn.commit()
    if target_copied > 0:
        log(f"  {target:25s} → {target_copied:,} files ({target_bytes/1e6:,.1f} MB)")
    stats['total_copied'] += target_copied

log(f"\n  Total copied: {stats['total_copied']:,} files ({copied_bytes/1e9:.2f} GB)")
log(f"  Copy failures: {stats['copy_fail']:,}")

# ============================================================
# STEP 5: Final verification
# ============================================================
log("\n[STEP 5] Updated LitigationOS structure:")
log(f"\n  {'FOLDER':30s} {'FILES':>10s} {'SIZE_MB':>12s}")
log(f"  {'-'*54}")

total_files = 0
total_size = 0
for item in sorted(os.listdir(LOS)):
    path = os.path.join(LOS, item)
    if not os.path.isdir(path) or item.startswith('.'):
        continue
    try:
        count = sum(1 for _, _, fs in os.walk(path) for _ in fs)
        size = sum(os.path.getsize(os.path.join(r, f))
                   for r, _, fs in os.walk(path) for f in fs
                   if os.path.exists(os.path.join(r, f)))
    except:
        count = size = 0
    log(f"  {item:30s} {count:>10,} {size/1e6:>10,.1f}")
    total_files += count
    total_size += size

log(f"  {'-'*54}")
log(f"  {'TOTAL':30s} {total_files:>10,} {total_size/1e6:>10,.1f}")

# C: free space check
import ctypes
free_bytes = ctypes.c_ulonglong(0)
ctypes.windll.kernel32.GetDiskFreeSpaceExW(ctypes.c_wchar_p('C:\\'), None, None, ctypes.pointer(free_bytes))
log(f"\n  C: Free space remaining: {free_bytes.value/1e9:.1f} GB")

conn.close()

# Save log
with open(os.path.join(LOS, '00_SYSTEM', 'OMEGA_FLATTEN_P5_LOG.txt'), 'w', encoding='utf-8') as f:
    f.write('\n'.join(log_lines))

log(f"\n{'='*70}")
log(f"  PHASE 5 CROSS-DRIVE MIGRATION COMPLETE")
log(f"  Scanned: {total_scanned:,} relevant files across {len(DRIVES)} drives")
log(f"  Unique: {unique_count:,} | Duplicates: {dup_count:,}")
log(f"  Copied: {stats['total_copied']:,} files ({copied_bytes/1e9:.2f} GB)")
log(f"{'='*70}")
