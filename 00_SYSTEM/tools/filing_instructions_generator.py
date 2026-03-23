#!/usr/bin/env python3
"""Tool #275: Filing Instructions Generator
Generates step-by-step filing instructions for each of the 10 filing packages.
Tells Andrew exactly what to do: package contents, filing method, service, fees, deadlines.
"""
import sys
import os
import sqlite3
from datetime import datetime

sys.stdout = open(sys.stdout.fileno(), mode='w', encoding='utf-8', errors='replace')

DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', 'litigation_context.db')
REPORT_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'reports')
OUTPUT_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', 'GENERATED_FILINGS')

def s(v):
    return (v or "").lower()

def safe_query(conn, sql, params=()):
    try:
        return conn.execute(sql, params).fetchall()
    except:
        return []

# ── Court locations ──────────────────────────────────────────────────────────
COURTS = {
    "14th_circuit": {
        "name": "14th Judicial Circuit Court, Muskegon County",
        "address": "Michael E. Kobza Hall of Justice\n  990 Terrace St\n  Muskegon, MI 49442",
        "hours": "8:00 AM - 5:00 PM, Monday-Friday",
        "efiling": "MiFILE (https://mifile.courts.michigan.gov)",
        "phone": "(231) 724-6241",
    },
    "wdmi": {
        "name": "U.S. District Court, Western District of Michigan",
        "address": "Gerald R. Ford Federal Building\n  110 Michigan St NW\n  Grand Rapids, MI 49503",
        "hours": "8:30 AM - 4:30 PM, Monday-Friday",
        "efiling": "CM/ECF (https://ecf.miwd.uscourts.gov)",
        "phone": "(616) 456-2381",
    },
    "coa": {
        "name": "Michigan Court of Appeals",
        "address": "925 W. Ottawa St\n  Lansing, MI 48915",
        "hours": "8:00 AM - 5:00 PM, Monday-Friday",
        "efiling": "MiFILE (https://mifile.courts.michigan.gov)",
        "phone": "(517) 373-0786",
    },
    "msc": {
        "name": "Michigan Supreme Court",
        "address": "925 W. Ottawa St\n  Lansing, MI 48915",
        "hours": "8:00 AM - 5:00 PM, Monday-Friday",
        "efiling": "MiFILE (https://mifile.courts.michigan.gov)",
        "phone": "(517) 373-0120",
    },
    "jtc": {
        "name": "Judicial Tenure Commission",
        "address": "3034 W. Grand Blvd, Suite 8-450\n  Detroit, MI 48202",
        "hours": "8:00 AM - 5:00 PM, Monday-Friday",
        "efiling": "Mail or hand delivery only",
        "phone": "(313) 875-5110",
    },
    "prosecutor": {
        "name": "Muskegon County Prosecutor's Office",
        "address": "990 Terrace Street, Suite 500\n  Muskegon, MI 49442",
        "hours": "8:00 AM - 5:00 PM, Monday-Friday",
        "efiling": "Mail or hand delivery only",
        "phone": "(231) 724-6435",
    },
}

# ── Filing definitions ───────────────────────────────────────────────────────
FILINGS = [
    {
        "id": "F1",
        "title": "MOTION FOR EMERGENCY RELIEF AND REINSTATEMENT OF PARENTING TIME",
        "court_key": "14th_circuit",
        "case_number": "2024-001507-DC",
        "filing_fee": "$20",
        "contents": [
            "[1] Cover Page / Caption — F1_cover_page.txt",
            "[2] Motion for Emergency Relief — F1_motion.txt",
            "[3] Affidavit in Support — F1_affidavit.txt (MUST BE NOTARIZED)",
            "[4] SCAO Form: MC 303 (Fee Waiver Request, if applicable)",
            "[5] Exhibit Binder — F1_exhibits/ (attach all supporting evidence)",
            "[6] Proposed Order — F1_proposed_order.txt",
            "[7] Certificate of Service — F1_cert_service.txt",
        ],
        "service_parties": [
            ("Emily A. Watson", "2160 Garland Drive, Norton Shores, MI 49441", "First-class mail and/or personal service"),
            ("FOC — Pamela Rusco", "990 Terrace St, Muskegon, MI 49442", "First-class mail"),
        ],
        "deadline": "File IMMEDIATELY — emergency relief requires prompt filing. Court may hear ex parte if immediate danger to child.",
        "response_time": "Emergency motions may be heard same day or within 1-3 days. If denied ex parte, hearing set within 14 days.",
        "scao_forms": ["MC 303 (Fee Waiver)", "FOC 115 (Motion/Stipulation for Parenting Time)"],
        "special_notes": "Emphasize emergency nature at filing window. Request expedited hearing. Bring proposed order for judge's signature.",
    },
    {
        "id": "F2",
        "title": "MOTION TO MODIFY/TERMINATE PERSONAL PROTECTION ORDER",
        "court_key": "14th_circuit",
        "case_number": "2023-5907-PP",
        "filing_fee": "$0 (no fee for PPO modification)",
        "contents": [
            "[1] Cover Page / Caption — F2_cover_page.txt",
            "[2] Motion to Modify/Terminate PPO — F2_motion.txt",
            "[3] Affidavit in Support — F2_affidavit.txt (MUST BE NOTARIZED)",
            "[4] SCAO Form: CC 381 (Motion to Modify/Terminate PPO)",
            "[5] Exhibit Binder — F2_exhibits/ (evidence PPO is unwarranted)",
            "[6] Proposed Order — F2_proposed_order.txt",
            "[7] Certificate of Service — F2_cert_service.txt",
        ],
        "service_parties": [
            ("Emily A. Watson", "2160 Garland Drive, Norton Shores, MI 49441", "Personal service required per MCR 3.707"),
        ],
        "deadline": "No statutory deadline, but file as soon as grounds are established. PPO restricts parenting rights until modified.",
        "response_time": "Hearing must be set within 14 days of filing per MCL 600.2950(12).",
        "scao_forms": ["CC 381 (Motion to Modify/Terminate PPO)", "CC 382 (Order on Motion)"],
        "special_notes": "Court MUST hold a hearing. You have right to present evidence. Cannot be denied without hearing.",
    },
    {
        "id": "F3",
        "title": "MOTION TO DISQUALIFY JUDGE PURSUANT TO MCR 2.003",
        "court_key": "14th_circuit",
        "case_number": "2024-001507-DC",
        "filing_fee": "$20",
        "contents": [
            "[1] Cover Page / Caption — F3_cover_page.txt",
            "[2] Motion to Disqualify — F3_motion.txt",
            "[3] Affidavit of Bias and Prejudice — F3_affidavit.txt (MUST BE NOTARIZED)",
            "[4] Brief in Support — F3_brief.txt",
            "[5] Exhibit Binder — F3_exhibits/ (evidence of bias/prejudice)",
            "[6] Proposed Order — F3_proposed_order.txt",
            "[7] Certificate of Service — F3_cert_service.txt",
        ],
        "service_parties": [
            ("Emily A. Watson", "2160 Garland Drive, Norton Shores, MI 49441", "First-class mail"),
            ("Hon. Jenny L. McNeill (chambers copy)", "990 Terrace St, Muskegon, MI 49442", "Deliver to judicial assistant"),
        ],
        "deadline": "Must be filed within 14 days of discovering grounds for disqualification per MCR 2.003(D)(1).",
        "response_time": "Opposing party has 14 days to respond. Judge must decide within 14 days of response (or opposition deadline if no response).",
        "scao_forms": [],
        "special_notes": "Judge may decide without a hearing. If denied, appeal is by application for leave to COA. Preserve all grounds on the record.",
    },
    {
        "id": "F4",
        "title": "COMPLAINT UNDER 42 U.S.C. § 1983",
        "court_key": "wdmi",
        "case_number": "[TO BE ASSIGNED]",
        "filing_fee": "$405 (or IFP waiver — file Application to Proceed In Forma Pauperis)",
        "contents": [
            "[1] Cover Page / Caption — F4_cover_page.txt",
            "[2] Complaint — F4_complaint.txt",
            "[3] Application to Proceed IFP — F4_ifp_application.txt",
            "[4] Civil Cover Sheet — JS-44 (federal form)",
            "[5] Summons for Each Defendant — F4_summons.txt",
            "[6] Exhibit Binder — F4_exhibits/ (constitutional violation evidence)",
            "[7] Certificate of Service — F4_cert_service.txt",
        ],
        "service_parties": [
            ("Hon. Jenny L. McNeill (individual capacity)", "c/o 14th Circuit Court, 990 Terrace St, Muskegon, MI 49442", "U.S. Marshal service (federal court arranges for IFP plaintiffs)"),
            ("Emily A. Watson", "2160 Garland Drive, Norton Shores, MI 49441", "U.S. Marshal service or certified mail"),
            ("County of Muskegon", "c/o County Clerk, 990 Terrace St, Muskegon, MI 49442", "U.S. Marshal service"),
        ],
        "deadline": "Statute of limitations: 3 years from date of constitutional violation (Michigan borrowing statute). File promptly.",
        "response_time": "Defendants have 60 days to respond (government defendants). Court screens IFP complaints under 28 USC §1915.",
        "scao_forms": ["JS-44 (Civil Cover Sheet — federal)", "AO 240 (Application to Proceed IFP)"],
        "special_notes": "Federal court requires CM/ECF electronic filing for attorneys, but pro se litigants may file on paper. IFP application must include financial affidavit. U.S. Marshal handles service for IFP plaintiffs.",
    },
    {
        "id": "F5",
        "title": "APPLICATION FOR LEAVE TO FILE ORIGINAL ACTION / COMPLAINT FOR SUPERINTENDING CONTROL",
        "court_key": "msc",
        "case_number": "[TO BE ASSIGNED]",
        "filing_fee": "$375",
        "contents": [
            "[1] Cover Page / Caption — F5_cover_page.txt",
            "[2] Application for Leave — F5_application.txt",
            "[3] Complaint for Superintending Control — F5_complaint.txt",
            "[4] Brief in Support — F5_brief.txt",
            "[5] Appendix (lower court orders, transcripts) — F5_appendix/",
            "[6] Proposed Order — F5_proposed_order.txt",
            "[7] Certificate of Service — F5_cert_service.txt",
            "[8] IFP Application (if needed) — F5_ifp.txt",
        ],
        "service_parties": [
            ("Hon. Jenny L. McNeill", "c/o 14th Circuit Court, 990 Terrace St, Muskegon, MI 49442", "First-class mail"),
            ("Emily A. Watson", "2160 Garland Drive, Norton Shores, MI 49441", "First-class mail"),
        ],
        "deadline": "No strict deadline, but filing delay weakens claims. File as soon as lower court remedy is exhausted.",
        "response_time": "MSC sets briefing schedule. Typically 28 days for response, 21 days for reply.",
        "scao_forms": [],
        "special_notes": "MSC grants original actions rarely. Must demonstrate extraordinary circumstances and no adequate remedy. Include lower court record as appendix. 50-page brief limit per MCR 7.305.",
    },
    {
        "id": "F6",
        "title": "VERIFIED COMPLAINT — JUDICIAL TENURE COMMISSION",
        "court_key": "jtc",
        "case_number": None,
        "filing_fee": "$0 (no filing fee)",
        "contents": [
            "[1] Cover Page / Caption — F6_cover_page.txt",
            "[2] Verified Complaint — F6_complaint.txt (MUST BE NOTARIZED)",
            "[3] Supporting Documentation — F6_exhibits/",
            "[4] Timeline of Judicial Misconduct — F6_timeline.txt",
            "[5] Copies of Relevant Court Orders — F6_orders/",
        ],
        "service_parties": [],
        "deadline": "No statutory deadline. JTC investigates at its discretion. File promptly while evidence is fresh.",
        "response_time": "JTC does not disclose investigation timelines. May take months. You may not receive updates.",
        "scao_forms": [],
        "special_notes": "JTC complaints are CONFIDENTIAL until formal charges are filed. Do not publicize the complaint. Include only verified, factual allegations. JTC investigates — they are not an advocacy body. Mail original + one copy. Keep a copy for your records.",
    },
    {
        "id": "F7",
        "title": "APPLICATION FOR LEAVE TO APPEAL",
        "court_key": "coa",
        "case_number": "[TO BE ASSIGNED]",
        "filing_fee": "$375",
        "contents": [
            "[1] Cover Page / Caption — F7_cover_page.txt",
            "[2] Application for Leave to Appeal — F7_application.txt",
            "[3] Brief in Support per MCR 7.205(D) — F7_brief.txt",
            "[4] Appendix (order being appealed, relevant transcripts) — F7_appendix/",
            "[5] Proof of Service — F7_cert_service.txt",
            "[6] IFP Application (if needed) — F7_ifp.txt",
        ],
        "service_parties": [
            ("Emily A. Watson", "2160 Garland Drive, Norton Shores, MI 49441", "First-class mail"),
            ("14th Circuit Court Clerk", "990 Terrace St, Muskegon, MI 49442", "First-class mail (copy of application)"),
        ],
        "deadline": "21 days from entry of the order being appealed per MCR 7.205(A). STRICT DEADLINE — NO EXTENSIONS.",
        "response_time": "Appellee has 21 days to respond. COA decides on application without oral argument typically.",
        "scao_forms": [],
        "special_notes": "This is the STRICTEST deadline. Missing the 21-day window forfeits appellate rights. File via MiFILE if possible. Include ALL relevant lower court orders in appendix. 50-page brief limit per MCR 7.212.",
    },
    {
        "id": "F8",
        "title": "MOTION AND AFFIDAVIT FOR FINDING OF CONTEMPT",
        "court_key": "14th_circuit",
        "case_number": "2024-001507-DC",
        "filing_fee": "$20",
        "contents": [
            "[1] Cover Page / Caption — F8_cover_page.txt",
            "[2] Motion for Contempt — F8_motion.txt",
            "[3] Affidavit in Support — F8_affidavit.txt (MUST BE NOTARIZED)",
            "[4] SCAO Form: FOC 102 (Order to Show Cause for Contempt)",
            "[5] Exhibit Binder — F8_exhibits/ (proof of violations)",
            "[6] Proposed Order to Show Cause — F8_proposed_order.txt",
            "[7] Certificate of Service — F8_cert_service.txt",
        ],
        "service_parties": [
            ("Emily A. Watson", "2160 Garland Drive, Norton Shores, MI 49441", "Personal service required for contempt"),
            ("FOC — Pamela Rusco", "990 Terrace St, Muskegon, MI 49442", "First-class mail"),
        ],
        "deadline": "No strict deadline, but file promptly after each violation. Pattern of violations strengthens motion.",
        "response_time": "Court sets show cause hearing. Respondent must appear. Typically 14-28 days from order to show cause.",
        "scao_forms": ["FOC 102 (Order to Show Cause)", "FOC 104 (Affidavit of Contempt)"],
        "special_notes": "Contempt requires: (1) valid court order, (2) knowledge of the order, (3) ability to comply, (4) willful failure to comply. Document EACH element for EACH violation.",
    },
    {
        "id": "F9",
        "title": "VERIFIED COMPLAINT — NEGLIGENCE AND BREACH OF HABITABILITY WARRANTY",
        "court_key": "14th_circuit",
        "case_number": "2025-002760-CZ",
        "filing_fee": "$175 (civil complaint filing fee)",
        "contents": [
            "[1] Cover Page / Caption — F9_cover_page.txt",
            "[2] Verified Complaint — F9_complaint.txt (MUST BE NOTARIZED)",
            "[3] SCAO Form: MC 01 (Summons)",
            "[4] Civil Case Cover Sheet",
            "[5] Exhibit Binder — F9_exhibits/ (photos, inspection reports, communications)",
            "[6] Certificate of Service — F9_cert_service.txt",
        ],
        "service_parties": [
            ("Shady Oaks Mobile Home Park (registered agent/owner)", "Serve via registered agent — check Michigan LARA/Corps Online for registered agent address", "Personal service or certified mail per MCR 2.105"),
        ],
        "deadline": "Statute of limitations: 3 years for negligence (MCL 600.5805), 6 years for contract/warranty (MCL 600.5807). File promptly.",
        "response_time": "Defendant has 21 days to answer after personal service (28 days if served by mail per MCR 2.108).",
        "scao_forms": ["MC 01 (Summons)", "MC 21 (Civil Cover Sheet)"],
        "special_notes": "This is a DIFFERENT case (housing, not custody). Different defendants (Shady Oaks, not Emily Watson). Include photos of habitability issues, written complaints to management, repair requests, inspection reports.",
    },
    {
        "id": "F10",
        "title": "CRIMINAL REFERRAL PACKET",
        "court_key": "prosecutor",
        "case_number": None,
        "filing_fee": "$0 (no fee for referral)",
        "contents": [
            "[1] Cover Page / Referral Letter — F10_cover_page.txt",
            "[2] Criminal Referral Narrative — F10_referral.txt",
            "[3] Evidence Summary — F10_evidence_summary.txt",
            "[4] Timeline of Criminal Conduct — F10_timeline.txt",
            "[5] Supporting Exhibits — F10_exhibits/ (documents proving criminal conduct)",
            "[6] Witness List — F10_witness_list.txt",
        ],
        "service_parties": [],
        "deadline": "No deadline. File when evidence is compiled. Statute of limitations for perjury (MCL 750.423) is 6 years.",
        "response_time": "Prosecutor has full discretion. May take weeks to months. No guarantee of prosecution. Follow up in 30 days if no response.",
        "scao_forms": [],
        "special_notes": "This is NOT a court filing — it is a referral to the prosecutor requesting investigation. Be factual, not emotional. Present evidence clearly. Do not accuse — present facts and let prosecutor determine charges. Include all relevant MCL sections (750.423 perjury, 750.157a conspiracy, 600.916 UPL).",
    },
]


def generate_instructions(filing):
    """Generate the full instruction document for a filing."""
    fid = filing["id"]
    title = filing["title"]
    court = COURTS[filing["court_key"]]
    case_num = filing["case_number"] or "N/A"
    fee = filing["filing_fee"]

    lines = []

    # Header
    lines.append("+" + "=" * 68 + "+")
    lines.append(f"|  FILING INSTRUCTIONS — {fid}: {title[:42]}")
    lines.append(f"|  Case: {case_num} | Court: {court['name'][:45]}")
    lines.append("+" + "=" * 68 + "+")
    lines.append("")

    # Package contents
    lines.append("PACKAGE CONTENTS:")
    lines.append("-" * 50)
    for item in filing["contents"]:
        lines.append(f"  [] {item}")
    lines.append("")

    # Before filing
    lines.append("BEFORE FILING:")
    lines.append("-" * 50)
    lines.append("  1. Review ALL documents for accuracy and completeness")
    lines.append("  2. Sign and date ALL signature blocks")
    notarized = [c for c in filing["contents"] if "NOTARIZED" in c.upper()]
    if notarized:
        lines.append("  3. Have affidavit(s) NOTARIZED:")
        lines.append("     - UPS Store (multiple Muskegon locations)")
        lines.append("     - Your bank (many offer free notary)")
        lines.append("     - Muskegon County Clerk's Office (990 Terrace St)")
    copy_count = 1 + len(filing["service_parties"]) + 1
    lines.append(f"  {4 if notarized else 3}. Make {copy_count} copies:")
    lines.append("     - 1 original for the court")
    for i, (name, _, _) in enumerate(filing.get("service_parties", []), 1):
        lines.append(f"     - 1 copy for service on {name}")
    lines.append("     - 1 copy for YOUR records")
    lines.append("")

    # Filing method
    lines.append("FILING METHOD:")
    lines.append("-" * 50)
    lines.append(f"  IN PERSON:")
    lines.append(f"    {court['address']}")
    lines.append(f"    Hours: {court['hours']}")
    lines.append(f"    Phone: {court['phone']}")
    lines.append("")
    lines.append(f"  E-FILING:")
    lines.append(f"    {court['efiling']}")
    if "mifile" in s(court["efiling"]):
        lines.append("    Steps:")
        lines.append("      1. Create account at mifile.courts.michigan.gov (if needed)")
        lines.append(f"      2. Select case number: {case_num}")
        lines.append("      3. Upload all documents as individual PDFs")
        lines.append(f"      4. Pay filing fee: {fee}")
    elif "cm/ecf" in s(court["efiling"]):
        lines.append("    Note: Pro se litigants may file on paper in federal court.")
        lines.append("    For paper filing, mail or deliver to clerk's office.")
    elif "mail" in s(court["efiling"]):
        lines.append("    Mail original + 1 copy to the address above.")
        lines.append("    Keep a copy for your records.")
        lines.append("    Send via certified mail with return receipt requested.")
    lines.append("")

    # Service requirements
    if filing["service_parties"]:
        lines.append("SERVICE REQUIREMENTS (MCR 2.107):")
        lines.append("-" * 50)
        lines.append("  After filing, serve copies on:")
        for i, (name, addr, method) in enumerate(filing["service_parties"], 1):
            lines.append(f"  {i}. {name}")
            lines.append(f"     Address: {addr}")
            lines.append(f"     Method:  {method}")
            lines.append("")
        lines.append("  Complete the Certificate of Service with the actual service")
        lines.append("  date and method used, then file the completed certificate")
        lines.append("  with the court.")
    else:
        lines.append("SERVICE REQUIREMENTS:")
        lines.append("-" * 50)
        lines.append("  No formal service required for this filing type.")
        lines.append("  Retain proof of delivery/mailing for your records.")
    lines.append("")

    # Filing fee
    lines.append(f"FILING FEE: {fee}")
    lines.append("-" * 50)
    if "$0" in fee:
        lines.append("  No fee required.")
    else:
        lines.append("  Payment methods: cash, check, money order, credit card (at window)")
        lines.append("  If IFP (In Forma Pauperis) approved: $0 — attach IFP order")
        lines.append("  IFP form: MC 20 (Affidavit and Order, Suspension of Fees/Costs)")
    lines.append("")

    # Deadline
    lines.append(f"DEADLINE:")
    lines.append("-" * 50)
    lines.append(f"  {filing['deadline']}")
    lines.append("")

    # Expected response time
    lines.append(f"EXPECTED RESPONSE TIME:")
    lines.append("-" * 50)
    lines.append(f"  {filing['response_time']}")
    lines.append("")

    # SCAO forms
    if filing["scao_forms"]:
        lines.append("REQUIRED / RECOMMENDED SCAO FORMS:")
        lines.append("-" * 50)
        for form in filing["scao_forms"]:
            lines.append(f"  - {form}")
        lines.append("  Download from: https://courts.michigan.gov/scao-forms")
    lines.append("")

    # After filing
    lines.append("AFTER FILING:")
    lines.append("-" * 50)
    lines.append("  1. Keep the file-stamped copy for your records")
    lines.append("  2. File proof of service with the court within 7 days")
    lines.append("  3. Calendar the hearing date when set by the court")
    lines.append("  4. Prepare for oral argument if hearing is scheduled")
    lines.append("  5. Monitor the case on MiFILE for any court activity")
    lines.append("")

    # Special notes
    if filing.get("special_notes"):
        lines.append("IMPORTANT NOTES:")
        lines.append("-" * 50)
        lines.append(f"  {filing['special_notes']}")
        lines.append("")

    # Footer
    lines.append("+" + "=" * 68 + "+")
    lines.append(f"|  Prepared for: Andrew James Pigors, Pro Se")
    lines.append(f"|  Generated:    {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    lines.append(f"|  System:       LitigationOS — Tool #275")
    lines.append("+" + "=" * 68 + "+")

    return "\n".join(lines)


def main():
    print("=" * 70)
    print("  TOOL #275: FILING INSTRUCTIONS GENERATOR")
    print("  Pigors v. Watson — LitigationOS")
    print("=" * 70)
    print()

    instructions_dir = os.path.join(OUTPUT_DIR, "instructions")
    os.makedirs(instructions_dir, exist_ok=True)
    os.makedirs(REPORT_DIR, exist_ok=True)

    # ── Connect to DB ────────────────────────────────────────────────────
    conn = None
    if os.path.exists(DB_PATH):
        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA journal_mode=WAL")
        conn.execute("PRAGMA busy_timeout=60000")
        conn.execute("PRAGMA cache_size=-32000")
        conn.execute("""
            CREATE TABLE IF NOT EXISTS filing_instructions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                filing_id TEXT,
                court TEXT,
                filing_fee TEXT,
                deadline_info TEXT,
                service_parties TEXT,
                output_path TEXT,
                generated_date TEXT
            )
        """)
        conn.commit()

    today = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    generated = []

    for filing in FILINGS:
        fid = filing["id"]
        instructions_text = generate_instructions(filing)
        out_path = os.path.join(instructions_dir, f"{fid}_INSTRUCTIONS.txt")

        with open(out_path, 'w', encoding='utf-8') as f:
            f.write(instructions_text)

        court = COURTS[filing["court_key"]]
        service_summary = "; ".join([name for name, _, _ in filing.get("service_parties", [])]) or "None"

        print(f"  [OK] {fid}: {filing['title'][:55]}")
        print(f"        Fee: {filing['filing_fee']} | Service: {service_summary[:40]}")

        generated.append({
            "filing_id": fid,
            "court": court["name"],
            "fee": filing["filing_fee"],
            "deadline": filing["deadline"][:60],
            "path": out_path,
        })

        if conn:
            conn.execute(
                "INSERT INTO filing_instructions "
                "(filing_id, court, filing_fee, deadline_info, service_parties, output_path, generated_date) "
                "VALUES (?, ?, ?, ?, ?, ?, ?)",
                (fid, court["name"], filing["filing_fee"],
                 filing["deadline"], service_summary, out_path, today)
            )

    if conn:
        conn.commit()

    # ── Summary ──────────────────────────────────────────────────────────
    print(f"\n{'=' * 70}")
    print(f"  INSTRUCTIONS GENERATED: {len(generated)} / {len(FILINGS)}")
    print(f"  Output directory: {instructions_dir}")
    if conn:
        print(f"  DB table: filing_instructions ({len(generated)} rows inserted)")
    print(f"{'=' * 70}")

    # ── Summary report ───────────────────────────────────────────────────
    report_path = os.path.join(REPORT_DIR, "filing_instructions_report.txt")
    with open(report_path, 'w', encoding='utf-8') as f:
        f.write("=" * 70 + "\n")
        f.write("  FILING INSTRUCTIONS GENERATION REPORT\n")
        f.write(f"  Generated: {today}\n")
        f.write("=" * 70 + "\n\n")
        f.write(f"  {'ID':<5s} {'Fee':<12s} {'Court':<40s}\n")
        f.write(f"  {'-'*4:<5s} {'-'*10:<12s} {'-'*38:<40s}\n")
        for g in generated:
            f.write(f"  {g['filing_id']:<5s} {g['fee']:<12s} {g['court'][:38]:<40s}\n")
        f.write(f"\n  Total: {len(generated)} instruction packages\n")
    print(f"  Report: {report_path}")

    if conn:
        conn.close()


if __name__ == "__main__":
    main()
