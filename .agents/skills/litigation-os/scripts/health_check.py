#!/usr/bin/env python3
"""
LitigationOS Health Check Script

Quick diagnostic of MCP server and database health.
Run: python health_check.py [--db-path PATH]
"""

import os
import sys
import time
import sqlite3
import json


DEFAULT_DB = os.path.join(os.path.expanduser("~"), "litigation_context.db")


def check_database(db_path):
    """Check database connectivity and basic health."""
    results = []

    # 1. File exists
    if not os.path.exists(db_path):
        results.append(("DB File", "FAIL", f"Not found: {db_path}"))
        return results
    
    size_mb = os.path.getsize(db_path) / (1024 * 1024)
    results.append(("DB File", "PASS", f"{size_mb:.1f} MB at {db_path}"))

    # 2. Connection
    try:
        conn = sqlite3.connect(db_path, timeout=10)
        conn.execute("PRAGMA journal_mode=WAL")
        conn.execute("PRAGMA busy_timeout=10000")
        results.append(("DB Connect", "PASS", "Connected with WAL mode"))
    except Exception as e:
        results.append(("DB Connect", "FAIL", str(e)))
        return results

    # 3. Schema check
    try:
        tables = [r[0] for r in conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table' ORDER BY name"
        ).fetchall()]
        expected = ["documents", "pages", "graph_nodes", "court_rules", "md_sections"]
        missing = [t for t in expected if t not in tables]
        if missing:
            results.append(("Schema", "WARN", f"Missing tables: {missing}"))
        else:
            results.append(("Schema", "PASS", f"{len(tables)} tables found"))
    except Exception as e:
        results.append(("Schema", "FAIL", str(e)))

    # 4. Row counts
    try:
        counts = {}
        for table in ["documents", "pages", "graph_nodes", "court_rules", 
                       "md_sections", "md_cross_refs", "risk_events"]:
            if table in tables:
                count = conn.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0]
                counts[table] = count
        results.append(("Row Counts", "PASS", json.dumps(counts, indent=2)))
    except Exception as e:
        results.append(("Row Counts", "WARN", str(e)))

    # 5. FTS5 health
    try:
        if "pages_fts" in tables:
            fts_count = conn.execute("SELECT COUNT(*) FROM pages_fts").fetchone()[0]
            page_count = counts.get("pages", 0)
            if fts_count == page_count:
                results.append(("FTS5 Sync", "PASS", f"{fts_count} rows in sync"))
            else:
                results.append(("FTS5 Sync", "WARN", 
                    f"Desync: pages={page_count}, FTS={fts_count}"))
        else:
            results.append(("FTS5 Sync", "WARN", "pages_fts table not found"))
    except Exception as e:
        results.append(("FTS5 Sync", "FAIL", str(e)))

    # 6. Integrity check
    try:
        integrity = conn.execute("PRAGMA integrity_check(1)").fetchone()[0]
        results.append(("Integrity", "PASS" if integrity == "ok" else "FAIL", integrity))
    except Exception as e:
        results.append(("Integrity", "FAIL", str(e)))

    # 7. Disk space
    try:
        import shutil
        drive = os.path.splitdrive(db_path)[0] or "/"
        usage = shutil.disk_usage(drive + "\\")
        free_gb = usage.free / (1024**3)
        status = "PASS" if free_gb > 1.0 else ("WARN" if free_gb > 0.1 else "FAIL")
        results.append(("Disk Space", status, f"{free_gb:.1f} GB free on {drive}"))
    except Exception as e:
        results.append(("Disk Space", "WARN", str(e)))

    conn.close()
    return results


def check_mcp_server():
    """Check if the MCP server module is importable."""
    results = []
    try:
        import litigation_context_mcp
        results.append(("MCP Import", "PASS", "litigation_context_mcp importable"))
    except ImportError as e:
        results.append(("MCP Import", "FAIL", f"Cannot import: {e}"))
    
    try:
        import pymupdf
        results.append(("PyMuPDF", "PASS", f"Version {pymupdf.__version__}"))
    except ImportError:
        results.append(("PyMuPDF", "FAIL", "pymupdf not installed"))

    try:
        import mcp
        results.append(("MCP SDK", "PASS", "MCP SDK available"))
    except ImportError:
        results.append(("MCP SDK", "FAIL", "mcp not installed"))

    return results


def check_knowledge_graphs(graph_dir=None):
    """Check knowledge graph files."""
    results = []
    if graph_dir is None:
        graph_dir = os.path.join(os.path.expanduser("~"), "Scans")
    
    expected_graphs = [
        "MasterGraph.json",
        "MASTER_COURT_FORMS_GRAPH_v2.json",
        "MI_AuthorityFormsGraph.json",
        "rules_authority_index.json",
        "rules_extracted.json",
        "MCR_organized.json",
        "risk_event_types.json",
    ]
    
    found = 0
    for graph in expected_graphs:
        path = os.path.join(graph_dir, graph)
        if os.path.exists(path):
            size_kb = os.path.getsize(path) / 1024
            found += 1
        
    results.append(("Knowledge Graphs", 
                     "PASS" if found >= 5 else "WARN",
                     f"{found}/{len(expected_graphs)} graph files found in {graph_dir}"))
    return results


def main():
    db_path = DEFAULT_DB
    if len(sys.argv) > 2 and sys.argv[1] == "--db-path":
        db_path = sys.argv[2]

    print("=" * 60)
    print("  LitigationOS Health Check")
    print("=" * 60)
    print()

    start = time.time()
    all_results = []

    print("[1/3] Checking MCP server dependencies...")
    all_results.extend(check_mcp_server())

    print("[2/3] Checking database...")
    all_results.extend(check_database(db_path))

    print("[3/3] Checking knowledge graphs...")
    all_results.extend(check_knowledge_graphs())

    elapsed = time.time() - start

    print()
    print("-" * 60)
    passes = sum(1 for _, s, _ in all_results if s == "PASS")
    warns = sum(1 for _, s, _ in all_results if s == "WARN")
    fails = sum(1 for _, s, _ in all_results if s == "FAIL")

    for name, status, detail in all_results:
        icon = {"PASS": "+", "WARN": "!", "FAIL": "X"}[status]
        print(f"  [{icon}] {status:4s} | {name:20s} | {detail}")

    print("-" * 60)
    print(f"  Total: {passes} PASS, {warns} WARN, {fails} FAIL  ({elapsed:.1f}s)")
    
    if fails > 0:
        print("  STATUS: UNHEALTHY - fix FAIL items above")
        sys.exit(1)
    elif warns > 0:
        print("  STATUS: DEGRADED - review WARN items")
        sys.exit(0)
    else:
        print("  STATUS: HEALTHY")
        sys.exit(0)


if __name__ == "__main__":
    main()
