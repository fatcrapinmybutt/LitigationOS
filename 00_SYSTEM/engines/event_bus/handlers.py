"""Default event handlers for the LitigationOS Event Bus.

Each handler receives an Event object and performs a database write or
system action. All DB writes use parameterized queries with standard
PRAGMAs (busy_timeout=60000, WAL, cache_size=-32000).

Handlers:
    on_evidence_new       — Log new evidence discoveries to evidence_quotes
    on_file_detected      — Log discovered files to timeline_events
    on_contradiction_found — Persist contradictions to contradiction_map
    on_error_detected     — Log system errors to timeline_events
    on_db_updated         — Log DB mutation events to timeline_events
"""

import sys
import os
import re
import sqlite3
import logging
from datetime import datetime
from typing import Optional

sys.path.insert(0, r"C:\Users\andre\LitigationOS")

logger = logging.getLogger(__name__)

# ── DB Connection Helper ──────────────────────────────────────────────────

def _get_connection() -> sqlite3.Connection:
    """Get a connection to litigation_context.db with standard PRAGMAs."""
    try:
        from shared import get_db
        return get_db("litigation_context")
    except ImportError:
        db_path = os.path.join(
            r"C:\Users\andre\LitigationOS", "litigation_context.db"
        )
        conn = sqlite3.connect(db_path, timeout=60)
        conn.execute("PRAGMA busy_timeout = 60000")
        conn.execute("PRAGMA journal_mode = WAL")
        conn.execute("PRAGMA cache_size = -32000")
        return conn


# ── Handler Functions ─────────────────────────────────────────────────────

def on_evidence_new(event) -> None:
    """Handle evidence.new events — insert into evidence_quotes.

    Expected payload keys:
        quote_text (str, required): The evidence text
        source_file (str): Source file path
        page_number (int): Page number in source
        category (str): Evidence category
        lane (str): Case lane (A-F, CRIMINAL)
        tags (str): Comma-separated tags
    """
    payload = event.payload
    quote_text = payload.get("quote_text")
    if not quote_text:
        logger.warning("evidence.new event missing 'quote_text' — skipping")
        return

    conn = _get_connection()
    try:
        conn.execute(
            """INSERT INTO evidence_quotes
               (source_file, quote_text, page_number, category, lane, tags, created_at)
               VALUES (?, ?, ?, ?, ?, ?, ?)""",
            (
                payload.get("source_file", "event_bus"),
                quote_text,
                payload.get("page_number"),
                payload.get("category", "uncategorized"),
                payload.get("lane", ""),
                payload.get("tags", ""),
                datetime.utcnow().isoformat(),
            ),
        )
        conn.commit()
        logger.info("Persisted evidence quote from event %s", event.event_id)
    except sqlite3.Error as exc:
        logger.error("DB error in on_evidence_new: %s", exc)
    finally:
        conn.close()


def on_file_detected(event) -> None:
    """Handle file.detected events — log to timeline_events.

    Expected payload keys:
        file_path (str, required): Path to detected file
        file_type (str): File extension or type
        drive (str): Drive letter
        lane (str): Assigned lane
    """
    payload = event.payload
    file_path = payload.get("file_path")
    if not file_path:
        logger.warning("file.detected event missing 'file_path' — skipping")
        return

    conn = _get_connection()
    try:
        conn.execute(
            """INSERT INTO timeline_events
               (event_date, event_description, actors, lane, category,
                source_table, source_id, severity, filing_relevance, created_at)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (
                datetime.utcnow().strftime("%Y-%m-%d"),
                f"File detected: {os.path.basename(file_path)}",
                payload.get("drive", ""),
                payload.get("lane", ""),
                "file_detection",
                "event_bus",
                event.event_id,
                "low",
                "",
                datetime.utcnow().isoformat(),
            ),
        )
        conn.commit()
        logger.info("Logged file detection: %s", file_path)
    except sqlite3.Error as exc:
        logger.error("DB error in on_file_detected: %s", exc)
    finally:
        conn.close()


def on_contradiction_found(event) -> None:
    """Handle contradiction.found events — persist to contradiction_map.

    Expected payload keys:
        claim_id (str): Identifier for the claim
        source_a (str, required): First source
        source_b (str, required): Second source
        contradiction_text (str, required): Description
        severity (str): low/medium/high/critical
        lane (str): Case lane
    """
    payload = event.payload
    contradiction_text = payload.get("contradiction_text")
    source_a = payload.get("source_a")
    source_b = payload.get("source_b")

    if not all([contradiction_text, source_a, source_b]):
        logger.warning(
            "contradiction.found event missing required fields — skipping"
        )
        return

    conn = _get_connection()
    try:
        conn.execute(
            """INSERT OR IGNORE INTO contradiction_map
               (claim_id, source_a, source_b, contradiction_text, severity, lane)
               VALUES (?, ?, ?, ?, ?, ?)""",
            (
                payload.get("claim_id", ""),
                source_a,
                source_b,
                contradiction_text,
                payload.get("severity", "medium"),
                payload.get("lane", ""),
            ),
        )
        conn.commit()
        logger.info("Persisted contradiction from event %s", event.event_id)
    except sqlite3.Error as exc:
        logger.error("DB error in on_contradiction_found: %s", exc)
    finally:
        conn.close()


def on_error_detected(event) -> None:
    """Handle error.detected events — log to timeline_events for audit.

    Expected payload keys:
        error_code (str): Error code (e.g., ERR_DB_CONNECT)
        error_detail (str, required): Error description
        tool (str): Tool/engine that raised the error
        severity (str): low/medium/high/critical
    """
    payload = event.payload
    detail = payload.get("error_detail")
    if not detail:
        logger.warning("error.detected event missing 'error_detail' — skipping")
        return

    conn = _get_connection()
    try:
        code = payload.get("error_code", "ERR_UNKNOWN")
        tool = payload.get("tool", "unknown")
        conn.execute(
            """INSERT INTO timeline_events
               (event_date, event_description, actors, lane, category,
                source_table, source_id, severity, filing_relevance, created_at)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (
                datetime.utcnow().strftime("%Y-%m-%d"),
                f"[{code}] {detail}",
                tool,
                "",
                "system_error",
                "event_bus",
                event.event_id,
                payload.get("severity", "medium"),
                "",
                datetime.utcnow().isoformat(),
            ),
        )
        conn.commit()
        logger.info("Logged error event: %s from %s", code, tool)
    except sqlite3.Error as exc:
        logger.error("DB error in on_error_detected: %s", exc)
    finally:
        conn.close()


def on_db_updated(event) -> None:
    """Handle db.updated events — log mutation events for audit trail.

    Expected payload keys:
        table_name (str, required): Table that was modified
        operation (str): insert/update/delete
        row_count (int): Number of rows affected
        description (str): Human-readable description
    """
    payload = event.payload
    table_name = payload.get("table_name")
    if not table_name:
        logger.warning("db.updated event missing 'table_name' — skipping")
        return

    conn = _get_connection()
    try:
        operation = payload.get("operation", "unknown")
        row_count = payload.get("row_count", 0)
        desc = payload.get(
            "description",
            f"DB {operation} on {table_name}: {row_count} rows",
        )
        conn.execute(
            """INSERT INTO timeline_events
               (event_date, event_description, actors, lane, category,
                source_table, source_id, severity, filing_relevance, created_at)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (
                datetime.utcnow().strftime("%Y-%m-%d"),
                desc,
                "event_bus",
                "",
                "db_mutation",
                table_name,
                event.event_id,
                "low",
                "",
                datetime.utcnow().isoformat(),
            ),
        )
        conn.commit()
        logger.info("Logged DB update: %s on %s (%d rows)",
                     operation, table_name, row_count)
    except sqlite3.Error as exc:
        logger.error("DB error in on_db_updated: %s", exc)
    finally:
        conn.close()


# ── Registration ──────────────────────────────────────────────────────────

def register_default_handlers(bus) -> None:
    """Register all default handlers on the given EventBus.

    Topics registered:
        evidence.new         → on_evidence_new
        file.detected        → on_file_detected
        contradiction.found  → on_contradiction_found
        error.detected       → on_error_detected
        db.updated           → on_db_updated
    """
    bus.subscribe("evidence.new", on_evidence_new, priority=10, name="on_evidence_new")
    bus.subscribe("file.detected", on_file_detected, priority=20, name="on_file_detected")
    bus.subscribe("contradiction.found", on_contradiction_found, priority=10, name="on_contradiction_found")
    bus.subscribe("error.detected", on_error_detected, priority=5, name="on_error_detected")
    bus.subscribe("db.updated", on_db_updated, priority=30, name="on_db_updated")
    logger.info("Registered 5 default event handlers")
