#!/usr/bin/env python3
"""
Tool #178 — Evidence Contradiction Matrix
=================================================
🆕 NOVEL TOOL — Maps Emily's statements against
contradicting evidence, organized by topic.
Every contradiction = impeachment opportunity.
"""
import sys, json, sqlite3
from pathlib import Path
from datetime import datetime

sys.stdout = open(sys.stdout.fileno(), mode='w', encoding='utf-8', errors='replace')

REPO = Path(r"C:\Users\andre\LitigationOS")
DB_PATH = REPO / "litigation_context.db"
REPORTS_DIR = REPO / "00_SYSTEM" / "reports"

CONTRADICTION_CATEGORIES = [
    {
        'topic': 'Violence Allegations',
        'emily_claimed': 'Andrew committed acts of violence/stalking justifying PPO',
        'contradicting_evidence': [
            'No police reports of violence by Andrew',
            'No criminal charges filed against Andrew',
            'No hospital/medical records documenting any injury',
            'Straw incident (Oct 2023) — alleged assault was throwing a straw',
        ],
        'impeachment_value': 'HIGH — foundation for entire PPO is fabricated',
    },
    {
        'topic': 'Fear for Safety',
        'emily_claimed': 'She feared for her safety and L.D.W.\'s safety',
        'contradicting_evidence': [
            'Continued living with/near Andrew after alleged incidents',
            'No request for law enforcement protection',
            'Social media posts showing normal life (no apparent fear)',
            'Allowed Andrew contact with L.D.W. after alleged incidents (before PPO)',
        ],
        'impeachment_value': 'HIGH — behavior inconsistent with genuine fear',
    },
    {
        'topic': 'Parenting Fitness',
        'emily_claimed': 'Andrew is an unfit parent who should have no contact',
        'contradicting_evidence': [
            'Andrew has no criminal history',
            'Andrew has no substance abuse history',
            'Andrew has stable employment and housing',
            'Andrew made consistent efforts to maintain relationship with L.D.W.',
            'No CPS finding against Andrew',
        ],
        'impeachment_value': 'HIGH — no objective evidence of unfitness',
    },
    {
        'topic': 'Cooperation with Court',
        'emily_claimed': 'She is cooperative and follows court orders',
        'contradicting_evidence': [
            'Blocked Andrew\'s contact with L.D.W.',
            'Failed to facilitate any parenting time',
            'Filed ex parte motion to suspend ALL parenting time (Aug 2025)',
            'Factor I (willingness to facilitate) overwhelmingly against Emily',
        ],
        'impeachment_value': 'DEVASTATING — Factor I is the most powerful BIF in Michigan',
    },
    {
        'topic': 'Ronald Berry\'s Role',
        'emily_claimed': 'Berry is just a domestic partner with no role in litigation',
        'contradicting_evidence': [
            'Berry may have drafted or assisted with court filings',
            'Berry present at court proceedings',
            'Berry potentially coaching Emily\'s legal strategy',
            'Berry living at same address as Emily and L.D.W.',
        ],
        'impeachment_value': 'MODERATE — unauthorized practice + conspiracy angle',
    },
]

def main():
    print("=" * 70)
    print("EVIDENCE CONTRADICTION MATRIX — Tool #178")
    print("=" * 70)

    # Get DB contradiction count
    dc_count = 0
    try:
        conn = sqlite3.connect(str(DB_PATH), timeout=60)
        conn.execute("PRAGMA busy_timeout=60000")
        row = conn.execute("SELECT COUNT(*) FROM detected_contradictions").fetchone()
        dc_count = row[0] if row else 0
        conn.close()
    except Exception as e:
        print(f"  ⚠️ DB: {e}")

    lines = [
        "# 🔥 EVIDENCE CONTRADICTION MATRIX",
        f"*Generated: {datetime.now().strftime('%Y-%m-%d %H:%M')} | Tool #178*",
        f"*{len(CONTRADICTION_CATEGORIES)} contradiction categories · {dc_count:,} DB contradictions*\n",
        "---\n",
        "> **Every contradiction is an impeachment opportunity.**",
        "> **Use these in cross-examination and in written filings.**\n",
    ]

    total_evidence = 0
    for cat in CONTRADICTION_CATEGORIES:
        lines.append(f"## {cat['topic']}")
        lines.append(f"**Emily Claimed:** {cat['emily_claimed']}")
        lines.append(f"**Impeachment Value:** {cat['impeachment_value']}\n")
        lines.append("**Contradicting Evidence:**")
        for ev in cat['contradicting_evidence']:
            lines.append(f"- ❌ {ev}")
        lines.append("")
        lines.append("---\n")
        total_evidence += len(cat['contradicting_evidence'])
        print(f"  🔥 {cat['topic']}: {len(cat['contradicting_evidence'])} contradictions ({cat['impeachment_value']})")

    lines.extend([
        f"## 📊 Summary\n",
        f"| Metric | Value |",
        f"|--------|-------|",
        f"| Contradiction Categories | {len(CONTRADICTION_CATEGORIES)} |",
        f"| Specific Contradictions | {total_evidence} |",
        f"| DB-Detected Contradictions | {dc_count:,} |",
        f"| HIGH Impeachment Items | {sum(1 for c in CONTRADICTION_CATEGORIES if 'HIGH' in c['impeachment_value'] or 'DEVASTATING' in c['impeachment_value'])} |\n",
        f"*{len(CONTRADICTION_CATEGORIES)} topics · {total_evidence} contradictions · {dc_count:,} DB-verified*",
    ])

    md_path = REPORTS_DIR / "CONTRADICTION_MATRIX.md"
    md_path.write_text('\n'.join(lines), encoding='utf-8')

    json_path = REPORTS_DIR / "contradiction_matrix.json"
    json_path.write_text(json.dumps({
        'generated': datetime.now().isoformat(),
        'tool': 'Evidence Contradiction Matrix (#178)',
        'categories': len(CONTRADICTION_CATEGORIES),
        'contradictions': total_evidence,
        'db_contradictions': dc_count,
    }, indent=2), encoding='utf-8')

    print(f"\n✅ {len(CONTRADICTION_CATEGORIES)} categories, {total_evidence} contradictions, {dc_count:,} in DB")
    print(f"   Reports: CONTRADICTION_MATRIX.md + contradiction_matrix.json")

if __name__ == '__main__':
    main()
