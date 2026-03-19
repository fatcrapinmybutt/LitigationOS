"""
DELTA9 — L01 Lane A Scorer
Tier L · Lane 2 Intelligence · MAX LEVEL 9999++

Scores ALL evidence against Lane A legal actions (A1–A35).
Computes composite scores from fact/citation/person atoms weighted by posture.
"""
import json
import math
from typing import Any

from ..agent_base import Agent9999
from ..agent_models import (
    SkipItemError, FatalAgentError, MASTER_INDEX_DB,
    LANE_A_SIGNALS, LANE_B_SIGNALS, LANE_C_SIGNALS,
)

# Posture weights — sworn testimony > record > evidence > allegation > inference
POSTURE_WEIGHTS = {
    "SWORN_FACT": 5.0,
    "RECORD_FACT": 4.0,
    "EVIDENCE_FACT": 3.0,
    "ALLEGATION": 1.0,
    "INFERENCE": 0.5,
}

# Lane A Actions: A1–A35 — family/custody legal warfare actions
LANE_A_ACTIONS = {
    "A1":  {"name": "Emergency Motion to Modify Custody",          "required": ["custody_order", "changed_circumstances", "child_endangerment"]},
    "A2":  {"name": "Motion for Contempt of Custody Order",        "required": ["custody_order", "violation_evidence", "pattern_proof"]},
    "A3":  {"name": "Motion to Compel Discovery",                  "required": ["discovery_request", "non_compliance_proof", "good_faith_effort"]},
    "A4":  {"name": "Motion for Protective Order",                 "required": ["threat_evidence", "prior_incidents", "witness_statements"]},
    "A5":  {"name": "Motion to Modify Parenting Time",             "required": ["current_order", "best_interest_factors", "changed_circumstances"]},
    "A6":  {"name": "Motion for Psychological Evaluation",         "required": ["behavioral_evidence", "child_impact", "expert_basis"]},
    "A7":  {"name": "Motion to Appoint Guardian Ad Litem",         "required": ["conflict_evidence", "child_needs", "statutory_basis"]},
    "A8":  {"name": "Motion for Drug/Alcohol Testing",             "required": ["substance_evidence", "child_risk", "incident_reports"]},
    "A9":  {"name": "Motion to Restrict Overnight Parenting Time", "required": ["safety_concerns", "housing_evidence", "child_welfare"]},
    "A10": {"name": "Motion for Makeup Parenting Time",            "required": ["denied_time_log", "order_terms", "communication_records"]},
    "A11": {"name": "Motion to Hold in Contempt (Support)",        "required": ["support_order", "payment_records", "arrearage_calc"]},
    "A12": {"name": "Motion to Modify Child Support",              "required": ["income_change", "current_order", "child_needs_update"]},
    "A13": {"name": "Motion for Attorney Fees",                    "required": ["fee_records", "ability_to_pay", "litigation_conduct"]},
    "A14": {"name": "Motion to Enforce Property Settlement",       "required": ["settlement_terms", "non_compliance", "asset_records"]},
    "A15": {"name": "Motion for Change of Venue",                  "required": ["bias_evidence", "convenience_factors", "statutory_basis"]},
    "A16": {"name": "Motion to Disqualify Judge",                  "required": ["bias_evidence", "ex_parte_contact", "pattern_proof"]},
    "A17": {"name": "Motion to Seal Records",                      "required": ["privacy_interest", "minor_children", "good_cause"]},
    "A18": {"name": "Motion for De Novo Hearing",                  "required": ["referee_recommendation", "objection_basis", "timeline_proof"]},
    "A19": {"name": "Motion to Strike Pleading",                   "required": ["defective_pleading", "prejudice_shown", "rule_violation"]},
    "A20": {"name": "Motion for Summary Disposition",              "required": ["undisputed_facts", "legal_basis", "no_genuine_issue"]},
    "A21": {"name": "Motion to Amend Complaint",                   "required": ["new_facts", "timeliness", "no_prejudice"]},
    "A22": {"name": "Motion for Stay Pending Appeal",              "required": ["likelihood_success", "irreparable_harm", "bond_offer"]},
    "A23": {"name": "PPO Petition (Domestic)",                     "required": ["threat_evidence", "prior_abuse", "immediate_danger"]},
    "A24": {"name": "Motion to Terminate PPO",                     "required": ["changed_circumstances", "no_current_threat", "compliance_record"]},
    "A25": {"name": "Motion for Friend of Court Review",           "required": ["current_order", "changed_circumstances", "foc_referral"]},
    "A26": {"name": "Motion to Correct Clerical Error",            "required": ["error_identification", "correct_terms", "order_reference"]},
    "A27": {"name": "Motion for Bench Warrant",                    "required": ["non_appearance", "proper_notice", "order_to_appear"]},
    "A28": {"name": "Motion to Set Aside Default",                 "required": ["good_cause", "meritorious_defense", "timeliness"]},
    "A29": {"name": "Motion for Interim Support",                  "required": ["need_showing", "ability_to_pay", "current_expenses"]},
    "A30": {"name": "Motion to Consolidate Cases",                 "required": ["common_facts", "common_parties", "judicial_economy"]},
    "A31": {"name": "Motion for Sanctions (Bad Faith)",            "required": ["bad_faith_conduct", "prejudice", "prior_warnings"]},
    "A32": {"name": "Motion to Quash Subpoena",                    "required": ["subpoena_defect", "privilege_claim", "undue_burden"]},
    "A33": {"name": "Application for Leave to Appeal",             "required": ["legal_error", "interlocutory_basis", "irreparable_harm"]},
    "A34": {"name": "Complaint for Superintending Control",        "required": ["judicial_error", "no_adequate_remedy", "clear_duty"]},
    "A35": {"name": "Federal §1983 Civil Rights (Custody Lane)",   "required": ["constitutional_violation", "state_actor", "damages_proof"]},
}


def _safe_score(value: float) -> float:
    """Clamp to [0, 100] and replace NaN/Inf with 0."""
    if math.isnan(value) or math.isinf(value):
        return 0.0
    return max(0.0, min(100.0, value))


class LaneAScorer(Agent9999):
    """Score all evidence against Lane A legal actions (A1–A35)."""

    def __init__(self):
        super().__init__(agent_id="L01-LANE-A-SCORE")
        self.parallel_workers = 4   # I/O bound — parallelize file reads
        self.item_timeout = 15      # skip files that take >15s to read
        self.checkpoint_interval = 200

    # ------------------------------------------------------------------
    def _validate_preconditions(self) -> None:
        cursor = self._db_execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name='atoms'"
        )
        if not cursor.fetchone():
            raise FatalAgentError("Required table 'atoms' missing — run Tier 1 first")
        row = self._db_execute(
            "SELECT COUNT(*) FROM atoms WHERE meek_lane LIKE '%A%'"
        ).fetchone()
        if row[0] == 0:
            self._log("WARN", "No Lane-A atoms found — scores will be zero")

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
        return list(LANE_A_ACTIONS.keys())

    def _process_item(self, action_id: Any) -> None:
        action = LANE_A_ACTIONS[action_id]
        needs_review = 0

        # Fetch Lane-A atoms
        rows = self._db_execute(
            "SELECT atom_type, posture, content FROM atoms WHERE meek_lane LIKE '%A%'"
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

        # Normalise to 0–100 (sigmoid-like: tanh scaling)
        raw = weighted_sum
        evidence_score = _safe_score((math.tanh(raw / 500.0)) * 100.0)
        authority_score = _safe_score((citation_count / max(len(action["required"]), 1)) * 100.0)

        # Gap count: required elements not yet evidenced
        gap_count = max(0, len(action["required"]) - citation_count - fact_count)

        # Check for NaN flag
        if evidence_score == 0.0 and len(rows) > 0:
            needs_review = 1

        self._upsert_score(action_id, evidence_score, authority_score, 0.0, gap_count, needs_review)

    # ------------------------------------------------------------------
    def _upsert_score(self, action_id: str, evidence: float, authority: float,
                      vulnerability: float, gap_count: int, needs_review: int) -> None:
        self._db_execute("""
            INSERT OR REPLACE INTO action_scores
                (action_id, lane, evidence_score, authority_score, vulnerability_score, readiness_score, composite_score, gap_count, updated_by)
            VALUES (?, 'A', ?, ?, ?, 0.0, 0.0, ?, ?)
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
            "SELECT COUNT(*), AVG(evidence_score) FROM action_scores WHERE lane='A'"
        ).fetchone()
        self._log("SUMMARY", f"Lane A: {row[0]} actions scored, avg evidence={row[1]:.1f}")
