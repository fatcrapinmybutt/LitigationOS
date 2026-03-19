# -*- coding: utf-8 -*-
"""
LitigationOS Context Orchestrator — Δ99 Ω∞
============================================
Unified context engineering hub that extends the base ContextManager
with token-aware budgeting, validation, compression, auto-snapshots,
and quality metrics.

Closes P0/P1 gaps identified in context management audit:
  P0: Token-aware context window (prevents LLM overflow)
  P0: Auto context snapshots (session recovery)
  P1: Context validator + quality gate (prevents errors)
  P1: Context compression/summarization (manage memory growth)
  P1: Context quality scorer (transparency + freshness warnings)

Architecture:
    TokenBudget          — Token allocation and tracking per model tier
    ContextValidator     — Entity, lane, fabrication, contradiction checks
    ContextCompressor    — TF-IDF extractive summarization (stdlib only)
    AutoSnapshotManager  — Periodic state capture with SHA-256 integrity
    ContextQualityScorer — Freshness, relevance, coverage, purity metrics
    ContextOrchestrator  — Central hub wrapping all subsystems

Integration Points:
    - ContextManager (context_manager.py)     — base window + memory + handoffs
    - QualityGate (quality_gate.py)           — filing validation checks
    - ProvenanceTracker (provenance_tracker.py) — evidence chain integrity
    - FreshnessScorer (context_manager.py)    — staleness detection

Zero network. Zero APIs. 100% local.
"""

from __future__ import annotations

import collections
import copy
import hashlib
import json
import logging
import math
import os
import re
import sqlite3
import sys
import threading
import time
from dataclasses import dataclass, field, asdict
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple, Union

# ─── UTF-8 Safety ─────────────────────────────────────────────────────
if hasattr(sys.stdout, "fileno"):
    try:
        sys.stdout = open(
            sys.stdout.fileno(), mode="w", encoding="utf-8", errors="replace"
        )
    except Exception:
        pass

logger = logging.getLogger("legal_ai.context_orchestrator")

# ─── Pydantic v2 with Dataclass Fallback ──────────────────────────────
_PYDANTIC = False
try:
    from pydantic import BaseModel, Field, field_validator, model_validator

    _PYDANTIC = True
except ImportError:
    pass

# ─── Path Resolution ──────────────────────────────────────────────────
_HERE = Path(__file__).resolve().parent
_REPO = _HERE.parents[1]  # 00_SYSTEM -> LitigationOS
_DB_PATH = Path(
    os.environ.get("LITIGOS_DB", str(_REPO / "litigation_context.db"))
)
_SNAPSHOT_DIR = _REPO / "00_SYSTEM" / "snapshots" / "context"

# ─── Constants ────────────────────────────────────────────────────────
VALID_LANES: Set[str] = {"A", "B", "C", "D", "E", "F"}

LANE_LABELS: Dict[str, str] = {
    "A": "Watson custody (2024-001507-DC)",
    "B": "Shady Oaks housing (2025-002760-CZ)",
    "C": "Convergence (cross-lane)",
    "D": "PPO / Protection Orders (2023-5907-PP)",
    "E": "Judicial Misconduct / JTC",
    "F": "Appellate (COA 366810)",
}

# Token estimation: ~1.3 tokens per word for English legal text
TOKENS_PER_WORD: float = 1.3

# Model tier default budgets
MODEL_TOKEN_LIMITS: Dict[str, int] = {
    "small": 4096,
    "medium": 8192,
    "large": 16384,
    "xl": 32768,
    "xxl": 65536,
    "128k": 128000,
}

# Snapshot defaults
SNAPSHOT_INTERVAL_S: int = 300  # 5 minutes
MAX_SNAPSHOTS: int = 50

# Quality scoring weights
QUALITY_WEIGHTS: Dict[str, float] = {
    "freshness": 0.25,
    "relevance": 0.30,
    "coverage": 0.20,
    "lane_purity": 0.15,
    "contradiction_penalty": 0.10,
}

# Required context domains for coverage scoring
REQUIRED_DOMAINS: List[str] = [
    "parties",
    "case_numbers",
    "judge",
    "current_filing",
    "deadlines",
    "evidence",
    "authorities",
]

# Freshness thresholds (aligned with context_manager.py)
FRESHNESS_DECAY_HALF_LIFE_S: float = 86400.0 * 7  # 7-day half-life
STALE_THRESHOLD: float = 0.3
EXPIRED_THRESHOLD: float = 0.1

# ─── Entity Guards (authoritative reference) ─────────────────────────
CORRECT_ENTITIES: Dict[str, Dict[str, Any]] = {
    "plaintiff": {
        "name": "Andrew James Pigors",
        "patterns": [r"\bAndrew\s+(?:James\s+)?Pigors\b"],
    },
    "defendant": {
        "name": "Emily A. Watson",
        "correct_patterns": [r"\bEmily\s+A\.?\s+Watson\b"],
        "wrong_variants": [
            "Emily Ann Watson",
            "Emily M. Watson",
            "Emily M Watson",
            "Tiffany Watson",
        ],
    },
    "child": {
        "name": "Lincoln David Watson",
        "initials": "L.D.W.",
        "rule": "MCR 8.119(H) — use initials only in filings",
    },
    "judge": {
        "name": "Hon. Jenny L. McNeill",
        "correct_patterns": [r"\bJenny\s+L\.?\s+McNeill\b"],
        "wrong_variants": [
            "Amy McNeill",
            "Jenny McNeil",   # single L
            "Jenny McNiel",
            "Jenny McNeill",  # missing Hon. is a soft warning, not error
        ],
    },
    "ron_berry": {
        "name": "Ronald Berry",
        "role": "Emily's boyfriend — NOT an attorney",
        "forbidden_titles": ["Esq.", "Attorney", "Counsel"],
    },
    "emily_attorney": {
        "name": "Jennifer Barnes (P55406)",
        "status": "WITHDREW",
        "wrong_variants": [
            "Jane Berry",
            "Patricia Berry (P35878)",
        ],
    },
}

FABRICATED_ITEMS: List[str] = [
    "9 CPS investigations",
    "Jane Berry",
    "Patricia Berry (P35878)",
    "91% alienation score",
]

# ─── SQLite PRAGMAs ──────────────────────────────────────────────────
_WAL_PRAGMAS = """
PRAGMA journal_mode = WAL;
PRAGMA busy_timeout = 60000;
PRAGMA cache_size = -32000;
PRAGMA temp_store = MEMORY;
PRAGMA synchronous = NORMAL;
"""


# ─── Helper: Safe DB Connection ──────────────────────────────────────
def _safe_connect(db_path: Union[str, Path] = _DB_PATH) -> Optional[sqlite3.Connection]:
    """Open a SQLite connection with WAL + safety PRAGMAs. Returns None on failure."""
    try:
        conn = sqlite3.connect(str(db_path), timeout=30)
        conn.row_factory = sqlite3.Row
        for pragma in _WAL_PRAGMAS.strip().splitlines():
            pragma = pragma.strip()
            if pragma:
                conn.execute(pragma)
        return conn
    except Exception as exc:
        logger.error("DB connect failed (%s): %s", db_path, exc)
        return None


# ═════════════════════════════════════════════════════════════════════
#  Pydantic v2 Models (with dataclass fallback)
# ═════════════════════════════════════════════════════════════════════

if _PYDANTIC:

    class TokenBudgetConfig(BaseModel):
        """Configuration for token budget allocation."""

        max_tokens: int = Field(default=8192, ge=512, le=128000)
        prompt_reserve: float = Field(default=0.30, ge=0.05, le=0.50)
        response_reserve: float = Field(default=0.30, ge=0.05, le=0.50)
        context_allocation: float = Field(default=0.40, ge=0.10, le=0.80)
        model_tier: str = Field(default="medium")

        @model_validator(mode="after")
        def _check_total(self) -> "TokenBudgetConfig":
            total = self.prompt_reserve + self.response_reserve + self.context_allocation
            if not (0.95 <= total <= 1.05):
                raise ValueError(
                    f"Budget fractions must sum to ~1.0, got {total:.2f}"
                )
            return self

    class SnapshotMeta(BaseModel):
        """Metadata for a context snapshot."""

        snapshot_id: str = Field(default="")
        created_at: float = Field(default_factory=time.time)
        item_count: int = Field(default=0, ge=0)
        sha256: str = Field(default="")
        lane: Optional[str] = Field(default=None)
        description: str = Field(default="")
        size_bytes: int = Field(default=0, ge=0)

    class QualityReport(BaseModel):
        """Context quality assessment report."""

        overall_score: float = Field(default=0.0, ge=0.0, le=1.0)
        freshness_score: float = Field(default=0.0, ge=0.0, le=1.0)
        relevance_score: float = Field(default=0.0, ge=0.0, le=1.0)
        coverage_score: float = Field(default=0.0, ge=0.0, le=1.0)
        lane_purity_score: float = Field(default=0.0, ge=0.0, le=1.0)
        contradiction_penalty: float = Field(default=0.0, ge=0.0, le=1.0)
        missing_domains: List[str] = Field(default_factory=list)
        warnings: List[str] = Field(default_factory=list)
        item_count: int = Field(default=0, ge=0)
        stale_count: int = Field(default=0, ge=0)
        expired_count: int = Field(default=0, ge=0)

    class ValidationResult(BaseModel):
        """Result from context validation."""

        valid: bool = Field(default=True)
        errors: List[str] = Field(default_factory=list)
        warnings: List[str] = Field(default_factory=list)
        entity_issues: List[str] = Field(default_factory=list)
        lane_violations: List[str] = Field(default_factory=list)
        fabrication_hits: List[str] = Field(default_factory=list)
        contradiction_pairs: List[Tuple[str, str]] = Field(default_factory=list)

    class CompressionResult(BaseModel):
        """Result from context compression."""

        original_tokens: int = Field(default=0, ge=0)
        compressed_tokens: int = Field(default=0, ge=0)
        compression_ratio: float = Field(default=1.0, ge=0.0)
        sentences_kept: int = Field(default=0, ge=0)
        sentences_dropped: int = Field(default=0, ge=0)
        summary_text: str = Field(default="")

else:
    # ── Dataclass Fallback ────────────────────────────────────────────

    @dataclass
    class TokenBudgetConfig:  # type: ignore[no-redef]
        """Configuration for token budget allocation."""

        max_tokens: int = 8192
        prompt_reserve: float = 0.30
        response_reserve: float = 0.30
        context_allocation: float = 0.40
        model_tier: str = "medium"

        def __post_init__(self) -> None:
            if not (512 <= self.max_tokens <= 128000):
                raise ValueError(f"max_tokens must be 512..128000, got {self.max_tokens}")
            total = self.prompt_reserve + self.response_reserve + self.context_allocation
            if not (0.95 <= total <= 1.05):
                raise ValueError(f"Budget fractions must sum to ~1.0, got {total:.2f}")

    @dataclass
    class SnapshotMeta:  # type: ignore[no-redef]
        """Metadata for a context snapshot."""

        snapshot_id: str = ""
        created_at: float = field(default_factory=time.time)
        item_count: int = 0
        sha256: str = ""
        lane: Optional[str] = None
        description: str = ""
        size_bytes: int = 0

    @dataclass
    class QualityReport:  # type: ignore[no-redef]
        """Context quality assessment report."""

        overall_score: float = 0.0
        freshness_score: float = 0.0
        relevance_score: float = 0.0
        coverage_score: float = 0.0
        lane_purity_score: float = 0.0
        contradiction_penalty: float = 0.0
        missing_domains: List[str] = field(default_factory=list)
        warnings: List[str] = field(default_factory=list)
        item_count: int = 0
        stale_count: int = 0
        expired_count: int = 0

    @dataclass
    class ValidationResult:  # type: ignore[no-redef]
        """Result from context validation."""

        valid: bool = True
        errors: List[str] = field(default_factory=list)
        warnings: List[str] = field(default_factory=list)
        entity_issues: List[str] = field(default_factory=list)
        lane_violations: List[str] = field(default_factory=list)
        fabrication_hits: List[str] = field(default_factory=list)
        contradiction_pairs: List[Tuple[str, str]] = field(default_factory=list)

    @dataclass
    class CompressionResult:  # type: ignore[no-redef]
        """Result from context compression."""

        original_tokens: int = 0
        compressed_tokens: int = 0
        compression_ratio: float = 1.0
        sentences_kept: int = 0
        sentences_dropped: int = 0
        summary_text: str = ""


# ═════════════════════════════════════════════════════════════════════
#  1. Token-Aware Context Budget (P0)
# ═════════════════════════════════════════════════════════════════════

class TokenBudget:
    """Manages token budget for context assembly.

    Uses a word-based heuristic (~1.3 tokens per English word) to estimate
    token counts without requiring a tokenizer library.  Tracks usage across
    three budget sections: prompt, response, and context.
    """

    def __init__(self, config: Optional[TokenBudgetConfig] = None) -> None:
        self._config = config or TokenBudgetConfig()
        self._lock = threading.Lock()

        max_t = self._config.max_tokens
        if self._config.model_tier in MODEL_TOKEN_LIMITS:
            max_t = MODEL_TOKEN_LIMITS[self._config.model_tier]
        self._max_tokens = max_t

        self._prompt_budget = int(max_t * self._config.prompt_reserve)
        self._response_budget = int(max_t * self._config.response_reserve)
        self._context_budget = int(max_t * self._config.context_allocation)

        self._prompt_used: int = 0
        self._response_used: int = 0
        self._context_used: int = 0

    # ── Token Estimation ──

    @staticmethod
    def estimate_tokens(text: str) -> int:
        """Estimate token count from text using word-based heuristic.

        Legal English averages ~1.3 tokens per whitespace-delimited word
        due to legal terminology, citations, and punctuation.
        """
        if not text:
            return 0
        words = text.split()
        return max(1, int(len(words) * TOKENS_PER_WORD))

    @staticmethod
    def estimate_tokens_for_items(items: List[Dict[str, Any]]) -> int:
        """Estimate total tokens across a list of context item dicts."""
        total = 0
        for item in items:
            val = item.get("value", "")
            if isinstance(val, str):
                total += TokenBudget.estimate_tokens(val)
            else:
                total += TokenBudget.estimate_tokens(str(val))
            key = item.get("key", "")
            total += TokenBudget.estimate_tokens(str(key))
        return total

    # ── Budget Tracking ──

    @property
    def context_budget(self) -> int:
        """Total tokens allocated for context."""
        return self._context_budget

    @property
    def context_remaining(self) -> int:
        """Tokens remaining in the context budget."""
        return max(0, self._context_budget - self._context_used)

    @property
    def total_remaining(self) -> int:
        """Tokens remaining across all budgets."""
        used = self._prompt_used + self._response_used + self._context_used
        return max(0, self._max_tokens - used)

    def allocate_prompt(self, text: str) -> bool:
        """Charge tokens to the prompt budget. Returns False if over-budget."""
        tokens = self.estimate_tokens(text)
        with self._lock:
            if self._prompt_used + tokens > self._prompt_budget:
                return False
            self._prompt_used += tokens
            return True

    def allocate_context(self, text: str) -> bool:
        """Charge tokens to the context budget. Returns False if over-budget."""
        tokens = self.estimate_tokens(text)
        with self._lock:
            if self._context_used + tokens > self._context_budget:
                return False
            self._context_used += tokens
            return True

    def allocate_response(self, tokens: int) -> bool:
        """Reserve tokens for the expected response."""
        with self._lock:
            if self._response_used + tokens > self._response_budget:
                return False
            self._response_used += tokens
            return True

    def try_fit(self, text: str, section: str = "context") -> bool:
        """Check if text fits in the given section without allocating."""
        tokens = self.estimate_tokens(text)
        if section == "prompt":
            return (self._prompt_used + tokens) <= self._prompt_budget
        elif section == "response":
            return (self._response_used + tokens) <= self._response_budget
        else:
            return (self._context_used + tokens) <= self._context_budget

    def release_context(self, text: str) -> None:
        """Release previously allocated context tokens (e.g., after eviction)."""
        tokens = self.estimate_tokens(text)
        with self._lock:
            self._context_used = max(0, self._context_used - tokens)

    def reset(self) -> None:
        """Reset all budget counters."""
        with self._lock:
            self._prompt_used = 0
            self._response_used = 0
            self._context_used = 0

    def resize(self, model_tier: str) -> None:
        """Resize budget for a different model tier, preserving usage ratios."""
        new_max = MODEL_TOKEN_LIMITS.get(model_tier, self._max_tokens)
        with self._lock:
            ratio = new_max / max(self._max_tokens, 1)
            self._max_tokens = new_max
            self._prompt_budget = int(new_max * self._config.prompt_reserve)
            self._response_budget = int(new_max * self._config.response_reserve)
            self._context_budget = int(new_max * self._config.context_allocation)
            self._prompt_used = int(self._prompt_used * ratio)
            self._response_used = int(self._response_used * ratio)
            self._context_used = int(self._context_used * ratio)

    def utilization(self) -> Dict[str, Any]:
        """Current budget utilization report."""
        return {
            "max_tokens": self._max_tokens,
            "model_tier": self._config.model_tier,
            "prompt": {
                "budget": self._prompt_budget,
                "used": self._prompt_used,
                "remaining": self._prompt_budget - self._prompt_used,
                "pct": round(self._prompt_used / max(self._prompt_budget, 1) * 100, 1),
            },
            "response": {
                "budget": self._response_budget,
                "used": self._response_used,
                "remaining": self._response_budget - self._response_used,
                "pct": round(
                    self._response_used / max(self._response_budget, 1) * 100, 1
                ),
            },
            "context": {
                "budget": self._context_budget,
                "used": self._context_used,
                "remaining": self._context_budget - self._context_used,
                "pct": round(
                    self._context_used / max(self._context_budget, 1) * 100, 1
                ),
            },
            "total_used": self._prompt_used + self._response_used + self._context_used,
            "total_remaining": self.total_remaining,
        }


# ═════════════════════════════════════════════════════════════════════
#  2. Context Validator (P1)
# ═════════════════════════════════════════════════════════════════════

class ContextValidator:
    """Validates context items before insertion.

    Checks:
      - Entity references (party names, judge spelling)
      - Lane boundary enforcement (IRON LAW)
      - Fabrication guards (known false claims, hallucinated citations)
      - Contradiction detection with existing context items
    """

    def __init__(self) -> None:
        self._wrong_name_patterns: List[Tuple[re.Pattern, str, str]] = []
        self._fabrication_patterns: List[Tuple[re.Pattern, str]] = []
        self._forbidden_title_patterns: List[Tuple[re.Pattern, str]] = []
        self._compile_patterns()

    def _compile_patterns(self) -> None:
        """Pre-compile regex patterns for entity and fabrication checks."""
        for entity_key, info in CORRECT_ENTITIES.items():
            for wrong in info.get("wrong_variants", []):
                try:
                    pat = re.compile(re.escape(wrong), re.IGNORECASE)
                    correct = info.get("name", entity_key)
                    self._wrong_name_patterns.append((pat, wrong, correct))
                except re.error:
                    pass

            for title in info.get("forbidden_titles", []):
                name = info.get("name", "")
                first_name = name.split()[0] if name else entity_key
                try:
                    pat = re.compile(
                        rf"\b{re.escape(first_name)}\b.*?\b{re.escape(title)}\b",
                        re.IGNORECASE,
                    )
                    self._forbidden_title_patterns.append(
                        (pat, f"{name} must NOT have title '{title}'")
                    )
                except re.error:
                    pass

        for fab in FABRICATED_ITEMS:
            try:
                search_term = fab.split(" (")[0]
                pat = re.compile(re.escape(search_term), re.IGNORECASE)
                self._fabrication_patterns.append((pat, fab))
            except re.error:
                pass

    def validate_text(self, text: str) -> ValidationResult:
        """Validate a text string against all guards."""
        result = ValidationResult()

        if not text or not isinstance(text, str):
            return result

        for pat, wrong, correct in self._wrong_name_patterns:
            if pat.search(text):
                msg = f"WRONG NAME: '{wrong}' found — correct: '{correct}'"
                result.entity_issues.append(msg)
                result.errors.append(msg)
                result.valid = False

        for pat, fab in self._fabrication_patterns:
            if pat.search(text):
                msg = f"FABRICATED: '{fab}' — PURGE IMMEDIATELY"
                result.fabrication_hits.append(msg)
                result.errors.append(msg)
                result.valid = False

        for pat, msg in self._forbidden_title_patterns:
            if pat.search(text):
                result.entity_issues.append(msg)
                result.warnings.append(msg)

        return result

    def validate_lane(
        self, item_lane: Optional[str], target_lane: Optional[str]
    ) -> ValidationResult:
        """Validate lane boundary compliance.

        IRON LAW: items from one lane must not leak into another.
        Lane C (convergence) is allowed to consume items from any lane.
        """
        result = ValidationResult()

        if item_lane is not None and item_lane not in VALID_LANES:
            result.errors.append(f"Invalid lane '{item_lane}'; valid: {VALID_LANES}")
            result.valid = False
            return result

        if target_lane is not None and target_lane not in VALID_LANES:
            result.errors.append(f"Invalid target lane '{target_lane}'; valid: {VALID_LANES}")
            result.valid = False
            return result

        if item_lane and target_lane:
            if target_lane == "C":
                pass  # convergence lane may consume any lane
            elif item_lane != target_lane and item_lane != "C":
                msg = (
                    f"LANE VIOLATION: item from lane {item_lane} "
                    f"({LANE_LABELS.get(item_lane, '?')}) "
                    f"entering lane {target_lane} "
                    f"({LANE_LABELS.get(target_lane, '?')})"
                )
                result.lane_violations.append(msg)
                result.errors.append(msg)
                result.valid = False

        return result

    def detect_contradictions(
        self, new_text: str, existing_items: List[Dict[str, Any]]
    ) -> List[Tuple[str, str]]:
        """Detect potential contradictions between new text and existing items.

        Uses keyword overlap + negation detection to flag contradictory statements.
        Returns list of (new_fragment, existing_fragment) pairs.
        """
        pairs: List[Tuple[str, str]] = []
        if not new_text or not existing_items:
            return pairs

        negation_words = {
            "not", "no", "never", "denied", "false", "incorrect",
            "without", "lacks", "failed", "refused", "absent",
            "contrary", "opposite", "untrue", "disproven",
        }

        new_lower = new_text.lower()
        new_words = set(re.findall(r"\b\w{3,}\b", new_lower))
        new_has_negation = bool(new_words & negation_words)

        for item in existing_items:
            existing_text = str(item.get("value", ""))
            if not existing_text:
                continue
            existing_lower = existing_text.lower()
            existing_words = set(re.findall(r"\b\w{3,}\b", existing_lower))
            existing_has_negation = bool(existing_words & negation_words)

            shared = new_words & existing_words - {
                "the", "and", "for", "that", "this", "with", "was", "has",
                "court", "filed", "motion", "order", "case", "party",
            }

            if len(shared) < 3:
                continue

            if new_has_negation != existing_has_negation:
                new_snippet = new_text[:120].strip()
                existing_snippet = existing_text[:120].strip()
                pairs.append((new_snippet, existing_snippet))

        return pairs

    def validate_item(
        self,
        key: str,
        value: Any,
        lane: Optional[str] = None,
        target_lane: Optional[str] = None,
        existing_items: Optional[List[Dict[str, Any]]] = None,
    ) -> ValidationResult:
        """Full validation of a single context item."""
        result = ValidationResult()
        text = str(value) if value is not None else ""

        text_result = self.validate_text(text)
        result.errors.extend(text_result.errors)
        result.warnings.extend(text_result.warnings)
        result.entity_issues.extend(text_result.entity_issues)
        result.fabrication_hits.extend(text_result.fabrication_hits)

        key_result = self.validate_text(key)
        result.errors.extend(key_result.errors)
        result.entity_issues.extend(key_result.entity_issues)
        result.fabrication_hits.extend(key_result.fabrication_hits)

        lane_result = self.validate_lane(lane, target_lane)
        result.errors.extend(lane_result.errors)
        result.lane_violations.extend(lane_result.lane_violations)

        if existing_items:
            contradictions = self.detect_contradictions(text, existing_items)
            result.contradiction_pairs.extend(contradictions)
            for new_frag, old_frag in contradictions:
                result.warnings.append(
                    f"CONTRADICTION: new='{new_frag[:60]}...' vs existing='{old_frag[:60]}...'"
                )

        if result.errors:
            result.valid = False

        return result


# ═════════════════════════════════════════════════════════════════════
#  3. Context Compressor (P1)
# ═════════════════════════════════════════════════════════════════════

class ContextCompressor:
    """Compresses context via extractive summarization.

    Uses TF-IDF sentence scoring (stdlib only) to select the most
    informative sentences while discarding verbosity.  Supports
    multi-level abstraction: detail → summary → concept.
    """

    _SENTENCE_SPLIT = re.compile(r"(?<=[.!?])\s+(?=[A-Z])")
    _WORD_SPLIT = re.compile(r"\b\w+\b")

    def __init__(self, min_sentence_words: int = 4) -> None:
        self._min_sentence_words = min_sentence_words

    def _tokenize_sentences(self, text: str) -> List[str]:
        """Split text into sentences, filtering trivially short ones."""
        if not text:
            return []
        raw = self._SENTENCE_SPLIT.split(text.strip())
        sentences = []
        for s in raw:
            s = s.strip()
            words = self._WORD_SPLIT.findall(s)
            if len(words) >= self._min_sentence_words:
                sentences.append(s)
        return sentences

    def _compute_tf(self, sentence: str) -> Dict[str, float]:
        """Term frequency for a single sentence."""
        words = [w.lower() for w in self._WORD_SPLIT.findall(sentence)]
        if not words:
            return {}
        counts: Dict[str, int] = collections.Counter(words)
        total = len(words)
        return {w: c / total for w, c in counts.items()}

    def _compute_idf(self, sentences: List[str]) -> Dict[str, float]:
        """Inverse document frequency across sentences."""
        n = len(sentences)
        if n == 0:
            return {}
        doc_freq: Dict[str, int] = collections.Counter()
        for s in sentences:
            unique_words = set(w.lower() for w in self._WORD_SPLIT.findall(s))
            for w in unique_words:
                doc_freq[w] += 1
        return {w: math.log((n + 1) / (df + 1)) + 1.0 for w, df in doc_freq.items()}

    def _score_sentences(self, sentences: List[str]) -> List[Tuple[float, int, str]]:
        """Score sentences by TF-IDF importance. Returns (score, index, sentence)."""
        if not sentences:
            return []

        idf = self._compute_idf(sentences)
        scored: List[Tuple[float, int, str]] = []

        for idx, sent in enumerate(sentences):
            tf = self._compute_tf(sent)
            tfidf_score = sum(tf.get(w, 0) * idf.get(w, 0) for w in tf)

            position_bonus = 0.0
            if idx == 0:
                position_bonus = 0.3
            elif idx == len(sentences) - 1:
                position_bonus = 0.15
            elif idx <= 2:
                position_bonus = 0.1

            legal_bonus = 0.0
            lower = sent.lower()
            legal_terms = [
                "court", "order", "motion", "statute", "mcr", "mcl",
                "evidence", "filed", "granted", "denied", "hearing",
                "custody", "plaintiff", "defendant", "judge",
            ]
            for term in legal_terms:
                if term in lower:
                    legal_bonus += 0.05
            legal_bonus = min(legal_bonus, 0.3)

            total = tfidf_score + position_bonus + legal_bonus
            scored.append((total, idx, sent))

        scored.sort(key=lambda x: x[0], reverse=True)
        return scored

    def compress(
        self,
        text: str,
        target_tokens: Optional[int] = None,
        ratio: float = 0.5,
    ) -> CompressionResult:
        """Compress text via extractive summarization.

        Args:
            text: Source text to compress.
            target_tokens: Desired output token count. If None, uses ratio.
            ratio: Fraction of sentences to keep (0.0–1.0). Default 0.5.

        Returns:
            CompressionResult with summary text and metrics.
        """
        original_tokens = TokenBudget.estimate_tokens(text)
        sentences = self._tokenize_sentences(text)

        if len(sentences) <= 2:
            return CompressionResult(
                original_tokens=original_tokens,
                compressed_tokens=original_tokens,
                compression_ratio=1.0,
                sentences_kept=len(sentences),
                sentences_dropped=0,
                summary_text=text.strip(),
            )

        scored = self._score_sentences(sentences)

        if target_tokens is not None:
            selected: List[Tuple[float, int, str]] = []
            running = 0
            for score, idx, sent in scored:
                sent_tokens = TokenBudget.estimate_tokens(sent)
                if running + sent_tokens <= target_tokens:
                    selected.append((score, idx, sent))
                    running += sent_tokens
                if running >= target_tokens:
                    break
        else:
            keep_count = max(1, int(len(scored) * ratio))
            selected = scored[:keep_count]

        selected.sort(key=lambda x: x[1])
        summary = " ".join(s for _, _, s in selected)

        compressed_tokens = TokenBudget.estimate_tokens(summary)
        kept = len(selected)
        dropped = len(sentences) - kept

        return CompressionResult(
            original_tokens=original_tokens,
            compressed_tokens=compressed_tokens,
            compression_ratio=round(compressed_tokens / max(original_tokens, 1), 3),
            sentences_kept=kept,
            sentences_dropped=dropped,
            summary_text=summary,
        )

    def compress_items(
        self,
        items: List[Dict[str, Any]],
        budget_tokens: int,
    ) -> List[Dict[str, Any]]:
        """Compress a list of context items to fit within a token budget.

        Strategy:
          1. Keep CRITICAL items unchanged.
          2. Compress HIGH items to 70% if needed.
          3. Compress MEDIUM items to 50%.
          4. Drop LOW items if still over budget.
        """
        priority_order = {"critical": 0, "high": 1, "medium": 2, "low": 3}
        items_sorted = sorted(
            items, key=lambda i: priority_order.get(str(i.get("priority", "low")).lower(), 3)
        )

        result: List[Dict[str, Any]] = []
        used = 0

        for item in items_sorted:
            val = str(item.get("value", ""))
            key = str(item.get("key", ""))
            item_tokens = TokenBudget.estimate_tokens(val) + TokenBudget.estimate_tokens(key)
            prio = str(item.get("priority", "low")).lower()

            if prio == "critical":
                result.append(item)
                used += item_tokens
                continue

            if used + item_tokens <= budget_tokens:
                result.append(item)
                used += item_tokens
                continue

            remaining = budget_tokens - used
            if remaining <= 10:
                continue

            if prio == "high":
                target = int(item_tokens * 0.70)
            elif prio == "medium":
                target = int(item_tokens * 0.50)
            else:
                continue

            target = min(target, remaining)
            cr = self.compress(val, target_tokens=target)
            compressed_item = dict(item)
            compressed_item["value"] = cr.summary_text
            compressed_item["_compressed"] = True
            compressed_item["_original_tokens"] = item_tokens
            result.append(compressed_item)
            used += cr.compressed_tokens

        return result

    def summarize_evicted(self, items: List[Dict[str, Any]], max_tokens: int = 200) -> str:
        """Create a brief summary of evicted context items for retention."""
        if not items:
            return ""

        lines: List[str] = []
        for item in items:
            key = item.get("key", "?")
            val = str(item.get("value", ""))
            snippet = val[:80].replace("\n", " ").strip()
            lines.append(f"- {key}: {snippet}")

        combined = "\n".join(lines)
        if TokenBudget.estimate_tokens(combined) <= max_tokens:
            return combined

        cr = self.compress(combined, target_tokens=max_tokens)
        return cr.summary_text


# ═════════════════════════════════════════════════════════════════════
#  4. Auto-Snapshot Manager (P0)
# ═════════════════════════════════════════════════════════════════════

class AutoSnapshotManager:
    """Automated context state capture and versioning.

    Features:
      - Periodic snapshots (configurable interval)
      - Version history with diffs between snapshots
      - Rollback to any prior snapshot
      - SHA-256 integrity verification on every snapshot
      - Atomic writes to prevent corruption
    """

    def __init__(
        self,
        snapshot_dir: Optional[Path] = None,
        interval_s: int = SNAPSHOT_INTERVAL_S,
        max_snapshots: int = MAX_SNAPSHOTS,
        db_path: Union[str, Path] = _DB_PATH,
    ) -> None:
        self._snapshot_dir = snapshot_dir or _SNAPSHOT_DIR
        self._interval_s = interval_s
        self._max_snapshots = max_snapshots
        self._db_path = Path(db_path)
        self._lock = threading.Lock()
        self._history: List[SnapshotMeta] = []
        self._timer: Optional[threading.Timer] = None
        self._shutdown = threading.Event()

        self._ensure_snapshot_dir()
        self._init_db_table()
        self._load_history()

    def _ensure_snapshot_dir(self) -> None:
        """Create snapshot directory if it doesn't exist."""
        try:
            self._snapshot_dir.mkdir(parents=True, exist_ok=True)
        except OSError as exc:
            logger.warning("Cannot create snapshot dir %s: %s", self._snapshot_dir, exc)

    def _init_db_table(self) -> None:
        """Create context_snapshots table for metadata tracking."""
        conn = _safe_connect(self._db_path)
        if conn is None:
            return
        try:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS context_snapshots (
                    snapshot_id TEXT PRIMARY KEY,
                    created_at REAL NOT NULL,
                    item_count INTEGER DEFAULT 0,
                    sha256 TEXT NOT NULL,
                    lane TEXT,
                    description TEXT DEFAULT '',
                    size_bytes INTEGER DEFAULT 0,
                    file_path TEXT
                )
            """)
            conn.commit()
        except Exception as exc:
            logger.error("Failed to create snapshot table: %s", exc)
        finally:
            conn.close()

    def _load_history(self) -> None:
        """Load snapshot history from DB on startup."""
        conn = _safe_connect(self._db_path)
        if conn is None:
            return
        try:
            rows = conn.execute(
                "SELECT snapshot_id, created_at, item_count, sha256, lane, "
                "description, size_bytes FROM context_snapshots "
                "ORDER BY created_at DESC LIMIT ?",
                (self._max_snapshots,),
            ).fetchall()
            self._history = []
            for row in rows:
                meta = SnapshotMeta(
                    snapshot_id=row["snapshot_id"],
                    created_at=row["created_at"],
                    item_count=row["item_count"],
                    sha256=row["sha256"],
                    lane=row["lane"],
                    description=row["description"] or "",
                    size_bytes=row["size_bytes"],
                )
                self._history.append(meta)
        except Exception as exc:
            logger.error("Failed to load snapshot history: %s", exc)
        finally:
            conn.close()

    def capture(
        self,
        state: Dict[str, Any],
        lane: Optional[str] = None,
        description: str = "",
    ) -> Optional[SnapshotMeta]:
        """Capture a snapshot of the current context state.

        Args:
            state: Serializable dict representing current context.
            lane: Optional lane filter for the snapshot.
            description: Human-readable description of why this snapshot was taken.

        Returns:
            SnapshotMeta on success, None on failure.
        """
        with self._lock:
            try:
                payload = json.dumps(state, default=str, sort_keys=True)
                sha = hashlib.sha256(payload.encode("utf-8")).hexdigest()

                if self._history and self._history[0].sha256 == sha:
                    return self._history[0]

                ts = time.time()
                snap_id = f"snap_{int(ts)}_{sha[:8]}"

                snap_path = self._snapshot_dir / f"{snap_id}.json"
                temp_path = snap_path.with_suffix(".tmp")

                try:
                    temp_path.write_text(payload, encoding="utf-8")
                    if temp_path.exists():
                        if snap_path.exists():
                            snap_path.unlink()
                        temp_path.rename(snap_path)
                except OSError as exc:
                    logger.warning("Snapshot file write failed: %s", exc)
                    snap_path = None

                item_count = 0
                if isinstance(state, dict):
                    for key in ("items", "window_items", "context_items"):
                        if key in state and isinstance(state[key], list):
                            item_count = len(state[key])
                            break

                meta = SnapshotMeta(
                    snapshot_id=snap_id,
                    created_at=ts,
                    item_count=item_count,
                    sha256=sha,
                    lane=lane,
                    description=description,
                    size_bytes=len(payload.encode("utf-8")),
                )

                self._persist_meta(meta, str(snap_path) if snap_path else "")
                self._history.insert(0, meta)
                self._prune_old_snapshots()

                return meta

            except Exception as exc:
                logger.error("Snapshot capture failed: %s", exc)
                return None

    def _persist_meta(self, meta: SnapshotMeta, file_path: str) -> None:
        """Write snapshot metadata to DB."""
        conn = _safe_connect(self._db_path)
        if conn is None:
            return
        try:
            conn.execute(
                "INSERT OR REPLACE INTO context_snapshots "
                "(snapshot_id, created_at, item_count, sha256, lane, "
                "description, size_bytes, file_path) "
                "VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                (
                    meta.snapshot_id,
                    meta.created_at,
                    meta.item_count,
                    meta.sha256,
                    meta.lane,
                    meta.description,
                    meta.size_bytes,
                    file_path,
                ),
            )
            conn.commit()
        except Exception as exc:
            logger.error("Snapshot DB persist failed: %s", exc)
        finally:
            conn.close()

    def _prune_old_snapshots(self) -> None:
        """Remove snapshots beyond max_snapshots limit."""
        while len(self._history) > self._max_snapshots:
            old = self._history.pop()
            snap_path = self._snapshot_dir / f"{old.snapshot_id}.json"
            try:
                if snap_path.exists():
                    snap_path.unlink()
            except OSError:
                pass
            conn = _safe_connect(self._db_path)
            if conn:
                try:
                    conn.execute(
                        "DELETE FROM context_snapshots WHERE snapshot_id = ?",
                        (old.snapshot_id,),
                    )
                    conn.commit()
                except Exception:
                    pass
                finally:
                    conn.close()

    def restore(self, snapshot_id: str) -> Optional[Dict[str, Any]]:
        """Restore a prior snapshot by ID.

        Returns the deserialized state dict or None on failure.
        """
        snap_path = self._snapshot_dir / f"{snapshot_id}.json"
        try:
            if snap_path.exists():
                payload = snap_path.read_text(encoding="utf-8")
                state = json.loads(payload)
                stored_sha = None
                for meta in self._history:
                    if meta.snapshot_id == snapshot_id:
                        stored_sha = meta.sha256
                        break
                if stored_sha:
                    actual_sha = hashlib.sha256(
                        json.dumps(state, default=str, sort_keys=True).encode("utf-8")
                    ).hexdigest()
                    if actual_sha != stored_sha:
                        logger.error(
                            "Integrity check FAILED for snapshot %s: "
                            "expected %s, got %s",
                            snapshot_id, stored_sha[:12], actual_sha[:12],
                        )
                        return None
                return state
        except Exception as exc:
            logger.error("Snapshot restore failed for %s: %s", snapshot_id, exc)

        conn = _safe_connect(self._db_path)
        if conn is None:
            return None
        try:
            row = conn.execute(
                "SELECT file_path FROM context_snapshots WHERE snapshot_id = ?",
                (snapshot_id,),
            ).fetchone()
            if row and row["file_path"]:
                alt_path = Path(row["file_path"])
                if alt_path.exists():
                    payload = alt_path.read_text(encoding="utf-8")
                    return json.loads(payload)
        except Exception as exc:
            logger.error("Snapshot restore from DB path failed: %s", exc)
        finally:
            conn.close()

        return None

    def diff(self, snap_id_a: str, snap_id_b: str) -> Dict[str, Any]:
        """Compute diff between two snapshots.

        Returns dict with added, removed, and modified keys.
        """
        state_a = self.restore(snap_id_a)
        state_b = self.restore(snap_id_b)

        if state_a is None or state_b is None:
            return {
                "error": "One or both snapshots could not be restored",
                "snap_a_found": state_a is not None,
                "snap_b_found": state_b is not None,
            }

        def _extract_items(state: Dict) -> Dict[str, Any]:
            items = {}
            for key in ("items", "window_items", "context_items"):
                if key in state and isinstance(state[key], list):
                    for item in state[key]:
                        k = item.get("key", str(len(items)))
                        items[k] = item
                    break
            if not items:
                for k, v in state.items():
                    items[k] = v
            return items

        items_a = _extract_items(state_a)
        items_b = _extract_items(state_b)
        keys_a = set(items_a.keys())
        keys_b = set(items_b.keys())

        added = {k: items_b[k] for k in (keys_b - keys_a)}
        removed = {k: items_a[k] for k in (keys_a - keys_b)}
        modified = {}
        for k in keys_a & keys_b:
            if json.dumps(items_a[k], default=str) != json.dumps(items_b[k], default=str):
                modified[k] = {"before": items_a[k], "after": items_b[k]}

        return {
            "added_count": len(added),
            "removed_count": len(removed),
            "modified_count": len(modified),
            "added": added,
            "removed": removed,
            "modified": modified,
        }

    def list_snapshots(self, limit: int = 20) -> List[Dict[str, Any]]:
        """List recent snapshots with metadata."""
        result = []
        for meta in self._history[:limit]:
            entry = {
                "snapshot_id": meta.snapshot_id,
                "created_at": meta.created_at,
                "item_count": meta.item_count,
                "sha256": meta.sha256[:16] + "...",
                "lane": meta.lane,
                "description": meta.description,
                "size_bytes": meta.size_bytes,
                "age_minutes": round((time.time() - meta.created_at) / 60, 1),
            }
            result.append(entry)
        return result

    def verify_integrity(self, snapshot_id: str) -> bool:
        """Verify SHA-256 integrity of a snapshot file."""
        snap_path = self._snapshot_dir / f"{snapshot_id}.json"
        if not snap_path.exists():
            return False
        try:
            payload = snap_path.read_text(encoding="utf-8")
            state = json.loads(payload)
            actual_sha = hashlib.sha256(
                json.dumps(state, default=str, sort_keys=True).encode("utf-8")
            ).hexdigest()
            for meta in self._history:
                if meta.snapshot_id == snapshot_id:
                    return actual_sha == meta.sha256
            return True
        except Exception:
            return False

    def start_periodic(self, state_provider: Any) -> None:
        """Start periodic snapshot capture.

        Args:
            state_provider: callable that returns current state dict.
        """
        if self._shutdown.is_set():
            return

        def _tick() -> None:
            if self._shutdown.is_set():
                return
            try:
                state = state_provider()
                if state:
                    self.capture(state, description="periodic")
            except Exception as exc:
                logger.error("Periodic snapshot failed: %s", exc)
            if not self._shutdown.is_set():
                self._timer = threading.Timer(self._interval_s, _tick)
                self._timer.daemon = True
                self._timer.start()

        self._timer = threading.Timer(self._interval_s, _tick)
        self._timer.daemon = True
        self._timer.start()

    def stop_periodic(self) -> None:
        """Stop periodic snapshot capture."""
        self._shutdown.set()
        if self._timer:
            self._timer.cancel()
            self._timer = None

    def stats(self) -> Dict[str, Any]:
        """Snapshot subsystem statistics."""
        total_bytes = sum(m.size_bytes for m in self._history)
        return {
            "snapshot_count": len(self._history),
            "max_snapshots": self._max_snapshots,
            "total_bytes": total_bytes,
            "snapshot_dir": str(self._snapshot_dir),
            "interval_s": self._interval_s,
            "latest": self._history[0].snapshot_id if self._history else None,
            "oldest": self._history[-1].snapshot_id if self._history else None,
        }


# ═════════════════════════════════════════════════════════════════════
#  5. Context Quality Scorer (P1)
# ═════════════════════════════════════════════════════════════════════

class ContextQualityScorer:
    """Measures quality of assembled context.

    Dimensions:
      - Freshness: age-weighted composite across all items
      - Relevance: query-context similarity via TF-IDF cosine
      - Coverage: are all required context domains present?
      - Lane purity: no cross-contamination across lanes
      - Contradiction penalty: reduces score when contradictions detected
    """

    def __init__(self, validator: Optional[ContextValidator] = None) -> None:
        self._validator = validator or ContextValidator()
        self._word_re = re.compile(r"\b\w+\b")

    def _freshness_score(self, items: List[Dict[str, Any]]) -> Tuple[float, int, int]:
        """Compute composite freshness. Returns (score, stale_count, expired_count)."""
        if not items:
            return (1.0, 0, 0)

        now = time.time()
        scores: List[float] = []
        stale = 0
        expired = 0

        for item in items:
            created = item.get("created_at", now)
            if isinstance(created, str):
                try:
                    import datetime as _dt
                    created = _dt.datetime.fromisoformat(
                        created.replace("Z", "+00:00")
                    ).timestamp()
                except (ValueError, TypeError):
                    created = now

            age = now - created
            freshness = math.exp(-0.693 * age / FRESHNESS_DECAY_HALF_LIFE_S)
            scores.append(freshness)

            if freshness < EXPIRED_THRESHOLD:
                expired += 1
            elif freshness < STALE_THRESHOLD:
                stale += 1

        avg = sum(scores) / len(scores) if scores else 1.0
        return (round(avg, 4), stale, expired)

    def _relevance_score(
        self, query: str, items: List[Dict[str, Any]]
    ) -> float:
        """Compute TF-IDF cosine similarity between query and context items."""
        if not query or not items:
            return 0.5  # neutral score when no query provided

        corpus: List[str] = [query]
        for item in items:
            text = str(item.get("value", "")) + " " + str(item.get("key", ""))
            corpus.append(text)

        all_words: Set[str] = set()
        doc_words: List[Set[str]] = []
        for doc in corpus:
            words = set(w.lower() for w in self._word_re.findall(doc))
            doc_words.append(words)
            all_words |= words

        if not all_words:
            return 0.5

        n_docs = len(corpus)
        idf: Dict[str, float] = {}
        for word in all_words:
            doc_count = sum(1 for dw in doc_words if word in dw)
            idf[word] = math.log((n_docs + 1) / (doc_count + 1)) + 1.0

        def _tfidf_vec(text: str) -> Dict[str, float]:
            words = [w.lower() for w in self._word_re.findall(text)]
            if not words:
                return {}
            tf = collections.Counter(words)
            total = len(words)
            return {w: (c / total) * idf.get(w, 1.0) for w, c in tf.items()}

        query_vec = _tfidf_vec(query)
        if not query_vec:
            return 0.5

        similarities: List[float] = []
        for item in items:
            text = str(item.get("value", "")) + " " + str(item.get("key", ""))
            item_vec = _tfidf_vec(text)

            shared_words = set(query_vec.keys()) & set(item_vec.keys())
            dot = sum(query_vec[w] * item_vec[w] for w in shared_words)
            mag_q = math.sqrt(sum(v * v for v in query_vec.values()))
            mag_i = math.sqrt(sum(v * v for v in item_vec.values()))

            if mag_q > 0 and mag_i > 0:
                sim = dot / (mag_q * mag_i)
            else:
                sim = 0.0
            similarities.append(sim)

        return round(max(similarities) * 0.5 + (sum(similarities) / len(similarities)) * 0.5, 4) if similarities else 0.0

    def _coverage_score(
        self, items: List[Dict[str, Any]], required_domains: Optional[List[str]] = None
    ) -> Tuple[float, List[str]]:
        """Check coverage of required context domains.

        Returns (score, missing_domains).
        """
        domains = required_domains or REQUIRED_DOMAINS
        if not domains:
            return (1.0, [])

        all_text = ""
        all_keys: Set[str] = set()
        for item in items:
            all_text += " " + str(item.get("value", "")) + " " + str(item.get("key", ""))
            all_keys.add(str(item.get("key", "")).lower())

        all_text_lower = all_text.lower()

        domain_indicators: Dict[str, List[str]] = {
            "parties": ["plaintiff", "defendant", "petitioner", "respondent", "pigors", "watson"],
            "case_numbers": ["2024-001507", "2023-5907", "2025-002760", "366810", "case_number"],
            "judge": ["mcneill", "judge", "hon.", "judicial"],
            "current_filing": ["filing", "motion", "brief", "complaint", "petition"],
            "deadlines": ["deadline", "due_date", "due date", "filing_date"],
            "evidence": ["evidence", "exhibit", "document", "testimony", "affidavit"],
            "authorities": ["mcr", "mcl", "mre", "authority", "statute", "rule"],
        }

        found: Set[str] = set()
        missing: List[str] = []

        for domain in domains:
            indicators = domain_indicators.get(domain, [domain])
            domain_found = False
            for indicator in indicators:
                if indicator in all_text_lower or indicator in all_keys:
                    domain_found = True
                    break
            if domain_found:
                found.add(domain)
            else:
                missing.append(domain)

        score = len(found) / len(domains) if domains else 1.0
        return (round(score, 4), missing)

    def _lane_purity_score(
        self, items: List[Dict[str, Any]], target_lane: Optional[str] = None
    ) -> float:
        """Score lane purity: 1.0 = all items from target lane, 0.0 = total cross-contamination."""
        if not target_lane or not items:
            return 1.0

        total = 0
        correct = 0
        for item in items:
            item_lane = item.get("lane")
            if item_lane is None:
                continue
            total += 1
            if item_lane == target_lane or item_lane == "C":
                correct += 1

        if total == 0:
            return 1.0
        return round(correct / total, 4)

    def _contradiction_penalty(self, items: List[Dict[str, Any]]) -> float:
        """Compute contradiction penalty across context items.

        Returns 0.0 (no contradictions) to 1.0 (severe contradictions).
        """
        if len(items) < 2:
            return 0.0

        contradiction_count = 0
        checked = 0

        for i in range(len(items)):
            text_i = str(items[i].get("value", ""))
            if len(text_i) < 20:
                continue
            remaining = items[i + 1:]
            pairs = self._validator.detect_contradictions(text_i, remaining)
            contradiction_count += len(pairs)
            checked += 1

        if checked == 0:
            return 0.0

        penalty = min(contradiction_count / max(checked, 1) * 0.3, 1.0)
        return round(penalty, 4)

    def score(
        self,
        items: List[Dict[str, Any]],
        query: str = "",
        target_lane: Optional[str] = None,
        required_domains: Optional[List[str]] = None,
    ) -> QualityReport:
        """Compute overall context quality score.

        Args:
            items: List of context item dicts.
            query: Optional query text for relevance scoring.
            target_lane: Expected lane for purity scoring.
            required_domains: Override default required domains.

        Returns:
            QualityReport with dimensional scores and overall composite.
        """
        freshness, stale_count, expired_count = self._freshness_score(items)
        relevance = self._relevance_score(query, items)
        coverage, missing = self._coverage_score(items, required_domains)
        purity = self._lane_purity_score(items, target_lane)
        contradiction = self._contradiction_penalty(items)

        overall = (
            QUALITY_WEIGHTS["freshness"] * freshness
            + QUALITY_WEIGHTS["relevance"] * relevance
            + QUALITY_WEIGHTS["coverage"] * coverage
            + QUALITY_WEIGHTS["lane_purity"] * purity
            - QUALITY_WEIGHTS["contradiction_penalty"] * contradiction
        )
        overall = round(max(0.0, min(1.0, overall)), 4)

        warnings: List[str] = []
        if freshness < STALE_THRESHOLD:
            warnings.append(f"Context is STALE (freshness={freshness:.3f})")
        if stale_count > 0:
            warnings.append(f"{stale_count} stale items detected")
        if expired_count > 0:
            warnings.append(f"{expired_count} EXPIRED items — eviction recommended")
        if missing:
            warnings.append(f"Missing domains: {', '.join(missing)}")
        if purity < 0.8 and target_lane:
            warnings.append(
                f"Lane contamination detected (purity={purity:.3f}) for lane {target_lane}"
            )
        if contradiction > 0.1:
            warnings.append(
                f"Contradictions detected (penalty={contradiction:.3f})"
            )

        if _PYDANTIC:
            return QualityReport(
                overall_score=overall,
                freshness_score=freshness,
                relevance_score=relevance,
                coverage_score=coverage,
                lane_purity_score=purity,
                contradiction_penalty=contradiction,
                missing_domains=missing,
                warnings=warnings,
                item_count=len(items),
                stale_count=stale_count,
                expired_count=expired_count,
            )
        else:
            return QualityReport(
                overall_score=overall,
                freshness_score=freshness,
                relevance_score=relevance,
                coverage_score=coverage,
                lane_purity_score=purity,
                contradiction_penalty=contradiction,
                missing_domains=list(missing),
                warnings=list(warnings),
                item_count=len(items),
                stale_count=stale_count,
                expired_count=expired_count,
            )


# ═════════════════════════════════════════════════════════════════════
#  6. Unified Context Orchestrator
# ═════════════════════════════════════════════════════════════════════

class ContextOrchestrator:
    """Central context engineering hub — wraps all subsystems.

    Responsibilities:
      - Assemble optimal context for any consumer (agent, pipeline, UI)
      - Route to appropriate retrieval backend
      - Manage token budget across context sections
      - Validate all context before delivery
      - Compress when budget is tight
      - Auto-snapshot on significant state changes
      - Report quality metrics

    Extends (does not replace) the base ContextManager from context_manager.py.
    """

    _instance: Optional["ContextOrchestrator"] = None
    _init_lock = threading.Lock()

    def __new__(cls, *args: Any, **kwargs: Any) -> "ContextOrchestrator":
        with cls._init_lock:
            if cls._instance is None:
                cls._instance = super().__new__(cls)
                cls._instance._initialized = False
            return cls._instance

    def __init__(
        self,
        db_path: Optional[Union[str, Path]] = None,
        model_tier: str = "medium",
        snapshot_interval: int = SNAPSHOT_INTERVAL_S,
    ) -> None:
        if self._initialized:
            return
        self._initialized = True

        self._db_path = Path(db_path) if db_path else _DB_PATH
        self._model_tier = model_tier

        budget_cfg = TokenBudgetConfig(
            max_tokens=MODEL_TOKEN_LIMITS.get(model_tier, 8192),
            model_tier=model_tier,
        )
        self.budget = TokenBudget(config=budget_cfg)
        self.validator = ContextValidator()
        self.compressor = ContextCompressor()
        self.snapshots = AutoSnapshotManager(
            db_path=self._db_path,
            interval_s=snapshot_interval,
        )
        self.quality = ContextQualityScorer(validator=self.validator)

        self._base_manager = None  # lazy-loaded ContextManager
        self._lock = threading.Lock()
        self._assembly_count: int = 0
        self._validation_count: int = 0
        self._compression_count: int = 0
        self._rejection_count: int = 0

        self._init_orchestrator_table()

    def _init_orchestrator_table(self) -> None:
        """Create orchestrator_log table for audit trail."""
        conn = _safe_connect(self._db_path)
        if conn is None:
            return
        try:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS context_orchestrator_log (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp REAL NOT NULL,
                    action TEXT NOT NULL,
                    lane TEXT,
                    item_count INTEGER DEFAULT 0,
                    tokens_used INTEGER DEFAULT 0,
                    quality_score REAL,
                    details TEXT,
                    created_at TEXT DEFAULT (datetime('now'))
                )
            """)
            conn.commit()
        except Exception as exc:
            logger.error("Failed to create orchestrator log table: %s", exc)
        finally:
            conn.close()

    def _get_base_manager(self) -> Any:
        """Lazy-load the base ContextManager to avoid circular imports."""
        if self._base_manager is not None:
            return self._base_manager
        try:
            local_model_dir = _HERE.parent / "local_model"
            if str(local_model_dir) not in sys.path:
                sys.path.insert(0, str(local_model_dir))
            from context_manager import ContextManager
            self._base_manager = ContextManager(db_path=self._db_path)
            return self._base_manager
        except ImportError:
            logger.warning("Base ContextManager not available — running standalone")
            return None

    # ── Core Assembly ─────────────────────────────────────────────

    def assemble(
        self,
        query: str = "",
        lane: Optional[str] = None,
        max_tokens: Optional[int] = None,
        include_entities: bool = True,
        required_domains: Optional[List[str]] = None,
    ) -> Dict[str, Any]:
        """Assemble optimal context for a consumer.

        This is the primary entry point. It:
          1. Gathers items from the base ContextManager window and memory
          2. Validates each item (entity, lane, fabrication checks)
          3. Scores quality across all dimensions
          4. Compresses if over token budget
          5. Snapshots if state has changed significantly
          6. Returns assembled context with quality report

        Args:
            query: The consumer's query/task for relevance scoring.
            lane: Target lane for filtering and purity enforcement.
            max_tokens: Override token budget for this assembly.
            include_entities: Whether to include entity facts.
            required_domains: Override required coverage domains.

        Returns:
            Dict with keys: items, quality, budget, metadata.
        """
        with self._lock:
            self._assembly_count += 1

        effective_budget = max_tokens or self.budget.context_budget

        raw_items = self._gather_items(lane, include_entities)

        validated_items, validation_warnings = self._validate_batch(raw_items, lane)

        item_tokens = TokenBudget.estimate_tokens_for_items(validated_items)
        compressed = False
        if item_tokens > effective_budget:
            validated_items = self.compressor.compress_items(
                validated_items, effective_budget
            )
            compressed = True
            with self._lock:
                self._compression_count += 1

        quality_report = self.quality.score(
            validated_items,
            query=query,
            target_lane=lane,
            required_domains=required_domains,
        )

        final_tokens = TokenBudget.estimate_tokens_for_items(validated_items)
        self.budget.reset()
        for item in validated_items:
            val = str(item.get("value", ""))
            self.budget.allocate_context(val)

        if self._assembly_count % 5 == 0:
            self._auto_snapshot(validated_items, lane)

        self._log_assembly(lane, len(validated_items), final_tokens, quality_report)

        result = {
            "items": validated_items,
            "quality": self._quality_to_dict(quality_report),
            "budget": self.budget.utilization(),
            "metadata": {
                "assembly_id": self._assembly_count,
                "lane": lane,
                "query": query[:100] if query else "",
                "compressed": compressed,
                "original_count": len(raw_items),
                "final_count": len(validated_items),
                "final_tokens": final_tokens,
                "validation_warnings": validation_warnings[:10],
            },
        }
        return result

    def _gather_items(
        self, lane: Optional[str], include_entities: bool
    ) -> List[Dict[str, Any]]:
        """Gather raw context items from all available sources."""
        items: List[Dict[str, Any]] = []

        base = self._get_base_manager()
        if base is not None:
            try:
                window_items = base.get_context(lane=lane)
                for wi in window_items:
                    if hasattr(wi, "to_dict"):
                        items.append(wi.to_dict())
                    elif isinstance(wi, dict):
                        items.append(wi)
                    else:
                        items.append({"key": str(getattr(wi, "key", "?")), "value": str(wi)})
            except Exception as exc:
                logger.error("Failed to get window items: %s", exc)

            if include_entities:
                try:
                    entities = base.memory.get_all_entities()
                    for ek, ev in entities.items():
                        items.append({
                            "key": f"entity:{ek}",
                            "value": json.dumps(ev, default=str),
                            "priority": "critical",
                            "lane": None,
                            "source": "entity_memory",
                            "created_at": time.time(),
                        })
                except Exception as exc:
                    logger.error("Failed to get entities: %s", exc)

            try:
                short_items = base.memory.recall_short(lane=lane)
                for si in short_items:
                    if hasattr(si, "to_dict"):
                        d = si.to_dict()
                        if d.get("key") not in {i.get("key") for i in items}:
                            items.append(d)
                    elif isinstance(si, dict):
                        items.append(si)
            except Exception as exc:
                logger.error("Failed to get short-term items: %s", exc)
        else:
            if include_entities:
                for ek, ev in CORRECT_ENTITIES.items():
                    items.append({
                        "key": f"entity:{ek}",
                        "value": json.dumps(ev, default=str),
                        "priority": "critical",
                        "lane": None,
                        "source": "entity_memory_fallback",
                        "created_at": time.time(),
                    })

        return items

    def _validate_batch(
        self, items: List[Dict[str, Any]], target_lane: Optional[str]
    ) -> Tuple[List[Dict[str, Any]], List[str]]:
        """Validate a batch of context items. Returns (valid_items, warnings)."""
        valid: List[Dict[str, Any]] = []
        all_warnings: List[str] = []

        for item in items:
            key = str(item.get("key", ""))
            value = item.get("value", "")
            item_lane = item.get("lane")

            result = self.validator.validate_item(
                key=key,
                value=value,
                lane=item_lane,
                target_lane=target_lane,
                existing_items=valid,
            )

            with self._lock:
                self._validation_count += 1

            all_warnings.extend(result.warnings)

            if result.valid:
                valid.append(item)
            else:
                with self._lock:
                    self._rejection_count += 1
                all_warnings.extend(
                    [f"REJECTED '{key}': {e}" for e in result.errors]
                )
                logger.warning(
                    "Context item '%s' REJECTED: %s", key, "; ".join(result.errors)
                )

        return valid, all_warnings

    def _auto_snapshot(
        self, items: List[Dict[str, Any]], lane: Optional[str]
    ) -> None:
        """Capture an automatic snapshot after significant state changes."""
        state = {
            "items": items,
            "assembly_count": self._assembly_count,
            "timestamp": time.time(),
        }
        self.snapshots.capture(
            state,
            lane=lane,
            description=f"auto:assembly#{self._assembly_count}",
        )

    def _log_assembly(
        self,
        lane: Optional[str],
        item_count: int,
        tokens: int,
        quality: QualityReport,
    ) -> None:
        """Log assembly event to DB."""
        conn = _safe_connect(self._db_path)
        if conn is None:
            return
        try:
            q_score = quality.overall_score if hasattr(quality, "overall_score") else 0.0
            conn.execute(
                "INSERT INTO context_orchestrator_log "
                "(timestamp, action, lane, item_count, tokens_used, quality_score, details) "
                "VALUES (?, ?, ?, ?, ?, ?, ?)",
                (
                    time.time(),
                    "assemble",
                    lane,
                    item_count,
                    tokens,
                    q_score,
                    json.dumps({
                        "freshness": getattr(quality, "freshness_score", 0),
                        "relevance": getattr(quality, "relevance_score", 0),
                        "coverage": getattr(quality, "coverage_score", 0),
                        "warnings_count": len(getattr(quality, "warnings", [])),
                    }),
                ),
            )
            conn.commit()
        except Exception as exc:
            logger.error("Assembly log failed: %s", exc)
        finally:
            conn.close()

    @staticmethod
    def _quality_to_dict(report: QualityReport) -> Dict[str, Any]:
        """Convert QualityReport to dict regardless of Pydantic/dataclass."""
        if _PYDANTIC and hasattr(report, "model_dump"):
            return report.model_dump()
        elif hasattr(report, "__dict__"):
            d = {}
            for k, v in report.__dict__.items():
                if not k.startswith("_"):
                    d[k] = v
            return d
        return {}

    # ── Item Management ───────────────────────────────────────────

    def add(
        self,
        key: str,
        value: Any,
        priority: str = "medium",
        lane: Optional[str] = None,
        source: str = "orchestrator",
        validate: bool = True,
    ) -> Dict[str, Any]:
        """Add a context item through the orchestrator with full validation.

        Returns dict with success status and any validation warnings.
        """
        result: Dict[str, Any] = {"success": False, "key": key, "warnings": []}

        if validate:
            vr = self.validator.validate_item(
                key=key,
                value=value,
                lane=lane,
                target_lane=lane,
            )
            result["warnings"] = vr.warnings + vr.errors
            if not vr.valid:
                with self._lock:
                    self._rejection_count += 1
                result["rejected"] = True
                result["errors"] = vr.errors
                return result

        text = str(value)
        if not self.budget.try_fit(text, "context"):
            cr = self.compressor.compress(text, target_tokens=self.budget.context_remaining // 2)
            value = cr.summary_text
            result["compressed"] = True
            result["compression_ratio"] = cr.compression_ratio

        base = self._get_base_manager()
        if base is not None:
            try:
                from context_manager import ContextPriority as CP
                prio_map = {
                    "critical": CP.CRITICAL,
                    "high": CP.HIGH,
                    "medium": CP.MEDIUM,
                    "low": CP.LOW,
                }
                base.add_context(
                    key=key,
                    value=value,
                    priority=prio_map.get(priority.lower(), CP.MEDIUM),
                    lane=lane,
                    source=source,
                )
                result["success"] = True
            except Exception as exc:
                result["error"] = str(exc)
                logger.error("Failed to add context via base manager: %s", exc)
        else:
            result["success"] = True
            result["note"] = "stored in orchestrator only (base manager unavailable)"

        self.budget.allocate_context(str(value))
        return result

    def remove(self, key: str) -> bool:
        """Remove a context item by key. Returns True if found and removed."""
        base = self._get_base_manager()
        if base is not None:
            try:
                item = base.find_context(key)
                if item:
                    self.budget.release_context(str(item.value))
                    base.window._items = [
                        i for i in base.window._items if i.key != key
                    ]
                    base.window._pinned = [
                        i for i in base.window._pinned if i.key != key
                    ]
                    return True
            except Exception as exc:
                logger.error("Remove failed: %s", exc)
        return False

    def find(self, key: str) -> Optional[Dict[str, Any]]:
        """Find a context item by key."""
        base = self._get_base_manager()
        if base is not None:
            try:
                item = base.find_context(key)
                if item and hasattr(item, "to_dict"):
                    return item.to_dict()
            except Exception:
                pass
        return None

    # ── Compression API ───────────────────────────────────────────

    def compress_text(
        self, text: str, target_tokens: Optional[int] = None, ratio: float = 0.5
    ) -> CompressionResult:
        """Public API for text compression."""
        return self.compressor.compress(text, target_tokens=target_tokens, ratio=ratio)

    def compress_context(self, max_tokens: Optional[int] = None) -> Dict[str, Any]:
        """Compress the entire active context to fit within budget.

        Returns compression report.
        """
        base = self._get_base_manager()
        if base is None:
            return {"error": "base manager unavailable"}

        items = []
        try:
            for item in base.window.items:
                if hasattr(item, "to_dict"):
                    items.append(item.to_dict())
        except Exception:
            return {"error": "failed to read window items"}

        budget = max_tokens or self.budget.context_budget
        original_tokens = TokenBudget.estimate_tokens_for_items(items)

        if original_tokens <= budget:
            return {
                "action": "none_needed",
                "original_tokens": original_tokens,
                "budget": budget,
            }

        compressed = self.compressor.compress_items(items, budget)
        compressed_tokens = TokenBudget.estimate_tokens_for_items(compressed)

        with self._lock:
            self._compression_count += 1

        return {
            "action": "compressed",
            "original_tokens": original_tokens,
            "compressed_tokens": compressed_tokens,
            "ratio": round(compressed_tokens / max(original_tokens, 1), 3),
            "items_before": len(items),
            "items_after": len(compressed),
        }

    # ── Validation API ────────────────────────────────────────────

    def validate_text(self, text: str) -> Dict[str, Any]:
        """Validate text against all guards. Returns dict with results."""
        result = self.validator.validate_text(text)
        if _PYDANTIC and hasattr(result, "model_dump"):
            return result.model_dump()
        return {
            "valid": result.valid,
            "errors": result.errors,
            "warnings": result.warnings,
            "entity_issues": result.entity_issues,
            "fabrication_hits": result.fabrication_hits,
        }

    def validate_lane(
        self, item_lane: Optional[str], target_lane: Optional[str]
    ) -> Dict[str, Any]:
        """Validate lane boundary compliance."""
        result = self.validator.validate_lane(item_lane, target_lane)
        return {
            "valid": result.valid,
            "errors": result.errors,
            "lane_violations": result.lane_violations,
        }

    # ── Snapshot API ──────────────────────────────────────────────

    def snapshot(
        self, description: str = "manual", lane: Optional[str] = None
    ) -> Optional[Dict[str, Any]]:
        """Take a manual snapshot of current context state."""
        items = self._gather_items(lane, include_entities=True)
        state = {
            "items": items,
            "assembly_count": self._assembly_count,
            "timestamp": time.time(),
            "budget": self.budget.utilization(),
        }
        meta = self.snapshots.capture(state, lane=lane, description=description)
        if meta:
            return {
                "snapshot_id": meta.snapshot_id,
                "sha256": meta.sha256[:16] + "...",
                "item_count": meta.item_count,
                "size_bytes": meta.size_bytes,
            }
        return None

    def restore_snapshot(self, snapshot_id: str) -> Dict[str, Any]:
        """Restore context from a prior snapshot."""
        state = self.snapshots.restore(snapshot_id)
        if state is None:
            return {"success": False, "error": f"Snapshot {snapshot_id} not found or corrupt"}

        items = state.get("items", [])
        base = self._get_base_manager()
        if base is not None:
            try:
                base.window.clear(keep_pinned=False)
                from context_manager import ContextPriority as CP, ContextItem as CI
                prio_map = {
                    "critical": CP.CRITICAL,
                    "high": CP.HIGH,
                    "medium": CP.MEDIUM,
                    "low": CP.LOW,
                }
                for item in items:
                    ci = CI(
                        key=item.get("key", "?"),
                        value=item.get("value", ""),
                        priority=prio_map.get(
                            str(item.get("priority", "medium")).lower(), CP.MEDIUM
                        ),
                        lane=item.get("lane"),
                        source=item.get("source", "snapshot_restore"),
                    )
                    base.window.add(ci)
            except Exception as exc:
                return {"success": False, "error": f"Restore failed: {exc}"}

        self.budget.reset()
        return {
            "success": True,
            "snapshot_id": snapshot_id,
            "items_restored": len(items),
        }

    def list_snapshots(self, limit: int = 20) -> List[Dict[str, Any]]:
        """List available snapshots."""
        return self.snapshots.list_snapshots(limit=limit)

    # ── Quality API ───────────────────────────────────────────────

    def quality_report(
        self,
        query: str = "",
        lane: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Generate a quality report for the current context."""
        items = self._gather_items(lane, include_entities=True)
        report = self.quality.score(items, query=query, target_lane=lane)
        return self._quality_to_dict(report)

    # ── Budget API ────────────────────────────────────────────────

    def resize_budget(self, model_tier: str) -> Dict[str, Any]:
        """Resize token budget for a different model tier."""
        self._model_tier = model_tier
        self.budget.resize(model_tier)
        return self.budget.utilization()

    def budget_status(self) -> Dict[str, Any]:
        """Current token budget status."""
        return self.budget.utilization()

    # ── Health & Stats ────────────────────────────────────────────

    def get_stats(self) -> Dict[str, Any]:
        """Comprehensive stats for the entire orchestrator."""
        base_health = {}
        base = self._get_base_manager()
        if base is not None:
            try:
                base_health = base.health()
            except Exception:
                base_health = {"error": "unavailable"}

        return {
            "orchestrator": {
                "assemblies": self._assembly_count,
                "validations": self._validation_count,
                "compressions": self._compression_count,
                "rejections": self._rejection_count,
                "model_tier": self._model_tier,
                "db_path": str(self._db_path),
            },
            "budget": self.budget.utilization(),
            "snapshots": self.snapshots.stats(),
            "base_manager": base_health,
            "valid_lanes": sorted(VALID_LANES),
            "pydantic_available": _PYDANTIC,
        }

    def health(self) -> Dict[str, Any]:
        """Quick health check for the orchestrator."""
        base = self._get_base_manager()
        base_ok = base is not None

        snap_stats = self.snapshots.stats()
        budget_util = self.budget.utilization()

        status = "healthy"
        issues: List[str] = []

        if not base_ok:
            issues.append("Base ContextManager unavailable")
            status = "degraded"

        if budget_util["context"]["pct"] > 90:
            issues.append("Context budget >90% utilized")
            status = "warning"

        if snap_stats["snapshot_count"] == 0:
            issues.append("No snapshots captured yet")

        return {
            "status": status,
            "base_manager": "connected" if base_ok else "disconnected",
            "budget_pct": budget_util["context"]["pct"],
            "snapshot_count": snap_stats["snapshot_count"],
            "assemblies": self._assembly_count,
            "rejections": self._rejection_count,
            "issues": issues,
        }

    # ── Lifecycle ─────────────────────────────────────────────────

    def shutdown(self) -> None:
        """Graceful shutdown — stop periodic snapshots and flush state."""
        self.snapshots.stop_periodic()

        items = self._gather_items(lane=None, include_entities=False)
        if items:
            self.snapshots.capture(
                {"items": items, "timestamp": time.time()},
                description="shutdown",
            )

        base = self._get_base_manager()
        if base is not None:
            try:
                base.shutdown()
            except Exception:
                pass

        logger.info(
            "ContextOrchestrator shutdown: %d assemblies, %d rejections",
            self._assembly_count,
            self._rejection_count,
        )

    def reset(self) -> None:
        """Reset singleton state for testing."""
        self.shutdown()
        ContextOrchestrator._instance = None
        ContextOrchestrator._initialized = False  # type: ignore[attr-defined]


# ═════════════════════════════════════════════════════════════════════
#  Module-Level Convenience
# ═════════════════════════════════════════════════════════════════════

def get_orchestrator(
    db_path: Optional[Union[str, Path]] = None,
    model_tier: str = "medium",
) -> ContextOrchestrator:
    """Get the singleton ContextOrchestrator instance."""
    return ContextOrchestrator(
        db_path=db_path,
        model_tier=model_tier,
    )


# ═════════════════════════════════════════════════════════════════════
#  CLI Interface
# ═════════════════════════════════════════════════════════════════════

def _cli_main() -> None:
    """Command-line interface for the Context Orchestrator."""
    import pprint

    orch = get_orchestrator()

    if len(sys.argv) < 2:
        print("LitigationOS Context Orchestrator — Δ99 Ω∞")
        print("=" * 50)
        h = orch.health()
        print(f"Status:      {h['status']}")
        print(f"Base Mgr:    {h['base_manager']}")
        print(f"Budget:      {h['budget_pct']}% used")
        print(f"Snapshots:   {h['snapshot_count']}")
        print(f"Assemblies:  {h['assemblies']}")
        print(f"Rejections:  {h['rejections']}")
        if h["issues"]:
            print(f"Issues:      {'; '.join(h['issues'])}")
        print()
        print("Commands: stats, health, assemble [query], validate <text>,")
        print("          compress <text>, snapshot, snapshots, budget,")
        print("          quality [query], lanes, entities")
        orch.shutdown()
        return

    cmd = sys.argv[1].lower()

    if cmd == "stats":
        pprint.pprint(orch.get_stats())

    elif cmd == "health":
        pprint.pprint(orch.health())

    elif cmd == "assemble":
        query = " ".join(sys.argv[2:]) if len(sys.argv) > 2 else ""
        result = orch.assemble(query=query)
        print(f"Items: {result['metadata']['final_count']}")
        print(f"Tokens: {result['metadata']['final_tokens']}")
        print(f"Quality: {result['quality'].get('overall_score', '?')}")
        if result["metadata"]["validation_warnings"]:
            print("Warnings:")
            for w in result["metadata"]["validation_warnings"][:5]:
                print(f"  ⚠️  {w}")

    elif cmd == "validate":
        text = " ".join(sys.argv[2:]) if len(sys.argv) > 2 else ""
        if not text:
            print("Usage: context_orchestrator.py validate <text>")
        else:
            result = orch.validate_text(text)
            if result["valid"]:
                print("✅ No issues found")
            else:
                for e in result["errors"]:
                    print(f"  ❌ {e}")
            for w in result.get("warnings", []):
                print(f"  ⚠️  {w}")

    elif cmd == "compress":
        text = " ".join(sys.argv[2:]) if len(sys.argv) > 2 else ""
        if not text:
            print("Usage: context_orchestrator.py compress <text>")
        else:
            cr = orch.compress_text(text)
            print(f"Original:   {cr.original_tokens} tokens")
            print(f"Compressed: {cr.compressed_tokens} tokens")
            print(f"Ratio:      {cr.compression_ratio}")
            print(f"Kept:       {cr.sentences_kept} sentences")
            print(f"Dropped:    {cr.sentences_dropped} sentences")
            if cr.summary_text:
                print(f"\nSummary:\n{cr.summary_text[:500]}")

    elif cmd == "snapshot":
        desc = " ".join(sys.argv[2:]) if len(sys.argv) > 2 else "manual_cli"
        result = orch.snapshot(description=desc)
        if result:
            pprint.pprint(result)
        else:
            print("❌ Snapshot failed")

    elif cmd == "snapshots":
        snaps = orch.list_snapshots()
        if not snaps:
            print("No snapshots found")
        for s in snaps:
            print(
                f"  {s['snapshot_id']}  "
                f"items={s['item_count']}  "
                f"age={s['age_minutes']:.0f}min  "
                f"{s['description']}"
            )

    elif cmd == "budget":
        pprint.pprint(orch.budget_status())

    elif cmd == "quality":
        query = " ".join(sys.argv[2:]) if len(sys.argv) > 2 else ""
        pprint.pprint(orch.quality_report(query=query))

    elif cmd == "lanes":
        for lane_id in sorted(VALID_LANES):
            print(f"  {lane_id}: {LANE_LABELS.get(lane_id, '?')}")

    elif cmd == "entities":
        for ek, ev in CORRECT_ENTITIES.items():
            print(f"\n[{ek}]")
            for k, v in ev.items():
                print(f"  {k}: {v}")

    else:
        print(f"Unknown command: {cmd}")
        print("Run without arguments for usage.")

    orch.shutdown()


if __name__ == "__main__":
    _cli_main()
