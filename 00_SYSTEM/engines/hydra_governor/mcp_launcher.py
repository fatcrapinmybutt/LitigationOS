#!/usr/bin/env python3
"""
MCP Server Auto-Launcher & Watchdog
====================================
Launches all configured MCP servers as background processes.
Monitors them and auto-restarts on crash with exponential backoff.

Usage:
    python mcp_launcher.py                # Launch + monitor all servers
    python mcp_launcher.py --check        # Just check server status
    python mcp_launcher.py --server NAME  # Launch only a specific server

This script is designed to be:
1. Run at Windows startup via Task Scheduler
2. Called by the HYDRA Governor for auto-restart
3. Run manually when needed

It launches MCP servers as DETACHED silent processes (no visible windows).
Logs all events to logs/mcp_launcher.log and mcp_watchdog DB table.
"""

import sys
import os
import json
import subprocess
import time
import logging
import argparse
import sqlite3
from pathlib import Path
from datetime import datetime

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------
LITIGOS_ROOT = Path(__file__).resolve().parents[3]
DB_PATH = LITIGOS_ROOT / "litigation_context.db"
LOG_DIR = LITIGOS_ROOT / "logs"
LOG_DIR.mkdir(exist_ok=True)

MCP_CONFIG = Path.home() / ".copilot" / "mcp.json"

# Logging
log_file = LOG_DIR / "mcp_launcher.log"
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.FileHandler(str(log_file), encoding="utf-8"),
        logging.StreamHandler(sys.stdout),
    ],
)
logger = logging.getLogger("mcp_launcher")


# ---------------------------------------------------------------------------
# Server Definitions
# ---------------------------------------------------------------------------
MCP_SERVERS = {
    "litigation_context": {
        "command": "python",
        "args": [str(LITIGOS_ROOT / "00_SYSTEM" / "mcp_server" / "run_litigation_server.py")],
        "cwd": str(LITIGOS_ROOT),
        "env_extra": {"PYTHONUTF8": "1", "PYTHONDONTWRITEBYTECODE": "1"},
        "max_restarts": 5,
        "backoff_base": 3,
    },
    "command_runner": {
        "command": "python",
        "args": [str(LITIGOS_ROOT / "00_SYSTEM" / "mcp_server" / "run_command_runner.py")],
        "cwd": str(LITIGOS_ROOT),
        "env_extra": {"PYTHONUTF8": "1", "PYTHONDONTWRITEBYTECODE": "1"},
        "max_restarts": 5,
        "backoff_base": 3,
    },
    "agent_memory": {
        "command": "node",
        "args": [
            str(Path.home() / ".agents" / "skills" / "agent-memory"
                / "out" / "mcp-server" / "server.js"),
            "LitigationOS",
            str(LITIGOS_ROOT),
        ],
        "cwd": str(LITIGOS_ROOT),
        "max_restarts": 3,
        "backoff_base": 5,
    },
}


# ---------------------------------------------------------------------------
# Database
# ---------------------------------------------------------------------------
def log_event(server_name, event_type, pid=None, error="", action=""):
    """Log event to mcp_watchdog table."""
    try:
        conn = sqlite3.connect(str(DB_PATH), timeout=5)
        conn.execute("PRAGMA busy_timeout=60000")
        conn.execute("PRAGMA journal_mode=WAL")
        conn.execute("PRAGMA cache_size=-32000")
        conn.execute("""
            CREATE TABLE IF NOT EXISTS mcp_watchdog (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                server_name TEXT NOT NULL,
                event_type TEXT NOT NULL,
                pid INTEGER,
                error_message TEXT,
                action_taken TEXT,
                timestamp TEXT DEFAULT (datetime('now'))
            )
        """)
        conn.execute("""
            INSERT INTO mcp_watchdog
                (server_name, event_type, pid, error_message, action_taken)
            VALUES (?, ?, ?, ?, ?)
        """, (server_name, event_type, pid, error[:500] if error else "", action))
        conn.commit()
        conn.close()
    except Exception as e:
        logger.warning("DB log failed: %s", e)


# ---------------------------------------------------------------------------
# Process Management
# ---------------------------------------------------------------------------
class ServerProcess:
    """Manages a single MCP server process with auto-restart."""

    def __init__(self, name, config):
        self.name = name
        self.config = config
        self.process = None
        self.restart_count = 0
        self.max_restarts = config.get("max_restarts", 5)
        self.backoff_base = config.get("backoff_base", 3)
        self.last_start = None

    def start(self):
        """Launch the server as a detached silent process."""
        cmd = self.config["command"]
        args = self.config["args"]
        cwd = self.config.get("cwd", str(LITIGOS_ROOT))
        env_extra = self.config.get("env_extra", {})
        merged_env = {**os.environ, **env_extra}

        # Verify script exists
        script = args[0] if args else ""
        if not Path(script).exists():
            logger.error("[%s] Script not found: %s", self.name, script)
            log_event(self.name, "start_failed", error="Script not found: {}".format(script))
            return False

        try:
            if os.name == "nt":
                CREATE_NO_WINDOW = 0x08000000
                self.process = subprocess.Popen(
                    [cmd] + args,
                    env=merged_env, cwd=cwd,
                    stdin=subprocess.PIPE,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    creationflags=CREATE_NO_WINDOW,
                )
            else:
                self.process = subprocess.Popen(
                    [cmd] + args,
                    env=merged_env, cwd=cwd,
                    stdin=subprocess.PIPE,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    start_new_session=True,
                )

            self.last_start = time.time()

            # Give it a moment to crash or stabilize
            time.sleep(1.5)

            if self.process.poll() is not None:
                stderr = self.process.stderr.read().decode("utf-8", errors="replace")[:500]
                logger.error("[%s] Crashed immediately (exit %d): %s",
                             self.name, self.process.returncode, stderr)
                log_event(self.name, "crash", self.process.pid, stderr, "start_failed")
                return False

            logger.info("[%s] Started (PID %d)", self.name, self.process.pid)
            log_event(self.name, "start", self.process.pid, action="running")
            return True

        except FileNotFoundError:
            logger.error("[%s] Command '%s' not found", self.name, cmd)
            log_event(self.name, "start_failed", error="{} not found".format(cmd))
            return False
        except Exception as e:
            logger.error("[%s] Start failed: %s", self.name, e)
            log_event(self.name, "start_failed", error=str(e))
            return False

    def is_alive(self):
        """Check if the process is still running."""
        if self.process is None:
            return False
        return self.process.poll() is None

    def get_exit_info(self):
        """Get stderr output from a dead process."""
        if self.process and self.process.poll() is not None:
            try:
                stderr = self.process.stderr.read().decode("utf-8", errors="replace")[:500]
                return self.process.returncode, stderr
            except Exception:
                return self.process.returncode, ""
        return None, ""

    def restart_with_backoff(self):
        """Restart with exponential backoff."""
        if self.restart_count >= self.max_restarts:
            logger.error("[%s] Max restarts (%d) reached. Giving up.",
                         self.name, self.max_restarts)
            log_event(self.name, "max_restarts", action="abandoned")
            return False

        wait_time = self.backoff_base * (2 ** self.restart_count)
        logger.info("[%s] Restart %d/%d in %ds...",
                     self.name, self.restart_count + 1, self.max_restarts, wait_time)
        time.sleep(wait_time)

        self.restart_count += 1
        log_event(self.name, "restart_attempt", action="attempt_{}".format(self.restart_count))
        return self.start()

    def status_dict(self):
        """Get status as a dict."""
        return {
            "name": self.name,
            "alive": self.is_alive(),
            "pid": self.process.pid if self.process else None,
            "restarts": self.restart_count,
            "last_start": self.last_start,
        }


# ---------------------------------------------------------------------------
# Launcher & Monitor
# ---------------------------------------------------------------------------
def launch_all(only_server=None):
    """Launch all MCP servers (or a specific one)."""
    servers = {}
    targets = {only_server: MCP_SERVERS[only_server]} if only_server else MCP_SERVERS

    for name, config in targets.items():
        srv = ServerProcess(name, config)
        if srv.start():
            servers[name] = srv
        else:
            logger.warning("[%s] Initial start failed", name)
            servers[name] = srv

    return servers


def monitor_loop(servers, check_interval=15, duration=0):
    """Monitor servers and auto-restart on crash.

    duration: 0 = run forever, >0 = run for N seconds then exit
    """
    start_time = time.time()
    logger.info("Watchdog monitor active (interval=%ds)", check_interval)

    while True:
        for name, srv in servers.items():
            if not srv.is_alive():
                exit_code, stderr = srv.get_exit_info()
                if exit_code is not None:
                    logger.warning("[%s] Died (exit %s): %s", name, exit_code, stderr[:200])
                    log_event(name, "crash", error=stderr, action="detected")
                    srv.restart_with_backoff()
                elif srv.process is None:
                    srv.start()

        if duration > 0 and (time.time() - start_time) >= duration:
            logger.info("Monitor duration expired (%ds). Exiting.", duration)
            break

        time.sleep(check_interval)


def check_status():
    """Just check and print status of servers."""
    print("=== MCP Server Status Check ===")
    for name, config in MCP_SERVERS.items():
        script = config["args"][0] if config["args"] else "?"
        exists = Path(script).exists()
        print("  {} : script {} : {}".format(
            name, "EXISTS" if exists else "MISSING", script))

    # Check DB watchdog
    try:
        conn = sqlite3.connect(str(DB_PATH), timeout=5)
        conn.execute("PRAGMA busy_timeout=60000")
        conn.execute("PRAGMA journal_mode=WAL")
        conn.execute("PRAGMA cache_size=-32000")
        conn.row_factory = sqlite3.Row
        rows = conn.execute("""
            SELECT server_name, event_type, action_taken, timestamp
            FROM mcp_watchdog ORDER BY timestamp DESC LIMIT 10
        """).fetchall()
        conn.close()
        if rows:
            print("\n=== Recent MCP Watchdog Events ===")
            for r in rows:
                print("  {} | {} | {} | {}".format(
                    r["timestamp"], r["server_name"],
                    r["event_type"], r["action_taken"]))
        else:
            print("\n  No watchdog events yet.")
    except Exception as e:
        print("  DB check failed: {}".format(e))


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------
def main():
    parser = argparse.ArgumentParser(description="MCP Server Auto-Launcher & Watchdog")
    parser.add_argument("--check", action="store_true",
                        help="Just check server status, don't launch")
    parser.add_argument("--server", type=str, default=None,
                        help="Launch only a specific server by name")
    parser.add_argument("--interval", type=int, default=15,
                        help="Health check interval in seconds (default: 15)")
    parser.add_argument("--duration", type=int, default=0,
                        help="Run monitor for N seconds then exit (0=forever)")
    parser.add_argument("--no-monitor", action="store_true",
                        help="Launch servers but don't start monitor loop")
    args = parser.parse_args()

    if args.check:
        check_status()
        return

    if args.server and args.server not in MCP_SERVERS:
        print("Unknown server: {}. Available: {}".format(
            args.server, ", ".join(MCP_SERVERS.keys())))
        sys.exit(1)

    logger.info("=== MCP Launcher starting ===")
    servers = launch_all(only_server=args.server)

    alive = sum(1 for s in servers.values() if s.is_alive())
    total = len(servers)
    logger.info("Launched %d/%d servers successfully", alive, total)

    if args.no_monitor:
        print(json.dumps({
            "launched": alive,
            "total": total,
            "servers": {n: s.status_dict() for n, s in servers.items()},
        }, default=str))
        return

    try:
        monitor_loop(servers, args.interval, args.duration)
    except KeyboardInterrupt:
        logger.info("Watchdog stopped by user")
    finally:
        logger.info("MCP Launcher exiting")


if __name__ == "__main__":
    main()
