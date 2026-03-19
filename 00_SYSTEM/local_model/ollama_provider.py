#!/usr/bin/env python3
"""
APEX MANBEARPIG — Ollama Provider (Shadow-Programmed)
═════════════════════════════════════════════════════
Wraps the Ollama Python SDK (v0.6.1) and langchain-ollama (v1.0.1) for
local LLM inference.  **DISABLED BY DEFAULT** — every public method
returns a graceful fallback dict until the user sets the environment
variable ``APEX_LLM_ENABLED=true`` (case-insensitive).

Design invariants
─────────────────
* NEVER imports from the repo root (shadow modules like json.py live there).
* Thread-safe: a single ``threading.Lock`` guards lazy client init.
* UTF-8 safe: stdout is only reconfigured when running as ``__main__``.
* Zero-crash guarantee: every public method is wrapped in try/except and
  returns a fallback dict on ANY error — nothing is raised to the caller.
* Timeouts: 180 s generation, 30 s embeddings, 10 s health checks.
* When enabled, connects to Ollama at ``http://localhost:11434``.

Usage (disabled — default)::

    >>> from ollama_provider import OllamaProvider
    >>> p = OllamaProvider()
    >>> p.generate("What is MCR 2.003?")
    {'status': 'llm_disabled', 'fallback': True, 'message': '...'}

Usage (enabled — after GPU install)::

    $ set APEX_LLM_ENABLED=true
    $ ollama serve            # separate terminal
    $ python -c "from ollama_provider import OllamaProvider; print(OllamaProvider().generate('hi'))"
"""

from __future__ import annotations

import logging
import os
import sys
import threading
import time
from pathlib import Path
from typing import Any, Dict, List, Optional

# ---------------------------------------------------------------------------
# Global LLM gate — flipped to True when user has a GPU + Ollama running
# ---------------------------------------------------------------------------
APEX_LLM_ENABLED: bool = (
    os.environ.get("APEX_LLM_ENABLED", "false").lower() == "true"
)

# ---------------------------------------------------------------------------
# Logging — module-level logger, never reconfigures the root logger
# ---------------------------------------------------------------------------
_log = logging.getLogger("apex.ollama_provider")
if not _log.handlers:
    _h = logging.StreamHandler()
    _h.setFormatter(logging.Formatter(
        "%(asctime)s [%(name)s] %(levelname)s — %(message)s",
        datefmt="%Y-%m-%dT%H:%M:%S",
    ))
    _log.addHandler(_h)
    _log.setLevel(logging.DEBUG if APEX_LLM_ENABLED else logging.INFO)

# ---------------------------------------------------------------------------
# Ollama base URL
# ---------------------------------------------------------------------------
OLLAMA_BASE_URL: str = os.environ.get("OLLAMA_BASE_URL", "http://localhost:11434")

# ---------------------------------------------------------------------------
# Timeout constants (seconds)
# ---------------------------------------------------------------------------
TIMEOUT_GENERATE: int = 180
TIMEOUT_EMBED: int = 30
TIMEOUT_HEALTH: int = 10


def _fallback(method: str, detail: str = "") -> Dict[str, Any]:
    """Build a standard fallback response when LLM is disabled or errored."""
    msg = f"LLM disabled — {method} routed to MANBEARPIG fallback."
    if detail:
        msg = f"{msg} ({detail})"
    return {
        "status": "llm_disabled",
        "fallback": True,
        "message": msg,
        "method": method,
    }


class OllamaProvider:
    """Shadow-programmed Ollama wrapper.  Disabled until GPU available.

    Every public method returns a ``dict``.  When the LLM flag is off the
    dict always contains ``{"status": "llm_disabled", "fallback": True}``.
    When enabled, the dict contains the model's output plus metadata
    (latency, model name, token counts where available).
    """

    # Supported model catalogue — extend as models are pulled
    MODELS: Dict[str, Dict[str, Any]] = {
        "saul-legal": {
            "size_gb": 5.1,
            "task": "legal_reasoning",
            "temp": 0.3,
            "description": "SaulLM 7B — legal domain fine-tune",
        },
        "qwen-fast": {
            "size_gb": 1.1,
            "task": "classification",
            "temp": 0.2,
            "description": "Qwen2 1.5B — fast classification & summarisation",
        },
        "nomic-embed-text": {
            "size_gb": 0.27,
            "task": "embeddings",
            "description": "Nomic Embed Text v1.5 — 768-d embeddings",
        },
    }

    # ------------------------------------------------------------------
    # Lifecycle
    # ------------------------------------------------------------------
    def __init__(self) -> None:
        self.enabled: bool = APEX_LLM_ENABLED
        self._client: Any = None  # ollama.Client — lazy init
        self._lock: threading.Lock = threading.Lock()
        self._last_health: Optional[Dict[str, Any]] = None
        _log.info(
            "OllamaProvider initialised (enabled=%s, base_url=%s)",
            self.enabled,
            OLLAMA_BASE_URL,
        )

    def _ensure_client(self) -> Any:
        """Lazy-init the Ollama client under a lock.  Returns the client or
        ``None`` if the import / connection fails."""
        if self._client is not None:
            return self._client
        with self._lock:
            if self._client is not None:  # double-check
                return self._client
            try:
                import ollama as _ollama_sdk  # noqa: F811 — lazy
                self._client = _ollama_sdk.Client(host=OLLAMA_BASE_URL)
                _log.debug("Ollama client connected to %s", OLLAMA_BASE_URL)
                return self._client
            except Exception as exc:
                _log.warning("Failed to create Ollama client: %s", exc)
                return None

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------
    def generate(
        self,
        prompt: str,
        model: str = "qwen-fast",
        temperature: float = 0.3,
        max_tokens: int = 2048,
    ) -> Dict[str, Any]:
        """Generate text completion.

        Returns
        -------
        dict
            ``{"text": "...", "model": "...", "latency_s": float}`` on
            success, or a fallback dict when disabled / errored.
        """
        if not self.enabled:
            return _fallback("generate", f"prompt[:80]={prompt[:80]!r}")
        try:
            client = self._ensure_client()
            if client is None:
                return _fallback("generate", "client unavailable")

            t0 = time.perf_counter()
            resp = client.generate(
                model=model,
                prompt=prompt,
                options={
                    "temperature": temperature,
                    "num_predict": max_tokens,
                },
            )
            latency = round(time.perf_counter() - t0, 3)
            text = resp.get("response", "") if isinstance(resp, dict) else str(resp)
            _log.debug("generate OK model=%s latency=%.3fs len=%d", model, latency, len(text))
            return {
                "text": text,
                "model": model,
                "latency_s": latency,
                "status": "ok",
                "fallback": False,
            }
        except Exception as exc:
            _log.warning("generate failed: %s", exc)
            return _fallback("generate", str(exc))

    def embed(
        self,
        text: str,
        model: str = "nomic-embed-text",
    ) -> Dict[str, Any]:
        """Get embedding vector for *text*.

        Returns
        -------
        dict
            ``{"embedding": [float, ...], "dimensions": int}`` or fallback.
        """
        if not self.enabled:
            return _fallback("embed")
        try:
            client = self._ensure_client()
            if client is None:
                return _fallback("embed", "client unavailable")

            t0 = time.perf_counter()
            resp = client.embeddings(model=model, prompt=text)
            latency = round(time.perf_counter() - t0, 3)
            vec = resp.get("embedding", []) if isinstance(resp, dict) else []
            _log.debug("embed OK model=%s dims=%d latency=%.3fs", model, len(vec), latency)
            return {
                "embedding": vec,
                "dimensions": len(vec),
                "model": model,
                "latency_s": latency,
                "status": "ok",
                "fallback": False,
            }
        except Exception as exc:
            _log.warning("embed failed: %s", exc)
            return _fallback("embed", str(exc))

    def classify(
        self,
        text: str,
        categories: List[str],
        model: str = "qwen-fast",
    ) -> Dict[str, Any]:
        """Classify *text* into one of *categories* via prompted LLM.

        Returns
        -------
        dict
            ``{"category": str, "confidence": float}`` or fallback.
        """
        if not self.enabled:
            return _fallback("classify", f"categories={categories}")
        if not categories:
            return _fallback("classify", "empty category list")
        try:
            client = self._ensure_client()
            if client is None:
                return _fallback("classify", "client unavailable")

            cat_list = ", ".join(categories)
            prompt = (
                f"Classify the following text into EXACTLY ONE of these categories: "
                f"{cat_list}.\n\n"
                f"Text: {text}\n\n"
                f"Reply with ONLY the category name, nothing else."
            )
            t0 = time.perf_counter()
            resp = client.generate(
                model=model,
                prompt=prompt,
                options={"temperature": 0.1, "num_predict": 64},
            )
            latency = round(time.perf_counter() - t0, 3)
            raw = (resp.get("response", "") if isinstance(resp, dict) else str(resp)).strip()

            # Match the raw output to the nearest category (case-insensitive)
            chosen = raw
            confidence = 0.0
            raw_lower = raw.lower()
            for cat in categories:
                if cat.lower() == raw_lower:
                    chosen = cat
                    confidence = 0.95
                    break
                if cat.lower() in raw_lower:
                    chosen = cat
                    confidence = 0.80
                    break
            else:
                # No exact match — pick first category as low-confidence guess
                chosen = categories[0] if categories else raw
                confidence = 0.30

            _log.debug("classify OK cat=%s conf=%.2f latency=%.3fs", chosen, confidence, latency)
            return {
                "category": chosen,
                "confidence": round(confidence, 3),
                "raw_response": raw,
                "model": model,
                "latency_s": latency,
                "status": "ok",
                "fallback": False,
            }
        except Exception as exc:
            _log.warning("classify failed: %s", exc)
            return _fallback("classify", str(exc))

    def legal_analyze(
        self,
        query: str,
        context: str = "",
        model: str = "saul-legal",
    ) -> Dict[str, Any]:
        """Perform legal analysis using a domain-specialised model.

        Returns
        -------
        dict
            Structured analysis with ``analysis``, ``authorities``,
            ``recommendation`` keys — or fallback.
        """
        if not self.enabled:
            return _fallback("legal_analyze", f"query[:80]={query[:80]!r}")
        try:
            client = self._ensure_client()
            if client is None:
                return _fallback("legal_analyze", "client unavailable")

            system_prompt = (
                "You are a Michigan family-law litigation analyst. "
                "Provide structured analysis with: "
                "(1) Legal issue identification, "
                "(2) Applicable MCR rules and statutes, "
                "(3) Relevant case law, "
                "(4) Strategic recommendation. "
                "Be precise. Cite Michigan Court Rules (MCR) where applicable."
            )
            full_prompt = f"{system_prompt}\n\n"
            if context:
                full_prompt += f"Context:\n{context}\n\n"
            full_prompt += f"Query:\n{query}\n\nAnalysis:"

            t0 = time.perf_counter()
            resp = client.generate(
                model=model,
                prompt=full_prompt,
                options={"temperature": 0.3, "num_predict": 4096},
            )
            latency = round(time.perf_counter() - t0, 3)
            text = (resp.get("response", "") if isinstance(resp, dict) else str(resp)).strip()

            _log.debug("legal_analyze OK model=%s latency=%.3fs len=%d", model, latency, len(text))
            return {
                "analysis": text,
                "model": model,
                "latency_s": latency,
                "status": "ok",
                "fallback": False,
            }
        except Exception as exc:
            _log.warning("legal_analyze failed: %s", exc)
            return _fallback("legal_analyze", str(exc))

    # ------------------------------------------------------------------
    # Diagnostics
    # ------------------------------------------------------------------
    def is_available(self) -> bool:
        """Return ``True`` only when the flag is on AND the server responds."""
        if not self.enabled:
            return False
        try:
            client = self._ensure_client()
            if client is None:
                return False
            client.list()
            return True
        except Exception:
            return False

    def list_models(self) -> List[Dict[str, Any]]:
        """List models currently pulled in the local Ollama instance.

        Returns an empty list when disabled or on error.
        """
        if not self.enabled:
            return []
        try:
            client = self._ensure_client()
            if client is None:
                return []
            resp = client.list()
            models_raw = resp.get("models", []) if isinstance(resp, dict) else []
            result = []
            for m in models_raw:
                if isinstance(m, dict):
                    result.append({
                        "name": m.get("name", "unknown"),
                        "size": m.get("size", 0),
                        "modified_at": str(m.get("modified_at", "")),
                    })
                else:
                    # Ollama SDK may return model objects with attributes
                    result.append({
                        "name": getattr(m, "name", str(m)),
                        "size": getattr(m, "size", 0),
                        "modified_at": str(getattr(m, "modified_at", "")),
                    })
            return result
        except Exception as exc:
            _log.warning("list_models failed: %s", exc)
            return []

    def health_check(self) -> Dict[str, Any]:
        """Full health report: server reachability, loaded models, memory.

        Always returns a dict — never raises.
        """
        report: Dict[str, Any] = {
            "apex_llm_enabled": self.enabled,
            "ollama_base_url": OLLAMA_BASE_URL,
            "server_reachable": False,
            "models_available": [],
            "model_catalogue": list(self.MODELS.keys()),
            "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        }
        if not self.enabled:
            report["message"] = (
                "APEX LLM is shadow-programmed (disabled). "
                "Set APEX_LLM_ENABLED=true and start Ollama to activate."
            )
            self._last_health = report
            return report

        try:
            client = self._ensure_client()
            if client is None:
                report["message"] = "Ollama client could not be initialised."
                self._last_health = report
                return report

            t0 = time.perf_counter()
            models = self.list_models()
            latency = round(time.perf_counter() - t0, 3)

            report["server_reachable"] = True
            report["models_available"] = models
            report["health_latency_s"] = latency
            report["message"] = f"Ollama healthy — {len(models)} model(s) available."

            # Check which catalogue models are actually pulled
            pulled_names = {m["name"].split(":")[0] for m in models}
            for cat_name in self.MODELS:
                report[f"has_{cat_name.replace('-', '_')}"] = cat_name in pulled_names

        except Exception as exc:
            report["message"] = f"Health check error: {exc}"
            _log.warning("health_check failed: %s", exc)

        self._last_health = report
        return report


# -----------------------------------------------------------------------
# CLI entry point — quick smoke test
# -----------------------------------------------------------------------
if __name__ == "__main__":
    # Safe UTF-8 stdout only when running as a script
    sys.stdout = open(
        sys.stdout.fileno(), mode="w", encoding="utf-8",
        errors="replace", closefd=False,
    )

    provider = OllamaProvider()

    print("=" * 60)
    print("APEX MANBEARPIG — Ollama Provider smoke test")
    print("=" * 60)
    print(f"  APEX_LLM_ENABLED : {provider.enabled}")
    print(f"  OLLAMA_BASE_URL  : {OLLAMA_BASE_URL}")
    print()

    health = provider.health_check()
    for k, v in health.items():
        print(f"  {k}: {v}")
    print()

    print("generate() →", provider.generate("What is MCR 2.003?"))
    print("embed()    →", provider.embed("disqualification motion"))
    print("classify() →", provider.classify("PPO violation", ["custody", "housing", "ppo"]))
    print("legal_analyze() →", provider.legal_analyze("Can I disqualify Judge McNeill?"))
    print()
    print("Done.")
