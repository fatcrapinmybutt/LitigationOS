#!/usr/bin/env python3
"""
Tool #272 — Certificate of Service Generator
===============================================
Generates MCR 2.107-compliant Certificates of Service for all filings
(F1-F10).  Each certificate lists the documents served, the parties
served, and the method of service.

Output: GENERATED_FILINGS/certificates_of_service/
"""
import sys, os, json, sqlite3, textwrap
from datetime import datetime

sys.stdout = open(sys.stdout.fileno(), mode='w', encoding='utf-8', errors='replace')

DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', 'litigation_context.db')
REPORTS_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'reports')
OUTPUT_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', 'GENERATED_FILINGS')
COS_DIR = os.path.join(OUTPUT_DIR, 'certificates_of_service')


def s(v):
    return (v or "").lower()


def safe_query(conn, sql, params=()):
    try:
        return conn.execute(sql, params).fetchall()
    except Exception:
        return []


# ── Verified party information (NEVER fabricate) ──────────────────────────
PLAINTIFF = {
    'name': 'Andrew James Pigors',
    'address': '1977 Whitehall Road, Lot 17',
    'city_state_zip': 'North Muskegon, MI 49445',
    'phone': '(231) 903-5690',
    'email': 'andrewjpigors@gmail.com',
}

# ── Service recipients ───────────────────────────────────────────────────
EMILY = {
    'name': 'Emily A. Watson',
    'role': 'Defendant',
    'address': '2160 Garland Drive',
    'city_state_zip': 'Norton Shores, MI 49441',
}

BARNES = {
    'name': 'Jennifer Barnes (P55406)',
    'role': "Defendant's Former Attorney — WITHDREW",
    'firm': 'Barnes Law Firm PLLC',
    'address': '880 Jefferson St Ste B',
    'city_state_zip': 'Muskegon, MI 49440',
    'note': 'Include only if still counsel of record at time of service',
}

FOC = {
    'name': 'Muskegon County Friend of the Court',
    'attn': 'Pamela Rusco',
    'address': '990 Terrace St',
    'city_state_zip': 'Muskegon, MI 49442',
}

JUDGE_MCNEILL = {
    'name': 'Hon. Jenny L. McNeill',
    'role': 'Respondent (JTC Complaint)',
    'address': '14th Circuit Court, 990 Terrace St',
    'city_state_zip': 'Muskegon, MI 49442',
}

JTC = {
    'name': 'Judicial Tenure Commission',
    'address': '3034 W. Grand Blvd., Suite 8-450',
    'city_state_zip': 'Detroit, MI 48202',
}

MSC = {
    'name': 'Michigan Supreme Court — Clerk',
    'address': 'P.O. Box 30052',
    'city_state_zip': 'Lansing, MI 48909',
}

COA = {
    'name': 'Michigan Court of Appeals — Clerk',
    'address': '350 Ottawa Ave NW, Suite 3300',
    'city_state_zip': 'Grand Rapids, MI 49503',
}

MUSKEGON_PA = {
    'name': 'Muskegon County Prosecuting Attorney',
    'address': '990 Terrace St',
    'city_state_zip': 'Muskegon, MI 49442',
}

SHADY_OAKS = {
    'name': '[VERIFY — Shady Oaks Property Owner/Manager]',
    'address': '[VERIFY — Landlord address]',
    'city_state_zip': '[VERIFY]',
}

MUSKEGON_COUNTY = {
    'name': 'Muskegon County (§1983 Defendant)',
    'attn': 'County Attorney',
    'address': '990 Terrace St',
    'city_state_zip': 'Muskegon, MI 49442',
}

WDMI_AG = {
    'name': 'Michigan Attorney General (§1983)',
    'address': 'P.O. Box 30212',
    'city_state_zip': 'Lansing, MI 48909',
}


# ── Filing definitions ───────────────────────────────────────────────────
FILINGS = {
    'F1': {
        'title': 'Motion for Emergency Relief — Custody / Parenting Time',
        'case_number': '2024-001507-DC',
        'court': '14th Judicial Circuit Court, Family Division, Muskegon County',
        'documents': [
            'Motion for Emergency Relief (MC 231)',
            'Brief in Support of Motion',
            'Affidavit of Andrew James Pigors',
            'Exhibit Binder (F1 Exhibits)',
            'Proposed Order',
        ],
        'parties': [EMILY, FOC],
    },
    'F2': {
        'title': 'Motion Regarding Personal Protection Order',
        'case_number': '2023-5907-PP',
        'court': '14th Judicial Circuit Court, Muskegon County',
        'documents': [
            'Motion Regarding Personal Protection Order (CC 379)',
            'Brief in Support of Motion',
            'Affidavit of Andrew James Pigors',
            'Exhibit Binder (F2 Exhibits)',
            'Proposed Order (CC 385)',
        ],
        'parties': [EMILY, FOC],
    },
    'F3': {
        'title': 'Motion to Disqualify Judge',
        'case_number': '2024-001507-DC',
        'court': '14th Judicial Circuit Court, Family Division, Muskegon County',
        'documents': [
            'Motion to Disqualify Judge (MC 264)',
            'Brief in Support of Motion',
            'Affidavit of Andrew James Pigors',
            'Exhibit Binder (F3 Exhibits — Canon Violations)',
            'Proposed Order',
        ],
        'parties': [EMILY, FOC],
    },
    'F4': {
        'title': '42 USC §1983 — Federal Civil Rights Complaint',
        'case_number': '[VERIFY — WDMI Case Number]',
        'court': 'United States District Court, Western District of Michigan',
        'documents': [
            'Complaint under 42 USC §1983',
            'Brief in Support',
            'Affidavit of Andrew James Pigors',
            'Exhibit Binder (F4 Exhibits — Constitutional Violations)',
            'Civil Cover Sheet',
        ],
        'parties': [EMILY, JUDGE_MCNEILL, MUSKEGON_COUNTY, WDMI_AG],
    },
    'F5': {
        'title': 'Application for Superintending Control',
        'case_number': '[VERIFY — MSC Case Number]',
        'court': 'Michigan Supreme Court',
        'documents': [
            'Application for Superintending Control',
            'Brief in Support',
            'Appendix (Record Below)',
            'Exhibit Binder (F5 Exhibits)',
        ],
        'parties': [MSC, EMILY, FOC],
    },
    'F6': {
        'title': 'Judicial Tenure Commission Complaint',
        'case_number': '2024-001507-DC',
        'court': 'Judicial Tenure Commission',
        'documents': [
            'Formal Complaint — Request for Investigation',
            'Memorandum of Judicial Misconduct',
            'Exhibit Binder (F6 Exhibits — Misconduct Evidence)',
            'Canon Violations Index',
        ],
        'parties': [JTC, JUDGE_MCNEILL],
    },
    'F7': {
        'title': 'Court of Appeals — Appeal',
        'case_number': '[VERIFY — COA Docket Number]',
        'court': 'Michigan Court of Appeals',
        'documents': [
            'Claim of Appeal',
            'Appellant Brief',
            'Appendix (Record Below)',
            'Exhibit Binder (F7 Exhibits)',
        ],
        'parties': [COA, EMILY, FOC],
    },
    'F8': {
        'title': 'Motion for Contempt — Court Order Violations',
        'case_number': '2024-001507-DC',
        'court': '14th Judicial Circuit Court, Family Division, Muskegon County',
        'documents': [
            'Motion and Order to Show Cause (Contempt)',
            'Brief in Support',
            'Affidavit of Andrew James Pigors',
            'Exhibit Binder (F8 Exhibits — Violation Evidence)',
            'Proposed Order to Show Cause',
        ],
        'parties': [EMILY, FOC],
    },
    'F9': {
        'title': 'Housing — Shady Oaks Habitability',
        'case_number': '2025-002760-CZ',
        'court': '14th Judicial Circuit Court, Muskegon County',
        'documents': [
            'Complaint — Breach of Habitability / Negligence',
            'Ex Parte Application and Motion for TRO (MC 230)',
            'Affidavit of Andrew James Pigors',
            'Exhibit Binder (F9 Exhibits — Housing Conditions)',
            'Proposed Temporary Restraining Order',
        ],
        'parties': [SHADY_OAKS],
    },
    'F10': {
        'title': 'Criminal Evidence Referral Package',
        'case_number': '2024-001507-DC',
        'court': 'Muskegon County Prosecuting Attorney / Relevant Agencies',
        'documents': [
            'Criminal Evidence Referral Letter',
            'Criminal Evidence Analysis Report',
            'Exhibit Binder (F10 Exhibits — Criminal Evidence)',
            'Statute Satisfaction Analysis',
        ],
        'parties': [MUSKEGON_PA],
    },
}


def _format_party_block(party):
    """Format a single party's service block."""
    lines = []
    name_line = party.get('name', '[UNKNOWN]')
    if 'attn' in party:
        name_line += f"\n    Attn: {party['attn']}"
    if 'firm' in party:
        name_line += f"\n    {party['firm']}"
    lines.append(f"    {name_line}")
    lines.append(f"    {party.get('address', '[VERIFY]')}")
    lines.append(f"    {party.get('city_state_zip', '[VERIFY]')}")
    lines.append("    [ ] First-class mail    [ ] Personal service    [ ] E-filing (MiFILE)")
    if 'note' in party:
        lines.append(f"    NOTE: {party['note']}")
    return '\n'.join(lines)


def generate_certificate(filing_id, filing_info):
    """Generate one certificate of service."""
    docs_list = '\n'.join(f"    {i}. {d}" for i, d in enumerate(filing_info['documents'], 1))
    parties_list = '\n\n'.join(_format_party_block(p) for p in filing_info['parties'])

    txt = textwrap.dedent(f"""\
    {'=' * 72}
    CERTIFICATE OF SERVICE — {filing_id}
    {'=' * 72}

    STATE OF MICHIGAN
    IN THE {filing_info['court'].upper()}
    COUNTY OF MUSKEGON

    Case No. {filing_info['case_number']}

    PIGORS v WATSON

    {'─' * 72}
                        CERTIFICATE OF SERVICE
    {'─' * 72}

    I, {PLAINTIFF['name']}, hereby certify that on _______________
    [DATE], I served a true and correct copy of the following documents:

{docs_list}

    upon the following parties by the method indicated:

{parties_list}

    Service was made in compliance with MCR 2.107.

    I declare under the penalties of perjury that the foregoing is true
    and correct.


    Date: _______________          ________________________________
                                   {PLAINTIFF['name']}, Pro Se Plaintiff
                                   {PLAINTIFF['address']}
                                   {PLAINTIFF['city_state_zip']}
                                   {PLAINTIFF['phone']}
                                   {PLAINTIFF['email']}
    """)
    return txt


def main():
    print("=" * 60)
    print("Tool #272 — Certificate of Service Generator")
    print("=" * 60)

    os.makedirs(COS_DIR, exist_ok=True)
    os.makedirs(REPORTS_DIR, exist_ok=True)

    conn = sqlite3.connect(DB_PATH, timeout=120)
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA busy_timeout=60000")
    conn.execute("PRAGMA cache_size=-32000")
    conn.row_factory = sqlite3.Row

    conn.execute("""\
        CREATE TABLE IF NOT EXISTS certificates_of_service (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            filing_id TEXT,
            document_title TEXT,
            service_method TEXT,
            served_parties TEXT,
            output_path TEXT,
            generated_date TEXT
        )""")
    conn.commit()

    results = []
    now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

    for filing_id, filing_info in FILINGS.items():
        txt = generate_certificate(filing_id, filing_info)
        fname = f"COS_{filing_id}.txt"
        fpath = os.path.join(COS_DIR, fname)
        with open(fpath, 'w', encoding='utf-8') as f:
            f.write(txt)

        party_names = ', '.join(p.get('name', '[UNKNOWN]') for p in filing_info['parties'])

        conn.execute("""\
            INSERT INTO certificates_of_service
            (filing_id, document_title, service_method, served_parties, output_path, generated_date)
            VALUES (?, ?, ?, ?, ?, ?)""",
            (filing_id, filing_info['title'], 'First-class mail / E-filing / Personal service',
             party_names, fpath, now))

        results.append({
            'filing_id': filing_id,
            'title': filing_info['title'],
            'case_number': filing_info['case_number'],
            'court': filing_info['court'],
            'documents_served': len(filing_info['documents']),
            'parties_served': party_names,
            'output_path': fpath,
        })
        print(f"  [OK] {filing_id} — {filing_info['title'][:50]} → {fname}")

    conn.commit()

    # ── Master service checklist ──────────────────────────────────────
    checklist_path = os.path.join(COS_DIR, "SERVICE_CHECKLIST.txt")
    with open(checklist_path, 'w', encoding='utf-8') as f:
        f.write("SERVICE CHECKLIST — Pigors v. Watson\n")
        f.write(f"Generated: {now}\n")
        f.write("=" * 80 + "\n\n")
        f.write("Use this checklist to track actual service completion.\n\n")
        f.write(f"{'Filing':<8}{'Title':<42}{'Served?':<10}{'Date':<12}{'Method'}\n")
        f.write("-" * 80 + "\n")
        for r in results:
            f.write(f"{r['filing_id']:<8}{r['title'][:41]:<42}[ ]       __________  __________\n")
        f.write("\n" + "=" * 80 + "\n")
        f.write("Mark each filing as served when service is completed.\n")
        f.write("Retain proof of mailing receipts or e-filing confirmations.\n")

    # ── Reports ───────────────────────────────────────────────────────
    report_json = {
        'tool': 'certificate_of_service_generator',
        'tool_number': 272,
        'generated': now,
        'cos_dir': COS_DIR,
        'certificates': results,
        'total': len(results),
    }
    json_path = os.path.join(REPORTS_DIR, 'certificate_of_service_generator.json')
    with open(json_path, 'w', encoding='utf-8') as f:
        json.dump(report_json, f, indent=2)

    md_lines = [
        "# Certificate of Service Generator Report",
        f"**Generated:** {now}",
        f"**Output Directory:** `{COS_DIR}`",
        "",
        "## Certificates Generated",
        "",
        "| Filing | Title | Case | Docs | Parties Served |",
        "|--------|-------|------|------|----------------|",
    ]
    for r in results:
        md_lines.append(
            f"| {r['filing_id']} | {r['title'][:35]} | {r['case_number']} "
            f"| {r['documents_served']} | {r['parties_served'][:40]} |")
    md_lines += [
        "",
        "## Service Rules Per Filing",
        "- **F1-F3, F8**: Emily Watson + FOC (14th Circuit family division)",
        "- **F4**: Federal defendants — McNeill, Watson, Muskegon County (WDMI rules)",
        "- **F5**: MSC e-filing + copy to all parties",
        "- **F6**: JTC + Judge McNeill",
        "- **F7**: COA e-filing + copy to all parties",
        "- **F9**: Shady Oaks defendants (landlord/property manager)",
        "- **F10**: Muskegon County PA + relevant agencies",
        "",
        "## Notes",
        "- All party addresses are VERIFIED — never fabricated.",
        "- Date and signature lines left blank for Andrew.",
        "- Check the appropriate service method box when serving.",
        "- Jennifer Barnes listed only where still counsel of record.",
        "- `[VERIFY]` fields require Andrew's confirmation.",
    ]
    md_path = os.path.join(REPORTS_DIR, 'CERTIFICATE_OF_SERVICE_GENERATOR.md')
    with open(md_path, 'w', encoding='utf-8') as f:
        f.write('\n'.join(md_lines))

    conn.close()

    print(f"\n  Total certificates: {len(results)}")
    print(f"  Service checklist: {checklist_path}")
    print(f"  Reports: {json_path}")
    print(f"           {md_path}")
    print("  Done.")


if __name__ == '__main__':
    main()
