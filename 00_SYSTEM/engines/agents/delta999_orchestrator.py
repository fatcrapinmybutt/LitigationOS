#!/usr/bin/env python3
"""
Delta999 Orchestrator — Master dispatcher for the Delta999 agent fleet.

Routes tasks to appropriate specialist agents, runs full litigation pipelines,
and monitors system status across all agents.

CLI:
    python delta999_orchestrator.py --action dispatch --task "check evidence for claim X"
    python delta999_orchestrator.py --action pipeline --filing-stack "MEEK1"
    python delta999_orchestrator.py --action status
"""

import sys
try:
    sys.stdout.reconfigure(encoding='utf-8')
except (AttributeError, OSError):
    pass

import argparse
import json
import os
import sqlite3
import importlib
import logging
from datetime import datetime
from pathlib import Path

logger = logging.getLogger(__name__)

# ── paths────────────────────────────────────────────────────────────────────
AGENT_DIR = Path(__file__).parent
ENGINE_DIR = AGENT_DIR.parent
sys.path.insert(0, str(ENGINE_DIR))
sys.path.insert(0, str(AGENT_DIR))

DB = str(Path(__file__).resolve().parents[3] / "litigation_context.db")

from llm_bridge import llm_ask, llm_classify


# ── DB helpers ───────────────────────────────────────────────────────────────

_conn = None  # lazy singleton — avoids opening a new connection per log_activity call


def get_conn():
    """Return a shared module-level connection (lazy singleton with PRAGMA triad)."""
    global _conn
    if _conn is None:
        _conn = sqlite3.connect(DB, timeout=120)
        _conn.execute('PRAGMA busy_timeout=60000')
        _conn.execute('PRAGMA journal_mode=WAL')
        _conn.execute('PRAGMA cache_size=-32000')
        _conn.row_factory = sqlite3.Row
    return _conn


def close_conn():
    """Close the shared connection for clean shutdown."""
    global _conn
    if _conn is not None:
        try:
            _conn.close()
        except Exception as e:
            logger.debug("[close_conn] connection close error (non-fatal): %s", e)
        _conn = None


def log_activity(agent_name, action, result):
    conn = get_conn()
    conn.execute(
        'INSERT INTO agent_activity_log (agent_name, action, result) VALUES (?,?,?)',
        (agent_name, action, str(result)[:2000])
    )
    conn.commit()


AGENT_NAME = 'delta999_orchestrator'

# ── Agent module map ─────────────────────────────────────────────────────────
AGENT_MODULES = {
    'delta999_coa_agent': 'delta999_coa_agent',
    'delta999_evidence_chain_agent': 'delta999_evidence_chain_agent',
    'delta999_citation_agent': 'delta999_citation_agent',
    'delta999_compliance_agent': 'delta999_compliance_agent',
    'delta999_rebuttal_agent': 'delta999_rebuttal_agent',
    'delta999_redteam_agent': 'delta999_redteam_agent',
}


# ── Core functions ───────────────────────────────────────────────────────────

def dispatch(task_description: str) -> dict:
    """Route a task to the appropriate agent based on dispatch rules and LLM classification."""
    conn = get_conn()

    # 1. Check dispatch rules table for keyword matches
    rules = conn.execute(
        'SELECT task_pattern, agent_name, priority, description '
        'FROM agent_dispatch_rules ORDER BY priority DESC'
    ).fetchall()
    conn.close()

    task_lower = task_description.lower()
    matched = []
    for r in rules:
        if r['task_pattern'].lower() in task_lower:
            matched.append({
                'agent': r['agent_name'],
                'pattern': r['task_pattern'],
                'priority': r['priority'],
                'description': r['description'],
            })

    if matched:
        best = matched[0]
        result = {
            'task': task_description,
            'routed_to': best['agent'],
            'match_type': 'rule',
            'pattern': best['pattern'],
            'all_matches': matched,
        }
        log_activity(AGENT_NAME, f'dispatch:{best["agent"]}', json.dumps(result))
        return result

    # 2. Fallback: LLM classification
    agents = list(AGENT_MODULES.keys())
    try:
        chosen = llm_classify(task_description, agents)
    except Exception as e:
        logger.warning("[dispatch] LLM classification failed, falling back to evidence_chain_agent: %s", e, exc_info=True)
        chosen = 'delta999_evidence_chain_agent'

    result = {
        'task': task_description,
        'routed_to': chosen,
        'match_type': 'llm_classify',
    }
    log_activity(AGENT_NAME, f'dispatch:{chosen}', json.dumps(result))
    return result


def run_pipeline(filing_stack: str) -> dict:
    """Run full pipeline: evidence -> citation -> compliance -> score."""
    results = {}
    pipeline_steps = [
        ('evidence_search', 'delta999_evidence_chain_agent', 'gap_analysis', {'filing_stack': filing_stack}),
        ('citation_check', 'delta999_citation_agent', 'search_authority', {'topic': filing_stack}),
        ('compliance_check', 'delta999_compliance_agent', 'full_compliance_report', {'filing_stack': filing_stack}),
        ('redteam_score', 'delta999_redteam_agent', 'attack_filing', {'filing_stack': filing_stack}),
    ]

    for step_name, agent_mod, func_name, kwargs in pipeline_steps:
        print(f"  ▸ Pipeline step: {step_name} ({agent_mod}.{func_name})")
        try:
            mod = importlib.import_module(agent_mod)
            func = getattr(mod, func_name)
            step_result = func(**kwargs)
            results[step_name] = {'status': 'ok', 'result': step_result}
        except Exception as e:
            logger.error("[run_pipeline] Step '%s' failed: %s", step_name, e, exc_info=True)
            results[step_name] = {'status': 'error', 'error': str(e)}

    log_activity(AGENT_NAME, f'pipeline:{filing_stack}', json.dumps(results, default=str)[:2000])
    return results


def status() -> dict:
    """Return current system status: agent activity, DB health, dispatch rules."""
    conn = get_conn()

    # Recent activity
    recent = conn.execute(
        'SELECT agent_name, action, timestamp FROM agent_activity_log '
        'ORDER BY timestamp DESC LIMIT 20'
    ).fetchall()

    # Agent counts
    agent_counts = conn.execute(
        'SELECT agent_name, COUNT(*) as cnt FROM agent_activity_log GROUP BY agent_name'
    ).fetchall()

    # Dispatch rules
    rules_count = conn.execute('SELECT COUNT(*) FROM agent_dispatch_rules').fetchone()[0]

    # DB size
    db_tables = conn.execute(
        "SELECT COUNT(*) FROM sqlite_master WHERE type='table'"
    ).fetchone()[0]

    conn.close()

    result = {
        'timestamp': datetime.now().isoformat(),
        'db_tables': db_tables,
        'dispatch_rules': rules_count,
        'agent_activity_summary': {r['agent_name']: r['cnt'] for r in agent_counts},
        'recent_activity': [
            {'agent': r['agent_name'], 'action': r['action'], 'time': r['timestamp']}
            for r in recent
        ],
        'agents_available': list(AGENT_MODULES.keys()),
    }
    log_activity(AGENT_NAME, 'status', json.dumps(result, default=str)[:2000])
    return result


# ── CLI ──────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description='Delta999 Orchestrator')
    parser.add_argument('--action', required=True,
                        choices=['dispatch', 'pipeline', 'status'],
                        help='Action to perform')
    parser.add_argument('--task', type=str, help='Task description for dispatch')
    parser.add_argument('--filing-stack', type=str, help='Filing stack for pipeline')
    args = parser.parse_args()

    if args.action == 'dispatch':
        if not args.task:
            parser.error('--task required for dispatch')
        result = dispatch(args.task)
    elif args.action == 'pipeline':
        if not args.filing_stack:
            parser.error('--filing-stack required for pipeline')
        result = run_pipeline(args.filing_stack)
    elif args.action == 'status':
        result = status()
    else:
        parser.print_help()
        return

    print(json.dumps(result, indent=2, default=str))


if __name__ == '__main__':
    main()
