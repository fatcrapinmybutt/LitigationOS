"""
LitigationOS Exception Hierarchy
==================================
Custom exception hierarchy following error-handling-patterns skill:
- ApplicationError base with structured context
- Domain-specific exceptions per subsystem
- Exception chaining via `raise ... from e`
- Circuit breaker + retry decorator patterns

Every exception carries: message, code, details dict, timestamp.
"""

from __future__ import annotations

import time
from datetime import datetime, timezone
from enum import Enum
from functools import wraps
from typing import Any, Callable, TypeVar

T = TypeVar("T")


# ─── Base Exception ──────────────────────────────────────────────

class ApplicationError(Exception):
    """Base exception for all LitigationOS errors."""

    def __init__(
        self,
        message: str,
        code: str | None = None,
        details: dict[str, Any] | None = None,
    ) -> None:
        super().__init__(message)
        self.code = code
        self.details = details or {}
        self.timestamp = datetime.now(timezone.utc)

    def to_dict(self) -> dict[str, Any]:
        return {
            "error": self.__class__.__name__,
            "message": str(self),
            "code": self.code,
            "details": self.details,
            "timestamp": self.timestamp.isoformat(),
        }


# ─── Lane Errors ─────────────────────────────────────────────────

class LaneError(ApplicationError):
    """Error scoped to a specific case lane."""

    def __init__(self, message: str, lane: str, **kwargs: Any) -> None:
        super().__init__(message, **kwargs)
        self.lane = lane
        self.details["lane"] = lane


class LaneCrossContaminationError(LaneError):
    """Evidence from wrong lane detected. Non-fatal, skip item."""

    def __init__(self, source_lane: str, target_lane: str, item_id: str = "") -> None:
        super().__init__(
            f"Cross-contamination: item from lane {source_lane} in lane {target_lane}",
            lane=target_lane,
            code="LANE_CROSS_CONTAMINATION",
            details={"source_lane": source_lane, "item_id": item_id},
        )


# ─── Filing Errors ───────────────────────────────────────────────

class FilingError(ApplicationError):
    """Error during filing assembly, validation, or export."""

    def __init__(self, message: str, vehicle: str = "", **kwargs: Any) -> None:
        super().__init__(message, code="FILING_ERROR", **kwargs)
        self.vehicle = vehicle
        if vehicle:
            self.details["vehicle"] = vehicle


class FilingValidationError(FilingError):
    """Filing failed pre-filing QA checks."""

    def __init__(self, message: str, failures: list[str] | None = None, **kwargs: Any) -> None:
        super().__init__(message, **kwargs)
        self.code = "FILING_VALIDATION_FAILED"
        self.failures = failures or []
        self.details["failures"] = self.failures


class PlaceholderError(FilingError):
    """Unresolved placeholder found in filing."""

    def __init__(self, placeholder: str, file_path: str = "", **kwargs: Any) -> None:
        super().__init__(
            f"Unresolved placeholder: {placeholder}",
            **kwargs,
        )
        self.code = "UNRESOLVED_PLACEHOLDER"
        self.details["placeholder"] = placeholder
        self.details["file_path"] = file_path


# ─── Evidence Errors ─────────────────────────────────────────────

class EvidenceError(ApplicationError):
    """Error during evidence processing or chain-of-custody."""

    def __init__(self, message: str, evidence_id: str = "", **kwargs: Any) -> None:
        super().__init__(message, code="EVIDENCE_ERROR", **kwargs)
        if evidence_id:
            self.details["evidence_id"] = evidence_id


class EvidenceChainBrokenError(EvidenceError):
    """Chain of custody has a gap."""

    def __init__(self, evidence_id: str, gap_description: str) -> None:
        super().__init__(
            f"Chain of custody broken for {evidence_id}: {gap_description}",
            evidence_id=evidence_id,
            code="EVIDENCE_CHAIN_BROKEN",
            details={"gap": gap_description},
        )


class CitationError(EvidenceError):
    """Citation is hallucinated, overruled, or malformed."""

    def __init__(self, citation: str, reason: str) -> None:
        super().__init__(
            f"Bad citation '{citation}': {reason}",
            code="CITATION_ERROR",
            details={"citation": citation, "reason": reason},
        )


# ─── Pipeline Errors ─────────────────────────────────────────────

class PipelineError(ApplicationError):
    """Error during pipeline phase execution."""

    def __init__(self, message: str, phase: str = "", **kwargs: Any) -> None:
        super().__init__(message, code="PIPELINE_ERROR", **kwargs)
        if phase:
            self.details["phase"] = phase


class PhaseFailedError(PipelineError):
    """A pipeline phase failed after retries."""

    def __init__(self, phase: str, attempt: int, original_error: str) -> None:
        super().__init__(
            f"Phase {phase} failed after {attempt} attempts: {original_error}",
            phase=phase,
            code="PHASE_FAILED",
            details={"attempt": attempt, "original_error": original_error},
        )


class CheckpointError(PipelineError):
    """Checkpoint save/restore failed."""
    pass


# ─── Database Errors ─────────────────────────────────────────────

class DatabaseError(ApplicationError):
    """Error during database operations."""

    def __init__(self, message: str, db_path: str = "", **kwargs: Any) -> None:
        super().__init__(message, code="DATABASE_ERROR", **kwargs)
        if db_path:
            self.details["db_path"] = db_path


class DatabaseLockedError(DatabaseError):
    """SQLite BUSY / database is locked."""

    def __init__(self, db_path: str = "", operation: str = "") -> None:
        super().__init__(
            f"Database locked during {operation}",
            db_path=db_path,
            code="DATABASE_LOCKED",
            details={"operation": operation},
        )


class SchemaError(DatabaseError):
    """Schema mismatch — expected column/table doesn't exist."""

    def __init__(self, table: str, expected: str, actual: str = "") -> None:
        super().__init__(
            f"Schema mismatch in {table}: expected {expected}, got {actual}",
            code="SCHEMA_MISMATCH",
            details={"table": table, "expected": expected, "actual": actual},
        )


# ─── Agent Errors ─────────────────────────────────────────────────

class AgentError(ApplicationError):
    """Error from an agent in the fleet."""

    def __init__(self, message: str, agent_id: str = "", **kwargs: Any) -> None:
        super().__init__(message, code="AGENT_ERROR", **kwargs)
        if agent_id:
            self.details["agent_id"] = agent_id


class AgentTimeoutError(AgentError):
    """Agent hit the 120s deadman switch."""

    def __init__(self, agent_id: str, elapsed_seconds: float) -> None:
        super().__init__(
            f"Agent {agent_id} timed out after {elapsed_seconds:.1f}s",
            agent_id=agent_id,
            code="AGENT_TIMEOUT",
            details={"elapsed_seconds": elapsed_seconds},
        )


class AgentCrashError(AgentError):
    """Agent returned CRASH status."""
    pass


# ─── External Service Errors ────────────────────────────────────

class ExternalServiceError(ApplicationError):
    """Error from an external service (MCP, file system, etc.)."""

    def __init__(self, message: str, service: str, **kwargs: Any) -> None:
        super().__init__(message, code="EXTERNAL_SERVICE_ERROR", **kwargs)
        self.service = service
        self.details["service"] = service


# ─── Convergence Errors ──────────────────────────────────────────

class ConvergenceError(ApplicationError):
    """Error during convergence cycle."""

    def __init__(self, message: str, cycle: int = 0, **kwargs: Any) -> None:
        super().__init__(message, code="CONVERGENCE_ERROR", **kwargs)
        if cycle:
            self.details["cycle"] = cycle


class QualityRegressionError(ConvergenceError):
    """Quality score dropped below threshold."""

    def __init__(self, previous: float, current: float, threshold: float = 70.0) -> None:
        super().__init__(
            f"Quality regression: {previous:.1f} → {current:.1f} (threshold: {threshold:.1f})",
            code="QUALITY_REGRESSION",
            details={
                "previous_score": previous,
                "current_score": current,
                "threshold": threshold,
            },
        )


# ═══════════════════════════════════════════════════════════════════
# RESILIENCE PATTERNS (from error-handling-patterns skill)
# ═══════════════════════════════════════════════════════════════════


# ─── Retry Decorator ──────────────────────────────────────────────

def retry(
    max_attempts: int = 3,
    backoff_factor: float = 2.0,
    exceptions: tuple[type[Exception], ...] = (Exception,),
    on_retry: Callable[[int, Exception], None] | None = None,
) -> Callable:
    """Retry with exponential backoff.

    Usage::

        @retry(max_attempts=3, exceptions=(DatabaseLockedError,))
        def write_to_db(data):
            ...
    """
    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        @wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> T:
            last_exception: Exception | None = None
            for attempt in range(1, max_attempts + 1):
                try:
                    return func(*args, **kwargs)
                except exceptions as e:
                    last_exception = e
                    if attempt < max_attempts:
                        sleep_time = backoff_factor ** (attempt - 1)
                        if on_retry:
                            on_retry(attempt, e)
                        time.sleep(sleep_time)
                    else:
                        raise
            raise last_exception  # type: ignore[misc]
        return wrapper
    return decorator


# ─── Circuit Breaker ──────────────────────────────────────────────

class CircuitState(Enum):
    CLOSED = "closed"
    OPEN = "open"
    HALF_OPEN = "half_open"


class CircuitBreaker:
    """Prevent cascading failures with circuit breaker pattern.

    Usage::

        breaker = CircuitBreaker(failure_threshold=5, timeout_seconds=60)
        result = breaker.call(lambda: risky_operation())
    """

    def __init__(
        self,
        failure_threshold: int = 5,
        timeout_seconds: float = 60.0,
        success_threshold: int = 2,
    ) -> None:
        self.failure_threshold = failure_threshold
        self.timeout_seconds = timeout_seconds
        self.success_threshold = success_threshold
        self.failure_count = 0
        self.success_count = 0
        self.state = CircuitState.CLOSED
        self.last_failure_time: float = 0.0

    def call(self, func: Callable[[], T]) -> T:
        if self.state == CircuitState.OPEN:
            if time.time() - self.last_failure_time > self.timeout_seconds:
                self.state = CircuitState.HALF_OPEN
                self.success_count = 0
            else:
                raise ExternalServiceError(
                    "Circuit breaker is OPEN — service unavailable",
                    service="circuit_breaker",
                )
        try:
            result = func()
            self._on_success()
            return result
        except Exception as e:
            self._on_failure()
            raise

    def _on_success(self) -> None:
        self.failure_count = 0
        if self.state == CircuitState.HALF_OPEN:
            self.success_count += 1
            if self.success_count >= self.success_threshold:
                self.state = CircuitState.CLOSED

    def _on_failure(self) -> None:
        self.failure_count += 1
        self.last_failure_time = time.time()
        if self.failure_count >= self.failure_threshold:
            self.state = CircuitState.OPEN

    def reset(self) -> None:
        self.state = CircuitState.CLOSED
        self.failure_count = 0
        self.success_count = 0


# ─── Batch Result (Partial Failure Handling) ─────────────────────

class BatchResult:
    """Track batch processing with partial failures.

    Usage::

        result = BatchResult()
        for item in items:
            try:
                output = process(item)
                result.add_success(item.id, output)
            except Exception as e:
                result.add_failure(item.id, e)
        print(result.summary())
    """

    def __init__(self) -> None:
        self.succeeded: dict[str, Any] = {}
        self.failed: dict[str, Exception] = {}

    def add_success(self, key: str, value: Any = None) -> None:
        self.succeeded[key] = value

    def add_failure(self, key: str, error: Exception) -> None:
        self.failed[key] = error

    @property
    def success_count(self) -> int:
        return len(self.succeeded)

    @property
    def failure_count(self) -> int:
        return len(self.failed)

    @property
    def total(self) -> int:
        return self.success_count + self.failure_count

    @property
    def all_succeeded(self) -> bool:
        return self.failure_count == 0

    def summary(self) -> str:
        return (
            f"BatchResult: {self.success_count}/{self.total} succeeded, "
            f"{self.failure_count} failed"
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "succeeded": list(self.succeeded.keys()),
            "failed": {k: str(v) for k, v in self.failed.items()},
            "success_count": self.success_count,
            "failure_count": self.failure_count,
        }


# ─── Graceful Degradation ───────────────────────────────────────

def with_fallback(
    primary: Callable[[], T],
    *fallbacks: Callable[[], T],
    default: T | None = None,
) -> T | None:
    """Try primary, then fallbacks in order. Return default if all fail.

    Usage::

        result = with_fallback(
            lambda: fetch_from_cache(key),
            lambda: fetch_from_db(key),
            lambda: fetch_from_backup(key),
            default=None,
        )
    """
    for func in (primary, *fallbacks):
        try:
            return func()
        except Exception:
            continue
    return default
