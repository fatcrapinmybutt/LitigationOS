#!/usr/bin/env python3
"""
LitigationOS Convergence Cycle Runner

Runs a full convergence cycle: self-test -> audit -> status -> report.
Run: python convergence_cycle.py [--db-path PATH]

Requires: litigation_context_mcp installed (pip install -e .)
"""

import os
import sys
import time
import json
import sqlite3


DEFAULT_DB = os.path.join(os.path.expanduser("~"), "litigation_context.db")


def get_connection(db_path):
    """Get a database connection with standard PRAGMAs."""
    conn = sqlite3.connect(db_path, timeout=30)
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA busy_timeout=10000")
    conn.execute("PRAGMA foreign_keys=ON")
    conn.row_factory = sqlite3.Row
    return conn


def run_self_test(conn):
    """Quick stack validation."""
    results = {}
    
    # DB connection
    results["db_connect"] = "PASS"
    
    # Schema check
    tables = [r[0] for r in conn.execute(
        "SELECT name FROM sqlite_master WHERE type='table'"
    ).fetchall()]
    expected = ["documents", "pages", "graph_nodes", "court_rules", "md_sections"]
    missing = [t for t in expected if t not in tables]
    results["schema"] = "PASS" if not missing else f"FAIL: missing {missing}"
    
    # FTS5 read/write test
    try:
        conn.execute("SELECT * FROM pages_fts WHERE pages_fts MATCH 'test' LIMIT 1")
        results["fts5_read"] = "PASS"
    except Exception as e:
        results["fts5_read"] = f"FAIL: {e}"
    
    # Graph nodes
    try:
        count = conn.execute("SELECT COUNT(*) FROM graph_nodes").fetchone()[0]
        results["graph_nodes"] = f"PASS ({count} nodes)" if count > 0 else "WARN: 0 nodes"
    except Exception as e:
        results["graph_nodes"] = f"FAIL: {e}"
    
    return results


def run_audit(conn):
    """Data quality analysis with score."""
    score = 0
    findings = []
    
    # 1. Document coverage (20%)
    try:
        doc_count = conn.execute("SELECT COUNT(*) FROM documents").fetchone()[0]
        if doc_count >= 10:
            score += 20
        elif doc_count >= 5:
            score += 15
            findings.append(f"Only {doc_count} documents ingested (target: 10+)")
        elif doc_count >= 1:
            score += 10
            findings.append(f"Only {doc_count} documents ingested (target: 10+)")
        else:
            findings.append("No documents ingested")
    except:
        findings.append("documents table missing")
    
    # 2. FTS sync (15%)
    try:
        pages = conn.execute("SELECT COUNT(*) FROM pages").fetchone()[0]
        fts = conn.execute("SELECT COUNT(*) FROM pages_fts").fetchone()[0]
        if pages == fts and pages > 0:
            score += 15
        elif pages > 0:
            findings.append(f"FTS desync: pages={pages}, fts={fts}")
            score += 5
    except:
        findings.append("FTS tables missing")
    
    # 3. Graph coverage (15%)
    try:
        sources = conn.execute(
            "SELECT COUNT(DISTINCT source) FROM graph_nodes"
        ).fetchone()[0]
        if sources >= 7:
            score += 15
        elif sources >= 4:
            score += 10
            findings.append(f"Only {sources}/8 graph sources loaded")
        else:
            score += 5
            findings.append(f"Only {sources}/8 graph sources loaded")
    except:
        findings.append("graph_nodes table missing")
    
    # 4. Cross-ref density (15%)
    try:
        sections = conn.execute("SELECT COUNT(*) FROM md_sections").fetchone()[0]
        refs = conn.execute("SELECT COUNT(*) FROM md_cross_refs").fetchone()[0]
        density = refs / max(sections, 1)
        if density >= 1.5:
            score += 15
        elif density >= 0.5:
            score += 10
            findings.append(f"Cross-ref density {density:.2f} (target: 1.5+)")
        else:
            score += 5
            findings.append(f"Low cross-ref density: {density:.2f}")
    except:
        findings.append("md_sections/md_cross_refs tables missing")
    
    # 5. Graph link rate (15%)
    try:
        total_refs = conn.execute("SELECT COUNT(*) FROM md_cross_refs").fetchone()[0]
        linked = conn.execute(
            "SELECT COUNT(*) FROM md_cross_refs WHERE graph_node_id IS NOT NULL"
        ).fetchone()[0]
        link_rate = linked / max(total_refs, 1) * 100
        if link_rate >= 60:
            score += 15
        elif link_rate >= 30:
            score += 10
            findings.append(f"Graph link rate {link_rate:.1f}% (target: 60%+)")
        else:
            score += 5
            findings.append(f"Low graph link rate: {link_rate:.1f}%")
    except:
        pass
    
    # 6. Risk completeness (10%)
    try:
        risk_count = conn.execute("SELECT COUNT(*) FROM risk_events").fetchone()[0]
        if risk_count >= 21:
            score += 10
        elif risk_count >= 10:
            score += 5
            findings.append(f"Only {risk_count}/21 risk events")
        else:
            findings.append(f"Only {risk_count}/21 risk events")
    except:
        findings.append("risk_events table missing")
    
    # 7. Evolution coverage (10%)
    try:
        evolved = conn.execute(
            "SELECT COUNT(DISTINCT source_file) FROM md_sections"
        ).fetchone()[0]
        if evolved >= 50:
            score += 10
        elif evolved >= 20:
            score += 7
            findings.append(f"Only {evolved} files evolved (target: 50+)")
        elif evolved >= 5:
            score += 4
            findings.append(f"Only {evolved} files evolved (target: 50+)")
        else:
            findings.append(f"Only {evolved} files evolved")
    except:
        findings.append("md_sections table missing")
    
    return score, findings


def get_convergence_status(conn):
    """Get DNEW, BLOCKERS, NEXT_PATCH."""
    status = {"DNEW": [], "BLOCKERS": [], "NEXT_PATCH": None}
    
    # Check for recent additions (DNEW)
    try:
        recent = conn.execute("""
            SELECT COUNT(*) FROM md_sections 
            WHERE created_at > datetime('now', '-24 hours')
        """).fetchone()[0]
        if recent > 0:
            status["DNEW"].append(f"{recent} sections added in last 24h")
    except:
        pass
    
    # Check for blockers
    try:
        sources = conn.execute(
            "SELECT COUNT(DISTINCT source) FROM graph_nodes"
        ).fetchone()[0]
        if sources < 8:
            status["BLOCKERS"].append(f"Only {sources}/8 knowledge graphs loaded")
    except:
        status["BLOCKERS"].append("Cannot check graph coverage")
    
    try:
        doc_count = conn.execute("SELECT COUNT(*) FROM documents").fetchone()[0]
        if doc_count < 5:
            status["BLOCKERS"].append(f"Only {doc_count} PDFs ingested (many available)")
    except:
        pass
    
    # Determine NEXT_PATCH
    if status["BLOCKERS"]:
        status["NEXT_PATCH"] = status["BLOCKERS"][0].replace("Only ", "Fix: load more - ")
    elif not status["DNEW"]:
        status["NEXT_PATCH"] = "System appears converged - switch to EMERGENCE mode"
    else:
        status["NEXT_PATCH"] = "Continue processing - new content being added"
    
    return status


def main():
    db_path = DEFAULT_DB
    if len(sys.argv) > 2 and sys.argv[1] == "--db-path":
        db_path = sys.argv[2]

    print("=" * 60)
    print("  LitigationOS Convergence Cycle")
    print("=" * 60)
    print()

    if not os.path.exists(db_path):
        print(f"ERROR: Database not found at {db_path}")
        sys.exit(1)

    conn = get_connection(db_path)
    start = time.time()

    # Step 1: Self-test
    print("[1/3] Running self-test...")
    test_results = run_self_test(conn)
    for name, result in test_results.items():
        icon = "+" if "PASS" in result else ("!" if "WARN" in result else "X")
        print(f"  [{icon}] {name}: {result}")
    
    failures = sum(1 for v in test_results.values() if "FAIL" in v)
    if failures > 0:
        print(f"\n  BLOCKED: {failures} test failures. Fix before continuing.")
        conn.close()
        sys.exit(1)

    # Step 2: Audit
    print("\n[2/3] Running quality audit...")
    score, findings = run_audit(conn)
    print(f"  Quality Score: {score}/100")
    for finding in findings:
        print(f"  [!] {finding}")

    # Step 3: Convergence status
    print("\n[3/3] Checking convergence...")
    status = get_convergence_status(conn)
    
    if status["DNEW"]:
        print("  DNEW:")
        for item in status["DNEW"]:
            print(f"    + {item}")
    else:
        print("  DNEW: (empty)")
    
    if status["BLOCKERS"]:
        print("  BLOCKERS:")
        for item in status["BLOCKERS"]:
            print(f"    X {item}")
    else:
        print("  BLOCKERS: (none)")
    
    print(f"  NEXT_PATCH: {status['NEXT_PATCH']}")

    elapsed = time.time() - start
    conn.close()

    # Summary
    print()
    print("-" * 60)
    if score >= 95 and not status["BLOCKERS"]:
        print("  CONVERGED - Ready for EMERGENCE mode")
    elif score >= 80:
        print(f"  GOOD ({score}/100) - Continue convergence cycles")
    elif score >= 60:
        print(f"  NEEDS WORK ({score}/100) - Focus on BLOCKERS")
    else:
        print(f"  CRITICAL ({score}/100) - Major ingestion/repair needed")
    print(f"  Completed in {elapsed:.1f}s")


if __name__ == "__main__":
    main()
