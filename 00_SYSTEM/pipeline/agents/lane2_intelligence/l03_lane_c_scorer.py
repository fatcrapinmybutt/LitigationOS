"""
DELTA9 — L03 Lane C Scorer
Tier L · Lane 2 Intelligence · MAX LEVEL 9999++

Scores against Lane C convergence actions (C1–C7).
BONUS: Pulls evidence from BOTH Lane A and Lane B for convergence scoring.
"""
import json
import math
from typing import Any

from ..agent_base import Agent9999
from ..agent_models import (
    SkipItemError, FatalAgentError, MASTER_INDEX_DB,
    LANE_A_SIGNALS, LANE_B_SIGNALS, LANE_C_SIGNALS,
)

POSTURE_WEIGHTS = {
    "SWORN_FACT": 5.0,
    "RECORD_FACT": 4.0,
    "EVIDENCE_FACT": 3.0,
    "ALLEGATION": 1.0,
    "INFERENCE": 0.5,
}

# Lane C Actions: C1–C7 — convergence / civil rights / systemic
LANE_C_ACTIONS = {
    "C1": {"name": "42 USC §1983 — Due Process Violation",          "required": ["constitutional_right", "state_actor", "causation", "damages"]},
    "C2": {"name": "42 USC §1983 — Equal Protection Violation",     "required": ["similarly_situated", "disparate_treatment", "no_rational_basis"]},
    "C3": {"name": "42 USC §1985 — Conspiracy to Deprive Rights",   "required": ["two_or_more_actors", "agreement", "overt_act", "class_animus"]},
    "C4": {"name": "Monell Municipal Liability",                     "required": ["policy_or_custom", "deliberate_indifference", "final_policymaker"]},
    "C5": {"name": "Judicial Misconduct Complaint (JTC)",            "required": ["judicial_act", "canon_violation", "pattern_evidence"]},
    "C6": {"name": "State Bar Grievance — Opposing Counsel",         "required": ["mrpc_violation", "specific_conduct", "client_harm"]},
    "C7": {"name": "Pattern & Practice — Systemic Challenge",        "required": ["multiple_incidents", "common_policy", "statistical_evidence", "representative_cases"]},
}


def _safe_score(value: float) -> float:
    if math.isnan(value) or math.isinf(value):
        return 0.0
    return max(0.0, min(100.0, value))


class LaneCScorer(Agent9999):
    """Score evidence against Lane C convergence actions (C1–C7).
    Convergence: draws atoms from ALL lanes (A, B, C)."""

    def __init__(self):
        super().__init__(agent_id="L03-LANE-C-SCORE")
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
            "SELECT COUNT(*) FROM atoms WHERE meek_lane LIKE '%C%'"
        ).fetchone()
        if row[0] == 0:
            self._log("WARN", "No Lane-C atoms found — will rely on convergence from A+B")

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
        return list(LANE_C_ACTIONS.keys())

    def _process_item(self, action_id: Any) -> None:
        action = LANE_C_ACTIONS[action_id]
        needs_review = 0

        # CONVERGENCE: pull atoms from Lane C direct AND from Lanes A+B
        lane_c_rows = self._db_execute(
            "SELECT atom_type, posture, content FROM atoms WHERE meek_lane LIKE '%C%'"
        ).fetchall()
        lane_ab_rows = self._db_execute(
            "SELECT atom_type, posture, content FROM atoms "
            "WHERE meek_lane LIKE '%A%' OR meek_lane LIKE '%B%'"
        ).fetchall()

        all_rows = list(lane_c_rows) + list(lane_ab_rows)

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

        # Convergence bonus: evidence from both Lane A and Lane B strengthens Lane C
        has_lane_a = len(lane_ab_rows) > 0 and any(
            r["content"] and any(s in (r["content"] or "").lower() for s in LANE_A_SIGNALS)
            for r in lane_ab_rows
        )
        has_lane_b = len(lane_ab_rows) > 0 and any(
            r["content"] and any(s in (r["content"] or "").lower() for s in LANE_B_SIGNALS)
            for r in lane_ab_rows
        )
        if has_lane_a and has_lane_b:
            convergence_bonus = 15.0  # Both lanes feeding convergence

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
            VALUES (?, 'C', ?, ?, ?, 0.0, 0.0, ?, ?)
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
            "SELECT COUNT(*), AVG(evidence_score) FROM action_scores WHERE lane='C'"
        ).fetchone()
        self._log("SUMMARY", f"Lane C: {row[0]} actions scored, avg evidence={row[1]:.1f}")
