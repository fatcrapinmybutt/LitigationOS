#!/usr/bin/env python3
"""
Delta999 COA Agent — COA 366810 specialist.

Handles word count checks, record citation validation, MCR 7.212 compliance,
expansion suggestions, and comprehensive brief validation.

CLI:
    python delta999_coa_agent.py --action check_word_count --brief-path "path/to/brief.docx"
    python delta999_coa_agent.py --action check_mcr_compliance --brief-path "path/to/brief.docx"
    python delta999_coa_agent.py --action suggest_expansion --section "Statement of Facts"
    python delta999_coa_agent.py --action validate_brief --brief-path "path/to/brief.docx"
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
AGENT_NAME = 'delta999_coa_agent'

from llm_bridge import llm_ask, llm_analyze_legal

# MCR 7.212 word limit
MAX_WORD_COUNT = 16000
COA_CASE = '366810'

# MCR 7.212 required sections
MCR_7212_SECTIONS = [
    'Cover Page',
    'Table of Contents',
    'Table of Authorities',
    'Statement of Jurisdiction',
    'Statement of Questions Presented',
    'Statement of Facts',
    'Argument',
    'Relief Requested',
    'Signature',
    'Certificate of Service',
    'Word Count Certificate',
]


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


# ── Text extraction ──────────────────────────────────────────────────────────

def extract_text(brief_path: str) -> str:
    """Extract text from a brief file (.txt, .md, .docx)."""
    p = Path(brief_path)
    if not p.exists():
        raise FileNotFoundError(f"Brief not found: {brief_path}")

    if p.suffix.lower() in ('.txt', '.md'):
        return p.read_text(encoding='utf-8')
    elif p.suffix.lower() == '.docx':
        try:
            from docx import Document
            doc = Document(str(p))
            return '\n'.join(para.text for para in doc.paragraphs)
        except ImportError:
            raise RuntimeError("python-docx not installed. Install with: pip install python-docx")
    else:
        return p.read_text(encoding='utf-8', errors='replace')


# ── Core functions ───────────────────────────────────────────────────────────

def check_word_count(brief_path: str) -> dict:
    """Check word count against MCR 7.212 16,000 word limit."""
    text = extract_text(brief_path)
    words = len(text.split())
    remaining = MAX_WORD_COUNT - words
    result = {
        'brief_path': brief_path,
        'word_count': words,
        'max_allowed': MAX_WORD_COUNT,
        'remaining': remaining,
        'over_limit': words > MAX_WORD_COUNT,
        'percentage_used': round((words / MAX_WORD_COUNT) * 100, 1),
        'rule': 'MCR 7.212(B)',
    }
    log_activity('check_word_count', json.dumps(result))
    return result


def check_record_citations(brief_path: str) -> dict:
    """Verify all record references in the brief follow proper format."""
    text = extract_text(brief_path)

    # Patterns for record citations: (R. 123), (T. 45), (Ex. A, p 12)
    record_patterns = {
        'transcript': r'\(T[.,]\s*(?:pp?\s*)?(\d+(?:\s*-\s*\d+)?)\)',
        'record': r'\(R[.,]\s*(?:pp?\s*)?(\d+(?:\s*-\s*\d+)?)\)',
        'exhibit': r'\(Ex[.,]\s*([A-Z0-9]+(?:\s*-\s*[A-Z0-9]+)?(?:,\s*pp?\s*\d+)?)\)',
        'appendix': r'\(App[.,]\s*(?:pp?\s*)?(\d+(?:\s*-\s*\d+)?)\)',
    }

    findings = {}
    total_citations = 0
    for name, pattern in record_patterns.items():
        matches = re.findall(pattern, text, re.IGNORECASE)
        findings[name] = {
            'count': len(matches),
            'references': matches[:20],
        }
        total_citations += len(matches)

    # Check for paragraphs that assert facts without citations
    paragraphs = text.split('\n\n')
    uncited_fact_paras = []
    for i, para in enumerate(paragraphs):
        if len(para.split()) > 30:  # substantial paragraph
            has_cite = any(
                re.search(p, para, re.IGNORECASE)
                for p in record_patterns.values()
            )
            if not has_cite and any(
                kw in para.lower()
                for kw in ['testified', 'stated', 'court found', 'record shows', 'evidence']
            ):
                uncited_fact_paras.append({
                    'paragraph_index': i,
                    'preview': para[:120] + '...',
                })

    result = {
        'brief_path': brief_path,
        'total_record_citations': total_citations,
        'citation_types': findings,
        'uncited_fact_paragraphs': uncited_fact_paras[:10],
        'issues_found': len(uncited_fact_paras),
    }
    log_activity('check_record_citations', json.dumps(result, default=str)[:2000])
    return result


def check_mcr_compliance(brief_path: str) -> dict:
    """Check brief against MCR 7.212 format checklist."""
    text = extract_text(brief_path)
    text_lower = text.lower()

    section_found = {}
    for section in MCR_7212_SECTIONS:
        patterns = [
            section.lower(),
            section.lower().replace(' ', ''),
        ]
        found = any(p in text_lower for p in patterns)
        section_found[section] = found

    missing = [s for s, found in section_found.items() if not found]

    # Word count check
    words = len(text.split())

    result = {
        'brief_path': brief_path,
        'case': f'COA {COA_CASE}',
        'rule': 'MCR 7.212',
        'sections_found': section_found,
        'missing_sections': missing,
        'word_count': words,
        'word_limit_ok': words <= MAX_WORD_COUNT,
        'compliant': len(missing) == 0 and words <= MAX_WORD_COUNT,
    }
    log_activity('check_mcr_compliance', json.dumps(result, default=str)[:2000])
    return result


def suggest_expansion(section: str) -> dict:
    """Suggest areas needing more content in a given section using LLM."""
    conn = get_conn()

    # Pull evidence and authority context from DB
    evidence = []
    try:
        rows = conn.execute(
            "SELECT quote, source_file FROM evidence_quotes "
            "WHERE quote LIKE ? LIMIT 20",
            (f'%{section}%',)
        ).fetchall()
        evidence = [{'quote': r['quote'][:200], 'source': r['source_file']} for r in rows]
    except Exception:
        pass

    conn.close()

    prompt = (
        f"You are drafting an appellate brief for COA Case No. {COA_CASE}.\n"
        f"Section: {section}\n"
        f"Available evidence count: {len(evidence)}\n\n"
        f"Suggest specific areas where this section should be expanded. "
        f"Focus on: (1) missing factual support, (2) under-argued legal points, "
        f"(3) record citations needed, (4) authority gaps.\n"
        f"Provide actionable expansion recommendations."
    )

    try:
        suggestions = llm_ask(prompt, system_prompt=(
            "You are an expert Michigan appellate attorney reviewing a brief "
            "for completeness under MCR 7.212. Be specific and actionable."
        ))
    except Exception as e:
        suggestions = f"LLM unavailable: {e}"

    result = {
        'section': section,
        'case': f'COA {COA_CASE}',
        'evidence_available': len(evidence),
        'suggestions': suggestions,
    }
    log_activity('suggest_expansion', json.dumps(result, default=str)[:2000])
    return result


def validate_brief(brief_path: str = None) -> dict:
    """Comprehensive brief validation combining all checks."""
    results = {}

    if brief_path:
        results['word_count'] = check_word_count(brief_path)
        results['record_citations'] = check_record_citations(brief_path)
        results['mcr_compliance'] = check_mcr_compliance(brief_path)

    # DB-based checks
    conn = get_conn()
    try:
        ev_count = conn.execute('SELECT COUNT(*) FROM evidence_quotes').fetchone()[0]
        results['evidence_count'] = ev_count
    except Exception:
        results['evidence_count'] = 'table not found'

    try:
        auth_count = conn.execute(
            "SELECT COUNT(*) FROM mcr_authority_library WHERE rule_number LIKE '7.212%'"
        ).fetchone()[0]
        results['mcr_7212_authorities'] = auth_count
    except Exception:
        results['mcr_7212_authorities'] = 'table not found'

    conn.close()

    # Overall assessment
    issues = []
    if brief_path:
        if results['word_count'].get('over_limit'):
            issues.append(f"Over word limit by {abs(results['word_count']['remaining'])} words")
        if results['mcr_compliance'].get('missing_sections'):
            issues.append(f"Missing sections: {', '.join(results['mcr_compliance']['missing_sections'])}")
        if results['record_citations'].get('issues_found', 0) > 0:
            issues.append(f"{results['record_citations']['issues_found']} uncited fact paragraphs")

    results['issues'] = issues
    results['overall_status'] = 'PASS' if not issues else 'NEEDS_ATTENTION'

    log_activity('validate_brief', json.dumps(results, default=str)[:2000])
    return results


# ── CLI ──────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description='Delta999 COA Agent — COA 366810 Specialist')
    parser.add_argument('--action', required=True,
                        choices=['check_word_count', 'check_record_citations',
                                 'check_mcr_compliance', 'suggest_expansion', 'validate_brief'],
                        help='Action to perform')
    parser.add_argument('--brief-path', type=str, help='Path to brief file')
    parser.add_argument('--section', type=str, help='Section name for expansion suggestions')
    args = parser.parse_args()

    if args.action == 'check_word_count':
        if not args.brief_path:
            parser.error('--brief-path required')
        result = check_word_count(args.brief_path)
    elif args.action == 'check_record_citations':
        if not args.brief_path:
            parser.error('--brief-path required')
        result = check_record_citations(args.brief_path)
    elif args.action == 'check_mcr_compliance':
        if not args.brief_path:
            parser.error('--brief-path required')
        result = check_mcr_compliance(args.brief_path)
    elif args.action == 'suggest_expansion':
        if not args.section:
            parser.error('--section required')
        result = suggest_expansion(args.section)
    elif args.action == 'validate_brief':
        result = validate_brief(args.brief_path)
    else:
        parser.print_help()
        return

    print(json.dumps(result, indent=2, default=str))


if __name__ == '__main__':
    main()
