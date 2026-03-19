#!/usr/bin/env python3
"""
OMEGA FLATTEN P3 - CLEANUP + CONSOLIDATE TO 15 FOLDERS
======================================================
Absorbs all _extracted folders, old numbered folders, and _DEDUP.
Target: exactly 15 visible folders + hidden system folders.
"""
import os, sys, shutil, sqlite3
from datetime import datetime
from collections import defaultdict

LOS = r'C:\Users\andre\LitigationOS'
DB = os.path.join(LOS, 'litigation_context.db')

stats = defaultdict(int)
log_lines = []

def log(msg):
    ts = datetime.now().strftime('%H:%M:%S')
    line = f"[{ts}] {msg}"
    print(line)
    log_lines.append(line)

# Extension → target mapping (same as P2)
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
    '.tiff': '10_IMAGES', '.webp': '10_IMAGES', '.ico': '10_IMAGES',
    '.py': '11_CODE', '.js': '11_CODE', '.ts': '11_CODE',
    '.jsx': '11_CODE', '.tsx': '11_CODE', '.java': '11_CODE',
    '.sh': '11_CODE', '.bat': '11_CODE', '.ps1': '11_CODE',
    '.svelte': '11_CODE', '.vue': '11_CODE', '.css': '11_CODE',
    '.scss': '11_CODE', '.go': '11_CODE', '.rs': '11_CODE',
    '.zip': '12_ARCHIVES', '.rar': '12_ARCHIVES', '.7z': '12_ARCHIVES',
    '.tar': '12_ARCHIVES', '.gz': '12_ARCHIVES', '.bz2': '12_ARCHIVES',
    '.exe': '13_TOOLS', '.dll': '13_TOOLS', '.msi': '13_TOOLS',
    '.jar': '13_TOOLS', '.class': '13_TOOLS', '.pyc': '13_TOOLS',
    '.pyi': '13_TOOLS', '.map': '13_TOOLS', '.mjs': '13_TOOLS',
    '.cjs': '13_TOOLS', '.cts': '13_TOOLS', '.mts': '13_TOOLS',
    '.wasm': '13_TOOLS', '.bcmap': '13_TOOLS', '.node': '13_TOOLS',
}

PROTECTED = {'00_SYSTEM', 'THIS_IS_THE_ONE',
             '01_COA_366810', '02_TRIAL_14TH', '03_FEDERAL_1983',
             '04_JTC_MCNEILL', '05_BAR_BARNES', '06_EMERGENCY',
             '07_PDF', '08_TEXT', '09_DATA', '10_IMAGES',
             '11_CODE', '12_ARCHIVES', '13_TOOLS'}

log("=" * 70)
log("  OMEGA FLATTEN P3 - FINAL CONSOLIDATION")
log("=" * 70)

# ============================================================
# STEP 1: Move all _extracted folder contents by extension
# ============================================================
log("\n[STEP 1] Absorbing _extracted folders...")

for item in os.listdir(LOS):
    if not item.endswith('_extracted'):
        continue
    src_dir = os.path.join(LOS, item)
    if not os.path.isdir(src_dir):
        continue

    file_count = sum(1 for _, _, fs in os.walk(src_dir) for _ in fs)
    if file_count == 0:
        try:
            shutil.rmtree(src_dir)
            stats['empty_extracted_removed'] += 1
        except:
            pass
        continue

    log(f"  Processing: {item} ({file_count} files)")
    for root, dirs, files in os.walk(src_dir):
        for fname in files:
            fpath = os.path.join(root, fname)
            ext = os.path.splitext(fname)[1].lower()
            target = EXT_MAP.get(ext, '13_TOOLS')

            # Compute subfolder (simplified)
            if target == '07_PDF':
                sub = 'general'
            elif target == '08_TEXT':
                sub = 'general' if ext == '.txt' else 'markdown' if ext == '.md' else 'word'
            elif target == '09_DATA':
                sub = ext.lstrip('.') if ext else 'other'
            elif target == '10_IMAGES':
                sub = ext.lstrip('.') if ext else 'other'
            elif target == '11_CODE':
                sub = 'python' if ext == '.py' else 'javascript' if ext in ('.js','.jsx') else 'other'
            elif target == '12_ARCHIVES':
                sub = ''
            else:
                sub = ''

            dest_dir = os.path.join(LOS, target, sub) if sub else os.path.join(LOS, target)
            os.makedirs(dest_dir, exist_ok=True)
            dest = os.path.join(dest_dir, fname)

            if os.path.exists(dest):
                # Skip — it's a dupe
                try:
                    os.remove(fpath)
                    stats['dedup_deleted'] += 1
                except:
                    pass
                continue

            try:
                shutil.move(fpath, dest)
                stats['extracted_moved'] += 1
            except:
                stats['extracted_fail'] += 1

    # Try to remove the now-empty extracted dir
    try:
        shutil.rmtree(src_dir)
        stats['extracted_dirs_removed'] += 1
    except:
        pass

log(f"  Extracted files moved: {stats['extracted_moved']:,}")
log(f"  Dupes deleted: {stats['dedup_deleted']:,}")

# ============================================================
# STEP 2: Absorb old numbered folders
# ============================================================
log("\n[STEP 2] Absorbing old numbered folders...")

old_folders = {
    '01_CASE_FILES': '09_DATA',      # case data → data
    '02_EVIDENCE': '10_IMAGES',      # evidence (mostly images after move)
    '03_AUTHORITIES': '07_PDF',      # legal authority → PDF
    '04_COURT_FILINGS': '07_PDF',    # court filings → PDF
    '05_ANALYSIS': '08_TEXT',        # analysis → text
    '06_ADVERSARY': '08_TEXT',       # adversary → text
    '07_DATABASES': '09_DATA',       # databases → data
    '08_TOOLS': '13_TOOLS',          # old tools → tools
    '09_DOCUMENTS': '08_TEXT',       # documents → text
    '10_ARCHIVES': '12_ARCHIVES',    # archives → archives
    '11_CONFIG': '09_DATA',          # config → data
    '12_PROJECTS': '11_CODE',        # projects → code
    '16_DOCUMENTS': '08_TEXT',       # ghost → text
    '_DEDUP': '_DEDUP_DELETE',       # dedup staging → delete pile
}

for old_name, default_target in old_folders.items():
    src_dir = os.path.join(LOS, old_name)
    if not os.path.isdir(src_dir):
        continue
    if old_name in PROTECTED:
        continue

    file_count = sum(1 for _, _, fs in os.walk(src_dir) for _ in fs)
    if file_count == 0:
        try:
            shutil.rmtree(src_dir)
            log(f"  [EMPTY] Removed: {old_name}")
        except:
            pass
        continue

    log(f"  Absorbing: {old_name} ({file_count:,} files)")

    for root, dirs, files in os.walk(src_dir):
        for fname in files:
            fpath = os.path.join(root, fname)
            ext = os.path.splitext(fname)[1].lower()

            # Route by extension, fallback to default
            target = EXT_MAP.get(ext, default_target)
            if target == '_DEDUP_DELETE':
                target = '_DEDUP'

            # For _DEDUP, just delete (they're duplicates)
            if old_name == '_DEDUP':
                try:
                    os.remove(fpath)
                    stats['dedup_purged'] += 1
                except:
                    pass
                continue

            # Compute simple subfolder
            if target in ('07_PDF', '08_TEXT', '09_DATA', '10_IMAGES', '11_CODE'):
                sub = ext.lstrip('.') if ext else 'other'
                if sub in ('jpg', 'jpeg'): sub = 'jpg'
                if sub in ('json', 'jsonl'): sub = 'json'
            else:
                sub = ''

            dest_dir = os.path.join(LOS, target, sub) if sub else os.path.join(LOS, target)
            os.makedirs(dest_dir, exist_ok=True)
            dest = os.path.join(dest_dir, fname)

            if os.path.exists(dest):
                try:
                    os.remove(fpath)
                    stats['dedup_deleted'] += 1
                except:
                    pass
                continue

            try:
                shutil.move(fpath, dest)
                stats['old_moved'] += 1
            except:
                stats['old_fail'] += 1

    # Remove old directory
    try:
        shutil.rmtree(src_dir)
        log(f"    → Removed: {old_name}")
    except Exception as e:
        log(f"    → Could not remove {old_name}: {e}")

log(f"  Old folder files moved: {stats['old_moved']:,}")
log(f"  Dedup purged: {stats['dedup_purged']:,}")

# ============================================================
# STEP 3: Final empty directory cleanup
# ============================================================
log("\n[STEP 3] Final cleanup...")

# Remove any remaining empty dirs at root
for item in list(os.listdir(LOS)):
    path = os.path.join(LOS, item)
    if not os.path.isdir(path):
        continue
    if item.startswith('.') or item in PROTECTED:
        continue
    file_count = sum(1 for _, _, fs in os.walk(path) for _ in fs)
    if file_count == 0:
        try:
            shutil.rmtree(path)
            log(f"  Removed empty: {item}")
            stats['final_cleanup'] += 1
        except:
            pass

# Deep empty dir cleanup within target folders
for target in PROTECTED:
    tpath = os.path.join(LOS, target)
    if not os.path.isdir(tpath):
        continue
    for root, dirs, files in os.walk(tpath, topdown=False):
        if not files and not dirs:
            try:
                os.rmdir(root)
            except:
                pass

# ============================================================
# STEP 4: Final verification
# ============================================================
log("\n[STEP 4] Final structure:")
log(f"\n  {'FOLDER':30s} {'FILES':>10s} {'SIZE_MB':>12s}")
log(f"  {'-'*54}")

visible = 0
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
    visible += 1
    total_files += count
    total_size += size

log(f"  {'-'*54}")
log(f"  {'TOTAL':30s} {total_files:>10,} {total_size/1e6:>10,.1f}")
log(f"\n  Visible folders: {visible}")

# Save log
with open(os.path.join(LOS, '00_SYSTEM', 'OMEGA_FLATTEN_P3_LOG.txt'), 'w', encoding='utf-8') as f:
    f.write('\n'.join(log_lines))

log(f"\n{'='*70}")
log(f"  PHASE 3 CONSOLIDATION COMPLETE")
log(f"  Extracted absorbed: {stats['extracted_moved']:,}")
log(f"  Old folders absorbed: {stats['old_moved']:,}")
log(f"  Duplicates purged: {stats['dedup_purged'] + stats['dedup_deleted']:,}")
log(f"  Empty dirs removed: {stats['empty_extracted_removed'] + stats['extracted_dirs_removed'] + stats['final_cleanup']:,}")
log(f"{'='*70}")
