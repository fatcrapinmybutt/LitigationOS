"""
Unit tests for daemon core module.
Tests DaemonCore initialization, config loading, health reporting, and main loop mechanics.
"""
import os
import sys
import tempfile
import unittest
from unittest.mock import MagicMock, patch

# Ensure daemon package is importable
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__)))))

from daemon.models import DaemonConfig, DaemonHealth
from daemon.core import DaemonCore


class TestDaemonConfig(unittest.TestCase):
    """Test DaemonConfig model defaults and validation."""

    def test_default_config(self):
        cfg = DaemonConfig()
        self.assertEqual(cfg.version, "1.0.0")
        self.assertEqual(len(cfg.drives), 6)
        self.assertEqual(cfg.max_concurrent_tasks, 3)
        self.assertEqual(cfg.task_timeout_sec, 300)

    def test_drive_roles(self):
        cfg = DaemonConfig()
        roles = {d.role.value for d in cfg.drives}
        self.assertIn("primary", roles)
        self.assertIn("heavy", roles)
        self.assertIn("lite", roles)

    def test_path_normalization(self):
        cfg = DaemonConfig(db_path="C:/some/path/db.sqlite")
        self.assertIn("\\", cfg.db_path)  # Windows normalized


class TestDaemonHealth(unittest.TestCase):
    """Test DaemonHealth model."""

    def test_health_defaults(self):
        h = DaemonHealth()
        self.assertEqual(h.status, "healthy")
        self.assertEqual(h.uptime_sec, 0.0)
        self.assertEqual(h.task_queue_depth, 0)
        self.assertIsNotNone(h.timestamp)

    def test_health_with_values(self):
        h = DaemonHealth(
            status="running",
            uptime_sec=3600.0,
            task_queue_depth=5,
            running_tasks=2,
            completed_tasks_24h=100,
        )
        self.assertEqual(h.uptime_sec, 3600.0)
        self.assertEqual(h.completed_tasks_24h, 100)


class TestDaemonCoreInit(unittest.TestCase):
    """Test DaemonCore initialization."""

    def test_core_creates(self):
        core = DaemonCore()
        self.assertIsNotNone(core)
        self.assertFalse(core._running)

    def test_core_with_config(self):
        with tempfile.NamedTemporaryFile(suffix=".yaml", delete=False, mode="w") as f:
            f.write("version: '2.0.0'\nmax_concurrent_tasks: 5\n")
            f.flush()
            path = f.name

        try:
            core = DaemonCore(config_path=path)
            self.assertIsNotNone(core._config)
        finally:
            os.unlink(path)

    def test_health_when_not_running(self):
        core = DaemonCore()
        # _get_health works even before subsystems are initialized
        health = core._get_health()
        self.assertEqual(health.status, "stopped")
        self.assertEqual(health.uptime_sec, 0.0)


class TestDaemonCoreIPC(unittest.TestCase):
    """Test IPC handler registration."""

    def test_ipc_handlers_registered(self):
        core = DaemonCore()
        # Mock subsystems
        core._logger = MagicMock()
        core._task_queue = MagicMock()
        core._task_queue.depth.return_value = {}
        core._satellite_mgr = MagicMock()
        core._skill_registry = MagicMock()
        core._skill_registry.list_all.return_value = []
        core._storage = MagicMock()
        core._storage.get_all_drive_health.return_value = []
        core._ipc = MagicMock()

        core._register_ipc_handlers()

        # Verify key handlers were registered
        calls = core._ipc.register.call_args_list
        methods = [c[0][0] for c in calls]
        self.assertIn("ping", methods)
        self.assertIn("status", methods)
        self.assertIn("shutdown", methods)
        self.assertIn("enqueue", methods)
        self.assertIn("skills", methods)
        self.assertIn("drives", methods)


if __name__ == "__main__":
    unittest.main()
