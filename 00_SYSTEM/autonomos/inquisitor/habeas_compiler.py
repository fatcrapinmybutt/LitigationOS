"""
APEX Ω∞ — Habeas Corpus Evidence Compiler
============================================
Compiles constitutional deprivation evidence for habeas corpus petition.
Focuses on physical custody deprivation since Aug 8, 2025.
Maps every day of separation to a constitutional violation.
Integrates with constitutional_mapper.py for §1983 alignment.
"""
import sys, sqlite3, json, time
from pathlib import Path
from datetime import datetime, date, timedelta

_shared = Path(__file__).parent.parent / "shared"
if str(_shared) not in sys.path:
    sys.path.insert(0, str(_shared))
from autonomos_config import CENTRAL_DB

HABEAS_DB = Path(__file__).parent / "habeas_compiler.db"

SEPARATION_DATE = date(2025, 8, 8)

HABEAS_GROUNDS = {
    "custody_without_due_process": {
        "label": "Custody Deprivation Without Due Process",
        "constitutional_basis": "US Const amend XIV §1; Const 1963 art 1 §17",
        "elements": [
            "Physical custody was altered or terminated",
            "No prior notice was given to the custodial/non-custodial parent",
            "No hearing was held before the deprivation",
            "No findings of fact or conclusions of law were made",
            "The deprivation is ongoing",
        ],
        "search_terms": ["ex parte", "without notice", "parenting time suspended", "custody"],
    },
    "void_orders_basis": {
        "label": "Orders Void for Jurisdictional/Constitutional Defect",
        "constitutional_basis": "MCR 2.612(C)(1)(d)",
        "elements": [
            "Orders entered without jurisdiction or constitutional authority",
            "Violating due process renders order void ab initio",
            "Void orders may be challenged at any time",
        ],
        "search_terms": ["void", "jurisdiction", "void ab initio", "void order"],
    },
    "right_to_parent_child": {
        "label": "Fundamental Right to Parent-Child Relationship",
        "constitutional_basis": "US Const amend XIV; Troxel v Granville, 530 US 57 (2000)",
        "elements": [
            "Parent has fundamental liberty interest in the care and custody of child",
            "State interference must satisfy strict scrutiny",
            "No compelling state interest demonstrated",
            "Less restrictive means were available but not considered",
        ],
        "search_terms": ["fundamental right", "liberty interest", "parent child", "troxel"],
    },
    "separation_harm": {
        "label": "Ongoing Harm from Prolonged Separation",
        "constitutional_basis": "US Const amend VIII (cruel and unusual); child welfare standards",
        "elements": [
            "Prolonged separation causes documented psychological harm to child",
            "Child has expressed desire to see parent",
            "No evidence of danger justifying continued separation",
            "Separation exceeds any reasonable temporary measure",
        ],
        "search_terms": ["separation", "harm", "child welfare", "psychological", "bonding"],
    },
}

def _init_db() -> sqlite3.Connection:
    HABEAS_DB.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(HABEAS_DB), timeout=30)
    conn.execute("PRAGMA journal_mode=WAL")
    conn.executescript("""
        CREATE TABLE IF NOT EXISTS habeas_evidence (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            ground_id TEXT NOT NULL,
            ground_label TEXT NOT NULL,
            element_text TEXT NOT NULL,
            evidence_count INTEGER DEFAULT 0,
            element_satisfied INTEGER DEFAULT 0,
            supporting_quotes TEXT DEFAULT '[]',
            generated_at TEXT DEFAULT (datetime('now'))
        );
        CREATE TABLE IF NOT EXISTS separation_log (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            log_date TEXT NOT NULL,
            day_number INTEGER NOT NULL,
            status TEXT DEFAULT 'separated',
            notes TEXT DEFAULT ''
        );
    """)
    conn.commit()
    return conn

def compile_habeas() -> dict:
    """Compile all habeas corpus evidence."""
    start = time.time()
    hdb = _init_db()
    today = date.today()
    sep_days = max(0, (today - SEPARATION_DATE).days)
    results = []

    try:
        cdb = sqlite3.connect(str(CENTRAL_DB), timeout=30)
        cdb.execute("PRAGMA query_only=ON")

        for gid, ground in HABEAS_GROUNDS.items():
            ground_result = {
                "ground": gid, "label": ground["label"],
                "constitutional_basis": ground["constitutional_basis"],
                "elements": [],
            }

            for elem in ground["elements"]:
                evidence_count = 0
                for term in ground["search_terms"]:
                    try:
                        cnt = cdb.execute("""
                            SELECT COUNT(*) FROM evidence_quotes
                            WHERE LOWER(COALESCE(quote_text,'')) LIKE ?
                        """, (f"%{term}%",)).fetchone()[0]
                        evidence_count += min(cnt, 100)
                    except Exception:
                        pass
                    try:
                        cnt = cdb.execute("""
                            SELECT COUNT(*) FROM judicial_violations
                            WHERE LOWER(COALESCE(description,'') || COALESCE(violation_type,''))
                            LIKE ?
                        """, (f"%{term}%",)).fetchone()[0]
                        evidence_count += cnt
                    except Exception:
                        pass

                satisfied = 1 if evidence_count >= 2 else 0
                hdb.execute("""
                    INSERT INTO habeas_evidence
                    (ground_id, ground_label, element_text, evidence_count, element_satisfied)
                    VALUES (?, ?, ?, ?, ?)
                """, (gid, ground["label"], elem, evidence_count, satisfied))

                ground_result["elements"].append({
                    "text": elem, "evidence": evidence_count,
                    "satisfied": bool(satisfied),
                })

            total_elems = len(ground["elements"])
            satisfied_elems = sum(1 for e in ground_result["elements"] if e["satisfied"])
            ground_result["elements_total"] = total_elems
            ground_result["elements_satisfied"] = satisfied_elems
            ground_result["strength"] = ("STRONG" if satisfied_elems == total_elems
                                          else "MODERATE" if satisfied_elems >= total_elems * 0.6
                                          else "WEAK")
            results.append(ground_result)

        # Log separation days
        existing = hdb.execute("SELECT COUNT(*) FROM separation_log").fetchone()[0]
        if existing < sep_days:
            for day_num in range(existing + 1, sep_days + 1):
                log_date = SEPARATION_DATE + timedelta(days=day_num)
                hdb.execute("""
                    INSERT OR IGNORE INTO separation_log (log_date, day_number)
                    VALUES (?, ?)
                """, (str(log_date), day_num))

        cdb.close()
    except Exception as e:
        results.append({"error": str(e)})

    hdb.commit()
    hdb.close()

    strong = [r for r in results if r.get("strength") == "STRONG"]
    return {
        "separation_days": sep_days,
        "grounds_analyzed": len(HABEAS_GROUNDS),
        "strong_grounds": len(strong),
        "results": results,
        "petition_basis": f"Father has been separated from his child for {sep_days} days without due process",
        "duration_s": round(time.time() - start, 2),
    }

if __name__ == "__main__":
    print(json.dumps(compile_habeas(), indent=2, default=str))
