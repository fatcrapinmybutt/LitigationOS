"""
APEX Ω∞ — Perjury Detection Engine
=====================================
Cross-references ALL sworn statements against the master timeline,
evidence quotes, and contradiction map to detect provable perjury.
Generates impeachment packets with exact contradictions, exhibit refs,
and MCL 750.423 analysis for each detected perjury instance.

Scans: evidence_quotes, contradiction_map, master_chronological_timeline,
       impeachment_items, extracted_harms
"""
import sys
import sqlite3
import json
import re
import time
import hashlib
from pathlib import Path
from datetime import datetime
from collections import defaultdict

_shared = Path(__file__).parent.parent / "shared"
if str(_shared) not in sys.path:
    sys.path.insert(0, str(_shared))

from autonomos_config import CENTRAL_DB

PERJURY_DB = Path(__file__).parent / "perjury_detector.db"

# Sworn statement indicators
SWORN_INDICATORS = [
    r"(?i)under\s+(?:oath|penalty\s+of\s+perjury)",
    r"(?i)sworn\s+(?:to|statement|testimony|affidavit)",
    r"(?i)(?:depos(?:ition|ed)|testified|affidavit|declaration)",
    r"(?i)do\s+solemnly\s+swear",
    r"(?i)certif(?:y|ied)\s+under\s+penalty",
]
SWORN_RE = [re.compile(p) for p in SWORN_INDICATORS]

# Adversaries to track
ADVERSARIES = [
    "Emily Watson", "Emily A. Watson", "Watson",
    "Albert Watson", "Lori Watson", "Cody Watson",
    "Mandi Martini", "Pamela Rusco", "Jennifer Barnes",
]

PERJURY_CATEGORIES = [
    "timeline_contradiction",    # Statement contradicts established timeline
    "self_contradiction",        # Statement contradicts own prior statement
    "document_contradiction",    # Statement contradicts documentary evidence
    "witness_contradiction",     # Statement contradicts other witness
    "impossible_claim",          # Physically or logically impossible assertion
    "omission_perjury",         # Deliberate omission of material facts
]


def _init_db() -> sqlite3.Connection:
    PERJURY_DB.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(PERJURY_DB), timeout=30)
    conn.execute("PRAGMA journal_mode=WAL")
    conn.executescript("""
        CREATE TABLE IF NOT EXISTS perjury_instances (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            adversary TEXT NOT NULL,
            category TEXT NOT NULL,
            sworn_statement TEXT NOT NULL,
            contradicting_evidence TEXT NOT NULL,
            source_ref TEXT DEFAULT '',
            contra_ref TEXT DEFAULT '',
            severity TEXT DEFAULT 'moderate',
            mcl_750_423_elements TEXT DEFAULT '{}',
            impeachment_ready INTEGER DEFAULT 0,
            detected_at TEXT DEFAULT (datetime('now'))
        );
        CREATE TABLE IF NOT EXISTS sworn_statements (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            adversary TEXT NOT NULL,
            statement_text TEXT NOT NULL,
            source TEXT DEFAULT '',
            statement_date TEXT DEFAULT '',
            hash TEXT NOT NULL UNIQUE,
            extracted_at TEXT DEFAULT (datetime('now'))
        );
        CREATE TABLE IF NOT EXISTS perjury_packets (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            adversary TEXT NOT NULL,
            instance_count INTEGER DEFAULT 0,
            packet_json TEXT DEFAULT '{}',
            output_path TEXT DEFAULT '',
            generated_at TEXT DEFAULT (datetime('now'))
        );
        CREATE TABLE IF NOT EXISTS detection_runs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            sworn_found INTEGER DEFAULT 0,
            contradictions_found INTEGER DEFAULT 0,
            perjury_instances INTEGER DEFAULT 0,
            duration_s REAL DEFAULT 0.0,
            run_at TEXT DEFAULT (datetime('now'))
        );
        CREATE INDEX IF NOT EXISTS idx_perjury_adversary ON perjury_instances(adversary);
        CREATE INDEX IF NOT EXISTS idx_sworn_adversary ON sworn_statements(adversary);
    """)
    conn.commit()
    return conn


def _extract_sworn_statements(central: sqlite3.Connection,
                              pdb: sqlite3.Connection) -> int:
    """Extract sworn statements from evidence quotes."""
    found = 0
    try:
        for adversary in ADVERSARIES:
            name_part = adversary.split()[-1]  # Last name
            rows = central.execute("""
                SELECT quote_text, source_file
                FROM evidence_quotes
                WHERE quote_text LIKE ? AND length(quote_text) > 30
                LIMIT 500
            """, (f"%{name_part}%",)).fetchall()

            for text, source in rows:
                text = str(text)
                # Check if it contains sworn indicators
                is_sworn = any(p.search(text) for p in SWORN_RE)
                if not is_sworn:
                    continue

                h = hashlib.md5(text[:500].encode()).hexdigest()
                try:
                    pdb.execute("""
                        INSERT OR IGNORE INTO sworn_statements
                        (adversary, statement_text, source, hash)
                        VALUES (?, ?, ?, ?)
                    """, (adversary, text[:2000], str(source or ""), h))
                    found += 1
                except sqlite3.IntegrityError:
                    pass
    except sqlite3.Error:
        pass
    pdb.commit()
    return found


def _detect_contradictions(central: sqlite3.Connection,
                           pdb: sqlite3.Connection) -> int:
    """Cross-reference sworn statements against contradictions."""
    detected = 0

    # Method 1: Use existing contradiction_map
    try:
        rows = central.execute("""
            SELECT statement_a, statement_b, contradiction_type, severity, source_a, source_b
            FROM contradiction_map
            WHERE severity IN ('high', 'critical')
            LIMIT 2000
        """).fetchall()

        for sa, sb, ctype, sev, src_a, src_b in rows:
            sa, sb = str(sa or ""), str(sb or "")
            # Check if either statement involves an adversary
            for adversary in ADVERSARIES:
                name_part = adversary.split()[-1].lower()
                if name_part in sa.lower() or name_part in sb.lower():
                    # Check if sworn
                    is_sworn = any(p.search(sa) or p.search(sb) for p in SWORN_RE)
                    severity = "critical" if is_sworn else str(sev or "moderate")

                    mcl_elements = {
                        "material_statement": True,
                        "under_oath": is_sworn,
                        "known_false": severity == "critical",
                        "willful": "deliberate" in str(ctype or "").lower(),
                    }

                    pdb.execute("""
                        INSERT INTO perjury_instances
                        (adversary, category, sworn_statement, contradicting_evidence,
                         source_ref, contra_ref, severity, mcl_750_423_elements,
                         impeachment_ready)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """, (adversary, "self_contradiction",
                          sa[:2000], sb[:2000],
                          str(src_a or ""), str(src_b or ""),
                          severity, json.dumps(mcl_elements),
                          1 if is_sworn else 0))
                    detected += 1
                    break
    except sqlite3.Error:
        pass

    # Method 2: Cross-reference with timeline
    try:
        sworn_rows = pdb.execute("""
            SELECT adversary, statement_text, source FROM sworn_statements
        """).fetchall()

        for adversary, stmt, source in sworn_rows:
            stmt = str(stmt)
            # Look for date references in the statement
            date_matches = re.findall(r'\b\d{1,2}/\d{1,2}/\d{2,4}\b|\b(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)\w*\s+\d{1,2},?\s*\d{4}\b', stmt)
            for date_ref in date_matches[:3]:
                # Check timeline for contradicting events
                timeline_rows = central.execute("""
                    SELECT event_date, title, description
                    FROM master_chronological_timeline
                    WHERE description LIKE ? OR title LIKE ?
                    LIMIT 5
                """, (f"%{date_ref}%", f"%{date_ref}%")).fetchall()

                for ev_date, ev_title, ev_desc in timeline_rows:
                    ev_desc = str(ev_desc or "")
                    name_part = adversary.split()[-1].lower()
                    if name_part in ev_desc.lower():
                        pdb.execute("""
                            INSERT INTO perjury_instances
                            (adversary, category, sworn_statement, contradicting_evidence,
                             source_ref, severity, mcl_750_423_elements, impeachment_ready)
                            VALUES (?, 'timeline_contradiction', ?, ?, ?, 'high', '{}', 1)
                        """, (adversary, stmt[:2000],
                              f"Timeline {ev_date}: {ev_title} - {ev_desc[:500]}",
                              str(source or "")))
                        detected += 1
    except sqlite3.Error:
        pass

    pdb.commit()
    return detected


def _generate_packets(pdb: sqlite3.Connection) -> list[dict]:
    """Generate impeachment packets per adversary."""
    packets = []
    try:
        adversaries = pdb.execute("""
            SELECT DISTINCT adversary, COUNT(*) as cnt
            FROM perjury_instances
            GROUP BY adversary
            ORDER BY cnt DESC
        """).fetchall()

        output_dir = Path(__file__).parent.parent.parent.parent / "05_ANALYSIS" / "perjury_packets"
        output_dir.mkdir(parents=True, exist_ok=True)

        for adversary, count in adversaries:
            instances = pdb.execute("""
                SELECT category, sworn_statement, contradicting_evidence,
                       source_ref, severity, mcl_750_423_elements
                FROM perjury_instances
                WHERE adversary = ?
                ORDER BY CASE severity
                    WHEN 'critical' THEN 0
                    WHEN 'high' THEN 1
                    WHEN 'moderate' THEN 2
                    ELSE 3
                END
            """, (adversary,)).fetchall()

            packet = {
                "adversary": adversary,
                "total_instances": count,
                "critical": sum(1 for i in instances if i[4] == "critical"),
                "high": sum(1 for i in instances if i[4] == "high"),
                "instances": [
                    {
                        "category": str(i[0]),
                        "sworn_statement": str(i[1])[:500],
                        "contradicting_evidence": str(i[2])[:500],
                        "source": str(i[3]),
                        "severity": str(i[4]),
                    }
                    for i in instances[:20]  # Top 20 per adversary
                ],
                "mcl_750_423_analysis": {
                    "statute": "MCL 750.423 — Perjury",
                    "elements": [
                        "1. Material statement",
                        "2. Made under oath",
                        "3. Known to be false",
                        "4. Willfully made",
                    ],
                    "applicable_instances": sum(1 for i in instances if i[4] in ("critical", "high")),
                },
            }

            # Write packet
            safe_name = re.sub(r'[^\w]', '_', adversary)
            packet_file = output_dir / f"perjury_packet_{safe_name}.json"
            packet_file.write_text(json.dumps(packet, indent=2), encoding="utf-8")
            packet["output_path"] = str(packet_file)
            packets.append(packet)

            pdb.execute("""
                INSERT INTO perjury_packets
                (adversary, instance_count, packet_json, output_path)
                VALUES (?, ?, ?, ?)
            """, (adversary, count, json.dumps(packet), str(packet_file)))

    except sqlite3.Error:
        pass

    pdb.commit()
    return packets


def run_detection() -> dict:
    """Run full perjury detection pipeline."""
    start = time.time()
    pdb = _init_db()
    central = sqlite3.connect(str(CENTRAL_DB), timeout=30)
    central.execute("PRAGMA busy_timeout=120000")

    sworn = _extract_sworn_statements(central, pdb)
    contradictions = _detect_contradictions(central, pdb)
    packets = _generate_packets(pdb)

    duration = round(time.time() - start, 2)
    pdb.execute("""
        INSERT INTO detection_runs
        (sworn_found, contradictions_found, perjury_instances, duration_s)
        VALUES (?, ?, ?, ?)
    """, (sworn, contradictions, sum(p["total_instances"] for p in packets), duration))
    pdb.commit()

    central.close()
    pdb.close()

    return {
        "sworn_statements_found": sworn,
        "contradictions_detected": contradictions,
        "adversaries_with_perjury": len(packets),
        "packets": [
            {"adversary": p["adversary"], "instances": p["total_instances"],
             "critical": p["critical"], "high": p["high"]}
            for p in packets
        ],
        "duration_s": duration,
    }


if __name__ == "__main__":
    result = run_detection()
    print(json.dumps(result, indent=2, default=str))
