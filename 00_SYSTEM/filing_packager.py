#!/usr/bin/env python3
"""
LitigationOS Filing Package Assembler
======================================
Generates court-ready filing packages with:
- Exhibit cover sheets (Bates-numbered, MRE foundation)
- Foundation paragraphs embedded in the motion/brief
- Filing set assembly (motion + affidavit + proposed order + CoS + exhibits)
- MCR 2.113 compliance verification
- SCAO form checklist per filing type

Usage:
  python filing_packager.py --filing <filing_id>     # Package specific filing
  python filing_packager.py --lane <lane>             # Package all filings in lane
  python filing_packager.py --all                     # Package everything
  python filing_packager.py --list                    # List available filings
"""

import os
import sys
import re
import json
import sqlite3
from datetime import datetime, date
from pathlib import Path

# ─── Configuration ──────────────────────────────────────────────────────────
DB_PATH = r"C:\Users\andre\litigation_context.db"
VEHICLES_DIR = r"C:\Users\andre\LitigationOS\06_VEHICLES"
FILINGS_DIR = r"C:\Users\andre\LitigationOS\04_COURT_FILINGS"
OUTPUT_DIR = r"C:\Users\andre\LitigationOS\04_COURT_FILINGS\03_FINAL\COURT_READY"
EXHIBIT_INDEX_PATH = os.path.join(FILINGS_DIR, "MASTER_EXHIBIT_INDEX.md")

CASE_INFO = {
    "plaintiff": "Andrew J. Pigors",
    "defendant": "Emily A. Watson (fka Pigors)",
    "judge": "Hon. Jenny L. McNeill",
    "custody_case": "2024-001507-DC",
    "ppo_case": "2023-5907-PP",
    "coa_case": "COA-366810",
    "court": "14th Judicial Circuit Court — Family Division",
    "county": "Muskegon",
    "address": "1977 Whitehall Road, Lot 17\nLaketon Township, Michigan 49445",
    "phone": "(231) 903-5690",
    "bates_prefix": "PIGORS",
    "separation_days": (date.today() - date(2024, 3, 26)).days,
}

# ─── Filing Type Definitions ────────────────────────────────────────────────
# Each filing type specifies required components and SCAO forms
FILING_TYPES = {
    "MOTION": {
        "components": [
            "main_document",
            "affidavit_or_declaration",
            "proposed_order",
            "exhibit_index",
            "exhibits_with_covers",
            "certificate_of_service",
        ],
        "scao_forms": ["FOC 2 (Motion Cover Page)", "FOC 88 (Affidavit/Declaration)"],
        "copies": {"court": 1, "judge": 1, "opposing": 1, "file": 1},
        "mcr_authority": "MCR 2.119(A)(1)",
    },
    "EMERGENCY_MOTION": {
        "components": [
            "main_document",
            "affidavit_or_declaration",
            "proposed_order",
            "exhibit_index",
            "exhibits_with_covers",
            "certificate_of_service",
            "notice_of_hearing",
        ],
        "scao_forms": [
            "FOC 2 (Motion Cover Page)",
            "FOC 88 (Affidavit/Declaration)",
            "MC 305 (Motion for Immediate Consideration)",
        ],
        "copies": {"court": 1, "judge": 1, "opposing": 1, "file": 1},
        "mcr_authority": "MCR 2.119(A)(1), MCR 3.206(B)(5)",
    },
    "BRIEF": {
        "components": [
            "main_document",
            "table_of_contents",
            "table_of_authorities",
            "appendix",
            "certificate_of_service",
        ],
        "scao_forms": [],
        "copies": {"court": 1, "opposing": 1, "file": 1},
        "mcr_authority": "MCR 7.212(B), MCR 7.312",
    },
    "COMPLAINT": {
        "components": [
            "main_document",
            "summons",
            "civil_case_cover_sheet",
            "exhibit_index",
            "exhibits_with_covers",
            "certificate_of_service",
        ],
        "scao_forms": ["MC 01 (Summons)", "MC 20 (Fee Waiver)", "CC 280 (Case Cover Sheet)"],
        "copies": {"court": 1, "per_defendant": 1, "file": 1},
        "mcr_authority": "MCR 2.110, MCR 2.111",
    },
    "APPLICATION": {
        "components": [
            "main_document",
            "appendix",
            "proof_of_service",
            "copy_of_coa_decision",
            "copy_of_trial_court_orders",
            "certificate_of_service",
        ],
        "scao_forms": [],
        "copies": {"court": 8, "opposing": 1, "file": 1},
        "mcr_authority": "MCR 7.305(A)",
    },
}

# ─── Exhibit Cover Sheet Generator ──────────────────────────────────────────
def generate_exhibit_cover_sheet(exhibit):
    """Generate a formal exhibit cover sheet per Michigan practice."""
    return f"""
{'='*72}
                    EXHIBIT COVER SHEET
{'='*72}

EXHIBIT NO.:     {exhibit['number']}
BATES RANGE:     {exhibit['bates_range']}
DESCRIPTION:     {exhibit['description']}
DATE OF DOC:     {exhibit['date']}
SOURCE:          {exhibit['source']}
PAGES:           {exhibit['page_count']}

{'─'*72}

CASE:            Pigors v. Watson
CASE NO.:        {CASE_INFO['custody_case']}
COURT:           {CASE_INFO['court']}
COUNTY:          {CASE_INFO['county']}

{'─'*72}

AUTHENTICATION METHOD:
  {exhibit['auth_method']}

MRE FOUNDATION:
  {exhibit['mre_foundation']}

RELEVANCE:
  {exhibit.get('relevance', 'See citing motion/brief for relevance discussion.')}

{'─'*72}

OFFERED BY:      {CASE_INFO['plaintiff']}, Plaintiff/Appellant, In Pro Per
PREPARED:        {datetime.now().strftime('%B %d, %Y')}

{'='*72}
""".strip()


# ─── Foundation Paragraph Generator ─────────────────────────────────────────
def generate_foundation_paragraph(exhibit, para_num):
    """Generate foundation-laying paragraph for embedding in motion/brief."""
    auth_type = exhibit.get('auth_type', 'witness_knowledge')

    templates = {
        'public_record': (
            f"{para_num}. **Exhibit {exhibit['number']}** "
            f"({exhibit['bates_range']}) is a certified copy of "
            f"{exhibit['description']}, obtained from {exhibit['source']}. "
            f"This exhibit is self-authenticating under MRE 902(1) (domestic "
            f"public document under seal) and MRE 902(4) (certified copy of "
            f"public record). It is admissible as a public record under "
            f"MRE 803(8). The document establishes {exhibit.get('relevance', '[relevance]')}."
        ),
        'witness_knowledge': (
            f"{para_num}. **Exhibit {exhibit['number']}** "
            f"({exhibit['bates_range']}) is {exhibit['description']}. "
            f"Plaintiff has personal knowledge of this document and can "
            f"authenticate it under MRE 901(b)(1) as a witness with knowledge. "
            f"The document is a fair and accurate representation of what it "
            f"purports to be. It is relevant to {exhibit.get('relevance', '[relevance]')} "
            f"and admissible under MRE 401-402."
        ),
        'business_record': (
            f"{para_num}. **Exhibit {exhibit['number']}** "
            f"({exhibit['bates_range']}) is {exhibit['description']}, "
            f"maintained in the regular course of business by {exhibit['source']}. "
            f"This exhibit is self-authenticating under MRE 902(11) "
            f"(certified domestic record of regularly conducted activity) "
            f"and admissible under MRE 803(6) (business records exception). "
            f"It establishes {exhibit.get('relevance', '[relevance]')}."
        ),
        'distinctive_characteristics': (
            f"{para_num}. **Exhibit {exhibit['number']}** "
            f"({exhibit['bates_range']}) is {exhibit['description']}. "
            f"The document is authenticated by its distinctive characteristics "
            f"under MRE 901(b)(4), including appearance, contents, substance, "
            f"and internal patterns. It is relevant to and tends to prove "
            f"{exhibit.get('relevance', '[relevance]')}."
        ),
    }

    return templates.get(auth_type, templates['witness_knowledge'])


# ─── Filing Package Assembly ────────────────────────────────────────────────
def get_filing_type(filename):
    """Determine filing type from filename."""
    fn = filename.upper()
    if 'EMERGENCY' in fn:
        return 'EMERGENCY_MOTION'
    if 'MOTION' in fn:
        return 'MOTION'
    if 'BRIEF' in fn or 'APPELLANT' in fn:
        return 'BRIEF'
    if 'COMPLAINT' in fn:
        return 'COMPLAINT'
    if 'APPLICATION' in fn:
        return 'APPLICATION'
    return 'MOTION'


def parse_exhibit_index():
    """Parse the MASTER_EXHIBIT_INDEX.md into structured exhibit data."""
    exhibits = []
    if not os.path.exists(EXHIBIT_INDEX_PATH):
        print(f"  ⚠ Exhibit index not found: {EXHIBIT_INDEX_PATH}")
        return exhibits

    with open(EXHIBIT_INDEX_PATH, 'r', encoding='utf-8', errors='replace') as f:
        content = f.read()

    # Parse table rows: | **A-1** | PIGORS-0001 – 0003 | Description | Date | Source | Auth | MRE |
    pattern = r'\|\s*\*\*([A-Z]-\d+)\*\*\s*\|\s*(PIGORS-\d+\s*[–—-]\s*\d+)\s*\|\s*([^|]+)\|\s*([^|]+)\|\s*([^|]+)\|\s*([^|]+)\|\s*([^|]+)\|'
    for match in re.finditer(pattern, content):
        num, bates, desc, dt, src, auth, mre = [m.strip() for m in match.groups()]
        # Determine auth type from MRE foundation text
        auth_type = 'public_record'
        if '901(b)(1)' in mre:
            auth_type = 'witness_knowledge'
        elif '902(11)' in mre or '803(6)' in mre:
            auth_type = 'business_record'
        elif '901(b)(4)' in mre:
            auth_type = 'distinctive_characteristics'

        # Count pages from Bates range
        bates_nums = re.findall(r'\d+', bates)
        page_count = int(bates_nums[-1]) - int(bates_nums[0]) + 1 if len(bates_nums) >= 2 else 1

        exhibits.append({
            'number': num,
            'bates_range': bates,
            'description': desc,
            'date': dt,
            'source': src,
            'auth_method': auth,
            'mre_foundation': mre,
            'auth_type': auth_type,
            'page_count': page_count,
        })

    return exhibits


def find_exhibits_for_filing(filing_content, all_exhibits):
    """Find which exhibits are referenced in a filing document.
    
    Uses multi-strategy matching:
    1. Direct exhibit number references (Exhibit A-1, Ex. A-1)
    2. Bates number references (PIGORS-0001)
    3. Semantic keyword matching — links filing content to exhibit descriptions
    """
    referenced = []
    content_lower = filing_content.lower()

    # Keyword map: filing content keywords → exhibit categories/descriptions
    keyword_exhibit_map = {
        # Court Orders
        'ppo': ['ppo', 'personal protection'],
        'ex parte order': ['ex parte order', 'ex parte'],
        'ex parte': ['ex parte'],
        'custody order': ['custody', 'judgment of custody'],
        'parenting time order': ['parenting time', 'custody'],
        'sanction': ['sanction'],
        # Evidence types
        'narcotics screen': ['narcotics', 'drug screen', 'toxicology'],
        'negative': ['narcotics', 'drug screen', 'negative'],
        'drug test': ['narcotics', 'drug screen', 'toxicology'],
        'transcript': ['transcript', 'hearing transcript'],
        'police report': ['police report', 'nspd', 'officer'],
        'photograph': ['photo', 'image'],
        'text message': ['text message', 'sms', 'communication'],
        'email': ['email', 'correspondence'],
        'voicemail': ['voicemail', 'recording', 'audio'],
        'usb': ['usb', 'recording'],
        'mental health': ['mental health', 'evaluation', 'assessment', 'healthwest'],
        'cas report': ['cas', 'child assessment'],
        'foc': ['friend of court', 'foc'],
        'financial': ['financial', 'income', 'tax', 'ledger'],
        'school record': ['school', 'academic'],
        'medical': ['medical', 'health', 'doctor'],
    }

    for ex in all_exhibits:
        matched = False
        ex_desc_lower = ex['description'].lower()

        # Strategy 1: Direct exhibit number
        for pat in [re.escape(ex['number']), re.escape(f"Ex. {ex['number']}")]:
            if re.search(pat, filing_content, re.IGNORECASE):
                matched = True
                break

        # Strategy 2: Bates number
        if not matched:
            bates_nums = re.findall(r'\d+', ex['bates_range'])
            if bates_nums:
                bates_pat = f"PIGORS-{bates_nums[0]}"
                if bates_pat in filing_content:
                    matched = True

        # Strategy 3: Semantic keyword matching
        if not matched:
            for filing_keyword, exhibit_keywords in keyword_exhibit_map.items():
                if filing_keyword in content_lower:
                    for ek in exhibit_keywords:
                        if ek in ex_desc_lower:
                            matched = True
                            break
                if matched:
                    break

        if matched:
            referenced.append(ex)

    return referenced


def generate_filing_checklist(filing_name, filing_type_key, exhibits_used):
    """Generate a comprehensive filing checklist."""
    ft = FILING_TYPES.get(filing_type_key, FILING_TYPES['MOTION'])

    checklist = f"""
# FILING PACKAGE CHECKLIST
## {filing_name}
### Generated: {datetime.now().strftime('%B %d, %Y at %H:%M')}

---

## FILING TYPE: {filing_type_key}
## GOVERNING AUTHORITY: {ft['mcr_authority']}

---

## REQUIRED COMPONENTS

"""
    for i, comp in enumerate(ft['components'], 1):
        label = comp.replace('_', ' ').title()
        checklist += f"- [ ] **{i}. {label}**\n"

    if ft['scao_forms']:
        checklist += "\n## SCAO FORMS REQUIRED\n\n"
        for form in ft['scao_forms']:
            checklist += f"- [ ] {form}\n"

    checklist += f"\n## COPIES REQUIRED\n\n"
    for recipient, count in ft['copies'].items():
        label = recipient.replace('_', ' ').title()
        checklist += f"- [ ] {label}: {count} cop{'y' if count == 1 else 'ies'}\n"

    if exhibits_used:
        checklist += f"\n## EXHIBITS INCLUDED ({len(exhibits_used)} total)\n\n"
        checklist += "| # | Ex. No. | Bates Range | Description | Cover Sheet | Foundation |\n"
        checklist += "|---|---------|-------------|-------------|-------------|------------|\n"
        for i, ex in enumerate(exhibits_used, 1):
            checklist += f"| {i} | {ex['number']} | {ex['bates_range']} | {ex['description'][:50]}... | ☐ | ☐ |\n"

    checklist += f"""
## MCR 2.113 FORMAT COMPLIANCE

- [ ] 8.5" × 11" paper
- [ ] 1-inch margins all sides
- [ ] 12-point proportional serif font (Times New Roman)
- [ ] Double-spaced body text
- [ ] Sequential paragraph numbering
- [ ] Full caption with case number and judge name
- [ ] Signature block with date
- [ ] Certificate of Service attached

## PRE-FILING VERIFICATION

- [ ] All citations verified against authority database
- [ ] All exhibit Bates numbers match Master Exhibit Index
- [ ] Alienation theme present (MCL 722.23(j), Harvey v Harvey)
- [ ] Separation day count current ({CASE_INFO['separation_days']}+ days)
- [ ] No naked legal claims (every assertion has citation)
- [ ] IRAC structure present in argument sections
- [ ] Proposed order attached (if motion)
- [ ] Filing fee paid or IFP affidavit attached

## SERVICE REQUIREMENTS

- [ ] Certificate of Service completed
- [ ] Opposing party served: Emily A. Watson
- [ ] Method documented: [First-class mail / Personal / E-filing]
- [ ] Date of service: _______________
"""
    return checklist


def generate_exhibit_foundation_section(exhibits_used, start_para=None):
    """Generate a complete foundation section for all exhibits used."""
    if not exhibits_used:
        return ""

    section = """
---

# EXHIBIT FOUNDATION AND AUTHENTICATION

The following exhibits are offered in support of this filing. Each exhibit
is identified by its Master Exhibit Index number, Bates range, and the
Michigan Rule of Evidence under which it is authenticated and admitted.

"""
    para = start_para or 100
    for ex in exhibits_used:
        section += generate_foundation_paragraph(ex, para) + "\n\n"
        para += 1

    return section


def assemble_filing_package(filing_path, all_exhibits):
    """Assemble a complete filing package for a single document."""
    filing_name = os.path.basename(filing_path)
    filing_type_key = get_filing_type(filing_name)

    print(f"\n{'='*60}")
    print(f"  PACKAGING: {filing_name}")
    print(f"  Type: {filing_type_key}")
    print(f"{'='*60}")

    with open(filing_path, 'r', encoding='utf-8', errors='replace') as f:
        content = f.read()

    # Find referenced exhibits
    exhibits_used = find_exhibits_for_filing(content, all_exhibits)
    print(f"  📎 Exhibits referenced: {len(exhibits_used)}")

    # Create output directory
    pkg_name = filing_name.replace('.md', '')
    pkg_dir = os.path.join(OUTPUT_DIR, pkg_name)
    os.makedirs(pkg_dir, exist_ok=True)

    # 1. Copy main document
    main_path = os.path.join(pkg_dir, f"01_MAIN_{filing_name}")
    with open(main_path, 'w', encoding='utf-8') as f:
        f.write(content)
    print(f"  ✅ Main document")

    # 2. Generate exhibit cover sheets
    if exhibits_used:
        covers_dir = os.path.join(pkg_dir, "EXHIBIT_COVERS")
        os.makedirs(covers_dir, exist_ok=True)
        for ex in exhibits_used:
            cover = generate_exhibit_cover_sheet(ex)
            cover_path = os.path.join(covers_dir, f"COVER_{ex['number']}.md")
            with open(cover_path, 'w', encoding='utf-8') as f:
                f.write(cover)
        print(f"  ✅ {len(exhibits_used)} exhibit cover sheets")

    # 3. Generate exhibit index for this filing
    if exhibits_used:
        index_content = f"# EXHIBIT INDEX — {filing_name}\n"
        index_content += f"## {CASE_INFO['plaintiff']} v. {CASE_INFO['defendant']}\n"
        index_content += f"## Case No. {CASE_INFO['custody_case']}\n\n"
        index_content += "| # | Ex. No. | Bates Range | Description | Auth. Method | Pages |\n"
        index_content += "|---|---------|-------------|-------------|-------------|-------|\n"
        for i, ex in enumerate(exhibits_used, 1):
            index_content += (
                f"| {i} | {ex['number']} | {ex['bates_range']} | "
                f"{ex['description'][:60]} | {ex['auth_method'][:30]} | "
                f"{ex['page_count']} |\n"
            )
        index_path = os.path.join(pkg_dir, f"02_EXHIBIT_INDEX.md")
        with open(index_path, 'w', encoding='utf-8') as f:
            f.write(index_content)
        print(f"  ✅ Exhibit index")

    # 4. Generate foundation section
    if exhibits_used:
        foundation = generate_exhibit_foundation_section(exhibits_used)
        found_path = os.path.join(pkg_dir, f"03_EXHIBIT_FOUNDATION.md")
        with open(found_path, 'w', encoding='utf-8') as f:
            f.write(foundation)
        print(f"  ✅ Foundation paragraphs")

    # 5. Generate filing checklist
    checklist = generate_filing_checklist(filing_name, filing_type_key, exhibits_used)
    checklist_path = os.path.join(pkg_dir, f"00_FILING_CHECKLIST.md")
    with open(checklist_path, 'w', encoding='utf-8') as f:
        f.write(checklist)
    print(f"  ✅ Filing checklist")

    # 6. Generate proof of service template
    pos = generate_proof_of_service(filing_name, filing_type_key)
    pos_path = os.path.join(pkg_dir, f"04_CERTIFICATE_OF_SERVICE.md")
    with open(pos_path, 'w', encoding='utf-8') as f:
        f.write(pos)
    print(f"  ✅ Certificate of Service")

    return {
        'filing': filing_name,
        'type': filing_type_key,
        'exhibits': len(exhibits_used),
        'output_dir': pkg_dir,
        'files_created': len(os.listdir(pkg_dir)) + (
            len(os.listdir(os.path.join(pkg_dir, "EXHIBIT_COVERS")))
            if os.path.exists(os.path.join(pkg_dir, "EXHIBIT_COVERS")) else 0
        ),
    }


def generate_proof_of_service(filing_name, filing_type):
    """Generate a Certificate/Proof of Service."""
    return f"""
# CERTIFICATE OF SERVICE

STATE OF MICHIGAN  )
                   ) ss.
COUNTY OF MUSKEGON )

I, {CASE_INFO['plaintiff']}, certify that on _________________, 2026,
I served a true and complete copy of the following document(s):

**1. {filing_name.replace('_', ' ').replace('.md', '')}**
**2. Exhibit Index and All Referenced Exhibits**
**3. Proposed Order** (if applicable)

upon the following parties by the method indicated:

---

**Emily A. Watson (fka Pigors)**
[Address]
Muskegon County, Michigan

☐ First-class U.S. Mail, postage prepaid
☐ Personal service
☐ Electronic service via [e-filing system]
☐ Other: _______________

---

I declare under the penalties of perjury that this Certificate of Service
is true and correct. MCR 2.107(C)(3).

Date: _________________

___________________________________
{CASE_INFO['plaintiff']}
{CASE_INFO['address']}
Telephone: {CASE_INFO['phone']}
Appearing Pro Se
""".strip()


# ─── Database Integration ───────────────────────────────────────────────────
def save_package_to_db(results):
    """Save packaging results to database."""
    try:
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        c.execute("""CREATE TABLE IF NOT EXISTS filing_packages (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            filing_name TEXT,
            filing_type TEXT,
            exhibit_count INTEGER,
            files_created INTEGER,
            output_dir TEXT,
            packaged_at TEXT DEFAULT (datetime('now')),
            status TEXT DEFAULT 'PACKAGED'
        )""")
        for r in results:
            c.execute(
                "INSERT INTO filing_packages (filing_name, filing_type, exhibit_count, files_created, output_dir) VALUES (?,?,?,?,?)",
                (r['filing'], r['type'], r['exhibits'], r['files_created'], r['output_dir'])
            )
        conn.commit()
        conn.close()
        print(f"\n📊 {len(results)} filing packages saved to database.")
    except Exception as e:
        print(f"\n⚠ DB save error: {e}")


# ─── Main Entry Point ───────────────────────────────────────────────────────
def main():
    print("=" * 60)
    print("  LITIGATIONOS FILING PACKAGE ASSEMBLER")
    print(f"  Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"  Separation: {CASE_INFO['separation_days']}+ days")
    print("=" * 60)

    # Parse master exhibit index
    print("\n📋 Parsing Master Exhibit Index...")
    all_exhibits = parse_exhibit_index()
    print(f"   Found {len(all_exhibits)} exhibits")

    # Find all V4 filing documents
    filings = []
    for root, dirs, files in os.walk(VEHICLES_DIR):
        for fname in files:
            if fname.endswith('_V4.md') and not fname.startswith('.'):
                filings.append(os.path.join(root, fname))

    # Also include MSC Application
    for root, dirs, files in os.walk(VEHICLES_DIR):
        for fname in files:
            if 'MSC_APPLICATION' in fname and fname.endswith('.md'):
                path = os.path.join(root, fname)
                if path not in filings:
                    filings.append(path)

    print(f"\n📂 Found {len(filings)} filing documents to package")

    # Handle command-line arguments
    target_filing = None
    target_lane = None
    list_only = False

    for arg in sys.argv[1:]:
        if arg == '--list':
            list_only = True
        elif arg == '--all':
            pass
        elif arg.startswith('--filing='):
            target_filing = arg.split('=', 1)[1]
        elif arg.startswith('--lane='):
            target_lane = arg.split('=', 1)[1].upper()

    if list_only:
        print("\nAvailable filings:")
        for f in sorted(filings):
            print(f"  • {os.path.basename(f)} ({get_filing_type(os.path.basename(f))})")
        return

    # Filter by target
    if target_filing:
        filings = [f for f in filings if target_filing.lower() in os.path.basename(f).lower()]
    if target_lane:
        filings = [f for f in filings if target_lane in f.upper()]

    if not filings:
        print("❌ No filings matched the filter criteria.")
        return

    # Create output directory
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    # Assemble packages
    results = []
    for fpath in sorted(filings):
        try:
            result = assemble_filing_package(fpath, all_exhibits)
            results.append(result)
        except Exception as e:
            print(f"\n❌ Error packaging {os.path.basename(fpath)}: {e}")

    # Summary
    print("\n" + "=" * 60)
    print("  PACKAGING SUMMARY")
    print("=" * 60)
    total_files = sum(r['files_created'] for r in results)
    total_exhibits = sum(r['exhibits'] for r in results)
    print(f"  Filing packages created: {len(results)}")
    print(f"  Total files generated:   {total_files}")
    print(f"  Total exhibits covered:  {total_exhibits}")
    print(f"  Output directory:        {OUTPUT_DIR}")

    # Save to database
    save_package_to_db(results)


if __name__ == '__main__':
    main()
