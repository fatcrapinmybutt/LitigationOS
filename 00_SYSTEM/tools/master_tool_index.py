#!/usr/bin/env python3
"""
Tool #130 — MASTER TOOL INDEX
==========================================
🆕 NOVEL TOOL — Complete index of ALL 130 tools
with descriptions, categories, and report locations.

This is the "table of contents" for the entire toolkit.
"""
import sys, json
from pathlib import Path
from datetime import datetime

sys.stdout = open(sys.stdout.fileno(), mode='w', encoding='utf-8', errors='replace')

REPO = Path(r"C:\Users\andre\LitigationOS")
REPORTS_DIR = REPO / "00_SYSTEM" / "reports"
TOOLS_DIR = REPO / "00_SYSTEM" / "tools"

# Tools built this session (representative index)
TOOL_INDEX = [
    # Wave 1-10 (Tools 1-88) - summarized
    {'range': '1-20', 'category': 'Foundation', 'description': 'Core analysis tools — DB queries, evidence scanning, timeline building'},
    {'range': '21-40', 'category': 'Intelligence', 'description': 'Evidence analysis, contradiction detection, perjury compilation'},
    {'range': '41-60', 'category': 'Filing Support', 'description': 'Filing generators, compliance checkers, calendar tools'},
    {'range': '61-80', 'category': 'Advanced Analysis', 'description': 'Sanctions scoring, appellate analysis, settlement calculation'},
    {'range': '81-88', 'category': 'Convergence', 'description': 'Dashboard, risk matrix, master reports'},
    
    # Wave 11-15 (Tools 89-130) - detailed
    {'id': 89, 'name': 'Risk Matrix', 'file': 'risk_matrix.py', 'category': 'Strategy'},
    {'id': 90, 'name': 'Master Dashboard', 'file': 'master_dashboard.py', 'category': 'Command Center'},
    {'id': 91, 'name': 'Deposition Questions', 'file': 'deposition_questions.py', 'category': 'Discovery'},
    {'id': 92, 'name': 'Settlement Calculator', 'file': 'settlement_calculator.py', 'category': 'Financial'},
    {'id': 93, 'name': 'Court Rule Compliance', 'file': 'court_rule_compliance.py', 'category': 'Compliance'},
    {'id': 94, 'name': 'Sanctions Risk Scorer', 'file': 'sanctions_risk_scorer.py', 'category': 'Risk'},
    {'id': 95, 'name': 'Filing Dependency Graph', 'file': 'filing_dependency_graph.py', 'category': 'Strategy'},
    {'id': 96, 'name': 'Appellate Issue Spotter', 'file': 'appellate_issue_spotter.py', 'category': 'Appellate'},
    {'id': 97, 'name': 'Damages Calculator', 'file': 'damages_calculator.py', 'category': 'Financial'},
    {'id': 98, 'name': 'Best Interest Analyzer', 'file': 'best_interest_analyzer.py', 'category': 'Custody'},
    {'id': 99, 'name': 'Litigation Calendar', 'file': 'litigation_calendar.py', 'category': 'Calendar'},
    {'id': 100, 'name': '🏆 CENTURY CONVERGENCE', 'file': 'convergence_report.py', 'category': 'Capstone'},
    {'id': 101, 'name': 'War Room Briefing', 'file': 'war_room_briefing.py', 'category': 'Intelligence'},
    {'id': 102, 'name': 'Objection Reference', 'file': 'objection_reference.py', 'category': 'Courtroom'},
    {'id': 103, 'name': 'Canon Violation Mapper', 'file': 'canon_violation_mapper.py', 'category': 'Judicial'},
    {'id': 104, 'name': 'Authentication Checklist', 'file': 'authentication_checklist.py', 'category': 'Evidence'},
    {'id': 105, 'name': 'IFP Generator', 'file': 'ifp_generator.py', 'category': 'Financial'},
    {'id': 106, 'name': 'Hearing Simulator', 'file': 'hearing_simulator.py', 'category': 'Practice'},
    {'id': 107, 'name': 'Discovery Generator', 'file': 'discovery_generator.py', 'category': 'Discovery'},
    {'id': 108, 'name': 'Cost Tracker', 'file': 'cost_tracker.py', 'category': 'Financial'},
    {'id': 109, 'name': 'GAL Briefing', 'file': 'gal_briefing.py', 'category': 'Custody'},
    {'id': 110, 'name': 'Post-Trial Motions', 'file': 'post_trial_motions.py', 'category': 'Motions'},
    {'id': 111, 'name': 'Perjury Trap Detector', 'file': 'perjury_trap_detector.py', 'category': 'Cross-Exam'},
    {'id': 112, 'name': 'Mediation Prep', 'file': 'mediation_prep.py', 'category': 'ADR'},
    {'id': 113, 'name': 'Case Similarity Engine', 'file': 'case_similarity.py', 'category': 'Research'},
    {'id': 114, 'name': 'Courtroom Checklists', 'file': 'courtroom_checklists.py', 'category': 'Courtroom'},
    {'id': 115, 'name': 'Legal Glossary', 'file': 'legal_glossary.py', 'category': 'Reference'},
    {'id': 116, 'name': 'Evidence Gap Filler', 'file': 'evidence_gap_filler.py', 'category': 'Evidence'},
    {'id': 117, 'name': 'Opposing Counsel Profile', 'file': 'opposing_counsel_profile.py', 'category': 'Intelligence'},
    {'id': 118, 'name': 'Readiness Scorecard v2', 'file': 'readiness_scorecard_v2.py', 'category': 'Assessment'},
    {'id': 119, 'name': 'Emergency Contact Card', 'file': 'emergency_contacts.py', 'category': 'Reference'},
    {'id': 120, 'name': '🏆 FINAL CONVERGENCE', 'file': 'final_convergence_120.py', 'category': 'Capstone'},
    {'id': 121, 'name': 'Witness Subpoenas', 'file': 'witness_subpoenas.py', 'category': 'Discovery'},
    {'id': 122, 'name': 'Exhibit Book Builder', 'file': 'exhibit_book_builder.py', 'category': 'Trial Prep'},
    {'id': 123, 'name': 'Closing Arguments', 'file': 'closing_arguments.py', 'category': 'Trial Prep'},
    {'id': 124, 'name': 'Appeal Record Organizer', 'file': 'appeal_record_organizer.py', 'category': 'Appellate'},
    {'id': 125, 'name': 'Compliance Monitor', 'file': 'compliance_monitor.py', 'category': 'Compliance'},
    {'id': 126, 'name': 'Contempt Motions', 'file': 'contempt_motions.py', 'category': 'Motions'},
    {'id': 127, 'name': 'E-Filing Guide', 'file': 'efiling_guide.py', 'category': 'Filing'},
    {'id': 128, 'name': 'Pro Se Rights Asserter', 'file': 'pro_se_rights.py', 'category': 'Rights'},
    {'id': 129, 'name': 'Service Matrix', 'file': 'service_matrix.py', 'category': 'Service'},
    {'id': 130, 'name': '📚 MASTER TOOL INDEX', 'file': 'master_tool_index.py', 'category': 'Index'},
]

def main():
    print("=" * 70)
    print("📚 MASTER TOOL INDEX — Tool #130")
    print("=" * 70)
    
    # Count actual tool files
    tool_files = list(TOOLS_DIR.glob('*.py'))
    report_files = list(REPORTS_DIR.glob('*.*'))
    
    lines = [
        "# 📚 MASTER TOOL INDEX",
        f"*Generated: {datetime.now().strftime('%Y-%m-%d %H:%M')} | Tool #130*",
        f"*{len(tool_files)} Python tools | {len(report_files)} reports*\n",
        "---\n",
        "## TOOL CATEGORIES\n",
    ]
    
    # Count categories
    categories = {}
    for t in TOOL_INDEX:
        if 'category' in t:
            cat = t['category']
            categories[cat] = categories.get(cat, 0) + 1
    
    lines.append("| Category | Count |")
    lines.append("|----------|-------|")
    for cat, count in sorted(categories.items(), key=lambda x: -x[1]):
        lines.append(f"| {cat} | {count} |")
    
    lines.extend(["", "---\n", "## COMPLETE TOOL LIST\n"])
    
    # Summary ranges
    lines.append("### Waves 1-10 (Foundation)")
    lines.append("| Range | Category | Description |")
    lines.append("|-------|----------|-------------|")
    for t in TOOL_INDEX:
        if 'range' in t:
            lines.append(f"| #{t['range']} | {t['category']} | {t['description']} |")
    
    # Detailed tools
    lines.extend(["", "### Waves 11-15 (Detailed)\n"])
    lines.append("| # | Tool | File | Category |")
    lines.append("|---|------|------|----------|")
    for t in TOOL_INDEX:
        if 'id' in t:
            lines.append(f"| {t['id']} | {t['name']} | `{t['file']}` | {t['category']} |")
    
    lines.extend([
        "",
        "---\n",
        "## STATISTICS\n",
        f"- **Python Tool Files:** {len(tool_files)}",
        f"- **Report Files:** {len(report_files)}",
        f"- **Tool Categories:** {len(categories)}",
        f"- **Milestones:** Tool #100 (Century), Tool #120 (Final Convergence), Tool #130 (Master Index)",
        "",
        "## HOW TO USE\n",
        "Each tool is a standalone Python script that can be run independently:",
        "```powershell",
        "$env:PYTHONUTF8='1'",
        "cd C:\\Users\\andre\\LitigationOS\\00_SYSTEM\\tools",
        "python <tool_name>.py",
        "```\n",
        "Reports are generated in `00_SYSTEM/reports/` as both `.md` (human-readable) and `.json` (machine-readable).\n",
        f"*📚 Master Tool Index — {len(tool_files)} tools · {len(report_files)} reports · Tool #130*",
    ])
    
    md_path = REPORTS_DIR / "MASTER_TOOL_INDEX.md"
    md_path.write_text('\n'.join(lines), encoding='utf-8')
    
    json_path = REPORTS_DIR / "master_tool_index.json"
    json_path.write_text(json.dumps({
        'generated': datetime.now().isoformat(),
        'tool': 'Master Tool Index (#130)',
        'tool_files': len(tool_files),
        'report_files': len(report_files),
        'categories': len(categories),
        'category_counts': categories,
    }, indent=2), encoding='utf-8')
    
    print(f"\n📚 MASTER TOOL INDEX")
    print(f"   {len(tool_files)} Python tools")
    print(f"   {len(report_files)} reports")
    print(f"   {len(categories)} categories")
    print(f"   Reports: MASTER_TOOL_INDEX.md + master_tool_index.json")

if __name__ == '__main__':
    main()
