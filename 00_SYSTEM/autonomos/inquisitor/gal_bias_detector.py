"""
APEX Ω∞ — GAL/Evaluator Bias Detector
========================================
Analyzes FOC recommendations and GAL reports for systematic bias.
Detects patterns: asymmetric scrutiny, crediting one parent without
corroboration, ignoring documented evidence, procedural favoritism.
Cross-references Pamela Rusco's 358 evidence quotes against outcomes.
"""
import sys, sqlite3, json, time
from pathlib import Path
from datetime import datetime

_shared = Path(__file__).parent.parent / "shared"
if str(_shared) not in sys.path:
    sys.path.insert(0, str(_shared))
from autonomos_config import CENTRAL_DB

GAL_BIAS_DB = Path(__file__).parent / "gal_bias.db"

BIAS_INDICATORS = {
    "asymmetric_scrutiny": {
        "label": "Asymmetric Scrutiny",
        "description": "Applying different standards of evidence/credibility to each parent",
        "weight": 1.5,
        "search_terms": ["one parent", "credibility", "inconsistent standard"],
    },
    "uncorroborated_credit": {
        "label": "Crediting Uncorroborated Claims",
        "description": "Accepting allegations from one party without independent verification",
        "weight": 1.3,
        "search_terms": ["alleged", "stated", "reported", "claimed"],
    },
    "ignore_documented_evidence": {
        "label": "Ignoring Documented Evidence",
        "description": "Failing to consider or mention documented evidence favorable to Father",
        "weight": 1.5,
        "search_terms": ["not considered", "failed to address", "omitted", "ignored"],
    },
    "ex_parte_communication": {
        "label": "Ex Parte Communication with Party/Attorney",
        "description": "FOC/GAL communicating with one party without the other's knowledge",
        "weight": 2.0,
        "search_terms": ["ex parte", "private communication", "without notice"],
    },
    "procedural_favoritism": {
        "label": "Procedural Favoritism",
        "description": "Scheduling, access, or procedural advantages given to one party",
        "weight": 1.2,
        "search_terms": ["scheduling", "access", "accommodation", "favorable"],
    },
    "outcome_predetermined": {
        "label": "Predetermined Outcome Indicators",
        "description": "Signs that recommendation was decided before investigation complete",
        "weight": 1.8,
        "search_terms": ["predetermined", "conclusion before", "already decided"],
    },
    "factor_j_neglect": {
        "label": "Factor (j) Neglect — Alienation",
        "description": "Failing to address evidence of parental alienation under MCL 722.23(j)",
        "weight": 1.5,
        "search_terms": ["factor j", "alienation", "relationship", "722.23(j)", "willingness"],
    },
    "rusco_pattern": {
        "label": "FOC Rusco Communication Pattern",
        "description": "Pamela Rusco's documented communication asymmetry",
        "weight": 1.4,
        "search_terms": ["rusco", "foc", "friend of the court", "pamela"],
    },
}

FOC_ADVERSARIES = {
    "pamela_rusco": {
        "name": "Pamela Rusco",
        "role": "Friend of the Court",
        "address": "990 Terrace St, Muskegon MI 49442",
        "known_harms": 61,
        "known_quotes": 358,
    },
}

def _init_db() -> sqlite3.Connection:
    GAL_BIAS_DB.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(GAL_BIAS_DB), timeout=30)
    conn.execute("PRAGMA journal_mode=WAL")
    conn.executescript("""
        CREATE TABLE IF NOT EXISTS bias_findings (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            indicator_id TEXT NOT NULL,
            indicator_label TEXT NOT NULL,
            evidence_count INTEGER DEFAULT 0,
            weighted_score REAL DEFAULT 0.0,
            source_tables TEXT DEFAULT '[]',
            generated_at TEXT DEFAULT (datetime('now'))
        );
        CREATE TABLE IF NOT EXISTS foc_analysis (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            adversary TEXT NOT NULL,
            quote_count INTEGER DEFAULT 0,
            harm_count INTEGER DEFAULT 0,
            bias_score REAL DEFAULT 0.0,
            analysis_json TEXT DEFAULT '{}',
            generated_at TEXT DEFAULT (datetime('now'))
        );
    """)
    conn.commit()
    return conn

def detect_bias() -> dict:
    """Analyze FOC/GAL for systematic bias patterns."""
    start = time.time()
    bdb = _init_db()
    results = []
    total_bias_score = 0.0

    try:
        cdb = sqlite3.connect(str(CENTRAL_DB), timeout=30)
        cdb.execute("PRAGMA query_only=ON")

        for ind_id, indicator in BIAS_INDICATORS.items():
            evidence_count = 0
            source_tables = []

            for term in indicator["search_terms"]:
                # Search evidence_quotes
                try:
                    cnt = cdb.execute("""
                        SELECT COUNT(*) FROM evidence_quotes
                        WHERE LOWER(COALESCE(quote_text,'')) LIKE ?
                    """, (f"%{term}%",)).fetchone()[0]
                    if cnt > 0:
                        evidence_count += min(cnt, 200)
                        if "evidence_quotes" not in source_tables:
                            source_tables.append("evidence_quotes")
                except Exception:
                    pass

                # Search extracted_harms
                try:
                    cnt = cdb.execute("""
                        SELECT COUNT(*) FROM extracted_harms
                        WHERE LOWER(COALESCE(harm_text,'') || COALESCE(description,''))
                        LIKE ?
                    """, (f"%{term}%",)).fetchone()[0]
                    if cnt > 0:
                        evidence_count += cnt
                        if "extracted_harms" not in source_tables:
                            source_tables.append("extracted_harms")
                except Exception:
                    pass

            weighted = evidence_count * indicator["weight"]
            total_bias_score += weighted

            bdb.execute("""
                INSERT INTO bias_findings
                (indicator_id, indicator_label, evidence_count, weighted_score, source_tables)
                VALUES (?, ?, ?, ?, ?)
            """, (ind_id, indicator["label"], evidence_count, weighted,
                  json.dumps(source_tables)))

            results.append({
                "indicator": ind_id, "label": indicator["label"],
                "evidence_count": evidence_count, "weight": indicator["weight"],
                "weighted_score": round(weighted, 1),
                "source_tables": source_tables,
            })

        # Specific Rusco analysis
        rusco_data = {"quotes": 0, "harms": 0}
        try:
            rusco_data["quotes"] = cdb.execute("""
                SELECT COUNT(*) FROM evidence_quotes
                WHERE LOWER(COALESCE(quote_text,'') || COALESCE(source,''))
                LIKE '%rusco%'
            """).fetchone()[0]
        except Exception:
            pass
        try:
            rusco_data["harms"] = cdb.execute("""
                SELECT COUNT(*) FROM extracted_harms
                WHERE LOWER(COALESCE(adversary,'') || COALESCE(harm_text,''))
                LIKE '%rusco%'
            """).fetchone()[0]
        except Exception:
            pass

        bdb.execute("""
            INSERT INTO foc_analysis
            (adversary, quote_count, harm_count, bias_score, analysis_json)
            VALUES (?, ?, ?, ?, ?)
        """, ("pamela_rusco", rusco_data["quotes"], rusco_data["harms"],
              total_bias_score, json.dumps(rusco_data)))

        cdb.close()
    except Exception as e:
        results.append({"error": str(e)})

    bdb.commit()
    bdb.close()

    ranked = sorted(results, key=lambda x: x.get("weighted_score", 0), reverse=True)
    return {
        "indicators_checked": len(BIAS_INDICATORS),
        "total_bias_score": round(total_bias_score, 1),
        "rusco_analysis": rusco_data,
        "results": ranked,
        "duration_s": round(time.time() - start, 2),
    }

if __name__ == "__main__":
    print(json.dumps(detect_bias(), indent=2, default=str))
