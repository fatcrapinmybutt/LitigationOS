#!/usr/bin/env python3
"""
Tool #47 — Master Strategy Updater
====================================
Generates a comprehensive, up-to-date master strategy document synthesizing:
- All 10 filing statuses and compliance levels
- E-filing instructions per court
- Priority filing order (from Tool #29)
- Current deadlines
- Evidence arsenal strength
- Remaining action items for Andrew
"""
import sys, json, os, sqlite3
from pathlib import Path
from datetime import datetime

sys.stdout = open(sys.stdout.fileno(), mode='w', encoding='utf-8', errors='replace')

REPO = Path(r"C:\Users\andre\LitigationOS")
DB_PATH = REPO / "litigation_context.db"
REPORTS_DIR = REPO / "00_SYSTEM" / "reports"
PKG_BASE = Path(r"C:\Users\andre\Desktop\LITIGATION_FILING_PACKAGE")

FILING_DATA = {
    'F1': {'name': 'Emergency Motion — Parenting Time', 'court': '14th Circuit Court', 'lane': 'A', 'type': 'motion', 'limit': 20},
    'F2': {'name': 'Fraud Upon the Court Complaint', 'court': '14th Circuit Court', 'lane': 'A', 'type': 'complaint', 'limit': None},
    'F3': {'name': 'Motion to Disqualify Judge McNeill (MCR 2.003)', 'court': '14th Circuit Court', 'lane': 'E', 'type': 'motion', 'limit': 20},
    'F4': {'name': '42 USC §1983 Federal Civil Rights Complaint', 'court': 'USDC Western District MI', 'lane': 'A', 'type': 'complaint', 'limit': None},
    'F5': {'name': 'MSC Application for Leave to Appeal', 'court': 'Michigan Supreme Court', 'lane': 'F', 'type': 'petition', 'limit': 50},
    'F6': {'name': 'JTC Complaint — Judicial Misconduct', 'court': 'Judicial Tenure Commission', 'lane': 'E', 'type': 'complaint', 'limit': None},
    'F7': {'name': 'Motion to Modify Custody and Parenting Time', 'court': '14th Circuit Court', 'lane': 'A', 'type': 'motion', 'limit': 20},
    'F8': {'name': 'COA Complaint for Superintending Control', 'court': 'Michigan Court of Appeals', 'lane': 'F', 'type': 'complaint', 'limit': 50},
    'F9': {'name': 'COA Brief on Appeal (366810)', 'court': 'Michigan Court of Appeals', 'lane': 'F', 'type': 'brief', 'limit': 50},
    'F10': {'name': 'Attorney Grievance Commission Complaint', 'court': 'AGC', 'lane': 'E', 'type': 'complaint', 'limit': None},
}

OPTIMAL_ORDER = ['F3', 'F4', 'F6', 'F5', 'F9', 'F8', 'F7', 'F10', 'F1', 'F2']

EFILING_INFO = {
    '14th Circuit Court': {'system': 'MiFILE', 'url': 'https://mifile.courts.michigan.gov', 'fee': '$20 motion / $175 complaint', 'filing_ids': ['F1','F2','F3','F7']},
    'USDC Western District MI': {'system': 'CM/ECF via PACER', 'url': 'https://ecf.miwd.uscourts.gov', 'fee': '$405 complaint', 'filing_ids': ['F4']},
    'Michigan Supreme Court': {'system': 'MiFILE', 'url': 'https://mifile.courts.michigan.gov', 'fee': '$375 application', 'filing_ids': ['F5']},
    'Michigan Court of Appeals': {'system': 'MiFILE', 'url': 'https://mifile.courts.michigan.gov', 'fee': '$375 appeal', 'filing_ids': ['F8','F9']},
    'Judicial Tenure Commission': {'system': 'Mail/email', 'url': 'https://jtc.courts.mi.gov', 'fee': 'Free', 'filing_ids': ['F6']},
    'AGC': {'system': 'Online form', 'url': 'https://www.agcmi.com', 'fee': 'Free', 'filing_ids': ['F10']},
}

def get_pkg_dir(fid):
    """Find the package directory for a filing ID."""
    matches = list(PKG_BASE.glob(f"PKG_{fid}_*"))
    return matches[0] if matches else None

def count_words(filepath):
    """Count words in a file."""
    try:
        text = filepath.read_text(encoding='utf-8', errors='replace')
        return len(text.split())
    except:
        return 0

def get_filing_status():
    """Get current status of all filings."""
    statuses = []
    for fid, info in FILING_DATA.items():
        pkg_dir = get_pkg_dir(fid)
        if not pkg_dir:
            statuses.append({**info, 'id': fid, 'status': 'MISSING', 'words': 0, 'pages': 0})
            continue
        
        main_file = pkg_dir / "01_MAIN_FILING.md"
        brief_file = pkg_dir / "01B_BRIEF_IN_SUPPORT.md"
        affidavit = pkg_dir / "02_AFFIDAVIT.md"
        
        words = count_words(main_file) if main_file.exists() else 0
        brief_words = count_words(brief_file) if brief_file.exists() else 0
        aff_words = count_words(affidavit) if affidavit.exists() else 0
        
        pages = round(words / 300, 1)
        brief_pages = round(brief_words / 300, 1) if brief_words else 0
        
        limit = info['limit']
        if limit:
            compliant = pages <= limit
            if brief_pages > 0:
                compliant = compliant and brief_pages <= limit
        else:
            compliant = True
        
        files_present = [f.name for f in pkg_dir.iterdir() if f.suffix == '.md' and not f.name.startswith('.')]
        
        statuses.append({
            **info, 'id': fid,
            'status': '✅ COMPLIANT' if compliant else '⚠️ OVER LIMIT',
            'words': words, 'pages': pages,
            'brief_words': brief_words, 'brief_pages': brief_pages,
            'aff_words': aff_words,
            'files': files_present,
            'compliant': compliant,
        })
    
    return statuses

def get_db_stats():
    """Get key database statistics."""
    stats = {}
    try:
        conn = sqlite3.connect(str(DB_PATH), timeout=30)
        conn.execute("PRAGMA busy_timeout=60000")
        conn.execute("PRAGMA journal_mode=WAL")
        
        row = conn.execute("""
            SELECT
                (SELECT COUNT(*) FROM evidence_quotes) as eq,
                (SELECT COUNT(*) FROM judicial_violations) as jv,
                (SELECT COUNT(*) FROM claims) as cl,
                (SELECT COUNT(*) FROM detected_contradictions) as dc,
                (SELECT COUNT(*) FROM watson_perjury_compilation) as wp
        """).fetchone()
        
        stats = {
            'evidence_quotes': row[0],
            'judicial_violations': row[1],
            'claims': row[2],
            'contradictions': row[3],
            'perjury_items': row[4],
        }
        conn.close()
    except Exception as e:
        stats['error'] = str(e)
    
    return stats

def main():
    print("=" * 70)
    print("MASTER STRATEGY UPDATER — Tool #47")
    print(f"Generated: {datetime.now().isoformat()}")
    print("=" * 70)
    
    # Gather data
    filings = get_filing_status()
    db_stats = get_db_stats()
    
    compliant_count = sum(1 for f in filings if f.get('compliant', False))
    print(f"\n📊 Filing compliance: {compliant_count}/10")
    
    # Build master strategy document
    lines = [
        "# MASTER LITIGATION STRATEGY — Pigors v. Watson",
        f"*Auto-generated: {datetime.now().strftime('%Y-%m-%d %H:%M')}*",
        "",
        "## 🎯 Strategic Objective",
        "Bypass the compromised Muskegon 14th Circuit Court through a multi-front",
        "legal offensive combining federal civil rights claims, appellate relief,",
        "judicial misconduct complaints, and fraud-upon-the-court actions.",
        "",
        "### Core Legal Theory: Fruit of the Poisonous Tree",
        "Emily Watson's initial fraudulent filings (fabricated PPO evidence, perjury",
        "in custody proceedings) poisoned ALL subsequent orders. Under MCR 2.612(C)(1)(d),",
        "void judgments have NO time limit for relief. Under MCR 2.612(C)(3), independent",
        "action for fraud upon the court has NO time bar.",
        "",
        "---",
        "",
        f"## 📋 Filing Status ({compliant_count}/10 compliant)",
        "",
        "### Optimal Filing Order (from Priority Optimizer)",
        "| Priority | Filing | Court | Type | Status |",
        "|----------|--------|-------|------|--------|",
    ]
    
    for i, fid in enumerate(OPTIMAL_ORDER, 1):
        f = next((x for x in filings if x['id'] == fid), None)
        if f:
            brief_note = f" + Brief {f['brief_pages']}p" if f.get('brief_pages') else ""
            lines.append(f"| {i} | {fid}: {f['name'][:50]} | {f['court'][:20]} | {f['type']} | {f['status']} ({f['pages']}p{brief_note}) |")
    
    lines.extend([
        "",
        "### Detailed Filing Breakdown",
    ])
    
    for f in filings:
        lines.extend([
            f"",
            f"#### {f['id']}: {f['name']}",
            f"- **Court:** {f['court']}",
            f"- **Lane:** {f['lane']}",
            f"- **Type:** {f['type']}",
            f"- **Main:** {f['words']:,} words ({f['pages']}p)",
        ])
        if f.get('brief_words'):
            lines.append(f"- **Brief:** {f['brief_words']:,} words ({f['brief_pages']}p)")
        if f.get('aff_words'):
            lines.append(f"- **Affidavit:** {f['aff_words']:,} words")
        limit_str = f"{f['limit']}p" if f['limit'] else "None (exempt)"
        lines.append(f"- **Page Limit:** {limit_str}")
        lines.append(f"- **Status:** {f['status']}")
    
    # E-Filing Instructions
    lines.extend([
        "",
        "---",
        "",
        "## 📡 E-Filing Instructions",
        "",
        "| Court | System | URL | Fee | Filings |",
        "|-------|--------|-----|-----|---------|",
    ])
    for court, info in EFILING_INFO.items():
        fids = ', '.join(info['filing_ids'])
        lines.append(f"| {court} | {info['system']} | {info['url']} | {info['fee']} | {fids} |")
    
    # Evidence Arsenal
    lines.extend([
        "",
        "---",
        "",
        "## 🛡️ Evidence Arsenal",
        "",
        "| Category | Count |",
        "|----------|-------|",
    ])
    for key, val in db_stats.items():
        if key != 'error':
            lines.append(f"| {key.replace('_', ' ').title()} | {val:,} |")
    
    # Action Items for Andrew
    lines.extend([
        "",
        "---",
        "",
        "## ⚡ ANDREW'S ACTION ITEMS (Required Before Filing)",
        "",
        "### IMMEDIATE (This Week)",
        "1. ☐ **Review all 10 affidavits** — they're sworn under oath, must be accurate",
        "2. ☐ **Register for MiFILE** at https://mifile.courts.michigan.gov/register",
        "3. ☐ **Register for PACER/CM-ECF** at https://pacer.uscourts.gov (for F4 federal case)",
        "4. ☐ **Complete IFP financial affidavit** (needed for F4 federal + F5 MSC)",
        "",
        "### BEFORE EACH FILING",
        "5. ☐ **Sign and notarize affidavit** for the filing being submitted",
        "6. ☐ **Complete certificate of service** with actual service date/method",
        "7. ☐ **Print/mail paper copies** to required parties per court rules",
        "",
        "### INFORMATION NEEDED",
        "8. ☐ **Ronald T. Berry's address** (for service of F4, F6, F10)",
        "9. ☐ **Shady Oaks registered agent address** (for F2 housing complaint)",
        "10. ☐ **Cricklewood Management registered agent** (for F2 housing complaint)",
        "",
        "### STRATEGIC DECISIONS",
        "11. ☐ **Confirm filing order** — recommended: F3→F4→F6→F5→F9→F8→F7→F10→F1→F2",
        "12. ☐ **Decision on IFP vs. fee payment** per court",
        "13. ☐ **Decision on requesting TRO** with F4 federal complaint",
        "",
        "---",
        "",
        "## 🔑 Key Authorities by Filing",
        "",
        "| Filing | Primary Authorities |",
        "|--------|-------------------|",
        "| F1 | MCL 722.27a(3), MCR 3.207(A), Shade v Wright 291 Mich App 17 |",
        "| F2 | MCR 2.612(C)(1)(c)(d), MCL 750.423-424, Fraud upon the court |",
        "| F3 | MCR 2.003(C)(1), Crampton v Dept of State 395 Mich 347, Canon 2 |",
        "| F4 | 42 USC §1983, Catz v Chalker 142 F.3d 279, Dennis v Sparks 449 US 24 |",
        "| F5 | MCR 7.306, Const 1963 Art 6 §4, Administrative control |",
        "| F6 | Const 1963 Art 6 §30, JTC Rules 1-8, Canon violations |",
        "| F7 | MCL 722.23, MCR 3.210, Vodvarka v Grasmeyer 259 Mich App 499 |",
        "| F8 | MCR 7.206(B)(1), Superintending control, Mandamus |",
        "| F9 | MCR 7.212, COA 366810, Abuse of discretion standard |",
        "| F10 | MRPC 3.1, 3.3, 3.4, 8.4, Barnes P55406 withdrawal |",
        "",
        "---",
        "",
        "*Strategy document auto-generated*",
    ])
    lines.append(f"*From {len(filings)} filings and {sum(db_stats.get(k,0) for k in db_stats if k != 'error'):,} DB items*")
    
    # Write report
    md_path = REPORTS_DIR / "MASTER_STRATEGY.md"
    md_path.write_text('\n'.join(lines), encoding='utf-8')
    
    json_path = REPORTS_DIR / "master_strategy.json"
    json_path.write_text(json.dumps({
        'generated': datetime.now().isoformat(),
        'filings': filings,
        'db_stats': db_stats,
        'efiling': EFILING_INFO,
        'optimal_order': OPTIMAL_ORDER,
        'compliance': f'{compliant_count}/10',
    }, indent=2, default=str), encoding='utf-8')
    
    print(f"\n✅ Master strategy: {md_path}")
    print(f"✅ Strategy JSON: {json_path}")
    print(f"📊 {compliant_count}/10 filings compliant")
    print(f"🛡️ Evidence arsenal: {sum(db_stats.get(k,0) for k in db_stats if k != 'error'):,} items")

if __name__ == '__main__':
    main()
