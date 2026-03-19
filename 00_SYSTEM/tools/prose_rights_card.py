#!/usr/bin/env python3
"""
Tool #78 — Pro Se Rights Quick Reference Card
=================================================
A pocket-sized reference of ALL procedural rights Andrew has
as a pro se litigant across all courts.

Designed to be printed on a single page and carried to court.
"""
import sys, json
from pathlib import Path
from datetime import datetime

sys.stdout = open(sys.stdout.fileno(), mode='w', encoding='utf-8', errors='replace')

REPO = Path(r"C:\Users\andre\LitigationOS")
REPORTS_DIR = REPO / "00_SYSTEM" / "reports"
PKG_BASE = Path(r"C:\Users\andre\Desktop\LITIGATION_FILING_PACKAGE")

RIGHTS = {
    'constitutional': {
        'title': '🇺🇸 Constitutional Rights',
        'items': [
            ('Due Process', '14th Amendment — notice and hearing before deprivation of liberty interest (parental rights). Mathews v Eldridge, 424 US 319.'),
            ('Equal Protection', '14th Amendment — cannot be treated differently than represented parties. Haines v Kerner, 404 US 519 (pro se filings held to less stringent standards).'),
            ('Access to Courts', '1st/14th Amendment — cannot be denied meaningful access. Bounds v Smith, 430 US 817.'),
            ('Parental Liberty', 'Fundamental right to care and custody of children. Troxel v Granville, 530 US 57.'),
        ],
    },
    'michigan_court': {
        'title': '⚖️ Michigan Court Rights',
        'items': [
            ('Right to Self-Represent', 'MCR 2.117(A) — parties may appear pro se in all Michigan courts.'),
            ('Liberal Construction', 'Pro se pleadings are held to less stringent standards. Estelle v Gamble, 429 US 97.'),
            ('Right to Be Heard', 'MCR 2.119(E) — oral argument on motions upon request.'),
            ('Right to Discovery', 'MCR 2.302 — same discovery rights as represented parties.'),
            ('Right to Trial', 'MCR 2.508/2.509 — right to jury/bench trial.'),
            ('Right to Appeal', 'MCR 7.203 — appeal as of right from final orders.'),
            ('Right to Record', 'MCR 8.108 — right to court reporter at all hearings.'),
            ('Right to Continuance', 'MCR 2.503 — may request adjournment for good cause.'),
        ],
    },
    'federal_court': {
        'title': '🏛️ Federal Court Rights',
        'items': [
            ('IFP Right', '28 USC §1915 — proceed without payment if financially unable.'),
            ('US Marshals Service', 'FRCP 4(c)(3) — if IFP, court orders US Marshals to serve.'),
            ('Liberal Pleading', 'FRCP 8(a) — short and plain statement of claim.'),
            ('Discovery Rights', 'FRCP 26-37 — full discovery rights same as attorneys.'),
            ('Right to Amend', 'FRCP 15(a) — may amend complaint once as matter of course within 21 days.'),
        ],
    },
    'hearing': {
        'title': '🎤 At Hearings / In Court',
        'items': [
            ('Object to Everything Improper', 'You have the RIGHT to object. Say: "Objection, [ground]." Common grounds: hearsay, relevance, foundation, speculation.'),
            ('Request Time', '"Your Honor, I request a brief recess to review this document."'),
            ('Request Clarification', '"Your Honor, could the Court clarify its ruling for the record?"'),
            ('Preserve the Record', 'State objections ON THE RECORD. If overruled, say: "Noting my objection for the record."'),
            ('Request Written Order', '"Your Honor, I respectfully request a written order with findings of fact and conclusions of law."'),
            ('Request Stay Pending Appeal', '"Your Honor, I respectfully request a stay of this order pending appeal pursuant to MCR 7.209."'),
        ],
    },
    'protections': {
        'title': '🛡️ Key Protections',
        'items': [
            ('Anti-Retaliation', 'Cannot be punished for exercising right to file motions/appeals. Thaddeus-X v Blatter, 175 F.3d 378 (6th Cir).'),
            ('Good Faith Filings', 'MCR 2.114 — filings made in good faith are protected from sanctions.'),
            ('Recusal Right', 'MCR 2.003 — right to move for disqualification of biased judge.'),
            ('Fee Waiver', 'MC 20 / AO 240 — right to waive fees if unable to pay.'),
            ('Sealed Records', 'MCR 8.119(H) — minor\'s name protected (use initials: L.D.W.).'),
        ],
    },
}

def main():
    print("=" * 70)
    print("PRO SE RIGHTS QUICK REFERENCE — Tool #78")
    print("=" * 70)
    
    total_rights = sum(len(cat['items']) for cat in RIGHTS.values())
    
    lines = [
        "# 📋 PRO SE RIGHTS — QUICK REFERENCE CARD",
        "## Andrew James Pigors — Pigors v. Watson",
        f"*{total_rights} rights across {len(RIGHTS)} categories*",
        "*Print this and bring to EVERY court appearance*\n",
        "---\n",
    ]
    
    for cat_id, category in RIGHTS.items():
        lines.append(f"## {category['title']}\n")
        for right_name, description in category['items']:
            lines.append(f"**{right_name}**: {description}\n")
            print(f"  ✓ {right_name}")
        lines.append("")
    
    lines.extend([
        "---",
        "## 🚨 EMERGENCY PHRASES (memorize these)",
        "",
        "**If denied the right to speak:**",
        '> "Your Honor, I respectfully request the opportunity to be heard',
        '> before the Court rules. Due process requires notice and hearing."',
        "",
        "**If opposing counsel makes ex-parte contact:**",
        '> "Your Honor, I object. Opposing counsel has communicated with',
        '> the Court outside my presence in violation of MRPC 3.5(b)."',
        "",
        "**If the judge shows hostility:**",
        '> "Your Honor, I respectfully note for the record that I am',
        '> concerned about the appearance of impartiality, and I preserve',
        '> my right to file a motion for disqualification under MCR 2.003."',
        "",
        "**If asked to waive rights:**",
        '> "Your Honor, I do not waive any rights. I preserve all rights',
        '> to appeal, to due process, and to equal protection."',
        "",
        "---",
        f"*Pro Se Rights Quick Reference — Tool #78*",
        f"*{total_rights} rights | Print and carry to court*",
    ])
    
    md_path = REPORTS_DIR / "PRO_SE_RIGHTS_CARD.md"
    md_path.write_text('\n'.join(lines), encoding='utf-8')
    
    # Save to key filing packages
    for pkg in ['PKG_F1', 'PKG_F3', 'PKG_F7']:
        pkg_path = PKG_BASE / pkg
        if pkg_path.exists():
            (pkg_path / "14_PRO_SE_RIGHTS_CARD.md").write_text('\n'.join(lines), encoding='utf-8')
    
    json_path = REPORTS_DIR / "prose_rights_card.json"
    json_path.write_text(json.dumps({
        'generated': datetime.now().isoformat(),
        'tool': 'Pro Se Rights Quick Reference (#78)',
        'total_rights': total_rights,
        'categories': len(RIGHTS),
        'rights': {k: {'title': v['title'], 'count': len(v['items'])} for k, v in RIGHTS.items()},
    }, indent=2), encoding='utf-8')
    
    print(f"\n✅ {total_rights} rights compiled across {len(RIGHTS)} categories")
    print(f"   Saved to reports/ + PKG_F1/F3/F7")

if __name__ == '__main__':
    main()
