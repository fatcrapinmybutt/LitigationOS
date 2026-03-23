#!/usr/bin/env python3
"""Tool #259: IFP (In Forma Pauperis) Financial Affidavit Helper
Generates the financial documentation needed for MCR 2.002 fee waiver applications.
Analyzes case costs, filing fees, and produces the financial affidavit template
with all required fields for the court.
"""
import sys, os, json, sqlite3
from datetime import datetime

sys.stdout = open(sys.stdout.fileno(), mode='w', encoding='utf-8', errors='replace')

def s(v):
    return (v or "").lower()

def main():
    db_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', 'litigation_context.db')
    report_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'reports')
    os.makedirs(report_dir, exist_ok=True)

    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA busy_timeout=60000")
    conn.execute("PRAGMA cache_size=-32000")

    print("=" * 70)
    print("TOOL #259: IFP FINANCIAL AFFIDAVIT HELPER")
    print("=" * 70)

    tables = [r[0] for r in conn.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall()]

    # --- 1. Filing Fee Inventory ---
    print("\n[1/4] Calculating filing fees across all cases...")
    filing_fees = {
        "14th_circuit_custody": {
            "case": "2024-001507-DC",
            "court": "14th Circuit Court",
            "filings": [
                {"type": "Motion to Disqualify (F2)", "fee": 20, "form": "MC 02"},
                {"type": "Emergency Motion (F5)", "fee": 20, "form": "MC 02"},
                {"type": "Motion Relief from Judgment (F1)", "fee": 20, "form": "MC 02"},
                {"type": "Motion for Sanctions (F10)", "fee": 20, "form": "MC 02"},
                {"type": "PPO Termination (F4)", "fee": 0, "form": "CC 381"},
            ],
            "subtotal": 80
        },
        "coa_appeal": {
            "case": "COA 366810",
            "court": "Court of Appeals",
            "filings": [
                {"type": "Appellant Brief (F9)", "fee": 0, "form": "Already filed claim of appeal"},
                {"type": "Emergency Motion for Stay", "fee": 0, "form": "Motion in pending appeal"},
            ],
            "subtotal": 0
        },
        "federal_1983": {
            "case": "New filing",
            "court": "USDC Western District MI",
            "filings": [
                {"type": "42 USC 1983 Complaint (F3)", "fee": 405, "form": "Pro Se Complaint Form"},
            ],
            "subtotal": 405
        },
        "msc_original": {
            "case": "New filing",
            "court": "Michigan Supreme Court",
            "filings": [
                {"type": "Complaint for Superintending Control (F7)", "fee": 375, "form": "MSC complaint"},
            ],
            "subtotal": 375
        },
        "jtc_complaint": {
            "case": "New filing",
            "court": "Judicial Tenure Commission",
            "filings": [
                {"type": "JTC Complaint (F6)", "fee": 0, "form": "JTC complaint form"},
            ],
            "subtotal": 0
        },
        "housing": {
            "case": "2025-002760-CZ",
            "court": "14th Circuit Court",
            "filings": [
                {"type": "Housing Complaint (F8)", "fee": 0, "form": "Already filed"},
            ],
            "subtotal": 0
        }
    }

    total_fees = sum(court["subtotal"] for court in filing_fees.values())
    print(f"  Total filing fees: ${total_fees}")
    for court_key, court in filing_fees.items():
        if court["subtotal"] > 0:
            print(f"    {court['court']}: ${court['subtotal']}")

    # --- 2. IFP Requirements ---
    print("\n[2/4] IFP requirements analysis...")
    ifp = {
        "state_court": {
            "authority": "MCR 2.002",
            "form": "MC 20 (Affidavit and Order — Suspension of Fees/Costs)",
            "requirements": [
                "Affidavit showing inability to pay fees",
                "Income below 125% of federal poverty guidelines",
                "List of monthly expenses exceeding income",
                "No substantial assets available",
                "Good faith basis for claims"
            ],
            "filing_covers": ["All 14th Circuit motions", "Service costs", "Transcript fees for appeal"],
            "poverty_guidelines_2026": {
                "household_1": 16090,
                "household_2": 21750,
                "125_percent_1": 20113,
                "125_percent_2": 27188
            }
        },
        "federal_court": {
            "authority": "28 USC 1915(a)",
            "form": "Application to Proceed In Forma Pauperis (AO 240)",
            "requirements": [
                "Affidavit of poverty including income, assets, expenses",
                "Statement of claims (must not be frivolous)",
                "Previous 12 months income",
                "Cash on hand and in bank accounts",
                "Real and personal property owned",
                "Debts and obligations"
            ],
            "fee_waived": 405,
            "note": "Federal IFP also waives service costs — US Marshals serve for free under 28 USC 1915(d)"
        },
        "msc": {
            "authority": "MCR 7.302(B)(4)",
            "form": "Affidavit of Indigency",
            "requirements": [
                "Same standard as MCR 2.002",
                "Filed with application for leave"
            ],
            "fee_waived": 375
        }
    }

    # --- 3. Service Cost Estimates ---
    print("\n[3/4] Estimating service costs...")
    service_costs = {
        "personal_service": {
            "per_party": 75,
            "parties_to_serve": [
                "Emily A. Watson",
                "Ronald T. Berry (if named)",
                "Hon. Jenny L. McNeill (JTC complaint — no service needed)",
                "Pamela Rusco (subpoena)"
            ],
            "estimated_total": 225
        },
        "certified_mail": {
            "per_mailing": 8,
            "estimated_mailings": 20,
            "estimated_total": 160
        },
        "copies": {
            "per_page": 0.25,
            "estimated_pages": 500,
            "estimated_total": 125
        },
        "mileage": {
            "per_mile": 0.67,
            "round_trip_court": 30,
            "estimated_trips": 10,
            "estimated_total": 201
        },
        "total_service_costs": 711
    }
    print(f"  Total service costs: ${service_costs['total_service_costs']}")

    # --- 4. Financial Affidavit Template ---
    print("\n[4/4] Generating affidavit template...")
    affidavit_template = {
        "header": "AFFIDAVIT IN SUPPORT OF APPLICATION TO PROCEED IN FORMA PAUPERIS",
        "case": "Pigors v. Watson, Case No. 2024-001507-DC",
        "court": "14th Circuit Court, Muskegon County, Michigan",
        "sections": {
            "personal_info": {
                "name": "Andrew James Pigors",
                "address": "1977 Whitehall Road, Lot 17, North Muskegon, MI 49445",
                "phone": "(231) 903-5690",
                "email": "andrewjpigors@gmail.com",
                "dependents": "L.D.W. (minor child)"
            },
            "income": {
                "instruction": "[ANDREW_REQUIRED: Enter current monthly income from all sources]",
                "fields": [
                    "Employment income: $____/month",
                    "Unemployment/disability: $____/month",
                    "Child support received: $____/month",
                    "Other income: $____/month",
                    "TOTAL MONTHLY INCOME: $____/month"
                ]
            },
            "expenses": {
                "instruction": "[ANDREW_REQUIRED: Enter monthly expenses]",
                "fields": [
                    "Rent/mortgage: $____/month",
                    "Utilities: $____/month",
                    "Food: $____/month",
                    "Transportation: $____/month",
                    "Medical: $____/month",
                    "Insurance: $____/month",
                    "Child-related expenses: $____/month",
                    "Other: $____/month",
                    "TOTAL MONTHLY EXPENSES: $____/month"
                ]
            },
            "assets": {
                "instruction": "[ANDREW_REQUIRED: List all assets]",
                "fields": [
                    "Cash on hand: $____",
                    "Bank accounts: $____",
                    "Vehicles: ____",
                    "Real property: ____",
                    "Other assets: ____"
                ]
            },
            "verification": "I declare under the penalties of perjury that the foregoing is true and correct. MCL 600.2922a."
        },
        "total_fees_requested_waived": total_fees + service_costs['total_service_costs']
    }

    results = {
        "tool": "#259 IFP Financial Affidavit Helper",
        "generated": datetime.now().isoformat(),
        "filing_fees": filing_fees,
        "total_fees": total_fees,
        "ifp_requirements": ifp,
        "service_costs": service_costs,
        "affidavit_template": affidavit_template,
        "total_costs_to_waive": total_fees + service_costs['total_service_costs'],
        "recommendation": "File MC 20 (state) + AO 240 (federal) to waive all fees"
    }

    # --- Reports ---
    md_lines = [
        "# Tool #259: IFP Financial Affidavit Helper",
        f"Generated: {datetime.now().isoformat()}",
        "",
        "## Cost Summary",
        f"- **Total Filing Fees**: ${total_fees}",
        f"- **Total Service Costs**: ${service_costs['total_service_costs']}",
        f"- **TOTAL TO WAIVE**: ${total_fees + service_costs['total_service_costs']}",
        "",
        "## Filing Fees by Court",
        "",
        "| Court | Case | Fee |",
        "|-------|------|-----|",
    ]
    for court_key, court in filing_fees.items():
        if court["subtotal"] > 0:
            md_lines.append(f"| {court['court']} | {court['case']} | ${court['subtotal']} |")
    md_lines.append(f"| **TOTAL** | | **${total_fees}** |")

    md_lines.extend([
        "",
        "## IFP Forms Required",
        "",
        f"### State Court: {ifp['state_court']['form']}",
        f"- Authority: {ifp['state_court']['authority']}",
        "",
        f"### Federal Court: {ifp['federal_court']['form']}",
        f"- Authority: {ifp['federal_court']['authority']}",
        f"- **Bonus**: US Marshals serve for FREE under 28 USC 1915(d)",
        "",
        "## Service Costs",
        f"- Personal service: ${service_costs['personal_service']['estimated_total']}",
        f"- Certified mail: ${service_costs['certified_mail']['estimated_total']}",
        f"- Copies: ${service_costs['copies']['estimated_total']}",
        f"- Mileage: ${service_costs['mileage']['estimated_total']}",
        "",
        "## ACTION ITEMS FOR ANDREW",
        "1. Complete income section of affidavit (monthly income from ALL sources)",
        "2. Complete expense section (rent, utilities, food, transport, medical, etc.)",
        "3. List all assets (bank accounts, vehicles, property)",
        "4. Get affidavit notarized",
        "5. File MC 20 with FIRST state court motion",
        "6. File AO 240 with federal 1983 complaint"
    ])

    md_path = os.path.join(report_dir, "tool_259_ifp_affidavit.md")
    json_path = os.path.join(report_dir, "tool_259_ifp_affidavit.json")
    with open(md_path, 'w', encoding='utf-8') as f:
        f.write('\n'.join(md_lines))
    with open(json_path, 'w', encoding='utf-8') as f:
        json.dump(results, f, indent=2, default=str)

    print(f"\n  MD:   {md_path}")
    print(f"  JSON: {json_path}")
    conn.close()

    print(f"\n{'='*70}")
    print(f"TOTAL TO WAIVE: ${total_fees + service_costs['total_service_costs']} | FORMS: MC 20 + AO 240")
    print(f"{'='*70}")

if __name__ == "__main__":
    main()
