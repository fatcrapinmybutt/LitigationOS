#!/usr/bin/env python3
"""
Tool #114 — Courtroom Checklist Generator
=============================================
🆕 NOVEL TOOL — Pre-hearing checklist for every filing type

What to bring, what to prepare, what to expect.
Like a pilot's pre-flight checklist but for court.
"""
import sys, json
from pathlib import Path
from datetime import datetime

sys.stdout = open(sys.stdout.fileno(), mode='w', encoding='utf-8', errors='replace')

REPO = Path(r"C:\Users\andre\LitigationOS")
REPORTS_DIR = REPO / "00_SYSTEM" / "reports"

CHECKLISTS = {
    'every_hearing': {
        'title': 'EVERY HEARING (Universal Checklist)',
        'items': [
            ('📁 Documents', [
                'Filed motion + 3 copies (judge, clerk, opposing)',
                'Exhibit binder (tabbed, indexed, Bates-numbered)',
                'Legal authority printouts (cases cited in brief)',
                'Pro Se Rights Card (pocket)',
                'Objection Quick-Reference (pocket)',
                'Notepad + 2 pens (take notes of EVERYTHING)',
                'Calendar (for scheduling)',
            ]),
            ('👔 Appearance', [
                'Business attire (suit/dress shirt + tie minimum)',
                'Clean, pressed, professional — first impressions matter',
                'Remove hat before entering courtroom',
                'Silence phone COMPLETELY (not vibrate — OFF)',
            ]),
            ('⏰ Timing', [
                'Arrive 30 minutes early',
                'Check in with clerk upon arrival',
                'Use restroom BEFORE hearing starts',
                'Review key points one final time in hallway',
            ]),
            ('🧠 Mental Prep', [
                'Review hearing simulator script (Tool #106)',
                'Practice opening statement out loud (car is fine)',
                'Breathe — 4 counts in, 4 counts hold, 4 counts out',
                'Remember: calm, prepared, respectful = winning strategy',
            ]),
        ],
    },
    'emergency_motion': {
        'title': 'EMERGENCY MOTION HEARING (F1)',
        'items': [
            ('📋 Specific Documents', [
                'Emergency motion + affidavit (signed, notarized)',
                'Proposed order (for judge to sign if granted)',
                'Evidence of emergency (dated, specific)',
                'MCL 722.27a printout (know the standard)',
                'Shade v Wright printout (your key case)',
            ]),
            ('🎯 Key Arguments', [
                'The emergency: complete denial of parenting time',
                'No MCL 722.27a(3) findings were ever made',
                'Irreparable harm: every day damages parent-child bond',
                'Balance of harms favors restoration of parenting time',
            ]),
        ],
    },
    'disqualification': {
        'title': 'DISQUALIFICATION HEARING (F3)',
        'items': [
            ('📋 Specific Documents', [
                'MCR 2.003 motion + affidavit of prejudice',
                'Documented instances of bias (TOP 3 STRONGEST)',
                'Canon violations cross-reference (Tool #103)',
                'Crain v Allison printout (objective test)',
                'Armstrong v Ypsilanti printout (pattern = bias)',
            ]),
            ('🎯 Key Arguments', [
                'This is NOT about adverse rulings — cite Cain exception',
                'Focus on PROCEDURAL irregularities not substantive disagreement',
                'Pattern of conduct, not single incident',
                'Appearance of impropriety under Canon 2',
            ]),
            ('⚠️ Special Notes', [
                'The judge YOU are disqualifying may hear this motion',
                'Be EXTRA respectful — "no personal disrespect intended"',
                'If denied, IMMEDIATELY file with Chief Judge per MCR 2.003(D)',
                'Also file JTC complaint (F6) simultaneously',
            ]),
        ],
    },
    'custody_hearing': {
        'title': 'CUSTODY MODIFICATION HEARING (F7)',
        'items': [
            ('📋 Specific Documents', [
                'Motion for custody modification',
                'Best Interest Factor analysis (12 factors)',
                'Evidence binder organized BY FACTOR',
                'Proposed parenting plan (3 options)',
                'Vodvarka v Grasmeyer printout (threshold test)',
                'Brown v Loveman printout (all 12 factors required)',
            ]),
            ('🎯 Key Arguments', [
                'Threshold: proper cause / change of circumstances EXISTS',
                'Factor (j): Andrew facilitates; Emily blocks',
                'Factor (e): Emily\'s moral fitness (deception in filings)',
                'Factor (b): Andrew\'s consistent requests for contact',
                'OVERALL: Andrew wins 10/12 factors per analysis',
            ]),
        ],
    },
}

def main():
    print("=" * 70)
    print("COURTROOM CHECKLIST GENERATOR — Tool #114")
    print("=" * 70)
    
    lines = [
        "# ✅ COURTROOM CHECKLISTS",
        f"*Generated: {datetime.now().strftime('%Y-%m-%d %H:%M')} | Tool #114*",
        "*PRINT AND BRING TO EVERY HEARING*\n",
        "---\n",
    ]
    
    total_items = 0
    
    for key, checklist in CHECKLISTS.items():
        lines.append(f"## {checklist['title']}\n")
        
        for section_name, items in checklist['items']:
            lines.append(f"### {section_name}\n")
            for item in items:
                lines.append(f"- [ ] {item}")
                total_items += 1
            lines.append("")
        
        lines.append("---\n")
        item_count = sum(len(items) for _, items in checklist['items'])
        print(f"  ✅ {checklist['title'][:40]}: {item_count} items")
    
    # Emergency procedures
    lines.extend([
        "## 🚨 EMERGENCY PROCEDURES (IF THINGS GO WRONG)\n",
        "### If Judge Rules Against You On The Spot:",
        "1. \"Your Honor, I respectfully request the court state its findings on the record.\"",
        "2. \"Your Honor, I note my objection for the record.\"",
        "3. DO NOT argue further — you'll address it on appeal",
        "4. Ask for stay pending appeal if appropriate",
        "5. File reconsideration within 21 days (MCR 2.119(F))\n",
        
        "### If Opposing Counsel Ambushes With New Evidence:",
        "1. \"Your Honor, I object. This evidence was not disclosed in discovery/advance.\"",
        "2. \"I request a continuance to review and respond to this new material.\"",
        "3. \"If the court admits this evidence, I request the opportunity to rebut.\"\n",
        
        "### If You Get Flustered:",
        "1. \"Your Honor, may I have a moment to gather my thoughts?\"",
        "2. Take a breath. Look at your notes.",
        "3. Return to your prepared arguments — the script is your anchor.",
        "4. It's OK to read from notes — judges expect pro se litigants to do this.\n",
        
        "### If Emily/Berry Cause a Scene:",
        "1. Say NOTHING. Do not react.",
        "2. The judge will handle courtroom order.",
        "3. If not addressed: \"Your Honor, I'd like the record to reflect [what happened].\"",
        "",
        f"*Courtroom Checklists — Tool #114 — {total_items} checklist items across {len(CHECKLISTS)} hearing types*",
    ])
    
    md_path = REPORTS_DIR / "COURTROOM_CHECKLISTS.md"
    md_path.write_text('\n'.join(lines), encoding='utf-8')
    
    json_path = REPORTS_DIR / "courtroom_checklists.json"
    json_path.write_text(json.dumps({
        'generated': datetime.now().isoformat(),
        'tool': 'Courtroom Checklist Generator (#114)',
        'checklists': len(CHECKLISTS),
        'total_items': total_items,
        'types': list(CHECKLISTS.keys()),
    }, indent=2), encoding='utf-8')
    
    print(f"\n✅ {len(CHECKLISTS)} checklists with {total_items} total items")
    print(f"   + Emergency procedures for 4 courtroom scenarios")
    print(f"   Reports: COURTROOM_CHECKLISTS.md + courtroom_checklists.json")

if __name__ == '__main__':
    main()
