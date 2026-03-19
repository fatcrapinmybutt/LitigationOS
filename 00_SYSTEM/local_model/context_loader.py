#!/usr/bin/env python3
"""
MBP LitigationOS -- Advanced Context Loader
=============================================
Connects to litigation_context.db and provides structured case intelligence.
100% local, 100% offline, graceful error handling on every operation.

Usage:
    from context_loader import ContextLoader
    ctx = ContextLoader()
    full = ctx.get_full_context()
    lane = ctx.get_lane_context("MEEK1")
    auth = ctx.get_authority_for("disqualification")
    timeline = ctx.get_timeline()
"""

from __future__ import annotations

import json
import logging
import os
import sqlite3
import sys
import time

logger = logging.getLogger(__name__)
from pathlib import Path
from typing import Any, Dict, List, Optional

sys.path.insert(0, str(Path(__file__).resolve().parent.parent if 'local_model' in str(Path(__file__)) else Path(__file__).resolve().parent))
try:
    from cycle_method import cycle_json, cycle_print
except ImportError:
    cycle_json = lambda obj, **kw: print(json.dumps(obj, default=str))
    cycle_print = print

DB_PATH = os.environ.get(
    "LITIGATION_DB_PATH",
    r"C:\Users\andre\LitigationOS\litigation_context.db",
)

# In-memory cache with TTL
_CACHE: Dict[str, Any] = {}
_CACHE_TS: Dict[str, float] = {}
_CACHE_TTL = 300  # 5 minutes


def _cache_get(key: str) -> Any:
    """Get from cache if fresh."""
    try:
        if key in _CACHE and (time.time() - _CACHE_TS.get(key, 0)) < _CACHE_TTL:
            return _CACHE[key]
    except Exception as e:
        logger.warning(f"Cache get failed for key '{key}': {e}")
    return None


def _cache_set(key: str, value: Any) -> None:
    """Set cache entry."""
    try:
        _CACHE[key] = value
        _CACHE_TS[key] = time.time()
    except Exception as e:
        logger.warning(f"Cache set failed for key '{key}': {e}")


class ContextLoader:
    """Loads structured case intelligence from litigation_context.db."""

    def __init__(self, db_path: str = DB_PATH):
        self.db_path = db_path
        self._conn: Optional[sqlite3.Connection] = None

    def _get_db(self) -> Optional[sqlite3.Connection]:
        """Get DB connection with WAL mode and row factory."""
        if self._conn is not None:
            try:
                self._conn.execute("SELECT 1")
                return self._conn
            except Exception as e:
                logger.warning(f"DB connection stale, reconnecting: {e}")
                self._conn = None

        try:
            self._conn = sqlite3.connect(self.db_path, timeout=30)
            self._conn.execute("PRAGMA journal_mode=WAL")
            self._conn.execute("PRAGMA cache_size=-65536")
            self._conn.execute("PRAGMA query_only=ON")
            self._conn.row_factory = sqlite3.Row
            return self._conn
        except Exception as e:
            logger.error(f"DB connection failed for '{self.db_path}': {e}")
            return None

    def _query(self, sql: str, params: tuple = ()) -> List[dict]:
        """Execute query and return list of dicts. Never raises."""
        try:
            conn = self._get_db()
            if not conn:
                return []
            rows = conn.execute(sql, params).fetchall()
            return [dict(r) for r in rows]
        except Exception as e:
            logger.warning(f"Query failed: {sql[:100]}... — {e}")
            return []

    def _query_one(self, sql: str, params: tuple = ()) -> Optional[dict]:
        """Execute query and return single dict or None."""
        results = self._query(sql, params)
        return results[0] if results else None

    def _scalar(self, sql: str, params: tuple = ()) -> Any:
        """Return single scalar value."""
        try:
            conn = self._get_db()
            if not conn:
                return None
            row = conn.execute(sql, params).fetchone()
            return row[0] if row else None
        except Exception as e:
            logger.warning(f"Scalar query failed: {sql[:100]}... — {e}")
            return None

    # ------------------------------------------------------------------
    def get_full_context(self) -> Dict[str, Any]:
        """
        Load comprehensive case intelligence.
        Returns structured dict of ALL case context.
        """
        cached = _cache_get("full_context")
        if cached is not None:
            return cached

        ctx: Dict[str, Any] = {
            "case_info": self._get_case_info(),
            "active_deadlines": self._get_active_deadlines(),
            "recent_docket_events": self._get_recent_docket_events(limit=20),
            "vehicles": self._get_vehicles(),
            "filing_readiness": self._get_filing_readiness(),
            "open_gaps": self._get_open_gaps(),
            "critical_risks": self._get_critical_risks(),
            "claim_summary": self._get_claim_summary(),
            "contradiction_count": self._scalar(
                "SELECT COUNT(*) FROM contradiction_map"
            ) or 0,
            "impeachment_count": self._scalar(
                "SELECT COUNT(*) FROM impeachment_items"
            ) or 0,
            "judicial_violations": self._get_judicial_violations(),
            "document_count": self._scalar(
                "SELECT COUNT(*) FROM documents"
            ) or 0,
            "evidence_quote_count": self._scalar(
                "SELECT COUNT(*) FROM evidence_quotes"
            ) or 0,
            "authority_rule_count": self._scalar(
                "SELECT COUNT(*) FROM auth_rules"
            ) or 0,
            "citation_count": self._scalar(
                "SELECT COUNT(*) FROM master_citations"
            ) or 0,
            "convergence": self._get_latest_convergence(),
            "loaded_at": time.strftime("%Y-%m-%dT%H:%M:%S"),
        }

        _cache_set("full_context", ctx)
        return ctx

    def _get_case_info(self) -> Dict[str, Any]:
        """Static case information."""
        return {
            "plaintiff": "Andrew Pigors",
            "defendant": "Tiffany Watson",
            "lanes": {
                "MEEK1": {
                    "case_number": "2023-5907-PP",
                    "court": "14th Circuit Court, Muskegon County",
                    "judge": "Hon. Jenny L. McNeill",
                    "type": "Custody/Parenting",
                },
                "MEEK2": {
                    "case_number": "2024-001507-DC",
                    "court": "14th Circuit Court, Muskegon County",
                    "judge": "Hon. Jenny L. McNeill",
                    "type": "Domestic",
                },
                "MEEK3": {
                    "case_number": "COA 366810",
                    "court": "Michigan Court of Appeals",
                    "judge": "Panel TBD",
                    "type": "Appeal of Right",
                },
                "MEEK4": {
                    "case_number": "MULTI",
                    "court": "Multiple Forums",
                    "judge": "Various",
                    "type": "Superintending/Complaints",
                },
            },
        }

    def _get_active_deadlines(self) -> List[dict]:
        """Get all non-satisfied deadlines ordered by date."""
        return self._query(
            "SELECT deadline_id, case_id, title, due_date_iso, basis, "
            "basis_authority, risk_if_missed, status "
            "FROM deadlines "
            "WHERE status NOT IN ('satisfied') "
            "ORDER BY due_date_iso ASC "
            "LIMIT 50"
        )

    def _get_recent_docket_events(self, limit: int = 20) -> List[dict]:
        """Get most recent docket events."""
        return self._query(
            "SELECT event_id, case_id, event_date_iso, title, event_type, summary "
            "FROM docket_events "
            "ORDER BY event_date_iso DESC "
            "LIMIT ?",
            (limit,),
        )

    def _get_vehicles(self) -> List[dict]:
        """Get all procedural vehicles."""
        return self._query(
            "SELECT vehicle_id, case_lane, title, forum, vehicle_type, "
            "objective, status, sbna_score "
            "FROM vehicles "
            "ORDER BY sbna_score DESC"
        )

    def _get_filing_readiness(self) -> List[dict]:
        """Get filing readiness scores."""
        return self._query(
            "SELECT vehicle_name, authority_score, evidence_score, "
            "compliance_score, total_score, status, gaps, strengths "
            "FROM filing_readiness "
            "ORDER BY total_score DESC "
            "LIMIT 20"
        )

    def _get_open_gaps(self) -> List[dict]:
        """Get unresolved gap tickets."""
        return self._query(
            "SELECT ticket_id, filing_name, gap_type, description, severity "
            "FROM gap_tickets "
            "WHERE resolution_status != 'resolved' "
            "ORDER BY CASE severity "
            "  WHEN 'critical' THEN 1 "
            "  WHEN 'high' THEN 2 "
            "  WHEN 'medium' THEN 3 "
            "  ELSE 4 END "
            "LIMIT 30"
        )

    def _get_critical_risks(self) -> List[dict]:
        """Get high/critical risk events."""
        return self._query(
            "SELECT risk_type_id, track, forum, risk_class, severity, title "
            "FROM risk_events "
            "WHERE severity >= 3 "
            "ORDER BY severity DESC "
            "LIMIT 20"
        )

    def _get_claim_summary(self) -> Dict[str, int]:
        """Summarize claims by classification."""
        rows = self._query(
            "SELECT classification, COUNT(*) as cnt "
            "FROM claims "
            "GROUP BY classification "
            "ORDER BY cnt DESC"
        )
        return {r["classification"]: r["cnt"] for r in rows if r.get("classification")}

    def _get_judicial_violations(self) -> List[dict]:
        """Get judicial violation findings."""
        return self._query(
            "SELECT violation_id, judge_name, canon_number, "
            "violation_description, severity "
            "FROM judicial_violations "
            "ORDER BY severity DESC "
            "LIMIT 20"
        )

    def _get_latest_convergence(self) -> Optional[dict]:
        """Get latest convergence cycle data."""
        return self._query_one(
            "SELECT cycle_id, delta_new, blockers, next_patch, quality_score "
            "FROM convergence_log "
            "ORDER BY cycle_id DESC LIMIT 1"
        )

    # ------------------------------------------------------------------
    # Lane-Specific Context
    # ------------------------------------------------------------------
    def get_lane_context(self, lane: str) -> Dict[str, Any]:
        """
        Deep dive into a specific case lane.
        lane: MEEK1, MEEK2, MEEK3, MEEK4
        """
        cache_key = f"lane_{lane}"
        cached = _cache_get(cache_key)
        if cached is not None:
            return cached

        case_info = self._get_case_info()
        lane_info = case_info.get("lanes", {}).get(lane, {})
        case_id = lane_info.get("case_number", "")

        ctx: Dict[str, Any] = {
            "lane": lane,
            "case_info": lane_info,
            "deadlines": self._query(
                "SELECT * FROM deadlines WHERE case_id = ? ORDER BY due_date_iso",
                (case_id,),
            ),
            "docket_events": self._query(
                "SELECT * FROM docket_events WHERE case_id = ? "
                "ORDER BY event_date_iso DESC LIMIT 30",
                (case_id,),
            ),
            "vehicles": self._query(
                "SELECT * FROM vehicles WHERE case_lane = ? ORDER BY sbna_score DESC",
                (lane,),
            ),
            "filing_readiness": self._get_filing_readiness(),
            "claims": self._query(
                "SELECT claim_id, classification, actor, proposition, status "
                "FROM claims LIMIT 50"
            ),
            "risks": self._query(
                "SELECT * FROM risk_events WHERE track = ? OR forum = ? "
                "ORDER BY severity DESC",
                (lane, lane_info.get("court", "")),
            ),
            "action_scores": self._query(
                "SELECT * FROM legal_action_scores WHERE lane = ? "
                "ORDER BY overall_score DESC",
                (lane,),
            ),
            "adversary_models": self._query(
                "SELECT * FROM adversary_models ORDER BY risk_level DESC LIMIT 10"
            ),
        }

        _cache_set(cache_key, ctx)
        return ctx

    # ------------------------------------------------------------------
    # Authority Search
    # ------------------------------------------------------------------
    def get_authority_for(self, topic: str) -> Dict[str, Any]:
        """
        Comprehensive authority search across all DB tables.
        Returns rules, statutes, case law, passages, and references.
        """
        cache_key = f"auth_{topic}"
        cached = _cache_get(cache_key)
        if cached is not None:
            return cached

        safe_topic = topic.replace("'", "''")
        like_pat = f"%{safe_topic}%"

        result: Dict[str, Any] = {
            "topic": topic,
            "court_rules": [],
            "statutes": [],
            "case_law": [],
            "authority_passages": [],
            "legal_references": [],
            "benchbook": [],
        }

        # auth_rules (direct LIKE)
        result["court_rules"] = self._query(
            "SELECT rule_number, title, substr(full_text, 1, 800) as excerpt "
            "FROM auth_rules "
            "WHERE rule_number LIKE ? OR title LIKE ? OR full_text LIKE ? "
            "LIMIT 10",
            (like_pat, like_pat, like_pat),
        )

        # auth_rules FTS
        try:
            fts_results = self._query(
                "SELECT rule_number, title, substr(full_text, 1, 800) as excerpt "
                "FROM auth_rules WHERE rowid IN "
                "(SELECT rowid FROM auth_rules_fts WHERE auth_rules_fts MATCH ?) "
                "LIMIT 10",
                (topic,),
            )
            seen = {r["rule_number"] for r in result["court_rules"]}
            for r in fts_results:
                if r.get("rule_number") not in seen:
                    result["court_rules"].append(r)
        except Exception as e:
            logger.warning(f"FTS search on auth_rules_fts failed for topic '{topic}': {e}")

        # rules_text (statutes)
        result["statutes"] = self._query(
            "SELECT id, rule, chapter, substr(context, 1, 800) as excerpt "
            "FROM rules_text "
            "WHERE rule LIKE ? OR context LIKE ? "
            "LIMIT 10",
            (like_pat, like_pat),
        )

        # master_citations (case law)
        result["case_law"] = self._query(
            "SELECT citation, cite_type, substr(context, 1, 500) as excerpt, source_file "
            "FROM master_citations "
            "WHERE citation LIKE ? OR context LIKE ? "
            "LIMIT 15",
            (like_pat, like_pat),
        )

        # auth_authority_passages
        result["authority_passages"] = self._query(
            "SELECT passage_text, section, source_file "
            "FROM auth_authority_passages "
            "WHERE passage_text LIKE ? OR section LIKE ? "
            "LIMIT 10",
            (like_pat, like_pat),
        )

        # FTS on passages
        try:
            fts_passages = self._query(
                "SELECT passage_text, section, source_file "
                "FROM auth_authority_passages WHERE rowid IN "
                "(SELECT rowid FROM auth_passages_fts WHERE auth_passages_fts MATCH ?) "
                "LIMIT 10",
                (topic,),
            )
            for p in fts_passages:
                if p not in result["authority_passages"]:
                    result["authority_passages"].append(p)
        except Exception as e:
            logger.warning(f"FTS search on auth_passages_fts failed for topic '{topic}': {e}")

        # legal_reference_docs
        result["legal_references"] = self._query(
            "SELECT heading, substr(body, 1, 800) as excerpt, source_file "
            "FROM legal_reference_docs "
            "WHERE heading LIKE ? OR body LIKE ? "
            "LIMIT 10",
            (like_pat, like_pat),
        )

        # auth_benchbook_entries
        result["benchbook"] = self._query(
            "SELECT section, title, substr(content, 1, 600) as excerpt "
            "FROM auth_benchbook_entries "
            "WHERE title LIKE ? OR content LIKE ? "
            "LIMIT 5",
            (like_pat, like_pat),
        )

        _cache_set(cache_key, result)
        return result

    # ------------------------------------------------------------------
    # Timeline Builder
    # ------------------------------------------------------------------
    def get_timeline(self, case_id: Optional[str] = None) -> List[dict]:
        """
        Build chronological event list from all evidence tables.
        Merges docket_events, evidence_quotes (with date_ref),
        and documents (modified_date).
        """
        cache_key = f"timeline_{case_id or 'all'}"
        cached = _cache_get(cache_key)
        if cached is not None:
            return cached

        events: List[dict] = []

        # Docket events
        if case_id:
            docket = self._query(
                "SELECT event_date_iso as date, title, event_type as type, "
                "summary, 'docket' as source "
                "FROM docket_events WHERE case_id = ? "
                "ORDER BY event_date_iso",
                (case_id,),
            )
        else:
            docket = self._query(
                "SELECT event_date_iso as date, title, event_type as type, "
                "summary, case_id, 'docket' as source "
                "FROM docket_events "
                "ORDER BY event_date_iso"
            )
        events.extend(docket)

        # Evidence quotes with date references
        eq = self._query(
            "SELECT date_ref as date, substr(quote_text, 1, 300) as title, "
            "evidence_category as type, legal_significance as summary, "
            "'evidence' as source "
            "FROM evidence_quotes "
            "WHERE date_ref IS NOT NULL AND date_ref != '' "
            "ORDER BY date_ref "
            "LIMIT 200"
        )
        events.extend(eq)

        # Documents by modified date
        docs = self._query(
            "SELECT modified_date as date, file_name as title, "
            "evidence_category as type, "
            "'Document ingested' as summary, 'document' as source "
            "FROM documents "
            "WHERE modified_date IS NOT NULL AND modified_date != '' "
            "ORDER BY modified_date "
            "LIMIT 200"
        )
        events.extend(docs)

        # Sort all events chronologically
        def sort_key(e):
            try:
                return e.get("date", "") or ""
            except Exception as e:
                logger.debug(f"Sort key extraction failed: {e}")
                return ""

        events.sort(key=sort_key)

        _cache_set(cache_key, events)
        return events

    # ------------------------------------------------------------------
    # Utility
    # ------------------------------------------------------------------
    def get_db_stats(self) -> Dict[str, Any]:
        """Get database statistics."""
        stats: Dict[str, Any] = {}
        key_tables = [
            "auth_rules", "master_citations", "legal_reference_docs",
            "rules_text", "documents", "evidence_quotes", "md_sections",
            "claims", "deadlines", "docket_events", "vehicles",
            "contradiction_map", "impeachment_items", "judicial_violations",
            "adversary_models", "filing_readiness", "gap_tickets",
            "risk_events", "auth_authority_passages", "auth_benchbook_entries",
        ]
        for table in key_tables:
            count = self._scalar(f"SELECT COUNT(*) FROM {table}")
            if count is not None:
                stats[table] = count
        return stats

    def search_everything(self, query: str, limit: int = 20) -> Dict[str, List[dict]]:
        """Search across all major tables for a query string."""
        like_pat = f"%{query}%"
        results: Dict[str, List[dict]] = {}

        searches = [
            ("auth_rules", "SELECT rule_number, title, substr(full_text,1,300) as text FROM auth_rules WHERE full_text LIKE ? LIMIT ?"),
            ("rules_text", "SELECT rule, chapter, substr(context,1,300) as text FROM rules_text WHERE context LIKE ? LIMIT ?"),
            ("master_citations", "SELECT citation, cite_type, substr(context,1,300) as text FROM master_citations WHERE citation LIKE ? OR context LIKE ? LIMIT ?"),
            ("evidence_quotes", "SELECT substr(quote_text,1,300) as text, speaker, evidence_category FROM evidence_quotes WHERE quote_text LIKE ? LIMIT ?"),
            ("md_sections", "SELECT section_title, substr(content,1,300) as text FROM md_sections WHERE content LIKE ? LIMIT ?"),
            ("legal_reference_docs", "SELECT heading, substr(body,1,300) as text FROM legal_reference_docs WHERE body LIKE ? LIMIT ?"),
        ]

        for table, sql in searches:
            try:
                if table == "master_citations":
                    rows = self._query(sql, (like_pat, like_pat, limit))
                else:
                    rows = self._query(sql, (like_pat, limit))
                if rows:
                    results[table] = rows
            except Exception as e:
                logger.warning(f"Search failed on table '{table}': {e}")

        return results

    def close(self):
        """Close DB connection."""
        try:
            if self._conn:
                self._conn.close()
                self._conn = None
        except Exception as e:
            logger.warning(f"Error closing DB connection: {e}")

    def __del__(self):
        self.close()


# ── CLI ───────────────────────────────────────────────────────────────
if __name__ == "__main__":
    loader = ContextLoader()

    if len(sys.argv) > 1:
        cmd = sys.argv[1]
        if cmd == "--full":
            ctx = loader.get_full_context()
            cycle_json(ctx)
        elif cmd == "--lane" and len(sys.argv) > 2:
            ctx = loader.get_lane_context(sys.argv[2])
            cycle_json(ctx)
        elif cmd == "--authority" and len(sys.argv) > 2:
            topic = " ".join(sys.argv[2:])
            ctx = loader.get_authority_for(topic)
            cycle_json(ctx)
        elif cmd == "--timeline":
            case_id = sys.argv[2] if len(sys.argv) > 2 else None
            events = loader.get_timeline(case_id)
            cycle_json(events)
        elif cmd == "--stats":
            stats = loader.get_db_stats()
            cycle_json(stats)
        elif cmd == "--search" and len(sys.argv) > 2:
            q = " ".join(sys.argv[2:])
            results = loader.search_everything(q)
            cycle_json(results)
        else:
            print("Context Loader CLI")
            print("  --full                  Full case context")
            print("  --lane MEEK1            Lane-specific context")
            print("  --authority <topic>     Authority search")
            print("  --timeline [case_id]    Chronological timeline")
            print("  --stats                 DB table counts")
            print("  --search <query>        Search all tables")
    else:
        stats = loader.get_db_stats()
        total = sum(stats.values())
        print(f"LitigationOS Context Loader -- {len(stats)} tables, {total:,} rows indexed")
        for t, c in sorted(stats.items(), key=lambda x: -x[1])[:10]:
            print(f"  {t}: {c:,}")

    loader.close()
