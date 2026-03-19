#!/usr/bin/env python3
"""
Tool #161 — Appellate Brief Outline Generator
=================================================
🆕 NOVEL TOOL — Generates complete structural outlines
for COA and MSC briefs with proper Michigan appellate
formatting requirements.
"""
import sys, json
from pathlib import Path
from datetime import datetime

sys.stdout = open(sys.stdout.fileno(), mode='w', encoding='utf-8', errors='replace')

REPO = Path(r"C:\Users\andre\LitigationOS")
REPORTS_DIR = REPO / "00_SYSTEM" / "reports"

BRIEF_OUTLINES = [
    {
        'brief': 'COA Brief on Appeal (F9)',
        'case': 'COA 366810',
        'rules': 'MCR 7.212',
        'sections': [
            {'name': 'Cover Page', 'rule': 'MCR 7.212(B)', 'content': 'Case caption, lower court info, parties, counsel/pro se designation'},
            {'name': 'Table of Contents', 'rule': 'MCR 7.212(B)', 'content': 'All headings with page numbers'},
            {'name': 'Index of Authorities', 'rule': 'MCR 7.212(B)', 'content': 'Cases, statutes, rules, constitutional provisions — alphabetical with page refs'},
            {'name': 'Statement of Jurisdiction', 'rule': 'MCR 7.212(C)(1)', 'content': 'Basis for COA jurisdiction — MCL 600.308, appeal of right from final order'},
            {'name': 'Statement of Questions Presented', 'rule': 'MCR 7.212(C)(2)', 'content': 'Each issue on appeal, stated as a question, with trial court answer'},
            {'name': 'Statement of Facts', 'rule': 'MCR 7.212(C)(3)', 'content': 'Chronological facts with record citations (lower court register of actions)'},
            {'name': 'Argument', 'rule': 'MCR 7.212(C)(4)', 'content': 'IRAC format for each issue — Issue, Rule, Application, Conclusion'},
            {'name': 'Standard of Review', 'rule': 'MCR 7.212(C)(4)', 'content': 'Abuse of discretion (custody), de novo (constitutional), clear error (findings of fact)'},
            {'name': 'Relief Requested', 'rule': 'MCR 7.212(C)(5)', 'content': 'Specific relief: reversal, remand, reassignment to new judge'},
            {'name': 'Signature', 'rule': 'MCR 7.212(B)', 'content': 'Pro se designation, address, phone, email'},
            {'name': 'Proof of Service', 'rule': 'MCR 2.107', 'content': 'Certificate of service on all parties'},
        ],
    },
    {
        'brief': 'MSC Application for Leave (F5)',
        'case': 'MSC [To Be Assigned]',
        'rules': 'MCR 7.305',
        'sections': [
            {'name': 'Cover Page', 'rule': 'MCR 7.305(B)(1)', 'content': 'Caption, lower courts, questions presented'},
            {'name': 'Questions Presented', 'rule': 'MCR 7.305(B)(2)', 'content': 'Constitutional issues — due process, parental liberty, equal protection'},
            {'name': 'Statement of Facts', 'rule': 'MCR 7.305(B)(3)', 'content': 'Concise factual background with citations to lower court record'},
            {'name': 'Argument for Leave', 'rule': 'MCR 7.305(B)(4)', 'content': 'Why MSC should accept: (1) significant constitutional question, (2) conflict with precedent, (3) public importance'},
            {'name': 'Relief Requested', 'rule': 'MCR 7.305(B)(5)', 'content': 'Grant leave, reverse lower courts, superintending control order'},
            {'name': 'Appendix', 'rule': 'MCR 7.305(B)(6)', 'content': 'Lower court opinions and orders being challenged'},
        ],
    },
]

APPELLATE_ISSUES = [
    {'issue': 'Due Process — Parental Liberty', 'standard': 'De novo', 'strength': 'STRONG',
     'question': 'Did the trial court violate Plaintiff\'s 14th Amendment right to parent L.D.W. by suspending all parenting time without constitutionally adequate findings?'},
    {'issue': 'Judicial Bias / Recusal', 'standard': 'Abuse of discretion', 'strength': 'STRONG',
     'question': 'Did Judge McNeill\'s pattern of ex parte communications, disparate treatment, and pre-determined outcomes require recusal under MCR 2.003(C)?'},
    {'issue': 'Fraud Upon the Court', 'standard': 'De novo', 'strength': 'STRONG',
     'question': 'Did the trial court err by failing to investigate Defendant\'s fraud on the court through perjured filings and fabricated evidence?'},
    {'issue': 'Best Interest Factors', 'standard': 'Clear error', 'strength': 'MODERATE',
     'question': 'Were the trial court\'s best interest findings clearly erroneous where Factor I (willingness to facilitate) overwhelmingly favors Plaintiff?'},
    {'issue': 'MCL 722.27a Parenting Time', 'standard': 'Abuse of discretion', 'strength': 'STRONG',
     'question': 'Did the trial court abuse its discretion by restricting parenting time without the required specific findings under MCL 722.27a(3)?'},
]

def main():
    print("=" * 70)
    print("APPELLATE BRIEF OUTLINE GENERATOR — Tool #161")
    print("=" * 70)

    lines = [
        "# 📝 APPELLATE BRIEF OUTLINES",
        f"*Generated: {datetime.now().strftime('%Y-%m-%d %H:%M')} | Tool #161*",
        f"*{len(BRIEF_OUTLINES)} brief structures · {len(APPELLATE_ISSUES)} appellate issues*\n",
        "---\n",
    ]

    for brief in BRIEF_OUTLINES:
        lines.append(f"## {brief['brief']}")
        lines.append(f"**Case:** {brief['case']} | **Governing Rule:** {brief['rules']}\n")
        lines.append("| # | Section | Rule | Content |")
        lines.append("|---|---------|------|---------|")
        for i, sec in enumerate(brief['sections'], 1):
            lines.append(f"| {i} | {sec['name']} | {sec['rule']} | {sec['content']} |")
        lines.append("")
        total_sections = len(brief['sections'])
        print(f"  📝 {brief['brief']}: {total_sections} sections")

    lines.extend(["---\n", "## APPELLATE ISSUES\n",
                   "| Issue | Standard | Strength | Question |",
                   "|-------|----------|----------|----------|"])
    for issue in APPELLATE_ISSUES:
        lines.append(f"| {issue['issue']} | {issue['standard']} | {issue['strength']} | {issue['question'][:80]}... |")
        print(f"  ⚖️ {issue['issue']}: {issue['strength']}")

    total_sections = sum(len(b['sections']) for b in BRIEF_OUTLINES)
    lines.extend([
        "", "---\n",
        f"*{len(BRIEF_OUTLINES)} briefs · {total_sections} sections · {len(APPELLATE_ISSUES)} issues*",
    ])

    md_path = REPORTS_DIR / "APPELLATE_BRIEF_OUTLINES.md"
    md_path.write_text('\n'.join(lines), encoding='utf-8')

    json_path = REPORTS_DIR / "appellate_brief_outlines.json"
    json_path.write_text(json.dumps({
        'generated': datetime.now().isoformat(),
        'tool': 'Appellate Brief Outline Generator (#161)',
        'briefs': len(BRIEF_OUTLINES),
        'total_sections': total_sections,
        'issues': len(APPELLATE_ISSUES),
    }, indent=2), encoding='utf-8')

    print(f"\n✅ {len(BRIEF_OUTLINES)} brief outlines with {total_sections} sections and {len(APPELLATE_ISSUES)} issues")
    print(f"   Reports: APPELLATE_BRIEF_OUTLINES.md + appellate_brief_outlines.json")

if __name__ == '__main__':
    main()
