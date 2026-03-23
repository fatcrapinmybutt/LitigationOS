"""
Organization Agent Base — Shared utilities for the 5 file organization agents.
All org agents use INDEX.db (not litigation_context.db) for file tracking.
"""
import sqlite3
import hashlib
import os
import sys
import json
import re
import shutil
from pathlib import Path
from datetime import datetime
from contextlib import contextmanager

INDEX_DB_PATH = Path(r"C:\Users\andre\LitigationOS\_INDEX\INDEX.db")
LITIGOS_ROOT = Path(r"C:\Users\andre\LitigationOS")
STATE_DB_PATH = Path(r"C:\Users\andre\LitigationOS\00_SYSTEM\copilot_state\copilot_state.db")

MEEK_SIGNALS = {
    "A": re.compile(r"(?i)(custody|parenting|FOC|child|MCL\s+722|MCR\s+3\.20[67]|MCR\s+3\.210|best.?interest|factor\s+[a-l])"),
    "B": re.compile(r"(?i)(shady.?oaks|homes.?of.?america|alden.?global|habitability|landlord|tenant|MCL\s+554|rent|mobile.?home|park)"),
    "C": re.compile(r"(?i)(convergence|cross.?lane|multi.?case)"),
    "D": re.compile(r"(?i)(PPO|protection.?order|contempt|MCL\s+600\.2950|MCR\s+3\.70[678]|bond|restrain)"),
    "E": re.compile(r"(?i)(bias|JTC|disqualif|MCR\s+2\.003|canon|judicial.?misconduct|superintend|McNeill)"),
    "F": re.compile(r"(?i)(appell|COA|MSC|MCR\s+7\.|leave.?to.?appeal|standard.?of.?review|de.?novo|abuse.?of.?discretion)"),
}

LANE_PRIORITY = ["E", "D", "F", "C", "A", "B"]

BUCKET_MAP = {
    ".pdf": "PDF", ".docx": "DOCX", ".doc": "DOCX",
    ".txt": "TXT", ".md": "TXT", ".rtf": "TXT",
    ".jpg": "IMG", ".jpeg": "IMG", ".png": "IMG", ".gif": "IMG",
    ".bmp": "IMG", ".tiff": "IMG", ".tif": "IMG", ".webp": "IMG",
    ".mp4": "AV", ".mp3": "AV", ".wav": "AV", ".avi": "AV",
    ".mkv": "AV", ".mov": "AV", ".m4a": "AV", ".ogg": "AV",
    ".csv": "CSV", ".xlsx": "CSV", ".xls": "CSV",
    ".eml": "EML", ".msg": "EML",
    ".py": "SYS", ".ps1": "SYS", ".bat": "SYS", ".sh": "SYS",
    ".js": "SYS", ".jsx": "SYS", ".ts": "SYS",
    ".db": "DB", ".sqlite": "DB", ".sqlite3": "DB",
    ".json": "OTHER", ".xml": "OTHER", ".html": "OTHER",
    ".zip": "OTHER", ".rar": "OTHER", ".7z": "OTHER",
}

DOC_TYPE_KEYWORDS = {
    "motion": re.compile(r"(?i)(motion\s+(to|for|in)|move\s+this\s+court)"),
    "brief": re.compile(r"(?i)(brief\s+in\s+support|memorandum\s+of\s+law|legal\s+brief)"),
    "complaint": re.compile(r"(?i)(complaint|count\s+[ivx]+|cause\s+of\s+action)"),
    "affidavit": re.compile(r"(?i)(affidavit|sworn\s+statement|under\s+oath|notarized)"),
    "order": re.compile(r"(?i)(order\s+(granting|denying|of\s+the\s+court)|it\s+is\s+(hereby\s+)?ordered)"),
    "transcript": re.compile(r"(?i)(transcript|proceedings|the\s+court:|q\.\s|a\.\s)"),
    "exhibit": re.compile(r"(?i)(exhibit\s+[a-z0-9]|evidence\s+item|bates\s+stamp)"),
    "correspondence": re.compile(r"(?i)(dear\s+(mr|ms|mrs|judge)|sincerely|regards|from:|to:|subject:)"),
    "financial": re.compile(r"(?i)(invoice|payment|balance|ledger|account\s+statement|billing)"),
    "statute": re.compile(r"(?i)(MCL\s+\d|MCR\s+\d|USC\s+§|public\s+act|statute)"),
    "form": re.compile(r"(?i)(mc\d{2,4}|foc\d{2,4}|cc\d{2,4}|scao|court\s+form)"),
    "photo": re.compile(r"(?i)(IMG_|DSC_|photo|screenshot|scan)"),
}


def sha256_file(filepath, chunk_size=65536):
    """Compute SHA-256 hash of a file."""
    h = hashlib.sha256()
    try:
        with open(filepath, "rb") as f:
            while True:
                chunk = f.read(chunk_size)
                if not chunk:
                    break
                h.update(chunk)
        return h.hexdigest()
    except (OSError, PermissionError):
        return None


def content_preview(filepath, max_chars=500):
    """Extract first max_chars of text content from a file."""
    ext = Path(filepath).suffix.lower()
    try:
        if ext == ".pdf":
            try:
                import fitz  # PyMuPDF
                doc = fitz.open(str(filepath))
                text = ""
                for page in doc:
                    text += page.get_text()
                    if len(text) >= max_chars:
                        break
                doc.close()
                return text[:max_chars].strip()
            except Exception:
                return ""
        elif ext in (".docx", ".doc"):
            try:
                from docx import Document
                doc = Document(str(filepath))
                text = "\n".join(p.text for p in doc.paragraphs[:20])
                return text[:max_chars].strip()
            except Exception:
                return ""
        elif ext in (".txt", ".md", ".csv", ".json", ".py", ".ps1", ".bat", ".eml", ".rtf"):
            with open(filepath, "r", encoding="utf-8", errors="replace") as f:
                return f.read(max_chars).strip()
        else:
            return ""
    except Exception:
        return ""


def detect_lane(text):
    """Detect case lane from text content using MEEK signals. Priority: E→D→F→C→A→B."""
    if not text:
        return None
    for lane in LANE_PRIORITY:
        if MEEK_SIGNALS[lane].search(text):
            return lane
    return None


def detect_doc_type(text, filename=""):
    """Classify document type from content and filename."""
    combined = f"{filename} {text}"
    for doc_type, pattern in DOC_TYPE_KEYWORDS.items():
        if pattern.search(combined):
            return doc_type
    return "unknown"


def get_bucket(filepath):
    """Determine storage bucket from file extension."""
    ext = Path(filepath).suffix.lower()
    return BUCKET_MAP.get(ext, "OTHER")


def safe_move(src, dst, dry_run=False):
    """Move a file safely: create parent dirs, handle conflicts, log provenance."""
    src, dst = Path(src), Path(dst)
    if not src.exists():
        return False, "source_missing"
    if dst.exists():
        # Add numeric suffix to avoid overwrite
        stem = dst.stem
        suffix = dst.suffix
        parent = dst.parent
        counter = 1
        while dst.exists():
            dst = parent / f"{stem}_{counter}{suffix}"
            counter += 1
    if dry_run:
        return True, f"would_move_to:{dst}"
    try:
        dst.parent.mkdir(parents=True, exist_ok=True)
        shutil.move(str(src), str(dst))
        return True, str(dst)
    except (OSError, PermissionError) as e:
        return False, str(e)


@contextmanager
def index_db():
    """Context manager for INDEX.db with proper PRAGMAs."""
    INDEX_DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(INDEX_DB_PATH))
    conn.execute("PRAGMA journal_mode = WAL")
    conn.execute("PRAGMA busy_timeout = 60000")
    conn.execute("PRAGMA cache_size = -32000")
    conn.execute("PRAGMA synchronous = NORMAL")
    conn.execute("PRAGMA foreign_keys = ON")
    conn.row_factory = sqlite3.Row
    try:
        yield conn
    finally:
        conn.close()


@contextmanager
def state_db():
    """Context manager for copilot_state.db."""
    conn = sqlite3.connect(str(STATE_DB_PATH))
    conn.execute("PRAGMA journal_mode = WAL")
    conn.execute("PRAGMA busy_timeout = 60000")
    conn.row_factory = sqlite3.Row
    try:
        yield conn
    finally:
        conn.close()


def log_audit(conn, action, target=None, details=None, agent_id=None, operation_id=None):
    """Write an entry to the audit log."""
    conn.execute(
        "INSERT INTO audit_log (action, target, details, agent_id, operation_id) VALUES (?,?,?,?,?)",
        (action, target, details, agent_id, operation_id),
    )
    conn.commit()


INDEX_SCHEMA = """
CREATE TABLE IF NOT EXISTS files (
    id TEXT PRIMARY KEY,
    path TEXT UNIQUE NOT NULL,
    filename TEXT NOT NULL,
    extension TEXT NOT NULL,
    bucket TEXT NOT NULL,
    tier TEXT NOT NULL DEFAULT 'hot',
    drive TEXT NOT NULL,
    size_bytes INTEGER,
    sha256 TEXT NOT NULL,
    case_lane TEXT,
    case_number TEXT,
    doc_type TEXT,
    doc_subtype TEXT,
    parties TEXT,
    date_relevant TEXT,
    tags TEXT,
    status TEXT DEFAULT 'indexed',
    original_path TEXT,
    classifier_confidence REAL,
    content_preview TEXT,
    page_count INTEGER,
    word_count INTEGER,
    canonical_id TEXT,
    dupe_cluster TEXT,
    dupe_count INTEGER DEFAULT 0,
    created_at TEXT DEFAULT (datetime('now')),
    indexed_at TEXT DEFAULT (datetime('now')),
    classified_at TEXT
);

CREATE TABLE IF NOT EXISTS file_lanes (
    file_id TEXT, case_lane TEXT, case_number TEXT,
    relevance_score REAL DEFAULT 1.0,
    PRIMARY KEY (file_id, case_lane),
    FOREIGN KEY (file_id) REFERENCES files(id)
);

CREATE TABLE IF NOT EXISTS file_links (
    source_id TEXT, target_id TEXT,
    link_type TEXT,
    confidence REAL DEFAULT 1.0,
    PRIMARY KEY (source_id, target_id, link_type)
);

CREATE TABLE IF NOT EXISTS migrations (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    file_id TEXT,
    from_path TEXT NOT NULL,
    to_path TEXT NOT NULL,
    from_drive TEXT,
    to_drive TEXT,
    action TEXT NOT NULL,
    reason TEXT,
    migrated_at TEXT DEFAULT (datetime('now')),
    agent_id TEXT
);

CREATE TABLE IF NOT EXISTS filing_tracker (
    file_id TEXT PRIMARY KEY,
    filing_type TEXT,
    target_court TEXT,
    case_number TEXT,
    deadline TEXT,
    status TEXT DEFAULT 'draft',
    completeness_pct REAL DEFAULT 0,
    missing_sections TEXT,
    FOREIGN KEY (file_id) REFERENCES files(id)
);

CREATE TABLE IF NOT EXISTS dedup_clusters (
    cluster_id TEXT NOT NULL,
    file_id TEXT NOT NULL,
    is_canonical BOOLEAN DEFAULT 0,
    similarity_score REAL,
    PRIMARY KEY (cluster_id, file_id)
);

CREATE INDEX IF NOT EXISTS idx_files_sha256 ON files(sha256);
CREATE INDEX IF NOT EXISTS idx_files_bucket ON files(bucket);
CREATE INDEX IF NOT EXISTS idx_files_tier ON files(tier);
CREATE INDEX IF NOT EXISTS idx_files_drive ON files(drive);
CREATE INDEX IF NOT EXISTS idx_files_case_lane ON files(case_lane);
CREATE INDEX IF NOT EXISTS idx_files_status ON files(status);
CREATE INDEX IF NOT EXISTS idx_files_extension ON files(extension);
CREATE INDEX IF NOT EXISTS idx_migrations_file ON migrations(file_id);
CREATE INDEX IF NOT EXISTS idx_dedup_canonical ON dedup_clusters(is_canonical) WHERE is_canonical = 1;
"""


def init_index_db():
    """Initialize INDEX.db with full schema."""
    with index_db() as conn:
        conn.executescript(INDEX_SCHEMA)
        conn.commit()
        tables = conn.execute("SELECT count(*) FROM sqlite_master WHERE type='table'").fetchone()[0]
        print(f"INDEX.db initialized: {tables} tables at {INDEX_DB_PATH}")
        return tables
