#!/usr/bin/env python3
"""
MBP LitigationOS -- Authority Search Skill
============================================
Search for legal authority on any topic across all DB tables.
Returns ranked list of authorities with full text.
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


def search_authority(topic: str, limit: int = 10) -> List[Dict]:
    """
    Comprehensive authority search across all DB tables.
    Returns ranked list: [{source, authority, title, text, relevance}]
    """
    results = []
    try:
        conn = _get_db()
        if not conn:
            return results

        like_pat = f"%{topic}%"

        # 1. auth_rules (highest priority - full text court rules)
        try:
            rows = conn.execute(
                "SELECT rule_number, title, substr(full_text, 1, 1000) as text "
                "FROM auth_rules "
                "WHERE rule_number LIKE ? OR title LIKE ? OR full_text LIKE ? "
                "LIMIT ?",
                (like_pat, like_pat, like_pat, limit),
            ).fetchall()
            for row in rows:
                results.append({
                    "source": "auth_rules",
                    "authority": row["rule_number"] or "",
                    "title": row["title"] or "",
                    "text": row["text"] or "",
                    "relevance": 1.0,
                })
        except Exception:
            pass

        # 2. auth_rules FTS (broader matches)
        try:
            rows = conn.execute(
                "SELECT rule_number, title, substr(full_text, 1, 1000) as text "
                "FROM auth_rules WHERE rowid IN "
                "(SELECT rowid FROM auth_rules_fts WHERE auth_rules_fts MATCH ?) "
                "LIMIT ?",
                (topic, limit),
            ).fetchall()
            seen = {r["authority"] for r in results}
            for row in rows:
                if row["rule_number"] not in seen:
                    results.append({
                        "source": "auth_rules_fts",
                        "authority": row["rule_number"] or "",
                        "title": row["title"] or "",
                        "text": row["text"] or "",
                        "relevance": 0.9,
                    })
        except Exception:
            pass

        # 3. rules_text (statutes)
        try:
            rows = conn.execute(
                "SELECT rule, chapter, substr(context, 1, 800) as text "
                "FROM rules_text "
                "WHERE rule LIKE ? OR context LIKE ? "
                "LIMIT ?",
                (like_pat, like_pat, limit),
            ).fetchall()
            for row in rows:
                results.append({
                    "source": "rules_text",
                    "authority": row["rule"] or "",
                    "title": row["chapter"] or "",
                    "text": row["text"] or "",
                    "relevance": 0.85,
                })
        except Exception:
            pass

        # 4. master_citations (case law)
        try:
            rows = conn.execute(
                "SELECT citation, cite_type, substr(context, 1, 600) as text, source_file "
                "FROM master_citations "
                "WHERE citation LIKE ? OR context LIKE ? "
                "LIMIT ?",
                (like_pat, like_pat, limit),
            ).fetchall()
            for row in rows:
                results.append({
                    "source": "master_citations",
                    "authority": row["citation"] or "",
                    "title": row["cite_type"] or "",
                    "text": row["text"] or "",
                    "relevance": 0.8,
                })
        except Exception:
            pass

        # 5. auth_authority_passages
        try:
            rows = conn.execute(
                "SELECT section, substr(passage_text, 1, 600) as text, source_file "
                "FROM auth_authority_passages "
                "WHERE passage_text LIKE ? OR section LIKE ? "
                "LIMIT ?",
                (like_pat, like_pat, limit),
            ).fetchall()
            for row in rows:
                results.append({
                    "source": "auth_authority_passages",
                    "authority": row["section"] or "",
                    "title": "",
                    "text": row["text"] or "",
                    "relevance": 0.75,
                })
        except Exception:
            pass

        # 6. legal_reference_docs
        try:
            rows = conn.execute(
                "SELECT heading, substr(body, 1, 600) as text, source_file "
                "FROM legal_reference_docs "
                "WHERE heading LIKE ? OR body LIKE ? "
                "LIMIT ?",
                (like_pat, like_pat, limit),
            ).fetchall()
            for row in rows:
                results.append({
                    "source": "legal_reference_docs",
                    "authority": row["heading"] or "",
                    "title": "",
                    "text": row["text"] or "",
                    "relevance": 0.7,
                })
        except Exception:
            pass

        # 7. auth_benchbook_entries
        try:
            rows = conn.execute(
                "SELECT section, title, substr(content, 1, 600) as text "
                "FROM auth_benchbook_entries "
                "WHERE title LIKE ? OR content LIKE ? "
                "LIMIT ?",
                (like_pat, like_pat, min(limit, 5)),
            ).fetchall()
            for row in rows:
                results.append({
                    "source": "auth_benchbook_entries",
                    "authority": row["section"] or "",
                    "title": row["title"] or "",
                    "text": row["text"] or "",
                    "relevance": 0.65,
                })
        except Exception:
            pass

        # 8. md_sections (markdown docs)
        try:
            rows = conn.execute(
                "SELECT section_title, substr(content, 1, 400) as text, source_file "
                "FROM md_sections "
                "WHERE section_title LIKE ? OR content LIKE ? "
                "LIMIT ?",
                (like_pat, like_pat, min(limit, 5)),
            ).fetchall()
            for row in rows:
                results.append({
                    "source": "md_sections",
                    "authority": row["section_title"] or "",
                    "title": "",
                    "text": row["text"] or "",
                    "relevance": 0.5,
                })
        except Exception:
            pass

        conn.close()

        # Sort by relevance descending
        results.sort(key=lambda x: x.get("relevance", 0), reverse=True)

        # Deduplicate by authority string
        seen = set()
        deduped = []
        for r in results:
            key = r["authority"].strip().lower()
            if key and key not in seen:
                seen.add(key)
                deduped.append(r)
            elif not key:
                deduped.append(r)
        results = deduped[:limit]

    except Exception:
        pass

    return results


def search_by_type(topic: str, auth_type: str = "all", limit: int = 10) -> List[Dict]:
    """
    Search for specific authority type.
    auth_type: 'mcr', 'mcl', 'case_law', 'benchbook', 'all'
    """
    if auth_type == "all":
        return search_authority(topic, limit)

    results = []
    try:
        conn = _get_db()
        if not conn:
            return results

        like_pat = f"%{topic}%"

        if auth_type == "mcr":
            rows = conn.execute(
                "SELECT rule_number, title, substr(full_text, 1, 1000) as text "
                "FROM auth_rules WHERE rule_type = 'MCR' AND "
                "(rule_number LIKE ? OR title LIKE ? OR full_text LIKE ?) LIMIT ?",
                (like_pat, like_pat, like_pat, limit),
            ).fetchall()
            for row in rows:
                results.append({
                    "source": "auth_rules",
                    "authority": row["rule_number"],
                    "title": row["title"],
                    "text": row["text"],
                    "relevance": 1.0,
                })
        elif auth_type == "mcl":
            rows = conn.execute(
                "SELECT rule, chapter, substr(context, 1, 800) as text "
                "FROM rules_text WHERE rule LIKE ? OR context LIKE ? LIMIT ?",
                (like_pat, like_pat, limit),
            ).fetchall()
            for row in rows:
                results.append({
                    "source": "rules_text",
                    "authority": row["rule"],
                    "title": row["chapter"],
                    "text": row["text"],
                    "relevance": 1.0,
                })
        elif auth_type == "case_law":
            rows = conn.execute(
                "SELECT citation, cite_type, substr(context, 1, 600) as text "
                "FROM master_citations WHERE citation LIKE ? OR context LIKE ? LIMIT ?",
                (like_pat, like_pat, limit),
            ).fetchall()
            for row in rows:
                results.append({
                    "source": "master_citations",
                    "authority": row["citation"],
                    "title": row["cite_type"],
                    "text": row["text"],
                    "relevance": 1.0,
                })
        elif auth_type == "benchbook":
            rows = conn.execute(
                "SELECT section, title, substr(content, 1, 600) as text "
                "FROM auth_benchbook_entries WHERE title LIKE ? OR content LIKE ? LIMIT ?",
                (like_pat, like_pat, limit),
            ).fetchall()
            for row in rows:
                results.append({
                    "source": "auth_benchbook_entries",
                    "authority": row["section"],
                    "title": row["title"],
                    "text": row["text"],
                    "relevance": 1.0,
                })

        conn.close()
    except Exception:
        pass

    return results


# ── CLI ───────────────────────────────────────────────────────────────
if __name__ == "__main__":
    if len(sys.argv) > 1:
        query = " ".join(sys.argv[1:])
        results = search_authority(query, limit=10)
        cycle_json(results)
        print(f"\n--- Found {len(results)} authorities ---", file=sys.stderr)
    else:
        print("Authority Search Skill")
        print("Usage: python authority_search.py 'disqualification bias'")
