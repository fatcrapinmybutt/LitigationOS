"""
DELTA9 — L04 Gap Detector
Tier L · Lane 2 Intelligence · MAX LEVEL 9999++

Compares discovered evidence against COMPLETE requirement list for all 56 actions.
Generates EGCP v2 gap tickets as atoms for missing evidence.
"""
import json
import hashlib
import math
import time
from typing import Any, Dict, List

from ..agent_base import Agent9999
from ..agent_models import (
    SkipItemError, FatalAgentError, MASTER_INDEX_DB,
    LANE_A_SIGNALS, LANE_B_SIGNALS, LANE_C_SIGNALS,
)

# Import action dicts from sibling scorers
from .l01_lane_a_scorer import LANE_A_ACTIONS
from .l02_lane_b_scorer import LANE_B_ACTIONS
from .l03_lane_c_scorer import LANE_C_ACTIONS

# Critical gap threshold
CRITICAL_THRESHOLD = 30.0

# Merge all actions into a single registry
ALL_ACTIONS: Dict[str, dict] = {}
ALL_ACTIONS.update({k: {**v, "lane": "A"} for k, v in LANE_A_ACTIONS.items()})
ALL_ACTIONS.update({k: {**v, "lane": "B"} for k, v in LANE_B_ACTIONS.items()})
ALL_ACTIONS.update({k: {**v, "lane": "C"} for k, v in LANE_C_ACTIONS.items()})

# Acquisition methods by element type
ACQUISITION_METHODS = {
    "custody_order":        "Court records search / FOIA request",
    "violation_evidence":   "Document review / witness interview",
    "pattern_proof":        "Timeline analysis / database query",
    "witness_statements":   "Deposition / affidavit collection",
    "threat_evidence":      "Police reports / communication records",
    "deposit_amount":       "Lease review / bank records",
    "constitutional_right": "Case law research / brief drafting",
    "state_actor":          "Official records / employment verification",
}


class GapDetector(Agent9999):
    """Detect evidence gaps across all 56 legal actions and generate gap tickets."""

    def __init__(self):
        super().__init__(agent_id="L04-GAP-DETECT")
        self.parallel_workers = 4   # I/O bound — parallelize file reads
        self.item_timeout = 15      # skip files that take >15s to read
        self.checkpoint_interval = 200

    def _validate_preconditions(self) -> None:
        for tbl in ("atoms", "action_scores"):
            cursor = self._db_execute(
                "SELECT name FROM sqlite_master WHERE type='table' AND name=?", (tbl,)
            )
            if not cursor.fetchone():
                raise FatalAgentError(f"Required table '{tbl}' missing — run scorers first")

    def _ensure_tables(self) -> None:
        # Ensure atoms table can hold gap_ticket type
        self._db_execute("""
            CREATE TABLE IF NOT EXISTS atoms (
                id          INTEGER PRIMARY KEY AUTOINCREMENT,
                atom_type   TEXT,
                content     TEXT,
                posture     TEXT,
                meek_lane   TEXT,
                source_file TEXT,
                created_at  TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        self.db.commit()

    def _get_work_items(self) -> list:
        return list(ALL_ACTIONS.keys())

    def _process_item(self, action_id: Any) -> None:
        action = ALL_ACTIONS[action_id]
        lane = action["lane"]
        required = action["required"]

        # Get current score
        score_row = self._db_execute(
            "SELECT evidence_score, gap_count FROM action_scores WHERE action_id=? AND lane=?",
            (action_id, lane)
        ).fetchone()

        evidence_score = float(score_row["evidence_score"]) if score_row else 0.0
        current_gaps = int(score_row["gap_count"]) if score_row else len(required)

        if current_gaps == 0 and evidence_score >= CRITICAL_THRESHOLD:
            return  # No gaps to detect

        # Identify which specific elements are missing
        existing_atoms = self._db_execute(
            "SELECT content FROM atoms WHERE meek_lane LIKE ? AND atom_type IN ('FACT','FACT_ATOM','CITATION','AUTHORITY')",
            (f"%{lane}%",)
        ).fetchall()

        existing_content = " ".join(
            (r["content"] or "") for r in existing_atoms
        ).lower()

        is_critical = evidence_score < CRITICAL_THRESHOLD
        severity = "CRITICAL" if is_critical else "MINOR"

        for element in required:
            # Simple heuristic: check if element keywords appear in existing evidence
            element_keywords = element.replace("_", " ").lower().split()
            found = sum(1 for kw in element_keywords if kw in existing_content)
            coverage = found / max(len(element_keywords), 1)

            if coverage < 0.5:
                # Generate gap ticket
                acquisition = ACQUISITION_METHODS.get(
                    element, "Manual review / targeted discovery"
                )
                search_terms = element.replace("_", " ").split()

                ticket = {
                    "action_id": action_id,
                    "action_name": action["name"],
                    "lane": lane,
                    "target_field": element,
                    "why_needed": f"Required element for {action['name']} — "
                                  f"current coverage {coverage:.0%}",
                    "acquisition_method": acquisition,
                    "search_terms": search_terms,
                    "severity": severity,
                    "evidence_score": evidence_score,
                }

                self._db_execute(
                    """INSERT OR IGNORE INTO atoms (id, atom_type, source_file_id, meek_lane, content, confidence, posture, created_by)
                       VALUES (?, 'gap_ticket', 0, ?, ?, 1.0, 'SYSTEM', ?)""",
                    (hashlib.sha1(f'L04|gap|{action_id}'.encode()).hexdigest()[:16],
                     lane, json.dumps(ticket), f'L04-GAP-DETECT/{action_id}')
                )

        self.db.commit()

    def _finalize(self) -> None:
        critical = self._db_execute(
            "SELECT COUNT(*) FROM atoms WHERE atom_type='gap_ticket' AND content LIKE '%CRITICAL%'"
        ).fetchone()[0]
        minor = self._db_execute(
            "SELECT COUNT(*) FROM atoms WHERE atom_type='gap_ticket' AND content LIKE '%MINOR%'"
        ).fetchone()[0]
        self._log("SUMMARY", f"Gap tickets: {critical} CRITICAL, {minor} MINOR")
