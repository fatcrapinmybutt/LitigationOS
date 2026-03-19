"""
A11 — TEXT MINER
DELTA9 Fleet · Tier 3 · Lane 1 Infrastructure

Classifies and extracts entities from canonical .md/.txt files.
Detects MEEK lane, scores relevance, generates atoms.
READ-ONLY on source files — all output goes to DB.
"""
import hashlib
import re
import time
from pathlib import Path

from ..agent_base import Agent9999
from ..agent_models import (
    SkipItemError, FatalAgentError, MASTER_INDEX_DB,
    LEGAL_EXTENSIONS, DATA_EXTENSIONS,
    LANE_A_SIGNALS, LANE_B_SIGNALS, LANE_C_SIGNALS
)

# Patterns
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

# 12 document categories with keyword patterns
CATEGORY_PATTERNS = {
    "COURT_ORDER": re.compile(
        r'\b(order|ruling|judgment|decree|opinion)\b.*\b(court|judge|honor)\b', re.IGNORECASE | re.DOTALL
    ),
    "MOTION": re.compile(
        r'\bmotion\s+(to|for)\b', re.IGNORECASE
    ),
    "BRIEF": re.compile(
        r'\b(brief|memorandum\s+of\s+law|argument)\b', re.IGNORECASE
    ),
    "AFFIDAVIT": re.compile(
        r'\b(affidavit|sworn\s+statement|declaration)\b', re.IGNORECASE
    ),
    "COMPLAINT": re.compile(
        r'\b(complaint|petition|summons)\b', re.IGNORECASE
    ),
    "TRANSCRIPT": re.compile(
        r'\b(transcript|proceedings|hearing|deposition)\b', re.IGNORECASE
    ),
    "EVIDENCE_LOG": re.compile(
        r'\b(exhibit|evidence\s+log|inventory)\b', re.IGNORECASE
    ),
    "ANALYSIS": re.compile(
        r'\b(analysis|assessment|evaluation|review)\b', re.IGNORECASE
    ),
    "CORRESPONDENCE": re.compile(
        r'\b(dear|sincerely|to\s+whom|re:|from:|letter)\b', re.IGNORECASE
    ),
    "STATUTE": re.compile(
        r'\bMCL\s+\d+', re.IGNORECASE
    ),
    "CASE_LAW": re.compile(
        r'\b\d+\s+(Mich|NW2d|NW\.2d)\b', re.IGNORECASE
    ),
}

CHUNK_SIZE = 50 * 1024  # 50KB
LARGE_FILE_THRESHOLD = 1 * 1024 * 1024  # 1MB


class TextMiner(Agent9999):
    """Classifies and extracts entities from canonical .md/.txt files."""

    def __init__(self):
        super().__init__(agent_id="A11-TEXT-MINER")

    def _validate_preconditions(self):
        cursor = self._db_execute(
            "SELECT COUNT(*) FROM files "
            "WHERE extension IN ('.md', '.txt') AND is_canonical = 1"
        )
        count = cursor.fetchone()[0]
        if count == 0:
            raise FatalAgentError("No canonical text files (.md/.txt) in DB")

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
        self._db_execute("""
            CREATE TABLE IF NOT EXISTS ready_queue (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                file_id INTEGER,
                agent_source TEXT,
                meek_lane TEXT,
                priority REAL DEFAULT 0,
                queued_at REAL,
                processed INTEGER DEFAULT 0
            )
        """)
        self.db.commit()

    def _get_work_items(self) -> list:
        cursor = self._db_execute(
            "SELECT * FROM files "
            "WHERE extension IN ('.md', '.txt') AND is_canonical = 1 AND processed = 0"
        )
        return cursor.fetchall()

    def _process_item(self, row) -> None:
        file_path = row["full_path"]
        long_path = self.long_path(file_path)
        file_id = row["id"]

        text = self._read_file(long_path)
        if text is None:
            raise SkipItemError(f"Unreadable file: {file_path}")

        file_size = len(text.encode("utf-8", errors="ignore"))

        # For large files, process in chunks then merge
        if file_size > LARGE_FILE_THRESHOLD:
            self._process_large(file_id, text, file_path)
        else:
            self._process_text(file_id, text, file_path)

    def _read_file(self, path: str) -> str | None:
        """Read file with encoding fallback chain."""
        for encoding in ("utf-8", "latin-1"):
            try:
                with open(path, "r", encoding=encoding, errors="strict") as f:
                    return f.read()
            except (UnicodeDecodeError, ValueError):
                continue
            except (OSError, PermissionError) as e:
                self._log("WARN", f"Cannot read {path}: {e}")
                return None
        return None

    def _process_large(self, file_id: int, text: str, file_path: str):
        """Chunk large files into CHUNK_SIZE segments and merge results."""
        all_citations = []
        all_facts = []
        combined_category_scores = {}
        total_score = 0.0
        chunk_count = 0

        for i in range(0, len(text), CHUNK_SIZE):
            chunk = text[i:i + CHUNK_SIZE]
            chunk_count += 1

            cat = self._classify(chunk)
            combined_category_scores[cat] = combined_category_scores.get(cat, 0) + 1

            citations = self._extract_citations(file_id, chunk, offset=i)
            all_citations.extend(citations)

            facts = self._extract_facts(file_id, chunk, offset=i)
            all_facts.extend(facts)

            total_score += self._score_content(chunk)

        # Dominant category
        category = max(combined_category_scores, key=combined_category_scores.get)
        avg_score = total_score / max(chunk_count, 1)
        lane = self._detect_lane(text[:CHUNK_SIZE * 3])  # Sample first 3 chunks for lane

        self._db_execute(
            "UPDATE files SET processed = 1, category = ?, meek_lane = ?, content_score = ? "
            "WHERE id = ?",
            (category, lane, avg_score, file_id)
        )

        self._store_atoms(all_citations, all_facts)

        try:
            self._db_execute(
                "INSERT OR IGNORE INTO ready_queue (file_id, queue_type, priority, agent_source, status) "
                "VALUES (?, ?, ?, ?, 'pending')",
                (file_id, lane or "UNCLASSIFIED", avg_score, self.agent_id)
            )
            self.db.commit()
        except Exception:
            pass  # ready_queue insert is non-critical

    def _process_text(self, file_id: int, text: str, file_path: str):
        """Process a normal-sized text file."""
        category = self._classify(text)
        lane = self._detect_lane(text)
        score = self._score_content(text)

        self._db_execute(
            "UPDATE files SET processed = 1, category = ?, meek_lane = ?, content_score = ? "
            "WHERE id = ?",
            (category, lane, score, file_id)
        )

        citations = self._extract_citations(file_id, text)
        facts = self._extract_facts(file_id, text)
        self._store_atoms(citations, facts)

        try:
            self._db_execute(
                "INSERT OR IGNORE INTO ready_queue (file_id, queue_type, priority, agent_source, status) "
                "VALUES (?, ?, ?, ?, 'pending')",
                (file_id, lane or "UNCLASSIFIED", score, self.agent_id)
            )
            self.db.commit()
        except Exception:
            pass  # ready_queue insert is non-critical

    def _classify(self, text: str) -> str:
        """Classify text into one of 12 categories."""
        best_cat = "OTHER"
        best_count = 0
        for cat, pattern in CATEGORY_PATTERNS.items():
            matches = pattern.findall(text)
            if len(matches) > best_count:
                best_count = len(matches)
                best_cat = cat
        return best_cat

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

    def _extract_citations(self, file_id: int, text: str, offset: int = 0) -> list:
        now = time.time()
        rows = []
        for m in MCL_PATTERN.finditer(text):
            aid = hashlib.md5(f"{file_id}:mcl:{m.group()}:{offset + m.start()}".encode()).hexdigest()[:16]
            rows.append((aid, file_id, "MCL", m.group(), None, now))
        for m in MCR_PATTERN.finditer(text):
            aid = hashlib.md5(f"{file_id}:mcr:{m.group()}:{offset + m.start()}".encode()).hexdigest()[:16]
            rows.append((aid, file_id, "MCR", m.group(), None, now))
        for m in CASE_NUM_PATTERN.finditer(text):
            aid = hashlib.md5(f"{file_id}:case:{m.group()}:{offset + m.start()}".encode()).hexdigest()[:16]
            rows.append((aid, file_id, "CASE_NUM", m.group(), None, now))
        return rows

    def _extract_facts(self, file_id: int, text: str, offset: int = 0) -> list:
        now = time.time()
        rows = []
        for m in NAME_PATTERN.finditer(text):
            aid = hashlib.md5(f"{file_id}:person:{m.group()}:{offset + m.start()}".encode()).hexdigest()[:16]
            start = max(0, m.start() - 100)
            end = min(len(text), m.end() + 100)
            context = text[start:end].replace("\n", " ").strip()
            rows.append((aid, file_id, "PERSON_MENTION", context, None, 1.0, now))
        for m in DATE_PATTERN.finditer(text):
            aid = hashlib.md5(f"{file_id}:date:{m.group()}:{offset + m.start()}".encode()).hexdigest()[:16]
            start = max(0, m.start() - 80)
            end = min(len(text), m.end() + 80)
            context = text[start:end].replace("\n", " ").strip()
            rows.append((aid, file_id, "DATE_MENTION", context, None, 0.8, now))
        return rows

    def _store_atoms(self, citations: list, facts: list):
        if citations:
            self._db_executemany(
                "INSERT OR IGNORE INTO citation_atoms "
                "(id, file_id, citation_type, citation_text, source_page, created_at) "
                "VALUES (?, ?, ?, ?, ?, ?)",
                citations
            )
        if facts:
            self._db_executemany(
                "INSERT OR IGNORE INTO fact_atoms "
                "(id, file_id, atom_type, content, source_page, confidence, created_at) "
                "VALUES (?, ?, ?, ?, ?, ?, ?)",
                facts
            )
