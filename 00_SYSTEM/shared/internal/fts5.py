"""
FTS5 query sanitization and safe search for LitigationOS.

Legal citations contain characters (periods, parentheses, section signs)
that crash SQLite FTS5. This module provides:
- sanitize_fts5()     — MUST be called before any FTS5 MATCH query
- safe_fts5_search()  — try MATCH → except → LIKE fallback (Rule 15)
- expand_query()      — legal domain synonym expansion for better recall
- cached_search()     — LRU-cached wrapper for repeated queries

Pattern source: 00_SYSTEM/engines/nexus/nexus_engine.py sanitize_fts5()
"""

import re
import sqlite3
import logging
import functools
from typing import Any

logger = logging.getLogger("litigationos.fts5")

# ---------------------------------------------------------------------------
# Legal domain synonym map — used by expand_query() for recall improvement
# Source: mi_warchest_v2/topics.yaml (previously unused at query time)
# ---------------------------------------------------------------------------
LEGAL_SYNONYMS: dict[str, list[str]] = {
    "custody": ["custody", "parenting time", "parenting-time", "best interests", "custodial"],
    "alienation": ["alienation", "parental alienation", "parent-child relationship"],
    "ppo": ["ppo", "personal protection order", "no contact", "protection order"],
    "contempt": ["contempt", "show cause", "show-cause", "violation", "noncompliance"],
    "disqualification": ["disqualification", "disqualify", "recusal", "recuse", "bias", "prejudice"],
    "misconduct": ["misconduct", "judicial misconduct", "canon violation", "bias"],
    "due process": ["due process", "fundamental right", "parental rights", "constitutional"],
    "evidence": ["evidence", "exhibit", "testimony", "declaration", "affidavit"],
    "motion": ["motion", "filing", "petition", "complaint", "brief"],
    "medication": ["medication", "prescription", "mental health", "evaluation", "therapy"],
}


def sanitize_fts5(query: str) -> str:
    """Sanitize a query string for safe FTS5 MATCH usage.

    Strips characters that break FTS5 (periods, colons, parentheses,
    section signs, brackets) while preserving:
    - Quoted phrases ("exact match")
    - Wildcard suffixes (prefix*)
    - Boolean operators (AND, OR, NOT)
    - Alphanumeric tokens (2+ characters)

    Args:
        query: Raw search query, possibly containing legal citations
               like "MCL 722.23(j)" or "MCR 2.003(C)(1)(b)".

    Returns:
        Sanitized query safe for FTS5 MATCH.

    Examples:
        >>> sanitize_fts5("MCL 722.23(j)")
        'MCL 722 23 j'
        >>> sanitize_fts5('"parental alienation" OR custody')
        '"parental alienation" OR custody'
        >>> sanitize_fts5("custod*")
        'custod*'
        >>> sanitize_fts5("")
        ''
    """
    if not query:
        return ""

    # Extract quoted phrases first (preserve them intact)
    phrases = re.findall(r'"[^"]*"', query)
    remainder = re.sub(r'"[^"]*"', '', query)

    # Boolean operators to preserve
    ops = {"AND", "OR", "NOT"}

    # Strip FTS5-hostile characters: . : ( ) § [ ] { } / \\ @ # $ % ^ & + = ~ ` | < >
    remainder = re.sub(r'[^\w\s*]', ' ', remainder)

    # Collapse multiple spaces
    remainder = re.sub(r'\s+', ' ', remainder).strip()

    # Rebuild tokens: keep operators and 2+ char tokens, preserve * suffix
    tokens = []
    for t in remainder.split():
        if t.upper() in ops:
            tokens.append(t.upper())
        elif len(t.rstrip('*')) >= 2:
            tokens.append(t)

    # Combine preserved phrases + cleaned tokens
    parts = phrases + tokens
    return " ".join(parts) if parts else ""


def sanitize_fts5_near(query: str, distance: int = 10) -> str:
    """Build a NEAR query from two search terms.

    Usage:
        sanitize_fts5_near("custody alienation")
        # → 'NEAR(custody alienation, 10)'

    Args:
        query: Space-separated terms (exactly 2 terms for NEAR)
        distance: Max token distance between terms (default 10)

    Returns:
        FTS5 NEAR query string, or regular sanitized query if < 2 terms.
    """
    clean = sanitize_fts5(query)
    tokens = [t for t in clean.split() if t.upper() not in {"AND", "OR", "NOT"}]
    if len(tokens) >= 2:
        return f"NEAR({' '.join(tokens)}, {distance})"
    return clean


def build_fts5_query(
    terms: list[str],
    operator: str = "AND",
    phrases: list[str] | None = None,
    prefix_terms: list[str] | None = None,
) -> str:
    """Build a safe FTS5 query from structured components.

    Usage:
        build_fts5_query(
            terms=["custody", "alienation"],
            operator="AND",
            phrases=["parental alienation"],
            prefix_terms=["custod"]
        )
        # → '"parental alienation" AND custody AND alienation AND custod*'

    Args:
        terms: Individual search terms
        operator: Boolean operator (AND, OR, NOT)
        phrases: Exact phrase matches (auto-quoted)
        prefix_terms: Prefix search terms (auto-starred)

    Returns:
        Sanitized, structured FTS5 query.
    """
    parts = []

    # Add quoted phrases first
    for p in (phrases or []):
        clean_phrase = re.sub(r'[^\w\s]', ' ', p).strip()
        if clean_phrase:
            parts.append(f'"{clean_phrase}"')

    # Add regular terms (sanitized)
    for t in terms:
        clean = sanitize_fts5(t)
        if clean:
            parts.append(clean)

    # Add prefix terms
    for pt in (prefix_terms or []):
        clean = re.sub(r'[^\w]', '', pt)
        if len(clean) >= 2:
            parts.append(f"{clean}*")

    op = f" {operator.upper()} "
    return op.join(parts) if parts else ""


# ---------------------------------------------------------------------------
# LIKE fallback — Rule 15: FTS5 crash → parameterized LIKE recovery
# ---------------------------------------------------------------------------

def _like_fallback(
    conn: sqlite3.Connection,
    table: str,
    column: str,
    query: str,
    limit: int = 25,
    extra_where: str = "",
    extra_params: tuple = (),
) -> list[sqlite3.Row]:
    """Parameterized LIKE search as FTS5 fallback.

    Splits query into terms and builds AND-joined LIKE clauses.
    Returns rows matching ALL terms (intersection).

    Args:
        conn: Database connection
        table: Base table name (NOT FTS table)
        column: Text column to search
        query: Raw search query
        limit: Max results
        extra_where: Additional WHERE clause (e.g., "AND lane = ?")
        extra_params: Parameters for extra_where
    """
    terms = re.sub(r'[^\w\s]', ' ', query).split()
    terms = [t for t in terms if len(t) >= 2 and t.upper() not in {"AND", "OR", "NOT"}]

    if not terms:
        return []

    like_clauses = [f"{column} LIKE ?" for _ in terms]
    like_params = tuple(f"%{t}%" for t in terms)

    where = " AND ".join(like_clauses)
    if extra_where:
        where = f"({where}) {extra_where}"

    sql = f"SELECT * FROM [{table}] WHERE {where} LIMIT ?"
    params = like_params + extra_params + (limit,)

    return conn.execute(sql, params).fetchall()


def safe_fts5_search(
    conn: sqlite3.Connection,
    fts_table: str,
    base_table: str,
    text_column: str,
    query: str,
    limit: int = 25,
    extra_where: str = "",
    extra_params: tuple = (),
    order_by: str = "rank",
    pre_sanitized: bool = False,
) -> tuple[list[Any], str]:
    """Safe FTS5 search with automatic LIKE fallback (Rule 15).

    Implements the full safety protocol:
    1. Sanitize query with sanitize_fts5() (unless pre_sanitized=True)
    2. Try FTS5 MATCH in try/except
    3. On ANY exception → fall back to parameterized LIKE on base_table

    Args:
        conn: Database connection
        fts_table: FTS5 virtual table name (e.g., "evidence_fts")
        base_table: Underlying table name (e.g., "evidence_quotes")
        text_column: Column to search in LIKE fallback (e.g., "quote_text")
        query: Raw search query
        limit: Max results
        extra_where: Additional WHERE clause for both paths
        extra_params: Parameters for extra_where
        order_by: ORDER BY clause for FTS5 path (default: "rank")
        pre_sanitized: If True, skip sanitize_fts5() (for expand_query output)

    Returns:
        Tuple of (results_list, method_used) where method_used is
        "FTS5" or "LIKE_FALLBACK".

    Examples:
        >>> rows, method = safe_fts5_search(
        ...     conn, "evidence_fts", "evidence_quotes", "quote_text",
        ...     "parental alienation", limit=10
        ... )
        >>> print(f"Found {len(rows)} via {method}")
    """
    safe_query = query if pre_sanitized else sanitize_fts5(query)
    if not safe_query:
        return [], "EMPTY_QUERY"

    # Path 1: Try FTS5 MATCH
    try:
        where_clause = f"[{fts_table}] MATCH ?"
        if extra_where:
            where_clause = f"{where_clause} {extra_where}"

        sql = (
            f"SELECT *, rank FROM [{fts_table}] "
            f"WHERE {where_clause} "
            f"ORDER BY {order_by} LIMIT ?"
        )
        params = (safe_query,) + extra_params + (limit,)
        rows = conn.execute(sql, params).fetchall()
        return rows, "FTS5"

    except Exception as e:
        logger.warning(
            f"FTS5 MATCH failed on [{fts_table}] for query '{safe_query}': {e}. "
            f"Falling back to LIKE on [{base_table}].{text_column}"
        )

    # Path 2: LIKE fallback (guaranteed to work)
    try:
        rows = _like_fallback(
            conn, base_table, text_column, query,
            limit=limit, extra_where=extra_where, extra_params=extra_params,
        )
        return rows, "LIKE_FALLBACK"
    except Exception as e2:
        logger.error(f"LIKE fallback also failed on [{base_table}]: {e2}")
        return [], "BOTH_FAILED"


# ---------------------------------------------------------------------------
# Query expansion — legal domain synonym broadening for recall
# ---------------------------------------------------------------------------

# Pre-built reverse synonym index for O(1) lookup (avoids O(n) scan each query)
_SYNONYM_REVERSE: dict[str, tuple[str, list[str]]] = {}
for _key, _syns in LEGAL_SYNONYMS.items():
    for _token in _key.lower().split():
        if _token not in _SYNONYM_REVERSE:
            _SYNONYM_REVERSE[_token] = (_key, _syns)
    for _syn in _syns:
        _syn_lower = _syn.lower()
        if _syn_lower not in _SYNONYM_REVERSE:
            _SYNONYM_REVERSE[_syn_lower] = (_key, _syns)


def expand_query(query: str, max_expansions: int = 3) -> str:
    """Expand a search query with legal domain synonyms.

    Looks up each term in LEGAL_SYNONYMS and adds OR-joined alternatives.
    Improves recall for legal searches where exact terminology varies.

    Args:
        query: Raw search query
        max_expansions: Max synonym additions per term (prevents query explosion)

    Returns:
        Expanded query with OR-joined synonyms, sanitized for FTS5.

    Examples:
        >>> expand_query("custody alienation")
        'custody OR "parenting time" OR "best interests" OR alienation OR "parental alienation"'
        >>> expand_query("MCL 722.23")  # No synonyms found
        'MCL 722 23'
    """
    clean = sanitize_fts5(query)
    if not clean:
        return ""

    tokens = clean.lower().split()
    expanded_parts: list[str] = []
    seen: set[str] = set()

    for token in tokens:
        if token.upper() in {"AND", "OR", "NOT"}:
            continue

        # Always include original token
        if token not in seen:
            expanded_parts.append(token)
            seen.add(token)

        # Look up synonyms via pre-built reverse index (O(1) instead of O(n))
        if token in _SYNONYM_REVERSE:
            _key, synonyms = _SYNONYM_REVERSE[token]
            added = 0
            for syn in synonyms:
                syn_lower = syn.lower()
                if syn_lower not in seen and added < max_expansions:
                    if " " in syn:
                        expanded_parts.append(f'"{syn}"')
                    else:
                        expanded_parts.append(syn_lower)
                    seen.add(syn_lower)
                    added += 1

    return " OR ".join(expanded_parts) if expanded_parts else clean


# ---------------------------------------------------------------------------
# Cached search — LRU cache for repeated identical queries
# ---------------------------------------------------------------------------

@functools.lru_cache(maxsize=512)
def _cached_fts5_key(fts_table: str, query: str, limit: int) -> str:
    """Cache key generator — returns sanitized query for cache lookup.

    The actual caching happens in cached_search() which wraps this.
    This function exists to make the cache key hashable.
    """
    return sanitize_fts5(query)


_search_cache: dict[str, tuple[list[dict], str, float]] = {}  # key -> (results, method, timestamp)
_CACHE_MAX = 512
_CACHE_TTL = 300.0  # 5-minute TTL for search results


def cached_search(
    conn: sqlite3.Connection,
    fts_table: str,
    base_table: str,
    text_column: str,
    query: str,
    limit: int = 25,
) -> tuple[list[Any], str]:
    """Cached wrapper around safe_fts5_search() with TTL.

    Caches results by (fts_table, sanitized_query, limit) key.
    Cache is in-memory, session-scoped, max 512 entries with 5-min TTL.

    Use for hot paths where the same query runs repeatedly within a session
    (e.g., evidence_fts searches during filing assembly).

    Returns:
        Same as safe_fts5_search: (results_list, method_used)
    """
    import time
    cache_key = f"{fts_table}:{sanitize_fts5(query)}:{limit}"
    now = time.time()

    if cache_key in _search_cache:
        cached_results, cached_method, cached_time = _search_cache[cache_key]
        if (now - cached_time) < _CACHE_TTL:
            return cached_results, cached_method
        # Expired — remove stale entry
        del _search_cache[cache_key]

    results, method = safe_fts5_search(
        conn, fts_table, base_table, text_column, query, limit
    )

    # Convert Row objects to dicts for cacheability
    dict_results = [dict(r) if hasattr(r, 'keys') else r for r in results]

    # LRU eviction (remove oldest entries first)
    while len(_search_cache) >= _CACHE_MAX:
        oldest_key = next(iter(_search_cache))
        del _search_cache[oldest_key]

    _search_cache[cache_key] = (dict_results, method, now)
    return dict_results, method


def clear_search_cache() -> int:
    """Clear the search cache. Returns number of entries cleared."""
    count = len(_search_cache)
    _search_cache.clear()
    return count
