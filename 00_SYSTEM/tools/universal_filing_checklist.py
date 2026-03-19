#!/usr/bin/env python3
"""
Tool #174 — Court Filing Checklist (Universal)
=================================================
🆕 NOVEL TOOL — A universal pre-filing checklist
that applies to EVERY filing. Print once, use forever.
"""
import sys, json
from pathlib import Path
from datetime import datetime

sys.stdout = open(sys.stdout.fileno(), mode='w', encoding='utf-8', errors='replace')

REPO = Path(r"C:\Users\andre\LitigationOS")
REPORTS_DIR = REPO / "00_SYSTEM" / "reports"

CHECKLIST = {
    'document_prep': {
        'title': '📄 Document Preparation',
        'items': [
            'Caption matches case number and court exactly',
            'All parties named correctly (Andrew James Pigors / Emily A. Watson)',
            'Child referred to by initials only (L.D.W.) per MCR 8.119(H)',
            'Judge name correct: Hon. Jenny L. McNeill (or new judge if reassigned)',
            'Numbered paragraphs throughout',
            'Signature block with pro se designation, address, phone, email',
            'Date on the document matches filing date',
        ],
    },
    'legal_review': {
        'title': '⚖️ Legal Review',
        'items': [
            'Every factual claim is supported by evidence (exhibit reference or DB cite)',
            'Every legal claim cites the correct statute/rule/case',
            'IRAC structure for each argument (Issue → Rule → Application → Conclusion)',
            'No fabricated statistics or inflated numbers',
            'No emotional language — factual and professional throughout',
            'Arguments address likely counterarguments',
            'Relief requested is specific and achievable',
        ],
    },
    'copies_service': {
        'title': '📋 Copies & Service',
        'items': [
            '4 copies minimum: Original (court), Judge copy, Emily copy, Your copy',
            'Certificate of Service attached to every filing',
            'Service method identified (personal, mail, email, MiFILE)',
            'If mail: add certified mail receipt number to cert of service',
            'Proof of service filed with clerk',
        ],
    },
    'exhibits': {
        'title': '📎 Exhibits',
        'items': [
            'All exhibits labeled (Exhibit A, B, C...)',
            'Exhibit index/list included',
            'Each exhibit is referenced in the body of the motion',
            'Exhibits are tabbed and in order',
            'No exhibits that haven\'t been authenticated',
        ],
    },
    'fees_filing': {
        'title': '💰 Fees & Filing',
        'items': [
            'IFP order in place (if applicable) — MC 20 filed',
            'Filing fee payment ready (if IFP not granted)',
            'MiFILE account active (if e-filing)',
            'Know the clerk\'s office hours and location',
            'Backup plan if MiFILE is down (paper filing)',
        ],
    },
    'final_checks': {
        'title': '✅ Final Checks',
        'items': [
            'Read the ENTIRE filing one more time — out loud',
            'Spell check completed',
            'Page numbers are correct',
            'No placeholder text remains ([INSERT], [ANDREW_REQUIRED], etc.)',
            'Proposed order is attached (if motion)',
            'Filing is within page limits (if applicable)',
            'You are filing within the deadline',
            'You have a plan for what happens AFTER filing',
        ],
    },
}

def main():
    print("=" * 70)
    print("UNIVERSAL COURT FILING CHECKLIST — Tool #174")
    print("=" * 70)

    lines = [
        "# ✅ UNIVERSAL COURT FILING CHECKLIST",
        f"*Generated: {datetime.now().strftime('%Y-%m-%d %H:%M')} | Tool #174*",
        f"*Use this for EVERY filing. Print it. Laminate it.*\n",
        "---\n",
    ]

    total_items = 0
    for key, section in CHECKLIST.items():
        lines.append(f"## {section['title']}\n")
        for item in section['items']:
            lines.append(f"- [ ] {item}")
        lines.append("")
        total_items += len(section['items'])
        print(f"  {section['title']}: {len(section['items'])} items")

    lines.extend([
        "---\n",
        "## 🎯 THE FILING MANTRA\n",
        "> **Before you file ANYTHING:**",
        "> - Is it TRUE? (every fact verifiable)",
        "> - Is it COMPLETE? (nothing missing)",
        "> - Is it PROFESSIONAL? (a judge would respect it)",
        "> - Is it TIMELY? (within all deadlines)",
        "> - Is it SERVED? (opposing party notified)\n",
        f"*{len(CHECKLIST)} categories · {total_items} checklist items · Use for every single filing*",
    ])

    md_path = REPORTS_DIR / "UNIVERSAL_FILING_CHECKLIST.md"
    md_path.write_text('\n'.join(lines), encoding='utf-8')

    json_path = REPORTS_DIR / "universal_filing_checklist.json"
    json_path.write_text(json.dumps({
        'generated': datetime.now().isoformat(),
        'tool': 'Universal Court Filing Checklist (#174)',
        'categories': len(CHECKLIST),
        'total_items': total_items,
    }, indent=2), encoding='utf-8')

    print(f"\n✅ {len(CHECKLIST)} categories, {total_items} checklist items")
    print(f"   Reports: UNIVERSAL_FILING_CHECKLIST.md + universal_filing_checklist.json")

if __name__ == '__main__':
    main()
