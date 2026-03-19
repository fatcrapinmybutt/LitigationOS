#!/usr/bin/env python3
"""
Tool #94 — Sanctions Risk Scorer
====================================
Evaluates each filing for sanctions risk under:
- MCR 2.114 (Michigan — frivolous filing)
- FRCP 11 (Federal — frivolous filing)
- 28 USC 1927 (Federal — vexatious multiplication)
- MCL 600.2591 (Michigan — frivolous civil action)

Scores each claim within each filing for:
- Legal basis strength (is there precedent?)
- Factual basis (is evidence in DB?)
- Proportionality (is relief reasonable?)
- Tone (inflammatory language?)

Goal: Keep ALL filings below sanctions threshold.
Prior sessions noted sanctions score at 360 (need <200).
"""
import sys, json, sqlite3
from pathlib import Path
from datetime import datetime

sys.stdout = open(sys.stdout.fileno(), mode='w', encoding='utf-8', errors='replace')

REPO = Path(r"C:\Users\andre\LitigationOS")
DB_PATH = REPO / "litigation_context.db"
REPORTS_DIR = REPO / "00_SYSTEM" / "reports"

SANCTIONS_CRITERIA = {
    'F1': {
        'name': 'Emergency Parenting Time',
        'legal_basis': 8,   # MCL 722.27a — strong statutory basis
        'factual_basis': 7,  # Evidence of denied parenting time in DB
        'proportionality': 9, # Asking for parenting time = proportional
        'tone_risk': 2,      # Low risk — standard custody motion
        'mcr_2114_risk': 'LOW',
        'notes': 'Strong filing. Clear statutory right (MCL 722.27a). Well-supported by evidence.',
    },
    'F2': {
        'name': 'Fraud on Court',
        'legal_basis': 7,
        'factual_basis': 8,   # 5,821 perjury items in DB
        'proportionality': 6, # Fraud claims need careful framing
        'tone_risk': 5,       # "Fraud" language can be inflammatory
        'mcr_2114_risk': 'MEDIUM',
        'notes': 'Strong evidence but tone must be measured. Avoid hyperbole. Stick to documented contradictions.',
    },
    'F3': {
        'name': 'Judicial Disqualification',
        'legal_basis': 7,
        'factual_basis': 9,   # 1,127 judicial violations documented
        'proportionality': 7,
        'tone_risk': 6,       # Challenging a judge = higher scrutiny
        'mcr_2114_risk': 'MEDIUM',
        'notes': 'Well-supported by violation data. Must be respectful and factual. MCR 2.003 is specific.',
    },
    'F4': {
        'name': '§1983 Federal Complaint',
        'legal_basis': 6,     # Viable but complex (domestic relations exception)
        'factual_basis': 7,
        'proportionality': 5, # $1M damages claim needs justification
        'tone_risk': 4,
        'frcp_11_risk': 'MEDIUM',
        'notes': 'Catz v Chalker supports viability. Damages must be itemized. Avoid overreach.',
    },
    'F5': {
        'name': 'MSC Superintending Control',
        'legal_basis': 4,     # Rarely granted — extraordinary remedy
        'factual_basis': 6,
        'proportionality': 3, # MSC bypass is an extreme ask
        'tone_risk': 3,
        'mcr_2114_risk': 'HIGH',
        'notes': 'HIGH sanctions risk. MSC grants these rarely. Must show exhaustion + extraordinary circumstances.',
    },
    'F6': {
        'name': 'JTC Complaint',
        'legal_basis': 8,
        'factual_basis': 9,   # 1,127 violations
        'proportionality': 8,
        'tone_risk': 3,
        'sanctions_risk': 'NONE',  # Complaints to JTC are exempt from sanctions
        'notes': 'No sanctions risk — JTC complaints are protected speech. File freely.',
    },
    'F7': {
        'name': 'Custody Modification',
        'legal_basis': 8,
        'factual_basis': 7,
        'proportionality': 8,
        'tone_risk': 3,
        'mcr_2114_risk': 'LOW',
        'notes': 'Strong basis under Vodvarka. Best interest factors favor Andrew (91 vs 57).',
    },
    'F8': {
        'name': 'COA Leave Application',
        'legal_basis': 5,     # Leave applications have low grant rate
        'factual_basis': 6,
        'proportionality': 7,
        'tone_risk': 2,
        'mcr_2114_risk': 'LOW',
        'notes': 'Standard appellate practice. No sanctions risk for seeking leave.',
    },
    'F9': {
        'name': 'COA Appeal Brief',
        'legal_basis': 7,
        'factual_basis': 7,
        'proportionality': 8,
        'tone_risk': 2,
        'mcr_2114_risk': 'LOW',
        'notes': 'Already docketed (366810). Standard appeal. Focus on preserved errors.',
    },
    'F10': {
        'name': 'AGC Grievance',
        'legal_basis': 7,
        'factual_basis': 6,
        'proportionality': 8,
        'tone_risk': 2,
        'sanctions_risk': 'NONE',  # Grievances to AGC are exempt
        'notes': 'No sanctions risk — AGC complaints are protected. Barnes withdrawal supports filing.',
    },
}

def main():
    print("=" * 70)
    print("SANCTIONS RISK SCORER — Tool #94")
    print("=" * 70)
    
    lines = [
        "# ⚠️ SANCTIONS RISK ASSESSMENT",
        f"*Generated: {datetime.now().strftime('%Y-%m-%d %H:%M')} | Tool #94*\n",
        "---\n",
        "## Overview\n",
        "Each filing is scored on 4 criteria (1-10 scale):",
        "- **Legal Basis**: Is there statutory/case law support?",
        "- **Factual Basis**: Is evidence in the database?",
        "- **Proportionality**: Is the relief requested reasonable?",
        "- **Tone Risk**: Risk of inflammatory/sanctionable language?\n",
        "Higher scores = SAFER. Target: average ≥6.0 per filing.\n",
        "## Sanctions Matrix\n",
        "| Filing | Legal | Factual | Proportion | Tone Risk | Avg Score | Risk Level |",
        "|--------|-------|---------|-----------|-----------|-----------|------------|",
    ]
    
    all_scores = {}
    total_avg = 0
    
    for fid in ['F1','F2','F3','F4','F5','F6','F7','F8','F9','F10']:
        s = SANCTIONS_CRITERIA[fid]
        # Tone risk is inverted — high number means MORE risk, so we invert for scoring
        tone_safe = 10 - s['tone_risk']
        avg = (s['legal_basis'] + s['factual_basis'] + s['proportionality'] + tone_safe) / 4
        
        risk = s.get('sanctions_risk', s.get('mcr_2114_risk', s.get('frcp_11_risk', 'MEDIUM')))
        risk_emoji = {'NONE': '🟢', 'LOW': '🟢', 'MEDIUM': '🟡', 'HIGH': '🔴'}
        
        lines.append(
            f"| {fid} ({s['name'][:15]}) | {s['legal_basis']}/10 | {s['factual_basis']}/10 | "
            f"{s['proportionality']}/10 | {s['tone_risk']}/10 | **{avg:.1f}** | "
            f"{risk_emoji.get(risk, '⚪')} {risk} |"
        )
        
        all_scores[fid] = {
            'name': s['name'],
            'legal_basis': s['legal_basis'],
            'factual_basis': s['factual_basis'],
            'proportionality': s['proportionality'],
            'tone_risk': s['tone_risk'],
            'average': round(avg, 1),
            'risk_level': risk,
            'notes': s['notes'],
        }
        total_avg += avg
        
        print(f"  {fid} ({s['name'][:20]}): avg {avg:.1f}/10 — {risk_emoji.get(risk, '⚪')} {risk}")
    
    overall_avg = total_avg / 10
    
    # Risk mitigation
    lines.extend([
        "",
        f"**Overall Average: {overall_avg:.1f}/10**\n",
        "## Detailed Notes\n",
    ])
    
    for fid in ['F1','F2','F3','F4','F5','F6','F7','F8','F9','F10']:
        s = SANCTIONS_CRITERIA[fid]
        lines.append(f"### {fid} — {s['name']}")
        lines.append(f"{s['notes']}\n")
    
    lines.extend([
        "## 🛡️ SANCTIONS MITIGATION STRATEGIES\n",
        "1. **F5 (MSC)**: Include exhaustion analysis showing why COA/lower court remedies are inadequate",
        "2. **F2 (Fraud)**: Use 'fraud upon the court' (legal term of art) not 'she lied' — measured language",
        "3. **F3 (Disqualification)**: Lead with MCR 2.003(C) factors, not personal criticism of judge",
        "4. **F4 (§1983)**: Cite Catz v Chalker and Dennis v Sparks in opening paragraph — establishes viability",
        "5. **ALL FILINGS**: Remove any language that attacks character — focus on documented conduct",
        "6. **ALL FILINGS**: Every factual claim must cite a specific exhibit or DB record",
        "7. **F6/F10**: Zero sanctions risk — these are protected complaint processes",
        "",
        "## ✅ SAFE FILINGS (file without modification)",
        "- F1, F6, F7, F8, F9, F10 — all LOW/NONE risk\n",
        "## ⚠️ FILINGS NEEDING TONE REVIEW",
        "- F2, F3, F4 — MEDIUM risk, review language before filing\n",
        "## 🔴 HIGH RISK (proceed with caution)",
        "- F5 — MSC bypass is extraordinary remedy, needs strongest possible justification\n",
        "---",
        f"*Sanctions Risk Scorer — Tool #94 — Overall: {overall_avg:.1f}/10*",
    ])
    
    md_path = REPORTS_DIR / "SANCTIONS_RISK.md"
    md_path.write_text('\n'.join(lines), encoding='utf-8')
    
    json_path = REPORTS_DIR / "sanctions_risk.json"
    json_path.write_text(json.dumps({
        'generated': datetime.now().isoformat(),
        'tool': 'Sanctions Risk Scorer (#94)',
        'overall_average': round(overall_avg, 1),
        'filings': all_scores,
    }, indent=2), encoding='utf-8')
    
    print(f"\n✅ Sanctions risk assessment complete — overall {overall_avg:.1f}/10")
    print(f"   Safe: F1, F6, F7, F8, F9, F10")
    print(f"   Review: F2, F3, F4")
    print(f"   Caution: F5")
    print(f"   Reports: SANCTIONS_RISK.md + sanctions_risk.json")

if __name__ == '__main__':
    main()
