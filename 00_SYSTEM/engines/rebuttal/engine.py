"""
Rebuttal Engine — queries, filters, and assembles judicial rebuttals.

Usage:
    from rebuttal import RebuttalEngine
    engine = RebuttalEngine()
    rebuttals = engine.by_factor("MCL 722.23(j)")
    brief_section = engine.format_appellate_section(rebuttals)
"""
from __future__ import annotations

import re
import sqlite3
from datetime import date
from pathlib import Path
from typing import Optional

from .models import JudicialRebuttal, RebuttalSeverity, StatementCategory

DB_PATH = Path(__file__).resolve().parents[3] / "litigation_context.db"
LAST_CONTACT = date(2025, 7, 29)


def _connect() -> sqlite3.Connection:
    conn = sqlite3.connect(str(DB_PATH))
    conn.execute("PRAGMA busy_timeout = 60000")
    conn.execute("PRAGMA journal_mode = WAL")
    conn.execute("PRAGMA cache_size = -32000")
    conn.row_factory = sqlite3.Row
    return conn


def _safe_fts5(raw: str) -> str:
    return re.sub(r'[^\w\s*"]', " ", raw).strip()


class RebuttalEngine:
    """Queries and assembles judicial rebuttals from the DB."""

    def __init__(self, conn: Optional[sqlite3.Connection] = None):
        self._conn = conn or _connect()

    def _rows_to_rebuttals(self, rows) -> list[JudicialRebuttal]:
        return [JudicialRebuttal(**dict(r)) for r in rows]

    # ── Active filter clause ──────────────────────────────────
    _ACTIVE = "is_active = 1"

    # ── Query Methods ──────────────────────────────────────────
    def all(self, limit: int = 500, include_inactive: bool = False) -> list[JudicialRebuttal]:
        where = "" if include_inactive else f"WHERE {self._ACTIVE}"
        rows = self._conn.execute(
            f"SELECT * FROM judicial_rebuttals {where} ORDER BY id LIMIT ?",
            (limit,),
        ).fetchall()
        return self._rows_to_rebuttals(rows)

    def by_severity(self, severity: str | RebuttalSeverity) -> list[JudicialRebuttal]:
        rows = self._conn.execute(
            f"SELECT * FROM judicial_rebuttals WHERE {self._ACTIVE} AND severity = ? ORDER BY id",
            (str(severity),),
        ).fetchall()
        return self._rows_to_rebuttals(rows)

    def by_category(self, category: str | StatementCategory) -> list[JudicialRebuttal]:
        rows = self._conn.execute(
            f"SELECT * FROM judicial_rebuttals WHERE {self._ACTIVE} AND statement_category = ? ORDER BY id",
            (str(category),),
        ).fetchall()
        return self._rows_to_rebuttals(rows)

    def by_factor(self, factor: str) -> list[JudicialRebuttal]:
        rows = self._conn.execute(
            f"SELECT * FROM judicial_rebuttals WHERE {self._ACTIVE} AND best_interest_factor LIKE ? ORDER BY id",
            (f"%{factor}%",),
        ).fetchall()
        return self._rows_to_rebuttals(rows)

    def by_lane(self, lane: str) -> list[JudicialRebuttal]:
        rows = self._conn.execute(
            f"SELECT * FROM judicial_rebuttals WHERE {self._ACTIVE} AND lane LIKE ? ORDER BY id",
            (f"%{lane}%",),
        ).fetchall()
        return self._rows_to_rebuttals(rows)

    def by_order_date(self, order_date: str) -> list[JudicialRebuttal]:
        rows = self._conn.execute(
            f"SELECT * FROM judicial_rebuttals WHERE {self._ACTIVE} AND order_date = ? ORDER BY id",
            (order_date,),
        ).fetchall()
        return self._rows_to_rebuttals(rows)

    def search(self, query: str, limit: int = 50) -> list[JudicialRebuttal]:
        safe = f"%{query}%"
        rows = self._conn.execute(
            f"""SELECT * FROM judicial_rebuttals 
               WHERE {self._ACTIVE} AND (
                 false_statement LIKE ? OR truth LIKE ? 
                 OR rebuttal_narrative LIKE ? OR legal_basis LIKE ?)
               ORDER BY id LIMIT ?""",
            (safe, safe, safe, safe, limit),
        ).fetchall()
        return self._rows_to_rebuttals(rows)

    def critical_for_filing(self, lane: str) -> list[JudicialRebuttal]:
        """Get CRITICAL + HIGH rebuttals for a specific filing lane."""
        rows = self._conn.execute(
            f"""SELECT * FROM judicial_rebuttals 
               WHERE {self._ACTIVE} AND lane LIKE ? AND severity IN ('CRITICAL', 'HIGH')
               ORDER BY 
                 CASE severity WHEN 'CRITICAL' THEN 1 WHEN 'HIGH' THEN 2 END,
                 id""",
            (f"%{lane}%",),
        ).fetchall()
        return self._rows_to_rebuttals(rows)

    def for_motion(self, lane: str, categories: list[str] | None = None) -> list[JudicialRebuttal]:
        """Get rebuttals organized for motion drafting."""
        cat_filter = ""
        params: list = [f"%{lane}%"]
        if categories:
            placeholders = ",".join("?" * len(categories))
            cat_filter = f"AND statement_category IN ({placeholders})"
            params.extend(categories)
        rows = self._conn.execute(
            f"""SELECT * FROM judicial_rebuttals 
               WHERE {self._ACTIVE} AND lane LIKE ? {cat_filter}
               ORDER BY 
                 CASE severity 
                   WHEN 'CRITICAL' THEN 1 WHEN 'HIGH' THEN 2 
                   WHEN 'MEDIUM' THEN 3 WHEN 'LOW' THEN 4 END,
                 order_date, id""",
            params,
        ).fetchall()
        return self._rows_to_rebuttals(rows)

    # ── Statistics ─────────────────────────────────────────────
    def stats(self) -> dict:
        total = self._conn.execute(
            f"SELECT COUNT(*) FROM judicial_rebuttals WHERE {self._ACTIVE}"
        ).fetchone()[0]
        inactive = self._conn.execute(
            "SELECT COUNT(*) FROM judicial_rebuttals WHERE is_active = 0"
        ).fetchone()[0]
        by_sev = dict(self._conn.execute(
            f"SELECT severity, COUNT(*) FROM judicial_rebuttals WHERE {self._ACTIVE} GROUP BY severity"
        ).fetchall())
        by_cat = dict(self._conn.execute(
            f"SELECT statement_category, COUNT(*) FROM judicial_rebuttals WHERE {self._ACTIVE} GROUP BY statement_category"
        ).fetchall())
        by_lane = dict(self._conn.execute(
            f"SELECT lane, COUNT(*) FROM judicial_rebuttals WHERE {self._ACTIVE} GROUP BY lane"
        ).fetchall())
        by_factor = dict(self._conn.execute(
            f"""SELECT best_interest_factor, COUNT(*) FROM judicial_rebuttals 
               WHERE {self._ACTIVE} AND best_interest_factor IS NOT NULL AND best_interest_factor != ''
               GROUP BY best_interest_factor"""
        ).fetchall())
        sep_days = (date.today() - LAST_CONTACT).days
        return {
            "total_active": total,
            "total_inactive": inactive,
            "separation_days": sep_days,
            "by_severity": by_sev,
            "by_category": by_cat,
            "by_lane": by_lane,
            "by_factor": by_factor,
        }

    # ── Cleanup ────────────────────────────────────────────────
    def deactivate_garbage_entries(self) -> int:
        """Soft-delete entries where false_statement is garbage (SQL patterns, JSON, etc.)."""
        cursor = self._conn.execute(
            """UPDATE judicial_rebuttals SET is_active = 0
               WHERE is_active = 1 AND (
                 false_statement LIKE '%|%|%|%'
                 OR false_statement LIKE '%{"id"%'
                 OR false_statement LIKE '%SELECT %FROM%'
                 OR LENGTH(false_statement) > 1000)"""
        )
        self._conn.commit()
        return cursor.rowcount

    def reactivate(self, rebuttal_id: int) -> bool:
        """Reactivate a previously deactivated rebuttal."""
        cursor = self._conn.execute(
            "UPDATE judicial_rebuttals SET is_active = 1 WHERE id = ? AND is_active = 0",
            (rebuttal_id,),
        )
        self._conn.commit()
        return cursor.rowcount > 0

    def close(self):
        if self._conn:
            self._conn.close()
