#!/usr/bin/env python3
"""
Filing Production Runner v1.0 - Agent-154 / LitigationOS
==========================================================
Batch runner: scans all filing stacks, runs pipeline on each,
generates PRODUCTION_MASTER_REPORT.md.

Usage:
    python filing_production_runner.py
    python filing_production_runner.py --stacks 01_COA_366810 02_TRIAL_14TH
    python filing_production_runner.py --quick   (skip production steps)
"""
import sys
sys.stdout.reconfigure(encoding='utf-8')

import os
import re
import json
import argparse
import sqlite3
from pathlib import Path
from datetime import datetime

LITOS_ROOT = Path(r"C:\Users\andre\LitigationOS")
ENGINES_DIR = Path(r"C:\Users\andre\LitigationOS\00_SYSTEM\engines")
SYSTEM_DIR = Path(r"C:\Users\andre\LitigationOS\00_SYSTEM")
DB_PATH = r"C:\Users\andre\LitigationOS\litigation_context.db"

# Import pipeline
sys.path.insert(0, str(ENGINES_DIR))
from filing_production_pipeline import FilingProductionPipeline

# Stack directory patterns (numeric prefix dirs that contain filings)
STACK_PATTERNS = [
    "01_COA*",
    "02_TRIAL*",
    "03_FEDERAL*",
    "04_JTC*",
    "04_MSC*",
    "05_BAR*",
    "06_EMERGENCY*",
    "06_FILINGS*",
]

# Sub-stack patterns (directories within a stack that are themselves stacks)
SUB_STACK_MARKERS = [
    "APEX_FILING_STACK",
    "CONVERGED_FILING_STACK",
    "COURT_READY",
    "FULL_*_STACK",
    "WDMI_FULL_STACK",
]


def discover_stacks(root=LITOS_ROOT, explicit=None):
    """Discover all filing stack directories under LitigationOS root."""
    stacks = []

    if explicit:
        for name in explicit:
            p = root / name
            if not p.exists():
                # Try as absolute
                p = Path(name)
            if p.exists() and p.is_dir():
                stacks.append(p)
            else:
                print(f"  [WARN] Stack not found: {name}")
        return stacks

    # Auto-discover top-level stacks
    for pattern in STACK_PATTERNS:
        import glob as globmod
        matches = sorted(globmod.glob(str(root / pattern)))
        for m in matches:
            mp = Path(m)
            if mp.is_dir():
                stacks.append(mp)

    return stacks


def run_all(stacks, verbose=True):
    """Run the pipeline on every discovered stack. Return list of results."""
    results = []
    total = len(stacks)

    for i, stack_path in enumerate(stacks, 1):
        print(f"\n{'#' * 70}")
        print(f"# STACK {i}/{total}: {stack_path.name}")
        print(f"{'#' * 70}")

        try:
            pipeline = FilingProductionPipeline(str(stack_path), verbose=verbose)
            result = pipeline.run()
            results.append(result)
        except Exception as e:
            print(f"  [ERROR] Pipeline failed for {stack_path.name}: {e}")
            results.append({
                "stack": stack_path.name,
                "path": str(stack_path),
                "court": {"court": "Unknown"},
                "go_nogo": "ERROR",
                "steps_passed": 0,
                "steps_total": 11,
                "documents": 0,
                "evidence_files": 0,
                "output_dir": "",
                "elapsed": 0,
                "error": str(e),
            })

    return results


def generate_master_report(results, output_path=None):
    """Generate the master production report across all stacks."""
    if output_path is None:
        output_path = SYSTEM_DIR / "PRODUCTION_MASTER_REPORT.md"

    now = datetime.now()
    go_count = sum(1 for r in results if r["go_nogo"] == "GO")
    nogo_count = sum(1 for r in results if r["go_nogo"] == "NO-GO")
    err_count = sum(1 for r in results if r["go_nogo"] == "ERROR")
    total_docs = sum(r.get("documents", 0) for r in results)
    total_evidence = sum(r.get("evidence_files", 0) for r in results)
    total_elapsed = sum(r.get("elapsed", 0) for r in results)

    with open(output_path, "w", encoding="utf-8") as f:
        f.write("# PRODUCTION MASTER REPORT\n\n")
        f.write(f"**Generated:** {now.strftime('%Y-%m-%d %H:%M:%S')}\n")
        f.write(f"**Pipeline:** Filing Production Pipeline v1.0\n")
        f.write(f"**Agent:** Agent-154\n\n")

        f.write("## Executive Summary\n\n")
        f.write(f"| Metric | Value |\n")
        f.write(f"|--------|-------|\n")
        f.write(f"| Total Stacks Processed | {len(results)} |\n")
        f.write(f"| GO (Court-Ready) | {go_count} |\n")
        f.write(f"| NO-GO (Needs Work) | {nogo_count} |\n")
        f.write(f"| ERROR (Pipeline Failure) | {err_count} |\n")
        f.write(f"| Total Documents Scanned | {total_docs} |\n")
        f.write(f"| Total Evidence Files | {total_evidence} |\n")
        f.write(f"| Total Processing Time | {total_elapsed:.1f}s |\n\n")

        # Readiness matrix
        f.write("## Filing Readiness Matrix\n\n")
        f.write("| Stack | Court | Verdict | Steps | Docs | Evidence | Time |\n")
        f.write("|-------|-------|---------|-------|------|----------|------|\n")
        for r in results:
            verdict = r["go_nogo"]
            if verdict == "GO":
                badge = "[GO]"
            elif verdict == "NO-GO":
                badge = "[NO-GO]"
            else:
                badge = "[ERROR]"
            court = r.get("court", {}).get("court", "Unknown")
            steps = f"{r.get('steps_passed', 0)}/{r.get('steps_total', 11)}"
            f.write(f"| {r['stack']} | {court} | {badge} "
                    f"| {steps} | {r.get('documents', 0)} "
                    f"| {r.get('evidence_files', 0)} "
                    f"| {r.get('elapsed', 0):.1f}s |\n")

        # Per-stack details
        f.write("\n## Per-Stack Details\n\n")
        for r in results:
            f.write(f"### {r['stack']}\n\n")
            f.write(f"- **Path:** `{r.get('path', 'N/A')}`\n")
            f.write(f"- **Court:** {r.get('court', {}).get('court', 'Unknown')}\n")
            f.write(f"- **Verdict:** {r['go_nogo']}\n")
            f.write(f"- **Steps Passed:** {r.get('steps_passed', 0)}/{r.get('steps_total', 11)}\n")
            f.write(f"- **Documents:** {r.get('documents', 0)}\n")
            f.write(f"- **Evidence:** {r.get('evidence_files', 0)}\n")
            if r.get("output_dir"):
                f.write(f"- **Output:** `{r['output_dir']}`\n")
            if r.get("error"):
                f.write(f"- **Error:** {r['error']}\n")
            f.write("\n")

        # Action items
        nogo_stacks = [r for r in results if r["go_nogo"] in ("NO-GO", "ERROR")]
        if nogo_stacks:
            f.write("## Action Items\n\n")
            for i, r in enumerate(nogo_stacks, 1):
                f.write(f"{i}. **{r['stack']}** -- {r['go_nogo']}. ")
                f.write(f"Check `{r.get('output_dir', 'N/A')}/PRODUCTION_REPORT.md` for details.\n")
            f.write("\n")

        f.write("---\n")
        f.write(f"*Report generated by Filing Production Runner v1.0 / Agent-154*\n")

    # Also write JSON
    json_path = output_path.with_suffix('.json')
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump({
            "generated": now.isoformat(),
            "summary": {
                "total": len(results),
                "go": go_count,
                "nogo": nogo_count,
                "error": err_count,
                "total_documents": total_docs,
                "total_evidence": total_evidence,
                "elapsed_seconds": round(total_elapsed, 2),
            },
            "results": results,
        }, f, indent=2, default=str)

    # Log to DB
    try:
        conn = sqlite3.connect(DB_PATH, timeout=120)
        conn.execute("PRAGMA busy_timeout=60000")
        conn.execute("PRAGMA journal_mode=WAL")
        conn.execute("PRAGMA cache_size=-32000")
        conn.execute("""CREATE TABLE IF NOT EXISTS production_master_runs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            stacks_processed INTEGER,
            go_count INTEGER,
            nogo_count INTEGER,
            error_count INTEGER,
            total_documents INTEGER,
            total_evidence INTEGER,
            elapsed_seconds REAL,
            report_path TEXT,
            run_timestamp TEXT DEFAULT CURRENT_TIMESTAMP
        )""")
        conn.execute("""INSERT INTO production_master_runs
            (stacks_processed, go_count, nogo_count, error_count,
             total_documents, total_evidence, elapsed_seconds, report_path)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
            (len(results), go_count, nogo_count, err_count,
             total_docs, total_evidence, round(total_elapsed, 2),
             str(output_path)))
        conn.commit()
        conn.close()
    except Exception as e:
        print(f"  [WARN] DB log failed: {e}")

    return str(output_path)


def main():
    parser = argparse.ArgumentParser(
        description="Filing Production Runner - batch pipeline execution")
    parser.add_argument("--stacks", nargs="*", default=None,
                        help="Specific stack names to process (default: auto-discover all)")
    parser.add_argument("--quiet", action="store_true",
                        help="Suppress verbose output")
    args = parser.parse_args()

    print("=" * 70)
    print("  FILING PRODUCTION RUNNER v1.0 -- Agent-154")
    print(f"  Root: {LITOS_ROOT}")
    print(f"  Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 70)

    # Discover stacks
    stacks = discover_stacks(explicit=args.stacks)
    print(f"\nDiscovered {len(stacks)} filing stacks:")
    for s in stacks:
        print(f"  --> {s.name}")

    if not stacks:
        print("\n[WARN] No stacks found. Nothing to process.")
        return 0

    # Run pipeline on each
    results = run_all(stacks, verbose=not args.quiet)

    # Generate master report
    report_path = generate_master_report(results)

    # Final summary
    go_count = sum(1 for r in results if r["go_nogo"] == "GO")
    nogo_count = sum(1 for r in results if r["go_nogo"] in ("NO-GO", "ERROR"))

    print(f"\n{'=' * 70}")
    print(f"  MASTER REPORT: {report_path}")
    print(f"  GO: {go_count} | NO-GO/ERROR: {nogo_count} | TOTAL: {len(results)}")
    print(f"{'=' * 70}")

    return 0 if nogo_count == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
