"""
Database Router — Routes analyzed content to the correct database tables.
=========================================================================

This is the CRITICAL missing link. Takes analysis results and INSERTs
them into the appropriate tables in the litigation database.

Routes:
  EvidenceQuote    → evidence_quotes table (+ evidence_fts)
  TimelineEvent    → timeline_events table (+ timeline_fts)
  AuthorityRef     → authority_chains_v2 table
  ImpeachmentItem  → impeachment_matrix table
  Document         → documents + pages tables
  Entities         → entities table (creates if missing)

Database creation: If the target DB doesn't exist, creates it with
the full litigation schema. If tables are missing, adds them.

100% case-agnostic. Table structures are generic litigation tables.
"""

import json
import logging
import os
import re
import sqlite3
from datetime import datetime
from pathlib import Path
from time import perf_counter_ns
from typing import Optional

logger = logging.getLogger("intake.router")

# Try shared module for DB connection
try:
    import sys
    _SYSTEM_DIR = str(Path(__file__).resolve().parent.parent.parent)
    if _SYSTEM_DIR not in sys.path:
        sys.path.insert(0, _SYSTEM_DIR)
    from shared import get_db, sanitize_fts5, STANDARD_PRAGMAS
    _HAS_SHARED = True
except ImportError:
    _HAS_SHARED = False

    def sanitize_fts5(q):
        return re.sub(r'[^\w\s*"]', ' ', q).strip()

    STANDARD_PRAGMAS = {
        "busy_timeout": 60000,
        "journal_mode": "WAL",
        "cache_size": -32000,
        "temp_store": 2,
        "synchronous": "NORMAL",
    }


# ─── Schema Definitions (case-agnostic) ──────────────────────────

CORE_SCHEMA = """
-- Documents table: tracks every ingested file
CREATE TABLE IF NOT EXISTS documents (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    file_path TEXT UNIQUE,
    file_name TEXT,
    file_ext TEXT,
    file_size INTEGER,
    sha256 TEXT,
    page_count INTEGER DEFAULT 0,
    char_count INTEGER DEFAULT 0,
    extraction_method TEXT,
    doc_type TEXT,
    lanes TEXT,  -- JSON array of lane IDs
    urgency TEXT,
    readiness_score REAL DEFAULT 0.0,  -- EGCP-style 0-100
    ingested_at TEXT DEFAULT (datetime('now')),
    metadata TEXT  -- JSON
);

-- Pages table: per-page text
CREATE TABLE IF NOT EXISTS pages (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    document_id INTEGER REFERENCES documents(id) ON DELETE CASCADE,
    page_number INTEGER,
    text_content TEXT,
    char_count INTEGER DEFAULT 0
);

-- Evidence quotes: significant extracted quotes
CREATE TABLE IF NOT EXISTS evidence_quotes (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    quote_text TEXT,
    context TEXT,
    category TEXT,
    relevance REAL,
    source_file TEXT,
    page_number INTEGER,
    lane TEXT,
    ingested_at TEXT DEFAULT (datetime('now'))
);

-- Timeline events: dated events
CREATE TABLE IF NOT EXISTS timeline_events (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    event_date TEXT,
    event_text TEXT,
    actors TEXT,
    source_file TEXT,
    category TEXT,
    lane TEXT,
    ingested_at TEXT DEFAULT (datetime('now'))
);

-- Authority chains: citation relationships
CREATE TABLE IF NOT EXISTS authority_chains_v2 (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    primary_citation TEXT,
    supporting_citation TEXT,
    relationship TEXT,
    source_document TEXT,
    source_type TEXT,
    lane TEXT,
    paragraph_context TEXT,
    ingested_at TEXT DEFAULT (datetime('now'))
);

-- Impeachment matrix: cross-examination ammunition
CREATE TABLE IF NOT EXISTS impeachment_matrix (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    category TEXT,
    evidence_summary TEXT,
    source_file TEXT,
    quote_text TEXT,
    impeachment_value INTEGER,
    cross_exam_question TEXT,
    filing_relevance TEXT,
    event_date TEXT,
    lane TEXT,
    ingested_at TEXT DEFAULT (datetime('now'))
);

-- Entities: people, organizations, case numbers
CREATE TABLE IF NOT EXISTS entities (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT,
    entity_type TEXT,
    source_file TEXT,
    lane TEXT,
    first_seen TEXT DEFAULT (datetime('now')),
    UNIQUE(name, entity_type)
);

-- Intake log: tracks every intake pipeline run
CREATE TABLE IF NOT EXISTS intake_log (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    file_path TEXT,
    file_name TEXT,
    sha256 TEXT,
    doc_type TEXT,
    lanes TEXT,
    quotes_inserted INTEGER DEFAULT 0,
    events_inserted INTEGER DEFAULT 0,
    authorities_inserted INTEGER DEFAULT 0,
    impeachment_inserted INTEGER DEFAULT 0,
    entities_inserted INTEGER DEFAULT 0,
    status TEXT DEFAULT 'completed',
    error TEXT,
    processed_at TEXT DEFAULT (datetime('now'))
);

-- Performance indexes (cover all common query patterns)
CREATE INDEX IF NOT EXISTS idx_documents_file_path ON documents(file_path);
CREATE INDEX IF NOT EXISTS idx_documents_sha256 ON documents(sha256);
CREATE INDEX IF NOT EXISTS idx_documents_doc_type ON documents(doc_type);
CREATE INDEX IF NOT EXISTS idx_documents_readiness ON documents(readiness_score);
CREATE INDEX IF NOT EXISTS idx_pages_document_id ON pages(document_id);
CREATE INDEX IF NOT EXISTS idx_evidence_quotes_lane ON evidence_quotes(lane);
CREATE INDEX IF NOT EXISTS idx_evidence_quotes_category ON evidence_quotes(category);
CREATE INDEX IF NOT EXISTS idx_evidence_quotes_source ON evidence_quotes(source_file);
CREATE INDEX IF NOT EXISTS idx_timeline_events_date ON timeline_events(event_date);
CREATE INDEX IF NOT EXISTS idx_timeline_events_lane ON timeline_events(lane);
CREATE INDEX IF NOT EXISTS idx_authority_chains_primary ON authority_chains_v2(primary_citation);
CREATE INDEX IF NOT EXISTS idx_authority_chains_lane ON authority_chains_v2(lane);
CREATE INDEX IF NOT EXISTS idx_impeachment_value ON impeachment_matrix(impeachment_value);
CREATE INDEX IF NOT EXISTS idx_impeachment_lane ON impeachment_matrix(lane);
CREATE INDEX IF NOT EXISTS idx_entities_name ON entities(name);
CREATE INDEX IF NOT EXISTS idx_entities_type ON entities(entity_type);
CREATE INDEX IF NOT EXISTS idx_intake_log_sha256 ON intake_log(sha256);
CREATE INDEX IF NOT EXISTS idx_intake_log_status ON intake_log(status);

-- Partial indexes (bleeding-edge: index only high-value subsets for faster filtered queries)
CREATE INDEX IF NOT EXISTS idx_evidence_high_relevance ON evidence_quotes(lane, category)
    WHERE relevance >= 7;
CREATE INDEX IF NOT EXISTS idx_impeachment_high_value ON impeachment_matrix(lane, category)
    WHERE impeachment_value >= 7;
CREATE INDEX IF NOT EXISTS idx_documents_ready ON documents(doc_type, readiness_score)
    WHERE readiness_score >= 65.0;
CREATE INDEX IF NOT EXISTS idx_intake_pending ON intake_log(status)
    WHERE status IN ('pending', 'processing');

-- Covering indexes (avoid table lookups for frequent query patterns)
CREATE INDEX IF NOT EXISTS idx_evidence_cover_lane_cat ON evidence_quotes(lane, category, relevance);
CREATE INDEX IF NOT EXISTS idx_timeline_cover_date_lane ON timeline_events(event_date, lane, category);

-- Case verdicts / outcomes
CREATE TABLE IF NOT EXISTS verdicts (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    case_id TEXT,
    verdict_date TEXT,
    judge TEXT,
    outcome TEXT NOT NULL,
    lane TEXT,
    summary TEXT,
    appeal_deadline TEXT,
    created_at TEXT DEFAULT (datetime('now'))
);
CREATE INDEX IF NOT EXISTS idx_verdicts_case ON verdicts(case_id);
CREATE INDEX IF NOT EXISTS idx_verdicts_lane ON verdicts(lane);

-- Document version tracking
CREATE TABLE IF NOT EXISTS document_versions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    document_id INTEGER NOT NULL REFERENCES documents(id) ON DELETE CASCADE,
    version INTEGER NOT NULL DEFAULT 1,
    file_path TEXT NOT NULL,
    sha256 TEXT NOT NULL,
    change_summary TEXT,
    created_at TEXT DEFAULT (datetime('now')),
    UNIQUE(document_id, version)
);
CREATE INDEX IF NOT EXISTS idx_doc_versions_doc ON document_versions(document_id);

-- Correspondence log (letters, emails, filings between parties)
CREATE TABLE IF NOT EXISTS correspondence_log (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    correspondence_date TEXT,
    from_party TEXT,
    to_party TEXT,
    method TEXT,
    subject TEXT,
    lane TEXT,
    document_id INTEGER REFERENCES documents(id),
    notes TEXT,
    created_at TEXT DEFAULT (datetime('now'))
);
CREATE INDEX IF NOT EXISTS idx_correspondence_date ON correspondence_log(correspondence_date);
CREATE INDEX IF NOT EXISTS idx_correspondence_lane ON correspondence_log(lane);
CREATE INDEX IF NOT EXISTS idx_correspondence_parties ON correspondence_log(from_party, to_party);
"""

FTS_SCHEMA = """
-- FTS5 indexes for fast full-text search
CREATE VIRTUAL TABLE IF NOT EXISTS evidence_fts USING fts5(
    quote_text, context, category, lane,
    content='evidence_quotes',
    content_rowid='id',
    tokenize='porter unicode61'
);

CREATE VIRTUAL TABLE IF NOT EXISTS timeline_fts USING fts5(
    event_text, actors, category, lane,
    content='timeline_events',
    content_rowid='id',
    tokenize='porter unicode61'
);
"""

FTS_TRIGGERS = """
-- Auto-sync FTS on INSERT
CREATE TRIGGER IF NOT EXISTS evidence_fts_insert AFTER INSERT ON evidence_quotes BEGIN
    INSERT INTO evidence_fts(rowid, quote_text, context, category, lane)
    VALUES (new.id, new.quote_text, new.context, new.category, new.lane);
END;

CREATE TRIGGER IF NOT EXISTS timeline_fts_insert AFTER INSERT ON timeline_events BEGIN
    INSERT INTO timeline_fts(rowid, event_text, actors, category, lane)
    VALUES (new.id, new.event_text, new.actors, new.category, new.lane);
END;
"""


class DatabaseRouter:
    """Routes analysis results to database tables. Creates schema if needed.

    Case-agnostic: works with any database path, creates tables on demand.
    """

    def __init__(self, db_path: str | Path = None):
        self.db_path = str(db_path) if db_path else None
        self._conn: Optional[sqlite3.Connection] = None

    def connect(self, db_path: str | Path = None) -> sqlite3.Connection:
        """Connect to database, creating schema if needed."""
        path = str(db_path or self.db_path)
        if not path:
            raise ValueError("No database path specified")

        self.db_path = path

        # Create parent directory if needed
        Path(path).parent.mkdir(parents=True, exist_ok=True)

        conn = sqlite3.connect(path, timeout=60)
        conn.row_factory = sqlite3.Row

        # Apply standard PRAGMAs
        for pragma, value in STANDARD_PRAGMAS.items():
            try:
                conn.execute(f"PRAGMA {pragma} = {value}")
            except sqlite3.OperationalError:
                pass

        # Ensure schema exists
        self._ensure_schema(conn)

        self._conn = conn
        return conn

    def _ensure_schema(self, conn: sqlite3.Connection):
        """Create tables and indexes if they don't exist."""
        conn.executescript(CORE_SCHEMA)

        # FTS tables need special handling — check if they exist first
        existing = {
            row[0] for row in
            conn.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall()
        }

        if "evidence_fts" not in existing:
            try:
                conn.executescript(FTS_SCHEMA)
            except sqlite3.OperationalError:
                pass  # FTS5 may not be available

        # Triggers
        existing_triggers = {
            row[0] for row in
            conn.execute("SELECT name FROM sqlite_master WHERE type='trigger'").fetchall()
        }
        if "evidence_fts_insert" not in existing_triggers:
            try:
                conn.executescript(FTS_TRIGGERS)
            except sqlite3.OperationalError:
                pass

        # Run ANALYZE for query planner optimization
        try:
            conn.execute("ANALYZE")
        except sqlite3.OperationalError:
            pass

        # PRAGMA optimize — bleeding-edge: let SQLite auto-analyze tables
        # that haven't been analyzed since last schema/data change
        try:
            conn.execute("PRAGMA optimize")
        except sqlite3.OperationalError:
            pass

    def get_conn(self) -> sqlite3.Connection:
        """Get current connection, connecting if needed."""
        if self._conn is None:
            return self.connect()
        return self._conn

    # ─── Routing Methods ──────────────────────────────────────────

    def store_document(self, extraction_result, classification_result,
                       analysis_result=None) -> int:
        """Store document metadata. Returns document_id."""
        t0 = perf_counter_ns()
        conn = self.get_conn()

        # Check if already ingested (by path or hash)
        existing = conn.execute(
            "SELECT id FROM documents WHERE file_path = ? OR sha256 = ?",
            (extraction_result.file_path, extraction_result.sha256)
        ).fetchone()

        if existing:
            logger.debug("Document already indexed (id=%d) in %.2fms",
                         existing["id"], (perf_counter_ns() - t0) / 1_000_000)
            return existing["id"]

        readiness = 0.0
        if analysis_result and hasattr(analysis_result, "readiness_score"):
            readiness = analysis_result.readiness_score

        cur = conn.execute(
            """INSERT INTO documents
               (file_path, file_name, file_ext, file_size, sha256,
                page_count, char_count, extraction_method,
                doc_type, lanes, urgency, readiness_score, metadata)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (
                extraction_result.file_path,
                extraction_result.file_name,
                extraction_result.file_ext,
                extraction_result.file_size,
                extraction_result.sha256,
                extraction_result.page_count,
                extraction_result.char_count,
                extraction_result.extraction_method,
                classification_result.doc_type,
                json.dumps(classification_result.lanes),
                classification_result.urgency,
                readiness,
                json.dumps(extraction_result.metadata),
            ),
        )
        conn.commit()
        elapsed_ms = (perf_counter_ns() - t0) / 1_000_000
        logger.info("Stored document id=%d (%s) in %.2fms",
                     cur.lastrowid, extraction_result.file_name, elapsed_ms)
        return cur.lastrowid

    def store_pages(self, document_id: int, pages: list):
        """Store page text for a document."""
        conn = self.get_conn()
        for page in pages:
            text = page.text if hasattr(page, "text") else str(page)
            num = page.page_number if hasattr(page, "page_number") else 0
            conn.execute(
                "INSERT INTO pages (document_id, page_number, text_content, char_count) "
                "VALUES (?, ?, ?, ?)",
                (document_id, num, text, len(text)),
            )
        conn.commit()

    def store_evidence_quotes(self, quotes: list) -> int:
        """Store evidence quotes. Returns count inserted."""
        conn = self.get_conn()
        count = 0
        for q in quotes:
            try:
                conn.execute(
                    """INSERT INTO evidence_quotes
                       (quote_text, context, category, relevance,
                        source_file, page_number, lane)
                       VALUES (?, ?, ?, ?, ?, ?, ?)""",
                    (q.text, q.context, q.category, q.relevance,
                     q.source_file, q.page_number, q.lane),
                )
                count += 1
            except sqlite3.IntegrityError as e:
                    logger.debug(f"Duplicate skipped in evidence_quotes: {e}")
        conn.commit()
        return count

    def store_timeline_events(self, events: list) -> int:
        """Store timeline events. Returns count inserted."""
        conn = self.get_conn()
        count = 0
        for e in events:
            try:
                conn.execute(
                    """INSERT INTO timeline_events
                       (event_date, event_text, actors, source_file, category, lane)
                       VALUES (?, ?, ?, ?, ?, ?)""",
                    (e.date_str, e.event_text, e.actors,
                     e.source_file, e.category, e.lane),
                )
                count += 1
            except sqlite3.IntegrityError as e_err:
                    logger.debug(f"Duplicate skipped in timeline_events: {e_err}")
        conn.commit()
        return count

    def store_authority_refs(self, refs: list, source_file: str = "") -> int:
        """Store authority references as chains. Returns count inserted."""
        conn = self.get_conn()
        count = 0
        for ref in refs:
            try:
                conn.execute(
                    """INSERT INTO authority_chains_v2
                       (primary_citation, relationship, source_document,
                        source_type, paragraph_context)
                       VALUES (?, ?, ?, ?, ?)""",
                    (ref.citation, "cited_in", source_file,
                     ref.citation_type, ref.context),
                )
                count += 1
            except sqlite3.IntegrityError as e:
                    logger.debug(f"Duplicate skipped in authority_chains_v2: {e}")
        conn.commit()
        return count

    def store_impeachment(self, items: list) -> int:
        """Store impeachment material. Returns count inserted."""
        conn = self.get_conn()
        count = 0
        for item in items:
            try:
                conn.execute(
                    """INSERT INTO impeachment_matrix
                       (category, evidence_summary, source_file,
                        quote_text, impeachment_value, cross_exam_question)
                       VALUES (?, ?, ?, ?, ?, ?)""",
                    (item.category, item.text, item.source_file,
                     item.text[:500], item.impeachment_value,
                     item.cross_exam_question),
                )
                count += 1
            except sqlite3.IntegrityError as e:
                    logger.debug(f"Duplicate skipped in impeachment_matrix: {e}")
        conn.commit()
        return count

    def store_entities(self, entities: dict, source_file: str = "", lane: str = "") -> int:
        """Store extracted entities. Returns count inserted."""
        conn = self.get_conn()
        count = 0
        for name, etype in entities.items():
            try:
                conn.execute(
                    "INSERT OR IGNORE INTO entities (name, entity_type, source_file, lane) "
                    "VALUES (?, ?, ?, ?)",
                    (name, etype, source_file, lane),
                )
                count += 1
            except sqlite3.IntegrityError as e:
                    logger.debug(f"Duplicate skipped in entities: {e}")
        conn.commit()
        return count

    def log_intake(self, result: dict):
        """Log an intake pipeline run."""
        conn = self.get_conn()
        conn.execute(
            """INSERT INTO intake_log
               (file_path, file_name, sha256, doc_type, lanes,
                quotes_inserted, events_inserted, authorities_inserted,
                impeachment_inserted, entities_inserted, status, error)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (
                result.get("file_path", ""),
                result.get("file_name", ""),
                result.get("sha256", ""),
                result.get("doc_type", ""),
                json.dumps(result.get("lanes", [])),
                result.get("quotes_inserted", 0),
                result.get("events_inserted", 0),
                result.get("authorities_inserted", 0),
                result.get("impeachment_inserted", 0),
                result.get("entities_inserted", 0),
                result.get("status", "completed"),
                result.get("error"),
            ),
        )
        conn.commit()

    def store_verdict(self, case_id: str, verdict_date: str, judge: str,
                      outcome: str, lane: str = "", summary: str = "",
                      appeal_deadline: str = "") -> int:
        """Store a case verdict/outcome."""
        conn = self.get_conn()
        cur = conn.execute(
            """INSERT INTO verdicts (case_id, verdict_date, judge, outcome, lane, summary, appeal_deadline)
               VALUES (?, ?, ?, ?, ?, ?, ?)""",
            (case_id, verdict_date, judge, outcome, lane, summary, appeal_deadline)
        )
        conn.commit()
        return cur.lastrowid

    def store_document_version(self, document_id: int, version: int,
                               file_path: str, sha256: str,
                               change_summary: str = "") -> int:
        """Store a new version of a document."""
        conn = self.get_conn()
        try:
            cur = conn.execute(
                """INSERT INTO document_versions (document_id, version, file_path, sha256, change_summary)
                   VALUES (?, ?, ?, ?, ?)""",
                (document_id, version, file_path, sha256, change_summary)
            )
            conn.commit()
            return cur.lastrowid
        except sqlite3.IntegrityError:
            logger.warning("Version %d already exists for document %d", version, document_id)
            return -1

    def store_correspondence(self, correspondence_date: str, from_party: str,
                             to_party: str, method: str, subject: str,
                             lane: str = "", document_id: int | None = None,
                             notes: str = "") -> int:
        """Store a correspondence log entry."""
        conn = self.get_conn()
        cur = conn.execute(
            """INSERT INTO correspondence_log
               (correspondence_date, from_party, to_party, method, subject, lane, document_id, notes)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
            (correspondence_date, from_party, to_party, method, subject, lane, document_id, notes)
        )
        conn.commit()
        return cur.lastrowid

    def close(self):
        """Close database connection."""
        if self._conn:
            self._conn.close()
            self._conn = None
