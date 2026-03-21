"""Bridge between app GUI screens and litigation_context.db real tables.

The desktop app's screens expect app-schema tables (cases, evidence, filings),
but the real litigation database uses a different schema (evidence_quotes,
documents, judicial_violations, docket_events, etc.).  This bridge adapts
the real schema for GUI consumption without modifying either side.

Provides read-only access to real litigation data for GUI dashboards.
Falls back gracefully when the DB is unavailable or tables are missing.
"""

from __future__ import annotations

import logging
import os
import re
import sqlite3
from datetime import date, datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)

# Default path to the central litigation database
_DEFAULT_DB = Path(r"C:\Users\andre\LitigationOS\litigation_context.db")

# Tables we probe to confirm this is the real litigation DB
_SIGNATURE_TABLES = ("evidence_quotes", "documents", "judicial_violations", "docket_events")

# Base directory for filing packages on disk
_PKG_BASE = Path(r"C:\Users\andre\Desktop\LITIGATION_FILING_PACKAGE")

# Human-readable names for known packages
_PKG_NAMES: dict[str, str] = {
    "PKG_F1_EMERGENCY_TRO": "F01 — Emergency TRO",
    "PKG_F2_SHADY_OAKS_COMPLAINT": "F02 — Shady Oaks Complaint",
    "PKG_F3_DISQUALIFICATION_MCR_2003": "F03 — McNeill Disqualification (MCR 2.003)",
    "PKG_F4_FEDERAL_S1983_COMPLAINT": "F04 — Federal §1983 Complaint",
    "PKG_F5_MSC_ORIGINAL_ACTION": "F05 — MSC Original Action",
    "PKG_F6_JTC_COMPLAINT": "F06 — JTC Complaint",
    "PKG_F7_CUSTODY_MODIFICATION": "F07 — Custody Modification",
    "PKG_F8_PPO_TERMINATION": "F08 — PPO Termination",
    "PKG_F9_COA_BRIEF_ON_APPEAL": "F09 — COA Brief on Appeal",
    "PKG_F10_COA_EMERGENCY_MOTION": "F10 — COA Emergency Motion",
}


class LitigationBridge:
    """Read-only bridge to litigation_context.db for dashboard data."""

    def __init__(self, db_path: Optional[str | Path] = None):
        self._db_path = Path(db_path) if db_path else _DEFAULT_DB
        self._is_real = False
        self._has_evidence_fts = False
        self._probe()

    def _probe(self) -> None:
        """Check if the DB exists and contains real litigation tables."""
        if not self._db_path.exists():
            # Try the default if the given path is a small app DB
            if self._db_path != _DEFAULT_DB and _DEFAULT_DB.exists():
                self._db_path = _DEFAULT_DB
            else:
                return
        try:
            with self._connect() as conn:
                cur = conn.execute(
                    "SELECT name FROM sqlite_master WHERE type IN ('table','view')"
                )
                tables = {row[0] for row in cur.fetchall()}
                # Must have at least 3 of 4 signature tables
                hits = sum(1 for t in _SIGNATURE_TABLES if t in tables)
                self._is_real = hits >= 3
                self._has_evidence_fts = "evidence_fts" in tables
        except Exception:
            logger.debug("LitigationBridge probe failed for %s", self._db_path)

    @property
    def is_real_db(self) -> bool:
        return self._is_real

    def _connect(self) -> sqlite3.Connection:
        conn = sqlite3.connect(str(self._db_path), timeout=60)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA busy_timeout = 60000")
        conn.execute("PRAGMA journal_mode = WAL")
        conn.execute("PRAGMA cache_size = -32000")
        conn.execute("PRAGMA temp_store = MEMORY")
        conn.execute("PRAGMA synchronous = NORMAL")
        conn.execute("PRAGMA query_only = ON")
        return conn

    def _table_exists(self, conn: sqlite3.Connection, name: str) -> bool:
        row = conn.execute(
            "SELECT 1 FROM sqlite_master WHERE type='table' AND name=?", (name,)
        ).fetchone()
        return row is not None

    # ------------------------------------------------------------------
    # Dashboard stats
    # ------------------------------------------------------------------

    def get_dashboard_stats(self) -> dict[str, Any]:
        """Return aggregate counts for the main dashboard stat cards."""
        try:
            with self._connect() as conn:
                row = conn.execute("""
                    SELECT
                        (SELECT COUNT(*) FROM evidence_quotes) AS evidence_count,
                        (SELECT COUNT(*) FROM documents) AS document_count,
                        (SELECT COUNT(*) FROM judicial_violations) AS violation_count,
                        (SELECT COUNT(*) FROM docket_events) AS docket_count,
                        (SELECT COUNT(*) FROM file_inventory) AS file_count
                """).fetchone()
                # Deadline count (table may not exist yet)
                deadline_count = 0
                next_deadline_date = None
                if self._table_exists(conn, "deadlines"):
                    dl_row = conn.execute(
                        "SELECT COUNT(*) FROM deadlines WHERE status = 'pending'"
                    ).fetchone()
                    deadline_count = dl_row[0] if dl_row else 0
                    nxt = conn.execute(
                        "SELECT due_date FROM deadlines "
                        "WHERE status = 'pending' AND due_date >= date('now') "
                        "ORDER BY due_date ASC LIMIT 1"
                    ).fetchone()
                    if nxt:
                        next_deadline_date = nxt[0]

                return {
                    "evidence_count": row["evidence_count"],
                    "document_count": row["document_count"],
                    "violation_count": row["violation_count"],
                    "docket_count": row["docket_count"],
                    "file_count": row["file_count"],
                    "deadline_count": deadline_count,
                    "next_deadline_date": next_deadline_date,
                }
        except Exception:
            logger.debug("get_dashboard_stats failed", exc_info=True)
            return {}

    # ------------------------------------------------------------------
    # Lane summary
    # ------------------------------------------------------------------

    def get_lane_summary(self) -> List[Dict[str, Any]]:
        """Per-lane evidence, document, and violation counts."""
        if not self._is_real:
            return []
        try:
            with self._connect() as conn:
                lanes: Dict[str, Dict[str, Any]] = {}
                table_map = [
                    ("evidence_quotes", "evidence"),
                    ("documents", "documents"),
                    ("judicial_violations", "violations"),
                ]
                for table, key in table_map:
                    rows = conn.execute(
                        f"SELECT lane, COUNT(*) AS cnt FROM {table} "
                        f"WHERE lane IS NOT NULL AND lane != '' GROUP BY lane"
                    ).fetchall()
                    for r in rows:
                        lane = r["lane"] or "Unknown"
                        if lane not in lanes:
                            lanes[lane] = {
                                "lane": lane,
                                "evidence": 0,
                                "documents": 0,
                                "violations": 0,
                            }
                        lanes[lane][key] = r["cnt"]
                return sorted(
                    lanes.values(), key=lambda x: x["evidence"], reverse=True
                )
        except Exception:
            logger.debug("get_lane_summary failed", exc_info=True)
            return []

    # ------------------------------------------------------------------
    # Evidence per lane (for evidence panel)
    # ------------------------------------------------------------------

    def get_evidence_by_lane(self) -> dict[str, dict[str, Any]]:
        """Return {lane: {count, avg_score}} for evidence_quotes."""
        result: dict[str, dict[str, Any]] = {}
        try:
            with self._connect() as conn:
                rows = conn.execute("""
                    SELECT
                        UPPER(COALESCE(lane, 'C')) AS lane,
                        COUNT(*) AS count,
                        ROUND(AVG(CASE WHEN relevance_score IS NOT NULL
                                       THEN relevance_score ELSE NULL END), 1) AS avg_score
                    FROM evidence_quotes
                    GROUP BY UPPER(COALESCE(lane, 'C'))
                """).fetchall()
                for r in rows:
                    lane_key = r["lane"] if r["lane"] in ("A","B","C","D","E","F") else "C"
                    if lane_key in result:
                        result[lane_key]["count"] += r["count"]
                    else:
                        result[lane_key] = {
                            "count": r["count"],
                            "avg_score": r["avg_score"] or 0,
                        }
        except Exception:
            logger.debug("get_evidence_by_lane failed", exc_info=True)
        return result

    # ------------------------------------------------------------------
    # Judicial violations
    # ------------------------------------------------------------------

    def get_judicial_violations(
        self, lane: Optional[str] = None, limit: int = 200
    ) -> List[Dict[str, Any]]:
        """Judicial violations, highest severity first."""
        if not self._is_real:
            return []
        try:
            with self._connect() as conn:
                sql = (
                    "SELECT id, violation_type, description, date_occurred, "
                    "       mcr_rule, canon, severity, lane "
                    "FROM judicial_violations"
                )
                params: list[Any] = []
                if lane:
                    sql += " WHERE lane = ?"
                    params.append(lane)
                sql += f" ORDER BY severity DESC, date_occurred DESC LIMIT {int(limit)}"
                return [dict(r) for r in conn.execute(sql, params).fetchall()]
        except Exception:
            logger.debug("get_judicial_violations failed", exc_info=True)
            return []

    # ------------------------------------------------------------------
    # Docket events (with optional case filter)
    # ------------------------------------------------------------------

    def get_docket_events(
        self, case_number: Optional[str] = None, limit: int = 100
    ) -> List[Dict[str, Any]]:
        """Docket events, most recent first. Optionally filter by case."""
        if not self._is_real:
            return []
        try:
            with self._connect() as conn:
                sql = (
                    "SELECT id, case_number, event_date, event_type, "
                    "       description, filed_by "
                    "FROM docket_events"
                )
                params: list[Any] = []
                if case_number:
                    sql += " WHERE case_number = ?"
                    params.append(case_number)
                sql += f" ORDER BY event_date DESC LIMIT {int(limit)}"
                return [dict(r) for r in conn.execute(sql, params).fetchall()]
        except Exception:
            logger.debug("get_docket_events failed", exc_info=True)
            return []

    # ------------------------------------------------------------------
    # Recent documents
    # ------------------------------------------------------------------

    def get_recent_documents(self, limit: int = 20) -> List[Dict[str, Any]]:
        """Most recently ingested documents."""
        if not self._is_real:
            return []
        try:
            with self._connect() as conn:
                return [
                    dict(r)
                    for r in conn.execute(
                        "SELECT id, title, doc_type, lane, case_number, created_at "
                        "FROM documents ORDER BY created_at DESC LIMIT ?",
                        (limit,),
                    ).fetchall()
                ]
        except Exception:
            logger.debug("get_recent_documents failed", exc_info=True)
            return []

    # ------------------------------------------------------------------
    # Deadlines
    # ------------------------------------------------------------------

    def get_deadlines(self, status: str = "pending", limit: int = 20) -> list[dict[str, Any]]:
        """Return deadline rows from the deadlines table."""
        try:
            with self._connect() as conn:
                if not self._table_exists(conn, "deadlines"):
                    return []
                # Verify columns exist
                cols_info = conn.execute("PRAGMA table_info(deadlines)").fetchall()
                col_names = {c["name"] for c in cols_info}
                # Build SELECT with available columns
                select_cols = ["title", "due_date", "status"]
                for opt in ("court", "case_number", "urgency", "filing_id", "notes", "id"):
                    if opt in col_names:
                        select_cols.append(opt)
                # due_date column name might differ
                date_col = "due_date"
                if "due_date" not in col_names and "due_date_iso" in col_names:
                    date_col = "due_date_iso"
                    select_cols = [date_col if c == "due_date" else c for c in select_cols]

                sql = (
                    f"SELECT {', '.join(select_cols)} FROM deadlines "
                    f"WHERE status = ? ORDER BY {date_col} ASC LIMIT ?"
                )
                rows = conn.execute(sql, (status, limit)).fetchall()
                result = []
                for r in rows:
                    d = dict(r)
                    # Normalize date column name
                    if date_col != "due_date" and date_col in d:
                        d["due_date"] = d.pop(date_col)
                    result.append(d)
                return result
        except Exception:
            logger.debug("get_deadlines failed", exc_info=True)
            return []

    # ------------------------------------------------------------------
    # Docket events (recent activity)
    # ------------------------------------------------------------------

    def get_recent_docket_events(self, limit: int = 10) -> list[dict[str, Any]]:
        """Return recent docket events for the activity feed."""
        try:
            with self._connect() as conn:
                rows = conn.execute(
                    "SELECT case_number, event_date, event_type, description, filed_by "
                    "FROM docket_events ORDER BY event_date DESC LIMIT ?",
                    (limit,),
                ).fetchall()
                return [dict(r) for r in rows]
        except Exception:
            logger.debug("get_recent_docket_events failed", exc_info=True)
            return []

    # ------------------------------------------------------------------
    # Case lanes from docket_events
    # ------------------------------------------------------------------

    def get_active_cases(self) -> list[dict[str, Any]]:
        """Synthesize active case list from docket_events case_number values."""
        try:
            with self._connect() as conn:
                rows = conn.execute("""
                    SELECT
                        case_number,
                        COUNT(*) AS event_count,
                        MAX(event_date) AS last_activity
                    FROM docket_events
                    WHERE case_number IS NOT NULL AND case_number != ''
                    GROUP BY case_number
                    ORDER BY last_activity DESC
                """).fetchall()
                results = []
                for r in rows:
                    cn = r["case_number"] or ""
                    # Detect lane from case number
                    if "PP" in cn.upper():
                        lane, case_type = "D", "PPO"
                    elif "CZ" in cn.upper():
                        lane, case_type = "B", "Housing"
                    elif "DC" in cn.upper():
                        lane, case_type = "A", "Custody"
                    else:
                        lane, case_type = "C", "Convergence"
                    results.append({
                        "case_number": cn,
                        "lane": lane,
                        "case_type": case_type,
                        "event_count": r["event_count"],
                        "last_activity": r["last_activity"],
                        "status": "active",
                    })
                return results
        except Exception:
            logger.debug("get_active_cases failed", exc_info=True)
            return []

    # ------------------------------------------------------------------
    # Evidence search (for Evidence Browser screen)
    # ------------------------------------------------------------------

    def search_evidence(
        self,
        query: str = "",
        *,
        lane: Optional[str] = None,
        category: Optional[str] = None,
        limit: int = 200,
    ) -> list[dict[str, Any]]:
        """Search evidence_quotes, optionally via FTS5."""
        try:
            with self._connect() as conn:
                if not self._table_exists(conn, "evidence_quotes"):
                    return []
                params: list[Any] = []

                if query and self._has_evidence_fts:
                    safe_query = re.sub(r"[^\w\s]", "", query).strip()
                    if not safe_query:
                        return []
                    fts_terms = " OR ".join(f'"{w}"*' for w in safe_query.split())
                    sql = (
                        "SELECT eq.id, eq.source_file, eq.quote_text, eq.page_number,"
                        "       eq.category, eq.lane, eq.relevance_score, eq.filing_refs,"
                        "       eq.tags, eq.created_at "
                        "FROM evidence_fts ef "
                        "JOIN evidence_quotes eq ON eq.id = ef.rowid "
                        "WHERE evidence_fts MATCH ?"
                    )
                    params.append(fts_terms)
                elif query:
                    sql = (
                        "SELECT id, source_file, quote_text, page_number,"
                        "       category, lane, relevance_score, filing_refs,"
                        "       tags, created_at "
                        "FROM evidence_quotes "
                        "WHERE quote_text LIKE ? OR source_file LIKE ?"
                    )
                    like_pat = f"%{query}%"
                    params.extend([like_pat, like_pat])
                else:
                    sql = (
                        "SELECT id, source_file, quote_text, page_number,"
                        "       category, lane, relevance_score, filing_refs,"
                        "       tags, created_at "
                        "FROM evidence_quotes WHERE 1=1"
                    )

                if lane and lane != "All":
                    sql += " AND lane = ?"
                    params.append(lane)
                if category and category != "All":
                    sql += " AND category = ?"
                    params.append(category)

                sql += " ORDER BY relevance_score DESC LIMIT ?"
                params.append(limit)

                rows = conn.execute(sql, params).fetchall()
                return [
                    {
                        "id": r["id"],
                        "source_file": r["source_file"] or "",
                        "quote_text": r["quote_text"] or "",
                        "page_number": r["page_number"],
                        "category": r["category"] or "",
                        "lane": r["lane"] or "",
                        "relevance_score": r["relevance_score"],
                        "filing_refs": r["filing_refs"] or "",
                        "tags": r["tags"] or "",
                        "created_at": r["created_at"] or "",
                    }
                    for r in rows
                ]
        except Exception:
            logger.debug("search_evidence failed", exc_info=True)
            return []

    def get_evidence_categories(self) -> list[str]:
        """Return distinct category values from evidence_quotes."""
        try:
            with self._connect() as conn:
                if not self._table_exists(conn, "evidence_quotes"):
                    return []
                rows = conn.execute(
                    "SELECT DISTINCT category FROM evidence_quotes "
                    "WHERE category IS NOT NULL AND category != '' "
                    "ORDER BY category"
                ).fetchall()
                return [r[0] for r in rows]
        except Exception:
            return []

    def get_evidence_lanes(self) -> list[str]:
        """Return distinct lane values from evidence_quotes."""
        try:
            with self._connect() as conn:
                if not self._table_exists(conn, "evidence_quotes"):
                    return []
                rows = conn.execute(
                    "SELECT DISTINCT lane FROM evidence_quotes "
                    "WHERE lane IS NOT NULL AND lane != '' "
                    "ORDER BY lane"
                ).fetchall()
                return [r[0] for r in rows]
        except Exception:
            return []

    def get_evidence_count(self) -> int:
        """Total number of evidence_quotes rows."""
        try:
            with self._connect() as conn:
                if not self._table_exists(conn, "evidence_quotes"):
                    return 0
                row = conn.execute("SELECT COUNT(*) FROM evidence_quotes").fetchone()
                return row[0] if row else 0
        except Exception:
            return 0

    # ------------------------------------------------------------------
    # Filing packages (for Filing Manager screen)
    # ------------------------------------------------------------------

    def get_filing_packages(self) -> list[dict[str, Any]]:
        """Scan disk for filing packages and return metadata."""
        packages: list[dict[str, Any]] = []
        if not _PKG_BASE.exists():
            return packages
        for entry in sorted(_PKG_BASE.iterdir()):
            if not entry.is_dir() or not entry.name.startswith("PKG_F"):
                continue
            pkg = self._scan_package(entry)
            if pkg:
                packages.append(pkg)
        return packages

    def _scan_package(self, pkg_dir: Path) -> Optional[dict[str, Any]]:
        """Build metadata dict for a single filing package directory."""
        try:
            all_files = [f for f in pkg_dir.iterdir() if f.is_file()]
            file_names = [f.name for f in all_files]
            total_size = sum(f.stat().st_size for f in all_files)

            main_filing = pkg_dir / "01_MAIN_FILING.md"
            has_main = main_filing.exists()
            has_affidavit = any(n.startswith("02_AFFIDAVIT") for n in file_names)
            has_exhibits = any("EXHIBIT" in n.upper() for n in file_names)
            has_assembled = any(n.startswith("ASSEMBLED_") for n in file_names)

            if has_main and (has_affidavit or has_exhibits):
                status = "ready"
            elif has_main:
                status = "draft"
            else:
                status = "incomplete"

            title = _PKG_NAMES.get(pkg_dir.name, pkg_dir.name)
            if has_main:
                extracted = self._extract_title(main_filing)
                if extracted:
                    title = extracted

            return {
                "id": pkg_dir.name,
                "dir_path": str(pkg_dir),
                "title": title,
                "status": status,
                "file_count": len(file_names),
                "total_size": total_size,
                "total_size_str": _format_size(total_size),
                "has_main_filing": has_main,
                "has_affidavit": has_affidavit,
                "has_exhibits": has_exhibits,
                "has_assembled": has_assembled,
                "files": sorted(file_names),
            }
        except Exception as exc:
            logger.warning("Failed to scan package %s: %s", pkg_dir.name, exc)
            return None

    @staticmethod
    def _extract_title(main_filing: Path) -> Optional[str]:
        """Extract the first markdown heading from a filing."""
        try:
            with open(main_filing, "r", encoding="utf-8", errors="replace") as fh:
                for line in fh:
                    stripped = line.strip()
                    if stripped.startswith("# "):
                        return stripped[2:].strip()[:120]
                    if fh.tell() > 4096:
                        break
        except Exception:
            pass
        return None


    # ------------------------------------------------------------------
    # Legal Knowledge — MCR, MCL, MRE, Case Law
    # ------------------------------------------------------------------

    def search_legal_knowledge(
        self,
        query: str,
        *,
        source_type: Optional[str] = None,
        limit: int = 25,
    ) -> List[Dict[str, Any]]:
        """Full-text search across ALL legal knowledge via FTS5.

        Searches michigan_court_rules, michigan_statutes,
        michigan_evidence_rules, and michigan_case_law through the
        unified legal_knowledge_fts index.

        Args:
            query: Search terms (FTS5 syntax: AND, OR, NOT, phrases).
            source_type: Filter — ``'MCR'``, ``'MCL'``, ``'MRE'``, ``'CASE'``.
            limit: Max results.
        """
        if not self._is_real:
            return []
        try:
            with self._connect() as conn:
                if not self._table_exists(conn, "legal_knowledge_fts"):
                    return self._fallback_legal_search(conn, query, limit)

                params: list[Any] = [query]
                type_clause = ""
                if source_type:
                    type_clause = "AND source_type = ?"
                    params.append(source_type)
                params.append(limit)

                rows = conn.execute(
                    f"""
                    SELECT source_type, source_id, rule_number, title,
                           snippet(legal_knowledge_fts, 4, '**', '**', '...', 40) AS snippet,
                           rank
                    FROM legal_knowledge_fts
                    WHERE legal_knowledge_fts MATCH ?
                    {type_clause}
                    ORDER BY rank
                    LIMIT ?
                    """,
                    params,
                ).fetchall()
                return [dict(r) for r in rows]
        except Exception:
            logger.debug("search_legal_knowledge failed", exc_info=True)
            return []

    def _fallback_legal_search(
        self, conn: sqlite3.Connection, query: str, limit: int
    ) -> List[Dict[str, Any]]:
        """LIKE-based fallback when FTS5 table doesn't exist yet."""
        results: List[Dict[str, Any]] = []
        pattern = f"%{query}%"
        table_map = [
            ("michigan_court_rules", "MCR", "rule_number"),
            ("michigan_statutes", "MCL", "statute_number"),
            ("michigan_evidence_rules", "MRE", "rule_number"),
        ]
        for tbl, stype, num_col in table_map:
            if not self._table_exists(conn, tbl):
                continue
            rows = conn.execute(
                f"SELECT {num_col} AS rule_number, title, full_text "
                f"FROM {tbl} WHERE title LIKE ? OR full_text LIKE ? LIMIT ?",
                (pattern, pattern, limit),
            ).fetchall()
            for r in rows:
                results.append({
                    "source_type": stype,
                    "rule_number": r["rule_number"],
                    "title": r["title"],
                    "snippet": (r["full_text"] or "")[:200],
                })
        # Case law
        if self._table_exists(conn, "michigan_case_law"):
            rows = conn.execute(
                "SELECT citation AS rule_number, case_name AS title, holding "
                "FROM michigan_case_law WHERE case_name LIKE ? OR holding LIKE ? LIMIT ?",
                (pattern, pattern, limit),
            ).fetchall()
            for r in rows:
                results.append({
                    "source_type": "CASE",
                    "rule_number": r["rule_number"],
                    "title": r["title"],
                    "snippet": (r["holding"] or "")[:200],
                })
        return results[:limit]

    def get_court_rule(self, rule_number: str) -> Optional[Dict[str, Any]]:
        """Get a specific MCR rule by number (e.g. ``'MCR 2.119'``)."""
        if not self._is_real:
            return None
        try:
            with self._connect() as conn:
                if not self._table_exists(conn, "michigan_court_rules"):
                    return None
                row = conn.execute(
                    "SELECT * FROM michigan_court_rules WHERE rule_number = ?",
                    (rule_number,),
                ).fetchone()
                return dict(row) if row else None
        except Exception:
            return None

    def get_statute(self, statute_number: str) -> Optional[Dict[str, Any]]:
        """Get a specific MCL statute (e.g. ``'MCL 722.27a'``)."""
        if not self._is_real:
            return None
        try:
            with self._connect() as conn:
                if not self._table_exists(conn, "michigan_statutes"):
                    return None
                row = conn.execute(
                    "SELECT * FROM michigan_statutes WHERE statute_number = ?",
                    (statute_number,),
                ).fetchone()
                return dict(row) if row else None
        except Exception:
            return None

    def get_evidence_rule(self, rule_number: str) -> Optional[Dict[str, Any]]:
        """Get a specific MRE rule (e.g. ``'MRE 803'``)."""
        if not self._is_real:
            return None
        try:
            with self._connect() as conn:
                if not self._table_exists(conn, "michigan_evidence_rules"):
                    return None
                row = conn.execute(
                    "SELECT * FROM michigan_evidence_rules WHERE rule_number = ?",
                    (rule_number,),
                ).fetchone()
                return dict(row) if row else None
        except Exception:
            return None

    def get_case_law(self, citation: str) -> Optional[Dict[str, Any]]:
        """Get a case by citation (e.g. ``'259 Mich App 499'``)."""
        if not self._is_real:
            return None
        try:
            with self._connect() as conn:
                if not self._table_exists(conn, "michigan_case_law"):
                    return None
                row = conn.execute(
                    "SELECT * FROM michigan_case_law WHERE citation LIKE ?",
                    (f"%{citation}%",),
                ).fetchone()
                return dict(row) if row else None
        except Exception:
            return None

    def get_legal_knowledge_stats(self) -> Dict[str, int]:
        """Return counts of all legal knowledge tables."""
        if not self._is_real:
            return {}
        try:
            with self._connect() as conn:
                stats = {}
                tables = [
                    ("michigan_court_rules", "mcr_rules"),
                    ("michigan_statutes", "mcl_statutes"),
                    ("michigan_evidence_rules", "mre_rules"),
                    ("michigan_case_law", "case_law"),
                    ("michigan_judicial_canons", "judicial_canons"),
                    ("filing_rule_map", "filing_mappings"),
                    ("legal_cross_references", "cross_references"),
                    ("legal_knowledge_fts", "fts_entries"),
                ]
                for tbl, key in tables:
                    if self._table_exists(conn, tbl):
                        cnt = conn.execute(
                            f"SELECT COUNT(*) FROM {tbl}"
                        ).fetchone()[0]
                        stats[key] = cnt
                    else:
                        stats[key] = 0
                return stats
        except Exception:
            return {}

    def get_cross_references(
        self, authority_type: str, authority_number: str
    ) -> List[Dict[str, Any]]:
        """Get cross-references for an authority (co-cited, references)."""
        if not self._is_real:
            return []
        try:
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
                    (authority_type, authority_number,
                     authority_type, authority_number),
                ).fetchall()
                return [dict(r) for r in rows]
        except Exception:
            return []

    def get_filing_authorities(self, filing_id: str) -> Dict[str, List[Dict]]:
        """Get all authorities for a filing, grouped by type."""
        result: Dict[str, List[Dict]] = {"MCR": [], "MCL": [], "MRE": []}
        if not self._is_real:
            return result
        try:
            with self._connect() as conn:
                if not self._table_exists(conn, "filing_rule_map"):
                    return result
                rows = conn.execute(
                    "SELECT authority_type, authority_number, requirement, mandatory "
                    "FROM filing_rule_map WHERE filing_id = ? "
                    "ORDER BY authority_type",
                    (filing_id,),
                ).fetchall()
                for r in rows:
                    entry = {
                        "authority_number": r["authority_number"],
                        "requirement": r["requirement"],
                        "mandatory": bool(r["mandatory"]),
                    }
                    atype = r["authority_type"]
                    result.setdefault(atype, []).append(entry)
                return result
        except Exception:
            return result


    def get_legal_coverage_stats(self) -> Dict[str, Any]:
        """Return counts and coverage metrics for the legal knowledge base."""
        result: Dict[str, Any] = {"mcr": 0, "mcl": 0, "mre": 0, "cases": 0,
                                   "canons": 0, "cross_refs": 0, "fts5": 0,
                                   "local_rules": 0, "categories": {}}
        try:
            with self._connect() as conn:
                row = conn.execute("""
                    SELECT
                        (SELECT COUNT(*) FROM michigan_court_rules) AS mcr,
                        (SELECT COUNT(*) FROM michigan_statutes) AS mcl,
                        (SELECT COUNT(*) FROM michigan_evidence_rules) AS mre,
                        (SELECT COUNT(*) FROM michigan_case_law) AS cases,
                        (SELECT COUNT(*) FROM michigan_judicial_canons) AS canons,
                        (SELECT COUNT(*) FROM legal_cross_references) AS xrefs,
                        (SELECT COUNT(*) FROM legal_knowledge_fts) AS fts5,
                        (SELECT COUNT(*) FROM michigan_court_rules
                         WHERE doc_type = 'LCR') AS lcr
                """).fetchone()
                result.update({
                    "mcr": row["mcr"], "mcl": row["mcl"], "mre": row["mre"],
                    "cases": row["cases"], "canons": row["canons"],
                    "cross_refs": row["xrefs"], "fts5": row["fts5"],
                    "local_rules": row["lcr"],
                    "total": row["mcr"] + row["mcl"] + row["mre"] + row["cases"] + row["canons"],
                })
                # Category breakdown for MCR
                for r in conn.execute(
                    "SELECT category, COUNT(*) AS cnt FROM michigan_court_rules "
                    "GROUP BY category ORDER BY cnt DESC"
                ).fetchall():
                    result["categories"][r["category"]] = r["cnt"]
        except Exception:
            pass
        return result


def _format_size(nbytes: int) -> str:
    """Format byte count as human-readable string."""
    if nbytes < 1024:
        return f"{nbytes} B"
    if nbytes < 1024 * 1024:
        return f"{nbytes / 1024:.1f} KB"
    return f"{nbytes / (1024 * 1024):.1f} MB"
