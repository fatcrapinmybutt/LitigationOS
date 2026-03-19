#!/usr/bin/env python3
"""
Tool #152 — Judicial Canons Quick Reference
=================================================
🆕 NOVEL TOOL — Every Michigan judicial canon relevant
to McNeill's conduct, with specific violation examples.

Essential reference for F3 (disqualification) and F6 (JTC).
"""
import sys, json
from pathlib import Path
from datetime import datetime

sys.stdout = open(sys.stdout.fileno(), mode='w', encoding='utf-8', errors='replace')

REPO = Path(r"C:\Users\andre\LitigationOS")
REPORTS_DIR = REPO / "00_SYSTEM" / "reports"

CANONS = [
    {
        'canon': 'Canon 1',
        'title': 'A Judge Should Uphold the Integrity and Independence of the Judiciary',
        'text': 'Judge should participate in establishing, maintaining, and enforcing high standards of conduct',
        'mcneill_violations': [
            'Pattern of one-sided rulings undermines public confidence in judiciary',
            'Failure to ensure due process for pro se litigant',
        ],
    },
    {
        'canon': 'Canon 2',
        'title': 'A Judge Should Avoid Impropriety and the Appearance of Impropriety',
        'text': 'Judge should act at all times in a manner that promotes public confidence in integrity of judiciary',
        'mcneill_violations': [
            'Ex parte communications (Rusco warrant email)',
            'Appearance of favoritism toward represented party over pro se litigant',
            'Pattern suggesting predetermined outcomes',
        ],
    },
    {
        'canon': 'Canon 3',
        'title': 'A Judge Should Perform the Duties of Office Impartially and Diligently',
        'text': 'Judge should be faithful to the law and maintain professional competence',
        'mcneill_violations': [
            'Canon 3(A)(3): Failed to be patient and courteous to pro se litigant',
            'Canon 3(A)(4): Failed to accord full right to be heard per law',
            'Canon 3(A)(7): Failed to ensure parties maintain decorum',
            'Canon 3(B)(5): Performed judicial duties without bias or prejudice (violated)',
            'Canon 3(B)(7): Ex parte communications occurred',
        ],
    },
    {
        'canon': 'Canon 4',
        'title': 'A Judge May Engage in Extra-Judicial Activities',
        'text': 'Permissive — not directly relevant to violations alleged',
        'mcneill_violations': [],
    },
    {
        'canon': 'Canon 5',
        'title': 'A Judge Should Regulate Extra-Judicial Activities to Minimize Conflicts',
        'text': 'Minimize risk of conflicts with judicial duties',
        'mcneill_violations': [],
    },
    {
        'canon': 'Canon 6',
        'title': 'A Judge Should Regularly File Financial Disclosure Reports',
        'text': 'Financial transparency requirement',
        'mcneill_violations': [],
    },
    {
        'canon': 'Canon 7',
        'title': 'A Judge Should Refrain from Political Activity Inappropriate to Judicial Office',
        'text': 'Limits political involvement',
        'mcneill_violations': [],
    },
]

def main():
    print("=" * 70)
    print("JUDICIAL CANONS QUICK REFERENCE — Tool #152")
    print("=" * 70)

    violated_canons = [c for c in CANONS if c['mcneill_violations']]
    total_violations = sum(len(c['mcneill_violations']) for c in CANONS)

    lines = [
        "# ⚖️ MICHIGAN JUDICIAL CANONS — QUICK REFERENCE",
        f"*Generated: {datetime.now().strftime('%Y-%m-%d %H:%M')} | Tool #152*",
        f"*{len(violated_canons)} canons violated · {total_violations} specific violations documented*\n",
        "---\n",
        "## VIOLATION SUMMARY\n",
        "| Canon | Title | Violations |",
        "|-------|-------|-----------|",
    ]

    for c in CANONS:
        v_count = len(c['mcneill_violations'])
        status = f"🔴 {v_count}" if v_count > 0 else "🟢 0"
        lines.append(f"| {c['canon']} | {c['title'][:50]} | {status} |")
        if v_count > 0:
            print(f"  🔴 {c['canon']}: {v_count} violations — {c['title'][:40]}")

    lines.extend(["", "---\n"])

    for c in CANONS:
        if c['mcneill_violations']:
            lines.append(f"## {c['canon']} — {c['title']}")
            lines.append(f"*{c['text']}*\n")
            lines.append("### McNeill Violations:")
            for v in c['mcneill_violations']:
                lines.append(f"- 🔴 {v}")
            lines.append("\n---\n")

    lines.extend([
        "## HOW TO CITE IN FILINGS\n",
        "### In F3 (Disqualification):",
        "\"Judge McNeill has violated Canons 1, 2, and 3 of the Michigan Code of Judicial Conduct,",
        "specifically Canon 3(B)(5) (bias), Canon 3(B)(7) (ex parte communications),",
        "and Canon 2 (appearance of impropriety). These violations establish that a",
        "reasonable person would question the judge's impartiality per MCR 2.003(C)(1)(b).\"\n",
        "### In F6 (JTC Complaint):",
        "\"The JTC should investigate violations of Canons 1, 2, and 3 as evidenced by",
        "the documented pattern of [cite specific incidents with dates].\"\n",
        f"*{len(violated_canons)} violated canons · {total_violations} violations · Use in F3 + F6*",
    ])

    md_path = REPORTS_DIR / "JUDICIAL_CANONS.md"
    md_path.write_text('\n'.join(lines), encoding='utf-8')

    json_path = REPORTS_DIR / "judicial_canons.json"
    json_path.write_text(json.dumps({
        'generated': datetime.now().isoformat(),
        'tool': 'Judicial Canons Quick Reference (#152)',
        'canons': len(CANONS),
        'violated': len(violated_canons),
        'total_violations': total_violations,
    }, indent=2), encoding='utf-8')

    print(f"\n✅ {len(violated_canons)} canons violated with {total_violations} specific violations")
    print(f"   Reports: JUDICIAL_CANONS.md + judicial_canons.json")

if __name__ == '__main__':
    main()
