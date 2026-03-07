"""
Shared Anthropic client with retry, cost tracking, and graceful degradation.

Usage::

    from claude_api.client import get_client, is_available

    if is_available():
        client = get_client()
        resp = client.messages.create(...)
"""

from __future__ import annotations

import logging
import os
import time
import threading
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

@dataclass
class ClaudeConfig:
    """Runtime configuration for Claude API calls."""
    model: str = "claude-sonnet-4-20250514"
    max_tokens: int = 4096
    temperature: float = 0.0
    max_retries: int = 3
    retry_base_delay: float = 1.0
    timeout: float = 120.0
    api_key_env: str = "ANTHROPIC_API_KEY"
    # Cost tracking (per 1M tokens, Sonnet 4 pricing)
    input_cost_per_mtok: float = 3.00
    output_cost_per_mtok: float = 15.00

_config = ClaudeConfig()
_client = None
_client_lock = threading.Lock()

# ---------------------------------------------------------------------------
# Cost tracker (thread-safe)
# ---------------------------------------------------------------------------

@dataclass
class _CostTracker:
    total_input_tokens: int = 0
    total_output_tokens: int = 0
    total_requests: int = 0
    total_errors: int = 0
    total_cost_usd: float = 0.0
    _lock: threading.Lock = field(default_factory=threading.Lock)

    def record(self, input_tokens: int, output_tokens: int) -> float:
        cost = (
            input_tokens * _config.input_cost_per_mtok / 1_000_000
            + output_tokens * _config.output_cost_per_mtok / 1_000_000
        )
        with self._lock:
            self.total_input_tokens += input_tokens
            self.total_output_tokens += output_tokens
            self.total_requests += 1
            self.total_cost_usd += cost
        return cost

    def record_error(self) -> None:
        with self._lock:
            self.total_errors += 1

    def summary(self) -> dict[str, Any]:
        with self._lock:
            return {
                "total_requests": self.total_requests,
                "total_errors": self.total_errors,
                "total_input_tokens": self.total_input_tokens,
                "total_output_tokens": self.total_output_tokens,
                "total_cost_usd": round(self.total_cost_usd, 4),
            }

cost_tracker = _CostTracker()

# ---------------------------------------------------------------------------
# API key resolution
# ---------------------------------------------------------------------------

def _resolve_api_key() -> str | None:
    """Find API key from env var, .env files, or config."""
    key = os.environ.get(_config.api_key_env)
    if key:
        return key

    # Check common .env file locations
    search_paths = [
        Path(r"C:\Users\andre\LitigationOS\.env"),
        Path(r"C:\Users\andre\LitigationOS\00_SYSTEM\.env"),
        Path.home() / ".env",
    ]
    for p in search_paths:
        if p.exists():
            try:
                for line in p.read_text(encoding="utf-8").splitlines():
                    line = line.strip()
                    if line.startswith(f"{_config.api_key_env}="):
                        val = line.split("=", 1)[1].strip().strip("'\"")
                        if val:
                            return val
            except Exception:
                continue
    return None


def is_available() -> bool:
    """Return True if an Anthropic API key is configured."""
    return _resolve_api_key() is not None


# ---------------------------------------------------------------------------
# Client singleton
# ---------------------------------------------------------------------------

def get_client():
    """
    Return a configured ``anthropic.Anthropic`` client (singleton).

    Raises ``RuntimeError`` if no API key is found.
    Raises ``ImportError`` if the ``anthropic`` package is not installed.
    """
    global _client
    if _client is not None:
        return _client

    with _client_lock:
        if _client is not None:
            return _client

        api_key = _resolve_api_key()
        if not api_key:
            raise RuntimeError(
                f"No Anthropic API key found. Set {_config.api_key_env} env var "
                f"or add it to .env in the LitigationOS root."
            )

        try:
            import anthropic
        except ImportError:
            raise ImportError(
                "The 'anthropic' package is required. Install with: "
                "pip install anthropic"
            )

        _client = anthropic.Anthropic(
            api_key=api_key,
            max_retries=0,  # We handle retries ourselves for cost tracking
            timeout=_config.timeout,
        )
        logger.info("Anthropic client initialized (model=%s)", _config.model)
        return _client


def configure(**kwargs) -> None:
    """Update runtime configuration. Call before first ``get_client()``."""
    for k, v in kwargs.items():
        if hasattr(_config, k):
            setattr(_config, k, v)
        else:
            raise ValueError(f"Unknown config key: {k}")


def get_config() -> ClaudeConfig:
    """Return current configuration (read-only copy)."""
    return ClaudeConfig(**_config.__dict__)


# ---------------------------------------------------------------------------
# Retry-wrapped message creation
# ---------------------------------------------------------------------------

def create_message(
    *,
    system: str | None = None,
    messages: list[dict],
    model: str | None = None,
    max_tokens: int | None = None,
    temperature: float | None = None,
    tools: list[dict] | None = None,
    tool_choice: dict | None = None,
) -> dict[str, Any]:
    """
    Send a message to Claude with automatic retry and cost tracking.

    Returns a dict with keys: ``content``, ``usage``, ``cost_usd``, ``model``,
    ``stop_reason``.

    Raises after ``max_retries`` exhausted.
    """
    client = get_client()
    model = model or _config.model
    max_tokens = max_tokens or _config.max_tokens
    temperature = temperature if temperature is not None else _config.temperature

    kwargs: dict[str, Any] = {
        "model": model,
        "max_tokens": max_tokens,
        "temperature": temperature,
        "messages": messages,
    }
    if system:
        kwargs["system"] = system
    if tools:
        kwargs["tools"] = tools
    if tool_choice:
        kwargs["tool_choice"] = tool_choice

    last_exc = None
    for attempt in range(_config.max_retries):
        try:
            response = client.messages.create(**kwargs)

            # Track cost
            usage = response.usage
            cost = cost_tracker.record(usage.input_tokens, usage.output_tokens)

            # Extract text content
            text_parts = []
            tool_uses = []
            for block in response.content:
                if block.type == "text":
                    text_parts.append(block.text)
                elif block.type == "tool_use":
                    tool_uses.append({
                        "id": block.id,
                        "name": block.name,
                        "input": block.input,
                    })

            return {
                "content": "\n".join(text_parts),
                "tool_uses": tool_uses,
                "usage": {
                    "input_tokens": usage.input_tokens,
                    "output_tokens": usage.output_tokens,
                },
                "cost_usd": round(cost, 6),
                "model": response.model,
                "stop_reason": response.stop_reason,
            }

        except Exception as exc:
            last_exc = exc
            cost_tracker.record_error()
            exc_name = type(exc).__name__

            # Don't retry on auth errors or invalid requests
            if "authentication" in str(exc).lower() or "invalid" in exc_name.lower():
                raise

            if attempt < _config.max_retries - 1:
                delay = _config.retry_base_delay * (2 ** attempt)
                logger.warning(
                    "Claude API attempt %d/%d failed (%s: %s), retrying in %.1fs",
                    attempt + 1, _config.max_retries, exc_name, exc, delay,
                )
                time.sleep(delay)
            else:
                logger.error(
                    "Claude API failed after %d attempts: %s",
                    _config.max_retries, exc,
                )

    raise last_exc  # type: ignore[misc]


# ---------------------------------------------------------------------------
# Convenience: structured JSON output
# ---------------------------------------------------------------------------

def create_json_message(
    *,
    system: str | None = None,
    messages: list[dict],
    model: str | None = None,
    max_tokens: int | None = None,
) -> dict[str, Any]:
    """
    Like ``create_message`` but instructs Claude to return valid JSON.

    Returns the parsed JSON as a Python dict/list under the ``parsed`` key,
    plus all standard response fields.
    """
    import json

    json_system = (system or "") + (
        "\n\nIMPORTANT: Respond with ONLY valid JSON. No markdown, no explanation, "
        "no code fences. Just the JSON object."
    )

    result = create_message(
        system=json_system.strip(),
        messages=messages,
        model=model,
        max_tokens=max_tokens,
        temperature=0.0,
    )

    text = result["content"].strip()
    # Strip markdown code fences if Claude adds them despite instructions
    if text.startswith("```"):
        lines = text.splitlines()
        lines = [l for l in lines if not l.strip().startswith("```")]
        text = "\n".join(lines).strip()

    try:
        result["parsed"] = json.loads(text)
    except json.JSONDecodeError:
        result["parsed"] = None
        result["parse_error"] = f"Failed to parse JSON from response: {text[:200]}"
        logger.warning("JSON parse failed: %s", text[:200])

    return result
