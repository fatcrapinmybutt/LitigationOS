#!/usr/bin/env python3
"""
skill_scao_forms.py — SCAO Forms Catalog & Search Skill
Scans SCAO_FORMS directory, catalogs forms, creates DB table, maps to case data.
"""
import sys, os, sqlite3, json, re
from datetime import datetime

sys.stdout.reconfigure(encoding='utf-8')

DB = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), 'litigation_context.db')
SCAO_DIR = r'F:\CANONICAL_ROOT_H\ZIPS\SCAO_FORMS\SCAO FORMS'

# ── Form Category Classification ───────────────────────────────────

FORM_CATEGORIES = {
    'cc': {'category': 'Circuit Court', 'applicable_court': 'Circuit Court', 'case_types': ['civil', 'domestic', 'general']},
    'foc': {'category': 'Friend of the Court', 'applicable_court': 'Circuit Court - Family', 'case_types': ['custody', 'parenting_time', 'support', 'domestic']},
    'pcm': {'category': 'Probate Court - Mental Health', 'applicable_court': 'Probate Court', 'case_types': ['mental_health', 'guardianship']},
    'mc': {'category': 'General / Multi-Court', 'applicable_court': 'All Courts', 'case_types': ['general', 'fee_waiver']},
    'p': {'category': 'Probate', 'applicable_court': 'Probate Court', 'case_types': ['probate']},
    'pa': {'category': 'Prosecuting Attorney', 'applicable_court': 'Circuit Court', 'case_types': ['criminal']},
}

# ── Known Form Titles ──────────────────────────────────────────────

KNOWN_FORMS = {
    'mc20': 'Fee Waiver Request',
    'cc08': 'Summons',
    'cc58': 'Default and Default Judgment',
    'cc59': 'Answer/Response',
    'cc61': 'Counterclaim',
    'cc79': 'Motion',
    'cc88': 'Proof of Service',
    'cc89': 'Affidavit of Service',
    'cc99e': 'Order',
    'cc115': 'Motion for Summary Disposition',
    'cc116': 'Brief in Support',
    'cc117': 'Response to Motion',
    'cc261': 'Subpoena',
    'cc293': 'Application for Entry of Default',
    'cc296': 'Complaint',
    'cc297': 'Answer to Complaint',
    'cc378': 'Discovery Request',
    'cc382a': 'Interrogatories',
    'cc383': 'Request for Production',
    'cc384': 'Request for Admissions',
    'cc385': 'Motion to Compel',
    'cc386': 'Motion for Protective Order',
    'cc387': 'Motion for Sanctions',
    'cc388': 'Motion to Dismiss',
    'cc401': 'Judgment',
    'cc404': 'Claim of Appeal',
    'cc434_new': 'Application for Leave to Appeal',
    'cc450': 'Bond',
    'cc457': 'Consent Judgment',
    'cc458a': 'Stipulation and Order',
    'cc463': 'Notice of Hearing',
    'cc465': 'Notice of Motion',
    'cc520': 'Petition for Personal Protection Order',
    'cc529': 'Personal Protection Order',
    'cc531': 'Motion to Modify/Terminate PPO',
    'cc532': 'Motion to Extend PPO',
    'cc533': 'Motion to Show Cause for PPO Violation',
    'foc': 'Friend of Court General Information',
    'foc101': 'Verified Statement and Application for IV-D Services',
    'foc102': 'Order Regarding Custody/Parenting Time',
    'foc103': 'Uniform Child Support Order',
    'foc104': 'Uniform Spousal Support Order',
    'foc106_new': 'Advice of Rights Regarding FOC',
    'foc110': 'Motion Regarding Support',
    'foc111': 'Order Regarding Support',
    'foc114': 'Motion Regarding Custody',
    'foc119': 'Motion for Show Cause',
    'foc120': 'Order to Show Cause',
    'foc123': 'Income Withholding Order',
    'foc13': 'Support Recommendation Summary',
    'foc13a': 'Child Support Recommendation',
    'foc14': 'Uniform Child Support Order Deviation Addendum',
    'foc16': 'Application for Transfer/Change of Venue',
    'foc17': 'Verified Statement',
    'foc18': 'Summons and Complaint',
    'foc19': 'Answer and Counterclaim',
    'foc1b': 'FOC Case Information',
    'foc2': 'FOC Complaint',
    'foc21': 'Motion for Contempt',
    'foc22': 'Order of Contempt',
    'foc22b': 'Order of Commitment for Contempt',
    'foc23': 'Motion to Modify Custody/Parenting Time',
    'foc24': 'Motion Regarding Parenting Time',
    'foc25': 'Order Regarding Parenting Time',
    'foc29': 'Motion and Affidavit for Custody/Change of Domicile',
    'foc2a': 'FOC Investigation Report',
    'foc39e': 'Motion Regarding Change of Domicile',
    'foc4': 'FOC Referral',
    'foc40': 'Motion for Friend of Court Alternate Dispute Resolution',
    'foc41': 'FOC Custody Mediation Report',
    'foc43': 'Motion for Specific Parenting Time',
    'foc44': 'Order for Specific Parenting Time',
    'foc45': 'Motion for Third Party Custody',
    'foc47': 'Objection to FOC Recommendation',
    'foc48': 'Objection to Proposed Order',
    'foc5': 'FOC Annual Statutory Notice',
    'foc53': 'Motion for Custody/Parenting Time/Support',
    'foc54': 'Custody/Parenting Time/Support Order',
    'foc55': 'Judgment/Order - General',
    'foc60': 'Notice of Custody Proceedings',
    'foc62': 'Response to Motion for Custody Change',
    'foc63': 'Motion to Change Parenting Time',
    'foc64': 'Response to Parenting Time Motion',
    'foc69': 'Motion to Change Support',
    'foc7': 'FOC Statistical Report',
    'foc70': 'Response to Support Motion',
    'foc71': 'Bench Warrant',
    'foc72': 'Bond for Bench Warrant',
    'foc80': 'Joint Custody Agreement',
    'foc81': 'Custody Agreement',
    'foc83': 'Parenting Time Agreement',
    'foc85': 'Affidavit of Income',
    'foc86': 'Financial Statement',
    'foc91': 'Ex Parte Motion for Custody Change',
    'foc92': 'Ex Parte Order for Custody Change',
    'foc93': 'Motion for Makeup Parenting Time',
    'foc94': 'Order for Makeup Parenting Time',
    'foc95': 'Motion for Joint Custody',
    'p05': 'Petition',
    'pab': 'Prosecuting Attorney Brief',
    'pah': 'Prosecuting Attorney Hearing',
    'pcm202': 'Petition for Mental Health Treatment',
    'pcm204': 'Clinical Certificate',
    'pcm205': 'Order for Examination',
    'pcm209a': 'Order for Hospitalization',
    'pcm212': 'Petition for Assisted Outpatient Treatment',
    'pcm215': 'Report of Treatment',
    'pcm220a': 'Motion for Continuing Treatment',
    'pcm222a': 'Order for Continuing Treatment',
    'pcm223': 'Discharge Report',
    'pcm225': 'Petition for New Hospitalization',
    'pcm227': 'Notice of Rights',
    'pcm233': 'Order for Alternative Treatment',
    'pcm236': 'Petition for Substance Use Disorder',
    'pcm237': 'Order for Assessment',
    'pcm238': 'Report of Assessment',
    'pcm239': 'Order for Treatment',
    'pcm240m': 'Motion to Modify Treatment',
    'pcm240o': 'Order to Modify Treatment',
    'pcm244': 'Motion for Review Hearing',
    'pcm245': 'Order After Review',
}

# ── Filing Type Mappings ───────────────────────────────────────────

FILING_TYPE_FORMS = {
    'fee_waiver': ['mc20'],
    'custody_motion': ['foc23', 'foc29', 'foc53', 'foc91', 'foc114', 'cc79', 'cc463'],
    'parenting_time': ['foc24', 'foc25', 'foc43', 'foc44', 'foc63', 'foc93', 'foc94', 'foc83'],
    'contempt': ['foc21', 'foc22', 'foc119', 'foc120', 'foc22b'],
    'support': ['foc110', 'foc111', 'foc69', 'foc103', 'foc104', 'foc123'],
    'ppo': ['cc520', 'cc529', 'cc531', 'cc532', 'cc533'],
    'appeal': ['cc404', 'cc434_new'],
    'discovery': ['cc261', 'cc378', 'cc382a', 'cc383', 'cc384', 'cc385', 'cc386'],
    'motion_general': ['cc79', 'cc115', 'cc116', 'cc117', 'cc387', 'cc388', 'cc463', 'cc465'],
    'complaint': ['cc296', 'cc297', 'foc2', 'foc18', 'foc19'],
    'service': ['cc88', 'cc89'],
    'domicile_change': ['foc29', 'foc39e'],
    'all_filings': ['mc20'],  # fee waiver applies to everything
}

def _conn():
    c = sqlite3.connect(DB, timeout=120)
    c.execute('PRAGMA busy_timeout=60000')
    c.execute('PRAGMA journal_mode=WAL')
    c.row_factory = sqlite3.Row
    return c


def parse_form_info(filename):
    """Parse form number and prefix from filename."""
    base = os.path.splitext(filename)[0].lower().replace('_new', '').replace('_', '')
    match = re.match(r'^([a-z]+)(\d+[a-z]?)$', base)
    if match:
        prefix = match.group(1)
        number = match.group(2)
        return prefix, f"{prefix.upper()} {number}"
    return base, base.upper()


def scan_and_catalog():
    """Scan SCAO forms directory and create catalog in DB."""
    conn = _conn()
    conn.execute("""
        CREATE TABLE IF NOT EXISTS scao_forms_catalog (
            form_id TEXT PRIMARY KEY,
            form_number TEXT,
            form_title TEXT,
            filename TEXT,
            category TEXT,
            applicable_court TEXT,
            applicable_case_type TEXT,
            description TEXT,
            file_path TEXT,
            file_size INTEGER,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP
        )
    """)
    conn.execute("DELETE FROM scao_forms_catalog")

    if not os.path.exists(SCAO_DIR):
        print(f"  ⚠ SCAO directory not found: {SCAO_DIR}")
        return 0

    count = 0
    for fname in os.listdir(SCAO_DIR):
        if not fname.lower().endswith('.pdf'):
            continue
        fpath = os.path.join(SCAO_DIR, fname)
        fsize = os.path.getsize(fpath) if os.path.isfile(fpath) else 0
        base = os.path.splitext(fname)[0].lower()
        prefix, form_number = parse_form_info(fname)

        cat_info = FORM_CATEGORIES.get(prefix, {'category': 'Unknown', 'applicable_court': 'Unknown', 'case_types': []})
        title = KNOWN_FORMS.get(base, KNOWN_FORMS.get(base.replace('_new', ''), f'SCAO Form {form_number}'))

        conn.execute(
            "INSERT OR REPLACE INTO scao_forms_catalog VALUES (?,?,?,?,?,?,?,?,?,?,?)",
            (
                base, form_number, title, fname,
                cat_info['category'], cat_info['applicable_court'],
                json.dumps(cat_info.get('case_types', [])),
                f"Michigan SCAO Form {form_number} — {title}",
                fpath, fsize, datetime.now().isoformat()
            )
        )
        count += 1

    conn.commit()
    conn.execute("PRAGMA wal_checkpoint(TRUNCATE)")
    conn.close()
    return count


# ── Query Functions ─────────────────────────────────────────────────

def search_forms(keyword):
    """Search forms by keyword in title, number, category, or description."""
    conn = _conn()
    rows = conn.execute(
        "SELECT * FROM scao_forms_catalog WHERE "
        "form_title LIKE ? OR form_number LIKE ? OR category LIKE ? OR description LIKE ? "
        "ORDER BY form_number",
        (f'%{keyword}%', f'%{keyword}%', f'%{keyword}%', f'%{keyword}%')
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def get_form(form_number):
    """Get a specific form by form number or form_id."""
    conn = _conn()
    row = conn.execute(
        "SELECT * FROM scao_forms_catalog WHERE form_id LIKE ? OR form_number LIKE ?",
        (f'%{form_number.lower()}%', f'%{form_number}%')
    ).fetchone()
    conn.close()
    return dict(row) if row else None


def get_forms_for_filing(filing_type):
    """Get all forms needed for a specific filing type."""
    form_ids = FILING_TYPE_FORMS.get(filing_type, [])
    if not form_ids:
        # Try fuzzy match
        for ft, ids in FILING_TYPE_FORMS.items():
            if filing_type.lower() in ft:
                form_ids = ids
                break

    conn = _conn()
    results = []
    for fid in form_ids:
        row = conn.execute(
            "SELECT * FROM scao_forms_catalog WHERE form_id=?", (fid,)
        ).fetchone()
        if row:
            results.append(dict(row))
    conn.close()
    return {
        'filing_type': filing_type,
        'forms': results,
        'always_include': [get_form('mc20')] if get_form('mc20') else []
    }


def get_all_forms():
    """Get the complete catalog."""
    conn = _conn()
    rows = conn.execute("SELECT * FROM scao_forms_catalog ORDER BY category, form_number").fetchall()
    conn.close()
    return [dict(r) for r in rows]


def get_forms_by_category():
    """Get forms grouped by category."""
    conn = _conn()
    rows = conn.execute(
        "SELECT category, COUNT(*) as cnt, GROUP_CONCAT(form_number, ', ') as forms "
        "FROM scao_forms_catalog GROUP BY category ORDER BY cnt DESC"
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]


# ── Main ────────────────────────────────────────────────────────────

if __name__ == '__main__':
    print("=" * 70)
    print("SCAO FORMS CATALOG SKILL — DB-WIRED")
    print("=" * 70)

    count = scan_and_catalog()
    print(f"\n[CATALOG] {count} SCAO forms cataloged into DB")

    cats = get_forms_by_category()
    print("\n[CATEGORIES]")
    for c in cats:
        print(f"  • {c['category']}: {c['cnt']} forms")

    print("\n[FILING TYPE MAPPINGS]")
    for ft in ['custody_motion', 'parenting_time', 'ppo', 'contempt', 'discovery']:
        forms = get_forms_for_filing(ft)
        print(f"  • {ft}: {len(forms['forms'])} forms")
        for f in forms['forms']:
            print(f"    - {f['form_number']}: {f['form_title']}")

    print("\n✅ SCAO Forms Skill operational")
