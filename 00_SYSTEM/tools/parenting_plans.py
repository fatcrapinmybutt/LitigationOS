#!/usr/bin/env python3
"""
Tool #139 — Parenting Plan Proposal Generator
=================================================
🆕 NOVEL TOOL — Creates a detailed, reasonable parenting
plan proposal that Andrew can present to the court.

Courts LOVE specificity. A well-drafted parenting plan
shows the judge you're serious and focused on L.D.W.'s needs.
"""
import sys, json
from pathlib import Path
from datetime import datetime

sys.stdout = open(sys.stdout.fileno(), mode='w', encoding='utf-8', errors='replace')

REPO = Path(r"C:\Users\andre\LitigationOS")
REPORTS_DIR = REPO / "00_SYSTEM" / "reports"

PARENTING_PLANS = {
    'primary': {
        'name': 'Plan A — Primary Custody to Andrew',
        'schedule': {
            'regular': 'L.D.W. resides primarily with Andrew; Emily has parenting time every other weekend (Friday 6 PM to Sunday 6 PM) plus one weekday evening (Wednesday 5-8 PM)',
            'summer': 'Emily gets 4 consecutive weeks in summer (with 2 weeks advance notice)',
            'holidays': 'Alternating holidays per standard Michigan schedule',
            'communication': 'Both parents may call/video chat daily between 6-7 PM on non-custodial days',
        },
        'when': 'After custody modification (F7) — best outcome',
    },
    'joint': {
        'name': 'Plan B — Joint Custody (50/50)',
        'schedule': {
            'regular': 'Week-on/week-off schedule. Exchange Sundays at 6 PM.',
            'summer': 'Same week-on/week-off continues through summer',
            'holidays': 'Alternating holidays per standard Michigan schedule',
            'communication': 'Both parents may call/video chat daily between 6-7 PM on non-custodial weeks',
        },
        'when': 'Compromise position — shows willingness to cooperate',
    },
    'expanded': {
        'name': 'Plan C — Expanded Parenting Time',
        'schedule': {
            'regular': 'Emily retains primary custody. Andrew gets every other weekend (Fri-Sun) PLUS every Wednesday overnight PLUS one additional weeknight dinner',
            'summer': 'Andrew gets 6 weeks (3 periods of 2 weeks each)',
            'holidays': 'Alternating holidays per standard Michigan schedule',
            'communication': 'Both parents may call/video chat daily between 6-7 PM',
        },
        'when': 'Minimum acceptable outcome — used for F1 (emergency)',
    },
}

PLAN_PROVISIONS = [
    {
        'section': 'Communication Protocol',
        'provisions': [
            'Parents shall communicate about L.D.W. via OurFamilyWizard app',
            'Both parents entitled to daily phone/video contact with L.D.W.',
            'Response to non-emergency communications within 24 hours',
            'Emergency communications responded to immediately',
            'Neither parent shall disparage the other in front of L.D.W.',
        ],
    },
    {
        'section': 'Exchange Logistics',
        'provisions': [
            'Exchanges at a neutral public location (e.g., police station lobby)',
            'Exchanging parent arrives on time (15-minute grace period)',
            'If late without notice, the other parent may leave after 30 minutes',
            'Both parents keep L.D.W.\'s belongings (clothes, toys, medicines) accessible',
        ],
    },
    {
        'section': 'Decision Making',
        'provisions': [
            'Major decisions (education, health, religion) made jointly',
            'Day-to-day decisions made by custodial parent on their time',
            'If parents disagree on major decision → mediation first, then court',
            'Both parents have access to all medical, educational, and activity records',
        ],
    },
    {
        'section': 'Travel',
        'provisions': [
            '14 days advance written notice for out-of-state travel',
            'Itinerary and contact information provided before travel',
            'Neither parent shall relocate more than 100 miles without court order (MCL 722.31)',
        ],
    },
    {
        'section': 'Third Parties',
        'provisions': [
            'Introduction of significant others to L.D.W. only after 6 months of relationship',
            'Neither parent shall allow overnight guests of romantic nature when L.D.W. is present without prior discussion',
            'Both parents shall ensure appropriate supervision at all times',
        ],
    },
    {
        'section': 'Enforcement',
        'provisions': [
            'Violation of this plan may result in contempt (MCR 3.606)',
            'Make-up time shall be granted for denied parenting time (MCL 722.27a(7)(c))',
            'Costs and fees may be assessed for violations',
        ],
    },
]

def main():
    print("=" * 70)
    print("PARENTING PLAN PROPOSAL GENERATOR — Tool #139")
    print("=" * 70)
    
    lines = [
        "# 👨‍👧 PARENTING PLAN PROPOSALS",
        f"*Generated: {datetime.now().strftime('%Y-%m-%d %H:%M')} | Tool #139*",
        f"*Three plans — from best outcome to minimum acceptable*\n",
        "---\n",
    ]
    
    for key, plan in PARENTING_PLANS.items():
        lines.append(f"## {plan['name']}")
        lines.append(f"*When to use: {plan['when']}*\n")
        
        for sched_key, sched_val in plan['schedule'].items():
            lines.append(f"**{sched_key.title()}:** {sched_val}")
        
        lines.append("\n---\n")
        print(f"  👨‍👧 {plan['name']}")
    
    lines.append("## STANDARD PROVISIONS (Apply to All Plans)\n")
    
    for prov in PLAN_PROVISIONS:
        lines.append(f"### {prov['section']}\n")
        for p in prov['provisions']:
            lines.append(f"- {p}")
        lines.append("")
    
    total_provisions = sum(len(p['provisions']) for p in PLAN_PROVISIONS)
    
    lines.extend([
        "---\n",
        "## STRATEGY\n",
        "1. **Present Plan A** (primary custody) — this is what you really want",
        "2. **Have Plan B ready** as a compromise if the judge pushes back",
        "3. **Plan C is your floor** — do not accept less than this",
        "4. **The specific provisions** show the judge you've thought this through",
        "5. **OurFamilyWizard** is preferred by Michigan courts for high-conflict cases\n",
        
        f"*{len(PARENTING_PLANS)} plans · {total_provisions} provisions · Present the one that fits*",
    ])
    
    md_path = REPORTS_DIR / "PARENTING_PLANS.md"
    md_path.write_text('\n'.join(lines), encoding='utf-8')
    
    json_path = REPORTS_DIR / "parenting_plans.json"
    json_path.write_text(json.dumps({
        'generated': datetime.now().isoformat(),
        'tool': 'Parenting Plan Proposal Generator (#139)',
        'plans': len(PARENTING_PLANS),
        'provisions': total_provisions,
    }, indent=2), encoding='utf-8')
    
    print(f"\n✅ {len(PARENTING_PLANS)} parenting plans + {total_provisions} standard provisions")
    print(f"   Reports: PARENTING_PLANS.md + parenting_plans.json")

if __name__ == '__main__':
    main()
