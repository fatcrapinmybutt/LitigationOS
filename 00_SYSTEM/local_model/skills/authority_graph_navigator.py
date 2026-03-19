#!/usr/bin/env python3
"""
MBP LitigationOS -- Authority Graph Navigator Skill
=====================================================
Traverse the authority graph (auth_authority_nodes/edges, graph_nodes,
court_rule_graphs) to find supporting/opposing authority, build chains,
and visualize authority trees for Pigors v. Watson (COA 366810).
"""

from __future__ import annotations

import json
import os
import sqlite3
import sys
from collections import defaultdict
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


class AuthorityGraphNavigator:
    """Navigate the authority graph (12k+ nodes, 461k+ edges,
    31k+ graph_nodes, 25k+ court_rule_graphs)."""

    # ── Raw data access ───────────────────────────────────────────────

    def get_authority_nodes(
        self, node_type: Optional[str] = None, limit: int = 100
    ) -> List[Dict]:
        """Query auth_authority_nodes (12,409 rows)."""
        conn = _get_db()
        if not conn:
            return []
        try:
            if node_type:
                rows = conn.execute(
                    "SELECT * FROM auth_authority_nodes "
                    "WHERE node_type = ? ORDER BY rowid LIMIT ?",
                    (node_type, limit),
                ).fetchall()
            else:
                rows = conn.execute(
                    "SELECT * FROM auth_authority_nodes ORDER BY rowid LIMIT ?",
                    (limit,),
                ).fetchall()
            return [dict(r) for r in rows]
        except Exception:
            return []
        finally:
            conn.close()

    def get_authority_edges(
        self, source_id: Optional[str] = None, limit: int = 200
    ) -> List[Dict]:
        """Query auth_authority_edges (461,769 rows)."""
        conn = _get_db()
        if not conn:
            return []
        try:
            if source_id:
                rows = conn.execute(
                    "SELECT * FROM auth_authority_edges "
                    "WHERE source_id = ? ORDER BY rowid LIMIT ?",
                    (source_id, limit),
                ).fetchall()
            else:
                rows = conn.execute(
                    "SELECT * FROM auth_authority_edges ORDER BY rowid LIMIT ?",
                    (limit,),
                ).fetchall()
            return [dict(r) for r in rows]
        except Exception:
            return []
        finally:
            conn.close()

    def get_graph_nodes(self, limit: int = 100) -> List[Dict]:
        """Query graph_nodes (31,565 rows)."""
        conn = _get_db()
        if not conn:
            return []
        try:
            rows = conn.execute(
                "SELECT * FROM graph_nodes ORDER BY rowid LIMIT ?", (limit,)
            ).fetchall()
            return [dict(r) for r in rows]
        except Exception:
            return []
        finally:
            conn.close()

    def get_court_rule_graph(
        self, rule: Optional[str] = None, limit: int = 100
    ) -> List[Dict]:
        """Query court_rule_graphs (25,571 rows)."""
        conn = _get_db()
        if not conn:
            return []
        try:
            if rule:
                rows = conn.execute(
                    "SELECT * FROM court_rule_graphs "
                    "WHERE rule LIKE ? ORDER BY rowid LIMIT ?",
                    (f"%{rule}%", limit),
                ).fetchall()
            else:
                rows = conn.execute(
                    "SELECT * FROM court_rule_graphs ORDER BY rowid LIMIT ?",
                    (limit,),
                ).fetchall()
            return [dict(r) for r in rows]
        except Exception:
            return []
        finally:
            conn.close()

    # ── Graph traversal ───────────────────────────────────────────────

    def find_supporting_authority(
        self, topic: str, limit: int = 20
    ) -> List[Dict]:
        """Traverse the graph to find authorities supporting a topic."""
        conn = _get_db()
        if not conn:
            return []
        results: List[Dict] = []
        try:
            # Search nodes by label
            try:
                rows = conn.execute(
                    "SELECT * FROM auth_authority_nodes "
                    "WHERE label LIKE ? ORDER BY rowid LIMIT ?",
                    (f"%{topic}%", limit),
                ).fetchall()
                for r in rows:
                    d = dict(r)
                    d["_source"] = "auth_authority_nodes"
                    results.append(d)
            except Exception:
                pass

            # Search graph_nodes
            try:
                rows = conn.execute(
                    "SELECT * FROM graph_nodes "
                    "WHERE rowid IN (SELECT rowid FROM graph_nodes LIMIT 5000) "
                    "LIMIT ?",
                    (limit * 3,),
                ).fetchall()
                for r in rows:
                    rd = dict(r)
                    if any(
                        topic.lower() in str(v).lower()
                        for v in rd.values()
                        if v is not None
                    ):
                        rd["_source"] = "graph_nodes"
                        results.append(rd)
                        if len(results) >= limit:
                            break
            except Exception:
                pass

            # Search auth_rules via FTS
            try:
                rows = conn.execute(
                    "SELECT rule_number, title, substr(full_text, 1, 400) as text "
                    "FROM auth_rules WHERE rowid IN "
                    "(SELECT rowid FROM auth_rules_fts "
                    " WHERE auth_rules_fts MATCH ?) LIMIT ?",
                    (topic, limit),
                ).fetchall()
                for r in rows:
                    d = dict(r)
                    d["_source"] = "auth_rules"
                    results.append(d)
            except Exception:
                pass

            # Search authority passages via FTS
            try:
                rows = conn.execute(
                    "SELECT section, substr(passage_text, 1, 400) as text "
                    "FROM auth_authority_passages WHERE rowid IN "
                    "(SELECT rowid FROM auth_passages_fts "
                    " WHERE auth_passages_fts MATCH ?) LIMIT ?",
                    (topic, limit),
                ).fetchall()
                for r in rows:
                    d = dict(r)
                    d["_source"] = "auth_authority_passages"
                    results.append(d)
            except Exception:
                pass

        except Exception:
            pass
        finally:
            conn.close()
        return results[:limit]

    def find_opposing_authority(
        self, topic: str, limit: int = 10
    ) -> List[Dict]:
        """Find potentially opposing / adverse authorities for a topic."""
        conn = _get_db()
        if not conn:
            return []
        results: List[Dict] = []
        try:
            # Check adversary_models
            try:
                rows = conn.execute(
                    "SELECT * FROM adversary_models "
                    "WHERE attack_type LIKE ? OR rebuttal_strategy LIKE ? "
                    "ORDER BY rowid LIMIT ?",
                    (f"%{topic}%", f"%{topic}%", limit),
                ).fetchall()
                for r in rows:
                    d = dict(r)
                    d["_source"] = "adversary_models"
                    results.append(d)
            except Exception:
                pass

            # Check contradiction_map
            try:
                rows = conn.execute(
                    "SELECT * FROM contradiction_map "
                    "WHERE source_a_text LIKE ? OR source_b_text LIKE ? "
                    "ORDER BY rowid LIMIT ?",
                    (f"%{topic}%", f"%{topic}%", limit),
                ).fetchall()
                for r in rows:
                    d = dict(r)
                    d["_source"] = "contradiction_map"
                    results.append(d)
            except Exception:
                pass

        except Exception:
            pass
        finally:
            conn.close()
        return results[:limit]

    def build_authority_chain(self, starting_rule: str) -> Dict:
        """Trace chain of authority from a rule to related statutes,
        cases, and rules via edges."""
        conn = _get_db()
        if not conn:
            return {"error": "DB unavailable"}
        try:
            # Find starting node
            start_node = None
            try:
                row = conn.execute(
                    "SELECT * FROM auth_authority_nodes "
                    "WHERE label LIKE ? LIMIT 1",
                    (f"%{starting_rule}%",),
                ).fetchone()
                if row:
                    start_node = dict(row)
            except Exception:
                pass

            if not start_node:
                return {
                    "starting_rule": starting_rule,
                    "found": False,
                    "chain": [],
                }

            node_id = start_node.get("id", "")

            # Follow edges outward (depth 1)
            direct_edges = []
            try:
                rows = conn.execute(
                    "SELECT e.*, n.label as target_label, n.node_type as target_type "
                    "FROM auth_authority_edges e "
                    "LEFT JOIN auth_authority_nodes n ON e.target_id = n.id "
                    "WHERE e.source_id = ? LIMIT 50",
                    (node_id,),
                ).fetchall()
                direct_edges = [dict(r) for r in rows]
            except Exception:
                pass

            # Follow edges inward (who cites this rule)
            citing = []
            try:
                rows = conn.execute(
                    "SELECT e.*, n.label as source_label, n.node_type as source_type "
                    "FROM auth_authority_edges e "
                    "LEFT JOIN auth_authority_nodes n ON e.source_id = n.id "
                    "WHERE e.target_id = ? LIMIT 50",
                    (node_id,),
                ).fetchall()
                citing = [dict(r) for r in rows]
            except Exception:
                pass

            # Court rule graph entries
            rule_graph = []
            try:
                rows = conn.execute(
                    "SELECT * FROM court_rule_graphs WHERE rule LIKE ? LIMIT 20",
                    (f"%{starting_rule}%",),
                ).fetchall()
                rule_graph = [dict(r) for r in rows]
            except Exception:
                pass

            return {
                "starting_rule": starting_rule,
                "found": True,
                "start_node": start_node,
                "outward_edges": direct_edges,
                "inward_edges": citing,
                "rule_graph": rule_graph,
                "chain_depth": 1,
                "total_connections": len(direct_edges) + len(citing),
            }
        except Exception as e:
            return {"error": str(e)}
        finally:
            conn.close()

    def get_rule_relationships(self, rule_number: str) -> Dict:
        """Find all rules related to a given rule number."""
        conn = _get_db()
        if not conn:
            return {"error": "DB unavailable"}
        try:
            # Direct rule entry
            rule_entry = None
            try:
                row = conn.execute(
                    "SELECT rule_number, title, substr(full_text, 1, 500) as text "
                    "FROM auth_rules WHERE rule_number LIKE ? LIMIT 1",
                    (f"%{rule_number}%",),
                ).fetchone()
                if row:
                    rule_entry = dict(row)
            except Exception:
                pass

            # Court rule graph connections
            graph_entries = []
            try:
                rows = conn.execute(
                    "SELECT * FROM court_rule_graphs "
                    "WHERE rule LIKE ? ORDER BY rowid LIMIT 50",
                    (f"%{rule_number}%",),
                ).fetchall()
                graph_entries = [dict(r) for r in rows]
            except Exception:
                pass

            # Cross-references from md_cross_refs
            cross_refs = []
            try:
                rows = conn.execute(
                    "SELECT * FROM md_cross_refs "
                    "WHERE source_file LIKE ? OR target_file LIKE ? "
                    "ORDER BY rowid LIMIT 30",
                    (f"%{rule_number}%", f"%{rule_number}%"),
                ).fetchall()
                cross_refs = [dict(r) for r in rows]
            except Exception:
                pass

            return {
                "rule_number": rule_number,
                "rule_entry": rule_entry,
                "graph_connections": graph_entries,
                "cross_references": cross_refs,
            }
        except Exception as e:
            return {"error": str(e)}
        finally:
            conn.close()

    def get_authority_strength(self, topic: str) -> Dict:
        """Measure authority strength by counting supporting nodes/edges."""
        conn = _get_db()
        if not conn:
            return {"error": "DB unavailable"}
        try:
            # Count matching nodes
            node_count = 0
            try:
                row = conn.execute(
                    "SELECT COUNT(*) as cnt FROM auth_authority_nodes "
                    "WHERE label LIKE ?",
                    (f"%{topic}%",),
                ).fetchone()
                node_count = row["cnt"] if row else 0
            except Exception:
                pass

            # Count matching auth_rules via FTS
            rule_count = 0
            try:
                row = conn.execute(
                    "SELECT COUNT(*) as cnt FROM auth_rules WHERE rowid IN "
                    "(SELECT rowid FROM auth_rules_fts "
                    " WHERE auth_rules_fts MATCH ?)",
                    (topic,),
                ).fetchone()
                rule_count = row["cnt"] if row else 0
            except Exception:
                pass

            # Count matching passages via FTS
            passage_count = 0
            try:
                row = conn.execute(
                    "SELECT COUNT(*) as cnt FROM auth_authority_passages "
                    "WHERE rowid IN "
                    "(SELECT rowid FROM auth_passages_fts "
                    " WHERE auth_passages_fts MATCH ?)",
                    (topic,),
                ).fetchone()
                passage_count = row["cnt"] if row else 0
            except Exception:
                pass

            # Count matching citations
            cite_count = 0
            try:
                row = conn.execute(
                    "SELECT COUNT(*) as cnt FROM master_citations "
                    "WHERE citation LIKE ? OR context LIKE ?",
                    (f"%{topic}%", f"%{topic}%"),
                ).fetchone()
                cite_count = row["cnt"] if row else 0
            except Exception:
                pass

            total = node_count + rule_count + passage_count + cite_count
            if total >= 50:
                strength = "STRONG"
            elif total >= 20:
                strength = "MODERATE"
            elif total >= 5:
                strength = "WEAK"
            else:
                strength = "MINIMAL"

            return {
                "topic": topic,
                "strength": strength,
                "total_supporting": total,
                "breakdown": {
                    "authority_nodes": node_count,
                    "auth_rules": rule_count,
                    "authority_passages": passage_count,
                    "citations": cite_count,
                },
            }
        except Exception as e:
            return {"error": str(e)}
        finally:
            conn.close()

    def visualize_authority_tree(self, root_rule: str) -> Dict:
        """Generate a text-based tree visualization of authority relationships."""
        chain = self.build_authority_chain(root_rule)
        if not chain.get("found"):
            return {
                "root": root_rule,
                "tree": f"[{root_rule}] — not found in authority graph",
                "total_nodes": 0,
            }

        lines: List[str] = []
        start = chain.get("start_node", {})
        label = start.get("label", root_rule)
        ntype = start.get("node_type", "unknown")
        lines.append(f"[{label}] ({ntype})")

        outward = chain.get("outward_edges", [])
        for i, edge in enumerate(outward[:30]):
            prefix = "├── " if i < len(outward) - 1 else "└── "
            target_label = edge.get("target_label", edge.get("target_id", "?"))
            target_type = edge.get("target_type", "")
            edge_type = edge.get("edge_type", "")
            lines.append(
                f"  {prefix}{target_label} ({target_type}) [{edge_type}]"
            )

        inward = chain.get("inward_edges", [])
        if inward:
            lines.append(f"  ╔══ Cited by ({len(inward)} sources):")
            for i, edge in enumerate(inward[:20]):
                prefix = "  ║ ├── " if i < len(inward) - 1 else "  ║ └── "
                src_label = edge.get("source_label", edge.get("source_id", "?"))
                src_type = edge.get("source_type", "")
                lines.append(f"{prefix}{src_label} ({src_type})")

        tree_text = "\n".join(lines)
        return {
            "root": root_rule,
            "tree": tree_text,
            "total_nodes": len(outward) + len(inward) + 1,
        }


# ── CLI ───────────────────────────────────────────────────────────────
if __name__ == "__main__":
    agn = AuthorityGraphNavigator()
    usage = (
        "Authority Graph Navigator Skill\n"
        "Usage:\n"
        "  python authority_graph_navigator.py nodes [TYPE] [LIMIT]\n"
        "  python authority_graph_navigator.py edges [SOURCE_ID] [LIMIT]\n"
        "  python authority_graph_navigator.py graph-nodes [LIMIT]\n"
        "  python authority_graph_navigator.py court-rule [RULE] [LIMIT]\n"
        "  python authority_graph_navigator.py support <TOPIC> [LIMIT]\n"
        "  python authority_graph_navigator.py oppose <TOPIC> [LIMIT]\n"
        "  python authority_graph_navigator.py chain <RULE>\n"
        "  python authority_graph_navigator.py relationships <RULE>\n"
        "  python authority_graph_navigator.py strength <TOPIC>\n"
        "  python authority_graph_navigator.py tree <RULE>\n"
    )

    if len(sys.argv) < 2:
        print(usage)
        sys.exit(0)

    cmd = sys.argv[1].lower()

    if cmd == "nodes":
        ntype = sys.argv[2] if len(sys.argv) > 2 else None
        lim = int(sys.argv[3]) if len(sys.argv) > 3 else 100
        cycle_json(agn.get_authority_nodes(ntype, lim))
    elif cmd == "edges":
        sid = sys.argv[2] if len(sys.argv) > 2 else None
        lim = int(sys.argv[3]) if len(sys.argv) > 3 else 200
        cycle_json(agn.get_authority_edges(sid, lim))
    elif cmd == "graph-nodes":
        lim = int(sys.argv[2]) if len(sys.argv) > 2 else 100
        cycle_json(agn.get_graph_nodes(lim))
    elif cmd == "court-rule":
        rule = sys.argv[2] if len(sys.argv) > 2 else None
        lim = int(sys.argv[3]) if len(sys.argv) > 3 else 100
        cycle_json(agn.get_court_rule_graph(rule, lim))
    elif cmd == "support":
        if len(sys.argv) < 3:
            print("Error: topic required", file=sys.stderr)
            sys.exit(1)
        lim = int(sys.argv[3]) if len(sys.argv) > 3 else 20
        cycle_json(agn.find_supporting_authority(sys.argv[2], lim))
    elif cmd == "oppose":
        if len(sys.argv) < 3:
            print("Error: topic required", file=sys.stderr)
            sys.exit(1)
        lim = int(sys.argv[3]) if len(sys.argv) > 3 else 10
        cycle_json(agn.find_opposing_authority(sys.argv[2], lim))
    elif cmd == "chain":
        if len(sys.argv) < 3:
            print("Error: rule required", file=sys.stderr)
            sys.exit(1)
        cycle_json(agn.build_authority_chain(sys.argv[2]))
    elif cmd == "relationships":
        if len(sys.argv) < 3:
            print("Error: rule number required", file=sys.stderr)
            sys.exit(1)
        cycle_json(agn.get_rule_relationships(sys.argv[2]))
    elif cmd == "strength":
        if len(sys.argv) < 3:
            print("Error: topic required", file=sys.stderr)
            sys.exit(1)
        cycle_json(agn.get_authority_strength(sys.argv[2]))
    elif cmd == "tree":
        if len(sys.argv) < 3:
            print("Error: rule required", file=sys.stderr)
            sys.exit(1)
        result = agn.visualize_authority_tree(sys.argv[2])
        if "tree" in result:
            print(result["tree"])
            print(f"\n--- Total nodes: {result.get('total_nodes', 0)} ---",
                  file=sys.stderr)
        else:
            cycle_json(result)
    else:
        print(usage)
