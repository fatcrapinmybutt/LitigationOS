#!/usr/bin/env python3
"""
LLM Client - LOCAL-ONLY AI Interface for LitigationOS Pipeline
===============================================================
PERMANENT LOCAL-ONLY LOCK: No remote providers. No API calls.
No Ollama, no Gemini, no OpenAI, no Groq, no OpenRouter, no network.

All intelligence is provided by local_ai_engine.py:
  - Document classification (regex + TF-IDF pattern matching)
  - Entity extraction (dates, case numbers, statutes, judges)
  - Evidence scoring (keyword density + pattern matching)
  - Text summarization (extractive, sentence scoring)
  - Lane detection (A/B/C/D/E/F case lanes)

Usage:
    from llm_client import LLMClient
    client = LLMClient()
    result = client.generate("Classify this document: ...")
    result = client.classify_document(text, categories)
    result = client.summarize(text, max_words=200)
"""

import json, os, sys, re, logging
from pathlib import Path
from typing import Optional

logger = logging.getLogger("llm_client")

# ════════════════════════════════════════════════════════════════════════
#  LOCAL-ONLY Provider (wraps local_ai_engine.py)
# ════════════════════════════════════════════════════════════════════════

class OfflineFallback:
    """Pure local AI engine - regex/keyword/TF-IDF. No network. No API.
    Delegates to LocalAI engine for intelligent local processing."""

    def __init__(self):
        try:
            from local_ai_engine import LocalAI
            self._engine = LocalAI()
        except ImportError:
            self._engine = None

    @property
    def name(self) -> str:
        return "local/pattern-engine"

    def is_available(self) -> bool:
        return True

    def generate(self, prompt: str, system: str = "", temperature: float = 0.7,
                 max_tokens: int = 2000) -> str:
        if self._engine:
            return self._engine.generate(prompt, system, temperature, max_tokens)
        return self._regex_fallback(prompt)

    def chat(self, messages: list, temperature: float = 0.7,
             max_tokens: int = 2000) -> str:
        prompt = "\n".join(m.get("content", "") for m in messages if m.get("content"))
        return self.generate(prompt, temperature=temperature, max_tokens=max_tokens)

    def _regex_fallback(self, text: str) -> str:
        """Absolute minimum fallback if even local_ai_engine fails to import."""
        text_lower = text.lower()
        if "classif" in text_lower:
            for cat in ["Motion", "Order", "Brief", "Affidavit", "Complaint", "Petition"]:
                if cat.lower() in text_lower:
                    return json.dumps({"category": cat, "confidence": 0.6})
            return json.dumps({"category": "Document", "confidence": 0.3})
        if "summar" in text_lower:
            sentences = re.split(r'[.!?]+', text)
            return ". ".join(s.strip() for s in sentences[:3] if s.strip()) + "."
        if "extract" in text_lower or "entit" in text_lower:
            dates = re.findall(r'\b\d{4}-\d{2}-\d{2}\b', text)
            cases = re.findall(r'\b\d{4}-\d{6}-[A-Z]{2}\b', text)
            statutes = re.findall(r'MCL\s+\d+\.\d+', text)
            return json.dumps({"dates": dates[:10], "cases": cases[:10], "statutes": statutes[:10]})
        return text[:500] if len(text) > 500 else text


# ════════════════════════════════════════════════════════════════════════
#  MLLM Provider (trained Michigan Legal Language Model)
# ════════════════════════════════════════════════════════════════════════

class MLLMProvider:
    """Wraps the trained MLLM for use in the pipeline. Falls back to OfflineFallback."""

    def __init__(self):
        self._model = None
        try:
            sys.path.insert(0, str(Path(__file__).parent.parent / "local_model"))
            from inference_engine import MichiganLegalModel
            self._model = MichiganLegalModel()
            if not self._model.loaded:
                self._model = None
        except Exception:
            self._model = None

    @property
    def name(self) -> str:
        return "mllm/michigan-legal-v1.0"

    def is_available(self) -> bool:
        return self._model is not None and self._model.loaded

    def generate(self, prompt: str, system: str = "", temperature: float = 0.7,
                 max_tokens: int = 2000) -> str:
        if not self._model:
            return ""
        try:
            result = self._model.query(prompt)
            return result.get("response", "")
        except Exception:
            return ""

    def chat(self, messages: list, temperature: float = 0.7,
             max_tokens: int = 2000) -> str:
        prompt = "\n".join(m.get("content", "") for m in messages if m.get("content"))
        return self.generate(prompt, temperature=temperature, max_tokens=max_tokens)


# ════════════════════════════════════════════════════════════════════════
#  LLMClient — Unified Interface (LOCAL-ONLY)
# ════════════════════════════════════════════════════════════════════════

class LLMClient:
    """
    Unified AI client. PERMANENTLY LOCAL-ONLY.
    Priority: MLLM (trained model) → OfflineFallback (regex/TF-IDF).
    No remote providers. No API keys. No network calls. Zero errors.
    """

    def __init__(self, preferred_provider: str = "local",
                 ollama_model: str = "", ollama_url: str = ""):
        # Try MLLM first, fall back to pattern engine
        self._mllm = MLLMProvider()
        self._fallback = OfflineFallback()
        self._active = self._mllm if self._mllm.is_available() else self._fallback
        self.providers = [p for p in [self._mllm, self._fallback] if p.is_available()]
        logger.info(f"LLMClient active: {self._active.name}")

    @property
    def provider_name(self) -> str:
        return self._active.name

    @property
    def is_remote(self) -> bool:
        return False

    def generate(self, prompt: str, system: str = "", temperature: float = 0.7,
                 max_tokens: int = 2000) -> str:
        return self._active.generate(prompt, system, temperature, max_tokens)

    def chat(self, messages: list, temperature: float = 0.7,
             max_tokens: int = 2000) -> str:
        return self._active.chat(messages, temperature, max_tokens)

    def classify_document(self, text: str, categories: list = None) -> dict:
        if hasattr(self._active, '_engine') and self._active._engine:
            return self._active._engine.classify_document(text)
        result = self._active.generate(f"Classify: {text[:1000]}")
        try:
            return json.loads(result)
        except json.JSONDecodeError:
            return {"category": "Document", "confidence": 0.3}

    def summarize(self, text: str, max_words: int = 200) -> str:
        if hasattr(self._active, '_engine') and self._active._engine:
            return self._active._engine.summarize(text, max_sentences=max(3, max_words // 20))
        return self._active.generate(f"Summarize: {text[:2000]}")

    def extract_entities(self, text: str) -> dict:
        if hasattr(self._active, '_engine') and self._active._engine:
            return self._active._engine.extract_entities(text)
        result = self._active.generate(f"Extract entities: {text[:2000]}")
        try:
            return json.loads(result)
        except json.JSONDecodeError:
            return {"entities": []}

    def detect_lane(self, text: str) -> str:
        if hasattr(self._active, '_engine') and self._active._engine:
            return self._active._engine.detect_lane(text)
        return "A"

    def score_evidence(self, text: str) -> float:
        if hasattr(self._active, '_engine') and self._active._engine:
            return self._active._engine.score_evidence(text)
        return 0.5

    def get_local_engine(self):
        if hasattr(self._active, '_engine') and self._active._engine:
            return self._active._engine
        from local_ai_engine import LocalAI
        return LocalAI()

    def status(self) -> dict:
        return {
            "active_provider": self.provider_name,
            "is_remote": False,
            "providers": [{"name": "local/pattern-engine", "available": True, "type": "local"}],
            "mode": "LOCAL-ONLY-PERMANENT"
        }


# ════════════════════════════════════════════════════════════════════════
#  Module-level convenience
# ════════════════════════════════════════════════════════════════════════

def get_client(**kwargs) -> LLMClient:
    return LLMClient(**kwargs)

if __name__ == "__main__":
    client = LLMClient()
    print(f"Provider: {client.provider_name}")
    print(f"Status: {json.dumps(client.status(), indent=2)}")
    result = client.generate("Test: classify this as a motion or order")
    print(f"Result: {result}")
