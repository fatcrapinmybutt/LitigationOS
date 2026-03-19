#!/usr/bin/env python3
"""
Tool #145 — Cross-Examination Scripts
=================================================
🆕 NOVEL TOOL — Ready-to-use cross-examination question
sequences for every opposing witness.

Each script is designed to:
1. Establish a foundation
2. Lock the witness into a position
3. Impeach with contradicting evidence
4. Drive the point home for the judge
"""
import sys, json
from pathlib import Path
from datetime import datetime

sys.stdout = open(sys.stdout.fileno(), mode='w', encoding='utf-8', errors='replace')

REPO = Path(r"C:\Users\andre\LitigationOS")
REPORTS_DIR = REPO / "00_SYSTEM" / "reports"

CROSS_SCRIPTS = [
    {
        'witness': 'Emily A. Watson',
        'topic': 'The Straw Incident (PPO Foundation)',
        'objective': 'Expose that the PPO was based on a trivial incident with no corroboration',
        'questions': [
            {'q': 'Ms. Watson, your petition for a PPO was filed in October 2023, correct?', 'purpose': 'Establish timeline'},
            {'q': 'And the incident you described involved a drinking straw, correct?', 'purpose': 'Name the evidence'},
            {'q': 'Did you seek medical attention after this incident?', 'purpose': 'No injuries = no danger'},
            {'q': 'Did you call the police at the time of the incident?', 'purpose': 'No police = not frightened'},
            {'q': 'Were there any witnesses to this incident other than yourself?', 'purpose': 'No corroboration'},
            {'q': 'Isn\'t it true that the only evidence you presented was your own written statement?', 'purpose': 'Lock into uncorroborated claim'},
            {'q': 'And based solely on that statement, a PPO was issued that prevented Mr. Pigors from seeing his daughter?', 'purpose': 'Show disproportionate consequence'},
        ],
    },
    {
        'witness': 'Emily A. Watson',
        'topic': 'Denial of Parenting Time',
        'objective': 'Document systematic interference with parent-child relationship',
        'questions': [
            {'q': 'Ms. Watson, are you aware that the court ordered parenting time for Mr. Pigors?', 'purpose': 'Establish obligation'},
            {'q': 'On how many occasions has Mr. Pigors had parenting time with L.D.W. in the last 12 months?', 'purpose': 'Establish deprivation'},
            {'q': 'Isn\'t it true that Mr. Pigors has attempted to contact you about parenting time on numerous occasions?', 'purpose': 'Show Andrew\'s effort'},
            {'q': 'And you did not respond to those attempts, correct?', 'purpose': 'Lock into non-response'},
            {'q': 'Are you familiar with Factor I of the Best Interest of the Child — the willingness to facilitate a close relationship with the other parent?', 'purpose': 'Frame legal standard'},
            {'q': 'Would you say your actions have facilitated Mr. Pigors\' relationship with L.D.W.?', 'purpose': 'Force admission or look unreasonable'},
        ],
    },
    {
        'witness': 'Emily A. Watson',
        'topic': 'Communication Interference',
        'objective': 'Show pattern of blocking father-child communication',
        'questions': [
            {'q': 'Ms. Watson, does L.D.W. have a phone or device on which she can receive calls?', 'purpose': 'Establish method exists'},
            {'q': 'Has Mr. Pigors attempted to call or video chat with L.D.W.?', 'purpose': 'Establish attempts'},
            {'q': 'Were those calls answered?', 'purpose': 'Establish blocking'},
            {'q': 'Did you receive birthday or holiday messages from Mr. Pigors intended for L.D.W.?', 'purpose': 'Establish withholding'},
            {'q': 'Were those messages delivered to L.D.W.?', 'purpose': 'Force admission of withholding'},
            {'q': 'Are you aware that interfering with a parent-child relationship can constitute a change in circumstances under Michigan law?', 'purpose': 'Legal consequence'},
        ],
    },
    {
        'witness': 'Ronald T. Berry',
        'topic': 'Relationship and Influence',
        'objective': 'Establish bias and potential interference',
        'questions': [
            {'q': 'Mr. Berry, what is your relationship with Emily Watson?', 'purpose': 'Establish romantic interest'},
            {'q': 'Do you live with Ms. Watson and L.D.W.?', 'purpose': 'Establish household role'},
            {'q': 'Have you been present when Mr. Pigors attempted to contact L.D.W.?', 'purpose': 'Potential interference'},
            {'q': 'Have you ever answered calls from Mr. Pigors on behalf of Ms. Watson?', 'purpose': 'Direct involvement'},
            {'q': 'Do you have any professional training in child psychology or family law?', 'purpose': 'No credentials'},
            {'q': 'Would you agree you have a personal interest in the outcome of this custody case?', 'purpose': 'Establish bias'},
        ],
    },
]

def main():
    print("=" * 70)
    print("CROSS-EXAMINATION SCRIPTS — Tool #145")
    print("=" * 70)
    
    total_questions = sum(len(s['questions']) for s in CROSS_SCRIPTS)
    
    lines = [
        "# ⚔️ CROSS-EXAMINATION SCRIPTS",
        f"*Generated: {datetime.now().strftime('%Y-%m-%d %H:%M')} | Tool #145*",
        f"*{len(CROSS_SCRIPTS)} scripts · {total_questions} questions · Practice until automatic*\n",
        "---\n",
        "## RULES OF CROSS-EXAMINATION\n",
        "1. **Ask only leading questions** — questions that suggest the answer",
        "2. **One fact per question** — keep it simple",
        "3. **Never ask a question you don't know the answer to**",
        "4. **Control the witness** — don't let them explain",
        "5. **If they dodge, repeat the exact question** — \"I'll ask again...\"",
        "6. **End on your strongest point** — primacy/recency effect\n",
        "---\n",
    ]
    
    for script in CROSS_SCRIPTS:
        lines.append(f"## CROSS: {script['witness']} — {script['topic']}")
        lines.append(f"**Objective:** {script['objective']}\n")
        
        for i, qa in enumerate(script['questions'], 1):
            lines.append(f"**Q{i}.** {qa['q']}")
            lines.append(f"  *[Purpose: {qa['purpose']}]*\n")
        
        lines.append("---\n")
        print(f"  ⚔️ {script['witness'][:20]} — {script['topic']}: {len(script['questions'])} questions")
    
    lines.extend([
        "## POST-CROSS NOTES\n",
        "- **If Emily cries**: Pause respectfully. Say: \"Your Honor, I'll give the witness a moment.\" (Shows the judge YOU are the reasonable one.)",
        "- **If she refuses to answer**: \"Your Honor, I'd ask the court to direct the witness to answer.\"",
        "- **If opposing objects**: Wait for the judge to rule. If sustained, rephrase. If overruled, proceed.",
        "- **If you get a good admission**: STOP. Move to the next topic. Don't give them a chance to walk it back.\n",
        
        f"*{len(CROSS_SCRIPTS)} scripts · {total_questions} questions · PRACTICE OUT LOUD*",
    ])
    
    md_path = REPORTS_DIR / "CROSS_EXAM_SCRIPTS.md"
    md_path.write_text('\n'.join(lines), encoding='utf-8')
    
    json_path = REPORTS_DIR / "cross_exam_scripts.json"
    json_path.write_text(json.dumps({
        'generated': datetime.now().isoformat(),
        'tool': 'Cross-Examination Scripts (#145)',
        'scripts': len(CROSS_SCRIPTS),
        'total_questions': total_questions,
    }, indent=2), encoding='utf-8')
    
    print(f"\n✅ {len(CROSS_SCRIPTS)} cross-exam scripts with {total_questions} questions")
    print(f"   Reports: CROSS_EXAM_SCRIPTS.md + cross_exam_scripts.json")

if __name__ == '__main__':
    main()
