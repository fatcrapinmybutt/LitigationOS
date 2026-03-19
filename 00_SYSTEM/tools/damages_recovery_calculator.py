#!/usr/bin/env python3
"""
Tool #77 — Legal Fee & Damages Recovery Calculator
======================================================
Calculates what Andrew can potentially RECOVER if successful:
- 42 USC §1988 attorney fees (even pro se can recover costs)
- 42 USC §1983 compensatory damages
- MCL 600.2919a exemplary damages (treble damages for fraud)
- Costs of litigation (filing fees, service, copies)
- Emotional distress damages
- Loss of parenting time damages

This is for INTERNAL strategy use — NOT for filing.
Helps Andrew understand the financial stakes.
"""
import sys, json
from pathlib import Path
from datetime import datetime

sys.stdout = open(sys.stdout.fileno(), mode='w', encoding='utf-8', errors='replace')

REPO = Path(r"C:\Users\andre\LitigationOS")
REPORTS_DIR = REPO / "00_SYSTEM" / "reports"

# Damages categories with conservative and aggressive estimates
DAMAGES = {
    'compensatory': {
        'name': 'Compensatory Damages (§1983)',
        'items': [
            {
                'description': 'Emotional distress from parental alienation/separation',
                'conservative': 50000,
                'aggressive': 250000,
                'basis': 'Carey v Piphus, 435 US 247 (1978) — compensatory damages for due process violations',
            },
            {
                'description': 'Loss of parent-child relationship (45+ days denied contact)',
                'conservative': 25000,
                'aggressive': 150000,
                'basis': 'Troxel v Granville, 530 US 57 (2000) — fundamental liberty interest',
            },
            {
                'description': 'Reputational harm from false allegations',
                'conservative': 10000,
                'aggressive': 75000,
                'basis': 'Paul v Davis, 424 US 693 (1976) — stigma + denial of right',
            },
            {
                'description': 'Housing loss/discrimination (Shady Oaks)',
                'conservative': 15000,
                'aggressive': 50000,
                'basis': 'Fair Housing Act, 42 USC §3613(c) — actual damages',
            },
            {
                'description': 'Lost wages/economic harm from litigation burden',
                'conservative': 5000,
                'aggressive': 25000,
                'basis': 'Documented economic losses',
            },
        ],
    },
    'punitive': {
        'name': 'Punitive Damages',
        'items': [
            {
                'description': 'Punitive damages against private defendants (Watson, Berry, Barnes)',
                'conservative': 25000,
                'aggressive': 250000,
                'basis': 'Smith v Wade, 461 US 30 (1983) — punitive damages available in §1983 against private actors for reckless/callous conduct',
            },
        ],
        'notes': 'Punitive damages NOT available against government entities or officials in official capacity. Available against Watson, Berry, Barnes as private actors.',
    },
    'statutory': {
        'name': 'Statutory Damages',
        'items': [
            {
                'description': 'FHA statutory damages (housing discrimination)',
                'conservative': 10000,
                'aggressive': 50000,
                'basis': '42 USC §3613(c)(1) — compensatory and punitive damages',
            },
            {
                'description': 'Michigan exemplary damages for fraud (MCL 600.2919a)',
                'conservative': 0,
                'aggressive': 100000,
                'basis': 'MCL 600.2919a — exemplary damages for fraud (court discretion)',
            },
        ],
    },
    'costs': {
        'name': 'Recoverable Costs',
        'items': [
            {
                'description': 'Filing fees (if not waived by IFP)',
                'conservative': 525,
                'aggressive': 2030,
                'basis': '28 USC §1920 — taxable costs; MCR 2.625',
            },
            {
                'description': 'Service of process costs',
                'conservative': 200,
                'aggressive': 500,
                'basis': '28 USC §1920(1)',
            },
            {
                'description': 'Copying and printing costs',
                'conservative': 100,
                'aggressive': 300,
                'basis': '28 USC §1920(4)',
            },
            {
                'description': 'Travel/mileage for court appearances',
                'conservative': 200,
                'aggressive': 1000,
                'basis': 'IRS mileage rate × documented trips',
            },
        ],
    },
    'fees': {
        'name': 'Attorney Fees (§1988)',
        'items': [
            {
                'description': 'Reasonable attorney fees under 42 USC §1988',
                'conservative': 0,
                'aggressive': 50000,
                'basis': '42 USC §1988 — pro se litigants generally cannot recover attorney fees (Kay v Ehrler, 499 US 432 (1991)), but can recover paralegal/expert costs',
            },
        ],
        'notes': 'Pro se litigants cannot recover "attorney fees" per Kay v Ehrler. However, costs, expert fees, and paralegal fees may be recoverable.',
    },
}

def main():
    print("=" * 70)
    print("LEGAL FEE & DAMAGES RECOVERY CALCULATOR — Tool #77")
    print("⚠️ FOR INTERNAL STRATEGY USE ONLY — NOT FOR COURT FILING")
    print("=" * 70)
    
    total_conservative = 0
    total_aggressive = 0
    
    lines = [
        "# 💰 DAMAGES & RECOVERY CALCULATOR",
        "## Pigors v. Watson — Potential Recovery Analysis",
        f"*Generated: {datetime.now().strftime('%Y-%m-%d %H:%M')}*",
        "",
        "⚠️ **FOR INTERNAL STRATEGY USE ONLY — NOT FOR COURT FILING**",
        "These are estimates based on comparable cases, not guarantees.\n",
        "---\n",
    ]
    
    for cat_id, category in DAMAGES.items():
        cat_conservative = sum(i['conservative'] for i in category['items'])
        cat_aggressive = sum(i['aggressive'] for i in category['items'])
        total_conservative += cat_conservative
        total_aggressive += cat_aggressive
        
        lines.append(f"## {category['name']}")
        lines.append(f"*Range: ${cat_conservative:,.0f} — ${cat_aggressive:,.0f}*\n")
        lines.append("| Item | Conservative | Aggressive | Legal Basis |")
        lines.append("|------|-------------|------------|-------------|")
        
        for item in category['items']:
            lines.append(f"| {item['description'][:50]} | ${item['conservative']:,.0f} | ${item['aggressive']:,.0f} | {item['basis'][:50]} |")
            print(f"  ${item['conservative']:>8,.0f} — ${item['aggressive']:>9,.0f}  {item['description'][:50]}")
        
        if 'notes' in category:
            lines.append(f"\n*Note: {category['notes']}*")
        lines.append("")
    
    lines.extend([
        "---",
        "## TOTAL RECOVERY RANGE",
        f"| Scenario | Amount |",
        f"|----------|--------|",
        f"| **Conservative** | **${total_conservative:,.0f}** |",
        f"| **Aggressive** | **${total_aggressive:,.0f}** |",
        "",
        "## Key Caveats",
        "1. **Judicial immunity**: McNeill is immune from damages for judicial acts",
        "   (Stump v Sparkman). Damages only from PRIVATE defendants.",
        "2. **Pro se fees**: Kay v Ehrler bars attorney fee recovery for pro se.",
        "   BUT costs, paralegal fees, and expert fees ARE recoverable.",
        "3. **Collection**: Even with a judgment, collection depends on defendants'",
        "   assets. Watson/Berry may have limited assets.",
        "4. **Sovereign immunity**: State entities may have immunity defenses.",
        "5. **These are ESTIMATES** — actual recovery depends on evidence,",
        "   judge/jury, and defendants' conduct at trial.",
        "",
        f"*Damages Recovery Calculator — Tool #77*",
        f"*Range: ${total_conservative:,.0f} — ${total_aggressive:,.0f}*",
    ])
    
    print(f"\n  TOTAL RECOVERY RANGE:")
    print(f"    Conservative: ${total_conservative:,.0f}")
    print(f"    Aggressive:   ${total_aggressive:,.0f}")
    
    md_path = REPORTS_DIR / "DAMAGES_RECOVERY.md"
    md_path.write_text('\n'.join(lines), encoding='utf-8')
    
    json_path = REPORTS_DIR / "damages_recovery.json"
    json_path.write_text(json.dumps({
        'generated': datetime.now().isoformat(),
        'tool': 'Damages Recovery Calculator (#77)',
        'conservative_total': total_conservative,
        'aggressive_total': total_aggressive,
        'categories': {k: {
            'name': v['name'],
            'conservative': sum(i['conservative'] for i in v['items']),
            'aggressive': sum(i['aggressive'] for i in v['items']),
        } for k, v in DAMAGES.items()},
    }, indent=2), encoding='utf-8')
    
    print(f"\n✅ Recovery analysis complete")
    print(f"   Reports: DAMAGES_RECOVERY.md + damages_recovery.json")

if __name__ == '__main__':
    main()
