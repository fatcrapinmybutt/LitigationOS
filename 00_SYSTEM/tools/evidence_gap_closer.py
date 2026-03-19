#!/usr/bin/env python3
"""
Tool #64 — Evidence Gap Closer
==================================
Analyzes each filing's claims against available evidence to find:
1. Claims with strong evidence (ready to file)
2. Claims with weak evidence (need more support)
3. Claims with NO evidence (remove or find evidence)

Uses the DB to cross-reference claims → evidence_quotes → exhibits.
"""
import sys, json, sqlite3
from pathlib import Path
from datetime import datetime

sys.stdout = open(sys.stdout.fileno(), mode='w', encoding='utf-8', errors='replace')

REPO = Path(r"C:\Users\andre\LitigationOS")
DB_PATH = REPO / "litigation_context.db"
REPORTS_DIR = REPO / "00_SYSTEM" / "reports"
PKG_BASE = Path(r"C:\Users\andre\Desktop\LITIGATION_FILING_PACKAGE")

FILING_CLAIMS = {
    'F1': {
        'title': 'Emergency Parenting Time',
        'claims': [
            'Complete denial of parenting time',
            'Child welfare endangered by parental alienation',
            'Emergency circumstances under MCL 722.27a(7)',
            'Best interest factors favor father contact',
        ],
    },
    'F2': {
        'title': 'Fraud Upon the Court',
        'claims': [
            'Perjury in initial PPO application',
            'Fabricated evidence (straw incident)',
            'False allegations of violence/stalking',
            'Conspiracy to deprive parental rights',
        ],
    },
    'F3': {
        'title': 'Judicial Disqualification',
        'claims': [
            'Pattern of bias against father',
            'Ex parte communications',
            'Failure to follow mandatory statutes',
            'Denial of due process rights',
            'Appearance of impropriety',
        ],
    },
    'F4': {
        'title': '42 USC §1983 Civil Rights',
        'claims': [
            'Deprivation of parental liberty interest (14th Amendment)',
            'Denial of due process',
            'Conspiracy with private parties (Dennis v Sparks)',
            'Pattern of constitutional violations',
            'Failure to provide meaningful hearing',
        ],
    },
    'F5': {
        'title': 'MSC Superintending Control',
        'claims': [
            'Lower court exceeded jurisdiction',
            'Systematic denial of statutory rights',
            'Void orders require MSC intervention',
            'Extraordinary circumstances exist',
        ],
    },
    'F6': {
        'title': 'JTC Judicial Misconduct',
        'claims': [
            'Canon 1 — Uphold integrity of judiciary',
            'Canon 2 — Appearance of impropriety',
            'Canon 3(A)(4) — Ex parte communications',
            'Canon 3(B)(5) — Perform duties impartially',
            'Pattern of misconduct over time',
        ],
    },
    'F7': {
        'title': 'Custody Modification',
        'claims': [
            'Proper cause / change of circumstances',
            'Best interest factor analysis (MCL 722.23)',
            'Parental alienation pattern',
            'Willful interference with parenting time',
            'Child needs relationship with both parents',
        ],
    },
    'F8': {
        'title': 'COA Application for Leave',
        'claims': [
            'Trial court abused discretion',
            'Legal errors in custody determination',
            'Denial of due process at trial level',
            'Manifest injustice in outcome',
        ],
    },
    'F9': {
        'title': 'COA Appeal Brief (366810)',
        'claims': [
            'Lower court errors preserved for appeal',
            'Standard of review met (abuse of discretion)',
            'Record supports reversal',
            'Constitutional rights violated below',
        ],
    },
    'F10': {
        'title': 'AGC Attorney Misconduct',
        'claims': [
            'MRPC 3.3 — Failed duty of candor',
            'MRPC 3.4 — Unfairness to opposing party',
            'MRPC 8.4 — Dishonesty/fraud/deceit',
            'Failed to correct known false testimony',
        ],
    },
}

def search_evidence(conn, claim_text):
    """Search for evidence supporting a claim."""
    keywords = [w for w in claim_text.lower().split() if len(w) > 3 and w not in 
                {'with', 'from', 'that', 'this', 'have', 'been', 'were', 'their', 'under', 'against'}]
    
    total = 0
    sources = {}
    
    tables_to_search = [
        ('evidence_quotes', ['quote_text', 'category', 'source_document']),
        ('judicial_violations', []),  # Will auto-detect
        ('watson_perjury_compilation', ['statement_text', 'contradicting_evidence']),
        ('detected_contradictions', ['statement_1', 'statement_2']),
    ]
    
    for table, preferred_cols in tables_to_search:
        try:
            cols = [r[1] for r in conn.execute(f"PRAGMA table_info({table})").fetchall()]
            if not cols:
                continue
            
            search_cols = preferred_cols if preferred_cols else [
                c for c in cols if any(t in c.lower() for t in ['text', 'description', 'finding', 'violation', 'quote', 'statement'])
            ]
            if not search_cols:
                search_cols = [cols[1]] if len(cols) > 1 else []
            
            table_count = 0
            for kw in keywords[:5]:  # Limit to 5 keywords for speed
                for col in search_cols[:2]:  # Limit to 2 columns
                    try:
                        count = conn.execute(
                            f"SELECT COUNT(*) FROM {table} WHERE {col} LIKE ? LIMIT 1000",
                            (f'%{kw}%',)
                        ).fetchone()[0]
                        table_count += min(count, 1000)
                    except:
                        continue
            
            if table_count > 0:
                sources[table] = min(table_count, 5000)  # Cap to avoid overcounting
                total += sources[table]
        except:
            continue
    
    return total, sources

def main():
    print("=" * 70)
    print("EVIDENCE GAP CLOSER — Tool #64")
    print(f"Started: {datetime.now().isoformat()}")
    print("=" * 70)
    
    conn = sqlite3.connect(str(DB_PATH), timeout=30)
    conn.execute("PRAGMA busy_timeout=60000")
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA cache_size=-32000")
    
    results = {}
    
    for fid, fdata in FILING_CLAIMS.items():
        print(f"\n📋 {fid}: {fdata['title']}")
        filing_results = {'title': fdata['title'], 'claims': []}
        
        for claim in fdata['claims']:
            count, sources = search_evidence(conn, claim)
            
            if count >= 100:
                strength = '🟢 STRONG'
            elif count >= 20:
                strength = '🟡 ADEQUATE'
            elif count >= 5:
                strength = '🟠 WEAK'
            else:
                strength = '🔴 GAP'
            
            print(f"   {strength} ({count:,}) {claim[:60]}")
            
            filing_results['claims'].append({
                'claim': claim,
                'evidence_count': count,
                'strength': strength.split()[0],
                'strength_label': strength.split()[1],
                'sources': sources,
            })
        
        results[fid] = filing_results
    
    conn.close()
    
    # Generate report
    lines = [
        "# EVIDENCE GAP ANALYSIS",
        f"*Generated: {datetime.now().strftime('%Y-%m-%d %H:%M')}*\n",
        "## Summary",
        "| Filing | Title | Strong | Adequate | Weak | Gap |",
        "|--------|-------|--------|----------|------|-----|",
    ]
    
    total_strong = total_adequate = total_weak = total_gap = 0
    
    for fid, fdata in results.items():
        strong = sum(1 for c in fdata['claims'] if c['strength'] == '🟢')
        adequate = sum(1 for c in fdata['claims'] if c['strength'] == '🟡')
        weak = sum(1 for c in fdata['claims'] if c['strength'] == '🟠')
        gap = sum(1 for c in fdata['claims'] if c['strength'] == '🔴')
        total_strong += strong
        total_adequate += adequate
        total_weak += weak
        total_gap += gap
        lines.append(f"| {fid} | {fdata['title'][:30]} | {strong} | {adequate} | {weak} | {gap} |")
    
    lines.append(f"| **TOTAL** | | **{total_strong}** | **{total_adequate}** | **{total_weak}** | **{total_gap}** |")
    
    for fid, fdata in results.items():
        lines.extend([
            f"\n## {fid} — {fdata['title']}",
            "| Claim | Strength | Evidence Count | Sources |",
            "|-------|----------|---------------|---------|",
        ])
        for claim in fdata['claims']:
            src_str = ', '.join(f"{k}:{v}" for k, v in claim['sources'].items()) if claim['sources'] else 'None'
            lines.append(f"| {claim['claim'][:50]} | {claim['strength']} {claim['strength_label']} | {claim['evidence_count']:,} | {src_str[:40]} |")
    
    # Recommendations
    lines.extend([
        "\n---",
        "## Gap Remediation Recommendations",
    ])
    
    for fid, fdata in results.items():
        gaps = [c for c in fdata['claims'] if c['strength'] in ['🟠', '🔴']]
        if gaps:
            lines.append(f"\n### {fid} — {fdata['title']}")
            for gap in gaps:
                lines.append(f"- **{gap['strength']} {gap['claim']}** — Need additional evidence. Search drives for documents, request from court, or obtain through discovery.")
    
    lines.extend([
        "\n---",
        f"*{total_strong} strong, {total_adequate} adequate, {total_weak} weak, {total_gap} gaps across {len(results)} filings*",
    ])
    
    md_path = REPORTS_DIR / "EVIDENCE_GAP_ANALYSIS.md"
    md_path.write_text('\n'.join(lines), encoding='utf-8')
    
    json_path = REPORTS_DIR / "evidence_gaps.json"
    json_path.write_text(json.dumps({
        'generated': datetime.now().isoformat(),
        'tool': 'Evidence Gap Closer (#64)',
        'summary': {'strong': total_strong, 'adequate': total_adequate, 'weak': total_weak, 'gap': total_gap},
        'filings': results,
    }, indent=2, default=str), encoding='utf-8')
    
    print(f"\n✅ Gap analysis: {total_strong} strong, {total_adequate} adequate, {total_weak} weak, {total_gap} gaps")
    print(f"   Reports: {md_path.name}, {json_path.name}")

if __name__ == '__main__':
    main()
