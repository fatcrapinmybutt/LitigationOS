import sys, os, sqlite3, re, time
from collections import defaultdict, Counter
from pathlib import Path
sys.stdout = open(sys.stdout.fileno(), mode='w', encoding='utf-8', errors='replace')

ROOT = r"C:\Users\andre\LitigationOS"
DB_PATH = os.path.join(ROOT, "00_SYSTEM", "file_catalog.db")

print(f"=== LitigationOS Full File Catalog Scanner ===")
print(f"Root: {ROOT}")
print(f"DB: {DB_PATH}")

# Name normalization: strip versions, dupes, timestamps
def normalize_name(name):
    n = name.lower().strip()
    # Remove (1), (2), _v2, _v3, _dup, _copy suffixes
    n = re.sub(r'\s*\(\d+\)\s*', '', n)
    n = re.sub(r'_v\d+', '', n)
    n = re.sub(r'_dup\d*', '', n)
    n = re.sub(r'_copy\d*', '', n)
    n = re.sub(r'_root$', '', n)
    # Remove timestamps like 20260222, 20260222_1300
    n = re.sub(r'_?\d{8}(_\d{4,6})?', '', n)
    # Remove UUID-like patterns
    n = re.sub(r'[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}', '', n)
    # Collapse multiple underscores/hyphens
    n = re.sub(r'[_-]+', '_', n).strip('_')
    return n

# Create DB
conn = sqlite3.connect(DB_PATH)
conn.execute("PRAGMA journal_mode=WAL")
conn.execute("PRAGMA synchronous=NORMAL")

conn.executescript("""
    DROP TABLE IF EXISTS files;
    CREATE TABLE files (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        file_path TEXT NOT NULL,
        file_name TEXT NOT NULL,
        normalized_name TEXT NOT NULL,
        extension TEXT,
        size_bytes INTEGER,
        modified_time TEXT,
        parent_dir TEXT,
        depth INTEGER,
        top_folder TEXT,
        category TEXT DEFAULT ''
    );
    CREATE INDEX IF NOT EXISTS idx_norm ON files(normalized_name);
    CREATE INDEX IF NOT EXISTS idx_ext ON files(extension);
    CREATE INDEX IF NOT EXISTS idx_size ON files(size_bytes);
    CREATE INDEX IF NOT EXISTS idx_top ON files(top_folder);
    
    DROP TABLE IF EXISTS duplicates;
    CREATE TABLE duplicates (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        normalized_name TEXT,
        extension TEXT,
        size_bytes INTEGER,
        copy_count INTEGER,
        file_paths TEXT
    );
    
    DROP TABLE IF EXISTS scan_stats;
    CREATE TABLE scan_stats (
        key TEXT PRIMARY KEY,
        value TEXT
    );
""")

# Walk and catalog
start = time.time()
batch = []
total = 0
errors = 0
BATCH_SIZE = 5000

def get_top_folder(rel):
    parts = Path(rel).parts
    return parts[0] if parts else ''

def classify(ext, name):
    ext = ext.lower()
    nl = name.lower()
    if ext in ('.py', '.js', '.ts', '.jsx', '.tsx', '.rs', '.go', '.java', '.c', '.cpp', '.h', '.cs', '.rb', '.php', '.sh', '.ps1', '.bat', '.cmd'):
        return 'code'
    if ext in ('.md', '.txt', '.rst', '.doc', '.docx', '.rtf'):
        return 'document'
    if ext in ('.pdf',):
        return 'pdf'
    if ext in ('.json', '.jsonl', '.yaml', '.yml', '.toml', '.xml', '.csv', '.tsv'):
        return 'data'
    if ext in ('.html', '.htm', '.css', '.scss', '.less'):
        return 'web'
    if ext in ('.png', '.jpg', '.jpeg', '.gif', '.svg', '.bmp', '.ico', '.webp', '.tiff'):
        return 'image'
    if ext in ('.zip', '.tar', '.gz', '.7z', '.rar', '.bz2'):
        return 'archive'
    if ext in ('.db', '.sqlite', '.sqlite3', '.mdb'):
        return 'database'
    if ext in ('.exe', '.dll', '.so', '.dylib', '.msi', '.whl'):
        return 'binary'
    if ext in ('.pyc', '.pyo', '.class', '.o', '.obj'):
        return 'compiled'
    if ext in ('.mp3', '.mp4', '.avi', '.mkv', '.wav', '.flac', '.mov'):
        return 'media'
    if ext in ('.lnk',):
        return 'shortcut'
    if ext in ('.log',):
        return 'log'
    if 'legal' in nl or 'court' in nl or 'mcl' in nl or 'mcr' in nl or 'motion' in nl:
        return 'legal'
    return 'other'

for dirpath, dirnames, filenames in os.walk(ROOT):
    # Skip .git internals
    if '.git' in dirpath.split(os.sep):
        continue
    
    rel_dir = os.path.relpath(dirpath, ROOT)
    depth = rel_dir.count(os.sep) + 1 if rel_dir != '.' else 0
    top = get_top_folder(rel_dir) if rel_dir != '.' else '(root)'
    
    for fn in filenames:
        fp = os.path.join(dirpath, fn)
        try:
            st = os.stat(fp)
            ext = os.path.splitext(fn)[1].lower()
            norm = normalize_name(os.path.splitext(fn)[0]) + ext
            cat = classify(ext, fn)
            mtime = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(st.st_mtime))
            
            batch.append((fp, fn, norm, ext, st.st_size, mtime, rel_dir, depth, top, cat))
            total += 1
            
            if len(batch) >= BATCH_SIZE:
                conn.executemany("INSERT INTO files (file_path,file_name,normalized_name,extension,size_bytes,modified_time,parent_dir,depth,top_folder,category) VALUES (?,?,?,?,?,?,?,?,?,?)", batch)
                conn.commit()
                batch = []
                if total % 50000 == 0:
                    elapsed = time.time() - start
                    print(f"  {total:>8} files scanned ({elapsed:.0f}s)")
        except Exception as e:
            errors += 1

# Final batch
if batch:
    conn.executemany("INSERT INTO files (file_path,file_name,normalized_name,extension,size_bytes,modified_time,parent_dir,depth,top_folder,category) VALUES (?,?,?,?,?,?,?,?,?,?)", batch)
    conn.commit()

elapsed = time.time() - start
print(f"\n=== SCAN COMPLETE ===")
print(f"Total files: {total}")
print(f"Errors: {errors}")
print(f"Time: {elapsed:.1f}s")

# Find duplicates by normalized name + size
print("\nFinding duplicates by normalized name + size...")
cursor = conn.execute("""
    SELECT normalized_name, extension, size_bytes, COUNT(*) as cnt, GROUP_CONCAT(file_path, '|||')
    FROM files
    WHERE size_bytes > 100
    GROUP BY normalized_name, size_bytes
    HAVING cnt > 1
    ORDER BY cnt * size_bytes DESC
""")

dup_count = 0
total_waste = 0
for row in cursor:
    norm, ext, sz, cnt, paths = row
    conn.execute("INSERT INTO duplicates (normalized_name, extension, size_bytes, copy_count, file_paths) VALUES (?,?,?,?,?)",
                 (norm, ext, sz, cnt, paths))
    dup_count += 1
    total_waste += sz * (cnt - 1)

conn.commit()

# Save stats
stats = {
    'total_files': total,
    'errors': errors,
    'scan_time_s': round(elapsed, 1),
    'duplicate_groups': dup_count,
    'wasted_bytes': total_waste,
}
for k, v in stats.items():
    conn.execute("INSERT OR REPLACE INTO scan_stats (key, value) VALUES (?, ?)", (k, str(v)))
conn.commit()

print(f"Duplicate groups: {dup_count}")
print(f"Wasted space: {total_waste/1024/1024:.1f} MB")

# Top folders summary
print("\n=== TOP FOLDER SUMMARY ===")
cursor = conn.execute("""
    SELECT top_folder, COUNT(*) as cnt, SUM(size_bytes) as total_sz
    FROM files
    GROUP BY top_folder
    ORDER BY total_sz DESC
    LIMIT 25
""")
for row in cursor:
    tf, cnt, sz = row
    sz_mb = (sz or 0) / (1024*1024)
    print(f"  {cnt:>8} files  {sz_mb:>10.1f} MB  {tf}")

# Category summary
print("\n=== CATEGORY SUMMARY ===")
cursor = conn.execute("""
    SELECT category, COUNT(*) as cnt, SUM(size_bytes) as total_sz
    FROM files
    GROUP BY category
    ORDER BY cnt DESC
""")
for row in cursor:
    cat, cnt, sz = row
    sz_mb = (sz or 0) / (1024*1024)
    print(f"  {cnt:>8} files  {sz_mb:>10.1f} MB  {cat}")

# Extension summary
print("\n=== EXTENSION SUMMARY (top 20) ===")
cursor = conn.execute("""
    SELECT extension, COUNT(*) as cnt, SUM(size_bytes) as total_sz
    FROM files
    GROUP BY extension
    ORDER BY cnt DESC
    LIMIT 20
""")
for row in cursor:
    ext, cnt, sz = row
    sz_mb = (sz or 0) / (1024*1024)
    print(f"  {cnt:>8}x {ext or '(none)':>10}  {sz_mb:>10.1f} MB")

# Top 15 largest duplicate groups
print("\n=== TOP 15 LARGEST DUPLICATE GROUPS ===")
cursor = conn.execute("""
    SELECT normalized_name, size_bytes, copy_count, file_paths
    FROM duplicates
    ORDER BY size_bytes * copy_count DESC
    LIMIT 15
""")
for row in cursor:
    norm, sz, cnt, paths = row
    path_list = paths.split('|||')
    print(f"\n  [{cnt} copies, {sz/1024:.0f} KB each] {norm}")
    for p in path_list[:3]:
        print(f"    {p[-80:]}")
    if len(path_list) > 3:
        print(f"    ... and {len(path_list)-3} more")

conn.close()
print(f"\n=== CATALOG SAVED: {DB_PATH} ===")
