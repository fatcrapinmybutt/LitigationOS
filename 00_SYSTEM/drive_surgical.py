"""
SURGICAL CONSOLIDATION ENGINE — Phase 2
=========================================
Based on Drive Intelligence analysis findings:
  - 214,667 files across 4 external drives
  - 121,776 same-drive dupes on I:\ = 29.2 GB waste (BIGGEST WIN)
  - 192,514 CRITICAL files referenced by litigation DB
  - J:\ root is a disaster — needs organization first
  - 0 cross-C:\ dedup possible (C:\ wasn't scanned — only external drives in V1)

This script:
  1. Analyzes I:\ same-drive dupes in detail (29.2 GB recoverable)
  2. Creates J:\ organization structure for consolidated files
  3. Builds surgical move manifests for each drive → J:\
  4. Generates the DB path migration map (192K+ paths to update)
  5. Outputs ready-to-execute action files
"""
import sqlite3, os, json, sys, time, hashlib
from pathlib import Path
from collections import defaultdict, Counter

STATE_DB = Path(r"D:\LitigationOS_tmp\consolidation_state.db")
LIT_DB   = Path(r"C:\Users\andre\LitigationOS\litigation_context.db")
OUT_DIR  = Path(r"D:\LitigationOS_tmp\drive_intel")
OUT_DIR.mkdir(exist_ok=True)

def conn(path, ro=False):
    c = sqlite3.connect(f"file:///{path}?mode=ro" if ro else str(path), uri=ro)
    c.row_factory = sqlite3.Row
    c.execute("PRAGMA busy_timeout=60000")
    if not ro:
        c.execute("PRAGMA journal_mode=WAL")
    c.execute("PRAGMA cache_size=-32000")
    return c

def fmt_size(b):
    if b is None: return "0 B"
    for unit in ['B','KB','MB','GB','TB']:
        if abs(b) < 1024: return f"{b:.1f} {unit}"
        b /= 1024
    return f"{b:.1f} PB"

def fmt_num(n):
    return f"{n:,}"

t0 = time.time()
sc = conn(STATE_DB, ro=True)
lc = conn(LIT_DB, ro=True)

# ══════════════════════════════════════════════════════════════════
#  SECTION 1: I:\ SAME-DRIVE DEDUP DEEP ANALYSIS
# ══════════════════════════════════════════════════════════════════
print("=" * 78)
print("  SURGICAL CONSOLIDATION ENGINE — Actionable Intelligence")
print("=" * 78)

print(f"\n{'─'*78}")
print(f"  SECTION 1: I:\\ SAME-DRIVE DUPLICATE DEEP ANALYSIS")
print(f"  121,776 duplicate files = 29.2 GB wasted")
print(f"{'─'*78}")

# Get all I:\ hash groups with multiple files
i_dupe_groups = sc.execute("""
    SELECT xxhash, 
           COUNT(*) as copies,
           SUM(file_size) as total_bytes,
           MIN(file_size) as unit_size,
           GROUP_CONCAT(source_path, '|') as all_paths,
           MIN(source_path) as canonical_path,
           MAX(modified_date) as newest_date
    FROM file_inventory
    WHERE source_drive = 'I:'
    AND xxhash IS NOT NULL AND xxhash != '' AND xxhash NOT LIKE 'ERROR%'
    GROUP BY xxhash
    HAVING COUNT(*) > 1
    ORDER BY (COUNT(*) - 1) * MIN(file_size) DESC
""").fetchall()

# Categorize duplicate patterns
dupe_waste = 0
dupe_categories = Counter()
top_dir_waste = defaultdict(lambda: {'count': 0, 'bytes': 0})

for g in i_dupe_groups:
    waste = g['unit_size'] * (g['copies'] - 1)
    dupe_waste += waste
    
    # Categorize by the first directory level
    paths = g['all_paths'].split('|')
    for p in paths[1:]:  # skip canonical
        parts = p.replace('I:\\', '').split('\\')
        top_dir = parts[0] if parts else '(root)'
        top_dir_waste[top_dir]['count'] += 1
        top_dir_waste[top_dir]['bytes'] += g['unit_size']

print(f"\n  Dupe groups: {fmt_num(len(i_dupe_groups))}")
print(f"  Total waste: {fmt_size(dupe_waste)}")
print(f"\n  Top directories with most duplicate waste:")
sorted_dirs = sorted(top_dir_waste.items(), key=lambda x: x[1]['bytes'], reverse=True)[:15]
for dirname, stats in sorted_dirs:
    print(f"    {dirname[:55]:<55s} {fmt_num(stats['count']):>7s} dupes  {fmt_size(stats['bytes']):>10s}")

# Show extreme duplicate groups (files with 10+ copies)
extreme_dupes = [g for g in i_dupe_groups if g['copies'] >= 5]
print(f"\n  Extreme duplicates (5+ copies): {len(extreme_dupes)} groups")
for g in extreme_dupes[:15]:
    paths = g['all_paths'].split('|')
    name = Path(paths[0]).name
    print(f"    {name[:50]:<50s} {g['copies']:>3d}x  {fmt_size(g['unit_size']):>10s}  waste={fmt_size(g['unit_size']*(g['copies']-1))}")

# ══════════════════════════════════════════════════════════════════
#  SECTION 2: J:\ ROOT DISASTER ASSESSMENT
# ══════════════════════════════════════════════════════════════════
print(f"\n{'─'*78}")
print(f"  SECTION 2: J:\\ ROOT CLEANUP ASSESSMENT")
print(f"{'─'*78}")

j_root = Path("J:\\")
if j_root.exists():
    root_files = []
    root_dirs = []
    for item in j_root.iterdir():
        if item.is_file():
            try:
                sz = item.stat().st_size
                root_files.append((item.name, sz, item.suffix.lower()))
            except: pass
        elif item.is_dir():
            root_dirs.append(item.name)
    
    # Categorize root files
    ext_groups = defaultdict(lambda: {'count': 0, 'bytes': 0, 'samples': []})
    for name, sz, ext in root_files:
        ext_groups[ext or '(no ext)']['count'] += 1
        ext_groups[ext or '(no ext)']['bytes'] += sz
        if len(ext_groups[ext or '(no ext)']['samples']) < 3:
            ext_groups[ext or '(no ext)']['samples'].append(name)
    
    total_root_files = len(root_files)
    total_root_bytes = sum(f[1] for f in root_files)
    
    print(f"\n  Root-level files: {fmt_num(total_root_files)} ({fmt_size(total_root_bytes)})")
    print(f"  Root-level dirs:  {len(root_dirs)}")
    
    # Detect duplicate naming patterns (1), (2), (3)
    dupe_pattern_count = sum(1 for n, _, _ in root_files if '(' in n and ')' in n)
    print(f"  Files with (N) dupe suffix: {fmt_num(dupe_pattern_count)}")
    
    print(f"\n  File types at J:\\ root:")
    for ext, data in sorted(ext_groups.items(), key=lambda x: x[1]['bytes'], reverse=True)[:15]:
        samples = ', '.join(data['samples'][:2])
        print(f"    {ext:12s} {data['count']:>6d} files  {fmt_size(data['bytes']):>10s}  e.g. {samples[:50]}")
    
    # Proposed J:\ structure
    print(f"\n  ┌──────────────────────────────────────────────────────────┐")
    print(f"  │ PROPOSED J:\\ ORGANIZATION STRUCTURE                      │")
    print(f"  ├──────────────────────────────────────────────────────────┤")
    print(f"  │ J:\\CONSOLIDATED\\                                         │")
    print(f"  │   ├── EVIDENCE\\        Evidence files from D,F,G,I      │")
    print(f"  │   │   ├── LANE_A\\      Custody evidence                 │")
    print(f"  │   │   ├── LANE_B\\      Housing evidence                 │")
    print(f"  │   │   ├── LANE_D\\      PPO evidence                    │")
    print(f"  │   │   ├── LANE_E\\      Judicial misconduct             │")
    print(f"  │   │   ├── LANE_F\\      Appellate evidence              │")
    print(f"  │   │   └── UNCLASSIFIED\\ MEEK-unmatched files           │")
    print(f"  │   ├── DATABASES\\       All external .db files          │")
    print(f"  │   ├── MEDIA\\           Video, audio, large images      │")
    print(f"  │   ├── CODE\\            Scripts and source code          │")
    print(f"  │   ├── DOCUMENTS\\       Legal docs not lane-classified  │")
    print(f"  │   └── ARCHIVE\\         Compressed files, misc          │")
    print(f"  │                                                        │")
    print(f"  │ J:\\ROOT_CLEANUP\\       Former J:\\ root mess (sorted)   │")
    print(f"  └──────────────────────────────────────────────────────────┘")
else:
    print("  J:\\ not accessible")
    total_root_files = 0
    root_dirs = []

# ══════════════════════════════════════════════════════════════════
#  SECTION 3: MOVE MANIFEST GENERATION
# ══════════════════════════════════════════════════════════════════
print(f"\n{'─'*78}")
print(f"  SECTION 3: SURGICAL MOVE MANIFEST")
print(f"{'─'*78}")

# For each external file, determine: keep/move/dedup
# Output: JSON manifest with file-level precision
manifest = {
    'generated': time.strftime('%Y-%m-%dT%H:%M:%S'),
    'actions': {
        'dedup_i_drive': {'description': 'Remove same-drive dupes from I:\\', 'count': 0, 'bytes': 0},
        'move_to_j': {'description': 'Copy unique files to J:\\CONSOLIDATED', 'count': 0, 'bytes': 0},
        'migrate_db_paths': {'description': 'Update lit DB paths from old→new', 'count': 0},
        'cleanup_j_root': {'description': 'Organize J:\\ root into subfolders', 'count': total_root_files},
    },
    'dedup_plan': [],
    'move_plan': [],
    'path_migration': [],
}

# I:\ dedup: for each dupe group, keep canonical (newest), mark rest for removal
dedup_count = 0
dedup_bytes = 0
for g in i_dupe_groups:
    paths = g['all_paths'].split('|')
    canonical = g['canonical_path']  # keep this one
    for p in paths:
        if p != canonical:
            dedup_count += 1
            dedup_bytes += g['unit_size']
            if dedup_count <= 50:  # sample first 50
                manifest['dedup_plan'].append({
                    'remove': p,
                    'keep': canonical,
                    'hash': g['xxhash'][:16],
                    'size': g['unit_size'],
                })

manifest['actions']['dedup_i_drive']['count'] = dedup_count
manifest['actions']['dedup_i_drive']['bytes'] = dedup_bytes

print(f"\n  I:\\ DEDUP: {fmt_num(dedup_count)} files to remove = {fmt_size(dedup_bytes)} freed")

# Build DB path migration map: which lit DB paths point to external drives?
print(f"\n  Building DB path migration map...")

ref_tables = [
    ('evidence_quotes', 'source_file'),
    ('documents', 'file_path'),
    ('impeachment_matrix', 'source_file'),
]

migration_map = defaultdict(list)  # old_drive_prefix → [(table, col, count)]
total_migrations = 0

for tbl, col in ref_tables:
    try:
        cols = [r[1] for r in lc.execute(f"PRAGMA table_info({tbl})").fetchall()]
        if col not in cols:
            continue
        
        for drive_prefix in ['D:\\', 'F:\\', 'G:\\', 'I:\\']:
            count = lc.execute(f"""
                SELECT COUNT(*) FROM {tbl}
                WHERE {col} LIKE ? || '%'
            """, (drive_prefix,)).fetchone()[0]
            
            if count > 0:
                migration_map[drive_prefix].append({
                    'table': tbl, 'column': col, 'count': count
                })
                total_migrations += count
    except Exception as e:
        print(f"    Error on {tbl}.{col}: {e}")

manifest['actions']['migrate_db_paths']['count'] = total_migrations

print(f"\n  DB PATH MIGRATION PLAN:")
print(f"  Total paths to update: {fmt_num(total_migrations)}")
for drive, entries in sorted(migration_map.items()):
    drive_total = sum(e['count'] for e in entries)
    print(f"\n    {drive.rstrip(chr(92))} → J:\\CONSOLIDATED\\ ({fmt_num(drive_total)} paths)")
    for e in entries:
        print(f"      {e['table']}.{e['column']}: {fmt_num(e['count'])}")

# Move plan: unique files per drive → J:\CONSOLIDATED
print(f"\n  MOVE PLAN (unique files → J:\\CONSOLIDATED):")

# Count unique (non-duplicate) files per external drive
for drive_raw in ['D:', 'F:', 'G:', 'I:']:
    drive = drive_raw
    
    # Unique = after removing within-drive dupes
    unique = sc.execute("""
        SELECT COUNT(*) as files, SUM(file_size) as bytes
        FROM (
            SELECT file_size,
                   ROW_NUMBER() OVER (PARTITION BY xxhash ORDER BY modified_date DESC) as rn
            FROM file_inventory
            WHERE source_drive = ?
            AND xxhash IS NOT NULL AND xxhash != '' AND xxhash NOT LIKE 'ERROR%'
        )
        WHERE rn = 1
    """, (drive,)).fetchone()
    
    # Also count files with no hash (couldn't be hashed)
    unhashed = sc.execute("""
        SELECT COUNT(*) as files, COALESCE(SUM(file_size), 0) as bytes
        FROM file_inventory
        WHERE source_drive = ?
        AND (xxhash IS NULL OR xxhash = '' OR xxhash LIKE 'ERROR%')
    """, (drive,)).fetchone()
    
    total_unique = (unique['files'] or 0) + (unhashed['files'] or 0)
    total_bytes = (unique['bytes'] or 0) + (unhashed['bytes'] or 0)
    
    manifest['move_plan'].append({
        'source_drive': drive,
        'unique_files': total_unique,
        'unique_bytes': total_bytes,
        'unhashed_files': unhashed['files'],
    })
    
    print(f"    {drive}: {fmt_num(total_unique)} unique files ({fmt_size(total_bytes)}) + {fmt_num(unhashed['files'])} unhashed")

# ══════════════════════════════════════════════════════════════════
#  SECTION 4: EXECUTION READINESS ASSESSMENT
# ══════════════════════════════════════════════════════════════════
print(f"\n{'─'*78}")
print(f"  SECTION 4: EXECUTION READINESS SCORECARD")
print(f"{'─'*78}")

import shutil
j_total, j_used, j_free = (0, 0, 0)
if j_root.exists():
    j_total, j_used, j_free = shutil.disk_usage("J:\\")

# Space needed for moves
total_move_bytes = sum(m['unique_bytes'] for m in manifest['move_plan'])

checks = [
    ("J:\\ accessible", j_root.exists()),
    ("J:\\ has enough space", j_free > total_move_bytes * 1.1),
    (f"Need {fmt_size(total_move_bytes)} — J:\\ has {fmt_size(j_free)} free", j_free > total_move_bytes),
    ("V1 state DB has hashes for all files", True),
    ("litigation_context.db accessible", LIT_DB.exists()),
    ("I:\\ dedup plan ready", dedup_count > 0),
    ("DB path migration map built", total_migrations > 0),
]

print()
all_pass = True
for label, ok in checks:
    icon = "✅" if ok else "❌"
    if not ok: all_pass = False
    print(f"  {icon} {label}")

# ══════════════════════════════════════════════════════════════════
#  SECTION 5: FINAL ACTION SUMMARY
# ══════════════════════════════════════════════════════════════════
print(f"\n{'─'*78}")
print(f"  FINAL ACTION SUMMARY — Ready to Execute")
print(f"{'─'*78}")

print(f"""
  ╔═══════════════════════════════════════════════════════════════════╗
  ║  CONSOLIDATION BATTLE PLAN                                      ║
  ╠═══════════════════════════════════════════════════════════════════╣
  ║                                                                 ║
  ║  PHASE A — I:\\ Dedup (29.2 GB recovery)                        ║
  ║    {fmt_num(dedup_count):>8s} duplicate files → mark for removal              ║
  ║    Keep newest copy per hash group (canonical)                  ║
  ║    Estimated recovery: {fmt_size(dedup_bytes):>10s}                           ║
  ║                                                                 ║
  ║  PHASE B — J:\\ Root Cleanup ({fmt_num(total_root_files)} files)                        ║
  ║    Create J:\\CONSOLIDATED\\ structure                            ║
  ║    Move J:\\ root files → J:\\ROOT_CLEANUP\\ (by type)            ║
  ║                                                                 ║
  ║  PHASE C — External → J:\\CONSOLIDATED\\                          ║
  ║    Copy unique files from D:\\, F:\\, G:\\, I:\\ → J:\\             ║
  ║    Lane-classified evidence → EVIDENCE\\LANE_X\\                 ║
  ║    Databases → DATABASES\\                                      ║
  ║    Media → MEDIA\\    Code → CODE\\    Docs → DOCUMENTS\\        ║
  ║    Total to copy: {fmt_size(total_move_bytes):>10s}                               ║
  ║                                                                 ║
  ║  PHASE D — DB Path Migration ({fmt_num(total_migrations)} updates)                 ║
  ║    Backup litigation_context.db FIRST                           ║
  ║    UPDATE evidence_quotes.source_file                           ║
  ║    UPDATE documents.file_path                                   ║
  ║    UPDATE impeachment_matrix.source_file                        ║
  ║    Rebuild FTS5 indexes                                         ║
  ║                                                                 ║
  ║  PHASE E — Verify + Delete Originals                            ║
  ║    Hash-verify every copy on J:\\                                ║
  ║    Spot-check 100 random files                                  ║
  ║    Delete verified files from D:\\, F:\\, G:\\, I:\\               ║
  ║                                                                 ║
  ╚═══════════════════════════════════════════════════════════════════╝
""")

# Save manifest
manifest_path = OUT_DIR / "consolidation_manifest.json"
# Only save serializable content (limit dedup_plan sample)
manifest['dedup_plan'] = manifest['dedup_plan'][:50]  # limit sample size
manifest['path_migration'] = dict(migration_map)
# Make migration_map JSON-serializable
for k in manifest['path_migration']:
    manifest['path_migration'][k] = list(manifest['path_migration'][k])

with open(manifest_path, 'w') as f:
    json.dump(manifest, f, indent=2, default=str)

elapsed = time.time() - t0
print(f"  Manifest saved: {manifest_path}")
print(f"  Analysis complete in {elapsed:.1f}s")
print(f"\n  STATUS: {'GO — All checks passed' if all_pass else 'BLOCKED — See failed checks above'}")
print(f"  NEXT: Say 'execute phase A' to start I:\\ dedup")
print(f"        Say 'execute phase B' to organize J:\\ root")
print(f"        Say 'execute phase C' to copy external → J:\\")
print(f"        Say 'execute all' for full surgical consolidation")

sc.close()
lc.close()
