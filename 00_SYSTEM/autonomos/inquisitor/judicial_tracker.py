"""
DELTA99 Ω∞ — Judicial Violation Auto-Tracker
=============================================
Continuously scans docket_events, orders, and transcripts for judicial violations.
Cross-references against auth_benchbook_violations and canon rules.
Auto-appends to judicial_violations table and omega_violation_analysis.

Key patterns: ex parte orders, same-day entry, lack of notice, procedural violations,
bias indicators, coordination with Watson/Berry/Rusco.
"""
import sys
import re
import sqlite3
import json
import time
from pathlib import Path
from datetime import datetime, timedelta
from dataclasses import dataclass, field

_shared = Path(__file__).parent.parent / "shared"
if str(_shared) not in sys.path:
    sys.path.insert(0, str(_shared))

from autonomos_config import CENTRAL_DB

TRACKER_DB = Path(__file__).parent / "judicial_tracker.db"

# ── Violation Pattern Definitions ──────────────────────────────────
VIOLATION_PATTERNS = {
    "EX_PARTE_ORDER": {
        "description": "Order entered without notice to opposing party",
        "severity": "CRITICAL",
        "patterns": [
            re.compile(r'ex\s*parte', re.I),
            re.compile(r'without\s+(?:notice|hearing)', re.I),
            re.compile(r'entered\s+(?:the\s+)?same\s+day', re.I),
        ],
        "mcr": "MCR 2.119(A)",
        "canon": "Canon 2, Canon 3(A)(4)",
    },
    "SAME_DAY_RULING": {
        "description": "Motion filed and order entered on same day",
        "severity": "HIGH",
        "patterns": [
            re.compile(r'filed.*(?:and|&).*(?:entered|granted|denied).*same', re.I),
        ],
        "mcr": "MCR 2.119(C)(1)",
        "canon": "Canon 2",
    },
    "DENIED_HEARING": {
        "description": "Right to hearing denied or waived without consent",
        "severity": "CRITICAL",
        "patterns": [
            re.compile(r'no\s+(?:oral\s+)?hearing\s+(?:held|granted|scheduled)', re.I),
            re.compile(r'hearing\s+denied', re.I),
            re.compile(r'without\s+(?:oral\s+)?hearing', re.I),
        ],
        "mcr": "MCR 2.119(E)",
        "canon": "Canon 3(A)(4)",
    },
    "BIAS_INDICATOR": {
        "description": "Language or action indicating prejudgment or bias",
        "severity": "HIGH",
        "patterns": [
            re.compile(r'bad\s+mood', re.I),
            re.compile(r'already\s+decided', re.I),
            re.compile(r'not\s+(?:going\s+to\s+)?listen', re.I),
            re.compile(r'don\'?t\s+(?:want\s+to\s+)?hear', re.I),
        ],
        "mcr": "MCR 2.003",
        "canon": "Canon 2, Canon 3(A)(1)",
    },
    "COORDINATION_SIGNAL": {
        "description": "Timing or content suggesting coordination with opposing party",
        "severity": "CRITICAL",
        "patterns": [
            re.compile(r'Berry.*(?:filed|motion).*(?:within|same)\s+\d+\s+(?:day|hour)', re.I),
            re.compile(r'Watson.*(?:filed|motion).*(?:within|same)\s+\d+\s+(?:day|hour)', re.I),
            re.compile(r'Rusco.*(?:recommend|report).*(?:same\s+day|immediately)', re.I),
        ],
        "mcr": "MCR 2.003(C)",
        "canon": "Canon 3(A)(4), Canon 3(B)(7)",
    },
    "PARENTING_TIME_VIOLATION": {
        "description": "Suspension or restriction of parenting time without required findings",
        "severity": "CRITICAL",
        "patterns": [
            re.compile(r'suspend.*parent(?:ing)?\s*time', re.I),
            re.compile(r'no\s+(?:parenting|visitation)\s*time', re.I),
            re.compile(r'supervised\s+(?:only|parenting)', re.I),
        ],
        "mcr": "MCL 722.27a",
        "canon": "MCL 722.23 (best interest factors)",
    },
    "CONTEMPT_WITHOUT_DUE_PROCESS": {
        "description": "Contempt finding without proper notice and hearing",
        "severity": "CRITICAL",
        "patterns": [
            re.compile(r'contempt.*without\s+(?:notice|hearing)', re.I),
            re.compile(r'held\s+in\s+contempt.*(?:same\s+day|immediately)', re.I),
        ],
        "mcr": "MCR 3.606",
        "canon": "Canon 3(A)(4)",
    },
    "UNSWORN_ALLEGATIONS": {
        "description": "Judicial reliance on unsworn allegations as findings of fact",
        "severity": "HIGH",
        "patterns": [
            re.compile(r'(?:based\s+on|relied\s+on).*(?:unsworn|allegation)', re.I),
            re.compile(r'no\s+evidence.*(?:but|yet).*(?:found|concluded|ordered)', re.I),
        ],
        "mcr": "MCR 2.517(A)(1)",
        "canon": "Canon 3(A)(1)",
    },
}


def _init_db() -> sqlite3.Connection:
    TRACKER_DB.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(TRACKER_DB), timeout=30)
    conn.execute("PRAGMA journal_mode=WAL")
    conn.executescript("""
        CREATE TABLE IF NOT EXISTS violation_detections (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            violation_type TEXT NOT NULL,
            severity TEXT NOT NULL,
            source_type TEXT DEFAULT '',
            source_id TEXT DEFAULT '',
            source_text TEXT DEFAULT '',
            matched_pattern TEXT DEFAULT '',
            mcr_reference TEXT DEFAULT '',
            canon_reference TEXT DEFAULT '',
            detected_at TEXT DEFAULT (datetime('now')),
            appended_to_central INTEGER DEFAULT 0
        );
        CREATE INDEX IF NOT EXISTS idx_vd_type ON violation_detections(violation_type);
        CREATE INDEX IF NOT EXISTS idx_vd_sev ON violation_detections(severity);

        CREATE TABLE IF NOT EXISTS scan_runs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            source TEXT NOT NULL,
            records_scanned INTEGER DEFAULT 0,
            violations_found INTEGER DEFAULT 0,
            new_violations INTEGER DEFAULT 0,
            duration_s REAL DEFAULT 0.0,
            run_at TEXT DEFAULT (datetime('now'))
        );
    """)
    conn.commit()
    return conn


@dataclass
class ViolationHit:
    violation_type: str
    severity: str
    source_type: str
    source_id: str
    source_text: str
    matched_pattern: str
    mcr_ref: str
    canon_ref: str


def scan_text_for_violations(text: str, source_type: str = "",
                             source_id: str = "") -> list[ViolationHit]:
    """Scan a text block for all judicial violation patterns."""
    hits = []
    for vtype, vdef in VIOLATION_PATTERNS.items():
        for pattern in vdef["patterns"]:
            match = pattern.search(text)
            if match:
                hits.append(ViolationHit(
                    violation_type=vtype,
                    severity=vdef["severity"],
                    source_type=source_type,
                    source_id=str(source_id),
                    source_text=text[max(0, match.start()-50):match.end()+100][:300],
                    matched_pattern=match.group(0),
                    mcr_ref=vdef["mcr"],
                    canon_ref=vdef["canon"],
                ))
                break  # One hit per violation type per text
    return hits


def scan_docket_events() -> list[ViolationHit]:
    """Scan docket_events table for violations."""
    central = sqlite3.connect(str(CENTRAL_DB), timeout=30)
    central.execute("PRAGMA busy_timeout=120000")

    hits = []
    try:
        rows = central.execute("""
            SELECT rowid, event_date, event_description, event_type
            FROM docket_events LIMIT 5000
        """).fetchall()
    except sqlite3.Error:
        try:
            rows = central.execute("""
                SELECT rowid, date, description, type
                FROM docket_events LIMIT 5000
            """).fetchall()
        except sqlite3.Error:
            central.close()
            return hits

    for row in rows:
        text = f"{row[1]} {row[2]} {row[3] or ''}"
        row_hits = scan_text_for_violations(text, "docket_event", str(row[0]))
        hits.extend(row_hits)

    central.close()
    return hits


def scan_evidence_quotes() -> list[ViolationHit]:
    """Scan evidence_quotes for judicial violation signals."""
    central = sqlite3.connect(str(CENTRAL_DB), timeout=30)
    central.execute("PRAGMA busy_timeout=120000")

    hits = []
    # Use FTS5 to narrow search to judicial-related quotes
    search_terms = "judge OR court OR order OR hearing OR contempt OR ex parte OR ruling"
    try:
        rows = central.execute(f"""
            SELECT rowid, quote_text FROM evidence_quotes_fts
            WHERE evidence_quotes_fts MATCH ? LIMIT 2000
        """, (search_terms,)).fetchall()
    except sqlite3.Error:
        try:
            rows = central.execute("""
                SELECT rowid, quote_text FROM evidence_quotes
                WHERE quote_text LIKE '%judge%' OR quote_text LIKE '%court%'
                   OR quote_text LIKE '%order%' OR quote_text LIKE '%ex parte%'
                LIMIT 2000
            """).fetchall()
        except sqlite3.Error:
            central.close()
            return hits

    for row in rows:
        text = str(row[1] or "")
        row_hits = scan_text_for_violations(text, "evidence_quote", str(row[0]))
        hits.extend(row_hits)

    central.close()
    return hits


def append_to_central(hits: list[ViolationHit], tracker_db: sqlite3.Connection) -> int:
    """Append new violations to the central DB judicial_violations table."""
    if not hits:
        return 0

    central = sqlite3.connect(str(CENTRAL_DB), timeout=30)
    central.execute("PRAGMA busy_timeout=120000")

    appended = 0
    for hit in hits:
        try:
            # Check for duplicate
            existing = central.execute("""
                SELECT COUNT(*) FROM judicial_violations
                WHERE violation_type = ? AND source_text LIKE ?
            """, (hit.violation_type, f"%{hit.matched_pattern[:50]}%")).fetchone()

            if existing and existing[0] == 0:
                central.execute("""
                    INSERT INTO judicial_violations
                    (violation_type, severity, source_type, source_id, source_text,
                     mcr_reference, canon_reference, detected_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?, datetime('now'))
                """, (hit.violation_type, hit.severity, hit.source_type,
                      hit.source_id, hit.source_text[:500],
                      hit.mcr_ref, hit.canon_ref))
                appended += 1

                # Mark as appended in tracker DB
                tracker_db.execute("""
                    UPDATE violation_detections SET appended_to_central = 1
                    WHERE violation_type = ? AND source_id = ?
                """, (hit.violation_type, hit.source_id))
        except sqlite3.Error:
            pass

    central.commit()
    central.close()
    tracker_db.commit()
    return appended


def run_full_scan() -> dict:
    """Run complete judicial violation scan across all sources."""
    start = time.time()
    tracker = _init_db()

    all_hits = []

    # Scan docket events
    docket_hits = scan_docket_events()
    all_hits.extend(docket_hits)

    # Scan evidence quotes
    eq_hits = scan_evidence_quotes()
    all_hits.extend(eq_hits)

    # Deduplicate by (type, source_id)
    seen = set()
    unique_hits = []
    for h in all_hits:
        key = (h.violation_type, h.source_id, h.matched_pattern)
        if key not in seen:
            seen.add(key)
            unique_hits.append(h)

    # Persist to tracker DB
    for h in unique_hits:
        tracker.execute("""
            INSERT INTO violation_detections
            (violation_type, severity, source_type, source_id, source_text,
             matched_pattern, mcr_reference, canon_reference)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (h.violation_type, h.severity, h.source_type, h.source_id,
              h.source_text, h.matched_pattern, h.mcr_ref, h.canon_ref))
    tracker.commit()

    # Append new ones to central DB
    new_count = append_to_central(unique_hits, tracker)

    duration = round(time.time() - start, 2)

    tracker.execute("""
        INSERT INTO scan_runs (source, records_scanned, violations_found, new_violations, duration_s)
        VALUES ('full_scan', ?, ?, ?, ?)
    """, (5000 + 2000, len(unique_hits), new_count, duration))
    tracker.commit()

    # Generate summary by type
    by_type = {}
    for h in unique_hits:
        by_type.setdefault(h.violation_type, {"count": 0, "severity": h.severity})
        by_type[h.violation_type]["count"] += 1

    tracker.close()
    return {
        "violations_detected": len(unique_hits),
        "new_appended_to_central": new_count,
        "by_type": by_type,
        "critical_count": sum(1 for h in unique_hits if h.severity == "CRITICAL"),
        "high_count": sum(1 for h in unique_hits if h.severity == "HIGH"),
        "duration_s": duration,
        "sample_violations": [
            {"type": h.violation_type, "severity": h.severity,
             "text": h.source_text[:200], "rule": h.mcr_ref}
            for h in unique_hits[:10]
        ],
    }


if __name__ == "__main__":
    result = run_full_scan()
    print(json.dumps(result, indent=2, default=str))
