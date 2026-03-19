#!/usr/bin/env python3
"""
Tool #128 — Pro Se Rights Asserter
==========================================
🆕 NOVEL TOOL — Complete guide to Andrew's rights as a 
pro se litigant, with exact citations and scripts for 
asserting each right in court.

Michigan gives pro se litigants specific protections.
Know them. Use them. Assert them.
"""
import sys, json
from pathlib import Path
from datetime import datetime

sys.stdout = open(sys.stdout.fileno(), mode='w', encoding='utf-8', errors='replace')

REPO = Path(r"C:\Users\andre\LitigationOS")
REPORTS_DIR = REPO / "00_SYSTEM" / "reports"

PRO_SE_RIGHTS = [
    {
        'right': 'Right to Be Heard',
        'authority': 'US Const Amend XIV; Mich Const Art 1 §17; Mathews v Eldridge, 424 US 319 (1976)',
        'description': 'Every party has the right to be heard before a court takes action affecting their rights.',
        'script': 'Your Honor, I respectfully assert my right to be heard on this matter before any order is entered. Due process requires notice and an opportunity to be heard.',
        'violations_in_case': 'Ex parte orders entered without notice; "don\'t speak" directive; orders entered based solely on Emily\'s filings.',
    },
    {
        'right': 'Right of Access to Courts',
        'authority': 'US Const Amend I; Mich Const Art 1 §13; Bounds v Smith, 430 US 817 (1977)',
        'description': 'Every person has the right to access the courts and file pleadings.',
        'script': 'Your Honor, I have a constitutional right of access to this Court. Any restriction on my ability to file must be narrowly tailored to a compelling interest.',
        'violations_in_case': '"Do not file anymore" directive restricts court access.',
    },
    {
        'right': 'Right to Impartial Judge',
        'authority': 'MCR 2.003(C); Canon 2, Michigan Code of Judicial Conduct; Caperton v AT Massey Coal, 556 US 868 (2009)',
        'description': 'Every party is entitled to a fair and impartial judge who has no bias or prejudice.',
        'script': 'Your Honor, with all due respect, I move for disqualification under MCR 2.003 based on the pattern of conduct documented in my motion.',
        'violations_in_case': '1,127 documented judicial violations; pattern of one-sided rulings.',
    },
    {
        'right': 'Right to Present Evidence',
        'authority': 'MRE 103; US Const Amend XIV; Crane v Kentucky, 476 US 683 (1986)',
        'description': 'Every party has the right to present relevant evidence in their case.',
        'script': 'Your Honor, I offer Exhibit [X] as evidence relevant to [issue]. I request the opportunity to lay foundation and have this exhibit admitted.',
        'violations_in_case': 'Limited opportunity to present evidence at hearings.',
    },
    {
        'right': 'Right to Cross-Examine Witnesses',
        'authority': 'MRE 611; US Const Amend VI (incorporated); Davis v Alaska, 415 US 308 (1974)',
        'description': 'Every party has the right to cross-examine adverse witnesses.',
        'script': 'Your Honor, I request the right to cross-examine [witness] regarding their testimony.',
        'violations_in_case': 'Limited cross-examination opportunities in prior hearings.',
    },
    {
        'right': 'Liberal Construction of Pro Se Filings',
        'authority': 'Haines v Kerner, 404 US 519 (1972); Estelle v Gamble, 429 US 97 (1976)',
        'description': 'Pro se filings are held to less stringent standards than attorney filings and should be liberally construed.',
        'script': 'Your Honor, as a self-represented litigant, my filings are entitled to liberal construction under Haines v Kerner. I ask the Court to consider the substance of my arguments, not merely their form.',
        'violations_in_case': 'Filings potentially held to attorney standards rather than pro se standards.',
    },
    {
        'right': 'Right to Adequate Time',
        'authority': 'MCR 2.108; MCR 2.119(C)(1); US Const Amend XIV',
        'description': 'Pro se litigants are entitled to adequate time to prepare and respond to filings.',
        'script': 'Your Honor, I need additional time to prepare my response. As a self-represented party, I do not have a legal team and need reasonable time to address this matter.',
        'violations_in_case': 'Orders entered with insufficient notice periods.',
    },
    {
        'right': 'Right to Record Proceedings',
        'authority': 'MCR 8.109; Michigan Freedom of Information Act',
        'description': 'All court proceedings must be recorded. Parties can request transcripts.',
        'script': 'Your Honor, I request that this proceeding be on the record. I also request a copy of the transcript after the hearing.',
        'violations_in_case': 'Ensure all future hearings are properly recorded.',
    },
    {
        'right': 'Right to Object',
        'authority': 'MRE 103(a); MCR 2.111',
        'description': 'Every party has the right to make objections to preserve issues for appeal.',
        'script': 'Objection, Your Honor. [State grounds per MRE — see Tool #102 for complete list].',
        'violations_in_case': 'Must preserve all objections for appellate record.',
    },
    {
        'right': 'Right to Appeal',
        'authority': 'Mich Const Art 6 §1; MCR 7.203; MCR 7.205',
        'description': 'Every party has the right to appeal adverse rulings to a higher court.',
        'script': 'I give notice that I intend to appeal this ruling. I request a stay pending appeal per MCR 7.209.',
        'violations_in_case': 'COA 366810 already filed; additional appeals may follow.',
    },
]

def main():
    print("=" * 70)
    print("PRO SE RIGHTS ASSERTER — Tool #128")
    print("=" * 70)
    
    lines = [
        "# 🛡️ PRO SE RIGHTS — KNOW THEM, USE THEM, ASSERT THEM",
        f"*Generated: {datetime.now().strftime('%Y-%m-%d %H:%M')} | Tool #128*",
        f"*Andrew Pigors — Self-Represented Litigant*\n",
        "---\n",
        "## QUICK REFERENCE CARD (Print This)\n",
        "| # | Right | Key Authority |",
        "|---|-------|---------------|",
    ]
    
    for i, right in enumerate(PRO_SE_RIGHTS, 1):
        auth_short = right['authority'].split(';')[0]
        lines.append(f"| {i} | {right['right']} | {auth_short} |")
    
    lines.extend(["", "---\n"])
    
    for i, right in enumerate(PRO_SE_RIGHTS, 1):
        lines.append(f"## {i}. {right['right']}")
        lines.append(f"**Authority:** {right['authority']}\n")
        lines.append(f"{right['description']}\n")
        lines.append(f"### 🎤 Script (Say This in Court):")
        lines.append(f"> \"{right['script']}\"\n")
        lines.append(f"### ⚠️ Violations in This Case:")
        lines.append(f"{right['violations_in_case']}\n")
        lines.append("---\n")
        
        print(f"  🛡️ {i}. {right['right'][:45]}")
    
    lines.extend([
        "## 🎯 HOW TO USE THIS IN COURT\n",
        "1. **Print this document** and bring it to every hearing",
        "2. **Tab the rights** most relevant to that day's hearing",
        "3. **Read the scripts** out loud before going to court",
        "4. **Stay calm and respectful** when asserting rights",
        "5. **Cite the authority** — judges respond to legal citations",
        "6. **If a right is denied**, state for the record: 'I object to the denial of my right to [X] and preserve this issue for appeal.'\n",
        
        "## ⚡ EMERGENCY PHRASES (Memorize These)\n",
        "- 'Your Honor, I respectfully assert my right to be heard.'",
        "- 'I object and preserve this issue for appeal.'",
        "- 'I request this be placed on the record.'",
        "- 'I need additional time to prepare as a self-represented party.'",
        "- 'I move for recusal under MCR 2.003.'",
        "",
        f"*{len(PRO_SE_RIGHTS)} rights documented · Print and carry at all times*",
    ])
    
    md_path = REPORTS_DIR / "PRO_SE_RIGHTS.md"
    md_path.write_text('\n'.join(lines), encoding='utf-8')
    
    json_path = REPORTS_DIR / "pro_se_rights.json"
    json_path.write_text(json.dumps({
        'generated': datetime.now().isoformat(),
        'tool': 'Pro Se Rights Asserter (#128)',
        'rights_count': len(PRO_SE_RIGHTS),
        'rights': [r['right'] for r in PRO_SE_RIGHTS],
    }, indent=2), encoding='utf-8')
    
    print(f"\n✅ {len(PRO_SE_RIGHTS)} pro se rights documented with scripts")
    print(f"   PRINT AND BRING TO EVERY HEARING")
    print(f"   Reports: PRO_SE_RIGHTS.md + pro_se_rights.json")

if __name__ == '__main__':
    main()
