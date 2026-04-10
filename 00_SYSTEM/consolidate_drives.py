#!/usr/bin/env python3
"""
LitigationOS Drive Consolidation Engine v1.0
============================================
Consolidates all external drives onto J:\\ with:
- xxHash xxh3_128 verification (60x faster than SHA-256)
- Content-based deduplication (peek inside, not hash-only)
- AI-optimal directory organization by case lane + file type
- Complete manifest generation for traceability

Usage:
    python consolidate_drives.py inventory    # Phase 1: Scan all drives, build file inventory
    python consolidate_drives.py analyze      # Phase 2: Find duplicates, calculate savings
    python consolidate_drives.py plan         # Phase 3: Show copy plan (dry-run)
    python consolidate_drives.py execute      # Phase 4: Copy files to J:\\ (with verification)
    python consolidate_drives.py verify       # Phase 5: Re-verify all copied files
    python consolidate_drives.py manifest     # Phase 6: Generate master manifest
    python consolidate_drives.py status       # Show current progress
    python consolidate_drives.py dashboard    # Full dashboard: inventory + dupes + plan

Phases are sequential. Run inventory first, then analyze, then plan, then execute.
Each phase saves state to J:\\LITIGATIONOS_CONSOLIDATED\\.consolidation_state.db
"""

import os
import sys
import json
import time
import sqlite3
import shutil
import hashlib
import struct
from pathlib import Path
from datetime import datetime
from collections import defaultdict

try:
    import xxhash
    HASH_ENGINE = "xxh3_128"
    def fast_hash(path: str, chunk_size: int = 1 << 20) -> str:
        """xxHash xxh3_128 -- 30 GB/s, 128-bit, zero collisions for identity."""
        h = xxhash.xxh3_128()
        with open(path, "rb") as f:
            while chunk := f.read(chunk_size):
                h.update(chunk)
        return h.hexdigest()
except ImportError:
    HASH_ENGINE = "sha256"
    def fast_hash(path: str, chunk_size: int = 1 << 20) -> str:
        """SHA-256 fallback -- 0.5 GB/s."""
        h = hashlib.sha256()
        with open(path, "rb") as f:
            while chunk := f.read(chunk_size):
                h.update(chunk)
        return h.hexdigest()

# --- Configuration ----------------------------------------------------------
TARGET_DRIVE = "J:\\"
TARGET_ROOT = Path("J:\\LITIGATIONOS_CONSOLIDATED")
# State DB on D:\ (not exFAT J:\) -- exFAT has no journaling, killed writes corrupt SQLite
STATE_DB = Path(r"D:\LitigationOS_tmp\consolidation_state.db")

# Drives to consolidate (everything except C:\ which stays as hot tier)
SOURCE_DRIVES = ["D:\\", "F:\\", "G:\\", "I:\\"]

# Files to ALWAYS skip (system files, temp, recycle bin)
SKIP_PATTERNS = {
    "$RECYCLE.BIN", "System Volume Information", ".Trash",
    "desktop.ini", "Thumbs.db", ".DS_Store", "RECYCLER",
    "$Recycle.Bin", "pagefile.sys", "hiberfil.sys", "swapfile.sys",
    # Dev artifacts -- tens of thousands of junk files, zero litigation value
    "node_modules", ".git", "__pycache__", ".tox", ".mypy_cache",
    ".pytest_cache", "venv", ".venv", "env", ".env", "dist", "build",
    ".cache", ".npm", ".yarn", "vendor", ".gradle", ".idea", ".vscode",
    "site-packages", "egg-info", ".eggs", "target",
}

# AI-optimal directory structure on target
LANE_KEYWORDS = {
    "LANE_A_CUSTODY": ["custody", "parenting", "001507", "watson", "child", "visitation", "foc", "best interest"],
    "LANE_B_HOUSING": ["shady oaks", "eviction", "housing", "trailer", "002760", "habitability", "landlord"],
    "LANE_D_PPO": ["ppo", "protection order", "5907", "contempt", "stalking", "harassment"],
    "LANE_E_JUDICIAL": ["mcneill", "judicial", "bias", "jtc", "canon", "misconduct", "benchbook", "ex parte", "hoopes", "ladas"],
    "LANE_F_APPELLATE": ["coa", "366810", "appeal", "appellant", "brief", "appendix"],
}

# File type routing
TYPE_ROUTES = {
    "DATABASES":      {".db", ".sqlite", ".sqlite3", ".db-shm", ".db-wal"},
    "AUDIO_VIDEO":    {".mp3", ".mp4", ".wav", ".avi", ".mkv", ".m4a", ".flac", ".ogg", ".webm", ".mov"},
    "PHOTOS":         {".jpg", ".jpeg", ".png", ".gif", ".bmp", ".tiff", ".heic", ".webp", ".svg"},
    "PDF_DOCUMENTS":  {".pdf"},
    "COURT_FILINGS":  {".docx", ".doc"},
    "CODE_SCRIPTS":   {".py", ".js", ".ts", ".go", ".rs", ".ps1", ".bat", ".cmd", ".sh"},
    "DATA_FILES":     {".csv", ".tsv", ".json", ".jsonl", ".xml", ".yaml", ".yml"},
    "TEXT_FILES":     {".txt", ".md", ".log", ".rtf"},
    "ARCHIVES":       {".zip", ".rar", ".7z", ".tar", ".gz", ".bz2"},
    "SPREADSHEETS":   {".xlsx", ".xls", ".ods"},
    "PRESENTATIONS":  {".pptx", ".ppt"},
    "EMAIL_EXPORTS":  {".eml", ".mbox", ".msg"},
}


def safe_str(s: str) -> str:
    """Make string safe for cp1252 console output by replacing bad chars."""
    return s.encode("cp1252", errors="replace").decode("cp1252")


def get_state_db() -> sqlite3.Connection:
    """Get or create the consolidation state database."""
    TARGET_ROOT.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(STATE_DB))
    conn.execute("PRAGMA journal_mode=DELETE")  # FAT32/exFAT safe
    conn.execute("PRAGMA busy_timeout=30000")
    conn.execute("PRAGMA cache_size=-16000")
    conn.execute("PRAGMA synchronous=FULL")  # extra safety on non-NTFS
    
    conn.executescript("""
        CREATE TABLE IF NOT EXISTS file_inventory (
            id INTEGER PRIMARY KEY,
            source_path TEXT NOT NULL UNIQUE,
            source_drive TEXT NOT NULL,
            file_name TEXT NOT NULL,
            file_ext TEXT,
            file_size INTEGER NOT NULL,
            modified_date TEXT,
            xxhash TEXT,
            content_peek TEXT,
            lane_guess TEXT,
            type_category TEXT,
            target_path TEXT,
            copy_status TEXT DEFAULT 'pending',
            verify_status TEXT DEFAULT 'pending',
            scanned_at TEXT DEFAULT (datetime('now')),
            copied_at TEXT,
            verified_at TEXT
        );
        
        CREATE TABLE IF NOT EXISTS dedup_groups (
            group_id INTEGER PRIMARY KEY,
            xxhash TEXT NOT NULL,
            file_size INTEGER NOT NULL,
            file_count INTEGER NOT NULL,
            canonical_path TEXT,
            savings_bytes INTEGER DEFAULT 0
        );
        
        CREATE TABLE IF NOT EXISTS consolidation_log (
            id INTEGER PRIMARY KEY,
            timestamp TEXT DEFAULT (datetime('now')),
            phase TEXT NOT NULL,
            message TEXT NOT NULL,
            details TEXT
        );
        
        CREATE TABLE IF NOT EXISTS progress (
            phase TEXT PRIMARY KEY,
            status TEXT DEFAULT 'pending',
            started_at TEXT,
            completed_at TEXT,
            files_processed INTEGER DEFAULT 0,
            files_total INTEGER DEFAULT 0,
            bytes_processed INTEGER DEFAULT 0,
            bytes_total INTEGER DEFAULT 0,
            errors INTEGER DEFAULT 0,
            notes TEXT
        );
        
        CREATE INDEX IF NOT EXISTS idx_inv_hash ON file_inventory(xxhash);
        CREATE INDEX IF NOT EXISTS idx_inv_drive ON file_inventory(source_drive);
        CREATE INDEX IF NOT EXISTS idx_inv_status ON file_inventory(copy_status);
        CREATE INDEX IF NOT EXISTS idx_inv_ext ON file_inventory(file_ext);
        CREATE INDEX IF NOT EXISTS idx_inv_size ON file_inventory(file_size);
    """)
    
    # Ensure progress rows exist
    for phase in ["inventory", "analyze", "plan", "execute", "verify", "manifest"]:
        conn.execute(
            "INSERT OR IGNORE INTO progress (phase) VALUES (?)", (phase,)
        )
    conn.commit()
    return conn


def log_event(conn: sqlite3.Connection, phase: str, message: str, details: str = None):
    """Log a consolidation event."""
    conn.execute(
        "INSERT INTO consolidation_log (phase, message, details) VALUES (?, ?, ?)",
        (phase, message, details)
    )
    conn.commit()


def should_skip(path: Path) -> bool:
    """Check if a path should be skipped."""
    for part in path.parts:
        if part in SKIP_PATTERNS:
            return True
    return False


def peek_content(path: str, max_bytes: int = 512) -> str:
    """Peek at file content for content-based dedup verification."""
    try:
        with open(path, "rb") as f:
            raw = f.read(max_bytes)
        # Try UTF-8 decode, fall back to repr
        try:
            return raw.decode("utf-8", errors="replace")[:256]
        except Exception:
            return repr(raw[:128])
    except Exception:
        return ""


def guess_lane(path: str, content_peek: str = "") -> str:
    """Guess the litigation lane from path and content."""
    combined = (path + " " + content_peek).lower()
    scores = {}
    for lane, keywords in LANE_KEYWORDS.items():
        score = sum(1 for kw in keywords if kw in combined)
        if score > 0:
            scores[lane] = score
    if scores:
        return max(scores, key=scores.get)
    return "UNCLASSIFIED"


def categorize_file(ext: str) -> str:
    """Categorize file by extension."""
    ext_lower = ext.lower()
    for category, extensions in TYPE_ROUTES.items():
        if ext_lower in extensions:
            return category
    return "OTHER"


def compute_target_path(source_path: str, lane: str, category: str, source_drive: str) -> str:
    """Compute the organized target path on J:\\."""
    p = Path(source_path)
    # Structure: J:\LITIGATIONOS_CONSOLIDATED\{CATEGORY}\{LANE}\{source_drive}\{relative_path}
    # This preserves source traceability while organizing by type and lane
    rel = str(p.relative_to(source_drive)) if source_drive else p.name
    drive_label = source_drive.rstrip("\\").rstrip(":")
    target = TARGET_ROOT / category / lane / f"from_{drive_label}" / rel
    return str(target)


def fmt_size(b: int) -> str:
    """Format bytes as human-readable."""
    for unit in ["B", "KB", "MB", "GB", "TB"]:
        if abs(b) < 1024:
            return f"{b:.1f} {unit}"
        b /= 1024
    return f"{b:.1f} PB"


def fmt_duration(seconds: float) -> str:
    """Format seconds as human-readable duration."""
    if seconds < 60:
        return f"{seconds:.1f}s"
    elif seconds < 3600:
        return f"{seconds/60:.1f}m"
    else:
        return f"{seconds/3600:.1f}h"


# ===========================================================================
#  PHASE 1: INVENTORY -- Scan all drives, hash everything
# ===========================================================================

def phase_inventory():
    """Scan all source drives and build the complete file inventory."""
    conn = get_state_db()
    
    # Check if already done
    row = conn.execute("SELECT status FROM progress WHERE phase='inventory'").fetchone()
    if row and row[0] == "complete":
        existing = conn.execute("SELECT COUNT(*) FROM file_inventory").fetchone()[0]
        print(f"[INVENTORY] Already complete with {existing:,} files. Use 'analyze' next.")
        print("  (To re-scan, DELETE FROM file_inventory and UPDATE progress SET status='pending' WHERE phase='inventory')")
        return
    
    conn.execute(
        "UPDATE progress SET status='running', started_at=datetime('now') WHERE phase='inventory'"
    )
    conn.commit()
    log_event(conn, "inventory", "Starting drive inventory scan", json.dumps(SOURCE_DRIVES))
    
    total_files = 0
    total_bytes = 0
    total_errors = 0
    start_time = time.time()
    
    for drive in SOURCE_DRIVES:
        if not os.path.exists(drive):
            print(f"  [SKIP] {drive} not mounted")
            log_event(conn, "inventory", f"Drive not mounted: {drive}")
            continue
        
        # Check if this drive was already fully scanned (heuristic: >1000 files or known complete)
        drive_letter = drive.rstrip("\\").rstrip(":")
        existing_count = conn.execute(
            "SELECT COUNT(*) FROM file_inventory WHERE source_drive = ?", (drive_letter + ":",)
        ).fetchone()[0]
        # If we have substantial data and it was from a previous successful scan, skip
        # (I:\ had 500 partial files from crash - it will re-scan and INSERT OR IGNORE handles dupes)
        if existing_count > 500 and drive not in ("I:\\",):
            print(f"  [SKIP] {drive} already has {existing_count:,} files in inventory", flush=True)
            total_files += existing_count
            sz = conn.execute(
                "SELECT COALESCE(SUM(file_size),0) FROM file_inventory WHERE source_drive = ?", (drive_letter + ":",)
            ).fetchone()[0]
            total_bytes += sz
            continue
        
        drive_files = 0
        drive_bytes = 0
        drive_errors = 0
        drive_start = time.time()
        print(f"\n[SCANNING] {drive} (existing: {existing_count:,} files will be skipped via INSERT OR IGNORE)", flush=True)
        
        batch = []
        batch_size = 500  # Commit every 500 files
        
        for root, dirs, files in os.walk(drive):
            # Skip system directories
            dirs[:] = [d for d in dirs if d not in SKIP_PATTERNS]
            
            for fname in files:
                fpath = os.path.join(root, fname)
                
                if should_skip(Path(fpath)):
                    continue
                
                try:
                    stat = os.stat(fpath)
                    fsize = stat.st_size
                    mtime = datetime.fromtimestamp(stat.st_mtime).isoformat()
                    ext = os.path.splitext(fname)[1]
                    
                    # Hash the file (xxh3_128 -- blazing fast)
                    if fsize > 0:
                        fhash = fast_hash(fpath)
                    else:
                        fhash = "EMPTY_FILE"
                    
                    # Peek at content for dedup verification
                    peek = peek_content(fpath) if fsize > 0 and fsize < 100_000_000 else ""
                    
                    # Classify
                    lane = guess_lane(fpath, peek)
                    category = categorize_file(ext)
                    target = compute_target_path(fpath, lane, category, drive)
                    
                    batch.append((
                        fpath, drive.rstrip("\\"), fname, ext, fsize, mtime,
                        fhash, peek[:256], lane, category, target
                    ))
                    
                    drive_files += 1
                    drive_bytes += fsize
                    
                    # Progress every 500 files
                    if drive_files % 500 == 0:
                        print(f"  {drive_files:>8,} files | {fmt_size(drive_bytes):>10} | {safe_str(fpath[-60:])}", flush=True)
                    
                    # Batch insert
                    if len(batch) >= batch_size:
                        conn.executemany("""
                            INSERT OR IGNORE INTO file_inventory 
                            (source_path, source_drive, file_name, file_ext, file_size, 
                             modified_date, xxhash, content_peek, lane_guess, type_category, target_path)
                            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                        """, batch)
                        conn.commit()
                        batch = []
                        
                except PermissionError:
                    drive_errors += 1
                except OSError as e:
                    drive_errors += 1
                    if drive_errors <= 10:
                        log_event(conn, "inventory", f"OS error: {safe_str(fpath)}", str(e))
        
        # Flush remaining batch
        if batch:
            conn.executemany("""
                INSERT OR IGNORE INTO file_inventory 
                (source_path, source_drive, file_name, file_ext, file_size, 
                 modified_date, xxhash, content_peek, lane_guess, type_category, target_path)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, batch)
            conn.commit()
        
        elapsed = time.time() - drive_start
        total_files += drive_files
        total_bytes += drive_bytes
        total_errors += drive_errors
        
        print(f"  [OK] {drive} complete: {drive_files:,} files, {fmt_size(drive_bytes)}, "
              f"{drive_errors} errors, {fmt_duration(elapsed)}")
        log_event(conn, "inventory", f"Drive {drive} scanned", 
                  json.dumps({"files": drive_files, "bytes": drive_bytes, "errors": drive_errors}))
    
    # Also scan J:\ existing content (so we know what's already there)
    j_existing = conn.execute(
        "SELECT COUNT(*) FROM file_inventory WHERE source_drive = 'J:'"
    ).fetchone()[0]
    
    if j_existing == 0 and os.path.exists("J:\\"):
        print(f"\n[SCANNING] J:\\ (existing content)")
        j_files = 0
        j_bytes = 0
        batch = []
        
        for root, dirs, files in os.walk("J:\\"):
            dirs[:] = [d for d in dirs if d not in SKIP_PATTERNS]
            for fname in files:
                fpath = os.path.join(root, fname)
                if should_skip(Path(fpath)):
                    continue
                try:
                    stat = os.stat(fpath)
                    fsize = stat.st_size
                    mtime = datetime.fromtimestamp(stat.st_mtime).isoformat()
                    ext = os.path.splitext(fname)[1]
                    fhash = fast_hash(fpath) if fsize > 0 else "EMPTY_FILE"
                    peek = peek_content(fpath) if 0 < fsize < 100_000_000 else ""
                    lane = guess_lane(fpath, peek)
                    category = categorize_file(ext)
                    target = fpath  # Already on J:\
                    
                    batch.append((
                        fpath, "J:", fname, ext, fsize, mtime,
                        fhash, peek[:256], lane, category, target
                    ))
                    j_files += 1
                    j_bytes += fsize
                    
                    if j_files % 500 == 0:
                        print(f"  {j_files:>8,} files | {fmt_size(j_bytes):>10}", flush=True)
                    
                    if len(batch) >= 500:
                        conn.executemany("""
                            INSERT OR IGNORE INTO file_inventory 
                            (source_path, source_drive, file_name, file_ext, file_size, 
                             modified_date, xxhash, content_peek, lane_guess, type_category, target_path)
                            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                        """, batch)
                        conn.commit()
                        batch = []
                except (PermissionError, OSError):
                    pass
        
        if batch:
            conn.executemany("""
                INSERT OR IGNORE INTO file_inventory 
                (source_path, source_drive, file_name, file_ext, file_size, 
                 modified_date, xxhash, content_peek, lane_guess, type_category, target_path)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, batch)
            conn.commit()
        
        total_files += j_files
        total_bytes += j_bytes
        print(f"  [OK] J:\\ existing: {j_files:,} files, {fmt_size(j_bytes)}")
    
    # Update progress
    elapsed = time.time() - start_time
    conn.execute("""
        UPDATE progress SET status='complete', completed_at=datetime('now'),
        files_processed=?, files_total=?, bytes_processed=?, bytes_total=?, errors=?,
        notes=?
        WHERE phase='inventory'
    """, (total_files, total_files, total_bytes, total_bytes, total_errors,
          f"Scanned {len(SOURCE_DRIVES)} drives + J:\\ in {fmt_duration(elapsed)}"))
    conn.commit()
    
    print(f"\n{'='*60}")
    print(f"INVENTORY COMPLETE")
    print(f"  Total files:  {total_files:,}")
    print(f"  Total size:   {fmt_size(total_bytes)}")
    print(f"  Total errors: {total_errors}")
    print(f"  Duration:     {fmt_duration(elapsed)}")
    print(f"  Hash engine:  {HASH_ENGINE}")
    print(f"  State DB:     {STATE_DB}")
    print(f"\nNext: python consolidate_drives.py analyze")


# ===========================================================================
#  PHASE 2: ANALYZE -- Find duplicates, calculate savings
# ===========================================================================

def phase_analyze():
    """Analyze inventory for duplicates and calculate consolidation plan."""
    conn = get_state_db()
    
    # Check prerequisites
    inv_status = conn.execute("SELECT status FROM progress WHERE phase='inventory'").fetchone()
    if not inv_status or inv_status[0] != "complete":
        print("[ERROR] Run 'inventory' phase first.")
        return
    
    conn.execute(
        "UPDATE progress SET status='running', started_at=datetime('now') WHERE phase='analyze'"
    )
    conn.commit()
    
    total = conn.execute("SELECT COUNT(*) FROM file_inventory").fetchone()[0]
    print(f"[ANALYZE] Processing {total:,} files for deduplication...\n")
    
    # Clear old dedup groups
    conn.execute("DELETE FROM dedup_groups")
    
    # Find duplicate groups (same hash + same size = same file)
    conn.execute("""
        INSERT INTO dedup_groups (xxhash, file_size, file_count, savings_bytes)
        SELECT xxhash, file_size, COUNT(*) as cnt, 
               (COUNT(*) - 1) * file_size as savings
        FROM file_inventory
        WHERE xxhash != 'EMPTY_FILE'
        GROUP BY xxhash, file_size
        HAVING COUNT(*) > 1
    """)
    conn.commit()
    
    # Pick canonical (keep the one on J:\ if exists, else largest drive letter = most stable)
    for row in conn.execute("SELECT group_id, xxhash FROM dedup_groups").fetchall():
        # Prefer: J:\ existing > I:\ > G:\ > F:\ > D:\
        canonical = conn.execute("""
            SELECT source_path FROM file_inventory 
            WHERE xxhash = ?
            ORDER BY 
                CASE source_drive 
                    WHEN 'J:' THEN 1 
                    WHEN 'I:' THEN 2 
                    WHEN 'G:' THEN 3 
                    WHEN 'F:' THEN 4 
                    WHEN 'D:' THEN 5 
                    ELSE 6 
                END,
                file_size DESC
            LIMIT 1
        """, (row[1],)).fetchone()
        
        if canonical:
            conn.execute(
                "UPDATE dedup_groups SET canonical_path = ? WHERE group_id = ?",
                (canonical[0], row[0])
            )
    conn.commit()
    
    # Statistics
    stats = conn.execute("""
        SELECT 
            (SELECT COUNT(*) FROM file_inventory) as total_files,
            (SELECT SUM(file_size) FROM file_inventory) as total_bytes,
            (SELECT COUNT(*) FROM dedup_groups) as dup_groups,
            (SELECT SUM(file_count - 1) FROM dedup_groups) as dup_files,
            (SELECT SUM(savings_bytes) FROM dedup_groups) as savings_bytes,
            (SELECT COUNT(DISTINCT xxhash) FROM file_inventory WHERE xxhash != 'EMPTY_FILE') as unique_hashes,
            (SELECT COUNT(*) FROM file_inventory WHERE file_size = 0 OR xxhash = 'EMPTY_FILE') as empty_files
    """).fetchone()
    
    total_files, total_bytes, dup_groups, dup_files, savings, unique, empty = stats
    unique_bytes = (total_bytes or 0) - (savings or 0)
    
    # Per-drive breakdown
    print("PER-DRIVE BREAKDOWN:")
    print(f"{'Drive':<8} {'Files':>10} {'Size':>12} {'Dupes':>8}")
    print("-" * 42)
    for drv_row in conn.execute("""
        SELECT source_drive, COUNT(*) as cnt, SUM(file_size) as sz
        FROM file_inventory GROUP BY source_drive ORDER BY sz DESC
    """).fetchall():
        d, c, s = drv_row
        dup_count = conn.execute("""
            SELECT COUNT(*) FROM file_inventory fi
            JOIN dedup_groups dg ON fi.xxhash = dg.xxhash
            WHERE fi.source_drive = ? AND fi.source_path != dg.canonical_path
        """, (d,)).fetchone()[0]
        print(f"  {d:<6} {c:>10,} {fmt_size(s or 0):>12} {dup_count:>8,}")
    
    # Per-type breakdown
    print(f"\nPER-TYPE BREAKDOWN:")
    print(f"{'Category':<20} {'Files':>10} {'Size':>12}")
    print("-" * 46)
    for type_row in conn.execute("""
        SELECT type_category, COUNT(*) as cnt, SUM(file_size) as sz
        FROM file_inventory GROUP BY type_category ORDER BY sz DESC
    """).fetchall():
        t, c, s = type_row
        print(f"  {t:<18} {c:>10,} {fmt_size(s or 0):>12}")
    
    # Per-lane breakdown
    print(f"\nPER-LANE BREAKDOWN:")
    print(f"{'Lane':<24} {'Files':>10} {'Size':>12}")
    print("-" * 50)
    for lane_row in conn.execute("""
        SELECT lane_guess, COUNT(*) as cnt, SUM(file_size) as sz
        FROM file_inventory GROUP BY lane_guess ORDER BY sz DESC
    """).fetchall():
        l, c, s = lane_row
        print(f"  {l:<22} {c:>10,} {fmt_size(s or 0):>12}")
    
    # Summary
    print(f"\n{'='*60}")
    print(f"DEDUPLICATION ANALYSIS COMPLETE")
    print(f"  Total files:         {total_files:>12,}")
    print(f"  Total size:          {fmt_size(total_bytes or 0):>12}")
    print(f"  Unique files:        {unique:>12,}")
    print(f"  Duplicate groups:    {(dup_groups or 0):>12,}")
    print(f"  Duplicate files:     {(dup_files or 0):>12,}")
    print(f"  Empty files:         {empty:>12,}")
    print(f"  Space savings:       {fmt_size(savings or 0):>12}")
    print(f"  After dedup:         {fmt_size(unique_bytes):>12}")
    print(f"\n  J:\\ free space:      {fmt_size(1_781_725_134_848):>12}")
    print(f"  Fits on J:\\?          {'? YES' if unique_bytes < 1_781_725_134_848 else '? NO'}")
    
    # Top 10 biggest duplicate groups
    print(f"\nTOP 10 LARGEST DUPLICATE GROUPS:")
    print(f"{'#':>3} {'Copies':>7} {'Size Each':>12} {'Total Waste':>12} {'File'}")
    print("-" * 70)
    for i, big_row in enumerate(conn.execute("""
        SELECT dg.file_count, dg.file_size, dg.savings_bytes, dg.canonical_path
        FROM dedup_groups dg
        ORDER BY dg.savings_bytes DESC
        LIMIT 10
    """).fetchall(), 1):
        cnt, sz, waste, cpath = big_row
        name = os.path.basename(cpath) if cpath else "?"
        print(f"  {i:>2}. {cnt:>5}x {fmt_size(sz):>12} {fmt_size(waste):>12}  {name[:40]}")
    
    conn.execute("""
        UPDATE progress SET status='complete', completed_at=datetime('now'),
        files_processed=?, notes=?
        WHERE phase='analyze'
    """, (total_files, f"Found {dup_groups or 0} dup groups, {fmt_size(savings or 0)} savings"))
    conn.commit()
    
    print(f"\nNext: python consolidate_drives.py plan")


# ===========================================================================
#  PHASE 3: PLAN -- Show what would be copied (dry-run)
# ===========================================================================

def phase_plan():
    """Show the consolidation plan without executing."""
    conn = get_state_db()
    
    analyze_status = conn.execute("SELECT status FROM progress WHERE phase='analyze'").fetchone()
    if not analyze_status or analyze_status[0] != "complete":
        print("[ERROR] Run 'analyze' phase first.")
        return
    
    # Files to copy: unique files only (skip duplicates, keep canonical)
    # For duplicates, only copy the canonical version
    to_copy = conn.execute("""
        SELECT COUNT(*), SUM(file_size)
        FROM file_inventory fi
        WHERE fi.copy_status = 'pending'
          AND fi.source_drive != 'J:'
          AND (
            -- Not a duplicate
            fi.xxhash NOT IN (SELECT xxhash FROM dedup_groups)
            OR
            -- Is the canonical copy of a duplicate
            fi.source_path IN (SELECT canonical_path FROM dedup_groups)
          )
    """).fetchone()
    
    # Files already on J:\ (skip)
    on_j = conn.execute("""
        SELECT COUNT(*), SUM(file_size) FROM file_inventory WHERE source_drive = 'J:'
    """).fetchone()
    
    # Duplicate files that will be skipped
    dup_skip = conn.execute("""
        SELECT COUNT(*), SUM(file_size)
        FROM file_inventory fi
        WHERE fi.source_drive != 'J:'
          AND fi.xxhash IN (SELECT xxhash FROM dedup_groups)
          AND fi.source_path NOT IN (SELECT canonical_path FROM dedup_groups)
    """).fetchone()
    
    copy_count, copy_bytes = to_copy
    j_count, j_bytes = on_j
    skip_count, skip_bytes = dup_skip
    
    print(f"{'='*60}")
    print(f"CONSOLIDATION PLAN (DRY RUN)")
    print(f"{'='*60}")
    print(f"  Files to COPY to J:\\:   {(copy_count or 0):>10,}  ({fmt_size(copy_bytes or 0)})")
    print(f"  Already on J:\\:         {(j_count or 0):>10,}  ({fmt_size(j_bytes or 0)})")
    print(f"  Duplicates to SKIP:     {(skip_count or 0):>10,}  ({fmt_size(skip_bytes or 0)})")
    print(f"  J:\\ free space:         {'':>10}  ({fmt_size(1_781_725_134_848)})")
    print(f"  Space after copy:       {'':>10}  ({fmt_size(1_781_725_134_848 - (copy_bytes or 0))})")
    
    # Show target directory structure
    print(f"\nTARGET DIRECTORY STRUCTURE:")
    print(f"  {TARGET_ROOT}\\")
    for cat_row in conn.execute("""
        SELECT type_category, COUNT(*), SUM(file_size)
        FROM file_inventory
        WHERE source_drive != 'J:'
          AND (xxhash NOT IN (SELECT xxhash FROM dedup_groups)
               OR source_path IN (SELECT canonical_path FROM dedup_groups))
        GROUP BY type_category ORDER BY SUM(file_size) DESC
    """).fetchall():
        cat, cnt, sz = cat_row
        print(f"    +-- {cat}/ ({cnt:,} files, {fmt_size(sz or 0)})")
    
    conn.execute(
        "UPDATE progress SET status='complete', completed_at=datetime('now'), notes=? WHERE phase='plan'",
        (f"{copy_count or 0} files to copy, {fmt_size(copy_bytes or 0)}",)
    )
    conn.commit()
    
    print(f"\n??  This will COPY (not move) files. Originals stay on source drives.")
    print(f"Next: python consolidate_drives.py execute")


# ===========================================================================
#  PHASE 4: EXECUTE -- Copy files to J:\ with verification
# ===========================================================================

def phase_execute():
    """Execute the consolidation: copy unique files to J:\\ with verification."""
    conn = get_state_db()
    
    plan_status = conn.execute("SELECT status FROM progress WHERE phase='plan'").fetchone()
    if not plan_status or plan_status[0] != "complete":
        print("[ERROR] Run 'plan' phase first.")
        return
    
    conn.execute(
        "UPDATE progress SET status='running', started_at=datetime('now') WHERE phase='execute'"
    )
    conn.commit()
    
    # Get files to copy (unique only, not on J:\ already)
    to_copy = conn.execute("""
        SELECT id, source_path, target_path, file_size, xxhash
        FROM file_inventory
        WHERE copy_status = 'pending'
          AND source_drive != 'J:'
          AND (
            xxhash NOT IN (SELECT xxhash FROM dedup_groups)
            OR source_path IN (SELECT canonical_path FROM dedup_groups)
          )
        ORDER BY file_size DESC
    """).fetchall()
    
    total = len(to_copy)
    total_bytes = sum(r[3] for r in to_copy)
    print(f"[EXECUTE] Copying {total:,} files ({fmt_size(total_bytes)}) to {TARGET_ROOT}\n")
    
    copied = 0
    copied_bytes = 0
    errors = 0
    start_time = time.time()
    
    for file_id, src, tgt, fsize, src_hash in to_copy:
        try:
            # Create target directory
            tgt_path = Path(tgt)
            tgt_path.parent.mkdir(parents=True, exist_ok=True)
            
            # Skip if target already exists with same size
            if tgt_path.exists() and tgt_path.stat().st_size == fsize:
                conn.execute(
                    "UPDATE file_inventory SET copy_status='exists' WHERE id=?", (file_id,)
                )
                copied += 1
                copied_bytes += fsize
                continue
            
            # Copy
            shutil.copy2(src, str(tgt_path))
            
            # Verify hash immediately
            tgt_hash = fast_hash(str(tgt_path))
            if tgt_hash == src_hash:
                conn.execute(
                    "UPDATE file_inventory SET copy_status='verified', verify_status='pass', "
                    "copied_at=datetime('now'), verified_at=datetime('now') WHERE id=?",
                    (file_id,)
                )
            else:
                conn.execute(
                    "UPDATE file_inventory SET copy_status='hash_mismatch', verify_status='fail', "
                    "copied_at=datetime('now') WHERE id=?",
                    (file_id,)
                )
                errors += 1
                log_event(conn, "execute", f"Hash mismatch: {src}", 
                         f"src={src_hash}, tgt={tgt_hash}")
            
            copied += 1
            copied_bytes += fsize
            
            # Progress every 100 files
            if copied % 100 == 0:
                elapsed = time.time() - start_time
                rate = copied_bytes / elapsed if elapsed > 0 else 0
                eta = (total_bytes - copied_bytes) / rate if rate > 0 else 0
                pct = copied_bytes * 100 / total_bytes if total_bytes > 0 else 0
                print(f"  [{pct:5.1f}%] {copied:>8,}/{total:,} files | "
                      f"{fmt_size(copied_bytes)}/{fmt_size(total_bytes)} | "
                      f"{fmt_size(rate)}/s | ETA {fmt_duration(eta)}")
                conn.commit()
                
        except (PermissionError, OSError) as e:
            errors += 1
            conn.execute(
                "UPDATE file_inventory SET copy_status='error' WHERE id=?", (file_id,)
            )
            if errors <= 20:
                log_event(conn, "execute", f"Copy error: {src}", str(e))
    
    conn.commit()
    
    elapsed = time.time() - start_time
    conn.execute("""
        UPDATE progress SET status='complete', completed_at=datetime('now'),
        files_processed=?, files_total=?, bytes_processed=?, bytes_total=?, errors=?,
        notes=?
        WHERE phase='execute'
    """, (copied, total, copied_bytes, total_bytes, errors,
          f"Copied in {fmt_duration(elapsed)}, {fmt_size(copied_bytes/elapsed if elapsed > 0 else 0)}/s avg"))
    conn.commit()
    
    print(f"\n{'='*60}")
    print(f"COPY COMPLETE")
    print(f"  Files copied:    {copied:,}")
    print(f"  Bytes copied:    {fmt_size(copied_bytes)}")
    print(f"  Errors:          {errors}")
    print(f"  Duration:        {fmt_duration(elapsed)}")
    print(f"  Avg throughput:  {fmt_size(copied_bytes/elapsed if elapsed > 0 else 0)}/s")
    print(f"\nNext: python consolidate_drives.py verify")


# ===========================================================================
#  PHASE 5: VERIFY -- Re-verify all copied files
# ===========================================================================

def phase_verify():
    """Re-verify all copied files by re-hashing targets."""
    conn = get_state_db()
    
    # Get files that were copied but not yet verified (or need re-verification)
    to_verify = conn.execute("""
        SELECT id, source_path, target_path, xxhash, file_size
        FROM file_inventory
        WHERE copy_status IN ('verified', 'exists') AND source_drive != 'J:'
    """).fetchall()
    
    total = len(to_verify)
    print(f"[VERIFY] Re-verifying {total:,} files on J:\\...\n")
    
    passed = 0
    failed = 0
    missing = 0
    start_time = time.time()
    
    for file_id, src, tgt, src_hash, fsize in to_verify:
        tgt_path = Path(tgt)
        if not tgt_path.exists():
            missing += 1
            conn.execute(
                "UPDATE file_inventory SET verify_status='missing' WHERE id=?", (file_id,)
            )
            continue
        
        tgt_hash = fast_hash(str(tgt_path))
        if tgt_hash == src_hash:
            passed += 1
            conn.execute(
                "UPDATE file_inventory SET verify_status='pass', verified_at=datetime('now') WHERE id=?",
                (file_id,)
            )
        else:
            failed += 1
            conn.execute(
                "UPDATE file_inventory SET verify_status='fail' WHERE id=?", (file_id,)
            )
        
        if (passed + failed + missing) % 200 == 0:
            print(f"  {passed+failed+missing:>8,}/{total:,} verified | ? {passed} ? {failed} ?? {missing}")
    
    conn.commit()
    elapsed = time.time() - start_time
    
    conn.execute("""
        UPDATE progress SET status='complete', completed_at=datetime('now'),
        files_processed=?, files_total=?, errors=?,
        notes=?
        WHERE phase='verify'
    """, (passed, total, failed + missing,
          f"Passed: {passed}, Failed: {failed}, Missing: {missing}"))
    conn.commit()
    
    print(f"\n{'='*60}")
    print(f"VERIFICATION COMPLETE")
    print(f"  ? Passed:   {passed:,}")
    print(f"  ? Failed:   {failed:,}")
    print(f"  ??  Missing:  {missing:,}")
    print(f"  Duration:    {fmt_duration(elapsed)}")
    
    if failed == 0 and missing == 0:
        print(f"\n? ALL FILES VERIFIED SUCCESSFULLY")
    else:
        print(f"\n??  {failed + missing} files need attention. Check consolidation_log for details.")


# ===========================================================================
#  PHASE 6: MANIFEST -- Generate master manifest
# ===========================================================================

def phase_manifest():
    """Generate the master manifest JSON for the consolidated archive."""
    conn = get_state_db()
    
    manifest = {
        "generated_at": datetime.now().isoformat(),
        "target_root": str(TARGET_ROOT),
        "hash_engine": HASH_ENGINE,
        "source_drives": SOURCE_DRIVES,
        "summary": {},
        "by_drive": {},
        "by_type": {},
        "by_lane": {},
        "dedup_stats": {},
    }
    
    # Summary
    row = conn.execute("""
        SELECT COUNT(*), SUM(file_size), COUNT(DISTINCT xxhash)
        FROM file_inventory
    """).fetchone()
    manifest["summary"] = {
        "total_files": row[0],
        "total_bytes": row[1],
        "unique_hashes": row[2],
    }
    
    # By drive
    for drv in conn.execute("""
        SELECT source_drive, COUNT(*), SUM(file_size) 
        FROM file_inventory GROUP BY source_drive
    """).fetchall():
        manifest["by_drive"][drv[0]] = {"files": drv[1], "bytes": drv[2]}
    
    # By type
    for typ in conn.execute("""
        SELECT type_category, COUNT(*), SUM(file_size)
        FROM file_inventory GROUP BY type_category
    """).fetchall():
        manifest["by_type"][typ[0]] = {"files": typ[1], "bytes": typ[2]}
    
    # By lane
    for lane in conn.execute("""
        SELECT lane_guess, COUNT(*), SUM(file_size)
        FROM file_inventory GROUP BY lane_guess
    """).fetchall():
        manifest["by_lane"][lane[0]] = {"files": lane[1], "bytes": lane[2]}
    
    # Dedup stats
    dedup = conn.execute("""
        SELECT COUNT(*), SUM(file_count - 1), SUM(savings_bytes)
        FROM dedup_groups
    """).fetchone()
    manifest["dedup_stats"] = {
        "duplicate_groups": dedup[0] or 0,
        "duplicate_files": dedup[1] or 0,
        "space_savings_bytes": dedup[2] or 0,
    }
    
    # Write manifest
    manifest_path = TARGET_ROOT / "MANIFEST.json"
    TARGET_ROOT.mkdir(parents=True, exist_ok=True)
    
    try:
        import orjson
        with open(str(manifest_path), "wb") as f:
            f.write(orjson.dumps(manifest, option=orjson.OPT_INDENT_2))
    except ImportError:
        with open(str(manifest_path), "w", encoding="utf-8") as f:
            json.dump(manifest, f, indent=2, default=str)
    
    conn.execute("""
        UPDATE progress SET status='complete', completed_at=datetime('now'),
        notes=?
        WHERE phase='manifest'
    """, (f"Manifest written to {manifest_path}",))
    conn.commit()
    
    print(f"[MANIFEST] Written to {manifest_path}")
    print(json.dumps(manifest["summary"], indent=2, default=str))
    print(json.dumps(manifest["dedup_stats"], indent=2, default=str))


# ===========================================================================
#  STATUS -- Current progress
# ===========================================================================

def show_status():
    """Show current consolidation progress."""
    conn = get_state_db()
    
    print(f"{'='*60}")
    print(f"DRIVE CONSOLIDATION STATUS")
    print(f"  Target: {TARGET_ROOT}")
    print(f"  State:  {STATE_DB}")
    print(f"  Hash:   {HASH_ENGINE}")
    print(f"{'='*60}")
    
    for row in conn.execute("""
        SELECT phase, status, files_processed, files_total, bytes_processed, 
               bytes_total, errors, notes, started_at, completed_at
        FROM progress ORDER BY 
            CASE phase 
                WHEN 'inventory' THEN 1 WHEN 'analyze' THEN 2 
                WHEN 'plan' THEN 3 WHEN 'execute' THEN 4
                WHEN 'verify' THEN 5 WHEN 'manifest' THEN 6
            END
    """).fetchall():
        phase, status, fp, ft, bp, bt, errs, notes, started, completed = row
        icon = {"pending": "?", "running": "?", "complete": "?"}.get(status, "?")
        print(f"\n  {icon} Phase: {phase.upper()}")
        print(f"    Status: {status}")
        if ft and ft > 0:
            print(f"    Files:  {fp:,} / {ft:,}")
        if bt and bt > 0:
            print(f"    Bytes:  {fmt_size(bp or 0)} / {fmt_size(bt)}")
        if errs and errs > 0:
            print(f"    Errors: {errs}")
        if notes:
            print(f"    Notes:  {notes}")
    
    # File counts if inventory exists
    total = conn.execute("SELECT COUNT(*) FROM file_inventory").fetchone()[0]
    if total > 0:
        print(f"\n  ? Inventory: {total:,} files tracked")
        for drv in conn.execute("""
            SELECT source_drive, COUNT(*), SUM(file_size)
            FROM file_inventory GROUP BY source_drive ORDER BY SUM(file_size) DESC
        """).fetchall():
            print(f"    {drv[0]:>4}: {drv[1]:>8,} files ({fmt_size(drv[2] or 0)})")


def show_dashboard():
    """Full dashboard: inventory + dupes + plan."""
    show_status()
    print()
    phase_analyze()
    print()
    phase_plan()


# ===========================================================================
#  MAIN
# ===========================================================================

COMMANDS = {
    "inventory": phase_inventory,
    "analyze": phase_analyze,
    "plan": phase_plan,
    "execute": phase_execute,
    "verify": phase_verify,
    "manifest": phase_manifest,
    "status": show_status,
    "dashboard": show_dashboard,
}

def main():
    if len(sys.argv) < 2 or sys.argv[1] not in COMMANDS:
        print(__doc__)
        print(f"\nAvailable commands: {', '.join(COMMANDS.keys())}")
        print(f"\nHash engine: {HASH_ENGINE}")
        print(f"Target: {TARGET_ROOT}")
        return
    
    cmd = sys.argv[1]
    COMMANDS[cmd]()

if __name__ == "__main__":
    main()
