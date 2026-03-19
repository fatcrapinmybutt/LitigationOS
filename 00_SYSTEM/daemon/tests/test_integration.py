"""
Integration tests for daemon lifecycle and watchdog pipeline.
Tests full daemon startup/shutdown cycle and watchdog → auto-ingest flow.
"""
import os
import sys
import tempfile
import time
import unittest
from unittest.mock import MagicMock, patch

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__)))))

from daemon.models import (
    DaemonConfig, WatchdogConfig, TaskPriority, DriveConfig, DriveRole,
)
from daemon.task_queue import TaskQueue
from daemon.watchdog_engine import WatchdogEngine, FileEvent
from daemon.auto_ingest import AutoIngestEngine
from daemon.storage import StorageResolver
from daemon.skill_registry import SkillRegistry
from daemon.resource_monitor import ResourceMonitor, ResourceSnapshot, ResourceThresholds
from daemon.file_migrator import FileMigrator


class TestDaemonLifecycle(unittest.TestCase):
    """Test daemon startup/shutdown without actually running the async loop."""

    def test_config_loads_defaults(self):
        cfg = DaemonConfig()
        self.assertGreater(len(cfg.drives), 0)
        self.assertIsNotNone(cfg.watchdog)
        self.assertIsNotNone(cfg.scheduler)

    def test_task_queue_lifecycle(self):
        with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
            db_path = f.name

        try:
            queue = TaskQueue(db_path)
            tid = queue.enqueue("lifecycle_test", {"step": "init"})
            self.assertTrue(len(tid) > 0)

            depth = queue.depth()
            self.assertEqual(depth.get("queued", 0), 1)

            task = queue.dequeue()
            self.assertIsNotNone(task)
            self.assertEqual(task.task_type, "lifecycle_test")
        finally:
            os.unlink(db_path)
            for ext in ["-wal", "-shm"]:
                if os.path.exists(db_path + ext):
                    os.unlink(db_path + ext)

    def test_storage_resolver_creates(self):
        cfg = DaemonConfig()
        resolver = StorageResolver(cfg)
        self.assertIsNotNone(resolver)

    def test_storage_metrics(self):
        cfg = DaemonConfig()
        resolver = StorageResolver(cfg)
        metrics = resolver.get_storage_metrics()
        self.assertIn("drives", metrics)
        self.assertIn("health_summary", metrics)
        self.assertIn("total_capacity_gb", metrics)


class TestWatchdogPipeline(unittest.TestCase):
    """Test watchdog → classification → auto-ingest pipeline."""

    def setUp(self):
        self.db_fd, self.db_path = tempfile.mkstemp(suffix=".db")
        self.queue = TaskQueue(self.db_path)

    def tearDown(self):
        os.close(self.db_fd)
        os.unlink(self.db_path)
        for ext in ["-wal", "-shm"]:
            p = self.db_path + ext
            if os.path.exists(p):
                os.unlink(p)

    def test_watchdog_classifies_and_routes(self):
        """Test that watchdog classifies and routes events correctly."""
        config = WatchdogConfig(auto_classify=True, auto_lane_route=True)
        events = []

        def handler(event):
            events.append(event)

        engine = WatchdogEngine(config, on_event=handler)

        # Simulate events
        engine._handle_event(r"C:\custody_motion.pdf", "created")
        engine._handle_event(r"C:\ppo_evidence.pdf", "created")
        engine._handle_event(r"C:\jtc_complaint.pdf", "created")

        self.assertEqual(len(events), 3)
        self.assertEqual(events[0].lane, "A")
        self.assertEqual(events[0].doc_type, "motion")
        self.assertEqual(events[1].lane, "D")
        self.assertEqual(events[1].doc_type, "evidence")
        self.assertEqual(events[2].lane, "E")
        self.assertEqual(events[2].doc_type, "complaint")

    @patch.object(AutoIngestEngine, '_load_known_hashes')
    def test_auto_ingest_enqueues_tasks(self, mock_load):
        """Test auto-ingest creates tasks from watchdog events."""
        mock_load.return_value = None

        ingest = AutoIngestEngine(self.queue)
        ingest._processed_hashes = set()

        # Create a real temp file to process
        with tempfile.NamedTemporaryFile(
            suffix=".pdf", delete=False, mode="wb"
        ) as f:
            f.write(b"x" * 1000)  # >100 bytes
            temp_path = f.name

        try:
            event = FileEvent(path=temp_path, event_type="created")
            event.lane = "A"
            event.doc_type = "motion"

            ingest.handle_event(event)

            depth = self.queue.depth()
            # Should have enqueued classify + OCR + brain_feed tasks
            total = sum(depth.values())
            self.assertGreaterEqual(total, 2)
        finally:
            os.unlink(temp_path)

    @patch.object(AutoIngestEngine, '_load_known_hashes')
    def test_auto_ingest_skips_tiny_files(self, mock_load):
        """Tiny files (<100 bytes) should be skipped."""
        mock_load.return_value = None

        ingest = AutoIngestEngine(self.queue)
        ingest._processed_hashes = set()

        with tempfile.NamedTemporaryFile(
            suffix=".pdf", delete=False, mode="wb"
        ) as f:
            f.write(b"tiny")
            temp_path = f.name

        try:
            event = FileEvent(path=temp_path, event_type="created")
            ingest.handle_event(event)

            depth = self.queue.depth()
            self.assertEqual(sum(depth.values()), 0)
        finally:
            os.unlink(temp_path)


class TestResourceMonitor(unittest.TestCase):
    """Test resource monitor snapshot and alerts."""

    def test_snapshot_creates(self):
        monitor = ResourceMonitor()
        snap = monitor.snapshot()
        self.assertIsInstance(snap, ResourceSnapshot)
        self.assertIsNotNone(snap.timestamp)

    def test_thresholds(self):
        t = ResourceThresholds()
        self.assertEqual(t.cpu_warning, 80.0)
        self.assertEqual(t.ram_critical_percent, 95.0)

    def test_alert_callback(self):
        alerts = []

        def on_alert(severity, message, details):
            alerts.append((severity, message))

        monitor = ResourceMonitor(on_alert=on_alert)
        # Force a critical CPU alert
        snap = ResourceSnapshot(cpu_percent=99.0, ram_percent=50.0)
        monitor._check_alerts(snap)

        self.assertEqual(len(alerts), 1)
        self.assertEqual(alerts[0][0], "critical")


class TestFileMigrator(unittest.TestCase):
    """Test file migration engine."""

    def setUp(self):
        self.db_fd, self.db_path = tempfile.mkstemp(suffix=".db")
        cfg = DaemonConfig()
        self.storage = StorageResolver(cfg)
        self.migrator = FileMigrator(self.storage, self.db_path)

    def tearDown(self):
        os.close(self.db_fd)
        os.unlink(self.db_path)
        for ext in ["-wal", "-shm"]:
            p = self.db_path + ext
            if os.path.exists(p):
                os.unlink(p)

    def test_migration_stats_empty(self):
        stats = self.migrator.get_migration_stats()
        self.assertEqual(stats["total"], 0)
        self.assertEqual(stats["completed"], 0)

    def test_migrate_nonexistent_file(self):
        result = self.migrator.migrate_file(r"C:\nonexistent\file.pdf")
        self.assertFalse(result["success"])
        self.assertIn("not found", result["error"])

    def test_batch_migrate_dry_run(self):
        summary = self.migrator.batch_migrate(dry_run=True)
        self.assertTrue(summary["dry_run"])
        self.assertEqual(summary["migrated"], 0)


if __name__ == "__main__":
    unittest.main()
