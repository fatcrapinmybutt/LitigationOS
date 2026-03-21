"""Unified Michigan Legal Knowledge Engine.

Provides FTS5-powered search across all legal knowledge tables:
michigan_court_rules, michigan_statutes, michigan_evidence_rules,
michigan_case_law, and cross-references between them.

This engine connects directly to litigation_context.db so it can operate
both inside the desktop app and standalone in pipeline scripts.
"""

from __future__ import annotations

import logging
import re
import sqlite3
from collections import defaultdict
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

logger = logging.getLogger(__name__)

# Path to central litigation database
_DEFAULT_DB = Path(r"C:\Users\andre\LitigationOS\litigation_context.db")

# All jurisdiction databases
_JURISDICTION_DBS = Path(r"C:\Users\andre\LitigationOS\databases")


class LegalKnowledgeEngine:
    """Unified search engine across all Michigan legal knowledge.

    Connects to litigation_context.db and optionally jurisdiction DBs.
    Provides FTS5-powered full-text search, cross-references, and
    structured lookups for MCR, MCL, MRE, and case law.

    Usage::

        engine = LegalKnowledgeEngine()
        results = engine.search("parenting time modification")
        xrefs = engine.get_cross_references("MCR", "MCR 3.210")
        stats = engine.get_stats()
    """

    # Source tables and their mapping into the unified FTS5 index
    _SOURCE_TABLES: List[Tuple[str, str, str, str, str]] = [
        # (table_name, source_type, rule_col, title_col, text_col)
        ("michigan_court_rules", "MCR", "rule_number", "title", "full_text"),
        ("michigan_statutes", "MCL", "statute_number", "title", "full_text"),
        ("michigan_evidence_rules", "MRE", "rule_number", "title", "full_text"),
    ]

    def __init__(self, db_path: Optional[str | Path] = None) -> None:
        self._db_path = Path(db_path) if db_path else _DEFAULT_DB
        self._ensure_fts5()
        self._ensure_cross_references()
        self._populate_fts5()

    # ------------------------------------------------------------------
    # Connection helper
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
        row = conn.execute(
            "SELECT 1 FROM sqlite_master WHERE type IN ('table','view') AND name=?",
            (name,),
        ).fetchone()
        return row is not None

    # ------------------------------------------------------------------
    # FTS5 Setup
    # ------------------------------------------------------------------

    def _ensure_fts5(self) -> None:
        """Create unified ``legal_knowledge_fts`` FTS5 table if absent."""
        with self._connect() as conn:
            conn.execute(
                """
                CREATE VIRTUAL TABLE IF NOT EXISTS legal_knowledge_fts USING fts5(
                    source_type,
                    source_id,
                    rule_number,
                    title,
                    full_text,
                    category,
                    tokenize='porter unicode61'
                )
                """
            )

            # Back-fill the existing (empty) court_rules_fts from MCR data
            if self._table_exists(conn, "court_rules_fts"):
                cnt = conn.execute("SELECT COUNT(*) FROM court_rules_fts").fetchone()[0]
                if cnt == 0 and self._table_exists(conn, "michigan_court_rules"):
                    conn.execute(
                        """
                        INSERT INTO court_rules_fts(rule_number, title, full_text, category)
                        SELECT rule_number, title, full_text, category
                        FROM michigan_court_rules
                        """
                    )
            conn.commit()

    def _populate_fts5(self) -> None:
        """Populate ``legal_knowledge_fts`` from every source table."""
        with self._connect() as conn:
            if conn.execute("SELECT COUNT(*) FROM legal_knowledge_fts").fetchone()[0] > 0:
                return  # already populated

            # Standard three-column tables (MCR / MCL / MRE)
            for table, src_type, rule_col, title_col, text_col in self._SOURCE_TABLES:
                if not self._table_exists(conn, table):
                    continue
                conn.execute(
                    f"""
                    INSERT INTO legal_knowledge_fts(
                        source_type, source_id, rule_number, title, full_text, category
                    )
                    SELECT ?, CAST(id AS TEXT), {rule_col}, {title_col},
                           COALESCE({text_col}, ''), COALESCE(category, '')
                    FROM {table}
                    """,
                    (src_type,),
                )

            # Case law (different column layout)
            if self._table_exists(conn, "michigan_case_law"):
                conn.execute(
                    """
                    INSERT INTO legal_knowledge_fts(
                        source_type, source_id, rule_number, title, full_text, category
                    )
                    SELECT 'CASE', CAST(id AS TEXT), citation, case_name,
                           COALESCE(holding, '') || ' ' || COALESCE(relevance, ''),
                           COALESCE(court, '')
                    FROM michigan_case_law
                    """
                )

            # Judicial canons (schema varies — discover columns at runtime)
            self._index_judicial_canons(conn)

            conn.commit()
            total = conn.execute("SELECT COUNT(*) FROM legal_knowledge_fts").fetchone()[0]
            logger.info("Populated legal_knowledge_fts with %d entries", total)

    def _index_judicial_canons(self, conn: sqlite3.Connection) -> None:
        """Best-effort indexing of ``michigan_judicial_canons``."""
        if not self._table_exists(conn, "michigan_judicial_canons"):
            return
        try:
            cols = [
                c[1]
                for c in conn.execute("PRAGMA table_info(michigan_judicial_canons)").fetchall()
            ]
            rule_col = next(
                (c for c in ("canon_number", "rule_number") if c in cols),
                cols[1] if len(cols) > 1 else "id",
            )
            title_col = next(
                (c for c in ("title", "canon_title") if c in cols),
                cols[2] if len(cols) > 2 else rule_col,
            )
            text_col = next(
                (c for c in ("full_text", "description") if c in cols),
                title_col,
            )
            conn.execute(
                f"""
                INSERT INTO legal_knowledge_fts(
                    source_type, source_id, rule_number, title, full_text, category
                )
                SELECT 'CANON', CAST(id AS TEXT), {rule_col}, {title_col},
                       COALESCE({text_col}, ''), 'judicial_conduct'
                FROM michigan_judicial_canons
                """
            )
        except Exception as exc:  # noqa: BLE001
            logger.warning("Could not index judicial canons: %s", exc)

    # ------------------------------------------------------------------
    # Cross-Reference Table
    # ------------------------------------------------------------------

    def _ensure_cross_references(self) -> None:
        """Create and populate ``legal_cross_references``."""
        with self._connect() as conn:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS legal_cross_references (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    source_type TEXT NOT NULL,
                    source_number TEXT NOT NULL,
                    target_type TEXT NOT NULL,
                    target_number TEXT NOT NULL,
                    relationship TEXT DEFAULT 'related',
                    filing_ids TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    UNIQUE(source_type, source_number, target_type, target_number)
                )
                """
            )

            if conn.execute("SELECT COUNT(*) FROM legal_cross_references").fetchone()[0] > 0:
                conn.commit()
                return

            self._xref_from_filing_rule_map(conn)
            self._xref_from_mcr_text(conn)

            conn.commit()
            total = conn.execute("SELECT COUNT(*) FROM legal_cross_references").fetchone()[0]
            logger.info("Built %d legal cross-references", total)

    def _xref_from_filing_rule_map(self, conn: sqlite3.Connection) -> None:
        """Derive co-citation cross-references from ``filing_rule_map``."""
        if not self._table_exists(conn, "filing_rule_map"):
            return

        rows = conn.execute(
            "SELECT filing_id, authority_type, authority_number FROM filing_rule_map ORDER BY filing_id"
        ).fetchall()

        filing_auths: Dict[str, List[Tuple[str, str]]] = defaultdict(list)
        for r in rows:
            filing_auths[r[0]].append((r[1], r[2]))

        xrefs: List[Tuple[str, str, str, str, str, Optional[str]]] = []
        for filing_id, auths in filing_auths.items():
            for i, (t1, n1) in enumerate(auths):
                for t2, n2 in auths[i + 1 :]:
                    if (t1, n1) != (t2, n2):
                        xrefs.append((t1, n1, t2, n2, "co_cited", str(filing_id)))

        if xrefs:
            conn.executemany(
                """
                INSERT OR IGNORE INTO legal_cross_references
                    (source_type, source_number, target_type, target_number, relationship, filing_ids)
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                xrefs,
            )

    def _xref_from_mcr_text(self, conn: sqlite3.Connection) -> None:
        """Extract MCR-to-MCR references from rule full_text."""
        if not self._table_exists(conn, "michigan_court_rules"):
            return

        rules = conn.execute(
            "SELECT rule_number, full_text FROM michigan_court_rules"
        ).fetchall()

        mcr_xrefs: List[Tuple[str, str, str, str, str, None]] = []
        for rule in rules:
            if not rule[1]:
                continue
            mentions = re.findall(r"MCR\s+(\d+\.\d+(?:\([A-Z]\))?)", rule[1])
            for m in mentions:
                target = f"MCR {m}"
                if target != rule[0]:
                    mcr_xrefs.append(("MCR", rule[0], "MCR", target, "references", None))

        if mcr_xrefs:
            conn.executemany(
                """
                INSERT OR IGNORE INTO legal_cross_references
                    (source_type, source_number, target_type, target_number, relationship, filing_ids)
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                mcr_xrefs,
            )

    # ------------------------------------------------------------------
    # Public API — Search
    # ------------------------------------------------------------------

    def search(
        self,
        query: str,
        *,
        source_type: Optional[str] = None,
        limit: int = 25,
    ) -> List[Dict[str, Any]]:
        """Full-text search across ALL legal knowledge.

        Args:
            query: Search terms (FTS5 syntax: AND, OR, NOT, phrases).
            source_type: Optional filter — ``'MCR'``, ``'MCL'``, ``'MRE'``,
                ``'CASE'``, ``'CANON'``.
            limit: Maximum results (default 25).

        Returns:
            List of dicts with *source_type*, *source_id*, *rule_number*,
            *title*, *snippet* (highlighted), and *rank*.
        """
        try:
            with self._connect() as conn:
                if source_type:
                    rows = conn.execute(
                        """
                        SELECT source_type, source_id, rule_number, title,
                               snippet(legal_knowledge_fts, 4, '<b>', '</b>', '...', 40) AS snippet,
                               rank
                        FROM legal_knowledge_fts
                        WHERE legal_knowledge_fts MATCH ? AND source_type = ?
                        ORDER BY rank
                        LIMIT ?
                        """,
                        (query, source_type, limit),
                    ).fetchall()
                else:
                    rows = conn.execute(
                        """
                        SELECT source_type, source_id, rule_number, title,
                               snippet(legal_knowledge_fts, 4, '<b>', '</b>', '...', 40) AS snippet,
                               rank
                        FROM legal_knowledge_fts
                        WHERE legal_knowledge_fts MATCH ?
                        ORDER BY rank
                        LIMIT ?
                        """,
                        (query, limit),
                    ).fetchall()
                return [dict(r) for r in rows]
        except Exception:
            logger.exception("Legal knowledge search failed")
            return []

    # ------------------------------------------------------------------
    # Public API — Direct Lookups
    # ------------------------------------------------------------------

    def get_rule(self, rule_number: str) -> Optional[Dict[str, Any]]:
        """Get a specific MCR rule by number (e.g. ``'MCR 2.119'``)."""
        with self._connect() as conn:
            row = conn.execute(
                "SELECT * FROM michigan_court_rules WHERE rule_number = ?",
                (rule_number,),
            ).fetchone()
            return dict(row) if row else None

    def get_statute(self, statute_number: str) -> Optional[Dict[str, Any]]:
        """Get a specific MCL statute by number (e.g. ``'MCL 722.27a'``)."""
        with self._connect() as conn:
            row = conn.execute(
                "SELECT * FROM michigan_statutes WHERE statute_number = ?",
                (statute_number,),
            ).fetchone()
            return dict(row) if row else None

    def get_evidence_rule(self, rule_number: str) -> Optional[Dict[str, Any]]:
        """Get a specific MRE rule by number (e.g. ``'MRE 803'``)."""
        with self._connect() as conn:
            row = conn.execute(
                "SELECT * FROM michigan_evidence_rules WHERE rule_number = ?",
                (rule_number,),
            ).fetchone()
            return dict(row) if row else None

    def get_case(self, citation: str) -> Optional[Dict[str, Any]]:
        """Get a case by citation (e.g. ``'259 Mich App 499'``)."""
        with self._connect() as conn:
            row = conn.execute(
                "SELECT * FROM michigan_case_law WHERE citation = ?",
                (citation,),
            ).fetchone()
            if row:
                return dict(row)
            # Fall back to partial match
            row = conn.execute(
                "SELECT * FROM michigan_case_law WHERE citation LIKE ?",
                (f"%{citation}%",),
            ).fetchone()
            return dict(row) if row else None

    # ------------------------------------------------------------------
    # Public API — Cross-References
    # ------------------------------------------------------------------

    def get_cross_references(
        self, authority_type: str, authority_number: str
    ) -> List[Dict[str, Any]]:
        """Return all cross-references for a given authority.

        Finds authorities that are related to, reference, or are co-cited
        with the given authority in either direction.
        """
        with self._connect() as conn:
            if not self._table_exists(conn, "legal_cross_references"):
                return []
            rows = conn.execute(
                """
                SELECT * FROM legal_cross_references
                WHERE (source_type = ? AND source_number = ?)
                   OR (target_type = ? AND target_number = ?)
                ORDER BY relationship
                """,
                (authority_type, authority_number, authority_type, authority_number),
            ).fetchall()
            return [dict(r) for r in rows]

    def get_applicable_authorities(self, filing_id: str) -> Dict[str, List[Dict[str, Any]]]:
        """All authorities applicable to a filing, grouped by type.

        Returns:
            Dict with keys ``'MCR'``, ``'MCL'``, ``'MRE'``, ``'CASE'``
            each containing a list of enriched authority dicts.
        """
        result: Dict[str, List[Dict[str, Any]]] = {
            "MCR": [],
            "MCL": [],
            "MRE": [],
            "CASE": [],
        }
        with self._connect() as conn:
            if not self._table_exists(conn, "filing_rule_map"):
                return result

            mappings = conn.execute(
                "SELECT authority_type, authority_number, requirement, mandatory "
                "FROM filing_rule_map WHERE filing_id = ? ORDER BY authority_type",
                (filing_id,),
            ).fetchall()

            for m in mappings:
                auth_type: str = m[0]
                auth_num: str = m[1]
                entry: Dict[str, Any] = {
                    "authority_number": auth_num,
                    "requirement": m[2],
                    "mandatory": bool(m[3]),
                }

                # Enrich with full details from source table
                detail = self._lookup_detail(conn, auth_type, auth_num)
                if detail:
                    entry.update(detail)

                result.setdefault(auth_type, []).append(entry)

        return result

    def _lookup_detail(
        self, conn: sqlite3.Connection, auth_type: str, auth_num: str
    ) -> Optional[Dict[str, Any]]:
        """Fetch title / full_text / category for an authority."""
        table_map = {
            "MCR": ("michigan_court_rules", "rule_number"),
            "MCL": ("michigan_statutes", "statute_number"),
            "MRE": ("michigan_evidence_rules", "rule_number"),
        }
        spec = table_map.get(auth_type)
        if spec is None:
            return None
        table, col = spec
        if not self._table_exists(conn, table):
            return None
        row = conn.execute(
            f"SELECT title, full_text, category FROM {table} WHERE {col} = ?",
            (auth_num,),
        ).fetchone()
        if row:
            return {"title": row[0], "full_text": row[1], "category": row[2]}
        return None

    # ------------------------------------------------------------------
    # Public API — Stats
    # ------------------------------------------------------------------

    def get_stats(self) -> Dict[str, int]:
        """Return row counts for all legal knowledge tables."""
        with self._connect() as conn:
            stats: Dict[str, int] = {}
            for tbl, key in [
                ("michigan_court_rules", "mcr_rules"),
                ("michigan_statutes", "mcl_statutes"),
                ("michigan_evidence_rules", "mre_rules"),
                ("michigan_case_law", "case_law"),
                ("michigan_judicial_canons", "judicial_canons"),
                ("filing_rule_map", "filing_mappings"),
                ("legal_cross_references", "cross_references"),
                ("legal_knowledge_fts", "fts_entries"),
            ]:
                try:
                    if self._table_exists(conn, tbl):
                        stats[key] = conn.execute(f"SELECT COUNT(*) FROM {tbl}").fetchone()[0]
                    else:
                        stats[key] = 0
                except Exception:  # noqa: BLE001
                    stats[key] = 0
            return stats

    # ------------------------------------------------------------------
    # Public API — Jurisdiction DB Search
    # ------------------------------------------------------------------

    def search_jurisdiction_dbs(self, query: str) -> List[Dict[str, Any]]:
        """Search across all jurisdiction databases in ``databases/``.

        Performs LIKE-based search on text columns of every table in each
        jurisdiction ``.db`` file.  Returns matches with source DB and table.
        """
        results: List[Dict[str, Any]] = []
        if not _JURISDICTION_DBS.exists():
            return results

        _TEXT_COLUMNS = frozenset(
            ("title", "description", "full_text", "content", "rule_text", "holding", "notes")
        )

        for db_file in sorted(_JURISDICTION_DBS.glob("*.db")):
            try:
                conn = sqlite3.connect(str(db_file), timeout=10)
                conn.row_factory = sqlite3.Row
                conn.execute("PRAGMA busy_timeout = 10000")

                tables = [
                    r[0]
                    for r in conn.execute(
                        "SELECT name FROM sqlite_master WHERE type='table'"
                    ).fetchall()
                ]

                for tbl in tables:
                    try:
                        cols = [
                            c[1]
                            for c in conn.execute(f"PRAGMA table_info({tbl})").fetchall()
                        ]
                        text_cols = [c for c in cols if c in _TEXT_COLUMNS]
                        if not text_cols:
                            continue

                        where_clause = " OR ".join(f"{c} LIKE ?" for c in text_cols)
                        params = [f"%{query}%" for _ in text_cols]

                        rows = conn.execute(
                            f"SELECT * FROM {tbl} WHERE {where_clause} LIMIT 10",
                            params,
                        ).fetchall()

                        for row in rows:
                            results.append(
                                {
                                    "source_db": db_file.stem,
                                    "table": tbl,
                                    "data": dict(row),
                                }
                            )
                    except Exception:  # noqa: BLE001
                        continue

                conn.close()
            except Exception:  # noqa: BLE001
                continue

        return results
