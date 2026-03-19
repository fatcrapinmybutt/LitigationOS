#!/usr/bin/env python3
"""Tool #197 — Case Law Quick Reference Cards.
Key authorities for each legal theory — carry to court."""

import json, os, sys
sys.stdout = open(sys.stdout.fileno(), mode='w', encoding='utf-8', errors='replace')

REPORT_DIR = os.path.join(os.path.dirname(__file__), '..', 'reports')
os.makedirs(REPORT_DIR, exist_ok=True)

def build_case_law_cards():
    cards = {
        "tool_id": 197,
        "title": "CASE LAW QUICK REFERENCE CARDS",
        "subtitle": "Key Authorities for Court — Organized by Legal Theory",
        "theories": [
            {
                "theory": "Parental Rights as Fundamental Liberty",
                "cases": [
                    {"case": "Troxel v Granville, 530 US 57 (2000)", "holding": "Parents have fundamental liberty interest in care and custody of children", "use": "ANY hearing where parenting time is at issue"},
                    {"case": "Santosky v Kramer, 455 US 745 (1982)", "holding": "Clear and convincing standard required before terminating parental rights", "use": "Challenge any order that effectively terminates contact"},
                    {"case": "Stanley v Illinois, 405 US 645 (1972)", "holding": "Unwed fathers have protected liberty interest in parental relationship", "use": "Establish Andrew's equal parental standing"},
                ]
            },
            {
                "theory": "Judicial Disqualification",
                "cases": [
                    {"case": "Caperton v Massey, 556 US 868 (2009)", "holding": "Due process requires recusal when probability of bias is too high", "use": "Motion to disqualify McNeill"},
                    {"case": "Crampton v Dept of State, 395 Mich 347 (1975)", "holding": "Objective test for judicial bias — appearance of impropriety sufficient", "use": "Michigan-specific disqualification standard"},
                    {"case": "Armstrong v Ypsilanti, 248 Mich App 573 (2001)", "holding": "Pattern of conduct establishes bias — no need for single smoking gun", "use": "1,127 violations constitute a pattern"},
                ]
            },
            {
                "theory": "Federal §1983 Civil Rights",
                "cases": [
                    {"case": "Dennis v Sparks, 449 US 24 (1980)", "holding": "Private parties who conspire with judge lose state-action immunity", "use": "Include Emily, Berry, Barnes as co-defendants"},
                    {"case": "Catz v Chalker, 142 F.3d 279 (6th Cir 1998)", "holding": "§1983 claims for custody interference are NOT barred by domestic relations exception", "use": "Overcome jurisdiction objection"},
                    {"case": "Thaddeus-X v Blatter, 175 F.3d 378 (6th Cir 1999)", "holding": "1st Amendment retaliation: protected activity + adverse action + causal connection", "use": "McNeill retaliated for Andrew filing motions"},
                ]
            },
            {
                "theory": "Fraud Upon the Court",
                "cases": [
                    {"case": "Hazel-Atlas Glass v Hartford, 322 US 238 (1944)", "holding": "Courts have inherent power to vacate judgments obtained by fraud", "use": "Vacate ALL orders based on Emily's fraud"},
                    {"case": "Chambers v NASCO, 501 US 32 (1991)", "holding": "Inherent power to sanction fraud includes full costs and fees", "use": "Sanctions against Emily and Barnes"},
                    {"case": "Aoude v Mobil Oil, 892 F.2d 1115 (1st Cir 1989)", "holding": "Party who obtains judgment through perjury forfeits all claims", "use": "Emily's perjury voids her custody position"},
                ]
            },
            {
                "theory": "Parenting Time / Make-Up Time",
                "cases": [
                    {"case": "MCL 722.27a(1)", "holding": "Parenting time SHALL be granted — presumption in favor", "use": "Restoration argument"},
                    {"case": "MCL 722.27a(3)", "holding": "Suspension ONLY with clear and convincing evidence of danger", "use": "Challenge suspension — no such finding made"},
                    {"case": "MCL 722.27a(8)", "holding": "Court SHALL provide make-up time for wrongfully denied visits", "use": "Calculate and demand make-up overnights"},
                ]
            },
            {
                "theory": "Void Judgment / Relief from Judgment",
                "cases": [
                    {"case": "MCR 2.612(C)(1)(c)", "holding": "Relief from judgment for fraud — within 1 year", "use": "Vacate recent orders"},
                    {"case": "MCR 2.612(C)(1)(d)", "holding": "Void judgment — NO time limit", "use": "Orders entered without jurisdiction/due process are void ab initio"},
                    {"case": "MCR 2.612(C)(3)", "holding": "Independent action for fraud on court — NO time bar", "use": "Attack foundational fraud at any time"},
                ]
            },
        ]
    }
    cards["total_theories"] = len(cards["theories"])
    cards["total_cases"] = sum(len(t["cases"]) for t in cards["theories"])
    return cards

def main():
    c = build_case_law_cards()
    md_path = os.path.join(REPORT_DIR, 'CASE_LAW_REFERENCE_CARDS.md')
    with open(md_path, 'w', encoding='utf-8') as f:
        f.write(f"# {c['title']}\n\n*{c['subtitle']}*\n\n")
        f.write(f"**{c['total_theories']} theories | {c['total_cases']} authorities**\n\n")
        for theory in c["theories"]:
            f.write(f"## {theory['theory']}\n\n")
            for case in theory["cases"]:
                f.write(f"### {case['case']}\n")
                f.write(f"**Holding:** {case['holding']}\n\n")
                f.write(f"**Use:** {case['use']}\n\n")
        f.write(f"---\n*Tool #197 | {c['total_cases']} authorities — CARRY TO COURT*\n")
    json_path = os.path.join(REPORT_DIR, 'case_law_reference_cards.json')
    with open(json_path, 'w', encoding='utf-8') as f:
        json.dump(c, f, indent=2)
    print(f"Tool #197 — CASE LAW QUICK REFERENCE CARDS")
    print(f"  {c['total_theories']} theories | {c['total_cases']} authorities")
    print(f"  Reports: {md_path}")

if __name__ == '__main__':
    main()
