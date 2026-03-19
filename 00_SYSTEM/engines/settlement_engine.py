#!/usr/bin/env python3
"""Settlement Engine - Case valuation calculator for Michigan litigation.

Calculates damages across multiple categories including custody separation,
economic damages, non-economic damages, punitive/treble damages, RICO,
housing violations, and attorney fee equivalents. Allocates per-defendant.

Usage:
    python settlement_engine.py --defendant all --aggressive --output md
    python settlement_engine.py --defendant watson --conservative --output json
    python settlement_engine.py --defendant shadyoaks --output md --save valuation.md
"""
import sys
sys.stdout.reconfigure(encoding='utf-8')

import argparse
import json
import math
import os
import re
import sqlite3
from collections import OrderedDict
from datetime import datetime, date
from pathlib import Path

DB = r'C:\Users\andre\LitigationOS\litigation_context.db'

# Per diem rates for custody separation damages
CUSTODY_PER_DIEM = {
    'conservative': 150.0,
    'moderate': 275.0,
    'aggressive': 500.0,
}

# Separation baseline: 571+ days documented
SEPARATION_DAYS_DEFAULT = 571

# Michigan-specific multipliers and caps
MI_NONECONOMIC_CAP = 497500  # MCL 600.1483 adjusted (non-medical malpractice has no cap for intentional torts)
MI_PUNITIVE_NOTE = "Michigan generally does not allow punitive damages except by statute"
RICO_MULTIPLIER = 3  # MCL 750.159j
HOUSING_TREBLE_MULTIPLIER = 3  # MCL 600.2919
HUD_PENALTY_FIRST = 21663  # Fair Housing Act max per violation (adjusted)
HUD_PENALTY_PATTERN = 54133  # Pattern/practice

# Attorney fee equivalent rate
PRO_SE_HOURLY_RATE = {
    'conservative': 200.0,
    'moderate': 350.0,
    'aggressive': 500.0,
}

DEFENDANTS = {
    'watson': {
        'full_name': 'Emily Watson',
        'categories': ['custody_separation', 'defamation', 'iied', 'parental_alienation',
                       'fraud_on_court', 'economic_direct'],
    },
    'barnes': {
        'full_name': 'Attorney Barnes',
        'categories': ['malpractice', 'fraud', 'conspiracy', 'economic_direct',
                       'attorney_fees_wasted'],
    },
    'mcneill': {
        'full_name': 'Judge McNeill',
        'categories': ['section_1983', 'due_process', 'economic_direct'],
    },
    'shadyoaks': {
        'full_name': 'Shady Oaks / HOA / Alden Management',
        'categories': ['housing_violations', 'rico', 'conversion', 'fair_housing',
                       'economic_direct', 'habitability'],
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
    """Execute query safely, return empty list on error."""
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
    """Check if table exists."""
    result = conn.execute(
        "SELECT name FROM sqlite_master WHERE type='table' AND name=?",
        (table_name,)
    ).fetchone()
    return result is not None


def load_db_damages(conn):
    """Load existing damage calculations from DB."""
    damages = {}

    if table_exists(conn, 'damages_calculations'):
        rows = safe_query(conn,
            "SELECT category, subcategory, amount_low, amount_high, "
            "evidence_source, methodology, authority, confidence_level "
            "FROM damages_calculations ORDER BY category"
        )
        for r in rows:
            cat = r.get('category', 'unknown')
            if cat not in damages:
                damages[cat] = []
            damages[cat].append(r)

    if table_exists(conn, 'financial_damages_comprehensive'):
        rows = safe_query(conn,
            "SELECT category, subcategory, description, amount_low, amount_high, "
            "evidence_source, legal_basis "
            "FROM financial_damages_comprehensive ORDER BY category"
        )
        for r in rows:
            cat = r.get('category', 'unknown')
            if cat not in damages:
                damages[cat] = []
            damages[cat].append(r)

    return damages


def load_separation_days(conn):
    """Load separation days from separation_log if available."""
    if not table_exists(conn, 'separation_log'):
        return SEPARATION_DAYS_DEFAULT

    rows = safe_query(conn, "SELECT COUNT(*) as cnt FROM separation_log")
    if rows and rows[0].get('cnt', 0) > 0:
        count = rows[0]['cnt']
        return max(count, SEPARATION_DAYS_DEFAULT)
    return SEPARATION_DAYS_DEFAULT


def load_pro_se_hours(conn):
    """Estimate pro se litigation hours from various tables."""
    total_hours = 0

    # Estimate from filing count
    if table_exists(conn, 'filing_documents'):
        rows = safe_query(conn, "SELECT COUNT(*) as cnt FROM filing_documents")
        filing_count = rows[0]['cnt'] if rows else 0
        total_hours += filing_count * 8  # ~8 hours per filing

    # Estimate from research sessions
    if table_exists(conn, 'copilot_sessions'):
        rows = safe_query(conn, "SELECT COUNT(*) as cnt FROM copilot_sessions")
        sessions = rows[0]['cnt'] if rows else 0
        total_hours += sessions * 1.5  # ~1.5 hours per session

    # Minimum baseline
    total_hours = max(total_hours, 500)
    return total_hours


def calc_custody_separation(mode, separation_days):
    """Calculate custody separation damages."""
    per_diem = CUSTODY_PER_DIEM[mode]
    base = separation_days * per_diem

    return {
        'label': 'Custody Separation Damages',
        'authority': 'Intentional tort / Custodial interference',
        'methodology': f'{separation_days} days x ${per_diem:.0f}/day per diem',
        'amount_low': round(base * 0.7),
        'amount_high': round(base * 1.3),
        'amount_mid': round(base),
        'details': {
            'days_separated': separation_days,
            'per_diem_rate': per_diem,
        }
    }


def calc_defamation(mode):
    """Calculate defamation damages."""
    ranges = {
        'conservative': (25000, 75000),
        'moderate': (75000, 250000),
        'aggressive': (250000, 750000),
    }
    low, high = ranges[mode]
    return {
        'label': 'Defamation Damages',
        'authority': 'MCL 600.2911',
        'methodology': 'Defamation per se (false statements regarding parental fitness)',
        'amount_low': low,
        'amount_high': high,
        'amount_mid': (low + high) // 2,
    }


def calc_iied(mode):
    """Calculate Intentional Infliction of Emotional Distress damages."""
    ranges = {
        'conservative': (50000, 150000),
        'moderate': (150000, 500000),
        'aggressive': (500000, 1500000),
    }
    low, high = ranges[mode]
    return {
        'label': 'IIED Damages',
        'authority': 'Roberts v Auto-Owners Ins Co, 422 Mich 594 (1985)',
        'methodology': 'Extreme and outrageous conduct causing severe emotional distress',
        'amount_low': low,
        'amount_high': high,
        'amount_mid': (low + high) // 2,
    }


def calc_parental_alienation(mode, separation_days):
    """Calculate parental alienation tort damages."""
    base = {
        'conservative': 100000,
        'moderate': 350000,
        'aggressive': 750000,
    }[mode]
    # Scale by separation duration
    duration_factor = min(2.0, separation_days / 365)
    low = round(base * 0.7 * duration_factor)
    high = round(base * 1.3 * duration_factor)
    return {
        'label': 'Parental Alienation Tort',
        'authority': 'Emerging tort theory; Brokaw v Mercer County, 235 F.3d 1000 (7th Cir 2000)',
        'methodology': f'Duration-scaled alienation damages ({separation_days} days)',
        'amount_low': low,
        'amount_high': high,
        'amount_mid': (low + high) // 2,
    }


def calc_fraud_on_court(mode):
    """Calculate fraud on court damages."""
    ranges = {
        'conservative': (25000, 100000),
        'moderate': (100000, 300000),
        'aggressive': (300000, 750000),
    }
    low, high = ranges[mode]
    return {
        'label': 'Fraud on the Court',
        'authority': 'MCR 2.612; Inherent court power',
        'methodology': 'Damages from fraudulent representations affecting court proceedings',
        'amount_low': low,
        'amount_high': high,
        'amount_mid': (low + high) // 2,
    }


def calc_malpractice(mode):
    """Calculate attorney malpractice damages."""
    ranges = {
        'conservative': (50000, 200000),
        'moderate': (200000, 500000),
        'aggressive': (500000, 1500000),
    }
    low, high = ranges[mode]
    return {
        'label': 'Attorney Malpractice',
        'authority': 'Simko v Blake, 448 Mich 648 (1995)',
        'methodology': 'Case-within-a-case: damages from negligent/fraudulent representation',
        'amount_low': low,
        'amount_high': high,
        'amount_mid': (low + high) // 2,
    }


def calc_conspiracy(mode):
    """Calculate civil conspiracy damages."""
    ranges = {
        'conservative': (25000, 75000),
        'moderate': (75000, 250000),
        'aggressive': (250000, 500000),
    }
    low, high = ranges[mode]
    return {
        'label': 'Civil Conspiracy',
        'authority': 'Advocacy Org for Patients & Providers v Auto Club Ins Assn, 276 Mich App 32 (2007)',
        'methodology': 'Concerted action resulting in tortious harm',
        'amount_low': low,
        'amount_high': high,
        'amount_mid': (low + high) // 2,
    }


def calc_section_1983(mode):
    """Calculate 42 USC 1983 damages (if immunity pierced)."""
    ranges = {
        'conservative': (0, 50000),
        'moderate': (50000, 500000),
        'aggressive': (500000, 2000000),
    }
    low, high = ranges[mode]
    return {
        'label': 'Section 1983 Civil Rights Damages',
        'authority': '42 USC 1983; Monell v Dept of Social Services, 436 US 658 (1978)',
        'methodology': 'Constitutional deprivation damages (contingent on immunity analysis)',
        'amount_low': low,
        'amount_high': high,
        'amount_mid': (low + high) // 2,
        'caveat': 'Requires piercing judicial immunity - highest risk/reward category',
    }


def calc_due_process(mode):
    """Calculate due process violation damages."""
    ranges = {
        'conservative': (25000, 100000),
        'moderate': (100000, 350000),
        'aggressive': (350000, 1000000),
    }
    low, high = ranges[mode]
    return {
        'label': 'Due Process Violation Damages',
        'authority': '14th Amendment; Mathews v Eldridge, 424 US 319 (1976)',
        'methodology': 'Deprivation of liberty interest in parental rights without due process',
        'amount_low': low,
        'amount_high': high,
        'amount_mid': (low + high) // 2,
    }


def calc_housing_violations(mode):
    """Calculate housing violation damages (with treble)."""
    base_ranges = {
        'conservative': (10000, 30000),
        'moderate': (30000, 75000),
        'aggressive': (75000, 200000),
    }
    low, high = base_ranges[mode]
    return {
        'label': 'Housing Violations (Treble)',
        'authority': 'MCL 600.2919; MCL 554.139',
        'methodology': f'Statutory violations x{HOUSING_TREBLE_MULTIPLIER} treble damages',
        'amount_low': low * HOUSING_TREBLE_MULTIPLIER,
        'amount_high': high * HOUSING_TREBLE_MULTIPLIER,
        'amount_mid': ((low + high) // 2) * HOUSING_TREBLE_MULTIPLIER,
        'details': {
            'base_low': low,
            'base_high': high,
            'multiplier': HOUSING_TREBLE_MULTIPLIER,
        }
    }


def calc_rico(mode, base_actual_damages):
    """Calculate RICO treble damages."""
    trebled_low = base_actual_damages * RICO_MULTIPLIER
    trebled_high = base_actual_damages * RICO_MULTIPLIER * 1.5
    return {
        'label': 'RICO Treble Damages',
        'authority': 'MCL 750.159j (Michigan RICO); 18 USC 1964(c) (Federal)',
        'methodology': f'Actual damages ${base_actual_damages:,.0f} x{RICO_MULTIPLIER} treble',
        'amount_low': round(trebled_low * 0.8),
        'amount_high': round(trebled_high),
        'amount_mid': round(trebled_low),
        'details': {
            'base_actual': base_actual_damages,
            'multiplier': RICO_MULTIPLIER,
        }
    }


def calc_fair_housing(mode):
    """Calculate Fair Housing Act damages."""
    ranges = {
        'conservative': (HUD_PENALTY_FIRST, HUD_PENALTY_FIRST * 3),
        'moderate': (HUD_PENALTY_FIRST * 3, HUD_PENALTY_PATTERN),
        'aggressive': (HUD_PENALTY_PATTERN, HUD_PENALTY_PATTERN * 3),
    }
    low, high = ranges[mode]
    return {
        'label': 'Fair Housing Act Penalties',
        'authority': '42 USC 3613; Fair Housing Act',
        'methodology': 'Federal housing discrimination penalties plus compensatory damages',
        'amount_low': round(low),
        'amount_high': round(high),
        'amount_mid': round((low + high) / 2),
    }


def calc_conversion(mode):
    """Calculate conversion damages."""
    ranges = {
        'conservative': (5000, 25000),
        'moderate': (25000, 75000),
        'aggressive': (75000, 200000),
    }
    low, high = ranges[mode]
    return {
        'label': 'Conversion of Property',
        'authority': 'Foremost Ins Co v Allstate Ins Co, 439 Mich 378 (1992)',
        'methodology': 'Value of converted personal property plus consequential damages',
        'amount_low': low,
        'amount_high': high,
        'amount_mid': (low + high) // 2,
    }


def calc_economic_direct(conn, mode):
    """Calculate direct economic damages from DB records."""
    db_damages = load_db_damages(conn)
    total_low = 0
    total_high = 0
    items = []

    for cat, entries in db_damages.items():
        for entry in entries:
            low = entry.get('amount_low', 0) or 0
            high = entry.get('amount_high', 0) or 0
            total_low += low
            total_high += high
            items.append({
                'category': cat,
                'subcategory': entry.get('subcategory', ''),
                'amount_low': low,
                'amount_high': high,
            })

    if total_low == 0 and total_high == 0:
        # Fallback estimates
        fallback = {'conservative': (25000, 75000), 'moderate': (75000, 200000), 'aggressive': (200000, 500000)}
        total_low, total_high = fallback[mode]
        items.append({'category': 'estimated', 'subcategory': 'fallback', 'amount_low': total_low, 'amount_high': total_high})

    return {
        'label': 'Direct Economic Damages',
        'authority': 'Various - documented financial losses',
        'methodology': 'Aggregated from litigation database records',
        'amount_low': round(total_low),
        'amount_high': round(total_high),
        'amount_mid': round((total_low + total_high) / 2),
        'details': {'line_items': items[:20]},
    }


def calc_attorney_fee_equivalent(mode, hours):
    """Calculate pro se attorney fee equivalent."""
    rate = PRO_SE_HOURLY_RATE[mode]
    total = hours * rate
    return {
        'label': 'Attorney Fee Equivalent (Pro Se)',
        'authority': 'Kay v Ehrler, 499 US 432 (1991); MCL 600.2405',
        'methodology': f'{hours:.0f} hours x ${rate:.0f}/hr reasonable rate',
        'amount_low': round(total * 0.5),
        'amount_high': round(total * 1.2),
        'amount_mid': round(total),
        'details': {
            'hours': hours,
            'hourly_rate': rate,
        }
    }


def calc_defendant_damages(conn, defendant_key, mode):
    """Calculate all applicable damages for a specific defendant."""
    info = DEFENDANTS[defendant_key]
    categories = info['categories']
    separation_days = load_separation_days(conn)
    pro_se_hours = load_pro_se_hours(conn)

    items = []

    calc_map = {
        'custody_separation': lambda: calc_custody_separation(mode, separation_days),
        'defamation': lambda: calc_defamation(mode),
        'iied': lambda: calc_iied(mode),
        'parental_alienation': lambda: calc_parental_alienation(mode, separation_days),
        'fraud_on_court': lambda: calc_fraud_on_court(mode),
        'malpractice': lambda: calc_malpractice(mode),
        'fraud': lambda: calc_fraud_on_court(mode),
        'conspiracy': lambda: calc_conspiracy(mode),
        'section_1983': lambda: calc_section_1983(mode),
        'due_process': lambda: calc_due_process(mode),
        'housing_violations': lambda: calc_housing_violations(mode),
        'fair_housing': lambda: calc_fair_housing(mode),
        'conversion': lambda: calc_conversion(mode),
        'economic_direct': lambda: calc_economic_direct(conn, mode),
        'attorney_fees_wasted': lambda: calc_attorney_fee_equivalent(mode, pro_se_hours * 0.3),
        'habitability': lambda: {
            'label': 'Habitability Damages',
            'authority': 'MCL 554.139; Trentadue v Gorton, 479 Mich 378 (2007)',
            'methodology': 'Rent abatement and repair costs for uninhabitable conditions',
            'amount_low': {'conservative': 5000, 'moderate': 15000, 'aggressive': 40000}[mode],
            'amount_high': {'conservative': 15000, 'moderate': 40000, 'aggressive': 100000}[mode],
            'amount_mid': {'conservative': 10000, 'moderate': 27500, 'aggressive': 70000}[mode],
        },
    }

    for cat in categories:
        if cat in calc_map:
            item = calc_map[cat]()
            item['category_key'] = cat
            items.append(item)

    # RICO calculation for shadyoaks (treble on base actual damages)
    if 'rico' in categories:
        base_actual = sum(i.get('amount_mid', 0) for i in items if i.get('category_key') != 'rico')
        rico = calc_rico(mode, base_actual)
        rico['category_key'] = 'rico'
        items.append(rico)

    # Attorney fee equivalent (applicable to all defendants)
    atty_fees = calc_attorney_fee_equivalent(mode, pro_se_hours)
    atty_fees['category_key'] = 'attorney_fee_equivalent'
    items.append(atty_fees)

    # Totals
    total_low = sum(i.get('amount_low', 0) for i in items)
    total_high = sum(i.get('amount_high', 0) for i in items)
    total_mid = sum(i.get('amount_mid', 0) for i in items)

    return {
        'defendant': defendant_key,
        'full_name': info['full_name'],
        'mode': mode,
        'calculated_at': datetime.now().isoformat(),
        'line_items': items,
        'totals': {
            'low': total_low,
            'mid': total_mid,
            'high': total_high,
        }
    }


def format_damages_md(all_damages, mode):
    """Format damages matrix as markdown."""
    lines = []
    lines.append(f"# SETTLEMENT VALUATION REPORT")
    lines.append(f"")
    lines.append(f"**Mode:** {mode.upper()}")
    lines.append(f"**Generated:** {datetime.now().isoformat()}")
    lines.append(f"")

    grand_low = 0
    grand_mid = 0
    grand_high = 0

    for defendant_key, data in all_damages.items():
        totals = data['totals']
        grand_low += totals['low']
        grand_mid += totals['mid']
        grand_high += totals['high']

        lines.append(f"## {data['full_name']}")
        lines.append(f"")
        lines.append(f"| Category | Low | Mid | High | Authority |")
        lines.append(f"|----------|-----|-----|------|-----------|")

        for item in data['line_items']:
            label = item.get('label', item.get('category_key', ''))
            low = f"${item.get('amount_low', 0):,.0f}"
            mid = f"${item.get('amount_mid', 0):,.0f}"
            high = f"${item.get('amount_high', 0):,.0f}"
            auth = item.get('authority', '')[:50]
            lines.append(f"| {label} | {low} | {mid} | {high} | {auth} |")

        lines.append(f"| **SUBTOTAL** | **${totals['low']:,.0f}** | **${totals['mid']:,.0f}** | **${totals['high']:,.0f}** | |")
        lines.append(f"")

    lines.append(f"---")
    lines.append(f"")
    lines.append(f"## GRAND TOTAL (All Defendants)")
    lines.append(f"")
    lines.append(f"| Estimate | Amount |")
    lines.append(f"|----------|--------|")
    lines.append(f"| Conservative (Low) | **${grand_low:,.0f}** |")
    lines.append(f"| Moderate (Mid) | **${grand_mid:,.0f}** |")
    lines.append(f"| Aggressive (High) | **${grand_high:,.0f}** |")
    lines.append(f"")

    lines.append(f"## Executive Summary")
    lines.append(f"")
    lines.append(f"This valuation covers {len(all_damages)} defendant(s) across multiple ")
    lines.append(f"categories of damages under Michigan and federal law. The {mode} ")
    lines.append(f"estimate range is **${grand_low:,.0f}** to **${grand_high:,.0f}** ")
    lines.append(f"with a midpoint of **${grand_mid:,.0f}**.")
    lines.append(f"")
    lines.append(f"**Key Authorities:**")
    lines.append(f"- Michigan RICO: MCL 750.159j (3x actual damages)")
    lines.append(f"- Housing Treble: MCL 600.2919 (3x statutory violations)")
    lines.append(f"- Fair Housing: 42 USC 3613")
    lines.append(f"- Section 1983: 42 USC 1983 (federal civil rights)")
    lines.append(f"- Non-economic: MCL 600.2946 (pain and suffering)")
    lines.append(f"- Pro Se Fees: Kay v Ehrler, 499 US 432 (1991)")
    lines.append(f"")
    lines.append(f"**Disclaimers:**")
    lines.append(f"- Section 1983 claims against Judge McNeill contingent on piercing judicial immunity")
    lines.append(f"- Michigan restricts punitive damages; treble damages available only by statute")
    lines.append(f"- RICO damages require proof of enterprise and pattern of racketeering")
    lines.append(f"- All amounts are estimates for settlement negotiation purposes")

    return '\n'.join(lines)


def main():
    parser = argparse.ArgumentParser(
        description='Settlement Engine - Michigan litigation case valuation calculator'
    )
    parser.add_argument('--defendant', type=str, required=True,
                        choices=list(DEFENDANTS.keys()) + ['all'],
                        help='Defendant to calculate damages for')
    mode_group = parser.add_mutually_exclusive_group()
    mode_group.add_argument('--conservative', action='store_const', const='conservative',
                            dest='mode', help='Conservative damage estimates')
    mode_group.add_argument('--moderate', action='store_const', const='moderate',
                            dest='mode', help='Moderate damage estimates (default)')
    mode_group.add_argument('--aggressive', action='store_const', const='aggressive',
                            dest='mode', help='Aggressive damage estimates')
    parser.set_defaults(mode='moderate')
    parser.add_argument('--output', type=str, choices=['json', 'md'], default='json',
                        help='Output format (default: json)')
    parser.add_argument('--save', type=str, help='Save report to file')

    args = parser.parse_args()

    print(f"[START] Settlement Engine - {datetime.now().isoformat()}")
    print(f"[MODE] {args.mode.upper()}")

    try:
        conn = get_db_connection()

        if args.defendant == 'all':
            targets = list(DEFENDANTS.keys())
        else:
            targets = [args.defendant]

        all_damages = OrderedDict()
        for target in targets:
            print(f"[CALC] {DEFENDANTS[target]['full_name']}...")
            damages = calc_defendant_damages(conn, target, args.mode)
            all_damages[target] = damages
            print(f"  -> Range: ${damages['totals']['low']:,.0f} - ${damages['totals']['high']:,.0f}")

        conn.close()

        # Format output
        if args.output == 'md':
            output_text = format_damages_md(all_damages, args.mode)
        else:
            output_text = json.dumps(all_damages, indent=2, ensure_ascii=True, default=str)

        if args.save:
            with open(args.save, 'w', encoding='utf-8') as f:
                f.write(output_text)
            print(f"[SAVED] Report written to {args.save}")
        else:
            print(f"\n{output_text}")

        # Grand total summary
        grand_low = sum(d['totals']['low'] for d in all_damages.values())
        grand_mid = sum(d['totals']['mid'] for d in all_damages.values())
        grand_high = sum(d['totals']['high'] for d in all_damages.values())
        print(f"\n[GRAND TOTAL] ({args.mode.upper()})")
        print(f"  Low:  ${grand_low:>14,.0f}")
        print(f"  Mid:  ${grand_mid:>14,.0f}")
        print(f"  High: ${grand_high:>14,.0f}")

    except Exception as e:
        print(f"[FATAL] {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

    print(f"[DONE] {datetime.now().isoformat()}")


if __name__ == '__main__':
    main()
