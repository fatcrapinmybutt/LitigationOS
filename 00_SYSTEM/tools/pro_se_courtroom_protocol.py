#!/usr/bin/env python3
"""
Tool #62 — Pro Se Courtroom Protocol
========================================
Step-by-step courtroom behavior guide for a pro se litigant.
Covers: dress code, addressing the court, objections, evidence presentation,
time management, emotional control, and common pro se mistakes to avoid.

This is a practical survival guide for each court Andrew will appear in.
"""
import sys, json
from pathlib import Path
from datetime import datetime

sys.stdout = open(sys.stdout.fileno(), mode='w', encoding='utf-8', errors='replace')

REPO = Path(r"C:\Users\andre\LitigationOS")
REPORTS_DIR = REPO / "00_SYSTEM" / "reports"
PKG_BASE = Path(r"C:\Users\andre\Desktop\LITIGATION_FILING_PACKAGE")

COURTS = {
    '14th_circuit': {
        'name': '14th Circuit Court — Muskegon County',
        'address': '990 Terrace St, Muskegon, MI 49442',
        'phone': '(231) 724-6241',
        'filings': ['F1', 'F2', 'F3', 'F7'],
        'judge': 'Hon. Jenny L. McNeill (seeking disqualification)',
        'courtroom_rules': [
            'Arrive 30 minutes early — check in with clerk',
            'Business attire (suit/tie preferred, minimum: dress shirt, slacks, dress shoes)',
            'No cell phones in courtroom (turn OFF, not vibrate)',
            'Stand when addressing the court',
            'Address judge as "Your Honor" — even if seeking disqualification',
            'Do NOT interrupt opposing counsel — note objections for your turn',
            'Bring 3 copies of everything (court, opposing party, yourself)',
        ],
    },
    'federal': {
        'name': 'US District Court — Western District of Michigan',
        'address': '399 Federal Building, 110 Michigan St NW, Grand Rapids, MI 49503',
        'phone': '(616) 456-2381',
        'filings': ['F4'],
        'judge': 'TBD — assigned on filing',
        'courtroom_rules': [
            'Federal court is MORE formal than state court',
            'Must register for CM/ECF (PACER) before filing',
            'All filings through electronic system — no walk-in filings',
            'Follow Federal Rules of Civil Procedure (FRCP)',
            'Address judge as "Your Honor" or "Judge [Last Name]"',
            'Arrive 45 minutes early for security screening',
            'No electronics of any kind in courtroom',
            'Stand when judge enters and exits',
        ],
    },
    'coa': {
        'name': 'Michigan Court of Appeals',
        'address': '925 W Ottawa St, Lansing, MI 48915 (Cadillac Place: 3020 W Grand Blvd, Detroit)',
        'phone': '(517) 373-0786',
        'filings': ['F8', 'F9'],
        'judge': 'Three-judge panel (assigned after filing)',
        'courtroom_rules': [
            'Oral argument is NOT guaranteed — granted only if court deems it helpful',
            'If granted: strictly timed (usually 15-20 minutes per side)',
            'Focus on legal arguments, NOT facts — judges have read the briefs',
            'Be prepared for questions from the bench — they will interrupt',
            'Know your record cites cold (page and line numbers)',
            'Do NOT repeat what is in your brief — add value',
        ],
    },
}

OBJECTIONS = [
    {'objection': 'Hearsay', 'rule': 'MRE 801-806', 'when': 'Opposing party offers out-of-court statement for truth', 'how': '"Objection, Your Honor — hearsay. The statement is offered for the truth of the matter asserted."'},
    {'objection': 'Relevance', 'rule': 'MRE 401-402', 'when': 'Evidence does not relate to any issue in the case', 'how': '"Objection — relevance. This evidence does not tend to prove or disprove any fact of consequence."'},
    {'objection': 'Leading question', 'rule': 'MRE 611(c)', 'when': 'Attorney asks leading questions on direct examination', 'how': '"Objection — leading. Counsel is suggesting the answer to their own witness."'},
    {'objection': 'Foundation', 'rule': 'MRE 901', 'when': 'Document or evidence not properly authenticated', 'how': '"Objection — lack of foundation. The exhibit has not been properly authenticated."'},
    {'objection': 'Speculation', 'rule': 'MRE 602', 'when': 'Witness testifies about something they have no personal knowledge of', 'how': '"Objection — speculation. The witness has no personal knowledge of this matter."'},
    {'objection': 'Best evidence rule', 'rule': 'MRE 1002', 'when': 'Party offers copy when original is available', 'how': '"Objection — best evidence rule. The original document should be produced."'},
    {'objection': 'Cumulative', 'rule': 'MRE 403', 'when': 'Same point made repeatedly with multiple witnesses', 'how': '"Objection — cumulative. This evidence is duplicative of what has already been presented."'},
    {'objection': 'Assumes facts not in evidence', 'rule': 'MRE 611', 'when': 'Question presupposes something not yet proven', 'how': '"Objection — the question assumes facts not in evidence."'},
]

COMMON_MISTAKES = [
    'Speaking when it is not your turn — wait for the judge to address you',
    'Arguing with the judge — state your position once, then say "For the record, I respectfully disagree"',
    'Getting emotional — courts reward calm, factual presentation',
    'Reading your entire brief aloud — summarize key points, judges can read',
    'Failing to make a record — if the judge rules against you, state your objection clearly for appeal',
    'Not having organized exhibits — tab and number everything, have copies ready',
    'Addressing opposing party directly — always speak to the judge, never to the other side',
    'Making personal attacks — focus on actions and evidence, not character',
    'Failing to preserve issues for appeal — object, cite the rule, get a ruling on the record',
    'Waiving time limits — if you need more time, ask BEFORE the deadline passes',
]

EVIDENCE_PRESENTATION = [
    'Step 1: Mark the exhibit (e.g., "I would like to mark this as Plaintiff\'s Exhibit 1")',
    'Step 2: Show to opposing party ("May I approach? I am showing opposing party Exhibit 1")',
    'Step 3: Lay foundation ("Your Honor, I would like to have this exhibit admitted. It is a [describe]...")',
    'Step 4: Authenticate ("I can authenticate this document as [basis]...")',
    'Step 5: Move for admission ("I move to admit Plaintiff\'s Exhibit 1 into evidence")',
    'Step 6: Wait for ruling before using the exhibit in argument',
    'Step 7: If objection, respond to the specific objection (not a general argument)',
]

def main():
    print("=" * 70)
    print("PRO SE COURTROOM PROTOCOL — Tool #62")
    print(f"Started: {datetime.now().isoformat()}")
    print("=" * 70)
    
    lines = [
        "# PRO SE COURTROOM PROTOCOL & SURVIVAL GUIDE",
        f"*Generated: {datetime.now().strftime('%Y-%m-%d %H:%M')}*",
        "*For: Andrew James Pigors, Pro Se Plaintiff*\n",
        "---\n",
    ]
    
    # Court-specific sections
    for court_id, court in COURTS.items():
        lines.extend([
            f"## {court['name']}",
            f"**Address:** {court['address']}",
            f"**Phone:** {court['phone']}",
            f"**Judge:** {court['judge']}",
            f"**Your filings here:** {', '.join(court['filings'])}\n",
            "### Courtroom Rules",
        ])
        for rule in court['courtroom_rules']:
            lines.append(f"- {rule}")
        lines.append("")
        
        print(f"  📍 {court['name']}: {len(court['filings'])} filings")
    
    # Objections guide
    lines.extend([
        "\n---\n",
        "## OBJECTIONS QUICK REFERENCE",
        "| Objection | Rule | When to Use | Exact Words |",
        "|-----------|------|------------|-------------|",
    ])
    for obj in OBJECTIONS:
        lines.append(f"| **{obj['objection']}** | {obj['rule']} | {obj['when'][:50]} | {obj['how'][:60]}... |")
    
    lines.append("\n### Detailed Objection Scripts")
    for obj in OBJECTIONS:
        lines.extend([
            f"\n#### {obj['objection']} ({obj['rule']})",
            f"**When:** {obj['when']}",
            f"**Say:** *{obj['how']}*",
        ])
    
    # Evidence presentation
    lines.extend([
        "\n---\n",
        "## EVIDENCE PRESENTATION PROTOCOL",
        "Follow these steps EXACTLY for every exhibit:\n",
    ])
    for step in EVIDENCE_PRESENTATION:
        lines.append(f"- {step}")
    
    # Common mistakes
    lines.extend([
        "\n---\n",
        "## TOP 10 PRO SE MISTAKES TO AVOID\n",
    ])
    for i, mistake in enumerate(COMMON_MISTAKES, 1):
        lines.append(f"{i}. **{mistake}**")
    
    # Pre-hearing checklist
    lines.extend([
        "\n---\n",
        "## PRE-HEARING CHECKLIST (Day Before)",
        "- [ ] Review hearing prep kit for this filing (08_HEARING_PREP_KIT.md)",
        "- [ ] Print 3 copies of ALL documents (court + opposing + yourself)",
        "- [ ] Tab and number all exhibits",
        "- [ ] Prepare 2-minute opening statement (memorize, don't read)",
        "- [ ] Prepare 1-minute closing (tie evidence to legal standard)",
        "- [ ] Review anticipated opposition responses (RESPONSE_ANTICIPATOR.md)",
        "- [ ] Charge phone (for GPS directions — turn OFF before entering court)",
        "- [ ] Set 2 alarms (no excuse for being late)",
        "- [ ] Lay out clothes tonight (business attire)",
        "- [ ] Pack folder: filings, exhibits, pen, notepad, water bottle",
        "",
        "## DAY-OF CHECKLIST",
        "- [ ] Arrive 30-45 minutes early",
        "- [ ] Check in with court clerk",
        "- [ ] Review notes while waiting",
        "- [ ] Turn phone completely OFF",
        "- [ ] Use restroom before hearing starts",
        "- [ ] Deep breaths — you are prepared, you have evidence, you have the law",
    ])
    
    lines.extend([
        "\n---",
        f"*Generated by Tool #62 — Pro Se Courtroom Protocol*",
        f"*Covers {len(COURTS)} courts, {len(OBJECTIONS)} objections, {len(COMMON_MISTAKES)} mistake warnings*",
    ])
    
    md_path = REPORTS_DIR / "PRO_SE_COURTROOM_PROTOCOL.md"
    md_path.write_text('\n'.join(lines), encoding='utf-8')
    
    json_path = REPORTS_DIR / "courtroom_protocol.json"
    json_path.write_text(json.dumps({
        'generated': datetime.now().isoformat(),
        'tool': 'Pro Se Courtroom Protocol (#62)',
        'courts': len(COURTS),
        'objections': len(OBJECTIONS),
        'mistakes': len(COMMON_MISTAKES),
        'evidence_steps': len(EVIDENCE_PRESENTATION),
        'courts_detail': COURTS,
        'objections_detail': OBJECTIONS,
    }, indent=2, default=str), encoding='utf-8')
    
    # Save to each package that has a hearing
    for fid in ['F1', 'F3', 'F7']:
        for pkg in PKG_BASE.glob(f"PKG_{fid}_*"):
            proto_path = pkg / "11_COURTROOM_PROTOCOL.md"
            proto_path.write_text('\n'.join(lines), encoding='utf-8')
            print(f"  ✅ {fid}: 11_COURTROOM_PROTOCOL.md saved")
    
    print(f"\n✅ Protocol: {md_path.name}")
    print(f"   {len(COURTS)} courts, {len(OBJECTIONS)} objections, {len(COMMON_MISTAKES)} mistakes to avoid")

if __name__ == '__main__':
    main()
