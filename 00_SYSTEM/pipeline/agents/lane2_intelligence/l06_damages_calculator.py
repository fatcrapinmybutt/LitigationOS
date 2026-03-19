"""
DELTA9 — L06 Damages Calculator
Tier L · Lane 2 Intelligence · MAX LEVEL 9999++

Computes damages per lane:
  Lane A: emotional distress, economic (legal costs), punitive
  Lane B: habitability, security deposit (treble MCL), moving costs
  Lane C: §1983 compensatory + punitive from both lanes
"""
import json
import math
from typing import Any, Dict

from ..agent_base import Agent9999
from ..agent_models import (
    SkipItemError, FatalAgentError, MASTER_INDEX_DB,
    LANE_A_SIGNALS, LANE_B_SIGNALS, LANE_C_SIGNALS,
)

# Import action dicts
from .l01_lane_a_scorer import LANE_A_ACTIONS
from .l02_lane_b_scorer import LANE_B_ACTIONS
from .l03_lane_c_scorer import LANE_C_ACTIONS

# Damages constants
DURATION_DAYS = 329                  # Duration of harm in days
PER_DIEM_RATE = 75.00                # Conservative mid-range ($50–$100)
BASELINE_EMOTIONAL_DISTRESS = DURATION_DAYS * PER_DIEM_RATE  # $24,675

# Lane B multipliers
TREBLE_MULTIPLIER = 3.0              # MCL security deposit treble damages
ESTIMATED_SECURITY_DEPOSIT = 1500.00
ESTIMATED_HABITABILITY_DAMAGES = 5000.00
ESTIMATED_MOVING_COSTS = 3500.00

# Lane A economic estimates
ESTIMATED_LEGAL_COSTS = 15000.00
ESTIMATED_LOST_INCOME = 8000.00

# Punitive multiplier (based on pattern evidence strength)
PUNITIVE_BASE_MULTIPLIER = 2.0


def _safe_score(value: float) -> float:
    if math.isnan(value) or math.isinf(value):
        return 0.0
    return max(0.0, min(100.0, value))


class DamagesCalculator(Agent9999):
    """Compute damages for all legal actions across all lanes."""

    def __init__(self):
        super().__init__(agent_id="L06-DAMAGES")
        self.parallel_workers = 4   # I/O bound — parallelize file reads
        self.item_timeout = 15      # skip files that take >15s to read
        self.checkpoint_interval = 200

    def _validate_preconditions(self) -> None:
        cursor = self._db_execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name='action_scores'"
        )
        if not cursor.fetchone():
            raise FatalAgentError("Required table 'action_scores' missing — run scorers first")

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
        items = []
        for aid in LANE_A_ACTIONS:
            items.append({"action_id": aid, "lane": "A"})
        for aid in LANE_B_ACTIONS:
            items.append({"action_id": aid, "lane": "B"})
        for aid in LANE_C_ACTIONS:
            items.append({"action_id": aid, "lane": "C"})
        return items

    def _process_item(self, item: Any) -> None:
        action_id = item["action_id"]
        lane = item["lane"]

        # Get current evidence score to weight damages
        score_row = self._db_execute(
            "SELECT evidence_score FROM action_scores WHERE action_id=? AND lane=?",
            (action_id, lane)
        ).fetchone()
        evidence_pct = float(score_row["evidence_score"]) / 100.0 if score_row else 0.0

        if lane == "A":
            damages = self._calc_lane_a_damages(action_id, evidence_pct)
        elif lane == "B":
            damages = self._calc_lane_b_damages(action_id, evidence_pct)
        else:
            damages = self._calc_lane_c_damages(action_id, evidence_pct)

        damages_json = json.dumps(damages)
        total_damages = damages.get("total_estimated", 0.0)

        # Only update damages_json — do NOT overwrite composite_score from L07
        self._db_execute("""
            UPDATE action_scores SET damages_json = ?, updated_by = ?
            WHERE action_id = ?
        """, (damages_json, self.agent_id, action_id))
        if self.db.total_changes == 0:
            # Row doesn't exist yet — insert with damages only
            self._db_execute("""
                INSERT OR IGNORE INTO action_scores (action_id, lane, composite_score, damages_json, updated_by)
                VALUES (?, ?, 0.0, ?, ?)
            """, (action_id, lane, damages_json, self.agent_id))
        self.db.commit()

    def _calc_lane_a_damages(self, action_id: str, evidence_pct: float) -> Dict:
        """Lane A: emotional distress + economic + punitive."""
        emotional = BASELINE_EMOTIONAL_DISTRESS * evidence_pct
        economic = (ESTIMATED_LEGAL_COSTS + ESTIMATED_LOST_INCOME) * evidence_pct

        # Punitive: only for pattern-based actions
        pattern_actions = {"A2", "A16", "A31", "A35"}
        punitive_mult = PUNITIVE_BASE_MULTIPLIER if action_id in pattern_actions else 0.0
        punitive = (emotional + economic) * punitive_mult * evidence_pct

        total = emotional + economic + punitive
        return {
            "lane": "A",
            "action_id": action_id,
            "emotional_distress": round(emotional, 2),
            "emotional_basis": f"{DURATION_DAYS} days × ${PER_DIEM_RATE}/day × {evidence_pct:.0%} evidence",
            "economic_damages": round(economic, 2),
            "punitive_damages": round(punitive, 2),
            "total_estimated": round(total, 2),
            "confidence": "HIGH" if evidence_pct > 0.7 else "MEDIUM" if evidence_pct > 0.4 else "LOW",
        }

    def _calc_lane_b_damages(self, action_id: str, evidence_pct: float) -> Dict:
        """Lane B: habitability + security deposit (treble) + moving costs."""
        habitability = ESTIMATED_HABITABILITY_DAMAGES * evidence_pct
        moving = ESTIMATED_MOVING_COSTS * evidence_pct

        # Treble damages for security deposit actions
        treble_actions = {"B3", "B13"}
        if action_id in treble_actions:
            security = ESTIMATED_SECURITY_DEPOSIT * TREBLE_MULTIPLIER * evidence_pct
        else:
            security = ESTIMATED_SECURITY_DEPOSIT * evidence_pct

        total = habitability + security + moving
        return {
            "lane": "B",
            "action_id": action_id,
            "habitability_damages": round(habitability, 2),
            "security_deposit": round(security, 2),
            "treble_applied": action_id in treble_actions,
            "moving_costs": round(moving, 2),
            "total_estimated": round(total, 2),
            "confidence": "HIGH" if evidence_pct > 0.7 else "MEDIUM" if evidence_pct > 0.4 else "LOW",
        }

    def _calc_lane_c_damages(self, action_id: str, evidence_pct: float) -> Dict:
        """Lane C: §1983 compensatory + punitive from converging lanes."""
        # Pull Lane A + Lane B totals for convergence
        lane_a_total = 0.0
        lane_b_total = 0.0

        a_rows = self._db_execute(
            "SELECT damages_json FROM action_scores WHERE lane='A' AND damages_json IS NOT NULL"
        ).fetchall()
        for r in a_rows:
            try:
                d = json.loads(r["damages_json"])
                lane_a_total += d.get("total_estimated", 0.0)
            except (json.JSONDecodeError, TypeError):
                pass

        b_rows = self._db_execute(
            "SELECT damages_json FROM action_scores WHERE lane='B' AND damages_json IS NOT NULL"
        ).fetchall()
        for r in b_rows:
            try:
                d = json.loads(r["damages_json"])
                lane_b_total += d.get("total_estimated", 0.0)
            except (json.JSONDecodeError, TypeError):
                pass

        compensatory = (lane_a_total + lane_b_total) * evidence_pct * 0.5
        punitive = compensatory * PUNITIVE_BASE_MULTIPLIER * evidence_pct
        total = compensatory + punitive

        return {
            "lane": "C",
            "action_id": action_id,
            "compensatory_from_A": round(lane_a_total * evidence_pct * 0.5, 2),
            "compensatory_from_B": round(lane_b_total * evidence_pct * 0.5, 2),
            "compensatory_total": round(compensatory, 2),
            "punitive_damages": round(punitive, 2),
            "total_estimated": round(total, 2),
            "convergence_note": "§1983 damages drawn from both Lane A and Lane B harm",
            "confidence": "HIGH" if evidence_pct > 0.7 else "MEDIUM" if evidence_pct > 0.4 else "LOW",
        }

    def _finalize(self) -> None:
        import json as _json
        for lane in ("A", "B", "C"):
            rows = self._db_execute(
                "SELECT damages_json FROM action_scores WHERE lane=? AND damages_json IS NOT NULL",
                (lane,)
            ).fetchall()
            total = 0.0
            for r in rows:
                try:
                    total += _json.loads(r["damages_json"]).get("total_estimated", 0.0)
                except (TypeError, ValueError):
                    pass
            self._log("SUMMARY", f"Lane {lane} total estimated damages: ${total:,.2f}")
