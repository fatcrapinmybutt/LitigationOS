"""Base classes for the multi-jurisdiction plugin architecture."""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Dict, List, Optional


@dataclass
class JurisdictionInfo:
    """Metadata describing a single jurisdiction."""

    state: str
    courts: List[str]
    rules_db: Optional[str] = None
    forms_db: Optional[str] = None
    statutes_prefix: str = ""


class JurisdictionPlugin(ABC):
    """Abstract base class every jurisdiction plugin must implement."""

    @abstractmethod
    def get_info(self) -> JurisdictionInfo:
        """Return jurisdiction metadata."""
        ...

    @abstractmethod
    def get_court_rules(self, court: str) -> Dict:
        """Return court rules for the specified court.

        Args:
            court: Court identifier (e.g. '14th-circuit', 'coa').

        Returns:
            Dict with rule_set, local_rules, and any court-specific data.
        """
        ...

    @abstractmethod
    def get_filing_requirements(self, court: str, filing_type: str) -> Dict:
        """Return filing requirements for a specific court and filing type.

        Args:
            court: Court identifier.
            filing_type: E.g. 'motion', 'brief', 'complaint', 'answer'.

        Returns:
            Dict with required fields, format rules, deadlines, and fees.
        """
        ...

    @abstractmethod
    def validate_filing(self, filing: dict) -> List[str]:
        """Validate a filing dict against jurisdiction rules.

        Args:
            filing: Dict containing filing metadata and content.

        Returns:
            List of validation error strings (empty if valid).
        """
        ...


class JurisdictionRegistry:
    """Registry of available jurisdiction plugins."""

    def __init__(self) -> None:
        self._plugins: Dict[str, JurisdictionPlugin] = {}

    def register(self, key: str, plugin: JurisdictionPlugin) -> None:
        """Register a jurisdiction plugin under *key* (e.g. 'MI')."""
        self._plugins[key] = plugin

    def get(self, key: str) -> Optional[JurisdictionPlugin]:
        """Return the plugin for *key*, or ``None``."""
        return self._plugins.get(key)

    def list_jurisdictions(self) -> List[str]:
        """Return all registered jurisdiction keys."""
        return list(self._plugins.keys())
