"""
Separation Day Counter Skill
Run anytime to get current separation count.
Usage: python separation_counter.py
"""
import sys, io
from datetime import datetime

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

SEPARATION_START = datetime(2025, 8, 8)

def get_separation_count(reference_date=None):
    """Calculate separation days from Aug 8, 2025 to the given date (default: today)."""
    if reference_date is None:
        reference_date = datetime.now()
    delta = reference_date - SEPARATION_START
    total_days = delta.days
    total_weeks = total_days / 7
    total_months = total_days / 30.44
    return {
        'start_date': SEPARATION_START.strftime('%Y-%m-%d'),
        'current_date': reference_date.strftime('%Y-%m-%d'),
        'total_days': total_days,
        'total_weeks': round(total_weeks, 1),
        'total_months': round(total_months, 1),
        'trigger': '5 ex parte orders by Judge McNeill — no hearing, no notice',
        'bif_hearing_held': False,
        'constitutional_thresholds_exceeded': [
            t for t in [30, 60, 90, 180, 365] if total_days >= t
        ]
    }

def print_separation_report(reference_date=None):
    """Print a formatted separation report."""
    data = get_separation_count(reference_date)
    print("=" * 60)
    print("  SEPARATION DAY COUNTER — Pigors v. Watson")
    print("  Case: 2024-001507-DC | 14th Circuit Court")
    print("=" * 60)
    print(f"  Separation Start:  {data['start_date']}")
    print(f"  Current Date:      {data['current_date']}")
    print(f"  Total Days:        {data['total_days']} days")
    print(f"  Total Weeks:       {data['total_weeks']} weeks")
    print(f"  Total Months:      {data['total_months']} months")
    print(f"  BIF Hearing Held:  {'YES' if data['bif_hearing_held'] else 'NO'}")
    print(f"  Trigger:           {data['trigger']}")
    print(f"  Thresholds Exceeded: {data['constitutional_thresholds_exceeded']}")
    print("=" * 60)
    if data['total_days'] > 180:
        print("  ⚠️  CRITICAL: Separation exceeds 180-day threshold.")
        print("  De facto permanent deprivation without due process.")
    return data

if __name__ == '__main__':
    print_separation_report()
