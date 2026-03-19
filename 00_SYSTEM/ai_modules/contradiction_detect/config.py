"""Contradiction Detection Engine — configuration constants."""
from __future__ import annotations

import os
import re

# ---------------------------------------------------------------------------
# Database
# ---------------------------------------------------------------------------
DB_PATH: str = os.environ.get(
    "LITIGATION_DB",
    os.path.join(
        os.path.dirname(__file__), os.pardir, os.pardir, os.pardir,
        "litigation_context.db",
    ),
)
DB_PATH = os.path.normpath(DB_PATH)

DB_PRAGMAS: list[str] = [
    "PRAGMA busy_timeout = 60000;",
    "PRAGMA journal_mode = WAL;",
    "PRAGMA cache_size = -32000;",
    "PRAGMA temp_store = MEMORY;",
    "PRAGMA synchronous = NORMAL;",
]

# ---------------------------------------------------------------------------
# Similarity / scoring thresholds
# ---------------------------------------------------------------------------
SIMILARITY_THRESHOLD: float = 0.6    # minimum cosine sim to consider same-topic
CONTRADICTION_THRESHOLD: float = 0.4  # below this on same topic → contradiction
MIN_STATEMENT_LENGTH: int = 20        # ignore very short fragments

# ---------------------------------------------------------------------------
# Date extraction patterns (order matters — most specific first)
# ---------------------------------------------------------------------------
DATE_PATTERNS: list[re.Pattern[str]] = [
    re.compile(
        r"\b(?:January|February|March|April|May|June|July|August|September|"
        r"October|November|December)\s+\d{1,2},?\s+\d{4}\b", re.IGNORECASE,
    ),
    re.compile(r"\b\d{1,2}/\d{1,2}/\d{2,4}\b"),
    re.compile(r"\b\d{4}-\d{2}-\d{2}\b"),
    re.compile(
        r"\b(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)"
        r"\.?\s+\d{1,2},?\s+\d{4}\b", re.IGNORECASE,
    ),
]

# ---------------------------------------------------------------------------
# Statement attribution markers
# ---------------------------------------------------------------------------
STATEMENT_MARKERS: list[re.Pattern[str]] = [
    re.compile(
        r"\b(?:testified|declared|stated|alleged|claimed|asserted|"
        r"reported|affirmed|swore|acknowledged|admitted|denied|"
        r"contended|maintained|represented|indicated|told|said)\b",
        re.IGNORECASE,
    ),
]

# ---------------------------------------------------------------------------
# Party / entity patterns  (Pigors v. Watson, Michigan family law)
# ---------------------------------------------------------------------------
PARTY_PATTERNS: dict[str, re.Pattern[str]] = {
    "Andrew Pigors": re.compile(
        r"\b(?:Andrew\s+Pigors|Mr\.?\s+Pigors|Pigors|Plaintiff|Father|"
        r"Respondent[\s\-]?Father)\b", re.IGNORECASE,
    ),
    "Opposing Party": re.compile(
        r"\b(?:Watson|Ms\.?\s+Watson|Defendant|Mother|"
        r"Petitioner[\s\-]?Mother|Respondent[\s\-]?Mother)\b", re.IGNORECASE,
    ),
    "Judge McNeill": re.compile(
        r"\b(?:Judge\s+McNeill|McNeill|Hon\.?\s+Jenny\s+L?\.?\s*McNeill|"
        r"the\s+Court)\b", re.IGNORECASE,
    ),
}

# Pronoun → party heuristic (resolved from nearest prior party mention)
PRONOUN_PATTERNS: list[re.Pattern[str]] = [
    re.compile(r"\b(?:he|him|his)\b", re.IGNORECASE),
    re.compile(r"\b(?:she|her|hers)\b", re.IGNORECASE),
]

# ---------------------------------------------------------------------------
# Severity levels
# ---------------------------------------------------------------------------
SEVERITY_LEVELS: dict[str, int] = {
    "CRITICAL": 3,
    "MAJOR": 2,
    "MINOR": 1,
}

# ---------------------------------------------------------------------------
# Sworn-statement indicators (boost impeachment value)
# ---------------------------------------------------------------------------
SWORN_INDICATORS: list[re.Pattern[str]] = [
    re.compile(
        r"\b(?:under\s+oath|under\s+penalty\s+of\s+perjury|"
        r"sworn\s+(?:testimony|statement|affidavit|declaration)|"
        r"deposition|transcript)\b", re.IGNORECASE,
    ),
]

# ---------------------------------------------------------------------------
# Case lanes
# ---------------------------------------------------------------------------
LANE_MAP: dict[str, list[str]] = {
    "A": ["2024-001507-DC"],
    "B": ["2025-002760-CZ"],
    "D": ["2023-5907-PP"],
    "E": ["misconduct", "JTC"],
    "F": ["appellate", "COA", "MSC"],
}

# ---------------------------------------------------------------------------
# Stop words (lightweight, no NLTK dependency)
# ---------------------------------------------------------------------------
STOP_WORDS: frozenset[str] = frozenset(
    "a an the and or but in on at to for of is was were be been being "
    "have has had do does did will would shall should may might can could "
    "i me my we our you your he him his she her it its they them their "
    "this that these those with from by as not no nor so if then than "
    "very too also just about above after before between into through "
    "during each few more most other some such only own same up down out "
    "off over under again further once here there when where why how all "
    "both which what who whom".split()
)
