# -*- coding: utf-8 -*-
r"""
LitigationOS Deep Forensic Drive Scanner v3.0
================================================
- SHA256 fingerprinting for dedup
- Magic-byte content detection (not just extensions)
- Legal document scoring (Michigan patterns, case numbers, parties)
- Project structure detection (Python pkg, Node app, .NET, DB)
- Corrupt/empty/temp/trash classification
- SQLite manifest output for cross-drive queries
- Handles permission errors, symlinks, junction points gracefully

Usage: python deep_scanner.py <drive_letter> [max_depth]
Output: C:\Users\andre\LitigationOS\00_SYSTEM\manifests\drive_<X>_manifest.db
"""
import os, sys, json, hashlib, sqlite3, time, struct, re, stat
from pathlib import Path
from collections import Counter, defaultdict
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor, as_completed

DRIVE = sys.argv[1].upper().rstrip(':') if len(sys.argv) > 1 else 'C'
MAX_DEPTH = int(sys.argv[2]) if len(sys.argv) > 2 else 6
ROOT = f"{DRIVE}:\\"
MANIFEST_DIR = r"C:\Users\andre\LitigationOS\00_SYSTEM\manifests"
DB_PATH = os.path.join(MANIFEST_DIR, f"drive_{DRIVE}_manifest.db")

# ─── MAGIC BYTES ───
MAGIC_SIGS = {
    b'%PDF':       'pdf',
    b'PK\x03\x04': 'zip_or_docx',
    b'\x89PNG':    'png',
    b'\xff\xd8\xff': 'jpeg',
    b'GIF8':       'gif',
    b'SQLite format 3': 'sqlite',
    b'RIFF':       'riff_avi_wav',
    b'\x00\x00\x01\x00': 'ico',
    b'{\n':        'json_maybe',
    b'{\r\n':      'json_maybe',
    b'<!DOCTYPE':  'html',
    b'<html':      'html',
    b'#!':         'script',
    b'\x1f\x8b':   'gzip',
    b'BM':         'bmp',
    b'\x00\x00\x00\x1c\x66\x74\x79\x70': 'mp4',
    b'\x49\x44\x33': 'mp3',
    b'\xff\xfb':   'mp3',
}

# ─── LEGAL PATTERNS ───
LEGAL_PATTERNS = [
    (re.compile(r'20(23|24|25)-\d{4,6}-(DC|PP|CZ|DM|FC|CC)', re.I), 20, 'case_number'),
    (re.compile(r'pigors|watson|hoopes|mcneill|muskegon', re.I), 15, 'party_judge'),
    (re.compile(r'14th\s*(judicial|circuit)|muskegon\s*county', re.I), 15, 'jurisdiction'),
    (re.compile(r'motion\s*(to|for)|brief\s*in|complaint|petition|affidavit', re.I), 10, 'filing_type'),
    (re.compile(r'MCR\s*\d|MCL\s*\d|USC\s*§|42\s*USC|1983|due\s*process', re.I), 10, 'legal_cite'),
    (re.compile(r'custody|parenting\s*time|child\s*support|FOC|friend\s*of\s*court', re.I), 8, 'family_law'),
    (re.compile(r'shady\s*oaks|housing|habitability|mold|lead|repair', re.I), 8, 'housing'),
    (re.compile(r'JTC|judicial\s*tenure|misconduct|disqualif', re.I), 10, 'judicial'),
    (re.compile(r'exhibit|evidence|deposition|discovery|subpoena', re.I), 6, 'evidence'),
    (re.compile(r'court\s*of\s*appeals|COA|supreme\s*court|appellant|appellee', re.I), 8, 'appellate'),
]

# ─── TRASH PATTERNS ───
TRASH_NAMES = {
    'thumbs.db', 'desktop.ini', '.ds_store', 'ntuser.dat', 'ntuser.dat.log',
    'ntuser.pol', 'iconcache.db', 'usrclass.dat', 'usrclass.dat.log',
}
TRASH_EXTS = {'.tmp', '.temp', '.bak', '.old', '.log', '.swp', '.swo', '.pyc', '.pyo'}

SKIP_DIRS = {
    'node_modules', '.git', '__pycache__', '.next', 'venv', '.venv', 'dist',
    '$Recycle.Bin', 'System Volume Information', 'Windows', 'ProgramData',
    'Recovery', 'AppData', '.cache', '.npm', '.nuget',
    'Program Files', 'Program Files (x86)',
}

# ─── PROJECT MARKERS ───
PROJECT_MARKERS = {
    'python_package': ['setup.py', 'pyproject.toml', 'requirements.txt', '__init__.py'],
    'node_app': ['package.json', 'node_modules'],
    'litigationos_pipeline': ['agent_base.py', 'local_ai_engine.py', 'config.py'],
    'litigationos_lexos': ['lexos_server.py', 'lexos_config.json'],
    'litigationos_app': ['base_agent.py', 'base_agent_upgraded.py'],
    'dotnet': ['*.csproj', '*.sln'],
    'database_dir': ['*.db', '*.sqlite', '*.sqlite3'],
    'legal_filing_dir': ['motion_*.pdf', 'brief_*.pdf', 'complaint_*.pdf'],
}

def detect_magic(filepath, size=32):
    """Detect file type by magic bytes."""
    try:
        with open(filepath, 'rb') as f:
            header = f.read(size)
        for sig, ftype in MAGIC_SIGS.items():
            if header.startswith(sig):
                return ftype
        if header and all(b < 128 for b in header[:min(len(header), 512)] if b != 0):
            return 'text'
        return 'binary'
    except:
        return 'unreadable'

def sha256_file(filepath, chunk_size=65536):
    """SHA256 hash, first 1MB only for speed on large files."""
    h = hashlib.sha256()
    try:
        with open(filepath, 'rb') as f:
            total = 0
            while total < 1_048_576:
                chunk = f.read(chunk_size)
                if not chunk:
                    break
                h.update(chunk)
                total += len(chunk)
        return h.hexdigest()
    except:
        return None

def score_legal_content(filepath, filename):
    """Score how legally relevant a file is (0-100)."""
    score = 0
    signals = []
    name_lower = filename.lower()
    path_lower = filepath.lower()
    
    # Score by filename/path
    for pattern, points, signal_type in LEGAL_PATTERNS:
        if pattern.search(name_lower) or pattern.search(path_lower):
            score += points
            signals.append(signal_type)
    
    # Bonus for being in known legal directories
    legal_dirs = ['evidence', 'court', 'filing', 'motion', 'brief', 'custody', 'housing',
                  'legal', 'litigation', 'case', 'judicial', 'exhibit']
    for ld in legal_dirs:
        if ld in path_lower:
            score += 3
            break
    
    # Try to peek into text files for legal content
    ext = os.path.splitext(filename)[1].lower()
    if ext in ('.txt', '.md', '.py', '.json', '.csv', '.log') and os.path.getsize(filepath) < 500_000:
        try:
            with open(filepath, 'r', errors='ignore') as f:
                sample = f.read(2000)
            for pattern, points, signal_type in LEGAL_PATTERNS:
                if pattern.search(sample) and signal_type not in signals:
                    score += points // 2
                    signals.append(signal_type + '_content')
        except:
            pass
    
    return min(score, 100), signals

def classify_file(filepath, filename, size, magic_type):
    """Classify a file into a category."""
    name_lower = filename.lower()
    ext = os.path.splitext(name_lower)[1]
    
    # Trash detection
    if name_lower in TRASH_NAMES:
        return 'trash'
    if ext in TRASH_EXTS:
        return 'temp_trash'
    if size == 0:
        return 'empty'
    
    # By magic type
    if magic_type == 'sqlite':
        return 'database'
    if magic_type == 'pdf':
        return 'document_pdf'
    if magic_type in ('jpeg', 'png', 'gif', 'bmp'):
        return 'image'
    if magic_type in ('mp3', 'riff_avi_wav'):
        return 'audio'
    if magic_type == 'mp4':
        return 'video'
    if magic_type == 'zip_or_docx':
        if ext in ('.docx', '.xlsx', '.pptx'):
            return 'document_office'
        return 'archive'
    if magic_type == 'gzip':
        return 'archive'
    if magic_type == 'html':
        return 'web'
    
    # By extension
    if ext in ('.py', '.js', '.ts', '.jsx', '.tsx', '.go', '.rs', '.java', '.cs', '.cpp', '.c', '.h'):
        return 'source_code'
    if ext in ('.md', '.txt', '.rst', '.rtf'):
        return 'text'
    if ext in ('.json', '.yml', '.yaml', '.toml', '.ini', '.cfg', '.env'):
        return 'config'
    if ext in ('.pdf',):
        return 'document_pdf'
    if ext in ('.doc', '.docx', '.xlsx', '.xls', '.pptx'):
        return 'document_office'
    if ext in ('.jpg', '.jpeg', '.png', '.gif', '.bmp', '.svg', '.ico', '.webp', '.tiff', '.heic'):
        return 'image'
    if ext in ('.mp3', '.wav', '.flac', '.aac', '.ogg', '.wma'):
        return 'audio'
    if ext in ('.mp4', '.avi', '.mov', '.mkv', '.wmv', '.flv'):
        return 'video'
    if ext in ('.zip', '.tar', '.gz', '.7z', '.rar', '.bz2'):
        return 'archive'
    if ext in ('.exe', '.msi', '.dll', '.so', '.dylib'):
        return 'binary_executable'
    if ext in ('.bat', '.cmd', '.ps1', '.sh'):
        return 'script'
    
    if magic_type == 'text':
        return 'text'
    return 'other'

def init_db(db_path):
    """Create manifest database."""
    conn = sqlite3.connect(db_path)
    c = conn.cursor()
    c.executescript('''
        DROP TABLE IF EXISTS files;
        DROP TABLE IF EXISTS directories;
        DROP TABLE IF EXISTS projects;
        DROP TABLE IF EXISTS summary;
        
        CREATE TABLE files (
            id INTEGER PRIMARY KEY,
            path TEXT NOT NULL,
            filename TEXT NOT NULL,
            extension TEXT,
            size_bytes INTEGER,
            sha256_1mb TEXT,
            magic_type TEXT,
            category TEXT,
            legal_score INTEGER DEFAULT 0,
            legal_signals TEXT,
            is_trash BOOLEAN DEFAULT 0,
            is_empty BOOLEAN DEFAULT 0,
            is_corrupt BOOLEAN DEFAULT 0,
            modified_ts TEXT,
            created_ts TEXT
        );
        
        CREATE TABLE directories (
            id INTEGER PRIMARY KEY,
            path TEXT NOT NULL,
            depth INTEGER,
            file_count INTEGER,
            total_size_bytes INTEGER,
            dominant_category TEXT,
            project_type TEXT,
            legal_relevance_avg REAL DEFAULT 0
        );
        
        CREATE TABLE projects (
            id INTEGER PRIMARY KEY,
            root_path TEXT NOT NULL,
            project_type TEXT,
            file_count INTEGER,
            total_size_bytes INTEGER,
            has_python BOOLEAN,
            has_node BOOLEAN,
            has_database BOOLEAN,
            description TEXT
        );
        
        CREATE TABLE summary (
            key TEXT PRIMARY KEY,
            value TEXT
        );
        
        CREATE INDEX idx_files_sha ON files(sha256_1mb);
        CREATE INDEX idx_files_cat ON files(category);
        CREATE INDEX idx_files_legal ON files(legal_score);
        CREATE INDEX idx_files_path ON files(path);
        CREATE INDEX idx_dirs_path ON directories(path);
    ''')
    conn.commit()
    return conn

# ─── MAIN SCAN ───
print(f"{'='*70}")
print(f"  DEEP FORENSIC SCAN: {DRIVE}: drive")
print(f"  Max depth: {MAX_DEPTH} | Output: {DB_PATH}")
print(f"{'='*70}")

os.makedirs(MANIFEST_DIR, exist_ok=True)
conn = init_db(DB_PATH)
cursor = conn.cursor()

t0 = time.time()
file_count = 0
dir_count = 0
errors = 0
categories = Counter()
dir_data = {}

# For C: drive, only scan user directories
if DRIVE == 'C':
    scan_roots = [
        r'C:\Users\andre\LitigationOS',
        r'C:\Users\andre\LITIGATIONOS_MASTER',
        r'C:\Users\andre\Desktop',
        r'C:\Users\andre\Documents',
        r'C:\Users\andre\Downloads',
        r'C:\Users\andre\scans',
        r'C:\Users\andre\.agents',
    ]
    scan_roots = [r for r in scan_roots if os.path.exists(r)]
else:
    scan_roots = [ROOT]

for scan_root in scan_roots:
    for dirpath, dirnames, filenames in os.walk(scan_root):
        depth = dirpath.replace(scan_root, '').count(os.sep)
        if depth > MAX_DEPTH:
            dirnames.clear()
            continue
        
        # Skip junk directories
        original_count = len(dirnames)
        dirnames[:] = [d for d in dirnames if d not in SKIP_DIRS and not d.startswith('$')]
        
        dir_count += 1
        dir_files = 0
        dir_size = 0
        dir_cats = Counter()
        dir_legal_scores = []
        
        # Detect project type
        all_files_lower = set(f.lower() for f in filenames)
        project_type = None
        for ptype, markers in PROJECT_MARKERS.items():
            for marker in markers:
                if '*' in marker:
                    ext = marker.replace('*', '')
                    if any(f.endswith(ext) for f in all_files_lower):
                        project_type = ptype
                        break
                elif marker.lower() in all_files_lower:
                    project_type = ptype
                    break
            if project_type:
                break
        
        for filename in filenames:
            filepath = os.path.join(dirpath, filename)
            try:
                fstat = os.stat(filepath)
                size = fstat.st_size
                ext = os.path.splitext(filename)[1].lower()
                
                # Magic byte detection (skip very large files)
                magic = 'skipped' if size > 50_000_000 else detect_magic(filepath)
                
                # SHA256 (first 1MB)
                sha = sha256_file(filepath) if size > 0 and size < 500_000_000 else None
                
                # Classify
                category = classify_file(filepath, filename, size, magic)
                
                # Legal scoring
                legal_score, legal_signals = score_legal_content(filepath, filename)
                
                # Timestamps
                try:
                    mtime = datetime.fromtimestamp(fstat.st_mtime).isoformat()
                    ctime = datetime.fromtimestamp(fstat.st_ctime).isoformat()
                except:
                    mtime = ctime = None
                
                is_trash = category in ('trash', 'temp_trash')
                is_empty = size == 0
                is_corrupt = magic == 'unreadable' and size > 0
                
                cursor.execute('''INSERT INTO files 
                    (path, filename, extension, size_bytes, sha256_1mb, magic_type, 
                     category, legal_score, legal_signals, is_trash, is_empty, is_corrupt,
                     modified_ts, created_ts)
                    VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?)''',
                    (filepath, filename, ext, size, sha, magic, category,
                     legal_score, json.dumps(legal_signals) if legal_signals else None,
                     is_trash, is_empty, is_corrupt, mtime, ctime))
                
                file_count += 1
                dir_files += 1
                dir_size += size
                dir_cats[category] += 1
                if legal_score > 0:
                    dir_legal_scores.append(legal_score)
                categories[category] += 1
                
            except (PermissionError, OSError) as e:
                errors += 1
                continue
        
        # Record directory
        dominant = dir_cats.most_common(1)[0][0] if dir_cats else 'empty'
        avg_legal = sum(dir_legal_scores) / len(dir_legal_scores) if dir_legal_scores else 0
        
        cursor.execute('''INSERT INTO directories 
            (path, depth, file_count, total_size_bytes, dominant_category, project_type, legal_relevance_avg)
            VALUES (?,?,?,?,?,?,?)''',
            (dirpath, depth, dir_files, dir_size, dominant, project_type, avg_legal))
        
        # Record projects
        if project_type:
            cursor.execute('''INSERT INTO projects 
                (root_path, project_type, file_count, total_size_bytes, has_python, has_node, has_database, description)
                VALUES (?,?,?,?,?,?,?,?)''',
                (dirpath, project_type, dir_files, dir_size,
                 any(f.endswith('.py') for f in all_files_lower),
                 'package.json' in all_files_lower,
                 any(f.endswith(('.db','.sqlite','.sqlite3')) for f in all_files_lower),
                 f"{project_type} in {os.path.basename(dirpath)}"))
        
        # Progress every 500 dirs
        if dir_count % 500 == 0:
            conn.commit()
            elapsed = time.time() - t0
            print(f"  ... {dir_count:,} dirs, {file_count:,} files scanned ({elapsed:.0f}s)")

# Write summary
elapsed = time.time() - t0
summary = {
    'drive': DRIVE,
    'scan_time': datetime.now().isoformat(),
    'elapsed_seconds': round(elapsed, 1),
    'total_files': file_count,
    'total_dirs': dir_count,
    'scan_errors': errors,
    'categories': dict(categories.most_common()),
}

for k, v in summary.items():
    cursor.execute('INSERT OR REPLACE INTO summary (key, value) VALUES (?,?)', (k, json.dumps(v)))

conn.commit()

# ─── PRINT RESULTS ───
print(f"\n{'─'*70}")
print(f"  ✅ SCAN COMPLETE: {DRIVE}: drive")
print(f"  {file_count:,} files | {dir_count:,} dirs | {errors} errors | {elapsed:.1f}s")
print(f"{'─'*70}")

print(f"\n  📊 FILE CATEGORIES:")
for cat, count in categories.most_common():
    cursor.execute('SELECT SUM(size_bytes) FROM files WHERE category=?', (cat,))
    size_mb = (cursor.fetchone()[0] or 0) / 1048576
    print(f"    {cat:25s} {count:>7,} files  {size_mb:>10.1f} MB")

# Duplicates
print(f"\n  🔁 DUPLICATE DETECTION (by SHA256):")
cursor.execute('''SELECT sha256_1mb, COUNT(*) as cnt, SUM(size_bytes) as total_size
    FROM files WHERE sha256_1mb IS NOT NULL 
    GROUP BY sha256_1mb HAVING cnt > 1
    ORDER BY total_size DESC LIMIT 15''')
dupes = cursor.fetchall()
total_dupe_waste = 0
for sha, cnt, tsize in dupes:
    cursor.execute('SELECT path FROM files WHERE sha256_1mb=? LIMIT 3', (sha,))
    paths = [r[0] for r in cursor.fetchall()]
    waste = tsize - (tsize // cnt)
    total_dupe_waste += waste
    print(f"    {cnt}x copies ({tsize/1048576:.1f}MB total, {waste/1048576:.1f}MB wasted)")
    for p in paths:
        print(f"      └─ {p}")

cursor.execute('''SELECT COUNT(*), SUM(size_bytes) FROM (
    SELECT sha256_1mb, COUNT(*) as cnt, SUM(size_bytes) as size_bytes
    FROM files WHERE sha256_1mb IS NOT NULL
    GROUP BY sha256_1mb HAVING cnt > 1)''')
dupe_groups, dupe_total = cursor.fetchone()
print(f"\n  Total duplicate groups: {dupe_groups or 0}")
print(f"  Estimated recoverable space: {(total_dupe_waste/1048576):.1f} MB")

# Legal files
print(f"\n  ⚖️  TOP LEGAL-RELEVANT FILES:")
cursor.execute('''SELECT path, legal_score, legal_signals FROM files 
    WHERE legal_score > 10 ORDER BY legal_score DESC LIMIT 15''')
for path, score, signals in cursor.fetchall():
    print(f"    [{score:3d}] {path}")
    if signals:
        print(f"           signals: {signals}")

# Trash/empty
cursor.execute('SELECT COUNT(*), SUM(size_bytes) FROM files WHERE is_trash=1')
trash_count, trash_size = cursor.fetchone()
cursor.execute('SELECT COUNT(*) FROM files WHERE is_empty=1')
empty_count = cursor.fetchone()[0]
cursor.execute('SELECT COUNT(*) FROM files WHERE is_corrupt=1')
corrupt_count = cursor.fetchone()[0]
print(f"\n  🗑️  CLEANUP TARGETS:")
print(f"    Trash files:   {trash_count or 0:,} ({(trash_size or 0)/1048576:.1f} MB)")
print(f"    Empty files:   {empty_count:,}")
print(f"    Corrupt files: {corrupt_count:,}")

# Projects
print(f"\n  📁 PROJECT STRUCTURES DETECTED:")
cursor.execute('SELECT root_path, project_type, file_count, total_size_bytes FROM projects ORDER BY total_size_bytes DESC LIMIT 20')
for root, ptype, fcount, psize in cursor.fetchall():
    print(f"    [{ptype:30s}] {root} ({fcount} files, {psize/1048576:.1f}MB)")

# Databases
print(f"\n  💾 DATABASES:")
cursor.execute("SELECT path, size_bytes FROM files WHERE category='database' ORDER BY size_bytes DESC LIMIT 15")
for path, size in cursor.fetchall():
    print(f"    {size/1048576:>10.1f} MB — {path}")

conn.close()
print(f"\n  💾 Manifest DB: {DB_PATH}")
print(f"  Query with: sqlite3 {DB_PATH} \"SELECT ...\"")