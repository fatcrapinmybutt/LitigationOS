#!/usr/bin/env python3
"""
Delta999 Rebuttal Agent — Adversary rebuttal specialist.

Predicts opposing defense arguments, builds counter-arguments with authority,
plans impeachment using evidence inconsistencies, and identifies weaknesses.

CLI:
    python delta999_rebuttal_agent.py --action predict_defense --filing-stack "MEEK1"
    python delta999_rebuttal_agent.py --action build_rebuttal --defense "res judicata"
    python delta999_rebuttal_agent.py --action impeachment_plan --adversary "FOC"
    python delta999_rebuttal_agent.py --action weakness_analysis --filing-stack "MEEK1"
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
AGENT_NAME = 'delta999_rebuttal_agent'

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

def predict_defense(filing_stack: str) -> dict:
    """Predict opposing arguments the adversary will raise."""
    conn = get_conn()

    # Gather adversary assertions
    adversary_data = []
    try:
        rows = conn.execute(
            "SELECT * FROM adversary_assertions ORDER BY rowid DESC LIMIT 30"
        ).fetchall()
        adversary_data = [dict(r) for r in rows]
    except Exception:
        pass

    # Gather filing stack info
    stack_info = []
    try:
        rows = conn.execute(
            "SELECT * FROM apex_filing_stack_index WHERE stack_label LIKE ? OR meek_track LIKE ?",
            (f'%{filing_stack}%', f'%{filing_stack}%')
        ).fetchall()
        stack_info = [dict(r) for r in rows]
    except Exception:
        pass

    # Existing rebuttals
    rebuttals = []
    try:
        rows = conn.execute('SELECT * FROM rebuttal_matrix LIMIT 20').fetchall()
        rebuttals = [dict(r) for r in rows]
    except Exception:
        pass

    conn.close()

    # LLM prediction
    try:
        prediction = llm_ask(
            f"Predict the opposing party's defense arguments for filing stack: '{filing_stack}'\n\n"
            f"Known adversary assertions ({len(adversary_data)}):\n"
            f"{json.dumps(adversary_data[:5], default=str)[:800]}\n\n"
            f"Filing stack info:\n{json.dumps(stack_info[:3], default=str)[:400]}\n\n"
            f"Existing rebuttals ({len(rebuttals)}):\n"
            f"{json.dumps(rebuttals[:3], default=str)[:400]}\n\n"
            f"For each predicted defense:\n"
            f"1. State the defense argument\n"
            f"2. Cite the legal basis they would use\n"
            f"3. Rate likelihood (high/medium/low)\n"
            f"4. Suggest counter-argument strategy",
            system_prompt=(
                "You are a Michigan litigation strategist predicting adversary defenses. "
                "Consider: res judicata, collateral estoppel, statute of limitations, "
                "immunity, standing, failure to state a claim, qualified immunity, "
                "abstention doctrines. Be specific about Michigan law."
            )
        )
    except Exception as e:
        prediction = f"LLM unavailable: {e}"

    result = {
        'filing_stack': filing_stack,
        'adversary_assertions_analyzed': len(adversary_data),
        'existing_rebuttals': len(rebuttals),
        'predicted_defenses': prediction,
    }
    log_activity(f'predict_defense:{filing_stack}', json.dumps(result, default=str)[:2000])
    return result


def build_rebuttal(defense_argument: str) -> dict:
    """Build a counter-argument with authority for a specific defense."""
    conn = get_conn()

    # Search for relevant rebuttals already in DB
    existing = []
    try:
        rows = conn.execute(
            "SELECT * FROM rebuttal_matrix_fts WHERE rebuttal_matrix_fts MATCH ? "
            "ORDER BY rank LIMIT 10",
            (defense_argument,)
        ).fetchall()
        existing = [dict(r) for r in rows]
    except Exception:
        pass

    # Search authority
    authorities = []
    for fts in ['auth_rules_fts', 'caselaw_unified_fts', 'auth_passages_fts']:
        try:
            rows = conn.execute(
                f"SELECT * FROM [{fts}] WHERE [{fts}] MATCH ? ORDER BY rank LIMIT 5",
                (defense_argument,)
            ).fetchall()
            authorities.extend([dict(r) for r in rows])
        except Exception:
            pass

    # Search impeachment index
    impeachment = []
    try:
        rows = conn.execute(
            "SELECT * FROM impeachment_index_fts WHERE impeachment_index_fts MATCH ? "
            "ORDER BY rank LIMIT 5",
            (defense_argument,)
        ).fetchall()
        impeachment = [dict(r) for r in rows]
    except Exception:
        pass

    conn.close()

    # LLM rebuttal construction
    try:
        rebuttal = llm_ask(
            f"Build a legal rebuttal against the defense: '{defense_argument}'\n\n"
            f"Existing rebuttals in DB ({len(existing)}):\n"
            f"{json.dumps(existing[:3], default=str)[:600]}\n\n"
            f"Available authorities ({len(authorities)}):\n"
            f"{json.dumps(authorities[:5], default=str)[:600]}\n\n"
            f"Impeachment material ({len(impeachment)}):\n"
            f"{json.dumps(impeachment[:3], default=str)[:400]}\n\n"
            f"Structure the rebuttal:\n"
            f"1. Restate and characterize the defense\n"
            f"2. Legal standard that defeats it\n"
            f"3. Factual basis from evidence\n"
            f"4. Authority citations\n"
            f"5. Conclusion",
            system_prompt=(
                "You are a Michigan litigation rebuttal specialist. "
                "Build thorough, authority-backed rebuttals. "
                "Cite specific MCL, MCR, and Michigan case law."
            )
        )
    except Exception as e:
        rebuttal = f"LLM unavailable: {e}"

    result = {
        'defense_argument': defense_argument,
        'existing_rebuttals_found': len(existing),
        'authorities_found': len(authorities),
        'impeachment_material': len(impeachment),
        'rebuttal': rebuttal,
    }
    log_activity(f'build_rebuttal:{defense_argument[:50]}', json.dumps(result, default=str)[:2000])
    return result


def impeachment_plan(adversary: str) -> dict:
    """Build impeachment plan identifying inconsistencies for a specific adversary."""
    conn = get_conn()

    # Adversary assertions
    assertions = []
    try:
        rows = conn.execute(
            "SELECT * FROM adversary_assertions_fts WHERE adversary_assertions_fts MATCH ? "
            "ORDER BY rank LIMIT 30",
            (adversary,)
        ).fetchall()
        assertions = [dict(r) for r in rows]
    except Exception:
        pass

    # Evidence quotes mentioning adversary
    evidence = []
    try:
        rows = conn.execute(
            "SELECT * FROM evidence_quotes_fts WHERE evidence_quotes_fts MATCH ? "
            "ORDER BY rank LIMIT 30",
            (adversary,)
        ).fetchall()
        evidence = [dict(r) for r in rows]
    except Exception:
        pass

    # Extracted harms
    harms = []
    try:
        rows = conn.execute(
            "SELECT * FROM extracted_harms_fts WHERE extracted_harms_fts MATCH ? "
            "ORDER BY rank LIMIT 20",
            (adversary,)
        ).fetchall()
        harms = [dict(r) for r in rows]
    except Exception:
        pass

    # Impeachment index
    impeach_records = []
    try:
        rows = conn.execute(
            "SELECT * FROM impeachment_index_fts WHERE impeachment_index_fts MATCH ? "
            "ORDER BY rank LIMIT 20",
            (adversary,)
        ).fetchall()
        impeach_records = [dict(r) for r in rows]
    except Exception:
        pass

    conn.close()

    # LLM impeachment plan
    try:
        plan = llm_ask(
            f"Build an impeachment plan for adversary: '{adversary}'\n\n"
            f"Their assertions ({len(assertions)}):\n"
            f"{json.dumps(assertions[:5], default=str)[:600]}\n\n"
            f"Contradicting evidence ({len(evidence)}):\n"
            f"{json.dumps(evidence[:5], default=str)[:600]}\n\n"
            f"Documented harms ({len(harms)}):\n"
            f"{json.dumps(harms[:3], default=str)[:400]}\n\n"
            f"Existing impeachment records ({len(impeach_records)}):\n"
            f"{json.dumps(impeach_records[:3], default=str)[:400]}\n\n"
            f"Identify:\n"
            f"1. Specific contradictions between assertions and evidence\n"
            f"2. Prior inconsistent statements\n"
            f"3. Bias or motive evidence\n"
            f"4. Character for untruthfulness (MRE 608/609)\n"
            f"5. Recommended impeachment sequence for cross-examination",
            system_prompt=(
                "You are a Michigan trial impeachment specialist. "
                "Reference MRE 607, 608, 609, 613, and 801(d)(1). "
                "Be specific about contradictions and inconsistencies."
            )
        )
    except Exception as e:
        plan = f"LLM unavailable: {e}"

    result = {
        'adversary': adversary,
        'assertions_analyzed': len(assertions),
        'evidence_found': len(evidence),
        'harms_documented': len(harms),
        'existing_impeachment': len(impeach_records),
        'impeachment_plan': plan,
    }
    log_activity(f'impeachment:{adversary[:50]}', json.dumps(result, default=str)[:2000])
    return result


def weakness_analysis(filing_stack: str) -> dict:
    """Find weaknesses in our filing before the opponent does."""
    conn = get_conn()

    # Get stack info
    stack_info = []
    try:
        rows = conn.execute(
            "SELECT * FROM apex_filing_stack_index WHERE stack_label LIKE ? OR meek_track LIKE ?",
            (f'%{filing_stack}%', f'%{filing_stack}%')
        ).fetchall()
        stack_info = [dict(r) for r in rows]
    except Exception:
        pass

    # Evidence coverage
    ev_count = 0
    try:
        ev_count = conn.execute('SELECT COUNT(*) FROM evidence_quotes').fetchone()[0]
    except Exception:
        pass

    # Constitutional violations
    violations = []
    try:
        rows = conn.execute('SELECT * FROM constitutional_violations LIMIT 10').fetchall()
        violations = [dict(r) for r in rows]
    except Exception:
        pass

    conn.close()

    # LLM weakness analysis
    try:
        analysis = llm_ask(
            f"Perform a weakness analysis of filing stack: '{filing_stack}'\n\n"
            f"Stack info: {json.dumps(stack_info[:3], default=str)[:500]}\n"
            f"Evidence quotes available: {ev_count}\n"
            f"Constitutional violations documented: {len(violations)}\n\n"
            f"Identify:\n"
            f"1. Weakest claims (insufficient evidence)\n"
            f"2. Procedural vulnerabilities\n"
            f"3. Standing issues\n"
            f"4. Statute of limitations risks\n"
            f"5. Inconsistencies within our own filings\n"
            f"6. Missing elements for each cause of action\n"
            f"7. Recommended fixes for each weakness",
            system_prompt=(
                "You are a litigation risk analyst performing internal weakness assessment. "
                "Be brutally honest. Think like the opposing counsel. "
                "Cite Michigan law for each vulnerability identified."
            )
        )
    except Exception as e:
        analysis = f"LLM unavailable: {e}"

    result = {
        'filing_stack': filing_stack,
        'filings_analyzed': len(stack_info),
        'evidence_available': ev_count,
        'violations_documented': len(violations),
        'weakness_analysis': analysis,
    }
    log_activity(f'weakness:{filing_stack}', json.dumps(result, default=str)[:2000])
    return result


# ── CLI ──────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description='Delta999 Rebuttal Agent')
    parser.add_argument('--action', required=True,
                        choices=['predict_defense', 'build_rebuttal',
                                 'impeachment_plan', 'weakness_analysis'],
                        help='Action to perform')
    parser.add_argument('--filing-stack', type=str, help='Filing stack identifier')
    parser.add_argument('--defense', type=str, help='Defense argument to rebut')
    parser.add_argument('--adversary', type=str, help='Adversary name')
    args = parser.parse_args()

    if args.action == 'predict_defense':
        if not args.filing_stack:
            parser.error('--filing-stack required')
        result = predict_defense(args.filing_stack)
    elif args.action == 'build_rebuttal':
        if not args.defense:
            parser.error('--defense required')
        result = build_rebuttal(args.defense)
    elif args.action == 'impeachment_plan':
        if not args.adversary:
            parser.error('--adversary required')
        result = impeachment_plan(args.adversary)
    elif args.action == 'weakness_analysis':
        if not args.filing_stack:
            parser.error('--filing-stack required')
        result = weakness_analysis(args.filing_stack)
    else:
        parser.print_help()
        return

    print(json.dumps(result, indent=2, default=str))


if __name__ == '__main__':
    main()
