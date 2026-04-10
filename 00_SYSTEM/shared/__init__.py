"""
LitigationOS Shared Primitives
===============================
Cross-cutting concerns used by engines, brains, tools, and pipeline.

This module provides THE ONE WAY to:
- Connect to any LitigationOS database (with standard PRAGMAs)
- Resolve file paths (respecting env overrides)
- Sanitize FTS5 queries (preventing crashes from legal citations)

Import ONLY from this file. Never import from shared.internal.

Usage:
    from shared import get_db, get_db_path, sanitize_fts5, get_root

    conn = get_db()                          # litigation_context.db
    conn = get_db("authority_brain")         # brain DB
    safe = sanitize_fts5("MCL 722.23(j)")   # → "MCL 722 23 j"
    root = get_root()                        # Path to LitigationOS
"""

from .internal.db import (
    get_db,
    get_db_path,
    STANDARD_PRAGMAS,
    LitigationDBError,
    db_connection,
    db_transaction,
    retry_on_busy,
    query_timer,
    get_db_readonly,
)
from .internal.config import (
    get_root,
    get_brain_dir,
    get_engine_dir,
    get_tools_dir,
    DB_REGISTRY,
    get_filing_dir,
    get_evidence_dir,
    get_analysis_dir,
    get_workspace_dir,
    get_archive_dir,
    get_data_dir,
    get_canon_dir,
    CANON_DIRS,
)
from .internal.fts5 import (
    sanitize_fts5,
    sanitize_fts5_near,
    build_fts5_query,
    safe_fts5_search,
    expand_query,
    cached_search,
    clear_search_cache,
    LEGAL_SYNONYMS,
)

try:
    from .internal.eval import (
        SafetyChecker,
        CitationVerifier,
        FormatChecker,
        MetricsRecorder,
        AgentEvalSuite,
        evaluate_text,
        quick_safety_check,
    )
except Exception:  # noqa: BLE001 – graceful degradation if eval deps missing
    SafetyChecker = None  # type: ignore[assignment,misc]
    CitationVerifier = None  # type: ignore[assignment,misc]
    FormatChecker = None  # type: ignore[assignment,misc]
    MetricsRecorder = None  # type: ignore[assignment,misc]
    AgentEvalSuite = None  # type: ignore[assignment,misc]
    evaluate_text = None  # type: ignore[assignment]
    quick_safety_check = None  # type: ignore[assignment]

__all__ = [
    # Database
    "get_db",
    "get_db_path",
    "STANDARD_PRAGMAS",
    "LitigationDBError",
    "db_connection",
    "db_transaction",
    "retry_on_busy",
    "query_timer",
    "get_db_readonly",
    # Configuration
    "get_root",
    "get_brain_dir",
    "get_engine_dir",
    "get_tools_dir",
    "DB_REGISTRY",
    "get_filing_dir",
    "get_evidence_dir",
    "get_analysis_dir",
    "get_workspace_dir",
    "get_archive_dir",
    "get_data_dir",
    "get_canon_dir",
    "CANON_DIRS",
    # FTS5 safety + search
    "sanitize_fts5",
    "sanitize_fts5_near",
    "build_fts5_query",
    "safe_fts5_search",
    "expand_query",
    "cached_search",
    "clear_search_cache",
    "LEGAL_SYNONYMS",
    # Evaluation framework
    "SafetyChecker",
    "CitationVerifier",
    "FormatChecker",
    "MetricsRecorder",
    "AgentEvalSuite",
    "evaluate_text",
    "quick_safety_check",
    # Engine accessors (lazy-loaded)
    "get_analytics_engine",
    "get_semantic_engine",
    "get_search_engine",
    "get_typst_engine",
    # Data acceleration
    "quick_query",
    "fast_dataframe",
]


# ---------------------------------------------------------------------------
# Lazy engine accessors — import on first call to avoid heavy startup costs
# ---------------------------------------------------------------------------

_engine_cache: dict = {}


def get_analytics_engine():
    """Get or create the DuckDB analytics engine (10-100x faster analytical queries)."""
    if "analytics" not in _engine_cache:
        from engines.analytics import AnalyticsEngine
        _engine_cache["analytics"] = AnalyticsEngine(str(get_db_path()))
    return _engine_cache["analytics"]


def get_semantic_engine():
    """Get or create the LanceDB semantic search engine (384-dim embeddings)."""
    if "semantic" not in _engine_cache:
        from engines.semantic import SemanticSearchEngine
        _engine_cache["semantic"] = SemanticSearchEngine(str(get_db_path()))
    return _engine_cache["semantic"]


def get_search_engine():
    """Get or create the hybrid search engine (tantivy + semantic + FTS5)."""
    if "search" not in _engine_cache:
        from engines.search import HybridSearchEngine
        _engine_cache["search"] = HybridSearchEngine(str(get_db_path()))
    return _engine_cache["search"]


def get_typst_engine():
    """Get or create the Typst filing engine (court-ready PDF generation)."""
    if "typst" not in _engine_cache:
        from engines.typst import TypstFilingEngine
        _engine_cache["typst"] = TypstFilingEngine(str(get_db_path()))
    return _engine_cache["typst"]


def get_perception_engine():
    """Get or create the Legal-BERT perception engine (INT8 ONNX, 768-dim)."""
    if "perception" not in _engine_cache:
        from engines.perception.engine import LegalBERTEngine
        engine = LegalBERTEngine()
        engine.setup()
        _engine_cache["perception"] = engine
    return _engine_cache["perception"]


def quick_query(sql: str, params: tuple = ()) -> list[dict]:
    """Execute an analytical SQL query via DuckDB (10-100x faster for GROUP BY, JOINs).

    Falls back to SQLite if DuckDB is unavailable.

    Args:
        sql: SQL query string (DuckDB SQL dialect).
        params: Query parameters.

    Returns:
        List of dicts, one per result row.
    """
    try:
        eng = get_analytics_engine()
        return eng.query(sql, params)
    except Exception:  # noqa: BLE001
        import sqlite3
        conn = get_db()
        conn.row_factory = sqlite3.Row
        rows = conn.execute(sql, params).fetchall()
        return [dict(r) for r in rows]


def fast_dataframe(table: str, columns: str = "*", where: str = "", limit: int = 0):
    """Load a table into a Polars DataFrame for fast columnar analysis.

    Args:
        table: Table name in litigation_context.db.
        columns: Column list (default "*").
        where: Optional WHERE clause (without 'WHERE').
        limit: Optional row limit.

    Returns:
        polars.DataFrame if polars is available, else list[dict].
    """
    sql = f"SELECT {columns} FROM {table}"  # noqa: S608
    if where:
        sql += f" WHERE {where}"
    if limit:
        sql += f" LIMIT {limit}"
    try:
        import polars as pl
        import sqlite3
        conn = sqlite3.connect(str(get_db_path()))
        conn.execute("PRAGMA busy_timeout=60000")
        conn.execute("PRAGMA journal_mode=WAL")
        return pl.read_database(sql, connection=conn)
    except ImportError:
        return quick_query(sql)


__version__ = "3.0.0"
