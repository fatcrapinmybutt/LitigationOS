#!/usr/bin/env python3
"""Tool #252: Parental Alienation Evidence Compiler
Compiles evidence of parental alienation using the 8 Gardner indicators.
Maps each evidence item to specific indicators and MCL 722.23(j).
Includes case law authorities: Keenan v Dawson, Demski v Petlick.

Output: PARENTAL_ALIENATION_EVIDENCE.md + parental_alienation_evidence.json
"""
import sys, os, json, sqlite3
from datetime import datetime
from collections import defaultdict

sys.stdout = open(sys.stdout.fileno(), mode='w', encoding='utf-8', errors='replace')

def s(v):
    return (v or "").lower()

# --- Path setup ---
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
REPO_ROOT = os.path.normpath(os.path.join(SCRIPT_DIR, '..', '..'))
DB_PATH = os.path.join(REPO_ROOT, 'litigation_context.db')
REPORTS_DIR = os.path.join(REPO_ROOT, '00_SYSTEM', 'reports')
os.makedirs(REPORTS_DIR, exist_ok=True)

# --- 8 Gardner Indicators of Parental Alienation ---
GARDNER_INDICATORS = {
    1: {
        'name': 'Campaign of Denigration',
        'description': 'The child participates in denigrating the alienated parent. '
                       'The alienating parent encourages or facilitates the child making '
                       'negative statements about the other parent.',
        'keywords': ['denigrat', 'bad mouth', 'talk bad', 'negative about father',
                     'negative about dad', 'say bad things', 'disparag', 'defam',
                     'trash talk', 'criticiz', 'demean', 'belittl', 'insult father',
                     'insult dad', 'hate dad', 'hate father'],
    },
    2: {
        'name': 'Weak, Frivolous, or Absurd Rationalizations',
        'description': 'The child gives weak or absurd reasons for rejection of the '
                       'alienated parent that do not justify the level of hostility.',
        'keywords': ['frivolous', 'absurd', 'no reason', 'weak excuse', 'irrational',
                     'unjustified', 'trivial reason', 'no basis', 'fabricat',
                     'made up reason', 'false allegation', 'false claim'],
    },
    3: {
        'name': 'Lack of Ambivalence',
        'description': 'The child sees the alienated parent as all bad and the alienating '
                       'parent as all good, with no nuanced view.',
        'keywords': ['all bad', 'all good', 'perfect', 'no ambivalence', 'black and white',
                     'only negative', 'nothing good', 'refuse to acknowledge',
                     'one-sided view', 'never wrong'],
    },
    4: {
        'name': 'Independent Thinker Phenomenon',
        'description': 'The child claims the rejection of the alienated parent is their '
                       'own idea, not influenced by the alienating parent.',
        'keywords': ['independent thinker', 'my own idea', 'nobody told me',
                     'my decision', 'i decided', 'not influenced', 'own choice',
                     'coached to say', 'scripted', 'rehearsed'],
    },
    5: {
        'name': 'Reflexive Support of Alienating Parent',
        'description': 'The child reflexively supports the alienating parent in conflicts '
                       'between parents, regardless of merit.',
        'keywords': ['always side', 'always support', 'reflexive', 'automatic support',
                     'side with mother', 'side with mom', 'never question',
                     'blind loyalty', 'take her side', 'defend mother'],
    },
    6: {
        'name': 'Absence of Guilt',
        'description': 'The child shows no guilt about cruelty toward the alienated parent.',
        'keywords': ['no guilt', 'no remorse', 'callous', 'cruel without guilt',
                     'indifferen', 'cold toward father', 'heartless',
                     'no empathy', 'no concern for father'],
    },
    7: {
        'name': 'Borrowed Scenarios',
        'description': 'The child uses words or scenarios borrowed from the alienating '
                       'parent that are not from personal experience.',
        'keywords': ['borrowed', 'parrot', 'repeat', 'adult language', 'not age appropriate',
                     'scripted', 'coached', 'someone told', 'mother said', 'mom said',
                     'told to say', 'put words', 'programmed'],
    },
    8: {
        'name': 'Spread of Animosity to Extended Family',
        'description': 'The child extends hostility to the alienated parent\'s extended '
                       'family and friends who were previously liked.',
        'keywords': ['extended family', 'grandparent', 'reject family', 'refuse to see',
                     'aunt', 'uncle', 'cousin', 'animosity spread', 'family cut off',
                     'paternal family', 'paternal grandparent'],
    },
}

# Broad alienation keywords for initial evidence capture
ALIENATION_KEYWORDS = [
    'alienat', 'parental alienation', 'interfere', 'withhold', 'gatekeep',
    'deny access', 'block contact', 'restrict', 'prevent visit', 'cancel visit',
    'no parenting time', 'refused call', 'phone denial', 'no contact',
    'turn child against', 'manipulat', 'brainwash', 'coach', 'program',
    'false allegation', 'fabricated', 'poisoning child', 'estrange',
    'custody interference', 'parenting time violation', 'denied visitation',
    'unilateral', 'excluded from', 'kept from',
]


def connect_db():
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


def is_alienation_related(text):
    """Check if text contains any alienation-related keyword."""
    t = s(text)
    return any(kw in t for kw in ALIENATION_KEYWORDS)


def match_indicators(text):
    """Return list of Gardner indicator numbers that text matches."""
    t = s(text)
    matched = []
    for num, info in GARDNER_INDICATORS.items():
        if any(kw in t for kw in info['keywords']):
            matched.append(num)
    return matched


def scan_evidence_quotes(conn):
    """Scan evidence_quotes for alienation evidence."""
    if not table_exists(conn, 'evidence_quotes'):
        return [], 0
    cols = get_columns(conn, 'evidence_quotes')
    if 'quote_text' not in cols:
        return [], 0

    rows = safe_query(conn, "SELECT id, quote_text, evidence_category, speaker, "
                            "date_ref, legal_significance FROM evidence_quotes")
    total = len(rows)
    results = []
    for row in rows:
        combined = ' '.join(str(row[c]) for c in dict(row).keys() if row[c])
        if is_alienation_related(combined):
            indicators = match_indicators(combined)
            results.append({
                'source': 'evidence_quotes',
                'id': row['id'],
                'text': str(row['quote_text'])[:300],
                'category': row['evidence_category'],
                'speaker': row['speaker'],
                'date_ref': row['date_ref'],
                'legal_significance': row['legal_significance'],
                'gardner_indicators': indicators,
            })
    return results, total


def scan_d_drive_events(conn):
    """Scan d_drive_events for alienation evidence."""
    if not table_exists(conn, 'd_drive_events'):
        return [], 0
    cols = get_columns(conn, 'd_drive_events')
    if 'event_description' not in cols:
        return [], 0

    rows = safe_query(conn, "SELECT id, event_description, category, actors, "
                            "event_date, severity FROM d_drive_events")
    total = len(rows)
    results = []
    for row in rows:
        combined = ' '.join(str(row[c]) for c in dict(row).keys() if row[c])
        if is_alienation_related(combined):
            indicators = match_indicators(combined)
            results.append({
                'source': 'd_drive_events',
                'id': row['id'],
                'text': str(row['event_description'])[:300],
                'category': row['category'],
                'actors': row['actors'],
                'date': row['event_date'],
                'severity': row['severity'],
                'gardner_indicators': indicators,
            })
    return results, total


def scan_claims(conn):
    """Scan claims for alienation-related claims."""
    if not table_exists(conn, 'claims'):
        return [], 0
    cols = get_columns(conn, 'claims')
    if 'proposition' not in cols:
        return [], 0

    rows = safe_query(conn, "SELECT claim_id, proposition, actor, classification, "
                            "status FROM claims")
    total = len(rows)
    results = []
    for row in rows:
        combined = ' '.join(str(row[c]) for c in dict(row).keys() if row[c])
        if is_alienation_related(combined):
            indicators = match_indicators(combined)
            results.append({
                'source': 'claims',
                'claim_id': row['claim_id'],
                'text': str(row['proposition'])[:300],
                'actor': row['actor'],
                'classification': row['classification'],
                'status': row['status'],
                'gardner_indicators': indicators,
            })
    return results, total


def scan_docket_events(conn):
    """Scan docket_events for alienation-related entries."""
    if not table_exists(conn, 'docket_events'):
        return [], 0

    rows = safe_query(conn, "SELECT event_id, title, summary, event_date_iso, "
                            "event_type FROM docket_events")
    total = len(rows)
    results = []
    for row in rows:
        combined = ' '.join(str(row[c]) for c in dict(row).keys() if row[c])
        if is_alienation_related(combined):
            indicators = match_indicators(combined)
            results.append({
                'source': 'docket_events',
                'event_id': row['event_id'],
                'text': str(row['title'])[:300],
                'summary': str(row['summary'] or '')[:200],
                'date': row['event_date_iso'],
                'event_type': row['event_type'],
                'gardner_indicators': indicators,
            })
    return results, total


def build_indicator_summary(all_evidence):
    """Build per-indicator evidence summary."""
    summary = {}
    for num in GARDNER_INDICATORS:
        items = [e for e in all_evidence if num in e.get('gardner_indicators', [])]
        summary[num] = {
            'indicator_number': num,
            'indicator_name': GARDNER_INDICATORS[num]['name'],
            'description': GARDNER_INDICATORS[num]['description'],
            'evidence_count': len(items),
            'sources': defaultdict(int),
            'top_evidence': [],
        }
        for item in items:
            summary[num]['sources'][item['source']] += 1
        summary[num]['sources'] = dict(summary[num]['sources'])
        summary[num]['top_evidence'] = items[:5]
    return summary


def generate_md(indicator_summary, all_evidence, source_totals):
    """Generate markdown report."""
    lines = [
        "# Parental Alienation Evidence Compilation",
        f"**Generated:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
        f"**Case:** Pigors v. Watson — 2024-001507-DC",
        f"**Court:** 14th Circuit Court, Family Division, Muskegon County, MI",
        f"**Judge:** Hon. Jenny L. McNeill",
        f"**Alienating Parent:** Emily A. Watson (Defendant)",
        f"**Alienated Parent:** Andrew James Pigors (Plaintiff, Pro Se)",
        "",
        "## Legal Framework",
        "",
        "### MCL 722.23(j) — Willingness to Facilitate Relationship",
        "> *The willingness and ability of each of the parties to facilitate and encourage "
        "a close and continuing parent-child relationship between the child and the other parent "
        "or the child and the parents. A court may not consider negatively for the purposes of this "
        "factor any reasonable action taken by a parent to protect a child or that parent from "
        "sexual assault or domestic violence by the child's other parent.*",
        "",
        "### Controlling Authorities",
        "",
        "| Case | Citation | Holding |",
        "|------|----------|---------|",
        "| Keenan v Dawson | 275 Mich App 671 (2007) | Parental alienation is a proper "
        "consideration under MCL 722.23(j); interference with parent-child relationship "
        "is a significant factor in best interest analysis |",
        "| Demski v Petlick | 309 Mich App 404 (2015) | Court properly considered pattern "
        "of conduct designed to undermine relationship with other parent; systematic "
        "interference weighs heavily against alienating parent |",
        "| Berger v Berger | 277 Mich App 700 (2008) | Parental conduct that erodes "
        "the child's relationship with the other parent is contrary to best interests |",
        "| Shade v Wright | 291 Mich App 17 (2010) | Factor (j) weighs against parent "
        "who impedes the other parent's relationship with child |",
        "",
        "### Gardner's 8 Indicators of Parental Alienation Syndrome",
        "",
        "Richard Gardner (1992) identified 8 behavioral indicators commonly present in "
        "cases of parental alienation. While Michigan courts do not use the term 'PAS' "
        "as a diagnosis, the behavioral indicators are relevant evidence under MCL 722.23(j).",
        "",
        "## Evidence Sources Scanned",
        "",
        "| Source | Total Records | Alienation Matches |",
        "|--------|--------------|-------------------|",
    ]
    for src, (total, matches) in sorted(source_totals.items()):
        pct = (matches / total * 100) if total > 0 else 0
        lines.append(f"| `{src}` | {total:,} | {matches:,} ({pct:.1f}%) |")

    total_matches = sum(m for _, m in source_totals.values())
    lines += [
        "",
        f"**Total alienation-related evidence items: {total_matches:,}**",
        "",
        "## Indicator Summary",
        "",
        "| # | Indicator | Evidence Count | Sources |",
        "|---|-----------|---------------|---------|",
    ]
    for num in sorted(indicator_summary.keys()):
        ind = indicator_summary[num]
        src_list = ', '.join(f"{k}({v})" for k, v in ind['sources'].items()) if ind['sources'] else 'None'
        lines.append(f"| {num} | {ind['indicator_name']} | {ind['evidence_count']} | {src_list} |")

    # Indicators with evidence (strength assessment)
    indicators_with_evidence = sum(1 for ind in indicator_summary.values()
                                   if ind['evidence_count'] > 0)
    lines += [
        "",
        f"**Indicators with evidence: {indicators_with_evidence}/8**",
        "",
    ]

    # Detail per indicator
    lines.append("## Detailed Indicator Analysis")
    for num in sorted(indicator_summary.keys()):
        ind = indicator_summary[num]
        lines += [
            "",
            f"### Indicator {num}: {ind['indicator_name']}",
            "",
            f"*{ind['description']}*",
            "",
            f"**Evidence items: {ind['evidence_count']}**",
            "",
        ]
        if ind['top_evidence']:
            for i, ev in enumerate(ind['top_evidence'], 1):
                date_str = ev.get('date') or ev.get('date_ref') or 'undated'
                lines.append(f"  {i}. **[{ev['source']}]** ({date_str}) — {ev['text'][:180]}")
            lines.append("")
        else:
            lines.append("  *No direct evidence mapped to this indicator.*\n")

    # Unmatched alienation evidence (broad match but no specific indicator)
    unmatched = [e for e in all_evidence if not e.get('gardner_indicators')]
    if unmatched:
        lines += [
            "",
            "## Additional Alienation Evidence (No Specific Indicator Match)",
            "",
            f"**{len(unmatched)} items** matched broad alienation keywords but did not map "
            "to a specific Gardner indicator. These may still be relevant under MCL 722.23(j).",
            "",
        ]
        for i, ev in enumerate(unmatched[:15], 1):
            date_str = ev.get('date') or ev.get('date_ref') or 'undated'
            lines.append(f"  {i}. **[{ev['source']}]** ({date_str}) — {ev['text'][:180]}")

    lines += [
        "",
        "---",
        "",
        "## Recommended Filing Strategy",
        "",
        "1. **Primary argument:** MCL 722.23(j) — Emily's pattern of conduct demonstrates "
        "unwillingness to facilitate Andrew's relationship with L.D.W.",
        "2. **Authority:** Cite Keenan v Dawson and Demski v Petlick for the proposition "
        "that systematic interference warrants modification of custody.",
        "3. **Evidence presentation:** Organize chronologically to show a *pattern* "
        "rather than isolated incidents.",
        "4. **Cross-reference:** Each alienation event should also be mapped to the "
        "relevant best interest factor in the MCL 722.23 analysis (Tool #251).",
        "",
        "---",
        f"*Generated by Tool #252 — Parental Alienation Evidence Compiler*",
    ]
    return '\n'.join(lines)


def main():
    print("=" * 70)
    print("TOOL #252: PARENTAL ALIENATION EVIDENCE COMPILER")
    print("=" * 70)
    print(f"DB: {DB_PATH}")
    print(f"Reports: {REPORTS_DIR}")
    print()

    if not os.path.exists(DB_PATH):
        print(f"[FATAL] Database not found: {DB_PATH}")
        sys.exit(1)

    conn = connect_db()

    # Verify tables
    for t in ['evidence_quotes', 'd_drive_events', 'claims', 'docket_events']:
        if table_exists(conn, t):
            cols = get_columns(conn, t)
            print(f"  [OK] {t}: {len(cols)} columns")
        else:
            print(f"  [MISS] {t}: not found")

    print("\n[1/4] Scanning evidence_quotes...")
    eq_results, eq_total = scan_evidence_quotes(conn)
    print(f"  => {len(eq_results)} alienation matches from {eq_total:,} records")

    print("[2/4] Scanning d_drive_events...")
    dd_results, dd_total = scan_d_drive_events(conn)
    print(f"  => {len(dd_results)} alienation matches from {dd_total:,} records")

    print("[3/4] Scanning claims...")
    cl_results, cl_total = scan_claims(conn)
    print(f"  => {len(cl_results)} alienation matches from {cl_total:,} records")

    print("[4/4] Scanning docket_events...")
    de_results, de_total = scan_docket_events(conn)
    print(f"  => {len(de_results)} alienation matches from {de_total:,} records")

    all_evidence = eq_results + dd_results + cl_results + de_results
    source_totals = {
        'evidence_quotes': (eq_total, len(eq_results)),
        'd_drive_events': (dd_total, len(dd_results)),
        'claims': (cl_total, len(cl_results)),
        'docket_events': (de_total, len(de_results)),
    }

    print(f"\n  TOTAL alienation evidence: {len(all_evidence):,}")

    # Build indicator summary
    indicator_summary = build_indicator_summary(all_evidence)

    # Generate reports
    md_report = generate_md(indicator_summary, all_evidence, source_totals)
    md_path = os.path.join(REPORTS_DIR, 'PARENTAL_ALIENATION_EVIDENCE.md')
    with open(md_path, 'w', encoding='utf-8') as f:
        f.write(md_report)
    print(f"\n[OK] Markdown: {md_path}")

    json_data = {
        'tool': '#252 Parental Alienation Evidence Compiler',
        'generated': datetime.now().isoformat(),
        'case': 'Pigors v. Watson — 2024-001507-DC',
        'authorities': [
            'Keenan v Dawson, 275 Mich App 671 (2007)',
            'Demski v Petlick, 309 Mich App 404 (2015)',
            'Berger v Berger, 277 Mich App 700 (2008)',
            'Shade v Wright, 291 Mich App 17 (2010)',
        ],
        'sources_scanned': {k: {'total': v[0], 'matches': v[1]}
                            for k, v in source_totals.items()},
        'total_alienation_evidence': len(all_evidence),
        'indicator_summary': {str(k): {
            'name': v['indicator_name'],
            'evidence_count': v['evidence_count'],
            'sources': v['sources'],
        } for k, v in indicator_summary.items()},
        'all_evidence': all_evidence,
    }
    json_path = os.path.join(REPORTS_DIR, 'parental_alienation_evidence.json')
    with open(json_path, 'w', encoding='utf-8') as f:
        json.dump(json_data, f, indent=2, default=str)
    print(f"[OK] JSON: {json_path}")

    # Print summary
    print("\n" + "=" * 70)
    print("GARDNER INDICATOR SCORECARD")
    print("=" * 70)
    for num in sorted(indicator_summary.keys()):
        ind = indicator_summary[num]
        bar = "█" * min(ind['evidence_count'], 40) if ind['evidence_count'] > 0 else "—"
        print(f"  [{num}] {ind['indicator_name']:<45} {ind['evidence_count']:>4}  {bar}")
    indicators_hit = sum(1 for v in indicator_summary.values() if v['evidence_count'] > 0)
    print(f"\n  Indicators with evidence: {indicators_hit}/8")
    print(f"  Total alienation evidence items: {len(all_evidence):,}")
    print("=" * 70)

    conn.close()
    return 0


if __name__ == '__main__':
    sys.exit(main())
