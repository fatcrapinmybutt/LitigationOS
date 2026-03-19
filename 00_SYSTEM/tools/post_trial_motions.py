#!/usr/bin/env python3
"""
Tool #110 — Post-Trial Motion Template Engine
=================================================
🆕 NOVEL TOOL — Templates for motions AFTER adverse rulings

If the court rules against Andrew, these are ready to file:
- MCR 2.611: Motion for New Trial (14 days)
- MCR 2.612: Relief from Judgment (various deadlines)
- MCR 2.119: Motion for Reconsideration (21 days)

Having these pre-built means Andrew can file IMMEDIATELY
instead of scrambling after a bad ruling.
"""
import sys, json
from pathlib import Path
from datetime import datetime

sys.stdout = open(sys.stdout.fileno(), mode='w', encoding='utf-8', errors='replace')

REPO = Path(r"C:\Users\andre\LitigationOS")
REPORTS_DIR = REPO / "00_SYSTEM" / "reports"

MOTIONS = {
    'new_trial': {
        'title': 'MOTION FOR NEW TRIAL / TO SET ASIDE VERDICT',
        'rule': 'MCR 2.611',
        'deadline': '14 days after entry of judgment',
        'grounds': [
            {
                'rule': 'MCR 2.611(A)(1)(a)',
                'ground': 'Irregularity in the proceedings that denied a fair trial',
                'when_to_use': 'Judge refused to hear testimony, excluded evidence improperly, or denied opportunity to present case',
                'template': 'The Court committed irregularity in the proceedings by [specific irregularity], which denied Plaintiff a fair trial. Specifically, [describe what happened]. This irregularity was prejudicial because [explain how it affected the outcome].',
            },
            {
                'rule': 'MCR 2.611(A)(1)(b)',
                'ground': 'Excessive or inadequate damages',
                'when_to_use': 'Parenting time order is disproportionate to the evidence',
                'template': 'The Court\'s order is disproportionate to the evidence presented. The record shows [evidence], yet the Court ordered [outcome]. This constitutes an inadequate/excessive remedy because [explain].',
            },
            {
                'rule': 'MCR 2.611(A)(1)(f)',
                'ground': 'Verdict/decision is against the great weight of evidence',
                'when_to_use': 'Evidence overwhelmingly supported Andrew but court ruled against him',
                'template': 'The Court\'s decision is against the great weight of the evidence. Plaintiff presented [describe evidence], which established [facts]. The Court\'s contrary finding cannot be reconciled with this evidence because [explain].',
            },
        ],
    },
    'relief_from_judgment': {
        'title': 'MOTION FOR RELIEF FROM JUDGMENT',
        'rule': 'MCR 2.612',
        'deadline': 'Varies: 1 year for (a)-(c); "reasonable time" for (d)-(f); NO limit for fraud on court',
        'grounds': [
            {
                'rule': 'MCR 2.612(C)(1)(a)',
                'ground': 'Mistake, inadvertence, surprise, or excusable neglect',
                'when_to_use': 'Pro se litigant missed procedural requirement, or court made factual error',
                'template': 'Plaintiff moves for relief under MCR 2.612(C)(1)(a) based on [mistake/inadvertence]. Specifically, [describe what happened]. Relief is warranted because [explain why the error affected the judgment].',
            },
            {
                'rule': 'MCR 2.612(C)(1)(b)',
                'ground': 'Newly discovered evidence',
                'when_to_use': 'Found new evidence after trial that would have changed outcome',
                'template': 'Plaintiff has discovered new evidence that was not available at the time of trial despite reasonable diligence. This evidence consists of [describe]. This evidence would likely have changed the outcome because [explain].',
            },
            {
                'rule': 'MCR 2.612(C)(1)(c)',
                'ground': 'Fraud, misrepresentation, or misconduct by opposing party',
                'when_to_use': 'Emily lied in court, fabricated evidence, or concealed information — YOUR STRONGEST GROUND',
                'template': 'Plaintiff moves for relief based on fraud/misrepresentation by Defendant. Specifically, Defendant [describe fraudulent conduct]. This fraud was material because [explain how it affected the judgment]. Evidence of this fraud includes [list evidence].',
            },
            {
                'rule': 'MCR 2.612(C)(1)(d)',
                'ground': 'Judgment is void',
                'when_to_use': 'Court lacked jurisdiction, violated due process, or judge was disqualified — NO TIME LIMIT',
                'template': 'The judgment is void because [lack of jurisdiction / due process violation / disqualified judge]. Specifically, [describe basis]. A void judgment may be challenged at any time. See Bowie v Arder, 441 Mich 23 (1992).',
            },
            {
                'rule': 'MCR 2.612(C)(3)',
                'ground': 'Independent action for fraud on the court',
                'when_to_use': 'The fraud is so egregious it undermines the integrity of the judicial process — NO TIME LIMIT',
                'template': 'This Court has inherent power to vacate judgments obtained by fraud upon the court. MCR 2.612(C)(3). The fraud here goes beyond party-on-party deception — it is an assault on the integrity of the judicial process itself. [Describe the systemic fraud].',
            },
        ],
    },
    'reconsideration': {
        'title': 'MOTION FOR RECONSIDERATION',
        'rule': 'MCR 2.119(F)',
        'deadline': '21 days after entry of order',
        'grounds': [
            {
                'rule': 'MCR 2.119(F)(3)',
                'ground': 'Palpable error by which the court and parties have been misled',
                'when_to_use': 'Court made a clear factual or legal error that can be pointed to specifically',
                'template': 'The Court committed palpable error by [describe error]. This error misled the Court into [describe consequence]. The correct analysis under [cite law] requires [explain correct analysis]. See MCR 2.119(F)(3).',
            },
        ],
    },
}

def main():
    print("=" * 70)
    print("POST-TRIAL MOTION TEMPLATE ENGINE — Tool #110")
    print("=" * 70)
    
    lines = [
        "# ⚡ POST-TRIAL MOTION TEMPLATES",
        f"*Generated: {datetime.now().strftime('%Y-%m-%d %H:%M')} | Tool #110*",
        "*PRE-BUILT — File within HOURS of an adverse ruling*\n",
        "---\n",
        "## ⏰ DEADLINE CHEAT SHEET\n",
        "| Motion | Rule | Deadline | Priority |",
        "|--------|------|----------|----------|",
        "| Reconsideration | MCR 2.119(F) | **21 days** | File first |",
        "| New Trial | MCR 2.611 | **14 days** | File simultaneously |",
        "| Relief (fraud) | MCR 2.612(C)(1)(c) | **1 year** | Can wait for evidence |",
        "| Relief (void) | MCR 2.612(C)(1)(d) | **NO LIMIT** | File when ready |",
        "| Fraud on Court | MCR 2.612(C)(3) | **NO LIMIT** | Nuclear option |",
        "",
    ]
    
    total_templates = 0
    
    for key, motion in MOTIONS.items():
        lines.extend([
            f"## {motion['title']}",
            f"**Rule:** {motion['rule']}",
            f"**Deadline:** {motion['deadline']}\n",
        ])
        
        for ground in motion['grounds']:
            lines.extend([
                f"### {ground['rule']}: {ground['ground']}\n",
                f"**When to use:** {ground['when_to_use']}\n",
                f"**Template language:**",
                f"> {ground['template']}\n",
            ])
            total_templates += 1
        
        lines.append("---\n")
        print(f"  📄 {motion['title'][:40]}: {len(motion['grounds'])} grounds ({motion['deadline']})")
    
    lines.extend([
        "## 🎯 FILING STRATEGY AFTER ADVERSE RULING\n",
        "**Day 1 (same day as ruling):**",
        "1. File Motion for Reconsideration (MCR 2.119(F)) — 21-day deadline",
        "2. File Motion for New Trial (MCR 2.611) — 14-day deadline",
        "3. File Notice of Appeal if applicable\n",
        "**Day 2-7:**",
        "4. Prepare COA application for leave to appeal",
        "5. Prepare emergency stay motion if needed\n",
        "**Day 7-365:**",
        "6. File MCR 2.612(C)(1)(c) relief based on fraud evidence",
        "7. Gather additional evidence for appeal\n",
        "**No time limit:**",
        "8. MCR 2.612(C)(1)(d) — void judgment (can file anytime)",
        "9. MCR 2.612(C)(3) — fraud on the court (can file anytime)\n",
        
        "## ⚠️ CRITICAL NOTES\n",
        "1. **Do NOT miss the 14-day and 21-day deadlines** — these are jurisdictional",
        "2. **File protective motions** even if you plan to appeal — preserves all options",
        "3. **Reconsideration + New Trial + Appeal can all be filed simultaneously**",
        "4. **Void judgment** and **fraud on court** have NO time limit — your safety net",
        "5. **All templates need customization** — fill in specific facts from your case",
        "",
        f"*Post-Trial Motion Templates — Tool #110 — {total_templates} templates across 3 motion types*",
    ])
    
    md_path = REPORTS_DIR / "POST_TRIAL_MOTIONS.md"
    md_path.write_text('\n'.join(lines), encoding='utf-8')
    
    json_path = REPORTS_DIR / "post_trial_motions.json"
    json_path.write_text(json.dumps({
        'generated': datetime.now().isoformat(),
        'tool': 'Post-Trial Motion Templates (#110)',
        'motion_types': len(MOTIONS),
        'total_templates': total_templates,
        'deadlines': {k: v['deadline'] for k, v in MOTIONS.items()},
    }, indent=2), encoding='utf-8')
    
    print(f"\n✅ {total_templates} templates across {len(MOTIONS)} motion types")
    print(f"   Most critical: MCR 2.612(C)(1)(d) VOID — NO time limit")
    print(f"   Reports: POST_TRIAL_MOTIONS.md + post_trial_motions.json")

if __name__ == '__main__':
    main()
