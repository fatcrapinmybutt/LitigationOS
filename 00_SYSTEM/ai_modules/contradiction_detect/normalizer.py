"""Normalize extracted statements for comparison."""
from __future__ import annotations

import logging
import re
import string
from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional

from . import config
from .statement_extractor import Statement

logger = logging.getLogger(__name__)

# Month lookup for date normalization
_MONTH_MAP: dict[str, int] = {
    "january": 1, "february": 2, "march": 3, "april": 4,
    "may": 5, "june": 6, "july": 7, "august": 8,
    "september": 9, "october": 10, "november": 11, "december": 12,
    "jan": 1, "feb": 2, "mar": 3, "apr": 4,
    "jun": 6, "jul": 7, "aug": 8, "sep": 9,
    "oct": 10, "nov": 11, "dec": 12,
}


@dataclass
class NormalizedStatement:
    """A statement after normalization — ready for comparison."""

    original: Statement
    canonical_text: str = ""
    topic_keywords: list[str] = field(default_factory=list)
    entities: list[str] = field(default_factory=list)
    date_normalized: Optional[str] = None  # ISO-8601 or None

    def __hash__(self) -> int:
        return hash(id(self.original))


class StatementNormalizer:
    """Transform raw *Statement* objects into comparison-ready form."""

    _punct_table = str.maketrans("", "", string.punctuation)
    _number_re = re.compile(r"\$?\d[\d,]*\.?\d*")
    _entity_re = re.compile(r"\b[A-Z][a-z]+(?:\s+[A-Z][a-z]+)*\b")

    def normalize(self, statement: Statement) -> NormalizedStatement:
        """Return a *NormalizedStatement* from a raw *Statement*."""
        canonical = self._canonicalize(statement.text)
        keywords = self._extract_keywords(canonical)
        entities = self._extract_entities(statement.text)
        date_norm = self._normalize_date(statement.date)

        return NormalizedStatement(
            original=statement,
            canonical_text=canonical,
            topic_keywords=keywords,
            entities=entities,
            date_normalized=date_norm,
        )

    # ------------------------------------------------------------------
    # Text canonicalization
    # ------------------------------------------------------------------

    def _canonicalize(self, text: str) -> str:
        """Lowercase, strip punctuation, collapse whitespace."""
        text = text.lower()
        text = text.translate(self._punct_table)
        text = re.sub(r"\s+", " ", text).strip()
        return text

    # ------------------------------------------------------------------
    # Keyword extraction (lightweight TF proxy)
    # ------------------------------------------------------------------

    def _extract_keywords(self, canonical: str) -> list[str]:
        """Return significant words (stop-word removal, length filter)."""
        tokens = canonical.split()
        return [
            w for w in tokens
            if w not in config.STOP_WORDS and len(w) > 2
        ]

    # ------------------------------------------------------------------
    # Entity extraction
    # ------------------------------------------------------------------

    def _extract_entities(self, raw_text: str) -> list[str]:
        """Pull proper-noun phrases and numeric values from *raw_text*."""
        entities: list[str] = []

        # Proper nouns (capitalized multi-word spans)
        for m in self._entity_re.finditer(raw_text):
            val = m.group(0)
            if val.lower() not in config.STOP_WORDS:
                entities.append(val)

        # Numbers / monetary amounts
        for m in self._number_re.finditer(raw_text):
            entities.append(m.group(0))

        # Known parties
        for name, pat in config.PARTY_PATTERNS.items():
            if pat.search(raw_text):
                entities.append(name)

        return list(dict.fromkeys(entities))  # dedupe, preserve order

    # ------------------------------------------------------------------
    # Date normalization → ISO-8601
    # ------------------------------------------------------------------

    def _normalize_date(self, raw_date: Optional[str]) -> Optional[str]:
        """Best-effort parse of *raw_date* into ``YYYY-MM-DD``."""
        if not raw_date:
            return None

        raw = raw_date.strip().rstrip(",")

        # Already ISO
        iso_match = re.match(r"^(\d{4})-(\d{2})-(\d{2})$", raw)
        if iso_match:
            return raw

        # MM/DD/YYYY or M/D/YY
        slash = re.match(r"^(\d{1,2})/(\d{1,2})/(\d{2,4})$", raw)
        if slash:
            m, d, y = int(slash[1]), int(slash[2]), int(slash[3])
            if y < 100:
                y += 2000
            try:
                return datetime(y, m, d).strftime("%Y-%m-%d")
            except ValueError:
                return None

        # Month DD, YYYY  or  Mon DD, YYYY
        wordy = re.match(
            r"^([A-Za-z]+)\.?\s+(\d{1,2}),?\s+(\d{4})$", raw,
        )
        if wordy:
            month_str = wordy[1].lower().rstrip(".")
            month_num = _MONTH_MAP.get(month_str)
            if month_num:
                try:
                    return datetime(
                        int(wordy[3]), month_num, int(wordy[2]),
                    ).strftime("%Y-%m-%d")
                except ValueError:
                    return None

        logger.debug("Could not normalize date: %r", raw_date)
        return None
