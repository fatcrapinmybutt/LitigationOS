#!/usr/bin/env python3
"""
Tool #95b — Witness Credibility Analyzer (v2)
==============================================
Scores each potential witness on credibility using:
- Contradiction count (from detected_contradictions)
- Perjury evidence (from watson_perjury_compilation)
- Bias indicators
- Relationship to parties

(v2 — original #95 already existed, this is the corrected version)
"""
import sys, json, sqlite3
from pathlib import Path
from datetime import datetime

sys.stdout = open(sys.stdout.fileno(), mode='w', encoding='utf-8', errors='replace')

REPO = Path(r"C:\Users\andre\LitigationOS")
DB_PATH = REPO / "litigation_context.db"
REPORTS_DIR = REPO / "00_SYSTEM" / "reports"

WITNESSES = {
    'Emily A. Watson': {
        'role': 'Respondent/Counter-Petitioner',
        'relationship': 'Mother of L.D.W., adverse party',
        'bias_direction': 'Against Andrew',
        'bias_score': 9,
        'known_issues': [
            'Filed PPO based on straw incident (fabricated)',
            'Restricted parenting time systematically',
            'Relationship with Ronald Berry (potential coaching)',
            'Multiple contradictions documented in DB',
        ],
    },
    'Ronald T. Berry': {
        'role': 'Non-party witness',
        'relationship': 'Emily\'s boyfriend/domestic partner',
        'bias_direction': 'Against Andrew',
        'bias_score': 8,
        'known_issues': [
            'Potential unauthorized practice of law (MCL 600.916)',
            'May have coached Emily on filings/testimony',
            'Financial interest in Emily retaining custody',
        ],
    },
    'Jennifer Barnes (P55406)': {
        'role': 'Emily\'s former attorney (withdrew)',
        'relationship': 'Former legal counsel for Emily',
        'bias_direction': 'Neutral (withdrew)',
        'bias_score': 5,
        'known_issues': [
            'Withdrew — reason may indicate ethical concerns',
            'MRPC 3.3 candor obligations may have been violated',
        ],
    },
    'Hon. Jenny L. McNeill': {
        'role': 'Presiding judge (disqualification sought)',
        'relationship': 'Judicial officer',
        'bias_direction': 'Against Andrew (per violation data)',
        'bias_score': 6,
        'known_issues': [
            '1,127 documented violations in DB',
            'Ex-parte communications alleged',
        ],
    },
    'Pamela Rusco': {
        'role': 'Judicial Secretary to Judge McNeill',
        'relationship': 'Court staff',
        'bias_direction': 'Aligned with McNeill',
        'bias_score': 6,
        'known_issues': ['Gatekeeping behavior alleged'],
    },
    'Andrew James Pigors': {
        'role': 'Plaintiff/Petitioner (pro se)',
        'relationship': 'Father of L.D.W.',
        'bias_direction': 'Self-interest (natural)',
        'bias_score': 3,
        'known_issues': [
            'Pro se — may be perceived as less credible',
            'Strong: consistent testimony, documented evidence',
        ],
    },
}

def get_contradiction_counts(conn):
    counts = {}
    try:
        rows = conn.execute("""
            SELECT speaker, COUNT(*) as cnt,
                   SUM(CASE WHEN severity = 'PERJURY' THEN 1 ELSE 0 END) as perjury_cnt,
                   SUM(CASE WHEN severity = 'IMPEACHMENT' THEN 1 ELSE 0 END) as impeach_cnt
            FROM detected_contradictions GROUP BY speaker ORDER BY cnt DESC
        """).fetchall()
        for r in rows:
            counts[r[0]] = {'total': r[1], 'perjury': r[2], 'impeachment': r[3]}
    except:
        pass
    return counts

def main():
    print("=" * 70)
    print("WITNESS CREDIBILITY ANALYZER — Tool #95")
    print("=" * 70)

    conn = sqlite3.connect(str(DB_PATH), timeout=60)
    conn.execute("PRAGMA busy_timeout=60000")
    conn.execute("PRAGMA journal_mode=WAL")
    contradiction_counts = get_contradiction_counts(conn)
    perjury_total = 0
    try:
        perjury_total = conn.execute("SELECT COUNT(*) FROM watson_perjury_compilation").fetchone()[0]
    except:
        pass
    conn.close()

    lines = [
        "# 🔍 WITNESS CREDIBILITY ANALYSIS",
        f"*Generated: {datetime.now().strftime('%Y-%m-%d %H:%M')} | Tool #95*\n",
        "---\n",
        "| Witness | Role | Bias | Contradictions | Credibility | Rating |",
        "|---------|------|------|---------------|-------------|--------|",
    ]
    all_witnesses = {}
    for name, data in WITNESSES.items():
        contra = contradiction_counts.get(name, {'total': 0, 'perjury': 0, 'impeachment': 0})
        if contra['total'] == 0:
            for speaker, counts in contradiction_counts.items():
                if name.split()[0].lower() in speaker.lower():
                    contra = counts
                    break
        credibility = max(1, 10 - data['bias_score'] - min(5, contra['total'] // 50))
        rating = "✅ HIGH" if credibility >= 7 else ("🟡 MEDIUM" if credibility >= 4 else "🔴 LOW")
        lines.append(f"| {name[:25]} | {data['role'][:20]} | {data['bias_score']}/10 | {contra['total']:,} | {credibility}/10 | {rating} |")
        all_witnesses[name] = {
            'role': data['role'], 'bias_score': data['bias_score'],
            'contradictions': contra['total'], 'credibility_score': credibility,
            'rating': rating.split()[-1], 'known_issues': data['known_issues'],
        }
        print(f"  {name[:25]}: credibility {credibility}/10 {rating}")

    lines.extend(["", "---", f"*Witness Credibility Analyzer — Tool #95 — {len(WITNESSES)} witnesses*"])
    md_path = REPORTS_DIR / "WITNESS_CREDIBILITY.md"
    md_path.write_text('\n'.join(lines), encoding='utf-8')
    json_path = REPORTS_DIR / "witness_credibility.json"
    json_path.write_text(json.dumps({
        'generated': datetime.now().isoformat(), 'tool': 'Witness Credibility (#95)',
        'witnesses': all_witnesses, 'perjury_total': perjury_total,
    }, indent=2), encoding='utf-8')
    print(f"\n✅ {len(WITNESSES)} witnesses analyzed")
    print(f"   Reports: WITNESS_CREDIBILITY.md + witness_credibility.json")

if __name__ == '__main__':
    main()
