#!/usr/bin/env python3
"""
Tool #136 — Fee Waiver Application Generator
=================================================
🆕 NOVEL TOOL — Generates IFP (In Forma Pauperis)
application language tailored to each court system.

State (MCR 2.002), Federal (28 USC §1915), COA, MSC
all have different IFP requirements. This tool covers all.
"""
import sys, json
from pathlib import Path
from datetime import datetime

sys.stdout = open(sys.stdout.fileno(), mode='w', encoding='utf-8', errors='replace')

REPO = Path(r"C:\Users\andre\LitigationOS")
REPORTS_DIR = REPO / "00_SYSTEM" / "reports"

IFP_APPLICATIONS = [
    {
        'court': '14th Circuit Court (State)',
        'authority': 'MCR 2.002; MCL 600.2529',
        'form': 'MC 20 (Fee Waiver Request)',
        'filings_covered': ['F1', 'F2', 'F3', 'F7'],
        'fees_waived': '$175 per motion filing',
        'requirements': [
            'Complete MC 20 form with financial information',
            'Attach proof of income (pay stubs, tax return)',
            'Attach proof of expenses (rent, utilities, child support)',
            'File with first filing — covers all subsequent filings in same case',
            'Judge decides — may grant full or partial waiver',
        ],
        'tips': [
            'File MC 20 WITH your first motion — not separately',
            'Be honest about finances — lying on IFP is a crime',
            'If partially denied, ask for installment payments',
            'One IFP covers ALL filings in the same case number',
        ],
    },
    {
        'court': 'US District Court (Federal)',
        'authority': '28 USC §1915',
        'form': 'Application to Proceed In Forma Pauperis (local form)',
        'filings_covered': ['F4'],
        'fees_waived': '$405 filing fee + US Marshal service fees',
        'requirements': [
            'Complete the USDC WDMI IFP application form',
            'Attach financial affidavit (sworn)',
            'List all income sources',
            'List all assets and debts',
            'File simultaneously with complaint',
        ],
        'tips': [
            'Federal IFP also waives service fees — US Marshals serve for free',
            'Must file IFP WITH the complaint — court won\'t accept complaint without fee or IFP',
            'If denied, you have 30 days to pay the filing fee',
            'Federal courts are stricter about IFP — be thorough',
        ],
    },
    {
        'court': 'Court of Appeals',
        'authority': 'MCR 7.202(7); MCR 2.002',
        'form': 'MC 20 (same form as circuit court)',
        'filings_covered': ['F8', 'F9'],
        'fees_waived': '$375 application fee',
        'requirements': [
            'Complete MC 20 form',
            'File with application for leave (F8)',
            'COA clerk reviews — same standards as circuit court',
        ],
        'tips': [
            'If IFP was granted in circuit court, attach that order — COA may honor it',
            'COA IFP covers both the application fee and any transcript costs',
        ],
    },
    {
        'court': 'Michigan Supreme Court',
        'authority': 'MCR 7.302(D); MCR 2.002',
        'form': 'MC 20 (same form)',
        'filings_covered': ['F5'],
        'fees_waived': '$375 application fee',
        'requirements': [
            'Complete MC 20 form',
            'File with complaint for superintending control',
            'MSC clerk reviews',
        ],
        'tips': [
            'MSC is the most difficult IFP to get — be thorough',
            'Attach all prior IFP grants from lower courts',
        ],
    },
    {
        'court': 'JTC / AGC (No Fee)',
        'authority': 'N/A — filing is free',
        'form': 'None required',
        'filings_covered': ['F6', 'F10'],
        'fees_waived': 'N/A — $0 cost',
        'requirements': ['No fee waiver needed — these filings are always free'],
        'tips': ['Just file — no financial disclosure required'],
    },
]

def main():
    print("=" * 70)
    print("FEE WAIVER APPLICATION GENERATOR — Tool #136")
    print("=" * 70)
    
    total_savings = 0
    
    lines = [
        "# 💰 FEE WAIVER (IFP) APPLICATION GUIDE",
        f"*Generated: {datetime.now().strftime('%Y-%m-%d %H:%M')} | Tool #136*",
        f"*Save $1,680+ in filing fees across all courts*\n",
        "---\n",
        "## FEE WAIVER DASHBOARD\n",
        "| Court | Filings | Fees Waived | Form |",
        "|-------|---------|-------------|------|",
    ]
    
    for app in IFP_APPLICATIONS:
        filings = ', '.join(app['filings_covered'])
        lines.append(f"| {app['court']} | {filings} | {app['fees_waived']} | {app['form']} |")
        print(f"  💰 {app['court'][:30]}: {app['fees_waived']}")
    
    lines.extend(["", "---\n"])
    
    for app in IFP_APPLICATIONS:
        lines.append(f"## {app['court']}")
        lines.append(f"**Authority:** {app['authority']}")
        lines.append(f"**Form:** {app['form']}")
        lines.append(f"**Covers:** {', '.join(app['filings_covered'])}")
        lines.append(f"**Saves:** {app['fees_waived']}\n")
        
        lines.append("### Requirements:")
        for r in app['requirements']:
            lines.append(f"- {r}")
        
        lines.append("\n### Tips:")
        for t in app['tips']:
            lines.append(f"- 💡 {t}")
        
        lines.append("\n---\n")
    
    lines.extend([
        "## TOTAL SAVINGS WITH IFP\n",
        "| Fee | Amount |",
        "|-----|--------|",
        "| Circuit Court (4 filings × $175) | $700 |",
        "| Federal Court ($405) | $405 |",
        "| COA ($375) | $375 |",
        "| MSC ($375) | $375 |",
        "| JTC + AGC | $0 (always free) |",
        "| **TOTAL SAVED** | **$1,855** |",
        "",
        f"*{len(IFP_APPLICATIONS)} court systems covered · $1,855 total savings*",
    ])
    
    md_path = REPORTS_DIR / "FEE_WAIVER_GUIDE.md"
    md_path.write_text('\n'.join(lines), encoding='utf-8')
    
    json_path = REPORTS_DIR / "fee_waiver_guide.json"
    json_path.write_text(json.dumps({
        'generated': datetime.now().isoformat(),
        'tool': 'Fee Waiver Application Generator (#136)',
        'courts': len(IFP_APPLICATIONS),
        'total_savings': 1855,
    }, indent=2), encoding='utf-8')
    
    print(f"\n✅ {len(IFP_APPLICATIONS)} court IFP guides | $1,855 total savings")
    print(f"   Reports: FEE_WAIVER_GUIDE.md + fee_waiver_guide.json")

if __name__ == '__main__':
    main()
