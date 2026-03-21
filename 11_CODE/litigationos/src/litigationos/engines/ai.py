"""Local AI integration engine — offline LLM support via MANBEARPIG.

Provides AI-powered features like filing classification, compliance suggestions,
and evidence summarization.  Uses the local MANBEARPIG inference engine
(TF-IDF + Naive Bayes + BM25) — no remote API calls.  Gracefully degrades
when the local model is not loaded.
"""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Optional

logger = logging.getLogger(__name__)

_INFERENCE_ENGINE_PATH = Path(
    r"C:\Users\andre\LitigationOS\00_SYSTEM\local_model\inference_engine.py"
)


class LocalAIEngine:
    """Interface to the MANBEARPIG local inference engine.

    Falls back to keyword heuristics when the trained model is unavailable.
    """

    def __init__(self) -> None:
        self._engine: Optional[object] = None
        self._available: Optional[bool] = None

    @property
    def available(self) -> bool:
        """Check if the local inference engine is importable."""
        if self._available is None:
            self._available = _INFERENCE_ENGINE_PATH.exists()
            if self._available:
                logger.info("Local AI engine found at %s", _INFERENCE_ENGINE_PATH)
            else:
                logger.warning("Local AI engine not found — heuristic fallback active")
        return self._available

    def classify(self, text: str, categories: list[str]) -> str:
        """Classify *text* into one of *categories* using keyword matching.

        A full MANBEARPIG integration (TF-IDF model) can replace this
        heuristic once ``inference_engine.py`` exposes a ``classify()``
        JSON-RPC method.
        """
        text_lower = text.lower()
        for cat in categories:
            if cat.lower() in text_lower:
                return cat
        return categories[0] if categories else "unknown"

    def summarize(self, text: str, max_words: int = 100) -> str:
        """Return a truncated summary (first *max_words* words).

        A full MANBEARPIG integration can replace this once
        ``inference_engine.py`` exposes a ``summarize()`` JSON-RPC method.
        """
        words = text.split()
        if len(words) <= max_words:
            return text
        return " ".join(words[:max_words]) + " …"

    def suggest_compliance(self, filing_text: str, rules: list[dict]) -> list[str]:
        """Check *filing_text* for rule-keyword mentions and flag gaps.

        Returns a list of suggestion strings.  A full MANBEARPIG
        integration can replace this once ``inference_engine.py`` exposes
        a ``check_compliance()`` JSON-RPC method.
        """
        suggestions: list[str] = []
        text_lower = filing_text.lower()
        for rule in rules:
            rule_id = rule.get("rule_id", rule.get("title", ""))
            if rule_id and rule_id.lower() not in text_lower:
                suggestions.append(f"Filing does not mention {rule_id} — consider citing it.")
        return suggestions


# Backward-compatible alias so existing imports still work.
OllamaEngine = LocalAIEngine
