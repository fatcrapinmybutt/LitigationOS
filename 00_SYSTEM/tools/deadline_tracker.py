#!/usr/bin/env python3
"""
Tool #67 — Active Deadline Tracker
======================================
Tracks ALL litigation deadlines across all 10 filings and 6 courts.
Calculates days remaining, urgency level, and next actions.

Categories:
- Filing deadlines (when documents must be filed)
- Service deadlines (when parties must be served)
- Response deadlines (when opposing party must respond)
- Hearing deadlines (when hearings are scheduled)
- Statutory deadlines (MCR time limits)
"""
import sys, json
from pathlib import Path
from datetime import datetime, timedelta

sys.stdout = open(sys.stdout.fileno(), mode='w', encoding='utf-8', errors='replace')

REPO = Path(r"C:\Users\andre\LitigationOS")
REPORTS_DIR = REPO / "00_SYSTEM" / "reports"

TODAY = datetime.now()

# Known deadlines and time-sensitive items
# NOTE: Many dates are relative to filing date (TBD) — marked with RELATIVE
DEADLINES = [
    # Pre-filing preparation deadlines
    {
        'id': 'PREP-01',
        'filing': 'ALL',
        'deadline': 'IMMEDIATE',
        'days_from_now': 0,
        'description': 'Register for MiFILE (mifile.courts.michigan.gov)',
        'urgency': '🔴 CRITICAL',
        'category': 'Preparation',
        'notes': 'Cannot e-file without registration. May take 1-3 business days.',
    },
    {
        'id': 'PREP-02',
        'filing': 'F4',
        'deadline': 'IMMEDIATE',
        'days_from_now': 0,
        'description': 'Register for PACER/CM-ECF (pacer.uscourts.gov)',
        'urgency': '🔴 CRITICAL',
        'category': 'Preparation',
        'notes': 'Required for federal e-filing. Registration may take 1-5 business days.',
    },
    {
        'id': 'PREP-03',
        'filing': 'ALL',
        'deadline': 'IMMEDIATE',
        'days_from_now': 0,
        'description': 'Review and sign all 10 affidavits (sworn under oath)',
        'urgency': '🔴 CRITICAL',
        'category': 'Preparation',
        'notes': 'MUST be notarized or signed under penalty of perjury. Cannot file without signed affidavit.',
    },
    {
        'id': 'PREP-04',
        'filing': 'F1/F4/F5/F8',
        'deadline': 'BEFORE FILING',
        'days_from_now': 0,
        'description': 'Complete IFP financial affidavit (MC 20 / AO 240)',
        'urgency': '🟡 HIGH',
        'category': 'Preparation',
        'notes': 'Need income, expenses, bank balances, assets. See 09_IFP_APPLICATION.md in each package.',
    },
    
    # Relative deadlines (triggered by filing date)
    {
        'id': 'F1-SVC',
        'filing': 'F1',
        'deadline': 'RELATIVE: 9 days before hearing',
        'days_from_now': None,
        'description': 'Serve Emily Watson with F1 Emergency Motion',
        'urgency': '🟡 HIGH',
        'category': 'Service',
        'notes': 'MCR 2.119(C) — motion must be served 9 days before hearing. Court may shorten for emergency.',
    },
    {
        'id': 'F2-SVC',
        'filing': 'F2',
        'deadline': 'RELATIVE: 91 days from filing',
        'days_from_now': None,
        'description': 'Serve Emily Watson with F2 Fraud Complaint + Summons',
        'urgency': '🟡 HIGH',
        'category': 'Service',
        'notes': 'MCR 2.102(D) — summons expires after 91 days. Must perfect service before then.',
    },
    {
        'id': 'F3-RESP',
        'filing': 'F3',
        'deadline': 'RELATIVE: 14 days from service',
        'days_from_now': None,
        'description': 'Judge McNeill response to disqualification motion',
        'urgency': '🟡 HIGH',
        'category': 'Response',
        'notes': 'MCR 2.003(D)(3) — if judge does not recuse within 14 days, motion goes to chief judge.',
    },
    {
        'id': 'F4-SVC',
        'filing': 'F4',
        'deadline': 'RELATIVE: 90 days from filing',
        'days_from_now': None,
        'description': 'Serve ALL defendants in federal §1983 case',
        'urgency': '🔴 CRITICAL',
        'category': 'Service',
        'notes': 'FRCP 4(m) — if not served within 90 days, case may be dismissed. Request US Marshals if IFP.',
    },
    {
        'id': 'F4-RESP',
        'filing': 'F4',
        'deadline': 'RELATIVE: 21 days from service',
        'days_from_now': None,
        'description': 'Defendants must respond to federal complaint',
        'urgency': '🟡 HIGH',
        'category': 'Response',
        'notes': 'FRCP 12(a)(1) — 21 days to answer or file motion to dismiss. State actors get 60 days (FRCP 12(a)(2)).',
    },
    {
        'id': 'F9-BRIEF',
        'filing': 'F9',
        'deadline': 'CHECK WITH COA CLERK',
        'days_from_now': None,
        'description': 'COA 366810 — Appellant brief due date',
        'urgency': '🔴 CRITICAL',
        'category': 'Filing',
        'notes': 'COA 366810 already docketed. Brief may already be due. CALL COA CLERK: (517) 373-0786 to confirm deadline.',
    },
    {
        'id': 'F9-SETTLE',
        'filing': 'F9',
        'deadline': 'RELATIVE: 14 days before brief',
        'days_from_now': None,
        'description': 'Serve proposed settled statement on Emily Watson',
        'urgency': '🟡 HIGH',
        'category': 'Service',
        'notes': 'MCR 7.210(B)(2)(b) — opposing party has 14 days to object after service.',
    },
    
    # Statutory limits
    {
        'id': 'STAT-01',
        'filing': 'F2',
        'deadline': 'MCR 2.612(C)(1)(c): 1 year from judgment',
        'days_from_now': None,
        'description': 'Fraud relief from judgment — 1 year limit',
        'urgency': '🟠 MEDIUM',
        'category': 'Statutory',
        'notes': 'MCR 2.612(C)(1)(c) has 1-year limit. BUT MCR 2.612(C)(3) independent fraud action has NO time limit. Use (C)(3).',
    },
    {
        'id': 'STAT-02',
        'filing': 'F4',
        'deadline': '3 years from violation (42 USC §1983)',
        'days_from_now': None,
        'description': 'Federal §1983 statute of limitations',
        'urgency': '🟠 MEDIUM',
        'category': 'Statutory',
        'notes': 'Michigan borrows 3-year personal injury SOL for §1983. Continuing violations doctrine extends if pattern ongoing.',
    },
]

def main():
    print("=" * 70)
    print("ACTIVE DEADLINE TRACKER — Tool #67")
    print(f"Date: {TODAY.strftime('%Y-%m-%d')}")
    print("=" * 70)
    
    # Sort by urgency
    urgency_order = {'🔴 CRITICAL': 0, '🟡 HIGH': 1, '🟠 MEDIUM': 2, '🟢 LOW': 3}
    sorted_deadlines = sorted(DEADLINES, key=lambda d: urgency_order.get(d['urgency'], 9))
    
    lines = [
        "# ⏰ ACTIVE DEADLINE TRACKER",
        f"*Generated: {TODAY.strftime('%Y-%m-%d %H:%M')}*\n",
        "---\n",
        "## 🔴 IMMEDIATE ACTION REQUIRED",
        "| # | Filing | Deadline | Action | Notes |",
        "|---|--------|----------|--------|-------|",
    ]
    
    critical = [d for d in sorted_deadlines if d['urgency'] == '🔴 CRITICAL']
    high = [d for d in sorted_deadlines if d['urgency'] == '🟡 HIGH']
    medium = [d for d in sorted_deadlines if d['urgency'] == '🟠 MEDIUM']
    
    for d in critical:
        lines.append(f"| {d['id']} | {d['filing']} | **{d['deadline']}** | {d['description'][:50]} | {d['notes'][:40]} |")
        print(f"  🔴 {d['id']}: {d['description'][:60]}")
    
    lines.extend([
        "",
        "## 🟡 HIGH PRIORITY (Triggered by Filing)",
        "| # | Filing | Deadline | Action | Notes |",
        "|---|--------|----------|--------|-------|",
    ])
    
    for d in high:
        lines.append(f"| {d['id']} | {d['filing']} | {d['deadline']} | {d['description'][:50]} | {d['notes'][:40]} |")
        print(f"  🟡 {d['id']}: {d['description'][:60]}")
    
    lines.extend([
        "",
        "## 🟠 STATUTORY LIMITS",
        "| # | Filing | Deadline | Action | Notes |",
        "|---|--------|----------|--------|-------|",
    ])
    
    for d in medium:
        lines.append(f"| {d['id']} | {d['filing']} | {d['deadline']} | {d['description'][:50]} | {d['notes'][:40]} |")
    
    lines.extend([
        "",
        "---",
        "## Andrew's Immediate Checklist",
        "1. 🔴 **Register for MiFILE** — mifile.courts.michigan.gov (1-3 business days)",
        "2. 🔴 **Register for PACER** — pacer.uscourts.gov (1-5 business days)",
        "3. 🔴 **Sign ALL 10 affidavits** — notarize or sign under penalty of perjury",
        "4. 🔴 **Call COA Clerk** — (517) 373-0786 — confirm 366810 brief deadline",
        "5. 🟡 **Complete IFP financial data** — income, expenses, bank balances",
        "6. 🟡 **Get Ronald Berry's address** — needed for F4 service",
        "7. 🟡 **Get LARA addresses** — Shady Oaks/Cricklewood registered agents",
        "",
        f"*{len(DEADLINES)} deadlines tracked across 10 filings*",
        f"*{len(critical)} critical, {len(high)} high, {len(medium)} medium*",
    ])
    
    md_path = REPORTS_DIR / "DEADLINE_TRACKER.md"
    md_path.write_text('\n'.join(lines), encoding='utf-8')
    
    json_path = REPORTS_DIR / "deadline_tracker.json"
    json_path.write_text(json.dumps({
        'generated': TODAY.isoformat(),
        'tool': 'Active Deadline Tracker (#67)',
        'total_deadlines': len(DEADLINES),
        'critical': len(critical),
        'high': len(high),
        'medium': len(medium),
        'deadlines': DEADLINES,
    }, indent=2, default=str), encoding='utf-8')
    
    print(f"\n✅ {len(DEADLINES)} deadlines tracked")
    print(f"   🔴 {len(critical)} critical | 🟡 {len(high)} high | 🟠 {len(medium)} medium")
    print(f"   Reports: {md_path.name}, {json_path.name}")

if __name__ == '__main__':
    main()
