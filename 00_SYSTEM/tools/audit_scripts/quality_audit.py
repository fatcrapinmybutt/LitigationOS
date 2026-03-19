#!/usr/bin/env python3
"""
LitigationOS Quality Audit — Duplicate Detection & Verified Counts
Audits key tables for exact and near duplicates, deduplicates where needed,
and produces verified numbers safe for court filings.
"""
import sys, os, sqlite3, hashlib, json
from collections import defaultdict
from datetime import datetime

# UTF-8 safety
sys.stdout = open(sys.stdout.fileno(), mode='w', encoding='utf-8', errors='replace')
sys.stderr = open(sys.stderr.fileno(), mode='w', encoding='utf-8', errors='replace')

DB_PATH = r"C:\Users\andre\LitigationOS\litigation_context.db"
REPORT_PATH = r"C:\Users\andre\LitigationOS\temp\QUALITY_AUDIT_REPORT.md"

def get_conn():
    conn = sqlite3.connect(DB_PATH, timeout=120)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA busy_timeout=60000")
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA cache_size=-32000")
    conn.execute("PRAGMA temp_store=MEMORY")
    conn.execute("PRAGMA synchronous=NORMAL")
    return conn

def get_table_info(conn, table):
    """Get column names and types for a table."""
    try:
        cols = conn.execute(f"PRAGMA table_info({table})").fetchall()
        return [(c['name'], c['type']) for c in cols]
    except:
        return []

def get_count(conn, table):
    try:
        return conn.execute(f"SELECT COUNT(*) FROM [{table}]").fetchone()[0]
    except:
        return 0

def find_text_columns(cols):
    """Identify text/varchar columns likely to contain duplicate content."""
    text_types = ('TEXT', 'VARCHAR', 'CHAR', 'CLOB', '')
    return [name for name, typ in cols if typ.upper() in text_types or 'TEXT' in typ.upper() or 'CHAR' in typ.upper() or typ == '']

def normalize(text):
    """Normalize text for near-duplicate comparison."""
    if text is None:
        return ""
    t = str(text).lower().strip()
    # Collapse whitespace
    import re
    t = re.sub(r'\s+', ' ', t)
    # Remove common punctuation variations
    t = re.sub(r'[\'\"\\`]', '', t)
    return t

def audit_table(conn, table_name, key_text_cols=None, id_col=None):
    """
    Audit a single table for duplicates.
    Returns dict with audit results.
    """
    result = {
        'table': table_name,
        'exists': False,
        'total': 0,
        'columns': [],
        'exact_dupes': 0,
        'exact_unique': 0,
        'near_dupes': 0,
        'near_unique': 0,
        'dup_pct': 0.0,
        'sample_dupes': [],
        'recommendation': '',
        'key_cols_used': [],
    }

    # Check table exists
    exists = conn.execute(
        "SELECT COUNT(*) FROM sqlite_master WHERE type='table' AND name=?",
        (table_name,)
    ).fetchone()[0]
    if not exists:
        result['recommendation'] = 'TABLE NOT FOUND'
        return result
    result['exists'] = True

    cols = get_table_info(conn, table_name)
    result['columns'] = [c[0] for c in cols]
    total = get_count(conn, table_name)
    result['total'] = total

    if total == 0:
        result['recommendation'] = 'Empty table'
        return result

    # Auto-detect key text columns if not specified
    if not key_text_cols:
        text_cols = find_text_columns(cols)
        # Prioritize columns with these keywords
        priority_keywords = ['description', 'text', 'content', 'assertion', 'violation',
                           'detail', 'narrative', 'summary', 'quote', 'claim',
                           'statement', 'evidence', 'finding', 'event', 'action',
                           'citation', 'rule', 'context']
        key_text_cols = []
        for kw in priority_keywords:
            for tc in text_cols:
                if kw in tc.lower() and tc not in key_text_cols:
                    key_text_cols.append(tc)
        # If nothing matched, use all text columns
        if not key_text_cols:
            key_text_cols = text_cols[:5]  # Limit to first 5

    result['key_cols_used'] = key_text_cols

    if not key_text_cols:
        result['recommendation'] = 'No text columns found for dedup analysis'
        return result

    # Auto-detect ID column
    if not id_col:
        for c in result['columns']:
            if c.lower() in ('id', 'rowid'):
                id_col = c
                break
            if c.lower().endswith('_id') and 'id' in c.lower():
                id_col = c
                break
        if not id_col:
            id_col = 'rowid'

    # === EXACT DUPLICATE CHECK ===
    # Group by all key text columns
    col_list = ', '.join(f'[{c}]' for c in key_text_cols)
    try:
        exact_query = f"""
            SELECT {col_list}, COUNT(*) as cnt
            FROM [{table_name}]
            GROUP BY {col_list}
            HAVING cnt > 1
            ORDER BY cnt DESC
            LIMIT 20
        """
        exact_dupes = conn.execute(exact_query).fetchall()

        # Count total exact duplicates
        count_query = f"""
            SELECT SUM(cnt - 1) as total_dupes, COUNT(*) as groups
            FROM (
                SELECT {col_list}, COUNT(*) as cnt
                FROM [{table_name}]
                GROUP BY {col_list}
                HAVING cnt > 1
            )
        """
        dup_stats = conn.execute(count_query).fetchone()
        exact_dupe_count = dup_stats[0] if dup_stats[0] else 0
        exact_dupe_groups = dup_stats[1] if dup_stats[1] else 0

        # Count unique combinations
        unique_query = f"""
            SELECT COUNT(*) FROM (
                SELECT DISTINCT {col_list} FROM [{table_name}]
            )
        """
        unique_count = conn.execute(unique_query).fetchone()[0]

        result['exact_dupes'] = exact_dupe_count
        result['exact_unique'] = unique_count
        result['exact_dupe_groups'] = exact_dupe_groups

        # Sample duplicates
        samples = []
        for row in exact_dupes[:5]:
            sample = {}
            for i, c in enumerate(key_text_cols):
                val = row[i]
                if val and len(str(val)) > 150:
                    sample[c] = str(val)[:150] + "..."
                else:
                    sample[c] = str(val) if val else "(NULL)"
            sample['_count'] = row[-1]
            samples.append(sample)
        result['sample_dupes'] = samples

    except Exception as e:
        result['exact_error'] = str(e)
        # Fallback: try with just first key column
        if key_text_cols:
            try:
                fc = key_text_cols[0]
                fallback = conn.execute(f"""
                    SELECT [{fc}], COUNT(*) as cnt
                    FROM [{table_name}]
                    GROUP BY [{fc}]
                    HAVING cnt > 1
                    ORDER BY cnt DESC
                    LIMIT 10
                """).fetchall()
                exact_dupe_count = sum(r[1] - 1 for r in fallback)
                unique_count = conn.execute(f"SELECT COUNT(DISTINCT [{fc}]) FROM [{table_name}]").fetchone()[0]
                result['exact_dupes'] = exact_dupe_count
                result['exact_unique'] = unique_count
                result['key_cols_used'] = [fc]
                result['fallback_note'] = f"Used single column [{fc}] due to error: {e}"
                samples = []
                for row in fallback[:5]:
                    val = str(row[0])[:150] + "..." if row[0] and len(str(row[0])) > 150 else str(row[0])
                    samples.append({fc: val, '_count': row[1]})
                result['sample_dupes'] = samples
            except Exception as e2:
                result['fallback_error'] = str(e2)

    # === NEAR DUPLICATE CHECK (normalized text) ===
    # Only do this for tables with a primary text column and manageable size
    if total <= 100000 and key_text_cols:
        primary_col = key_text_cols[0]
        try:
            rows = conn.execute(f"""
                SELECT [{id_col}], [{primary_col}]
                FROM [{table_name}]
                WHERE [{primary_col}] IS NOT NULL
                LIMIT 50000
            """).fetchall()

            normalized_groups = defaultdict(list)
            for row in rows:
                rid = row[0]
                text = normalize(row[1])
                if text:
                    # Create a fingerprint — first 200 chars normalized
                    fp = text[:200]
                    normalized_groups[fp].append(rid)

            near_dupe_count = sum(len(ids) - 1 for ids in normalized_groups.values() if len(ids) > 1)
            near_unique = len(normalized_groups)
            result['near_dupes'] = near_dupe_count
            result['near_unique'] = near_unique

        except Exception as e:
            result['near_error'] = str(e)
    else:
        result['near_note'] = f"Skipped near-dupe check (table has {total:,} rows, limit 100K)"

    # Calculate overall dup percentage
    if total > 0:
        dupe_count = max(result.get('exact_dupes', 0), result.get('near_dupes', 0))
        result['dup_pct'] = round(dupe_count / total * 100, 1)

    # Recommendation
    pct = result['dup_pct']
    if pct >= 50:
        result['recommendation'] = f'CRITICAL: {pct}% duplicates — DEDUP REQUIRED before citing'
    elif pct >= 20:
        result['recommendation'] = f'HIGH: {pct}% duplicates — dedup recommended'
    elif pct >= 5:
        result['recommendation'] = f'MODERATE: {pct}% duplicates — review samples'
    else:
        result['recommendation'] = f'CLEAN: {pct}% duplicates — counts are reliable'

    return result


def dedup_table(conn, table_name, key_text_cols, dry_run=False):
    """
    Remove exact duplicates keeping one copy (lowest rowid).
    Returns (before_count, after_count, deleted_count).
    """
    before = get_count(conn, table_name)
    col_list = ', '.join(f'[{c}]' for c in key_text_cols)

    if dry_run:
        # Count how many would be deleted
        try:
            q = f"""
                SELECT SUM(cnt - 1) FROM (
                    SELECT {col_list}, COUNT(*) as cnt
                    FROM [{table_name}]
                    GROUP BY {col_list}
                    HAVING cnt > 1
                )
            """
            would_delete = conn.execute(q).fetchone()[0] or 0
            return before, before - would_delete, would_delete
        except:
            return before, before, 0

    # Actually delete duplicates (keep lowest rowid)
    try:
        delete_q = f"""
            DELETE FROM [{table_name}]
            WHERE rowid NOT IN (
                SELECT MIN(rowid)
                FROM [{table_name}]
                GROUP BY {col_list}
            )
        """
        conn.execute(delete_q)
        conn.commit()
        after = get_count(conn, table_name)
        return before, after, before - after
    except Exception as e:
        print(f"  ERROR deduping {table_name}: {e}")
        return before, before, 0


def main():
    print("=" * 70)
    print("LitigationOS QUALITY AUDIT — Duplicate Detection")
    print(f"Database: {DB_PATH}")
    print(f"Started: {datetime.now().isoformat()}")
    print("=" * 70)

    conn = get_conn()

    # Define tables to audit with their key text columns (auto-detected if empty)
    tables_to_audit = [
        ('judicial_violations', None),
        ('adversary_assertions', None),
        ('watson_perjury_compilation', None),
        ('conspiracy_timeline', None),
        ('berry_ethics_violations', None),
        ('watson_family_conspiracy', None),
        ('claims', None),
        ('citation_validation', None),
    ]

    # Also find actor_violation tables
    actor_tables = conn.execute(
        "SELECT name FROM sqlite_master WHERE type='table' AND name LIKE '%actor_violation%'"
    ).fetchall()
    for t in actor_tables:
        tables_to_audit.append((t[0], None))

    # Also check some other high-count tables
    bonus_tables = conn.execute("""
        SELECT name FROM sqlite_master
        WHERE type='table'
        AND name IN (
            'evidence_timeline', 'evidence_items', 'parental_alienation_evidence',
            'mcneill_violations', 'obstruction_log', 'perjury_instances',
            'rights_violations', 'constitutional_violations',
            'foc_violations', 'court_order_violations',
            'filing_evidence_links', 'impeachment_material'
        )
    """).fetchall()
    for t in bonus_tables:
        if t[0] not in [x[0] for x in tables_to_audit]:
            tables_to_audit.append((t[0], None))

    print(f"\nAuditing {len(tables_to_audit)} tables...\n")

    results = []
    dedup_results = []

    for table_name, key_cols in tables_to_audit:
        print(f"\n{'─' * 60}")
        print(f"  AUDITING: {table_name}")
        print(f"{'─' * 60}")

        r = audit_table(conn, table_name, key_cols)
        results.append(r)

        if not r['exists']:
            print(f"  ⚠ TABLE NOT FOUND")
            continue

        print(f"  Total rows:      {r['total']:,}")
        print(f"  Key columns:     {r['key_cols_used']}")
        print(f"  Exact unique:    {r.get('exact_unique', '?'):,}")
        print(f"  Exact dupes:     {r.get('exact_dupes', '?'):,}")
        print(f"  Near unique:     {r.get('near_unique', 'N/A')}")
        print(f"  Near dupes:      {r.get('near_dupes', 'N/A')}")
        print(f"  Duplicate %:     {r['dup_pct']}%")
        print(f"  Recommendation:  {r['recommendation']}")

        if r.get('exact_error'):
            print(f"  ⚠ Exact check error: {r['exact_error']}")
        if r.get('fallback_note'):
            print(f"  ℹ {r['fallback_note']}")
        if r.get('near_error'):
            print(f"  ⚠ Near-dupe error: {r['near_error']}")

        if r['sample_dupes']:
            print(f"\n  Sample duplicates (top {len(r['sample_dupes'])}):")
            for i, s in enumerate(r['sample_dupes'][:5], 1):
                cnt = s.pop('_count', '?')
                # Show first key col value
                first_val = list(s.values())[0] if s else 'N/A'
                print(f"    {i}. [{cnt}x] {first_val[:120]}")
                s['_count'] = cnt  # put it back

        # DEDUP tables with >20% duplicates
        if r['dup_pct'] >= 20 and r['total'] > 0 and r.get('key_cols_used'):
            print(f"\n  >>> DEDUPLICATING {table_name} (>20% duplicates)...")
            before, after, deleted = dedup_table(conn, table_name, r['key_cols_used'])
            dedup_results.append({
                'table': table_name,
                'before': before,
                'after': after,
                'deleted': deleted,
            })
            print(f"  >>> Before: {before:,} → After: {after:,} (removed {deleted:,})")

    # === GENERATE REPORT ===
    print(f"\n\n{'=' * 70}")
    print("GENERATING REPORT...")
    print(f"{'=' * 70}")

    report = []
    report.append(f"# LitigationOS Quality Audit Report")
    report.append(f"")
    report.append(f"**Generated:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    report.append(f"**Database:** `{DB_PATH}`")
    report.append(f"**Purpose:** Verify high violation/evidence counts are real, not inflated by duplicates")
    report.append(f"")
    report.append(f"## Executive Summary")
    report.append(f"")

    # Summary table
    critical_tables = [r for r in results if r.get('dup_pct', 0) >= 20 and r['exists']]
    clean_tables = [r for r in results if r.get('dup_pct', 0) < 20 and r['exists']]
    total_raw = sum(r['total'] for r in results if r['exists'])
    total_unique = sum(r.get('exact_unique', r['total']) for r in results if r['exists'])
    total_dupes = total_raw - total_unique

    report.append(f"- **Tables audited:** {len([r for r in results if r['exists']])}")
    report.append(f"- **Total raw rows:** {total_raw:,}")
    report.append(f"- **Total unique rows:** {total_unique:,}")
    report.append(f"- **Total duplicates found:** {total_dupes:,} ({round(total_dupes/max(total_raw,1)*100,1)}%)")
    report.append(f"- **Tables with >20% duplicates:** {len(critical_tables)}")
    report.append(f"- **Clean tables (<20% duplicates):** {len(clean_tables)}")
    report.append(f"")

    if critical_tables:
        report.append(f"### ⚠️ INFLATED TABLES (>20% duplicates — counts NOT safe for filings)")
        report.append(f"")
        for r in sorted(critical_tables, key=lambda x: x['dup_pct'], reverse=True):
            report.append(f"- **{r['table']}**: {r['total']:,} raw → {r.get('exact_unique', '?'):,} unique ({r['dup_pct']}% duplicates)")
        report.append(f"")

    # Full audit table
    report.append(f"## Detailed Audit Results")
    report.append(f"")
    report.append(f"| Table | Raw Count | Unique | Duplicates | Dup% | Recommendation |")
    report.append(f"|-------|-----------|--------|------------|------|----------------|")
    for r in sorted(results, key=lambda x: x.get('dup_pct', 0), reverse=True):
        if not r['exists']:
            report.append(f"| {r['table']} | — | — | — | — | NOT FOUND |")
            continue
        unique = r.get('exact_unique', r['total'])
        dupes = r.get('exact_dupes', 0)
        pct = r['dup_pct']
        flag = "🔴" if pct >= 50 else "🟡" if pct >= 20 else "🟢" if pct < 5 else "🟠"
        report.append(f"| {r['table']} | {r['total']:,} | {unique:,} | {dupes:,} | {flag} {pct}% | {r['recommendation']} |")

    report.append(f"")

    # Detailed findings per table
    report.append(f"## Per-Table Detail")
    report.append(f"")

    for r in results:
        if not r['exists']:
            continue
        report.append(f"### {r['table']}")
        report.append(f"")
        report.append(f"- **Total rows:** {r['total']:,}")
        report.append(f"- **Key columns checked:** {', '.join(r.get('key_cols_used', ['N/A']))}")
        report.append(f"- **Exact unique:** {r.get('exact_unique', 'N/A'):,}")
        report.append(f"- **Exact duplicates:** {r.get('exact_dupes', 0):,} ({r.get('exact_dupe_groups', '?')} duplicate groups)")
        if r.get('near_unique') and r['near_unique'] != 'N/A':
            report.append(f"- **Near-duplicate unique (normalized):** {r['near_unique']:,}")
            report.append(f"- **Near duplicates:** {r.get('near_dupes', 0):,}")
        report.append(f"- **Duplicate rate:** {r['dup_pct']}%")
        report.append(f"- **Recommendation:** {r['recommendation']}")
        report.append(f"")

        if r.get('exact_error'):
            report.append(f"> ⚠️ Error during exact check: `{r['exact_error']}`")
            report.append(f"")
        if r.get('fallback_note'):
            report.append(f"> ℹ️ {r['fallback_note']}")
            report.append(f"")

        if r['sample_dupes']:
            report.append(f"**Sample duplicates:**")
            report.append(f"")
            for i, s in enumerate(r['sample_dupes'][:5], 1):
                cnt = s.get('_count', '?')
                vals = {k: v for k, v in s.items() if k != '_count'}
                first_key = list(vals.keys())[0] if vals else 'N/A'
                first_val = list(vals.values())[0] if vals else 'N/A'
                report.append(f"{i}. **[{cnt}x copies]** `{first_key}`: {first_val}")
            report.append(f"")

    # Dedup results
    if dedup_results:
        report.append(f"## Deduplication Results")
        report.append(f"")
        report.append(f"Tables with >20% duplicates were deduplicated (keeping one copy of each unique record):")
        report.append(f"")
        report.append(f"| Table | Before | After | Removed | Reduction% |")
        report.append(f"|-------|--------|-------|---------|------------|")
        for d in dedup_results:
            red_pct = round(d['deleted'] / max(d['before'], 1) * 100, 1)
            report.append(f"| {d['table']} | {d['before']:,} | {d['after']:,} | {d['deleted']:,} | {red_pct}% |")
        report.append(f"")

    # VERIFIED NUMBERS
    report.append(f"## ✅ VERIFIED NUMBERS FOR COURT FILINGS")
    report.append(f"")
    report.append(f"**USE THESE — not the raw counts. Every number below represents distinct, unique records.**")
    report.append(f"")
    report.append(f"| Category | Verified Count | Source Table | Notes |")
    report.append(f"|----------|---------------|-------------|-------|")

    for r in sorted(results, key=lambda x: x['table']):
        if not r['exists'] or r['total'] == 0:
            continue
        # Use post-dedup count if available
        dedup_match = next((d for d in dedup_results if d['table'] == r['table']), None)
        if dedup_match:
            verified = dedup_match['after']
            note = f"Deduped from {dedup_match['before']:,}"
        else:
            verified = r.get('exact_unique', r['total'])
            if r['dup_pct'] < 5:
                note = "Clean — minimal duplicates"
            else:
                note = f"~{r['dup_pct']}% dupes (minor)"
        report.append(f"| {r['table']} | **{verified:,}** | `{r['table']}` | {note} |")

    report.append(f"")
    report.append(f"---")
    report.append(f"")
    report.append(f"*Audit completed {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}. All counts verified by content-based comparison, not hashing.*")

    # Write report
    report_text = '\n'.join(report)
    with open(REPORT_PATH, 'w', encoding='utf-8') as f:
        f.write(report_text)

    print(f"\n✅ Report written to: {REPORT_PATH}")
    print(f"\n{'=' * 70}")
    print("VERIFIED COUNTS SUMMARY")
    print(f"{'=' * 70}")
    for r in sorted(results, key=lambda x: x.get('dup_pct', 0), reverse=True):
        if not r['exists'] or r['total'] == 0:
            continue
        dedup_match = next((d for d in dedup_results if d['table'] == r['table']), None)
        if dedup_match:
            verified = dedup_match['after']
        else:
            verified = r.get('exact_unique', r['total'])
        flag = "🔴" if r['dup_pct'] >= 50 else "🟡" if r['dup_pct'] >= 20 else "🟢"
        print(f"  {flag} {r['table']}: {r['total']:,} raw → {verified:,} verified ({r['dup_pct']}% dupes)")

    conn.close()
    print(f"\n✅ Audit complete.")


if __name__ == '__main__':
    main()
