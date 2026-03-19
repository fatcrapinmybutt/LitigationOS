"""Unified embedding model manager for LitigationOS.

Manages four local embedding models for litigation document similarity,
semantic search, legal analysis, and named entity recognition.  Every
path is CPU-first, zero-API, and fully local.

Supported models
----------------
+-----------------------------------------------+------+---------------------+
| Model directory                                | Dims | Purpose             |
+-----------------------------------------------+------+---------------------+
| sentence-transformers_all-MiniLM-L6-v2        |  384 | Semantic search     |
| nlpaueb_legal-bert-small-uncased              |  512 | Legal analysis      |
| nlpaueb_legal-bert-base-uncased               |  768 | Deep legal analysis |
| dslim_bert-base-NER                           |  768 | NER extraction      |
+-----------------------------------------------+------+---------------------+

Embedding generation priority (first available wins):
  1. ONNX Runtime (onnxruntime) – fastest CPU inference
  2. sentence-transformers (torch) – reference implementation
  3. TF-IDF hashing fallback (stdlib only) – ALWAYS works

The TF-IDF hashing fallback is the *primary* path because most
environments will not have ``onnxruntime`` or ``torch`` installed.

Usage
-----
>>> mgr = EmbeddingManager()
>>> specs = mgr.discover_models()
>>> vec = mgr.embed_text("MCL 722.23 best interest factors")
>>> batch = mgr.embed_batch(["text one", "text two"], model='legal_analysis')
"""
from __future__ import annotations

import hashlib
import json
import logging
import math
import os
import pathlib
import re
import sqlite3
import struct
import time
from dataclasses import dataclass, field, asdict
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple, Union

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------

_HERE = pathlib.Path(__file__).resolve().parent
_REPO = _HERE.parents[1]          # legal_ai → 00_SYSTEM → repo root
_DB_PATH = _REPO / "litigation_context.db"
_MODELS_DIR = _HERE.parent / "local_model" / "models"

# ---------------------------------------------------------------------------
# Optional dependency probes
# ---------------------------------------------------------------------------

_HAS_ONNX = False
_HAS_SENTENCE_TRANSFORMERS = False
_HAS_NUMPY = False

try:
    import numpy as _np          # type: ignore[import-untyped]
    _HAS_NUMPY = True
except ImportError:
    _np = None  # type: ignore[assignment]

try:
    import onnxruntime as _ort   # type: ignore[import-untyped]
    _HAS_ONNX = True
except ImportError:
    _ort = None  # type: ignore[assignment]

try:
    from sentence_transformers import SentenceTransformer as _ST  # type: ignore[import-untyped]
    _HAS_SENTENCE_TRANSFORMERS = True
except ImportError:
    _ST = None  # type: ignore[assignment]


# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

# Default SQLite PRAGMAs (LitigationOS convention)
_PRAGMAS = (
    "PRAGMA busy_timeout = 60000;",
    "PRAGMA journal_mode = WAL;",
    "PRAGMA cache_size  = -32000;",
    "PRAGMA temp_store  = MEMORY;",
    "PRAGMA synchronous = NORMAL;",
)

_MODEL_REGISTRY: Dict[str, Dict[str, Any]] = {
    "sentence-transformers_all-MiniLM-L6-v2": {
        "dimensions": 384,
        "model_type": "sentence_transformer",
        "max_seq_length": 256,
        "task_alias": "semantic_search",
    },
    "nlpaueb_legal-bert-small-uncased": {
        "dimensions": 512,
        "model_type": "legal_bert",
        "max_seq_length": 512,
        "task_alias": "legal_analysis",
    },
    "nlpaueb_legal-bert-base-uncased": {
        "dimensions": 768,
        "model_type": "legal_bert",
        "max_seq_length": 512,
        "task_alias": "deep_analysis",
    },
    "dslim_bert-base-NER": {
        "dimensions": 768,
        "model_type": "ner",
        "max_seq_length": 512,
        "task_alias": "ner",
    },
}

# Task → preferred model directory name
_TASK_MAP: Dict[str, str] = {
    "semantic_search": "sentence-transformers_all-MiniLM-L6-v2",
    "legal_analysis":  "nlpaueb_legal-bert-small-uncased",
    "deep_analysis":   "nlpaueb_legal-bert-base-uncased",
    "ner":             "dslim_bert-base-NER",
    "default":         "sentence-transformers_all-MiniLM-L6-v2",
}

# Default TF-IDF output dimensionality
_DEFAULT_TFIDF_DIM = 300

# Cache defaults
_CACHE_MAX_SIZE = 100_000
_CACHE_TTL_HOURS = 168  # 7 days


# ---------------------------------------------------------------------------
# Enums & Dataclasses
# ---------------------------------------------------------------------------

class ModelType(Enum):
    """Embedding model family."""
    SENTENCE_TRANSFORMER = "sentence_transformer"
    LEGAL_BERT = "legal_bert"
    NER = "ner"


class EmbeddingBackend(Enum):
    """Runtime backend used to generate embeddings."""
    ONNX = "onnx"
    SENTENCE_TRANSFORMERS = "sentence_transformers"
    TFIDF_HASH = "tfidf_hash"


@dataclass
class ModelSpec:
    """Specification for a single embedding model.

    Attributes
    ----------
    name : str
        Directory name of the model (e.g. ``sentence-transformers_all-MiniLM-L6-v2``).
    dimensions : int
        Output embedding dimensionality.
    model_dir : pathlib.Path
        Absolute path to the model directory on disk.
    model_type : str
        One of ``sentence_transformer``, ``legal_bert``, ``ner``.
    has_onnx : bool
        True when an ``onnx/`` sub-directory with ``.onnx`` files exists.
    has_safetensors : bool
        True when ``model.safetensors`` is present in the model directory.
    max_seq_length : int
        Maximum input token length the model supports.
    vocab_size : int
        Number of entries in the model vocabulary (from ``config.json``).
    config_raw : dict
        Full contents of the model's ``config.json`` (if found).
    """
    name: str
    dimensions: int
    model_dir: pathlib.Path
    model_type: str
    has_onnx: bool
    has_safetensors: bool
    max_seq_length: int
    vocab_size: int
    config_raw: Dict[str, Any] = field(default_factory=dict, repr=False)

    def to_dict(self) -> dict:
        """Return a JSON-serialisable dictionary representation."""
        return {
            "name": self.name,
            "dimensions": self.dimensions,
            "model_dir": str(self.model_dir),
            "model_type": self.model_type,
            "has_onnx": self.has_onnx,
            "has_safetensors": self.has_safetensors,
            "max_seq_length": self.max_seq_length,
            "vocab_size": self.vocab_size,
        }


# ---------------------------------------------------------------------------
# EmbeddingCache
# ---------------------------------------------------------------------------

class EmbeddingCache:
    """LRU cache for embeddings backed by SQLite.

    Stores ``text_hash → embedding_blob`` pairs with TTL-based expiration
    and a configurable maximum row count.  When the cache exceeds
    ``max_size``, the oldest entries are evicted.

    Parameters
    ----------
    db_path : pathlib.Path | str
        Path to the SQLite database (defaults to the repo-root
        ``litigation_context.db``).
    max_size : int
        Maximum number of cached embeddings before LRU eviction.
    ttl_hours : int
        Time-to-live for each cache entry in hours.
    """

    _TABLE = "embedding_cache"
    _CREATE_SQL = f"""
        CREATE TABLE IF NOT EXISTS {_TABLE} (
            text_hash     TEXT PRIMARY KEY,
            model_name    TEXT    NOT NULL,
            dimensions    INTEGER NOT NULL,
            embedding     BLOB    NOT NULL,
            created_at    TEXT    NOT NULL DEFAULT (datetime('now')),
            accessed_at   TEXT    NOT NULL DEFAULT (datetime('now')),
            access_count  INTEGER NOT NULL DEFAULT 1
        );
    """
    _IDX_SQL = f"""
        CREATE INDEX IF NOT EXISTS idx_{_TABLE}_accessed
            ON {_TABLE}(accessed_at);
    """

    def __init__(
        self,
        db_path: Union[pathlib.Path, str, None] = None,
        max_size: int = _CACHE_MAX_SIZE,
        ttl_hours: int = _CACHE_TTL_HOURS,
    ) -> None:
        self._db_path = pathlib.Path(db_path) if db_path else _DB_PATH
        self._max_size = max_size
        self._ttl_hours = ttl_hours
        self._hits = 0
        self._misses = 0
        self._evictions = 0
        self._ensure_table()

    # -- internal helpers ---------------------------------------------------

    def _connect(self) -> sqlite3.Connection:
        """Open a WAL-mode connection with standard PRAGMAs."""
        conn = sqlite3.connect(str(self._db_path), timeout=60)
        conn.row_factory = sqlite3.Row
        for pragma in _PRAGMAS:
            conn.execute(pragma)
        return conn

    def _ensure_table(self) -> None:
        """Create the cache table and index if they don't exist."""
        try:
            conn = self._connect()
            conn.execute(self._CREATE_SQL)
            conn.execute(self._IDX_SQL)
            conn.commit()
            conn.close()
        except Exception as exc:  # noqa: BLE001
            logger.warning("EmbeddingCache: could not ensure table: %s", exc)

    # -- public API ---------------------------------------------------------

    def get(
        self, text_hash: str, model_name: str = ""
    ) -> Optional[List[float]]:
        """Retrieve a cached embedding.

        Returns ``None`` on miss or if the entry has expired.
        """
        try:
            conn = self._connect()
            row = conn.execute(
                f"SELECT embedding, dimensions, created_at "
                f"FROM {self._TABLE} WHERE text_hash = ?",
                (text_hash,),
            ).fetchone()
            if row is None:
                self._misses += 1
                conn.close()
                return None

            # TTL check
            created = datetime.fromisoformat(row["created_at"])
            if datetime.utcnow() - created > timedelta(hours=self._ttl_hours):
                conn.execute(
                    f"DELETE FROM {self._TABLE} WHERE text_hash = ?",
                    (text_hash,),
                )
                conn.commit()
                conn.close()
                self._misses += 1
                return None

            # Decode blob → list[float]
            dims = row["dimensions"]
            blob: bytes = row["embedding"]
            vector = list(struct.unpack(f"<{dims}f", blob))

            # Update access stats
            conn.execute(
                f"UPDATE {self._TABLE} SET accessed_at = datetime('now'), "
                f"access_count = access_count + 1 WHERE text_hash = ?",
                (text_hash,),
            )
            conn.commit()
            conn.close()
            self._hits += 1
            return vector
        except Exception as exc:  # noqa: BLE001
            logger.debug("EmbeddingCache.get error: %s", exc)
            self._misses += 1
            return None

    def put(
        self,
        text_hash: str,
        embedding: List[float],
        model_name: str = "unknown",
    ) -> None:
        """Store an embedding in the cache.

        If the cache exceeds ``max_size``, the least-recently-accessed
        entries are evicted.
        """
        dims = len(embedding)
        blob = struct.pack(f"<{dims}f", *embedding)
        try:
            conn = self._connect()
            conn.execute(
                f"INSERT OR REPLACE INTO {self._TABLE} "
                f"(text_hash, model_name, dimensions, embedding, "
                f" created_at, accessed_at, access_count) "
                f"VALUES (?, ?, ?, ?, datetime('now'), datetime('now'), 1)",
                (text_hash, model_name, dims, blob),
            )
            conn.commit()
            self._enforce_max_size(conn)
            conn.close()
        except Exception as exc:  # noqa: BLE001
            logger.debug("EmbeddingCache.put error: %s", exc)

    def clear(self) -> int:
        """Delete all entries. Returns number of rows removed."""
        try:
            conn = self._connect()
            cur = conn.execute(f"DELETE FROM {self._TABLE}")
            conn.commit()
            removed = cur.rowcount
            conn.close()
            return removed
        except Exception as exc:  # noqa: BLE001
            logger.warning("EmbeddingCache.clear error: %s", exc)
            return 0

    def stats(self) -> Dict[str, Any]:
        """Return cache statistics."""
        total = 0
        models: Dict[str, int] = {}
        try:
            conn = self._connect()
            row = conn.execute(
                f"SELECT COUNT(*) AS cnt FROM {self._TABLE}"
            ).fetchone()
            total = row["cnt"] if row else 0
            for r in conn.execute(
                f"SELECT model_name, COUNT(*) AS cnt "
                f"FROM {self._TABLE} GROUP BY model_name"
            ):
                models[r["model_name"]] = r["cnt"]
            conn.close()
        except Exception:  # noqa: BLE001
            pass
        return {
            "total_entries": total,
            "max_size": self._max_size,
            "ttl_hours": self._ttl_hours,
            "hits": self._hits,
            "misses": self._misses,
            "evictions": self._evictions,
            "hit_rate": (
                round(self._hits / max(self._hits + self._misses, 1), 4)
            ),
            "models": models,
        }

    # -- eviction -----------------------------------------------------------

    def _enforce_max_size(self, conn: sqlite3.Connection) -> None:
        """Evict oldest entries when cache exceeds max_size."""
        row = conn.execute(
            f"SELECT COUNT(*) AS cnt FROM {self._TABLE}"
        ).fetchone()
        if row is None:
            return
        total = row["cnt"]
        if total <= self._max_size:
            return
        overflow = total - self._max_size
        conn.execute(
            f"DELETE FROM {self._TABLE} WHERE text_hash IN ("
            f"  SELECT text_hash FROM {self._TABLE} "
            f"  ORDER BY accessed_at ASC LIMIT ?"
            f")",
            (overflow,),
        )
        conn.commit()
        self._evictions += overflow
        logger.info(
            "EmbeddingCache: evicted %d entries (total was %d, max %d)",
            overflow, total, self._max_size,
        )


# ---------------------------------------------------------------------------
# Tokeniser helpers (stdlib only)
# ---------------------------------------------------------------------------

_WORD_RE = re.compile(r"[a-zA-Z0-9]+(?:\.[a-zA-Z0-9]+)*")

_LEGAL_STOP_WORDS = frozenset({
    "the", "of", "and", "to", "in", "a", "is", "that", "for", "it",
    "was", "on", "are", "as", "with", "his", "they", "at", "be", "this",
    "have", "from", "or", "one", "had", "by", "but", "not", "what",
    "all", "were", "we", "when", "your", "can", "said", "there", "an",
    "each", "which", "she", "do", "how", "their", "if", "will", "up",
    "other", "about", "out", "many", "then", "them", "these", "so",
    "some", "her", "would", "been", "has", "its", "who", "did", "no",
})


def _tokenize(text: str, lower: bool = True) -> List[str]:
    """Tokenise text into word tokens, removing stop-words.

    Handles legal citations (``MCL 722.23``) as single tokens and
    keeps numeric components like section numbers.
    """
    if lower:
        text = text.lower()
    tokens = _WORD_RE.findall(text)
    return [t for t in tokens if t not in _LEGAL_STOP_WORDS and len(t) > 1]


def _text_hash(text: str) -> str:
    """SHA-256 hex digest of normalised text."""
    normed = " ".join(text.lower().split())
    return hashlib.sha256(normed.encode("utf-8")).hexdigest()


# ---------------------------------------------------------------------------
# TF-IDF Hashing Embedder (ALWAYS works — stdlib only)
# ---------------------------------------------------------------------------

class _TfidfHashEmbedder:
    """Deterministic sparse embedding via the hashing trick.

    Each token is hashed with SHA-256 and mapped to a fixed number of
    dimensions.  Token frequency (TF) weights are applied, and the
    resulting vector is L2-normalised for cosine-similarity compatibility.

    This is the *primary* embedding path because most deployment
    environments will not have ``onnxruntime`` or ``torch``.

    Parameters
    ----------
    dim : int
        Output embedding dimensionality.
    subword : bool
        If ``True``, augment tokens with character 3-grams for better
        handling of unseen words (e.g. case numbers, statute refs).
    """

    def __init__(self, dim: int = _DEFAULT_TFIDF_DIM, subword: bool = True):
        self.dim = dim
        self.subword = subword
        # IDF accumulator (updated over embed calls)
        self._doc_count = 0
        self._doc_freq: Dict[str, int] = {}

    def _hash_token(self, token: str) -> Tuple[int, int]:
        """Return (dimension_index, sign) for a token.

        Uses first 8 bytes of SHA-256 for the index and the 9th byte
        for the sign (+1 / -1).  The sign trick allows cancellation of
        hash collisions in expectation.
        """
        h = hashlib.sha256(token.encode("utf-8")).digest()
        idx = int.from_bytes(h[:8], "little") % self.dim
        sign = 1 if h[8] & 1 else -1
        return idx, sign

    def _char_ngrams(self, token: str, n: int = 3) -> List[str]:
        """Generate character n-grams for a token."""
        padded = f"<{token}>"
        return [padded[i:i + n] for i in range(max(1, len(padded) - n + 1))]

    def _compute_tf(self, tokens: List[str]) -> Dict[str, float]:
        """Compute sub-linear TF weights: 1 + log(count)."""
        freq: Dict[str, int] = {}
        for t in tokens:
            freq[t] = freq.get(t, 0) + 1
        return {t: 1.0 + math.log(c) for t, c in freq.items()}

    def embed(self, text: str) -> List[float]:
        """Produce a fixed-dimensionality embedding for ``text``.

        Returns
        -------
        list[float]
            L2-normalised vector of length ``self.dim``.
        """
        tokens = _tokenize(text)
        if not tokens:
            return [0.0] * self.dim

        # Optionally expand tokens with character n-grams
        expanded = list(tokens)
        if self.subword:
            for t in tokens:
                expanded.extend(self._char_ngrams(t))

        tf = self._compute_tf(expanded)

        # Update IDF counts
        self._doc_count += 1
        seen: set = set()
        for t in expanded:
            if t not in seen:
                self._doc_freq[t] = self._doc_freq.get(t, 0) + 1
                seen.add(t)

        # Build sparse vector via hashing trick
        vec = [0.0] * self.dim
        for token, weight in tf.items():
            idx, sign = self._hash_token(token)
            # IDF component: log(N / df) with smoothing
            df = self._doc_freq.get(token, 1)
            idf = math.log(max(self._doc_count, 1) / df + 1.0)
            vec[idx] += sign * weight * idf

        # L2 normalise
        norm = math.sqrt(sum(v * v for v in vec))
        if norm > 1e-12:
            vec = [v / norm for v in vec]

        return vec

    def embed_batch(self, texts: List[str]) -> List[List[float]]:
        """Embed a list of texts."""
        return [self.embed(t) for t in texts]

    def get_stats(self) -> Dict[str, Any]:
        """Return embedder statistics."""
        return {
            "backend": "tfidf_hash",
            "dimensions": self.dim,
            "subword": self.subword,
            "doc_count": self._doc_count,
            "vocab_size": len(self._doc_freq),
        }


# ---------------------------------------------------------------------------
# Dimension Reduction (stdlib PCA fallback)
# ---------------------------------------------------------------------------

def _mean_vec(vecs: List[List[float]]) -> List[float]:
    """Column-wise mean of a list of vectors."""
    n = len(vecs)
    d = len(vecs[0])
    mean = [0.0] * d
    for v in vecs:
        for i in range(d):
            mean[i] += v[i]
    return [m / n for m in mean]


def _center(vecs: List[List[float]], mean: List[float]) -> List[List[float]]:
    """Subtract mean from each vector."""
    return [[v[i] - mean[i] for i in range(len(mean))] for v in vecs]


def _dot(a: List[float], b: List[float]) -> float:
    """Dot product of two vectors."""
    return sum(x * y for x, y in zip(a, b))


def _outer_accumulate(
    mat: List[List[float]], vec: List[float], d: int
) -> None:
    """Accumulate outer product vec @ vec^T into symmetric matrix *mat*."""
    for i in range(d):
        vi = vec[i]
        for j in range(i, d):
            val = vi * vec[j]
            mat[i][j] += val
            if i != j:
                mat[j][i] += val


def _power_iteration(
    cov: List[List[float]], d: int, n_iter: int = 100
) -> Tuple[List[float], float]:
    """Extract dominant eigenvector via power iteration."""
    # Deterministic seed vector
    vec = [1.0 / math.sqrt(d)] * d
    eigenvalue = 0.0
    for _ in range(n_iter):
        new_vec = [0.0] * d
        for i in range(d):
            s = 0.0
            row = cov[i]
            for j in range(d):
                s += row[j] * vec[j]
            new_vec[i] = s
        norm = math.sqrt(sum(x * x for x in new_vec))
        if norm < 1e-15:
            break
        vec = [x / norm for x in new_vec]
        eigenvalue = norm
    return vec, eigenvalue


def _deflate(
    cov: List[List[float]], eigvec: List[float], eigval: float, d: int
) -> None:
    """Deflate covariance matrix by removing a principal component."""
    for i in range(d):
        ei = eigvec[i]
        for j in range(i, d):
            val = eigval * ei * eigvec[j]
            cov[i][j] -= val
            if i != j:
                cov[j][i] -= val


def _reduce_pca_stdlib(
    vectors: List[List[float]], target_dim: int
) -> List[List[float]]:
    """Pure-Python PCA dimension reduction via power iteration.

    This is O(n * d^2 + k * d^2) where n = sample count, d = original
    dimensionality, k = target dimensions.  Fine for d ≤ 768 and small
    to medium n.

    Parameters
    ----------
    vectors : list of list of float
        Input vectors (all same dimensionality).
    target_dim : int
        Desired output dimensionality.

    Returns
    -------
    list of list of float
        Projected vectors with ``target_dim`` dimensions.
    """
    if not vectors:
        return []
    d = len(vectors[0])
    if target_dim >= d:
        return [list(v) for v in vectors]

    n = len(vectors)
    mean = _mean_vec(vectors)
    centered = _center(vectors, mean)

    # Build covariance matrix (d × d)
    cov: List[List[float]] = [[0.0] * d for _ in range(d)]
    for v in centered:
        _outer_accumulate(cov, v, d)
    for i in range(d):
        for j in range(d):
            cov[i][j] /= max(n - 1, 1)

    # Extract top-k eigenvectors
    components: List[List[float]] = []
    for _k in range(target_dim):
        eigvec, eigval = _power_iteration(cov, d)
        components.append(eigvec)
        _deflate(cov, eigvec, eigval, d)

    # Project
    projected: List[List[float]] = []
    for v in centered:
        proj = [_dot(v, comp) for comp in components]
        projected.append(proj)

    return projected


def _reduce_numpy(
    vectors: List[List[float]], target_dim: int
) -> List[List[float]]:
    """NumPy-accelerated PCA via SVD."""
    if _np is None:
        raise ImportError("numpy not available")
    arr = _np.array(vectors, dtype=_np.float32)
    mean = arr.mean(axis=0)
    centered = arr - mean
    _U, _S, Vt = _np.linalg.svd(centered, full_matrices=False)
    components = Vt[:target_dim]
    projected = centered @ components.T
    return projected.tolist()


# ---------------------------------------------------------------------------
# Cosine similarity helper
# ---------------------------------------------------------------------------

def cosine_similarity(a: List[float], b: List[float]) -> float:
    """Compute cosine similarity between two vectors.

    Parameters
    ----------
    a, b : list[float]
        Input vectors of equal length.

    Returns
    -------
    float
        Cosine similarity in [-1, 1].
    """
    dot_val = sum(x * y for x, y in zip(a, b))
    norm_a = math.sqrt(sum(x * x for x in a))
    norm_b = math.sqrt(sum(x * x for x in b))
    if norm_a < 1e-12 or norm_b < 1e-12:
        return 0.0
    return dot_val / (norm_a * norm_b)


# ---------------------------------------------------------------------------
# EmbeddingManager
# ---------------------------------------------------------------------------

class EmbeddingManager:
    """Unified embedding model manager for LitigationOS.

    Discovers local models, selects the best model for each task, and
    generates embeddings via the highest-performance backend available
    (ONNX → sentence-transformers → TF-IDF hashing fallback).

    Parameters
    ----------
    models_dir : Path or str or None
        Override for the model directory.  Defaults to
        ``00_SYSTEM/local_model/models/``.
    db_path : Path or str or None
        Override for the cache database.
    cache_max_size : int
        Maximum embedding cache entries.
    cache_ttl_hours : int
        Cache entry time-to-live in hours.
    default_dim : int
        Default embedding dimension for the TF-IDF fallback.
    """

    def __init__(
        self,
        models_dir: Union[pathlib.Path, str, None] = None,
        db_path: Union[pathlib.Path, str, None] = None,
        cache_max_size: int = _CACHE_MAX_SIZE,
        cache_ttl_hours: int = _CACHE_TTL_HOURS,
        default_dim: int = _DEFAULT_TFIDF_DIM,
    ) -> None:
        self._models_dir = pathlib.Path(models_dir) if models_dir else _MODELS_DIR
        self._db_path = pathlib.Path(db_path) if db_path else _DB_PATH
        self._default_dim = default_dim

        # Embedding cache
        self._cache = EmbeddingCache(
            db_path=self._db_path,
            max_size=cache_max_size,
            ttl_hours=cache_ttl_hours,
        )

        # TF-IDF fallback embedders keyed by dimension
        self._tfidf: Dict[int, _TfidfHashEmbedder] = {}

        # Lazy-loaded model handles (ONNX sessions or ST instances)
        self._loaded_models: Dict[str, Any] = {}

        # Discovered model specs
        self._specs: Dict[str, ModelSpec] = {}

        # Counters
        self._embed_count = 0
        self._fallback_count = 0
        self._backend_used: Dict[str, int] = {
            "onnx": 0,
            "sentence_transformers": 0,
            "tfidf_hash": 0,
        }

        # Auto-discover on init
        self.discover_models()
        logger.info(
            "EmbeddingManager initialised: %d models discovered, "
            "backends available: onnx=%s st=%s numpy=%s",
            len(self._specs),
            _HAS_ONNX,
            _HAS_SENTENCE_TRANSFORMERS,
            _HAS_NUMPY,
        )

    # ------------------------------------------------------------------
    # Discovery
    # ------------------------------------------------------------------

    def discover_models(self) -> List[ModelSpec]:
        """Scan model directories and return a list of ``ModelSpec`` objects.

        Reads each model's ``config.json`` to determine vocabulary size,
        hidden dimensionality, and weight format availability.

        Returns
        -------
        list[ModelSpec]
            One spec per model directory found.
        """
        self._specs.clear()
        if not self._models_dir.is_dir():
            logger.warning(
                "Models directory not found: %s", self._models_dir,
            )
            return []

        results: List[ModelSpec] = []
        for name, meta in _MODEL_REGISTRY.items():
            model_dir = self._models_dir / name
            if not model_dir.is_dir():
                logger.debug("Model dir missing: %s", model_dir)
                continue

            # Read config.json
            config_raw: Dict[str, Any] = {}
            config_path = model_dir / "config.json"
            if config_path.is_file():
                try:
                    with open(config_path, "r", encoding="utf-8") as fh:
                        config_raw = json.load(fh)
                except (json.JSONDecodeError, OSError) as exc:
                    logger.warning("Bad config.json in %s: %s", name, exc)

            # Detect weight formats
            has_onnx = (model_dir / "onnx").is_dir() and any(
                f.suffix == ".onnx" for f in (model_dir / "onnx").iterdir()
            ) if (model_dir / "onnx").is_dir() else False

            has_safetensors = (model_dir / "model.safetensors").is_file()

            vocab_size = config_raw.get(
                "vocab_size", config_raw.get("_vocab_size", 0)
            )

            # The hidden_size in config.json is the real dimension
            dims = config_raw.get(
                "hidden_size", meta["dimensions"]
            )

            spec = ModelSpec(
                name=name,
                dimensions=dims,
                model_dir=model_dir,
                model_type=meta["model_type"],
                has_onnx=has_onnx,
                has_safetensors=has_safetensors,
                max_seq_length=meta["max_seq_length"],
                vocab_size=vocab_size,
                config_raw=config_raw,
            )
            self._specs[name] = spec
            results.append(spec)
            logger.debug(
                "Discovered model %s: %dd, onnx=%s, safetensors=%s",
                name, dims, has_onnx, has_safetensors,
            )

        logger.info("Model discovery complete: %d models found", len(results))
        return results

    # ------------------------------------------------------------------
    # Model selection
    # ------------------------------------------------------------------

    def select_model(self, task: str = "default") -> ModelSpec:
        """Select the best model for a given task.

        Parameters
        ----------
        task : str
            One of ``semantic_search``, ``legal_analysis``,
            ``deep_analysis``, ``ner``, or ``default``.

        Returns
        -------
        ModelSpec
            Specification for the selected model.

        Raises
        ------
        ValueError
            If no suitable model is found for the requested task.
        """
        model_name = _TASK_MAP.get(task, _TASK_MAP["default"])
        if model_name in self._specs:
            return self._specs[model_name]

        # Fallback: return first available model
        if self._specs:
            first = next(iter(self._specs.values()))
            logger.warning(
                "Preferred model %s not available for task '%s'; "
                "falling back to %s",
                model_name, task, first.name,
            )
            return first

        raise ValueError(
            f"No models available for task '{task}'. "
            f"Run discover_models() or check {self._models_dir}"
        )

    def list_models(self) -> List[ModelSpec]:
        """Return all discovered model specs."""
        return list(self._specs.values())

    # ------------------------------------------------------------------
    # Embedding generation
    # ------------------------------------------------------------------

    def embed_text(
        self,
        text: str,
        model: str = "default",
        use_cache: bool = True,
    ) -> List[float]:
        """Generate an embedding for a single text string.

        Tries backends in priority order:
        1. ONNX Runtime
        2. sentence-transformers
        3. TF-IDF hashing fallback (always available)

        Parameters
        ----------
        text : str
            Input text to embed.
        model : str
            Task name or model directory name.
        use_cache : bool
            Whether to check / populate the embedding cache.

        Returns
        -------
        list[float]
            Embedding vector.
        """
        if not text or not text.strip():
            spec = self._resolve_spec(model)
            return [0.0] * spec.dimensions

        spec = self._resolve_spec(model)
        th = _text_hash(text)

        # Cache lookup
        if use_cache:
            cached = self._cache.get(th, spec.name)
            if cached is not None:
                self._embed_count += 1
                return cached

        # Try backends in order
        vec = self._try_onnx(text, spec)
        if vec is None:
            vec = self._try_sentence_transformers(text, spec)
        if vec is None:
            vec = self._tfidf_embed(text, spec.dimensions)
            self._fallback_count += 1
            self._backend_used["tfidf_hash"] += 1

        # Cache store
        if use_cache:
            self._cache.put(th, vec, spec.name)

        self._embed_count += 1
        return vec

    def embed_batch(
        self,
        texts: List[str],
        model: str = "default",
        batch_size: int = 32,
        use_cache: bool = True,
    ) -> List[List[float]]:
        """Generate embeddings for a batch of texts.

        Parameters
        ----------
        texts : list[str]
            Input texts.
        model : str
            Task name or model directory name.
        batch_size : int
            Processing batch size for progress logging.
        use_cache : bool
            Whether to use the embedding cache.

        Returns
        -------
        list[list[float]]
            One embedding vector per input text.
        """
        results: List[List[float]] = []
        total = len(texts)
        t0 = time.monotonic()

        for i in range(0, total, batch_size):
            batch = texts[i: i + batch_size]
            for text in batch:
                vec = self.embed_text(text, model=model, use_cache=use_cache)
                results.append(vec)

            done = min(i + batch_size, total)
            if done % (batch_size * 4) == 0 or done == total:
                elapsed = time.monotonic() - t0
                rate = done / max(elapsed, 0.001)
                logger.info(
                    "embed_batch: %d/%d (%.1f/s)", done, total, rate,
                )

        elapsed = time.monotonic() - t0
        logger.info(
            "embed_batch complete: %d texts in %.2fs (%.1f/s)",
            total, elapsed, total / max(elapsed, 0.001),
        )
        return results

    # ------------------------------------------------------------------
    # Dimension reduction
    # ------------------------------------------------------------------

    def reduce_dimensions(
        self,
        vectors: List[List[float]],
        target_dim: int,
    ) -> List[List[float]]:
        """Reduce embedding dimensionality via PCA.

        Attempts NumPy-accelerated SVD first, falls back to pure-Python
        power iteration.

        Parameters
        ----------
        vectors : list of list of float
            Input vectors (same dimensionality).
        target_dim : int
            Desired output dimensionality.

        Returns
        -------
        list of list of float
            Projected vectors.
        """
        if not vectors:
            return []

        orig_dim = len(vectors[0])
        if target_dim >= orig_dim:
            logger.info(
                "target_dim %d >= original %d; returning original vectors",
                target_dim, orig_dim,
            )
            return [list(v) for v in vectors]

        t0 = time.monotonic()

        # Try numpy path
        if _HAS_NUMPY:
            try:
                result = _reduce_numpy(vectors, target_dim)
                elapsed = time.monotonic() - t0
                logger.info(
                    "Dimension reduction (numpy SVD): %dd → %dd "
                    "for %d vectors in %.2fs",
                    orig_dim, target_dim, len(vectors), elapsed,
                )
                return result
            except Exception as exc:  # noqa: BLE001
                logger.warning("NumPy SVD failed, using stdlib: %s", exc)

        # Stdlib fallback
        result = _reduce_pca_stdlib(vectors, target_dim)
        elapsed = time.monotonic() - t0
        logger.info(
            "Dimension reduction (stdlib PCA): %dd → %dd "
            "for %d vectors in %.2fs",
            orig_dim, target_dim, len(vectors), elapsed,
        )
        return result

    # ------------------------------------------------------------------
    # TF-IDF fallback (primary path)
    # ------------------------------------------------------------------

    def _tfidf_embed(self, text: str, dim: int = _DEFAULT_TFIDF_DIM) -> List[float]:
        """Generate a deterministic TF-IDF hash embedding.

        This is the *primary* embedding path since most environments
        lack ``onnxruntime`` and ``sentence-transformers``.

        Parameters
        ----------
        text : str
            Input text.
        dim : int
            Output dimensionality.

        Returns
        -------
        list[float]
            L2-normalised vector.
        """
        if dim not in self._tfidf:
            self._tfidf[dim] = _TfidfHashEmbedder(dim=dim)
        return self._tfidf[dim].embed(text)

    # ------------------------------------------------------------------
    # Backend: ONNX Runtime
    # ------------------------------------------------------------------

    def _try_onnx(self, text: str, spec: ModelSpec) -> Optional[List[float]]:
        """Attempt embedding via ONNX Runtime.

        Returns ``None`` if ONNX is unavailable or the model does not
        have an ONNX export.
        """
        if not _HAS_ONNX or not spec.has_onnx:
            return None

        try:
            session = self._get_onnx_session(spec)
            if session is None:
                return None

            # Tokenise with vocab.txt (WordPiece-like)
            input_ids, attention_mask = self._simple_tokenize(text, spec)

            # Run inference
            inputs = {
                "input_ids": [input_ids],
                "attention_mask": [attention_mask],
            }
            # Some models also need token_type_ids
            input_names = [inp.name for inp in session.get_inputs()]
            if "token_type_ids" in input_names:
                inputs["token_type_ids"] = [[0] * len(input_ids)]

            outputs = session.run(None, inputs)

            # Mean pooling of last hidden state
            hidden = outputs[0]  # shape: (1, seq_len, hidden_dim)
            if hasattr(hidden, "tolist"):
                hidden = hidden.tolist()
            seq_vecs = hidden[0]
            mask_sum = sum(attention_mask)
            if mask_sum == 0:
                return [0.0] * spec.dimensions

            pooled = [0.0] * spec.dimensions
            for i, m in enumerate(attention_mask):
                if m:
                    for d in range(spec.dimensions):
                        pooled[d] += seq_vecs[i][d]
            pooled = [v / mask_sum for v in pooled]

            # L2 normalise
            norm = math.sqrt(sum(v * v for v in pooled))
            if norm > 1e-12:
                pooled = [v / norm for v in pooled]

            self._backend_used["onnx"] += 1
            return pooled

        except Exception as exc:  # noqa: BLE001
            logger.debug("ONNX embedding failed for %s: %s", spec.name, exc)
            return None

    def _get_onnx_session(self, spec: ModelSpec) -> Optional[Any]:
        """Lazy-load and cache an ONNX InferenceSession."""
        cache_key = f"onnx_{spec.name}"
        if cache_key in self._loaded_models:
            return self._loaded_models[cache_key]

        onnx_dir = spec.model_dir / "onnx"
        if not onnx_dir.is_dir():
            return None

        onnx_files = [f for f in onnx_dir.iterdir() if f.suffix == ".onnx"]
        if not onnx_files:
            return None

        # Prefer model.onnx or the first found
        model_path = onnx_dir / "model.onnx"
        if not model_path.is_file():
            model_path = onnx_files[0]

        try:
            sess_opts = _ort.SessionOptions()
            sess_opts.graph_optimization_level = (
                _ort.GraphOptimizationLevel.ORT_ENABLE_ALL
            )
            sess_opts.intra_op_num_threads = max(1, os.cpu_count() or 1)
            session = _ort.InferenceSession(
                str(model_path),
                sess_options=sess_opts,
                providers=["CPUExecutionProvider"],
            )
            self._loaded_models[cache_key] = session
            logger.info("Loaded ONNX session: %s", model_path.name)
            return session
        except Exception as exc:  # noqa: BLE001
            logger.warning("Failed to load ONNX model %s: %s", model_path, exc)
            return None

    # ------------------------------------------------------------------
    # Backend: sentence-transformers
    # ------------------------------------------------------------------

    def _try_sentence_transformers(
        self, text: str, spec: ModelSpec
    ) -> Optional[List[float]]:
        """Attempt embedding via sentence-transformers.

        Only works for ``sentence_transformer`` model type and requires
        the ``sentence-transformers`` package.
        """
        if not _HAS_SENTENCE_TRANSFORMERS:
            return None
        if spec.model_type != "sentence_transformer":
            return None

        try:
            st_model = self._get_st_model(spec)
            if st_model is None:
                return None

            vec = st_model.encode(text, show_progress_bar=False)
            result = vec.tolist() if hasattr(vec, "tolist") else list(vec)

            # L2 normalise
            norm = math.sqrt(sum(v * v for v in result))
            if norm > 1e-12:
                result = [v / norm for v in result]

            self._backend_used["sentence_transformers"] += 1
            return result

        except Exception as exc:  # noqa: BLE001
            logger.debug("sentence-transformers failed for %s: %s", spec.name, exc)
            return None

    def _get_st_model(self, spec: ModelSpec) -> Optional[Any]:
        """Lazy-load a SentenceTransformer model."""
        cache_key = f"st_{spec.name}"
        if cache_key in self._loaded_models:
            return self._loaded_models[cache_key]

        try:
            model = _ST(str(spec.model_dir))
            self._loaded_models[cache_key] = model
            logger.info("Loaded sentence-transformers model: %s", spec.name)
            return model
        except Exception as exc:  # noqa: BLE001
            logger.warning("Failed to load ST model %s: %s", spec.name, exc)
            return None

    # ------------------------------------------------------------------
    # Simple tokeniser for ONNX (WordPiece-lite)
    # ------------------------------------------------------------------

    def _load_vocab(self, spec: ModelSpec) -> Dict[str, int]:
        """Load vocab.txt into a token→id mapping."""
        cache_key = f"vocab_{spec.name}"
        if cache_key in self._loaded_models:
            return self._loaded_models[cache_key]

        vocab_path = spec.model_dir / "vocab.txt"
        vocab: Dict[str, int] = {}
        if vocab_path.is_file():
            with open(vocab_path, "r", encoding="utf-8") as fh:
                for idx, line in enumerate(fh):
                    token = line.rstrip("\n")
                    vocab[token] = idx
        self._loaded_models[cache_key] = vocab
        return vocab

    def _simple_tokenize(
        self, text: str, spec: ModelSpec
    ) -> Tuple[List[int], List[int]]:
        """Minimal WordPiece-ish tokenisation for ONNX inference.

        Splits on whitespace, lowercases, then looks up each token in
        vocab.txt.  Unknown tokens are mapped to ``[UNK]``.  The result
        is padded/truncated to ``spec.max_seq_length`` and wrapped with
        ``[CLS]`` / ``[SEP]``.

        Returns
        -------
        tuple[list[int], list[int]]
            ``(input_ids, attention_mask)``
        """
        vocab = self._load_vocab(spec)
        cls_id = vocab.get("[CLS]", 101)
        sep_id = vocab.get("[SEP]", 102)
        unk_id = vocab.get("[UNK]", 100)
        pad_id = vocab.get("[PAD]", 0)

        words = text.lower().split()
        token_ids: List[int] = [cls_id]

        max_tokens = spec.max_seq_length - 2  # reserve CLS + SEP

        for word in words:
            if len(token_ids) - 1 >= max_tokens:
                break
            # Try full word
            if word in vocab:
                token_ids.append(vocab[word])
                continue

            # WordPiece: try subwords
            remaining = word
            matched_any = False
            while remaining:
                found = False
                for end in range(len(remaining), 0, -1):
                    sub = remaining[:end]
                    if matched_any:
                        sub = "##" + sub
                    if sub in vocab:
                        token_ids.append(vocab[sub])
                        remaining = remaining[end:]
                        found = True
                        matched_any = True
                        break
                if not found:
                    token_ids.append(unk_id)
                    break

            if len(token_ids) - 1 >= max_tokens:
                break

        token_ids.append(sep_id)

        # Pad to max_seq_length
        seq_len = spec.max_seq_length
        attention_mask = [1] * len(token_ids) + [0] * (seq_len - len(token_ids))
        token_ids = token_ids + [pad_id] * (seq_len - len(token_ids))

        # Truncate if somehow too long
        token_ids = token_ids[:seq_len]
        attention_mask = attention_mask[:seq_len]

        return token_ids, attention_mask

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _resolve_spec(self, model: str) -> ModelSpec:
        """Resolve a task name or model name to a ModelSpec.

        Falls back to a synthetic spec for the TF-IDF embedder when
        no models are discovered.
        """
        # Direct match by model directory name
        if model in self._specs:
            return self._specs[model]

        # Task alias lookup
        model_name = _TASK_MAP.get(model, _TASK_MAP.get("default", ""))
        if model_name in self._specs:
            return self._specs[model_name]

        # Fallback synthetic spec
        dim = self._default_dim
        for _name, meta in _MODEL_REGISTRY.items():
            if meta.get("task_alias") == model:
                dim = meta["dimensions"]
                break

        return ModelSpec(
            name=f"tfidf_fallback_{dim}d",
            dimensions=dim,
            model_dir=self._models_dir,
            model_type="tfidf_hash",
            has_onnx=False,
            has_safetensors=False,
            max_seq_length=512,
            vocab_size=0,
        )

    # ------------------------------------------------------------------
    # Stats
    # ------------------------------------------------------------------

    def get_stats(self) -> Dict[str, Any]:
        """Return comprehensive manager statistics.

        Returns
        -------
        dict
            Statistics covering discovered models, cache, backends,
            and embedding counts.
        """
        return {
            "models_discovered": len(self._specs),
            "models": {n: s.to_dict() for n, s in self._specs.items()},
            "models_dir": str(self._models_dir),
            "db_path": str(self._db_path),
            "backends_available": {
                "onnx": _HAS_ONNX,
                "sentence_transformers": _HAS_SENTENCE_TRANSFORMERS,
                "numpy": _HAS_NUMPY,
            },
            "backends_used": dict(self._backend_used),
            "embed_count": self._embed_count,
            "fallback_count": self._fallback_count,
            "tfidf_embedders": {
                str(dim): emb.get_stats()
                for dim, emb in self._tfidf.items()
            },
            "cache": self._cache.stats(),
            "loaded_models": list(self._loaded_models.keys()),
        }


# ---------------------------------------------------------------------------
# Module-level convenience
# ---------------------------------------------------------------------------

_DEFAULT_MANAGER: Optional[EmbeddingManager] = None


def get_manager(**kwargs: Any) -> EmbeddingManager:
    """Return a module-level singleton ``EmbeddingManager``.

    Keyword arguments are forwarded to the constructor on first call.
    """
    global _DEFAULT_MANAGER
    if _DEFAULT_MANAGER is None:
        _DEFAULT_MANAGER = EmbeddingManager(**kwargs)
    return _DEFAULT_MANAGER


def embed(text: str, model: str = "default") -> List[float]:
    """Convenience: embed a single text via the default manager."""
    return get_manager().embed_text(text, model=model)


def embed_batch(
    texts: List[str], model: str = "default", batch_size: int = 32
) -> List[List[float]]:
    """Convenience: embed a batch of texts via the default manager."""
    return get_manager().embed_batch(texts, model=model, batch_size=batch_size)


# ---------------------------------------------------------------------------
# CLI smoke test
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    )
    mgr = EmbeddingManager()
    specs = mgr.discover_models()
    print(f"\nDiscovered {len(specs)} models:")
    for s in specs:
        print(f"  {s.name}: {s.dimensions}d, onnx={s.has_onnx}, "
              f"safetensors={s.has_safetensors}, vocab={s.vocab_size}")

    test_texts = [
        "MCL 722.23 best interest of the child factors",
        "Motion to disqualify Judge McNeill under MCR 2.003",
        "Defendant failed to comply with discovery order",
        "Personal protection order violation under MCL 600.2950",
    ]
    print(f"\nEmbedding {len(test_texts)} texts:")
    for txt in test_texts:
        vec = mgr.embed_text(txt)
        print(f"  [{len(vec)}d] {txt[:60]}...")

    print(f"\nSimilarity matrix:")
    vecs = mgr.embed_batch(test_texts)
    for i, t1 in enumerate(test_texts):
        for j, t2 in enumerate(test_texts):
            sim = cosine_similarity(vecs[i], vecs[j])
            if j >= i:
                print(f"  [{i}↔{j}] {sim:.4f}  "
                      f"{t1[:30]}... ↔ {t2[:30]}...")

    stats = mgr.get_stats()
    print(f"\nStats: {json.dumps(stats, indent=2, default=str)}")
