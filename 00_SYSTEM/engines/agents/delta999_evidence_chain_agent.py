#!/usr/bin/env python3
"""
Delta999 Evidence Chain Agent — Evidence management and chain-of-custody.

Searches 308K+ evidence_quotes via FTS5, builds evidence chains for claims,
checks MRE 901 authentication, assigns Bates numbers, and performs gap analysis.

CLI:
    python delta999_evidence_chain_agent.py --action search --query "ex parte order"
    python delta999_evidence_chain_agent.py --action build_chain --claim "judicial bias" --adversary "FOC"
    python delta999_evidence_chain_agent.py --action check_auth --exhibit "Exhibit A"
    python delta999_evidence_chain_agent.py --action bates --exhibits "A,B,C"
    python delta999_evidence_chain_agent.py --action gap_analysis --filing-stack "MEEK1"
"""

import sys
sys.stdout.reconfigure(encoding='utf-8')

import argparse
import json
import os
import sqlite3
from datetime import datetime
from pathlib import Path

# ── paths ────────────────────────────────────────────────────────────────────
AGENT_DIR = Path(__file__).parent
ENGINE_DIR = AGENT_DIR.parent
sys.path.insert(0, str(ENGINE_DIR))

DB = r'C:\Users\andre\LitigationOS\litigation_context.db'
AGENT_NAME = 'delta999_evidence_chain_agent'

from llm_bridge import llm_ask, llm_analyze_legal


# ── DB helpers ───────────────────────────────────────────────────────────────

def get_conn():
    conn = sqlite3.connect(DB, timeout=120)
    conn.execute('PRAGMA busy_timeout=60000')
    conn.row_factory = sqlite3.Row
    return conn


def log_activity(action, result):
    conn = get_conn()
    conn.execute(
        'INSERT INTO agent_activity_log (agent_name, action, result) VALUES (?,?,?)',
        (AGENT_NAME, action, str(result)[:2000])
    )
    conn.commit()
    conn.close()


# ── Core functions ───────────────────────────────────────────────────────────

def search_evidence(query: str) -> dict:
    """Search across all evidence_quotes via FTS5."""
    conn = get_conn()
    results = []

    # FTS5 search on evidence_quotes_fts
    fts_tables = [
        ('evidence_quotes_fts', 'evidence_quotes'),
        ('canonical_facts_fts', 'canonical_facts'),
        ('exhibit_registry_fts', 'exhibit_registry'),
    ]

    for fts_table, base_table in fts_tables:
        try:
            rows = conn.execute(
                f"SELECT *, rank FROM [{fts_table}] WHERE [{fts_table}] MATCH ? "
                f"ORDER BY rank LIMIT 25",
                (query,)
            ).fetchall()
            for r in rows:
                results.append({
                    'source_table': base_table,
                    'data': dict(r),
                })
        except Exception as e:
            results.append({'source_table': base_table, 'error': str(e)})

    # Also search extracted_harms
    try:
        rows = conn.execute(
            "SELECT * FROM extracted_harms_fts WHERE extracted_harms_fts MATCH ? "
            "ORDER BY rank LIMIT 10",
            (query,)
        ).fetchall()
        for r in rows:
            results.append({'source_table': 'extracted_harms', 'data': dict(r)})
    except Exception:
        pass

    conn.close()

    output = {
        'query': query,
        'total_results': len(results),
        'results': results[:50],
    }
    log_activity(f'search:{query[:80]}', json.dumps(output, default=str)[:2000])
    return output


def build_evidence_chain(claim: str, adversary: str = '') -> dict:
    """Build a linked evidence chain for a specific claim against an adversary."""
    conn = get_conn()

    # Search evidence quotes related to the claim
    evidence = []
    try:
        rows = conn.execute(
            "SELECT * FROM evidence_quotes_fts WHERE evidence_quotes_fts MATCH ? "
            "ORDER BY rank LIMIT 30",
            (claim,)
        ).fetchall()
        evidence = [dict(r) for r in rows]
    except Exception:
        pass

    # Search adversary assertions if adversary specified
    adversary_assertions = []
    if adversary:
        try:
            rows = conn.execute(
                "SELECT * FROM adversary_assertions_fts "
                "WHERE adversary_assertions_fts MATCH ? ORDER BY rank LIMIT 15",
                (adversary,)
            ).fetchall()
            adversary_assertions = [dict(r) for r in rows]
        except Exception:
            pass

    # Search extracted harms
    harms = []
    try:
        rows = conn.execute(
            "SELECT * FROM extracted_harms_fts WHERE extracted_harms_fts MATCH ? "
            "ORDER BY rank LIMIT 15",
            (claim,)
        ).fetchall()
        harms = [dict(r) for r in rows]
    except Exception:
        pass

    conn.close()

    # Use LLM to synthesize chain
    context = json.dumps({
        'evidence_count': len(evidence),
        'adversary_assertions_count': len(adversary_assertions),
        'harms_count': len(harms),
        'sample_evidence': [str(e)[:200] for e in evidence[:5]],
    }, default=str)

    try:
        synthesis = llm_ask(
            f"Build an evidence chain for the claim: '{claim}'\n"
            f"Against adversary: '{adversary}'\n"
            f"Available evidence context: {context}\n\n"
            f"Create a numbered chain linking evidence to the claim. "
            f"Identify the strongest pieces and any gaps.",
            system_prompt=(
                "You are a litigation evidence specialist for Michigan courts. Rules:\n"
                "1. Number each link in the chain: Evidence → Fact Established → Legal Element\n"
                "2. Rate each link: STRONG (direct proof), MODERATE (circumstantial), WEAK (inferential)\n"
                "3. Identify gaps where additional evidence is needed\n"
                "4. Only reference evidence present in the provided context — never fabricate exhibits"
            )
        )
    except Exception as e:
        synthesis = f"LLM unavailable: {e}"

    result = {
        'claim': claim,
        'adversary': adversary,
        'evidence_found': len(evidence),
        'adversary_assertions': len(adversary_assertions),
        'harms_linked': len(harms),
        'chain_synthesis': synthesis,
        'evidence_preview': [str(e)[:150] for e in evidence[:10]],
    }
    log_activity(f'build_chain:{claim[:50]}', json.dumps(result, default=str)[:2000])
    return result


def check_authentication(exhibit: str) -> dict:
    """Check MRE 901 authentication requirements for an exhibit."""
    conn = get_conn()

    # MRE 901 authentication methods
    mre_901_methods = {
        '901(b)(1)': 'Testimony of witness with knowledge',
        '901(b)(2)': 'Nonexpert opinion on handwriting',
        '901(b)(3)': 'Comparison by trier or expert witness',
        '901(b)(4)': 'Distinctive characteristics',
        '901(b)(5)': 'Voice identification',
        '901(b)(6)': 'Telephone conversations',
        '901(b)(7)': 'Public records or reports',
        '901(b)(8)': 'Ancient documents or data compilations',
        '901(b)(9)': 'Process or system',
        '901(b)(10)': 'Methods provided by statute or rule',
    }

    # Look up exhibit in registry
    exhibit_info = None
    try:
        rows = conn.execute(
            "SELECT * FROM exhibit_registry WHERE exhibit_id LIKE ? OR description LIKE ? LIMIT 5",
            (f'%{exhibit}%', f'%{exhibit}%')
        ).fetchall()
        if rows:
            exhibit_info = [dict(r) for r in rows]
    except Exception:
        pass

    conn.close()

    # LLM analysis of authentication requirements
    try:
        analysis = llm_ask(
            f"Analyze authentication requirements for exhibit: '{exhibit}'\n"
            f"Exhibit info from registry: {json.dumps(exhibit_info, default=str)[:500]}\n\n"
            f"Under MRE 901, identify: (1) which authentication method(s) apply, "
            f"(2) what foundation must be laid, (3) potential challenges to authentication.",
            system_prompt=(
                "You are a Michigan evidence law expert. Rules:\n"
                "1. Cite specific MRE 901 subsections (e.g., MRE 901(b)(1) testimony of witness with knowledge)\n"
                "2. Only cite rules present in the context — mark others UNVERIFIED\n"
                "3. For each exhibit, specify: authentication method, required foundation, likely challenges\n"
                "4. Note if a self-authenticating exception under MRE 902 may apply"
            )
        )
    except Exception as e:
        analysis = f"LLM unavailable: {e}"

    result = {
        'exhibit': exhibit,
        'mre_901_methods': mre_901_methods,
        'exhibit_registry_match': exhibit_info,
        'authentication_analysis': analysis,
    }
    log_activity(f'check_auth:{exhibit[:50]}', json.dumps(result, default=str)[:2000])
    return result


def bates_number(exhibit_list: str) -> dict:
    """Assign Bates numbers to a list of exhibits."""
    exhibits = [e.strip() for e in exhibit_list.split(',')]
    conn = get_conn()

    # Check for existing Bates assignments
    existing = {}
    try:
        for ex in exhibits:
            rows = conn.execute(
                "SELECT * FROM exhibit_registry WHERE exhibit_id LIKE ? LIMIT 1",
                (f'%{ex}%',)
            ).fetchall()
            if rows:
                existing[ex] = dict(rows[0])
    except Exception:
        pass

    # Get next available Bates number
    try:
        max_bates = conn.execute(
            "SELECT MAX(CAST(bates_end AS INTEGER)) FROM exhibit_registry "
            "WHERE bates_end IS NOT NULL AND bates_end != ''"
        ).fetchone()[0]
        next_bates = (max_bates or 0) + 1
    except Exception:
        next_bates = 1

    # Assign new numbers
    assignments = []
    current_bates = next_bates
    for ex in exhibits:
        if ex in existing:
            assignments.append({
                'exhibit': ex,
                'status': 'existing',
                'info': str(existing[ex])[:200],
            })
        else:
            bates_start = current_bates
            bates_end = current_bates + 9  # default 10 pages
            assignments.append({
                'exhibit': ex,
                'status': 'assigned',
                'bates_start': f'{bates_start:06d}',
                'bates_end': f'{bates_end:06d}',
            })
            current_bates = bates_end + 1

    conn.close()

    result = {
        'exhibits': exhibits,
        'assignments': assignments,
        'next_available_bates': current_bates,
    }
    log_activity('bates_number', json.dumps(result, default=str)[:2000])
    return result


def gap_analysis(filing_stack: str) -> dict:
    """Find evidence gaps in a filing stack."""
    conn = get_conn()

    # Get filing stack claims/counts
    stack_info = {}
    try:
        rows = conn.execute(
            "SELECT * FROM apex_filing_stack_index WHERE stack_label LIKE ? OR meek_track LIKE ?",
            (f'%{filing_stack}%', f'%{filing_stack}%')
        ).fetchall()
        stack_info['filings'] = [dict(r) for r in rows]
    except Exception:
        stack_info['filings'] = []

    # Evidence coverage
    evidence_count = 0
    try:
        evidence_count = conn.execute('SELECT COUNT(*) FROM evidence_quotes').fetchone()[0]
    except Exception:
        pass

    # Harms coverage
    harms_count = 0
    try:
        harms_count = conn.execute('SELECT COUNT(*) FROM extracted_harms').fetchone()[0]
    except Exception:
        pass

    # Rebuttal coverage
    rebuttal_count = 0
    try:
        rebuttal_count = conn.execute('SELECT COUNT(*) FROM rebuttal_matrix').fetchone()[0]
    except Exception:
        pass

    conn.close()

    # LLM gap analysis
    try:
        analysis = llm_ask(
            f"Perform evidence gap analysis for filing stack: '{filing_stack}'\n"
            f"Total evidence quotes: {evidence_count}\n"
            f"Total extracted harms: {harms_count}\n"
            f"Total rebuttals: {rebuttal_count}\n"
            f"Filing info: {json.dumps(stack_info, default=str)[:800]}\n\n"
            f"Identify: (1) claims lacking evidence support, (2) evidence not linked to claims, "
            f"(3) harms without remedies, (4) unrebutted adversary assertions.",
            system_prompt=(
                "You are a litigation evidence analyst identifying gaps. Rules:\n"
                "1. For each gap found, classify: CRITICAL (blocks claim), MODERATE (weakens argument), MINOR\n"
                "2. Suggest specific evidence types that could fill each gap\n"
                "3. Only reference claims/evidence present in the provided context\n"
                "4. Never fabricate evidence counts or statistics — report only what is provided"
            )
        )
    except Exception as e:
        analysis = f"LLM unavailable: {e}"

    result = {
        'filing_stack': filing_stack,
        'evidence_quotes_total': evidence_count,
        'extracted_harms_total': harms_count,
        'rebuttal_total': rebuttal_count,
        'stack_filings': len(stack_info.get('filings', [])),
        'gap_analysis': analysis,
    }
    log_activity(f'gap_analysis:{filing_stack}', json.dumps(result, default=str)[:2000])
    return result


# ── CLI ──────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description='Delta999 Evidence Chain Agent')
    parser.add_argument('--action', required=True,
                        choices=['search', 'build_chain', 'check_auth', 'bates', 'gap_analysis'],
                        help='Action to perform')
    parser.add_argument('--query', type=str, help='Search query')
    parser.add_argument('--claim', type=str, help='Claim for evidence chain')
    parser.add_argument('--adversary', type=str, default='', help='Adversary name')
    parser.add_argument('--exhibit', type=str, help='Exhibit identifier')
    parser.add_argument('--exhibits', type=str, help='Comma-separated exhibit list')
    parser.add_argument('--filing-stack', type=str, help='Filing stack identifier')
    args = parser.parse_args()

    if args.action == 'search':
        if not args.query:
            parser.error('--query required')
        result = search_evidence(args.query)
    elif args.action == 'build_chain':
        if not args.claim:
            parser.error('--claim required')
        result = build_evidence_chain(args.claim, args.adversary)
    elif args.action == 'check_auth':
        if not args.exhibit:
            parser.error('--exhibit required')
        result = check_authentication(args.exhibit)
    elif args.action == 'bates':
        if not args.exhibits:
            parser.error('--exhibits required')
        result = bates_number(args.exhibits)
    elif args.action == 'gap_analysis':
        if not args.filing_stack:
            parser.error('--filing-stack required')
        result = gap_analysis(args.filing_stack)
    else:
        parser.print_help()
        return

    print(json.dumps(result, indent=2, default=str))


if __name__ == '__main__':
    main()
