#!/usr/bin/env python3
"""
Tool #163 — Courtroom Etiquette & Protocol Guide
=================================================
🆕 NOVEL TOOL — Comprehensive guide to courtroom behavior,
pro se protocol, and how to present yourself as a
credible, professional litigant.
"""
import sys, json
from pathlib import Path
from datetime import datetime

sys.stdout = open(sys.stdout.fileno(), mode='w', encoding='utf-8', errors='replace')

REPO = Path(r"C:\Users\andre\LitigationOS")
REPORTS_DIR = REPO / "00_SYSTEM" / "reports"

ETIQUETTE = {
    'address_the_court': [
        'Always say "Your Honor" — never "Judge" or first name',
        'Stand when speaking to the judge',
        'Stand when the judge enters or leaves',
        'Begin with: "May it please the Court..."',
        'End arguments with: "Thank you, Your Honor"',
        'If interrupted: stop immediately, wait, then continue',
    ],
    'speak_properly': [
        '"I would like to direct the Court\'s attention to..."',
        '"Respectfully, Your Honor, I disagree because..."',
        '"For the record, I object on the basis of..."',
        '"May I approach the bench/witness, Your Honor?"',
        '"I have no further questions for this witness"',
        'NEVER: "That\'s a lie" — instead: "That statement is contradicted by Exhibit [X]"',
        'NEVER: "She\'s lying" — instead: "The testimony is inconsistent with [document]"',
        'NEVER: argue with opposing counsel directly — always through the judge',
    ],
    'dress_code': [
        'Dark suit (navy or charcoal) with conservative tie',
        'White or light blue dress shirt',
        'Polished dress shoes (no sneakers, no sandals)',
        'No hat, no sunglasses, no visible electronics',
        'Minimal jewelry — wedding band only',
        'Clean-shaven or neatly groomed',
        'Professional briefcase or portfolio (not a backpack)',
    ],
    'document_handling': [
        'Organize all documents in a labeled binder with tabs',
        'Have 4 copies minimum: yours, judge, opposing, clerk',
        'Pre-mark all exhibits (Exhibit A, B, C...)',
        'When presenting: "Your Honor, I offer Exhibit [X] for identification"',
        'Wait for the judge to admit before referencing the exhibit',
        'Never hand documents directly to the judge — give to the clerk',
    ],
    'common_mistakes': [
        'Talking over the judge — FATAL',
        'Arguing with opposing counsel — unprofessional',
        'Getting emotional — understandable but damaging',
        'Not having enough copies — looks unprepared',
        'Bringing up issues not on the motion — stay focused',
        'Failing to object timely — waives the issue',
        'Not preserving the record — object clearly for appeal',
        'Speaking without being recognized — wait to be called on',
    ],
}

def main():
    print("=" * 70)
    print("COURTROOM ETIQUETTE & PROTOCOL — Tool #163")
    print("=" * 70)

    lines = [
        "# 🎩 COURTROOM ETIQUETTE & PROTOCOL",
        f"*Generated: {datetime.now().strftime('%Y-%m-%d %H:%M')} | Tool #163*",
        f"*How to present yourself as credible, professional, and prepared*\n",
        "---\n",
    ]

    total_items = 0
    for category, items in ETIQUETTE.items():
        title = category.replace('_', ' ').title()
        lines.append(f"## {title}\n")
        for item in items:
            marker = "❌" if "NEVER" in item or "FATAL" in item else "✅"
            lines.append(f"- {marker} {item}")
        lines.append("")
        total_items += len(items)
        print(f"  🎩 {title}: {len(items)} rules")

    lines.extend([
        "---\n",
        "## 🎯 THE PRO SE ADVANTAGE\n",
        "> Judges WANT pro se litigants to succeed. They know you don't have",
        "> a law degree. They will give you reasonable latitude — but ONLY if",
        "> you show them respect and preparation.\n",
        "> **Prepared + Professional + Respectful = Credible.**",
        "> **Credible = Judge listens to you.**",
        "> **Judge listens = You win.**\n",
        f"*{len(ETIQUETTE)} categories · {total_items} rules · Master these before your first hearing*",
    ])

    md_path = REPORTS_DIR / "COURTROOM_ETIQUETTE.md"
    md_path.write_text('\n'.join(lines), encoding='utf-8')

    json_path = REPORTS_DIR / "courtroom_etiquette.json"
    json_path.write_text(json.dumps({
        'generated': datetime.now().isoformat(),
        'tool': 'Courtroom Etiquette & Protocol (#163)',
        'categories': len(ETIQUETTE),
        'total_rules': total_items,
    }, indent=2), encoding='utf-8')

    print(f"\n✅ {len(ETIQUETTE)} categories, {total_items} rules")
    print(f"   Reports: COURTROOM_ETIQUETTE.md + courtroom_etiquette.json")

if __name__ == '__main__':
    main()
