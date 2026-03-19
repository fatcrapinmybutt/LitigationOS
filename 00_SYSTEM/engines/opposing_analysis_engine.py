#!/usr/bin/env python3
"""Opposing Analysis Engine - Adversary pattern analyzer for litigation strategy.

Queries adversary data from the litigation database to generate profiles,
pattern analysis, contradiction maps, predicted strategies, and weakness scores.

Usage:
    python opposing_analysis_engine.py --adversary watson --output md
    python opposing_analysis_engine.py --adversary all --output json
    python opposing_analysis_engine.py --adversary mcneill --output md --save report.md
"""
import sys
sys.stdout.reconfigure(encoding='utf-8')

import argparse
import json
import os
import re
import sqlite3
from collections import Counter, OrderedDict, defaultdict
from datetime import datetime
from pathlib import Path

DB = r'C:\Users\andre\LitigationOS\litigation_context.db'

ADVERSARIES = {
    'watson': {
        'full_name': 'Emily Watson',
        'role': 'Opposing Party / Co-Parent',
        'db_aliases': ['Watson', 'Emily Watson', 'Emily', 'emily watson', 'Emily R. Watson'],
        'tables': ['appclose_messages', 'adversary_assertions', 'adversary_harm_summary',
                   'impeachment_index', 'parental_alienation_evidence'],
        'claim_types': ['custody torts', 'defamation', 'IIED', 'parental alienation',
                       'perjury', 'fraud on the court', 'contempt'],
    },
    'barnes': {
        'full_name': 'Attorney Barnes',
        'role': 'Opposing Counsel',
        'db_aliases': ['Barnes', 'Attorney Barnes', 'barnes'],
        'tables': ['adversary_assertions', 'adversary_harm_summary', 'impeachment_index',
                   'berry_ethics_violations'],
        'claim_types': ['malpractice', 'fraud', 'conspiracy', 'ethics violations',
                       'abuse of process'],
    },
    'mcneill': {
        'full_name': 'Judge McNeill',
        'role': 'Judicial Officer',
        'db_aliases': ['McNeill', 'Judge McNeill', 'mcneill', 'McNeil'],
        'tables': ['adversary_assertions', 'adversary_harm_summary', 'judicial_violations',
                   'impeachment_index', 'forensic_judicial_analysis'],
        'claim_types': ['1983 damages', 'due process violations', 'judicial misconduct',
                       'ex parte communications', 'bias'],
    },
    'shadyoaks': {
        'full_name': 'Shady Oaks / HOA / Alden Management',
        'role': 'Housing Defendants',
        'db_aliases': ['Shady Oaks', 'ShadyOaks', 'HOA', 'Alden', 'Alden Management',
                       'shady oaks', 'shadyoaks'],
        'tables': ['adversary_assertions', 'adversary_harm_summary', 'housing_violations',
                   'shadyoaks_evidence', 'shady_oaks_evidence'],
        'claim_types': ['housing violations', 'RICO', 'conversion', 'Fair Housing Act',
                       'landlord-tenant', 'retaliation', 'discrimination'],
    },
}


def get_db_connection():
    """Open DB connection with standard pragmas."""
    conn = sqlite3.connect(DB, timeout=120)
    conn.execute("PRAGMA busy_timeout=60000")
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA cache_size=-32000")
    conn.row_factory = sqlite3.Row
    return conn


def safe_query(conn, query, params=None):
    """Execute a query safely, returning empty list on error."""
    try:
        if params:
            rows = conn.execute(query, params).fetchall()
        else:
            rows = conn.execute(query).fetchall()
        return [dict(r) for r in rows]
    except Exception as e:
        print(f"  [QUERY WARN] {e}")
        return []


def table_exists(conn, table_name):
    """Check if a table exists in the database."""
    result = conn.execute(
        "SELECT name FROM sqlite_master WHERE type='table' AND name=?",
        (table_name,)
    ).fetchone()
    return result is not None


def build_alias_clause(aliases, column='speaker'):
    """Build a WHERE clause matching any alias."""
    clauses = ' OR '.join(f"{column} LIKE ?" for _ in aliases)
    params = [f"%{a}%" for a in aliases]
    return clauses, params


def query_assertions(conn, adversary_key):
    """Query adversary_assertions for a specific adversary."""
    info = ADVERSARIES[adversary_key]
    if not table_exists(conn, 'adversary_assertions'):
        return []

    clause, params = build_alias_clause(info['db_aliases'], 'speaker')
    rows = safe_query(conn,
        f"SELECT assertion_text, assertion_type, speaker, page_ref, "
        f"is_false, rebuttal_evidence, severity, created_at "
        f"FROM adversary_assertions WHERE {clause} ORDER BY created_at DESC",
        params
    )
    return rows


def query_harm_summary(conn, adversary_key):
    """Query adversary_harm_summary for a specific adversary."""
    info = ADVERSARIES[adversary_key]
    if not table_exists(conn, 'adversary_harm_summary'):
        return []

    clause, params = build_alias_clause(info['db_aliases'], 'adversary')
    rows = safe_query(conn,
        f"SELECT adversary, total_mentions, harm_count, top_categories, "
        f"key_incidents, legal_theories, filing_stacks "
        f"FROM adversary_harm_summary WHERE {clause}",
        params
    )
    return rows


def query_appclose_messages(conn, adversary_key):
    """Query appclose_messages for Watson analysis."""
    if adversary_key != 'watson':
        return []
    if not table_exists(conn, 'appclose_messages'):
        return []

    rows = safe_query(conn,
        "SELECT sender, recipient, message_date, message_type, "
        "message_text, page_ref FROM appclose_messages "
        "WHERE sender LIKE '%Watson%' OR sender LIKE '%Emily%' "
        "ORDER BY message_date DESC LIMIT 200"
    )
    return rows


def query_impeachment(conn, adversary_key):
    """Query impeachment_index for contradictions."""
    info = ADVERSARIES[adversary_key]
    if not table_exists(conn, 'impeachment_index'):
        return []

    clause, params = build_alias_clause(info['db_aliases'], 'target_witness')
    rows = safe_query(conn,
        f"SELECT target_witness, statement_a, source_a, date_a, "
        f"statement_b, source_b, date_b, contradiction_type, "
        f"impeachment_value, legal_use "
        f"FROM impeachment_index WHERE {clause} ORDER BY impeachment_value DESC",
        params
    )
    return rows


def query_judicial_patterns(conn):
    """Query judicial-specific tables for McNeill."""
    results = {}

    if table_exists(conn, 'judicial_violations'):
        results['violations'] = safe_query(conn,
            "SELECT * FROM judicial_violations ORDER BY rowid DESC LIMIT 100"
        )

    if table_exists(conn, 'forensic_judicial_analysis'):
        results['forensic'] = safe_query(conn,
            "SELECT * FROM forensic_judicial_analysis LIMIT 50"
        )

    return results


def build_adversary_profile(conn, adversary_key):
    """Build comprehensive adversary profile."""
    info = ADVERSARIES[adversary_key]
    print(f"[PROFILE] Building profile for {info['full_name']}...")

    # Query all data sources
    assertions = query_assertions(conn, adversary_key)
    harm_data = query_harm_summary(conn, adversary_key)
    impeachment = query_impeachment(conn, adversary_key)

    # Adversary-specific queries
    messages = []
    judicial_data = {}
    if adversary_key == 'watson':
        messages = query_appclose_messages(conn, adversary_key)
    elif adversary_key == 'mcneill':
        judicial_data = query_judicial_patterns(conn)

    # Analyze assertions
    assertion_types = Counter(a.get('assertion_type', 'unknown') for a in assertions)
    false_assertions = [a for a in assertions if a.get('is_false') == 1]
    severity_dist = Counter(a.get('severity', 'unknown') for a in assertions)

    # Analyze communication patterns (Watson)
    comm_patterns = {}
    if messages:
        msg_types = Counter(m.get('message_type', 'unknown') for m in messages)
        dates = [m.get('message_date', '') for m in messages if m.get('message_date')]
        comm_patterns = {
            'total_messages': len(messages),
            'message_types': dict(msg_types),
            'date_range': f"{min(dates) if dates else 'N/A'} to {max(dates) if dates else 'N/A'}",
        }

    # Build contradiction map
    contradictions = []
    for imp in impeachment:
        contradictions.append({
            'statement_a': imp.get('statement_a', ''),
            'source_a': imp.get('source_a', ''),
            'date_a': imp.get('date_a', ''),
            'statement_b': imp.get('statement_b', ''),
            'source_b': imp.get('source_b', ''),
            'date_b': imp.get('date_b', ''),
            'type': imp.get('contradiction_type', ''),
            'impeachment_value': imp.get('impeachment_value', ''),
        })

    # Calculate weakness/exploitability score
    weakness_score = calc_weakness_score(
        assertions=assertions,
        false_assertions=false_assertions,
        contradictions=contradictions,
        harm_data=harm_data
    )

    # Predicted defense strategies
    predicted_defenses = predict_defenses(adversary_key, assertions, harm_data)

    profile = {
        'adversary_key': adversary_key,
        'full_name': info['full_name'],
        'role': info['role'],
        'generated_at': datetime.now().isoformat(),
        'summary': {
            'total_assertions': len(assertions),
            'false_assertions': len(false_assertions),
            'assertion_types': dict(assertion_types),
            'severity_distribution': dict(severity_dist),
            'total_contradictions': len(contradictions),
            'weakness_score': weakness_score,
        },
        'harm_summary': harm_data,
        'communication_patterns': comm_patterns,
        'contradiction_map': contradictions[:50],
        'predicted_defenses': predicted_defenses,
        'claim_types': info['claim_types'],
    }

    if judicial_data:
        profile['judicial_analysis'] = {
            'violations': judicial_data.get('violations', [])[:20],
            'forensic_findings': judicial_data.get('forensic', [])[:20],
        }

    print(f"  Assertions: {len(assertions)} | False: {len(false_assertions)} | "
          f"Contradictions: {len(contradictions)} | Weakness: {weakness_score}/100")

    return profile


def calc_weakness_score(assertions, false_assertions, contradictions, harm_data):
    """Calculate exploitability/weakness score 0-100."""
    score = 0

    # False assertions factor (max 30 points)
    if assertions:
        false_ratio = len(false_assertions) / max(len(assertions), 1)
        score += min(30, round(false_ratio * 60))

    # Contradiction factor (max 30 points)
    contradiction_count = len(contradictions)
    if contradiction_count >= 10:
        score += 30
    elif contradiction_count >= 5:
        score += 20
    elif contradiction_count >= 1:
        score += 10

    # Harm documentation factor (max 20 points)
    if harm_data:
        total_harms = sum(h.get('harm_count', 0) for h in harm_data)
        if total_harms >= 20:
            score += 20
        elif total_harms >= 10:
            score += 15
        elif total_harms >= 1:
            score += 10

    # Severity factor (max 20 points)
    high_severity = sum(1 for a in assertions if a.get('severity', '').upper() in ('HIGH', 'CRITICAL'))
    if high_severity >= 10:
        score += 20
    elif high_severity >= 5:
        score += 15
    elif high_severity >= 1:
        score += 10

    return min(100, score)


def predict_defenses(adversary_key, assertions, harm_data):
    """Predict likely defense strategies based on adversary patterns."""
    defenses = []

    if adversary_key == 'watson':
        defenses = [
            {'strategy': 'Parental fitness defense',
             'likelihood': 'HIGH',
             'counter': 'Document pattern of alienation with AppClose messages and timeline'},
            {'strategy': 'Deny access interference',
             'likelihood': 'HIGH',
             'counter': 'Use separation log + AppClose message timestamps'},
            {'strategy': 'Claim mutual conflict',
             'likelihood': 'MEDIUM',
             'counter': 'Show asymmetric communication pattern and unilateral decisions'},
            {'strategy': 'Best interest of child argument',
             'likelihood': 'HIGH',
             'counter': 'Present BIF factor analysis showing alienation harm'},
        ]
    elif adversary_key == 'barnes':
        defenses = [
            {'strategy': 'Attorney judgment/strategy defense',
             'likelihood': 'HIGH',
             'counter': 'Document deviation from standard of care with expert analysis'},
            {'strategy': 'Claim client authorized actions',
             'likelihood': 'MEDIUM',
             'counter': 'Show lack of informed consent and undisclosed conflicts'},
            {'strategy': 'Litigation privilege',
             'likelihood': 'MEDIUM',
             'counter': 'Distinguish between advocacy and fraudulent representations'},
        ]
    elif adversary_key == 'mcneill':
        defenses = [
            {'strategy': 'Judicial immunity',
             'likelihood': 'HIGH',
             'counter': 'Argue actions were administrative/non-judicial per Mireles v. Waco'},
            {'strategy': 'Discretionary decision-making',
             'likelihood': 'HIGH',
             'counter': 'Show pattern of abuse exceeding discretion bounds'},
            {'strategy': 'Claim procedural compliance',
             'likelihood': 'MEDIUM',
             'counter': 'Document specific MCR violations and ex parte contacts'},
        ]
    elif adversary_key == 'shadyoaks':
        defenses = [
            {'strategy': 'Lease compliance defense',
             'likelihood': 'HIGH',
             'counter': 'Document specific lease and statutory violations'},
            {'strategy': 'Business judgment rule',
             'likelihood': 'MEDIUM',
             'counter': 'Show pattern of discriminatory enforcement'},
            {'strategy': 'Deny knowledge of conditions',
             'likelihood': 'MEDIUM',
             'counter': 'Use maintenance request records and inspection documentation'},
            {'strategy': 'Challenge RICO standing',
             'likelihood': 'HIGH',
             'counter': 'Document pattern of enterprise activity per MCL 750.159j'},
        ]

    return defenses


def format_dossier_md(profile):
    """Format adversary profile as markdown dossier."""
    lines = []
    lines.append(f"# ADVERSARY DOSSIER: {profile['full_name']}")
    lines.append(f"")
    lines.append(f"**Role:** {profile['role']}")
    lines.append(f"**Generated:** {profile['generated_at']}")
    lines.append(f"**Weakness Score:** {profile['summary']['weakness_score']}/100")
    lines.append(f"")

    # Summary
    s = profile['summary']
    lines.append(f"## Summary Statistics")
    lines.append(f"- Total Assertions Tracked: {s['total_assertions']}")
    lines.append(f"- False Assertions Identified: {s['false_assertions']}")
    lines.append(f"- Contradictions Documented: {s['total_contradictions']}")
    lines.append(f"- Applicable Claims: {', '.join(profile['claim_types'])}")
    lines.append(f"")

    if s['assertion_types']:
        lines.append(f"### Assertion Types")
        for atype, count in sorted(s['assertion_types'].items(), key=lambda x: -x[1]):
            lines.append(f"- {atype}: {count}")
        lines.append(f"")

    if s['severity_distribution']:
        lines.append(f"### Severity Distribution")
        for sev, count in sorted(s['severity_distribution'].items()):
            lines.append(f"- {sev}: {count}")
        lines.append(f"")

    # Communication Patterns
    if profile['communication_patterns']:
        cp = profile['communication_patterns']
        lines.append(f"## Communication Patterns")
        lines.append(f"- Total Messages Analyzed: {cp.get('total_messages', 0)}")
        lines.append(f"- Date Range: {cp.get('date_range', 'N/A')}")
        if cp.get('message_types'):
            lines.append(f"- Message Types:")
            for mt, count in cp['message_types'].items():
                lines.append(f"  - {mt}: {count}")
        lines.append(f"")

    # Contradiction Map
    if profile['contradiction_map']:
        lines.append(f"## Contradiction Map ({len(profile['contradiction_map'])} items)")
        lines.append(f"")
        for i, c in enumerate(profile['contradiction_map'][:15], 1):
            lines.append(f"### Contradiction #{i}")
            lines.append(f"**Statement A:** {c.get('statement_a', 'N/A')[:200]}")
            lines.append(f"  - Source: {c.get('source_a', 'N/A')} | Date: {c.get('date_a', 'N/A')}")
            lines.append(f"**Statement B:** {c.get('statement_b', 'N/A')[:200]}")
            lines.append(f"  - Source: {c.get('source_b', 'N/A')} | Date: {c.get('date_b', 'N/A')}")
            lines.append(f"**Type:** {c.get('type', 'N/A')} | **Value:** {c.get('impeachment_value', 'N/A')}")
            lines.append(f"")

    # Predicted Defenses
    if profile['predicted_defenses']:
        lines.append(f"## Predicted Defense Strategies")
        lines.append(f"")
        for d in profile['predicted_defenses']:
            lines.append(f"### {d['strategy']}")
            lines.append(f"- **Likelihood:** {d['likelihood']}")
            lines.append(f"- **Counter-Strategy:** {d['counter']}")
            lines.append(f"")

    # Judicial Analysis
    if profile.get('judicial_analysis'):
        ja = profile['judicial_analysis']
        if ja.get('violations'):
            lines.append(f"## Judicial Violations ({len(ja['violations'])} documented)")
            for v in ja['violations'][:10]:
                desc = str(dict(v))[:150] if isinstance(v, dict) else str(v)[:150]
                lines.append(f"- {desc}")
            lines.append(f"")

    # Harm Summary
    if profile['harm_summary']:
        lines.append(f"## Documented Harms")
        for h in profile['harm_summary']:
            lines.append(f"- **{h.get('adversary', 'N/A')}**: {h.get('harm_count', 0)} harms, "
                         f"{h.get('total_mentions', 0)} mentions")
            if h.get('top_categories'):
                lines.append(f"  - Categories: {h['top_categories'][:200]}")
            if h.get('legal_theories'):
                lines.append(f"  - Legal Theories: {h['legal_theories'][:200]}")
        lines.append(f"")

    return '\n'.join(lines)


def main():
    parser = argparse.ArgumentParser(
        description='Opposing Analysis Engine - Adversary pattern analyzer'
    )
    parser.add_argument('--adversary', type=str, required=True,
                        choices=list(ADVERSARIES.keys()) + ['all'],
                        help='Adversary to analyze')
    parser.add_argument('--output', type=str, choices=['json', 'md'], default='json',
                        help='Output format (default: json)')
    parser.add_argument('--save', type=str, help='Save report to file')

    args = parser.parse_args()

    print(f"[START] Opposing Analysis Engine - {datetime.now().isoformat()}")

    try:
        conn = get_db_connection()

        if args.adversary == 'all':
            targets = list(ADVERSARIES.keys())
        else:
            targets = [args.adversary]

        profiles = {}
        for target in targets:
            profile = build_adversary_profile(conn, target)
            profiles[target] = profile

        conn.close()

        # Format output
        if args.output == 'md':
            parts = []
            for key, profile in profiles.items():
                parts.append(format_dossier_md(profile))
            output_text = '\n\n---\n\n'.join(parts)
        else:
            output_text = json.dumps(profiles, indent=2, ensure_ascii=True, default=str)

        if args.save:
            with open(args.save, 'w', encoding='utf-8') as f:
                f.write(output_text)
            print(f"[SAVED] Report written to {args.save}")
        else:
            print(f"\n{output_text}")

        # Print summary
        print(f"\n[SUMMARY]")
        for key, profile in profiles.items():
            s = profile['summary']
            print(f"  {profile['full_name']:<30s} "
                  f"Assertions: {s['total_assertions']:>4d} | "
                  f"Contradictions: {s['total_contradictions']:>3d} | "
                  f"Weakness: {s['weakness_score']:>3d}/100")

    except Exception as e:
        print(f"[FATAL] {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

    print(f"[DONE] {datetime.now().isoformat()}")


if __name__ == '__main__':
    main()
