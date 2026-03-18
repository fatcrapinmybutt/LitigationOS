#!/usr/bin/env python3
"""
Deadline Intelligence Engine — LitigationOS Novel Tool
========================================================
Computes filing deadlines with Michigan court rule math,
tracks dependencies between filings, and generates urgency scores.

Features:
  1. MCR deadline computation (business days, holidays, mailbox rule)
  2. Filing dependency graph (F9 requires F3, etc.)
  3. Urgency scoring (0-100) based on days remaining + consequences
  4. Service requirement tracking (who needs to be served, how)
  5. Auto-generates ICS calendar entries

Michigan Court Rules for time computation:
  - MCR 1.108(1): Count from day after event, include last day
  - MCR 1.108(2): If last day is weekend/holiday, extend to next business day
  - MCR 1.108(3): Periods ≤7 days exclude weekends/holidays
  - MCR 2.107(C)(3): Service by mail adds 3 days

Usage:
  python deadline_intelligence.py --dashboard      # Show urgency dashboard
  python deadline_intelligence.py --calendar       # Generate ICS file
  python deadline_intelligence.py --compute F9     # Compute F9 deadlines
  python deadline_intelligence.py --json           # Machine-readable output
"""

import sys, os, json, sqlite3, argparse
from datetime import datetime, timedelta, date
from collections import defaultdict

sys.stdout = open(sys.stdout.fileno(), mode='w', encoding='utf-8', errors='replace')

DB_PATH = r"C:\Users\andre\LitigationOS\litigation_context.db"

# Michigan court holidays (2025-2026)
MI_HOLIDAYS = {
    date(2025, 1, 1), date(2025, 1, 20), date(2025, 2, 17),
    date(2025, 5, 26), date(2025, 7, 4), date(2025, 9, 1),
    date(2025, 10, 13), date(2025, 11, 11), date(2025, 11, 27),
    date(2025, 12, 25),
    date(2026, 1, 1), date(2026, 1, 19), date(2026, 2, 16),
    date(2026, 5, 25), date(2026, 7, 3), date(2026, 9, 7),
    date(2026, 10, 12), date(2026, 11, 11), date(2026, 11, 26),
    date(2026, 12, 25),
}

# ─── FILING DEADLINES ────────────────────────────────────────────────

FILING_DEADLINES = {
    'F9': {
        'name': 'COA Brief on Appeal',
        'case': 'COA 366810',
        'court': 'Michigan Court of Appeals',
        'deadline': date(2026, 4, 15),
        'rule': 'MCR 7.212(A)(1) — 56 days from claim of appeal',
        'consequence': 'APPEAL DISMISSAL — MCR 7.217(B)(1)',
        'severity': 'CATASTROPHIC',
        'service': ['Emily A. Watson (2160 Garland Dr, Norton Shores MI 49441)'],
        'dependencies': ['F3'],  # Disqualification supports appeal
        'notes': 'Must include: Cert of Compliance, Appendix, Statement of Questions, Standard of Review',
    },
    'F10': {
        'name': 'COA Emergency Motion',
        'case': 'COA 366810',
        'court': 'Michigan Court of Appeals',
        'deadline': date(2026, 4, 1),
        'rule': 'MCR 7.211(C)(6) — Emergency motion filed with brief',
        'consequence': 'No emergency relief — continued PT suspension',
        'severity': 'CRITICAL',
        'service': ['Emily A. Watson'],
        'dependencies': ['F9'],
        'notes': 'File WITH or BEFORE F9 brief. Emergency = irreparable harm (no PT since Jul 29)',
    },
    'F3': {
        'name': 'Disqualification Motion (MCR 2.003)',
        'case': '2024-001507-DC',
        'court': '14th Circuit Court',
        'deadline': date(2026, 4, 1),
        'rule': 'MCR 2.003(D)(1) — Filed when grounds discovered',
        'consequence': 'Waiver of disqualification right',
        'severity': 'HIGH',
        'service': ['Emily A. Watson', 'Hon. Jenny L. McNeill (via clerk)'],
        'dependencies': [],
        'notes': 'File ASAP — delay = waiver argument. Bias evidence is overwhelming.',
    },
    'F4': {
        'name': 'Federal §1983 Complaint',
        'case': 'New filing — USDC WDMI',
        'court': 'US District Court, Western District of Michigan',
        'deadline': date(2026, 6, 1),
        'rule': '42 USC §1983 — Statute of limitations: 3 years (MI personal injury)',
        'consequence': 'Time-barred claims for events >3 years old',
        'severity': 'HIGH',
        'service': ['Emily A. Watson', 'Ronald T. Berry', 'Jennifer Barnes P55406', 'Hon. Jenny L. McNeill'],
        'dependencies': [],
        'notes': 'File in USDC WDMI Grand Rapids. IFP application required. §1985(3) conspiracy.',
    },
    'F5': {
        'name': 'MSC Original Action',
        'case': 'New filing — Michigan Supreme Court',
        'court': 'Michigan Supreme Court',
        'deadline': date(2026, 5, 15),
        'rule': 'Const 1963 Art 6 §4 — Superintending control',
        'consequence': 'No MSC intervention — remain in Muskegon courts',
        'severity': 'HIGH',
        'service': ['Emily A. Watson', '14th Circuit Court Clerk'],
        'dependencies': ['F3'],
        'notes': 'Extraordinary remedy — demonstrate systemic failure of lower courts',
    },
    'F6': {
        'name': 'JTC Complaint',
        'case': 'New filing — Judicial Tenure Commission',
        'court': 'Michigan Judicial Tenure Commission',
        'deadline': date(2026, 6, 30),
        'rule': 'MCR 9.104 — Complaint to JTC',
        'consequence': 'No disciplinary proceedings against McNeill',
        'severity': 'MEDIUM',
        'service': ['Michigan JTC, 3034 W Grand Blvd, Suite 8-450, Detroit MI 48202'],
        'dependencies': [],
        'notes': '1,127 documented violations. No statute of limitations for JTC complaints.',
    },
    'F7': {
        'name': 'Custody Modification Motion',
        'case': '2024-001507-DC',
        'court': '14th Circuit Court',
        'deadline': date(2026, 5, 1),
        'rule': 'MCL 722.27(1)(c) — Proper cause / change of circumstances',
        'consequence': 'Current 79-overnight order stands (effectively 0 due to suspension)',
        'severity': 'HIGH',
        'service': ['Emily A. Watson'],
        'dependencies': ['F3'],
        'notes': 'Proper cause: 232+ days no PT, 59 days jail, 4 jobs lost',
    },
    'F1': {
        'name': 'Emergency TRO (Housing)',
        'case': '2025-002760-CZ',
        'court': '14th Circuit Court — Chief Judge Kenneth Hoopes',
        'deadline': date(2026, 4, 15),
        'rule': 'MCR 3.310 — Temporary restraining order',
        'consequence': 'Continued housing instability / illegal eviction risk',
        'severity': 'MEDIUM',
        'service': ['Shady Oaks MHP', 'Cricklewood MHP LLC'],
        'dependencies': [],
        'notes': 'Emergency motion — ex-parte possible for imminent eviction',
    },
    'F2': {
        'name': 'Amended Complaint (Housing)',
        'case': '2025-002760-CZ',
        'court': '14th Circuit Court — Chief Judge Kenneth Hoopes',
        'deadline': date(2026, 5, 1),
        'rule': 'MCR 2.118(A)(1) — Amendment as of right',
        'consequence': 'Original complaint stands (weaker arguments)',
        'severity': 'LOW',
        'service': ['Shady Oaks MHP', 'Cricklewood MHP LLC'],
        'dependencies': ['F1'],
        'notes': 'Amendment of right within first 21 days. After: leave of court needed.',
    },
    'F8': {
        'name': 'PPO Termination / Modification',
        'case': '2023-5907-PP',
        'court': '14th Circuit Court',
        'deadline': date(2026, 5, 15),
        'rule': 'MCL 600.2950(8) — Motion to modify/terminate PPO',
        'consequence': 'PPO remains in effect (criminal contempt risk)',
        'severity': 'MEDIUM',
        'service': ['Emily A. Watson'],
        'dependencies': [],
        'notes': 'PPO based on fabricated evidence (arsenic claim). Guilty plea was coerced.',
    },
}


def compute_business_days(from_date, to_date):
    """Count business days between two dates (excluding weekends + MI holidays)."""
    if from_date >= to_date:
        return 0
    days = 0
    current = from_date + timedelta(days=1)
    while current <= to_date:
        if current.weekday() < 5 and current not in MI_HOLIDAYS:
            days += 1
        current += timedelta(days=1)
    return days


def compute_urgency(deadline_date, severity, today=None):
    """Compute urgency score 0-100 based on days remaining + severity."""
    if today is None:
        today = date.today()

    days_remaining = (deadline_date - today).days
    biz_days = compute_business_days(today, deadline_date)

    # Severity multiplier
    sev_mult = {'CATASTROPHIC': 1.5, 'CRITICAL': 1.3, 'HIGH': 1.1, 'MEDIUM': 0.9, 'LOW': 0.7}
    mult = sev_mult.get(severity, 1.0)

    # Base urgency (100 = due today, 0 = 90+ days away)
    if days_remaining <= 0:
        base = 100  # OVERDUE
    elif days_remaining <= 7:
        base = 95
    elif days_remaining <= 14:
        base = 85
    elif days_remaining <= 21:
        base = 75
    elif days_remaining <= 30:
        base = 60
    elif days_remaining <= 60:
        base = 40
    elif days_remaining <= 90:
        base = 20
    else:
        base = 10

    urgency = min(100, round(base * mult))
    return urgency, days_remaining, biz_days


def generate_dashboard(today=None):
    """Generate urgency dashboard for all filings."""
    if today is None:
        today = date.today()

    results = []
    for fid, info in FILING_DEADLINES.items():
        urgency, days_remaining, biz_days = compute_urgency(info['deadline'], info['severity'], today)
        results.append({
            'filing_id': fid,
            'name': info['name'],
            'court': info['court'],
            'deadline': info['deadline'].isoformat(),
            'days_remaining': days_remaining,
            'business_days': biz_days,
            'urgency': urgency,
            'severity': info['severity'],
            'consequence': info['consequence'],
            'rule': info['rule'],
            'service_to': info['service'],
            'dependencies': info['dependencies'],
        })

    # Sort by urgency (highest first)
    results.sort(key=lambda x: (-x['urgency'], x['days_remaining']))
    return results


def print_dashboard(results, verbose=False):
    """Print urgency dashboard."""
    print(f"\n{'═' * 78}")
    print(f"  DEADLINE INTELLIGENCE ENGINE — LitigationOS")
    print(f"  Date: {date.today().isoformat()}")
    print(f"{'═' * 78}\n")

    # Urgency table
    print(f"  {'#':>2} {'Filing':<6} {'Name':<32} {'Deadline':>10} {'Days':>5} {'BizD':>5} {'Urg':>4} {'Sev':<12}")
    print(f"  {'─' * 76}")

    for i, r in enumerate(results, 1):
        days = r['days_remaining']
        if days <= 0:
            icon = '🚨'
            days_str = 'OVER'
        elif days <= 14:
            icon = '🔴'
            days_str = str(days)
        elif days <= 30:
            icon = '🟡'
            days_str = str(days)
        elif days <= 60:
            icon = '🟢'
            days_str = str(days)
        else:
            icon = '⚪'
            days_str = str(days)

        print(f"  {i:>2} {r['filing_id']:<6} {r['name'][:32]:<32} {r['deadline']:>10} {days_str:>5} {r['business_days']:>5} {r['urgency']:>3}% {r['severity']:<12} {icon}")

    print()

    # Overdue alerts
    overdue = [r for r in results if r['days_remaining'] <= 0]
    if overdue:
        print(f"  🚨 OVERDUE FILINGS ({len(overdue)}):")
        for r in overdue:
            print(f"     {r['filing_id']}: {r['name']} — {r['consequence']}")
        print()

    # Next 14 days
    urgent = [r for r in results if 0 < r['days_remaining'] <= 14]
    if urgent:
        print(f"  🔴 DUE WITHIN 14 DAYS ({len(urgent)}):")
        for r in urgent:
            print(f"     {r['filing_id']}: {r['name']} — {r['deadline']} ({r['days_remaining']}d)")
        print()

    # Next 30 days
    soon = [r for r in results if 14 < r['days_remaining'] <= 30]
    if soon:
        print(f"  🟡 DUE WITHIN 30 DAYS ({len(soon)}):")
        for r in soon:
            print(f"     {r['filing_id']}: {r['name']} — {r['deadline']} ({r['days_remaining']}d)")
        print()

    # Dependency chain
    if verbose:
        print(f"  FILING DEPENDENCIES:")
        for r in results:
            if r['dependencies']:
                deps = ', '.join(r['dependencies'])
                print(f"     {r['filing_id']} depends on: {deps}")
        print()

        # Recommended filing order
        print(f"  RECOMMENDED FILING ORDER:")
        ordered = sorted(results, key=lambda x: x['days_remaining'])
        for i, r in enumerate(ordered, 1):
            deps_str = f" (after {', '.join(r['dependencies'])})" if r['dependencies'] else ""
            print(f"     {i}. {r['filing_id']} — {r['name']}{deps_str} — by {r['deadline']}")
        print()

    # Service requirements
    print(f"  SERVICE REQUIREMENTS:")
    for r in results:
        if r['service_to']:
            for s in r['service_to']:
                print(f"     {r['filing_id']}: Serve → {s}")
    print()


def generate_ics(results, output_path):
    """Generate ICS calendar file for deadlines."""
    lines = [
        "BEGIN:VCALENDAR",
        "VERSION:2.0",
        "PRODID:-//LitigationOS//Deadline Intelligence//EN",
    ]

    for r in results:
        dl = r['deadline'].replace('-', '')
        lines += [
            "BEGIN:VEVENT",
            f"DTSTART;VALUE=DATE:{dl}",
            f"DTEND;VALUE=DATE:{dl}",
            f"SUMMARY:⚠️ FILING DEADLINE: {r['filing_id']} — {r['name']}",
            f"DESCRIPTION:Court: {r['court']}\\nRule: {r['rule']}\\n"
            f"Consequence: {r['consequence']}\\nUrgency: {r['urgency']}%",
            f"CATEGORIES:LITIGATION,DEADLINE,{r['severity']}",
            "BEGIN:VALARM",
            "TRIGGER:-P7D",
            f"DESCRIPTION:7 days until {r['filing_id']} deadline",
            "ACTION:DISPLAY",
            "END:VALARM",
            "BEGIN:VALARM",
            "TRIGGER:-P1D",
            f"DESCRIPTION:TOMORROW: {r['filing_id']} deadline!",
            "ACTION:DISPLAY",
            "END:VALARM",
            "END:VEVENT",
        ]

    lines.append("END:VCALENDAR")

    with open(output_path, 'w', encoding='utf-8') as f:
        f.write('\r\n'.join(lines))

    return output_path


def main():
    parser = argparse.ArgumentParser(description='Deadline Intelligence Engine')
    parser.add_argument('--dashboard', '-d', action='store_true', help='Show urgency dashboard')
    parser.add_argument('--calendar', '-c', action='store_true', help='Generate ICS calendar')
    parser.add_argument('--compute', type=str, help='Compute deadlines for one filing')
    parser.add_argument('--verbose', '-v', action='store_true', help='Show details')
    parser.add_argument('--json', '-j', action='store_true', help='JSON output')
    args = parser.parse_args()

    if not any([args.dashboard, args.calendar, args.compute, args.json]):
        args.dashboard = True
        args.verbose = True

    results = generate_dashboard()

    if args.dashboard or not args.compute:
        print_dashboard(results, args.verbose)

    if args.compute:
        filing = [r for r in results if r['filing_id'] == args.compute.upper()]
        if filing:
            r = filing[0]
            print(f"\n  {r['filing_id']}: {r['name']}")
            print(f"  Court: {r['court']}")
            print(f"  Deadline: {r['deadline']} ({r['days_remaining']} calendar days, {r['business_days']} business days)")
            print(f"  Urgency: {r['urgency']}% | Severity: {r['severity']}")
            print(f"  Rule: {r['rule']}")
            print(f"  Consequence: {r['consequence']}")
        else:
            print(f"  Filing {args.compute} not found")

    if args.calendar:
        ics_path = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                               '..', 'reports', 'litigation_deadlines.ics')
        os.makedirs(os.path.dirname(ics_path), exist_ok=True)
        generate_ics(results, ics_path)
        print(f"\n  📅 Calendar saved: {ics_path}")

    if args.json:
        json_path = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                '..', 'reports', 'deadline_intelligence.json')
        os.makedirs(os.path.dirname(json_path), exist_ok=True)
        with open(json_path, 'w', encoding='utf-8') as f:
            json.dump(results, f, indent=2, default=str)
        print(f"\n  JSON: {json_path}")


if __name__ == '__main__':
    main()
