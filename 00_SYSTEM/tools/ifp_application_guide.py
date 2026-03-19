#!/usr/bin/env python3
"""Tool #189 — IFP (In Forma Pauperis) Application Guide.
Complete guide for applying for fee waivers in Michigan state
and federal courts. Templates and checklists."""

import json, os, sys
sys.stdout = open(sys.stdout.fileno(), mode='w', encoding='utf-8', errors='replace')

REPORT_DIR = os.path.join(os.path.dirname(__file__), '..', 'reports')
os.makedirs(REPORT_DIR, exist_ok=True)

def build_ifp_guide():
    guide = {
        "tool_id": 189,
        "title": "IN FORMA PAUPERIS (IFP) APPLICATION GUIDE",
        "subtitle": "Fee Waiver Strategy for ALL Courts — State + Federal",
        "courts": []
    }

    guide["courts"].append({
        "court": "Michigan Circuit Court (14th Circuit)",
        "form": "MC 20 — Fee Waiver Request",
        "authority": "MCR 2.002",
        "requirements": [
            "Affidavit of indigency (income, assets, expenses, dependents)",
            "Proof of income (pay stubs, tax returns, benefits statements)",
            "Proof of government assistance (if applicable)",
            "List of all assets and liabilities",
        ],
        "tips": [
            "Michigan uses 125% of federal poverty line as guideline",
            "Single person 2024: $18,225/year ($1,519/month) = auto-qualify",
            "If above 125% but still unable to afford: explain circumstances in detail",
            "Include litigation costs already incurred (travel, copies, postage)",
            "Judge has discretion — be thorough and honest in the affidavit",
        ],
        "fees_waived": ["Filing fees", "Service fees", "Transcript fees (MCR 8.108(3))", "Appeal fees", "Certified copy fees"],
    })

    guide["courts"].append({
        "court": "Michigan Court of Appeals",
        "form": "MC 20 — same form as circuit court",
        "authority": "MCR 7.202(6)(c)",
        "requirements": [
            "Same MC 20 affidavit of indigency",
            "If granted at circuit level, COA usually honors it",
            "If not previously granted, file fresh MC 20 with COA",
        ],
        "tips": [
            "COA filing fee is $375 — IFP waives this entirely",
            "File MC 20 WITH the claim of appeal (same day)",
            "If denied, can file motion for reconsideration within 21 days",
        ],
        "fees_waived": ["$375 filing fee", "Transcript ordering fees", "Brief printing/copying fees"],
    })

    guide["courts"].append({
        "court": "Michigan Supreme Court",
        "form": "MC 20 + MSC-specific supplement",
        "authority": "MCR 7.302(B)",
        "requirements": [
            "MC 20 affidavit of indigency",
            "Prior IFP orders from lower courts (if any)",
            "Description of case and why review is warranted",
        ],
        "tips": [
            "MSC filing fee is $375 — IFP waives this",
            "Include prior IFP grants to show established indigency",
            "MSC has broad discretion — focus on meritorious legal issues",
        ],
        "fees_waived": ["$375 application fee", "Printing fees", "Service fees"],
    })

    guide["courts"].append({
        "court": "Federal Court (USDC Western District Michigan)",
        "form": "AO 239 — Application to Proceed Without Prepaying Fees",
        "authority": "28 USC §1915",
        "requirements": [
            "AO 239 affidavit (different from state MC 20)",
            "Monthly income from ALL sources",
            "Monthly expenses itemized",
            "All assets (bank accounts, vehicles, property)",
            "All debts and obligations",
            "Employment history (last 12 months)",
            "Dependents and their ages",
        ],
        "tips": [
            "Federal IFP is broader — 28 USC §1915(a) allows ANY person to apply",
            "Filing fee is $405 — IFP waives completely",
            "Federal courts also waive service of process costs (US Marshal serves for free)",
            "Pro se litigants get liberal construction — Haines v Kerner 404 US 519",
            "If denied, can appeal to magistrate judge, then district judge",
            "Partial IFP: court may allow installment payments if not fully indigent",
        ],
        "fees_waived": ["$405 filing fee", "Service of process fees (US Marshal serves free)", "Transcript fees", "Witness fees", "Appeal fees to 6th Circuit"],
    })

    guide["courts"].append({
        "court": "Judicial Tenure Commission (JTC)",
        "form": "No filing fee",
        "authority": "Const 1963 Art 6 §30",
        "requirements": [
            "NO FEE TO FILE — JTC complaints are always free",
            "Standard complaint form available at courts.michigan.gov/jtc",
        ],
        "tips": [
            "JTC complaints are FREE — no IFP needed",
            "Focus on specific Canon violations with dates and evidence",
        ],
        "fees_waived": ["No fees — JTC complaints are always free"],
    })

    guide["courts"].append({
        "court": "Attorney Grievance Commission (AGC)",
        "form": "Request for Investigation form",
        "authority": "MCR 9.104",
        "requirements": [
            "NO FEE TO FILE — grievance complaints are always free",
            "Standard form available at agc.michigan.gov",
        ],
        "tips": [
            "AGC complaints are FREE — no IFP needed",
            "Specify bar number of attorney (Barnes: P55406)",
            "Include specific MRPC rules violated",
        ],
        "fees_waived": ["No fees — grievance complaints are always free"],
    })

    guide["total_savings"] = "$1,215+ (circuit $175 + COA $375 + MSC $375 + federal $405) — all waived with IFP"
    guide["total_courts"] = len(guide["courts"])

    return guide

def main():
    guide = build_ifp_guide()
    
    md_path = os.path.join(REPORT_DIR, 'IFP_APPLICATION_GUIDE.md')
    with open(md_path, 'w', encoding='utf-8') as f:
        f.write(f"# {guide['title']}\n\n*{guide['subtitle']}*\n\n")
        f.write(f"**{guide['total_courts']} courts | Total savings: {guide['total_savings']}**\n\n")
        for court in guide["courts"]:
            f.write(f"## {court['court']}\n\n")
            f.write(f"**Form:** {court['form']}\n")
            f.write(f"**Authority:** {court['authority']}\n\n")
            f.write("### Requirements\n")
            for r in court["requirements"]:
                f.write(f"- {r}\n")
            f.write("\n### Tips\n")
            for t in court["tips"]:
                f.write(f"- {t}\n")
            f.write("\n### Fees Waived\n")
            for fee in court["fees_waived"]:
                f.write(f"- ✅ {fee}\n")
            f.write("\n---\n\n")
        f.write(f"**TOTAL SAVINGS: {guide['total_savings']}**\n")
    
    json_path = os.path.join(REPORT_DIR, 'ifp_application_guide.json')
    with open(json_path, 'w', encoding='utf-8') as f:
        json.dump(guide, f, indent=2)
    
    print(f"Tool #189 — IFP APPLICATION GUIDE")
    print(f"  {guide['total_courts']} courts | Savings: {guide['total_savings']}")
    print(f"  Reports: {md_path}")

if __name__ == '__main__':
    main()
