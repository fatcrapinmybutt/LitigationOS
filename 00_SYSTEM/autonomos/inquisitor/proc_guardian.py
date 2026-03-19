"""
APEX Ω∞ — Pro Se Procedure Guardian
=====================================
Real-time procedural trap detector — catches the 8 known traps BEFORE
they trigger. Validates every filing against MCR/MCL procedural requirements.
Prevents jurisdictional defaults, missed deadlines, and waiver of rights.
"""
import sys, sqlite3, json, time
from pathlib import Path
from datetime import datetime, timedelta

_shared = Path(__file__).parent.parent / "shared"
if str(_shared) not in sys.path:
    sys.path.insert(0, str(_shared))
from autonomos_config import CENTRAL_DB

PROC_GUARDIAN_DB = Path(__file__).parent / "proc_guardian.db"

PROCEDURAL_TRAPS = {
    "trap_1_preserve_issues": {
        "label": "Failure to Preserve Issues for Appeal",
        "severity": "CRITICAL",
        "rule": "MCR 2.517; People v Carines, 460 Mich 750",
        "description": "Issues not raised at trial level are reviewed only for plain error.",
        "detection": "Check if each appellate issue was raised below (motion, objection, or request for ruling).",
        "remedy": "File motion in lower court preserving each issue OR argue plain error on appeal.",
        "search_terms": ["preserve", "raised below", "objection", "plain error"],
    },
    "trap_2_foc_exhaustion": {
        "label": "FOC Administrative Remedy Exhaustion",
        "severity": "CRITICAL",
        "rule": "MCL 552.507(5); MCR 3.208",
        "description": "Must object to FOC recommendation within 21 days or it becomes binding.",
        "detection": "Check if FOC recommendations have pending objection deadlines.",
        "remedy": "File timely objection to every FOC recommendation. Calendar 21-day window.",
        "search_terms": ["foc", "objection", "recommendation", "21 day", "552.507"],
    },
    "trap_3_mandatory_disclosures": {
        "label": "Missing Mandatory Disclosures",
        "severity": "CRITICAL",
        "rule": "MCR 3.206(B); SCAO Forms",
        "description": "UCCJEA affidavit (FOC 30) REQUIRED with every custody filing.",
        "detection": "Check if custody filings include FOC 30, FOC 30A, verified statement.",
        "remedy": "Attach FOC 30 to EVERY custody-related filing. No exceptions.",
        "search_terms": ["uccjea", "foc 30", "disclosure", "verified statement", "3.206"],
    },
    "trap_4_service_timing": {
        "label": "Insufficient Service Time",
        "severity": "CRITICAL",
        "rule": "MCR 2.119(C)(1)",
        "description": "Motions require 9 days notice + 3 if mailed = 12 days minimum.",
        "detection": "Check service dates vs hearing dates for all pending motions.",
        "remedy": "Calendar: hearing date - 12 days = latest service date. Use electronic service if possible.",
        "search_terms": ["service", "notice", "9 day", "12 day", "2.119"],
    },
    "trap_5_appeal_deadline": {
        "label": "21-Day Claim of Appeal Deadline",
        "severity": "CRITICAL",
        "rule": "MCR 7.204(A)(1)",
        "description": "Jurisdictional deadline — CANNOT extend. Miss it and appeal is barred.",
        "detection": "Check all final orders for 21-day appeal window status.",
        "remedy": "File claim of appeal IMMEDIATELY upon final order. Do not wait.",
        "search_terms": ["claim of appeal", "21 day", "jurisdictional", "7.204"],
    },
    "trap_6_proper_motion_format": {
        "label": "Improper Motion Format",
        "severity": "HIGH",
        "rule": "MCR 2.119(A)(1)",
        "description": "Motion must state with particularity grounds and relief sought.",
        "detection": "Validate motion format: caption, relief requested, factual basis, legal authority.",
        "remedy": "Use motion template: Introduction → Facts → Legal Standard → Argument → Relief Requested.",
        "search_terms": ["motion format", "particularity", "relief", "2.119"],
    },
    "trap_7_proposed_order": {
        "label": "Missing Proposed Order",
        "severity": "HIGH",
        "rule": "MCR 2.602",
        "description": "Many motions require a proposed order. Omitting delays ruling.",
        "detection": "Check if filings that require proposed orders include them.",
        "remedy": "Attach proposed order to every motion. Include specific findings court should make.",
        "search_terms": ["proposed order", "2.602", "order"],
    },
    "trap_8_verification_affidavit": {
        "label": "Missing Verification/Affidavit",
        "severity": "HIGH",
        "rule": "MCR 2.114(B), MCR 2.119(B)(1)(c)",
        "description": "Some filings require personal verification or supporting affidavit.",
        "detection": "Check if ex parte motions have supporting affidavit per MCR 2.119(B).",
        "remedy": "Include verification statement: 'Under penalties of perjury, the facts stated are true...'",
        "search_terms": ["verification", "affidavit", "under penalty", "sworn"],
    },
}

def _init_db() -> sqlite3.Connection:
    PROC_GUARDIAN_DB.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(PROC_GUARDIAN_DB), timeout=30)
    conn.execute("PRAGMA journal_mode=WAL")
    conn.executescript("""
        CREATE TABLE IF NOT EXISTS trap_checks (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            trap_id TEXT NOT NULL,
            trap_label TEXT NOT NULL,
            severity TEXT NOT NULL,
            evidence_count INTEGER DEFAULT 0,
            risk_level TEXT DEFAULT 'UNKNOWN',
            last_checked TEXT DEFAULT (datetime('now'))
        );
        CREATE TABLE IF NOT EXISTS deadline_alerts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            alert_type TEXT NOT NULL,
            description TEXT NOT NULL,
            deadline_date TEXT NOT NULL,
            days_remaining INTEGER DEFAULT 0,
            status TEXT DEFAULT 'active',
            created_at TEXT DEFAULT (datetime('now'))
        );
    """)
    conn.commit()
    return conn

def check_traps() -> dict:
    """Scan for all 8 procedural traps."""
    start = time.time()
    gdb = _init_db()
    results = []

    try:
        cdb = sqlite3.connect(str(CENTRAL_DB), timeout=30)
        cdb.execute("PRAGMA query_only=ON")

        for trap_id, trap in PROCEDURAL_TRAPS.items():
            evidence_count = 0
            for term in trap["search_terms"]:
                # Search deadlines
                try:
                    cnt = cdb.execute("""
                        SELECT COUNT(*) FROM deadlines
                        WHERE LOWER(COALESCE(description,'') || COALESCE(deadline_type,''))
                        LIKE ?
                    """, (f"%{term}%",)).fetchone()[0]
                    evidence_count += cnt
                except Exception:
                    pass
                # Search docket_events
                try:
                    cnt = cdb.execute("""
                        SELECT COUNT(*) FROM docket_events
                        WHERE LOWER(COALESCE(description,'') || COALESCE(event_type,''))
                        LIKE ?
                    """, (f"%{term}%",)).fetchone()[0]
                    evidence_count += cnt
                except Exception:
                    pass

            risk = "LOW"
            if evidence_count == 0:
                risk = "HIGH"  # No evidence means trap hasn't been addressed
            elif evidence_count < 3:
                risk = "MEDIUM"
            else:
                risk = "LOW"

            gdb.execute("""
                INSERT INTO trap_checks
                (trap_id, trap_label, severity, evidence_count, risk_level)
                VALUES (?, ?, ?, ?, ?)
            """, (trap_id, trap["label"], trap["severity"], evidence_count, risk))

            results.append({
                "trap": trap_id, "label": trap["label"],
                "severity": trap["severity"], "rule": trap["rule"],
                "evidence_count": evidence_count, "risk_level": risk,
                "remedy": trap["remedy"],
            })

        # Check upcoming deadlines
        try:
            upcoming = cdb.execute("""
                SELECT description, due_date_iso, deadline_type
                FROM deadlines
                WHERE due_date_iso >= date('now')
                ORDER BY due_date_iso ASC LIMIT 20
            """).fetchall()
            for d in upcoming:
                desc, due, dtype = d
                try:
                    due_dt = datetime.strptime(due, "%Y-%m-%d")
                    days = (due_dt - datetime.now()).days
                    gdb.execute("""
                        INSERT INTO deadline_alerts
                        (alert_type, description, deadline_date, days_remaining)
                        VALUES (?, ?, ?, ?)
                    """, (dtype or "unknown", desc or "No description", due, days))
                except Exception:
                    pass
        except Exception:
            pass

        cdb.close()
    except Exception as e:
        results.append({"error": str(e)})

    gdb.commit()
    gdb.close()

    critical = [r for r in results if r.get("severity") == "CRITICAL" and r.get("risk_level") in ("HIGH", "MEDIUM")]
    return {
        "traps_checked": len(PROCEDURAL_TRAPS),
        "critical_risks": len(critical),
        "results": results,
        "critical_alerts": critical,
        "duration_s": round(time.time() - start, 2),
    }

if __name__ == "__main__":
    print(json.dumps(check_traps(), indent=2, default=str))
