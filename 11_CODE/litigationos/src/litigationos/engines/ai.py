"""Ollama integration engine — optional local LLM support.

Provides AI-powered features like filing classification, compliance suggestions,
and evidence summarization. Gracefully degrades when Ollama is not available.
"""

from __future__ import annotations

from typing import Optional


class OllamaEngine:
    """Interface to local Ollama LLM for AI-assisted features."""

    def __init__(
        self,
        base_url: str = "http://localhost:11434",
        model: str = "llama3.2",
    ):
        self.base_url = base_url
        self.model = model
        self._available: Optional[bool] = None

    @property
    def available(self) -> bool:
        """Check if Ollama is running and accessible."""
        if self._available is None:
            try:
                import requests
                resp = requests.get(f"{self.base_url}/api/tags", timeout=2)
                self._available = resp.status_code == 200
            except Exception:
                self._available = False
        return self._available

    def classify(self, text: str, categories: list[str]) -> str:
        """Classify text into one of the given categories."""
        # TODO: Send classification prompt to Ollama
        raise NotImplementedError("AI classification not yet implemented")

    def summarize(self, text: str, max_words: int = 100) -> str:
        """Generate a brief summary of text."""
        # TODO: Send summarization prompt to Ollama
        raise NotImplementedError("AI summarization not yet implemented")

    def suggest_compliance(self, filing_text: str, rules: list[dict]) -> str:
        """Generate compliance suggestions for a filing."""
        # TODO: Analyze filing against rules using LLM
        raise NotImplementedError("AI compliance suggestions not yet implemented")
