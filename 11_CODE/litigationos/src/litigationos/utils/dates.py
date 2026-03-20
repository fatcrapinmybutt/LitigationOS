"""Date calculation helpers — business days, court holidays, and deadlines.

Provides Michigan-aware date math for calculating filing deadlines,
accounting for weekends and court holidays.
"""

from __future__ import annotations

from datetime import date, timedelta
from typing import Optional


# Michigan court holidays (observed)
MICHIGAN_HOLIDAYS_2024 = [
    date(2024, 1, 1),   # New Year's Day
    date(2024, 1, 15),  # MLK Day
    date(2024, 2, 19),  # Presidents' Day
    date(2024, 5, 27),  # Memorial Day
    date(2024, 6, 19),  # Juneteenth
    date(2024, 7, 4),   # Independence Day
    date(2024, 9, 2),   # Labor Day
    date(2024, 11, 11), # Veterans Day
    date(2024, 11, 28), # Thanksgiving
    date(2024, 11, 29), # Day after Thanksgiving
    date(2024, 12, 25), # Christmas Day
]


def is_business_day(d: date, holidays: Optional[list[date]] = None) -> bool:
    """Check if a date is a business day (not weekend, not holiday)."""
    if d.weekday() >= 5:  # Saturday=5, Sunday=6
        return False
    if holidays and d in holidays:
        return False
    return True


def add_business_days(
    start: date, days: int, holidays: Optional[list[date]] = None
) -> date:
    """Add N business days to a start date, skipping weekends and holidays."""
    holidays = holidays or MICHIGAN_HOLIDAYS_2024
    current = start
    added = 0
    while added < days:
        current += timedelta(days=1)
        if is_business_day(current, holidays):
            added += 1
    return current


def add_calendar_days(start: date, days: int) -> date:
    """Add N calendar days to a start date."""
    return start + timedelta(days=days)


def days_between(start: date, end: date) -> int:
    """Calculate calendar days between two dates."""
    return (end - start).days


def business_days_between(
    start: date, end: date, holidays: Optional[list[date]] = None
) -> int:
    """Calculate business days between two dates."""
    holidays = holidays or MICHIGAN_HOLIDAYS_2024
    count = 0
    current = start
    while current < end:
        current += timedelta(days=1)
        if is_business_day(current, holidays):
            count += 1
    return count
