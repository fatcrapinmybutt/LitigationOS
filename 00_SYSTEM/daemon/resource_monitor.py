"""
Resource Monitor for LitigationOS Daemon.
Tracks CPU, RAM, disk I/O, and process health.
Enforces resource caps on satellites.
Triggers alerts when thresholds are exceeded.
"""
import logging
import os
import sys
import time
import threading
from dataclasses import dataclass, field
from datetime import datetime
from typing import Callable, Optional

logger = logging.getLogger("daemon.resource_monitor")


@dataclass
class ResourceSnapshot:
    """Point-in-time system resource snapshot."""
    timestamp: datetime = field(default_factory=datetime.utcnow)
    cpu_percent: float = 0.0
    ram_total_mb: float = 0.0
    ram_used_mb: float = 0.0
    ram_available_mb: float = 0.0
    ram_percent: float = 0.0
    disk_read_mb: float = 0.0
    disk_write_mb: float = 0.0
    process_count: int = 0
    daemon_ram_mb: float = 0.0
    daemon_cpu_percent: float = 0.0
    satellite_resources: dict = field(default_factory=dict)


@dataclass
class ResourceThresholds:
    """Alert thresholds for resource usage."""
    cpu_warning: float = 80.0
    cpu_critical: float = 95.0
    ram_warning_percent: float = 85.0
    ram_critical_percent: float = 95.0
    disk_warning_gb: float = 5.0
    disk_critical_gb: float = 2.0
    satellite_max_ram_mb: float = 4096.0
    satellite_max_cpu: float = 100.0


class ResourceMonitor:
    """Monitors system resources and enforces satellite caps."""

    def __init__(self, thresholds: ResourceThresholds = None,
                 check_interval_sec: float = 30.0,
                 on_alert: Callable[[str, str, dict], None] = None):
        self.thresholds = thresholds or ResourceThresholds()
        self.check_interval = check_interval_sec
        self.on_alert = on_alert
        self._running = False
        self._thread: Optional[threading.Thread] = None
        self._history: list[ResourceSnapshot] = []
        self._max_history = 120  # ~1hr at 30s intervals
        self._psutil_available = False

        try:
            import psutil  # noqa: F401
            self._psutil_available = True
        except ImportError:
            logger.warning("psutil not installed — resource monitoring limited. Install: pip install psutil")

    def start(self):
        """Start background resource monitoring."""
        self._running = True
        self._thread = threading.Thread(target=self._monitor_loop, daemon=True)
        self._thread.start()
        logger.info("Resource monitor started")

    def stop(self):
        """Stop monitoring."""
        self._running = False
        if self._thread:
            self._thread.join(timeout=10)
        logger.info("Resource monitor stopped")

    def snapshot(self) -> ResourceSnapshot:
        """Take a current resource snapshot."""
        snap = ResourceSnapshot()

        if not self._psutil_available:
            return self._basic_snapshot(snap)

        import psutil

        # System-wide metrics
        snap.cpu_percent = psutil.cpu_percent(interval=0.5)
        mem = psutil.virtual_memory()
        snap.ram_total_mb = mem.total / (1024 ** 2)
        snap.ram_used_mb = mem.used / (1024 ** 2)
        snap.ram_available_mb = mem.available / (1024 ** 2)
        snap.ram_percent = mem.percent

        # Disk I/O
        try:
            disk = psutil.disk_io_counters()
            if disk:
                snap.disk_read_mb = disk.read_bytes / (1024 ** 2)
                snap.disk_write_mb = disk.write_bytes / (1024 ** 2)
        except Exception:
            pass

        # Current process (daemon)
        try:
            proc = psutil.Process(os.getpid())
            snap.daemon_ram_mb = proc.memory_info().rss / (1024 ** 2)
            snap.daemon_cpu_percent = proc.cpu_percent(interval=0.1)
        except Exception:
            pass

        snap.process_count = len(psutil.pids())
        return snap

    def _basic_snapshot(self, snap: ResourceSnapshot) -> ResourceSnapshot:
        """Fallback snapshot without psutil — uses OS-level info."""
        if sys.platform == "win32":
            try:
                import ctypes
                kernel32 = ctypes.windll.kernel32
                mem_status = ctypes.c_ulonglong()

                class MEMORYSTATUSEX(ctypes.Structure):
                    _fields_ = [
                        ("dwLength", ctypes.c_ulong),
                        ("dwMemoryLoad", ctypes.c_ulong),
                        ("ullTotalPhys", ctypes.c_ulonglong),
                        ("ullAvailPhys", ctypes.c_ulonglong),
                        ("ullTotalPageFile", ctypes.c_ulonglong),
                        ("ullAvailPageFile", ctypes.c_ulonglong),
                        ("ullTotalVirtual", ctypes.c_ulonglong),
                        ("ullAvailVirtual", ctypes.c_ulonglong),
                        ("ullAvailExtendedVirtual", ctypes.c_ulonglong),
                    ]

                stat = MEMORYSTATUSEX()
                stat.dwLength = ctypes.sizeof(MEMORYSTATUSEX)
                kernel32.GlobalMemoryStatusEx(ctypes.byref(stat))

                snap.ram_total_mb = stat.ullTotalPhys / (1024 ** 2)
                snap.ram_available_mb = stat.ullAvailPhys / (1024 ** 2)
                snap.ram_used_mb = snap.ram_total_mb - snap.ram_available_mb
                snap.ram_percent = stat.dwMemoryLoad
            except Exception:
                pass
        return snap

    def check_satellite_resources(self, satellites: dict) -> list[dict]:
        """Check if any satellites exceed resource caps. Returns violations."""
        if not self._psutil_available:
            return []

        import psutil
        violations = []

        for name, pid in satellites.items():
            if pid is None:
                continue
            try:
                proc = psutil.Process(pid)
                ram_mb = proc.memory_info().rss / (1024 ** 2)
                cpu_pct = proc.cpu_percent(interval=0.1)

                if ram_mb > self.thresholds.satellite_max_ram_mb:
                    violations.append({
                        "satellite": name, "pid": pid,
                        "type": "ram_exceeded",
                        "value": round(ram_mb, 1),
                        "limit": self.thresholds.satellite_max_ram_mb,
                    })

                if cpu_pct > self.thresholds.satellite_max_cpu:
                    violations.append({
                        "satellite": name, "pid": pid,
                        "type": "cpu_exceeded",
                        "value": round(cpu_pct, 1),
                        "limit": self.thresholds.satellite_max_cpu,
                    })
            except Exception:
                pass

        return violations

    def get_history(self, minutes: int = 60) -> list[ResourceSnapshot]:
        """Get recent resource history."""
        cutoff = time.time() - (minutes * 60)
        return [s for s in self._history if s.timestamp.timestamp() > cutoff]

    def _monitor_loop(self):
        """Background monitoring loop."""
        while self._running:
            try:
                snap = self.snapshot()
                self._history.append(snap)

                # Trim history
                if len(self._history) > self._max_history:
                    self._history = self._history[-self._max_history:]

                # Check thresholds
                self._check_alerts(snap)

            except Exception as e:
                logger.error(f"Resource monitor error: {e}")

            time.sleep(self.check_interval)

    def _check_alerts(self, snap: ResourceSnapshot):
        """Check resource thresholds and fire alerts."""
        t = self.thresholds

        if snap.cpu_percent >= t.cpu_critical:
            self._fire_alert("critical", "CPU critical", {
                "cpu_percent": snap.cpu_percent, "threshold": t.cpu_critical
            })
        elif snap.cpu_percent >= t.cpu_warning:
            self._fire_alert("warning", "CPU high", {
                "cpu_percent": snap.cpu_percent, "threshold": t.cpu_warning
            })

        if snap.ram_percent >= t.ram_critical_percent:
            self._fire_alert("critical", "RAM critical", {
                "ram_percent": snap.ram_percent,
                "available_mb": round(snap.ram_available_mb, 0),
            })
        elif snap.ram_percent >= t.ram_warning_percent:
            self._fire_alert("warning", "RAM high", {
                "ram_percent": snap.ram_percent,
                "available_mb": round(snap.ram_available_mb, 0),
            })

    def _fire_alert(self, severity: str, message: str, details: dict):
        """Fire an alert to the callback and log."""
        logger.log(
            logging.CRITICAL if severity == "critical" else logging.WARNING,
            f"Resource alert [{severity}]: {message} — {details}"
        )
        if self.on_alert:
            try:
                self.on_alert(severity, message, details)
            except Exception as e:
                logger.error(f"Alert callback error: {e}")
