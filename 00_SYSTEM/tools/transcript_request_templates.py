#!/usr/bin/env python3
"""Tool #188 — Court Reporter / Transcript Request Templates.
Templates for requesting court transcripts and managing transcript evidence."""

import json, os, sys
sys.stdout = open(sys.stdout.fileno(), mode='w', encoding='utf-8', errors='replace')

REPORT_DIR = os.path.join(os.path.dirname(__file__), '..', 'reports')
os.makedirs(REPORT_DIR, exist_ok=True)

def build_transcript_templates():
    templates = {
        "tool_id": 188,
        "title": "COURT TRANSCRIPT REQUEST TEMPLATES",
        "subtitle": "Templates for Requesting, Managing, and Using Transcript Evidence",
        "sections": []
    }

    templates["sections"].append({
        "title": "TRANSCRIPT REQUEST LETTER",
        "template": {
            "to": "Court Reporter, 14th Circuit Court, 990 Terrace Street, Muskegon, MI 49442",
            "subject": "REQUEST FOR COURT TRANSCRIPTS — Case No. [CASE_NUMBER]",
            "body_elements": [
                "Identification: Andrew James Pigors, Plaintiff, pro se",
                "Case number(s): 2024-001507-DC, 2023-5907-PP",
                "Hearing dates requested: [SPECIFIC DATES]",
                "Judge: Hon. Jenny L. McNeill",
                "Purpose: Appeal preparation / Federal complaint evidence",
                "IFP status: If IFP granted, request fee waiver per MCR 8.108(3)",
                "Format: Certified copy, paper and electronic (PDF)",
                "Delivery: Mail to 1977 Whitehall Road, Lot 17, North Muskegon, MI 49445",
            ],
            "fee_note": "Standard rate: ~$3.25/page. IFP waiver applies if granted. Request cost estimate first.",
        }
    })

    templates["sections"].append({
        "title": "PRIORITY TRANSCRIPTS TO REQUEST",
        "hearings": [
            {"hearing": "Initial PPO hearing (2023)", "reason": "Foundation of fraud — Emily's original false testimony", "priority": "CRITICAL"},
            {"hearing": "Custody hearing (2024)", "reason": "McNeill's bias visible in rulings and comments", "priority": "CRITICAL"},
            {"hearing": "Any hearing where Andrew was denied opportunity to speak", "reason": "Due process violation evidence", "priority": "HIGH"},
            {"hearing": "Emily's ex-parte motion (Aug 2025)", "reason": "Lack of required findings per MCL 722.27a(3)", "priority": "HIGH"},
            {"hearing": "Any hearing involving Barnes (P55406)", "reason": "Pattern of collusion between Barnes and McNeill", "priority": "MEDIUM"},
            {"hearing": "All status conferences", "reason": "McNeill's off-record comments and directives", "priority": "MEDIUM"},
        ]
    })

    templates["sections"].append({
        "title": "TRANSCRIPT ANALYSIS CHECKLIST",
        "checklist": [
            "Identify every instance where McNeill cut off Andrew's testimony",
            "Identify every instance where McNeill accepted Emily's claims without evidence",
            "Identify every ex parte communication referenced",
            "Identify every denial of Andrew's motions",
            "Identify every time McNeill cited a statute or rule — verify accuracy",
            "Identify every factual statement by Emily that contradicts other evidence",
            "Identify every threat or warning directed at Andrew",
            "Identify timeline of events per testimony (for contradiction analysis)",
            "Mark potential perjury with page/line citations",
            "Cross-reference with evidence_quotes table in litigation_context.db",
        ]
    })

    templates["sections"].append({
        "title": "USING TRANSCRIPTS IN FILINGS",
        "rules": [
            {"rule": "Citation format", "text": "Tr. [Date] at p. [page], ll. [lines] (e.g., Tr. 03/15/2024 at p. 47, ll. 5-12)"},
            {"rule": "Certification", "text": "All transcript excerpts must be from certified copies"},
            {"rule": "Context", "text": "Include sufficient surrounding context to avoid misleading excerpts"},
            {"rule": "Accuracy", "text": "Quote verbatim — never paraphrase in sworn filings"},
            {"rule": "Exhibit marking", "text": "Attach relevant transcript pages as numbered exhibits"},
            {"rule": "Hearsay", "text": "Transcript testimony is NOT hearsay — it's prior testimony (MRE 801(d)(1))"},
            {"rule": "Impeachment", "text": "Use transcript inconsistencies to impeach at future hearings (MRE 613)"},
        ]
    })

    templates["total_items"] = sum(
        len(s.get("body_elements", s.get("hearings", s.get("checklist", s.get("rules", [])))))
        for s in templates["sections"]
    )

    return templates

def main():
    t = build_transcript_templates()
    
    md_path = os.path.join(REPORT_DIR, 'TRANSCRIPT_REQUEST_TEMPLATES.md')
    with open(md_path, 'w', encoding='utf-8') as f:
        f.write(f"# {t['title']}\n\n*{t['subtitle']}*\n\n")
        f.write(f"**{len(t['sections'])} sections | {t['total_items']} items**\n\n")
        for sec in t["sections"]:
            f.write(f"## {sec['title']}\n\n")
            if "template" in sec:
                tmpl = sec["template"]
                f.write(f"**To:** {tmpl['to']}\n\n")
                f.write(f"**Re:** {tmpl['subject']}\n\n")
                for elem in tmpl["body_elements"]:
                    f.write(f"- {elem}\n")
                f.write(f"\n*{tmpl['fee_note']}*\n\n")
            if "hearings" in sec:
                for h in sec["hearings"]:
                    f.write(f"- **{h['hearing']}** [{h['priority']}]\n  {h['reason']}\n\n")
            if "checklist" in sec:
                for i, item in enumerate(sec["checklist"], 1):
                    f.write(f"{i}. {item}\n")
                f.write("\n")
            if "rules" in sec:
                for r in sec["rules"]:
                    f.write(f"- **{r['rule']}:** {r['text']}\n")
                f.write("\n")
        f.write(f"---\n*Tool #188 | {t['total_items']} items*\n")
    
    json_path = os.path.join(REPORT_DIR, 'transcript_request_templates.json')
    with open(json_path, 'w', encoding='utf-8') as f:
        json.dump(t, f, indent=2)
    
    print(f"Tool #188 — COURT TRANSCRIPT REQUEST TEMPLATES")
    print(f"  {len(t['sections'])} sections | {t['total_items']} items")
    print(f"  Reports: {md_path}")

if __name__ == '__main__':
    main()
