# -*- coding: utf-8 -*-
"""
self_healing_monitor.py — Self-Healing System Health Monitor
==============================================================
Monitors all LitigationOS engines, skills, pipeline phases, databases,
agents, and MCP tools for health issues. Auto-detects anomalies and
generates prioritized recovery plans.

Components monitored:
  - Databases: litigation_context.db (694 tables, 10.9 GB), lane DBs (A-F),
    master_index.db, mcr_rules.db
  - Engines: 80+ engines in 00_SYSTEM/engines/
  - Skills: 14 MI domain skills in engines/ and skills/
  - Pipeline: 16-phase data pipeline in 00_SYSTEM/pipeline/
  - Legal AI: 24+ modules in 00_SYSTEM/legal_ai/
  - MCP server: litigation-context-mcp (45 tools)
  - Agent fleet: 155+ agents conforming to Agent9999 contract
  - File system: critical paths, disk space, permissions

Recovery actions:
  - DB: VACUUM, REINDEX, WAL checkpoint, integrity repair
  - Modules: syntax fix suggestions, dependency identification
  - Disk: large file identification, cleanup targets
  - Failing modules: fallback alternatives, code fix hints

Zero external dependencies. Local-only.
"""

from __future__ import annotations

import ast
import json
import logging
import os
import re
import sqlite3
import time
from dataclasses import dataclass, field, asdict
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple

logger = logging.getLogger("legal_ai.self_healing_monitor")

_HERE = Path(__file__).resolve().parent
_SYSTEM = _HERE.parent                    # 00_SYSTEM
_REPO = _SYSTEM.parent                    # LitigationOS root
_DB_PATH = _REPO / "litigation_context.db"

# ---------------------------------------------------------------------------
# Critical paths map
# ---------------------------------------------------------------------------

_CRITICAL_PATHS: Dict[str, Path] = {
    "litigation_context_db": _REPO / "litigation_context.db",
    "engines_dir": _SYSTEM / "engines",
    "skills_dir": _SYSTEM / "skills",
    "pipeline_dir": _SYSTEM / "pipeline",
    "legal_ai_dir": _HERE,
    "mcp_server_dir": _SYSTEM / "mcp_server",
    "agents_dir": _SYSTEM / "pipeline" / "agents",
    "brains_dir": _SYSTEM / "brains",
    "local_model_dir": _SYSTEM / "local_model",
    "config_dir": _SYSTEM / "config",
}

_LANE_DBS: Dict[str, str] = {
    "lane_A_custody": "lane_A_custody.db",
    "lane_B_housing": "lane_B_housing.db",
    "lane_C_convergence": "lane_C_convergence.db",
    "lane_D_ppo": "lane_D_ppo.db",
    "lane_E_misconduct": "lane_E_misconduct.db",
    "lane_F_appellate": "lane_F_appellate.db",
}

_PIPELINE_PHASES: List[str] = [
    "phase0_safety_snapshot",
    "phase1_inventory",
    "phase2_dedup",
    "phase3_classify",
    "phase4a_extract_pdf",
    "phase4b_extract_docx",
    "phase4c_extract_structured",
    "phase4d_atomize",
    "phase4e_archive",
    "phase5_brain_feed",
    "phase6_gap_analysis",
    "phase7a_graph_delta",
    "phase7b_synthesis_merge",
    "phase7c_knowledge_merge",
    "phase8_litigation_refresh",
    "phase9_mcp_ingest",
]

# ---------------------------------------------------------------------------
# DB DDL
# ---------------------------------------------------------------------------

_HEALTH_CHECK_DDL = """\
CREATE TABLE IF NOT EXISTS health_checks (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    component TEXT NOT NULL,
    status TEXT NOT NULL,
    checked_at TEXT NOT NULL,
    details TEXT
)"""

# ---------------------------------------------------------------------------
# Enums & Dataclasses
# ---------------------------------------------------------------------------


class HealthStatus(Enum):
    """Health status levels for system components."""
    HEALTHY = "healthy"
    DEGRADED = "degraded"
    FAILING = "failing"
    DEAD = "dead"
    UNKNOWN = "unknown"


@dataclass
class ComponentHealth:
    """Health assessment for a single system component."""

    component_name: str
    component_type: str
    status: HealthStatus = HealthStatus.UNKNOWN
    last_check: str = ""
    uptime_pct: float = 100.0
    error_rate: float = 0.0
    response_time_ms: float = 0.0
    last_error: Optional[str] = None
    recovery_action: Optional[str] = None
    dependencies: List[str] = field(default_factory=list)
    details: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict:
        d = asdict(self)
        d["status"] = self.status.value
        return d


@dataclass
class HealthAlert:
    """An urgent health issue requiring attention."""

    severity: str  # critical, warning, info
    component: str
    message: str
    suggested_action: str
    detected_at: str = ""

    def to_dict(self) -> dict:
        return asdict(self)


@dataclass
class RecoveryAction:
    """An ordered recovery action for a failing component."""

    priority: int
    component: str
    action: str
    command: str
    estimated_impact: str
    risk_level: str = "low"  # low, medium, high

    def to_dict(self) -> dict:
        return asdict(self)


@dataclass
class HealthReport:
    """Complete system health report."""

    generated_at: str = ""
    overall_status: HealthStatus = HealthStatus.UNKNOWN
    total_components: int = 0
    healthy: int = 0
    degraded: int = 0
    failing: int = 0
    dead: int = 0
    components: List[ComponentHealth] = field(default_factory=list)
    alerts: List[Dict[str, Any]] = field(default_factory=list)
    recovery_plan: List[Dict[str, Any]] = field(default_factory=list)
    system_metrics: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict:
        return {
            "generated_at": self.generated_at,
            "overall_status": self.overall_status.value,
            "total_components": self.total_components,
            "healthy": self.healthy,
            "degraded": self.degraded,
            "failing": self.failing,
            "dead": self.dead,
            "components": [c.to_dict() for c in self.components],
            "alerts": self.alerts,
            "recovery_plan": self.recovery_plan,
            "system_metrics": self.system_metrics,
        }


# ---------------------------------------------------------------------------
# AST helpers
# ---------------------------------------------------------------------------


def _try_parse_ast(path: Path) -> Tuple[bool, Optional[str]]:
    """Attempt AST parse; return (success, error_message)."""
    try:
        source = path.read_text(encoding="utf-8", errors="replace")
        ast.parse(source)
        return True, None
    except SyntaxError as exc:
        return False, f"SyntaxError at line {exc.lineno}: {exc.msg}"
    except OSError as exc:
        return False, f"Read error: {exc}"


def _check_function_exists(path: Path, func_name: str) -> bool:
    """Check if a function or method exists in a Python module."""
    try:
        source = path.read_text(encoding="utf-8", errors="replace")
        tree = ast.parse(source)
        for node in ast.walk(tree):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                if node.name == func_name:
                    return True
    except (SyntaxError, OSError):
        pass
    return False


# ---------------------------------------------------------------------------
# SelfHealingMonitor
# ---------------------------------------------------------------------------


class SelfHealingMonitor:
    """Monitor system health and provide auto-recovery recommendations.

    Checks all LitigationOS subsystems — databases, engines, skills,
    pipeline phases, legal AI modules, agents, MCP tools, and disk health.
    Generates prioritized recovery plans for any degraded components.
    """

    # Thresholds
    _DB_SIZE_WARN_GB = 15.0
    _DB_SIZE_CRIT_GB = 25.0
    _DISK_FREE_WARN_GB = 10.0
    _DISK_FREE_CRIT_GB = 2.0
    _WAL_SIZE_WARN_MB = 500.0
    _MODULE_ERROR_RATE_WARN = 0.10
    _MODULE_ERROR_RATE_CRIT = 0.30

    def __init__(self, db_path: Optional[str] = None):
        self._db_path = Path(db_path) if db_path else _DB_PATH
        self._checks_run = 0
        self._alerts_generated = 0
        self._last_report: Optional[HealthReport] = None

        self._ensure_tables()

    # -- DB helpers ---------------------------------------------------------

    def _open_db(self, path: Optional[Path] = None) -> sqlite3.Connection:
        """Open a DB connection with required PRAGMAs."""
        target = path or self._db_path
        conn = sqlite3.connect(str(target))
        conn.execute("PRAGMA busy_timeout = 60000")
        conn.execute("PRAGMA journal_mode = WAL")
        conn.execute("PRAGMA cache_size = -32000")
        conn.execute("PRAGMA temp_store = MEMORY")
        conn.execute("PRAGMA synchronous = NORMAL")
        conn.row_factory = sqlite3.Row
        return conn

    def _ensure_tables(self) -> None:
        """Create health_checks table if it does not exist."""
        if not self._db_path.exists():
            logger.warning("DB not found at %s — table creation deferred", self._db_path)
            return
        try:
            conn = self._open_db()
            conn.execute(_HEALTH_CHECK_DDL)
            conn.commit()
            conn.close()
            logger.debug("health_checks table ensured")
        except sqlite3.Error as exc:
            logger.warning("Could not ensure health_checks table: %s", exc)

    def _persist_check(self, health: ComponentHealth) -> None:
        """Write a health check result to the DB."""
        if not self._db_path.exists():
            return
        try:
            conn = self._open_db()
            conn.execute(
                "INSERT INTO health_checks (component, status, checked_at, details) "
                "VALUES (?, ?, ?, ?)",
                (
                    health.component_name,
                    health.status.value,
                    health.last_check,
                    json.dumps(health.details, default=str),
                ),
            )
            conn.commit()
            conn.close()
        except sqlite3.Error as exc:
            logger.debug("Could not persist health check: %s", exc)

    # -- Database health checks ---------------------------------------------

    def check_database_health(self, db_path: str) -> ComponentHealth:
        """Check health of a single SQLite database.

        Runs integrity check, measures size, counts tables, checks WAL.

        Args:
            db_path: Filesystem path to the .db file.

        Returns:
            ComponentHealth with status and details.
        """
        self._checks_run += 1
        now = datetime.now().isoformat()
        path = Path(db_path)
        name = path.stem

        health = ComponentHealth(
            component_name=name,
            component_type="database",
            last_check=now,
        )

        if not path.exists():
            health.status = HealthStatus.DEAD
            health.last_error = f"Database file not found: {path}"
            health.recovery_action = "Restore from backup or recreate database"
            self._persist_check(health)
            return health

        start = time.monotonic()
        details: Dict[str, Any] = {}

        try:
            # File size
            size_bytes = path.stat().st_size
            size_gb = size_bytes / (1024 ** 3)
            details["size_bytes"] = size_bytes
            details["size_gb"] = round(size_gb, 3)

            # WAL size
            wal_path = path.with_suffix(".db-wal")
            if wal_path.exists():
                wal_size = wal_path.stat().st_size
                details["wal_size_bytes"] = wal_size
                details["wal_size_mb"] = round(wal_size / (1024 ** 2), 1)
            else:
                details["wal_size_bytes"] = 0
                details["wal_size_mb"] = 0.0

            conn = self._open_db(path)

            # Table count
            tables = conn.execute(
                "SELECT COUNT(*) FROM sqlite_master WHERE type = 'table'"
            ).fetchone()[0]
            details["table_count"] = tables

            # FTS table count
            fts_count = conn.execute(
                "SELECT COUNT(*) FROM sqlite_master WHERE type = 'table' "
                "AND sql LIKE '%fts5%'"
            ).fetchone()[0]
            details["fts_table_count"] = fts_count

            # Index count
            index_count = conn.execute(
                "SELECT COUNT(*) FROM sqlite_master WHERE type = 'index'"
            ).fetchone()[0]
            details["index_count"] = index_count

            # Quick integrity check (limited to first result)
            integrity = conn.execute("PRAGMA integrity_check(1)").fetchone()[0]
            details["integrity"] = integrity

            # Page stats
            page_size = conn.execute("PRAGMA page_size").fetchone()[0]
            page_count = conn.execute("PRAGMA page_count").fetchone()[0]
            freelist = conn.execute("PRAGMA freelist_count").fetchone()[0]
            details["page_size"] = page_size
            details["page_count"] = page_count
            details["freelist_pages"] = freelist
            details["fragmentation_pct"] = round(
                (freelist / max(page_count, 1)) * 100, 1
            )

            conn.close()

            elapsed = (time.monotonic() - start) * 1000
            health.response_time_ms = round(elapsed, 1)
            health.details = details

            # Determine status
            issues: List[str] = []

            if integrity != "ok":
                health.status = HealthStatus.FAILING
                issues.append(f"Integrity check failed: {integrity}")
                health.recovery_action = (
                    "Run: sqlite3 DB '.recover' > recovered.sql; "
                    "then rebuild from recovered.sql"
                )
            elif size_gb > self._DB_SIZE_CRIT_GB:
                health.status = HealthStatus.DEGRADED
                issues.append(f"Database very large: {size_gb:.1f} GB")
                health.recovery_action = "VACUUM to reclaim space"
            elif details.get("wal_size_mb", 0) > self._WAL_SIZE_WARN_MB:
                health.status = HealthStatus.DEGRADED
                issues.append(
                    f"WAL file large: {details['wal_size_mb']:.0f} MB"
                )
                health.recovery_action = "PRAGMA wal_checkpoint(TRUNCATE)"
            elif details["fragmentation_pct"] > 20:
                health.status = HealthStatus.DEGRADED
                issues.append(
                    f"High fragmentation: {details['fragmentation_pct']:.1f}%"
                )
                health.recovery_action = "VACUUM; REINDEX"
            else:
                health.status = HealthStatus.HEALTHY

            if issues:
                health.last_error = "; ".join(issues)

        except sqlite3.Error as exc:
            health.status = HealthStatus.FAILING
            health.last_error = f"SQLite error: {exc}"
            health.recovery_action = "Check DB file permissions and corruption"
            health.response_time_ms = round(
                (time.monotonic() - start) * 1000, 1
            )
        except OSError as exc:
            health.status = HealthStatus.DEAD
            health.last_error = f"OS error: {exc}"
            health.recovery_action = "Check file system and permissions"

        self._persist_check(health)
        return health

    def check_all_databases(self) -> List[ComponentHealth]:
        """Check health of all known databases.

        Returns:
            List of ComponentHealth for each database found.
        """
        results: List[ComponentHealth] = []

        # Central DB
        if self._db_path.exists():
            results.append(self.check_database_health(str(self._db_path)))

        # Lane databases — search in repo root and brains dir
        for lane_name, db_file in _LANE_DBS.items():
            for search_dir in (_REPO, _SYSTEM / "brains", _SYSTEM):
                candidate = search_dir / db_file
                if candidate.exists():
                    results.append(self.check_database_health(str(candidate)))
                    break
            else:
                results.append(ComponentHealth(
                    component_name=lane_name,
                    component_type="database",
                    status=HealthStatus.UNKNOWN,
                    last_check=datetime.now().isoformat(),
                    last_error=f"Database not found: {db_file}",
                ))

        # Other known databases
        for extra in ("master_index.db", "mcr_rules.db"):
            for search_dir in (_REPO, _SYSTEM / "pipeline" / "agents", _SYSTEM):
                candidate = search_dir / extra
                if candidate.exists():
                    results.append(self.check_database_health(str(candidate)))
                    break

        return results

    # -- Module health checks -----------------------------------------------

    def check_module_health(self, module_path: str) -> ComponentHealth:
        """Check health of a Python module via AST parse + interface check.

        Args:
            module_path: Filesystem path to the .py module.

        Returns:
            ComponentHealth for the module.
        """
        self._checks_run += 1
        now = datetime.now().isoformat()
        path = Path(module_path)

        health = ComponentHealth(
            component_name=path.stem,
            component_type="module",
            last_check=now,
        )

        if not path.exists():
            health.status = HealthStatus.DEAD
            health.last_error = f"Module not found: {path}"
            health.recovery_action = "Restore module from version control"
            self._persist_check(health)
            return health

        start = time.monotonic()
        details: Dict[str, Any] = {}

        # AST parse check
        success, error = _try_parse_ast(path)
        details["parseable"] = success
        if not success:
            health.status = HealthStatus.FAILING
            health.last_error = error
            health.recovery_action = f"Fix syntax error in {path.name}"
            health.details = details
            health.response_time_ms = round(
                (time.monotonic() - start) * 1000, 1
            )
            self._persist_check(health)
            return health

        # Size info
        try:
            source = path.read_text(encoding="utf-8", errors="replace")
            lines = source.splitlines()
            details["lines_of_code"] = len(lines)
            details["size_bytes"] = path.stat().st_size

            tree = ast.parse(source)

            # Count definitions
            func_count = sum(
                1 for n in ast.walk(tree)
                if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef))
            )
            class_count = sum(
                1 for n in ast.walk(tree) if isinstance(n, ast.ClassDef)
            )
            details["function_count"] = func_count
            details["class_count"] = class_count
            details["has_get_stats"] = _check_function_exists(path, "get_stats")

            # Check for bare excepts (code smell)
            bare_excepts = 0
            for node in ast.walk(tree):
                if isinstance(node, ast.ExceptHandler) and node.type is None:
                    bare_excepts += 1
            details["bare_excepts"] = bare_excepts

            health.status = HealthStatus.HEALTHY
            issues: List[str] = []

            if bare_excepts > 0:
                issues.append(f"{bare_excepts} bare except(s) found")
                health.status = HealthStatus.DEGRADED
                health.recovery_action = (
                    "Replace bare except with specific exception types"
                )

            if func_count == 0 and class_count == 0:
                issues.append("No functions or classes defined")
                if health.status == HealthStatus.HEALTHY:
                    health.status = HealthStatus.DEGRADED

            if issues:
                health.last_error = "; ".join(issues)

        except OSError as exc:
            health.status = HealthStatus.FAILING
            health.last_error = f"Read error: {exc}"

        health.details = details
        health.response_time_ms = round(
            (time.monotonic() - start) * 1000, 1
        )
        self._persist_check(health)
        return health

    def check_all_modules(self) -> List[ComponentHealth]:
        """Check health of all legal_ai modules.

        Returns:
            List of ComponentHealth for each module in legal_ai/.
        """
        results: List[ComponentHealth] = []
        if not _HERE.is_dir():
            return results

        for py_file in sorted(_HERE.glob("*.py")):
            if py_file.stem.startswith("__"):
                continue
            # Skip test/runner files
            if any(kw in py_file.stem for kw in ("test", "runner", "bisect", "wrapper", "wait")):
                continue
            results.append(self.check_module_health(str(py_file)))

        return results

    # -- Skill health checks ------------------------------------------------

    def check_skill_health(self, skill_path: str) -> ComponentHealth:
        """Check health of a single skill module.

        In addition to AST parsing, verifies expected skill interfaces:
        a main class, domain methods, and get_stats().

        Args:
            skill_path: Filesystem path to the skill .py file.

        Returns:
            ComponentHealth for the skill.
        """
        health = self.check_module_health(skill_path)
        health.component_type = "skill"

        if health.status in (HealthStatus.DEAD, HealthStatus.FAILING):
            return health

        path = Path(skill_path)
        details = health.details

        # Skill-specific checks
        has_get_stats = details.get("has_get_stats", False)
        class_count = details.get("class_count", 0)

        issues: List[str] = []
        if not has_get_stats:
            issues.append("Missing get_stats() method")
        if class_count == 0:
            issues.append("No class defined — skills should use class-based design")

        if issues:
            health.status = HealthStatus.DEGRADED
            existing = health.last_error or ""
            health.last_error = "; ".join(filter(None, [existing] + issues))
            health.recovery_action = "Add missing interfaces: " + ", ".join(issues)

        return health

    def check_all_skills(self) -> List[ComponentHealth]:
        """Check health of all skill modules in engines/ and skills/ dirs.

        Returns:
            List of ComponentHealth for each skill module found.
        """
        results: List[ComponentHealth] = []

        for directory in (_CRITICAL_PATHS["engines_dir"], _CRITICAL_PATHS["skills_dir"]):
            if not directory.is_dir():
                results.append(ComponentHealth(
                    component_name=directory.name,
                    component_type="skill_directory",
                    status=HealthStatus.DEAD,
                    last_check=datetime.now().isoformat(),
                    last_error=f"Directory not found: {directory}",
                ))
                continue

            for py_file in sorted(directory.glob("skill_*.py")):
                results.append(self.check_skill_health(str(py_file)))

            # Also check alienation_quantifier
            alienation = directory / "alienation_quantifier.py"
            if alienation.exists():
                results.append(self.check_skill_health(str(alienation)))

        return results

    # -- Pipeline health checks ---------------------------------------------

    def check_pipeline_health(self) -> ComponentHealth:
        """Check health of the 16-phase pipeline.

        Verifies that runner files exist and parse for all phases.

        Returns:
            ComponentHealth summarizing pipeline status.
        """
        self._checks_run += 1
        now = datetime.now().isoformat()
        pipeline_dir = _CRITICAL_PATHS["pipeline_dir"]

        health = ComponentHealth(
            component_name="pipeline",
            component_type="pipeline",
            last_check=now,
        )

        if not pipeline_dir.is_dir():
            health.status = HealthStatus.DEAD
            health.last_error = f"Pipeline directory not found: {pipeline_dir}"
            health.recovery_action = "Restore pipeline directory from version control"
            self._persist_check(health)
            return health

        start = time.monotonic()
        details: Dict[str, Any] = {"phases": {}}
        healthy_count = 0
        missing_count = 0
        error_count = 0

        for phase_name in _PIPELINE_PHASES:
            phase_file = pipeline_dir / f"{phase_name}.py"
            if not phase_file.exists():
                details["phases"][phase_name] = "missing"
                missing_count += 1
            else:
                success, error = _try_parse_ast(phase_file)
                if success:
                    details["phases"][phase_name] = "healthy"
                    healthy_count += 1
                else:
                    details["phases"][phase_name] = f"error: {error}"
                    error_count += 1

        total = len(_PIPELINE_PHASES)
        details["total_phases"] = total
        details["healthy_phases"] = healthy_count
        details["missing_phases"] = missing_count
        details["error_phases"] = error_count

        # Also check orchestrator
        orchestrator = pipeline_dir / "run_omega_pipeline.py"
        details["orchestrator_exists"] = orchestrator.exists()
        if orchestrator.exists():
            success, error = _try_parse_ast(orchestrator)
            details["orchestrator_parseable"] = success

        # Determine status
        if error_count > 0:
            health.status = HealthStatus.FAILING
            health.last_error = f"{error_count} phase(s) have syntax errors"
            health.recovery_action = "Fix syntax errors in failing phases"
        elif missing_count > total * 0.3:
            health.status = HealthStatus.DEGRADED
            health.last_error = f"{missing_count}/{total} phases missing"
            health.recovery_action = "Restore missing phase runners"
        elif missing_count > 0:
            health.status = HealthStatus.DEGRADED
            health.last_error = f"{missing_count} optional phase(s) missing"
        else:
            health.status = HealthStatus.HEALTHY

        health.uptime_pct = round((healthy_count / max(total, 1)) * 100, 1)
        health.details = details
        health.response_time_ms = round(
            (time.monotonic() - start) * 1000, 1
        )
        self._persist_check(health)
        return health

    # -- Agent health checks ------------------------------------------------

    def check_agent_health(self) -> ComponentHealth:
        """Check health of the agent fleet infrastructure.

        Verifies agent_base.py, orchestrator, and agent directory structure.

        Returns:
            ComponentHealth for the agent subsystem.
        """
        self._checks_run += 1
        now = datetime.now().isoformat()
        agents_dir = _CRITICAL_PATHS["agents_dir"]

        health = ComponentHealth(
            component_name="agent_fleet",
            component_type="agent",
            last_check=now,
        )

        if not agents_dir.is_dir():
            health.status = HealthStatus.DEAD
            health.last_error = f"Agents directory not found: {agents_dir}"
            health.recovery_action = "Restore agents directory from version control"
            self._persist_check(health)
            return health

        start = time.monotonic()
        details: Dict[str, Any] = {}

        # Check agent_base.py
        agent_base = agents_dir / "agent_base.py"
        details["agent_base_exists"] = agent_base.exists()
        if agent_base.exists():
            success, error = _try_parse_ast(agent_base)
            details["agent_base_parseable"] = success
            if not success:
                details["agent_base_error"] = error

        # Check orchestrator
        orchestrator = agents_dir / "agent_orchestrator.py"
        details["orchestrator_exists"] = orchestrator.exists()
        if orchestrator.exists():
            success, error = _try_parse_ast(orchestrator)
            details["orchestrator_parseable"] = success

        # Count agent files
        agent_files = list(agents_dir.glob("*.py"))
        details["total_agent_files"] = len(agent_files)

        # Check master_index.db
        master_db = agents_dir / "master_index.db"
        if not master_db.exists():
            master_db = _REPO / "master_index.db"
        details["master_index_exists"] = master_db.exists()

        # Parse each agent file
        parseable = 0
        unparseable = 0
        agent_errors: List[str] = []
        for af in agent_files:
            if af.stem.startswith("__"):
                continue
            success, error = _try_parse_ast(af)
            if success:
                parseable += 1
            else:
                unparseable += 1
                agent_errors.append(f"{af.name}: {error}")

        details["parseable_agents"] = parseable
        details["unparseable_agents"] = unparseable
        if agent_errors:
            details["agent_errors"] = agent_errors[:10]

        # Determine status
        if not agent_base.exists():
            health.status = HealthStatus.FAILING
            health.last_error = "agent_base.py missing — fleet cannot operate"
            health.recovery_action = "Restore agent_base.py from version control"
        elif unparseable > 0:
            health.status = HealthStatus.DEGRADED
            health.last_error = f"{unparseable} agent file(s) have syntax errors"
            health.recovery_action = "Fix syntax errors in agent files"
        else:
            health.status = HealthStatus.HEALTHY

        health.details = details
        health.response_time_ms = round(
            (time.monotonic() - start) * 1000, 1
        )
        self._persist_check(health)
        return health

    # -- Disk / system checks -----------------------------------------------

    def check_disk_health(self) -> ComponentHealth:
        """Check disk space on drives used by LitigationOS.

        Returns:
            ComponentHealth with disk metrics for C: and other drives.
        """
        self._checks_run += 1
        now = datetime.now().isoformat()

        health = ComponentHealth(
            component_name="disk_storage",
            component_type="filesystem",
            last_check=now,
        )

        start = time.monotonic()
        details: Dict[str, Any] = {"drives": {}}

        drives_to_check = ["C:\\"]
        for extra in ("D:\\", "F:\\", "G:\\", "H:\\", "I:\\"):
            if os.path.exists(extra):
                drives_to_check.append(extra)

        worst_free_gb = float("inf")
        issues: List[str] = []

        for drive in drives_to_check:
            try:
                usage = os.statvfs(drive) if hasattr(os, "statvfs") else None
                # Windows: use ctypes-free approach
                total, used, free = self._get_disk_usage(drive)
                free_gb = free / (1024 ** 3)
                total_gb = total / (1024 ** 3)
                used_pct = (used / max(total, 1)) * 100

                details["drives"][drive] = {
                    "total_gb": round(total_gb, 1),
                    "free_gb": round(free_gb, 1),
                    "used_pct": round(used_pct, 1),
                }

                if free_gb < worst_free_gb:
                    worst_free_gb = free_gb

                if free_gb < self._DISK_FREE_CRIT_GB:
                    issues.append(f"CRITICAL: {drive} only {free_gb:.1f} GB free")
                elif free_gb < self._DISK_FREE_WARN_GB:
                    issues.append(f"WARNING: {drive} only {free_gb:.1f} GB free")

            except OSError as exc:
                details["drives"][drive] = {"error": str(exc)}

        # Determine status
        if any("CRITICAL" in i for i in issues):
            health.status = HealthStatus.FAILING
            health.recovery_action = "Free disk space immediately — delete temp files, old backups"
        elif any("WARNING" in i for i in issues):
            health.status = HealthStatus.DEGRADED
            health.recovery_action = "Consider cleaning up large files or archiving old data"
        else:
            health.status = HealthStatus.HEALTHY

        if issues:
            health.last_error = "; ".join(issues)

        health.details = details
        health.response_time_ms = round(
            (time.monotonic() - start) * 1000, 1
        )
        self._persist_check(health)
        return health

    @staticmethod
    def _get_disk_usage(path: str) -> Tuple[int, int, int]:
        """Get (total, used, free) bytes for a path. Works on Windows."""
        try:
            stat = os.statvfs(path)
            total = stat.f_frsize * stat.f_blocks
            free = stat.f_frsize * stat.f_bavail
            used = total - free
            return total, used, free
        except AttributeError:
            # Windows fallback using os.path
            pass

        # Windows: try shutil-free approach
        try:
            import ctypes
            free_bytes = ctypes.c_ulonglong(0)
            total_bytes = ctypes.c_ulonglong(0)
            ctypes.windll.kernel32.GetDiskFreeSpaceExW(  # type: ignore[attr-defined]
                path,
                None,
                ctypes.pointer(total_bytes),
                ctypes.pointer(free_bytes),
            )
            total = total_bytes.value
            free = free_bytes.value
            return total, total - free, free
        except (AttributeError, OSError):
            return 0, 0, 0

    def check_system_resources(self) -> Dict[str, Any]:
        """Gather system resource metrics (disk, DB size, file counts).

        Returns:
            Dictionary of system-level metrics.
        """
        metrics: Dict[str, Any] = {}

        # DB size
        if self._db_path.exists():
            metrics["main_db_size_gb"] = round(
                self._db_path.stat().st_size / (1024 ** 3), 3
            )

        # Disk info
        disk_health = self.check_disk_health()
        metrics["disk"] = disk_health.details.get("drives", {})

        # File counts in critical dirs
        for name, path in _CRITICAL_PATHS.items():
            if path.is_dir():
                try:
                    py_count = sum(1 for _ in path.glob("*.py"))
                    metrics[f"{name}_py_files"] = py_count
                except OSError:
                    pass

        return metrics

    # -- MCP check ----------------------------------------------------------

    def _check_mcp_health(self) -> ComponentHealth:
        """Check health of the MCP server package."""
        self._checks_run += 1
        now = datetime.now().isoformat()
        mcp_dir = _CRITICAL_PATHS["mcp_server_dir"]

        health = ComponentHealth(
            component_name="mcp_server",
            component_type="mcp_tool",
            last_check=now,
        )

        if not mcp_dir.is_dir():
            health.status = HealthStatus.DEAD
            health.last_error = f"MCP server directory not found: {mcp_dir}"
            health.recovery_action = "Install MCP server: pip install -e 00_SYSTEM/mcp_server/"
            return health

        details: Dict[str, Any] = {}

        # Check for key files
        init_file = mcp_dir / "__init__.py"
        server_py = mcp_dir / "server.py"
        db_py = mcp_dir / "db.py"

        details["has_init"] = init_file.exists()
        details["has_server"] = server_py.exists()
        details["has_db"] = db_py.exists()

        # Check parseability of server module
        if server_py.exists():
            success, error = _try_parse_ast(server_py)
            details["server_parseable"] = success
            if not success:
                health.status = HealthStatus.FAILING
                health.last_error = f"MCP server.py syntax error: {error}"
                health.recovery_action = "Fix syntax error in MCP server.py"
                health.details = details
                return health

        py_files = list(mcp_dir.glob("*.py"))
        details["total_py_files"] = len(py_files)

        health.status = HealthStatus.HEALTHY
        health.details = details
        return health

    # -- Component check (generic) ------------------------------------------

    def check_component(self, name: str, component_type: str) -> ComponentHealth:
        """Check health of a named component by type.

        Args:
            name: Component name (e.g., 'pipeline', 'agent_fleet').
            component_type: One of: engine, skill, pipeline_phase, agent,
                           database, mcp_tool, module.

        Returns:
            ComponentHealth for the component.
        """
        if component_type == "database":
            # Try to find the DB
            for search_dir in (_REPO, _SYSTEM / "brains", _SYSTEM):
                candidate = search_dir / f"{name}.db"
                if candidate.exists():
                    return self.check_database_health(str(candidate))
            return ComponentHealth(
                component_name=name,
                component_type=component_type,
                status=HealthStatus.UNKNOWN,
                last_check=datetime.now().isoformat(),
                last_error=f"Database {name}.db not found",
            )

        if component_type == "pipeline":
            return self.check_pipeline_health()

        if component_type == "agent":
            return self.check_agent_health()

        if component_type == "mcp_tool":
            return self._check_mcp_health()

        if component_type in ("engine", "skill", "module"):
            for directory in (_CRITICAL_PATHS["engines_dir"], _HERE, _CRITICAL_PATHS["skills_dir"]):
                candidate = directory / f"{name}.py"
                if candidate.exists():
                    if component_type == "skill":
                        return self.check_skill_health(str(candidate))
                    return self.check_module_health(str(candidate))

        return ComponentHealth(
            component_name=name,
            component_type=component_type,
            status=HealthStatus.UNKNOWN,
            last_check=datetime.now().isoformat(),
            last_error=f"Could not locate component: {name} ({component_type})",
        )

    # -- Full health check --------------------------------------------------

    def run_full_health_check(self) -> HealthReport:
        """Run a comprehensive health check across all subsystems.

        Returns:
            HealthReport with component statuses, alerts, and recovery plan.
        """
        start = time.monotonic()
        now = datetime.now().isoformat()
        components: List[ComponentHealth] = []

        # 1. Databases
        logger.info("Checking databases...")
        db_results = self.check_all_databases()
        components.extend(db_results)

        # 2. Legal AI modules
        logger.info("Checking legal_ai modules...")
        module_results = self.check_all_modules()
        components.extend(module_results)

        # 3. Skills
        logger.info("Checking skills...")
        skill_results = self.check_all_skills()
        components.extend(skill_results)

        # 4. Pipeline
        logger.info("Checking pipeline...")
        pipeline_health = self.check_pipeline_health()
        components.append(pipeline_health)

        # 5. Agents
        logger.info("Checking agents...")
        agent_health = self.check_agent_health()
        components.append(agent_health)

        # 6. MCP
        logger.info("Checking MCP server...")
        mcp_health = self._check_mcp_health()
        components.append(mcp_health)

        # 7. Disk
        logger.info("Checking disk health...")
        disk_health = self.check_disk_health()
        components.append(disk_health)

        # Tally
        status_counts = {s: 0 for s in HealthStatus}
        for c in components:
            status_counts[c.status] += 1

        # Overall status
        if status_counts[HealthStatus.DEAD] > 0:
            overall = HealthStatus.FAILING
        elif status_counts[HealthStatus.FAILING] > 0:
            overall = HealthStatus.FAILING
        elif status_counts[HealthStatus.DEGRADED] > 2:
            overall = HealthStatus.DEGRADED
        elif status_counts[HealthStatus.DEGRADED] > 0:
            overall = HealthStatus.DEGRADED
        else:
            overall = HealthStatus.HEALTHY

        # Generate alerts
        alerts = self._generate_alerts(components)

        # System metrics
        system_metrics = {
            "check_duration_ms": round(
                (time.monotonic() - start) * 1000, 1
            ),
        }
        if self._db_path.exists():
            system_metrics["main_db_size_gb"] = round(
                self._db_path.stat().st_size / (1024 ** 3), 3
            )

        # Recovery plan
        recovery_plan = self.generate_recovery_plan_from_components(components)

        report = HealthReport(
            generated_at=now,
            overall_status=overall,
            total_components=len(components),
            healthy=status_counts[HealthStatus.HEALTHY],
            degraded=status_counts[HealthStatus.DEGRADED],
            failing=status_counts[HealthStatus.FAILING],
            dead=status_counts[HealthStatus.DEAD],
            components=components,
            alerts=[a.to_dict() for a in alerts],
            recovery_plan=[r.to_dict() for r in recovery_plan],
            system_metrics=system_metrics,
        )

        self._last_report = report
        self._alerts_generated += len(alerts)

        logger.info(
            "Health check complete: %s — %d components, %d healthy, "
            "%d degraded, %d failing, %d dead",
            overall.value, len(components),
            status_counts[HealthStatus.HEALTHY],
            status_counts[HealthStatus.DEGRADED],
            status_counts[HealthStatus.FAILING],
            status_counts[HealthStatus.DEAD],
        )
        return report

    # -- Alert generation ---------------------------------------------------

    def _generate_alerts(self, components: List[ComponentHealth]) -> List[HealthAlert]:
        """Generate alerts from component health results."""
        alerts: List[HealthAlert] = []
        now = datetime.now().isoformat()

        for c in components:
            if c.status == HealthStatus.DEAD:
                alerts.append(HealthAlert(
                    severity="critical",
                    component=c.component_name,
                    message=f"DEAD: {c.last_error or 'Component unresponsive'}",
                    suggested_action=c.recovery_action or "Investigate immediately",
                    detected_at=now,
                ))
            elif c.status == HealthStatus.FAILING:
                alerts.append(HealthAlert(
                    severity="critical",
                    component=c.component_name,
                    message=f"FAILING: {c.last_error or 'Component failing'}",
                    suggested_action=c.recovery_action or "Check logs and fix errors",
                    detected_at=now,
                ))
            elif c.status == HealthStatus.DEGRADED:
                alerts.append(HealthAlert(
                    severity="warning",
                    component=c.component_name,
                    message=f"DEGRADED: {c.last_error or 'Performance degraded'}",
                    suggested_action=c.recovery_action or "Monitor and address soon",
                    detected_at=now,
                ))

        # Sort: critical first
        severity_order = {"critical": 0, "warning": 1, "info": 2}
        alerts.sort(key=lambda a: severity_order.get(a.severity, 3))
        return alerts

    # -- Recovery plan generation -------------------------------------------

    def generate_recovery_plan(self, report: HealthReport) -> List[Dict[str, Any]]:
        """Generate an ordered recovery plan from a health report.

        Args:
            report: A HealthReport from run_full_health_check().

        Returns:
            Ordered list of recovery action dicts.
        """
        actions = self.generate_recovery_plan_from_components(report.components)
        return [a.to_dict() for a in actions]

    def generate_recovery_plan_from_components(
        self, components: List[ComponentHealth]
    ) -> List[RecoveryAction]:
        """Build prioritized recovery actions from component health data."""
        actions: List[RecoveryAction] = []
        priority = 0

        # Phase 1: Fix DEAD components (highest priority)
        for c in components:
            if c.status == HealthStatus.DEAD:
                priority += 1
                actions.append(RecoveryAction(
                    priority=priority,
                    component=c.component_name,
                    action=c.recovery_action or f"Restore {c.component_name}",
                    command=self._suggest_command(c),
                    estimated_impact="critical — component non-functional",
                    risk_level="high",
                ))

        # Phase 2: Fix FAILING components
        for c in components:
            if c.status == HealthStatus.FAILING:
                priority += 1
                actions.append(RecoveryAction(
                    priority=priority,
                    component=c.component_name,
                    action=c.recovery_action or f"Fix {c.component_name}",
                    command=self._suggest_command(c),
                    estimated_impact="high — component unreliable",
                    risk_level="medium",
                ))

        # Phase 3: Fix DEGRADED components
        for c in components:
            if c.status == HealthStatus.DEGRADED:
                priority += 1
                actions.append(RecoveryAction(
                    priority=priority,
                    component=c.component_name,
                    action=c.recovery_action or f"Optimize {c.component_name}",
                    command=self._suggest_command(c),
                    estimated_impact="medium — reduced performance",
                    risk_level="low",
                ))

        return actions

    def _suggest_command(self, health: ComponentHealth) -> str:
        """Suggest a remediation command based on component type and issue."""
        ct = health.component_type
        name = health.component_name

        if ct == "database":
            if health.status == HealthStatus.DEAD:
                return f"# Restore {name}.db from backup"
            if "integrity" in (health.last_error or "").lower():
                return f'sqlite3 {name}.db ".recover" > recovered.sql'
            if "wal" in (health.last_error or "").lower():
                return f'sqlite3 {name}.db "PRAGMA wal_checkpoint(TRUNCATE)"'
            if "fragmentation" in (health.last_error or "").lower():
                return f'sqlite3 {name}.db "VACUUM; REINDEX"'
            return f'sqlite3 {name}.db "PRAGMA integrity_check"'

        if ct == "module" or ct == "skill":
            return f"python -c \"import ast; ast.parse(open('{name}.py').read())\""

        if ct == "pipeline":
            return "python 00_SYSTEM/pipeline/run_omega_pipeline.py --dry-run"

        if ct == "agent":
            return "python -m agents.agent_orchestrator --dry-run"

        if ct == "filesystem":
            return "# Review disk usage and free space"

        if ct == "mcp_tool":
            return "pip install -e 00_SYSTEM/mcp_server/"

        return f"# Investigate {name} ({ct})"

    # -- Export -------------------------------------------------------------

    def export_health_report(self, output_path: str) -> str:
        """Export the health report as JSON.

        Args:
            output_path: Filesystem path for the JSON output.

        Returns:
            The output path written to.
        """
        if self._last_report is None:
            self._last_report = self.run_full_health_check()

        out = Path(output_path)
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(
            json.dumps(self._last_report.to_dict(), indent=2, default=str),
            encoding="utf-8",
        )
        logger.info("Health report exported to %s", out)
        return str(out)

    # -- Stats --------------------------------------------------------------

    def get_stats(self) -> dict:
        """Return monitor operational statistics."""
        return {
            "checks_run": self._checks_run,
            "alerts_generated": self._alerts_generated,
            "db_path": str(self._db_path),
            "has_last_report": self._last_report is not None,
            "last_overall_status": (
                self._last_report.overall_status.value
                if self._last_report else "no_check_run"
            ),
        }


# ---------------------------------------------------------------------------
# Module-level convenience
# ---------------------------------------------------------------------------


def quick_health_check() -> HealthReport:
    """Run a full health check and return the report."""
    return SelfHealingMonitor().run_full_health_check()


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(name)s | %(message)s")
    monitor = SelfHealingMonitor()
    report = monitor.run_full_health_check()

    print(f"\n{'='*60}")
    print(f"  LitigationOS Health Report — {report.generated_at}")
    print(f"{'='*60}")
    print(f"  Overall: {report.overall_status.value.upper()}")
    print(f"  Components: {report.total_components}")
    print(f"  Healthy: {report.healthy}  |  Degraded: {report.degraded}  |  "
          f"Failing: {report.failing}  |  Dead: {report.dead}")

    if report.alerts:
        print(f"\n--- Alerts ({len(report.alerts)}) ---")
        for alert in report.alerts[:15]:
            sev = alert.get("severity", "?").upper()
            print(f"  [{sev}] {alert.get('component')}: {alert.get('message')}")

    if report.recovery_plan:
        print(f"\n--- Recovery Plan ({len(report.recovery_plan)} actions) ---")
        for action in report.recovery_plan[:10]:
            print(f"  #{action.get('priority')} {action.get('component')}: "
                  f"{action.get('action')}")
            print(f"       cmd: {action.get('command')}")

    print(f"\nStats: {json.dumps(monitor.get_stats(), indent=2)}")
