#!/usr/bin/env python3
"""
Tool #227: Service Requirements Matrix
Generate a complete service requirements matrix for all filings.
Determines WHO, HOW, WHAT, WHEN, and MCR citation for each filing.
Outputs: SERVICE_REQUIREMENTS.md + service_requirements.json
"""
import sys
import os
import json
import sqlite3
from datetime import datetime
from pathlib import Path

sys.stdout = open(sys.stdout.fileno(), mode='w', encoding='utf-8', errors='replace')

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = r"C:\Users\andre\LitigationOS\litigation_context.db"
REPORT_DIR = Path(r"C:\Users\andre\LitigationOS\00_SYSTEM\reports")
REPORT_DIR.mkdir(parents=True, exist_ok=True)

# Verified party identity — NEVER fabricate
PARTIES = {
    "plaintiff": {
        "name": "Andrew James Pigors",
        "address": "1977 Whitehall Road, Lot 17, North Muskegon, MI 49445",
        "phone": "(231) 903-5690",
        "email": "andrewjpigors@gmail.com",
        "role": "Plaintiff / Petitioner / Appellant (Pro Se)"
    },
    "defendant": {
        "name": "Emily A. Watson",
        "address": "2160 Garland Drive, Norton Shores, MI 49441",
        "role": "Defendant / Respondent",
        "attorney_status": "UNREPRESENTED (Jennifer Barnes P55406 withdrew)"
    },
    "judge": {
        "name": "Hon. Jenny L. McNeill",
        "court": "14th Circuit Court, Family Division"
    },
    "foc": {
        "name": "Pamela Rusco",
        "address": "990 Terrace St, Muskegon, MI 49442",
        "role": "Friend of the Court"
    }
}

# Service requirements definitions — per filing type
FILING_MATRIX = [
    {
        "filing_id": "F1",
        "filing_type": "Motion to Restore Parenting Time",
        "court": "14th Circuit Court — Family Division",
        "case_number": "2024-001507-DC",
        "lane": "A",
        "serve_to": [
            {
                "party": "Emily A. Watson",
                "address": "2160 Garland Drive, Norton Shores, MI 49441",
                "method": "First-class mail OR personal service",
                "mcr": "MCR 2.107(C)(1) — mail service on unrepresented party",
                "note": "Barnes withdrew — Watson is unrepresented. Cannot e-serve."
            },
            {
                "party": "Friend of the Court (Pamela Rusco)",
                "address": "990 Terrace St, Muskegon, MI 49442",
                "method": "First-class mail or courthouse delivery",
                "mcr": "MCR 3.203(A) — FOC must receive copies of all motions",
                "note": "Required for all domestic relations filings"
            }
        ],
        "documents": ["Motion", "Brief in Support", "Proposed Order", "Certificate of Service", "Exhibits"],
        "timing": "At least 9 days before hearing (MCR 2.119(C)(1))",
        "timing_mcr": "MCR 2.119(C)(1)",
        "filing_method": "MiFILE e-filing or counter filing"
    },
    {
        "filing_id": "F2",
        "filing_type": "Motion to Terminate PPO / Motion to Rescind",
        "court": "14th Circuit Court",
        "case_number": "2023-5907-PP",
        "lane": "D",
        "serve_to": [
            {
                "party": "Emily A. Watson",
                "address": "2160 Garland Drive, Norton Shores, MI 49441",
                "method": "First-class mail OR personal service",
                "mcr": "MCR 2.107(C)(1); MCL 600.2950(14)",
                "note": "Unrepresented party — mail or personal only"
            },
            {
                "party": "14th Circuit Court Clerk",
                "address": "990 Terrace St, Muskegon, MI 49442",
                "method": "MiFILE e-filing",
                "mcr": "MCR 3.706(B)",
                "note": "Original filed with court via MiFILE"
            }
        ],
        "documents": ["Motion to Terminate PPO", "Brief in Support", "Affidavit", "Proposed Order", "Certificate of Service", "Exhibits"],
        "timing": "At least 9 days before hearing (MCR 2.119(C)(1))",
        "timing_mcr": "MCR 2.119(C)(1); MCR 3.706(B)",
        "filing_method": "MiFILE e-filing"
    },
    {
        "filing_id": "F3",
        "filing_type": "Emergency Motion (Ex Parte)",
        "court": "14th Circuit Court — Family Division",
        "case_number": "2024-001507-DC",
        "lane": "A",
        "serve_to": [
            {
                "party": "Emily A. Watson",
                "address": "2160 Garland Drive, Norton Shores, MI 49441",
                "method": "Personal service REQUIRED for ex parte",
                "mcr": "MCR 3.207(B) — ex parte orders require immediate personal service",
                "note": "Must be served immediately after entry of order"
            },
            {
                "party": "Friend of the Court",
                "address": "990 Terrace St, Muskegon, MI 49442",
                "method": "First-class mail or hand delivery",
                "mcr": "MCR 3.203(A)",
                "note": "FOC receives copy of all emergency filings"
            }
        ],
        "documents": ["Emergency Motion", "Brief in Support", "Affidavit of Emergency", "Proposed Ex Parte Order", "Certificate of Service"],
        "timing": "Immediate filing; service within 24 hours of order entry",
        "timing_mcr": "MCR 3.207(B)",
        "filing_method": "MiFILE e-filing (expedited) or counter"
    },
    {
        "filing_id": "F4",
        "filing_type": "JTC Complaint (Judicial Tenure Commission)",
        "court": "Judicial Tenure Commission",
        "case_number": "JTC-001",
        "lane": "E",
        "serve_to": [
            {
                "party": "Judicial Tenure Commission",
                "address": "3034 W. Grand Blvd, Suite 8-350, Detroit, MI 48202",
                "method": "MAIL ONLY — NOT e-file",
                "mcr": "MCR 9.234; Const 1963, art 6, §30",
                "note": "JTC does NOT accept e-filings. Send via USPS certified mail with return receipt."
            }
        ],
        "documents": ["Formal Complaint", "Supporting Evidence Packet", "Chronological Index", "Exhibit List"],
        "timing": "No statutory deadline — file when evidence is complete",
        "timing_mcr": "MCR 9.234",
        "filing_method": "USPS Certified Mail (NOT e-file, NOT hand delivery required)"
    },
    {
        "filing_id": "F5",
        "filing_type": "COA Application for Leave / Appeal",
        "court": "Michigan Court of Appeals",
        "case_number": "COA-366810",
        "lane": "F",
        "serve_to": [
            {
                "party": "Emily A. Watson",
                "address": "2160 Garland Drive, Norton Shores, MI 49441",
                "method": "First-class mail",
                "mcr": "MCR 7.205(D); MCR 7.208(A)",
                "note": "Unrepresented — serve at last known address"
            },
            {
                "party": "14th Circuit Court Clerk",
                "address": "990 Terrace St, Muskegon, MI 49442",
                "method": "Copy to trial court",
                "mcr": "MCR 7.205(D)(4)",
                "note": "File copy with trial court clerk"
            },
            {
                "party": "Michigan Court of Appeals",
                "address": "MiFILE",
                "method": "MiFILE e-service",
                "mcr": "MCR 7.202(2); Admin Order 2019-8",
                "note": "COA filings via MiFILE mandatory"
            }
        ],
        "documents": ["Application for Leave to Appeal", "Appellant Brief", "Lower Court Record", "Proposed Index", "Certificate of Service"],
        "timing": "21 days from entry of order being appealed (MCR 7.205(F)(3))",
        "timing_mcr": "MCR 7.205(F)(3)",
        "filing_method": "MiFILE e-filing"
    },
    {
        "filing_id": "F6",
        "filing_type": "Federal §1983 Complaint (WDMI)",
        "court": "US District Court — Western District of Michigan",
        "case_number": "[To be assigned on filing]",
        "lane": "E",
        "serve_to": [
            {
                "party": "Hon. Jenny L. McNeill (individual capacity)",
                "address": "Via WDMI CM/ECF + Certified Mail to 990 Terrace St, Muskegon, MI 49442",
                "method": "CM/ECF e-filing + USPS Certified Mail",
                "mcr": "FRCP 4(e); 42 USC §1983",
                "note": "Federal service requires summons + complaint via certified mail"
            },
            {
                "party": "Michigan Attorney General (official capacity)",
                "address": "P.O. Box 30212, Lansing, MI 48909",
                "method": "USPS Certified Mail",
                "mcr": "FRCP 4(j)(2) — service on state officer",
                "note": "Required when suing state judicial officer in official capacity"
            }
        ],
        "documents": ["Civil Complaint", "Civil Cover Sheet", "Summons", "Certificate of Service", "IFP Application (if applicable)"],
        "timing": "90 days for service after filing (FRCP 4(m))",
        "timing_mcr": "FRCP 4(m)",
        "filing_method": "WDMI CM/ECF e-filing"
    },
    {
        "filing_id": "F7",
        "filing_type": "Motion for Sanctions / Contempt",
        "court": "14th Circuit Court — Family Division",
        "case_number": "2024-001507-DC",
        "lane": "A",
        "serve_to": [
            {
                "party": "Emily A. Watson",
                "address": "2160 Garland Drive, Norton Shores, MI 49441",
                "method": "Personal service REQUIRED for contempt",
                "mcr": "MCR 3.606(A) — personal service required for show cause/contempt",
                "note": "Contempt requires personal service — mail insufficient"
            },
            {
                "party": "Friend of the Court",
                "address": "990 Terrace St, Muskegon, MI 49442",
                "method": "First-class mail",
                "mcr": "MCR 3.203(A)",
                "note": "FOC copy required"
            }
        ],
        "documents": ["Motion for Contempt", "Order to Show Cause", "Affidavit", "Proposed Order", "Certificate of Service"],
        "timing": "14 days before hearing for show cause (MCR 3.606(A))",
        "timing_mcr": "MCR 3.606(A)",
        "filing_method": "MiFILE e-filing"
    },
    {
        "filing_id": "F8",
        "filing_type": "Motion to Disqualify Judge",
        "court": "14th Circuit Court",
        "case_number": "2024-001507-DC",
        "lane": "E",
        "serve_to": [
            {
                "party": "Emily A. Watson",
                "address": "2160 Garland Drive, Norton Shores, MI 49441",
                "method": "First-class mail",
                "mcr": "MCR 2.107(C)(1)",
                "note": "Unrepresented party service"
            },
            {
                "party": "Chief Judge (14th Circuit)",
                "address": "990 Terrace St, Muskegon, MI 49442",
                "method": "Hand delivery or mail to chambers",
                "mcr": "MCR 2.003(D)(3)(a) — disqualification served on chief judge",
                "note": "Motion goes to chief judge, not the judge being disqualified"
            },
            {
                "party": "Friend of the Court",
                "address": "990 Terrace St, Muskegon, MI 49442",
                "method": "First-class mail",
                "mcr": "MCR 3.203(A)",
                "note": "FOC copy"
            }
        ],
        "documents": ["Motion for Disqualification", "Affidavit of Bias/Prejudice", "Brief in Support", "Proposed Order", "Certificate of Service"],
        "timing": "As soon as grounds become known (MCR 2.003(D)(1))",
        "timing_mcr": "MCR 2.003(D)(1)",
        "filing_method": "MiFILE e-filing"
    },
    {
        "filing_id": "F9",
        "filing_type": "FOC Objection",
        "court": "14th Circuit Court — Family Division",
        "case_number": "2024-001507-DC",
        "lane": "A",
        "serve_to": [
            {
                "party": "Emily A. Watson",
                "address": "2160 Garland Drive, Norton Shores, MI 49441",
                "method": "First-class mail",
                "mcr": "MCR 2.107(C)(1)",
                "note": "Unrepresented party"
            },
            {
                "party": "Friend of the Court",
                "address": "990 Terrace St, Muskegon, MI 49442",
                "method": "First-class mail or hand delivery",
                "mcr": "MCR 3.218(D)",
                "note": "FOC must receive objection"
            }
        ],
        "documents": ["Objection to FOC Recommendation", "Brief in Support", "Certificate of Service"],
        "timing": "21 days from date of FOC recommendation (MCR 3.218(D))",
        "timing_mcr": "MCR 3.218(D)",
        "filing_method": "MiFILE e-filing"
    },
    {
        "filing_id": "F10",
        "filing_type": "Housing Complaint (Shady Oaks)",
        "court": "14th Circuit Court — Civil Division",
        "case_number": "2025-002760-CZ",
        "lane": "B",
        "serve_to": [
            {
                "party": "Shady Oaks MHC / Park Management",
                "address": "[Verify registered agent address via LARA]",
                "method": "Personal service on registered agent OR certified mail",
                "mcr": "MCR 2.105(D) — service on corporation",
                "note": "Must serve registered agent or officer per MCR 2.105(D)"
            },
            {
                "party": "Any named individual defendants",
                "address": "[Verify addresses]",
                "method": "Personal service or first-class mail (after initial service)",
                "mcr": "MCR 2.105(A) — personal service on individuals",
                "note": "First service must be personal; subsequent by mail"
            }
        ],
        "documents": ["Summons", "Complaint", "Civil Cover Sheet", "Certificate of Service"],
        "timing": "91 days to serve after filing (MCR 2.102(D))",
        "timing_mcr": "MCR 2.102(D)",
        "filing_method": "MiFILE e-filing"
    }
]


def get_db():
    conn = sqlite3.connect(DB_PATH, timeout=120)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA busy_timeout=60000")
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA cache_size=-32000")
    conn.execute("PRAGMA temp_store=MEMORY")
    conn.execute("PRAGMA synchronous=NORMAL")
    return conn


def table_exists(conn, name):
    row = conn.execute(
        "SELECT COUNT(*) FROM sqlite_master WHERE type='table' AND name=?", (name,)
    ).fetchone()
    return row[0] > 0


def get_columns(conn, table):
    rows = conn.execute(f"PRAGMA table_info({table})").fetchall()
    return [r[1] for r in rows]


def enrich_from_db(conn):
    """Pull service_tracking and filing data from DB to cross-reference."""
    enrichment = {"service_tracking": [], "filing_readiness": [], "filing_sequence": []}

    if table_exists(conn, "service_tracking"):
        cols = get_columns(conn, "service_tracking")
        rows = conn.execute("SELECT * FROM service_tracking ORDER BY filing_name").fetchall()
        enrichment["service_tracking"] = [dict(r) for r in rows]

    if table_exists(conn, "filing_readiness"):
        cols = get_columns(conn, "filing_readiness")
        rows = conn.execute(
            "SELECT vehicle_name, total_score, status FROM filing_readiness ORDER BY total_score DESC"
        ).fetchall()
        enrichment["filing_readiness"] = [dict(r) for r in rows]

    if table_exists(conn, "filing_sequence"):
        cols = get_columns(conn, "filing_sequence")
        rows = conn.execute(
            "SELECT tier, priority, filing_title, target_court, status FROM filing_sequence ORDER BY tier, priority"
        ).fetchall()
        enrichment["filing_sequence"] = [dict(r) for r in rows]

    return enrichment


def generate_md(matrix, enrichment, generated_at):
    lines = [
        "# SERVICE REQUIREMENTS MATRIX",
        f"**Generated:** {generated_at}",
        f"**Database:** litigation_context.db",
        "",
        "## Key Service Rules",
        "",
        "| Rule | Citation |",
        "|---|---|",
        "| Emily Watson is UNREPRESENTED (Barnes withdrew) — serve at home address | MCR 2.107(C)(1) |",
        "| JTC Complaint: MAIL ONLY to Suite 8-350 Detroit | MCR 9.234 |",
        "| COA filings: MiFILE e-service mandatory | MCR 7.202(2); AO 2019-8 |",
        "| Federal (WDMI): CM/ECF + certified mail | FRCP 4(e) |",
        "| Contempt requires PERSONAL service | MCR 3.606(A) |",
        "| Ex parte orders require IMMEDIATE personal service | MCR 3.207(B) |",
        "",
        "---",
        ""
    ]

    for filing in matrix:
        lines.append(f"## {filing['filing_id']}: {filing['filing_type']}")
        lines.append(f"**Court:** {filing['court']}  ")
        lines.append(f"**Case:** {filing['case_number']}  ")
        lines.append(f"**Lane:** {filing['lane']}  ")
        lines.append(f"**Filing Method:** {filing['filing_method']}  ")
        lines.append(f"**Timing:** {filing['timing']}  ")
        lines.append("")

        lines.append("### WHO / HOW to Serve")
        lines.append("")
        lines.append("| Party | Method | MCR Citation | Notes |")
        lines.append("|---|---|---|---|")
        for s in filing["serve_to"]:
            lines.append(f"| {s['party']} | {s['method']} | {s['mcr']} | {s.get('note', '')} |")
        lines.append("")

        lines.append("### WHAT to Serve")
        lines.append("")
        for doc in filing["documents"]:
            lines.append(f"- {doc}")
        lines.append("")

    # DB cross-reference
    if enrichment["service_tracking"]:
        lines.extend([
            "---",
            "## Existing Service Tracking Records (from DB)",
            "",
            "| Filing | Served To | Method | Date | Compliant |",
            "|---|---|---|---|---|"
        ])
        for rec in enrichment["service_tracking"]:
            lines.append(
                f"| {rec.get('filing_name', 'N/A')} | {rec.get('served_to', 'N/A')} | "
                f"{rec.get('service_method', 'N/A')} | {rec.get('service_date', 'N/A')} | "
                f"{'Yes' if rec.get('compliant') else 'No'} |"
            )
        lines.append("")

    if enrichment["filing_sequence"]:
        lines.extend([
            "---",
            "## Filing Sequence (from DB)",
            "",
            "| Tier | Priority | Title | Court | Status |",
            "|---|---|---|---|---|"
        ])
        for rec in enrichment["filing_sequence"][:20]:
            lines.append(
                f"| {rec.get('tier', '')} | {rec.get('priority', '')} | "
                f"{rec.get('filing_title', 'N/A')} | {rec.get('target_court', 'N/A')} | "
                f"{rec.get('status', 'N/A')} |"
            )
        lines.append("")

    return "\n".join(lines)


def main():
    print("=" * 60)
    print("TOOL #227: SERVICE REQUIREMENTS MATRIX")
    print("=" * 60)
    generated_at = datetime.now().isoformat()

    conn = get_db()
    print(f"[OK] Connected to DB: {DB_PATH}")

    # Enrich from DB
    print("[1/3] Querying DB for existing service records...")
    enrichment = enrich_from_db(conn)
    print(f"  Service tracking records: {len(enrichment['service_tracking'])}")
    print(f"  Filing readiness entries: {len(enrichment['filing_readiness'])}")
    print(f"  Filing sequence entries:  {len(enrichment['filing_sequence'])}")

    conn.close()

    # Build output
    print("[2/3] Building service matrix for 10 filing types...")
    output = {
        "tool": "service_requirements_matrix",
        "tool_number": 227,
        "generated_at": generated_at,
        "database": DB_PATH,
        "parties": PARTIES,
        "total_filings": len(FILING_MATRIX),
        "filings": FILING_MATRIX,
        "db_enrichment": {
            "service_tracking_count": len(enrichment["service_tracking"]),
            "filing_readiness_count": len(enrichment["filing_readiness"]),
            "filing_sequence_count": len(enrichment["filing_sequence"]),
            "service_tracking": enrichment["service_tracking"],
        }
    }

    # Write JSON
    json_path = REPORT_DIR / "service_requirements.json"
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(output, f, indent=2, default=str)
    print(f"\n[OK] JSON report: {json_path}")

    # Write MD
    print("[3/3] Generating markdown report...")
    md = generate_md(FILING_MATRIX, enrichment, generated_at)
    md_path = REPORT_DIR / "SERVICE_REQUIREMENTS.md"
    with open(md_path, "w", encoding="utf-8") as f:
        f.write(md)
    print(f"[OK] MD report:   {md_path}")

    # Summary
    print("\n" + "=" * 60)
    print("SERVICE REQUIREMENTS SUMMARY:")
    print(f"  Total filing types mapped:   {len(FILING_MATRIX)}")
    total_serve_entries = sum(len(f["serve_to"]) for f in FILING_MATRIX)
    print(f"  Total service requirements:  {total_serve_entries}")
    print(f"  DB service records found:    {len(enrichment['service_tracking'])}")
    print("=" * 60)

    # Special warnings
    print("\n⚠  SPECIAL SERVICE WARNINGS:")
    print("  • JTC Complaint (F4): MAIL ONLY to Suite 8-350 Detroit — NOT e-file")
    print("  • Contempt (F7): PERSONAL SERVICE REQUIRED — mail insufficient")
    print("  • Ex Parte (F3): Serve IMMEDIATELY after order entry")
    print("  • Federal §1983 (F6): CM/ECF + Certified Mail to each defendant")
    print("  • Emily Watson: UNREPRESENTED — serve at 2160 Garland Dr, Norton Shores")


if __name__ == "__main__":
    main()
