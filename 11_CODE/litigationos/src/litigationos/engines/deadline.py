"""Michigan deadline calculation engine.

Computes filing deadlines based on MCR rules, adjusts for weekends and
Michigan court holidays, and persists/queries deadlines in the database.
"""

from __future__ import annotations

import logging
from datetime import date, timedelta
from typing import TYPE_CHECKING, Optional

if TYPE_CHECKING:
    from litigationos.db.connection import DatabaseManager

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Priority constants
# ---------------------------------------------------------------------------

PRIORITY_CRITICAL = "critical"
PRIORITY_HIGH = "high"
PRIORITY_MEDIUM = "medium"
PRIORITY_LOW = "low"

# ---------------------------------------------------------------------------
# Michigan court holidays  (2025-2027)
# ---------------------------------------------------------------------------


def _michigan_holidays() -> set[date]:
    """Return a set of Michigan court-observed holidays for 2025-2027."""
    holidays: set[date] = set()
    for year in (2025, 2026, 2027):
        holidays.add(date(year, 1, 1))   # New Year's Day

        # MLK Day — 3rd Monday in January
        jan1 = date(year, 1, 1)
        first_mon = jan1 + timedelta(days=(7 - jan1.weekday()) % 7)
        if first_mon.month != 1:
            first_mon = date(year, 1, (8 - jan1.weekday()) % 7 or 7)
        mlk = date(year, 1, 1)
        # Find the 3rd Monday
        count = 0
        d = date(year, 1, 1)
        while count < 3:
            if d.weekday() == 0:  # Monday
                count += 1
                if count == 3:
                    break
            d += timedelta(days=1)
        holidays.add(d)

        # Presidents' Day — 3rd Monday in February
        count = 0
        d = date(year, 2, 1)
        while count < 3:
            if d.weekday() == 0:
                count += 1
                if count == 3:
                    break
            d += timedelta(days=1)
        holidays.add(d)

        # Memorial Day — last Monday in May
        d = date(year, 5, 31)
        while d.weekday() != 0:
            d -= timedelta(days=1)
        holidays.add(d)

        # Independence Day
        holidays.add(date(year, 7, 4))

        # Labor Day — 1st Monday in September
        d = date(year, 9, 1)
        while d.weekday() != 0:
            d += timedelta(days=1)
        holidays.add(d)

        # Veterans Day
        holidays.add(date(year, 11, 11))

        # Thanksgiving — 4th Thursday in November
        count = 0
        d = date(year, 11, 1)
        while count < 4:
            if d.weekday() == 3:  # Thursday
                count += 1
                if count == 4:
                    break
            d += timedelta(days=1)
        holidays.add(d)

        # Christmas Day
        holidays.add(date(year, 12, 25))

    return holidays


_HOLIDAYS: set[date] = _michigan_holidays()

# ---------------------------------------------------------------------------
# MCR deadline rules  (filing_type → (calendar_days, rule_basis, description, priority))
# ---------------------------------------------------------------------------

_MCR_DEADLINES: dict[str, dict[str, tuple[int, str, str, str]]] = {
    # circuit court deadlines
    "circuit": {
        "answer_complaint": (
            21,
            "MCR 2.108",
            "Answer or respond to complaint within 21 days of service",
            PRIORITY_CRITICAL,
        ),
        "motion_service": (
            -9,  # negative = days *before* hearing
            "MCR 2.119(C)(1)",
            "Serve motion and brief at least 9 days before hearing",
            PRIORITY_HIGH,
        ),
        "motion_response": (
            -5,
            "MCR 2.119(C)(1)",
            "Serve response brief at least 5 days before hearing",
            PRIORITY_HIGH,
        ),
        "motion_reply": (
            -3,
            "MCR 2.119(C)(1)",
            "Serve reply brief at least 3 days before hearing",
            PRIORITY_MEDIUM,
        ),
    },
    # Court of Appeals
    "coa": {
        "appellant_brief": (
            56,
            "MCR 7.212(A)(1)",
            "File appellant's brief within 56 days after claim of appeal",
            PRIORITY_CRITICAL,
        ),
        "appellee_brief": (
            35,
            "MCR 7.212(A)(1)",
            "File appellee's brief within 35 days after service of appellant's brief",
            PRIORITY_HIGH,
        ),
        "reply_brief": (
            21,
            "MCR 7.212(A)(1)",
            "File reply brief within 21 days after service of appellee's brief",
            PRIORITY_MEDIUM,
        ),
    },
    # Supreme Court
    "supreme": {
        "msc_application": (
            56,
            "MCR 7.305(C)(1)",
            "File application for leave to appeal within 56 days",
            PRIORITY_CRITICAL,
        ),
        "msc_leave_application": (
            42,
            "MCR 7.302",
            "File application for leave to appeal within 42 days of COA decision",
            PRIORITY_CRITICAL,
        ),
        "msc_cross_application": (
            21,
            "MCR 7.303",
            "File cross-application within 21 days of service of application",
            PRIORITY_HIGH,
        ),
        "msc_response": (
            28,
            "MCR 7.304",
            "File response to application within 28 days of service",
            PRIORITY_HIGH,
        ),
    },
}


class DeadlineEngine:
    """Calculate and manage Michigan court deadlines.

    Handles MCR-based deadline computation, weekend/holiday adjustment,
    and CRUD operations on the ``deadlines`` table.
    """

    def __init__(self, db: "DatabaseManager") -> None:
        self._db = db

    # ------------------------------------------------------------------
    # Date helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _is_business_day(d: date) -> bool:
        """Return True if *d* is a weekday and not a Michigan court holiday."""
        return d.weekday() < 5 and d not in _HOLIDAYS

    @staticmethod
    def _next_business_day(d: date) -> date:
        """Advance *d* to the next business day if it falls on a weekend or holiday."""
        while not DeadlineEngine._is_business_day(d):
            d += timedelta(days=1)
        return d

    # ------------------------------------------------------------------
    # Core calculation
    # ------------------------------------------------------------------

    def calculate_deadline(
        self,
        filing_type: str,
        trigger_date: date | str,
        court_type: str = "circuit",
    ) -> Optional[dict]:
        """Calculate a deadline based on MCR rules.

        Args:
            filing_type: Key into the deadline rules (e.g. ``"answer_complaint"``).
            trigger_date: The event date that starts the clock.  Accepts
                          :class:`date` or ISO-format string.
            court_type: ``"circuit"``, ``"coa"``, or ``"supreme"``.

        Returns:
            ``{"due_date": date, "rule_basis": str, "description": str,
              "priority": str, "calendar_days": int}`` or ``None``.
        """
        if isinstance(trigger_date, str):
            trigger_date = date.fromisoformat(trigger_date)

        court_rules = _MCR_DEADLINES.get(court_type, {})
        rule = court_rules.get(filing_type)
        if rule is None:
            logger.warning(
                "No deadline rule for filing_type=%s court_type=%s",
                filing_type,
                court_type,
            )
            return None

        calendar_days, rule_basis, description, priority = rule
        raw_date = trigger_date + timedelta(days=calendar_days)
        due = self._next_business_day(raw_date)

        return {
            "due_date": due,
            "rule_basis": rule_basis,
            "description": description,
            "priority": priority,
            "calendar_days": calendar_days,
        }

    # ------------------------------------------------------------------
    # CRUD
    # ------------------------------------------------------------------

    def add_deadline(
        self,
        case_id: int,
        title: str,
        due_date: date | str,
        filing_type: Optional[str] = None,
        court: Optional[str] = None,
        priority: str = PRIORITY_MEDIUM,
        rule_basis: Optional[str] = None,
        filing_id: Optional[int] = None,
        notes: Optional[str] = None,
    ) -> int:
        """Insert a new deadline and return its ``id``.

        The ``due_date`` is automatically adjusted to the next business day
        if it falls on a weekend or Michigan court holiday.

        Args:
            case_id: FK to the cases table.
            title: Human-readable deadline title.
            due_date: Target date (adjusted for holidays/weekends).
            filing_type: Optional filing type tag.
            court: Optional court type for context.
            priority: One of ``critical``, ``high``, ``medium``, ``low``.
            rule_basis: MCR rule citation.
            filing_id: Optional FK to filings table.
            notes: Free-text notes.

        Returns:
            The newly created deadline row id.
        """
        if isinstance(due_date, str):
            due_date = date.fromisoformat(due_date)

        due_date = self._next_business_day(due_date)

        cursor = self._db.execute(
            "INSERT INTO deadlines "
            "(case_id, filing_id, title, due_date, rule_basis, status, priority, notes) "
            "VALUES (?, ?, ?, ?, ?, 'pending', ?, ?)",
            (
                case_id,
                filing_id,
                title,
                due_date.isoformat(),
                rule_basis,
                priority,
                notes,
            ),
        )
        logger.info(
            "Added deadline '%s' due %s (priority=%s) for case %d",
            title,
            due_date.isoformat(),
            priority,
            case_id,
        )
        return cursor.lastrowid  # type: ignore[return-value]

    def get_upcoming(
        self, case_id: Optional[int] = None, days: int = 30
    ) -> list[dict]:
        """Return pending deadlines within the next *days* calendar days.

        Args:
            case_id: Optional case filter.  ``None`` returns all cases.
            days: Look-ahead window (default 30).

        Returns:
            List of deadline dicts sorted by ``due_date`` ascending.
        """
        if case_id is not None:
            rows = self._db.fetchall(
                "SELECT * FROM deadlines "
                "WHERE case_id = ? AND status = 'pending' "
                "AND due_date >= date('now') "
                "AND due_date <= date('now', '+' || ? || ' days') "
                "ORDER BY due_date ASC",
                (case_id, days),
            )
        else:
            rows = self._db.fetchall(
                "SELECT * FROM deadlines "
                "WHERE status = 'pending' "
                "AND due_date >= date('now') "
                "AND due_date <= date('now', '+' || ? || ' days') "
                "ORDER BY due_date ASC",
                (days,),
            )
        return [dict(r) for r in rows]

    def get_overdue(self, case_id: Optional[int] = None) -> list[dict]:
        """Get overdue deadlines, optionally filtered by case."""
        if case_id:
            rows = self._db.fetchall(
                "SELECT * FROM deadlines "
                "WHERE case_id = ? AND status = 'pending' AND due_date < date('now') "
                "ORDER BY due_date ASC",
                (case_id,),
            )
        else:
            rows = self._db.fetchall(
                "SELECT * FROM deadlines "
                "WHERE status = 'pending' AND due_date < date('now') "
                "ORDER BY due_date ASC",
            )
        return [dict(r) for r in rows]

    def check_conflicts(self, target_date: date | str) -> dict:
        """Check whether a date falls on a weekend or Michigan court holiday.

        Args:
            target_date: Date to check.

        Returns:
            ``{"date": str, "is_business_day": bool, "is_weekend": bool,
              "is_holiday": bool, "next_business_day": str}``
        """
        if isinstance(target_date, str):
            target_date = date.fromisoformat(target_date)

        is_weekend = target_date.weekday() >= 5
        is_holiday = target_date in _HOLIDAYS
        nbd = self._next_business_day(target_date)

        return {
            "date": target_date.isoformat(),
            "is_business_day": self._is_business_day(target_date),
            "is_weekend": is_weekend,
            "is_holiday": is_holiday,
            "next_business_day": nbd.isoformat(),
        }
