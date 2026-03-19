#!/usr/bin/env python3
"""
Tool #57 — Lawsuit Target Harvester
======================================
Mines the litigation database for evidence supporting claims against
each defendant/target. Maps evidence → legal theories → damages.

Targets:
1. Emily A. Watson — Perjury, fraud, parental alienation, conspiracy
2. Ronald T. Berry — Conspiracy, unauthorized practice of law, interference
3. Jennifer Barnes P55406 — Malpractice-adjacent, conspiracy, withdrawal issues
4. Hon. Jenny L. McNeill — §1983 (via conspiracy exception), judicial misconduct
5. Shady Oaks / Cricklewood — Housing discrimination, lease violations
"""
import sys, json, sqlite3
from pathlib import Path
from datetime import datetime

sys.stdout = open(sys.stdout.fileno(), mode='w', encoding='utf-8', errors='replace')

REPO = Path(r"C:\Users\andre\LitigationOS")
DB_PATH = REPO / "litigation_context.db"
REPORTS_DIR = REPO / "00_SYSTEM" / "reports"

TARGETS = {
    'Emily A. Watson': {
        'role': 'Defendant — Mother/Opposing Party',
        'legal_theories': [
            'MCL 750.423 — Perjury (false PPO allegations)',
            'MCL 750.424 — False swearing in custody proceedings', 
            'MCL 750.157a — Criminal conspiracy to deprive parental rights',
            '42 USC §1985(3) — Conspiracy to deprive civil rights',
            'MCL 722.23(j) — Willful interference with parenting time',
            'Tortious interference with parental relationship',
        ],
        'search_terms': ['Emily', 'Watson', 'mother', 'respondent', 'defendant'],
        'db_tables': ['watson_perjury_compilation', 'detected_contradictions', 'adversary_assertions'],
    },
    'Ronald T. Berry': {
        'role': 'Co-conspirator — Emily\'s boyfriend/domestic partner',
        'legal_theories': [
            '42 USC §1985(3) — Conspiracy to deprive civil rights',
            'MCL 600.916 — Unauthorized practice of law (if acted as legal advisor)',
            'Tortious interference with parental relationship',
            'Dennis v Sparks — Co-conspirator loses judicial immunity shield',
        ],
        'search_terms': ['Berry', 'Ronald', 'boyfriend', 'partner'],
        'db_tables': ['watson_perjury_compilation', 'adversary_assertions'],
    },
    'Jennifer Barnes P55406': {
        'role': 'Emily\'s former attorney (withdrew)',
        'legal_theories': [
            'MRPC 3.3 — Candor toward tribunal (presenting false evidence)',
            'MRPC 3.4 — Fairness to opposing party',
            'MRPC 8.4 — Misconduct (dishonesty, fraud)',
            '42 USC §1985(3) — Conspiracy (if participated in fraud)',
            'AGC complaint for professional misconduct',
        ],
        'search_terms': ['Barnes', 'attorney', 'counsel', 'P55406'],
        'db_tables': ['adversary_assertions'],
    },
    'Hon. Jenny L. McNeill': {
        'role': 'Judge — 14th Circuit Court, Family Division',
        'legal_theories': [
            '42 USC §1983 — Deprivation of rights under color of law',
            'Dennis v Sparks 449 US 24 — Conspiracy pierces judicial immunity',
            'Const 1963 Art 6 §30 — JTC complaint',
            'Canon 2 — Appearance of impropriety',
            'Canon 3(A)(4) — Ex parte communications',
        ],
        'search_terms': ['McNeill', 'judge', 'court', 'Honor'],
        'db_tables': ['judicial_violations', 'actor_violations'],
    },
    'Shady Oaks / Cricklewood': {
        'role': 'Housing — Mobile home park and management company',
        'legal_theories': [
            'MCL 600.5714 — Wrongful eviction',
            'Fair Housing Act — Discrimination',
            'Breach of lease agreement',
            'Michigan Mobile Home Commission Act violations',
        ],
        'search_terms': ['Shady Oaks', 'Cricklewood', 'mobile home', 'lot rent', 'eviction'],
        'db_tables': ['evidence_quotes'],
    },
}

def count_evidence(conn, target_name, target_info):
    """Count evidence items for a target across relevant tables."""
    counts = {}
    
    for table in target_info['db_tables']:
        try:
            # Get columns
            cols = [r[1] for r in conn.execute(f"PRAGMA table_info({table})").fetchall()]
            if not cols:
                continue
            
            # Search across text columns
            text_cols = [c for c in cols if any(t in c.lower() for t in ['text', 'statement', 'description', 'quote', 'content', 'finding', 'violation', 'assertion'])]
            if not text_cols:
                text_cols = cols[1:3]  # Fall back to first couple data columns
            
            total = 0
            for term in target_info['search_terms']:
                for col in text_cols:
                    try:
                        count = conn.execute(
                            f"SELECT COUNT(*) FROM {table} WHERE {col} LIKE ?",
                            (f'%{term}%',)
                        ).fetchone()[0]
                        total += count
                    except:
                        continue
            
            if total > 0:
                counts[table] = total
        except Exception as e:
            counts[f'{table}_error'] = str(e)
    
    return counts

def main():
    print("=" * 70)
    print("LAWSUIT TARGET HARVESTER — Tool #57")
    print(f"Started: {datetime.now().isoformat()}")
    print("=" * 70)
    
    conn = sqlite3.connect(str(DB_PATH), timeout=30)
    conn.execute("PRAGMA busy_timeout=60000")
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA cache_size=-32000")
    conn.row_factory = sqlite3.Row
    
    all_results = {}
    
    for target_name, target_info in TARGETS.items():
        print(f"\n🎯 Harvesting evidence against: {target_name}")
        print(f"   Role: {target_info['role']}")
        
        # Count evidence
        counts = count_evidence(conn, target_name, target_info)
        total = sum(v for k, v in counts.items() if not k.endswith('_error'))
        
        print(f"   Evidence items: {total:,}")
        for table, count in counts.items():
            if not str(table).endswith('_error'):
                print(f"     {table}: {count:,}")
        
        all_results[target_name] = {
            'role': target_info['role'],
            'legal_theories': target_info['legal_theories'],
            'evidence_counts': counts,
            'total_evidence': total,
        }
    
    conn.close()
    
    # Generate report
    lines = [
        "# LAWSUIT TARGET EVIDENCE HARVEST",
        f"*Generated: {datetime.now().strftime('%Y-%m-%d %H:%M')}*\n",
        "## Target Summary",
        "| Target | Role | Evidence Items | Legal Theories |",
        "|--------|------|---------------|----------------|",
    ]
    
    for name, data in all_results.items():
        lines.append(f"| {name} | {data['role'][:40]} | {data['total_evidence']:,} | {len(data['legal_theories'])} |")
    
    for name, data in all_results.items():
        lines.extend([
            f"\n## {name}",
            f"**Role:** {data['role']}",
            f"**Total evidence items:** {data['total_evidence']:,}",
            "",
            "### Legal Theories",
        ])
        for theory in data['legal_theories']:
            lines.append(f"- {theory}")
        
        lines.extend(["", "### Evidence by Source"])
        for table, count in data['evidence_counts'].items():
            if not str(table).endswith('_error'):
                lines.append(f"- `{table}`: {count:,} items")
    
    grand_total = sum(d['total_evidence'] for d in all_results.values())
    lines.extend([
        "",
        "---",
        f"*Grand total: {grand_total:,} evidence items across {len(TARGETS)} targets*",
    ])
    
    md_path = REPORTS_DIR / "LAWSUIT_TARGET_HARVEST.md"
    md_path.write_text('\n'.join(lines), encoding='utf-8')
    
    json_path = REPORTS_DIR / "lawsuit_targets.json"
    json_path.write_text(json.dumps({
        'generated': datetime.now().isoformat(),
        'tool': 'Lawsuit Target Harvester (#57)',
        'targets': all_results,
        'grand_total': grand_total,
    }, indent=2, default=str), encoding='utf-8')
    
    print(f"\n✅ Reports: {md_path.name}, {json_path.name}")
    print(f"🎯 Grand total: {grand_total:,} evidence items across {len(TARGETS)} targets")

if __name__ == '__main__':
    main()
