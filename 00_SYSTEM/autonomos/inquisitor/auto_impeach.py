"""
DELTA99 Ω∞ — Auto-Impeachment Engine
=======================================
Automatically builds impeachment outlines for each adversary by fusing
cross-lane evidence: contradictions, judicial violations, timeline anomalies,
behavioral patterns, and false allegations.

Depends on: d99-cross-lane-fusion (cross-lane evidence links)
Uses: contradiction_map(10K), impeachment_items(15K), judicial_violations(1K),
      extracted_harms(26K), adversary_models(114)
"""
import sys
import sqlite3
import json
import time
from pathlib import Path
from datetime import datetime
from collections import defaultdict
from dataclasses import dataclass, field

_shared = Path(__file__).parent.parent / "shared"
if str(_shared) not in sys.path:
    sys.path.insert(0, str(_shared))

from autonomos_config import CENTRAL_DB, LITIGOS_ROOT

IMPEACH_DB = Path(__file__).parent / "auto_impeach.db"
OUTPUT_DIR = LITIGOS_ROOT / "05_ANALYSIS" / "impeachment_outlines"

ADVERSARIES = {
    "Emily Watson": {
        "role": "Defendant/Respondent",
        "search_terms": ["watson", "emily", "respondent", "mother"],
    },
    "Judge McNeill": {
        "role": "Presiding Judge",
        "search_terms": ["mcneill", "judge", "court"],
    },
    "Ron Berry": {
        "role": "Attorney for Watson (former)",
        "search_terms": ["berry", "ron berry", "attorney"],
    },
    "Pamela Rusco": {
        "role": "Friend of the Court",
        "search_terms": ["rusco", "FOC", "friend of the court"],
    },
    "Albert Watson": {
        "role": "Watson family member",
        "search_terms": ["albert watson", "albert"],
    },
    "Cody Watson": {
        "role": "Watson family member",
        "search_terms": ["cody watson", "cody"],
    },
    "Mandi Martini": {
        "role": "Court staff / associated party",
        "search_terms": ["martini", "mandi"],
    },
}


def _init_db() -> sqlite3.Connection:
    IMPEACH_DB.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(IMPEACH_DB), timeout=30)
    conn.execute("PRAGMA journal_mode=WAL")
    conn.executescript("""
        CREATE TABLE IF NOT EXISTS impeachment_outlines (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            adversary TEXT NOT NULL,
            category TEXT NOT NULL,
            evidence_text TEXT DEFAULT '',
            source_table TEXT DEFAULT '',
            source_id TEXT DEFAULT '',
            impeachment_value TEXT DEFAULT 'MEDIUM',
            filing_use TEXT DEFAULT '',
            generated_at TEXT DEFAULT (datetime('now'))
        );
        CREATE INDEX IF NOT EXISTS idx_io_adv ON impeachment_outlines(adversary);
        CREATE INDEX IF NOT EXISTS idx_io_cat ON impeachment_outlines(category);

        CREATE TABLE IF NOT EXISTS impeachment_summaries (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            adversary TEXT NOT NULL,
            total_items INTEGER DEFAULT 0,
            critical_items INTEGER DEFAULT 0,
            categories TEXT DEFAULT '{}',
            top_3_items TEXT DEFAULT '[]',
            output_path TEXT DEFAULT '',
            generated_at TEXT DEFAULT (datetime('now'))
        );

        CREATE TABLE IF NOT EXISTS build_runs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            adversaries_processed INTEGER DEFAULT 0,
            total_items INTEGER DEFAULT 0,
            duration_s REAL DEFAULT 0.0,
            run_at TEXT DEFAULT (datetime('now'))
        );
    """)
    conn.commit()
    return conn


def _search_adversary(central: sqlite3.Connection, name: str,
                      search_terms: list[str]) -> dict:
    """Pull all impeachment material for an adversary."""
    items = defaultdict(list)

    # 1. Contradictions
    for term in search_terms[:2]:
        try:
            rows = central.execute("""
                SELECT rowid, description, contradiction_type
                FROM contradiction_map
                WHERE description LIKE ? LIMIT 200
            """, (f"%{term}%",)).fetchall()
            for r in rows:
                items["contradictions"].append({
                    "id": f"cm_{r[0]}", "text": str(r[1])[:400],
                    "type": str(r[2] or ""), "source": "contradiction_map"
                })
        except sqlite3.Error:
            pass

    # 2. Existing impeachment items
    for term in search_terms[:2]:
        try:
            rows = central.execute("""
                SELECT rowid, item_text, category, strength
                FROM impeachment_items
                WHERE item_text LIKE ? LIMIT 200
            """, (f"%{term}%",)).fetchall()
            for r in rows:
                items["impeachment"].append({
                    "id": f"ii_{r[0]}", "text": str(r[1])[:400],
                    "category": str(r[2] or ""), "strength": str(r[3] or ""),
                    "source": "impeachment_items"
                })
        except sqlite3.Error:
            pass

    # 3. Judicial violations (for judge targets)
    if any("judge" in t.lower() or "mcneill" in t.lower() for t in search_terms):
        try:
            rows = central.execute("""
                SELECT rowid, violation_description, severity, canon_number
                FROM judicial_violations LIMIT 500
            """).fetchall()
            for r in rows:
                items["violations"].append({
                    "id": f"jv_{r[0]}", "text": str(r[1])[:400],
                    "severity": str(r[2] or ""), "canon": str(r[3] or ""),
                    "source": "judicial_violations"
                })
        except sqlite3.Error:
            pass

    # 4. Extracted harms
    for term in search_terms[:2]:
        try:
            rows = central.execute("""
                SELECT rowid, harm_description FROM extracted_harms_fts
                WHERE extracted_harms_fts MATCH ? LIMIT 100
            """, (term,)).fetchall()
            for r in rows:
                items["harms"].append({
                    "id": f"eh_{r[0]}", "text": str(r[1])[:400],
                    "source": "extracted_harms"
                })
        except sqlite3.Error:
            try:
                rows = central.execute("""
                    SELECT rowid, harm_description FROM extracted_harms
                    WHERE harm_description LIKE ? LIMIT 100
                """, (f"%{term}%",)).fetchall()
                for r in rows:
                    items["harms"].append({
                        "id": f"eh_{r[0]}", "text": str(r[1])[:400],
                        "source": "extracted_harms"
                    })
            except sqlite3.Error:
                pass

    # 5. Evidence quotes
    for term in search_terms[:2]:
        try:
            rows = central.execute("""
                SELECT rowid, quote_text FROM evidence_quotes_fts
                WHERE evidence_quotes_fts MATCH ? LIMIT 100
            """, (term,)).fetchall()
            for r in rows:
                items["evidence"].append({
                    "id": f"eq_{r[0]}", "text": str(r[1])[:400],
                    "source": "evidence_quotes"
                })
        except sqlite3.Error:
            pass

    return dict(items)


def _score_impeachment_value(item: dict) -> str:
    """Score impeachment value of an item."""
    text = item.get("text", "").lower()
    if any(w in text for w in ["perjur", "lied", "false", "fabricat", "sworn"]):
        return "CRITICAL"
    if any(w in text for w in ["contradict", "inconsistent", "changed", "different"]):
        return "HIGH"
    if any(w in text for w in ["concern", "question", "unusual", "pattern"]):
        return "MEDIUM"
    return "LOW"


def _generate_outline(name: str, role: str, items_by_cat: dict) -> str:
    """Generate formatted impeachment outline."""
    lines = [
        f"IMPEACHMENT OUTLINE — {name.upper()}",
        f"Role: {role}",
        f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M')}",
        "=" * 60, ""
    ]

    total = sum(len(v) for v in items_by_cat.values())
    lines.append(f"Total impeachment items: {total}")
    lines.append("")

    for cat, items in sorted(items_by_cat.items(), key=lambda x: -len(x[1])):
        lines.append(f"\n{'─' * 40}")
        lines.append(f"  {cat.upper()} ({len(items)} items)")
        lines.append(f"{'─' * 40}\n")
        for i, item in enumerate(items[:20], 1):
            value = _score_impeachment_value(item)
            lines.append(f"  [{value}] {i}. {item['text'][:300]}")
            lines.append(f"      Source: {item.get('source', '')} #{item.get('id', '')}")
            lines.append("")

    return "\n".join(lines)


def build_all_outlines() -> dict:
    """Build impeachment outlines for all adversaries."""
    start = time.time()
    idb = _init_db()
    central = sqlite3.connect(str(CENTRAL_DB), timeout=30)
    central.execute("PRAGMA busy_timeout=120000")

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    results = []
    total_items = 0

    for name, info in ADVERSARIES.items():
        items_by_cat = _search_adversary(central, name, info["search_terms"])
        cat_count = sum(len(v) for v in items_by_cat.values())
        total_items += cat_count

        # Persist items
        for cat, items in items_by_cat.items():
            for item in items:
                value = _score_impeachment_value(item)
                idb.execute("""
                    INSERT INTO impeachment_outlines
                    (adversary, category, evidence_text, source_table,
                     source_id, impeachment_value)
                    VALUES (?, ?, ?, ?, ?, ?)
                """, (name, cat, item["text"][:500],
                      item.get("source", ""), item.get("id", ""), value))

        # Generate outline file
        outline = _generate_outline(name, info["role"], items_by_cat)
        safe_name = name.replace(" ", "_").lower()
        output_file = OUTPUT_DIR / f"impeach_{safe_name}.txt"
        output_file.write_text(outline, encoding="utf-8")

        # Summary
        critical = sum(1 for cat_items in items_by_cat.values()
                       for item in cat_items
                       if _score_impeachment_value(item) == "CRITICAL")

        idb.execute("""
            INSERT INTO impeachment_summaries
            (adversary, total_items, critical_items, categories, output_path)
            VALUES (?, ?, ?, ?, ?)
        """, (name, cat_count, critical,
              json.dumps({k: len(v) for k, v in items_by_cat.items()}),
              str(output_file)))

        results.append({
            "adversary": name,
            "role": info["role"],
            "total_items": cat_count,
            "critical": critical,
            "categories": {k: len(v) for k, v in items_by_cat.items()},
            "output": str(output_file),
        })

    duration = round(time.time() - start, 2)
    idb.execute("""
        INSERT INTO build_runs (adversaries_processed, total_items, duration_s)
        VALUES (?, ?, ?)
    """, (len(results), total_items, duration))
    idb.commit()
    central.close()
    idb.close()

    return {
        "adversaries_processed": len(results),
        "total_items": total_items,
        "results": results,
        "duration_s": duration,
    }


if __name__ == "__main__":
    result = build_all_outlines()
    print(json.dumps(result, indent=2, default=str))
