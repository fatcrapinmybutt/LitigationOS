"""Michigan jurisdiction plugin — ships built-in with LitigationOS.

Provides Michigan Court Rules (MCR), SCAO forms, court directory,
and Michigan-specific deadline calculations.
"""

from litigationos.plugins.michigan.rules import MichiganRules
from litigationos.plugins.michigan.forms import MichiganForms
from litigationos.plugins.michigan.courts import MichiganCourts
from litigationos.plugins.michigan.deadlines import MichiganDeadlines
from litigationos.plugins.base import JurisdictionPlugin

from datetime import date
from typing import List, Optional


class Plugin(JurisdictionPlugin):
    """Michigan jurisdiction plugin."""

    def __init__(self):
        self._rules = MichiganRules()
        self._forms = MichiganForms()
        self._courts = MichiganCourts()
        self._deadlines = MichiganDeadlines()

    @property
    def jurisdiction_id(self) -> str:
        return "MI"

    @property
    def name(self) -> str:
        return "Michigan"

    def get_rules(self, category: Optional[str] = None) -> List[dict]:
        return self._rules.get_rules(category)

    def get_forms(self, category: Optional[str] = None) -> List[dict]:
        return self._forms.get_forms(category)

    def get_courts(self, court_type: Optional[str] = None) -> List[dict]:
        return self._courts.get_courts(court_type)

    def calculate_deadline(
        self,
        filing_type: str,
        trigger_date: date,
        case_type: Optional[str] = None,
        court_type: Optional[str] = None,
    ) -> Optional[dict]:
        return self._deadlines.calculate(filing_type, trigger_date, case_type, court_type)

    def validate_filing(self, filing: dict, filing_type: str) -> dict:
        return self._rules.validate_filing(filing, filing_type)

    def seed_database(self, db) -> None:
        from litigationos.db.seed import seed_michigan
        seed_michigan(db)
