"""
Multi-Brain Universe — Extraction Engine (BRAIN-04)
Extracts text from PDFs and documents, classifies content by lane and brain,
and inserts into the correct brain database with full provenance tracking.

Usage:
    python extraction_engine.py --scan-dir <path>     # Scan directory, queue files, process
    python extraction_engine.py --process-queue        # Process pending queue items
    python extraction_engine.py --status               # Show queue and brain stats
    python extraction_engine.py --file <path>          # Process single file
"""
import sqlite3
import os
import sys
import re
import hashlib
import time
import argparse
import uuid
from datetime import datetime
from contextlib import contextmanager

try:
    sys.stdout = open(sys.stdout.fileno(), mode='w', encoding='utf-8', errors='replace')
except (OSError, AttributeError):
    pass  # Handle redirected/piped stdout gracefully

# ---------------------------------------------------------------------------
# Resolve imports — never run from repo root (shadow-module risk)
# ---------------------------------------------------------------------------
BRAIN_DIR = os.path.dirname(os.path.abspath(__file__))
if BRAIN_DIR not in sys.path:
    sys.path.insert(0, BRAIN_DIR)

from brain_manager import BrainManager, PRAGMAS

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------
SUPPORTED_EXTENSIONS = {'.pdf', '.txt', '.md', '.csv'}
TESSERACT_PATH = r'C:\Program Files\Tesseract-OCR\tesseract.exe'
CHECKPOINT_INTERVAL = 50
MAX_RETRIES = 3
RETRY_BASE_DELAY = 1.0  # seconds, doubles each retry

# Minimum characters per page to consider it "text-rich" (vs scanned/image)
MIN_TEXT_DENSITY = 30


# ═══════════════════════════════════════════════════════════════════════════
# MEEK Lane Classification Patterns
# Priority order: E → D → F → A → B  (highest → lowest)
# ═══════════════════════════════════════════════════════════════════════════

MEEK_PATTERNS = {
    'E': {  # Lane E — Judicial Misconduct (MEEK4)
        'lane': 'E',
        'label': 'Misconduct',
        'patterns': [
            re.compile(r'\bMcNeill\b', re.IGNORECASE),
            re.compile(r'\bdisqualif', re.IGNORECASE),
            re.compile(r'\bMCR\s*2\.003\b', re.IGNORECASE),
            re.compile(r'\bex\s*parte\b', re.IGNORECASE),
            re.compile(r'\bjudicial\s+misconduct\b', re.IGNORECASE),
            re.compile(r'\bJTC\b'),
            re.compile(r'\bjudicial\s+tenure\b', re.IGNORECASE),
            re.compile(r'\bcanon\s+\d', re.IGNORECASE),
            re.compile(r'\brecus(al|e)\b', re.IGNORECASE),
        ],
    },
    'D': {  # Lane D — PPO (MEEK3)
        'lane': 'D',
        'label': 'PPO',
        'patterns': [
            re.compile(r'\bprotection\s+order\b', re.IGNORECASE),
            re.compile(r'\bPPO\b'),
            re.compile(r'\bMCL\s*600\.2950\b', re.IGNORECASE),
            re.compile(r'\bstalk(ing|er)\b', re.IGNORECASE),
            re.compile(r'\bharass(ment|ing)\b', re.IGNORECASE),
            re.compile(r'\bdomestic\s+violence\b', re.IGNORECASE),
            re.compile(r'\brestraining\s+order\b', re.IGNORECASE),
            re.compile(r'\b2023[-\s]*5907[-\s]*PP\b', re.IGNORECASE),
        ],
    },
    'F': {  # Lane F — Appellate (MEEK5)
        'lane': 'F',
        'label': 'Appellate',
        'patterns': [
            re.compile(r'\bappeal\b', re.IGNORECASE),
            re.compile(r'\bCOA\b'),
            re.compile(r'\bMCR\s*7\.2', re.IGNORECASE),
            re.compile(r'\bappellant\b', re.IGNORECASE),
            re.compile(r'\bappellee\b', re.IGNORECASE),
            re.compile(r'\b366810\b'),
            re.compile(r'\bcourt\s+of\s+appeals\b', re.IGNORECASE),
            re.compile(r'\bMCR\s*7\.\d', re.IGNORECASE),
            re.compile(r'\bsupreme\s+court\b', re.IGNORECASE),
        ],
    },
    'A': {  # Lane A — Custody (MEEK2)
        'lane': 'A',
        'label': 'Custody',
        'patterns': [
            re.compile(r'\bcustody\b', re.IGNORECASE),
            re.compile(r'\bparent(ing|al)\b', re.IGNORECASE),
            re.compile(r'\bvisitation\b', re.IGNORECASE),
            re.compile(r'\bMCL\s*722\b', re.IGNORECASE),
            re.compile(r'\bbest\s+interest\b', re.IGNORECASE),
            re.compile(r'\bchild\s+support\b', re.IGNORECASE),
            re.compile(r'\bguardian\s+ad\s+litem\b', re.IGNORECASE),
            re.compile(r'\b2024[-\s]*001507[-\s]*DC\b', re.IGNORECASE),
            re.compile(r'\bfriend\s+of\s+the\s+court\b', re.IGNORECASE),
            re.compile(r'\bFOC\b'),
        ],
    },
    'B': {  # Lane B — Housing (MEEK1)
        'lane': 'B',
        'label': 'Housing',
        'patterns': [
            re.compile(r'\bShady\s+Oaks\b', re.IGNORECASE),
            re.compile(r'\blandlord\b', re.IGNORECASE),
            re.compile(r'\btenant\b', re.IGNORECASE),
            re.compile(r'\bMCL\s*125\b', re.IGNORECASE),
            re.compile(r'\bMCL\s*554\b', re.IGNORECASE),
            re.compile(r'\bhabitability\b', re.IGNORECASE),
            re.compile(r'\brent\b', re.IGNORECASE),
            re.compile(r'\beviction\b', re.IGNORECASE),
            re.compile(r'\b2025[-\s]*002760[-\s]*CZ\b', re.IGNORECASE),
            re.compile(r'\bsecurity\s+deposit\b', re.IGNORECASE),
        ],
    },
}

# Evaluation order (E highest priority → B lowest)
LANE_PRIORITY = ['E', 'D', 'F', 'A', 'B']

# ---------------------------------------------------------------------------
# Brain routing patterns
# ---------------------------------------------------------------------------
AUTHORITY_PATTERNS = [
    re.compile(r'\bMCR\s+\d+\.\d+', re.IGNORECASE),
    re.compile(r'\bMCL\s+\d+\.\d+', re.IGNORECASE),
    re.compile(r'\bMRE\s+\d+', re.IGNORECASE),
    re.compile(r'\bUSC\s+\d+', re.IGNORECASE),
    re.compile(r'\b42\s+USC\b', re.IGNORECASE),
    re.compile(r'\bFRCP\s+\d+', re.IGNORECASE),
]
NARRATIVE_PATTERNS = [
    re.compile(r'\b\d{1,2}[/-]\d{1,2}[/-]\d{2,4}\b'),
    re.compile(r'\b(?:January|February|March|April|May|June|July|August|September|October|November|December)\s+\d{1,2},?\s+\d{4}\b', re.IGNORECASE),
    re.compile(r'\border\b.*\bcourt\b', re.IGNORECASE),
    re.compile(r'\bhearing\b', re.IGNORECASE),
    re.compile(r'\bordered\b', re.IGNORECASE),
    re.compile(r'\bfiled\b', re.IGNORECASE),
]
ENTITY_PATTERNS = [
    re.compile(r'\b(?:plaintiff|defendant|respondent|petitioner|appellant|appellee)\b', re.IGNORECASE),
    re.compile(r'\b(?:Judge|Hon\.|Honorable)\s+[A-Z][a-z]+', re.IGNORECASE),
    re.compile(r'\b(?:Attorney|Counsel|Esq\.)\b', re.IGNORECASE),
    re.compile(r'\bPigors\b', re.IGNORECASE),
    re.compile(r'\bWatson\b', re.IGNORECASE),
]
CLAIMS_PATTERNS = [
    re.compile(r'\bcause\s+of\s+action\b', re.IGNORECASE),
    re.compile(r'\bdamages?\b', re.IGNORECASE),
    re.compile(r'\bliabilit(y|ies)\b', re.IGNORECASE),
    re.compile(r'\bclaim\b', re.IGNORECASE),
    re.compile(r'\bremedy\b', re.IGNORECASE),
    re.compile(r'\brelief\b', re.IGNORECASE),
    re.compile(r'\bnegligen(ce|t)\b', re.IGNORECASE),
]
INTERPRETATION_PATTERNS = [
    re.compile(r'\bstrateg(y|ic)\b', re.IGNORECASE),
    re.compile(r'\banalys[ie]s\b', re.IGNORECASE),
    re.compile(r'\bargument\b', re.IGNORECASE),
    re.compile(r'\bimpeach(ment)?\b', re.IGNORECASE),
    re.compile(r'\brebuttal\b', re.IGNORECASE),
    re.compile(r'\bcounter[-\s]?argument\b', re.IGNORECASE),
    re.compile(r'\brisk\s+(assess|score|analy)', re.IGNORECASE),
]


# ═══════════════════════════════════════════════════════════════════════════
# Extraction Helpers
# ═══════════════════════════════════════════════════════════════════════════

def _sha256(text: str) -> str:
    """Compute SHA-256 hash of text content."""
    return hashlib.sha256(text.encode('utf-8', errors='replace')).hexdigest()


def _gen_id(prefix: str = 'ext') -> str:
    """Generate a unique ID with a descriptive prefix."""
    return f"{prefix}_{uuid.uuid4().hex[:12]}"


def _retry_on_lock(func, *args, max_retries=MAX_RETRIES, **kwargs):
    """Retry a function up to max_retries times on SQLite lock errors."""
    for attempt in range(max_retries):
        try:
            return func(*args, **kwargs)
        except sqlite3.OperationalError as e:
            if 'locked' in str(e).lower() and attempt < max_retries - 1:
                delay = RETRY_BASE_DELAY * (2 ** attempt)
                time.sleep(delay)
            else:
                raise
    return None


# ═══════════════════════════════════════════════════════════════════════════
# PDF Extraction
# ═══════════════════════════════════════════════════════════════════════════

def extract_pdf(file_path: str) -> dict:
    """Extract text and metadata from a PDF file using PyMuPDF.

    Falls back to Tesseract OCR for scanned pages with low text density.

    Returns:
        dict with keys: pages (list of {page_num, text, confidence}),
        metadata (dict), full_text (str), total_pages (int)
    """
    try:
        import pymupdf
    except ImportError:
        return {'error': 'pymupdf not installed', 'pages': [], 'metadata': {},
                'full_text': '', 'total_pages': 0}

    result = {'pages': [], 'metadata': {}, 'full_text': '', 'total_pages': 0}

    try:
        doc = pymupdf.open(file_path)
    except Exception as e:
        return {'error': f'Failed to open PDF: {e}', 'pages': [],
                'metadata': {}, 'full_text': '', 'total_pages': 0}

    # Extract metadata
    meta = doc.metadata or {}
    result['metadata'] = {
        'title': meta.get('title', ''),
        'author': meta.get('author', ''),
        'subject': meta.get('subject', ''),
        'creator': meta.get('creator', ''),
        'creation_date': meta.get('creationDate', ''),
        'mod_date': meta.get('modDate', ''),
        'page_count': doc.page_count,
    }
    result['total_pages'] = doc.page_count

    full_text_parts = []

    for page_num in range(doc.page_count):
        page = doc[page_num]
        text = page.get_text('text') or ''
        text = text.strip()

        # Calculate text density confidence
        page_area = page.rect.width * page.rect.height
        char_density = len(text) / max(page_area, 1) * 10000
        confidence = min(1.0, char_density / 5.0) if text else 0.0

        # OCR fallback for scanned pages
        if len(text) < MIN_TEXT_DENSITY and os.path.isfile(TESSERACT_PATH):
            ocr_text = _ocr_page(page, file_path, page_num)
            if ocr_text and len(ocr_text) > len(text):
                text = ocr_text
                confidence = min(0.7, len(ocr_text) / 500.0)  # OCR caps at 0.7

        result['pages'].append({
            'page_num': page_num + 1,
            'text': text,
            'confidence': round(confidence, 3),
            'word_count': len(text.split()),
        })
        full_text_parts.append(text)

    doc.close()
    result['full_text'] = '\n\n'.join(full_text_parts)
    return result


def _ocr_page(page, file_path: str, page_num: int) -> str:
    """Run Tesseract OCR on a single PDF page rendered as an image.

    Returns extracted text or empty string on failure.
    """
    import subprocess
    import tempfile

    try:
        pix = page.get_pixmap(dpi=300)
        with tempfile.NamedTemporaryFile(suffix='.png', delete=False) as tmp_img:
            tmp_img_path = tmp_img.name
            pix.save(tmp_img_path)

        proc = subprocess.run(
            [TESSERACT_PATH, tmp_img_path, 'stdout', '--psm', '6'],
            capture_output=True, text=True, timeout=60,
            encoding='utf-8', errors='replace',
        )
        return proc.stdout.strip() if proc.returncode == 0 else ''
    except Exception:
        return ''
    finally:
        try:
            os.unlink(tmp_img_path)
        except (OSError, UnboundLocalError):
            pass


# ═══════════════════════════════════════════════════════════════════════════
# Text / Markdown / CSV Extraction
# ═══════════════════════════════════════════════════════════════════════════

def extract_text_file(file_path: str) -> dict:
    """Extract content from .txt, .md, or .csv files.

    Returns:
        dict with keys: full_text, structure_type, line_count, word_count
    """
    try:
        with open(file_path, 'r', encoding='utf-8', errors='replace') as f:
            text = f.read()
    except Exception as e:
        return {'error': str(e), 'full_text': '', 'structure_type': 'unknown',
                'line_count': 0, 'word_count': 0}

    ext = os.path.splitext(file_path)[1].lower()
    lines = text.splitlines()

    # Detect structure type
    if ext == '.csv':
        structure_type = 'csv'
    elif ext == '.md' or any(line.startswith('#') for line in lines[:20]):
        structure_type = 'markdown'
    else:
        structure_type = 'plain_text'

    return {
        'full_text': text,
        'structure_type': structure_type,
        'line_count': len(lines),
        'word_count': len(text.split()),
    }


# ═══════════════════════════════════════════════════════════════════════════
# Lane Classification
# ═══════════════════════════════════════════════════════════════════════════

def classify_lane(text: str) -> dict:
    """Classify text into a case lane using MEEK regex patterns.

    Evaluates in priority order E → D → F → A → B.
    Returns the highest-priority lane with at least one match.

    Returns:
        dict with keys: lane, label, match_count, matched_patterns
    """
    if not text:
        return {'lane': None, 'label': 'Unclassified', 'match_count': 0,
                'matched_patterns': []}

    scores = {}
    for lane_key in LANE_PRIORITY:
        config = MEEK_PATTERNS[lane_key]
        matches = []
        for pattern in config['patterns']:
            found = pattern.findall(text)
            if found:
                matches.extend(found[:5])  # cap per pattern to avoid runaway
        if matches:
            scores[lane_key] = {
                'lane': config['lane'],
                'label': config['label'],
                'match_count': len(matches),
                'matched_patterns': matches[:10],
            }

    # Return highest-priority lane that matched
    for lane_key in LANE_PRIORITY:
        if lane_key in scores:
            return scores[lane_key]

    return {'lane': None, 'label': 'Unclassified', 'match_count': 0,
            'matched_patterns': []}


# ═══════════════════════════════════════════════════════════════════════════
# Brain Routing
# ═══════════════════════════════════════════════════════════════════════════

def classify_brain(text: str) -> list:
    """Determine which brain(s) should receive this content.

    Returns list of brain names sorted by relevance score (descending).
    A document can route to multiple brains.
    """
    if not text:
        return ['narrative_brain']

    scores = {
        'authority_brain': 0,
        'narrative_brain': 0,
        'entity_brain': 0,
        'claims_brain': 0,
        'interpretation_brain': 0,
    }

    for pattern in AUTHORITY_PATTERNS:
        scores['authority_brain'] += len(pattern.findall(text))
    for pattern in NARRATIVE_PATTERNS:
        scores['narrative_brain'] += len(pattern.findall(text))
    for pattern in ENTITY_PATTERNS:
        scores['entity_brain'] += len(pattern.findall(text))
    for pattern in CLAIMS_PATTERNS:
        scores['claims_brain'] += len(pattern.findall(text))
    for pattern in INTERPRETATION_PATTERNS:
        scores['interpretation_brain'] += len(pattern.findall(text))

    # Always include narrative_brain as baseline (every doc gets an extraction)
    scores['narrative_brain'] = max(scores['narrative_brain'], 1)

    # Filter to brains with score >= 2 (except narrative which always qualifies)
    result = []
    for brain, score in sorted(scores.items(), key=lambda x: -x[1]):
        if score >= 2 or brain == 'narrative_brain':
            result.append(brain)

    return result if result else ['narrative_brain']


# ═══════════════════════════════════════════════════════════════════════════
# Brain Insertion
# ═══════════════════════════════════════════════════════════════════════════

class BrainInserter:
    """Handles inserting extracted content into the correct brain databases."""

    def __init__(self, brain_manager: BrainManager = None):
        self.bm = brain_manager or BrainManager()
        self.stats = {
            'narrative_inserts': 0,
            'authority_inserts': 0,
            'entity_inserts': 0,
            'claims_inserts': 0,
            'interpretation_inserts': 0,
            'universal_search_inserts': 0,
            'provenance_inserts': 0,
        }

    def insert_to_brain(self, brain_name: str, extraction: dict,
                        source_file: str, lane: str) -> list:
        """Route an extraction to the appropriate brain table.

        Returns list of (record_table, record_id) tuples inserted.
        """
        inserted = []
        if brain_name == 'narrative_brain':
            inserted.extend(self._insert_narrative(extraction, source_file, lane))
        elif brain_name == 'authority_brain':
            inserted.extend(self._insert_authority(extraction, source_file, lane))
        elif brain_name == 'entity_brain':
            inserted.extend(self._insert_entity(extraction, source_file, lane))
        elif brain_name == 'claims_brain':
            inserted.extend(self._insert_claims(extraction, source_file, lane))
        elif brain_name == 'interpretation_brain':
            inserted.extend(self._insert_interpretation(extraction, source_file, lane))

        # Add to universal search for every insertion
        for table, record_id in inserted:
            self._add_to_universal_search(brain_name, table, record_id,
                                          extraction.get('text', ''))

        return inserted

    def _insert_narrative(self, extraction: dict, source_file: str,
                          lane: str) -> list:
        """Insert into narrative_brain.document_extractions."""
        record_id = _gen_id('narr')
        text = extraction.get('text', '')
        page_num = extraction.get('page_num')
        confidence = extraction.get('confidence', 0.8)

        def _do_insert():
            with self.bm.open_brain('narrative_brain') as conn:
                conn.execute(
                    """INSERT OR IGNORE INTO document_extractions
                       (extraction_id, source_file, source_type, source_page,
                        extracted_text, case_lane, extraction_method,
                        extraction_confidence, word_count, sha256)
                       VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                    (record_id, source_file,
                     os.path.splitext(source_file)[1].lstrip('.'),
                     page_num, text, lane, 'extraction_engine',
                     confidence, len(text.split()), _sha256(text))
                )
                conn.commit()

        _retry_on_lock(_do_insert)
        self.stats['narrative_inserts'] += 1

        # Add provenance
        self._add_provenance('narrative_brain', 'document_extractions',
                             record_id, source_file, page_num, confidence)

        return [('document_extractions', record_id)]

    def _insert_authority(self, extraction: dict, source_file: str,
                          lane: str) -> list:
        """Extract MCR/MCL citations and insert stubs into authority_brain."""
        text = extraction.get('text', '')
        inserted = []

        # Find MCR citations
        mcr_matches = re.findall(r'\bMCR\s+(\d+\.\d+\w*)', text, re.IGNORECASE)
        for rule_num in set(mcr_matches):
            rule_id = _gen_id('mcr')
            # Extract surrounding context as the rule_text snippet
            snippet = _extract_context(text, f'MCR {rule_num}', window=300)

            def _do_insert(rid=rule_id, rn=rule_num, snip=snippet):
                with self.bm.open_brain('authority_brain') as conn:
                    conn.execute(
                        """INSERT OR IGNORE INTO court_rules
                           (rule_id, rule_number, rule_text, source_type,
                            trust_level, sha256)
                           VALUES (?, ?, ?, ?, ?, ?)""",
                        (rid, f'MCR {rn}', snip, 'extracted',
                         'reference', _sha256(snip))
                    )
                    conn.commit()

            _retry_on_lock(_do_insert)
            self.stats['authority_inserts'] += 1
            inserted.append(('court_rules', rule_id))

        # Find MCL citations
        mcl_matches = re.findall(r'\bMCL\s+(\d+\.\d+\w*)', text, re.IGNORECASE)
        for stat_num in set(mcl_matches):
            stat_id = _gen_id('mcl')
            snippet = _extract_context(text, f'MCL {stat_num}', window=300)

            def _do_insert(sid=stat_id, sn=stat_num, snip=snippet):
                with self.bm.open_brain('authority_brain') as conn:
                    conn.execute(
                        """INSERT OR IGNORE INTO statutes
                           (statute_id, statute_number, statute_text,
                            source_type, trust_level, sha256)
                           VALUES (?, ?, ?, ?, ?, ?)""",
                        (sid, f'MCL {sn}', snip, 'extracted',
                         'reference', _sha256(snip))
                    )
                    conn.commit()

            _retry_on_lock(_do_insert)
            self.stats['authority_inserts'] += 1
            inserted.append(('statutes', stat_id))

        if inserted:
            self._add_provenance(
                'authority_brain', 'court_rules', inserted[0][1],
                source_file, extraction.get('page_num'),
                extraction.get('confidence', 0.6))

        return inserted

    def _insert_entity(self, extraction: dict, source_file: str,
                       lane: str) -> list:
        """Detect party/judge references and insert into entity_brain."""
        text = extraction.get('text', '')
        inserted = []

        # Detect judge references
        judge_pattern = re.compile(
            r'\b(?:Judge|Hon\.|Honorable)\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)',
            re.IGNORECASE)
        for match in set(judge_pattern.findall(text)):
            party_id = _gen_id('judge')

            def _do_insert(pid=party_id, name=match):
                with self.bm.open_brain('entity_brain') as conn:
                    # Check if already exists by name
                    existing = conn.execute(
                        "SELECT party_id FROM parties WHERE legal_name = ?",
                        (name,)).fetchone()
                    if existing:
                        return
                    conn.execute(
                        """INSERT OR IGNORE INTO parties
                           (party_id, legal_name, display_name, party_type,
                            role, case_lanes, is_judge)
                           VALUES (?, ?, ?, ?, ?, ?, ?)""",
                        (pid, name, name, 'individual', 'judge', lane, 1)
                    )
                    conn.commit()

            _retry_on_lock(_do_insert)
            self.stats['entity_inserts'] += 1
            inserted.append(('parties', party_id))

        # Detect party role references (plaintiff/defendant)
        role_pattern = re.compile(
            r'\b(plaintiff|defendant|respondent|petitioner)\s*[,:]?\s*'
            r'([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)',
            re.IGNORECASE)
        for role, name in set(role_pattern.findall(text)):
            party_id = _gen_id('party')
            role_lower = role.lower()

            def _do_insert(pid=party_id, n=name, r=role_lower, ln=lane):
                with self.bm.open_brain('entity_brain') as conn:
                    existing = conn.execute(
                        "SELECT party_id FROM parties WHERE legal_name = ?",
                        (n,)).fetchone()
                    if existing:
                        return
                    conn.execute(
                        """INSERT OR IGNORE INTO parties
                           (party_id, legal_name, display_name, party_type,
                            role, case_lanes, is_plaintiff, is_defendant)
                           VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
                        (pid, n, n, 'individual', r, ln,
                         1 if r in ('plaintiff', 'petitioner') else 0,
                         1 if r in ('defendant', 'respondent') else 0)
                    )
                    conn.commit()

            _retry_on_lock(_do_insert)
            self.stats['entity_inserts'] += 1
            inserted.append(('parties', party_id))

        if inserted:
            self._add_provenance(
                'entity_brain', 'parties', inserted[0][1],
                source_file, extraction.get('page_num'),
                extraction.get('confidence', 0.5))

        return inserted

    def _insert_claims(self, extraction: dict, source_file: str,
                       lane: str) -> list:
        """Detect cause-of-action language and insert into claims_brain."""
        text = extraction.get('text', '')
        inserted = []

        # Detect cause-of-action structures in the text
        coa_patterns = [
            (r'\bcause\s+of\s+action\b[^.]{0,200}', 'cause_of_action'),
            (r'\bcount\s+(?:I{1,5}|[0-9]+)\b[^.]{0,200}', 'count'),
            (r'\bnegligen(?:ce|t)\b[^.]{0,200}', 'negligence'),
            (r'\bbreach\s+of\s+(?:contract|duty|covenant)\b[^.]{0,200}', 'breach'),
        ]

        for pattern_str, claim_type in coa_patterns:
            matches = re.findall(pattern_str, text, re.IGNORECASE)
            for match_text in matches[:3]:  # max 3 per type per page
                claim_id = _gen_id('claim')

                def _do_insert(cid=claim_id, ct=claim_type, mt=match_text, ln=lane):
                    with self.bm.open_brain('claims_brain') as conn:
                        conn.execute(
                            """INSERT OR IGNORE INTO causes_of_action
                               (claim_id, claim_name, claim_type, case_lane,
                                elements, notes)
                               VALUES (?, ?, ?, ?, ?, ?)""",
                            (cid, ct.replace('_', ' ').title(), ct, ln,
                             '[]', mt.strip()[:500])
                        )
                        conn.commit()

                _retry_on_lock(_do_insert)
                self.stats['claims_inserts'] += 1
                inserted.append(('causes_of_action', claim_id))

        if inserted:
            self._add_provenance(
                'claims_brain', 'causes_of_action', inserted[0][1],
                source_file, extraction.get('page_num'),
                extraction.get('confidence', 0.5))

        return inserted

    def _insert_interpretation(self, extraction: dict, source_file: str,
                               lane: str) -> list:
        """Detect strategy/analysis/argument text → interpretation_brain."""
        text = extraction.get('text', '')
        inserted = []

        # Check for substantial interpretation content (at least 50 words)
        if len(text.split()) < 50:
            return inserted

        # Determine argument type from content
        arg_type = 'general'
        if re.search(r'\bimpeach', text, re.IGNORECASE):
            arg_type = 'impeachment'
        elif re.search(r'\brebuttal\b', text, re.IGNORECASE):
            arg_type = 'rebuttal'
        elif re.search(r'\bstrateg', text, re.IGNORECASE):
            arg_type = 'strategy'
        elif re.search(r'\banalys[ie]s\b', text, re.IGNORECASE):
            arg_type = 'analysis'

        arg_id = _gen_id('arg')

        def _do_insert():
            with self.bm.open_brain('interpretation_brain') as conn:
                conn.execute(
                    """INSERT OR IGNORE INTO legal_arguments
                       (argument_id, case_lane, argument_type, argument_text,
                        ai_model, ai_confidence)
                       VALUES (?, ?, ?, ?, ?, ?)""",
                    (arg_id, lane, arg_type, text[:5000],
                     'extraction_engine', extraction.get('confidence', 0.5))
                )
                conn.commit()

        _retry_on_lock(_do_insert)
        self.stats['interpretation_inserts'] += 1
        inserted.append(('legal_arguments', arg_id))

        self._add_provenance(
            'interpretation_brain', 'legal_arguments', arg_id,
            source_file, extraction.get('page_num'),
            extraction.get('confidence', 0.5))

        return inserted

    def _add_provenance(self, brain_name: str, record_table: str,
                        record_id: str, source_file: str,
                        source_page: int = None,
                        confidence: float = 1.0):
        """Track extraction provenance in the target brain's provenance table."""
        def _do_insert():
            self.bm.add_provenance(
                brain_name, record_table, record_id,
                source_file=source_file, source_page=source_page,
                source_type=os.path.splitext(source_file)[1].lstrip('.'),
                extraction_method='extraction_engine',
                extraction_confidence=confidence,
                sha256=None,
            )

        try:
            _retry_on_lock(_do_insert)
            self.stats['provenance_inserts'] += 1
        except Exception:
            pass  # provenance failure is non-fatal

    def _add_to_universal_search(self, brain_name: str, table_name: str,
                                 record_id: str, text: str):
        """Add record to the cross-brain universal search FTS5 index."""
        def _do_insert():
            with self.bm.open_brain('cross_brain_index') as conn:
                conn.execute(
                    """INSERT INTO universal_search
                       (brain_name, table_name, record_id,
                        searchable_text, record_type)
                       VALUES (?, ?, ?, ?, ?)""",
                    (brain_name, table_name, record_id,
                     text[:10000], table_name)
                )
                conn.commit()

        try:
            _retry_on_lock(_do_insert)
            self.stats['universal_search_inserts'] += 1
        except Exception:
            pass  # search index failure is non-fatal


def _extract_context(text: str, target: str, window: int = 300) -> str:
    """Extract a window of text surrounding a target string."""
    idx = text.lower().find(target.lower())
    if idx == -1:
        return text[:window]
    start = max(0, idx - window // 2)
    end = min(len(text), idx + len(target) + window // 2)
    return text[start:end].strip()


# ═══════════════════════════════════════════════════════════════════════════
# Extraction Engine (orchestrator)
# ═══════════════════════════════════════════════════════════════════════════

class ExtractionEngine:
    """Main engine: reads queue, extracts content, classifies, inserts into brains."""

    def __init__(self, brain_dir: str = None):
        self.bm = BrainManager(brain_dir)
        self.inserter = BrainInserter(self.bm)
        self.stats = {
            'files_processed': 0,
            'files_failed': 0,
            'pages_extracted': 0,
            'items_inserted': 0,
            'errors': [],
        }

    # ------------------------------------------------------------------
    # Queue management
    # ------------------------------------------------------------------

    def scan_directory(self, dir_path: str, priority: int = 5) -> int:
        """Scan a directory for supported files and add them to the queue.

        Returns number of files queued.
        """
        if not os.path.isdir(dir_path):
            print(f"ERROR: Directory not found: {dir_path}")
            return 0

        queued = 0
        for root, _dirs, files in os.walk(dir_path):
            for fname in files:
                ext = os.path.splitext(fname)[1].lower()
                if ext not in SUPPORTED_EXTENSIONS:
                    continue
                full_path = os.path.join(root, fname)
                try:
                    file_size = os.path.getsize(full_path)
                except OSError:
                    continue

                try:
                    self.bm.queue_extraction(
                        file_path=full_path,
                        priority=priority,
                        file_type=ext.lstrip('.'),
                        file_size=file_size,
                        extraction_method='auto',
                    )
                    queued += 1
                except Exception as e:
                    self.stats['errors'].append(f"Queue error ({fname}): {e}")

        print(f"Queued {queued} files from {dir_path}")
        return queued

    def process_queue(self, limit: int = 0) -> dict:
        """Process pending items from the extraction queue.

        Args:
            limit: Max files to process (0 = unlimited)

        Returns:
            Stats dict with processing results.
        """
        with self.bm.open_brain('cross_brain_index') as conn:
            sql = """SELECT queue_id, file_path, file_type, priority
                     FROM extraction_queue
                     WHERE status = 'pending'
                     ORDER BY priority ASC, queued_at ASC"""
            if limit > 0:
                sql += f" LIMIT {limit}"
            items = conn.execute(sql).fetchall()

        if not items:
            print("No pending items in extraction queue.")
            return self.stats

        print(f"Processing {len(items)} queued files...")

        for i, item in enumerate(items):
            queue_id = item['queue_id']
            file_path = item['file_path']

            # Mark as processing
            self._update_queue_status(queue_id, 'processing')

            try:
                result = self.process_file(file_path)
                status = 'completed' if result else 'failed'
                error_msg = None if result else 'No content extracted'
            except Exception as e:
                status = 'failed'
                error_msg = str(e)[:500]
                self.stats['errors'].append(f"{file_path}: {e}")
                self.stats['files_failed'] += 1

            self._update_queue_status(queue_id, status, error_msg)

            # Checkpoint every CHECKPOINT_INTERVAL files
            if (i + 1) % CHECKPOINT_INTERVAL == 0:
                self._print_progress(i + 1, len(items))

        self._print_progress(len(items), len(items))
        return self.stats

    def process_file(self, file_path: str) -> bool:
        """Process a single file: extract → classify → insert.

        Returns True if extraction succeeded, False otherwise.
        """
        if not os.path.isfile(file_path):
            self.stats['errors'].append(f"File not found: {file_path}")
            self.stats['files_failed'] += 1
            return False

        ext = os.path.splitext(file_path)[1].lower()

        # ── Extract ──
        if ext == '.pdf':
            result = extract_pdf(file_path)
            if 'error' in result and result['error']:
                self.stats['errors'].append(f"{file_path}: {result['error']}")
                self.stats['files_failed'] += 1
                return False
            pages = result.get('pages', [])
            self.stats['pages_extracted'] += len(pages)
        elif ext in ('.txt', '.md', '.csv'):
            result = extract_text_file(file_path)
            if 'error' in result and result['error']:
                self.stats['errors'].append(f"{file_path}: {result['error']}")
                self.stats['files_failed'] += 1
                return False
            # Wrap as single-page for uniform processing
            pages = [{
                'page_num': None,
                'text': result['full_text'],
                'confidence': 0.9,
                'word_count': result.get('word_count', 0),
            }]
            self.stats['pages_extracted'] += 1
        else:
            self.stats['errors'].append(f"Unsupported extension: {ext}")
            self.stats['files_failed'] += 1
            return False

        # ── Classify and insert each page ──
        total_inserted = 0
        full_text = '\n'.join(p['text'] for p in pages if p.get('text'))

        # Lane classification on full document text
        lane_result = classify_lane(full_text)
        lane = lane_result['lane']

        # Brain routing on full document text
        target_brains = classify_brain(full_text)

        for page in pages:
            text = page.get('text', '').strip()
            if not text or len(text) < 10:
                continue

            extraction = {
                'text': text,
                'page_num': page.get('page_num'),
                'confidence': page.get('confidence', 0.5),
                'word_count': page.get('word_count', 0),
            }

            for brain_name in target_brains:
                try:
                    inserted = self.inserter.insert_to_brain(
                        brain_name, extraction, file_path, lane)
                    total_inserted += len(inserted)
                except Exception as e:
                    self.stats['errors'].append(
                        f"{file_path} p{page.get('page_num', '?')} "
                        f"→ {brain_name}: {e}")

        self.stats['files_processed'] += 1
        self.stats['items_inserted'] += total_inserted
        return total_inserted > 0

    # ------------------------------------------------------------------
    # Queue helpers
    # ------------------------------------------------------------------

    def _update_queue_status(self, queue_id: int, status: str,
                             error_message: str = None):
        """Update extraction_queue item status with retry."""
        def _do_update():
            with self.bm.open_brain('cross_brain_index') as conn:
                now = datetime.utcnow().isoformat()
                if status == 'processing':
                    conn.execute(
                        """UPDATE extraction_queue
                           SET status = ?, started_at = ?, attempts = attempts + 1
                           WHERE queue_id = ?""",
                        (status, now, queue_id))
                else:
                    conn.execute(
                        """UPDATE extraction_queue
                           SET status = ?, completed_at = ?, error_message = ?
                           WHERE queue_id = ?""",
                        (status, now, error_message, queue_id))
                conn.commit()

        try:
            _retry_on_lock(_do_update)
        except Exception:
            pass  # queue status update is non-fatal

    def _print_progress(self, current: int, total: int):
        """Print a checkpoint progress line."""
        elapsed_errors = len(self.stats['errors'])
        print(f"  [{current}/{total}] processed={self.stats['files_processed']} "
              f"pages={self.stats['pages_extracted']} "
              f"inserted={self.stats['items_inserted']} "
              f"errors={elapsed_errors}")

    # ------------------------------------------------------------------
    # Status reporting
    # ------------------------------------------------------------------

    def get_status(self) -> dict:
        """Get comprehensive status of the extraction system."""
        queue_status = self.bm.get_queue_status()
        brain_stats = self.bm.get_brain_stats()

        total_rows = 0
        total_tables = 0
        for brain_name, tables in brain_stats.items():
            if isinstance(tables, dict) and 'error' not in tables:
                total_tables += len(tables)
                total_rows += sum(c for c in tables.values() if c > 0)

        return {
            'queue': queue_status,
            'brains': brain_stats,
            'total_tables': total_tables,
            'total_rows': total_rows,
            'engine_stats': self.stats,
            'inserter_stats': self.inserter.stats,
        }

    def print_status(self):
        """Print a formatted status report."""
        status = self.get_status()

        print("\n" + "=" * 60)
        print("  EXTRACTION ENGINE — STATUS REPORT")
        print("=" * 60)

        # Queue status
        queue = status['queue']
        counts = queue.get('counts', {})
        print(f"\n  Extraction Queue:")
        for s, c in sorted(counts.items()):
            print(f"    {s:<15} {c:>6}")
        print(f"    {'TOTAL':<15} {sum(counts.values()):>6}")

        # Brain stats
        print(f"\n  Brain Database Summary:")
        print(f"    Total tables: {status['total_tables']}")
        print(f"    Total rows:   {status['total_rows']}")

        for brain_name, tables in status['brains'].items():
            if isinstance(tables, dict) and 'error' not in tables:
                brain_rows = sum(c for c in tables.values() if c > 0)
                if brain_rows > 0:
                    print(f"    {brain_name:<30} {brain_rows:>8} rows")

        # Engine stats
        if status['engine_stats']['files_processed'] > 0:
            es = status['engine_stats']
            print(f"\n  Last Run Stats:")
            print(f"    Files processed: {es['files_processed']}")
            print(f"    Files failed:    {es['files_failed']}")
            print(f"    Pages extracted: {es['pages_extracted']}")
            print(f"    Items inserted:  {es['items_inserted']}")
            if es['errors']:
                print(f"    Errors ({len(es['errors'])}):")
                for err in es['errors'][:5]:
                    print(f"      - {err[:100]}")

        # Inserter stats
        ins = status['inserter_stats']
        active_inserts = {k: v for k, v in ins.items() if v > 0}
        if active_inserts:
            print(f"\n  Insertion Breakdown:")
            for k, v in active_inserts.items():
                print(f"    {k:<35} {v:>6}")

        print("\n" + "=" * 60)


# ═══════════════════════════════════════════════════════════════════════════
# CLI Entry Point
# ═══════════════════════════════════════════════════════════════════════════

def main():
    """CLI entry point for the Extraction Engine."""
    parser = argparse.ArgumentParser(
        description='Multi-Brain Universe — Extraction Engine (BRAIN-04)',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python extraction_engine.py --scan-dir "C:\\evidence\\pdfs"
  python extraction_engine.py --process-queue --limit 100
  python extraction_engine.py --file "C:\\docs\\motion.pdf"
  python extraction_engine.py --status
        """)

    parser.add_argument('--scan-dir', type=str,
                        help='Scan directory for files, queue and process them')
    parser.add_argument('--process-queue', action='store_true',
                        help='Process pending items in the extraction queue')
    parser.add_argument('--status', action='store_true',
                        help='Show extraction queue and brain statistics')
    parser.add_argument('--file', type=str,
                        help='Process a single file directly')
    parser.add_argument('--limit', type=int, default=0,
                        help='Max files to process (0 = unlimited)')
    parser.add_argument('--priority', type=int, default=5,
                        help='Queue priority for scanned files (1=highest, 10=lowest)')
    parser.add_argument('--brain-dir', type=str, default=None,
                        help='Override brain database directory')

    args = parser.parse_args()

    # Require at least one action
    if not any([args.scan_dir, args.process_queue, args.status, args.file]):
        parser.print_help()
        sys.exit(1)

    engine = ExtractionEngine(brain_dir=args.brain_dir)

    if args.status:
        engine.print_status()
        return

    if args.file:
        print(f"Processing single file: {args.file}")
        ok = engine.process_file(args.file)
        if ok:
            print(f"  ✅ Success — {engine.stats['items_inserted']} items inserted")
        else:
            print(f"  ❌ Failed")
            for err in engine.stats['errors']:
                print(f"    {err}")
        engine.print_status()
        return

    if args.scan_dir:
        queued = engine.scan_directory(args.scan_dir, priority=args.priority)
        if queued > 0:
            print(f"\nProcessing {queued} queued files...")
            engine.process_queue(limit=args.limit)
        engine.print_status()
        return

    if args.process_queue:
        engine.process_queue(limit=args.limit)
        engine.print_status()
        return


if __name__ == '__main__':
    main()
