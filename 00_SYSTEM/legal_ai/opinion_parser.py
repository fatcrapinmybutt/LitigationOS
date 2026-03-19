"""
LitigationOS Opinion Parser v1.0
=================================
Structural parser for Michigan court orders and opinions.

Features:
  - Section segmentation (headings, findings, conclusions, holdings, relief)
  - Procedural defect detection (ex-parte, missing notice/hearing/findings)
  - Order type classification (ex_parte, stipulated, contested, default, emergency)
  - Integration with CitationExtractor and EntityExtractor
  - Michigan-specific patterns and authorities

Usage::

    from legal_ai.opinion_parser import OpinionParser

    parser = OpinionParser()
    result = parser.parse(order_text)
    for defect in result.procedural_defects:
        print(f"[{defect.severity}] {defect.defect_type}: {defect.description}")
"""

from __future__ import annotations

import logging
import re
import sys
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

logger = logging.getLogger("legal_ai.opinion_parser")

_HERE = Path(__file__).parent
_REPO = _HERE.parent.parent

# ---------------------------------------------------------------------------
# Dataclasses
# ---------------------------------------------------------------------------


@dataclass
class OrderSection:
    """A structural section within a court order."""

    section_type: str  # heading/finding_of_fact/conclusion_of_law/holding/order/relief/recital/caption
    text: str
    start_offset: int = 0
    end_offset: int = 0
    confidence: float = 0.0
    citations: List[str] = field(default_factory=list)
    entities: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ProceduralDefect:
    """A procedural defect detected in a court order."""

    defect_type: str  # ex_parte/missing_notice/missing_hearing/missing_findings/missing_service/missing_signature
    description: str
    severity: str = "moderate"  # critical/high/moderate/low
    authority: str = ""
    evidence_text: str = ""
    confidence: float = 0.0


@dataclass
class ParsedOpinion:
    """Complete structured parse of a court order or opinion."""

    order_id: str = ""
    order_date: str = ""
    court: str = ""
    judge: str = ""
    case_number: str = ""
    order_type: str = ""  # ex_parte/stipulated/contested/default/emergency
    sections: List[OrderSection] = field(default_factory=list)
    holdings: List[str] = field(default_factory=list)
    findings_of_fact: List[str] = field(default_factory=list)
    conclusions_of_law: List[str] = field(default_factory=list)
    relief_granted: List[str] = field(default_factory=list)
    relief_denied: List[str] = field(default_factory=list)
    procedural_defects: List[ProceduralDefect] = field(default_factory=list)
    citations_found: List[str] = field(default_factory=list)
    entities_found: List[str] = field(default_factory=list)
    is_ex_parte: bool = False
    has_required_findings: bool = False
    has_best_interest_analysis: bool = False
    parse_time_ms: float = 0.0
    warnings: List[str] = field(default_factory=list)


# ---------------------------------------------------------------------------
# Defect detection patterns (Michigan-specific)
# ---------------------------------------------------------------------------

DEFECT_PATTERNS: Dict[str, Dict[str, Any]] = {
    "ex_parte": {
        "indicators": [
            "ex parte",
            "without notice",
            "without hearing",
            "upon review of the file",
            "without oral argument",
        ],
        "negative_indicators": ["after hearing", "parties present", "stipulat"],
        "authority": "MCR 2.119(B); US Const Amend XIV",
        "severity": "critical",
    },
    "missing_notice": {
        "indicators": ["no proof of service", "service not shown"],
        "authority": "MCR 2.107; MCR 2.119(C)",
        "severity": "critical",
    },
    "missing_findings": {
        "required_for": ["custody", "parenting time", "domicile"],
        "must_contain": ["best interest", "722.23", "endangerment"],
        "authority": "MCL 722.27(1)(c); MCL 722.27a(7)",
        "severity": "high",
    },
    "missing_hearing": {
        "indicators": [
            "no hearing held",
            "without hearing",
            "no oral argument",
        ],
        "authority": "MCR 2.119(E); US Const Amend XIV Due Process",
        "severity": "high",
    },
    "missing_service": {
        "indicators": ["service not perfected", "no proof of service filed"],
        "authority": "MCR 2.105; MCR 2.107",
        "severity": "high",
    },
    "missing_signature": {
        "indicators": ["unsigned", "no judicial signature"],
        "authority": "MCR 2.602(A)",
        "severity": "moderate",
    },
}

# ---------------------------------------------------------------------------
# Section detection regexes (Michigan court order headers)
# ---------------------------------------------------------------------------

_SECTION_PATTERNS: List[Tuple[str, re.Pattern]] = [
    ("order", re.compile(
        r"(?:^|\n)\s*(?:IT\s+IS\s+(?:HEREBY\s+)?ORDERED|THE\s+COURT\s+(?:HEREBY\s+)?ORDERS)",
        re.IGNORECASE,
    )),
    ("finding_of_fact", re.compile(
        r"(?:^|\n)\s*FINDING(?:S)?\s+OF\s+FACT",
        re.IGNORECASE,
    )),
    ("conclusion_of_law", re.compile(
        r"(?:^|\n)\s*CONCLUSION(?:S)?\s+OF\s+LAW",
        re.IGNORECASE,
    )),
    ("holding", re.compile(
        r"(?:^|\n)\s*(?:ORDER|JUDGMENT|OPINION)\s*(?:\n|$)",
        re.IGNORECASE,
    )),
    ("relief", re.compile(
        r"(?:^|\n)\s*(?:RELIEF|REMEDY|DISPOSITION)\b",
        re.IGNORECASE,
    )),
    ("recital", re.compile(
        r"(?:^|\n)\s*(?:WHEREAS|NOW\s+THEREFORE|RECITAL)",
        re.IGNORECASE,
    )),
    ("caption", re.compile(
        r"(?:^|\n)\s*(?:STATE\s+OF\s+MICHIGAN|(?:IN\s+THE\s+)?(?:CIRCUIT|DISTRICT|FAMILY)\s+COURT)",
        re.IGNORECASE,
    )),
]

# Order type classification patterns
_ORDER_TYPE_PATTERNS: Dict[str, List[re.Pattern]] = {
    "ex_parte": [
        re.compile(r"\bex\s*parte\b", re.IGNORECASE),
        re.compile(r"\bwithout\s+(?:notice|hearing)\b", re.IGNORECASE),
        re.compile(r"\bupon\s+review\s+of\s+the\s+file\b", re.IGNORECASE),
    ],
    "stipulated": [
        re.compile(r"\bstipulat(?:ed|ion)\b", re.IGNORECASE),
        re.compile(r"\bconsent\s+(?:order|judgment)\b", re.IGNORECASE),
        re.compile(r"\bagreed\s+order\b", re.IGNORECASE),
    ],
    "default": [
        re.compile(r"\bdefault\s+(?:order|judgment)\b", re.IGNORECASE),
        re.compile(r"\bfailure\s+to\s+(?:appear|respond)\b", re.IGNORECASE),
    ],
    "emergency": [
        re.compile(r"\bemergency\b", re.IGNORECASE),
        re.compile(r"\btemporary\s+restraining\s+order\b", re.IGNORECASE),
    ],
    "contested": [
        re.compile(r"\bafter\s+(?:hearing|trial|argument)\b", re.IGNORECASE),
        re.compile(r"\bparties\s+(?:present|appeared)\b", re.IGNORECASE),
    ],
}

# Patterns for extracting relief items
_RELIEF_GRANTED_RE = re.compile(
    r"(?:(?:IT\s+IS\s+)?(?:HEREBY\s+)?ORDERED\s+(?:THAT\s+)?|(?:The\s+Court\s+)?(?:ORDERS|GRANTS)\s+)"
    r"(.+?)(?:\.|;|\n\s*\n)",
    re.IGNORECASE | re.DOTALL,
)
_RELIEF_DENIED_RE = re.compile(
    r"(?:(?:is\s+)?(?:HEREBY\s+)?DENIED|MOTION\s+(?:IS\s+)?DENIED)\s*[:\-]?\s*(.+?)(?:\.|;|\n\s*\n)",
    re.IGNORECASE | re.DOTALL,
)

# Michigan best-interest factors
_BEST_INTEREST_RE = re.compile(
    r"\b(?:best\s+interest|722\.23|child(?:ren)?(?:'s)?\s+best\s+interest)\b",
    re.IGNORECASE,
)

# Date extraction from order text
_ORDER_DATE_RE = re.compile(
    r"(?:dated|entered|signed)\s*[:\-]?\s*(\w+\s+\d{1,2},?\s+\d{4}|\d{1,2}/\d{1,2}/\d{4})",
    re.IGNORECASE,
)

# Judge name extraction
_JUDGE_RE = re.compile(
    r"(?:(?:Honorable|Hon\.?|Judge|Circuit\s+(?:Court\s+)?Judge)\s+)([\w.\-]+(?:\s+[\w.\-]+){0,3})",
    re.IGNORECASE,
)

# Case number extraction
_CASE_NUMBER_RE = re.compile(
    r"\b(\d{4}[-\s]?\d{4,6}[-\s]?(?:DC|DM|CZ|PP|FC|DO|FH|GC|NO)\b)",
    re.IGNORECASE,
)


# ---------------------------------------------------------------------------
# OpinionParser
# ---------------------------------------------------------------------------


class OpinionParser:
    """Structural parser for Michigan court orders and opinions."""

    def __init__(
        self,
        brain_manager: Optional[Any] = None,
        use_citation_extractor: bool = True,
        use_entity_extractor: bool = True,
    ):
        self._brain_manager = brain_manager
        self._use_citations = use_citation_extractor
        self._use_entities = use_entity_extractor
        self._citation_extractor: Optional[Any] = None
        self._entity_extractor: Optional[Any] = None
        self._citation_available = False
        self._entity_available = False
        self._parse_count = 0
        self._total_defects_found = 0

        self._init_citation_extractor()
        self._init_entity_extractor()

    # -- lazy loaders -------------------------------------------------------

    def _init_citation_extractor(self) -> None:
        """Lazy-load CitationExtractor with graceful fallback."""
        if not self._use_citations:
            return
        try:
            from legal_ai.citation_extractor import CitationExtractor

            self._citation_extractor = CitationExtractor(
                use_eyecite=False, validate_against_db=False
            )
            self._citation_available = True
            logger.info("CitationExtractor loaded for opinion parsing")
        except Exception:
            logger.warning(
                "CitationExtractor unavailable — citation extraction disabled"
            )

    def _init_entity_extractor(self) -> None:
        """Lazy-load EntityExtractor with graceful fallback."""
        if not self._use_entities:
            return
        try:
            from legal_ai.entity_extractor import EntityExtractor

            self._entity_extractor = EntityExtractor(use_spacy=False)
            self._entity_available = True
            logger.info("EntityExtractor loaded for opinion parsing")
        except Exception:
            logger.warning(
                "EntityExtractor unavailable — entity extraction disabled"
            )

    # -- public API ---------------------------------------------------------

    def parse(
        self,
        order_text: str,
        order_metadata: Optional[Dict[str, Any]] = None,
    ) -> ParsedOpinion:
        """Parse a court order into structured sections, defects, and metadata."""
        t0 = time.perf_counter()
        meta = order_metadata or {}
        warnings: List[str] = []

        if not order_text or not order_text.strip():
            warnings.append("Empty order text provided")
            return ParsedOpinion(
                parse_time_ms=_elapsed_ms(t0), warnings=warnings
            )

        text = order_text.strip()

        # Classify order type
        order_type = self.classify_order_type(text)

        # Segment sections
        sections = self._segment_sections(text)

        # Detect procedural defects
        defects = self.detect_defects(text)

        # Extract citations
        citations: List[str] = []
        if self._citation_available and self._citation_extractor is not None:
            try:
                cit_result = self._citation_extractor.extract(text)
                citations = [c.canonical for c in cit_result.citations]
            except Exception as exc:
                warnings.append(f"Citation extraction failed: {exc}")

        # Extract entities
        entities: List[str] = []
        if self._entity_available and self._entity_extractor is not None:
            try:
                ent_result = self._entity_extractor.extract(text)
                entities = [e.text for e in ent_result.entities]
            except Exception as exc:
                warnings.append(f"Entity extraction failed: {exc}")

        # Enrich sections with citations/entities
        for section in sections:
            if self._citation_available and self._citation_extractor is not None:
                try:
                    sec_cit = self._citation_extractor.extract(section.text)
                    section.citations = [c.canonical for c in sec_cit.citations]
                except Exception:
                    pass
            if self._entity_available and self._entity_extractor is not None:
                try:
                    sec_ent = self._entity_extractor.extract(section.text)
                    section.entities = [e.text for e in sec_ent.entities]
                except Exception:
                    pass

        # Collect holdings, findings, conclusions, relief
        holdings = [
            s.text for s in sections if s.section_type in ("holding", "order")
        ]
        findings = [
            s.text for s in sections if s.section_type == "finding_of_fact"
        ]
        conclusions = [
            s.text for s in sections if s.section_type == "conclusion_of_law"
        ]
        relief_granted = self._extract_relief_granted(text)
        relief_denied = self._extract_relief_denied(text)

        # Extract metadata from text
        order_date = meta.get("order_date", "") or self._extract_date(text)
        judge = meta.get("judge", "") or self._extract_judge(text)
        case_number = meta.get("case_number", "") or self._extract_case_number(text)
        court = meta.get("court", "")

        is_ex_parte = order_type == "ex_parte"
        has_findings = len(findings) > 0
        has_best_interest = bool(_BEST_INTEREST_RE.search(text))

        self._parse_count += 1
        self._total_defects_found += len(defects)

        return ParsedOpinion(
            order_id=meta.get("order_id", ""),
            order_date=order_date,
            court=court,
            judge=judge,
            case_number=case_number,
            order_type=order_type,
            sections=sections,
            holdings=holdings,
            findings_of_fact=findings,
            conclusions_of_law=conclusions,
            relief_granted=relief_granted,
            relief_denied=relief_denied,
            procedural_defects=defects,
            citations_found=citations,
            entities_found=entities,
            is_ex_parte=is_ex_parte,
            has_required_findings=has_findings,
            has_best_interest_analysis=has_best_interest,
            parse_time_ms=_elapsed_ms(t0),
            warnings=warnings,
        )

    def detect_defects(self, order_text: str) -> List[ProceduralDefect]:
        """Detect procedural defects in a court order using pattern matching."""
        defects: List[ProceduralDefect] = []
        text_lower = order_text.lower()

        # Ex-parte detection
        ep = DEFECT_PATTERNS["ex_parte"]
        ep_hits = [ind for ind in ep["indicators"] if ind in text_lower]
        ep_neg = [neg for neg in ep["negative_indicators"] if neg in text_lower]
        if ep_hits and not ep_neg:
            defects.append(ProceduralDefect(
                defect_type="ex_parte",
                description=(
                    f"Order appears to be entered ex parte. "
                    f"Indicators: {', '.join(ep_hits)}"
                ),
                severity=ep["severity"],
                authority=ep["authority"],
                evidence_text=ep_hits[0],
                confidence=min(0.5 + 0.15 * len(ep_hits), 0.95),
            ))

        # Missing notice
        mn = DEFECT_PATTERNS["missing_notice"]
        mn_hits = [ind for ind in mn["indicators"] if ind in text_lower]
        if mn_hits:
            defects.append(ProceduralDefect(
                defect_type="missing_notice",
                description=(
                    f"Notice deficiency detected. "
                    f"Indicators: {', '.join(mn_hits)}"
                ),
                severity=mn["severity"],
                authority=mn["authority"],
                evidence_text=mn_hits[0],
                confidence=0.80,
            ))

        # Missing findings (custody/parenting time context)
        mf = DEFECT_PATTERNS["missing_findings"]
        involves_custody = any(kw in text_lower for kw in mf["required_for"])
        if involves_custody:
            has_required = any(kw in text_lower for kw in mf["must_contain"])
            if not has_required:
                defects.append(ProceduralDefect(
                    defect_type="missing_findings",
                    description=(
                        "Order affects custody/parenting time but lacks "
                        "required best-interest findings under MCL 722.23"
                    ),
                    severity=mf["severity"],
                    authority=mf["authority"],
                    evidence_text="",
                    confidence=0.75,
                ))

        # Missing hearing
        mh = DEFECT_PATTERNS["missing_hearing"]
        mh_hits = [ind for ind in mh["indicators"] if ind in text_lower]
        # Only flag if not already flagged as ex-parte (avoids double-flag)
        if mh_hits and not any(d.defect_type == "ex_parte" for d in defects):
            defects.append(ProceduralDefect(
                defect_type="missing_hearing",
                description=(
                    f"No hearing appears to have been held. "
                    f"Indicators: {', '.join(mh_hits)}"
                ),
                severity=mh["severity"],
                authority=mh["authority"],
                evidence_text=mh_hits[0],
                confidence=0.70,
            ))

        # Missing service
        ms = DEFECT_PATTERNS["missing_service"]
        ms_hits = [ind for ind in ms["indicators"] if ind in text_lower]
        if ms_hits:
            defects.append(ProceduralDefect(
                defect_type="missing_service",
                description=(
                    f"Service deficiency detected. "
                    f"Indicators: {', '.join(ms_hits)}"
                ),
                severity=ms["severity"],
                authority=ms["authority"],
                evidence_text=ms_hits[0],
                confidence=0.80,
            ))

        # Missing signature
        msig = DEFECT_PATTERNS["missing_signature"]
        msig_hits = [ind for ind in msig["indicators"] if ind in text_lower]
        if msig_hits:
            defects.append(ProceduralDefect(
                defect_type="missing_signature",
                description=(
                    f"Signature deficiency detected. "
                    f"Indicators: {', '.join(msig_hits)}"
                ),
                severity=msig["severity"],
                authority=msig["authority"],
                evidence_text=msig_hits[0],
                confidence=0.70,
            ))

        return defects

    def classify_order_type(self, order_text: str) -> str:
        """Classify the type of court order (ex_parte, stipulated, contested, default, emergency)."""
        scores: Dict[str, int] = {}
        for otype, patterns in _ORDER_TYPE_PATTERNS.items():
            hits = sum(1 for p in patterns if p.search(order_text))
            if hits > 0:
                scores[otype] = hits

        if not scores:
            return "contested"  # default assumption

        # Ex-parte trumps contested when both indicators are present
        if "ex_parte" in scores and "contested" in scores:
            if scores["ex_parte"] >= scores["contested"]:
                return "ex_parte"
            return "contested"

        return max(scores, key=scores.get)  # type: ignore[arg-type]

    def parse_batch(
        self,
        texts: List[str],
        metadata_list: Optional[List[Dict[str, Any]]] = None,
    ) -> List[ParsedOpinion]:
        """Parse multiple court orders."""
        results: List[ParsedOpinion] = []
        metas = metadata_list or [{}] * len(texts)
        for text, meta in zip(texts, metas):
            try:
                results.append(self.parse(text, meta))
            except Exception as exc:
                logger.error("Batch parse error: %s", exc)
                results.append(ParsedOpinion(
                    warnings=[f"Parse failed: {exc}"],
                ))
        return results

    def get_stats(self) -> Dict[str, Any]:
        """Return parser status and capabilities."""
        return {
            "version": "1.0.0",
            "citation_extractor_available": self._citation_available,
            "entity_extractor_available": self._entity_available,
            "defect_patterns": len(DEFECT_PATTERNS),
            "section_patterns": len(_SECTION_PATTERNS),
            "order_type_patterns": len(_ORDER_TYPE_PATTERNS),
            "orders_parsed": self._parse_count,
            "total_defects_found": self._total_defects_found,
        }

    # -- private helpers ----------------------------------------------------

    def _segment_sections(self, text: str) -> List[OrderSection]:
        """Split order text into structural sections."""
        matches: List[Tuple[int, int, str]] = []
        for section_type, pattern in _SECTION_PATTERNS:
            for m in pattern.finditer(text):
                matches.append((m.start(), m.end(), section_type))

        if not matches:
            return [OrderSection(
                section_type="order",
                text=text,
                start_offset=0,
                end_offset=len(text),
                confidence=0.3,
            )]

        matches.sort(key=lambda x: x[0])
        sections: List[OrderSection] = []

        # If text before first match, treat as caption/heading
        if matches[0][0] > 0:
            pre_text = text[: matches[0][0]].strip()
            if pre_text:
                sections.append(OrderSection(
                    section_type="caption",
                    text=pre_text,
                    start_offset=0,
                    end_offset=matches[0][0],
                    confidence=0.5,
                ))

        for i, (start, header_end, section_type) in enumerate(matches):
            end = matches[i + 1][0] if i + 1 < len(matches) else len(text)
            section_text = text[start:end].strip()
            if section_text:
                sections.append(OrderSection(
                    section_type=section_type,
                    text=section_text,
                    start_offset=start,
                    end_offset=end,
                    confidence=0.7,
                ))

        return sections

    def _extract_relief_granted(self, text: str) -> List[str]:
        """Extract relief/orders granted."""
        results: List[str] = []
        for m in _RELIEF_GRANTED_RE.finditer(text):
            item = m.group(1).strip()
            if len(item) > 10:
                results.append(item[:500])
        return results

    def _extract_relief_denied(self, text: str) -> List[str]:
        """Extract denied relief items."""
        results: List[str] = []
        for m in _RELIEF_DENIED_RE.finditer(text):
            item = m.group(1).strip()
            if len(item) > 5:
                results.append(item[:500])
        return results

    def _extract_date(self, text: str) -> str:
        """Extract order date from text."""
        m = _ORDER_DATE_RE.search(text)
        return m.group(1).strip() if m else ""

    def _extract_judge(self, text: str) -> str:
        """Extract judge name from text."""
        m = _JUDGE_RE.search(text)
        return m.group(1).strip() if m else ""

    def _extract_case_number(self, text: str) -> str:
        """Extract case number from text."""
        m = _CASE_NUMBER_RE.search(text)
        return m.group(1).strip() if m else ""


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _elapsed_ms(t0: float) -> float:
    return (time.perf_counter() - t0) * 1000.0
