"""SCAO forms catalog for Michigan.

Provides a directory of State Court Administrative Office (SCAO) forms
with form numbers, titles, categories, and download URLs.
"""

from __future__ import annotations

from typing import List, Optional


class MichiganForms:
    """Catalog of Michigan SCAO forms."""

    def get_forms(self, category: Optional[str] = None) -> List[dict]:
        """Return SCAO forms, optionally filtered by category.

        Each dict: {form_number, title, category, url, notes}
        """
        # TODO: Load SCAO form catalog from embedded data
        return []

    def get_form(self, form_number: str) -> Optional[dict]:
        """Get a specific SCAO form by form number."""
        forms = [f for f in self.get_forms() if f.get("form_number") == form_number]
        return forms[0] if forms else None
