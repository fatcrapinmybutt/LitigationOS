#!/usr/bin/env python3
"""
DOCUMENT ANALYSIS ENGINE — Core Intelligence for LitigationOS
==============================================================
Reads legal documents line-by-line and extracts everything useful
for litigation across three case lanes:

  Lane A: Custody  (2024-001507-DC, Judge McNeill)
  Lane B: Housing  (2023-5907-PP, Judge Hoopes)
  Lane C: Civil Rights / Convergence (2025-002760-CZ)

Consumes drive scanner manifests, prioritizes files, extracts text,
performs deep pattern analysis, and stores structured findings in
case_analysis.db.

Usage:
    python analysis_engine.py scan           # Prioritize files from manifests
    python analysis_engine.py analyze        # Run full analysis
    python analysis_engine.py analyze --lane A  # Only Lane A files
    python analysis_engine.py report         # Generate summary report
    python analysis_engine.py all            # Full pipeline

Author: LitigationOS Pipeline
"""

import argparse
import datetime
import json
import os
import re
import sqlite3
import sys
import time
import traceback
from collections import Counter, defaultdict
from pathlib import Path
from typing import Dict, List, Optional, Tuple

# ════════════════════════════════════════════════════════════════════════
#  Paths & Constants
# ════════════════════════════════════════════════════════════════════════

SYSTEM_DIR = Path(r"C:\Users\andre\LitigationOS\00_SYSTEM")
MANIFEST_DIR = SYSTEM_DIR / "manifests"
ANALYSIS_DB_PATH = MANIFEST_DIR / "case_analysis.db"
BATCH_SIZE = 50
PROGRESS_INTERVAL = 10

# Import LocalAI from the pipeline
sys.path.insert(0, str(SYSTEM_DIR / "pipeline"))
try:
    from local_ai_engine import LocalAI
    _AI = LocalAI()
    _HAS_AI = True
except ImportError:
    _HAS_AI = False
    _AI = None

# Optional extraction libraries — graceful fallback
try:
    import pdfplumber
    _PDF_ENGINE = "pdfplumber"
except ImportError:
    try:
        from PyPDF2 import PdfReader
        _PDF_ENGINE = "PyPDF2"
    except ImportError:
        _PDF_ENGINE = None

try:
    from docx import Document as DocxDocument
    _HAS_DOCX = True
except ImportError:
    _HAS_DOCX = False


# ════════════════════════════════════════════════════════════════════════
#  Regex Patterns — Compiled Once
# ════════════════════════════════════════════════════════════════════════

# --- Legal Citations ---
_RE_MCR = re.compile(
    r'\bMCR\s+(\d+\.\d+(?:\([A-Z]\)(?:\(\d+\))?)?)', re.I
)
_RE_MCL = re.compile(
    r'\bMCL\s+(\d+\.\d+[a-z]*(?:\(\d+\))?)', re.I
)
_RE_FEDERAL_STATUTE = re.compile(
    r'\b(\d{1,2})\s*U\.?S\.?C\.?\s*§?\s*(\d+[a-z]*)', re.I
)
_RE_CASE_LAW = re.compile(
    r'([A-Z][A-Za-z\'\-]+(?:\s+[A-Z][A-Za-z\'\-]+)*)'
    r'\s+v\.?\s+'
    r'([A-Z][A-Za-z\'\-]+(?:\s+[A-Za-z\'\-]+)*)'
    r'(?:,\s*(\d+)\s+(Mich(?:\s+App)?|NW2d|NW\.?2d|F\.?(?:2d|3d|4th)|'
    r'US|U\.S\.|S\.?\s*Ct\.?|F\.?\s*Supp\.?\s*(?:2d|3d)?)\s+(\d+))?'
)
_RE_CONST_MI = re.compile(
    r'Const\.?\s+(?:of\s+)?1963,?\s+art\.?\s*([IVXLC]+),?\s*§\s*(\d+)', re.I
)
_RE_CONST_US = re.compile(
    r'U\.?S\.?\s*Const\.?,?\s*(?:amend\.?\s*([IVXLC]+\b)|art\.?\s*([IVXLC]+))', re.I
)
_RE_MRE = re.compile(r'\bMRE\s+(\d+)', re.I)

# --- Dates ---
_RE_DATE_ISO = re.compile(r'\b(\d{4}-\d{2}-\d{2})\b')
_RE_DATE_US = re.compile(r'\b(\d{1,2})/(\d{1,2})/(\d{2,4})\b')
_RE_DATE_LONG = re.compile(
    r'\b((?:January|February|March|April|May|June|July|August|September|'
    r'October|November|December)\s+\d{1,2},?\s+\d{4})\b', re.I
)
_RE_DATE_MDY = re.compile(
    r'\b((?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)\.?\s+\d{1,2},?\s+\d{4})\b', re.I
)

# --- Money ---
_RE_DOLLAR = re.compile(r'\$\s*([\d,]+(?:\.\d{2})?)')

# --- Case Numbers ---
_RE_CASE_NUM = re.compile(r'\b(\d{4}-\d{4,6}-[A-Z]{2})\b')

# --- Names / People (capitalized two-word+) ---
_RE_PERSON = re.compile(
    r'\b([A-Z][a-z]{2,}(?:\s+[A-Z]\.?)?\s+[A-Z][a-z]{2,})\b'
)
_RE_JUDGE = re.compile(
    r'(?:Judge|Hon\.?|Honorable|the\s+Court)\s+([A-Z][a-z]+(?:\s+[A-Z]\.?)?\s*[A-Z][a-z]+)', re.I
)

# --- Addresses ---
_RE_ADDRESS = re.compile(
    r'\b(\d{1,6}\s+(?:[A-Z][a-z]+\s+){1,3}'
    r'(?:St(?:reet)?|Ave(?:nue)?|Blvd|Dr(?:ive)?|Rd|Road|Ln|Lane|Ct|Court|Way|Pl|Place)'
    r'\.?(?:,?\s+(?:[A-Z][a-z]+\s*)+,?\s+[A-Z]{2}\s+\d{5})?)\b'
)

# --- Factual Allegations ---
_ALLEGATION_VERBS = re.compile(
    r'\b(failed\s+to|refused\s+to|violated|denied|harmed|neglected|'
    r'deliberately|intentionally|unlawfully|wrongfully|fraudulently|'
    r'knowingly|recklessly|willfully|improperly|arbitrarily)\b', re.I
)

# --- Exhibit / Evidence References ---
_RE_EXHIBIT = re.compile(r'\b(?:Exhibit|Ex\.?)\s+([A-Z0-9]+)', re.I)
_RE_EVIDENCE = re.compile(
    r'\b(?:attached\s+hereto|incorporated\s+by\s+reference|'
    r'see\s+(?:attached|exhibit|evidence))\b', re.I
)

# --- Court Proceedings Quotes ---
_RE_COURT_QUOTE = re.compile(r'THE\s+COURT:\s*(.+?)(?:\n|$)', re.I)
_RE_QA = re.compile(r'^[QA]\.\s+(.+)', re.M)

# --- Legal Issue Indicators ---
ISSUE_PATTERNS = {
    "due_process": re.compile(
        r'\b(?:due\s+process|procedural\s+(?:due\s+process|rights?)|'
        r'notice\s+and\s+(?:an?\s+)?(?:opportunity\s+to\s+be\s+heard|hearing)|'
        r'deprived?\s+of\s+(?:liberty|property|life)\s+without|'
        r'fundamentally?\s+unfair|arbitrary\s+and\s+capricious)\b', re.I
    ),
    "equal_protection": re.compile(
        r'\b(?:equal\s+protection|similarly\s+situated|'
        r'discriminat(?:ion|ed|ory)|disparate\s+treatment|'
        r'class\s+of\s+(?:one|persons))\b', re.I
    ),
    "judicial_misconduct": re.compile(
        r'\b(?:judicial\s+(?:misconduct|bias|prejudice|impropriety)|'
        r'ex\s+parte\s+(?:communication|contact)|'
        r'recus(?:e|al)|disqualif(?:y|ication)|'
        r'abuse\s+of\s+discretion|'
        r'predetermined|prejudged|partial(?:ity)?)\b', re.I
    ),
    "foc_misconduct": re.compile(
        r'\b(?:FOC|Friend\s+of\s+(?:the\s+)?Court)\b.*'
        r'(?:fail|refus|violat|neglect|improp|bias|misrepresent|error|wrong)', re.I
    ),
    "custody_interference": re.compile(
        r'\b(?:(?:custody|parenting\s+time)\s+(?:interference|denial|violation|withh[eo]ld)|'
        r'alienat(?:ion|ed|ing)|denied?\s+(?:access|visitation|parenting\s+time)|'
        r'parental\s+kidnapping|custodial\s+interference)\b', re.I
    ),
    "housing_habitability": re.compile(
        r'\b(?:habitability|uninhabitable|mold|(?:building|housing)\s+code\s+violation|'
        r'unsafe\s+(?:condition|living)|health\s+hazard|'
        r'failed?\s+to\s+(?:repair|maintain|address)|'
        r'MCL\s+554\.139|warranty\s+of\s+habitability)\b', re.I
    ),
    "civil_rights_1983": re.compile(
        r'\b(?:42\s*U\.?S\.?C\.?\s*§?\s*1983|section\s+1983|'
        r'civil\s+rights\s+(?:violation|claim|action)|'
        r'under\s+color\s+of\s+(?:state\s+)?law|'
        r'Monell|municipal\s+liability|'
        r'qualified\s+immunity|deliberate\s+indifference)\b', re.I
    ),
    "fraud": re.compile(
        r'\b(?:fraud(?:ulent)?|misrepresent(?:ation|ed)|'
        r'false\s+(?:statement|representation|testimony|claim)|'
        r'material\s+(?:omission|misstatement)|'
        r'decei(?:t|ve|ved)|conceale?(?:d|ment))\b', re.I
    ),
    "perjury": re.compile(
        r'\b(?:perjur(?:y|ed|ious)|false(?:ly)?\s+(?:swore?|testified?|stated?)|'
        r'lied?\s+under\s+oath|contradicted?\s+(?:sworn|prior)\s+(?:testimony|statement))\b', re.I
    ),
    "discovery_abuse": re.compile(
        r'\b(?:discovery\s+(?:abuse|violation|sanction)|'
        r'fail(?:ed|ure)?\s+to\s+(?:disclose|produce|respond\s+to\s+(?:interrogator|discovery))|'
        r'spoliat(?:ion|ed)|destroyed?\s+evidence|'
        r'withheld?\s+(?:evidence|document|information))\b', re.I
    ),
}

# --- Known Entities ---
KNOWN_CASE_NUMBERS = {
    "2024-001507-DC": "A",
    "2023-5907-PP": "A",
    "2025-002760-CZ": "C",
}
KNOWN_PARTIES = {
    "andrew pigors": ("person", "plaintiff", "A,B,C"),
    "pigors": ("person", "plaintiff", "A,B,C"),
    "watson": ("person", "defendant", "A"),
}
KNOWN_JUDGES = {
    "mcneill": ("person", "judge", "A"),
    "hoopes": ("person", "judge", "B"),
}
KNOWN_PROPERTIES = {
    "shady oaks": ("property", "subject_property", "B"),
}

# Lane assignment keywords (lightweight supplement to LocalAI lane detection)
LANE_KEYWORDS = {
    "A": {"custody", "parenting time", "child", "children", "mcneill",
           "watson", "2024-001507", "2023-5907", "best interest",
           "foc", "friend of the court", "visitation", "guardian ad litem",
           "CPS", "DHHS", "foster"},
    "B": {"housing", "habitability", "shady oaks", "hoopes", "mold",
           "landlord", "tenant", "MCL 554.139", "2023-5907-PP",
           "lease", "rent", "evict", "inspection", "repair", "code violation"},
    "C": {"1983", "civil rights", "monell", "convergence", "muskegon county",
           "14th circuit", "federal", "qualified immunity", "2025-002760",
           "under color of", "municipal liability", "pattern and practice"},
}


# ════════════════════════════════════════════════════════════════════════
#  Database Setup
# ════════════════════════════════════════════════════════════════════════

_SCHEMA_SQL = """
CREATE TABLE IF NOT EXISTS analyzed_files (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    path TEXT UNIQUE,
    file_type TEXT,
    page_count INTEGER,
    word_count INTEGER,
    legal_score INTEGER,
    analysis_timestamp TEXT,
    extraction_success BOOLEAN,
    error_message TEXT
);

CREATE TABLE IF NOT EXISTS citations (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    file_id INTEGER REFERENCES analyzed_files(id),
    citation_text TEXT,
    citation_type TEXT,
    rule_number TEXT,
    page_number INTEGER,
    line_number INTEGER,
    context TEXT,
    case_lane TEXT,
    verified BOOLEAN DEFAULT 0
);

CREATE TABLE IF NOT EXISTS factual_findings (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    file_id INTEGER REFERENCES analyzed_files(id),
    finding_type TEXT,
    finding_text TEXT,
    normalized_value TEXT,
    page_number INTEGER,
    line_number INTEGER,
    context TEXT,
    case_lane TEXT,
    admissibility_score INTEGER,
    relevance_score INTEGER,
    weight_score INTEGER,
    authentication_level TEXT
);

CREATE TABLE IF NOT EXISTS legal_issues (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    file_id INTEGER REFERENCES analyzed_files(id),
    issue_type TEXT,
    description TEXT,
    supporting_text TEXT,
    page_number INTEGER,
    line_number INTEGER,
    case_lane TEXT,
    strength_score INTEGER
);

CREATE TABLE IF NOT EXISTS entities (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    entity_type TEXT,
    entity_name TEXT,
    normalized_name TEXT,
    role TEXT,
    first_seen_file_id INTEGER,
    mention_count INTEGER DEFAULT 1,
    case_lanes TEXT
);

CREATE TABLE IF NOT EXISTS evidence_chain (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    finding_id INTEGER REFERENCES factual_findings(id),
    supports_issue_id INTEGER REFERENCES legal_issues(id),
    connection_type TEXT,
    strength INTEGER,
    explanation TEXT
);

CREATE TABLE IF NOT EXISTS analysis_summary (
    case_lane TEXT PRIMARY KEY,
    total_files INTEGER,
    total_citations INTEGER,
    total_findings INTEGER,
    total_issues INTEGER,
    strongest_claims TEXT,
    weakest_areas TEXT,
    recommended_actions TEXT
);

CREATE INDEX IF NOT EXISTS idx_citations_file ON citations(file_id);
CREATE INDEX IF NOT EXISTS idx_citations_type ON citations(citation_type);
CREATE INDEX IF NOT EXISTS idx_citations_lane ON citations(case_lane);
CREATE INDEX IF NOT EXISTS idx_findings_file ON factual_findings(file_id);
CREATE INDEX IF NOT EXISTS idx_findings_type ON factual_findings(finding_type);
CREATE INDEX IF NOT EXISTS idx_findings_lane ON factual_findings(case_lane);
CREATE INDEX IF NOT EXISTS idx_issues_file ON legal_issues(file_id);
CREATE INDEX IF NOT EXISTS idx_issues_type ON legal_issues(issue_type);
CREATE INDEX IF NOT EXISTS idx_issues_lane ON legal_issues(case_lane);
CREATE INDEX IF NOT EXISTS idx_entities_type ON entities(entity_type);
CREATE INDEX IF NOT EXISTS idx_entities_name ON entities(normalized_name);
CREATE INDEX IF NOT EXISTS idx_chain_finding ON evidence_chain(finding_id);
CREATE INDEX IF NOT EXISTS idx_chain_issue ON evidence_chain(supports_issue_id);
"""


def init_db(db_path: Path = ANALYSIS_DB_PATH) -> sqlite3.Connection:
    """Create or connect to the analysis database."""
    db_path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(db_path), timeout=30)
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA foreign_keys=ON")
    conn.executescript(_SCHEMA_SQL)
    conn.commit()
    return conn


# ════════════════════════════════════════════════════════════════════════
#  Text Extraction
# ════════════════════════════════════════════════════════════════════════

def extract_pdf(path: str) -> Tuple[str, int]:
    """Extract text from a PDF. Returns (full_text_with_page_markers, page_count)."""
    if _PDF_ENGINE == "pdfplumber":
        return _extract_pdf_pdfplumber(path)
    elif _PDF_ENGINE == "PyPDF2":
        return _extract_pdf_pypdf2(path)
    else:
        return _extract_pdf_fallback(path)


def _extract_pdf_pdfplumber(path: str) -> Tuple[str, int]:
    import pdfplumber
    pages = []
    try:
        with pdfplumber.open(path) as pdf:
            for i, page in enumerate(pdf.pages, 1):
                text = page.extract_text() or ""
                pages.append(f"[PAGE {i}]\n{text}")
            return "\n\n".join(pages), len(pdf.pages)
    except Exception as e:
        raise RuntimeError(f"pdfplumber failed on {path}: {e}")


def _extract_pdf_pypdf2(path: str) -> Tuple[str, int]:
    from PyPDF2 import PdfReader
    pages = []
    try:
        reader = PdfReader(path)
        for i, page in enumerate(reader.pages, 1):
            text = page.extract_text() or ""
            pages.append(f"[PAGE {i}]\n{text}")
        return "\n\n".join(pages), len(reader.pages)
    except Exception as e:
        raise RuntimeError(f"PyPDF2 failed on {path}: {e}")


def _extract_pdf_fallback(path: str) -> Tuple[str, int]:
    """Last-resort fallback: try subprocess with Python's built-in capabilities."""
    try:
        import subprocess
        result = subprocess.run(
            [sys.executable, "-c",
             f"from PyPDF2 import PdfReader; r=PdfReader(r'{path}'); "
             f"[print(f'[PAGE {{i+1}}]\\n{{p.extract_text() or \"\"}}') for i,p in enumerate(r.pages)]"],
            capture_output=True, text=True, timeout=60
        )
        if result.returncode == 0 and result.stdout.strip():
            page_count = result.stdout.count("[PAGE ")
            return result.stdout, max(page_count, 1)
    except Exception:
        pass
    raise RuntimeError(
        f"No PDF library available. Install pdfplumber or PyPDF2: pip install pdfplumber"
    )


def extract_docx(path: str) -> Tuple[str, int]:
    """Extract text from a DOCX. Returns (full_text, 1) — DOCX has no page concept."""
    if _HAS_DOCX:
        return _extract_docx_native(path)
    return _extract_docx_fallback(path)


def _extract_docx_native(path: str) -> Tuple[str, int]:
    from docx import Document as DocxDocument
    try:
        doc = DocxDocument(path)
        paragraphs = [p.text for p in doc.paragraphs if p.text.strip()]
        return "\n".join(paragraphs), 1
    except Exception as e:
        raise RuntimeError(f"python-docx failed on {path}: {e}")


def _extract_docx_fallback(path: str) -> Tuple[str, int]:
    """Fallback: extract from DOCX XML directly (standard library only)."""
    import zipfile
    from xml.etree import ElementTree
    try:
        with zipfile.ZipFile(path, "r") as z:
            with z.open("word/document.xml") as f:
                tree = ElementTree.parse(f)
        ns = {"w": "http://schemas.openxmlformats.org/wordprocessingml/2006/main"}
        paragraphs = []
        for p in tree.iter(f"{{{ns['w']}}}p"):
            texts = [t.text for t in p.iter(f"{{{ns['w']}}}t") if t.text]
            if texts:
                paragraphs.append("".join(texts))
        return "\n".join(paragraphs), 1
    except Exception as e:
        raise RuntimeError(f"DOCX fallback failed on {path}: {e}")


def extract_text_file(path: str) -> Tuple[str, int]:
    """Extract text from TXT/MD/CSV with encoding detection."""
    encodings = ["utf-8", "utf-8-sig", "latin-1", "cp1252", "ascii"]
    for enc in encodings:
        try:
            with open(path, "r", encoding=enc, errors="strict") as f:
                text = f.read()
            return text, 1
        except (UnicodeDecodeError, UnicodeError):
            continue
    # Final fallback with replacement
    with open(path, "r", encoding="utf-8", errors="replace") as f:
        return f.read(), 1


def extract_file(path: str) -> Tuple[str, int, str]:
    """
    Extract text from any supported file.
    Returns (text, page_count, file_type).
    Raises RuntimeError on failure.
    """
    ext = os.path.splitext(path)[1].lower()
    if ext == ".pdf":
        text, pages = extract_pdf(path)
        return text, pages, "pdf"
    elif ext == ".docx":
        text, pages = extract_docx(path)
        return text, pages, "docx"
    elif ext in (".txt", ".md", ".csv", ".log", ".rtf", ".text", ".rst"):
        text, pages = extract_text_file(path)
        return text, pages, ext.lstrip(".")
    else:
        # Try as text
        text, pages = extract_text_file(path)
        return text, pages, ext.lstrip(".") or "unknown"


# ════════════════════════════════════════════════════════════════════════
#  Date Parsing
# ════════════════════════════════════════════════════════════════════════

_MONTH_MAP = {
    "january": 1, "february": 2, "march": 3, "april": 4,
    "may": 5, "june": 6, "july": 7, "august": 8,
    "september": 9, "october": 10, "november": 11, "december": 12,
    "jan": 1, "feb": 2, "mar": 3, "apr": 4,
    "jun": 6, "jul": 7, "aug": 8, "sep": 9, "oct": 10, "nov": 11, "dec": 12,
}


def parse_date_to_iso(text: str) -> Optional[str]:
    """Attempt to parse a date string into ISO 8601 format."""
    text = text.strip().rstrip(",")
    # ISO format
    m = re.match(r'^(\d{4})-(\d{2})-(\d{2})$', text)
    if m:
        return text
    # US format M/D/YYYY
    m = re.match(r'^(\d{1,2})/(\d{1,2})/(\d{2,4})$', text)
    if m:
        month, day, year = int(m.group(1)), int(m.group(2)), int(m.group(3))
        if year < 100:
            year += 2000 if year < 50 else 1900
        try:
            return f"{year:04d}-{month:02d}-{day:02d}"
        except ValueError:
            return None
    # Long/abbreviated month format
    m = re.match(r'^([A-Za-z]+)\.?\s+(\d{1,2}),?\s+(\d{4})$', text)
    if m:
        month_str = m.group(1).lower().rstrip(".")
        month_num = _MONTH_MAP.get(month_str)
        if month_num:
            return f"{int(m.group(3)):04d}-{month_num:02d}-{int(m.group(2)):02d}"
    return None


# ════════════════════════════════════════════════════════════════════════
#  Line-by-Line Analyzer
# ════════════════════════════════════════════════════════════════════════

class LineAnalyzer:
    """Extracts structured legal intelligence from a single line of text."""

    def __init__(self):
        self._entity_cache: Dict[str, dict] = {}

    def analyze_line(
        self, line: str, line_num: int, page_num: int, full_text: str
    ) -> dict:
        """
        Analyze one line of text and return all findings.
        full_text is provided for context-window lookups.
        """
        result = {
            "citations": [],
            "findings": [],
            "issues": [],
        }
        stripped = line.strip()
        if not stripped or len(stripped) < 3:
            return result

        context = self._get_context(line, full_text)

        # --- Citations ---
        self._extract_citations(stripped, line_num, page_num, context, result)

        # --- Factual Findings ---
        self._extract_facts(stripped, line_num, page_num, context, result)

        # --- Legal Issues ---
        self._extract_issues(stripped, line_num, page_num, context, result)

        return result

    @staticmethod
    def _get_context(line: str, full_text: str) -> str:
        """Get surrounding context for a line (±200 chars)."""
        pos = full_text.find(line)
        if pos < 0:
            return line
        start = max(0, pos - 200)
        end = min(len(full_text), pos + len(line) + 200)
        return full_text[start:end]

    def _extract_citations(
        self, line: str, line_num: int, page_num: int, context: str,
        result: dict
    ):
        """Extract all legal citations from a line."""
        # MCR
        for m in _RE_MCR.finditer(line):
            result["citations"].append({
                "citation_text": m.group(0),
                "citation_type": "mcr",
                "rule_number": m.group(1),
                "page_number": page_num,
                "line_number": line_num,
                "context": context[:500],
            })

        # MCL
        for m in _RE_MCL.finditer(line):
            result["citations"].append({
                "citation_text": m.group(0),
                "citation_type": "mcl",
                "rule_number": m.group(1),
                "page_number": page_num,
                "line_number": line_num,
                "context": context[:500],
            })

        # MRE
        for m in _RE_MRE.finditer(line):
            result["citations"].append({
                "citation_text": m.group(0),
                "citation_type": "mre",
                "rule_number": m.group(1),
                "page_number": page_num,
                "line_number": line_num,
                "context": context[:500],
            })

        # Federal statutes
        for m in _RE_FEDERAL_STATUTE.finditer(line):
            title, section = m.group(1), m.group(2)
            result["citations"].append({
                "citation_text": m.group(0),
                "citation_type": "statute",
                "rule_number": f"{title} USC {section}",
                "page_number": page_num,
                "line_number": line_num,
                "context": context[:500],
            })

        # Case law
        for m in _RE_CASE_LAW.finditer(line):
            # Only keep if it looks like a real citation (has reporter info or known case)
            plaintiff = m.group(1)
            defendant = m.group(2)
            reporter = m.group(4) if m.lastindex and m.lastindex >= 4 else None
            cite_text = m.group(0).strip()
            # Filter false positives: require reporter or known party names
            if reporter or any(
                k in cite_text.lower()
                for k in ("pigors", "watson", "mich", "nw2d", "f.3d", "u.s.")
            ):
                result["citations"].append({
                    "citation_text": cite_text,
                    "citation_type": "case_law",
                    "rule_number": f"{plaintiff} v. {defendant}",
                    "page_number": page_num,
                    "line_number": line_num,
                    "context": context[:500],
                })

        # Michigan Constitution
        for m in _RE_CONST_MI.finditer(line):
            result["citations"].append({
                "citation_text": m.group(0),
                "citation_type": "constitutional",
                "rule_number": f"Const 1963 art {m.group(1)} § {m.group(2)}",
                "page_number": page_num,
                "line_number": line_num,
                "context": context[:500],
            })

        # US Constitution
        for m in _RE_CONST_US.finditer(line):
            amend = m.group(1) or ""
            art = m.group(2) or ""
            ref = f"amend {amend}" if amend else f"art {art}"
            result["citations"].append({
                "citation_text": m.group(0),
                "citation_type": "constitutional",
                "rule_number": f"US Const {ref}",
                "page_number": page_num,
                "line_number": line_num,
                "context": context[:500],
            })

    def _extract_facts(
        self, line: str, line_num: int, page_num: int, context: str,
        result: dict
    ):
        """Extract factual findings from a line."""
        # Dates
        for m in _RE_DATE_ISO.finditer(line):
            iso = parse_date_to_iso(m.group(1))
            if iso:
                result["findings"].append(self._finding(
                    "date", m.group(0), iso, page_num, line_num, context
                ))
        for m in _RE_DATE_US.finditer(line):
            raw = f"{m.group(1)}/{m.group(2)}/{m.group(3)}"
            iso = parse_date_to_iso(raw)
            if iso:
                result["findings"].append(self._finding(
                    "date", raw, iso, page_num, line_num, context
                ))
        for m in _RE_DATE_LONG.finditer(line):
            iso = parse_date_to_iso(m.group(1))
            if iso:
                result["findings"].append(self._finding(
                    "date", m.group(1), iso, page_num, line_num, context
                ))
        for m in _RE_DATE_MDY.finditer(line):
            iso = parse_date_to_iso(m.group(1))
            if iso:
                result["findings"].append(self._finding(
                    "date", m.group(1), iso, page_num, line_num, context
                ))

        # Dollar amounts
        for m in _RE_DOLLAR.finditer(line):
            raw = m.group(1)
            normalized = raw.replace(",", "")
            result["findings"].append(self._finding(
                "amount", f"${raw}", normalized, page_num, line_num, context
            ))

        # People / Names
        for m in _RE_JUDGE.finditer(line):
            name = m.group(1).strip()
            result["findings"].append(self._finding(
                "person", name, name.lower(), page_num, line_num, context,
                auth="self-authenticating"
            ))

        # Addresses
        for m in _RE_ADDRESS.finditer(line):
            result["findings"].append(self._finding(
                "location", m.group(0).strip(), m.group(0).strip().lower(),
                page_num, line_num, context
            ))

        # Case numbers
        for m in _RE_CASE_NUM.finditer(line):
            result["findings"].append(self._finding(
                "case_number", m.group(1), m.group(1),
                page_num, line_num, context,
                auth="self-authenticating"
            ))

        # Factual allegations
        for m in _ALLEGATION_VERBS.finditer(line):
            # Capture the full sentence containing the allegation verb
            result["findings"].append(self._finding(
                "allegation", line.strip(), m.group(1).lower(),
                page_num, line_num, context
            ))

        # Court quotes
        for m in _RE_COURT_QUOTE.finditer(line):
            result["findings"].append(self._finding(
                "quote", m.group(0).strip(), m.group(1).strip(),
                page_num, line_num, context,
                auth="self-authenticating"
            ))

        # Exhibit references
        for m in _RE_EXHIBIT.finditer(line):
            result["findings"].append(self._finding(
                "exhibit_ref", m.group(0), f"Exhibit {m.group(1)}",
                page_num, line_num, context
            ))

    def _extract_issues(
        self, line: str, line_num: int, page_num: int, context: str,
        result: dict
    ):
        """Detect legal issues in a line."""
        for issue_type, pattern in ISSUE_PATTERNS.items():
            m = pattern.search(line)
            if m:
                # Score the strength based on keyword specificity
                strength = self._score_issue_strength(issue_type, line, context)
                result["issues"].append({
                    "issue_type": issue_type,
                    "description": f"{issue_type.replace('_', ' ').title()} indicator",
                    "supporting_text": line.strip()[:500],
                    "page_number": page_num,
                    "line_number": line_num,
                    "strength_score": strength,
                })

    @staticmethod
    def _score_issue_strength(issue_type: str, line: str, context: str) -> int:
        """Score 0-100 how strong a legal issue indicator is."""
        score = 30  # Base: pattern matched
        text = (line + " " + context).lower()

        # Boost: multiple legal terms present
        legal_terms = len(re.findall(
            r'\b(?:mcl|mcr|usc|statute|court|order|motion|evidence|'
            r'plaintiff|defendant|judge|violated?|denied?|rights?)\b',
            text, re.I
        ))
        score += min(legal_terms * 5, 30)

        # Boost: specific case references
        for case_num in KNOWN_CASE_NUMBERS:
            if case_num in text:
                score += 10

        # Boost: specific party/judge names
        for name in ("pigors", "watson", "mcneill", "hoopes", "shady oaks"):
            if name in text:
                score += 5

        # Boost: allegation verbs present
        if _ALLEGATION_VERBS.search(text):
            score += 10

        return min(score, 100)

    @staticmethod
    def _finding(
        finding_type: str, text: str, normalized: str,
        page: int, line: int, context: str,
        auth: str = "needs foundation"
    ) -> dict:
        """Build a finding dict with evidence quality scoring."""
        admissibility = _score_admissibility(finding_type, text, context, auth)
        relevance = _score_relevance(text, context)
        weight = _score_weight(finding_type, text, context)
        return {
            "finding_type": finding_type,
            "finding_text": text[:1000],
            "normalized_value": str(normalized)[:500],
            "page_number": page,
            "line_number": line,
            "context": context[:500],
            "admissibility_score": admissibility,
            "relevance_score": relevance,
            "weight_score": weight,
            "authentication_level": auth,
        }


# ════════════════════════════════════════════════════════════════════════
#  Evidence Quality Scoring
# ════════════════════════════════════════════════════════════════════════

def _score_admissibility(
    finding_type: str, text: str, context: str, auth: str
) -> int:
    """Score 0-100: would this survive an evidence objection?"""
    score = 40  # Base
    if auth == "self-authenticating":
        score += 30
    elif auth == "needs foundation":
        score += 10

    # Court documents are more admissible
    ctx_lower = context.lower()
    if any(w in ctx_lower for w in ("court", "order", "filed", "certified")):
        score += 15
    # Official records boost
    if any(w in ctx_lower for w in ("official", "record", "transcript", "clerk")):
        score += 10
    # Hearsay concern for quotes/allegations
    if finding_type in ("allegation", "quote") and "said" in ctx_lower:
        score -= 15

    return max(0, min(score, 100))


def _score_relevance(text: str, context: str) -> int:
    """Score 0-100: how relevant to the three case lanes?"""
    score = 20  # Base
    combined = (text + " " + context).lower()

    # Direct case references
    for case_num, lane in KNOWN_CASE_NUMBERS.items():
        if case_num in combined:
            score += 25
    # Party/judge names
    for name in ("pigors", "watson", "mcneill", "hoopes", "shady oaks"):
        if name in combined:
            score += 10
    # Legal terms
    legal_hits = len(re.findall(
        r'\b(?:custody|housing|civil rights|due process|mold|habitability|'
        r'parenting time|1983|monell)\b', combined
    ))
    score += min(legal_hits * 8, 25)

    return min(score, 100)


def _score_weight(finding_type: str, text: str, context: str) -> int:
    """Score 0-100: how persuasive is this evidence?"""
    score = 25
    combined = (text + " " + context).lower()

    # Stronger types
    type_weights = {
        "quote": 20, "case_number": 15, "allegation": 15,
        "date": 10, "amount": 10, "person": 5, "location": 5,
        "exhibit_ref": 15,
    }
    score += type_weights.get(finding_type, 5)

    # Specificity bonus
    if any(c.isdigit() for c in text):
        score += 5
    if len(text) > 50:
        score += 5

    # Corroboration hints
    if "exhibit" in combined or "attached" in combined:
        score += 10
    if "sworn" in combined or "under oath" in combined:
        score += 15

    return min(score, 100)


# ════════════════════════════════════════════════════════════════════════
#  Case Lane Assignment
# ════════════════════════════════════════════════════════════════════════

def assign_lane(text: str, context: str = "") -> str:
    """Determine which case lane(s) a finding belongs to. Returns comma-separated."""
    combined = (text + " " + context).lower()
    scores = {"A": 0, "B": 0, "C": 0}

    # Check known entities
    for case_num, lane in KNOWN_CASE_NUMBERS.items():
        if case_num in combined:
            scores[lane] += 20

    for name, (_, _, lanes) in {**KNOWN_JUDGES, **KNOWN_PROPERTIES}.items():
        if name in combined:
            for lane in lanes.split(","):
                scores[lane.strip()] += 15

    # Keyword matching
    for lane, keywords in LANE_KEYWORDS.items():
        for kw in keywords:
            if kw.lower() in combined:
                scores[lane] += 5

    # Use LocalAI if available for tiebreaking
    if _HAS_AI and max(scores.values()) < 10:
        try:
            ai_result = _AI.detect_lane(combined[:3000])
            detected = ai_result.get("lane", "unknown")
            if detected in scores:
                scores[detected] += 10
        except Exception:
            pass

    # Return lanes with non-trivial scores
    threshold = 5
    active = [lane for lane, s in sorted(scores.items()) if s >= threshold]
    if not active:
        # Default assignment based on strongest keyword
        best = max(scores, key=scores.get)
        if scores[best] > 0:
            return best
        return "A,B,C"  # Potentially relevant to all
    return ",".join(active)


# ════════════════════════════════════════════════════════════════════════
#  File Prioritization (reads manifest DBs)
# ════════════════════════════════════════════════════════════════════════

def discover_manifest_dbs() -> List[Path]:
    """Find all drive manifest databases."""
    if not MANIFEST_DIR.exists():
        return []
    return sorted(MANIFEST_DIR.glob("drive_*_manifest.db"))


def load_prioritized_files(
    conn_analysis: sqlite3.Connection, lane_filter: Optional[str] = None
) -> List[dict]:
    """
    Read all manifest DBs, rank files by analysis value, skip already-analyzed.
    Returns list of dicts: {path, extension, size_bytes, legal_score, priority_rank}.
    """
    already_analyzed = set()
    try:
        rows = conn_analysis.execute("SELECT path FROM analyzed_files").fetchall()
        already_analyzed = {r[0] for r in rows}
    except sqlite3.OperationalError:
        pass

    all_files = []
    for db_path in discover_manifest_dbs():
        try:
            mconn = sqlite3.connect(str(db_path), timeout=10)
            mconn.row_factory = sqlite3.Row
            rows = mconn.execute(
                "SELECT path, extension, size_bytes, legal_score, category "
                "FROM files WHERE is_trash = 0 AND is_empty = 0 AND is_corrupt = 0"
            ).fetchall()
            for r in rows:
                rec = dict(r)
                if rec["path"] in already_analyzed:
                    continue
                all_files.append(rec)
            mconn.close()
        except Exception as e:
            print(f"  [WARN] Could not read {db_path.name}: {e}")

    # Apply lane filter if requested (keyword heuristic on path)
    if lane_filter:
        lane_kw = LANE_KEYWORDS.get(lane_filter.upper(), set())
        if lane_kw:
            filtered = []
            for f in all_files:
                path_lower = f["path"].lower()
                if any(kw in path_lower for kw in lane_kw):
                    filtered.append(f)
                else:
                    # Keep high-score files regardless
                    if f.get("legal_score", 0) and f["legal_score"] > 30:
                        filtered.append(f)
            if filtered:
                all_files = filtered

    # Priority ranking
    def priority_key(f):
        ext = (f.get("extension") or "").lower()
        score = f.get("legal_score") or 0
        # Priority tiers: lower = higher priority
        if ext == ".pdf" and score > 20:
            tier = 0
        elif ext == ".txt" and score > 20:
            tier = 1
        elif ext == ".docx":
            tier = 2
        elif ext == ".pdf":
            tier = 3
        elif ext in (".txt", ".md"):
            tier = 4
        else:
            tier = 5
        return (tier, -score, f.get("size_bytes", 0))

    all_files.sort(key=priority_key)

    # Add priority rank and estimated processing time
    for i, f in enumerate(all_files):
        f["priority_rank"] = i + 1
        size_mb = (f.get("size_bytes") or 0) / (1024 * 1024)
        # Rough estimate: ~2 sec/MB for text, ~5 sec/MB for PDF
        ext = (f.get("extension") or "").lower()
        if ext == ".pdf":
            f["est_seconds"] = max(1, int(size_mb * 5))
        elif ext == ".docx":
            f["est_seconds"] = max(1, int(size_mb * 3))
        else:
            f["est_seconds"] = max(1, int(size_mb * 2))

    return all_files


# ════════════════════════════════════════════════════════════════════════
#  Entity Tracking
# ════════════════════════════════════════════════════════════════════════

class EntityTracker:
    """Deduplicates and tracks entities across all analyzed files."""

    def __init__(self, conn: sqlite3.Connection):
        self.conn = conn
        self._cache: Dict[str, int] = {}  # normalized_name -> entity id
        self._load_existing()

    def _load_existing(self):
        try:
            rows = self.conn.execute(
                "SELECT id, normalized_name FROM entities"
            ).fetchall()
            for row in rows:
                self._cache[row[1]] = row[0]
        except sqlite3.OperationalError:
            pass

    def track(
        self, entity_name: str, entity_type: str, role: str,
        file_id: int, case_lanes: str
    ) -> int:
        """Record or update an entity. Returns entity id."""
        normalized = entity_name.strip().lower()
        if not normalized:
            return -1

        # Check known entities first
        detected_type, detected_role, detected_lanes = entity_type, role, case_lanes
        for known_name, (kt, kr, kl) in {
            **KNOWN_PARTIES, **KNOWN_JUDGES, **KNOWN_PROPERTIES
        }.items():
            if known_name in normalized:
                detected_type = kt
                detected_role = kr
                detected_lanes = kl
                break

        if normalized in self._cache:
            eid = self._cache[normalized]
            self.conn.execute(
                "UPDATE entities SET mention_count = mention_count + 1, "
                "case_lanes = ? WHERE id = ? AND "
                "(case_lanes IS NULL OR case_lanes NOT LIKE ?)",
                (detected_lanes, eid, f"%{detected_lanes}%")
            )
            # Also update if lanes differ
            self.conn.execute(
                "UPDATE entities SET mention_count = mention_count + 1 "
                "WHERE id = ? AND case_lanes LIKE ?",
                (eid, f"%{detected_lanes}%")
            )
            return eid

        cursor = self.conn.execute(
            "INSERT INTO entities "
            "(entity_type, entity_name, normalized_name, role, "
            "first_seen_file_id, mention_count, case_lanes) "
            "VALUES (?, ?, ?, ?, ?, 1, ?)",
            (detected_type, entity_name.strip(), normalized,
             detected_role, file_id, detected_lanes)
        )
        eid = cursor.lastrowid
        self._cache[normalized] = eid
        return eid


# ════════════════════════════════════════════════════════════════════════
#  Evidence Chain Builder
# ════════════════════════════════════════════════════════════════════════

def build_evidence_chains(conn: sqlite3.Connection):
    """
    Link factual findings to legal issues they support.
    Runs after all files are analyzed.
    """
    print("\n[CHAIN] Building evidence chains...")

    # Get all findings and issues
    findings = conn.execute(
        "SELECT id, finding_type, finding_text, context, case_lane "
        "FROM factual_findings"
    ).fetchall()
    issues = conn.execute(
        "SELECT id, issue_type, supporting_text, case_lane "
        "FROM legal_issues"
    ).fetchall()

    if not findings or not issues:
        print("  [CHAIN] No findings or issues to link.")
        return

    chains_added = 0
    for f_id, f_type, f_text, f_ctx, f_lane in findings:
        f_combined = ((f_text or "") + " " + (f_ctx or "")).lower()
        for i_id, i_type, i_text, i_lane in issues:
            # Must share at least one lane
            if f_lane and i_lane:
                f_lanes = set(f_lane.split(","))
                i_lanes = set(i_lane.split(","))
                if not f_lanes & i_lanes:
                    continue

            connection, strength = _assess_connection(
                f_type, f_combined, i_type, (i_text or "").lower()
            )
            if connection and strength >= 30:
                try:
                    conn.execute(
                        "INSERT INTO evidence_chain "
                        "(finding_id, supports_issue_id, connection_type, "
                        "strength, explanation) VALUES (?, ?, ?, ?, ?)",
                        (f_id, i_id, connection, strength,
                         f"{f_type} supports {i_type} claim")
                    )
                    chains_added += 1
                except sqlite3.IntegrityError:
                    pass

    conn.commit()
    print(f"  [CHAIN] Linked {chains_added} evidence connections.")


def _assess_connection(
    finding_type: str, finding_text: str,
    issue_type: str, issue_text: str
) -> Tuple[Optional[str], int]:
    """Determine if a finding supports an issue, and how strongly."""
    # Map finding types to issue types they naturally support
    relevance_map = {
        ("allegation", "due_process"): ("direct", 60),
        ("allegation", "equal_protection"): ("direct", 55),
        ("allegation", "judicial_misconduct"): ("direct", 65),
        ("allegation", "foc_misconduct"): ("direct", 60),
        ("allegation", "custody_interference"): ("direct", 60),
        ("allegation", "housing_habitability"): ("direct", 55),
        ("allegation", "civil_rights_1983"): ("direct", 50),
        ("allegation", "fraud"): ("direct", 65),
        ("allegation", "perjury"): ("direct", 70),
        ("allegation", "discovery_abuse"): ("direct", 60),
        ("quote", "judicial_misconduct"): ("direct", 70),
        ("quote", "perjury"): ("impeachment", 65),
        ("date", "due_process"): ("corroborative", 35),
        ("date", "discovery_abuse"): ("corroborative", 40),
        ("amount", "housing_habitability"): ("corroborative", 45),
        ("amount", "fraud"): ("direct", 55),
        ("exhibit_ref", "discovery_abuse"): ("corroborative", 40),
        ("case_number", "civil_rights_1983"): ("corroborative", 35),
    }

    key = (finding_type, issue_type)
    if key in relevance_map:
        conn_type, base_strength = relevance_map[key]
        # Boost if texts share significant words
        f_words = set(re.findall(r'\b[a-z]{4,}\b', finding_text))
        i_words = set(re.findall(r'\b[a-z]{4,}\b', issue_text))
        overlap = len(f_words & i_words)
        boost = min(overlap * 3, 20)
        return conn_type, min(base_strength + boost, 100)

    # Generic weak connection if same lane
    return None, 0


# ════════════════════════════════════════════════════════════════════════
#  Main Analysis Engine
# ════════════════════════════════════════════════════════════════════════

class AnalysisEngine:
    """Core document analysis engine."""

    def __init__(self, db_path: Path = ANALYSIS_DB_PATH):
        self.db_path = db_path
        self.conn = init_db(db_path)
        self.analyzer = LineAnalyzer()
        self.entity_tracker = EntityTracker(self.conn)
        self.stats = {
            "files_processed": 0,
            "files_skipped": 0,
            "files_errored": 0,
            "citations_found": 0,
            "findings_found": 0,
            "issues_found": 0,
            "start_time": None,
        }

    def close(self):
        if self.conn:
            self.conn.commit()
            self.conn.close()

    # ── Scan: Prioritize files from manifests ────────────────────
    def cmd_scan(self, lane_filter: Optional[str] = None):
        """Discover and prioritize files from manifest databases."""
        print("=" * 70)
        print("  DOCUMENT ANALYSIS ENGINE — File Scan & Prioritization")
        print("=" * 70)

        manifests = discover_manifest_dbs()
        if not manifests:
            print("\n  [ERROR] No manifest databases found in:")
            print(f"          {MANIFEST_DIR}")
            print("  Run the drive scanner first.")
            return

        print(f"\n  Found {len(manifests)} manifest DB(s):")
        for m in manifests:
            print(f"    • {m.name}")

        files = load_prioritized_files(self.conn, lane_filter)
        if not files:
            print("\n  [INFO] No new files to analyze (all previously analyzed or no matches).")
            return

        # Stats
        ext_counts = Counter(f.get("extension", "?") for f in files)
        high_legal = sum(1 for f in files if (f.get("legal_score") or 0) > 20)
        total_size = sum(f.get("size_bytes", 0) for f in files)
        total_est = sum(f.get("est_seconds", 0) for f in files)

        print(f"\n  Prioritized {len(files)} files for analysis:")
        print(f"    High legal score (>20): {high_legal}")
        for ext, cnt in ext_counts.most_common(10):
            print(f"    {ext or '(none)':>8}: {cnt:>6} files")
        print(f"    Total size: {total_size / (1024*1024):.1f} MB")
        print(f"    Est. processing time: {total_est // 60}m {total_est % 60}s")

        if lane_filter:
            print(f"    Lane filter: {lane_filter}")

        # Show top 20
        print(f"\n  Top 20 priority files:")
        for f in files[:20]:
            score = f.get("legal_score", 0)
            size_kb = (f.get("size_bytes") or 0) / 1024
            name = os.path.basename(f["path"])
            print(f"    [{score:>3}] {name[:60]:<60} ({size_kb:.0f} KB)")

        print(f"\n  [OK] Scan complete. Run 'analyze' to process these files.")

    # ── Analyze: Full document analysis ──────────────────────────
    def cmd_analyze(self, lane_filter: Optional[str] = None):
        """Run full line-by-line analysis on prioritized files."""
        print("=" * 70)
        print("  DOCUMENT ANALYSIS ENGINE — Full Analysis")
        print("=" * 70)

        files = load_prioritized_files(self.conn, lane_filter)
        if not files:
            print("\n  [INFO] No files to analyze.")
            return

        total = len(files)
        print(f"\n  Processing {total} files...")
        if lane_filter:
            print(f"  Lane filter: {lane_filter}")
        print()

        self.stats["start_time"] = time.time()
        batch_count = 0

        for i, file_rec in enumerate(files):
            path = file_rec["path"]
            try:
                self._analyze_one_file(file_rec)
                self.stats["files_processed"] += 1
            except Exception as e:
                self.stats["files_errored"] += 1
                self._record_error(path, file_rec, str(e))
                if i < 5:
                    # Show first few errors in detail
                    print(f"  [ERR] {os.path.basename(path)}: {e}")

            batch_count += 1
            if batch_count >= BATCH_SIZE:
                self.conn.commit()
                batch_count = 0

            if (i + 1) % PROGRESS_INTERVAL == 0 or (i + 1) == total:
                elapsed = time.time() - self.stats["start_time"]
                rate = (i + 1) / max(elapsed, 0.1)
                remaining = (total - i - 1) / max(rate, 0.01)
                print(
                    f"  [{i+1:>5}/{total}] "
                    f"OK:{self.stats['files_processed']} "
                    f"ERR:{self.stats['files_errored']} "
                    f"Citations:{self.stats['citations_found']} "
                    f"Findings:{self.stats['findings_found']} "
                    f"Issues:{self.stats['issues_found']} "
                    f"({elapsed:.0f}s elapsed, ~{remaining:.0f}s remaining)"
                )

        # Final commit
        self.conn.commit()

        # Build evidence chains
        build_evidence_chains(self.conn)

        # Summary
        elapsed = time.time() - self.stats["start_time"]
        print(f"\n  ── Analysis Complete ──")
        print(f"  Files processed: {self.stats['files_processed']}")
        print(f"  Files errored:   {self.stats['files_errored']}")
        print(f"  Citations found: {self.stats['citations_found']}")
        print(f"  Findings found:  {self.stats['findings_found']}")
        print(f"  Issues found:    {self.stats['issues_found']}")
        print(f"  Total time:      {elapsed:.1f}s")
        print(f"  Database:        {self.db_path}")

    def _analyze_one_file(self, file_rec: dict):
        """Extract text and run line-by-line analysis on a single file."""
        path = file_rec["path"]
        if not os.path.isfile(path):
            raise FileNotFoundError(f"File not found: {path}")

        # Extract text
        text, page_count, file_type = extract_file(path)
        if not text or not text.strip():
            raise RuntimeError("No text extracted")

        word_count = len(text.split())

        # Compute overall legal score via LocalAI if available
        legal_score = file_rec.get("legal_score") or 0
        if _HAS_AI:
            try:
                ev = _AI.score_evidence(text[:5000], "legal document analysis")
                legal_score = max(legal_score, ev.get("score", 0))
            except Exception:
                pass

        # Record the file
        now = datetime.datetime.now().isoformat()
        cursor = self.conn.execute(
            "INSERT OR REPLACE INTO analyzed_files "
            "(path, file_type, page_count, word_count, legal_score, "
            "analysis_timestamp, extraction_success, error_message) "
            "VALUES (?, ?, ?, ?, ?, ?, 1, NULL)",
            (path, file_type, page_count, word_count, legal_score, now)
        )
        file_id = cursor.lastrowid

        # Parse page structure for PDFs
        pages = self._split_pages(text)

        # Line-by-line analysis
        all_citations = []
        all_findings = []
        all_issues = []

        for page_num, page_text in pages:
            lines = page_text.split("\n")
            for line_idx, line in enumerate(lines, 1):
                if len(line.strip()) < 3:
                    continue
                result = self.analyzer.analyze_line(
                    line, line_idx, page_num, text
                )
                for c in result["citations"]:
                    c["case_lane"] = assign_lane(
                        c["citation_text"], c.get("context", "")
                    )
                    all_citations.append(c)

                for f in result["findings"]:
                    f["case_lane"] = assign_lane(
                        f["finding_text"], f.get("context", "")
                    )
                    all_findings.append(f)

                    # Track entities
                    if f["finding_type"] == "person":
                        self.entity_tracker.track(
                            f["finding_text"], "person", "unknown",
                            file_id, f["case_lane"]
                        )
                    elif f["finding_type"] == "location":
                        self.entity_tracker.track(
                            f["finding_text"], "location", "address",
                            file_id, f["case_lane"]
                        )
                    elif f["finding_type"] == "case_number":
                        self.entity_tracker.track(
                            f["finding_text"], "case_number", "case",
                            file_id, f["case_lane"]
                        )

                for iss in result["issues"]:
                    iss["case_lane"] = assign_lane(
                        iss["supporting_text"], ""
                    )
                    all_issues.append(iss)

        # Deduplicate citations (same cite in same file)
        seen_cites = set()
        unique_citations = []
        for c in all_citations:
            key = (c["citation_text"], c["citation_type"])
            if key not in seen_cites:
                seen_cites.add(key)
                unique_citations.append(c)

        # Deduplicate findings (same text + type)
        seen_findings = set()
        unique_findings = []
        for f in all_findings:
            key = (f["finding_type"], f["finding_text"][:200])
            if key not in seen_findings:
                seen_findings.add(key)
                unique_findings.append(f)

        # Deduplicate issues (same type per file, keep strongest)
        issue_best = {}
        for iss in all_issues:
            key = iss["issue_type"]
            if key not in issue_best or iss["strength_score"] > issue_best[key]["strength_score"]:
                issue_best[key] = iss
        unique_issues = list(issue_best.values())

        # Insert into DB
        for c in unique_citations:
            self.conn.execute(
                "INSERT INTO citations "
                "(file_id, citation_text, citation_type, rule_number, "
                "page_number, line_number, context, case_lane) "
                "VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                (file_id, c["citation_text"], c["citation_type"],
                 c.get("rule_number"), c["page_number"], c["line_number"],
                 c.get("context", "")[:500], c.get("case_lane"))
            )

        for f in unique_findings:
            self.conn.execute(
                "INSERT INTO factual_findings "
                "(file_id, finding_type, finding_text, normalized_value, "
                "page_number, line_number, context, case_lane, "
                "admissibility_score, relevance_score, weight_score, "
                "authentication_level) "
                "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
                (file_id, f["finding_type"], f["finding_text"][:1000],
                 f.get("normalized_value", "")[:500],
                 f["page_number"], f["line_number"],
                 f.get("context", "")[:500], f.get("case_lane"),
                 f.get("admissibility_score", 0),
                 f.get("relevance_score", 0),
                 f.get("weight_score", 0),
                 f.get("authentication_level", "needs foundation"))
            )

        for iss in unique_issues:
            self.conn.execute(
                "INSERT INTO legal_issues "
                "(file_id, issue_type, description, supporting_text, "
                "page_number, line_number, case_lane, strength_score) "
                "VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                (file_id, iss["issue_type"], iss["description"],
                 iss["supporting_text"][:500],
                 iss["page_number"], iss["line_number"],
                 iss.get("case_lane"), iss["strength_score"])
            )

        self.stats["citations_found"] += len(unique_citations)
        self.stats["findings_found"] += len(unique_findings)
        self.stats["issues_found"] += len(unique_issues)

    def _record_error(self, path: str, file_rec: dict, error_msg: str):
        """Record a failed file analysis."""
        now = datetime.datetime.now().isoformat()
        ext = (file_rec.get("extension") or os.path.splitext(path)[1]).lstrip(".")
        try:
            self.conn.execute(
                "INSERT OR REPLACE INTO analyzed_files "
                "(path, file_type, page_count, word_count, legal_score, "
                "analysis_timestamp, extraction_success, error_message) "
                "VALUES (?, ?, 0, 0, ?, ?, 0, ?)",
                (path, ext, file_rec.get("legal_score", 0), now,
                 error_msg[:1000])
            )
        except Exception:
            pass

    @staticmethod
    def _split_pages(text: str) -> List[Tuple[int, str]]:
        """Split text into (page_number, page_text) tuples.
        Uses [PAGE N] markers from PDF extraction, or treats as single page."""
        parts = re.split(r'\[PAGE\s+(\d+)\]', text)
        if len(parts) <= 1:
            return [(1, text)]

        pages = []
        i = 1
        while i < len(parts):
            try:
                page_num = int(parts[i])
            except (ValueError, IndexError):
                page_num = (len(pages) + 1)
            page_text = parts[i + 1] if i + 1 < len(parts) else ""
            pages.append((page_num, page_text))
            i += 2

        if not pages:
            return [(1, text)]
        return pages

    # ── Report: Generate summary ─────────────────────────────────
    def cmd_report(self):
        """Generate and display an analysis summary report."""
        print("=" * 70)
        print("  DOCUMENT ANALYSIS ENGINE — Summary Report")
        print("=" * 70)

        # Overall stats
        total_files = self.conn.execute(
            "SELECT COUNT(*) FROM analyzed_files WHERE extraction_success = 1"
        ).fetchone()[0]
        total_errors = self.conn.execute(
            "SELECT COUNT(*) FROM analyzed_files WHERE extraction_success = 0"
        ).fetchone()[0]
        total_citations = self.conn.execute(
            "SELECT COUNT(*) FROM citations"
        ).fetchone()[0]
        total_findings = self.conn.execute(
            "SELECT COUNT(*) FROM factual_findings"
        ).fetchone()[0]
        total_issues = self.conn.execute(
            "SELECT COUNT(*) FROM legal_issues"
        ).fetchone()[0]
        total_entities = self.conn.execute(
            "SELECT COUNT(*) FROM entities"
        ).fetchone()[0]
        total_chains = self.conn.execute(
            "SELECT COUNT(*) FROM evidence_chain"
        ).fetchone()[0]

        print(f"\n  Overall Statistics:")
        print(f"    Files analyzed:    {total_files}")
        print(f"    Files with errors: {total_errors}")
        print(f"    Citations found:   {total_citations}")
        print(f"    Factual findings:  {total_findings}")
        print(f"    Legal issues:      {total_issues}")
        print(f"    Entities tracked:  {total_entities}")
        print(f"    Evidence chains:   {total_chains}")

        # Per-lane breakdown
        for lane, label in [
            ("A", "Lane A: Custody (2024-001507-DC, Judge McNeill)"),
            ("B", "Lane B: Housing (2023-5907-PP, Judge Hoopes)"),
            ("C", "Lane C: Convergence / Civil Rights (2025-002760-CZ)"),
        ]:
            print(f"\n  ── {label} ──")

            lane_citations = self.conn.execute(
                "SELECT COUNT(*) FROM citations WHERE case_lane LIKE ?",
                (f"%{lane}%",)
            ).fetchone()[0]
            lane_findings = self.conn.execute(
                "SELECT COUNT(*) FROM factual_findings WHERE case_lane LIKE ?",
                (f"%{lane}%",)
            ).fetchone()[0]
            lane_issues = self.conn.execute(
                "SELECT COUNT(*) FROM legal_issues WHERE case_lane LIKE ?",
                (f"%{lane}%",)
            ).fetchone()[0]

            print(f"    Citations: {lane_citations}  |  "
                  f"Findings: {lane_findings}  |  Issues: {lane_issues}")

            # Top citation types
            cite_types = self.conn.execute(
                "SELECT citation_type, COUNT(*) as cnt "
                "FROM citations WHERE case_lane LIKE ? "
                "GROUP BY citation_type ORDER BY cnt DESC LIMIT 5",
                (f"%{lane}%",)
            ).fetchall()
            if cite_types:
                print(f"    Top citation types: "
                      + ", ".join(f"{t}({c})" for t, c in cite_types))

            # Top issues by strength
            top_issues = self.conn.execute(
                "SELECT issue_type, MAX(strength_score) as strength, COUNT(*) as cnt "
                "FROM legal_issues WHERE case_lane LIKE ? "
                "GROUP BY issue_type ORDER BY strength DESC LIMIT 5",
                (f"%{lane}%",)
            ).fetchall()
            if top_issues:
                print(f"    Strongest issues:")
                for itype, strength, cnt in top_issues:
                    print(f"      • {itype.replace('_', ' ').title()}: "
                          f"strength={strength}, occurrences={cnt}")

            # High-value findings
            high_findings = self.conn.execute(
                "SELECT finding_type, COUNT(*) as cnt, "
                "AVG(relevance_score) as avg_rel "
                "FROM factual_findings WHERE case_lane LIKE ? "
                "GROUP BY finding_type ORDER BY avg_rel DESC LIMIT 5",
                (f"%{lane}%",)
            ).fetchall()
            if high_findings:
                print(f"    Finding breakdown:")
                for ftype, cnt, avg_rel in high_findings:
                    print(f"      • {ftype}: {cnt} found, avg relevance={avg_rel:.0f}")

            # Update analysis_summary table
            strongest = [
                {"type": t, "strength": s, "count": c}
                for t, s, c in (top_issues or [])
            ]
            weakest = self._identify_weak_areas(lane)
            recommended = self._recommend_actions(lane)

            self.conn.execute(
                "INSERT OR REPLACE INTO analysis_summary "
                "(case_lane, total_files, total_citations, total_findings, "
                "total_issues, strongest_claims, weakest_areas, "
                "recommended_actions) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                (lane,
                 self.conn.execute(
                     "SELECT COUNT(DISTINCT file_id) FROM citations "
                     "WHERE case_lane LIKE ?", (f"%{lane}%",)
                 ).fetchone()[0],
                 lane_citations, lane_findings, lane_issues,
                 json.dumps(strongest),
                 json.dumps(weakest),
                 json.dumps(recommended))
            )

        self.conn.commit()

        # Entity summary
        print(f"\n  ── Key Entities ──")
        top_entities = self.conn.execute(
            "SELECT entity_name, entity_type, role, mention_count, case_lanes "
            "FROM entities ORDER BY mention_count DESC LIMIT 15"
        ).fetchall()
        for name, etype, role, count, lanes in top_entities:
            print(f"    {name:<30} {etype:<12} {role:<12} "
                  f"mentions={count:<5} lanes={lanes}")

        # Evidence chain summary
        print(f"\n  ── Evidence Chain Highlights ──")
        strong_chains = self.conn.execute(
            "SELECT ec.strength, ec.connection_type, ec.explanation, "
            "li.issue_type, ff.finding_type "
            "FROM evidence_chain ec "
            "JOIN legal_issues li ON ec.supports_issue_id = li.id "
            "JOIN factual_findings ff ON ec.finding_id = ff.id "
            "ORDER BY ec.strength DESC LIMIT 10"
        ).fetchall()
        for strength, conn_type, expl, issue, finding in strong_chains:
            print(f"    [{strength:>3}] {conn_type:<14} "
                  f"{finding} → {issue.replace('_', ' ')}")

        print(f"\n  Database: {self.db_path}")
        print(f"  Report generated: {datetime.datetime.now().isoformat()}")

    def _identify_weak_areas(self, lane: str) -> list:
        """Identify areas lacking evidence for a lane."""
        weak = []
        all_issue_types = list(ISSUE_PATTERNS.keys())

        found_types = set()
        rows = self.conn.execute(
            "SELECT DISTINCT issue_type FROM legal_issues WHERE case_lane LIKE ?",
            (f"%{lane}%",)
        ).fetchall()
        for r in rows:
            found_types.add(r[0])

        # Issues relevant to each lane
        lane_relevant = {
            "A": {"due_process", "custody_interference", "judicial_misconduct",
                   "foc_misconduct", "perjury", "fraud"},
            "B": {"housing_habitability", "fraud", "discovery_abuse"},
            "C": {"civil_rights_1983", "due_process", "equal_protection",
                   "judicial_misconduct"},
        }
        relevant = lane_relevant.get(lane, set(all_issue_types))

        for issue_type in relevant:
            if issue_type not in found_types:
                weak.append({
                    "issue": issue_type,
                    "gap": "No supporting evidence found"
                })

        # Also flag low-strength issues
        low_strength = self.conn.execute(
            "SELECT issue_type, MAX(strength_score) "
            "FROM legal_issues WHERE case_lane LIKE ? "
            "GROUP BY issue_type HAVING MAX(strength_score) < 40",
            (f"%{lane}%",)
        ).fetchall()
        for itype, score in low_strength:
            weak.append({
                "issue": itype,
                "gap": f"Low strength score ({score}), needs stronger evidence"
            })

        return weak

    def _recommend_actions(self, lane: str) -> list:
        """Generate recommended actions for a lane."""
        actions = []

        # Check for high-priority issues lacking strong evidence
        weak = self._identify_weak_areas(lane)
        for w in weak[:3]:
            actions.append(
                f"Gather stronger evidence for {w['issue'].replace('_', ' ')}: {w['gap']}"
            )

        # Check for unverified citations
        unverified = self.conn.execute(
            "SELECT COUNT(*) FROM citations "
            "WHERE case_lane LIKE ? AND verified = 0",
            (f"%{lane}%",)
        ).fetchone()[0]
        if unverified > 0:
            actions.append(
                f"Verify {unverified} unverified citations for accuracy"
            )

        # Check for hearsay concerns
        hearsay = self.conn.execute(
            "SELECT COUNT(*) FROM factual_findings "
            "WHERE case_lane LIKE ? AND authentication_level = 'hearsay concern'",
            (f"%{lane}%",)
        ).fetchone()[0]
        if hearsay > 0:
            actions.append(
                f"Address {hearsay} findings with hearsay concerns"
            )

        if not actions:
            actions.append("Evidence collection appears adequate — proceed to drafting")

        return actions

    # ── All: Full pipeline ───────────────────────────────────────
    def cmd_all(self, lane_filter: Optional[str] = None):
        """Run complete pipeline: scan → analyze → report."""
        self.cmd_scan(lane_filter)
        print()
        self.cmd_analyze(lane_filter)
        print()
        self.cmd_report()


# ════════════════════════════════════════════════════════════════════════
#  CLI Entry Point
# ════════════════════════════════════════════════════════════════════════

def main():
    parser = argparse.ArgumentParser(
        description="LitigationOS Document Analysis Engine",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Commands:
  scan       Discover and prioritize files from drive manifests
  analyze    Run full line-by-line document analysis
  report     Generate summary report from analysis database
  all        Run complete pipeline (scan → analyze → report)

Examples:
  python analysis_engine.py scan
  python analysis_engine.py analyze --lane A
  python analysis_engine.py report
  python analysis_engine.py all
        """
    )
    parser.add_argument(
        "command", choices=["scan", "analyze", "report", "all"],
        help="Command to execute"
    )
    parser.add_argument(
        "--lane", type=str, default=None, choices=["A", "B", "C"],
        help="Filter to a specific case lane"
    )
    parser.add_argument(
        "--db", type=str, default=None,
        help="Override analysis database path"
    )
    args = parser.parse_args()

    db_path = Path(args.db) if args.db else ANALYSIS_DB_PATH

    # Report library availability
    print(f"  PDF engine:  {_PDF_ENGINE or 'NONE (install pdfplumber or PyPDF2)'}")
    print(f"  DOCX engine: {'python-docx' if _HAS_DOCX else 'fallback (zipfile XML)'}")
    print(f"  LocalAI:     {'available' if _HAS_AI else 'not loaded'}")
    print(f"  Output DB:   {db_path}")
    print()

    engine = AnalysisEngine(db_path)
    try:
        if args.command == "scan":
            engine.cmd_scan(args.lane)
        elif args.command == "analyze":
            engine.cmd_analyze(args.lane)
        elif args.command == "report":
            engine.cmd_report()
        elif args.command == "all":
            engine.cmd_all(args.lane)
    except KeyboardInterrupt:
        print("\n\n  [INTERRUPTED] Saving progress...")
        engine.conn.commit()
        print("  Progress saved. Resume with the same command.")
    except Exception as e:
        print(f"\n  [FATAL ERROR] {e}")
        traceback.print_exc()
        engine.conn.commit()
        sys.exit(1)
    finally:
        engine.close()

    print("\n  [DONE]")


if __name__ == "__main__":
    main()
