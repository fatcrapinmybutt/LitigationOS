#!/usr/bin/env python3
"""Tool #251: MCL 722.23 Best Interest Factor Mapper
Maps ALL evidence to each of the 12 MCL 722.23 best interest factors (a-l).
For each factor: queries evidence_quotes, d_drive_events, claims, docket_events.
Counts evidence items per factor per party (Andrew vs Emily).
Calculates which parent is favored on each factor.

Output: BEST_INTEREST_FACTOR_MAP.md + best_interest_factor_map.json
"""
import sys, os, json, sqlite3, re
from datetime import datetime
from collections import defaultdict

sys.stdout = open(sys.stdout.fileno(), mode='w', encoding='utf-8', errors='replace')

def s(v):
    return (v or "").lower()

# --- Path setup (never set CWD to repo root — shadow modules) ---
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
REPO_ROOT = os.path.normpath(os.path.join(SCRIPT_DIR, '..', '..'))
DB_PATH = os.path.join(REPO_ROOT, 'litigation_context.db')
REPORTS_DIR = os.path.join(REPO_ROOT, '00_SYSTEM', 'reports')
os.makedirs(REPORTS_DIR, exist_ok=True)

# --- MCL 722.23 Best Interest Factors ---
FACTORS = {
    'a': {
        'name': 'Love, Affection, and Other Emotional Ties',
        'keywords': ['love', 'affection', 'emotional', 'bond', 'attachment',
                     'relationship', 'nurtur', 'caring', 'comfort', 'warmth'],
        'neg_keywords': ['withhold', 'alienat', 'reject', 'abandon', 'neglect',
                         'estrange', 'interfere with relationship'],
    },
    'b': {
        'name': 'Capacity for Love, Affection, Guidance; Continuation of Education',
        'keywords': ['guidance', 'education', 'school', 'homework', 'tutor',
                     'teach', 'enroll', 'academic', 'learning', 'parenting skill'],
        'neg_keywords': ['fail to enroll', 'truancy', 'no guidance', 'neglect education'],
    },
    'c': {
        'name': 'Capacity to Provide Food, Clothing, Medical Care',
        'keywords': ['food', 'clothing', 'medical', 'insurance', 'healthcare',
                     'housing', 'shelter', 'income', 'employ', 'provid', 'necessit'],
        'neg_keywords': ['no insurance', 'unfit home', 'unable to provide', 'unstable housing',
                         'homeless', 'evict', 'shady oaks'],
    },
    'd': {
        'name': 'Established Custodial Environment',
        'keywords': ['custodial environment', 'established custod', 'stable home',
                     'primary caregiv', 'routine', 'consistent care', 'lived with',
                     'primary residence', 'custodial parent'],
        'neg_keywords': ['disrupt', 'uprooted', 'changed residence', 'instability',
                         'moved repeatedly', 'no stable home'],
    },
    'e': {
        'name': 'Permanence of Existing/Proposed Custodial Home',
        'keywords': ['permanent', 'stability', 'long-term', 'established home',
                     'community ties', 'neighborhood', 'own home', 'lease', 'roots'],
        'neg_keywords': ['temporary', 'transient', 'eviction', 'frequent moves',
                         'boyfriend', 'cohabit', 'shady oaks'],
    },
    'f': {
        'name': 'Moral Fitness of the Parties',
        'keywords': ['moral', 'integrity', 'honest', 'character', 'ethical',
                     'law-abiding', 'responsible', 'truthful'],
        'neg_keywords': ['perjury', 'lie', 'dishonest', 'fraud', 'false statement',
                         'decepti', 'criminal', 'substance abuse', 'drug',
                         'alcohol', 'upl', 'unauthorized practice'],
    },
    'g': {
        'name': 'Mental and Physical Health of the Parties',
        'keywords': ['health', 'mental health', 'physical health', 'therapy',
                     'counseling', 'diagnos', 'treatment', 'medication', 'well-being'],
        'neg_keywords': ['substance abuse', 'addiction', 'untreated', 'mental illness',
                         'unfit', 'impair', 'healthwest'],
    },
    'h': {
        'name': 'Home, School, and Community Record of the Child',
        'keywords': ['school record', 'community', 'extracurricular', 'friend',
                     'social', 'behavio', 'grade', 'teacher', 'church', 'sport'],
        'neg_keywords': ['behavioral issue', 'decline', 'withdraw', 'regression',
                         'absent', 'failing grade'],
    },
    'i': {
        'name': 'Reasonable Preference of the Child',
        'keywords': ['child preference', 'child wish', 'child want', 'child express',
                     'child stated', 'child request', 'preference of the child'],
        'neg_keywords': ['coached', 'manipulated', 'coerced', 'programmed', 'scripted'],
    },
    'j': {
        'name': 'Willingness to Facilitate Relationship with Other Parent',
        'keywords': ['facilitat', 'co-parent', 'cooperat', 'encourage relationship',
                     'support contact', 'phone call', 'visitation', 'parenting time'],
        'neg_keywords': ['alienat', 'interfere', 'withhold', 'block', 'deny access',
                         'gatekeep', 'restrict contact', 'parenting time violation',
                         'no-show', 'cancel visit', 'refuse call'],
    },
    'k': {
        'name': 'Domestic Violence',
        'keywords': ['domestic violence', 'ppo', 'protection order', 'assault',
                     'threat', 'intimidat', 'abuse', 'battery', 'physical harm',
                     'restraining order'],
        'neg_keywords': ['false ppo', 'frivolous ppo', 'weaponized ppo',
                         'fabricated allegation'],
    },
    'l': {
        'name': 'Any Other Relevant Factor',
        'keywords': ['relevant', 'other factor', 'additional', 'pattern',
                     'contempt', 'court order violation', 'foc', 'guardian ad litem',
                     'best interest'],
        'neg_keywords': ['ex parte', 'bias', 'judicial misconduct', 'due process',
                         'violation of rights', 'sanctions'],
    },
}


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


def classify_party(text):
    """Determine which party evidence relates to based on text content."""
    t = s(text)
    andrew_signals = ['andrew', 'pigors', 'father', 'plaintiff', 'dad', 'paternal']
    emily_signals = ['emily', 'watson', 'mother', 'defendant', 'mom', 'maternal',
                     'respondent', 'berry', 'ronald']
    a_score = sum(1 for sig in andrew_signals if sig in t)
    e_score = sum(1 for sig in emily_signals if sig in t)
    if a_score > e_score:
        return 'andrew'
    elif e_score > a_score:
        return 'emily'
    return 'neutral'


def match_factor(text, factor_key):
    """Check if text matches a factor's keywords. Returns (positive_match, negative_match)."""
    t = s(text)
    info = FACTORS[factor_key]
    pos = any(kw in t for kw in info['keywords'])
    neg = any(kw in t for kw in info['neg_keywords'])
    return pos, neg


def map_evidence_quotes(conn):
    """Map evidence_quotes to best interest factors."""
    if not table_exists(conn, 'evidence_quotes'):
        print("  [SKIP] evidence_quotes not found")
        return {}
    cols = get_columns(conn, 'evidence_quotes')
    text_col = 'quote_text' if 'quote_text' in cols else None
    cat_col = 'evidence_category' if 'evidence_category' in cols else None
    speaker_col = 'speaker' if 'speaker' in cols else None
    sig_col = 'legal_significance' if 'legal_significance' in cols else None
    if not text_col:
        print("  [SKIP] evidence_quotes missing quote_text column")
        return {}

    select_parts = [f'id, {text_col}']
    if cat_col:
        select_parts.append(cat_col)
    if speaker_col:
        select_parts.append(speaker_col)
    if sig_col:
        select_parts.append(sig_col)

    rows = safe_query(conn, f"SELECT {', '.join(select_parts)} FROM evidence_quotes")
    print(f"  evidence_quotes: {len(rows)} rows loaded")

    mapping = defaultdict(lambda: {'andrew': [], 'emily': [], 'neutral': []})
    for row in rows:
        combined = ' '.join(str(row[c]) for c in dict(row).keys() if row[c])
        party = classify_party(combined)
        for fk in FACTORS:
            pos, neg = match_factor(combined, fk)
            if pos or neg:
                entry = {
                    'source': 'evidence_quotes',
                    'id': row['id'],
                    'excerpt': str(row[text_col])[:200],
                    'positive_match': pos,
                    'negative_match': neg,
                }
                mapping[fk][party].append(entry)
    return dict(mapping)


def map_d_drive_events(conn):
    """Map d_drive_events to best interest factors."""
    if not table_exists(conn, 'd_drive_events'):
        print("  [SKIP] d_drive_events not found")
        return {}
    cols = get_columns(conn, 'd_drive_events')
    desc_col = 'event_description' if 'event_description' in cols else None
    cat_col = 'category' if 'category' in cols else None
    actors_col = 'actors' if 'actors' in cols else None
    if not desc_col:
        print("  [SKIP] d_drive_events missing event_description")
        return {}

    rows = safe_query(conn, f"SELECT id, {desc_col}, {cat_col or 'NULL'} AS category, "
                            f"{actors_col or 'NULL'} AS actors, "
                            f"event_date FROM d_drive_events")
    print(f"  d_drive_events: {len(rows)} rows loaded")

    mapping = defaultdict(lambda: {'andrew': [], 'emily': [], 'neutral': []})
    for row in rows:
        combined = ' '.join(str(row[c]) for c in dict(row).keys() if row[c])
        party = classify_party(combined)
        for fk in FACTORS:
            pos, neg = match_factor(combined, fk)
            if pos or neg:
                entry = {
                    'source': 'd_drive_events',
                    'id': row['id'],
                    'excerpt': str(row[desc_col])[:200],
                    'date': row['event_date'],
                    'positive_match': pos,
                    'negative_match': neg,
                }
                mapping[fk][party].append(entry)
    return dict(mapping)


def map_claims(conn):
    """Map claims to best interest factors."""
    if not table_exists(conn, 'claims'):
        print("  [SKIP] claims not found")
        return {}
    cols = get_columns(conn, 'claims')
    prop_col = 'proposition' if 'proposition' in cols else None
    actor_col = 'actor' if 'actor' in cols else None
    class_col = 'classification' if 'classification' in cols else None
    if not prop_col:
        print("  [SKIP] claims missing proposition")
        return {}

    rows = safe_query(conn, f"SELECT claim_id, {prop_col}, {actor_col or 'NULL'} AS actor, "
                            f"{class_col or 'NULL'} AS classification FROM claims")
    print(f"  claims: {len(rows)} rows loaded")

    mapping = defaultdict(lambda: {'andrew': [], 'emily': [], 'neutral': []})
    for row in rows:
        combined = ' '.join(str(row[c]) for c in dict(row).keys() if row[c])
        party = classify_party(combined)
        for fk in FACTORS:
            pos, neg = match_factor(combined, fk)
            if pos or neg:
                entry = {
                    'source': 'claims',
                    'claim_id': row['claim_id'],
                    'excerpt': str(row[prop_col])[:200],
                    'classification': row['classification'],
                    'positive_match': pos,
                    'negative_match': neg,
                }
                mapping[fk][party].append(entry)
    return dict(mapping)


def map_docket_events(conn):
    """Map docket_events to best interest factors."""
    if not table_exists(conn, 'docket_events'):
        print("  [SKIP] docket_events not found")
        return {}
    cols = get_columns(conn, 'docket_events')
    title_col = 'title' if 'title' in cols else None
    summary_col = 'summary' if 'summary' in cols else None
    if not title_col:
        print("  [SKIP] docket_events missing title")
        return {}

    rows = safe_query(conn, f"SELECT event_id, {title_col}, "
                            f"{summary_col or 'NULL'} AS summary, "
                            f"event_date_iso FROM docket_events")
    print(f"  docket_events: {len(rows)} rows loaded")

    mapping = defaultdict(lambda: {'andrew': [], 'emily': [], 'neutral': []})
    for row in rows:
        combined = ' '.join(str(row[c]) for c in dict(row).keys() if row[c])
        party = classify_party(combined)
        for fk in FACTORS:
            pos, neg = match_factor(combined, fk)
            if pos or neg:
                entry = {
                    'source': 'docket_events',
                    'event_id': row['event_id'],
                    'excerpt': str(row[title_col])[:200],
                    'date': row['event_date_iso'],
                    'positive_match': pos,
                    'negative_match': neg,
                }
                mapping[fk][party].append(entry)
    return dict(mapping)


def merge_mappings(*mappings):
    """Merge multiple factor mappings into one consolidated structure."""
    merged = {}
    for fk in FACTORS:
        merged[fk] = {'andrew': [], 'emily': [], 'neutral': []}
        for m in mappings:
            if fk in m:
                for party in ['andrew', 'emily', 'neutral']:
                    merged[fk][party].extend(m[fk].get(party, []))
    return merged


def compute_factor_scores(merged):
    """For each factor, compute evidence count and which parent is favored."""
    results = {}
    for fk, parties in merged.items():
        a_pos = sum(1 for e in parties['andrew'] if e.get('positive_match'))
        a_neg = sum(1 for e in parties['andrew'] if e.get('negative_match'))
        e_pos = sum(1 for e in parties['emily'] if e.get('positive_match'))
        e_neg = sum(1 for e in parties['emily'] if e.get('negative_match'))
        n_count = len(parties['neutral'])

        # Favorable evidence = positive mentions; unfavorable = negative mentions
        a_net = a_pos - a_neg + e_neg  # Emily's negatives favor Andrew
        e_net = e_pos - e_neg + a_neg  # Andrew's negatives favor Emily

        if a_net > e_net:
            favored = 'Andrew'
        elif e_net > a_net:
            favored = 'Emily'
        else:
            favored = 'Neutral/Insufficient'

        results[fk] = {
            'factor_letter': fk,
            'factor_name': FACTORS[fk]['name'],
            'andrew_evidence_count': len(parties['andrew']),
            'andrew_positive': a_pos,
            'andrew_negative': a_neg,
            'emily_evidence_count': len(parties['emily']),
            'emily_positive': e_pos,
            'emily_negative': e_neg,
            'neutral_count': n_count,
            'total_evidence': len(parties['andrew']) + len(parties['emily']) + n_count,
            'andrew_net_score': a_net,
            'emily_net_score': e_net,
            'favored_parent': favored,
            'top_evidence_andrew': parties['andrew'][:5],
            'top_evidence_emily': parties['emily'][:5],
        }
    return results


def generate_md(factor_scores, total_by_source):
    """Generate markdown report."""
    lines = [
        "# MCL 722.23 Best Interest Factor Map",
        f"**Generated:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
        f"**Case:** Pigors v. Watson — 2024-001507-DC",
        f"**Court:** 14th Circuit Court, Family Division, Muskegon County, MI",
        f"**Judge:** Hon. Jenny L. McNeill",
        "",
        "## Overview",
        "",
        "This report maps **all available evidence** in `litigation_context.db` to each",
        "of the 12 MCL 722.23 best interest factors. Each evidence item is classified",
        "by party (Andrew Pigors vs Emily Watson) and by factor relevance.",
        "",
        "### Evidence Sources Queried",
        "",
        "| Source | Records Scanned |",
        "|--------|----------------|",
    ]
    for src, cnt in sorted(total_by_source.items()):
        lines.append(f"| `{src}` | {cnt:,} |")

    # Summary table
    lines += [
        "",
        "## Factor Summary",
        "",
        "| Factor | Name | Andrew Evidence | Emily Evidence | Neutral | Total | Favored |",
        "|--------|------|----------------|----------------|---------|-------|---------|",
    ]
    andrew_favored = 0
    emily_favored = 0
    for fk in sorted(factor_scores.keys()):
        fs = factor_scores[fk]
        lines.append(
            f"| ({fk}) | {fs['factor_name']} | {fs['andrew_evidence_count']} "
            f"(+{fs['andrew_positive']}/-{fs['andrew_negative']}) | "
            f"{fs['emily_evidence_count']} (+{fs['emily_positive']}/-{fs['emily_negative']}) | "
            f"{fs['neutral_count']} | {fs['total_evidence']} | **{fs['favored_parent']}** |"
        )
        if fs['favored_parent'] == 'Andrew':
            andrew_favored += 1
        elif fs['favored_parent'] == 'Emily':
            emily_favored += 1

    neutral_count = 12 - andrew_favored - emily_favored
    lines += [
        "",
        f"### Scorecard: Andrew favored on **{andrew_favored}/12**, "
        f"Emily favored on **{emily_favored}/12**, "
        f"Neutral/Insufficient on **{neutral_count}/12**",
        "",
    ]

    # Detail per factor
    lines.append("## Detailed Factor Analysis")
    for fk in sorted(factor_scores.keys()):
        fs = factor_scores[fk]
        lines += [
            "",
            f"### Factor ({fk}): {fs['factor_name']}",
            f"- **Favored Parent:** {fs['favored_parent']}",
            f"- **Andrew net score:** {fs['andrew_net_score']} "
            f"(positive: {fs['andrew_positive']}, negative: {fs['andrew_negative']})",
            f"- **Emily net score:** {fs['emily_net_score']} "
            f"(positive: {fs['emily_positive']}, negative: {fs['emily_negative']})",
            f"- **Total evidence items:** {fs['total_evidence']}",
            "",
        ]
        if fs['top_evidence_andrew']:
            lines.append("**Top Andrew Evidence:**")
            for i, ev in enumerate(fs['top_evidence_andrew'][:3], 1):
                lines.append(f"  {i}. [{ev['source']}] {ev['excerpt']}")
            lines.append("")
        if fs['top_evidence_emily']:
            lines.append("**Top Emily Evidence:**")
            for i, ev in enumerate(fs['top_evidence_emily'][:3], 1):
                lines.append(f"  {i}. [{ev['source']}] {ev['excerpt']}")
            lines.append("")

    lines += [
        "---",
        "",
        "## Legal Authority",
        "",
        "- **MCL 722.23** — Child Custody Act, Best Interest Factors (a)-(l)",
        "- **MCL 722.27** — Modification requires proper cause or change of circumstances",
        "- **Vodvarka v Grasmeyer, 259 Mich App 499 (2003)** — Established custodial environment",
        "- **Fletcher v Fletcher, 447 Mich 871 (1994)** — Best interest factor weighing",
        "- **Ireland v Smith, 451 Mich 457 (1996)** — Equal weight to all factors",
        "",
        "---",
        f"*Generated by Tool #251 — MCL 722.23 Best Interest Factor Mapper*",
    ]
    return '\n'.join(lines)


def main():
    print("=" * 70)
    print("TOOL #251: MCL 722.23 BEST INTEREST FACTOR MAPPER")
    print("=" * 70)
    print(f"DB: {DB_PATH}")
    print(f"Reports: {REPORTS_DIR}")
    print()

    if not os.path.exists(DB_PATH):
        print(f"[FATAL] Database not found: {DB_PATH}")
        sys.exit(1)

    conn = connect_db()

    # Verify tables exist before querying
    required = ['evidence_quotes', 'd_drive_events', 'claims', 'docket_events']
    for t in required:
        if table_exists(conn, t):
            cols = get_columns(conn, t)
            print(f"  [OK] {t}: {len(cols)} columns")
        else:
            print(f"  [MISS] {t}: table not found — will skip")

    print("\n[1/5] Mapping evidence_quotes to factors...")
    eq_map = map_evidence_quotes(conn)

    print("[2/5] Mapping d_drive_events to factors...")
    dd_map = map_d_drive_events(conn)

    print("[3/5] Mapping claims to factors...")
    cl_map = map_claims(conn)

    print("[4/5] Mapping docket_events to factors...")
    de_map = map_docket_events(conn)

    print("[5/5] Merging and scoring...")
    merged = merge_mappings(eq_map, dd_map, cl_map, de_map)
    factor_scores = compute_factor_scores(merged)

    # Count totals by source
    total_by_source = {}
    for tbl in required:
        if table_exists(conn, tbl):
            cnt = conn.execute(f"SELECT COUNT(*) FROM [{tbl}]").fetchone()[0]
            total_by_source[tbl] = cnt

    # Generate reports
    md_report = generate_md(factor_scores, total_by_source)
    md_path = os.path.join(REPORTS_DIR, 'BEST_INTEREST_FACTOR_MAP.md')
    with open(md_path, 'w', encoding='utf-8') as f:
        f.write(md_report)
    print(f"\n[OK] Markdown report: {md_path}")

    json_data = {
        'tool': '#251 MCL 722.23 Best Interest Factor Mapper',
        'generated': datetime.now().isoformat(),
        'case': 'Pigors v. Watson — 2024-001507-DC',
        'sources_scanned': total_by_source,
        'factor_scores': factor_scores,
    }
    json_path = os.path.join(REPORTS_DIR, 'best_interest_factor_map.json')
    with open(json_path, 'w', encoding='utf-8') as f:
        json.dump(json_data, f, indent=2, default=str)
    print(f"[OK] JSON report: {json_path}")

    # Print summary
    print("\n" + "=" * 70)
    print("FACTOR SCORECARD")
    print("=" * 70)
    a_fav = sum(1 for fs in factor_scores.values() if fs['favored_parent'] == 'Andrew')
    e_fav = sum(1 for fs in factor_scores.values() if fs['favored_parent'] == 'Emily')
    n_fav = 12 - a_fav - e_fav
    for fk in sorted(factor_scores.keys()):
        fs = factor_scores[fk]
        marker = ">>>" if fs['favored_parent'] == 'Andrew' else "   "
        print(f"  {marker} ({fk}) {fs['factor_name'][:45]:<45} => {fs['favored_parent']:<20} "
              f"[A:{fs['andrew_evidence_count']} E:{fs['emily_evidence_count']}]")
    print(f"\n  TOTAL: Andrew={a_fav}  Emily={e_fav}  Neutral={n_fav}")
    total_ev = sum(fs['total_evidence'] for fs in factor_scores.values())
    print(f"  Evidence items mapped: {total_ev:,}")
    print("=" * 70)

    conn.close()
    return 0


if __name__ == '__main__':
    sys.exit(main())
