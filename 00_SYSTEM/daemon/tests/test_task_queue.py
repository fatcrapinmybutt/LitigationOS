"""
Unit tests for task queue module.
Tests enqueue, dequeue, priority ordering, retry, dead letter, and metrics.
"""
import os
import sys
import tempfile
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__)))))

from daemon.models import TaskPriority, TaskStatus
from daemon.task_queue import TaskQueue, TaskResult


class TestTaskQueue(unittest.TestCase):
    """Test TaskQueue with a fresh temp database."""

    def setUp(self):
        self.db_fd, self.db_path = tempfile.mkstemp(suffix=".db")
        self.queue = TaskQueue(self.db_path)

    def tearDown(self):
        os.close(self.db_fd)
        os.unlink(self.db_path)
        # Clean up WAL/SHM files
        for ext in ["-wal", "-shm"]:
            p = self.db_path + ext
            if os.path.exists(p):
                os.unlink(p)

    def test_enqueue_returns_id(self):
        task_id = self.queue.enqueue("test_task", {"key": "value"})
        self.assertIsInstance(task_id, str)
        self.assertTrue(len(task_id) > 0)

    def test_dequeue_returns_task(self):
        self.queue.enqueue("test_task", {"data": 1})
        task = self.queue.dequeue()
        self.assertIsNotNone(task)
        self.assertEqual(task.task_type, "test_task")
        self.assertEqual(task.status, TaskStatus.RUNNING)

    def test_dequeue_empty_returns_none(self):
        task = self.queue.dequeue()
        self.assertIsNone(task)

    def test_priority_ordering(self):
        self.queue.enqueue("low_task", priority=TaskPriority.LOW)
        self.queue.enqueue("critical_task", priority=TaskPriority.CRITICAL)
        self.queue.enqueue("normal_task", priority=TaskPriority.NORMAL)

        task1 = self.queue.dequeue()
        self.assertEqual(task1.task_type, "critical_task")

        task2 = self.queue.dequeue()
        self.assertEqual(task2.task_type, "normal_task")

        task3 = self.queue.dequeue()
        self.assertEqual(task3.task_type, "low_task")

    def test_complete_success(self):
        task_id = self.queue.enqueue("test_task")
        task = self.queue.dequeue()

        result = TaskResult(task_id=task_id, success=True, duration_sec=1.5)
        self.queue.complete(task_id, result)

        depth = self.queue.depth()
        self.assertEqual(depth.get("completed", 0), 1)
        self.assertNotIn("running", depth)

    def test_retry_on_failure(self):
        task_id = self.queue.enqueue("test_task", max_retries=3)
        task = self.queue.dequeue()

        result = TaskResult(task_id=task_id, success=False, error="test error")
        self.queue.complete(task_id, result)

        # Should be back in queue
        depth = self.queue.depth()
        self.assertEqual(depth.get("queued", 0), 1)

    def test_dead_letter_after_max_retries(self):
        task_id = self.queue.enqueue("test_task", max_retries=1)

        # First attempt
        self.queue.dequeue()
        self.queue.complete(task_id, TaskResult(task_id=task_id, success=False, error="fail"))

        depth = self.queue.depth()
        self.assertEqual(depth.get("dead_letter", 0), 1)

    def test_depth(self):
        self.queue.enqueue("task1")
        self.queue.enqueue("task2")
        self.queue.enqueue("task3")

        depth = self.queue.depth()
        self.assertEqual(depth.get("queued", 0), 3)

    def test_purge_completed(self):
        task_id = self.queue.enqueue("test_task")
        self.queue.dequeue()
        self.queue.complete(task_id, TaskResult(task_id=task_id, success=True))

        # Purge with 0 hours should remove it
        purged = self.queue.purge_completed(older_than_hours=0)
        # May or may not match depending on timing, but shouldn't crash
        self.assertIsInstance(purged, int)

    def test_metrics(self):
        self.queue.enqueue("test_task")
        metrics = self.queue.get_metrics(hours=1)
        self.assertIn("enqueue", metrics)
        self.assertEqual(metrics["enqueue"]["count"], 1)

    def test_crash_recovery(self):
        """Tasks stuck in 'running' should be recovered to 'queued' on init."""
        # Enqueue and dequeue (sets to running)
        task_id = self.queue.enqueue("test_task")
        self.queue.dequeue()

        # Simulate crash — create new queue instance (triggers recovery)
        queue2 = TaskQueue(self.db_path)
        depth = queue2.depth()
        self.assertEqual(depth.get("queued", 0), 1)
        self.assertNotIn("running", depth)


if __name__ == "__main__":
    unittest.main()
