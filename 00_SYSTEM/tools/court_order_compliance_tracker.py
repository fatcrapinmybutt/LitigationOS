#!/usr/bin/env python3
"""Tool #241: Court Order Compliance Tracker.

Tracks compliance with ALL court orders by both parties (Andrew Pigors vs Emily Watson).
Queries docket_events for orders, evidence_quotes for compliance/violation evidence,
d_drive_events for timeline events. Scores each party's compliance rate.

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
    """Verify table exists and return column names."""
    cur = conn.execute(f"PRAGMA table_info({table_name})")
    cols = [row['name'] for row in cur.fetchall()]
    if not cols:
        print(f"  WARNING: Table '{table_name}' does not exist")
        return []
    return cols

def get_court_orders(conn):
    """Extract all court orders from docket_events."""
    cols = verify_table(conn, 'docket_events')
    if not cols:
        return []
    rows = conn.execute("""
        SELECT event_id, case_id, event_date_iso, title, event_type, summary, truth_tag
        FROM docket_events
        WHERE LOWER(event_type) IN ('order', 'ruling', 'judgment')
           OR LOWER(title) LIKE '%order%'
           OR LOWER(summary) LIKE '%order%'
           OR LOWER(summary) LIKE '%it is ordered%'
        ORDER BY event_date_iso
    """).fetchall()
    return [dict(r) for r in rows]

def get_compliance_evidence(conn):
    """Get evidence of compliance or non-compliance from evidence_quotes."""
    cols = verify_table(conn, 'evidence_quotes')
    if not cols:
        return []
    compliance_keywords = [
        '%comply%', '%compliance%', '%violat%', '%contempt%', '%disobey%',
        '%withhold%', '%refus%', '%ignor%', '%fail%to%', '%denied%access%',
        '%interfere%', '%obstruct%', '%parenting time%', '%visitation%',
        '%custody order%', '%court order%', '%non-compliance%'
    ]
    where_clauses = " OR ".join([f"LOWER(quote_text) LIKE ?" for _ in compliance_keywords])
    rows = conn.execute(f"""
        SELECT id, document_id, page_number, evidence_category,
               quote_text, speaker, date_ref, legal_significance, source_type
        FROM evidence_quotes
        WHERE {where_clauses}
        LIMIT 500
    """, compliance_keywords).fetchall()
    return [dict(r) for r in rows]

def get_timeline_events(conn):
    """Get d_drive_events related to compliance/interference."""
    cols = verify_table(conn, 'd_drive_events')
    if not cols:
        return []
    rows = conn.execute("""
        SELECT id, source_doc, event_date, event_description, actors, category, lane, severity
        FROM d_drive_events
        WHERE LOWER(category) IN ('interference', 'fraud', 'contempt', 'medical', 'alienation',
                                   'withholding', 'violation')
           OR LOWER(event_description) LIKE '%order%'
           OR LOWER(event_description) LIKE '%comply%'
           OR LOWER(event_description) LIKE '%violat%'
           OR LOWER(event_description) LIKE '%withhold%'
           OR LOWER(event_description) LIKE '%interfere%'
        ORDER BY event_date
    """).fetchall()
    return [dict(r) for r in rows]

def classify_party(text):
    """Determine which party is referenced in text."""
    t = s(text)
    andrew_signals = ['andrew', 'pigors', 'plaintiff', 'father', 'dad']
    emily_signals = ['emily', 'watson', 'defendant', 'mother', 'mom', 'tiffany']
    a_score = sum(1 for sig in andrew_signals if sig in t)
    e_score = sum(1 for sig in emily_signals if sig in t)
    if a_score > e_score:
        return 'Andrew Pigors'
    elif e_score > a_score:
        return 'Emily Watson'
    return 'Unknown'

def classify_compliance(text):
    """Classify whether text indicates compliance or non-compliance."""
    t = s(text)
    noncompliance_signals = [
        'violat', 'contempt', 'disobey', 'withhold', 'refus', 'ignor',
        'fail', 'denied', 'interfere', 'obstruct', 'non-compliance',
        'did not', 'would not', 'never', 'unilateral', 'without notice',
        'without consulting', 'suspended', 'ex parte'
    ]
    compliance_signals = [
        'compli', 'follow', 'adher', 'fulfil', 'satisfied', 'met the',
        'in accordance', 'pursuant to', 'timely', 'cooperat'
    ]
    nc_score = sum(1 for sig in noncompliance_signals if sig in t)
    c_score = sum(1 for sig in compliance_signals if sig in t)
    if nc_score > c_score:
        return 'NON-COMPLIANT'
    elif c_score > nc_score:
        return 'COMPLIANT'
    return 'INDETERMINATE'

def relevance_score(order_text, evidence_text):
    """Score how relevant an evidence item is to a specific order."""
    ot = s(order_text)
    et = s(evidence_text)
    shared_terms = ['parenting time', 'custody', 'visitation', 'protection order',
                    'ppo', 'ex parte', 'evaluation', 'hearing', 'mental health']
    score = 0
    for term in shared_terms:
        if term in ot and term in et:
            score += 2
    # Date overlap check
    import re
    order_dates = set(re.findall(r'\d{4}-\d{2}-\d{2}', ot))
    ev_dates = set(re.findall(r'\d{1,2}/\d{1,2}/\d{2,4}', et))
    if order_dates or ev_dates:
        score += 1
    return score

def classify_violator(text):
    """Determine who is the ACTOR committing the violation (not just mentioned)."""
    t = s(text)
    # Patterns where Emily/defendant is the actor of non-compliance
    emily_actor_patterns = [
        'emily withh', 'watson withh', 'defendant withh', 'mother withh',
        'emily refus', 'watson refus', 'defendant refus',
        'emily denied', 'watson denied', 'defendant denied',
        'emily fail', 'watson fail', 'defendant fail',
        'emily did not', 'watson did not', 'defendant did not',
        'emily ignor', 'watson ignor', 'defendant ignor',
        'emily interfere', 'watson interfere', 'defendant interfere',
        'emily unilateral', 'watson unilateral', 'defendant unilateral',
        'defendant requested, and the court signed an ex parte',
        'without consulting me, emily', 'emily delayed notif',
        'emily made unilateral', 'emily alleged',
    ]
    andrew_actor_patterns = [
        'andrew withh', 'pigors withh', 'plaintiff withh',
        'andrew refus', 'pigors refus', 'plaintiff refus',
        'andrew fail', 'pigors fail', 'plaintiff fail',
        'andrew violat', 'pigors violat', 'plaintiff violat',
    ]
    emily_score = sum(1 for p in emily_actor_patterns if p in t)
    andrew_score = sum(1 for p in andrew_actor_patterns if p in t)
    if emily_score > andrew_score:
        return 'Emily Watson'
    elif andrew_score > emily_score:
        return 'Andrew Pigors'
    return None

def build_compliance_matrix(orders, evidence, timeline):
    """Build compliance matrix tracking each order and party compliance."""
    matrix = []
    # Pre-classify timeline events by actor for faster lookup
    emily_timeline = [e for e in timeline if 'emily' in s(e.get('actors', ''))]
    andrew_timeline = [e for e in timeline if 'andrew' in s(e.get('actors', ''))]

    for order in orders:
        entry = {
            'order_id': order.get('event_id', 'N/A'),
            'case_id': order.get('case_id', 'N/A'),
            'date': order.get('event_date_iso', 'N/A'),
            'title': order.get('title', 'N/A'),
            'summary': (order.get('summary', '') or '')[:200],
            'andrew_compliance': 'NO EVIDENCE OF VIOLATION',
            'emily_compliance': 'NO EVIDENCE OF VIOLATION',
            'andrew_evidence': [],
            'emily_evidence': []
        }
        order_text = (order.get('title', '') or '') + ' ' + (order.get('summary', '') or '')

        # Check evidence quotes — only attach if relevant to this order
        for ev in evidence:
            qt = ev.get('quote_text', '') or ''
            if relevance_score(order_text, qt) < 2:
                continue
            violator = classify_violator(qt)
            if not violator:
                continue
            status = classify_compliance(qt)
            snippet = qt[:150].replace('\n', ' ')
            ref = f"EQ-{ev.get('id', '?')} (p.{ev.get('page_number', '?')})"
            if violator == 'Emily Watson' and status == 'NON-COMPLIANT':
                entry['emily_evidence'].append({'ref': ref, 'status': status, 'snippet': snippet})
                entry['emily_compliance'] = 'NON-COMPLIANT'
            elif violator == 'Andrew Pigors' and status == 'NON-COMPLIANT':
                entry['andrew_evidence'].append({'ref': ref, 'status': status, 'snippet': snippet})
                entry['andrew_compliance'] = 'NON-COMPLIANT'

        # Check timeline — Emily incidents
        for ev in emily_timeline:
            desc = ev.get('event_description', '') or ''
            if relevance_score(order_text, desc) < 1:
                continue
            status = classify_compliance(desc)
            snippet = desc[:150].replace('\n', ' ')
            ref = f"DDE-{ev.get('id', '?')}"
            entry['emily_evidence'].append({'ref': ref, 'status': status, 'snippet': snippet})
            if status == 'NON-COMPLIANT':
                entry['emily_compliance'] = 'NON-COMPLIANT'

        # Check timeline — Andrew incidents (if any)
        for ev in andrew_timeline:
            desc = ev.get('event_description', '') or ''
            if relevance_score(order_text, desc) < 1:
                continue
            status = classify_compliance(desc)
            snippet = desc[:150].replace('\n', ' ')
            ref = f"DDE-{ev.get('id', '?')}"
            entry['andrew_evidence'].append({'ref': ref, 'status': status, 'snippet': snippet})
            if status == 'NON-COMPLIANT':
                entry['andrew_compliance'] = 'NON-COMPLIANT'

        matrix.append(entry)
    return matrix

def compute_scores(matrix, timeline):
    """Compute compliance scores per party from the compliance matrix and timeline."""
    andrew_stats = {'compliant': 0, 'non_compliant': 0, 'indeterminate': 0}
    emily_stats = {'compliant': 0, 'non_compliant': 0, 'indeterminate': 0}
    for entry in matrix:
        if entry['andrew_compliance'] == 'NON-COMPLIANT':
            andrew_stats['non_compliant'] += 1
        elif entry['andrew_compliance'] == 'COMPLIANT':
            andrew_stats['compliant'] += 1
        else:
            andrew_stats['indeterminate'] += 1
        if entry['emily_compliance'] == 'NON-COMPLIANT':
            emily_stats['non_compliant'] += 1
        elif entry['emily_compliance'] == 'COMPLIANT':
            emily_stats['compliant'] += 1
        else:
            emily_stats['indeterminate'] += 1

    # Count d_drive_events by actor for supplementary scoring
    emily_incidents = sum(1 for e in timeline if 'emily' in s(e.get('actors', '')))
    andrew_incidents = sum(1 for e in timeline if 'andrew' in s(e.get('actors', '')))
    emily_categories = {}
    for e in timeline:
        if 'emily' in s(e.get('actors', '')):
            cat = (e.get('category', '') or 'UNKNOWN')
            emily_categories[cat] = emily_categories.get(cat, 0) + 1
    andrew_total = andrew_stats['compliant'] + andrew_stats['non_compliant'] + andrew_stats['indeterminate']
    emily_total = emily_stats['compliant'] + emily_stats['non_compliant'] + emily_stats['indeterminate']
    andrew_rate = ((andrew_total - andrew_stats['non_compliant']) / andrew_total * 100) if andrew_total > 0 else 0
    emily_rate = ((emily_total - emily_stats['non_compliant']) / emily_total * 100) if emily_total > 0 else 0
    return {
        'andrew': {
            **andrew_stats,
            'total_orders_evaluated': andrew_total,
            'compliance_rate_pct': round(andrew_rate, 1),
            'timeline_incidents': andrew_incidents
        },
        'emily': {
            **emily_stats,
            'total_orders_evaluated': emily_total,
            'compliance_rate_pct': round(emily_rate, 1),
            'timeline_incidents': emily_incidents,
            'incident_categories': emily_categories
        }
    }

def generate_md(matrix, scores, order_count, evidence_count, timeline_count):
    """Generate Markdown report."""
    ts = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    lines = [
        f"# Court Order Compliance Tracker — Tool #241",
        f"",
        f"**Generated:** {ts}",
        f"**Database:** litigation_context.db",
        f"**Court orders analyzed:** {order_count} (from docket_events WHERE event_type='order' or title/summary LIKE '%order%')",
        f"**Evidence quotes scanned:** {evidence_count} compliance-related (from evidence_quotes)",
        f"**Timeline events scanned:** {timeline_count} (from d_drive_events)",
        f"",
        f"---",
        f"",
        f"## Compliance Score Summary",
        f"",
        f"| Party | Orders Evaluated | Non-Compliant | Compliant/No Violation | Compliance Rate | Timeline Incidents |",
        f"|-------|-----------------|---------------|----------------------|-----------------|-------------------|",
        f"| **Andrew Pigors** | {scores['andrew']['total_orders_evaluated']} | {scores['andrew']['non_compliant']} | {scores['andrew']['compliant'] + scores['andrew']['indeterminate']} | **{scores['andrew']['compliance_rate_pct']}%** | {scores['andrew']['timeline_incidents']} |",
        f"| **Emily Watson** | {scores['emily']['total_orders_evaluated']} | {scores['emily']['non_compliant']} | {scores['emily']['compliant'] + scores['emily']['indeterminate']} | **{scores['emily']['compliance_rate_pct']}%** | {scores['emily']['timeline_incidents']} |",
        f"",
    ]
    if scores['emily'].get('incident_categories'):
        lines.append("### Emily Watson — Incident Categories (d_drive_events)")
        lines.append("")
        lines.append("| Category | Count |")
        lines.append("|----------|-------|")
        for cat, cnt in sorted(scores['emily']['incident_categories'].items(), key=lambda x: -x[1]):
            lines.append(f"| {cat} | {cnt} |")
        lines.append("")

    lines.append("---")
    lines.append("")
    lines.append("## Compliance Matrix — All Court Orders")
    lines.append("")
    for entry in matrix:
        lines.append(f"### {entry['date']} — {entry['title']}")
        lines.append(f"")
        lines.append(f"- **Order ID:** {entry['order_id']}")
        lines.append(f"- **Case:** {entry['case_id']}")
        lines.append(f"- **Summary:** {entry['summary']}")
        lines.append(f"- **Andrew Pigors:** {entry['andrew_compliance']}")
        lines.append(f"- **Emily Watson:** {entry['emily_compliance']}")
        if entry['emily_evidence']:
            lines.append(f"")
            lines.append(f"  **Emily evidence ({len(entry['emily_evidence'])} items):**")
            for ev in entry['emily_evidence'][:5]:
                lines.append(f"  - [{ev['status']}] {ev['ref']}: {ev['snippet'][:120]}...")
        if entry['andrew_evidence']:
            lines.append(f"")
            lines.append(f"  **Andrew evidence ({len(entry['andrew_evidence'])} items):**")
            for ev in entry['andrew_evidence'][:5]:
                lines.append(f"  - [{ev['status']}] {ev['ref']}: {ev['snippet'][:120]}...")
        lines.append(f"")

    lines.append("---")
    lines.append("")
    lines.append("## Traceable Queries")
    lines.append("")
    lines.append("```sql")
    lines.append("-- Orders: SELECT * FROM docket_events WHERE LOWER(event_type) IN ('order','ruling','judgment') OR LOWER(title) LIKE '%order%'")
    lines.append("-- Evidence: SELECT * FROM evidence_quotes WHERE LOWER(quote_text) LIKE '%comply%' OR '%violat%' ... (15 keywords)")
    lines.append("-- Timeline: SELECT * FROM d_drive_events WHERE category IN ('INTERFERENCE','FRAUD','CONTEMPT',...)")
    lines.append("```")
    return "\n".join(lines)

def main():
    print("=" * 70)
    print("  TOOL #241: Court Order Compliance Tracker")
    print("=" * 70)
    if not os.path.exists(DB_PATH):
        print(f"ERROR: Database not found at {DB_PATH}")
        sys.exit(1)
    print(f"  DB: {DB_PATH}")
    conn = get_connection()
    try:
        print("  [1/4] Extracting court orders from docket_events...")
        orders = get_court_orders(conn)
        print(f"         Found {len(orders)} court orders")

        print("  [2/4] Scanning evidence_quotes for compliance evidence...")
        evidence = get_compliance_evidence(conn)
        print(f"         Found {len(evidence)} compliance-related quotes")

        print("  [3/4] Scanning d_drive_events for timeline incidents...")
        timeline = get_timeline_events(conn)
        print(f"         Found {len(timeline)} timeline events")

        print("  [4/4] Building compliance matrix and scoring...")
        matrix = build_compliance_matrix(orders, evidence, timeline)
        scores = compute_scores(matrix, timeline)

        # Write JSON
        json_path = os.path.join(REPORTS_DIR, 'court_order_compliance_tracker.json')
        report_data = {
            'tool': 'Tool #241: Court Order Compliance Tracker',
            'generated': datetime.now().isoformat(),
            'db_queries': {
                'docket_events_orders': len(orders),
                'evidence_quotes_compliance': len(evidence),
                'd_drive_events_timeline': len(timeline)
            },
            'scores': scores,
            'matrix': matrix
        }
        with open(json_path, 'w', encoding='utf-8') as f:
            json.dump(report_data, f, indent=2, ensure_ascii=False, default=str)
        print(f"  JSON: {json_path}")

        # Write MD
        md_path = os.path.join(REPORTS_DIR, 'COURT_ORDER_COMPLIANCE_TRACKER.md')
        md_content = generate_md(matrix, scores, len(orders), len(evidence), len(timeline))
        with open(md_path, 'w', encoding='utf-8') as f:
            f.write(md_content)
        print(f"  MD:   {md_path}")

        print()
        print("  === KEY FINDINGS ===")
        print(f"  Andrew compliance rate: {scores['andrew']['compliance_rate_pct']}% ({scores['andrew']['non_compliant']} violations found)")
        print(f"  Emily compliance rate:  {scores['emily']['compliance_rate_pct']}% ({scores['emily']['non_compliant']} violations found)")
        print(f"  Emily timeline incidents: {scores['emily']['timeline_incidents']}")
        if scores['emily'].get('incident_categories'):
            print(f"  Emily incident breakdown: {dict(scores['emily']['incident_categories'])}")
        print()
        print("  DONE.")
    finally:
        conn.close()

if __name__ == '__main__':
    main()
