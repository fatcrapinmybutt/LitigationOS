"""
Scheduler for LitigationOS Daemon.
Wraps APScheduler (or fallback simple scheduler) for periodic tasks.

Scheduled Jobs:
- Brain auto-evolution (hourly)
- Drive health scan (daily)
- Deadline check (every 6h)
- Citation verification (weekly)
- Health check (every 30m)
"""
import os
import threading
import time
from datetime import datetime, timedelta
from typing import Callable, Optional

from .models import SchedulerConfig


class ScheduledJob:
    """Represents a recurring scheduled job."""

    def __init__(self, name: str, func: Callable, interval_seconds: float,
                 run_immediately: bool = False):
        self.name = name
        self.func = func
        self.interval_seconds = interval_seconds
        self.run_immediately = run_immediately
        self.last_run: Optional[datetime] = None
        self.next_run: Optional[datetime] = None
        self.run_count: int = 0
        self.error_count: int = 0
        self.enabled: bool = True

    def is_due(self) -> bool:
        if not self.enabled:
            return False
        if self.next_run is None:
            return self.run_immediately
        return datetime.utcnow() >= self.next_run

    def execute(self, logger=None):
        try:
            self.func()
            self.run_count += 1
            self.last_run = datetime.utcnow()
            self.next_run = self.last_run + timedelta(seconds=self.interval_seconds)
        except Exception as e:
            self.error_count += 1
            if logger:
                logger.error(f"Scheduled job '{self.name}' failed: {e}")
            self.last_run = datetime.utcnow()
            self.next_run = self.last_run + timedelta(seconds=self.interval_seconds)


class DaemonScheduler:
    """Simple scheduler that integrates with the daemon main loop."""

    def __init__(self, config: SchedulerConfig, logger=None):
        self.config = config
        self.logger = logger
        self._jobs: dict[str, ScheduledJob] = {}

    def add_job(self, name: str, func: Callable, interval_seconds: float,
                run_immediately: bool = False):
        """Add a scheduled job."""
        job = ScheduledJob(name, func, interval_seconds, run_immediately)
        job.next_run = datetime.utcnow()
        if not run_immediately:
            job.next_run += timedelta(seconds=interval_seconds)
        self._jobs[name] = job
        if self.logger:
            self.logger.info(
                f"Scheduled '{name}' every {interval_seconds}s"
                f"{' (immediate)' if run_immediately else ''}"
            )

    def remove_job(self, name: str):
        self._jobs.pop(name, None)

    def tick(self):
        """Check and execute due jobs. Call this from the main loop."""
        for name, job in self._jobs.items():
            if job.is_due():
                if self.logger:
                    self.logger.debug(f"Running scheduled job: {name}")
                job.execute(self.logger)

    def status(self) -> list[dict]:
        """Get status of all scheduled jobs."""
        return [
            {
                "name": job.name,
                "enabled": job.enabled,
                "interval_sec": job.interval_seconds,
                "run_count": job.run_count,
                "error_count": job.error_count,
                "last_run": job.last_run.isoformat() if job.last_run else None,
                "next_run": job.next_run.isoformat() if job.next_run else None,
            }
            for job in self._jobs.values()
        ]

    def setup_default_jobs(self, task_queue=None):
        """Register the default daemon scheduled jobs."""

        def _brain_evolution():
            if task_queue:
                from .models import TaskPriority
                task_queue.enqueue("brain_evolution", priority=TaskPriority.LOW)

        def _drive_scan():
            if task_queue:
                from .models import TaskPriority
                task_queue.enqueue("drive_health_scan", priority=TaskPriority.LOW)

        def _deadline_check():
            if task_queue:
                from .models import TaskPriority
                task_queue.enqueue("deadline_check", priority=TaskPriority.HIGH)

        def _citation_verify():
            if task_queue:
                from .models import TaskPriority
                task_queue.enqueue("citation_verification", priority=TaskPriority.LOW)

        def _health_check():
            if task_queue:
                from .models import TaskPriority
                task_queue.enqueue("system_health_check", priority=TaskPriority.NORMAL)

        self.add_job("brain_evolution", _brain_evolution,
                      self.config.brain_evolution_hours * 3600)
        self.add_job("drive_scan", _drive_scan,
                      self.config.drive_scan_hours * 3600)
        self.add_job("deadline_check", _deadline_check,
                      self.config.deadline_check_hours * 3600,
                      run_immediately=True)
        self.add_job("citation_verify", _citation_verify,
                      self.config.citation_verify_hours * 3600)
        self.add_job("health_check", _health_check,
                      self.config.health_check_minutes * 60,
                      run_immediately=True)
