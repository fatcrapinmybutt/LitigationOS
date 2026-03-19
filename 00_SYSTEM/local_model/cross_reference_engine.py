"""
Cross-Reference Engine — LitigationOS 2026
Traces document evolution, cross-references, and reference graphs across
md_cross_refs (69,744 rows) and md_evolution_log (1,388 rows) for
Pigors v. Watson consolidated litigation.
"""

import json
import os
import sqlite3
import sys
from collections import Counter, defaultdict
from typing import Any, Dict, List, Optional

DB_PATH = os.environ.get("LITIGATION_DB_PATH", r"C:\Users\andre\LitigationOS\litigation_context.db")


def _get_db() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH, timeout=30)
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA query_only=ON")
    conn.row_factory = sqlite3.Row
    return conn


class CrossReferenceEngine:
    """Traces document cross-references, evolution, and reference graphs."""

    def get_cross_refs(
        self, source_file: Optional[str] = None, limit: int = 100
    ) -> List[Dict[str, Any]]:
        """Query md_cross_refs table (69,744 rows).
        Columns: id, section_id, ref_type, ref_value, graph_node_id, graph_source, confidence.
        """
        conn = _get_db()
        try:
            if source_file:
                rows = conn.execute(
                    """SELECT * FROM md_cross_refs
                       WHERE ref_value LIKE ? OR graph_node_id LIKE ? OR graph_source LIKE ?
                       ORDER BY id DESC LIMIT ?""",
                    (f"%{source_file}%", f"%{source_file}%", f"%{source_file}%", limit),
                ).fetchall()
            else:
                rows = conn.execute(
                    "SELECT * FROM md_cross_refs ORDER BY id DESC LIMIT ?",
                    (limit,),
                ).fetchall()
            return [dict(r) for r in rows]
        finally:
            conn.close()

    def get_evolution_log(
        self, source_file: Optional[str] = None, limit: int = 50
    ) -> List[Dict[str, Any]]:
        """Query md_evolution_log table (1,388 rows).
        Columns: source_path, evolved_at, section_count, cross_ref_count, file_size_bytes, sha256_hash.
        """
        conn = _get_db()
        try:
            if source_file:
                rows = conn.execute(
                    """SELECT * FROM md_evolution_log
                       WHERE source_path LIKE ?
                       ORDER BY evolved_at DESC LIMIT ?""",
                    (f"%{source_file}%", limit),
                ).fetchall()
            else:
                rows = conn.execute(
                    "SELECT * FROM md_evolution_log ORDER BY evolved_at DESC LIMIT ?",
                    (limit,),
                ).fetchall()
            return [dict(r) for r in rows]
        finally:
            conn.close()

    def trace_document_evolution(self, file_path: str) -> Dict[str, Any]:
        """Trace how a document evolved over time via md_evolution_log."""
        conn = _get_db()
        try:
            evolutions = conn.execute(
                """SELECT * FROM md_evolution_log
                   WHERE source_path LIKE ?
                   ORDER BY evolved_at ASC""",
                (f"%{file_path}%",),
            ).fetchall()

            # Also find cross-refs that reference this document
            refs_to = conn.execute(
                """SELECT * FROM md_cross_refs
                   WHERE ref_value LIKE ? OR graph_node_id LIKE ?
                   ORDER BY id ASC""",
                (f"%{file_path}%", f"%{file_path}%"),
            ).fetchall()

            return {
                "file_path": file_path,
                "evolution_entries": [dict(r) for r in evolutions],
                "evolution_count": len(evolutions),
                "related_cross_refs": [dict(r) for r in refs_to],
                "cross_ref_count": len(refs_to),
            }
        finally:
            conn.close()

    def find_cross_references(self, topic: str) -> List[Dict[str, Any]]:
        """Find all cross-references related to a topic."""
        conn = _get_db()
        try:
            # Search in source_file, target_ref, and any text columns
            cols = conn.execute("PRAGMA table_info(md_cross_refs)").fetchall()
            col_names = [c["name"] for c in cols]

            conditions = []
            params = []
            for col in col_names:
                conditions.append(f"{col} LIKE ?")
                params.append(f"%{topic}%")

            query = f"""SELECT * FROM md_cross_refs
                        WHERE {' OR '.join(conditions)}
                        ORDER BY rowid DESC LIMIT 200"""
            rows = conn.execute(query, params).fetchall()
            return [dict(r) for r in rows]
        finally:
            conn.close()

    def build_reference_graph(self, starting_doc: str) -> Dict[str, Any]:
        """Build graph of document cross-references starting from a document.
        Uses graph_node_id as node identifier and ref_value/graph_source as edges.
        """
        conn = _get_db()
        try:
            # Find refs where graph_node_id or ref_value matches starting doc
            outgoing = conn.execute(
                """SELECT * FROM md_cross_refs
                   WHERE graph_node_id LIKE ?
                   LIMIT 500""",
                (f"%{starting_doc}%",),
            ).fetchall()

            incoming = conn.execute(
                """SELECT * FROM md_cross_refs
                   WHERE ref_value LIKE ?
                   LIMIT 500""",
                (f"%{starting_doc}%",),
            ).fetchall()

            nodes = set()
            edges = []
            nodes.add(starting_doc)

            for r in outgoing:
                rd = dict(r)
                target = rd.get("ref_value", "unknown")
                nodes.add(target)
                edges.append({
                    "source": starting_doc,
                    "target": target,
                    "ref_type": rd.get("ref_type"),
                    "graph_source": rd.get("graph_source"),
                    "confidence": rd.get("confidence"),
                    "direction": "outgoing",
                })

            for r in incoming:
                rd = dict(r)
                source = rd.get("graph_node_id", "unknown")
                nodes.add(source)
                edges.append({
                    "source": source,
                    "target": starting_doc,
                    "ref_type": rd.get("ref_type"),
                    "graph_source": rd.get("graph_source"),
                    "confidence": rd.get("confidence"),
                    "direction": "incoming",
                })

            return {
                "starting_document": starting_doc,
                "nodes": list(nodes),
                "node_count": len(nodes),
                "edges": edges,
                "edge_count": len(edges),
                "outgoing_refs": len(outgoing),
                "incoming_refs": len(incoming),
            }
        finally:
            conn.close()

    def find_orphaned_references(self) -> Dict[str, Any]:
        """Find graph_node_id values not matching any known document or evolution path."""
        conn = _get_db()
        try:
            # Get all unique graph_node_ids
            node_ids = conn.execute(
                "SELECT DISTINCT graph_node_id FROM md_cross_refs WHERE graph_node_id IS NOT NULL LIMIT 5000"
            ).fetchall()

            # Get known evolution source_paths
            known_paths = set()
            try:
                paths = conn.execute(
                    "SELECT DISTINCT source_path FROM md_evolution_log"
                ).fetchall()
                known_paths = {r["source_path"] for r in paths if r["source_path"]}
            except sqlite3.OperationalError:
                pass

            # Also check documents table
            try:
                docs = conn.execute(
                    "SELECT DISTINCT file_path FROM documents"
                ).fetchall()
                known_paths.update(r["file_path"] for r in docs if r["file_path"])
            except sqlite3.OperationalError:
                pass

            # Node IDs that don't match any known path (orphaned graph nodes)
            all_nodes = {r["graph_node_id"] for r in node_ids}

            # Check ref_values that have no corresponding graph_node_id
            ref_values = conn.execute(
                "SELECT DISTINCT ref_value FROM md_cross_refs WHERE ref_value IS NOT NULL LIMIT 5000"
            ).fetchall()
            all_ref_values = {r["ref_value"] for r in ref_values}

            return {
                "total_unique_nodes": len(all_nodes),
                "total_unique_ref_values": len(all_ref_values),
                "known_document_paths": len(known_paths),
                "sample_nodes": sorted(list(all_nodes))[:50],
                "sample_ref_values": sorted(list(all_ref_values))[:50],
            }
        finally:
            conn.close()

    def get_most_referenced_documents(self, limit: int = 20) -> List[Dict[str, Any]]:
        """Graph nodes cited most often in cross-references."""
        conn = _get_db()
        try:
            rows = conn.execute(
                """SELECT graph_node_id, ref_type, COUNT(*) as ref_count
                   FROM md_cross_refs
                   WHERE graph_node_id IS NOT NULL AND graph_node_id != ''
                   GROUP BY graph_node_id
                   ORDER BY ref_count DESC
                   LIMIT ?""",
                (limit,),
            ).fetchall()
            return [dict(r) for r in rows]
        finally:
            conn.close()

    def get_statistics(self) -> Dict[str, Any]:
        """Total refs, evolution entries, top referenced docs."""
        conn = _get_db()
        try:
            ref_count = conn.execute(
                "SELECT COUNT(*) as cnt FROM md_cross_refs"
            ).fetchone()["cnt"]

            evo_count = conn.execute(
                "SELECT COUNT(*) as cnt FROM md_evolution_log"
            ).fetchone()["cnt"]

            unique_nodes = conn.execute(
                "SELECT COUNT(DISTINCT graph_node_id) as cnt FROM md_cross_refs"
            ).fetchone()["cnt"]

            unique_ref_values = conn.execute(
                "SELECT COUNT(DISTINCT ref_value) as cnt FROM md_cross_refs"
            ).fetchone()["cnt"]

            unique_ref_types = conn.execute(
                "SELECT ref_type, COUNT(*) as cnt FROM md_cross_refs GROUP BY ref_type ORDER BY cnt DESC"
            ).fetchall()

            top_refs = conn.execute(
                """SELECT graph_node_id, COUNT(*) as ref_count
                   FROM md_cross_refs
                   WHERE graph_node_id IS NOT NULL AND graph_node_id != ''
                   GROUP BY graph_node_id
                   ORDER BY ref_count DESC
                   LIMIT 10"""
            ).fetchall()

            ref_cols = conn.execute("PRAGMA table_info(md_cross_refs)").fetchall()
            evo_cols = conn.execute("PRAGMA table_info(md_evolution_log)").fetchall()

            return {
                "total_cross_refs": ref_count,
                "total_evolution_entries": evo_count,
                "unique_graph_nodes": unique_nodes,
                "unique_ref_values": unique_ref_values,
                "ref_types": [dict(r) for r in unique_ref_types],
                "top_referenced_nodes": [dict(r) for r in top_refs],
                "cross_refs_columns": [c["name"] for c in ref_cols],
                "evolution_log_columns": [c["name"] for c in evo_cols],
            }
        finally:
            conn.close()


def self_test() -> Dict[str, Any]:
    """Run self-test to verify database connectivity and table access."""
    results = {"status": "ok", "tests": {}}
    cre = CrossReferenceEngine()

    try:
        stats = cre.get_statistics()
        results["tests"]["statistics"] = {
            "passed": stats["total_cross_refs"] > 0,
            "cross_refs": stats["total_cross_refs"],
            "evolution_entries": stats["total_evolution_entries"],
        }
    except Exception as e:
        results["tests"]["statistics"] = {"passed": False, "error": str(e)}

    try:
        refs = cre.get_cross_refs(limit=5)
        results["tests"]["get_cross_refs"] = {
            "passed": isinstance(refs, list),
            "count": len(refs),
        }
    except Exception as e:
        results["tests"]["get_cross_refs"] = {"passed": False, "error": str(e)}

    try:
        evo = cre.get_evolution_log(limit=5)
        results["tests"]["get_evolution_log"] = {
            "passed": isinstance(evo, list),
            "count": len(evo),
        }
    except Exception as e:
        results["tests"]["get_evolution_log"] = {"passed": False, "error": str(e)}

    try:
        top = cre.get_most_referenced_documents(limit=5)
        results["tests"]["most_referenced"] = {
            "passed": isinstance(top, list),
            "count": len(top),
        }
    except Exception as e:
        results["tests"]["most_referenced"] = {"passed": False, "error": str(e)}

    results["status"] = (
        "ok" if all(t.get("passed") for t in results["tests"].values()) else "degraded"
    )
    return results


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "test":
        print(json.dumps(self_test(), indent=2, default=str))
    elif len(sys.argv) > 1 and sys.argv[1] == "stats":
        cre = CrossReferenceEngine()
        print(json.dumps(cre.get_statistics(), indent=2, default=str))
    elif len(sys.argv) > 1 and sys.argv[1] == "trace" and len(sys.argv) > 2:
        cre = CrossReferenceEngine()
        print(json.dumps(cre.trace_document_evolution(sys.argv[2]), indent=2, default=str))
    elif len(sys.argv) > 1 and sys.argv[1] == "graph" and len(sys.argv) > 2:
        cre = CrossReferenceEngine()
        print(json.dumps(cre.build_reference_graph(sys.argv[2]), indent=2, default=str))
    elif len(sys.argv) > 1 and sys.argv[1] == "top":
        cre = CrossReferenceEngine()
        print(json.dumps(cre.get_most_referenced_documents(), indent=2, default=str))
    else:
        print("Usage: python cross_reference_engine.py [test|stats|trace <path>|graph <doc>|top]")
