"""
DELTA9 — F06 Convergence Certifier
Convergence Tier · MAX LEVEL 9999++

Computes FINAL convergence scores and issues pipeline verdict.
Runs AFTER both lanes complete (last agent in the fleet).
"""
import json
from typing import Any

from ..agent_base import Agent9999
from ..agent_models import (
    SkipItemError, FatalAgentError, MASTER_INDEX_DB,
    LANE_A_SIGNALS, LANE_B_SIGNALS, LANE_C_SIGNALS,
)
from ..agent_models import CHECKPOINT_DIR

# Metric weights for overall score
_WEIGHTS = {
    "coverage": 0.30,
    "gaps": 0.15,
    "lane_balance": 0.15,
    "filing_readiness": 0.25,
    "overall": 0.15,
}


class ConvergenceCertifier(Agent9999):
    """Computes FINAL convergence scores and issues verdict."""

    def __init__(self):
        super().__init__(agent_id="F06-CERTIFY")
        self._metrics: dict[str, float] = {}
        self._blockers: list[str] = []

    # ------------------------------------------------------------------
    # Abstract implementations
    # ------------------------------------------------------------------
    def _validate_preconditions(self) -> None:
        # Certifier runs last — minimal hard requirements
        if not self.db_path.exists():
            raise FatalAgentError(f"master_index.db not found at {self.db_path}")

    def _get_work_items(self) -> list:
        return ["coverage", "gaps", "lane_balance", "filing_readiness", "overall"]

    def _process_item(self, metric: Any) -> None:
        handler = getattr(self, f"_compute_{metric}", None)
        if handler:
            score = handler()
            self._metrics[metric] = score
            self._log("METRIC", f"{metric} = {score:.2f}")
        else:
            raise SkipItemError(f"No handler for metric: {metric}")

    def _finalize(self) -> None:
        CHECKPOINT_DIR.mkdir(parents=True, exist_ok=True)

        overall = self._metrics.get("overall", 0.0)
        verdict = "READY-FOR-TESTING" if overall > 60 else "BLOCKED-BY"

        report = {
            "metrics": {k: round(v, 2) for k, v in self._metrics.items()},
            "weights": _WEIGHTS,
            "overall_score": round(overall, 2),
            "verdict": verdict,
            "blockers": self._blockers if verdict != "READY-FOR-TESTING" else [],
        }

        report_path = CHECKPOINT_DIR / "DELTA9_CONVERGENCE_REPORT.json"
        report_path.write_text(json.dumps(report, indent=2))

        # Prominent verdict output
        self._log("=" * 50, "")
        self._log("VERDICT", f"{'★ ' * 5} {verdict} {'★ ' * 5}")
        self._log("SCORE", f"Overall convergence: {overall:.2f} / 100")
        if self._blockers:
            for b in self._blockers:
                self._log("BLOCKER", b)
        self._log("=" * 50, "")

    # ------------------------------------------------------------------
    # Metric computations
    # ------------------------------------------------------------------
    def _compute_coverage(self) -> float:
        """(files_processed / total_canonical_files) × 100."""
        if not self._table_exists("files"):
            self._blockers.append("files table missing — no coverage data")
            return 0.0
        total_row = self._db_execute("SELECT COUNT(*) FROM files").fetchone()
        total = total_row[0] if total_row else 0
        if total == 0:
            self._blockers.append("No files indexed")
            return 0.0
        try:
            canonical_row = self._db_execute(
                "SELECT COUNT(*) FROM files WHERE is_canonical = 1"
            ).fetchone()
            canonical = canonical_row[0] if canonical_row else 0
        except Exception:
            canonical = total  # no canonical column — treat all as canonical
        # processed = atoms with source_file_id references
        if self._table_exists("atoms"):
            processed_row = self._db_execute(
                "SELECT COUNT(DISTINCT source_file_id) FROM atoms WHERE source_file_id IS NOT NULL"
            ).fetchone()
            processed = processed_row[0] if processed_row else 0
        else:
            processed = 0
            self._blockers.append("atoms table missing — coverage unknown")
        denom = max(canonical, 1)
        return min((processed / denom) * 100, 100.0)

    def _compute_gaps(self) -> float:
        """Score based on gap_ticket atom count (fewer gaps = higher score)."""
        if not self._table_exists("atoms"):
            self._blockers.append("atoms table missing — cannot assess gaps")
            return 0.0
        row = self._db_execute(
            "SELECT COUNT(*) FROM atoms WHERE atom_type = 'gap_ticket'"
        ).fetchone()
        gap_count = row[0] if row else 0
        # 0 gaps = 100, 50+ gaps = 0
        score = max(100 - (gap_count * 2), 0.0)
        if gap_count > 20:
            self._blockers.append(f"{gap_count} evidence gaps detected")
        return score

    def _compute_lane_balance(self) -> float:
        """Compare Lane A vs B vs C evidence counts."""
        if not self._table_exists("atoms"):
            self._blockers.append("atoms table missing — cannot assess lane balance")
            return 0.0
        counts = {}
        for lane_name, signals in [("A", LANE_A_SIGNALS), ("B", LANE_B_SIGNALS), ("C", LANE_C_SIGNALS)]:
            total = 0
            for sig in list(signals)[:5]:  # sample top 5 signals for speed
                row = self._db_execute(
                    "SELECT COUNT(*) FROM atoms WHERE LOWER(content) LIKE ?",
                    (f"%{sig}%",)
                ).fetchone()
                total += row[0] if row else 0
            counts[lane_name] = total

        values = list(counts.values())
        if max(values) == 0:
            self._blockers.append("No lane evidence found at all")
            return 0.0
        # Balance = 1 - coefficient of variation (capped 0-100)
        mean = sum(values) / len(values)
        if mean == 0:
            return 0.0
        variance = sum((v - mean) ** 2 for v in values) / len(values)
        std = variance ** 0.5
        cv = std / mean
        score = max((1.0 - cv) * 100, 0.0)
        return min(score, 100.0)

    def _compute_filing_readiness(self) -> float:
        """Average composite_score for top 10 actions."""
        if not self._table_exists("action_scores"):
            self._blockers.append("action_scores table missing")
            return 0.0
        rows = self._db_execute(
            "SELECT composite_score FROM action_scores ORDER BY composite_score DESC LIMIT 10"
        ).fetchall()
        if not rows:
            self._blockers.append("No action scores computed")
            return 0.0
        avg = sum(r[0] for r in rows) / len(rows)
        return min(avg, 100.0)

    def _compute_overall(self) -> float:
        """Weighted average of all other metrics."""
        weighted_sum = 0.0
        total_weight = 0.0
        for metric, weight in _WEIGHTS.items():
            if metric == "overall":
                continue
            score = self._metrics.get(metric, 0.0)
            weighted_sum += score * weight
            total_weight += weight
        if total_weight == 0:
            return 0.0
        return weighted_sum / total_weight

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------
    def _table_exists(self, name: str) -> bool:
        row = self._db_execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name=?", (name,)
        ).fetchone()
        return row is not None
