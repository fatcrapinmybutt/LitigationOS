#!/usr/bin/env python3
"""
Tool #223: Custody Factor Analyzer
Analyzes Michigan best interest factors (MCL 722.23 a-l) with evidence mapping.
For each factor: cite specific evidence, rate strength, identify gaps.
Compare Andrew vs Emily on each factor.

Output: CUSTODY_FACTOR_ANALYSIS.md + custody_factor_analysis.json
"""
import sys
import os
import json
import sqlite3
from datetime import datetime

sys.stdout = open(sys.stdout.fileno(), mode='w', encoding='utf-8', errors='replace')

# --- Path setup (never set CWD to repo root due to shadow modules) ---
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
REPO_ROOT = os.path.normpath(os.path.join(SCRIPT_DIR, '..', '..'))
DB_PATH = os.path.join(REPO_ROOT, 'litigation_context.db')
REPORTS_DIR = os.path.join(REPO_ROOT, '00_SYSTEM', 'reports')
os.makedirs(REPORTS_DIR, exist_ok=True)

# --- Michigan Best Interest Factors (MCL 722.23) ---
FACTORS = {
    'a': 'Love, Affection, and Other Emotional Ties',
    'b': 'Capacity to Give Love, Affection, and Guidance; Continuation of Education',
    'c': 'Capacity to Provide Food, Clothing, Medical Care, and Other Material Needs',
    'd': 'Length of Time the Child Has Lived in a Stable, Satisfactory Environment',
    'e': 'Permanence of the Existing or Proposed Custodial Home',
    'f': 'Moral Fitness of the Parties',
    'g': 'Mental and Physical Health of the Parties',
    'h': 'Home, School, and Community Record of the Child',
    'i': 'Reasonable Preference of the Child (if old enough)',
    'j': 'Willingness to Facilitate a Close Relationship with the Other Parent',
    'k': 'Domestic Violence',
    'l': 'Any Other Factor Considered by the Court to be Relevant',
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


def analyze_factors(conn):
    """Analyze all 12 best interest factors."""
    results = {}

    # --- Load pre-computed factor data from bif_factor_complete ---
    bif_data = {}
    if table_exists(conn, 'bif_factor_complete'):
        cols = get_columns(conn, 'bif_factor_complete')
        print(f"  bif_factor_complete columns: {cols}")
        rows = safe_query(conn, "SELECT * FROM bif_factor_complete ORDER BY factor_letter")
        for r in rows:
            bif_data[r['factor_letter']] = dict(r)

    # --- Load alienation evidence (critical for factor j) ---
    alienation_items = []
    if table_exists(conn, 'alienation_scoring'):
        cols = get_columns(conn, 'alienation_scoring')
        print(f"  alienation_scoring columns: {cols}")
        alienation_items = safe_query(
            conn, "SELECT indicator_name, category, score, max_score, evidence FROM alienation_scoring"
        )

    alienation_events = []
    if table_exists(conn, 'parental_alienation_evidence'):
        alienation_events = safe_query(
            conn, "SELECT event_date, description, mcl_factor, severity FROM parental_alienation_evidence"
        )

    # --- Load constitutional violations (due process) ---
    const_violations = []
    if table_exists(conn, 'constitutional_violations'):
        const_violations = safe_query(
            conn, "SELECT amendment, violation_type, description, severity FROM constitutional_violations"
        )

    # --- Load AppClose violations (co-parenting evidence) ---
    appclose_items = []
    if table_exists(conn, 'appclose_violations'):
        appclose_items = safe_query(
            conn, "SELECT violation_type, content, severity FROM appclose_violations"
        )

    # --- Load impeachment index for Emily contradictions ---
    impeachment = []
    if table_exists(conn, 'impeachment_index'):
        impeachment = safe_query(
            conn,
            "SELECT target_witness, statement_a, statement_b, contradiction_type, impeachment_value "
            "FROM impeachment_index WHERE target_witness LIKE '%Watson%' OR target_witness LIKE '%Emily%'"
        )

    # --- Count evidence per factor from evidence_quotes ---
    factor_evidence_counts = {}
    if table_exists(conn, 'evidence_quotes'):
        # Search for factor-related keywords
        factor_keywords = {
            'a': ['love', 'affection', 'emotional', 'bond', 'attachment'],
            'b': ['guidance', 'education', 'nurturing', 'discipline', 'school'],
            'c': ['food', 'clothing', 'medical', 'housing', 'financial', 'support', 'material'],
            'd': ['stable', 'environment', 'custodial', 'residence', 'home'],
            'e': ['permanence', 'proposed', 'custodial home', 'relocation'],
            'f': ['moral', 'fitness', 'character', 'drug', 'alcohol', 'substance', 'criminal'],
            'g': ['mental health', 'physical health', 'HealthWest', 'evaluation', 'assessment'],
            'h': ['school', 'community', 'record', 'child development'],
            'i': ['preference', 'child wish', 'old enough'],
            'j': ['alienation', 'facilitate', 'relationship', 'co-parent', 'withholding', 'parenting time'],
            'k': ['domestic violence', 'abuse', 'assault', 'PPO', 'protection order', 'threat'],
            'l': ['relevant', 'ex parte', 'due process', 'bias', 'judicial'],
        }
        for letter, keywords in factor_keywords.items():
            like_clauses = " OR ".join([f"quote_text LIKE '%{kw}%'" for kw in keywords])
            count_row = safe_query(
                conn, f"SELECT COUNT(*) as cnt FROM evidence_quotes WHERE {like_clauses}"
            )
            factor_evidence_counts[letter] = count_row[0][0] if count_row else 0

    # --- Get relevant claims counts ---
    claims_counts = {}
    if table_exists(conn, 'claims'):
        claim_keywords = {
            'f': ['drug', 'substance', 'criminal', 'moral'],
            'g': ['mental_health', 'evaluation', 'assessment'],
            'j': ['alienation', 'parenting_time', 'withholding'],
            'k': ['violence', 'abuse', 'ppo', 'assault'],
            'l': ['ex_parte', 'due_process', 'bias'],
        }
        for letter, keywords in claim_keywords.items():
            like_clauses = " OR ".join(
                [f"classification LIKE '%{kw}%' OR proposition LIKE '%{kw}%'" for kw in keywords]
            )
            count_row = safe_query(
                conn, f"SELECT COUNT(*) as cnt FROM claims WHERE {like_clauses}"
            )
            claims_counts[letter] = count_row[0][0] if count_row else 0

    # --- Build per-factor analysis ---
    for letter, name in FACTORS.items():
        bif = bif_data.get(letter, {})
        andrew_score = bif.get('andrew_score', None)
        emily_score = bif.get('emily_score', None)
        evidence_count_bif = bif.get('evidence_count', 0) or 0
        key_evidence = bif.get('key_evidence', '') or ''
        key_citations = bif.get('key_citations', '') or ''
        eq_count = factor_evidence_counts.get(letter, 0)
        cl_count = claims_counts.get(letter, 0)

        # Determine strength rating
        total_evidence = evidence_count_bif + eq_count
        if total_evidence >= 40:
            strength = 'STRONG'
        elif total_evidence >= 15:
            strength = 'MODERATE'
        elif total_evidence > 0:
            strength = 'WEAK'
        else:
            strength = 'INSUFFICIENT'

        # Identify gaps
        gaps = []
        if total_evidence < 5:
            gaps.append(f"Need more evidence for factor ({letter})")
        if andrew_score is not None and andrew_score < 5:
            gaps.append(f"Andrew's score is low ({andrew_score}/10)")
        if key_evidence and len(key_evidence) < 20:
            gaps.append("Key evidence citations are thin")

        # Factor-specific analysis
        specific_notes = []
        if letter == 'j':
            # Alienation factor - critical
            total_alienation_score = sum(
                r['score'] for r in alienation_items
            ) if alienation_items else 0
            max_alienation_score = sum(
                r['max_score'] for r in alienation_items
            ) if alienation_items else 0
            specific_notes.append(
                f"Alienation score: {total_alienation_score}/{max_alienation_score} "
                f"({len(alienation_items)} indicators)"
            )
            for ae in alienation_events:
                specific_notes.append(
                    f"  [{ae['event_date']}] {ae['description'][:120]} (Severity: {ae['severity']})"
                )
            if appclose_items:
                specific_notes.append(
                    f"AppClose violations documented: {len(appclose_items)} incidents"
                )

        elif letter == 'k':
            # Domestic violence - 7 law enforcement investigations found no violence
            specific_notes.append(
                "CRITICAL: 7 law enforcement investigations found NO violence by Andrew"
            )
            specific_notes.append(
                "PPO issued ex parte without evidentiary hearing"
            )
            for imp in impeachment:
                specific_notes.append(
                    f"  Impeachment [{imp['contradiction_type']}]: {str(imp['statement_a'])[:100]}"
                )

        elif letter == 'g':
            # Mental health - HealthWest clean eval
            specific_notes.append(
                "HealthWest evaluation #1 returned ALL ZEROS (no concerns)"
            )
            specific_notes.append(
                "Judge McNeill sent biasing letter to evaluator after clean eval"
            )
            for cv in const_violations:
                if 'EVAL' in str(cv['violation_type']).upper() or 'HEALTH' in str(cv['description']).upper():
                    specific_notes.append(f"  Constitutional: {str(cv['description'])[:120]}")

        elif letter == 'f':
            # Moral fitness - drug screens negative
            specific_notes.append("All drug screens returned NEGATIVE for Andrew")
            for imp in impeachment:
                if 'substance' in str(imp['statement_a']).lower() or 'drug' in str(imp['statement_a']).lower():
                    specific_notes.append(
                        f"  Emily's false allegation: {str(imp['statement_a'])[:120]}"
                    )

        elif letter == 'l':
            # Other relevant factors - judicial bias
            specific_notes.append(
                f"Constitutional violations documented: {len(const_violations)}"
            )
            for cv in const_violations[:3]:
                specific_notes.append(
                    f"  [{cv['amendment']}] {str(cv['description'])[:120]}"
                )

        results[letter] = {
            'factor_letter': letter,
            'factor_name': name,
            'mcl_citation': f'MCL 722.23({letter})',
            'andrew_score': float(andrew_score) if andrew_score is not None else None,
            'emily_score': float(emily_score) if emily_score is not None else None,
            'evidence_count_bif': int(evidence_count_bif),
            'evidence_quotes_count': eq_count,
            'claims_count': cl_count,
            'total_evidence': total_evidence,
            'strength_rating': strength,
            'key_evidence_excerpt': key_evidence[:300] if key_evidence else '',
            'key_citations': key_citations,
            'gaps': gaps,
            'specific_notes': specific_notes,
        }

    return results


def build_summary(conn, factors):
    """Build overall summary statistics."""
    summary = {
        'total_factors': 12,
        'strong_factors': sum(1 for f in factors.values() if f['strength_rating'] == 'STRONG'),
        'moderate_factors': sum(1 for f in factors.values() if f['strength_rating'] == 'MODERATE'),
        'weak_factors': sum(1 for f in factors.values() if f['strength_rating'] == 'WEAK'),
        'insufficient_factors': sum(1 for f in factors.values() if f['strength_rating'] == 'INSUFFICIENT'),
        'andrew_advantage_count': 0,
        'emily_advantage_count': 0,
        'tied_count': 0,
    }
    for f in factors.values():
        a = f['andrew_score']
        e = f['emily_score']
        if a is not None and e is not None:
            if a > e:
                summary['andrew_advantage_count'] += 1
            elif e > a:
                summary['emily_advantage_count'] += 1
            else:
                summary['tied_count'] += 1

    # Get overall case strength from case_strength_scores
    if table_exists(conn, 'case_strength_scores'):
        row = safe_query(conn, "SELECT * FROM case_strength_scores WHERE lane='A' LIMIT 1")
        if row:
            summary['lane_a_grade'] = row[0]['grade']
            summary['lane_a_total'] = row[0]['total_score']
            summary['lane_a_strengths'] = row[0]['strengths']

    return summary


def generate_md(factors, summary):
    """Generate markdown report."""
    lines = []
    lines.append("# CUSTODY FACTOR ANALYSIS — MCL 722.23 Best Interest Factors")
    lines.append(f"\n**Generated:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    lines.append(f"**Case:** Pigors v. Watson (2024-001507-DC)")
    lines.append(f"**Court:** 14th Circuit Court, Family Division, Muskegon County")
    lines.append(f"**Judge:** Hon. Jenny L. McNeill")
    lines.append(f"**Database:** litigation_context.db")

    # Summary
    lines.append("\n## EXECUTIVE SUMMARY\n")
    lines.append(f"| Metric | Count |")
    lines.append(f"|--------|-------|")
    lines.append(f"| Strong Factors | **{summary['strong_factors']}** |")
    lines.append(f"| Moderate Factors | **{summary['moderate_factors']}** |")
    lines.append(f"| Weak Factors | **{summary['weak_factors']}** |")
    lines.append(f"| Insufficient Factors | **{summary['insufficient_factors']}** |")
    lines.append(f"| Andrew Advantage | **{summary['andrew_advantage_count']}** factors |")
    lines.append(f"| Emily Advantage | **{summary['emily_advantage_count']}** factors |")
    lines.append(f"| Tied | **{summary['tied_count']}** factors |")
    if summary.get('lane_a_grade'):
        lines.append(f"| Lane A Overall Grade | **{summary['lane_a_grade']}** ({summary.get('lane_a_total', 'N/A')}/100) |")

    # Comparison table
    lines.append("\n## FACTOR COMPARISON SCORECARD\n")
    lines.append("| Factor | Name | Andrew | Emily | Strength | Evidence |")
    lines.append("|--------|------|--------|-------|----------|----------|")
    for letter in 'abcdefghijkl':
        f = factors[letter]
        a_str = f"{f['andrew_score']:.0f}" if f['andrew_score'] is not None else "N/A"
        e_str = f"{f['emily_score']:.0f}" if f['emily_score'] is not None else "N/A"
        adv = ""
        if f['andrew_score'] is not None and f['emily_score'] is not None:
            if f['andrew_score'] > f['emily_score']:
                adv = " ✅"
            elif f['emily_score'] > f['andrew_score']:
                adv = " ⚠️"
        lines.append(
            f"| ({letter}) | {f['factor_name'][:45]} | {a_str}{adv} | {e_str} | "
            f"{f['strength_rating']} | {f['total_evidence']} items |"
        )

    # Detailed per-factor analysis
    lines.append("\n## DETAILED FACTOR ANALYSIS\n")
    for letter in 'abcdefghijkl':
        f = factors[letter]
        lines.append(f"### Factor ({letter}): {f['factor_name']}")
        lines.append(f"**Citation:** {f['mcl_citation']}")
        a_str = f"{f['andrew_score']:.1f}/10" if f['andrew_score'] is not None else "Not scored"
        e_str = f"{f['emily_score']:.1f}/10" if f['emily_score'] is not None else "Not scored"
        lines.append(f"**Andrew Score:** {a_str} | **Emily Score:** {e_str}")
        lines.append(f"**Strength Rating:** {f['strength_rating']}")
        lines.append(
            f"**Evidence:** {f['evidence_count_bif']} (BIF) + "
            f"{f['evidence_quotes_count']} (quotes) + "
            f"{f['claims_count']} (claims) = **{f['total_evidence']}** total"
        )
        if f['key_evidence_excerpt']:
            lines.append(f"\n**Key Evidence:**\n> {f['key_evidence_excerpt'][:300]}")
        if f['key_citations']:
            lines.append(f"\n**Legal Citations:** {f['key_citations']}")
        if f['specific_notes']:
            lines.append("\n**Analysis Notes:**")
            for note in f['specific_notes']:
                lines.append(f"- {note}")
        if f['gaps']:
            lines.append("\n**Gaps to Address:**")
            for gap in f['gaps']:
                lines.append(f"- ⚠️ {gap}")
        lines.append("")

    # Key evidence highlights
    lines.append("\n## KEY EVIDENCE HIGHLIGHTS\n")
    lines.append("### Andrew's Strongest Evidence")
    lines.append("1. **7 law enforcement investigations** — ALL found NO violence (Factor k)")
    lines.append("2. **HealthWest evaluation #1** — ALL ZEROS, clean mental health (Factor g)")
    lines.append("3. **Negative drug screens** — All substance tests negative (Factor f)")
    lines.append("4. **Watson family alienation pattern** — Systematic parenting time denial (Factor j)")
    lines.append("5. **124 cooperative messages** via AppClose showing good faith (Factor j)")
    lines.append("")
    lines.append("### Emily's Weaknesses")
    lines.append("1. **Alienation pattern** — Systematic parenting time interference (Factor j)")
    lines.append("2. **False allegations** — Claims contradicted by investigation results (Factors f, k)")
    lines.append("3. **Ex parte abuse** — Used ex parte orders to circumvent due process (Factor l)")
    lines.append("4. **DOB discrepancies** — Document inconsistencies undermine credibility")

    return "\n".join(lines)


def main():
    print("=" * 60)
    print("TOOL #223: CUSTODY FACTOR ANALYZER")
    print(f"MCL 722.23 Best Interest Factors — Pigors v. Watson")
    print("=" * 60)

    if not os.path.exists(DB_PATH):
        print(f"[ERROR] Database not found: {DB_PATH}")
        sys.exit(1)

    conn = connect_db()
    print(f"[OK] Connected to database ({os.path.getsize(DB_PATH) // (1024*1024)} MB)")

    # Verify critical tables exist
    for tbl in ['bif_factor_complete', 'evidence_quotes', 'claims']:
        if table_exists(conn, tbl):
            count = conn.execute(f"SELECT COUNT(*) FROM [{tbl}]").fetchone()[0]
            print(f"  {tbl}: {count} rows")
        else:
            print(f"  [WARN] Table {tbl} not found")

    print("\n[ANALYZING] 12 best interest factors...")
    factors = analyze_factors(conn)

    print("[BUILDING] Summary statistics...")
    summary = build_summary(conn, factors)

    # Generate outputs
    output_data = {
        'tool': 'custody_factor_analyzer',
        'tool_number': 223,
        'generated_at': datetime.now().isoformat(),
        'case': 'Pigors v. Watson (2024-001507-DC)',
        'court': '14th Circuit Court, Family Division',
        'summary': summary,
        'factors': factors,
    }

    # Write JSON
    json_path = os.path.join(REPORTS_DIR, 'custody_factor_analysis.json')
    with open(json_path, 'w', encoding='utf-8') as f:
        json.dump(output_data, f, indent=2, ensure_ascii=False, default=str)
    print(f"[SAVED] {json_path}")

    # Write MD
    md_content = generate_md(factors, summary)
    md_path = os.path.join(REPORTS_DIR, 'CUSTODY_FACTOR_ANALYSIS.md')
    with open(md_path, 'w', encoding='utf-8') as f:
        f.write(md_content)
    print(f"[SAVED] {md_path}")

    # Print summary
    print("\n" + "=" * 60)
    print("RESULTS SUMMARY")
    print("=" * 60)
    print(f"Strong factors:       {summary['strong_factors']}")
    print(f"Moderate factors:     {summary['moderate_factors']}")
    print(f"Weak factors:         {summary['weak_factors']}")
    print(f"Insufficient factors: {summary['insufficient_factors']}")
    print(f"Andrew advantage:     {summary['andrew_advantage_count']} factors")
    print(f"Emily advantage:      {summary['emily_advantage_count']} factors")
    if summary.get('lane_a_grade'):
        print(f"Lane A grade:         {summary['lane_a_grade']} ({summary.get('lane_a_total')}/100)")
    print()
    for letter in 'abcdefghijkl':
        f = factors[letter]
        a_str = f"{f['andrew_score']:.0f}" if f['andrew_score'] is not None else "?"
        e_str = f"{f['emily_score']:.0f}" if f['emily_score'] is not None else "?"
        print(
            f"  ({letter}) {f['factor_name'][:40]:<42} "
            f"A:{a_str:>3} E:{e_str:>3} [{f['strength_rating']:>12}] "
            f"({f['total_evidence']} evidence)"
        )

    conn.close()
    print("\n[DONE] Custody factor analysis complete.")


if __name__ == '__main__':
    main()
