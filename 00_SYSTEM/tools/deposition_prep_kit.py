#!/usr/bin/env python3
"""Tool #242: Deposition Prep Kit.

Generates deposition preparation materials for Emily Watson, Ronald Berry,
Pamela Rusco, and Jennifer Barnes. For each deponent: queries evidence_quotes
for contradictions, d_drive_cip for contradiction/impeachment pairs, claims
for disputed facts, judicial_violations for relevant violations.

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

DEPONENTS = {
    'Emily Watson': {
        'role': 'Defendant / Mother',
        'search_terms': ['emily', 'watson', 'defendant', 'mother', 'mom', 'tiffany'],
        'topics': ['custody interference', 'parenting time', 'withholding child',
                   'false allegations', 'ex parte', 'unilateral decisions',
                   'medical decisions', 'communication refusal', 'alienation'],
    },
    'Ronald Berry': {
        'role': 'Non-attorney / Emily\'s domestic partner',
        'search_terms': ['ronald', 'berry', 'ron berry', 'boyfriend'],
        'topics': ['unauthorized legal practice', 'interference with custody',
                   'presence during parenting time', 'influence on child',
                   'domestic violence history', 'relationship with Emily'],
    },
    'Pamela Rusco': {
        'role': 'Friend of the Court (FOC)',
        'search_terms': ['rusco', 'pamela', 'foc', 'friend of the court'],
        'topics': ['ex parte communications', 'bias', 'recommendation basis',
                   'investigation thoroughness', 'contact with parties',
                   'healthwest evaluation', 'procedural compliance'],
    },
    'Jennifer Barnes': {
        'role': 'Emily\'s former attorney (P55406) — WITHDREW',
        'search_terms': ['barnes', 'jennifer', 'p55406', 'attorney'],
        'topics': ['ex parte communications with court', 'withdrawal circumstances',
                   'discovery compliance', 'service of process',
                   'filing representations', 'client communications'],
    },
}

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

def get_deponent_quotes(conn, search_terms):
    """Get evidence quotes mentioning this deponent."""
    cols = verify_table(conn, 'evidence_quotes')
    if not cols:
        return []
    clauses = []
    params = []
    for term in search_terms:
        clauses.append("LOWER(quote_text) LIKE ?")
        params.append(f"%{term}%")
    where = " OR ".join(clauses)
    rows = conn.execute(f"""
        SELECT id, document_id, page_number, evidence_category,
               quote_text, speaker, date_ref, legal_significance, source_type
        FROM evidence_quotes
        WHERE {where}
        ORDER BY id
        LIMIT 300
    """, params).fetchall()
    return [dict(r) for r in rows]

def get_contradiction_pairs(conn, search_terms):
    """Get contradiction/impeachment pairs from d_drive_cip mentioning deponent."""
    cols = verify_table(conn, 'd_drive_cip')
    if not cols:
        return []
    clauses = []
    params = []
    for term in search_terms:
        clauses.append("(LOWER(statement_A) LIKE ? OR LOWER(statement_B) LIKE ?)")
        params.extend([f"%{term}%", f"%{term}%"])
    where = " OR ".join(clauses)
    rows = conn.execute(f"""
        SELECT id, pair_id, statement_A, A_pinpoint, statement_B, B_pinpoint,
               contradiction_type, verification_status
        FROM d_drive_cip
        WHERE {where}
        ORDER BY id
        LIMIT 200
    """, params).fetchall()
    return [dict(r) for r in rows]

def get_relevant_claims(conn, search_terms, topics):
    """Get claims related to this deponent's topics."""
    cols = verify_table(conn, 'claims')
    if not cols:
        return []
    clauses = []
    params = []
    for term in search_terms:
        clauses.append("(LOWER(proposition) LIKE ? OR LOWER(actor) LIKE ?)")
        params.extend([f"%{term}%", f"%{term}%"])
    for topic in topics:
        clauses.append("LOWER(proposition) LIKE ?")
        params.append(f"%{topic}%")
    where = " OR ".join(clauses)
    rows = conn.execute(f"""
        SELECT claim_id, issue_id, classification, actor, proposition,
               affirmative_counter_proposition, evidence_targets, status
        FROM claims
        WHERE {where}
        ORDER BY claim_id
        LIMIT 200
    """, params).fetchall()
    return [dict(r) for r in rows]

def get_relevant_violations(conn, search_terms):
    """Get judicial violations related to this deponent."""
    cols = verify_table(conn, 'judicial_violations')
    if not cols:
        return []
    clauses = []
    params = []
    for term in search_terms:
        clauses.append("LOWER(violation_description) LIKE ?")
        params.append(f"%{term}%")
    where = " OR ".join(clauses)
    rows = conn.execute(f"""
        SELECT violation_id, judge_name, canon_number, violation_description,
               evidence_refs, severity
        FROM judicial_violations
        WHERE {where}
        ORDER BY violation_id
        LIMIT 100
    """, params).fetchall()
    return [dict(r) for r in rows]

def generate_questions(deponent_name, info, quotes, cips, claims, violations):
    """Generate recommended deposition questions organized by topic."""
    questions = {}
    for topic in info['topics']:
        topic_qs = []
        # Find evidence related to this topic
        topic_evidence = []
        for q in quotes:
            if topic.replace(' ', '') in s(q.get('quote_text', '')).replace(' ', ''):
                topic_evidence.append(q)
        for cl in claims:
            if topic.replace(' ', '') in s(cl.get('proposition', '')).replace(' ', ''):
                topic_evidence.append(cl)

        # Generate topic-specific questions
        if 'ex parte' in s(topic):
            topic_qs.extend([
                f"Did you communicate with Judge McNeill outside the presence of Andrew Pigors?",
                f"Were you present during any meetings between the FOC and the judge that Andrew Pigors was not notified of?",
                f"Describe all communications you had with court staff regarding this case.",
            ])
        elif 'interference' in s(topic) or 'withhold' in s(topic):
            topic_qs.extend([
                f"How many times did you deny or limit Andrew Pigors' scheduled parenting time?",
                f"Did you ever withhold information about the child's medical appointments or school events?",
                f"Describe each instance where scheduled parenting time did not occur as ordered.",
            ])
        elif 'parenting time' in s(topic):
            topic_qs.extend([
                f"What was the court-ordered parenting time schedule?",
                f"How many parenting time exchanges were missed and what was the reason for each?",
                f"Did you ever unilaterally change the parenting time schedule?",
            ])
        elif 'false allegation' in s(topic):
            topic_qs.extend([
                f"What specific evidence did you have when you made allegations against Andrew Pigors?",
                f"Were any of your allegations investigated and found to be unsubstantiated?",
                f"Did you file any police reports that were later dismissed?",
            ])
        elif 'medical' in s(topic):
            topic_qs.extend([
                f"Did you make any medical decisions for the child without consulting Andrew Pigors?",
                f"Describe the circumstances of each medical decision made without the other parent's knowledge.",
            ])
        elif 'alienation' in s(topic):
            topic_qs.extend([
                f"Have you ever made negative statements about Andrew Pigors in front of the child?",
                f"Have you encouraged the child to refuse contact with Andrew Pigors?",
            ])
        elif 'unauthorized' in s(topic) or 'legal practice' in s(topic):
            topic_qs.extend([
                f"Are you a licensed attorney in the State of Michigan?",
                f"Have you ever drafted, prepared, or filed any court documents on behalf of Emily Watson?",
                f"Have you provided legal advice to Emily Watson regarding this case?",
            ])
        elif 'bias' in s(topic):
            topic_qs.extend([
                f"Describe your investigation methodology for this case.",
                f"How many times did you meet with each parent?",
                f"Did you review all evidence submitted by both parties?",
            ])
        elif 'healthwest' in s(topic):
            topic_qs.extend([
                f"What role did you play in arranging the HealthWest evaluation?",
                f"Did you communicate with HealthWest about the evaluation before or after it occurred?",
            ])
        elif 'withdrawal' in s(topic):
            topic_qs.extend([
                f"What were the circumstances of your withdrawal from representing Emily Watson?",
                f"Did you communicate with the court ex parte before or during your withdrawal?",
            ])
        elif 'discovery' in s(topic):
            topic_qs.extend([
                f"Did you comply with all discovery requests in a timely manner?",
                f"Were any discovery responses incomplete or evasive?",
            ])
        else:
            topic_qs.append(f"Describe your knowledge and involvement regarding {topic}.")

        # Add evidence-backed questions
        for ev in topic_evidence[:3]:
            snippet = ''
            if 'quote_text' in ev:
                snippet = ((ev.get('quote_text', '') or '')[:100]).replace('\n', ' ')
            elif 'proposition' in ev:
                snippet = ((ev.get('proposition', '') or '')[:100]).replace('\n', ' ')
            if snippet:
                topic_qs.append(f"I'm showing you a document that states: \"{snippet}...\" — is this accurate?")

        questions[topic] = topic_qs
    return questions

def build_impeachment_ammo(cips, quotes):
    """Build impeachment ammunition from contradiction pairs and inconsistent statements."""
    ammo = []
    for cip in cips:
        stmt_a = ((cip.get('statement_A', '') or '')[:200]).replace('\n', ' ')
        stmt_b = ((cip.get('statement_B', '') or '')[:200]).replace('\n', ' ')
        ammo.append({
            'pair_id': cip.get('pair_id', 'N/A'),
            'type': cip.get('contradiction_type', 'N/A'),
            'status': cip.get('verification_status', 'N/A'),
            'statement_A': stmt_a,
            'A_pinpoint': ((cip.get('A_pinpoint', '') or '')[:150]).replace('\n', ' '),
            'statement_B': stmt_b,
            'B_pinpoint': ((cip.get('B_pinpoint', '') or '')[:150]).replace('\n', ' '),
        })
    # Also find quotes with contradictory content
    seen = set()
    for q in quotes:
        qt = s(q.get('quote_text', ''))
        if any(kw in qt for kw in ['inconsistent', 'contradict', 'prior statement', 'previously stated']):
            key = q.get('id', '')
            if key not in seen:
                seen.add(key)
                ammo.append({
                    'pair_id': f"EQ-{q.get('id', '?')}",
                    'type': 'PRIOR_INCONSISTENT_STATEMENT',
                    'status': 'FROM_EVIDENCE_QUOTES',
                    'statement_A': ((q.get('quote_text', '') or '')[:200]).replace('\n', ' '),
                    'A_pinpoint': f"doc:{q.get('document_id', '?')} p.{q.get('page_number', '?')}",
                    'statement_B': '',
                    'B_pinpoint': '',
                })
    return ammo

def build_exhibit_list(quotes, claims, violations):
    """Build list of document exhibits to confront deponent with."""
    exhibits = []
    seen_docs = set()
    for q in quotes[:30]:
        doc_id = q.get('document_id', '')
        if doc_id and doc_id not in seen_docs:
            seen_docs.add(doc_id)
            exhibits.append({
                'type': 'evidence_quote',
                'document_id': doc_id,
                'page': q.get('page_number', 'N/A'),
                'category': q.get('evidence_category', 'N/A'),
                'snippet': ((q.get('quote_text', '') or '')[:120]).replace('\n', ' '),
                'ref': f"EQ-{q.get('id', '?')}"
            })
    for cl in claims[:15]:
        exhibits.append({
            'type': 'claim',
            'claim_id': cl.get('claim_id', 'N/A'),
            'issue': cl.get('issue_id', 'N/A'),
            'proposition': ((cl.get('proposition', '') or '')[:120]).replace('\n', ' '),
            'counter': ((cl.get('affirmative_counter_proposition', '') or '')[:120]).replace('\n', ' '),
            'ref': f"CL-{cl.get('claim_id', '?')}"
        })
    for v in violations[:10]:
        exhibits.append({
            'type': 'judicial_violation',
            'violation_id': v.get('violation_id', 'N/A'),
            'canon': v.get('canon_number', 'N/A'),
            'description': ((v.get('violation_description', '') or '')[:120]).replace('\n', ' '),
            'ref': f"JV-{v.get('violation_id', '?')}"
        })
    return exhibits

def generate_md(all_kits, stats):
    """Generate Markdown report for all deponents."""
    ts = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    lines = [
        f"# Deposition Prep Kit — Tool #242",
        f"",
        f"**Generated:** {ts}",
        f"**Database:** litigation_context.db",
        f"**Deponents:** {', '.join(all_kits.keys())}",
        f"",
        f"---",
        f"",
        f"## Data Summary",
        f"",
        f"| Source Table | Query | Count |",
        f"|-------------|-------|-------|",
    ]
    for tbl, info in stats.items():
        lines.append(f"| {tbl} | {info['query']} | {info['count']} |")
    lines.append("")

    for deponent, kit in all_kits.items():
        lines.append(f"---")
        lines.append(f"")
        lines.append(f"# Deposition: {deponent}")
        lines.append(f"")
        lines.append(f"**Role:** {kit['role']}")
        lines.append(f"**Evidence quotes found:** {kit['quote_count']}")
        lines.append(f"**Contradiction pairs found:** {kit['cip_count']}")
        lines.append(f"**Related claims found:** {kit['claim_count']}")
        lines.append(f"**Relevant judicial violations:** {kit['violation_count']}")
        lines.append(f"")

        # Questions
        lines.append(f"## Recommended Questions")
        lines.append(f"")
        for topic, qs in kit['questions'].items():
            lines.append(f"### {topic.title()}")
            lines.append(f"")
            for i, q in enumerate(qs, 1):
                lines.append(f"{i}. {q}")
            lines.append(f"")

        # Impeachment
        lines.append(f"## Impeachment Ammunition ({len(kit['impeachment'])} items)")
        lines.append(f"")
        if kit['impeachment']:
            for imp in kit['impeachment'][:15]:
                lines.append(f"### {imp['pair_id']} ({imp['type']})")
                lines.append(f"")
                lines.append(f"- **Status:** {imp['status']}")
                lines.append(f"- **Statement A:** {imp['statement_A'][:200]}")
                if imp.get('A_pinpoint'):
                    lines.append(f"  - *Source:* {imp['A_pinpoint'][:150]}")
                if imp.get('statement_B'):
                    lines.append(f"- **Statement B:** {imp['statement_B'][:200]}")
                    if imp.get('B_pinpoint'):
                        lines.append(f"  - *Source:* {imp['B_pinpoint'][:150]}")
                lines.append(f"")
        else:
            lines.append(f"*No contradiction pairs found for this deponent.*")
            lines.append(f"")

        # Exhibits
        lines.append(f"## Document Exhibits ({len(kit['exhibits'])} items)")
        lines.append(f"")
        if kit['exhibits']:
            lines.append(f"| # | Type | Ref | Description |")
            lines.append(f"|---|------|-----|-------------|")
            for i, ex in enumerate(kit['exhibits'][:20], 1):
                desc = ex.get('snippet', '') or ex.get('proposition', '') or ex.get('description', '')
                lines.append(f"| {i} | {ex['type']} | {ex['ref']} | {desc[:80]} |")
            lines.append(f"")
        else:
            lines.append(f"*No specific exhibits identified.*")
            lines.append(f"")

    lines.append("---")
    lines.append("")
    lines.append("## Traceable Queries")
    lines.append("")
    lines.append("```sql")
    lines.append("-- Quotes per deponent: SELECT * FROM evidence_quotes WHERE LOWER(quote_text) LIKE '%[name]%' LIMIT 300")
    lines.append("-- CIP pairs: SELECT * FROM d_drive_cip WHERE LOWER(statement_A) LIKE '%[name]%' OR LOWER(statement_B) LIKE '%[name]%'")
    lines.append("-- Claims: SELECT * FROM claims WHERE LOWER(proposition) LIKE '%[name]%' OR LOWER(actor) LIKE '%[name]%'")
    lines.append("-- Violations: SELECT * FROM judicial_violations WHERE LOWER(violation_description) LIKE '%[name]%'")
    lines.append("```")
    return "\n".join(lines)

def main():
    print("=" * 70)
    print("  TOOL #242: Deposition Prep Kit")
    print("=" * 70)
    if not os.path.exists(DB_PATH):
        print(f"ERROR: Database not found at {DB_PATH}")
        sys.exit(1)
    print(f"  DB: {DB_PATH}")
    conn = get_connection()
    try:
        # Verify all tables upfront
        for tbl in ['evidence_quotes', 'd_drive_cip', 'claims', 'judicial_violations']:
            verify_table(conn, tbl)

        all_kits = {}
        stats = {}
        total_quotes = 0
        total_cips = 0
        total_claims = 0
        total_violations = 0

        for deponent, info in DEPONENTS.items():
            print(f"\n  --- Preparing kit for: {deponent} ({info['role']}) ---")

            print(f"    Querying evidence_quotes...")
            quotes = get_deponent_quotes(conn, info['search_terms'])
            print(f"    Found {len(quotes)} quotes")
            total_quotes += len(quotes)

            print(f"    Querying d_drive_cip...")
            cips = get_contradiction_pairs(conn, info['search_terms'])
            print(f"    Found {len(cips)} contradiction pairs")
            total_cips += len(cips)

            print(f"    Querying claims...")
            claims_data = get_relevant_claims(conn, info['search_terms'], info['topics'])
            print(f"    Found {len(claims_data)} claims")
            total_claims += len(claims_data)

            print(f"    Querying judicial_violations...")
            violations = get_relevant_violations(conn, info['search_terms'])
            print(f"    Found {len(violations)} violations")
            total_violations += len(violations)

            print(f"    Generating questions...")
            questions = generate_questions(deponent, info, quotes, cips, claims_data, violations)

            print(f"    Building impeachment ammunition...")
            impeachment = build_impeachment_ammo(cips, quotes)

            print(f"    Building exhibit list...")
            exhibits = build_exhibit_list(quotes, claims_data, violations)

            all_kits[deponent] = {
                'role': info['role'],
                'quote_count': len(quotes),
                'cip_count': len(cips),
                'claim_count': len(claims_data),
                'violation_count': len(violations),
                'questions': questions,
                'impeachment': impeachment,
                'exhibits': exhibits,
            }

        stats = {
            'evidence_quotes': {'query': 'LIKE search per deponent', 'count': total_quotes},
            'd_drive_cip': {'query': 'LIKE search per deponent', 'count': total_cips},
            'claims': {'query': 'LIKE search per deponent + topics', 'count': total_claims},
            'judicial_violations': {'query': 'LIKE search per deponent', 'count': total_violations},
        }

        # Write JSON
        json_path = os.path.join(REPORTS_DIR, 'deposition_prep_kit.json')
        report_data = {
            'tool': 'Tool #242: Deposition Prep Kit',
            'generated': datetime.now().isoformat(),
            'stats': stats,
            'kits': all_kits,
        }
        with open(json_path, 'w', encoding='utf-8') as f:
            json.dump(report_data, f, indent=2, ensure_ascii=False, default=str)
        print(f"\n  JSON: {json_path}")

        # Write MD
        md_path = os.path.join(REPORTS_DIR, 'DEPOSITION_PREP_KIT.md')
        md_content = generate_md(all_kits, stats)
        with open(md_path, 'w', encoding='utf-8') as f:
            f.write(md_content)
        print(f"  MD:   {md_path}")

        print()
        print("  === KEY FINDINGS ===")
        for deponent, kit in all_kits.items():
            q_count = sum(len(qs) for qs in kit['questions'].values())
            print(f"  {deponent}: {q_count} questions, {len(kit['impeachment'])} impeachment items, {len(kit['exhibits'])} exhibits")
        print()
        print("  DONE.")
    finally:
        conn.close()

if __name__ == '__main__':
    main()
