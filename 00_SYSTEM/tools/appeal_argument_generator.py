#!/usr/bin/env python3
"""Tool #243: Appeal Argument Generator.

Generates structured appellate arguments for COA 366810. Queries authority_chains
for legal authorities, judicial_violations for McNeill errors, docket_events for
procedural history. Generates IRAC-format arguments:
  (1) Due process violations
  (2) Abuse of discretion in custody
  (3) Ex parte communications
  (4) Failure to make required findings per MCL 722.27a

Each argument with standard of review, authorities, evidence citations.

Outputs: MD + JSON reports to 00_SYSTEM/reports/
"""
import sys
import os
import json
import sqlite3
from datetime import datetime

sys.stdout = open(sys.stdout.fileno(), mode='w', encoding='utf-8', errors='replace')

def s(v):
    """Safe lowercase string conversion — prevents NoneType crashes."""
    return (v or "").lower()

DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', 'litigation_context.db')
REPORTS_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'reports')
os.makedirs(REPORTS_DIR, exist_ok=True)

APPELLATE_ARGUMENTS = [
    {
        'id': 'ARG-1',
        'title': 'Due Process Violations',
        'issue': 'Whether the trial court violated Plaintiff-Appellant\'s procedural due process rights under the Fourteenth Amendment and Const 1963, art 1, § 17 by entering ex parte orders without notice or opportunity to be heard.',
        'standard_of_review': 'Constitutional questions are reviewed de novo. Const 1963, art 1, § 17; US Const, Am XIV. Due process violations are questions of law reviewed without deference. In re Rood, 483 Mich 73, 91 (2009).',
        'keywords': ['due process', 'ex parte', 'notice', 'hearing', 'opportunity to be heard',
                     'without notice', 'emergency order', 'suspend', 'fundamental right',
                     'fourteenth amendment', 'constitutional'],
        'violation_keywords': ['due process', 'ex parte', 'notice', 'hearing', 'opportunity'],
        'authorities': [
            'US Const, Am XIV (Due Process Clause)',
            'Const 1963, art 1, § 17 (Michigan Due Process)',
            'Mathews v Eldridge, 424 US 319 (1976) (three-factor balancing test)',
            'In re Rood, 483 Mich 73, 91 (2009) (de novo review of constitutional questions)',
            'MCR 3.207(B) (ex parte orders in domestic relations)',
            'Troxel v Granville, 530 US 57 (2000) (parental rights as fundamental liberty interest)',
        ],
    },
    {
        'id': 'ARG-2',
        'title': 'Abuse of Discretion in Custody Determination',
        'issue': 'Whether the trial court abused its discretion by restricting Plaintiff-Appellant\'s parenting time without adequate evidentiary basis and without proper consideration of the best-interest factors under MCL 722.23.',
        'standard_of_review': 'Custody decisions are reviewed for abuse of discretion. MCL 722.28. The trial court\'s findings of fact are reviewed for clear error. A finding is clearly erroneous if, after review of the entire record, the appellate court is left with the definite and firm conviction that a mistake was made. Pierron v Pierron, 486 Mich 81, 85 (2010).',
        'keywords': ['custody', 'parenting time', 'best interest', 'abuse of discretion',
                     'restrict', 'suspend', 'factor', '722.23', '722.27', 'evidentiary',
                     'finding', 'clear error'],
        'violation_keywords': ['custody', 'parenting', 'best interest', 'restrict', 'suspend'],
        'authorities': [
            'MCL 722.23 (Best Interest Factors)',
            'MCL 722.27 (Court authority to modify custody)',
            'MCL 722.27a (Parenting time)',
            'MCL 722.28 (Appellate review standard)',
            'Pierron v Pierron, 486 Mich 81 (2010) (clear error review of findings)',
            'Vodvarka v Grasmeyer, 259 Mich App 499 (2003) (proper cause/change of circumstances)',
            'Shade v Wright, 291 Mich App 17 (2010) (parenting time modification standard)',
        ],
    },
    {
        'id': 'ARG-3',
        'title': 'Ex Parte Communications',
        'issue': 'Whether the trial court engaged in improper ex parte communications with Defendant\'s counsel, the FOC, or other parties in violation of MCR 2.003 and the Michigan Code of Judicial Conduct.',
        'standard_of_review': 'Judicial disqualification is reviewed for abuse of discretion. MCR 2.003(D). However, actual bias is reviewed de novo as a constitutional question. Armstrong v Ypsilanti Charter Twp, 248 Mich App 573, 597 (2001).',
        'keywords': ['ex parte', 'communication', 'off-record', 'bias', 'disqualification',
                     'mcr 2.003', 'canon', 'judicial conduct', 'rusco', 'foc', 'barnes'],
        'violation_keywords': ['ex parte', 'communication', 'off-record', 'canon', 'bias'],
        'authorities': [
            'MCR 2.003(C) (Grounds for disqualification)',
            'MCJC Canon 2 (Impropriety and appearance of impropriety)',
            'MCJC Canon 3(A)(4) (Prohibition on ex parte communications)',
            'Armstrong v Ypsilanti Charter Twp, 248 Mich App 573 (2001)',
            'Cain v Dep\'t of Corrections, 451 Mich 470 (1996) (due process requires impartial tribunal)',
            'In re MKK, 286 Mich App 546 (2009) (ex parte communications as basis for disqualification)',
        ],
    },
    {
        'id': 'ARG-4',
        'title': 'Failure to Make Required Findings Under MCL 722.27a',
        'issue': 'Whether the trial court erred by restricting parenting time without making the specific findings required by MCL 722.27a(6), including findings that parenting time would endanger the child\'s physical, mental, or emotional health.',
        'standard_of_review': 'Failure to make required findings is a question of law reviewed de novo. The trial court\'s findings, where made, are reviewed for clear error. Lieberman v Orr, 319 Mich App 68, 78 (2017).',
        'keywords': ['722.27a', 'required findings', 'endanger', 'physical mental emotional',
                     'parenting time restriction', 'specific findings', 'no finding',
                     'failed to find', 'absent findings', 'conditions'],
        'violation_keywords': ['finding', '722.27', 'parenting', 'restrict', 'endanger'],
        'authorities': [
            'MCL 722.27a(6) (Required findings for parenting time restriction)',
            'MCL 722.27a(7) (Conditions on parenting time)',
            'Lieberman v Orr, 319 Mich App 68 (2017) (required findings)',
            'Shade v Wright, 291 Mich App 17 (2010) (parenting time standard)',
            'Brown v Loveman, 260 Mich App 576 (2004) (necessity of findings on record)',
            'Berger v Berger, 277 Mich App 700 (2008) (clear error in custody findings)',
        ],
    },
]

def get_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA busy_timeout=60000")
    conn.execute("PRAGMA cache_size=-32000")
    conn.execute("PRAGMA temp_store=MEMORY")
    conn.execute("PRAGMA synchronous=NORMAL")
    return conn

def verify_table(conn, table_name):
    cur = conn.execute(f"PRAGMA table_info({table_name})")
    cols = [row['name'] for row in cur.fetchall()]
    if not cols:
        print(f"  WARNING: Table '{table_name}' does not exist")
    return cols

def get_authority_chains(conn):
    """Get all authority chains for appellate arguments."""
    cols = verify_table(conn, 'authority_chains')
    if not cols:
        return []
    rows = conn.execute("""
        SELECT id, filing_vehicle, fact_claim, authority_cite, authority_type,
               elements, evidence_doc_id, evidence_quote, chain_complete, gap_description
        FROM authority_chains
        ORDER BY id
    """).fetchall()
    return [dict(r) for r in rows]

def get_judicial_violations(conn):
    """Get all judicial violations by McNeill."""
    cols = verify_table(conn, 'judicial_violations')
    if not cols:
        return []
    rows = conn.execute("""
        SELECT violation_id, judge_name, canon_number, canon_text,
               violation_description, evidence_refs, severity, jtc_exhibit_id
        FROM judicial_violations
        WHERE LOWER(judge_name) LIKE '%mcneill%'
        ORDER BY severity DESC, violation_id
    """).fetchall()
    return [dict(r) for r in rows]

def get_procedural_history(conn):
    """Get docket events for procedural history."""
    cols = verify_table(conn, 'docket_events')
    if not cols:
        return []
    rows = conn.execute("""
        SELECT event_id, case_id, event_date_iso, title, event_type, summary
        FROM docket_events
        ORDER BY event_date_iso
    """).fetchall()
    return [dict(r) for r in rows]

def get_evidence_for_argument(conn, keywords):
    """Get evidence quotes matching argument keywords."""
    cols = verify_table(conn, 'evidence_quotes')
    if not cols:
        return []
    clauses = []
    params = []
    for kw in keywords:
        clauses.append("LOWER(quote_text) LIKE ?")
        params.append(f"%{kw}%")
    where = " OR ".join(clauses)
    rows = conn.execute(f"""
        SELECT id, document_id, page_number, evidence_category,
               quote_text, speaker, date_ref, legal_significance, source_type
        FROM evidence_quotes
        WHERE {where}
        ORDER BY id
        LIMIT 200
    """, params).fetchall()
    return [dict(r) for r in rows]

def filter_violations_for_arg(all_violations, violation_keywords):
    """Filter judicial violations relevant to a specific argument."""
    results = []
    for v in all_violations:
        desc = s(v.get('violation_description', ''))
        canon = s(v.get('canon_number', ''))
        if any(kw in desc or kw in canon for kw in violation_keywords):
            results.append(v)
    return results

def filter_authorities_for_arg(all_chains, keywords):
    """Filter authority chains relevant to a specific argument."""
    results = []
    for ac in all_chains:
        text = s(ac.get('fact_claim', '')) + ' ' + s(ac.get('authority_cite', '')) + ' ' + s(ac.get('elements', ''))
        if any(kw in text for kw in keywords):
            results.append(ac)
    return results

def build_irac_argument(arg_def, violations, authorities, evidence, procedural_events):
    """Build IRAC-format argument structure."""
    # Filter for this argument
    arg_violations = filter_violations_for_arg(violations, arg_def['violation_keywords'])
    arg_authorities = filter_authorities_for_arg(authorities, arg_def['keywords'])

    # Count severities from DB
    severity_counts = {}
    for v in arg_violations:
        sev = v.get('severity', 'unknown')
        severity_counts[sev] = severity_counts.get(sev, 0) + 1

    # Build IRAC
    irac = {
        'id': arg_def['id'],
        'title': arg_def['title'],
        'issue': arg_def['issue'],
        'standard_of_review': arg_def['standard_of_review'],
        'rule': {
            'authorities': arg_def['authorities'],
            'db_authority_chains': [
                {
                    'cite': ac.get('authority_cite', 'N/A'),
                    'fact_claim': ((ac.get('fact_claim', '') or '')[:200]).replace('\n', ' '),
                    'chain_complete': bool(ac.get('chain_complete')),
                    'gap': ac.get('gap_description', None),
                }
                for ac in arg_authorities
            ],
        },
        'application': {
            'violation_count': len(arg_violations),
            'severity_breakdown': severity_counts,
            'key_violations': [
                {
                    'id': v.get('violation_id', 'N/A'),
                    'canon': v.get('canon_number', 'N/A'),
                    'severity': v.get('severity', 'N/A'),
                    'description': ((v.get('violation_description', '') or '')[:250]).replace('\n', ' '),
                    'evidence_refs': v.get('evidence_refs', 'N/A'),
                }
                for v in arg_violations[:10]
            ],
            'supporting_evidence': [
                {
                    'ref': f"EQ-{ev.get('id', '?')}",
                    'document_id': ev.get('document_id', 'N/A'),
                    'page': ev.get('page_number', 'N/A'),
                    'snippet': ((ev.get('quote_text', '') or '')[:200]).replace('\n', ' '),
                    'source': ev.get('source_type', 'N/A'),
                }
                for ev in evidence[:15]
            ],
            'procedural_events': [
                {
                    'date': pe.get('event_date_iso', 'N/A'),
                    'title': pe.get('title', 'N/A'),
                    'type': pe.get('event_type', 'N/A'),
                }
                for pe in procedural_events
                if any(kw in s(pe.get('title', '')) or kw in s(pe.get('summary', ''))
                       for kw in arg_def['keywords'][:5])
            ][:10],
        },
        'conclusion': f"The trial court's actions constitute reversible error requiring vacatur and remand. "
                      f"DB evidence: {len(arg_violations)} judicial violations found "
                      f"(query: judicial_violations WHERE judge_name LIKE '%mcneill%' filtered by [{', '.join(arg_def['violation_keywords'][:3])}...]), "
                      f"{len(evidence)} supporting evidence quotes "
                      f"(query: evidence_quotes WHERE quote_text LIKE '%keyword%'), "
                      f"{len(arg_authorities)} authority chains "
                      f"(query: authority_chains filtered by argument keywords).",
    }
    return irac

def generate_md(arguments, total_violations, total_authorities, total_events, total_evidence):
    """Generate Markdown report in IRAC format."""
    ts = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    lines = [
        f"# Appeal Argument Generator — Tool #243",
        f"",
        f"**Case:** COA 366810 (Pigors v Watson)",
        f"**Court:** Michigan Court of Appeals",
        f"**Generated:** {ts}",
        f"**Database:** litigation_context.db",
        f"",
        f"---",
        f"",
        f"## Data Sources",
        f"",
        f"| Table | Query | Results |",
        f"|-------|-------|---------|",
        f"| judicial_violations | WHERE judge_name LIKE '%mcneill%' | {total_violations} |",
        f"| authority_chains | SELECT * (all chains) | {total_authorities} |",
        f"| docket_events | SELECT * ORDER BY event_date_iso | {total_events} |",
        f"| evidence_quotes | LIKE search per argument keywords | {total_evidence} per argument (capped at 200) |",
        f"",
        f"---",
        f"",
    ]

    for arg in arguments:
        lines.append(f"# {arg['id']}: {arg['title']}")
        lines.append(f"")

        # ISSUE
        lines.append(f"## Issue")
        lines.append(f"")
        lines.append(f"{arg['issue']}")
        lines.append(f"")

        # STANDARD OF REVIEW
        lines.append(f"## Standard of Review")
        lines.append(f"")
        lines.append(f"{arg['standard_of_review']}")
        lines.append(f"")

        # RULE
        lines.append(f"## Rule")
        lines.append(f"")
        lines.append(f"### Controlling Authorities")
        lines.append(f"")
        for i, auth in enumerate(arg['rule']['authorities'], 1):
            lines.append(f"{i}. {auth}")
        lines.append(f"")
        if arg['rule']['db_authority_chains']:
            lines.append(f"### Authority Chains from Database ({len(arg['rule']['db_authority_chains'])} chains)")
            lines.append(f"")
            for ac in arg['rule']['db_authority_chains']:
                complete = "COMPLETE" if ac['chain_complete'] else "INCOMPLETE"
                lines.append(f"- **{ac['cite']}** [{complete}]: {ac['fact_claim'][:150]}")
                if ac.get('gap'):
                    lines.append(f"  - *Gap:* {ac['gap']}")
            lines.append(f"")

        # APPLICATION
        lines.append(f"## Application")
        lines.append(f"")
        lines.append(f"**Judicial violations found:** {arg['application']['violation_count']} "
                     f"(severity: {arg['application']['severity_breakdown']})")
        lines.append(f"")

        if arg['application']['key_violations']:
            lines.append(f"### Key Violations")
            lines.append(f"")
            for v in arg['application']['key_violations'][:7]:
                lines.append(f"**{v['id']}** — {v['canon']} [{v['severity'].upper()}]")
                lines.append(f"")
                lines.append(f"> {v['description'][:300]}")
                lines.append(f"")
                lines.append(f"*Evidence:* {v['evidence_refs']}")
                lines.append(f"")

        if arg['application']['supporting_evidence']:
            lines.append(f"### Supporting Evidence ({len(arg['application']['supporting_evidence'])} items)")
            lines.append(f"")
            lines.append(f"| Ref | Doc ID | Page | Source | Snippet |")
            lines.append(f"|-----|--------|------|--------|---------|")
            for ev in arg['application']['supporting_evidence'][:10]:
                snippet = ev['snippet'][:80].replace('|', '/')
                lines.append(f"| {ev['ref']} | {ev['document_id']} | {ev['page']} | {ev['source']} | {snippet} |")
            lines.append(f"")

        if arg['application']['procedural_events']:
            lines.append(f"### Relevant Procedural Events")
            lines.append(f"")
            for pe in arg['application']['procedural_events']:
                lines.append(f"- **{pe['date']}** — {pe['title']} ({pe['type']})")
            lines.append(f"")

        # CONCLUSION
        lines.append(f"## Conclusion")
        lines.append(f"")
        lines.append(f"{arg['conclusion']}")
        lines.append(f"")
        lines.append(f"---")
        lines.append(f"")

    lines.append("## Traceable Queries")
    lines.append("")
    lines.append("```sql")
    lines.append("-- Violations: SELECT * FROM judicial_violations WHERE LOWER(judge_name) LIKE '%mcneill%' ORDER BY severity DESC")
    lines.append("-- Authorities: SELECT * FROM authority_chains ORDER BY id")
    lines.append("-- Procedural: SELECT * FROM docket_events ORDER BY event_date_iso")
    lines.append("-- Evidence: SELECT * FROM evidence_quotes WHERE LOWER(quote_text) LIKE '%keyword%' LIMIT 200")
    lines.append("```")
    return "\n".join(lines)

def main():
    print("=" * 70)
    print("  TOOL #243: Appeal Argument Generator (COA 366810)")
    print("=" * 70)
    if not os.path.exists(DB_PATH):
        print(f"ERROR: Database not found at {DB_PATH}")
        sys.exit(1)
    print(f"  DB: {DB_PATH}")
    conn = get_connection()
    try:
        print("  [1/4] Loading authority chains...")
        all_authorities = get_authority_chains(conn)
        print(f"         Found {len(all_authorities)} authority chains")

        print("  [2/4] Loading judicial violations (McNeill)...")
        all_violations = get_judicial_violations(conn)
        print(f"         Found {len(all_violations)} McNeill violations")

        print("  [3/4] Loading procedural history...")
        all_events = get_procedural_history(conn)
        print(f"         Found {len(all_events)} docket events")

        arguments = []
        total_evidence = 0
        for arg_def in APPELLATE_ARGUMENTS:
            print(f"  [4/4] Building {arg_def['id']}: {arg_def['title']}...")
            evidence = get_evidence_for_argument(conn, arg_def['keywords'])
            total_evidence += len(evidence)
            print(f"         Found {len(evidence)} evidence quotes for this argument")
            irac = build_irac_argument(arg_def, all_violations, all_authorities, evidence, all_events)
            arguments.append(irac)

        # Write JSON
        json_path = os.path.join(REPORTS_DIR, 'appeal_argument_generator.json')
        report_data = {
            'tool': 'Tool #243: Appeal Argument Generator',
            'case': 'COA 366810 — Pigors v Watson',
            'court': 'Michigan Court of Appeals',
            'generated': datetime.now().isoformat(),
            'data_sources': {
                'authority_chains': len(all_authorities),
                'judicial_violations_mcneill': len(all_violations),
                'docket_events': len(all_events),
                'evidence_quotes_total': total_evidence,
            },
            'arguments': arguments,
        }
        with open(json_path, 'w', encoding='utf-8') as f:
            json.dump(report_data, f, indent=2, ensure_ascii=False, default=str)
        print(f"\n  JSON: {json_path}")

        # Write MD
        md_path = os.path.join(REPORTS_DIR, 'APPEAL_ARGUMENT_GENERATOR.md')
        md_content = generate_md(arguments, len(all_violations), len(all_authorities),
                                 len(all_events), total_evidence)
        with open(md_path, 'w', encoding='utf-8') as f:
            f.write(md_content)
        print(f"  MD:   {md_path}")

        print()
        print("  === KEY FINDINGS ===")
        for arg in arguments:
            v_count = arg['application']['violation_count']
            e_count = len(arg['application']['supporting_evidence'])
            p_count = len(arg['application']['procedural_events'])
            sev = arg['application']['severity_breakdown']
            print(f"  {arg['id']} ({arg['title']}):")
            print(f"    Violations: {v_count} | Evidence: {e_count} | Procedural events: {p_count}")
            print(f"    Severity: {sev}")
        print()
        print("  DONE.")
    finally:
        conn.close()

if __name__ == '__main__':
    main()
