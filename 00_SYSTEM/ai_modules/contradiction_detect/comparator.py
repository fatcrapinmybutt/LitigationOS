"""Compare normalized statements and detect contradictions."""
from __future__ import annotations

import logging
from dataclasses import dataclass, field
from difflib import SequenceMatcher
from typing import Optional

try:
    from sklearn.feature_extraction.text import TfidfVectorizer
    from sklearn.metrics.pairwise import cosine_similarity
    _HAS_SKLEARN = True
except ImportError:  # pragma: no cover
    _HAS_SKLEARN = False

from . import config
from .normalizer import NormalizedStatement

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Data classes
# ---------------------------------------------------------------------------

@dataclass
class ComparisonResult:
    """Result of comparing two normalized statements."""

    similarity_score: float = 0.0
    topic_match: bool = False
    factual_match: bool = True
    is_contradiction: bool = False
    contradiction_type: Optional[str] = None


@dataclass
class Contradiction:
    """A detected contradiction between two statements."""

    statement_a: NormalizedStatement
    statement_b: NormalizedStatement
    contradiction_type: str = "DIRECT"
    severity: str = "MINOR"
    explanation: str = ""
    evidence_citations: list[str] = field(default_factory=list)


# ---------------------------------------------------------------------------
# Comparator
# ---------------------------------------------------------------------------

class StatementComparator:
    """Pairwise comparison engine for normalized statements."""

    def __init__(self) -> None:
        self._sim_threshold = config.SIMILARITY_THRESHOLD
        self._contra_threshold = config.CONTRADICTION_THRESHOLD

    # ------------------------------------------------------------------
    # Single-pair comparison
    # ------------------------------------------------------------------

    def compare_pair(
        self,
        stmt1: NormalizedStatement,
        stmt2: NormalizedStatement,
    ) -> ComparisonResult:
        """Compare two statements and return a *ComparisonResult*."""
        topic_sim = self._topic_similarity(stmt1, stmt2)

        # Entity overlap — shared entities boost topic relevance
        shared_entities = set(stmt1.entities) & set(stmt2.entities)
        entity_sim = (
            len(shared_entities) / max(len(set(stmt1.entities) | set(stmt2.entities)), 1)
        )

        # Combined topic signal: keyword similarity + entity overlap
        combined_topic = max(topic_sim, (topic_sim + entity_sim) / 2)
        topic_match = combined_topic >= self._sim_threshold

        # Text-level similarity (SequenceMatcher)
        text_sim = SequenceMatcher(
            None, stmt1.canonical_text, stmt2.canonical_text,
        ).ratio()

        # Unique-word divergence: how many words differ between statements
        words_a = set(stmt1.canonical_text.split())
        words_b = set(stmt2.canonical_text.split())
        union = words_a | words_b
        divergence = len((words_a - words_b) | (words_b - words_a)) / max(len(union), 1)

        # Contradiction: same topic, but either low text similarity or high divergence
        factual_match = text_sim >= self._sim_threshold and divergence < 0.4
        is_contradiction = topic_match and (
            text_sim < self._contra_threshold
            or (divergence >= 0.4 and not factual_match)
        )

        # Determine contradiction type
        ctype: Optional[str] = None
        if is_contradiction:
            ctype = self._classify_type(stmt1, stmt2, topic_sim, text_sim)

        return ComparisonResult(
            similarity_score=text_sim,
            topic_match=topic_match,
            factual_match=factual_match,
            is_contradiction=is_contradiction,
            contradiction_type=ctype,
        )

    # ------------------------------------------------------------------
    # Batch contradiction finder
    # ------------------------------------------------------------------

    def find_contradictions(
        self,
        statements: list[NormalizedStatement],
    ) -> list[Contradiction]:
        """Pairwise scan for contradictions with early-termination."""
        contradictions: list[Contradiction] = []
        n = len(statements)
        logger.info("Comparing %d statements (%d pairs)", n, n * (n - 1) // 2)

        for i in range(n):
            for j in range(i + 1, n):
                a, b = statements[i], statements[j]

                # Skip pairs from the same document + same page
                if (
                    a.original.source_file
                    and a.original.source_file == b.original.source_file
                    and a.original.page_number == b.original.page_number
                ):
                    continue

                result = self.compare_pair(a, b)
                if result.is_contradiction:
                    severity = self._assess_severity(a, b, result)
                    explanation = self._build_explanation(a, b, result)
                    citations = self._build_citations(a, b)

                    contradictions.append(Contradiction(
                        statement_a=a,
                        statement_b=b,
                        contradiction_type=result.contradiction_type or "DIRECT",
                        severity=severity,
                        explanation=explanation,
                        evidence_citations=citations,
                    ))

        logger.info("Found %d contradictions", len(contradictions))
        return contradictions

    # ------------------------------------------------------------------
    # Internals
    # ------------------------------------------------------------------

    def _topic_similarity(
        self,
        a: NormalizedStatement,
        b: NormalizedStatement,
    ) -> float:
        """Compute topic similarity via TF-IDF cosine or keyword overlap."""
        kw_a = " ".join(a.topic_keywords)
        kw_b = " ".join(b.topic_keywords)

        if not kw_a or not kw_b:
            return 0.0

        if _HAS_SKLEARN:
            try:
                vec = TfidfVectorizer()
                tfidf = vec.fit_transform([kw_a, kw_b])
                return float(cosine_similarity(tfidf[0:1], tfidf[1:2])[0, 0])
            except ValueError:
                pass

        # Fallback: Jaccard overlap
        set_a, set_b = set(a.topic_keywords), set(b.topic_keywords)
        union = set_a | set_b
        if not union:
            return 0.0
        return len(set_a & set_b) / len(union)

    @staticmethod
    def _classify_type(
        a: NormalizedStatement,
        b: NormalizedStatement,
        topic_sim: float,
        text_sim: float,
    ) -> str:
        """Classify the contradiction into a specific type."""
        # Temporal: both have dates that differ
        if a.date_normalized and b.date_normalized and a.date_normalized != b.date_normalized:
            return "TEMPORAL"

        # Magnitude: shared numeric entities with different values
        nums_a = {e for e in a.entities if any(c.isdigit() for c in e)}
        nums_b = {e for e in b.entities if any(c.isdigit() for c in e)}
        if nums_a and nums_b and nums_a != nums_b:
            return "MAGNITUDE"

        # Evolution: same speaker, different claims over time
        if (
            a.original.speaker == b.original.speaker
            and a.original.speaker != "Unknown"
        ):
            return "EVOLUTION"

        return "DIRECT"

    @staticmethod
    def _assess_severity(
        a: NormalizedStatement,
        b: NormalizedStatement,
        result: ComparisonResult,
    ) -> str:
        """Assign CRITICAL / MAJOR / MINOR severity."""
        score = 0.0

        # Same speaker contradicting themselves
        if (
            a.original.speaker == b.original.speaker
            and a.original.speaker != "Unknown"
        ):
            score += 2.0

        # Sworn testimony
        if a.original.is_sworn or b.original.is_sworn:
            score += 1.5

        # Topic match but very low text similarity
        if result.similarity_score < 0.2:
            score += 1.0

        if score >= 3.0:
            return "CRITICAL"
        if score >= 1.5:
            return "MAJOR"
        return "MINOR"

    @staticmethod
    def _build_explanation(
        a: NormalizedStatement,
        b: NormalizedStatement,
        result: ComparisonResult,
    ) -> str:
        """Human-readable explanation of the contradiction."""
        parts: list[str] = []
        ctype = result.contradiction_type or "DIRECT"
        parts.append(f"{ctype} contradiction detected.")

        if a.original.speaker == b.original.speaker and a.original.speaker != "Unknown":
            parts.append(f"Same speaker ({a.original.speaker}) made conflicting claims.")
        else:
            speakers = {a.original.speaker, b.original.speaker} - {"Unknown"}
            if speakers:
                parts.append(f"Involves: {', '.join(sorted(speakers))}.")

        parts.append(f"Text similarity: {result.similarity_score:.2f}.")
        return " ".join(parts)

    @staticmethod
    def _build_citations(
        a: NormalizedStatement,
        b: NormalizedStatement,
    ) -> list[str]:
        """Build source citation strings for the two statements."""
        cites: list[str] = []
        for label, s in [("A", a), ("B", b)]:
            src = s.original.source_file or "<unknown>"
            pg = s.original.page_number
            cites.append(f"[{label}] {src}, p.{pg}, line {s.original.line_number}")
        return cites
