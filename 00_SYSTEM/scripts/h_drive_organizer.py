#!/usr/bin/env python3
r"""
H: Drive Organizer -- LitigationOS File Reorganization Engine
=============================================================

Inventories, classifies, deduplicates, and reorganizes all files on H:\
into a standardized 20-folder structure.  Designed for 119,000+ files.

Phases:
    --inventory   Phase 1: catalog every file on H:\
    --classify    Phase 2: assign each file to a target folder
    --dedup       Phase 3: find and move duplicates to I:\DEDUP_H_DRIVE\
    --organize    Phase 4: move files into the 20-folder structure
    --verify      Phase 5: post-reorganization integrity check
    --full        Run all phases sequentially

Safety:
    * NO hard deletions -- duplicates move to I:\DEDUP_H_DRIVE\
    * Checkpoint every 5,000 files
    * Full manifest CSV at H:\_INDEX\manifest.csv
    * Detailed log at H:\_INDEX\organizer.log
    * --dry-run available for --dedup, --organize, and --full

Usage:
    python h_drive_organizer.py --inventory
    python h_drive_organizer.py --classify
    python h_drive_organizer.py --dedup --dry-run
    python h_drive_organizer.py --organize --dry-run
    python h_drive_organizer.py --full --dry-run
"""
from __future__ import annotations

# ── UTF-8 stdout/stderr (MUST be before any other import that prints) ───────
import sys, os
sys.stdout = open(sys.stdout.fileno(), mode='w', encoding='utf-8', errors='replace')
sys.stderr = open(sys.stderr.fileno(), mode='w', encoding='utf-8', errors='replace')

# ── CWD safety: never run from repo root (shadow modules) ──────────────────
os.chdir(os.path.dirname(os.path.abspath(__file__)))

# ── Standard library ────────────────────────────────────────────────────────
import argparse
import csv
import datetime
import hashlib
import json
import shutil
import sqlite3
import time
import traceback
from collections import defaultdict
from difflib import SequenceMatcher
from pathlib import Path
from typing import Optional

# ── Optional third-party (graceful fallback) ────────────────────────────────
try:
    import fitz as pymupdf          # PyMuPDF
    HAS_PYMUPDF = True
except ImportError:
    HAS_PYMUPDF = False

try:
    import pdfplumber
    HAS_PDFPLUMBER = True
except ImportError:
    HAS_PDFPLUMBER = False

try:
    from docx import Document as DocxDocument
    HAS_DOCX = True
except ImportError:
    HAS_DOCX = False


# ═══════════════════════════════════════════════════════════════════════════════
# CONSTANTS
# ═══════════════════════════════════════════════════════════════════════════════

H_DRIVE         = Path("H:\\")
I_DRIVE_DEDUP   = Path("I:\\DEDUP_H_DRIVE")
INDEX_DIR       = H_DRIVE / "_INDEX"
MANIFEST_DB     = INDEX_DIR / "organizer.db"
MANIFEST_CSV    = INDEX_DIR / "manifest.csv"
CHECKPOINT_FILE = INDEX_DIR / "checkpoint.json"
LOG_FILE        = INDEX_DIR / "organizer.log"

CHECKPOINT_INTERVAL = 5_000     # save state every N files
PROGRESS_INTERVAL   = 1_000     # print progress every N files
BATCH_SIZE          = 1_000     # DB insert batch size
CONTENT_PEEK_LIMIT  = 5_000     # max chars to read for content classification
SHA256_READ_SIZE    = 1 << 16   # 64 KB blocks for hashing

# Exact-duplicate threshold for content comparison
EXACT_DUP_THRESHOLD = 0.99

# 20 target folders
TARGET_FOLDERS = [
    "01_FILINGS", "02_EVIDENCE", "03_LEGAL_DOCS", "04_CASE_DATA",
    "05_LEGAL_RESEARCH", "06_TRANSCRIPTS", "07_CORRESPONDENCE",
    "08_TEMPLATES", "09_REPORTS", "10_SOURCE_CODE", "11_DOCUMENTATION",
    "12_IMAGES", "13_ARCHIVES", "14_CONFIG", "15_TOOLS", "16_BACKUPS",
    "17_MEDIA", "18_QUARANTINE", "19_MISC", "_INDEX",
]

# ── Extension-based classification map ──────────────────────────────────────
EXTENSION_MAP: dict[str, str] = {
    # 02_EVIDENCE — screenshots / document photos
    '.png':  '02_EVIDENCE', '.jpg':  '02_EVIDENCE', '.jpeg': '02_EVIDENCE',
    '.bmp':  '02_EVIDENCE', '.tiff': '02_EVIDENCE', '.tif':  '02_EVIDENCE',
    '.gif':  '02_EVIDENCE',
    # 04_CASE_DATA — structured data
    '.csv':  '04_CASE_DATA', '.db':     '04_CASE_DATA',
    '.sqlite': '04_CASE_DATA', '.sql':  '04_CASE_DATA',
    '.sqlite3': '04_CASE_DATA',
    # 10_SOURCE_CODE — programming languages & assets
    '.java': '10_SOURCE_CODE', '.js':   '10_SOURCE_CODE',
    '.jsx':  '10_SOURCE_CODE', '.py':   '10_SOURCE_CODE',
    '.ts':   '10_SOURCE_CODE', '.tsx':  '10_SOURCE_CODE',
    '.mts':  '10_SOURCE_CODE', '.c':    '10_SOURCE_CODE',
    '.cpp':  '10_SOURCE_CODE', '.h':    '10_SOURCE_CODE',
    '.hpp':  '10_SOURCE_CODE', '.rs':   '10_SOURCE_CODE',
    '.go':   '10_SOURCE_CODE', '.rb':   '10_SOURCE_CODE',
    '.php':  '10_SOURCE_CODE', '.cs':   '10_SOURCE_CODE',
    '.swift': '10_SOURCE_CODE', '.kt':  '10_SOURCE_CODE',
    '.scala': '10_SOURCE_CODE', '.r':   '10_SOURCE_CODE',
    '.map':  '10_SOURCE_CODE', '.patch': '10_SOURCE_CODE',
    '.css':  '10_SOURCE_CODE', '.scss': '10_SOURCE_CODE',
    '.less': '10_SOURCE_CODE',
    # 11_DOCUMENTATION
    '.md':   '11_DOCUMENTATION', '.txt':  '11_DOCUMENTATION',
    '.rst':  '11_DOCUMENTATION', '.adoc': '11_DOCUMENTATION',
    '.html': '11_DOCUMENTATION', '.htm':  '11_DOCUMENTATION',
    # 12_IMAGES — non-evidence vector/icon assets
    '.svg':  '12_IMAGES', '.ico': '12_IMAGES', '.webp': '12_IMAGES',
    # 13_ARCHIVES
    '.zip':  '13_ARCHIVES', '.tar':  '13_ARCHIVES', '.gz':  '13_ARCHIVES',
    '.7z':   '13_ARCHIVES', '.rar':  '13_ARCHIVES', '.bz2': '13_ARCHIVES',
    '.xz':   '13_ARCHIVES',
    # 14_CONFIG
    '.yaml': '14_CONFIG', '.yml':  '14_CONFIG', '.toml': '14_CONFIG',
    '.ini':  '14_CONFIG', '.env':  '14_CONFIG', '.cfg':  '14_CONFIG',
    '.conf': '14_CONFIG', '.xml':  '14_CONFIG',
    # 15_TOOLS
    '.ps1':  '15_TOOLS', '.sh': '15_TOOLS', '.bat': '15_TOOLS',
    '.cmd':  '15_TOOLS',
    # 17_MEDIA
    '.mp3':  '17_MEDIA', '.wav':  '17_MEDIA', '.mp4':  '17_MEDIA',
    '.avi':  '17_MEDIA', '.mkv':  '17_MEDIA', '.mov':  '17_MEDIA',
    '.flac': '17_MEDIA', '.ogg':  '17_MEDIA', '.wma':  '17_MEDIA',
    '.wmv':  '17_MEDIA',
}

# Path fragments that override extension classification (case-insensitive)
PATH_HEURISTICS: list[tuple[str, str]] = [
    # High-priority overrides first
    ('quarantine',          '18_QUARANTINE'),
    ('safety_snapshot',     '16_BACKUPS'),
    ('litigationos_recycle', '13_ARCHIVES'),
    ('backup',              '16_BACKUPS'),
    # Legal content detection
    ('motion',              '01_FILINGS'),
    ('brief',               '01_FILINGS'),
    ('complaint',           '01_FILINGS'),
    ('order',               '01_FILINGS'),
    ('petition',            '01_FILINGS'),
    ('affidavit',           '03_LEGAL_DOCS'),
    ('declaration',         '03_LEGAL_DOCS'),
    ('contract',            '03_LEGAL_DOCS'),
    ('exhibit',             '02_EVIDENCE'),
    ('transcript',          '06_TRANSCRIPTS'),
    ('deposition',          '06_TRANSCRIPTS'),
    ('template',            '08_TEMPLATES'),
    ('form',                '08_TEMPLATES'),
    ('report',              '09_REPORTS'),
    ('correspondence',      '07_CORRESPONDENCE'),
    ('letter',              '07_CORRESPONDENCE'),
    ('email',               '07_CORRESPONDENCE'),
    ('notice',              '07_CORRESPONDENCE'),
]

# Legal filing keywords used for PDF/DOCX content peeks
FILING_KEYWORDS = [
    'circuit court', 'district court', 'court of appeals',
    'motion to', 'motion for', 'complaint', 'order of the court',
    'order granting', 'order denying', 'judgment', 'summons',
    'plaintiff', 'defendant', 'petitioner', 'respondent',
    'case no', 'file no', 'docket',
]
EVIDENCE_KEYWORDS = ['exhibit', 'evidence', 'attachment', 'bates']
RESEARCH_KEYWORDS = [
    'mcl ', 'mcr ', 'mich comp laws', 'us const', 'usc §',
    'v.', 'supra', 'infra', 'id. at', 'citing',
]


# ═══════════════════════════════════════════════════════════════════════════════
# LOGGING
# ═══════════════════════════════════════════════════════════════════════════════

def log(msg: str, level: str = "INFO") -> None:
    """Dual-output logger: prints to stdout and appends to log file."""
    ts = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    line = f"[{ts}] [{level}] {msg}"
    print(line, flush=True)
    try:
        LOG_FILE.parent.mkdir(parents=True, exist_ok=True)
        with open(LOG_FILE, "a", encoding="utf-8", errors="replace") as f:
            f.write(line + "\n")
    except OSError:
        pass


def fmt_bytes(n: int) -> str:
    """Human-readable byte count."""
    if n < 1024:
        return f"{n} B"
    for unit in ("KB", "MB", "GB", "TB"):
        n /= 1024.0
        if n < 1024:
            return f"{n:,.1f} {unit}"
    return f"{n:,.1f} PB"


# ═══════════════════════════════════════════════════════════════════════════════
# DATABASE
# ═══════════════════════════════════════════════════════════════════════════════

def get_db() -> sqlite3.Connection:
    """Open the manifest database with safe PRAGMAs."""
    INDEX_DIR.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(MANIFEST_DB), timeout=120)
    conn.execute("PRAGMA busy_timeout = 60000")
    conn.execute("PRAGMA journal_mode = WAL")
    conn.execute("PRAGMA cache_size = -32000")
    conn.execute("PRAGMA temp_store = MEMORY")
    conn.execute("PRAGMA synchronous = NORMAL")
    conn.row_factory = sqlite3.Row
    return conn


def init_schema(conn: sqlite3.Connection) -> None:
    """Create tables if they don't exist."""
    conn.executescript("""
        CREATE TABLE IF NOT EXISTS files (
            id              INTEGER PRIMARY KEY AUTOINCREMENT,
            original_path   TEXT NOT NULL UNIQUE,
            file_name       TEXT NOT NULL,
            extension       TEXT NOT NULL DEFAULT '',
            size_bytes      INTEGER NOT NULL DEFAULT 0,
            modified_ts     TEXT NOT NULL DEFAULT '',
            sha256          TEXT DEFAULT '',
            category        TEXT DEFAULT '',
            confidence      TEXT DEFAULT '',
            target_path     TEXT DEFAULT '',
            is_duplicate    INTEGER NOT NULL DEFAULT 0,
            keeper_path     TEXT DEFAULT '',
            dedup_dest      TEXT DEFAULT '',
            action          TEXT NOT NULL DEFAULT '',
            processed       INTEGER NOT NULL DEFAULT 0,
            error           TEXT DEFAULT ''
        );

        CREATE INDEX IF NOT EXISTS idx_files_sha256
            ON files(sha256) WHERE sha256 != '';
        CREATE INDEX IF NOT EXISTS idx_files_size
            ON files(size_bytes);
        CREATE INDEX IF NOT EXISTS idx_files_category
            ON files(category) WHERE category != '';
        CREATE INDEX IF NOT EXISTS idx_files_action
            ON files(action) WHERE action != '';
        CREATE INDEX IF NOT EXISTS idx_files_processed
            ON files(processed);
    """)
    conn.commit()


# ═══════════════════════════════════════════════════════════════════════════════
# CHECKPOINT
# ═══════════════════════════════════════════════════════════════════════════════

def save_checkpoint(phase: str, last_id: int, stats: dict) -> None:
    """Persist progress for resume capability."""
    data = {
        "phase": phase,
        "last_id": last_id,
        "stats": stats,
        "timestamp": datetime.datetime.now().isoformat(),
    }
    CHECKPOINT_FILE.parent.mkdir(parents=True, exist_ok=True)
    tmp = CHECKPOINT_FILE.with_suffix(".tmp")
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)
    tmp.replace(CHECKPOINT_FILE)


def load_checkpoint(phase: str) -> tuple[int, dict]:
    """Load previous checkpoint for the given phase.  Returns (last_id, stats)."""
    if not CHECKPOINT_FILE.exists():
        return 0, {}
    try:
        with open(CHECKPOINT_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
        if data.get("phase") == phase:
            return data.get("last_id", 0), data.get("stats", {})
    except (json.JSONDecodeError, OSError):
        pass
    return 0, {}


# ═══════════════════════════════════════════════════════════════════════════════
# PHASE 1: INVENTORY
# ═══════════════════════════════════════════════════════════════════════════════

def phase_inventory(conn: sqlite3.Connection) -> dict:
    r"""Recursively scan H:\ and insert every file into the database."""
    log("═══ PHASE 1: INVENTORY ═══")

    if not H_DRIVE.exists():
        log("H:\\ drive not found — aborting", "ERROR")
        return {"error": "H:\\ not found"}

    resume_id, prev_stats = load_checkpoint("inventory")
    # Collect already-known paths for fast skip
    known: set[str] = set()
    if resume_id > 0:
        log(f"Resuming from checkpoint (last_id={resume_id})")
        rows = conn.execute("SELECT original_path FROM files").fetchall()
        known = {r["original_path"] for r in rows}

    stats = {
        "total_scanned": prev_stats.get("total_scanned", 0),
        "total_inserted": prev_stats.get("total_inserted", 0),
        "errors": prev_stats.get("errors", 0),
        "total_size": prev_stats.get("total_size", 0),
    }
    batch: list[tuple] = []
    t0 = time.time()

    # Walk using os.scandir for speed
    def _walk(root: str):
        """Yield (full_path_str, file_name, size, mtime_iso) via os.scandir."""
        try:
            with os.scandir(root) as it:
                for entry in it:
                    try:
                        if entry.is_symlink():
                            continue
                        if entry.is_dir(follow_symlinks=False):
                            # Skip our index folder and system dirs
                            low = entry.name.lower()
                            if low in ('$recycle.bin', 'system volume information',
                                       '$windows.~bt', '$windows.~ws'):
                                continue
                            yield from _walk(entry.path)
                        elif entry.is_file(follow_symlinks=False):
                            st = entry.stat(follow_symlinks=False)
                            mtime = datetime.datetime.fromtimestamp(
                                st.st_mtime
                            ).isoformat()
                            yield entry.path, entry.name, st.st_size, mtime
                    except (PermissionError, OSError):
                        stats["errors"] += 1
        except (PermissionError, OSError):
            stats["errors"] += 1

    for fpath, fname, fsize, mtime in _walk(str(H_DRIVE)):
        stats["total_scanned"] += 1

        if fpath in known:
            if stats["total_scanned"] % PROGRESS_INTERVAL == 0:
                log(f"  [INV] {stats['total_scanned']:,} scanned "
                    f"({stats['total_inserted']:,} new, "
                    f"{stats['errors']} err, "
                    f"{time.time()-t0:.0f}s)")
            continue

        ext = Path(fname).suffix.lower()
        batch.append((fpath, fname, ext, fsize, mtime))
        stats["total_inserted"] += 1
        stats["total_size"] += fsize

        if len(batch) >= BATCH_SIZE:
            conn.executemany(
                "INSERT OR IGNORE INTO files "
                "(original_path, file_name, extension, size_bytes, modified_ts) "
                "VALUES (?, ?, ?, ?, ?)",
                batch,
            )
            conn.commit()
            batch.clear()

        if stats["total_scanned"] % PROGRESS_INTERVAL == 0:
            log(f"  [INV] {stats['total_scanned']:,} scanned "
                f"({stats['total_inserted']:,} new, "
                f"{fmt_bytes(stats['total_size'])}, "
                f"{stats['errors']} err, "
                f"{time.time()-t0:.0f}s)")

        if stats["total_scanned"] % CHECKPOINT_INTERVAL == 0:
            if batch:
                conn.executemany(
                    "INSERT OR IGNORE INTO files "
                    "(original_path, file_name, extension, size_bytes, modified_ts) "
                    "VALUES (?, ?, ?, ?, ?)",
                    batch,
                )
                conn.commit()
                batch.clear()
            save_checkpoint("inventory", stats["total_scanned"], stats)

    # Flush remaining batch
    if batch:
        conn.executemany(
            "INSERT OR IGNORE INTO files "
            "(original_path, file_name, extension, size_bytes, modified_ts) "
            "VALUES (?, ?, ?, ?, ?)",
            batch,
        )
        conn.commit()

    elapsed = time.time() - t0
    log(f"  [INV] DONE — {stats['total_scanned']:,} scanned, "
        f"{stats['total_inserted']:,} inserted, "
        f"{fmt_bytes(stats['total_size'])}, "
        f"{stats['errors']} errors, {elapsed:.1f}s")
    save_checkpoint("inventory", stats["total_scanned"], stats)
    return stats


# ═══════════════════════════════════════════════════════════════════════════════
# CONTENT PEEKING (for classification & dedup verification)
# ═══════════════════════════════════════════════════════════════════════════════

def _peek_pdf(filepath: Path) -> str:
    """Extract first-page text from a PDF. Returns empty string on failure."""
    text = ""
    if HAS_PYMUPDF:
        try:
            doc = pymupdf.open(str(filepath))
            if doc.page_count > 0:
                text = doc[0].get_text()[:CONTENT_PEEK_LIMIT]
            doc.close()
            return text
        except Exception:
            pass
    if HAS_PDFPLUMBER:
        try:
            with pdfplumber.open(str(filepath)) as pdf:
                if pdf.pages:
                    text = (pdf.pages[0].extract_text() or "")[:CONTENT_PEEK_LIMIT]
            return text
        except Exception:
            pass
    return ""


def _peek_docx(filepath: Path) -> str:
    """Extract text from a DOCX file. Returns empty string on failure."""
    if HAS_DOCX:
        try:
            doc = DocxDocument(str(filepath))
            paragraphs = [p.text for p in doc.paragraphs[:50]]
            return "\n".join(paragraphs)[:CONTENT_PEEK_LIMIT]
        except Exception:
            pass
    # Fallback: try reading as zip → word/document.xml
    try:
        import zipfile, re
        with zipfile.ZipFile(str(filepath), 'r') as z:
            if 'word/document.xml' in z.namelist():
                raw = z.read('word/document.xml').decode('utf-8', errors='replace')
                text = re.sub(r'<[^>]+>', ' ', raw)
                return text[:CONTENT_PEEK_LIMIT]
    except Exception:
        pass
    return ""


def _peek_text(filepath: Path, max_bytes: int = 8192) -> str:
    """Read initial bytes of a text-like file."""
    for enc in ('utf-8', 'latin-1', 'cp1252'):
        try:
            with open(filepath, 'r', encoding=enc, errors='replace') as f:
                return f.read(max_bytes)
        except Exception:
            continue
    return ""


def _peek_json(filepath: Path) -> Optional[dict]:
    """Try to parse a JSON file and return the top-level object."""
    try:
        with open(filepath, 'r', encoding='utf-8', errors='replace') as f:
            raw = f.read(32_768)  # 32 KB should be enough to determine type
        return json.loads(raw)
    except Exception:
        return None


def peek_content(filepath: Path, ext: str) -> str:
    """Dispatch content peeking by file type. Returns extracted text."""
    if ext == '.pdf':
        return _peek_pdf(filepath)
    elif ext == '.docx':
        return _peek_docx(filepath)
    elif ext in ('.txt', '.md', '.rst', '.html', '.htm', '.adoc'):
        return _peek_text(filepath)
    return ""


# ═══════════════════════════════════════════════════════════════════════════════
# PHASE 2: CLASSIFICATION
# ═══════════════════════════════════════════════════════════════════════════════

def _classify_by_extension(ext: str) -> Optional[tuple[str, str]]:
    """Return (category, confidence) from extension map, or None."""
    cat = EXTENSION_MAP.get(ext)
    if cat:
        return cat, "ext_match"
    return None


def _classify_by_path(original_path: str) -> Optional[tuple[str, str]]:
    """Check path fragments for heuristic overrides."""
    path_lower = original_path.lower()
    for fragment, category in PATH_HEURISTICS:
        if fragment in path_lower:
            return category, f"path_heuristic:{fragment}"
    return None


def _classify_pdf_by_content(filepath: Path) -> tuple[str, str]:
    """Classify a PDF by peeking at its first-page text."""
    text = _peek_pdf(filepath).lower()
    if not text:
        return "03_LEGAL_DOCS", "pdf_no_text"

    # Check for court filing keywords first (highest priority)
    for kw in FILING_KEYWORDS:
        if kw in text:
            return "01_FILINGS", f"pdf_content:{kw}"
    # Evidence
    for kw in EVIDENCE_KEYWORDS:
        if kw in text:
            return "02_EVIDENCE", f"pdf_content:{kw}"
    # Legal research
    for kw in RESEARCH_KEYWORDS:
        if kw in text:
            return "05_LEGAL_RESEARCH", f"pdf_content:{kw}"
    return "03_LEGAL_DOCS", "pdf_content:generic"


def _classify_docx_by_content(filepath: Path) -> tuple[str, str]:
    """Classify a DOCX by peeking at its text."""
    text = _peek_docx(filepath).lower()
    if not text:
        return "03_LEGAL_DOCS", "docx_no_text"

    for kw in FILING_KEYWORDS:
        if kw in text:
            return "01_FILINGS", f"docx_content:{kw}"
    for kw in EVIDENCE_KEYWORDS:
        if kw in text:
            return "02_EVIDENCE", f"docx_content:{kw}"
    for kw in RESEARCH_KEYWORDS:
        if kw in text:
            return "05_LEGAL_RESEARCH", f"docx_content:{kw}"
    return "03_LEGAL_DOCS", "docx_content:generic"


def _classify_json_by_content(filepath: Path) -> tuple[str, str]:
    """Classify a JSON file: config (package.json-like) vs. data."""
    obj = _peek_json(filepath)
    if obj is None:
        return "14_CONFIG", "json_parse_fail"
    if isinstance(obj, dict):
        keys = set(obj.keys())
        # npm / node package patterns
        if keys & {'name', 'version', 'dependencies', 'devDependencies', 'scripts'}:
            return "14_CONFIG", "json_content:package"
        # VS Code / editor settings
        if keys & {'editor.fontSize', 'workbench.colorTheme', 'settings'}:
            return "14_CONFIG", "json_content:vscode"
        # tsconfig, eslint, etc.
        if keys & {'compilerOptions', 'extends', 'rules', 'env'}:
            return "14_CONFIG", "json_content:toolconfig"
        # Legal data patterns
        legal_keys = {'case_number', 'claim_id', 'vehicle_name', 'filing_type',
                      'docket', 'parties', 'evidence'}
        if keys & legal_keys:
            return "04_CASE_DATA", "json_content:legal_data"
    # Arrays of objects → likely data
    if isinstance(obj, list) and len(obj) > 5:
        return "04_CASE_DATA", "json_content:array_data"
    return "14_CONFIG", "json_content:default"


def _classify_txt_by_content(filepath: Path, ext: str) -> Optional[tuple[str, str]]:
    """For .txt and .md files, check if they're actually code or legal docs."""
    text = _peek_text(filepath, max_bytes=4096)
    if not text:
        return None

    # Check for code patterns (override to SOURCE_CODE)
    lines = text.split('\n')
    code_indicators = 0
    for line in lines[:50]:
        stripped = line.strip()
        if any(stripped.startswith(p) for p in
               ('import ', 'from ', 'def ', 'class ', 'function ',
                'const ', 'let ', 'var ', 'public ', 'private ',
                '#include', 'package ', 'using ', '//', '/*')):
            code_indicators += 1
    if code_indicators >= 5:
        return "10_SOURCE_CODE", f"txt_content:code_patterns({code_indicators})"

    # Check for legal content
    text_lower = text.lower()
    for kw in FILING_KEYWORDS:
        if kw in text_lower:
            return "05_LEGAL_RESEARCH", f"txt_content:legal:{kw}"

    return None  # keep default extension classification


def classify_file(
    original_path: str, file_name: str, ext: str
) -> tuple[str, str]:
    """
    Master classifier. Returns (category, confidence_reason).

    Priority order:
        1. Path heuristics (highest — handles quarantine, backups, legal keywords)
        2. Content peek for ambiguous types (.pdf, .docx, .json, .txt)
        3. Extension map (default for unambiguous types)
        4. Fallback to 19_MISC
    """
    # ── 1. Path heuristics override everything ──────────────────────────────
    result = _classify_by_path(original_path)
    if result:
        return result

    # ── 2. Content-based classification for ambiguous types ─────────────────
    filepath = Path(original_path)
    if ext == '.pdf':
        return _classify_pdf_by_content(filepath)
    if ext == '.docx':
        return _classify_docx_by_content(filepath)
    if ext == '.json':
        return _classify_json_by_content(filepath)
    if ext in ('.txt', '.md'):
        content_result = _classify_txt_by_content(filepath, ext)
        if content_result:
            return content_result
        # Fall through to extension map

    # ── 3. Extension map ────────────────────────────────────────────────────
    result = _classify_by_extension(ext)
    if result:
        return result

    # ── 4. Additional extension groups not in the primary map ───────────────
    if ext in ('.docx', '.doc', '.rtf', '.odt'):
        return "03_LEGAL_DOCS", "ext_doc_generic"
    if ext in ('.xlsx', '.xls', '.ods'):
        return "04_CASE_DATA", "ext_spreadsheet"
    if ext in ('.pptx', '.ppt', '.odp'):
        return "11_DOCUMENTATION", "ext_presentation"
    if ext in ('.log',):
        return "09_REPORTS", "ext_log"
    if ext in ('.lock', '.editorconfig', '.gitignore', '.gitattributes',
               '.eslintrc', '.prettierrc', '.babelrc'):
        return "14_CONFIG", "ext_dotfile"
    if ext in ('.whl', '.egg', '.gem', '.jar', '.war', '.class'):
        return "13_ARCHIVES", "ext_package_artifact"
    if ext in ('.exe', '.msi', '.dll', '.so', '.dylib'):
        return "15_TOOLS", "ext_binary"
    if ext in ('.pem', '.crt', '.key', '.cer', '.p12'):
        return "14_CONFIG", "ext_cert"

    # ── 5. Fallback ────────────────────────────────────────────────────────
    return "19_MISC", "unclassified"


def phase_classify(conn: sqlite3.Connection) -> dict:
    """Classify every unclassified file in the database."""
    log("═══ PHASE 2: CLASSIFY ═══")

    total = conn.execute(
        "SELECT COUNT(*) AS c FROM files WHERE category = ''"
    ).fetchone()["c"]

    if total == 0:
        log("  All files already classified.")
        return {"classified": 0}

    log(f"  {total:,} files to classify")
    resume_id, prev_stats = load_checkpoint("classify")
    stats = {
        "classified": prev_stats.get("classified", 0),
        "errors": prev_stats.get("errors", 0),
        "by_category": prev_stats.get("by_category", {}),
    }
    t0 = time.time()

    # Process in pages of BATCH_SIZE
    offset = resume_id
    while True:
        rows = conn.execute(
            "SELECT id, original_path, file_name, extension "
            "FROM files WHERE category = '' ORDER BY id LIMIT ? OFFSET ?",
            (BATCH_SIZE, offset),
        ).fetchall()
        if not rows:
            break

        updates: list[tuple] = []
        for row in rows:
            try:
                cat, conf = classify_file(
                    row["original_path"], row["file_name"], row["extension"]
                )
                target = str(H_DRIVE / cat / row["file_name"])
                updates.append((cat, conf, target, row["id"]))
                stats["by_category"][cat] = stats["by_category"].get(cat, 0) + 1
            except Exception as exc:
                updates.append(("19_MISC", f"error:{exc}", "", row["id"]))
                stats["errors"] += 1

            stats["classified"] += 1

            if stats["classified"] % PROGRESS_INTERVAL == 0:
                log(f"  [CLS] {stats['classified']:,}/{total:,} "
                    f"({stats['errors']} err, {time.time()-t0:.0f}s)")

        conn.executemany(
            "UPDATE files SET category=?, confidence=?, target_path=? WHERE id=?",
            updates,
        )
        conn.commit()
        offset += len(rows)

        if stats["classified"] % CHECKPOINT_INTERVAL == 0:
            save_checkpoint("classify", offset, stats)

    elapsed = time.time() - t0
    log(f"  [CLS] DONE — {stats['classified']:,} classified, "
        f"{stats['errors']} errors, {elapsed:.1f}s")

    # Print distribution
    log("  Category distribution:")
    for cat in sorted(stats["by_category"], key=lambda c: stats["by_category"][c],
                      reverse=True):
        log(f"    {cat:25s}  {stats['by_category'][cat]:>8,}")

    save_checkpoint("classify", offset, stats)
    return stats


# ═══════════════════════════════════════════════════════════════════════════════
# PHASE 3: DEDUPLICATION
# ═══════════════════════════════════════════════════════════════════════════════

def _compute_sha256(filepath: str) -> str:
    """Compute SHA-256 of a file."""
    h = hashlib.sha256()
    try:
        with open(filepath, 'rb') as f:
            while True:
                chunk = f.read(SHA256_READ_SIZE)
                if not chunk:
                    break
                h.update(chunk)
        return h.hexdigest()
    except (PermissionError, OSError):
        return ""


def phase_dedup(conn: sqlite3.Connection, dry_run: bool = False) -> dict:
    r"""
    Content-based deduplication.

    Steps:
        1. Compute SHA-256 for all files (skip if already hashed)
        2. Group by (size, sha256) -> candidate clusters
        3. For PDF/DOCX in same cluster, verify via content peek
        4. Designate keeper (prefer shortest path, then most-recent modified)
        5. Move non-keepers to I:\DEDUP_H_DRIVE\ (or report in dry-run)
    """
    log(f"═══ PHASE 3: DEDUP {'(DRY RUN)' if dry_run else ''} ═══")

    # ── Step 1: Hash files that haven't been hashed yet ─────────────────────
    unhashed = conn.execute(
        "SELECT COUNT(*) AS c FROM files WHERE sha256 = '' AND size_bytes > 0"
    ).fetchone()["c"]
    log(f"  {unhashed:,} files need hashing")

    stats = {
        "hashed": 0, "hash_errors": 0,
        "clusters": 0, "duplicates": 0,
        "bytes_reclaimed": 0, "moved": 0, "move_errors": 0,
    }
    t0 = time.time()

    if unhashed > 0:
        offset = 0
        while True:
            rows = conn.execute(
                "SELECT id, original_path FROM files "
                "WHERE sha256 = '' AND size_bytes > 0 "
                "ORDER BY id LIMIT ?",
                (BATCH_SIZE,),
            ).fetchall()
            if not rows:
                break

            updates: list[tuple] = []
            for row in rows:
                sha = _compute_sha256(row["original_path"])
                if sha:
                    updates.append((sha, row["id"]))
                    stats["hashed"] += 1
                else:
                    updates.append(("ERROR", row["id"]))
                    stats["hash_errors"] += 1

                if (stats["hashed"] + stats["hash_errors"]) % PROGRESS_INTERVAL == 0:
                    log(f"  [HASH] {stats['hashed']:,}/{unhashed:,} "
                        f"({stats['hash_errors']} err, {time.time()-t0:.0f}s)")

            conn.executemany(
                "UPDATE files SET sha256=? WHERE id=?", updates
            )
            conn.commit()

            if (stats["hashed"] + stats["hash_errors"]) % CHECKPOINT_INTERVAL == 0:
                save_checkpoint("dedup_hash", stats["hashed"], stats)

        log(f"  [HASH] DONE — {stats['hashed']:,} hashed, "
            f"{stats['hash_errors']} errors, {time.time()-t0:.1f}s")

    # ── Step 2: Find duplicate clusters ─────────────────────────────────────
    log("  Finding duplicate clusters (size + sha256)...")
    clusters = conn.execute("""
        SELECT size_bytes, sha256, COUNT(*) AS cnt
        FROM files
        WHERE sha256 != '' AND sha256 != 'ERROR' AND size_bytes > 0
        GROUP BY size_bytes, sha256
        HAVING cnt > 1
        ORDER BY size_bytes DESC
    """).fetchall()

    stats["clusters"] = len(clusters)
    log(f"  Found {stats['clusters']:,} duplicate clusters")

    if stats["clusters"] == 0:
        log("  No duplicates found.")
        save_checkpoint("dedup", 0, stats)
        return stats

    # ── Step 3 & 4: Verify and designate keepers ───────────────────────────
    t1 = time.time()
    cluster_num = 0
    dedup_updates: list[tuple] = []  # (is_duplicate, keeper_path, dedup_dest, id)

    for cluster in clusters:
        cluster_num += 1
        members = conn.execute(
            "SELECT id, original_path, file_name, extension, modified_ts "
            "FROM files WHERE size_bytes = ? AND sha256 = ? "
            "ORDER BY LENGTH(original_path) ASC, modified_ts DESC",
            (cluster["size_bytes"], cluster["sha256"]),
        ).fetchall()

        if len(members) < 2:
            continue

        # Content verification for PDF/DOCX (peek inside to confirm true dup)
        verified_groups: list[list[sqlite3.Row]] = []
        peekable_exts = {'.pdf', '.docx'}
        first_ext = members[0]["extension"]

        if first_ext in peekable_exts:
            # Group by actual content similarity
            placed = [False] * len(members)
            for i in range(len(members)):
                if placed[i]:
                    continue
                group = [members[i]]
                placed[i] = True
                text_i = peek_content(
                    Path(members[i]["original_path"]), first_ext
                )
                for j in range(i + 1, len(members)):
                    if placed[j]:
                        continue
                    text_j = peek_content(
                        Path(members[j]["original_path"]), first_ext
                    )
                    if not text_i and not text_j:
                        # Both unreadable — treat as dup by hash
                        group.append(members[j])
                        placed[j] = True
                    elif text_i and text_j:
                        ratio = SequenceMatcher(
                            None, text_i, text_j
                        ).ratio()
                        if ratio >= EXACT_DUP_THRESHOLD:
                            group.append(members[j])
                            placed[j] = True
                if len(group) > 1:
                    verified_groups.append(group)
        else:
            # Non-peekable: trust sha256 completely
            verified_groups.append(list(members))

        # Designate keeper for each verified group
        for group in verified_groups:
            # Keeper: shortest path, then most recent modification
            keeper = group[0]  # already sorted by LENGTH, then modified_ts DESC
            for dup in group[1:]:
                # Compute destination path on I:\
                orig = Path(dup["original_path"])
                try:
                    rel = orig.relative_to(H_DRIVE)
                except ValueError:
                    rel = Path(orig.name)
                dest = I_DRIVE_DEDUP / str(rel)

                dedup_updates.append((
                    1,
                    keeper["original_path"],
                    str(dest),
                    dup["id"],
                ))
                stats["duplicates"] += 1
                stats["bytes_reclaimed"] += cluster["size_bytes"]

        if cluster_num % 500 == 0:
            log(f"  [DEDUP] {cluster_num:,}/{stats['clusters']:,} clusters, "
                f"{stats['duplicates']:,} dups found, "
                f"{fmt_bytes(stats['bytes_reclaimed'])}")

    # Write dedup decisions to DB
    conn.executemany(
        "UPDATE files SET is_duplicate=?, keeper_path=?, dedup_dest=? WHERE id=?",
        dedup_updates,
    )
    conn.commit()
    log(f"  [DEDUP] {stats['duplicates']:,} duplicates identified, "
        f"{fmt_bytes(stats['bytes_reclaimed'])} reclaimable")

    # ── Step 5: Move duplicates (or report) ─────────────────────────────────
    if dry_run:
        log("  DRY RUN — no files moved. Review manifest for planned actions.")
    else:
        log("  Moving duplicates to I:\\DEDUP_H_DRIVE\\...")
        dups = conn.execute(
            "SELECT id, original_path, dedup_dest FROM files "
            "WHERE is_duplicate = 1 AND dedup_dest != '' AND action != 'dedup_moved'"
        ).fetchall()

        move_batch: list[tuple] = []
        for dup in dups:
            src = Path(dup["original_path"])
            dst = Path(dup["dedup_dest"])
            try:
                if not src.exists():
                    move_batch.append(("dedup_missing", dup["id"]))
                    continue
                dst.parent.mkdir(parents=True, exist_ok=True)
                # Handle name collision at destination
                if dst.exists():
                    counter = 1
                    stem = dst.stem
                    suffix = dst.suffix
                    while dst.exists():
                        dst = dst.with_name(f"{stem}_{counter:03d}{suffix}")
                        counter += 1
                shutil.move(str(src), str(dst))
                move_batch.append(("dedup_moved", dup["id"]))
                stats["moved"] += 1
            except Exception as exc:
                move_batch.append((f"dedup_error:{exc}", dup["id"]))
                stats["move_errors"] += 1

            if (stats["moved"] + stats["move_errors"]) % PROGRESS_INTERVAL == 0:
                log(f"  [MOVE] {stats['moved']:,} moved, "
                    f"{stats['move_errors']} errors")

            if len(move_batch) >= BATCH_SIZE:
                conn.executemany(
                    "UPDATE files SET action=? WHERE id=?", move_batch
                )
                conn.commit()
                move_batch.clear()

        if move_batch:
            conn.executemany(
                "UPDATE files SET action=? WHERE id=?", move_batch
            )
            conn.commit()

        log(f"  [MOVE] DONE — {stats['moved']:,} moved, "
            f"{stats['move_errors']} errors")

    save_checkpoint("dedup", 0, stats)
    return stats


# ═══════════════════════════════════════════════════════════════════════════════
# PHASE 4: ORGANIZE
# ═══════════════════════════════════════════════════════════════════════════════

def _unique_target(target: Path) -> Path:
    """If target exists, append _001, _002, etc. until unique."""
    if not target.exists():
        return target
    stem = target.stem
    suffix = target.suffix
    counter = 1
    while True:
        candidate = target.with_name(f"{stem}_{counter:03d}{suffix}")
        if not candidate.exists():
            return candidate
        counter += 1


def phase_organize(conn: sqlite3.Connection, dry_run: bool = False) -> dict:
    """
    Move non-duplicate files into the 20-folder target structure.

    Skips:
        * Files already marked as duplicates (handled in Phase 3)
        * Files already in their target location
        * Files that have already been moved (action='organized')
    """
    log(f"═══ PHASE 4: ORGANIZE {'(DRY RUN)' if dry_run else ''} ═══")

    # Create target folders
    for folder in TARGET_FOLDERS:
        (H_DRIVE / folder).mkdir(parents=True, exist_ok=True)

    # Count work
    to_move = conn.execute(
        "SELECT COUNT(*) AS c FROM files "
        "WHERE is_duplicate = 0 AND category != '' "
        "AND action NOT IN ('organized', 'organize_skipped')"
    ).fetchone()["c"]

    log(f"  {to_move:,} files to organize")
    if to_move == 0:
        return {"moved": 0}

    stats = {
        "moved": 0, "skipped": 0, "errors": 0, "already_in_place": 0,
    }
    t0 = time.time()
    offset = 0

    while True:
        rows = conn.execute(
            "SELECT id, original_path, file_name, category "
            "FROM files "
            "WHERE is_duplicate = 0 AND category != '' "
            "AND action NOT IN ('organized', 'organize_skipped') "
            "ORDER BY id LIMIT ? OFFSET ?",
            (BATCH_SIZE, 0),  # always offset 0 because processed rows change action
        ).fetchall()
        if not rows:
            break

        updates: list[tuple] = []
        for row in rows:
            src = Path(row["original_path"])
            cat = row["category"]
            target_dir = H_DRIVE / cat
            target = target_dir / row["file_name"]

            # Already in target location?
            try:
                if src.parent == target_dir:
                    updates.append(("organize_skipped", str(src), row["id"]))
                    stats["already_in_place"] += 1
                    continue
            except Exception:
                pass

            if dry_run:
                final_target = _unique_target(target)
                updates.append(("organize_planned", str(final_target), row["id"]))
                stats["moved"] += 1
            else:
                try:
                    if not src.exists():
                        updates.append(("organize_missing", "", row["id"]))
                        stats["errors"] += 1
                        continue
                    final_target = _unique_target(target)
                    final_target.parent.mkdir(parents=True, exist_ok=True)
                    shutil.move(str(src), str(final_target))
                    updates.append(("organized", str(final_target), row["id"]))
                    stats["moved"] += 1
                except Exception as exc:
                    updates.append((f"organize_error:{exc}", "", row["id"]))
                    stats["errors"] += 1

            total_done = stats["moved"] + stats["skipped"] + stats["errors"] + stats["already_in_place"]
            if total_done % PROGRESS_INTERVAL == 0:
                log(f"  [ORG] {total_done:,}/{to_move:,} "
                    f"(moved={stats['moved']:,}, skip={stats['already_in_place']:,}, "
                    f"err={stats['errors']}, {time.time()-t0:.0f}s)")

        conn.executemany(
            "UPDATE files SET action=?, target_path=? WHERE id=?", updates
        )
        conn.commit()

        if (stats["moved"] + stats["errors"]) % CHECKPOINT_INTERVAL == 0:
            save_checkpoint("organize", offset, stats)

        offset += len(rows)

    elapsed = time.time() - t0

    # Clean up empty directories left behind
    if not dry_run:
        empty_removed = _remove_empty_dirs(str(H_DRIVE))
        log(f"  Removed {empty_removed} empty directories")

    log(f"  [ORG] DONE — moved={stats['moved']:,}, "
        f"already_in_place={stats['already_in_place']:,}, "
        f"errors={stats['errors']}, {elapsed:.1f}s")
    save_checkpoint("organize", 0, stats)
    return stats


def _remove_empty_dirs(root: str) -> int:
    """Remove empty directories bottom-up. Returns count removed."""
    removed = 0
    for dirpath, dirnames, filenames in os.walk(root, topdown=False):
        # Don't remove target folders or _INDEX
        dp = Path(dirpath)
        if dp == Path(root):
            continue
        if dp.name in TARGET_FOLDERS:
            continue
        try:
            if not filenames and not dirnames:
                os.rmdir(dirpath)
                removed += 1
        except OSError:
            pass
    return removed


# ═══════════════════════════════════════════════════════════════════════════════
# PHASE 5: VERIFY
# ═══════════════════════════════════════════════════════════════════════════════

def phase_verify(conn: sqlite3.Connection) -> dict:
    """Post-reorganization integrity verification."""
    log("═══ PHASE 5: VERIFY ═══")
    t0 = time.time()

    stats = {
        "total_files": 0,
        "verified_ok": 0,
        "missing": 0,
        "size_mismatch": 0,
        "errors": 0,
        "by_category": {},
    }

    # Verify organized files exist at their target paths
    rows = conn.execute(
        "SELECT id, original_path, target_path, file_name, size_bytes, "
        "       category, action "
        "FROM files WHERE action IN ('organized', 'organize_skipped')"
    ).fetchall()

    stats["total_files"] = len(rows)
    log(f"  Verifying {stats['total_files']:,} organized files...")

    for row in rows:
        target = row["target_path"] or row["original_path"]
        p = Path(target)
        try:
            if p.exists():
                actual_size = p.stat().st_size
                if actual_size == row["size_bytes"]:
                    stats["verified_ok"] += 1
                else:
                    stats["size_mismatch"] += 1
                    log(f"  SIZE MISMATCH: {target} "
                        f"(expected {row['size_bytes']}, got {actual_size})",
                        "WARN")
            else:
                stats["missing"] += 1
                if stats["missing"] <= 50:  # limit log noise
                    log(f"  MISSING: {target}", "WARN")
        except Exception as exc:
            stats["errors"] += 1
            log(f"  ERROR verifying {target}: {exc}", "ERROR")

        cat = row["category"]
        stats["by_category"][cat] = stats["by_category"].get(cat, 0) + 1

    # Verify duplicates were actually moved
    dup_rows = conn.execute(
        "SELECT original_path, dedup_dest FROM files "
        "WHERE action = 'dedup_moved'"
    ).fetchall()

    dup_ok = 0
    dup_missing = 0
    for dr in dup_rows:
        if Path(dr["dedup_dest"]).exists():
            dup_ok += 1
        else:
            dup_missing += 1

    # Walk actual filesystem to find orphans (files not in manifest)
    log("  Scanning for orphan files not in manifest...")
    known_paths: set[str] = set()
    for row in conn.execute("SELECT original_path, target_path FROM files").fetchall():
        known_paths.add(row["original_path"])
        if row["target_path"]:
            known_paths.add(row["target_path"])

    orphans = 0
    for dirpath, _, filenames in os.walk(str(H_DRIVE)):
        for fn in filenames:
            fp = os.path.join(dirpath, fn)
            if fp not in known_paths:
                orphans += 1
    stats["orphans"] = orphans

    elapsed = time.time() - t0
    log("  ── Verification Results ──")
    log(f"  Organized files verified OK : {stats['verified_ok']:,}")
    log(f"  Missing from target         : {stats['missing']:,}")
    log(f"  Size mismatches             : {stats['size_mismatch']:,}")
    log(f"  Verify errors               : {stats['errors']:,}")
    log(f"  Dedup moved OK              : {dup_ok:,}")
    log(f"  Dedup moved missing         : {dup_missing:,}")
    log(f"  Orphan files (not in manifest): {orphans:,}")
    log(f"  Elapsed: {elapsed:.1f}s")

    log("  Files per category:")
    for cat in sorted(stats["by_category"],
                      key=lambda c: stats["by_category"][c], reverse=True):
        log(f"    {cat:25s}  {stats['by_category'][cat]:>8,}")

    # Pass/fail
    if stats["missing"] == 0 and stats["size_mismatch"] == 0:
        log("  ✓ VERIFICATION PASSED", "INFO")
    else:
        log(f"  ✗ VERIFICATION FAILED — "
            f"{stats['missing']} missing, {stats['size_mismatch']} mismatches",
            "WARN")

    save_checkpoint("verify", 0, stats)
    return stats


# ═══════════════════════════════════════════════════════════════════════════════
# MANIFEST EXPORT
# ═══════════════════════════════════════════════════════════════════════════════

def export_manifest_csv(conn: sqlite3.Connection) -> None:
    """Export the full manifest to CSV."""
    log("Exporting manifest CSV...")
    MANIFEST_CSV.parent.mkdir(parents=True, exist_ok=True)

    rows = conn.execute(
        "SELECT original_path, target_path, category, confidence, "
        "       size_bytes, sha256, is_duplicate, keeper_path, action "
        "FROM files ORDER BY category, original_path"
    ).fetchall()

    with open(MANIFEST_CSV, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow([
            "original_path", "target_path", "category", "confidence",
            "file_size", "sha256", "is_duplicate", "keeper_path", "action",
        ])
        for row in rows:
            writer.writerow([
                row["original_path"], row["target_path"],
                row["category"], row["confidence"],
                row["size_bytes"], row["sha256"],
                row["is_duplicate"], row["keeper_path"],
                row["action"],
            ])

    log(f"  Manifest written: {MANIFEST_CSV}  ({len(rows):,} rows)")


# ═══════════════════════════════════════════════════════════════════════════════
# SUMMARY REPORT
# ═══════════════════════════════════════════════════════════════════════════════

def print_summary(conn: sqlite3.Connection) -> None:
    """Print a final summary of the database state."""
    row = conn.execute("""
        SELECT
            (SELECT COUNT(*) FROM files) AS total,
            (SELECT COUNT(*) FROM files WHERE category != '') AS classified,
            (SELECT COUNT(*) FROM files WHERE sha256 != '' AND sha256 != 'ERROR') AS hashed,
            (SELECT COUNT(*) FROM files WHERE is_duplicate = 1) AS duplicates,
            (SELECT COUNT(*) FROM files WHERE action = 'organized') AS organized,
            (SELECT COUNT(*) FROM files WHERE action = 'dedup_moved') AS dedup_moved,
            (SELECT SUM(size_bytes) FROM files) AS total_bytes,
            (SELECT SUM(size_bytes) FROM files WHERE is_duplicate = 1) AS dup_bytes
    """).fetchone()

    log("═══════════════════════════════════════════════════════")
    log("  H: DRIVE ORGANIZER — SUMMARY")
    log("═══════════════════════════════════════════════════════")
    log(f"  Total files in DB       : {row['total']:>10,}")
    log(f"  Classified              : {row['classified']:>10,}")
    log(f"  SHA-256 hashed          : {row['hashed']:>10,}")
    log(f"  Duplicates found        : {row['duplicates']:>10,}")
    log(f"  Organized (moved)       : {row['organized']:>10,}")
    log(f"  Dedup moved to I:\\      : {row['dedup_moved']:>10,}")
    log(f"  Total size              : {fmt_bytes(row['total_bytes'] or 0):>10}")
    log(f"  Duplicate size          : {fmt_bytes(row['dup_bytes'] or 0):>10}")
    log("═══════════════════════════════════════════════════════")

    # Category breakdown
    cats = conn.execute(
        "SELECT category, COUNT(*) AS cnt, SUM(size_bytes) AS sz "
        "FROM files WHERE category != '' "
        "GROUP BY category ORDER BY cnt DESC"
    ).fetchall()
    if cats:
        log("  Category Breakdown:")
        for c in cats:
            log(f"    {c['category']:25s}  {c['cnt']:>8,} files  "
                f"{fmt_bytes(c['sz'] or 0):>10}")


# ═══════════════════════════════════════════════════════════════════════════════
# CLI
# ═══════════════════════════════════════════════════════════════════════════════

def main() -> None:
    parser = argparse.ArgumentParser(
        description="H: Drive Organizer — LitigationOS File Reorganization Engine",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python h_drive_organizer.py --inventory          # Phase 1: catalog all files
  python h_drive_organizer.py --classify           # Phase 2: classify into categories
  python h_drive_organizer.py --dedup --dry-run    # Phase 3: find duplicates (preview)
  python h_drive_organizer.py --dedup              # Phase 3: move duplicates to I:\\
  python h_drive_organizer.py --organize --dry-run # Phase 4: preview reorganization
  python h_drive_organizer.py --organize           # Phase 4: execute reorganization
  python h_drive_organizer.py --verify             # Phase 5: integrity check
  python h_drive_organizer.py --full               # All phases sequentially
  python h_drive_organizer.py --summary            # Print current DB summary
  python h_drive_organizer.py --export-csv         # Export manifest CSV
        """,
    )
    parser.add_argument("--inventory",  action="store_true", help="Phase 1: catalog all files")
    parser.add_argument("--classify",   action="store_true", help="Phase 2: classify files")
    parser.add_argument("--dedup",      action="store_true", help="Phase 3: deduplicate")
    parser.add_argument("--organize",   action="store_true", help="Phase 4: move to target folders")
    parser.add_argument("--verify",     action="store_true", help="Phase 5: verify integrity")
    parser.add_argument("--full",       action="store_true", help="Run all phases")
    parser.add_argument("--summary",    action="store_true", help="Print DB summary")
    parser.add_argument("--export-csv", action="store_true", help="Export manifest.csv")
    parser.add_argument("--dry-run",    action="store_true",
                        help="Preview changes without moving files (dedup/organize)")

    args = parser.parse_args()

    # Must select at least one action
    if not any([args.inventory, args.classify, args.dedup, args.organize,
                args.verify, args.full, args.summary, args.export_csv]):
        parser.print_help()
        sys.exit(1)

    log("=" * 60)
    log(f"H: Drive Organizer started — {datetime.datetime.now().isoformat()}")
    log(f"  H:\\ target:     {H_DRIVE}")
    log(f"  Dedup dest:     {I_DRIVE_DEDUP}")
    log(f"  Index dir:      {INDEX_DIR}")
    log(f"  Manifest DB:    {MANIFEST_DB}")
    log(f"  Dry run:        {args.dry_run}")
    log(f"  PyMuPDF:        {'yes' if HAS_PYMUPDF else 'no'}")
    log(f"  pdfplumber:     {'yes' if HAS_PDFPLUMBER else 'no'}")
    log(f"  python-docx:    {'yes' if HAS_DOCX else 'no'}")
    log("=" * 60)

    conn = get_db()
    init_schema(conn)

    try:
        if args.full:
            phase_inventory(conn)
            phase_classify(conn)
            phase_dedup(conn, dry_run=args.dry_run)
            phase_organize(conn, dry_run=args.dry_run)
            if not args.dry_run:
                phase_verify(conn)
            export_manifest_csv(conn)
            print_summary(conn)
        else:
            if args.inventory:
                phase_inventory(conn)
            if args.classify:
                phase_classify(conn)
            if args.dedup:
                phase_dedup(conn, dry_run=args.dry_run)
            if args.organize:
                phase_organize(conn, dry_run=args.dry_run)
            if args.verify:
                phase_verify(conn)
            if args.export_csv:
                export_manifest_csv(conn)
            if args.summary:
                print_summary(conn)
    except KeyboardInterrupt:
        log("Interrupted by user — progress saved in checkpoint.", "WARN")
    except Exception as exc:
        log(f"FATAL: {exc}", "ERROR")
        log(traceback.format_exc(), "ERROR")
        sys.exit(1)
    finally:
        conn.close()

    log("Done.")


if __name__ == "__main__":
    main()
