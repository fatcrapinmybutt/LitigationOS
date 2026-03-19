"""
DELTA9 — L09 Lane D Scorer
Tier L · Lane 2 Intelligence · MAX LEVEL 9999++

Scores against Lane D PPO actions (D1–D7).
BONUS: Pulls evidence from Lane A since PPO overlaps custody.
"""
import json
import math
from typing import Any

from ..agent_base import Agent9999
from ..agent_models import (
    SkipItemError, FatalAgentError, MASTER_INDEX_DB,
    LANE_A_SIGNALS, LANE_D_SIGNALS,
)

POSTURE_WEIGHTS = {
    "SWORN_FACT": 5.0,
    "RECORD_FACT": 4.0,
    "EVIDENCE_FACT": 3.0,
    "ALLEGATION": 1.0,
    "INFERENCE": 0.5,
}

# Lane D Actions: D1–D7 — PPO enforcement / protection orders
LANE_D_ACTIONS = {
    "D1": {"name": "Motion to Enforce PPO",              "required": ["active_ppo", "violation_evidence", "police_report_or_affidavit"]},
    "D2": {"name": "Motion for Contempt (PPO Violation)", "required": ["ppo_order_copy", "violation_documentation", "witness_statement"]},
    "D3": {"name": "Motion to Modify PPO",                "required": ["changed_circumstances", "current_ppo_terms", "proposed_modifications"]},
    "D4": {"name": "Motion to Extend PPO",                "required": ["expiration_date", "continuing_threat_evidence", "good_cause_showing"]},
    "D5": {"name": "PPO Violation Criminal Complaint",    "required": ["violation_evidence", "police_report", "ppo_certified_copy"]},
    "D6": {"name": "Motion for Bond Conditions",          "required": ["risk_assessment", "proposed_conditions", "statutory_basis"]},
    "D7": {"name": "Emergency Ex Parte PPO Petition",     "required": ["immediate_danger_affidavit", "specific_threat_evidence", "mcl_600_2950_basis"]},
}


def _safe_score(value: float) -> float:
    if math.isnan(value) or math.isinf(value):
        return 0.0
    return max(0.0, min(100.0, value))


class LaneDScorer(Agent9999):
    """Score evidence against Lane D PPO actions (D1–D7).
    PPO overlap: draws atoms from Lane D and Lane A (custody)."""

    def __init__(self):
        super().__init__(agent_id="L09-LANE-D-SCORE")
        self.parallel_workers = 4   # I/O bound — parallelize file reads
        self.item_timeout = 15      # skip files that take >15s to read
        self.checkpoint_interval = 200

    def _validate_preconditions(self) -> None:
        cursor = self._db_execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name='atoms'"
        )
        if not cursor.fetchone():
            raise FatalAgentError("Required table 'atoms' missing — run Tier 1 first")
        row = self._db_execute(
            "SELECT COUNT(*) FROM atoms WHERE meek_lane LIKE '%D%'"
        ).fetchone()
        if row[0] == 0:
            self._log("WARN", "No Lane-D atoms found — will rely on overlap from Lane A")

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
        return list(LANE_D_ACTIONS.keys())

    def _process_item(self, action_id: Any) -> None:
        action = LANE_D_ACTIONS[action_id]
        needs_review = 0

        # PPO overlap: pull atoms from Lane D direct AND from Lane A (custody)
        lane_d_rows = self._db_execute(
            "SELECT atom_type, posture, content FROM atoms WHERE meek_lane LIKE '%D%'"
        ).fetchall()
        lane_a_rows = self._db_execute(
            "SELECT atom_type, posture, content FROM atoms WHERE meek_lane LIKE '%A%'"
        ).fetchall()

        all_rows = list(lane_d_rows) + list(lane_a_rows)

        if not all_rows:
            self._upsert_score(action_id, 0.0, 0.0, 0.0, 0, needs_review)
            return

        fact_count = 0
        citation_count = 0
        person_count = 0
        weighted_sum = 0.0
        convergence_bonus = 0.0

        for row in all_rows:
            atom_type = (row["atom_type"] or "").upper()
            posture = (row["posture"] or "ALLEGATION").upper()
            weight = POSTURE_WEIGHTS.get(posture, 1.0)

            if atom_type in ("FACT", "FACT_ATOM"):
                fact_count += 1
                weighted_sum += 3.0 * weight
            elif atom_type in ("CITATION", "AUTHORITY"):
                citation_count += 1
                weighted_sum += 2.0 * weight
            elif atom_type in ("PERSON", "ENTITY"):
                person_count += 1
                weighted_sum += 1.0 * weight
            else:
                weighted_sum += 1.0 * weight

        # Convergence bonus: evidence from Lane A strengthens Lane D PPO scoring
        has_lane_a = len(lane_a_rows) > 0 and any(
            r["content"] and any(s in (r["content"] or "").lower() for s in LANE_A_SIGNALS)
            for r in lane_a_rows
        )
        has_lane_d = len(lane_d_rows) > 0 and any(
            r["content"] and any(s in (r["content"] or "").lower() for s in LANE_D_SIGNALS)
            for r in lane_d_rows
        )
        if has_lane_a and has_lane_d:
            convergence_bonus = 15.0  # Both lanes feeding PPO scoring

        raw = weighted_sum
        evidence_score = _safe_score((math.tanh(raw / 400.0)) * 100.0 + convergence_bonus)
        authority_score = _safe_score((citation_count / max(len(action["required"]), 1)) * 100.0)
        gap_count = max(0, len(action["required"]) - citation_count - fact_count)

        if evidence_score == 0.0 and len(all_rows) > 0:
            needs_review = 1

        self._upsert_score(action_id, evidence_score, authority_score, 0.0, gap_count, needs_review)

    def _upsert_score(self, action_id: str, evidence: float, authority: float,
                      vulnerability: float, gap_count: int, needs_review: int) -> None:
        self._db_execute("""
            INSERT OR REPLACE INTO action_scores
                (action_id, lane, evidence_score, authority_score, vulnerability_score, readiness_score, composite_score, gap_count, updated_by)
            VALUES (?, 'D', ?, ?, ?, 0.0, 0.0, ?, ?)
            ON CONFLICT(action_id) DO UPDATE SET
                evidence_score    = excluded.evidence_score,
                authority_score   = excluded.authority_score,
                vulnerability_score = excluded.vulnerability_score,
                gap_count         = excluded.gap_count,
                updated_by        = excluded.updated_by
        """, (action_id, evidence, authority, vulnerability, gap_count, self.agent_id))
        self.db.commit()

    def _finalize(self) -> None:
        row = self._db_execute(
            "SELECT COUNT(*), AVG(evidence_score) FROM action_scores WHERE lane='D'"
        ).fetchone()
        self._log("SUMMARY", f"Lane D: {row[0]} actions scored, avg evidence={row[1]:.1f}")
