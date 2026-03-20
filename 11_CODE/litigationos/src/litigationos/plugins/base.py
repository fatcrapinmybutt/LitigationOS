"""JurisdictionPlugin abstract base class.

All jurisdiction plugins must implement this interface, providing
court rules, forms, courts, deadline calculations, and filing validation
for their specific jurisdiction.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from datetime import date
from typing import List, Optional


class JurisdictionPlugin(ABC):
    """Base class for jurisdiction plugins."""

    @property
    @abstractmethod
    def jurisdiction_id(self) -> str:
        """Return jurisdiction identifier, e.g. 'MI'."""
        ...

    @property
    @abstractmethod
    def name(self) -> str:
        """Return human-readable name, e.g. 'Michigan'."""
        ...

    @abstractmethod
    def get_rules(self, category: Optional[str] = None) -> List[dict]:
        """Return list of court rules for this jurisdiction.

        Each dict: {rule_number, title, full_text, category, effective_date, source_url}
        """
        ...

    @abstractmethod
    def get_forms(self, category: Optional[str] = None) -> List[dict]:
        """Return list of official forms (e.g., SCAO forms).

        Each dict: {form_number, title, category, url, notes}
        """
        ...

    @abstractmethod
    def get_courts(self, court_type: Optional[str] = None) -> List[dict]:
        """Return list of courts in this jurisdiction.

        Each dict: {name, type, county, address, phone, efiling_url, local_rules_url}
        """
        ...

    @abstractmethod
    def calculate_deadline(
        self,
        filing_type: str,
        trigger_date: date,
        case_type: Optional[str] = None,
        court_type: Optional[str] = None,
    ) -> Optional[dict]:
        """Calculate a deadline based on a triggering event.

        Returns: {due_date, rule_basis, description, priority} or None
        """
        ...

    @abstractmethod
    def validate_filing(self, filing: dict, filing_type: str) -> dict:
        """Validate a filing against jurisdiction rules.

        Returns: {valid: bool, score: float, errors: [], warnings: []}
        """
        ...

    def seed_database(self, db) -> None:
        """Optional: Seed jurisdiction data into the database.

        Called once when the plugin is first enabled.
        """
        pass
