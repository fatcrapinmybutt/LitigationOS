"""Silent background script execution engine for LitigationOS."""

import logging
import os
import subprocess
import sys
import threading
import queue
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Callable, List, Optional


@dataclass
class ScriptResult:
    """Result of a single script execution."""

    script_path: str
    exit_code: int
    stdout: str
    stderr: str
    duration: float
    started_at: str
    completed_at: str

    @property
    def success(self) -> bool:
        return self.exit_code == 0


class ScriptRunner:
    """Run Python scripts silently in background threads.

    Designed for LitigationOS pipeline and automation tasks that need to
    execute scripts without blocking the GUI or main thread.
    """

    def __init__(
        self,
        python_path: Optional[str] = None,
        cwd: Optional[str] = None,
        max_concurrent: int = 3,
    ):
        self.python_path = python_path or sys.executable
        self.cwd = cwd or str(Path(__file__).parents[4])  # LitigationOS root
        self.max_concurrent = max_concurrent
        self._results: queue.Queue[ScriptResult] = queue.Queue()
        self._active: List[threading.Thread] = []
        self._lock = threading.Lock()
        self.logger = logging.getLogger("ScriptRunner")

    def _execute(
        self,
        script_path: str,
        args: Optional[List[str]] = None,
        timeout: Optional[int] = None,
    ) -> ScriptResult:
        """Execute a single script and return its result."""
        cmd = [self.python_path, script_path] + (args or [])
        started = datetime.now(timezone.utc)
        started_str = started.isoformat()

        env = os.environ.copy()
        env["PYTHONUTF8"] = "1"

        try:
            proc = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                encoding="utf-8",
                errors="replace",
                cwd=self.cwd,
                env=env,
                timeout=timeout,
            )
            completed = datetime.now(timezone.utc)
            duration = (completed - started).total_seconds()

            return ScriptResult(
                script_path=script_path,
                exit_code=proc.returncode,
                stdout=proc.stdout,
                stderr=proc.stderr,
                duration=duration,
                started_at=started_str,
                completed_at=completed.isoformat(),
            )
        except subprocess.TimeoutExpired:
            completed = datetime.now(timezone.utc)
            duration = (completed - started).total_seconds()
            self.logger.warning("Script timed out after %.1fs: %s", duration, script_path)
            return ScriptResult(
                script_path=script_path,
                exit_code=-1,
                stdout="",
                stderr=f"Timed out after {duration:.1f}s",
                duration=duration,
                started_at=started_str,
                completed_at=completed.isoformat(),
            )
        except Exception as exc:
            completed = datetime.now(timezone.utc)
            duration = (completed - started).total_seconds()
            self.logger.error("Script execution error: %s — %s", script_path, exc)
            return ScriptResult(
                script_path=script_path,
                exit_code=-2,
                stdout="",
                stderr=str(exc),
                duration=duration,
                started_at=started_str,
                completed_at=completed.isoformat(),
            )

    def run_silent(
        self,
        script_path: str,
        args: Optional[List[str]] = None,
        callback: Optional[Callable[[ScriptResult], None]] = None,
    ) -> threading.Thread:
        """Run script in background thread, optionally call back on completion.

        Args:
            script_path: Path to the Python script.
            args: Command-line arguments for the script.
            callback: Optional function called with the ScriptResult on completion.

        Returns:
            The background Thread (already started).
        """

        def _worker():
            result = self._execute(script_path, args)
            self._results.put(result)
            with self._lock:
                if t in self._active:
                    self._active.remove(t)
            if callback is not None:
                try:
                    callback(result)
                except Exception as cb_exc:
                    self.logger.error("Callback error for %s: %s", script_path, cb_exc)

        t = threading.Thread(target=_worker, daemon=True, name=f"script-{Path(script_path).stem}")
        with self._lock:
            self._active.append(t)
        t.start()
        return t

    def run_and_wait(
        self,
        script_path: str,
        args: Optional[List[str]] = None,
        timeout: int = 300,
    ) -> ScriptResult:
        """Run script synchronously and wait for the result.

        Args:
            script_path: Path to the Python script.
            args: Command-line arguments for the script.
            timeout: Maximum seconds to wait (default 300).

        Returns:
            ScriptResult with exit code, stdout, stderr, and timing.
        """
        result = self._execute(script_path, args, timeout=timeout)
        self._results.put(result)
        self.logger.info(
            "Script %s completed (exit=%d, %.1fs)",
            script_path,
            result.exit_code,
            result.duration,
        )
        return result

    def run_batch(
        self,
        scripts: List[str],
        max_parallel: int = 3,
    ) -> List[ScriptResult]:
        """Run multiple scripts with concurrency limit.

        Args:
            scripts: List of script paths to execute.
            max_parallel: Max simultaneous scripts (default 3).

        Returns:
            List of ScriptResult in completion order.
        """
        effective_parallel = min(max_parallel, self.max_concurrent)
        results: List[ScriptResult] = []

        with ThreadPoolExecutor(max_workers=effective_parallel) as pool:
            futures = {
                pool.submit(self._execute, script): script for script in scripts
            }
            for future in as_completed(futures):
                script = futures[future]
                try:
                    result = future.result()
                except Exception as exc:
                    self.logger.error("Batch script failed: %s — %s", script, exc)
                    result = ScriptResult(
                        script_path=script,
                        exit_code=-3,
                        stdout="",
                        stderr=str(exc),
                        duration=0.0,
                        started_at=datetime.now(timezone.utc).isoformat(),
                        completed_at=datetime.now(timezone.utc).isoformat(),
                    )
                results.append(result)
                self._results.put(result)

        self.logger.info(
            "Batch complete: %d/%d succeeded",
            sum(1 for r in results if r.success),
            len(results),
        )
        return results

    def get_results(self) -> List[ScriptResult]:
        """Get all completed results accumulated so far.

        Returns:
            List of ScriptResult (drains the internal queue).
        """
        results: List[ScriptResult] = []
        while True:
            try:
                results.append(self._results.get_nowait())
            except queue.Empty:
                break
        return results
