"""MCP server bridge engine.

Wraps MCP server tool functionality so the LitigationOS desktop GUI can
invoke litigation-context tools (search, deadlines, evidence, filings,
quality checks) as plain Python calls — no running MCP server required.

Each public method mirrors an MCP tool endpoint but queries the central
``litigation_context.db`` directly.  Methods degrade gracefully when
tables are missing (empty results, never exceptions).
"""

from __future__ import annotations

import logging
import os
import sqlite3
from datetime import date, datetime, timedelta
from pathlib import Path
from typing import TYPE_CHECKING, Any, Optional

if TYPE_CHECKING:
    from litigationos.db.connection import DatabaseManager

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

_DEFAULT_DB = Path(
    os.environ.get(
        "LITIGATIONOS_DB",
        r"C:\Users\andre\LitigationOS\litigation_context.db",
    )
)

_PRAGMAS: tuple[str, ...] = (
    "PRAGMA busy_timeout = 60000",
    "PRAGMA journal_mode = WAL",
    "PRAGMA cache_size  = -32000",
    "PRAGMA temp_store  = MEMORY",
    "PRAGMA synchronous = NORMAL",
)

# Urgency thresholds (days until due date)
_URGENCY_CRITICAL = 3
_URGENCY_HIGH = 7
_URGENCY_MEDIUM = 14

# Pre-filing QA check names
_QA_CHECKS: tuple[str, ...] = (
    "filing_exists",
    "title_present",
    "filing_type_set",
    "evidence_attached",
    "authorities_cited",
    "word_count_ok",
    "compliance_score_ok",
    "served_date_set",
    "file_path_valid",
    "no_placeholder_text",
)

# Contradiction / impeachment signal words
_CONTRADICTION_SIGNALS: tuple[str, ...] = (
    "contradict",
    "inconsisten",
    "false",
    "lied",
    "denied",
    "changed story",
    "prior statement",
    "sworn testimony",
    "perjur",
    "misrepresent",
)

_IMPEACHMENT_SIGNALS: tuple[str, ...] = (
    "impeach",
    "credibility",
    "bias",
    "motive",
    "prior conviction",
    "inconsisten",
    "false statement",
    "lie",
    "untruthful",
    "perjur",
)


# ---------------------------------------------------------------------------
# Engine
# ---------------------------------------------------------------------------


class MCPBridge:
    """Bridge between the LitigationOS GUI and MCP server tools.

    Provides the same tool surface as the ``litigation-context-mcp`` server
    but executes entirely in-process via direct SQLite queries against
    ``litigation_context.db``.

    Parameters
    ----------
    db:
        Optional :class:`DatabaseManager` instance.  When ``None`` the
        bridge opens its own connection to the default litigation database.
    """

    def __init__(self, db: Optional["DatabaseManager"] = None) -> None:
        self._db = db
        self._db_path = _DEFAULT_DB
        self._table_cache: dict[str, list[str]] = {}
        logger.debug(
            "MCPBridge initialised (db_manager=%s, db_path=%s)",
            db is not None,
            self._db_path,
        )

    # ------------------------------------------------------------------
    # Connection helpers
    # ------------------------------------------------------------------

    def _connect(self) -> sqlite3.Connection:
        """Return a connection with standard PRAGMAs applied.

        Uses the injected :class:`DatabaseManager` when available,
        otherwise opens a direct connection.
        """
        if self._db is not None:
            return self._db.connect()

        conn = sqlite3.connect(str(self._db_path), timeout=120)
        for pragma in _PRAGMAS:
            conn.execute(pragma)
        conn.row_factory = sqlite3.Row
        return conn

    def _table_exists(self, conn: sqlite3.Connection, table: str) -> bool:
        """Check whether *table* exists in the database."""
        row = conn.execute(
            "SELECT 1 FROM sqlite_master WHERE type='table' AND name = ?",
            (table,),
        ).fetchone()
        return row is not None

    def _get_columns(self, conn: sqlite3.Connection, table: str) -> list[str]:
        """Return column names for *table*, caching the result."""
        if table in self._table_cache:
            return self._table_cache[table]
        rows = conn.execute(f"PRAGMA table_info([{table}])").fetchall()
        cols = [r[1] for r in rows]
        if cols:
            self._table_cache[table] = cols
        return cols

    def _safe_fetchall(
        self,
        conn: sqlite3.Connection,
        sql: str,
        params: tuple[Any, ...] = (),
    ) -> list[dict]:
        """Execute *sql* and return a list of dicts.  Returns ``[]`` on error."""
        try:
            rows = conn.execute(sql, params).fetchall()
            return [dict(r) for r in rows]
        except sqlite3.Error as exc:
            logger.warning("Query failed (%s): %s", exc, sql[:120])
            return []

    def _safe_fetchone(
        self,
        conn: sqlite3.Connection,
        sql: str,
        params: tuple[Any, ...] = (),
    ) -> Optional[dict]:
        """Execute *sql* and return a single dict or ``None``."""
        try:
            row = conn.execute(sql, params).fetchone()
            return dict(row) if row else None
        except sqlite3.Error as exc:
            logger.warning("Query failed (%s): %s", exc, sql[:120])
            return None

    # ------------------------------------------------------------------
    # 1. search
    # ------------------------------------------------------------------

    def search(self, query: str, limit: int = 20) -> list[dict]:
        """Full-text search across documents and evidence.

        Attempts FTS5 first (``evidence_fts``), then falls back to LIKE
        searches on ``documents`` and ``evidence_quotes``.

        Args:
            query: Search terms.
            limit: Maximum results to return.

        Returns:
            List of ``{"source", "id", "title", "snippet", "score"}`` dicts.
        """
        if not query or not query.strip():
            return []

        results: list[dict] = []
        conn = self._connect()
        try:
            # --- FTS5 on evidence_fts ---
            if self._table_exists(conn, "evidence_fts"):
                fts_sql = (
                    "SELECT rowid, quote_text, category, source_file, "
                    "       rank "
                    "FROM evidence_fts "
                    "WHERE evidence_fts MATCH ? "
                    "ORDER BY rank "
                    "LIMIT ?"
                )
                try:
                    rows = conn.execute(fts_sql, (query, limit)).fetchall()
                    for r in rows:
                        results.append({
                            "source": "evidence_quotes",
                            "id": r["rowid"],
                            "title": (r["source_file"] or "")[:120],
                            "snippet": (r["quote_text"] or "")[:300],
                            "category": r["category"],
                            "score": r["rank"],
                        })
                except sqlite3.OperationalError:
                    logger.debug("FTS5 MATCH failed, falling back to LIKE")

            # --- LIKE search on documents ---
            remaining = limit - len(results)
            if remaining > 0 and self._table_exists(conn, "documents"):
                cols = self._get_columns(conn, "documents")
                title_col = "title" if "title" in cols else None
                preview_col = (
                    "content_preview" if "content_preview" in cols else None
                )
                if title_col or preview_col:
                    where_parts: list[str] = []
                    if title_col:
                        where_parts.append(f"{title_col} LIKE ?")
                    if preview_col:
                        where_parts.append(f"{preview_col} LIKE ?")
                    where_clause = " OR ".join(where_parts)

                    like_param = f"%{query}%"
                    params = tuple(
                        like_param for _ in where_parts
                    )
                    doc_sql = (
                        f"SELECT id, title, content_preview, doc_type, lane "
                        f"FROM documents WHERE {where_clause} "
                        f"LIMIT ?"
                    )
                    doc_rows = self._safe_fetchall(
                        conn, doc_sql, (*params, remaining)
                    )
                    for d in doc_rows:
                        results.append({
                            "source": "documents",
                            "id": d.get("id"),
                            "title": (d.get("title") or "")[:120],
                            "snippet": (d.get("content_preview") or "")[:300],
                            "category": d.get("doc_type"),
                            "score": None,
                        })

            logger.info("search(%r) → %d results", query, len(results))
        finally:
            conn.close()
        return results

    # ------------------------------------------------------------------
    # 2. get_stats
    # ------------------------------------------------------------------

    def get_stats(self) -> dict:
        """Return consolidated database statistics.

        Uses a single compound query for efficiency.

        Returns:
            ``{"table_count", "document_count", "evidence_quote_count",
              "deadline_count", "filing_count", "claim_count",
              "judicial_violation_count", "docket_event_count",
              "filing_rule_count", "db_size_mb"}``
        """
        conn = self._connect()
        try:
            # Table count
            table_count = conn.execute(
                "SELECT COUNT(*) FROM sqlite_master WHERE type='table'"
            ).fetchone()[0]

            # Build consolidated count query for tables that exist
            count_parts: dict[str, str] = {
                "document_count": "documents",
                "evidence_quote_count": "evidence_quotes",
                "deadline_count": "deadlines",
                "filing_count": "filings",
                "claim_count": "claims",
                "judicial_violation_count": "judicial_violations",
                "docket_event_count": "docket_events",
                "filing_rule_count": "filing_rule_map",
            }

            subqueries: list[str] = []
            for alias, table in count_parts.items():
                if self._table_exists(conn, table):
                    subqueries.append(
                        f"(SELECT COUNT(*) FROM [{table}]) AS {alias}"
                    )
                else:
                    subqueries.append(f"0 AS {alias}")

            row = conn.execute(
                f"SELECT {', '.join(subqueries)}"
            ).fetchone()

            stats: dict[str, Any] = {"table_count": table_count}
            for i, alias in enumerate(count_parts):
                stats[alias] = row[i]

            # DB file size
            try:
                stats["db_size_mb"] = round(
                    os.path.getsize(self._db_path) / (1024 * 1024), 1
                )
            except OSError:
                stats["db_size_mb"] = None

            logger.info("get_stats() → %d tables", table_count)
            return stats
        finally:
            conn.close()

    # ------------------------------------------------------------------
    # 3. upcoming_deadlines
    # ------------------------------------------------------------------

    def upcoming_deadlines(self, days: int = 30) -> list[dict]:
        """Return deadlines due within the next *days* calendar days.

        Args:
            days: Look-ahead window.

        Returns:
            List of deadline dicts sorted by ``due_date`` ascending.
        """
        conn = self._connect()
        try:
            if not self._table_exists(conn, "deadlines"):
                return []

            cols = self._get_columns(conn, "deadlines")
            due_col = "due_date" if "due_date" in cols else None
            if due_col is None:
                logger.warning("deadlines table has no due_date column")
                return []

            status_filter = (
                "AND status = 'pending'" if "status" in cols else ""
            )

            sql = (
                f"SELECT * FROM deadlines "
                f"WHERE {due_col} >= date('now') "
                f"  AND {due_col} <= date('now', '+' || ? || ' days') "
                f"  {status_filter} "
                f"ORDER BY {due_col} ASC"
            )
            rows = self._safe_fetchall(conn, sql, (days,))
            logger.info("upcoming_deadlines(%d) → %d results", days, len(rows))
            return rows
        finally:
            conn.close()

    # ------------------------------------------------------------------
    # 4. filing_readiness
    # ------------------------------------------------------------------

    def filing_readiness(self, filing_id: str) -> dict:
        """Assess readiness of a filing for court submission.

        Checks the ``filings`` table, related ``filing_rule_map``
        entries, and linked evidence.

        Args:
            filing_id: Identifier of the filing to check.

        Returns:
            ``{"filing_id", "found", "title", "status",
              "rules_total", "rules_satisfied", "readiness_pct",
              "evidence_linked", "issues"}``
        """
        result: dict[str, Any] = {
            "filing_id": filing_id,
            "found": False,
            "title": None,
            "status": None,
            "rules_total": 0,
            "rules_satisfied": 0,
            "readiness_pct": 0.0,
            "evidence_linked": 0,
            "issues": [],
        }

        conn = self._connect()
        try:
            # --- Filing record ---
            if self._table_exists(conn, "filings"):
                cols = self._get_columns(conn, "filings")
                id_col = "id" if "id" in cols else None
                if id_col:
                    filing = self._safe_fetchone(
                        conn,
                        f"SELECT * FROM filings WHERE {id_col} = ?",
                        (filing_id,),
                    )
                    if filing:
                        result["found"] = True
                        result["title"] = filing.get("title")
                        result["status"] = filing.get("status")

                        if not filing.get("file_path"):
                            result["issues"].append(
                                "No file path — filing document not generated."
                            )
                        score = filing.get("compliance_score")
                        if score is not None and score < 80:
                            result["issues"].append(
                                f"Low compliance score ({score}/100)."
                            )

            # --- Rules / authorities ---
            if self._table_exists(conn, "filing_rule_map"):
                rules = self._safe_fetchall(
                    conn,
                    "SELECT * FROM filing_rule_map WHERE filing_id = ?",
                    (filing_id,),
                )
                result["rules_total"] = len(rules)
                satisfied = sum(
                    1 for r in rules if r.get("mandatory") == 0
                    or r.get("requirement")
                )
                result["rules_satisfied"] = satisfied
                if result["rules_total"] > 0:
                    result["readiness_pct"] = round(
                        satisfied / result["rules_total"] * 100, 1
                    )
                mandatory_missing = [
                    r for r in rules
                    if r.get("mandatory") == 1 and not r.get("requirement")
                ]
                for mm in mandatory_missing:
                    result["issues"].append(
                        f"Missing mandatory authority: "
                        f"{mm.get('authority_type')} {mm.get('authority_number')}"
                    )

            # --- Evidence linkage ---
            if self._table_exists(conn, "evidence_quotes"):
                eq_count = conn.execute(
                    "SELECT COUNT(*) FROM evidence_quotes "
                    "WHERE filing_refs LIKE ?",
                    (f"%{filing_id}%",),
                ).fetchone()[0]
                result["evidence_linked"] = eq_count
                if eq_count == 0:
                    result["issues"].append(
                        "No evidence quotes linked to this filing."
                    )

            if not result["found"]:
                result["issues"].append(
                    "Filing not found in the filings table."
                )

            logger.info(
                "filing_readiness(%s) → ready=%.1f%%",
                filing_id,
                result["readiness_pct"],
            )
            return result
        finally:
            conn.close()

    # ------------------------------------------------------------------
    # 5. evidence_chain
    # ------------------------------------------------------------------

    def evidence_chain(self, claim_type: str) -> list[dict]:
        """Return the evidence chain supporting a claim type.

        Searches ``evidence_quotes`` by category and returns items
        ordered by relevance score.

        Args:
            claim_type: Category / claim type to filter (e.g. ``"custody"``).

        Returns:
            List of evidence quote dicts.
        """
        conn = self._connect()
        try:
            if not self._table_exists(conn, "evidence_quotes"):
                return []

            cols = self._get_columns(conn, "evidence_quotes")
            cat_col = "category" if "category" in cols else None
            score_col = "relevance_score" if "relevance_score" in cols else None

            if cat_col is None:
                logger.warning("evidence_quotes has no category column")
                return []

            order = f"ORDER BY {score_col} DESC" if score_col else ""
            sql = (
                f"SELECT * FROM evidence_quotes "
                f"WHERE {cat_col} LIKE ? "
                f"{order} "
                f"LIMIT 100"
            )
            rows = self._safe_fetchall(conn, sql, (f"%{claim_type}%",))
            logger.info(
                "evidence_chain(%r) → %d quotes", claim_type, len(rows)
            )
            return rows
        finally:
            conn.close()

    # ------------------------------------------------------------------
    # 6. evidence_gaps
    # ------------------------------------------------------------------

    def evidence_gaps(self, vehicle_name: str) -> list[dict]:
        """Identify gaps in evidence coverage for a case lane.

        Cross-references ``claims`` against ``evidence_quotes`` for
        the given vehicle/lane and reports claims without supporting
        evidence.

        Args:
            vehicle_name: The case lane or vehicle name to analyse.

        Returns:
            List of ``{"claim_id", "claim_type", "description", "gap"}``
            dicts for claims lacking evidence.
        """
        gaps: list[dict] = []
        conn = self._connect()
        try:
            # --- Gather claims for this lane ---
            claims_rows: list[dict] = []
            if self._table_exists(conn, "claims"):
                cols = self._get_columns(conn, "claims")
                lane_col = "lane" if "lane" in cols else None
                if lane_col:
                    claims_rows = self._safe_fetchall(
                        conn,
                        f"SELECT * FROM claims WHERE {lane_col} LIKE ?",
                        (f"%{vehicle_name}%",),
                    )

            if not claims_rows:
                logger.info(
                    "evidence_gaps(%r) → no claims found", vehicle_name
                )
                return []

            # --- Gather evidence for this lane ---
            eq_text = ""
            if self._table_exists(conn, "evidence_quotes"):
                eq_rows = self._safe_fetchall(
                    conn,
                    "SELECT quote_text, category FROM evidence_quotes "
                    "WHERE lane LIKE ?",
                    (f"%{vehicle_name}%",),
                )
                eq_text = " ".join(
                    (r.get("quote_text") or "") + " " + (r.get("category") or "")
                    for r in eq_rows
                ).lower()

            # --- Identify gaps ---
            for claim in claims_rows:
                desc = (claim.get("description") or "").lower()
                ctype = (claim.get("claim_type") or "").lower()
                keywords = [
                    w for w in (desc + " " + ctype).split() if len(w) > 3
                ]
                has_match = any(kw in eq_text for kw in keywords)
                if not has_match:
                    gaps.append({
                        "claim_id": claim.get("claim_id") or claim.get("id"),
                        "claim_type": claim.get("claim_type"),
                        "description": claim.get("description"),
                        "gap": "No supporting evidence found for this claim.",
                    })

            logger.info(
                "evidence_gaps(%r) → %d gaps out of %d claims",
                vehicle_name,
                len(gaps),
                len(claims_rows),
            )
            return gaps
        finally:
            conn.close()

    # ------------------------------------------------------------------
    # 7. deadline_dashboard
    # ------------------------------------------------------------------

    def deadline_dashboard(self) -> dict:
        """Build a full deadline overview with urgency scoring.

        Returns:
            ``{"overdue", "critical", "high", "medium", "low",
              "total", "summary"}`` — each category is a list of
            deadline dicts augmented with ``days_remaining`` and
            ``urgency``.
        """
        dashboard: dict[str, Any] = {
            "overdue": [],
            "critical": [],
            "high": [],
            "medium": [],
            "low": [],
            "total": 0,
            "summary": "",
        }

        conn = self._connect()
        try:
            if not self._table_exists(conn, "deadlines"):
                dashboard["summary"] = "No deadlines table found."
                return dashboard

            cols = self._get_columns(conn, "deadlines")
            due_col = "due_date" if "due_date" in cols else None
            if not due_col:
                dashboard["summary"] = "deadlines table has no due_date column."
                return dashboard

            rows = self._safe_fetchall(
                conn,
                f"SELECT * FROM deadlines ORDER BY {due_col} ASC",
            )
            today = date.today()

            for row in rows:
                raw_due = row.get(due_col)
                if not raw_due:
                    continue
                try:
                    due_date = date.fromisoformat(str(raw_due)[:10])
                except ValueError:
                    continue

                days_remaining = (due_date - today).days
                entry = {**row, "days_remaining": days_remaining}

                if days_remaining < 0:
                    entry["urgency"] = "overdue"
                    dashboard["overdue"].append(entry)
                elif days_remaining <= _URGENCY_CRITICAL:
                    entry["urgency"] = "critical"
                    dashboard["critical"].append(entry)
                elif days_remaining <= _URGENCY_HIGH:
                    entry["urgency"] = "high"
                    dashboard["high"].append(entry)
                elif days_remaining <= _URGENCY_MEDIUM:
                    entry["urgency"] = "medium"
                    dashboard["medium"].append(entry)
                else:
                    entry["urgency"] = "low"
                    dashboard["low"].append(entry)

            dashboard["total"] = len(rows)
            counts = (
                f"{len(dashboard['overdue'])} overdue, "
                f"{len(dashboard['critical'])} critical, "
                f"{len(dashboard['high'])} high, "
                f"{len(dashboard['medium'])} medium, "
                f"{len(dashboard['low'])} low"
            )
            dashboard["summary"] = (
                f"{len(rows)} total deadlines: {counts}"
            )

            logger.info("deadline_dashboard() → %s", dashboard["summary"])
            return dashboard
        finally:
            conn.close()

    # ------------------------------------------------------------------
    # 8. prefiling_qa
    # ------------------------------------------------------------------

    def prefiling_qa(self, filing_id: str) -> dict:
        """Run pre-filing quality assurance checks.

        Performs 10+ checks against the filing and its related records
        and returns a GO / NO-GO recommendation.

        Args:
            filing_id: Identifier of the filing to check.

        Returns:
            ``{"filing_id", "checks", "passed", "failed",
              "score_pct", "go_no_go"}``
        """
        checks: list[dict] = []
        conn = self._connect()
        try:
            filing: Optional[dict] = None

            # --- Load filing ---
            if self._table_exists(conn, "filings"):
                filing = self._safe_fetchone(
                    conn,
                    "SELECT * FROM filings WHERE id = ?",
                    (filing_id,),
                )

            # 1. Filing exists
            checks.append({
                "check": "filing_exists",
                "passed": filing is not None,
                "detail": "Filing record found." if filing else "Filing not found.",
            })

            if filing is None:
                filing = {}

            # 2. Title present
            has_title = bool(filing.get("title"))
            checks.append({
                "check": "title_present",
                "passed": has_title,
                "detail": filing.get("title", "No title."),
            })

            # 3. Filing type set
            has_type = bool(filing.get("filing_type"))
            checks.append({
                "check": "filing_type_set",
                "passed": has_type,
                "detail": filing.get("filing_type", "No filing type."),
            })

            # 4. Evidence attached
            ev_count = 0
            if self._table_exists(conn, "evidence_quotes"):
                row = conn.execute(
                    "SELECT COUNT(*) FROM evidence_quotes "
                    "WHERE filing_refs LIKE ?",
                    (f"%{filing_id}%",),
                ).fetchone()
                ev_count = row[0] if row else 0
            checks.append({
                "check": "evidence_attached",
                "passed": ev_count > 0,
                "detail": f"{ev_count} evidence quotes linked.",
            })

            # 5. Authorities cited
            rule_count = 0
            if self._table_exists(conn, "filing_rule_map"):
                row = conn.execute(
                    "SELECT COUNT(*) FROM filing_rule_map WHERE filing_id = ?",
                    (filing_id,),
                ).fetchone()
                rule_count = row[0] if row else 0
            checks.append({
                "check": "authorities_cited",
                "passed": rule_count > 0,
                "detail": f"{rule_count} authority citations.",
            })

            # 6. Word count acceptable
            wc = filing.get("word_count") or 0
            checks.append({
                "check": "word_count_ok",
                "passed": 100 <= wc <= 50_000 if wc else False,
                "detail": f"Word count: {wc}.",
            })

            # 7. Compliance score
            score = filing.get("compliance_score")
            checks.append({
                "check": "compliance_score_ok",
                "passed": (score or 0) >= 80,
                "detail": f"Compliance score: {score}." if score else "No score.",
            })

            # 8. Served date
            has_served = bool(filing.get("served_date"))
            checks.append({
                "check": "served_date_set",
                "passed": has_served,
                "detail": (
                    f"Served on {filing.get('served_date')}."
                    if has_served
                    else "Not yet served."
                ),
            })

            # 9. File path valid
            fp = filing.get("file_path") or ""
            path_valid = bool(fp) and Path(fp).suffix.lower() in (
                ".pdf", ".docx", ".doc", ".md",
            )
            checks.append({
                "check": "file_path_valid",
                "passed": path_valid,
                "detail": fp if fp else "No file path.",
            })

            # 10. No placeholder text
            title = filing.get("title") or ""
            notes = filing.get("notes") or ""
            combined = title + " " + notes
            has_placeholder = any(
                marker in combined.upper()
                for marker in (
                    "[ANDREW_REQUIRED]",
                    "[INSERT",
                    "[ATTACH",
                    "[TODO",
                    "[PLACEHOLDER",
                )
            )
            checks.append({
                "check": "no_placeholder_text",
                "passed": not has_placeholder,
                "detail": (
                    "Placeholder text detected!" if has_placeholder
                    else "No placeholders found."
                ),
            })

            # 11. Deadline compliance
            if self._table_exists(conn, "deadlines"):
                overdue_row = conn.execute(
                    "SELECT COUNT(*) FROM deadlines "
                    "WHERE filing_id = ? AND due_date < date('now') "
                    "  AND status = 'pending'",
                    (filing_id,),
                ).fetchone()
                overdue = overdue_row[0] if overdue_row else 0
                checks.append({
                    "check": "no_overdue_deadlines",
                    "passed": overdue == 0,
                    "detail": (
                        f"{overdue} overdue deadline(s)!" if overdue
                        else "All deadlines current."
                    ),
                })

            passed = sum(1 for c in checks if c["passed"])
            total = len(checks)
            score_pct = round(passed / total * 100, 1) if total else 0.0

            result = {
                "filing_id": filing_id,
                "checks": checks,
                "passed": passed,
                "failed": total - passed,
                "total_checks": total,
                "score_pct": score_pct,
                "go_no_go": "GO" if score_pct >= 70 else "NO-GO",
            }

            logger.info(
                "prefiling_qa(%s) → %s (%.1f%% — %d/%d)",
                filing_id,
                result["go_no_go"],
                score_pct,
                passed,
                total,
            )
            return result
        finally:
            conn.close()

    # ------------------------------------------------------------------
    # 9. system_health
    # ------------------------------------------------------------------

    def system_health(self) -> dict:
        """Run system health diagnostics on the litigation database.

        Returns:
            ``{"db_path", "db_exists", "db_size_mb", "table_count",
              "index_count", "fts_tables", "wal_mode", "integrity",
              "row_counts"}``
        """
        health: dict[str, Any] = {
            "db_path": str(self._db_path),
            "db_exists": self._db_path.exists(),
            "db_size_mb": None,
            "table_count": 0,
            "index_count": 0,
            "fts_tables": [],
            "wal_mode": False,
            "integrity": "unknown",
            "row_counts": {},
        }

        if not health["db_exists"]:
            logger.warning("system_health: DB not found at %s", self._db_path)
            return health

        try:
            health["db_size_mb"] = round(
                os.path.getsize(self._db_path) / (1024 * 1024), 1
            )
        except OSError:
            pass

        conn = self._connect()
        try:
            # Table count
            health["table_count"] = conn.execute(
                "SELECT COUNT(*) FROM sqlite_master WHERE type='table'"
            ).fetchone()[0]

            # Index count
            health["index_count"] = conn.execute(
                "SELECT COUNT(*) FROM sqlite_master WHERE type='index'"
            ).fetchone()[0]

            # FTS5 tables
            fts_rows = conn.execute(
                "SELECT name FROM sqlite_master "
                "WHERE type='table' AND name LIKE '%fts%' "
                "ORDER BY name"
            ).fetchall()
            health["fts_tables"] = [r[0] for r in fts_rows]

            # WAL mode
            journal = conn.execute("PRAGMA journal_mode").fetchone()
            health["wal_mode"] = (
                journal[0].lower() == "wal" if journal else False
            )

            # Quick integrity check (fast — only checks b-tree structure)
            try:
                ic = conn.execute("PRAGMA quick_check(1)").fetchone()
                health["integrity"] = ic[0] if ic else "unknown"
            except sqlite3.Error:
                health["integrity"] = "check_failed"

            # Row counts for key tables
            key_tables = (
                "documents",
                "evidence_quotes",
                "deadlines",
                "filings",
                "claims",
                "judicial_violations",
                "docket_events",
            )
            for tbl in key_tables:
                if self._table_exists(conn, tbl):
                    cnt = conn.execute(
                        f"SELECT COUNT(*) FROM [{tbl}]"
                    ).fetchone()[0]
                    health["row_counts"][tbl] = cnt

            logger.info(
                "system_health() → %d tables, %.1f MB, integrity=%s",
                health["table_count"],
                health["db_size_mb"] or 0,
                health["integrity"],
            )
            return health
        finally:
            conn.close()

    # ------------------------------------------------------------------
    # 10. citation_graph
    # ------------------------------------------------------------------

    def citation_graph(self, filing_id: str) -> dict:
        """Build a citation dependency graph for a filing.

        Queries ``filing_rule_map`` for the authorities cited by the
        filing and constructs a node/edge graph structure.

        Args:
            filing_id: The filing to map.

        Returns:
            ``{"filing_id", "nodes", "edges", "authority_count"}``
        """
        graph: dict[str, Any] = {
            "filing_id": filing_id,
            "nodes": [],
            "edges": [],
            "authority_count": 0,
        }

        conn = self._connect()
        try:
            # Filing node
            filing_label = filing_id
            if self._table_exists(conn, "filings"):
                frow = self._safe_fetchone(
                    conn,
                    "SELECT title FROM filings WHERE id = ?",
                    (filing_id,),
                )
                if frow:
                    filing_label = frow.get("title") or filing_id

            graph["nodes"].append({
                "id": f"filing:{filing_id}",
                "label": filing_label,
                "type": "filing",
            })

            # Authority nodes and edges
            if self._table_exists(conn, "filing_rule_map"):
                rules = self._safe_fetchall(
                    conn,
                    "SELECT * FROM filing_rule_map WHERE filing_id = ?",
                    (filing_id,),
                )
                seen: set[str] = set()
                for rule in rules:
                    auth_type = rule.get("authority_type") or "rule"
                    auth_num = rule.get("authority_number") or "unknown"
                    node_id = f"auth:{auth_type}:{auth_num}"

                    if node_id not in seen:
                        seen.add(node_id)
                        graph["nodes"].append({
                            "id": node_id,
                            "label": f"{auth_type} {auth_num}",
                            "type": "authority",
                            "mandatory": bool(rule.get("mandatory")),
                        })
                    graph["edges"].append({
                        "from": f"filing:{filing_id}",
                        "to": node_id,
                        "label": rule.get("requirement") or "cites",
                    })

                graph["authority_count"] = len(seen)

            logger.info(
                "citation_graph(%s) → %d authorities, %d edges",
                filing_id,
                graph["authority_count"],
                len(graph["edges"]),
            )
            return graph
        finally:
            conn.close()

    # ------------------------------------------------------------------
    # 11. impeachment_search
    # ------------------------------------------------------------------

    def impeachment_search(self, party: str) -> list[dict]:
        """Find impeachment material against a party.

        Searches ``evidence_quotes`` and ``judicial_violations`` for
        statements or findings that could be used to impeach the
        named party's credibility.

        Args:
            party: The party name (or partial) to search for.

        Returns:
            List of ``{"source_table", "id", "text", "category",
            "relevance", "signal"}`` dicts.
        """
        if not party or not party.strip():
            return []

        results: list[dict] = []
        party_lower = party.strip().lower()
        conn = self._connect()
        try:
            # --- evidence_quotes ---
            if self._table_exists(conn, "evidence_quotes"):
                eq_rows = self._safe_fetchall(
                    conn,
                    "SELECT id, quote_text, category, relevance_score, "
                    "       source_file "
                    "FROM evidence_quotes "
                    "WHERE LOWER(quote_text) LIKE ? "
                    "ORDER BY relevance_score DESC "
                    "LIMIT 200",
                    (f"%{party_lower}%",),
                )
                for row in eq_rows:
                    text = (row.get("quote_text") or "").lower()
                    matched_signals = [
                        s for s in _IMPEACHMENT_SIGNALS if s in text
                    ]
                    if matched_signals:
                        results.append({
                            "source_table": "evidence_quotes",
                            "id": row.get("id"),
                            "text": (row.get("quote_text") or "")[:500],
                            "category": row.get("category"),
                            "relevance": row.get("relevance_score"),
                            "signal": ", ".join(matched_signals),
                            "source_file": row.get("source_file"),
                        })

            # --- judicial_violations ---
            if self._table_exists(conn, "judicial_violations"):
                jv_rows = self._safe_fetchall(
                    conn,
                    "SELECT id, violation_type, description, mcr_rule, "
                    "       severity, source_file, source_quote "
                    "FROM judicial_violations "
                    "WHERE LOWER(description) LIKE ? "
                    "   OR LOWER(source_quote) LIKE ? "
                    "ORDER BY severity DESC "
                    "LIMIT 100",
                    (f"%{party_lower}%", f"%{party_lower}%"),
                )
                for row in jv_rows:
                    results.append({
                        "source_table": "judicial_violations",
                        "id": row.get("id"),
                        "text": (row.get("description") or "")[:500],
                        "category": row.get("violation_type"),
                        "relevance": row.get("severity"),
                        "signal": row.get("mcr_rule") or "judicial_violation",
                        "source_file": row.get("source_file"),
                    })

            logger.info(
                "impeachment_search(%r) → %d results", party, len(results)
            )
            return results
        finally:
            conn.close()

    # ------------------------------------------------------------------
    # 12. contradiction_find
    # ------------------------------------------------------------------

    def contradiction_find(self, party: str) -> list[dict]:
        """Find contradictions in a party's statements.

        Searches ``evidence_quotes`` for statements by or about the
        named party that contain contradiction indicators, then groups
        them by category so the caller can compare pairs.

        Args:
            party: The party name (or partial) to search for.

        Returns:
            List of ``{"source_table", "id", "text", "category",
            "date", "signal", "source_file"}`` dicts.
        """
        if not party or not party.strip():
            return []

        results: list[dict] = []
        party_lower = party.strip().lower()
        conn = self._connect()
        try:
            # --- evidence_quotes with contradiction signals ---
            if self._table_exists(conn, "evidence_quotes"):
                eq_rows = self._safe_fetchall(
                    conn,
                    "SELECT id, quote_text, category, source_file, "
                    "       created_at, relevance_score "
                    "FROM evidence_quotes "
                    "WHERE LOWER(quote_text) LIKE ? "
                    "ORDER BY category, created_at "
                    "LIMIT 500",
                    (f"%{party_lower}%",),
                )
                for row in eq_rows:
                    text = (row.get("quote_text") or "").lower()
                    matched = [
                        s for s in _CONTRADICTION_SIGNALS if s in text
                    ]
                    if matched:
                        results.append({
                            "source_table": "evidence_quotes",
                            "id": row.get("id"),
                            "text": (row.get("quote_text") or "")[:500],
                            "category": row.get("category"),
                            "date": row.get("created_at"),
                            "signal": ", ".join(matched),
                            "source_file": row.get("source_file"),
                        })

            # --- docket_events mentioning the party ---
            if self._table_exists(conn, "docket_events"):
                de_rows = self._safe_fetchall(
                    conn,
                    "SELECT id, event_date, event_type, description, "
                    "       filed_by, source_file "
                    "FROM docket_events "
                    "WHERE LOWER(description) LIKE ? "
                    "ORDER BY event_date "
                    "LIMIT 200",
                    (f"%{party_lower}%",),
                )
                for row in de_rows:
                    desc = (row.get("description") or "").lower()
                    matched = [
                        s for s in _CONTRADICTION_SIGNALS if s in desc
                    ]
                    if matched:
                        results.append({
                            "source_table": "docket_events",
                            "id": row.get("id"),
                            "text": (row.get("description") or "")[:500],
                            "category": row.get("event_type"),
                            "date": row.get("event_date"),
                            "signal": ", ".join(matched),
                            "source_file": row.get("source_file"),
                        })

            logger.info(
                "contradiction_find(%r) → %d results", party, len(results)
            )
            return results
        finally:
            conn.close()
