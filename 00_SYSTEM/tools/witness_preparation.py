#!/usr/bin/env python3
"""
Tool #166 — Witness Preparation Guide
=================================================
🆕 NOVEL TOOL — Prepares Andrew for testifying as
a witness (and for direct examination of any
witnesses he may call).
"""
import sys, json
from pathlib import Path
from datetime import datetime

sys.stdout = open(sys.stdout.fileno(), mode='w', encoding='utf-8', errors='replace')

REPO = Path(r"C:\Users\andre\LitigationOS")
REPORTS_DIR = REPO / "00_SYSTEM" / "reports"

WITNESS_PREP = {
    'andrew_testimony': {
        'title': 'Andrew\'s Direct Testimony Preparation',
        'sections': [
            {
                'topic': 'Opening Statement (who you are)',
                'key_points': [
                    'State full name, address, occupation',
                    'Relationship to L.D.W. — her father',
                    'How long you\'ve been involved in her life',
                    'What you\'re asking the court for — parenting time',
                ],
            },
            {
                'topic': 'Relationship with L.D.W.',
                'key_points': [
                    'Describe your bond — specific examples',
                    'Activities you did together before separation',
                    'Attempts to maintain contact since separation',
                    'How the separation has affected you and L.D.W.',
                ],
            },
            {
                'topic': 'Emily\'s Interference',
                'key_points': [
                    'Specific documented instances of blocked contact',
                    'Pattern of escalation — PPO, custody, suspended time',
                    'DO NOT speculate about Emily\'s motives',
                    'Let the EVIDENCE speak — reference exhibits',
                ],
            },
            {
                'topic': 'Fraud/Perjury Allegations',
                'key_points': [
                    'State ONLY what you can prove with documents',
                    'Reference specific exhibit numbers',
                    'Avoid emotional language — stay factual',
                    '"Exhibit [X] shows [statement]. Exhibit [Y] contradicts it because..."',
                ],
            },
            {
                'topic': 'Best Interest Factors',
                'key_points': [
                    'Address each factor methodically',
                    'Factor I is your strongest — emphasize willingness to facilitate',
                    'Acknowledge where Emily has strengths (shows fairness)',
                    'Focus on what\'s best for L.D.W., not what\'s bad about Emily',
                ],
            },
        ],
    },
    'cross_exam_survival': {
        'title': 'Surviving Cross-Examination',
        'rules': [
            'Listen to the ENTIRE question before answering',
            'Answer ONLY the question asked — do not volunteer',
            'If you don\'t understand: "Could you rephrase that?"',
            'If you don\'t remember: "I don\'t recall" (never guess)',
            'If it\'s a yes/no question: answer yes or no, then explain if needed',
            'NEVER argue with the examiner — address the judge',
            'If the question mischaracterizes: "That\'s not accurate because..."',
            'If compound question: "I\'d like to answer that in parts"',
            'TAKE YOUR TIME — there is no penalty for pausing to think',
            'If you feel trapped: "I\'d like to explain my answer, Your Honor"',
        ],
    },
    'objection_triggers': {
        'title': 'When to Object During Their Testimony',
        'triggers': [
            {'trigger': 'Hearsay', 'example': 'Emily says "My friend told me Andrew..."', 'objection': '"Objection, hearsay — MRE 801/802"'},
            {'trigger': 'Speculation', 'example': '"I think Andrew would..." / "He probably..."', 'objection': '"Objection, calls for speculation"'},
            {'trigger': 'Leading', 'example': 'Barnes asks Emily "Isn\'t it true that..."', 'objection': '"Objection, leading — MRE 611(c)"'},
            {'trigger': 'Relevance', 'example': 'Testimony about unrelated topics', 'objection': '"Objection, relevance — MRE 401/402"'},
            {'trigger': 'Character', 'example': '"Andrew is the type of person who..."', 'objection': '"Objection, improper character evidence — MRE 404"'},
            {'trigger': 'Best evidence', 'example': 'Testimony about document contents without showing it', 'objection': '"Objection, best evidence rule — MRE 1002"'},
        ],
    },
}

def main():
    print("=" * 70)
    print("WITNESS PREPARATION GUIDE — Tool #166")
    print("=" * 70)

    lines = [
        "# 🎤 WITNESS PREPARATION GUIDE",
        f"*Generated: {datetime.now().strftime('%Y-%m-%d %H:%M')} | Tool #166*",
        f"*Complete preparation for Andrew\'s testimony + cross-exam survival*\n",
        "---\n",
    ]

    # Andrew's testimony
    testimony = WITNESS_PREP['andrew_testimony']
    lines.append(f"## {testimony['title']}\n")
    total_points = 0
    for section in testimony['sections']:
        lines.append(f"### {section['topic']}\n")
        for pt in section['key_points']:
            lines.append(f"- {pt}")
        lines.append("")
        total_points += len(section['key_points'])
    print(f"  🎤 Testimony: {len(testimony['sections'])} topics, {total_points} key points")

    # Cross-exam survival
    cross = WITNESS_PREP['cross_exam_survival']
    lines.extend(["---\n", f"## {cross['title']}\n"])
    for i, rule in enumerate(cross['rules'], 1):
        lines.append(f"{i}. **{rule}**")
    lines.append("")
    print(f"  🛡️ Cross-exam survival: {len(cross['rules'])} rules")

    # Objection triggers
    obj = WITNESS_PREP['objection_triggers']
    lines.extend(["---\n", f"## {obj['title']}\n",
                   "| Trigger | Example | Objection |",
                   "|---------|---------|-----------|"])
    for t in obj['triggers']:
        lines.append(f"| {t['trigger']} | {t['example'][:50]} | {t['objection']} |")
    lines.append("")
    print(f"  ⚖️ Objection triggers: {len(obj['triggers'])}")

    total = total_points + len(cross['rules']) + len(obj['triggers'])
    lines.append(f"*{total} total preparation items · Practice with a friend before court*")

    md_path = REPORTS_DIR / "WITNESS_PREPARATION.md"
    md_path.write_text('\n'.join(lines), encoding='utf-8')

    json_path = REPORTS_DIR / "witness_preparation.json"
    json_path.write_text(json.dumps({
        'generated': datetime.now().isoformat(),
        'tool': 'Witness Preparation Guide (#166)',
        'testimony_topics': len(testimony['sections']),
        'key_points': total_points,
        'cross_exam_rules': len(cross['rules']),
        'objection_triggers': len(obj['triggers']),
    }, indent=2), encoding='utf-8')

    print(f"\n✅ {total} preparation items across testimony, cross-exam, and objections")
    print(f"   Reports: WITNESS_PREPARATION.md + witness_preparation.json")

if __name__ == '__main__':
    main()
