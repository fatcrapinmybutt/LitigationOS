"""
Legal Entity Extractor — LitigationOS Legal AI
================================================
Extracts named entities from legal text using a multi-strategy pipeline:
  1. Rule-based patterns (Michigan-specific judges, courts, parties)
  2. spaCy NER (general entity recognition)
  3. Legal-specific patterns (case names, statutory references)

Entity Types:
  JUDGE, PARTY, COURT, ATTORNEY, STATUTE, CASE_NAME,
  DATE, AMOUNT, ADDRESS, CASE_NUMBER, ORGANIZATION

Usage:
    from legal_ai.entity_extractor import EntityExtractor
    ex = EntityExtractor()
    entities = ex.extract("Judge McNeill issued an order on March 15, 2026")
"""

from __future__ import annotations

import logging
import re
import time
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Set, Tuple

logger = logging.getLogger("legal_ai.entities")


# ── Data Models ──────────────────────────────────────────────────

@dataclass
class Entity:
    """A single extracted named entity."""
    text: str
    entity_type: str
    start: int = 0
    end: int = 0
    confidence: float = 0.0
    source: str = ""       # rules, spacy, pattern
    normalized: str = ""   # canonical form
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class EntityExtractionResult:
    """Complete entity extraction result."""
    entities: List[Entity] = field(default_factory=list)
    by_type: Dict[str, List[Entity]] = field(default_factory=dict)
    total_found: int = 0
    extraction_time_ms: float = 0.0
    engines_used: List[str] = field(default_factory=list)


# ── Known Entities (Pigors v. Watson case) ────────────────────────

KNOWN_JUDGES: Dict[str, Dict[str, str]] = {
    "mcneill": {"full": "Hon. Jenny L. McNeill", "court": "14th Circuit", "role": "presiding_judge"},
    "jenny l. mcneill": {"full": "Hon. Jenny L. McNeill", "court": "14th Circuit", "role": "presiding_judge"},
    "jenny mcneill": {"full": "Hon. Jenny L. McNeill", "court": "14th Circuit", "role": "presiding_judge"},
    "judge mcneill": {"full": "Hon. Jenny L. McNeill", "court": "14th Circuit", "role": "presiding_judge"},
}

KNOWN_PARTIES: Dict[str, Dict[str, str]] = {
    "andrew pigors": {"full": "Andrew James Pigors", "role": "plaintiff"},
    "andrew j. pigors": {"full": "Andrew James Pigors", "role": "plaintiff"},
    "pigors": {"full": "Andrew James Pigors", "role": "plaintiff"},
    "emily watson": {"full": "Emily A. Watson", "role": "defendant"},
    "emily a. watson": {"full": "Emily A. Watson", "role": "defendant"},
    "watson": {"full": "Emily A. Watson", "role": "defendant"},
    "ronald berry": {"full": "Ronald Berry", "role": "defendant"},
    "berry": {"full": "Ronald Berry", "role": "defendant"},
    "lane watson": {"full": "Lane A. Watson", "role": "defendant"},
    "lori watson": {"full": "Lori Watson", "role": "defendant"},
    "albert watson": {"full": "Albert Watson", "role": "defendant"},
    "cody watson": {"full": "Cody Watson", "role": "defendant"},
    "pamela rusco": {"full": "Pamela Rusco", "role": "defendant_foc_referee"},
    "mandi martini": {"full": "Mandi Martini, Esq.", "role": "former_attorney"},
    "cassandra vandam": {"full": "Cassandra \"Casey\" VanDam", "role": "defendant_park_manager"},
    "casey vandam": {"full": "Cassandra \"Casey\" VanDam", "role": "defendant_park_manager"},
    "nicole browley": {"full": "Nicole Browley", "role": "defendant"},
    "kim davis": {"full": "Kim Davis", "role": "defendant_park_manager"},
}

KNOWN_ORGANIZATIONS: Dict[str, Dict[str, str]] = {
    "shady oaks": {"full": "Shady Oaks Park MHP, LLC", "type": "corporate_defendant"},
    "homes of america": {"full": "Homes of America, LLC", "type": "corporate_defendant"},
    "alden global": {"full": "Alden Global Capital, LLC", "type": "corporate_defendant"},
    "partridge equity": {"full": "Partridge Equity Group", "type": "corporate_defendant"},
    "vrm capital": {"full": "VRM Capital Corp", "type": "corporate_defendant"},
    "cricklewood": {"full": "Cricklewood MHP LLC", "type": "corporate_defendant"},
    "muskegon county": {"full": "Muskegon County", "type": "municipal_defendant"},
}

# ── Regex Patterns ───────────────────────────────────────────────

CASE_NUMBER_PATTERN = re.compile(
    r"(?:No\.\s*|Case\s+(?:No\.?\s*)?|#\s*)"
    r"(\d{4}[-–]\d{5,6}[-–][A-Z]{2,3})",
    re.IGNORECASE,
)

STANDALONE_CASE_NUMBER = re.compile(
    r"\b(\d{4}[-–]0?\d{1,6}[-–](?:DC|CZ|PP|DO|DM|FH|FC|GC))\b"
)

DATE_PATTERN = re.compile(
    r"\b(?:"
    r"(?:January|February|March|April|May|June|July|August|September|October|November|December)"
    r"\s+\d{1,2},?\s+\d{4}"
    r"|"
    r"\d{1,2}/\d{1,2}/\d{4}"
    r"|"
    r"\d{4}-\d{2}-\d{2}"
    r")\b",
    re.IGNORECASE,
)

AMOUNT_PATTERN = re.compile(
    r"\$[\d,]+(?:\.\d{2})?(?:\s*(?:million|billion|thousand))?"
)

JUDGE_TITLE_PATTERN = re.compile(
    r"(?:(?:Hon(?:orable)?\.?\s+|Judge\s+|Referee\s+|Magistrate\s+)"
    r"([A-Z][a-z]+(?:\s+[A-Z]\.?)?\s+[A-Z][a-z]+(?:[-'][A-Z][a-z]+)?))",
)

CASE_NAME_PATTERN = re.compile(
    r"([A-Z][a-z]+(?:\s+[A-Z]\.?)?\s+(?:v\.?|vs\.?)\s+"
    r"[A-Z][a-z]+(?:\s+[A-Z][a-z]+)?(?:\s+(?:et\s+al\.?))?)"
)

ADDRESS_PATTERN = re.compile(
    r"\b(\d+\s+[A-Z][a-z]+(?:\s+[A-Z][a-z]+)*\s+"
    r"(?:Road|Rd|Street|St|Avenue|Ave|Drive|Dr|Boulevard|Blvd|Lane|Ln|Court|Ct|Way|Place|Pl)"
    r"(?:,?\s+(?:Lot|Apt|Suite|Unit|#)\s*\d+)?"
    r"(?:,?\s+[A-Z][a-z]+(?:\s+[A-Z][a-z]+)*,?\s+(?:MI|Michigan)\s+\d{5})?)"
    r"\b",
    re.IGNORECASE,
)


# ── Entity Extractor Engine ──────────────────────────────────────

class EntityExtractor:
    """Multi-strategy legal entity extractor."""

    def __init__(self, use_spacy: bool = True):
        self._use_spacy = use_spacy
        self._spacy_available = False
        self._nlp = None
        self._init_spacy()

    def _init_spacy(self) -> None:
        """Try to load spaCy with legal model."""
        if not self._use_spacy:
            return
        try:
            import spacy
            # Try legal model first, then general
            for model_name in ["en_core_web_sm", "en_core_web_md", "en_core_web_lg"]:
                try:
                    self._nlp = spacy.load(model_name)
                    self._spacy_available = True
                    logger.info("spaCy loaded: %s", model_name)
                    break
                except OSError:
                    continue
            if not self._spacy_available:
                logger.warning("No spaCy model found — using rule-based extraction only")
        except ImportError:
            logger.warning("spaCy not installed — using rule-based extraction only")

    def extract(self, text: str) -> EntityExtractionResult:
        """Extract all entities from text."""
        t0 = time.perf_counter()
        result = EntityExtractionResult()
        seen: Set[Tuple[str, str]] = set()

        # Engine 1: Known entities (case-specific, highest confidence)
        known = self._extract_known_entities(text)
        for e in known:
            key = (e.normalized or e.text.lower(), e.entity_type)
            if key not in seen:
                seen.add(key)
                result.entities.append(e)
        if known:
            result.engines_used.append("known_entities")

        # Engine 2: Regex patterns
        regex_ents = self._extract_regex_entities(text)
        for e in regex_ents:
            key = (e.normalized or e.text.lower(), e.entity_type)
            if key not in seen:
                seen.add(key)
                result.entities.append(e)
        if regex_ents:
            result.engines_used.append("regex")

        # Engine 3: spaCy NER
        if self._spacy_available:
            spacy_ents = self._extract_spacy(text)
            for e in spacy_ents:
                key = (e.normalized or e.text.lower(), e.entity_type)
                if key not in seen:
                    seen.add(key)
                    result.entities.append(e)
            if spacy_ents:
                result.engines_used.append("spacy")

        # Build by-type index
        for e in result.entities:
            result.by_type.setdefault(e.entity_type, []).append(e)

        result.total_found = len(result.entities)
        result.extraction_time_ms = (time.perf_counter() - t0) * 1000
        return result

    # ── Known Entities ───────────────────────────────────────────

    def _extract_known_entities(self, text: str) -> List[Entity]:
        """Match known case-specific entities."""
        entities: List[Entity] = []
        text_lower = text.lower()

        for key, info in KNOWN_JUDGES.items():
            idx = text_lower.find(key)
            if idx >= 0:
                entities.append(Entity(
                    text=text[idx:idx + len(key)],
                    entity_type="JUDGE",
                    start=idx,
                    end=idx + len(key),
                    confidence=0.99,
                    source="known_entities",
                    normalized=info["full"],
                    metadata={"court": info.get("court", ""), "role": info.get("role", "")},
                ))

        for key, info in KNOWN_PARTIES.items():
            idx = text_lower.find(key)
            if idx >= 0:
                entities.append(Entity(
                    text=text[idx:idx + len(key)],
                    entity_type="PARTY",
                    start=idx,
                    end=idx + len(key),
                    confidence=0.99,
                    source="known_entities",
                    normalized=info["full"],
                    metadata={"role": info.get("role", "")},
                ))

        for key, info in KNOWN_ORGANIZATIONS.items():
            idx = text_lower.find(key)
            if idx >= 0:
                entities.append(Entity(
                    text=text[idx:idx + len(key)],
                    entity_type="ORGANIZATION",
                    start=idx,
                    end=idx + len(key),
                    confidence=0.95,
                    source="known_entities",
                    normalized=info["full"],
                    metadata={"type": info.get("type", "")},
                ))

        return entities

    # ── Regex Patterns ───────────────────────────────────────────

    def _extract_regex_entities(self, text: str) -> List[Entity]:
        """Extract entities via compiled regex patterns."""
        entities: List[Entity] = []

        # Case numbers
        for pattern in [CASE_NUMBER_PATTERN, STANDALONE_CASE_NUMBER]:
            for m in pattern.finditer(text):
                entities.append(Entity(
                    text=m.group(1) if m.lastindex else m.group(0),
                    entity_type="CASE_NUMBER",
                    start=m.start(),
                    end=m.end(),
                    confidence=0.90,
                    source="regex",
                ))

        # Dates
        for m in DATE_PATTERN.finditer(text):
            entities.append(Entity(
                text=m.group(0),
                entity_type="DATE",
                start=m.start(),
                end=m.end(),
                confidence=0.85,
                source="regex",
            ))

        # Amounts
        for m in AMOUNT_PATTERN.finditer(text):
            entities.append(Entity(
                text=m.group(0),
                entity_type="AMOUNT",
                start=m.start(),
                end=m.end(),
                confidence=0.90,
                source="regex",
            ))

        # Judge titles
        for m in JUDGE_TITLE_PATTERN.finditer(text):
            entities.append(Entity(
                text=m.group(0).strip(),
                entity_type="JUDGE",
                start=m.start(),
                end=m.end(),
                confidence=0.80,
                source="regex",
                normalized=m.group(1) if m.lastindex else "",
            ))

        # Case names (X v. Y)
        for m in CASE_NAME_PATTERN.finditer(text):
            entities.append(Entity(
                text=m.group(0).strip(),
                entity_type="CASE_NAME",
                start=m.start(),
                end=m.end(),
                confidence=0.80,
                source="regex",
            ))

        # Addresses
        for m in ADDRESS_PATTERN.finditer(text):
            entities.append(Entity(
                text=m.group(0).strip(),
                entity_type="ADDRESS",
                start=m.start(),
                end=m.end(),
                confidence=0.75,
                source="regex",
            ))

        return entities

    # ── spaCy NER ────────────────────────────────────────────────

    def _extract_spacy(self, text: str) -> List[Entity]:
        """Extract entities via spaCy NER model."""
        if not self._nlp:
            return []

        entities: List[Entity] = []
        try:
            # Limit text to prevent OOM on very large documents
            doc = self._nlp(text[:100_000])
            type_map = {
                "PERSON": "PARTY",
                "ORG": "ORGANIZATION",
                "GPE": "LOCATION",
                "DATE": "DATE",
                "MONEY": "AMOUNT",
                "LAW": "STATUTE",
                "FAC": "FACILITY",
            }

            for ent in doc.ents:
                mapped_type = type_map.get(ent.label_, ent.label_)
                if mapped_type in ("PARTY", "ORGANIZATION", "DATE", "AMOUNT",
                                   "STATUTE", "LOCATION"):
                    entities.append(Entity(
                        text=ent.text,
                        entity_type=mapped_type,
                        start=ent.start_char,
                        end=ent.end_char,
                        confidence=0.70,
                        source="spacy",
                    ))
        except Exception as exc:
            logger.warning("spaCy extraction error: %s", exc)

        return entities

    # ── Batch + Stats ────────────────────────────────────────────

    def extract_batch(
        self, texts: List[str], labels: Optional[List[str]] = None
    ) -> Dict[str, EntityExtractionResult]:
        """Extract entities from multiple texts."""
        results: Dict[str, EntityExtractionResult] = {}
        for i, text in enumerate(texts):
            label = labels[i] if labels and i < len(labels) else f"doc_{i}"
            results[label] = self.extract(text)
        return results

    def get_stats(self) -> Dict[str, Any]:
        """Return engine status."""
        return {
            "version": "1.0.0",
            "spacy_available": self._spacy_available,
            "spacy_model": self._nlp.meta.get("name", "unknown") if self._nlp else None,
            "known_judges": len(KNOWN_JUDGES),
            "known_parties": len(KNOWN_PARTIES),
            "known_organizations": len(KNOWN_ORGANIZATIONS),
        }
