"""
DELTA9 — L07 Filing Readiness
Tier L · Lane 2 Intelligence · MAX LEVEL 9999++

Scores each of 56 legal actions on 4 dimensions:
  1. Evidence strength   (35%)
  2. Authority backing   (25%)
  3. Adversary vulnerability (20%)
  4. Procedural readiness    (20%)

Flags actions READY TO FILE when composite > 70.
"""
import json
import math
from typing import Any, Dict, List

from ..agent_base import Agent9999
from ..agent_models import (
    SkipItemError, FatalAgentError, MASTER_INDEX_DB,
    LANE_A_SIGNALS, LANE_B_SIGNALS, LANE_C_SIGNALS,
)

from .l01_lane_a_scorer import LANE_A_ACTIONS
from .l02_lane_b_scorer import LANE_B_ACTIONS
from .l03_lane_c_scorer import LANE_C_ACTIONS

# Composite weights
W_EVIDENCE = 0.35
W_AUTHORITY = 0.25
W_VULNERABILITY = 0.20
W_PROCEDURAL = 0.20

# Filing readiness threshold
READY_THRESHOLD = 70.0

# All actions
ALL_ACTIONS: Dict[str, dict] = {}
ALL_ACTIONS.update({k: {**v, "lane": "A"} for k, v in LANE_A_ACTIONS.items()})
ALL_ACTIONS.update({k: {**v, "lane": "B"} for k, v in LANE_B_ACTIONS.items()})
ALL_ACTIONS.update({k: {**v, "lane": "C"} for k, v in LANE_C_ACTIONS.items()})


def _safe_score(value: float) -> float:
    if math.isnan(value) or math.isinf(value):
        return 0.0
    return max(0.0, min(100.0, value))


class FilingReadiness(Agent9999):
    """Score all 56 actions on 4-dimension filing readiness composite."""

    def __init__(self):
        super().__init__(agent_id="L07-READINESS")
        self.parallel_workers = 4   # I/O bound — parallelize file reads
        self.item_timeout = 15      # skip files that take >15s to read
        self.checkpoint_interval = 200

    def _validate_preconditions(self) -> None:
        for tbl in ("atoms", "action_scores"):
            cursor = self._db_execute(
                "SELECT name FROM sqlite_master WHERE type='table' AND name=?", (tbl,)
            )
            if not cursor.fetchone():
                raise FatalAgentError(f"Required table '{tbl}' missing — run prior agents first")

    def _ensure_tables(self) -> None:
        self._db_execute("""
            CREATE TABLE IF NOT EXISTS action_scores (
                action_id   TEXT NOT NULL,
                lane        TEXT NOT NULL,
                evidence_score    REAL DEFAULT 0.0,
                authority_score   REAL DEFAULT 0.0,
                vulnerability_score REAL DEFAULT 0.0,
                readiness_score   REAL DEFAULT 0.0,
                composite_score   REAL DEFAULT 0.0,
                gap_count         INTEGER DEFAULT 0,
                damages_json      TEXT,
                needs_review      INTEGER DEFAULT 0,
                updated_at        TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                PRIMARY KEY (action_id, lane)
            )
        """)
        self.db.commit()

    def _get_work_items(self) -> list:
        return list(ALL_ACTIONS.keys())

    def _process_item(self, action_id: Any) -> None:
        action = ALL_ACTIONS[action_id]
        lane = action["lane"]

        # 1. Evidence strength (from action_scores)
        score_row = self._db_execute(
            "SELECT evidence_score, authority_score FROM action_scores WHERE action_id=? AND lane=?",
            (action_id, lane)
        ).fetchone()

        evidence = float(score_row["evidence_score"]) if score_row else 0.0
        authority = float(score_row["authority_score"]) if score_row else 0.0

        # 2. Adversary vulnerability (contradiction count per adversary)
        vulnerability = self._calc_vulnerability(lane)

        # 3. Procedural readiness (filing requirements check)
        procedural = self._calc_procedural(action_id, lane, action)

        # Composite score
        composite = _safe_score(
            (evidence * W_EVIDENCE +
             authority * W_AUTHORITY +
             vulnerability * W_VULNERABILITY +
             procedural * W_PROCEDURAL) * 100.0 / 100.0
        )

        readiness = composite
        is_ready = composite >= READY_THRESHOLD

        needs_review = 0
        if composite == 0.0 and (evidence > 0 or authority > 0):
            needs_review = 1

        self._db_execute("""
            INSERT OR REPLACE INTO action_scores (action_id, lane, evidence_score, authority_score, vulnerability_score, readiness_score, composite_score, gap_count, updated_by)
            VALUES (?, ?, 0.0, 0.0, ?, ?, ?, 0, ?)
            ON CONFLICT(action_id) DO UPDATE SET
                vulnerability_score = excluded.vulnerability_score,
                readiness_score     = excluded.readiness_score,
                composite_score     = excluded.composite_score,
                updated_by          = excluded.updated_by
        """, (action_id, lane, vulnerability, readiness, composite, self.agent_id))
        self.db.commit()

        if is_ready:
            self._log("READY", f"{action_id} ({action['name']}): composite={composite:.1f} — READY TO FILE")

    def _calc_vulnerability(self, lane: str) -> float:
        """Score adversary vulnerability based on contradiction atoms."""
        contradiction_count = self._db_execute(
            "SELECT COUNT(*) FROM atoms WHERE meek_lane LIKE ? AND "
            "(atom_type='CONTRADICTION' OR content LIKE '%contradict%' OR content LIKE '%inconsist%')",
            (f"%{lane}%",)
        ).fetchone()[0]

        # Scale: 0 contradictions = 0, 10+ = 100
        return _safe_score(min(contradiction_count * 10.0, 100.0))

    def _calc_procedural(self, action_id: str, lane: str, action: dict) -> float:
        """Estimate procedural readiness from available artifacts."""
        checks = 0
        total_checks = 3  # complaint, exhibits, service plan

        # Check for complaint/motion drafts
        draft_count = self._db_execute(
            "SELECT COUNT(*) FROM atoms WHERE meek_lane LIKE ? AND "
            "(atom_type='DRAFT' OR content LIKE '%complaint%' OR content LIKE '%motion%')",
            (f"%{lane}%",)
        ).fetchone()[0]
        if draft_count > 0:
            checks += 1

        # Check for exhibits
        exhibit_count = self._db_execute(
            "SELECT COUNT(*) FROM atoms WHERE meek_lane LIKE ? AND "
            "(atom_type='EXHIBIT' OR content LIKE '%exhibit%')",
            (f"%{lane}%",)
        ).fetchone()[0]
        if exhibit_count > 0:
            checks += 1

        # Check for service plan / proof of service
        service_count = self._db_execute(
            "SELECT COUNT(*) FROM atoms WHERE meek_lane LIKE ? AND "
            "(content LIKE '%service%' OR content LIKE '%summons%')",
            (f"%{lane}%",)
        ).fetchone()[0]
        if service_count > 0:
            checks += 1

        return _safe_score((checks / total_checks) * 100.0)

    def _finalize(self) -> None:
        ready = self._db_execute(
            "SELECT COUNT(*) FROM action_scores WHERE composite_score >= ?",
            (READY_THRESHOLD,)
        ).fetchone()[0]
        total = self._db_execute(
            "SELECT COUNT(*) FROM action_scores"
        ).fetchone()[0]
        self._log("SUMMARY", f"Filing readiness: {ready}/{total} actions READY TO FILE (composite >= {READY_THRESHOLD})")

        # Log top 10
        top10 = self._db_execute(
            "SELECT action_id, lane, composite_score FROM action_scores "
            "ORDER BY composite_score DESC LIMIT 10"
        ).fetchall()
        for r in top10:
            self._log("TOP10", f"{r['action_id']} (Lane {r['lane']}): {float(r.get('composite_score') or 0):.1f}")
