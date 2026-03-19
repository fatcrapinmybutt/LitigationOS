#!/usr/bin/env python3
"""
Tool #225: Witness Credibility Scorer
Scores each witness's credibility based on the evidence record.
Calculates consistency, corroboration, contradiction count, bias indicators,
and prior false statements.

Output: WITNESS_CREDIBILITY.md + witness_credibility.json
"""
import sys
import os
import json
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

# Key witnesses to evaluate
KEY_WITNESSES = [
    {'name': 'Emily Watson', 'aliases': ['Emily Watson', 'Emily A. Watson', 'Tiffany Watson',
                                          'Tiffany Emily Watson', 'Watson', 'Emily'],
     'role': 'Defendant / Mother', 'relationship': 'Opposing party',
     'motive_to_lie': 'Retain sole custody; justify parenting time denial'},
    {'name': 'Albert Watson', 'aliases': ['Albert Watson', 'Al Watson', 'Albert'],
     'role': "Defendant's Father", 'relationship': "Emily's father",
     'motive_to_lie': 'Protect daughter; prior aggressive behavior documented'},
    {'name': 'Lori Watson', 'aliases': ['Lori Watson', 'Lori'],
     'role': "Defendant's Mother", 'relationship': "Emily's mother",
     'motive_to_lie': "Support daughter's custody claims"},
    {'name': 'Cody Watson', 'aliases': ['Cody Watson', 'Cody'],
     'role': "Defendant's Brother", 'relationship': "Emily's brother",
     'motive_to_lie': "Family loyalty; support Emily's narrative"},
    {'name': 'Ronald Berry', 'aliases': ['Ronald Berry', 'Ron Berry', 'Berry'],
     'role': "Emily's Domestic Partner (NON-ATTORNEY)", 'relationship': "Emily's boyfriend",
     'motive_to_lie': 'Protect partner; potential UPL exposure'},
    {'name': 'Pamela Rusco', 'aliases': ['Pamela Rusco', 'Rusco', 'Pam Rusco'],
     'role': 'Friend of Court', 'relationship': 'Court official',
     'motive_to_lie': 'Institutional alignment with judge'},
    {'name': 'Michelle Mitchell', 'aliases': ['Michelle Mitchell', 'Mitchell'],
     'role': 'HealthWest Evaluator', 'relationship': 'Court-appointed evaluator',
     'motive_to_lie': 'Responded to judicial pressure (biasing letter)'},
    {'name': 'Jennifer Barnes', 'aliases': ['Jennifer Barnes', 'Barnes', 'Jennifer L. Barnes'],
     'role': "Emily's Former Attorney (P55406, WITHDREW)", 'relationship': "Emily's attorney",
     'motive_to_lie': 'Client advocacy; ethical obligations limit scope'},
]


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


def build_alias_where(aliases, column):
    """Build a WHERE clause matching any alias."""
    clauses = []
    for alias in aliases:
        clauses.append(f"{column} LIKE '%{alias}%'")
    return " OR ".join(clauses)


def score_witness(conn, witness):
    """Score a single witness's credibility."""
    aliases = witness['aliases']
    name = witness['name']
    result = {
        'name': name,
        'role': witness['role'],
        'relationship': witness['relationship'],
        'motive_to_lie': witness['motive_to_lie'],
        'consistency_score': 0.0,
        'corroboration_score': 0.0,
        'contradiction_count': 0,
        'impeachment_count': 0,
        'perjury_count': 0,
        'bias_indicators': [],
        'prior_false_statements': [],
        'evidence_appearances': 0,
        'credibility_score': 0.0,
        'credibility_grade': '',
        'key_findings': [],
    }

    # --- 1. Count contradictions from detected_contradictions ---
    if table_exists(conn, 'detected_contradictions'):
        where = build_alias_where(aliases, 'speaker')
        rows = safe_query(conn, f"""
            SELECT speaker, statement_1, source_1, statement_2, source_2,
                   contradiction_type, severity, impeachment_value
            FROM detected_contradictions
            WHERE {where}
        """)
        result['contradiction_count'] = len(rows)
        for r in rows[:5]:
            result['prior_false_statements'].append({
                'statement_1': str(r['statement_1'])[:150],
                'source_1': str(r['source_1'])[:80],
                'statement_2': str(r['statement_2'])[:150],
                'source_2': str(r['source_2'])[:80],
                'type': r['contradiction_type'],
                'severity': r['severity'],
            })

    # --- 2. Count impeachment items ---
    if table_exists(conn, 'impeachment_items'):
        where = build_alias_where(aliases, 'speaker')
        rows = safe_query(conn, f"SELECT COUNT(*) as cnt FROM impeachment_items WHERE {where}")
        result['impeachment_count'] = rows[0][0] if rows else 0

    # --- 3. Count impeachment index entries ---
    if table_exists(conn, 'impeachment_index'):
        where = build_alias_where(aliases, 'target_witness')
        rows = safe_query(conn, f"""
            SELECT target_witness, statement_a, source_a, statement_b, source_b,
                   contradiction_type, impeachment_value, legal_use
            FROM impeachment_index
            WHERE {where}
        """)
        for r in rows:
            result['key_findings'].append({
                'type': 'IMPEACHMENT_INDEX',
                'contradiction_type': r['contradiction_type'],
                'value': r['impeachment_value'],
                'statement_a': str(r['statement_a'])[:150],
                'statement_b': str(r['statement_b'])[:150],
                'legal_use': str(r['legal_use'])[:200] if r['legal_use'] else '',
            })

    # --- 4. Perjury compilation (Watson family) ---
    if table_exists(conn, 'watson_perjury_compilation'):
        where = build_alias_where(aliases, 'watson_member')
        rows = safe_query(conn, f"""
            SELECT COUNT(*) as cnt FROM watson_perjury_compilation WHERE {where}
        """)
        result['perjury_count'] = rows[0][0] if rows else 0

        # Get top perjury entries
        top_perjury = safe_query(conn, f"""
            SELECT watson_member, statement_text, contradicting_evidence,
                   perjury_type, severity_score, mcr_mre_authority
            FROM watson_perjury_compilation
            WHERE ({where}) AND severity_score >= 4
            ORDER BY severity_score DESC
            LIMIT 5
        """)
        for r in top_perjury:
            result['prior_false_statements'].append({
                'statement_1': str(r['statement_text'])[:150],
                'source_1': 'watson_perjury_compilation',
                'statement_2': str(r['contradicting_evidence'])[:150],
                'source_2': str(r['mcr_mre_authority'])[:80] if r['mcr_mre_authority'] else '',
                'type': r['perjury_type'],
                'severity': str(r['severity_score']),
            })

    # --- 5. Evidence appearances (evidence_quotes) ---
    if table_exists(conn, 'evidence_quotes'):
        cols = get_columns(conn, 'evidence_quotes')
        if 'speaker' in cols:
            where = build_alias_where(aliases, 'speaker')
            rows = safe_query(conn, f"SELECT COUNT(*) as cnt FROM evidence_quotes WHERE {where}")
            result['evidence_appearances'] = rows[0][0] if rows else 0

    # --- 6. Contradiction map references ---
    if table_exists(conn, 'contradiction_map'):
        where_a = build_alias_where(aliases, 'source_a_text')
        where_b = build_alias_where(aliases, 'source_b_text')
        rows = safe_query(conn, f"""
            SELECT COUNT(*) as cnt FROM contradiction_map
            WHERE ({where_a}) OR ({where_b})
        """)
        contradiction_map_count = rows[0][0] if rows else 0
        if contradiction_map_count > 0:
            result['bias_indicators'].append(
                f"Referenced in {contradiction_map_count} contradiction map entries"
            )

    # --- 7. Berry-specific investigation ---
    if 'Berry' in name:
        if table_exists(conn, 'berry_investigation'):
            rows = safe_query(conn, "SELECT source, evidence_text, strength FROM berry_investigation")
            for r in rows:
                result['key_findings'].append({
                    'type': 'BERRY_INVESTIGATION',
                    'source': r['source'],
                    'evidence': str(r['evidence_text'])[:200],
                    'strength': r['strength'],
                })
        if table_exists(conn, 'berry_ethics_violations'):
            rows = safe_query(conn, "SELECT COUNT(*) as cnt FROM berry_ethics_violations")
            ethics_count = rows[0][0] if rows else 0
            if ethics_count > 0:
                result['bias_indicators'].append(
                    f"{ethics_count} ethics violations documented (MRPC violations)"
                )
                result['key_findings'].append({
                    'type': 'ETHICS_VIOLATIONS',
                    'count': ethics_count,
                    'source': 'berry_ethics_violations',
                })

    # --- 8. Witness database/profiles ---
    if table_exists(conn, 'witness_profiles'):
        for alias in aliases:
            rows = safe_query(conn, """
                SELECT name, credibility_score, testimony_count, impeachment_count, notes
                FROM witness_profiles WHERE name LIKE ?
            """, (f'%{alias}%',))
            if rows:
                r = rows[0]
                if r['credibility_score']:
                    result['key_findings'].append({
                        'type': 'PROFILE_SCORE',
                        'existing_credibility': r['credibility_score'],
                        'testimony_count': r['testimony_count'],
                        'notes': str(r['notes'])[:200] if r['notes'] else '',
                    })
                break

    # --- 9. AppClose violations (for Emily) ---
    if 'Watson' in name or 'Emily' in name:
        if table_exists(conn, 'appclose_violations'):
            rows = safe_query(conn, "SELECT COUNT(*) as cnt FROM appclose_violations")
            appclose_count = rows[0][0] if rows else 0
            if appclose_count > 0:
                result['bias_indicators'].append(
                    f"{appclose_count} AppClose co-parenting violations documented"
                )

    # --- 10. Alienation scoring (for Emily/Watson family) ---
    if any(w in name for w in ['Watson', 'Emily', 'Albert', 'Lori', 'Cody']):
        if table_exists(conn, 'alienation_scoring'):
            rows = safe_query(conn, "SELECT SUM(score) as total, SUM(max_score) as max_total FROM alienation_scoring")
            if rows and rows[0]['total']:
                result['bias_indicators'].append(
                    f"Alienation scoring: {rows[0]['total']}/{rows[0]['max_total']} "
                    f"(family pattern)"
                )

    # --- Calculate composite credibility score ---
    # Start at 10 (perfect), deduct for issues
    base = 10.0
    deductions = 0.0

    # Contradiction penalty (each contradiction = -0.1, capped)
    deductions += min(3.0, result['contradiction_count'] * 0.05)

    # Impeachment penalty
    deductions += min(3.0, result['impeachment_count'] * 0.01)

    # Perjury penalty (serious)
    deductions += min(3.0, result['perjury_count'] * 0.02)

    # Bias penalty (motive to lie)
    if result['motive_to_lie']:
        deductions += 0.5

    # Prior false statements penalty
    deductions += min(1.5, len(result['prior_false_statements']) * 0.3)

    # Consistency score (inverse of contradictions)
    max_contradictions = max(result['contradiction_count'], 1)
    result['consistency_score'] = round(max(0, 10.0 - (result['contradiction_count'] * 0.1)), 1)

    # Corroboration score (based on evidence appearances vs contradictions)
    if result['evidence_appearances'] > 0:
        corr_ratio = max(0, result['evidence_appearances'] - result['contradiction_count']) / \
                     max(1, result['evidence_appearances'])
        result['corroboration_score'] = round(corr_ratio * 10, 1)
    else:
        result['corroboration_score'] = 5.0  # neutral if no data

    final_score = round(max(0, min(10, base - deductions)), 1)
    result['credibility_score'] = final_score

    # Grade
    if final_score >= 8.0:
        result['credibility_grade'] = 'A (Highly Credible)'
    elif final_score >= 6.0:
        result['credibility_grade'] = 'B (Generally Credible)'
    elif final_score >= 4.0:
        result['credibility_grade'] = 'C (Questionable Credibility)'
    elif final_score >= 2.0:
        result['credibility_grade'] = 'D (Low Credibility)'
    else:
        result['credibility_grade'] = 'F (Not Credible)'

    return result


def generate_md(scores, summary):
    """Generate markdown report."""
    lines = []
    lines.append("# WITNESS CREDIBILITY REPORT")
    lines.append(f"\n**Generated:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    lines.append(f"**Case:** Pigors v. Watson (2024-001507-DC)")
    lines.append(f"**Court:** 14th Circuit Court, Family Division, Muskegon County")
    lines.append(f"**Database:** litigation_context.db")
    lines.append(f"\n**Methodology:** Credibility scores are computed from DB evidence: "
                 "contradictions, impeachment items, perjury records, bias indicators, "
                 "and corroboration metrics. Base score is 10.0, with deductions for "
                 "documented inconsistencies. All statistics are traceable to specific "
                 "DB tables and queries.")

    # Summary table
    lines.append("\n## CREDIBILITY SCORECARD\n")
    lines.append("| Witness | Role | Score | Grade | Contradictions | Impeachments | Perjury |")
    lines.append("|---------|------|-------|-------|---------------|-------------|---------|")
    for s in sorted(scores, key=lambda x: x['credibility_score']):
        lines.append(
            f"| **{s['name']}** | {s['role'][:30]} | "
            f"**{s['credibility_score']:.1f}**/10 | {s['credibility_grade']} | "
            f"{s['contradiction_count']} | {s['impeachment_count']} | {s['perjury_count']} |"
        )

    # Summary stats
    lines.append(f"\n**Total contradictions across all witnesses:** {summary['total_contradictions']}")
    lines.append(f"**Total impeachment items:** {summary['total_impeachments']}")
    lines.append(f"**Total perjury entries:** {summary['total_perjury']}")

    # Detailed per-witness analysis
    lines.append("\n## DETAILED WITNESS ANALYSIS\n")
    for s in sorted(scores, key=lambda x: x['credibility_score']):
        lines.append(f"### {s['name']}")
        lines.append(f"**Role:** {s['role']}")
        lines.append(f"**Relationship to Parties:** {s['relationship']}")
        lines.append(f"**Motive to Lie:** {s['motive_to_lie']}")
        lines.append(f"\n| Metric | Value |")
        lines.append(f"|--------|-------|")
        lines.append(f"| Credibility Score | **{s['credibility_score']:.1f}/10** |")
        lines.append(f"| Credibility Grade | **{s['credibility_grade']}** |")
        lines.append(f"| Consistency Score | {s['consistency_score']:.1f}/10 |")
        lines.append(f"| Corroboration Score | {s['corroboration_score']:.1f}/10 |")
        lines.append(f"| Contradictions | {s['contradiction_count']} |")
        lines.append(f"| Impeachment Items | {s['impeachment_count']} |")
        lines.append(f"| Perjury Entries | {s['perjury_count']} |")
        lines.append(f"| Evidence Appearances | {s['evidence_appearances']} |")

        if s['bias_indicators']:
            lines.append("\n**Bias Indicators:**")
            for bi in s['bias_indicators']:
                lines.append(f"- ⚠️ {bi}")

        if s['prior_false_statements']:
            lines.append(f"\n**Documented Inconsistencies/False Statements** (top {len(s['prior_false_statements'])}):")
            for i, pfs in enumerate(s['prior_false_statements'][:5], 1):
                lines.append(f"\n{i}. **Type:** {pfs['type']} | **Severity:** {pfs['severity']}")
                lines.append(f"   - Statement: \"{pfs['statement_1']}\"")
                lines.append(f"   - Contradicted by: \"{pfs['statement_2']}\"")

        if s['key_findings']:
            lines.append("\n**Key Findings:**")
            for kf in s['key_findings'][:5]:
                if kf['type'] == 'IMPEACHMENT_INDEX':
                    lines.append(
                        f"- **[{kf['contradiction_type']}]** ({kf['value']}): "
                        f"\"{kf['statement_a']}\" vs \"{kf['statement_b']}\""
                    )
                elif kf['type'] == 'BERRY_INVESTIGATION':
                    lines.append(f"- **[Berry Investigation]** ({kf['strength']}): {kf['evidence']}")
                elif kf['type'] == 'ETHICS_VIOLATIONS':
                    lines.append(f"- **[Ethics]** {kf['count']} MRPC violations documented")
                elif kf['type'] == 'PROFILE_SCORE':
                    lines.append(
                        f"- **[Profile]** Existing credibility: {kf['existing_credibility']}, "
                        f"testimony count: {kf['testimony_count']}"
                    )

        lines.append("")

    # Impeachment strategy
    lines.append("\n## IMPEACHMENT STRATEGY RECOMMENDATIONS\n")
    for s in sorted(scores, key=lambda x: x['credibility_score']):
        if s['credibility_score'] < 6.0:
            lines.append(f"### {s['name']} (Score: {s['credibility_score']:.1f})")
            lines.append(f"- **{s['contradiction_count']}** contradictions available for cross-examination")
            lines.append(f"- **{s['impeachment_count']}** impeachment items (MRE 613, MRE 608)")
            if s['perjury_count'] > 0:
                lines.append(f"- **{s['perjury_count']}** potential perjury entries (MCL 750.423)")
            if s['bias_indicators']:
                lines.append(f"- Bias: {'; '.join(s['bias_indicators'][:3])}")
            lines.append("")

    return "\n".join(lines)


def main():
    print("=" * 60)
    print("TOOL #225: WITNESS CREDIBILITY SCORER")
    print("Pigors v. Watson — Evidence-Based Credibility Analysis")
    print("=" * 60)

    if not os.path.exists(DB_PATH):
        print(f"[ERROR] Database not found: {DB_PATH}")
        sys.exit(1)

    conn = connect_db()
    print(f"[OK] Connected to database ({os.path.getsize(DB_PATH) // (1024*1024)} MB)")

    # Verify critical tables
    critical_tables = [
        'detected_contradictions', 'impeachment_items', 'impeachment_index',
        'watson_perjury_compilation', 'evidence_quotes', 'witness_profiles',
    ]
    for tbl in critical_tables:
        if table_exists(conn, tbl):
            count = conn.execute(f"SELECT COUNT(*) FROM [{tbl}]").fetchone()[0]
            print(f"  {tbl}: {count} rows")
        else:
            print(f"  [WARN] Table {tbl} not found")

    print(f"\n[SCORING] {len(KEY_WITNESSES)} key witnesses...")
    scores = []
    for witness in KEY_WITNESSES:
        print(f"  Analyzing: {witness['name']}...")
        score = score_witness(conn, witness)
        scores.append(score)
        print(
            f"    Score: {score['credibility_score']:.1f}/10 | "
            f"Contradictions: {score['contradiction_count']} | "
            f"Impeachments: {score['impeachment_count']} | "
            f"Perjury: {score['perjury_count']}"
        )

    # Build summary
    summary = {
        'total_witnesses': len(scores),
        'total_contradictions': sum(s['contradiction_count'] for s in scores),
        'total_impeachments': sum(s['impeachment_count'] for s in scores),
        'total_perjury': sum(s['perjury_count'] for s in scores),
        'lowest_credibility': min(scores, key=lambda x: x['credibility_score'])['name'],
        'highest_credibility': max(scores, key=lambda x: x['credibility_score'])['name'],
    }

    # Build output data
    output_data = {
        'tool': 'witness_credibility_scorer',
        'tool_number': 225,
        'generated_at': datetime.now().isoformat(),
        'case': 'Pigors v. Watson (2024-001507-DC)',
        'summary': summary,
        'witnesses': scores,
    }

    # Write JSON
    json_path = os.path.join(REPORTS_DIR, 'witness_credibility.json')
    with open(json_path, 'w', encoding='utf-8') as f:
        json.dump(output_data, f, indent=2, ensure_ascii=False, default=str)
    print(f"\n[SAVED] {json_path}")

    # Write MD
    md_content = generate_md(scores, summary)
    md_path = os.path.join(REPORTS_DIR, 'WITNESS_CREDIBILITY.md')
    with open(md_path, 'w', encoding='utf-8') as f:
        f.write(md_content)
    print(f"[SAVED] {md_path}")

    # Print summary
    print("\n" + "=" * 60)
    print("RESULTS SUMMARY")
    print("=" * 60)
    print(f"{'Witness':<25} {'Score':>6} {'Grade':<25} {'Contradictions':>14} {'Impeach':>8} {'Perjury':>8}")
    print("-" * 92)
    for s in sorted(scores, key=lambda x: x['credibility_score']):
        print(
            f"{s['name']:<25} {s['credibility_score']:>5.1f} "
            f"{s['credibility_grade']:<25} "
            f"{s['contradiction_count']:>14} {s['impeachment_count']:>8} {s['perjury_count']:>8}"
        )
    print(f"\nLowest credibility:  {summary['lowest_credibility']}")
    print(f"Highest credibility: {summary['highest_credibility']}")

    conn.close()
    print("\n[DONE] Witness credibility scoring complete.")


if __name__ == '__main__':
    main()
