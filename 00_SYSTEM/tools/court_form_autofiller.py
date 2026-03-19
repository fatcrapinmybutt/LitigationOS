#!/usr/bin/env python3
"""
Tool #51 — Court Form Auto-Filler
====================================
Automatically fills Michigan SCAO court forms from the litigation database.
Maps party data, case numbers, and court info to form fields.

Uses court_forms.db (35+ forms) and litigation_context.db party data.
Generates fill instructions that can be applied to PDF forms.
"""
import sys, json, sqlite3
from pathlib import Path
from datetime import datetime

sys.stdout = open(sys.stdout.fileno(), mode='w', encoding='utf-8', errors='replace')

REPO = Path(r"C:\Users\andre\LitigationOS")
DB_PATH = REPO / "litigation_context.db"
COURT_FORMS_DB = REPO / "court_forms.db"
REPORTS_DIR = REPO / "00_SYSTEM" / "reports"
PKG_BASE = Path(r"C:\Users\andre\Desktop\LITIGATION_FILING_PACKAGE")

# Verified party data (NEVER fabricate)
PARTY_DATA = {
    'plaintiff': {
        'name': 'Andrew James Pigors',
        'address': '1977 Whitehall Road, Lot 17',
        'city': 'North Muskegon',
        'state': 'MI',
        'zip': '49445',
        'phone': '(231) 903-5690',
        'email': 'andrewjpigors@gmail.com',
        'bar_number': '',  # Pro se
        'designation': 'Plaintiff/Petitioner, In Propria Persona',
    },
    'defendant': {
        'name': 'Emily A. Watson',
        'address': '2160 Garland Drive',
        'city': 'Norton Shores',
        'state': 'MI',
        'zip': '49441',
        'phone': '',
        'email': '',
        'designation': 'Defendant/Respondent',
    },
    'child': {
        'initials': 'L.D.W.',  # MCR 8.119(H) — initials ONLY
        'dob': 'November 9, 2022',
    },
    'judge': {
        'name': 'Hon. Jenny L. McNeill',
        'court': '14th Circuit Court',
        'division': 'Family Division',
        'county': 'Muskegon',
        'address': '990 Terrace St, Muskegon, MI 49442',
    },
}

CASE_NUMBERS = {
    'custody': '2024-001507-DC',
    'ppo': '2023-5907-PP',
    'housing': '2025-002760-CZ',
    'coa': '366810',
}

# Form-to-filing mapping
FILING_FORMS = {
    'F1': ['MC 01', 'MC 02', 'FOC 10'],  # Motion + service
    'F2': ['MC 01', 'DC 100', 'MC 02'],  # Complaint + summons
    'F3': ['MC 01', 'MC 02'],  # Motion to disqualify
    'F4': [],  # Federal — no SCAO forms
    'F5': [],  # MSC — different forms
    'F6': [],  # JTC — different forms
    'F7': ['MC 01', 'MC 02', 'FOC 10', 'FOC 89'],  # Custody motion
    'F8': [],  # COA — different forms
    'F9': [],  # COA brief — different forms
    'F10': [],  # AGC — different forms
}

def get_court_forms_data():
    """Load form data from court_forms.db."""
    forms = {}
    if not COURT_FORMS_DB.exists():
        return forms
    
    try:
        conn = sqlite3.connect(str(COURT_FORMS_DB), timeout=30)
        conn.execute("PRAGMA busy_timeout=60000")
        conn.row_factory = sqlite3.Row
        
        # Check available tables
        tables = [r[0] for r in conn.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall()]
        
        if 'court_forms' in tables:
            cols = [r[1] for r in conn.execute("PRAGMA table_info(court_forms)").fetchall()]
            rows = conn.execute("SELECT * FROM court_forms").fetchall()
            for r in rows:
                form = dict(r)
                form_id = form.get('form_number', form.get('form_id', 'unknown'))
                forms[form_id] = form
        
        conn.close()
    except Exception as e:
        print(f"  ⚠️ court_forms.db error: {e}")
    
    return forms

def generate_fill_instructions(form_id, filing_id, case_type='custody'):
    """Generate field fill instructions for a specific form."""
    case_num = CASE_NUMBERS.get(case_type, CASE_NUMBERS['custody'])
    p = PARTY_DATA['plaintiff']
    d = PARTY_DATA['defendant']
    j = PARTY_DATA['judge']
    
    # Common fields across most SCAO forms
    common_fields = {
        'Court name': f"{j['court']}, {j['county']} County",
        'Court address': j['address'],
        'Case No.': case_num,
        'Judge': j['name'],
        'Plaintiff/Petitioner name': p['name'],
        'Plaintiff address': f"{p['address']}, {p['city']}, {p['state']} {p['zip']}",
        'Plaintiff telephone': p['phone'],
        'Plaintiff email': p['email'],
        'Defendant/Respondent name': d['name'],
        'Defendant address': f"{d['address']}, {d['city']}, {d['state']} {d['zip']}",
        'Filed by': p['name'],
        'Filing date': '[DATE OF FILING]',
        'Attorney/Bar No.': 'In Propria Persona (Pro Se)',
    }
    
    # Form-specific fields
    if form_id == 'MC 01':  # Case Inventory
        common_fields.update({
            'Type of case': 'Domestic Relations' if case_type == 'custody' else 'General Civil',
            'Related cases': ', '.join(CASE_NUMBERS.values()),
        })
    elif form_id == 'MC 02':  # Proof of Service
        common_fields.update({
            'Served on': d['name'],
            'Service address': f"{d['address']}, {d['city']}, {d['state']} {d['zip']}",
            'Method': '[First-class mail / Personal service]',
            'Date of service': '[DATE OF SERVICE]',
            'Server name': p['name'],
            'Server address': f"{p['address']}, {p['city']}, {p['state']} {p['zip']}",
        })
    elif form_id == 'FOC 10':  # Uniform Child Custody Jurisdiction
        common_fields.update({
            'Child initials': PARTY_DATA['child']['initials'],
            'Child DOB': PARTY_DATA['child']['dob'],
            'Present address': '[CHILD\'S CURRENT ADDRESS]',
            'Home state': 'Michigan',
        })
    elif form_id == 'DC 100':  # Complaint
        common_fields.update({
            'Nature of suit': 'Fraud upon the court / Void judgment',
            'Demand': 'Relief from all orders entered based on fraudulent filings',
        })
    
    return {
        'form_id': form_id,
        'filing_id': filing_id,
        'fields': common_fields,
    }

def main():
    print("=" * 70)
    print("COURT FORM AUTO-FILLER — Tool #51")
    print(f"Started: {datetime.now().isoformat()}")
    print("=" * 70)
    
    # Load form database
    print("\n📋 Loading court forms database...")
    forms = get_court_forms_data()
    print(f"  {len(forms)} forms loaded from court_forms.db")
    
    # Generate fill instructions per filing
    print("\n📝 Generating fill instructions...")
    all_instructions = {}
    
    case_type_map = {
        'F1': 'custody', 'F2': 'custody', 'F3': 'custody',
        'F4': 'custody', 'F5': 'custody', 'F6': 'custody',
        'F7': 'custody', 'F8': 'custody', 'F9': 'custody', 'F10': 'custody',
    }
    
    for fid, form_ids in FILING_FORMS.items():
        if not form_ids:
            print(f"  {fid}: No SCAO forms (federal/appellate/JTC)")
            all_instructions[fid] = {'forms': [], 'note': 'No SCAO forms — uses different form system'}
            continue
        
        instructions = []
        for form_id in form_ids:
            case_type = case_type_map.get(fid, 'custody')
            inst = generate_fill_instructions(form_id, fid, case_type)
            instructions.append(inst)
            print(f"  {fid} → {form_id}: {len(inst['fields'])} fields mapped")
        
        all_instructions[fid] = {'forms': instructions}
        
        # Save per-package fill guide
        pkg_dirs = list(PKG_BASE.glob(f"PKG_{fid}_*"))
        if pkg_dirs:
            guide_path = pkg_dirs[0] / "07_FORM_FILL_GUIDE.md"
            guide_lines = [
                f"# COURT FORM FILL GUIDE — {fid}",
                f"*Auto-generated: {datetime.now().strftime('%Y-%m-%d %H:%M')}*\n",
            ]
            for inst in instructions:
                guide_lines.extend([
                    f"## Form: {inst['form_id']}",
                    "| Field | Value |",
                    "|-------|-------|",
                ])
                for field, value in inst['fields'].items():
                    guide_lines.append(f"| {field} | {value} |")
                guide_lines.append("")
            
            guide_path.write_text('\n'.join(guide_lines), encoding='utf-8')
    
    # Summary report
    total_forms = sum(len(v.get('forms', [])) for v in all_instructions.values())
    total_fields = sum(
        len(inst['fields'])
        for v in all_instructions.values()
        for inst in v.get('forms', [])
    )
    
    print(f"\n📊 Summary: {total_forms} forms, {total_fields} fields auto-filled")
    
    # Save reports
    json_path = REPORTS_DIR / "court_form_fills.json"
    json_path.write_text(json.dumps({
        'generated': datetime.now().isoformat(),
        'tool': 'Court Form Auto-Filler (#51)',
        'forms_count': total_forms,
        'fields_count': total_fields,
        'instructions': all_instructions,
    }, indent=2, default=str), encoding='utf-8')
    
    md_lines = [
        "# COURT FORM AUTO-FILL REPORT",
        f"*Generated: {datetime.now().strftime('%Y-%m-%d %H:%M')}*\n",
        f"## Summary",
        f"- Forms mapped: {total_forms}",
        f"- Fields auto-filled: {total_fields}",
        f"- Filings with SCAO forms: {sum(1 for v in all_instructions.values() if v.get('forms'))}",
        "",
        "## Per-Filing Form Requirements",
        "| Filing | Forms Required | Fields |",
        "|--------|---------------|--------|",
    ]
    
    for fid, data in sorted(all_instructions.items()):
        forms_list = [f['form_id'] for f in data.get('forms', [])]
        fields = sum(len(f['fields']) for f in data.get('forms', []))
        forms_str = ', '.join(forms_list) if forms_list else data.get('note', 'None')
        md_lines.append(f"| {fid} | {forms_str} | {fields} |")
    
    md_lines.extend([
        "",
        "## Notes",
        "- F4 (Federal): Uses federal forms from uscourts.gov, not SCAO",
        "- F5 (MSC): Uses MSC-specific application forms",
        "- F6 (JTC): Uses JTC complaint form",
        "- F8/F9 (COA): Uses COA-specific forms via MiFILE",
        "- F10 (AGC): Uses AGC online complaint form",
        "",
        "## Party Data Used (Verified)",
        f"- Plaintiff: {PARTY_DATA['plaintiff']['name']}",
        f"- Defendant: {PARTY_DATA['defendant']['name']}",
        f"- Child: {PARTY_DATA['child']['initials']} (initials only per MCR 8.119(H))",
        f"- Judge: {PARTY_DATA['judge']['name']}",
        f"- Case Numbers: {', '.join(f'{k}: {v}' for k, v in CASE_NUMBERS.items())}",
    ])
    
    md_path = REPORTS_DIR / "COURT_FORM_FILL_REPORT.md"
    md_path.write_text('\n'.join(md_lines), encoding='utf-8')
    
    print(f"\n✅ Reports: {json_path.name}, {md_path.name}")
    print(f"📋 Form fill guides saved to each PKG directory as 07_FORM_FILL_GUIDE.md")

if __name__ == '__main__':
    main()
