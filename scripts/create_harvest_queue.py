"""Create and populate harvest_queue table from file_inventory.

Filters to C:\ and I:\ drives only. Excludes already-processed files from kraken_processed.
Assigns phase (by file type) and priority (by path patterns).
"""
import sqlite3
import re
import sys
import time

DB_PATH = r"C:\Users\andre\LitigationOS\litigation_context.db"

# Phase mapping: extension -> phase number
PHASE_MAP = {
    'pdf': '2', 'docx': '2',
    'txt': '3',
    'md': '4',
    'html': '5', 'csv': '5', 'htm': '5',
    'json': '6', 'jsonl': '6',
}

# Priority patterns: list of (compiled_regex, priority_level)
PRIORITY_PATTERNS = [
    (re.compile(r'(?i)(police|NSPD|NS\d{7}|incident.report|officer.report)', re.I), 0),
    (re.compile(r'(?i)(court.order|judgment|ex.parte|PPO|protection.order|motion|petition|complaint)', re.I), 0),
    (re.compile(r'(?i)(affidavit|deposition|testimony|witness|subpoena)', re.I), 1),
    (re.compile(r'(?i)(evidence|exhibit|healthwest|randall|appclose)', re.I), 1),
    (re.compile(r'(?i)(MCR|MCL|MRE|statute|rule|benchbook|authority)', re.I), 2),
    (re.compile(r'(?i)(analysis|dossier|timeline|chronolog|summary|brief)', re.I), 3),
    (re.compile(r'(?i)(email|message|communication|correspondence|text.export)', re.I), 4),
    (re.compile(r'(?i)(financial|medical|housing|shady.oaks|rent|lease|mortgage)', re.I), 5),
    (re.compile(r'(?i)(reference|template|guide|manual|README)', re.I), 6),
]

# Exclusion patterns (directories to skip)
EXCLUSIONS = re.compile(
    r'(?i)([\\/]node_modules[\\/]|[\\/]__pycache__[\\/]|[\\/]\.git[\\/]|'
    r'[\\/]site-packages[\\/]|[\\/]\.venv[\\/]|[\\/]pytools_venv[\\/]|'
    r'[\\/]awesome-\w+[\\/]|[\\/]\.pytest_cache[\\/]|'
    r'[\\/]LitigationOS\.worktrees[\\/]|[\\/]\.mcp_venv[\\/])'
)

def assign_priority(file_path: str) -> int:
    """Assign priority 0-7 based on path patterns."""
    for pattern, priority in PRIORITY_PATTERNS:
        if pattern.search(file_path):
            return priority
    return 7  # default

def normalize_ext(ext: str) -> str:
    """Normalize extension: strip leading dot, lowercase."""
    return ext.lstrip('.').lower()

def main():
    conn = sqlite3.connect(DB_PATH)
    conn.execute("PRAGMA busy_timeout = 60000")
    conn.execute("PRAGMA journal_mode = WAL")
    conn.execute("PRAGMA cache_size = -32000")
    conn.execute("PRAGMA synchronous = NORMAL")
    conn.execute("PRAGMA temp_store = MEMORY")

    # Create table
    conn.execute("""
        CREATE TABLE IF NOT EXISTS harvest_queue (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            file_path TEXT UNIQUE NOT NULL,
            drive TEXT NOT NULL,
            file_type TEXT NOT NULL,
            file_size INTEGER DEFAULT 0,
            phase TEXT NOT NULL,
            priority INTEGER DEFAULT 7,
            status TEXT DEFAULT 'QUEUED',
            batch_id TEXT,
            session_id TEXT,
            findings_count INTEGER DEFAULT 0,
            error_msg TEXT,
            queued_at TEXT DEFAULT (datetime('now')),
            processed_at TEXT
        )
    """)
    conn.execute("CREATE INDEX IF NOT EXISTS idx_hq_status ON harvest_queue(status)")
    conn.execute("CREATE INDEX IF NOT EXISTS idx_hq_phase_status ON harvest_queue(phase, status)")
    conn.execute("CREATE INDEX IF NOT EXISTS idx_hq_priority ON harvest_queue(priority, status)")
    conn.execute("CREATE INDEX IF NOT EXISTS idx_hq_drive ON harvest_queue(drive, status)")
    conn.commit()
    print("[OK] harvest_queue table + indexes created")

    # Load already-processed paths from kraken_processed
    kraken_paths = set()
    try:
        rows = conn.execute("SELECT file_path FROM kraken_processed").fetchall()
        kraken_paths = {r[0] for r in rows}
        print(f"[OK] Loaded {len(kraken_paths)} kraken_processed paths for dedup")
    except Exception as e:
        print(f"[WARN] kraken_processed query failed: {e}")

    # Load already-queued paths
    existing_paths = set()
    try:
        rows = conn.execute("SELECT file_path FROM harvest_queue").fetchall()
        existing_paths = {r[0] for r in rows}
        print(f"[OK] {len(existing_paths)} paths already in harvest_queue")
    except Exception:
        pass

    # Supported extensions (both dotted and undotted)
    supported = {'pdf', 'txt', 'md', 'docx', 'csv', 'html', 'htm', 'json', 'jsonl',
                 '.pdf', '.txt', '.md', '.docx', '.csv', '.html', '.htm', '.json', '.jsonl'}

    # Query file_inventory for C and I drives
    cursor = conn.execute("""
        SELECT file_path, drive_letter, extension, size_bytes
        FROM file_inventory
        WHERE drive_letter IN ('C', 'I')
          AND extension IS NOT NULL
    """)

    batch = []
    skipped_ext = 0
    skipped_excl = 0
    skipped_kraken = 0
    skipped_existing = 0
    total_queued = 0
    batch_size = 5000

    t0 = time.time()

    for row in cursor:
        fp, drive, ext, size = row
        if not fp or not ext:
            continue

        # Filter by supported extension
        if ext not in supported:
            skipped_ext += 1
            continue

        # Exclusion filter
        if EXCLUSIONS.search(fp):
            skipped_excl += 1
            continue

        # Dedup against kraken_processed
        if fp in kraken_paths:
            skipped_kraken += 1
            continue

        # Dedup against already-queued
        if fp in existing_paths:
            skipped_existing += 1
            continue

        norm = normalize_ext(ext)
        phase = PHASE_MAP.get(norm, '6')
        priority = assign_priority(fp)

        batch.append((fp, drive, norm, size or 0, phase, priority))

        if len(batch) >= batch_size:
            conn.executemany(
                "INSERT OR IGNORE INTO harvest_queue (file_path, drive, file_type, file_size, phase, priority) "
                "VALUES (?, ?, ?, ?, ?, ?)",
                batch
            )
            conn.commit()
            total_queued += len(batch)
            elapsed = time.time() - t0
            print(f"  ... queued {total_queued:,} files ({elapsed:.1f}s)")
            batch = []

    # Flush remaining
    if batch:
        conn.executemany(
            "INSERT OR IGNORE INTO harvest_queue (file_path, drive, file_type, file_size, phase, priority) "
            "VALUES (?, ?, ?, ?, ?, ?)",
            batch
        )
        conn.commit()
        total_queued += len(batch)

    elapsed = time.time() - t0

    # Verify
    count = conn.execute("SELECT COUNT(*) FROM harvest_queue").fetchone()[0]
    by_phase = conn.execute(
        "SELECT phase, COUNT(*) FROM harvest_queue GROUP BY phase ORDER BY phase"
    ).fetchall()
    by_priority = conn.execute(
        "SELECT priority, COUNT(*) FROM harvest_queue GROUP BY priority ORDER BY priority"
    ).fetchall()
    by_drive = conn.execute(
        "SELECT drive, COUNT(*) FROM harvest_queue GROUP BY drive ORDER BY drive"
    ).fetchall()

    print(f"\n{'='*60}")
    print(f"HARVEST QUEUE POPULATED")
    print(f"{'='*60}")
    print(f"Total queued:      {count:>10,}")
    print(f"Queued this run:   {total_queued:>10,}")
    print(f"Skipped (ext):     {skipped_ext:>10,}")
    print(f"Skipped (excl):    {skipped_excl:>10,}")
    print(f"Skipped (kraken):  {skipped_kraken:>10,}")
    print(f"Skipped (dup):     {skipped_existing:>10,}")
    print(f"Time:              {elapsed:>10.1f}s")
    print(f"\nBy Phase:")
    for phase, cnt in by_phase:
        print(f"  Phase {phase}: {cnt:>10,}")
    print(f"\nBy Priority:")
    for pri, cnt in by_priority:
        print(f"  P{pri}: {cnt:>10,}")
    print(f"\nBy Drive:")
    for drv, cnt in by_drive:
        print(f"  {drv}:\\  {cnt:>10,}")

    conn.close()
    print(f"\n[DONE] harvest_queue ready for Go harvest engine")

if __name__ == "__main__":
    main()
