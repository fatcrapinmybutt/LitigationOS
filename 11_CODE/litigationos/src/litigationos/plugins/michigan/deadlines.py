"""Michigan-specific deadline calculation rules.

Implements deadline rules from the Michigan Court Rules (MCR),
including response times, appeal deadlines, and service requirements.
"""

from __future__ import annotations

from datetime import date, timedelta
from typing import Optional


class MichiganDeadlines:
    """Calculate deadlines based on Michigan Court Rules."""

    # Common Michigan deadline rules (days)
    DEADLINE_RULES = {
        "response_to_complaint": {
            "days": 21,
            "rule_basis": "MCR 2.108(A)(1)",
            "description": "Answer or responsive pleading due",
            "priority": "high",
        },
        "response_to_motion": {
            "days": 21,
            "rule_basis": "MCR 2.119(A)(2)",
            "description": "Response to motion due",
            "priority": "high",
        },
        "reply_brief": {
            "days": 7,
            "rule_basis": "MCR 2.119(A)(2)",
            "description": "Reply brief due",
            "priority": "normal",
        },
        "claim_of_appeal": {
            "days": 21,
            "rule_basis": "MCR 7.204(A)(1)",
            "description": "Claim of appeal due",
            "priority": "critical",
        },
        "appellate_brief": {
            "days": 56,
            "rule_basis": "MCR 7.212(A)(1)(a)",
            "description": "Appellant's brief due",
            "priority": "high",
        },
    }

    def calculate(
        self,
        filing_type: str,
        trigger_date: date,
        case_type: Optional[str] = None,
        court_type: Optional[str] = None,
    ) -> Optional[dict]:
        """Calculate a deadline from a triggering event.

        Args:
            filing_type: Type of filing that triggers the deadline
            trigger_date: Date of the triggering event
            case_type: Optional case type for context
            court_type: Optional court type for context

        Returns:
            Dict with {due_date, rule_basis, description, priority} or None
        """
        rule = self.DEADLINE_RULES.get(filing_type)
        if not rule:
            return None

        due_date = trigger_date + timedelta(days=rule["days"])
        return {
            "due_date": due_date.isoformat(),
            "rule_basis": rule["rule_basis"],
            "description": rule["description"],
            "priority": rule["priority"],
        }
