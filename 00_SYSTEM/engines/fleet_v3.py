#!/usr/bin/env python3
"""
LitigationOS Agent Fleet v3 — Production-Grade Harvester
=========================================================
Major upgrade over v2: threaded workers, skill engine integration,
enrichment cycles with delta convergence, SHA256 dedup, atomic writes,
exponential-backoff retry, graceful shutdown, JSONL journals, and
checkpoint/resume with full audit trail.
"""

import os, re, json, hashlib, time, signal, sys, tempfile, traceback, threading
from pathlib import Path
from datetime import datetime, timezone
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Dict, List, Optional, Any, Set, Tuple
from collections import defaultdict

# ── PATH SETUP ──
for p in ["D:/TEMP", "D:/TEMP/pylibs"]:
    if p not in sys.path:
        sys.path.insert(0, p)

# ── Skill Engine import (fail-soft) ──
try:
    from frankenstein_engine import SkillEngine
    SKILL_ENGINE = SkillEngine()
    HAS_SKILL_ENGINE = True
except Exception:
    SKILL_ENGINE = None
    HAS_SKILL_ENGINE = False

# ═══════════════════════════════════════════════════════════════════════
# CONFIGURATION
# ═══════════════════════════════════════════════════════════════════════

SCANS_DIR       = "C:/Users/andre/Scans"
JOURNALS_ROOT   = "C:/Users/andre/Desktop/AGENT_JOURNALS"
DASHBOARD_DIR   = "C:/Users/andre/Desktop/AGENT_JOURNALS/00_FLEET_DASHBOARD"
STATE_FILE      = "D:/TEMP/fleet_v3_state.json"
ERROR_LOG       = "D:/TEMP/fleet_v3_errors.log"

WORKERS         = 10
CHECKPOINT_EVERY = 500
MAX_FILE_SIZE   = 50 * 1024 * 1024   # 50 MB
FILE_TIMEOUT    = 30                   # seconds
MAX_TEXT_CHARS  = 50_000
RETRY_ATTEMPTS  = 3
DEDUP_PREFIX_LEN = 500
ENRICHMENT_DELTA_THRESHOLD = 5         # stop enrichment when new findings < threshold

GOOD_EXTS = {
    '.txt', '.md', '.pdf', '.jsonl', '.csv', '.json',
    '.msg', '.docx', '.eml', '.rtf', '.log', '.yaml', '.yml', '.toml',
}

SKIP_DIRS = {
    '__pycache__', 'node_modules', '.git', 'venv', '.venv',
    '.tox', '.mypy_cache', '.pytest_cache',
}

# ═══════════════════════════════════════════════════════════════════════
# ERROR CATEGORIES
# ═══════════════════════════════════════════════════════════════════════

class ErrorCategory:
    IO       = "IOError"
    UNICODE  = "UnicodeError"
    PERM     = "PermissionError"
    TIMEOUT  = "TimeoutError"
    PARSE    = "ParseError"
    UNKNOWN  = "UnknownError"

def categorize_error(exc: Exception) -> str:
    if isinstance(exc, PermissionError):
        return ErrorCategory.PERM
    if isinstance(exc, (UnicodeDecodeError, UnicodeEncodeError)):
        return ErrorCategory.UNICODE
    if isinstance(exc, (IOError, OSError)):
        return ErrorCategory.IO
    if isinstance(exc, TimeoutError):
        return ErrorCategory.TIMEOUT
    if isinstance(exc, (json.JSONDecodeError, ValueError)):
        return ErrorCategory.PARSE
    return ErrorCategory.UNKNOWN

# ═══════════════════════════════════════════════════════════════════════
# AGENT DEFINITIONS (50 agents, enhanced regex)
# ═══════════════════════════════════════════════════════════════════════

AGENTS: Dict[str, List[str]] = {
    # Group 1 (01-08): Legal Authority
    "01_MCL":          [r'MCL\s*\d+\.\d+', r'Michigan\s+Compiled\s+Law'],
    "02_MCR":          [r'MCR\s*\d+\.\d+', r'Michigan\s+Court\s+Rule'],
    "03_CASELAW":      [r'\bv\.\s+\w+', r'\d+\s+Mich\s+(App\s+)?\d+', r'\d+\s+NW\.?\s*2d\s+\d+', r'\d+\s+F\.\s*\d+d\s+\d+'],
    "04_USC":          [r'\d+\s+U\.?S\.?C\.?\s*§?\s*\d+', r'42\s+USC\s+1983', r'Section\s+1983'],
    "05_CFR":          [r'\d+\s+C\.?F\.?R\.?\s*§?\s*\d+'],
    "06_CONSTITUTION": [r'(?:First|Fourth|Fifth|Sixth|Fourteenth)\s+Amendment', r'Due\s+Process', r'Equal\s+Protection', r'Art(?:icle)?\s+\d+\s*§\s*\d+'],
    "07_BENCHBOOK":    [r'[Bb]enchbook', r'MJI', r'Michigan\s+Judicial\s+Institute'],
    "08_AUTHORITY":    [r'[Cc]anon\s+\d+', r'MRPC\s+\d+', r'Rule\s+of\s+Professional'],
    # Group 2 (09-17): Person tracking
    "09_ANDREW":       [r'Andrew\s+(?:J\.?\s+)?Pigors', r'\bPigors\b', r'\bAJP\b', r'[Ff]ather', r'[Pp]ro\s+[Ss]e'],
    "10_EMILY":        [r'Emily\s+(?:Rose\s+)?Watson', r'Emily\s+Watson', r'[Mm]other', r'[Rr]espondent'],
    "11_ALBERT":       [r'Albert\s+Watson', r'[Gg]randfather'],
    "12_LORI":         [r'Lori\s+Watson', r'[Gg]randmother'],
    "13_CODY":         [r'Cody\s+Watson', r'\b[Uu]ncle\b'],
    "14_MCNEILL":      [r'McNeill', r'Judge\s+Jenny', r'[Pp]residing\s+[Jj]udge'],
    "15_RUSCO":        [r'Rusco', r'[Oo]pposing\s+[Cc]ounsel'],
    "16_CHILD":        [r'L\.?D\.?W\.?', r'\b[Cc]hild\b', r'\b[Mm]inor\b', r'\b[Ss]on\b', r'\b[Bb]aby\b', r'\b[Tt]oddler\b'],
    "17_PERSONS":      [r'[A-Z][a-z]+\s+[A-Z][a-z]+', r'\b[Ww]itness\b', r'\b[Aa]ttorney\b', r'\b[Oo]fficer\b'],
    # Group 3 (18-25): Issue analysis
    "18_ALIENATION":   [r'[Aa]lienation', r'[Ee]strangement', r'[Bb]onding', r'[Aa]ttachment', r'[Pp]arental\s+[Aa]lienation'],
    "19_CUSTODY":      [r'[Cc]ustody', r'[Pp]arenting\s+[Tt]ime', r'[Vv]isitation', r'[Pp]lacement'],
    "20_PPO":          [r'\bPPO\b', r'[Pp]rotective\s+[Oo]rder', r'[Rr]estraining', r'MCL\s+600\.2950'],
    "21_DUE_PROCESS":  [r'[Dd]ue\s+[Pp]rocess', r'\b[Nn]otice\b', r'[Hh]earing\s+[Rr]ight', r'\b[Pp]rocedural\b'],
    "22_MISCONDUCT":   [r'[Mm]isconduct', r'\b[Bb]ias\b', r'[Pp]rejudice', r'[Ee]x\s+[Pp]arte', r'[Aa]buse\s+of\s+[Dd]iscretion'],
    "23_FRAUD":        [r'[Ff]raud', r'[Mm]isrepresent', r'[Dd]ecei', r'[Ff]alsif', r'[Pp]erjur'],
    "24_CONTEMPT":     [r'[Cc]ontempt', r'[Ss]how\s+[Cc]ause', r'[Ss]anction', r'[Pp]urge'],
    "25_VIOLATIONS":   [r'[Vv]iolat', r'[Ii]nfract', r'[Bb]reach', r'[Nn]on-?[Cc]omplian'],
    # Group 4 (26-30): Procedural
    "26_HEARINGS":     [r'[Hh]earing', r'[Cc]ourt\s+[Dd]ate', r'[Dd]ocket', r'[Cc]alendar'],
    "27_ORDERS":       [r'\b[Oo]rder\b', r'[Jj]udgment', r'[Dd]ecree', r'[Ss]tipulat'],
    "28_MOTIONS":      [r'[Mm]otion', r'[Pp]etition', r'[Ff]iling', r'[Rr]esponse', r'\b[Bb]rief\b'],
    "29_DISCOVERY":    [r'[Dd]iscovery', r'[Ii]nterrogator', r'[Dd]eposition', r'[Ss]ubpoena', r'\bFOIA\b'],
    "30_EVIDENCE":     [r'[Ee]xhibit', r'\b[Ee]vidence\b', r'[Aa]ttachment', r'[Dd]ocument'],
    # Group 5 (31-40): Deep analysis
    "31_BEST_INT":     [r'[Bb]est\s+[Ii]nterest', r'MCL\s+722\.23', r'[Ff]actor\s+[a-l]', r'\bBIF\b'],
    "32_FINANCIAL":    [r'\$\s*[\d,]+', r'\b[Ff]ee\b', r'\b[Cc]ost\b', r'\b[Bb]ond\b', r'\b[Dd]amage\b', r'[Rr]estitution'],
    "33_TIMELINE":     [r'\d{1,2}/\d{1,2}/\d{2,4}', r'\d{4}-\d{2}-\d{2}', r'(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)\w*\s+\d{1,2}'],
    "34_NARRATIVE":    [r'[Ss]tory', r'[Nn]arrative', r'[Aa]ccount', r'[Tt]estimon'],
    "35_WELFARE":      [r'\bCPS\b', r'[Ww]elfare', r'\bDHHS\b', r'[Ss]ocial\s+[Ww]orker'],
    "36_BOND":         [r'\$\s*250', r'\b[Bb]ond\b', r'[Ss]urety', r'MC-?20', r'[Ff]ee\s+[Ww]aiver'],
    "37_COMMS":        [r'\b[Tt]ext\b', r'\b[Ee]mail\b', r'\b[Mm]essage\b', r'[Cc]ommunicat', r'AppClose'],
    "38_CREDIBILITY":  [r'[Cc]redibl', r'\b[Ll]ie\b', r'\b[Ff]alse\b', r'[Ii]nconsist', r'[Cc]ontradict'],
    "39_PATTERNS":     [r'[Pp]attern', r'[Ss]ystemic', r'[Rr]epeat', r'[Hh]istory\s+of'],
    "40_IMPACT":       [r'\b[Hh]arm\b', r'\b[Dd]amage\b', r'[Tt]rauma', r'[Ss]uffer', r'[Ii]mpact'],
    # Group 6 (41-50): Appellate + specialized
    "41_APPELLATE":    [r'[Aa]ppeal', r'\bCOA\b', r'\bMSC\b', r'MCR\s+7\.\d+', r'[Ss]tandard\s+of\s+[Rr]eview'],
    "42_EMERGENCY":    [r'[Ee]mergency', r'[Ee]x\s+[Pp]arte', r'[Tt]emporary', r'[Ii]mmediate', r'[Uu]rgent'],
    "43_REMEDIES":     [r'[Rr]emedy', r'[Rr]elief', r'[Rr]estore', r'[Rr]einstate', r'[Mm]odif[iy]'],
    "44_REVIEW":       [r'[Rr]eview', r'[Rr]econsider', r'[Rr]ehear', r'MCR\s+2\.119'],
    "45_PROCEDURAL":   [r'[Pp]rocedur', r'[Jj]urisdiction', r'[Vv]enue', r'[Ss]tanding'],
    "46_FOC":          [r'\bFOC\b', r'[Ff]riend\s+of\s+(?:the\s+)?[Cc]ourt', r'[Rr]eferee'],
    "47_POLICE":       [r'[Pp]olice', r'\b[Oo]fficer\b', r'[Aa]rrest', r'\bCAD\b', r'[Ii]ncident\s+[Rr]eport'],
    "48_MEDICAL":      [r'[Mm]edical', r'[Hh]ealth[Ww]est', r'DeAugustine', r'[Ee]valuation', r'[Tt]herapy'],
    "49_MEEK":         [r'Meek', r'Shady\s+Oaks', r'Bluewater', r'[Ll]andlord', r'[Hh]ousing'],
    "50_CASE_NO":      [r'2024-001507', r'2023-5907', r'2025-002760', r'[Cc]ase\s+[Nn]o'],
}

# Pre-compile all regex patterns per agent
COMPILED: Dict[str, List[re.Pattern]] = {}
for _aid, _pats in AGENTS.items():
    COMPILED[_aid] = [re.compile(p, re.IGNORECASE) for p in _pats]

# ═══════════════════════════════════════════════════════════════════════
# LOGGING
# ═══════════════════════════════════════════════════════════════════════

_log_lock = threading.Lock()
_journal_locks: Dict[str, threading.Lock] = defaultdict(threading.Lock)

def log_error(msg: str, category: str = "GENERAL") -> None:
    ts = datetime.now(timezone.utc).isoformat()
    line = f"[{ts}] [{category}] {msg}\n"
    with _log_lock:
        with open(ERROR_LOG, "a", encoding="utf-8") as f:
            f.write(line)

def log_info(msg: str) -> None:
    print(f"[{datetime.now().strftime('%H:%M:%S')}] {msg}", flush=True)

# ═══════════════════════════════════════════════════════════════════════
# ATOMIC WRITES
# ═══════════════════════════════════════════════════════════════════════

def atomic_json_write(filepath: str, data: Any) -> None:
    """Write JSON via temp file + rename to prevent corruption."""
    dirpath = os.path.dirname(filepath) or "."
    os.makedirs(dirpath, exist_ok=True)
    fd, tmp = tempfile.mkstemp(dir=dirpath, suffix=".tmp")
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, default=str)
        # On Windows, remove target first if exists
        if os.path.exists(filepath):
            os.replace(tmp, filepath)
        else:
            os.rename(tmp, filepath)
    except Exception:
        if os.path.exists(tmp):
            os.unlink(tmp)
        raise

# ═══════════════════════════════════════════════════════════════════════
# STATE & CHECKPOINT
# ═══════════════════════════════════════════════════════════════════════

class HarvesterState:
    """Thread-safe state manager with atomic checkpoint writes."""

    def __init__(self, state_path: str = STATE_FILE):
        self.state_path = state_path
        self._lock = threading.Lock()
        self.done_files: Set[str] = set()
        self.file_hashes: Dict[str, str] = {}       # filepath -> sha256
        self.hash_to_path: Dict[str, str] = {}      # sha256 -> first filepath (dedup)
        self.dedup_skipped: List[Dict] = []
        self.agent_stats: Dict[str, int] = {}
        self.error_counts: Dict[str, int] = defaultdict(int)
        self.total_errors: int = 0
        self.total_hits: int = 0
        self.enrichment_cycle: int = 0
        self.run_id: str = hashlib.sha1(datetime.now().isoformat().encode()).hexdigest()[:12]
        self.start_time: float = time.time()
        self._files_since_checkpoint: int = 0

    def load(self) -> None:
        if not os.path.exists(self.state_path):
            return
        try:
            with open(self.state_path, "r", encoding="utf-8") as f:
                d = json.load(f)
            done = d.get("done_files", [])
            if isinstance(done, dict):
                done = list(done.keys())
            self.done_files = set(done)
            self.file_hashes = d.get("file_hashes", {})
            self.hash_to_path = d.get("hash_to_path", {})
            self.agent_stats = d.get("agent_stats", {})
            self.total_errors = d.get("total_errors", 0)
            self.total_hits = d.get("total_hits", 0)
            self.enrichment_cycle = d.get("enrichment_cycle", 0)
            ec = d.get("error_counts", {})
            self.error_counts = defaultdict(int, ec)
            log_info(f"  Resumed: {len(self.done_files)} files, {self.total_errors} prior errors, cycle {self.enrichment_cycle}")
        except Exception as e:
            log_error(f"State load failed: {e}", "STATE")

    def save(self, force: bool = False) -> None:
        with self._lock:
            if not force and self._files_since_checkpoint < CHECKPOINT_EVERY:
                return
            self._do_save()

    def _do_save(self) -> None:
        data = {
            "run_id": self.run_id,
            "done_files": list(self.done_files),
            "file_hashes": self.file_hashes,
            "hash_to_path": self.hash_to_path,
            "agent_stats": self.agent_stats,
            "error_counts": dict(self.error_counts),
            "total_errors": self.total_errors,
            "total_hits": self.total_hits,
            "enrichment_cycle": self.enrichment_cycle,
            "n_done": len(self.done_files),
            "last_save": datetime.now(timezone.utc).isoformat(),
        }
        atomic_json_write(self.state_path, data)
        self._files_since_checkpoint = 0

    def mark_done(self, filepath: str, file_hash: str, hits: int) -> None:
        with self._lock:
            self.done_files.add(filepath)
            self.file_hashes[filepath] = file_hash
            self.total_hits += hits
            self._files_since_checkpoint += 1
        if self._files_since_checkpoint >= CHECKPOINT_EVERY:
            self.save(force=True)

    def mark_error(self, filepath: str, category: str) -> None:
        with self._lock:
            self.done_files.add(filepath)
            self.total_errors += 1
            self.error_counts[category] += 1
            self._files_since_checkpoint += 1

    def add_agent_hits(self, agent_id: str, count: int) -> None:
        with self._lock:
            self.agent_stats[agent_id] = self.agent_stats.get(agent_id, 0) + count

    def register_hash(self, filepath: str, sha: str) -> Optional[str]:
        """Register file hash. Returns existing path if duplicate, else None."""
        with self._lock:
            if sha in self.hash_to_path:
                dup_of = self.hash_to_path[sha]
                self.dedup_skipped.append({"file": filepath, "duplicate_of": dup_of, "hash": sha})
                return dup_of
            self.hash_to_path[sha] = filepath
            return None

# ═══════════════════════════════════════════════════════════════════════
# FILE I/O
# ═══════════════════════════════════════════════════════════════════════

def sha256_file(filepath: str) -> str:
    h = hashlib.sha256()
    with open(filepath, "rb") as f:
        while True:
            chunk = f.read(65536)
            if not chunk:
                break
            h.update(chunk)
    return h.hexdigest()


def read_file_text(filepath: str) -> str:
    """Read text from file, handling PDFs and multiple encodings."""
    ext = os.path.splitext(filepath)[1].lower()
    if ext == ".pdf":
        try:
            import fitz
            doc = fitz.open(filepath)
            text = ""
            for page in doc:
                text += page.get_text()
                if len(text) >= MAX_TEXT_CHARS:
                    break
            doc.close()
            return text[:MAX_TEXT_CHARS]
        except Exception:
            return ""
    # Text-based files
    for enc in ("utf-8", "latin-1", "cp1252"):
        try:
            with open(filepath, "r", encoding=enc, errors="replace") as f:
                return f.read(MAX_TEXT_CHARS)
        except Exception:
            continue
    return ""

# ═══════════════════════════════════════════════════════════════════════
# NEAR-DUPLICATE DETECTION
# ═══════════════════════════════════════════════════════════════════════

_near_dup_lock = threading.Lock()
_near_dup_prefixes: Dict[str, str] = {}   # prefix_hash -> first filepath

def check_near_duplicate(filepath: str, text: str) -> Optional[str]:
    """Return path of near-duplicate if first 500 chars match, else None."""
    prefix = text[:DEDUP_PREFIX_LEN].strip()
    if len(prefix) < 50:
        return None
    ph = hashlib.md5(prefix.encode("utf-8", errors="replace")).hexdigest()
    with _near_dup_lock:
        if ph in _near_dup_prefixes:
            return _near_dup_prefixes[ph]
        _near_dup_prefixes[ph] = filepath
    return None

# ═══════════════════════════════════════════════════════════════════════
# SKILL ENGINE WRAPPERS
# ═══════════════════════════════════════════════════════════════════════

def run_citation_mining(text: str) -> List[str]:
    """Skill 13 — deep citation mining."""
    if not HAS_SKILL_ENGINE:
        return []
    try:
        result = SKILL_ENGINE.run("citation_mining", text=text)
        cites = result.get("citations", {})
        flat = []
        for cat_list in cites.values():
            if isinstance(cat_list, list):
                flat.extend(cat_list)
        return flat
    except Exception:
        return []

def run_violation_detection(text: str) -> List[Dict]:
    """Skill 08 — higher court violation engine on legal docs."""
    if not HAS_SKILL_ENGINE:
        return []
    try:
        result = SKILL_ENGINE.run("misconduct_detection", text=text)
        return result.get("findings", [])
    except Exception:
        return []

def run_person_extraction(text: str) -> List[str]:
    """Skill 17 — person extraction via journal synthesis patterns."""
    persons = set()
    for m in re.finditer(r'\b([A-Z][a-z]{2,15})\s+([A-Z][a-z]{2,15})\b', text):
        persons.add(f"{m.group(1)} {m.group(2)}")
    return list(persons)[:50]

def run_bif_scoring(text: str) -> Dict:
    """Skill 06 — BIF scoring on custody-related content."""
    if not HAS_SKILL_ENGINE:
        return {}
    try:
        return SKILL_ENGINE.run("harm_quantification", text=text)
    except Exception:
        return {}

# ═══════════════════════════════════════════════════════════════════════
# JOURNAL WRITER (JSONL, thread-safe)
# ═══════════════════════════════════════════════════════════════════════

def write_journal_entry(agent_id: str, entry: Dict) -> None:
    """Append one JSONL line to the agent's journal file."""
    journal_dir = os.path.join(JOURNALS_ROOT, agent_id)
    os.makedirs(journal_dir, exist_ok=True)
    journal_file = os.path.join(journal_dir, "journal.jsonl")
    line = json.dumps(entry, default=str, ensure_ascii=False) + "\n"
    with _journal_locks[agent_id]:
        with open(journal_file, "a", encoding="utf-8") as f:
            f.write(line)

# ═══════════════════════════════════════════════════════════════════════
# CORE FILE PROCESSOR (per-file, with retry + skill engine)
# ═══════════════════════════════════════════════════════════════════════

def classify_evidence_type(filepath: str, text: str) -> str:
    ext = os.path.splitext(filepath)[1].lower()
    lower = text[:2000].lower()
    if ext == ".pdf":
        return "pdf_document"
    if any(w in lower for w in ("order", "decree", "judgment", "court")):
        return "court_document"
    if any(w in lower for w in ("motion", "petition", "brief")):
        return "filing"
    if any(w in lower for w in ("dear", "re:", "from:", "to:", "subject:")):
        return "correspondence"
    if ext in (".csv", ".jsonl"):
        return "data_file"
    return "general_document"


def compute_relevance_score(findings: Dict) -> float:
    """0.0-1.0 relevance score based on finding density."""
    total = (
        len(findings.get("citations", [])) * 3
        + len(findings.get("persons", [])) * 1
        + len(findings.get("dates", [])) * 1
        + len(findings.get("violations", [])) * 5
    )
    return min(1.0, total / 30.0)


def process_single_file(filepath: str, state: HarvesterState) -> int:
    """Process one file through all 50 agents + skill engine. Returns hit count."""
    # -- Size gate --
    try:
        fsize = os.path.getsize(filepath)
    except OSError:
        return 0
    if fsize > MAX_FILE_SIZE:
        log_error(f"Skipped (>{MAX_FILE_SIZE//1024//1024}MB): {filepath}", "SIZE")
        state.mark_done(filepath, "SKIPPED_SIZE", 0)
        return 0

    # -- SHA256 dedup --
    file_hash = sha256_file(filepath)
    dup_of = state.register_hash(filepath, file_hash)
    if dup_of:
        log_error(f"Exact duplicate skipped: {filepath} == {dup_of}", "DEDUP")
        state.mark_done(filepath, file_hash, 0)
        return 0

    # -- Read text --
    text = read_file_text(filepath)
    if not text or len(text.strip()) < 20:
        state.mark_done(filepath, file_hash, 0)
        return 0

    # -- Near-duplicate check --
    near_dup = check_near_duplicate(filepath, text)
    if near_dup:
        log_error(f"Near-duplicate skipped: {filepath} ~= {near_dup}", "NEAR_DEDUP")
        state.mark_done(filepath, file_hash, 0)
        return 0

    rel_path = os.path.relpath(filepath, SCANS_DIR)
    ts = datetime.now(timezone.utc).isoformat()
    ev_type = classify_evidence_type(filepath, text)

    # -- Skill engine analysis (run once, share across agents) --
    citations = run_citation_mining(text)
    persons = run_person_extraction(text)
    violations = run_violation_detection(text) if ev_type in ("court_document", "filing") else []
    bif = run_bif_scoring(text) if any(w in text.lower() for w in ("custody", "best interest", "factor", "bif", "child")) else {}

    # -- Date extraction --
    dates_found = list(set(
        m.group() for m in re.finditer(r'\d{1,2}/\d{1,2}/\d{2,4}|\d{4}-\d{2}-\d{2}', text)
    ))[:30]

    # -- Build common findings dict --
    findings = {
        "citations": citations,
        "persons": persons,
        "dates": dates_found,
        "violations": [v.get("match", "") for v in violations] if violations else [],
        "evidence_type": ev_type,
        "relevance_score": 0.0,
        "bif_factors_found": bif.get("factors_scored", 0) if bif else 0,
    }
    findings["relevance_score"] = compute_relevance_score(findings)

    # -- Run all 50 agent regex patterns --
    total_hits = 0
    for agent_id, patterns in COMPILED.items():
        matches = []
        for pat in patterns:
            for m in pat.finditer(text):
                start = max(0, m.start() - 80)
                end = min(len(text), m.end() + 80)
                context = text[start:end].replace("\n", " ").strip()
                matches.append({"match": m.group(), "context": context})
                if len(matches) >= 10:
                    break
            if len(matches) >= 10:
                break

        if matches:
            total_hits += len(matches)
            state.add_agent_hits(agent_id, len(matches))
            entry = {
                "timestamp": ts,
                "file_path": rel_path,
                "file_hash": file_hash,
                "findings": findings,
                "agent_matches": [{"match": m["match"], "context": m["context"]} for m in matches[:10]],
                "match_count": len(matches),
            }
            write_journal_entry(agent_id, entry)

    state.mark_done(filepath, file_hash, total_hits)
    return total_hits


def process_file_with_retry(filepath: str, state: HarvesterState) -> int:
    """Wrap process_single_file with exponential-backoff retry."""
    for attempt in range(1, RETRY_ATTEMPTS + 1):
        try:
            return process_single_file(filepath, state)
        except Exception as exc:
            cat = categorize_error(exc)
            if attempt < RETRY_ATTEMPTS:
                delay = 0.5 * (2 ** (attempt - 1))   # 0.5s, 1s, 2s
                time.sleep(delay)
                log_error(f"Retry {attempt}/{RETRY_ATTEMPTS} for {filepath}: [{cat}] {exc}", cat)
            else:
                log_error(f"FAILED after {RETRY_ATTEMPTS} attempts: {filepath}: [{cat}] {exc}\n{traceback.format_exc()}", cat)
                state.mark_error(filepath, cat)
    return 0

# ═══════════════════════════════════════════════════════════════════════
# FILE DISCOVERY
# ═══════════════════════════════════════════════════════════════════════

def discover_files(root: str = SCANS_DIR) -> List[str]:
    """Walk tree, yield high-value files sorted by size (smallest first)."""
    results = []
    for dirpath, dirs, files in os.walk(root):
        dirs[:] = [d for d in dirs if d not in SKIP_DIRS and not d.startswith(".")]
        for fname in files:
            ext = os.path.splitext(fname)[1].lower()
            if ext in GOOD_EXTS:
                results.append(os.path.join(dirpath, fname))
    results.sort(key=lambda p: os.path.getsize(p) if os.path.exists(p) else 0)
    return results

# ═══════════════════════════════════════════════════════════════════════
# ENRICHMENT CYCLES (Delta Convergence)
# ═══════════════════════════════════════════════════════════════════════

def _load_all_journal_entries() -> Dict[str, List[Dict]]:
    """Load all JSONL journals into memory keyed by agent_id."""
    journals: Dict[str, List[Dict]] = {}
    for agent_id in AGENTS:
        jf = os.path.join(JOURNALS_ROOT, agent_id, "journal.jsonl")
        if not os.path.exists(jf):
            continue
        entries = []
        with open(jf, "r", encoding="utf-8", errors="replace") as f:
            for line in f:
                line = line.strip()
                if line:
                    try:
                        entries.append(json.loads(line))
                    except json.JSONDecodeError:
                        pass
        journals[agent_id] = entries
    return journals


def enrichment_cycle_1_crossref(journals: Dict[str, List[Dict]]) -> int:
    """Cross-reference citations across agent journals."""
    cite_index: Dict[str, List[str]] = defaultdict(list)  # citation -> [agents]
    for agent_id, entries in journals.items():
        for e in entries:
            for c in e.get("findings", {}).get("citations", []):
                cite_index[c].append(agent_id)
    cross_hits = sum(1 for agents in cite_index.values() if len(set(agents)) > 1)
    return cross_hits


def enrichment_cycle_2_score_rank(journals: Dict[str, List[Dict]]) -> int:
    """Score and rank evidence by relevance across all journals."""
    scores: List[Tuple[float, str]] = []
    for agent_id, entries in journals.items():
        for e in entries:
            score = e.get("findings", {}).get("relevance_score", 0)
            fp = e.get("file_path", "")
            scores.append((score, fp))
    scores.sort(key=lambda x: -x[0])
    high = sum(1 for s, _ in scores if s >= 0.5)
    return high


def enrichment_cycle_3_contradictions(journals: Dict[str, List[Dict]]) -> int:
    """Detect contradictions — files where opposing agents both fired."""
    file_agents: Dict[str, Set[str]] = defaultdict(set)
    for agent_id, entries in journals.items():
        for e in entries:
            fp = e.get("file_path", "")
            file_agents[fp].add(agent_id)
    contradiction_pairs = [
        ("09_ANDREW", "10_EMILY"),
        ("22_MISCONDUCT", "08_AUTHORITY"),
        ("23_FRAUD", "38_CREDIBILITY"),
    ]
    found = 0
    for fp, agents in file_agents.items():
        for a, b in contradiction_pairs:
            if a in agents and b in agents:
                found += 1
    return found


def enrichment_cycle_4_entity_graph(journals: Dict[str, List[Dict]]) -> int:
    """Build entity relationship graph from co-occurrence in files."""
    entity_pairs: Dict[Tuple[str, str], int] = defaultdict(int)
    for agent_id, entries in journals.items():
        for e in entries:
            persons = e.get("findings", {}).get("persons", [])
            for i in range(len(persons)):
                for j in range(i + 1, len(persons)):
                    pair = tuple(sorted([persons[i], persons[j]]))
                    entity_pairs[pair] += 1
    strong_links = sum(1 for v in entity_pairs.values() if v >= 2)
    return strong_links


def run_enrichment_cycles(state: HarvesterState) -> None:
    """Run all 4 enrichment cycles until delta converges."""
    log_info("═══ ENRICHMENT CYCLES ═══")
    cycles = [
        ("Cycle 1: Cross-reference citations", enrichment_cycle_1_crossref),
        ("Cycle 2: Score & rank evidence", enrichment_cycle_2_score_rank),
        ("Cycle 3: Detect contradictions", enrichment_cycle_3_contradictions),
        ("Cycle 4: Build entity graph", enrichment_cycle_4_entity_graph),
    ]
    journals = _load_all_journal_entries()
    if not journals:
        log_info("  No journals to enrich — skipping.")
        return

    for label, fn in cycles:
        state.enrichment_cycle += 1
        delta = fn(journals)
        log_info(f"  {label}: delta = {delta} new findings")
        if delta < ENRICHMENT_DELTA_THRESHOLD:
            log_info(f"  Converged at cycle {state.enrichment_cycle} (delta {delta} < {ENRICHMENT_DELTA_THRESHOLD})")
            break
    state.save(force=True)

# ═══════════════════════════════════════════════════════════════════════
# DASHBOARD
# ═══════════════════════════════════════════════════════════════════════

def write_dashboard(state: HarvesterState, total_files: int, processed: int) -> None:
    elapsed = time.time() - state.start_time
    rate = processed / elapsed if elapsed > 0 else 0
    dashboard = {
        "fleet_version": "v3.0",
        "run_id": state.run_id,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "skill_engine": "ACTIVE" if HAS_SKILL_ENGINE else "UNAVAILABLE",
        "files": {
            "total_discovered": total_files,
            "processed": len(state.done_files),
            "remaining": total_files - len(state.done_files),
            "dedup_skipped": len(state.dedup_skipped),
        },
        "performance": {
            "elapsed_seconds": round(elapsed, 1),
            "files_per_second": round(rate, 2),
            "workers": WORKERS,
        },
        "errors": {
            "total": state.total_errors,
            "by_category": dict(state.error_counts),
        },
        "total_hits": state.total_hits,
        "enrichment_cycles_completed": state.enrichment_cycle,
        "agent_stats": dict(sorted(state.agent_stats.items(), key=lambda x: -x[1])),
        "top_10_agents": dict(sorted(state.agent_stats.items(), key=lambda x: -x[1])[:10]),
    }
    os.makedirs(DASHBOARD_DIR, exist_ok=True)
    atomic_json_write(os.path.join(DASHBOARD_DIR, "fleet_v3_dashboard.json"), dashboard)

# ═══════════════════════════════════════════════════════════════════════
# PROGRESS BAR
# ═══════════════════════════════════════════════════════════════════════

class ProgressTracker:
    def __init__(self, total: int):
        self.total = total
        self.done = 0
        self.start = time.time()
        self._lock = threading.Lock()

    def tick(self, hits: int = 0) -> None:
        with self._lock:
            self.done += 1
            if self.done % 100 == 0 or self.done == self.total:
                self._print()

    def _print(self) -> None:
        elapsed = time.time() - self.start
        rate = self.done / elapsed if elapsed > 0 else 0
        remaining = self.total - self.done
        eta = remaining / rate if rate > 0 else 0
        pct = self.done / self.total * 100 if self.total else 0
        bar_len = 30
        filled = int(bar_len * self.done // max(self.total, 1))
        bar = "█" * filled + "░" * (bar_len - filled)
        print(
            f"\r  [{bar}] {pct:5.1f}% | {self.done}/{self.total} | "
            f"{rate:.1f} files/s | ETA {eta/60:.0f}m",
            end="", flush=True,
        )

# ═══════════════════════════════════════════════════════════════════════
# GRACEFUL SHUTDOWN
# ═══════════════════════════════════════════════════════════════════════

_shutdown_event = threading.Event()

def _shutdown_handler(signum, frame):
    log_info("\n⚠ Shutdown signal received — saving state...")
    _shutdown_event.set()

# ═══════════════════════════════════════════════════════════════════════
# MAIN
# ═══════════════════════════════════════════════════════════════════════

def main(rebuild: bool = False, workers: int = WORKERS) -> None:
    global WORKERS
    WORKERS = workers

    # Register signal handlers
    signal.signal(signal.SIGINT, _shutdown_handler)
    signal.signal(signal.SIGTERM, _shutdown_handler)

    log_info("╔══════════════════════════════════════════════╗")
    log_info("║   LitigationOS Fleet v3 — Production Harvester  ║")
    log_info("╚══════════════════════════════════════════════╝")
    log_info(f"  Skill Engine: {'ACTIVE' if HAS_SKILL_ENGINE else 'UNAVAILABLE (fail-soft)'}")
    log_info(f"  Workers: {WORKERS} | Checkpoint every: {CHECKPOINT_EVERY} files")
    log_info(f"  Target: {SCANS_DIR}")

    # -- State --
    state = HarvesterState()
    if rebuild:
        log_info("  REBUILD mode — starting from scratch")
        if os.path.exists(STATE_FILE):
            os.remove(STATE_FILE)
    else:
        state.load()

    # -- Discover --
    log_info("  Discovering files...")
    all_files = discover_files()
    total = len(all_files)
    pending = [f for f in all_files if f not in state.done_files]
    log_info(f"  Total: {total} | Already done: {total - len(pending)} | Pending: {len(pending)}")

    if not pending:
        log_info("  Nothing to process — running enrichment only.")
        run_enrichment_cycles(state)
        write_dashboard(state, total, 0)
        return

    # -- Ensure journal dirs exist --
    for agent_id in AGENTS:
        os.makedirs(os.path.join(JOURNALS_ROOT, agent_id), exist_ok=True)

    # -- Process --
    progress = ProgressTracker(len(pending))
    processed = 0

    with ThreadPoolExecutor(max_workers=WORKERS) as pool:
        futures = {}
        for fp in pending:
            if _shutdown_event.is_set():
                break
            fut = pool.submit(process_file_with_retry, fp, state)
            futures[fut] = fp

        for fut in as_completed(futures):
            if _shutdown_event.is_set():
                log_info("\n  Draining active workers...")
                break
            try:
                hits = fut.result(timeout=FILE_TIMEOUT + 5)
            except Exception as exc:
                fp = futures[fut]
                cat = categorize_error(exc)
                log_error(f"Worker exception: {fp}: {exc}", cat)
                state.mark_error(fp, cat)
                hits = 0
            processed += 1
            progress.tick(hits)

            # Periodic dashboard update
            if processed % 500 == 0:
                write_dashboard(state, total, processed)

    print()  # newline after progress bar
    state.save(force=True)
    log_info(f"  Harvest pass complete: {processed} files processed")

    # -- Enrichment --
    run_enrichment_cycles(state)

    # -- Dashboard --
    write_dashboard(state, total, processed)

    # -- Summary --
    elapsed = time.time() - state.start_time
    rate = processed / elapsed if elapsed > 0 else 0
    log_info("═══ FLEET v3 SUMMARY ═══")
    log_info(f"  Processed:  {processed} files in {elapsed/60:.1f} min ({rate:.1f} files/s)")
    log_info(f"  Total done: {len(state.done_files)}/{total}")
    log_info(f"  Total hits: {state.total_hits}")
    log_info(f"  Errors:     {state.total_errors} ({dict(state.error_counts)})")
    log_info(f"  Dedup:      {len(state.dedup_skipped)} exact duplicates skipped")
    log_info(f"  Enrichment: {state.enrichment_cycle} cycles completed")
    log_info(f"  State:      {STATE_FILE}")
    log_info(f"  Dashboard:  {DASHBOARD_DIR}/fleet_v3_dashboard.json")
    if state.agent_stats:
        log_info("  Top 10 agents:")
        for k, v in sorted(state.agent_stats.items(), key=lambda x: -x[1])[:10]:
            log_info(f"    {k}: {v} hits")


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="LitigationOS Fleet v3 Harvester")
    parser.add_argument("--rebuild", action="store_true", help="Ignore saved state; re-run from scratch")
    parser.add_argument("--workers", type=int, default=WORKERS, help=f"Thread pool size (default {WORKERS})")
    args = parser.parse_args()
    main(rebuild=args.rebuild, workers=args.workers)
