"""
EVENT HORIZON Δ∞ — ELYSIUM: The Quality Paradise
==================================================
7 quality gates that every routing run must pass through.
Only perfection survives ELYSIUM.

Gates:
  1. ZERO_LOSS       — No files disappeared (source gone + dest missing)
  2. ACCURACY        — Routing tier distribution within expected bounds
  3. DISTRIBUTION    — No single folder accumulated >40% of routed files
  4. EVIDENCE_INTEGRITY — Evidence files landed in 01_EVIDENCE/*
  5. PROTECTED_ZONES — Protected files/dirs were NOT touched
  6. CANONICAL_COMPLIANCE — All destinations are within canonical folders
  7. DEDUP           — No duplicate files created by routing
"""
from __future__ import annotations

import logging
from collections import Counter
from pathlib import Path
from typing import Optional

from .models import (
    CANONICAL_FOLDERS,
    PROTECTED_DIRS,
    ALLOWED_ROOT_FILES,
    REPO_ROOT,
    Confidence,
    MoveMetrics,
    QualityGate,
    QualityReport,
    QualityResult,
    RoutingDecision,
    RoutingPlan,
    RoutingTier,
)

log = logging.getLogger("event_horizon.elysium")


class Elysium:
    """🏛️ ELYSIUM — Quality validation paradise.
    
    Runs 7 quality gates on routing plans and move metrics.
    Returns a QualityReport with per-gate scores and an overall pass/fail.
    """

    def __init__(self, root: Path = REPO_ROOT):
        self.root = root

    def validate(
        self,
        plan: RoutingPlan,
        metrics: Optional[MoveMetrics] = None,
        dry_run: bool = True,
    ) -> QualityReport:
        """Run all 7 quality gates and produce a report."""
        report = QualityReport()
        report.results = [
            self._gate_zero_loss(plan, metrics, dry_run),
            self._gate_accuracy(plan),
            self._gate_distribution(plan),
            self._gate_evidence_integrity(plan),
            self._gate_protected_zones(plan),
            self._gate_canonical_compliance(plan),
            self._gate_dedup(plan),
        ]
        report.compute()
        
        status = "PASSED" if report.passed else "FAILED"
        log.info(f"ELYSIUM: {status} -- overall score: {report.overall_score:.2f}")
        for r in report.results:
            icon = "PASS" if r.passed else "FAIL"
            log.info(f"  [{icon}] {r.gate.value}: {r.score:.2f} -- {r.details}")
        
        return report

    # -- Gate 1: Zero Loss --
    def _gate_zero_loss(
        self,
        plan: RoutingPlan,
        metrics: Optional[MoveMetrics],
        dry_run: bool,
    ) -> QualityResult:
        """No files disappeared during routing."""
        if dry_run or metrics is None:
            return QualityResult(
                gate=QualityGate.ZERO_LOSS,
                passed=True,
                score=1.0,
                details="Dry run — no files moved, zero loss by definition",
            )

        # Check that all moved files have their destination existing
        violations = []
        for rec in metrics.moves:
            if rec.success and not rec.destination.exists():
                violations.append(f"LOST: {rec.source} → {rec.destination}")

        # Check error files
        for rec in metrics.errors:
            if not rec.source.exists() and (not rec.destination.exists()):
                violations.append(f"LOST (error): {rec.source}")

        score = 1.0 - (len(violations) / max(metrics.total_attempted, 1))
        return QualityResult(
            gate=QualityGate.ZERO_LOSS,
            passed=len(violations) == 0,
            score=max(score, 0.0),
            details=f"{len(violations)} files lost out of {metrics.total_attempted}",
            violations=violations[:20],
        )

    # -- Gate 2: Accuracy --
    def _gate_accuracy(self, plan: RoutingPlan) -> QualityResult:
        """Routing tier distribution should be reasonable."""
        if not plan.decisions:
            return QualityResult(
                gate=QualityGate.ACCURACY,
                passed=True,
                score=1.0,
                details="No decisions to evaluate",
            )

        tiers = Counter(d.tier for d in plan.decisions)
        total = len(plan.decisions)
        violations = []

        # Fallback tier should be <30% of total (most files should match a real tier)
        fallback_pct = tiers.get(RoutingTier.T7_FALLBACK, 0) / total
        if fallback_pct > 0.30:
            violations.append(
                f"Fallback tier = {fallback_pct:.0%} (threshold: 30%)"
            )

        # GREEN+YELLOW confidence should be >50%
        confidence_counts = Counter(d.confidence for d in plan.decisions)
        high_conf = (confidence_counts.get(Confidence.GREEN, 0) +
                     confidence_counts.get(Confidence.YELLOW, 0))
        high_pct = high_conf / total
        if high_pct < 0.50:
            violations.append(
                f"High-confidence decisions = {high_pct:.0%} (threshold: 50%)"
            )

        score = 1.0 - (0.3 * (fallback_pct > 0.30)) - (0.3 * (high_pct < 0.50))
        return QualityResult(
            gate=QualityGate.ACCURACY,
            passed=len(violations) == 0,
            score=max(score, 0.0),
            details=f"Fallback={fallback_pct:.0%}, HighConf={high_pct:.0%}",
            violations=violations,
        )

    # -- Gate 3: Distribution --
    def _gate_distribution(self, plan: RoutingPlan) -> QualityResult:
        """No single destination folder gets >40% of all routed files."""
        if not plan.decisions:
            return QualityResult(
                gate=QualityGate.DISTRIBUTION,
                passed=True,
                score=1.0,
                details="No decisions to evaluate",
            )

        # Extract top-level destination folder
        dest_counts = Counter()
        for d in plan.decisions:
            try:
                rel = d.destination.relative_to(self.root)
                top = rel.parts[0] if rel.parts else "ROOT"
            except ValueError:
                top = "EXTERNAL"
            dest_counts[top] += 1

        total = len(plan.decisions)
        violations = []
        for folder, count in dest_counts.most_common():
            pct = count / total
            if pct > 0.40:
                violations.append(f"{folder} = {pct:.0%} ({count} files) > 40% threshold")

        worst_pct = dest_counts.most_common(1)[0][1] / total if dest_counts else 0
        score = max(1.0 - max(worst_pct - 0.40, 0) * 2.5, 0.0)

        return QualityResult(
            gate=QualityGate.DISTRIBUTION,
            passed=len(violations) == 0,
            score=score,
            details=f"Top dest: {dest_counts.most_common(1)[0] if dest_counts else ('none',0)}",
            violations=violations,
        )

    # -- Gate 4: Evidence Integrity --
    def _gate_evidence_integrity(self, plan: RoutingPlan) -> QualityResult:
        """Evidence-tier files must land in 01_EVIDENCE/*."""
        violations = []
        evidence_count = 0

        for d in plan.decisions:
            if d.tier == RoutingTier.T1_EVIDENCE:
                evidence_count += 1
                try:
                    rel = d.destination.relative_to(self.root)
                    if not str(rel).startswith("01_EVIDENCE"):
                        violations.append(
                            f"Evidence file routed outside 01_EVIDENCE: {d.source.name} → {rel}"
                        )
                except ValueError:
                    violations.append(f"Evidence file outside repo: {d.source.name}")

        score = 1.0 - (len(violations) / max(evidence_count, 1))
        return QualityResult(
            gate=QualityGate.EVIDENCE_INTEGRITY,
            passed=len(violations) == 0,
            score=max(score, 0.0),
            details=f"{evidence_count} evidence files, {len(violations)} misrouted",
            violations=violations[:20],
        )

    # -- Gate 5: Protected Zones --
    def _gate_protected_zones(self, plan: RoutingPlan) -> QualityResult:
        """Protected files/dirs were NOT selected for routing."""
        violations = []

        for d in plan.decisions:
            # Check source isn't in a protected dir
            parts = set(d.source.parts)
            if parts & PROTECTED_DIRS:
                violations.append(f"Protected source: {d.source}")

            # Check source isn't an allowed root file
            if d.source.parent == self.root and d.source.name in ALLOWED_ROOT_FILES:
                violations.append(f"Allowed root file targeted: {d.source.name}")

        return QualityResult(
            gate=QualityGate.PROTECTED_ZONES,
            passed=len(violations) == 0,
            score=1.0 if not violations else 0.0,
            details=f"{len(violations)} protected zone violations",
            violations=violations[:20],
        )

    # -- Gate 6: Canonical Compliance --
    def _gate_canonical_compliance(self, plan: RoutingPlan) -> QualityResult:
        """All destinations must be within canonical folders."""
        violations = []

        for d in plan.decisions:
            try:
                rel = d.destination.relative_to(self.root)
                top = rel.parts[0] if rel.parts else ""
                if top not in CANONICAL_FOLDERS:
                    violations.append(f"Non-canonical dest: {d.destination} (top={top})")
            except ValueError:
                violations.append(f"Destination outside repo: {d.destination}")

        total = len(plan.decisions)
        score = 1.0 - (len(violations) / max(total, 1))
        return QualityResult(
            gate=QualityGate.CANONICAL_COMPLIANCE,
            passed=len(violations) == 0,
            score=max(score, 0.0),
            details=f"{len(violations)}/{total} non-canonical destinations",
            violations=violations[:20],
        )

    # -- Gate 7: Dedup --
    def _gate_dedup(self, plan: RoutingPlan) -> QualityResult:
        """No two files should be routed to the exact same destination."""
        seen: dict[str, list[str]] = {}
        for d in plan.decisions:
            dest_key = str(d.destination)
            if dest_key not in seen:
                seen[dest_key] = []
            seen[dest_key].append(str(d.source))

        violations = []
        for dest, sources in seen.items():
            if len(sources) > 1:
                violations.append(
                    f"Collision: {len(sources)} files → {dest}"
                )

        total = len(plan.decisions)
        score = 1.0 - (len(violations) / max(total, 1))
        return QualityResult(
            gate=QualityGate.DEDUP,
            passed=len(violations) == 0,
            score=max(score, 0.0),
            details=f"{len(violations)} destination collisions",
            violations=violations[:20],
        )
