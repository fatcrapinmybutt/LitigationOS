"""Tests for HealthMonitor engine — system health, self-healing, models."""

from __future__ import annotations

import sqlite3
import textwrap
from pathlib import Path

import pytest

from litigationos.engines.health_monitor import (
    HEAL_ACTIONS,
    DriveStatus,
    HealthCheck,
    HealthMonitor,
    Status,
    SystemHealth,
    _status_icon,
)


# ============================================================================
# Pydantic model unit tests
# ============================================================================


class TestHealthCheckModel:
    """Validate the HealthCheck Pydantic model."""

    def test_defaults(self):
        hc = HealthCheck(component="test")
        assert hc.status == Status.UNKNOWN
        assert hc.score == 0
        assert hc.message == ""
        assert hc.details == {}

    def test_score_clamped_high(self):
        with pytest.raises(Exception):
            HealthCheck(component="x", score=101)

    def test_score_clamped_low(self):
        with pytest.raises(Exception):
            HealthCheck(component="x", score=-1)

    def test_valid_statuses(self):
        for s in Status:
            hc = HealthCheck(component="x", status=s, score=50)
            assert hc.status == s

    def test_details_dict(self):
        hc = HealthCheck(component="db", details={"tables": 42})
        assert hc.details["tables"] == 42


class TestDriveStatusModel:
    """Validate the DriveStatus Pydantic model."""

    def test_defaults(self):
        ds = DriveStatus(drive_letter="C:\\")
        assert ds.total_gb == 0.0
        assert ds.free_gb == 0.0
        assert ds.accessible is False
        assert ds.file_count == 0

    def test_populated(self):
        ds = DriveStatus(
            drive_letter="C:\\",
            total_gb=500.0,
            free_gb=120.5,
            accessible=True,
            file_count=73,
        )
        assert ds.accessible is True
        assert ds.free_gb == 120.5


class TestSystemHealthModel:
    """Validate the SystemHealth aggregate model."""

    def test_overall_score_empty(self):
        sh = SystemHealth()
        assert sh.overall_score == 0

    def test_overall_score_single(self):
        sh = SystemHealth(
            checks=[HealthCheck(component="a", score=80)]
        )
        assert sh.overall_score == 80

    def test_overall_score_average(self):
        sh = SystemHealth(
            checks=[
                HealthCheck(component="a", score=100),
                HealthCheck(component="b", score=50),
            ]
        )
        assert sh.overall_score == 75

    def test_recommendations_list(self):
        sh = SystemHealth(recommendations=["fix X", "check Y"])
        assert len(sh.recommendations) == 2

    def test_timestamp_auto(self):
        sh = SystemHealth()
        assert sh.timestamp is not None


# ============================================================================
# HealthMonitor — database checks
# ============================================================================


@pytest.fixture
def health_db(tmp_path: Path) -> Path:
    """Create a minimal SQLite DB for health-check tests."""
    db_path = tmp_path / "health_test.db"
    conn = sqlite3.connect(str(db_path))
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute(
        "CREATE TABLE evidence (id INTEGER PRIMARY KEY, file_path TEXT, title TEXT)"
    )
    conn.execute(
        "CREATE TABLE documents (id INTEGER PRIMARY KEY, name TEXT)"
    )
    conn.close()
    return db_path


@pytest.fixture
def monitor(health_db: Path) -> HealthMonitor:
    return HealthMonitor(db_path=health_db)


class TestCheckDatabase:
    """Database connectivity and health checks."""

    def test_healthy_db(self, monitor: HealthMonitor):
        result = monitor.check_database()
        assert result.component == "database"
        assert result.status == Status.HEALTHY
        assert result.score > 0
        assert result.details["table_count"] >= 2
        assert result.details["integrity"] == "ok"

    def test_missing_db(self, tmp_path: Path):
        m = HealthMonitor(db_path=tmp_path / "nonexistent.db")
        result = m.check_database()
        assert result.status == Status.CRITICAL
        assert result.score == 0

    def test_journal_mode_wal(self, monitor: HealthMonitor):
        result = monitor.check_database()
        assert result.details.get("journal_mode") == "wal"


# ============================================================================
# HealthMonitor — drive checks
# ============================================================================


class TestCheckDrives:
    """Drive accessibility and space checks."""

    def test_returns_drives_details(self, monitor: HealthMonitor):
        result = monitor.check_drives()
        assert result.component == "drives"
        assert "drives" in result.details
        assert isinstance(result.details["drives"], list)
        assert len(result.details["drives"]) > 0

    def test_c_drive_accessible(self, monitor: HealthMonitor):
        result = monitor.check_drives()
        drives = result.details["drives"]
        c_drive = next((d for d in drives if d["drive_letter"] == "C:\\"), None)
        assert c_drive is not None
        assert c_drive["accessible"] is True
        assert c_drive["total_gb"] > 0


# ============================================================================
# HealthMonitor — pipeline checks
# ============================================================================


class TestCheckPipeline:
    """Pipeline script validation."""

    def test_with_valid_scripts(self, tmp_path: Path, monitor: HealthMonitor):
        # Patch the pipeline dir to a temp dir with valid scripts
        import litigationos.engines.health_monitor as hm

        orig = hm._PIPELINE_DIR
        hm._PIPELINE_DIR = tmp_path
        try:
            (tmp_path / "phase1.py").write_text("x = 1\n", encoding="utf-8")
            (tmp_path / "phase2.py").write_text("y = 2\n", encoding="utf-8")
            result = monitor.check_pipeline()
            assert result.status == Status.HEALTHY
            assert result.details["scripts_found"] == 2
            assert len(result.details["syntax_errors"]) == 0
        finally:
            hm._PIPELINE_DIR = orig

    def test_with_syntax_error(self, tmp_path: Path, monitor: HealthMonitor):
        import litigationos.engines.health_monitor as hm

        orig = hm._PIPELINE_DIR
        hm._PIPELINE_DIR = tmp_path
        try:
            (tmp_path / "good.py").write_text("x = 1\n", encoding="utf-8")
            (tmp_path / "bad.py").write_text("def f(\n", encoding="utf-8")
            result = monitor.check_pipeline()
            assert result.status == Status.WARNING
            assert len(result.details["syntax_errors"]) == 1
        finally:
            hm._PIPELINE_DIR = orig

    def test_missing_pipeline_dir(self, monitor: HealthMonitor):
        import litigationos.engines.health_monitor as hm

        orig = hm._PIPELINE_DIR
        hm._PIPELINE_DIR = Path("C:\\nonexistent_pipeline_dir_xyz")
        try:
            result = monitor.check_pipeline()
            assert result.status == Status.CRITICAL
            assert result.score == 0
        finally:
            hm._PIPELINE_DIR = orig


# ============================================================================
# HealthMonitor — agent checks
# ============================================================================


class TestCheckAgents:
    """Agent fleet file verification."""

    def test_with_agent_files(self, tmp_path: Path, monitor: HealthMonitor):
        import litigationos.engines.health_monitor as hm

        orig = hm._AGENTS_DIR
        hm._AGENTS_DIR = tmp_path
        try:
            (tmp_path / "agent_base.py").write_text("class Agent: pass\n", encoding="utf-8")
            (tmp_path / "agent_orchestrator.py").write_text("# orch\n", encoding="utf-8")
            (tmp_path / "a01_scanner.py").write_text("# a01\n", encoding="utf-8")
            result = monitor.check_agents()
            assert result.status == Status.HEALTHY
            assert result.details["agent_files"] == 3
            assert result.details["missing"] == []
        finally:
            hm._AGENTS_DIR = orig

    def test_missing_core_agents(self, tmp_path: Path, monitor: HealthMonitor):
        import litigationos.engines.health_monitor as hm

        orig = hm._AGENTS_DIR
        hm._AGENTS_DIR = tmp_path
        try:
            (tmp_path / "something.py").write_text("# x\n", encoding="utf-8")
            result = monitor.check_agents()
            assert len(result.details["missing"]) == 2
            assert result.score < 100
        finally:
            hm._AGENTS_DIR = orig


# ============================================================================
# HealthMonitor — evidence integrity
# ============================================================================


class TestCheckEvidenceIntegrity:
    """Evidence file integrity sampling."""

    def test_files_exist(self, health_db: Path, tmp_path: Path):
        # Insert evidence records pointing to real files
        evidence_file = tmp_path / "exhibit_a.pdf"
        evidence_file.write_text("PDF content", encoding="utf-8")

        conn = sqlite3.connect(str(health_db))
        conn.execute(
            "INSERT INTO evidence (file_path) VALUES (?)",
            (str(evidence_file),),
        )
        conn.commit()
        conn.close()

        m = HealthMonitor(db_path=health_db)
        result = m.check_evidence_integrity(sample_size=10)
        assert result.details["accessible"] == 1
        assert result.details["missing"] == 0

    def test_missing_files(self, health_db: Path):
        conn = sqlite3.connect(str(health_db))
        conn.execute(
            "INSERT INTO evidence (file_path) VALUES (?)",
            ("C:\\nonexistent_evidence_xyz.pdf",),
        )
        conn.commit()
        conn.close()

        m = HealthMonitor(db_path=health_db)
        result = m.check_evidence_integrity(sample_size=10)
        assert result.details["missing"] == 1

    def test_empty_table(self, monitor: HealthMonitor):
        result = monitor.check_evidence_integrity()
        assert result.status == Status.UNKNOWN


# ============================================================================
# HealthMonitor — system_health aggregate
# ============================================================================


class TestSystemHealth:
    """Full system_health aggregation."""

    def test_returns_system_health(self, monitor: HealthMonitor):
        health = monitor.system_health()
        assert isinstance(health, SystemHealth)
        assert len(health.checks) == 5
        assert 0 <= health.overall_score <= 100

    def test_component_names(self, monitor: HealthMonitor):
        health = monitor.system_health()
        names = {c.component for c in health.checks}
        assert names == {"database", "drives", "pipeline", "agents", "evidence_integrity"}


# ============================================================================
# HealthMonitor — self-healing
# ============================================================================


class TestSelfHeal:
    """Self-healing actions."""

    def test_wal_checkpoint(self, monitor: HealthMonitor):
        result = monitor.self_heal("wal_checkpoint")
        assert result.status == Status.HEALTHY
        assert "checkpoint" in result.message.lower()

    def test_reindex(self, monitor: HealthMonitor):
        result = monitor.self_heal("reindex")
        assert result.status == Status.HEALTHY
        assert "reindex" in result.message.lower()

    def test_unknown_action(self, monitor: HealthMonitor):
        result = monitor.self_heal("nonexistent_action")
        assert result.status == Status.UNKNOWN
        assert "unknown" in result.message.lower()

    def test_vacuum(self, monitor: HealthMonitor):
        result = monitor.self_heal("vacuum")
        assert result.status == Status.HEALTHY
        assert "vacuum" in result.message.lower()

    def test_clear_temp(self, monitor: HealthMonitor):
        result = monitor.self_heal("clear_temp")
        assert result.component == "self_heal"

    def test_heal_actions_constant(self):
        assert "wal_checkpoint" in HEAL_ACTIONS
        assert "vacuum" in HEAL_ACTIONS
        assert "reindex" in HEAL_ACTIONS
        assert "clear_temp" in HEAL_ACTIONS
        assert "fix_symlinks" in HEAL_ACTIONS


# ============================================================================
# HealthMonitor — report generation
# ============================================================================


class TestGenerateReport:
    """Markdown report generation."""

    def test_report_is_markdown(self, monitor: HealthMonitor):
        report = monitor.generate_report()
        assert report.startswith("# LitigationOS System Health Report")
        assert "Overall Score" in report
        assert "Component Checks" in report

    def test_report_contains_table(self, monitor: HealthMonitor):
        report = monitor.generate_report()
        assert "| Component |" in report
        assert "| database |" in report or "| database " in report


# ============================================================================
# Helper functions
# ============================================================================


class TestHelpers:
    """Module-level helper tests."""

    def test_status_icons(self):
        assert _status_icon(Status.HEALTHY) == "🟢"
        assert _status_icon(Status.WARNING) == "🟡"
        assert _status_icon(Status.CRITICAL) == "🔴"
        assert _status_icon(Status.UNKNOWN) == "⚪"
