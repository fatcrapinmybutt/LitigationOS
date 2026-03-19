#!/usr/bin/env python3
"""
Deadline Alert Engine — LitigationOS
=====================================
Monitors litigation deadlines and statute of limitations, generates urgency-coded
alerts and daily briefing reports.

Usage:
    python deadline_alert_engine.py              # Show all deadlines
    python deadline_alert_engine.py --urgent     # Show RED + YELLOW only
    python deadline_alert_engine.py --report     # Generate markdown report
    python deadline_alert_engine.py --update     # Recalculate days_remaining in DB
"""
import sys
import os
import sqlite3
import argparse
from datetime import datetime, date

sys.stdout.reconfigure(encoding='utf-8')

# Reference date per spec
REFERENCE_DATE = date(2026, 3, 4)

DB = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', 'litigation_context.db')
REPORT_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'deadline_dashboard.md')

# Try rich, fall back to plain text
try:
    from rich.console import Console
    from rich.table import Table
    from rich.panel import Panel
    from rich.text import Text
    HAS_RICH = True
except ImportError:
    HAS_RICH = False

# ─── Urgency helpers ───────────────────────────────────────────────

def classify_urgency(days_remaining):
    """Return (label, color) tuple based on days remaining."""
    if days_remaining < 0:
        return 'OVERDUE', 'bright_red'
    elif days_remaining <= 14:
        return 'RED', 'red'
    elif days_remaining <= 30:
        return 'YELLOW', 'yellow'
    else:
        return 'GREEN', 'green'

def urgency_emoji(label):
    return {'OVERDUE': '🚨', 'RED': '🔴', 'YELLOW': '🟡', 'GREEN': '🟢'}.get(label, '⚪')

# ─── Database helpers ──────────────────────────────────────────────

def get_connection():
    conn = sqlite3.connect(DB, timeout=120)
    conn.execute("PRAGMA busy_timeout = 60000")
    conn.execute("PRAGMA journal_mode = WAL")
    conn.row_factory = sqlite3.Row
    return conn

def load_deadlines(conn):
    """Load all deadlines with recalculated days_remaining."""
    cur = conn.execute(
        "SELECT deadline_id, case_name, court, filing_type, due_date, "
        "priority, status, basis, authority, notes FROM litigation_deadlines ORDER BY due_date"
    )
    rows = []
    for r in cur.fetchall():
        rec = dict(r)
        try:
            due = datetime.strptime(rec['due_date'], '%Y-%m-%d').date()
            rec['days_remaining'] = (due - REFERENCE_DATE).days
        except (ValueError, TypeError):
            rec['days_remaining'] = None
        rec['urgency'], rec['color'] = classify_urgency(rec['days_remaining']) if rec['days_remaining'] is not None else ('UNKNOWN', 'white')
        rows.append(rec)
    return rows

def load_sol_audit(conn):
    """Load SOL audit results and recalculate days remaining."""
    try:
        cur = conn.execute(
            "SELECT stack_name, court, count_name, sol_years, citation, "
            "earliest_incident_date, latest_incident_date, sol_expiration_date, "
            "tolling_arguments, risk_level, risk_notes FROM sol_audit_results ORDER BY sol_expiration_date"
        )
    except sqlite3.OperationalError:
        return []
    rows = []
    for r in cur.fetchall():
        rec = dict(r)
        try:
            exp = datetime.strptime(rec['sol_expiration_date'], '%Y-%m-%d').date()
            rec['days_remaining'] = (exp - REFERENCE_DATE).days
        except (ValueError, TypeError):
            rec['days_remaining'] = None
        rec['urgency'], rec['color'] = classify_urgency(rec['days_remaining']) if rec['days_remaining'] is not None else ('UNKNOWN', 'white')
        rows.append(rec)
    return rows

# ─── Display functions ─────────────────────────────────────────────

def display_deadlines_rich(deadlines, title="Litigation Deadlines", urgent_only=False):
    console = Console()
    table = Table(title=title, show_lines=True, title_style="bold bright_white")
    table.add_column("Status", width=8, justify="center")
    table.add_column("Deadline ID", style="cyan", width=20)
    table.add_column("Case", width=30)
    table.add_column("Filing Type", width=25)
    table.add_column("Due Date", width=12)
    table.add_column("Days Left", justify="right", width=10)
    table.add_column("Priority", width=10)

    for d in deadlines:
        if urgent_only and d['urgency'] not in ('OVERDUE', 'RED', 'YELLOW'):
            continue
        emoji = urgency_emoji(d['urgency'])
        days_str = str(d['days_remaining']) if d['days_remaining'] is not None else '?'
        style = d['color']
        table.add_row(
            emoji, d['deadline_id'], d['case_name'], d['filing_type'],
            d['due_date'] or '?', days_str, d.get('priority', ''), style=style
        )

    console.print(table)

    # Summary
    counts = {}
    for d in deadlines:
        counts[d['urgency']] = counts.get(d['urgency'], 0) + 1
    summary_parts = []
    for label in ('OVERDUE', 'RED', 'YELLOW', 'GREEN'):
        if counts.get(label, 0) > 0:
            summary_parts.append(f"{urgency_emoji(label)} {label}: {counts[label]}")
    console.print(Panel(" | ".join(summary_parts), title="Summary", border_style="bright_blue"))

def display_sol_rich(sol_items, urgent_only=False):
    if not sol_items:
        return
    console = Console()
    table = Table(title="Statute of Limitations Audit", show_lines=True, title_style="bold bright_white")
    table.add_column("Status", width=8, justify="center")
    table.add_column("Case Stack", width=28)
    table.add_column("Count", width=30)
    table.add_column("SOL (yrs)", justify="right", width=9)
    table.add_column("Expiration", width=12)
    table.add_column("Days Left", justify="right", width=10)
    table.add_column("Citation", width=20)

    for s in sol_items:
        if urgent_only and s['urgency'] not in ('OVERDUE', 'RED', 'YELLOW'):
            continue
        emoji = urgency_emoji(s['urgency'])
        days_str = str(s['days_remaining']) if s['days_remaining'] is not None else '?'
        table.add_row(
            emoji, s['stack_name'], s['count_name'],
            str(s.get('sol_years', '?')), s.get('sol_expiration_date', '?'),
            days_str, s.get('citation', ''), style=s['color']
        )

    console.print(table)

def display_deadlines_plain(deadlines, title="Litigation Deadlines", urgent_only=False):
    print(f"\n{'='*80}")
    print(f"  {title}")
    print(f"  Reference Date: {REFERENCE_DATE}")
    print(f"{'='*80}")
    print(f"{'Status':<10} {'ID':<22} {'Case':<28} {'Filing':<22} {'Due':<12} {'Days':>6} {'Priority':<10}")
    print('-' * 110)
    for d in deadlines:
        if urgent_only and d['urgency'] not in ('OVERDUE', 'RED', 'YELLOW'):
            continue
        emoji = urgency_emoji(d['urgency'])
        days_str = str(d['days_remaining']) if d['days_remaining'] is not None else '?'
        print(f"{emoji:<10} {d['deadline_id']:<22} {d['case_name'][:27]:<28} {d['filing_type'][:21]:<22} {d['due_date'] or '?':<12} {days_str:>6} {d.get('priority', ''):<10}")

    counts = {}
    for d in deadlines:
        counts[d['urgency']] = counts.get(d['urgency'], 0) + 1
    print(f"\n  Summary: ", end='')
    for label in ('OVERDUE', 'RED', 'YELLOW', 'GREEN'):
        if counts.get(label, 0) > 0:
            print(f"{urgency_emoji(label)} {label}: {counts[label]}  ", end='')
    print()

def display_sol_plain(sol_items, urgent_only=False):
    if not sol_items:
        return
    print(f"\n{'='*80}")
    print(f"  Statute of Limitations Audit")
    print(f"{'='*80}")
    print(f"{'Status':<10} {'Stack':<26} {'Count':<28} {'SOL':>5} {'Expiration':<12} {'Days':>6}")
    print('-' * 90)
    for s in sol_items:
        if urgent_only and s['urgency'] not in ('OVERDUE', 'RED', 'YELLOW'):
            continue
        emoji = urgency_emoji(s['urgency'])
        days_str = str(s['days_remaining']) if s['days_remaining'] is not None else '?'
        print(f"{emoji:<10} {s['stack_name'][:25]:<26} {s['count_name'][:27]:<28} {str(s.get('sol_years', '?')):>5} {s.get('sol_expiration_date', '?'):<12} {days_str:>6}")

# ─── Report generation ─────────────────────────────────────────────

def generate_report(deadlines, sol_items, output_path):
    """Generate markdown daily briefing report."""
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(f"# ⚖️ Deadline Dashboard — Daily Briefing\n\n")
        f.write(f"**Generated:** {datetime.now():%Y-%m-%d %H:%M:%S}  \n")
        f.write(f"**Reference Date:** {REFERENCE_DATE}  \n\n")

        # Summary counts
        dl_counts = {}
        for d in deadlines:
            dl_counts[d['urgency']] = dl_counts.get(d['urgency'], 0) + 1
        f.write("## 📊 Summary\n\n")
        f.write("| Urgency | Count |\n|---------|-------|\n")
        for label in ('OVERDUE', 'RED', 'YELLOW', 'GREEN'):
            if dl_counts.get(label, 0) > 0:
                f.write(f"| {urgency_emoji(label)} {label} | {dl_counts[label]} |\n")
        f.write(f"| **Total** | **{len(deadlines)}** |\n\n")

        # Critical items first
        critical = [d for d in deadlines if d['urgency'] in ('OVERDUE', 'RED')]
        if critical:
            f.write("## 🚨 CRITICAL — Immediate Action Required\n\n")
            for d in critical:
                emoji = urgency_emoji(d['urgency'])
                f.write(f"### {emoji} {d['deadline_id']} — {d['filing_type']}\n\n")
                f.write(f"- **Case:** {d['case_name']}\n")
                f.write(f"- **Court:** {d['court']}\n")
                f.write(f"- **Due Date:** {d['due_date']}\n")
                f.write(f"- **Days Remaining:** {d['days_remaining']}\n")
                f.write(f"- **Priority:** {d.get('priority', 'N/A')}\n")
                f.write(f"- **Authority:** {d.get('authority', 'N/A')}\n")
                if d.get('notes'):
                    f.write(f"- **Notes:** {d['notes']}\n")
                f.write("\n")

        # Upcoming (YELLOW)
        yellow = [d for d in deadlines if d['urgency'] == 'YELLOW']
        if yellow:
            f.write("## 🟡 UPCOMING — 15-30 Days\n\n")
            f.write("| Deadline | Case | Due | Days Left | Authority |\n")
            f.write("|----------|------|-----|-----------|----------|\n")
            for d in yellow:
                f.write(f"| {d['deadline_id']} | {d['case_name'][:35]} | {d['due_date']} | {d['days_remaining']} | {d.get('authority', '')} |\n")
            f.write("\n")

        # All deadlines table
        f.write("## 📅 All Deadlines\n\n")
        f.write("| Status | ID | Case | Filing | Due | Days | Priority |\n")
        f.write("|--------|----|------|--------|-----|------|----------|\n")
        for d in deadlines:
            emoji = urgency_emoji(d['urgency'])
            days_str = str(d['days_remaining']) if d['days_remaining'] is not None else '?'
            f.write(f"| {emoji} {d['urgency']} | {d['deadline_id']} | {d['case_name'][:30]} | {d['filing_type'][:25]} | {d['due_date'] or '?'} | {days_str} | {d.get('priority', '')} |\n")
        f.write("\n")

        # SOL Audit section
        if sol_items:
            f.write("## ⏳ Statute of Limitations Audit\n\n")
            approaching = [s for s in sol_items if s['urgency'] in ('OVERDUE', 'RED', 'YELLOW')]
            if approaching:
                f.write("### ⚠️ Approaching SOL Expirations\n\n")
                for s in approaching:
                    emoji = urgency_emoji(s['urgency'])
                    f.write(f"- {emoji} **{s['count_name']}** ({s['stack_name']}) — Expires: {s.get('sol_expiration_date', '?')} ({s['days_remaining']} days)\n")
                    f.write(f"  - Citation: {s.get('citation', 'N/A')}\n")
                    if s.get('tolling_arguments'):
                        f.write(f"  - Tolling: {s['tolling_arguments']}\n")
                f.write("\n")

            f.write("### Full SOL Table\n\n")
            f.write("| Status | Stack | Count | SOL (yrs) | Expiration | Days Left | Citation |\n")
            f.write("|--------|-------|-------|-----------|------------|-----------|----------|\n")
            for s in sol_items:
                emoji = urgency_emoji(s['urgency'])
                days_str = str(s['days_remaining']) if s['days_remaining'] is not None else '?'
                f.write(f"| {emoji} {s['urgency']} | {s['stack_name'][:25]} | {s['count_name'][:28]} | {s.get('sol_years', '?')} | {s.get('sol_expiration_date', '?')} | {days_str} | {s.get('citation', '')} |\n")
            f.write("\n")

        f.write("---\n")
        f.write(f"*Generated by LitigationOS Deadline Alert Engine — {datetime.now():%Y-%m-%d %H:%M:%S}*\n")

    return output_path

# ─── Update DB ─────────────────────────────────────────────────────

def update_days_remaining(conn):
    """Recalculate days_remaining column in both tables using reference date."""
    updated = 0
    # Update litigation_deadlines
    cur = conn.execute("SELECT deadline_id, due_date FROM litigation_deadlines")
    for row in cur.fetchall():
        try:
            due = datetime.strptime(row['due_date'], '%Y-%m-%d').date()
            days = (due - REFERENCE_DATE).days
            conn.execute(
                "UPDATE litigation_deadlines SET days_remaining = ?, updated_at = datetime('now') WHERE deadline_id = ?",
                (days, row['deadline_id'])
            )
            updated += 1
        except (ValueError, TypeError):
            pass

    # Update sol_audit_results
    try:
        cur = conn.execute("SELECT id, sol_expiration_date FROM sol_audit_results")
        for row in cur.fetchall():
            try:
                exp = datetime.strptime(row['sol_expiration_date'], '%Y-%m-%d').date()
                days = (exp - REFERENCE_DATE).days
                risk = classify_urgency(days)[0]
                conn.execute(
                    "UPDATE sol_audit_results SET days_remaining = ?, risk_level = ? WHERE id = ?",
                    (days, risk, row['id'])
                )
                updated += 1
            except (ValueError, TypeError):
                pass
    except sqlite3.OperationalError:
        pass

    conn.commit()
    return updated

# ─── Main ──────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description="LitigationOS Deadline Alert Engine")
    parser.add_argument('--urgent', action='store_true', help='Show RED + YELLOW deadlines only')
    parser.add_argument('--report', action='store_true', help='Generate markdown briefing report')
    parser.add_argument('--update', action='store_true', help='Recalculate days_remaining in DB')
    args = parser.parse_args()

    conn = get_connection()
    deadlines = load_deadlines(conn)
    sol_items = load_sol_audit(conn)

    if args.update:
        count = update_days_remaining(conn)
        print(f"✅ Updated {count} records with recalculated days_remaining (ref: {REFERENCE_DATE})")
        # Reload after update
        deadlines = load_deadlines(conn)
        sol_items = load_sol_audit(conn)

    if args.report:
        path = generate_report(deadlines, sol_items, REPORT_DIR)
        print(f"📄 Report generated: {os.path.abspath(path)}")

    # Display
    if HAS_RICH:
        display_deadlines_rich(deadlines, urgent_only=args.urgent)
        display_sol_rich(sol_items, urgent_only=args.urgent)
    else:
        display_deadlines_plain(deadlines, urgent_only=args.urgent)
        display_sol_plain(sol_items, urgent_only=args.urgent)

    conn.close()

if __name__ == '__main__':
    main()
