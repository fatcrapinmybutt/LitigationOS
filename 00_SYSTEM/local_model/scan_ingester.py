#!/usr/bin/env python3
"""
MBP LitigationOS — Bulk Scan Directory Ingester
================================================
Processes C:\\Users\\andre\\scans (175,000+ files, 57GB) into litigation_context.db.
Incremental: skips already-ingested files. Read-only access to source files.
"""

import csv
import hashlib
import json
import os
import re
import sqlite3
from collections import Counter, defaultdict
from datetime import datetime
from pathlib import Path

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

DEFAULT_DB = r"C:\Users\andre\LitigationOS\litigation_context.db"
DEFAULT_SCAN_ROOT = r"C:\Users\andre\scans"

SKIP_EXTENSIONS = frozenset({
    ".zip", ".gz", ".7z", ".rar", ".tar", ".bz2", ".xz",
    ".exe", ".dll", ".class", ".pyc", ".pyo", ".so", ".o", ".obj",
    ".bin", ".dat", ".iso", ".img", ".msi", ".cab",
    ".jpg", ".jpeg", ".png", ".gif", ".bmp", ".tiff", ".tif",
    ".ico", ".svg", ".webp", ".mp3", ".mp4", ".avi", ".mov",
    ".wav", ".flac", ".mkv", ".wmv", ".wma",
})

CODE_EXTENSIONS = frozenset({
    ".py", ".js", ".ts", ".java", ".rs", ".go", ".c", ".cpp",
    ".h", ".hpp", ".cs", ".rb", ".php", ".swift", ".kt",
})

INGESTIBLE_EXTENSIONS = frozenset({
    ".txt", ".csv", ".json", ".md", ".pdf", ".html", ".htm",
    ".docx", ".msg", ".eml", ".log", ".xml", ".yaml", ".yml",
})

LEGAL_KEYWORDS = [
    "plaintiff", "defendant", "court", "motion", "order", "judge",
    "custody", "parenting", "mcl", "mcr", "mre", "statute",
    "hearing", "petition", "respondent", "appellant", "appellee",
    "deposition", "discovery", "exhibit", "testimony", "sworn",
    "affidavit", "stipulation", "brief", "opinion", "ruling",
    "objection", "sustained", "overruled", "guardian", "foc",
    "friend of the court", "best interest", "ppo", "protection order",
    "muskegon", "circuit court", "pigors", "watson", "mcneill",
]

LEGAL_CITE_RE = re.compile(
    r"(?:MCL|MCR|MRE)\s+\d+[\.\d]*"
    r"|(?:\d+\s+Mich(?:\s+App)?\s+\d+)"
    r"|(?:\d+\s+NW2d\s+\d+)"
    r"|(?:Case\s+No\.?\s*\d[\d\-]+)",
    re.IGNORECASE,
)

DATE_RE = re.compile(
    r"\b(?:\d{1,2}[/-]\d{1,2}[/-]\d{2,4})"
    r"|(?:\b(?:January|February|March|April|May|June|July|August|"
    r"September|October|November|December)\s+\d{1,2},?\s+\d{4})",
    re.IGNORECASE,
)

MAX_READ_BYTES = 100 * 1024  # 100 KB for classification
HASH_HEAD_BYTES = 4096       # 4 KB for fast dedup hash

# ---------------------------------------------------------------------------
# Schema
# ---------------------------------------------------------------------------

SCHEMA_SQL = """
CREATE TABLE IF NOT EXISTS scan_inventory (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    file_path TEXT UNIQUE NOT NULL,
    file_name TEXT NOT NULL,
    file_ext TEXT,
    file_size INTEGER,
    parent_dir TEXT,
    ingested INTEGER DEFAULT 0,
    ingested_at TEXT,
    content_hash TEXT,
    doc_type TEXT,
    error TEXT,
    created_at TEXT DEFAULT (datetime('now'))
);
CREATE INDEX IF NOT EXISTS idx_scan_path ON scan_inventory(file_path);
CREATE INDEX IF NOT EXISTS idx_scan_ingested ON scan_inventory(ingested);
CREATE INDEX IF NOT EXISTS idx_scan_ext ON scan_inventory(file_ext);
CREATE INDEX IF NOT EXISTS idx_scan_doc_type ON scan_inventory(doc_type);
"""

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _safe_read(file_path, max_bytes=MAX_READ_BYTES):
    """Read file content with encoding fallback. Returns (text, encoding) or (None, None)."""
    if _is_binary(file_path):
        return None, None
    for enc in ("utf-8", "utf-8-sig", "latin-1"):
        try:
            with open(file_path, "r", encoding=enc, errors="replace") as fh:
                text = fh.read(max_bytes)
            return text, enc
        except (OSError, PermissionError, UnicodeDecodeError):
            continue
    return None, None


def _is_binary(file_path):
    """Check first 512 bytes for null bytes."""
    try:
        with open(file_path, "rb") as fh:
            chunk = fh.read(512)
        return b"\x00" in chunk
    except (OSError, PermissionError):
        return True


def _fast_hash(file_path, file_size):
    """Hash based on first 4KB + file_size for fast dedup."""
    h = hashlib.md5(usedforsecurity=False)
    h.update(str(file_size).encode())
    try:
        with open(file_path, "rb") as fh:
            h.update(fh.read(HASH_HEAD_BYTES))
    except (OSError, PermissionError):
        return None
    return h.hexdigest()


# ---------------------------------------------------------------------------
# ScanIngester
# ---------------------------------------------------------------------------


class ScanIngester:
    """Bulk ingester for the scans directory into litigation_context.db."""

    def __init__(self, db_path=DEFAULT_DB, scan_root=DEFAULT_SCAN_ROOT):
        self.db_path = db_path
        self.scan_root = Path(scan_root)
        self.conn = sqlite3.connect(db_path, timeout=30)
        self.conn.execute("PRAGMA journal_mode=WAL")
        self.conn.execute("PRAGMA busy_timeout=10000")
        self.conn.row_factory = sqlite3.Row
        self._init_schema()

    def _init_schema(self):
        cur = self.conn.cursor()
        cur.executescript(SCHEMA_SQL)
        self.conn.commit()

    def close(self):
        if self.conn:
            self.conn.close()
            self.conn = None

    # ------------------------------------------------------------------
    # catalog_directory
    # ------------------------------------------------------------------

    def catalog_directory(self, root_path=None):
        """Walk the directory tree and insert every file into scan_inventory."""
        root = Path(root_path) if root_path else self.scan_root
        if not root.exists():
            return {"error": f"Path does not exist: {root}"}

        # Pre-load existing paths for fast lookup
        cur = self.conn.cursor()
        cur.execute("SELECT file_path FROM scan_inventory")
        existing = {row[0] for row in cur.fetchall()}

        total = 0
        new = 0
        by_type = Counter()
        by_ext = Counter()
        batch = []
        batch_size = 500

        for dirpath, _dirnames, filenames in os.walk(root):
            for fname in filenames:
                fpath = os.path.join(dirpath, fname)
                total += 1

                ext = os.path.splitext(fname)[1].lower()
                by_ext[ext] += 1

                if fpath in existing:
                    doc_type = self._classify(fpath, ext)
                    by_type[doc_type] += 1
                    continue

                if ext in SKIP_EXTENSIONS:
                    continue

                try:
                    fsize = os.path.getsize(fpath)
                except OSError:
                    fsize = 0

                doc_type = self._classify(fpath, ext)
                by_type[doc_type] += 1
                parent = os.path.basename(dirpath)

                batch.append((fpath, fname, ext, fsize, parent, doc_type))
                new += 1

                if len(batch) >= batch_size:
                    self._flush_catalog(batch)
                    batch.clear()

        if batch:
            self._flush_catalog(batch)

        return {
            "total_files": total,
            "new_files": new,
            "by_type": dict(by_type),
            "by_ext": dict(by_ext),
        }

    def _flush_catalog(self, batch):
        try:
            self.conn.executemany(
                "INSERT OR IGNORE INTO scan_inventory "
                "(file_path, file_name, file_ext, file_size, parent_dir, doc_type) "
                "VALUES (?, ?, ?, ?, ?, ?)",
                batch,
            )
            self.conn.commit()
        except sqlite3.Error as exc:
            print(f"[WARN] catalog flush error: {exc}")

    def _classify(self, fpath, ext):
        """Classify doc_type from path and extension."""
        fpath_lower = fpath.lower()
        fname_lower = os.path.basename(fpath).lower()
        in_discovery = "discovery" in fpath_lower or "\\discovery\\" in fpath_lower

        if ext in CODE_EXTENSIONS:
            return "code"
        if ext in (".msg", ".eml"):
            return "email"
        if ext in (".csv", ".json"):
            return "data"
        if ext == ".pdf":
            return "court_doc" if in_discovery else "evidence"
        if ext == ".txt":
            if "chatgpt" in fname_lower or "chat gpt" in fname_lower:
                return "chatgpt"
            return "court_doc" if in_discovery else "evidence"
        if ext == ".md":
            return "evidence" if in_discovery else "documentation"
        if ext in (".html", ".htm"):
            return "evidence" if in_discovery else "documentation"
        if ext == ".docx":
            return "court_doc" if in_discovery else "evidence"
        return "unknown"

    # ------------------------------------------------------------------
    # ingest_batch
    # ------------------------------------------------------------------

    def ingest_batch(self, batch_size=100, file_types=None, doc_types=None):
        """Ingest next batch of un-ingested files."""
        query = (
            "SELECT id, file_path, file_name, file_ext, doc_type "
            "FROM scan_inventory WHERE ingested = 0 AND error IS NULL"
        )
        params = []

        if file_types:
            placeholders = ",".join("?" for _ in file_types)
            query += f" AND file_ext IN ({placeholders})"
            params.extend(file_types)

        if doc_types:
            placeholders = ",".join("?" for _ in doc_types)
            query += f" AND doc_type IN ({placeholders})"
            params.extend(doc_types)

        # Skip code and archive types
        query += " AND doc_type NOT IN ('code')"
        query += f" LIMIT {int(batch_size)}"

        cur = self.conn.cursor()
        cur.execute(query, params)
        rows = cur.fetchall()

        processed = 0
        succeeded = 0
        failed = 0
        skipped = 0
        errors = []

        for row in rows:
            rid, fpath, fname, ext, doc_type = (
                row["id"], row["file_path"], row["file_name"],
                row["file_ext"], row["doc_type"],
            )
            processed += 1

            try:
                if not os.path.exists(fpath):
                    self.mark_processed(fpath, success=False, error="File not found")
                    failed += 1
                    errors.append({"file": fname, "error": "File not found"})
                    continue

                if _is_binary(fpath):
                    self.mark_processed(fpath, success=False, error="Binary file")
                    skipped += 1
                    continue

                ok = False
                if ext == ".txt":
                    ok = self._ingest_text(fpath, fname, doc_type)
                elif ext == ".csv":
                    ok = self._ingest_csv(fpath, fname)
                elif ext == ".json":
                    ok = self._ingest_json(fpath, fname)
                elif ext == ".md":
                    ok = self._ingest_markdown(fpath, fname)
                elif ext == ".pdf":
                    ok = self._ingest_pdf_ref(fpath, fname)
                elif ext in (".html", ".htm"):
                    ok = self._ingest_text(fpath, fname, doc_type)
                elif ext in (".msg", ".eml"):
                    ok = self._ingest_email(fpath, fname)
                else:
                    ok = self._ingest_text(fpath, fname, doc_type)

                if ok:
                    self.mark_processed(fpath, success=True)
                    succeeded += 1
                else:
                    skipped += 1
                    self.mark_processed(fpath, success=True)

            except Exception as exc:
                err_msg = f"{type(exc).__name__}: {exc}"
                self.mark_processed(fpath, success=False, error=err_msg)
                failed += 1
                errors.append({"file": fname, "error": err_msg})

        return {
            "processed": processed,
            "succeeded": succeeded,
            "failed": failed,
            "skipped": skipped,
            "errors": errors,
        }

    def _ingest_text(self, fpath, fname, doc_type):
        """Read text file, extract legal content if relevant."""
        text, _ = _safe_read(fpath)
        if text is None:
            return False

        result = self.extract_legal_content(fpath, text=text)
        if result["legal_score"] < 0.05 and doc_type not in ("court_doc", "evidence", "chatgpt"):
            return True  # cataloged but low relevance

        # Store in md_sections for searchability
        try:
            self.conn.execute(
                "INSERT OR IGNORE INTO md_sections "
                "(section_title, content, source_file) VALUES (?, ?, ?)",
                (fname, text[:50000], fpath),
            )
            self.conn.commit()
        except sqlite3.Error:
            pass

        # Extract quotes if high legal relevance
        if result["legal_score"] >= 0.2 and result["citations_found"]:
            self._store_evidence_quotes(fpath, fname, text, result)

        return True

    def _ingest_csv(self, fpath, fname):
        """Read CSV rows and store in master_csv_data."""
        text, enc = _safe_read(fpath)
        if text is None:
            return False

        try:
            reader = csv.reader(text.splitlines())
            rows_stored = 0
            for i, row in enumerate(reader):
                if i > 5000:
                    break
                row_text = " | ".join(str(c) for c in row)
                try:
                    self.conn.execute(
                        "INSERT OR IGNORE INTO master_csv_data "
                        "(source_file, row_num, content) VALUES (?, ?, ?)",
                        (fpath, i, row_text),
                    )
                    rows_stored += 1
                except sqlite3.Error:
                    # Table may not have these exact columns — try alternate
                    break
            if rows_stored:
                self.conn.commit()
            return True
        except (csv.Error, UnicodeDecodeError):
            return False

    def _ingest_json(self, fpath, fname):
        """Parse JSON and store relevant fields."""
        text, _ = _safe_read(fpath)
        if text is None:
            return False

        try:
            data = json.loads(text)
        except (json.JSONDecodeError, ValueError):
            return False

        # Flatten to text for storage
        flat = json.dumps(data, indent=2, default=str)[:50000]
        try:
            self.conn.execute(
                "INSERT OR IGNORE INTO md_sections "
                "(section_title, content, source_file) VALUES (?, ?, ?)",
                (fname, flat, fpath),
            )
            self.conn.commit()
        except sqlite3.Error:
            pass
        return True

    def _ingest_markdown(self, fpath, fname):
        """Extract sections from markdown and store in md_sections."""
        text, _ = _safe_read(fpath)
        if text is None:
            return False

        # Split on headings
        sections = re.split(r"^(#{1,4}\s+.+)$", text, flags=re.MULTILINE)
        stored = 0

        if len(sections) <= 1:
            # No headings — store as single section
            try:
                self.conn.execute(
                    "INSERT OR IGNORE INTO md_sections "
                    "(section_title, content, source_file) VALUES (?, ?, ?)",
                    (fname, text[:50000], fpath),
                )
                self.conn.commit()
                stored = 1
            except sqlite3.Error:
                pass
        else:
            current_title = fname
            for part in sections:
                part = part.strip()
                if not part:
                    continue
                if part.startswith("#"):
                    current_title = part.lstrip("#").strip()
                else:
                    try:
                        self.conn.execute(
                            "INSERT OR IGNORE INTO md_sections "
                            "(section_title, content, source_file) VALUES (?, ?, ?)",
                            (current_title, part[:50000], fpath),
                        )
                        stored += 1
                    except sqlite3.Error:
                        pass
            if stored:
                self.conn.commit()

        return True

    def _ingest_pdf_ref(self, fpath, fname):
        """Check if PDF already in documents table; add reference if not."""
        try:
            cur = self.conn.cursor()
            cur.execute(
                "SELECT id FROM documents WHERE file_name = ? OR file_path = ?",
                (fname, fpath),
            )
            if cur.fetchone():
                return True  # already tracked

            # Register in documents table
            fsize = os.path.getsize(fpath)
            cur.execute(
                "INSERT OR IGNORE INTO documents "
                "(file_path, file_name, file_size_bytes) VALUES (?, ?, ?)",
                (fpath, fname, fsize),
            )
            self.conn.commit()
            return True
        except sqlite3.Error:
            return False

    def _ingest_email(self, fpath, fname):
        """Basic email ingestion — read as text and store."""
        text, _ = _safe_read(fpath)
        if text is None:
            return False

        try:
            self.conn.execute(
                "INSERT OR IGNORE INTO md_sections "
                "(section_title, content, source_file) VALUES (?, ?, ?)",
                (f"[EMAIL] {fname}", text[:50000], fpath),
            )
            self.conn.commit()
        except sqlite3.Error:
            pass
        return True

    def _store_evidence_quotes(self, fpath, fname, text, analysis):
        """Store extracted legal quotes as evidence."""
        # Extract sentences containing citations
        sentences = re.split(r"[.\n]", text)
        stored = 0
        for sent in sentences:
            sent = sent.strip()
            if len(sent) < 20 or len(sent) > 2000:
                continue
            if LEGAL_CITE_RE.search(sent) or any(
                kw in sent.lower() for kw in ("order", "motion", "ruling", "custody", "pigors", "watson")
            ):
                try:
                    self.conn.execute(
                        "INSERT OR IGNORE INTO evidence_quotes "
                        "(quote_text, speaker, legal_significance, evidence_category, source_file) "
                        "VALUES (?, ?, ?, ?, ?)",
                        (
                            sent[:2000],
                            "document",
                            f"Auto-extracted from {fname}",
                            "scan_ingested",
                            fpath,
                        ),
                    )
                    stored += 1
                    if stored >= 50:
                        break
                except sqlite3.Error:
                    break
        if stored:
            self.conn.commit()

    # ------------------------------------------------------------------
    # extract_legal_content
    # ------------------------------------------------------------------

    def extract_legal_content(self, file_path, text=None):
        """Analyze a file for legal content and return structured results."""
        if text is None:
            text, _ = _safe_read(file_path)
        if text is None:
            return {
                "text": None,
                "legal_score": 0.0,
                "citations_found": [],
                "dates_found": [],
                "entities_found": [],
            }

        text_lower = text.lower()
        word_count = max(len(text_lower.split()), 1)

        # Keyword density
        keyword_hits = sum(1 for kw in LEGAL_KEYWORDS if kw in text_lower)
        keyword_score = min(keyword_hits / 10.0, 1.0)

        # Citation density
        citations = LEGAL_CITE_RE.findall(text)
        cite_score = min(len(citations) / 5.0, 1.0)

        # Date extraction
        dates = DATE_RE.findall(text)

        # Entity extraction (case numbers, party names)
        entities = []
        if "pigors" in text_lower:
            entities.append("Pigors")
        if "watson" in text_lower:
            entities.append("Watson")
        if "mcneill" in text_lower:
            entities.append("Judge McNeill")
        case_nums = re.findall(r"\b\d{4}[-‐]\d{4,7}[-‐]?\w*\b", text)
        entities.extend(case_nums[:10])

        # Composite legal relevance score
        legal_score = round(min((keyword_score * 0.5) + (cite_score * 0.5), 1.0), 3)

        return {
            "text": text[:5000],
            "legal_score": legal_score,
            "citations_found": citations[:50],
            "dates_found": dates[:30],
            "entities_found": list(set(entities))[:20],
        }

    # ------------------------------------------------------------------
    # deduplicate
    # ------------------------------------------------------------------

    def deduplicate(self):
        """Find duplicate files by content hash. Does NOT delete anything."""
        cur = self.conn.cursor()

        # First, compute hashes for files that don't have one
        cur.execute(
            "SELECT id, file_path, file_size FROM scan_inventory "
            "WHERE content_hash IS NULL AND file_size > 0 LIMIT 10000"
        )
        rows = cur.fetchall()
        updates = []
        for row in rows:
            h = _fast_hash(row["file_path"], row["file_size"])
            if h:
                updates.append((h, row["id"]))

        if updates:
            self.conn.executemany(
                "UPDATE scan_inventory SET content_hash = ? WHERE id = ?",
                updates,
            )
            self.conn.commit()

        # Find duplicates
        cur.execute(
            "SELECT content_hash, COUNT(*) as cnt, SUM(file_size) as total_size "
            "FROM scan_inventory "
            "WHERE content_hash IS NOT NULL "
            "GROUP BY content_hash HAVING cnt > 1 "
            "ORDER BY total_size DESC"
        )
        groups = cur.fetchall()

        dup_groups = len(groups)
        dup_files = sum(r["cnt"] - 1 for r in groups)
        # Wasted space = (count - 1) * avg_size per group
        wasted = sum((r["cnt"] - 1) * (r["total_size"] / r["cnt"]) for r in groups) if groups else 0

        return {
            "duplicate_groups": dup_groups,
            "duplicate_files": dup_files,
            "space_wasted_mb": round(wasted / (1024 * 1024), 2),
        }

    # ------------------------------------------------------------------
    # get_ingestion_stats
    # ------------------------------------------------------------------

    def get_ingestion_stats(self):
        """Comprehensive ingestion statistics."""
        cur = self.conn.cursor()

        cur.execute("SELECT COUNT(*) FROM scan_inventory")
        total = cur.fetchone()[0]

        cur.execute("SELECT COUNT(*) FROM scan_inventory WHERE ingested = 1")
        ingested = cur.fetchone()[0]

        cur.execute(
            "SELECT COUNT(*) FROM scan_inventory WHERE ingested = 0 AND error IS NULL"
        )
        pending = cur.fetchone()[0]

        cur.execute("SELECT COUNT(*) FROM scan_inventory WHERE error IS NOT NULL")
        failed_count = cur.fetchone()[0]

        # By doc_type
        cur.execute(
            "SELECT doc_type, COUNT(*) as cnt FROM scan_inventory GROUP BY doc_type"
        )
        by_type = {r["doc_type"]: r["cnt"] for r in cur.fetchall()}

        # By extension
        cur.execute(
            "SELECT file_ext, COUNT(*) as cnt FROM scan_inventory "
            "GROUP BY file_ext ORDER BY cnt DESC LIMIT 30"
        )
        by_ext = {r["file_ext"]: r["cnt"] for r in cur.fetchall()}

        # Storage
        cur.execute("SELECT COALESCE(SUM(file_size), 0) FROM scan_inventory")
        total_bytes = cur.fetchone()[0]
        cur.execute(
            "SELECT COALESCE(SUM(file_size), 0) FROM scan_inventory WHERE ingested = 1"
        )
        ingested_bytes = cur.fetchone()[0]
        cur.execute(
            "SELECT COALESCE(SUM(file_size), 0) FROM scan_inventory "
            "WHERE ingested = 0 AND error IS NULL"
        )
        pending_bytes = cur.fetchone()[0]

        return {
            "total_cataloged": total,
            "total_ingested": ingested,
            "pending": pending,
            "failed": failed_count,
            "by_type": by_type,
            "by_ext": by_ext,
            "storage_summary": {
                "total_gb": round(total_bytes / (1024 ** 3), 2),
                "ingested_gb": round(ingested_bytes / (1024 ** 3), 2),
                "pending_gb": round(pending_bytes / (1024 ** 3), 2),
            },
        }

    # ------------------------------------------------------------------
    # get_unprocessed
    # ------------------------------------------------------------------

    def get_unprocessed(self, doc_type=None, limit=50):
        """Get list of files not yet ingested."""
        query = (
            "SELECT file_path, file_name, file_ext, file_size, doc_type "
            "FROM scan_inventory WHERE ingested = 0 AND error IS NULL"
        )
        params = []
        if doc_type:
            query += " AND doc_type = ?"
            params.append(doc_type)
        query += f" LIMIT {int(limit)}"

        cur = self.conn.cursor()
        cur.execute(query, params)
        return [dict(r) for r in cur.fetchall()]

    # ------------------------------------------------------------------
    # mark_processed
    # ------------------------------------------------------------------

    def mark_processed(self, file_path, success=True, error=None):
        """Mark a file as processed (or failed with error message)."""
        try:
            now = datetime.now().isoformat()
            if success:
                self.conn.execute(
                    "UPDATE scan_inventory SET ingested = 1, ingested_at = ?, error = NULL "
                    "WHERE file_path = ?",
                    (now, file_path),
                )
            else:
                self.conn.execute(
                    "UPDATE scan_inventory SET ingested = 0, error = ? "
                    "WHERE file_path = ?",
                    (error or "Unknown error", file_path),
                )
            self.conn.commit()
        except sqlite3.Error as exc:
            print(f"[WARN] mark_processed error: {exc}")

    # ------------------------------------------------------------------
    # find_legal_documents
    # ------------------------------------------------------------------

    def find_legal_documents(self, keywords):
        """Search scan_inventory + ingested content for documents matching keywords."""
        results = []
        cur = self.conn.cursor()

        # Search scan_inventory by filename
        for kw in keywords if isinstance(keywords, list) else [keywords]:
            pattern = f"%{kw}%"
            cur.execute(
                "SELECT file_path, file_name, file_ext, doc_type, file_size "
                "FROM scan_inventory WHERE file_name LIKE ? OR file_path LIKE ? "
                "LIMIT 50",
                (pattern, pattern),
            )
            for row in cur.fetchall():
                results.append({
                    "source": "scan_inventory",
                    **dict(row),
                })

        # Search ingested content (md_sections)
        for kw in keywords if isinstance(keywords, list) else [keywords]:
            try:
                cur.execute(
                    "SELECT section_title, source_file, "
                    "substr(content, 1, 200) as snippet "
                    "FROM md_sections WHERE content LIKE ? LIMIT 30",
                    (f"%{kw}%",),
                )
                for row in cur.fetchall():
                    results.append({
                        "source": "md_sections",
                        **dict(row),
                    })
            except sqlite3.Error:
                pass

        # Search evidence_quotes
        for kw in keywords if isinstance(keywords, list) else [keywords]:
            try:
                cur.execute(
                    "SELECT quote_text, source_file, evidence_category "
                    "FROM evidence_quotes WHERE quote_text LIKE ? LIMIT 20",
                    (f"%{kw}%",),
                )
                for row in cur.fetchall():
                    results.append({
                        "source": "evidence_quotes",
                        **dict(row),
                    })
            except sqlite3.Error:
                pass

        # Deduplicate by file_path where applicable
        seen = set()
        unique = []
        for r in results:
            key = r.get("file_path") or r.get("source_file") or str(r)
            if key not in seen:
                seen.add(key)
                unique.append(r)

        return unique

    # ------------------------------------------------------------------
    # generate_ingestion_report
    # ------------------------------------------------------------------

    def generate_ingestion_report(self):
        """Human-readable report of ingestion status, coverage, and gaps."""
        stats = self.get_ingestion_stats()
        lines = [
            "=" * 70,
            "  MBP LitigationOS — Scan Ingestion Report",
            f"  Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
            "=" * 70,
            "",
            "OVERVIEW",
            f"  Total cataloged:  {stats['total_cataloged']:>10,}",
            f"  Ingested:         {stats['total_ingested']:>10,}",
            f"  Pending:          {stats['pending']:>10,}",
            f"  Failed:           {stats['failed']:>10,}",
            "",
            f"  Coverage:         {self._pct(stats['total_ingested'], stats['total_cataloged'])}",
            "",
            "STORAGE",
            f"  Total:            {stats['storage_summary']['total_gb']:>10.2f} GB",
            f"  Ingested:         {stats['storage_summary']['ingested_gb']:>10.2f} GB",
            f"  Pending:          {stats['storage_summary']['pending_gb']:>10.2f} GB",
            "",
            "BY DOCUMENT TYPE",
        ]

        for dtype, cnt in sorted(
            stats["by_type"].items(), key=lambda x: x[1], reverse=True
        ):
            lines.append(f"  {dtype or '(none)':<20} {cnt:>10,}")

        lines.append("")
        lines.append("BY FILE EXTENSION (top 15)")
        for ext, cnt in list(
            sorted(stats["by_ext"].items(), key=lambda x: x[1], reverse=True)
        )[:15]:
            lines.append(f"  {ext or '(none)':<10} {cnt:>10,}")

        # Gaps
        lines.append("")
        lines.append("GAPS & RECOMMENDATIONS")

        if stats["pending"] > 0:
            lines.append(
                f"  [!] {stats['pending']:,} files pending ingestion. "
                f"Run ingest_batch() to process."
            )
        if stats["failed"] > 0:
            lines.append(
                f"  [!] {stats['failed']:,} files failed. "
                f"Review errors with: SELECT file_path, error FROM scan_inventory WHERE error IS NOT NULL"
            )

        court_docs = stats["by_type"].get("court_doc", 0)
        evidence = stats["by_type"].get("evidence", 0)
        if court_docs == 0:
            lines.append("  [!] No court documents cataloged — check discovery/ path")
        if evidence == 0:
            lines.append("  [!] No evidence files cataloged — verify scan directory")

        lines.append("")
        lines.append("=" * 70)
        return "\n".join(lines)

    @staticmethod
    def _pct(part, total):
        if total == 0:
            return "N/A"
        return f"{(part / total) * 100:.1f}%"


# ---------------------------------------------------------------------------
# CLI entry point — catalog only (no auto-ingest)
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    import sys
    import time

    print("=" * 70)
    print("  MBP LitigationOS — Bulk Scan Directory Ingester")
    print("=" * 70)
    print()

    db = DEFAULT_DB
    root = DEFAULT_SCAN_ROOT

    # Allow CLI overrides
    if len(sys.argv) >= 2:
        root = sys.argv[1]
    if len(sys.argv) >= 3:
        db = sys.argv[2]

    print(f"  DB:   {db}")
    print(f"  Root: {root}")
    print()

    ingester = ScanIngester(db_path=db, scan_root=root)

    print("[1/3] Cataloging directory tree ...")
    t0 = time.time()
    result = ingester.catalog_directory()
    elapsed = time.time() - t0

    if "error" in result:
        print(f"  ERROR: {result['error']}")
        sys.exit(1)

    print(f"  Scanned {result['total_files']:,} files in {elapsed:.1f}s")
    print(f"  New files added: {result['new_files']:,}")
    print()

    print("[2/3] Computing ingestion stats ...")
    stats = ingester.get_ingestion_stats()
    print(f"  Cataloged:  {stats['total_cataloged']:,}")
    print(f"  Ingested:   {stats['total_ingested']:,}")
    print(f"  Pending:    {stats['pending']:,}")
    print(f"  Failed:     {stats['failed']:,}")
    print(f"  Storage:    {stats['storage_summary']['total_gb']:.2f} GB")
    print()

    print("[3/3] Full report:")
    print()
    print(ingester.generate_ingestion_report())

    ingester.close()
    print("\nDone. To ingest files, use:")
    print("  ingester = ScanIngester()")
    print("  ingester.ingest_batch(batch_size=100, doc_types=['court_doc'])")
