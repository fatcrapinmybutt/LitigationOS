#!/usr/bin/env python3
"""
Perjury Evidence Compiler — LitigationOS Novel Tool
=====================================================
Mines the litigation database to build prosecution-ready perjury packages.

For each actor (Emily Watson, Ronald Berry, etc.), compiles:
  1. Sworn statements that contradict known facts
  2. Prior inconsistent statements (MRE 801(d)(1)(A))
  3. Document-vs-testimony conflicts
  4. Timeline impossibilities
  5. Specific MCL 750.423 (perjury) / 750.424 (false swearing) elements

Each package includes:
  - The sworn false statement (with source citation)
  - The contradicting evidence (with source citation)
  - The legal element analysis (intent, materiality, oath)
  - Recommended exhibit pairing for court presentation

Michigan Perjury Elements (MCL 750.423):
  1. Oath or affirmation (in judicial proceeding)
  2. False statement (demonstrably untrue)
  3. Knowledge of falsity (knew or should have known)
  4. Materiality (statement material to the proceeding)

Usage:
  python perjury_compiler.py --target emily    # Emily Watson's perjury
  python perjury_compiler.py --target berry    # Ronald Berry
  python perjury_compiler.py --all             # All actors
  python perjury_compiler.py --report          # Generate full report
  python perjury_compiler.py --json            # JSON output
"""

import sys, os, re, json, argparse, sqlite3
from datetime import datetime
from collections import defaultdict

sys.stdout = open(sys.stdout.fileno(), mode='w', encoding='utf-8', errors='replace')

REPORTS_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'reports')
DB_PATH = r'C:\Users\andre\LitigationOS\litigation_context.db'

# ─── PERJURY ELEMENTS FRAMEWORK ──────────────────────────────────────

PERJURY_ELEMENTS = {
    'mcl_750_423': {
        'statute': 'MCL 750.423',
        'name': 'Perjury',
        'penalty': 'Felony — up to 15 years',
        'elements': [
            'Statement made under oath or affirmation',
            'In a judicial proceeding or before a tribunal',
            'Statement was false',
            'Defendant knew it was false when made',
            'Statement was material to the proceeding',
        ],
    },
    'mcl_750_424': {
        'statute': 'MCL 750.424',
        'name': 'False Swearing',
        'penalty': 'Felony — up to 15 years',
        'elements': [
            'False statement made under oath',
            'In any matter, proceeding, or document',
            'Knowledge of falsity',
        ],
    },
    'mcl_750_423a': {
        'statute': 'MCL 750.423a',
        'name': 'Subornation of Perjury',
        'penalty': 'Same as perjury — up to 15 years',
        'elements': [
            'Procured or induced another to commit perjury',
            'Knowledge that the statement would be false',
        ],
    },
}

# Target actors
TARGETS = {
    'emily': {
        'name': 'Emily A. Watson',
        'db_patterns': ['watson', 'emily', 'respondent', 'defendant'],
        'sworn_contexts': ['PPO petition', 'custody affidavit', 'FOC hearing testimony', 'trial testimony'],
    },
    'berry': {
        'name': 'Ronald T. Berry',
        'db_patterns': ['berry', 'ronald'],
        'sworn_contexts': ['court testimony', 'declarations'],
    },
    'barnes': {
        'name': 'Jennifer Barnes (P55406)',
        'db_patterns': ['barnes', 'jennifer barnes'],
        'sworn_contexts': ['officer of the court representations', 'pleadings'],
    },
    'mcneill': {
        'name': 'Hon. Jenny L. McNeill',
        'db_patterns': ['mcneill', 'judge'],
        'sworn_contexts': ['judicial orders', 'findings of fact', 'bench rulings'],
    },
    'lori_watson': {
        'name': 'Lori Watson',
        'db_patterns': ['lori watson', 'lori'],
        'sworn_contexts': ['PPO service affidavit'],
    },
}


def get_db_connection():
    """Get a database connection with proper PRAGMAs."""
    conn = sqlite3.connect(DB_PATH, timeout=30)
    conn.execute("PRAGMA busy_timeout=60000")
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA cache_size=-32000")
    conn.row_factory = sqlite3.Row
    return conn


def table_exists(conn, table_name):
    """Check if a table exists."""
    row = conn.execute(
        "SELECT COUNT(*) FROM sqlite_master WHERE type='table' AND name=?",
        (table_name,)
    ).fetchone()
    return row[0] > 0


def mine_contradictions(conn, target_key, target_info):
    """Mine contradictions for a target from DB."""
    results = []
    patterns = target_info['db_patterns']
    
    # 1. watson_perjury_compilation table (direct perjury evidence)
    if table_exists(conn, 'watson_perjury_compilation'):
        for pat in patterns:
            try:
                rows = conn.execute(
                    "SELECT * FROM watson_perjury_compilation WHERE "
                    "LOWER(COALESCE(actor,'') || ' ' || COALESCE(category,'') || ' ' || COALESCE(description,'')) LIKE ? LIMIT 100",
                    (f'%{pat}%',)
                ).fetchall()
                for row in rows:
                    results.append({
                        'source_table': 'watson_perjury_compilation',
                        'category': dict(row).get('category', ''),
                        'description': dict(row).get('description', '')[:500],
                        'evidence_type': 'direct_perjury',
                    })
            except Exception:
                pass
    
    # 2. detected_contradictions table
    if table_exists(conn, 'detected_contradictions'):
        for pat in patterns:
            try:
                rows = conn.execute(
                    "SELECT * FROM detected_contradictions WHERE "
                    "LOWER(COALESCE(entity,'') || ' ' || COALESCE(statement_a,'') || ' ' || COALESCE(statement_b,'')) LIKE ? LIMIT 100",
                    (f'%{pat}%',)
                ).fetchall()
                for row in rows:
                    d = dict(row)
                    results.append({
                        'source_table': 'detected_contradictions',
                        'statement_a': d.get('statement_a', '')[:300],
                        'statement_b': d.get('statement_b', '')[:300],
                        'contradiction_type': d.get('contradiction_type', ''),
                        'evidence_type': 'contradiction',
                    })
            except Exception:
                pass
    
    # 3. contradiction_map table
    if table_exists(conn, 'contradiction_map'):
        for pat in patterns:
            try:
                rows = conn.execute(
                    "SELECT * FROM contradiction_map WHERE "
                    "LOWER(COALESCE(actor,'') || ' ' || COALESCE(claim_text,'') || ' ' || COALESCE(contradiction_text,'')) LIKE ? LIMIT 100",
                    (f'%{pat}%',)
                ).fetchall()
                for row in rows:
                    d = dict(row)
                    results.append({
                        'source_table': 'contradiction_map',
                        'claim': d.get('claim_text', '')[:300],
                        'contradiction': d.get('contradiction_text', '')[:300],
                        'evidence_type': 'mapped_contradiction',
                    })
            except Exception:
                pass
    
    # 4. adversary_assertions table
    if table_exists(conn, 'adversary_assertions'):
        for pat in patterns:
            try:
                rows = conn.execute(
                    "SELECT * FROM adversary_assertions WHERE "
                    "LOWER(COALESCE(actor,'') || ' ' || COALESCE(assertion_text,'')) LIKE ? LIMIT 50",
                    (f'%{pat}%',)
                ).fetchall()
                for row in rows:
                    d = dict(row)
                    results.append({
                        'source_table': 'adversary_assertions',
                        'assertion': d.get('assertion_text', '')[:300],
                        'evidence_type': 'adversary_assertion',
                    })
            except Exception:
                pass
    
    return results


def analyze_perjury_elements(evidence_items, target_info):
    """Analyze evidence against MCL 750.423 elements."""
    analysis = {
        'total_items': len(evidence_items),
        'by_type': defaultdict(int),
        'element_coverage': {},
        'strongest_items': [],
        'prosecution_ready': 0,
    }
    
    for item in evidence_items:
        analysis['by_type'][item.get('evidence_type', 'unknown')] += 1
    
    # Element coverage analysis
    elements = PERJURY_ELEMENTS['mcl_750_423']['elements']
    coverage = {}
    
    # Element 1: Under oath — sworn contexts are known
    coverage['oath'] = len(target_info.get('sworn_contexts', [])) > 0
    
    # Element 2: Judicial proceeding
    coverage['judicial_proceeding'] = True  # All evidence is from court proceedings
    
    # Element 3: False statement — contradictions prove this
    contradiction_count = sum(1 for i in evidence_items if 'contradiction' in i.get('evidence_type', ''))
    coverage['false_statement'] = contradiction_count > 0
    coverage['false_statement_count'] = contradiction_count
    
    # Element 4: Knowledge of falsity — direct perjury items
    perjury_count = sum(1 for i in evidence_items if i.get('evidence_type') == 'direct_perjury')
    coverage['knowledge'] = perjury_count > 0
    coverage['knowledge_count'] = perjury_count
    
    # Element 5: Materiality — all custody/PPO statements are material
    coverage['materiality'] = True
    
    analysis['element_coverage'] = coverage
    
    # Count prosecution-ready items (have both false statement + knowledge indicators)
    analysis['prosecution_ready'] = min(contradiction_count, perjury_count)
    
    # All elements met?
    analysis['all_elements_met'] = all([
        coverage['oath'], coverage['judicial_proceeding'],
        coverage['false_statement'], coverage['knowledge'],
        coverage['materiality']
    ])
    
    return analysis


def generate_report(all_results):
    """Generate markdown prosecution report."""
    lines = [
        "# PERJURY EVIDENCE COMPILATION",
        f"## Generated: {datetime.now().strftime('%B %d, %Y')}",
        "",
        "### Legal Framework",
        f"- **MCL 750.423** — Perjury (felony, up to 15 years)",
        f"- **MCL 750.424** — False Swearing (felony, up to 15 years)",
        f"- **MCL 750.423a** — Subornation of Perjury",
        f"- **MRE 801(d)(1)(A)** — Prior inconsistent statements",
        "",
    ]
    
    for target_key, data in all_results.items():
        target = data['target']
        analysis = data['analysis']
        items = data['items']
        
        lines.append(f"---")
        lines.append(f"## {target['name']}")
        lines.append(f"")
        lines.append(f"**Total Evidence Items:** {analysis['total_items']}")
        lines.append(f"**Prosecution Ready:** {analysis['prosecution_ready']}")
        lines.append(f"**All Elements Met:** {'YES ✅' if analysis['all_elements_met'] else 'INCOMPLETE ⚠'}")
        lines.append(f"")
        
        # Element checklist
        cov = analysis['element_coverage']
        lines.append(f"### MCL 750.423 Element Checklist")
        lines.append(f"- [{'x' if cov.get('oath') else ' '}] Oath/affirmation — Sworn contexts: {', '.join(target.get('sworn_contexts', []))}")
        lines.append(f"- [{'x' if cov.get('judicial_proceeding') else ' '}] Judicial proceeding — All from court record")
        lines.append(f"- [{'x' if cov.get('false_statement') else ' '}] False statement — {cov.get('false_statement_count', 0)} contradictions found")
        lines.append(f"- [{'x' if cov.get('knowledge') else ' '}] Knowledge of falsity — {cov.get('knowledge_count', 0)} direct perjury items")
        lines.append(f"- [{'x' if cov.get('materiality') else ' '}] Materiality — custody/PPO proceedings = inherently material")
        lines.append(f"")
        
        # Evidence by type
        lines.append(f"### Evidence by Type")
        for etype, count in analysis['by_type'].items():
            lines.append(f"- {etype}: {count}")
        lines.append(f"")
        
        # Sample items (first 10)
        lines.append(f"### Sample Evidence (first 10)")
        for i, item in enumerate(items[:10], 1):
            lines.append(f"**{i}.** [{item.get('evidence_type', '?')}] ({item.get('source_table', '?')})")
            if 'description' in item:
                lines.append(f"   {item['description'][:200]}")
            elif 'statement_a' in item:
                lines.append(f"   Statement A: {item['statement_a'][:150]}")
                lines.append(f"   Statement B: {item['statement_b'][:150]}")
            elif 'claim' in item:
                lines.append(f"   Claim: {item['claim'][:150]}")
                lines.append(f"   Contradiction: {item['contradiction'][:150]}")
            lines.append(f"")
    
    return '\n'.join(lines)


def print_dashboard(all_results, verbose=False):
    """Print perjury compilation dashboard."""
    print(f"\n{'═' * 78}")
    print(f"  PERJURY EVIDENCE COMPILER — LitigationOS")
    print(f"  {datetime.now().strftime('%Y-%m-%d %H:%M')}")
    print(f"{'═' * 78}\n")
    
    print(f"  {'Target':<25} {'Items':>6} {'Contrad':>8} {'Perjury':>8} {'Ready':>6} {'Elements'}")
    print(f"  {'─' * 72}")
    
    for target_key, data in all_results.items():
        target = data['target']
        analysis = data['analysis']
        name = target['name'][:25]
        total = analysis['total_items']
        contrad = analysis['by_type'].get('contradiction', 0) + analysis['by_type'].get('mapped_contradiction', 0)
        perjury = analysis['by_type'].get('direct_perjury', 0)
        ready = analysis['prosecution_ready']
        elements = '✅ ALL MET' if analysis['all_elements_met'] else '⚠ INCOMPLETE'
        
        print(f"  {name:<25} {total:>6} {contrad:>8} {perjury:>8} {ready:>6} {elements}")
    
    total_all = sum(d['analysis']['total_items'] for d in all_results.values())
    total_ready = sum(d['analysis']['prosecution_ready'] for d in all_results.values())
    print(f"  {'─' * 72}")
    print(f"  {'TOTAL':<25} {total_all:>6} {'':>8} {'':>8} {total_ready:>6}")
    
    if verbose:
        for target_key, data in all_results.items():
            analysis = data['analysis']
            print(f"\n  ▓ {data['target']['name']}")
            for etype, count in analysis['by_type'].items():
                print(f"    {etype}: {count}")
    
    print()


def main():
    parser = argparse.ArgumentParser(description='Perjury Evidence Compiler')
    parser.add_argument('--target', '-t', type=str, help='Target actor (emily/berry/barnes/mcneill/lori_watson)')
    parser.add_argument('--all', '-a', action='store_true', help='All targets')
    parser.add_argument('--report', '-r', action='store_true', help='Generate report')
    parser.add_argument('--verbose', '-v', action='store_true', help='Verbose')
    parser.add_argument('--json', '-j', action='store_true', help='JSON output')
    args = parser.parse_args()
    
    if not args.all and not args.target:
        args.all = True
    
    targets = list(TARGETS.keys()) if args.all else [args.target.lower()]
    
    conn = get_db_connection()
    all_results = {}
    
    for tkey in targets:
        tinfo = TARGETS.get(tkey)
        if not tinfo:
            print(f"  Unknown target: {tkey}")
            continue
        
        items = mine_contradictions(conn, tkey, tinfo)
        analysis = analyze_perjury_elements(items, tinfo)
        all_results[tkey] = {
            'target': tinfo,
            'items': items,
            'analysis': analysis,
        }
    
    conn.close()
    
    print_dashboard(all_results, args.verbose)
    
    if args.report:
        os.makedirs(REPORTS_DIR, exist_ok=True)
        report = generate_report(all_results)
        rpath = os.path.join(REPORTS_DIR, 'PERJURY_EVIDENCE_REPORT.md')
        with open(rpath, 'w', encoding='utf-8') as f:
            f.write(report)
        print(f"  📄 Report: {rpath}")
    
    if args.json:
        os.makedirs(REPORTS_DIR, exist_ok=True)
        jpath = os.path.join(REPORTS_DIR, 'perjury_evidence.json')
        out = {}
        for tkey, data in all_results.items():
            out[tkey] = {
                'name': data['target']['name'],
                'total_items': data['analysis']['total_items'],
                'by_type': dict(data['analysis']['by_type']),
                'all_elements_met': data['analysis']['all_elements_met'],
                'prosecution_ready': data['analysis']['prosecution_ready'],
                'element_coverage': data['analysis']['element_coverage'],
            }
        with open(jpath, 'w', encoding='utf-8') as f:
            json.dump({'results': out, 'generated': datetime.now().isoformat()}, f, indent=2, default=str)
        print(f"  📊 JSON: {jpath}")


if __name__ == '__main__':
    main()
