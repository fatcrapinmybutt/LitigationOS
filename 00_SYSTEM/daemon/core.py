"""
Core daemon loop for LitigationOS.
Asyncio-based main loop with <100ms cycle time.

Responsibilities:
- Config hot-reload
- Task queue processing
- Satellite health monitoring
- Scheduled job dispatch
- IPC request handling
"""
import asyncio
import logging
import os
import signal
import sys
import time
from datetime import datetime
from typing import Optional

from .config import ConfigManager
from .ipc import IPCServer
from .logging_config import setup_logging
from .models import DaemonConfig, DaemonHealth, TaskPriority
from .satellite import SatelliteManager
from .skill_registry import SkillRegistry
from .storage import StorageResolver
from .task_queue import TaskQueue


class DaemonCore:
    """Main daemon orchestrator."""

    def __init__(self, config_path: str = None):
        self._config_mgr = ConfigManager(config_path)
        self._config: DaemonConfig = self._config_mgr.config
        self._logger: Optional[logging.Logger] = None
        self._task_queue: Optional[TaskQueue] = None
        self._satellite_mgr: Optional[SatelliteManager] = None
        self._skill_registry: Optional[SkillRegistry] = None
        self._storage: Optional[StorageResolver] = None
        self._ipc: Optional[IPCServer] = None
        self._running = False
        self._start_time: Optional[datetime] = None
        self._completed_24h = 0
        self._failed_24h = 0

    def _init_subsystems(self):
        """Initialize all daemon subsystems."""
        cfg = self._config

        # Logging
        self._logger = setup_logging(cfg.logging, cfg.db_path)
        self._logger.info(f"LitigationOS Daemon v{cfg.version} starting...")

        # Task queue
        self._task_queue = TaskQueue(cfg.db_path)
        self._logger.info(f"Task queue initialized: {cfg.db_path}")

        # Satellites
        self._satellite_mgr = SatelliteManager(cfg.satellites, self._logger)

        # Skill registry
        self._skill_registry = SkillRegistry(cfg.db_path)
        skills = self._skill_registry.scan()
        self._logger.info(f"Skill registry: {len(skills)} skills loaded")

        # Storage resolver
        self._storage = StorageResolver(cfg)

        # IPC server
        self._ipc = IPCServer(self._logger)
        self._register_ipc_handlers()

    def _register_ipc_handlers(self):
        """Register IPC method handlers."""
        self._ipc.register("ping", lambda: True)
        self._ipc.register("status", self._get_health_dict)
        self._ipc.register("shutdown", self._request_shutdown)
        self._ipc.register("enqueue", self._ipc_enqueue)
        self._ipc.register("queue_depth", lambda: self._task_queue.depth())
        self._ipc.register("skills", lambda: [
            s.model_dump() for s in self._skill_registry.list_all()
        ])
        self._ipc.register("drives", lambda: [
            h.model_dump() for h in self._storage.get_all_drive_health()
        ])

    def _ipc_enqueue(self, task_type: str, payload: dict = None,
                     priority: str = "normal") -> str:
        pri = TaskPriority(priority)
        return self._task_queue.enqueue(task_type, payload, pri)

    def _request_shutdown(self):
        self._running = False
        return "shutdown_requested"

    def _get_health(self) -> DaemonHealth:
        """Build health snapshot."""
        depth = self._task_queue.depth() if self._task_queue else {}
        uptime = 0.0
        if self._start_time:
            uptime = (datetime.utcnow() - self._start_time).total_seconds()

        satellites = []
        if self._satellite_mgr:
            satellites = self._satellite_mgr.health_check()

        drives = []
        if self._storage:
            drives = self._storage.get_all_drive_health()

        return DaemonHealth(
            status="running" if self._running else "stopped",
            uptime_sec=round(uptime, 0),
            task_queue_depth=depth.get("queued", 0),
            running_tasks=depth.get("running", 0),
            completed_tasks_24h=self._completed_24h,
            failed_tasks_24h=self._failed_24h,
            drives=drives,
            satellites=satellites,
        )

    def _get_health_dict(self) -> dict:
        return self._get_health().model_dump(mode="json")

    async def _main_loop(self):
        """Core async event loop."""
        self._running = True
        self._start_time = datetime.utcnow()

        # Start subsystems
        self._satellite_mgr.start_all()
        self._ipc.start()

        self._logger.info("Daemon main loop started")

        tick = 0
        while self._running:
            loop_start = time.monotonic()

            try:
                # Hot-reload config every 30 ticks (~30s)
                if tick % 30 == 0:
                    if self._config_mgr.check_and_reload():
                        self._config = self._config_mgr.config
                        self._logger.info("Config hot-reloaded")

                # Process tasks (up to max_concurrent)
                if tick % 1 == 0:
                    await self._process_tasks()

                # Health check satellites every 30 ticks
                if tick % 30 == 0:
                    self._satellite_mgr.health_check()

                # Skill change detection every 60 ticks
                if tick % 60 == 0:
                    changed = self._skill_registry.detect_changes()
                    if changed:
                        self._skill_registry.scan()
                        self._logger.info(f"Skills updated: {changed}")

                # Purge old completed tasks every 3600 ticks (~1h)
                if tick % 3600 == 0 and tick > 0:
                    purged = self._task_queue.purge_completed(older_than_hours=48)
                    if purged > 0:
                        self._logger.info(f"Purged {purged} old tasks")

            except Exception as e:
                if self._logger:
                    self._logger.error(f"Main loop error: {e}", exc_info=True)

            tick += 1

            # Maintain ~1s cycle time
            elapsed = time.monotonic() - loop_start
            sleep_time = max(0.01, 1.0 - elapsed)
            await asyncio.sleep(sleep_time)

        # Shutdown
        self._logger.info("Daemon shutting down...")
        self._ipc.stop()
        self._satellite_mgr.stop_all()
        self._logger.info("Daemon stopped")

    async def _process_tasks(self):
        """Dequeue and process tasks (placeholder — real processing dispatches to handlers)."""
        depth = self._task_queue.depth()
        running = depth.get("running", 0)

        if running >= self._config.max_concurrent_tasks:
            return

        task = self._task_queue.dequeue(worker_id="daemon-core")
        if task is None:
            return

        # TODO: Route to actual task handlers based on task_type
        # For now, just log
        self._logger.info(f"Processing task {task.id}: {task.task_type}")

    def run(self):
        """Start the daemon (blocking)."""
        self._init_subsystems()

        # Handle graceful shutdown
        def signal_handler(sig, frame):
            self._logger.info(f"Signal {sig} received, shutting down...")
            self._running = False

        signal.signal(signal.SIGINT, signal_handler)
        signal.signal(signal.SIGTERM, signal_handler)

        asyncio.run(self._main_loop())


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="LitigationOS Daemon")
    parser.add_argument("--config", type=str, help="Config YAML path")
    args = parser.parse_args()

    daemon = DaemonCore(config_path=args.config)
    daemon.run()
