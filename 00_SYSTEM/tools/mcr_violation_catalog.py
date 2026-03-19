#!/usr/bin/env python3
"""
Tool #224: MCR Violation Catalog
Catalogs ALL Michigan Court Rule violations by Judge McNeill with citations.
Groups by MCR chapter, cross-references Canon violations, calculates frequency.

Output: MCR_VIOLATION_CATALOG.md + mcr_violation_catalog.json
"""
import sys
import os
import json
import re
import sqlite3
from datetime import datetime
from collections import defaultdict

sys.stdout = open(sys.stdout.fileno(), mode='w', encoding='utf-8', errors='replace')

# --- Path setup (never set CWD to repo root due to shadow modules) ---
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
REPO_ROOT = os.path.normpath(os.path.join(SCRIPT_DIR, '..', '..'))
DB_PATH = os.path.join(REPO_ROOT, 'litigation_context.db')
REPORTS_DIR = os.path.join(REPO_ROOT, '00_SYSTEM', 'reports')
os.makedirs(REPORTS_DIR, exist_ok=True)

# MCR chapter definitions for grouping
MCR_CHAPTERS = {
    '2.003': 'Disqualification of Judge',
    '2.107': 'Service and Filing of Pleadings',
    '2.119': 'Motion Practice',
    '2.517': 'Findings by the Court',
    '3.207': 'Domestic Relations — Mediation',
    '3.208': 'Domestic Relations — Friend of Court',
    '3.210': 'Domestic Relations — Child Custody',
    '3.211': 'Domestic Relations — Parenting Time',
    '7.211': 'Appeals — Motions',
    '7.212': 'Appeals — Briefs',
    '7.215': 'Appeals — Opinions and Orders',
    '2.003(C)': 'Disqualification — Standards',
    '2.003(D)': 'Disqualification — Procedure',
}


def connect_db():
    """Connect with mandatory PRAGMAs."""
    conn = sqlite3.connect(DB_PATH, timeout=120)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA busy_timeout=60000")
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA cache_size=-32000")
    conn.execute("PRAGMA temp_store=MEMORY")
    conn.execute("PRAGMA synchronous=NORMAL")
    return conn


def table_exists(conn, name):
    r = conn.execute(
        "SELECT COUNT(*) FROM sqlite_master WHERE type='table' AND name=?", (name,)
    ).fetchone()
    return r[0] > 0


def get_columns(conn, name):
    return [row[1] for row in conn.execute(f"PRAGMA table_info([{name}])").fetchall()]


def safe_query(conn, sql, params=()):
    try:
        return conn.execute(sql, params).fetchall()
    except Exception as e:
        print(f"  [WARN] Query failed: {e}")
        return []


def extract_mcr_rule(text):
    """Extract MCR rule number from text."""
    if not text:
        return []
    patterns = [
        r'MCR\s+(\d+\.\d+(?:\([A-Za-z0-9]+\))*)',
        r'MCR\s*(\d+\.\d+)',
    ]
    found = set()
    for pat in patterns:
        matches = re.findall(pat, str(text), re.IGNORECASE)
        found.update(matches)
    return list(found)


def extract_canon(text):
    """Extract Canon of Judicial Conduct references."""
    if not text:
        return []
    patterns = [
        r'Canon\s+(\d+[A-Z]?(?:\(\d+\))?)',
        r'Canon\s+(\d+)',
    ]
    found = set()
    for pat in patterns:
        matches = re.findall(pat, str(text), re.IGNORECASE)
        found.update(matches)
    return list(found)


def get_mcr_chapter(rule):
    """Extract the chapter from an MCR rule (e.g., '2.003(C)(1)' -> '2.003')."""
    match = re.match(r'(\d+\.\d+)', str(rule))
    return match.group(1) if match else str(rule)


def catalog_violations(conn):
    """Catalog all MCR violations from multiple tables."""
    all_violations = []

    # --- Source 1: judicial_violations (1127 rows) ---
    if table_exists(conn, 'judicial_violations'):
        cols = get_columns(conn, 'judicial_violations')
        print(f"  judicial_violations columns: {cols}")
        rows = safe_query(conn, """
            SELECT violation_id, judge_name, canon_number, violation_description,
                   evidence_refs, severity, jtc_exhibit_id, created_at
            FROM judicial_violations
            WHERE judge_name LIKE '%McNeill%'
        """)
        for r in rows:
            mcr_rules = extract_mcr_rule(r['canon_number']) + extract_mcr_rule(r['violation_description'])
            canons = extract_canon(r['canon_number']) + extract_canon(r['violation_description'])
            all_violations.append({
                'source_table': 'judicial_violations',
                'violation_id': r['violation_id'],
                'mcr_rules': list(set(mcr_rules)),
                'canons': list(set(canons)),
                'description': str(r['violation_description'])[:500] if r['violation_description'] else '',
                'severity': r['severity'],
                'evidence_source': str(r['evidence_refs'])[:300] if r['evidence_refs'] else '',
                'date': str(r['created_at'])[:10] if r['created_at'] else '',
                'jtc_exhibit': r['jtc_exhibit_id'],
            })
        print(f"  judicial_violations: {len(rows)} McNeill violations")

    # --- Source 2: forensic_judicial_analysis (3003 rows) ---
    if table_exists(conn, 'forensic_judicial_analysis'):
        cols = get_columns(conn, 'forensic_judicial_analysis')
        print(f"  forensic_judicial_analysis columns: {cols}")
        rows = safe_query(conn, """
            SELECT finding_id, category, severity, description, mcr_violations, date_iso
            FROM forensic_judicial_analysis
            WHERE mcr_violations IS NOT NULL AND mcr_violations != ''
        """)
        for r in rows:
            mcr_rules = extract_mcr_rule(r['mcr_violations'])
            canons = extract_canon(r['mcr_violations'])
            if mcr_rules or canons:
                all_violations.append({
                    'source_table': 'forensic_judicial_analysis',
                    'violation_id': r['finding_id'],
                    'mcr_rules': list(set(mcr_rules)),
                    'canons': list(set(canons)),
                    'description': str(r['description'])[:500] if r['description'] else '',
                    'severity': r['severity'],
                    'evidence_source': '',
                    'date': str(r['date_iso'])[:10] if r['date_iso'] else '',
                    'jtc_exhibit': None,
                })
        print(f"  forensic_judicial_analysis: {len(rows)} entries with MCR references")

    # --- Source 3: judicial_analysis_v13 (8348 rows) ---
    if table_exists(conn, 'judicial_analysis_v13'):
        cols = get_columns(conn, 'judicial_analysis_v13')
        print(f"  judicial_analysis_v13 columns: {cols}")
        rows = safe_query(conn, """
            SELECT id, analysis_type, finding, severity, category, mcr_rule,
                   mcl_statute, constitutional_provision, date_of_violation, actor
            FROM judicial_analysis_v13
            WHERE mcr_rule IS NOT NULL AND mcr_rule != ''
            AND (actor LIKE '%McNeill%' OR actor IS NULL)
        """)
        for r in rows:
            mcr_rules = extract_mcr_rule(r['mcr_rule'])
            all_violations.append({
                'source_table': 'judicial_analysis_v13',
                'violation_id': f"JA13-{r['id']}",
                'mcr_rules': list(set(mcr_rules)),
                'canons': [],
                'description': str(r['finding'])[:500] if r['finding'] else '',
                'severity': r['severity'],
                'evidence_source': r['category'] or '',
                'date': str(r['date_of_violation'])[:10] if r['date_of_violation'] else '',
                'jtc_exhibit': None,
            })
        print(f"  judicial_analysis_v13: {len(rows)} McNeill MCR violations")

    # --- Source 4: omega_violation_analysis (summary table) ---
    omega_summary = {}
    if table_exists(conn, 'omega_violation_analysis'):
        cols = get_columns(conn, 'omega_violation_analysis')
        print(f"  omega_violation_analysis columns: {cols}")
        rows = safe_query(conn, "SELECT * FROM omega_violation_analysis")
        for r in rows:
            omega_summary[r['category']] = {
                'count': r['count'],
                'percentage': r['percentage'],
                'severity_breakdown': r['severity_breakdown'],
            }
        print(f"  omega_violation_analysis: {len(rows)} categories")

    # --- Source 5: judicial_canons_matrix (18 rows) ---
    canons_matrix = {}
    if table_exists(conn, 'judicial_canons_matrix'):
        cols = get_columns(conn, 'judicial_canons_matrix')
        print(f"  judicial_canons_matrix columns: {cols}")
        rows = safe_query(conn, "SELECT * FROM judicial_canons_matrix")
        for r in rows:
            canons_matrix[r['canon']] = {
                'subsection': r['subsection'],
                'text': r['canon_text'],
                'violation_count': r['violation_count'],
                'examples': r['violation_examples'],
                'severity': r['severity'],
            }
        print(f"  judicial_canons_matrix: {len(rows)} canons loaded")

    # --- Source 6: violation_patterns ---
    violation_patterns = []
    if table_exists(conn, 'violation_patterns'):
        rows = safe_query(conn, """
            SELECT pattern_name, description, frequency, severity, evidence_strength
            FROM violation_patterns
            WHERE actors_involved LIKE '%McNeill%'
            ORDER BY frequency DESC
        """)
        for r in rows:
            violation_patterns.append({
                'pattern': r['pattern_name'],
                'frequency': r['frequency'],
                'severity': r['severity'],
            })
        print(f"  violation_patterns: {len(rows)} McNeill patterns")

    # --- Source 7: constitutional_violations ---
    constitutional = []
    if table_exists(conn, 'constitutional_violations'):
        rows = safe_query(conn, "SELECT * FROM constitutional_violations")
        for r in rows:
            constitutional.append({
                'amendment': r['amendment'],
                'clause': r['clause'],
                'violation_type': r['violation_type'],
                'description': str(r['description'])[:300],
                'severity': r['severity'],
                'caselaw': str(r['controlling_caselaw'])[:200] if r['controlling_caselaw'] else '',
            })
        print(f"  constitutional_violations: {len(rows)} entries")

    # --- Source 8: docket_events (for timeline) ---
    docket_timeline = []
    if table_exists(conn, 'docket_events'):
        rows = safe_query(conn, """
            SELECT event_date_iso, title, event_type, summary
            FROM docket_events
            ORDER BY event_date_iso
        """)
        for r in rows:
            docket_timeline.append({
                'date': r['event_date_iso'],
                'title': r['title'],
                'type': r['event_type'],
            })
        print(f"  docket_events: {len(rows)} timeline events")

    return all_violations, omega_summary, canons_matrix, violation_patterns, constitutional, docket_timeline


def group_by_mcr_chapter(violations):
    """Group violations by MCR chapter."""
    groups = defaultdict(list)
    no_mcr = []
    for v in violations:
        if v['mcr_rules']:
            for rule in v['mcr_rules']:
                chapter = get_mcr_chapter(rule)
                groups[chapter].append(v)
        else:
            no_mcr.append(v)
    return dict(groups), no_mcr


def calculate_frequency(violations, docket_timeline):
    """Calculate violation frequency metrics."""
    # Date range from docket
    dates = [d['date'] for d in docket_timeline if d['date']]
    if not dates:
        return {'per_month': 0, 'per_hearing': 0, 'total': len(violations)}

    try:
        first_date = min(dates)
        last_date = max(dates)
        from datetime import datetime as dt
        d1 = dt.strptime(first_date[:10], '%Y-%m-%d')
        d2 = dt.strptime(last_date[:10], '%Y-%m-%d')
        months = max(1, (d2 - d1).days / 30.0)
    except Exception:
        months = 12

    hearing_count = sum(1 for d in docket_timeline if d['type'] in ('hearing', 'order', 'motion'))
    hearing_count = max(1, hearing_count)

    return {
        'total': len(violations),
        'per_month': round(len(violations) / months, 1),
        'per_hearing': round(len(violations) / hearing_count, 1),
        'date_range': f"{dates[0] if dates else 'unknown'} to {dates[-1] if dates else 'unknown'}",
        'months_span': round(months, 1),
        'hearing_count': hearing_count,
    }


def generate_md(grouped, no_mcr, frequency, omega_summary, canons_matrix,
                violation_patterns, constitutional, all_violations):
    """Generate markdown catalog."""
    lines = []
    lines.append("# MCR VIOLATION CATALOG — Judge Jenny L. McNeill")
    lines.append(f"\n**Generated:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    lines.append(f"**Case:** Pigors v. Watson (2024-001507-DC)")
    lines.append(f"**Court:** 14th Circuit Court, Family Division, Muskegon County")
    lines.append(f"**Database:** litigation_context.db")

    # Executive summary
    lines.append("\n## EXECUTIVE SUMMARY\n")
    lines.append(f"| Metric | Value |")
    lines.append(f"|--------|-------|")
    lines.append(f"| **Total MCR Violations Cataloged** | **{frequency['total']}** |")
    lines.append(f"| Violations per Month | {frequency['per_month']} |")
    lines.append(f"| Violations per Hearing/Order | {frequency['per_hearing']} |")
    lines.append(f"| Date Range | {frequency.get('date_range', 'N/A')} |")
    lines.append(f"| MCR Chapters Affected | {len(grouped)} |")
    lines.append(f"| Constitutional Violations | {len(constitutional)} |")
    lines.append(f"| Violation Patterns | {len(violation_patterns)} |")

    # Severity breakdown
    severity_counts = defaultdict(int)
    for v in all_violations:
        sev = str(v.get('severity', 'unknown')).lower()
        severity_counts[sev] += 1
    lines.append("\n### Severity Distribution\n")
    lines.append("| Severity | Count |")
    lines.append("|----------|-------|")
    for sev in ['critical', 'high', 'medium', 'low']:
        if severity_counts.get(sev, 0) > 0:
            lines.append(f"| {sev.upper()} | {severity_counts[sev]} |")

    # Omega analysis summary
    if omega_summary:
        lines.append("\n### Violation Category Breakdown (Omega Analysis)\n")
        lines.append("| Category | Count | Percentage |")
        lines.append("|----------|-------|------------|")
        for cat, data in sorted(omega_summary.items(), key=lambda x: x[1]['count'], reverse=True):
            lines.append(f"| {cat} | {data['count']} | {data['percentage']}% |")

    # Violation patterns
    if violation_patterns:
        lines.append("\n### Top Violation Patterns\n")
        lines.append("| Pattern | Frequency | Severity |")
        lines.append("|---------|-----------|----------|")
        for vp in violation_patterns[:15]:
            lines.append(f"| {vp['pattern']} | {vp['frequency']} occurrences | {vp['severity']} |")

    # MCR Chapter catalog
    lines.append("\n## MCR VIOLATIONS BY CHAPTER\n")
    for chapter in sorted(grouped.keys()):
        violations = grouped[chapter]
        chapter_name = MCR_CHAPTERS.get(chapter, '')
        lines.append(f"### MCR {chapter}{' — ' + chapter_name if chapter_name else ''}")
        lines.append(f"**Violations:** {len(violations)}\n")

        # Deduplicate by description to avoid repetition
        seen_descs = set()
        unique_count = 0
        for v in violations:
            desc_key = str(v['description'])[:100]
            if desc_key in seen_descs:
                continue
            seen_descs.add(desc_key)
            unique_count += 1
            if unique_count > 10:
                lines.append(f"\n*... and {len(violations) - 10} more violations in this chapter*\n")
                break
            sev_marker = "🔴" if v['severity'] in ('critical', 'CRITICAL') else \
                         "🟠" if v['severity'] in ('high', 'HIGH') else "🟡"
            lines.append(f"{sev_marker} **[{v['severity'].upper() if v['severity'] else 'UNKNOWN'}]** "
                         f"(Source: {v['source_table']})")
            if v['date']:
                lines.append(f"  - **Date:** {v['date']}")
            desc = v['description'][:250].replace('\n', ' ')
            lines.append(f"  - {desc}")
            if v['canons']:
                lines.append(f"  - **Canon Cross-Ref:** {', '.join(v['canons'])}")
            if v['jtc_exhibit']:
                lines.append(f"  - **JTC Exhibit:** {v['jtc_exhibit']}")
            lines.append("")

    # Canon cross-reference
    lines.append("\n## CANON OF JUDICIAL CONDUCT CROSS-REFERENCE\n")
    lines.append("| Canon | Subsection | Violation Count | Severity |")
    lines.append("|-------|------------|----------------|----------|")
    for canon, data in canons_matrix.items():
        lines.append(
            f"| {canon} | {data['subsection']} | {data['violation_count']} | {data['severity']} |"
        )

    # All canons found in violations
    canon_counts = defaultdict(int)
    for v in all_violations:
        for c in v['canons']:
            canon_counts[c] += 1
    if canon_counts:
        lines.append("\n### Canon References Found in Violation Data\n")
        lines.append("| Canon | References |")
        lines.append("|-------|-----------|")
        for c, cnt in sorted(canon_counts.items(), key=lambda x: x[1], reverse=True):
            lines.append(f"| Canon {c} | {cnt} |")

    # Constitutional violations
    if constitutional:
        lines.append("\n## CONSTITUTIONAL VIOLATIONS\n")
        for cv in constitutional:
            lines.append(f"### {cv['amendment']} — {cv['clause']}")
            lines.append(f"**Type:** {cv['violation_type']}")
            lines.append(f"**Severity:** {cv['severity']}")
            lines.append(f"**Description:** {cv['description']}")
            if cv['caselaw']:
                lines.append(f"**Controlling Caselaw:** {cv['caselaw']}")
            lines.append("")

    return "\n".join(lines)


def main():
    print("=" * 60)
    print("TOOL #224: MCR VIOLATION CATALOG")
    print("Judge Jenny L. McNeill — Michigan Court Rule Violations")
    print("=" * 60)

    if not os.path.exists(DB_PATH):
        print(f"[ERROR] Database not found: {DB_PATH}")
        sys.exit(1)

    conn = connect_db()
    print(f"[OK] Connected to database ({os.path.getsize(DB_PATH) // (1024*1024)} MB)")

    print("\n[CATALOGING] Collecting violations from all sources...")
    all_violations, omega_summary, canons_matrix, violation_patterns, constitutional, docket_timeline = \
        catalog_violations(conn)

    print(f"\n[TOTAL] {len(all_violations)} violations collected from all sources")

    print("[GROUPING] By MCR chapter...")
    grouped, no_mcr = group_by_mcr_chapter(all_violations)
    print(f"  {len(grouped)} MCR chapters, {len(no_mcr)} without specific MCR reference")

    print("[CALCULATING] Frequency metrics...")
    frequency = calculate_frequency(all_violations, docket_timeline)

    # Build output data
    output_data = {
        'tool': 'mcr_violation_catalog',
        'tool_number': 224,
        'generated_at': datetime.now().isoformat(),
        'case': 'Pigors v. Watson (2024-001507-DC)',
        'judge': 'Hon. Jenny L. McNeill',
        'frequency': frequency,
        'severity_distribution': dict(defaultdict(int)),
        'mcr_chapters': {},
        'omega_summary': omega_summary,
        'canons_matrix': {k: v for k, v in canons_matrix.items()},
        'violation_patterns': violation_patterns,
        'constitutional_violations': constitutional,
    }

    # Severity distribution
    sev_dist = defaultdict(int)
    for v in all_violations:
        sev_dist[str(v.get('severity', 'unknown')).lower()] += 1
    output_data['severity_distribution'] = dict(sev_dist)

    # MCR chapters summary
    for chapter, violations in grouped.items():
        output_data['mcr_chapters'][chapter] = {
            'name': MCR_CHAPTERS.get(chapter, ''),
            'count': len(violations),
            'severities': dict(defaultdict(int)),
            'sample_violations': [
                {
                    'id': v['violation_id'],
                    'description': v['description'][:200],
                    'severity': v['severity'],
                    'date': v['date'],
                }
                for v in violations[:5]
            ],
        }
        chap_sev = defaultdict(int)
        for v in violations:
            chap_sev[str(v.get('severity', 'unknown')).lower()] += 1
        output_data['mcr_chapters'][chapter]['severities'] = dict(chap_sev)

    # Write JSON
    json_path = os.path.join(REPORTS_DIR, 'mcr_violation_catalog.json')
    with open(json_path, 'w', encoding='utf-8') as f:
        json.dump(output_data, f, indent=2, ensure_ascii=False, default=str)
    print(f"[SAVED] {json_path}")

    # Write MD
    md_content = generate_md(grouped, no_mcr, frequency, omega_summary,
                             canons_matrix, violation_patterns, constitutional, all_violations)
    md_path = os.path.join(REPORTS_DIR, 'MCR_VIOLATION_CATALOG.md')
    with open(md_path, 'w', encoding='utf-8') as f:
        f.write(md_content)
    print(f"[SAVED] {md_path}")

    # Print summary
    print("\n" + "=" * 60)
    print("RESULTS SUMMARY")
    print("=" * 60)
    print(f"Total violations:        {frequency['total']}")
    print(f"Violations per month:    {frequency['per_month']}")
    print(f"Violations per hearing:  {frequency['per_hearing']}")
    print(f"MCR chapters affected:   {len(grouped)}")
    print(f"Constitutional issues:   {len(constitutional)}")
    print(f"\nTop MCR chapters:")
    for chapter in sorted(grouped.keys(), key=lambda c: len(grouped[c]), reverse=True)[:10]:
        name = MCR_CHAPTERS.get(chapter, '')
        print(f"  MCR {chapter:>10} — {len(grouped[chapter]):>5} violations  {name}")
    print(f"\nSeverity: {dict(sev_dist)}")

    conn.close()
    print("\n[DONE] MCR violation catalog complete.")


if __name__ == '__main__':
    main()
