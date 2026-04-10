"""
DRIVE INTELLIGENCE — Apex Consolidation Analysis Engine
========================================================
Single-pass, cross-database, DuckDB-powered analysis of 172K+ files
across 6 drives. Produces a complete surgical move manifest.

Databases fused:
  - consolidation_state.db (172K file inventory with xxhash)
  - litigation_context.db (which files are REFERENCED by the case)

Output: Complete decision matrix with file-level precision.
"""
import sqlite3, os, json, sys, time
from pathlib import Path
from collections import defaultdict, Counter

# ─── CONFIG ────────────────────────────────────────────────────
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

# ─── PHASE 1: INVENTORY STATS ─────────────────────────────────
print("=" * 78)
print("  DRIVE INTELLIGENCE — Full Spectrum Analysis")
print("=" * 78)

sc = conn(STATE_DB, ro=True)
lc = conn(LIT_DB, ro=True)

# Total inventory
total = sc.execute("SELECT COUNT(*) FROM file_inventory").fetchone()[0]
print(f"\n  Total files inventoried: {fmt_num(total)}")

# Per-drive breakdown with sizes
print(f"\n  ┌──────────┬──────────────┬──────────────┬──────────────────────┐")
print(f"  │ Drive    │ Files        │ Total Size   │ Hashed (%)           │")
print(f"  ├──────────┼──────────────┼──────────────┼──────────────────────┤")

drive_stats = sc.execute("""
    SELECT source_drive,
           COUNT(*) as files,
           SUM(file_size) as total_bytes,
           SUM(CASE WHEN xxhash IS NOT NULL AND xxhash != '' 
                     AND xxhash NOT LIKE 'ERROR%' THEN 1 ELSE 0 END) as hashed
    FROM file_inventory
    GROUP BY source_drive
    ORDER BY total_bytes DESC
""").fetchall()

drive_order = []
for r in drive_stats:
    drive = r['source_drive'].rstrip('\\')
    pct = (r['hashed'] / r['files'] * 100) if r['files'] else 0
    print(f"  │ {drive:8s} │ {fmt_num(r['files']):>12s} │ {fmt_size(r['total_bytes']):>12s} │ {fmt_num(r['hashed']):>8s} ({pct:.0f}%)       │")
    drive_order.append(drive)

print(f"  └──────────┴──────────────┴──────────────┴──────────────────────┘")

# ─── PHASE 2: CROSS-DRIVE EXACT DUPLICATES ─────────────────────
print(f"\n{'─'*78}")
print(f"  PHASE 2: CROSS-DRIVE DUPLICATE ANALYSIS")
print(f"{'─'*78}")

# Total unique hashes
unique_hashes = sc.execute("""
    SELECT COUNT(DISTINCT xxhash) FROM file_inventory
    WHERE xxhash IS NOT NULL AND xxhash != '' AND xxhash NOT LIKE 'ERROR%'
""").fetchone()[0]

# Cross-drive dupes (same hash on 2+ drives)
cross_dupes = sc.execute("""
    SELECT xxhash, 
           COUNT(*) as copies,
           COUNT(DISTINCT source_drive) as drives,
           GROUP_CONCAT(DISTINCT source_drive) as drive_list,
           MIN(file_size) as size,
           MIN(file_name) as sample
    FROM file_inventory
    WHERE xxhash IS NOT NULL AND xxhash != '' AND xxhash NOT LIKE 'ERROR%'
    GROUP BY xxhash
    HAVING COUNT(DISTINCT source_drive) > 1
    ORDER BY size * (COUNT(*) - 1) DESC
""").fetchall()

# Same-drive dupes
same_drive_dupes = sc.execute("""
    SELECT source_drive, COUNT(*) as dupe_files, SUM(file_size) as waste
    FROM (
        SELECT source_drive, xxhash, file_size,
               ROW_NUMBER() OVER (PARTITION BY source_drive, xxhash ORDER BY modified_date DESC) as rn
        FROM file_inventory
        WHERE xxhash IS NOT NULL AND xxhash != '' AND xxhash NOT LIKE 'ERROR%'
    )
    WHERE rn > 1
    GROUP BY source_drive
    ORDER BY waste DESC
""").fetchall()

cross_waste = sum(r['size'] * (r['copies'] - 1) for r in cross_dupes)
total_dupe_groups = len(cross_dupes)
total_dupe_copies = sum(r['copies'] - 1 for r in cross_dupes)

print(f"\n  Unique content hashes: {fmt_num(unique_hashes)}")
print(f"  Cross-drive dupe groups: {fmt_num(total_dupe_groups)}")
print(f"  Redundant copies: {fmt_num(total_dupe_copies)}")
print(f"  Cross-drive waste: {fmt_size(cross_waste)}")

print(f"\n  Same-drive duplicates:")
for r in same_drive_dupes:
    d = r['source_drive'].rstrip('\\')
    print(f"    {d}: {fmt_num(r['dupe_files'])} dupe files = {fmt_size(r['waste'])} wasted")

# Top 20 biggest cross-drive wastes
print(f"\n  Top 20 biggest cross-drive duplicates:")
print(f"  {'File':<55s} {'Size':>10s} {'Copies':>7s} {'Drives'}")
for r in cross_dupes[:20]:
    name = r['sample'][:54] if r['sample'] else '?'
    print(f"  {name:<55s} {fmt_size(r['size']):>10s} {r['copies']:>5d}x  {r['drive_list']}")

# ─── PHASE 3: LITIGATION DB CROSS-REFERENCE ────────────────────
print(f"\n{'─'*78}")
print(f"  PHASE 3: LITIGATION DB PATH CROSS-REFERENCE")
print(f"{'─'*78}")
print(f"  (Which files are actually REFERENCED by your case data?)")

# Extract all external file paths from litigation_context.db
ref_tables = {
    'evidence_quotes': 'source_file',
    'documents': 'file_path', 
    'file_inventory': 'file_path',
    'impeachment_matrix': 'source_file',
    'timeline_events': 'source_file',
    'police_reports': 'source_file',
}

# Verify columns exist before querying
active_refs = {}
for tbl, col in ref_tables.items():
    try:
        cols = [r[1] for r in lc.execute(f"PRAGMA table_info({tbl})").fetchall()]
        if col in cols:
            active_refs[tbl] = col
    except:
        pass

external_paths = defaultdict(set)  # drive -> set of paths
ref_counts = {}

for tbl, col in active_refs.items():
    try:
        rows = lc.execute(f"""
            SELECT {col}, COUNT(*) as refs
            FROM {tbl}
            WHERE {col} IS NOT NULL AND {col} != ''
            AND (
                {col} LIKE 'D:%' OR {col} LIKE 'd:%' OR
                {col} LIKE 'F:%' OR {col} LIKE 'f:%' OR
                {col} LIKE 'G:%' OR {col} LIKE 'g:%' OR
                {col} LIKE 'I:%' OR {col} LIKE 'i:%' OR
                {col} LIKE 'J:%' OR {col} LIKE 'j:%'
            )
            GROUP BY {col}
        """).fetchall()
        
        ref_counts[tbl] = len(rows)
        for r in rows:
            path = r[0]
            drive = path[:2].upper()
            external_paths[drive].add(path)
    except Exception as e:
        ref_counts[tbl] = f"ERROR: {e}"

print(f"\n  External file references in litigation DB:")
print(f"  ┌─────────────────────────────┬────────────┐")
print(f"  │ Table                       │ Ext. Paths │")
print(f"  ├─────────────────────────────┼────────────┤")
for tbl, cnt in ref_counts.items():
    print(f"  │ {tbl:<27s} │ {str(cnt):>10s} │")
print(f"  └─────────────────────────────┴────────────┘")

total_ext_refs = sum(len(v) for v in external_paths.values())
print(f"\n  Total unique external paths referenced: {fmt_num(total_ext_refs)}")
for drive in sorted(external_paths.keys()):
    print(f"    {drive}: {fmt_num(len(external_paths[drive]))} referenced paths")

# ─── PHASE 4: CRITICALITY CLASSIFICATION ───────────────────────
print(f"\n{'─'*78}")
print(f"  PHASE 4: FILE CRITICALITY CLASSIFICATION")
print(f"{'─'*78}")

# For each external drive, classify files into:
#   CRITICAL: Referenced by litigation DB (must preserve path or migrate)
#   REDUNDANT: Exact hash match exists on C:\
#   UNIQUE: Content not on C:\ and not referenced (evaluate)
#   ARCHIVE: Large media/backups for J:\

all_ext_paths_flat = set()
for s in external_paths.values():
    all_ext_paths_flat.update(s)

# Get C:\ hashes for dedup comparison
c_hashes = set()
c_rows = sc.execute("""
    SELECT DISTINCT xxhash FROM file_inventory
    WHERE source_drive = 'C:\\'
    AND xxhash IS NOT NULL AND xxhash != '' AND xxhash NOT LIKE 'ERROR%'
""").fetchall()
for r in c_rows:
    c_hashes.add(r['xxhash'])

print(f"\n  C:\\ has {fmt_num(len(c_hashes))} unique content hashes")

# Classify every external file
classifications = defaultdict(lambda: defaultdict(list))  # drive -> class -> [(path, size, hash, type)]
summary = defaultdict(lambda: defaultdict(lambda: {'count': 0, 'bytes': 0}))

ext_files = sc.execute("""
    SELECT source_path, source_drive, file_name, file_ext, file_size, 
           xxhash, type_category, lane_guess
    FROM file_inventory
    WHERE source_drive != 'C:\\'
    ORDER BY source_drive, file_size DESC
""").fetchall()

for f in ext_files:
    drive = f['source_drive'].rstrip('\\')
    path = f['source_path']
    size = f['file_size'] or 0
    h = f['xxhash']
    ftype = f['type_category'] or 'OTHER'
    ext = (f['file_ext'] or '').lower()
    
    # Classification logic
    if path in all_ext_paths_flat:
        cls = 'CRITICAL'  # Referenced by litigation DB
    elif h and h not in ('', ) and not h.startswith('ERROR') and h in c_hashes:
        cls = 'REDUNDANT'  # Exact content already on C:\
    elif ext in ('.mp4', '.avi', '.mov', '.mkv', '.mp3', '.wav', '.flac', '.m4a'):
        cls = 'MEDIA'  # Large media → J:\
    elif ext in ('.db', '.db-wal', '.db-shm', '.sqlite', '.sqlite3'):
        cls = 'DATABASE'  # DB files → J:\DB_ARCHIVE
    elif ext in ('.parquet', '.csv', '.tsv', '.jsonl') and size > 10_000_000:
        cls = 'DATA_LARGE'  # Large data files → J:\
    elif ftype in ('PDF_DOCS', 'OFFICE_DOCS', 'TEXT_DOCS') or ext in ('.pdf', '.docx', '.doc', '.txt', '.md'):
        cls = 'DOCUMENT'  # Legal docs → evaluate for C:\ absorption
    elif ftype == 'CODE' or ext in ('.py', '.js', '.ts', '.go', '.rs', '.sql', '.sh', '.ps1', '.bat'):
        cls = 'CODE'  # Code → evaluate usefulness
    elif ftype == 'IMAGES' or ext in ('.jpg', '.jpeg', '.png', '.gif', '.bmp', '.tiff', '.svg'):
        cls = 'IMAGE'  # Images → evaluate (evidence vs junk)
    elif ext in ('.zip', '.rar', '.7z', '.tar', '.gz'):
        cls = 'ARCHIVE'  # Compressed → J:\
    else:
        cls = 'OTHER'
    
    summary[drive][cls]['count'] += 1
    summary[drive][cls]['bytes'] += size

# Print classification matrix
CLASS_ORDER = ['CRITICAL', 'REDUNDANT', 'DOCUMENT', 'CODE', 'DATABASE', 
               'MEDIA', 'IMAGE', 'DATA_LARGE', 'ARCHIVE', 'OTHER']
CLASS_ACTION = {
    'CRITICAL':   '⚠️  MIGRATE paths in lit DB, then archive on J:\\',
    'REDUNDANT':  '🗑️  Safe to remove (exact copy on C:\\)',
    'DOCUMENT':   '📄 Absorb unique into C:\\repo OR J:\\DOCUMENTS',
    'CODE':       '💻 Evaluate usefulness → C:\\07_CODE or J:\\CODE_ARCHIVE',
    'DATABASE':   '🗄️  J:\\DB_ARCHIVE (no WAL on exFAT)',
    'MEDIA':      '🎬 J:\\MEDIA_ARCHIVE',
    'IMAGE':      '🖼️  Evidence images → C:\\01_EVIDENCE, else J:\\',
    'DATA_LARGE': '📊 J:\\DATA_ARCHIVE',
    'ARCHIVE':    '📦 J:\\COMPRESSED_ARCHIVE',
    'OTHER':      '❓ Inspect manually → J:\\UNSORTED',
}

for drive in sorted(summary.keys()):
    data = summary[drive]
    drive_total = sum(v['count'] for v in data.values())
    drive_bytes = sum(v['bytes'] for v in data.values())
    
    print(f"\n  ┌─ {drive} ─ {fmt_num(drive_total)} files ─ {fmt_size(drive_bytes)} ──────────────────────────┐")
    print(f"  │ {'Class':<12s} │ {'Files':>8s} │ {'Size':>10s} │ {'Action':<40s} │")
    print(f"  ├──────────────┼──────────┼────────────┼──────────────────────────────────────────┤")
    
    for cls in CLASS_ORDER:
        if cls in data:
            d = data[cls]
            action = CLASS_ACTION.get(cls, '?')
            print(f"  │ {cls:<12s} │ {fmt_num(d['count']):>8s} │ {fmt_size(d['bytes']):>10s} │ {action:<40s} │")
    
    print(f"  └──────────────┴──────────┴────────────┴──────────────────────────────────────────┘")

# ─── PHASE 5: SURGICAL MOVE MANIFEST ──────────────────────────
print(f"\n{'─'*78}")
print(f"  PHASE 5: CONSOLIDATION SUMMARY")
print(f"{'─'*78}")

total_redundant = sum(summary[d].get('REDUNDANT', {}).get('count', 0) for d in summary)
total_redundant_bytes = sum(summary[d].get('REDUNDANT', {}).get('bytes', 0) for d in summary)
total_critical = sum(summary[d].get('CRITICAL', {}).get('count', 0) for d in summary)
total_critical_bytes = sum(summary[d].get('CRITICAL', {}).get('bytes', 0) for d in summary)
total_unique = sum(
    sum(v['count'] for k, v in summary[d].items() if k not in ('REDUNDANT', 'CRITICAL'))
    for d in summary
)
total_unique_bytes = sum(
    sum(v['bytes'] for k, v in summary[d].items() if k not in ('REDUNDANT', 'CRITICAL'))
    for d in summary
)

print(f"""
  REDUNDANT (safe to delete):    {fmt_num(total_redundant):>10s} files  {fmt_size(total_redundant_bytes):>10s}
  CRITICAL (must migrate refs):  {fmt_num(total_critical):>10s} files  {fmt_size(total_critical_bytes):>10s}
  UNIQUE (archive or absorb):    {fmt_num(total_unique):>10s} files  {fmt_size(total_unique_bytes):>10s}

  SPACE RECOVERABLE: ~{fmt_size(total_redundant_bytes)} from redundant files alone
  
  ACTION PLAN:
  ┌──────────────────────────────────────────────────────────────────────┐
  │ 1. DELETE redundant files (exact C:\\ copies) — {fmt_size(total_redundant_bytes):>10s} freed    │
  │ 2. MIGRATE critical file DB refs → J:\\ paths                        │
  │ 3. ARCHIVE unique media/data/DBs → J:\\ subfolders                   │
  │ 4. ABSORB unique legal docs → C:\\repo structure                     │
  │ 5. VERIFY all moves, rebuild FTS5, validate wiring                  │
  └──────────────────────────────────────────────────────────────────────┘
""")

# ─── PHASE 6: LANE INTELLIGENCE ───────────────────────────────
print(f"{'─'*78}")
print(f"  PHASE 6: EVIDENCE LANE DISTRIBUTION (MEEK)")
print(f"{'─'*78}")

lane_dist = sc.execute("""
    SELECT lane_guess, source_drive, COUNT(*) as cnt, 
           SUM(file_size) as bytes
    FROM file_inventory
    WHERE source_drive != 'C:\\'
    AND lane_guess IS NOT NULL AND lane_guess != ''
    GROUP BY lane_guess, source_drive
    ORDER BY lane_guess, cnt DESC
""").fetchall()

lane_data = defaultdict(lambda: defaultdict(lambda: {'count': 0, 'bytes': 0}))
for r in lane_dist:
    lane_data[r['lane_guess']][r['source_drive'].rstrip('\\')]['count'] = r['cnt']
    lane_data[r['lane_guess']][r['source_drive'].rstrip('\\')]['bytes'] = r['bytes']

LANE_NAMES = {
    'LANE_A': 'Custody (2024-001507-DC)',
    'LANE_B': 'Housing (Shady Oaks)',
    'LANE_C': 'Federal (§1983)',
    'LANE_D': 'PPO (2023-5907-PP)',
    'LANE_E': 'Misconduct (JTC)',
    'LANE_F': 'Appellate (COA 366810)',
}

for lane in sorted(lane_data.keys()):
    name = LANE_NAMES.get(lane, lane)
    drives = lane_data[lane]
    total_f = sum(v['count'] for v in drives.values())
    total_b = sum(v['bytes'] for v in drives.values())
    
    drive_parts = ", ".join(f"{d}:{v['count']}" for d, v in sorted(drives.items()))
    print(f"  {lane} ({name}): {fmt_num(total_f)} files, {fmt_size(total_b)}")
    print(f"    Drives: {drive_parts}")

# ─── PHASE 7: TOP-LEVEL DIRECTORY ANALYSIS ────────────────────
print(f"\n{'─'*78}")
print(f"  PHASE 7: TOP DIRECTORIES BY SIZE (external drives)")
print(f"{'─'*78}")

for drive_raw in ['D:\\', 'F:\\', 'G:\\', 'I:\\']:
    drive = drive_raw.rstrip('\\')
    top_dirs = sc.execute("""
        SELECT 
            CASE 
                WHEN INSTR(SUBSTR(source_path, LENGTH(?) + 1), '\\') > 0
                THEN SUBSTR(source_path, 1, LENGTH(?) + INSTR(SUBSTR(source_path, LENGTH(?) + 1), '\\') - 1)
                ELSE ?
            END as top_dir,
            COUNT(*) as files,
            SUM(file_size) as bytes
        FROM file_inventory
        WHERE source_drive = ?
        GROUP BY top_dir
        ORDER BY bytes DESC
        LIMIT 8
    """, (drive_raw, drive_raw, drive_raw, drive_raw, drive_raw)).fetchall()
    
    if top_dirs:
        print(f"\n  {drive}:")
        for r in top_dirs:
            d = r['top_dir'].replace(drive_raw, '').replace(drive + '\\', '') or '(root files)'
            print(f"    {d[:50]:<50s} {fmt_num(r['files']):>8s} files  {fmt_size(r['bytes']):>10s}")

# ─── PHASE 8: J:\ SCAN ─────────────────────────────────────────
print(f"\n{'─'*78}")
print(f"  PHASE 8: J:\\ TARGET DRIVE STATE")
print(f"{'─'*78}")

j_root = Path("J:\\")
if j_root.exists():
    import shutil
    total, used, free = shutil.disk_usage("J:\\")
    print(f"\n  Capacity: {fmt_size(total)} total, {fmt_size(used)} used, {fmt_size(free)} free")
    
    print(f"\n  Top-level contents:")
    try:
        items = sorted(j_root.iterdir())
        for item in items:
            if item.is_dir():
                try:
                    fcount = sum(1 for f in item.rglob("*") if f.is_file())
                    fsize = sum(f.stat().st_size for f in item.rglob("*") if f.is_file())
                    print(f"    📁 {item.name:<45s} {fmt_num(fcount):>7s} files  {fmt_size(fsize):>10s}")
                except PermissionError:
                    print(f"    📁 {item.name:<45s} (permission denied)")
            else:
                try:
                    sz = item.stat().st_size
                    print(f"    📄 {item.name:<45s}              {fmt_size(sz):>10s}")
                except:
                    pass
    except Exception as e:
        print(f"  Error: {e}")
else:
    print("  J:\\ not accessible")

# ─── SAVE RESULTS ──────────────────────────────────────────────
results = {
    'generated': time.strftime('%Y-%m-%dT%H:%M:%S'),
    'total_files': total,
    'drives': {d.rstrip('\\'): dict(summary[d.rstrip('\\')]) for d in [r['source_drive'] for r in drive_stats]},
    'redundant': {'count': total_redundant, 'bytes': total_redundant_bytes},
    'critical': {'count': total_critical, 'bytes': total_critical_bytes},
    'unique': {'count': total_unique, 'bytes': total_unique_bytes},
    'cross_drive_dupes': total_dupe_groups,
    'external_db_refs': total_ext_refs,
}

# Convert defaultdict values for JSON serialization
for dk in results['drives']:
    for ck in results['drives'][dk]:
        results['drives'][dk][ck] = dict(results['drives'][dk][ck])
    results['drives'][dk] = dict(results['drives'][dk])

out_file = OUT_DIR / "analysis.json"
with open(out_file, 'w') as f:
    json.dump(results, f, indent=2)

elapsed = time.time() - t0
print(f"\n{'='*78}")
print(f"  Analysis complete in {elapsed:.1f}s")
print(f"  Results saved to: {out_file}")
print(f"{'='*78}")

sc.close()
lc.close()
