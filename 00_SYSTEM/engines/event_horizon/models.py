"""
EVENT HORIZON Δ∞ — Shared Data Models
=====================================
Dataclasses used by all 12 subsystems. Immutable where possible.
"""
from __future__ import annotations

import hashlib
import os
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Optional


# ---------------------------------------------------------------------------
# Enums
# ---------------------------------------------------------------------------
class Confidence(Enum):
    """Routing confidence tiers."""
    GREEN = "GREEN"    # ≥0.90 — auto-route
    YELLOW = "YELLOW"  # 0.80–0.89 — route + log
    ORANGE = "ORANGE"  # 0.60–0.79 — route + flag for review
    RED = "RED"        # <0.60 — triage queue

    @classmethod
    def from_score(cls, score: float) -> "Confidence":
        if score >= 0.90:
            return cls.GREEN
        elif score >= 0.80:
            return cls.YELLOW
        elif score >= 0.60:
            return cls.ORANGE
        return cls.RED


class RoutingTier(Enum):
    """8-tier routing priority (from agentic_router_v2)."""
    T0_JUNK = 0
    T1_EVIDENCE = 1
    T2_COURT = 2
    T3_FILING = 3
    T4_ANALYSIS = 4
    T5_AUTHORITY = 5
    T6_BULK = 6
    T7_FALLBACK = 7


class QualityGate(Enum):
    """7 ELYSIUM quality gates."""
    ZERO_LOSS = "zero_loss"
    ACCURACY = "accuracy"
    DISTRIBUTION = "distribution"
    EVIDENCE_INTEGRITY = "evidence_integrity"
    PROTECTED_ZONES = "protected_zones"
    CANONICAL_COMPLIANCE = "canonical_compliance"
    DEDUP = "dedup"


class ConvergenceState(Enum):
    """ESCHATON convergence levels."""
    CHAOS = "CHAOS"          # <30% sorted
    FORMING = "FORMING"      # 30-50%
    STORMING = "STORMING"    # 50-70%
    NORMING = "NORMING"      # 70-90%
    ESCHATON = "ESCHATON"    # ≥90% — convergence achieved


# ---------------------------------------------------------------------------
# Core dataclasses
# ---------------------------------------------------------------------------
@dataclass
class FileManifest:
    """GENESIS output — profile of a single file."""
    path: Path
    name: str
    extension: str
    size_bytes: int
    modified: datetime
    content_hash: Optional[str] = None  # SHA-256, computed on demand
    content_sample: Optional[str] = None  # First 2KB for content-based routing
    is_protected: bool = False

    @classmethod
    def from_path(cls, p: Path, sample_size: int = 2048) -> "FileManifest":
        stat = p.stat()
        sample = None
        if p.suffix.lower() in (".txt", ".md", ".csv", ".json", ".jsonl",
                                  ".py", ".js", ".html", ".htm", ".rst",
                                  ".sql", ".xml", ".toml", ".yaml", ".yml",
                                  ".log", ".bat", ".ps1", ".sh", ".cfg"):
            try:
                with open(p, "r", encoding="utf-8", errors="replace") as f:
                    sample = f.read(sample_size)
            except Exception:
                pass
        return cls(
            path=p,
            name=p.name,
            extension=p.suffix.lower(),
            size_bytes=stat.st_size,
            modified=datetime.fromtimestamp(stat.st_mtime),
            content_sample=sample,
        )

    def compute_hash(self) -> str:
        """Compute SHA-256 (lazy, cached)."""
        if self.content_hash:
            return self.content_hash
        h = hashlib.sha256()
        try:
            with open(self.path, "rb") as f:
                for chunk in iter(lambda: f.read(65536), b""):
                    h.update(chunk)
            self.content_hash = h.hexdigest()
        except Exception:
            self.content_hash = "ERROR"
        return self.content_hash


@dataclass
class RoutingDecision:
    """ORACLE output — where a file should go and why."""
    source: Path
    destination: Path
    tier: RoutingTier
    confidence: Confidence
    score: float
    reason: str
    signals: list[str] = field(default_factory=list)


@dataclass
class MoveRecord:
    """PROMETHEAN output — record of an actual file move."""
    source: Path
    destination: Path
    timestamp: datetime = field(default_factory=datetime.now)
    success: bool = True
    error: Optional[str] = None
    rollback_path: Optional[Path] = None  # Original location for undo


@dataclass
class QualityResult:
    """ELYSIUM output — result of a single quality gate check."""
    gate: QualityGate
    passed: bool
    score: float  # 0.0–1.0
    details: str
    violations: list[str] = field(default_factory=list)


@dataclass
class QualityReport:
    """ELYSIUM output — aggregate report across all gates."""
    results: list[QualityResult] = field(default_factory=list)
    overall_score: float = 0.0
    passed: bool = False

    @property
    def gates_passed(self) -> int:
        return sum(1 for r in self.results if r.passed)

    @property
    def gates_total(self) -> int:
        return len(self.results)

    def compute(self):
        if not self.results:
            return
        self.overall_score = sum(r.score for r in self.results) / len(self.results)
        self.passed = all(r.passed for r in self.results)


@dataclass
class RoutingPlan:
    """ORACLE output — complete routing plan for a zone."""
    zone: str
    decisions: list[RoutingDecision] = field(default_factory=list)
    skipped: list[tuple[Path, str]] = field(default_factory=list)  # (path, reason)
    stats: dict = field(default_factory=dict)

    @property
    def total(self) -> int:
        return len(self.decisions) + len(self.skipped)

    @property
    def routable(self) -> int:
        return len(self.decisions)

    def by_confidence(self) -> dict[Confidence, list[RoutingDecision]]:
        result: dict[Confidence, list[RoutingDecision]] = {}
        for d in self.decisions:
            result.setdefault(d.confidence, []).append(d)
        return result


@dataclass
class MoveMetrics:
    """PROMETHEAN output — aggregate metrics from an execution run."""
    total_attempted: int = 0
    success_count: int = 0
    error_count: int = 0
    bytes_moved: int = 0
    moves: list[MoveRecord] = field(default_factory=list)
    errors: list[MoveRecord] = field(default_factory=list)

    @property
    def total_moved(self) -> int:
        return self.success_count

    @property
    def success_rate(self) -> float:
        if self.total_attempted == 0:
            return 1.0
        return self.success_count / self.total_attempted


@dataclass
class EmergenceEvent:
    """EVENT HORIZON output — a discovered emergent pattern."""
    pattern_type: str
    description: str
    novelty_score: float  # 0.0–1.0
    affected_files: int
    suggested_action: Optional[str] = None


@dataclass
class ConvergenceScore:
    """ESCHATON output — how close we are to completion."""
    state: ConvergenceState
    score: float  # 0.0–1.0
    files_sorted: int
    files_total: int
    root_files: int  # should approach 0
    bloated_zones: list[str] = field(default_factory=list)
    cycle: int = 1

    @property
    def pct(self) -> float:
        if self.files_total == 0:
            return 1.0
        return self.files_sorted / self.files_total


# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------
CANONICAL_FOLDERS = [
    "00_SYSTEM", "01_EVIDENCE", "02_AUTHORITY", "03_COURT",
    "04_ANALYSIS", "05_FILINGS", "06_DATA", "07_CODE",
    "08_MEDIA", "09_REFERENCE", "10_EXTERNAL", "11_ARCHIVES",
    "12_WORKSPACE",
]

PROTECTED_DIRS = {
    ".git", ".github", ".agents", ".claude", ".venv", ".vscode",
    "00_SYSTEM", "__pycache__", "node_modules", "pytools_venv",
    "site-packages", "logs",
}

ALLOWED_ROOT_FILES = {
    "_CANON.md", "README.md", "pyproject.toml", "requirements.txt",
    "mcp.json", ".gitignore", "litigationos.config.jsonc",
    "master.code-workspace", "litigation_context.db", "litigationos.db",
}

JUNK_EXTENSIONS = {
    ".tmp", ".bak", ".swp", ".swo", ".pyc", ".pyo",
    ".DS_Store", ".thumbs.db", "desktop.ini",
}

REPO_ROOT = Path(os.environ.get("LITIGATIONOS_ROOT", str(Path(__file__).resolve().parents[3])))
