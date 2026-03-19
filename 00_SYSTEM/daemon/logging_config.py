"""
Structured logging for LitigationOS Daemon.
JSON-formatted logs → file + optional SQLite storage.
"""
import json
import logging
import logging.handlers
import os
import sqlite3
import sys
from datetime import datetime
from typing import Optional

from .models import LoggingConfig


class JSONFormatter(logging.Formatter):
    """Structured JSON log formatter."""

    def format(self, record: logging.LogRecord) -> str:
        log_entry = {
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }
        if hasattr(record, "context") and record.context:
            log_entry["context"] = record.context
        if record.exc_info and record.exc_info[1]:
            log_entry["error"] = {
                "type": type(record.exc_info[1]).__name__,
                "message": str(record.exc_info[1]),
            }
        if hasattr(record, "task_id"):
            log_entry["task_id"] = record.task_id
        if hasattr(record, "correlation_id"):
            log_entry["correlation_id"] = record.correlation_id
        return json.dumps(log_entry, ensure_ascii=False)


class SQLiteHandler(logging.Handler):
    """Log handler that writes to SQLite daemon_logs table."""

    def __init__(self, db_path: str):
        super().__init__()
        self.db_path = db_path
        self._buffer: list[tuple] = []
        self._buffer_limit = 50

    def emit(self, record: logging.LogRecord):
        try:
            context = None
            if hasattr(record, "context"):
                context = json.dumps(record.context) if isinstance(record.context, dict) else str(record.context)

            self._buffer.append((
                record.levelname,
                record.name,
                record.getMessage(),
                context,
            ))

            if len(self._buffer) >= self._buffer_limit:
                self.flush()
        except Exception:
            self.handleError(record)

    def flush(self):
        if not self._buffer:
            return
        try:
            conn = sqlite3.connect(self.db_path, timeout=30)
            conn.execute("PRAGMA journal_mode=WAL")
            conn.execute("PRAGMA busy_timeout=30000")
            conn.executemany(
                "INSERT INTO daemon_logs (level, logger, message, context) VALUES (?, ?, ?, ?)",
                self._buffer
            )
            conn.commit()
            conn.close()
            self._buffer.clear()
        except Exception:
            pass  # Don't crash the daemon over logging

    def close(self):
        self.flush()
        super().close()


def setup_logging(config: LoggingConfig, db_path: str = None) -> logging.Logger:
    """Configure daemon logging with JSON formatter and optional SQLite handler."""
    os.makedirs(config.log_dir, exist_ok=True)

    logger = logging.getLogger("litigationos.daemon")
    logger.setLevel(getattr(logging, config.level.upper(), logging.INFO))
    logger.handlers.clear()

    # File handler with rotation
    log_file = os.path.join(config.log_dir, "daemon.log")
    file_handler = logging.handlers.RotatingFileHandler(
        log_file,
        maxBytes=config.max_file_size_mb * 1024 * 1024,
        backupCount=config.backup_count,
        encoding="utf-8",
    )

    if config.structured_json:
        file_handler.setFormatter(JSONFormatter())
    else:
        file_handler.setFormatter(logging.Formatter(
            "%(asctime)s [%(levelname)s] %(name)s: %(message)s"
        ))
    logger.addHandler(file_handler)

    # Console handler (for CLI mode)
    console = logging.StreamHandler(sys.stdout)
    console.setFormatter(logging.Formatter(
        "%(asctime)s [%(levelname)s] %(message)s", datefmt="%H:%M:%S"
    ))
    console.setLevel(logging.INFO)
    logger.addHandler(console)

    # SQLite handler (optional)
    if config.log_to_db and db_path:
        sqlite_handler = SQLiteHandler(db_path)
        sqlite_handler.setLevel(logging.WARNING)
        logger.addHandler(sqlite_handler)

    return logger
