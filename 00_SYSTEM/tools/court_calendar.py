#!/usr/bin/env python3
"""
Court Calendar & Gantt Generator — LitigationOS Novel Tool
=============================================================
Generates visual filing timelines and court date projections.

Features:
  1. ASCII Gantt chart of all 10 filings
  2. Court date projections (filing → hearing → decision)
  3. MCR response deadlines for each filing
  4. Conflict detection (two filings same week)
  5. Weekly action plan

Michigan timing rules:
  MCR 2.119(C): 9 days notice for motion hearing
  MCR 2.108(A): 14 days to answer/respond
  MCR 7.212(A): 56 days for appellee's brief
  MCR 7.211(C)(6): Emergency same-day

Usage:
  python court_calendar.py --gantt            # ASCII Gantt chart
  python court_calendar.py --weekly           # Weekly action plan
  python court_calendar.py --conflicts        # Detect scheduling conflicts
  python court_calendar.py --projections      # Hearing/decision dates
  python court_calendar.py --json             # JSON output
"""

import sys, os, json, argparse
from datetime import datetime, date, timedelta

sys.stdout = open(sys.stdout.fileno(), mode='w', encoding='utf-8', errors='replace')

REPORTS_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'reports')

# ─── FILING TIMELINE DATA ────────────────────────────────────────────

TODAY = date.today()

FILINGS = {
    'F3':  {'name': 'Disqualification', 'deadline': '2026-04-01', 'prep_days': 2, 'hearing_days': 14, 'decision_days': 7, 'ready': True,  'priority': 1},
    'F10': {'name': 'COA Emergency',    'deadline': '2026-04-01', 'prep_days': 5, 'hearing_days': 7,  'decision_days': 14, 'ready': False, 'priority': 2},
    'F1':  {'name': 'Emergency TRO',    'deadline': '2026-04-15', 'prep_days': 1, 'hearing_days': 3,  'decision_days': 1,  'ready': True,  'priority': 3},
    'F9':  {'name': 'COA Brief',        'deadline': '2026-04-15', 'prep_days': 3, 'hearing_days': 56, 'decision_days': 28, 'ready': False, 'priority': 4},
    'F7':  {'name': 'Custody Mod',      'deadline': '2026-05-01', 'prep_days': 7, 'hearing_days': 28, 'decision_days': 14, 'ready': False, 'priority': 5},
    'F2':  {'name': 'Housing Complaint','deadline': '2026-05-01', 'prep_days': 3, 'hearing_days': 91, 'decision_days': 14, 'ready': True,  'priority': 6},
    'F5':  {'name': 'MSC Action',       'deadline': '2026-05-15', 'prep_days': 10,'hearing_days': 60, 'decision_days': 30, 'ready': False, 'priority': 7},
    'F8':  {'name': 'PPO Termination',  'deadline': '2026-05-15', 'prep_days': 5, 'hearing_days': 21, 'decision_days': 7,  'ready': False, 'priority': 8},
    'F4':  {'name': 'Federal §1983',    'deadline': '2026-06-01', 'prep_days': 10,'hearing_days': 30, 'decision_days': 60, 'ready': False, 'priority': 9},
    'F6':  {'name': 'JTC Complaint',    'deadline': '2026-06-30', 'prep_days': 7, 'hearing_days': 90, 'decision_days': 90, 'ready': False, 'priority': 10},
}


def compute_dates(filing_id, info):
    """Compute filing → hearing → decision dates."""
    deadline = date.fromisoformat(info['deadline'])
    
    if info['ready']:
        file_date = max(TODAY, deadline - timedelta(days=info['hearing_days'] + info['decision_days'] + 7))
    else:
        file_date = max(TODAY + timedelta(days=info['prep_days']),
                        deadline - timedelta(days=info['hearing_days'] + info['decision_days']))
    
    # Don't file past deadline
    if file_date > deadline:
        file_date = deadline - timedelta(days=1)
    
    hearing_date = file_date + timedelta(days=info['hearing_days'])
    decision_date = hearing_date + timedelta(days=info['decision_days'])
    
    return {
        'file_date': file_date,
        'hearing_date': hearing_date,
        'decision_date': decision_date,
        'deadline': deadline,
        'days_to_deadline': (deadline - TODAY).days,
        'margin': (deadline - file_date).days,
    }


def print_gantt():
    """Print ASCII Gantt chart."""
    print(f"\n{'═' * 100}")
    print(f"  COURT CALENDAR & GANTT — LitigationOS")
    print(f"  Today: {TODAY.isoformat()}")
    print(f"{'═' * 100}\n")
    
    # Determine date range
    all_dates = []
    for fid, info in FILINGS.items():
        dates = compute_dates(fid, info)
        all_dates.extend([dates['file_date'], dates['hearing_date'], dates['decision_date']])
    
    start_date = min(all_dates)
    end_date = max(all_dates)
    total_days = (end_date - start_date).days + 1
    
    # Chart width
    chart_width = min(80, total_days)
    scale = total_days / chart_width
    
    # Month headers
    header = "  " + " " * 22
    month_line = "  " + " " * 22
    current_month = start_date.month
    for i in range(chart_width):
        d = start_date + timedelta(days=int(i * scale))
        if d.month != current_month or i == 0:
            current_month = d.month
            month_name = d.strftime('%b')
            header += month_name[:3]
        else:
            header += ' '
        
        if d == TODAY:
            month_line += '▼'
        elif d.weekday() == 0:
            month_line += '·'
        else:
            month_line += ' '
    
    print(header)
    print(month_line)
    print("  " + " " * 22 + "─" * chart_width)
    
    # Filing bars
    for fid in sorted(FILINGS.keys(), key=lambda f: FILINGS[f]['priority']):
        info = FILINGS[fid]
        dates = compute_dates(fid, info)
        
        label = f"  {fid:<4} {info['name']:<16} "
        bar = [' '] * chart_width
        
        # Mark filing date
        file_pos = int((dates['file_date'] - start_date).days / scale)
        file_pos = max(0, min(chart_width - 1, file_pos))
        
        # Mark hearing date
        hear_pos = int((dates['hearing_date'] - start_date).days / scale)
        hear_pos = max(0, min(chart_width - 1, hear_pos))
        
        # Mark decision date
        dec_pos = int((dates['decision_date'] - start_date).days / scale)
        dec_pos = max(0, min(chart_width - 1, dec_pos))
        
        # Mark deadline
        dl_pos = int((dates['deadline'] - start_date).days / scale)
        dl_pos = max(0, min(chart_width - 1, dl_pos))
        
        # Fill bar
        for i in range(file_pos, min(hear_pos + 1, chart_width)):
            bar[i] = '█'
        for i in range(hear_pos, min(dec_pos + 1, chart_width)):
            bar[i] = '░'
        
        bar[file_pos] = '▶' if info['ready'] else '○'
        if hear_pos < chart_width:
            bar[hear_pos] = '◆'
        if dl_pos < chart_width:
            bar[dl_pos] = '|'
        
        print(label + ''.join(bar))
    
    print("  " + " " * 22 + "─" * chart_width)
    print(f"  Legend: ▶=file(ready) ○=file(prep) █=waiting ◆=hearing ░=decision |=deadline ▼=today")
    print()


def print_weekly_plan():
    """Print weekly action plan."""
    print(f"\n  📅 WEEKLY ACTION PLAN")
    print(f"  {'─' * 60}")
    
    # Group filings by week
    weeks = {}
    for fid, info in FILINGS.items():
        dates = compute_dates(fid, info)
        week_num = dates['file_date'].isocalendar()[1]
        week_start = dates['file_date'] - timedelta(days=dates['file_date'].weekday())
        key = week_start.isoformat()
        if key not in weeks:
            weeks[key] = {'start': week_start, 'actions': []}
        
        action = 'FILE' if info['ready'] else 'PREP + FILE'
        weeks[key]['actions'].append(f"{action} {fid} ({info['name']}) — deadline {info['deadline']}")
    
    for week_key in sorted(weeks.keys()):
        week = weeks[week_key]
        week_end = week['start'] + timedelta(days=6)
        is_current = week['start'] <= TODAY <= week_end
        marker = ' 👈 THIS WEEK' if is_current else ''
        print(f"\n  Week of {week['start'].strftime('%b %d')} — {week_end.strftime('%b %d')}{marker}")
        for action in week['actions']:
            print(f"    • {action}")
    print()


def detect_conflicts():
    """Detect scheduling conflicts."""
    print(f"\n  ⚠ SCHEDULING CONFLICTS")
    print(f"  {'─' * 60}")
    
    events = []
    for fid, info in FILINGS.items():
        dates = compute_dates(fid, info)
        events.append((dates['file_date'], fid, 'FILING'))
        events.append((dates['hearing_date'], fid, 'HEARING'))
    
    events.sort()
    conflicts = 0
    
    for i in range(len(events) - 1):
        d1, f1, t1 = events[i]
        d2, f2, t2 = events[i + 1]
        
        if d1 == d2 and f1 != f2:
            conflicts += 1
            print(f"  ⚠ {d1}: {f1} ({t1}) and {f2} ({t2}) — SAME DAY")
        elif (d2 - d1).days <= 2 and f1 != f2:
            print(f"  🟡 {d1}–{d2}: {f1} ({t1}) and {f2} ({t2}) — within 2 days")
    
    if conflicts == 0:
        print(f"  ✅ No same-day conflicts detected")
    print()


def print_projections():
    """Print hearing/decision date projections."""
    print(f"\n  📊 FILING PROJECTIONS")
    print(f"  {'Filing':<6} {'File':>11} {'Hearing':>11} {'Decision':>11} {'Deadline':>11} {'Margin':>7}")
    print(f"  {'─' * 66}")
    
    for fid in sorted(FILINGS.keys(), key=lambda f: FILINGS[f]['priority']):
        info = FILINGS[fid]
        dates = compute_dates(fid, info)
        
        ready = '✅' if info['ready'] else '⬜'
        margin = dates['margin']
        margin_icon = '🟢' if margin > 14 else '🟡' if margin > 7 else '🔴'
        
        print(f"  {ready}{fid:<5} {dates['file_date'].strftime('%Y-%m-%d'):>11} "
              f"{dates['hearing_date'].strftime('%Y-%m-%d'):>11} "
              f"{dates['decision_date'].strftime('%Y-%m-%d'):>11} "
              f"{dates['deadline'].strftime('%Y-%m-%d'):>11} {margin_icon}{margin:>5}d")
    print()


def main():
    parser = argparse.ArgumentParser(description='Court Calendar & Gantt Generator')
    parser.add_argument('--gantt', '-g', action='store_true', help='ASCII Gantt chart')
    parser.add_argument('--weekly', '-w', action='store_true', help='Weekly plan')
    parser.add_argument('--conflicts', '-c', action='store_true', help='Conflict detection')
    parser.add_argument('--projections', '-p', action='store_true', help='Date projections')
    parser.add_argument('--json', '-j', action='store_true', help='JSON output')
    args = parser.parse_args()
    
    if not any([args.gantt, args.weekly, args.conflicts, args.projections]):
        args.gantt = True
        args.weekly = True
        args.conflicts = True
        args.projections = True
    
    if args.gantt:
        print_gantt()
    if args.projections:
        print_projections()
    if args.weekly:
        print_weekly_plan()
    if args.conflicts:
        detect_conflicts()
    
    if args.json:
        os.makedirs(REPORTS_DIR, exist_ok=True)
        jpath = os.path.join(REPORTS_DIR, 'court_calendar.json')
        data = {}
        for fid, info in FILINGS.items():
            dates = compute_dates(fid, info)
            data[fid] = {
                'name': info['name'],
                'file_date': dates['file_date'].isoformat(),
                'hearing_date': dates['hearing_date'].isoformat(),
                'decision_date': dates['decision_date'].isoformat(),
                'deadline': dates['deadline'].isoformat(),
                'margin_days': dates['margin'],
                'ready': info['ready'],
            }
        with open(jpath, 'w', encoding='utf-8') as f:
            json.dump({'filings': data, 'generated': datetime.now().isoformat()}, f, indent=2)
        print(f"  📊 JSON: {jpath}")


if __name__ == '__main__':
    main()
