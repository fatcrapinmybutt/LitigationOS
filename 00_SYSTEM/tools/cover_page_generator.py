#!/usr/bin/env python3
"""Tool #274: Cover Page Generator
Generates proper caption/cover pages for ALL filings per MCR 2.113.
Michigan court document format with proper case captions.
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

# ── Verified party info ─────────────────────────────────────────────────────
PRO_SE_BLOCK = """\
Andrew James Pigors, Pro Se
1977 Whitehall Road, Lot 17
North Muskegon, MI 49445
(231) 903-5690
andrewjpigors@gmail.com"""

# ── Filing definitions ───────────────────────────────────────────────────────
FILINGS = [
    {
        "id": "F1",
        "title": "MOTION FOR EMERGENCY RELIEF AND REINSTATEMENT OF PARENTING TIME",
        "subtitle": None,
        "court_type": "circuit",
        "case_number": "2024-001507-DC",
    },
    {
        "id": "F2",
        "title": "MOTION TO MODIFY/TERMINATE PERSONAL PROTECTION ORDER",
        "subtitle": None,
        "court_type": "circuit",
        "case_number": "2023-5907-PP",
    },
    {
        "id": "F3",
        "title": "MOTION TO DISQUALIFY JUDGE PURSUANT TO MCR 2.003",
        "subtitle": None,
        "court_type": "circuit",
        "case_number": "2024-001507-DC",
    },
    {
        "id": "F4",
        "title": "COMPLAINT UNDER 42 U.S.C. § 1983",
        "subtitle": "DEPRIVATION OF CIVIL RIGHTS UNDER COLOR OF LAW",
        "court_type": "federal",
        "case_number": "[TO BE ASSIGNED]",
    },
    {
        "id": "F5",
        "title": "APPLICATION FOR LEAVE TO FILE ORIGINAL ACTION",
        "subtitle": "COMPLAINT FOR SUPERINTENDING CONTROL",
        "court_type": "msc",
        "case_number": "[TO BE ASSIGNED]",
    },
    {
        "id": "F6",
        "title": "VERIFIED COMPLAINT",
        "subtitle": "REQUEST FOR INVESTIGATION OF JUDICIAL MISCONDUCT",
        "court_type": "jtc",
        "case_number": None,
    },
    {
        "id": "F7",
        "title": "APPLICATION FOR LEAVE TO APPEAL",
        "subtitle": "PURSUANT TO MCR 7.205",
        "court_type": "coa",
        "case_number": "[TO BE ASSIGNED]",
    },
    {
        "id": "F8",
        "title": "MOTION AND AFFIDAVIT FOR FINDING OF CONTEMPT",
        "subtitle": None,
        "court_type": "circuit",
        "case_number": "2024-001507-DC",
    },
    {
        "id": "F9",
        "title": "VERIFIED COMPLAINT",
        "subtitle": "NEGLIGENCE AND BREACH OF HABITABILITY WARRANTY",
        "court_type": "circuit_cz",
        "case_number": "2025-002760-CZ",
    },
    {
        "id": "F10",
        "title": "CRIMINAL REFERRAL PACKET",
        "subtitle": "REQUEST FOR INVESTIGATION AND PROSECUTION",
        "court_type": "prosecutor",
        "case_number": None,
    },
]

# ── Caption generators ───────────────────────────────────────────────────────

def gen_circuit_caption(filing):
    """Standard Michigan 14th Circuit Court caption per MCR 2.113."""
    case_no = filing["case_number"]
    title = filing["title"]
    subtitle = filing.get("subtitle") or ""

    # F9 has different parties (housing complaint)
    if filing["id"] == "F9":
        plaintiff_block = "ANDREW JAMES PIGORS,"
        plaintiff_label = "     Plaintiff,"
        defendant_block = "SHADY OAKS MOBILE HOME PARK;\nits owners, operators, and agents,\n     Defendants."
    else:
        plaintiff_block = "ANDREW JAMES PIGORS,"
        plaintiff_label = "     Plaintiff,"
        defendant_block = "EMILY A. WATSON,\n     Defendant."

    division = "FAMILY DIVISION"
    if filing["id"] == "F9":
        division = "CIVIL DIVISION"

    lines = []
    lines.append("STATE OF MICHIGAN")
    lines.append("IN THE 14TH JUDICIAL CIRCUIT COURT")
    lines.append("FOR THE COUNTY OF MUSKEGON")
    lines.append(division)
    lines.append("")
    lines.append(f"{plaintiff_block:<40s} Case No. {case_no}")
    lines.append(f"{plaintiff_label}")
    lines.append(f"{'':40s} Hon. Jenny L. McNeill")
    lines.append("v.")
    lines.append("")
    lines.append(defendant_block)
    lines.append("________________________________________/")
    lines.append("")
    lines.append(f"{'':>20s}{title}")
    if subtitle:
        lines.append(f"{'':>20s}{subtitle}")
    lines.append("")
    lines.append("")
    lines.append(PRO_SE_BLOCK)
    return "\n".join(lines)


def gen_federal_caption(filing):
    """Federal court caption for WDMI."""
    title = filing["title"]
    subtitle = filing.get("subtitle") or ""

    lines = []
    lines.append("UNITED STATES DISTRICT COURT")
    lines.append("WESTERN DISTRICT OF MICHIGAN")
    lines.append("SOUTHERN DIVISION")
    lines.append("")
    lines.append(f"{'ANDREW JAMES PIGORS,':<40s}")
    lines.append(f"{'     Plaintiff,':<40s} Case No. [TO BE ASSIGNED]")
    lines.append("")
    lines.append(f"{'v.':<40s} JURY TRIAL DEMANDED")
    lines.append("")
    lines.append("HON. JENNY L. McNEILL, in her")
    lines.append("individual capacity; EMILY A. WATSON;")
    lines.append("COUNTY OF MUSKEGON,")
    lines.append("     Defendants.")
    lines.append("________________________________________/")
    lines.append("")
    lines.append(f"{'':>20s}{title}")
    if subtitle:
        lines.append(f"{'':>20s}{subtitle}")
    lines.append("")
    lines.append("")
    lines.append(PRO_SE_BLOCK)
    return "\n".join(lines)


def gen_msc_caption(filing):
    """Michigan Supreme Court caption."""
    title = filing["title"]
    subtitle = filing.get("subtitle") or ""

    lines = []
    lines.append("STATE OF MICHIGAN")
    lines.append("IN THE SUPREME COURT")
    lines.append("")
    lines.append(f"{'ANDREW JAMES PIGORS,':<40s}")
    lines.append(f"{'     Plaintiff-Appellant,':<40s} Supreme Court No. [TO BE ASSIGNED]")
    lines.append("")
    lines.append(f"{'v.':<40s} 14th Circuit Court")
    lines.append(f"{'':40s} Case No. 2024-001507-DC")
    lines.append("")
    lines.append("HON. JENNY L. McNEILL,")
    lines.append("     Respondent.")
    lines.append("________________________________________/")
    lines.append("")
    lines.append(f"{'':>20s}{title}")
    if subtitle:
        lines.append(f"{'':>20s}{subtitle}")
    lines.append("")
    lines.append("")
    lines.append(PRO_SE_BLOCK)
    return "\n".join(lines)


def gen_coa_caption(filing):
    """Michigan Court of Appeals caption per MCR 7.205."""
    title = filing["title"]
    subtitle = filing.get("subtitle") or ""

    lines = []
    lines.append("STATE OF MICHIGAN")
    lines.append("IN THE COURT OF APPEALS")
    lines.append("")
    lines.append(f"{'ANDREW JAMES PIGORS,':<40s}")
    lines.append(f"{'     Plaintiff-Appellant,':<40s} Court of Appeals No. [TO BE ASSIGNED]")
    lines.append("")
    lines.append(f"{'v.':<40s} 14th Circuit Court")
    lines.append(f"{'':40s} Case No. 2024-001507-DC")
    lines.append("")
    lines.append("EMILY A. WATSON,")
    lines.append("     Defendant-Appellee.")
    lines.append("________________________________________/")
    lines.append("")
    lines.append(f"{'':>20s}{title}")
    if subtitle:
        lines.append(f"{'':>20s}{subtitle}")
    lines.append("")
    lines.append("")
    lines.append(PRO_SE_BLOCK)
    return "\n".join(lines)


def gen_jtc_caption(filing):
    """Judicial Tenure Commission complaint format."""
    title = filing["title"]
    subtitle = filing.get("subtitle") or ""

    lines = []
    lines.append("STATE OF MICHIGAN")
    lines.append("JUDICIAL TENURE COMMISSION")
    lines.append("")
    lines.append("In the Matter of:")
    lines.append("")
    lines.append("HON. JENNY L. McNEILL")
    lines.append("14th Judicial Circuit Court")
    lines.append("Muskegon County, Michigan")
    lines.append("________________________________________/")
    lines.append("")
    lines.append(f"{'':>20s}{title}")
    if subtitle:
        lines.append(f"{'':>20s}{subtitle}")
    lines.append("")
    lines.append("Filed by:")
    lines.append("")
    lines.append(PRO_SE_BLOCK)
    return "\n".join(lines)


def gen_prosecutor_caption(filing):
    """Criminal referral packet — addressed to Muskegon County Prosecutor."""
    title = filing["title"]
    subtitle = filing.get("subtitle") or ""

    lines = []
    lines.append("MUSKEGON COUNTY PROSECUTOR'S OFFICE")
    lines.append("990 Terrace Street, Suite 500")
    lines.append("Muskegon, Michigan 49442")
    lines.append("")
    lines.append("RE: " + title)
    if subtitle:
        lines.append("    " + subtitle)
    lines.append("")
    lines.append("Related Case Numbers:")
    lines.append("  - 2024-001507-DC (Pigors v. Watson, 14th Circuit, Family Division)")
    lines.append("  - 2023-5907-PP   (Personal Protection Order)")
    lines.append("")
    lines.append("Submitted by:")
    lines.append("")
    lines.append(PRO_SE_BLOCK)
    lines.append("")
    lines.append("________________________________________")
    lines.append(f"Date: {'_' * 20}")
    return "\n".join(lines)


GENERATORS = {
    "circuit": gen_circuit_caption,
    "circuit_cz": gen_circuit_caption,
    "federal": gen_federal_caption,
    "msc": gen_msc_caption,
    "coa": gen_coa_caption,
    "jtc": gen_jtc_caption,
    "prosecutor": gen_prosecutor_caption,
}

COURT_LABELS = {
    "circuit": "14th Circuit Court, Muskegon County",
    "circuit_cz": "14th Circuit Court, Muskegon County",
    "federal": "U.S. District Court, Western District of Michigan",
    "msc": "Michigan Supreme Court",
    "coa": "Michigan Court of Appeals",
    "jtc": "Judicial Tenure Commission",
    "prosecutor": "Muskegon County Prosecutor",
}


def main():
    print("=" * 70)
    print("  TOOL #274: COVER PAGE GENERATOR")
    print("  Pigors v. Watson — MCR 2.113 Compliant")
    print("=" * 70)
    print()

    cover_dir = os.path.join(OUTPUT_DIR, "cover_pages")
    os.makedirs(cover_dir, exist_ok=True)
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
            CREATE TABLE IF NOT EXISTS generated_cover_pages (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                filing_id TEXT,
                court TEXT,
                case_number TEXT,
                document_title TEXT,
                output_path TEXT,
                generated_date TEXT
            )
        """)
        conn.commit()

    today = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    generated = []

    for filing in FILINGS:
        fid = filing["id"]
        court_type = filing["court_type"]
        generator = GENERATORS.get(court_type)
        if not generator:
            print(f"  [SKIP] {fid}: No generator for court type '{court_type}'")
            continue

        cover_text = generator(filing)
        out_path = os.path.join(cover_dir, f"{fid}_cover_page.txt")

        with open(out_path, 'w', encoding='utf-8') as f:
            f.write(cover_text)

        court_label = COURT_LABELS.get(court_type, court_type)
        print(f"  [OK] {fid}: {filing['title'][:55]}")
        print(f"        Court: {court_label} | Case: {filing['case_number'] or 'N/A'}")
        print(f"        Saved: {out_path}")

        generated.append({
            "filing_id": fid,
            "court": court_label,
            "case_number": filing["case_number"] or "N/A",
            "title": filing["title"],
            "path": out_path,
        })

        if conn:
            conn.execute(
                "INSERT INTO generated_cover_pages "
                "(filing_id, court, case_number, document_title, output_path, generated_date) "
                "VALUES (?, ?, ?, ?, ?, ?)",
                (fid, court_label, filing["case_number"] or "N/A",
                 filing["title"], out_path, today)
            )

    if conn:
        conn.commit()

    # ── Summary ──────────────────────────────────────────────────────────
    print(f"\n{'=' * 70}")
    print(f"  COVER PAGES GENERATED: {len(generated)} / {len(FILINGS)}")
    print(f"  Output directory: {cover_dir}")
    if conn:
        print(f"  DB table: generated_cover_pages ({len(generated)} rows inserted)")
    print(f"{'=' * 70}")

    # ── Summary report ───────────────────────────────────────────────────
    report_path = os.path.join(REPORT_DIR, "cover_pages_report.txt")
    with open(report_path, 'w', encoding='utf-8') as f:
        f.write("=" * 70 + "\n")
        f.write("  COVER PAGE GENERATION REPORT\n")
        f.write(f"  Generated: {today}\n")
        f.write("=" * 70 + "\n\n")
        for g in generated:
            f.write(f"  {g['filing_id']}: {g['title']}\n")
            f.write(f"    Court: {g['court']}\n")
            f.write(f"    Case:  {g['case_number']}\n")
            f.write(f"    Path:  {g['path']}\n\n")
    print(f"  Report: {report_path}")

    if conn:
        conn.close()


if __name__ == "__main__":
    main()
