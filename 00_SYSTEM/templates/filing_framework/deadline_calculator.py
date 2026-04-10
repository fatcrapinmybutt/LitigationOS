"""
MCR Deadline Calculator
========================

Computes litigation deadlines using Michigan Court Rules day-counting:

- **< 7 days**: Exclude weekends and holidays (MCR 1.108(1)).
- **≥ 7 days**: Count all calendar days; if the last day falls on a
  weekend or holiday, extend to the next business day (MCR 1.108(2)).

Usage::

    from datetime import date
    from deadline_calculator import calculate_deadline, MOTION_RESPONSE

    deadline = calculate_deadline(date(2025, 6, 1), MOTION_RESPONSE)
    print(deadline)  # 2025-06-22 (or next business day)
"""

from __future__ import annotations

from datetime import date, timedelta
from typing import List, Optional, Union


# ── Common deadline constants (days) ─────────────────────────────────────────

MOTION_RESPONSE: int = 21
"""Days to respond to a motion. MCR 2.119(C)(1)."""

REPLY_BRIEF: int = 7
"""Days to file a reply brief after response. MCR 2.119(C)(2)."""

FOC_OBJECTION: int = 21
"""Days to object to a Friend of the Court recommendation. MCR 3.218(C)."""

CLAIM_OF_APPEAL: int = 21
"""Days to file a claim of appeal. MCR 7.204(A)(1)."""

COA_BRIEF: int = 56
"""Days to file an appellant's brief after claim of appeal. MCR 7.212(A)(1)."""

EX_PARTE_OBJECTION: int = 14
"""Days to object to an ex parte order. MCR 2.119(B)."""

PPO_OBJECTION: int = 14
"""Days to request hearing to terminate/modify a PPO. MCL 600.2950(12)."""

FEDERAL_SERVICE: int = 90
"""Days to serve a federal complaint. FRCP 4(m)."""

MSC_APPLICATION: int = 56
"""Days to file MSC application after COA decision. MCR 7.305(C)(2)."""

MOTION_HEARING_NOTICE: int = 9
"""Days' notice required for motion hearing. MCR 2.119(C)(1)."""

SUMMARY_DISPOSITION_RESPONSE: int = 21
"""Days to respond to summary disposition motion. MCR 2.116(B)(1)."""

ANSWER_TO_COMPLAINT: int = 21
"""Days to answer a complaint after service. MCR 2.108(A)(1)."""

RECONSIDERATION: int = 21
"""Days to move for reconsideration. MCR 2.119(F)(1)."""

COA_APPELLEE_BRIEF: int = 35
"""Days for appellee brief after appellant brief. MCR 7.212(A)(3)."""

COA_REPLY_BRIEF: int = 21
"""Days for reply brief after appellee brief. MCR 7.212(A)(4)."""


# ── Michigan Court Holidays ──────────────────────────────────────────────────

def get_michigan_holidays(year: int) -> List[date]:
    """Return Michigan court holidays for the given year.

    Includes all holidays recognized by Michigan courts per MCL 435.101
    and court administrative orders.

    Args:
        year: Calendar year.

    Returns:
        Sorted list of holiday dates for the year.
    """
    holidays: List[date] = []

    # New Year's Day — January 1
    holidays.append(date(year, 1, 1))

    # Martin Luther King Jr. Day — 3rd Monday of January
    holidays.append(_nth_weekday(year, 1, 0, 3))  # 0=Monday

    # Presidents' Day — 3rd Monday of February
    holidays.append(_nth_weekday(year, 2, 0, 3))

    # Memorial Day — last Monday of May
    holidays.append(_last_weekday(year, 5, 0))

    # Juneteenth — June 19
    holidays.append(date(year, 6, 19))

    # Independence Day — July 4
    holidays.append(date(year, 7, 4))

    # Labor Day — 1st Monday of September
    holidays.append(_nth_weekday(year, 9, 0, 1))

    # Columbus Day / Indigenous Peoples' Day — 2nd Monday of October
    holidays.append(_nth_weekday(year, 10, 0, 2))

    # Election Day — 1st Tuesday after 1st Monday in November (even years)
    if year % 2 == 0:
        first_monday = _nth_weekday(year, 11, 0, 1)
        holidays.append(first_monday + timedelta(days=1))

    # Veterans Day — November 11
    holidays.append(date(year, 11, 11))

    # Thanksgiving — 4th Thursday of November
    holidays.append(_nth_weekday(year, 11, 3, 4))  # 3=Thursday

    # Day after Thanksgiving — 4th Friday of November
    thanksgiving = _nth_weekday(year, 11, 3, 4)
    holidays.append(thanksgiving + timedelta(days=1))

    # Christmas Eve — December 24
    holidays.append(date(year, 12, 24))

    # Christmas Day — December 25
    holidays.append(date(year, 12, 25))

    # New Year's Eve — December 31
    holidays.append(date(year, 12, 31))

    holidays.sort()
    return holidays


def _nth_weekday(year: int, month: int, weekday: int, n: int) -> date:
    """Return the *n*-th occurrence of *weekday* in *month*/*year*.

    Args:
        weekday: 0=Monday … 6=Sunday.
        n: 1-based occurrence (1=first, 2=second, etc.).
    """
    first_day = date(year, month, 1)
    # Days until the first occurrence of the target weekday
    days_ahead = (weekday - first_day.weekday()) % 7
    first_occurrence = first_day + timedelta(days=days_ahead)
    return first_occurrence + timedelta(weeks=n - 1)


def _last_weekday(year: int, month: int, weekday: int) -> date:
    """Return the last occurrence of *weekday* in *month*/*year*."""
    if month == 12:
        last_day = date(year + 1, 1, 1) - timedelta(days=1)
    else:
        last_day = date(year, month + 1, 1) - timedelta(days=1)
    days_behind = (last_day.weekday() - weekday) % 7
    return last_day - timedelta(days=days_behind)


# ── Business-Day Utilities ───────────────────────────────────────────────────

def is_business_day(d: date) -> bool:
    """Check whether *d* is a business day (not weekend, not MI holiday).

    Args:
        d: Date to check.

    Returns:
        True if *d* is a business day.
    """
    if d.weekday() >= 5:  # Saturday=5, Sunday=6
        return False
    return d not in get_michigan_holidays(d.year)


def next_business_day(d: date) -> date:
    """Return *d* if it is a business day, otherwise the next business day.

    Args:
        d: Starting date.

    Returns:
        The same date or the next business day.
    """
    while not is_business_day(d):
        d += timedelta(days=1)
    return d


# ── Core Deadline Calculator ─────────────────────────────────────────────────

def calculate_deadline(
    trigger_date: Union[date, str],
    days: Union[int, str],
    court: str = "circuit",
) -> date:
    """Compute a deadline applying MCR 1.108 day-counting rules.

    **MCR 1.108(1)** — periods < 7 days: exclude weekends and holidays.
    **MCR 1.108(2)** — periods ≥ 7 days: count all calendar days; if the
    last day falls on a weekend or holiday, extend to the next business day.

    For federal court, FRCP 6(a) is substantially similar: periods < 7 days
    exclude weekends/holidays; ≥ 7 days include them with extension.

    Args:
        trigger_date: The event date that starts the clock (date or ISO string).
        days: Number of days in the period, or the name of a constant
            (e.g., ``"MOTION_RESPONSE"``).
        court: ``"circuit"``, ``"coa"``, ``"msc"``, ``"wdmi"``, ``"district"``.

    Returns:
        Computed deadline date.

    Raises:
        ValueError: If *days* is a string that does not match a known constant.
    """
    # Parse trigger_date
    if isinstance(trigger_date, str):
        trigger_date = date.fromisoformat(trigger_date)

    # Resolve named constants
    if isinstance(days, str):
        days = _resolve_constant(days)

    if days < 1:
        raise ValueError("Deadline days must be ≥ 1.")

    # MCR 1.108 / FRCP 6(a): exclude the trigger day itself; start counting
    # on the day after the trigger event.
    if days < 7:
        # Short period: count only business days
        return _count_business_days(trigger_date, days)
    else:
        # Long period: count calendar days, then extend if needed
        deadline = trigger_date + timedelta(days=days)
        return next_business_day(deadline)


def _count_business_days(start: date, n: int) -> date:
    """Count *n* business days forward from *start* (exclusive of *start*)."""
    current = start
    counted = 0
    while counted < n:
        current += timedelta(days=1)
        if is_business_day(current):
            counted += 1
    return current


def _resolve_constant(name: str) -> int:
    """Resolve a named deadline constant to its integer value."""
    constants = {
        "MOTION_RESPONSE": MOTION_RESPONSE,
        "REPLY_BRIEF": REPLY_BRIEF,
        "FOC_OBJECTION": FOC_OBJECTION,
        "CLAIM_OF_APPEAL": CLAIM_OF_APPEAL,
        "COA_BRIEF": COA_BRIEF,
        "EX_PARTE_OBJECTION": EX_PARTE_OBJECTION,
        "PPO_OBJECTION": PPO_OBJECTION,
        "FEDERAL_SERVICE": FEDERAL_SERVICE,
        "MSC_APPLICATION": MSC_APPLICATION,
        "MOTION_HEARING_NOTICE": MOTION_HEARING_NOTICE,
        "SUMMARY_DISPOSITION_RESPONSE": SUMMARY_DISPOSITION_RESPONSE,
        "ANSWER_TO_COMPLAINT": ANSWER_TO_COMPLAINT,
        "RECONSIDERATION": RECONSIDERATION,
        "COA_APPELLEE_BRIEF": COA_APPELLEE_BRIEF,
        "COA_REPLY_BRIEF": COA_REPLY_BRIEF,
    }
    key = name.upper().strip()
    if key not in constants:
        raise ValueError(
            f"Unknown deadline constant '{name}'. "
            f"Known constants: {', '.join(constants)}"
        )
    return constants[key]


def get_all_constants() -> dict[str, int]:
    """Return all deadline constants as a ``{name: days}`` dict."""
    return {
        "MOTION_RESPONSE": MOTION_RESPONSE,
        "REPLY_BRIEF": REPLY_BRIEF,
        "FOC_OBJECTION": FOC_OBJECTION,
        "CLAIM_OF_APPEAL": CLAIM_OF_APPEAL,
        "COA_BRIEF": COA_BRIEF,
        "EX_PARTE_OBJECTION": EX_PARTE_OBJECTION,
        "PPO_OBJECTION": PPO_OBJECTION,
        "FEDERAL_SERVICE": FEDERAL_SERVICE,
        "MSC_APPLICATION": MSC_APPLICATION,
        "MOTION_HEARING_NOTICE": MOTION_HEARING_NOTICE,
        "SUMMARY_DISPOSITION_RESPONSE": SUMMARY_DISPOSITION_RESPONSE,
        "ANSWER_TO_COMPLAINT": ANSWER_TO_COMPLAINT,
        "RECONSIDERATION": RECONSIDERATION,
        "COA_APPELLEE_BRIEF": COA_APPELLEE_BRIEF,
        "COA_REPLY_BRIEF": COA_REPLY_BRIEF,
    }


if __name__ == "__main__":
    import sys

    if len(sys.argv) >= 3:
        trigger = sys.argv[1]
        rule = sys.argv[2]
        court_arg = sys.argv[3] if len(sys.argv) > 3 else "circuit"

        try:
            days_val = int(rule)
        except ValueError:
            days_val = rule

        result = calculate_deadline(trigger, days_val, court_arg)
        print(f"Trigger date : {trigger}")
        print(f"Rule / days  : {rule}")
        print(f"Court        : {court_arg}")
        print(f"Deadline     : {result.isoformat()} ({result.strftime('%A, %B %d, %Y')})")
    else:
        print("Usage: python deadline_calculator.py <trigger_date> <days_or_constant> [court]")
        print(f"\nExample: python deadline_calculator.py 2025-06-01 MOTION_RESPONSE circuit")
        print(f"\nAvailable constants:")
        for name, days in get_all_constants().items():
            print(f"  {name}: {days} days")
