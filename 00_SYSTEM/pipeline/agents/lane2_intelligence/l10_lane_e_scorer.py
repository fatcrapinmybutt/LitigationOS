"""
DELTA9 — L10 Lane E Scorer
Tier L · Lane 2 Intelligence · MAX LEVEL 9999++

Scores against Lane E judicial misconduct actions (E1–E8).
BONUS: Pulls evidence from ALL lanes for cross-lane misconduct evidence.
"""
import json
import math
from typing import Any

from ..agent_base import Agent9999
from ..agent_models import (
    SkipItemError, FatalAgentError, MASTER_INDEX_DB,
    LANE_E_SIGNALS,
)

POSTURE_WEIGHTS = {
    "SWORN_FACT": 5.0,
    "RECORD_FACT": 4.0,
    "EVIDENCE_FACT": 3.0,
    "ALLEGATION": 1.0,
    "INFERENCE": 0.5,
}

# Lane E Actions: E1–E8 — judicial misconduct / attorney misconduct
LANE_E_ACTIONS = {
    "E1": {"name": "Motion for Disqualification (MCR 2.003)",   "required": ["bias_evidence", "specific_grounds", "mcr_2003_basis", "affidavit"]},
    "E2": {"name": "JTC Formal Complaint",                      "required": ["judicial_conduct_violations", "pattern_documentation", "canon_citations", "timeline"]},
    "E3": {"name": "Motion for Peremptory Disqualification",    "required": ["peremptory_challenge_basis", "timely_filing_proof"]},
    "E4": {"name": "Ex Parte Contact Documentation",            "required": ["communication_evidence", "dates_and_participants", "prejudice_showing"]},
    "E5": {"name": "Canon Violation Brief",                     "required": ["specific_canons_violated", "factual_basis", "authority_citations"]},
    "E6": {"name": "Pattern of Bias Memorandum",                "required": ["chronological_incidents", "statistical_evidence", "comparative_analysis"]},
    "E7": {"name": "Motion for New Trial (Judicial Bias)",      "required": ["bias_evidence", "prejudice_to_outcome", "mcr_2003_grounds", "preserved_objections"]},
    "E8": {"name": "State Bar Grievance (Attorney Misconduct)", "required": ["attorney_conduct_violations", "mrpc_citations", "evidence_of_misconduct"]},
}


def _safe_score(value: float) -> float:
    if math.isnan(value) or math.isinf(value):
        return 0.0
    return max(0.0, min(100.0, value))


class LaneEScorer(Agent9999):
    """Score evidence against Lane E judicial misconduct actions (E1–E8).
    Cross-lane: draws atoms from ALL lanes for misconduct evidence."""

    def __init__(self):
        super().__init__(agent_id="L10-LANE-E-SCORE")
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
            "SELECT COUNT(*) FROM atoms WHERE meek_lane LIKE '%E%'"
        ).fetchone()
        if row[0] == 0:
            self._log("WARN", "No Lane-E atoms found — will rely on cross-lane misconduct evidence")

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
        return list(LANE_E_ACTIONS.keys())

    def _process_item(self, action_id: Any) -> None:
        action = LANE_E_ACTIONS[action_id]
        needs_review = 0

        # Cross-lane: pull atoms from Lane E direct AND from all other lanes
        lane_e_rows = self._db_execute(
            "SELECT atom_type, posture, content FROM atoms WHERE meek_lane LIKE '%E%'"
        ).fetchall()
        all_lane_rows = self._db_execute(
            "SELECT atom_type, posture, content FROM atoms "
            "WHERE meek_lane NOT LIKE '%E%'"
        ).fetchall()

        all_rows = list(lane_e_rows) + list(all_lane_rows)

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

        # Convergence bonus: cross-lane misconduct evidence strengthens Lane E
        has_lane_e = len(lane_e_rows) > 0 and any(
            r["content"] and any(s in (r["content"] or "").lower() for s in LANE_E_SIGNALS)
            for r in lane_e_rows
        )
        has_cross_lane = len(all_lane_rows) > 0
        if has_lane_e and has_cross_lane:
            convergence_bonus = 15.0  # Cross-lane evidence feeding misconduct scoring

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
            VALUES (?, 'E', ?, ?, ?, 0.0, 0.0, ?, ?)
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
            "SELECT COUNT(*), AVG(evidence_score) FROM action_scores WHERE lane='E'"
        ).fetchone()
        self._log("SUMMARY", f"Lane E: {row[0]} actions scored, avg evidence={row[1]:.1f}")
