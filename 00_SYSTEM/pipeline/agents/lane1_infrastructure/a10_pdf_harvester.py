"""
A10 — PDF HARVESTER
DELTA9 Fleet · Tier 3 · Lane 1 Infrastructure

Extracts text from canonical PDFs, classifies content, detects MEEK lane,
scores relevance, and generates atoms for downstream intelligence agents.
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

# Citation patterns
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


class PdfHarvester(Agent9999):
    """Extracts text from canonical PDFs and generates DB atoms."""

    def __init__(self):
        super().__init__(agent_id="A10-PDF-HARVEST")

    def _validate_preconditions(self):
        cursor = self._db_execute(
            "SELECT COUNT(*) FROM files WHERE extension = '.pdf' AND is_canonical = 1"
        )
        count = cursor.fetchone()[0]
        if count == 0:
            raise FatalAgentError("No canonical PDF files in DB")

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
            "SELECT * FROM files WHERE extension = '.pdf' "
            "AND is_canonical = 1 AND processed = 0"
        )
        return cursor.fetchall()

    def _process_item(self, row) -> None:
        file_path = row["full_path"]
        long_path = self.long_path(file_path)
        file_id = row["id"]

        text = self._extract_text(long_path)
        if text is None:
            self._db_execute(
                "UPDATE files SET processed = 1 WHERE id = ?",
                (file_id,)
            )
            self.db.commit()
            raise SkipItemError(f"PDF needs OCR: {file_path}")

        lane = self._detect_lane(text)
        score = self._score_content(text)

        self._db_execute(
            "UPDATE files SET processed = 1, meek_lane = ?, content_score = ? WHERE id = ?",
            (lane, score, file_id)
        )

        self._extract_and_store_atoms(file_id, text)

        # Enqueue for Lane 2 intelligence
        self._db_execute(
            "INSERT OR IGNORE INTO ready_queue (file_id, queue_type, priority, claimed_by, status) "
            "VALUES (?, ?, ?, ?, 'pending')",
            (file_id, lane, score, self.agent_id)
        )
        self.db.commit()

    def _extract_text(self, path: str) -> str | None:
        """Try pymupdf first, then pdfplumber. Return None if both fail."""
        # Attempt 1: pymupdf
        try:
            import pymupdf
            doc = pymupdf.open(path)
            if doc.page_count == 0:
                doc.close()
                raise SkipItemError(f"Zero-page PDF: {path}")
            if doc.is_encrypted:
                doc.close()
                raise SkipItemError(f"Encrypted PDF: {path}")
            pages = []
            for page in doc:
                pages.append(page.get_text())
            doc.close()
            text = "\n".join(pages).strip()
            if text:
                return text
        except SkipItemError:
            raise
        except Exception as e:
            self._log("WARN", f"pymupdf failed: {e}")

        # Attempt 2: pdfplumber
        try:
            import pdfplumber
            with pdfplumber.open(path) as pdf:
                if len(pdf.pages) == 0:
                    raise SkipItemError(f"Zero-page PDF: {path}")
                pages = []
                for page in pdf.pages:
                    t = page.extract_text()
                    if t:
                        pages.append(t)
                text = "\n".join(pages).strip()
                if text:
                    return text
        except SkipItemError:
            raise
        except Exception as e:
            self._log("WARN", f"pdfplumber failed: {e}")

        return None

    def _detect_lane(self, text: str) -> str:
        """Detect MEEK lane from content signals."""
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
        """Score content by legal relevance."""
        mcl_count = len(MCL_PATTERN.findall(text))
        mcr_count = len(MCR_PATTERN.findall(text))
        citations = mcl_count + mcr_count
        persons = len(NAME_PATTERN.findall(text))
        dates = len(DATE_PATTERN.findall(text))
        case_nums = len(CASE_NUM_PATTERN.findall(text))

        # Length factor: diminishing returns beyond 10k chars
        length_factor = min(len(text) / 10000, 2.0)

        return (citations * 3 + case_nums * 2 + persons * 1.5 + dates) * max(length_factor, 0.1)

    def _extract_and_store_atoms(self, file_id: int, text: str):
        """Extract fact and citation atoms from text and INSERT into DB."""
        now = time.time()

        # Citation atoms
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

        if citation_rows:
            self._db_executemany(
                "INSERT OR IGNORE INTO citation_atoms "
                "(id, file_id, citation_type, citation_text, source_page, created_at) "
                "VALUES (?, ?, ?, ?, ?, ?)",
                citation_rows
            )

        # Fact atoms: person name mentions
        fact_rows = []
        for m in NAME_PATTERN.finditer(text):
            aid = hashlib.md5(f"{file_id}:person:{m.group()}:{m.start()}".encode()).hexdigest()[:16]
            # Capture surrounding context (±100 chars)
            start = max(0, m.start() - 100)
            end = min(len(text), m.end() + 100)
            context = text[start:end].replace("\n", " ").strip()
            fact_rows.append((aid, file_id, "PERSON_MENTION", context, None, 1.0, now))

        if fact_rows:
            self._db_executemany(
                "INSERT OR IGNORE INTO fact_atoms "
                "(id, file_id, atom_type, content, source_page, confidence, created_at) "
                "VALUES (?, ?, ?, ?, ?, ?, ?)",
                fact_rows
            )
