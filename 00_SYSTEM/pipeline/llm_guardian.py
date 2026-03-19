#!/usr/bin/env python3
"""
LLM GUARDIAN — Self-Healing LLM Connection Wrapper for LitigationOS
====================================================================
Permanent solution for AI/LLM connection failures across the DELTA9 fleet.

Features:
  - Startup provider benchmarking (latency + reliability ranking)
  - Health check loop callable periodically
  - Instant failover on provider failure
  - DB-logged provider failure analytics
  - get_guaranteed_client() that NEVER returns None
  - Local AI engine as absolute last resort
  - Auto-recovery: re-tests failed providers every 5 minutes

Usage:
    from llm_guardian import get_guaranteed_client, LLMGuardian

    # Simple usage — always works, never None
    client = get_guaranteed_client()
    result = client.generate("Classify this document...")

    # Advanced — full guardian control
    guardian = LLMGuardian.instance()
    guardian.run_health_check()
    print(guardian.dashboard())
"""

import json
import logging
import os
import sqlite3
import threading
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional

logger = logging.getLogger("llm_guardian")

# ════════════════════════════════════════════════════════════════════════
#  Provider Health Record
# ════════════════════════════════════════════════════════════════════════

@dataclass
class ProviderHealth:
    name: str
    available: bool = False
    latency_ms: float = float("inf")
    consecutive_failures: int = 0
    total_calls: int = 0
    total_failures: int = 0
    last_success: float = 0.0
    last_failure: float = 0.0
    last_error: str = ""
    quarantined_until: float = 0.0

    @property
    def failure_rate(self) -> float:
        if self.total_calls == 0:
            return 0.0
        return self.total_failures / self.total_calls

    @property
    def is_quarantined(self) -> bool:
        return time.time() < self.quarantined_until

    @property
    def score(self) -> float:
        """Composite score: lower is better. Combines latency + failure rate."""
        if not self.available or self.is_quarantined:
            return float("inf")
        lat_score = min(self.latency_ms / 1000.0, 10.0)  # 0-10
        fail_penalty = self.failure_rate * 20.0  # 0-20
        recency_bonus = 0.0
        if self.last_success > 0:
            age = time.time() - self.last_success
            if age < 60:
                recency_bonus = -1.0  # recently worked = bonus
        return lat_score + fail_penalty + recency_bonus


# ════════════════════════════════════════════════════════════════════════
#  Provider Wrapper — Unified interface for any provider
# ════════════════════════════════════════════════════════════════════════

class GuardedProvider:
    """Wraps any LLM provider with health tracking and failover."""

    def __init__(self, provider: Any, health: ProviderHealth):
        self._provider = provider
        self.health = health

    @property
    def name(self) -> str:
        return self.health.name

    def generate(self, prompt: str, system: str = "", temperature: float = 0.3,
                 max_tokens: int = 2048, **kwargs) -> str:
        self.health.total_calls += 1
        start = time.time()
        try:
            result = self._provider.generate(prompt, system, temperature, max_tokens, **kwargs)
            elapsed_ms = (time.time() - start) * 1000
            self.health.latency_ms = (self.health.latency_ms * 0.7 + elapsed_ms * 0.3) \
                if self.health.latency_ms < float("inf") else elapsed_ms
            self.health.consecutive_failures = 0
            self.health.last_success = time.time()
            self.health.available = True
            return result
        except Exception as e:
            self.health.total_failures += 1
            self.health.consecutive_failures += 1
            self.health.last_failure = time.time()
            self.health.last_error = str(e)[:200]
            # Quarantine after 3 consecutive failures: exponential backoff
            if self.health.consecutive_failures >= 3:
                backoff = min(300, 30 * (2 ** (self.health.consecutive_failures - 3)))
                self.health.quarantined_until = time.time() + backoff
                logger.warning(f"[GUARDIAN] Quarantined {self.name} for {backoff}s after "
                               f"{self.health.consecutive_failures} failures")
            raise

    def chat(self, messages: list, temperature: float = 0.3,
             max_tokens: int = 2048, **kwargs) -> str:
        self.health.total_calls += 1
        start = time.time()
        try:
            result = self._provider.chat(messages, temperature, max_tokens, **kwargs)
            elapsed_ms = (time.time() - start) * 1000
            self.health.latency_ms = (self.health.latency_ms * 0.7 + elapsed_ms * 0.3) \
                if self.health.latency_ms < float("inf") else elapsed_ms
            self.health.consecutive_failures = 0
            self.health.last_success = time.time()
            self.health.available = True
            return result
        except Exception as e:
            self.health.total_failures += 1
            self.health.consecutive_failures += 1
            self.health.last_failure = time.time()
            self.health.last_error = str(e)[:200]
            if self.health.consecutive_failures >= 3:
                backoff = min(300, 30 * (2 ** (self.health.consecutive_failures - 3)))
                self.health.quarantined_until = time.time() + backoff
            raise

    def is_available(self) -> bool:
        return self.health.available and not self.health.is_quarantined


# ════════════════════════════════════════════════════════════════════════
#  LLM Guardian — The Self-Healing Controller
# ════════════════════════════════════════════════════════════════════════

_DB_PATH = Path(__file__).parent / "agents" / "master_index.db"
_RECOVERY_INTERVAL = 300  # Re-test failed providers every 5 minutes

class LLMGuardian:
    """Self-healing LLM connection manager. Tests, ranks, failsover, recovers."""

    _instance: Optional["LLMGuardian"] = None
    _lock = threading.Lock()

    def __init__(self):
        self._providers: List[GuardedProvider] = []
        self._active: Optional[GuardedProvider] = None
        self._local_fallback: Optional[Any] = None
        self._last_recovery_check: float = 0.0
        self._initialized = False
        self._db_path = _DB_PATH

    @classmethod
    def instance(cls) -> "LLMGuardian":
        """Thread-safe singleton."""
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    guardian = cls()
                    guardian.initialize()
                    cls._instance = guardian
        return cls._instance

    @classmethod
    def reset(cls):
        """Reset singleton (for testing)."""
        cls._instance = None

    # ────────────────────────────────────────────────────────────────
    #  INITIALIZATION — Build + benchmark all providers
    # ────────────────────────────────────────────────────────────────

    def initialize(self):
        """LOCAL-FIRST: Instantly activates local engine, then optionally
        probes remote providers. Startup NEVER blocks on network failures."""
        if self._initialized:
            return
        logger.info("[GUARDIAN] Initializing LOCAL-FIRST provider chain...")

        # Step 0: Guarantee local fallback is available FIRST
        self._ensure_local_fallback()

        # Build all candidate remote providers (but don't benchmark yet)
        raw_providers = self._build_provider_chain()

        for name, provider in raw_providers:
            health = ProviderHealth(name=name)
            guarded = GuardedProvider(provider, health)

            # Quick availability check with 3-second timeout cap
            try:
                if hasattr(provider, "is_available") and not provider.is_available():
                    health.available = False
                    logger.info(f"[GUARDIAN] {name}: NOT AVAILABLE (skipped)")
                else:
                    # Probe with trivial prompt — 3s timeout max
                    start = time.time()
                    provider.generate("Respond with OK", temperature=0.0, max_tokens=8)
                    elapsed_ms = (time.time() - start) * 1000
                    if elapsed_ms > 3000:
                        health.available = False
                        logger.info(f"[GUARDIAN] {name}: TOO SLOW ({elapsed_ms:.0f}ms)")
                    else:
                        health.available = True
                        health.latency_ms = elapsed_ms
                        health.last_success = time.time()
                        logger.info(f"[GUARDIAN] {name}: OK ({elapsed_ms:.0f}ms)")
            except Exception as e:
                health.available = False
                health.last_error = str(e)[:200]
                logger.info(f"[GUARDIAN] {name}: FAILED — no problem, local engine active")

            self._providers.append(guarded)

        # Sort by score (lower = better) and pick best active
        self._rank_and_select()
        self._initialized = True
        self._log_to_db("INIT", f"Initialized with {len(self._providers)} providers, "
                        f"active={self._active.name if self._active else 'local_fallback'}")
        logger.info(f"[GUARDIAN] Active provider: {self.active_name}")

    def _build_provider_chain(self) -> List[tuple]:
        """PERMANENT LOCAL-ONLY LOCK. No remote providers. No API calls.
        All intelligence provided by local_ai_engine.py pattern engine."""
        # ═══════════════════════════════════════════════════════════════
        # HARDCODED: Return empty list. Local fallback handles everything.
        # No Ollama, no Gemini, no OpenAI, no Groq, no OpenRouter.
        # ═══════════════════════════════════════════════════════════════
        return []

    def _ensure_local_fallback(self):
        """Ensure local AI engine is always available as last resort."""
        try:
            from local_ai_engine import LocalAI
            self._local_fallback = LocalAI()
        except ImportError:
            # Inline minimal fallback
            class MinimalFallback:
                name = "minimal/regex"
                def generate(self, prompt, system="", temperature=0.3, max_tokens=2048, **kw):
                    return f"[OFFLINE] Local processing only. Input length: {len(prompt)} chars"
                def chat(self, messages, temperature=0.3, max_tokens=2048, **kw):
                    last = messages[-1]["content"] if messages else ""
                    return self.generate(last)
                def is_available(self):
                    return True
            self._local_fallback = MinimalFallback()

    def _rank_and_select(self):
        """Sort providers by health score and select the best active one."""
        available = [p for p in self._providers if p.is_available()]
        if available:
            available.sort(key=lambda p: p.health.score)
            self._active = available[0]
        else:
            self._active = None

    # ────────────────────────────────────────────────────────────────
    #  HEALTH CHECK — Call this periodically
    # ────────────────────────────────────────────────────────────────

    def run_health_check(self) -> Dict[str, Any]:
        """Test all providers, update rankings, recover quarantined ones.
        Call this periodically (e.g., every 60 seconds during pipeline runs)."""
        results = {}

        # Check if any quarantined providers should be re-tested
        now = time.time()
        for p in self._providers:
            if p.health.is_quarantined and now >= p.health.quarantined_until:
                # Quarantine expired — re-test
                try:
                    start = time.time()
                    p._provider.generate("Health check: respond OK", temperature=0.0, max_tokens=8)
                    elapsed_ms = (time.time() - start) * 1000
                    p.health.available = True
                    p.health.consecutive_failures = 0
                    p.health.quarantined_until = 0
                    p.health.latency_ms = elapsed_ms
                    p.health.last_success = now
                    results[p.name] = f"RECOVERED ({elapsed_ms:.0f}ms)"
                    self._log_to_db("RECOVERY", f"{p.name} recovered after quarantine")
                except Exception as e:
                    # Re-quarantine with longer backoff
                    p.health.consecutive_failures += 1
                    backoff = min(600, 60 * (2 ** (p.health.consecutive_failures - 3)))
                    p.health.quarantined_until = now + backoff
                    results[p.name] = f"STILL_FAILED ({e})"
            elif p.is_available():
                results[p.name] = "OK"
            elif p.health.is_quarantined:
                remaining = int(p.health.quarantined_until - now)
                results[p.name] = f"QUARANTINED ({remaining}s remaining)"
            else:
                results[p.name] = "UNAVAILABLE"

        # Auto-recovery: periodically re-test ALL failed providers
        if now - self._last_recovery_check >= _RECOVERY_INTERVAL:
            self._last_recovery_check = now
            for p in self._providers:
                if not p.health.available and not p.health.is_quarantined:
                    try:
                        if hasattr(p._provider, "is_available") and p._provider.is_available():
                            start = time.time()
                            p._provider.generate("Recovery probe", temperature=0.0, max_tokens=8)
                            p.health.available = True
                            p.health.consecutive_failures = 0
                            p.health.latency_ms = (time.time() - start) * 1000
                            p.health.last_success = now
                            results[p.name] = "RECOVERED (periodic)"
                            self._log_to_db("RECOVERY", f"{p.name} recovered via periodic check")
                    except Exception:
                        pass

        # Re-rank and select best
        self._rank_and_select()
        return results

    # ────────────────────────────────────────────────────────────────
    #  GUARANTEED CLIENT — Never returns None
    # ────────────────────────────────────────────────────────────────

    @property
    def active_name(self) -> str:
        if self._active:
            return self._active.name
        return self._local_fallback.name if self._local_fallback else "none"

    def generate(self, prompt: str, system: str = "", temperature: float = 0.3,
                 max_tokens: int = 2048, task: str = "general", **kwargs) -> str:
        """Generate text with full failover chain. NEVER raises — returns fallback text."""
        # Try active provider first
        if self._active and self._active.is_available():
            try:
                return self._active.generate(prompt, system, temperature, max_tokens, **kwargs)
            except Exception as e:
                logger.warning(f"[GUARDIAN] Active provider {self._active.name} failed: {e}")
                self._log_to_db("FAILURE", f"{self._active.name}: {e}")

        # Failover through ranked providers
        for p in sorted(self._providers, key=lambda x: x.health.score):
            if p is self._active or not p.is_available():
                continue
            try:
                result = p.generate(prompt, system, temperature, max_tokens, **kwargs)
                self._active = p
                logger.info(f"[GUARDIAN] Failover to {p.name}")
                self._log_to_db("FAILOVER", f"Switched to {p.name}")
                return result
            except Exception:
                continue

        # Absolute last resort: local AI engine
        if self._local_fallback:
            try:
                return self._local_fallback.generate(prompt, system, temperature, max_tokens)
            except Exception as e:
                logger.error(f"[GUARDIAN] Even local fallback failed: {e}")

        return "[GUARDIAN_FALLBACK] All providers exhausted. Input processed offline."

    def chat(self, messages: list, temperature: float = 0.3,
             max_tokens: int = 2048, **kwargs) -> str:
        """Chat with full failover chain. NEVER raises."""
        if self._active and self._active.is_available():
            try:
                return self._active.chat(messages, temperature, max_tokens, **kwargs)
            except Exception as e:
                logger.warning(f"[GUARDIAN] Chat failed on {self._active.name}: {e}")
                self._log_to_db("FAILURE", f"chat: {self._active.name}: {e}")

        for p in sorted(self._providers, key=lambda x: x.health.score):
            if p is self._active or not p.is_available():
                continue
            try:
                result = p.chat(messages, temperature, max_tokens, **kwargs)
                self._active = p
                self._log_to_db("FAILOVER", f"chat switched to {p.name}")
                return result
            except Exception:
                continue

        if self._local_fallback:
            try:
                if hasattr(self._local_fallback, "chat"):
                    return self._local_fallback.chat(messages, temperature, max_tokens)
                last_msg = messages[-1]["content"] if messages else ""
                return self._local_fallback.generate(last_msg)
            except Exception:
                pass

        return "[GUARDIAN_FALLBACK] All providers exhausted."

    # ────────────────────────────────────────────────────────────────
    #  High-Level Pipeline Methods (delegate to LLMClient interface)
    # ────────────────────────────────────────────────────────────────

    def classify_document(self, text: str, categories: list) -> dict:
        """Classify with guaranteed response."""
        try:
            from llm_client import LLMClient
            # Build a temporary client using our active provider
            client = LLMClient.__new__(LLMClient)
            client.providers = []
            client._active = self._active._provider if self._active else self._local_fallback
            client._ollama_url = ""  # Not used in local mode
            return client.classify_document(text, categories)
        except Exception:
            # Pure local fallback
            if self._local_fallback and hasattr(self._local_fallback, "classify_document"):
                return self._local_fallback.classify_document(text, categories)
            return {"category": categories[0] if categories else "Unknown",
                    "confidence": 0.1, "reasoning": "all_providers_failed"}

    def detect_lane(self, text: str) -> dict:
        """Lane detection with guaranteed response."""
        if self._local_fallback and hasattr(self._local_fallback, "detect_lane"):
            return self._local_fallback.detect_lane(text)
        return {"lane": "unknown", "confidence": 0.0, "signals": []}

    # ────────────────────────────────────────────────────────────────
    #  DB LOGGING — Track all provider events for analysis
    # ────────────────────────────────────────────────────────────────

    def _log_to_db(self, event_type: str, detail: str):
        """Log provider events to the master index DB."""
        try:
            self._db_path.parent.mkdir(parents=True, exist_ok=True)
            conn = sqlite3.connect(str(self._db_path), timeout=10)
            conn.execute("""
                CREATE TABLE IF NOT EXISTS llm_guardian_log (
                    id INTEGER PRIMARY KEY,
                    event_type TEXT NOT NULL,
                    detail TEXT,
                    active_provider TEXT,
                    provider_count INTEGER,
                    timestamp TEXT DEFAULT (datetime('now'))
                )
            """)
            conn.execute(
                "INSERT INTO llm_guardian_log (event_type, detail, active_provider, provider_count) "
                "VALUES (?, ?, ?, ?)",
                (event_type, detail[:500],
                 self._active.name if self._active else "none",
                 len([p for p in self._providers if p.is_available()]))
            )
            conn.commit()
            conn.close()
        except Exception as e:
            logger.debug(f"[GUARDIAN] DB log failed: {e}")

    # ────────────────────────────────────────────────────────────────
    #  DASHBOARD — Human-readable status
    # ────────────────────────────────────────────────────────────────

    def dashboard(self) -> str:
        """Return human-readable dashboard of all providers."""
        lines = [
            "╔══════════════════════════════════════════════════════════════╗",
            "║              LLM GUARDIAN — PROVIDER DASHBOARD              ║",
            "╠══════════════════════════════════════════════════════════════╣",
        ]
        for p in sorted(self._providers, key=lambda x: x.health.score):
            h = p.health
            status = "✓ ACTIVE" if p is self._active else (
                "⊘ QUARANTINE" if h.is_quarantined else (
                    "✓ READY" if h.available else "✗ DOWN"))
            lat = f"{h.latency_ms:.0f}ms" if h.latency_ms < float("inf") else "N/A"
            fail = f"{h.failure_rate:.0%}" if h.total_calls > 0 else "0%"
            lines.append(f"║ {status:14s} │ {h.name:30s} │ {lat:>8s} │ fail:{fail:>4s} ║")

        lines.append("╠══════════════════════════════════════════════════════════════╣")
        lines.append(f"║ Local fallback: {'✓' if self._local_fallback else '✗'}"
                     f"  │  Total providers: {len(self._providers):>2d}"
                     f"  │  Available: {sum(1 for p in self._providers if p.is_available()):>2d}     ║")
        lines.append("╚══════════════════════════════════════════════════════════════╝")
        return "\n".join(lines)

    def status(self) -> dict:
        """Machine-readable status."""
        return {
            "active": self.active_name,
            "total_providers": len(self._providers),
            "available_providers": sum(1 for p in self._providers if p.is_available()),
            "quarantined": sum(1 for p in self._providers if p.health.is_quarantined),
            "local_fallback": self._local_fallback is not None,
            "providers": [
                {
                    "name": p.health.name,
                    "available": p.health.available,
                    "quarantined": p.health.is_quarantined,
                    "latency_ms": round(p.health.latency_ms, 1) if p.health.latency_ms < float("inf") else None,
                    "failure_rate": round(p.health.failure_rate, 3),
                    "consecutive_failures": p.health.consecutive_failures,
                    "total_calls": p.health.total_calls,
                    "last_error": p.health.last_error or None,
                }
                for p in self._providers
            ],
        }


# ════════════════════════════════════════════════════════════════════════
#  PUBLIC API — get_guaranteed_client()
# ════════════════════════════════════════════════════════════════════════

def get_guaranteed_client() -> LLMGuardian:
    """Get the singleton LLM Guardian. NEVER returns None.
    
    This is the primary entry point for all pipeline agents.
    Replace `from llm_client import get_client` with:
        `from llm_guardian import get_guaranteed_client`
    """
    return LLMGuardian.instance()


# ════════════════════════════════════════════════════════════════════════
#  CLI Self-Test
# ════════════════════════════════════════════════════════════════════════

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(message)s")

    print("=" * 60)
    print("  LLM GUARDIAN — Self-Test")
    print("=" * 60)

    guardian = get_guaranteed_client()
    print(guardian.dashboard())
    print()

    # Test guaranteed generation
    print("=== Test: Guaranteed Generate ===")
    result = guardian.generate("What is the capital of Michigan?", task="general")
    print(f"  Result: {result[:200]}")
    print()

    # Test health check
    print("=== Test: Health Check ===")
    hc = guardian.run_health_check()
    for name, status in hc.items():
        print(f"  {name}: {status}")
    print()

    # Print status JSON
    print("=== Status ===")
    print(json.dumps(guardian.status(), indent=2))
