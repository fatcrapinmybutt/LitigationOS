"""
DELTA9 — L02 Lane B Scorer
Tier L · Lane 2 Intelligence · MAX LEVEL 9999++

Scores ALL evidence against Lane B housing/tenant legal actions (B1–B14).
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

# Lane B Actions: B1–B14 — housing/tenant legal warfare actions
LANE_B_ACTIONS = {
    "B1":  {"name": "Breach of Warranty of Habitability",            "required": ["habitability_defect", "notice_to_landlord", "failure_to_repair"]},
    "B2":  {"name": "Violation of Truth in Renting Act",             "required": ["lease_provision", "statutory_violation", "tenant_harm"]},
    "B3":  {"name": "Security Deposit Violation (MCL 554.602)",      "required": ["deposit_amount", "move_out_date", "itemization_failure"]},
    "B4":  {"name": "Retaliatory Eviction Defense",                  "required": ["protected_activity", "adverse_action", "temporal_proximity"]},
    "B5":  {"name": "Consumer Protection Act Violation (MCL 445)",   "required": ["unfair_practice", "consumer_transaction", "damages_proof"]},
    "B6":  {"name": "Constructive Eviction",                        "required": ["uninhabitable_conditions", "notice_given", "tenant_vacated"]},
    "B7":  {"name": "Illegal Entry / Privacy Violation",             "required": ["unauthorized_entry", "date_time_evidence", "notice_absence"]},
    "B8":  {"name": "Utility Shutoff Violation",                     "required": ["shutoff_evidence", "no_court_order", "tenant_damages"]},
    "B9":  {"name": "Mobile Home Commission Act Violation",          "required": ["commission_rule", "park_violation", "tenant_impact"]},
    "B10": {"name": "Rent Overcharge / Improper Fee",                "required": ["fee_documentation", "lease_terms", "overcharge_calc"]},
    "B11": {"name": "Failure to Provide Essential Services",         "required": ["service_type", "duration", "notice_to_landlord"]},
    "B12": {"name": "Lease Fraud / Misrepresentation",               "required": ["false_statement", "reliance", "damages"]},
    "B13": {"name": "Treble Damages (Security Deposit)",             "required": ["deposit_violation", "bad_faith", "statutory_basis"]},
    "B14": {"name": "Class Action — Pattern of Violations",          "required": ["common_questions", "numerosity", "typicality", "adequacy"]},
}


def _safe_score(value: float) -> float:
    if math.isnan(value) or math.isinf(value):
        return 0.0
    return max(0.0, min(100.0, value))


class LaneBScorer(Agent9999):
    """Score all evidence against Lane B housing actions (B1–B14)."""

    def __init__(self):
        super().__init__(agent_id="L02-LANE-B-SCORE")
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
            "SELECT COUNT(*) FROM atoms WHERE meek_lane LIKE '%B%'"
        ).fetchone()
        if row[0] == 0:
            self._log("WARN", "No Lane-B atoms found — scores will be zero")

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
        return list(LANE_B_ACTIONS.keys())

    def _process_item(self, action_id: Any) -> None:
        action = LANE_B_ACTIONS[action_id]
        needs_review = 0

        rows = self._db_execute(
            "SELECT atom_type, posture, content FROM atoms WHERE meek_lane LIKE '%B%'"
        ).fetchall()

        if not rows:
            self._upsert_score(action_id, 0.0, 0.0, 0.0, 0, needs_review)
            return

        fact_count = 0
        citation_count = 0
        person_count = 0
        weighted_sum = 0.0

        for row in rows:
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

        raw = weighted_sum
        evidence_score = _safe_score((math.tanh(raw / 300.0)) * 100.0)
        authority_score = _safe_score((citation_count / max(len(action["required"]), 1)) * 100.0)
        gap_count = max(0, len(action["required"]) - citation_count - fact_count)

        if evidence_score == 0.0 and len(rows) > 0:
            needs_review = 1

        self._upsert_score(action_id, evidence_score, authority_score, 0.0, gap_count, needs_review)

    def _upsert_score(self, action_id: str, evidence: float, authority: float,
                      vulnerability: float, gap_count: int, needs_review: int) -> None:
        self._db_execute("""
            INSERT OR REPLACE INTO action_scores
                (action_id, lane, evidence_score, authority_score, vulnerability_score, readiness_score, composite_score, gap_count, updated_by)
            VALUES (?, 'B', ?, ?, ?, 0.0, 0.0, ?, ?)
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
            "SELECT COUNT(*), AVG(evidence_score) FROM action_scores WHERE lane='B'"
        ).fetchone()
        self._log("SUMMARY", f"Lane B: {row[0]} actions scored, avg evidence={row[1]:.1f}")
