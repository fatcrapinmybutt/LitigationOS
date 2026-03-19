#!/usr/bin/env python3
"""
Tool #170 — Legal Writing Style Guide
=================================================
🆕 NOVEL TOOL — How to write like a lawyer even
when you're not one. Tone, structure, citations,
and persuasive techniques for pro se filings.
"""
import sys, json
from pathlib import Path
from datetime import datetime

sys.stdout = open(sys.stdout.fileno(), mode='w', encoding='utf-8', errors='replace')

REPO = Path(r"C:\Users\andre\LitigationOS")
REPORTS_DIR = REPO / "00_SYSTEM" / "reports"

STYLE_GUIDE = {
    'structure': {
        'title': 'Filing Structure',
        'rules': [
            'Caption → Introduction → Statement of Facts → Legal Standard → Argument → Relief Requested → Signature',
            'Every argument follows IRAC: Issue → Rule → Application → Conclusion',
            'One issue per section — don\'t mix arguments',
            'Use numbered paragraphs throughout (1, 2, 3...)',
            'Bold key phrases for emphasis (sparingly)',
            'Keep paragraphs to 3-5 sentences max',
        ],
    },
    'tone': {
        'title': 'Tone & Voice',
        'rules': [
            'Professional, not emotional: "The evidence demonstrates..." NOT "She destroyed my life..."',
            'Respectful to the court: "This Court should find..." NOT "Any reasonable person can see..."',
            'Confident but not arrogant: "The law clearly supports..." NOT "Obviously..."',
            'Factual, not conclusory: "On [date], Defendant stated [X]..." NOT "Defendant always lies..."',
            'Third person when referring to yourself: "Plaintiff respectfully requests..." NOT "I want..."',
            'Avoid ALL CAPS, exclamation marks, and underlining',
        ],
    },
    'citations': {
        'title': 'Citation Format (Michigan)',
        'rules': [
            'Cases: People v Smith, 123 Mich App 456, 459; 789 NW2d 012 (2020)',
            'Statutes: MCL 722.27a(1)(a)',
            'Court Rules: MCR 2.119(C)(1)',
            'Constitution: Const 1963, art 6, § 4',
            'Federal cases: Smith v Jones, 123 F.3d 456, 459 (6th Cir. 2020)',
            'Pin cites (specific page): Always include — "at 459" or "at *3"',
            'String cites: Strongest case first, then supporting',
            'Use "Id." for consecutive references to the same source',
            'Use "see also" for supporting but not directly on point',
        ],
    },
    'persuasion': {
        'title': 'Persuasive Techniques',
        'rules': [
            'Lead with your STRONGEST argument — judges may stop reading',
            'Use the court\'s own language against opposing party — quote prior orders',
            'Anticipate and address counterarguments BEFORE they\'re raised',
            'Use analogical reasoning — "Like in [case], where the court held..."',
            'Distinguish unfavorable precedent — "Unlike [case], here the facts show..."',
            'End each section with a clear conclusion — "Therefore, this Court should..."',
            'Frame everything around the child\'s best interest — judges respond to this',
        ],
    },
    'common_errors': {
        'title': 'Common Pro Se Writing Errors',
        'rules': [
            'DON\'T: Write a narrative/story — DO: Write structured legal argument',
            'DON\'T: Include irrelevant personal grievances — DO: Stick to legally relevant facts',
            'DON\'T: Attack opposing party\'s character — DO: Show their actions violated the law',
            'DON\'T: Use legal jargon you don\'t understand — DO: Use plain language accurately',
            'DON\'T: Make unsupported claims — DO: Cite evidence for every factual assertion',
            'DON\'T: Exceed page limits — DO: Be concise (judges appreciate brevity)',
            'DON\'T: File everything you write — DO: Wait 24 hours, re-read, then file',
        ],
    },
}

def main():
    print("=" * 70)
    print("LEGAL WRITING STYLE GUIDE — Tool #170")
    print("=" * 70)

    lines = [
        "# ✍️ LEGAL WRITING STYLE GUIDE",
        f"*Generated: {datetime.now().strftime('%Y-%m-%d %H:%M')} | Tool #170*",
        f"*How to write like a lawyer even when you\'re not one*\n",
        "---\n",
    ]

    total_rules = 0
    for key, section in STYLE_GUIDE.items():
        lines.append(f"## {section['title']}\n")
        for rule in section['rules']:
            lines.append(f"- {rule}")
        lines.append("")
        total_rules += len(section['rules'])
        print(f"  ✍️ {section['title']}: {len(section['rules'])} rules")

    lines.extend([
        "---\n",
        "## 🎯 THE ONE-PAGE TEST\n",
        "> Before filing anything, ask: **Can a judge understand my argument",
        "> by reading ONLY the first page?**",
        ">",
        "> If not, rewrite. Judges have hundreds of cases. They skim.",
        "> Your first page must hook them.\n",
        f"*{len(STYLE_GUIDE)} categories · {total_rules} writing rules · Apply to every filing*",
    ])

    md_path = REPORTS_DIR / "LEGAL_WRITING_GUIDE.md"
    md_path.write_text('\n'.join(lines), encoding='utf-8')

    json_path = REPORTS_DIR / "legal_writing_guide.json"
    json_path.write_text(json.dumps({
        'generated': datetime.now().isoformat(),
        'tool': 'Legal Writing Style Guide (#170)',
        'categories': len(STYLE_GUIDE),
        'total_rules': total_rules,
    }, indent=2), encoding='utf-8')

    print(f"\n✅ {len(STYLE_GUIDE)} categories, {total_rules} writing rules")
    print(f"   Reports: LEGAL_WRITING_GUIDE.md + legal_writing_guide.json")

if __name__ == '__main__':
    main()
