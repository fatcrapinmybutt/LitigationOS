"""
skill_deadline_sentinel.py — Litigation Deadline Sentinel Skill
Tracks ALL litigation deadlines, calculates SOL windows, generates dashboards.
"""
import sqlite3, sys, json, re, os
from datetime import datetime, date, timedelta
sys.stdout.reconfigure(encoding='utf-8')

DB = r"C:\Users\andre\LitigationOS\litigation_context.db"
TODAY = date.today()

def _connect():
    conn = sqlite3.connect(DB, timeout=120)
    conn.execute("PRAGMA busy_timeout=60000")
    conn.execute("PRAGMA journal_mode=WAL")
    conn.row_factory = sqlite3.Row
    return conn

def _init_table():
    """Create litigation_deadlines table if it doesn't exist."""
    conn = _connect()
    conn.executescript("""
    CREATE TABLE IF NOT EXISTS litigation_deadlines (
        deadline_id   TEXT PRIMARY KEY,
        case_name     TEXT NOT NULL,
        court         TEXT,
        filing_type   TEXT,
        due_date      TEXT,
        days_remaining INTEGER,
        priority      TEXT DEFAULT 'MEDIUM' CHECK(priority IN ('CRITICAL','HIGH','MEDIUM','LOW')),
        status        TEXT DEFAULT 'upcoming' CHECK(status IN ('upcoming','overdue','filed','satisfied','waived','tbd')),
        basis         TEXT,
        authority     TEXT,
        notes         TEXT,
        created_at    TEXT DEFAULT (datetime('now')),
        updated_at    TEXT DEFAULT (datetime('now'))
    );
    """)
    conn.commit()
    conn.close()

def _calc_days(due_date_str):
    """Calculate days remaining from today to due date."""
    if not due_date_str or due_date_str in ('TBD', 'N/A', 'ASAP'):
        return None
    try:
        due = datetime.strptime(due_date_str, '%Y-%m-%d').date()
        return (due - TODAY).days
    except:
        return None

# ─── SOL Reference Table ───
SOL_TABLE = {
    'michigan_tort':          {'years': 3, 'statute': 'MCL 600.5805(2)', 'note': 'General personal injury'},
    'michigan_defamation':    {'years': 1, 'statute': 'MCL 600.5805(2)', 'note': 'Defamation/libel/slander'},
    'michigan_fraud':         {'years': 6, 'statute': 'MCL 600.5813', 'note': 'Fraud'},
    'michigan_rico':          {'years': 5, 'statute': 'MCL 750.159j', 'note': 'Michigan RICO'},
    'michigan_mhca':          {'years': 3, 'statute': 'MCL 333.20201', 'note': 'Michigan Housing Code Act violations'},
    'michigan_truth_in_renting': {'years': 6, 'statute': 'MCL 554.636', 'note': 'Truth in Renting (general contract period)'},
    'michigan_security_deposit': {'years': 6, 'statute': 'MCL 554.613', 'note': 'Security Deposit Act'},
    'michigan_consumer_protection': {'years': 6, 'statute': 'MCL 445.911', 'note': 'Michigan Consumer Protection Act'},
    'michigan_contract':      {'years': 6, 'statute': 'MCL 600.5807(8)', 'note': 'Written contract'},
    'michigan_property_damage': {'years': 3, 'statute': 'MCL 600.5805(2)', 'note': 'Property damage'},
    'michigan_wrongful_eviction': {'years': 3, 'statute': 'MCL 600.5805(2)', 'note': 'Wrongful eviction'},
    'michigan_retaliatory_eviction': {'years': 3, 'statute': 'MCL 600.5720', 'note': 'Retaliatory eviction'},
    'federal_1983':           {'years': 3, 'statute': '42 USC 1983 / MCL 600.5805', 'note': 'Federal civil rights (borrows MI SOL)'},
    'federal_1985':           {'years': 3, 'statute': '42 USC 1985', 'note': 'Civil rights conspiracy'},
    'michigan_perjury':       {'years': 6, 'statute': 'MCL 767.24', 'note': 'Criminal perjury (no private SOL)'},
    'michigan_abuse_of_process': {'years': 3, 'statute': 'MCL 600.5805(2)', 'note': 'Abuse of process'},
    'michigan_iied':          {'years': 3, 'statute': 'MCL 600.5805(2)', 'note': 'Intentional infliction of emotional distress'},
}

# ─────────────────────────────────────────────
# get_critical_deadlines() — All deadlines sorted by urgency
# ─────────────────────────────────────────────
def get_critical_deadlines() -> list[dict]:
    """Get all deadlines sorted by urgency (overdue first, then by days remaining)."""
    conn = _connect()
    rows = conn.execute("""
        SELECT * FROM litigation_deadlines
        ORDER BY
            CASE status WHEN 'overdue' THEN 0 WHEN 'upcoming' THEN 1 WHEN 'tbd' THEN 2 ELSE 3 END,
            CASE WHEN days_remaining IS NULL THEN 9999 ELSE days_remaining END ASC
    """).fetchall()
    conn.close()
    results = []
    for r in rows:
        d = dict(r)
        # Recalculate days_remaining live
        d['days_remaining'] = _calc_days(d['due_date'])
        if d['days_remaining'] is not None and d['days_remaining'] < 0 and d['status'] == 'upcoming':
            d['status'] = 'overdue'
        results.append(d)
    return results

# ─────────────────────────────────────────────
# days_until(case_name) — Countdown for specific case
# ─────────────────────────────────────────────
def days_until(case_name: str) -> list[dict]:
    """Get countdown for all deadlines related to a specific case."""
    conn = _connect()
    rows = conn.execute("""
        SELECT * FROM litigation_deadlines
        WHERE case_name LIKE ? OR deadline_id LIKE ?
        ORDER BY due_date
    """, (f"%{case_name}%", f"%{case_name}%")).fetchall()
    conn.close()
    results = []
    for r in rows:
        d = dict(r)
        d['days_remaining'] = _calc_days(d['due_date'])
        if d['days_remaining'] is not None:
            if d['days_remaining'] < 0:
                d['urgency'] = f"OVERDUE by {abs(d['days_remaining'])} days"
            elif d['days_remaining'] == 0:
                d['urgency'] = "DUE TODAY"
            elif d['days_remaining'] <= 7:
                d['urgency'] = f"DUE IN {d['days_remaining']} DAYS — CRITICAL"
            elif d['days_remaining'] <= 30:
                d['urgency'] = f"Due in {d['days_remaining']} days — HIGH"
            else:
                d['urgency'] = f"Due in {d['days_remaining']} days"
        else:
            d['urgency'] = 'No fixed deadline'
        results.append(d)
    return results

# ─────────────────────────────────────────────
# check_sol(cause_of_action, incident_date) — SOL analysis
# ─────────────────────────────────────────────
def check_sol(cause_of_action: str, incident_date: str) -> dict:
    """Check statute of limitations for a cause of action from an incident date.
    
    cause_of_action: key from SOL_TABLE or descriptive text
    incident_date: ISO date string (YYYY-MM-DD)
    """
    # Find matching SOL entry
    coa_lower = cause_of_action.lower().replace(' ', '_')
    sol_entry = SOL_TABLE.get(coa_lower)
    
    if not sol_entry:
        # Try fuzzy match
        for key, val in SOL_TABLE.items():
            if coa_lower in key or key in coa_lower:
                sol_entry = val
                break
            # Check note field
            if coa_lower.replace('_', ' ') in val['note'].lower():
                sol_entry = val
                break
    
    if not sol_entry:
        return {
            'cause_of_action': cause_of_action,
            'incident_date': incident_date,
            'status': 'UNKNOWN',
            'message': f'No SOL entry found for "{cause_of_action}". Known types: {", ".join(SOL_TABLE.keys())}'
        }
    
    try:
        incident = datetime.strptime(incident_date, '%Y-%m-%d').date()
    except ValueError:
        return {'error': f'Invalid date format: {incident_date}. Use YYYY-MM-DD.'}
    
    expiration = date(incident.year + sol_entry['years'], incident.month, incident.day)
    days_left = (expiration - TODAY).days
    
    if days_left < 0:
        status = 'EXPIRED'
        urgency = f'EXPIRED {abs(days_left)} days ago'
    elif days_left == 0:
        status = 'EXPIRES_TODAY'
        urgency = 'EXPIRES TODAY — FILE IMMEDIATELY'
    elif days_left <= 30:
        status = 'CRITICAL'
        urgency = f'Expires in {days_left} days — FILE NOW'
    elif days_left <= 90:
        status = 'HIGH'
        urgency = f'Expires in {days_left} days — prepare filing'
    elif days_left <= 365:
        status = 'MEDIUM'
        urgency = f'Expires in {days_left} days ({days_left // 30} months)'
    else:
        status = 'OK'
        urgency = f'Expires in {days_left} days ({days_left // 365}y {(days_left % 365) // 30}m)'
    
    return {
        'cause_of_action': cause_of_action,
        'incident_date': incident_date,
        'sol_years': sol_entry['years'],
        'statute': sol_entry['statute'],
        'note': sol_entry['note'],
        'expiration_date': expiration.isoformat(),
        'days_remaining': days_left,
        'status': status,
        'urgency': urgency,
        'today': TODAY.isoformat()
    }

# ─────────────────────────────────────────────
# generate_deadline_dashboard() — Markdown dashboard
# ─────────────────────────────────────────────
def generate_deadline_dashboard(output_path: str = None) -> str:
    """Generate a markdown deadline dashboard for all cases."""
    deadlines = get_critical_deadlines()
    
    lines = []
    lines.append(f"# ⚖️ LitigationOS Deadline Dashboard")
    lines.append(f"**Generated:** {datetime.now().strftime('%Y-%m-%d %H:%M')} | **Today:** {TODAY.isoformat()}")
    lines.append("")
    
    # Summary stats
    overdue = [d for d in deadlines if d.get('status') == 'overdue' or (d.get('days_remaining') is not None and d['days_remaining'] < 0)]
    critical = [d for d in deadlines if d.get('priority') == 'CRITICAL' and d.get('status') not in ('filed', 'satisfied')]
    upcoming_30 = [d for d in deadlines if d.get('days_remaining') is not None and 0 <= d['days_remaining'] <= 30 and d.get('status') not in ('filed', 'satisfied')]
    
    lines.append(f"## 📊 Summary")
    lines.append(f"| Metric | Count |")
    lines.append(f"|--------|-------|")
    lines.append(f"| 🔴 Overdue | **{len(overdue)}** |")
    lines.append(f"| 🟠 Critical Priority | **{len(critical)}** |")
    lines.append(f"| 🟡 Due within 30 days | **{len(upcoming_30)}** |")
    lines.append(f"| Total Active | **{len([d for d in deadlines if d.get('status') not in ('filed','satisfied','waived')])}** |")
    lines.append("")
    
    # Overdue section
    if overdue:
        lines.append(f"## 🔴 OVERDUE")
        lines.append(f"| Case | Filing | Due Date | Days Over | Priority | Authority |")
        lines.append(f"|------|--------|----------|-----------|----------|-----------|")
        for d in overdue:
            days = abs(d.get('days_remaining', 0)) if d.get('days_remaining') is not None else '?'
            lines.append(f"| {d['case_name']} | {d.get('filing_type','')} | {d.get('due_date','')} | **{days}** | {d.get('priority','')} | {d.get('authority','')} |")
        lines.append("")
    
    # Critical section
    lines.append(f"## 🟠 CRITICAL & HIGH PRIORITY")
    lines.append(f"| Case | Filing | Due Date | Days Left | Priority | Court | Authority |")
    lines.append(f"|------|--------|----------|-----------|----------|-------|-----------|")
    for d in deadlines:
        if d.get('priority') in ('CRITICAL', 'HIGH') and d.get('status') not in ('filed', 'satisfied', 'waived', 'overdue'):
            days = d.get('days_remaining', '?')
            lines.append(f"| {d['case_name']} | {d.get('filing_type','')} | {d.get('due_date','')} | **{days}** | {d.get('priority','')} | {d.get('court','')} | {d.get('authority','')} |")
    lines.append("")
    
    # All deadlines
    lines.append(f"## 📋 All Active Deadlines")
    lines.append(f"| # | Case | Filing Type | Due Date | Days | Priority | Status | Notes |")
    lines.append(f"|---|------|-------------|----------|------|----------|--------|-------|")
    for i, d in enumerate(deadlines, 1):
        if d.get('status') in ('filed', 'satisfied', 'waived'):
            continue
        days = d.get('days_remaining', 'TBD')
        icon = '🔴' if (isinstance(days, int) and days < 0) else '🟠' if d.get('priority') == 'CRITICAL' else '🟡' if (isinstance(days, int) and days <= 30) else '🟢'
        notes = (d.get('notes', '') or '')[:60]
        lines.append(f"| {i} | {d['case_name']} | {d.get('filing_type','')} | {d.get('due_date','TBD')} | {days} | {icon} {d.get('priority','')} | {d.get('status','')} | {notes} |")
    lines.append("")
    
    # SOL Reference
    lines.append(f"## ⏳ Statute of Limitations Reference")
    lines.append(f"| Cause of Action | SOL | Statute | Note |")
    lines.append(f"|----------------|-----|---------|------|")
    for key, val in sorted(SOL_TABLE.items()):
        lines.append(f"| {key.replace('_',' ').title()} | {val['years']} yrs | {val['statute']} | {val['note']} |")
    lines.append("")
    
    dashboard = '\n'.join(lines)
    
    if output_path:
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(dashboard)
    
    return dashboard


# ─────────────────────────────────────────────
# CLI Interface
# ─────────────────────────────────────────────
if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Deadline Sentinel Skill")
    sub = parser.add_subparsers(dest='command')
    
    sub.add_parser('critical', help='Show all critical deadlines')
    
    p_days = sub.add_parser('days', help='Days until deadline for case')
    p_days.add_argument('case_name', help='Case name or ID')
    
    p_sol = sub.add_parser('sol', help='Check statute of limitations')
    p_sol.add_argument('cause', help='Cause of action')
    p_sol.add_argument('incident_date', help='Incident date (YYYY-MM-DD)')
    
    p_dash = sub.add_parser('dashboard', help='Generate deadline dashboard')
    p_dash.add_argument('--output', default=r'C:\Users\andre\LitigationOS\00_SYSTEM\deadline_dashboard.md')
    
    sub.add_parser('init', help='Initialize/populate deadline table')
    
    args = parser.parse_args()
    
    if args.command == 'init':
        _init_table()
        print("[OK] litigation_deadlines table ready")
    
    elif args.command == 'critical':
        deadlines = get_critical_deadlines()
        print(f"\n{'='*80}")
        print(f"  ⚖️  DEADLINE SENTINEL — Critical Deadlines Report")
        print(f"  Today: {TODAY.isoformat()}")
        print(f"{'='*80}\n")
        for d in deadlines:
            if d.get('status') in ('filed', 'satisfied', 'waived'):
                continue
            days = d.get('days_remaining', 'TBD')
            icon = '🔴' if (isinstance(days, int) and days < 0) else '🟠' if d.get('priority') == 'CRITICAL' else '🟡' if (isinstance(days, int) and days <= 30) else '🟢'
            print(f"  {icon} [{d.get('priority','?'):8s}] {d['case_name'][:30]:30s} | {d.get('filing_type',''):30s} | {d.get('due_date','TBD'):12s} | {days} days")
        print()
    
    elif args.command == 'days':
        results = days_until(args.case_name)
        print(f"\n{'='*70}")
        print(f"  Deadline Countdown — '{args.case_name}'")
        print(f"{'='*70}\n")
        if not results:
            print(f"  No deadlines found for '{args.case_name}'")
        for d in results:
            print(f"  ⏰ {d.get('filing_type',''):30s} | Due: {d.get('due_date','TBD'):12s} | {d.get('urgency','')}")
    
    elif args.command == 'sol':
        result = check_sol(args.cause, args.incident_date)
        print(f"\n{'='*70}")
        print(f"  SOL Analysis — {result.get('cause_of_action','')}")
        print(f"{'='*70}\n")
        for k, v in result.items():
            print(f"  {k:20s}: {v}")
    
    elif args.command == 'dashboard':
        _init_table()
        dashboard = generate_deadline_dashboard(args.output)
        print(f"[OK] Dashboard written to {args.output}")
        print(dashboard[:2000])
    
    else:
        parser.print_help()
