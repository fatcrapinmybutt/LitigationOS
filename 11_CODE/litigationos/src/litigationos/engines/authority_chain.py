"""Citation Chain Builder and Validator engine.

Builds, validates, and scores chains of legal authority for Michigan court
filings.  Each chain links authorities from the Michigan hierarchy —
constitutional provisions → statutes → court rules → evidence rules → case
law — and grades chain completeness so filings never cite an MCR without
its statutory anchor or miss binding precedent.

Connects directly to ``litigation_context.db`` so it can operate both
inside the desktop app and standalone in pipeline scripts.  Uses FTS5
for authority search when available, falling back to ``LIKE`` queries.
"""

from __future__ import annotations

import logging
import re
import sqlite3
from datetime import datetime
from pathlib import Path
from typing import TYPE_CHECKING, Any, Dict, List, Optional, Tuple

if TYPE_CHECKING:
    from litigationos.db.connection import DatabaseManager

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Path to central litigation database
# ---------------------------------------------------------------------------

_DEFAULT_DB = Path(r"C:\Users\andre\LitigationOS\litigation_context.db")

# ---------------------------------------------------------------------------
# Michigan Authority Hierarchy (highest → lowest weight)
# ---------------------------------------------------------------------------

AUTHORITY_LEVELS: List[Dict[str, Any]] = [
    {"level": "constitutional", "rank": 1, "label": "US / MI Constitution",
     "weight": 1.0},
    {"level": "federal_statute", "rank": 2, "label": "Federal Statutes (USC)",
     "weight": 0.95},
    {"level": "state_statute", "rank": 3, "label": "Michigan Statutes (MCL)",
     "weight": 0.90},
    {"level": "court_rule", "rank": 4, "label": "Michigan Court Rules (MCR)",
     "weight": 0.85},
    {"level": "evidence_rule", "rank": 5, "label": "Michigan Rules of Evidence (MRE)",
     "weight": 0.80},
    {"level": "supreme_court", "rank": 6,
     "label": "MI Supreme Court (binding)", "weight": 0.75},
    {"level": "court_of_appeals", "rank": 7,
     "label": "MI Court of Appeals (binding in division)", "weight": 0.70},
    {"level": "federal_circuit", "rank": 8,
     "label": "Federal Circuit Cases (persuasive)", "weight": 0.55},
    {"level": "secondary", "rank": 9,
     "label": "Secondary Sources (treatises, law review)", "weight": 0.30},
]

_LEVEL_NAMES: List[str] = [lvl["level"] for lvl in AUTHORITY_LEVELS]

_LEVEL_WEIGHTS: Dict[str, float] = {
    lvl["level"]: lvl["weight"] for lvl in AUTHORITY_LEVELS
}

# Minimum levels expected for a filing-quality chain
_REQUIRED_LEVELS = {"state_statute", "court_rule"}

# ---------------------------------------------------------------------------
# Citation‐type detection patterns
# ---------------------------------------------------------------------------

_CITE_PATTERNS: Dict[str, re.Pattern[str]] = {
    "constitutional": re.compile(
        r"(?:U\.?S\.?\s*Const|Const\s+Art|MI\s+Const|Mich\.?\s*Const)",
        re.IGNORECASE,
    ),
    "federal_statute": re.compile(
        r"\b\d{1,2}\s+U\.?S\.?C\.?\s*§\s*\d+", re.IGNORECASE,
    ),
    "state_statute": re.compile(
        r"\bMCL\s+\d{2,4}\.\d+", re.IGNORECASE,
    ),
    "court_rule": re.compile(
        r"\bMCR\s+\d+\.\d+", re.IGNORECASE,
    ),
    "evidence_rule": re.compile(
        r"\bMRE\s+\d+", re.IGNORECASE,
    ),
    "supreme_court": re.compile(
        r"\d+\s+Mich\s+\d+", re.IGNORECASE,
    ),
    "court_of_appeals": re.compile(
        r"\d+\s+Mich\s+App\s+\d+", re.IGNORECASE,
    ),
    "federal_circuit": re.compile(
        r"\d+\s+F\.?\s*(?:2d|3d|4th)\s+\d+", re.IGNORECASE,
    ),
}

# ---------------------------------------------------------------------------
# Source table mapping — verified at runtime via PRAGMA table_info
# ---------------------------------------------------------------------------

_SOURCE_TABLES: Dict[str, Dict[str, str]] = {
    "michigan_court_rules": {
        "level": "court_rule",
        "cite_col": "rule_number",
        "title_col": "title",
        "text_col": "full_text",
    },
    "michigan_statutes": {
        "level": "state_statute",
        "cite_col": "statute_number",
        "title_col": "title",
        "text_col": "full_text",
    },
    "michigan_case_law": {
        "level": "case",
        "cite_col": "citation",
        "title_col": "case_name",
        "text_col": "holding",
    },
    "michigan_rules_of_evidence": {
        "level": "evidence_rule",
        "cite_col": "rule_number",
        "title_col": "title",
        "text_col": "full_text",
    },
}

# FTS5 tables that may exist for accelerated search
_FTS_TABLES = ("legal_knowledge_fts", "auth_rules_fts", "auth_passages_fts")


# ===================================================================
# Helper utilities (module-level, not part of the class)
# ===================================================================

def _sanitize_fts_query(query: str) -> str:
    """Escape special FTS5 characters so user input is safe.

    Wraps each word in double-quotes to prevent syntax errors from
    stray ``*``, ``(``, ``)`` etc.
    """
    words = re.findall(r"[\w']+", query)
    if not words:
        return '""'
    return " ".join(f'"{w}"' for w in words)


def _detect_level(citation: str) -> str:
    """Infer the authority level from a citation string."""
    for level, pat in _CITE_PATTERNS.items():
        if pat.search(citation):
            return level
    return "secondary"


def _extract_pin_cite(text: str) -> str:
    """Extract a parenthetical pin cite from a citation string.

    Looks for common patterns like ``(2020)``, ``at 345``, ``¶ 12``.
    Returns the pin cite portion or an empty string.
    """
    m = re.search(r"(?:at\s+\d+|¶\s*\d+|\(\d{4}\))", text)
    return m.group(0) if m else ""


# ===================================================================
# AuthorityChainEngine
# ===================================================================

class AuthorityChainEngine:
    """Build, validate, and score chains of legal authority.

    Each *chain* is an ordered list of authority links spanning the
    Michigan hierarchy (constitutional → statutory → rule → case).
    The engine queries ``litigation_context.db`` for authorities across
    multiple tables, validates chain completeness, and scores chain
    strength for filing readiness.

    Usage::

        engine = AuthorityChainEngine()
        chain = engine.build_chain("custody_modification")
        result = engine.validate_chain(chain)
        score = engine.score_chain_strength(chain)

    Or with the desktop app's :class:`DatabaseManager`::

        engine = AuthorityChainEngine(db=my_db_manager)
    """

    def __init__(
        self,
        db: Optional["DatabaseManager"] = None,
        db_path: Optional[str | Path] = None,
    ) -> None:
        self._db = db
        self._db_path = Path(db_path) if db_path else _DEFAULT_DB
        # Cache discovered table schemas: {table_name: [col_name, ...]}
        self._schema_cache: Dict[str, List[str]] = {}
        # Cache whether FTS5 tables are available
        self._fts_available: Optional[bool] = None

    # ------------------------------------------------------------------
    # Connection helpers
    # ------------------------------------------------------------------

    def _connect(self) -> sqlite3.Connection:
        """Open a WAL-mode connection with litigation-safe PRAGMAs."""
        conn = sqlite3.connect(str(self._db_path), timeout=60)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA busy_timeout = 60000")
        conn.execute("PRAGMA journal_mode = WAL")
        conn.execute("PRAGMA cache_size = -32000")
        conn.execute("PRAGMA temp_store = MEMORY")
        conn.execute("PRAGMA synchronous = NORMAL")
        return conn

    def _table_exists(self, conn: sqlite3.Connection, name: str) -> bool:
        """Return ``True`` if *name* is a table or view in the database."""
        row = conn.execute(
            "SELECT 1 FROM sqlite_master WHERE type IN ('table','view') AND name = ?",
            (name,),
        ).fetchone()
        return row is not None

    def _get_columns(self, conn: sqlite3.Connection, table: str) -> List[str]:
        """Return column names for *table*, caching the result.

        Always runs ``PRAGMA table_info`` on the first call for a table
        to avoid stale assumptions about column names.
        """
        if table in self._schema_cache:
            return self._schema_cache[table]
        try:
            info = conn.execute(f"PRAGMA table_info({table})").fetchall()
            cols = [row[1] for row in info]
            self._schema_cache[table] = cols
            return cols
        except sqlite3.Error:
            logger.warning("Cannot read schema for table %s", table)
            return []

    def _has_column(
        self, conn: sqlite3.Connection, table: str, column: str
    ) -> bool:
        """Check if *table* has a column named *column*."""
        return column in self._get_columns(conn, table)

    def _check_fts(self, conn: sqlite3.Connection) -> bool:
        """Return ``True`` if at least one FTS5 index is available."""
        if self._fts_available is not None:
            return self._fts_available
        for fts in _FTS_TABLES:
            if self._table_exists(conn, fts):
                self._fts_available = True
                return True
        self._fts_available = False
        return False

    # ------------------------------------------------------------------
    # 1. build_chain
    # ------------------------------------------------------------------

    def build_chain(
        self,
        claim_type: str,
        vehicle_name: str = "",
    ) -> List[Dict[str, Any]]:
        """Build an authority chain for a claim type.

        Searches the authority tables for entries relevant to
        *claim_type* (e.g. ``"custody_modification"``,
        ``"disqualification"``) and returns an ordered list of
        authority links from highest to lowest hierarchy.

        Args:
            claim_type: The legal claim or filing type to build a
                chain for (e.g. ``"custody_modification"``).
            vehicle_name: Optional filing vehicle / case lane name
                to narrow results.

        Returns:
            Ordered list of authority link dicts, each containing:

            * **level** — hierarchy level (``"constitutional"``, etc.)
            * **citation** — canonical citation string
            * **text** — relevant excerpt or holding
            * **relevance** — ``0.0``–``1.0`` relevance score
            * **pin_cite** — pin cite if found, else ``""``
        """
        chain: List[Dict[str, Any]] = []
        try:
            with self._connect() as conn:
                # Try FTS5 first, then fall back to LIKE queries
                if self._check_fts(conn):
                    chain = self._build_chain_fts(conn, claim_type, vehicle_name)
                if not chain:
                    chain = self._build_chain_like(conn, claim_type, vehicle_name)

                # Supplement with existing authority_chains table data
                chain = self._merge_existing_chains(
                    conn, chain, claim_type, vehicle_name,
                )
        except sqlite3.Error:
            logger.exception("Failed to build authority chain for %r", claim_type)

        # Sort by hierarchy rank
        chain.sort(key=lambda link: _LEVEL_NAMES.index(link["level"])
                   if link["level"] in _LEVEL_NAMES else 99)
        return chain

    def _build_chain_fts(
        self,
        conn: sqlite3.Connection,
        claim_type: str,
        vehicle_name: str,
    ) -> List[Dict[str, Any]]:
        """Build chain via FTS5 search on ``legal_knowledge_fts``."""
        if not self._table_exists(conn, "legal_knowledge_fts"):
            return []

        safe_q = _sanitize_fts_query(claim_type)
        try:
            rows = conn.execute(
                """
                SELECT source_type, source_id, rule_number, title,
                       snippet(legal_knowledge_fts, 4, '', '', '...', 60) AS snippet,
                       rank
                FROM legal_knowledge_fts
                WHERE legal_knowledge_fts MATCH ?
                ORDER BY rank
                LIMIT 30
                """,
                (safe_q,),
            ).fetchall()
        except sqlite3.OperationalError:
            logger.debug("FTS5 MATCH failed for %r — falling back", safe_q)
            return []

        chain: List[Dict[str, Any]] = []
        for row in rows:
            level = self._source_type_to_level(row["source_type"])
            relevance = self._rank_to_relevance(row["rank"])
            chain.append({
                "level": level,
                "citation": row["rule_number"] or "",
                "text": row["snippet"] or row["title"] or "",
                "relevance": round(relevance, 3),
                "pin_cite": _extract_pin_cite(row["rule_number"] or ""),
            })
        return chain

    def _build_chain_like(
        self,
        conn: sqlite3.Connection,
        claim_type: str,
        vehicle_name: str,
    ) -> List[Dict[str, Any]]:
        """Build chain via ``LIKE`` queries when FTS5 is unavailable."""
        chain: List[Dict[str, Any]] = []
        pattern = f"%{claim_type}%"

        for table, meta in _SOURCE_TABLES.items():
            if not self._table_exists(conn, table):
                continue
            cols = self._get_columns(conn, table)
            cite_col = meta["cite_col"] if meta["cite_col"] in cols else None
            title_col = meta["title_col"] if meta["title_col"] in cols else None
            text_col = meta["text_col"] if meta["text_col"] in cols else None
            if not cite_col:
                continue

            where_parts: List[str] = []
            params: List[str] = []
            for c in (title_col, text_col):
                if c:
                    where_parts.append(f"{c} LIKE ?")
                    params.append(pattern)
            if "category" in cols:
                where_parts.append("category LIKE ?")
                params.append(pattern)
            if not where_parts:
                continue

            # Optionally filter by vehicle_name / lane
            if vehicle_name and "vehicle_name" in cols:
                where_parts.append("vehicle_name = ?")
                params.append(vehicle_name)
            elif vehicle_name and "lane" in cols:
                where_parts.append("lane = ?")
                params.append(vehicle_name)

            sql = (
                f"SELECT {cite_col}"
                f"{', ' + title_col if title_col else ''}"
                f"{', ' + text_col if text_col else ''}"
                f" FROM {table}"
                f" WHERE {' OR '.join(where_parts)}"
                f" LIMIT 15"
            )
            try:
                rows = conn.execute(sql, params).fetchall()
            except sqlite3.Error:
                logger.debug("LIKE query failed on %s", table)
                continue

            level = meta["level"]
            # Case-law sub-classification
            for row in rows:
                actual_level = level
                cite = row[0] or ""
                if level == "case":
                    actual_level = self._classify_case_level(conn, cite, table)
                text = row[2] if len(row) > 2 and row[2] else (
                    row[1] if len(row) > 1 and row[1] else ""
                )
                chain.append({
                    "level": actual_level,
                    "citation": cite,
                    "text": str(text)[:500],
                    "relevance": 0.5,
                    "pin_cite": _extract_pin_cite(cite),
                })
        return chain

    def _merge_existing_chains(
        self,
        conn: sqlite3.Connection,
        chain: List[Dict[str, Any]],
        claim_type: str,
        vehicle_name: str,
    ) -> List[Dict[str, Any]]:
        """Merge results from the ``authority_chains`` table if it exists."""
        if not self._table_exists(conn, "authority_chains"):
            return chain

        cols = self._get_columns(conn, "authority_chains")
        existing_cites = {link["citation"] for link in chain}

        where_parts: List[str] = []
        params: List[str] = []

        # Build query dynamically based on actual columns
        claim_col = next(
            (c for c in ("claim_type", "fact_claim", "claim") if c in cols),
            None,
        )
        if claim_col:
            where_parts.append(f"{claim_col} LIKE ?")
            params.append(f"%{claim_type}%")
        if vehicle_name:
            vn_col = next(
                (c for c in ("vehicle_name", "vehicle", "lane") if c in cols),
                None,
            )
            if vn_col:
                where_parts.append(f"{vn_col} = ?")
                params.append(vehicle_name)

        if not where_parts:
            return chain

        cite_col = next(
            (c for c in ("authority_cite", "citation", "cite") if c in cols),
            None,
        )
        text_col = next(
            (c for c in ("authority_text", "text", "holding", "description")
             if c in cols),
            None,
        )

        select_cols = [c for c in (cite_col, text_col) if c]
        if not select_cols:
            return chain

        sql = (
            f"SELECT {', '.join(select_cols)} FROM authority_chains"
            f" WHERE {' AND '.join(where_parts)}"
            f" LIMIT 30"
        )
        try:
            rows = conn.execute(sql, params).fetchall()
        except sqlite3.Error:
            logger.debug("Could not query authority_chains table")
            return chain

        for row in rows:
            cite = row[0] or ""
            if cite in existing_cites:
                continue
            existing_cites.add(cite)
            text = row[1] if len(row) > 1 and row[1] else ""
            chain.append({
                "level": _detect_level(cite),
                "citation": cite,
                "text": str(text)[:500],
                "relevance": 0.6,
                "pin_cite": _extract_pin_cite(cite),
            })
        return chain

    # ------------------------------------------------------------------
    # 2. validate_chain
    # ------------------------------------------------------------------

    def validate_chain(self, chain: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Validate authority chain completeness and strength.

        Checks that the chain includes the required hierarchy levels,
        flags gaps, and calculates an overall strength score.

        Args:
            chain: List of authority link dicts as returned by
                :meth:`build_chain`.

        Returns:
            Dict with:

            * **complete** — ``True`` if all required levels are present
            * **missing_levels** — list of hierarchy levels not covered
            * **strength** — ``0.0``–``1.0`` weighted strength score
            * **suggestions** — list of human-readable improvement tips
            * **level_coverage** — dict mapping each level to its count
        """
        if not chain:
            return {
                "complete": False,
                "missing_levels": list(_REQUIRED_LEVELS),
                "strength": 0.0,
                "suggestions": [
                    "Chain is empty — run build_chain() first.",
                ],
                "level_coverage": {},
            }

        present_levels: Dict[str, int] = {}
        total_relevance = 0.0
        has_pin_cite = 0
        has_binding = 0

        for link in chain:
            lvl = link.get("level", "secondary")
            present_levels[lvl] = present_levels.get(lvl, 0) + 1
            total_relevance += link.get("relevance", 0.0)
            if link.get("pin_cite"):
                has_pin_cite += 1
            if lvl in ("supreme_court", "court_of_appeals", "constitutional",
                       "state_statute", "court_rule"):
                has_binding += 1

        missing = [
            lvl for lvl in _REQUIRED_LEVELS if lvl not in present_levels
        ]
        complete = len(missing) == 0

        # Weighted strength: hierarchy coverage + relevance + extras
        coverage_score = sum(
            _LEVEL_WEIGHTS.get(lvl, 0.3) for lvl in present_levels
        ) / sum(_LEVEL_WEIGHTS.get(lvl, 0.3) for lvl in _LEVEL_NAMES)

        avg_relevance = (
            total_relevance / len(chain) if chain else 0.0
        )
        pin_cite_bonus = min(has_pin_cite / max(len(chain), 1), 1.0) * 0.1
        binding_bonus = min(has_binding / max(len(chain), 1), 1.0) * 0.15

        strength = min(
            coverage_score * 0.50
            + avg_relevance * 0.25
            + pin_cite_bonus
            + binding_bonus,
            1.0,
        )

        suggestions = self._generate_suggestions(
            present_levels, missing, chain, has_pin_cite,
        )

        return {
            "complete": complete,
            "missing_levels": missing,
            "strength": round(strength, 3),
            "suggestions": suggestions,
            "level_coverage": present_levels,
        }

    @staticmethod
    def _generate_suggestions(
        present: Dict[str, int],
        missing: List[str],
        chain: List[Dict[str, Any]],
        pin_count: int,
    ) -> List[str]:
        """Generate human-readable suggestions for improving the chain."""
        tips: List[str] = []
        for lvl in missing:
            label = next(
                (a["label"] for a in AUTHORITY_LEVELS if a["level"] == lvl),
                lvl,
            )
            tips.append(f"Add {label} authority to strengthen the chain.")

        if "constitutional" not in present:
            tips.append(
                "Consider adding a constitutional anchor (e.g. 14th Amendment "
                "due process for parental rights cases)."
            )
        if "supreme_court" not in present and "court_of_appeals" not in present:
            tips.append(
                "No binding Michigan case law found — add MI Supreme Court "
                "or Court of Appeals precedent."
            )
        if pin_count == 0 and chain:
            tips.append(
                "No pin cites detected — add page or paragraph references "
                "for each authority."
            )
        low_rel = [
            lnk for lnk in chain if lnk.get("relevance", 0) < 0.3
        ]
        if low_rel:
            tips.append(
                f"{len(low_rel)} authorities have low relevance — "
                "consider replacing with more on-point citations."
            )
        return tips

    # ------------------------------------------------------------------
    # 3. find_authorities
    # ------------------------------------------------------------------

    def find_authorities(
        self,
        query: str,
        category: str = "",
    ) -> List[Dict[str, Any]]:
        """Search for authorities matching *query*.

        Uses FTS5 on ``legal_knowledge_fts`` when available, otherwise
        falls back to ``LIKE`` queries across ``michigan_court_rules``,
        ``michigan_statutes``, ``michigan_case_law``, and
        ``michigan_rules_of_evidence``.

        Args:
            query: Search terms (e.g. ``"parenting time modification"``).
            category: Optional category filter (e.g. ``"custody"``).

        Returns:
            List of authority dicts with *level*, *citation*, *title*,
            *text*, and *relevance*.
        """
        results: List[Dict[str, Any]] = []
        try:
            with self._connect() as conn:
                if self._check_fts(conn):
                    results = self._search_fts(conn, query, category)
                if not results:
                    results = self._search_like(conn, query, category)

                # Also search research_authorities if it exists
                results.extend(
                    self._search_research_authorities(conn, query, category)
                )
        except sqlite3.Error:
            logger.exception("Authority search failed for %r", query)

        # Deduplicate by citation
        seen: set[str] = set()
        deduped: List[Dict[str, Any]] = []
        for r in results:
            cite = r.get("citation", "")
            if cite and cite not in seen:
                seen.add(cite)
                deduped.append(r)
        return deduped

    def _search_fts(
        self,
        conn: sqlite3.Connection,
        query: str,
        category: str,
    ) -> List[Dict[str, Any]]:
        """FTS5 authority search on ``legal_knowledge_fts``."""
        if not self._table_exists(conn, "legal_knowledge_fts"):
            return []

        safe_q = _sanitize_fts_query(query)
        try:
            if category:
                rows = conn.execute(
                    """
                    SELECT source_type, rule_number, title, full_text, rank
                    FROM legal_knowledge_fts
                    WHERE legal_knowledge_fts MATCH ? AND category = ?
                    ORDER BY rank
                    LIMIT 25
                    """,
                    (safe_q, category),
                ).fetchall()
            else:
                rows = conn.execute(
                    """
                    SELECT source_type, rule_number, title, full_text, rank
                    FROM legal_knowledge_fts
                    WHERE legal_knowledge_fts MATCH ?
                    ORDER BY rank
                    LIMIT 25
                    """,
                    (safe_q,),
                ).fetchall()
        except sqlite3.OperationalError:
            logger.debug("FTS5 search failed for %r", safe_q)
            return []

        results: List[Dict[str, Any]] = []
        for row in rows:
            level = self._source_type_to_level(row["source_type"])
            results.append({
                "level": level,
                "citation": row["rule_number"] or "",
                "title": row["title"] or "",
                "text": (row["full_text"] or "")[:500],
                "relevance": round(self._rank_to_relevance(row["rank"]), 3),
            })
        return results

    def _search_like(
        self,
        conn: sqlite3.Connection,
        query: str,
        category: str,
    ) -> List[Dict[str, Any]]:
        """Fallback ``LIKE`` search across source tables."""
        results: List[Dict[str, Any]] = []
        pattern = f"%{query}%"

        for table, meta in _SOURCE_TABLES.items():
            if not self._table_exists(conn, table):
                continue
            cols = self._get_columns(conn, table)
            cite_col = meta["cite_col"] if meta["cite_col"] in cols else None
            title_col = meta["title_col"] if meta["title_col"] in cols else None
            text_col = meta["text_col"] if meta["text_col"] in cols else None
            if not cite_col:
                continue

            where_clauses: List[str] = []
            params: List[str] = []
            for c in (title_col, text_col):
                if c:
                    where_clauses.append(f"{c} LIKE ?")
                    params.append(pattern)
            if cite_col:
                where_clauses.append(f"{cite_col} LIKE ?")
                params.append(pattern)
            if category and "category" in cols:
                where_clauses.append("category LIKE ?")
                params.append(f"%{category}%")

            if not where_clauses:
                continue

            select_parts = [c for c in (cite_col, title_col, text_col) if c]
            sql = (
                f"SELECT {', '.join(select_parts)} FROM {table}"
                f" WHERE {' OR '.join(where_clauses)}"
                f" LIMIT 15"
            )
            try:
                rows = conn.execute(sql, params).fetchall()
            except sqlite3.Error:
                logger.debug("LIKE search failed on %s", table)
                continue

            level = meta["level"]
            for row in rows:
                cite = row[0] or ""
                actual_level = level
                if level == "case":
                    actual_level = self._classify_case_level(conn, cite, table)
                results.append({
                    "level": actual_level,
                    "citation": cite,
                    "title": row[1] if len(row) > 1 and row[1] else "",
                    "text": (str(row[2]) if len(row) > 2 and row[2] else "")[:500],
                    "relevance": 0.5,
                })
        return results

    def _search_research_authorities(
        self,
        conn: sqlite3.Connection,
        query: str,
        category: str,
    ) -> List[Dict[str, Any]]:
        """Search ``research_authorities`` table if it exists."""
        if not self._table_exists(conn, "research_authorities"):
            return []

        cols = self._get_columns(conn, "research_authorities")
        cite_col = next(
            (c for c in ("citation", "authority_cite", "cite") if c in cols),
            None,
        )
        text_col = next(
            (c for c in ("text", "holding", "description", "summary")
             if c in cols),
            None,
        )
        if not cite_col:
            return []

        where_parts: List[str] = []
        params: List[str] = []
        pattern = f"%{query}%"
        for c in (cite_col, text_col):
            if c:
                where_parts.append(f"{c} LIKE ?")
                params.append(pattern)
        if not where_parts:
            return []

        select_parts = [c for c in (cite_col, text_col) if c]
        sql = (
            f"SELECT {', '.join(select_parts)} FROM research_authorities"
            f" WHERE {' OR '.join(where_parts)}"
            f" LIMIT 10"
        )
        try:
            rows = conn.execute(sql, params).fetchall()
        except sqlite3.Error:
            return []

        results: List[Dict[str, Any]] = []
        for row in rows:
            cite = row[0] or ""
            results.append({
                "level": _detect_level(cite),
                "citation": cite,
                "title": "",
                "text": (str(row[1]) if len(row) > 1 and row[1] else "")[:500],
                "relevance": 0.4,
            })
        return results

    # ------------------------------------------------------------------
    # 4. get_supporting_evidence
    # ------------------------------------------------------------------

    def get_supporting_evidence(
        self,
        citation: str,
        vehicle_name: str = "",
    ) -> List[Dict[str, Any]]:
        """Find evidence quotes that support a cited authority.

        Searches the ``evidence_quotes`` table for rows matching the
        citation string and optional vehicle/filing context.

        Args:
            citation: The authority citation (e.g. ``"MCL 722.23"``).
            vehicle_name: Optional filing vehicle name to narrow results.

        Returns:
            List of evidence dicts with available columns from the table.
        """
        results: List[Dict[str, Any]] = []
        try:
            with self._connect() as conn:
                if not self._table_exists(conn, "evidence_quotes"):
                    logger.debug("evidence_quotes table not found")
                    return []

                cols = self._get_columns(conn, "evidence_quotes")

                # Try FTS on evidence_quotes_fts first
                if self._table_exists(conn, "evidence_quotes_fts"):
                    results = self._evidence_fts(conn, citation, vehicle_name)
                    if results:
                        return results

                # Fallback: LIKE query on evidence_quotes
                cite_cols = [
                    c for c in ("citation", "authority_cite", "claim_id",
                                "source", "rule_reference")
                    if c in cols
                ]
                text_cols = [
                    c for c in ("quote_text", "text", "quote", "content",
                                "description")
                    if c in cols
                ]

                if not cite_cols:
                    # Search across all text columns
                    cite_cols = text_cols

                where_parts: List[str] = []
                params: List[str] = []
                for c in cite_cols:
                    where_parts.append(f"{c} LIKE ?")
                    params.append(f"%{citation}%")
                if not where_parts:
                    return []

                if vehicle_name:
                    vn_col = next(
                        (c for c in ("vehicle_name", "vehicle", "filing_id",
                                     "lane")
                         if c in cols),
                        None,
                    )
                    if vn_col:
                        where_parts.append(f"{vn_col} = ?")
                        params.append(vehicle_name)

                select_cols = list(dict.fromkeys(cite_cols + text_cols))[:6]
                if not select_cols:
                    return []

                sql = (
                    f"SELECT {', '.join(select_cols)} FROM evidence_quotes"
                    f" WHERE {' OR '.join(where_parts)}"
                    f" LIMIT 20"
                )
                rows = conn.execute(sql, params).fetchall()
                results = [dict(row) for row in rows]
        except sqlite3.Error:
            logger.exception("Evidence search failed for %r", citation)

        return results

    def _evidence_fts(
        self,
        conn: sqlite3.Connection,
        citation: str,
        vehicle_name: str,
    ) -> List[Dict[str, Any]]:
        """Search evidence via FTS5 on ``evidence_quotes_fts``."""
        safe_q = _sanitize_fts_query(citation)
        try:
            rows = conn.execute(
                """
                SELECT * FROM evidence_quotes_fts
                WHERE evidence_quotes_fts MATCH ?
                LIMIT 20
                """,
                (safe_q,),
            ).fetchall()
            return [dict(row) for row in rows]
        except sqlite3.Error:
            return []

    # ------------------------------------------------------------------
    # 5. format_citation
    # ------------------------------------------------------------------

    def format_citation(
        self,
        authority: Dict[str, Any],
        style: str = "bluebook",
    ) -> str:
        """Format a citation in Bluebook or Michigan style.

        Args:
            authority: Dict with at least a ``citation`` key (and
                optionally ``level``, ``title``, ``pin_cite``).
            style: ``"bluebook"`` (default) or ``"michigan"``.

        Returns:
            Formatted citation string.
        """
        cite = authority.get("citation", "")
        pin = authority.get("pin_cite", "")
        level = authority.get("level", _detect_level(cite))
        title = authority.get("title", "")

        if style == "michigan":
            return self._format_michigan(cite, pin, level, title)
        return self._format_bluebook(cite, pin, level, title)

    @staticmethod
    def _format_bluebook(
        cite: str, pin: str, level: str, title: str,
    ) -> str:
        """Bluebook citation formatting."""
        parts: List[str] = []

        if level in ("supreme_court", "court_of_appeals", "federal_circuit"):
            # Case citation: Title, Reporter (Year)
            if title:
                parts.append(f"{title}, ")
            parts.append(cite)
            if pin and "at" not in pin:
                parts.append(f", at {pin}")
            elif pin:
                parts.append(f", {pin}")
        elif level in ("state_statute", "federal_statute"):
            # Statute: Mich Comp Laws § 722.23
            cleaned = cite.strip()
            if cleaned.upper().startswith("MCL"):
                num = cleaned[3:].strip().lstrip("§").strip()
                parts.append(f"Mich Comp Laws § {num}")
            elif re.match(r"\d+\s+U\.?S\.?C", cleaned):
                parts.append(cleaned)
            else:
                parts.append(cleaned)
            if pin:
                parts.append(f" {pin}")
        elif level == "court_rule":
            parts.append(f"Mich Ct R {cite.replace('MCR ', '')}")
            if pin:
                parts.append(f" {pin}")
        elif level == "evidence_rule":
            parts.append(f"Mich R Evid {cite.replace('MRE ', '')}")
            if pin:
                parts.append(f" {pin}")
        elif level == "constitutional":
            parts.append(cite)
            if pin:
                parts.append(f" {pin}")
        else:
            parts.append(cite)
            if pin:
                parts.append(f" {pin}")

        return "".join(parts)

    @staticmethod
    def _format_michigan(
        cite: str, pin: str, level: str, title: str,
    ) -> str:
        """Michigan-style citation formatting.

        Michigan courts generally accept citations as-is (MCL, MCR, MRE
        abbreviations) without the Bluebook expansions.
        """
        parts: List[str] = []

        if level in ("supreme_court", "court_of_appeals", "federal_circuit"):
            if title:
                parts.append(f"{title}, ")
            parts.append(cite)
            if pin:
                sep = ", " if "at" not in pin else " "
                parts.append(f"{sep}{pin}")
        else:
            parts.append(cite)
            if pin:
                parts.append(f" {pin}")

        return "".join(parts)

    # ------------------------------------------------------------------
    # 6. check_good_law
    # ------------------------------------------------------------------

    def check_good_law(self, citation: str) -> Dict[str, Any]:
        """Basic good-law check for a citation.

        Looks in the database for overruled, superseded, or modified
        flags.  This is NOT a replacement for Shepard's / KeyCite but
        catches known issues stored locally.

        Args:
            citation: Citation to check (e.g. ``"450 Mich 100"``).

        Returns:
            Dict with:

            * **citation** — the queried citation
            * **good_law** — ``True`` if no negative flags found
            * **flags** — list of flag strings (``"overruled"``, etc.)
            * **superseded_by** — replacement citation if known
            * **checked_tables** — list of tables that were searched
        """
        result: Dict[str, Any] = {
            "citation": citation,
            "good_law": True,
            "flags": [],
            "superseded_by": "",
            "checked_tables": [],
        }
        negative_patterns = re.compile(
            r"overrul|supersed|abrogat|disapprov|modif|reversed|vacated",
            re.IGNORECASE,
        )

        try:
            with self._connect() as conn:
                # Check michigan_case_law
                if self._table_exists(conn, "michigan_case_law"):
                    result["checked_tables"].append("michigan_case_law")
                    cols = self._get_columns(conn, "michigan_case_law")
                    cite_col = (
                        "citation" if "citation" in cols else None
                    )
                    if cite_col:
                        row = conn.execute(
                            f"SELECT * FROM michigan_case_law WHERE {cite_col} = ?",
                            (citation,),
                        ).fetchone()
                        if row:
                            row_d = dict(row)
                            for col_name in ("status", "treatment",
                                             "subsequent_history", "notes",
                                             "relevance"):
                                val = row_d.get(col_name, "")
                                if val and negative_patterns.search(str(val)):
                                    result["good_law"] = False
                                    result["flags"].append(
                                        f"{col_name}: {str(val)[:200]}"
                                    )

                # Check authority_chains for flags
                if self._table_exists(conn, "authority_chains"):
                    result["checked_tables"].append("authority_chains")
                    cols = self._get_columns(conn, "authority_chains")
                    cite_col = next(
                        (c for c in ("authority_cite", "citation", "cite")
                         if c in cols),
                        None,
                    )
                    status_col = next(
                        (c for c in ("status", "treatment", "good_law")
                         if c in cols),
                        None,
                    )
                    if cite_col:
                        rows = conn.execute(
                            f"SELECT * FROM authority_chains WHERE {cite_col} = ?",
                            (citation,),
                        ).fetchall()
                        for row in rows:
                            row_d = dict(row)
                            if status_col:
                                val = row_d.get(status_col, "")
                                if val and negative_patterns.search(str(val)):
                                    result["good_law"] = False
                                    result["flags"].append(
                                        f"{status_col}: {str(val)[:200]}"
                                    )
                            # Check for superseded_by column
                            sup_col = next(
                                (c for c in ("superseded_by", "replaced_by")
                                 if c in cols),
                                None,
                            )
                            if sup_col and row_d.get(sup_col):
                                result["superseded_by"] = str(
                                    row_d[sup_col]
                                )

                # Check research_authorities
                if self._table_exists(conn, "research_authorities"):
                    result["checked_tables"].append("research_authorities")
                    cols = self._get_columns(conn, "research_authorities")
                    cite_col = next(
                        (c for c in ("citation", "authority_cite", "cite")
                         if c in cols),
                        None,
                    )
                    if cite_col:
                        rows = conn.execute(
                            f"SELECT * FROM research_authorities"
                            f" WHERE {cite_col} = ? LIMIT 5",
                            (citation,),
                        ).fetchall()
                        for row in rows:
                            row_d = dict(row)
                            for val in row_d.values():
                                if val and negative_patterns.search(str(val)):
                                    result["good_law"] = False
                                    result["flags"].append(
                                        f"research: {str(val)[:200]}"
                                    )
                                    break
        except sqlite3.Error:
            logger.exception("Good-law check failed for %r", citation)

        return result

    # ------------------------------------------------------------------
    # 7. build_string_cite
    # ------------------------------------------------------------------

    def build_string_cite(
        self,
        authorities: List[Dict[str, Any]],
        style: str = "bluebook",
    ) -> str:
        """Build a string citation (multiple authorities in one footnote).

        Authorities are separated by semicolons and ordered by hierarchy
        rank (highest first).

        Args:
            authorities: List of authority dicts.
            style: ``"bluebook"`` or ``"michigan"``.

        Returns:
            Semicolon-separated citation string (e.g.
            ``"US Const amend XIV; Mich Comp Laws § 722.23; ..."``).
        """
        if not authorities:
            return ""

        # Sort by hierarchy rank
        def _rank(auth: Dict[str, Any]) -> int:
            lvl = auth.get("level", _detect_level(auth.get("citation", "")))
            try:
                return _LEVEL_NAMES.index(lvl)
            except ValueError:
                return 99

        sorted_auths = sorted(authorities, key=_rank)
        formatted = [
            self.format_citation(auth, style=style)
            for auth in sorted_auths
        ]
        # Filter empty strings
        formatted = [f for f in formatted if f.strip()]
        return "; ".join(formatted)

    # ------------------------------------------------------------------
    # 8. get_chain_for_filing
    # ------------------------------------------------------------------

    def get_chain_for_filing(
        self,
        filing_id: str,
    ) -> List[Dict[str, Any]]:
        """Get all authority chains stored for a filing.

        Queries ``authority_chains`` and ``filing_rule_map`` for the
        given filing ID and returns a unified chain.

        Args:
            filing_id: The filing identifier (e.g. ``"motion_disq_001"``).

        Returns:
            List of authority link dicts ordered by hierarchy rank.
        """
        chain: List[Dict[str, Any]] = []
        seen: set[str] = set()

        try:
            with self._connect() as conn:
                # Query authority_chains table
                if self._table_exists(conn, "authority_chains"):
                    cols = self._get_columns(conn, "authority_chains")
                    fid_col = next(
                        (c for c in ("filing_id", "filing", "vehicle_name")
                         if c in cols),
                        None,
                    )
                    cite_col = next(
                        (c for c in ("authority_cite", "citation", "cite")
                         if c in cols),
                        None,
                    )
                    text_col = next(
                        (c for c in ("authority_text", "text", "holding",
                                     "description")
                         if c in cols),
                        None,
                    )
                    complete_col = next(
                        (c for c in ("chain_complete", "is_complete",
                                     "complete")
                         if c in cols),
                        None,
                    )

                    if fid_col and cite_col:
                        select_parts = [
                            c for c in (cite_col, text_col, complete_col)
                            if c
                        ]
                        sql = (
                            f"SELECT {', '.join(select_parts)}"
                            f" FROM authority_chains"
                            f" WHERE {fid_col} = ?"
                        )
                        rows = conn.execute(sql, (filing_id,)).fetchall()
                        for row in rows:
                            cite = row[0] or ""
                            if cite in seen:
                                continue
                            seen.add(cite)
                            text = (
                                row[1]
                                if len(row) > 1 and row[1]
                                else ""
                            )
                            chain.append({
                                "level": _detect_level(cite),
                                "citation": cite,
                                "text": str(text)[:500],
                                "relevance": 0.7,
                                "pin_cite": _extract_pin_cite(cite),
                            })

                # Query filing_rule_map for mapped authorities
                if self._table_exists(conn, "filing_rule_map"):
                    cols = self._get_columns(conn, "filing_rule_map")
                    if "filing_id" in cols and "authority_number" in cols:
                        rows = conn.execute(
                            """
                            SELECT authority_type, authority_number,
                                   requirement
                            FROM filing_rule_map
                            WHERE filing_id = ?
                            """,
                            (filing_id,),
                        ).fetchall()
                        for row in rows:
                            cite = row["authority_number"] or ""
                            a_type = row["authority_type"] or ""
                            if cite in seen:
                                continue
                            seen.add(cite)
                            full_cite = (
                                f"{a_type} {cite}" if a_type else cite
                            )
                            chain.append({
                                "level": _detect_level(full_cite),
                                "citation": full_cite,
                                "text": row["requirement"] or "",
                                "relevance": 0.8,
                                "pin_cite": "",
                            })

        except sqlite3.Error:
            logger.exception(
                "Failed to get chain for filing %r", filing_id,
            )

        chain.sort(
            key=lambda link: _LEVEL_NAMES.index(link["level"])
            if link["level"] in _LEVEL_NAMES else 99
        )
        return chain

    # ------------------------------------------------------------------
    # 9. score_chain_strength
    # ------------------------------------------------------------------

    def score_chain_strength(
        self,
        chain: List[Dict[str, Any]],
    ) -> float:
        """Score a chain 0–100 based on multiple quality factors.

        Scoring factors (weighted):

        * **Constitutional backing** (15 pts) — chain includes a
          constitutional provision.
        * **Binding authority** (25 pts) — MI Supreme Court or COA
          cases present, statutes cited.
        * **Recency** (15 pts) — cases from the last 10 years score
          higher.
        * **Pin cites** (10 pts) — every link with a pin cite adds
          points.
        * **Evidence linkage** (15 pts) — authorities linked to
          evidence in the DB.
        * **Hierarchy coverage** (20 pts) — more distinct levels =
          higher score.

        Args:
            chain: List of authority link dicts.

        Returns:
            Score from ``0.0`` to ``100.0``.
        """
        if not chain:
            return 0.0

        score = 0.0

        # --- Constitutional backing (15 pts) ---
        has_constitutional = any(
            link.get("level") == "constitutional" for link in chain
        )
        if has_constitutional:
            score += 15.0

        # --- Binding authority (25 pts) ---
        binding_levels = {
            "state_statute", "court_rule", "evidence_rule",
            "supreme_court", "court_of_appeals",
        }
        binding_count = sum(
            1 for link in chain if link.get("level") in binding_levels
        )
        score += min(binding_count * 5.0, 25.0)

        # --- Recency (15 pts) ---
        current_year = datetime.now().year
        recency_points = 0.0
        year_pattern = re.compile(r"\((\d{4})\)")
        case_count = 0
        for link in chain:
            if link.get("level") in ("supreme_court", "court_of_appeals",
                                     "federal_circuit"):
                case_count += 1
                cite = link.get("citation", "") + " " + link.get("text", "")
                m = year_pattern.search(cite)
                if m:
                    year = int(m.group(1))
                    age = current_year - year
                    if age <= 5:
                        recency_points += 15.0
                    elif age <= 10:
                        recency_points += 10.0
                    elif age <= 20:
                        recency_points += 5.0
                    else:
                        recency_points += 2.0
        if case_count > 0:
            score += min(recency_points / case_count, 15.0)
        else:
            # No case law — partial credit if statutes exist
            if binding_count > 0:
                score += 5.0

        # --- Pin cites (10 pts) ---
        pin_count = sum(1 for link in chain if link.get("pin_cite"))
        if chain:
            score += min((pin_count / len(chain)) * 10.0, 10.0)

        # --- Evidence linkage (15 pts) ---
        evidence_score = self._score_evidence_linkage(chain)
        score += min(evidence_score, 15.0)

        # --- Hierarchy coverage (20 pts) ---
        distinct_levels = {link.get("level") for link in chain}
        coverage = len(distinct_levels & set(_LEVEL_NAMES))
        max_levels = len(_LEVEL_NAMES)
        score += (coverage / max_levels) * 20.0

        return round(min(score, 100.0), 1)

    def _score_evidence_linkage(
        self,
        chain: List[Dict[str, Any]],
    ) -> float:
        """Check how many chain citations have supporting evidence."""
        if not chain:
            return 0.0

        linked = 0
        try:
            with self._connect() as conn:
                if not self._table_exists(conn, "evidence_quotes"):
                    return 0.0
                cols = self._get_columns(conn, "evidence_quotes")
                search_cols = [
                    c for c in ("citation", "authority_cite", "rule_reference",
                                "source", "quote_text", "text")
                    if c in cols
                ]
                if not search_cols:
                    return 0.0

                for link in chain:
                    cite = link.get("citation", "")
                    if not cite:
                        continue
                    where = " OR ".join(f"{c} LIKE ?" for c in search_cols)
                    params = [f"%{cite}%"] * len(search_cols)
                    row = conn.execute(
                        f"SELECT 1 FROM evidence_quotes"
                        f" WHERE {where} LIMIT 1",
                        params,
                    ).fetchone()
                    if row:
                        linked += 1
        except sqlite3.Error:
            logger.debug("Evidence linkage scoring failed")

        if chain:
            return (linked / len(chain)) * 15.0
        return 0.0

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _source_type_to_level(source_type: str) -> str:
        """Map FTS5 ``source_type`` codes to hierarchy level names."""
        mapping = {
            "MCR": "court_rule",
            "MCL": "state_statute",
            "MRE": "evidence_rule",
            "CASE": "court_of_appeals",
            "CANON": "secondary",
            "USC": "federal_statute",
            "CONST": "constitutional",
        }
        return mapping.get(source_type, "secondary")

    @staticmethod
    def _rank_to_relevance(rank: float) -> float:
        """Convert an FTS5 rank (negative, lower = better) to 0–1."""
        if rank is None:
            return 0.5
        # FTS5 rank is negative; closer to 0 = better match
        abs_rank = abs(float(rank))
        if abs_rank < 1:
            return 0.95
        if abs_rank < 5:
            return 0.8
        if abs_rank < 15:
            return 0.6
        if abs_rank < 30:
            return 0.4
        return 0.2

    def _classify_case_level(
        self,
        conn: sqlite3.Connection,
        citation: str,
        table: str,
    ) -> str:
        """Classify a case citation into supreme_court / court_of_appeals / federal_circuit."""
        # Pattern-based classification first
        if re.search(r"\d+\s+Mich\s+\d+", citation) and not re.search(
            r"Mich\s+App", citation
        ):
            return "supreme_court"
        if re.search(r"Mich\s+App", citation):
            return "court_of_appeals"
        if re.search(r"F\.?\s*(?:2d|3d|4th)", citation):
            return "federal_circuit"
        if re.search(r"U\.?S\.?\s+\d+", citation):
            return "supreme_court"  # US Supreme Court

        # Try DB court column
        if self._table_exists(conn, table):
            cols = self._get_columns(conn, table)
            cite_col = next(
                (c for c in ("citation", "cite") if c in cols), None,
            )
            court_col = next(
                (c for c in ("court", "court_name") if c in cols), None,
            )
            if cite_col and court_col:
                row = conn.execute(
                    f"SELECT {court_col} FROM {table}"
                    f" WHERE {cite_col} = ? LIMIT 1",
                    (citation,),
                ).fetchone()
                if row and row[0]:
                    court = str(row[0]).lower()
                    if "supreme" in court:
                        return "supreme_court"
                    if "appeal" in court or "coa" in court:
                        return "court_of_appeals"
                    if "circuit" in court or "district" in court:
                        return "federal_circuit"

        return "court_of_appeals"  # default for MI cases
