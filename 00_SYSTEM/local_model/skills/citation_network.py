#!/usr/bin/env python3
"""
MBP LitigationOS -- Citation Network Skill
============================================
Search and analyze the citation network across master_citations
(3.6M+ rows), authority_chains (25 rows), and authority_shards
(1,684 rows) for Pigors v. Watson (COA 366810).
"""

from __future__ import annotations

import json
import os
import sqlite3
import sys
from pathlib import Path
from typing import Dict, List, Optional

sys.path.insert(
    0,
    str(
        Path(__file__).resolve().parent.parent
        if "skills" in str(Path(__file__))
        else Path(__file__).resolve().parent
    ),
)
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


class CitationNetwork:
    """Analyze the citation network (3.6M+ master_citations,
    25 authority_chains, 1.6k+ authority_shards)."""

    # ── Core queries ──────────────────────────────────────────────────

    def search_citations(
        self,
        query: str,
        cite_type: Optional[str] = None,
        limit: int = 50,
    ) -> List[Dict]:
        """Search master_citations (3,596,625 rows) by text and optional type."""
        conn = _get_db()
        if not conn:
            return []
        try:
            if cite_type:
                rows = conn.execute(
                    "SELECT citation, cite_type, substr(context, 1, 400) as context, "
                    "source_file "
                    "FROM master_citations "
                    "WHERE cite_type = ? AND (citation LIKE ? OR context LIKE ?) "
                    "LIMIT ?",
                    (cite_type, f"%{query}%", f"%{query}%", limit),
                ).fetchall()
            else:
                rows = conn.execute(
                    "SELECT citation, cite_type, substr(context, 1, 400) as context, "
                    "source_file "
                    "FROM master_citations "
                    "WHERE citation LIKE ? OR context LIKE ? "
                    "LIMIT ?",
                    (f"%{query}%", f"%{query}%", limit),
                ).fetchall()
            return [dict(r) for r in rows]
        except Exception:
            return []
        finally:
            conn.close()

    def get_authority_chains(self, limit: int = 30) -> List[Dict]:
        """Query authority_chains (25 rows)."""
        conn = _get_db()
        if not conn:
            return []
        try:
            rows = conn.execute(
                "SELECT * FROM authority_chains ORDER BY rowid LIMIT ?",
                (limit,),
            ).fetchall()
            return [dict(r) for r in rows]
        except Exception:
            return []
        finally:
            conn.close()

    def get_authority_shards(
        self, chain_id: Optional[str] = None, limit: int = 100
    ) -> List[Dict]:
        """Query authority_shards (1,684 rows)."""
        conn = _get_db()
        if not conn:
            return []
        try:
            if chain_id:
                rows = conn.execute(
                    "SELECT * FROM authority_shards "
                    "WHERE chain_id = ? ORDER BY rowid LIMIT ?",
                    (chain_id, limit),
                ).fetchall()
            else:
                rows = conn.execute(
                    "SELECT * FROM authority_shards ORDER BY rowid LIMIT ?",
                    (limit,),
                ).fetchall()
            return [dict(r) for r in rows]
        except Exception:
            return []
        finally:
            conn.close()

    # ── Analysis methods ──────────────────────────────────────────────

    def find_most_cited(
        self, cite_type: Optional[str] = None, limit: int = 20
    ) -> List[Dict]:
        """Find the most frequently cited authorities."""
        conn = _get_db()
        if not conn:
            return []
        try:
            if cite_type:
                rows = conn.execute(
                    "SELECT citation, cite_type, COUNT(*) as cite_count "
                    "FROM master_citations "
                    "WHERE cite_type = ? "
                    "GROUP BY citation ORDER BY cite_count DESC LIMIT ?",
                    (cite_type, limit),
                ).fetchall()
            else:
                rows = conn.execute(
                    "SELECT citation, cite_type, COUNT(*) as cite_count "
                    "FROM master_citations "
                    "GROUP BY citation ORDER BY cite_count DESC LIMIT ?",
                    (limit,),
                ).fetchall()
            return [dict(r) for r in rows]
        except Exception:
            return []
        finally:
            conn.close()

    def find_citations_for_rule(self, rule: str) -> List[Dict]:
        """Find all citations referencing a specific rule (MCR/MCL/MRE)."""
        conn = _get_db()
        if not conn:
            return []
        try:
            rows = conn.execute(
                "SELECT citation, cite_type, substr(context, 1, 400) as context, "
                "source_file "
                "FROM master_citations "
                "WHERE citation LIKE ? "
                "ORDER BY rowid LIMIT 100",
                (f"%{rule}%",),
            ).fetchall()
            return [dict(r) for r in rows]
        except Exception:
            return []
        finally:
            conn.close()

    def find_citations_for_topic(self, topic: str) -> List[Dict]:
        """Search citations by topic context."""
        conn = _get_db()
        if not conn:
            return []
        try:
            rows = conn.execute(
                "SELECT citation, cite_type, substr(context, 1, 400) as context, "
                "source_file "
                "FROM master_citations "
                "WHERE context LIKE ? "
                "ORDER BY rowid LIMIT 50",
                (f"%{topic}%",),
            ).fetchall()
            return [dict(r) for r in rows]
        except Exception:
            return []
        finally:
            conn.close()

    def verify_citation(self, citation: str) -> Dict:
        """Check if a citation exists in the database and return its data."""
        conn = _get_db()
        if not conn:
            return {"citation": citation, "verified": False, "error": "DB unavailable"}
        try:
            # Exact match first
            row = conn.execute(
                "SELECT citation, cite_type, substr(context, 1, 600) as context, "
                "source_file "
                "FROM master_citations WHERE citation = ? LIMIT 1",
                (citation,),
            ).fetchone()

            if row:
                return {
                    "citation": citation,
                    "verified": True,
                    "match_type": "exact",
                    "data": dict(row),
                }

            # Fuzzy match
            row = conn.execute(
                "SELECT citation, cite_type, substr(context, 1, 600) as context, "
                "source_file "
                "FROM master_citations WHERE citation LIKE ? LIMIT 1",
                (f"%{citation}%",),
            ).fetchone()

            if row:
                return {
                    "citation": citation,
                    "verified": True,
                    "match_type": "fuzzy",
                    "data": dict(row),
                }

            # Check auth_rules as fallback
            row = conn.execute(
                "SELECT rule_number, title, substr(full_text, 1, 600) as text "
                "FROM auth_rules WHERE rule_number LIKE ? "
                "OR full_text LIKE ? LIMIT 1",
                (f"%{citation}%", f"%{citation}%"),
            ).fetchone()

            if row:
                return {
                    "citation": citation,
                    "verified": True,
                    "match_type": "auth_rules_fallback",
                    "data": dict(row),
                }

            return {"citation": citation, "verified": False, "data": None}
        except Exception as e:
            return {"citation": citation, "verified": False, "error": str(e)}
        finally:
            conn.close()

    def build_citation_chain(self, starting_cite: str) -> Dict:
        """Trace citation references starting from one citation."""
        conn = _get_db()
        if not conn:
            return {"error": "DB unavailable"}
        try:
            # Find the starting citation
            start_rows = conn.execute(
                "SELECT citation, cite_type, substr(context, 1, 500) as context, "
                "source_file "
                "FROM master_citations WHERE citation LIKE ? LIMIT 5",
                (f"%{starting_cite}%",),
            ).fetchall()
            start_entries = [dict(r) for r in start_rows]

            if not start_entries:
                return {
                    "starting_cite": starting_cite,
                    "found": False,
                    "chain": [],
                }

            # Find other citations in the same source files
            related: List[Dict] = []
            source_files = set()
            for entry in start_entries:
                sf = entry.get("source_file", "")
                if sf:
                    source_files.add(sf)

            for sf in list(source_files)[:5]:
                rows = conn.execute(
                    "SELECT DISTINCT citation, cite_type "
                    "FROM master_citations WHERE source_file = ? "
                    "AND citation NOT LIKE ? LIMIT 20",
                    (sf, f"%{starting_cite}%"),
                ).fetchall()
                for r in rows:
                    related.append(dict(r))

            # Check authority_chains
            chains = []
            try:
                rows = conn.execute(
                    "SELECT * FROM authority_chains ORDER BY rowid"
                ).fetchall()
                for r in rows:
                    rd = dict(r)
                    if any(
                        starting_cite.lower() in str(v).lower()
                        for v in rd.values()
                        if v is not None
                    ):
                        chains.append(rd)
            except Exception:
                pass

            # Check authority_shards
            shards = []
            try:
                rows = conn.execute(
                    "SELECT * FROM authority_shards "
                    "WHERE rowid IN (SELECT rowid FROM authority_shards LIMIT 1684)"
                ).fetchall()
                for r in rows:
                    rd = dict(r)
                    if any(
                        starting_cite.lower() in str(v).lower()
                        for v in rd.values()
                        if v is not None
                    ):
                        shards.append(rd)
            except Exception:
                pass

            return {
                "starting_cite": starting_cite,
                "found": True,
                "start_entries": start_entries,
                "co_occurring_citations": related[:30],
                "authority_chains": chains,
                "authority_shards": shards,
            }
        except Exception as e:
            return {"error": str(e)}
        finally:
            conn.close()

    def get_citation_statistics(self) -> Dict:
        """Summary statistics: total citations, by type, top cited."""
        conn = _get_db()
        if not conn:
            return {"error": "DB unavailable"}
        try:
            # Total count
            total = 0
            try:
                row = conn.execute(
                    "SELECT COUNT(*) as cnt FROM master_citations"
                ).fetchone()
                total = row["cnt"] if row else 0
            except Exception:
                pass

            # By cite_type
            by_type: List[Dict] = []
            try:
                rows = conn.execute(
                    "SELECT cite_type, COUNT(*) as cnt "
                    "FROM master_citations GROUP BY cite_type "
                    "ORDER BY cnt DESC LIMIT 20"
                ).fetchall()
                by_type = [dict(r) for r in rows]
            except Exception:
                pass

            # Top 10 most cited
            top_cited: List[Dict] = []
            try:
                rows = conn.execute(
                    "SELECT citation, cite_type, COUNT(*) as cnt "
                    "FROM master_citations "
                    "GROUP BY citation ORDER BY cnt DESC LIMIT 10"
                ).fetchall()
                top_cited = [dict(r) for r in rows]
            except Exception:
                pass

            # Chain count
            chain_count = 0
            try:
                row = conn.execute(
                    "SELECT COUNT(*) as cnt FROM authority_chains"
                ).fetchone()
                chain_count = row["cnt"] if row else 0
            except Exception:
                pass

            # Shard count
            shard_count = 0
            try:
                row = conn.execute(
                    "SELECT COUNT(*) as cnt FROM authority_shards"
                ).fetchone()
                shard_count = row["cnt"] if row else 0
            except Exception:
                pass

            return {
                "total_citations": total,
                "by_type": by_type,
                "top_cited": top_cited,
                "authority_chains": chain_count,
                "authority_shards": shard_count,
            }
        except Exception as e:
            return {"error": str(e)}
        finally:
            conn.close()


# ── CLI ───────────────────────────────────────────────────────────────
if __name__ == "__main__":
    cn = CitationNetwork()
    usage = (
        "Citation Network Skill\n"
        "Usage:\n"
        "  python citation_network.py search <QUERY> [TYPE] [LIMIT]\n"
        "  python citation_network.py chains [LIMIT]\n"
        "  python citation_network.py shards [CHAIN_ID] [LIMIT]\n"
        "  python citation_network.py most-cited [TYPE] [LIMIT]\n"
        "  python citation_network.py for-rule <RULE>\n"
        "  python citation_network.py for-topic <TOPIC>\n"
        "  python citation_network.py verify <CITATION>\n"
        "  python citation_network.py trace <CITATION>\n"
        "  python citation_network.py stats\n"
    )

    if len(sys.argv) < 2:
        print(usage)
        sys.exit(0)

    cmd = sys.argv[1].lower()

    if cmd == "search":
        if len(sys.argv) < 3:
            print("Error: query required", file=sys.stderr)
            sys.exit(1)
        query = sys.argv[2]
        ctype = sys.argv[3] if len(sys.argv) > 3 else None
        lim = int(sys.argv[4]) if len(sys.argv) > 4 else 50
        cycle_json(cn.search_citations(query, ctype, lim))
    elif cmd == "chains":
        lim = int(sys.argv[2]) if len(sys.argv) > 2 else 30
        cycle_json(cn.get_authority_chains(lim))
    elif cmd == "shards":
        cid = sys.argv[2] if len(sys.argv) > 2 else None
        lim = int(sys.argv[3]) if len(sys.argv) > 3 else 100
        cycle_json(cn.get_authority_shards(cid, lim))
    elif cmd == "most-cited":
        ctype = sys.argv[2] if len(sys.argv) > 2 else None
        lim = int(sys.argv[3]) if len(sys.argv) > 3 else 20
        cycle_json(cn.find_most_cited(ctype, lim))
    elif cmd == "for-rule":
        if len(sys.argv) < 3:
            print("Error: rule required", file=sys.stderr)
            sys.exit(1)
        cycle_json(cn.find_citations_for_rule(sys.argv[2]))
    elif cmd == "for-topic":
        if len(sys.argv) < 3:
            print("Error: topic required", file=sys.stderr)
            sys.exit(1)
        cycle_json(cn.find_citations_for_topic(" ".join(sys.argv[2:])))
    elif cmd == "verify":
        if len(sys.argv) < 3:
            print("Error: citation required", file=sys.stderr)
            sys.exit(1)
        cycle_json(cn.verify_citation(" ".join(sys.argv[2:])))
    elif cmd == "trace":
        if len(sys.argv) < 3:
            print("Error: citation required", file=sys.stderr)
            sys.exit(1)
        cycle_json(cn.build_citation_chain(" ".join(sys.argv[2:])))
    elif cmd == "stats":
        cycle_json(cn.get_citation_statistics())
    else:
        print(usage)
