#!/usr/bin/env python3
"""
Tool #147 — Legal Standard Quick Reference
=================================================
🆕 NOVEL TOOL — One-page cheat sheet for every legal
standard Andrew needs to cite in court.

Organized by topic: burden of proof, BIF factors,
disqualification, contempt, modification, etc.
"""
import sys, json
from pathlib import Path
from datetime import datetime

sys.stdout = open(sys.stdout.fileno(), mode='w', encoding='utf-8', errors='replace')

REPO = Path(r"C:\Users\andre\LitigationOS")
REPORTS_DIR = REPO / "00_SYSTEM" / "reports"

STANDARDS = [
    {
        'topic': 'Disqualification (F3)',
        'standard': 'A reasonable person, knowing all the circumstances, would question the judge\'s impartiality',
        'authority': 'MCR 2.003(C)(1)(b); Armstrong v Ypsilanti Twp, 248 Mich App 573 (2001)',
        'burden': 'Movant (Andrew)',
        'key_point': 'Pattern of conduct establishes objective bias — no need to prove subjective intent',
    },
    {
        'topic': 'Best Interest of the Child (F7)',
        'standard': '12 statutory factors — court must consider and make findings on each',
        'authority': 'MCL 722.23(a)-(l); Vodvarka v Grasmeyer, 259 Mich App 499 (2003)',
        'burden': 'Movant must show proper cause or change of circumstances first',
        'key_point': 'Factor I (willingness to facilitate) is often dispositive in alienation cases',
    },
    {
        'topic': 'Change of Circumstances (F7)',
        'standard': 'Normal life changes OR proper cause (one or more appropriate grounds)',
        'authority': 'MCL 722.27(1)(c); Vodvarka v Grasmeyer, 259 Mich App 499',
        'burden': 'Movant (Andrew)',
        'key_point': 'Multiple changes can aggregate — attorney withdrawal + denied parenting time + new evidence of fraud',
    },
    {
        'topic': 'Contempt of Court (F1/F7)',
        'standard': 'Clear and convincing evidence of willful violation of a court order',
        'authority': 'MCR 3.606; In re Contempt of Dougherty, 429 Mich 81 (1987)',
        'burden': 'Movant (Andrew)',
        'key_point': 'Must prove: (1) a clear order existed, (2) the other party knew about it, (3) they violated it willfully',
    },
    {
        'topic': 'Fraud Upon the Court (F2)',
        'standard': 'Unconscionable plan or scheme designed to influence the court\'s decision',
        'authority': 'MCR 2.612(C)(1)(c)/(3); Phinney v Perlmutter, 222 Mich App 513 (1997)',
        'burden': 'Clear and convincing evidence',
        'key_point': 'NO TIME LIMIT for MCR 2.612(C)(3) — independent action for fraud on court',
    },
    {
        'topic': '§1983 Due Process (F4)',
        'standard': 'Deprivation of a constitutional right under color of state law',
        'authority': '42 USC §1983; Monroe v Pape, 365 US 167 (1961)',
        'burden': 'Preponderance of evidence',
        'key_point': 'Parental rights are fundamental liberty interests — Troxel v Granville, 530 US 57 (2000)',
    },
    {
        'topic': 'Judicial Immunity Exception (F4)',
        'standard': 'Immunity pierced when judge acts in concert with party conspiracy',
        'authority': 'Dennis v Sparks, 449 US 24 (1980)',
        'burden': 'Preponderance showing conspiracy',
        'key_point': 'Co-conspirators (Emily, Berry, Barnes) lose ALL immunity',
    },
    {
        'topic': 'IFP Standard (All courts)',
        'standard': 'Unable to pay fees without substantial hardship',
        'authority': 'MCR 2.002; 28 USC §1915',
        'burden': 'Applicant shows financial inability',
        'key_point': 'One IFP grant covers all filings in that case — file MC 20 with first filing',
    },
    {
        'topic': 'Emergency Ex Parte (F1)',
        'standard': 'Immediate and irreparable injury will result from delay',
        'authority': 'MCR 3.207(B); MCL 722.27a(3)',
        'burden': 'Movant must show emergency + irreparable harm',
        'key_point': 'Must establish specific required findings — general allegations insufficient',
    },
    {
        'topic': 'Superintending Control (F5)',
        'standard': 'Lower court clearly erred + no adequate remedy on appeal',
        'authority': 'Const 1963 Art 6 §4; MCR 7.304',
        'burden': 'Complainant — extraordinary showing required',
        'key_point': 'MSC rarely grants — use only if COA fails',
    },
]

def main():
    print("=" * 70)
    print("LEGAL STANDARD QUICK REFERENCE — Tool #147")
    print("=" * 70)

    lines = [
        "# 📖 LEGAL STANDARD QUICK REFERENCE",
        f"*Generated: {datetime.now().strftime('%Y-%m-%d %H:%M')} | Tool #147*",
        f"*{len(STANDARDS)} standards — cite these in every filing and hearing*\n",
        "---\n",
        "## QUICK REFERENCE TABLE\n",
        "| Topic | Burden | Key Authority |",
        "|-------|--------|--------------|",
    ]

    for s in STANDARDS:
        lines.append(f"| {s['topic']} | {s['burden'][:20]} | {s['authority'][:50]} |")
        print(f"  📖 {s['topic']}: {s['burden']}")

    lines.extend(["", "---\n"])

    for s in STANDARDS:
        lines.append(f"## {s['topic']}")
        lines.append(f"**Standard:** {s['standard']}")
        lines.append(f"**Authority:** {s['authority']}")
        lines.append(f"**Burden:** {s['burden']}")
        lines.append(f"**💡 Key Point:** {s['key_point']}")
        lines.append("\n---\n")

    lines.append(f"*{len(STANDARDS)} standards · PRINT AND BRING TO EVERY HEARING*")

    md_path = REPORTS_DIR / "LEGAL_STANDARDS.md"
    md_path.write_text('\n'.join(lines), encoding='utf-8')

    json_path = REPORTS_DIR / "legal_standards.json"
    json_path.write_text(json.dumps({
        'generated': datetime.now().isoformat(),
        'tool': 'Legal Standard Quick Reference (#147)',
        'standards': len(STANDARDS),
    }, indent=2), encoding='utf-8')

    print(f"\n✅ {len(STANDARDS)} legal standards with authorities and key points")
    print(f"   Reports: LEGAL_STANDARDS.md + legal_standards.json")

if __name__ == '__main__':
    main()
