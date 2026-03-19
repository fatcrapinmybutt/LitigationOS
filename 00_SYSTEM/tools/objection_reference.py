#!/usr/bin/env python3
"""
Tool #102 — Objection Quick-Reference Engine
================================================
🆕 NOVEL TOOL — Courtroom survival guide

Generates a pocket-sized objection reference for pro se use:
- Common objections with exact phrasing
- When to use each objection
- Michigan Rules of Evidence (MRE) citations
- Response to opposing objections
- Emergency phrases for when you're caught off guard

Designed to be printed and carried to EVERY hearing.
"""
import sys, json
from pathlib import Path
from datetime import datetime

sys.stdout = open(sys.stdout.fileno(), mode='w', encoding='utf-8', errors='replace')

REPO = Path(r"C:\Users\andre\LitigationOS")
REPORTS_DIR = REPO / "00_SYSTEM" / "reports"
PKG_BASE = Path(r"C:\Users\andre\Desktop\LITIGATION_FILING_PACKAGE")

OBJECTIONS = [
    {
        'objection': 'HEARSAY',
        'phrase': '"Objection, Your Honor. Hearsay."',
        'rule': 'MRE 801-807',
        'when': 'Witness testifies about what someone ELSE said, offered for truth',
        'exceptions': 'Excited utterance (803(2)), business records (803(6)), party admission (801(d)(2))',
        'response_if_raised': '"Your Honor, this falls under the [exception] exception to hearsay under MRE [rule]."',
    },
    {
        'objection': 'RELEVANCE',
        'phrase': '"Objection. Irrelevant. This has no bearing on the matter before the court."',
        'rule': 'MRE 401-403',
        'when': 'Evidence doesn\'t relate to any issue in the case',
        'response_if_raised': '"Your Honor, this is directly relevant to [specific issue] because [reason]."',
    },
    {
        'objection': 'LEADING',
        'phrase': '"Objection. Leading the witness."',
        'rule': 'MRE 611(c)',
        'when': 'Attorney suggests the answer in the question during direct examination',
        'note': 'Leading IS allowed on cross-examination',
        'response_if_raised': '"Your Honor, this is cross-examination. Leading questions are permitted under MRE 611(c)."',
    },
    {
        'objection': 'SPECULATION',
        'phrase': '"Objection. Calls for speculation."',
        'rule': 'MRE 602',
        'when': 'Witness asked to guess or speculate about something they don\'t know',
        'response_if_raised': '"Your Honor, the witness has personal knowledge of this matter as established in their testimony."',
    },
    {
        'objection': 'LACK OF FOUNDATION',
        'phrase': '"Objection. Lack of foundation."',
        'rule': 'MRE 602, 901',
        'when': 'Witness hasn\'t established personal knowledge or document hasn\'t been authenticated',
        'response_if_raised': '"Your Honor, I will lay the foundation. [Ask: Were you present? Did you see/hear this?]"',
    },
    {
        'objection': 'ASKED AND ANSWERED',
        'phrase': '"Objection. Asked and answered."',
        'rule': 'MRE 611(a)',
        'when': 'Same question has already been asked and answered — opposing counsel is badgering',
        'response_if_raised': '"Your Honor, I\'m asking from a different angle to clarify [specific point]."',
    },
    {
        'objection': 'ASSUMES FACTS NOT IN EVIDENCE',
        'phrase': '"Objection. Assumes facts not in evidence."',
        'rule': 'MRE 611(a)',
        'when': 'Question contains a factual assertion that hasn\'t been established',
        'response_if_raised': '"Your Honor, I will establish this fact through testimony/exhibits."',
    },
    {
        'objection': 'BEST EVIDENCE RULE',
        'phrase': '"Objection. Best evidence rule. The original document should be produced."',
        'rule': 'MRE 1002',
        'when': 'Party tries to prove content of a writing without producing the original',
        'response_if_raised': '"Your Honor, the original is [unavailable/in possession of opposing party]. MRE 1004 permits secondary evidence."',
    },
    {
        'objection': 'UNFAIRLY PREJUDICIAL',
        'phrase': '"Objection. The probative value is substantially outweighed by the danger of unfair prejudice."',
        'rule': 'MRE 403',
        'when': 'Evidence may technically be relevant but would inflame or mislead',
        'response_if_raised': '"Your Honor, this evidence is highly probative of [issue] and any prejudice is not unfair — it reflects the truth."',
    },
    {
        'objection': 'IMPROPER CHARACTER EVIDENCE',
        'phrase': '"Objection. Improper character evidence."',
        'rule': 'MRE 404',
        'when': 'Evidence of character offered to prove action in conformity — not allowed except specific exceptions',
        'response_if_raised': '"Your Honor, this is not character evidence — it\'s evidence of [habit/plan/knowledge] under MRE 404(b)."',
    },
    {
        'objection': 'PRIVILEGED',
        'phrase': '"Objection. That communication is privileged."',
        'rule': 'MRE 501',
        'when': 'Question asks about attorney-client, spousal, or other privileged communication',
        'response_if_raised': '"Your Honor, the privilege was waived when [party disclosed to third party / crime-fraud exception applies]."',
    },
    {
        'objection': 'BEYOND THE SCOPE',
        'phrase': '"Objection. Beyond the scope of direct examination."',
        'rule': 'MRE 611(b)',
        'when': 'Cross-examination goes beyond topics covered on direct',
        'response_if_raised': '"Your Honor, this is within the scope of direct examination regarding [topic covered]."',
    },
]

EMERGENCY_PHRASES = [
    '"Your Honor, I need a moment to gather my thoughts."',
    '"Your Honor, I object and request a brief recess to research the applicable rule."',
    '"Your Honor, I\'m a pro se litigant. I respectfully request the court\'s guidance on proper procedure."',
    '"Your Honor, for the record, I object to this entire line of questioning."',
    '"Your Honor, I would like to make an offer of proof outside the presence of [the jury/opposing party]."',
    '"Your Honor, I request that the court note my continuing objection to this evidence."',
    '"Your Honor, I move to strike that testimony as non-responsive."',
]

def main():
    print("=" * 70)
    print("OBJECTION QUICK-REFERENCE — Tool #102")
    print("=" * 70)
    
    lines = [
        "# ⚡ OBJECTION QUICK-REFERENCE CARD",
        f"*Generated: {datetime.now().strftime('%Y-%m-%d %H:%M')} | Tool #102*",
        "*PRINT THIS AND CARRY TO EVERY HEARING*\n",
        "---\n",
    ]
    
    for obj in OBJECTIONS:
        lines.extend([
            f"## {obj['objection']}",
            f"**Say:** {obj['phrase']}",
            f"**Rule:** {obj['rule']}",
            f"**When:** {obj['when']}",
        ])
        if 'exceptions' in obj:
            lines.append(f"**Exceptions:** {obj['exceptions']}")
        if 'note' in obj:
            lines.append(f"**Note:** {obj['note']}")
        lines.append(f"**If raised against you:** {obj['response_if_raised']}\n")
    
    lines.extend([
        "---",
        "## 🆘 EMERGENCY PHRASES\n",
        "*When you\'re caught off guard, say one of these:*\n",
    ])
    for i, phrase in enumerate(EMERGENCY_PHRASES, 1):
        lines.append(f"{i}. {phrase}")
    
    lines.extend([
        "",
        "## 📋 COURTROOM PROTOCOL REMINDERS\n",
        "- Always stand when speaking to the judge",
        "- Address the judge as \"Your Honor\" — never by name",
        "- Wait for the judge to finish speaking before responding",
        "- Never argue with the judge — object, state your reason, then accept the ruling",
        "- If ruling is wrong, say: \"Your Honor, I respectfully disagree and wish to preserve this issue for appeal.\"",
        "- Keep your voice calm and level — emotion hurts credibility",
        "- Never speak directly to opposing counsel — all communication through the judge",
        "",
        f"*Objection Quick-Reference — Tool #102 — {len(OBJECTIONS)} objections, {len(EMERGENCY_PHRASES)} emergency phrases*",
    ])
    
    md_path = REPORTS_DIR / "OBJECTION_REFERENCE.md"
    md_path.write_text('\n'.join(lines), encoding='utf-8')
    
    # Also save to F1/F3/F7 packages
    for fid in ['F1', 'F3', 'F7']:
        try:
            pkg_path = PKG_BASE / f"PKG_{fid}" / "15_OBJECTION_REFERENCE.md"
            pkg_path.write_text('\n'.join(lines), encoding='utf-8')
        except:
            pass
    
    json_path = REPORTS_DIR / "objection_reference.json"
    json_path.write_text(json.dumps({
        'generated': datetime.now().isoformat(),
        'tool': 'Objection Quick-Reference (#102)',
        'objection_count': len(OBJECTIONS),
        'emergency_phrases': len(EMERGENCY_PHRASES),
        'objections': [{'type': o['objection'], 'rule': o['rule']} for o in OBJECTIONS],
    }, indent=2), encoding='utf-8')
    
    print(f"\n  ⚡ {len(OBJECTIONS)} objections with exact phrasing")
    print(f"  🆘 {len(EMERGENCY_PHRASES)} emergency courtroom phrases")
    print(f"  📄 Saved to reports/ + PKG_F1/F3/F7")
    print(f"\n✅ PRINT THIS AND CARRY TO EVERY HEARING")
    print(f"   Reports: OBJECTION_REFERENCE.md + objection_reference.json")

if __name__ == '__main__':
    main()
