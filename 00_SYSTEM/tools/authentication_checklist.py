#!/usr/bin/env python3
"""
Tool #104 — Evidence Authentication Checklist
=================================================
🆕 NOVEL TOOL — Ensures every exhibit is properly authenticated

For each exhibit category, generates an authentication checklist:
- Who needs to authenticate it?
- What foundation questions are needed?
- Which MRE rule applies?
- Is a custodian affidavit needed?

Categories:
- Text messages / Screenshots
- Emails
- ChatGPT exports (262K+ items)
- Court documents
- Photos
- Medical/Psych records
- Financial records
- Social media posts
"""
import sys, json
from pathlib import Path
from datetime import datetime

sys.stdout = open(sys.stdout.fileno(), mode='w', encoding='utf-8', errors='replace')

REPO = Path(r"C:\Users\andre\LitigationOS")
REPORTS_DIR = REPO / "00_SYSTEM" / "reports"

EVIDENCE_TYPES = [
    {
        'type': 'Text Messages / SMS',
        'mre_rule': 'MRE 901(b)(1), 901(b)(4)',
        'authentication_method': 'Self-authentication by phone records + distinctive characteristics',
        'foundation_questions': [
            'Do you recognize this phone number as [person\'s] number?',
            'Did you send/receive this text message?',
            'Is this a complete and accurate copy of the conversation?',
            'When was this message sent/received?',
        ],
        'custodian_affidavit': False,
        'notes': 'Screenshots should show phone number, date/time, and message content. Carrier records can corroborate.',
    },
    {
        'type': 'Email Communications',
        'mre_rule': 'MRE 901(b)(1), 901(b)(4), 901(b)(7)',
        'authentication_method': 'Sender/recipient identification + email header metadata',
        'foundation_questions': [
            'Do you recognize this email address as belonging to [person]?',
            'Did you send/receive this email?',
            'Is this a true and accurate copy of the email as you sent/received it?',
        ],
        'custodian_affidavit': False,
        'notes': 'Include full email headers if authenticity is challenged. Gmail/Outlook can export with metadata.',
    },
    {
        'type': 'ChatGPT / AI Chat Exports',
        'mre_rule': 'MRE 901(b)(1), 901(b)(9)',
        'authentication_method': 'Account holder testimony + export metadata + platform verification',
        'foundation_questions': [
            'Is this your ChatGPT/AI account?',
            'Did you have these conversations with the AI system?',
            'Were these exports made directly from your account?',
            'Have these exports been altered in any way?',
        ],
        'custodian_affidavit': True,
        'notes': 'CRITICAL: 262K+ items. Export with timestamps. OpenAI provides data export feature. Affidavit from account holder authenticates.',
    },
    {
        'type': 'Court Documents / Orders',
        'mre_rule': 'MRE 902(1), 902(4)',
        'authentication_method': 'Self-authenticating — certified copies from court clerk',
        'foundation_questions': [
            'No foundation needed for certified copies',
            'For uncertified: "Is this a true and accurate copy of the court order?"',
        ],
        'custodian_affidavit': False,
        'notes': 'Request certified copies from court clerk. Self-authenticating under MRE 902(1) if bearing court seal.',
    },
    {
        'type': 'Photographs',
        'mre_rule': 'MRE 901(b)(1)',
        'authentication_method': 'Witness testimony that photo "fairly and accurately depicts" the scene',
        'foundation_questions': [
            'Do you recognize what is shown in this photograph?',
            'Does this photo fairly and accurately depict [scene/person] as it appeared on [date]?',
            'Who took this photograph?',
            'Has this photo been altered or edited in any way?',
        ],
        'custodian_affidavit': False,
        'notes': 'EXIF metadata (date, location, device) corroborates. Be ready to explain any editing (cropping, etc.).',
    },
    {
        'type': 'Medical / Psychological Records',
        'mre_rule': 'MRE 803(6), 902(11)',
        'authentication_method': 'Business records exception — custodian certification OR testimony',
        'foundation_questions': [
            'Were these records made at or near the time of the events recorded?',
            'Were they made by a person with knowledge?',
            'Were they kept in the regular course of business?',
            'Is it the regular practice to make such records?',
        ],
        'custodian_affidavit': True,
        'notes': 'Subpoena records with custodian affidavit. HIPAA authorization needed. MRE 902(11) allows certification in lieu of testimony.',
    },
    {
        'type': 'Financial Records / Bank Statements',
        'mre_rule': 'MRE 803(6), 902(11)',
        'authentication_method': 'Business records exception — bank custodian certification',
        'foundation_questions': [
            'Are these your bank/financial records?',
            'Do they accurately reflect your financial transactions?',
            'Were they obtained directly from the financial institution?',
        ],
        'custodian_affidavit': True,
        'notes': 'Bank statements are self-authenticating with certification. Useful for IFP applications.',
    },
    {
        'type': 'Social Media Posts',
        'mre_rule': 'MRE 901(b)(1), 901(b)(4)',
        'authentication_method': 'Distinctive characteristics + witness testimony + platform data',
        'foundation_questions': [
            'Do you recognize this social media profile as belonging to [person]?',
            'How do you know this is their profile?',
            'Did you see this post on [date]?',
            'Is this screenshot a complete and accurate copy of the post?',
        ],
        'custodian_affidavit': False,
        'notes': 'Screenshot with URL, username, date visible. Archive.org/Wayback Machine can preserve. Courts increasingly accept social media with proper foundation.',
    },
]

def main():
    print("=" * 70)
    print("EVIDENCE AUTHENTICATION CHECKLIST — Tool #104")
    print("=" * 70)
    
    lines = [
        "# 🔐 EVIDENCE AUTHENTICATION CHECKLIST",
        f"*Generated: {datetime.now().strftime('%Y-%m-%d %H:%M')} | Tool #104*",
        "*CARRY TO EVERY HEARING — know how to get your evidence admitted*\n",
        "---\n",
    ]
    
    for ev in EVIDENCE_TYPES:
        lines.extend([
            f"## {ev['type']}",
            f"**Rule:** {ev['mre_rule']}",
            f"**Method:** {ev['authentication_method']}",
            f"**Custodian Affidavit Needed:** {'✅ YES' if ev['custodian_affidavit'] else '❌ No'}\n",
            "**Foundation Questions:**",
        ])
        for q in ev['foundation_questions']:
            lines.append(f"- \"{q}\"")
        lines.append(f"\n**Notes:** {ev['notes']}\n")
        lines.append("---\n")
        
        affidavit = " [AFFIDAVIT NEEDED]" if ev['custodian_affidavit'] else ""
        print(f"  📋 {ev['type'][:30]}: {ev['mre_rule']}{affidavit}")
    
    lines.extend([
        "## ⚡ QUICK AUTHENTICATION GUIDE\n",
        "1. **Before hearing**: Prepare authentication for EVERY exhibit",
        "2. **At hearing**: Lay foundation before offering exhibit",
        "3. **Magic words**: \"Your Honor, I offer Exhibit [X] for identification.\"",
        "4. **After foundation**: \"Your Honor, I move to admit Exhibit [X] into evidence.\"",
        "5. **If objected**: Address the specific objection — usually foundation or hearsay",
        "",
        f"*Evidence Authentication Checklist — Tool #104 — {len(EVIDENCE_TYPES)} evidence types covered*",
    ])
    
    md_path = REPORTS_DIR / "AUTHENTICATION_CHECKLIST.md"
    md_path.write_text('\n'.join(lines), encoding='utf-8')
    
    json_path = REPORTS_DIR / "authentication_checklist.json"
    json_path.write_text(json.dumps({
        'generated': datetime.now().isoformat(),
        'tool': 'Evidence Authentication Checklist (#104)',
        'evidence_types': len(EVIDENCE_TYPES),
        'types': [{'type': e['type'], 'rule': e['mre_rule'], 
                   'needs_affidavit': e['custodian_affidavit']} for e in EVIDENCE_TYPES],
    }, indent=2), encoding='utf-8')
    
    print(f"\n✅ {len(EVIDENCE_TYPES)} evidence types with authentication checklists")
    print(f"   {sum(1 for e in EVIDENCE_TYPES if e['custodian_affidavit'])} types need custodian affidavits")
    print(f"   Reports: AUTHENTICATION_CHECKLIST.md + authentication_checklist.json")

if __name__ == '__main__':
    main()
