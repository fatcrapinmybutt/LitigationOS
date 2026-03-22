"""Static legal data modules for LitigationOS.

This package contains comprehensive offline datasets for Michigan law:
- mcr_complete: Complete Michigan Court Rules (MCR) — 50+ rules, 9 chapters
- mcl_complete: Complete Michigan Compiled Laws (MCL) — 7 chapters
- mre_complete: Complete Michigan Rules of Evidence (MRE) — 11 articles, 40+ rules
- federal_rules: Federal Rules (FRCP, FRE, §1983, WDMI local rules)
- federal_forms: Federal Court Form Library for WDMI — JS 44, AO 440, AO 240, subpoenas, motions
- local_rules: 14th Circuit, 60th District, admin orders, jury instructions, bench books
- scao_forms: Complete SCAO court forms catalog (35+ forms)
- ppo_forms: PPO Form Suite for Lane D — petition, order, modify, extend, contempt
- msc_forms: Michigan Supreme Court filing form library (MCR 7.300-series)
- foc_forms: FOC Form Automation System — Friend of the Court forms, deadlines, routing
- discovery_forms: Discovery & Subpoena Form Generator — MC 11 series, templates, MCR 2.301–2.313
- domestic_forms: Domestic Relations Judgment & Order Forms — CC 350–360, MC 20–22, GC 100/104
- interlocutory_forms: Interlocutory Appeal Form Suite — COA filings before final judgment (MCR 7.200)
- legal_scraper: Web scraper engine with FTS5 indexing and offline fallback
"""

from __future__ import annotations

__all__ = [
    "mcr_complete",
    "mcl_complete",
    "mre_complete",
    "federal_rules",
    "federal_forms",
    "local_rules",
    "scao_forms",
    "ppo_forms",
    "msc_forms",
    "foc_forms",
    "discovery_forms",
    "domestic_forms",
    "interlocutory_forms",
    "legal_scraper",
    "rule_lookup",
]
