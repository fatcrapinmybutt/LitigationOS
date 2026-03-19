#!/usr/bin/env python3
"""
Tool #106 — Pro Se Hearing Simulator
=========================================
🆕 TRULY NOVEL — Nothing like this exists

Generates a mock hearing script that Andrew can practice:
- Judge's likely questions
- Opposing counsel's likely objections
- Andrew's prepared responses
- Proper courtroom procedure flow

This is like a flight simulator for court hearings.
Practice makes perfect — especially for pro se litigants.
"""
import sys, json
from pathlib import Path
from datetime import datetime

sys.stdout = open(sys.stdout.fileno(), mode='w', encoding='utf-8', errors='replace')

REPO = Path(r"C:\Users\andre\LitigationOS")
REPORTS_DIR = REPO / "00_SYSTEM" / "reports"

HEARING_SCRIPTS = {
    'F1_emergency': {
        'title': 'Emergency Motion for Parenting Time',
        'court': '14th Circuit Court, Family Division',
        'estimated_duration': '15-30 minutes',
        'script': [
            {
                'speaker': 'CLERK',
                'text': 'All rise. The 14th Circuit Court for the County of Muskegon is now in session. The Honorable [Judge] presiding.',
                'instruction': 'Stand. Remain standing until told to sit.',
            },
            {
                'speaker': 'JUDGE',
                'text': 'Please be seated. We are here on the matter of Pigors v. Watson, case number 2024-001507-DC. Mr. Pigors, you filed an emergency motion for parenting time?',
                'instruction': 'Stand when addressed. "Yes, Your Honor."',
            },
            {
                'speaker': 'ANDREW',
                'text': 'Yes, Your Honor. I filed an emergency motion pursuant to MCL 722.27a seeking restoration of my parenting time with my child, L.D.W.',
                'instruction': 'Be clear, concise, confident. Reference the statute.',
            },
            {
                'speaker': 'JUDGE',
                'text': 'What is the emergency nature of this motion?',
                'instruction': 'This is your opening. Hit the key points.',
            },
            {
                'speaker': 'ANDREW',
                'text': 'Your Honor, my parenting time has been completely suspended without the required findings under MCL 722.27a(3). Every day without contact causes irreparable harm to the parent-child bond. Under Shade v Wright, 291 Mich App 17, I have a fundamental right to parenting time absent clear and convincing evidence of harm — and no such evidence exists.',
                'instruction': 'Cite the statute AND case law. Show you know the standard.',
            },
            {
                'speaker': 'OPPOSING',
                'text': 'Your Honor, the respondent respectfully objects. The court\'s prior orders suspended parenting time based on safety concerns.',
                'instruction': 'Listen carefully. Note the specific basis claimed.',
            },
            {
                'speaker': 'JUDGE',
                'text': 'Mr. Pigors, what safety concerns were raised?',
                'instruction': 'This is where you expose the fraud. Stay calm and factual.',
            },
            {
                'speaker': 'ANDREW',
                'text': 'Your Honor, the only "safety concern" was an allegation that I threw a straw near my child — a straw. There was no medical evidence, no police report, no CPS investigation, and no corroborating witness. I respectfully submit this was a fabricated incident used to obtain an improper PPO, and the suspension of my parenting time is the fruit of that initial fraud.',
                'instruction': 'Stay measured. "A straw" is powerful — let the absurdity speak for itself.',
            },
            {
                'speaker': 'JUDGE',
                'text': 'Do you have evidence to support your position?',
                'instruction': 'This is where your 200 exhibits and database pay off.',
            },
            {
                'speaker': 'ANDREW',
                'text': 'Yes, Your Honor. I have [X] exhibits including text messages, email communications, and documented instances of parenting time interference. I also have evidence showing the respondent\'s statements contain material contradictions. May I approach with my exhibits?',
                'instruction': 'Always ask "May I approach?" before handing anything to the judge.',
            },
            {
                'speaker': 'JUDGE',
                'text': 'You may.',
                'instruction': 'Walk to the bench, hand exhibits to clerk, return to your position.',
            },
            {
                'speaker': 'ANDREW',
                'text': 'Your Honor, I direct the court\'s attention to Exhibit 1, which shows [specific evidence]. This demonstrates that the respondent has systematically denied my parenting time. Under MCL 722.23(j), the court must consider which parent is more likely to facilitate a close and continuing relationship. The evidence shows I have consistently sought contact while the respondent has consistently blocked it.',
                'instruction': 'Factor (j) is your STRONGEST factor. Hit it hard.',
            },
        ],
    },
    'F3_disqualification': {
        'title': 'Motion for Judicial Disqualification',
        'court': '14th Circuit Court',
        'estimated_duration': '10-20 minutes',
        'script': [
            {
                'speaker': 'JUDGE',
                'text': 'Mr. Pigors, you have filed a motion for my disqualification under MCR 2.003. I will hear your argument.',
                'instruction': 'Note: The judge being disqualified often hears the initial motion. Stay respectful.',
            },
            {
                'speaker': 'ANDREW',
                'text': 'Thank you, Your Honor. I have filed this motion pursuant to MCR 2.003(C)(1)(b), which requires disqualification when a judge has personal bias or prejudice concerning a party. I do not bring this motion lightly, and I intend no personal disrespect to the court.',
                'instruction': 'CRITICAL: Start with respect. You\'re challenging the judge TO the judge.',
            },
            {
                'speaker': 'ANDREW',
                'text': 'Your Honor, I have documented [specific number] instances that, taken together, demonstrate an appearance of impropriety under Canon 2 of the Michigan Code of Judicial Conduct. These include [cite 2-3 strongest examples].',
                'instruction': 'Don\'t list all 1,127. Pick the 3 STRONGEST and go deep.',
            },
            {
                'speaker': 'JUDGE',
                'text': 'Mr. Pigors, adverse rulings alone are not evidence of bias.',
                'instruction': 'Expected response. You have the comeback ready.',
            },
            {
                'speaker': 'ANDREW',
                'text': 'I agree, Your Honor. Adverse rulings alone are not sufficient under Cain v Department of Corrections, 451 Mich 470. However, what I am presenting is not adverse rulings — it is a pattern of procedural irregularities including [ex-parte communications / denial of hearing / lack of notice] that goes beyond mere disagreement with outcomes. Under Armstrong v Ypsilanti Township, 248 Mich App 573, a pattern of conduct can establish bias.',
                'instruction': 'Distinguish "adverse rulings" from "procedural bias." This is the winning argument.',
            },
        ],
    },
}

def main():
    print("=" * 70)
    print("PRO SE HEARING SIMULATOR — Tool #106")
    print("=" * 70)
    
    lines = [
        "# 🎭 PRO SE HEARING SIMULATOR",
        f"*Generated: {datetime.now().strftime('%Y-%m-%d %H:%M')} | Tool #106*",
        "*PRACTICE THESE SCRIPTS OUT LOUD BEFORE EVERY HEARING*\n",
        "---\n",
    ]
    
    total_exchanges = 0
    
    for key, hearing in HEARING_SCRIPTS.items():
        lines.extend([
            f"## 🎬 {hearing['title']}",
            f"**Court:** {hearing['court']}",
            f"**Duration:** {hearing['estimated_duration']}\n",
            "---\n",
        ])
        
        for exchange in hearing['script']:
            speaker = exchange['speaker']
            emoji = {'JUDGE': '⚖️', 'ANDREW': '💪', 'OPPOSING': '⚔️', 'CLERK': '📋'}
            
            lines.extend([
                f"### {emoji.get(speaker, '👤')} {speaker}",
                f"> {exchange['text']}\n",
                f"*📝 {exchange['instruction']}*\n",
            ])
            total_exchanges += 1
        
        lines.append("---\n")
        print(f"  🎬 {hearing['title'][:35]}: {len(hearing['script'])} exchanges")
    
    lines.extend([
        "## 🎯 PRACTICE TIPS\n",
        "1. **Read aloud** — your voice needs to sound confident, not angry",
        "2. **Time yourself** — each response should be 30-60 seconds max",
        "3. **Record yourself** — listen back for pacing and tone",
        "4. **Practice standing** — you'll stand when speaking to the judge",
        "5. **Have exhibits ready** — practice finding the right one quickly",
        "6. **Breathe** — pause before responding. It shows confidence, not hesitation.",
        "7. **The judge is human** — respectful, prepared litigants get better outcomes",
        "",
        f"*Hearing Simulator — Tool #106 — {total_exchanges} practice exchanges*",
    ])
    
    md_path = REPORTS_DIR / "HEARING_SIMULATOR.md"
    md_path.write_text('\n'.join(lines), encoding='utf-8')
    
    json_path = REPORTS_DIR / "hearing_simulator.json"
    json_path.write_text(json.dumps({
        'generated': datetime.now().isoformat(),
        'tool': 'Hearing Simulator (#106)',
        'hearings': len(HEARING_SCRIPTS),
        'total_exchanges': total_exchanges,
        'scripts': list(HEARING_SCRIPTS.keys()),
    }, indent=2), encoding='utf-8')
    
    print(f"\n✅ {len(HEARING_SCRIPTS)} hearing scripts with {total_exchanges} exchanges")
    print(f"   PRACTICE OUT LOUD BEFORE EVERY HEARING")
    print(f"   Reports: HEARING_SIMULATOR.md + hearing_simulator.json")

if __name__ == '__main__':
    main()
