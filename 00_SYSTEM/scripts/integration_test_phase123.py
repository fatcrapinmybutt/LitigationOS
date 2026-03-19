import sys, os, sqlite3, json, time
sys.path.insert(0, r'C:\Users\andre\scans\tooling')
from pathlib import Path
from config import MASTER_ROOT, SCANS_ROOT

# Test cycle dir
test_dir = MASTER_ROOT / 'cyclepacks' / 'CYCLE_INTEGRATION_TEST'
test_dir.mkdir(parents=True, exist_ok=True)
print('=' * 60)
print('CYCLE 3 INTEGRATION TEST')
print('=' * 60)

# === PHASE 1: Real inventory (NOT dry-run, but limited) ===
print('\n[TEST] Phase 1: Real inventory (first 2000 files)...')
from phase1_inventory import run_inventory, should_skip_dir, get_top_bucket, DB_SCHEMA
from config import SKIP_DIRS, SKIP_EXTENSIONS, SKIP_PREFIXES, LEGAL_EXTENSIONS, sha256_file, long_path

db_path = test_dir / 'inventory.db'
conn = sqlite3.connect(str(db_path))
conn.execute('PRAGMA journal_mode=WAL')
conn.execute('PRAGMA synchronous=NORMAL')
conn.executescript(DB_SCHEMA)

start = time.time()
total = 0
batch = []
LIMIT = 2000

for dirpath, dirnames, filenames in os.walk(str(SCANS_ROOT)):
    dirnames[:] = [d for d in dirnames if not should_skip_dir(d)]
    dp = Path(dirpath)
    try:
        depth = len(dp.relative_to(SCANS_ROOT).parts)
    except ValueError:
        depth = 0
    for fname in filenames:
        if total >= LIMIT:
            break
        fpath = dp / fname
        ext = fpath.suffix.lower()
        if ext in SKIP_EXTENSIONS:
            continue
        try:
            stat = fpath.stat()
            file_hash = None
            is_legal = 1 if ext in LEGAL_EXTENSIONS else 0
            if stat.st_size < 50_000_000:
                try:
                    file_hash = sha256_file(fpath)
                except (PermissionError, OSError):
                    pass
            batch.append((str(fpath), fname, ext or None, stat.st_size,
                         time.strftime('%Y-%m-%dT%H:%M:%S', time.localtime(stat.st_mtime)),
                         file_hash, depth, str(dp), get_top_bucket(fpath), is_legal))
            total += 1
        except (PermissionError, OSError):
            continue
    if total >= LIMIT:
        break

conn.executemany('INSERT OR IGNORE INTO files (file_path, file_name, extension, size_bytes, modified_time, sha256, depth, parent_dir, top_bucket, is_legal_content) VALUES (?,?,?,?,?,?,?,?,?,?)', batch)
conn.commit()
elapsed1 = time.time() - start
print(f'  Inserted {total} files in {elapsed1:.1f}s')

# Stats
row = conn.execute('SELECT COUNT(*), SUM(size_bytes), COUNT(DISTINCT extension), COUNT(DISTINCT top_bucket) FROM files').fetchone()
print(f'  Total rows: {row[0]}, Total size: {row[1]/1024/1024:.1f} MB, Extensions: {row[2]}, Buckets: {row[3]}')
exts = conn.execute('SELECT extension, COUNT(*) FROM files GROUP BY extension ORDER BY COUNT(*) DESC LIMIT 8').fetchall()
print(f'  Top extensions: {dict(exts)}')
buckets = conn.execute('SELECT top_bucket, COUNT(*) FROM files GROUP BY top_bucket ORDER BY COUNT(*) DESC LIMIT 5').fetchall()
print(f'  Top buckets: {dict(buckets)}')
hashed = conn.execute('SELECT COUNT(*) FROM files WHERE sha256 IS NOT NULL').fetchone()[0]
print(f'  Hashed: {hashed}/{total}')
legal = conn.execute('SELECT COUNT(*) FROM files WHERE is_legal_content=1').fetchone()[0]
print(f'  Legal content: {legal}/{total}')
conn.close()

# === PHASE 2: Dedup ===
print('\n[TEST] Phase 2: Dedup...')
from phase2_dedup import run_dedup
start2 = time.time()
run_dedup(test_dir, dry_run=False)
elapsed2 = time.time() - start2
print(f'  Phase 2 completed in {elapsed2:.1f}s')

# Check dedup results
dedup_report = test_dir / 'dedup_report.json'
if dedup_report.exists():
    dr = json.loads(dedup_report.read_text(encoding='utf-8'))
    total_clusters = dr.get('total_clusters', '?')
    total_duplicates = dr.get('total_duplicates', '?')
    print(f'  Clusters: {total_clusters}, Duplicates: {total_duplicates}')
else:
    print('  (no dedup report - checking checkpoint)')
    cp = test_dir / 'checkpoints' / 'phase2_complete.json'
    if cp.exists():
        print(f'  Checkpoint: {cp.read_text(encoding="utf-8")}')

# === PHASE 3: Classify ===
print('\n[TEST] Phase 3: Classify...')
from phase3_classify import run_classify
start3 = time.time()
run_classify(test_dir, dry_run=False)
elapsed3 = time.time() - start3
print(f'  Phase 3 completed in {elapsed3:.1f}s')

# Check classification results
conn = sqlite3.connect(str(db_path))
cats = conn.execute('SELECT category, COUNT(*) FROM files WHERE category IS NOT NULL GROUP BY category ORDER BY COUNT(*) DESC LIMIT 10').fetchall()
pris = conn.execute('SELECT priority, COUNT(*) FROM files WHERE priority IS NOT NULL GROUP BY priority ORDER BY COUNT(*) DESC').fetchall()
meek = conn.execute('SELECT meek_lanes, COUNT(*) FROM files WHERE meek_lanes IS NOT NULL AND meek_lanes != "" GROUP BY meek_lanes ORDER BY COUNT(*) DESC LIMIT 5').fetchall()
scored = conn.execute('SELECT COUNT(*) FROM files WHERE content_score > 0').fetchone()[0]
print(f'  Categories: {dict(cats)}')
print(f'  Priorities: {dict(pris)}')
print(f'  MEEK lanes: {dict(meek)}')
print(f'  Content scored: {scored}/{total}')
conn.close()

print('\n' + '=' * 60)
total_elapsed = elapsed1 + elapsed2 + elapsed3
print(f'INTEGRATION TEST COMPLETE: {total_elapsed:.1f}s total')
print('=' * 60)

# Cleanup
import shutil
shutil.rmtree(str(test_dir))
print('Test directory cleaned.')
