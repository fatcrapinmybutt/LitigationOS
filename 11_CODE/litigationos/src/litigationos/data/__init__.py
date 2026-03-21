"""Static legal data modules for LitigationOS.

This package contains comprehensive offline datasets for Michigan law:
- mcr_complete: Complete Michigan Court Rules (MCR) — 50+ rules, 9 chapters
- mcl_complete: Complete Michigan Compiled Laws (MCL) — 7 chapters
- mre_complete: Complete Michigan Rules of Evidence (MRE) — 11 articles, 40+ rules
- federal_rules: Federal Rules (FRCP, FRE, §1983, WDMI local rules)
- legal_scraper: Web scraper engine with FTS5 indexing and offline fallback
"""

from __future__ import annotations

__all__ = [
    "mcr_complete",
    "mcl_complete",
    "mre_complete",
    "federal_rules",
    "legal_scraper",
]
