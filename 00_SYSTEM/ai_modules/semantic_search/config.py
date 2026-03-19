"""Semantic search configuration constants.

All paths, PRAGMAs, and tuning knobs for the evidence neural search module.
Zero network calls — everything runs locally.
"""
from __future__ import annotations

import os
from pathlib import Path

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------
_MODULE_DIR = Path(__file__).resolve().parent
_REPO_ROOT = _MODULE_DIR.parents[2]  # 00_SYSTEM -> LitigationOS

DB_PATH: str = os.environ.get(
    "LITIGATIONOS_DB",
    str(_REPO_ROOT / "litigation_context.db"),
)

INDEX_DIR: Path = _MODULE_DIR / "index_store"
INDEX_DIR.mkdir(exist_ok=True)

FAISS_INDEX_PATH: str = str(INDEX_DIR / "evidence.faiss")
METADATA_PATH: str = str(INDEX_DIR / "evidence_meta.pkl")
TFIDF_PATH: str = str(INDEX_DIR / "tfidf_vectorizer.joblib")
EMBEDDER_STATE_PATH: str = str(INDEX_DIR / "embedder_state.joblib")

# ---------------------------------------------------------------------------
# Chunking
# ---------------------------------------------------------------------------
CHUNK_SIZE: int = 512          # tokens (whitespace-split words)
CHUNK_OVERLAP: int = 128       # tokens overlap between consecutive chunks

# ---------------------------------------------------------------------------
# Embedding
# ---------------------------------------------------------------------------
MODEL_NAME: str = "all-MiniLM-L6-v2"   # sentence-transformers model (optional)
EMBEDDING_DIM_ST: int = 384             # dimension for sentence-transformers
# TF-IDF dimension is determined dynamically by the fitted vocabulary

# ---------------------------------------------------------------------------
# Search
# ---------------------------------------------------------------------------
TOP_K_DEFAULT: int = 10
SIMILARITY_THRESHOLD: float = 0.3

# ---------------------------------------------------------------------------
# Ingestion
# ---------------------------------------------------------------------------
SUPPORTED_EXTENSIONS: frozenset[str] = frozenset({
    ".pdf", ".docx", ".doc", ".txt", ".md",
    ".rtf", ".odt", ".html", ".htm", ".csv",
})

INGEST_BATCH_SIZE: int = 500   # rows to read from DB per batch

# ---------------------------------------------------------------------------
# SQLite PRAGMAs — applied to EVERY connection
# ---------------------------------------------------------------------------
DB_PRAGMAS: list[str] = [
    "PRAGMA busy_timeout = 60000;",
    "PRAGMA journal_mode = WAL;",
    "PRAGMA cache_size = -32000;",
    "PRAGMA temp_store = MEMORY;",
    "PRAGMA synchronous = NORMAL;",
]

# ---------------------------------------------------------------------------
# Case Lanes (for filtering)
# ---------------------------------------------------------------------------
VALID_LANES: frozenset[str] = frozenset({"A", "B", "C", "D", "E", "F"})
