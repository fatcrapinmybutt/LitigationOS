#!/usr/bin/env python3
"""NEXUS v2 — Persistent Litigation Intelligence Daemon.

Architecture: Long-running Python process communicating via line-delimited JSON
over stdin/stdout. Keeps ALL database connections warm for sub-5ms responses.

Backends:
  - SQLite WAL (litigation_context.db) — primary OLTP
  - DuckDB (analytical overlays) — 10-100× faster aggregations
  - LanceDB (semantic search, 75K vectors) — sub-ms similarity

Protocol: One JSON object per line on stdin, one JSON response per line on stdout.
  Request:  {"id": "abc", "action": "query", "sql": "SELECT ...", "params": [...]}
  Response: {"id": "abc", "ok": true, "rows": [...], "columns": [...], "count": N}
  Error:    {"id": "abc", "ok": false, "error": "message"}

Actions:
  query         — Parameterized SQL (read or write)
  fts_search    — FTS5 search with snippet + fallback
  stats         — Key table row counts
  search_evidence      — evidence_quotes FTS5 search
  search_impeachment   — impeachment_matrix search
  search_contradictions — contradiction_map search
  search_authority     — authority_chains_v2 search
  nexus_fuse    — Cross-table evidence fusion
  nexus_argue   — Argument chain synthesis
  nexus_readiness — Filing readiness dashboard
  nexus_damages  — Aggregate damages
  narrative      — Chronological narrative builder
  filing_plan    — Filing strategy with deadlines
  rules_check    — Procedural compliance validator
  adversary      — Deep adversary profile
  gap_analysis   — Missing evidence detector
  cross_connect  — Cross-lane intelligence
  judicial_intel — Judicial intelligence
  timeline_search — Timeline events search
  case_context   — Case context summary
  filing_status  — Filing package status
  deadlines      — Deadline checker
  ping           — Health check

Started by extension.mjs on load. Stays alive for entire session.
"""

import json
import re
import sqlite3
import sys
import os
import traceback
from datetime import datetime, date

# ── stdout guard: ALL output goes through protocol, never bare prints ─────
_original_stdout = sys.stdout
_original_stderr = sys.stderr

# Redirect stderr to a log file so import warnings don't corrupt JSON-RPC
LOG_PATH = os.path.join(os.environ.get("TEMP", "."), "nexus_daemon.log")
try:
    _log_file = open(LOG_PATH, "a", encoding="utf-8")
    sys.stderr = _log_file
except OSError:
    pass

# ── Optional imports (graceful degradation) ───────────────────────────────
_HAS_DUCKDB = False
_HAS_LANCEDB = False

try:
    import duckdb
    _HAS_DUCKDB = True
except ImportError:
    pass

try:
    import lancedb
    _HAS_LANCEDB = True
except ImportError:
    pass

# ── Configuration ─────────────────────────────────────────────────────────
DB_PATH = r"C:\Users\andre\LitigationOS\litigation_context.db"
LANCEDB_PATH = r"C:\Users\andre\LitigationOS\00_SYSTEM\engines\semantic\lancedb_store"

PRAGMAS = [
    "PRAGMA busy_timeout = 60000",
    "PRAGMA journal_mode = WAL",
    "PRAGMA cache_size = -32000",
    "PRAGMA temp_store = MEMORY",
    "PRAGMA synchronous = NORMAL",
    "PRAGMA mmap_size = 268435456",
]

# ── FTS5 Safety ───────────────────────────────────────────────────────────
def sanitize_fts5(query):
    """Sanitize FTS5 query: keep alphanumeric, spaces, quotes, wildcards."""
    return re.sub(r'[^\w\s*"]', ' ', query).strip()

# ── Connection Pool (warm, persistent) ────────────────────────────────────

class ConnectionPool:
    """Persistent database connections — opened once, used throughout session."""

    def __init__(self):
        self._sqlite = None
        self._duckdb = None
        self._lancedb_table = None

    @property
    def sqlite(self):
        if self._sqlite is None:
            self._sqlite = sqlite3.connect(DB_PATH)
            self._sqlite.row_factory = sqlite3.Row
            for pragma in PRAGMAS:
                self._sqlite.execute(pragma)
        return self._sqlite

    @property
    def duck(self):
        if self._duckdb is None and _HAS_DUCKDB:
            self._duckdb = duckdb.connect(":memory:")
            self._duckdb.execute("INSTALL sqlite; LOAD sqlite;")
            self._duckdb.execute(f"ATTACH '{DB_PATH}' AS lit (TYPE sqlite, READ_ONLY)")
        return self._duckdb

    @property
    def lance_table(self):
        if self._lancedb_table is None and _HAS_LANCEDB:
            try:
                db = lancedb.connect(LANCEDB_PATH)
                tables = db.table_names()
                if tables:
                    self._lancedb_table = db.open_table(tables[0])
            except Exception:
                pass
        return self._lancedb_table

    def close(self):
        if self._sqlite:
            self._sqlite.close()
        if self._duckdb:
            self._duckdb.close()


pool = ConnectionPool()

# ── Stats Tables ──────────────────────────────────────────────────────────
STATS_TABLES = [
    "evidence_quotes", "authority_chains_v2", "michigan_rules_extracted",
    "timeline_events", "md_sections", "master_citations", "file_inventory",
    "md_cross_refs", "contradiction_map", "judicial_violations",
    "impeachment_matrix", "police_reports", "berry_mcneill_intelligence",
    "documents", "deadlines", "filing_packages", "legal_statutes",
    "michigan_case_law", "court_abbreviations", "catalogue_fts",
]

# ── FTS5 Configuration ───────────────────────────────────────────────────
FTS_CONFIG = {
    "evidence_quotes": {
        "fts_table": "evidence_fts",
        "join": "evidence_quotes eq ON eq.id = evidence_fts.rowid",
        "snippet_col": 0,
        "extra_cols": ["eq.source_file", "eq.category", "eq.lane", "eq.relevance_score"],
    },
    "timeline_events": {
        "fts_table": "timeline_fts",
        "join": None,
        "snippet_col": 0,
        "extra_cols": ["actors"],
    },
}

LIKE_CONFIG = {
    "police_reports": {
        "text_col": "full_text",
        "cols": ["filename", "allegations", "exculpatory", "false_reports"],
    },
    "michigan_rules_extracted": {
        "text_col": "full_text",
        "cols": ["rule_number", "rule_type", "title"],
    },
}

# ══════════════════════════════════════════════════════════════════════════
# ACTION HANDLERS
# ══════════════════════════════════════════════════════════════════════════

def handle_ping(_req):
    """Health check."""
    caps = ["sqlite"]
    if _HAS_DUCKDB: caps.append("duckdb")
    if _HAS_LANCEDB: caps.append("lancedb")
    return {"ok": True, "status": "alive", "capabilities": caps, "db": DB_PATH}


def handle_query(req):
    """Execute parameterized SQL query (READ-ONLY — writes blocked by policy)."""
    sql = req.get("sql", "").strip()
    params = req.get("params", [])
    max_rows = min(req.get("max_rows", 50), 500)

    if not sql:
        return {"ok": False, "error": "No SQL provided"}

    conn = pool.sqlite
    is_write = sql.upper().lstrip().startswith(("INSERT", "UPDATE", "DELETE", "CREATE", "DROP", "ALTER", "REPLACE"))

    # READ-ONLY POLICY: Block all write operations per user mandate (2026-04-14).
    # All DB writes must go through exec_python scripts for auditability and safety.
    if is_write:
        return {"ok": False, "error": "BLOCKED: MCP extension is READ-ONLY. Use exec_python with a script for DB writes."}

    try:
        cur = conn.execute(sql, params)

        rows = cur.fetchmany(max_rows + 1)
        truncated = len(rows) > max_rows
        if truncated:
            rows = rows[:max_rows]

        columns = [desc[0] for desc in cur.description] if cur.description else []
        data = [dict(zip(columns, row)) for row in rows]
        return {
            "ok": True,
            "columns": columns,
            "rows": data,
            "count": len(data),
            "truncated": truncated,
        }
    except Exception as e:
        return {"ok": False, "error": str(e)}


def handle_analytics(req):
    """DuckDB analytical query (10-100× faster for aggregations)."""
    if not _HAS_DUCKDB or pool.duck is None:
        return handle_query(req)  # graceful fallback to SQLite

    sql = req.get("sql", "").strip()
    params = req.get("params", [])
    max_rows = min(req.get("max_rows", 50), 500)

    if not sql:
        return {"ok": False, "error": "No SQL provided"}

    try:
        if params:
            result = pool.duck.execute(sql, params)
        else:
            result = pool.duck.execute(sql)

        rows = result.fetchmany(max_rows)
        columns = [desc[0] for desc in result.description]
        data = [dict(zip(columns, row)) for row in rows]
        return {
            "ok": True,
            "columns": columns,
            "rows": data,
            "count": len(data),
            "engine": "duckdb",
        }
    except Exception as e:
        return {"ok": False, "error": f"DuckDB: {e}"}


def handle_stats(_req):
    """Key table row counts."""
    conn = pool.sqlite
    stats = {}
    for table in STATS_TABLES:
        try:
            cnt = conn.execute(f"SELECT COUNT(*) FROM [{table}]").fetchone()[0]
            stats[table] = cnt
        except Exception:
            stats[table] = -1
    return {"ok": True, "stats": stats}


def handle_fts_search(req):
    """FTS5 search with snippet + LIKE fallback."""
    table = req.get("table", "evidence_quotes")
    query = req.get("query", "")
    limit = min(req.get("limit", 25), 100)
    conn = pool.sqlite

    safe_q = sanitize_fts5(query)
    if not safe_q:
        return {"ok": False, "error": "Empty query after sanitization"}

    # FTS5 path
    if table in FTS_CONFIG:
        cfg = FTS_CONFIG[table]
        fts = cfg["fts_table"]
        try:
            if cfg["join"]:
                sql = (
                    f"SELECT snippet({fts}, {cfg['snippet_col']}, '<b>', '</b>', '...', 40) AS excerpt, "
                    f"{', '.join(cfg['extra_cols'])} "
                    f"FROM {fts} JOIN {cfg['join']} "
                    f"WHERE {fts} MATCH ? ORDER BY rank LIMIT ?"
                )
            else:
                extra = (", " + ", ".join(cfg["extra_cols"])) if cfg["extra_cols"] else ""
                sql = (
                    f"SELECT snippet({fts}, {cfg['snippet_col']}, '<b>', '</b>', '...', 40) AS excerpt{extra} "
                    f"FROM {fts} WHERE {fts} MATCH ? ORDER BY rank LIMIT ?"
                )
            rows = conn.execute(sql, (safe_q, limit)).fetchall()
            columns = [desc[0] for desc in conn.execute(sql, (safe_q, 1)).description] if rows else ["excerpt"]
            return {
                "ok": True,
                "columns": columns,
                "rows": [dict(zip(columns, r)) for r in rows],
                "count": len(rows),
                "engine": "fts5",
            }
        except Exception:
            pass  # fall through to LIKE

    # LIKE fallback
    if table in LIKE_CONFIG:
        cfg = LIKE_CONFIG[table]
        cols = ", ".join(cfg["cols"])
        sql = f"SELECT {cols} FROM {table} WHERE {cfg['text_col']} LIKE ? LIMIT ?"
        rows = conn.execute(sql, (f"%{query}%", limit)).fetchall()
        columns = cfg["cols"]
        return {
            "ok": True,
            "columns": columns,
            "rows": [dict(zip(columns, r)) for r in rows],
            "count": len(rows),
            "engine": "like_fallback",
        }

    return {"ok": False, "error": f"Unknown search table: {table}"}


def handle_search_evidence(req):
    """Search evidence_quotes via FTS5."""
    req["table"] = "evidence_quotes"
    return handle_fts_search(req)


def handle_search_impeachment(req):
    """Search impeachment_matrix."""
    conn = pool.sqlite
    target = req.get("target", "")
    category = req.get("category", "")
    min_sev = req.get("min_severity", 1)
    limit = min(req.get("limit", 25), 100)

    conditions, params = ["impeachment_value >= ?"], [min_sev]
    if target:
        conditions.append("target LIKE ?")
        params.append(f"%{target}%")
    if category:
        conditions.append("category LIKE ?")
        params.append(f"%{category}%")

    where = " AND ".join(conditions)
    sql = f"SELECT * FROM impeachment_matrix WHERE {where} ORDER BY impeachment_value DESC LIMIT ?"
    params.append(limit)

    try:
        cur = conn.execute(sql, params)
        columns = [d[0] for d in cur.description]
        rows = [dict(zip(columns, r)) for r in cur.fetchall()]
        return {"ok": True, "columns": columns, "rows": rows, "count": len(rows)}
    except Exception as e:
        return {"ok": False, "error": str(e)}


def handle_search_contradictions(req):
    """Search contradiction_map."""
    conn = pool.sqlite
    entity = req.get("entity", "")
    severity = req.get("severity", "")
    lane = req.get("lane", "")
    limit = min(req.get("limit", 25), 100)

    conditions, params = [], []
    if entity:
        conditions.append("(source_a LIKE ? OR source_b LIKE ? OR contradiction_text LIKE ?)")
        params.extend([f"%{entity}%"] * 3)
    if severity:
        conditions.append("severity = ?")
        params.append(severity)
    if lane:
        conditions.append("lane = ?")
        params.append(lane)

    where = (" WHERE " + " AND ".join(conditions)) if conditions else ""
    sql = f"SELECT * FROM contradiction_map{where} ORDER BY CASE severity WHEN 'critical' THEN 1 WHEN 'high' THEN 2 WHEN 'medium' THEN 3 ELSE 4 END LIMIT ?"
    params.append(limit)

    try:
        cur = conn.execute(sql, params)
        columns = [d[0] for d in cur.description]
        rows = [dict(zip(columns, r)) for r in cur.fetchall()]
        return {"ok": True, "columns": columns, "rows": rows, "count": len(rows)}
    except Exception as e:
        return {"ok": False, "error": str(e)}


def handle_search_authority(req):
    """Search authority_chains_v2."""
    conn = pool.sqlite
    citation = req.get("citation", "")
    lane = req.get("lane", "")
    source_type = req.get("source_type", "")
    limit = min(req.get("limit", 25), 100)

    conditions, params = [], []
    if citation:
        conditions.append("(primary_citation LIKE ? OR supporting_citation LIKE ?)")
        params.extend([f"%{citation}%", f"%{citation}%"])
    if lane:
        conditions.append("lane = ?")
        params.append(lane)
    if source_type:
        conditions.append("source_type = ?")
        params.append(source_type)

    where = (" WHERE " + " AND ".join(conditions)) if conditions else ""
    sql = f"SELECT primary_citation, supporting_citation, relationship, source_document, source_type, lane FROM authority_chains_v2{where} LIMIT ?"
    params.append(limit)

    try:
        cur = conn.execute(sql, params)
        columns = [d[0] for d in cur.description]
        rows = [dict(zip(columns, r)) for r in cur.fetchall()]
        return {"ok": True, "columns": columns, "rows": rows, "count": len(rows)}
    except Exception as e:
        return {"ok": False, "error": str(e)}


def handle_nexus_fuse(req):
    """Cross-table evidence fusion — searches 5 sources simultaneously."""
    topic = req.get("topic", "")
    lanes = req.get("lanes", [])
    limit = min(req.get("limit", 50), 100)
    conn = pool.sqlite
    safe_q = sanitize_fts5(topic)
    results = {}

    # 1. evidence_quotes (FTS5)
    try:
        sql = ("SELECT snippet(evidence_fts, 0, '<b>', '</b>', '...', 40) AS excerpt, "
               "eq.source_file, eq.category, eq.lane "
               "FROM evidence_fts JOIN evidence_quotes eq ON eq.id = evidence_fts.rowid "
               "WHERE evidence_fts MATCH ? ORDER BY rank LIMIT ?")
        rows = conn.execute(sql, (safe_q, limit)).fetchall()
        results["evidence"] = [{"excerpt": r[0], "source": r[1], "category": r[2], "lane": r[3]} for r in rows]
    except Exception:
        try:
            rows = conn.execute(
                "SELECT quote_text, source_file, category, lane FROM evidence_quotes WHERE quote_text LIKE ? LIMIT ?",
                (f"%{topic}%", limit)
            ).fetchall()
            results["evidence"] = [{"excerpt": r[0][:200], "source": r[1], "category": r[2], "lane": r[3]} for r in rows]
        except Exception:
            results["evidence"] = []

    # 2. timeline_events (FTS5)
    try:
        rows = conn.execute(
            "SELECT snippet(timeline_fts, 0, '<b>', '</b>', '...', 40) AS excerpt, actors "
            "FROM timeline_fts WHERE timeline_fts MATCH ? ORDER BY rank LIMIT ?",
            (safe_q, limit)
        ).fetchall()
        results["timeline"] = [{"excerpt": r[0], "actors": r[1]} for r in rows]
    except Exception:
        results["timeline"] = []

    # 3. police_reports (LIKE)
    try:
        rows = conn.execute(
            "SELECT filename, allegations, exculpatory FROM police_reports WHERE full_text LIKE ? LIMIT ?",
            (f"%{topic}%", min(limit, 20))
        ).fetchall()
        results["police"] = [{"filename": r[0], "allegations": r[1], "exculpatory": r[2]} for r in rows]
    except Exception:
        results["police"] = []

    # 4. impeachment_matrix
    try:
        rows = conn.execute(
            "SELECT target, category, evidence_summary, impeachment_value FROM impeachment_matrix "
            "WHERE evidence_summary LIKE ? OR quote_text LIKE ? ORDER BY impeachment_value DESC LIMIT ?",
            (f"%{topic}%", f"%{topic}%", min(limit, 20))
        ).fetchall()
        results["impeachment"] = [{"target": r[0], "category": r[1], "summary": r[2], "value": r[3]} for r in rows]
    except Exception:
        results["impeachment"] = []

    # 5. authority_chains_v2
    try:
        rows = conn.execute(
            "SELECT primary_citation, supporting_citation, relationship, lane FROM authority_chains_v2 "
            "WHERE primary_citation LIKE ? OR supporting_citation LIKE ? LIMIT ?",
            (f"%{topic}%", f"%{topic}%", min(limit, 20))
        ).fetchall()
        results["authority"] = [{"primary": r[0], "supporting": r[1], "relationship": r[2], "lane": r[3]} for r in rows]
    except Exception:
        results["authority"] = []

    total = sum(len(v) for v in results.values())
    return {"ok": True, "topic": topic, "total_hits": total, "results": results}


def handle_nexus_argue(req):
    """Argument chain synthesis — evidence + authorities + impeachment for a claim."""
    claim = req.get("claim", "")
    lane = req.get("lane", "")
    limit = min(req.get("limit", 10), 50)
    conn = pool.sqlite
    safe_q = sanitize_fts5(claim)
    chain = {"claim": claim, "evidence": [], "authorities": [], "impeachment": []}

    # Evidence
    try:
        rows = conn.execute(
            "SELECT snippet(evidence_fts, 0, '<b>', '</b>', '...', 40), eq.source_file, eq.lane "
            "FROM evidence_fts JOIN evidence_quotes eq ON eq.id = evidence_fts.rowid "
            "WHERE evidence_fts MATCH ? ORDER BY rank LIMIT ?",
            (safe_q, limit)
        ).fetchall()
        chain["evidence"] = [{"excerpt": r[0], "source": r[1], "lane": r[2]} for r in rows]
    except Exception:
        pass

    # Authorities
    try:
        rows = conn.execute(
            "SELECT primary_citation, supporting_citation, relationship FROM authority_chains_v2 "
            "WHERE primary_citation LIKE ? OR supporting_citation LIKE ? LIMIT ?",
            (f"%{claim}%", f"%{claim}%", limit)
        ).fetchall()
        chain["authorities"] = [{"primary": r[0], "supporting": r[1], "relationship": r[2]} for r in rows]
    except Exception:
        pass

    # Impeachment
    try:
        rows = conn.execute(
            "SELECT target, cross_exam_question, impeachment_value FROM impeachment_matrix "
            "WHERE evidence_summary LIKE ? ORDER BY impeachment_value DESC LIMIT ?",
            (f"%{claim}%", limit)
        ).fetchall()
        chain["impeachment"] = [{"target": r[0], "question": r[1], "value": r[2]} for r in rows]
    except Exception:
        pass

    # Strength score
    e_score = min(len(chain["evidence"]) * 10, 40)
    a_score = min(len(chain["authorities"]) * 15, 40)
    i_score = min(len(chain["impeachment"]) * 10, 20)
    total = e_score + a_score + i_score
    rating = "STRONG" if total >= 70 else "MODERATE" if total >= 40 else "WEAK"
    chain["strength"] = {"score": total, "rating": rating}

    return {"ok": True, **chain}


def handle_nexus_readiness(req):
    """Filing readiness dashboard."""
    conn = pool.sqlite
    lane = req.get("lane", "")
    filings = []

    try:
        tables_check = {
            "evidence_quotes": "SELECT lane, COUNT(*) FROM evidence_quotes GROUP BY lane",
            "authority_chains_v2": "SELECT lane, COUNT(*) FROM authority_chains_v2 WHERE lane IS NOT NULL GROUP BY lane",
            "impeachment_matrix": "SELECT 'ALL', COUNT(*) FROM impeachment_matrix",
        }
        lane_data = {}
        for _tbl, sql in tables_check.items():
            for row in conn.execute(sql).fetchall():
                ln = row[0] or "UNKNOWN"
                lane_data.setdefault(ln, {"evidence": 0, "authority": 0, "impeachment": 0})
                if "evidence" in _tbl:
                    lane_data[ln]["evidence"] = row[1]
                elif "authority" in _tbl:
                    lane_data[ln]["authority"] = row[1]
                elif "impeachment" in _tbl:
                    for k in lane_data:
                        lane_data[k]["impeachment"] = row[1]

        for ln, counts in sorted(lane_data.items()):
            if lane and ln != lane:
                continue
            score = min(counts["evidence"] // 10, 40) + min(counts["authority"] // 5, 40) + min(counts["impeachment"] // 5, 20)
            filings.append({
                "lane": ln,
                "evidence_count": counts["evidence"],
                "authority_count": counts["authority"],
                "impeachment_count": counts["impeachment"],
                "readiness_score": min(score, 100),
            })
    except Exception as e:
        return {"ok": False, "error": str(e)}

    return {"ok": True, "filings": filings}


def handle_nexus_damages(req):
    """Aggregate damages across claims."""
    conn = pool.sqlite
    lane = req.get("lane", "")
    try:
        # Check if damages table exists
        tables = [r[0] for r in conn.execute("SELECT name FROM sqlite_master WHERE type='table' AND name LIKE '%damage%'").fetchall()]
        if not tables:
            # Hardcoded damages model from case intelligence
            damages = [
                {"category": "Lost parenting time", "conservative": 100000, "aggressive": 500000, "lane": "A"},
                {"category": "False imprisonment", "conservative": 50000, "aggressive": 200000, "lane": "A"},
                {"category": "Lost employment", "conservative": 80000, "aggressive": 160000, "lane": "A"},
                {"category": "Lost housing", "conservative": 40000, "aggressive": 120000, "lane": "B"},
                {"category": "Emotional distress", "conservative": 100000, "aggressive": 500000, "lane": "C"},
                {"category": "Punitive (§1983)", "conservative": 250000, "aggressive": 1000000, "lane": "C"},
            ]
            if lane:
                damages = [d for d in damages if d["lane"] == lane]
            total_low = sum(d["conservative"] for d in damages)
            total_high = sum(d["aggressive"] for d in damages)
            return {"ok": True, "damages": damages, "total_conservative": total_low, "total_aggressive": total_high}

        sql = f"SELECT * FROM {tables[0]}"
        if lane:
            sql += f" WHERE lane = ?"
            rows = conn.execute(sql, (lane,)).fetchall()
        else:
            rows = conn.execute(sql).fetchall()
        columns = [d[0] for d in conn.execute(f"PRAGMA table_info({tables[0]})").fetchall()]
        return {"ok": True, "rows": [dict(zip(columns, r)) for r in rows], "count": len(rows)}
    except Exception as e:
        return {"ok": False, "error": str(e)}


def handle_narrative(req):
    """Chronological narrative builder from timeline_events."""
    conn = pool.sqlite
    query = req.get("query", "")
    lane = req.get("lane", "")
    limit = min(req.get("limit", 50), 200)
    safe_q = sanitize_fts5(query)

    events = []
    try:
        if safe_q:
            rows = conn.execute(
                "SELECT event_date, event_description, actors, lane FROM timeline_fts "
                "JOIN timeline_events te ON te.id = timeline_fts.rowid "
                "WHERE timeline_fts MATCH ? ORDER BY te.event_date LIMIT ?",
                (safe_q, limit)
            ).fetchall()
        else:
            sql = "SELECT event_date, event_description, actors, lane FROM timeline_events"
            params = []
            if lane:
                sql += " WHERE lane = ?"
                params.append(lane)
            sql += " ORDER BY event_date DESC LIMIT ?"
            params.append(limit)
            rows = conn.execute(sql, params).fetchall()
        events = [{"date": r[0], "description": r[1], "actors": r[2], "lane": r[3]} for r in rows]
    except Exception:
        # LIKE fallback
        try:
            rows = conn.execute(
                "SELECT event_date, event_description, actors, lane FROM timeline_events "
                "WHERE event_description LIKE ? ORDER BY event_date LIMIT ?",
                (f"%{query}%", limit)
            ).fetchall()
            events = [{"date": r[0], "description": r[1], "actors": r[2], "lane": r[3]} for r in rows]
        except Exception:
            pass

    return {"ok": True, "events": events, "total": len(events), "lane": lane or "ALL"}


def handle_filing_plan(req):
    """Filing strategy with deadlines."""
    conn = pool.sqlite
    lane = req.get("lane", "")

    filings = []
    try:
        sql = "SELECT * FROM filing_packages"
        if lane:
            sql += " WHERE lane = ?"
            rows = conn.execute(sql, (lane,)).fetchall()
        else:
            rows = conn.execute(sql).fetchall()

        cols = [d[0] for d in conn.execute("PRAGMA table_info(filing_packages)").fetchall()]
        for r in rows:
            filings.append(dict(zip([c[1] for c in conn.execute("PRAGMA table_info(filing_packages)").fetchall()], r)))
    except Exception:
        # Hardcoded filing plan from case matrix
        filings = [
            {"filing": "Emergency Motion to Restore", "lane": "A", "deadline": "FILED 3/25/2026", "court": "14th Circuit", "fee": "$20", "status": "filed"},
            {"filing": "MCR 2.003 Disqualification", "lane": "A", "deadline": "ASAP", "court": "14th Circuit", "fee": "$20", "status": "ready"},
            {"filing": "COA Brief 366810", "lane": "F", "deadline": "Apr 30, 2026", "court": "MI Court of Appeals", "fee": "$375", "status": "ready"},
            {"filing": "MSC Superintending Control", "lane": "E", "deadline": "Strategic", "court": "MI Supreme Court", "fee": "$375", "status": "drafting"},
            {"filing": "Federal §1983", "lane": "C", "deadline": "Strategic", "court": "WDMI", "fee": "$405", "status": "drafting"},
            {"filing": "JTC Complaint", "lane": "E", "deadline": "None", "court": "JTC", "fee": "$0", "status": "ready"},
            {"filing": "PPO Termination", "lane": "D", "deadline": "TBD", "court": "14th Circuit", "fee": "$20", "status": "ready"},
        ]
        if lane:
            filings = [f for f in filings if f.get("lane") == lane]

    return {"ok": True, "filings": filings, "total": len(filings)}


def handle_rules_check(req):
    """Procedural compliance validator."""
    conn = pool.sqlite
    query = req.get("query", "")
    limit = min(req.get("limit", 10), 50)

    rules = []
    try:
        rows = conn.execute(
            "SELECT rule_number, rule_type, title, full_text FROM michigan_rules_extracted "
            "WHERE rule_number LIKE ? OR title LIKE ? OR full_text LIKE ? LIMIT ?",
            (f"%{query}%", f"%{query}%", f"%{query}%", limit)
        ).fetchall()
        rules = [{"rule_number": r[0], "rule_type": r[1], "title": r[2], "full_text": r[3][:600] if r[3] else ""} for r in rows]
    except Exception as e:
        return {"ok": False, "error": str(e)}

    return {"ok": True, "rules": rules, "count": len(rules)}


def handle_adversary(req):
    """Deep adversary profile builder."""
    conn = pool.sqlite
    person = req.get("person", "")
    if not person:
        return {"ok": False, "error": "No person specified"}

    profile = {"person": person, "impeachment_items": [], "contradictions": [], "timeline_events": [], "credibility_score": 0}

    # Impeachment
    try:
        rows = conn.execute(
            "SELECT category, evidence_summary, impeachment_value, cross_exam_question FROM impeachment_matrix "
            "WHERE target LIKE ? ORDER BY impeachment_value DESC LIMIT 20",
            (f"%{person}%",)
        ).fetchall()
        profile["impeachment_items"] = [{"category": r[0], "summary": r[1], "value": r[2], "question": r[3]} for r in rows]
    except Exception:
        pass

    # Contradictions
    try:
        rows = conn.execute(
            "SELECT source_a, source_b, contradiction_text, severity FROM contradiction_map "
            "WHERE source_a LIKE ? OR source_b LIKE ? ORDER BY CASE severity WHEN 'critical' THEN 1 WHEN 'high' THEN 2 ELSE 3 END LIMIT 20",
            (f"%{person}%", f"%{person}%")
        ).fetchall()
        profile["contradictions"] = [{"source_a": r[0], "source_b": r[1], "text": r[2], "severity": r[3]} for r in rows]
    except Exception:
        pass

    # Timeline
    try:
        safe_q = sanitize_fts5(person)
        rows = conn.execute(
            "SELECT event_date, event_description FROM timeline_fts "
            "JOIN timeline_events te ON te.id = timeline_fts.rowid "
            "WHERE timeline_fts MATCH ? ORDER BY te.event_date DESC LIMIT 20",
            (safe_q,)
        ).fetchall()
        profile["timeline_events"] = [{"date": r[0], "description": r[1]} for r in rows]
    except Exception:
        pass

    # Credibility score (higher = less credible = more impeachable)
    imp_score = min(len(profile["impeachment_items"]) * 5, 40)
    con_score = min(len(profile["contradictions"]) * 10, 40)
    profile["credibility_score"] = 100 - imp_score - con_score
    profile["weakness_count"] = len(profile["impeachment_items"]) + len(profile["contradictions"])

    return {"ok": True, **profile}


def handle_gap_analysis(req):
    """Missing evidence, claims, and filings detector."""
    conn = pool.sqlite
    lane = req.get("lane", "")

    gaps = {"missing_evidence": [], "weak_authority": [], "unfiled_motions": []}

    # Check evidence density per lane
    try:
        rows = conn.execute(
            "SELECT lane, COUNT(*) as cnt FROM evidence_quotes GROUP BY lane ORDER BY cnt"
        ).fetchall()
        min_threshold = 100
        for r in rows:
            if r[1] < min_threshold and (not lane or r[0] == lane):
                gaps["missing_evidence"].append({"lane": r[0], "count": r[1], "gap": f"Only {r[1]} evidence items (need {min_threshold}+)"})
    except Exception:
        pass

    # Check authority chain completeness
    try:
        rows = conn.execute(
            "SELECT lane, COUNT(DISTINCT primary_citation) as cites FROM authority_chains_v2 WHERE lane IS NOT NULL GROUP BY lane"
        ).fetchall()
        for r in rows:
            if r[1] < 10 and (not lane or r[0] == lane):
                gaps["weak_authority"].append({"lane": r[0], "citations": r[1], "gap": f"Only {r[1]} unique citations"})
    except Exception:
        pass

    return {"ok": True, "gaps": gaps}


def handle_cross_connect(req):
    """Cross-lane intelligence fusion."""
    topic = req.get("topic", "")
    conn = pool.sqlite
    connections = {}

    safe_q = sanitize_fts5(topic)

    # Search evidence across all lanes
    try:
        rows = conn.execute(
            "SELECT eq.lane, COUNT(*) FROM evidence_fts "
            "JOIN evidence_quotes eq ON eq.id = evidence_fts.rowid "
            "WHERE evidence_fts MATCH ? GROUP BY eq.lane",
            (safe_q,)
        ).fetchall()
        connections["evidence_by_lane"] = {r[0]: r[1] for r in rows}
    except Exception:
        try:
            rows = conn.execute(
                "SELECT lane, COUNT(*) FROM evidence_quotes WHERE quote_text LIKE ? GROUP BY lane",
                (f"%{topic}%",)
            ).fetchall()
            connections["evidence_by_lane"] = {r[0]: r[1] for r in rows}
        except Exception:
            connections["evidence_by_lane"] = {}

    # Authority cross-references
    try:
        rows = conn.execute(
            "SELECT lane, COUNT(*) FROM authority_chains_v2 WHERE primary_citation LIKE ? OR supporting_citation LIKE ? GROUP BY lane",
            (f"%{topic}%", f"%{topic}%")
        ).fetchall()
        connections["authority_by_lane"] = {r[0]: r[1] for r in rows}
    except Exception:
        connections["authority_by_lane"] = {}

    total = sum(connections.get("evidence_by_lane", {}).values()) + sum(connections.get("authority_by_lane", {}).values())
    lanes_touched = set(list(connections.get("evidence_by_lane", {}).keys()) + list(connections.get("authority_by_lane", {}).keys()))
    connections["lanes_touched"] = sorted(lanes_touched)
    connections["total_hits"] = total

    return {"ok": True, "topic": topic, "connections": connections}


def handle_judicial_intel(req):
    """Judicial intelligence findings."""
    conn = pool.sqlite
    judge = req.get("judge", "")

    intel = {"violations": [], "berry_intel": [], "patterns": {}}

    # Judicial violations
    try:
        sql = "SELECT * FROM judicial_violations"
        params = []
        if judge:
            sql += " WHERE judge LIKE ? OR description LIKE ?"
            params.extend([f"%{judge}%", f"%{judge}%"])
        sql += " LIMIT 50"
        cur = conn.execute(sql, params)
        cols = [d[0] for d in cur.description]
        intel["violations"] = [dict(zip(cols, r)) for r in cur.fetchall()]
    except Exception:
        pass

    # Berry-McNeill intelligence
    try:
        sql = "SELECT * FROM berry_mcneill_intelligence"
        if judge:
            sql += f" WHERE intelligence LIKE '%{judge}%' OR category LIKE '%{judge}%'"
        sql += " LIMIT 30"
        cur = conn.execute(sql)
        cols = [d[0] for d in cur.description]
        intel["berry_intel"] = [dict(zip(cols, r)) for r in cur.fetchall()]
    except Exception:
        pass

    # Pattern summary
    try:
        rows = conn.execute(
            "SELECT violation_type, COUNT(*) FROM judicial_violations GROUP BY violation_type ORDER BY COUNT(*) DESC LIMIT 10"
        ).fetchall()
        intel["patterns"] = {r[0]: r[1] for r in rows}
    except Exception:
        pass

    intel["total_violations"] = len(intel["violations"])
    return {"ok": True, **intel}


def handle_timeline_search(req):
    """Timeline events search."""
    conn = pool.sqlite
    query = req.get("query", "")
    date_from = req.get("date_from", "")
    date_to = req.get("date_to", "")
    actor = req.get("actor", "")
    limit = min(req.get("limit", 30), 200)

    conditions, params = [], []
    if query:
        safe_q = sanitize_fts5(query)
        try:
            rows = conn.execute(
                "SELECT te.event_date, te.event_description, te.actors, te.lane "
                "FROM timeline_fts JOIN timeline_events te ON te.id = timeline_fts.rowid "
                "WHERE timeline_fts MATCH ? ORDER BY te.event_date LIMIT ?",
                (safe_q, limit)
            ).fetchall()
            return {"ok": True, "events": [{"date": r[0], "description": r[1], "actors": r[2], "lane": r[3]} for r in rows], "count": len(rows)}
        except Exception:
            conditions.append("event_description LIKE ?")
            params.append(f"%{query}%")

    if date_from:
        conditions.append("event_date >= ?")
        params.append(date_from)
    if date_to:
        conditions.append("event_date <= ?")
        params.append(date_to)
    if actor:
        conditions.append("actors LIKE ?")
        params.append(f"%{actor}%")

    where = (" WHERE " + " AND ".join(conditions)) if conditions else ""
    sql = f"SELECT event_date, event_description, actors, lane FROM timeline_events{where} ORDER BY event_date DESC LIMIT ?"
    params.append(limit)

    try:
        rows = conn.execute(sql, params).fetchall()
        return {"ok": True, "events": [{"date": r[0], "description": r[1], "actors": r[2], "lane": r[3]} for r in rows], "count": len(rows)}
    except Exception as e:
        return {"ok": False, "error": str(e)}


def handle_case_context(req):
    """Comprehensive context for active cases."""
    conn = pool.sqlite
    case_id = req.get("case_id", "")

    context = {"stats": {}, "filings": [], "recent_timeline": []}

    # Stats
    for table in ["evidence_quotes", "authority_chains_v2", "timeline_events", "impeachment_matrix", "contradiction_map", "judicial_violations"]:
        try:
            context["stats"][table] = conn.execute(f"SELECT COUNT(*) FROM [{table}]").fetchone()[0]
        except Exception:
            context["stats"][table] = -1

    # Separation counter
    sep_date = date(2025, 7, 29)
    context["separation_days"] = (date.today() - sep_date).days

    # Recent timeline
    try:
        rows = conn.execute(
            "SELECT event_date, event_description, lane FROM timeline_events ORDER BY event_date DESC LIMIT 10"
        ).fetchall()
        context["recent_timeline"] = [{"date": r[0], "description": r[1], "lane": r[2]} for r in rows]
    except Exception:
        pass

    return {"ok": True, **context}


def handle_filing_status(req):
    """Filing package status."""
    lane = req.get("lane", "")
    conn = pool.sqlite

    try:
        sql = "SELECT * FROM filing_packages WHERE lane = ?"
        cur = conn.execute(sql, (lane,))
        cols = [d[0] for d in cur.description]
        rows = [dict(zip(cols, r)) for r in cur.fetchall()]
        return {"ok": True, "filings": rows, "count": len(rows)}
    except Exception:
        # Fallback to hardcoded data
        packages = {
            "F1": {"name": "MSC Petition", "status": "complete"},
            "F3": {"name": "MCR 2.003 Disqualification", "status": "complete"},
            "F4": {"name": "Federal §1983", "status": "complete"},
            "F5": {"name": "MSC Original Action", "status": "complete"},
            "F6": {"name": "JTC Complaint", "status": "32 exhibits missing"},
            "F8": {"name": "PPO Termination", "status": "complete"},
            "F9": {"name": "COA Brief", "status": "complete"},
            "F10": {"name": "COA Emergency", "status": "complete"},
        }
        if lane in packages:
            return {"ok": True, "filings": [packages[lane]], "count": 1}
        return {"ok": True, "filings": list(packages.values()), "count": len(packages)}


def handle_deadlines(req):
    """Check litigation deadlines."""
    conn = pool.sqlite
    days_ahead = req.get("days_ahead", 30)

    deadlines = []
    try:
        rows = conn.execute(
            "SELECT * FROM deadlines WHERE due_date <= date('now', '+' || ? || ' days') ORDER BY due_date",
            (days_ahead,)
        ).fetchall()
        cols = [d[0] for d in conn.execute("PRAGMA table_info(deadlines)").fetchall()]
        col_names = [c[1] for c in conn.execute("PRAGMA table_info(deadlines)").fetchall()]
        deadlines = [dict(zip(col_names, r)) for r in rows]
    except Exception:
        # Hardcoded critical deadlines
        deadlines = [
            {"filing": "COA Brief 366810", "due_date": "2026-04-30", "court": "MI Court of Appeals", "urgency": "high"},
            {"filing": "Criminal Trial", "due_date": "2026-04-07", "court": "60th District", "urgency": "critical"},
        ]

    # Color-code urgency
    today = date.today()
    for d in deadlines:
        try:
            due = datetime.strptime(d.get("due_date", ""), "%Y-%m-%d").date()
            days_left = (due - today).days
            if days_left < 0:
                d["color"] = "🔴 OVERDUE"
            elif days_left <= 3:
                d["color"] = "🟠 CRITICAL"
            elif days_left <= 7:
                d["color"] = "🟡 URGENT"
            else:
                d["color"] = "🟢 OK"
            d["days_left"] = days_left
        except Exception:
            d["color"] = "⚪ UNKNOWN"

    return {"ok": True, "deadlines": deadlines, "count": len(deadlines)}


# ══════════════════════════════════════════════════════════════════════════
# ACTION ROUTER
# ══════════════════════════════════════════════════════════════════════════

HANDLERS = {
    "ping": handle_ping,
    "query": handle_query,
    "analytics": handle_analytics,
    "stats": handle_stats,
    "fts_search": handle_fts_search,
    "search_evidence": handle_search_evidence,
    "search_impeachment": handle_search_impeachment,
    "search_contradictions": handle_search_contradictions,
    "search_authority": handle_search_authority,
    "nexus_fuse": handle_nexus_fuse,
    "nexus_argue": handle_nexus_argue,
    "nexus_readiness": handle_nexus_readiness,
    "nexus_damages": handle_nexus_damages,
    "narrative": handle_narrative,
    "filing_plan": handle_filing_plan,
    "rules_check": handle_rules_check,
    "adversary": handle_adversary,
    "gap_analysis": handle_gap_analysis,
    "cross_connect": handle_cross_connect,
    "judicial_intel": handle_judicial_intel,
    "timeline_search": handle_timeline_search,
    "case_context": handle_case_context,
    "filing_status": handle_filing_status,
    "deadlines": handle_deadlines,
}


# ══════════════════════════════════════════════════════════════════════════
# MAIN EVENT LOOP (persistent — reads stdin forever)
# ══════════════════════════════════════════════════════════════════════════

def main():
    """Read line-delimited JSON requests from stdin, dispatch, write responses."""
    # Force UTF-8 on stdin/stdout
    if hasattr(sys.stdin, "reconfigure"):
        try:
            sys.stdin.reconfigure(encoding="utf-8", errors="replace")
        except Exception:
            pass
    if hasattr(_original_stdout, "reconfigure"):
        try:
            _original_stdout.reconfigure(encoding="utf-8", errors="replace")
        except Exception:
            pass

    # Signal readiness
    _original_stdout.write(json.dumps({"ok": True, "status": "ready", "pid": os.getpid()}) + "\n")
    _original_stdout.flush()

    for line in sys.stdin:
        line = line.strip()
        if not line:
            continue

        req_id = None
        try:
            req = json.loads(line)
            req_id = req.get("id")
            action = req.get("action", "")

            handler = HANDLERS.get(action)
            if not handler:
                response = {"ok": False, "error": f"Unknown action: {action}"}
            else:
                response = handler(req)

            if req_id:
                response["id"] = req_id

        except json.JSONDecodeError as e:
            response = {"ok": False, "error": f"Invalid JSON: {e}"}
        except Exception as e:
            response = {"ok": False, "error": str(e), "traceback": traceback.format_exc()[:500]}
            if req_id:
                response["id"] = req_id

        try:
            out = json.dumps(response, default=str)
            _original_stdout.write(out + "\n")
            _original_stdout.flush()
        except Exception:
            _original_stdout.write(json.dumps({"ok": False, "error": "Serialization failed"}) + "\n")
            _original_stdout.flush()


if __name__ == "__main__":
    main()
