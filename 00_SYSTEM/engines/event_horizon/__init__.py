"""
EVENT HORIZON Δ∞ — The Autonomous-Multi-Agent-Omega-Engine
===========================================================

12-subsystem engine for intelligent, self-evolving filesystem organization.

Usage:
    python -m event_horizon --zone ROOT --dry-run
    python -m event_horizon --zone ROOT --execute
    python -m event_horizon --zone 06_DATA --dry-run
    python -m event_horizon --census
"""
from __future__ import annotations

import argparse
import json
import logging
import sys
from datetime import datetime
from pathlib import Path
from typing import Optional

from .models import REPO_ROOT, RoutingPlan, MoveMetrics, QualityReport
from .state import StateDB
from .genesis import Genesis
from .oracle import Oracle
from .promethean import Promethean
from .elysium import Elysium

__version__ = "1.0.0"
__codename__ = "EVENT HORIZON Δ∞"

log = logging.getLogger("event_horizon")


class Engine:
    """EVENT HORIZON Δ∞ — Autonomous filesystem intelligence engine.
    
    Pipeline: GENESIS → ORACLE → PROMETHEAN → ELYSIUM
    
    Usage:
        engine = Engine()
        report = engine.run("ROOT", dry_run=True)
        print(report.summary())
    """

    def __init__(self, root: Path = REPO_ROOT, db_path: Optional[Path] = None):
        self.root = root
        if db_path is None:
            db_path = root / "00_SYSTEM" / "engines" / "event_horizon" / "event_horizon.db"
        self.state = StateDB(db_path)
        self.genesis = Genesis(root)
        self.oracle = Oracle(root, self.state)
        self.promethean = Promethean(root, self.state)
        self.elysium = Elysium(root)

    def run(self, zone: str, dry_run: bool = True) -> dict:
        """Execute the full 4-subsystem MVP pipeline on a zone.
        
        Returns a summary dict with plan, metrics, and quality report.
        """
        mode = "DRY-RUN" if dry_run else "LIVE"
        log.info("=" * 60)
        log.info("EVENT HORIZON v%s -- %s", __version__, mode)
        log.info("Zone: %s", zone)
        log.info("=" * 60)

        # Start run in state DB
        with self.state:
            run_id = self.state.start_run(zone, dry_run)

            # -- GENESIS: Scan --
            log.info("[GENESIS] Scanning...")
            manifests = self.genesis.scan(zone)
            self.state.save_manifests(run_id, manifests)
            log.info("[GENESIS] %d files profiled", len(manifests))

            # -- ORACLE: Decide --
            log.info("[ORACLE] Routing decisions...")
            plan = self.oracle.decide(manifests)
            self.state.save_decisions(run_id, plan.decisions)
            log.info("[ORACLE] %d routable, %d skipped", plan.routable, len(plan.skipped))

            # -- ELYSIUM PRE-CHECK: Validate plan --
            log.info("[ELYSIUM] Pre-flight validation...")
            pre_report = self.elysium.validate(plan, dry_run=True)
            log.info("[ELYSIUM] Pre-check: %s", "PASSED" if pre_report.passed else "ISSUES")

            # -- PROMETHEAN: Execute --
            log.info("[PROMETHEAN] Executing...")
            metrics = self.promethean.execute(plan, dry_run=dry_run, run_id=run_id)
            log.info("[PROMETHEAN] %d ok, %d err", metrics.success_count, metrics.error_count)

            # -- ELYSIUM POST-CHECK: Validate results --
            log.info("[ELYSIUM] Post-flight validation...")
            post_report = self.elysium.validate(plan, metrics, dry_run=dry_run)
            self.state.save_quality(run_id, post_report)
            log.info("[ELYSIUM] Post-check: %s", "PASSED" if post_report.passed else "FAILED")

            # Finalize run
            self.state.finish_run(run_id, metrics.success_count, metrics.error_count)

        # Build summary
        summary = {
            "engine": f"{__codename__} v{__version__}",
            "zone": zone,
            "mode": mode,
            "run_id": run_id,
            "timestamp": datetime.now().isoformat(),
            "scan": {
                "total_files": len(manifests),
            },
            "routing": {
                "routable": plan.routable,
                "skipped": len(plan.skipped),
                "stats": plan.stats,
            },
            "execution": {
                "success": metrics.success_count,
                "errors": metrics.error_count,
                "total": metrics.total_attempted,
            },
            "quality": {
                "passed": post_report.passed,
                "score": post_report.overall_score,
                "gates_passed": post_report.gates_passed,
                "gates_total": post_report.gates_total,
                "results": [
                    {"gate": r.gate.value, "passed": r.passed, "score": r.score, "details": r.details}
                    for r in post_report.results
                ],
            },
        }

        # Print summary
        self._print_summary(summary)
        return summary

    def census(self) -> dict[str, int]:
        """Quick file census across all zones."""
        return self.genesis.quick_census()

    def _print_summary(self, summary: dict):
        """Pretty-print the run summary."""
        s = summary
        q = s["quality"]
        print()
        print(f"+{'='*58}+")
        print(f"|  EVENT HORIZON -- Run Summary{' '*28}|")
        print(f"+{'='*58}+")
        print(f"|  Zone:    {s['zone']:<47}|")
        print(f"|  Mode:    {s['mode']:<47}|")
        print(f"|  Scanned: {s['scan']['total_files']:<47}|")
        print(f"|  Routed:  {s['routing']['routable']:<47}|")
        print(f"|  Moved:   {s['execution']['success']:<47}|")
        print(f"|  Errors:  {s['execution']['errors']:<47}|")
        print(f"+{'='*58}+")
        icon = "PASS" if q["passed"] else "FAIL"
        print(f"||  Quality: [{icon}] {q['gates_passed']}/{q['gates_total']} gates -- score {q['score']:.2f}{' '*14}||")
        for r in q["results"]:
            gi = "OK" if r["passed"] else "XX"
            name = r["gate"][:20].ljust(20)
            print(f"||    [{gi}] {name} {r['score']:.2f}  {r['details'][:25]:<25}||")
        print(f"+{'='*58}+")
        print()


# ---------------------------------------------------------------------------
# CLI entry point
# ---------------------------------------------------------------------------
def main():
    parser = argparse.ArgumentParser(
        prog="event_horizon",
        description="EVENT HORIZON Δ∞ — Autonomous filesystem intelligence engine",
    )
    parser.add_argument(
        "--zone", type=str, default="ROOT",
        help="Zone to process: ROOT, 06_DATA, 04_ANALYSIS, etc.",
    )
    parser.add_argument(
        "--dry-run", action="store_true", default=True,
        help="Preview routing decisions without moving files (default)",
    )
    parser.add_argument(
        "--execute", action="store_true",
        help="Actually move files (overrides --dry-run)",
    )
    parser.add_argument(
        "--census", action="store_true",
        help="Quick file count per zone (no routing)",
    )
    parser.add_argument(
        "--json", action="store_true",
        help="Output results as JSON",
    )
    parser.add_argument(
        "--root", type=str, default=None,
        help="Repository root (default: auto-detect)",
    )

    args = parser.parse_args()

    # Configure logging
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(name)s] %(message)s",
        datefmt="%H:%M:%S",
    )

    root = Path(args.root) if args.root else REPO_ROOT
    engine = Engine(root)

    if args.census:
        census = engine.census()
        if args.json:
            print(json.dumps(census, indent=2))
        else:
            print("\nEVENT HORIZON -- File Census")
            print("-" * 40)
            total = 0
            for zone, count in sorted(census.items()):
                total += max(count, 0)
                indicator = "[!]" if count > 10000 else "[~]" if count > 1000 else "[ ]"
                print(f"  {indicator} {zone:<25} {count:>8,}")
            print("-" * 40)
            print(f"  {'TOTAL':<25} {total:>8,}")
        return

    dry_run = not args.execute
    summary = engine.run(args.zone, dry_run=dry_run)

    if args.json:
        print(json.dumps(summary, indent=2, default=str))


if __name__ == "__main__":
    main()
