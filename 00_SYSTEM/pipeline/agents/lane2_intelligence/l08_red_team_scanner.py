"""
DELTA9 — L08 Red Team Scanner
Tier L · Lane 2 Intelligence · MAX LEVEL 9999++

For each top-10 priority filing (highest composite scores):
  1. Simulate opposing counsel attacks
  2. Simulate judge skepticism
  3. Simulate appellate review
Inserts red_team_finding atoms for each vulnerability found.

GUARD: Never weakens filings — only identifies weaknesses for strengthening.
"""
import json
import hashlib
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

# Merge for name lookups
ALL_ACTIONS: Dict[str, dict] = {}
ALL_ACTIONS.update({k: {**v, "lane": "A"} for k, v in LANE_A_ACTIONS.items()})
ALL_ACTIONS.update({k: {**v, "lane": "B"} for k, v in LANE_B_ACTIONS.items()})
ALL_ACTIONS.update({k: {**v, "lane": "C"} for k, v in LANE_C_ACTIONS.items()})

# Standards of review for appellate simulation
STANDARDS_OF_REVIEW = {
    "factual_finding":      "Clear error",
    "discretionary_ruling": "Abuse of discretion",
    "legal_question":       "De novo",
    "mixed_question":       "De novo for legal, clear error for factual",
    "constitutional":       "De novo",
}

# Common procedural defenses
PROCEDURAL_DEFENSES = [
    "statute_of_limitations",
    "failure_to_exhaust_administrative_remedies",
    "lack_of_standing",
    "improper_venue",
    "failure_to_state_a_claim",
    "qualified_immunity",
    "judicial_immunity",
    "res_judicata",
    "collateral_estoppel",
    "laches",
]


class RedTeamScanner(Agent9999):
    """Red-team the top-10 priority filings to identify vulnerabilities."""

    def __init__(self):
        super().__init__(agent_id="L08-RED-TEAM")
        self.parallel_workers = 4   # I/O bound — parallelize file reads
        self.item_timeout = 15      # skip files that take >15s to read
        self.checkpoint_interval = 200

    def _validate_preconditions(self) -> None:
        for tbl in ("atoms", "action_scores"):
            cursor = self._db_execute(
                "SELECT name FROM sqlite_master WHERE type='table' AND name=?", (tbl,)
            )
            if not cursor.fetchone():
                raise FatalAgentError(f"Required table '{tbl}' missing — run readiness agent first")

    def _ensure_tables(self) -> None:
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
        """Get top-10 priority filings by composite score."""
        rows = self._db_execute(
            "SELECT action_id, lane, composite_score, evidence_score, authority_score, "
            "vulnerability_score, gap_count FROM action_scores "
            "ORDER BY composite_score DESC LIMIT 10"
        ).fetchall()
        return list(rows)

    def _process_item(self, item: Any) -> None:
        action_id = item["action_id"]
        lane = item["lane"]
        composite = float(item["composite_score"] or 0)
        evidence = float(item["evidence_score"] or 0)
        authority = float(item["authority_score"] or 0)
        gap_count = int(item["gap_count"] or 0)

        action = ALL_ACTIONS.get(action_id, {"name": action_id, "required": [], "lane": lane})

        # === 1. OPPOSING COUNSEL ATTACK SIMULATION ===
        self._simulate_opposing_counsel(action_id, lane, action, evidence, authority, gap_count)

        # === 2. JUDGE SKEPTICISM SIMULATION ===
        self._simulate_judge_skepticism(action_id, lane, action, evidence, authority)

        # === 3. APPELLATE REVIEW SIMULATION ===
        self._simulate_appellate_review(action_id, lane, action, composite)

    # ------------------------------------------------------------------
    # 1. Opposing Counsel Attacks
    # ------------------------------------------------------------------
    def _simulate_opposing_counsel(self, action_id: str, lane: str,
                                   action: dict, evidence: float,
                                   authority: float, gap_count: int) -> None:
        findings: List[Dict] = []

        # Weakest evidence check
        if evidence < 50.0:
            findings.append({
                "attack_type": "weak_evidence",
                "severity": "HIGH",
                "detail": f"Evidence score {evidence:.1f}/100 — opposing counsel will move for "
                          f"summary disposition arguing insufficient facts",
                "recommendation": "Strengthen with sworn affidavits or documentary evidence",
            })

        # Citation challenge check
        if authority < 40.0:
            findings.append({
                "attack_type": "citation_challenge",
                "severity": "MEDIUM",
                "detail": f"Authority score {authority:.1f}/100 — citations may be challenged as "
                          f"inapplicable or distinguishable",
                "recommendation": "Add on-point case law and binding authority",
            })

        # Gap-based attacks
        if gap_count > 0:
            missing = action.get("required", [])[-gap_count:] if gap_count <= len(action.get("required", [])) else action.get("required", [])
            findings.append({
                "attack_type": "element_gaps",
                "severity": "HIGH" if gap_count > 2 else "MEDIUM",
                "detail": f"{gap_count} required elements potentially unsupported: {missing}",
                "recommendation": "Acquire evidence for each missing element before filing",
            })

        # Procedural defense scan
        applicable_defenses = self._check_procedural_defenses(action_id, lane, action)
        if applicable_defenses:
            findings.append({
                "attack_type": "procedural_defense",
                "severity": "HIGH",
                "detail": f"Potential procedural defenses: {applicable_defenses}",
                "recommendation": "Pre-emptively address each defense in complaint/motion",
            })

        for finding in findings:
            self._insert_finding(action_id, lane, "opposing_counsel", finding)

    def _check_procedural_defenses(self, action_id: str, lane: str,
                                   action: dict) -> List[str]:
        """Identify procedural defenses likely to be raised."""
        applicable = []
        action_name = action.get("name", "").lower()

        # §1983 actions face qualified/judicial immunity
        if "1983" in action_name or action_id in ("A35", "C1", "C2", "C3", "C4"):
            applicable.append("qualified_immunity")
            if "judicial" in action_name:
                applicable.append("judicial_immunity")

        # All actions face SOL defense
        applicable.append("statute_of_limitations")

        # Housing actions face exhaustion defense
        if lane == "B":
            applicable.append("failure_to_exhaust_administrative_remedies")

        return applicable

    # ------------------------------------------------------------------
    # 2. Judge Skepticism
    # ------------------------------------------------------------------
    def _simulate_judge_skepticism(self, action_id: str, lane: str,
                                   action: dict, evidence: float,
                                   authority: float) -> None:
        findings: List[Dict] = []

        # Claims lacking sufficient evidence
        if evidence < 60.0:
            findings.append({
                "attack_type": "insufficient_evidence",
                "severity": "HIGH",
                "detail": f"Judge may find evidence insufficient at {evidence:.1f}/100 — "
                          f"risk of sua sponte dismissal or directed verdict",
                "recommendation": "Build evidentiary record with admissible documents and testimony",
            })

        # Novel vs established arguments
        novel_indicators = {"pattern & practice", "systemic", "conspiracy", "monell"}
        action_name = action.get("name", "").lower()
        is_novel = any(ind in action_name for ind in novel_indicators)
        if is_novel and authority < 60.0:
            findings.append({
                "attack_type": "novel_argument",
                "severity": "MEDIUM",
                "detail": f"'{action['name']}' involves novel legal theory with authority "
                          f"score {authority:.1f}/100 — judge may be skeptical",
                "recommendation": "Cite analogous cases from other jurisdictions, "
                                  "law review articles, and persuasive authority",
            })

        # Credibility concerns (allegations without sworn support)
        unsworn_count = 0
        try:
            row = self._db_execute(
                "SELECT COUNT(*) FROM atoms WHERE meek_lane LIKE ? AND "
                "(posture='ALLEGATION' OR posture='INFERENCE')",
                (f"%{lane}%",)
            ).fetchone()
            unsworn_count = row[0] if row else 0
        except Exception:
            pass

        sworn_count = 0
        try:
            row = self._db_execute(
                "SELECT COUNT(*) FROM atoms WHERE meek_lane LIKE ? AND "
                "posture IN ('SWORN_FACT','RECORD_FACT')",
                (f"%{lane}%",)
            ).fetchone()
            sworn_count = row[0] if row else 0
        except Exception:
            pass

        if unsworn_count > sworn_count * 2 and unsworn_count > 5:
            findings.append({
                "attack_type": "credibility_gap",
                "severity": "MEDIUM",
                "detail": f"Unsworn claims ({unsworn_count}) far exceed sworn facts ({sworn_count}) — "
                          f"judge may discount unsupported allegations",
                "recommendation": "Convert key allegations to sworn affidavits",
            })

        for finding in findings:
            self._insert_finding(action_id, lane, "judge_skepticism", finding)

    # ------------------------------------------------------------------
    # 3. Appellate Review
    # ------------------------------------------------------------------
    def _simulate_appellate_review(self, action_id: str, lane: str,
                                   action: dict, composite: float) -> None:
        findings: List[Dict] = []
        action_name = action.get("name", "").lower()

        # Issue preservation check
        findings.append({
            "attack_type": "issue_preservation",
            "severity": "LOW",
            "detail": "Ensure all issues are properly preserved: contemporaneous objection, "
                      "motion for reconsideration, or included in proposed findings",
            "recommendation": "Create issue-preservation checklist for this action",
        })

        # Standard of review
        if "constitutional" in action_name or "1983" in action_name or "civil rights" in action_name:
            standard = STANDARDS_OF_REVIEW["constitutional"]
        elif "discretion" in action_name or "custody" in action_name or "parenting" in action_name:
            standard = STANDARDS_OF_REVIEW["discretionary_ruling"]
        elif "fact" in action_name or "evidence" in action_name:
            standard = STANDARDS_OF_REVIEW["factual_finding"]
        else:
            standard = STANDARDS_OF_REVIEW["legal_question"]

        findings.append({
            "attack_type": "standard_of_review",
            "severity": "INFO",
            "detail": f"Applicable standard of review: {standard}",
            "recommendation": f"Frame arguments to survive '{standard}' review on appeal",
        })

        # Weak composite = harder to defend on appeal
        if composite < 50.0:
            findings.append({
                "attack_type": "appellate_risk",
                "severity": "MEDIUM",
                "detail": f"Composite score {composite:.1f}/100 — if adverse ruling, "
                          f"reversal unlikely without strong legal error argument",
                "recommendation": "Strengthen record now to preserve appellate options",
            })

        for finding in findings:
            self._insert_finding(action_id, lane, "appellate_review", finding)

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------
    def _insert_finding(self, action_id: str, lane: str,
                        simulation_type: str, finding: Dict) -> None:
        payload = json.dumps({
            "action_id": action_id,
            "lane": lane,
            "simulation": simulation_type,
            **finding,
        })
        self._db_execute(
            """INSERT OR IGNORE INTO atoms (id, atom_type, source_file_id, meek_lane, content, confidence, posture, created_by)
               VALUES (?, 'red_team_finding', 0, ?, ?, 1.0, 'SYSTEM', ?)""",
            (hashlib.sha1(f'L08|rt|{action_id}|{simulation_type}'.encode()).hexdigest()[:16],
             lane, payload, f'L08-RED-TEAM/{action_id}/{simulation_type}')
        )
        self.db.commit()

    def _finalize(self) -> None:
        total = self._db_execute(
            "SELECT COUNT(*) FROM atoms WHERE atom_type='red_team_finding'"
        ).fetchone()[0]
        high = self._db_execute(
            "SELECT COUNT(*) FROM atoms WHERE atom_type='red_team_finding' AND content LIKE '%\"severity\": \"HIGH\"%'"
        ).fetchone()[0]
        self._log("SUMMARY", f"Red team findings: {total} total, {high} HIGH severity")
        self._log("GUARD", "Red team scan complete — findings are for STRENGTHENING only")
