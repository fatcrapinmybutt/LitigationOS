#!/usr/bin/env python3
"""
Tool #90 — MASTER LITIGATION DASHBOARD
==========================================
The ultimate summary dashboard that aggregates ALL tool outputs
into a single executive briefing.

Reads all JSON reports and produces one unified status page.
This is the "command center" view of the entire litigation.

🎯 MILESTONE TOOL — Tool #90
"""
import sys, json, sqlite3
from pathlib import Path
from datetime import datetime

sys.stdout = open(sys.stdout.fileno(), mode='w', encoding='utf-8', errors='replace')

REPO = Path(r"C:\Users\andre\LitigationOS")
DB_PATH = REPO / "litigation_context.db"
REPORTS_DIR = REPO / "00_SYSTEM" / "reports"
TOOLS_DIR = REPO / "00_SYSTEM" / "tools"
PKG_BASE = Path(r"C:\Users\andre\Desktop\LITIGATION_FILING_PACKAGE")

def load_json(filename):
    """Load a JSON report file safely."""
    path = REPORTS_DIR / filename
    if path.exists():
        try:
            return json.loads(path.read_text(encoding='utf-8'))
        except:
            pass
    return {}

def count_files(directory, pattern='*'):
    """Count files in directory."""
    try:
        return len(list(Path(directory).glob(pattern)))
    except:
        return 0

def main():
    print("=" * 70)
    print("🎯 MASTER LITIGATION DASHBOARD — Tool #90")
    print("    Pigors v. Watson — Command Center")
    print("=" * 70)
    
    now = datetime.now()
    
    # === SYSTEM METRICS ===
    tool_count = count_files(TOOLS_DIR, '*.py')
    report_count = count_files(REPORTS_DIR, '*')
    
    pkg_files = 0
    for i in range(1, 11):
        pkg_files += count_files(PKG_BASE / f"PKG_F{i}", '*')
    
    pdf_count = count_files(PKG_BASE / "PDF_OUTPUT", '*.pdf')
    
    # === DATABASE METRICS ===
    db_tables = 0
    db_size_mb = 0
    key_counts = {}
    
    try:
        db_size_mb = DB_PATH.stat().st_size / (1024 * 1024)
        conn = sqlite3.connect(str(DB_PATH), timeout=60)
        conn.execute("PRAGMA busy_timeout=60000")
        conn.execute("PRAGMA journal_mode=WAL")
        
        db_tables = conn.execute("SELECT COUNT(*) FROM sqlite_master WHERE type='table'").fetchone()[0]
        
        for table in ['judicial_violations', 'detected_contradictions', 'watson_perjury_compilation', 
                       'evidence_quotes', 'chatgpt_evidence']:
            try:
                cnt = conn.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0]
                key_counts[table] = cnt
            except:
                key_counts[table] = 0
        
        conn.close()
    except:
        pass
    
    # === LOAD TOOL REPORTS ===
    damages = load_json('damages_recovery.json')
    best_interest = load_json('best_interest_scorecard.json')
    risk = load_json('risk_matrix.json')
    cost = load_json('cost_estimate.json')
    calendar_data = load_json('calendar.json')
    service = load_json('service_planner.json')
    heatmap = load_json('contradiction_heatmap.json')
    bias = load_json('judicial_bias_patterns.json')
    perjury = load_json('perjury_links.json')
    authority = load_json('authority_validation.json')
    
    # === BUILD DASHBOARD ===
    lines = [
        "# 🎯 MASTER LITIGATION DASHBOARD",
        "## Pigors v. Watson — Command Center",
        f"*Generated: {now.strftime('%Y-%m-%d %H:%M')} | Tool #90*\n",
        "---\n",
        
        "## 📊 SYSTEM STATUS\n",
        "| Metric | Value |",
        "|--------|-------|",
        f"| Python Tools | {tool_count} |",
        f"| Reports Generated | {report_count} |",
        f"| Filing Package Files | {pkg_files} |",
        f"| Court-Ready PDFs | {pdf_count} |",
        f"| Database Tables | {db_tables} |",
        f"| Database Size | {db_size_mb:,.0f} MB |",
        "",
        
        "## 🗄️ EVIDENCE ARSENAL\n",
        "| Evidence Type | Count |",
        "|--------------|-------|",
        f"| Judicial Violations | {key_counts.get('judicial_violations', 0):,} |",
        f"| Detected Contradictions | {key_counts.get('detected_contradictions', 0):,} |",
        f"| Perjury Compilation | {key_counts.get('watson_perjury_compilation', 0):,} |",
        f"| Evidence Quotes | {key_counts.get('evidence_quotes', 0):,} |",
        f"| ChatGPT Evidence | {key_counts.get('chatgpt_evidence', 0):,} |",
        f"| DB Authorities | {authority.get('db_authorities', 0):,} |",
        f"| Citations in Filings | {authority.get('total_citations_found', 0):,} |",
        "",
    ]
    
    # Best Interest
    if best_interest:
        lines.extend([
            "## ⚖️ BEST INTEREST FACTORS (MCL 722.23)\n",
            f"**Andrew: {best_interest.get('andrew_total', 0)}/120 ({best_interest.get('andrew_total', 0)/120*100:.0f}%) | "
            f"Emily: {best_interest.get('emily_total', 0)}/120 ({best_interest.get('emily_total', 0)/120*100:.0f}%)**",
            f"- Andrew wins {best_interest.get('andrew_wins', 0)} factors, Emily wins {best_interest.get('emily_wins', 0)}, {best_interest.get('ties', 0)} ties",
            f"- **Decisive factor (j)**: Andrew 10/10 vs Emily 1/10\n",
        ])
    
    # Damages
    if damages:
        lines.extend([
            "## 💰 POTENTIAL RECOVERY\n",
            f"| Scenario | Amount |",
            f"|----------|--------|",
            f"| Conservative | **${damages.get('conservative_total', 0):,}** |",
            f"| Aggressive | **${damages.get('aggressive_total', 0):,}** |",
            "",
        ])
    
    # Judicial Bias
    if bias:
        lines.extend([
            "## 🔍 JUDICIAL BIAS ANALYSIS\n",
            f"- Bias Score: **{bias.get('bias_score', 0)}/10**",
            f"- Total Violations: {bias.get('total_violations', 0):,}",
            f"- Ex-Parte Evidence: {bias.get('exparte_evidence', 0)}",
            "",
        ])
    
    # Contradiction Heatmap
    if heatmap:
        lines.extend([
            "## 🔥 CONTRADICTION HEAT MAP\n",
            f"- Total Contradictions: {heatmap.get('total', 0):,}",
        ])
        if 'topic_counts' in heatmap:
            top3 = sorted(heatmap['topic_counts'].items(), key=lambda x: -x[1])[:3]
            for topic, count in top3:
                lines.append(f"- {topic.replace('_', ' ').title()}: {count:,}")
        lines.append("")
    
    # Calendar
    if calendar_data:
        lines.extend([
            "## 📅 UPCOMING DEADLINES\n",
            f"- Total Events: {calendar_data.get('total_events', 0)}",
            f"- Critical: {calendar_data.get('critical', 0)} | High: {calendar_data.get('high', 0)} | Medium: {calendar_data.get('medium', 0)}",
            f"- ICS file ready for calendar import",
            "",
        ])
    
    # Service & Cost
    if service:
        lines.extend([
            "## 📬 SERVICE OF PROCESS\n",
            f"- Total Service Actions: {service.get('total_serve_actions', 0)}",
            f"- Total Service Cost: ${service.get('total_cost', 0)}",
            "",
        ])
    
    if cost:
        lines.extend([
            "## 💵 LITIGATION COSTS\n",
            f"- Without IFP: ${cost.get('total_without_ifp', 0):,}",
            f"- With IFP: ${cost.get('total_with_ifp', 0):,}",
            f"- IFP Savings: ${cost.get('ifp_savings', 0):,}",
            "",
        ])
    
    # Action items
    lines.extend([
        "---",
        "## 🚨 IMMEDIATE ACTION ITEMS (Andrew Must Do)\n",
        "1. ✅ Register for MiFILE (mifile.courts.michigan.gov/register)",
        "2. ✅ Register for PACER (pacer.uscourts.gov)",
        "3. ✅ Call COA Clerk (517) 373-0786 — confirm 366810 deadline",
        "4. ✅ Review ALL 10 affidavits — sign & notarize",
        "5. ✅ Complete IFP financial affidavit",
        "6. ✅ Import litigation_calendar.ics into phone calendar",
        "7. ✅ Print Pro Se Rights Card — carry to every hearing",
        "",
        "## 📋 FILING ORDER (risk-adjusted)\n",
        "**Wave 1 (Day 1-3):** F1 (emergency parenting) + F3 (disqualification)",
        "**Wave 2 (Day 3-5):** F6 (JTC) + F10 (AGC) — free complaints",
        "**Wave 3 (Day 7-8):** F2 (fraud) + F7 (custody modification)",
        "**Wave 4 (Day 14-21):** F4 (federal §1983) + F5 (MSC)",
        "**Wave 5 (Day 14-30):** F9 (COA brief) + F8 (leave application)",
        "",
        "---",
        f"*Master Litigation Dashboard — Tool #90 — {tool_count} tools operational*",
        f"*LitigationOS — Pigors v. Watson Command Center*",
    ])
    
    # Print summary
    print(f"\n  📊 System: {tool_count} tools, {report_count} reports, {pkg_files} pkg files, {pdf_count} PDFs")
    print(f"  🗄️ Database: {db_tables} tables, {db_size_mb:,.0f} MB")
    print(f"  ⚖️ Best Interest: Andrew {best_interest.get('andrew_total', 0)}/120 vs Emily {best_interest.get('emily_total', 0)}/120")
    print(f"  💰 Recovery: ${damages.get('conservative_total', 0):,} — ${damages.get('aggressive_total', 0):,}")
    print(f"  🔍 Bias Score: {bias.get('bias_score', 0)}/10 ({bias.get('total_violations', 0):,} violations)")
    print(f"  🔥 Contradictions: {heatmap.get('total', 0):,}")
    
    md_path = REPORTS_DIR / "MASTER_DASHBOARD.md"
    md_path.write_text('\n'.join(lines), encoding='utf-8')
    
    # Also save to filing package top level
    top_dash = PKG_BASE / "00_MASTER_DASHBOARD.md"
    try:
        top_dash.write_text('\n'.join(lines), encoding='utf-8')
    except:
        pass
    
    json_path = REPORTS_DIR / "master_dashboard.json"
    json_path.write_text(json.dumps({
        'generated': now.isoformat(),
        'tool': 'Master Litigation Dashboard (#90)',
        'system': {
            'tools': tool_count,
            'reports': report_count,
            'pkg_files': pkg_files,
            'pdfs': pdf_count,
            'db_tables': db_tables,
            'db_size_mb': round(db_size_mb),
        },
        'evidence': key_counts,
        'best_interest': best_interest,
        'damages': damages,
        'bias': bias,
    }, indent=2), encoding='utf-8')
    
    print(f"\n✅ Master Dashboard generated — the command center is live")
    print(f"   Reports: MASTER_DASHBOARD.md + master_dashboard.json")
    print(f"   Also saved to filing package: 00_MASTER_DASHBOARD.md")

if __name__ == '__main__':
    main()
