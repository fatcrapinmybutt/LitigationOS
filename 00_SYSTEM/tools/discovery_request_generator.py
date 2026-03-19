#!/usr/bin/env python3
"""
NOVEL TOOL #33: Discovery Request Generator
==============================================
Auto-generates targeted discovery requests (interrogatories,
requests for production, requests for admission) based on:
- Known contradictions in opponent's statements
- Evidence gaps identified by other tools
- Perjury evidence requiring sworn responses
- Judicial misconduct requiring court records

Michigan-specific:
- MCR 2.309 (Interrogatories)
- MCR 2.310 (Requests for Production)
- MCR 2.312 (Requests for Admission)
- 35-interrogatory limit per MCR 2.309(A)(2)

This automates what takes attorneys 10+ hours of manual work.
"""

import sys
import os
import json
import sqlite3
from pathlib import Path
from datetime import datetime

sys.stdout = open(sys.stdout.fileno(), mode='w', encoding='utf-8', errors='replace')

DB_PATH = Path(r"C:\Users\andre\LitigationOS\litigation_context.db")
REPORTS_DIR = Path(r"C:\Users\andre\LitigationOS\00_SYSTEM\reports")

PLAINTIFF = {
    "name": "ANDREW JAMES PIGORS",
    "address": "1977 Whitehall Road, Lot 17\nNorth Muskegon, MI 49445",
    "phone": "(231) 903-5690",
    "email": "andrewjpigors@gmail.com"
}

DEFENDANT = {
    "name": "EMILY A. WATSON",
    "address": "2160 Garland Drive\nNorton Shores, MI 49441"
}


def get_db_connection():
    conn = sqlite3.connect(str(DB_PATH), timeout=60)
    conn.execute("PRAGMA busy_timeout=60000")
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA cache_size=-32000")
    conn.row_factory = sqlite3.Row
    return conn


def get_contradictions(conn, limit=20):
    """Get high-severity contradictions for targeted discovery."""
    try:
        rows = conn.execute("""
            SELECT speaker, statement_1, source_1, statement_2, source_2,
                   contradiction_type, severity
            FROM detected_contradictions
            WHERE severity >= 7
            ORDER BY severity DESC
            LIMIT ?
        """, (limit,)).fetchall()
        return [dict(r) for r in rows]
    except Exception:
        return []


def get_perjury_evidence(conn, limit=20):
    """Get prosecution-ready perjury for admission requests."""
    try:
        rows = conn.execute("""
            SELECT watson_member, statement_text, contradicting_evidence,
                   source_doc, perjury_type, severity_score
            FROM watson_perjury_compilation
            WHERE severity_score >= 8 AND admissible = 1
            ORDER BY severity_score DESC
            LIMIT ?
        """, (limit,)).fetchall()
        return [dict(r) for r in rows]
    except Exception:
        return []


def get_adversary_assertions(conn, limit=20):
    """Get false assertions for targeted discovery."""
    try:
        rows = conn.execute("""
            SELECT speaker, assertion_text, assertion_type, rebuttal_evidence, severity
            FROM adversary_assertions
            WHERE is_false = 1 AND severity >= 7
            ORDER BY severity DESC
            LIMIT ?
        """, (limit,)).fetchall()
        return [dict(r) for r in rows]
    except Exception:
        return []


def generate_interrogatories(contradictions, perjury, assertions):
    """Generate interrogatories (max 35 per MCR 2.309(A)(2))."""
    interrogatories = []
    used = 0

    # From contradictions — demand explanation
    for c in contradictions[:10]:
        if used >= 35:
            break
        used += 1
        speaker = c.get("speaker", "you")
        stmt1 = (c.get("statement_1") or "")[:150]
        stmt2 = (c.get("statement_2") or "")[:150]
        interrogatories.append({
            "number": used,
            "category": "Contradiction",
            "severity": c.get("severity", 5),
            "text": (
                f"In {c.get('source_1', 'a prior statement')}, {speaker} stated: "
                f"\"{stmt1}\". However, in {c.get('source_2', 'another statement')}, "
                f"{speaker} stated: \"{stmt2}\". "
                f"Please explain the discrepancy between these two statements, "
                f"identify which statement is accurate, and state all facts "
                f"supporting the accurate statement."
            ),
            "source": "detected_contradictions"
        })

    # From perjury — demand facts
    for p in perjury[:10]:
        if used >= 35:
            break
        used += 1
        stmt = (p.get("statement_text") or "")[:200]
        interrogatories.append({
            "number": used,
            "category": "Perjury Investigation",
            "severity": p.get("severity_score", 5),
            "text": (
                f"Regarding your statement: \"{stmt}\", "
                f"please identify: (a) the date you made this statement; "
                f"(b) all persons present when you made this statement; "
                f"(c) all documents supporting this statement; "
                f"(d) whether you were under oath; and "
                f"(e) whether you still maintain this statement is true."
            ),
            "source": "watson_perjury_compilation"
        })

    # From assertions — demand proof
    for a in assertions[:10]:
        if used >= 35:
            break
        used += 1
        stmt = (a.get("assertion_text") or "")[:200]
        interrogatories.append({
            "number": used,
            "category": "False Assertion",
            "severity": a.get("severity", 5),
            "text": (
                f"You have asserted: \"{stmt}\". "
                f"Please identify: (a) all evidence supporting this assertion; "
                f"(b) all witnesses who can corroborate this assertion; "
                f"(c) all documents relating to this assertion; and "
                f"(d) whether you have any reason to believe this assertion "
                f"may be inaccurate or incomplete."
            ),
            "source": "adversary_assertions"
        })

    # Standard custody interrogatories
    standard = [
        "State your current residential address, all persons residing with you, and the relationship of each person to L.D.W.",
        "Identify all persons who have provided childcare for L.D.W. in the past 12 months, including dates and duration.",
        "State all communications you have had with Ronald T. Berry regarding this litigation, including dates, methods, and substance.",
        "Identify all income sources, employment, and financial support you have received in the past 24 months.",
        "State whether you have ever been investigated by Child Protective Services, and if so, provide dates, case numbers, and outcomes."
    ]

    for s in standard:
        if used >= 35:
            break
        used += 1
        interrogatories.append({
            "number": used,
            "category": "Standard Custody",
            "severity": 5,
            "text": s,
            "source": "standard"
        })

    return interrogatories


def generate_production_requests(contradictions, perjury):
    """Generate requests for production of documents."""
    requests = []

    requests.append({
        "number": 1,
        "text": "All text messages, emails, and electronic communications between you and Ronald T. Berry from January 1, 2023 to present.",
        "category": "Communications"
    })
    requests.append({
        "number": 2,
        "text": "All text messages, emails, and electronic communications between you and Jennifer Barnes (P55406) from January 1, 2023 to present.",
        "category": "Attorney Communications"
    })
    requests.append({
        "number": 3,
        "text": "All photographs, videos, and recordings relating to L.D.W., Andrew Pigors, or any incident described in your pleadings, from January 1, 2023 to present.",
        "category": "Media Evidence"
    })
    requests.append({
        "number": 4,
        "text": "All medical records for L.D.W. from January 1, 2023 to present, including but not limited to pediatric visits, ER visits, therapy records, and medication records.",
        "category": "Medical"
    })
    requests.append({
        "number": 5,
        "text": "All school records for L.D.W., including attendance records, report cards, disciplinary records, and communications with teachers or administrators.",
        "category": "Educational"
    })
    requests.append({
        "number": 6,
        "text": "All documents relating to any police report, CPS investigation, or protective order involving Andrew Pigors, L.D.W., or yourself from January 1, 2022 to present.",
        "category": "Law Enforcement"
    })
    requests.append({
        "number": 7,
        "text": "All financial records including bank statements, pay stubs, tax returns, and evidence of income from January 1, 2023 to present.",
        "category": "Financial"
    })
    requests.append({
        "number": 8,
        "text": "All documents, communications, or records relating to the Personal Protection Order (Case No. 2023-5907-PP), including the original petition and all supporting evidence.",
        "category": "PPO Records"
    })
    requests.append({
        "number": 9,
        "text": "All communications with Judge McNeill's chambers, judicial secretary Pamela Rusco, or any court staff outside of normal court proceedings.",
        "category": "Ex Parte Communications"
    })
    requests.append({
        "number": 10,
        "text": "All documents, notes, calendars, or records reflecting dates and times you permitted or denied Andrew Pigors parenting time with L.D.W.",
        "category": "Parenting Time"
    })

    # Add contradiction-specific requests
    for i, c in enumerate(contradictions[:5], 11):
        source = c.get("source_1", "the referenced document")
        requests.append({
            "number": i,
            "text": f"All documents referenced in or relating to {source}, including but not limited to drafts, notes, and communications about the preparation of said document.",
            "category": "Contradiction Source"
        })

    return requests


def generate_admission_requests(perjury, assertions):
    """Generate requests for admission targeting known false statements."""
    admissions = []

    for i, p in enumerate(perjury[:15], 1):
        stmt = (p.get("statement_text") or "")[:200]
        contra = (p.get("contradicting_evidence") or "")[:200]
        admissions.append({
            "number": i,
            "text": f"Admit that you stated: \"{stmt}\"",
            "follow_up": f"Admit that this statement is contradicted by: {contra}",
            "category": "Perjury Admission",
            "severity": p.get("severity_score", 5)
        })

    for i, a in enumerate(assertions[:10], len(admissions) + 1):
        stmt = (a.get("assertion_text") or "")[:200]
        admissions.append({
            "number": i,
            "text": f"Admit that the following assertion is false: \"{stmt}\"",
            "follow_up": f"Admit that you cannot produce evidence supporting this assertion.",
            "category": "False Assertion Admission",
            "severity": a.get("severity", 5)
        })

    # Standard admissions
    standard_admissions = [
        "Admit that Ronald T. Berry is not a licensed attorney in the State of Michigan.",
        "Admit that Ronald T. Berry has participated in the preparation of legal documents filed in this case.",
        "Admit that you have communicated with Judge McNeill's chambers outside of scheduled court proceedings.",
        "Admit that you have denied Andrew Pigors parenting time with L.D.W. on dates not authorized by court order.",
        "Admit that L.D.W. has expressed a desire to spend time with Andrew Pigors."
    ]

    for s in standard_admissions:
        admissions.append({
            "number": len(admissions) + 1,
            "text": s,
            "follow_up": "",
            "category": "Standard Admission",
            "severity": 6
        })

    return admissions


def format_discovery_document(interrogatories, production_requests, admissions):
    """Format into court-ready discovery document."""
    lines = []

    # Header
    lines.append("STATE OF MICHIGAN")
    lines.append("14TH JUDICIAL CIRCUIT COURT — FAMILY DIVISION")
    lines.append("MUSKEGON COUNTY")
    lines.append("")
    lines.append(f"{PLAINTIFF['name']},")
    lines.append("    Plaintiff,                    Case No. 2024-001507-DC")
    lines.append("                                  Hon. Jenny L. McNeill")
    lines.append("v.")
    lines.append("")
    lines.append(f"{DEFENDANT['name']},")
    lines.append("    Defendant.")
    lines.append("_" * 50)
    lines.append("")

    # Part 1: Interrogatories
    lines.append("=" * 60)
    lines.append("PLAINTIFF'S FIRST SET OF INTERROGATORIES")
    lines.append("Pursuant to MCR 2.309")
    lines.append("=" * 60)
    lines.append("")
    lines.append(f"TO: {DEFENDANT['name']}")
    lines.append("")
    lines.append("You are hereby requested to answer the following interrogatories")
    lines.append("under oath within twenty-eight (28) days of service pursuant to")
    lines.append("MCR 2.309(B).")
    lines.append("")

    for interrog in interrogatories:
        lines.append(f"\nINTERROGATORY NO. {interrog['number']}:")
        lines.append(f"[{interrog['category']}]")
        lines.append(interrog["text"])

    lines.append(f"\n\nTotal Interrogatories: {len(interrogatories)} of 35 maximum (MCR 2.309(A)(2))")

    # Part 2: Requests for Production
    lines.append("\n\n" + "=" * 60)
    lines.append("PLAINTIFF'S FIRST REQUEST FOR PRODUCTION OF DOCUMENTS")
    lines.append("Pursuant to MCR 2.310")
    lines.append("=" * 60)
    lines.append("")
    lines.append(f"TO: {DEFENDANT['name']}")
    lines.append("")
    lines.append("You are hereby requested to produce the following documents")
    lines.append("within twenty-eight (28) days of service pursuant to MCR 2.310(B).")
    lines.append("")

    for req in production_requests:
        lines.append(f"\nREQUEST NO. {req['number']}:")
        lines.append(f"[{req['category']}]")
        lines.append(req["text"])

    # Part 3: Requests for Admission
    lines.append("\n\n" + "=" * 60)
    lines.append("PLAINTIFF'S FIRST REQUEST FOR ADMISSIONS")
    lines.append("Pursuant to MCR 2.312")
    lines.append("=" * 60)
    lines.append("")
    lines.append(f"TO: {DEFENDANT['name']}")
    lines.append("")
    lines.append("You are hereby requested to admit or deny the following")
    lines.append("within twenty-eight (28) days of service pursuant to MCR 2.312(B).")
    lines.append("Failure to respond within 28 days results in automatic admission.")
    lines.append("")

    for adm in admissions:
        lines.append(f"\nADMISSION NO. {adm['number']}:")
        lines.append(f"[{adm['category']}]")
        lines.append(adm["text"])
        if adm.get("follow_up"):
            lines.append(f"\nADMISSION NO. {adm['number']}A:")
            lines.append(adm["follow_up"])

    # Signature
    lines.append("\n\n" + "_" * 50)
    lines.append("Respectfully submitted,")
    lines.append("")
    lines.append("____________________________")
    lines.append(f"{PLAINTIFF['name']}, Pro Se")
    lines.append(PLAINTIFF["address"])
    lines.append(PLAINTIFF["phone"])
    lines.append(PLAINTIFF["email"])
    lines.append(f"\nDate: _______________")

    return "\n".join(lines)


def main():
    print("=" * 60)
    print("DISCOVERY REQUEST GENERATOR v1.0")
    print("Auto-generating targeted discovery from evidence DB")
    print("=" * 60)

    conn = get_db_connection()

    # Extract data for targeted discovery
    print("\n📊 Loading evidence for targeted discovery...")
    contradictions = get_contradictions(conn)
    perjury = get_perjury_evidence(conn)
    assertions = get_adversary_assertions(conn)
    print(f"  Contradictions (sev≥7): {len(contradictions)}")
    print(f"  Perjury (sev≥8, admissible): {len(perjury)}")
    print(f"  False assertions (sev≥7): {len(assertions)}")

    conn.close()

    # Generate discovery
    print("\n📝 Generating interrogatories...")
    interrogatories = generate_interrogatories(contradictions, perjury, assertions)
    print(f"  Generated: {len(interrogatories)} of 35 maximum")

    print("\n📝 Generating production requests...")
    production = generate_production_requests(contradictions, perjury)
    print(f"  Generated: {len(production)} requests")

    print("\n📝 Generating admission requests...")
    admissions = generate_admission_requests(perjury, assertions)
    print(f"  Generated: {len(admissions)} admissions")

    # Format document
    document = format_discovery_document(interrogatories, production, admissions)

    # Save
    md_path = REPORTS_DIR / "DISCOVERY_REQUESTS.md"
    with open(md_path, "w", encoding="utf-8") as f:
        f.write(document)

    # Save JSON
    output = {
        "generated": datetime.now().isoformat(),
        "interrogatories": {"count": len(interrogatories), "max": 35, "items": interrogatories},
        "production_requests": {"count": len(production), "items": production},
        "admissions": {"count": len(admissions), "items": admissions},
        "data_sources": {
            "contradictions": len(contradictions),
            "perjury": len(perjury),
            "assertions": len(assertions)
        }
    }

    json_path = REPORTS_DIR / "discovery_requests.json"
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(output, f, indent=2, default=str)

    print(f"\n{'='*60}")
    print(f"DISCOVERY REQUEST GENERATOR — COMPLETE")
    print(f"{'='*60}")
    print(f"Interrogatories:      {len(interrogatories)}/35")
    print(f"Production requests:  {len(production)}")
    print(f"Admission requests:   {len(admissions)}")
    print(f"\n📄 Document: {md_path}")
    print(f"📊 JSON: {json_path}")

    return output


if __name__ == "__main__":
    main()
