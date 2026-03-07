"""SQLite database layer with FTS5 full-text search for litigation documents, knowledge graphs, and evolved .md knowledge."""

import csv
import functools
import glob as _glob_mod
import hashlib
import json
import logging
import os
import re
import sqlite3
import sys
import time
from datetime import datetime, timezone
from enum import Enum
from pathlib import Path
from typing import Optional, List, Dict, Any, Callable, TypeVar, Tuple

# Logging to stderr (MCP stdio servers must not pollute stdout)
logger = logging.getLogger("litigation_context_mcp")
_handler = logging.StreamHandler(sys.stderr)
_handler.setFormatter(logging.Formatter("%(asctime)s [%(levelname)s] %(name)s: %(message)s"))
logger.addHandler(_handler)
logger.setLevel(logging.INFO)

DB_PATH = os.path.join(
    os.environ.get("LITIGATION_DB_DIR", os.path.expanduser("~")),
    "litigation_context.db",
)

# Known knowledge-graph JSON files to auto-load
KNOWLEDGE_GRAPH_DIR = os.environ.get(
    "LITIGATION_GRAPH_DIR",
    r"C:\Users\andre\Scans",
)

GRAPH_FILES = {
    "court_forms_graph": "MASTER_COURT_FORMS_GRAPH_v2.json",
    "authority_forms_graph": "MI_AuthorityFormsGraph.json",
    "rules_authority_index": "rules_authority_index.json",
    "rules_extracted": "rules_extracted.json",
    "risk_event_types": "risk_event_types.json",
    "mcr_organized": "MCR_organized.json",
    "master_forms_graph_ext": "MI_MASTER_COURT_FORMS_GRAPH(3).json",
}

_CREATE_SQL = """
CREATE TABLE IF NOT EXISTS documents (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    file_path TEXT UNIQUE NOT NULL,
    file_name TEXT NOT NULL,
    file_size_bytes INTEGER,
    modified_date TEXT,
    page_count INTEGER DEFAULT 0,
    sha256_hash TEXT,
    ingested_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS pages (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    document_id INTEGER NOT NULL,
    page_number INTEGER NOT NULL,
    text_content TEXT NOT NULL,
    FOREIGN KEY (document_id) REFERENCES documents(id) ON DELETE CASCADE,
    UNIQUE(document_id, page_number)
);

CREATE VIRTUAL TABLE IF NOT EXISTS pages_fts USING fts5(
    text_content,
    content='pages',
    content_rowid='id',
    tokenize='porter unicode61'
);

CREATE TRIGGER IF NOT EXISTS pages_ai AFTER INSERT ON pages BEGIN
    INSERT INTO pages_fts(rowid, text_content) VALUES (new.id, new.text_content);
END;

CREATE TRIGGER IF NOT EXISTS pages_ad AFTER DELETE ON pages BEGIN
    INSERT INTO pages_fts(pages_fts, rowid, text_content) VALUES('delete', old.id, old.text_content);
END;

CREATE TRIGGER IF NOT EXISTS pages_au AFTER UPDATE ON pages BEGIN
    INSERT INTO pages_fts(pages_fts, rowid, text_content) VALUES('delete', old.id, old.text_content);
    INSERT INTO pages_fts(rowid, text_content) VALUES (new.id, new.text_content);
END;

CREATE INDEX IF NOT EXISTS idx_documents_hash ON documents(sha256_hash);
CREATE INDEX IF NOT EXISTS idx_pages_doc ON pages(document_id);

-- Knowledge graph tables
CREATE TABLE IF NOT EXISTS graph_nodes (
    id TEXT NOT NULL,
    graph_source TEXT NOT NULL,
    label TEXT,
    node_type TEXT,
    data TEXT,  -- full JSON blob
    PRIMARY KEY (id, graph_source)
);

CREATE TABLE IF NOT EXISTS court_rules (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    rule TEXT NOT NULL,
    chapter TEXT,
    context TEXT,
    source_doc TEXT,
    authority_id TEXT,
    context_count INTEGER DEFAULT 0
);

CREATE TABLE IF NOT EXISTS risk_events (
    risk_type_id TEXT PRIMARY KEY,
    track TEXT,
    forum TEXT,
    risk_class TEXT,
    severity INTEGER,
    title TEXT,
    trigger_json TEXT,
    cure_cost INTEGER,
    cure_deadline_clock TEXT,
    cure_packet_json TEXT,
    authority_refs_json TEXT
);

CREATE TABLE IF NOT EXISTS rules_text (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    rule TEXT NOT NULL,
    chapter TEXT,
    context TEXT,
    source_doc TEXT
);

CREATE VIRTUAL TABLE IF NOT EXISTS rules_text_fts USING fts5(
    rule, context,
    content='rules_text',
    content_rowid='id',
    tokenize='porter unicode61'
);

CREATE TRIGGER IF NOT EXISTS rules_text_ai AFTER INSERT ON rules_text BEGIN
    INSERT INTO rules_text_fts(rowid, rule, context) VALUES (new.id, new.rule, new.context);
END;

CREATE TABLE IF NOT EXISTS graph_load_log (
    graph_source TEXT PRIMARY KEY,
    loaded_at TEXT NOT NULL,
    record_count INTEGER,
    file_size_bytes INTEGER
);

-- Evolved .md knowledge sections (Level 2-3: structured + indexed)
CREATE TABLE IF NOT EXISTS md_sections (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    source_file TEXT NOT NULL,
    source_path TEXT NOT NULL,
    section_level INTEGER NOT NULL,       -- heading depth (1=H1, 2=H2, etc.)
    section_title TEXT NOT NULL,
    section_path TEXT NOT NULL,            -- hierarchical: "§9 > CONVERGENCE > Stop condition"
    content TEXT NOT NULL,
    char_count INTEGER DEFAULT 0,
    sha256_hash TEXT,
    evolved_at TEXT NOT NULL
);

CREATE VIRTUAL TABLE IF NOT EXISTS md_sections_fts USING fts5(
    section_title, content, section_path,
    content='md_sections',
    content_rowid='id',
    tokenize='porter unicode61'
);

CREATE TRIGGER IF NOT EXISTS md_sections_ai AFTER INSERT ON md_sections BEGIN
    INSERT INTO md_sections_fts(rowid, section_title, content, section_path)
    VALUES (new.id, new.section_title, new.content, new.section_path);
END;

CREATE TRIGGER IF NOT EXISTS md_sections_ad AFTER DELETE ON md_sections BEGIN
    INSERT INTO md_sections_fts(md_sections_fts, rowid, section_title, content, section_path)
    VALUES('delete', old.id, old.section_title, old.content, old.section_path);
END;

-- Cross-references: links between sections and graph nodes (Level 4: connected)
CREATE TABLE IF NOT EXISTS md_cross_refs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    section_id INTEGER NOT NULL,
    ref_type TEXT NOT NULL,               -- 'agent', 'rule', 'authority', 'vehicle', 'risk', 'keyword'
    ref_value TEXT NOT NULL,              -- the extracted reference (e.g. 'AGENT:AUTH_HARVESTER', 'MCR 3.706')
    graph_node_id TEXT,                   -- linked graph_nodes.id if matched
    graph_source TEXT,                    -- linked graph_nodes.graph_source if matched
    confidence REAL DEFAULT 1.0,
    FOREIGN KEY (section_id) REFERENCES md_sections(id) ON DELETE CASCADE
);

-- Convergence tracking
CREATE TABLE IF NOT EXISTS convergence_log (
    cycle_id INTEGER PRIMARY KEY AUTOINCREMENT,
    delta_new TEXT,          -- JSON: what was added
    blockers TEXT,           -- JSON: what's missing
    next_patch TEXT,         -- highest-leverage fix
    quality_score REAL,      -- 0-100
    measured_at TEXT NOT NULL
);

-- Audit metrics
CREATE TABLE IF NOT EXISTS audit_metrics (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    metric_name TEXT NOT NULL,
    metric_value REAL NOT NULL,
    detail TEXT,
    measured_at TEXT NOT NULL
);

-- Evolution log: tracks .md file processing
CREATE TABLE IF NOT EXISTS md_evolution_log (
    source_path TEXT PRIMARY KEY,
    evolved_at TEXT NOT NULL,
    section_count INTEGER,
    cross_ref_count INTEGER,
    file_size_bytes INTEGER,
    sha256_hash TEXT
);

CREATE INDEX IF NOT EXISTS idx_graph_nodes_type ON graph_nodes(node_type);
CREATE INDEX IF NOT EXISTS idx_court_rules_rule ON court_rules(rule);
CREATE INDEX IF NOT EXISTS idx_court_rules_authority ON court_rules(authority_id);
CREATE INDEX IF NOT EXISTS idx_rules_text_rule ON rules_text(rule);
CREATE INDEX IF NOT EXISTS idx_md_sections_source ON md_sections(source_file);
CREATE INDEX IF NOT EXISTS idx_md_sections_level ON md_sections(section_level);
CREATE INDEX IF NOT EXISTS idx_md_cross_refs_section ON md_cross_refs(section_id);
CREATE INDEX IF NOT EXISTS idx_md_cross_refs_type ON md_cross_refs(ref_type);
CREATE INDEX IF NOT EXISTS idx_md_cross_refs_value ON md_cross_refs(ref_value);

-- System registry: all LitigationOS subsystems across drives
CREATE TABLE IF NOT EXISTS system_registry (
    id TEXT PRIMARY KEY,
    system_name TEXT NOT NULL,
    system_type TEXT NOT NULL,  -- 'compiler', 'meek_lane', 'capstone', 'nucleus', 'gui', 'autopilot', 'graph', 'data'
    drive TEXT,
    path TEXT NOT NULL,
    version TEXT,
    status TEXT DEFAULT 'discovered',
    capabilities TEXT,  -- JSON array
    file_count INTEGER DEFAULT 0,
    total_size_mb REAL DEFAULT 0,
    last_scanned TEXT,
    metadata TEXT  -- JSON
);

CREATE TABLE IF NOT EXISTS master_csv_data (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    dataset TEXT NOT NULL,  -- 'citations', 'violations', 'timeline', 'persons', 'evidence_index'
    row_data TEXT NOT NULL,  -- JSON of the row
    source_file TEXT,
    row_number INTEGER
);

CREATE VIRTUAL TABLE IF NOT EXISTS master_csv_fts USING fts5(
    dataset, row_data, content=master_csv_data, content_rowid=id,
    tokenize='porter unicode61'
);

-- Triggers for FTS sync
CREATE TRIGGER IF NOT EXISTS master_csv_ai AFTER INSERT ON master_csv_data BEGIN
    INSERT INTO master_csv_fts(rowid, dataset, row_data) VALUES (new.id, new.dataset, new.row_data);
END;

CREATE INDEX IF NOT EXISTS idx_system_registry_type ON system_registry(system_type);
CREATE INDEX IF NOT EXISTS idx_master_csv_dataset ON master_csv_data(dataset);

-- Composite indexes for common multi-column filter patterns
CREATE INDEX IF NOT EXISTS idx_md_cross_refs_type_value ON md_cross_refs(ref_type, ref_value);
CREATE INDEX IF NOT EXISTS idx_graph_nodes_source_type ON graph_nodes(graph_source, node_type);
CREATE INDEX IF NOT EXISTS idx_court_rules_rule_chapter ON court_rules(rule, chapter);
"""


class DatabaseError(Exception):
    """Raised for non-recoverable database errors."""


class ExtractionError(Exception):
    """Raised when PDF extraction fails."""


class ErrorCode(Enum):
    """Structured error codes for actionable diagnostics."""
    ERR_DB_CONNECT = "ERR_DB_CONNECT"
    ERR_DB_LOCKED = "ERR_DB_LOCKED"
    ERR_DB_CORRUPT = "ERR_DB_CORRUPT"
    ERR_DB_SCHEMA = "ERR_DB_SCHEMA"
    ERR_FTS_DESYNC = "ERR_FTS_DESYNC"
    ERR_FTS_SYNTAX = "ERR_FTS_SYNTAX"
    ERR_PDF_CORRUPT = "ERR_PDF_CORRUPT"
    ERR_PDF_TOO_LARGE = "ERR_PDF_TOO_LARGE"
    ERR_PDF_TIMEOUT = "ERR_PDF_TIMEOUT"
    ERR_PDF_PERMISSION = "ERR_PDF_PERMISSION"
    ERR_GRAPH_LOAD = "ERR_GRAPH_LOAD"
    ERR_GRAPH_PARSE = "ERR_GRAPH_PARSE"
    ERR_MD_PARSE = "ERR_MD_PARSE"
    ERR_MD_EVOLVE = "ERR_MD_EVOLVE"
    ERR_DISK_FULL = "ERR_DISK_FULL"
    ERR_CIRCUIT_OPEN = "ERR_CIRCUIT_OPEN"


# ── Error recovery hints (maps ErrorCode → actionable guidance) ──
_RECOVERY_HINTS: Dict[ErrorCode, str] = {
    ErrorCode.ERR_DB_CONNECT: "Check that the database file exists and is not locked by another process. Try: `litigation_self_test`",
    ErrorCode.ERR_DB_LOCKED: "Another process holds the database lock. Wait a few seconds and retry, or close other connections.",
    ErrorCode.ERR_DB_CORRUPT: "Database integrity compromised. Run `litigation_self_test` then consider restoring from backup.",
    ErrorCode.ERR_DB_SCHEMA: "Schema mismatch — delete litigation_context.db and restart the server to recreate tables.",
    ErrorCode.ERR_FTS_DESYNC: "FTS index out of sync with source table. Run `litigation_self_test` to auto-repair.",
    ErrorCode.ERR_FTS_SYNTAX: "Invalid FTS5 query syntax. Use: AND, OR, NOT, \"quoted phrases\", prefix*. Avoid unbalanced quotes.",
    ErrorCode.ERR_PDF_CORRUPT: "PDF file is damaged or encrypted. Try opening it manually to verify. Skip with bulk ingest.",
    ErrorCode.ERR_PDF_TOO_LARGE: "PDF exceeds 500 MB size limit. Set LITIGATION_MAX_PDF_BYTES env var to increase.",
    ErrorCode.ERR_PDF_TIMEOUT: "PDF extraction timed out (120s). Set LITIGATION_PDF_TIMEOUT env var to increase.",
    ErrorCode.ERR_PDF_PERMISSION: "Permission denied reading the file. Run as administrator or check NTFS permissions.",
    ErrorCode.ERR_GRAPH_LOAD: "Knowledge graph JSON file not found. Check LITIGATION_GRAPH_DIR path.",
    ErrorCode.ERR_GRAPH_PARSE: "Knowledge graph JSON is malformed. Validate with a JSON linter.",
    ErrorCode.ERR_MD_PARSE: "Markdown file parsing failed. File may have encoding issues — ensure UTF-8.",
    ErrorCode.ERR_MD_EVOLVE: "Evolution pipeline error. Check file permissions and disk space.",
    ErrorCode.ERR_DISK_FULL: "Insufficient disk space. Free up space on the database drive.",
    ErrorCode.ERR_CIRCUIT_OPEN: "Circuit breaker tripped after repeated failures. Wait 60s or run `litigation_self_test` to reset.",
}


class StructuredError(Exception):
    """Error with structured code, message, and recovery hint for MCP protocol."""

    def __init__(self, code: ErrorCode, message: str, cause: Optional[Exception] = None):
        self.code = code
        self.message = message
        self.hint = _RECOVERY_HINTS.get(code, "")
        self.cause = cause
        super().__init__(f"[{code.value}] {message}")

    def to_dict(self) -> Dict[str, Any]:
        return {
            "error_code": self.code.value,
            "message": self.message,
            "recovery_hint": self.hint,
            "cause": str(self.cause) if self.cause else None,
        }


# ── Circuit Breaker ──────────────────────────────────────────────

class CircuitBreaker:
    """Circuit breaker for database connections — fast-fails after repeated errors."""

    def __init__(self, failure_threshold: int = 5, reset_timeout: float = 60.0):
        self._failure_count = 0
        self._failure_threshold = failure_threshold
        self._reset_timeout = reset_timeout
        self._last_failure_time: float = 0.0
        self._state = "closed"  # closed=normal, open=failing, half_open=testing

    @property
    def is_open(self) -> bool:
        if self._state == "open":
            if time.time() - self._last_failure_time >= self._reset_timeout:
                self._state = "half_open"
                return False
            return True
        return False

    def record_success(self):
        self._failure_count = 0
        self._state = "closed"

    def record_failure(self):
        self._failure_count += 1
        self._last_failure_time = time.time()
        if self._failure_count >= self._failure_threshold:
            self._state = "open"
            logger.error("Circuit breaker OPEN after %d consecutive failures", self._failure_count)

    def reset(self):
        self._failure_count = 0
        self._state = "closed"
        logger.info("Circuit breaker reset to CLOSED")

    @property
    def status(self) -> Dict[str, Any]:
        return {
            "state": self._state,
            "failure_count": self._failure_count,
            "threshold": self._failure_threshold,
            "reset_timeout_s": self._reset_timeout,
        }


_db_circuit = CircuitBreaker()


# ── Error Telemetry ──────────────────────────────────────────────

_ERROR_TELEMETRY_SQL = """
CREATE TABLE IF NOT EXISTS error_telemetry (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    error_code TEXT NOT NULL,
    tool_name TEXT,
    message TEXT,
    traceback TEXT,
    recorded_at TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_error_telemetry_code ON error_telemetry(error_code);
CREATE INDEX IF NOT EXISTS idx_error_telemetry_time ON error_telemetry(recorded_at);
"""


def record_error(conn: Optional[sqlite3.Connection], code: ErrorCode, tool_name: str, message: str, tb: str = ""):
    """Record an error in the telemetry table for audit analysis."""
    try:
        if conn is None:
            return
        now = datetime.now(timezone.utc).isoformat()
        conn.execute(
            "INSERT INTO error_telemetry (error_code, tool_name, message, traceback, recorded_at) VALUES (?, ?, ?, ?, ?)",
            (code.value, tool_name, message[:2000], tb[:4000], now),
        )
        conn.commit()
    except Exception:
        pass  # telemetry must never crash the main flow


def get_error_summary(conn: sqlite3.Connection, hours: int = 24) -> List[Dict[str, Any]]:
    """Get error telemetry summary for the last N hours."""
    try:
        rows = conn.execute(
            """SELECT error_code, tool_name, COUNT(*) as count,
                      MAX(recorded_at) as last_seen, MIN(recorded_at) as first_seen
               FROM error_telemetry
               WHERE recorded_at >= datetime('now', ?)
               GROUP BY error_code, tool_name
               ORDER BY count DESC""",
            (f"-{hours} hours",),
        ).fetchall()
        return [dict(r) for r in rows]
    except Exception:
        return []


# ── FTS5 Query Sanitizer ─────────────────────────────────────────

_FTS5_SPECIAL = re.compile(r'[{}()\[\]^~\\]')


def sanitize_fts_query(query: str) -> str:
    """Sanitize a user query for safe use in FTS5 MATCH.

    - Strips dangerous characters
    - Balances quotes
    - Falls back to simple term search if syntax is broken
    """
    if not query or not query.strip():
        return '""'
    q = query.strip()
    q = _FTS5_SPECIAL.sub(' ', q)
    if q.count('"') % 2 != 0:
        q = q.replace('"', '')
    if not q.strip():
        return f'"{query.strip()[:200]}"'
    return q


def safe_fts_search(conn: sqlite3.Connection, fts_table: str, match_col: str,
                    query: str, select_sql: str, params: tuple = (),
                    limit: int = 20, offset: int = 0) -> Tuple[List[Dict], int]:
    """Execute an FTS5 search with automatic syntax error recovery.

    Returns (results, total_count). On FTS syntax error, falls back
    to a quoted-phrase search. Never raises on bad user input.
    """
    sanitized = sanitize_fts_query(query)
    for attempt_query in [sanitized, f'"{query.strip()[:200]}"']:
        try:
            count_sql = f"SELECT COUNT(*) as cnt FROM {fts_table} WHERE {fts_table} MATCH ?"
            total = conn.execute(count_sql, (attempt_query,)).fetchone()["cnt"]
            full_sql = f"{select_sql} WHERE {fts_table} MATCH ? ORDER BY rank LIMIT ? OFFSET ?"
            rows = conn.execute(full_sql, (*params, attempt_query, limit, offset) if params
                                else (attempt_query, limit, offset)).fetchall()
            return [dict(r) for r in rows], total
        except sqlite3.OperationalError as e:
            err_msg = str(e).lower()
            if "fts5" in err_msg or "syntax" in err_msg or "parse" in err_msg:
                logger.warning("FTS5 syntax error on query %r, retrying as phrase: %s", attempt_query, e)
                continue
            raise
    return [], 0


# ── Disk Space Guard ─────────────────────────────────────────────

def check_disk_space(min_mb: int = 100) -> bool:
    """Return True if the database drive has at least min_mb free. Raises StructuredError if not."""
    try:
        import shutil
        db_dir = os.path.dirname(DB_PATH) or os.path.expanduser("~")
        usage = shutil.disk_usage(db_dir)
        free_mb = usage.free / (1024 * 1024)
        if free_mb < min_mb:
            raise StructuredError(
                ErrorCode.ERR_DISK_FULL,
                f"Only {free_mb:.0f} MB free on {db_dir} (need {min_mb} MB minimum)",
            )
        return True
    except StructuredError:
        raise
    except Exception:
        return True  # can't check → assume OK


# ── Health State ─────────────────────────────────────────────────

class _HealthState:
    """Tracks server health for lifespan-level issues."""
    def __init__(self):
        self.graphs_loaded: bool = False
        self.graph_errors: List[str] = []
        self.startup_time: Optional[str] = None
        self.degraded: bool = False

    @property
    def status(self) -> Dict[str, Any]:
        return {
            "graphs_loaded": self.graphs_loaded,
            "graph_errors": self.graph_errors,
            "startup_time": self.startup_time,
            "degraded": self.degraded,
            "circuit_breaker": _db_circuit.status,
        }

health = _HealthState()


# ── Retry Decorator ──────────────────────────────────────────────

T = TypeVar("T")

_TRANSIENT_SQLITE_ERRORS = {"database is locked", "database table is locked", "disk I/O error"}


def retry_on_transient(
    max_retries: int = 3,
    base_delay: float = 0.5,
    max_delay: float = 8.0,
) -> Callable:
    """Retry decorator with exponential backoff for transient SQLite errors."""
    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        @functools.wraps(func)
        def wrapper(*args, **kwargs) -> T:
            last_error = None
            for attempt in range(max_retries + 1):
                try:
                    return func(*args, **kwargs)
                except sqlite3.OperationalError as e:
                    err_msg = str(e).lower()
                    if any(t in err_msg for t in _TRANSIENT_SQLITE_ERRORS) and attempt < max_retries:
                        delay = min(base_delay * (2 ** attempt), max_delay)
                        logger.warning("Transient DB error (attempt %d/%d), retrying in %.1fs: %s",
                                       attempt + 1, max_retries, delay, e)
                        time.sleep(delay)
                        last_error = e
                    else:
                        raise
            raise last_error  # type: ignore
        return wrapper
    return decorator


class ConnectionManager:
    """Context manager for database connections with health checks."""

    def __init__(self, timeout: float = 30.0):
        self.timeout = timeout
        self._conn: Optional[sqlite3.Connection] = None

    def __enter__(self) -> sqlite3.Connection:
        self._conn = get_connection(self.timeout)
        return self._conn

    def __exit__(self, exc_type, exc_val, exc_tb):
        if self._conn:
            try:
                if exc_type is None:
                    self._conn.commit()
                self._conn.close()
            except sqlite3.Error:
                pass
            self._conn = None
        return False


def get_connection(timeout: float = 30.0) -> sqlite3.Connection:
    """Get a database connection, creating tables if needed.

    Raises DatabaseError if connection or initialization fails.
    Respects circuit breaker state for fast-fail on repeated errors.
    Uses a fast-path check: skip schema creation if 'documents' table already exists.
    """
    if _db_circuit.is_open:
        raise StructuredError(
            ErrorCode.ERR_CIRCUIT_OPEN,
            "Database circuit breaker is OPEN — too many consecutive failures",
        )
    try:
        os.makedirs(os.path.dirname(DB_PATH) or ".", exist_ok=True)
        conn = sqlite3.connect(DB_PATH, timeout=timeout)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA journal_mode=WAL")
        conn.execute("PRAGMA foreign_keys=ON")
        conn.execute("PRAGMA busy_timeout=60000")
        conn.execute("PRAGMA cache_size=-32000")
        conn.execute("PRAGMA temp_store=MEMORY")
        conn.execute("PRAGMA synchronous=NORMAL")
        # Fast-path: skip heavy schema creation if core tables exist
        existing = {r[0] for r in conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table'"
        ).fetchall()}
        if "documents" not in existing or "error_telemetry" not in existing:
            conn.executescript(_CREATE_SQL)
            conn.executescript(_ERROR_TELEMETRY_SQL)
        _db_circuit.record_success()
        return conn
    except sqlite3.OperationalError as e:
        err_msg = str(e).lower()
        _db_circuit.record_failure()
        if "locked" in err_msg:
            raise StructuredError(ErrorCode.ERR_DB_LOCKED, str(e), e) from e
        if "corrupt" in err_msg or "malformed" in err_msg:
            raise StructuredError(ErrorCode.ERR_DB_CORRUPT, str(e), e) from e
        logger.error("Database connection failed: %s", e)
        raise StructuredError(ErrorCode.ERR_DB_CONNECT, f"Cannot connect to database at {DB_PATH}: {e}", e) from e
    except sqlite3.Error as e:
        _db_circuit.record_failure()
        logger.error("Database connection failed: %s", e)
        raise DatabaseError(f"Cannot connect to database at {DB_PATH}: {e}") from e


def document_exists(conn: sqlite3.Connection, file_path: str) -> bool:
    row = conn.execute(
        "SELECT 1 FROM documents WHERE file_path = ?", (file_path,)
    ).fetchone()
    return row is not None


def hash_exists(conn: sqlite3.Connection, sha256_hash: str) -> Optional[str]:
    """Return file_path if hash already indexed, else None."""
    row = conn.execute(
        "SELECT file_path FROM documents WHERE sha256_hash = ?", (sha256_hash,)
    ).fetchone()
    return row["file_path"] if row else None


def insert_document(
    conn: sqlite3.Connection,
    file_path: str,
    file_name: str,
    file_size_bytes: int,
    modified_date: str,
    page_count: int,
    sha256_hash: str,
    pages: List[Dict[str, Any]],
) -> int:
    """Insert a document and its pages. Returns the document id."""
    now = datetime.now(timezone.utc).isoformat()
    cur = conn.execute(
        """INSERT INTO documents
           (file_path, file_name, file_size_bytes, modified_date, page_count, sha256_hash, ingested_at)
           VALUES (?, ?, ?, ?, ?, ?, ?)""",
        (file_path, file_name, file_size_bytes, modified_date, page_count, sha256_hash, now),
    )
    doc_id = cur.lastrowid
    conn.executemany(
        "INSERT INTO pages (document_id, page_number, text_content) VALUES (?, ?, ?)",
        [(doc_id, p["page_number"], p["text_content"]) for p in pages],
    )
    conn.commit()
    return doc_id


def search_pages(
    conn: sqlite3.Connection,
    query: str,
    limit: int = 20,
    offset: int = 0,
) -> Dict[str, Any]:
    """Full-text search across all pages. Returns matches with context."""
    count_row = conn.execute(
        "SELECT COUNT(*) as cnt FROM pages_fts WHERE pages_fts MATCH ?", (query,)
    ).fetchone()
    total = count_row["cnt"]

    rows = conn.execute(
        """SELECT p.id, p.document_id, p.page_number,
                  snippet(pages_fts, 0, '>>>', '<<<', '...', 40) AS snippet,
                  d.file_path, d.file_name
           FROM pages_fts
           JOIN pages p ON p.id = pages_fts.rowid
           JOIN documents d ON d.id = p.document_id
           WHERE pages_fts MATCH ?
           ORDER BY rank
           LIMIT ? OFFSET ?""",
        (query, limit, offset),
    ).fetchall()

    return {
        "total": total,
        "count": len(rows),
        "offset": offset,
        "has_more": total > offset + len(rows),
        "next_offset": offset + len(rows) if total > offset + len(rows) else None,
        "results": [dict(r) for r in rows],
    }


def list_documents(
    conn: sqlite3.Connection,
    limit: int = 20,
    offset: int = 0,
    name_filter: Optional[str] = None,
) -> Dict[str, Any]:
    """List indexed documents with optional name filter."""
    where = ""
    params: list = []
    if name_filter:
        where = "WHERE file_name LIKE ?"
        params.append(f"%{name_filter}%")

    total = conn.execute(
        f"SELECT COUNT(*) as cnt FROM documents {where}", params
    ).fetchone()["cnt"]

    rows = conn.execute(
        f"""SELECT id, file_path, file_name, file_size_bytes, modified_date,
                   page_count, ingested_at
            FROM documents {where}
            ORDER BY ingested_at DESC
            LIMIT ? OFFSET ?""",
        params + [limit, offset],
    ).fetchall()

    return {
        "total": total,
        "count": len(rows),
        "offset": offset,
        "has_more": total > offset + len(rows),
        "next_offset": offset + len(rows) if total > offset + len(rows) else None,
        "documents": [dict(r) for r in rows],
    }


def get_document_text(
    conn: sqlite3.Connection, doc_id: int
) -> Optional[Dict[str, Any]]:
    """Get a document's metadata and full text (all pages)."""
    doc = conn.execute(
        "SELECT * FROM documents WHERE id = ?", (doc_id,)
    ).fetchone()
    if not doc:
        return None
    pages = conn.execute(
        "SELECT page_number, text_content FROM pages WHERE document_id = ? ORDER BY page_number",
        (doc_id,),
    ).fetchall()
    return {
        "document": dict(doc),
        "pages": [dict(p) for p in pages],
    }


def delete_document(conn: sqlite3.Connection, doc_id: int) -> bool:
    """Delete a document and its pages. Returns True if found."""
    row = conn.execute("SELECT id FROM documents WHERE id = ?", (doc_id,)).fetchone()
    if not row:
        return False
    conn.execute("DELETE FROM pages WHERE document_id = ?", (doc_id,))
    conn.execute("DELETE FROM documents WHERE id = ?", (doc_id,))
    conn.commit()
    return True


def get_stats(conn: sqlite3.Connection) -> Dict[str, Any]:
    """Get knowledge base statistics including graph data.

    Uses a single query with conditional aggregation instead of 6+ separate COUNT(*) calls.
    """
    stats_row = conn.execute(
        """SELECT
               (SELECT COUNT(*) FROM documents) AS doc_count,
               (SELECT COUNT(*) FROM pages) AS page_count,
               (SELECT COALESCE(SUM(file_size_bytes), 0) FROM documents) AS total_size,
               (SELECT COUNT(*) FROM graph_nodes) AS graph_node_count,
               (SELECT COUNT(*) FROM court_rules) AS rule_count,
               (SELECT COUNT(*) FROM rules_text) AS rules_text_count,
               (SELECT COUNT(*) FROM risk_events) AS risk_count"""
    ).fetchone()
    latest = conn.execute(
        "SELECT ingested_at FROM documents ORDER BY ingested_at DESC LIMIT 1"
    ).fetchone()
    graphs_loaded = [
        dict(r) for r in conn.execute(
            "SELECT graph_source, record_count, loaded_at FROM graph_load_log ORDER BY loaded_at"
        ).fetchall()
    ]
    total_size = stats_row["total_size"]
    return {
        "total_documents": stats_row["doc_count"],
        "total_pages": stats_row["page_count"],
        "total_size_bytes": total_size,
        "total_size_mb": round(total_size / (1024 * 1024), 2),
        "graph_nodes": stats_row["graph_node_count"],
        "court_rules_indexed": stats_row["rule_count"],
        "rules_text_entries": stats_row["rules_text_count"],
        "risk_events": stats_row["risk_count"],
        "graphs_loaded": graphs_loaded,
        "database_path": DB_PATH,
        "last_ingested_at": latest["ingested_at"] if latest else None,
    }


# ── Knowledge Graph Loading ──────────────────────────────────────

def _is_graph_loaded(conn: sqlite3.Connection, source: str) -> bool:
    row = conn.execute(
        "SELECT 1 FROM graph_load_log WHERE graph_source = ?", (source,)
    ).fetchone()
    return row is not None


def load_court_forms_graph(conn: sqlite3.Connection, file_path: str, source: str) -> int:
    """Load a court forms/authority graph (nodes with id/label/type/pin_cite).

    Uses executemany for batch insertion instead of row-by-row inserts.
    """
    if _is_graph_loaded(conn, source):
        logger.info("Graph '%s' already loaded, skipping.", source)
        return 0
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            data = json.load(f)
        nodes = data.get("nodes", data) if isinstance(data, dict) else data
        if not isinstance(nodes, list):
            nodes = list(nodes.values()) if isinstance(nodes, dict) else []
        rows = []
        for node in nodes:
            nid = node.get("id", "")
            label = node.get("label", node.get("name", ""))
            ntype = node.get("type", node.get("node_type", node.get("group", "")))
            rows.append((nid, source, label, ntype, json.dumps(node, default=str)))
        conn.executemany(
            "INSERT OR IGNORE INTO graph_nodes (id, graph_source, label, node_type, data) VALUES (?, ?, ?, ?, ?)",
            rows,
        )
        count = len(rows)
        conn.execute(
            "INSERT OR REPLACE INTO graph_load_log (graph_source, loaded_at, record_count, file_size_bytes) VALUES (?, ?, ?, ?)",
            (source, datetime.now(timezone.utc).isoformat(), count, os.path.getsize(file_path)),
        )
        conn.commit()
        logger.info("Loaded %d nodes from '%s'.", count, source)
        return count
    except Exception as e:
        logger.error("Failed to load graph '%s': %s", source, e)
        return 0


def load_rules_authority_index(conn: sqlite3.Connection, file_path: str) -> int:
    """Load rules_authority_index.json into court_rules table.

    Uses executemany for batch insertion.
    """
    source = "rules_authority_index"
    if _is_graph_loaded(conn, source):
        return 0
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            data = json.load(f)
        records = data.get("records", data) if isinstance(data, dict) else data
        rows = [
            (rec.get("rule"), str(rec.get("chapter", "")), rec.get("source_doc", ""),
             rec.get("context_count", 0), rec.get("authority_id", ""))
            for rec in records
        ]
        conn.executemany(
            "INSERT INTO court_rules (rule, chapter, source_doc, context_count, authority_id) VALUES (?, ?, ?, ?, ?)",
            rows,
        )
        count = len(rows)
        conn.execute(
            "INSERT OR REPLACE INTO graph_load_log (graph_source, loaded_at, record_count, file_size_bytes) VALUES (?, ?, ?, ?)",
            (source, datetime.now(timezone.utc).isoformat(), count, os.path.getsize(file_path)),
        )
        conn.commit()
        logger.info("Loaded %d rules from '%s'.", count, source)
        return count
    except Exception as e:
        logger.error("Failed to load rules index: %s", e)
        return 0


def load_rules_extracted(conn: sqlite3.Connection, file_path: str) -> int:
    """Load rules_extracted.json into rules_text table with FTS."""
    source = "rules_extracted"
    if _is_graph_loaded(conn, source):
        return 0
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            data = json.load(f)
        records = data if isinstance(data, list) else data.get("records", [])
        count = 0
        for rec in records:
            conn.execute(
                "INSERT INTO rules_text (rule, chapter, context, source_doc) VALUES (?, ?, ?, ?)",
                (rec.get("rule", ""), str(rec.get("chapter", "")),
                 rec.get("context", ""), rec.get("source_doc", "")),
            )
            count += 1
        conn.execute(
            "INSERT OR REPLACE INTO graph_load_log (graph_source, loaded_at, record_count, file_size_bytes) VALUES (?, ?, ?, ?)",
            (source, datetime.now(timezone.utc).isoformat(), count, os.path.getsize(file_path)),
        )
        conn.commit()
        logger.info("Loaded %d rule texts from '%s'.", count, source)
        return count
    except Exception as e:
        logger.error("Failed to load rules text: %s", e)
        return 0


def load_risk_events(conn: sqlite3.Connection, file_path: str) -> int:
    """Load risk_event_types.json into risk_events table.

    Uses executemany for batch insertion.
    """
    source = "risk_event_types"
    if _is_graph_loaded(conn, source):
        return 0
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            data = json.load(f)
        records = data if isinstance(data, list) else data.get("records", [])
        rows = [
            (rec.get("risk_type_id", ""), rec.get("track", "*"), rec.get("forum", "*"),
             rec.get("risk_class", ""), rec.get("severity", 0), rec.get("title", ""),
             json.dumps(rec.get("trigger_when", []), default=str), rec.get("cure_cost", 0),
             rec.get("cure_deadline_clock", ""), json.dumps(rec.get("cure_minimum_packet", []), default=str),
             json.dumps(rec.get("authority_refs", []), default=str))
            for rec in records
        ]
        conn.executemany(
            """INSERT OR IGNORE INTO risk_events
               (risk_type_id, track, forum, risk_class, severity, title,
                trigger_json, cure_cost, cure_deadline_clock, cure_packet_json, authority_refs_json)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            rows,
        )
        count = len(rows)
        conn.execute(
            "INSERT OR REPLACE INTO graph_load_log (graph_source, loaded_at, record_count, file_size_bytes) VALUES (?, ?, ?, ?)",
            (source, datetime.now(timezone.utc).isoformat(), count, os.path.getsize(file_path)),
        )
        conn.commit()
        logger.info("Loaded %d risk events from '%s'.", count, source)
        return count
    except Exception as e:
        logger.error("Failed to load risk events: %s", e)
        return 0


def load_all_knowledge_graphs(conn: sqlite3.Connection) -> Dict[str, int]:
    """Load all available knowledge graphs from disk. Returns counts per source."""
    results: Dict[str, int] = {}
    graph_dir = Path(KNOWLEDGE_GRAPH_DIR)

    # Court forms and authority graphs → graph_nodes table
    for source_key, filename in GRAPH_FILES.items():
        fp = graph_dir / filename
        if not fp.exists():
            logger.warning("Graph file not found: %s", fp)
            continue
        if source_key in ("rules_authority_index", "rules_extracted", "risk_event_types"):
            continue  # handled by specialized loaders
        results[source_key] = load_court_forms_graph(conn, str(fp), source_key)

    # Specialized loaders
    rules_idx = graph_dir / "rules_authority_index.json"
    if rules_idx.exists():
        results["rules_authority_index"] = load_rules_authority_index(conn, str(rules_idx))

    rules_ext = graph_dir / "rules_extracted.json"
    if rules_ext.exists():
        results["rules_extracted"] = load_rules_extracted(conn, str(rules_ext))

    risk_fp = graph_dir / "risk_event_types.json"
    if risk_fp.exists():
        results["risk_event_types"] = load_risk_events(conn, str(risk_fp))

    # Also try loading MasterGraph.json (large, separate)
    master_graph = graph_dir / "MasterGraph.json"
    if master_graph.exists():
        results["master_graph"] = load_court_forms_graph(conn, str(master_graph), "master_graph")

    logger.info("Knowledge graph loading complete: %s", results)
    return results


# ── Graph Query Functions ─────────────────────────────────────────

def search_rules(
    conn: sqlite3.Connection, query: str, limit: int = 20, offset: int = 0
) -> Dict[str, Any]:
    """Search court rules by rule cite or full-text in context."""
    # First try exact/prefix match on rule column
    exact = conn.execute(
        "SELECT * FROM court_rules WHERE rule LIKE ? ORDER BY rule LIMIT ? OFFSET ?",
        (f"%{query}%", limit, offset),
    ).fetchall()
    if exact:
        total = conn.execute(
            "SELECT COUNT(*) as cnt FROM court_rules WHERE rule LIKE ?", (f"%{query}%",)
        ).fetchone()["cnt"]
        return {
            "total": total, "count": len(exact), "offset": offset,
            "has_more": total > offset + len(exact),
            "results": [dict(r) for r in exact],
        }

    # Fall back to FTS on rules_text
    try:
        total = conn.execute(
            "SELECT COUNT(*) as cnt FROM rules_text_fts WHERE rules_text_fts MATCH ?", (query,)
        ).fetchone()["cnt"]
        rows = conn.execute(
            """SELECT rt.id, rt.rule, rt.chapter,
                      snippet(rules_text_fts, 1, '>>>', '<<<', '...', 40) AS snippet,
                      rt.source_doc
               FROM rules_text_fts
               JOIN rules_text rt ON rt.id = rules_text_fts.rowid
               WHERE rules_text_fts MATCH ?
               ORDER BY rank LIMIT ? OFFSET ?""",
            (query, limit, offset),
        ).fetchall()
        return {
            "total": total, "count": len(rows), "offset": offset,
            "has_more": total > offset + len(rows),
            "results": [dict(r) for r in rows],
        }
    except sqlite3.OperationalError:
        return {"total": 0, "count": 0, "offset": 0, "has_more": False, "results": []}


def search_graph_nodes(
    conn: sqlite3.Connection,
    query: str,
    node_type: Optional[str] = None,
    graph_source: Optional[str] = None,
    limit: int = 20,
    offset: int = 0,
) -> Dict[str, Any]:
    """Search graph nodes by label/id with optional type and source filters."""
    where_parts = ["(label LIKE ? OR id LIKE ?)"]
    params: list = [f"%{query}%", f"%{query}%"]
    if node_type:
        where_parts.append("node_type = ?")
        params.append(node_type)
    if graph_source:
        where_parts.append("graph_source = ?")
        params.append(graph_source)
    where = " AND ".join(where_parts)

    total = conn.execute(
        f"SELECT COUNT(*) as cnt FROM graph_nodes WHERE {where}", params
    ).fetchone()["cnt"]
    rows = conn.execute(
        f"SELECT id, graph_source, label, node_type, data FROM graph_nodes WHERE {where} ORDER BY label LIMIT ? OFFSET ?",
        params + [limit, offset],
    ).fetchall()
    return {
        "total": total, "count": len(rows), "offset": offset,
        "has_more": total > offset + len(rows),
        "results": [dict(r) for r in rows],
    }


def get_risk_events(
    conn: sqlite3.Connection,
    severity_min: int = 0,
    risk_class: Optional[str] = None,
) -> List[Dict[str, Any]]:
    """Get risk events filtered by severity and/or class."""
    where = "severity >= ?"
    params: list = [severity_min]
    if risk_class:
        where += " AND risk_class = ?"
        params.append(risk_class)
    rows = conn.execute(
        f"SELECT * FROM risk_events WHERE {where} ORDER BY severity DESC", params
    ).fetchall()
    return [dict(r) for r in rows]


# ══════════════════════════════════════════════════════════════════
#  .MD EVOLUTION ENGINE — Level 1 → Level 5
# ══════════════════════════════════════════════════════════════════

# Patterns for cross-reference extraction
_AGENT_PATTERN = re.compile(r"AGENT:([A-Z_]+)")
_RULE_PATTERN = re.compile(r"(MCR|MCL|MRE)\s+(\d+[\.\d]*)")
_RISK_PATTERN = re.compile(r"(severity|risk_class|cure_cost|risk_type_id)")
_VEHICLE_PATTERN = re.compile(r"(motion|brief|complaint|application|order|petition|objection)", re.IGNORECASE)


def _parse_md_sections(content: str, source_file: str) -> List[Dict[str, Any]]:
    """Parse markdown into hierarchical sections. Level 1→2 evolution."""
    sections: List[Dict[str, Any]] = []
    lines = content.split("\n")
    current_stack: List[Tuple[int, str]] = []  # (level, title)
    current_content: List[str] = []
    current_level = 0
    current_title = "(preamble)"

    def _flush():
        text = "\n".join(current_content).strip()
        if text or current_title != "(preamble)":
            path_parts = [t for _, t in current_stack]
            if current_title not in path_parts:
                path_parts.append(current_title)
            sections.append({
                "source_file": source_file,
                "section_level": current_level or 1,
                "section_title": current_title,
                "section_path": " > ".join(path_parts) if path_parts else current_title,
                "content": text,
                "char_count": len(text),
            })

    for line in lines:
        heading_match = re.match(r"^(#{1,6})\s+(.+)$", line)
        if heading_match:
            _flush()
            current_content = []
            level = len(heading_match.group(1))
            title = heading_match.group(2).strip()
            # Update stack: pop everything at or below this level
            while current_stack and current_stack[-1][0] >= level:
                current_stack.pop()
            current_stack.append((level, title))
            current_level = level
            current_title = title
        else:
            current_content.append(line)

    _flush()  # last section
    return sections


def _extract_cross_refs(section_id: int, content: str, title: str) -> List[Dict[str, Any]]:
    """Extract cross-references from section content. Level 3→4 evolution."""
    refs: List[Dict[str, Any]] = []
    full_text = f"{title}\n{content}"

    # Agents
    for match in _AGENT_PATTERN.finditer(full_text):
        refs.append({"section_id": section_id, "ref_type": "agent", "ref_value": f"AGENT:{match.group(1)}"})

    # Court rules (MCR/MCL/MRE)
    for match in _RULE_PATTERN.finditer(full_text):
        refs.append({"section_id": section_id, "ref_type": "rule", "ref_value": f"{match.group(1)} {match.group(2)}"})

    # Vehicles
    for match in _VEHICLE_PATTERN.finditer(content):
        refs.append({"section_id": section_id, "ref_type": "vehicle", "ref_value": match.group(1).lower()})

    # Deduplicate
    seen = set()
    unique: List[Dict[str, Any]] = []
    for ref in refs:
        key = (ref["ref_type"], ref["ref_value"])
        if key not in seen:
            seen.add(key)
            unique.append(ref)
    return unique


def _link_cross_refs_to_graph(conn: sqlite3.Connection, refs: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Match cross-references against existing graph nodes. Level 4 linking."""
    for ref in refs:
        if ref["ref_type"] == "rule":
            row = conn.execute(
                "SELECT id, graph_source FROM graph_nodes WHERE id LIKE ? OR label LIKE ? LIMIT 1",
                (f"%{ref['ref_value']}%", f"%{ref['ref_value']}%"),
            ).fetchone()
            if row:
                ref["graph_node_id"] = row["id"]
                ref["graph_source"] = row["graph_source"]
    return refs


@retry_on_transient()
def evolve_md_file(conn: sqlite3.Connection, file_path: str) -> Dict[str, Any]:
    """Evolve a single .md file from Level 1 (flat text) to Level 5 (indexed + cross-referenced).

    Returns evolution stats.
    """
    path = Path(file_path)
    if not path.exists():
        raise FileNotFoundError(f"File not found: {file_path}")
    if not path.suffix.lower() == ".md":
        raise ValueError(f"Not a markdown file: {file_path}")

    abs_path = str(path.resolve())

    # Check if already evolved (idempotent)
    existing = conn.execute(
        "SELECT 1 FROM md_evolution_log WHERE source_path = ?", (abs_path,)
    ).fetchone()
    if existing:
        return {"status": "already_evolved", "source": abs_path, "sections": 0, "cross_refs": 0}

    # Read and hash
    content = path.read_text(encoding="utf-8", errors="replace")
    sha = hashlib.sha256(content.encode("utf-8")).hexdigest()

    # Parse into sections (Level 1 → Level 2)
    sections = _parse_md_sections(content, path.name)
    if not sections:
        return {"status": "empty", "source": abs_path, "sections": 0, "cross_refs": 0}

    now = datetime.now(timezone.utc).isoformat()
    total_refs = 0

    for section in sections:
        cur = conn.execute(
            """INSERT INTO md_sections
               (source_file, source_path, section_level, section_title, section_path,
                content, char_count, sha256_hash, evolved_at)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (section["source_file"], abs_path, section["section_level"],
             section["section_title"], section["section_path"],
             section["content"], section["char_count"], sha, now),
        )
        section_id = cur.lastrowid

        # Extract and link cross-references (Level 3 → Level 4)
        refs = _extract_cross_refs(section_id, section["content"], section["section_title"])
        refs = _link_cross_refs_to_graph(conn, refs)
        for ref in refs:
            conn.execute(
                """INSERT INTO md_cross_refs (section_id, ref_type, ref_value, graph_node_id, graph_source, confidence)
                   VALUES (?, ?, ?, ?, ?, ?)""",
                (ref["section_id"], ref["ref_type"], ref["ref_value"],
                 ref.get("graph_node_id"), ref.get("graph_source"), ref.get("confidence", 1.0)),
            )
        total_refs += len(refs)

    # Log evolution
    conn.execute(
        """INSERT OR REPLACE INTO md_evolution_log
           (source_path, evolved_at, section_count, cross_ref_count, file_size_bytes, sha256_hash)
           VALUES (?, ?, ?, ?, ?, ?)""",
        (abs_path, now, len(sections), total_refs, path.stat().st_size, sha),
    )
    conn.commit()

    logger.info("Evolved '%s': %d sections, %d cross-refs", path.name, len(sections), total_refs)
    return {
        "status": "evolved",
        "source": abs_path,
        "file_name": path.name,
        "sections": len(sections),
        "cross_refs": total_refs,
        "chars": sum(s["char_count"] for s in sections),
    }


@retry_on_transient()
def evolve_all_md_files(conn: sqlite3.Connection, directory: str) -> Dict[str, Any]:
    """Evolve all .md files in a directory. Batch Level 1 → Level 5."""
    md_dir = Path(directory)
    if not md_dir.is_dir():
        raise ValueError(f"Not a directory: {directory}")

    results: Dict[str, Any] = {"evolved": 0, "skipped": 0, "errors": 0, "files": []}
    for md_file in sorted(md_dir.glob("*.md")):
        try:
            result = evolve_md_file(conn, str(md_file))
            if result["status"] == "evolved":
                results["evolved"] += 1
            else:
                results["skipped"] += 1
            results["files"].append(result)
        except Exception as e:
            logger.error("Failed to evolve '%s': %s", md_file.name, e)
            results["errors"] += 1
            results["files"].append({"status": "error", "source": str(md_file), "error": str(e)})

    logger.info("Batch evolution: %d evolved, %d skipped, %d errors",
                results["evolved"], results["skipped"], results["errors"])
    return results


# ── Evolved .md Query Functions ───────────────────────────────────

def search_evolved_knowledge(
    conn: sqlite3.Connection,
    query: str,
    section_level: Optional[int] = None,
    source_file: Optional[str] = None,
    limit: int = 20,
    offset: int = 0,
) -> Dict[str, Any]:
    """Full-text search across evolved .md sections. Level 5: executable query."""
    try:
        where_extra = ""
        params_extra: list = []
        if section_level:
            where_extra += " AND ms.section_level = ?"
            params_extra.append(section_level)
        if source_file:
            where_extra += " AND ms.source_file LIKE ?"
            params_extra.append(f"%{source_file}%")

        total = conn.execute(
            f"""SELECT COUNT(*) as cnt FROM md_sections_fts
                JOIN md_sections ms ON ms.id = md_sections_fts.rowid
                WHERE md_sections_fts MATCH ?{where_extra}""",
            [query] + params_extra,
        ).fetchone()["cnt"]

        rows = conn.execute(
            f"""SELECT ms.id, ms.source_file, ms.section_level, ms.section_title,
                       ms.section_path, ms.char_count,
                       snippet(md_sections_fts, 1, '>>>', '<<<', '...', 50) AS snippet
                FROM md_sections_fts
                JOIN md_sections ms ON ms.id = md_sections_fts.rowid
                WHERE md_sections_fts MATCH ?{where_extra}
                ORDER BY rank
                LIMIT ? OFFSET ?""",
            [query] + params_extra + [limit, offset],
        ).fetchall()

        return {
            "total": total, "count": len(rows), "offset": offset,
            "has_more": total > offset + len(rows),
            "next_offset": offset + len(rows) if total > offset + len(rows) else None,
            "results": [dict(r) for r in rows],
        }
    except sqlite3.OperationalError:
        return {"total": 0, "count": 0, "offset": 0, "has_more": False, "results": []}


def get_cross_refs(
    conn: sqlite3.Connection,
    ref_type: Optional[str] = None,
    ref_value: Optional[str] = None,
    limit: int = 50,
) -> List[Dict[str, Any]]:
    """Get cross-references, optionally filtered by type or value."""
    where_parts = ["1=1"]
    params: list = []
    if ref_type:
        where_parts.append("cr.ref_type = ?")
        params.append(ref_type)
    if ref_value:
        where_parts.append("cr.ref_value LIKE ?")
        params.append(f"%{ref_value}%")
    where = " AND ".join(where_parts)

    rows = conn.execute(
        f"""SELECT cr.*, ms.section_title, ms.source_file, ms.section_path
            FROM md_cross_refs cr
            JOIN md_sections ms ON ms.id = cr.section_id
            WHERE {where}
            ORDER BY cr.ref_type, cr.ref_value
            LIMIT ?""",
        params + [limit],
    ).fetchall()
    return [dict(r) for r in rows]


def get_evolution_stats(conn: sqlite3.Connection) -> Dict[str, Any]:
    """Get statistics about the .md evolution layer.

    Uses a single subquery block instead of 4 separate COUNT(*) calls.
    """
    counts = conn.execute(
        """SELECT
               (SELECT COUNT(*) FROM md_sections) AS section_count,
               (SELECT COUNT(*) FROM md_cross_refs) AS ref_count,
               (SELECT COUNT(*) FROM md_evolution_log) AS file_count,
               (SELECT COUNT(*) FROM md_cross_refs WHERE graph_node_id IS NOT NULL) AS linked_refs"""
    ).fetchone()

    ref_types = conn.execute(
        "SELECT ref_type, COUNT(*) as cnt FROM md_cross_refs GROUP BY ref_type ORDER BY cnt DESC"
    ).fetchall()

    files = conn.execute(
        "SELECT source_path, section_count, cross_ref_count, evolved_at FROM md_evolution_log ORDER BY evolved_at DESC"
    ).fetchall()

    ref_count = counts["ref_count"]
    linked_refs = counts["linked_refs"]
    return {
        "total_files_evolved": counts["file_count"],
        "total_sections": counts["section_count"],
        "total_cross_refs": ref_count,
        "graph_linked_refs": linked_refs,
        "link_rate": round(linked_refs / max(ref_count, 1) * 100, 1),
        "ref_types": [dict(r) for r in ref_types],
        "evolved_files": [dict(r) for r in files],
    }


# ── TXT Evolution ─────────────────────────────────────────────────

# Patterns for TXT section detection
_TXT_SEPARATOR_RE = re.compile(r"^[\s]*(═{3,}|─{3,}|\*{3,}|-{3,})[\s]*$")
_TXT_SAMPLE_MARKER_RE = re.compile(r"^===\s*SAMPLE FROM:\s*(.+?)\s*===$", re.IGNORECASE)
_TXT_EMOJI_HEADER_RE = re.compile(
    r"^[\s]*([\U0001F300-\U0001FAF8\u2600-\u27BF\u2702-\u27B0\u2705\u274C\u2714\u2716✓✅🔴📋])"
    r"\s*(.+)$"
)
_TXT_NUMBERED_RE = re.compile(r"^[\s]*(?:(?:\d{1,3})[.\)]\s+|Step\s+\d+[:.]\s*)", re.IGNORECASE)


def _is_allcaps_header(line: str) -> bool:
    """Return True if line is ≥5 chars and ≥60% uppercase letters."""
    stripped = line.strip()
    if len(stripped) < 5:
        return False
    alpha = [c for c in stripped if c.isalpha()]
    if not alpha:
        return False
    upper_ratio = sum(1 for c in alpha if c.isupper()) / len(alpha)
    return upper_ratio >= 0.60


def _parse_txt_sections(content: str, source_file: str) -> List[Dict[str, Any]]:
    """Parse a .txt file into sections using heuristic detection."""
    sections: List[Dict[str, Any]] = []
    lines = content.split("\n")
    current_title = "(preamble)"
    current_level = 1
    current_content: List[str] = []

    def _flush():
        text = "\n".join(current_content).strip()
        if text or current_title != "(preamble)":
            sections.append({
                "source_file": source_file,
                "section_level": current_level,
                "section_title": current_title,
                "section_path": current_title,
                "content": text,
                "char_count": len(text),
            })

    i = 0
    while i < len(lines):
        line = lines[i]

        # 1. Separator lines → section break (title is the next non-blank line)
        if _TXT_SEPARATOR_RE.match(line):
            _flush()
            current_content = []
            # Look ahead for a title line
            j = i + 1
            while j < len(lines) and not lines[j].strip():
                j += 1
            if j < len(lines) and lines[j].strip():
                current_title = lines[j].strip()
                current_level = 1
                i = j + 1
            else:
                current_title = f"Section {len(sections) + 1}"
                current_level = 1
                i += 1
            continue

        # 3. === SAMPLE FROM: ... === markers
        sample_m = _TXT_SAMPLE_MARKER_RE.match(line)
        if sample_m:
            _flush()
            current_content = []
            current_title = sample_m.group(1).strip()
            current_level = 1
            i += 1
            continue

        # 2. ALL-CAPS header lines
        if _is_allcaps_header(line) and not _TXT_SEPARATOR_RE.match(line):
            _flush()
            current_content = []
            current_title = line.strip()
            current_level = 1
            i += 1
            continue

        # 4. Emoji-prefixed header lines
        emoji_m = _TXT_EMOJI_HEADER_RE.match(line)
        if emoji_m:
            _flush()
            current_content = []
            current_title = line.strip()
            current_level = 1
            i += 1
            continue

        # 5. Numbered sections as subsection markers
        if _TXT_NUMBERED_RE.match(line) and line.strip():
            _flush()
            current_content = []
            current_title = line.strip()
            current_level = 2
            i += 1
            continue

        current_content.append(line)
        i += 1

    _flush()

    # 6. Fallback: if no sections were detected (only preamble), chunk by double-blank-line paragraphs
    if len(sections) <= 1 and len(content) > 2000:
        sections = []
        paragraphs = re.split(r"\n\s*\n\s*\n", content)
        chunk: List[str] = []
        chunk_chars = 0
        para_idx = 0
        for para in paragraphs:
            para = para.strip()
            if not para:
                continue
            if chunk_chars + len(para) > 2000 and chunk:
                para_idx += 1
                sections.append({
                    "source_file": source_file,
                    "section_level": 1,
                    "section_title": f"Chunk {para_idx}",
                    "section_path": f"Chunk {para_idx}",
                    "content": "\n\n".join(chunk),
                    "char_count": chunk_chars,
                })
                chunk = []
                chunk_chars = 0
            chunk.append(para)
            chunk_chars += len(para)
        if chunk:
            para_idx += 1
            sections.append({
                "source_file": source_file,
                "section_level": 1,
                "section_title": f"Chunk {para_idx}",
                "section_path": f"Chunk {para_idx}",
                "content": "\n\n".join(chunk),
                "char_count": chunk_chars,
            })

    return sections


@retry_on_transient()
def evolve_txt_file(conn: sqlite3.Connection, file_path: str) -> Dict[str, Any]:
    """Evolve a .txt file by detecting sections and cross-references."""
    path = Path(file_path)
    if not path.exists():
        raise FileNotFoundError(f"File not found: {file_path}")
    if path.suffix.lower() != ".txt":
        raise ValueError(f"Not a text file: {file_path}")

    abs_path = str(path.resolve())

    # Idempotency check
    existing = conn.execute(
        "SELECT 1 FROM md_evolution_log WHERE source_path = ?", (abs_path,)
    ).fetchone()
    if existing:
        return {"status": "already_evolved", "source": abs_path, "sections": 0, "cross_refs": 0}

    content = path.read_text(encoding="utf-8", errors="replace")
    sha = hashlib.sha256(content.encode("utf-8")).hexdigest()

    sections = _parse_txt_sections(content, path.name)
    if not sections:
        return {"status": "empty", "source": abs_path, "sections": 0, "cross_refs": 0}

    now = datetime.now(timezone.utc).isoformat()
    total_refs = 0

    for section in sections:
        cur = conn.execute(
            """INSERT INTO md_sections
               (source_file, source_path, section_level, section_title, section_path,
                content, char_count, sha256_hash, evolved_at)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (section["source_file"], abs_path, section["section_level"],
             section["section_title"], section["section_path"],
             section["content"], section["char_count"], sha, now),
        )
        section_id = cur.lastrowid

        refs = _extract_cross_refs(section_id, section["content"], section["section_title"])
        refs = _link_cross_refs_to_graph(conn, refs)
        for ref in refs:
            conn.execute(
                """INSERT INTO md_cross_refs (section_id, ref_type, ref_value, graph_node_id, graph_source, confidence)
                   VALUES (?, ?, ?, ?, ?, ?)""",
                (ref["section_id"], ref["ref_type"], ref["ref_value"],
                 ref.get("graph_node_id"), ref.get("graph_source"), ref.get("confidence", 1.0)),
            )
        total_refs += len(refs)

    conn.execute(
        """INSERT OR REPLACE INTO md_evolution_log
           (source_path, evolved_at, section_count, cross_ref_count, file_size_bytes, sha256_hash)
           VALUES (?, ?, ?, ?, ?, ?)""",
        (abs_path, now, len(sections), total_refs, path.stat().st_size, sha),
    )
    conn.commit()

    logger.info("Evolved TXT '%s': %d sections, %d cross-refs", path.name, len(sections), total_refs)
    return {
        "status": "evolved",
        "source": abs_path,
        "file_name": path.name,
        "sections": len(sections),
        "cross_refs": total_refs,
        "chars": sum(s["char_count"] for s in sections),
    }


@retry_on_transient()
def evolve_all_txt_files(conn: sqlite3.Connection, directory: str) -> Dict[str, Any]:
    """Evolve all .txt files in a directory."""
    txt_dir = Path(directory)
    if not txt_dir.is_dir():
        raise ValueError(f"Not a directory: {directory}")

    results: Dict[str, Any] = {"evolved": 0, "skipped": 0, "errors": 0, "files": []}
    for txt_file in sorted(txt_dir.glob("*.txt")):
        try:
            result = evolve_txt_file(conn, str(txt_file))
            if result["status"] == "evolved":
                results["evolved"] += 1
            else:
                results["skipped"] += 1
            results["files"].append(result)
        except Exception as e:
            logger.error("Failed to evolve '%s': %s", txt_file.name, e)
            results["errors"] += 1
            results["files"].append({"status": "error", "source": str(txt_file), "error": str(e)})

    logger.info("Batch TXT evolution: %d evolved, %d skipped, %d errors",
                results["evolved"], results["skipped"], results["errors"])
    return results


# ── PDF Pages Evolution Bridge ────────────────────────────────────

@retry_on_transient()
def evolve_from_pages(conn: sqlite3.Connection, document_id: Optional[int] = None) -> Dict[str, Any]:
    """Evolve ingested PDF pages into the cross-reference knowledge layer.

    If document_id is given, evolve just that document. Otherwise evolve all.
    Each page becomes an md_sections entry with section_level=0.
    """
    # Find documents to evolve
    if document_id is not None:
        docs = conn.execute(
            "SELECT id, file_path, file_name FROM documents WHERE id = ?", (document_id,)
        ).fetchall()
    else:
        docs = conn.execute("SELECT id, file_path, file_name FROM documents").fetchall()

    if not docs:
        return {"status": "no_documents", "documents": 0, "sections": 0, "cross_refs": 0}

    total_sections = 0
    total_refs = 0
    docs_evolved = 0
    docs_skipped = 0
    now = datetime.now(timezone.utc).isoformat()

    for doc in docs:
        doc_id = doc["id"]
        file_path = doc["file_path"]
        file_name = doc["file_name"]

        # Idempotency: skip if already evolved
        existing = conn.execute(
            "SELECT 1 FROM md_evolution_log WHERE source_path = ?", (file_path,)
        ).fetchone()
        if existing:
            docs_skipped += 1
            continue

        pages = conn.execute(
            "SELECT page_number, text_content FROM pages WHERE document_id = ? ORDER BY page_number",
            (doc_id,),
        ).fetchall()
        if not pages:
            docs_skipped += 1
            continue

        doc_refs = 0
        for page in pages:
            page_num = page["page_number"]
            text = page["text_content"]
            sha = hashlib.sha256(text.encode("utf-8")).hexdigest()

            cur = conn.execute(
                """INSERT INTO md_sections
                   (source_file, source_path, section_level, section_title, section_path,
                    content, char_count, sha256_hash, evolved_at)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                (file_name, file_path, 0, f"Page {page_num}",
                 f"{file_name} > Page {page_num}", text, len(text), sha, now),
            )
            section_id = cur.lastrowid

            refs = _extract_cross_refs(section_id, text, f"Page {page_num}")
            refs = _link_cross_refs_to_graph(conn, refs)
            for ref in refs:
                conn.execute(
                    """INSERT INTO md_cross_refs (section_id, ref_type, ref_value, graph_node_id, graph_source, confidence)
                       VALUES (?, ?, ?, ?, ?, ?)""",
                    (ref["section_id"], ref["ref_type"], ref["ref_value"],
                     ref.get("graph_node_id"), ref.get("graph_source"), ref.get("confidence", 1.0)),
                )
            doc_refs += len(refs)

        # Log evolution for this document
        conn.execute(
            """INSERT OR REPLACE INTO md_evolution_log
               (source_path, evolved_at, section_count, cross_ref_count, file_size_bytes, sha256_hash)
               VALUES (?, ?, ?, ?, ?, ?)""",
            (file_path, now, len(pages), doc_refs, 0, ""),
        )
        conn.commit()

        total_sections += len(pages)
        total_refs += doc_refs
        docs_evolved += 1
        logger.info("Evolved PDF pages for '%s': %d pages, %d cross-refs", file_name, len(pages), doc_refs)

    return {
        "status": "evolved" if docs_evolved > 0 else "already_evolved",
        "documents": docs_evolved,
        "skipped": docs_skipped,
        "sections": total_sections,
        "cross_refs": total_refs,
    }


# ══════════════════════════════════════════════════════════════════
#  SYSTEM REGISTRY + MASTER CSV INGESTION
# ══════════════════════════════════════════════════════════════════

# Known LitigationOS subsystem locations
_KNOWN_SYSTEMS: List[Dict[str, str]] = [
    {"path": r"D:\LITIGATIONOS_DATA", "type": "data", "name": "LITIGATIONOS_DATA"},
    {"path": r"D:\LitigationOS-Watson-FINAL-PACKAGE", "type": "data", "name": "Watson-FINAL-PACKAGE"},
    {"path": r"G:\CAPSTONE", "type": "capstone", "name": "CAPSTONE"},
    {"path": r"H:\MEEK", "type": "meek_lane", "name": "MEEK"},
    {"path": r"H:\LitigationOS-Ultimate", "type": "compiler", "name": "LitigationOS-Ultimate"},
    {"path": r"H:\LitigationOS_CompilerRuntime_v1_2_0_FULL", "type": "compiler", "name": "CompilerRuntime_v1.2"},
    {"path": r"H:\LitigationOS_Authority_Integrated_v3", "type": "graph", "name": "Authority_Integrated_v3"},
    {"path": r"H:\SuperBloom_STACK_v2026-01-22.1", "type": "graph", "name": "SuperBloom_ERD"},
    {"path": r"F:\LitigationOS_AutopilotSuite_v1_0_0", "type": "autopilot", "name": "AutopilotSuite"},
    {"path": r"H:\LitigationOS_GraphContract_v1_0_0", "type": "graph", "name": "GraphContract"},
    {"path": r"C:\Users\andre\LitigationOS-Desktop", "type": "gui", "name": "LitigationOS-Desktop"},
    {"path": r"C:\Users\andre\LitigationOS-Mobile", "type": "gui", "name": "LitigationOS-Mobile"},
    # MEEK234 stacks
    {"path": r"F:\MEEK234_STACK_v1", "type": "meek_lane", "name": "MEEK234_STACK_v1"},
    {"path": r"F:\MEEK234_STACK_v2", "type": "meek_lane", "name": "MEEK234_STACK_v2"},
    {"path": r"F:\MEEK234_STACK_v3", "type": "meek_lane", "name": "MEEK234_STACK_v3"},
    {"path": r"H:\MEEK234_STACK_v4", "type": "meek_lane", "name": "MEEK234_STACK_v4"},
    {"path": r"H:\MEEK234_STACK_v5", "type": "meek_lane", "name": "MEEK234_STACK_v5"},
    # NUCLEUS_APEX
    {"path": r"H:\NUCLEUS_APEX_v1", "type": "nucleus", "name": "NUCLEUS_APEX_v1"},
    {"path": r"H:\NUCLEUS_APEX_v2", "type": "nucleus", "name": "NUCLEUS_APEX_v2"},
    {"path": r"H:\NUCLEUS_APEX_v3", "type": "nucleus", "name": "NUCLEUS_APEX_v3"},
]


def _scan_directory(dir_path: str) -> Dict[str, Any]:
    """Walk a directory and return file_count, total_size_mb, version, and capabilities."""
    file_count = 0
    total_size = 0
    version = None
    capabilities = None
    metadata: Dict[str, Any] = {}

    for root, _dirs, files in os.walk(dir_path):
        for fname in files:
            fpath = os.path.join(root, fname)
            try:
                total_size += os.path.getsize(fpath)
            except OSError:
                pass
            file_count += 1

            # Extract version/capabilities from well-known files at top level
            if root == dir_path:
                if fname.lower() == "manifest.json":
                    try:
                        with open(fpath, "r", encoding="utf-8") as f:
                            data = json.load(f)
                        version = version or data.get("version")
                        capabilities = capabilities or data.get("capabilities")
                        metadata["manifest"] = {k: v for k, v in data.items()
                                                 if k in ("name", "version", "description", "capabilities")}
                    except Exception:
                        pass
                elif fname.lower() == "package.json":
                    try:
                        with open(fpath, "r", encoding="utf-8") as f:
                            data = json.load(f)
                        version = version or data.get("version")
                        metadata["package"] = {k: v for k, v in data.items()
                                                if k in ("name", "version", "description")}
                    except Exception:
                        pass
                elif fname.lower() in ("readme.md", "readme.txt", "readme"):
                    try:
                        with open(fpath, "r", encoding="utf-8", errors="replace") as f:
                            header = f.read(2048)
                        # Try to extract version from first few lines
                        for line in header.splitlines()[:10]:
                            m = re.search(r'v(?:ersion)?\s*[:\-]?\s*(\d+\.\d+[\.\d]*)', line, re.IGNORECASE)
                            if m and not version:
                                version = m.group(1)
                                break
                    except Exception:
                        pass

    return {
        "file_count": file_count,
        "total_size_mb": round(total_size / (1024 * 1024), 2),
        "version": version,
        "capabilities": json.dumps(capabilities) if capabilities else None,
        "metadata": json.dumps(metadata) if metadata else None,
    }


@retry_on_transient()
def scan_all_systems(conn: sqlite3.Connection) -> Dict[str, Any]:
    """Discover and register all LitigationOS subsystems across all drives."""
    now = datetime.now(timezone.utc).isoformat()
    registered = 0
    skipped = 0
    missing = 0
    by_type: Dict[str, int] = {}

    for sys_info in _KNOWN_SYSTEMS:
        dir_path = sys_info["path"]
        sys_type = sys_info["type"]
        sys_name = sys_info["name"]
        drive = os.path.splitdrive(dir_path)[0] or None
        sys_id = f"{sys_type}:{sys_name}"

        if not os.path.isdir(dir_path):
            missing += 1
            logger.debug("System path not found: %s", dir_path)
            continue

        try:
            info = _scan_directory(dir_path)
        except Exception as e:
            logger.warning("Failed to scan %s: %s", dir_path, e)
            skipped += 1
            continue

        conn.execute(
            """INSERT OR REPLACE INTO system_registry
               (id, system_name, system_type, drive, path, version, status,
                capabilities, file_count, total_size_mb, last_scanned, metadata)
               VALUES (?, ?, ?, ?, ?, ?, 'discovered', ?, ?, ?, ?, ?)""",
            (sys_id, sys_name, sys_type, drive, dir_path,
             info["version"], info["capabilities"],
             info["file_count"], info["total_size_mb"], now, info["metadata"]),
        )
        registered += 1
        by_type[sys_type] = by_type.get(sys_type, 0) + 1
        logger.info("Registered system %s (%s): %d files, %.1f MB",
                     sys_name, sys_type, info["file_count"], info["total_size_mb"])

    conn.commit()
    return {
        "registered": registered,
        "missing": missing,
        "skipped": skipped,
        "by_type": by_type,
    }


@retry_on_transient()
def ingest_master_csv(conn: sqlite3.Connection, csv_path: str, dataset_name: str) -> Dict[str, Any]:
    """Ingest a master CSV file from D:\\LITIGATIONOS_DATA into master_csv_data + FTS."""
    if not os.path.isfile(csv_path):
        raise FileNotFoundError(f"CSV file not found: {csv_path}")

    source_file = os.path.basename(csv_path)

    # Try utf-8 first, fall back to latin-1
    rows_inserted = 0
    for encoding in ("utf-8", "latin-1"):
        try:
            with open(csv_path, "r", encoding=encoding, newline="") as f:
                reader = csv.DictReader(f)
                for row_num, row in enumerate(reader, start=1):
                    row_json = json.dumps(row, ensure_ascii=False)
                    conn.execute(
                        """INSERT INTO master_csv_data (dataset, row_data, source_file, row_number)
                           VALUES (?, ?, ?, ?)""",
                        (dataset_name, row_json, source_file, row_num),
                    )
                    rows_inserted += 1
            break  # success, stop trying encodings
        except UnicodeDecodeError:
            if encoding == "latin-1":
                raise
            rows_inserted = 0
            continue

    conn.commit()
    logger.info("Ingested %d rows from '%s' as dataset '%s'", rows_inserted, source_file, dataset_name)
    return {"rows": rows_inserted, "dataset": dataset_name}


@retry_on_transient()
def ingest_all_master_csvs(conn: sqlite3.Connection, data_dir: str = r"D:\LITIGATIONOS_DATA") -> Dict[str, Any]:
    """Ingest all master CSV files from the data directory."""
    if not os.path.isdir(data_dir):
        return {"status": "directory_not_found", "dir": data_dir, "datasets": []}

    pattern = os.path.join(data_dir, "MASTER_*.csv")
    csv_files = sorted(_glob_mod.glob(pattern))

    results: List[Dict[str, Any]] = []
    total_rows = 0
    for csv_path in csv_files:
        fname = os.path.basename(csv_path)
        # Derive dataset name: MASTER_CITATIONS.csv → citations
        dataset_name = fname.replace("MASTER_", "").replace(".csv", "").lower()
        try:
            r = ingest_master_csv(conn, csv_path, dataset_name)
            results.append(r)
            total_rows += r["rows"]
        except Exception as e:
            logger.warning("Failed to ingest %s: %s", fname, e)
            results.append({"dataset": dataset_name, "rows": 0, "error": str(e)})

    return {"status": "ok", "datasets": results, "total_rows": total_rows, "files_found": len(csv_files)}


def search_master_data(conn: sqlite3.Connection, query: str, dataset: Optional[str] = None, limit: int = 20) -> List[Dict]:
    """FTS5 search across all master CSV datasets."""
    if dataset:
        rows = conn.execute(
            """SELECT m.id, m.dataset, m.row_data, m.source_file, m.row_number
               FROM master_csv_fts f
               JOIN master_csv_data m ON f.rowid = m.id
               WHERE master_csv_fts MATCH ? AND m.dataset = ?
               LIMIT ?""",
            (query, dataset, limit),
        ).fetchall()
    else:
        rows = conn.execute(
            """SELECT m.id, m.dataset, m.row_data, m.source_file, m.row_number
               FROM master_csv_fts f
               JOIN master_csv_data m ON f.rowid = m.id
               WHERE master_csv_fts MATCH ?
               LIMIT ?""",
            (query, limit),
        ).fetchall()

    results = []
    for row in rows:
        try:
            parsed = json.loads(row["row_data"])
        except (json.JSONDecodeError, TypeError):
            parsed = row["row_data"]
        results.append({
            "id": row["id"],
            "dataset": row["dataset"],
            "row_data": parsed,
            "source_file": row["source_file"],
            "row_number": row["row_number"],
        })
    return results


# ══════════════════════════════════════════════════════════════════
#  AUTONOMOUS INTELLIGENCE ENGINES (Slots 1-5)
# ══════════════════════════════════════════════════════════════════

# ── SLOT 1: TF-IDF Vector Search ────────────────────────────────

_STOPWORDS = frozenset(
    "a about above after again against all am an and any are aren't as at be because been before being below "
    "between both but by can't cannot could couldn't did didn't do does doesn't doing don't down during each "
    "few for from further get got had hadn't has hasn't have haven't having he he'd he'll he's her here "
    "here's hers herself him himself his how how's i i'd i'll i'm i've if in into is isn't it it's its "
    "itself let's me more most mustn't my myself no nor not of off on once only or other ought our ours "
    "ourselves out over own same shan't she she'd she'll she's should shouldn't so some such than that "
    "that's the their theirs them themselves then there there's these they they'd they'll they're they've "
    "this those through to too under until up upon very was wasn't we we'd we'll we're we've were weren't "
    "what what's when when's where where's which while who who's whom why why's will with won't would "
    "wouldn't you you'd you'll you're you've your yours yourself yourselves also just shall may might "
    "however therefore thus hence moreover furthermore nevertheless nonetheless accordingly consequently "
    "although though even still already yet another each every either neither much many such the".split()
)


def _tokenize(text: str) -> List[str]:
    """Lowercase, split on non-alpha, remove stopwords and short tokens."""
    tokens = re.split(r"[^a-zA-Z]+", text.lower())
    return [t for t in tokens if len(t) > 2 and t not in _STOPWORDS]


@retry_on_transient()
def build_tfidf_index(conn: sqlite3.Connection) -> Dict[str, Any]:
    """Build a TF-IDF index over all md_sections for semantic similarity queries.
    Uses Python stdlib math — no numpy/sklearn needed."""
    import math as _math
    from collections import Counter as _Counter

    conn.execute("""CREATE TABLE IF NOT EXISTS tfidf_index (
        section_id INTEGER PRIMARY KEY,
        vector TEXT
    )""")
    conn.execute("DELETE FROM tfidf_index")

    rows = conn.execute("SELECT id, content FROM md_sections").fetchall()
    if not rows:
        conn.commit()
        return {"sections_indexed": 0, "vocabulary_size": 0}

    # Tokenize all documents
    doc_tokens: Dict[int, List[str]] = {}
    for row in rows:
        doc_tokens[row["id"]] = _tokenize(row["content"])

    total_docs = len(doc_tokens)

    # Compute document frequency for each term
    df: Dict[str, int] = {}
    for tokens in doc_tokens.values():
        for t in set(tokens):
            df[t] = df.get(t, 0) + 1

    # IDF
    idf: Dict[str, float] = {}
    for term, freq in df.items():
        idf[term] = _math.log((total_docs + 1) / (freq + 1)) + 1.0

    vocabulary: set = set()
    for sec_id, tokens in doc_tokens.items():
        if not tokens:
            continue
        tf_counts = _Counter(tokens)
        max_tf = max(tf_counts.values())
        scores: Dict[str, float] = {}
        for term, count in tf_counts.items():
            scores[term] = (count / max_tf) * idf.get(term, 1.0)
        top = sorted(scores.items(), key=lambda x: x[1], reverse=True)[:50]
        vector = {t: round(s, 6) for t, s in top}
        vocabulary.update(vector.keys())
        conn.execute(
            "INSERT INTO tfidf_index (section_id, vector) VALUES (?, ?)",
            (sec_id, json.dumps(vector)),
        )

    conn.commit()
    return {"sections_indexed": len(doc_tokens), "vocabulary_size": len(vocabulary)}


def vector_search(conn: sqlite3.Connection, query: str, top_k: int = 10) -> List[Dict]:
    """Semantic similarity search using TF-IDF cosine similarity."""
    import math as _math
    from collections import Counter as _Counter

    query_tokens = _tokenize(query)
    if not query_tokens:
        return []

    qtf = _Counter(query_tokens)
    max_qtf = max(qtf.values())
    q_vec: Dict[str, float] = {t: c / max_qtf for t, c in qtf.items()}

    rows = conn.execute("SELECT section_id, vector FROM tfidf_index").fetchall()
    if not rows:
        return []

    scored: List[Tuple[int, float]] = []
    for row in rows:
        doc_vec: Dict[str, float] = json.loads(row["vector"])
        dot = 0.0
        for t, qw in q_vec.items():
            if t in doc_vec:
                dot += qw * doc_vec[t]
        if dot == 0.0:
            continue
        mag_q = _math.sqrt(sum(v * v for v in q_vec.values()))
        mag_d = _math.sqrt(sum(v * v for v in doc_vec.values()))
        score = dot / (mag_q * mag_d) if (mag_q * mag_d) > 0 else 0.0
        scored.append((row["section_id"], score))

    scored.sort(key=lambda x: x[1], reverse=True)
    top = scored[:top_k]

    results: List[Dict] = []
    for sec_id, score in top:
        sec = conn.execute(
            "SELECT id, section_title, content, source_file FROM md_sections WHERE id = ?",
            (sec_id,),
        ).fetchone()
        if sec:
            snippet = sec["content"][:200] + ("..." if len(sec["content"]) > 200 else "")
            results.append({
                "section_id": sec["id"],
                "title": sec["section_title"],
                "source_file": sec["source_file"],
                "snippet": snippet,
                "score": round(score, 4),
            })
    return results


# ── SLOT 2: Temporal Deadline Reasoner ──────────────────────────

_MCR_TIMINGS: Dict[str, Dict[str, Any]] = {
    "MCR 2.108": {
        "triggers": ["motion_filed", "motion_served"],
        "response_days": 21,
        "reply_days": 7,
        "description": "Response to motion = 21 days; Reply = 7 days after response",
    },
    "MCR 2.119": {
        "triggers": ["motion_filed", "motion_hearing"],
        "notice_personal_days": 9,
        "notice_mail_days": 14,
        "description": "Motion hearing notice = 9 days (personal) / 14 days (mail)",
    },
    "MCR 7.205": {
        "triggers": ["order_entered"],
        "appeal_days": 21,
        "description": "Leave to appeal = 21 days from order",
    },
    "MCR 3.210": {
        "triggers": ["motion_filed", "temporary_order"],
        "notice_days": 14,
        "description": "Temporary orders = heard on 14 days notice",
    },
    "MCR 2.107": {
        "triggers": ["service_completed", "service_required"],
        "personal_days": 0,
        "mail_add_days": 3,
        "description": "Service methods + timing; add 3 days for mailing (MCR 1.108)",
    },
}

_TIMING_PATTERN = re.compile(
    r"(?:within|not\s+less\s+than|not\s+later\s+than)\s+(\d+)\s+days", re.IGNORECASE
)
_DAYS_BEFORE_PATTERN = re.compile(r"(\d+)\s+days?\s+before", re.IGNORECASE)


def _add_business_days(start_date: datetime, days: int) -> datetime:
    """Add business days (skip weekends). MCR 1.108 compliant."""
    from datetime import timedelta
    current = start_date
    added = 0
    while added < days:
        current += timedelta(days=1)
        if current.weekday() < 5:
            added += 1
    return current


def compute_deadlines(
    conn: sqlite3.Connection,
    trigger_event: str,
    trigger_date: str,
    jurisdiction: str = "MI",
) -> List[Dict]:
    """Compute court deadlines from a trigger event using MCR timing rules.

    Args:
        trigger_event: e.g. 'motion_filed', 'order_entered', 'service_completed'
        trigger_date: ISO date string 'YYYY-MM-DD'
        jurisdiction: 'MI' for Michigan
    """
    from datetime import timedelta

    base_date = datetime.strptime(trigger_date, "%Y-%m-%d")
    today = datetime.now()
    deadlines: List[Dict] = []

    for rule, info in _MCR_TIMINGS.items():
        if trigger_event not in info["triggers"]:
            continue
        if "response_days" in info:
            dl = _add_business_days(base_date, info["response_days"])
            deadlines.append({
                "rule": rule,
                "deadline": dl.strftime("%Y-%m-%d"),
                "description": f"Response due ({info['response_days']} business days)",
                "days_remaining": (dl - today).days,
            })
        if "reply_days" in info and "response_days" in info:
            response_dl = _add_business_days(base_date, info["response_days"])
            reply_dl = _add_business_days(response_dl, info["reply_days"])
            deadlines.append({
                "rule": rule,
                "deadline": reply_dl.strftime("%Y-%m-%d"),
                "description": f"Reply due ({info['reply_days']} business days after response deadline)",
                "days_remaining": (reply_dl - today).days,
            })
        if "notice_personal_days" in info:
            dl = _add_business_days(base_date, info["notice_personal_days"])
            deadlines.append({
                "rule": rule,
                "deadline": dl.strftime("%Y-%m-%d"),
                "description": f"Hearing notice (personal service, {info['notice_personal_days']} days)",
                "days_remaining": (dl - today).days,
            })
        if "notice_mail_days" in info:
            dl = _add_business_days(base_date, info["notice_mail_days"])
            deadlines.append({
                "rule": rule,
                "deadline": dl.strftime("%Y-%m-%d"),
                "description": f"Hearing notice (mail service, {info['notice_mail_days']} days)",
                "days_remaining": (dl - today).days,
            })
        if "appeal_days" in info:
            dl = _add_business_days(base_date, info["appeal_days"])
            deadlines.append({
                "rule": rule,
                "deadline": dl.strftime("%Y-%m-%d"),
                "description": f"Appeal deadline ({info['appeal_days']} business days)",
                "days_remaining": (dl - today).days,
            })
        if "notice_days" in info:
            dl = _add_business_days(base_date, info["notice_days"])
            deadlines.append({
                "rule": rule,
                "deadline": dl.strftime("%Y-%m-%d"),
                "description": f"Notice required ({info['notice_days']} business days)",
                "days_remaining": (dl - today).days,
            })
        if "mail_add_days" in info:
            dl = base_date + timedelta(days=info["mail_add_days"])
            deadlines.append({
                "rule": rule + " (MCR 1.108 mailing add-on)",
                "deadline": dl.strftime("%Y-%m-%d"),
                "description": f"+{info['mail_add_days']} calendar days added for mailing",
                "days_remaining": (dl - today).days,
            })

    # Search rules_text for additional timing rules
    try:
        rule_rows = conn.execute(
            """SELECT rule, context FROM rules_text
               WHERE context LIKE ? OR context LIKE ?
               LIMIT 20""",
            (f"%{trigger_event}%", f"%{trigger_event.replace('_', ' ')}%"),
        ).fetchall()
        for rr in rule_rows:
            for m in _TIMING_PATTERN.finditer(rr["context"] or ""):
                days = int(m.group(1))
                dl = _add_business_days(base_date, days)
                deadlines.append({
                    "rule": rr["rule"],
                    "deadline": dl.strftime("%Y-%m-%d"),
                    "description": f"Within {days} days (from rules_text)",
                    "days_remaining": (dl - today).days,
                })
            for m in _DAYS_BEFORE_PATTERN.finditer(rr["context"] or ""):
                days = int(m.group(1))
                dl = base_date - timedelta(days=days)
                deadlines.append({
                    "rule": rr["rule"],
                    "deadline": dl.strftime("%Y-%m-%d"),
                    "description": f"{days} days before trigger (from rules_text)",
                    "days_remaining": (dl - today).days,
                })
    except sqlite3.OperationalError:
        pass  # rules_text may not exist yet

    deadlines.sort(key=lambda d: d["deadline"])
    return deadlines


# ── SLOT 3: Red Team Validator ──────────────────────────────────

def red_team_validate(conn: sqlite3.Connection, claim_text: str) -> Dict[str, Any]:
    """Adversarial validation of a legal claim.
    Checks: authority grounding, evidence linking, contradiction detection.
    Returns severity-scored findings."""
    findings: List[Dict[str, Any]] = []
    rule_refs_found = 0
    rule_refs_total = 0
    evidence_found = 0
    evidence_claims = 0
    contradictions = 0

    # 1. Authority grounding — find MCR/MCL/caselaw references in claim
    rule_matches = list(_RULE_PATTERN.finditer(claim_text))
    rule_refs_total = max(len(rule_matches), 1)
    for m in rule_matches:
        ref_val = f"{m.group(1)} {m.group(2)}"
        try:
            hit = conn.execute(
                "SELECT id FROM md_cross_refs WHERE ref_value LIKE ? LIMIT 1",
                (f"%{ref_val}%",),
            ).fetchone()
            if not hit:
                hit = conn.execute(
                    "SELECT id FROM court_rules WHERE rule LIKE ? LIMIT 1",
                    (f"%{ref_val}%",),
                ).fetchone()
            if hit:
                rule_refs_found += 1
            else:
                findings.append({
                    "type": "authority", "severity": "HIGH",
                    "message": f"Rule {ref_val} cited but not found in knowledge base",
                    "ref": ref_val,
                })
        except sqlite3.OperationalError:
            pass

    # 2. Evidence linking — search pages_fts for supporting evidence
    claim_keywords = _tokenize(claim_text)
    key_phrases = claim_keywords[:10]
    for phrase in key_phrases:
        if len(phrase) < 4:
            continue
        evidence_claims += 1
        try:
            hit = conn.execute(
                "SELECT COUNT(*) as cnt FROM pages_fts WHERE pages_fts MATCH ?",
                (phrase,),
            ).fetchone()
            if hit and hit["cnt"] > 0:
                evidence_found += 1
        except sqlite3.OperationalError:
            pass

    evidence_claims = max(evidence_claims, 1)

    # 3. Contradiction detection
    negation_terms = ["denied", "overruled", "rejected", "dismissed", "contrary", "incorrect", "false"]
    for neg in negation_terms:
        try:
            for kw in key_phrases[:3]:
                if len(kw) < 4:
                    continue
                hit = conn.execute(
                    "SELECT COUNT(*) as cnt FROM pages_fts WHERE pages_fts MATCH ?",
                    (f"{neg} {kw}",),
                ).fetchone()
                if hit and hit["cnt"] > 0:
                    contradictions += 1
                    findings.append({
                        "type": "contradiction", "severity": "MEDIUM",
                        "message": f"Potential contradiction found: '{neg}' near '{kw}'",
                    })
                    break
        except sqlite3.OperationalError:
            pass

    if not rule_matches:
        findings.append({
            "type": "authority", "severity": "CRITICAL",
            "message": "No legal authority (MCR/MCL/MRE) cited in claim",
        })

    authority_score = int((rule_refs_found / rule_refs_total) * 100) if rule_refs_total else 0
    evidence_score = int((evidence_found / evidence_claims) * 100)
    consistency_score = max(0, 100 - (contradictions * 20))
    overall_score = int((authority_score * 0.4) + (evidence_score * 0.35) + (consistency_score * 0.25))

    if authority_score < 30:
        findings.append({"type": "authority", "severity": "CRITICAL",
                         "message": f"Authority grounding critically low ({authority_score}%)"})
    elif authority_score < 60:
        findings.append({"type": "authority", "severity": "HIGH",
                         "message": f"Authority grounding weak ({authority_score}%)"})
    if evidence_score < 30:
        findings.append({"type": "evidence", "severity": "HIGH",
                         "message": f"Evidence support critically low ({evidence_score}%)"})
    if consistency_score < 60:
        findings.append({"type": "consistency", "severity": "HIGH",
                         "message": f"Consistency concerns detected ({consistency_score}%)"})

    return {
        "overall_score": overall_score,
        "authority_score": authority_score,
        "evidence_score": evidence_score,
        "consistency_score": consistency_score,
        "findings": findings,
        "filing_ready": overall_score >= 70 and authority_score >= 50 and not any(
            f["severity"] == "CRITICAL" for f in findings
        ),
    }


# ── SLOT 4: Evidence Chain Prover ───────────────────────────────

def trace_evidence_chain(conn: sqlite3.Connection, claim: str) -> Dict[str, Any]:
    """Trace a claim back through the evidence chain to source documents.
    Returns the full provenance path: claim → cross_ref → section → document → page."""
    chains: List[Dict[str, Any]] = []
    gaps: List[str] = []

    # 1. Search md_sections_fts for sections matching the claim
    matching_sections: List[Dict] = []
    try:
        claim_query = " OR ".join(t for t in _tokenize(claim)[:8] if len(t) > 3)
        if claim_query:
            rows = conn.execute(
                """SELECT s.id, s.section_title, s.source_file, s.source_path,
                          snippet(md_sections_fts, 1, '>>>', '<<<', '...', 30) AS snippet
                   FROM md_sections_fts
                   JOIN md_sections s ON s.id = md_sections_fts.rowid
                   WHERE md_sections_fts MATCH ?
                   ORDER BY rank LIMIT 20""",
                (claim_query,),
            ).fetchall()
            matching_sections = [dict(r) for r in rows]
    except sqlite3.OperationalError:
        gaps.append("md_sections_fts not available")

    if not matching_sections:
        gaps.append("No matching sections found for claim")
        return {"chains": [], "completeness": 0, "gaps": gaps}

    for sec in matching_sections:
        chain: Dict[str, Any] = {
            "section_id": sec["id"],
            "section_title": sec["section_title"],
            "source_file": sec["source_file"],
            "section_path": sec.get("source_path", ""),
            "snippet": sec.get("snippet", ""),
            "cross_refs": [],
            "sources": [],
        }

        # 2. Get cross_refs for this section
        try:
            ref_rows = conn.execute(
                """SELECT ref_type, ref_value, graph_node_id, graph_source
                   FROM md_cross_refs WHERE section_id = ?""",
                (sec["id"],),
            ).fetchall()
            chain["cross_refs"] = [dict(r) for r in ref_rows]
        except sqlite3.OperationalError:
            gaps.append(f"md_cross_refs not available for section {sec['id']}")

        # 3. For each cross_ref, trace to source tables
        for ref in chain["cross_refs"]:
            source: Dict[str, Any] = {"ref": ref["ref_value"], "type": ref["ref_type"]}

            if ref.get("graph_node_id"):
                try:
                    node = conn.execute(
                        "SELECT id, label, node_type, graph_source FROM graph_nodes WHERE id = ? AND graph_source = ?",
                        (ref["graph_node_id"], ref.get("graph_source", "")),
                    ).fetchone()
                    if node:
                        source["graph_node"] = dict(node)
                except sqlite3.OperationalError:
                    pass

            if ref["ref_type"] == "rule":
                try:
                    rule_row = conn.execute(
                        "SELECT rule, chapter, context, source_doc FROM court_rules WHERE rule LIKE ? LIMIT 1",
                        (f"%{ref['ref_value']}%",),
                    ).fetchone()
                    if rule_row:
                        source["court_rule"] = dict(rule_row)
                except sqlite3.OperationalError:
                    pass

            try:
                page_hit = conn.execute(
                    """SELECT p.id, p.document_id, p.page_number, d.file_name,
                              snippet(pages_fts, 0, '>>>', '<<<', '...', 20) AS snippet
                       FROM pages_fts
                       JOIN pages p ON p.id = pages_fts.rowid
                       JOIN documents d ON d.id = p.document_id
                       WHERE pages_fts MATCH ?
                       LIMIT 3""",
                    (ref["ref_value"],),
                ).fetchall()
                if page_hit:
                    source["pages"] = [dict(p) for p in page_hit]
            except sqlite3.OperationalError:
                pass

            chain["sources"].append(source)

        total_refs = len(chain["cross_refs"])
        sourced_refs = sum(
            1 for s in chain["sources"]
            if s.get("graph_node") or s.get("court_rule") or s.get("pages")
        )
        chain["completeness"] = int((sourced_refs / max(total_refs, 1)) * 100)
        chains.append(chain)

    overall_completeness = int(sum(c["completeness"] for c in chains) / max(len(chains), 1))
    return {"chains": chains, "completeness": overall_completeness, "gaps": gaps}


# ── SLOT 5: Swarm Dispatch Protocol ─────────────────────────────

def dispatch_to_swarm(conn: sqlite3.Connection, task_description: str) -> Dict[str, Any]:
    """Map a task to the best subagent(s) from the 50+ agent swarm.
    Uses keyword matching against agent specs stored in md_sections."""
    task_tokens = set(_tokenize(task_description))
    if not task_tokens:
        return {"agents": [{"name": "ORCHESTRATOR", "relevance_score": 1.0,
                            "role_description": "Fallback orchestrator for unclassified tasks",
                            "suggested_inputs": [task_description]}]}

    agent_specs: List[Dict[str, Any]] = []
    try:
        rows = conn.execute(
            """SELECT id, section_title, content, source_file, section_path
               FROM md_sections
               WHERE content LIKE '%AGENT:%' OR section_title LIKE '%AGENT%'
               OR content LIKE '%agent_name%' OR content LIKE '%Role:%'"""
        ).fetchall()
        for row in rows:
            spec: Dict[str, Any] = {
                "section_id": row["id"],
                "name": "",
                "role": "",
                "triggers": [],
                "inputs": [],
                "outputs": [],
                "content": row["content"],
                "title": row["section_title"],
                "source_file": row["source_file"],
            }
            agent_match = _AGENT_PATTERN.search(row["content"])
            if agent_match:
                spec["name"] = agent_match.group(1)
            elif "AGENT" in row["section_title"].upper():
                spec["name"] = row["section_title"].strip()
            else:
                spec["name"] = row["section_title"].strip()

            role_match = re.search(r"(?:Role|Purpose|Description):\s*(.+?)(?:\n|$)",
                                   row["content"], re.IGNORECASE)
            if role_match:
                spec["role"] = role_match.group(1).strip()
            else:
                spec["role"] = row["content"][:150].strip()

            trigger_match = re.findall(
                r"(?:Trigger|Activat|Invoke)[^:]*:\s*(.+?)(?:\n|$)",
                row["content"], re.IGNORECASE,
            )
            spec["triggers"] = [t.strip() for t in trigger_match]

            input_match = re.findall(
                r"(?:Input|Accepts)[^:]*:\s*(.+?)(?:\n|$)",
                row["content"], re.IGNORECASE,
            )
            spec["inputs"] = [i.strip() for i in input_match]
            output_match = re.findall(
                r"(?:Output|Produces|Returns)[^:]*:\s*(.+?)(?:\n|$)",
                row["content"], re.IGNORECASE,
            )
            spec["outputs"] = [o.strip() for o in output_match]

            agent_specs.append(spec)
    except sqlite3.OperationalError:
        pass

    if not agent_specs:
        return {"agents": [{"name": "ORCHESTRATOR", "relevance_score": 1.0,
                            "role_description": "No agent specs found — fallback orchestrator",
                            "suggested_inputs": [task_description]}]}

    scored: List[Tuple[Dict[str, Any], float]] = []
    for spec in agent_specs:
        spec_tokens = set(_tokenize(
            f"{spec['name']} {spec['role']} {' '.join(spec['triggers'])} {spec['content'][:500]}"
        ))
        if not spec_tokens:
            continue
        overlap = task_tokens & spec_tokens
        score = len(overlap) / max(len(task_tokens), 1)
        scored.append((spec, score))

    scored.sort(key=lambda x: x[1], reverse=True)
    top = scored[:5]

    agents: List[Dict[str, Any]] = []
    for spec, score in top:
        if score <= 0:
            continue
        agents.append({
            "name": spec["name"],
            "relevance_score": round(score, 4),
            "role_description": spec["role"][:200],
            "suggested_inputs": spec["inputs"][:3] if spec["inputs"] else [task_description],
            "section_id": spec["section_id"],
            "source_file": spec["source_file"],
        })

    if not agents:
        agents.append({
            "name": "ORCHESTRATOR",
            "relevance_score": 1.0,
            "role_description": "Fallback orchestrator for unclassified tasks",
            "suggested_inputs": [task_description],
        })

    return {"agents": agents}


# ══════════════════════════════════════════════════════════════════
#  INTEGRITY + SELF-AUDIT
# ══════════════════════════════════════════════════════════════════

def check_integrity(conn: sqlite3.Connection) -> Dict[str, Any]:
    """Run PRAGMA integrity_check and validate FTS sync."""
    results: Dict[str, Any] = {"passed": True, "checks": []}

    # SQLite integrity
    try:
        row = conn.execute("PRAGMA integrity_check").fetchone()
        ok = row[0] == "ok" if row else False
        results["checks"].append({"name": "sqlite_integrity", "passed": ok, "detail": row[0] if row else "no result"})
        if not ok:
            results["passed"] = False
    except sqlite3.Error as e:
        results["checks"].append({"name": "sqlite_integrity", "passed": False, "detail": str(e)})
        results["passed"] = False

    # FTS sync: pages vs pages_fts AND md_sections vs md_sections_fts (batched)
    try:
        fts_sync = conn.execute(
            """SELECT
                   (SELECT COUNT(*) FROM pages) AS page_count,
                   (SELECT COUNT(*) FROM pages_fts) AS page_fts_count,
                   (SELECT COUNT(*) FROM md_sections) AS sec_count,
                   (SELECT COUNT(*) FROM md_sections_fts) AS sec_fts_count"""
        ).fetchone()

        page_synced = fts_sync["page_count"] == fts_sync["page_fts_count"]
        results["checks"].append({
            "name": "pages_fts_sync", "passed": page_synced,
            "detail": f"pages={fts_sync['page_count']}, fts={fts_sync['page_fts_count']}"
                      + ("" if page_synced else " — DESYNC"),
        })
        if not page_synced:
            results["passed"] = False

        sec_synced = fts_sync["sec_count"] == fts_sync["sec_fts_count"]
        results["checks"].append({
            "name": "md_sections_fts_sync", "passed": sec_synced,
            "detail": f"sections={fts_sync['sec_count']}, fts={fts_sync['sec_fts_count']}"
                      + ("" if sec_synced else " — DESYNC"),
        })
        if not synced:
            results["passed"] = False
    except sqlite3.Error as e:
        results["checks"].append({"name": "md_sections_fts_sync", "passed": False, "detail": str(e)})

    return results


def repair_fts_index(conn: sqlite3.Connection, table: str = "pages") -> Dict[str, Any]:
    """Rebuild an FTS5 index from its source table."""
    fts_table = f"{table}_fts"
    try:
        conn.execute(f"INSERT INTO {fts_table}({fts_table}) VALUES('rebuild')")
        conn.commit()
        count = conn.execute(f"SELECT COUNT(*) as c FROM {fts_table}").fetchone()["c"]
        return {"repaired": True, "table": fts_table, "rows": count}
    except sqlite3.Error as e:
        return {"repaired": False, "table": fts_table, "error": str(e)}


def run_self_audit(conn: sqlite3.Connection) -> Dict[str, Any]:
    """Comprehensive data quality audit. Returns quality score 0-100.

    Batches related COUNT(*) queries to reduce round-trips.
    """
    findings: List[Dict[str, Any]] = []
    score = 100.0
    now = datetime.now(timezone.utc).isoformat()

    # Batch quality-check counts in a single query
    quality_counts = conn.execute(
        """SELECT
               (SELECT COUNT(*) FROM pages p WHERE NOT EXISTS
                   (SELECT 1 FROM documents d WHERE d.id = p.document_id)) AS orphan_pages,
               (SELECT COUNT(*) FROM pages
                   WHERE text_content IS NULL OR text_content = '') AS empty_pages,
               (SELECT COUNT(*) FROM risk_events) AS risk_count,
               (SELECT COUNT(*) FROM md_evolution_log) AS md_count,
               (SELECT COUNT(*) FROM md_sections) AS section_count,
               (SELECT COUNT(*) FROM md_cross_refs) AS total_refs,
               (SELECT COUNT(*) FROM md_cross_refs
                   WHERE graph_node_id IS NOT NULL) AS linked_refs,
               (SELECT COUNT(*) FROM documents) AS doc_count,
               (SELECT COUNT(*) FROM pages) AS page_count,
               (SELECT COUNT(*) FROM graph_nodes) AS graph_node_count"""
    ).fetchone()

    # 1. Orphan pages
    orphans = quality_counts["orphan_pages"]
    if orphans > 0:
        score -= min(10, orphans)
        findings.append({"issue": "orphan_pages", "count": orphans, "severity": "high"})

    # 2. Empty page content
    empty_pages = quality_counts["empty_pages"]
    if empty_pages > 0:
        score -= min(5, empty_pages * 0.5)
        findings.append({"issue": "empty_pages", "count": empty_pages, "severity": "medium"})

    # 3. Graph coverage
    expected_graphs = set(GRAPH_FILES.keys()) | {"master_graph"}
    loaded_graphs = {r["graph_source"] for r in conn.execute("SELECT graph_source FROM graph_load_log").fetchall()}
    missing_graphs = expected_graphs - loaded_graphs
    if missing_graphs:
        score -= len(missing_graphs) * 3
        findings.append({"issue": "missing_graphs", "missing": list(missing_graphs), "severity": "high"})

    # 4. Risk event completeness
    if quality_counts["risk_count"] == 0:
        score -= 5
        findings.append({"issue": "no_risk_events", "severity": "medium"})

    # 5. FTS integrity
    integrity = check_integrity(conn)
    if not integrity["passed"]:
        score -= 15
        findings.append({"issue": "integrity_failure", "checks": integrity["checks"], "severity": "critical"})

    # 6. .md evolution coverage
    md_count = quality_counts["md_count"]
    section_count = quality_counts["section_count"]
    if md_count == 0:
        score -= 5
        findings.append({"issue": "no_md_evolved", "severity": "medium"})

    # 7. Cross-ref link rate
    total_refs = quality_counts["total_refs"]
    linked_refs = quality_counts["linked_refs"]
    link_rate = linked_refs / max(total_refs, 1) * 100

    score = max(0, min(100, score))

    # Log audit
    conn.execute(
        "INSERT INTO audit_metrics (metric_name, metric_value, detail, measured_at) VALUES (?, ?, ?, ?)",
        ("quality_score", score, json.dumps(findings, default=str), now),
    )
    conn.commit()

    return {
        "quality_score": round(score, 1),
        "findings": findings,
        "summary": {
            "documents": quality_counts["doc_count"],
            "pages": quality_counts["page_count"],
            "graph_nodes": quality_counts["graph_node_count"],
            "md_files_evolved": md_count,
            "md_sections": section_count,
            "cross_refs": total_refs,
            "cross_ref_link_rate": round(link_rate, 1),
        },
        "measured_at": now,
    }


def record_convergence_cycle(
    conn: sqlite3.Connection,
    delta_new: List[str],
    blockers: List[str],
    next_patch: str,
    quality_score: float,
) -> int:
    """Record a convergence cycle. Returns cycle_id."""
    now = datetime.now(timezone.utc).isoformat()
    cur = conn.execute(
        """INSERT INTO convergence_log (delta_new, blockers, next_patch, quality_score, measured_at)
           VALUES (?, ?, ?, ?, ?)""",
        (json.dumps(delta_new), json.dumps(blockers), next_patch, quality_score, now),
    )
    conn.commit()
    return cur.lastrowid


def get_convergence_status(conn: sqlite3.Connection) -> Dict[str, Any]:
    """Get current convergence status with ΔNEW, BLOCKERS, NEXT_PATCH."""
    # Current state
    audit = run_self_audit(conn)
    quality = audit["quality_score"]

    # Compute deltas
    delta_new: List[str] = []
    blockers: List[str] = []

    # Check what's new since last cycle
    last_cycle = conn.execute(
        "SELECT * FROM convergence_log ORDER BY cycle_id DESC LIMIT 1"
    ).fetchone()

    if last_cycle:
        last_quality = last_cycle["quality_score"]
        if quality > last_quality:
            delta_new.append(f"Quality improved: {last_quality} → {quality}")
    else:
        delta_new.append("First convergence cycle")

    # Detect blockers
    for finding in audit["findings"]:
        if finding["severity"] in ("critical", "high"):
            blockers.append(f"{finding['issue']}: {json.dumps(finding, default=str)[:100]}")

    # Determine next patch
    if "integrity_failure" in [f["issue"] for f in audit["findings"]]:
        next_patch = "repair_fts_index — fix FTS desync"
    elif "missing_graphs" in [f["issue"] for f in audit["findings"]]:
        missing = [f for f in audit["findings"] if f["issue"] == "missing_graphs"]
        next_patch = f"load missing graphs: {missing[0]['missing'][:3]}" if missing else "load graphs"
    elif audit["summary"]["md_files_evolved"] == 0:
        next_patch = "evolve .md files — run evolve_all_md_files on C:\\Users\\andre\\Scans"
    elif quality < 95:
        next_patch = "ingest more PDFs or fix remaining findings"
    else:
        next_patch = "CONVERGED — switch to emergence mode"

    # Emergence signals
    cross_ref_clusters = conn.execute(
        """SELECT ref_value, COUNT(*) as mentions FROM md_cross_refs
           GROUP BY ref_value HAVING mentions >= 3 ORDER BY mentions DESC LIMIT 10"""
    ).fetchall()

    converged = len(blockers) == 0 and quality >= 95

    return {
        "converged": converged,
        "quality_score": quality,
        "delta_new": delta_new,
        "blockers": blockers,
        "next_patch": next_patch,
        "emergence_signals": [dict(r) for r in cross_ref_clusters],
        "cycle_count": conn.execute("SELECT COUNT(*) as c FROM convergence_log").fetchone()["c"],
        "audit_summary": audit["summary"],
    }
