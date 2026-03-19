#!/usr/bin/env python3
"""
Delta999 Citation Agent — Legal authority validator.

Validates citation format, searches all authority tables (MCL, MCR, MRE, FRCP,
case law), suggests authorities for claims, and bulk-validates document citations.

CLI:
    python delta999_citation_agent.py --action validate --citation "MCR 7.212(B)"
    python delta999_citation_agent.py --action search --topic "judicial disqualification"
    python delta999_citation_agent.py --action suggest --claim-type "due process violation"
    python delta999_citation_agent.py --action check_all --doc-path "path/to/brief.docx"
"""

import sys
sys.stdout.reconfigure(encoding='utf-8')

import argparse
import json
import os
import re
import sqlite3
from datetime import datetime
from pathlib import Path

# ── paths ────────────────────────────────────────────────────────────────────
AGENT_DIR = Path(__file__).parent
ENGINE_DIR = AGENT_DIR.parent
sys.path.insert(0, str(ENGINE_DIR))

DB = r'C:\Users\andre\LitigationOS\litigation_context.db'
AGENT_NAME = 'delta999_citation_agent'

from llm_bridge import llm_ask, llm_extract_legal_entities

# Authority tables to search
AUTHORITY_TABLES = {
    'mcl': 'mcl_authority_library',
    'mcr': 'mcr_authority_library',
    'mre': 'mre_authority_library',
    'frcp': 'frcp_authority_library',
    'caselaw': 'case_law_library',
}

# Citation format patterns
CITATION_PATTERNS = {
    'mcl': r'MCL\s+(\d+[\.\d]*[a-z]?)',
    'mcr': r'MCR\s+(\d+[\.\d]*(?:\([A-Z0-9]+\))*)',
    'mre': r'MRE\s+(\d+(?:\([a-z0-9]+\))*)',
    'frcp': r'(?:FRCP|Fed\s*R\s*Civ\s*P)\s+(\d+(?:\([a-z0-9]+\))*)',
    'usc': r'(\d+)\s+USC?\s+[§]?\s*(\d+)',
    'mich_case': r'(\d+)\s+Mich(?:\s+App)?\s+(\d+)',
    'nw2d': r'(\d+)\s+NW\s*2d\s+(\d+)',
    'fed_case': r'(\d+)\s+F\.\s*(?:2d|3d|4th)\s+(\d+)',
}


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

def validate_citation(citation_text: str) -> dict:
    """Validate a single citation: check format and verify existence in DB."""
    # Identify citation type
    detected_type = None
    detected_ref = None
    for ctype, pattern in CITATION_PATTERNS.items():
        m = re.search(pattern, citation_text, re.IGNORECASE)
        if m:
            detected_type = ctype
            detected_ref = m.group(0)
            break

    if not detected_type:
        result = {
            'citation': citation_text,
            'valid_format': False,
            'error': 'Unrecognized citation format',
            'suggestion': 'Expected formats: MCL 600.1234, MCR 2.003, MRE 901, FRCP 12(b)(6), 123 Mich App 456',
        }
        log_activity(f'validate:{citation_text[:50]}', json.dumps(result))
        return result

    # Check if it exists in authority tables
    conn = get_conn()
    found_in_db = False
    db_match = None

    # Search appropriate authority table
    table_map = {
        'mcl': ('mcl_authority_library', 'statute_number'),
        'mcr': ('mcr_authority_library', 'rule_number'),
        'mre': ('mre_authority_library', 'rule_number'),
        'frcp': ('frcp_authority_library', 'rule_number'),
    }

    if detected_type in table_map:
        table, col = table_map[detected_type]
        try:
            rows = conn.execute(
                f"SELECT * FROM [{table}] WHERE [{col}] LIKE ? LIMIT 3",
                (f'%{detected_ref.split()[-1]}%',)
            ).fetchall()
            if rows:
                found_in_db = True
                db_match = [dict(r) for r in rows]
        except Exception:
            pass

    elif detected_type in ('mich_case', 'nw2d', 'fed_case', 'caselaw'):
        try:
            rows = conn.execute(
                "SELECT * FROM case_law_library WHERE citation LIKE ? LIMIT 3",
                (f'%{citation_text[:30]}%',)
            ).fetchall()
            if rows:
                found_in_db = True
                db_match = [dict(r) for r in rows]
        except Exception:
            pass

    # Also search FTS
    fts_results = []
    try:
        for fts in ['auth_rules_fts', 'auth_passages_fts', 'caselaw_unified_fts']:
            rows = conn.execute(
                f"SELECT * FROM [{fts}] WHERE [{fts}] MATCH ? LIMIT 3",
                (citation_text,)
            ).fetchall()
            fts_results.extend([dict(r) for r in rows])
    except Exception:
        pass

    conn.close()

    result = {
        'citation': citation_text,
        'detected_type': detected_type,
        'detected_ref': detected_ref,
        'valid_format': True,
        'found_in_db': found_in_db,
        'db_match': db_match,
        'fts_matches': len(fts_results),
    }
    log_activity(f'validate:{citation_text[:50]}', json.dumps(result, default=str)[:2000])
    return result


def search_authority(topic: str) -> dict:
    """Search all authority tables for a given topic."""
    conn = get_conn()
    results = {}

    # Search each FTS index related to authority
    fts_searches = [
        ('auth_rules_fts', 'rules'),
        ('auth_passages_fts', 'passages'),
        ('caselaw_unified_fts', 'caselaw'),
    ]

    for fts_table, label in fts_searches:
        try:
            rows = conn.execute(
                f"SELECT *, rank FROM [{fts_table}] WHERE [{fts_table}] MATCH ? "
                f"ORDER BY rank LIMIT 15",
                (topic,)
            ).fetchall()
            results[label] = [dict(r) for r in rows]
        except Exception as e:
            results[label] = {'error': str(e)}

    # Search specific authority tables
    for lib_name, table_name in AUTHORITY_TABLES.items():
        try:
            # Get column names
            cur = conn.execute(f"PRAGMA table_info([{table_name}])")
            cols = [r[1] for r in cur.fetchall()]

            # Search text columns
            text_cols = [c for c in cols if any(k in c.lower() for k in ['text', 'title', 'description', 'name', 'content'])]
            if text_cols:
                where_clauses = ' OR '.join(f"[{c}] LIKE ?" for c in text_cols)
                params = [f'%{topic}%'] * len(text_cols)
                rows = conn.execute(
                    f"SELECT * FROM [{table_name}] WHERE {where_clauses} LIMIT 10",
                    params
                ).fetchall()
                results[f'{lib_name}_library'] = [dict(r) for r in rows]
        except Exception:
            pass

    conn.close()

    output = {
        'topic': topic,
        'sources_searched': list(results.keys()),
        'results': results,
        'total_matches': sum(
            len(v) if isinstance(v, list) else 0 for v in results.values()
        ),
    }
    log_activity(f'search_authority:{topic[:50]}', json.dumps(output, default=str)[:2000])
    return output


def suggest_authority(claim_type: str) -> dict:
    """Recommend authorities for a given claim type using DB + LLM."""
    conn = get_conn()

    # Gather context from authority tables
    context_parts = []
    for fts in ['auth_rules_fts', 'caselaw_unified_fts']:
        try:
            rows = conn.execute(
                f"SELECT * FROM [{fts}] WHERE [{fts}] MATCH ? ORDER BY rank LIMIT 10",
                (claim_type,)
            ).fetchall()
            context_parts.extend([str(dict(r))[:200] for r in rows])
        except Exception:
            pass

    conn.close()

    # LLM recommendation
    try:
        suggestions = llm_ask(
            f"Suggest legal authorities for the claim type: '{claim_type}'\n\n"
            f"Available authority context from DB:\n{chr(10).join(context_parts[:10])}\n\n"
            f"Provide: (1) Primary Michigan statutes (MCL), (2) Court Rules (MCR), "
            f"(3) Evidence Rules (MRE), (4) Key Michigan case law, "
            f"(5) Federal authorities if applicable.\n"
            f"For each, explain its relevance.",
            system_prompt=(
                "You are a Michigan litigation authority specialist. "
                "Cite specific statutes, rules, and cases with full citations."
            )
        )
    except Exception as e:
        suggestions = f"LLM unavailable: {e}"

    result = {
        'claim_type': claim_type,
        'db_authorities_found': len(context_parts),
        'suggestions': suggestions,
    }
    log_activity(f'suggest:{claim_type[:50]}', json.dumps(result, default=str)[:2000])
    return result


def check_all_citations(document_path: str) -> dict:
    """Validate all citations found in a document."""
    p = Path(document_path)
    if not p.exists():
        raise FileNotFoundError(f"Document not found: {document_path}")

    if p.suffix.lower() in ('.txt', '.md'):
        text = p.read_text(encoding='utf-8')
    elif p.suffix.lower() == '.docx':
        try:
            from docx import Document
            doc = Document(str(p))
            text = '\n'.join(para.text for para in doc.paragraphs)
        except ImportError:
            raise RuntimeError("python-docx required")
    else:
        text = p.read_text(encoding='utf-8', errors='replace')

    # Extract all citations
    all_citations = []
    for ctype, pattern in CITATION_PATTERNS.items():
        matches = re.finditer(pattern, text, re.IGNORECASE)
        for m in matches:
            all_citations.append({
                'type': ctype,
                'text': m.group(0),
                'position': m.start(),
            })

    # Validate each unique citation
    unique_cites = list({c['text'] for c in all_citations})
    validations = {}
    for cite in unique_cites[:50]:  # cap at 50
        validations[cite] = validate_citation(cite)

    valid_count = sum(1 for v in validations.values() if v.get('found_in_db'))
    format_ok = sum(1 for v in validations.values() if v.get('valid_format'))

    result = {
        'document_path': document_path,
        'total_citations_found': len(all_citations),
        'unique_citations': len(unique_cites),
        'valid_format': format_ok,
        'found_in_db': valid_count,
        'not_verified': len(unique_cites) - valid_count,
        'validations': validations,
    }
    log_activity(f'check_all:{document_path}', json.dumps(result, default=str)[:2000])
    return result


# ── CLI ──────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description='Delta999 Citation Agent')
    parser.add_argument('--action', required=True,
                        choices=['validate', 'search', 'suggest', 'check_all'],
                        help='Action to perform')
    parser.add_argument('--citation', type=str, help='Citation text to validate')
    parser.add_argument('--topic', type=str, help='Topic for authority search')
    parser.add_argument('--claim-type', type=str, help='Claim type for suggestions')
    parser.add_argument('--doc-path', type=str, help='Document path for bulk check')
    args = parser.parse_args()

    if args.action == 'validate':
        if not args.citation:
            parser.error('--citation required')
        result = validate_citation(args.citation)
    elif args.action == 'search':
        if not args.topic:
            parser.error('--topic required')
        result = search_authority(args.topic)
    elif args.action == 'suggest':
        if not args.claim_type:
            parser.error('--claim-type required')
        result = suggest_authority(args.claim_type)
    elif args.action == 'check_all':
        if not args.doc_path:
            parser.error('--doc-path required')
        result = check_all_citations(args.doc_path)
    else:
        parser.print_help()
        return

    print(json.dumps(result, indent=2, default=str))


if __name__ == '__main__':
    main()
