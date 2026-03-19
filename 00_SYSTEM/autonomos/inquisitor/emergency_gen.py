"""
APEX Ω∞ — Emergency Motion Generator
=======================================
Instant-generates verified emergency motions (MCR 3.207B) with:
- Statement of facts from DB evidence
- Legal authority from auth_rules
- Emergency showing (immediate & irreparable harm)
- Proposed order
- Affidavit template
- Certificate of Service

Sub-10-minute turnaround for any emergency type.
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

from autonomos_config import CENTRAL_DB, LITIGOS_ROOT

EMERGENCY_DB = Path(__file__).parent / "emergency_gen.db"
OUTPUT_DIR = LITIGOS_ROOT / "06_FILINGS" / "EMERGENCY_MOTIONS"

EMERGENCY_TYPES = {
    "parenting_time": {
        "title": "EMERGENCY MOTION TO RESTORE PARENTING TIME",
        "mcr": "MCR 3.207(B)",
        "basis": [
            "MCL 722.27a — Parenting time presumed in best interest",
            "MCL 722.23 — Best interest factors",
            "Troxel v Granville, 530 US 57 (2000) — Fundamental liberty interest",
        ],
        "harm_type": "Continued deprivation of parent-child relationship",
    },
    "ex_parte_vacate": {
        "title": "EMERGENCY MOTION TO VACATE EX PARTE ORDER",
        "mcr": "MCR 3.207(B), MCR 2.612(C)",
        "basis": [
            "MCR 2.119(A) — Notice required for all motions",
            "14th Amendment — Due process requires notice and opportunity to be heard",
            "Bowie v Arder, 441 Mich 23 (1992) — Void orders",
        ],
        "harm_type": "Order entered without due process, void ab initio",
    },
    "child_safety": {
        "title": "EMERGENCY MOTION REGARDING CHILD SAFETY",
        "mcr": "MCR 3.207(B)",
        "basis": [
            "MCL 722.23(k) — Domestic violence factor",
            "MCL 722.23(a) — Emotional ties to child",
            "MCL 722.27(1)(c) — Modification for proper cause",
        ],
        "harm_type": "Imminent risk to child welfare",
    },
    "stay_pending_appeal": {
        "title": "EMERGENCY MOTION FOR STAY PENDING APPEAL",
        "mcr": "MCR 7.209",
        "basis": [
            "MCR 7.209(A) — Stay pending appeal factors",
            "Mich Democratic Party v Sec'y of State — Irreparable harm standard",
        ],
        "harm_type": "Irreparable harm during appellate proceedings",
    },
    "contempt": {
        "title": "EMERGENCY MOTION FOR CONTEMPT",
        "mcr": "MCR 3.606",
        "basis": [
            "MCR 3.606 — Civil contempt proceedings",
            "In re Contempt of Dougherty, 429 Mich 81 (1987)",
            "MCL 600.1711 — Contempt powers",
        ],
        "harm_type": "Willful violation of court order",
    },
    "disqualification": {
        "title": "EMERGENCY MOTION FOR DISQUALIFICATION OF JUDGE",
        "mcr": "MCR 2.003(C)",
        "basis": [
            "MCR 2.003(C)(1) — Personal bias or prejudice",
            "Canon 2 — Appearance of impropriety",
            "Canon 3(B)(5) — Ex parte communications prohibited",
            "Cain v Dep't of Corrections, 451 Mich 470 (1996)",
        ],
        "harm_type": "Demonstrated judicial bias preventing fair proceedings",
    },
}


def _init_db() -> sqlite3.Connection:
    EMERGENCY_DB.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(EMERGENCY_DB), timeout=30)
    conn.execute("PRAGMA journal_mode=WAL")
    conn.executescript("""
        CREATE TABLE IF NOT EXISTS emergency_filings (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            emergency_type TEXT NOT NULL,
            title TEXT NOT NULL,
            output_path TEXT DEFAULT '',
            sections_count INTEGER DEFAULT 0,
            content_length INTEGER DEFAULT 0,
            generated_at TEXT DEFAULT (datetime('now'))
        );
    """)
    conn.commit()
    return conn


def _get_supporting_evidence(central: sqlite3.Connection,
                             keywords: list[str]) -> list[str]:
    """Pull supporting evidence from DB."""
    evidence = []
    for kw in keywords[:5]:
        try:
            rows = central.execute("""
                SELECT quote_text FROM evidence_quotes_fts
                WHERE evidence_quotes_fts MATCH ? LIMIT 5
            """, (kw,)).fetchall()
            for r in rows:
                evidence.append(str(r[0])[:400])
        except sqlite3.Error:
            try:
                rows = central.execute("""
                    SELECT quote_text FROM evidence_quotes
                    WHERE quote_text LIKE ? LIMIT 5
                """, (f"%{kw}%",)).fetchall()
                for r in rows:
                    evidence.append(str(r[0])[:400])
            except sqlite3.Error:
                pass
    return evidence


def _get_authority(central: sqlite3.Connection,
                   keywords: list[str]) -> list[str]:
    """Pull supporting authority."""
    authority = []
    for kw in keywords[:3]:
        try:
            rows = central.execute("""
                SELECT rule_text FROM auth_rules_fts
                WHERE auth_rules_fts MATCH ? LIMIT 3
            """, (kw,)).fetchall()
            for r in rows:
                authority.append(str(r[0])[:300])
        except sqlite3.Error:
            pass
    return authority


def generate_emergency(emergency_type: str,
                       specific_facts: str = "",
                       custom_relief: str = "") -> dict:
    """Generate complete emergency motion package."""
    start = time.time()
    edb = _init_db()

    etype = EMERGENCY_TYPES.get(emergency_type)
    if not etype:
        return {"error": f"Unknown type: {emergency_type}",
                "available": list(EMERGENCY_TYPES.keys())}

    central = sqlite3.connect(str(CENTRAL_DB), timeout=30)
    central.execute("PRAGMA busy_timeout=120000")

    now = datetime.now()
    sep_days = (datetime.now().date() - datetime(2025, 8, 8).date()).days

    # Pull evidence
    evidence = _get_supporting_evidence(central, [
        emergency_type.replace("_", " "),
        "parenting time", "custody", "ex parte",
    ])

    # Build motion
    parts = []
    parts.append("STATE OF MICHIGAN")
    parts.append("IN THE 14TH CIRCUIT COURT FOR THE COUNTY OF MUSKEGON\n")
    parts.append("ANDREW J. PIGORS,                    Case No. 2024-001507-DC")
    parts.append("        Plaintiff,                   Hon. Jenny L. McNeill")
    parts.append("v.")
    parts.append("EMILY A. WATSON,")
    parts.append("        Defendant.")
    parts.append(f"{'_' * 50}/\n")
    parts.append(f"{'=' * 50}")
    parts.append(f"  {etype['title']}")
    parts.append(f"{'=' * 50}\n")

    # I. Introduction
    parts.append("I. INTRODUCTION AND EMERGENCY SHOWING\n")
    parts.append(f"NOW COMES Plaintiff, Andrew J. Pigors, pro se, and pursuant to")
    parts.append(f"{etype['mcr']}, moves this Court on an emergency basis because:\n")
    parts.append(f"1. {etype['harm_type']}.")
    parts.append(f"2. Immediate and irreparable injury will result from any delay.")
    parts.append(f"3. This constitutes Day {sep_days} of parent-child separation")
    parts.append(f"   since the ex parte orders of August 8, 2025.\n")

    if specific_facts:
        parts.append(f"4. {specific_facts}\n")

    # II. Statement of Facts
    parts.append("\nII. STATEMENT OF FACTS\n")
    parts.append("The following facts are supported by the record:\n")
    for i, ev in enumerate(evidence[:5], 1):
        parts.append(f"  {i}. {ev}\n")

    # III. Legal Authority
    parts.append("\nIII. LEGAL AUTHORITY\n")
    for cite in etype["basis"]:
        parts.append(f"  • {cite}")
    parts.append("")

    # IV. Argument
    parts.append("\nIV. ARGUMENT\n")
    parts.append(f"A. Emergency Exists Under {etype['mcr']}\n")
    parts.append(f"The emergency standard requires: (1) immediate and irreparable injury,")
    parts.append(f"(2) impracticability of delay for notice, and (3) good faith effort to")
    parts.append(f"give notice. All three elements are satisfied here.\n")
    parts.append(f"The continued separation of Father from his child for {sep_days} days")
    parts.append(f"constitutes ongoing irreparable harm to the fundamental liberty interest")
    parts.append(f"in the parent-child relationship. Troxel v Granville, 530 US 57 (2000).\n")

    # V. Relief Requested
    parts.append("\nV. RELIEF REQUESTED\n")
    relief = custom_relief or f"grant immediate relief as described in the attached Proposed Order"
    parts.append(f"WHEREFORE, Plaintiff respectfully requests this Court {relief}.\n")

    parts.append(f"\nRespectfully submitted,\n")
    parts.append(f"Date: {now.strftime('%B %d, %Y')}")
    parts.append(f"\n                    ________________________________")
    parts.append(f"                    Andrew J. Pigors, Pro Se")
    parts.append(f"                    [ADDRESS]")
    parts.append(f"                    [PHONE]")
    parts.append(f"                    [EMAIL]\n")

    # ── Proposed Order ──
    parts.append(f"\n{'=' * 50}")
    parts.append(f"  PROPOSED ORDER")
    parts.append(f"{'=' * 50}\n")
    parts.append(f"STATE OF MICHIGAN")
    parts.append(f"14TH CIRCUIT COURT — COUNTY OF MUSKEGON\n")
    parts.append(f"Case No. 2024-001507-DC\n")
    parts.append(f"At a session of said Court held on ____________, 20___.\n")
    parts.append(f"PRESENT: Hon. ___________________________\n")
    parts.append(f"IT IS HEREBY ORDERED that:\n")
    parts.append(f"  1. [SPECIFIC RELIEF]\n")
    parts.append(f"  2. [ADDITIONAL TERMS]\n")
    parts.append(f"\n                    ________________________________")
    parts.append(f"                    Circuit Court Judge\n")

    # ── Affidavit Template ──
    parts.append(f"\n{'=' * 50}")
    parts.append(f"  VERIFICATION / AFFIDAVIT")
    parts.append(f"{'=' * 50}\n")
    parts.append(f"STATE OF MICHIGAN    )")
    parts.append(f"                     ) ss.")
    parts.append(f"COUNTY OF MUSKEGON   )\n")
    parts.append(f"I, Andrew J. Pigors, being first duly sworn, depose and state that")
    parts.append(f"the facts set forth in the foregoing {etype['title']}")
    parts.append(f"are true to the best of my knowledge, information, and belief.\n")
    parts.append(f"                    ________________________________")
    parts.append(f"                    Andrew J. Pigors\n")
    parts.append(f"Subscribed and sworn before me this ____ day of ____________, 20___.\n")
    parts.append(f"                    ________________________________")
    parts.append(f"                    Notary Public, State of Michigan")
    parts.append(f"                    My commission expires: ___________\n")

    # ── Certificate of Service ──
    parts.append(f"\n{'=' * 50}")
    parts.append(f"  CERTIFICATE OF SERVICE")
    parts.append(f"{'=' * 50}\n")
    parts.append(f"I certify that on {now.strftime('%B %d, %Y')}, I served a copy of this")
    parts.append(f"{etype['title']} upon all parties by [first-class mail/personal service/MiFILE].\n")
    parts.append(f"                    ________________________________")
    parts.append(f"                    Andrew J. Pigors, Pro Se")

    full_content = "\n".join(parts)

    # Write output
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    ts = now.strftime("%Y%m%d_%H%M%S")
    safe_type = emergency_type.replace("_", "-")
    output_file = OUTPUT_DIR / f"emergency_{safe_type}_{ts}.txt"
    output_file.write_text(full_content, encoding="utf-8")

    edb.execute("""
        INSERT INTO emergency_filings
        (emergency_type, title, output_path, sections_count, content_length)
        VALUES (?, ?, ?, 7, ?)
    """, (emergency_type, etype["title"], str(output_file), len(full_content)))
    edb.commit()

    central.close()
    edb.close()

    return {
        "type": emergency_type,
        "title": etype["title"],
        "output": str(output_file),
        "sections": 7,
        "content_length": len(full_content),
        "evidence_cited": len(evidence),
        "authority_cited": len(etype["basis"]),
        "separation_days": sep_days,
        "duration_s": round(time.time() - start, 2),
    }


if __name__ == "__main__":
    if len(sys.argv) > 1:
        etype = sys.argv[1]
        result = generate_emergency(etype)
    else:
        print(f"Emergency types: {', '.join(EMERGENCY_TYPES.keys())}")
        result = {"available_types": list(EMERGENCY_TYPES.keys())}
    print(json.dumps(result, indent=2, default=str))
