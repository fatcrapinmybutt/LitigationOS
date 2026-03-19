"""
J06 Disqualification Engine — Scores MCR 2.003(C) grounds for judicial disqualification.
Evaluates personal bias, knowledge of disputed facts, and self-reinforcing patterns.
"""
import json
from typing import Any, Dict, List

from ..agent_base import Agent9999
from ..agent_models import (
    SkipItemError, FatalAgentError, MASTER_INDEX_DB,
    LANE_A_SIGNALS, LANE_B_SIGNALS, LANE_C_SIGNALS,
)

# MCR 2.003(C) grounds with scoring weights
DISQUALIFICATION_GROUNDS: Dict[str, Dict[str, Any]] = {
    "personal_bias": {
        "label": "MCR 2.003(C)(1)(a) — Personal bias or prejudice",
        "weight": 3.0,
        "finding_types": {"bias_indicator", "canon_violation"},
    },
    "personal_knowledge": {
        "label": "MCR 2.003(C)(1)(b) — Personal knowledge of disputed facts",
        "weight": 2.5,
        "finding_types": {"ex_parte", "procedural_issue"},
    },
    "self_reinforcing": {
        "label": "Self-reinforcing pattern — 329+ days separation",
        "weight": 2.0,
        "finding_types": {"order_analysis", "benchbook_violation", "procedural_issue"},
    },
}

# Key data point: days of separation enforcement
SEPARATION_DAYS_KEY = 329


class DisqualificationEngine(Agent9999):
    """Score MCR 2.003(C) disqualification grounds from judicial findings."""

    def __init__(self, **kwargs):
        super().__init__(agent_id="J06-DISQUAL", **kwargs)
        self.confidence_threshold = 0.7

    # ------------------------------------------------------------------
    def _ensure_tables(self) -> None:
        self._db_execute("""
            CREATE TABLE IF NOT EXISTS judicial_findings (
                id          INTEGER PRIMARY KEY AUTOINCREMENT,
                judge       TEXT NOT NULL,
                finding_type TEXT NOT NULL,
                description TEXT,
                severity    INTEGER DEFAULT 0,
                source_file_id INTEGER,
                canon_ref   TEXT,
                confidence  REAL DEFAULT 0.0,
                status      TEXT DEFAULT 'active',
                agent_id    TEXT,
                created_at  TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        self._db_execute("""
            CREATE TABLE IF NOT EXISTS action_scores (
                id          INTEGER PRIMARY KEY AUTOINCREMENT,
                action_type TEXT NOT NULL,
                judge       TEXT NOT NULL,
                ground      TEXT NOT NULL,
                score       REAL DEFAULT 0.0,
                max_score   REAL DEFAULT 10.0,
                detail      TEXT,
                metadata    TEXT,
                source_ids  TEXT,
                status      TEXT DEFAULT 'active',
                agent_id    TEXT,
                created_at  TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        self.db.commit()

    # ------------------------------------------------------------------
    def _validate_preconditions(self) -> None:
        try:
            row = self._db_execute(
                "SELECT COUNT(*) as cnt FROM judicial_findings WHERE status = 'active'"
            ).fetchone()
            if row and row["cnt"] > 0:
                return
        except Exception:
            pass
        self._log("WARN", "No active judicial findings for disqualification scoring")

    # ------------------------------------------------------------------
    def _get_work_items(self) -> list:
        """Each judge with active findings is a work item."""
        try:
            judges = self._db_execute(
                "SELECT DISTINCT judge FROM judicial_findings WHERE status = 'active'"
            ).fetchall()
            return judges if judges else []
        except Exception:
            return []

    # ------------------------------------------------------------------
    def _process_item(self, item: Any) -> None:
        judge = item["judge"]
        findings = self._db_execute(
            """SELECT * FROM judicial_findings
               WHERE judge = ? AND status = 'active'""",
            (judge,),
        ).fetchall()

        if not findings:
            raise SkipItemError(f"No active findings for judge {judge}")

        for ground_key, ground_def in DISQUALIFICATION_GROUNDS.items():
            relevant = [f for f in findings
                        if f["finding_type"] in ground_def["finding_types"]]
            if not relevant:
                continue

            score = self._compute_ground_score(relevant, ground_def)
            source_ids = [f["id"] for f in relevant]

            detail = self._format_ground_detail(judge, ground_def, relevant, score)
            metadata = json.dumps({
                "judge": judge,
                "ground": ground_key,
                "finding_count": len(relevant),
                "separation_days": SEPARATION_DAYS_KEY if ground_key == "self_reinforcing" else None,
            })

            status = "active" if score >= 5.0 else "NEEDS_REVIEW"

            self._db_execute(
                """INSERT OR REPLACE INTO action_scores
                   (action_id, lane, evidence_score, authority_score,
                    vulnerability_score, readiness_score, composite_score,
                    gap_count, updated_by)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                (f"DISQUAL-{judge}-{ground_def['label'][:20]}",
                 "C", round(score, 2), 0.0,
                 0.0, 0.0, round(score, 2),
                 0, self.agent_id),
            )
        self.db.commit()
        self._log("INFO", f"Disqualification scoring complete for {judge}")

    # ------------------------------------------------------------------
    def _compute_ground_score(self, findings: list, ground_def: dict) -> float:
        """Cumulative score: weighted severity × count factor."""
        if not findings:
            return 0.0
        total_severity = sum(f["severity"] for f in findings)
        avg_severity = total_severity / len(findings)
        count_factor = min(2.0, 1.0 + len(findings) * 0.1)
        raw = avg_severity * ground_def["weight"] * count_factor
        return min(10.0, raw / ground_def["weight"])

    def _format_ground_detail(self, judge: str, ground_def: dict,
                              findings: list, score: float) -> str:
        lines = [
            f"DISQUALIFICATION ANALYSIS — {judge}",
            f"Ground: {ground_def['label']}",
            f"Score: {score:.2f}/10.0",
            f"Supporting findings: {len(findings)}",
            "",
        ]
        for f in findings[:10]:  # cap detail at 10
            lines.append(f"  • [{f['severity']}/10] {f['description']}")
        if len(findings) > 10:
            lines.append(f"  ... and {len(findings) - 10} more")
        return "\n".join(lines)
