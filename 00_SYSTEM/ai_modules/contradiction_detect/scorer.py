"""Score contradictions by severity and impeachment value."""
from __future__ import annotations

import logging
from dataclasses import dataclass

from . import config
from .comparator import Contradiction

logger = logging.getLogger(__name__)


@dataclass
class ScoredContradiction:
    """A *Contradiction* enriched with numeric scoring."""

    # Original contradiction fields
    statement_a: object
    statement_b: object
    contradiction_type: str = "DIRECT"
    severity: str = "MINOR"
    explanation: str = ""
    evidence_citations: list = None  # type: ignore[assignment]

    # Scoring additions
    severity_score: float = 0.0      # 0–100
    impeachment_value: str = "LOW"   # LOW / MEDIUM / HIGH / EXTREME
    legal_significance: str = "LOW"  # LOW / MEDIUM / HIGH

    def __post_init__(self) -> None:
        if self.evidence_citations is None:
            self.evidence_citations = []


class ContradictionScorer:
    """Assign numeric severity, impeachment value, and legal significance."""

    # Weights (tune as case evolves)
    _W_SAME_SPEAKER = 25.0
    _W_SWORN = 20.0
    _W_MATERIAL = 15.0
    _W_RECENT = 10.0
    _W_CUMULATIVE_PENALTY = 5.0

    def __init__(self) -> None:
        self._speaker_counts: dict[str, int] = {}

    def reset_counts(self) -> None:
        """Reset cumulative speaker contradiction counts."""
        self._speaker_counts = {}

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def score(self, contradiction: Contradiction) -> ScoredContradiction:
        """Produce a *ScoredContradiction* from a raw *Contradiction*."""
        points = 0.0

        a_orig = contradiction.statement_a.original
        b_orig = contradiction.statement_b.original

        # ---- Same speaker contradicting themselves ----
        if a_orig.speaker == b_orig.speaker and a_orig.speaker != "Unknown":
            points += self._W_SAME_SPEAKER
            # Cumulative penalty
            speaker = a_orig.speaker
            self._speaker_counts[speaker] = self._speaker_counts.get(speaker, 0) + 1
            points += self._W_CUMULATIVE_PENALTY * (self._speaker_counts[speaker] - 1)

        # ---- Sworn testimony ----
        if a_orig.is_sworn or b_orig.is_sworn:
            points += self._W_SWORN
        if a_orig.is_sworn and b_orig.is_sworn:
            points += self._W_SWORN * 0.5  # double-sworn = even worse

        # ---- Material fact detection ----
        if self._is_material(contradiction):
            points += self._W_MATERIAL

        # ---- Recency boost ----
        if self._is_recent(contradiction):
            points += self._W_RECENT

        # ---- Contradiction type modifier ----
        type_mods = {
            "DIRECT": 1.2,
            "TEMPORAL": 1.1,
            "MAGNITUDE": 1.0,
            "EVOLUTION": 0.9,
            "OMISSION": 0.8,
        }
        points *= type_mods.get(contradiction.contradiction_type, 1.0)

        # Clamp to 0–100
        severity_score = min(max(round(points, 1), 0.0), 100.0)

        # Derive labels
        impeachment = self._impeachment_label(severity_score)
        legal_sig = self._legal_significance(contradiction, severity_score)
        severity = self._severity_label(severity_score)

        return ScoredContradiction(
            statement_a=contradiction.statement_a,
            statement_b=contradiction.statement_b,
            contradiction_type=contradiction.contradiction_type,
            severity=severity,
            explanation=contradiction.explanation,
            evidence_citations=contradiction.evidence_citations,
            severity_score=severity_score,
            impeachment_value=impeachment,
            legal_significance=legal_sig,
        )

    def score_batch(
        self, contradictions: list[Contradiction],
    ) -> list[ScoredContradiction]:
        """Score a list of contradictions, respecting cumulative penalties."""
        self.reset_counts()
        return [self.score(c) for c in contradictions]

    # ------------------------------------------------------------------
    # Internals
    # ------------------------------------------------------------------

    @staticmethod
    def _is_material(c: Contradiction) -> bool:
        """Heuristic: material facts involve custody, money, safety, or dates."""
        material_kw = {
            "custody", "visitation", "parenting", "child", "children",
            "income", "payment", "support", "money", "financial",
            "safety", "abuse", "neglect", "harm", "danger",
            "order", "court", "violation", "contempt",
        }
        combined = " ".join(
            c.statement_a.topic_keywords + c.statement_b.topic_keywords
        ).lower()
        return any(kw in combined for kw in material_kw)

    @staticmethod
    def _is_recent(c: Contradiction) -> bool:
        """Heuristic: 2024-2026 dates count as recent."""
        for s in [c.statement_a, c.statement_b]:
            d = s.date_normalized
            if d and d >= "2024-01-01":
                return True
        return False

    @staticmethod
    def _impeachment_label(score: float) -> str:
        if score >= 70:
            return "EXTREME"
        if score >= 50:
            return "HIGH"
        if score >= 30:
            return "MEDIUM"
        return "LOW"

    @staticmethod
    def _severity_label(score: float) -> str:
        if score >= 60:
            return "CRITICAL"
        if score >= 30:
            return "MAJOR"
        return "MINOR"

    @staticmethod
    def _legal_significance(c: Contradiction, score: float) -> str:
        """Determine legal significance for Michigan family law context."""
        if score >= 60:
            return "HIGH"
        if score >= 30 or c.contradiction_type in ("DIRECT", "TEMPORAL"):
            return "MEDIUM"
        return "LOW"
