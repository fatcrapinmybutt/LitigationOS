# -*- coding: utf-8 -*-
"""
skill_evolver.py — Skill Auto-Evolution Engine
================================================
Analyzes skill module performance, generates evolution recommendations,
versions skill snapshots, and tracks improvement metrics over time.

Capabilities:
  - Scan skill directories and catalog all skill modules (engines/ + skills/)
  - Analyze each skill: LOC, functions, error handling, docstrings, complexity
  - Track invocation metrics via DB table ``skill_evolution_log``
  - Score skills on completeness, error handling, documentation, performance
  - Generate evolution recommendations (what to add, fix, improve)
  - Create versioned snapshots before/after evolution
  - Track improvement over time with trend analysis
  - Export evolution report as JSON

14 MI Domain Skills tracked:
  - skill_best_interest.py      (12 BIF factors, MCL 722.23)
  - skill_ppo_detector.py       (PPO weaponization patterns)
  - skill_bias_quantifier.py    (judicial bias scoring)
  - skill_deadline_sentinel.py  (deadline monitoring & alerts)
  - skill_mcl_library.py        (MCL statute lookup)
  - skill_mcr_encyclopedia.py   (MCR rule lookup)
  - skill_landlord_tenant.py    (housing / landlord-tenant law)
  - skill_scao_forms.py         (SCAO court form catalog)
  - alienation_quantifier.py    (parental alienation scoring)
  - skill_authority_validator.py (authority chain validation)
  - skill_filing_tracker.py     (filing status tracking)
  - skill_convergence_engine.py (cross-lane convergence)
  - skill_timeline_builder.py   (event timeline construction)
  - skill_torts_claims.py       (tort claim analysis)

Zero external dependencies. Local-only.
"""

from __future__ import annotations

import ast
import hashlib
import inspect
import json
import logging
import os
import re
import sqlite3
import textwrap
import time
from collections import Counter
from dataclasses import dataclass, field, asdict
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple

logger = logging.getLogger("legal_ai.skill_evolver")

_HERE = Path(__file__).resolve().parent
_SYSTEM = _HERE.parent                    # 00_SYSTEM
_REPO = _SYSTEM.parent                    # LitigationOS root
_DB_PATH = _REPO / "litigation_context.db"
_ENGINES_DIR = _SYSTEM / "engines"
_SKILLS_DIR = _SYSTEM / "skills"

# ---------------------------------------------------------------------------
# DB DDL
# ---------------------------------------------------------------------------

_EVOLUTION_LOG_DDL = """\
CREATE TABLE IF NOT EXISTS skill_evolution_log (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    skill_name TEXT NOT NULL,
    version TEXT NOT NULL,
    evolved_at TEXT NOT NULL,
    score_before REAL,
    score_after REAL,
    changes TEXT,
    metrics TEXT
)"""

# ---------------------------------------------------------------------------
# Dataclasses
# ---------------------------------------------------------------------------


@dataclass
class SkillMetrics:
    """Performance and quality metrics for a single skill module."""

    skill_name: str
    module_path: str
    invocation_count: int = 0
    success_rate: float = 1.0
    avg_execution_time_ms: float = 0.0
    error_count: int = 0
    last_error: Optional[str] = None
    last_invoked: str = ""
    output_quality_score: float = 0.0
    coverage_score: float = 0.0
    lines_of_code: int = 0
    function_count: int = 0
    class_count: int = 0
    docstring_coverage: float = 0.0
    error_handling_score: float = 0.0
    has_get_stats: bool = False
    has_to_dict: bool = False
    has_main_guard: bool = False
    complexity_estimate: int = 0
    sha256: str = ""

    def to_dict(self) -> dict:
        return asdict(self)


@dataclass
class EvolutionRecord:
    """Record of a single skill evolution event."""

    skill_name: str
    version: str = "v1.0"
    evolved_at: str = ""
    changes: List[str] = field(default_factory=list)
    before_score: float = 0.0
    after_score: float = 0.0
    improvement_pct: float = 0.0

    def to_dict(self) -> dict:
        return asdict(self)


@dataclass
class EvolutionReport:
    """Complete evolution analysis report for all tracked skills."""

    generated_at: str = ""
    total_skills: int = 0
    evolved_count: int = 0
    improvement_avg: float = 0.0
    skills_needing_evolution: List[str] = field(default_factory=list)
    top_performers: List[SkillMetrics] = field(default_factory=list)
    bottom_performers: List[SkillMetrics] = field(default_factory=list)
    evolution_history: List[EvolutionRecord] = field(default_factory=list)
    recommendations: List[str] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {
            "generated_at": self.generated_at,
            "total_skills": self.total_skills,
            "evolved_count": self.evolved_count,
            "improvement_avg": round(self.improvement_avg, 2),
            "skills_needing_evolution": self.skills_needing_evolution,
            "top_performers": [m.to_dict() for m in self.top_performers],
            "bottom_performers": [m.to_dict() for m in self.bottom_performers],
            "evolution_history": [r.to_dict() for r in self.evolution_history],
            "recommendations": self.recommendations,
        }


# ---------------------------------------------------------------------------
# Known MI domain skills
# ---------------------------------------------------------------------------

MI_DOMAIN_SKILLS: List[Dict[str, str]] = [
    {"name": "skill_best_interest", "file": "skill_best_interest.py",
     "domain": "custody", "description": "12 Best-Interest Factors (MCL 722.23)"},
    {"name": "skill_ppo_detector", "file": "skill_ppo_detector.py",
     "domain": "ppo", "description": "PPO weaponization pattern detection"},
    {"name": "skill_bias_quantifier", "file": "skill_bias_quantifier.py",
     "domain": "judicial", "description": "Judicial bias scoring engine"},
    {"name": "skill_deadline_sentinel", "file": "skill_deadline_sentinel.py",
     "domain": "deadlines", "description": "Deadline monitoring & multi-tier alerts"},
    {"name": "skill_mcl_library", "file": "skill_mcl_library.py",
     "domain": "statutes", "description": "MCL statute lookup & cross-reference"},
    {"name": "skill_mcr_encyclopedia", "file": "skill_mcr_encyclopedia.py",
     "domain": "rules", "description": "MCR rule lookup & interpretation"},
    {"name": "skill_landlord_tenant", "file": "skill_landlord_tenant.py",
     "domain": "housing", "description": "Landlord-tenant / housing law"},
    {"name": "skill_scao_forms", "file": "skill_scao_forms.py",
     "domain": "forms", "description": "SCAO court form catalog & lookup"},
    {"name": "alienation_quantifier", "file": "alienation_quantifier.py",
     "domain": "custody", "description": "Parental alienation scoring"},
    {"name": "skill_authority_validator", "file": "skill_authority_validator.py",
     "domain": "authority", "description": "Authority chain validation"},
    {"name": "skill_filing_tracker", "file": "skill_filing_tracker.py",
     "domain": "filing", "description": "Filing status tracking"},
    {"name": "skill_convergence_engine", "file": "skill_convergence_engine.py",
     "domain": "convergence", "description": "Cross-lane convergence engine"},
    {"name": "skill_timeline_builder", "file": "skill_timeline_builder.py",
     "domain": "timeline", "description": "Event timeline construction"},
    {"name": "skill_torts_claims", "file": "skill_torts_claims.py",
     "domain": "torts", "description": "Tort claim analysis"},
]


# ---------------------------------------------------------------------------
# AST Helpers
# ---------------------------------------------------------------------------


def _parse_module_ast(source: str) -> Optional[ast.Module]:
    """Parse Python source into an AST, returning None on syntax errors."""
    try:
        return ast.parse(source)
    except SyntaxError as exc:
        logger.debug("AST parse failed: %s", exc)
        return None


def _count_functions(tree: ast.Module) -> int:
    """Count top-level and method function definitions."""
    return sum(1 for node in ast.walk(tree) if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)))


def _count_classes(tree: ast.Module) -> int:
    """Count class definitions."""
    return sum(1 for node in ast.walk(tree) if isinstance(node, ast.ClassDef))


def _count_try_except(tree: ast.Module) -> int:
    """Count try/except blocks (error handling indicator)."""
    return sum(1 for node in ast.walk(tree) if isinstance(node, ast.Try))


def _count_docstrings(tree: ast.Module) -> Tuple[int, int]:
    """Return (documented_count, total_count) for functions and classes."""
    total = 0
    documented = 0
    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            total += 1
            if (node.body
                    and isinstance(node.body[0], ast.Expr)
                    and isinstance(node.body[0].value, (ast.Constant, ast.Str))):
                documented += 1
    return documented, total


def _has_name(tree: ast.Module, name: str) -> bool:
    """Check if a function or method with the given name exists."""
    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) and node.name == name:
            return True
    return False


def _has_main_guard(source: str) -> bool:
    """Check for if __name__ == '__main__' guard."""
    return bool(re.search(r'if\s+__name__\s*==\s*["\']__main__["\']', source))


def _estimate_complexity(tree: ast.Module) -> int:
    """Rough cyclomatic complexity estimate (branches + loops)."""
    score = 0
    for node in ast.walk(tree):
        if isinstance(node, (ast.If, ast.IfExp)):
            score += 1
        elif isinstance(node, (ast.For, ast.While)):
            score += 1
        elif isinstance(node, ast.BoolOp):
            score += len(node.values) - 1
        elif isinstance(node, ast.Try):
            score += len(node.handlers)
    return score


def _file_sha256(path: Path) -> str:
    """Compute SHA-256 hash of a file."""
    h = hashlib.sha256()
    try:
        with open(path, "rb") as f:
            for chunk in iter(lambda: f.read(8192), b""):
                h.update(chunk)
        return h.hexdigest()
    except OSError:
        return ""


# ---------------------------------------------------------------------------
# SkillEvolver
# ---------------------------------------------------------------------------


class SkillEvolver:
    """Auto-analyze and evolve litigation skill modules.

    Scans the engines/ and skills/ directories for skill modules, performs
    static analysis via AST parsing, scores them on quality dimensions,
    and tracks evolution over time in the central DB.
    """

    # Quality dimension weights (sum to 1.0)
    _WEIGHTS = {
        "documentation": 0.15,
        "error_handling": 0.20,
        "completeness": 0.20,
        "structure": 0.15,
        "complexity": 0.10,
        "interface": 0.10,
        "size": 0.10,
    }

    def __init__(
        self,
        db_path: Optional[str] = None,
        engines_dir: Optional[str] = None,
        skills_dir: Optional[str] = None,
    ):
        self._db_path = Path(db_path) if db_path else _DB_PATH
        self._engines_dir = Path(engines_dir) if engines_dir else _ENGINES_DIR
        self._skills_dir = Path(skills_dir) if skills_dir else _SKILLS_DIR
        self._scans_run = 0
        self._evolutions_recorded = 0
        self._cache: Dict[str, SkillMetrics] = {}

        self._ensure_tables()

    # -- DB helpers ---------------------------------------------------------

    def _open_db(self) -> sqlite3.Connection:
        """Open a DB connection with required PRAGMAs."""
        conn = sqlite3.connect(str(self._db_path))
        conn.execute("PRAGMA busy_timeout = 60000")
        conn.execute("PRAGMA journal_mode = WAL")
        conn.execute("PRAGMA cache_size = -32000")
        conn.execute("PRAGMA temp_store = MEMORY")
        conn.execute("PRAGMA synchronous = NORMAL")
        conn.row_factory = sqlite3.Row
        return conn

    def _ensure_tables(self) -> None:
        """Create skill_evolution_log table if it does not exist."""
        if not self._db_path.exists():
            logger.warning("DB not found at %s — table creation deferred", self._db_path)
            return
        try:
            conn = self._open_db()
            conn.execute(_EVOLUTION_LOG_DDL)
            conn.commit()
            conn.close()
            logger.debug("skill_evolution_log table ensured")
        except sqlite3.Error as exc:
            logger.warning("Could not ensure evolution tables: %s", exc)

    # -- Scanning -----------------------------------------------------------

    def _discover_skill_files(self) -> List[Path]:
        """Find all skill module files across engines/ and skills/ dirs."""
        found: List[Path] = []
        for directory in (self._engines_dir, self._skills_dir):
            if not directory.is_dir():
                logger.debug("Skill directory not found: %s", directory)
                continue
            for py_file in sorted(directory.glob("*.py")):
                name = py_file.stem
                if name.startswith("__"):
                    continue
                if name.startswith("skill_") or name in {
                    "alienation_quantifier",
                    "best_interest_engine",
                }:
                    found.append(py_file)
        return found

    def _is_known_skill(self, name: str) -> bool:
        """Check if a skill name is in the MI domain skill registry."""
        return any(s["name"] == name or s["file"] == name + ".py" for s in MI_DOMAIN_SKILLS)

    def scan_skills(self, skill_dir: Optional[str] = None) -> List[SkillMetrics]:
        """Scan skill directories and return metrics for each discovered module.

        Args:
            skill_dir: Optional override directory to scan instead of defaults.

        Returns:
            List of SkillMetrics, one per discovered skill module.
        """
        self._scans_run += 1
        start = time.monotonic()

        if skill_dir:
            paths = sorted(Path(skill_dir).glob("skill_*.py"))
            paths += sorted(Path(skill_dir).glob("alienation_quantifier.py"))
        else:
            paths = self._discover_skill_files()

        results: List[SkillMetrics] = []
        for p in paths:
            try:
                metrics = self.analyze_skill(str(p))
                results.append(metrics)
                self._cache[metrics.skill_name] = metrics
            except Exception as exc:
                logger.warning("Failed to analyze %s: %s", p.name, exc)
                results.append(SkillMetrics(
                    skill_name=p.stem,
                    module_path=str(p),
                    last_error=str(exc),
                ))

        elapsed = (time.monotonic() - start) * 1000
        logger.info("Scanned %d skills in %.1f ms", len(results), elapsed)
        return results

    def analyze_skill(self, skill_path: str) -> SkillMetrics:
        """Perform deep static analysis on a single skill module.

        Args:
            skill_path: Filesystem path to the .py skill file.

        Returns:
            SkillMetrics with all analysis fields populated.
        """
        path = Path(skill_path).resolve()
        if not path.exists():
            raise FileNotFoundError(f"Skill not found: {path}")

        source = path.read_text(encoding="utf-8", errors="replace")
        lines = source.splitlines()
        loc = len([ln for ln in lines if ln.strip() and not ln.strip().startswith("#")])

        tree = _parse_module_ast(source)
        if tree is None:
            return SkillMetrics(
                skill_name=path.stem,
                module_path=str(path),
                lines_of_code=loc,
                last_error="SyntaxError — could not parse AST",
                sha256=_file_sha256(path),
            )

        func_count = _count_functions(tree)
        class_count = _count_classes(tree)
        try_count = _count_try_except(tree)
        documented, total_defs = _count_docstrings(tree)
        docstring_pct = (documented / total_defs * 100) if total_defs > 0 else 0.0
        error_handling_pct = min(100.0, (try_count / max(func_count, 1)) * 100)
        complexity = _estimate_complexity(tree)

        has_stats = _has_name(tree, "get_stats")
        has_todict = _has_name(tree, "to_dict")
        has_main = _has_main_guard(source)

        # Coverage score: how many expected interface elements exist
        expected_interfaces = ["get_stats", "to_dict", "__init__"]
        found_interfaces = sum(1 for name in expected_interfaces if _has_name(tree, name))
        coverage = (found_interfaces / len(expected_interfaces)) * 100

        return SkillMetrics(
            skill_name=path.stem,
            module_path=str(path),
            lines_of_code=loc,
            function_count=func_count,
            class_count=class_count,
            docstring_coverage=round(docstring_pct, 1),
            error_handling_score=round(error_handling_pct, 1),
            has_get_stats=has_stats,
            has_to_dict=has_todict,
            has_main_guard=has_main,
            complexity_estimate=complexity,
            coverage_score=round(coverage, 1),
            sha256=_file_sha256(path),
        )

    # -- Scoring ------------------------------------------------------------

    def score_skill(self, metrics: SkillMetrics) -> float:
        """Compute a composite quality score (0-100) for a skill module.

        Weighted dimensions:
          - documentation (15%): docstring coverage
          - error_handling (20%): try/except density
          - completeness (20%): coverage_score + expected interfaces
          - structure (15%): classes, functions, organization
          - complexity (10%): penalize excessive complexity
          - interface (10%): get_stats, to_dict, __main__
          - size (10%): reward adequate LOC, penalize extremes
        """
        scores: Dict[str, float] = {}

        # Documentation: docstring coverage 0-100
        scores["documentation"] = min(100.0, metrics.docstring_coverage)

        # Error handling: score 0-100
        scores["error_handling"] = min(100.0, metrics.error_handling_score)

        # Completeness: coverage of expected interfaces
        scores["completeness"] = metrics.coverage_score

        # Structure: reward having classes + multiple functions
        structure = 0.0
        if metrics.class_count >= 1:
            structure += 40.0
        if metrics.function_count >= 3:
            structure += 30.0
        if metrics.function_count >= 6:
            structure += 20.0
        if metrics.has_main_guard:
            structure += 10.0
        scores["structure"] = min(100.0, structure)

        # Complexity: moderate is good, excessive is bad
        if metrics.complexity_estimate == 0:
            scores["complexity"] = 30.0  # trivial
        elif metrics.complexity_estimate <= 20:
            scores["complexity"] = 100.0
        elif metrics.complexity_estimate <= 50:
            scores["complexity"] = 80.0
        elif metrics.complexity_estimate <= 100:
            scores["complexity"] = 60.0
        else:
            scores["complexity"] = max(20.0, 100.0 - (metrics.complexity_estimate - 100))

        # Interface: get_stats + to_dict + main guard
        iface_score = 0.0
        if metrics.has_get_stats:
            iface_score += 40.0
        if metrics.has_to_dict:
            iface_score += 40.0
        if metrics.has_main_guard:
            iface_score += 20.0
        scores["interface"] = iface_score

        # Size: reward 100-800 LOC, penalize extremes
        loc = metrics.lines_of_code
        if loc < 20:
            scores["size"] = 10.0
        elif loc < 50:
            scores["size"] = 40.0
        elif loc < 100:
            scores["size"] = 70.0
        elif loc <= 800:
            scores["size"] = 100.0
        elif loc <= 1500:
            scores["size"] = 80.0
        else:
            scores["size"] = 60.0

        # Weighted composite
        total = sum(scores[dim] * self._WEIGHTS[dim] for dim in self._WEIGHTS)
        return round(min(100.0, max(0.0, total)), 1)

    # -- Evolution targets --------------------------------------------------

    def identify_evolution_targets(self) -> List[Tuple[str, List[str]]]:
        """Identify skills that need improvement and what to fix.

        Returns:
            List of (skill_name, [recommended_improvements]).
        """
        if not self._cache:
            self.scan_skills()

        targets: List[Tuple[str, List[str]]] = []

        for name, metrics in self._cache.items():
            improvements: List[str] = []
            score = self.score_skill(metrics)

            if metrics.docstring_coverage < 50:
                improvements.append(
                    f"Add docstrings — only {metrics.docstring_coverage:.0f}% coverage"
                )
            if metrics.error_handling_score < 30:
                improvements.append(
                    "Add try/except error handling to key functions"
                )
            if not metrics.has_get_stats:
                improvements.append("Add get_stats() -> dict method for observability")
            if not metrics.has_to_dict:
                improvements.append("Add to_dict() methods to dataclasses")
            if not metrics.has_main_guard:
                improvements.append("Add if __name__ == '__main__' guard for CLI usage")
            if metrics.class_count == 0:
                improvements.append("Refactor into a class with clear interface")
            if metrics.lines_of_code < 50:
                improvements.append(
                    f"Module is thin ({metrics.lines_of_code} LOC) — expand domain coverage"
                )
            if metrics.function_count < 3:
                improvements.append(
                    "Add more functions — module has limited functionality"
                )
            if metrics.complexity_estimate > 100:
                improvements.append(
                    f"Reduce complexity ({metrics.complexity_estimate}) — extract helpers"
                )
            if metrics.last_error:
                improvements.append(f"Fix error: {metrics.last_error}")

            # Include skills scoring below 60 or with any improvements
            if improvements or score < 60:
                if not improvements:
                    improvements.append(f"General quality improvement needed (score: {score})")
                targets.append((name, improvements))

        # Sort by most improvements needed
        targets.sort(key=lambda t: len(t[1]), reverse=True)
        return targets

    # -- Evolution recording ------------------------------------------------

    def evolve_skill(self, skill_name: str, changes: List[str]) -> EvolutionRecord:
        """Record an evolution event for a skill.

        Args:
            skill_name: Name of the skill that was evolved.
            changes: List of changes made during evolution.

        Returns:
            EvolutionRecord with before/after scores.
        """
        now = datetime.now().isoformat()

        # Determine before score
        before_score = 0.0
        if skill_name in self._cache:
            before_score = self.score_skill(self._cache[skill_name])

        # Re-scan to get after score
        after_score = before_score
        for path in self._discover_skill_files():
            if path.stem == skill_name:
                try:
                    new_metrics = self.analyze_skill(str(path))
                    after_score = self.score_skill(new_metrics)
                    self._cache[skill_name] = new_metrics
                except Exception as exc:
                    logger.warning("Could not re-analyze %s: %s", skill_name, exc)
                break

        improvement = 0.0
        if before_score > 0:
            improvement = ((after_score - before_score) / before_score) * 100

        # Compute version from history
        version = self._next_version(skill_name)

        record = EvolutionRecord(
            skill_name=skill_name,
            version=version,
            evolved_at=now,
            changes=changes,
            before_score=round(before_score, 1),
            after_score=round(after_score, 1),
            improvement_pct=round(improvement, 1),
        )

        # Persist to DB
        self._persist_evolution(record)
        self._evolutions_recorded += 1
        logger.info(
            "Evolved %s %s: %.1f → %.1f (%+.1f%%)",
            skill_name, version, before_score, after_score, improvement,
        )
        return record

    def _next_version(self, skill_name: str) -> str:
        """Determine the next version string for a skill."""
        history = self.get_evolution_history(skill_name)
        if not history:
            return "v1.0"
        last = history[-1].version
        match = re.match(r"v(\d+)\.(\d+)", last)
        if match:
            major, minor = int(match.group(1)), int(match.group(2))
            return f"v{major}.{minor + 1}"
        return "v1.0"

    def _persist_evolution(self, record: EvolutionRecord) -> None:
        """Write an evolution record to the DB."""
        if not self._db_path.exists():
            logger.warning("DB not found — evolution record not persisted")
            return
        try:
            conn = self._open_db()
            conn.execute(
                """INSERT INTO skill_evolution_log
                   (skill_name, version, evolved_at, score_before, score_after, changes, metrics)
                   VALUES (?, ?, ?, ?, ?, ?, ?)""",
                (
                    record.skill_name,
                    record.version,
                    record.evolved_at,
                    record.before_score,
                    record.after_score,
                    json.dumps(record.changes),
                    json.dumps(self._cache.get(record.skill_name, SkillMetrics(
                        skill_name=record.skill_name, module_path="",
                    )).to_dict()),
                ),
            )
            conn.commit()
            conn.close()
        except sqlite3.Error as exc:
            logger.warning("Could not persist evolution record: %s", exc)

    # -- History retrieval --------------------------------------------------

    def get_evolution_history(self, skill_name: Optional[str] = None) -> List[EvolutionRecord]:
        """Retrieve evolution history from the DB.

        Args:
            skill_name: Filter to a specific skill. None returns all.

        Returns:
            List of EvolutionRecord in chronological order.
        """
        if not self._db_path.exists():
            return []
        records: List[EvolutionRecord] = []
        try:
            conn = self._open_db()
            if skill_name:
                rows = conn.execute(
                    "SELECT skill_name, version, evolved_at, score_before, score_after, changes "
                    "FROM skill_evolution_log WHERE skill_name = ? ORDER BY evolved_at",
                    (skill_name,),
                ).fetchall()
            else:
                rows = conn.execute(
                    "SELECT skill_name, version, evolved_at, score_before, score_after, changes "
                    "FROM skill_evolution_log ORDER BY evolved_at"
                ).fetchall()
            conn.close()

            for row in rows:
                changes = []
                try:
                    changes = json.loads(row["changes"]) if row["changes"] else []
                except (json.JSONDecodeError, TypeError):
                    changes = [str(row["changes"])]

                before = float(row["score_before"] or 0)
                after = float(row["score_after"] or 0)
                improvement = ((after - before) / before * 100) if before > 0 else 0.0

                records.append(EvolutionRecord(
                    skill_name=row["skill_name"],
                    version=row["version"],
                    evolved_at=row["evolved_at"],
                    changes=changes,
                    before_score=before,
                    after_score=after,
                    improvement_pct=round(improvement, 1),
                ))
        except sqlite3.Error as exc:
            logger.warning("Could not read evolution history: %s", exc)
        return records

    # -- Trend analysis -----------------------------------------------------

    def _compute_trend(self, skill_name: str) -> Dict[str, Any]:
        """Compute improvement trend for a skill over its evolution history."""
        history = self.get_evolution_history(skill_name)
        if not history:
            return {"trend": "no_data", "versions": 0}

        scores = [r.after_score for r in history]
        if len(scores) < 2:
            return {
                "trend": "single_version",
                "versions": 1,
                "current_score": scores[0],
            }

        # Simple linear trend: positive = improving
        deltas = [scores[i] - scores[i - 1] for i in range(1, len(scores))]
        avg_delta = sum(deltas) / len(deltas)

        if avg_delta > 1.0:
            trend = "improving"
        elif avg_delta < -1.0:
            trend = "declining"
        else:
            trend = "stable"

        return {
            "trend": trend,
            "versions": len(scores),
            "current_score": scores[-1],
            "avg_improvement_per_version": round(avg_delta, 2),
            "first_score": scores[0],
            "latest_score": scores[-1],
            "total_improvement": round(scores[-1] - scores[0], 1),
        }

    # -- Report generation --------------------------------------------------

    def generate_report(self) -> EvolutionReport:
        """Generate a comprehensive evolution report for all tracked skills.

        Returns:
            EvolutionReport with scored rankings, history, and recommendations.
        """
        if not self._cache:
            self.scan_skills()

        # Score all skills
        scored: List[Tuple[str, SkillMetrics, float]] = []
        for name, metrics in self._cache.items():
            score = self.score_skill(metrics)
            metrics.output_quality_score = score
            scored.append((name, metrics, score))

        scored.sort(key=lambda t: t[2], reverse=True)

        # Top/bottom performers
        top_n = min(5, len(scored))
        top = [s[1] for s in scored[:top_n]]
        bottom = [s[1] for s in scored[-top_n:]] if len(scored) > top_n else []

        # Evolution targets
        targets = self.identify_evolution_targets()
        needing_evolution = [t[0] for t in targets]

        # Full history
        history = self.get_evolution_history()

        # Recommendations
        recommendations = self._build_recommendations(scored, targets)

        # Compute average improvement from history
        improvements = [r.improvement_pct for r in history if r.improvement_pct != 0]
        avg_improvement = (sum(improvements) / len(improvements)) if improvements else 0.0

        report = EvolutionReport(
            generated_at=datetime.now().isoformat(),
            total_skills=len(scored),
            evolved_count=len(history),
            improvement_avg=avg_improvement,
            skills_needing_evolution=needing_evolution,
            top_performers=top,
            bottom_performers=bottom,
            evolution_history=history,
            recommendations=recommendations,
        )

        logger.info(
            "Report: %d skills, %d evolved, %d needing evolution",
            report.total_skills, report.evolved_count, len(needing_evolution),
        )
        return report

    def _build_recommendations(
        self,
        scored: List[Tuple[str, SkillMetrics, float]],
        targets: List[Tuple[str, List[str]]],
    ) -> List[str]:
        """Build prioritized recommendations from analysis."""
        recs: List[str] = []

        # Critical issues first
        for name, improvements in targets:
            if any("error" in imp.lower() or "syntax" in imp.lower() for imp in improvements):
                recs.append(f"CRITICAL: {name} has errors — fix immediately")

        # Missing interfaces
        missing_stats = [n for n, m in self._cache.items() if not m.has_get_stats]
        if missing_stats:
            recs.append(
                f"Add get_stats() to {len(missing_stats)} skill(s): "
                + ", ".join(missing_stats[:5])
            )

        missing_todict = [n for n, m in self._cache.items() if not m.has_to_dict]
        if missing_todict:
            recs.append(
                f"Add to_dict() to {len(missing_todict)} skill(s): "
                + ", ".join(missing_todict[:5])
            )

        # Low documentation
        low_docs = [
            n for n, m in self._cache.items()
            if m.docstring_coverage < 50
        ]
        if low_docs:
            recs.append(
                f"Improve docstring coverage in {len(low_docs)} skill(s): "
                + ", ".join(low_docs[:5])
            )

        # Low error handling
        low_err = [
            n for n, m in self._cache.items()
            if m.error_handling_score < 30
        ]
        if low_err:
            recs.append(
                f"Add error handling to {len(low_err)} skill(s): "
                + ", ".join(low_err[:5])
            )

        # Overall quality
        avg_score = 0.0
        if scored:
            avg_score = sum(s[2] for s in scored) / len(scored)
            recs.append(f"Fleet average quality score: {avg_score:.1f}/100")

        # Trend insights
        improving = 0
        declining = 0
        for name in self._cache:
            trend = self._compute_trend(name)
            if trend.get("trend") == "improving":
                improving += 1
            elif trend.get("trend") == "declining":
                declining += 1
        if improving:
            recs.append(f"{improving} skill(s) showing improvement trend")
        if declining:
            recs.append(f"WARNING: {declining} skill(s) showing declining trend")

        return recs

    # -- Export -------------------------------------------------------------

    def export_report(self, output_path: str) -> str:
        """Export the evolution report as JSON.

        Args:
            output_path: Filesystem path for the JSON output.

        Returns:
            The output path written to.
        """
        report = self.generate_report()
        out = Path(output_path)
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(
            json.dumps(report.to_dict(), indent=2, default=str),
            encoding="utf-8",
        )
        logger.info("Evolution report exported to %s", out)
        return str(out)

    # -- Stats --------------------------------------------------------------

    def get_stats(self) -> dict:
        """Return evolver operational statistics."""
        return {
            "scans_run": self._scans_run,
            "evolutions_recorded": self._evolutions_recorded,
            "skills_cached": len(self._cache),
            "db_path": str(self._db_path),
            "engines_dir": str(self._engines_dir),
            "skills_dir": str(self._skills_dir),
            "known_mi_skills": len(MI_DOMAIN_SKILLS),
        }


# ---------------------------------------------------------------------------
# Module-level convenience
# ---------------------------------------------------------------------------


def scan_all_skills() -> List[SkillMetrics]:
    """Quick scan of all skill modules."""
    return SkillEvolver().scan_skills()


def get_evolution_report() -> EvolutionReport:
    """Generate a full evolution report."""
    return SkillEvolver().generate_report()


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(name)s | %(message)s")
    evolver = SkillEvolver()
    skills = evolver.scan_skills()
    print(f"Found {len(skills)} skill modules\n")
    for s in skills:
        score = evolver.score_skill(s)
        flag = "✓" if score >= 60 else "⚠"
        print(f"  {flag} {s.skill_name:35s}  score={score:5.1f}  LOC={s.lines_of_code:4d}  "
              f"funcs={s.function_count:2d}  docs={s.docstring_coverage:5.1f}%  "
              f"err={s.error_handling_score:5.1f}%")

    targets = evolver.identify_evolution_targets()
    if targets:
        print(f"\n--- Evolution Targets ({len(targets)}) ---")
        for name, improvements in targets[:10]:
            print(f"\n  {name}:")
            for imp in improvements:
                print(f"    → {imp}")

    print(f"\nStats: {json.dumps(evolver.get_stats(), indent=2)}")
