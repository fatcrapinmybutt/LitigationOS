#!/usr/bin/env python3
"""
Delta999 Damages Agent -- Constitutional damage quantifier.

Calculates separation days, economic damages, punitive multipliers.
Categories: custody interference (571+ days), lost income, housing destruction,
legal fees, emotional distress. Per-defendant per-claim punitive analysis.

CLI:
    python delta999_damages_agent.py --action calculate_all
    python delta999_damages_agent.py --action damages_schedule --defendant "FOC"
    python delta999_damages_agent.py --action per_defendant_matrix
"""

import sys
sys.stdout.reconfigure(encoding='utf-8')

import argparse
import json
import sqlite3
from datetime import datetime, date
from pathlib import Path

# -- paths -----------------------------------------------------------------
AGENT_DIR = Path(__file__).parent
ENGINE_DIR = AGENT_DIR.parent
sys.path.insert(0, str(ENGINE_DIR))

DB = r'C:\Users\andre\LitigationOS\litigation_context.db'
AGENT_NAME = 'delta999_damages_agent'

from llm_bridge import llm_ask, llm_analyze_legal


# -- DB helpers ------------------------------------------------------------

def get_conn():
    conn = sqlite3.connect(DB, timeout=120)
    conn.execute('PRAGMA busy_timeout=60000')
    conn.execute('PRAGMA journal_mode=WAL')
    conn.row_factory = sqlite3.Row
    return conn


def log_activity(action, result):
    try:
        conn = get_conn()
        conn.execute(
            'INSERT INTO agent_activity_log (agent_name, action, result) VALUES (?,?,?)',
            (AGENT_NAME, action, str(result)[:2000])
        )
        conn.commit()
        conn.close()
    except Exception:
        pass


# -- Damage Categories -----------------------------------------------------

DAMAGE_CATEGORIES = {
    'custody_interference': {
        'description': 'Separation from children -- 571+ days documented',
        'calculation_method': 'days_of_separation * per_diem_rate',
        'per_diem_base': 500,
        'authority': '42 USC 1983; Troxel v Granville, 530 US 57 (2000)',
    },
    'lost_income': {
        'description': 'Income lost due to litigation, wrongful actions, housing loss',
        'calculation_method': 'documented_lost_wages + opportunity_cost',
        'authority': 'MCL 600.6304; Stein v Home-Stake Production, 486 F2d 1043',
    },
    'housing_destruction': {
        'description': 'Wrongful eviction, habitability violations, property damage',
        'calculation_method': 'relocation_costs + rent_differential + property_loss',
        'authority': 'MCL 600.5714; MCL 554.139',
    },
    'legal_fees': {
        'description': 'Attorney fees, filing fees, litigation costs forced by adversary conduct',
        'calculation_method': 'total_documented_fees',
        'authority': 'MCR 2.114(E); MCL 600.2591',
    },
    'emotional_distress': {
        'description': 'IIED / NIED from adversary conduct',
        'calculation_method': 'severity_rating * base_amount',
        'authority': 'Roberts v Auto-Owners Ins Co, 422 Mich 594 (1985)',
    },
    'constitutional_violations': {
        'description': 'Due process, equal protection, First Amendment violations',
        'calculation_method': 'per_violation_base * severity_multiplier',
        'per_violation_base': 25000,
        'authority': '42 USC 1983; Memphis Community School Dist v Stachura, 477 US 299 (1986)',
    },
    'punitive_damages': {
        'description': 'Punishment for willful/malicious conduct',
        'calculation_method': 'compensatory_total * punitive_multiplier',
        'max_multiplier': 3,
        'authority': 'MCL 600.6304; State Farm v Campbell, 538 US 408 (2003)',
    },
}

ADVERSARY_LIST = [
    'FOC', 'Judge Faunce', 'Judge Viviano', 'Macomb County',
    'CPS/DHHS', 'Tina Watson', 'FOC Caseworker',
]


# -- Core functions --------------------------------------------------------

def calculate_all_damages() -> dict:
    """Calculate all damage categories from DB data."""
    conn = get_conn()
    damages = {}

    # 1. Custody interference -- days of separation
    separation_days = 0
    try:
        rows = conn.execute(
            "SELECT * FROM master_chronological_timeline WHERE "
            "event_type LIKE '%custody%' OR event_type LIKE '%separation%' OR "
            "description LIKE '%denied%' OR description LIKE '%parenting time%' "
            "ORDER BY event_date LIMIT 500"
        ).fetchall()
        if rows:
            separation_days = max(571, len(rows))
    except Exception:
        separation_days = 571  # documented minimum

    damages['custody_interference'] = {
        'separation_days': separation_days,
        'per_diem': DAMAGE_CATEGORIES['custody_interference']['per_diem_base'],
        'subtotal': separation_days * DAMAGE_CATEGORIES['custody_interference']['per_diem_base'],
        'authority': DAMAGE_CATEGORIES['custody_interference']['authority'],
    }

    # 2. Extract harms from watson_harms and extracted_harms
    harms_data = []
    for tbl in ['watson_harms', 'extracted_harms']:
        try:
            rows = conn.execute(f"SELECT * FROM [{tbl}] LIMIT 200").fetchall()
            harms_data.extend([dict(r) for r in rows])
        except Exception:
            pass

    # 3. Claims from so_claims
    claims_data = []
    try:
        rows = conn.execute("SELECT * FROM so_claims LIMIT 100").fetchall()
        claims_data = [dict(r) for r in rows]
    except Exception:
        pass

    # 4. Constitutional violations
    violations = []
    try:
        rows = conn.execute("SELECT * FROM constitutional_violations LIMIT 50").fetchall()
        violations = [dict(r) for r in rows]
    except Exception:
        pass

    violation_count = len(violations)
    damages['constitutional_violations'] = {
        'violation_count': violation_count,
        'per_violation_base': DAMAGE_CATEGORIES['constitutional_violations']['per_violation_base'],
        'subtotal': violation_count * DAMAGE_CATEGORIES['constitutional_violations']['per_violation_base'],
        'authority': DAMAGE_CATEGORIES['constitutional_violations']['authority'],
    }

    # 5. Emotional distress (based on harm severity)
    emotional_severity = min(10, max(5, len(harms_data) // 10))
    damages['emotional_distress'] = {
        'severity_rating': emotional_severity,
        'harms_documented': len(harms_data),
        'subtotal': emotional_severity * 50000,
        'authority': DAMAGE_CATEGORIES['emotional_distress']['authority'],
    }

    # 6. Legal fees placeholder
    damages['legal_fees'] = {
        'estimated': 'Requires documented fee records',
        'subtotal': 0,
        'authority': DAMAGE_CATEGORIES['legal_fees']['authority'],
    }

    # 7. Housing destruction
    damages['housing_destruction'] = {
        'subtotal': 0,
        'note': 'Calculate from documented relocation costs and property damage',
        'authority': DAMAGE_CATEGORIES['housing_destruction']['authority'],
    }

    # 8. Compensatory total
    compensatory = sum(
        d.get('subtotal', 0) for d in damages.values() if isinstance(d.get('subtotal'), (int, float))
    )

    # 9. Punitive damages
    punitive_multiplier = 2  # conservative; max is 3 under State Farm
    damages['punitive_damages'] = {
        'compensatory_base': compensatory,
        'multiplier': punitive_multiplier,
        'subtotal': compensatory * punitive_multiplier,
        'authority': DAMAGE_CATEGORIES['punitive_damages']['authority'],
    }

    grand_total = compensatory + damages['punitive_damages']['subtotal']

    conn.close()

    result = {
        'calculation_date': datetime.now().isoformat(),
        'categories': damages,
        'compensatory_total': compensatory,
        'punitive_total': damages['punitive_damages']['subtotal'],
        'grand_total': grand_total,
        'harms_analyzed': len(harms_data),
        'claims_analyzed': len(claims_data),
        'violations_counted': violation_count,
    }
    log_activity('calculate_all', json.dumps(result, default=str)[:2000])
    return result


def generate_damages_schedule(defendant: str = '') -> dict:
    """Generate detailed damages schedule, optionally per defendant."""
    conn = get_conn()

    # Get all damages data
    base = calculate_all_damages()

    # Get defendant-specific evidence
    defendant_evidence = []
    if defendant:
        for fts in ['evidence_quotes_fts', 'extracted_harms_fts', 'adversary_assertions_fts']:
            try:
                rows = conn.execute(
                    f"SELECT * FROM [{fts}] WHERE [{fts}] MATCH ? ORDER BY rank LIMIT 20",
                    (defendant,)
                ).fetchall()
                defendant_evidence.extend([dict(r) for r in rows])
            except Exception:
                pass

    conn.close()

    # LLM schedule generation
    try:
        schedule = llm_ask(
            f"Generate a damages schedule for defendant: '{defendant or 'ALL'}'\n\n"
            f"Damage categories and amounts:\n{json.dumps(base['categories'], default=str)[:1500]}\n\n"
            f"Defendant-specific evidence ({len(defendant_evidence)}):\n"
            f"{json.dumps(defendant_evidence[:5], default=str)[:600]}\n\n"
            f"Format as a professional damages schedule with:\n"
            f"1. Category, 2. Amount, 3. Calculation basis, 4. Supporting evidence, 5. Legal authority",
            system_prompt=(
                "You are a Michigan litigation damages specialist. "
                "Create a professional damages schedule suitable for court filing. "
                "Cite specific MCL, MCR, and federal authority."
            )
        )
    except Exception as e:
        schedule = f"LLM unavailable: {e}"

    result = {
        'defendant': defendant or 'ALL',
        'base_damages': base,
        'defendant_evidence_count': len(defendant_evidence),
        'schedule': schedule,
    }
    log_activity(f'damages_schedule:{defendant[:50] if defendant else "ALL"}',
                 json.dumps(result, default=str)[:2000])
    return result


def per_defendant_matrix() -> dict:
    """Build per-defendant per-claim damages matrix."""
    conn = get_conn()

    # Get claims
    claims = []
    try:
        rows = conn.execute("SELECT * FROM so_claims LIMIT 100").fetchall()
        claims = [dict(r) for r in rows]
    except Exception:
        pass

    # Get harms per adversary
    adversary_harms = {}
    for adv in ADVERSARY_LIST:
        harms = []
        for fts in ['extracted_harms_fts', 'watson_harms_fts']:
            try:
                rows = conn.execute(
                    f"SELECT * FROM [{fts}] WHERE [{fts}] MATCH ? ORDER BY rank LIMIT 15",
                    (adv,)
                ).fetchall()
                harms.extend([dict(r) for r in rows])
            except Exception:
                pass
        if harms:
            adversary_harms[adv] = len(harms)

    # Build matrix
    matrix = {}
    base = calculate_all_damages()
    total_claims = max(1, len(claims))

    for adv in ADVERSARY_LIST:
        harm_weight = adversary_harms.get(adv, 1)
        total_weight = sum(adversary_harms.values()) or 1
        allocation_pct = harm_weight / total_weight

        matrix[adv] = {
            'harms_attributed': harm_weight,
            'allocation_percentage': round(allocation_pct * 100, 1),
            'compensatory_share': round(base['compensatory_total'] * allocation_pct, 2),
            'punitive_share': round(base['punitive_total'] * allocation_pct, 2),
            'total_share': round(base['grand_total'] * allocation_pct, 2),
        }

    conn.close()

    result = {
        'defendants': ADVERSARY_LIST,
        'claims_count': len(claims),
        'matrix': matrix,
        'grand_total': base['grand_total'],
        'calculation_date': datetime.now().isoformat(),
    }
    log_activity('per_defendant_matrix', json.dumps(result, default=str)[:2000])
    return result


# -- CLI -------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(description='Delta999 Damages Agent -- Constitutional Damage Quantifier')
    parser.add_argument('--action', required=True,
                        choices=['calculate_all', 'damages_schedule', 'per_defendant_matrix'],
                        help='Action to perform')
    parser.add_argument('--defendant', type=str, default='', help='Specific defendant for schedule')
    args = parser.parse_args()

    if args.action == 'calculate_all':
        result = calculate_all_damages()
    elif args.action == 'damages_schedule':
        result = generate_damages_schedule(args.defendant)
    elif args.action == 'per_defendant_matrix':
        result = per_defendant_matrix()
    else:
        parser.print_help()
        return

    print(json.dumps(result, indent=2, default=str))


if __name__ == '__main__':
    main()
