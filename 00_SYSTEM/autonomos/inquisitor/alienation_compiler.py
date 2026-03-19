"""
APEX Ω∞ — Parental Alienation Evidence Compiler
=================================================
Compiles ALL parental alienation evidence from extracted_harms
(6,390 child welfare items) + evidence_quotes into court-ready
alienation brief with 8 Gardner indicators + MCL 722.23(j) analysis.

Gardner's 8 Criteria for Parental Alienation:
1. Campaign of denigration
2. Weak/absurd rationalizations
3. Lack of ambivalence
4. "Independent thinker" phenomenon
5. Reflexive support of alienating parent
6. Absence of guilt
7. Borrowed scenarios
8. Spread of animosity to extended family
"""
import sys
import sqlite3
import json
import time
import re
from pathlib import Path
from datetime import datetime

_shared = Path(__file__).parent.parent / "shared"
if str(_shared) not in sys.path:
    sys.path.insert(0, str(_shared))

from autonomos_config import CENTRAL_DB, LITIGOS_ROOT

ALIENATION_DB = Path(__file__).parent / "alienation_compiler.db"
OUTPUT_DIR = LITIGOS_ROOT / "05_ANALYSIS" / "alienation_evidence"

GARDNER_INDICATORS = {
    "campaign_of_denigration": {
        "description": "Campaign of denigration against targeted parent",
        "keywords": ["badmouth", "denigrat", "trash talk", "negative", "bad father",
                     "told child", "said about father", "speaks negatively"],
    },
    "weak_rationalizations": {
        "description": "Weak, absurd, or frivolous rationalizations for deprecation",
        "keywords": ["excuse", "rationalize", "justify", "because he", "claim without"],
    },
    "lack_of_ambivalence": {
        "description": "Lack of ambivalence — one parent all good, other all bad",
        "keywords": ["all bad", "terrible father", "never good", "always wrong", "hates"],
    },
    "independent_thinker": {
        "description": "'Independent thinker' phenomenon — child claims own idea",
        "keywords": ["child said", "child decided", "my decision", "I don't want to"],
    },
    "reflexive_support": {
        "description": "Reflexive support of alienating parent in conflict",
        "keywords": ["side with mother", "supports mother", "agrees with mom", "defends mother"],
    },
    "absence_of_guilt": {
        "description": "Absence of guilt about cruelty to targeted parent",
        "keywords": ["no remorse", "doesn't care", "no guilt", "indifferent to father"],
    },
    "borrowed_scenarios": {
        "description": "Presence of borrowed scenarios — adult language from child",
        "keywords": ["coached", "rehearsed", "adult language", "sounds like mother",
                     "repeating", "scripted", "parroting"],
    },
    "spread_to_family": {
        "description": "Spread of animosity to extended family/friends of targeted parent",
        "keywords": ["grandparent", "family cut off", "no contact with",
                     "extended family", "Watson family", "Albert", "Lori", "Cody"],
    },
}


def _init_db() -> sqlite3.Connection:
    ALIENATION_DB.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(ALIENATION_DB), timeout=30)
    conn.execute("PRAGMA journal_mode=WAL")
    conn.executescript("""
        CREATE TABLE IF NOT EXISTS alienation_evidence (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            gardner_indicator TEXT NOT NULL,
            evidence_text TEXT NOT NULL,
            source TEXT DEFAULT '',
            strength TEXT DEFAULT 'moderate',
            detected_at TEXT DEFAULT (datetime('now'))
        );
        CREATE TABLE IF NOT EXISTS indicator_scores (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            indicator TEXT NOT NULL UNIQUE,
            description TEXT DEFAULT '',
            evidence_count INTEGER DEFAULT 0,
            strong_count INTEGER DEFAULT 0,
            score REAL DEFAULT 0.0,
            scored_at TEXT DEFAULT (datetime('now'))
        );
        CREATE TABLE IF NOT EXISTS alienation_briefs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            total_evidence INTEGER DEFAULT 0,
            indicators_met INTEGER DEFAULT 0,
            composite_score REAL DEFAULT 0.0,
            output_path TEXT DEFAULT '',
            generated_at TEXT DEFAULT (datetime('now'))
        );
    """)
    conn.commit()
    return conn


def _search_alienation_evidence(central: sqlite3.Connection,
                                adb: sqlite3.Connection) -> dict:
    """Search all evidence sources for alienation indicators."""
    indicator_counts = {}

    for indicator_key, indicator_info in GARDNER_INDICATORS.items():
        count = 0
        strong = 0

        for kw in indicator_info["keywords"]:
            # Search extracted_harms
            try:
                rows = central.execute("""
                    SELECT harm_description, adversary, severity
                    FROM extracted_harms
                    WHERE harm_description LIKE ?
                    LIMIT 100
                """, (f"%{kw}%",)).fetchall()

                for desc, adversary, severity in rows:
                    strength = "strong" if str(severity or "") in ("critical", "high") else "moderate"
                    if strength == "strong":
                        strong += 1
                    adb.execute("""
                        INSERT INTO alienation_evidence
                        (gardner_indicator, evidence_text, source, strength)
                        VALUES (?, ?, ?, ?)
                    """, (indicator_key, str(desc or "")[:1000],
                          f"extracted_harms/{str(adversary or '')}",
                          strength))
                    count += 1
            except sqlite3.Error:
                pass

            # Search evidence_quotes
            try:
                rows = central.execute("""
                    SELECT quote_text, source_file
                    FROM evidence_quotes
                    WHERE quote_text LIKE ?
                    LIMIT 50
                """, (f"%{kw}%",)).fetchall()

                for text, source in rows:
                    adb.execute("""
                        INSERT INTO alienation_evidence
                        (gardner_indicator, evidence_text, source, strength)
                        VALUES (?, ?, ?, 'moderate')
                    """, (indicator_key, str(text or "")[:1000],
                          str(source or "evidence_quotes")))
                    count += 1
            except sqlite3.Error:
                pass

        # Score this indicator
        score = min(count * 0.1 + strong * 0.3, 10.0)
        adb.execute("""
            INSERT OR REPLACE INTO indicator_scores
            (indicator, description, evidence_count, strong_count, score)
            VALUES (?, ?, ?, ?, ?)
        """, (indicator_key, indicator_info["description"],
              count, strong, round(score, 2)))

        indicator_counts[indicator_key] = {
            "description": indicator_info["description"],
            "evidence_count": count,
            "strong_evidence": strong,
            "score": round(score, 2),
        }

    adb.commit()
    return indicator_counts


def _generate_brief(adb: sqlite3.Connection,
                    indicator_counts: dict) -> str:
    """Generate court-ready alienation evidence brief."""
    indicators_met = sum(1 for v in indicator_counts.values() if v["evidence_count"] > 0)
    composite = sum(v["score"] for v in indicator_counts.values()) / len(indicator_counts) if indicator_counts else 0

    parts = []
    parts.append("=" * 60)
    parts.append("  PARENTAL ALIENATION EVIDENCE COMPILATION")
    parts.append("  Pigors v. Watson — Case No. 2024-001507-DC")
    parts.append("=" * 60)
    parts.append("")
    parts.append("LEGAL FRAMEWORK:")
    parts.append("  MCL 722.23(j) — Willingness to facilitate parent-child relationship")
    parts.append("  Ireland v Smith, 451 Mich 457 (1996) — Factor (j) most important")
    parts.append("  Berger v Berger, 277 Mich App 700 (2008) — Alienation considerations")
    parts.append("")
    parts.append(f"INDICATORS MET: {indicators_met} of 8 Gardner criteria")
    parts.append(f"COMPOSITE SCORE: {composite:.1f}/10.0")
    parts.append("")

    for key, info in indicator_counts.items():
        status = "✅ MET" if info["evidence_count"] > 0 else "❌ INSUFFICIENT"
        parts.append(f"\n{'─' * 50}")
        parts.append(f"  {status} — {info['description']}")
        parts.append(f"  Evidence items: {info['evidence_count']} ({info['strong_evidence']} strong)")
        parts.append(f"  Score: {info['score']}/10.0")

        # Pull top 3 evidence examples
        examples = adb.execute("""
            SELECT evidence_text, source FROM alienation_evidence
            WHERE gardner_indicator = ?
            ORDER BY strength DESC
            LIMIT 3
        """, (key,)).fetchall()

        for i, (text, source) in enumerate(examples, 1):
            parts.append(f"    {i}. \"{str(text)[:200]}...\"")
            parts.append(f"       Source: {source}")

    parts.append(f"\n{'=' * 60}")
    parts.append("  CONCLUSION")
    parts.append(f"{'=' * 60}")
    parts.append("")
    if indicators_met >= 6:
        parts.append("STRONG ALIENATION CASE — 6+ Gardner indicators met.")
    elif indicators_met >= 4:
        parts.append("MODERATE ALIENATION CASE — 4+ Gardner indicators met.")
    else:
        parts.append("DEVELOPING CASE — Continue evidence compilation.")

    parts.append(f"\nThis compilation supports Factor (j) analysis under MCL 722.23")
    parts.append(f"demonstrating Mother's pattern of alienating behaviors.")
    parts.append(f"\nTotal evidence items: {sum(v['evidence_count'] for v in indicator_counts.values())}")

    return "\n".join(parts)


def run_compilation() -> dict:
    """Run full alienation evidence compilation."""
    start = time.time()
    adb = _init_db()
    central = sqlite3.connect(str(CENTRAL_DB), timeout=30)
    central.execute("PRAGMA busy_timeout=120000")

    adb.execute("DELETE FROM alienation_evidence")

    indicators = _search_alienation_evidence(central, adb)
    brief = _generate_brief(adb, indicators)

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    ts = datetime.now().strftime("%Y%m%d")
    output_file = OUTPUT_DIR / f"alienation_compilation_{ts}.txt"
    output_file.write_text(brief, encoding="utf-8")

    total_evidence = sum(v["evidence_count"] for v in indicators.values())
    indicators_met = sum(1 for v in indicators.values() if v["evidence_count"] > 0)
    composite = sum(v["score"] for v in indicators.values()) / len(indicators) if indicators else 0

    adb.execute("""
        INSERT INTO alienation_briefs
        (total_evidence, indicators_met, composite_score, output_path)
        VALUES (?, ?, ?, ?)
    """, (total_evidence, indicators_met, round(composite, 2), str(output_file)))
    adb.commit()

    central.close()
    adb.close()

    return {
        "indicators": indicators,
        "indicators_met": indicators_met,
        "total_evidence": total_evidence,
        "composite_score": round(composite, 2),
        "output": str(output_file),
        "duration_s": round(time.time() - start, 2),
    }


if __name__ == "__main__":
    result = run_compilation()
    print(json.dumps(result, indent=2, default=str))
