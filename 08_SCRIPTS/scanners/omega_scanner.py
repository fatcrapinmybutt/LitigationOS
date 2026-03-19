"""
LitigationOS OMEGA Scanner v2.0
=================================
- Magic-byte file type detection (first 16 bytes, NO full-file hashing)
- Legal document scoring (Michigan patterns, case numbers, parties)
- Name normalization for dedup (no SHA256 — names+sizes only)
- Per-drive SQLite manifest
- Category classification
- Fast: only reads first 16 bytes per file

Usage: python omega_scanner.py <drive_or_path> [max_depth]
"""
import sys, os, re, sqlite3, time, struct
from pathlib import Path
from collections import Counter, defaultdict
from datetime import datetime
sys.stdout = open(sys.stdout.fileno(), mode='w', encoding='utf-8', errors='replace')

TARGET = sys.argv[1] if len(sys.argv) > 1 else r"C:\Users\andre\LitigationOS"
MAX_DEPTH = int(sys.argv[2]) if len(sys.argv) > 2 else 999

# Determine if this is a drive letter or a path
if len(TARGET) <= 2 and TARGET[0].isalpha():
    ROOT = f"{TARGET.upper().rstrip(':')}:\\"
    DRIVE = TARGET[0].upper()
else:
    ROOT = TARGET
    DRIVE = "C"  # default

MANIFEST_DIR = r"C:\Users\andre\LitigationOS\00_SYSTEM\manifests"
os.makedirs(MANIFEST_DIR, exist_ok=True)
DB_PATH = os.path.join(MANIFEST_DIR, f"omega_{DRIVE}_manifest.db")

# ─── MAGIC BYTES (first 16 bytes) ───
MAGIC_SIGS = {
    b'%PDF':        'pdf',
    b'PK\x03\x04':  'zip_or_docx',
    b'\x89PNG':     'png',
    b'\xff\xd8\xff': 'jpeg',
    b'GIF8':        'gif',
    b'SQLite format': 'sqlite',
    b'RIFF':        'riff',
    b'<!DOCTYPE':   'html',
    b'<html':       'html',
    b'#!':          'script',
    b'\x1f\x8b':    'gzip',
    b'BM':          'bmp',
    b'\x49\x44\x33': 'mp3',
    b'\xff\xfb':    'mp3',
    b'\x00\x00\x01\x00': 'ico',
    b'{':           'json_maybe',
    b'[':           'json_maybe',
}

def detect_magic(filepath):
    try:
        with open(filepath, 'rb') as f:
            header = f.read(16)
        if not header:
            return 'empty'
        for sig, ftype in MAGIC_SIGS.items():
            if header.startswith(sig):
                return ftype
        if all(32 <= b < 127 or b in (9,10,13) for b in header):
            return 'text'
        return 'binary'
    except:
        return 'unknown'

# ─── LEGAL SCORING ───
LEGAL_PATTERNS = [
    (re.compile(r'MCL\s+\d+\.\d+', re.I), 20, 'MCL'),
    (re.compile(r'MCR\s+\d+\.\d+', re.I), 20, 'MCR'),
    (re.compile(r'MRE\s+\d+', re.I), 15, 'MRE'),
    (re.compile(r'\d+\s+Mich\s+App\s+\d+', re.I), 25, 'CASE_CITE'),
    (re.compile(r'42\s+USC\s+.{1,10}1983', re.I), 20, 'USC_1983'),
    (re.compile(r'(?:motion|brief|order|stipulation|affidavit|petition|complaint)', re.I), 10, 'LEGAL_DOC'),
    (re.compile(r'(?:custody|parenting|child|visitation|support)', re.I), 8, 'CUSTODY'),
    (re.compile(r'(?:watson|pigors|mcneill|barnes)', re.I), 15, 'PARTY_NAME'),
    (re.compile(r'(?:PPO|protection order|personal protection)', re.I), 12, 'PPO'),
    (re.compile(r'(?:best.interest|BIF|722\.23)', re.I), 15, 'BIF'),
    (re.compile(r'(?:contempt|discovery|sanctions|disqualif)', re.I), 10, 'LEGAL_ACTION'),
    (re.compile(r'(?:JTC|judicial.tenure|misconduct)', re.I), 15, 'JTC'),
    (re.compile(r'2024-001507|2023-5907|2025-002760', re.I), 25, 'CASE_NUMBER'),
    (re.compile(r'(?:exhibit|evidence|transcript|deposition)', re.I), 8, 'EVIDENCE'),
    (re.compile(r'(?:court\s+of\s+appeals|COA|appellate|MSC|supreme\s+court)', re.I), 12, 'APPELLATE'),
]

def score_legal(filename, filepath=None):
    text = filename
    score = 0
    signals = []
    for pat, pts, label in LEGAL_PATTERNS:
        if pat.search(text):
            score += pts
            signals.append(label)
    return score, ','.join(signals)

# ─── NAME NORMALIZATION ───
def normalize_name(name):
    n = name.lower().strip()
    n = re.sub(r'\s*\(\d+\)\s*', '', n)           # (1), (2)
    n = re.sub(r'_v\d+(\.\d+)*', '', n)            # _v2, _v1.0.0
    n = re.sub(r'_dup\d*', '', n)                   # _dup, _dup2
    n = re.sub(r'_copy\d*', '', n)                  # _copy
    n = re.sub(r'_root$', '', n)
    n = re.sub(r'_?\d{8}[T_]?\d{0,6}Z?', '', n)    # timestamps
    n = re.sub(r'[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}', '', n)  # UUIDs
    n = re.sub(r'[_-]+', '_', n).strip('_. ')
    return n

# ─── CATEGORY CLASSIFICATION ───
EXT_CATEGORIES = {
    '.py': 'code', '.js': 'code', '.ts': 'code', '.jsx': 'code', '.tsx': 'code',
    '.rs': 'code', '.go': 'code', '.java': 'code', '.c': 'code', '.cpp': 'code',
    '.h': 'code', '.cs': 'code', '.rb': 'code', '.php': 'code', '.sh': 'code',
    '.ps1': 'code', '.bat': 'code', '.cmd': 'code', '.r': 'code', '.lua': 'code',
    '.md': 'document', '.txt': 'document', '.rst': 'document', '.doc': 'document',
    '.docx': 'document', '.rtf': 'document', '.odt': 'document',
    '.pdf': 'pdf',
    '.json': 'data', '.jsonl': 'data', '.yaml': 'data', '.yml': 'data',
    '.toml': 'data', '.xml': 'data', '.csv': 'data', '.tsv': 'data',
    '.html': 'web', '.htm': 'web', '.css': 'web', '.scss': 'web',
    '.png': 'image', '.jpg': 'image', '.jpeg': 'image', '.gif': 'image',
    '.svg': 'image', '.bmp': 'image', '.ico': 'image', '.webp': 'image',
    '.zip': 'archive', '.tar': 'archive', '.gz': 'archive', '.7z': 'archive',
    '.rar': 'archive', '.bz2': 'archive',
    '.db': 'database', '.sqlite': 'database', '.sqlite3': 'database',
    '.exe': 'binary', '.dll': 'binary', '.so': 'binary', '.msi': 'binary',
    '.pyc': 'compiled', '.pyo': 'compiled', '.class': 'compiled',
    '.mp3': 'media', '.mp4': 'media', '.avi': 'media', '.wav': 'media',
    '.lnk': 'shortcut', '.log': 'log', '.mmd': 'diagram', '.ebnf': 'grammar',
}

def classify(ext, name):
    ext = ext.lower()
    cat = EXT_CATEGORIES.get(ext)
    if cat:
        return cat
    nl = name.lower()
    if any(k in nl for k in ('legal','court','mcl','mcr','motion','custody','order')):
        return 'legal'
    return 'other'

# ─── DATABASE SETUP ───
conn = sqlite3.connect(DB_PATH)
conn.execute("PRAGMA journal_mode=WAL")
conn.execute("PRAGMA synchronous=NORMAL")
conn.executescript("""
    DROP TABLE IF EXISTS files;
    CREATE TABLE files (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        path TEXT NOT NULL,
        filename TEXT NOT NULL,
        normalized_name TEXT NOT NULL,
        extension TEXT,
        size_bytes INTEGER,
        magic_type TEXT,
        category TEXT,
        legal_score INTEGER DEFAULT 0,
        legal_signals TEXT,
        is_empty BOOLEAN DEFAULT 0,
        modified_ts TEXT,
        parent_dir TEXT,
        depth INTEGER,
        top_folder TEXT
    );
    CREATE INDEX idx_norm ON files(normalized_name);
    CREATE INDEX idx_ext ON files(extension);
    CREATE INDEX idx_size ON files(size_bytes);
    CREATE INDEX idx_cat ON files(category);
    CREATE INDEX idx_legal ON files(legal_score);
    CREATE INDEX idx_top ON files(top_folder);
    
    DROP TABLE IF EXISTS duplicates;
    CREATE TABLE duplicates (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        normalized_name TEXT,
        extension TEXT,
        size_bytes INTEGER,
        copy_count INTEGER,
        file_paths TEXT,
        total_waste INTEGER
    );
    
    DROP TABLE IF EXISTS directories;
    CREATE TABLE directories (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        path TEXT NOT NULL,
        name TEXT NOT NULL,
        file_count INTEGER DEFAULT 0,
        total_size INTEGER DEFAULT 0,
        depth INTEGER
    );
    
    DROP TABLE IF EXISTS summary;
    CREATE TABLE summary (key TEXT PRIMARY KEY, value TEXT);
""")

# ─── SCAN ───
print(f"{'='*70}")
print(f"  OMEGA SCANNER v2.0: {ROOT}")
print(f"  Max depth: {MAX_DEPTH} | DB: {DB_PATH}")
print(f"{'='*70}")

start = time.time()
batch_files = []
batch_dirs = []
total_files = 0
total_dirs = 0
errors = 0
BATCH = 3000
SKIP_DIRS = {'.git', '__pycache__', 'node_modules', '.svn', '$RECYCLE.BIN', 'System Volume Information'}

for dirpath, dirnames, filenames in os.walk(ROOT):
    # Skip blacklisted dirs
    dirnames[:] = [d for d in dirnames if d not in SKIP_DIRS]
    
    rel = os.path.relpath(dirpath, ROOT)
    depth = 0 if rel == '.' else rel.count(os.sep) + 1
    if depth > MAX_DEPTH:
        dirnames.clear()
        continue
    
    top = Path(rel).parts[0] if rel != '.' else '(root)'
    
    # Count dir stats
    dir_size = 0
    dir_files = 0
    
    for fn in filenames:
        fp = os.path.join(dirpath, fn)
        try:
            st = os.stat(fp)
            sz = st.st_size
            ext = os.path.splitext(fn)[1].lower()
            norm = normalize_name(os.path.splitext(fn)[0]) + ext
            cat = classify(ext, fn)
            lscore, lsigs = score_legal(fn)
            is_empty = 1 if sz == 0 else 0
            mtime = datetime.fromtimestamp(st.st_mtime).isoformat()
            
            # Magic bytes (only for files > 0 bytes, read first 16 bytes only)
            magic = 'empty' if sz == 0 else detect_magic(fp)
            
            batch_files.append((fp, fn, norm, ext, sz, magic, cat, lscore, lsigs, is_empty, mtime, rel, depth, top))
            total_files += 1
            dir_size += sz
            dir_files += 1
            
            if len(batch_files) >= BATCH:
                conn.executemany("""INSERT INTO files 
                    (path,filename,normalized_name,extension,size_bytes,magic_type,category,
                     legal_score,legal_signals,is_empty,modified_ts,parent_dir,depth,top_folder)
                    VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?)""", batch_files)
                conn.commit()
                batch_files = []
                elapsed = time.time() - start
                rate = total_files / elapsed if elapsed > 0 else 0
                print(f"  {total_files:>8,} files | {total_dirs:>6,} dirs | {elapsed:.0f}s | {rate:.0f} files/s")
        except Exception as e:
            errors += 1
    
    batch_dirs.append((dirpath, os.path.basename(dirpath), dir_files, dir_size, depth))
    total_dirs += 1
    
    if len(batch_dirs) >= 500:
        conn.executemany("INSERT INTO directories (path,name,file_count,total_size,depth) VALUES (?,?,?,?,?)", batch_dirs)
        conn.commit()
        batch_dirs = []

# Final batches
if batch_files:
    conn.executemany("""INSERT INTO files 
        (path,filename,normalized_name,extension,size_bytes,magic_type,category,
         legal_score,legal_signals,is_empty,modified_ts,parent_dir,depth,top_folder)
        VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?)""", batch_files)
if batch_dirs:
    conn.executemany("INSERT INTO directories (path,name,file_count,total_size,depth) VALUES (?,?,?,?,?)", batch_dirs)
conn.commit()

elapsed = time.time() - start
print(f"\n{'='*70}")
print(f"  SCAN COMPLETE: {total_files:,} files, {total_dirs:,} dirs, {errors} errors in {elapsed:.1f}s")
print(f"{'='*70}")

# ─── FIND DUPLICATES (name + size) ───
print("\nFinding duplicates by normalized name + size...")
cursor = conn.execute("""
    SELECT normalized_name, extension, size_bytes, COUNT(*) as cnt, 
           GROUP_CONCAT(path, '|||')
    FROM files WHERE size_bytes > 100
    GROUP BY normalized_name, size_bytes
    HAVING cnt > 1
    ORDER BY cnt * size_bytes DESC
""")

dup_count = 0
total_waste = 0
for row in cursor:
    norm, ext, sz, cnt, paths = row
    waste = sz * (cnt - 1)
    conn.execute("""INSERT INTO duplicates 
        (normalized_name, extension, size_bytes, copy_count, file_paths, total_waste) 
        VALUES (?,?,?,?,?,?)""", (norm, ext, sz, cnt, paths, waste))
    dup_count += 1
    total_waste += waste

conn.commit()

# ─── SUMMARY STATS ───
stats = {
    'total_files': str(total_files),
    'total_dirs': str(total_dirs),
    'errors': str(errors),
    'scan_time_s': str(round(elapsed, 1)),
    'duplicate_groups': str(dup_count),
    'wasted_bytes': str(total_waste),
    'scan_root': ROOT,
    'scan_date': datetime.now().isoformat(),
}
for k, v in stats.items():
    conn.execute("INSERT OR REPLACE INTO summary (key, value) VALUES (?,?)", (k, v))
conn.commit()

# ─── REPORTS ───
print(f"\n  Duplicate groups: {dup_count:,}")
print(f"  Wasted space: {total_waste/1024/1024:.1f} MB")

print("\n=== TOP FOLDERS ===")
for row in conn.execute("""
    SELECT top_folder, COUNT(*) as cnt, SUM(size_bytes) as sz, 
           SUM(CASE WHEN legal_score > 0 THEN 1 ELSE 0 END) as legal_cnt,
           AVG(legal_score) as avg_legal
    FROM files GROUP BY top_folder ORDER BY sz DESC LIMIT 25
"""):
    tf, cnt, sz, lcnt, lavg = row
    print(f"  {cnt:>8,} files  {(sz or 0)/1024/1024:>10.1f} MB  legal:{lcnt:>5}  avg_score:{lavg or 0:>5.1f}  {tf}")

print("\n=== CATEGORIES ===")
for row in conn.execute("""
    SELECT category, COUNT(*) as cnt, SUM(size_bytes) as sz
    FROM files GROUP BY category ORDER BY cnt DESC
"""):
    cat, cnt, sz = row
    print(f"  {cnt:>8,} files  {(sz or 0)/1024/1024:>10.1f} MB  {cat}")

print("\n=== MAGIC TYPES ===")
for row in conn.execute("""
    SELECT magic_type, COUNT(*) as cnt, SUM(size_bytes) as sz
    FROM files GROUP BY magic_type ORDER BY cnt DESC LIMIT 15
"""):
    mt, cnt, sz = row
    print(f"  {cnt:>8,} files  {(sz or 0)/1024/1024:>10.1f} MB  {mt}")

print("\n=== TOP LEGAL-SCORING FILES ===")
for row in conn.execute("""
    SELECT legal_score, legal_signals, filename, path
    FROM files WHERE legal_score > 30
    ORDER BY legal_score DESC LIMIT 15
"""):
    score, sigs, fn, path = row
    print(f"  [{score:>3}] {sigs}: {fn[:60]}")

print("\n=== TOP 10 LARGEST DUPLICATE GROUPS ===")
for row in conn.execute("""
    SELECT normalized_name, size_bytes, copy_count, total_waste, file_paths
    FROM duplicates ORDER BY total_waste DESC LIMIT 10
"""):
    norm, sz, cnt, waste, paths = row
    plist = paths.split('|||')
    print(f"\n  [{cnt} copies, {sz/1024:.0f}KB each, {waste/1024/1024:.1f}MB wasted] {norm[:60]}")
    for p in plist[:2]:
        print(f"    {p[-80:]}")
    if len(plist) > 2:
        print(f"    ... +{len(plist)-2} more")

conn.close()
print(f"\n=== MANIFEST SAVED: {DB_PATH} ===")
