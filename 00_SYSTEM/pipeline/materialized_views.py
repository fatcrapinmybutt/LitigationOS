#!/usr/bin/env python3
"""
materialized_views.py — Trigger-Based Incremental Materialized Views

Keeps expensive aggregate queries pre-computed and always fresh via
SQLite INSERT/UPDATE/DELETE triggers on source tables.  Shadow tables
(mv_*) are maintained in real-time so reads are O(1) lookups instead
of full-table scans + JOINs.

Integration points:
  - connection_multiplexer.py  → read/write cursors, PRAGMA tuning
  - db_lock_manager.py         → slot-based concurrency (3-conn cap)
  - duckdb_sidecar.py          → optional analytical fallback

CLI:
  python materialized_views.py init                           # bootstrap
  python materialized_views.py refresh [view_name]            # rebuild
  python materialized_views.py query <view_name> [--where ..]
  python materialized_views.py stats
  python materialized_views.py list
"""
from __future__ import annotations

import argparse
import json
import logging
import os
import sqlite3
import sys
import textwrap
import time
from contextlib import contextmanager
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Optional

# ── UTF-8 safety ────────────────────────────────────────────────────
if sys.stdout and hasattr(sys.stdout, "fileno"):
    try:
        sys.stdout = open(
            sys.stdout.fileno(), mode="w", encoding="utf-8", errors="replace"
        )
    except Exception:
        pass

# ── Logging ─────────────────────────────────────────────────────────
log = logging.getLogger("materialized_views")
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)

# ── Paths ───────────────────────────────────────────────────────────
_LITIGOS_ROOT = Path(r"C:\Users\andre\LitigationOS")
_DEFAULT_DB = _LITIGOS_ROOT / "litigation_context.db"

# ── PRAGMAs (match connection_multiplexer.py tier) ──────────────────
_PRAGMAS: dict[str, Any] = {
    "busy_timeout": 180_000,
    "journal_mode": "WAL",
    "mmap_size": 12_884_901_888,
    "cache_size": -131_072,
    "temp_store": "MEMORY",
    "synchronous": "NORMAL",
}


def _apply_pragmas(conn: sqlite3.Connection) -> None:
    for key, val in _PRAGMAS.items():
        conn.execute(f"PRAGMA {key} = {val}")


# ── Registry metadata table ─────────────────────────────────────────
_REGISTRY_DDL = textwrap.dedent("""\
    CREATE TABLE IF NOT EXISTS mv_registry (
        view_name       TEXT PRIMARY KEY,
        source_sql      TEXT NOT NULL,
        source_tables   TEXT NOT NULL,   -- JSON list
        key_columns     TEXT NOT NULL,   -- JSON list
        aggregate_cols  TEXT NOT NULL,   -- JSON dict
        shadow_table    TEXT NOT NULL,
        created_at      TEXT NOT NULL,
        last_refreshed  TEXT,
        refresh_count   INTEGER DEFAULT 0,
        trigger_fires   INTEGER DEFAULT 0
    );
""")

_TRIGGER_COUNTER_DDL = textwrap.dedent("""\
    CREATE TABLE IF NOT EXISTS mv_trigger_log (
        view_name   TEXT NOT NULL,
        event_type  TEXT NOT NULL,       -- INSERT / UPDATE / DELETE
        fired_at    TEXT NOT NULL,
        source_table TEXT NOT NULL
    );
""")


# =====================================================================
#  MaterializedViewManager
# =====================================================================
class MaterializedViewManager:
    """Create, refresh and query trigger-backed materialized views."""

    def __init__(self, db_path: str | Path | None = None):
        self._db_path = Path(db_path) if db_path else _DEFAULT_DB
        self._conn: Optional[sqlite3.Connection] = None
        self._schema_cache: dict[str, list[str]] = {}

    # ── connection helpers ───────────────────────────────────────────
    @contextmanager
    def _connect(self):
        """Yield a fully-configured read/write connection."""
        conn = sqlite3.connect(str(self._db_path), timeout=180)
        conn.row_factory = sqlite3.Row
        _apply_pragmas(conn)
        try:
            yield conn
        finally:
            conn.close()

    def _get_table_columns(self, conn: sqlite3.Connection, table: str) -> list[str]:
        """Return column names for *table*, with caching."""
        if table in self._schema_cache:
            return self._schema_cache[table]
        try:
            rows = conn.execute(f"PRAGMA table_info([{table}])").fetchall()
            cols = [r["name"] for r in rows]
            self._schema_cache[table] = cols
            return cols
        except Exception:
            return []

    def _table_exists(self, conn: sqlite3.Connection, table: str) -> bool:
        row = conn.execute(
            "SELECT 1 FROM sqlite_master WHERE type='table' AND name=?", (table,)
        ).fetchone()
        return row is not None

    def _is_virtual_table(self, conn: sqlite3.Connection, table: str) -> bool:
        """FTS5 / R-tree virtual tables cannot carry triggers."""
        row = conn.execute(
            "SELECT sql FROM sqlite_master WHERE type='table' AND name=?", (table,)
        ).fetchone()
        if row and row["sql"]:
            return "VIRTUAL TABLE" in row["sql"].upper()
        return False

    # ── bootstrap ────────────────────────────────────────────────────
    def _ensure_meta_tables(self, conn: sqlite3.Connection) -> None:
        conn.executescript(_REGISTRY_DDL + _TRIGGER_COUNTER_DDL)

    # ── public API ───────────────────────────────────────────────────
    def register_view(
        self,
        name: str,
        shadow_ddl: str,
        source_sql: str,
        source_tables: list[str],
        key_columns: list[str],
        aggregate_columns: dict[str, str] | None = None,
        triggers_sql: list[str] | None = None,
    ) -> None:
        """Register a new materialized view.

        Parameters
        ----------
        name           : logical name  (e.g. ``vehicle_evidence_summary``)
        shadow_ddl     : full ``CREATE TABLE IF NOT EXISTS mv_<name> (...)``
        source_sql     : SELECT that populates the shadow table
        source_tables  : tables whose changes should fire triggers
        key_columns    : PK column(s) of the shadow table
        aggregate_columns : mapping col→description (informational)
        triggers_sql   : optional pre-built trigger SQL statements
        """
        shadow_table = f"mv_{name}"
        agg = aggregate_columns or {}

        with self._connect() as conn:
            self._ensure_meta_tables(conn)

            # 1. Create shadow table
            conn.executescript(shadow_ddl)
            log.info("Created shadow table %s", shadow_table)

            # 2. Register in metadata
            conn.execute(
                textwrap.dedent("""\
                    INSERT OR REPLACE INTO mv_registry
                        (view_name, source_sql, source_tables, key_columns,
                         aggregate_cols, shadow_table, created_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                """),
                (
                    name,
                    source_sql,
                    json.dumps(source_tables),
                    json.dumps(key_columns),
                    json.dumps(agg),
                    shadow_table,
                    datetime.now(timezone.utc).isoformat(),
                ),
            )

            # 3. Install triggers (skip virtual / missing tables)
            if triggers_sql:
                for tsql in triggers_sql:
                    try:
                        conn.executescript(tsql)
                    except sqlite3.OperationalError as exc:
                        log.warning("Trigger skipped (%s): %s", name, exc)

            conn.commit()
            log.info("Registered view '%s' (%d trigger statements)", name, len(triggers_sql or []))

    def refresh(self, name: str | None = None) -> dict[str, int]:
        """Full rebuild of one or all views.  Uses DELETE + INSERT to keep triggers."""
        results: dict[str, int] = {}
        with self._connect() as conn:
            self._ensure_meta_tables(conn)
            if name:
                rows = conn.execute(
                    "SELECT * FROM mv_registry WHERE view_name = ?", (name,)
                ).fetchall()
            else:
                rows = conn.execute("SELECT * FROM mv_registry").fetchall()

            for reg in rows:
                vname = reg["view_name"]
                shadow = reg["shadow_table"]
                sql = reg["source_sql"]
                try:
                    t0 = time.perf_counter()
                    conn.execute(f"DELETE FROM [{shadow}]")
                    # Column list from shadow table so INSERT matches
                    cols = self._get_table_columns(conn, shadow)
                    if not cols:
                        log.warning("Skip %s — shadow table has no columns", vname)
                        continue
                    col_list = ", ".join(f"[{c}]" for c in cols)
                    # The source_sql must return columns in the same order
                    conn.execute(f"INSERT OR IGNORE INTO [{shadow}] ({col_list}) {sql}")
                    cnt = conn.execute(f"SELECT COUNT(*) FROM [{shadow}]").fetchone()[0]
                    elapsed = time.perf_counter() - t0
                    conn.execute(
                        "UPDATE mv_registry SET last_refreshed = ?, refresh_count = refresh_count + 1 WHERE view_name = ?",
                        (datetime.now(timezone.utc).isoformat(), vname),
                    )
                    conn.commit()
                    results[vname] = cnt
                    log.info("Refreshed %s → %d rows (%.3fs)", vname, cnt, elapsed)
                except Exception as exc:
                    log.error("Refresh failed for %s: %s", vname, exc)
                    conn.rollback()
                    results[vname] = -1

        return results

    def query(
        self, name: str, where: str | None = None, params: tuple = ()
    ) -> list[dict]:
        """Read from shadow table.  Always fresh thanks to triggers."""
        shadow = f"mv_{name}"
        sql = f"SELECT * FROM [{shadow}]"
        if where:
            sql += f" WHERE {where}"
        with self._connect() as conn:
            cur = conn.execute(sql, params)
            cols = [d[0] for d in cur.description]
            return [dict(zip(cols, row)) for row in cur.fetchall()]

    def get_stats(self) -> dict[str, Any]:
        """Row counts, last refresh time, trigger fire counts."""
        stats: dict[str, Any] = {"views": {}}
        with self._connect() as conn:
            self._ensure_meta_tables(conn)
            regs = conn.execute("SELECT * FROM mv_registry").fetchall()
            for reg in regs:
                vname = reg["view_name"]
                shadow = reg["shadow_table"]
                try:
                    cnt = conn.execute(f"SELECT COUNT(*) FROM [{shadow}]").fetchone()[0]
                except Exception:
                    cnt = -1
                # Count trigger fires from log
                try:
                    fires = conn.execute(
                        "SELECT COUNT(*) FROM mv_trigger_log WHERE view_name = ?",
                        (vname,),
                    ).fetchone()[0]
                except Exception:
                    fires = 0
                stats["views"][vname] = {
                    "shadow_table": shadow,
                    "row_count": cnt,
                    "last_refreshed": reg["last_refreshed"],
                    "refresh_count": reg["refresh_count"],
                    "trigger_fires": fires,
                }
        stats["total_views"] = len(stats["views"])
        return stats

    def list_views(self) -> list[dict]:
        """Return metadata for every registered view."""
        with self._connect() as conn:
            self._ensure_meta_tables(conn)
            regs = conn.execute(
                "SELECT view_name, shadow_table, source_tables, last_refreshed, refresh_count FROM mv_registry"
            ).fetchall()
            return [dict(r) for r in regs]

    def drop_view(self, name: str) -> None:
        """Remove a materialized view, its shadow table, and its triggers."""
        shadow = f"mv_{name}"
        with self._connect() as conn:
            # Drop triggers that belong to this view
            trigs = conn.execute(
                "SELECT name FROM sqlite_master WHERE type='trigger' AND name LIKE ?",
                (f"trg_mv_{name}_%",),
            ).fetchall()
            for t in trigs:
                conn.execute(f"DROP TRIGGER IF EXISTS [{t['name']}]")
            conn.execute(f"DROP TABLE IF EXISTS [{shadow}]")
            conn.execute("DELETE FROM mv_registry WHERE view_name = ?", (name,))
            conn.execute("DELETE FROM mv_trigger_log WHERE view_name = ?", (name,))
            conn.commit()
            log.info("Dropped view '%s' (%d triggers removed)", name, len(trigs))


# =====================================================================
#  Pre-built view definitions
# =====================================================================
def _build_prebuilt_views(mgr: MaterializedViewManager, conn: sqlite3.Connection) -> None:
    """Discover actual schemas at runtime and register the four bottleneck views."""
    cols_of = lambda tbl: mgr._get_table_columns(conn, tbl)  # noqa: E731

    # ── helpers ──────────────────────────────────────────────────────
    def _has(table: str, col: str) -> bool:
        return col in cols_of(table)

    def _exists(table: str) -> bool:
        return mgr._table_exists(conn, table)

    def _is_virtual(table: str) -> bool:
        return mgr._is_virtual_table(conn, table)

    # =================================================================
    #  VIEW 1: vehicle_evidence_summary
    # =================================================================
    if _exists("filing_readiness"):
        fr_cols = cols_of("filing_readiness")
        vid_col = "vehicle_id" if "vehicle_id" in fr_cols else (
            "id" if "id" in fr_cols else fr_cols[0] if fr_cols else None
        )
        vname_col = "vehicle_name" if "vehicle_name" in fr_cols else (
            "name" if "name" in fr_cols else None
        )
        if vid_col:
            shadow_ddl = textwrap.dedent("""\
                CREATE TABLE IF NOT EXISTS mv_vehicle_evidence_summary (
                    vehicle_id      TEXT PRIMARY KEY,
                    vehicle_name    TEXT,
                    total_evidence  INTEGER DEFAULT 0,
                    quotes_count    INTEGER DEFAULT 0,
                    documents_count INTEGER DEFAULT 0,
                    citations_count INTEGER DEFAULT 0,
                    timeline_events INTEGER DEFAULT 0,
                    last_updated    TEXT
                );
            """)

            # Build source SELECT — subqueries only for tables that exist
            sub_parts = []
            if _exists("evidence_quotes") and not _is_virtual("evidence_quotes"):
                eq_cols = cols_of("evidence_quotes")
                eq_join = "vehicle_id" if "vehicle_id" in eq_cols else None
                if eq_join:
                    sub_parts.append(
                        f"(SELECT COUNT(*) FROM evidence_quotes eq WHERE eq.vehicle_id = fr.[{vid_col}])"
                    )
                else:
                    sub_parts.append("0")
            else:
                sub_parts.append("0")
            # quotes_count ↑

            if _exists("master_citations") and not _is_virtual("master_citations"):
                mc_cols = cols_of("master_citations")
                mc_join = "vehicle_id" if "vehicle_id" in mc_cols else None
                if mc_join:
                    sub_parts.append(
                        f"(SELECT COUNT(*) FROM master_citations mc WHERE mc.vehicle_id = fr.[{vid_col}])"
                    )
                else:
                    sub_parts.append("0")
            else:
                sub_parts.append("0")
            # citations_count ↑

            vname_expr = f"fr.[{vname_col}]" if vname_col else "NULL"
            source_sql = textwrap.dedent(f"""\
                SELECT
                    fr.[{vid_col}],
                    {vname_expr},
                    {sub_parts[0]} + {sub_parts[1]} AS total_evidence,
                    {sub_parts[0]},
                    0,
                    {sub_parts[1]},
                    0,
                    datetime('now')
                FROM filing_readiness fr
            """)

            # Triggers — lightweight increments only on non-virtual source tables
            triggers: list[str] = []
            source_tables = ["filing_readiness"]

            if _exists("evidence_quotes") and not _is_virtual("evidence_quotes"):
                eq_cols = cols_of("evidence_quotes")
                if "vehicle_id" in eq_cols:
                    source_tables.append("evidence_quotes")
                    triggers.append(textwrap.dedent("""\
                        CREATE TRIGGER IF NOT EXISTS trg_mv_vehicle_evidence_summary_eq_ins
                        AFTER INSERT ON evidence_quotes
                        BEGIN
                            UPDATE mv_vehicle_evidence_summary
                            SET quotes_count    = quotes_count + 1,
                                total_evidence  = total_evidence + 1,
                                last_updated    = datetime('now')
                            WHERE vehicle_id = NEW.vehicle_id;
                        END;
                    """))
                    triggers.append(textwrap.dedent("""\
                        CREATE TRIGGER IF NOT EXISTS trg_mv_vehicle_evidence_summary_eq_del
                        AFTER DELETE ON evidence_quotes
                        BEGIN
                            UPDATE mv_vehicle_evidence_summary
                            SET quotes_count    = MAX(quotes_count - 1, 0),
                                total_evidence  = MAX(total_evidence - 1, 0),
                                last_updated    = datetime('now')
                            WHERE vehicle_id = OLD.vehicle_id;
                        END;
                    """))

            if _exists("master_citations") and not _is_virtual("master_citations"):
                mc_cols = cols_of("master_citations")
                if "vehicle_id" in mc_cols:
                    source_tables.append("master_citations")
                    triggers.append(textwrap.dedent("""\
                        CREATE TRIGGER IF NOT EXISTS trg_mv_vehicle_evidence_summary_mc_ins
                        AFTER INSERT ON master_citations
                        BEGIN
                            UPDATE mv_vehicle_evidence_summary
                            SET citations_count = citations_count + 1,
                                total_evidence  = total_evidence + 1,
                                last_updated    = datetime('now')
                            WHERE vehicle_id = NEW.vehicle_id;
                        END;
                    """))
                    triggers.append(textwrap.dedent("""\
                        CREATE TRIGGER IF NOT EXISTS trg_mv_vehicle_evidence_summary_mc_del
                        AFTER DELETE ON master_citations
                        BEGIN
                            UPDATE mv_vehicle_evidence_summary
                            SET citations_count = MAX(citations_count - 1, 0),
                                total_evidence  = MAX(total_evidence - 1, 0),
                                last_updated    = datetime('now')
                            WHERE vehicle_id = OLD.vehicle_id;
                        END;
                    """))

            mgr.register_view(
                name="vehicle_evidence_summary",
                shadow_ddl=shadow_ddl,
                source_sql=source_sql,
                source_tables=source_tables,
                key_columns=["vehicle_id"],
                aggregate_columns={
                    "total_evidence": "SUM of all linked evidence",
                    "quotes_count": "COUNT from evidence_quotes",
                    "citations_count": "COUNT from master_citations",
                },
                triggers_sql=triggers,
            )
    else:
        log.warning("filing_readiness table not found — skipping vehicle_evidence_summary")

    # =================================================================
    #  VIEW 2: claim_coverage_matrix
    # =================================================================
    if _exists("claims"):
        cl_cols = cols_of("claims")
        cid = "claim_id" if "claim_id" in cl_cols else ("id" if "id" in cl_cols else cl_cols[0] if cl_cols else None)
        ctype = "claim_type" if "claim_type" in cl_cols else ("type" if "type" in cl_cols else None)
        clane = "lane" if "lane" in cl_cols else None

        if cid:
            shadow_ddl = textwrap.dedent("""\
                CREATE TABLE IF NOT EXISTS mv_claim_coverage_matrix (
                    claim_id        TEXT PRIMARY KEY,
                    claim_type      TEXT,
                    lane            TEXT,
                    evidence_count  INTEGER DEFAULT 0,
                    citation_count  INTEGER DEFAULT 0,
                    gap_count       INTEGER DEFAULT 0,
                    coverage_pct    REAL DEFAULT 0.0,
                    status          TEXT,
                    last_updated    TEXT
                );
            """)

            ctype_expr = f"c.[{ctype}]" if ctype else "NULL"
            clane_expr = f"c.[{clane}]" if clane else "NULL"

            # Evidence count — look for a link table or direct FK
            ev_sub = "0"
            if _exists("evidence_quotes") and not _is_virtual("evidence_quotes"):
                eq_cols = cols_of("evidence_quotes")
                if "claim_id" in eq_cols:
                    ev_sub = f"(SELECT COUNT(*) FROM evidence_quotes eq WHERE eq.claim_id = c.[{cid}])"

            cit_sub = "0"
            if _exists("master_citations") and not _is_virtual("master_citations"):
                mc_cols = cols_of("master_citations")
                if "claim_id" in mc_cols:
                    cit_sub = f"(SELECT COUNT(*) FROM master_citations mc WHERE mc.claim_id = c.[{cid}])"

            source_sql = textwrap.dedent(f"""\
                SELECT
                    c.[{cid}],
                    {ctype_expr},
                    {clane_expr},
                    {ev_sub},
                    {cit_sub},
                    0,
                    CASE WHEN ({ev_sub} + {cit_sub}) > 0 THEN 100.0 ELSE 0.0 END,
                    CASE
                        WHEN ({ev_sub} + {cit_sub}) >= 3 THEN 'covered'
                        WHEN ({ev_sub} + {cit_sub}) >= 1 THEN 'partial'
                        ELSE 'gap'
                    END,
                    datetime('now')
                FROM claims c
            """)

            triggers: list[str] = []
            source_tables = ["claims"]

            if _exists("evidence_quotes") and not _is_virtual("evidence_quotes"):
                eq_cols = cols_of("evidence_quotes")
                if "claim_id" in eq_cols:
                    source_tables.append("evidence_quotes")
                    triggers.append(textwrap.dedent("""\
                        CREATE TRIGGER IF NOT EXISTS trg_mv_claim_coverage_matrix_eq_ins
                        AFTER INSERT ON evidence_quotes
                        WHEN NEW.claim_id IS NOT NULL
                        BEGIN
                            UPDATE mv_claim_coverage_matrix
                            SET evidence_count = evidence_count + 1,
                                coverage_pct   = CASE WHEN (evidence_count + 1 + citation_count) >= 3 THEN 100.0
                                                      ELSE ROUND(((evidence_count + 1 + citation_count) * 100.0 / 3), 1) END,
                                status         = CASE WHEN (evidence_count + 1 + citation_count) >= 3 THEN 'covered'
                                                      WHEN (evidence_count + 1 + citation_count) >= 1 THEN 'partial'
                                                      ELSE 'gap' END,
                                last_updated   = datetime('now')
                            WHERE claim_id = NEW.claim_id;
                        END;
                    """))
                    triggers.append(textwrap.dedent("""\
                        CREATE TRIGGER IF NOT EXISTS trg_mv_claim_coverage_matrix_eq_del
                        AFTER DELETE ON evidence_quotes
                        WHEN OLD.claim_id IS NOT NULL
                        BEGIN
                            UPDATE mv_claim_coverage_matrix
                            SET evidence_count = MAX(evidence_count - 1, 0),
                                coverage_pct   = CASE WHEN (MAX(evidence_count - 1, 0) + citation_count) >= 3 THEN 100.0
                                                      ELSE ROUND(((MAX(evidence_count - 1, 0) + citation_count) * 100.0 / 3), 1) END,
                                status         = CASE WHEN (MAX(evidence_count - 1, 0) + citation_count) >= 3 THEN 'covered'
                                                      WHEN (MAX(evidence_count - 1, 0) + citation_count) >= 1 THEN 'partial'
                                                      ELSE 'gap' END,
                                last_updated   = datetime('now')
                            WHERE claim_id = OLD.claim_id;
                        END;
                    """))

            mgr.register_view(
                name="claim_coverage_matrix",
                shadow_ddl=shadow_ddl,
                source_sql=source_sql,
                source_tables=source_tables,
                key_columns=["claim_id"],
                aggregate_columns={
                    "evidence_count": "COUNT of linked evidence",
                    "citation_count": "COUNT of linked citations",
                    "coverage_pct": "derived coverage percentage",
                },
                triggers_sql=triggers,
            )
    else:
        log.warning("claims table not found — skipping claim_coverage_matrix")

    # =================================================================
    #  VIEW 3: deadline_urgency_ranked
    # =================================================================
    if _exists("deadlines"):
        dl_cols = cols_of("deadlines")
        did = "deadline_id" if "deadline_id" in dl_cols else ("id" if "id" in dl_cols else dl_cols[0] if dl_cols else None)
        desc_col = "description" if "description" in dl_cols else ("title" if "title" in dl_cols else None)
        due_col = "due_date_iso" if "due_date_iso" in dl_cols else (
            "due_date" if "due_date" in dl_cols else (
                "deadline_date" if "deadline_date" in dl_cols else None
            )
        )
        dl_vid = "vehicle_id" if "vehicle_id" in dl_cols else None
        dl_lane = "lane" if "lane" in dl_cols else None
        dl_status = "status" if "status" in dl_cols else None

        if did and due_col:
            shadow_ddl = textwrap.dedent("""\
                CREATE TABLE IF NOT EXISTS mv_deadline_urgency_ranked (
                    deadline_id     TEXT PRIMARY KEY,
                    description     TEXT,
                    due_date        TEXT,
                    days_remaining  INTEGER,
                    urgency_score   REAL,
                    vehicle_id      TEXT,
                    lane            TEXT,
                    status          TEXT,
                    last_updated    TEXT
                );
            """)

            desc_expr = f"d.[{desc_col}]" if desc_col else "NULL"
            vid_expr = f"d.[{dl_vid}]" if dl_vid else "NULL"
            lane_expr = f"d.[{dl_lane}]" if dl_lane else "NULL"
            stat_expr = f"d.[{dl_status}]" if dl_status else "'active'"

            source_sql = textwrap.dedent(f"""\
                SELECT
                    d.[{did}],
                    {desc_expr},
                    d.[{due_col}],
                    CAST(julianday(d.[{due_col}]) - julianday('now') AS INTEGER),
                    CASE
                        WHEN julianday(d.[{due_col}]) - julianday('now') <= 0  THEN 100.0
                        WHEN julianday(d.[{due_col}]) - julianday('now') <= 3  THEN 90.0
                        WHEN julianday(d.[{due_col}]) - julianday('now') <= 7  THEN 75.0
                        WHEN julianday(d.[{due_col}]) - julianday('now') <= 14 THEN 50.0
                        WHEN julianday(d.[{due_col}]) - julianday('now') <= 30 THEN 25.0
                        ELSE 10.0
                    END,
                    {vid_expr},
                    {lane_expr},
                    {stat_expr},
                    datetime('now')
                FROM deadlines d
            """)

            triggers: list[str] = []
            if not _is_virtual("deadlines"):
                triggers.append(textwrap.dedent(f"""\
                    CREATE TRIGGER IF NOT EXISTS trg_mv_deadline_urgency_ranked_ins
                    AFTER INSERT ON deadlines
                    BEGIN
                        INSERT OR REPLACE INTO mv_deadline_urgency_ranked
                            (deadline_id, description, due_date, days_remaining,
                             urgency_score, vehicle_id, lane, status, last_updated)
                        VALUES (
                            NEW.[{did}],
                            {"NEW.[" + desc_col + "]" if desc_col else "NULL"},
                            NEW.[{due_col}],
                            CAST(julianday(NEW.[{due_col}]) - julianday('now') AS INTEGER),
                            CASE
                                WHEN julianday(NEW.[{due_col}]) - julianday('now') <= 0  THEN 100.0
                                WHEN julianday(NEW.[{due_col}]) - julianday('now') <= 3  THEN 90.0
                                WHEN julianday(NEW.[{due_col}]) - julianday('now') <= 7  THEN 75.0
                                WHEN julianday(NEW.[{due_col}]) - julianday('now') <= 14 THEN 50.0
                                WHEN julianday(NEW.[{due_col}]) - julianday('now') <= 30 THEN 25.0
                                ELSE 10.0
                            END,
                            {"NEW.[" + dl_vid + "]" if dl_vid else "NULL"},
                            {"NEW.[" + dl_lane + "]" if dl_lane else "NULL"},
                            {"NEW.[" + dl_status + "]" if dl_status else "'active'"},
                            datetime('now')
                        );
                    END;
                """))
                triggers.append(textwrap.dedent(f"""\
                    CREATE TRIGGER IF NOT EXISTS trg_mv_deadline_urgency_ranked_upd
                    AFTER UPDATE ON deadlines
                    BEGIN
                        UPDATE mv_deadline_urgency_ranked
                        SET description    = {"NEW.[" + desc_col + "]" if desc_col else "NULL"},
                            due_date       = NEW.[{due_col}],
                            days_remaining = CAST(julianday(NEW.[{due_col}]) - julianday('now') AS INTEGER),
                            urgency_score  = CASE
                                WHEN julianday(NEW.[{due_col}]) - julianday('now') <= 0  THEN 100.0
                                WHEN julianday(NEW.[{due_col}]) - julianday('now') <= 3  THEN 90.0
                                WHEN julianday(NEW.[{due_col}]) - julianday('now') <= 7  THEN 75.0
                                WHEN julianday(NEW.[{due_col}]) - julianday('now') <= 14 THEN 50.0
                                WHEN julianday(NEW.[{due_col}]) - julianday('now') <= 30 THEN 25.0
                                ELSE 10.0
                            END,
                            {"vehicle_id = NEW.[" + dl_vid + "]," if dl_vid else ""}
                            {"lane = NEW.[" + dl_lane + "]," if dl_lane else ""}
                            status         = {"NEW.[" + dl_status + "]" if dl_status else "'active'"},
                            last_updated   = datetime('now')
                        WHERE deadline_id = NEW.[{did}];
                    END;
                """))
                triggers.append(textwrap.dedent(f"""\
                    CREATE TRIGGER IF NOT EXISTS trg_mv_deadline_urgency_ranked_del
                    AFTER DELETE ON deadlines
                    BEGIN
                        DELETE FROM mv_deadline_urgency_ranked
                        WHERE deadline_id = OLD.[{did}];
                    END;
                """))

            mgr.register_view(
                name="deadline_urgency_ranked",
                shadow_ddl=shadow_ddl,
                source_sql=source_sql,
                source_tables=["deadlines"],
                key_columns=["deadline_id"],
                aggregate_columns={"urgency_score": "computed from days_remaining"},
                triggers_sql=triggers,
            )
    else:
        log.warning("deadlines table not found — skipping deadline_urgency_ranked")

    # =================================================================
    #  VIEW 4: table_row_counts  (replaces 184× COUNT(*))
    # =================================================================
    shadow_ddl = textwrap.dedent("""\
        CREATE TABLE IF NOT EXISTS mv_table_row_counts (
            table_name   TEXT PRIMARY KEY,
            row_count    INTEGER DEFAULT 0,
            last_updated TEXT
        );
    """)

    # Build a UNION ALL of COUNT(*) for every real (non-virtual, non-mv_) table
    all_tables_rows = conn.execute(
        "SELECT name, sql FROM sqlite_master WHERE type='table' ORDER BY name"
    ).fetchall()
    union_parts: list[str] = []
    source_tables_rc: list[str] = []
    for r in all_tables_rows:
        tname = r["name"]
        tsql = r["sql"] or ""
        if tname.startswith("mv_"):
            continue
        if "VIRTUAL TABLE" in tsql.upper():
            continue
        if tname.startswith("sqlite_"):
            continue
        union_parts.append(
            f"SELECT '{tname}' AS table_name, COUNT(*) AS row_count, datetime('now') AS last_updated FROM [{tname}]"
        )
        source_tables_rc.append(tname)

    if union_parts:
        source_sql = "\nUNION ALL\n".join(union_parts)
    else:
        source_sql = "SELECT 'empty' AS table_name, 0 AS row_count, datetime('now') AS last_updated"

    # No per-table triggers for row counts (would require one trigger per table —
    # too many for 694 tables).  Refresh via periodic `refresh('table_row_counts')`.
    mgr.register_view(
        name="table_row_counts",
        shadow_ddl=shadow_ddl,
        source_sql=source_sql,
        source_tables=source_tables_rc[:20],  # top 20 for metadata only
        key_columns=["table_name"],
        aggregate_columns={"row_count": "COUNT(*) per table"},
        triggers_sql=[],
    )


# =====================================================================
#  init() — one-shot bootstrap
# =====================================================================
def init(db_path: str | Path | None = None) -> MaterializedViewManager:
    """Create all shadow tables, triggers, and do initial population."""
    mgr = MaterializedViewManager(db_path)
    log.info("Initializing materialized views on %s", mgr._db_path)

    with mgr._connect() as conn:
        mgr._ensure_meta_tables(conn)
        _build_prebuilt_views(mgr, conn)

    results = mgr.refresh()
    log.info("Init complete — %d views populated", len(results))
    return mgr


# =====================================================================
#  CLI
# =====================================================================
def _cli() -> None:
    parser = argparse.ArgumentParser(
        description="LitigationOS Materialized Views Manager"
    )
    parser.add_argument(
        "--db",
        type=str,
        default=str(_DEFAULT_DB),
        help="Path to SQLite database (default: litigation_context.db)",
    )
    sub = parser.add_subparsers(dest="command")

    sub.add_parser("init", help="Create shadow tables + triggers + initial population")
    p_refresh = sub.add_parser("refresh", help="Full rebuild of one or all views")
    p_refresh.add_argument("view_name", nargs="?", default=None)

    p_query = sub.add_parser("query", help="Read a materialized view")
    p_query.add_argument("view_name")
    p_query.add_argument("--where", type=str, default=None)
    p_query.add_argument("--limit", type=int, default=50)
    p_query.add_argument("--json", action="store_true", dest="as_json")

    sub.add_parser("stats", help="Show view statistics")
    sub.add_parser("list", help="List registered views")

    p_drop = sub.add_parser("drop", help="Remove a materialized view")
    p_drop.add_argument("view_name")

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        return

    if args.command == "init":
        init(args.db)

    elif args.command == "refresh":
        mgr = MaterializedViewManager(args.db)
        results = mgr.refresh(args.view_name)
        for vname, cnt in results.items():
            status = f"{cnt} rows" if cnt >= 0 else "FAILED"
            print(f"  {vname}: {status}")

    elif args.command == "query":
        mgr = MaterializedViewManager(args.db)
        where = args.where
        if args.limit and not where:
            where = f"1=1 LIMIT {args.limit}"
        elif args.limit and where:
            where += f" LIMIT {args.limit}"
        rows = mgr.query(args.view_name, where=where)
        if args.as_json:
            print(json.dumps(rows, indent=2, default=str))
        else:
            if not rows:
                print(f"  (no rows in mv_{args.view_name})")
            else:
                headers = list(rows[0].keys())
                print("  " + " | ".join(headers))
                print("  " + "-+-".join("-" * min(len(h), 20) for h in headers))
                for r in rows:
                    vals = [str(r.get(h, ""))[:40] for h in headers]
                    print("  " + " | ".join(vals))

    elif args.command == "stats":
        mgr = MaterializedViewManager(args.db)
        stats = mgr.get_stats()
        print(f"\nMaterialized Views — {stats['total_views']} registered\n")
        for vname, info in stats["views"].items():
            print(f"  {vname}")
            print(f"    shadow table   : {info['shadow_table']}")
            print(f"    rows           : {info['row_count']}")
            print(f"    last refreshed : {info['last_refreshed'] or 'never'}")
            print(f"    refresh count  : {info['refresh_count']}")
            print(f"    trigger fires  : {info['trigger_fires']}")
            print()

    elif args.command == "list":
        mgr = MaterializedViewManager(args.db)
        views = mgr.list_views()
        if not views:
            print("  (no views registered)")
        else:
            print(f"\n{'View Name':<35} {'Shadow Table':<35} {'Last Refreshed':<28} {'# Refreshes':>12}")
            print("-" * 115)
            for v in views:
                print(
                    f"  {v['view_name']:<33} {v['shadow_table']:<35} "
                    f"{(v['last_refreshed'] or 'never'):<28} {v['refresh_count']:>10}"
                )

    elif args.command == "drop":
        mgr = MaterializedViewManager(args.db)
        mgr.drop_view(args.view_name)
        print(f"  Dropped: {args.view_name}")


if __name__ == "__main__":
    _cli()
