#!/usr/bin/env python3
"""
Tool #232: Filing Sequencing Engine
Determines optimal filing ORDER for Pigors v. Watson litigation.
Analyzes dependencies, evidence readiness, deadlines, and strategic timing.
Outputs: MD report + JSON to reports dir.
"""
import sys, os, sqlite3, json, textwrap
from datetime import datetime, timedelta
from collections import defaultdict

sys.stdout = open(sys.stdout.fileno(), mode='w', encoding='utf-8', errors='replace')

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
REPO_ROOT = os.path.abspath(os.path.join(SCRIPT_DIR, '..', '..'))
DB_PATH = os.path.join(REPO_ROOT, 'litigation_context.db')
REPORT_DIR = os.path.join(REPO_ROOT, '00_SYSTEM', 'reports')
os.makedirs(REPORT_DIR, exist_ok=True)

TIMESTAMP = datetime.now().strftime('%Y-%m-%d_%H%M%S')
MD_PATH = os.path.join(REPORT_DIR, f'filing_sequence_report_{TIMESTAMP}.md')
JSON_PATH = os.path.join(REPORT_DIR, f'filing_sequence_report_{TIMESTAMP}.json')


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


def query_filing_sequence(conn):
    cols = verify_table(conn, 'filing_sequence')
    if not cols:
        return []
    rows = conn.execute("SELECT * FROM filing_sequence ORDER BY priority").fetchall()
    return [dict(r) for r in rows]


def query_filing_dependencies(conn):
    cols = verify_table(conn, 'filing_dependencies')
    if not cols:
        return []
    rows = conn.execute("SELECT * FROM filing_dependencies").fetchall()
    return [dict(r) for r in rows]


def query_filing_readiness(conn):
    cols = verify_table(conn, 'filing_readiness')
    if not cols:
        return []
    rows = conn.execute("SELECT * FROM filing_readiness ORDER BY total_score DESC").fetchall()
    return [dict(r) for r in rows]


def query_deadlines(conn):
    cols = verify_table(conn, 'deadlines')
    if not cols:
        return []
    rows = conn.execute("SELECT * FROM deadlines ORDER BY due_date_iso").fetchall()
    return [dict(r) for r in rows]


def query_evidence_counts_per_filing(conn):
    """Count evidence quotes related to each filing vehicle."""
    cols = verify_table(conn, 'evidence_quotes')
    if not cols:
        return {}
    vehicle_keywords = {
        'EMERGENCY_MOTION': ['parenting time', 'emergency', 'restore', 'custody'],
        'COA_BRIEF': ['appeal', 'appellant', 'COA', 'court of appeals'],
        'JTC_COMPLAINT': ['judicial', 'misconduct', 'JTC', 'McNeill', 'bias'],
        'DISQUALIFY': ['disqualif', 'MCR 2.003', 'recusal', 'bias'],
        'VOID_EX_PARTE': ['ex parte', 'void', 'without hearing'],
        'PPO': ['PPO', 'protection order', 'personal protection'],
        'FEDERAL_1983': ['1983', 'civil rights', 'due process', '14th amendment'],
        'CONTEMPT': ['contempt', 'enforcement', 'violation', 'non-compliance'],
        'HOUSING': ['housing', 'eviction', 'Shady Oaks', 'discrimination'],
        'FOC_OBJECTION': ['FOC', 'friend of court', 'Rusco', 'recommendation'],
    }
    counts = {}
    for vehicle, keywords in vehicle_keywords.items():
        conditions = " OR ".join([f"quote_text LIKE '%{kw}%'" for kw in keywords])
        sql = f"SELECT COUNT(*) as cnt FROM evidence_quotes WHERE {conditions}"
        row = conn.execute(sql).fetchone()
        counts[vehicle] = row['cnt']
    return counts


def query_claims_per_issue(conn):
    cols = verify_table(conn, 'claims')
    if not cols:
        return {}
    rows = conn.execute("""
        SELECT issue_id, COUNT(*) as cnt, 
               SUM(CASE WHEN status='supported' THEN 1 ELSE 0 END) as supported
        FROM claims GROUP BY issue_id ORDER BY cnt DESC
    """).fetchall()
    return {r['issue_id']: {'total': r['cnt'], 'supported': r['supported']} for r in rows}


def build_dependency_graph(deps, sequence):
    """Build adjacency list from filing_dependencies + filing_sequence.depends_on."""
    graph = defaultdict(list)       # pkg -> [depends_on_pkgs]
    reverse_graph = defaultdict(list)  # pkg -> [enables_pkgs]

    # From filing_sequence.depends_on field
    for filing in sequence:
        pkg = filing.get('package_id', '')
        dep = filing.get('depends_on')
        if dep:
            graph[pkg].append(dep)
            reverse_graph[dep].append(pkg)

    # From filing_dependencies table
    for d in deps:
        src = d.get('source_filing', '')
        tgt = d.get('target_filing', '')
        rel = d.get('relationship', '')
        if rel in ('enables', 'precedes', 'appeals'):
            graph[tgt].append(src)
            reverse_graph[src].append(tgt)

    return graph, reverse_graph


def compute_critical_path(sequence, graph):
    """Topological sort to find critical path through filings."""
    in_degree = defaultdict(int)
    all_pkgs = set()
    for filing in sequence:
        pkg = filing['package_id']
        all_pkgs.add(pkg)
        for dep in graph.get(pkg, []):
            all_pkgs.add(dep)

    for pkg in all_pkgs:
        for dep in graph.get(pkg, []):
            in_degree[pkg] += 1

    # BFS topological sort
    queue = [p for p in all_pkgs if in_degree[p] == 0]
    order = []
    while queue:
        queue.sort()
        node = queue.pop(0)
        order.append(node)
        for target_pkg in all_pkgs:
            if node in graph.get(target_pkg, []):
                in_degree[target_pkg] -= 1
                if in_degree[target_pkg] == 0:
                    queue.append(target_pkg)
    return order


def compute_recommended_sequence(sequence, readiness, deadlines, deps, evidence_counts):
    """Score and order filings by multi-factor analysis."""
    readiness_map = {r['vehicle_name']: r for r in readiness}
    deadline_map = {}
    today = datetime.now()

    for dl in deadlines:
        due = dl.get('due_date_iso', '')
        if due and dl.get('status') != 'satisfied':
            try:
                due_dt = datetime.strptime(due, '%Y-%m-%d')
                days_until = (due_dt - today).days
                deadline_map[dl.get('title', '')] = {
                    'due_date': due,
                    'days_until': days_until,
                    'urgency': 'CRITICAL' if days_until < 14 else 'HIGH' if days_until < 30 else 'MEDIUM' if days_until < 60 else 'LOW',
                    'authority': dl.get('basis_authority', ''),
                    'risk': dl.get('risk_if_missed', '')
                }
            except ValueError:
                pass

    scored_filings = []
    for filing in sequence:
        pkg = filing['package_id']
        score = 0
        factors = []

        # Factor 1: Priority tier (Tier 1 = +40, Tier 2 = +30, etc.)
        tier = filing.get('tier', 4)
        tier_score = max(0, (5 - tier) * 10)
        score += tier_score
        factors.append(f"Tier {tier} priority: +{tier_score}")

        # Factor 2: Deadline urgency
        target_date = filing.get('target_date', '')
        if target_date:
            try:
                target_dt = datetime.strptime(target_date, '%Y-%m-%d')
                days_out = (target_dt - today).days
                if days_out < 0:
                    urgency_score = 50
                    factors.append(f"OVERDUE by {abs(days_out)} days: +50")
                elif days_out < 14:
                    urgency_score = 40
                    factors.append(f"Due in {days_out} days (CRITICAL): +40")
                elif days_out < 30:
                    urgency_score = 30
                    factors.append(f"Due in {days_out} days (HIGH): +30")
                elif days_out < 60:
                    urgency_score = 20
                    factors.append(f"Due in {days_out} days (MEDIUM): +20")
                else:
                    urgency_score = 10
                    factors.append(f"Due in {days_out} days (LOW): +10")
                score += urgency_score
            except ValueError:
                pass

        # Factor 3: Evidence readiness (from filing_readiness table)
        vehicle_match = None
        for vn in readiness_map:
            if any(part in pkg.upper() for part in vn.upper().split('_') if len(part) > 3):
                vehicle_match = readiness_map[vn]
                break
        if vehicle_match:
            ready_score = min(30, vehicle_match.get('total_score', 0) // 3)
            score += ready_score
            factors.append(f"Evidence readiness ({vehicle_match.get('total_score', 0)}/100): +{ready_score}")

        # Factor 4: No blocking dependencies = bonus
        dep_on = filing.get('depends_on')
        if not dep_on:
            score += 15
            factors.append("No dependencies (can file immediately): +15")
        else:
            factors.append(f"Blocked by: {dep_on}")

        # Factor 5: Evidence volume
        for ev_key, ev_count in evidence_counts.items():
            if any(part in pkg.upper() for part in ev_key.split('_') if len(part) > 3):
                ev_score = min(15, ev_count // 50)
                score += ev_score
                factors.append(f"Evidence quotes ({ev_count}): +{ev_score}")
                break

        scored_filings.append({
            'package_id': pkg,
            'filing_title': filing.get('filing_title', ''),
            'target_court': filing.get('target_court', ''),
            'target_date': target_date,
            'tier': tier,
            'priority_original': filing.get('priority'),
            'composite_score': score,
            'scoring_factors': factors,
            'depends_on': dep_on,
            'strategic_purpose': filing.get('strategic_purpose', ''),
            'status': filing.get('status', ''),
        })

    scored_filings.sort(key=lambda x: -x['composite_score'])
    for i, f in enumerate(scored_filings):
        f['recommended_order'] = i + 1

    return scored_filings


def generate_gantt(scored_filings):
    """Generate ASCII Gantt-style timeline."""
    today = datetime.now()
    lines = []
    lines.append("```")
    lines.append(f"Filing Timeline (today: {today.strftime('%Y-%m-%d')})")
    lines.append("=" * 90)

    # Find date range
    dates = []
    for f in scored_filings:
        if f.get('target_date'):
            try:
                dates.append(datetime.strptime(f['target_date'], '%Y-%m-%d'))
            except ValueError:
                pass

    if not dates:
        lines.append("No dates available for timeline.")
        lines.append("```")
        return "\n".join(lines)

    min_date = min(today, min(dates))
    max_date = max(dates) + timedelta(days=7)
    total_days = (max_date - min_date).days or 1

    # Header with month markers
    header = " " * 45
    for month_offset in range(6):
        m = today + timedelta(days=month_offset * 30)
        header += f"|{m.strftime('%b')}".ljust(10)
    lines.append(header)
    lines.append("-" * 90)

    # Chart width
    chart_width = 40

    for f in scored_filings:
        label = f['filing_title'][:40].ljust(40)
        if f.get('target_date'):
            try:
                target = datetime.strptime(f['target_date'], '%Y-%m-%d')
                offset = (target - min_date).days
                pos = int((offset / total_days) * chart_width)
                pos = max(0, min(chart_width - 1, pos))
                bar = "." * pos + "▓" + "." * (chart_width - pos - 1)

                days_left = (target - today).days
                if days_left < 0:
                    marker = f" ◀ OVERDUE {abs(days_left)}d"
                elif days_left < 14:
                    marker = f" ◀ {days_left}d ⚠️"
                elif days_left < 30:
                    marker = f" ◀ {days_left}d"
                else:
                    marker = f" ◀ {days_left}d"
                lines.append(f"{label} |{bar}|{marker}")
            except ValueError:
                lines.append(f"{label} | {'?' * chart_width} | NO DATE")
        else:
            lines.append(f"{label} | {'~' * chart_width} | FLEXIBLE")

    lines.append("=" * 90)
    lines.append("▓ = Target filing date | . = timeline span")
    lines.append("```")
    return "\n".join(lines)


def generate_dependency_diagram(deps, sequence):
    """ASCII dependency flow diagram."""
    lines = ["```"]
    lines.append("FILING DEPENDENCY FLOW")
    lines.append("=" * 60)

    pkg_map = {f['package_id']: f['filing_title'][:35] for f in sequence}

    for filing in sequence:
        pkg = filing['package_id']
        dep = filing.get('depends_on')
        title = filing['filing_title'][:40]
        tier = filing.get('tier', '?')

        if dep:
            lines.append(f"  T{tier} [{dep}] ──enables──▶ [{pkg}]")
            lines.append(f"     {pkg_map.get(dep, dep)[:35]:35s}   {title}")
        else:
            lines.append(f"  T{tier} [ROOT] ──────────▶ [{pkg}]")
            lines.append(f"     {'(no dependency)':35s}   {title}")
        lines.append("")

    lines.append("Critical chains:")
    lines.append("  COA Brief → JTC Complaint → Disqualification → Void Orders → Vacate PPO")
    lines.append("  COA Brief → Federal §1983 (parallel track)")
    lines.append("  COA Brief → MSC Application (contingent)")
    lines.append("```")
    return "\n".join(lines)


def main():
    print(f"[Filing Sequencing Engine] Connecting to: {DB_PATH}")
    if not os.path.exists(DB_PATH):
        print(f"ERROR: Database not found at {DB_PATH}")
        sys.exit(1)

    conn = get_connection()

    # Query all data
    print("  Querying filing_sequence...")
    sequence = query_filing_sequence(conn)
    print(f"    Found {len(sequence)} filings in sequence")

    print("  Querying filing_dependencies...")
    deps = query_filing_dependencies(conn)
    print(f"    Found {len(deps)} dependency relationships")

    print("  Querying filing_readiness...")
    readiness = query_filing_readiness(conn)
    print(f"    Found {len(readiness)} readiness assessments")

    print("  Querying deadlines...")
    deadlines_data = query_deadlines(conn)
    print(f"    Found {len(deadlines_data)} deadlines")

    print("  Querying evidence counts per filing vehicle...")
    evidence_counts = query_evidence_counts_per_filing(conn)
    for k, v in evidence_counts.items():
        print(f"    {k}: {v} supporting quotes")

    print("  Querying claims distribution...")
    claims = query_claims_per_issue(conn)
    print(f"    Found {len(claims)} issue categories with {sum(c['total'] for c in claims.values())} total claims")

    # Build dependency graph
    graph, reverse_graph = build_dependency_graph(deps, sequence)
    critical_path = compute_critical_path(sequence, graph)

    # Compute recommended sequence
    scored = compute_recommended_sequence(sequence, readiness, deadlines_data, deps, evidence_counts)

    # Generate visualizations
    gantt = generate_gantt(scored)
    dep_diagram = generate_dependency_diagram(deps, sequence)

    conn.close()

    # Build JSON output
    json_output = {
        'report_type': 'filing_sequence_engine',
        'generated_at': datetime.now().isoformat(),
        'case': 'Pigors v. Watson (14th Circuit, COA 366810)',
        'summary': {
            'total_filings': len(sequence),
            'total_dependencies': len(deps),
            'total_deadlines': len(deadlines_data),
            'readiness_assessments': len(readiness),
            'evidence_quote_counts': evidence_counts,
            'claims_by_issue': claims,
        },
        'recommended_sequence': scored,
        'critical_path_order': critical_path,
        'dependency_relationships': deps,
    }

    # Build MD report
    md_lines = []
    md_lines.append("# Filing Sequencing Engine Report")
    md_lines.append(f"\n**Generated:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    md_lines.append(f"**Case:** Pigors v. Watson | 14th Circuit | COA 366810")
    md_lines.append(f"**Filings Analyzed:** {len(sequence)} | **Dependencies:** {len(deps)} | **Deadlines:** {len(deadlines_data)}")

    md_lines.append("\n## Recommended Filing Order (Multi-Factor Scored)\n")
    md_lines.append("| # | Filing | Court | Target Date | Score | Key Factor |")
    md_lines.append("|---|--------|-------|-------------|-------|------------|")
    for f in scored:
        top_factor = f['scoring_factors'][0] if f['scoring_factors'] else 'N/A'
        blocked = f" ⛔ Blocked by {f['depends_on']}" if f['depends_on'] else ""
        md_lines.append(f"| {f['recommended_order']} | {f['filing_title'][:45]} | {f['target_court'][:25]} | {f['target_date']} | **{f['composite_score']}** | {top_factor}{blocked} |")

    md_lines.append("\n## Scoring Detail\n")
    for f in scored:
        md_lines.append(f"### #{f['recommended_order']}: {f['filing_title']}")
        md_lines.append(f"- **Package:** {f['package_id']}")
        md_lines.append(f"- **Court:** {f['target_court']}")
        md_lines.append(f"- **Target Date:** {f['target_date']}")
        md_lines.append(f"- **Composite Score:** {f['composite_score']}")
        md_lines.append(f"- **Depends On:** {f['depends_on'] or 'None (root filing)'}")
        md_lines.append("- **Scoring Factors:**")
        for factor in f['scoring_factors']:
            md_lines.append(f"  - {factor}")
        purpose = f['strategic_purpose'][:300] if f['strategic_purpose'] else 'N/A'
        md_lines.append(f"- **Strategic Purpose:** {purpose}")
        md_lines.append("")

    md_lines.append("\n## Gantt-Style Timeline\n")
    md_lines.append(gantt)

    md_lines.append("\n## Dependency Flow\n")
    md_lines.append(dep_diagram)

    md_lines.append("\n## Critical Path Analysis\n")
    md_lines.append("The critical path determines the longest chain of dependent filings:")
    md_lines.append("")
    for i, pkg in enumerate(critical_path):
        arrow = " → " if i < len(critical_path) - 1 else ""
        md_lines.append(f"  {i+1}. **{pkg}**{arrow}")

    md_lines.append("\n## Evidence Readiness Summary\n")
    md_lines.append("| Filing Vehicle | Score | Status | Gaps |")
    md_lines.append("|---------------|-------|--------|------|")
    for r in readiness[:15]:
        md_lines.append(f"| {r['vehicle_name'][:40]} | {r['total_score']}/100 | {r['status']} | {str(r.get('gaps', ''))[:60]} |")

    md_lines.append("\n## Active Deadlines\n")
    md_lines.append("| Deadline | Due Date | Days | Authority | Risk |")
    md_lines.append("|----------|----------|------|-----------|------|")
    today = datetime.now()
    for dl in deadlines_data:
        if dl.get('status') == 'satisfied':
            continue
        due = dl.get('due_date_iso', '')
        days = ''
        if due:
            try:
                days_int = (datetime.strptime(due, '%Y-%m-%d') - today).days
                days = f"{'⚠️ ' if days_int < 30 else ''}{days_int}d"
            except ValueError:
                pass
        md_lines.append(f"| {dl['title'][:45]} | {due} | {days} | {dl.get('basis_authority', '')[:30]} | {str(dl.get('risk_if_missed', ''))[:40]} |")

    md_lines.append("\n## Claims Distribution (Top Issues)\n")
    sorted_claims = sorted(claims.items(), key=lambda x: -x[1]['total'])[:10]
    for issue, data in sorted_claims:
        md_lines.append(f"- **{issue}**: {data['total']} claims ({data['supported']} supported)")

    md_report = "\n".join(md_lines)

    # Write outputs
    with open(MD_PATH, 'w', encoding='utf-8') as f:
        f.write(md_report)
    print(f"\n  MD report written: {MD_PATH}")

    with open(JSON_PATH, 'w', encoding='utf-8') as f:
        json.dump(json_output, f, indent=2, default=str, ensure_ascii=False)
    print(f"  JSON report written: {JSON_PATH}")

    # Print summary
    print("\n" + "=" * 60)
    print("FILING SEQUENCE ENGINE — RECOMMENDED ORDER")
    print("=" * 60)
    for f in scored:
        dep_note = f" [BLOCKED BY {f['depends_on']}]" if f['depends_on'] else " [READY]"
        print(f"  #{f['recommended_order']:2d} | Score {f['composite_score']:3d} | {f['target_date']} | {f['filing_title'][:50]}{dep_note}")
    print("=" * 60)
    print(f"Reports: {MD_PATH}")
    print(f"         {JSON_PATH}")


if __name__ == '__main__':
    main()
