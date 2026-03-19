"""
DELTA9 — L11 Lane F Scorer
Tier L · Lane 2 Intelligence · MAX LEVEL 9999++

Scores against Lane F appellate actions (F1–F8).
BONUS: Pulls evidence from ALL lanes for appellate-relevant evidence.
"""
import json
import math
from typing import Any

from ..agent_base import Agent9999
from ..agent_models import (
    SkipItemError, FatalAgentError, MASTER_INDEX_DB,
    LANE_F_SIGNALS,
)

POSTURE_WEIGHTS = {
    "SWORN_FACT": 5.0,
    "RECORD_FACT": 4.0,
    "EVIDENCE_FACT": 3.0,
    "ALLEGATION": 1.0,
    "INFERENCE": 0.5,
}

# Lane F Actions: F1–F8 — appellate / higher court actions
LANE_F_ACTIONS = {
    "F1": {"name": "Claim of Appeal (COA)",                       "required": ["final_order", "timely_filing", "jurisdictional_basis", "mcr_7_203"]},
    "F2": {"name": "Application for Leave to Appeal (COA)",       "required": ["order_appealed", "standard_of_review", "error_identification", "mcr_7_205"]},
    "F3": {"name": "Application for Leave to Appeal (MSC)",       "required": ["coa_decision", "significant_question", "conflict_with_precedent", "mcr_7_303"]},
    "F4": {"name": "Interlocutory Appeal",                        "required": ["non_final_order", "irreparable_harm", "leave_to_appeal_grounds"]},
    "F5": {"name": "MSC Original Action (Superintending Control)","required": ["extraordinary_circumstances", "no_adequate_remedy", "mcr_7_305"]},
    "F6": {"name": "Motion for Immediate Consideration",          "required": ["urgency_basis", "irreparable_harm", "likelihood_of_success"]},
    "F7": {"name": "Motion for Stay Pending Appeal",              "required": ["likelihood_of_success", "irreparable_harm", "balance_of_equities", "public_interest"]},
    "F8": {"name": "Brief on Appeal",                             "required": ["statement_of_facts", "issues_presented", "argument_with_authority", "standard_of_review"]},
}


def _safe_score(value: float) -> float:
    if math.isnan(value) or math.isinf(value):
        return 0.0
    return max(0.0, min(100.0, value))


class LaneFScorer(Agent9999):
    """Score evidence against Lane F appellate actions (F1–F8).
    Appellate: draws atoms from ALL lanes for appellate-relevant evidence."""

    def __init__(self):
        super().__init__(agent_id="L11-LANE-F-SCORE")
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
            "SELECT COUNT(*) FROM atoms WHERE meek_lane LIKE '%F%'"
        ).fetchone()
        if row[0] == 0:
            self._log("WARN", "No Lane-F atoms found — will rely on cross-lane appellate evidence")

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
        return list(LANE_F_ACTIONS.keys())

    def _process_item(self, action_id: Any) -> None:
        action = LANE_F_ACTIONS[action_id]
        needs_review = 0

        # Appellate: pull atoms from Lane F direct AND from all other lanes
        lane_f_rows = self._db_execute(
            "SELECT atom_type, posture, content FROM atoms WHERE meek_lane LIKE '%F%'"
        ).fetchall()
        all_lane_rows = self._db_execute(
            "SELECT atom_type, posture, content FROM atoms "
            "WHERE meek_lane NOT LIKE '%F%'"
        ).fetchall()

        all_rows = list(lane_f_rows) + list(all_lane_rows)

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

        # Convergence bonus: cross-lane evidence strengthens appellate scoring
        has_lane_f = len(lane_f_rows) > 0 and any(
            r["content"] and any(s in (r["content"] or "").lower() for s in LANE_F_SIGNALS)
            for r in lane_f_rows
        )
        has_cross_lane = len(all_lane_rows) > 0
        if has_lane_f and has_cross_lane:
            convergence_bonus = 15.0  # Cross-lane evidence feeding appellate scoring

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
            VALUES (?, 'F', ?, ?, ?, 0.0, 0.0, ?, ?)
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
            "SELECT COUNT(*), AVG(evidence_score) FROM action_scores WHERE lane='F'"
        ).fetchone()
        self._log("SUMMARY", f"Lane F: {row[0]} actions scored, avg evidence={row[1]:.1f}")
