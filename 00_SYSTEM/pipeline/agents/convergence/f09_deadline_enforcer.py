"""
DELTA9 — F09 Deadline Enforcer
Convergence Tier · MAX LEVEL 9999++

Monitors filing deadlines, calculates urgency using MCR computation rules,
and generates priority-ordered urgency alerts.

Michigan Court Rule computation:
  MCR 1.108(1): Exclude day of event, include last day
  MCR 1.108(2): If last day is weekend/holiday, extend to next business day
  MCR 2.107(C)(3): +3 days for mail service, +1 day for electronic
  MCR 2.119(C)(1): Motion hearing = 9 days before (14 days notice - 5 if served by mail)

Urgency scoring:
  CRITICAL (90-100): ≤3 calendar days or OVERDUE
  HIGH (70-89): 4-7 calendar days
  MEDIUM (40-69): 8-21 calendar days
  LOW (0-39): >21 calendar days

Outputs:
  - deadline_urgency_report.json: all deadlines with urgency scores
  - Logs CRITICAL/OVERDUE to agent_log for escalation
"""
import json
import sqlite3
import time
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, List, Optional

from ..agent_base import Agent9999
from ..agent_models import SkipItemError, FatalAgentError, CHECKPOINT_DIR

# MCR service add-on days
_SERVICE_ADDONS = {
    "mail": 3,          # MCR 2.107(C)(3)
    "electronic": 1,    # MCR 2.107(C)(3) — e-service
    "personal": 0,      # MCR 2.107(C)(1) — hand delivery
    "fax": 1,           # MCR 2.107(C)(3)
}

# Standard MCR deadlines (days before hearing / after event)
_MCR_DEADLINES = {
    "motion_hearing_notice": 9,    # MCR 2.119(C)(1) — days before hearing
    "motion_response": 7,          # MCR 2.119(C)(2) — days before hearing
    "motion_reply": 4,             # MCR 2.119(C)(3) — days before hearing
    "answer_complaint": 21,        # MCR 2.108(A)(1) — after service
    "answer_complaint_mail": 28,   # MCR 2.108(A)(2) — served by mail
    "appeal_claim_right": 21,      # MCR 7.204(A)(1) — after entry of order
    "appeal_leave": 21,            # MCR 7.205(A) — after entry of order
    "disqualification": 14,        # MCR 2.003(D)(1) — after discovery of grounds
    "discovery_interrogatories": 28,  # MCR 2.309(B)(2)
    "discovery_rfp": 28,           # MCR 2.310(B)(2)
    "discovery_rfa": 28,           # MCR 2.312(B)(1)
    "scheduling_order": 91,        # MCR 2.401(B)(2)(a) — 91 days after filing
    "pretrial_conference": 14,     # MCR 2.401(G) — before trial
    "coa_brief": 56,              # MCR 7.212(A)(1)(a) — 56 days after claim
    "coa_appendix": 28,           # MCR 7.212(C)(1) — with brief
    "msc_application": 56,        # MCR 7.305(C)(2) — after COA decision
    "void_judgment": 365,          # MCR 2.612(C)(1)(a-c) — reasonable time
    "sol_defamation": 365,         # MCL 600.5805(2) — 1 year
    "sol_tort_general": 1095,      # MCL 600.5805(10) — 3 years
    "sol_fraud": 2190,             # MCL 600.5813 — 6 years
    "sol_contract": 2190,          # MCL 600.5807(8) — 6 years
}

# Michigan state holidays (2026)
_MI_HOLIDAYS_2026 = {
    "2026-01-01", "2026-01-19", "2026-02-16", "2026-05-25",
    "2026-07-04", "2026-09-07", "2026-10-12", "2026-11-11",
    "2026-11-26", "2026-11-27", "2026-12-25",
}


def _is_business_day(dt: datetime) -> bool:
    """Check if a date is a Michigan business day."""
    if dt.weekday() >= 5:  # Saturday=5, Sunday=6
        return False
    if dt.strftime("%Y-%m-%d") in _MI_HOLIDAYS_2026:
        return False
    return True


def _next_business_day(dt: datetime) -> datetime:
    """MCR 1.108(2): If deadline falls on non-business day, extend to next."""
    while not _is_business_day(dt):
        dt += timedelta(days=1)
    return dt


def _compute_urgency(days_remaining: int) -> tuple:
    """Compute urgency score and label from days remaining."""
    if days_remaining < 0:
        return (100, "OVERDUE")
    elif days_remaining <= 3:
        return (95 - days_remaining, "CRITICAL")
    elif days_remaining <= 7:
        return (85 - (days_remaining - 4) * 4, "HIGH")
    elif days_remaining <= 21:
        return (65 - (days_remaining - 8) * 2, "MEDIUM")
    else:
        return (max(35 - (days_remaining - 21), 0), "LOW")


class DeadlineEnforcer(Agent9999):
    """Monitors deadlines and computes MCR-aware urgency scores."""

    def __init__(self):
        super().__init__(agent_id="F09-DEADLINES")
        self._deadline_results: List[Dict] = []
        self._central_conn: Optional[sqlite3.Connection] = None

    def _validate_preconditions(self) -> None:
        central_path = Path(r"C:\Users\andre\LitigationOS\litigation_context.db")
        if not central_path.exists():
            raise FatalAgentError("litigation_context.db not found")

        try:
            self._central_conn = sqlite3.connect(str(central_path), timeout=30)
            self._central_conn.execute("PRAGMA busy_timeout=60000")
            self._central_conn.execute("PRAGMA journal_mode=WAL")
            self._central_conn.row_factory = sqlite3.Row

            # Check if deadlines table exists
            row = self._central_conn.execute(
                "SELECT name FROM sqlite_master WHERE type='table' AND name='deadlines'"
            ).fetchone()
            if not row:
                # Try filing_readiness as fallback
                row2 = self._central_conn.execute(
                    "SELECT name FROM sqlite_master WHERE type='table' AND name='filing_readiness'"
                ).fetchone()
                if not row2:
                    raise FatalAgentError("Neither deadlines nor filing_readiness table found")
        except FatalAgentError:
            raise
        except Exception as e:
            raise FatalAgentError(f"Cannot connect to central DB: {e}")

    def _get_work_items(self) -> list:
        """Gather all deadline sources: DB deadlines + known filing schedule."""
        items = []

        # 1. Query deadlines table
        try:
            tables = {r[0] for r in self._central_conn.execute(
                "SELECT name FROM sqlite_master WHERE type='table'"
            ).fetchall()}

            if "deadlines" in tables:
                # Discover columns first (schema evolves)
                cols = [c[1] for c in self._central_conn.execute(
                    "PRAGMA table_info(deadlines)"
                ).fetchall()]

                rows = self._central_conn.execute("SELECT * FROM deadlines").fetchall()
                for row in rows:
                    items.append({"source": "db_deadlines", "data": dict(row)})
        except Exception as e:
            self._log("WARN", f"Error reading deadlines table: {e}")

        # 2. Add known filing deadlines from the plan
        known_deadlines = [
            {
                "name": "COA 366810 Record Appendix",
                "due_date": "2026-03-10",
                "court": "Michigan Court of Appeals",
                "filing_type": "coa_appendix",
                "service_method": "electronic",
                "case_number": "COA 366810",
            },
            {
                "name": "McNeill Disqualification Motion",
                "due_date": "2026-03-15",
                "court": "14th Circuit Court",
                "filing_type": "disqualification",
                "service_method": "electronic",
                "case_number": "2024-001507-DC",
            },
            {
                "name": "Emergency Motion Restore Parenting Time",
                "due_date": "2026-03-01",  # OVERDUE
                "court": "14th Circuit Court",
                "filing_type": "motion_hearing_notice",
                "service_method": "electronic",
                "case_number": "2024-001507-DC",
            },
            {
                "name": "COA Appellant Brief",
                "due_date": "2026-04-15",
                "court": "Michigan Court of Appeals",
                "filing_type": "coa_brief",
                "service_method": "electronic",
                "case_number": "COA 366810",
            },
            {
                "name": "Defamation SOL Expiration",
                "due_date": "2027-02-01",
                "court": "14th Circuit Court",
                "filing_type": "sol_defamation",
                "service_method": "N/A",
                "case_number": "NEW",
            },
        ]
        for kd in known_deadlines:
            items.append({"source": "known_schedule", "data": kd})

        self._log("SCAN", f"Found {len(items)} deadlines to evaluate")
        return items

    def _process_item(self, item: Any) -> None:
        """Evaluate a single deadline."""
        if isinstance(item, dict):
            source = item.get("source", "unknown")
            data = item.get("data", {})
        else:
            raise SkipItemError(f"Unexpected item type: {type(item)}")

        # Extract due date
        due_str = None
        name = "Unknown"

        if source == "known_schedule":
            due_str = data.get("due_date")
            name = data.get("name", "Unknown")
        elif source == "db_deadlines":
            # Try common column names
            for col in ("due_date_iso", "due_date", "deadline_date", "date"):
                if col in data and data[col]:
                    due_str = str(data[col])
                    break
            for col in ("name", "title", "description", "vehicle_name", "filing_type"):
                if col in data and data[col]:
                    name = str(data[col])
                    break

        if not due_str:
            raise SkipItemError(f"No due date for: {name}")

        # Parse date
        try:
            due_date = datetime.strptime(due_str[:10], "%Y-%m-%d")
        except (ValueError, TypeError) as e:
            raise SkipItemError(f"Cannot parse date '{due_str}' for {name}: {e}")

        # Apply MCR 1.108(2) — business day extension
        adjusted_due = _next_business_day(due_date)

        # Apply service add-on if applicable
        service_method = data.get("service_method", "electronic")
        addon = _SERVICE_ADDONS.get(service_method, 0)
        if addon:
            adjusted_due += timedelta(days=addon)
            adjusted_due = _next_business_day(adjusted_due)

        # Calculate days remaining
        now = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
        days_remaining = (adjusted_due - now).days
        urgency_score, urgency_label = _compute_urgency(days_remaining)

        result = {
            "name": name,
            "due_date_original": due_str,
            "due_date_adjusted": adjusted_due.strftime("%Y-%m-%d"),
            "days_remaining": days_remaining,
            "urgency_score": urgency_score,
            "urgency_label": urgency_label,
            "service_method": service_method,
            "service_addon_days": addon,
            "court": data.get("court", "Unknown"),
            "case_number": data.get("case_number", "Unknown"),
            "source": source,
        }
        self._deadline_results.append(result)

        # Log critical/overdue
        if urgency_label in ("CRITICAL", "OVERDUE"):
            self._log("URGENT", f"⚠ {urgency_label}: {name} — {days_remaining}d remaining (due {due_str})")
        else:
            self._log("EVAL", f"{urgency_label}: {name} — {days_remaining}d remaining")

    def _finalize(self) -> None:
        """Write urgency report sorted by score (most urgent first)."""
        if self._central_conn:
            try:
                self._central_conn.close()
            except Exception:
                pass  # Intentionally silent — teardown

        if not self._deadline_results:
            self._log("DONE", "No deadlines evaluated")
            return

        # Sort by urgency (most urgent first)
        self._deadline_results.sort(key=lambda x: x["urgency_score"], reverse=True)

        # Summary counts
        counts = {"OVERDUE": 0, "CRITICAL": 0, "HIGH": 0, "MEDIUM": 0, "LOW": 0}
        for r in self._deadline_results:
            label = r["urgency_label"]
            counts[label] = counts.get(label, 0) + 1

        CHECKPOINT_DIR.mkdir(parents=True, exist_ok=True)
        report_path = CHECKPOINT_DIR / "deadline_urgency_report.json"
        report_path.write_text(json.dumps({
            "summary": {
                "total_deadlines": len(self._deadline_results),
                "overdue": counts["OVERDUE"],
                "critical": counts["CRITICAL"],
                "high": counts["HIGH"],
                "medium": counts["MEDIUM"],
                "low": counts["LOW"],
                "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
            },
            "deadlines": self._deadline_results,
        }, indent=2))

        self._log("DONE",
                   f"{len(self._deadline_results)} deadlines: "
                   f"{counts['OVERDUE']} OVERDUE, {counts['CRITICAL']} CRITICAL, "
                   f"{counts['HIGH']} HIGH, {counts['MEDIUM']} MEDIUM, {counts['LOW']} LOW "
                   f"| report: {report_path}")

    def _ensure_tables(self) -> None:
        """Create deadline tracking table in master_index.db."""
        self._db_execute("""
            CREATE TABLE IF NOT EXISTS deadline_tracking (
                id INTEGER PRIMARY KEY,
                name TEXT,
                due_date TEXT,
                adjusted_date TEXT,
                days_remaining INTEGER,
                urgency_score INTEGER,
                urgency_label TEXT,
                case_number TEXT,
                court TEXT,
                agent_id TEXT,
                evaluated_at TEXT DEFAULT (datetime('now'))
            )
        """)
        self.db.commit()
