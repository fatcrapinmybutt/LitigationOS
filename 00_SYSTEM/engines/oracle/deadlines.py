#!/usr/bin/env python3
"""
Michigan Legal Deadline Calculator

Handles:
- Calendar day counting
- Business day counting (skip weekends)
- Michigan holiday handling (MCR 1.108)
- "Next business day" rule when deadline falls on weekend/holiday
- Service-by-mail +3 day extension (MCR 2.107(C)(3))
- COA/MSC specific deadline rules

Usage:
    from oracle.deadlines import MichiganCalendar, DeadlineCalculator

    cal = MichiganCalendar()
    calc = DeadlineCalculator()

    # Motion deadlines relative to hearing
    timeline = calc.motion_deadlines(date(2026, 4, 15))

    # Appeal deadlines from judgment
    timeline = calc.appeal_of_right_timeline(date(2026, 3, 1))

CLI:
    python deadlines.py motion --hearing 2026-04-15
    python deadlines.py appeal --judgment 2026-03-01
    python deadlines.py foc --recommendation 2026-03-15
    python deadlines.py coa-leave --order 2026-03-01
"""

import sys
import os
import json
import argparse
import logging
from datetime import date, timedelta
from typing import List, Dict, Optional

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Michigan Calendar
# ---------------------------------------------------------------------------

class MichiganCalendar:
    """Michigan court calendar with holiday and business-day logic (MCR 1.108)."""

    def _michigan_holidays(self, year: int) -> List[date]:
        """Compute Michigan court holidays for a given year.

        Includes all state holidays observed by Michigan courts.
        Floating holidays (e.g., MLK Day = 3rd Monday of January) are
        computed dynamically so this works for any year.
        """
        holidays: List[date] = []

        # Fixed-date holidays
        holidays.append(date(year, 1, 1))    # New Year's Day
        holidays.append(date(year, 7, 4))    # Independence Day
        holidays.append(date(year, 11, 11))  # Veterans Day
        holidays.append(date(year, 12, 24))  # Christmas Eve
        holidays.append(date(year, 12, 25))  # Christmas Day
        holidays.append(date(year, 12, 31))  # New Year's Eve

        # Nth-weekday helpers -----------------------------------------------
        def nth_weekday(year: int, month: int, weekday: int, n: int) -> date:
            """Return the nth occurrence of weekday in month/year.
            weekday: 0=Mon … 6=Sun.  n: 1-based.
            """
            first = date(year, month, 1)
            # days until first occurrence of weekday
            delta = (weekday - first.weekday()) % 7
            target = first + timedelta(days=delta + 7 * (n - 1))
            return target

        def last_weekday(year: int, month: int, weekday: int) -> date:
            """Return the last occurrence of weekday in month/year."""
            if month == 12:
                first_next = date(year + 1, 1, 1)
            else:
                first_next = date(year, month + 1, 1)
            last_day = first_next - timedelta(days=1)
            delta = (last_day.weekday() - weekday) % 7
            return last_day - timedelta(days=delta)

        # Floating holidays
        holidays.append(nth_weekday(year, 1, 0, 3))   # MLK Day — 3rd Mon Jan
        holidays.append(nth_weekday(year, 2, 0, 3))   # Presidents Day — 3rd Mon Feb
        holidays.append(last_weekday(year, 5, 0))      # Memorial Day — last Mon May
        holidays.append(nth_weekday(year, 9, 0, 1))   # Labor Day — 1st Mon Sep

        # Thanksgiving — 4th Thursday of November + day after
        thanksgiving = nth_weekday(year, 11, 3, 4)
        holidays.append(thanksgiving)
        holidays.append(thanksgiving + timedelta(days=1))

        # If a fixed holiday falls on Saturday → observed Friday;
        # on Sunday → observed Monday (federal observance rule used by MI courts)
        observed: List[date] = []
        for h in holidays:
            if h.weekday() == 5:  # Saturday
                observed.append(h - timedelta(days=1))
            elif h.weekday() == 6:  # Sunday
                observed.append(h + timedelta(days=1))
            else:
                observed.append(h)

        return sorted(set(observed))

    def holidays_for_year(self, year: int) -> List[date]:
        """Return sorted list of Michigan court holidays for *year*."""
        return self._michigan_holidays(year)

    def is_holiday(self, d: date) -> bool:
        """Return True if *d* is a Michigan court holiday."""
        return d in self._michigan_holidays(d.year)

    def is_business_day(self, d: date) -> bool:
        """Return True if *d* is a court business day (not weekend, not holiday)."""
        if d.weekday() >= 5:  # Saturday=5, Sunday=6
            return False
        return not self.is_holiday(d)

    def next_business_day(self, d: date) -> date:
        """If *d* falls on a weekend or holiday, advance to the next business day.

        Per MCR 1.108(1): when the last day of a period falls on a Saturday,
        Sunday, or legal holiday, the period runs until the next business day.
        """
        while not self.is_business_day(d):
            d += timedelta(days=1)
        return d

    def add_business_days(self, start: date, days: int) -> date:
        """Add *days* business days to *start* (skipping weekends/holidays)."""
        if days < 0:
            return self.subtract_business_days(start, abs(days))
        current = start
        added = 0
        while added < days:
            current += timedelta(days=1)
            if self.is_business_day(current):
                added += 1
        return current

    def subtract_business_days(self, start: date, days: int) -> date:
        """Subtract *days* business days from *start*."""
        if days < 0:
            return self.add_business_days(start, abs(days))
        current = start
        subtracted = 0
        while subtracted < days:
            current -= timedelta(days=1)
            if self.is_business_day(current):
                subtracted += 1
        return current

    def count_business_days(self, start: date, end: date) -> int:
        """Count business days between *start* (exclusive) and *end* (inclusive).

        If end < start the result is negative.
        """
        if start == end:
            return 0
        step = 1 if end > start else -1
        count = 0
        current = start
        while current != end:
            current += timedelta(days=step)
            if self.is_business_day(current):
                count += step
        return count


# ---------------------------------------------------------------------------
# Deadline Calculator
# ---------------------------------------------------------------------------

class DeadlineCalculator:
    """Compute litigation deadlines using Michigan Court Rules.

    All public methods return ``List[Dict]`` timelines, where each dict
    contains at minimum: event, date (ISO string), days_from_ref, rule.
    """

    def __init__(self, calendar: Optional[MichiganCalendar] = None):
        self.cal = calendar or MichiganCalendar()

    # -- helpers -------------------------------------------------------------

    def _fmt(self, d: date) -> str:
        return d.isoformat()

    def _before(self, ref: date, calendar_days: int, *, business: bool = False) -> date:
        """Compute a date *calendar_days* before *ref*, optionally in business days."""
        if business:
            return self.cal.subtract_business_days(ref, calendar_days)
        raw = ref - timedelta(days=calendar_days)
        return self.cal.next_business_day(raw)

    def _after(self, ref: date, calendar_days: int, *, business: bool = False) -> date:
        """Compute a date *calendar_days* after *ref*, optionally in business days."""
        if business:
            return self.cal.add_business_days(ref, calendar_days)
        raw = ref + timedelta(days=calendar_days)
        return self.cal.next_business_day(raw)

    # -- generic compute -----------------------------------------------------

    def compute(
        self,
        trigger_event: str,
        reference_date: Optional[date] = None,
        rules: Optional[List[Dict]] = None,
    ) -> List[Dict]:
        """Compute deadlines from a trigger event and optional rule list.

        If *rules* is ``None``, delegates to the appropriate pre-built
        timeline based on *trigger_event*.  Recognised triggers:

        - ``motion_filing``, ``motion_hearing`` → :meth:`motion_deadlines`
        - ``appeal_of_right`` → :meth:`appeal_of_right_timeline`
        - ``leave_to_appeal_coa`` → :meth:`leave_to_appeal_coa_timeline`
        - ``leave_to_appeal_msc`` → :meth:`leave_to_appeal_msc_timeline`
        - ``foc_objection`` → :meth:`foc_objection_timeline`
        - ``contempt`` → :meth:`contempt_motion_timeline`

        When *rules* is provided, each dict should have keys:
        ``direction`` ("before"/"after"), ``days`` (int), ``description``,
        ``rule`` (MCR reference), and optionally ``business_days`` (bool).
        """
        ref = reference_date or date.today()

        if rules is not None:
            timeline: List[Dict] = []
            for r in rules:
                direction = r.get("direction", "before")
                days = int(r.get("days", 0))
                biz = r.get("business_days", False)
                if direction == "before":
                    computed = self._before(ref, days, business=biz)
                else:
                    computed = self._after(ref, days, business=biz)
                timeline.append({
                    "event": r.get("description", ""),
                    "date": self._fmt(computed),
                    "days_from_ref": -days if direction == "before" else days,
                    "rule": r.get("rule", ""),
                })
            timeline.sort(key=lambda x: x["date"])
            return timeline

        # delegate to pre-built timelines
        dispatch = {
            "motion_filing": lambda: self.motion_deadlines(ref),
            "motion_hearing": lambda: self.motion_deadlines(ref),
            "appeal_of_right": lambda: self.appeal_of_right_timeline(ref),
            "leave_to_appeal_coa": lambda: self.leave_to_appeal_coa_timeline(ref),
            "leave_to_appeal_msc": lambda: self.leave_to_appeal_msc_timeline(ref),
            "foc_objection": lambda: self.foc_objection_timeline(ref),
            "contempt": lambda: self.contempt_motion_timeline(ref),
        }
        handler = dispatch.get(trigger_event)
        if handler:
            return handler()

        logger.warning("Unknown trigger event %r — returning empty timeline", trigger_event)
        return []

    # -- pre-built timelines -------------------------------------------------

    def motion_deadlines(self, hearing_date: date) -> List[Dict]:
        """MCR 2.119 motion practice timeline relative to a hearing date.

        Returns deadlines for filing, service, response, and reply briefs.
        Assumes service by mail (+3 days per MCR 2.107(C)(3)).
        """
        serve_date = self._before(hearing_date, 9 + 3)  # 9 days + 3 mail days
        file_date = serve_date  # typically file and serve same day
        response_due = self._before(hearing_date, 7)
        reply_due = self._before(hearing_date, 4)  # MCR 2.119(C)(2) practice

        return [
            {
                "event": "File motion and brief",
                "date": self._fmt(file_date),
                "days_from_ref": (file_date - hearing_date).days,
                "rule": "MCR 2.119(A)",
            },
            {
                "event": "Serve opposing party (mail — includes +3 days)",
                "date": self._fmt(serve_date),
                "days_from_ref": (serve_date - hearing_date).days,
                "rule": "MCR 2.107(C)(3)",
            },
            {
                "event": "Response brief due",
                "date": self._fmt(response_due),
                "days_from_ref": (response_due - hearing_date).days,
                "rule": "MCR 2.119(C)(2)",
            },
            {
                "event": "Reply brief due (if filing)",
                "date": self._fmt(reply_due),
                "days_from_ref": (reply_due - hearing_date).days,
                "rule": "MCR 2.119(C)(2)",
            },
            {
                "event": "HEARING",
                "date": self._fmt(hearing_date),
                "days_from_ref": 0,
                "rule": "",
            },
        ]

    def motion_to_modify_custody_timeline(self, hearing_date: date) -> List[Dict]:
        """Full timeline for a custody modification motion (MCR 3.206 + 2.119).

        Includes FOC requirements and SCAO form deadlines.
        """
        base = self.motion_deadlines(hearing_date)
        file_date = date.fromisoformat(base[0]["date"])

        # Insert custody-specific steps
        extra = [
            {
                "event": "Complete FOC 89 Verified Statement",
                "date": self._fmt(file_date),
                "days_from_ref": (file_date - hearing_date).days,
                "rule": "MCR 3.206(A)",
            },
            {
                "event": "Provide FOC copy of all filed documents",
                "date": self._fmt(file_date),
                "days_from_ref": (file_date - hearing_date).days,
                "rule": "MCR 3.203",
            },
        ]
        combined = extra + base
        combined.sort(key=lambda x: x["date"])
        return combined

    def appeal_of_right_timeline(self, judgment_date: date) -> List[Dict]:
        """MCR 7.204 appeal of right from Circuit Court to COA.

        21 calendar-day jurisdictional deadline for claim of appeal.
        """
        claim_deadline = self._after(judgment_date, 21)
        transcript_order = self._after(judgment_date, 14)
        appellant_brief = self._after(claim_deadline, 56)
        appellee_brief = self._after(appellant_brief, 42)
        reply_brief = self._after(appellee_brief, 21)

        return [
            {
                "event": "Entry of judgment/order",
                "date": self._fmt(judgment_date),
                "days_from_ref": 0,
                "rule": "",
            },
            {
                "event": "Order transcripts (recommended)",
                "date": self._fmt(transcript_order),
                "days_from_ref": 14,
                "rule": "MCR 7.210(B)",
            },
            {
                "event": "File Claim of Appeal — JURISDICTIONAL",
                "date": self._fmt(claim_deadline),
                "days_from_ref": 21,
                "rule": "MCR 7.204(A)(1)",
            },
            {
                "event": "Appellant brief due",
                "date": self._fmt(appellant_brief),
                "days_from_ref": 77,
                "rule": "MCR 7.212(A)(1)",
            },
            {
                "event": "Appellee brief due",
                "date": self._fmt(appellee_brief),
                "days_from_ref": 119,
                "rule": "MCR 7.212(A)(2)",
            },
            {
                "event": "Reply brief due (optional)",
                "date": self._fmt(reply_brief),
                "days_from_ref": 140,
                "rule": "MCR 7.212(G)",
            },
        ]

    def leave_to_appeal_coa_timeline(self, order_date: date) -> List[Dict]:
        """MCR 7.205 application for leave to appeal to COA.

        21 calendar-day deadline (may be extended for good cause).
        """
        app_deadline = self._after(order_date, 21)
        answer_due = self._after(app_deadline, 21)

        return [
            {
                "event": "Entry of order",
                "date": self._fmt(order_date),
                "days_from_ref": 0,
                "rule": "",
            },
            {
                "event": "File Application for Leave to Appeal",
                "date": self._fmt(app_deadline),
                "days_from_ref": 21,
                "rule": "MCR 7.205(A)",
            },
            {
                "event": "Answer to application due",
                "date": self._fmt(answer_due),
                "days_from_ref": 42,
                "rule": "MCR 7.205(E)",
            },
        ]

    def leave_to_appeal_msc_timeline(self, coa_decision_date: date) -> List[Dict]:
        """MCR 7.305 application for leave to appeal to MSC.

        42 calendar-day deadline from COA decision.
        """
        app_deadline = self._after(coa_decision_date, 42)
        answer_due = self._after(app_deadline, 28)

        return [
            {
                "event": "COA decision issued",
                "date": self._fmt(coa_decision_date),
                "days_from_ref": 0,
                "rule": "",
            },
            {
                "event": "File Application for Leave to Appeal (MSC)",
                "date": self._fmt(app_deadline),
                "days_from_ref": 42,
                "rule": "MCR 7.305(C)(1)",
            },
            {
                "event": "Answer to application due",
                "date": self._fmt(answer_due),
                "days_from_ref": 70,
                "rule": "MCR 7.305(H)(1)",
            },
        ]

    def foc_objection_timeline(self, recommendation_date: date) -> List[Dict]:
        """FOC objection and de novo hearing timeline.

        21-day objection period per MCL 552.507(5).
        """
        objection_deadline = self._after(recommendation_date, 21)
        hearing_request = objection_deadline  # filed with objection

        return [
            {
                "event": "FOC recommendation/report issued",
                "date": self._fmt(recommendation_date),
                "days_from_ref": 0,
                "rule": "",
            },
            {
                "event": "File objection to FOC recommendation",
                "date": self._fmt(objection_deadline),
                "days_from_ref": 21,
                "rule": "MCL 552.507(5)",
            },
            {
                "event": "Request de novo hearing (with objection)",
                "date": self._fmt(hearing_request),
                "days_from_ref": 21,
                "rule": "MCR 3.218(D)",
            },
        ]

    def contempt_motion_timeline(self, hearing_date: date) -> List[Dict]:
        """Contempt motion timeline.

        Uses standard MCR 2.119 motion practice plus personal-service
        requirement for contempt proceedings.
        """
        serve_date = self._before(hearing_date, 14)  # conservative — personal service
        file_date = serve_date
        response_due = self._before(hearing_date, 7)

        return [
            {
                "event": "File Motion and Order to Show Cause",
                "date": self._fmt(file_date),
                "days_from_ref": (file_date - hearing_date).days,
                "rule": "MCR 3.606",
            },
            {
                "event": "Personal service on respondent",
                "date": self._fmt(serve_date),
                "days_from_ref": (serve_date - hearing_date).days,
                "rule": "MCR 2.105(A)(1)",
            },
            {
                "event": "Response due",
                "date": self._fmt(response_due),
                "days_from_ref": (response_due - hearing_date).days,
                "rule": "MCR 2.119(C)(2)",
            },
            {
                "event": "HEARING (Show Cause)",
                "date": self._fmt(hearing_date),
                "days_from_ref": 0,
                "rule": "",
            },
        ]

    def service_deadline(self, method: str, hearing_date: date) -> Dict:
        """Compute last day to serve based on method and hearing date.

        Args:
            method: ``"personal"``, ``"mail"``, or ``"email"``
            hearing_date: the date of the hearing

        Returns:
            Dict with serve_by date and rule citations.
        """
        base_days = 9  # MCR 2.119(C)(1) — 9 days before hearing

        if method == "mail":
            base_days += 3  # MCR 2.107(C)(3) mail extension
            rule = "MCR 2.119(C)(1) + MCR 2.107(C)(3)"
            note = "9 days before hearing + 3 days for mailing"
        elif method == "email":
            base_days += 1  # e-service: +1 day courtesy
            rule = "MCR 2.119(C)(1) + MCR 2.107(C)(4)"
            note = "9 days before hearing + 1 day for e-service"
        else:
            rule = "MCR 2.119(C)(1)"
            note = "9 days before hearing (personal service)"

        serve_by = self._before(hearing_date, base_days)

        return {
            "method": method,
            "serve_by": self._fmt(serve_by),
            "hearing_date": self._fmt(hearing_date),
            "total_days_before": base_days,
            "rule": rule,
            "note": note,
        }


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def _parse_date(s: str) -> date:
    """Parse an ISO date string (YYYY-MM-DD)."""
    return date.fromisoformat(s)


def main() -> None:
    sys.stdout = open(sys.stdout.fileno(), mode="w", encoding="utf-8", errors="replace")

    parser = argparse.ArgumentParser(
        description="Michigan Legal Deadline Calculator",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=(
            "Examples:\n"
            "  python deadlines.py motion --hearing 2026-04-15\n"
            "  python deadlines.py appeal --judgment 2026-03-01\n"
            "  python deadlines.py foc --recommendation 2026-03-15\n"
            "  python deadlines.py coa-leave --order 2026-03-01\n"
            "  python deadlines.py msc-leave --decision 2026-06-01\n"
            "  python deadlines.py contempt --hearing 2026-04-15\n"
            "  python deadlines.py holidays --year 2026\n"
        ),
    )
    sub = parser.add_subparsers(dest="command")

    # motion
    p_motion = sub.add_parser("motion", help="MCR 2.119 motion practice deadlines")
    p_motion.add_argument("--hearing", required=True, help="Hearing date (YYYY-MM-DD)")
    p_motion.add_argument("--custody", action="store_true", help="Include custody-specific steps")

    # appeal
    p_appeal = sub.add_parser("appeal", help="Appeal of right (MCR 7.204) timeline")
    p_appeal.add_argument("--judgment", required=True, help="Judgment date (YYYY-MM-DD)")

    # foc
    p_foc = sub.add_parser("foc", help="FOC objection timeline")
    p_foc.add_argument("--recommendation", required=True, help="Recommendation date (YYYY-MM-DD)")

    # coa-leave
    p_coa = sub.add_parser("coa-leave", help="Application for leave to appeal — COA (MCR 7.205)")
    p_coa.add_argument("--order", required=True, help="Order date (YYYY-MM-DD)")

    # msc-leave
    p_msc = sub.add_parser("msc-leave", help="Application for leave to appeal — MSC (MCR 7.305)")
    p_msc.add_argument("--decision", required=True, help="COA decision date (YYYY-MM-DD)")

    # contempt
    p_contempt = sub.add_parser("contempt", help="Contempt motion timeline")
    p_contempt.add_argument("--hearing", required=True, help="Hearing date (YYYY-MM-DD)")

    # holidays
    p_holidays = sub.add_parser("holidays", help="List Michigan court holidays for a year")
    p_holidays.add_argument("--year", type=int, default=date.today().year, help="Year (default: current)")

    args = parser.parse_args()
    if not args.command:
        parser.print_help()
        sys.exit(1)

    calc = DeadlineCalculator()

    if args.command == "motion":
        hearing = _parse_date(args.hearing)
        if args.custody:
            timeline = calc.motion_to_modify_custody_timeline(hearing)
        else:
            timeline = calc.motion_deadlines(hearing)
    elif args.command == "appeal":
        timeline = calc.appeal_of_right_timeline(_parse_date(args.judgment))
    elif args.command == "foc":
        timeline = calc.foc_objection_timeline(_parse_date(args.recommendation))
    elif args.command == "coa-leave":
        timeline = calc.leave_to_appeal_coa_timeline(_parse_date(args.order))
    elif args.command == "msc-leave":
        timeline = calc.leave_to_appeal_msc_timeline(_parse_date(args.decision))
    elif args.command == "contempt":
        timeline = calc.contempt_motion_timeline(_parse_date(args.hearing))
    elif args.command == "holidays":
        cal = MichiganCalendar()
        holidays = cal.holidays_for_year(args.year)
        print(f"\nMichigan Court Holidays — {args.year}")
        print("=" * 40)
        for h in holidays:
            print(f"  {h.isoformat()}  ({h.strftime('%A')})")
        sys.exit(0)
    else:
        parser.print_help()
        sys.exit(1)

    # Print timeline
    print(f"\n{'='*60}")
    print(f"  {args.command.upper()} TIMELINE")
    print(f"{'='*60}")
    for entry in timeline:
        marker = ">>>" if entry["event"].startswith("HEARING") or "JURISDICTIONAL" in entry["event"] else "   "
        rule_tag = f"  [{entry['rule']}]" if entry["rule"] else ""
        print(f"  {marker} {entry['date']}  {entry['event']}{rule_tag}")
    print()


if __name__ == "__main__":
    main()
