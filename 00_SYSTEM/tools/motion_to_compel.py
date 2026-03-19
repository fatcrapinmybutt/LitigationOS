#!/usr/bin/env python3
"""Tool #191 — Motion to Compel Discovery Template.
When Emily or Berry refuse to produce documents, this motion forces compliance."""

import json, os, sys
sys.stdout = open(sys.stdout.fileno(), mode='w', encoding='utf-8', errors='replace')

REPORT_DIR = os.path.join(os.path.dirname(__file__), '..', 'reports')
os.makedirs(REPORT_DIR, exist_ok=True)

def build_motion_to_compel():
    motion = {
        "tool_id": 191,
        "title": "MOTION TO COMPEL DISCOVERY — TEMPLATE & GUIDE",
        "subtitle": "Force Production of Documents Emily/Berry Are Withholding",
        "sections": []
    }

    motion["sections"].append({
        "title": "REQUIRED ELEMENTS",
        "elements": [
            {"element": "Caption with case number 2024-001507-DC", "authority": "MCR 2.113(A)"},
            {"element": "Statement that good faith conference was attempted per MCR 2.313(A)(1)", "note": "MUST certify you tried to resolve without court intervention"},
            {"element": "Specific discovery requests that were served", "note": "List each interrogatory/document request by number"},
            {"element": "Date discovery was served and response deadline", "authority": "MCR 2.309(B) — 28 days to respond"},
            {"element": "Description of deficient or missing responses", "note": "Be specific about what was not provided"},
            {"element": "Relevance of requested information", "note": "Explain why each item matters to custody/fraud claims"},
            {"element": "Request for sanctions under MCR 2.313(B)(2)", "note": "Costs of bringing motion + evidentiary sanctions"},
            {"element": "Proposed order for court signature", "authority": "MCR 2.119(A)(2)"},
        ]
    })

    motion["sections"].append({
        "title": "DISCOVERY ITEMS TO COMPEL",
        "items": [
            {"item": "All text messages between Emily and Berry regarding L.D.W. or Andrew", "reason": "Conspiracy evidence", "priority": "CRITICAL"},
            {"item": "Emily's phone records (call log) for 2023-2025", "reason": "Pattern of coordination with Berry/Barnes/McNeill", "priority": "HIGH"},
            {"item": "Berry's employment and criminal records", "reason": "Fitness assessment for household contact with L.D.W.", "priority": "HIGH"},
            {"item": "All communications between Berry and Barnes (P55406)", "reason": "Conspiracy evidence — Berry is NOT Barnes's client, no privilege", "priority": "CRITICAL"},
            {"item": "Emily's social media posts (Facebook, Instagram) 2023-2025", "reason": "Contradictions to sworn statements", "priority": "HIGH"},
            {"item": "Medical records for L.D.W. since separation", "reason": "Best interest factor analysis + potential neglect evidence", "priority": "HIGH"},
            {"item": "Emily's financial records (income, expenses, assets)", "reason": "Child support calculation + potential hidden assets", "priority": "MEDIUM"},
            {"item": "Photos/videos of L.D.W. since Aug 2025 suspension", "reason": "Child welfare assessment during denial of father contact", "priority": "MEDIUM"},
        ]
    })

    motion["sections"].append({
        "title": "SANCTIONS FOR NON-COMPLIANCE",
        "sanctions": [
            {"sanction": "MCR 2.313(B)(2)(a) — Order establishing facts as proven", "effect": "Court deems disputed facts true in Andrew's favor"},
            {"sanction": "MCR 2.313(B)(2)(b) — Refuse to allow disobedient party to support/oppose claims", "effect": "Emily cannot use defenses she refused to disclose"},
            {"sanction": "MCR 2.313(B)(2)(c) — Strike pleadings", "effect": "Emily's counterclaims dismissed"},
            {"sanction": "MCR 2.313(B)(2)(d) — Default judgment", "effect": "Andrew wins on all claims — nuclear option"},
            {"sanction": "MCR 2.313(A)(5) — Reasonable expenses including attorney fees", "effect": "Andrew recovers costs of bringing motion (pro se hourly rate)"},
            {"sanction": "Adverse inference instruction", "effect": "Jury/court may infer withheld evidence would be unfavorable to Emily"},
        ]
    })

    motion["sections"].append({
        "title": "GOOD FAITH CONFERENCE CERTIFICATION",
        "template": "I, Andrew James Pigors, hereby certify that on [DATE], I attempted in good faith to resolve this discovery dispute with Emily A. Watson by [METHOD — email/letter/in-person] as required by MCR 2.313(A)(1). Despite my efforts, Defendant has [refused to respond / provided incomplete responses / failed to produce documents]. This motion is therefore necessary to obtain Court intervention.",
        "methods": [
            "Send written request via email and certified mail to Emily at 2160 Garland Drive, Norton Shores, MI 49441",
            "Document date sent and response (or lack thereof)",
            "Wait minimum 7 days for response before filing motion",
            "Keep copies of ALL correspondence as exhibits to the motion",
        ]
    })

    motion["total_elements"] = sum(
        len(s.get("elements", s.get("items", s.get("sanctions", s.get("methods", [])))))
        for s in motion["sections"]
    )

    return motion

def main():
    m = build_motion_to_compel()
    md_path = os.path.join(REPORT_DIR, 'MOTION_TO_COMPEL.md')
    with open(md_path, 'w', encoding='utf-8') as f:
        f.write(f"# {m['title']}\n\n*{m['subtitle']}*\n\n")
        f.write(f"**{len(m['sections'])} sections | {m['total_elements']} total items**\n\n")
        for sec in m["sections"]:
            f.write(f"## {sec['title']}\n\n")
            for item in sec.get("elements", sec.get("items", sec.get("sanctions", []))):
                if isinstance(item, dict):
                    main_text = item.get("element") or item.get("item") or item.get("sanction", "")
                    extra = item.get("authority") or item.get("reason") or item.get("effect", "")
                    f.write(f"- {main_text}\n")
                    if extra:
                        f.write(f"  *{extra}*\n")
                    f.write("\n")
            if "template" in sec:
                f.write(f"### Template Language\n\n> {sec['template']}\n\n")
            if "methods" in sec:
                f.write("### Steps\n")
                for method in sec["methods"]:
                    f.write(f"1. {method}\n")
                f.write("\n")
        f.write(f"---\n*Tool #191 | {m['total_elements']} items*\n")
    json_path = os.path.join(REPORT_DIR, 'motion_to_compel.json')
    with open(json_path, 'w', encoding='utf-8') as f:
        json.dump(m, f, indent=2)
    print(f"Tool #191 — MOTION TO COMPEL DISCOVERY")
    print(f"  {len(m['sections'])} sections | {m['total_elements']} items")
    print(f"  Reports: {md_path}")

if __name__ == '__main__':
    main()
