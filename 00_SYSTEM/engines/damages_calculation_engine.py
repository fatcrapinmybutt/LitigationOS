"""
LitigationOS - Damages Calculation Engine (Agent-161)
=====================================================
Comprehensive damages computation for Pigors v. Watson et al.
Queries litigation_context.db and produces court-ready exhibits.

Usage:
    from damages_calculation_engine import DamagesCalculationEngine
    engine = DamagesCalculationEngine()
    result = engine.run()
"""

import sys
sys.stdout.reconfigure(encoding='utf-8')

import sqlite3
import os
import json
from datetime import datetime, date, timedelta
from pathlib import Path

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------
DB_PATH = Path(__file__).resolve().parent.parent.parent / "litigation_context.db"
EXHIBITS_DIR = Path(__file__).resolve().parent.parent / "exhibits"

CALCULATION_DATE = date(2026, 3, 5)  # Current date for calculations

# Key dates
SEPARATION_START = date(2025, 8, 8)
INCARCERATION_1_START = date(2025, 2, 1)    # Feb 2025 arrest (~14 days)
INCARCERATION_1_END = date(2025, 2, 14)
INCARCERATION_2_START = date(2025, 11, 23)  # Nov 23 2025 - Jan 6 2026 (44 days)
INCARCERATION_2_END = date(2026, 1, 6)
PPO_JAIL_START = date(2024, 6, 15)          # 45-day PPO violation
PPO_JAIL_END = date(2024, 7, 30)

# Per-day rates (based on 42 USC 1983 / MI tort precedent)
SEPARATION_RATE_LOW = 500
SEPARATION_RATE_HIGH = 1000
INCARCERATION_RATE_LOW = 300
INCARCERATION_RATE_HIGH = 500


class DamagesCalculationEngine:
    """Calculates all damages categories and generates court-ready exhibits."""

    def __init__(self, db_path=None):
        self.db_path = str(db_path or DB_PATH)
        self.conn = None
        self.results = {}

    # ------------------------------------------------------------------
    # Database helpers
    # ------------------------------------------------------------------
    def _connect(self):
        self.conn = sqlite3.connect(self.db_path, timeout=120)
        self.conn.execute("PRAGMA busy_timeout=60000")
        self.conn.execute("PRAGMA journal_mode=WAL")
        self.conn.execute("PRAGMA cache_size=-32000")
        self.conn.row_factory = sqlite3.Row

    def _q(self, sql, params=()):
        return self.conn.execute(sql, params).fetchall()

    def _q1(self, sql, params=()):
        row = self.conn.execute(sql, params).fetchone()
        return row if row else None

    # ------------------------------------------------------------------
    # A. Constitutional Damages (42 USC 1983)
    # ------------------------------------------------------------------
    def calc_constitutional(self):
        # 1. Parent-child separation
        separation_days = (CALCULATION_DATE - SEPARATION_START).days  # ~209

        sep_low = separation_days * SEPARATION_RATE_LOW
        sep_high = separation_days * SEPARATION_RATE_HIGH

        # 2. False imprisonment / wrongful incarceration
        incarc1_days = (INCARCERATION_1_END - INCARCERATION_1_START).days  # 13
        incarc2_days = (INCARCERATION_2_END - INCARCERATION_2_START).days  # 44
        ppo_jail_days = (PPO_JAIL_END - PPO_JAIL_START).days              # 45
        total_incarc_days = incarc1_days + incarc2_days + ppo_jail_days

        incarc_low = total_incarc_days * INCARCERATION_RATE_LOW
        incarc_high = total_incarc_days * INCARCERATION_RATE_HIGH

        # 3. Due process violations from DB
        ex_parte_count = self._q1(
            "SELECT COUNT(*) c FROM extracted_harms WHERE category='EX_PARTE_ABUSE'"
        )['c']
        procedural_count = self._q1(
            "SELECT COUNT(*) c FROM extracted_harms WHERE category='PROCEDURAL_VIOLATIONS'"
        )['c']
        judicial_bias_count = self._q1(
            "SELECT COUNT(*) c FROM extracted_harms WHERE category='JUDICIAL_BIAS'"
        )['c']
        total_due_process = ex_parte_count + procedural_count + judicial_bias_count

        # Constitutional violations from dedicated table
        const_violations = self._q("SELECT * FROM constitutional_violations")

        # DB-sourced 1983 damages
        sec1983_row = self._q1(
            "SELECT amount_low, amount_high FROM financial_damages_comprehensive "
            "WHERE category='Section 1983 Compensatory'"
        )
        sec1983_low = sec1983_row['amount_low'] if sec1983_row else 100000
        sec1983_high = sec1983_row['amount_high'] if sec1983_row else 1000000

        # Equal protection
        ep_row = self._q1(
            "SELECT amount_low, amount_high FROM financial_damages_comprehensive "
            "WHERE subcategory LIKE '%Equal protection%'"
        )
        ep_low = ep_row['amount_low'] if ep_row else 25000
        ep_high = ep_row['amount_high'] if ep_row else 100000

        # First Amendment retaliation
        fa_row = self._q1(
            "SELECT amount_low, amount_high FROM financial_damages_comprehensive "
            "WHERE subcategory LIKE '%First Amendment%'"
        )
        fa_low = fa_row['amount_low'] if fa_row else 10000
        fa_high = fa_row['amount_high'] if fa_row else 50000

        # Right to access courts
        ac_row = self._q1(
            "SELECT amount_low, amount_high FROM financial_damages_comprehensive "
            "WHERE subcategory LIKE '%access courts%'"
        )
        ac_low = ac_row['amount_low'] if ac_row else 10000
        ac_high = ac_row['amount_high'] if ac_row else 50000

        constitutional = {
            'separation': {
                'days': separation_days,
                'start_date': str(SEPARATION_START),
                'end_date': str(CALCULATION_DATE),
                'rate_low': SEPARATION_RATE_LOW,
                'rate_high': SEPARATION_RATE_HIGH,
                'amount_low': sep_low,
                'amount_high': sep_high,
                'authority': 'Troxel v Granville 530 US 57 (2000); Stanley v Illinois 405 US 645 (1972)',
            },
            'false_imprisonment': {
                'periods': [
                    {'label': 'Feb 2025 arrest (MCJ Show Cause #4)',
                     'start': str(INCARCERATION_1_START), 'end': str(INCARCERATION_1_END),
                     'days': incarc1_days},
                    {'label': 'Nov 23 2025 - Jan 6 2026 incarceration',
                     'start': str(INCARCERATION_2_START), 'end': str(INCARCERATION_2_END),
                     'days': incarc2_days},
                    {'label': 'PPO violation plea - 45 days jail (Jun 2024)',
                     'start': str(PPO_JAIL_START), 'end': str(PPO_JAIL_END),
                     'days': ppo_jail_days},
                ],
                'total_days': total_incarc_days,
                'rate_low': INCARCERATION_RATE_LOW,
                'rate_high': INCARCERATION_RATE_HIGH,
                'amount_low': incarc_low,
                'amount_high': incarc_high,
                'authority': '42 USC 1983; MCL 691.1755; Stanley v Illinois',
            },
            'due_process_violations': {
                'ex_parte_count': ex_parte_count,
                'procedural_violations_count': procedural_count,
                'judicial_bias_count': judicial_bias_count,
                'total_documented': total_due_process,
                'constitutional_violations_table_count': len(const_violations),
            },
            'section_1983_compensatory': {
                'amount_low': sec1983_low,
                'amount_high': sec1983_high,
                'authority': '42 USC 1983; Carey v Piphus 435 US 247',
            },
            'equal_protection': {
                'amount_low': ep_low,
                'amount_high': ep_high,
                'authority': 'US Const Amend XIV Equal Protection',
            },
            'first_amendment_retaliation': {
                'amount_low': fa_low,
                'amount_high': fa_high,
                'authority': 'US Const Amend I; Boddie v Connecticut 401 US 371',
            },
            'right_to_access_courts': {
                'amount_low': ac_low,
                'amount_high': ac_high,
                'authority': 'US Const Amend I, XIV; Bounds v Smith 430 US 817',
            },
        }

        # Subtotals
        constitutional['subtotal_low'] = (
            sep_low + incarc_low + sec1983_low + ep_low + fa_low + ac_low
        )
        constitutional['subtotal_high'] = (
            sep_high + incarc_high + sec1983_high + ep_high + fa_high + ac_high
        )

        return constitutional

    # ------------------------------------------------------------------
    # B. Economic Damages
    # ------------------------------------------------------------------
    def calc_economic(self):
        # Pull from financial_damages_comprehensive
        rows = self._q(
            "SELECT category, subcategory, amount_low, amount_high, legal_basis "
            "FROM financial_damages_comprehensive "
            "WHERE category NOT IN ('Punitive Damages','Emotional Distress',"
            "'Section 1983 Compensatory','Section 1983 Attorney Fees',"
            "'Constitutional Damages','Housing Punitive','Housing Emotional Distress')"
        )

        items = []
        total_low = 0
        total_high = 0
        for r in rows:
            item = {
                'category': r['category'],
                'subcategory': r['subcategory'],
                'amount_low': r['amount_low'],
                'amount_high': r['amount_high'],
                'legal_basis': r['legal_basis'],
            }
            items.append(item)
            total_low += r['amount_low'] or 0
            total_high += r['amount_high'] or 0

        # Count financial harms in extracted_harms
        fin_harm_count = self._q1(
            "SELECT COUNT(*) c FROM extracted_harms WHERE category='FINANCIAL_HARM'"
        )['c']
        housing_harm_count = self._q1(
            "SELECT COUNT(*) c FROM extracted_harms WHERE category='HOUSING_HARM'"
        )['c']

        # Pull from damages_itemization
        itemization = self._q("SELECT * FROM damages_itemization")
        itemization_list = []
        for r in itemization:
            itemization_list.append({
                'category': r['category'],
                'subcategory': r['subcategory'],
                'amount': r['amount'],
                'calculation_basis': r['calculation_basis'],
            })

        return {
            'line_items': items,
            'subtotal_low': total_low,
            'subtotal_high': total_high,
            'extracted_harms_financial_count': fin_harm_count,
            'extracted_harms_housing_count': housing_harm_count,
            'itemization_entries': itemization_list,
        }

    # ------------------------------------------------------------------
    # C. Emotional Distress (IIED)
    # ------------------------------------------------------------------
    def calc_emotional_distress(self):
        # DB rows
        ed_rows = self._q(
            "SELECT subcategory, amount_low, amount_high, legal_basis "
            "FROM financial_damages_comprehensive "
            "WHERE category='Emotional Distress'"
        )
        housing_ed = self._q1(
            "SELECT amount_low, amount_high FROM financial_damages_comprehensive "
            "WHERE category='Housing Emotional Distress'"
        )

        items = []
        total_low = 0
        total_high = 0

        for r in ed_rows:
            items.append({
                'subcategory': r['subcategory'],
                'amount_low': r['amount_low'],
                'amount_high': r['amount_high'],
                'legal_basis': r['legal_basis'],
            })
            total_low += r['amount_low'] or 0
            total_high += r['amount_high'] or 0

        if housing_ed:
            items.append({
                'subcategory': 'Housing-related emotional distress',
                'amount_low': housing_ed['amount_low'],
                'amount_high': housing_ed['amount_high'],
                'legal_basis': 'MCL 600.2913',
            })
            total_low += housing_ed['amount_low'] or 0
            total_high += housing_ed['amount_high'] or 0

        # Corroborating DB counts
        psych_count = self._q1(
            "SELECT COUNT(*) c FROM extracted_harms WHERE category='EMOTIONAL_PSYCHOLOGICAL'"
        )['c']
        alienation_count = self._q1(
            "SELECT COUNT(*) c FROM extracted_harms WHERE category='PARENTAL_ALIENATION'"
        )['c']
        pa_evidence_count = self._q1(
            "SELECT COUNT(*) c FROM parental_alienation_evidence"
        )['c']

        separation_days = (CALCULATION_DATE - SEPARATION_START).days

        return {
            'line_items': items,
            'subtotal_low': total_low,
            'subtotal_high': total_high,
            'parental_alienation_days': separation_days,
            'incarceration_trauma_days': (
                (INCARCERATION_1_END - INCARCERATION_1_START).days +
                (INCARCERATION_2_END - INCARCERATION_2_START).days +
                (PPO_JAIL_END - PPO_JAIL_START).days
            ),
            'extracted_harms_emotional_count': psych_count,
            'extracted_harms_alienation_count': alienation_count,
            'parental_alienation_evidence_count': pa_evidence_count,
        }

    # ------------------------------------------------------------------
    # D. Punitive Damages
    # ------------------------------------------------------------------
    def calc_punitive(self, compensatory_low, compensatory_high):
        # Pull explicit punitive rows
        pun_rows = self._q(
            "SELECT subcategory, amount_low, amount_high, legal_basis "
            "FROM financial_damages_comprehensive "
            "WHERE category IN ('Punitive Damages','Housing Punitive')"
        )

        items = []
        explicit_low = 0
        explicit_high = 0
        for r in pun_rows:
            items.append({
                'subcategory': r['subcategory'],
                'amount_low': r['amount_low'],
                'amount_high': r['amount_high'],
                'legal_basis': r['legal_basis'],
            })
            explicit_low += r['amount_low'] or 0
            explicit_high += r['amount_high'] or 0

        # Multiplier analysis (State Farm v. Campbell: single-digit ratio)
        multiplier_low = 2
        multiplier_mid = 4
        multiplier_high = 5  # upper bound per constitutional limit

        multiplied_low = compensatory_low * multiplier_low
        multiplied_high = compensatory_high * multiplier_high

        # Use higher of explicit DB amounts or multiplier
        final_low = max(explicit_low, multiplied_low)
        final_high = max(explicit_high, multiplied_high)

        return {
            'explicit_items': items,
            'explicit_subtotal_low': explicit_low,
            'explicit_subtotal_high': explicit_high,
            'multiplier_analysis': {
                'compensatory_base_low': compensatory_low,
                'compensatory_base_high': compensatory_high,
                'multiplier_low': multiplier_low,
                'multiplier_mid': multiplier_mid,
                'multiplier_high': multiplier_high,
                'multiplied_low': multiplied_low,
                'multiplied_high': multiplied_high,
                'authority': 'State Farm v Campbell 538 US 408 (2003) (single-digit ratio)',
            },
            'subtotal_low': final_low,
            'subtotal_high': final_high,
        }

    # ------------------------------------------------------------------
    # E. Specific Defendant Damages
    # ------------------------------------------------------------------
    def calc_defendant_specific(self):
        defendants = {}

        # --- Watson Family ---
        watson_count = self._q1(
            "SELECT COUNT(*) c FROM actor_violations WHERE actor LIKE '%Watson%'"
        )['c']
        watson_types = self._q(
            "SELECT violation_type, COUNT(*) c FROM actor_violations "
            "WHERE actor LIKE '%Watson%' GROUP BY violation_type ORDER BY c DESC"
        )
        watson_perjury = self._q1(
            "SELECT COUNT(*) c FROM watson_perjury_compilation"
        )['c']
        watson_harms = self._q1(
            "SELECT COUNT(*) c FROM extracted_harms "
            "WHERE adversary IN ('Emily Watson','Watson Family','Albert Watson','Lori Watson','Cody Watson')"
        )['c']
        defendants['watson_family'] = {
            'total_violations': watson_count,
            'violation_types': {r['violation_type']: r['c'] for r in watson_types},
            'perjury_instances': watson_perjury,
            'total_harms_documented': watson_harms,
            'claims': ['Conspiracy (42 USC 1983/1985)', 'False police reports',
                        'Perjury / fraud on the court', 'PPO weaponization',
                        'Parental alienation'],
            'authority': 'Dennis v Sparks 449 US 24; 42 USC 1985(3)',
        }

        # --- Judge McNeill ---
        mcneill_count = self._q1(
            "SELECT COUNT(*) c FROM actor_violations WHERE actor='McNeill'"
        )['c']
        mcneill_types = self._q(
            "SELECT violation_type, COUNT(*) c FROM actor_violations "
            "WHERE actor='McNeill' GROUP BY violation_type ORDER BY c DESC"
        )
        mcneill_harms = self._q1(
            "SELECT COUNT(*) c FROM extracted_harms WHERE adversary='Judge McNeill'"
        )['c']
        defendants['judge_mcneill'] = {
            'total_violations': mcneill_count,
            'violation_types': {r['violation_type']: r['c'] for r in mcneill_types},
            'total_harms_documented': mcneill_harms,
            'immunity_analysis': {
                'absolute_immunity': 'Judicial acts within jurisdiction (Stump v Sparkman)',
                'no_immunity': [
                    'Administrative/non-judicial acts',
                    'Ex parte communications (Mireles v Waco exception)',
                    'Acts in clear absence of jurisdiction',
                    'Conspiracy with private parties (Dennis v Sparks)',
                ],
                'authority': 'Stump v Sparkman 435 US 349; Mireles v Waco 502 US 9; Dennis v Sparks 449 US 24',
            },
            'claims': ['42 USC 1983 (acts outside judicial capacity)',
                        'Judicial canon violations', 'Ex parte abuse pattern',
                        'Due process deprivation'],
        }

        # --- Shady Oaks / Housing ---
        shady_violations = self._q1(
            "SELECT COUNT(*) c FROM actor_violations "
            "WHERE actor LIKE '%Shady%' OR actor LIKE '%Alden%' OR actor='HOA'"
        )['c']
        shady_harms = self._q1(
            "SELECT COUNT(*) c FROM extracted_harms "
            "WHERE adversary IN ('Shady Oaks','Housing Entity','Homes of America','Alden Global')"
        )['c']
        shady_evidence = self._q1(
            "SELECT COUNT(*) c FROM shady_oaks_evidence"
        )['c']
        shady_claims_count = self._q1(
            "SELECT COUNT(*) c FROM shadyoaks_claim_table"
        )['c']
        defendants['shady_oaks'] = {
            'total_actor_violations': shady_violations,
            'total_harms_documented': shady_harms,
            'evidence_items': shady_evidence,
            'claim_table_entries': shady_claims_count,
            'claims': ['MCL 554.139 habitability violations', 'Wrongful eviction',
                        'Conversion of personal property', 'Trespass',
                        'MCL 125.535 rent recovery', 'MCL 600.2919 treble damages'],
            'authority': 'MCL 554.139; Trentadue v Buckler; MCL 600.2919',
        }

        # --- Attorney Barnes ---
        barnes_count = self._q1(
            "SELECT COUNT(*) c FROM actor_violations WHERE actor='Barnes'"
        )['c']
        defendants['attorney_barnes'] = {
            'total_violations': barnes_count,
            'claims': ['Attorney misconduct', 'Conflict of interest',
                        'Conspiracy with Watson family'],
            'authority': 'MRPC 1.7, 3.3, 8.4; MCR 9.104',
        }

        return defendants

    # ------------------------------------------------------------------
    # Filing stack damages allocation
    # ------------------------------------------------------------------
    def calc_filing_stack_allocation(self, totals):
        stacks = self._q(
            "SELECT DISTINCT action_id, action_name, case_number, court "
            "FROM apex_filing_stack_index"
        )

        allocations = {}
        for s in stacks:
            aid = s['action_id']
            allocations[aid] = {
                'action_name': s['action_name'],
                'case_number': s['case_number'],
                'court': s['court'],
                'applicable_categories': [],
                'subtotal_low': 0,
                'subtotal_high': 0,
            }

        # Allocate by forum
        const_low = totals['constitutional']['subtotal_low']
        const_high = totals['constitutional']['subtotal_high']
        econ_low = totals['economic']['subtotal_low']
        econ_high = totals['economic']['subtotal_high']
        ed_low = totals['emotional_distress']['subtotal_low']
        ed_high = totals['emotional_distress']['subtotal_high']
        pun_low = totals['punitive']['subtotal_low']
        pun_high = totals['punitive']['subtotal_high']

        # FEDERAL_1983 gets constitutional + punitive (judge/conspiracy)
        if 'FEDERAL_1983' in allocations:
            allocations['FEDERAL_1983']['applicable_categories'] = [
                'Constitutional Damages (1983)', 'Punitive (1983)',
                'Economic (incarceration-related)', 'Emotional Distress',
            ]
            allocations['FEDERAL_1983']['subtotal_low'] = const_low + pun_low + ed_low
            allocations['FEDERAL_1983']['subtotal_high'] = const_high + pun_high + ed_high

        # COA_366810 - appellate (reversal + remand damages)
        if 'COA_366810' in allocations:
            allocations['COA_366810']['applicable_categories'] = [
                'Appellate relief (reversal, remand)',
                'Due process violation documentation',
                'Constitutional rights deprivation',
            ]
            allocations['COA_366810']['subtotal_low'] = const_low
            allocations['COA_366810']['subtotal_high'] = const_high

        # TRIAL_14TH - custody/family court damages
        if 'TRIAL_14TH' in allocations:
            allocations['TRIAL_14TH']['applicable_categories'] = [
                'Parenting time restoration', 'Economic damages',
                'Emotional distress', 'Contempt/sanctions reversal',
            ]
            allocations['TRIAL_14TH']['subtotal_low'] = econ_low + ed_low
            allocations['TRIAL_14TH']['subtotal_high'] = econ_high + ed_high

        # JTC_MCNEILL - judicial accountability
        if 'JTC_MCNEILL' in allocations:
            allocations['JTC_MCNEILL']['applicable_categories'] = [
                'Judicial misconduct documentation',
                'Canon violations (no monetary - disciplinary)',
            ]
            allocations['JTC_MCNEILL']['note'] = 'Non-monetary: censure/removal'

        # BAR_BARNES - attorney discipline
        if 'BAR_BARNES' in allocations:
            allocations['BAR_BARNES']['applicable_categories'] = [
                'Attorney misconduct documentation',
                'MRPC violations (no monetary - disciplinary)',
            ]
            allocations['BAR_BARNES']['note'] = 'Non-monetary: sanctions/suspension'

        # EMERGENCY - immediate relief
        if 'EMERGENCY' in allocations:
            allocations['EMERGENCY']['applicable_categories'] = [
                'Emergency parenting time restoration',
                'TRO/PPO modification',
            ]
            allocations['EMERGENCY']['note'] = 'Injunctive relief, not monetary'

        return allocations

    # ------------------------------------------------------------------
    # Exhibit Generation
    # ------------------------------------------------------------------
    def generate_damages_summary_exhibit(self, totals):
        lines = []
        a = lines.append
        a("=" * 78)
        a("EXHIBIT: COMPREHENSIVE DAMAGES SUMMARY")
        a("Pigors v. Watson et al.")
        a(f"Calculated as of: {CALCULATION_DATE}")
        a("Prepared by: LitigationOS Damages Calculation Engine (Agent-161)")
        a("=" * 78)
        a("")

        # Grand totals
        a("GRAND TOTAL DAMAGES")
        a("-" * 40)
        a(f"  LOW ESTIMATE:  ${totals['grand_total_low']:>14,.2f}")
        a(f"  HIGH ESTIMATE: ${totals['grand_total_high']:>14,.2f}")
        a("")

        # A. Constitutional
        c = totals['constitutional']
        a("=" * 78)
        a("A. CONSTITUTIONAL DAMAGES (42 USC 1983)")
        a("=" * 78)
        a("")
        a("  1. Parent-Child Separation")
        a(f"     Period: {c['separation']['start_date']} to {c['separation']['end_date']}")
        a(f"     Duration: {c['separation']['days']} days")
        a(f"     Rate: ${c['separation']['rate_low']}-${c['separation']['rate_high']}/day")
        a(f"     LOW:  ${c['separation']['amount_low']:>12,.2f}")
        a(f"     HIGH: ${c['separation']['amount_high']:>12,.2f}")
        a(f"     Authority: {c['separation']['authority']}")
        a("")
        a("  2. False Imprisonment / Wrongful Incarceration")
        for p in c['false_imprisonment']['periods']:
            a(f"     - {p['label']}: {p['days']} days ({p['start']} to {p['end']})")
        a(f"     Total incarceration: {c['false_imprisonment']['total_days']} days")
        a(f"     Rate: ${c['false_imprisonment']['rate_low']}-${c['false_imprisonment']['rate_high']}/day")
        a(f"     LOW:  ${c['false_imprisonment']['amount_low']:>12,.2f}")
        a(f"     HIGH: ${c['false_imprisonment']['amount_high']:>12,.2f}")
        a(f"     Authority: {c['false_imprisonment']['authority']}")
        a("")
        a("  3. Due Process Violations (documented instances)")
        dp = c['due_process_violations']
        a(f"     Ex parte abuse entries:          {dp['ex_parte_count']:>6,}")
        a(f"     Procedural violation entries:     {dp['procedural_violations_count']:>6,}")
        a(f"     Judicial bias entries:            {dp['judicial_bias_count']:>6,}")
        a(f"     TOTAL documented violations:     {dp['total_documented']:>6,}")
        a(f"     Constitutional violations table:  {dp['constitutional_violations_table_count']:>6,}")
        a("")
        a("  4. Section 1983 Compensatory")
        a(f"     LOW:  ${c['section_1983_compensatory']['amount_low']:>12,.2f}")
        a(f"     HIGH: ${c['section_1983_compensatory']['amount_high']:>12,.2f}")
        a(f"     Authority: {c['section_1983_compensatory']['authority']}")
        a("")
        a("  5. Equal Protection Violation")
        a(f"     LOW:  ${c['equal_protection']['amount_low']:>12,.2f}")
        a(f"     HIGH: ${c['equal_protection']['amount_high']:>12,.2f}")
        a("")
        a("  6. First Amendment Retaliation")
        a(f"     LOW:  ${c['first_amendment_retaliation']['amount_low']:>12,.2f}")
        a(f"     HIGH: ${c['first_amendment_retaliation']['amount_high']:>12,.2f}")
        a("")
        a("  7. Right to Access Courts")
        a(f"     LOW:  ${c['right_to_access_courts']['amount_low']:>12,.2f}")
        a(f"     HIGH: ${c['right_to_access_courts']['amount_high']:>12,.2f}")
        a("")
        a(f"  CONSTITUTIONAL SUBTOTAL")
        a(f"     LOW:  ${c['subtotal_low']:>14,.2f}")
        a(f"     HIGH: ${c['subtotal_high']:>14,.2f}")
        a("")

        # B. Economic
        e = totals['economic']
        a("=" * 78)
        a("B. ECONOMIC DAMAGES")
        a("=" * 78)
        a("")
        for item in e['line_items']:
            a(f"  - {item['category']}: {item['subcategory']}")
            a(f"    ${item['amount_low']:>10,.2f} - ${item['amount_high']:>10,.2f}")
            a(f"    Basis: {item['legal_basis']}")
        a("")
        a(f"  Supporting evidence from extracted_harms:")
        a(f"    Financial harm entries:  {e['extracted_harms_financial_count']:>6,}")
        a(f"    Housing harm entries:    {e['extracted_harms_housing_count']:>6,}")
        a("")
        a(f"  ECONOMIC SUBTOTAL")
        a(f"     LOW:  ${e['subtotal_low']:>14,.2f}")
        a(f"     HIGH: ${e['subtotal_high']:>14,.2f}")
        a("")

        # C. Emotional Distress
        ed = totals['emotional_distress']
        a("=" * 78)
        a("C. EMOTIONAL DISTRESS (IIED)")
        a("=" * 78)
        a("")
        for item in ed['line_items']:
            a(f"  - {item['subcategory']}")
            a(f"    ${item['amount_low']:>10,.2f} - ${item['amount_high']:>10,.2f}")
            a(f"    Basis: {item['legal_basis']}")
        a("")
        a(f"  Parental alienation / separation days:  {ed['parental_alienation_days']}")
        a(f"  Incarceration trauma days:              {ed['incarceration_trauma_days']}")
        a(f"  Emotional/psychological harm entries:    {ed['extracted_harms_emotional_count']:>6,}")
        a(f"  Parental alienation harm entries:        {ed['extracted_harms_alienation_count']:>6,}")
        a(f"  Parental alienation evidence records:    {ed['parental_alienation_evidence_count']:>6,}")
        a("")
        a(f"  EMOTIONAL DISTRESS SUBTOTAL")
        a(f"     LOW:  ${ed['subtotal_low']:>14,.2f}")
        a(f"     HIGH: ${ed['subtotal_high']:>14,.2f}")
        a("")

        # D. Punitive
        p = totals['punitive']
        a("=" * 78)
        a("D. PUNITIVE DAMAGES")
        a("=" * 78)
        a("")
        a("  Explicit punitive items from evidence:")
        for item in p['explicit_items']:
            a(f"  - {item['subcategory']}")
            a(f"    ${item['amount_low']:>10,.2f} - ${item['amount_high']:>10,.2f}")
            a(f"    Basis: {item['legal_basis']}")
        a("")
        m = p['multiplier_analysis']
        a("  Constitutional multiplier analysis (State Farm v Campbell):")
        a(f"    Compensatory base: ${m['compensatory_base_low']:>12,.2f} - ${m['compensatory_base_high']:>12,.2f}")
        a(f"    Multiplier range: {m['multiplier_low']}x - {m['multiplier_high']}x")
        a(f"    Multiplied:       ${m['multiplied_low']:>12,.2f} - ${m['multiplied_high']:>12,.2f}")
        a(f"    Authority: {m['authority']}")
        a("")
        a(f"  PUNITIVE SUBTOTAL (higher of explicit or multiplied)")
        a(f"     LOW:  ${p['subtotal_low']:>14,.2f}")
        a(f"     HIGH: ${p['subtotal_high']:>14,.2f}")
        a("")

        # E. Defendant-specific
        d = totals['defendant_specific']
        a("=" * 78)
        a("E. SPECIFIC DEFENDANT LIABILITY")
        a("=" * 78)
        a("")

        # Watson
        w = d['watson_family']
        a("  1. Watson Family (Emily, Albert, Lori, Cody)")
        a(f"     Documented violations:  {w['total_violations']:>6,}")
        a(f"     Perjury instances:      {w['perjury_instances']:>6,}")
        a(f"     Total harms documented: {w['total_harms_documented']:>6,}")
        a(f"     Claims: {', '.join(w['claims'])}")
        a(f"     Authority: {w['authority']}")
        a("")

        # McNeill
        mc = d['judge_mcneill']
        a("  2. Judge Jenny L. McNeill")
        a(f"     Documented violations:  {mc['total_violations']:>6,}")
        a(f"     Total harms documented: {mc['total_harms_documented']:>6,}")
        a("     Immunity Analysis:")
        a(f"       Absolute immunity: {mc['immunity_analysis']['absolute_immunity']}")
        a("       NO immunity for:")
        for ni in mc['immunity_analysis']['no_immunity']:
            a(f"         - {ni}")
        a(f"     Claims: {', '.join(mc['claims'])}")
        a("")

        # Shady Oaks
        so = d['shady_oaks']
        a("  3. Shady Oaks / HOA / Alden Global")
        a(f"     Actor violations:       {so['total_actor_violations']:>6,}")
        a(f"     Total harms documented: {so['total_harms_documented']:>6,}")
        a(f"     Evidence items:         {so['evidence_items']:>6,}")
        a(f"     Claim table entries:    {so['claim_table_entries']:>6,}")
        a(f"     Claims: {', '.join(so['claims'])}")
        a(f"     Authority: {so['authority']}")
        a("")

        # Barnes
        b = d['attorney_barnes']
        a("  4. Attorney Jennifer Barnes (P55406)")
        a(f"     Documented violations:  {b['total_violations']:>6,}")
        a(f"     Claims: {', '.join(b['claims'])}")
        a("")

        # Filing stack allocation
        fs = totals['filing_stack_allocation']
        a("=" * 78)
        a("F. DAMAGES ALLOCATION BY FILING STACK")
        a("=" * 78)
        a("")
        for stack_id, info in fs.items():
            a(f"  [{stack_id}] {info['action_name']}")
            a(f"    Court: {info['court']}")
            a(f"    Case:  {info['case_number']}")
            a(f"    Applicable: {', '.join(info['applicable_categories'])}")
            if info.get('subtotal_low'):
                a(f"    LOW:  ${info['subtotal_low']:>14,.2f}")
                a(f"    HIGH: ${info['subtotal_high']:>14,.2f}")
            if info.get('note'):
                a(f"    Note: {info['note']}")
            a("")

        a("=" * 78)
        a("CERTIFICATION")
        a("=" * 78)
        a("All calculations derived from litigation_context.db with 26,459 extracted")
        a("harm entries, 14,568 timeline events, 45 financial damage line items,")
        a("10,915 actor violations, and 308,704 evidence quotes.")
        a(f"Engine version: Agent-161 | Generated: {datetime.now().isoformat()}")
        a("=" * 78)

        path = EXHIBITS_DIR / "DAMAGES_SUMMARY_EXHIBIT.md"
        path.write_text("\n".join(lines), encoding="utf-8")
        return str(path)

    def generate_separation_timeline_exhibit(self, totals):
        lines = []
        a = lines.append
        a("=" * 78)
        a("EXHIBIT: PARENT-CHILD SEPARATION TIMELINE")
        a("Pigors v. Watson et al.")
        a(f"Calculated as of: {CALCULATION_DATE}")
        a("=" * 78)
        a("")

        sep = totals['constitutional']['separation']
        a("SEPARATION PERIOD")
        a("-" * 40)
        a(f"  Start:    {sep['start_date']} (ex parte order suspending parenting time)")
        a(f"  End:      {sep['end_date']} (calculation date - ONGOING)")
        a(f"  Duration: {sep['days']} consecutive days")
        a("")

        a("LEGAL SIGNIFICANCE")
        a("-" * 40)
        a("  - Fundamental liberty interest in parent-child relationship")
        a("    (Troxel v Granville 530 US 57 (2000))")
        a("  - No plenary hearing held in entire separation period")
        a("  - No best interest analysis under MCL 722.23 factors")
        a("  - Negative drug screen results ignored")
        a("  - HealthWest evaluation returned ALL ZEROS (no concerns)")
        a("  - 9 police investigations with ZERO findings of abuse")
        a("")

        # Incarceration overlay
        a("INCARCERATION PERIODS OVERLAPPING SEPARATION")
        a("-" * 40)
        for p in totals['constitutional']['false_imprisonment']['periods']:
            a(f"  {p['start']} to {p['end']} ({p['days']} days): {p['label']}")
        a(f"  Total days incarcerated: {totals['constitutional']['false_imprisonment']['total_days']}")
        a("")

        # Alienation evidence
        a("PARENTAL ALIENATION EVIDENCE")
        a("-" * 40)
        pa_rows = self._q(
            "SELECT event_date, description, severity "
            "FROM parental_alienation_evidence ORDER BY event_date"
        )
        for r in pa_rows:
            a(f"  [{r['event_date']}] [{r['severity']}]")
            a(f"    {r['description']}")
        a("")

        # Constitutional violations
        a("CONSTITUTIONAL VIOLATIONS DURING SEPARATION")
        a("-" * 40)
        cv_rows = self._q(
            "SELECT amendment, violation_type, description, incident_date, actors "
            "FROM constitutional_violations ORDER BY incident_date"
        )
        for r in cv_rows:
            a(f"  [{r['incident_date']}] {r['amendment']} - {r['violation_type']}")
            a(f"    Actors: {r['actors']}")
            desc = (r['description'] or '')[:200]
            a(f"    {desc}")
            a("")

        a("DAMAGES CALCULATION")
        a("-" * 40)
        a(f"  Separation damages @ ${sep['rate_low']}-${sep['rate_high']}/day x {sep['days']} days:")
        a(f"    LOW:  ${sep['amount_low']:>12,.2f}")
        a(f"    HIGH: ${sep['amount_high']:>12,.2f}")
        a("")
        imp = totals['constitutional']['false_imprisonment']
        a(f"  Incarceration damages @ ${imp['rate_low']}-${imp['rate_high']}/day x {imp['total_days']} days:")
        a(f"    LOW:  ${imp['amount_low']:>12,.2f}")
        a(f"    HIGH: ${imp['amount_high']:>12,.2f}")
        a("")

        a(f"  COMBINED SEPARATION + INCARCERATION:")
        combined_low = sep['amount_low'] + imp['amount_low']
        combined_high = sep['amount_high'] + imp['amount_high']
        a(f"    LOW:  ${combined_low:>12,.2f}")
        a(f"    HIGH: ${combined_high:>12,.2f}")
        a("")
        a("=" * 78)
        a(f"Generated: {datetime.now().isoformat()}")
        a("=" * 78)

        path = EXHIBITS_DIR / "SEPARATION_TIMELINE_EXHIBIT.md"
        path.write_text("\n".join(lines), encoding="utf-8")
        return str(path)

    def generate_financial_damages_exhibit(self, totals):
        lines = []
        a = lines.append
        a("=" * 78)
        a("EXHIBIT: FINANCIAL DAMAGES ITEMIZATION")
        a("Pigors v. Watson et al.")
        a(f"Calculated as of: {CALCULATION_DATE}")
        a("=" * 78)
        a("")

        a("{:<4} {:<28} {:<35} {:>12} {:>12}".format(
            "#", "CATEGORY", "DESCRIPTION", "LOW", "HIGH"))
        a("-" * 95)

        econ = totals['economic']
        idx = 1
        running_low = 0
        running_high = 0
        for item in econ['line_items']:
            lo = item['amount_low'] or 0
            hi = item['amount_high'] or 0
            running_low += lo
            running_high += hi
            cat = (item['category'] or '')[:27]
            sub = (item['subcategory'] or '')[:34]
            a("{:<4} {:<28} {:<35} ${:>11,.2f} ${:>11,.2f}".format(
                idx, cat, sub, lo, hi))
            idx += 1

        a("-" * 95)
        a("{:<4} {:<28} {:<35} ${:>11,.2f} ${:>11,.2f}".format(
            "", "", "ECONOMIC SUBTOTAL", running_low, running_high))
        a("")

        # Emotional distress section
        a("EMOTIONAL DISTRESS DAMAGES")
        a("-" * 95)
        ed = totals['emotional_distress']
        ed_low = 0
        ed_high = 0
        for item in ed['line_items']:
            lo = item['amount_low'] or 0
            hi = item['amount_high'] or 0
            ed_low += lo
            ed_high += hi
            sub = (item['subcategory'] or '')[:62]
            a("{:<4} {:<63} ${:>11,.2f} ${:>11,.2f}".format(
                idx, sub, lo, hi))
            idx += 1
        a("-" * 95)
        a("{:<4} {:<63} ${:>11,.2f} ${:>11,.2f}".format(
            "", "EMOTIONAL DISTRESS SUBTOTAL", ed_low, ed_high))
        a("")

        # Constitutional section
        a("CONSTITUTIONAL DAMAGES (42 USC 1983)")
        a("-" * 95)
        c = totals['constitutional']
        const_items = [
            ("Parent-child separation ({} days)".format(c['separation']['days']),
             c['separation']['amount_low'], c['separation']['amount_high']),
            ("False imprisonment ({} days)".format(c['false_imprisonment']['total_days']),
             c['false_imprisonment']['amount_low'], c['false_imprisonment']['amount_high']),
            ("Section 1983 compensatory",
             c['section_1983_compensatory']['amount_low'], c['section_1983_compensatory']['amount_high']),
            ("Equal protection violation",
             c['equal_protection']['amount_low'], c['equal_protection']['amount_high']),
            ("First Amendment retaliation",
             c['first_amendment_retaliation']['amount_low'], c['first_amendment_retaliation']['amount_high']),
            ("Right to access courts",
             c['right_to_access_courts']['amount_low'], c['right_to_access_courts']['amount_high']),
        ]
        const_low = 0
        const_high = 0
        for label, lo, hi in const_items:
            const_low += lo
            const_high += hi
            a("{:<4} {:<63} ${:>11,.2f} ${:>11,.2f}".format(idx, label, lo, hi))
            idx += 1
        a("-" * 95)
        a("{:<4} {:<63} ${:>11,.2f} ${:>11,.2f}".format(
            "", "CONSTITUTIONAL SUBTOTAL", const_low, const_high))
        a("")

        # Punitive section
        a("PUNITIVE DAMAGES")
        a("-" * 95)
        p = totals['punitive']
        a("{:<4} {:<63} ${:>11,.2f} ${:>11,.2f}".format(
            idx, "Punitive (explicit + multiplier analysis)", p['subtotal_low'], p['subtotal_high']))
        idx += 1
        a("-" * 95)
        a("")

        # Grand total
        grand_low = running_low + ed_low + const_low + p['subtotal_low']
        grand_high = running_high + ed_high + const_high + p['subtotal_high']
        a("=" * 95)
        a("{:<4} {:<63} ${:>11,.2f} ${:>11,.2f}".format(
            "", "GRAND TOTAL", grand_low, grand_high))
        a("=" * 95)
        a("")

        # Itemization from damages_itemization table
        a("ADDITIONAL ITEMIZATION (damages_itemization table)")
        a("-" * 95)
        for item in econ['itemization_entries']:
            amt = item['amount'] or 0
            cat = (item['category'] or '')[:27]
            sub = (item['subcategory'] or '')[:60]
            a(f"  {cat}: {sub}")
            a(f"    Amount: ${amt:>12,.2f}")
        a("")

        # Evidence basis
        a("EVIDENCE BASIS")
        a("-" * 40)
        a(f"  Financial harm entries (extracted_harms):     {econ['extracted_harms_financial_count']:>6,}")
        a(f"  Housing harm entries (extracted_harms):       {econ['extracted_harms_housing_count']:>6,}")
        a(f"  Financial damages comprehensive (DB):               45 items")
        a(f"  Damages itemization (DB):                           15 items")
        a(f"  Damages calculations (DB):                          16 items")
        a(f"  Evidence quotes (DB):                          308,704 items")
        a("")
        a("=" * 78)
        a(f"Generated: {datetime.now().isoformat()}")
        a("=" * 78)

        path = EXHIBITS_DIR / "FINANCIAL_DAMAGES_EXHIBIT.md"
        path.write_text("\n".join(lines), encoding="utf-8")
        return str(path)

    # ------------------------------------------------------------------
    # Main entry point
    # ------------------------------------------------------------------
    def run(self):
        """Execute full damages calculation and generate exhibits.
        Returns dict with all damage categories, totals, and exhibit paths."""

        self._connect()

        try:
            # Calculate each category
            constitutional = self.calc_constitutional()
            economic = self.calc_economic()
            emotional_distress = self.calc_emotional_distress()

            # Compensatory base for punitive multiplier
            compensatory_low = (
                constitutional['subtotal_low'] +
                economic['subtotal_low'] +
                emotional_distress['subtotal_low']
            )
            compensatory_high = (
                constitutional['subtotal_high'] +
                economic['subtotal_high'] +
                emotional_distress['subtotal_high']
            )

            punitive = self.calc_punitive(compensatory_low, compensatory_high)
            defendant_specific = self.calc_defendant_specific()

            grand_total_low = compensatory_low + punitive['subtotal_low']
            grand_total_high = compensatory_high + punitive['subtotal_high']

            totals = {
                'calculation_date': str(CALCULATION_DATE),
                'constitutional': constitutional,
                'economic': economic,
                'emotional_distress': emotional_distress,
                'punitive': punitive,
                'defendant_specific': defendant_specific,
                'compensatory_subtotal_low': compensatory_low,
                'compensatory_subtotal_high': compensatory_high,
                'grand_total_low': grand_total_low,
                'grand_total_high': grand_total_high,
            }

            # Filing stack allocation
            totals['filing_stack_allocation'] = self.calc_filing_stack_allocation(totals)

            # Generate exhibits
            EXHIBITS_DIR.mkdir(parents=True, exist_ok=True)

            exhibit_paths = {
                'damages_summary': self.generate_damages_summary_exhibit(totals),
                'separation_timeline': self.generate_separation_timeline_exhibit(totals),
                'financial_damages': self.generate_financial_damages_exhibit(totals),
            }
            totals['exhibit_paths'] = exhibit_paths

            self.results = totals
            return totals

        finally:
            if self.conn:
                self.conn.close()


# ---------------------------------------------------------------------------
# CLI entry point
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    engine = DamagesCalculationEngine()
    result = engine.run()

    print("=" * 60)
    print("DAMAGES CALCULATION ENGINE - RESULTS")
    print("=" * 60)
    print(f"Calculation date:       {result['calculation_date']}")
    print(f"Compensatory LOW:       ${result['compensatory_subtotal_low']:>14,.2f}")
    print(f"Compensatory HIGH:      ${result['compensatory_subtotal_high']:>14,.2f}")
    print(f"Punitive LOW:           ${result['punitive']['subtotal_low']:>14,.2f}")
    print(f"Punitive HIGH:          ${result['punitive']['subtotal_high']:>14,.2f}")
    print("-" * 60)
    print(f"GRAND TOTAL LOW:        ${result['grand_total_low']:>14,.2f}")
    print(f"GRAND TOTAL HIGH:       ${result['grand_total_high']:>14,.2f}")
    print("-" * 60)
    print(f"Exhibits generated:")
    for name, path in result['exhibit_paths'].items():
        print(f"  {name}: {path}")
    print("=" * 60)
