"""
OMEGA DEEP TRAVERSAL — Shared Configuration
All pipeline phases import from here for consistency.

FAILSAFE: All blocking operations are wrapped with timeouts.
          Import of this module NEVER hangs, NEVER crashes.
"""
import os
import re
from pathlib import Path
from datetime import datetime

# ── Failsafe (must be first — protects everything below) ────────────
try:
    from failsafe import safe_call, timeout, never_crash, _log_incident
except ImportError:
    # Minimal inline fallback if failsafe.py itself is missing
    def safe_call(fn, *a, timeout_s=30, fallback=None, **kw):
        try:
            return fn(*a, **kw)
        except Exception:
            return fallback
    def timeout(s, fallback=None):
        def d(f): return f
        return d
    def never_crash(fallback=None):
        def d(f): return f
        return d
    def _log_incident(*a, **kw): pass

# ── Root Paths ──────────────────────────────────────────────────────
LITIGOS_ROOT = Path(r"C:\Users\andre\LitigationOS")
SCANS_ROOT = LITIGOS_ROOT / "02_EVIDENCE"
MASTER_ROOT = LITIGOS_ROOT

# ── Universal Drive Detection (LAZY — never blocks import) ────────────
# Only probes KNOWN drives when first accessed.  A-Z scan is gone.
import shutil as _shutil

_KNOWN_DRIVE_LETTERS = ("C", "D", "F", "G", "H", "I")  # add letters here if needed
_ALL_DRIVES_CACHE: dict | None = None  # populated on first access


@never_crash(fallback={})
@timeout(10, fallback={})
def detect_drives(*, _timeout_letters: tuple[str, ...] | None = None) -> dict:
    """Detect available drives with usage stats. Failsafe-protected: 10s max."""
    global _ALL_DRIVES_CACHE
    if _ALL_DRIVES_CACHE is not None:
        return _ALL_DRIVES_CACHE
    letters = _timeout_letters or _KNOWN_DRIVE_LETTERS
    drives: dict = {}
    for letter in letters:
        root = f"{letter}:\\"
        try:
            if os.path.exists(root):
                usage = _shutil.disk_usage(root)
                drives[letter] = {
                    "root": Path(root),
                    "total_gb": round(usage.total / 1e9, 1),
                    "used_gb": round(usage.used / 1e9, 1),
                    "free_gb": round(usage.free / 1e9, 1),
                }
        except OSError:
            pass
    _ALL_DRIVES_CACHE = drives
    return drives


class _LazyDrives:
    """Proxy that defers detect_drives() until someone actually reads the dict."""
    def __getattr__(self, name):
        return getattr(detect_drives(), name)
    def __getitem__(self, key):
        return detect_drives()[key]
    def __contains__(self, key):
        return key in detect_drives()
    def __iter__(self):
        return iter(detect_drives())
    def __len__(self):
        return len(detect_drives())
    def __repr__(self):
        return repr(detect_drives())
    def __bool__(self):
        return bool(detect_drives())


ALL_DRIVES = _LazyDrives()  # zero cost at import — probes drives only on first use

# Known scan roots per drive — everything gets indexed
DRIVE_SCAN_ROOTS = {
    "C": [
        Path(r"C:\Users\andre\LitigationOS"),
        Path(r"C:\Users\andre\LITIGATIONOS_MASTER"),
        Path(r"C:\Users\andre\scans"),
    ],
    "D": [Path(r"D:\\")],
    "F": [Path(r"F:\\")],
    "G": [Path(r"G:\\")],
    "H": [Path(r"H:\\")],
    "I": [Path(r"I:\\")],
}

# Legacy compat
EXTRA_SCAN_DIRS = [
    Path(r"C:\Users\andre\scans\discovery"),
    Path(r"C:\Users\andre\scans\Documents"),
    Path(r"C:\Users\andre\scans\New folder"),
]
TOOLING_DIR = LITIGOS_ROOT / "00_SYSTEM" / "pipeline"
BACKUPS_DIR = LITIGOS_ROOT / "00_SYSTEM" / "backups"
LEXOS_BIBLE = LITIGOS_ROOT / "00_SYSTEM" / "lexos_bible"

# ── AI Model Configuration ──────────────────────────────────────────
# PERMANENT LOCAL-ONLY LOCK: All remote providers permanently disabled.
# No Ollama, no Gemini, no OpenAI, no Groq, no OpenRouter. Zero network.
# LocalAI (pure Python TF-IDF + pattern engine) handles ALL intelligence.
AI_PROVIDER = "local"  # HARDCODED — ignores env var. LOCAL ONLY.
OLLAMA_URL = ""  # DISABLED
OLLAMA_MODEL = ""  # DISABLED
# Task-specific model routing — use ONLY verified local models
# mistral:latest = 4.4GB truly local, ~28s/call, 100% reliable
# Cloud proxy models (qwen3-coder:480b-cloud, gpt-oss:120b-cloud) are UNRELIABLE
AI_MODEL_ROUTES = {
    "classify":  "mistral:latest",
    "summarize": "mistral:latest",
    "analyze":   "mistral:latest",
    "legal":     "mistral:latest",
    "code":      "mistral:latest",
    "general":   "mistral:latest",
    "extract":   "mistral:latest",
}

# Cycle ID (set once per pipeline run)
CYCLE_TS = datetime.now().strftime("%Y%m%d_%H%M%S")
CYCLEPACK_DIR = LITIGOS_ROOT / "00_SYSTEM" / "cyclepacks" / f"CYCLE_{CYCLE_TS}"


def get_cyclepack_dir(cycle_ts: str | None = None) -> Path:
    ts = cycle_ts or CYCLE_TS
    return LITIGOS_ROOT / "00_SYSTEM" / "cyclepacks" / f"CYCLE_{ts}"


# ── Skip Lists ──────────────────────────────────────────────────────
SKIP_DIRS = {
    "__pycache__", ".git", "node_modules", ".venv", "venv",
    "tesseract-main", "czkawka-master", "java-1.8.0-openjdk",
    ".mypy_cache", ".pytest_cache", "target", ".gradle",
    "AppData", "ProgramData",
}

SKIP_EXTENSIONS = {
    ".pyc", ".pyo", ".class", ".dll", ".exe", ".so", ".o", ".obj",
    ".qml", ".typed", ".lombok", ".jar", ".war", ".ear",
    ".whl", ".egg-info", ".node", ".map",
}

SKIP_PREFIXES = (
    "java-1.8.0-openjdk", "tesseract-main", "czkawka-master",
)

# ── File Classification ─────────────────────────────────────────────
LEGAL_EXTENSIONS = {
    ".pdf", ".docx", ".doc", ".rtf", ".odt",
    ".txt", ".md",
    ".json", ".jsonl", ".csv",
    ".graphml", ".cypher",
    ".html", ".htm",
}

HIGH_PRIORITY_PATTERNS = [
    re.compile(r"(?i)(complaint|motion|brief|affidavit|order|subpoena)"),
    re.compile(r"(?i)(court_order|CORE_PDF|SCANNED_EVIDENCE|FINAL_FILING)"),
    re.compile(r"(?i)(SCAO|FOC|MEEK|evidence|exhibit)"),
]

# ── Content Signal Patterns (from brain_builder.py) ─────────────────
MCL_PATTERN = re.compile(r"MCL\s+\d+[\.\d]*")
MCR_PATTERN = re.compile(r"MCR\s+\d+[\.\d]*")
MRE_PATTERN = re.compile(r"MRE\s+\d+[\.\d]*")
CASE_CITE_PATTERN = re.compile(r"\b\d+\s+(Mich|NW2d|NW\.2d|US|F\.\d+d|F\.Supp)\b")
USC_PATTERN = re.compile(r"\b\d+\s+USC\s+§?\s*\d+")
CANON_PATTERN = re.compile(r"(?i)canon\s+\d+")

VIOLATION_KEYWORDS = [
    "contempt", "ex parte", "bias", "fraud", "perjury", "alienation",
    "misconduct", "deprivation", "due process", "fabricat",
    "obstruction", "coercion", "retaliation", "suppress",
]

PERSON_NAMES = {
    "Pigors": "PLAINTIFF",
    "Watson": "DEFENDANT",
    "Emily": "DEFENDANT",
    "McNeill": "JUDGE",
    "Hoopes": "JUDGE",
    "Rusco": "FOC/ATTORNEY",
    "David Rusco": "ATTORNEY",
    "Pamela Rusco": "FOC",
    "HealthWest": "ENTITY",
    "Albert Watson": "ADVERSARY",
    "Lori Watson": "ADVERSARY",
    "Cody Watson": "ADVERSARY",
    "Shady Oaks": "CORPORATE_DEFENDANT",
    "Homes of America": "CORPORATE_DEFENDANT",
    "Alden Global": "CORPORATE_DEFENDANT",
}

# ── MEEK Lane Assignment ────────────────────────────────────────────
MEEK_SIGNALS = {
    "MEEK1": re.compile(r"(?i)(shady.?oaks|homes.?of.?america|alden.?global|habitability|landlord|tenant|MCL\s+554|rent|mobile.?home|park)"),
    "MEEK2": re.compile(r"(?i)(custody|parenting|FOC|child|MCL\s+722|MCR\s+3\.20[67]|MCR\s+3\.210|best.?interest|factor\s+[a-l])"),
    "MEEK3": re.compile(r"(?i)(PPO|protection.?order|contempt|MCL\s+600\.2950|MCR\s+3\.70[678]|bond|restrain)"),
    "MEEK4": re.compile(r"(?i)(bias|JTC|disqualif|MCR\s+2\.003|canon|judicial.?misconduct|superintend)"),
    "MEEK5": re.compile(r"(?i)(appell|COA|MSC|MCR\s+7\.|leave.?to.?appeal|standard.?of.?review|de.?novo|abuse.?of.?discretion)"),
}

LANE_D_KEYWORDS = [
    re.compile(r"(?i)(PPO|protection.?order|personal.?protection)"),
    re.compile(r"(?i)(contempt|bond|restrain|stalking|harassment.?order)"),
    re.compile(r"(?i)(MCL\s+600\.2950|MCR\s+3\.70[678])"),
    re.compile(r"(?i)(violat.*order|enforce.*order|modify.*PPO)"),
]

LANE_E_KEYWORDS = [
    re.compile(r"(?i)(bias|prejudice|impartial|recus|disqualif)"),
    re.compile(r"(?i)(JTC|judicial.?tenure|judicial.?misconduct)"),
    re.compile(r"(?i)(MCR\s+2\.003|canon\s+\d+|code.?of.?conduct)"),
    re.compile(r"(?i)(ex.?parte|improper.?communication|unilateral)"),
    re.compile(r"(?i)(McNeill.*bias|McNeill.*misconduct|McNeill.*violat)"),
]

LANE_F_KEYWORDS = [
    re.compile(r"(?i)(appell|leave.?to.?appeal|interlocutory)"),
    re.compile(r"(?i)(COA|court.?of.?appeals|MSC|supreme.?court)"),
    re.compile(r"(?i)(MCR\s+7\.\d+|standard.?of.?review)"),
    re.compile(r"(?i)(de.?novo|abuse.?of.?discretion|clearly.?erroneous)"),
    re.compile(r"(?i)(peremptory|superintending.?control|original.?action)"),
]

# ── Case Lane Mapping ───────────────────────────────────────────────
LANE_A_CASES = {"2024-001507-DC", "2023-5907-PP"}
LANE_B_CASES = {"2025-002760-CZ"}
LANE_C_CASES = set()  # Convergence — cross-lane issues
LANE_D_CASES = {"2024-001507-DC", "2023-5907-PP"}  # PPO cases overlap with Lane A
LANE_E_CASES = {"2024-001507-DC"}  # Judicial misconduct — McNeill
LANE_F_CASES = set()  # Appellate — COA/MSC (case numbers assigned on filing)

LANE_REGISTRY = {
    "A": {"name": "Watson Custody", "meek": "MEEK2", "db": "lane_A_custody.db"},
    "B": {"name": "Shady Oaks Housing", "meek": "MEEK1", "db": "lane_B_housing.db"},
    "C": {"name": "Convergence", "meek": None, "db": "lane_C_convergence.db"},
    "D": {"name": "PPO / Protection Orders", "meek": "MEEK3", "db": "lane_D_ppo.db"},
    "E": {"name": "Judicial Misconduct / JTC", "meek": "MEEK4", "db": "lane_E_misconduct.db"},
    "F": {"name": "Appellate", "meek": "MEEK5", "db": "lane_F_appellate.db"},
}

# ── Bucket Priority (for dedup canonical election) ──────────────────
BUCKET_PRIORITY = {
    "LITIGATIONOS_MASTER": 10,
    "PIGORS_CASE_MASTER": 9,
    "SCANNED_EVIDENCE": 8,
    "extracts_full": 7,
    "COURT_FILINGS_FINAL": 7,
    "COURT_PACKETS": 6,
    "discovery": 5,
    "Documents": 4,
}

# ── Evidence Posture Tags ───────────────────────────────────────────
POSTURE_TAGS = ["RECORD_FACT", "EVIDENCE_FACT", "SWORN_FACT", "ALLEGATION", "INFERENCE"]

# ── Atom ID Generation ──────────────────────────────────────────────
import hashlib

def make_atom_id(prefix: str, brain_id: str, type_str: str, key_fields: str) -> str:
    raw = f"{brain_id}|{type_str}|{key_fields}"
    return f"{prefix}-{hashlib.sha1(raw.encode()).hexdigest()[:16]}"


def sha256_file(path: Path | str, chunk_size: int = 65536) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        while True:
            chunk = f.read(chunk_size)
            if not chunk:
                break
            h.update(chunk)
    return h.hexdigest()


# ── Master Files That Phases Will Modify ─────────────────────────────
MASTER_MODIFIABLE = [
    "SYNTHESIS_DATA.json",
    "SYNTHESIS_STATS.md",
    "MASTER_EVIDENCE_INDEX.csv",
    "MASTER_VIOLATIONS.csv",
    "MASTER_PERSONS.csv",
    "MASTER_TIMELINE.csv",
    "MASTER_CITATIONS.csv",
    "authority_shards_all.jsonl",
    "EC_AUTHORITY_MAP (1) (1).jsonl",
    "KNOWLEDGE_ALL.jsonl",
    "neo4j_nodes.csv",
    "neo4j_edges.csv",
    "EVENT_HORIZON_DELTA_INTEGRATION_MAP.md",
    "graph_contract.yml",
]

# ── Pipeline Phase Registry ──────────────────────────────────────────
PHASES = [
    ("0", "safety", "Safety Snapshot"),
    ("1", "phase1_inventory", "Recursive Inventory"),
    ("2", "phase2_dedup", "Hash-Cluster Dedup"),
    ("3", "phase3_classify", "3-Pass Classification"),
    ("4a", "phase4a_pdf_extract", "PDF Extraction"),
    ("4b", "phase4b_docx_extract", "DOCX Extraction"),
    ("4c", "phase4c_structured_extract", "Structured Data"),
    ("4d", "phase4d_atomize", "Atom Generation"),
    ("4e", "phase4e_archive_extract", "Archive Extraction"),
    ("5", "phase5_brain_feed", "LEXOS Brain Feed"),
    ("6", "phase6_gap_analysis", "EGCP Gap Analysis"),
    ("7a", "phase7a_graph_delta", "Graph Delta"),
    ("7b", "phase7b_synthesis_merge", "Synthesis Merge"),
    ("7c", "phase7c_knowledge_merge", "Knowledge Merge"),
    ("8", "phase8_litigation_refresh", "Litigation Refresh"),
    ("9", "phase9_mcp_ingest", "MCP Ingest"),
    ("10", "phase10_judicial_analysis", "Judicial Analysis"),
    ("11", "phase11_legal_action_discovery", "Legal Action Discovery"),
    ("12", "phase12_rule_audit", "MCR/MCL Rule Audit"),
    ("13", "phase13_refinement", "Document Refinement"),
    ("14", "phase14_finalize", "Filing Finalization"),
    ("15", "phase15_validation", "Court-Ready Validation"),
    ("16", "phase16_desktop", "Desktop Offload"),
]

# ── Windows Long Path Support ────────────────────────────────────────
def long_path(p: str | Path) -> str:
    s = str(p)
    if not s.startswith("\\\\?\\"):
        return f"\\\\?\\{s}"
    return s


# ── Progress Reporting ───────────────────────────────────────────────
import json
import sys

def report_progress(phase: str, current: int, total: int, extra: dict | None = None):
    msg = {"phase": phase, "current": current, "total": total}
    if extra:
        msg.update(extra)
    if current % 10000 == 0 or current == total:
        print(f"[{phase}] {current:,}/{total:,} ({100*current/max(total,1):.1f}%)", file=sys.stderr)


# ── Structured Pipeline Logger ───────────────────────────────────────

class PipelineLogger:
    """Dual-output logger: stderr (human-readable) + JSONL file (machine-readable)."""

    def __init__(self, phase: str, cycle_dir: Path | None = None):
        self._phase = phase
        self._cycle_dir = cycle_dir
        self._jsonl_path: Path | None = None
        if cycle_dir is not None:
            cycle_dir.mkdir(parents=True, exist_ok=True)
            self._jsonl_path = cycle_dir / "pipeline.log.jsonl"

    def _emit(self, level: str, message: str, extra: dict | None = None):
        ts = datetime.now().isoformat()
        # Human-readable to stderr
        print(f"[{self._phase}] {level}: {message}", file=sys.stderr)
        # Machine-readable JSONL
        if self._jsonl_path is not None:
            entry = {"timestamp": ts, "phase": self._phase, "level": level, "message": message}
            if extra:
                entry["extra"] = extra
            with open(self._jsonl_path, "a", encoding="utf-8") as f:
                f.write(json.dumps(entry) + "\n")

    def info(self, msg: str):
        self._emit("INFO", msg)

    def warn(self, msg: str):
        self._emit("WARN", msg)

    def error(self, msg: str):
        self._emit("ERROR", msg)

    def progress(self, current: int, total: int, extra: dict | None = None):
        pct = 100 * current / max(total, 1)
        self._emit("PROGRESS", f"{current:,}/{total:,} ({pct:.1f}%)", extra=extra)
