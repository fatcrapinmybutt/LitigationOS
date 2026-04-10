#!/usr/bin/env python3
"""PROJECT INFINITE HARVEST — Recursive Intelligence Convergence Engine.

Self-perpetuating, queue-driven evidence harvesting across C:\ and I:\ drives.
Survives session boundaries via harvest_queue DB state + passdown files.

Usage:
    python infinite_harvest.py init          # Create harvest_queue + populate from file_inventory
    python infinite_harvest.py status        # Show queue status by phase/priority
    python infinite_harvest.py batch [N]     # Process next N files (default 25)
    python infinite_harvest.py batch --phase 2  # Process only phase 2 (PDF/DOCX)
    python infinite_harvest.py wiztree PATH  # Supplement queue from WizTree CSV export
    python infinite_harvest.py passdown      # Generate passdown .md for session handoff

Designed for LitigationOS — all intelligence persists to litigation_context.db.
"""

import csv
import hashlib
import logging
import os
import re
import sqlite3
import sys
import time
import uuid
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Set, Tuple

# Ensure we can import from parent dirs
REPO_ROOT = Path(__file__).resolve().parent.parent.parent.parent
sys.path.insert(0, str(REPO_ROOT / "00_SYSTEM"))

logger = logging.getLogger("infinite_harvest")

# ── Constants ─────────────────────────────────────────────────────────────────

DB_PATH = REPO_ROOT / "litigation_context.db"
SESSION_ID = f"ih-{datetime.now().strftime('%Y%m%d-%H%M%S')}-{uuid.uuid4().hex[:6]}"

HARVESTABLE_EXTENSIONS = {
    '.pdf', '.txt', '.md', '.docx', '.csv', '.html', '.json',
    'pdf', 'txt', 'md', 'docx', 'csv', 'html', 'json',
}

EXCLUDE_PATTERNS = [
    'node_modules', '__pycache__', 'site-packages', '.git',
    '.venv', 'pytools_venv', 'awesome-ctf', 'awesome-forensics',
    'awesome-hacking', 'awesome-incident-response', 'awesome-malware-analysis',
    'awesome-osint', 'awesome-pentest', 'awesome-security',
    'LitigationOS.worktrees', '.pytest_cache', '.mypy_cache',
    'fredprime-legal-system', '.eide', '.superpower-copilot',
]

# Phase mapping: extension → phase number
PHASE_MAP = {
    '.pdf': '2', 'pdf': '2',
    '.docx': '2', 'docx': '2',
    '.txt': '3', 'txt': '3',
    '.md': '4', 'md': '4',
    '.html': '5', 'html': '5',
    '.csv': '5', 'csv': '5',
    '.json': '6', 'json': '6',
}

# Priority patterns: path substring → priority (lower = higher priority)
PRIORITY_RULES = [
    # P0: CRITICAL — direct case evidence
    (r'(?i)police.?report|NSPD|NS\d{7}', 0),
    (r'(?i)court.?order|judgment|sentence', 0),
    (r'(?i)ex.?parte|emergency.?order', 0),
    (r'(?i)PPO|protection.?order|2023.?5907', 0),
    (r'(?i)motion|brief|complaint|petition', 0),
    (r'(?i)05_FILINGS|03_COURT', 0),
    # P1: HIGH — evidence + witness
    (r'(?i)affidavit|deposition|testimony|witness', 1),
    (r'(?i)01_EVIDENCE|evidence', 1),
    (r'(?i)AppClose|appclose|text.?message', 1),
    (r'(?i)healthwest|evaluation|assessment', 1),
    (r'(?i)watson|mcneill|rusco|berry|pigors', 1),
    # P2: HIGH — legal authority
    (r'(?i)MCR|MCL|MRE|michigan.?rule|court.?rule', 2),
    (r'(?i)02_AUTHORITY|authority|statute|act\.', 2),
    (r'(?i)09_REFERENCE|reference', 2),
    (r'(?i)case.?law|opinion|appellate|supreme', 2),
    (r'(?i)benchbook|bench.?book', 2),
    # P3: MEDIUM — analysis
    (r'(?i)04_ANALYSIS|analysis|dossier|profile', 3),
    (r'(?i)timeline|chronolog|narrative|summary', 3),
    (r'(?i)impeach|contradict|credibility', 3),
    # P4: MEDIUM — communications
    (r'(?i)email|message|correspondence|letter', 4),
    (r'(?i)chat|conversation|transcript', 4),
    (r'(?i)06_DATA|data', 4),
    # P5: LOWER — financial/medical/housing
    (r'(?i)financial|invoice|receipt|tax|bank', 5),
    (r'(?i)medical|health|prescription|pharmacy', 5),
    (r'(?i)housing|lease|rent|eviction|shady.?oaks', 5),
    (r'(?i)property|title|deed|mortgage', 5),
    # P6: LOW — reference/templates
    (r'(?i)template|guide|manual|reference|README', 6),
    (r'(?i)00_SYSTEM|system|config|setting', 6),
    (r'(?i)07_CODE|code|script', 6),
]

# Compile priority patterns once
COMPILED_PRIORITY_RULES = [(re.compile(p), pri) for p, pri in PRIORITY_RULES]


# ── Database Connection ──────────────────────────────────────────────────────

def get_connection() -> sqlite3.Connection:
    """Get a connection with proper PRAGMAs (Rule 18)."""
    conn = sqlite3.connect(str(DB_PATH), timeout=120)
    conn.execute("PRAGMA busy_timeout = 60000")
    conn.execute("PRAGMA journal_mode = WAL")
    conn.execute("PRAGMA cache_size = -32000")
    conn.execute("PRAGMA temp_store = MEMORY")
    conn.execute("PRAGMA synchronous = NORMAL")
    return conn


# ── DDL ───────────────────────────────────────────────────────────────────────

HARVEST_QUEUE_DDL = """
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
);
"""

HARVEST_QUEUE_INDEXES = [
    "CREATE INDEX IF NOT EXISTS idx_hq_status ON harvest_queue(status);",
    "CREATE INDEX IF NOT EXISTS idx_hq_phase_status ON harvest_queue(phase, status);",
    "CREATE INDEX IF NOT EXISTS idx_hq_priority ON harvest_queue(priority, status);",
    "CREATE INDEX IF NOT EXISTS idx_hq_drive ON harvest_queue(drive, status);",
    "CREATE INDEX IF NOT EXISTS idx_hq_file_type ON harvest_queue(file_type, status);",
]


# ── Utility ──────────────────────────────────────────────────────────────────

def assign_priority(file_path: str) -> int:
    """Assign priority 0-7 based on path patterns. Lower = higher priority."""
    for pattern, priority in COMPILED_PRIORITY_RULES:
        if pattern.search(file_path):
            return priority
    return 7  # Default: lowest priority


def is_excluded(file_path: str) -> bool:
    """Check if file path matches any exclusion pattern."""
    fp_lower = file_path.lower()
    for excl in EXCLUDE_PATTERNS:
        if excl.lower() in fp_lower:
            return True
    return False


def get_drive(file_path: str) -> str:
    """Extract drive letter from path."""
    if len(file_path) >= 2 and file_path[1] == ':':
        return file_path[0].upper()
    return 'C'


# ── INIT: Create table + populate from file_inventory ────────────────────────

def cmd_init(conn: sqlite3.Connection) -> dict:
    """Create harvest_queue and populate from file_inventory."""
    stats = {'created': False, 'inserted': 0, 'skipped_excluded': 0,
             'skipped_processed': 0, 'skipped_duplicate': 0, 'total_queried': 0}

    # Create table
    conn.execute(HARVEST_QUEUE_DDL)
    for idx_sql in HARVEST_QUEUE_INDEXES:
        conn.execute(idx_sql)
    conn.commit()
    stats['created'] = True
    print("[INIT] harvest_queue table created with indexes")

    # Check existing queue size
    existing = conn.execute("SELECT COUNT(*) FROM harvest_queue").fetchone()[0]
    if existing > 0:
        print(f"[INIT] harvest_queue already has {existing:,} rows. Use 'status' to check.")
        choice = input("Repopulate? (y/N): ").strip().lower() if sys.stdin.isatty() else 'y'
        if choice != 'y':
            return stats

    # Get already-processed file paths from kraken_processed
    processed_paths: Set[str] = set()
    try:
        rows = conn.execute("SELECT file_path FROM kraken_processed").fetchall()
        processed_paths = {r[0] for r in rows}
        print(f"[INIT] {len(processed_paths):,} files already processed by KRAKEN")
    except sqlite3.OperationalError:
        pass

    # Query file_inventory for harvestable files on C:\ and I:\
    print("[INIT] Querying file_inventory for harvestable files...")
    cursor = conn.execute("""
        SELECT file_path, extension, size_bytes, drive_letter
        FROM file_inventory
        WHERE drive_letter IN ('C', 'I')
        ORDER BY drive_letter, extension
    """)

    batch = []
    batch_size = 5000
    row_count = 0

    while True:
        rows = cursor.fetchmany(batch_size)
        if not rows:
            break

        for file_path, ext, size_bytes, drive in rows:
            row_count += 1
            stats['total_queried'] += 1

            # Normalize extension
            ext_lower = ext.lower() if ext else ''
            if ext_lower not in HARVESTABLE_EXTENSIONS:
                continue

            # Exclusion check
            if is_excluded(file_path):
                stats['skipped_excluded'] += 1
                continue

            # Already processed check
            if file_path in processed_paths:
                stats['skipped_processed'] += 1
                continue

            # Determine phase and priority
            phase = PHASE_MAP.get(ext_lower, '6')
            priority = assign_priority(file_path)
            drv = drive if drive else get_drive(file_path)
            file_type = ext_lower.lstrip('.')

            batch.append((file_path, drv, file_type, size_bytes or 0, phase, priority))

        # Flush batch
        if len(batch) >= batch_size:
            inserted = _flush_batch(conn, batch)
            stats['inserted'] += inserted
            stats['skipped_duplicate'] += len(batch) - inserted
            print(f"  ... {stats['inserted']:,} inserted ({row_count:,} scanned)")
            batch = []

    # Final flush
    if batch:
        inserted = _flush_batch(conn, batch)
        stats['inserted'] += inserted
        stats['skipped_duplicate'] += len(batch) - inserted

    conn.commit()
    print(f"\n[INIT] COMPLETE:")
    print(f"  Scanned:          {stats['total_queried']:,}")
    print(f"  Inserted:         {stats['inserted']:,}")
    print(f"  Skipped excluded: {stats['skipped_excluded']:,}")
    print(f"  Skipped processed:{stats['skipped_processed']:,}")
    print(f"  Skipped duplicate:{stats['skipped_duplicate']:,}")

    return stats


def _flush_batch(conn: sqlite3.Connection, batch: list) -> int:
    """Insert batch into harvest_queue, ignoring duplicates."""
    inserted = 0
    try:
        conn.executemany(
            """INSERT OR IGNORE INTO harvest_queue
               (file_path, drive, file_type, file_size, phase, priority)
               VALUES (?, ?, ?, ?, ?, ?)""",
            batch
        )
        inserted = conn.total_changes  # approximate
        conn.commit()
    except sqlite3.Error as e:
        logger.error("Batch insert error: %s", e)
        # Fall back to row-by-row
        for row in batch:
            try:
                conn.execute(
                    """INSERT OR IGNORE INTO harvest_queue
                       (file_path, drive, file_type, file_size, phase, priority)
                       VALUES (?, ?, ?, ?, ?, ?)""",
                    row
                )
                inserted += 1
            except sqlite3.Error:
                pass
        conn.commit()
    return inserted


# ── STATUS: Queue dashboard ──────────────────────────────────────────────────

def cmd_status(conn: sqlite3.Connection) -> dict:
    """Show queue status by phase, priority, and drive."""
    stats = {}

    # Overall
    row = conn.execute("SELECT COUNT(*) FROM harvest_queue").fetchone()
    total = row[0]
    print(f"\n=== INFINITE HARVEST QUEUE: {total:,} total files ===\n")

    if total == 0:
        print("Queue is empty. Run 'init' to populate.")
        return stats

    # By status
    print("--- By Status ---")
    rows = conn.execute(
        "SELECT status, COUNT(*) as cnt FROM harvest_queue GROUP BY status ORDER BY cnt DESC"
    ).fetchall()
    for status, cnt in rows:
        pct = cnt * 100.0 / total
        print(f"  {status:12s} {cnt:>8,}  ({pct:.1f}%)")
        stats[f'status_{status}'] = cnt

    # By phase + status
    print("\n--- By Phase ---")
    phase_names = {'2': 'PDF/DOCX', '3': 'TXT', '4': 'MD', '5': 'HTML/CSV', '6': 'JSON'}
    rows = conn.execute("""
        SELECT phase, status, COUNT(*) as cnt
        FROM harvest_queue
        GROUP BY phase, status
        ORDER BY phase, status
    """).fetchall()
    current_phase = None
    for phase, status, cnt in rows:
        if phase != current_phase:
            pname = phase_names.get(phase, f'Phase {phase}')
            print(f"\n  Phase {phase} ({pname}):")
            current_phase = phase
        print(f"    {status:12s} {cnt:>8,}")

    # By priority (QUEUED only)
    print("\n--- QUEUED by Priority ---")
    rows = conn.execute("""
        SELECT priority, COUNT(*) as cnt
        FROM harvest_queue
        WHERE status = 'QUEUED'
        GROUP BY priority
        ORDER BY priority
    """).fetchall()
    pri_names = {0: 'P0-CRITICAL', 1: 'P1-HIGH(evidence)', 2: 'P2-HIGH(legal)',
                 3: 'P3-MED(analysis)', 4: 'P4-MED(comms)', 5: 'P5-LOW(fin/med)',
                 6: 'P6-LOW(ref)', 7: 'P7-LOWEST'}
    for pri, cnt in rows:
        pname = pri_names.get(pri, f'P{pri}')
        print(f"  {pname:20s} {cnt:>8,}")

    # By drive
    print("\n--- By Drive ---")
    rows = conn.execute("""
        SELECT drive, status, COUNT(*) as cnt
        FROM harvest_queue
        GROUP BY drive, status
        ORDER BY drive, status
    """).fetchall()
    current_drive = None
    for drive, status, cnt in rows:
        if drive != current_drive:
            print(f"\n  Drive {drive}:\\")
            current_drive = drive
        print(f"    {status:12s} {cnt:>8,}")

    # Top 10 next files to process
    print("\n--- Next 10 Files (by priority) ---")
    rows = conn.execute("""
        SELECT file_path, priority, phase, file_type
        FROM harvest_queue
        WHERE status = 'QUEUED'
        ORDER BY priority ASC, phase ASC, RANDOM()
        LIMIT 10
    """).fetchall()
    for fp, pri, phase, ft in rows:
        short = fp if len(fp) < 80 else '...' + fp[-77:]
        print(f"  P{pri} ph{phase} [{ft:4s}] {short}")

    return stats


# ── BATCH: Process next N files ──────────────────────────────────────────────

def cmd_batch(conn: sqlite3.Connection, batch_size: int = 25,
              phase_filter: str = None, priority_max: int = 7) -> dict:
    """Process next batch of files from harvest_queue."""
    from engines.harvest.extractor import extract_file
    from engines.harvest.classifier import classify_text
    from engines.harvest.analyzer import analyze_text

    stats = {'processed': 0, 'findings': 0, 'errors': 0, 'empty': 0,
             'evidence_inserted': 0, 'timeline_inserted': 0, 'impeachment_inserted': 0}

    batch_id = f"batch-{datetime.now().strftime('%H%M%S')}"

    # Build query
    where_clauses = ["status = 'QUEUED'", f"priority <= {priority_max}"]
    if phase_filter:
        where_clauses.append(f"phase = '{phase_filter}'")

    where = " AND ".join(where_clauses)
    query = f"""
        SELECT id, file_path, file_type, file_size, phase, priority
        FROM harvest_queue
        WHERE {where}
        ORDER BY priority ASC, phase ASC, RANDOM()
        LIMIT {batch_size}
    """

    rows = conn.execute(query).fetchall()
    if not rows:
        print("[BATCH] No QUEUED files matching criteria. Queue may be empty.")
        return stats

    print(f"[BATCH] Processing {len(rows)} files (session: {SESSION_ID}, batch: {batch_id})")

    # Load adaptive_insert
    try:
        from shared.adaptive_insert import adaptive_insert
        has_adaptive = True
    except ImportError:
        has_adaptive = False
        print("[WARN] adaptive_insert not available — using direct inserts")

    for row_id, file_path, file_type, file_size, phase, priority in rows:
        # Mark as PROCESSING
        conn.execute(
            "UPDATE harvest_queue SET status='PROCESSING', batch_id=?, session_id=? WHERE id=?",
            (batch_id, SESSION_ID, row_id)
        )
        conn.commit()

        findings = 0
        error_msg = None

        try:
            # Check file exists
            if not os.path.exists(file_path):
                conn.execute(
                    "UPDATE harvest_queue SET status='ERROR', error_msg='File not found', processed_at=datetime('now') WHERE id=?",
                    (row_id,)
                )
                stats['errors'] += 1
                continue

            # Extract text
            text = extract_file(file_path)
            if not text or len(text.strip()) < 20:
                conn.execute(
                    "UPDATE harvest_queue SET status='EMPTY', processed_at=datetime('now') WHERE id=?",
                    (row_id,)
                )
                stats['empty'] += 1
                continue

            # Classify
            classification = classify_text(text, file_path)

            # Analyze for impeachment/harm/patterns
            analysis = analyze_text(text, file_path)

            # Extract key quotes (sentences with high-value patterns)
            quotes = _extract_key_quotes(text, file_path, classification)

            # Persist findings
            if has_adaptive:
                findings = _persist_findings_adaptive(
                    conn, file_path, text, classification, analysis, quotes, stats
                )
            else:
                findings = _persist_findings_direct(
                    conn, file_path, text, classification, analysis, quotes, stats
                )

            # Mark HARVESTED
            conn.execute(
                """UPDATE harvest_queue
                   SET status='HARVESTED', findings_count=?, processed_at=datetime('now')
                   WHERE id=?""",
                (findings, row_id)
            )
            stats['processed'] += 1
            stats['findings'] += findings

            short_path = file_path if len(file_path) < 60 else '...' + file_path[-57:]
            print(f"  [{stats['processed']:>3}/{len(rows)}] {short_path} => {findings} findings (lane={classification.primary_lane})")

        except Exception as e:
            error_msg = str(e)[:200]
            conn.execute(
                "UPDATE harvest_queue SET status='ERROR', error_msg=?, processed_at=datetime('now') WHERE id=?",
                (error_msg, row_id)
            )
            stats['errors'] += 1
            logger.error("Error processing %s: %s", file_path, e)

        conn.commit()

    print(f"\n[BATCH] COMPLETE:")
    print(f"  Processed:  {stats['processed']}")
    print(f"  Findings:   {stats['findings']}")
    print(f"  Empty:      {stats['empty']}")
    print(f"  Errors:     {stats['errors']}")
    print(f"  Evidence:   {stats['evidence_inserted']}")
    print(f"  Timeline:   {stats['timeline_inserted']}")
    print(f"  Impeach:    {stats['impeachment_inserted']}")

    return stats


def _extract_key_quotes(text: str, file_path: str, classification) -> list:
    """Extract high-value sentences/paragraphs from text."""
    quotes = []

    # Split into sentences (rough)
    sentences = re.split(r'(?<=[.!?])\s+', text)

    # High-value patterns to look for
    HV_PATTERNS = [
        re.compile(r'(?:I\s+)?(?:swear|affirm|state|deny|admit|never|always)', re.I),
        re.compile(r'(?:order|judgment|sentence|grant|deny|sustain|overrule)', re.I),
        re.compile(r'(?:parenting\s+time|custody|visitation|contact)', re.I),
        re.compile(r'(?:ex\s+parte|without\s+(?:notice|hearing))', re.I),
        re.compile(r'(?:PPO|protection\s+order|stalking|harassment)', re.I),
        re.compile(r'(?:Watson|McNeill|Rusco|Berry|Pigors|Emily|Albert|Lori)', re.I),
        re.compile(r'(?:contempt|jail|incarcerat|arrest|charge)', re.I),
        re.compile(r'(?:false|fabricat|lie|perjur|mislead)', re.I),
        re.compile(r'(?:assault|abuse|threaten|danger|harm|violen)', re.I),
        re.compile(r'(?:meth|drug|substance|intoxicat|DUI)', re.I),
        re.compile(r'(?:MCR|MCL|MRE|USC|FRCP)\s+\d', re.I),
        re.compile(r'(?:evict|lockout|property|belongings|stolen)', re.I),
        re.compile(r'(?:Shady\s+Oaks|Garland|Whitehall|Norton)', re.I),
    ]

    for sent in sentences:
        sent = sent.strip()
        if len(sent) < 30 or len(sent) > 2000:
            continue
        for pattern in HV_PATTERNS:
            if pattern.search(sent):
                quotes.append(sent)
                break

    # Limit to top 20 quotes per file
    return quotes[:20]


def _persist_findings_adaptive(conn, file_path, text, classification, analysis, quotes, stats):
    """Persist findings using adaptive_insert (handles column mismatches)."""
    from shared.adaptive_insert import adaptive_insert
    findings = 0

    # Persist key quotes to evidence_quotes
    for quote in quotes:
        row = {
            'source_file': file_path,
            'quote_text': quote[:2000],
            'category': classification.doc_type,
            'lane': classification.primary_lane,
            'relevance_score': 7,
            'tags': ','.join([a[0] for a in classification.actors[:3]]),
        }
        try:
            adaptive_insert(conn, 'evidence_quotes', row)
            stats['evidence_inserted'] += 1
            findings += 1
        except Exception:
            pass

    # Persist dates as timeline events
    for date_str in classification.dates[:5]:
        row = {
            'event_date': date_str,
            'event_description': f"Event referenced in {os.path.basename(file_path)}",
            'actors': ','.join([a[0] for a in classification.actors[:3]]),
            'lane': classification.primary_lane,
            'category': classification.doc_type,
            'source_table': 'harvest_queue',
            'filing_relevance': file_path,
        }
        try:
            adaptive_insert(conn, 'timeline_events', row)
            stats['timeline_inserted'] += 1
            findings += 1
        except Exception:
            pass

    # Persist high-impeachment quotes
    if hasattr(analysis, 'impeachment_score') and analysis.impeachment_score >= 5:
        for quote in quotes[:3]:
            row = {
                'category': classification.doc_type,
                'evidence_summary': quote[:500],
                'source_file': file_path,
                'quote_text': quote[:2000],
                'impeachment_value': analysis.impeachment_score if hasattr(analysis, 'impeachment_score') else 5,
                'filing_relevance': classification.primary_lane,
            }
            try:
                adaptive_insert(conn, 'impeachment_matrix', row)
                stats['impeachment_inserted'] += 1
                findings += 1
            except Exception:
                pass

    return findings


def _persist_findings_direct(conn, file_path, text, classification, analysis, quotes, stats):
    """Persist findings using direct INSERT (fallback if adaptive_insert unavailable)."""
    findings = 0

    # Get evidence_quotes columns
    eq_cols = {r[1] for r in conn.execute("PRAGMA table_info(evidence_quotes)").fetchall()}

    for quote in quotes:
        cols_to_use = []
        vals = []
        if 'source_file' in eq_cols:
            cols_to_use.append('source_file')
            vals.append(file_path)
        if 'quote_text' in eq_cols:
            cols_to_use.append('quote_text')
            vals.append(quote[:2000])
        if 'category' in eq_cols:
            cols_to_use.append('category')
            vals.append(classification.doc_type)
        if 'lane' in eq_cols:
            cols_to_use.append('lane')
            vals.append(classification.primary_lane)
        if 'relevance_score' in eq_cols:
            cols_to_use.append('relevance_score')
            vals.append(7)

        if cols_to_use:
            placeholders = ','.join(['?'] * len(cols_to_use))
            col_names = ','.join(cols_to_use)
            try:
                conn.execute(
                    f"INSERT INTO evidence_quotes ({col_names}) VALUES ({placeholders})",
                    tuple(vals)
                )
                stats['evidence_inserted'] += 1
                findings += 1
            except sqlite3.IntegrityError:
                pass
            except sqlite3.Error as e:
                logger.error("Direct insert error: %s", e)

    conn.commit()
    return findings


# ── WIZTREE: Supplement queue from WizTree CSV ───────────────────────────────

def cmd_wiztree(conn: sqlite3.Connection, wiztree_path: str) -> dict:
    """Stream WizTree CSV and add missing files to harvest_queue."""
    stats = {'scanned': 0, 'inserted': 0, 'skipped': 0, 'errors': 0}

    if not os.path.exists(wiztree_path):
        print(f"[ERROR] WizTree file not found: {wiztree_path}")
        return stats

    # Get existing paths in queue for fast dedup
    print("[WIZTREE] Loading existing queue paths for dedup...")
    existing_paths: Set[str] = set()
    rows = conn.execute("SELECT file_path FROM harvest_queue").fetchall()
    existing_paths = {r[0] for r in rows}
    print(f"[WIZTREE] {len(existing_paths):,} paths already in queue")

    # Also get kraken_processed paths
    try:
        rows = conn.execute("SELECT file_path FROM kraken_processed").fetchall()
        processed_paths = {r[0] for r in rows}
    except sqlite3.OperationalError:
        processed_paths = set()

    print(f"[WIZTREE] Streaming WizTree CSV: {wiztree_path}")
    batch = []
    batch_size = 5000

    try:
        with open(wiztree_path, 'r', encoding='utf-8', errors='replace') as f:
            # Skip WizTree header comment line
            first_line = f.readline()
            if not first_line.startswith('"File Name"'):
                # It's a comment line, read the actual header
                header_line = f.readline()
            else:
                header_line = first_line

            reader = csv.reader(f)

            for row in reader:
                if not row or len(row) < 17:
                    continue

                stats['scanned'] += 1
                file_path = row[0].strip('"')

                # Skip directories (they have Files/Folders counts)
                attributes = row[4] if len(row) > 4 else ''
                if 'd' in attributes.lower() or 'D' in attributes:
                    continue

                # Get extension
                file_ext = row[16].strip('"').lower() if len(row) > 16 else ''
                if not file_ext:
                    _, ext = os.path.splitext(file_path)
                    file_ext = ext.lower().lstrip('.')

                if file_ext not in {'pdf', 'txt', 'md', 'docx', 'csv', 'html', 'json'}:
                    continue

                if is_excluded(file_path):
                    stats['skipped'] += 1
                    continue

                if file_path in existing_paths or file_path in processed_paths:
                    stats['skipped'] += 1
                    continue

                # Get file size
                try:
                    file_size = int(row[1].strip('"').replace(',', '')) if row[1] else 0
                except ValueError:
                    file_size = 0

                phase = PHASE_MAP.get(file_ext, PHASE_MAP.get('.' + file_ext, '6'))
                priority = assign_priority(file_path)
                drive = get_drive(file_path)

                batch.append((file_path, drive, file_ext, file_size, phase, priority))
                existing_paths.add(file_path)  # Prevent intra-batch dupes

                if len(batch) >= batch_size:
                    inserted = _flush_batch(conn, batch)
                    stats['inserted'] += inserted
                    batch = []
                    if stats['scanned'] % 100000 == 0:
                        print(f"  ... {stats['scanned']:,} scanned, {stats['inserted']:,} new files added")

    except Exception as e:
        print(f"[ERROR] WizTree parsing error: {e}")
        stats['errors'] += 1

    # Final flush
    if batch:
        inserted = _flush_batch(conn, batch)
        stats['inserted'] += inserted

    print(f"\n[WIZTREE] COMPLETE:")
    print(f"  Scanned:  {stats['scanned']:,}")
    print(f"  Inserted: {stats['inserted']:,}")
    print(f"  Skipped:  {stats['skipped']:,}")
    print(f"  Errors:   {stats['errors']}")

    return stats


# ── PASSDOWN: Generate session handoff document ──────────────────────────────

def cmd_passdown(conn: sqlite3.Connection, output_path: str = None) -> str:
    """Generate a passdown .md for session handoff."""
    now = datetime.now().strftime('%Y-%m-%d %H:%M')

    # Gather stats
    status_rows = conn.execute(
        "SELECT status, COUNT(*) FROM harvest_queue GROUP BY status"
    ).fetchall()
    status_map = {s: c for s, c in status_rows}

    phase_rows = conn.execute(
        "SELECT phase, status, COUNT(*) FROM harvest_queue GROUP BY phase, status ORDER BY phase, status"
    ).fetchall()

    # DB stats
    db_stats = {}
    for table in ['evidence_quotes', 'timeline_events', 'impeachment_matrix',
                   'authority_chains_v2', 'michigan_rules_extracted']:
        try:
            row = conn.execute(f"SELECT COUNT(*) FROM {table}").fetchone()
            db_stats[table] = row[0]
        except sqlite3.OperationalError:
            db_stats[table] = 'N/A'

    # Recent findings
    recent = conn.execute("""
        SELECT file_path, findings_count, processed_at
        FROM harvest_queue
        WHERE status = 'HARVESTED' AND findings_count > 0
        ORDER BY processed_at DESC LIMIT 10
    """).fetchall()

    total = sum(status_map.values()) if status_map else 0
    queued = status_map.get('QUEUED', 0)
    harvested = status_map.get('HARVESTED', 0)
    errors = status_map.get('ERROR', 0)

    # Build passdown
    lines = [
        f"# INFINITE HARVEST PASSDOWN - Session {SESSION_ID}",
        f"## Date: {now}",
        f"## Total Queue: {total:,} files",
        f"## Harvested: {harvested:,} | Queued: {queued:,} | Errors: {errors}",
        "",
        "## Queue Status",
        "| Status | Count |",
        "|--------|-------|",
    ]
    for status, cnt in sorted(status_map.items()):
        lines.append(f"| {status} | {cnt:,} |")

    lines.extend(["", "## Phase Breakdown",
                   "| Phase | Status | Count |",
                   "|-------|--------|-------|"])
    for phase, status, cnt in phase_rows:
        lines.append(f"| {phase} | {status} | {cnt:,} |")

    lines.extend(["", "## DB Stats After Session",
                   "| Table | Rows |",
                   "|-------|------|"])
    for table, cnt in db_stats.items():
        lines.append(f"| {table} | {cnt:,} |" if isinstance(cnt, int) else f"| {table} | {cnt} |")

    if recent:
        lines.extend(["", "## Recent Findings"])
        for fp, fc, pa in recent:
            short = os.path.basename(fp)
            lines.append(f"- {short}: {fc} findings ({pa})")

    lines.extend([
        "",
        "## Next Session Should",
        f"1. Resume from harvest_queue WHERE status='QUEUED' ORDER BY priority ASC",
        f"2. Queued files remaining: {queued:,}",
        f"3. Focus on P0-P2 files first (highest priority evidence + legal authority)",
    ])

    passdown_text = '\n'.join(lines)

    if output_path:
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(passdown_text)
        print(f"[PASSDOWN] Written to {output_path}")
    else:
        print(passdown_text)

    return passdown_text


# ── CLI Entry Point ──────────────────────────────────────────────────────────

def main():
    """CLI entry point."""
    logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')

    if len(sys.argv) < 2:
        print(__doc__)
        return

    command = sys.argv[1].lower()
    conn = get_connection()

    try:
        if command == 'init':
            cmd_init(conn)

        elif command == 'status':
            cmd_status(conn)

        elif command == 'batch':
            batch_size = 25
            phase_filter = None
            priority_max = 7

            i = 2
            while i < len(sys.argv):
                arg = sys.argv[i]
                if arg.isdigit():
                    batch_size = int(arg)
                elif arg == '--phase' and i + 1 < len(sys.argv):
                    phase_filter = sys.argv[i + 1]
                    i += 1
                elif arg == '--priority' and i + 1 < len(sys.argv):
                    priority_max = int(sys.argv[i + 1])
                    i += 1
                i += 1

            cmd_batch(conn, batch_size, phase_filter, priority_max)

        elif command == 'wiztree':
            if len(sys.argv) < 3:
                print("Usage: infinite_harvest.py wiztree <path_to_wiztree_csv>")
                return
            cmd_wiztree(conn, sys.argv[2])

        elif command == 'passdown':
            output = sys.argv[2] if len(sys.argv) > 2 else None
            cmd_passdown(conn, output)

        else:
            print(f"Unknown command: {command}")
            print(__doc__)

    finally:
        conn.close()


if __name__ == '__main__':
    main()
