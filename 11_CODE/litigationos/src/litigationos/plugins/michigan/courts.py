"""Michigan courts directory.

Provides a directory of Michigan courts including circuit courts,
district courts, probate courts, Court of Appeals, and Supreme Court.
"""

from __future__ import annotations

from typing import List, Optional


class MichiganCourts:
    """Directory of Michigan courts."""

    def get_courts(self, court_type: Optional[str] = None) -> List[dict]:
        """Return Michigan courts, optionally filtered by type.

        Each dict: {name, type, county, address, phone, efiling_url, local_rules_url}
        """
        # TODO: Load Michigan court directory from embedded data
        return []

    def get_court(self, name: str) -> Optional[dict]:
        """Look up a specific court by name."""
        courts = [c for c in self.get_courts() if c.get("name") == name]
        return courts[0] if courts else None
