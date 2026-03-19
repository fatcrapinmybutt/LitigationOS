#!/usr/bin/env python3
"""
MBP LitigationOS — Brain Nuclei Integration Query Engine
=========================================================
Graph-guided search: loads brain nuclei JSON files, matches user queries
to brain nodes, then searches connected DB tables for comprehensive results.

Brain Nuclei:
  - evidence_nucleus.json  → evidence_quotes, impeachment_items
  - legal_nucleus.json     → auth_rules, rules_text, master_citations
  - filing_nucleus.json    → vehicles, claims, docket_events
  - party_nucleus.json     → evidence_quotes (by speaker), judicial_violations
  - timeline_nucleus.json  → docket_events, deadlines

Usage:
    python brain_query.py "what evidence shows alienation?"
    python brain_query.py "MCR 2.003 disqualification" --nucleus legal
    python brain_query.py "Watson contradictions" --format json

Example:
    python brain_query.py "parental alienation evidence" --limit 15
    # Matches evidence_nucleus → searches evidence_quotes, impeachment_items
"""

from __future__ import annotations

import argparse
import json
import os
import re
import sqlite3
import sys
import time
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

sys.path.insert(0, str(Path(__file__).resolve().parent))
try:
    from cycle_method import cycle_json, cycle_print
except ImportError:
    cycle_json = lambda obj, **kw: print(json.dumps(obj, default=str))
    cycle_print = print

DB_PATH = os.environ.get(
    "LITIGATION_DB_PATH",
    r"C:\Users\andre\litigation_context.db",
)
NUCLEI_DIR = Path(__file__).parent / "nuclei"

# ── Nucleus-to-DB table mapping ─────────────────────────────────────
NUCLEUS_DB_MAP = {
    "evidence": {
        "tables": ["evidence_quotes", "impeachment_items"],
        "fts_tables": ["evidence_quotes_fts"],
        "keywords": ["evidence", "quote", "exhibit", "testimony", "witness",
                      "statement", "communication", "credibility", "police",
                      "medical", "fraud", "pattern"],
    },
    "legal_authority": {
        "tables": ["auth_rules", "rules_text", "master_citations"],
        "fts_tables": ["auth_rules_fts", "rules_text_fts"],
        "keywords": ["mcr", "mcl", "mre", "rule", "statute", "law", "authority",
                      "constitution", "benchbook", "ethics", "case law",
                      "court rule", "compiled law"],
    },
    "filing": {
        "tables": ["vehicles", "claims", "docket_events"],
        "fts_tables": [],
        "keywords": ["motion", "filing", "brief", "discovery", "appeal",
                      "emergency", "remedy", "review", "procedural", "foc",
                      "appellate", "subpoena"],
    },
    "party": {
        "tables": ["evidence_quotes", "judicial_violations"],
        "fts_tables": ["evidence_quotes_fts"],
        "keywords": ["watson", "pigors", "mcneill", "judge", "andrew",
                      "tiffany", "emily", "albert", "lori", "cody",
                      "rusco", "child", "party"],
    },
    "timeline": {
        "tables": ["docket_events", "deadlines"],
        "fts_tables": [],
        "keywords": ["timeline", "date", "hearing", "order", "event",
                      "deadline", "schedule", "when", "chronolog"],
    },
}


def _safe_text(val: Any, max_len: int = 500) -> str:
    """Safely convert DB value to string."""
    if val is None:
        return ""
    try:
        s = str(val).strip()
    except Exception:
        s = str(val).encode("utf-8", errors="replace").decode("utf-8", errors="replace").strip()
    return s[:max_len] if len(s) > max_len else s


# ── Brain Nuclei Loader ─────────────────────────────────────────────
class BrainNucleiLoader:
    """Loads and indexes brain nuclei JSON files."""

    def __init__(self, nuclei_dir: Path = NUCLEI_DIR):
        self.nuclei_dir = nuclei_dir
        self.nuclei: Dict[str, Dict] = {}
        self._load_all()

    def _load_all(self) -> None:
        """Load all nucleus JSON files."""
        if not self.nuclei_dir.exists():
            print(f"  [WARN] Nuclei directory not found: {self.nuclei_dir}")
            return

        for json_file in self.nuclei_dir.glob("*.json"):
            try:
                with open(json_file, "r", encoding="utf-8", errors="replace") as f:
                    data = json.load(f)
                nucleus_id = data.get("nucleus_id", json_file.stem)
                self.nuclei[nucleus_id] = data
            except Exception as e:
                print(f"  [WARN] Failed to load {json_file.name}: {e}")

        print(f"  Loaded {len(self.nuclei)} brain nuclei: {list(self.nuclei.keys())}")

    def match_query_to_nuclei(self, query: str) -> List[Tuple[str, float, List[Dict]]]:
        """
        Match a query to brain nuclei by keyword overlap and node text similarity.

        Returns: List of (nucleus_id, match_score, matching_nodes)
        """
        query_lower = query.lower()
        query_words = set(query_lower.split())
        results = []

        for nuc_id, nuc_data in self.nuclei.items():
            # Map nucleus_id to our config key
            config_key = nuc_id
            if config_key not in NUCLEUS_DB_MAP:
                # Try matching by name
                for key in NUCLEUS_DB_MAP:
                    if key in nuc_id or nuc_id in key:
                        config_key = key
                        break

            if config_key not in NUCLEUS_DB_MAP:
                continue

            config = NUCLEUS_DB_MAP[config_key]

            # Score 1: Keyword overlap
            keyword_score = 0
            for kw in config["keywords"]:
                if kw in query_lower:
                    keyword_score += 2
                elif any(w in kw for w in query_words):
                    keyword_score += 1

            # Score 2: Node text matching
            matching_nodes = []
            nodes = nuc_data.get("nodes", [])
            for node in nodes[:100]:  # Check top 100 nodes
                node_text = _safe_text(node.get("text", "")).lower()
                node_score = 0
                for word in query_words:
                    if len(word) >= 3 and word in node_text:
                        node_score += 1

                if node_score > 0:
                    matching_nodes.append({
                        "node_id": node.get("id", ""),
                        "text": _safe_text(node.get("text", ""), max_len=200),
                        "score": node.get("score", 0),
                        "source": node.get("source", ""),
                        "brain": node.get("brain", ""),
                        "tags": node.get("tags", []),
                        "match_score": node_score,
                    })

            matching_nodes.sort(key=lambda x: x["match_score"], reverse=True)
            matching_nodes = matching_nodes[:10]  # Top 10 matching nodes

            total_score = keyword_score + len(matching_nodes) * 0.5
            if total_score > 0:
                results.append((config_key, total_score, matching_nodes))

        results.sort(key=lambda x: x[1], reverse=True)
        return results


# ── Brain Query Engine ──────────────────────────────────────────────
class BrainQueryEngine:
    """Graph-guided search: query → brain nodes → DB tables → structured results."""

    def __init__(self, db_path: str = DB_PATH, nuclei_dir: Path = NUCLEI_DIR):
        self.db_path = db_path
        self._conn: Optional[sqlite3.Connection] = None
        self.brain = BrainNucleiLoader(nuclei_dir)

    def _get_db(self) -> sqlite3.Connection:
        if self._conn is not None:
            try:
                self._conn.execute("SELECT 1")
                return self._conn
            except Exception:
                self._conn = None

        self._conn = sqlite3.connect(self.db_path, timeout=30)
        self._conn.execute("PRAGMA journal_mode=WAL")
        self._conn.execute("PRAGMA cache_size=-65536")
        self._conn.execute("PRAGMA query_only=ON")
        return self._conn

    def _search_table(self, table: str, query: str, limit: int = 10) -> List[Dict]:
        """Search a DB table using LIKE or FTS5."""
        conn = self._get_db()
        results = []

        # Determine searchable columns
        try:
            col_info = conn.execute(f"PRAGMA table_info([{table}])").fetchall()
        except Exception:
            return []

        col_names = [c[1] for c in col_info]
        text_cols = [c[1] for c in col_info if c[2].upper() in ("TEXT", "")]

        if not text_cols:
            return []

        # Build LIKE search across text columns
        query_words = [w for w in query.split() if len(w) >= 3]
        if not query_words:
            return []

        where_clauses = []
        params = []
        for word in query_words[:5]:  # Max 5 search terms
            col_checks = " OR ".join(f'[{col}] LIKE ?' for col in text_cols[:5])
            where_clauses.append(f"({col_checks})")
            params.extend([f"%{word}%"] * min(len(text_cols), 5))

        if not where_clauses:
            return []

        sql = f"SELECT rowid, * FROM [{table}] WHERE {' AND '.join(where_clauses)} LIMIT {limit}"

        try:
            rows = conn.execute(sql, params).fetchall()
            all_cols = ["rowid"] + col_names
            for row in rows:
                row_dict = {}
                for i, val in enumerate(row):
                    if i < len(all_cols):
                        row_dict[all_cols[i]] = _safe_text(val, max_len=300)
                results.append(row_dict)
        except Exception as e:
            if "no such table" not in str(e).lower():
                print(f"    [WARN] Search failed on {table}: {e}")

        return results

    def _search_fts(self, fts_table: str, query: str, limit: int = 10) -> List[Dict]:
        """Search an FTS5 table."""
        conn = self._get_db()
        results = []

        # Sanitize query for FTS5
        sanitized = re.sub(r'[^\w\s]', ' ', query)
        terms = [w for w in sanitized.split() if len(w) >= 3]
        if not terms:
            return []

        fts_query = " OR ".join(terms)

        try:
            rows = conn.execute(
                f"SELECT rowid, rank, * FROM [{fts_table}] WHERE [{fts_table}] MATCH ? ORDER BY rank LIMIT ?",
                (fts_query, limit),
            ).fetchall()

            for row in rows:
                row_dict = {"rowid": row[0], "rank": row[1]}
                for i, val in enumerate(row[2:], 2):
                    row_dict[f"col_{i-2}"] = _safe_text(val, max_len=300)
                results.append(row_dict)
        except Exception as e:
            if "no such table" not in str(e).lower():
                pass  # Silent fail for FTS

        return results

    def query(
        self,
        query: str,
        nucleus_filter: Optional[str] = None,
        limit: int = 20,
    ) -> Dict[str, Any]:
        """
        Execute brain-guided query.

        Args:
            query: Natural language query
            nucleus_filter: Restrict to specific nucleus (e.g., 'evidence')
            limit: Max results per table

        Returns:
            {query, brain_matches, db_results, sources, total_results}
        """
        start_time = time.time()

        # Step 1: Match query to brain nuclei
        print(f"  Matching query to brain nuclei...")
        brain_matches = self.brain.match_query_to_nuclei(query)

        if nucleus_filter:
            brain_matches = [(nid, sc, nodes) for nid, sc, nodes in brain_matches if nid == nucleus_filter]

        if not brain_matches:
            # Fallback: search all nuclei tables
            print(f"  No strong brain match — falling back to broad search")
            brain_matches = [(k, 0, []) for k in NUCLEUS_DB_MAP.keys()]

        # Step 2: Search connected DB tables
        print(f"  Searching connected DB tables...")
        db_results = {}
        sources = set()
        total_results = 0

        for nuc_id, score, nodes in brain_matches[:3]:  # Top 3 nuclei
            config = NUCLEUS_DB_MAP.get(nuc_id, {})

            # FTS search first (faster and ranked)
            for fts_table in config.get("fts_tables", []):
                results = self._search_fts(fts_table, query, limit=limit)
                if results:
                    db_results[fts_table] = results
                    sources.add(fts_table)
                    total_results += len(results)

            # LIKE search on base tables
            for table in config.get("tables", []):
                if table not in db_results:  # Don't double-search
                    results = self._search_table(table, query, limit=limit)
                    if results:
                        db_results[table] = results
                        sources.add(table)
                        total_results += len(results)

        elapsed = time.time() - start_time

        return {
            "query": query,
            "brain_matches": [
                {
                    "nucleus": nid,
                    "score": round(sc, 2),
                    "matching_nodes": len(nodes),
                    "top_node": nodes[0] if nodes else None,
                }
                for nid, sc, nodes in brain_matches[:5]
            ],
            "db_results": db_results,
            "sources": sorted(sources),
            "total_results": total_results,
            "elapsed_seconds": round(elapsed, 3),
        }

    def close(self) -> None:
        if self._conn:
            try:
                self._conn.close()
            except Exception:
                pass
            self._conn = None


def _print_results(report: Dict[str, Any], format_type: str = "text") -> None:
    """Print brain query results."""
    if format_type == "json":
        cycle_json(report)
        return

    print(f"\n{'='*60}")
    print(f"BRAIN-GUIDED QUERY RESULTS")
    print(f"{'='*60}")
    print(f"  Query:   {report['query']}")
    print(f"  Results: {report['total_results']}")
    print(f"  Time:    {report['elapsed_seconds']}s")
    print(f"  Sources: {', '.join(report['sources'])}")

    # Brain matches
    bm = report.get("brain_matches", [])
    if bm:
        print(f"\n  Brain Nuclei Matches:")
        for m in bm:
            print(f"    → {m['nucleus']} (score: {m['score']}, nodes: {m['matching_nodes']})")

    # DB Results
    for table, rows in report.get("db_results", {}).items():
        print(f"\n  {'─'*56}")
        print(f"  [{table}] — {len(rows)} results")
        for i, row in enumerate(rows[:5], 1):
            # Show first meaningful text column
            text_vals = [v for k, v in row.items()
                         if k not in ("rowid", "rank", "id") and v and len(str(v)) > 10]
            snippet = text_vals[0][:200] if text_vals else str(row)[:200]
            print(f"    {i}. {snippet}")

    print(f"\n{'='*60}")


# ── CLI ─────────────────────────────────────────────────────────────
if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Brain nuclei-guided query engine for LitigationOS"
    )
    parser.add_argument("query", type=str, help="Natural language query")
    parser.add_argument("--nucleus", type=str, default=None,
                        help="Filter to specific nucleus: evidence, legal_authority, filing, party, timeline")
    parser.add_argument("--limit", type=int, default=20,
                        help="Max results per table (default: 20)")
    parser.add_argument("--format", type=str, default="text",
                        choices=["text", "json"], help="Output format")

    args = parser.parse_args()

    engine = BrainQueryEngine()
    try:
        report = engine.query(
            query=args.query,
            nucleus_filter=args.nucleus,
            limit=args.limit,
        )
        _print_results(report, format_type=args.format)
    finally:
        engine.close()
