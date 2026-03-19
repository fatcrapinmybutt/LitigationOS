#!/usr/bin/env python3
"""
Tool #58 — Convergence Dashboard
===================================
Final status report across ALL dimensions:
- Filing compliance (page limits, formatting)
- Sanctions risk score
- Evidence arsenal size
- Tool inventory (all 58 tools)
- Todo completion status
- PDF generation status
- Hearing kit status
- Court form fill status
- Overall readiness assessment

This is the capstone tool — the "GO/NO-GO for court" dashboard.
"""
import sys, json, os, sqlite3
from pathlib import Path
from datetime import datetime

sys.stdout = open(sys.stdout.fileno(), mode='w', encoding='utf-8', errors='replace')

REPO = Path(r"C:\Users\andre\LitigationOS")
DB_PATH = REPO / "litigation_context.db"
REPORTS_DIR = REPO / "00_SYSTEM" / "reports"
TOOLS_DIR = REPO / "00_SYSTEM" / "tools"
PKG_BASE = Path(r"C:\Users\andre\Desktop\LITIGATION_FILING_PACKAGE")

FILINGS = ['F1','F2','F3','F4','F5','F6','F7','F8','F9','F10']

def count_tools():
    """Count all tools in the tools directory."""
    tools = list(TOOLS_DIR.glob("*.py"))
    return len(tools), [t.stem for t in sorted(tools)]

def check_filing_compliance():
    """Check all filings for page limit compliance."""
    results = {}
    limits = {'F1':20,'F2':None,'F3':20,'F4':None,'F5':50,'F6':None,'F7':20,'F8':50,'F9':50,'F10':None}
    
    for fid in FILINGS:
        pkg_dirs = list(PKG_BASE.glob(f"PKG_{fid}_*"))
        if not pkg_dirs:
            results[fid] = {'status': 'MISSING', 'pages': 0}
            continue
        
        pkg = pkg_dirs[0]
        main = pkg / "01_MAIN_FILING.md"
        brief = pkg / "01B_BRIEF_IN_SUPPORT.md"
        
        main_words = len(main.read_text(encoding='utf-8', errors='replace').split()) if main.exists() else 0
        brief_words = len(brief.read_text(encoding='utf-8', errors='replace').split()) if brief.exists() else 0
        
        main_pages = round(main_words / 300, 1)
        brief_pages = round(brief_words / 300, 1) if brief_words else 0
        limit = limits.get(fid)
        
        compliant = True
        if limit:
            if main_pages > limit:
                compliant = False
            if brief_pages > 0 and brief_pages > limit:
                compliant = False
        
        # Check what files exist
        files = [f.name for f in pkg.iterdir() if f.suffix == '.md' and '.bak.' not in f.name]
        
        results[fid] = {
            'status': '✅' if compliant else '⚠️',
            'main_pages': main_pages,
            'brief_pages': brief_pages,
            'limit': limit,
            'files': len(files),
            'has_affidavit': (pkg / '02_AFFIDAVIT.md').exists(),
            'has_hearing_kit': (pkg / '08_HEARING_PREP_KIT.md').exists(),
            'has_form_guide': (pkg / '07_FORM_FILL_GUIDE.md').exists(),
        }
    
    return results

def check_pdfs():
    """Check PDF generation status."""
    pdf_dir = PKG_BASE / "PDF_OUTPUT"
    if not pdf_dir.exists():
        return 0, {}
    
    total = 0
    per_filing = {}
    for fid in FILINGS:
        fid_dir = pdf_dir / fid
        if fid_dir.exists():
            pdfs = list(fid_dir.glob("*.pdf"))
            per_filing[fid] = len(pdfs)
            total += len(pdfs)
        else:
            per_filing[fid] = 0
    
    return total, per_filing

def get_evidence_stats():
    """Get evidence arsenal statistics."""
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
                (SELECT COUNT(*) FROM watson_perjury_compilation) as wp,
                (SELECT COUNT(*) FROM adversary_assertions) as aa
        """).fetchone()
        
        stats = {
            'evidence_quotes': row[0],
            'judicial_violations': row[1],
            'claims': row[2],
            'contradictions': row[3],
            'perjury_items': row[4],
            'adversary_assertions': row[5],
        }
        
        # DB size
        db_size = os.path.getsize(str(DB_PATH))
        stats['db_size_gb'] = round(db_size / (1024**3), 1)
        
        # Table count
        tables = conn.execute("SELECT COUNT(*) FROM sqlite_master WHERE type='table'").fetchone()[0]
        stats['table_count'] = tables
        
        conn.close()
    except Exception as e:
        stats['error'] = str(e)
    
    return stats

def load_sanctions_score():
    """Load the most recent sanctions score."""
    json_path = REPORTS_DIR / "sanctions_risk.json"
    if json_path.exists():
        try:
            data = json.loads(json_path.read_text(encoding='utf-8'))
            return data.get('overall_score', '?'), data.get('overall_level', '?')
        except:
            pass
    return '?', '?'

def main():
    print("=" * 70)
    print("🏁 CONVERGENCE DASHBOARD — Tool #58")
    print(f"   Final Status Report")
    print(f"   Generated: {datetime.now().isoformat()}")
    print("=" * 70)
    
    # Gather all data
    tool_count, tool_names = count_tools()
    filings = check_filing_compliance()
    total_pdfs, pdf_counts = check_pdfs()
    evidence = get_evidence_stats()
    sanctions_score, sanctions_level = load_sanctions_score()
    
    compliant = sum(1 for f in filings.values() if f['status'] == '✅')
    with_affidavit = sum(1 for f in filings.values() if f.get('has_affidavit'))
    with_hearing = sum(1 for f in filings.values() if f.get('has_hearing_kit'))
    with_forms = sum(1 for f in filings.values() if f.get('has_form_guide'))
    
    total_evidence = sum(v for k, v in evidence.items() if isinstance(v, int) and k != 'table_count')
    
    # Print dashboard
    print(f"\n{'='*50}")
    print(f"  📋 FILING COMPLIANCE:  {compliant}/10 compliant")
    print(f"  📄 AFFIDAVITS:         {with_affidavit}/10 rebuilt")
    print(f"  📑 PDFs GENERATED:     {total_pdfs} court-ready")
    print(f"  ⚖️  HEARING KITS:      {with_hearing}/10")
    print(f"  📝 FORM GUIDES:        {with_forms}/10")
    print(f"  ⚠️  SANCTIONS SCORE:   {sanctions_score} ({sanctions_level})")
    print(f"  🛡️  EVIDENCE ARSENAL:  {total_evidence:,} items")
    print(f"  🔧 TOOLS BUILT:        {tool_count}")
    print(f"  💾 DATABASE:           {evidence.get('db_size_gb', '?')} GB, {evidence.get('table_count', '?')} tables")
    print(f"{'='*50}")
    
    # Readiness assessment
    go_criteria = [
        ('Filing compliance', compliant == 10),
        ('Affidavits present', with_affidavit >= 10),
        ('PDFs generated', total_pdfs >= 50),
        ('Sanctions < 200', isinstance(sanctions_score, (int, float)) and sanctions_score < 200),
        ('Evidence > 10K', total_evidence > 10000),
    ]
    
    passed = sum(1 for _, v in go_criteria if v)
    
    print(f"\n🏁 GO/NO-GO ASSESSMENT: {passed}/{len(go_criteria)} criteria met")
    for name, ok in go_criteria:
        print(f"  {'✅' if ok else '❌'} {name}")
    
    overall = "🟢 GO — Ready for court filing" if passed >= 4 else "🟡 CONDITIONAL GO — Review remaining items" if passed >= 3 else "🔴 NO-GO — Address critical gaps"
    print(f"\n  >>> {overall} <<<")
    
    # Generate report
    lines = [
        "# 🏁 CONVERGENCE DASHBOARD",
        f"*Generated: {datetime.now().strftime('%Y-%m-%d %H:%M')}*",
        "",
        f"## Overall Assessment: {overall}",
        "",
        "---",
        "",
        "## Filing Status",
        "| Filing | Pages | Limit | Brief | Status | Affidavit | Hearing Kit | Form Guide |",
        "|--------|-------|-------|-------|--------|-----------|-------------|------------|",
    ]
    
    for fid in FILINGS:
        f = filings.get(fid, {})
        limit_str = str(f.get('limit', 'None')) if f.get('limit') else 'None'
        brief_str = f"{f.get('brief_pages', 0)}p" if f.get('brief_pages') else '—'
        lines.append(f"| {fid} | {f.get('main_pages', 0)}p | {limit_str} | {brief_str} | {f.get('status', '?')} | {'✅' if f.get('has_affidavit') else '❌'} | {'✅' if f.get('has_hearing_kit') else '—'} | {'✅' if f.get('has_form_guide') else '—'} |")
    
    lines.extend([
        "",
        "## Metrics",
        f"| Metric | Value |",
        f"|--------|-------|",
        f"| Filing compliance | {compliant}/10 |",
        f"| PDFs generated | {total_pdfs} |",
        f"| Sanctions score | {sanctions_score} ({sanctions_level}) |",
        f"| Evidence arsenal | {total_evidence:,} items |",
        f"| Tools built | {tool_count} |",
        f"| DB size | {evidence.get('db_size_gb', '?')} GB |",
        f"| DB tables | {evidence.get('table_count', '?')} |",
    ])
    
    lines.extend([
        "",
        "## Evidence Arsenal Breakdown",
        "| Category | Count |",
        "|----------|-------|",
    ])
    for key, val in evidence.items():
        if isinstance(val, int) and key != 'table_count':
            lines.append(f"| {key.replace('_', ' ').title()} | {val:,} |")
    
    lines.extend([
        "",
        "## GO/NO-GO Criteria",
        "| Criterion | Status |",
        "|-----------|--------|",
    ])
    for name, ok in go_criteria:
        lines.append(f"| {name} | {'✅ PASS' if ok else '❌ FAIL'} |")
    
    lines.extend([
        "",
        f"## Tool Inventory ({tool_count} tools)",
    ])
    for i, name in enumerate(tool_names, 1):
        lines.append(f"{i}. `{name}`")
    
    lines.extend([
        "",
        "---",
        f"*Dashboard generated by Tool #58 — Convergence Dashboard*",
        f"*{tool_count} tools, {total_pdfs} PDFs, {total_evidence:,} evidence items*",
    ])
    
    md_path = REPORTS_DIR / "CONVERGENCE_DASHBOARD.md"
    md_path.write_text('\n'.join(lines), encoding='utf-8')
    
    json_path = REPORTS_DIR / "convergence_dashboard.json"
    json_path.write_text(json.dumps({
        'generated': datetime.now().isoformat(),
        'tool': 'Convergence Dashboard (#58)',
        'assessment': overall,
        'criteria_passed': passed,
        'criteria_total': len(go_criteria),
        'filings': filings,
        'pdfs': {'total': total_pdfs, 'per_filing': pdf_counts},
        'evidence': evidence,
        'sanctions': {'score': sanctions_score, 'level': sanctions_level},
        'tools': {'count': tool_count, 'names': tool_names},
    }, indent=2, default=str), encoding='utf-8')
    
    print(f"\n✅ Dashboard: {md_path.name}")
    print(f"✅ JSON: {json_path.name}")

if __name__ == '__main__':
    main()
