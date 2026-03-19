"""
APEX Ω∞ — Discovery Demand Generator
======================================
Auto-generates interrogatories, RFPs, RFAs per MCR 2.309/2.310/2.312.
Targets Watson financial records, communication records, McNeill ex parte logs.
Tracks response deadlines (28 days per MCR 2.309(B)(2)).
"""
import sys, sqlite3, json, time
from pathlib import Path
from datetime import datetime, timedelta

_shared = Path(__file__).parent.parent / "shared"
if str(_shared) not in sys.path:
    sys.path.insert(0, str(_shared))
from autonomos_config import CENTRAL_DB, LITIGOS_ROOT

DISCOVERY_DB = Path(__file__).parent / "discovery_gen.db"
OUTPUT_DIR = LITIGOS_ROOT / "06_FILINGS" / "DISCOVERY"

DISCOVERY_SETS = {
    "interrogatories_watson": {
        "type": "Interrogatories", "mcr": "MCR 2.309",
        "target": "Emily A. Watson", "deadline_days": 28,
        "questions": [
            "State your current residential address and all addresses at which you have resided since January 1, 2023.",
            "Identify all sources of income, including employment, government benefits, gifts, and loans, for the period January 1, 2023 to present.",
            "State the dates, times, and content of ALL communications with Judge Jenny L. McNeill or her staff outside of formal court proceedings.",
            "Identify all communications with Ron Berry, including dates, methods, and subject matter.",
            "Describe in detail the circumstances of each instance in which you denied or interfered with Plaintiff's parenting time since August 8, 2025.",
            "State whether you have been diagnosed with or treated for any mental health condition. If so, identify the provider and dates.",
            "Identify all persons who have had contact with the minor child during parenting time exchanges since January 1, 2024.",
            "Describe all instances in which Albert Watson, Lori Watson, or Cody Watson were present during custody exchanges or had contact with the minor child.",
            "State whether you have filed any reports with CPS, law enforcement, or other agencies regarding Plaintiff. If so, provide dates, agencies, and outcomes.",
            "Identify all bank accounts, credit cards, and financial assets held individually or jointly since January 1, 2023.",
        ],
    },
    "rfp_watson": {
        "type": "Request for Production", "mcr": "MCR 2.310",
        "target": "Emily A. Watson", "deadline_days": 28,
        "requests": [
            "All text messages, emails, and written communications between you and Ron Berry from January 1, 2024 to present.",
            "All text messages, emails, and written communications between you and any employee or staff of the 14th Circuit Court from January 1, 2024 to present.",
            "All financial records including bank statements, pay stubs, and tax returns for 2023 and 2024.",
            "All records of the minor child's medical appointments, school records, and extracurricular activities.",
            "All photographs, videos, or recordings related to custody exchanges or parenting time.",
            "All documents filed or prepared for filing in any court regarding the minor child.",
            "All communications with Mandi Martini regarding this case.",
            "All records of payments to or from Albert Watson, Lori Watson, or Cody Watson.",
        ],
    },
    "rfa_watson": {
        "type": "Request for Admissions", "mcr": "MCR 2.312",
        "target": "Emily A. Watson", "deadline_days": 28,
        "requests": [
            "Admit that you had contact with Ron Berry regarding this case prior to any formal court proceedings.",
            "Admit that Judge McNeill entered orders on August 8, 2025 without providing notice to Plaintiff.",
            "Admit that you denied Plaintiff parenting time on [SPECIFIC DATES].",
            "Admit that Albert Watson was present during custody exchanges on [SPECIFIC DATES].",
            "Admit that you communicated with the Friend of the Court office without copying Plaintiff.",
            "Admit that you filed a Personal Protection Order petition that was subsequently dismissed.",
            "Admit that the minor child has expressed a desire to see his father.",
            "Admit that you have not complied with [SPECIFIC COURT ORDER] dated [DATE].",
        ],
    },
}

def _init_db() -> sqlite3.Connection:
    DISCOVERY_DB.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(DISCOVERY_DB), timeout=30)
    conn.execute("PRAGMA journal_mode=WAL")
    conn.executescript("""
        CREATE TABLE IF NOT EXISTS discovery_sets (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            set_key TEXT NOT NULL,
            discovery_type TEXT NOT NULL,
            target TEXT NOT NULL,
            item_count INTEGER DEFAULT 0,
            output_path TEXT DEFAULT '',
            served_date TEXT DEFAULT '',
            response_deadline TEXT DEFAULT '',
            response_received INTEGER DEFAULT 0,
            generated_at TEXT DEFAULT (datetime('now'))
        );
    """)
    conn.commit()
    return conn

def generate_discovery(set_key: str = None) -> dict:
    """Generate discovery demand documents."""
    start = time.time()
    ddb = _init_db()
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    results = []
    sets = {set_key: DISCOVERY_SETS[set_key]} if set_key and set_key in DISCOVERY_SETS else DISCOVERY_SETS

    for sk, sinfo in sets.items():
        now = datetime.now()
        deadline = (now + timedelta(days=sinfo["deadline_days"])).strftime("%Y-%m-%d")
        items = sinfo.get("questions") or sinfo.get("requests", [])

        parts = []
        parts.append("STATE OF MICHIGAN")
        parts.append("IN THE 14TH CIRCUIT COURT FOR THE COUNTY OF MUSKEGON\n")
        parts.append("ANDREW J. PIGORS,                    Case No. 2024-001507-DC")
        parts.append("        Plaintiff,                   Hon. Jenny L. McNeill")
        parts.append("v.")
        parts.append("EMILY A. WATSON,")
        parts.append("        Defendant.")
        parts.append(f"{'_' * 50}/\n")
        parts.append(f"PLAINTIFF'S {sinfo['type'].upper()} TO DEFENDANT")
        parts.append(f"({sinfo['mcr']})\n")
        parts.append(f"TO: {sinfo['target']}\n")
        parts.append(f"Pursuant to {sinfo['mcr']}, Plaintiff requests that Defendant")
        parts.append(f"respond to the following within {sinfo['deadline_days']} days:\n")

        label = "INTERROGATORY" if "interrog" in sk else "REQUEST"
        for i, item in enumerate(items, 1):
            parts.append(f"  {label} NO. {i}:")
            parts.append(f"  {item}\n")

        parts.append(f"\nRespectfully submitted,")
        parts.append(f"Date: {now.strftime('%B %d, %Y')}")
        parts.append(f"\n                    ________________________________")
        parts.append(f"                    Andrew J. Pigors, Pro Se\n")
        parts.append(f"CERTIFICATE OF SERVICE")
        parts.append(f"I certify service upon {sinfo['target']} on [DATE] by [METHOD].")

        content = "\n".join(parts)
        fname = f"{sk}_{now.strftime('%Y%m%d')}.txt"
        output_file = OUTPUT_DIR / fname
        output_file.write_text(content, encoding="utf-8")

        ddb.execute("""
            INSERT INTO discovery_sets
            (set_key, discovery_type, target, item_count, output_path, response_deadline)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (sk, sinfo["type"], sinfo["target"], len(items), str(output_file), deadline))

        results.append({
            "set": sk, "type": sinfo["type"], "target": sinfo["target"],
            "items": len(items), "output": str(output_file), "deadline": deadline,
        })

    ddb.commit()
    ddb.close()
    return {"sets_generated": len(results), "results": results,
            "duration_s": round(time.time() - start, 2)}

if __name__ == "__main__":
    sk = sys.argv[1] if len(sys.argv) > 1 else None
    print(json.dumps(generate_discovery(sk), indent=2, default=str))
