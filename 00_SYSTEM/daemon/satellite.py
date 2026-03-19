"""
Satellite Process Manager for LitigationOS Daemon.
Launches, monitors, and recovers isolated satellite processes.

Satellites are fault-isolated heavy processes (Legal AI, MANBEARPIG v10, etc.)
that communicate with the core daemon via task queue and named pipes.
"""
import json
import os
import subprocess
import sys
import threading
import time
from datetime import datetime
from typing import Optional

from .models import SatelliteConfig, SatelliteHealth, SatelliteStatus


class SatelliteProcess:
    """Manages a single satellite process lifecycle."""

    def __init__(self, config: SatelliteConfig, logger=None):
        self.config = config
        self.logger = logger
        self._process: Optional[subprocess.Popen] = None
        self._status = SatelliteStatus.STOPPED
        self._start_time: Optional[datetime] = None
        self._last_heartbeat: Optional[datetime] = None
        self._crash_count = 0
        self._restart_index = 0

    @property
    def status(self) -> SatelliteStatus:
        if self._process is None:
            return SatelliteStatus.STOPPED
        poll = self._process.poll()
        if poll is not None:
            if self._status == SatelliteStatus.RUNNING:
                self._status = SatelliteStatus.CRASHED
                self._crash_count += 1
            return self._status
        return self._status

    @property
    def pid(self) -> Optional[int]:
        return self._process.pid if self._process else None

    def start(self) -> bool:
        """Start the satellite process."""
        if self._process and self._process.poll() is None:
            return True  # Already running

        cmd = [self.config.command] + self.config.args
        cwd = self.config.cwd or os.getcwd()

        try:
            self._process = subprocess.Popen(
                cmd,
                cwd=cwd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                creationflags=subprocess.CREATE_NEW_PROCESS_GROUP
                if sys.platform == "win32" else 0,
            )
            self._status = SatelliteStatus.STARTING
            self._start_time = datetime.utcnow()
            self._last_heartbeat = datetime.utcnow()

            # Wait briefly to confirm it didn't crash on startup
            time.sleep(1)
            if self._process.poll() is not None:
                self._status = SatelliteStatus.CRASHED
                self._crash_count += 1
                if self.logger:
                    self.logger.error(f"Satellite {self.config.name} crashed on startup")
                return False

            self._status = SatelliteStatus.RUNNING
            if self.logger:
                self.logger.info(
                    f"Satellite {self.config.name} started (PID {self._process.pid})"
                )
            return True

        except Exception as e:
            self._status = SatelliteStatus.CRASHED
            self._crash_count += 1
            if self.logger:
                self.logger.error(f"Failed to start satellite {self.config.name}: {e}")
            return False

    def stop(self, timeout: int = 10) -> bool:
        """Stop the satellite process gracefully."""
        if self._process is None or self._process.poll() is not None:
            self._status = SatelliteStatus.STOPPED
            return True

        try:
            self._process.terminate()
            try:
                self._process.wait(timeout=timeout)
            except subprocess.TimeoutExpired:
                self._process.kill()
                self._process.wait(timeout=5)

            self._status = SatelliteStatus.STOPPED
            if self.logger:
                self.logger.info(f"Satellite {self.config.name} stopped")
            return True

        except Exception as e:
            if self.logger:
                self.logger.error(f"Error stopping satellite {self.config.name}: {e}")
            return False

    def restart(self) -> bool:
        """Restart with exponential backoff."""
        self.stop()

        backoffs = self.config.restart_backoff_sec
        delay = backoffs[min(self._restart_index, len(backoffs) - 1)]
        self._restart_index += 1

        if self.logger:
            self.logger.info(
                f"Restarting satellite {self.config.name} in {delay}s "
                f"(attempt {self._restart_index})"
            )
        time.sleep(delay)
        return self.start()

    def health(self) -> SatelliteHealth:
        """Get satellite health snapshot."""
        ram_mb = 0.0
        cpu_pct = 0.0

        if self._process and self._process.poll() is None:
            try:
                import psutil
                proc = psutil.Process(self._process.pid)
                mem = proc.memory_info()
                ram_mb = mem.rss / (1024 * 1024)
                cpu_pct = proc.cpu_percent(interval=0.1)
            except Exception:
                pass

        uptime = 0.0
        if self._start_time and self.status == SatelliteStatus.RUNNING:
            uptime = (datetime.utcnow() - self._start_time).total_seconds()

        return SatelliteHealth(
            name=self.config.name,
            status=self.status,
            pid=self.pid,
            ram_mb=round(ram_mb, 1),
            cpu_percent=round(cpu_pct, 1),
            uptime_sec=round(uptime, 0),
            last_heartbeat=self._last_heartbeat,
            crash_count=self._crash_count,
        )

    def record_heartbeat(self):
        """Record a heartbeat from the satellite."""
        self._last_heartbeat = datetime.utcnow()
        self._restart_index = 0  # Reset backoff on successful heartbeat

    def is_healthy(self) -> bool:
        """Check if satellite is responding within heartbeat window."""
        if self.status != SatelliteStatus.RUNNING:
            return False
        if self._last_heartbeat is None:
            return False
        elapsed = (datetime.utcnow() - self._last_heartbeat).total_seconds()
        max_gap = self.config.heartbeat_interval_sec * self.config.max_missed_heartbeats
        return elapsed < max_gap


class SatelliteManager:
    """Manages all satellite processes."""

    def __init__(self, configs: list[SatelliteConfig], logger=None):
        self.logger = logger
        self._satellites: dict[str, SatelliteProcess] = {}
        for cfg in configs:
            self._satellites[cfg.name] = SatelliteProcess(cfg, logger)

    def start_all(self):
        """Start all auto-start satellites."""
        for name, sat in self._satellites.items():
            if sat.config.auto_start:
                sat.start()

    def stop_all(self):
        """Stop all satellites."""
        for sat in self._satellites.values():
            sat.stop()

    def health_check(self) -> list[SatelliteHealth]:
        """Check all satellites, restart unhealthy ones."""
        results = []
        for name, sat in self._satellites.items():
            health = sat.health()
            if sat.config.auto_start and not sat.is_healthy():
                if sat.status in (SatelliteStatus.CRASHED, SatelliteStatus.UNHEALTHY):
                    if self.logger:
                        self.logger.warning(f"Satellite {name} unhealthy, restarting")
                    sat.restart()
                    health = sat.health()
            results.append(health)
        return results

    def get(self, name: str) -> Optional[SatelliteProcess]:
        return self._satellites.get(name)

    def send_command(self, name: str, command: str, payload: dict = None) -> dict:
        """Send a command to a satellite via its IPC channel (stdin JSON-RPC).

        Satellites listen on stdin for JSON-RPC commands.
        This is the core satellite IPC mechanism.
        """
        sat = self._satellites.get(name)
        if sat is None:
            return {"success": False, "error": f"Unknown satellite: {name}"}

        if sat.status != SatelliteStatus.RUNNING:
            return {"success": False, "error": f"Satellite {name} not running (status: {sat.status.value})"}

        if sat._process is None or sat._process.stdin is None:
            return {"success": False, "error": f"Satellite {name} has no stdin pipe"}

        import json
        import uuid

        request = {
            "jsonrpc": "2.0",
            "id": str(uuid.uuid4()),
            "method": command,
            "params": payload or {},
        }

        try:
            msg = json.dumps(request) + "\n"
            sat._process.stdin.write(msg.encode("utf-8"))
            sat._process.stdin.flush()

            # Read response (with timeout)
            import select
            if sys.platform == "win32":
                # Windows: use threading with timeout
                response_line = None

                def _read():
                    nonlocal response_line
                    try:
                        response_line = sat._process.stdout.readline()
                    except Exception:
                        pass

                t = threading.Thread(target=_read, daemon=True)
                t.start()
                t.join(timeout=10)

                if response_line:
                    resp = json.loads(response_line.decode("utf-8"))
                    return {"success": True, "response": resp}
                return {"success": False, "error": "Timeout waiting for satellite response"}
            else:
                # Unix: use select
                ready, _, _ = select.select([sat._process.stdout], [], [], 10)
                if ready:
                    response_line = sat._process.stdout.readline()
                    resp = json.loads(response_line.decode("utf-8"))
                    return {"success": True, "response": resp}
                return {"success": False, "error": "Timeout"}

        except Exception as e:
            if self.logger:
                self.logger.error(f"Satellite IPC error ({name}): {e}")
            return {"success": False, "error": str(e)}

    def broadcast(self, command: str, payload: dict = None) -> dict:
        """Send a command to all running satellites."""
        results = {}
        for name, sat in self._satellites.items():
            if sat.status == SatelliteStatus.RUNNING:
                results[name] = self.send_command(name, command, payload)
        return results
