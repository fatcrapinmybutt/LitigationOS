import sys; sys.stdout = open(sys.stdout.fileno(), mode='w', encoding='utf-8', errors='replace')
"""
OMEGA Phase 0.5: Drive Ingestion Pipeline
==========================================
Sits between Phase 0 (Safety Snapshot) and Phase 1 (Inventory).
Scans local drive mirrors for new files, deduplicates by SHA-256,
classifies by case lane (MEEK signals), extracts text via PyMuPDF,
atomizes content into citations/entities/quotes, and records provenance.

Usage:
    python phase0_5_drive_ingest.py                     # Full run
    python phase0_5_drive_ingest.py --dry-run            # Scan only
    python phase0_5_drive_ingest.py --max-files 200      # Limit files
    python phase0_5_drive_ingest.py --roots C,D,F        # Specific drives

Callable from run_omega_pipeline.py:
    from phase0_5_drive_ingest import run_drive_ingest
    result = run_drive_ingest(cycle_dir, dry_run=False)
"""

import argparse
import hashlib
import json
import os
import re
import sqlite3
import threading
import time
from datetime import datetime
from pathlib import Path

# ── Ensure pipeline dir is importable ────────────────────────────────
_PIPELINE_DIR = Path(__file__).resolve().parent
if str(_PIPELINE_DIR) not in sys.path:
    sys.path.insert(0, str(_PIPELINE_DIR))

from config import (
    LITIGOS_ROOT, MEEK_SIGNALS, LANE_REGISTRY, DRIVE_SCAN_ROOTS,
    SKIP_DIRS, SKIP_EXTENSIONS, LEGAL_EXTENSIONS, long_path,
    MCL_PATTERN, MCR_PATTERN, MRE_PATTERN, CASE_CITE_PATTERN,
    USC_PATTERN, CANON_PATTERN, PERSON_NAMES,
    sha256_file, make_atom_id, PipelineLogger, report_progress,
    get_cyclepack_dir, CYCLE_TS,
)
from failsafe import safe_call, timeout, never_crash

# ── Optional heavy imports (lazy) ────────────────────────────────────
_fitz = None
_docx = None


def _get_fitz():
    """Lazy-load PyMuPDF."""
    global _fitz
    if _fitz is None:
        try:
            import fitz as _f
            _fitz = _f
        except ImportError:
            pass
    return _fitz


def _get_docx():
    """Lazy-load python-docx."""
    global _docx
    if _docx is None:
        try:
            import docx as _d
            _docx = _d
        except ImportError:
            pass
    return _docx


# ── Constants ────────────────────────────────────────────────────────
_CENTRAL_DB = LITIGOS_ROOT / "litigation_context.db"
_PHASE_ID = "phase0_5"
_PHASE_NAME = "Phase 0.5: Drive Ingest"

_DATE_PATTERNS = [
    re.compile(r"\b(\d{1,2}[/\-]\d{1,2}[/\-]\d{2,4})\b"),
    re.compile(r"\b((?:January|February|March|April|May|June|July|August|"
               r"September|October|November|December)\s+\d{1,2},?\s+\d{4})\b", re.I),
    re.compile(r"\b(\d{4}-\d{2}-\d{2})\b"),
]

# MEEK lane priority: E → D → F → C → A → B
_LANE_PRIORITY = [
    ("E", "MEEK4"),
    ("D", "MEEK3"),
    ("F", "MEEK5"),
    ("C", None),
    ("A", "MEEK2"),
    ("B", "MEEK1"),
]

# ── DB Schema ────────────────────────────────────────────────────────
_SCHEMA_SQL = """
CREATE TABLE IF NOT EXISTS drive_files (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    file_path TEXT NOT NULL UNIQUE,
    file_name TEXT NOT NULL,
    extension TEXT,
    size_bytes INTEGER,
    sha256 TEXT NOT NULL,
    modified_time TEXT,
    drive_letter TEXT,
    lane TEXT,
    meek_signal TEXT,
    status TEXT DEFAULT 'pending',
    page_count INTEGER DEFAULT 0,
    extracted_text_length INTEGER DEFAULT 0,
    atom_count INTEGER DEFAULT 0,
    run_id TEXT,
    created_at TEXT,
    updated_at TEXT
);
CREATE INDEX IF NOT EXISTS idx_df_sha256 ON drive_files(sha256);
CREATE INDEX IF NOT EXISTS idx_df_status ON drive_files(status);
CREATE INDEX IF NOT EXISTS idx_df_lane ON drive_files(lane);
CREATE INDEX IF NOT EXISTS idx_df_run_id ON drive_files(run_id);
CREATE INDEX IF NOT EXISTS idx_df_extension ON drive_files(extension);

CREATE TABLE IF NOT EXISTS file_atoms (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    atom_id TEXT NOT NULL UNIQUE,
    file_id INTEGER NOT NULL,
    atom_type TEXT NOT NULL,
    content TEXT NOT NULL,
    page_num INTEGER,
    char_offset INTEGER,
    lane TEXT,
    provenance_hash TEXT,
    run_id TEXT,
    created_at TEXT,
    FOREIGN KEY (file_id) REFERENCES drive_files(id)
);
CREATE INDEX IF NOT EXISTS idx_fa_file_id ON file_atoms(file_id);
CREATE INDEX IF NOT EXISTS idx_fa_type ON file_atoms(atom_type);
CREATE INDEX IF NOT EXISTS idx_fa_lane ON file_atoms(lane);
CREATE INDEX IF NOT EXISTS idx_fa_atom_id ON file_atoms(atom_id);

CREATE TABLE IF NOT EXISTS provenance_refs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    atom_id TEXT NOT NULL,
    source_table TEXT NOT NULL,
    source_id TEXT,
    match_type TEXT,
    confidence REAL DEFAULT 0.0,
    run_id TEXT,
    created_at TEXT
);
CREATE INDEX IF NOT EXISTS idx_pr_atom ON provenance_refs(atom_id);
CREATE INDEX IF NOT EXISTS idx_pr_source ON provenance_refs(source_table, source_id);

CREATE TABLE IF NOT EXISTS ingest_logs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    run_id TEXT NOT NULL,
    phase TEXT DEFAULT 'phase0_5',
    step TEXT,
    status TEXT,
    files_scanned INTEGER DEFAULT 0,
    files_new INTEGER DEFAULT 0,
    files_deduped INTEGER DEFAULT 0,
    files_classified INTEGER DEFAULT 0,
    files_extracted INTEGER DEFAULT 0,
    atoms_created INTEGER DEFAULT 0,
    atoms_linked INTEGER DEFAULT 0,
    gaps_created INTEGER DEFAULT 0,
    errors INTEGER DEFAULT 0,
    elapsed_seconds REAL DEFAULT 0.0,
    detail TEXT,
    created_at TEXT
);
CREATE INDEX IF NOT EXISTS idx_il_run ON ingest_logs(run_id);
"""


class DriveIngestPhase:
    """Phase 0.5: Drive ingestion — scan, dedup, classify, extract, atomize."""

    SUPPORTED_TEXT_EXTS = {'.pdf', '.docx', '.doc', '.txt', '.md', '.rtf', '.html', '.htm'}
    SUPPORTED_DATA_EXTS = {'.csv', '.json', '.jsonl', '.xml', '.yaml', '.yml'}

    def __init__(self, db_path=None, run_id=None, scan_roots=None,
                 max_files_per_root=10000, batch_size=100, dry_run=False,
                 cycle_dir=None):
        self.db_path = Path(db_path) if db_path else _CENTRAL_DB
        self.run_id = run_id or f"RUN_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        self.scan_roots = scan_roots or DRIVE_SCAN_ROOTS
        self.max_files_per_root = max_files_per_root
        self.batch_size = batch_size
        self.dry_run = dry_run
        self.cycle_dir = Path(cycle_dir) if cycle_dir else None
        self.log = PipelineLogger(_PHASE_NAME, self.cycle_dir)
        self._local = threading.local()
        self._stats = {
            "files_scanned": 0,
            "files_new": 0,
            "files_deduped": 0,
            "files_classified": 0,
            "files_extracted": 0,
            "atoms_created": 0,
            "atoms_linked": 0,
            "gaps_created": 0,
            "errors": 0,
        }
        # Extracted text cache: file_id → text (cleared after atomize)
        self._text_cache: dict[int, str] = {}

    # ── DB Connection (thread-safe) ──────────────────────────────────
    def _get_conn(self) -> sqlite3.Connection:
        """Thread-local DB connection with WAL mode."""
        conn = getattr(self._local, 'conn', None)
        if conn is None:
            conn = sqlite3.connect(str(self.db_path), timeout=120)
            conn.execute("PRAGMA journal_mode=WAL")
            conn.execute("PRAGMA synchronous=NORMAL")
            conn.execute("PRAGMA busy_timeout=180000")
            conn.execute("PRAGMA mmap_size=12884901888")  # 12GB mmap (Δ∞)
            conn.execute("PRAGMA cache_size=-131072")  # 128MB cache
            conn.execute("PRAGMA temp_store=MEMORY")
            conn.row_factory = sqlite3.Row
            self._local.conn = conn
        return conn

    def _ensure_schema(self):
        """Create tables if they don't exist."""
        conn = self._get_conn()
        conn.executescript(_SCHEMA_SQL)
        conn.commit()

    def _close(self):
        """Close thread-local connection."""
        conn = getattr(self._local, 'conn', None)
        if conn is not None:
            try:
                conn.close()
            except Exception:
                pass
            self._local.conn = None

    # ── Main Entry Point ─────────────────────────────────────────────
    def run(self) -> dict:
        """Execute the full phase. Returns summary stats dict."""
        t0 = time.time()
        self._start_time = datetime.now().isoformat()
        self.log.info(f"Starting {_PHASE_NAME} — run_id={self.run_id}")
        self.log.info(f"DB: {self.db_path} | dry_run={self.dry_run}")

        try:
            self._ensure_schema()

            # Step 1: Scan
            self.log.info("Step 1/8: Scanning drive roots...")
            n_scanned = safe_call(self.scan, timeout_s=600, fallback=0,
                                  component="phase0_5.scan")
            self.log.info(f"Scan complete: {n_scanned} new files found")

            if self.dry_run:
                self.log.info("DRY RUN — skipping steps 2-8")
                self._stats["elapsed"] = time.time() - t0
                self.log_summary(self._stats)
                return self._stats

            # Step 2: Dedup
            self.log.info("Step 2/8: Deduplicating by SHA-256...")
            n_deduped = safe_call(self.dedup, timeout_s=300, fallback=0,
                                  component="phase0_5.dedup")
            self.log.info(f"Dedup complete: {n_deduped} duplicates marked")

            # Step 3: Classify
            self.log.info("Step 3/8: Classifying by MEEK lane...")
            n_classified = safe_call(self.classify, timeout_s=300, fallback=0,
                                     component="phase0_5.classify")
            self.log.info(f"Classify complete: {n_classified} files assigned lanes")

            # Step 4: Extract
            self.log.info("Step 4/8: Extracting text...")
            n_extracted = safe_call(self.extract, timeout_s=600, fallback=0,
                                    component="phase0_5.extract")
            self.log.info(f"Extract complete: {n_extracted} files processed")

            # Step 5: Atomize
            self.log.info("Step 5/8: Atomizing content...")
            n_atoms = safe_call(self.atomize, timeout_s=600, fallback=0,
                                component="phase0_5.atomize")
            self.log.info(f"Atomize complete: {n_atoms} atoms created")

            # Step 6: Cross-link
            self.log.info("Step 6/8: Cross-linking atoms to evidence_quotes...")
            n_linked = safe_call(self.cross_link, timeout_s=300, fallback=0,
                                 component="phase0_5.cross_link")
            self.log.info(f"Cross-link complete: {n_linked} atoms linked")

            # Step 7: Gap check
            self.log.info("Step 7/8: Checking for evidence gaps...")
            n_gaps = safe_call(self.gap_check, timeout_s=300, fallback=0,
                               component="phase0_5.gap_check")
            self.log.info(f"Gap check complete: {n_gaps} new gap tickets")

            # Step 8: Log summary
            self._stats["elapsed"] = time.time() - t0
            self.log.info("Step 8/8: Recording summary...")
            self.log_summary(self._stats)

        except Exception as e:
            self.log.error(f"Phase failed: {e}")
            self._stats["errors"] += 1
            self._stats["elapsed"] = time.time() - t0
            self.log_summary(self._stats)
        finally:
            self._text_cache.clear()
            self._close()

        elapsed = self._stats.get("elapsed", time.time() - t0)
        self.log.info(f"Phase 0.5 complete in {elapsed:.1f}s — {self._stats}")
        return self._stats

    # ── Step 1: Scan ─────────────────────────────────────────────────
    @never_crash(fallback=0)
    def scan(self) -> int:
        """Scan drive roots for new litigation-relevant files.
        Records new files in drive_files with status='pending'.
        Returns count of new files found."""
        conn = self._get_conn()
        total_new = 0
        total_scanned = 0

        for drive_letter, roots in self.scan_roots.items():
            for root in roots:
                root_path = Path(root)
                if not root_path.exists():
                    self.log.warn(f"Scan root not found: {root_path}")
                    continue

                self.log.info(f"Scanning {root_path} (drive {drive_letter})...")
                root_new = 0
                root_scanned = 0
                batch = []

                try:
                    for dirpath, dirnames, filenames in os.walk(
                            long_path(root_path), topdown=True):
                        # Filter out skip dirs in-place
                        dirnames[:] = [
                            d for d in dirnames
                            if d not in SKIP_DIRS
                            and not d.startswith('.')
                        ]

                        for fname in filenames:
                            if root_scanned >= self.max_files_per_root:
                                break

                            ext = os.path.splitext(fname)[1].lower()
                            if ext in SKIP_EXTENSIONS:
                                continue
                            if ext not in LEGAL_EXTENSIONS:
                                continue

                            fpath = os.path.join(dirpath, fname)
                            root_scanned += 1
                            total_scanned += 1

                            try:
                                file_hash = self._compute_sha256(fpath)
                            except (OSError, PermissionError) as e:
                                self._stats["errors"] += 1
                                continue

                            # Check if already in drive_files
                            existing = conn.execute(
                                "SELECT id FROM drive_files WHERE file_path = ?",
                                (fpath,)
                            ).fetchone()
                            if existing:
                                continue

                            try:
                                stat = os.stat(long_path(fpath))
                                size = stat.st_size
                                mtime = datetime.fromtimestamp(
                                    stat.st_mtime).isoformat()
                            except OSError:
                                size = 0
                                mtime = None

                            now = datetime.now().isoformat()
                            batch.append((
                                fpath, fname, ext, size, file_hash, mtime,
                                drive_letter, 'pending', self.run_id, now, now
                            ))
                            root_new += 1
                            total_new += 1

                            # Checkpoint every batch_size files
                            if len(batch) >= self.batch_size:
                                if not self.dry_run:
                                    self._insert_file_batch(conn, batch)
                                batch = []
                                self._log_checkpoint("scan", {
                                    "scanned": total_scanned,
                                    "new": total_new
                                })

                        if root_scanned >= self.max_files_per_root:
                            self.log.warn(
                                f"Hit max_files_per_root ({self.max_files_per_root}) "
                                f"for {root_path}")
                            break

                except (PermissionError, OSError) as e:
                    self.log.error(f"Walk error on {root_path}: {e}")
                    self._stats["errors"] += 1

                # Flush remaining batch
                if batch and not self.dry_run:
                    self._insert_file_batch(conn, batch)

                self.log.info(
                    f"  {root_path}: scanned={root_scanned}, new={root_new}")

                if total_scanned % 1000 == 0:
                    report_progress(_PHASE_ID, total_scanned,
                                    self.max_files_per_root * len(self.scan_roots))

        self._stats["files_scanned"] = total_scanned
        self._stats["files_new"] = total_new
        return total_new

    def _insert_file_batch(self, conn: sqlite3.Connection, batch: list):
        """Batch-insert files into drive_files."""
        conn.executemany(
            """INSERT OR IGNORE INTO drive_files
               (file_path, file_name, extension, size_bytes, sha256,
                modified_time, drive_letter, status, run_id,
                created_at, updated_at)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            batch
        )
        conn.commit()

    # ── Step 2: Dedup ────────────────────────────────────────────────
    @never_crash(fallback=0)
    def dedup(self) -> int:
        """Mark duplicate files (same SHA-256) in drive_files.
        Keeps the file with smallest id (earliest ingested).
        Returns count of duplicates marked."""
        conn = self._get_conn()
        # Find SHA-256 hashes with more than one file
        dupes = conn.execute("""
            SELECT sha256, COUNT(*) as cnt
            FROM drive_files
            WHERE status = 'pending' AND run_id = ?
            GROUP BY sha256
            HAVING cnt > 1
        """, (self.run_id,)).fetchall()

        total_duped = 0
        for row in dupes:
            sha = row["sha256"]
            # Keep the one with the lowest id (earliest path)
            files = conn.execute("""
                SELECT id FROM drive_files
                WHERE sha256 = ? AND status = 'pending'
                ORDER BY id ASC
            """, (sha,)).fetchall()

            if len(files) <= 1:
                continue

            # Mark all except first as duplicate
            dupe_ids = [f["id"] for f in files[1:]]
            placeholders = ",".join("?" * len(dupe_ids))
            conn.execute(
                f"UPDATE drive_files SET status = 'duplicate', "
                f"updated_at = ? WHERE id IN ({placeholders})",
                [datetime.now().isoformat()] + dupe_ids
            )
            total_duped += len(dupe_ids)

        conn.commit()
        self._stats["files_deduped"] = total_duped
        return total_duped

    # ── Step 3: Classify ─────────────────────────────────────────────
    @never_crash(fallback=0)
    def classify(self) -> int:
        """Assign MEEK lane to each pending file in drive_files.
        Priority: E → D → F → C → A → B
        Returns count classified."""
        conn = self._get_conn()
        pending = conn.execute("""
            SELECT id, file_path, file_name
            FROM drive_files
            WHERE status = 'pending' AND run_id = ?
        """, (self.run_id,)).fetchall()

        classified = 0
        batch_updates = []

        for row in pending:
            fid = row["id"]
            fpath = row["file_path"]
            fname = row["file_name"]

            # Read first 10KB for content-based classification
            preview = ""
            try:
                with open(long_path(fpath), "r", encoding="utf-8",
                          errors="replace") as f:
                    preview = f.read(10240)
            except (OSError, PermissionError, UnicodeDecodeError):
                # Binary file — try reading as bytes and decode
                try:
                    with open(long_path(fpath), "rb") as f:
                        raw = f.read(10240)
                    preview = raw.decode("utf-8", errors="replace")
                except (OSError, PermissionError):
                    pass

            lane, meek_signal = self._classify_lane(fname, preview)
            now = datetime.now().isoformat()
            batch_updates.append((lane, meek_signal, 'classified', now, fid))
            classified += 1

            if len(batch_updates) >= self.batch_size:
                conn.executemany(
                    """UPDATE drive_files
                       SET lane = ?, meek_signal = ?, status = ?,
                           updated_at = ?
                       WHERE id = ?""",
                    batch_updates
                )
                conn.commit()
                batch_updates = []
                self._log_checkpoint("classify", {"classified": classified})

        # Flush remaining
        if batch_updates:
            conn.executemany(
                """UPDATE drive_files
                   SET lane = ?, meek_signal = ?, status = ?,
                       updated_at = ?
                   WHERE id = ?""",
                batch_updates
            )
            conn.commit()

        self._stats["files_classified"] = classified
        return classified

    # ── Step 4: Extract ──────────────────────────────────────────────
    @never_crash(fallback=0)
    def extract(self, max_extract=500) -> int:
        """Extract text from classified files.
        Returns count of files successfully extracted."""
        conn = self._get_conn()
        files = conn.execute("""
            SELECT id, file_path, extension
            FROM drive_files
            WHERE status IN ('pending', 'classified') AND run_id = ?
            ORDER BY size_bytes ASC
            LIMIT ?
        """, (self.run_id, max_extract)).fetchall()

        extracted = 0
        for row in files:
            fid = row["id"]
            fpath = row["file_path"]
            ext = (row["extension"] or "").lower()
            text = ""
            page_count = 0

            try:
                if ext == ".pdf":
                    pages = self._extract_pdf(fpath)
                    page_count = len(pages)
                    text = "\n\n".join(p["text"] for p in pages if p["text"])
                elif ext in (".docx", ".doc"):
                    text = self._extract_docx(fpath)
                elif ext in ('.txt', '.md', '.html', '.htm', '.rtf'):
                    text = self._extract_text(fpath)
                elif ext in self.SUPPORTED_DATA_EXTS:
                    text = self._extract_text(fpath)
                else:
                    continue
            except Exception as e:
                self.log.error(f"Extract failed [{fpath}]: {e}")
                self._stats["errors"] += 1
                conn.execute(
                    "UPDATE drive_files SET status = 'extract_error', "
                    "updated_at = ? WHERE id = ?",
                    (datetime.now().isoformat(), fid)
                )
                conn.commit()
                continue

            text_len = len(text)
            if text_len > 0:
                self._text_cache[fid] = text

            now = datetime.now().isoformat()
            conn.execute(
                """UPDATE drive_files
                   SET status = 'extracted', page_count = ?,
                       extracted_text_length = ?, updated_at = ?
                   WHERE id = ?""",
                (page_count, text_len, now, fid)
            )
            extracted += 1

            if extracted % self.batch_size == 0:
                conn.commit()
                self._log_checkpoint("extract", {"extracted": extracted})
                report_progress(_PHASE_ID, extracted, len(files))

        conn.commit()
        self._stats["files_extracted"] = extracted
        return extracted

    # ── Step 5: Atomize ──────────────────────────────────────────────
    @never_crash(fallback=0)
    def atomize(self) -> int:
        """Break extracted text into atoms (citations, entities, quotes, dates).
        Inserts into file_atoms with provenance.
        Returns count of atoms created."""
        conn = self._get_conn()
        total_atoms = 0

        # Process files that are extracted and have cached text
        file_ids = list(self._text_cache.keys())
        if not file_ids:
            # Fall back: load from DB for files marked extracted this run
            rows = conn.execute("""
                SELECT id, file_path FROM drive_files
                WHERE status = 'extracted' AND run_id = ?
            """, (self.run_id,)).fetchall()
            for r in rows:
                text = safe_call(self._extract_text, r["file_path"],
                                 timeout_s=30, fallback="")
                if text:
                    self._text_cache[r["id"]] = text
            file_ids = list(self._text_cache.keys())

        for fid in file_ids:
            text = self._text_cache.get(fid, "")
            if not text:
                continue

            # Get lane for this file
            row = conn.execute(
                "SELECT lane FROM drive_files WHERE id = ?", (fid,)
            ).fetchone()
            lane = row["lane"] if row else None

            atoms_batch = []
            now = datetime.now().isoformat()

            # Citation atoms (MCL, MCR, MRE, case law, USC, Canon)
            for match in MCL_PATTERN.finditer(text):
                aid = make_atom_id("DI", str(fid), "mcl_cite", match.group())
                atoms_batch.append((
                    aid, fid, "mcl_citation", match.group().strip(),
                    None, match.start(), lane,
                    hashlib.sha256(match.group().encode()).hexdigest()[:16],
                    self.run_id, now
                ))

            for match in MCR_PATTERN.finditer(text):
                aid = make_atom_id("DI", str(fid), "mcr_cite", match.group())
                atoms_batch.append((
                    aid, fid, "mcr_citation", match.group().strip(),
                    None, match.start(), lane,
                    hashlib.sha256(match.group().encode()).hexdigest()[:16],
                    self.run_id, now
                ))

            for match in MRE_PATTERN.finditer(text):
                aid = make_atom_id("DI", str(fid), "mre_cite", match.group())
                atoms_batch.append((
                    aid, fid, "mre_citation", match.group().strip(),
                    None, match.start(), lane,
                    hashlib.sha256(match.group().encode()).hexdigest()[:16],
                    self.run_id, now
                ))

            for match in CASE_CITE_PATTERN.finditer(text):
                aid = make_atom_id("DI", str(fid), "case_cite", match.group())
                atoms_batch.append((
                    aid, fid, "case_citation", match.group().strip(),
                    None, match.start(), lane,
                    hashlib.sha256(match.group().encode()).hexdigest()[:16],
                    self.run_id, now
                ))

            for match in USC_PATTERN.finditer(text):
                aid = make_atom_id("DI", str(fid), "usc_cite", match.group())
                atoms_batch.append((
                    aid, fid, "usc_citation", match.group().strip(),
                    None, match.start(), lane,
                    hashlib.sha256(match.group().encode()).hexdigest()[:16],
                    self.run_id, now
                ))

            # Entity atoms
            for entity_atoms in self._find_entities(text):
                aid = make_atom_id(
                    "DI", str(fid), "entity",
                    f"{entity_atoms['name']}@{entity_atoms['offset']}"
                )
                atoms_batch.append((
                    aid, fid, "entity", entity_atoms["name"],
                    None, entity_atoms["offset"], lane,
                    hashlib.sha256(entity_atoms["name"].encode()).hexdigest()[:16],
                    self.run_id, now
                ))

            # Date atoms
            for date_atom in self._find_dates(text):
                aid = make_atom_id(
                    "DI", str(fid), "date",
                    f"{date_atom['text']}@{date_atom['offset']}"
                )
                atoms_batch.append((
                    aid, fid, "date", date_atom["text"],
                    None, date_atom["offset"], lane,
                    hashlib.sha256(date_atom["text"].encode()).hexdigest()[:16],
                    self.run_id, now
                ))

            # Quote atoms: paragraphs > 50 chars
            for para in text.split("\n"):
                para = para.strip()
                if len(para) > 50:
                    offset = text.find(para)
                    aid = make_atom_id(
                        "DI", str(fid), "quote",
                        hashlib.sha256(para.encode()).hexdigest()[:32]
                    )
                    atoms_batch.append((
                        aid, fid, "quote", para[:2000],  # cap at 2KB
                        None, offset if offset >= 0 else None, lane,
                        hashlib.sha256(para.encode()).hexdigest()[:16],
                        self.run_id, now
                    ))

            # Batch insert
            if atoms_batch:
                try:
                    conn.executemany(
                        """INSERT OR IGNORE INTO file_atoms
                           (atom_id, file_id, atom_type, content,
                            page_num, char_offset, lane, provenance_hash,
                            run_id, created_at)
                           VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                        atoms_batch
                    )
                    conn.commit()
                    total_atoms += len(atoms_batch)
                except Exception as e:
                    self.log.error(f"Atom insert error (file_id={fid}): {e}")
                    self._stats["errors"] += 1

            # Update atom_count on the file
            conn.execute(
                "UPDATE drive_files SET atom_count = ?, updated_at = ? WHERE id = ?",
                (len(atoms_batch), datetime.now().isoformat(), fid)
            )

            if total_atoms % 500 == 0 and total_atoms > 0:
                self._log_checkpoint("atomize", {"atoms": total_atoms})

        conn.commit()
        self._stats["atoms_created"] = total_atoms
        # Free memory
        self._text_cache.clear()
        return total_atoms

    # ── Step 6: Cross-link ───────────────────────────────────────────
    @never_crash(fallback=0)
    def cross_link(self) -> int:
        """Link new atoms to existing evidence_quotes via text matching.
        Returns count of atoms linked."""
        conn = self._get_conn()
        linked = 0

        # Check if evidence_quotes table exists
        tbl = conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name='evidence_quotes'"
        ).fetchone()
        if not tbl:
            self.log.warn("evidence_quotes table not found — skipping cross-link")
            return 0

        # Get citation atoms from this run
        citation_atoms = conn.execute("""
            SELECT atom_id, content, atom_type
            FROM file_atoms
            WHERE run_id = ? AND atom_type IN (
                'mcl_citation', 'mcr_citation', 'mre_citation',
                'case_citation', 'usc_citation'
            )
        """, (self.run_id,)).fetchall()

        now = datetime.now().isoformat()
        batch = []

        for atom in citation_atoms:
            content = atom["content"]
            # Exact substring search in evidence_quotes
            try:
                matches = conn.execute(
                    """SELECT rowid AS rid FROM evidence_quotes
                       WHERE quote_text LIKE ? LIMIT 5""",
                    (f"%{content}%",)
                ).fetchall()
            except Exception:
                try:
                    matches = conn.execute(
                        """SELECT rowid AS rid FROM evidence_quotes
                           WHERE text LIKE ? LIMIT 5""",
                        (f"%{content}%",)
                    ).fetchall()
                except Exception:
                    matches = []

            for m in matches:
                batch.append((
                    atom["atom_id"], "evidence_quotes", str(m["rid"]),
                    "exact_substring", 1.0, self.run_id, now
                ))
                linked += 1

            if len(batch) >= self.batch_size:
                conn.executemany(
                    """INSERT OR IGNORE INTO provenance_refs
                       (atom_id, source_table, source_id, match_type,
                        confidence, run_id, created_at)
                       VALUES (?, ?, ?, ?, ?, ?, ?)""",
                    batch
                )
                conn.commit()
                batch = []

        # Flush
        if batch:
            conn.executemany(
                """INSERT OR IGNORE INTO provenance_refs
                   (atom_id, source_table, source_id, match_type,
                    confidence, run_id, created_at)
                   VALUES (?, ?, ?, ?, ?, ?, ?)""",
                batch
            )
            conn.commit()

        self._stats["atoms_linked"] = linked
        return linked

    # ── Step 7: Gap Check ────────────────────────────────────────────
    @never_crash(fallback=0)
    def gap_check(self) -> int:
        """Analyze for missing evidence and create gap_tickets.
        Returns count of new gaps found."""
        conn = self._get_conn()
        gaps = 0

        # Check if gap_tickets table exists
        tbl = conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name='gap_tickets'"
        ).fetchone()
        if not tbl:
            self.log.warn("gap_tickets table not found — skipping gap check")
            return 0

        # Find lanes with low atom counts from this run
        lane_stats = conn.execute("""
            SELECT lane, COUNT(*) as file_count,
                   SUM(atom_count) as total_atoms
            FROM drive_files
            WHERE run_id = ? AND lane IS NOT NULL
            GROUP BY lane
        """, (self.run_id,)).fetchall()

        now = datetime.now().isoformat()
        for ls in lane_stats:
            lane = ls["lane"]
            total_atoms = ls["total_atoms"] or 0
            file_count = ls["file_count"] or 0

            # If a lane has files but very few atoms, flag it
            if file_count > 0 and total_atoms < file_count * 2:
                try:
                    lane_name = LANE_REGISTRY.get(lane, {}).get("name", lane)
                    conn.execute(
                        """INSERT INTO gap_tickets
                           (ticket_id, filing_name, gap_type, description,
                            severity, resolution_status, created_at)
                           VALUES (?, ?, ?, ?, ?, ?, ?)""",
                        (f"GAP-{self.run_id}-{lane}",
                         f"Lane {lane}",
                         "low_atom_density",
                         f"Lane {lane} ({lane_name}): {file_count} files but only "
                         f"{total_atoms} atoms — may need manual review",
                         "medium", "open", now)
                    )
                    gaps += 1
                except Exception as e:
                    # gap_tickets schema may differ — log and continue
                    self.log.warn(f"Could not insert gap_ticket: {e}")

        conn.commit()
        self._stats["gaps_created"] = gaps
        return gaps

    # ── Step 8: Log Summary ──────────────────────────────────────────
    def log_summary(self, stats: dict):
        """Record run results in ingest_logs."""
        try:
            conn = self._get_conn()
            now = datetime.now().isoformat()
            conn.execute(
                """INSERT INTO ingest_logs
                   (run_id, phase, step, status, started_at, ended_at,
                    files_scanned, files_new, files_deduped,
                    files_classified, files_extracted,
                    atoms_created, atoms_linked, gaps_created,
                    errors, elapsed_seconds, detail, created_at)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                (self.run_id, _PHASE_ID, "complete",
                 "dry_run" if self.dry_run else "done",
                 getattr(self, '_start_time', now), now,
                 stats.get("files_scanned", 0),
                 stats.get("files_new", 0),
                 stats.get("files_deduped", 0),
                 stats.get("files_classified", 0),
                 stats.get("files_extracted", 0),
                 stats.get("atoms_created", 0),
                 stats.get("atoms_linked", 0),
                 stats.get("gaps_created", 0),
                 stats.get("errors", 0),
                 stats.get("elapsed", 0.0),
                 json.dumps(stats),
                 now)
            )
            conn.commit()
        except Exception as e:
            self.log.error(f"Failed to write ingest_logs: {e}")

    # ── Utility: SHA-256 ─────────────────────────────────────────────
    def _compute_sha256(self, filepath: str) -> str:
        """Compute SHA-256 hash reading in 64KB chunks."""
        h = hashlib.sha256()
        with open(long_path(filepath), "rb") as f:
            while True:
                chunk = f.read(65536)
                if not chunk:
                    break
                h.update(chunk)
        return h.hexdigest()

    # ── Utility: MEEK Lane Classification ────────────────────────────
    def _classify_lane(self, filename: str, text_preview: str) -> tuple:
        """Classify file into lane using MEEK signals.
        Returns (lane, meek_signal). Priority: E → D → F → C → A → B."""
        combined = f"{filename}\n{text_preview}"

        for lane, meek_key in _LANE_PRIORITY:
            if meek_key is None:
                continue  # Lane C has no MEEK signal — assigned by cross-reference
            pattern = MEEK_SIGNALS.get(meek_key)
            if pattern and pattern.search(combined):
                return (lane, meek_key)

        # Default: Lane A (custody — most common)
        return ("A", "MEEK2_default")

    # ── Utility: PDF Extraction ──────────────────────────────────────
    @never_crash(fallback=[])
    def _extract_pdf(self, filepath: str) -> list:
        """Extract text from PDF via PyMuPDF.
        Returns [{'page': int, 'text': str}, ...]."""
        fitz = _get_fitz()
        if fitz is None:
            self.log.warn("PyMuPDF not available — skipping PDF extraction")
            return []

        pages = []
        try:
            doc = fitz.open(long_path(filepath))
            for i, page in enumerate(doc):
                text = page.get_text("text") or ""
                pages.append({"page": i + 1, "text": text})
            doc.close()
        except Exception as e:
            self.log.error(f"PDF extract error [{filepath}]: {e}")
        return pages

    # ── Utility: DOCX Extraction ─────────────────────────────────────
    @never_crash(fallback="")
    def _extract_docx(self, filepath: str) -> str:
        """Extract text from DOCX via python-docx. Returns full text."""
        docx_mod = _get_docx()
        if docx_mod is None:
            self.log.warn("python-docx not available — skipping DOCX extraction")
            return ""

        try:
            doc = docx_mod.Document(long_path(filepath))
            return "\n".join(p.text for p in doc.paragraphs if p.text)
        except Exception as e:
            self.log.error(f"DOCX extract error [{filepath}]: {e}")
            return ""

    # ── Utility: Text Extraction ─────────────────────────────────────
    @never_crash(fallback="")
    def _extract_text(self, filepath: str) -> str:
        """Extract text from TXT/MD/HTML/etc. Returns full text."""
        try:
            with open(long_path(filepath), "r", encoding="utf-8",
                      errors="replace") as f:
                return f.read(5_000_000)  # Cap at 5MB
        except (OSError, PermissionError) as e:
            self.log.error(f"Text extract error [{filepath}]: {e}")
            return ""

    # ── Utility: Find Citations ──────────────────────────────────────
    def _find_citations(self, text: str) -> list:
        """Find all legal citations in text using config regex patterns."""
        citations = []
        for pattern, ctype in [
            (MCL_PATTERN, "mcl"), (MCR_PATTERN, "mcr"),
            (MRE_PATTERN, "mre"), (CASE_CITE_PATTERN, "case"),
            (USC_PATTERN, "usc"), (CANON_PATTERN, "canon"),
        ]:
            for m in pattern.finditer(text):
                citations.append({
                    "type": ctype,
                    "text": m.group().strip(),
                    "offset": m.start(),
                })
        return citations

    # ── Utility: Find Entities ───────────────────────────────────────
    def _find_entities(self, text: str) -> list:
        """Find person/entity mentions using PERSON_NAMES from config."""
        entities = []
        seen = set()
        for name, role in PERSON_NAMES.items():
            for m in re.finditer(re.escape(name), text, re.IGNORECASE):
                key = f"{name}@{m.start()}"
                if key not in seen:
                    seen.add(key)
                    entities.append({
                        "name": name,
                        "role": role,
                        "offset": m.start(),
                    })
        return entities

    # ── Utility: Find Dates ──────────────────────────────────────────
    def _find_dates(self, text: str) -> list:
        """Find date references in text."""
        dates = []
        seen = set()
        for pattern in _DATE_PATTERNS:
            for m in pattern.finditer(text):
                key = f"{m.group()}@{m.start()}"
                if key not in seen:
                    seen.add(key)
                    dates.append({
                        "text": m.group().strip(),
                        "offset": m.start(),
                    })
        return dates

    # ── Checkpoint Helper ────────────────────────────────────────────
    def _log_checkpoint(self, step: str, detail: dict):
        """Write intermediate checkpoint to ingest_logs."""
        try:
            conn = self._get_conn()
            now = datetime.now().isoformat()
            conn.execute(
                """INSERT INTO ingest_logs
                   (run_id, phase, step, status, started_at, detail, created_at)
                   VALUES (?, ?, ?, ?, ?, ?, ?)""",
                (self.run_id, _PHASE_ID, step, "checkpoint",
                 getattr(self, '_start_time', now),
                 json.dumps(detail), now)
            )
            conn.commit()
        except Exception:
            pass  # Never crash on checkpoint logging


# ── Pipeline Integration Function ────────────────────────────────────

def run_drive_ingest(cycle_dir=None, dry_run=False, **kwargs) -> dict:
    """Entry point for run_omega_pipeline.py integration.
    Matches the phase runner signature: run_X(cycle_dir, dry_run)."""
    phase = DriveIngestPhase(
        cycle_dir=cycle_dir,
        dry_run=dry_run,
        max_files_per_root=kwargs.get("max_files_per_root", 10000),
        batch_size=kwargs.get("batch_size", 100),
        scan_roots=kwargs.get("scan_roots", None),
    )
    return phase.run()


# ── CLI Entry Point ──────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(
        description="Phase 0.5: Drive Ingestion — scan, dedup, classify, "
                    "extract, atomize"
    )
    parser.add_argument(
        "--dry-run", action="store_true",
        help="Scan only — do not insert into DB"
    )
    parser.add_argument(
        "--max-files", type=int, default=10000,
        help="Max files per scan root (default: 10000)"
    )
    parser.add_argument(
        "--roots", type=str, default=None,
        help="Comma-separated drive letters to scan (e.g., C,D,F)"
    )
    parser.add_argument(
        "--batch-size", type=int, default=100,
        help="Checkpoint batch size (default: 100)"
    )
    parser.add_argument(
        "--cycle-ts", type=str, default=None,
        help="Cycle timestamp for cyclepack dir"
    )
    parser.add_argument(
        "--db", type=str, default=None,
        help="Override database path"
    )
    args = parser.parse_args()

    # Resolve scan roots
    scan_roots = None
    if args.roots:
        letters = [l.strip().upper() for l in args.roots.split(",")]
        scan_roots = {
            k: v for k, v in DRIVE_SCAN_ROOTS.items() if k in letters
        }
        if not scan_roots:
            print(f"[ERROR] No valid roots found for: {args.roots}",
                  file=sys.stderr)
            sys.exit(1)

    cycle_dir = None
    if args.cycle_ts:
        cycle_dir = get_cyclepack_dir(args.cycle_ts)

    phase = DriveIngestPhase(
        db_path=args.db,
        scan_roots=scan_roots,
        max_files_per_root=args.max_files,
        batch_size=args.batch_size,
        dry_run=args.dry_run,
        cycle_dir=cycle_dir,
    )

    result = phase.run()

    # Print summary to stdout (machine-readable)
    print(json.dumps(result, indent=2))
    sys.exit(0 if result.get("errors", 0) == 0 else 1)


if __name__ == "__main__":
    main()
