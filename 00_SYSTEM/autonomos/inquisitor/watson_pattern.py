"""
DELTA99 Ω∞ — Watson Behavior Pattern Detector
===============================================
Mines all evidence sources for patterns of behavior by Emily Watson and Watson
family members. Tracks: filing patterns, escalation behavior, false allegations,
alienation tactics, financial manipulation, coordination with court actors.

Uses: extracted_harms(26K), evidence_quotes(308K), chatgpt_conversations(168K),
      adversary_models(114), global_weaponization(7131)
"""
import sys
import sqlite3
import json
import re
import time
from pathlib import Path
from datetime import datetime
from dataclasses import dataclass, field
from collections import defaultdict

_shared = Path(__file__).parent.parent / "shared"
if str(_shared) not in sys.path:
    sys.path.insert(0, str(_shared))

from autonomos_config import CENTRAL_DB

PATTERN_DB = Path(__file__).parent / "watson_patterns.db"

# ── Behavior Categories ────────────────────────────────────────────
BEHAVIOR_CATEGORIES = {
    "ALIENATION": {
        "description": "Parent alienation tactics against father-child relationship",
        "keywords": ["alienat", "turn.*against", "poisoning", "brainwash",
                     "don't.*love", "bad.*father", "hate.*dad", "not.*real.*dad",
                     "refuse.*phone", "block.*contact", "withhold.*child",
                     "keep.*away", "no.*visit"],
        "severity": "CRITICAL",
    },
    "FALSE_ALLEGATIONS": {
        "description": "Fabricated or unsupported allegations to gain advantage",
        "keywords": ["false.*alleg", "fabricat", "made.*up", "didn't.*happen",
                     "never.*occurred", "lie.*court", "perjur", "unsworn",
                     "no.*evidence.*but", "contrary.*to.*evidence"],
        "severity": "CRITICAL",
    },
    "FINANCIAL_MANIPULATION": {
        "description": "Financial abuse or manipulation",
        "keywords": ["money", "financ", "child.*support", "arrearage",
                     "income.*hid", "unreported.*income", "cash.*only",
                     "work.*under.*table", "refuse.*disclose.*financ"],
        "severity": "HIGH",
    },
    "PROCEDURAL_ABUSE": {
        "description": "Abuse of court procedures",
        "keywords": ["ex.*parte", "without.*notice", "same.*day.*order",
                     "emergency.*motion.*false", "ppo.*weapon", "weaponiz",
                     "filing.*harassment", "vexatious"],
        "severity": "CRITICAL",
    },
    "PHYSICAL_INTIMIDATION": {
        "description": "Physical threats or intimidation by Watson family",
        "keywords": ["threw.*paper", "window", "forcib", "intimidat",
                     "threaten", "harass.*exchange", "road.*rage",
                     "follow.*car", "block.*driveway", "physical.*confront"],
        "severity": "HIGH",
    },
    "COORDINATION": {
        "description": "Evidence of coordinated action with court actors",
        "keywords": ["Berry.*call", "Berry.*voicemail", "attorney.*ex.*parte",
                     "judge.*told", "whisper", "off.*record",
                     "in.*chambers.*without", "Rusco.*recommend",
                     "Martini.*said.*judge"],
        "severity": "CRITICAL",
    },
    "ESCALATION": {
        "description": "Escalating behavior over time",
        "keywords": ["worse", "escalat", "increase.*restrict",
                     "more.*aggressive", "additional.*allegation",
                     "new.*motion", "another.*filing", "yet.*another"],
        "severity": "HIGH",
    },
    "CHILD_WELFARE": {
        "description": "Actions harming child welfare",
        "keywords": ["child.*harm", "best.*interest", "emotional.*damage",
                     "therapy.*need", "school.*problem", "behavioral.*issue",
                     "child.*cry", "child.*ask.*for.*dad", "separation.*trauma"],
        "severity": "CRITICAL",
    },
}


def _init_db() -> sqlite3.Connection:
    PATTERN_DB.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(PATTERN_DB), timeout=30)
    conn.execute("PRAGMA journal_mode=WAL")
    conn.executescript("""
        CREATE TABLE IF NOT EXISTS behavior_patterns (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            category TEXT NOT NULL,
            severity TEXT DEFAULT 'MEDIUM',
            actor TEXT DEFAULT 'Emily Watson',
            source_table TEXT DEFAULT '',
            source_id TEXT DEFAULT '',
            matched_text TEXT DEFAULT '',
            matched_keyword TEXT DEFAULT '',
            context TEXT DEFAULT '',
            detected_at TEXT DEFAULT (datetime('now'))
        );
        CREATE INDEX IF NOT EXISTS idx_bp_cat ON behavior_patterns(category);
        CREATE INDEX IF NOT EXISTS idx_bp_actor ON behavior_patterns(actor);

        CREATE TABLE IF NOT EXISTS pattern_summaries (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            category TEXT NOT NULL,
            total_instances INTEGER DEFAULT 0,
            date_range TEXT DEFAULT '',
            escalation_trend TEXT DEFAULT '',
            evidence_strength TEXT DEFAULT '',
            filing_relevance TEXT DEFAULT '',
            computed_at TEXT DEFAULT (datetime('now'))
        );

        CREATE TABLE IF NOT EXISTS scan_runs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            sources_scanned TEXT DEFAULT '',
            records_scanned INTEGER DEFAULT 0,
            patterns_found INTEGER DEFAULT 0,
            duration_s REAL DEFAULT 0.0,
            run_at TEXT DEFAULT (datetime('now'))
        );
    """)
    conn.commit()
    return conn


def _compile_patterns() -> dict[str, list[re.Pattern]]:
    """Compile keyword patterns for each category."""
    compiled = {}
    for cat, info in BEHAVIOR_CATEGORIES.items():
        compiled[cat] = [re.compile(kw, re.I) for kw in info["keywords"]]
    return compiled


def _scan_table(central: sqlite3.Connection, table: str, text_col: str,
                patterns: dict[str, list[re.Pattern]],
                limit: int = 5000) -> list[dict]:
    """Scan a table for behavior patterns."""
    hits = []
    try:
        rows = central.execute(f"""
            SELECT rowid, {text_col} FROM {table} LIMIT {limit}
        """).fetchall()
    except sqlite3.Error:
        return hits

    for row in rows:
        text = str(row[1] or "")
        text_lower = text.lower()

        # Quick pre-filter: must mention Watson or family
        if not any(w in text_lower for w in ["watson", "emily", "albert", "cody", "lori"]):
            continue

        for cat, cat_patterns in patterns.items():
            for pat in cat_patterns:
                m = pat.search(text)
                if m:
                    # Determine specific actor
                    actor = "Emily Watson"
                    if "albert" in text_lower:
                        actor = "Albert Watson"
                    elif "cody" in text_lower:
                        actor = "Cody Watson"
                    elif "lori" in text_lower:
                        actor = "Lori Watson"

                    hits.append({
                        "category": cat,
                        "severity": BEHAVIOR_CATEGORIES[cat]["severity"],
                        "actor": actor,
                        "source_table": table,
                        "source_id": str(row[0]),
                        "matched_text": text[max(0, m.start()-30):m.end()+100][:300],
                        "matched_keyword": m.group(0),
                    })
                    break  # One hit per category per row
    return hits


def _scan_extracted_harms(central: sqlite3.Connection,
                          patterns: dict[str, list[re.Pattern]]) -> list[dict]:
    """Special scan using extracted_harms_fts."""
    hits = []
    search_terms = "Watson OR Emily OR alienation OR false OR weapon OR harass"
    try:
        rows = central.execute("""
            SELECT rowid, harm_description FROM extracted_harms_fts
            WHERE extracted_harms_fts MATCH ? LIMIT 5000
        """, (search_terms,)).fetchall()
    except sqlite3.Error:
        try:
            rows = central.execute("""
                SELECT rowid, harm_description FROM extracted_harms
                WHERE harm_description LIKE '%Watson%'
                   OR harm_description LIKE '%Emily%'
                   OR harm_description LIKE '%alienat%'
                LIMIT 5000
            """).fetchall()
        except sqlite3.Error:
            return hits

    for row in rows:
        text = str(row[1] or "")
        for cat, cat_patterns in patterns.items():
            for pat in cat_patterns:
                m = pat.search(text)
                if m:
                    hits.append({
                        "category": cat,
                        "severity": BEHAVIOR_CATEGORIES[cat]["severity"],
                        "actor": "Emily Watson",
                        "source_table": "extracted_harms",
                        "source_id": str(row[0]),
                        "matched_text": text[:300],
                        "matched_keyword": m.group(0),
                    })
                    break
    return hits


def run_full_scan() -> dict:
    """Run comprehensive Watson behavior pattern detection."""
    start = time.time()
    pdb = _init_db()
    patterns = _compile_patterns()

    central = sqlite3.connect(str(CENTRAL_DB), timeout=30)
    central.execute("PRAGMA busy_timeout=120000")

    all_hits = []
    scanned = 0

    # Scan evidence_quotes
    eq_hits = _scan_table(central, "evidence_quotes", "quote_text", patterns, 10000)
    all_hits.extend(eq_hits)
    scanned += 10000

    # Scan extracted_harms
    harm_hits = _scan_extracted_harms(central, patterns)
    all_hits.extend(harm_hits)
    scanned += 5000

    # Scan global_weaponization
    gw_hits = _scan_table(central, "global_weaponization", "description", patterns, 7131)
    all_hits.extend(gw_hits)
    scanned += 7131

    # Scan contradiction_map
    cm_hits = _scan_table(central, "contradiction_map", "description", patterns, 5000)
    all_hits.extend(cm_hits)
    scanned += 5000

    central.close()

    # Dedup by (category, source_table, source_id)
    seen = set()
    unique = []
    for h in all_hits:
        key = (h["category"], h["source_table"], h["source_id"])
        if key not in seen:
            seen.add(key)
            unique.append(h)

    # Persist
    for h in unique:
        pdb.execute("""
            INSERT INTO behavior_patterns
            (category, severity, actor, source_table, source_id,
             matched_text, matched_keyword)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (h["category"], h["severity"], h["actor"],
              h["source_table"], h["source_id"],
              h["matched_text"], h["matched_keyword"]))

    # Compute summaries
    by_category = defaultdict(lambda: {"count": 0, "actors": set()})
    for h in unique:
        by_category[h["category"]]["count"] += 1
        by_category[h["category"]]["actors"].add(h["actor"])

    for cat, info in by_category.items():
        pdb.execute("""
            INSERT INTO pattern_summaries
            (category, total_instances, evidence_strength)
            VALUES (?, ?, ?)
        """, (cat, info["count"],
              "STRONG" if info["count"] > 50 else "MODERATE" if info["count"] > 10 else "EMERGING"))

    duration = round(time.time() - start, 2)
    pdb.execute("""
        INSERT INTO scan_runs (sources_scanned, records_scanned, patterns_found, duration_s)
        VALUES (?, ?, ?, ?)
    """, ("evidence_quotes,extracted_harms,global_weaponization,contradiction_map",
          scanned, len(unique), duration))
    pdb.commit()
    pdb.close()

    return {
        "records_scanned": scanned,
        "total_patterns_found": len(unique),
        "by_category": {
            cat: {"count": info["count"],
                   "severity": BEHAVIOR_CATEGORIES.get(cat, {}).get("severity", ""),
                   "actors": list(info["actors"])}
            for cat, info in by_category.items()
        },
        "critical_patterns": sum(1 for h in unique if h["severity"] == "CRITICAL"),
        "top_hits": [
            {"category": h["category"], "actor": h["actor"],
             "text": h["matched_text"][:150], "keyword": h["matched_keyword"]}
            for h in unique if h["severity"] == "CRITICAL"
        ][:10],
        "duration_s": duration,
    }


if __name__ == "__main__":
    result = run_full_scan()
    print(json.dumps(result, indent=2, default=str))
