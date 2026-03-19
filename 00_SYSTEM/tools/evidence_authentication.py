#!/usr/bin/env python3
"""
Tool #149 — Evidence Authentication Checklist
=================================================
🆕 NOVEL TOOL — For every piece of evidence Andrew wants
to use in court, this ensures it can be properly authenticated
per Michigan Rules of Evidence (MRE).
"""
import sys, json
from pathlib import Path
from datetime import datetime

sys.stdout = open(sys.stdout.fileno(), mode='w', encoding='utf-8', errors='replace')

REPO = Path(r"C:\Users\andre\LitigationOS")
REPORTS_DIR = REPO / "00_SYSTEM" / "reports"

EVIDENCE_TYPES = [
    {
        'type': 'Text Messages / Chat Logs',
        'mre_rule': 'MRE 901(b)(1) — testimony of person with knowledge',
        'authentication_steps': [
            'Screenshot showing sender, recipient, date/time, and content',
            'Provide metadata (phone number, app name, account owner)',
            'Testify: "I personally sent/received this message on [date]"',
            'If from Emily: show phone number matches known number',
            'Best: export full conversation thread (not just selected messages)',
        ],
        'objections_to_expect': [
            'Hearsay — response: admissions by party-opponent (MRE 801(d)(2))',
            'Lack of foundation — response: testify to personal knowledge',
            'Authenticity — response: metadata + context establishes authenticity',
        ],
    },
    {
        'type': 'Emails',
        'mre_rule': 'MRE 901(b)(4) — distinctive characteristics',
        'authentication_steps': [
            'Print with full headers (to, from, date, subject)',
            'Show email address matches known party',
            'Testify: "I received this email at [address] on [date]"',
            'If forwarded: show original headers preserved',
        ],
        'objections_to_expect': [
            'Could be fabricated — response: headers + email provider records',
            'Hearsay — response: party-opponent admission (MRE 801(d)(2))',
        ],
    },
    {
        'type': 'Court Documents / Orders',
        'mre_rule': 'MRE 902(1) — self-authenticating public documents',
        'authentication_steps': [
            'Get CERTIFIED copies from the court clerk ($1/page + $10 cert)',
            'Certified copies are self-authenticating — no further foundation needed',
            'Stamp/seal from clerk = authenticated',
        ],
        'objections_to_expect': [
            'Almost none if properly certified — self-authentication is powerful',
        ],
    },
    {
        'type': 'Photographs / Videos',
        'mre_rule': 'MRE 901(b)(1) — testimony that photo accurately depicts scene',
        'authentication_steps': [
            'Testify: "I took this photo on [date] at [location]"',
            'Show EXIF data if available (date, location, device)',
            'If others took it: get their testimony or affidavit',
            'For screenshots: show device, date, and context',
        ],
        'objections_to_expect': [
            'Could be manipulated — response: EXIF data + originals available',
            'Relevance — response: explain how photo relates to claim',
        ],
    },
    {
        'type': 'ChatGPT / AI Chat Exports',
        'mre_rule': 'MRE 901(b)(9) — process or system evidence',
        'authentication_steps': [
            'Export full conversation from ChatGPT account',
            'Show account ownership (email, login, settings page)',
            'Testify: "I exported this from my ChatGPT account at [email]"',
            'Show timestamps and conversation continuity',
            'If used to document events: explain context of each entry',
        ],
        'objections_to_expect': [
            'Novel evidence type — response: same authentication as any digital record',
            'Hearsay — response: present purpose or state of mind exception',
            'Not reliable — response: consistent with other evidence, used as documentation tool',
        ],
    },
    {
        'type': 'Financial Records',
        'mre_rule': 'MRE 803(6) — business records exception',
        'authentication_steps': [
            'Get records from bank/employer directly',
            'Custodian of records affidavit if available',
            'Testify: "I obtained these records from [institution] on [date]"',
            'Show account ownership matches party',
        ],
        'objections_to_expect': [
            'Hearsay — response: business records exception MRE 803(6)',
            'Relevance — response: shows financial capacity (BIF Factor C)',
        ],
    },
]

def main():
    print("=" * 70)
    print("EVIDENCE AUTHENTICATION CHECKLIST — Tool #149")
    print("=" * 70)

    total_steps = sum(len(e['authentication_steps']) for e in EVIDENCE_TYPES)
    total_objections = sum(len(e['objections_to_expect']) for e in EVIDENCE_TYPES)

    lines = [
        "# ✅ EVIDENCE AUTHENTICATION CHECKLIST",
        f"*Generated: {datetime.now().strftime('%Y-%m-%d %H:%M')} | Tool #149*",
        f"*{len(EVIDENCE_TYPES)} evidence types · {total_steps} auth steps · {total_objections} objection responses*\n",
        "---\n",
        "## QUICK REFERENCE\n",
        "| Evidence Type | MRE Rule | Steps |",
        "|--------------|----------|-------|",
    ]

    for e in EVIDENCE_TYPES:
        lines.append(f"| {e['type']} | {e['mre_rule'][:40]} | {len(e['authentication_steps'])} |")
        print(f"  ✅ {e['type']}: {len(e['authentication_steps'])} steps")

    lines.extend(["", "---\n"])

    for e in EVIDENCE_TYPES:
        lines.append(f"## {e['type']}")
        lines.append(f"**Rule:** {e['mre_rule']}\n")
        lines.append("### Authentication Steps:")
        for step in e['authentication_steps']:
            lines.append(f"- [ ] {step}")
        lines.append("\n### Objections to Expect & Responses:")
        for obj in e['objections_to_expect']:
            lines.append(f"- ⚠️ {obj}")
        lines.append("\n---\n")

    lines.append(f"*{len(EVIDENCE_TYPES)} types · {total_steps} steps · {total_objections} objection responses*")

    md_path = REPORTS_DIR / "EVIDENCE_AUTHENTICATION.md"
    md_path.write_text('\n'.join(lines), encoding='utf-8')

    json_path = REPORTS_DIR / "evidence_authentication.json"
    json_path.write_text(json.dumps({
        'generated': datetime.now().isoformat(),
        'tool': 'Evidence Authentication Checklist (#149)',
        'types': len(EVIDENCE_TYPES),
        'total_steps': total_steps,
        'total_objections': total_objections,
    }, indent=2), encoding='utf-8')

    print(f"\n✅ {len(EVIDENCE_TYPES)} evidence types with {total_steps} auth steps + {total_objections} objection responses")
    print(f"   Reports: EVIDENCE_AUTHENTICATION.md + evidence_authentication.json")

if __name__ == '__main__':
    main()
