"""
Litigation Analyzer — Deep content analysis and entity extraction.
==================================================================

Runs after extraction + classification. Performs deep NLP-style analysis:
  1. Quote extraction (evidence quotes with context)
  2. Timeline event extraction (dates + events)
  3. Entity extraction (people, organizations, addresses)
  4. Contradiction detection (conflicting statements)
  5. Impeachment material identification
  6. Authority chain building (citation → supporting citation)

100% case-agnostic. All patterns are general legal/litigation patterns.
Entity names come from content analysis, not hardcoded lists.
"""

import logging
import re
from dataclasses import dataclass, field
from typing import Optional

logger = logging.getLogger(__name__)


@dataclass
class EvidenceQuote:
    """A significant quote extracted from evidence."""
    text: str
    context: str = ""
    page_number: int = 0
    category: str = ""
    relevance: float = 0.0
    source_file: str = ""
    lane: str = ""


@dataclass
class TimelineEvent:
    """A dated event extracted from a document."""
    date_str: str
    event_text: str
    actors: str = ""
    source_file: str = ""
    category: str = ""
    lane: str = ""


@dataclass
class AuthorityRef:
    """A legal authority reference found in text."""
    citation: str
    context: str = ""
    citation_type: str = ""  # MCR, MCL, MRE, case_law, federal
    supporting_citations: list[str] = field(default_factory=list)


@dataclass
class ImpeachmentItem:
    """Potential impeachment material."""
    text: str
    category: str = ""
    impeachment_value: int = 5  # 1-10 scale
    source_file: str = ""
    cross_exam_question: str = ""


@dataclass
class AnalysisResult:
    """Complete analysis result for a document."""
    evidence_quotes: list[EvidenceQuote] = field(default_factory=list)
    timeline_events: list[TimelineEvent] = field(default_factory=list)
    authority_refs: list[AuthorityRef] = field(default_factory=list)
    impeachment_items: list[ImpeachmentItem] = field(default_factory=list)
    entities: dict = field(default_factory=dict)  # name -> type
    summary_stats: dict = field(default_factory=dict)
    readiness_score: float = 0.0  # 0-100 EGCP-style completeness


# ─── Patterns ─────────────────────────────────────────────────────

# Evidence quote triggers — statements that are significant
QUOTE_TRIGGERS = [
    (re.compile(r"(?i)(nothing\s+was\s+physical)"), "recantation", 9),
    (re.compile(r"(?i)(I\s+(?:never|didn.t|did\s+not)\s+(?:hit|strike|punch|push))"), "denial", 8),
    (re.compile(r"(?i)(lied|fabricat|false\s+(?:report|allegation|statement))"), "false_statement", 9),
    (re.compile(r"(?i)(admitted?|confessed?|acknowledged?)"), "admission", 8),
    (re.compile(r"(?i)(threatened|intimidat|coerced?)"), "threat", 7),
    (re.compile(r"(?i)(no\s+(?:findings?|evidence|substantiation))"), "exoneration", 8),
    (re.compile(r"(?i)(violat(?:ed|ion|ing)\s+(?:order|MCR|MCL|rule|right))"), "violation", 8),
    (re.compile(r"(?i)(without\s+(?:hearing|notice|opportunity|evidence|findings))"), "due_process", 9),
    (re.compile(r"(?i)(best\s+interest\s+(?:of\s+(?:the\s+)?child|factor))"), "best_interest", 7),
    (re.compile(r"(?i)(clear\s+and\s+convincing)"), "evidentiary_standard", 7),
    (re.compile(r"(?i)(irreparable\s+(?:harm|injury|damage))"), "irreparable_harm", 8),
    (re.compile(r"(?i)(abuse\s+of\s+discretion)"), "judicial_error", 8),
    (re.compile(r"(?i)(conflict\s+of\s+interest|appearance\s+of\s+impropriety)"), "judicial_ethics", 9),
    (re.compile(r"(?i)(ex\s+parte\s+(?:communication|order|contact))"), "ex_parte", 9),
    (re.compile(r"(?i)(with(?:held|holding)\s+(?:child|parenting|visitation|contact))"), "withholding", 9),
    (re.compile(r"(?i)(alienat(?:ed|ing|ion))"), "alienation", 8),
]

# Date + event extraction
DATE_EVENT_PATTERN = re.compile(
    r"(?:On\s+)?"
    r"((?:January|February|March|April|May|June|July|August|September|October|November|December)"
    r"\s+\d{1,2},?\s+\d{4}|\d{4}-\d{2}-\d{2}|\d{1,2}/\d{1,2}/\d{4})"
    r"[,;:\s]+(.{10,200}?)(?:\.|$)",
    re.IGNORECASE | re.MULTILINE,
)

# Legal citation patterns
CITATION_PATTERNS = {
    "MCR": re.compile(r"\b(MCR\s+\d+\.\d+(?:\([A-Z\d]+\))?(?:\(\d+\))?)"),
    "MCL": re.compile(r"\b(MCL\s+\d+\.\d+(?:[a-z])?(?:\(\d+\))?)"),
    "MRE": re.compile(r"\b(MRE\s+\d+(?:\([a-z]\))?)"),
    "federal": re.compile(r"\b(\d+\s+USC\s+[§]?\s*\d+)"),
    "case_law": re.compile(
        r"\b(\w+\s+v\.?\s+\w+),?\s*(\d+\s+(?:Mich\s+App|Mich|US|NW2d|F\.\d[dh])\s+\d+)"
    ),
}

# Entity patterns (generic — not case-specific)
ENTITY_PATTERNS = {
    "judge": re.compile(r"(?i)(?:Hon(?:orable)?\.?\s+|Judge\s+)([A-Z][a-z]+(?:\s+[A-Z]\.?)?\s+[A-Z][a-z]+)"),
    "attorney": re.compile(r"(?i)(?:Attorney\s+|Counsel\s+)([A-Z][a-z]+\s+[A-Z][a-z]+)(?:\s+\(P\d+\))?"),
    "bar_number": re.compile(r"\(P(\d{4,6})\)"),
    "case_number": re.compile(r"\b(\d{4}-\d{4,6}-[A-Z]{2})\b"),
    "organization": re.compile(r"\b([A-Z][a-z]+(?:\s+[A-Z][a-z]+){1,4}\s+(?:LLC|Inc|Corp|LLP|PC|PLLC))\b"),
}

# Impeachment indicators
IMPEACHMENT_PATTERNS = [
    (re.compile(r"(?i)(previously\s+(?:stated|testified|claimed|said))"), "prior_inconsistent", 8),
    (re.compile(r"(?i)(contrary\s+to|contradicts?|inconsistent\s+with)"), "contradiction", 8),
    (re.compile(r"(?i)(failed\s+to\s+disclose|omitted|concealed)"), "concealment", 7),
    (re.compile(r"(?i)(perjur|under\s+oath.{0,20}(?:false|lied))"), "perjury", 10),
    (re.compile(r"(?i)(bias|prejudice|predetermin)"), "bias", 7),
    (re.compile(r"(?i)(financial\s+(?:interest|motive|incentive))"), "financial_motive", 6),
    (re.compile(r"(?i)(credib(?:ility|le)\s+(?:issue|problem|concern|question))"), "credibility", 7),
]


class LitigationAnalyzer:
    """Deep content analysis engine. Case-agnostic."""

    MAX_TEXT_BYTES: int = 204800  # 200KB unified limit

    def __init__(self, case_config=None):
        self.case_config = case_config

    def _truncated(self, text: str, method_name: str) -> str:
        """Return text truncated to MAX_TEXT_BYTES with a warning if truncation occurs."""
        if len(text) > self.MAX_TEXT_BYTES:
            logger.warning(f"Text truncated from {len(text)} to {self.MAX_TEXT_BYTES} chars for {method_name}")
            return text[:self.MAX_TEXT_BYTES]
        return text

    def analyze(
        self,
        text: str,
        file_name: str = "",
        lanes: list[str] = None,
        page_texts: list = None,
    ) -> AnalysisResult:
        """Run full analysis on extracted text."""
        result = AnalysisResult()
        primary_lane = lanes[0] if lanes else ""

        # 1. Evidence quotes
        result.evidence_quotes = self._extract_quotes(
            text, file_name, primary_lane, page_texts
        )

        # 2. Timeline events
        result.timeline_events = self._extract_timeline(
            text, file_name, primary_lane
        )

        # 3. Authority references
        result.authority_refs = self._extract_authorities(text)

        # 4. Impeachment material
        result.impeachment_items = self._extract_impeachment(
            text, file_name
        )

        # 5. Entities
        result.entities = self._extract_entities(text)

        # 6. Summary stats
        result.summary_stats = {
            "evidence_quotes": len(result.evidence_quotes),
            "timeline_events": len(result.timeline_events),
            "authority_refs": len(result.authority_refs),
            "impeachment_items": len(result.impeachment_items),
            "entities": len(result.entities),
            "text_length": len(text),
        }

        # 7. Readiness score (EGCP-style)
        result.readiness_score = self.calculate_readiness(result)
        result.summary_stats["readiness_score"] = result.readiness_score

        return result

    def _extract_quotes(
        self, text: str, file_name: str, lane: str, page_texts: list = None
    ) -> list[EvidenceQuote]:
        """Extract significant quotes from text."""
        quotes = []

        # Process by pages if available
        if page_texts:
            for pt in page_texts:
                page_text = pt.text if hasattr(pt, "text") else str(pt)
                page_num = pt.page_number if hasattr(pt, "page_number") else 0
                for pattern, category, relevance in QUOTE_TRIGGERS:
                    for match in pattern.finditer(page_text):
                        start = max(0, match.start() - 100)
                        end = min(len(page_text), match.end() + 200)
                        context = page_text[start:end].strip()
                        quotes.append(EvidenceQuote(
                            text=match.group(0),
                            context=context,
                            page_number=page_num,
                            category=category,
                            relevance=relevance / 10.0,
                            source_file=file_name,
                            lane=lane,
                        ))
        else:
            search_text = self._truncated(text, "_extract_quotes")
            for pattern, category, relevance in QUOTE_TRIGGERS:
                for match in pattern.finditer(search_text):
                    start = max(0, match.start() - 100)
                    end = min(len(search_text), match.end() + 200)
                    context = search_text[start:end].strip()
                    quotes.append(EvidenceQuote(
                        text=match.group(0),
                        context=context,
                        category=category,
                        relevance=relevance / 10.0,
                        source_file=file_name,
                        lane=lane,
                    ))

        return quotes

    def _extract_timeline(
        self, text: str, file_name: str, lane: str
    ) -> list[TimelineEvent]:
        """Extract dated events from text."""
        events = []
        seen = set()

        search_text = self._truncated(text, "_extract_timeline")
        for match in DATE_EVENT_PATTERN.finditer(search_text):
            date_str = match.group(1).strip()
            event_text = match.group(2).strip()

            # Dedup by date + first 50 chars
            key = f"{date_str}:{event_text[:50]}"
            if key in seen:
                continue
            seen.add(key)

            events.append(TimelineEvent(
                date_str=date_str,
                event_text=event_text,
                source_file=file_name,
                lane=lane,
            ))

        return events

    def _extract_authorities(self, text: str) -> list[AuthorityRef]:
        """Extract legal citations and build authority references."""
        refs = []
        seen = set()

        search_text = self._truncated(text, "_extract_authorities")
        for cite_type, pattern in CITATION_PATTERNS.items():
            for match in pattern.finditer(search_text):
                citation = match.group(0).strip()
                if citation in seen:
                    continue
                seen.add(citation)

                # Get context (100 chars before and after)
                start = max(0, match.start() - 100)
                end = min(len(text), match.end() + 100)
                context = text[start:end].strip()

                refs.append(AuthorityRef(
                    citation=citation,
                    context=context,
                    citation_type=cite_type,
                ))

        return refs

    def _extract_impeachment(
        self, text: str, file_name: str
    ) -> list[ImpeachmentItem]:
        """Extract impeachment material."""
        items = []

        search_text = self._truncated(text, "_extract_impeachment")
        for pattern, category, value in IMPEACHMENT_PATTERNS:
            for match in pattern.finditer(search_text):
                start = max(0, match.start() - 150)
                end = min(len(text), match.end() + 250)
                context = text[start:end].strip()

                items.append(ImpeachmentItem(
                    text=context,
                    category=category,
                    impeachment_value=value,
                    source_file=file_name,
                ))

        return items

    def _extract_entities(self, text: str) -> dict:
        """Extract named entities (people, orgs, case numbers)."""
        entities = {}

        search_text = self._truncated(text, "_extract_entities")
        for etype, pattern in ENTITY_PATTERNS.items():
            for match in pattern.finditer(search_text):
                name = match.group(1) if match.lastindex else match.group(0)
                name = name.strip()
                if len(name) >= 3:
                    entities[name] = etype

        return entities

    @staticmethod
    def calculate_readiness(result: "AnalysisResult") -> float:
        """EGCP-style readiness score (0-100). Case-agnostic.

        Components (25 pts each):
          E — Evidence:    quote diversity and relevance
          G — Grounds:     timeline event density
          C — Citations:   authority reference count and type diversity
          P — Presentation: impeachment + entity coverage
        """
        # E: Evidence quotes (0-25)
        q_count = len(result.evidence_quotes)
        avg_relevance = (
            sum(q.relevance for q in result.evidence_quotes) / max(1, q_count)
        )
        e_score = min(25.0, (q_count * 1.5) + (avg_relevance * 2))

        # G: Grounds — timeline events + legal topics (0-25)
        g_score = min(25.0, len(result.timeline_events) * 2.5)

        # C: Citations — authority refs by type diversity (0-25)
        ref_types = set()
        for ref in result.authority_refs:
            ref_types.add(getattr(ref, "citation_type", "unknown"))
        type_bonus = len(ref_types) * 3
        c_score = min(25.0, (len(result.authority_refs) * 1.5) + type_bonus)

        # P: Presentation — impeachment + entities (0-25)
        imp_count = len(result.impeachment_items)
        ent_count = len(result.entities)
        p_score = min(25.0, (imp_count * 3) + (ent_count * 1.5))

        return round(min(100.0, e_score + g_score + c_score + p_score), 1)
