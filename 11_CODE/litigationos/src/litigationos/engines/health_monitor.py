"""System Health Monitor with self-healing for LitigationOS.

Provides comprehensive health checks across database, drives, pipeline,
agent fleet, and evidence integrity.  Includes self-healing capabilities
for common issues (WAL checkpoint, vacuum, reindex, temp cleanup).

Usage::

    monitor = HealthMonitor()
    report  = monitor.system_health()
    print(report.overall_score)

    # Self-heal a specific issue
    monitor.self_heal("wal_checkpoint")

    # Markdown report
    md = monitor.generate_report()
"""

from __future__ import annotations

import ast
import logging
import os
import sqlite3
import tempfile
import time
from datetime import datetime, timezone
from enum import Enum
from pathlib import Path
from typing import Any, Optional

from pydantic import BaseModel, ConfigDict, Field, computed_field

logger = logging.getLogger(__name__)

# -- Defaults -----------------------------------------------------------------

_DEFAULT_DB = Path(r"C:\Users\andre\LitigationOS\litigation_context.db")
_PIPELINE_DIR = Path(r"C:\Users\andre\LitigationOS\00_SYSTEM\pipeline")
_AGENTS_DIR = Path(r"C:\Users\andre\LitigationOS\00_SYSTEM\pipeline\agents")
_MONITORED_DRIVES = ["C:\\", "D:\\", "F:\\", "G:\\", "H:\\", "I:\\"]
_WAL_THRESHOLD_MB = 100
_LOW_DISK_THRESHOLD_GB = 5.0
_TEMP_DIRS = [
    Path(tempfile.gettempdir()),
    Path(r"C:\Users\andre\LitigationOS\temp"),
]

_SQLITE_PRAGMAS = (
    "PRAGMA busy_timeout=60000",
    "PRAGMA journal_mode=WAL",
    "PRAGMA cache_size=-32000",
    "PRAGMA temp_store=MEMORY",
    "PRAGMA synchronous=NORMAL",
)


# -- Pydantic models ----------------------------------------------------------


class Status(str, Enum):
    """Health-check status values."""

    HEALTHY = "healthy"
    WARNING = "warning"
    CRITICAL = "critical"
    UNKNOWN = "unknown"


class HealthCheck(BaseModel):
    """Result of a single health-check probe."""

    component: str
    status: Status = Status.UNKNOWN
    score: int = Field(default=0, ge=0, le=100)
    message: str = ""
    details: dict[str, Any] = Field(default_factory=dict)

    model_config = ConfigDict(from_attributes=True)


class DriveStatus(BaseModel):
    """Disk-drive health snapshot."""

    drive_letter: str
    total_gb: float = 0.0
    free_gb: float = 0.0
    accessible: bool = False
    file_count: int = 0

    model_config = ConfigDict(from_attributes=True)


class SystemHealth(BaseModel):
    """Aggregate health report for the entire system."""

    checks: list[HealthCheck] = Field(default_factory=list)
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    recommendations: list[str] = Field(default_factory=list)

    model_config = ConfigDict(from_attributes=True)

    @computed_field  # type: ignore[prop-decorator]
    @property
    def overall_score(self) -> int:
        """Weighted average of individual check scores (0-100)."""
        if not self.checks:
            return 0
        return round(sum(c.score for c in self.checks) / len(self.checks))


# -- Self-heal action registry ------------------------------------------------

HEAL_ACTIONS = (
    "wal_checkpoint",
    "vacuum",
    "reindex",
    "clear_temp",
    "fix_symlinks",
)


# -- Health Monitor -----------------------------------------------------------


class HealthMonitor:
    """System-wide health monitor with self-healing.

    Connects to the central ``litigation_context.db`` (or a caller-supplied
    path) and probes every subsystem.  All SQLite connections use the
    project-standard PRAGMAs.
    """

    def __init__(self, db_path: Optional[Path] = None) -> None:
        self._db_path = Path(db_path) if db_path else _DEFAULT_DB

    # -- helpers --------------------------------------------------------------

    def _connect(self) -> sqlite3.Connection:
        """Open a connection with required PRAGMAs."""
        conn = sqlite3.connect(str(self._db_path), timeout=120)
        conn.row_factory = sqlite3.Row
        for pragma in _SQLITE_PRAGMAS:
            conn.execute(pragma)
        return conn

    @staticmethod
    def _table_columns(conn: sqlite3.Connection, table: str) -> list[str]:
        """Return column names for *table* (PRAGMA table_info guard)."""
        rows = conn.execute(f"PRAGMA table_info({table})").fetchall()
        return [r["name"] for r in rows]

    @staticmethod
    def _table_exists(conn: sqlite3.Connection, table: str) -> bool:
        row = conn.execute(
            "SELECT 1 FROM sqlite_master WHERE type='table' AND name=?",
            (table,),
        ).fetchone()
        return row is not None

    # -- individual checks ----------------------------------------------------

    def check_database(self) -> HealthCheck:
        """Probe database connectivity, size, WAL status, and integrity."""
        details: dict[str, Any] = {}
        try:
            if not self._db_path.exists():
                return HealthCheck(
                    component="database",
                    status=Status.CRITICAL,
                    score=0,
                    message=f"Database not found: {self._db_path}",
                )

            db_size_mb = self._db_path.stat().st_size / (1024 * 1024)
            details["size_mb"] = round(db_size_mb, 2)

            # WAL file size
            wal_path = self._db_path.with_suffix(".db-wal")
            wal_mb = 0.0
            if wal_path.exists():
                wal_mb = wal_path.stat().st_size / (1024 * 1024)
            details["wal_size_mb"] = round(wal_mb, 2)

            conn = self._connect()
            try:
                # Journal mode
                journal = conn.execute("PRAGMA journal_mode").fetchone()
                details["journal_mode"] = journal[0] if journal else "unknown"

                # Table count
                row = conn.execute(
                    "SELECT COUNT(*) AS cnt FROM sqlite_master WHERE type='table'"
                ).fetchone()
                details["table_count"] = row["cnt"] if row else 0

                # Quick integrity check (faster than full)
                integrity = conn.execute("PRAGMA quick_check(1)").fetchone()
                details["integrity"] = integrity[0] if integrity else "unknown"
            finally:
                conn.close()

            # Scoring
            score = 100
            issues: list[str] = []

            if details.get("integrity") != "ok":
                score -= 50
                issues.append("Integrity check failed")

            if wal_mb > _WAL_THRESHOLD_MB:
                score -= 15
                issues.append(f"WAL file is {wal_mb:.0f} MB — checkpoint recommended")

            if details.get("table_count", 0) == 0:
                score -= 30
                issues.append("No tables found")

            status = (
                Status.CRITICAL if score < 40
                else Status.WARNING if score < 70
                else Status.HEALTHY
            )

            return HealthCheck(
                component="database",
                status=status,
                score=max(score, 0),
                message="; ".join(issues) if issues else "Database healthy",
                details=details,
            )

        except Exception as exc:
            logger.exception("Database health check failed")
            return HealthCheck(
                component="database",
                status=Status.CRITICAL,
                score=0,
                message=f"Database check error: {exc}",
                details=details,
            )

    def check_drives(self) -> HealthCheck:
        """Scan monitored drives for space and accessibility."""
        drive_statuses: list[dict[str, Any]] = []
        total_score = 0
        checked = 0

        for drive in _MONITORED_DRIVES:
            ds = self._probe_drive(drive)
            drive_statuses.append(ds.model_dump())
            if ds.accessible:
                checked += 1
                if ds.free_gb < _LOW_DISK_THRESHOLD_GB:
                    total_score += 40
                elif ds.free_gb < _LOW_DISK_THRESHOLD_GB * 3:
                    total_score += 70
                else:
                    total_score += 100

        score = round(total_score / max(checked, 1))
        accessible_count = sum(1 for d in drive_statuses if d["accessible"])

        status = (
            Status.CRITICAL if accessible_count == 0
            else Status.WARNING if accessible_count < len(_MONITORED_DRIVES) // 2
            else Status.HEALTHY if score >= 70
            else Status.WARNING
        )

        return HealthCheck(
            component="drives",
            status=status,
            score=min(score, 100),
            message=f"{accessible_count}/{len(_MONITORED_DRIVES)} drives accessible",
            details={"drives": drive_statuses},
        )

    def check_pipeline(self) -> HealthCheck:
        """Verify pipeline scripts exist and are syntactically valid Python."""
        details: dict[str, Any] = {"scripts_found": 0, "syntax_errors": []}

        if not _PIPELINE_DIR.exists():
            return HealthCheck(
                component="pipeline",
                status=Status.CRITICAL,
                score=0,
                message=f"Pipeline directory missing: {_PIPELINE_DIR}",
                details=details,
            )

        py_files = list(_PIPELINE_DIR.glob("*.py"))
        details["scripts_found"] = len(py_files)
        errors: list[str] = []

        for fp in py_files:
            try:
                source = fp.read_text(encoding="utf-8", errors="replace")
                ast.parse(source, filename=str(fp))
            except SyntaxError as exc:
                errors.append(f"{fp.name}: line {exc.lineno} — {exc.msg}")

        details["syntax_errors"] = errors
        error_count = len(errors)
        total = max(len(py_files), 1)
        score = round(((total - error_count) / total) * 100)

        status = (
            Status.CRITICAL if error_count > total // 2
            else Status.WARNING if error_count > 0
            else Status.HEALTHY
        )

        return HealthCheck(
            component="pipeline",
            status=status,
            score=max(score, 0),
            message=(
                f"{len(py_files)} scripts, {error_count} syntax error(s)"
                if error_count else f"{len(py_files)} scripts — all valid"
            ),
            details=details,
        )

    def check_agents(self) -> HealthCheck:
        """Verify the agent fleet files exist."""
        details: dict[str, Any] = {"agent_files": 0, "missing": []}

        if not _AGENTS_DIR.exists():
            return HealthCheck(
                component="agents",
                status=Status.WARNING,
                score=30,
                message=f"Agents directory missing: {_AGENTS_DIR}",
                details=details,
            )

        py_files = list(_AGENTS_DIR.glob("*.py"))
        details["agent_files"] = len(py_files)

        # Look for the core orchestrator and base
        expected = ["agent_base.py", "agent_orchestrator.py"]
        missing = [f for f in expected if not (_AGENTS_DIR / f).exists()]
        details["missing"] = missing

        score = 100
        if missing:
            score -= 25 * len(missing)
        if len(py_files) == 0:
            score = 10

        status = (
            Status.CRITICAL if score < 40
            else Status.WARNING if score < 70
            else Status.HEALTHY
        )

        return HealthCheck(
            component="agents",
            status=status,
            score=max(score, 0),
            message=f"{len(py_files)} agent files found",
            details=details,
        )

    def check_evidence_integrity(self, sample_size: int = 20) -> HealthCheck:
        """Sample evidence records and verify referenced files are not corrupted."""
        details: dict[str, Any] = {
            "sampled": 0,
            "accessible": 0,
            "missing": 0,
            "empty": 0,
        }

        if not self._db_path.exists():
            return HealthCheck(
                component="evidence_integrity",
                status=Status.UNKNOWN,
                score=0,
                message="Database unavailable — cannot check evidence",
                details=details,
            )

        conn = self._connect()
        try:
            if not self._table_exists(conn, "evidence"):
                return HealthCheck(
                    component="evidence_integrity",
                    status=Status.UNKNOWN,
                    score=50,
                    message="No evidence table — skipped",
                    details=details,
                )

            # Verify columns before querying
            columns = self._table_columns(conn, "evidence")
            if "file_path" not in columns:
                return HealthCheck(
                    component="evidence_integrity",
                    status=Status.UNKNOWN,
                    score=50,
                    message="evidence table lacks file_path column",
                    details=details,
                )

            query = (
                "SELECT file_path FROM evidence "
                "WHERE file_path IS NOT NULL "
                "ORDER BY RANDOM() LIMIT ?"
            )
            rows = conn.execute(query, (sample_size,)).fetchall()

            sampled = len(rows)
            details["sampled"] = sampled
            accessible = 0
            missing = 0
            empty = 0

            for row in rows:
                fp = Path(row["file_path"])
                if not fp.exists():
                    missing += 1
                elif fp.stat().st_size == 0:
                    empty += 1
                else:
                    accessible += 1

            details["accessible"] = accessible
            details["missing"] = missing
            details["empty"] = empty
        finally:
            conn.close()

        if sampled == 0:
            return HealthCheck(
                component="evidence_integrity",
                status=Status.UNKNOWN,
                score=50,
                message="No evidence file_path records to sample",
                details=details,
            )

        integrity_pct = accessible / sampled
        score = round(integrity_pct * 100)
        status = (
            Status.CRITICAL if score < 50
            else Status.WARNING if score < 80
            else Status.HEALTHY
        )

        return HealthCheck(
            component="evidence_integrity",
            status=status,
            score=score,
            message=(
                f"{accessible}/{sampled} files OK, "
                f"{missing} missing, {empty} empty"
            ),
            details=details,
        )

    # -- aggregate health ------------------------------------------------------

    def system_health(self) -> SystemHealth:
        """Run all checks and return an aggregate :class:`SystemHealth`."""
        checks = [
            self.check_database(),
            self.check_drives(),
            self.check_pipeline(),
            self.check_agents(),
            self.check_evidence_integrity(),
        ]

        recommendations = self._build_recommendations(checks)

        return SystemHealth(
            checks=checks,
            recommendations=recommendations,
        )

    # -- self-healing ----------------------------------------------------------

    def self_heal(self, issue: str) -> HealthCheck:
        """Attempt an automatic fix for *issue*.

        Supported issues: ``wal_checkpoint``, ``vacuum``, ``reindex``,
        ``clear_temp``, ``fix_symlinks``.
        """
        handlers: dict[str, Any] = {
            "wal_checkpoint": self._heal_wal_checkpoint,
            "vacuum": self._heal_vacuum,
            "reindex": self._heal_reindex,
            "clear_temp": self._heal_clear_temp,
            "fix_symlinks": self._heal_fix_symlinks,
        }

        handler = handlers.get(issue)
        if handler is None:
            return HealthCheck(
                component="self_heal",
                status=Status.UNKNOWN,
                score=0,
                message=f"Unknown heal action: {issue!r}. Valid: {', '.join(HEAL_ACTIONS)}",
            )

        try:
            return handler()
        except Exception as exc:
            logger.exception("Self-heal '%s' failed", issue)
            return HealthCheck(
                component="self_heal",
                status=Status.CRITICAL,
                score=0,
                message=f"Heal action {issue!r} failed: {exc}",
            )

    # -- report ----------------------------------------------------------------

    def generate_report(self) -> str:
        """Return a Markdown-formatted health report."""
        health = self.system_health()

        lines: list[str] = [
            "# LitigationOS System Health Report",
            "",
            f"**Generated:** {health.timestamp:%Y-%m-%d %H:%M:%S UTC}",
            f"**Overall Score:** {health.overall_score}/100",
            "",
            "## Component Checks",
            "",
            "| Component | Status | Score | Message |",
            "|-----------|--------|------:|---------|",
        ]

        for chk in health.checks:
            icon = _status_icon(chk.status)
            lines.append(
                f"| {chk.component} | {icon} {chk.status.value} "
                f"| {chk.score} | {chk.message} |"
            )

        if health.recommendations:
            lines += ["", "## Recommendations", ""]
            for idx, rec in enumerate(health.recommendations, 1):
                lines.append(f"{idx}. {rec}")

        # Drive breakdown
        drive_check = next((c for c in health.checks if c.component == "drives"), None)
        if drive_check and "drives" in drive_check.details:
            lines += ["", "## Drive Details", ""]
            lines.append("| Drive | Total GB | Free GB | Accessible | Files |")
            lines.append("|-------|--------:|--------:|:----------:|------:|")
            for d in drive_check.details["drives"]:
                acc = "✅" if d["accessible"] else "❌"
                lines.append(
                    f"| {d['drive_letter']} | {d['total_gb']:.1f} | "
                    f"{d['free_gb']:.1f} | {acc} | {d['file_count']} |"
                )

        lines.append("")
        return "\n".join(lines)

    # -- private heal implementations -----------------------------------------

    def _heal_wal_checkpoint(self) -> HealthCheck:
        """Run WAL checkpoint to shrink the WAL file."""
        conn = self._connect()
        try:
            result = conn.execute("PRAGMA wal_checkpoint(TRUNCATE)").fetchone()
            details = {
                "blocked": result[0] if result else -1,
                "wal_pages": result[1] if result else -1,
                "checkpointed": result[2] if result else -1,
            }
            return HealthCheck(
                component="self_heal",
                status=Status.HEALTHY,
                score=100,
                message="WAL checkpoint completed",
                details=details,
            )
        finally:
            conn.close()

    def _heal_vacuum(self) -> HealthCheck:
        """VACUUM the database to reclaim space and reduce fragmentation."""
        conn = self._connect()
        try:
            size_before = self._db_path.stat().st_size
            conn.execute("VACUUM")
            size_after = self._db_path.stat().st_size
            saved_mb = (size_before - size_after) / (1024 * 1024)
            return HealthCheck(
                component="self_heal",
                status=Status.HEALTHY,
                score=100,
                message=f"VACUUM complete — reclaimed {saved_mb:.1f} MB",
                details={
                    "size_before_mb": round(size_before / (1024 * 1024), 2),
                    "size_after_mb": round(size_after / (1024 * 1024), 2),
                    "reclaimed_mb": round(saved_mb, 2),
                },
            )
        finally:
            conn.close()

    def _heal_reindex(self) -> HealthCheck:
        """Rebuild all indexes to improve query performance."""
        conn = self._connect()
        try:
            start = time.monotonic()
            conn.execute("REINDEX")
            elapsed = time.monotonic() - start
            return HealthCheck(
                component="self_heal",
                status=Status.HEALTHY,
                score=100,
                message=f"REINDEX completed in {elapsed:.1f}s",
                details={"elapsed_seconds": round(elapsed, 2)},
            )
        finally:
            conn.close()

    def _heal_clear_temp(self) -> HealthCheck:
        """Remove stale files from known temp directories."""
        removed = 0
        errors = 0
        for tmp_dir in _TEMP_DIRS:
            if not tmp_dir.exists():
                continue
            for item in tmp_dir.iterdir():
                if item.is_file() and item.suffix in (".tmp", ".log", ".bak"):
                    try:
                        item.unlink()
                        removed += 1
                    except OSError:
                        errors += 1

        return HealthCheck(
            component="self_heal",
            status=Status.HEALTHY if errors == 0 else Status.WARNING,
            score=100 if errors == 0 else 80,
            message=f"Removed {removed} temp files ({errors} errors)",
            details={"removed": removed, "errors": errors},
        )

    def _heal_fix_symlinks(self) -> HealthCheck:
        """Find and remove broken symlinks under the project root."""
        project_root = self._db_path.parent
        broken = 0
        fixed = 0

        for item in project_root.rglob("*"):
            if item.is_symlink() and not item.exists():
                broken += 1
                try:
                    item.unlink()
                    fixed += 1
                except OSError:
                    pass

        return HealthCheck(
            component="self_heal",
            status=Status.HEALTHY,
            score=100,
            message=f"Found {broken} broken symlinks, removed {fixed}",
            details={"broken_found": broken, "removed": fixed},
        )

    # -- private helpers -------------------------------------------------------

    @staticmethod
    def _probe_drive(drive: str) -> DriveStatus:
        """Gather size/accessibility info for a single drive letter."""
        letter = drive.rstrip(":\\") + ":\\"
        try:
            if not os.path.exists(letter):
                return DriveStatus(drive_letter=letter)

            usage = os.statvfs(letter) if hasattr(os, "statvfs") else None
            if usage is None:
                # Windows: use ctypes or shutil
                import shutil
                total, _used, free = shutil.disk_usage(letter)
                total_gb = total / (1024 ** 3)
                free_gb = free / (1024 ** 3)
            else:
                total_gb = (usage.f_frsize * usage.f_blocks) / (1024 ** 3)
                free_gb = (usage.f_frsize * usage.f_bavail) / (1024 ** 3)

            # Count top-level items only
            try:
                file_count = sum(1 for _ in Path(letter).iterdir())
            except PermissionError:
                file_count = -1

            return DriveStatus(
                drive_letter=letter,
                total_gb=round(total_gb, 2),
                free_gb=round(free_gb, 2),
                accessible=True,
                file_count=file_count,
            )
        except Exception:
            return DriveStatus(drive_letter=letter)

    @staticmethod
    def _build_recommendations(checks: list[HealthCheck]) -> list[str]:
        """Derive actionable recommendations from check results."""
        recs: list[str] = []

        for chk in checks:
            if chk.status == Status.CRITICAL:
                recs.append(f"CRITICAL — {chk.component}: {chk.message}")

            if chk.component == "database":
                wal_mb = chk.details.get("wal_size_mb", 0)
                if wal_mb > _WAL_THRESHOLD_MB:
                    recs.append(
                        f"Run `self_heal('wal_checkpoint')` — WAL is {wal_mb:.0f} MB"
                    )
                if chk.details.get("integrity") != "ok":
                    recs.append(
                        "Database integrity check failed — investigate immediately"
                    )

            if chk.component == "drives":
                for d in chk.details.get("drives", []):
                    if d.get("accessible") and d.get("free_gb", 999) < _LOW_DISK_THRESHOLD_GB:
                        recs.append(
                            f"Drive {d['drive_letter']} has only {d['free_gb']:.1f} GB free"
                        )

            if chk.component == "pipeline" and chk.details.get("syntax_errors"):
                recs.append(
                    f"Fix {len(chk.details['syntax_errors'])} pipeline syntax errors"
                )

            if chk.component == "evidence_integrity":
                missing = chk.details.get("missing", 0)
                if missing > 0:
                    recs.append(f"{missing} evidence files missing — verify drive mounts")

        return recs


# -- module-level helpers -----------------------------------------------------


def _status_icon(status: Status) -> str:
    return {
        Status.HEALTHY: "🟢",
        Status.WARNING: "🟡",
        Status.CRITICAL: "🔴",
        Status.UNKNOWN: "⚪",
    }.get(status, "⚪")
