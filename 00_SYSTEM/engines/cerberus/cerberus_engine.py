#!/usr/bin/env python3
"""CERBERUS Evidence Guardian Engine v1.0

Complete Evidence Recovery, Binding, Extraction, Routing, and Utilization System.

Solves the core problem: 996,000+ files scattered across 6 drives, most unprocessed,
with unknown legal value. CERBERUS scans, extracts, classifies, and weaponizes evidence
for the Pigors v. Watson litigation system.

Usage:
    python cerberus_engine.py scan <directory> [--recursive] [--extensions pdf,docx,txt]
    python cerberus_engine.py extract <path> [--limit N]
    python cerberus_engine.py classify <file> [--lane A|B|C|D|E|F]
    python cerberus_engine.py weapons [--min-severity 5]
    python cerberus_engine.py gaps [--lane A]
    python cerberus_engine.py report [--output json|md]
    python cerberus_engine.py status
"""

import sys
import os
import io
import re
import json
import csv
import sqlite3
import hashlib
import argparse
import logging
from pathlib import Path
from datetime import datetime, timezone
from contextlib import contextmanager
from dataclasses import dataclass, field, asdict
from typing import Optional

# Force UTF-8 stdout to prevent encoding crashes on Windows
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8", errors="replace")

logger = logging.getLogger("cerberus")

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

DB_PATH = r"C:\Users\andre\LitigationOS\litigation_context.db"
DRIVES = [
    r"C:\Users\andre\LitigationOS",
    r"F:\\",
    r"G:\\",
    r"H:\\",
    r"I:\\",
    r"J:\\",
]

# MEEK signal patterns — sourced from pipeline/config.py
MEEK_SIGNALS = {
    "E": re.compile(
        r"bias|JTC|disqualif|MCR\s+2\.003|canon|judicial[\s\-_]?misconduct|superintend",
        re.IGNORECASE,
    ),
    "D": re.compile(
        r"PPO|protection[\s\-_]?order|contempt|MCL\s+600\.2950|MCR\s+3\.70[678]|bond|restrain",
        re.IGNORECASE,
    ),
    "F": re.compile(
        r"appell|COA|MSC|MCR\s+7\.|leave[\s\-_]?to[\s\-_]?appeal|standard[\s\-_]?of[\s\-_]?review"
        r"|de[\s\-_]?novo|abuse[\s\-_]?of[\s\-_]?discretion|366810",
        re.IGNORECASE,
    ),
    "A": re.compile(
        r"custody|parenting|FOC|child|MCL\s+722|MCR\s+3\.20[67]|MCR\s+3\.210"
        r"|best[\s\-_]?interest|factor\s+[a-l]|L\.?D\.?W\.?|visitation",
        re.IGNORECASE,
    ),
    "B": re.compile(
        r"shady[\s\-_]?oaks|homes[\s\-_]?of[\s\-_]?america|alden[\s\-_]?global"
        r"|habitability|landlord|tenant|MCL\s+554|rent|mobile[\s\-_]?home|park"
        r"|eviction|housing|property|title",
        re.IGNORECASE,
    ),
}
# Lane C (Convergence) assigned when 2+ lanes match
LANE_PRIORITY = ["E", "D", "F", "A", "B"]

LANE_NAMES = {
    "A": "Watson / Custody",
    "B": "Shady Oaks / Housing",
    "C": "Convergence (multi-lane)",
    "D": "PPO / Protection Orders",
    "E": "Judicial Misconduct / JTC",
    "F": "Appellate (COA/MSC)",
}

# File extensions we process, grouped by category
EXT_CATEGORIES = {
    "pdf": "document",
    "docx": "document",
    "doc": "document",
    "txt": "text",
    "md": "text",
    "json": "structured",
    "jsonl": "structured",
    "csv": "structured",
    "tsv": "structured",
    "jpg": "image",
    "jpeg": "image",
    "png": "image",
    "tiff": "image",
    "tif": "image",
    "bmp": "image",
    "gif": "image",
    "mp3": "audio",
    "wav": "audio",
    "m4a": "audio",
    "mp4": "video",
    "avi": "video",
    "mov": "video",
    "eml": "email",
    "msg": "email",
    "mbox": "email",
    "html": "web",
    "htm": "web",
    "xlsx": "spreadsheet",
    "xls": "spreadsheet",
}

# Weapon detection patterns — severity 1-10
WEAPON_PATTERNS = {
    "admission": {
        "pattern": re.compile(
            r"I\s+did|I\s+admit|we\s+planned\s+to|I\s+made\s+that\s+up|I\s+lied"
            r"|that\s+was\s+false|I\s+knew\s+it\s+was\s+wrong|I\s+fabricated",
            re.IGNORECASE,
        ),
        "severity": 9,
    },
    "threat": {
        "pattern": re.compile(
            r"I\s+will\s+make\s+sure|you'?ll\s+never\s+see|I'?ll\s+destroy"
            r"|I\s+will\s+ruin|you'?ll\s+pay|I\s+will\s+take\s+(him|her|them|the\s+kid)",
            re.IGNORECASE,
        ),
        "severity": 8,
    },
    "contradiction": {
        "pattern": re.compile(
            r"I\s+never\s+said\s+that|that'?s\s+not\s+what\s+(happened|I\s+said)"
            r"|I\s+don'?t\s+recall|I\s+didn'?t\s+mean",
            re.IGNORECASE,
        ),
        "severity": 7,
    },
    "order_violation": {
        "pattern": re.compile(
            r"despite\s+(the\s+)?court\s+order|in\s+violation\s+of|violated\s+(the\s+)?order"
            r"|failed\s+to\s+comply|refused\s+to\s+(follow|obey|comply)"
            r"|willful(ly)?\s+(violat|disregard|ignor)",
            re.IGNORECASE,
        ),
        "severity": 8,
    },
    "police_report": {
        "pattern": re.compile(
            r"victim|offender|incident\s+report|responding\s+officer|dispatch"
            r"|complainant|law\s+enforcement|arrested|domestic\s+(violence|assault)",
            re.IGNORECASE,
        ),
        "severity": 6,
    },
    "alienation": {
        "pattern": re.compile(
            r"turned?\s+(him|her|the\s+child)\s+against|bad[\s\-]?mouth"
            r"|refuses?\s+to\s+let\s+(him|her)|withholding\s+(parenting|visitation)"
            r"|parental\s+alienat",
            re.IGNORECASE,
        ),
        "severity": 7,
    },
    "perjury_indicator": {
        "pattern": re.compile(
            r"under\s+oath.{0,40}(false|untrue|lie)|false\s+(statement|testimony|affidavit)"
            r"|perjur|sworn.{0,30}(false|fabricat)",
            re.IGNORECASE,
        ),
        "severity": 10,
    },
    "financial_fraud": {
        "pattern": re.compile(
            r"hid(den)?\s+(asset|income|money)|undisclosed\s+(income|account)"
            r"|dissipat(ed|ing)\s+(marital\s+)?asset|fraudulent\s+transfer",
            re.IGNORECASE,
        ),
        "severity": 8,
    },
}

# Litigation relevance keywords (broad net)
RELEVANCE_KEYWORDS = re.compile(
    r"custody|court|judge|order|motion|hearing|attorney|lawyer|filed|docket"
    r"|parenting|visitation|child|PPO|protection|contempt|appeal|evidence"
    r"|testimony|affidavit|sworn|deposition|subpoena|exhibit|plaintiff|defendant"
    r"|Watson|Pigors|McNeill|Shady\s+Oaks|FOC|Rusco|Barnes"
    r"|MCL|MCR|statute|violation|complaint|petition",
    re.IGNORECASE,
)


# ---------------------------------------------------------------------------
# Data Models
# ---------------------------------------------------------------------------


@dataclass
class FileRecord:
    path: str
    filename: str
    extension: str
    category: str
    size_bytes: int
    modified_iso: str
    sha256: str = ""
    relevance_score: float = 0.0
    scanned_at: str = ""


@dataclass
class Extraction:
    file_path: str
    content_preview: str  # first 2000 chars
    content_length: int
    encoding: str = "utf-8"
    extraction_method: str = ""
    extracted_at: str = ""
    error: str = ""


@dataclass
class Weapon:
    file_path: str
    weapon_type: str
    matched_text: str
    severity: int
    context: str  # surrounding text
    lane: str = ""
    detected_at: str = ""


@dataclass
class Gap:
    lane: str
    gap_type: str  # date_gap, claim_gap, evidence_gap
    description: str
    severity: int  # 1-10
    suggestion: str = ""
    detected_at: str = ""


# ---------------------------------------------------------------------------
# Database Layer
# ---------------------------------------------------------------------------

SCHEMA_SQL = """
CREATE TABLE IF NOT EXISTS cerberus_inventory (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    path TEXT UNIQUE NOT NULL,
    filename TEXT NOT NULL,
    extension TEXT,
    category TEXT,
    size_bytes INTEGER,
    modified_iso TEXT,
    sha256 TEXT,
    relevance_score REAL DEFAULT 0.0,
    scanned_at TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_cerberus_inv_ext ON cerberus_inventory(extension);
CREATE INDEX IF NOT EXISTS idx_cerberus_inv_cat ON cerberus_inventory(category);
CREATE INDEX IF NOT EXISTS idx_cerberus_inv_relevance ON cerberus_inventory(relevance_score);

CREATE TABLE IF NOT EXISTS cerberus_extractions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    file_path TEXT NOT NULL,
    content_preview TEXT,
    content_length INTEGER,
    encoding TEXT,
    extraction_method TEXT,
    extracted_at TEXT NOT NULL,
    error TEXT,
    FOREIGN KEY (file_path) REFERENCES cerberus_inventory(path)
);
CREATE INDEX IF NOT EXISTS idx_cerberus_ext_path ON cerberus_extractions(file_path);

CREATE TABLE IF NOT EXISTS cerberus_lanes (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    file_path TEXT NOT NULL,
    lane TEXT NOT NULL,
    confidence REAL DEFAULT 0.0,
    matched_signals TEXT,
    classified_at TEXT NOT NULL,
    FOREIGN KEY (file_path) REFERENCES cerberus_inventory(path)
);
CREATE INDEX IF NOT EXISTS idx_cerberus_lanes_lane ON cerberus_lanes(lane);

CREATE TABLE IF NOT EXISTS cerberus_weapons (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    file_path TEXT NOT NULL,
    weapon_type TEXT NOT NULL,
    matched_text TEXT,
    severity INTEGER DEFAULT 0,
    context TEXT,
    lane TEXT,
    detected_at TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_cerberus_weap_sev ON cerberus_weapons(severity);
CREATE INDEX IF NOT EXISTS idx_cerberus_weap_type ON cerberus_weapons(weapon_type);

CREATE TABLE IF NOT EXISTS cerberus_gaps (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    lane TEXT NOT NULL,
    gap_type TEXT NOT NULL,
    description TEXT,
    severity INTEGER DEFAULT 0,
    suggestion TEXT,
    detected_at TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_cerberus_gaps_lane ON cerberus_gaps(lane);
"""


@contextmanager
def _db(db_path: str = DB_PATH, readonly: bool = False):
    """Open a SQLite connection with LitigationOS-standard PRAGMAs."""
    conn = sqlite3.connect(db_path, timeout=60)
    conn.row_factory = sqlite3.Row
    try:
        conn.execute("PRAGMA busy_timeout = 60000")
        conn.execute("PRAGMA journal_mode = WAL")
        conn.execute("PRAGMA cache_size = -32000")
        conn.execute("PRAGMA temp_store = MEMORY")
        conn.execute("PRAGMA synchronous = NORMAL")
        if readonly:
            conn.execute("PRAGMA query_only = ON")
        yield conn
        if not readonly:
            conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _sha256(path: str, chunk_size: int = 65536) -> str:
    """Compute SHA-256 of a file. Returns empty string on error."""
    h = hashlib.sha256()
    try:
        with open(path, "rb") as f:
            while True:
                chunk = f.read(chunk_size)
                if not chunk:
                    break
                h.update(chunk)
        return h.hexdigest()
    except (OSError, PermissionError):
        return ""


# ---------------------------------------------------------------------------
# CerberusEngine
# ---------------------------------------------------------------------------


class CerberusEngine:
    """Core engine: scan → extract → classify → weaponize → gap-analyze."""

    def __init__(self, db_path: str = DB_PATH):
        self.db_path = db_path
        self._ensure_schema()
        logger.info("CERBERUS engine initialized — DB: %s", db_path)

    def _ensure_schema(self) -> None:
        with _db(self.db_path) as conn:
            conn.executescript(SCHEMA_SQL)

    # ------------------------------------------------------------------
    # 1. Drive Scanner
    # ------------------------------------------------------------------

    def scan(
        self,
        directory: str,
        recursive: bool = True,
        extensions: Optional[list[str]] = None,
    ) -> int:
        """Scan a directory for litigation-relevant files. Returns count of files inventoried."""
        directory = os.path.abspath(directory)
        if not os.path.isdir(directory):
            raise FileNotFoundError(f"Directory not found: {directory}")

        allowed_exts = {e.lower().lstrip(".") for e in extensions} if extensions else set(EXT_CATEGORIES.keys())
        records: list[tuple] = []
        skipped = 0

        walker = os.walk(directory) if recursive else [(directory, [], os.listdir(directory))]
        for root, _dirs, files in walker:
            for fname in files:
                ext = Path(fname).suffix.lower().lstrip(".")
                if ext not in allowed_exts:
                    skipped += 1
                    continue
                fpath = os.path.join(root, fname)
                try:
                    stat = os.stat(fpath)
                except (OSError, PermissionError):
                    skipped += 1
                    continue

                category = EXT_CATEGORIES.get(ext, "other")
                modified = datetime.fromtimestamp(stat.st_mtime, tz=timezone.utc).isoformat()

                # Quick relevance check on filename
                rel = 1.0 if RELEVANCE_KEYWORDS.search(fname) else 0.0
                records.append((
                    fpath, fname, ext, category, stat.st_size,
                    modified, "", rel, _now(),
                ))

        with _db(self.db_path) as conn:
            conn.executemany(
                """INSERT OR REPLACE INTO cerberus_inventory
                   (path, filename, extension, category, size_bytes,
                    modified_iso, sha256, relevance_score, scanned_at)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                records,
            )

        logger.info("Scanned %s — %d files inventoried, %d skipped", directory, len(records), skipped)
        return len(records)

    # ------------------------------------------------------------------
    # 2. Content Extractor
    # ------------------------------------------------------------------

    def extract(self, path: str, limit: int = 0) -> int:
        """Extract text content from file(s). Returns count of extractions."""
        path = os.path.abspath(path)
        if os.path.isfile(path):
            targets = [path]
        elif os.path.isdir(path):
            with _db(self.db_path, readonly=True) as conn:
                rows = conn.execute(
                    "SELECT path FROM cerberus_inventory WHERE path LIKE ? AND category IN ('document','text','structured')",
                    (path + "%",),
                ).fetchall()
                targets = [r["path"] for r in rows]
        else:
            raise FileNotFoundError(f"Path not found: {path}")

        if limit > 0:
            targets = targets[:limit]

        extractions: list[tuple] = []
        for fpath in targets:
            ext = Path(fpath).suffix.lower().lstrip(".")
            content, method, error = "", "", ""
            try:
                if ext == "pdf":
                    content, method = self._extract_pdf(fpath)
                elif ext in ("docx", "doc"):
                    content, method = self._extract_docx(fpath)
                elif ext in ("txt", "md", "html", "htm", "eml"):
                    content, method = self._extract_text(fpath)
                elif ext in ("json", "jsonl"):
                    content, method = self._extract_json(fpath)
                elif ext in ("csv", "tsv"):
                    content, method = self._extract_csv(fpath)
                else:
                    method = "skipped"
                    error = f"No extractor for .{ext}"
            except Exception as exc:
                error = str(exc)[:500]
                method = "error"

            preview = content[:2000] if content else ""

            # Update relevance score based on content
            rel = self._score_relevance(content) if content else 0.0
            extractions.append((fpath, preview, len(content), "utf-8", method, _now(), error))

            if rel > 0:
                with _db(self.db_path) as conn:
                    conn.execute(
                        "UPDATE cerberus_inventory SET relevance_score = MAX(relevance_score, ?) WHERE path = ?",
                        (rel, fpath),
                    )

        with _db(self.db_path) as conn:
            conn.executemany(
                """INSERT INTO cerberus_extractions
                   (file_path, content_preview, content_length, encoding,
                    extraction_method, extracted_at, error)
                   VALUES (?, ?, ?, ?, ?, ?, ?)""",
                extractions,
            )

        logger.info("Extracted %d files from %s", len(extractions), path)
        return len(extractions)

    def _extract_pdf(self, path: str) -> tuple[str, str]:
        try:
            import fitz
        except ImportError:
            return "", "fitz_unavailable"
        text_parts = []
        with fitz.open(path) as doc:
            for page in doc:
                text_parts.append(page.get_text("text"))
        text = "\n".join(text_parts).strip()
        if not text:
            return "", "pdf_image_only_needs_ocr"
        return text, "pymupdf"

    def _extract_docx(self, path: str) -> tuple[str, str]:
        try:
            from docx import Document
        except ImportError:
            return "", "docx_unavailable"
        doc = Document(path)
        text = "\n".join(p.text for p in doc.paragraphs if p.text.strip())
        return text, "python-docx"

    def _extract_text(self, path: str) -> tuple[str, str]:
        for enc in ("utf-8", "utf-16", "latin-1", "cp1252"):
            try:
                with open(path, "r", encoding=enc, errors="replace") as f:
                    return f.read(), f"text_{enc}"
            except (UnicodeError, OSError):
                continue
        return "", "text_failed"

    def _extract_json(self, path: str) -> tuple[str, str]:
        with open(path, "r", encoding="utf-8", errors="replace") as f:
            raw = f.read()
        try:
            data = json.loads(raw)
            return json.dumps(data, indent=2, default=str)[:50000], "json_parsed"
        except json.JSONDecodeError:
            return raw[:50000], "json_raw"

    def _extract_csv(self, path: str) -> tuple[str, str]:
        lines = []
        with open(path, "r", encoding="utf-8", errors="replace", newline="") as f:
            reader = csv.reader(f)
            for i, row in enumerate(reader):
                lines.append(" | ".join(row))
                if i > 200:
                    lines.append(f"... (truncated at 200 rows)")
                    break
        return "\n".join(lines), "csv_parsed"

    def _score_relevance(self, text: str) -> float:
        """Score 0.0-1.0 based on litigation keyword density."""
        if not text:
            return 0.0
        matches = RELEVANCE_KEYWORDS.findall(text[:10000])
        word_count = max(len(text[:10000].split()), 1)
        density = len(matches) / word_count
        # Scale: 0 matches=0, 1+=0.1, density>0.01=0.5, density>0.05=0.9
        if not matches:
            return 0.0
        if density > 0.05:
            return min(0.95, 0.5 + density * 5)
        if density > 0.01:
            return 0.3 + density * 20
        return min(0.3, len(matches) * 0.05)

    # ------------------------------------------------------------------
    # 3. Evidence Classifier (Lane Router)
    # ------------------------------------------------------------------

    def classify(self, file_path: str, force_lane: Optional[str] = None) -> str:
        """Classify a file into a case lane. Returns lane letter."""
        file_path = os.path.abspath(file_path)

        if force_lane and force_lane.upper() in LANE_NAMES:
            lane = force_lane.upper()
            with _db(self.db_path) as conn:
                conn.execute(
                    "INSERT INTO cerberus_lanes (file_path, lane, confidence, matched_signals, classified_at) VALUES (?, ?, ?, ?, ?)",
                    (file_path, lane, 1.0, "manual_override", _now()),
                )
            return lane

        # Get extracted content
        text = ""
        with _db(self.db_path, readonly=True) as conn:
            row = conn.execute(
                "SELECT content_preview FROM cerberus_extractions WHERE file_path = ? ORDER BY id DESC LIMIT 1",
                (file_path,),
            ).fetchone()
            if row:
                text = row["content_preview"] or ""

        # Also use filename for classification
        text = f"{os.path.basename(file_path)} {text}"
        return self._classify_text(file_path, text)

    def _classify_text(self, file_path: str, text: str) -> str:
        """Apply MEEK signals with priority E → D → F → A → B. Multi-match → C."""
        matched_lanes = []
        match_details = {}

        for lane in LANE_PRIORITY:
            pattern = MEEK_SIGNALS[lane]
            hits = pattern.findall(text[:5000])
            if hits:
                matched_lanes.append(lane)
                match_details[lane] = hits[:5]

        if not matched_lanes:
            lane = "A"  # default to custody (primary case)
            confidence = 0.1
            signals = "no_match_default"
        elif len(matched_lanes) >= 2:
            lane = "C"
            confidence = 0.7
            signals = json.dumps(match_details, default=str)
        else:
            lane = matched_lanes[0]
            confidence = min(0.9, 0.3 + len(match_details.get(lane, [])) * 0.15)
            signals = json.dumps(match_details, default=str)

        with _db(self.db_path) as conn:
            conn.execute(
                "INSERT INTO cerberus_lanes (file_path, lane, confidence, matched_signals, classified_at) VALUES (?, ?, ?, ?, ?)",
                (file_path, lane, confidence, signals, _now()),
            )
        return lane

    def classify_batch(self) -> dict[str, int]:
        """Classify all extracted files that haven't been classified yet."""
        with _db(self.db_path, readonly=True) as conn:
            rows = conn.execute(
                """SELECT e.file_path, e.content_preview
                   FROM cerberus_extractions e
                   LEFT JOIN cerberus_lanes l ON e.file_path = l.file_path
                   WHERE l.id IS NULL AND e.content_preview IS NOT NULL""",
            ).fetchall()

        counts: dict[str, int] = {k: 0 for k in LANE_NAMES}
        for row in rows:
            text = f"{os.path.basename(row['file_path'])} {row['content_preview'] or ''}"
            lane = self._classify_text(row["file_path"], text)
            counts[lane] = counts.get(lane, 0) + 1

        logger.info("Classified %d files: %s", sum(counts.values()), counts)
        return counts

    # ------------------------------------------------------------------
    # 4. Weapon Detector
    # ------------------------------------------------------------------

    def detect_weapons(self, min_severity: int = 1) -> int:
        """Scan all extractions for legal weapons. Returns count found."""
        with _db(self.db_path, readonly=True) as conn:
            rows = conn.execute(
                "SELECT file_path, content_preview FROM cerberus_extractions WHERE content_preview IS NOT NULL AND content_preview != ''",
            ).fetchall()

        weapons: list[tuple] = []
        for row in rows:
            text = row["content_preview"] or ""
            fpath = row["file_path"]
            for wtype, spec in WEAPON_PATTERNS.items():
                if spec["severity"] < min_severity:
                    continue
                for match in spec["pattern"].finditer(text):
                    start = max(0, match.start() - 100)
                    end = min(len(text), match.end() + 100)
                    context = text[start:end].replace("\n", " ").strip()

                    # Get lane if classified
                    lane = ""
                    with _db(self.db_path, readonly=True) as conn2:
                        lr = conn2.execute(
                            "SELECT lane FROM cerberus_lanes WHERE file_path = ? ORDER BY id DESC LIMIT 1",
                            (fpath,),
                        ).fetchone()
                        if lr:
                            lane = lr["lane"]

                    weapons.append((
                        fpath, wtype, match.group()[:200],
                        spec["severity"], context[:500], lane, _now(),
                    ))

        with _db(self.db_path) as conn:
            # Clear prior weapon scan results to avoid duplicates
            conn.execute("DELETE FROM cerberus_weapons")
            conn.executemany(
                """INSERT INTO cerberus_weapons
                   (file_path, weapon_type, matched_text, severity, context, lane, detected_at)
                   VALUES (?, ?, ?, ?, ?, ?, ?)""",
                weapons,
            )

        logger.info("Detected %d legal weapons (min severity %d)", len(weapons), min_severity)
        return len(weapons)

    # ------------------------------------------------------------------
    # 5. Gap Analyzer
    # ------------------------------------------------------------------

    def analyze_gaps(self, lane_filter: Optional[str] = None) -> int:
        """Identify evidence gaps. Returns count of gaps found."""
        gaps: list[tuple] = []

        with _db(self.db_path, readonly=True) as conn:
            # Gap type 1: Lanes with zero or few files
            lane_counts = conn.execute(
                "SELECT lane, COUNT(*) as cnt FROM cerberus_lanes GROUP BY lane",
            ).fetchall()
            lane_map = {r["lane"]: r["cnt"] for r in lane_counts}

            for lane_code, lane_name in LANE_NAMES.items():
                if lane_filter and lane_code != lane_filter.upper():
                    continue
                cnt = lane_map.get(lane_code, 0)
                if cnt == 0:
                    gaps.append((
                        lane_code, "evidence_gap",
                        f"Lane {lane_code} ({lane_name}) has ZERO classified evidence files",
                        9, f"Scan drives for {lane_name} related documents", _now(),
                    ))
                elif cnt < 10:
                    gaps.append((
                        lane_code, "evidence_gap",
                        f"Lane {lane_code} ({lane_name}) has only {cnt} files — may be insufficient",
                        6, f"Search for more {lane_name} evidence across all drives", _now(),
                    ))

            # Gap type 2: Lanes with no high-severity weapons
            for lane_code in LANE_NAMES:
                if lane_filter and lane_code != lane_filter.upper():
                    continue
                weap_row = conn.execute(
                    "SELECT COUNT(*) as cnt FROM cerberus_weapons WHERE lane = ? AND severity >= 7",
                    (lane_code,),
                ).fetchone()
                if (weap_row["cnt"] or 0) == 0 and lane_map.get(lane_code, 0) > 0:
                    gaps.append((
                        lane_code, "weapon_gap",
                        f"Lane {lane_code} has evidence but no high-severity legal weapons detected",
                        5, "Re-examine evidence for admissions, threats, or contradictions", _now(),
                    ))

            # Gap type 3: Files scanned but not extracted
            unextracted = conn.execute(
                """SELECT COUNT(*) as cnt FROM cerberus_inventory i
                   LEFT JOIN cerberus_extractions e ON i.path = e.file_path
                   WHERE e.id IS NULL AND i.category IN ('document','text','structured')""",
            ).fetchone()
            if unextracted["cnt"] > 0:
                gaps.append((
                    "ALL", "extraction_gap",
                    f"{unextracted['cnt']} files scanned but not yet extracted",
                    7, "Run: cerberus extract <directory> to process unextracted files", _now(),
                ))

            # Gap type 4: Files extracted but not classified
            unclassified = conn.execute(
                """SELECT COUNT(*) as cnt FROM cerberus_extractions e
                   LEFT JOIN cerberus_lanes l ON e.file_path = l.file_path
                   WHERE l.id IS NULL""",
            ).fetchone()
            if unclassified["cnt"] > 0:
                gaps.append((
                    "ALL", "classification_gap",
                    f"{unclassified['cnt']} files extracted but not classified into lanes",
                    6, "Run: cerberus classify to auto-classify all extracted files", _now(),
                ))

        with _db(self.db_path) as conn:
            conn.execute("DELETE FROM cerberus_gaps")
            conn.executemany(
                """INSERT INTO cerberus_gaps
                   (lane, gap_type, description, severity, suggestion, detected_at)
                   VALUES (?, ?, ?, ?, ?, ?)""",
                gaps,
            )

        logger.info("Found %d evidence gaps", len(gaps))
        return len(gaps)

    # ------------------------------------------------------------------
    # 6. Reporting
    # ------------------------------------------------------------------

    def report(self, output_format: str = "md") -> str:
        """Generate a summary report. Returns report as string."""
        with _db(self.db_path, readonly=True) as conn:
            stats = conn.execute("""
                SELECT
                    (SELECT COUNT(*) FROM cerberus_inventory) AS total_files,
                    (SELECT COUNT(*) FROM cerberus_extractions) AS total_extracted,
                    (SELECT COUNT(*) FROM cerberus_extractions WHERE error = '' OR error IS NULL) AS successful_extractions,
                    (SELECT COUNT(*) FROM cerberus_lanes) AS total_classified,
                    (SELECT COUNT(*) FROM cerberus_weapons) AS total_weapons,
                    (SELECT COUNT(*) FROM cerberus_gaps) AS total_gaps,
                    (SELECT SUM(size_bytes) FROM cerberus_inventory) AS total_bytes
            """).fetchone()

            lane_breakdown = conn.execute(
                "SELECT lane, COUNT(*) as cnt FROM cerberus_lanes GROUP BY lane ORDER BY cnt DESC",
            ).fetchall()

            top_weapons = conn.execute(
                "SELECT weapon_type, COUNT(*) as cnt, AVG(severity) as avg_sev FROM cerberus_weapons GROUP BY weapon_type ORDER BY avg_sev DESC",
            ).fetchall()

            critical_gaps = conn.execute(
                "SELECT lane, gap_type, description, severity FROM cerberus_gaps WHERE severity >= 7 ORDER BY severity DESC",
            ).fetchall()

            ext_breakdown = conn.execute(
                "SELECT extension, COUNT(*) as cnt FROM cerberus_inventory GROUP BY extension ORDER BY cnt DESC LIMIT 15",
            ).fetchall()

        if output_format == "json":
            return json.dumps({
                "stats": dict(stats),
                "lanes": [dict(r) for r in lane_breakdown],
                "weapons": [dict(r) for r in top_weapons],
                "gaps": [dict(r) for r in critical_gaps],
                "extensions": [dict(r) for r in ext_breakdown],
                "generated_at": _now(),
            }, indent=2, default=str)

        # Markdown report
        total_mb = (stats["total_bytes"] or 0) / (1024 * 1024)
        lines = [
            "# CERBERUS Evidence Guardian — Status Report",
            f"Generated: {_now()}\n",
            "## Inventory Summary",
            f"| Metric | Count |",
            f"|--------|-------|",
            f"| Files scanned | {stats['total_files']:,} |",
            f"| Total size | {total_mb:,.1f} MB |",
            f"| Extracted | {stats['total_extracted']:,} |",
            f"| Successful extractions | {stats['successful_extractions']:,} |",
            f"| Classified | {stats['total_classified']:,} |",
            f"| Legal weapons | {stats['total_weapons']:,} |",
            f"| Evidence gaps | {stats['total_gaps']:,} |",
            "",
            "## File Types",
            "| Extension | Count |",
            "|-----------|-------|",
        ]
        for r in ext_breakdown:
            lines.append(f"| .{r['extension']} | {r['cnt']:,} |")

        lines += ["", "## Lane Distribution", "| Lane | Name | Files |", "|------|------|-------|"]
        for r in lane_breakdown:
            name = LANE_NAMES.get(r["lane"], "Unknown")
            lines.append(f"| {r['lane']} | {name} | {r['cnt']:,} |")

        if top_weapons:
            lines += ["", "## Weapon Arsenal", "| Type | Count | Avg Severity |", "|------|-------|-------------|"]
            for r in top_weapons:
                lines.append(f"| {r['weapon_type']} | {r['cnt']:,} | {r['avg_sev']:.1f} |")

        if critical_gaps:
            lines += ["", "## ⚠️ Critical Gaps (severity ≥ 7)", "| Lane | Type | Description |", "|------|------|-------------|"]
            for r in critical_gaps:
                lines.append(f"| {r['lane']} | {r['gap_type']} | {r['description']} |")

        return "\n".join(lines)

    # ------------------------------------------------------------------
    # 7. Status
    # ------------------------------------------------------------------

    def status(self) -> dict:
        """Return engine status as a dict."""
        with _db(self.db_path, readonly=True) as conn:
            row = conn.execute("""
                SELECT
                    (SELECT COUNT(*) FROM cerberus_inventory) AS files,
                    (SELECT COUNT(*) FROM cerberus_extractions) AS extracted,
                    (SELECT COUNT(*) FROM cerberus_lanes) AS classified,
                    (SELECT COUNT(*) FROM cerberus_weapons) AS weapons,
                    (SELECT COUNT(*) FROM cerberus_gaps) AS gaps,
                    (SELECT MAX(scanned_at) FROM cerberus_inventory) AS last_scan,
                    (SELECT MAX(extracted_at) FROM cerberus_extractions) AS last_extract,
                    (SELECT MAX(detected_at) FROM cerberus_weapons) AS last_weapon_scan
            """).fetchone()
        return dict(row)


# ---------------------------------------------------------------------------
# CLI Interface
# ---------------------------------------------------------------------------


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="cerberus",
        description="CERBERUS Evidence Guardian Engine — scan, extract, classify, weaponize",
    )
    sub = parser.add_subparsers(dest="command", required=True)

    # scan
    p_scan = sub.add_parser("scan", help="Scan directory for files")
    p_scan.add_argument("directory", help="Directory path to scan")
    p_scan.add_argument("--recursive", action="store_true", default=True, help="Recurse into subdirectories (default: True)")
    p_scan.add_argument("--no-recursive", dest="recursive", action="store_false")
    p_scan.add_argument("--extensions", type=str, default=None, help="Comma-separated extensions (e.g., pdf,docx,txt)")

    # extract
    p_ext = sub.add_parser("extract", help="Extract text content from files")
    p_ext.add_argument("path", help="File or directory to extract")
    p_ext.add_argument("--limit", type=int, default=0, help="Max files to extract (0=all)")

    # classify
    p_cls = sub.add_parser("classify", help="Classify file(s) into case lanes")
    p_cls.add_argument("file", nargs="?", default=None, help="File to classify (omit for batch)")
    p_cls.add_argument("--lane", type=str, default=None, choices=["A", "B", "C", "D", "E", "F"], help="Force lane assignment")

    # weapons
    p_weap = sub.add_parser("weapons", help="Detect legal weapons in evidence")
    p_weap.add_argument("--min-severity", type=int, default=1, help="Minimum severity threshold (1-10)")

    # gaps
    p_gaps = sub.add_parser("gaps", help="Analyze evidence gaps")
    p_gaps.add_argument("--lane", type=str, default=None, choices=["A", "B", "C", "D", "E", "F"], help="Filter by lane")

    # report
    p_rep = sub.add_parser("report", help="Generate summary report")
    p_rep.add_argument("--output", type=str, default="md", choices=["json", "md"], help="Output format")

    # status
    sub.add_parser("status", help="Show engine status")

    return parser


def main() -> int:
    logging.basicConfig(level=logging.INFO, format="%(asctime)s [CERBERUS] %(message)s")
    parser = _build_parser()
    args = parser.parse_args()

    engine = CerberusEngine()

    if args.command == "scan":
        exts = args.extensions.split(",") if args.extensions else None
        count = engine.scan(args.directory, recursive=args.recursive, extensions=exts)
        print(f"✓ Scanned {count:,} files from {args.directory}")

    elif args.command == "extract":
        count = engine.extract(args.path, limit=args.limit)
        print(f"✓ Extracted {count:,} files")

    elif args.command == "classify":
        if args.file:
            lane = engine.classify(args.file, force_lane=args.lane)
            print(f"✓ Classified → Lane {lane} ({LANE_NAMES.get(lane, '?')})")
        else:
            counts = engine.classify_batch()
            total = sum(counts.values())
            print(f"✓ Batch classified {total:,} files:")
            for l, c in sorted(counts.items()):
                if c > 0:
                    print(f"  Lane {l} ({LANE_NAMES.get(l, '?')}): {c:,}")

    elif args.command == "weapons":
        count = engine.detect_weapons(min_severity=args.min_severity)
        print(f"✓ Detected {count:,} legal weapons (min severity {args.min_severity})")

    elif args.command == "gaps":
        count = engine.analyze_gaps(lane_filter=args.lane)
        print(f"✓ Found {count:,} evidence gaps")
        if count > 0:
            report = engine.report(output_format="md")
            # Print just the gaps section
            for line in report.split("\n"):
                if "Gap" in line or "gap" in line:
                    print(f"  {line}")

    elif args.command == "report":
        report = engine.report(output_format=args.output)
        print(report)

    elif args.command == "status":
        s = engine.status()
        print("CERBERUS Engine Status:")
        for k, v in s.items():
            label = k.replace("_", " ").title()
            print(f"  {label}: {v if v is not None else '—'}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
