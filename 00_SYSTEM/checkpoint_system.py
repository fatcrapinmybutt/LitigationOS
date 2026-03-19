#!/usr/bin/env python3
"""
LitigationOS Evidence Checkpoint System v2.0
=============================================
Prevents data loss by persisting session evidence to disk.
AUTO-SAVES every 40KB of new data (configurable via AUTOSAVE_THRESHOLD_KB).

Usage:
    python 00_SYSTEM/checkpoint_system.py save           # Save session to disk
    python 00_SYSTEM/checkpoint_system.py load            # Load disk and show stats
    python 00_SYSTEM/checkpoint_system.py export-catalog  # Regenerate MASTER_EVIDENCE_CATALOG.md
    python 00_SYSTEM/checkpoint_system.py import-json FILE# Import from JSON backup
    python 00_SYSTEM/checkpoint_system.py watch           # Auto-save daemon (monitors JSON size)
    python 00_SYSTEM/checkpoint_system.py restore         # Restore latest checkpoint to JSON
    python 00_SYSTEM/checkpoint_system.py --help

Persistence chain:
    Session SQL -> evidence_checkpoint.json (live buffer)
        -> evidence_checkpoint.db (SQLite on disk, auto-saved every 40KB)
        -> MASTER_EVIDENCE_CATALOG.md (regenerated on each save)
        -> backups/evidence_checkpoints/ (timestamped snapshots)

Integrated into LitigationOS:
    - startup hook loads last checkpoint on session start
    - auto-save triggers on 40KB growth threshold
    - crash recovery from any checkpoint in the backup chain
"""
import sys
import os
import json
import sqlite3
import hashlib
import time
import threading
from datetime import datetime, timezone
from pathlib import Path

# Fix Windows encoding
sys.stdout = open(sys.stdout.fileno(), mode='w', encoding='utf-8', errors='replace')

# === PATHS ===
BASE = Path(r"C:\Users\andre\LitigationOS")
CHECKPOINT_DB = BASE / "00_SYSTEM" / "evidence_checkpoint.db"
CHECKPOINT_JSON = BASE / "00_SYSTEM" / "evidence_checkpoint.json"
CATALOG_MD = BASE / "05_ANALYSIS" / "MASTER_EVIDENCE_CATALOG.md"
CHECKPOINT_LOG = BASE / "00_SYSTEM" / "CHECKPOINT_LOG.md"
BACKUP_DIR = BASE / "00_SYSTEM" / "backups" / "evidence_checkpoints"
AUTOSAVE_STATE = BASE / "00_SYSTEM" / "checkpoint_autosave_state.json"

# === AUTO-SAVE CONFIG ===
AUTOSAVE_THRESHOLD_KB = 40  # Save every 40KB of new data
AUTOSAVE_POLL_SECONDS = 15  # Check for changes every 15 seconds
AUTOSAVE_MAX_INTERVAL = 600  # Force save every 10 minutes regardless

# === DB PRAGMAS (EAGAIN prevention) ===
PRAGMAS = """
PRAGMA busy_timeout=60000;
PRAGMA journal_mode=WAL;
PRAGMA cache_size=-32000;
PRAGMA synchronous=NORMAL;
"""

SCHEMA = """
CREATE TABLE IF NOT EXISTS evidence_findings (
    id TEXT PRIMARY KEY,
    category TEXT NOT NULL,
    severity TEXT NOT NULL,
    source_file TEXT DEFAULT '',
    source_line INTEGER DEFAULT 0,
    quote TEXT NOT NULL,
    legal_significance TEXT NOT NULL,
    lane TEXT NOT NULL,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    checkpoint_ts DATETIME DEFAULT CURRENT_TIMESTAMP,
    sha256 TEXT DEFAULT ''
);

CREATE TABLE IF NOT EXISTS checkpoint_meta (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    timestamp TEXT NOT NULL,
    total_findings INTEGER NOT NULL,
    nuclear_count INTEGER NOT NULL,
    critical_count INTEGER NOT NULL,
    high_count INTEGER NOT NULL,
    source TEXT NOT NULL,
    notes TEXT DEFAULT ''
);

CREATE INDEX IF NOT EXISTS idx_severity ON evidence_findings(severity);
CREATE INDEX IF NOT EXISTS idx_category ON evidence_findings(category);
CREATE INDEX IF NOT EXISTS idx_lane ON evidence_findings(lane);
"""


def get_db():
    """Get checkpoint DB connection with EAGAIN-safe pragmas."""
    conn = sqlite3.connect(str(CHECKPOINT_DB), timeout=120)
    conn.executescript(PRAGMAS)
    conn.executescript(SCHEMA)
    conn.row_factory = sqlite3.Row
    return conn


def hash_finding(row):
    """Content hash for dedup — based on quote + legal_significance."""
    content = f"{row['quote']}|{row['legal_significance']}"
    return hashlib.sha256(content.encode('utf-8', errors='replace')).hexdigest()[:16]


def save_from_json(json_path):
    """Import findings from a JSON file into checkpoint DB."""
    with open(json_path, 'r', encoding='utf-8-sig') as f:
        findings = json.load(f)

    if isinstance(findings, str):
        findings = json.loads(findings)

    db = get_db()
    inserted = 0
    updated = 0
    now = datetime.now(timezone.utc).isoformat()

    for row in findings:
        sha = hashlib.sha256(
            f"{row.get('quote','')}|{row.get('legal_significance','')}".encode('utf-8', errors='replace')
        ).hexdigest()[:16]

        existing = db.execute("SELECT id FROM evidence_findings WHERE id = ?", (row['id'],)).fetchone()
        if existing:
            # Update if content changed
            db.execute("""
                UPDATE evidence_findings SET
                    category=?, severity=?, source_file=?, source_line=?,
                    quote=?, legal_significance=?, lane=?, checkpoint_ts=?, sha256=?
                WHERE id=?
            """, (
                row.get('category', ''), row.get('severity', ''),
                row.get('source_file', ''), row.get('source_line', 0),
                row.get('quote', ''), row.get('legal_significance', ''),
                row.get('lane', ''), now, sha, row['id']
            ))
            updated += 1
        else:
            db.execute("""
                INSERT INTO evidence_findings
                    (id, category, severity, source_file, source_line, quote, legal_significance, lane, created_at, checkpoint_ts, sha256)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                row['id'], row.get('category', ''), row.get('severity', ''),
                row.get('source_file', ''), row.get('source_line', 0),
                row.get('quote', ''), row.get('legal_significance', ''),
                row.get('lane', ''), row.get('created_at', now), now, sha
            ))
            inserted += 1

    # Log checkpoint
    counts = db.execute("""
        SELECT COUNT(*) as total,
            SUM(CASE WHEN severity='NUCLEAR' THEN 1 ELSE 0 END) as nuclear,
            SUM(CASE WHEN severity='CRITICAL' THEN 1 ELSE 0 END) as critical,
            SUM(CASE WHEN severity='HIGH' THEN 1 ELSE 0 END) as high
        FROM evidence_findings
    """).fetchone()

    db.execute("""
        INSERT INTO checkpoint_meta (timestamp, total_findings, nuclear_count, critical_count, high_count, source, notes)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    """, (now, counts['total'], counts['nuclear'], counts['critical'], counts['high'],
          f"json_import:{json_path}", f"inserted={inserted} updated={updated}"))

    db.commit()
    db.close()

    # Create timestamped backup
    BACKUP_DIR.mkdir(parents=True, exist_ok=True)
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_path = BACKUP_DIR / f"evidence_{ts}.json"
    import shutil
    shutil.copy2(json_path, str(backup_path))

    _append_checkpoint_log(ts, counts['total'], counts['nuclear'] or 0, counts['critical'] or 0,
                           counts['high'] or 0, inserted, updated, f"json_import:{Path(json_path).name}")

    return inserted, updated, counts['total']


def save_checkpoint(findings_data, source="session_sql"):
    """
    Save evidence findings to checkpoint DB + JSON backup.
    findings_data: list of dicts with keys matching schema.
    Returns (inserted, updated, total).
    """
    # Write JSON backup first (atomic — always succeeds)
    BACKUP_DIR.mkdir(parents=True, exist_ok=True)
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_path = BACKUP_DIR / f"evidence_{ts}.json"
    with open(backup_path, 'w', encoding='utf-8') as f:
        json.dump(findings_data, f, indent=2, ensure_ascii=False, default=str)

    # Also write to canonical JSON location
    with open(CHECKPOINT_JSON, 'w', encoding='utf-8') as f:
        json.dump(findings_data, f, indent=2, ensure_ascii=False, default=str)

    # Now persist to SQLite
    db = get_db()
    inserted = 0
    updated = 0
    now = datetime.now(timezone.utc).isoformat()

    for row in findings_data:
        sha = hashlib.sha256(
            f"{row.get('quote','')}|{row.get('legal_significance','')}".encode('utf-8', errors='replace')
        ).hexdigest()[:16]

        existing = db.execute("SELECT sha256 FROM evidence_findings WHERE id = ?", (row['id'],)).fetchone()
        if existing:
            if existing['sha256'] != sha:
                db.execute("""
                    UPDATE evidence_findings SET
                        category=?, severity=?, source_file=?, source_line=?,
                        quote=?, legal_significance=?, lane=?, checkpoint_ts=?, sha256=?
                    WHERE id=?
                """, (
                    row.get('category', ''), row.get('severity', ''),
                    row.get('source_file', ''), row.get('source_line', 0),
                    row.get('quote', ''), row.get('legal_significance', ''),
                    row.get('lane', ''), now, sha, row['id']
                ))
                updated += 1
        else:
            db.execute("""
                INSERT INTO evidence_findings
                    (id, category, severity, source_file, source_line, quote, legal_significance, lane, created_at, checkpoint_ts, sha256)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                row['id'], row.get('category', ''), row.get('severity', ''),
                row.get('source_file', ''), row.get('source_line', 0),
                row.get('quote', ''), row.get('legal_significance', ''),
                row.get('lane', ''), row.get('created_at', now), now, sha
            ))
            inserted += 1

    counts = db.execute("""
        SELECT COUNT(*) as total,
            SUM(CASE WHEN severity='NUCLEAR' THEN 1 ELSE 0 END) as nuclear,
            SUM(CASE WHEN severity='CRITICAL' THEN 1 ELSE 0 END) as critical,
            SUM(CASE WHEN severity='HIGH' THEN 1 ELSE 0 END) as high
        FROM evidence_findings
    """).fetchone()

    db.execute("""
        INSERT INTO checkpoint_meta (timestamp, total_findings, nuclear_count, critical_count, high_count, source, notes)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    """, (now, counts['total'], counts['nuclear'], counts['critical'], counts['high'],
          source, f"inserted={inserted} updated={updated} backup={backup_path.name}"))

    db.commit()
    db.close()

    # Append to checkpoint log
    _append_checkpoint_log(ts, counts['total'], counts['nuclear'], counts['critical'],
                           counts['high'], inserted, updated, source)

    return inserted, updated, counts['total']


def load_checkpoint():
    """Load all findings from checkpoint DB. Returns list of dicts."""
    if not CHECKPOINT_DB.exists():
        # Try JSON fallback
        if CHECKPOINT_JSON.exists():
            with open(CHECKPOINT_JSON, 'r', encoding='utf-8') as f:
                return json.load(f)
        return []

    db = get_db()
    rows = db.execute("SELECT * FROM evidence_findings ORDER BY id").fetchall()
    findings = [dict(r) for r in rows]
    db.close()
    return findings


def get_stats():
    """Get checkpoint statistics."""
    if not CHECKPOINT_DB.exists():
        return {"total": 0, "nuclear": 0, "critical": 0, "high": 0, "checkpoints": 0}

    db = get_db()
    counts = db.execute("""
        SELECT COUNT(*) as total,
            SUM(CASE WHEN severity='NUCLEAR' THEN 1 ELSE 0 END) as nuclear,
            SUM(CASE WHEN severity='CRITICAL' THEN 1 ELSE 0 END) as critical,
            SUM(CASE WHEN severity='HIGH' THEN 1 ELSE 0 END) as high
        FROM evidence_findings
    """).fetchone()

    meta = db.execute("SELECT COUNT(*) as cnt FROM checkpoint_meta").fetchone()
    last = db.execute("SELECT * FROM checkpoint_meta ORDER BY id DESC LIMIT 1").fetchone()

    db.close()
    return {
        "total": counts['total'],
        "nuclear": counts['nuclear'],
        "critical": counts['critical'],
        "high": counts['high'],
        "checkpoints": meta['cnt'],
        "last_checkpoint": dict(last) if last else None,
        "db_path": str(CHECKPOINT_DB),
        "db_size_kb": CHECKPOINT_DB.stat().st_size // 1024 if CHECKPOINT_DB.exists() else 0
    }


def export_catalog():
    """Regenerate MASTER_EVIDENCE_CATALOG.md from checkpoint DB."""
    findings = load_checkpoint()
    if not findings:
        print("ERROR: No findings in checkpoint DB. Run 'save' first.")
        return False

    # Calculate days since separation
    sep_date = datetime(2025, 8, 8)
    days = (datetime.now() - sep_date).days

    # Group by severity
    nuclear = [f for f in findings if f.get('severity') == 'NUCLEAR']
    critical = [f for f in findings if f.get('severity') == 'CRITICAL']
    high = [f for f in findings if f.get('severity') == 'HIGH']

    # Group by category
    categories = {}
    for f in findings:
        cat = f.get('category', 'UNCATEGORIZED')
        categories.setdefault(cat, []).append(f)

    # Group by lane
    lanes = {'A': 0, 'B': 0, 'D': 0, 'E': 0, 'F': 0}
    for f in findings:
        for lane in f.get('lane', '').split(','):
            lane = lane.strip()
            if lane in lanes:
                lanes[lane] += 1

    lines = []
    lines.append("# MASTER EVIDENCE CATALOG — Pigors v. Watson")
    lines.append("## Case No. 2024-001507-DC | 14th Circuit Court, Muskegon County, Michigan")
    lines.append("")
    lines.append(f"**Generated:** {datetime.now().strftime('%Y-%m-%d %H:%M')} (auto-generated by checkpoint_system.py)")
    lines.append(f"**Parent-Child Separation:** {days} consecutive days (since Aug 8, 2025)")
    lines.append(f"**Total Evidence Findings:** {len(findings)}")
    lines.append(f"**Severity Breakdown:** {len(nuclear)} NUCLEAR | {len(critical)} CRITICAL | {len(high)} HIGH")
    lines.append(f"**Sources:** Police reports, court filings, HealthWest evaluations, AppClose records, text messages, MEGA brief, evidence atoms, orders journal, prosecution timeline, PPO timeline")
    lines.append(f"**Checkpoint DB:** `{CHECKPOINT_DB}` ({CHECKPOINT_DB.stat().st_size // 1024}KB)")
    lines.append("")
    lines.append("---")
    lines.append("")
    lines.append("## ⚠️ PRIVILEGED WORK PRODUCT — NOT FOR FILING")
    lines.append("")
    lines.append("This document is attorney work product / litigation strategy. It catalogs evidence findings for internal use only.")
    lines.append("")
    lines.append("---")
    lines.append("")
    lines.append("## 🔴 SEVERITY LEGEND")
    lines.append("")
    lines.append("| Level | Count | Meaning |")
    lines.append("|-------|-------|---------|")
    lines.append(f"| **NUCLEAR** | {len(nuclear)} | Case-dispositive. Single finding sufficient to win motion/appeal. |")
    lines.append(f"| **CRITICAL** | {len(critical)} | Strongly supports claims. Important corroborating evidence. |")
    lines.append(f"| **HIGH** | {len(high)} | Relevant supporting evidence. Strengthens pattern arguments. |")
    lines.append("")
    lines.append("---")
    lines.append("")

    # Lane distribution
    lines.append("## 📊 LANE DISTRIBUTION")
    lines.append("")
    lines.append("| Lane | Count | Subject |")
    lines.append("|------|-------|---------|")
    lines.append(f"| **A** | {lanes['A']} | Watson custody (2024-001507-DC) |")
    lines.append(f"| **B** | {lanes['B']} | Shady Oaks housing (2025-002760-CZ) |")
    lines.append(f"| **D** | {lanes['D']} | PPO / Protection Orders |")
    lines.append(f"| **E** | {lanes['E']} | Judicial Misconduct / JTC |")
    lines.append(f"| **F** | {lanes['F']} | Appellate (COA/MSC) |")
    lines.append("")
    lines.append("---")
    lines.append("")

    # Category summary
    lines.append("## 📋 CATEGORY SUMMARY")
    lines.append("")
    lines.append("| Category | Count | Nuclear | Critical | High |")
    lines.append("|----------|-------|---------|----------|------|")
    for cat in sorted(categories.keys()):
        items = categories[cat]
        n = sum(1 for i in items if i.get('severity') == 'NUCLEAR')
        c = sum(1 for i in items if i.get('severity') == 'CRITICAL')
        h = sum(1 for i in items if i.get('severity') == 'HIGH')
        lines.append(f"| {cat} | {len(items)} | {n} | {c} | {h} |")
    lines.append("")
    lines.append("---")
    lines.append("")

    # Full findings by severity
    for severity, label, emoji in [
        ('NUCLEAR', 'NUCLEAR FINDINGS', '🔴'),
        ('CRITICAL', 'CRITICAL FINDINGS', '🟠'),
        ('HIGH', 'HIGH FINDINGS', '🟡')
    ]:
        group = [f for f in findings if f.get('severity') == severity]
        if not group:
            continue

        lines.append(f"## {emoji} {label} ({len(group)})")
        lines.append("")

        # Sub-group by category
        cat_groups = {}
        for f in group:
            cat_groups.setdefault(f.get('category', 'OTHER'), []).append(f)

        for cat in sorted(cat_groups.keys()):
            lines.append(f"### {cat}")
            lines.append("")
            for f in cat_groups[cat]:
                src = f.get('source_file', '')
                line_num = f.get('source_line', '')
                src_str = f"{src}" + (f" line {line_num}" if line_num else "")
                lines.append(f"**{f['id']}** | {src_str} | Lane: {f.get('lane', '?')}")
                lines.append(f"> {f.get('quote', 'N/A')}")
                lines.append(f"")
                lines.append(f"*Legal significance:* {f.get('legal_significance', 'N/A')}")
                lines.append("")

        lines.append("---")
        lines.append("")

    # Write catalog
    with open(CATALOG_MD, 'w', encoding='utf-8') as f:
        f.write('\n'.join(lines))

    print(f"CATALOG EXPORTED: {CATALOG_MD}")
    print(f"  {len(findings)} findings | {len(nuclear)} NUCLEAR | {len(critical)} CRITICAL | {len(high)} HIGH")
    return True


def _append_checkpoint_log(ts, total, nuclear, critical, high, inserted, updated, source):
    """Append entry to CHECKPOINT_LOG.md."""
    entry = f"| {ts} | {total} | {nuclear} | {critical} | {high} | +{inserted} ~{updated} | {source} |\n"
    if not CHECKPOINT_LOG.exists():
        with open(CHECKPOINT_LOG, 'w', encoding='utf-8') as f:
            f.write("# Evidence Checkpoint Log\n\n")
            f.write("| Timestamp | Total | Nuclear | Critical | High | Changes | Source |\n")
            f.write("|-----------|-------|---------|----------|------|---------|--------|\n")
            f.write(entry)
    else:
        with open(CHECKPOINT_LOG, 'a', encoding='utf-8') as f:
            f.write(entry)


def save_from_stdin():
    """Read JSON from stdin and save to checkpoint."""
    data = json.load(sys.stdin)
    if isinstance(data, str):
        data = json.loads(data)
    inserted, updated, total = save_checkpoint(data, source="stdin_pipe")
    print(f"CHECKPOINT SAVED: {total} total ({inserted} new, {updated} updated)")


# === AUTO-SAVE ENGINE (40KB threshold) ===

def _load_autosave_state():
    """Load the last known file size for threshold tracking."""
    if AUTOSAVE_STATE.exists():
        try:
            with open(AUTOSAVE_STATE, 'r', encoding='utf-8') as f:
                return json.load(f)
        except:
            pass
    return {"last_size_bytes": 0, "last_save_ts": 0, "saves_count": 0}


def _save_autosave_state(state):
    """Persist autosave state tracker."""
    with open(AUTOSAVE_STATE, 'w', encoding='utf-8') as f:
        json.dump(state, f, indent=2)


def check_autosave_threshold():
    """
    Check if evidence_checkpoint.json has grown by >= 40KB since last save.
    If yes, trigger a save to SQLite DB + backup + catalog regeneration.
    Returns True if save was triggered.
    """
    if not CHECKPOINT_JSON.exists():
        return False

    current_size = CHECKPOINT_JSON.stat().st_size
    state = _load_autosave_state()
    last_size = state.get("last_size_bytes", 0)
    last_ts = state.get("last_save_ts", 0)
    now = time.time()

    growth_bytes = current_size - last_size
    growth_kb = growth_bytes / 1024
    elapsed = now - last_ts

    # Trigger if: grew by 40KB+ OR 10 minutes elapsed with ANY growth
    should_save = (
        (growth_kb >= AUTOSAVE_THRESHOLD_KB) or
        (elapsed >= AUTOSAVE_MAX_INTERVAL and growth_bytes > 0)
    )

    if should_save:
        print(f"[AUTOSAVE] Triggered: +{growth_kb:.1f}KB growth, {elapsed:.0f}s elapsed")
        try:
            inserted, updated, total = save_from_json(str(CHECKPOINT_JSON))
            export_catalog()  # Regenerate catalog on every autosave
            state["last_size_bytes"] = current_size
            state["last_save_ts"] = now
            state["saves_count"] = state.get("saves_count", 0) + 1
            _save_autosave_state(state)
            print(f"[AUTOSAVE] Saved: {total} findings ({inserted} new, {updated} updated) | Save #{state['saves_count']}")
            return True
        except Exception as e:
            print(f"[AUTOSAVE] ERROR: {e}")
            return False

    return False


def watch_autosave():
    """
    Daemon loop: poll evidence_checkpoint.json every 15s.
    Save to DB + backup when 40KB growth detected.
    """
    print(f"[AUTOSAVE WATCH] Started — threshold: {AUTOSAVE_THRESHOLD_KB}KB, poll: {AUTOSAVE_POLL_SECONDS}s")
    print(f"[AUTOSAVE WATCH] Monitoring: {CHECKPOINT_JSON}")
    print(f"[AUTOSAVE WATCH] DB target: {CHECKPOINT_DB}")
    print(f"[AUTOSAVE WATCH] Press Ctrl+C to stop")
    print()

    # Initialize state if needed
    state = _load_autosave_state()
    if CHECKPOINT_JSON.exists() and state.get("last_size_bytes", 0) == 0:
        state["last_size_bytes"] = CHECKPOINT_JSON.stat().st_size
        state["last_save_ts"] = time.time()
        _save_autosave_state(state)

    try:
        while True:
            saved = check_autosave_threshold()
            if saved:
                print(f"[AUTOSAVE WATCH] Checkpoint saved at {datetime.now().strftime('%H:%M:%S')}")
            time.sleep(AUTOSAVE_POLL_SECONDS)
    except KeyboardInterrupt:
        print("\n[AUTOSAVE WATCH] Stopped by user")
        # Final save on exit
        if CHECKPOINT_JSON.exists():
            check_autosave_threshold()


def restore_latest():
    """Restore from the latest backup to evidence_checkpoint.json."""
    BACKUP_DIR.mkdir(parents=True, exist_ok=True)

    # Try DB first
    if CHECKPOINT_DB.exists():
        findings = load_checkpoint()
        if findings:
            with open(CHECKPOINT_JSON, 'w', encoding='utf-8') as f:
                json.dump(findings, f, indent=2, ensure_ascii=False, default=str)
            print(f"RESTORED from DB: {len(findings)} findings -> {CHECKPOINT_JSON}")
            return True

    # Try backup JSONs
    backups = sorted(BACKUP_DIR.glob("evidence_*.json"), reverse=True)
    if backups:
        import shutil
        latest = backups[0]
        shutil.copy2(str(latest), str(CHECKPOINT_JSON))
        with open(latest, 'r', encoding='utf-8-sig') as f:
            data = json.load(f)
        count = len(data) if isinstance(data, list) else 0
        print(f"RESTORED from backup: {latest.name} ({count} findings) -> {CHECKPOINT_JSON}")
        return True

    # Try backup DBs
    db_backups = sorted(BACKUP_DIR.glob("evidence_*.db"), reverse=True)
    if db_backups:
        import shutil
        shutil.copy2(str(db_backups[0]), str(CHECKPOINT_DB))
        findings = load_checkpoint()
        with open(CHECKPOINT_JSON, 'w', encoding='utf-8') as f:
            json.dump(findings, f, indent=2, ensure_ascii=False, default=str)
        print(f"RESTORED from DB backup: {db_backups[0].name} ({len(findings)} findings)")
        return True

    print("ERROR: No checkpoint data found anywhere. Nothing to restore.")
    return False


def quick_save_hook():
    """
    Called by agents/pipeline after every batch operation.
    Checks 40KB threshold and auto-saves if needed.
    Non-blocking, safe to call frequently.
    """
    return check_autosave_threshold()


# === CLI ===
def main():
    if len(sys.argv) < 2 or sys.argv[1] == '--help':
        print(__doc__)
        return 0

    cmd = sys.argv[1].lower()

    if cmd == 'save':
        # Try to load from JSON if it exists, or prompt for stdin
        if CHECKPOINT_JSON.exists():
            inserted, updated, total = save_from_json(str(CHECKPOINT_JSON))
            export_catalog()  # Always regenerate catalog on explicit save
            print(f"CHECKPOINT SAVED from JSON: {total} total ({inserted} new, {updated} updated)")
        else:
            print("No JSON backup found. Pipe data via stdin or use import-json.")
            return 1

    elif cmd == 'load':
        stats = get_stats()
        print(f"CHECKPOINT DB: {stats['db_path']}")
        print(f"  Size: {stats['db_size_kb']}KB")
        print(f"  Total findings: {stats['total']}")
        print(f"  NUCLEAR: {stats['nuclear']} | CRITICAL: {stats['critical']} | HIGH: {stats['high']}")
        print(f"  Total checkpoints: {stats['checkpoints']}")
        if stats.get('last_checkpoint'):
            lc = stats['last_checkpoint']
            print(f"  Last checkpoint: {lc.get('timestamp', 'N/A')} ({lc.get('notes', '')})")

    elif cmd == 'export-catalog':
        export_catalog()

    elif cmd == 'import-json':
        if len(sys.argv) < 3:
            print("Usage: checkpoint_system.py import-json FILE.json")
            return 1
        path = sys.argv[2]
        inserted, updated, total = save_from_json(path)
        export_catalog()
        print(f"IMPORTED: {total} total ({inserted} new, {updated} updated)")

    elif cmd == 'backup-list':
        BACKUP_DIR.mkdir(parents=True, exist_ok=True)
        backups_json = sorted(BACKUP_DIR.glob("evidence_*.json"), reverse=True)
        backups_db = sorted(BACKUP_DIR.glob("evidence_*.db"), reverse=True)
        print(f"Backups in {BACKUP_DIR}:")
        for b in backups_json[:10]:
            size = b.stat().st_size // 1024
            print(f"  [JSON] {b.name} ({size}KB)")
        for b in backups_db[:10]:
            size = b.stat().st_size // 1024
            print(f"  [DB]   {b.name} ({size}KB)")
        print(f"Total: {len(backups_json)} JSON + {len(backups_db)} DB backups")

    elif cmd == 'watch':
        watch_autosave()

    elif cmd == 'restore':
        restore_latest()

    elif cmd == 'check':
        # Silent threshold check — for pipeline integration
        if check_autosave_threshold():
            print("AUTOSAVE: triggered")
        else:
            print("AUTOSAVE: not needed")

    elif cmd == 'status':
        # Quick status for dashboard integration
        stats = get_stats()
        state = _load_autosave_state()
        json_size = CHECKPOINT_JSON.stat().st_size // 1024 if CHECKPOINT_JSON.exists() else 0
        last_size = state.get("last_size_bytes", 0) // 1024
        growth = json_size - last_size
        print(f"Evidence: {stats['total']} ({stats['nuclear']}N/{stats['critical']}C/{stats['high']}H)")
        print(f"JSON: {json_size}KB | DB: {stats['db_size_kb']}KB | Growth since save: {growth}KB")
        print(f"Autosaves: {state.get('saves_count', 0)} | Threshold: {AUTOSAVE_THRESHOLD_KB}KB")

    else:
        print(f"Unknown command: {cmd}")
        print("Commands: save, load, export-catalog, import-json, backup-list, watch, restore, check, status, --help")
        return 1

    return 0


if __name__ == '__main__':
    sys.exit(main())
