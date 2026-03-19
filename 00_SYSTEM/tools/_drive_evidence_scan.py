#!/usr/bin/env python3
"""
Drive Evidence Scanner — Pigors v Watson Litigation
Scans all drives for files relevant to the case and inserts into litigation_context.db
"""
import os, sqlite3, re, json, time, sys
from datetime import datetime

DB = r'C:\Users\andre\litigation_context.db'

KEYWORDS = [
    'watson', 'emily', 'albert', 'lori', 'cody', 'berry',
    'shady oaks', 'homes of america',
    'custody', 'parenting time', 'alienation', 'ppo', 'mcneill', 'barnes', 'pigors',
    'muskegon', 'norton shores', '2024-001507', '2023-5907', '366810', '2025-002760',
    'garland drive', 'whitehall road', 'friend of court', 'foc', 'visitation',
    'contempt', 'ex parte', 'hearing', 'petition', 'respondent', 'domestic',
    'protective order', 'child support', 'parental rights', 'best interest',
    'forensic', 'guardian ad litem', 'gal', 'supervised', 'tort',
    'intentional infliction', 'defamation', 'conspiracy', 'fraud',
    'court of appeals', 'docket', 'motion', 'affidavit', 'brief',
    'tiffany', 'andrew pigors', '14th circuit'
]

EXTENSIONS = {
    '.pdf', '.docx', '.doc', '.txt', '.md', '.msg', '.eml',
    '.csv', '.xlsx', '.xls', '.rtf', '.html', '.htm', '.json',
    '.odt', '.log', '.xml', '.yaml', '.yml', '.png', '.jpg', '.jpeg',
    '.tiff', '.tif', '.bmp', '.gif'
}

# Image extensions — only match by filename, don't try to read content
IMAGE_EXTS = {'.png', '.jpg', '.jpeg', '.tiff', '.tif', '.bmp', '.gif'}

SKIP_DIRS = {
    '$Recycle.Bin', 'System Volume Information', 'Windows', 'ProgramData',
    '.git', 'node_modules', '__pycache__', '.npm', '.cache', 'AppData',
    'Program Files', 'Program Files (x86)', 'LitigationOS',
    'Microsoft', 'Package Cache', 'AMD', 'Intel', 'NVIDIA',
    'WindowsApps', 'WinSxS', 'assembly', 'Recovery',
    '.vscode', '.vs', 'obj', 'bin', 'dist', 'build',
    'site-packages', 'Lib', 'venv', '.env',
}

# Additional skip for C:\Users\andre specifically
SKIP_DIRS_ANDRE = SKIP_DIRS | {'LitigationOS', 'node_modules'}

MAX_READ_SIZE = 50000  # 50KB

TORT_KEYWORDS = {
    'alienation': ['alienat', 'withhold', 'deny access', 'refuse', 'parenting time denied', 'kept from', 'no contact'],
    'fraud': ['fraud', 'misrepresent', 'false', 'lie', 'deceiv', 'fabricat', 'forged'],
    'conspiracy': ['conspir', 'concert', 'joint', 'plan', 'collu', 'scheme'],
    'abuse_of_process': ['abuse of process', 'ppo', 'false report', 'weaponiz', 'vexatious', 'frivolous'],
    'iied': ['emotional distress', 'outrageous', 'extreme', 'cruel', 'intentional infliction', 'severe emotional'],
    'defamation': ['defam', 'slander', 'libel', 'reputation', 'false statement', 'false accusation'],
    'interference': ['interfer', 'prevent', 'block', 'deny access', 'tortious interference', 'custodial interference'],
    'contempt': ['contempt', 'violat', 'disobey', 'willful', 'court order violat'],
    'due_process': ['due process', 'fundamental right', 'constitutional', 'deprivation', 'liberty interest'],
    'negligence': ['negligence', 'duty of care', 'breach', 'proximate cause', 'damages'],
}

PARTY_NAMES = [
    'emily watson', 'watson', 'albert watson', 'lori watson', 'cody watson',
    'tiffany watson', 'tiffany pigors', 'berry', 'mcneill', 'barnes',
    'pigors', 'andrew pigors', 'shady oaks', 'homes of america',
    'friend of court', 'guardian ad litem'
]


def create_table(conn):
    """Create the drive_evidence table if it doesn't exist."""
    conn.execute('''CREATE TABLE IF NOT EXISTS drive_evidence (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        file_path TEXT UNIQUE NOT NULL,
        drive_letter TEXT,
        file_type TEXT,
        file_size_bytes INTEGER,
        file_modified TEXT,
        relevance_score REAL DEFAULT 0,
        keyword_hits TEXT,
        extracted_facts TEXT,
        party_mentions TEXT,
        date_mentions TEXT,
        tort_relevance TEXT,
        case_lane TEXT,
        scan_timestamp TEXT DEFAULT CURRENT_TIMESTAMP,
        notes TEXT
    )''')
    conn.execute('''CREATE INDEX IF NOT EXISTS idx_drive_evidence_relevance 
                     ON drive_evidence(relevance_score DESC)''')
    conn.execute('''CREATE INDEX IF NOT EXISTS idx_drive_evidence_drive 
                     ON drive_evidence(drive_letter)''')
    conn.execute('''CREATE INDEX IF NOT EXISTS idx_drive_evidence_tort 
                     ON drive_evidence(tort_relevance)''')
    conn.commit()
    print("drive_evidence table ready.")


def determine_case_lane(combined_text):
    """Determine which case lane(s) a file pertains to."""
    lanes = []
    if any(w in combined_text for w in ['custody', 'parenting time', 'best interest', 'visitation', '2024-001507', 'child support']):
        lanes.append('A-Custody')
    if any(w in combined_text for w in ['shady oaks', 'homes of america', 'housing', 'garland', 'whitehall', 'manufactured home', 'mobile home']):
        lanes.append('B-Housing')
    if any(w in combined_text for w in ['ppo', 'protective order', '2023-5907', 'domestic violence', 'stalking']):
        lanes.append('D-PPO')
    if any(w in combined_text for w in ['misconduct', 'jt c', 'canon', 'judicial tenure', 'bias', 'prejudice']):
        lanes.append('E-Misconduct')
    if any(w in combined_text for w in ['appeal', 'court of appeals', '366810', 'claim of appeal', 'appellate']):
        lanes.append('F-Appellate')
    if len(lanes) > 1:
        lanes.append('C-Convergence')
    return lanes


def scan_drive(root, conn, max_files=5000, skip_dirs=None):
    """Walk a drive root, find relevant files, insert into DB."""
    if skip_dirs is None:
        skip_dirs = SKIP_DIRS
    count = 0
    found = 0
    errors = 0
    start = time.time()

    for dirpath, dirnames, filenames in os.walk(root, topdown=True):
        # Prune directories
        dirnames[:] = [d for d in dirnames if d not in skip_dirs and not d.startswith('.')]
        
        depth = dirpath.replace(root, '').count(os.sep)
        if depth > 15:
            dirnames.clear()
            continue

        for fname in filenames:
            if count >= max_files:
                print(f'  {root}: Hit max_files limit ({max_files}). Found {found} relevant.')
                return found
            
            ext = os.path.splitext(fname)[1].lower()
            if ext not in EXTENSIONS:
                continue

            fpath = os.path.join(dirpath, fname)
            count += 1

            try:
                # Check filename keywords
                fname_lower = fname.lower()
                path_lower = fpath.lower()
                name_hits = [k for k in KEYWORDS if k in fname_lower or k in path_lower]

                # Read content for text files (not images)
                content = ''
                content_hits = []
                if ext not in IMAGE_EXTS:
                    try:
                        with open(fpath, 'r', encoding='utf-8', errors='replace') as f:
                            content = f.read(MAX_READ_SIZE).lower()
                        content_hits = [k for k in KEYWORDS if k in content]
                    except Exception:
                        pass

                all_hits = list(set(name_hits + content_hits))
                if not all_hits:
                    continue

                found += 1

                # Extract dates from content
                dates = []
                if content:
                    date_patterns = re.findall(
                        r'\d{1,2}/\d{1,2}/\d{2,4}|\d{4}-\d{2}-\d{2}|\w+ \d{1,2},? \d{4}',
                        content[:MAX_READ_SIZE]
                    )
                    dates = list(set(date_patterns[:30]))

                # Party mentions
                combined = (path_lower + ' ' + content).lower()
                parties = [p for p in PARTY_NAMES if p in combined]
                parties = list(set(parties))

                # Tort relevance
                tort_hits = []
                for tort, words in TORT_KEYWORDS.items():
                    if any(w in combined for w in words):
                        tort_hits.append(tort)

                # Case lane
                lanes = determine_case_lane(combined)

                # Relevance score: more keyword hits = higher score, tort hits add weight
                score = len(all_hits) * 10.0 + len(tort_hits) * 15.0 + len(parties) * 5.0

                # File metadata
                try:
                    stat = os.stat(fpath)
                    fsize = stat.st_size
                    fmod = datetime.fromtimestamp(stat.st_mtime).isoformat()
                except Exception:
                    fsize = 0
                    fmod = ''

                conn.execute('''INSERT OR IGNORE INTO drive_evidence 
                    (file_path, drive_letter, file_type, file_size_bytes, file_modified,
                     relevance_score, keyword_hits, extracted_facts, 
                     party_mentions, date_mentions, tort_relevance, case_lane)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)''',
                    (fpath, root[0], ext, fsize, fmod,
                     score, json.dumps(all_hits), json.dumps(all_hits),
                     json.dumps(parties), json.dumps(dates),
                     json.dumps(tort_hits), json.dumps(lanes)))

                if found % 50 == 0:
                    conn.commit()
                    elapsed = time.time() - start
                    print(f'  {root}: {found} relevant / {count} scanned ({elapsed:.0f}s)')

            except (PermissionError, OSError):
                errors += 1
                continue
            except Exception as e:
                errors += 1
                continue

    conn.commit()
    elapsed = time.time() - start
    print(f'  {root}: DONE — {found} relevant / {count} scanned / {errors} errors ({elapsed:.0f}s)')
    return found


def print_summary(conn):
    """Print detailed summary of findings."""
    print('\n' + '='*80)
    print('EVIDENCE SCAN SUMMARY')
    print('='*80)

    total = conn.execute('SELECT COUNT(*) FROM drive_evidence').fetchone()[0]
    print(f'\nTotal files cataloged: {total}')

    # By drive
    print('\n--- FILES BY DRIVE ---')
    for r in conn.execute('SELECT drive_letter, COUNT(*), ROUND(AVG(relevance_score),1) FROM drive_evidence GROUP BY drive_letter ORDER BY COUNT(*) DESC'):
        print(f'  Drive {r[0]}: {r[1]} files (avg relevance: {r[2]})')

    # By file type
    print('\n--- FILES BY TYPE ---')
    for r in conn.execute('SELECT file_type, COUNT(*) FROM drive_evidence GROUP BY file_type ORDER BY COUNT(*) DESC LIMIT 15'):
        print(f'  {r[0]}: {r[1]} files')

    # Top 30 by relevance
    print('\n--- TOP 30 FILES BY RELEVANCE ---')
    for i, r in enumerate(conn.execute('''SELECT file_path, relevance_score, party_mentions, 
            tort_relevance, case_lane FROM drive_evidence 
            ORDER BY relevance_score DESC LIMIT 30''').fetchall(), 1):
        print(f'\n  #{i} [{r[1]:.0f}] {r[0]}')
        if r[2] and r[2] != '[]':
            print(f'    Parties: {r[2]}')
        if r[3] and r[3] != '[]':
            print(f'    Torts: {r[3]}')
        if r[4] and r[4] != '[]':
            print(f'    Lanes: {r[4]}')

    # Tort coverage
    print('\n--- TORT CLAIM EVIDENCE COVERAGE ---')
    for tort in TORT_KEYWORDS:
        count = conn.execute(
            "SELECT COUNT(*) FROM drive_evidence WHERE tort_relevance LIKE ?",
            (f'%{tort}%',)
        ).fetchone()[0]
        indicator = '✓' if count > 0 else '✗'
        print(f'  {indicator} {tort}: {count} files')

    # Case lane coverage
    print('\n--- CASE LANE COVERAGE ---')
    for lane in ['A-Custody', 'B-Housing', 'C-Convergence', 'D-PPO', 'E-Misconduct', 'F-Appellate']:
        count = conn.execute(
            "SELECT COUNT(*) FROM drive_evidence WHERE case_lane LIKE ?",
            (f'%{lane}%',)
        ).fetchone()[0]
        print(f'  {lane}: {count} files')

    # High-value evidence (score > 100)
    hv = conn.execute('SELECT COUNT(*) FROM drive_evidence WHERE relevance_score > 100').fetchone()[0]
    print(f'\nHigh-value evidence files (score > 100): {hv}')

    print('\n' + '='*80)


def main():
    print(f'Evidence Scanner — Pigors v Watson')
    print(f'Started: {datetime.now().isoformat()}')
    print(f'Database: {DB}')
    print()

    conn = sqlite3.connect(DB, timeout=30)
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA synchronous=NORMAL")
    
    create_table(conn)

    # Clear previous scan results to avoid stale data
    existing = conn.execute('SELECT COUNT(*) FROM drive_evidence').fetchone()[0]
    if existing > 0:
        print(f'Clearing {existing} previous scan results...')
        conn.execute('DELETE FROM drive_evidence')
        conn.commit()

    drives = [
        (r'C:\Users\andre', 10000, SKIP_DIRS_ANDRE),
        (r'D:\\', 8000, SKIP_DIRS),
        (r'F:\\', 8000, SKIP_DIRS),
        (r'G:\\', 8000, SKIP_DIRS),
        (r'H:\\', 8000, SKIP_DIRS),
        (r'I:\\', 10000, SKIP_DIRS),
    ]

    total = 0
    for root, max_files, skip in drives:
        if os.path.exists(root):
            print(f'\nScanning {root} (max {max_files} files)...')
            found = scan_drive(root, conn, max_files, skip)
            total += found
        else:
            print(f'  {root}: NOT MOUNTED — skipping')

    conn.commit()
    print(f'\n--- SCAN COMPLETE: {total} relevant files found ---')

    print_summary(conn)
    conn.close()
    print(f'\nFinished: {datetime.now().isoformat()}')


if __name__ == '__main__':
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')
    main()
