#!/usr/bin/env python3
"""
Settlement Value Calculator — Comprehensive case valuation model.

Novel LitigationOS Tool #24

Calculates settlement ranges across all 6 case lanes:
1. Lane A (Custody) — Parental rights deprivation damages
2. Lane B (Housing) — Habitability/discrimination damages
3. Lane C (Convergence) — Cross-lane multiplier
4. Lane D (PPO) — False PPO / malicious prosecution
5. Lane E (Misconduct) — §1983 judicial misconduct
6. Lane F (Appellate) — Costs of appeal + underlying damages

Damage Categories:
- Compensatory (actual losses)
- Special damages (quantifiable costs)
- General damages (pain & suffering)
- Punitive damages (§1983 + fraud)
- Attorney fees equivalent (pro se hourly rate)
- Statutory damages (specific Michigan statutes)
"""
import sys, os, json, sqlite3, re
from collections import defaultdict
from pathlib import Path
from datetime import datetime, timedelta

sys.stdout = open(sys.stdout.fileno(), mode='w', encoding='utf-8', errors='replace')

DB_PATH = Path(r"C:\Users\andre\LitigationOS\litigation_context.db")
REPORT_DIR = Path(r"C:\Users\andre\LitigationOS\00_SYSTEM\reports")

# Case timeline
SEPARATION_DATE = datetime(2023, 10, 1)  # approximate
CASE_START_DATE = datetime(2024, 1, 1)
TODAY = datetime.now()
DAYS_SEPARATED = (TODAY - SEPARATION_DATE).days

# Pro se hourly rate (Michigan standard for fee-shifting)
PRO_SE_HOURLY = 150  # Conservative estimate for Western MI

# Michigan damage precedents and multipliers
DAMAGE_MODELS = {
    'Lane_A_Custody': {
        'name': 'Custody / Parental Rights',
        'case_number': '2024-001507-DC',
        'components': {
            'lost_parenting_time': {
                'description': 'Value of lost parenting time',
                'method': 'days_lost * daily_rate',
                'daily_rate': 100,  # conservative per-day value
                'notes': 'Troxel v Granville 530 US 57: fundamental right',
            },
            'emotional_distress': {
                'description': 'Emotional distress from child separation',
                'method': 'base + duration_multiplier',
                'base': 50000,
                'per_month': 2000,
                'notes': 'Michigan allows emotional distress in custody interference',
            },
            'child_relationship_damage': {
                'description': 'Damage to parent-child bond',
                'method': 'severity_based',
                'range': (25000, 150000),
                'notes': 'Stanley v Illinois 405 US 645: parental bond is liberty interest',
            },
            'counseling_costs': {
                'description': 'Therapy/counseling for parent and child',
                'method': 'actual + projected',
                'estimate': 15000,
            },
        },
    },
    'Lane_B_Housing': {
        'name': 'Housing Rights',
        'case_number': '2025-002760-CZ',
        'components': {
            'habitability_damages': {
                'description': 'Rent abatement for uninhabitable conditions',
                'method': 'months * rent * reduction_pct',
                'monthly_rent': 800,
                'reduction_pct': 0.30,
                'months': 12,
            },
            'security_deposit': {
                'description': 'Wrongfully withheld security deposit',
                'method': 'MCL 554.613 (2x deposit)',
                'deposit_amount': 800,
                'multiplier': 2,
                'notes': 'MCL 554.613: double damages for bad faith retention',
            },
            'moving_costs': {
                'description': 'Forced relocation expenses',
                'method': 'actual_costs',
                'estimate': 5000,
            },
            'emotional_distress_housing': {
                'description': 'Distress from housing instability',
                'method': 'base_amount',
                'base': 10000,
            },
        },
    },
    'Lane_D_PPO': {
        'name': 'False PPO / Malicious Prosecution',
        'case_number': '2023-5907-PP',
        'components': {
            'malicious_prosecution': {
                'description': 'Filing false PPO with knowledge of falsity',
                'method': 'severity_based',
                'range': (25000, 200000),
                'notes': 'Friedman v Dozorc 412 Mich 1: elements met when PPO based on fabrications',
            },
            'abuse_of_process': {
                'description': 'Using PPO to gain custody advantage',
                'method': 'severity_based',
                'range': (15000, 100000),
                'notes': 'Bonner v Chicago Title 194 Mich App 462',
            },
            'stigma_damages': {
                'description': 'Reputational harm from false DV/stalking allegations',
                'method': 'base + impact_multiplier',
                'base': 30000,
                'notes': 'Defamation per se: false accusation of crime',
            },
            'lost_employment': {
                'description': 'Employment impact of false allegations',
                'method': 'actual_losses',
                'estimate': 20000,
            },
        },
    },
    'Lane_E_Misconduct': {
        'name': 'Judicial Misconduct (§1983)',
        'case_number': '2024-001507-DC',
        'components': {
            'constitutional_violation': {
                'description': '14th Amendment due process violation',
                'method': 'per_violation * count',
                'per_violation': 5000,
                'notes': '42 USC §1983: each violation is independent cause of action',
            },
            'conspiracy_damages': {
                'description': '42 USC §1985(3) conspiracy',
                'method': 'severity_based',
                'range': (50000, 500000),
                'notes': 'Dennis v Sparks: private actors lose immunity when conspiring with judge',
            },
            'punitive_damages': {
                'description': 'Punitive damages for willful misconduct',
                'method': 'multiplier_of_compensatory',
                'multiplier': 3,
                'notes': 'Smith v Wade 461 US 30: punitive available under §1983',
            },
        },
    },
    'Lane_F_Appellate': {
        'name': 'Appellate Costs',
        'case_number': 'COA 366810',
        'components': {
            'filing_fees': {
                'description': 'Court filing fees across all courts',
                'method': 'itemized',
                'estimate': 2500,
            },
            'pro_se_time': {
                'description': 'Compensable pro se litigation time',
                'method': 'hours * rate',
                'notes': 'Kay v Ehrler 499 US 432 limits pro se fee recovery, but Michigan MCR 2.403 allows',
            },
            'transcript_costs': {
                'description': 'Court reporter / transcript costs',
                'method': 'actual',
                'estimate': 3000,
            },
        },
    },
}


def get_connection():
    conn = sqlite3.connect(str(DB_PATH), timeout=60)
    conn.execute("PRAGMA busy_timeout=60000")
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA cache_size=-32000")
    return conn


def table_exists(conn, name):
    r = conn.execute("SELECT COUNT(*) FROM sqlite_master WHERE type='table' AND name=?", (name,)).fetchone()
    return r[0] > 0


def get_violation_count(conn):
    """Get total documented violations for §1983 damages."""
    count = 0
    if table_exists(conn, 'judicial_violations'):
        try:
            row = conn.execute("SELECT COUNT(*) FROM judicial_violations").fetchone()
            count = row[0]
        except Exception:
            pass
    return count


def get_contradiction_count(conn):
    """Get total contradictions for perjury/fraud damages."""
    count = 0
    if table_exists(conn, 'detected_contradictions'):
        try:
            row = conn.execute("SELECT COUNT(*) FROM detected_contradictions").fetchone()
            count = row[0]
        except Exception:
            pass
    return count


def get_perjury_count(conn):
    """Get documented perjury instances."""
    count = 0
    if table_exists(conn, 'watson_perjury_compilation'):
        try:
            row = conn.execute("SELECT COUNT(*) FROM watson_perjury_compilation").fetchone()
            count = row[0]
        except Exception:
            pass
    return count


def estimate_lost_parenting_days():
    """Estimate days of lost parenting time."""
    # Assume roughly 50% parenting time denied since separation
    return int(DAYS_SEPARATED * 0.5)


def estimate_pro_se_hours():
    """Estimate hours spent on pro se litigation."""
    # Conservative: 4 hours/day average since case started
    litigation_days = (TODAY - CASE_START_DATE).days
    return int(litigation_days * 2.5)  # 2.5 hours/day avg


def calculate_lane_damages(lane_id, model, conn):
    """Calculate damages for a specific lane."""
    results = {
        'lane': lane_id,
        'name': model['name'],
        'case_number': model.get('case_number', 'N/A'),
        'components': {},
        'low_total': 0,
        'mid_total': 0,
        'high_total': 0,
    }
    
    violation_count = get_violation_count(conn)
    perjury_count = get_perjury_count(conn)
    lost_days = estimate_lost_parenting_days()
    pro_se_hours = estimate_pro_se_hours()
    months_separated = DAYS_SEPARATED // 30
    
    for comp_id, comp in model['components'].items():
        low = mid = high = 0
        
        if comp.get('method') == 'days_lost * daily_rate':
            rate = comp['daily_rate']
            low = lost_days * int(rate * 0.5)
            mid = lost_days * rate
            high = lost_days * int(rate * 1.5)
            
        elif comp.get('method') == 'base + duration_multiplier':
            base = comp.get('base', 0)
            per_month = comp.get('per_month', 0)
            duration_add = per_month * months_separated
            low = int((base + duration_add) * 0.5)
            mid = base + duration_add
            high = int((base + duration_add) * 2)
            
        elif comp.get('method') == 'severity_based':
            r = comp.get('range', (10000, 100000))
            low = r[0]
            mid = (r[0] + r[1]) // 2
            high = r[1]
            
        elif comp.get('method') == 'months * rent * reduction_pct':
            rent = comp.get('monthly_rent', 800)
            pct = comp.get('reduction_pct', 0.3)
            months = comp.get('months', 12)
            mid = int(rent * pct * months)
            low = int(mid * 0.5)
            high = int(mid * 2)
            
        elif comp.get('method') == 'MCL 554.613 (2x deposit)':
            deposit = comp.get('deposit_amount', 800)
            mult = comp.get('multiplier', 2)
            low = deposit
            mid = deposit * mult
            high = deposit * mult  # statutory cap
            
        elif comp.get('method') == 'per_violation * count':
            per_v = comp.get('per_violation', 5000)
            # Cap at reasonable count for damages calculation
            capped_count = min(violation_count, 100)
            low = capped_count * int(per_v * 0.25)
            mid = capped_count * per_v
            high = capped_count * per_v * 2
            
        elif comp.get('method') == 'multiplier_of_compensatory':
            # Will be calculated after other components
            pass
            
        elif comp.get('method') == 'hours * rate':
            hours = pro_se_hours
            low = int(hours * PRO_SE_HOURLY * 0.5)
            mid = hours * PRO_SE_HOURLY
            high = int(hours * PRO_SE_HOURLY * 1.5)
            
        elif comp.get('method') in ['actual_costs', 'actual_losses', 'actual + projected', 'base_amount', 'base + impact_multiplier', 'itemized', 'actual']:
            est = comp.get('estimate', comp.get('base', 10000))
            low = int(est * 0.5)
            mid = est
            high = int(est * 2)
        
        results['components'][comp_id] = {
            'description': comp['description'],
            'low': low,
            'mid': mid,
            'high': high,
            'notes': comp.get('notes', ''),
        }
        results['low_total'] += low
        results['mid_total'] += mid
        results['high_total'] += high
    
    # Handle punitive multiplier
    if 'punitive_damages' in results['components'] and results['components']['punitive_damages']['mid'] == 0:
        compensatory = results['mid_total']
        mult = model['components']['punitive_damages'].get('multiplier', 3)
        results['components']['punitive_damages']['low'] = int(compensatory * 1)
        results['components']['punitive_damages']['mid'] = int(compensatory * mult)
        results['components']['punitive_damages']['high'] = int(compensatory * mult * 2)
        results['low_total'] += results['components']['punitive_damages']['low']
        results['mid_total'] += results['components']['punitive_damages']['mid']
        results['high_total'] += results['components']['punitive_damages']['high']
    
    return results


def main():
    print("=" * 70)
    print("SETTLEMENT VALUE CALCULATOR — Case Valuation Model")
    print("=" * 70)
    print(f"Run: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"Days since separation: {DAYS_SEPARATED}")
    print(f"Estimated lost parenting days: {estimate_lost_parenting_days()}")
    print(f"Estimated pro se hours: {estimate_pro_se_hours()}")
    print()
    
    conn = get_connection()
    
    # Get DB stats for damage calculations
    violations = get_violation_count(conn)
    contradictions = get_contradiction_count(conn)
    perjury = get_perjury_count(conn)
    print(f"  DB Stats: {violations:,} violations | {contradictions:,} contradictions | {perjury:,} perjury items")
    print()
    
    all_results = {}
    grand_low = grand_mid = grand_high = 0
    
    for lane_id, model in DAMAGE_MODELS.items():
        results = calculate_lane_damages(lane_id, model, conn)
        all_results[lane_id] = results
        
        grand_low += results['low_total']
        grand_mid += results['mid_total']
        grand_high += results['high_total']
        
        print(f"{'─' * 60}")
        print(f"  {lane_id}: {model['name']} ({model.get('case_number', 'N/A')})")
        print(f"{'─' * 60}")
        
        for comp_id, comp in results['components'].items():
            print(f"    {comp['description']:40s}  ${comp['low']:>10,} – ${comp['high']:>10,}")
        
        print(f"    {'LANE TOTAL':40s}  ${results['low_total']:>10,} – ${results['high_total']:>10,}")
        print(f"    {'(midpoint)':40s}  ${results['mid_total']:>10,}")
    
    # Convergence multiplier (Lane C)
    # Cross-lane conspiracy multiplier: when same actors commit violations across multiple lanes
    convergence_low = int(grand_low * 0.10)
    convergence_mid = int(grand_mid * 0.15)
    convergence_high = int(grand_high * 0.20)
    
    print(f"\n{'─' * 60}")
    print(f"  Lane C: CONVERGENCE MULTIPLIER")
    print(f"{'─' * 60}")
    print(f"    Cross-lane conspiracy premium (10-20%)    ${convergence_low:>10,} – ${convergence_high:>10,}")
    
    grand_low += convergence_low
    grand_mid += convergence_mid
    grand_high += convergence_high
    
    print(f"\n{'=' * 70}")
    print(f"  GRAND TOTAL — ALL LANES")
    print(f"{'=' * 70}")
    print(f"    LOW  estimate:  ${grand_low:>12,}")
    print(f"    MID  estimate:  ${grand_mid:>12,}")
    print(f"    HIGH estimate:  ${grand_high:>12,}")
    print(f"\n    Settlement negotiation range: ${grand_low:,} – ${grand_high:,}")
    print(f"    Recommended demand: ${int(grand_mid * 1.5):,} (1.5x midpoint)")
    
    # Save reports
    REPORT_DIR.mkdir(parents=True, exist_ok=True)
    
    all_results['convergence'] = {
        'low': convergence_low, 'mid': convergence_mid, 'high': convergence_high,
    }
    all_results['grand_total'] = {
        'low': grand_low, 'mid': grand_mid, 'high': grand_high,
        'recommended_demand': int(grand_mid * 1.5),
    }
    all_results['case_parameters'] = {
        'days_separated': DAYS_SEPARATED,
        'lost_parenting_days': estimate_lost_parenting_days(),
        'pro_se_hours': estimate_pro_se_hours(),
        'violations': violations,
        'contradictions': contradictions,
        'perjury_items': perjury,
    }
    
    report_path = REPORT_DIR / "settlement_valuation.json"
    with open(report_path, 'w', encoding='utf-8') as f:
        json.dump(all_results, f, indent=2, default=str)
    print(f"\n  Report saved: {report_path}")
    
    # Markdown
    md_path = REPORT_DIR / "SETTLEMENT_VALUATION_REPORT.md"
    with open(md_path, 'w', encoding='utf-8') as f:
        f.write("# Settlement Value Calculator\n\n")
        f.write(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
        f.write(f"## Case Parameters\n\n")
        f.write(f"- Days since separation: {DAYS_SEPARATED}\n")
        f.write(f"- Lost parenting days: ~{estimate_lost_parenting_days()}\n")
        f.write(f"- Pro se hours: ~{estimate_pro_se_hours()}\n")
        f.write(f"- Documented violations: {violations:,}\n")
        f.write(f"- Documented contradictions: {contradictions:,}\n")
        f.write(f"- Perjury compilation items: {perjury:,}\n\n")
        
        f.write("## Grand Total\n\n")
        f.write(f"| Estimate | Amount |\n")
        f.write(f"|----------|--------|\n")
        f.write(f"| Low | ${grand_low:,} |\n")
        f.write(f"| Midpoint | ${grand_mid:,} |\n")
        f.write(f"| High | ${grand_high:,} |\n")
        f.write(f"| **Recommended Demand** | **${int(grand_mid * 1.5):,}** |\n\n")
        
        for lane_id, results in all_results.items():
            if lane_id in ['convergence', 'grand_total', 'case_parameters']:
                continue
            f.write(f"\n---\n\n## {results['name']} ({results.get('case_number', '')})\n\n")
            f.write(f"| Component | Low | Mid | High |\n")
            f.write(f"|-----------|-----|-----|------|\n")
            for comp_id, comp in results['components'].items():
                f.write(f"| {comp['description']} | ${comp['low']:,} | ${comp['mid']:,} | ${comp['high']:,} |\n")
            f.write(f"| **Lane Total** | **${results['low_total']:,}** | **${results['mid_total']:,}** | **${results['high_total']:,}** |\n")
    
    print(f"  Markdown report saved: {md_path}")
    conn.close()


if __name__ == '__main__':
    main()
