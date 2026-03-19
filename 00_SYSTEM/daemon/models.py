"""
Pydantic models for the LitigationOS Daemon.
Covers: configuration, task queue, health, satellites, skills, storage.
"""
import os
import sys
from datetime import datetime
from enum import Enum
from typing import Any, Optional

from pydantic import BaseModel, Field, field_validator


# ---------------------------------------------------------------------------
# Enums
# ---------------------------------------------------------------------------

class TaskPriority(str, Enum):
    CRITICAL = "critical"
    HIGH = "high"
    NORMAL = "normal"
    LOW = "low"


class TaskStatus(str, Enum):
    QUEUED = "queued"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    DEAD_LETTER = "dead_letter"


class SatelliteStatus(str, Enum):
    STOPPED = "stopped"
    STARTING = "starting"
    RUNNING = "running"
    UNHEALTHY = "unhealthy"
    CRASHED = "crashed"


class FilingPhase(str, Enum):
    DRAFT = "draft"
    REVIEW = "review"
    QA = "qa"
    APPROVED = "approved"
    FORMATTED = "formatted"
    FILED = "filed"
    SERVED = "served"


class DriveRole(str, Enum):
    HEAVY = "heavy"      # I: — DBs, archives, dedup, indexes, brains
    LITE = "lite"        # D:/F:/G:/H: — refs, templates, quick-access
    PRIMARY = "primary"  # C: — main project


class SkillTier(str, Enum):
    CORE = "core"
    ENHANCEMENT = "enhancement"
    INFRASTRUCTURE = "infrastructure"


# ---------------------------------------------------------------------------
# Configuration Models
# ---------------------------------------------------------------------------

class DriveConfig(BaseModel):
    path: str
    role: DriveRole
    max_file_size_mb: int = Field(default=50)
    alert_free_gb: float = Field(default=5.0)
    pause_ingest_free_gb: float = Field(default=2.0)


class WatchdogConfig(BaseModel):
    watch_dirs: list[str] = Field(default_factory=lambda: [r"C:\Users\andre\LitigationOS"])
    poll_interval_sec: float = 1.0
    exclude_patterns: list[str] = Field(
        default_factory=lambda: [
            "__pycache__", ".git", "node_modules", "*.pyc",
            "temp", "build", ".vscode", "*.tmp", "*.swp"
        ]
    )
    auto_classify: bool = True
    auto_lane_route: bool = True
    auto_ingest: bool = False


class SchedulerConfig(BaseModel):
    brain_evolution_hours: int = 1
    drive_scan_hours: int = 24
    deadline_check_hours: int = 6
    citation_verify_hours: int = 168
    health_check_minutes: int = 30


class SatelliteConfig(BaseModel):
    name: str
    command: str
    args: list[str] = Field(default_factory=list)
    cwd: Optional[str] = None
    max_ram_mb: int = 4096
    max_cpu_percent: float = 100.0
    heartbeat_interval_sec: int = 30
    max_missed_heartbeats: int = 3
    restart_backoff_sec: list[int] = Field(default_factory=lambda: [5, 10, 20, 60])
    auto_start: bool = True


class LoggingConfig(BaseModel):
    level: str = "INFO"
    log_dir: str = r"C:\Users\andre\LitigationOS\00_SYSTEM\daemon\logs"
    max_file_size_mb: int = 10
    backup_count: int = 5
    log_to_db: bool = True
    structured_json: bool = True


class DaemonConfig(BaseModel):
    version: str = "1.0.0"
    db_path: str = r"C:\Users\andre\LitigationOS\00_SYSTEM\daemon\daemon.db"
    litigation_db_path: str = r"C:\Users\andre\LitigationOS\litigation_context.db"
    brain_dir: str = r"C:\Users\andre\LitigationOS\00_SYSTEM\brains"
    max_concurrent_tasks: int = 3
    task_timeout_sec: int = 300
    drives: list[DriveConfig] = Field(default_factory=lambda: [
        DriveConfig(path="C:", role=DriveRole.PRIMARY, max_file_size_mb=100, alert_free_gb=10.0),
        DriveConfig(path="I:", role=DriveRole.HEAVY, max_file_size_mb=10000, alert_free_gb=5.0),
        DriveConfig(path="D:", role=DriveRole.LITE, max_file_size_mb=50, alert_free_gb=2.0),
        DriveConfig(path="F:", role=DriveRole.LITE, max_file_size_mb=50, alert_free_gb=2.0),
        DriveConfig(path="G:", role=DriveRole.LITE, max_file_size_mb=50, alert_free_gb=2.0),
        DriveConfig(path="H:", role=DriveRole.LITE, max_file_size_mb=50, alert_free_gb=2.0),
    ])
    watchdog: WatchdogConfig = Field(default_factory=WatchdogConfig)
    scheduler: SchedulerConfig = Field(default_factory=SchedulerConfig)
    satellites: list[SatelliteConfig] = Field(default_factory=list)
    logging: LoggingConfig = Field(default_factory=LoggingConfig)

    @field_validator("db_path", "litigation_db_path", "brain_dir")
    @classmethod
    def validate_path(cls, v: str) -> str:
        return os.path.normpath(v)


# ---------------------------------------------------------------------------
# Task Queue Models
# ---------------------------------------------------------------------------

class TaskItem(BaseModel):
    id: str
    task_type: str
    payload: dict[str, Any] = Field(default_factory=dict)
    priority: TaskPriority = TaskPriority.NORMAL
    status: TaskStatus = TaskStatus.QUEUED
    created_at: datetime = Field(default_factory=datetime.utcnow)
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    error: Optional[str] = None
    retries: int = 0
    max_retries: int = 3
    source: str = "daemon"


class TaskResult(BaseModel):
    task_id: str
    success: bool
    output: dict[str, Any] = Field(default_factory=dict)
    duration_sec: float = 0.0
    error: Optional[str] = None


# ---------------------------------------------------------------------------
# Health & Status Models
# ---------------------------------------------------------------------------

class DriveHealth(BaseModel):
    path: str
    role: DriveRole
    total_gb: float
    used_gb: float
    free_gb: float
    percent_used: float
    status: str = "healthy"


class SatelliteHealth(BaseModel):
    name: str
    status: SatelliteStatus
    pid: Optional[int] = None
    ram_mb: float = 0.0
    cpu_percent: float = 0.0
    uptime_sec: float = 0.0
    last_heartbeat: Optional[datetime] = None
    crash_count: int = 0


class DaemonHealth(BaseModel):
    status: str = "healthy"
    uptime_sec: float = 0.0
    task_queue_depth: int = 0
    running_tasks: int = 0
    completed_tasks_24h: int = 0
    failed_tasks_24h: int = 0
    drives: list[DriveHealth] = Field(default_factory=list)
    satellites: list[SatelliteHealth] = Field(default_factory=list)
    last_brain_evolution: Optional[datetime] = None
    last_drive_scan: Optional[datetime] = None
    last_deadline_check: Optional[datetime] = None
    errors_last_hour: int = 0
    timestamp: datetime = Field(default_factory=datetime.utcnow)


# ---------------------------------------------------------------------------
# Skill Registry Models
# ---------------------------------------------------------------------------

class SkillInfo(BaseModel):
    id: str
    name: str
    version: str
    tier: SkillTier
    path: str
    description: str = ""
    dependencies: list[str] = Field(default_factory=list)
    status: str = "active"
    loaded_at: Optional[datetime] = None
    content_hash: str = ""
    usage_count: int = 0
    success_rate: float = 1.0


class SkillRun(BaseModel):
    skill_id: str
    input_summary: str
    output_summary: str
    duration_sec: float
    success: bool
    error: Optional[str] = None
    timestamp: datetime = Field(default_factory=datetime.utcnow)


# ---------------------------------------------------------------------------
# IPC Models
# ---------------------------------------------------------------------------

class IPCRequest(BaseModel):
    id: str
    method: str
    params: dict[str, Any] = Field(default_factory=dict)
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class IPCResponse(BaseModel):
    id: str
    success: bool
    result: Any = None
    error: Optional[str] = None
    timestamp: datetime = Field(default_factory=datetime.utcnow)
