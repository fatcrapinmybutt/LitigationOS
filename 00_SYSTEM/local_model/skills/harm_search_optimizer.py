#!/usr/bin/env python3
"""
MBP LitigationOS — Harm Search Optimizer Skill (m41)
=====================================================
Optimized FTS5 searching across extracted_harms (26K+ rows) and
evidence_quotes (308K rows) with cross-referencing, adversary
aggregation, and category summaries.

Tables used:
    extracted_harms (26,459 rows) — FTS5 via extracted_harms_fts
    evidence_quotes (308,704 rows) — FTS5 via evidence_quotes_fts
    claims, claim_evidence_links — cross-referencing

Authority:
    All searches DB-grounded; no hallucination.

Usage:
    from skills.harm_search_optimizer import HarmSearchOptimizer
    opt = HarmSearchOptimizer()
    results = opt.search_harms("parenting time")
"""

from __future__ import annotations

import json
import os
import sqlite3
import sys
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

sys.path.insert(0, str(Path(__file__).resolve().parent.parent
    if "skills" in str(Path(__file__)) else Path(__file__).resolve().parent))
try:
    from cycle_method import cycle_json, cycle_print
except ImportError:
    cycle_json = lambda obj, **kw: print(json.dumps(obj, default=str))
    cycle_print = print

DB_PATH = os.environ.get(
    "LITIGATION_DB_PATH",
    r"C:\Users\andre\LitigationOS\litigation_context.db",
)


def _get_db(readonly: bool = True) -> Optional[sqlite3.Connection]:
    try:
        conn = sqlite3.connect(DB_PATH, timeout=60)
        conn.execute("PRAGMA journal_mode=WAL")
        conn.execute("PRAGMA busy_timeout=60000")
        if readonly:
            conn.execute("PRAGMA query_only=ON")
        conn.row_factory = sqlite3.Row
        return conn
    except Exception:
        return None


class HarmSearchOptimizer:
    """Optimized search across extracted_harms and evidence_quotes via FTS5."""

    def search_harms(
        self,
        query: str,
        filters: Optional[Dict[str, str]] = None,
        limit: int = 50,
    ) -> Dict[str, Any]:
        """FTS5 search across extracted_harms with optional filters.

        Filters: adversary, category, severity_min, date_from, date_to.
        Returns structured results with relevance ranking.
        """
        conn = _get_db()
        if not conn:
            return {"error": "DB unavailable", "results": []}
        filters = filters or {}
        results = []
        try:
            # FTS5 search with rank
            sql = (
                "SELECT h.id, h.category, h.subcategory, h.adversary, "
                "h.date_ref, h.description, h.andrew_quote, h.severity, "
                "h.constitutional_violation, h.mcr_violation, "
                "h.filing_stacks, h.conversation_title, "
                "rank "
                "FROM extracted_harms h "
                "JOIN (SELECT rowid, rank FROM extracted_harms_fts "
                "      WHERE extracted_harms_fts MATCH ? ORDER BY rank) fts "
                "ON h.rowid = fts.rowid "
            )
            where_parts = []
            params: list = [query]

            if filters.get("adversary"):
                where_parts.append("h.adversary = ?")
                params.append(filters["adversary"])
            if filters.get("category"):
                where_parts.append("h.category = ?")
                params.append(filters["category"])
            if filters.get("severity_min"):
                where_parts.append("h.severity >= ?")
                params.append(int(filters["severity_min"]))
            if filters.get("date_from"):
                where_parts.append("h.date_ref >= ?")
                params.append(filters["date_from"])
            if filters.get("date_to"):
                where_parts.append("h.date_ref <= ?")
                params.append(filters["date_to"])

            if where_parts:
                sql += "WHERE " + " AND ".join(where_parts) + " "
            sql += "ORDER BY fts.rank LIMIT ?"
            params.append(limit)

            rows = conn.execute(sql, params).fetchall()
            for r in rows:
                results.append({
                    "id": r["id"],
                    "category": r["category"],
                    "subcategory": r["subcategory"],
                    "adversary": r["adversary"],
                    "date_ref": r["date_ref"],
                    "description": r["description"],
                    "andrew_quote": r["andrew_quote"],
                    "severity": r["severity"],
                    "constitutional_violation": r["constitutional_violation"],
                    "mcr_violation": r["mcr_violation"],
                    "filing_stacks": r["filing_stacks"],
                    "relevance_rank": r["rank"],
                })
        except Exception as e:
            return {"error": str(e), "results": [], "query": query}
        finally:
            conn.close()

        return {
            "query": query,
            "filters": filters,
            "total_results": len(results),
            "results": results,
        }

    def search_evidence(
        self,
        query: str,
        source_type: Optional[str] = None,
        limit: int = 50,
    ) -> Dict[str, Any]:
        """FTS5 search on evidence_quotes_fts with optional source_type filter.

        source_type: PDF_COURT_DOC, CHATGPT_REFERENCE, etc.
        """
        conn = _get_db()
        if not conn:
            return {"error": "DB unavailable", "results": []}
        results = []
        try:
            sql = (
                "SELECT e.id, e.document_id, e.page_number, "
                "e.evidence_category, e.quote_text, e.quote_type, "
                "e.speaker, e.date_ref, e.legal_significance, "
                "e.source_type, fts.rank "
                "FROM evidence_quotes e "
                "JOIN (SELECT rowid, rank FROM evidence_quotes_fts "
                "      WHERE evidence_quotes_fts MATCH ? ORDER BY rank) fts "
                "ON e.rowid = fts.rowid "
            )
            params: list = [query]
            if source_type:
                sql += "WHERE e.source_type = ? "
                params.append(source_type)
            sql += "ORDER BY fts.rank LIMIT ?"
            params.append(limit)

            rows = conn.execute(sql, params).fetchall()
            for r in rows:
                results.append({
                    "id": r["id"],
                    "document_id": r["document_id"],
                    "page_number": r["page_number"],
                    "evidence_category": r["evidence_category"],
                    "quote_text": r["quote_text"][:500],
                    "speaker": r["speaker"],
                    "date_ref": r["date_ref"],
                    "legal_significance": r["legal_significance"],
                    "source_type": r["source_type"],
                    "relevance_rank": r["rank"],
                })
        except Exception as e:
            return {"error": str(e), "results": [], "query": query}
        finally:
            conn.close()

        return {
            "query": query,
            "source_type": source_type,
            "total_results": len(results),
            "results": results,
        }

    def cross_reference(self, harm_id: int) -> Dict[str, Any]:
        """Find related evidence, claims, and filings for a given harm ID."""
        conn = _get_db()
        if not conn:
            return {"error": "DB unavailable"}
        result: Dict[str, Any] = {"harm_id": harm_id}
        try:
            # Get the harm record
            harm = conn.execute(
                "SELECT * FROM extracted_harms WHERE id = ?", (harm_id,)
            ).fetchone()
            if not harm:
                return {"error": f"Harm ID {harm_id} not found"}
            result["harm"] = dict(harm)

            desc = harm["description"]
            # Find related evidence via FTS5 on key terms
            terms = " OR ".join(
                w for w in desc.split()[:8]
                if len(w) > 3 and w.isalpha()
            ) or desc[:50]
            try:
                ev_rows = conn.execute(
                    "SELECT e.id, e.quote_text, e.speaker, "
                    "e.legal_significance, e.source_type "
                    "FROM evidence_quotes e "
                    "JOIN (SELECT rowid FROM evidence_quotes_fts "
                    "      WHERE evidence_quotes_fts MATCH ?) fts "
                    "ON e.rowid = fts.rowid LIMIT 10",
                    (terms,),
                ).fetchall()
                result["related_evidence"] = [dict(r) for r in ev_rows]
            except Exception:
                result["related_evidence"] = []

            # Find related claims
            try:
                claim_rows = conn.execute(
                    "SELECT c.claim_id, c.proposition, c.classification, c.actor "
                    "FROM claims c WHERE c.proposition LIKE ? LIMIT 10",
                    (f"%{desc[:40]}%",),
                ).fetchall()
                result["related_claims"] = [dict(r) for r in claim_rows]
            except Exception:
                result["related_claims"] = []

            # Find related filings via filing_stacks
            if harm["filing_stacks"]:
                result["filing_stacks"] = harm["filing_stacks"]

        except Exception as e:
            result["error"] = str(e)
        finally:
            conn.close()
        return result

    def harm_summary_by_adversary(self, name: str) -> Dict[str, Any]:
        """Aggregate harms by a specific adversary."""
        conn = _get_db()
        if not conn:
            return {"error": "DB unavailable"}
        try:
            # Total count
            total = conn.execute(
                "SELECT count(*) FROM extracted_harms WHERE adversary = ?",
                (name,),
            ).fetchone()[0]

            # By category
            cats = conn.execute(
                "SELECT category, count(*) as cnt, "
                "avg(severity) as avg_sev, max(severity) as max_sev "
                "FROM extracted_harms WHERE adversary = ? "
                "GROUP BY category ORDER BY cnt DESC",
                (name,),
            ).fetchall()

            # By severity
            sevs = conn.execute(
                "SELECT severity, count(*) as cnt "
                "FROM extracted_harms WHERE adversary = ? "
                "GROUP BY severity ORDER BY severity DESC",
                (name,),
            ).fetchall()

            # Constitutional violations
            const = conn.execute(
                "SELECT constitutional_violation, count(*) as cnt "
                "FROM extracted_harms "
                "WHERE adversary = ? AND constitutional_violation IS NOT NULL "
                "GROUP BY constitutional_violation ORDER BY cnt DESC LIMIT 10",
                (name,),
            ).fetchall()

            # Top MCR violations
            mcr = conn.execute(
                "SELECT mcr_violation, count(*) as cnt "
                "FROM extracted_harms "
                "WHERE adversary = ? AND mcr_violation IS NOT NULL "
                "GROUP BY mcr_violation ORDER BY cnt DESC LIMIT 10",
                (name,),
            ).fetchall()

            return {
                "adversary": name,
                "total_harms": total,
                "by_category": [dict(r) for r in cats],
                "by_severity": [dict(r) for r in sevs],
                "constitutional_violations": [dict(r) for r in const],
                "mcr_violations": [dict(r) for r in mcr],
            }
        except Exception as e:
            return {"error": str(e), "adversary": name}
        finally:
            conn.close()

    def harm_summary_by_category(self, category: str) -> Dict[str, Any]:
        """Aggregate harms by harm type/category."""
        conn = _get_db()
        if not conn:
            return {"error": "DB unavailable"}
        try:
            total = conn.execute(
                "SELECT count(*) FROM extracted_harms WHERE category = ?",
                (category,),
            ).fetchone()[0]

            # By adversary
            advs = conn.execute(
                "SELECT adversary, count(*) as cnt, avg(severity) as avg_sev "
                "FROM extracted_harms WHERE category = ? "
                "GROUP BY adversary ORDER BY cnt DESC",
                (category,),
            ).fetchall()

            # By subcategory
            subs = conn.execute(
                "SELECT subcategory, count(*) as cnt "
                "FROM extracted_harms WHERE category = ? "
                "AND subcategory IS NOT NULL "
                "GROUP BY subcategory ORDER BY cnt DESC LIMIT 15",
                (category,),
            ).fetchall()

            # Severity distribution
            sevs = conn.execute(
                "SELECT severity, count(*) as cnt "
                "FROM extracted_harms WHERE category = ? "
                "GROUP BY severity ORDER BY severity DESC",
                (category,),
            ).fetchall()

            # Sample high-severity items
            samples = conn.execute(
                "SELECT id, adversary, description, severity, date_ref "
                "FROM extracted_harms WHERE category = ? "
                "ORDER BY severity DESC LIMIT 5",
                (category,),
            ).fetchall()

            return {
                "category": category,
                "total_harms": total,
                "by_adversary": [dict(r) for r in advs],
                "by_subcategory": [dict(r) for r in subs],
                "by_severity": [dict(r) for r in sevs],
                "top_severity_samples": [dict(r) for r in samples],
            }
        except Exception as e:
            return {"error": str(e), "category": category}
        finally:
            conn.close()


# ── JSON-RPC dispatch ─────────────────────────────────────────────────

def handle_rpc(method: str, params: Dict[str, Any] = None) -> Dict:
    params = params or {}
    opt = HarmSearchOptimizer()
    dispatch = {
        "search_harms": opt.search_harms,
        "search_evidence": opt.search_evidence,
        "cross_reference": opt.cross_reference,
        "harm_summary_by_adversary": opt.harm_summary_by_adversary,
        "harm_summary_by_category": opt.harm_summary_by_category,
    }
    fn = dispatch.get(method)
    if not fn:
        return {"error": f"Unknown method: {method}", "available": list(dispatch.keys())}
    try:
        result = fn(**params)
        return {"result": result, "method": method, "status": "ok"}
    except Exception as e:
        return {"error": str(e), "method": method}


if __name__ == "__main__":
    if sys.stdout and hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    opt = HarmSearchOptimizer()
    print("=== Harm Search Optimizer Skill (m41) ===\n")

    # Quick test: search harms
    r = opt.search_harms("parenting time", limit=3)
    print(f"search_harms('parenting time'): {r['total_results']} results")

    # Quick test: search evidence
    r2 = opt.search_evidence("ex parte", limit=3)
    print(f"search_evidence('ex parte'): {r2['total_results']} results")

    # Adversary summary
    r3 = opt.harm_summary_by_adversary("McNeill")
    print(f"harm_summary_by_adversary('McNeill'): {r3.get('total_harms', 0)} harms")

    print("\n[OK] Harm Search Optimizer operational")
