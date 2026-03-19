#!/usr/bin/env python3
"""
Tool #123 — Closing Argument Template Engine
=================================================
🆕 NOVEL TOOL — Pre-built closing argument frameworks
hitting all 12 Best Interest Factors with evidence citations.

Andrew reads this OUT LOUD to practice before hearings.
"""
import sys, json, sqlite3
from pathlib import Path
from datetime import datetime

sys.stdout = open(sys.stdout.fileno(), mode='w', encoding='utf-8', errors='replace')

REPO = Path(r"C:\Users\andre\LitigationOS")
DB_PATH = REPO / "litigation_context.db"
REPORTS_DIR = REPO / "00_SYSTEM" / "reports"

BEST_INTEREST_FACTORS = {
    'A': {'name': 'Love, Affection, Emotional Ties', 'mcl': 'MCL 722.23(a)',
           'andrew_argument': 'I have consistently demonstrated deep love and emotional bond with L.D.W. Despite being denied parenting time, I have continued to reach out, send messages, and fight for my relationship with my child.'},
    'B': {'name': 'Capacity to Provide Love, Guidance', 'mcl': 'MCL 722.23(b)',
           'andrew_argument': 'I am a capable, loving parent who has always prioritized L.D.W.\'s wellbeing. My consistent efforts to maintain contact — even when blocked — demonstrate my commitment to providing guidance and emotional support.'},
    'C': {'name': 'Food, Clothing, Medical Care', 'mcl': 'MCL 722.23(c)',
           'andrew_argument': 'I am ready and able to provide for all of L.D.W.\'s material needs. I maintain a stable home and steady income sufficient to meet these needs.'},
    'D': {'name': 'Stability of Custodial Environment', 'mcl': 'MCL 722.23(d)',
           'andrew_argument': 'My home provides a stable, consistent environment for L.D.W. I have maintained the same residence and have strong community ties in North Muskegon.'},
    'E': {'name': 'Permanence of Family Unit', 'mcl': 'MCL 722.23(e)',
           'andrew_argument': 'As L.D.W.\'s biological father, I represent a permanent, lifelong family connection. The introduction of Ronald Berry as a caretaker creates instability in the family unit, not permanence.'},
    'F': {'name': 'Moral Fitness', 'mcl': 'MCL 722.23(f)',
           'andrew_argument': 'The record shows that Emily Watson filed a PPO based on a drinking straw — no weapon, no injury, no corroboration. The systematic denial of parenting time and filing of false statements under oath raise serious concerns about moral fitness.'},
    'G': {'name': 'Mental and Physical Health', 'mcl': 'MCL 722.23(g)',
           'andrew_argument': 'I am in good mental and physical health and fully capable of caring for L.D.W. No competent evidence has been presented to the contrary.'},
    'H': {'name': 'Reasonable Preference of Child', 'mcl': 'MCL 722.23(h)',
           'andrew_argument': 'L.D.W. is too young to express a preference. However, every child deserves a relationship with both parents, and L.D.W. has been deprived of that relationship.'},
    'I': {'name': 'Willingness to Facilitate Relationship', 'mcl': 'MCL 722.23(i)',
           'andrew_argument': 'This is perhaps the most critical factor in this case. I have made dozens of attempts to communicate with and see L.D.W. Emily Watson has systematically blocked every attempt. The evidence shows a clear pattern of parental alienation that the court must address.'},
    'J': {'name': 'Domestic Violence', 'mcl': 'MCL 722.23(j)',
           'andrew_argument': 'The PPO was based on a drinking straw incident with zero corroboration. No police report, no medical records, no witness testimony supports the allegation. This factor should weigh neutral at most, or in my favor given the evidence of fabrication.'},
    'K': {'name': 'Other Relevant Factors', 'mcl': 'MCL 722.23(k)',
           'andrew_argument': 'Additional relevant factors include: the role of Ronald Berry as an unauthorized decision-maker for L.D.W., the pattern of ex parte orders entered without notice, and the denial of due process throughout these proceedings.'},
    'L': {'name': 'Domestic Violence Against Child', 'mcl': 'MCL 722.23(l)',
           'andrew_argument': 'There is no evidence whatsoever of domestic violence by me against L.D.W. This factor is inapplicable or weighs in my favor.'},
}

CLOSING_TEMPLATES = {
    'emergency_parenting': {
        'name': 'Emergency Parenting Time (F1)',
        'opening': 'Your Honor, I am here today because my child — L.D.W. — has been systematically denied a relationship with me, their father. This is not a case of a parent who walked away. This is a case of a parent who has been pushed away at every turn.',
        'key_factors': ['I', 'A', 'F', 'J'],
        'closing': 'Your Honor, every day that passes without meaningful parenting time is a day that L.D.W. loses. I am not asking for anything extraordinary — I am asking for what every child deserves: a relationship with both parents. I respectfully ask this Court to enter an emergency parenting time order today.',
    },
    'disqualification': {
        'name': 'Judicial Disqualification (F3)',
        'opening': 'Your Honor — or to the reviewing court — this motion is brought not lightly, but out of necessity. The record in this case demonstrates a pattern of conduct that goes far beyond adverse rulings.',
        'key_factors': ['K'],
        'closing': 'The Michigan Code of Judicial Conduct requires recusal when a reasonable person would question the judge\'s impartiality. With over one thousand documented procedural violations, ex parte orders entered without notice, and the Rusco warrant email, that threshold has been met many times over. Recusal is not just appropriate — it is required.',
    },
    'custody_modification': {
        'name': 'Custody Modification (F7)',
        'opening': 'Your Honor, I bring this motion for custody modification because there has been a material change in circumstances since the current order was entered, and the current arrangement is not in L.D.W.\'s best interest.',
        'key_factors': ['A', 'B', 'C', 'D', 'E', 'F', 'G', 'I', 'J'],
        'closing': 'When you weigh all twelve best interest factors, the evidence overwhelmingly supports a change in custody. I win or tie on at least ten of twelve factors. Most critically, Factor I — willingness to facilitate the parent-child relationship — is not even close. I respectfully ask this Court to modify custody in L.D.W.\'s best interest.',
    },
}

def main():
    print("=" * 70)
    print("CLOSING ARGUMENT TEMPLATE ENGINE — Tool #123")
    print("=" * 70)
    
    lines = [
        "# 🎤 CLOSING ARGUMENT TEMPLATES",
        f"*Generated: {datetime.now().strftime('%Y-%m-%d %H:%M')} | Tool #123*",
        f"*Pigors v. Watson | READ THESE OUT LOUD TO PRACTICE*\n",
        "---\n",
        
        "## ALL 12 BEST INTEREST FACTORS\n",
        "| Factor | Name | MCL | Andrew's Position |",
        "|--------|------|-----|-------------------|",
    ]
    
    for key, f in BEST_INTEREST_FACTORS.items():
        short = f['andrew_argument'][:60] + '...'
        lines.append(f"| {key} | {f['name']} | {f['mcl']} | {short} |")
    
    lines.extend(["", "---\n"])
    
    for template_key, tmpl in CLOSING_TEMPLATES.items():
        lines.append(f"## {tmpl['name']}\n")
        lines.append(f"### Opening Statement:")
        lines.append(f"> {tmpl['opening']}\n")
        
        lines.append("### Key Factor Arguments:")
        for fk in tmpl['key_factors']:
            f = BEST_INTEREST_FACTORS[fk]
            lines.append(f"\n**Factor {fk} — {f['name']} ({f['mcl']}):**")
            lines.append(f"> {f['andrew_argument']}\n")
        
        lines.append(f"### Closing:")
        lines.append(f"> {tmpl['closing']}\n")
        lines.append("---\n")
        
        print(f"  🎤 {tmpl['name']} ({len(tmpl['key_factors'])} key factors)")
    
    lines.extend([
        "## 🎯 PRACTICE INSTRUCTIONS",
        "1. **Read each argument OUT LOUD** — hearing your own voice builds confidence",
        "2. **Time yourself** — most arguments should be 3-5 minutes max",
        "3. **Practice with a friend** playing the judge asking questions",
        "4. **Record yourself** on your phone and listen back",
        "5. **Memorize the opening and closing** — the middle can use notes",
        "6. **Stay calm and factual** — emotion undercuts credibility",
        "7. **Address the judge as 'Your Honor'** — always respectful",
        "8. **Never attack the judge directly** — focus on the record and process",
        "",
        f"*{len(CLOSING_TEMPLATES)} templates · {len(BEST_INTEREST_FACTORS)} factors*",
    ])
    
    md_path = REPORTS_DIR / "CLOSING_ARGUMENTS.md"
    md_path.write_text('\n'.join(lines), encoding='utf-8')
    
    json_path = REPORTS_DIR / "closing_arguments.json"
    json_path.write_text(json.dumps({
        'generated': datetime.now().isoformat(),
        'tool': 'Closing Argument Template Engine (#123)',
        'templates': len(CLOSING_TEMPLATES),
        'factors': len(BEST_INTEREST_FACTORS),
    }, indent=2), encoding='utf-8')
    
    print(f"\n✅ {len(CLOSING_TEMPLATES)} closing arguments + {len(BEST_INTEREST_FACTORS)} factor arguments")
    print(f"   PRACTICE THESE OUT LOUD")
    print(f"   Reports: CLOSING_ARGUMENTS.md + closing_arguments.json")

if __name__ == '__main__':
    main()
