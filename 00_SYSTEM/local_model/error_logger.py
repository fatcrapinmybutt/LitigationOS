#!/usr/bin/env python3
"""
LitigationOS Error Logger — Lightweight, thread-safe error telemetry.
Logs to both a rotating file and the error_telemetry table in the DB.
Zero external dependencies (stdlib only). Drop-in for silent except blocks.

Usage:
    from error_logger import log_exception, log_degraded, get_recent_errors

    try:
        result = engine.query(topic)
    except Exception:
        log_exception("inference_engine", "query", {"topic": topic})
        result = {}

    if not result:
        log_degraded("inference_engine", "query", "empty result set")
"""
from __future__ import annotations

import datetime
import json
import logging
import logging.handlers
import os
import sqlite3
import threading
import traceback
from typing import Any, Dict, List, Optional

# ── Defaults ────────────────────────────────────────────────────────
_DEFAULT_DB = os.path.join(
    os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
    "litigation_context.db",
)
_DEFAULT_LOG = os.path.join(os.path.dirname(os.path.abspath(__file__)), "error_log.log")
_MAX_BYTES = 10 * 1024 * 1024  # 10 MB
_BACKUP_COUNT = 3

# ── Module-level singleton ──────────────────────────────────────────
_lock = threading.Lock()
_file_logger: Optional[logging.Logger] = None
_db_path: Optional[str] = None
_initialized = False

# ── Table DDL ───────────────────────────────────────────────────────
_CREATE_TABLE = """
CREATE TABLE IF NOT EXISTS error_telemetry (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    timestamp   TEXT    NOT NULL,
    severity    TEXT    NOT NULL DEFAULT 'ERROR',
    engine      TEXT,
    method      TEXT,
    message     TEXT,
    traceback   TEXT,
    context     TEXT,
    resolved    INTEGER NOT NULL DEFAULT 0
)
"""
_CREATE_INDEX = """
CREATE INDEX IF NOT EXISTS idx_error_telemetry_ts
ON error_telemetry (timestamp DESC)
"""


def _init(db_path: Optional[str] = None, log_path: Optional[str] = None) -> None:
    """Lazy one-time init of file logger and DB table."""
    global _file_logger, _db_path, _initialized
    if _initialized:
        return
    with _lock:
        if _initialized:
            return
        _db_path = db_path or os.environ.get("LITIGATION_DB", _DEFAULT_DB)
        log_file = log_path or os.environ.get("LITIGATION_ERROR_LOG", _DEFAULT_LOG)
        # File logger with rotation
        _file_logger = logging.getLogger("litigationos.errors")
        _file_logger.setLevel(logging.DEBUG)
        if not _file_logger.handlers:
            handler = logging.handlers.RotatingFileHandler(
                log_file, maxBytes=_MAX_BYTES, backupCount=_BACKUP_COUNT,
                encoding="utf-8",
            )
            handler.setFormatter(logging.Formatter(
                "%(asctime)s | %(levelname)-8s | %(message)s",
                datefmt="%Y-%m-%d %H:%M:%S",
            ))
            _file_logger.addHandler(handler)
        # Ensure DB table exists (handle pre-existing tables gracefully)
        try:
            conn = sqlite3.connect(_db_path, timeout=5)
            cols = {r[1] for r in conn.execute(
                "PRAGMA table_info(error_telemetry)").fetchall()}
            if not cols:
                conn.execute(_CREATE_TABLE)
            else:
                # Migrate: add any missing columns from our schema
                for col, typedef in [("timestamp", "TEXT"),
                                     ("severity", "TEXT DEFAULT 'ERROR'"),
                                     ("engine", "TEXT"), ("method", "TEXT"),
                                     ("message", "TEXT"), ("traceback", "TEXT"),
                                     ("context", "TEXT"),
                                     ("resolved", "INTEGER DEFAULT 0")]:
                    if col not in cols:
                        conn.execute(f"ALTER TABLE error_telemetry "
                                     f"ADD COLUMN {col} {typedef}")
            if "timestamp" in {r[1] for r in conn.execute(
                    "PRAGMA table_info(error_telemetry)").fetchall()}:
                conn.execute(_CREATE_INDEX)
            conn.commit()
            conn.close()
        except Exception:
            _file_logger.warning("Could not init error_telemetry table: %s",
                                 traceback.format_exc())
        _initialized = True


# ── Internal helpers ────────────────────────────────────────────────

def _write_db(severity: str, engine: str, method: str,
              message: str, tb: str, context: str) -> None:
    """Insert one row into error_telemetry. Never raises."""
    try:
        conn = sqlite3.connect(_db_path, timeout=5)
        conn.execute(
            "INSERT INTO error_telemetry "
            "(timestamp, severity, engine, method, message, traceback, context) "
            "VALUES (?, ?, ?, ?, ?, ?, ?)",
            (datetime.datetime.now().isoformat(), severity,
             engine, method, message[:2000], tb[:4000], context[:4000]),
        )
        conn.commit()
        conn.close()
    except Exception:
        pass  # File log is the fallback; DB write is best-effort


def _log(severity: str, engine: str, method: str,
         message: str, tb: str = "",
         extra: Optional[Dict[str, Any]] = None) -> None:
    """Core log dispatcher — file + DB."""
    _init()
    ctx = json.dumps(extra, default=str)[:4000] if extra else ""
    tag = f"[{engine}.{method}]" if method else f"[{engine}]"
    line = f"{tag} {message}"
    level = getattr(logging, severity.upper(), logging.ERROR)
    _file_logger.log(level, line)
    if tb:
        _file_logger.log(level, "Traceback:\n%s", tb)
    _write_db(severity.upper(), engine, method, message, tb, ctx)


# ── Public API ──────────────────────────────────────────────────────

def log_exception(engine: str, method: str = "",
                  extra: Optional[Dict[str, Any]] = None,
                  severity: str = "ERROR") -> None:
    """Capture the current exception with full traceback.

    Call inside an ``except`` block::

        except Exception:
            log_exception("inference_engine", "query")
    """
    tb = traceback.format_exc()
    parts = tb.strip().rsplit("\n", 1)
    msg = parts[-1] if parts else "unknown exception"
    _log(severity, engine, method, msg, tb, extra)


def log_degraded(engine: str, method: str = "",
                 reason: str = "returned fallback/empty result",
                 extra: Optional[Dict[str, Any]] = None) -> None:
    """Record a graceful degradation (function succeeded but returned
    empty or fallback data, which may mask a deeper issue)."""
    _log("WARNING", engine, method, f"DEGRADED: {reason}", extra=extra)


def log_error(engine: str, method: str = "", message: str = "",
              extra: Optional[Dict[str, Any]] = None,
              severity: str = "ERROR") -> None:
    """Log an explicit error message (no active exception required)."""
    _log(severity, engine, method, message, extra=extra)


def get_recent_errors(limit: int = 50,
                      severity: Optional[str] = None,
                      engine: Optional[str] = None) -> List[Dict[str, Any]]:
    """Return recent error_telemetry rows for the TUI dashboard.

    Returns a list of dicts, newest first.  Filters are optional.
    """
    _init()
    clauses: list[str] = []
    params: list[Any] = []
    if severity:
        clauses.append("severity = ?")
        params.append(severity.upper())
    if engine:
        clauses.append("engine = ?")
        params.append(engine)
    where = ("WHERE " + " AND ".join(clauses)) if clauses else ""
    sql = (f"SELECT id, timestamp, severity, engine, method, message, "
           f"traceback, context, resolved "
           f"FROM error_telemetry {where} "
           f"ORDER BY timestamp DESC LIMIT ?")
    params.append(limit)
    try:
        conn = sqlite3.connect(_db_path, timeout=5)
        conn.row_factory = sqlite3.Row
        rows = conn.execute(sql, params).fetchall()
        conn.close()
        return [dict(r) for r in rows]
    except Exception:
        return []


def configure(db_path: Optional[str] = None,
              log_path: Optional[str] = None) -> None:
    """Override defaults before first use (call early in startup)."""
    global _initialized
    with _lock:
        _initialized = False
    _init(db_path, log_path)
