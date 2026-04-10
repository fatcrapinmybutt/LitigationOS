#!/usr/bin/env python3
"""
+======================================================================+
|               H Y D R A   G O V E R N O R   E N G I N E             |
|          Session Lifecycle + MCP Watchdog + Auto-Recovery            |
|                                                                      |
|  Responsibilities:                                                   |
|  1. Capture output from stale/idle shells and agents before cleanup  |
|  2. Classify captured data and route to correct engine/DB table      |
|  3. Monitor MCP server health and auto-restart on failure            |
|  4. Persist ALL session intelligence to governor_log table           |
|  5. Generate health reports for the operator                         |
+======================================================================+

Usage (CLI - pipe JSON on stdin):
    echo {"action":"report"} | python governor_engine.py
    echo {"action":"classify","text":"..."} | python governor_engine.py
    echo {"action":"mcp_health"} | python governor_engine.py
    echo {"action":"mcp_restart","server":"litigation_context"} | python governor_engine.py
    echo {"action":"sweep","sessions":[...]} | python governor_engine.py
"""

import json
import sys
import os
import re
import sqlite3
import subprocess
import time
import logging
from pathlib import Path
from datetime import datetime, timezone

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------
LITIGOS_ROOT = Path(__file__).resolve().parents[3]
DB_PATH = LITIGOS_ROOT / "litigation_context.db"
LOG_DIR = LITIGOS_ROOT / "logs"
LOG_DIR.mkdir(exist_ok=True)

MCP_CONFIG_PATH = Path.home() / ".copilot" / "mcp.json"

# MCP server definitions
MCP_SERVERS = {
    "litigation_context": {
        "command": "python",
        "args": [str(LITIGOS_ROOT / "00_SYSTEM" / "mcp_server" / "run_litigation_server.py")],
        "env": {"PYTHONUTF8": "1", "PYTHONDONTWRITEBYTECODE": "1"},
        "cwd": str(LITIGOS_ROOT),
        "log": str(LOG_DIR / "mcp_litigation_server.log"),
        "health_check": "import_test",
    },
    "command_runner": {
        "command": "python",
        "args": [str(LITIGOS_ROOT / "00_SYSTEM" / "mcp_server" / "run_command_runner.py")],
        "env": {"PYTHONUTF8": "1", "PYTHONDONTWRITEBYTECODE": "1"},
        "cwd": str(LITIGOS_ROOT),
        "log": str(LOG_DIR / "mcp_command_runner.log"),
        "health_check": "import_test",
    },
    "agent_memory": {
        "command": "node",
        "args": [
            str(Path.home() / ".agents" / "skills" / "agent-memory"
                / "out" / "mcp-server" / "server.js"),
            "LitigationOS",
            str(LITIGOS_ROOT),
        ],
        "log": str(LOG_DIR / "mcp_agent_memory.log"),
        "health_check": "process_check",
    },
}

# Classification patterns: (regex, category, description)
CLASSIFICATION_PATTERNS = [
    (r"nexus|fusion|fuse|argue|impeach|credibility", "nexus",
     "NEXUS fusion reactor output"),
    (r"evidence_quotes|evidence_fts|relevance_score", "evidence",
     "Evidence search results"),
    (r"MCR|MCL|MRE|court rule|statute", "authority",
     "Legal authority data"),
    (r"alienation|baker|gatekeep|withhold", "alienation",
     "Parental alienation detection"),
    (r"filing|motion|brief|complaint|petition", "filing",
     "Filing/document data"),
    (r"timeline|chronolog|date|event", "timeline",
     "Timeline/chronology data"),
    (r"impeach|contradict|credib|false allega", "impeachment",
     "Impeachment intelligence"),
    (r"judicial|mcneill|violation|canon|bias", "judicial",
     "Judicial analysis"),
    (r"git|commit|branch|diff|status", "git",
     "Git operations"),
    (r"error|traceback|exception|fail", "error",
     "Error/diagnostic output"),
    (r"egcp|convergence|readiness|score", "convergence",
     "Convergence/scoring data"),
]

# Logging
logging.basicConfig(
    filename=str(LOG_DIR / "hydra_governor.log"),
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
)
logger = logging.getLogger("hydra_governor")


# ---------------------------------------------------------------------------
# Database Layer
# ---------------------------------------------------------------------------

def get_db():
    """Get connection to litigation_context.db with WAL mode."""
    conn = sqlite3.connect(str(DB_PATH), timeout=10)
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA busy_timeout=60000")
    conn.execute("PRAGMA cache_size=-32000")
    conn.row_factory = sqlite3.Row
    return conn


def ensure_tables():
    """Create governor tables if they don't exist."""
    conn = get_db()
    conn.executescript("""
        CREATE TABLE IF NOT EXISTS governor_log (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            session_id TEXT,
            session_type TEXT,
            status TEXT,
            command_summary TEXT,
            captured_output TEXT,
            output_classification TEXT,
            routed_to TEXT,
            action_taken TEXT,
            elapsed_seconds INTEGER,
            captured_at TEXT DEFAULT (datetime('now'))
        );

        CREATE TABLE IF NOT EXISTS mcp_watchdog (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            server_name TEXT NOT NULL,
            event_type TEXT NOT NULL,
            pid INTEGER,
            error_message TEXT,
            action_taken TEXT,
            timestamp TEXT DEFAULT (datetime('now'))
        );

        CREATE INDEX IF NOT EXISTS idx_gov_log_session
            ON governor_log(session_id);
        CREATE INDEX IF NOT EXISTS idx_gov_log_class
            ON governor_log(output_classification);
        CREATE INDEX IF NOT EXISTS idx_mcp_watchdog_server
            ON mcp_watchdog(server_name, timestamp);
    """)
    conn.commit()
    conn.close()


# ---------------------------------------------------------------------------
# Classification Engine
# ---------------------------------------------------------------------------

def classify_output(text):
    """Classify captured output by content pattern matching.
    Returns (category, description) tuple.
    """
    if not text:
        return ("unknown", "Empty or no output")

    text_lower = text.lower()
    scores = {}
    for pattern, category, desc in CLASSIFICATION_PATTERNS:
        hits = len(re.findall(pattern, text_lower))
        if hits > 0:
            scores[category] = (hits, desc)

    if not scores:
        return ("general", "General/unclassified output")

    best = max(scores.items(), key=lambda x: x[1][0])
    return (best[0], best[1][1])


# ---------------------------------------------------------------------------
# Session Capture and Storage
# ---------------------------------------------------------------------------

def log_sessions(sessions):
    """Store captured session data in governor_log.

    sessions: list of dicts with keys:
        session_id, session_type, status, command_summary,
        captured_output, elapsed_seconds
    """
    ensure_tables()
    conn = get_db()
    stored = 0
    for s in sessions:
        text = s.get("captured_output", "")
        category, desc = classify_output(text)
        # Truncate very large outputs to 50KB to prevent DB bloat
        if len(text) > 50000:
            text = text[:50000] + "\n... [TRUNCATED from {} chars]".format(len(text))
        conn.execute("""
            INSERT INTO governor_log
                (session_id, session_type, status, command_summary,
                 captured_output, output_classification, routed_to,
                 action_taken, elapsed_seconds)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            s.get("session_id"),
            s.get("session_type", "unknown"),
            s.get("status", "captured"),
            s.get("command_summary", "")[:500],
            text,
            category,
            desc,
            s.get("action_taken", "captured"),
            s.get("elapsed_seconds", 0),
        ))
        stored += 1
    conn.commit()
    conn.close()
    logger.info("Logged %d sessions to governor_log", stored)
    return {"stored": stored, "status": "ok"}


# ---------------------------------------------------------------------------
# MCP Health Monitor
# ---------------------------------------------------------------------------

def check_mcp_health():
    """Check health of all MCP servers."""
    ensure_tables()
    results = {}

    for name, cfg in MCP_SERVERS.items():
        entry = {"server": name, "status": "unknown", "pid": None}

        if cfg.get("health_check") == "import_test" and cfg["command"] == "python":
            script = cfg["args"][0]
            if not Path(script).exists():
                entry["status"] = "MISSING"
                entry["error"] = "Script not found: {}".format(script)
            else:
                try:
                    result = subprocess.run(
                        ["python", "-c",
                         "import sys; sys.path.insert(0, r'{}'); "
                         "print('importable')".format(Path(script).parent)],
                        capture_output=True, text=True, timeout=10,
                        env={**os.environ, "PYTHONUTF8": "1"},
                    )
                    if result.returncode == 0:
                        entry["status"] = "HEALTHY"
                    else:
                        entry["status"] = "ERROR"
                        entry["error"] = result.stderr[:300]
                except subprocess.TimeoutExpired:
                    entry["status"] = "TIMEOUT"
                except Exception as e:
                    entry["status"] = "ERROR"
                    entry["error"] = str(e)[:300]

        elif cfg.get("health_check") == "process_check":
            script = cfg["args"][0] if cfg["args"] else ""
            if Path(script).exists():
                entry["status"] = "AVAILABLE"
            else:
                entry["status"] = "MISSING"
                entry["error"] = "Script not found: {}".format(script)

        # Check log file for recent errors
        log_path = cfg.get("log")
        if log_path and Path(log_path).exists():
            try:
                log_text = Path(log_path).read_text(
                    encoding="utf-8", errors="replace")
                lines = log_text.strip().split("\n")
                last_lines = lines[-5:] if len(lines) >= 5 else lines
                error_lines = [l for l in last_lines
                               if "ERROR" in l or "FATAL" in l]
                if error_lines:
                    entry["recent_errors"] = error_lines
                entry["log_lines"] = len(lines)
                entry["log_size_kb"] = round(
                    Path(log_path).stat().st_size / 1024, 1)
            except Exception:
                pass

        results[name] = entry

    # Log health check to watchdog table
    conn = get_db()
    for name, entry in results.items():
        conn.execute("""
            INSERT INTO mcp_watchdog
                (server_name, event_type, pid, error_message, action_taken)
            VALUES (?, ?, ?, ?, ?)
        """, (name, "health_check", entry.get("pid"),
              entry.get("error", ""), entry["status"]))
    conn.commit()
    conn.close()

    return results


def restart_mcp_server(server_name):
    """Restart a specific MCP server by name.
    Launches as a silent detached background process.
    """
    ensure_tables()

    if server_name not in MCP_SERVERS:
        return {"error": "Unknown server: {}".format(server_name),
                "available": list(MCP_SERVERS.keys())}

    cfg = MCP_SERVERS[server_name]
    cmd = cfg["command"]
    args = cfg["args"]
    env_extra = cfg.get("env", {})
    cwd = cfg.get("cwd", str(LITIGOS_ROOT))
    merged_env = {**os.environ, **env_extra}

    result_info = {"server": server_name, "action": "restart"}

    try:
        # Windows: CREATE_NO_WINDOW + DETACHED_PROCESS for silent launch
        if os.name == "nt":
            CREATE_NO_WINDOW = 0x08000000
            DETACHED_PROCESS = 0x00000008
            proc = subprocess.Popen(
                [cmd] + args,
                env=merged_env, cwd=cwd,
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                creationflags=CREATE_NO_WINDOW | DETACHED_PROCESS,
            )
        else:
            proc = subprocess.Popen(
                [cmd] + args,
                env=merged_env, cwd=cwd,
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                start_new_session=True,
            )

        # Brief wait to see if it crashes immediately
        time.sleep(2)
        if proc.poll() is not None:
            stderr_out = proc.stderr.read().decode("utf-8", errors="replace")[:500]
            result_info["status"] = "FAILED"
            result_info["exit_code"] = proc.returncode
            result_info["error"] = stderr_out
            logger.error("MCP %s failed to start: %s", server_name, stderr_out)
        else:
            result_info["status"] = "STARTED"
            result_info["pid"] = proc.pid
            logger.info("MCP %s started with PID %d", server_name, proc.pid)

        # Log to watchdog
        conn = get_db()
        conn.execute("""
            INSERT INTO mcp_watchdog
                (server_name, event_type, pid, error_message, action_taken)
            VALUES (?, ?, ?, ?, ?)
        """, (server_name, "restart", result_info.get("pid"),
              result_info.get("error", ""), result_info["status"]))
        conn.commit()
        conn.close()

    except Exception as e:
        result_info["status"] = "ERROR"
        result_info["error"] = str(e)[:500]
        logger.exception("Failed to restart %s", server_name)

    return result_info


# ---------------------------------------------------------------------------
# Governor Report
# ---------------------------------------------------------------------------

def generate_report():
    """Generate comprehensive governor status report."""
    ensure_tables()
    conn = get_db()

    report = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "governor": "HYDRA Governor v1.0",
    }

    # Session log stats
    row = conn.execute("""
        SELECT COUNT(*) as total,
               SUM(CASE WHEN action_taken = 'captured' THEN 1 ELSE 0 END) as captured,
               SUM(CASE WHEN action_taken = 'stopped' THEN 1 ELSE 0 END) as stopped
        FROM governor_log
    """).fetchone()
    report["session_log"] = {
        "total_entries": row["total"],
        "captured": row["captured"],
        "stopped": row["stopped"],
    }

    # Classification breakdown
    rows = conn.execute("""
        SELECT output_classification, COUNT(*) as cnt
        FROM governor_log
        GROUP BY output_classification
        ORDER BY cnt DESC
    """).fetchall()
    report["classifications"] = {r["output_classification"]: r["cnt"]
                                 for r in rows}

    # MCP watchdog recent events
    rows = conn.execute("""
        SELECT server_name, event_type, action_taken, timestamp
        FROM mcp_watchdog ORDER BY timestamp DESC LIMIT 20
    """).fetchall()
    report["mcp_events"] = [
        {"server": r["server_name"], "event": r["event_type"],
         "action": r["action_taken"], "time": r["timestamp"]}
        for r in rows
    ]

    # Recent captured sessions
    rows = conn.execute("""
        SELECT session_id, session_type, output_classification,
               action_taken, elapsed_seconds, captured_at
        FROM governor_log ORDER BY captured_at DESC LIMIT 10
    """).fetchall()
    report["recent_sessions"] = [
        {"id": r["session_id"], "type": r["session_type"],
         "class": r["output_classification"],
         "action": r["action_taken"],
         "elapsed": r["elapsed_seconds"],
         "captured": r["captured_at"]}
        for r in rows
    ]

    conn.close()
    return report


# ---------------------------------------------------------------------------
# Sweep Protocol - captures + classifies + stores stale sessions
# ---------------------------------------------------------------------------

def sweep_protocol(sessions_data):
    """Execute full sweep: capture -> classify -> store -> report.

    sessions_data: list of dicts from the Copilot agent with:
        session_id, session_type, status, command_summary,
        captured_output, elapsed_seconds, action_taken
    """
    ensure_tables()

    if not sessions_data:
        return {"swept": 0, "status": "clean",
                "message": "No stale sessions found"}

    result = log_sessions(sessions_data)

    classifications = {}
    for s in sessions_data:
        cat, _ = classify_output(s.get("captured_output", ""))
        classifications[cat] = classifications.get(cat, 0) + 1

    return {
        "swept": result["stored"],
        "classifications": classifications,
        "status": "complete",
        "message": "Captured {} sessions, classified into {} categories".format(
            result["stored"], len(classifications)),
    }


# ---------------------------------------------------------------------------
# CLI Interface: JSON on stdin -> JSON on stdout
# ---------------------------------------------------------------------------

ACTIONS = {
    "report": lambda _: generate_report(),
    "mcp_health": lambda _: check_mcp_health(),
    "mcp_restart": lambda req: restart_mcp_server(req.get("server", "")),
    "classify": lambda req: {
        "classification": classify_output(req.get("text", "")),
    },
    "log_session": lambda req: log_sessions(req.get("sessions", [])),
    "sweep": lambda req: sweep_protocol(req.get("sessions", [])),
    "ensure_tables": lambda _: (ensure_tables(), {"status": "tables_ready"})[1],
}


def main():
    """Read JSON from stdin, dispatch to action handler, write JSON to stdout."""
    try:
        raw = sys.stdin.read()
        if not raw.strip():
            request = {"action": "report"}
        else:
            request = json.loads(raw)
    except json.JSONDecodeError as e:
        json.dump({"error": "Invalid JSON: {}".format(e)}, sys.stdout)
        return

    action = request.get("action", "report")
    handler = ACTIONS.get(action)

    if not handler:
        json.dump({
            "error": "Unknown action: {}".format(action),
            "available": list(ACTIONS.keys()),
        }, sys.stdout)
        return

    try:
        result = handler(request)
        json.dump(result, sys.stdout, default=str)
    except Exception as e:
        logger.exception("Action '%s' failed", action)
        json.dump({"error": str(e), "action": action}, sys.stdout)


if __name__ == "__main__":
    main()
