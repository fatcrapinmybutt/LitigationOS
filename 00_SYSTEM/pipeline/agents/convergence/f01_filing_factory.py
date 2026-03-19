"""
DELTA9 — F01 Filing Factory
Convergence Tier · MAX LEVEL 9999++

Assembles court packets from scored legal actions.
Runs AFTER both lanes complete.
"""
import json
from pathlib import Path
from typing import Any

from ..agent_base import Agent9999
from ..agent_models import (
    SkipItemError, FatalAgentError, MASTER_INDEX_DB,
    LANE_A_SIGNALS, LANE_B_SIGNALS, LANE_C_SIGNALS,
)
from ..agent_models import CHECKPOINT_DIR


class FilingFactory(Agent9999):
    """Assembles court packets from scored legal actions."""

    def __init__(self):
        super().__init__(agent_id="F01-FILING")
        self._filings: list = []

    # ------------------------------------------------------------------
    # Abstract implementations
    # ------------------------------------------------------------------
    def _validate_preconditions(self) -> None:
        cursor = self._db_execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name='action_scores'"
        )
        if not cursor.fetchone():
            raise FatalAgentError("action_scores table missing — run Lane 2 first")
        row = self._db_execute("SELECT COUNT(*) FROM action_scores WHERE composite_score > 0").fetchone()
        if row[0] == 0:
            raise FatalAgentError("action_scores has no scored entries — cannot build filings")

    def _get_work_items(self) -> list:
        cursor = self._db_execute(
            "SELECT * FROM action_scores WHERE composite_score > 50 "
            "ORDER BY composite_score DESC"
        )
        return cursor.fetchall()

    def _process_item(self, action: Any) -> None:
        # action_scores columns: id(0), action_id(1), lane(2), evidence_score(3),
        # authority_score(4), vulnerability_score(5), readiness_score(6),
        # composite_score(7), gap_count(8), damages_json(9), updated_by(10)
        action_id = action[1] if not isinstance(action, dict) else action.get("action_id", action.get("id"))
        composite = action[7] if not isinstance(action, dict) else action.get("composite_score", 0)
        if composite is None:
            composite = 0.0
        composite = float(composite)

        # 1. Gather supporting atoms based on lane
        lane = action_id[0] if isinstance(action_id, str) else "A"
        lane_map = {"A": "%A%", "B": "%B%", "C": "%C%"}
        lane_pattern = lane_map.get(lane, "%")
        atoms = self._db_execute(
            "SELECT * FROM atoms WHERE meek_lane LIKE ?", (lane_pattern,)
        ).fetchall()

        # 2. Gather citations
        citations = self._db_execute(
            "SELECT * FROM atoms WHERE atom_type = 'citation_validation' AND meek_lane LIKE ?",
            (lane_pattern,),
        ).fetchall()

        # 3. Build filing structure
        filing = {
            "action_id": action_id,
            "composite_score": composite,
            "motion": {
                "evidence_count": len(atoms),
                "citation_count": len(citations),
            },
            "brief": {
                "supporting_atoms": len(atoms),
                "authorities_cited": len(citations),
            },
            "exhibits": [
                {"atom_id": a["id"] if isinstance(a, dict) else a[0], "type": "evidence"}
                for a in atoms[:50]  # cap exhibit list
            ],
            "proposed_order": {
                "relief_requested": True,
                "based_on_actions": action_id,
            },
            "exhibit_count": min(len(atoms), 50),
            "readiness_score": min(composite / 100.0, 1.0),
        }

        # 4. Write filing manifest
        CHECKPOINT_DIR.mkdir(parents=True, exist_ok=True)
        manifest_path = CHECKPOINT_DIR / f"filing_{action_id}.json"
        manifest_path.write_text(json.dumps(filing, indent=2))
        self._log("FILING", f"action={action_id} evidence={len(atoms)} cites={len(citations)} exhibits={filing['exhibit_count']}")
        self._filings.append(filing)

    def _finalize(self) -> None:
        total = len(self._filings)
        if total == 0:
            self._log("DONE", "No filings generated (no actions above threshold)")
            return
        avg_readiness = sum(f["readiness_score"] for f in self._filings) / total
        self._log("DONE", f"{total} filings generated | avg readiness={avg_readiness:.2f}")
