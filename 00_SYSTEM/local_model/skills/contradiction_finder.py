#!/usr/bin/env python3
"""
MBP LitigationOS -- Contradiction Finder Skill
================================================
Find contradictions between documents/statements in the DB.
Surfaces existing contradiction_map entries and impeachment_items.
Can also do fresh cross-document comparison.
"""

from __future__ import annotations

import json
import os
import sqlite3
import sys
from pathlib import Path
from typing import Dict, List, Optional

sys.path.insert(0, str(Path(__file__).resolve().parent.parent if 'skills' in str(Path(__file__)) else Path(__file__).resolve().parent))
try:
    from cycle_method import cycle_json, cycle_print
except ImportError:
    cycle_json = lambda obj, **kw: print(json.dumps(obj, default=str))
    cycle_print = print

DB_PATH = os.environ.get(
    "LITIGATION_DB_PATH",
    r"C:\Users\andre\LitigationOS\litigation_context.db",
)


def _get_db() -> Optional[sqlite3.Connection]:
    """Get read-only DB connection."""
    try:
        conn = sqlite3.connect(DB_PATH, timeout=30)
        conn.execute("PRAGMA journal_mode=WAL")
        conn.execute("PRAGMA query_only=ON")
        conn.row_factory = sqlite3.Row
        return conn
    except Exception:
        return None


def get_contradictions(severity_filter: Optional[str] = None,
                       limit: int = 50) -> List[Dict]:
    """
    Get known contradictions from contradiction_map table.
    severity_filter: 'critical', 'high', 'medium', 'low', or None for all.
    """
    results = []
    try:
        conn = _get_db()
        if not conn:
            return results

        if severity_filter:
            rows = conn.execute(
                "SELECT id, source_a_type, source_a_text, source_b_type, source_b_text, "
                "contradiction_type, severity, legal_impact "
                "FROM contradiction_map "
                "WHERE severity = ? "
                "ORDER BY CASE severity "
                "  WHEN 'critical' THEN 1 WHEN 'high' THEN 2 "
                "  WHEN 'medium' THEN 3 ELSE 4 END "
                "LIMIT ?",
                (severity_filter, limit),
            ).fetchall()
        else:
            rows = conn.execute(
                "SELECT id, source_a_type, source_a_text, source_b_type, source_b_text, "
                "contradiction_type, severity, legal_impact "
                "FROM contradiction_map "
                "ORDER BY CASE severity "
                "  WHEN 'critical' THEN 1 WHEN 'high' THEN 2 "
                "  WHEN 'medium' THEN 3 ELSE 4 END "
                "LIMIT ?",
                (limit,),
            ).fetchall()

        for row in rows:
            results.append({
                "id": row["id"],
                "source_a_type": row["source_a_type"] or "",
                "source_a_text": row["source_a_text"] or "",
                "source_b_type": row["source_b_type"] or "",
                "source_b_text": row["source_b_text"] or "",
                "contradiction_type": row["contradiction_type"] or "",
                "severity": row["severity"] or "",
                "legal_impact": row["legal_impact"] or "",
            })

        conn.close()
    except Exception:
        pass

    return results


def get_impeachment_items(speaker_filter: Optional[str] = None,
                          severity_filter: Optional[str] = None,
                          limit: int = 50) -> List[Dict]:
    """
    Get impeachment material from impeachment_items table.
    """
    results = []
    try:
        conn = _get_db()
        if not conn:
            return results

        sql = (
            "SELECT id, item_type, speaker, statement, "
            "contradicting_source, contradicting_text, legal_hook, severity "
            "FROM impeachment_items WHERE 1=1 "
        )
        params: list = []

        if speaker_filter:
            sql += "AND speaker LIKE ? "
            params.append(f"%{speaker_filter}%")

        if severity_filter:
            sql += "AND severity = ? "
            params.append(severity_filter)

        sql += (
            "ORDER BY CASE severity "
            "  WHEN 'critical' THEN 1 WHEN 'high' THEN 2 "
            "  WHEN 'medium' THEN 3 ELSE 4 END "
            "LIMIT ?"
        )
        params.append(limit)

        rows = conn.execute(sql, params).fetchall()
        for row in rows:
            results.append({
                "id": row["id"],
                "item_type": row["item_type"] or "",
                "speaker": row["speaker"] or "",
                "statement": row["statement"] or "",
                "contradicting_source": row["contradicting_source"] or "",
                "contradicting_text": row["contradicting_text"] or "",
                "legal_hook": row["legal_hook"] or "",
                "severity": row["severity"] or "",
            })

        conn.close()
    except Exception:
        pass

    return results


def search_contradictions(topic: str, limit: int = 20) -> Dict[str, List[Dict]]:
    """
    Search for contradictions related to a specific topic.
    Returns both contradiction_map and impeachment_items results.
    """
    result: Dict[str, List[Dict]] = {
        "contradictions": [],
        "impeachment": [],
    }

    try:
        conn = _get_db()
        if not conn:
            return result

        like_pat = f"%{topic}%"

        # Search contradiction_map
        try:
            rows = conn.execute(
                "SELECT id, source_a_type, source_a_text, source_b_type, source_b_text, "
                "contradiction_type, severity, legal_impact "
                "FROM contradiction_map "
                "WHERE source_a_text LIKE ? OR source_b_text LIKE ? "
                "OR legal_impact LIKE ? OR contradiction_type LIKE ? "
                "ORDER BY CASE severity "
                "  WHEN 'critical' THEN 1 WHEN 'high' THEN 2 "
                "  WHEN 'medium' THEN 3 ELSE 4 END "
                "LIMIT ?",
                (like_pat, like_pat, like_pat, like_pat, limit),
            ).fetchall()

            for row in rows:
                result["contradictions"].append({
                    "id": row["id"],
                    "source_a": row["source_a_text"] or "",
                    "source_b": row["source_b_text"] or "",
                    "type": row["contradiction_type"] or "",
                    "severity": row["severity"] or "",
                    "legal_impact": row["legal_impact"] or "",
                })
        except Exception:
            pass

        # Search impeachment items
        try:
            rows = conn.execute(
                "SELECT id, speaker, statement, contradicting_text, "
                "legal_hook, severity "
                "FROM impeachment_items "
                "WHERE statement LIKE ? OR contradicting_text LIKE ? "
                "OR legal_hook LIKE ? "
                "ORDER BY CASE severity "
                "  WHEN 'critical' THEN 1 WHEN 'high' THEN 2 "
                "  WHEN 'medium' THEN 3 ELSE 4 END "
                "LIMIT ?",
                (like_pat, like_pat, like_pat, limit),
            ).fetchall()

            for row in rows:
                result["impeachment"].append({
                    "id": row["id"],
                    "speaker": row["speaker"] or "",
                    "statement": row["statement"] or "",
                    "contradicting_text": row["contradicting_text"] or "",
                    "legal_hook": row["legal_hook"] or "",
                    "severity": row["severity"] or "",
                })
        except Exception:
            pass

        conn.close()
    except Exception:
        pass

    return result


def get_contradiction_summary() -> Dict:
    """Get summary statistics about contradictions and impeachment material."""
    summary: Dict = {
        "total_contradictions": 0,
        "by_severity": {},
        "by_type": {},
        "total_impeachment": 0,
        "impeachment_by_speaker": {},
    }

    try:
        conn = _get_db()
        if not conn:
            return summary

        # Contradiction stats
        try:
            row = conn.execute("SELECT COUNT(*) as cnt FROM contradiction_map").fetchone()
            summary["total_contradictions"] = row["cnt"] if row else 0

            rows = conn.execute(
                "SELECT severity, COUNT(*) as cnt FROM contradiction_map "
                "GROUP BY severity ORDER BY cnt DESC"
            ).fetchall()
            summary["by_severity"] = {r["severity"]: r["cnt"] for r in rows if r["severity"]}

            rows = conn.execute(
                "SELECT contradiction_type, COUNT(*) as cnt FROM contradiction_map "
                "GROUP BY contradiction_type ORDER BY cnt DESC"
            ).fetchall()
            summary["by_type"] = {r["contradiction_type"]: r["cnt"] for r in rows if r["contradiction_type"]}
        except Exception:
            pass

        # Impeachment stats
        try:
            row = conn.execute("SELECT COUNT(*) as cnt FROM impeachment_items").fetchone()
            summary["total_impeachment"] = row["cnt"] if row else 0

            rows = conn.execute(
                "SELECT speaker, COUNT(*) as cnt FROM impeachment_items "
                "GROUP BY speaker ORDER BY cnt DESC"
            ).fetchall()
            summary["impeachment_by_speaker"] = {r["speaker"]: r["cnt"] for r in rows if r["speaker"]}
        except Exception:
            pass

        conn.close()
    except Exception:
        pass

    return summary


# ── CLI ───────────────────────────────────────────────────────────────
if __name__ == "__main__":
    if len(sys.argv) > 1:
        if sys.argv[1] == "--summary":
            result = get_contradiction_summary()
        elif sys.argv[1] == "--impeachment":
            speaker = sys.argv[2] if len(sys.argv) > 2 else None
            result = get_impeachment_items(speaker_filter=speaker)
        elif sys.argv[1] == "--search":
            topic = " ".join(sys.argv[2:]) if len(sys.argv) > 2 else ""
            result = search_contradictions(topic)
        else:
            severity = sys.argv[1] if sys.argv[1] in ("critical", "high", "medium", "low") else None
            result = get_contradictions(severity_filter=severity)
    else:
        result = get_contradiction_summary()

    cycle_json(result)
