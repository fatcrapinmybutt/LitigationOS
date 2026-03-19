#!/usr/bin/env python3
"""
Tool #133 — Courtroom Demeanor Coach
=================================================
🆕 NOVEL TOOL — Behavioral guide for pro se litigants.

Studies show judges form opinions in the first 30 seconds.
This tool trains Andrew on courtroom etiquette, body language,
verbal discipline, and emotional regulation.
"""
import sys, json
from pathlib import Path
from datetime import datetime

sys.stdout = open(sys.stdout.fileno(), mode='w', encoding='utf-8', errors='replace')

REPO = Path(r"C:\Users\andre\LitigationOS")
REPORTS_DIR = REPO / "00_SYSTEM" / "reports"

RULES = {
    'before_court': {
        'title': 'Before Court (Preparation)',
        'rules': [
            {'rule': 'Arrive 30 minutes early', 'why': 'Allows time to find the courtroom, calm nerves, and review notes'},
            {'rule': 'Dress professionally (suit or business casual)', 'why': 'Appearance signals you take the court seriously'},
            {'rule': 'Bring 3 copies of everything (judge, opposing party, yourself)', 'why': 'Courts expect copies — being unprepared looks bad'},
            {'rule': 'Organize documents in a labeled binder with tabs', 'why': 'Fumbling for papers wastes the court\'s time'},
            {'rule': 'Eat and hydrate beforehand', 'why': 'You need to be sharp — hunger and dehydration cloud thinking'},
            {'rule': 'Use the bathroom before entering', 'why': 'Asking to leave mid-hearing looks unprofessional'},
            {'rule': 'Silence your phone completely', 'why': 'A ringing phone can result in contempt'},
            {'rule': 'Review your key arguments one final time', 'why': 'Fresh memory of main points prevents freezing'},
        ],
    },
    'entering_courtroom': {
        'title': 'Entering the Courtroom',
        'rules': [
            {'rule': 'Stand when the judge enters', 'why': 'Universal sign of respect — EVERYONE does this'},
            {'rule': 'Do not chew gum or eat', 'why': 'Immediate disrespect — judges notice everything'},
            {'rule': 'Sit at the plaintiff/petitioner table (usually left)', 'why': 'Court convention — ask clerk if unsure'},
            {'rule': 'Place documents on the table neatly organized', 'why': 'Visual organization signals mental organization'},
        ],
    },
    'speaking': {
        'title': 'Speaking to the Judge',
        'rules': [
            {'rule': 'Always address the judge as "Your Honor"', 'why': 'Required — anything else is disrespectful'},
            {'rule': 'Stand when speaking unless told otherwise', 'why': 'Court convention for all speakers'},
            {'rule': 'Speak clearly and at a moderate pace', 'why': 'The court reporter needs to capture every word'},
            {'rule': 'Never interrupt the judge', 'why': 'Fastest way to lose credibility and possibly be held in contempt'},
            {'rule': 'Answer questions directly — then explain', 'why': 'Judges hate evasion; answer YES/NO first, then elaborate'},
            {'rule': 'Say "I don\'t know" if you don\'t know', 'why': 'Better than guessing — honesty builds credibility'},
            {'rule': 'Ask permission before approaching the bench or witness', 'why': '"May I approach, Your Honor?" — always ask first'},
        ],
    },
    'emotional_control': {
        'title': 'Emotional Regulation (CRITICAL)',
        'rules': [
            {'rule': 'NEVER raise your voice', 'why': 'Emotional outbursts destroy credibility instantly'},
            {'rule': 'If you feel angry, take a slow breath before speaking', 'why': '3-second pause resets your emotional state'},
            {'rule': 'Do not react to opposing party\'s statements visibly', 'why': 'Eye rolls, sighs, and head shakes are noticed by judges'},
            {'rule': 'Do not argue with opposing party directly — address the judge', 'why': '"Your Honor, the opposing party\'s claim is contradicted by..."'},
            {'rule': 'If Emily or Berry provoke you, IGNORE IT', 'why': 'They may try to make you lose composure — don\'t give them that'},
            {'rule': 'If you feel overwhelmed, ask for a brief recess', 'why': '"Your Honor, may I have a brief moment to collect my thoughts?"'},
        ],
    },
    'body_language': {
        'title': 'Body Language',
        'rules': [
            {'rule': 'Maintain respectful eye contact with the judge', 'why': 'Shows confidence and honesty'},
            {'rule': 'Keep hands visible on the table or at your sides', 'why': 'Hidden hands signal deception (subconsciously)'},
            {'rule': 'Sit up straight', 'why': 'Slouching signals disinterest or disrespect'},
            {'rule': 'Nod slightly when the judge speaks to show you\'re listening', 'why': 'Active listening builds rapport'},
            {'rule': 'Do NOT point at opposing party', 'why': 'Aggressive gesture — refer to them by name instead'},
        ],
    },
    'after_hearing': {
        'title': 'After the Hearing',
        'rules': [
            {'rule': 'Thank the judge regardless of outcome', 'why': '"Thank you, Your Honor" — always professional'},
            {'rule': 'Do not celebrate or show disappointment visibly', 'why': 'The judge may still be watching'},
            {'rule': 'Immediately write down everything that happened', 'why': 'Memory fades fast — detailed notes preserve the record'},
            {'rule': 'Ask the clerk for copies of any orders entered', 'why': 'You need the exact language for compliance or appeal'},
            {'rule': 'Do not confront opposing party in the hallway', 'why': 'Anything you say can be used against you'},
        ],
    },
}

def main():
    print("=" * 70)
    print("COURTROOM DEMEANOR COACH — Tool #133")
    print("=" * 70)
    
    total_rules = sum(len(cat['rules']) for cat in RULES.values())
    
    lines = [
        "# 🎭 COURTROOM DEMEANOR COACH",
        f"*Generated: {datetime.now().strftime('%Y-%m-%d %H:%M')} | Tool #133*",
        f"*{total_rules} rules for courtroom success*\n",
        "---\n",
        "## THE #1 RULE\n",
        "> **The judge is deciding your child's future.**",
        "> **Everything you do and say will be evaluated.**",
        "> **Calm, prepared, and respectful wins. Always.**\n",
        "---\n",
    ]
    
    for section_key, section in RULES.items():
        lines.append(f"## {section['title']}\n")
        lines.append("| Rule | Why |")
        lines.append("|------|-----|")
        for r in section['rules']:
            lines.append(f"| {r['rule']} | {r['why']} |")
        lines.append("")
        print(f"  🎭 {section['title']}: {len(section['rules'])} rules")
    
    lines.extend([
        "---\n",
        "## 🚫 THINGS THAT WILL HURT YOUR CASE\n",
        "1. Losing your temper — even once — can define the judge's perception of you",
        "2. Badmouthing Emily in court — focus on FACTS, not character attacks",
        "3. Being unprepared — fumbling for papers signals you don't take this seriously",
        "4. Lying or exaggerating — one caught lie destroys ALL your credibility",
        "5. Ignoring court rules — pro se litigants are held to the same procedural rules\n",
        
        "## ✅ THINGS THAT WILL HELP YOUR CASE\n",
        "1. Being the most prepared person in the room",
        "2. Citing specific evidence and authority (not just emotions)",
        "3. Showing genuine concern for L.D.W.'s wellbeing (not just winning)",
        "4. Being respectful to everyone — judge, clerk, opposing party",
        "5. Following through on every promise made to the court\n",
        
        f"*{total_rules} rules across {len(RULES)} phases of courtroom conduct*",
    ])
    
    md_path = REPORTS_DIR / "DEMEANOR_COACH.md"
    md_path.write_text('\n'.join(lines), encoding='utf-8')
    
    json_path = REPORTS_DIR / "demeanor_coach.json"
    json_path.write_text(json.dumps({
        'generated': datetime.now().isoformat(),
        'tool': 'Courtroom Demeanor Coach (#133)',
        'total_rules': total_rules,
        'sections': len(RULES),
    }, indent=2), encoding='utf-8')
    
    print(f"\n✅ {total_rules} courtroom rules across {len(RULES)} phases")
    print(f"   READ THIS BEFORE EVERY HEARING")
    print(f"   Reports: DEMEANOR_COACH.md + demeanor_coach.json")

if __name__ == '__main__':
    main()
