"""
APEX Ω∞ — Constitutional Violation Mapper
===========================================
Maps each ex parte order, denied hearing, and custody deprivation
to specific constitutional provisions. Feeds §1983 complaint.

14th Amendment analysis:
- Substantive due process (parental liberty interest)
- Procedural due process (notice + hearing)
- Equal protection (gender-based disparate treatment)

Also: 1st Amendment (access to courts), 4th Amendment (seizure of child)
"""
import sys
import sqlite3
import json
import time
from pathlib import Path
from datetime import datetime

_shared = Path(__file__).parent.parent / "shared"
if str(_shared) not in sys.path:
    sys.path.insert(0, str(_shared))

from autonomos_config import CENTRAL_DB

CONSTITUTIONAL_DB = Path(__file__).parent / "constitutional_mapper.db"

CONSTITUTIONAL_PROVISIONS = {
    "14th_substantive_dp": {
        "provision": "14th Amendment — Substantive Due Process",
        "standard": "Fundamental liberty interest in parent-child relationship",
        "case_law": [
            "Troxel v Granville, 530 US 57 (2000)",
            "Stanley v Illinois, 405 US 645 (1972)",
            "Santosky v Kramer, 455 US 745 (1982)",
        ],
        "triggers": ["custody", "parenting time", "separation", "terminated", "suspended"],
    },
    "14th_procedural_dp": {
        "provision": "14th Amendment — Procedural Due Process",
        "standard": "Notice and opportunity to be heard before deprivation",
        "case_law": [
            "Mathews v Eldridge, 424 US 319 (1976)",
            "Armstrong v Manzo, 380 US 545 (1965)",
        ],
        "triggers": ["ex parte", "without notice", "without hearing", "no opportunity"],
    },
    "14th_equal_protection": {
        "provision": "14th Amendment — Equal Protection",
        "standard": "Gender-neutral application of custody standards",
        "case_law": [
            "Craig v Boren, 429 US 190 (1976)",
            "Orr v Orr, 440 US 268 (1979)",
        ],
        "triggers": ["father", "mother", "gender", "preferential", "bias"],
    },
    "1st_access_courts": {
        "provision": "1st Amendment — Right of Access to Courts",
        "standard": "Meaningful access to judicial proceedings",
        "case_law": [
            "California Motor Transport v Trucking Unlimited, 404 US 508 (1972)",
        ],
        "triggers": ["denied hearing", "motion ignored", "no response", "blocked"],
    },
    "4th_seizure": {
        "provision": "4th Amendment — Seizure (via 14th)",
        "standard": "Unreasonable seizure of child from parent",
        "case_law": [
            "Kovacic v Cuyahoga Cty Dep't of Children, 606 F3d 301 (6th Cir 2010)",
        ],
        "triggers": ["removed child", "took child", "seized", "forcibly"],
    },
}


def _init_db() -> sqlite3.Connection:
    CONSTITUTIONAL_DB.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(CONSTITUTIONAL_DB), timeout=30)
    conn.execute("PRAGMA journal_mode=WAL")
    conn.executescript("""
        CREATE TABLE IF NOT EXISTS violations (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            provision TEXT NOT NULL,
            provision_name TEXT DEFAULT '',
            violating_event TEXT DEFAULT '',
            event_date TEXT DEFAULT '',
            actor TEXT DEFAULT '',
            evidence TEXT DEFAULT '',
            section_1983_count TEXT DEFAULT '',
            severity TEXT DEFAULT 'high',
            mapped_at TEXT DEFAULT (datetime('now'))
        );
        CREATE TABLE IF NOT EXISTS section_1983_counts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            count_number INTEGER NOT NULL,
            title TEXT NOT NULL,
            constitutional_basis TEXT NOT NULL,
            defendant TEXT NOT NULL,
            violations_supporting INTEGER DEFAULT 0,
            summary TEXT DEFAULT ''
        );
        CREATE TABLE IF NOT EXISTS mapping_runs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            total_violations INTEGER DEFAULT 0,
            provisions_violated INTEGER DEFAULT 0,
            defendants_implicated INTEGER DEFAULT 0,
            duration_s REAL DEFAULT 0.0,
            run_at TEXT DEFAULT (datetime('now'))
        );
    """)
    conn.commit()
    return conn


def _map_violations(central: sqlite3.Connection,
                    mdb: sqlite3.Connection) -> dict:
    """Map events to constitutional violations."""
    provision_counts = {}

    for prov_key, prov_info in CONSTITUTIONAL_PROVISIONS.items():
        count = 0
        for trigger in prov_info["triggers"]:
            # Search timeline
            try:
                rows = central.execute("""
                    SELECT event_date, title, description, actors
                    FROM master_chronological_timeline
                    WHERE LOWER(description) LIKE ? OR LOWER(title) LIKE ?
                    LIMIT 100
                """, (f"%{trigger}%", f"%{trigger}%")).fetchall()

                for ev_date, title, desc, actors in rows:
                    actor = "McNeill" if "mcneill" in str(actors or "").lower() else "Unknown"
                    mdb.execute("""
                        INSERT INTO violations
                        (provision, provision_name, violating_event,
                         event_date, actor, evidence, severity)
                        VALUES (?, ?, ?, ?, ?, ?, 'high')
                    """, (prov_key, prov_info["provision"],
                          f"{str(title or '')}: {str(desc or '')[:300]}",
                          str(ev_date or ""), actor,
                          f"Timeline entry + {', '.join(prov_info['case_law'][:2])}"))
                    count += 1
            except sqlite3.Error:
                pass

            # Search judicial violations table
            try:
                rows = central.execute("""
                    SELECT violation_type, description, severity
                    FROM judicial_violations
                    WHERE LOWER(description) LIKE ?
                    LIMIT 50
                """, (f"%{trigger}%",)).fetchall()

                for vtype, desc, sev in rows:
                    mdb.execute("""
                        INSERT INTO violations
                        (provision, provision_name, violating_event,
                         actor, evidence, severity)
                        VALUES (?, ?, ?, 'McNeill', ?, ?)
                    """, (prov_key, prov_info["provision"],
                          str(desc or "")[:300],
                          f"judicial_violations/{str(vtype or '')}",
                          str(sev or "high")))
                    count += 1
            except sqlite3.Error:
                pass

        provision_counts[prov_key] = {
            "provision": prov_info["provision"],
            "violation_count": count,
            "case_law": prov_info["case_law"],
        }

    mdb.commit()
    return provision_counts


def _build_1983_counts(mdb: sqlite3.Connection) -> list[dict]:
    """Build §1983 count structure from mapped violations."""
    counts = [
        {
            "count": 1,
            "title": "Deprivation of Substantive Due Process — Parental Liberty",
            "basis": "14th_substantive_dp",
            "defendant": "Judge Jenny L. McNeill, Emily A. Watson",
        },
        {
            "count": 2,
            "title": "Deprivation of Procedural Due Process — Ex Parte Orders",
            "basis": "14th_procedural_dp",
            "defendant": "Judge Jenny L. McNeill",
        },
        {
            "count": 3,
            "title": "Equal Protection Violation — Gender Discrimination",
            "basis": "14th_equal_protection",
            "defendant": "Judge Jenny L. McNeill",
        },
        {
            "count": 4,
            "title": "Conspiracy to Deprive Civil Rights — 42 USC §1985(3)",
            "basis": "14th_substantive_dp",
            "defendant": "Emily A. Watson, Ron Berry, Judge Jenny L. McNeill",
        },
    ]

    for c in counts:
        supporting = mdb.execute("""
            SELECT COUNT(*) FROM violations WHERE provision = ?
        """, (c["basis"],)).fetchone()[0]
        c["supporting_violations"] = supporting

        mdb.execute("""
            INSERT INTO section_1983_counts
            (count_number, title, constitutional_basis, defendant, violations_supporting)
            VALUES (?, ?, ?, ?, ?)
        """, (c["count"], c["title"], c["basis"], c["defendant"], supporting))

    mdb.commit()
    return counts


def run_mapping() -> dict:
    """Run complete constitutional violation mapping."""
    start = time.time()
    mdb = _init_db()
    central = sqlite3.connect(str(CENTRAL_DB), timeout=30)
    central.execute("PRAGMA busy_timeout=120000")

    mdb.execute("DELETE FROM violations")
    mdb.execute("DELETE FROM section_1983_counts")

    provisions = _map_violations(central, mdb)
    counts_1983 = _build_1983_counts(mdb)

    total = sum(v["violation_count"] for v in provisions.values())
    violated = sum(1 for v in provisions.values() if v["violation_count"] > 0)

    duration = round(time.time() - start, 2)
    mdb.execute("""
        INSERT INTO mapping_runs
        (total_violations, provisions_violated, defendants_implicated, duration_s)
        VALUES (?, ?, 3, ?)
    """, (total, violated, duration))
    mdb.commit()

    central.close()
    mdb.close()

    return {
        "provisions": provisions,
        "total_violations": total,
        "provisions_violated": f"{violated}/{len(CONSTITUTIONAL_PROVISIONS)}",
        "section_1983_counts": [
            {"count": c["count"], "title": c["title"],
             "defendant": c["defendant"], "supporting": c["supporting_violations"]}
            for c in counts_1983
        ],
        "duration_s": duration,
    }


if __name__ == "__main__":
    result = run_mapping()
    print(json.dumps(result, indent=2, default=str))
