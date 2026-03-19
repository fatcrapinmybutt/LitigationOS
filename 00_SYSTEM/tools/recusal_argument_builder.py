#!/usr/bin/env python3
"""
Tool #72 — Judicial Recusal Argument Builder
================================================
Builds the strongest possible MCR 2.003 disqualification argument
against Judge McNeill by mining ALL evidence in the DB.

Structures the argument per MCR 2.003(C)(1) factors:
(a) Personal bias or prejudice
(b) Personal knowledge of disputed facts
(c) Attorney in the matter
(d) Financial interest
(e) Related within third degree
(f) Would be a material witness

Also builds the "appearance of impropriety" argument under
Canon 2 of the Michigan Code of Judicial Conduct.
"""
import sys, json, sqlite3
from pathlib import Path
from datetime import datetime

sys.stdout = open(sys.stdout.fileno(), mode='w', encoding='utf-8', errors='replace')

REPO = Path(r"C:\Users\andre\LitigationOS")
DB_PATH = REPO / "litigation_context.db"
REPORTS_DIR = REPO / "00_SYSTEM" / "reports"

MCR_2003_FACTORS = {
    'C1a': {
        'factor': 'Personal bias or prejudice concerning a party',
        'mcr': 'MCR 2.003(C)(1)(a)',
        'evidence_queries': [
            ("judicial_violations", "SELECT COUNT(*) FROM judicial_violations WHERE violation_type LIKE '%bias%' OR violation_type LIKE '%prejudice%'"),
            ("docket_events", "SELECT COUNT(*) FROM docket_events WHERE description LIKE '%denied%father%' OR description LIKE '%denied%Andrew%' OR description LIKE '%denied%Pigors%'"),
        ],
        'key_facts': [
            'Pattern of ruling against father on every motion',
            'Granted Emily\'s ex-parte motions without hearing',
            'Denied Andrew\'s motions without stated basis',
            'Hostile demeanor toward pro se father',
        ],
    },
    'C1b': {
        'factor': 'Personal knowledge of disputed evidentiary facts',
        'mcr': 'MCR 2.003(C)(1)(b)',
        'evidence_queries': [],
        'key_facts': [
            'Received ex-parte communications through Pamela Rusco',
            'Relied on information not in the record',
            'Made factual findings without evidentiary hearing',
        ],
    },
    'appearance': {
        'factor': 'Appearance of impropriety (Canon 2, MI Code of Judicial Conduct)',
        'mcr': 'Canon 2, Rule 2.11',
        'evidence_queries': [
            ("judicial_violations", "SELECT COUNT(*) FROM judicial_violations"),
        ],
        'key_facts': [
            'Reasonable person would question impartiality',
            'Pattern establishes cumulative bias (Armstrong v Ypsilanti)',
            'Ex-parte orders without required findings (MCL 722.27a(3))',
            'Failure to recuse despite documented pattern',
        ],
    },
}

def mine_evidence():
    """Mine the DB for all McNeill-related evidence."""
    results = {}
    try:
        conn = sqlite3.connect(str(DB_PATH), timeout=30)
        conn.execute("PRAGMA busy_timeout=60000")
        conn.execute("PRAGMA journal_mode=WAL")
        
        tables = [r[0] for r in conn.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall()]
        
        # Count judicial violations
        if 'judicial_violations' in tables:
            try:
                total = conn.execute("SELECT COUNT(*) FROM judicial_violations").fetchone()[0]
                results['total_violations'] = total
                
                # Try to get violation types
                cols = [r[1] for r in conn.execute("PRAGMA table_info(judicial_violations)").fetchall()]
                if 'violation_type' in cols:
                    types = conn.execute("""
                        SELECT violation_type, COUNT(*) as cnt 
                        FROM judicial_violations 
                        WHERE violation_type IS NOT NULL
                        GROUP BY violation_type 
                        ORDER BY cnt DESC 
                        LIMIT 10
                    """).fetchall()
                    results['violation_types'] = {t: c for t, c in types}
            except Exception as e:
                results['jv_error'] = str(e)
        
        # Count docket events showing bias
        if 'docket_events' in tables:
            try:
                total = conn.execute("SELECT COUNT(*) FROM docket_events").fetchone()[0]
                results['docket_events'] = total
                
                denied = conn.execute("""
                    SELECT COUNT(*) FROM docket_events 
                    WHERE description LIKE '%denied%' OR description LIKE '%dismiss%'
                """).fetchone()[0]
                results['denied_events'] = denied
            except Exception as e:
                results['de_error'] = str(e)
        
        # Count ex-parte related items
        if 'evidence_quotes' in tables:
            try:
                exparte = conn.execute("""
                    SELECT COUNT(*) FROM evidence_quotes 
                    WHERE quote_text LIKE '%ex parte%' OR quote_text LIKE '%ex-parte%'
                """).fetchone()[0]
                results['exparte_evidence'] = exparte
            except:
                pass
        
        conn.close()
    except Exception as e:
        results['error'] = str(e)
    
    return results

def build_argument():
    """Build the structured recusal argument."""
    evidence = mine_evidence()
    
    argument = {
        'title': 'MOTION FOR DISQUALIFICATION OF HON. JENNY L. McNEILL',
        'authority': 'MCR 2.003(C)(1)',
        'standard': 'A reasonable person, knowing all the circumstances, would harbor a reasonable fear of lack of impartiality. Crampton v Dept of State, 395 Mich 347 (1975).',
        'factors': {},
        'evidence_counts': evidence,
        'authorities': [
            'MCR 2.003(C)(1)(a)-(f) — Grounds for disqualification',
            'Crampton v Dept of State, 395 Mich 347 (1975) — Objective bias test',
            'Armstrong v Ypsilanti Charter Twp, 248 Mich App 573 (2001) — Pattern establishes bias',
            'In re Dougherty, 429 Mich 81 (1987) — Contemnor must be heard',
            'Canon 2, MI Code of Judicial Conduct — Appearance of impropriety',
            'Rule 2.11, MI Rules of Judicial Conduct — Disqualification required',
            'Liteky v United States, 510 US 540 (1994) — Extrajudicial source doctrine',
            'In re MKK, 286 Mich App 546 (2009) — Cumulative errors require reversal',
        ],
    }
    
    for factor_id, factor in MCR_2003_FACTORS.items():
        argument['factors'][factor_id] = {
            'factor': factor['factor'],
            'mcr': factor['mcr'],
            'key_facts': factor['key_facts'],
        }
    
    return argument

def main():
    print("=" * 70)
    print("JUDICIAL RECUSAL ARGUMENT BUILDER — Tool #72")
    print("=" * 70)
    
    argument = build_argument()
    evidence = argument['evidence_counts']
    
    total_v = evidence.get('total_violations', 0)
    denied = evidence.get('denied_events', 0)
    exparte = evidence.get('exparte_evidence', 0)
    
    print(f"\n  Judicial violations in DB: {total_v}")
    print(f"  Denial/dismissal events: {denied}")
    print(f"  Ex-parte evidence items: {exparte}")
    
    if 'violation_types' in evidence:
        print("\n  Top violation types:")
        for vtype, cnt in list(evidence['violation_types'].items())[:5]:
            print(f"    {vtype}: {cnt}")
    
    lines = [
        "# ⚖️ JUDICIAL RECUSAL ARGUMENT — MCR 2.003",
        f"*Re: Hon. Jenny L. McNeill — 14th Circuit Court*",
        f"*Generated: {datetime.now().strftime('%Y-%m-%d %H:%M')}*\n",
        "---\n",
        "## Legal Standard",
        f"> {argument['standard']}\n",
        "## Evidence Arsenal",
        f"- **{total_v}** documented judicial violations",
        f"- **{denied}** denial/dismissal events in docket",
        f"- **{exparte}** ex-parte evidence items",
        "",
    ]
    
    for fid, factor in argument['factors'].items():
        lines.append(f"## {factor['mcr']}: {factor['factor']}\n")
        for fact in factor['key_facts']:
            lines.append(f"- {fact}")
        lines.append("")
    
    lines.append("## Supporting Authorities\n")
    for auth in argument['authorities']:
        lines.append(f"- {auth}")
    
    lines.extend([
        "",
        "## Argument Structure (for F3 brief)",
        "1. **Threshold**: MCR 2.003(C)(1) requires disqualification when a reasonable",
        "   person would question impartiality. *Crampton*, 395 Mich at 351.",
        "2. **Pattern**: Document the cumulative pattern of one-sided rulings.",
        "   *Armstrong*, 248 Mich App at 591 (pattern establishes bias).",
        "3. **Ex-Parte**: Show improper ex-parte communications through Rusco.",
        "   Canon 3(A)(4) prohibits ex-parte communications.",
        "4. **Due Process**: Father never received notice or hearing before",
        "   parenting time was suspended. MCL 722.27a(3) requires specific findings.",
        "5. **Cumulative Error**: Even if individual acts seem minor, the cumulative",
        "   effect destroys the appearance of impartiality. *In re MKK*, 286 Mich App 546.",
        "6. **Remedy**: Disqualification and reassignment to a new judge.",
        "   All orders entered by McNeill should be vacated as products of bias.",
        "",
        "---",
        f"*Judicial Recusal Argument Builder — Tool #72*",
        f"*{total_v} violations | {denied} denials | {exparte} ex-parte items*",
    ])
    
    md_path = REPORTS_DIR / "RECUSAL_ARGUMENT.md"
    md_path.write_text('\n'.join(lines), encoding='utf-8')
    
    json_path = REPORTS_DIR / "recusal_argument.json"
    json_path.write_text(json.dumps({
        'generated': datetime.now().isoformat(),
        'tool': 'Judicial Recusal Argument Builder (#72)',
        'argument': argument,
    }, indent=2, default=str), encoding='utf-8')
    
    print(f"\n✅ Recusal argument built with {len(argument['authorities'])} authorities")
    print(f"   Reports: RECUSAL_ARGUMENT.md + recusal_argument.json")

if __name__ == '__main__':
    main()
