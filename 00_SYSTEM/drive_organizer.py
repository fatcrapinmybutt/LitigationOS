"""
LitigationOS Drive Organizer Engine v1.0
=========================================
Paired with deep_scanner.py — reads its SQLite manifests and executes:
  Stage 1: Cross-drive dedup analysis
  Stage 2: Smart consolidation plan (map to 00-99 master structure)
  Stage 3: Trash cleanup manifest
  Stage 4: Execute moves with rollback
  Stage 5: Legal document ingestion into master_index.db
  Stage 6: Verification & report

Usage:
  python drive_organizer.py plan       # Stages 1-3: analyze only, no moves
  python drive_organizer.py execute    # Stage 4: execute the plan
  python drive_organizer.py ingest     # Stage 5: ingest legal docs
  python drive_organizer.py verify     # Stage 6: verify everything
  python drive_organizer.py all        # Stages 1-6 sequentially

Reads:  C:\\Users\\andre\\LitigationOS\\00_SYSTEM\\manifests\\drive_*_manifest.db
Writes: C:\\Users\\andre\\LitigationOS\\00_SYSTEM\\manifests\\consolidation_plan.db
        C:\\Users\\andre\\LitigationOS\\00_SYSTEM\\manifests\\rollback.db
"""

import os, sys, json, shutil, hashlib, sqlite3, time, glob as globmod
from pathlib import Path
from collections import defaultdict, Counter
from datetime import datetime

MASTER_ROOT = r"C:\Users\andre\LitigationOS"
MANIFEST_DIR = os.path.join(MASTER_ROOT, "00_SYSTEM", "manifests")
PLAN_DB = os.path.join(MANIFEST_DIR, "consolidation_plan.db")
ROLLBACK_DB = os.path.join(MANIFEST_DIR, "rollback.db")
MASTER_INDEX = os.path.join(MASTER_ROOT, "00_SYSTEM", "pipeline", "agents", "master_index.db")

# ─── MASTER DIRECTORY SCHEMA ───
# Maps content categories to their correct home in the 00-99 structure
CATEGORY_TO_DIR = {
    # Source code & pipeline
    'source_code':       '00_SYSTEM',
    'config':            '00_SYSTEM',
    'script':            '00_SYSTEM',
    'litigation_code':   '00_SYSTEM',
    
    # Legal documents by type
    'document_pdf':      '03_LEGAL_DOCS',
    'document_office':   '03_LEGAL_DOCS',
    'text':              '03_LEGAL_DOCS',
    
    # Evidence
    'image':             '04_EVIDENCE',
    'audio':             '04_EVIDENCE',
    'video':             '04_EVIDENCE',
    'evidence':          '04_EVIDENCE',
    
    # Databases
    'database':          '05_DATABASES',
    
    # Web apps
    'web':               '08_APPS',
    'web_app':           '08_APPS',
    
    # Archives to sort
    'archive':           '10_ARCHIVES',
    
    # Media (non-evidence)
    'media_photos':      '11_MEDIA',
    
    # Trash
    'trash':             '98_TRASH',
    'temp_trash':        '98_TRASH',
    'empty':             '98_TRASH',
    
    # Uncategorized
    'other':             '97_UNSORTED',
    'uncategorized':     '97_UNSORTED',
    'binary_executable': '97_UNSORTED',
}

# Legal relevance thresholds
LEGAL_HIGH = 20    # Definitely case-related
LEGAL_MED = 10     # Probably case-related
LEGAL_LOW = 5      # Maybe case-related


def load_all_manifests():
    """Load all drive manifest DBs into a unified view."""
    manifest_files = globmod.glob(os.path.join(MANIFEST_DIR, "drive_*_manifest.db"))
    if not manifest_files:
        print("  ❌ No manifest DBs found. Run deep_scanner.py first.")
        return None
    
    print(f"  Loading {len(manifest_files)} manifest(s)...")
    all_files = []
    for mf in manifest_files:
        drive = os.path.basename(mf).replace("drive_", "").replace("_manifest.db", "")
        try:
            conn = sqlite3.connect(mf)
            conn.row_factory = sqlite3.Row
            rows = conn.execute("SELECT * FROM files").fetchall()
            for r in rows:
                rec = dict(r)
                rec['source_drive'] = drive
                all_files.append(rec)
            print(f"    {drive}: — {len(rows):,} files loaded")
            conn.close()
        except Exception as e:
            print(f"    {drive}: — ERROR: {e}")
    
    return all_files


def init_plan_db():
    """Create the consolidation plan database."""
    conn = sqlite3.connect(PLAN_DB)
    c = conn.cursor()
    c.executescript('''
        DROP TABLE IF EXISTS dedup_groups;
        DROP TABLE IF EXISTS move_plan;
        DROP TABLE IF EXISTS trash_plan;
        DROP TABLE IF EXISTS ingest_plan;
        DROP TABLE IF EXISTS stats;
        
        CREATE TABLE dedup_groups (
            group_id INTEGER,
            sha256 TEXT,
            file_count INTEGER,
            total_size_bytes INTEGER,
            keep_path TEXT,
            keep_reason TEXT
        );
        
        CREATE TABLE move_plan (
            id INTEGER PRIMARY KEY,
            source_path TEXT NOT NULL,
            dest_path TEXT NOT NULL,
            source_drive TEXT,
            size_bytes INTEGER,
            category TEXT,
            legal_score INTEGER,
            action TEXT DEFAULT 'move',
            status TEXT DEFAULT 'pending',
            reason TEXT
        );
        
        CREATE TABLE trash_plan (
            id INTEGER PRIMARY KEY,
            path TEXT NOT NULL,
            size_bytes INTEGER,
            reason TEXT,
            status TEXT DEFAULT 'pending'
        );
        
        CREATE TABLE ingest_plan (
            id INTEGER PRIMARY KEY,
            path TEXT NOT NULL,
            legal_score INTEGER,
            legal_signals TEXT,
            category TEXT,
            case_lane TEXT,
            status TEXT DEFAULT 'pending'
        );
        
        CREATE TABLE stats (
            key TEXT PRIMARY KEY,
            value TEXT
        );
        
        CREATE INDEX idx_move_status ON move_plan(status);
        CREATE INDEX idx_trash_status ON trash_plan(status);
        CREATE INDEX idx_ingest_status ON ingest_plan(status);
    ''')
    conn.commit()
    return conn


def init_rollback_db():
    """Create rollback log."""
    conn = sqlite3.connect(ROLLBACK_DB)
    c = conn.cursor()
    c.executescript('''
        CREATE TABLE IF NOT EXISTS operations (
            id INTEGER PRIMARY KEY,
            timestamp TEXT,
            action TEXT,
            source_path TEXT,
            dest_path TEXT,
            sha256_before TEXT,
            success BOOLEAN,
            error TEXT
        );
    ''')
    conn.commit()
    return conn


# ══════════════════════════════════════════════════════════════
#  STAGE 1: Cross-Drive Dedup Analysis
# ══════════════════════════════════════════════════════════════
def stage1_dedup(all_files, plan_conn):
    """Find duplicates across all drives by SHA256."""
    print(f"\n{'═'*70}")
    print(f"  STAGE 1: Cross-Drive Duplicate Analysis")
    print(f"{'═'*70}")
    
    # Group by SHA256
    by_hash = defaultdict(list)
    for f in all_files:
        if f.get('sha256_1mb') and f['size_bytes'] > 0:
            by_hash[f['sha256_1mb']].append(f)
    
    dupe_groups = {h: files for h, files in by_hash.items() if len(files) > 1}
    
    total_waste = 0
    group_id = 0
    cursor = plan_conn.cursor()
    
    for sha, files in sorted(dupe_groups.items(), key=lambda x: sum(f['size_bytes'] for f in x[1]), reverse=True):
        group_id += 1
        
        # Decide which to KEEP: prefer C:\LitigationOS, then newest, then largest
        def keep_score(f):
            score = 0
            path = f['path'].lower()
            if r'c:\users\andre\litigationos' in path:
                score += 1000  # Strong preference for master location
            if '00_system' in path:
                score += 500
            if '99_archive' not in path and '98_trash' not in path:
                score += 100
            # Prefer files with higher legal scores
            score += (f.get('legal_score', 0) or 0)
            return score
        
        files_sorted = sorted(files, key=keep_score, reverse=True)
        keep = files_sorted[0]
        
        group_size = sum(f['size_bytes'] for f in files)
        waste = group_size - keep['size_bytes']
        total_waste += waste
        
        cursor.execute('''INSERT INTO dedup_groups 
            (group_id, sha256, file_count, total_size_bytes, keep_path, keep_reason)
            VALUES (?,?,?,?,?,?)''',
            (group_id, sha, len(files), group_size, keep['path'],
             f"score={keep_score(keep)}, drive={keep.get('source_drive','')}"))
    
    plan_conn.commit()
    
    print(f"  Files with hashes:     {len(by_hash):,}")
    print(f"  Duplicate groups:      {len(dupe_groups):,}")
    print(f"  Total duplicate files: {sum(len(v) for v in dupe_groups.values()):,}")
    print(f"  Wasted space:          {total_waste / (1024**3):.2f} GB")
    
    cursor.execute("INSERT OR REPLACE INTO stats VALUES ('dedup_groups', ?)", (str(len(dupe_groups)),))
    cursor.execute("INSERT OR REPLACE INTO stats VALUES ('dedup_waste_bytes', ?)", (str(total_waste),))
    plan_conn.commit()
    
    # Show top 10 biggest dupe groups
    print(f"\n  Top duplicate groups by wasted space:")
    cursor.execute('''SELECT group_id, sha256, file_count, total_size_bytes, keep_path 
        FROM dedup_groups ORDER BY total_size_bytes DESC LIMIT 10''')
    for gid, sha, cnt, tsize, kpath in cursor.fetchall():
        print(f"    Group {gid}: {cnt} copies, {tsize/1048576:.1f}MB total — keeping: {kpath}")
    
    return dupe_groups


# ══════════════════════════════════════════════════════════════
#  STAGE 2: Smart Consolidation Plan
# ══════════════════════════════════════════════════════════════
def stage2_consolidation(all_files, dupe_groups, plan_conn):
    """Map every non-C-master file to its correct destination."""
    print(f"\n{'═'*70}")
    print(f"  STAGE 2: Smart Consolidation Plan")
    print(f"{'═'*70}")
    
    cursor = plan_conn.cursor()
    master_prefix = r"C:\Users\andre\LitigationOS".lower()
    
    # Build set of files to SKIP (duplicates we're not keeping)
    dupe_skip = set()
    for sha, files in dupe_groups.items():
        def keep_score(f):
            score = 0
            path = f['path'].lower()
            if master_prefix in path: score += 1000
            if '00_system' in path: score += 500
            score += (f.get('legal_score', 0) or 0)
            return score
        
        files_sorted = sorted(files, key=keep_score, reverse=True)
        keep_path = files_sorted[0]['path']
        for f in files_sorted[1:]:
            dupe_skip.add(f['path'])
    
    move_count = 0
    skip_count = 0
    already_home = 0
    
    for f in all_files:
        path = f['path']
        
        # Already in master?
        if path.lower().startswith(master_prefix):
            already_home += 1
            continue
        
        # Duplicate we're discarding?
        if path in dupe_skip:
            skip_count += 1
            continue
        
        # Determine destination directory
        category = f.get('category', 'other')
        legal_score = f.get('legal_score', 0) or 0
        
        # High legal relevance overrides category
        if legal_score >= LEGAL_HIGH:
            if category in ('image', 'audio', 'video'):
                dest_dir = '04_EVIDENCE'
            else:
                dest_dir = '03_LEGAL_DOCS'
        else:
            dest_dir = CATEGORY_TO_DIR.get(category, '97_UNSORTED')
        
        # Build destination path preserving some structure
        source_drive = f.get('source_drive', 'X')
        # Preserve relative path from drive root, prefixed by source drive
        rel_path = path
        drive_root = f"{source_drive}:\\"
        if rel_path.lower().startswith(drive_root.lower()):
            rel_path = rel_path[len(drive_root):]
        
        dest_path = os.path.join(MASTER_ROOT, dest_dir, f"from_{source_drive}", rel_path)
        
        cursor.execute('''INSERT INTO move_plan 
            (source_path, dest_path, source_drive, size_bytes, category, legal_score, action, reason)
            VALUES (?,?,?,?,?,?,?,?)''',
            (path, dest_path, source_drive, f.get('size_bytes', 0),
             category, legal_score, 'move',
             f"cat={category}, legal={legal_score}"))
        move_count += 1
    
    plan_conn.commit()
    
    # Size summary
    cursor.execute("SELECT SUM(size_bytes) FROM move_plan WHERE status='pending'")
    total_move_size = cursor.fetchone()[0] or 0
    
    print(f"  Already in master:  {already_home:,}")
    print(f"  Duplicate (skip):   {skip_count:,}")
    print(f"  Files to move:      {move_count:,}")
    print(f"  Data to move:       {total_move_size / (1024**3):.2f} GB")
    
    # Breakdown by destination
    print(f"\n  Move plan by destination:")
    cursor.execute('''SELECT 
        SUBSTR(dest_path, 1, INSTR(SUBSTR(dest_path, LENGTH(?)+2), '\') + LENGTH(?)) as dest_dir,
        COUNT(*) as cnt, SUM(size_bytes) as total
        FROM move_plan WHERE status='pending'
        GROUP BY dest_dir ORDER BY total DESC''', (MASTER_ROOT, MASTER_ROOT))
    for dest, cnt, total in cursor.fetchall():
        print(f"    {dest}: {cnt:,} files ({(total or 0)/1048576:.1f} MB)")
    
    cursor.execute("INSERT OR REPLACE INTO stats VALUES ('move_count', ?)", (str(move_count),))
    cursor.execute("INSERT OR REPLACE INTO stats VALUES ('move_size_bytes', ?)", (str(total_move_size),))
    plan_conn.commit()


# ══════════════════════════════════════════════════════════════
#  STAGE 3: Trash Cleanup Plan
# ══════════════════════════════════════════════════════════════
def stage3_trash(all_files, plan_conn):
    """Identify all trash/empty/corrupt files for cleanup."""
    print(f"\n{'═'*70}")
    print(f"  STAGE 3: Trash Cleanup Plan")
    print(f"{'═'*70}")
    
    cursor = plan_conn.cursor()
    
    trash_count = 0
    trash_size = 0
    reasons = Counter()
    
    for f in all_files:
        reason = None
        if f.get('is_empty'):
            reason = 'empty_file'
        elif f.get('is_trash'):
            reason = 'trash_file'
        elif f.get('is_corrupt'):
            reason = 'corrupt_file'
        elif f.get('category') in ('trash', 'temp_trash'):
            reason = f['category']
        elif f.get('filename', '').lower() in ('thumbs.db', 'desktop.ini', '.ds_store'):
            reason = 'system_junk'
        elif f.get('extension') in ('.pyc', '.pyo'):
            reason = 'python_cache'
        
        if reason:
            cursor.execute('''INSERT INTO trash_plan (path, size_bytes, reason)
                VALUES (?,?,?)''', (f['path'], f.get('size_bytes', 0), reason))
            trash_count += 1
            trash_size += f.get('size_bytes', 0)
            reasons[reason] += 1
    
    plan_conn.commit()
    
    print(f"  Total trash files:   {trash_count:,}")
    print(f"  Recoverable space:   {trash_size / 1048576:.1f} MB")
    print(f"\n  Breakdown:")
    for reason, count in reasons.most_common():
        print(f"    {reason:25s}: {count:,}")
    
    cursor.execute("INSERT OR REPLACE INTO stats VALUES ('trash_count', ?)", (str(trash_count),))
    cursor.execute("INSERT OR REPLACE INTO stats VALUES ('trash_size_bytes', ?)", (str(trash_size),))
    plan_conn.commit()


# ══════════════════════════════════════════════════════════════
#  STAGE 4: Execute Moves (with rollback)
# ══════════════════════════════════════════════════════════════
def stage4_execute(plan_conn):
    """Execute the consolidation plan with full rollback logging."""
    print(f"\n{'═'*70}")
    print(f"  STAGE 4: Executing Consolidation Plan")
    print(f"{'═'*70}")
    
    rollback_conn = init_rollback_db()
    cursor = plan_conn.cursor()
    rb_cursor = rollback_conn.cursor()
    
    cursor.execute("SELECT COUNT(*) FROM move_plan WHERE status='pending'")
    total = cursor.fetchone()[0]
    print(f"  {total:,} moves to execute")
    
    if total == 0:
        print("  Nothing to move.")
        return
    
    # Confirm
    print(f"\n  ⚠️  This will MOVE {total:,} files.")
    print(f"  All operations logged to: {ROLLBACK_DB}")
    
    success = 0
    failed = 0
    batch_size = 100
    offset = 0
    
    while True:
        cursor.execute('''SELECT id, source_path, dest_path FROM move_plan 
            WHERE status='pending' LIMIT ?''', (batch_size,))
        rows = cursor.fetchall()
        if not rows:
            break
        
        for row_id, src, dst in rows:
            try:
                # Create destination directory
                dst_dir = os.path.dirname(dst)
                os.makedirs(dst_dir, exist_ok=True)
                
                # Move file
                shutil.move(src, dst)
                
                # Log to rollback
                rb_cursor.execute('''INSERT INTO operations 
                    (timestamp, action, source_path, dest_path, success)
                    VALUES (?,?,?,?,?)''',
                    (datetime.now().isoformat(), 'move', src, dst, True))
                
                cursor.execute("UPDATE move_plan SET status='done' WHERE id=?", (row_id,))
                success += 1
                
            except Exception as e:
                rb_cursor.execute('''INSERT INTO operations 
                    (timestamp, action, source_path, dest_path, success, error)
                    VALUES (?,?,?,?,?,?)''',
                    (datetime.now().isoformat(), 'move', src, dst, False, str(e)))
                cursor.execute("UPDATE move_plan SET status='failed' WHERE id=?", (row_id,))
                failed += 1
        
        plan_conn.commit()
        rollback_conn.commit()
        print(f"    ... {success + failed:,}/{total:,} processed ({success} ok, {failed} failed)")
    
    print(f"\n  ✅ Complete: {success:,} moved, {failed:,} failed")
    rollback_conn.close()


# ══════════════════════════════════════════════════════════════
#  STAGE 5: Legal Document Ingestion
# ══════════════════════════════════════════════════════════════
def stage5_ingest(all_files, plan_conn):
    """Identify legal documents for ingestion into master_index.db."""
    print(f"\n{'═'*70}")
    print(f"  STAGE 5: Legal Document Ingestion Plan")
    print(f"{'═'*70}")
    
    cursor = plan_conn.cursor()
    
    # Lane detection patterns
    LANE_A = ['custody', 'parenting', 'child', 'foc', 'friend of court', 'visitation',
              'mcneill', '2024-001507', 'domestic', 'family']
    LANE_B = ['housing', 'habitability', 'shady', 'mold', 'lead', 'repair', 'tenant',
              'hoopes', '2023-5907', 'landlord', 'lease', 'eviction']
    LANE_C = ['judicial', 'jtc', 'misconduct', 'disqualif', 'appeal', 'coa',
              '2025-002760', 'convergence', '1983', 'civil rights']
    LANE_D = ['ppo', 'protection order', 'contempt', 'bond', 'restrain',
              'no contact', 'stalking', 'harassment', 'mcl 600.2950',
              'mcr 3.706', 'domestic violence']
    LANE_E = ['judicial', 'jtc', 'misconduct', 'disqualif', 'bias', 'canon',
              'recus', 'ex parte', 'mcneill', 'improper', 'code of conduct']
    LANE_F = ['appeal', 'appellate', 'coa', 'msc', 'supreme court',
              'interlocutory', 'mcr 7.', 'standard of review', 'de novo',
              'leave to appeal', 'superintending']
    
    ingest_count = 0
    lanes = Counter()
    
    for f in all_files:
        legal_score = f.get('legal_score', 0) or 0
        if legal_score < LEGAL_LOW:
            continue
        
        # Only ingest document types
        cat = f.get('category', '')
        if cat not in ('document_pdf', 'document_office', 'text', 'source_code', 'config'):
            if legal_score < LEGAL_HIGH:
                continue
        
        # Detect case lane
        path_lower = f['path'].lower()
        fname_lower = f.get('filename', '').lower()
        combined = path_lower + ' ' + fname_lower
        signals = json.loads(f['legal_signals']) if f.get('legal_signals') else []
        
        lane_scores = {'A': 0, 'B': 0, 'C': 0, 'D': 0, 'E': 0, 'F': 0}
        for kw in LANE_A:
            if kw in combined: lane_scores['A'] += 1
        for kw in LANE_B:
            if kw in combined: lane_scores['B'] += 1
        for kw in LANE_C:
            if kw in combined: lane_scores['C'] += 1
        for kw in LANE_D:
            if kw in combined: lane_scores['D'] += 1
        for kw in LANE_E:
            if kw in combined: lane_scores['E'] += 1
        for kw in LANE_F:
            if kw in combined: lane_scores['F'] += 1
        
        if 'family_law' in signals: lane_scores['A'] += 3
        if 'housing' in signals: lane_scores['B'] += 3
        if 'judicial' in signals or 'appellate' in signals: lane_scores['C'] += 3
        if 'ppo' in signals or 'protection' in signals: lane_scores['D'] += 3
        if 'judicial' in signals or 'misconduct' in signals: lane_scores['E'] += 3
        if 'appellate' in signals or 'appeal' in signals: lane_scores['F'] += 3
        
        best_lane = max(lane_scores, key=lane_scores.get)
        if lane_scores[best_lane] == 0:
            best_lane = 'UNKNOWN'
        
        cursor.execute('''INSERT INTO ingest_plan 
            (path, legal_score, legal_signals, category, case_lane)
            VALUES (?,?,?,?,?)''',
            (f['path'], legal_score, f.get('legal_signals'), cat, best_lane))
        ingest_count += 1
        lanes[best_lane] += 1
    
    plan_conn.commit()
    
    print(f"  Legal files for ingestion: {ingest_count:,}")
    print(f"  By case lane:")
    for lane, count in lanes.most_common():
        label = {'A': 'Custody (McNeill)', 'B': 'Housing (Hoopes)', 
                 'C': 'Convergence/JTC', 'D': 'PPO/Protection',
                 'E': 'Judicial Misconduct', 'F': 'Appellate',
                 'UNKNOWN': 'Unassigned'}.get(lane, lane)
        print(f"    Lane {lane} ({label}): {count:,}")
    
    cursor.execute("INSERT OR REPLACE INTO stats VALUES ('ingest_count', ?)", (str(ingest_count),))
    plan_conn.commit()


# ══════════════════════════════════════════════════════════════
#  STAGE 6: Verification
# ══════════════════════════════════════════════════════════════
def stage6_verify(plan_conn):
    """Verify consolidation results."""
    print(f"\n{'═'*70}")
    print(f"  STAGE 6: Verification & Report")
    print(f"{'═'*70}")
    
    cursor = plan_conn.cursor()
    
    # Check stats
    stats = {}
    for row in cursor.execute("SELECT key, value FROM stats"):
        stats[row[0]] = row[1]
    
    print(f"\n  📊 CONSOLIDATION SUMMARY:")
    print(f"    Duplicate groups:      {stats.get('dedup_groups', '?')}")
    print(f"    Wasted by dupes:       {int(stats.get('dedup_waste_bytes', 0)) / (1024**3):.2f} GB")
    print(f"    Files to move:         {stats.get('move_count', '?')}")
    print(f"    Data to move:          {int(stats.get('move_size_bytes', 0)) / (1024**3):.2f} GB")
    print(f"    Trash files:           {stats.get('trash_count', '?')}")
    print(f"    Trash size:            {int(stats.get('trash_size_bytes', 0)) / 1048576:.1f} MB")
    print(f"    Legal docs to ingest:  {stats.get('ingest_count', '?')}")
    
    # Verify master structure exists
    print(f"\n  📁 MASTER STRUCTURE:")
    for d in sorted(os.listdir(MASTER_ROOT)):
        full = os.path.join(MASTER_ROOT, d)
        if os.path.isdir(full):
            count = sum(1 for _ in Path(full).rglob('*') if _.is_file())
            print(f"    {d:30s} {count:>7,} files")
    
    print(f"\n  ✅ Plan database: {PLAN_DB}")
    print(f"  ✅ Query with: sqlite3 \"{PLAN_DB}\" \"SELECT * FROM stats\"")


# ══════════════════════════════════════════════════════════════
#  MAIN
# ══════════════════════════════════════════════════════════════
def main():
    mode = sys.argv[1] if len(sys.argv) > 1 else 'plan'
    
    print(f"\n{'═'*70}")
    print(f"  LITIGATIONOS DRIVE ORGANIZER ENGINE v1.0")
    print(f"  Mode: {mode}")
    print(f"  Time: {datetime.now().isoformat()}")
    print(f"{'═'*70}")
    
    if mode in ('plan', 'all'):
        all_files = load_all_manifests()
        if not all_files:
            return
        
        plan_conn = init_plan_db()
        dupe_groups = stage1_dedup(all_files, plan_conn)
        stage2_consolidation(all_files, dupe_groups, plan_conn)
        stage3_trash(all_files, plan_conn)
        stage5_ingest(all_files, plan_conn)
        stage6_verify(plan_conn)
        plan_conn.close()
    
    if mode == 'execute':
        plan_conn = sqlite3.connect(PLAN_DB)
        stage4_execute(plan_conn)
        plan_conn.close()
    
    if mode == 'ingest':
        all_files = load_all_manifests()
        if not all_files:
            return
        plan_conn = sqlite3.connect(PLAN_DB)
        stage5_ingest(all_files, plan_conn)
        plan_conn.close()
    
    if mode == 'verify':
        plan_conn = sqlite3.connect(PLAN_DB)
        stage6_verify(plan_conn)
        plan_conn.close()
    
    if mode == 'all':
        plan_conn = sqlite3.connect(PLAN_DB)
        stage4_execute(plan_conn)
        stage6_verify(plan_conn)
        plan_conn.close()
    
    print(f"\n{'═'*70}")
    print(f"  ORGANIZER ENGINE COMPLETE")
    print(f"{'═'*70}")


if __name__ == '__main__':
    main()
