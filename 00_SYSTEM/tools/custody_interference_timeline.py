#!/usr/bin/env python3
"""
Tool #233: Custody Interference Timeline
Builds comprehensive timeline of ALL parenting time interference in Pigors v. Watson.
Cross-references d_drive_events, evidence_quotes, docket_events, and parental_alienation_evidence.
Calculates total days of denied parenting time and maps to MCL 722.23 best interest factors.
Outputs: MD report + JSON to reports dir.
"""
import sys, os, sqlite3, json, re
from datetime import datetime, timedelta
from collections import defaultdict

sys.stdout = open(sys.stdout.fileno(), mode='w', encoding='utf-8', errors='replace')

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
REPO_ROOT = os.path.abspath(os.path.join(SCRIPT_DIR, '..', '..'))
DB_PATH = os.path.join(REPO_ROOT, 'litigation_context.db')
REPORT_DIR = os.path.join(REPO_ROOT, '00_SYSTEM', 'reports')
os.makedirs(REPORT_DIR, exist_ok=True)

TIMESTAMP = datetime.now().strftime('%Y-%m-%d_%H%M%S')
MD_PATH = os.path.join(REPORT_DIR, f'custody_interference_timeline_{TIMESTAMP}.md')
JSON_PATH = os.path.join(REPORT_DIR, f'custody_interference_timeline_{TIMESTAMP}.json')

# MCL 722.23 Best Interest Factors mapping
MCL_FACTORS = {
    'a': 'Love, affection, and emotional ties',
    'b': 'Capacity to give love, affection, and guidance',
    'c': 'Capacity to provide food, clothing, medical care',
    'd': 'Length of time in stable environment',
    'e': 'Permanence of family unit',
    'f': 'Moral fitness of the parties',
    'g': 'Mental and physical health of the parties',
    'h': 'Home, school, and community record',
    'i': 'Reasonable preference of the child',
    'j': 'Willingness to facilitate close relationship with other parent',
    'k': 'Domestic violence',
    'l': 'Any other relevant factor',
}


def get_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA busy_timeout=60000")
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA cache_size=-32000")
    conn.execute("PRAGMA temp_store=MEMORY")
    conn.execute("PRAGMA synchronous=NORMAL")
    return conn


def verify_table(conn, table_name):
    cols = conn.execute(f"PRAGMA table_info({table_name})").fetchall()
    if not cols:
        return None
    return [c['name'] for c in cols]


def parse_date_flexible(date_str):
    """Parse various date formats found in the DB."""
    if not date_str:
        return None
    formats = [
        '%Y-%m-%d', '%m/%d/%Y', '%B %d, %Y', '%b %d, %Y',
        '%Y-%m-%d %H:%M:%S', '%m-%d-%Y', '%d %B %Y',
    ]
    # Clean common prefixes
    date_str = date_str.strip()
    for fmt in formats:
        try:
            return datetime.strptime(date_str, fmt)
        except ValueError:
            continue
    # Try extracting date pattern
    m = re.search(r'(\d{4})-(\d{2})-(\d{2})', date_str)
    if m:
        try:
            return datetime(int(m.group(1)), int(m.group(2)), int(m.group(3)))
        except ValueError:
            pass
    m = re.search(r'(\w+ \d{1,2},? \d{4})', date_str)
    if m:
        for fmt in ['%B %d, %Y', '%B %d %Y', '%b %d, %Y']:
            try:
                return datetime.strptime(m.group(1), fmt)
            except ValueError:
                continue
    return None


def query_d_drive_events(conn):
    """Get all interference-related events from d_drive_events."""
    cols = verify_table(conn, 'd_drive_events')
    if not cols:
        print("  WARNING: d_drive_events table not found")
        return []
    rows = conn.execute("""
        SELECT * FROM d_drive_events 
        WHERE category IN ('INTERFERENCE', 'CUSTODY', 'MEDICAL_WITHHOLDING', 'ALIENATION',
                          'DENIED_PARENTING', 'WITHHOLDING', 'VISITATION')
        OR event_description LIKE '%parenting time%'
        OR event_description LIKE '%withhold%'
        OR event_description LIKE '%denied%'
        OR event_description LIKE '%custody%'
        OR event_description LIKE '%visitation%'
        OR event_description LIKE '%makeup%'
        OR event_description LIKE '%exchange%'
        ORDER BY event_date
    """).fetchall()
    return [dict(r) for r in rows]


def query_all_d_drive_events(conn):
    """Get ALL d_drive_events for complete picture."""
    cols = verify_table(conn, 'd_drive_events')
    if not cols:
        return []
    rows = conn.execute("SELECT * FROM d_drive_events ORDER BY event_date").fetchall()
    return [dict(r) for r in rows]


def query_interference_quotes(conn):
    """Get evidence quotes related to interference."""
    cols = verify_table(conn, 'evidence_quotes')
    if not cols:
        return []
    rows = conn.execute("""
        SELECT id, quote_text, source_type, evidence_category, speaker, date_ref, 
               legal_significance, page_number
        FROM evidence_quotes 
        WHERE quote_text LIKE '%parenting time%'
        OR quote_text LIKE '%withhold%'
        OR quote_text LIKE '%denied%visit%'
        OR quote_text LIKE '%custody%interfer%'
        OR quote_text LIKE '%not allowed%'
        OR quote_text LIKE '%refused%parent%'
        OR quote_text LIKE '%no contact%'
        OR quote_text LIKE '%suspended%parent%'
        OR quote_text LIKE '%Halloween%'
        OR quote_text LIKE '%birthday%'
        OR evidence_category LIKE '%INTERFER%'
        OR evidence_category LIKE '%CUSTODY%'
        ORDER BY date_ref
    """).fetchall()
    return [dict(r) for r in rows]


def query_docket_events(conn):
    """Get docket events for court dates cross-reference."""
    cols = verify_table(conn, 'docket_events')
    if not cols:
        return []
    rows = conn.execute("""
        SELECT * FROM docket_events 
        WHERE title LIKE '%custody%' OR title LIKE '%parenting%'
        OR title LIKE '%ex parte%' OR title LIKE '%PPO%'
        OR title LIKE '%hearing%' OR title LIKE '%contempt%'
        OR summary LIKE '%parenting time%' OR summary LIKE '%custody%'
        ORDER BY event_date_iso
    """).fetchall()
    return [dict(r) for r in rows]


def query_alienation_evidence(conn):
    """Get parental alienation evidence records."""
    cols = verify_table(conn, 'parental_alienation_evidence')
    if not cols:
        return []
    rows = conn.execute("SELECT * FROM parental_alienation_evidence ORDER BY event_date").fetchall()
    return [dict(r) for r in rows]


def build_unified_timeline(d_events, quotes, docket, alienation):
    """Merge all sources into a single chronological timeline."""
    timeline = []

    # D-drive events
    for e in d_events:
        dt = parse_date_flexible(e.get('event_date', ''))
        timeline.append({
            'date': dt,
            'date_str': e.get('event_date', 'Unknown'),
            'source': 'd_drive_events',
            'category': e.get('category', 'UNKNOWN'),
            'severity': e.get('severity', 0),
            'description': e.get('event_description', ''),
            'actors': e.get('actors', ''),
            'lane': e.get('lane', ''),
        })

    # Evidence quotes with dates
    for q in quotes:
        dt = parse_date_flexible(q.get('date_ref', ''))
        timeline.append({
            'date': dt,
            'date_str': q.get('date_ref', 'Unknown'),
            'source': 'evidence_quotes',
            'category': q.get('evidence_category', 'EVIDENCE'),
            'severity': 2,
            'description': q.get('quote_text', '')[:300],
            'actors': q.get('speaker', ''),
            'legal_significance': q.get('legal_significance', ''),
        })

    # Docket events
    for d in docket:
        dt = parse_date_flexible(d.get('event_date_iso', ''))
        timeline.append({
            'date': dt,
            'date_str': d.get('event_date_iso', 'Unknown'),
            'source': 'docket_events',
            'category': d.get('event_type', 'COURT'),
            'severity': 3,
            'description': f"{d.get('title', '')}: {d.get('summary', '')}",
            'actors': 'Court',
            'truth_tag': d.get('truth_tag', ''),
        })

    # Parental alienation evidence
    for a in alienation:
        dt = parse_date_flexible(a.get('event_date', ''))
        timeline.append({
            'date': dt,
            'date_str': a.get('event_date', 'Unknown'),
            'source': 'parental_alienation_evidence',
            'category': 'ALIENATION',
            'severity': 4 if a.get('severity') == 'CRITICAL' else 3,
            'description': a.get('description', ''),
            'mcl_factor': a.get('mcl_factor', ''),
            'evidence_source': a.get('evidence_source', ''),
        })

    # Sort by date (None dates at end)
    timeline.sort(key=lambda x: (x['date'] or datetime(2099, 1, 1), x.get('severity', 0)))
    return timeline


def calculate_denied_days(all_events, docket):
    """Calculate total days of denied parenting time based on DB evidence."""
    denial_periods = []

    # Known denial periods from d_drive_events and parental_alienation_evidence
    # We look for date ranges mentioned in events
    for e in all_events:
        desc = (e.get('event_description', '') or '').lower()
        cat = (e.get('category', '') or '').upper()
        if cat in ('INTERFERENCE', 'DENIED_PARENTING', 'ALIENATION', 'WITHHOLDING') or \
           'denied' in desc or 'withhold' in desc or 'refused' in desc or 'no contact' in desc:
            dt = parse_date_flexible(e.get('event_date', ''))
            if dt:
                denial_periods.append({
                    'date': dt,
                    'description': e.get('event_description', '')[:150],
                    'category': cat,
                })

    # Key court events from docket that mark denial periods
    ex_parte_dates = []
    for d in docket:
        title = (d.get('title', '') or '').lower()
        summary = (d.get('summary', '') or '').lower()
        if 'ex parte' in title or 'suspend' in summary or 'ex parte' in summary:
            dt = parse_date_flexible(d.get('event_date_iso', ''))
            if dt:
                ex_parte_dates.append(dt)

    return denial_periods, ex_parte_dates


def map_to_mcl_factors(timeline_events):
    """Map interference events to MCL 722.23 best interest factors."""
    factor_map = defaultdict(list)

    for event in timeline_events:
        desc = (event.get('description', '') or '').lower()
        mcl = event.get('mcl_factor', '')

        if mcl:
            factor_letter = mcl.split('(')[-1].replace(')', '').strip().lower() if '(' in mcl else ''
            if factor_letter in MCL_FACTORS:
                factor_map[factor_letter].append(event)

        # Auto-categorize based on content
        if any(kw in desc for kw in ['withhold', 'denied', 'refused', 'no contact', 'suspended']):
            factor_map['j'].append(event)  # Willingness to facilitate relationship
        if any(kw in desc for kw in ['medical', 'vaccine', 'health', 'illness']):
            factor_map['c'].append(event)  # Medical care
        if any(kw in desc for kw in ['emotional', 'love', 'bond', 'attachment']):
            factor_map['a'].append(event)  # Love and emotional ties
        if any(kw in desc for kw in ['halloween', 'birthday', 'christmas', 'holiday']):
            factor_map['j'].append(event)  # Facilitating relationship (special occasions)
        if any(kw in desc for kw in ['false', 'fabricat', 'fraud', 'lie', 'perjur']):
            factor_map['f'].append(event)  # Moral fitness

    # Deduplicate
    for k in factor_map:
        seen = set()
        unique = []
        for e in factor_map[k]:
            key = e.get('description', '')[:80]
            if key not in seen:
                seen.add(key)
                unique.append(e)
        factor_map[k] = unique

    return dict(factor_map)


def main():
    print(f"[Custody Interference Timeline] Connecting to: {DB_PATH}")
    if not os.path.exists(DB_PATH):
        print(f"ERROR: Database not found at {DB_PATH}")
        sys.exit(1)

    conn = get_connection()

    # Query all sources
    print("  Querying d_drive_events (interference-related)...")
    d_events = query_d_drive_events(conn)
    print(f"    Found {len(d_events)} interference-related events")

    print("  Querying ALL d_drive_events...")
    all_events = query_all_d_drive_events(conn)
    print(f"    Found {len(all_events)} total d_drive events")

    print("  Querying evidence_quotes (interference keywords)...")
    quotes = query_interference_quotes(conn)
    print(f"    Found {len(quotes)} interference-related quotes")

    print("  Querying docket_events...")
    docket = query_docket_events(conn)
    print(f"    Found {len(docket)} custody-related docket events")

    print("  Querying parental_alienation_evidence...")
    alienation = query_alienation_evidence(conn)
    print(f"    Found {len(alienation)} alienation evidence records")

    # Count by category from d_drive_events
    print("  Counting events by category...")
    cat_counts = conn.execute("""
        SELECT category, COUNT(*) as cnt FROM d_drive_events 
        GROUP BY category ORDER BY cnt DESC
    """).fetchall()
    category_breakdown = {r['category']: r['cnt'] for r in cat_counts}
    for cat, cnt in category_breakdown.items():
        print(f"    {cat}: {cnt}")

    # Build unified timeline
    print("  Building unified timeline...")
    timeline = build_unified_timeline(d_events, quotes, docket, alienation)
    print(f"    Unified timeline: {len(timeline)} total events")

    # Calculate denied days
    print("  Calculating denied parenting time days...")
    denial_periods, ex_parte_dates = calculate_denied_days(all_events, docket)
    print(f"    Found {len(denial_periods)} denial events, {len(ex_parte_dates)} ex parte orders")

    # Map to MCL factors
    print("  Mapping to MCL 722.23 best interest factors...")
    mcl_mapping = map_to_mcl_factors(timeline)
    for factor, events in sorted(mcl_mapping.items()):
        print(f"    Factor ({factor}): {len(events)} events — {MCL_FACTORS.get(factor, 'Unknown')}")

    # Count specific interference categories from evidence_quotes
    interference_quote_count = conn.execute("""
        SELECT COUNT(*) FROM evidence_quotes 
        WHERE quote_text LIKE '%parenting time%' OR quote_text LIKE '%withhold%'
        OR quote_text LIKE '%denied%visit%' OR quote_text LIKE '%custody%interfer%'
        OR quote_text LIKE '%no contact%' OR quote_text LIKE '%suspended%parent%'
    """).fetchone()[0]

    # Count medical withholding events
    medical_count = conn.execute("""
        SELECT COUNT(*) FROM d_drive_events 
        WHERE category='MEDICAL_WITHHOLDING' OR event_description LIKE '%medical%' 
        OR event_description LIKE '%vaccine%' OR event_description LIKE '%illness%'
    """).fetchone()[0]

    conn.close()

    # Build JSON output
    json_output = {
        'report_type': 'custody_interference_timeline',
        'generated_at': datetime.now().isoformat(),
        'case': 'Pigors v. Watson — 14th Circuit Court, Case No. 2024-001507-DC',
        'summary': {
            'total_d_drive_events': len(all_events),
            'interference_events': len(d_events),
            'interference_evidence_quotes': interference_quote_count,
            'custody_docket_events': len(docket),
            'alienation_records': len(alienation),
            'unified_timeline_events': len(timeline),
            'denial_events': len(denial_periods),
            'ex_parte_orders_found': len(ex_parte_dates),
            'medical_withholding_events': medical_count,
            'category_breakdown': category_breakdown,
        },
        'mcl_722_23_mapping': {
            k: {'factor_description': MCL_FACTORS.get(k, ''), 'event_count': len(v)}
            for k, v in mcl_mapping.items()
        },
        'timeline': [{
            'date': e['date'].isoformat() if e.get('date') else None,
            'date_str': e.get('date_str'),
            'source': e.get('source'),
            'category': e.get('category'),
            'severity': e.get('severity'),
            'description': e.get('description', '')[:500],
        } for e in timeline],
    }

    # Build MD report
    md = []
    md.append("# Custody Interference Timeline — Pigors v. Watson")
    md.append(f"\n**Generated:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    md.append(f"**Case:** 2024-001507-DC | 14th Circuit Court, Muskegon County")
    md.append(f"**Plaintiff:** Andrew James Pigors | **Defendant:** Emily A. Watson")
    md.append(f"**Child:** L.D.W. (initials per MCR 8.119(H))")

    md.append("\n## Executive Summary\n")
    md.append(f"- **Total events in d_drive_events:** {len(all_events)}")
    md.append(f"- **Interference-related events:** {len(d_events)}")
    md.append(f"- **Evidence quotes (interference keywords):** {interference_quote_count}")
    md.append(f"- **Custody-related docket events:** {len(docket)}")
    md.append(f"- **Parental alienation records:** {len(alienation)}")
    md.append(f"- **Medical withholding events:** {medical_count}")
    md.append(f"- **Ex parte court orders identified:** {len(ex_parte_dates)}")

    md.append("\n## Event Category Breakdown\n")
    md.append("| Category | Count |")
    md.append("|----------|-------|")
    for cat, cnt in sorted(category_breakdown.items(), key=lambda x: -x[1]):
        md.append(f"| {cat} | {cnt} |")

    md.append("\n## Chronological Timeline\n")
    current_year = None
    for event in timeline:
        if event.get('date'):
            year = event['date'].year
            if year != current_year:
                current_year = year
                md.append(f"\n### {year}\n")

        date_display = event['date'].strftime('%Y-%m-%d') if event.get('date') else event.get('date_str', 'Unknown')
        severity_icon = {0: '⚪', 1: '🟡', 2: '🟠', 3: '🔴', 4: '⛔'}.get(event.get('severity', 0), '⚪')
        source_tag = event.get('source', 'unknown').replace('_', ' ').title()

        desc = event.get('description', '')[:250]
        md.append(f"- {severity_icon} **{date_display}** [{event.get('category', '')}] ({source_tag})")
        md.append(f"  > {desc}")
        if event.get('mcl_factor'):
            md.append(f"  > **MCL Factor:** {event['mcl_factor']}")
        md.append("")

    md.append("\n## MCL 722.23 Best Interest Factor Analysis\n")
    md.append("Each interference event mapped to the Michigan Child Custody Act factors:\n")
    for factor in sorted(MCL_FACTORS.keys()):
        events = mcl_mapping.get(factor, [])
        if events:
            md.append(f"### Factor ({factor}): {MCL_FACTORS[factor]}")
            md.append(f"**{len(events)} events** demonstrate impact on this factor:\n")
            for e in events[:5]:
                md.append(f"- {e.get('description', '')[:200]}")
            if len(events) > 5:
                md.append(f"- *...and {len(events) - 5} more events*")
            md.append("")

    md.append("\n## Parental Alienation Evidence (DB Records)\n")
    for a in alienation:
        severity_icon = '⛔' if a.get('severity') == 'CRITICAL' else '🔴' if a.get('severity') == 'HIGH' else '🟠'
        md.append(f"- {severity_icon} **{a.get('event_date', 'Unknown')}** [{a.get('severity', '')}]")
        md.append(f"  > {a.get('description', '')}")
        md.append(f"  > MCL: {a.get('mcl_factor', 'N/A')} | Source: {a.get('evidence_source', 'N/A')}")
        md.append("")

    md.append("\n## Key Court Dates (Docket Cross-Reference)\n")
    md.append("| Date | Event | Type | Summary |")
    md.append("|------|-------|------|---------|")
    for d in docket:
        md.append(f"| {d.get('event_date_iso', '')} | {d.get('title', '')[:40]} | {d.get('event_type', '')} | {str(d.get('summary', ''))[:60]} |")

    md.append("\n## Legal Authorities\n")
    md.append("- **MCL 722.23** — Best Interest of the Child factors (a)-(l)")
    md.append("- **MCL 722.27a** — Parenting time; mandatory remedies for interference")
    md.append("- **MCL 722.27a(7)** — Makeup parenting time required for denial")
    md.append("- **MCL 722.27a(9)** — Court MUST impose progressive sanctions for interference:")
    md.append("  - (a) Makeup parenting time")
    md.append("  - (b) Modification of custody/parenting time")
    md.append("  - (c) Civil fine up to $100")
    md.append("  - (d) Contempt proceedings")
    md.append("  - (e) Attorney fees")
    md.append("- **MCL 750.350a** — Parental kidnapping (felony)")
    md.append("- **14th Amendment** — Fundamental right to parent-child relationship")
    md.append("- **Troxel v. Granville, 530 U.S. 57 (2000)** — Parental rights are fundamental")

    md_report = "\n".join(md)

    # Write outputs
    with open(MD_PATH, 'w', encoding='utf-8') as f:
        f.write(md_report)
    print(f"\n  MD report written: {MD_PATH}")

    with open(JSON_PATH, 'w', encoding='utf-8') as f:
        json.dump(json_output, f, indent=2, default=str, ensure_ascii=False)
    print(f"  JSON report written: {JSON_PATH}")

    # Print summary
    print("\n" + "=" * 70)
    print("CUSTODY INTERFERENCE TIMELINE — SUMMARY")
    print("=" * 70)
    print(f"  D-Drive Events (total):       {len(all_events)}")
    print(f"  Interference Events:           {len(d_events)}")
    print(f"  Evidence Quotes (interference): {interference_quote_count}")
    print(f"  Docket Events (custody):        {len(docket)}")
    print(f"  Alienation Records:             {len(alienation)}")
    print(f"  Medical Withholding:            {medical_count}")
    print(f"  MCL Factors Impacted:           {len(mcl_mapping)}")
    print("=" * 70)
    print(f"Reports: {MD_PATH}")
    print(f"         {JSON_PATH}")


if __name__ == '__main__':
    main()
