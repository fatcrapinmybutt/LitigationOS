"""
EVENT HORIZON Δ∞ — PROMETHEAN: The Fire-Bringer (Execution Engine)
===================================================================
Actually moves files. Every operation is checkpointed, rollback-safe,
and streams progress to the state DB.
"""
from __future__ import annotations

import logging
from pathlib import Path
from typing import Optional

from .models import (
    MoveMetrics,
    MoveRecord,
    REPO_ROOT,
    RoutingDecision,
    RoutingPlan,
)
from .monad import safe_move, rollback_move
from .state import StateDB

log = logging.getLogger("event_horizon.promethean")


class Promethean:
    """🔥 PROMETHEAN — Execution engine.
    
    Executes a RoutingPlan by moving files according to Oracle decisions.
    Supports dry-run mode, checkpointing every N files, and full rollback.
    """

    CHECKPOINT_INTERVAL = 500

    def __init__(
        self,
        root: Path = REPO_ROOT,
        state_db: Optional[StateDB] = None,
        checkpoint_interval: int = 500,
    ):
        self.root = root
        self.state_db = state_db
        self.CHECKPOINT_INTERVAL = checkpoint_interval

    def execute(
        self,
        plan: RoutingPlan,
        dry_run: bool = True,
        run_id: Optional[str] = None,
    ) -> MoveMetrics:
        """Execute all routing decisions in the plan.
        
        Pre-checks (live mode only):
        - Disk space >= 1 GB before starting
        - Disk space re-checked every checkpoint interval
        """
        metrics = MoveMetrics()
        metrics.total_attempted = plan.routable

        mode = "DRY-RUN" if dry_run else "LIVE"
        log.info(f"PROMETHEAN [{mode}]: Executing {plan.routable} routing decisions")

        # Pre-flight disk check for live execution
        if not dry_run:
            import shutil as _sh
            try:
                usage = _sh.disk_usage(str(self.root))
                free_gb = usage.free / (1024**3)
                if free_gb < 1.0:
                    log.error("PROMETHEAN: ABORTING -- only %.1f GB free (need >= 1 GB)", free_gb)
                    metrics.error_count = plan.routable
                    return metrics
                log.info("PROMETHEAN: %.1f GB free disk space -- OK", free_gb)
            except Exception:
                pass  # Can't check, proceed with caution

            self._ensure_destinations(plan.decisions)

        for i, decision in enumerate(plan.decisions):
            rec = self._execute_one(decision, dry_run)

            if rec.success:
                metrics.moves.append(rec)
                metrics.success_count += 1
            else:
                metrics.errors.append(rec)
                metrics.error_count += 1

            # Save to state DB
            if self.state_db and run_id:
                self.state_db.save_move(run_id, rec)

            # Checkpoint with disk space re-check
            if (i + 1) % self.CHECKPOINT_INTERVAL == 0:
                log.info(f"PROMETHEAN: Checkpoint at {i+1}/{plan.routable} "
                         f"({metrics.success_count} ok, {metrics.error_count} err)")
                # Re-check disk space at each checkpoint (live only)
                if not dry_run:
                    try:
                        usage = _sh.disk_usage(str(self.root))
                        free_gb = usage.free / (1024**3)
                        if free_gb < 0.5:
                            log.error("PROMETHEAN: HALTING -- disk critically low (%.1f GB)", free_gb)
                            break
                    except Exception:
                        pass

        log.info(f"PROMETHEAN [{mode}]: Complete — "
                 f"{metrics.success_count} moved, {metrics.error_count} errors")
        return metrics

    def _execute_one(self, decision: RoutingDecision, dry_run: bool) -> MoveRecord:
        """Execute a single routing decision."""
        rec = safe_move(decision.source, decision.destination, dry_run=dry_run)
        if not rec.success and rec.error:
            log.warning(f"PROMETHEAN: Failed {decision.source.name}: {rec.error}")
        return rec

    def _ensure_destinations(self, decisions: list[RoutingDecision]):
        """Pre-create all target directories before moving files."""
        dirs_needed: set[Path] = set()
        for d in decisions:
            dirs_needed.add(d.destination.parent)

        for d in sorted(dirs_needed):
            d.mkdir(parents=True, exist_ok=True)

    def rollback(self, metrics: MoveMetrics, dry_run: bool = True) -> int:
        """Rollback all successful moves. Returns count of rollbacks."""
        mode = "DRY-RUN" if dry_run else "LIVE"
        log.info(f"PROMETHEAN ROLLBACK [{mode}]: Rolling back {metrics.success_count} moves")

        rolled_back = 0
        for rec in reversed(metrics.moves):
            if rollback_move(rec, dry_run=dry_run):
                rolled_back += 1
            else:
                log.warning(f"PROMETHEAN ROLLBACK: Failed to rollback {rec.destination}")

        log.info(f"PROMETHEAN ROLLBACK [{mode}]: {rolled_back}/{metrics.success_count} rolled back")
        return rolled_back
