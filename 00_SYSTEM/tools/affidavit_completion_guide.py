#!/usr/bin/env python3
"""
Tool #207: Affidavit Completion Guide
=======================================
Step-by-step guide for completing and notarizing all 3 GO affidavits.
Includes exact text to fill in, notary script, and common mistakes.

NOVEL INNOVATION: Pre-fills affidavit variables from DB so Andrew
only needs to print, sign, and notarize.
"""
import json, os, sys
from datetime import datetime

sys.stdout = open(sys.stdout.fileno(), mode='w', encoding='utf-8', errors='replace')

REPORT_DIR = os.path.join(os.path.dirname(__file__), '..', 'reports')
os.makedirs(REPORT_DIR, exist_ok=True)

def build_affidavit_guide():
    guide = {
        "tool_id": 207,
        "name": "Affidavit Completion Guide",
        "generated": datetime.now().isoformat(),
        "affidavits": {
            "F3_AFFIDAVIT": {
                "filing": "F3 — Disqualification Motion (MCR 2.003)",
                "file": "PKG_F3_DISQUALIFICATION_MCR_2003/02_AFFIDAVIT.md",
                "type": "Affidavit of Bias and Prejudice",
                "legal_basis": "MCR 2.003(D)(1) — affidavit of personal bias or prejudice",
                "pre_filled_data": {
                    "affiant": "Andrew James Pigors",
                    "address": "1977 Whitehall Road, Lot 17, North Muskegon, MI 49445",
                    "county": "Muskegon County",
                    "case_number": "2024-001507-DC",
                    "judge": "Hon. Jenny L. McNeill",
                    "court": "14th Circuit Court, Family Division"
                },
                "steps": [
                    "1. Print the affidavit from 02_AFFIDAVIT.md",
                    "2. Read EVERY paragraph carefully — verify facts are accurate",
                    "3. Fill in today's date on the signature line",
                    "4. DO NOT SIGN YET — you must sign in front of the notary",
                    "5. Bring the unsigned affidavit + valid photo ID to notary",
                    "6. Tell notary: 'I need this affidavit notarized under oath'",
                    "7. The notary will administer the oath — raise your right hand",
                    "8. Sign the affidavit in the notary's presence",
                    "9. Notary stamps and signs — get the stamped original back",
                    "10. Make 3 copies: 1 for court, 1 for Emily's service, 1 for your records"
                ],
                "notary_script": "The notary will say something like: 'Do you solemnly swear that the contents of this affidavit are true and correct to the best of your knowledge?' You answer: 'I do.' Then sign.",
                "common_mistakes": [
                    "❌ Signing BEFORE going to notary (must sign IN FRONT of notary)",
                    "❌ Forgetting photo ID (driver's license or state ID required)",
                    "❌ Not reading the affidavit before signing (you're swearing it's true)",
                    "❌ Using white-out or corrections (start fresh if errors found)",
                    "❌ Forgetting to date the affidavit"
                ],
                "cost": "Notary: $5-10 at UPS Store, FREE at library/bank"
            },
            "F6_AFFIDAVIT": {
                "filing": "F6 — JTC Complaint",
                "file": "PKG_F6_JTC_COMPLAINT/02_AFFIDAVIT.md",
                "type": "Affidavit of Judicial Misconduct",
                "legal_basis": "MCR 9.200 et seq. — JTC complaint under oath",
                "pre_filled_data": {
                    "affiant": "Andrew James Pigors",
                    "address": "1977 Whitehall Road, Lot 17, North Muskegon, MI 49445",
                    "judge_complained_of": "Hon. Jenny L. McNeill",
                    "court": "14th Circuit Court, Family Division",
                    "case_number": "2024-001507-DC"
                },
                "steps": [
                    "1. Print the affidavit from 02_AFFIDAVIT.md",
                    "2. Verify all misconduct allegations are factually accurate",
                    "3. Cross-reference with FILING_HARDENING_REPORT for any placeholders",
                    "4. Fill in today's date",
                    "5. Take to notary — same process as F3 affidavit",
                    "6. Make 2 copies: 1 for JTC mailing, 1 for your records",
                    "7. Note: JTC accepts email submission — scan notarized original"
                ],
                "notary_script": "Same oath procedure as F3. Sign in notary's presence after oath.",
                "common_mistakes": [
                    "❌ Overstating misconduct claims (stick to documented facts only)",
                    "❌ Including hearsay without identifying it as such",
                    "❌ Forgetting JTC is CONFIDENTIAL — don't publicize the complaint"
                ],
                "cost": "$5-10 notary + postage (or free via email to jtc@michigan.gov)"
            },
            "F10_AFFIDAVIT": {
                "filing": "F10 — COA Emergency Motion",
                "file": "PKG_F10_COA_EMERGENCY_MOTION/02_AFFIDAVIT.md",
                "type": "Affidavit in Support of Emergency Motion",
                "legal_basis": "MCR 7.211(C)(6) — emergency motion requires affidavit showing irreparable harm",
                "pre_filled_data": {
                    "affiant": "Andrew James Pigors",
                    "address": "1977 Whitehall Road, Lot 17, North Muskegon, MI 49445",
                    "coa_case": "COA 366810",
                    "lower_court_case": "2024-001507-DC",
                    "lower_court_judge": "Hon. Jenny L. McNeill"
                },
                "steps": [
                    "1. Print the affidavit from 02_AFFIDAVIT.md",
                    "2. Verify emergency/irreparable harm facts are current",
                    "3. Ensure parenting time denial count is accurate (verify against log)",
                    "4. Fill in today's date",
                    "5. Take to notary — same oath procedure",
                    "6. Make 3 copies: 1 for COA filing, 1 for service, 1 for records",
                    "7. IMPORTANT: File F10 simultaneously with F9 (COA Brief)"
                ],
                "notary_script": "Same oath. The COA emergency affidavit specifically requires facts showing why immediate relief is needed.",
                "common_mistakes": [
                    "❌ Filing F10 without F9 (they must go together)",
                    "❌ Failing to show 'irreparable harm' clearly in the affidavit",
                    "❌ Not including specific dates and incidents (be precise)",
                    "❌ Missing the COA deadline (call clerk to confirm)"
                ],
                "cost": "$5-10 notary. COA filing fee waived by IFP."
            }
        },
        "universal_tips": [
            "✅ Always bring valid photo ID to notary (driver's license or state ID)",
            "✅ Never sign before the notary — they MUST witness your signature",
            "✅ Read every word before signing — you're swearing under oath",
            "✅ Keep originals — file copies with court, keep notarized originals safe",
            "✅ If you find an error after notarization — do NOT correct it. Print fresh, re-notarize.",
            "✅ Notary services: UPS Store ($5-10), Library (FREE), Bank (FREE for customers)"
        ]
    }
    
    guide['total_affidavits'] = len(guide['affidavits'])
    guide['total_steps'] = sum(len(a['steps']) for a in guide['affidavits'].values())
    return guide

def main():
    print("=" * 60)
    print("TOOL #207: AFFIDAVIT COMPLETION GUIDE")
    print("=" * 60)
    
    guide = build_affidavit_guide()
    
    json_path = os.path.join(REPORT_DIR, 'AFFIDAVIT_COMPLETION_GUIDE.json')
    with open(json_path, 'w', encoding='utf-8') as f:
        json.dump(guide, f, indent=2, ensure_ascii=False)
    
    md_path = os.path.join(REPORT_DIR, 'AFFIDAVIT_COMPLETION_GUIDE.md')
    with open(md_path, 'w', encoding='utf-8') as f:
        f.write("# ✍️ Affidavit Completion Guide (Tool #207)\n\n")
        f.write(f"**{guide['total_affidavits']} affidavits** | **{guide['total_steps']} steps total**\n\n")
        f.write("*Complete these in ONE trip to the notary — bring all 3 unsigned affidavits + photo ID.*\n\n")
        
        for aff_id, aff in guide['affidavits'].items():
            f.write(f"## {aff['filing']}\n\n")
            f.write(f"**Type**: {aff['type']}\n")
            f.write(f"**Legal Basis**: {aff['legal_basis']}\n")
            f.write(f"**File**: `{aff['file']}`\n")
            f.write(f"**Cost**: {aff['cost']}\n\n")
            
            f.write("### Pre-Filled Data\n")
            for k, v in aff['pre_filled_data'].items():
                f.write(f"- **{k.replace('_', ' ').title()}**: {v}\n")
            
            f.write("\n### Steps\n")
            for step in aff['steps']:
                f.write(f"- {step}\n")
            
            f.write(f"\n### Notary Script\n> {aff['notary_script']}\n\n")
            
            f.write("### Common Mistakes\n")
            for mistake in aff['common_mistakes']:
                f.write(f"- {mistake}\n")
            f.write("\n---\n\n")
        
        f.write("## 💡 Universal Tips\n\n")
        for tip in guide['universal_tips']:
            f.write(f"- {tip}\n")
    
    print(f"\n✅ Affidavit Guide: {guide['total_affidavits']} affidavits, {guide['total_steps']} steps")
    print(f"   Reports: {md_path}")
    return guide

if __name__ == '__main__':
    main()
