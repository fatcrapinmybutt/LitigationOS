"""
DELTA9 — F04 MSC Architect
Convergence Tier · MAX LEVEL 9999++

Evaluates Michigan Supreme Court filing paths for viability.
Runs AFTER both lanes complete.
"""
import json
from typing import Any

from ..agent_base import Agent9999
from ..agent_models import (
    SkipItemError, FatalAgentError, MASTER_INDEX_DB,
    LANE_A_SIGNALS, LANE_B_SIGNALS, LANE_C_SIGNALS,
)
from ..agent_models import CHECKPOINT_DIR

# MSC filing paths with MCR references
_MSC_PATHS = [
    "leave_7305",       # MCR 7.305 — Application for Leave to Appeal
    "bypass_7305B2",    # MCR 7.305(B)(2) — Bypass COA
    "writ_7306",        # MCR 7.306 — Original Proceedings (Writs)
    "certified_7308",   # MCR 7.308 — Certified Questions
]

# Criteria keywords per path
_PATH_CRITERIA = {
    "leave_7305": {
        "signals": {"appeal", "error", "abuse of discretion", "clearly erroneous"},
        "min_evidence": 5,
    },
    "bypass_7305B2": {
        "signals": {"significant public interest", "constitutional", "statewide impact",
                     "urgency", "systemic"},
        "min_evidence": 10,
    },
    "writ_7306": {
        "signals": {"extraordinary", "mandamus", "superintending control",
                     "no adequate remedy", "habeas"},
        "min_evidence": 8,
    },
    "certified_7308": {
        "signals": {"federal court", "certified question", "unsettled law",
                     "no controlling precedent"},
        "min_evidence": 3,
    },
}


class MscArchitect(Agent9999):
    """Evaluates Michigan Supreme Court filing paths."""

    def __init__(self):
        super().__init__(agent_id="F04-MSC")
        self._viability: dict[str, dict] = {}

    # ------------------------------------------------------------------
    # Abstract implementations
    # ------------------------------------------------------------------
    def _validate_preconditions(self) -> None:
        cursor = self._db_execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name='action_scores'"
        )
        if not cursor.fetchone():
            raise FatalAgentError("action_scores table missing — run Lane 2 first")
        # Check Lane C evidence exists
        atoms_exists = self._db_execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name='atoms'"
        ).fetchone()
        if not atoms_exists:
            raise FatalAgentError("atoms table missing — cannot evaluate MSC paths")

    def _get_work_items(self) -> list:
        return list(_MSC_PATHS)

    def _process_item(self, path_type: Any) -> None:
        criteria = _PATH_CRITERIA.get(path_type)
        if not criteria:
            raise SkipItemError(f"Unknown MSC path: {path_type}")

        # 1. Gather evidence strength across all lanes
        lane_scores = {}
        for lane_name, signals in [("A", LANE_A_SIGNALS), ("B", LANE_B_SIGNALS), ("C", LANE_C_SIGNALS)]:
            count = 0
            for sig in signals:
                row = self._db_execute(
                    "SELECT COUNT(*) FROM atoms WHERE LOWER(content) LIKE ?",
                    (f"%{sig}%",)
                ).fetchone()
                count += row[0] if row else 0
            lane_scores[lane_name] = count

        total_evidence = sum(lane_scores.values())

        # 2. Score viability
        viability = 0.0

        # Evidence volume score (0-40 points)
        min_ev = criteria["min_evidence"]
        evidence_score = min(total_evidence / max(min_ev * 3, 1), 1.0) * 40

        # Signal match score (0-40 points)
        signal_hits = 0
        for sig in criteria["signals"]:
            row = self._db_execute(
                "SELECT COUNT(*) FROM atoms WHERE LOWER(content) LIKE ?",
                (f"%{sig}%",)
            ).fetchone()
            if row and row[0] > 0:
                signal_hits += 1
        signal_score = (signal_hits / max(len(criteria["signals"]), 1)) * 40

        # Lane C strength bonus (0-20 points) — MSC paths benefit from judicial misconduct evidence
        lane_c_bonus = min(lane_scores.get("C", 0) / 10, 1.0) * 20

        viability = evidence_score + signal_score + lane_c_bonus

        # 3. Path-specific checks
        blockers = []
        if path_type == "bypass_7305B2":
            if signal_hits < 2:
                blockers.append("Insufficient 'significant public interest' evidence for bypass")
        elif path_type == "writ_7306":
            if signal_hits < 1:
                blockers.append("No extraordinary circumstances documented")
        if total_evidence < min_ev:
            blockers.append(f"Below minimum evidence threshold ({total_evidence}/{min_ev})")

        report = {
            "path_type": path_type,
            "viability_score": round(viability, 2),
            "evidence_score": round(evidence_score, 2),
            "signal_score": round(signal_score, 2),
            "lane_c_bonus": round(lane_c_bonus, 2),
            "total_evidence": total_evidence,
            "signal_hits": signal_hits,
            "lane_scores": lane_scores,
            "blockers": blockers,
            "viable": viability > 50 and len(blockers) == 0,
        }
        self._viability[path_type] = report

        # Write to checkpoint
        CHECKPOINT_DIR.mkdir(parents=True, exist_ok=True)
        rpt_path = CHECKPOINT_DIR / f"msc_viability_{path_type}.json"
        rpt_path.write_text(json.dumps(report, indent=2))
        self._log("MSC", f"{path_type}: viability={viability:.1f} blockers={len(blockers)}")

    def _finalize(self) -> None:
        viable = [p for p, r in self._viability.items() if r["viable"]]
        blocked = [p for p, r in self._viability.items() if not r["viable"]]
        self._log("DONE", f"MSC paths: {len(viable)} viable, {len(blocked)} blocked")
        if viable:
            self._log("VIABLE", f"Recommended: {', '.join(viable)}")
        if blocked:
            self._log("BLOCKED", f"Not viable: {', '.join(blocked)}")
