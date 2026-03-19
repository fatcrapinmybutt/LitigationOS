#!/usr/bin/env python3
"""Tool #186v2 — Evidence Authentication Checklist.
Michigan Rules of Evidence (MRE) authentication requirements
for every evidence type in the arsenal."""

import json, os, sys
sys.stdout = open(sys.stdout.fileno(), mode='w', encoding='utf-8', errors='replace')

REPORT_DIR = os.path.join(os.path.dirname(__file__), '..', 'reports')
os.makedirs(REPORT_DIR, exist_ok=True)

def build_auth_checklist():
    checklist = {
        "tool_id": 186,
        "version": 2,
        "title": "EVIDENCE AUTHENTICATION CHECKLIST v2",
        "subtitle": "Michigan Rules of Evidence — Authentication for Every Evidence Type",
        "types": [
            {
                "type": "Text Messages / SMS", "rule": "MRE 901(b)(1), (b)(4)",
                "steps": ["Screenshot with phone number and contact name", "Metadata with date/time stamps", "Testimony identifying sender's number", "Content referencing details only sender would know", "Phone carrier records (subpoena if needed)"],
                "defense": "Self-authentication by distinctive characteristics — MRE 901(b)(4)"
            },
            {
                "type": "Emails", "rule": "MRE 901(b)(1), (b)(4)",
                "steps": ["Full email headers (From/To/Date/Subject)", "Email address identification", "Chain of custody from receipt to court", "Reply doctrine: reply chain authenticates both"],
                "defense": "Reply doctrine + distinctive characteristics"
            },
            {
                "type": "Social Media Posts", "rule": "MRE 901(b)(1), (b)(4)",
                "steps": ["Screenshot with URL, profile name, date visible", "Archive.org/Wayback copy if available", "Testimony identifying account as party's", "Content consistent with party's known statements"],
                "defense": "Screenshots + testimony + distinctive content"
            },
            {
                "type": "Court Records / Orders", "rule": "MRE 901(b)(7), 902(4)",
                "steps": ["Certified copy from court clerk (self-authenticating)", "Case number and judge visible", "Court seal/stamp present"],
                "defense": "Self-authenticating — MRE 902(4)"
            },
            {
                "type": "Photographs", "rule": "MRE 901(b)(1)",
                "steps": ["Testimony that photo accurately depicts scene", "EXIF metadata (date/time/location)", "Chain of custody from capture to court", "Original unedited file with hash"],
                "defense": "Fair and accurate depiction testimony"
            },
            {
                "type": "Audio / Video Recordings", "rule": "MRE 901(b)(1), (b)(5)",
                "steps": ["Testimony identifying voices/persons", "Original file with metadata preserved", "No gaps or undisclosed edits", "MI is ONE-PARTY CONSENT — MCL 750.539c", "Transcription provided to court and opposing party"],
                "defense": "Voice identification + one-party consent"
            },
            {
                "type": "Medical / Mental Health Records", "rule": "MRE 803(6), 902(11)",
                "steps": ["Certified copy from provider", "Business records affidavit — MRE 803(6)", "HIPAA-compliant release on file", "Records custodian certification"],
                "defense": "Business records exception — MRE 803(6)"
            },
            {
                "type": "Financial Records", "rule": "MRE 803(6), 902(11)",
                "steps": ["Certified copy from institution", "Business records affidavit", "Tax returns: certified from IRS or MI Treasury"],
                "defense": "Business records exception + certified copies"
            },
            {
                "type": "Police / CPS Reports", "rule": "MRE 803(8), 902(4)",
                "steps": ["Certified copy from agency (self-authenticating)", "Report number and officer identification", "MRE 803(8) public records exception"],
                "defense": "Public records exception — MRE 803(8)"
            },
            {
                "type": "Affidavits / Declarations", "rule": "MCR 2.119(B)",
                "steps": ["Signed under oath before notary", "Notary seal, signature, commission expiration", "Personal knowledge stated (MRE 602)", "Specific facts not conclusions"],
                "defense": "Sworn under penalty of perjury — MCL 600.1561a"
            },
        ]
    }
    checklist["total_types"] = len(checklist["types"])
    checklist["total_steps"] = sum(len(t["steps"]) for t in checklist["types"])
    return checklist

def main():
    cl = build_auth_checklist()
    md_path = os.path.join(REPORT_DIR, 'EVIDENCE_AUTHENTICATION_V2.md')
    with open(md_path, 'w', encoding='utf-8') as f:
        f.write(f"# {cl['title']}\n\n*{cl['subtitle']}*\n\n")
        f.write(f"**{cl['total_types']} evidence types | {cl['total_steps']} authentication steps**\n\n")
        for t in cl["types"]:
            f.write(f"## {t['type']}\n*Rule: {t['rule']}*\n\n")
            for i, s in enumerate(t["steps"], 1):
                f.write(f"{i}. {s}\n")
            f.write(f"\n**Defense:** {t['defense']}\n\n")
        f.write(f"---\n*Tool #186v2 | {cl['total_types']} types, {cl['total_steps']} steps*\n")
    json_path = os.path.join(REPORT_DIR, 'evidence_authentication_v2.json')
    with open(json_path, 'w', encoding='utf-8') as f:
        json.dump(cl, f, indent=2)
    print(f"Tool #186v2 — EVIDENCE AUTHENTICATION CHECKLIST")
    print(f"  {cl['total_types']} evidence types | {cl['total_steps']} steps")
    print(f"  Reports: {md_path}")

if __name__ == '__main__':
    main()
