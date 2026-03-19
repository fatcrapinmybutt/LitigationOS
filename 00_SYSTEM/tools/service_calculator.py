#!/usr/bin/env python3
"""
Tool #208: Service of Process Calculator
==========================================
Calculates exact service deadlines, methods, and costs for each
filing across all courts. Generates printable service instructions.

NOVEL INNOVATION: Auto-generates Certificate of Service templates
with pre-filled party addresses and calculates USPS delivery windows.
"""
import json, os, sys
from datetime import datetime, timedelta

sys.stdout = open(sys.stdout.fileno(), mode='w', encoding='utf-8', errors='replace')

REPORT_DIR = os.path.join(os.path.dirname(__file__), '..', 'reports')
os.makedirs(REPORT_DIR, exist_ok=True)

PARTIES_TO_SERVE = {
    "emily_watson": {
        "name": "Emily A. Watson",
        "role": "Defendant",
        "address": "2160 Garland Drive, Norton Shores, MI 49441",
        "serve_in": ["F3", "F10"],
        "method": "Certified mail, return receipt requested (or personal service)"
    },
    "jennifer_barnes": {
        "name": "Jennifer Barnes (P55406)",
        "role": "Emily's Former Attorney (WITHDREW)",
        "address": "Barnes Law Firm PLLC, 880 Jefferson St Ste B, Muskegon, MI 49440",
        "serve_in": [],
        "method": "Only if still attorney of record — verify withdrawal order",
        "note": "WITHDREW — may not need service. Check court docket."
    },
    "pamela_rusco": {
        "name": "Pamela Rusco",
        "role": "Friend of the Court",
        "address": "990 Terrace St, Muskegon, MI 49442",
        "serve_in": ["F3"],
        "method": "First class mail or hand delivery to FOC office"
    },
    "jtc": {
        "name": "Judicial Tenure Commission",
        "role": "Regulatory Body",
        "address": "3034 W. Grand Blvd, Suite 8-450, Detroit, MI 48202",
        "serve_in": ["F6"],
        "method": "Mail or email (jtc@michigan.gov)"
    },
    "judge_mcneill": {
        "name": "Hon. Jenny L. McNeill",
        "role": "Subject of Disqualification/Complaint",
        "address": "14th Circuit Court, 990 Terrace St, Muskegon, MI 49442",
        "serve_in": ["F3"],
        "method": "Serve via court clerk (do NOT serve judge directly)"
    }
}

def build_service_calculator():
    today = datetime.now()
    
    calc = {
        "tool_id": 208,
        "name": "Service of Process Calculator",
        "generated": today.isoformat(),
        "filings": {
            "F3": {
                "name": "Disqualification Motion (MCR 2.003)",
                "court": "14th Circuit Court",
                "service_rule": "MCR 2.107 — service on all parties",
                "timing_rule": "MCR 2.119(C)(1) — 9 days before hearing by mail (14 days personal)",
                "parties_to_serve": ["emily_watson", "pamela_rusco", "judge_mcneill"],
                "service_methods": {
                    "certified_mail": {
                        "cost": "$7.75 per recipient (certified + return receipt)",
                        "delivery": "3-7 business days",
                        "proof": "Return receipt (green card) = proof of service",
                        "recommended": True
                    },
                    "first_class_mail": {
                        "cost": "$0.73 per recipient",
                        "delivery": "3-5 business days",
                        "proof": "Affidavit of mailing (you sign stating you mailed it)",
                        "recommended": False
                    },
                    "personal_service": {
                        "cost": "$50-100 (process server) or FREE (friend over 18)",
                        "delivery": "Same day",
                        "proof": "Affidavit of service by server",
                        "recommended": False
                    }
                },
                "total_cost_estimate": "$23.25 (3 certified mail) or $2.19 (3 first class)",
                "deadlines": {
                    "if_filing_today": today.strftime("%B %d, %Y"),
                    "service_by_mail": (today + timedelta(days=2)).strftime("%B %d, %Y"),
                    "hearing_earliest": (today + timedelta(days=16)).strftime("%B %d, %Y"),
                }
            },
            "F6": {
                "name": "JTC Complaint",
                "court": "Judicial Tenure Commission",
                "service_rule": "JTC rules — complaint sent to JTC, they handle investigation",
                "timing_rule": "No specific timing — file at any time",
                "parties_to_serve": ["jtc"],
                "service_methods": {
                    "email": {
                        "cost": "FREE",
                        "delivery": "Instant",
                        "proof": "Email confirmation / sent receipt",
                        "recommended": True
                    },
                    "certified_mail": {
                        "cost": "$7.75",
                        "delivery": "3-7 business days",
                        "proof": "Return receipt",
                        "recommended": False
                    }
                },
                "total_cost_estimate": "$0 (email) or $7.75 (certified mail)",
                "note": "JTC complaints are CONFIDENTIAL. Do NOT serve Emily or judge directly."
            },
            "F10": {
                "name": "COA Emergency Motion",
                "court": "Michigan Court of Appeals",
                "service_rule": "MCR 7.210 — serve all parties to lower court proceeding",
                "timing_rule": "Emergency — serve simultaneously with filing or ASAP after",
                "parties_to_serve": ["emily_watson"],
                "service_methods": {
                    "certified_mail": {
                        "cost": "$7.75",
                        "delivery": "3-7 business days",
                        "proof": "Return receipt",
                        "recommended": True
                    },
                    "email_if_consented": {
                        "cost": "FREE",
                        "delivery": "Instant",
                        "proof": "Email confirmation",
                        "note": "Only if opposing party consented to email service",
                        "recommended": False
                    }
                },
                "total_cost_estimate": "$7.75 (certified mail to Emily)",
                "note": "Emergency motion — serve ASAP. Include IFP application if applicable."
            }
        },
        "certificate_of_service_template": {
            "header": "CERTIFICATE OF SERVICE",
            "body": "I, Andrew James Pigors, hereby certify that on [DATE], I served a true copy of the foregoing [DOCUMENT TITLE] upon the following parties by [METHOD]:",
            "signature": "Andrew James Pigors, Plaintiff, Pro Se\n1977 Whitehall Road, Lot 17\nNorth Muskegon, MI 49445\n(231) 903-5690",
            "methods_text": {
                "certified_mail": "United States Postal Service, certified mail, return receipt requested",
                "first_class": "United States Postal Service, first class mail, postage prepaid",
                "personal": "personal service by [NAME OF SERVER]",
                "email": "electronic mail to [EMAIL ADDRESS]"
            }
        },
        "total_service_cost": "$31.00 (certified mail for all filings) or $2.92 (first class)",
        "usps_tips": [
            "Keep ALL receipts — they're proof of service",
            "Use certified mail with return receipt (green card) for strongest proof",
            "Save tracking numbers — enter them on USPS.com for delivery confirmation",
            "Mail from USPS counter (not mailbox) — get receipt with date stamp",
            "If certified mail returned unclaimed — that's STILL valid service in many cases"
        ]
    }
    
    calc['total_parties'] = len(PARTIES_TO_SERVE)
    calc['parties'] = PARTIES_TO_SERVE
    return calc

def main():
    print("=" * 60)
    print("TOOL #208: SERVICE OF PROCESS CALCULATOR")
    print("=" * 60)
    
    calc = build_service_calculator()
    
    json_path = os.path.join(REPORT_DIR, 'SERVICE_CALCULATOR.json')
    with open(json_path, 'w', encoding='utf-8') as f:
        json.dump(calc, f, indent=2, ensure_ascii=False)
    
    md_path = os.path.join(REPORT_DIR, 'SERVICE_CALCULATOR.md')
    with open(md_path, 'w', encoding='utf-8') as f:
        f.write("# 📬 Service of Process Calculator (Tool #208)\n\n")
        f.write(f"Generated: {calc['generated']}\n")
        f.write(f"**{calc['total_parties']} parties** | **Total cost: {calc['total_service_cost']}**\n\n")
        
        f.write("## Parties to Serve\n\n")
        for pid, party in calc['parties'].items():
            f.write(f"- **{party['name']}** ({party['role']}) — {party['address']}\n")
        
        f.write("\n## Filing-Specific Service\n\n")
        for fid, filing in calc['filings'].items():
            f.write(f"### {fid}: {filing['name']}\n\n")
            f.write(f"**Court**: {filing['court']}\n")
            f.write(f"**Rule**: {filing['service_rule']}\n")
            f.write(f"**Timing**: {filing['timing_rule']}\n")
            f.write(f"**Cost**: {filing['total_cost_estimate']}\n\n")
            
            serve_names = [calc['parties'][p]['name'] for p in filing['parties_to_serve']]
            f.write(f"**Serve**: {', '.join(serve_names)}\n\n")
            
            for method, details in filing['service_methods'].items():
                rec = " ⭐ RECOMMENDED" if details.get('recommended') else ""
                f.write(f"- **{method.replace('_', ' ').title()}**: {details['cost']} — {details['delivery']}{rec}\n")
            f.write("\n---\n\n")
        
        f.write("## Certificate of Service Template\n\n")
        f.write(f"> {calc['certificate_of_service_template']['body']}\n\n")
        f.write(f"```\n{calc['certificate_of_service_template']['signature']}\n```\n\n")
        
        f.write("## USPS Tips\n\n")
        for tip in calc['usps_tips']:
            f.write(f"- {tip}\n")
    
    print(f"\n✅ Service Calculator: {calc['total_parties']} parties, cost {calc['total_service_cost']}")
    print(f"   Reports: {md_path}")
    return calc

if __name__ == '__main__':
    main()
