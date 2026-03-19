"""
A12 — STRUCTURED DATA PARSER
DELTA9 Fleet · Tier 3 · Lane 1 Infrastructure

Parses canonical .json, .jsonl, .csv files for legal content.
Extracts citations, entities, scores relevance, generates atoms.
READ-ONLY on source files — all output goes to DB.
"""
import csv
import hashlib
import io
import json
import re
import time
from pathlib import Path

from ..agent_base import Agent9999
from ..agent_models import (
    SkipItemError, FatalAgentError, MASTER_INDEX_DB,
    LEGAL_EXTENSIONS, DATA_EXTENSIONS,
    LANE_A_SIGNALS, LANE_B_SIGNALS, LANE_C_SIGNALS
)

MCL_PATTERN = re.compile(r'MCL\s+\d+[\.\d]*', re.IGNORECASE)
MCR_PATTERN = re.compile(r'MCR\s+\d+[\.\d]*', re.IGNORECASE)
CASE_NUM_PATTERN = re.compile(r'\d{4}-\d{4,7}')
PERSON_NAMES = {'pigors', 'watson', 'mcneill', 'rusco', 'hoopes'}
NAME_PATTERN = re.compile(
    r'\b(' + '|'.join(re.escape(n) for n in PERSON_NAMES) + r')\b',
    re.IGNORECASE
)
DATE_PATTERN = re.compile(
    r'\b\d{1,2}[/\-]\d{1,2}[/\-]\d{2,4}\b'
    r'|\b(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)\w*\s+\d{1,2},?\s+\d{4}\b',
    re.IGNORECASE
)

# Fields likely to contain legal content in JSON
LEGAL_CONTENT_FIELDS = {
    'text', 'content', 'description', 'atoms', 'body', 'summary',
    'notes', 'details', 'finding', 'ruling', 'citation', 'excerpt',
    'analysis', 'argument', 'statement', 'testimony'
}

HUGE_FILE_THRESHOLD = 50 * 1024 * 1024  # 50MB
SAMPLE_LINES = 1000


class StructParser(Agent9999):
    """Parses canonical structured data files (.json, .jsonl, .csv)."""

    def __init__(self):
        super().__init__(agent_id="A12-STRUCT-PARSE")

    def _validate_preconditions(self):
        cursor = self._db_execute(
            "SELECT COUNT(*) FROM files "
            "WHERE extension IN ('.json', '.csv', '.jsonl') AND is_canonical = 1"
        )
        count = cursor.fetchone()[0]
        if count == 0:
            raise FatalAgentError("No canonical structured files (.json/.csv/.jsonl) in DB")

    def _ensure_tables(self):
        self._db_execute("""
            CREATE TABLE IF NOT EXISTS fact_atoms (
                id TEXT PRIMARY KEY,
                file_id INTEGER,
                atom_type TEXT,
                content TEXT,
                source_page INTEGER,
                confidence REAL DEFAULT 1.0,
                created_at REAL
            )
        """)
        self._db_execute("""
            CREATE TABLE IF NOT EXISTS citation_atoms (
                id TEXT PRIMARY KEY,
                file_id INTEGER,
                citation_type TEXT,
                citation_text TEXT,
                source_page INTEGER,
                created_at REAL
            )
        """)
        self.db.commit()

    def _get_work_items(self) -> list:
        cursor = self._db_execute(
            "SELECT * FROM files "
            "WHERE extension IN ('.json', '.csv', '.jsonl') "
            "AND is_canonical = 1 AND processed = 0"
        )
        return cursor.fetchall()

    def _process_item(self, row) -> None:
        file_path = row["full_path"]
        long_path = self.long_path(file_path)
        file_id = row["id"]
        ext = row["extension"]

        # Check file size — sample huge files
        try:
            import os
            file_size = os.path.getsize(long_path)
        except OSError as e:
            raise SkipItemError(f"Cannot stat {file_path}: {e}")

        is_huge = file_size > HUGE_FILE_THRESHOLD

        raw_text = self._read_file(long_path, sample_only=is_huge)
        if raw_text is None:
            raise SkipItemError(f"Unreadable file: {file_path}")

        if ext == ".json":
            combined = self._parse_json(raw_text, file_path)
        elif ext == ".jsonl":
            combined = self._parse_jsonl(raw_text, file_path)
        elif ext == ".csv":
            combined = self._parse_csv(raw_text, file_path)
        else:
            raise SkipItemError(f"Unexpected extension: {ext}")

        if not combined:
            self._db_execute(
                "UPDATE files SET processed = 1, content_score = 0 WHERE id = ?",
                (file_id,)
            )
            self.db.commit()
            return

        score = self._score_content(combined)
        lane = self._detect_lane(combined)

        self._db_execute(
            "UPDATE files SET processed = 1, content_score = ?, meek_lane = ? WHERE id = ?",
            (score, lane, file_id)
        )

        self._extract_and_store_atoms(file_id, combined)
        self.db.commit()

    def _read_file(self, path: str, sample_only: bool = False) -> str | None:
        """Read file with encoding fallback. Optionally sample first N lines."""
        for encoding in ("utf-8", "latin-1"):
            try:
                with open(path, "r", encoding=encoding, errors="strict") as f:
                    if sample_only:
                        lines = []
                        for i, line in enumerate(f):
                            if i >= SAMPLE_LINES:
                                break
                            lines.append(line)
                        return "".join(lines)
                    else:
                        return f.read()
            except (UnicodeDecodeError, ValueError):
                continue
            except (OSError, PermissionError) as e:
                self._log("WARN", f"Cannot read {path}: {e}")
                return None
        return None

    def _parse_json(self, raw: str, file_path: str) -> str:
        """Parse JSON and extract text from legal content fields."""
        try:
            data = json.loads(raw)
        except (json.JSONDecodeError, ValueError) as e:
            self._log("WARN", f"Malformed JSON {file_path}: {e}")
            raise SkipItemError(f"Malformed JSON: {file_path}")

        return self._extract_json_text(data)

    def _parse_jsonl(self, raw: str, file_path: str) -> str:
        """Parse JSONL line by line, extract legal content."""
        parts = []
        for line_num, line in enumerate(raw.splitlines(), 1):
            line = line.strip()
            if not line:
                continue
            try:
                obj = json.loads(line)
                text = self._extract_json_text(obj)
                if text:
                    parts.append(text)
            except (json.JSONDecodeError, ValueError):
                # Skip malformed lines, don't fail the whole file
                continue
        return "\n".join(parts)

    def _parse_csv(self, raw: str, file_path: str) -> str:
        """Parse CSV, scan headers and values for legal terms."""
        parts = []
        try:
            reader = csv.reader(io.StringIO(raw))
            headers = None
            for row_num, row in enumerate(reader):
                if row_num == 0:
                    headers = row
                    parts.append(" ".join(row))
                else:
                    parts.append(" ".join(row))
        except csv.Error as e:
            self._log("WARN", f"CSV parse error {file_path}: {e}")
            raise SkipItemError(f"Malformed CSV: {file_path}")
        return "\n".join(parts)

    def _extract_json_text(self, data) -> str:
        """Recursively extract text from legal content fields in JSON."""
        parts = []
        if isinstance(data, dict):
            for key, val in data.items():
                if key.lower() in LEGAL_CONTENT_FIELDS and isinstance(val, str):
                    parts.append(val)
                elif isinstance(val, (dict, list)):
                    parts.append(self._extract_json_text(val))
        elif isinstance(data, list):
            for item in data:
                parts.append(self._extract_json_text(item))
        elif isinstance(data, str):
            parts.append(data)
        return "\n".join(p for p in parts if p)

    def _detect_lane(self, text: str) -> str:
        text_lower = text.lower()
        scores = {"A": 0, "B": 0, "C": 0}
        for signal in LANE_A_SIGNALS:
            if signal in text_lower:
                scores["A"] += 1
        for signal in LANE_B_SIGNALS:
            if signal in text_lower:
                scores["B"] += 1
        for signal in LANE_C_SIGNALS:
            if signal in text_lower:
                scores["C"] += 1
        if max(scores.values()) == 0:
            return "UNCLASSIFIED"
        return max(scores, key=scores.get)

    def _score_content(self, text: str) -> float:
        citations = len(MCL_PATTERN.findall(text)) + len(MCR_PATTERN.findall(text))
        keywords = len(CASE_NUM_PATTERN.findall(text))
        persons = len(NAME_PATTERN.findall(text))
        dates = len(DATE_PATTERN.findall(text))
        length_factor = min(len(text) / 10000, 2.0)
        return (citations * 3 + keywords * 1.5 + persons + dates) * max(length_factor, 0.1)

    def _extract_and_store_atoms(self, file_id: int, text: str):
        now = time.time()

        citation_rows = []
        for m in MCL_PATTERN.finditer(text):
            aid = hashlib.md5(f"{file_id}:mcl:{m.group()}:{m.start()}".encode()).hexdigest()[:16]
            citation_rows.append((aid, file_id, "MCL", m.group(), None, now))
        for m in MCR_PATTERN.finditer(text):
            aid = hashlib.md5(f"{file_id}:mcr:{m.group()}:{m.start()}".encode()).hexdigest()[:16]
            citation_rows.append((aid, file_id, "MCR", m.group(), None, now))
        for m in CASE_NUM_PATTERN.finditer(text):
            aid = hashlib.md5(f"{file_id}:case:{m.group()}:{m.start()}".encode()).hexdigest()[:16]
            citation_rows.append((aid, file_id, "CASE_NUM", m.group(), None, now))

        fact_rows = []
        for m in NAME_PATTERN.finditer(text):
            aid = hashlib.md5(f"{file_id}:person:{m.group()}:{m.start()}".encode()).hexdigest()[:16]
            start = max(0, m.start() - 100)
            end = min(len(text), m.end() + 100)
            context = text[start:end].replace("\n", " ").strip()
            fact_rows.append((aid, file_id, "PERSON_MENTION", context, None, 1.0, now))

        if citation_rows:
            self._db_executemany(
                "INSERT OR IGNORE INTO citation_atoms "
                "(id, file_id, citation_type, citation_text, source_page, created_at) "
                "VALUES (?, ?, ?, ?, ?, ?)",
                citation_rows
            )
        if fact_rows:
            self._db_executemany(
                "INSERT OR IGNORE INTO fact_atoms "
                "(id, file_id, atom_type, content, source_page, confidence, created_at) "
                "VALUES (?, ?, ?, ?, ?, ?, ?)",
                fact_rows
            )
