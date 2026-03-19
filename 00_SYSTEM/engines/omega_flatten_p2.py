#!/usr/bin/env python3
"""
OMEGA FLATTEN P2 - EXTRACT RARS + CLASSIFY + REORGANIZE
========================================================
Extracts 13 RARs with 7z, classifies all 276K unique files,
routes to final 14-folder litigation structure.

FINAL STRUCTURE:
  00_SYSTEM/           - engines, DB, scripts (PROTECTED)
  01_COA_366810/       - Court of Appeals filing stack
  02_TRIAL_14TH/       - Trial Court (14th Circuit) filing stack
  03_FEDERAL_1983/     - Federal §1983 filing stack
  04_JTC_MCNEILL/      - Judicial Tenure Commission complaint
  05_BAR_BARNES/       - State Bar complaint stack
  06_EMERGENCY/        - Emergency/support motions
  07_PDF/              - All PDFs by subcategory
  08_TEXT/             - TXT, MD, DOCX, RTF
  09_DATA/             - CSV, JSON, HTML, XML, DB, etc.
  10_IMAGES/           - JPG, PNG, GIF, SVG, etc.
  11_CODE/             - PY, JS, TS, YAML, etc.
  12_ARCHIVES/         - Original archive files
  13_TOOLS/            - Apps, executables, compiled, npm
  THIS_IS_THE_ONE/     - Critical final versions (PROTECTED)
"""
import os, sys, sqlite3, subprocess, shutil, re, time
from datetime import datetime
from collections import defaultdict
from pathlib import Path

LOS = r'C:\Users\andre\LitigationOS'
DB = os.path.join(LOS, 'litigation_context.db')
SZ = r'C:\Program Files\7-Zip\7z.exe'

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
    path = os.path.join(LOS, '00_SYSTEM', 'OMEGA_FLATTEN_P2_LOG.txt')
    with open(path, 'w', encoding='utf-8') as f:
        f.write('\n'.join(log_lines))

log("=" * 70)
log("  OMEGA FLATTEN P2 - EXTRACT + CLASSIFY + REORGANIZE")
log("=" * 70)

# ============================================================
# STEP 1: EXTRACT ALL RARs WITH 7z
# ============================================================
log("\n[STEP 1] Extracting RAR files with 7-Zip...")

cur.execute("SELECT id, file_path, file_size FROM file_inventory WHERE extension='.rar' ORDER BY file_size ASC")
rars = cur.fetchall()
rar_new = 0

for fid, fpath, fsize in rars:
    if not os.path.exists(fpath):
        log(f"  [SKIP] Not found: {os.path.basename(fpath)}")
        continue
    extract_dir = fpath + '_extracted'
    if os.path.exists(extract_dir) and os.listdir(extract_dir):
        log(f"  [SKIP] Already extracted: {os.path.basename(fpath)}")
        continue
    os.makedirs(extract_dir, exist_ok=True)
    log(f"  Extracting: {os.path.basename(fpath)} ({fsize/1e6:.1f} MB)...")
    result = subprocess.run(
        [SZ, 'x', '-y', f'-o{extract_dir}', fpath],
        capture_output=True, text=True, timeout=600
    )
    if result.returncode == 0:
        count = sum(1 for _, _, fs in os.walk(extract_dir) for _ in fs)
        log(f"    [OK] → {count:,} files extracted")
        rar_new += count
        stats['rar_ok'] += 1
    else:
        log(f"    [FAIL] {result.stderr[:200]}")
        stats['rar_fail'] += 1

log(f"  RAR extraction: {stats['rar_ok']} OK, {stats['rar_fail']} failed, {rar_new:,} new files")

# Re-inventory RAR extractions
if rar_new > 0:
    log("  Re-inventorying RAR extractions...")
    cur.execute("SELECT file_path FROM file_inventory")
    known = set(r[0] for r in cur.fetchall())
    archive_exts = {'.zip', '.rar', '.7z', '.tar', '.gz', '.tgz', '.bz2'}
    batch = []
    found = 0
    for root, dirs, files in os.walk(LOS):
        dirs[:] = [d for d in dirs if not d.startswith('.')]
        for fname in files:
            fpath = os.path.join(root, fname)
            if fpath in known:
                continue
            try:
                fsize = os.path.getsize(fpath)
            except:
                fsize = 0
            ext = os.path.splitext(fname)[1].lower()
            rel = os.path.relpath(root, LOS)
            top = rel.split(os.sep)[0] if rel != '.' else '_ROOT'
            is_arch = 1 if ext in archive_exts else 0
            is_prot = 1 if top in {'00_SYSTEM'} else 0
            batch.append((fpath, fname, ext, fsize, os.path.basename(root), top, is_arch, is_prot))
            found += 1
            if len(batch) >= 5000:
                cur.executemany(
                    "INSERT INTO file_inventory (file_path, file_name, extension, file_size, parent_folder, top_folder, is_archive, is_protected) VALUES (?,?,?,?,?,?,?,?)",
                    batch)
                conn.commit()
                batch = []
    if batch:
        cur.executemany(
            "INSERT INTO file_inventory (file_path, file_name, extension, file_size, parent_folder, top_folder, is_archive, is_protected) VALUES (?,?,?,?,?,?,?,?)",
            batch)
        conn.commit()
    log(f"  New files inventoried: {found:,}")

    # Re-run dedup on new files
    log("  Running dedup on new files...")
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
                WHERE is_protected = 0 AND file_size > 0 AND is_duplicate = 0
            ) WHERE rn > 1
        )
    """)
    conn.commit()
    new_dups = cur.execute("SELECT changes()").fetchone()[0]
    log(f"  New duplicates found: {new_dups:,}")

# ============================================================
# STEP 2: CLASSIFY ALL UNIQUE FILES
# ============================================================
log("\n[STEP 2] Classifying files into target folders...")

# Court action patterns (for filing-ready documents)
COURT_PATTERNS = {
    '01_COA_366810': [
        r'PKG05', r'COA[_\s]?BRIEF', r'366810', r'Court.of.Appeals',
        r'MCR\s*7\.212', r'appellate', r'COA_BRIEF_FINAL',
    ],
    '02_TRIAL_14TH': [
        r'PKG01', r'PKG03', r'PKG06', r'PKG07',
        r'14th.Circuit', r'2024[-_]?001507', r'McNeill', r'trial.court',
        r'disqualif', r'void.ex.parte', r'vacate.PPO', r'parenting.time',
        r'emergency.*motion', r'custody',
    ],
    '03_FEDERAL_1983': [
        r'PKG08', r'42\s*U\.?S\.?C.*1983', r'federal.*civil.rights',
        r'1983.*complaint', r'federal.*court',
    ],
    '04_JTC_MCNEILL': [
        r'PKG09', r'JTC', r'Judicial.Tenure', r'commission.*complaint',
    ],
    '05_BAR_BARNES': [
        r'PKG10', r'State.Bar', r'P55406', r'Barnes.*complaint',
        r'bar.*grievance', r'attorney.*discipline',
    ],
    '06_EMERGENCY': [
        r'PKG02', r'PKG04', r'PKG11', r'PKG12',
        r'contempt', r'spoliation', r'FOC.*objection',
        r'housing.*authority', r'emergency',
    ],
}

# Extension → target folder mapping
EXT_MAP = {
    # PDF
    '.pdf': '07_PDF',
    # Text
    '.txt': '08_TEXT', '.md': '08_TEXT', '.docx': '08_TEXT', '.doc': '08_TEXT',
    '.rtf': '08_TEXT', '.odt': '08_TEXT', '.tex': '08_TEXT', '.log': '08_TEXT',
    # Data
    '.csv': '09_DATA', '.json': '09_DATA', '.jsonl': '09_DATA',
    '.xml': '09_DATA', '.html': '09_DATA', '.htm': '09_DATA',
    '.db': '09_DATA', '.sqlite': '09_DATA', '.sql': '09_DATA',
    '.graphml': '09_DATA', '.mbox': '09_DATA', '.faiss': '09_DATA',
    '.xls': '09_DATA', '.xlsx': '09_DATA', '.tsv': '09_DATA',
    '.yaml': '09_DATA', '.yml': '09_DATA', '.toml': '09_DATA',
    '.ini': '09_DATA', '.cfg': '09_DATA', '.conf': '09_DATA',
    # Images
    '.jpg': '10_IMAGES', '.jpeg': '10_IMAGES', '.png': '10_IMAGES',
    '.gif': '10_IMAGES', '.bmp': '10_IMAGES', '.svg': '10_IMAGES',
    '.tiff': '10_IMAGES', '.tif': '10_IMAGES', '.webp': '10_IMAGES',
    '.ico': '10_IMAGES', '.heic': '10_IMAGES',
    # Code
    '.py': '11_CODE', '.js': '11_CODE', '.ts': '11_CODE',
    '.jsx': '11_CODE', '.tsx': '11_CODE', '.java': '11_CODE',
    '.go': '11_CODE', '.rs': '11_CODE', '.c': '11_CODE', '.cpp': '11_CODE',
    '.h': '11_CODE', '.sh': '11_CODE', '.bat': '11_CODE', '.ps1': '11_CODE',
    '.rb': '11_CODE', '.php': '11_CODE', '.swift': '11_CODE',
    '.svelte': '11_CODE', '.vue': '11_CODE', '.scss': '11_CODE',
    '.css': '11_CODE', '.less': '11_CODE',
    # Archives
    '.zip': '12_ARCHIVES', '.rar': '12_ARCHIVES', '.7z': '12_ARCHIVES',
    '.tar': '12_ARCHIVES', '.gz': '12_ARCHIVES', '.bz2': '12_ARCHIVES',
    '.tgz': '12_ARCHIVES',
    # Compiled/Tools
    '.exe': '13_TOOLS', '.dll': '13_TOOLS', '.msi': '13_TOOLS',
    '.jar': '13_TOOLS', '.class': '13_TOOLS', '.pyc': '13_TOOLS',
    '.pyi': '13_TOOLS', '.map': '13_TOOLS', '.mjs': '13_TOOLS',
    '.cjs': '13_TOOLS', '.cts': '13_TOOLS', '.mts': '13_TOOLS',
    '.wasm': '13_TOOLS', '.bcmap': '13_TOOLS', '.so': '13_TOOLS',
    '.node': '13_TOOLS', '.d.ts': '13_TOOLS',
}

def classify_file(file_path, file_name, extension, file_size, top_folder):
    """Classify a file into its target folder."""
    fname_lower = file_name.lower()
    fpath_lower = file_path.lower()

    # Rule 0: Protected folders
    if top_folder in ('00_SYSTEM', 'THIS_IS_THE_ONE'):
        return top_folder  # Don't move

    # Rule 1: Check if file matches court action patterns
    # Only for documents (pdf, txt, md, docx)
    if extension in ('.pdf', '.txt', '.md', '.docx', '.doc', '.rtf'):
        for target, patterns in COURT_PATTERNS.items():
            for pattern in patterns:
                if re.search(pattern, file_name, re.IGNORECASE) or \
                   re.search(pattern, file_path, re.IGNORECASE):
                    return target

    # Rule 2: Files in FINALIZED folder → route to court action by PKG number
    if 'FINALIZED' in file_path.upper():
        if 'PKG05' in file_name: return '01_COA_366810'
        if any(f'PKG0{n}' in file_name for n in [1,3,6,7]): return '02_TRIAL_14TH'
        if 'PKG08' in file_name: return '03_FEDERAL_1983'
        if 'PKG09' in file_name: return '04_JTC_MCNEILL'
        if 'PKG10' in file_name: return '05_BAR_BARNES'
        if any(f'PKG{n}' in file_name for n in ['02','04','11','12']): return '06_EMERGENCY'

    # Rule 3: Already in a target folder → stay there (if it maps)
    if top_folder.startswith(('07_', '08_', '09_', '10_', '11_', '12_', '13_')):
        # If it's 08_TOOLS (old merged folder), route to 13_TOOLS
        if top_folder == '08_TOOLS':
            return '13_TOOLS'

    # Rule 4: Extension-based routing
    if extension in EXT_MAP:
        return EXT_MAP[extension]

    # Rule 5: No extension → check if it looks like text
    if not extension:
        # Common text files without extension: README, LICENSE, Makefile, etc.
        if any(n in fname_lower for n in ['readme', 'license', 'makefile', 'dockerfile', 'changelog', 'authors']):
            return '08_TEXT'
        return '09_DATA'  # Default for extensionless files

    # Rule 6: Default
    return '13_TOOLS'

# Classify all unique, non-protected files
log("  Classifying files...")
cur.execute("""
    SELECT id, file_path, file_name, extension, file_size, top_folder
    FROM file_inventory
    WHERE is_duplicate = 0 AND is_protected = 0
    ORDER BY file_size DESC
""")

classified = 0
batch_updates = []
target_counts = defaultdict(lambda: [0, 0])  # [count, size]

for fid, fpath, fname, ext, fsize, top in cur.fetchall():
    target = classify_file(fpath, fname, ext, fsize, top)
    batch_updates.append((target, fid))
    target_counts[target][0] += 1
    target_counts[target][1] += fsize or 0
    classified += 1

    if len(batch_updates) >= 5000:
        cur.executemany("UPDATE file_inventory SET target_folder = ?, classification = 'classified' WHERE id = ?", batch_updates)
        conn.commit()
        batch_updates = []
        if classified % 50000 == 0:
            log(f"    Classified: {classified:,}")

if batch_updates:
    cur.executemany("UPDATE file_inventory SET target_folder = ?, classification = 'classified' WHERE id = ?", batch_updates)
    conn.commit()

log(f"  Classified: {classified:,} files")
log(f"\n  TARGET DISTRIBUTION:")
for target in sorted(target_counts.keys()):
    cnt, sz = target_counts[target]
    log(f"    {target:25s} {cnt:>8,} files  {sz/1e6:>10,.1f} MB")

# ============================================================
# STEP 3: COMPUTE SUBFOLDER STRUCTURE
# ============================================================
log("\n[STEP 3] Computing subfolder structure...")

# For each target folder, define subfolder routing
def compute_subfolder(target, file_name, extension, file_path, file_size):
    """Compute the subfolder within the target folder."""
    fname_lower = file_name.lower()

    if target == '07_PDF':
        # Subcategorize PDFs
        if any(w in fname_lower for w in ['court', 'order', 'motion', 'ruling', 'judgment']):
            return 'court_records'
        elif any(w in fname_lower for w in ['exhibit', 'evidence', 'photo', 'record']):
            return 'evidence'
        elif any(w in fname_lower for w in ['statute', 'mcl', 'mcr', 'law', 'rule', 'authority']):
            return 'legal_authority'
        elif any(w in fname_lower for w in ['form', 'scao', 'template']):
            return 'forms'
        else:
            return 'general'

    elif target == '08_TEXT':
        if extension == '.md':
            return 'markdown'
        elif extension in ('.docx', '.doc'):
            return 'word'
        elif extension == '.rtf':
            return 'rtf'
        elif any(w in fname_lower for w in ['analysis', 'report', 'summary']):
            return 'analysis'
        elif any(w in fname_lower for w in ['note', 'memo', 'draft']):
            return 'notes'
        elif any(w in fname_lower for w in ['log', 'output']):
            return 'logs'
        else:
            return 'general'

    elif target == '09_DATA':
        if extension == '.csv':
            return 'csv'
        elif extension in ('.json', '.jsonl'):
            return 'json'
        elif extension in ('.html', '.htm'):
            return 'html'
        elif extension in ('.xml', '.graphml'):
            return 'xml'
        elif extension in ('.db', '.sqlite', '.sql'):
            return 'databases'
        elif extension in ('.yaml', '.yml', '.toml', '.ini', '.cfg', '.conf'):
            return 'config'
        elif extension in ('.xls', '.xlsx', '.tsv'):
            return 'spreadsheets'
        else:
            return 'other'

    elif target == '10_IMAGES':
        if extension in ('.jpg', '.jpeg'):
            return 'jpg'
        elif extension == '.png':
            return 'png'
        elif extension == '.svg':
            return 'svg'
        else:
            return 'other'

    elif target == '11_CODE':
        if extension == '.py':
            return 'python'
        elif extension in ('.js', '.jsx', '.mjs', '.cjs'):
            return 'javascript'
        elif extension in ('.ts', '.tsx', '.mts', '.cts'):
            return 'typescript'
        elif extension == '.java':
            return 'java'
        elif extension in ('.sh', '.bat', '.ps1'):
            return 'scripts'
        elif extension in ('.css', '.scss', '.less'):
            return 'styles'
        elif extension in ('.svelte', '.vue'):
            return 'frontend'
        else:
            return 'other'

    elif target in ('01_COA_366810', '02_TRIAL_14TH', '03_FEDERAL_1983',
                     '04_JTC_MCNEILL', '05_BAR_BARNES', '06_EMERGENCY'):
        # Filing stacks: subfolder by doc type
        if extension == '.pdf':
            return 'filed_documents'
        elif extension in ('.md', '.txt'):
            return 'drafts'
        elif extension in ('.docx', '.doc'):
            return 'word_docs'
        else:
            return 'supporting'

    return ''  # No subfolder

# ============================================================
# STEP 4: EXECUTE MOVES
# ============================================================
log("\n[STEP 4] Creating target folder structure...")

# Create all target folders
target_folders = [
    '01_COA_366810', '02_TRIAL_14TH', '03_FEDERAL_1983',
    '04_JTC_MCNEILL', '05_BAR_BARNES', '06_EMERGENCY',
    '07_PDF', '08_TEXT', '09_DATA', '10_IMAGES',
    '11_CODE', '12_ARCHIVES', '13_TOOLS',
]
for tf in target_folders:
    os.makedirs(os.path.join(LOS, tf), exist_ok=True)

log("\n[STEP 4] Executing file moves...")
log("  NOTE: Same-drive moves are instant (rename operations)")

cur.execute("""
    SELECT id, file_path, file_name, extension, file_size, target_folder, top_folder
    FROM file_inventory
    WHERE is_duplicate = 0
      AND is_protected = 0
      AND target_folder IS NOT NULL
      AND classification = 'classified'
    ORDER BY target_folder, extension, file_name
""")

rows = cur.fetchall()
log(f"  Files to move: {len(rows):,}")

moved = 0
skipped = 0
failed = 0
collision = 0

for fid, fpath, fname, ext, fsize, target, top in rows:
    if not os.path.exists(fpath):
        skipped += 1
        continue

    # Don't move if already in correct target
    rel = os.path.relpath(fpath, LOS)
    current_top = rel.split(os.sep)[0]
    if current_top == target:
        skipped += 1
        cur.execute("UPDATE file_inventory SET processed = 1 WHERE id = ?", (fid,))
        continue

    # Compute subfolder
    subfolder = compute_subfolder(target, fname, ext, fpath, fsize)
    if subfolder:
        dest_dir = os.path.join(LOS, target, subfolder)
    else:
        dest_dir = os.path.join(LOS, target)

    os.makedirs(dest_dir, exist_ok=True)
    dest_path = os.path.join(dest_dir, fname)

    # Handle name collision
    if os.path.exists(dest_path):
        base, ext_part = os.path.splitext(fname)
        counter = 1
        while os.path.exists(dest_path):
            dest_path = os.path.join(dest_dir, f"{base}_{counter}{ext_part}")
            counter += 1
        collision += 1

    try:
        shutil.move(fpath, dest_path)
        cur.execute("UPDATE file_inventory SET file_path = ?, processed = 1 WHERE id = ?",
                     (dest_path, fid))
        moved += 1
    except Exception as e:
        failed += 1
        if failed <= 20:
            log(f"    [FAIL] {fname}: {e}")

    if moved % 10000 == 0 and moved > 0:
        conn.commit()
        log(f"    Moved: {moved:,} | Skipped: {skipped:,} | Collisions: {collision:,}")

conn.commit()
log(f"  MOVE COMPLETE: {moved:,} moved | {skipped:,} skipped | {collision:,} collisions | {failed:,} failed")

# ============================================================
# STEP 5: MOVE DUPLICATES TO _DEDUP FOLDER
# ============================================================
log("\n[STEP 5] Moving duplicate files to _DEDUP staging...")

dedup_dir = os.path.join(LOS, '_DEDUP')
os.makedirs(dedup_dir, exist_ok=True)

cur.execute("""
    SELECT id, file_path, file_name, file_size
    FROM file_inventory
    WHERE is_duplicate = 1 AND is_protected = 0
    ORDER BY file_size DESC
    LIMIT 50000
""")
dup_rows = cur.fetchall()
dup_moved = 0
dup_size = 0

for fid, fpath, fname, fsize in dup_rows:
    if not os.path.exists(fpath):
        continue
    try:
        dest = os.path.join(dedup_dir, fname)
        if os.path.exists(dest):
            # Just delete — it's a dupe of a dupe
            os.remove(fpath)
        else:
            shutil.move(fpath, dest)
        dup_moved += 1
        dup_size += fsize or 0
        cur.execute("UPDATE file_inventory SET processed = 1 WHERE id = ?", (fid,))
    except:
        pass

    if dup_moved % 10000 == 0 and dup_moved > 0:
        conn.commit()
        log(f"    Dedup: {dup_moved:,} files ({dup_size/1e9:.1f} GB)")

conn.commit()
log(f"  Duplicates processed: {dup_moved:,} ({dup_size/1e9:.2f} GB)")

# ============================================================
# STEP 6: CLEAN EMPTY DIRECTORIES
# ============================================================
log("\n[STEP 6] Cleaning empty directories...")

cleaned = 0
for root, dirs, files in os.walk(LOS, topdown=False):
    rel = os.path.relpath(root, LOS)
    top = rel.split(os.sep)[0] if rel != '.' else '_ROOT'
    if top.startswith('.') or top == '00_SYSTEM' or top == 'THIS_IS_THE_ONE':
        continue
    if not files and not dirs:
        try:
            os.rmdir(root)
            cleaned += 1
        except:
            pass

log(f"  Empty dirs removed: {cleaned:,}")

# ============================================================
# STEP 7: FINAL VERIFICATION
# ============================================================
log("\n[STEP 7] Final structure verification...")

log(f"\n  {'FOLDER':30s} {'FILES':>10s} {'SIZE':>12s}")
log(f"  {'-'*30} {'-'*10} {'-'*12}")

total_visible = 0
for item in sorted(os.listdir(LOS)):
    path = os.path.join(LOS, item)
    if not os.path.isdir(path) or item.startswith('.'):
        continue
    try:
        count = sum(1 for _, _, fs in os.walk(path) for _ in fs)
        size = sum(os.path.getsize(os.path.join(r, f)) for r, _, fs in os.walk(path) for f in fs
                   if os.path.exists(os.path.join(r, f)))
    except:
        count = size = 0
    log(f"  {item:30s} {count:>10,} {size/1e6:>10,.1f} MB")
    total_visible += 1

log(f"\n  Total visible folders: {total_visible}")

log(f"\n{'='*70}")
log(f"  PHASE 2 COMPLETE")
log(f"  Files moved: {moved:,} | Duplicates handled: {dup_moved:,}")
log(f"  Empty dirs cleaned: {cleaned:,}")
log(f"  Final folder count: {total_visible}")
log(f"{'='*70}")

save_log()
conn.close()
print(f"\nPhase 2 complete. Log: 00_SYSTEM/OMEGA_FLATTEN_P2_LOG.txt")
