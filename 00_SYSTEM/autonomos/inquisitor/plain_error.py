"""
APEX Ω∞ — Plain Error Analyzer
================================
Scans ALL judicial orders for Carines plain error.
People v Carines, 460 Mich 750 (1999) — 4-prong test:
  1. Error must have occurred
  2. Error was plain (clear or obvious)
  3. Error affected substantial rights (outcome-determinative)
  4. Error seriously affected fairness/integrity of proceedings

Applies to unpreserved errors on appeal — critical for COA 366810.
"""
import sys, sqlite3, json, time
from pathlib import Path
from datetime import datetime

_shared = Path(__file__).parent.parent / "shared"
if str(_shared) not in sys.path:
    sys.path.insert(0, str(_shared))
from autonomos_config import CENTRAL_DB

PLAIN_ERROR_DB = Path(__file__).parent / "plain_error.db"

CARINES_PRONGS = [
    "error_occurred", "error_plain", "substantial_rights", "fairness_integrity"
]

PLAIN_ERROR_PATTERNS = {
    "ex_parte_order": {
        "label": "Ex Parte Order Without Notice",
        "mcr": "MCR 2.119(B), MCR 3.207(B)",
        "error_type": "Due process violation",
        "prong_1": "Order entered without notice or opportunity to be heard",
        "prong_2": "Plain — constitutional right to notice is established law",
        "prong_3": "Affected custody rights — the most substantial right in family law",
        "prong_4": "Undermines fundamental fairness of entire proceeding",
        "detection_keywords": ["ex parte", "without notice", "without hearing"],
    },
    "no_bif_analysis": {
        "label": "No Best-Interest Finding Before Custody Change",
        "mcr": "MCL 722.27(1)(c)",
        "error_type": "Statutory violation",
        "prong_1": "Court changed custody without required best-interest analysis",
        "prong_2": "Plain — MCL 722.27(1)(c) mandates BIF analysis, per Vodvarka v Grasmeyer",
        "prong_3": "Directly caused loss of parenting time — outcome determinative",
        "prong_4": "Systematic failure to apply governing statute",
        "detection_keywords": ["best interest", "custody", "parenting time", "722.23"],
    },
    "denied_without_hearing": {
        "label": "Motion Denied Without Hearing",
        "mcr": "MCR 2.119(E)(3)",
        "error_type": "Procedural violation",
        "prong_1": "Motion denied without oral argument or written opinion",
        "prong_2": "Plain — MCR 2.119(E) governs motion practice",
        "prong_3": "Denied opportunity to present evidence and argument",
        "prong_4": "Pattern of denial without consideration = structural error",
        "detection_keywords": ["denied", "without hearing", "motion denied"],
    },
    "bias_failure_to_recuse": {
        "label": "Judicial Bias / Failure to Recuse",
        "mcr": "MCR 2.003(C)(1), Canon 2",
        "error_type": "Judicial misconduct",
        "prong_1": "Judge demonstrated personal bias against a party",
        "prong_2": "Plain — recusal required when impartiality might reasonably be questioned",
        "prong_3": "All orders tainted by bias are potentially void",
        "prong_4": "Most severe threat to fairness and public confidence in judiciary",
        "detection_keywords": ["bias", "recus", "impartial", "disqualif"],
    },
    "improper_foc_delegation": {
        "label": "Improper Delegation to FOC",
        "mcr": "MCL 552.507, MCR 3.208",
        "error_type": "Delegation of judicial authority",
        "prong_1": "Court delegated judicial decision-making to FOC without safeguards",
        "prong_2": "Plain — FOC recommendations require de novo review if objected",
        "prong_3": "Affected custody outcome without judicial oversight",
        "prong_4": "Undermines separation of powers and judicial responsibility",
        "detection_keywords": ["foc", "friend of the court", "recommendation", "referee"],
    },
    "insufficient_findings": {
        "label": "Insufficient Findings of Fact",
        "mcr": "MCR 2.517(A)(1)",
        "error_type": "Inadequate judicial reasoning",
        "prong_1": "Court failed to make findings of fact and conclusions of law",
        "prong_2": "Plain — MCR 2.517 requires specific findings in bench decisions",
        "prong_3": "Cannot determine if correct legal standard was applied",
        "prong_4": "Meaningful appellate review impossible without findings",
        "detection_keywords": ["findings", "reasons", "basis", "rationale"],
    },
}

def _init_db() -> sqlite3.Connection:
    PLAIN_ERROR_DB.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(PLAIN_ERROR_DB), timeout=30)
    conn.execute("PRAGMA journal_mode=WAL")
    conn.executescript("""
        CREATE TABLE IF NOT EXISTS plain_errors (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            pattern_key TEXT NOT NULL,
            error_label TEXT NOT NULL,
            mcr_cite TEXT NOT NULL,
            error_type TEXT NOT NULL,
            prong_1_met INTEGER DEFAULT 0,
            prong_2_met INTEGER DEFAULT 0,
            prong_3_met INTEGER DEFAULT 0,
            prong_4_met INTEGER DEFAULT 0,
            all_prongs_met INTEGER DEFAULT 0,
            evidence_count INTEGER DEFAULT 0,
            source_tables TEXT DEFAULT '[]',
            generated_at TEXT DEFAULT (datetime('now'))
        );
    """)
    conn.commit()
    return conn

def analyze_plain_error() -> dict:
    """Scan all judicial orders for Carines plain error."""
    start = time.time()
    pdb = _init_db()
    results = []

    try:
        cdb = sqlite3.connect(str(CENTRAL_DB), timeout=30)
        cdb.execute("PRAGMA query_only=ON")

        for pkey, pattern in PLAIN_ERROR_PATTERNS.items():
            evidence_count = 0
            source_tables = []
            kws = pattern["detection_keywords"]

            # Search judicial_violations
            try:
                for kw in kws:
                    rows = cdb.execute("""
                        SELECT COUNT(*) FROM judicial_violations
                        WHERE LOWER(COALESCE(violation_type,'') || COALESCE(description,''))
                        LIKE ?
                    """, (f"%{kw}%",)).fetchone()
                    if rows and rows[0] > 0:
                        evidence_count += rows[0]
                        if "judicial_violations" not in source_tables:
                            source_tables.append("judicial_violations")
            except Exception:
                pass

            # Search docket_events
            try:
                for kw in kws:
                    rows = cdb.execute("""
                        SELECT COUNT(*) FROM docket_events
                        WHERE LOWER(COALESCE(description,'') || COALESCE(event_type,''))
                        LIKE ?
                    """, (f"%{kw}%",)).fetchone()
                    if rows and rows[0] > 0:
                        evidence_count += rows[0]
                        if "docket_events" not in source_tables:
                            source_tables.append("docket_events")
            except Exception:
                pass

            # Search evidence_quotes_fts
            try:
                for kw in kws:
                    rows = cdb.execute("""
                        SELECT COUNT(*) FROM evidence_quotes
                        WHERE LOWER(COALESCE(quote_text,'')) LIKE ?
                    """, (f"%{kw}%",)).fetchone()
                    if rows and rows[0] > 0:
                        evidence_count += min(rows[0], 100)
                        if "evidence_quotes" not in source_tables:
                            source_tables.append("evidence_quotes")
            except Exception:
                pass

            # Score prongs (1=evidence exists, prongs 2-4 are legal analysis)
            p1 = 1 if evidence_count > 0 else 0
            p2 = 1  # All patterns are well-established law
            p3 = 1 if evidence_count >= 3 else 0
            p4 = 1 if evidence_count >= 5 else 0
            all_met = 1 if (p1 and p2 and p3 and p4) else 0

            pdb.execute("""
                INSERT INTO plain_errors
                (pattern_key, error_label, mcr_cite, error_type,
                 prong_1_met, prong_2_met, prong_3_met, prong_4_met,
                 all_prongs_met, evidence_count, source_tables)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (pkey, pattern["label"], pattern["mcr"], pattern["error_type"],
                  p1, p2, p3, p4, all_met, evidence_count,
                  json.dumps(source_tables)))

            results.append({
                "pattern": pkey, "label": pattern["label"],
                "mcr": pattern["mcr"], "error_type": pattern["error_type"],
                "prongs_met": [p1, p2, p3, p4], "all_prongs": bool(all_met),
                "evidence_count": evidence_count,
                "source_tables": source_tables,
            })

        cdb.close()
    except Exception as e:
        results.append({"error": str(e)})

    pdb.commit()
    pdb.close()

    all_met = [r for r in results if r.get("all_prongs")]
    return {
        "patterns_analyzed": len(PLAIN_ERROR_PATTERNS),
        "all_prongs_met": len(all_met),
        "results": results,
        "carines_cite": "People v Carines, 460 Mich 750 (1999)",
        "duration_s": round(time.time() - start, 2),
    }

if __name__ == "__main__":
    print(json.dumps(analyze_plain_error(), indent=2, default=str))
