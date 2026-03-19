"""
APEX Ω∞ — Witness Credibility Scorer
======================================
Scores every witness on 8 credibility axes:
1. Consistency (self-contradiction rate)
2. Bias (relationship to party)
3. Motive (financial/emotional interest)
4. Corroboration (independent verification)
5. Demeanor (court behavior indicators)
6. Expertise (relevant knowledge)
7. Specificity (detail level of claims)
8. Impeachment history (prior contradictions exposed)

Targets: Emily Watson, Albert Watson, Lori Watson, Cody Watson,
         Mandi Martini, Pamela Rusco, Jennifer Barnes, Ron Berry
"""
import sys, sqlite3, json, time
from pathlib import Path
from datetime import datetime

_shared = Path(__file__).parent.parent / "shared"
if str(_shared) not in sys.path:
    sys.path.insert(0, str(_shared))
from autonomos_config import CENTRAL_DB

CREDIBILITY_DB = Path(__file__).parent / "witness_credibility.db"

WITNESSES = {
    "emily_watson": {"name": "Emily A. Watson", "role": "Defendant-Mother",
                     "aliases": ["Emily", "Watson", "Emily Watson", "Emily A. Watson"],
                     "bias_base": 0.2, "motive_base": 0.2},
    "albert_watson": {"name": "Albert Watson", "role": "Father of Defendant",
                      "aliases": ["Albert", "Albert Watson"],
                      "bias_base": 0.15, "motive_base": 0.3},
    "lori_watson": {"name": "Lori Watson", "role": "Mother of Defendant",
                    "aliases": ["Lori", "Lori Watson"],
                    "bias_base": 0.15, "motive_base": 0.3},
    "cody_watson": {"name": "Cody Watson", "role": "Brother of Defendant",
                    "aliases": ["Cody", "Cody Watson"],
                    "bias_base": 0.15, "motive_base": 0.3},
    "mandi_martini": {"name": "Mandi Martini", "role": "Court staff/other",
                      "aliases": ["Mandi", "Martini", "Mandi Martini"],
                      "bias_base": 0.4, "motive_base": 0.5},
    "pamela_rusco": {"name": "Pamela Rusco", "role": "FOC Officer",
                     "aliases": ["Rusco", "Pamela Rusco", "FOC"],
                     "bias_base": 0.4, "motive_base": 0.5},
    "jennifer_barnes": {"name": "Jennifer Barnes", "role": "Former Def. Attorney",
                        "aliases": ["Barnes", "Jennifer Barnes"],
                        "bias_base": 0.3, "motive_base": 0.4},
    "ron_berry": {"name": "Ron Berry", "role": "Attorney (coordination suspect)",
                  "aliases": ["Berry", "Ron Berry"],
                  "bias_base": 0.2, "motive_base": 0.2},
}

CREDIBILITY_AXES = [
    "consistency", "bias", "motive", "corroboration",
    "demeanor", "expertise", "specificity", "impeachment_history",
]


def _init_db() -> sqlite3.Connection:
    CREDIBILITY_DB.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(CREDIBILITY_DB), timeout=30)
    conn.execute("PRAGMA journal_mode=WAL")
    conn.executescript("""
        CREATE TABLE IF NOT EXISTS credibility_scores (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            witness_key TEXT NOT NULL,
            witness_name TEXT NOT NULL,
            role TEXT DEFAULT '',
            consistency REAL DEFAULT 5.0,
            bias REAL DEFAULT 5.0,
            motive REAL DEFAULT 5.0,
            corroboration REAL DEFAULT 5.0,
            demeanor REAL DEFAULT 5.0,
            expertise REAL DEFAULT 5.0,
            specificity REAL DEFAULT 5.0,
            impeachment_history REAL DEFAULT 5.0,
            composite REAL DEFAULT 5.0,
            evidence_items INTEGER DEFAULT 0,
            scored_at TEXT DEFAULT (datetime('now'))
        );
        CREATE TABLE IF NOT EXISTS credibility_evidence (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            witness_key TEXT NOT NULL,
            axis TEXT NOT NULL,
            evidence_text TEXT DEFAULT '',
            score_impact REAL DEFAULT 0.0,
            source TEXT DEFAULT ''
        );
    """)
    conn.commit()
    return conn


def _score_witness(central: sqlite3.Connection, cdb: sqlite3.Connection,
                   witness_key: str, witness_info: dict) -> dict:
    """Score a single witness across all 8 axes."""
    scores = {}
    evidence_count = 0

    # ── Consistency (lower = more contradictions = less credible) ──
    contradiction_count = 0
    for alias in witness_info["aliases"][:3]:
        try:
            count = central.execute("""
                SELECT COUNT(*) FROM contradiction_map
                WHERE statement_a LIKE ? OR statement_b LIKE ?
            """, (f"%{alias}%", f"%{alias}%")).fetchone()[0]
            contradiction_count += count
        except sqlite3.Error:
            pass
    # More contradictions = lower score
    scores["consistency"] = max(1.0, 10.0 - contradiction_count * 0.05)
    evidence_count += contradiction_count

    # ── Bias (family relationship = inherent bias) ──
    scores["bias"] = max(1.0, witness_info["bias_base"] * 10.0)  # Lower = more biased

    # ── Motive (financial/custody interest) ──
    scores["motive"] = max(1.0, witness_info["motive_base"] * 10.0)

    # ── Corroboration (how much independent evidence supports claims) ──
    corroboration = 5.0
    for alias in witness_info["aliases"][:2]:
        try:
            count = central.execute("""
                SELECT COUNT(*) FROM evidence_quotes
                WHERE quote_text LIKE ? AND source_file NOT LIKE '%watson%'
            """, (f"%{alias}%",)).fetchone()[0]
            corroboration = min(10.0, 5.0 + count * 0.01)
        except sqlite3.Error:
            pass
    scores["corroboration"] = corroboration

    # ── Demeanor (court behavior) ──
    demeanor_score = 5.0
    for alias in witness_info["aliases"][:2]:
        try:
            bad_behavior = central.execute("""
                SELECT COUNT(*) FROM extracted_harms
                WHERE adversary LIKE ? AND (
                    harm_description LIKE '%courtroom%' OR
                    harm_description LIKE '%hearing%' OR
                    harm_description LIKE '%behavior%'
                )
            """, (f"%{alias}%",)).fetchone()[0]
            demeanor_score = max(1.0, 5.0 - bad_behavior * 0.1)
            evidence_count += bad_behavior
        except sqlite3.Error:
            pass
    scores["demeanor"] = demeanor_score

    # ── Expertise (relevant knowledge) ──
    scores["expertise"] = 3.0 if witness_info["role"] in ("Court staff/other", "FOC Officer") else 5.0

    # ── Specificity ──
    scores["specificity"] = 5.0  # Baseline — requires deposition analysis

    # ── Impeachment History ──
    impeach_count = 0
    for alias in witness_info["aliases"][:2]:
        try:
            count = central.execute("""
                SELECT COUNT(*) FROM impeachment_items
                WHERE target LIKE ?
            """, (f"%{alias}%",)).fetchone()[0]
            impeach_count += count
        except sqlite3.Error:
            pass
    scores["impeachment_history"] = max(1.0, 10.0 - impeach_count * 0.02)
    evidence_count += impeach_count

    # ── Composite ──
    composite = sum(scores.values()) / len(scores)
    scores["composite"] = round(composite, 2)

    # Persist
    cdb.execute("""
        INSERT INTO credibility_scores
        (witness_key, witness_name, role, consistency, bias, motive,
         corroboration, demeanor, expertise, specificity,
         impeachment_history, composite, evidence_items)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (witness_key, witness_info["name"], witness_info["role"],
          round(scores["consistency"], 2), round(scores["bias"], 2),
          round(scores["motive"], 2), round(scores["corroboration"], 2),
          round(scores["demeanor"], 2), round(scores["expertise"], 2),
          round(scores["specificity"], 2), round(scores["impeachment_history"], 2),
          round(composite, 2), evidence_count))

    return {
        "name": witness_info["name"],
        "role": witness_info["role"],
        "scores": {k: round(v, 2) for k, v in scores.items()},
        "evidence_items": evidence_count,
    }


def score_all_witnesses() -> dict:
    """Score all witnesses."""
    start = time.time()
    cdb = _init_db()
    central = sqlite3.connect(str(CENTRAL_DB), timeout=30)
    central.execute("PRAGMA busy_timeout=120000")

    cdb.execute("DELETE FROM credibility_scores")

    results = {}
    for wk, wi in WITNESSES.items():
        results[wk] = _score_witness(central, cdb, wk, wi)

    cdb.commit()
    central.close()
    cdb.close()

    # Rank by composite (lower = less credible)
    ranked = sorted(results.items(), key=lambda x: x[1]["scores"]["composite"])

    return {
        "witnesses": results,
        "least_credible": [
            {"name": r[1]["name"], "composite": r[1]["scores"]["composite"]}
            for r in ranked[:3]
        ],
        "most_credible": [
            {"name": r[1]["name"], "composite": r[1]["scores"]["composite"]}
            for r in ranked[-3:]
        ],
        "duration_s": round(time.time() - start, 2),
    }


if __name__ == "__main__":
    result = score_all_witnesses()
    print(json.dumps(result, indent=2, default=str))
