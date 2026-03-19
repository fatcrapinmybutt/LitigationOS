"""
DELTA9 — F02 Brain Feeder
Convergence Tier · MAX LEVEL 9999++

Feeds atoms into the 50 LEXOS brain nuclei concept.
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

# Brain mapping ranges by atom type
_BRAIN_MAP = {
    "citation":  list(range(1, 9)),    # brains 1-8 (legal authority)
    "person":    list(range(9, 18)),    # brains 9-17 (persons)
    "fact":      list(range(18, 26)),   # brains 18-25 (issues) — custody-related facts
    "event":     list(range(26, 31)),   # brains 26-30 (procedural)
}


class BrainFeeder(Agent9999):
    """Feeds atoms into the 50 LEXOS brain nuclei."""

    def __init__(self):
        super().__init__(agent_id="F02-BRAINS")
        self._brain_counts: dict[int, int] = {}
        self._total_fed = 0

    # ------------------------------------------------------------------
    # Abstract implementations
    # ------------------------------------------------------------------
    def _validate_preconditions(self) -> None:
        cursor = self._db_execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name='atoms'"
        )
        if not cursor.fetchone():
            raise FatalAgentError("atoms table missing — run Lane 2 first")

    def _get_work_items(self) -> list:
        cursor = self._db_execute(
            "SELECT * FROM atoms WHERE confidence > 0.5 ORDER BY confidence DESC"
        )
        return cursor.fetchall()

    def _process_item(self, atom: Any) -> None:
        atom_type = atom["atom_type"]
        confidence = atom["confidence"]
        content = atom["content"]

        # 1. Determine target brains
        brains = self._resolve_brains(atom_type, content)
        if not brains:
            raise SkipItemError(f"No brain mapping for atom_type={atom_type}")

        # 2. Score and distribute
        for brain_id in brains:
            relevance = self._score_relevance(atom_type, brain_id, content)
            feed_score = relevance * confidence
            if feed_score > 0.1:
                self._brain_counts[brain_id] = self._brain_counts.get(brain_id, 0) + 1
                self._total_fed += 1

    def _finalize(self) -> None:
        CHECKPOINT_DIR.mkdir(parents=True, exist_ok=True)
        report = {
            "total_atoms_fed": self._total_fed,
            "brains_populated": len(self._brain_counts),
            "counts_per_brain": {str(k): v for k, v in sorted(self._brain_counts.items())},
        }
        report_path = CHECKPOINT_DIR / "brain_feed_report.json"
        report_path.write_text(json.dumps(report, indent=2))
        self._log("DONE", f"{self._total_fed} atoms fed across {len(self._brain_counts)} brains")

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------
    @staticmethod
    def _resolve_brains(atom_type: str, content: str) -> list[int]:
        """Determine which brain(s) an atom maps to."""
        atom_type_lower = atom_type.lower()

        # Direct type match
        if atom_type_lower in _BRAIN_MAP:
            # For facts, only route custody-related to brains 18-25
            if atom_type_lower == "fact":
                content_lower = (content or "").lower()
                if any(kw in content_lower for kw in ("custody", "parenting", "child", "visitation")):
                    return _BRAIN_MAP["fact"]
                return []
            return _BRAIN_MAP[atom_type_lower]

        # Fallback: check content for signals
        content_lower = (content or "").lower()
        results = []
        if any(sig in content_lower for sig in ("mcl", "mcr", "statute", "rule")):
            results.extend(_BRAIN_MAP["citation"])
        if any(sig in content_lower for sig in ("judge", "plaintiff", "defendant", "attorney")):
            results.extend(_BRAIN_MAP["person"])
        return results

    @staticmethod
    def _score_relevance(atom_type: str, brain_id: int, content: str) -> float:
        """Score relevance of an atom to a specific brain (0.0-1.0)."""
        # Primary match gets full relevance
        primary = _BRAIN_MAP.get(atom_type.lower(), [])
        if brain_id in primary:
            return 1.0
        return 0.3  # secondary/inferred mapping
