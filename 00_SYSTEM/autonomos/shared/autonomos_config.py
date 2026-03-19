"""
AUTONOMOS Shared Configuration
===============================
Extends LitigationOS config.py with AUTONOMOS-specific constants.
All AUTONOMOS modules import from here.
"""
import sys
from pathlib import Path

# ── Import LitigationOS config (handles its own failsafe) ──────────
_pipeline_dir = Path(r"C:\Users\andre\LitigationOS\00_SYSTEM\pipeline")
if str(_pipeline_dir) not in sys.path:
    sys.path.insert(0, str(_pipeline_dir))

try:
    from config import (
        LITIGOS_ROOT, DRIVE_SCAN_ROOTS, ALL_DRIVES, detect_drives,
        SKIP_DIRS, SKIP_EXTENSIONS, SKIP_PREFIXES,
        LEGAL_EXTENSIONS, HIGH_PRIORITY_PATTERNS,
        MCL_PATTERN, MCR_PATTERN, MRE_PATTERN, CASE_CITE_PATTERN,
        USC_PATTERN, CANON_PATTERN, VIOLATION_KEYWORDS, PERSON_NAMES,
        MEEK_SIGNALS, LANE_REGISTRY, PHASES,
        sha256_file, long_path, PipelineLogger,
    )
except ImportError as e:
    print(f"[WARN] Could not import config.py: {e}", file=sys.stderr)
    LITIGOS_ROOT = Path(r"C:\Users\andre\LitigationOS")

# ── AUTONOMOS Paths ─────────────────────────────────────────────────
AUTONOMOS_ROOT = LITIGOS_ROOT / "00_SYSTEM" / "autonomos"
SENTINEL_DIR = AUTONOMOS_ROOT / "sentinel"
INQUISITOR_DIR = AUTONOMOS_ROOT / "inquisitor"
SHARED_DIR = AUTONOMOS_ROOT / "shared"
INBOX_DIR = AUTONOMOS_ROOT / ".inbox"
OUTBOX_DIR = AUTONOMOS_ROOT / ".outbox"

# ── Database Paths ──────────────────────────────────────────────────
CENTRAL_DB = LITIGOS_ROOT / "litigation_context.db"
SENTINEL_OPS_DB = SENTINEL_DIR / "sentinel_ops.db"
SENTINEL_QUEUE_DB = SENTINEL_DIR / "sentinel_queue.db"
INQUISITOR_QUEUE_DB = INQUISITOR_DIR / "inquisitor_queue.db"
INQUISITOR_RESULTS_DB = INQUISITOR_DIR / "inquisitor_results.db"
EVENT_BRIDGE_DB = AUTONOMOS_ROOT / "event_bridge.db"
PROVENANCE_DB = AUTONOMOS_ROOT / "provenance.db"

# ── LitigationOS Directory Standard ────────────────────────────────
DIRECTORY_STANDARD = {
    "00_SYSTEM":    "System code, pipeline, agents, tools, config",
    "01_EXTRACTS":  "Raw extracted text, OCR output, parsed content",
    "02_AUTHORITY":  "Legal authority: MCL, MCR, MRE, case law, benchbooks",
    "03_EVIDENCE":   "Evidence files: scans, photos, documents, recordings",
    "04_COURT_FILINGS": "Court filings: drafts → review → final → filed → served",
    "05_ANALYSIS":   "Analysis outputs: briefs, timelines, matrices, reports",
    "06_FILINGS":    "OMEGA-generated filing stacks (court-ready)",
    "07_SPECS":      "Strategy specs, filing specs, legal specs",
    "08_APPS":       "Desktop, web, mobile applications",
    "09_DOCS":       "Documentation, READMEs, architecture docs",
    "10_Exhibits":   "Formatted exhibits with Bates stamps",
    "_SORT_LOGS":    "Low-confidence files pending manual review",
    "_UNSORTED":     "Items pending automatic classification",
}

# Directory paths (resolved)
DIR_SYSTEM = LITIGOS_ROOT / "00_SYSTEM"
DIR_EXTRACTS = LITIGOS_ROOT / "01_EXTRACTS"
DIR_AUTHORITY = LITIGOS_ROOT / "02_AUTHORITY"
DIR_EVIDENCE = LITIGOS_ROOT / "03_EVIDENCE"
DIR_FILINGS = LITIGOS_ROOT / "04_COURT_FILINGS"
DIR_ANALYSIS = LITIGOS_ROOT / "05_ANALYSIS"
DIR_OMEGA_FILINGS = LITIGOS_ROOT / "06_FILINGS"
DIR_SPECS = LITIGOS_ROOT / "07_SPECS"
DIR_APPS = LITIGOS_ROOT / "08_APPS"
DIR_DOCS = LITIGOS_ROOT / "09_DOCS"
DIR_EXHIBITS = LITIGOS_ROOT / "10_Exhibits"
DIR_SORT_LOGS = LITIGOS_ROOT / "_SORT_LOGS"
DIR_UNSORTED = LITIGOS_ROOT / "_UNSORTED"
DIR_MY_DOCS_FILINGS = Path(r"C:\Users\andre\Documents\LitigationOS_Filings")

# ── File Exclusion Patterns ─────────────────────────────────────────
SENTINEL_SKIP_NAMES = {
    "desktop.ini", "thumbs.db", "Thumbs.db", ".DS_Store",
    "ntuser.dat", "ntuser.ini", "NTUSER.DAT",
    "pagefile.sys", "swapfile.sys", "hiberfil.sys",
}

SENTINEL_SKIP_EXTENSIONS = SKIP_EXTENSIONS | {
    ".tmp", ".partial", ".crdownload", ".part",
    ".lock", ".lck", ".~lock",
    ".bak~", ".swp", ".swo",
}

SENTINEL_SKIP_PREFIXES = ("~$", "~WRL", "._", ".~lock.")

# System directories to never monitor
SENTINEL_SKIP_DIRS = SKIP_DIRS | {
    "Windows", "Program Files", "Program Files (x86)",
    "ProgramData", "$Recycle.Bin", "System Volume Information",
    "Recovery", "PerfLogs", "Config.Msi",
    ".git", ".svn", ".hg", "node_modules",
    "__pycache__", ".venv", "venv",
}

# ── Lane Priority Order (for queue ordering) ────────────────────────
LANE_PRIORITY = {
    "A": 1,   # Custody — highest priority
    "D": 2,   # PPO
    "E": 3,   # Judicial misconduct
    "F": 4,   # Appellate
    "C": 5,   # Convergence
    "B": 6,   # Housing
}

# ── Processing Limits ───────────────────────────────────────────────
DEBOUNCE_SECONDS = 0.5
MAX_FILE_SIZE_MB = 500
MAX_QUEUE_DEPTH = 1000
PROCESSING_RATE_LIMIT = 10  # files per minute
ROLLBACK_DAYS = 30
CHECKPOINT_INTERVAL = 100  # checkpoint every N items

# ── Event Types ─────────────────────────────────────────────────────
EVENT_FILE_DETECTED = "FILE_DETECTED"
EVENT_FILE_CLASSIFIED = "FILE_CLASSIFIED"
EVENT_FILE_ORGANIZED = "FILE_ORGANIZED"
EVENT_FILE_ANALYZED = "FILE_ANALYZED"
EVENT_FILING_UPDATED = "FILING_UPDATED"
EVENT_FILING_PUSHED = "FILING_PUSHED"
EVENT_DRIVE_DISCONNECTED = "DRIVE_DISCONNECTED"
EVENT_DRIVE_RECONNECTED = "DRIVE_RECONNECTED"
EVENT_ERROR = "ERROR"

# ── Document Type Classification ────────────────────────────────────
DOCUMENT_TYPES = {
    "motion":        {"keywords": ["motion", "movant", "moves the court"], "extensions": {".pdf", ".docx"}},
    "order":         {"keywords": ["order", "it is ordered", "so ordered"], "extensions": {".pdf", ".docx"}},
    "affidavit":     {"keywords": ["affidavit", "sworn", "under oath", "notarized"], "extensions": {".pdf", ".docx"}},
    "brief":         {"keywords": ["brief", "argument", "issue presented"], "extensions": {".pdf", ".docx"}},
    "exhibit":       {"keywords": ["exhibit", "bates", "attachment"], "extensions": {".pdf", ".jpg", ".png", ".tif"}},
    "transcript":    {"keywords": ["transcript", "court reporter", "proceedings"], "extensions": {".pdf", ".txt"}},
    "correspondence":{"keywords": ["dear", "sincerely", "re:"], "extensions": {".pdf", ".docx", ".txt"}},
    "financial":     {"keywords": ["income", "expense", "asset", "debt", "bank"], "extensions": {".pdf", ".csv", ".xlsx"}},
    "photo":         {"keywords": [], "extensions": {".jpg", ".jpeg", ".png", ".tif", ".tiff", ".bmp", ".heic"}},
    "form":          {"keywords": ["scao", "foc", "mc ", "pcm"], "extensions": {".pdf"}},
    "code":          {"keywords": [], "extensions": {".py", ".js", ".ts", ".jsx", ".tsx", ".sql"}},
    "data":          {"keywords": [], "extensions": {".json", ".jsonl", ".csv", ".xml", ".db", ".sqlite"}},
}

# ── Lane → Filing Stack Mapping ─────────────────────────────────────
LANE_FILING_MAP = {
    "A": ["custody_modification", "contempt_enforcement", "emergency_pt"],
    "B": ["housing_complaint", "habitability_action"],
    "D": ["ppo_modification", "ppo_contempt"],
    "E": ["jtc_complaint", "disqualification_motion", "msc_superintending"],
    "F": ["coa_brief_366810", "msc_emergency_app", "msc_habeas", "msc_mandamus"],
}
