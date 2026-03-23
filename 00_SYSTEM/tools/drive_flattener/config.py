"""OMEGA-FLATTEN configuration — 30-folder taxonomy, MEEK patterns, DB schema, settings.

LitigationOS Event Horizon Δ∞
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, FrozenSet, List, Set, Tuple


# ---------------------------------------------------------------------------
# Folder taxonomy
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class FolderSpec:
    """Immutable specification for one taxonomy folder."""

    name: str
    description: str
    extensions: FrozenSet[str]  # lower-cased, with leading dot
    priority: int  # lower = higher priority when extensions overlap
    is_system: bool = False
    content_detected: bool = False


# The 30-folder taxonomy — exactly 30, no more.
TAXONOMY: Dict[str, FolderSpec] = {
    "_INDEX": FolderSpec(
        name="_INDEX",
        description="Master index, manifests, analysis reports, flatten.db",
        extensions=frozenset(),
        priority=0,
        is_system=True,
    ),
    "_DEDUP": FolderSpec(
        name="_DEDUP",
        description="Duplicate files moved here",
        extensions=frozenset(),
        priority=0,
        is_system=True,
    ),
    "_UNKNOWN": FolderSpec(
        name="_UNKNOWN",
        description="Unclassified files",
        extensions=frozenset(),
        priority=999,
    ),
    "PDF": FolderSpec(
        name="PDF",
        description="PDF documents",
        extensions=frozenset({".pdf"}),
        priority=10,
    ),
    "DOCX": FolderSpec(
        name="DOCX",
        description="Word documents",
        extensions=frozenset({".docx", ".doc", ".rtf", ".odt", ".wps"}),
        priority=15,
    ),
    "MD": FolderSpec(
        name="MD",
        description="Markdown files",
        extensions=frozenset({".md", ".markdown", ".mdx", ".rst"}),
        priority=20,
    ),
    "TXT": FolderSpec(
        name="TXT",
        description="Plain text",
        extensions=frozenset({".txt", ".text", ".asc", ".nfo"}),
        priority=25,
    ),
    "HTML": FolderSpec(
        name="HTML",
        description="Web files",
        extensions=frozenset({".html", ".htm", ".css", ".mhtml", ".mht", ".xhtml"}),
        priority=30,
    ),
    "JSON": FolderSpec(
        name="JSON",
        description="JSON data",
        extensions=frozenset({".json", ".jsonl", ".geojson", ".ndjson", ".har"}),
        priority=35,
    ),
    "CSV": FolderSpec(
        name="CSV",
        description="Tabular data",
        extensions=frozenset({".csv", ".tsv", ".xlsx", ".xls", ".ods", ".numbers"}),
        priority=40,
    ),
    "XML": FolderSpec(
        name="XML",
        description="XML files",
        extensions=frozenset({
            ".xml", ".xsl", ".xslt", ".xsd", ".dtd", ".rss", ".atom", ".plist",
        }),
        priority=45,
    ),
    "IMG": FolderSpec(
        name="IMG",
        description="Images",
        extensions=frozenset({
            ".png", ".jpg", ".jpeg", ".gif", ".bmp", ".tiff", ".tif", ".webp",
            ".ico", ".heic", ".svg", ".raw", ".cr2", ".nef", ".arw", ".dng",
        }),
        priority=50,
    ),
    "VIDEO": FolderSpec(
        name="VIDEO",
        description="Video",
        extensions=frozenset({
            ".mp4", ".avi", ".mov", ".mkv", ".wmv", ".flv", ".webm", ".m4v",
            ".mpg", ".mpeg", ".3gp", ".ts", ".vob",
        }),
        priority=55,
    ),
    "AUDIO": FolderSpec(
        name="AUDIO",
        description="Audio",
        extensions=frozenset({
            ".mp3", ".wav", ".m4a", ".ogg", ".flac", ".aac", ".wma", ".opus",
            ".aiff", ".mid", ".midi",
        }),
        priority=60,
    ),
    "MEDIA": FolderSpec(
        name="MEDIA",
        description="Design media",
        extensions=frozenset({
            ".psd", ".ai", ".sketch", ".fig", ".xd", ".indd", ".eps", ".cdr",
            ".blend",
        }),
        priority=65,
    ),
    "PY": FolderSpec(
        name="PY",
        description="Python code",
        extensions=frozenset({".py", ".pyw", ".pyi", ".pyx"}),
        priority=70,
    ),
    "CODE": FolderSpec(
        name="CODE",
        description="Other code",
        extensions=frozenset({
            ".js", ".ts", ".jsx", ".tsx", ".go", ".java", ".c", ".cpp", ".h",
            ".hpp", ".cs", ".rs", ".rb", ".php", ".sh", ".ps1", ".bat", ".cmd",
            ".sql", ".r", ".scala", ".kt", ".swift", ".lua", ".pl", ".vbs", ".asm",
        }),
        priority=75,
    ),
    "DB": FolderSpec(
        name="DB",
        description="Databases",
        extensions=frozenset({".db", ".sqlite", ".sqlite3", ".mdb", ".accdb"}),
        priority=80,
    ),
    "DATA": FolderSpec(
        name="DATA",
        description="Binary data",
        extensions=frozenset({
            ".dat", ".bin", ".parquet", ".avro", ".pickle", ".pkl", ".npy",
            ".npz", ".h5", ".hdf5", ".feather", ".arrow", ".protobuf", ".bson",
            ".msgpack",
        }),
        priority=85,
    ),
    "EMAIL": FolderSpec(
        name="EMAIL",
        description="Email files",
        extensions=frozenset({".eml", ".msg", ".mbox", ".pst", ".ost", ".emlx"}),
        priority=90,
    ),
    "PPTX": FolderSpec(
        name="PPTX",
        description="Presentations",
        extensions=frozenset({".pptx", ".ppt", ".key", ".odp"}),
        priority=95,
    ),
    "CONFIG": FolderSpec(
        name="CONFIG",
        description="Config files",
        extensions=frozenset({
            ".ini", ".yaml", ".yml", ".toml", ".env", ".cfg", ".conf",
            ".properties", ".reg", ".inf", ".editorconfig", ".gitignore",
            ".dockerignore",
        }),
        priority=100,
    ),
    "LOG": FolderSpec(
        name="LOG",
        description="Log files",
        extensions=frozenset({".log", ".logs"}),
        priority=105,
    ),
    "ARCHIVE": FolderSpec(
        name="ARCHIVE",
        description="Archives",
        extensions=frozenset({
            ".zip", ".rar", ".7z", ".tar", ".gz", ".bz2", ".xz", ".tgz",
            ".cab", ".iso", ".dmg",
        }),
        priority=110,
    ),
    "EXE": FolderSpec(
        name="EXE",
        description="Executables",
        extensions=frozenset({
            ".exe", ".msi", ".dll", ".sys", ".drv", ".ocx", ".com", ".scr",
            ".appx", ".apk", ".deb", ".rpm",
        }),
        priority=115,
    ),
    "FONT": FolderSpec(
        name="FONT",
        description="Fonts",
        extensions=frozenset({".ttf", ".otf", ".woff", ".woff2", ".eot"}),
        priority=120,
    ),
    "CERT": FolderSpec(
        name="CERT",
        description="Certificates",
        extensions=frozenset({".pem", ".crt", ".key", ".cer", ".p12", ".pfx", ".csr", ".jks"}),
        priority=125,
    ),
    "BACKUP": FolderSpec(
        name="BACKUP",
        description="Backups",
        extensions=frozenset({".bak", ".old", ".orig", ".swp", ".sav"}),
        priority=130,
    ),
    "TEMP": FolderSpec(
        name="TEMP",
        description="Temporary",
        extensions=frozenset({".tmp", ".cache", ".temp"}),
        priority=135,
    ),
    "LEGAL": FolderSpec(
        name="LEGAL",
        description="Legal documents detected by content analysis",
        extensions=frozenset(),
        priority=5,
        content_detected=True,
    ),
}

assert len(TAXONOMY) == 30, f"Taxonomy must have exactly 30 folders, got {len(TAXONOMY)}"


def _build_extension_map() -> Dict[str, str]:
    """Build reverse lookup: extension → folder name.

    When an extension appears in multiple folders, the one with the *lowest*
    priority value (= highest importance) wins.
    """
    ext_map: Dict[str, Tuple[str, int]] = {}
    for spec in TAXONOMY.values():
        for ext in spec.extensions:
            existing = ext_map.get(ext)
            if existing is None or spec.priority < existing[1]:
                ext_map[ext] = (spec.name, spec.priority)
    return {ext: name for ext, (name, _) in ext_map.items()}


EXTENSION_MAP: Dict[str, str] = _build_extension_map()

# ---------------------------------------------------------------------------
# MEEK lane patterns (litigation lane detection)
# ---------------------------------------------------------------------------

MEEK_PATTERNS: Dict[str, Dict[str, object]] = {
    "MEEK1": {
        "lane": "B",
        "label": "Shady Oaks / Housing",
        "case_numbers": ["2025-002760-CZ"],
        "keywords": [
            "shady oaks", "garland", "2160 garland", "norton shores",
            "housing", "lockout", "title", "property", "sewage", "egle",
            "habitability", "water shutoff", "utility", "mobile home",
        ],
    },
    "MEEK2": {
        "lane": "A",
        "label": "Watson Custody",
        "case_numbers": ["2024-001507-DC", "2023-5907-PP"],
        "keywords": [
            "custody", "parenting time", "parenting-time", "visitation",
            "watson", "emily watson", "l.d.w", "friend of the court",
            "foc", "pamela rusco", "child support", "best interest",
            "parental rights", "parental alienation",
        ],
    },
    "MEEK3": {
        "lane": "D",
        "label": "PPO / Protection Orders",
        "case_numbers": ["2024-001507-DC", "2023-5907-PP"],
        "keywords": [
            "personal protection order", "ppo", "stalking", "harassment",
            "restraining order", "no contact", "protection order",
            "domestic violence",
        ],
    },
    "MEEK4": {
        "lane": "E",
        "label": "Judicial Misconduct",
        "case_numbers": ["2024-001507-DC"],
        "keywords": [
            "judicial misconduct", "jtc", "judicial tenure",
            "disqualification", "mcr 2.003", "recusal", "bias",
            "mcneill", "jenny mcneill", "ex parte", "due process",
            "hostile record",
        ],
    },
    "MEEK5": {
        "lane": "F",
        "label": "Appellate",
        "case_numbers": [],
        "keywords": [
            "court of appeals", "coa", "supreme court", "msc",
            "appellate", "appeal", "leave to appeal", "application",
            "brief on appeal", "appendix", "lower court record",
        ],
    },
}

# Detection priority: E → D → F → C → A → B
MEEK_PRIORITY: List[str] = ["MEEK4", "MEEK3", "MEEK5", "MEEK2", "MEEK1"]

# ---------------------------------------------------------------------------
# Directories and files to skip during scanning
# ---------------------------------------------------------------------------

SKIP_DIRS: Set[str] = {
    "$Recycle.Bin",
    "$RECYCLE.BIN",
    "System Volume Information",
    "Windows",
    "ProgramData",
    "Program Files",
    "Program Files (x86)",
    "Recovery",
    "PerfLogs",
    "Config.Msi",
    "__pycache__",
    ".git",
    "node_modules",
    ".venv",
    "venv",
    ".tox",
    ".mypy_cache",
    ".pytest_cache",
    ".ruff_cache",
    "WindowsApps",
    "MSOCache",
}

SKIP_FILES: Set[str] = {
    "desktop.ini",
    "thumbs.db",
    "Thumbs.db",
    ".DS_Store",
    "ntuser.dat",
    "NTUSER.DAT",
    "ntuser.dat.LOG1",
    "ntuser.dat.LOG2",
    "ntuser.pol",
    "UsrClass.dat",
    "pagefile.sys",
    "swapfile.sys",
    "hiberfil.sys",
    "DumpStack.log.tmp",
}

# ---------------------------------------------------------------------------
# Known drives
# ---------------------------------------------------------------------------

KNOWN_DRIVES: Dict[str, str] = {
    "C": "System / LitigationOS",
    "D": "Data",
    "F": "Evidence Storage",
    "G": "Archive",
    "H": "External",
    "I": "Dedup / Overflow",
}

# ---------------------------------------------------------------------------
# Magic bytes for binary file type detection
# ---------------------------------------------------------------------------

MAGIC_BYTES: Dict[bytes, str] = {
    b"%PDF": "PDF",
    b"PK\x03\x04": "ARCHIVE",  # ZIP (also DOCX/XLSX/PPTX — refined later)
    b"PK\x05\x06": "ARCHIVE",
    b"Rar!\x1a\x07": "ARCHIVE",
    b"\x1f\x8b": "ARCHIVE",  # GZIP
    b"7z\xbc\xaf\x27\x1c": "ARCHIVE",
    b"SQLite format 3": "DB",
    b"\x89PNG\r\n\x1a\n": "IMG",
    b"\xff\xd8\xff": "IMG",  # JPEG
    b"GIF87a": "IMG",
    b"GIF89a": "IMG",
    b"RIFF": "MEDIA",  # could be AVI/WAV — generic media
    b"\x00\x00\x01\x00": "IMG",  # ICO
    b"MZ": "EXE",  # PE executable
    b"\x7fELF": "EXE",  # ELF executable
    b"ID3": "AUDIO",  # MP3 with ID3 tag
    b"\xff\xfb": "AUDIO",  # MP3 without ID3
    b"\xff\xf3": "AUDIO",
    b"\xff\xf2": "AUDIO",
    b"fLaC": "AUDIO",
    b"OggS": "AUDIO",
    b"\x00\x00\x00\x1cftyp": "VIDEO",  # MP4
    b"\x00\x00\x00\x20ftyp": "VIDEO",
    b"\x1aE\xdf\xa3": "VIDEO",  # MKV/WebM
}

# Maximum bytes to read for magic-byte detection
MAGIC_READ_SIZE: int = 16

# ---------------------------------------------------------------------------
# Content-analysis settings
# ---------------------------------------------------------------------------

CONTENT_PREVIEW_SIZE: int = 4096  # bytes to read for text content preview
MAX_ANALYSIS_FILE_SIZE: int = 50 * 1024 * 1024  # 50 MB — skip content analysis above this
BATCH_SIZE: int = 500  # DB batch insert size
PROGRESS_INTERVAL: int = 1000  # report progress every N files
CHECKPOINT_INTERVAL: int = 500  # checkpoint to DB every N files

# Dedup similarity threshold (0.0 – 1.0)
DEDUP_SIMILARITY_THRESHOLD: float = 0.85

# Text-based folder names eligible for content-comparison dedup
TEXT_FOLDERS: FrozenSet[str] = frozenset({
    "MD", "TXT", "JSON", "CSV", "PY", "CODE", "HTML", "XML", "CONFIG", "LOG",
    "LEGAL",
})

# ---------------------------------------------------------------------------
# SQLite schema for flatten.db
# ---------------------------------------------------------------------------

FLATTEN_DB_SCHEMA: str = """
-- OMEGA-FLATTEN schema v1.0

PRAGMA journal_mode = WAL;
PRAGMA busy_timeout = 60000;
PRAGMA cache_size = -32000;
PRAGMA temp_store = MEMORY;
PRAGMA synchronous = NORMAL;

CREATE TABLE IF NOT EXISTS flat_files (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    original_path   TEXT    NOT NULL,
    new_path        TEXT,
    drive           TEXT    NOT NULL,
    folder          TEXT    NOT NULL,
    filename        TEXT    NOT NULL,
    extension       TEXT,
    size_bytes      INTEGER NOT NULL DEFAULT 0,
    sha256          TEXT,
    content_preview TEXT,
    litigation_score REAL   DEFAULT 0.0,
    meek_lane       TEXT,
    evidence_value  TEXT    DEFAULT 'none',
    entities_json   TEXT,
    is_duplicate    INTEGER DEFAULT 0,
    duplicate_of    INTEGER,
    status          TEXT    NOT NULL DEFAULT 'discovered',
    created_at      TEXT    NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%S','now','localtime')),
    analyzed_at     TEXT,
    FOREIGN KEY (duplicate_of) REFERENCES flat_files(id)
);
CREATE INDEX IF NOT EXISTS idx_ff_drive          ON flat_files(drive);
CREATE INDEX IF NOT EXISTS idx_ff_folder         ON flat_files(folder);
CREATE INDEX IF NOT EXISTS idx_ff_status         ON flat_files(status);
CREATE INDEX IF NOT EXISTS idx_ff_sha256         ON flat_files(sha256);
CREATE INDEX IF NOT EXISTS idx_ff_litigation     ON flat_files(litigation_score DESC);
CREATE INDEX IF NOT EXISTS idx_ff_meek           ON flat_files(meek_lane);
CREATE INDEX IF NOT EXISTS idx_ff_evidence       ON flat_files(evidence_value);
CREATE INDEX IF NOT EXISTS idx_ff_dup            ON flat_files(is_duplicate);
CREATE INDEX IF NOT EXISTS idx_ff_orig_path      ON flat_files(original_path);

CREATE TABLE IF NOT EXISTS dedup_clusters (
    id                INTEGER PRIMARY KEY AUTOINCREMENT,
    cluster_hash      TEXT,
    canonical_file_id INTEGER NOT NULL,
    file_count        INTEGER NOT NULL DEFAULT 0,
    total_size_bytes  INTEGER NOT NULL DEFAULT 0,
    similarity_method TEXT    NOT NULL DEFAULT 'sha256',
    FOREIGN KEY (canonical_file_id) REFERENCES flat_files(id)
);
CREATE INDEX IF NOT EXISTS idx_dc_hash ON dedup_clusters(cluster_hash);

CREATE TABLE IF NOT EXISTS dedup_members (
    cluster_id       INTEGER NOT NULL,
    file_id          INTEGER NOT NULL,
    similarity_score REAL    NOT NULL DEFAULT 1.0,
    is_canonical     INTEGER NOT NULL DEFAULT 0,
    action           TEXT    NOT NULL DEFAULT 'keep',
    PRIMARY KEY (cluster_id, file_id),
    FOREIGN KEY (cluster_id) REFERENCES dedup_clusters(id),
    FOREIGN KEY (file_id)    REFERENCES flat_files(id)
);

CREATE TABLE IF NOT EXISTS scan_sessions (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    drive           TEXT    NOT NULL,
    started_at      TEXT    NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%S','now','localtime')),
    completed_at    TEXT,
    total_files     INTEGER DEFAULT 0,
    total_size_bytes INTEGER DEFAULT 0,
    files_moved     INTEGER DEFAULT 0,
    files_analyzed  INTEGER DEFAULT 0,
    files_deduped   INTEGER DEFAULT 0,
    status          TEXT    NOT NULL DEFAULT 'running'
);

CREATE TABLE IF NOT EXISTS file_analysis (
    file_id             INTEGER PRIMARY KEY,
    litigation_relevance REAL   DEFAULT 0.0,
    case_lanes          TEXT,
    entity_names        TEXT,
    entity_dates        TEXT,
    entity_case_numbers TEXT,
    entity_dollar_amounts TEXT,
    key_quotes          TEXT,
    document_type       TEXT,
    evidence_admissibility TEXT DEFAULT 'unknown',
    relationship_links  TEXT,
    forge_candidates    TEXT,
    FOREIGN KEY (file_id) REFERENCES flat_files(id)
);
CREATE INDEX IF NOT EXISTS idx_fa_relevance ON file_analysis(litigation_relevance DESC);

CREATE TABLE IF NOT EXISTS forge_outputs (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    output_path     TEXT    NOT NULL,
    output_type     TEXT    NOT NULL,
    source_file_ids TEXT,
    description     TEXT,
    case_lane       TEXT,
    created_at      TEXT    NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%S','now','localtime'))
);
"""
