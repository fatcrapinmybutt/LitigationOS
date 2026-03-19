#!/usr/bin/env python3
"""
Delta999 Red Team Agent — War-gaming and vulnerability assessment.

Attacks filings to find weaknesses, audits statute of limitations,
checks immunity/abstention defenses, predicts adversary responses,
and generates risk matrices.

CLI:
    python delta999_redteam_agent.py --action attack --filing-stack "MEEK1"
    python delta999_redteam_agent.py --action sol_audit --filing-stack "MEEK1"
    python delta999_redteam_agent.py --action immunity_audit --filing-stack "MEEK1"
    python delta999_redteam_agent.py --action predict_response --filing-stack "MEEK1" --adversary "FOC"
    python delta999_redteam_agent.py --action risk_matrix
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
AGENT_NAME = 'delta999_redteam_agent'

from llm_bridge import llm_ask, llm_analyze_legal

# Michigan statutes of limitation reference
SOL_REFERENCE = {
    'personal_injury': {'years': 3, 'mcl': 'MCL 600.5805(2)'},
    'property_damage': {'years': 3, 'mcl': 'MCL 600.5805(2)'},
    'fraud': {'years': 6, 'mcl': 'MCL 600.5813'},
    'contract_written': {'years': 6, 'mcl': 'MCL 600.5807(8)'},
    'contract_oral': {'years': 6, 'mcl': 'MCL 600.5807(8)'},
    'malpractice_legal': {'years': 2, 'mcl': 'MCL 600.5805(6)'},
    'civil_rights_1983': {'years': 3, 'mcl': '42 USC 1983 (state borrowing)'},
    'civil_rights_state': {'years': 3, 'mcl': 'MCL 600.5805'},
    'libel_slander': {'years': 1, 'mcl': 'MCL 600.5805(9)'},
    'governmental_tort': {'years': 3, 'mcl': 'MCL 691.1411', 'notice': '120 days MCL 691.1404'},
}

# Immunity/abstention doctrines
IMMUNITY_DOCTRINES = {
    'judicial_immunity': 'Absolute immunity for judicial acts within jurisdiction',
    'quasi_judicial_immunity': 'For court officers acting in quasi-judicial capacity',
    'prosecutorial_immunity': 'Absolute immunity for prosecutorial functions',
    'governmental_immunity': 'MCL 691.1407 — general governmental immunity',
    'qualified_immunity': '42 USC 1983 — clearly established rights test',
    'sovereign_immunity': '11th Amendment — state sovereign immunity',
    'rooker_feldman': 'State court judgment review barred in federal court',
    'younger_abstention': 'Federal abstention from pending state proceedings',
    'colorado_river': 'Abstention for parallel state proceedings',
    'domestic_relations': 'Federal abstention from domestic relations matters',
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

def attack_filing(filing_stack: str) -> dict:
    """Find top 10 weaknesses in a filing stack (red team perspective)."""
    conn = get_conn()

    # Gather filing data
    stack_info = []
    try:
        rows = conn.execute(
            "SELECT * FROM apex_filing_stack_index WHERE stack_label LIKE ? OR meek_track LIKE ?",
            (f'%{filing_stack}%', f'%{filing_stack}%')
        ).fetchall()
        stack_info = [dict(r) for r in rows]
    except Exception:
        pass

    # Evidence count
    ev_count = 0
    try:
        ev_count = conn.execute('SELECT COUNT(*) FROM evidence_quotes').fetchone()[0]
    except Exception:
        pass

    # Constitutional violations
    violations = []
    try:
        rows = conn.execute('SELECT * FROM constitutional_violations LIMIT 15').fetchall()
        violations = [dict(r) for r in rows]
    except Exception:
        pass

    # Adversary assertions
    adv_assertions = []
    try:
        rows = conn.execute('SELECT * FROM adversary_assertions LIMIT 15').fetchall()
        adv_assertions = [dict(r) for r in rows]
    except Exception:
        pass

    conn.close()

    # LLM red team attack
    try:
        attack = llm_ask(
            f"RED TEAM ATTACK on filing stack: '{filing_stack}'\n\n"
            f"You are opposing counsel. Find the TOP 10 WEAKNESSES.\n\n"
            f"Filing info: {json.dumps(stack_info[:5], default=str)[:600]}\n"
            f"Evidence quotes: {ev_count}\n"
            f"Constitutional violations claimed: {len(violations)}\n"
            f"Adversary has asserted: {json.dumps(adv_assertions[:5], default=str)[:500]}\n\n"
            f"For each weakness:\n"
            f"1. Vulnerability description\n"
            f"2. How opposing counsel would exploit it\n"
            f"3. Specific motion they would file\n"
            f"4. Authority they would cite\n"
            f"5. Severity (Critical/High/Medium/Low)\n"
            f"6. Recommended fix",
            system_prompt=(
                "You are an aggressive opposing counsel looking for every weakness. "
                "Think: 12(b)(6) motions, summary judgment, SOL defenses, immunity, "
                "standing, jurisdiction, res judicata, waiver, estoppel. "
                "Be ruthless and specific. Cite Michigan law."
            )
        )
    except Exception as e:
        attack = f"LLM unavailable: {e}"

    result = {
        'filing_stack': filing_stack,
        'filings_analyzed': len(stack_info),
        'evidence_available': ev_count,
        'violations_claimed': len(violations),
        'top_10_attack': attack,
    }
    log_activity(f'attack:{filing_stack}', json.dumps(result, default=str)[:2000])
    return result


def sol_audit(filing_stack: str) -> dict:
    """Statute of limitations analysis for every count in a filing stack."""
    conn = get_conn()

    # Get filings/counts
    stack_info = []
    try:
        rows = conn.execute(
            "SELECT * FROM apex_filing_stack_index WHERE stack_label LIKE ? OR meek_track LIKE ?",
            (f'%{filing_stack}%', f'%{filing_stack}%')
        ).fetchall()
        stack_info = [dict(r) for r in rows]
    except Exception:
        pass

    # Timeline for dates
    timeline = []
    try:
        rows = conn.execute(
            "SELECT event_date, description FROM master_timeline "
            "ORDER BY event_date ASC LIMIT 30"
        ).fetchall()
        timeline = [dict(r) for r in rows]
    except Exception:
        pass

    conn.close()

    # LLM SOL analysis
    try:
        analysis = llm_ask(
            f"STATUTE OF LIMITATIONS AUDIT for filing stack: '{filing_stack}'\n\n"
            f"Michigan SOL Reference:\n{json.dumps(SOL_REFERENCE, indent=2)}\n\n"
            f"Filing stack: {json.dumps(stack_info[:5], default=str)[:600]}\n"
            f"Timeline events: {json.dumps(timeline[:10], default=str)[:600]}\n\n"
            f"For each count/claim:\n"
            f"1. Identify the cause of action\n"
            f"2. Applicable SOL period and MCL citation\n"
            f"3. Accrual date (when did the claim accrue?)\n"
            f"4. Expiration date\n"
            f"5. Tolling arguments (discovery rule, fraudulent concealment, continuing wrong)\n"
            f"6. Status: SAFE / AT RISK / EXPIRED\n"
            f"7. Recommended action if at risk",
            system_prompt=(
                "You are a Michigan statute of limitations expert. "
                "Apply MCL 600.5805 et seq. Consider discovery rule (MCL 600.5838a), "
                "fraudulent concealment (MCL 600.5855), minority tolling, "
                "and continuing wrong doctrine."
            )
        )
    except Exception as e:
        analysis = f"LLM unavailable: {e}"

    result = {
        'filing_stack': filing_stack,
        'sol_reference': SOL_REFERENCE,
        'filings_analyzed': len(stack_info),
        'timeline_events': len(timeline),
        'sol_analysis': analysis,
    }
    log_activity(f'sol_audit:{filing_stack}', json.dumps(result, default=str)[:2000])
    return result


def immunity_audit(filing_stack: str) -> dict:
    """Analyze immunity and abstention defenses applicable to the filing stack."""
    conn = get_conn()

    # Get defendants/respondents from filings
    stack_info = []
    try:
        rows = conn.execute(
            "SELECT * FROM apex_filing_stack_index WHERE stack_label LIKE ? OR meek_track LIKE ?",
            (f'%{filing_stack}%', f'%{filing_stack}%')
        ).fetchall()
        stack_info = [dict(r) for r in rows]
    except Exception:
        pass

    # Search authority for immunity
    immunity_auth = []
    for fts in ['auth_rules_fts', 'caselaw_unified_fts']:
        try:
            rows = conn.execute(
                f"SELECT * FROM [{fts}] WHERE [{fts}] MATCH 'immunity OR abstention OR sovereign' "
                f"ORDER BY rank LIMIT 10"
            ).fetchall()
            immunity_auth.extend([dict(r) for r in rows])
        except Exception:
            pass

    conn.close()

    # LLM immunity analysis
    try:
        analysis = llm_ask(
            f"IMMUNITY & ABSTENTION AUDIT for filing stack: '{filing_stack}'\n\n"
            f"Known immunity/abstention doctrines:\n"
            f"{json.dumps(IMMUNITY_DOCTRINES, indent=2)}\n\n"
            f"Filing stack: {json.dumps(stack_info[:5], default=str)[:600]}\n"
            f"Immunity authority found: {len(immunity_auth)}\n\n"
            f"For each defendant/respondent:\n"
            f"1. Which immunity doctrines could they assert?\n"
            f"2. Likelihood of success (high/medium/low)\n"
            f"3. How to overcome/defeat each immunity claim\n"
            f"4. Exceptions that apply\n"
            f"5. Key Michigan cases on point",
            system_prompt=(
                "You are a Michigan immunity law expert. "
                "Analyze governmental immunity (MCL 691.1407), "
                "judicial immunity, qualified immunity under § 1983, "
                "and federal abstention doctrines. "
                "Focus on exceptions and ways to overcome."
            )
        )
    except Exception as e:
        analysis = f"LLM unavailable: {e}"

    result = {
        'filing_stack': filing_stack,
        'immunity_doctrines': IMMUNITY_DOCTRINES,
        'filings_analyzed': len(stack_info),
        'immunity_authorities_found': len(immunity_auth),
        'immunity_analysis': analysis,
    }
    log_activity(f'immunity:{filing_stack}', json.dumps(result, default=str)[:2000])
    return result


def predict_response(filing_stack: str, adversary: str = '') -> dict:
    """Predict the adversary's response to a filing stack."""
    conn = get_conn()

    # Adversary's historical patterns
    adv_data = []
    if adversary:
        try:
            rows = conn.execute(
                "SELECT * FROM adversary_assertions_fts "
                "WHERE adversary_assertions_fts MATCH ? ORDER BY rank LIMIT 20",
                (adversary,)
            ).fetchall()
            adv_data = [dict(r) for r in rows]
        except Exception:
            pass

    # Filing stack
    stack_info = []
    try:
        rows = conn.execute(
            "SELECT * FROM apex_filing_stack_index WHERE stack_label LIKE ? OR meek_track LIKE ?",
            (f'%{filing_stack}%', f'%{filing_stack}%')
        ).fetchall()
        stack_info = [dict(r) for r in rows]
    except Exception:
        pass

    conn.close()

    # LLM prediction
    try:
        prediction = llm_ask(
            f"Predict adversary response to filing stack: '{filing_stack}'\n"
            f"Adversary: '{adversary}'\n\n"
            f"Their historical assertions ({len(adv_data)}):\n"
            f"{json.dumps(adv_data[:5], default=str)[:600]}\n\n"
            f"Our filing stack: {json.dumps(stack_info[:3], default=str)[:400]}\n\n"
            f"Predict:\n"
            f"1. Will they file a motion to dismiss? What grounds?\n"
            f"2. Will they file a motion for summary judgment? When?\n"
            f"3. What affirmative defenses will they raise?\n"
            f"4. What discovery requests will they make?\n"
            f"5. Will they file counter-claims?\n"
            f"6. Timeline of expected responses\n"
            f"7. Our best pre-emptive actions",
            system_prompt=(
                "You are a litigation war-gaming strategist. "
                "Predict adversary behavior based on patterns. "
                "Think strategically about Michigan procedural rules."
            )
        )
    except Exception as e:
        prediction = f"LLM unavailable: {e}"

    result = {
        'filing_stack': filing_stack,
        'adversary': adversary,
        'historical_assertions': len(adv_data),
        'predicted_response': prediction,
    }
    log_activity(f'predict:{filing_stack}:{adversary}', json.dumps(result, default=str)[:2000])
    return result


def risk_matrix(all_stacks: str = '') -> dict:
    """Generate risk ranking across all filing stacks."""
    conn = get_conn()

    # Get all filing stacks
    stacks = []
    try:
        if all_stacks:
            for stack in all_stacks.split(','):
                rows = conn.execute(
                    "SELECT * FROM apex_filing_stack_index WHERE stack_label LIKE ? OR meek_track LIKE ?",
                    (f'%{stack.strip()}%', f'%{stack.strip()}%')
                ).fetchall()
                stacks.extend([dict(r) for r in rows])
        else:
            rows = conn.execute(
                "SELECT * FROM apex_filing_stack_index LIMIT 50"
            ).fetchall()
            stacks = [dict(r) for r in rows]
    except Exception:
        pass

    # Gather risk factors
    ev_count = 0
    try:
        ev_count = conn.execute('SELECT COUNT(*) FROM evidence_quotes').fetchone()[0]
    except Exception:
        pass

    violation_count = 0
    try:
        violation_count = conn.execute('SELECT COUNT(*) FROM constitutional_violations').fetchone()[0]
    except Exception:
        pass

    rebuttal_count = 0
    try:
        rebuttal_count = conn.execute('SELECT COUNT(*) FROM rebuttal_matrix').fetchone()[0]
    except Exception:
        pass

    conn.close()

    # LLM risk matrix
    try:
        matrix = llm_ask(
            f"RISK MATRIX across all filing stacks\n\n"
            f"Filing stacks ({len(stacks)}):\n"
            f"{json.dumps(stacks[:10], default=str)[:800]}\n\n"
            f"Evidence quotes: {ev_count}\n"
            f"Constitutional violations: {violation_count}\n"
            f"Rebuttals prepared: {rebuttal_count}\n\n"
            f"For each stack/claim, create a risk matrix:\n"
            f"| Stack | Claim | SOL Risk | Evidence Strength | "
            f"Immunity Risk | Procedural Risk | Overall Risk |\n"
            f"Rate each: Critical / High / Medium / Low\n"
            f"Then rank all stacks from highest to lowest risk.",
            system_prompt=(
                "You are a litigation risk analyst creating a comprehensive "
                "risk matrix. Consider SOL, evidence strength, immunity defenses, "
                "procedural defects, and judicial bias risk. Be quantitative."
            )
        )
    except Exception as e:
        matrix = f"LLM unavailable: {e}"

    result = {
        'stacks_analyzed': len(stacks),
        'evidence_total': ev_count,
        'violations_total': violation_count,
        'rebuttals_total': rebuttal_count,
        'risk_matrix': matrix,
    }
    log_activity('risk_matrix', json.dumps(result, default=str)[:2000])
    return result


# ── CLI ──────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description='Delta999 Red Team Agent')
    parser.add_argument('--action', required=True,
                        choices=['attack', 'sol_audit', 'immunity_audit',
                                 'predict_response', 'risk_matrix'],
                        help='Action to perform')
    parser.add_argument('--filing-stack', type=str, help='Filing stack identifier')
    parser.add_argument('--adversary', type=str, default='', help='Adversary name')
    parser.add_argument('--all-stacks', type=str, default='', help='Comma-separated stack list')
    args = parser.parse_args()

    if args.action == 'attack':
        if not args.filing_stack:
            parser.error('--filing-stack required')
        result = attack_filing(args.filing_stack)
    elif args.action == 'sol_audit':
        if not args.filing_stack:
            parser.error('--filing-stack required')
        result = sol_audit(args.filing_stack)
    elif args.action == 'immunity_audit':
        if not args.filing_stack:
            parser.error('--filing-stack required')
        result = immunity_audit(args.filing_stack)
    elif args.action == 'predict_response':
        if not args.filing_stack:
            parser.error('--filing-stack required')
        result = predict_response(args.filing_stack, args.adversary)
    elif args.action == 'risk_matrix':
        result = risk_matrix(args.all_stacks)
    else:
        parser.print_help()
        return

    print(json.dumps(result, indent=2, default=str))


if __name__ == '__main__':
    main()
