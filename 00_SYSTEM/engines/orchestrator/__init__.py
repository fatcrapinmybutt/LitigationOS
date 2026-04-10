"""
Cross-Engine Orchestrator — Unified Query Fusion for LitigationOS.

Chains ALL engine output tables into single-call fusion queries.
Tables: evidence_quotes, timeline_events, impeachment_matrix, contradiction_map,
authority_chains_v2, adversary_profiles, causal_chains, irac_analyses,
damages_calculation, judicial_violations, rebuttal_matrix.

FTS5 safety: sanitize → try/except MATCH → LIKE fallback.
Schema-verify: PRAGMA table_info(X) before first query to any table.
"""

import re
import sqlite3
from pathlib import Path
from typing import Any

DB_PATH = str(Path(__file__).resolve().parents[3] / "litigation_context.db")

_PRAGMAS = (
    "PRAGMA busy_timeout = 60000;",
    "PRAGMA journal_mode = WAL;",
    "PRAGMA cache_size = -32000;",
    "PRAGMA temp_store = MEMORY;",
    "PRAGMA synchronous = NORMAL;",
)

# Table definitions: name → (search_columns for LIKE, fts_index or None)
_TABLE_DEFS: dict[str, dict[str, Any]] = {
    "evidence_quotes": {
        "like_cols": ("quote_text", "category", "source_file"),
        "fts": "evidence_fts",
        "fts_match_col": "quote_text",
        "id_col": "id",
    },
    "timeline_events": {
        "like_cols": ("event_description", "actors"),
        "fts": "timeline_fts",
        "fts_match_col": "description",
        "id_col": "id",
    },
    "impeachment_matrix": {
        "like_cols": ("evidence_summary", "quote_text", "cross_exam_question"),
        "fts": "impeachment_matrix_fts",
        "fts_match_col": "evidence_summary",
        "id_col": "id",
    },
    "contradiction_map": {
        "like_cols": ("contradiction_text", "source_a", "source_b"),
        "fts": "contradiction_map_fts",
        "fts_match_col": "contradiction_text",
        "id_col": "id",
    },
    "authority_chains_v2": {
        "like_cols": ("primary_citation", "supporting_citation", "paragraph_context"),
        "fts": None,
        "id_col": "id",
    },
    "adversary_profiles": {
        "like_cols": ("name", "behavior_patterns", "weaknesses", "counter_strategies"),
        "fts": None,
        "id_col": "id",
    },
    "causal_chains": {
        "like_cols": ("cause_event", "effect_event", "narrative"),
        "fts": None,
        "id_col": "id",
    },
    "irac_analyses": {
        "like_cols": ("issue", "rule", "application", "conclusion"),
        "fts": None,
        "id_col": "id",
    },
    "damages_calculation": {
        "like_cols": ("category", "description", "basis"),
        "fts": None,
        "id_col": "id",
    },
    "judicial_violations": {
        "like_cols": ("violation_type", "description", "source_quote"),
        "fts": "judicial_violations_fts",
        "fts_match_col": "description",
        "id_col": "id",
    },
    "rebuttal_matrix": {
        "like_cols": ("claim_text", "rebuttal_text", "rebuttal_evidence"),
        "fts": None,
        "id_col": "id",
    },
}

# Additional tables for health check only (no search needed)
_HEALTH_TABLES = (
    "evidence_quotes", "timeline_events", "impeachment_matrix",
    "contradiction_map", "authority_chains_v2", "adversary_profiles",
    "causal_chains", "irac_analyses", "damages_calculation",
    "judicial_violations", "rebuttal_matrix", "police_reports",
    "berry_mcneill_intelligence", "master_citations",
    "md_sections", "md_cross_refs",
)


def _sanitize_fts5(query: str) -> str:
    """Strip non-alphanumeric chars except whitespace, *, and double-quotes."""
    return re.sub(r'[^\w\s*"]', " ", query).strip()


def _get_connection(db_path: Path | None = None) -> sqlite3.Connection:
    """Open a connection with mandatory PRAGMAs. Row factory = sqlite3.Row."""
    path = db_path or DB_PATH
    if not path.exists():
        raise FileNotFoundError(f"Database not found: {path}")
    conn = sqlite3.connect(str(path))
    conn.row_factory = sqlite3.Row
    for pragma in _PRAGMAS:
        conn.execute(pragma)
    return conn


class _SchemaCache:
    """Caches PRAGMA table_info results so we verify once per table per session."""

    def __init__(self, conn: sqlite3.Connection) -> None:
        self._conn = conn
        self._cache: dict[str, set[str]] = {}

    def columns(self, table: str) -> set[str]:
        if table not in self._cache:
            try:
                rows = self._conn.execute(f"PRAGMA table_info([{table}])").fetchall()
                self._cache[table] = {r["name"] for r in rows}
            except Exception:
                self._cache[table] = set()
        return self._cache[table]

    def exists(self, table: str) -> bool:
        return len(self.columns(table)) > 0

    def has_column(self, table: str, col: str) -> bool:
        return col in self.columns(table)

    def fts_exists(self, fts_table: str) -> bool:
        """Check if an FTS5 virtual table is usable."""
        try:
            self._conn.execute(f"SELECT * FROM [{fts_table}] LIMIT 0")
            return True
        except Exception:
            return False


class Orchestrator:
    """
    Unified query orchestrator that chains ALL engine output tables into
    single-call fusion queries.

    Usage:
        orch = Orchestrator()
        result = orch.fuse("McNeill")
        profile = orch.entity_profile("Emily A. Watson")
        intel = orch.filing_intel("A")
        status = orch.health()
        orch.close()
    """

    def __init__(self, db_path: Path | None = None) -> None:
        self._conn = _get_connection(db_path)
        self._schema = _SchemaCache(self._conn)

    def close(self) -> None:
        if self._conn:
            self._conn.close()
            self._conn = None

    def __enter__(self) -> "Orchestrator":
        return self

    def __exit__(self, *exc: object) -> None:
        self.close()

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _search_table_fts(
        self, table: str, fts_table: str, match_col: str, query: str, limit: int = 50
    ) -> list[dict]:
        """Try FTS5 MATCH first; fall back to LIKE on any error."""
        sanitized = _sanitize_fts5(query)
        if not sanitized:
            return []

        # Attempt FTS5
        if self._schema.fts_exists(fts_table):
            try:
                sql = (
                    f"SELECT t.* FROM [{table}] t "
                    f"JOIN [{fts_table}] f ON t.rowid = f.rowid "
                    f"WHERE [{fts_table}] MATCH ? "
                    f"LIMIT ?"
                )
                rows = self._conn.execute(sql, (sanitized, limit)).fetchall()
                return [dict(r) for r in rows]
            except Exception:
                pass  # fall through to LIKE

        # LIKE fallback
        return self._search_table_like(table, query, limit)

    def _search_table_like(
        self, table: str, query: str, limit: int = 50
    ) -> list[dict]:
        """Search a table using parameterized LIKE on its configured columns."""
        if not self._schema.exists(table):
            return []

        defn = _TABLE_DEFS.get(table)
        if not defn:
            return []

        available_cols = [
            c for c in defn["like_cols"] if self._schema.has_column(table, c)
        ]
        if not available_cols:
            return []

        clauses = " OR ".join(f"[{c}] LIKE '%' || ? || '%'" for c in available_cols)
        params = [query] * len(available_cols)
        params.append(limit)

        sql = f"SELECT * FROM [{table}] WHERE ({clauses}) LIMIT ?"
        try:
            rows = self._conn.execute(sql, params).fetchall()
            return [dict(r) for r in rows]
        except Exception:
            return []

    def _search_table(
        self, table: str, query: str, limit: int = 50
    ) -> list[dict]:
        """Unified search: FTS5 if available, else LIKE."""
        defn = _TABLE_DEFS.get(table)
        if not defn or not self._schema.exists(table):
            return []

        fts = defn.get("fts")
        if fts:
            return self._search_table_fts(
                table, fts, defn.get("fts_match_col", ""), query, limit
            )
        return self._search_table_like(table, query, limit)

    def _count_table(self, table: str) -> int:
        """Safe row count for a single table."""
        if not self._schema.exists(table):
            return 0
        try:
            row = self._conn.execute(f"SELECT COUNT(*) AS n FROM [{table}]").fetchone()
            return row["n"] if row else 0
        except Exception:
            return 0

    def _lane_filter(
        self, table: str, lane: str, limit: int = 100
    ) -> list[dict]:
        """Filter a table by lane column (if it has one)."""
        if not self._schema.exists(table) or not self._schema.has_column(table, "lane"):
            return []
        try:
            rows = self._conn.execute(
                f"SELECT * FROM [{table}] WHERE [lane] LIKE '%' || ? || '%' LIMIT ?",
                (lane, limit),
            ).fetchall()
            return [dict(r) for r in rows]
        except Exception:
            return []

    def _get_all(self, table: str, limit: int = 200) -> list[dict]:
        """Return all rows from a table, capped at limit."""
        if not self._schema.exists(table):
            return []
        try:
            rows = self._conn.execute(
                f"SELECT * FROM [{table}] LIMIT ?", (limit,)
            ).fetchall()
            return [dict(r) for r in rows]
        except Exception:
            return []

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def fuse(self, entity: str, limit: int = 30) -> dict:
        """
        Query ALL engine output tables simultaneously for a given entity/topic.

        Returns a dict keyed by source table, each containing:
          - "rows": list of matching row dicts
          - "count": number of matches found
        Plus a "summary" key with total hit counts.
        """
        results: dict[str, Any] = {}
        total_hits = 0

        for table in _TABLE_DEFS:
            if table == "damages_calculation":
                rows = self._get_all(table, limit=100)
            else:
                rows = self._search_table(table, entity, limit=limit)

            count = len(rows)
            total_hits += count
            results[table] = {"rows": rows, "count": count}

        results["summary"] = {
            "entity": entity,
            "total_hits": total_hits,
            "tables_searched": len(_TABLE_DEFS),
            "tables_with_hits": sum(
                1 for t in _TABLE_DEFS if results[t]["count"] > 0
            ),
        }
        return results

    def entity_profile(self, name: str, limit: int = 30) -> dict:
        """
        Build a complete intelligence profile for any person/entity.

        Searches adversary_profiles, impeachment_matrix, contradiction_map,
        timeline_events, evidence_quotes, judicial_violations, and causal_chains.
        """
        profile: dict[str, Any] = {"name": name}

        # Adversary profile (exact name match preferred, then LIKE)
        if self._schema.exists("adversary_profiles") and self._schema.has_column("adversary_profiles", "name"):
            try:
                exact = self._conn.execute(
                    "SELECT * FROM adversary_profiles WHERE name = ? LIMIT 5",
                    (name,),
                ).fetchall()
                if exact:
                    profile["adversary_profile"] = [dict(r) for r in exact]
                else:
                    profile["adversary_profile"] = self._search_table_like(
                        "adversary_profiles", name, limit=5
                    )
            except Exception:
                profile["adversary_profile"] = []
        else:
            profile["adversary_profile"] = []

        # Impeachment items
        profile["impeachment"] = self._search_table(
            "impeachment_matrix", name, limit=limit
        )

        # Contradictions
        profile["contradictions"] = self._search_table(
            "contradiction_map", name, limit=limit
        )

        # Timeline events mentioning them
        profile["timeline"] = self._search_table(
            "timeline_events", name, limit=limit
        )

        # Evidence quotes mentioning them
        profile["evidence"] = self._search_table(
            "evidence_quotes", name, limit=limit
        )

        # Judicial violations (meaningful for judges)
        profile["judicial_violations"] = self._search_table(
            "judicial_violations", name, limit=limit
        )

        # Causal chains involving them
        profile["causal_chains"] = self._search_table(
            "causal_chains", name, limit=limit
        )

        # Summary counts
        profile["counts"] = {
            k: len(profile[k])
            for k in (
                "adversary_profile", "impeachment", "contradictions",
                "timeline", "evidence", "judicial_violations", "causal_chains",
            )
        }
        profile["total_items"] = sum(profile["counts"].values())

        return profile

    def filing_intel(self, lane: str, limit: int = 50) -> dict:
        """
        Gather ALL intelligence for a filing lane (A, B, C, D, E, F).

        Returns evidence, authorities, IRAC analyses, impeachment items,
        contradictions, damages, rebuttals, and timeline events filtered
        by lane.
        """
        intel: dict[str, Any] = {"lane": lane}

        # Evidence quotes for this lane
        evidence = self._lane_filter("evidence_quotes", lane, limit=limit)
        intel["evidence"] = {
            "count": len(evidence),
            "top": evidence[:10],
        }

        # Authority chains for this lane
        authorities = self._lane_filter("authority_chains_v2", lane, limit=limit)
        intel["authorities"] = {
            "count": len(authorities),
            "items": authorities,
        }

        # IRAC analyses for this lane
        iracs = self._lane_filter("irac_analyses", lane, limit=limit)
        intel["irac_analyses"] = {
            "count": len(iracs),
            "items": iracs,
        }

        # Impeachment items for this lane
        impeach = self._lane_filter("impeachment_matrix", lane, limit=limit)
        intel["impeachment"] = {
            "count": len(impeach),
            "items": impeach,
        }

        # Contradictions for this lane
        contras = self._lane_filter("contradiction_map", lane, limit=limit)
        intel["contradictions"] = {
            "count": len(contras),
            "items": contras,
        }

        # Damages for this lane
        damages = self._lane_filter("damages_calculation", lane, limit=100)
        intel["damages"] = {
            "count": len(damages),
            "items": damages,
        }

        # Rebuttals for this lane
        rebuttals = self._lane_filter("rebuttal_matrix", lane, limit=limit)
        intel["rebuttals"] = {
            "count": len(rebuttals),
            "items": rebuttals,
        }

        # Timeline events for this lane
        timeline = self._lane_filter("timeline_events", lane, limit=limit)
        intel["timeline"] = {
            "count": len(timeline),
            "items": timeline,
        }

        # Causal chains for this lane
        causal = self._lane_filter("causal_chains", lane, limit=limit)
        intel["causal_chains"] = {
            "count": len(causal),
            "items": causal,
        }

        # Judicial violations for this lane
        jv = self._lane_filter("judicial_violations", lane, limit=limit)
        intel["judicial_violations"] = {
            "count": len(jv),
            "items": jv,
        }

        # Summary
        intel["summary"] = {
            "lane": lane,
            "total_items": sum(
                intel[k]["count"]
                for k in (
                    "evidence", "authorities", "irac_analyses", "impeachment",
                    "contradictions", "damages", "rebuttals", "timeline",
                    "causal_chains", "judicial_violations",
                )
            ),
            "categories_with_data": sum(
                1
                for k in (
                    "evidence", "authorities", "irac_analyses", "impeachment",
                    "contradictions", "damages", "rebuttals", "timeline",
                    "causal_chains", "judicial_violations",
                )
                if intel[k]["count"] > 0
            ),
        }
        return intel

    def health(self) -> dict:
        """
        Row counts for all engine output tables using a single consolidated
        query with subqueries. Also reports table existence and FTS5 status.
        """
        # Build a single mega-query with subqueries for every table that exists
        existing_tables = [t for t in _HEALTH_TABLES if self._schema.exists(t)]

        if not existing_tables:
            return {
                "status": "error",
                "message": "No engine tables found in database",
                "tables": {},
            }

        subqueries = ", ".join(
            f"(SELECT COUNT(*) FROM [{t}]) AS [{t}]" for t in existing_tables
        )
        sql = f"SELECT {subqueries}"

        try:
            row = self._conn.execute(sql).fetchone()
        except Exception as exc:
            # Fallback: query one-by-one
            counts = {}
            for t in existing_tables:
                counts[t] = self._count_table(t)
            return {
                "status": "degraded",
                "message": f"Consolidated query failed ({exc}); used per-table fallback",
                "tables": counts,
                "total_rows": sum(counts.values()),
            }

        counts = {t: row[t] for t in existing_tables}
        total = sum(counts.values())

        # Check which FTS5 indexes are live
        fts_status = {}
        for defn in _TABLE_DEFS.values():
            fts = defn.get("fts")
            if fts:
                fts_status[fts] = self._schema.fts_exists(fts)

        # Missing tables
        missing = [t for t in _HEALTH_TABLES if not self._schema.exists(t)]

        return {
            "status": "healthy" if not missing else "partial",
            "tables": counts,
            "total_rows": total,
            "fts5_indexes": fts_status,
            "missing_tables": missing,
            "table_count": len(existing_tables),
        }


# ------------------------------------------------------------------
# CLI demo
# ------------------------------------------------------------------

def _truncate(text: str | None, maxlen: int = 80) -> str:
    if not text:
        return ""
    t = str(text).replace("\n", " ").strip()
    return t[:maxlen] + "..." if len(t) > maxlen else t


def main() -> None:
    """Demonstrate all 4 orchestrator methods."""
    import json
    from datetime import date

    sep_days = (date.today() - date(2025, 7, 29)).days
    print(f"=== Cross-Engine Orchestrator Demo (separation day {sep_days}) ===\n")

    with Orchestrator() as orch:
        # 1. Health check
        print("─" * 60)
        print("1. HEALTH CHECK")
        print("─" * 60)
        h = orch.health()
        print(f"   Status: {h['status']}")
        print(f"   Total rows across {h.get('table_count', '?')} tables: "
              f"{h.get('total_rows', 0):,}")
        for tbl, cnt in h.get("tables", {}).items():
            print(f"   {tbl:30s} {cnt:>8,}")
        fts = h.get("fts5_indexes", {})
        if fts:
            print(f"\n   FTS5 indexes: {sum(fts.values())}/{len(fts)} live")
            for idx, ok in fts.items():
                print(f"     {'✓' if ok else '✗'} {idx}")
        missing = h.get("missing_tables", [])
        if missing:
            print(f"\n   Missing tables: {', '.join(missing)}")
        print()

        # 2. Fuse query
        print("─" * 60)
        print("2. FUSE: 'McNeill'")
        print("─" * 60)
        fused = orch.fuse("McNeill")
        summ = fused["summary"]
        print(f"   Entity: {summ['entity']}")
        print(f"   Total hits: {summ['total_hits']}")
        print(f"   Tables with hits: {summ['tables_with_hits']}/{summ['tables_searched']}")
        for tbl in _TABLE_DEFS:
            c = fused[tbl]["count"]
            if c > 0:
                sample = fused[tbl]["rows"][0] if fused[tbl]["rows"] else {}
                # Pick a representative text field
                preview = ""
                for col in ("quote_text", "event_description", "contradiction_text",
                            "description", "claim_text", "cause_event",
                            "issue", "name", "primary_citation", "category"):
                    if col in sample:
                        preview = _truncate(sample[col])
                        break
                print(f"   {tbl:30s} {c:>4} hits  │ {preview}")
            else:
                print(f"   {tbl:30s}    0 hits")
        print()

        # 3. Entity profile
        print("─" * 60)
        print("3. ENTITY PROFILE: 'Watson'")
        print("─" * 60)
        prof = orch.entity_profile("Watson")
        print(f"   Name: {prof['name']}")
        print(f"   Total items: {prof['total_items']}")
        for k, v in prof["counts"].items():
            print(f"   {k:30s} {v:>4}")
        # Show a sample impeachment if any
        if prof["impeachment"]:
            item = prof["impeachment"][0]
            print(f"\n   Sample impeachment:")
            print(f"     {_truncate(item.get('evidence_summary', ''), 120)}")
        print()

        # 4. Filing intel
        print("─" * 60)
        print("4. FILING INTEL: Lane A (Custody)")
        print("─" * 60)
        intel = orch.filing_intel("A")
        s = intel["summary"]
        print(f"   Lane: {s['lane']}")
        print(f"   Total items: {s['total_items']}")
        print(f"   Categories with data: {s['categories_with_data']}/10")
        for k in ("evidence", "authorities", "irac_analyses", "impeachment",
                   "contradictions", "damages", "rebuttals", "timeline",
                   "causal_chains", "judicial_violations"):
            print(f"   {k:30s} {intel[k]['count']:>4}")
        print()

    print("=== Orchestrator demo complete ===")


if __name__ == "__main__":
    main()
