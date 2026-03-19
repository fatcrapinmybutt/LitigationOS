"""
LitigationOS Finite State Machine — Litigation Workflow Orchestration
MBP LitigationOS 2026 v1.0 — THE MANBEARPIG System

Orchestrates six case lanes (A–F) through defined procedural states,
validates transitions against Michigan Court Rules, and infers current
state from the litigation_context.db.

Pigors v. Watson — Consolidated Case Matrix
"""

import json
import sqlite3
import os
import time
import logging
from dataclasses import dataclass, field, asdict
from typing import Optional

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger("LitigationFSM")

# ---------------------------------------------------------------------------
# State dataclass
# ---------------------------------------------------------------------------

@dataclass
class State:
    name: str
    description: str
    available_actions: list = field(default_factory=list)
    transitions: dict = field(default_factory=dict)
    mcr_authority: str = ""


# ---------------------------------------------------------------------------
# Lane definitions
# ---------------------------------------------------------------------------

def _build_lane_a() -> dict[str, State]:
    """Lane A — Custody 2024-001507-DC (14th Circuit, Muskegon County)."""
    return {
        "filing": State(
            name="filing",
            description="Initial filing / responsive pleading phase",
            available_actions=["serve_complaint", "file_answer", "begin_discovery"],
            transitions={
                "serve_complaint": "filing",
                "file_answer": "filing",
                "begin_discovery": "discovery",
            },
            mcr_authority="MCR 2.110 — Pleadings; MCR 2.105 — Service of Process",
        ),
        "discovery": State(
            name="discovery",
            description="Discovery phase — interrogatories, depositions, subpoenas",
            available_actions=["serve_interrogatories", "notice_deposition", "motion_to_compel", "request_foc"],
            transitions={
                "serve_interrogatories": "discovery",
                "notice_deposition": "discovery",
                "motion_to_compel": "motion_practice",
                "request_foc": "foc_investigation",
            },
            mcr_authority="MCR 2.302–2.316 — Discovery Rules",
        ),
        "foc_investigation": State(
            name="foc_investigation",
            description="Friend of the Court investigation / recommendation",
            available_actions=["submit_evidence", "object_to_recommendation", "accept_recommendation"],
            transitions={
                "submit_evidence": "foc_investigation",
                "object_to_recommendation": "motion_practice",
                "accept_recommendation": "hearing",
            },
            mcr_authority="MCL 552.505 — FOC Investigation; MCR 3.224",
        ),
        "motion_practice": State(
            name="motion_practice",
            description="Motions — compel, dismiss, summary disposition, etc.",
            available_actions=["file_motion", "file_response", "file_reply", "schedule_hearing"],
            transitions={
                "file_motion": "motion_practice",
                "file_response": "motion_practice",
                "file_reply": "motion_practice",
                "schedule_hearing": "hearing",
            },
            mcr_authority="MCR 2.119 — Motion Practice",
        ),
        "hearing": State(
            name="hearing",
            description="Scheduled hearing before the court",
            available_actions=["attend_hearing", "request_adjournment", "proceed_to_trial"],
            transitions={
                "attend_hearing": "hearing",
                "request_adjournment": "motion_practice",
                "proceed_to_trial": "trial_prep",
            },
            mcr_authority="MCR 2.119(E) — Hearing; MCR 2.501 — Scheduling",
        ),
        "trial_prep": State(
            name="trial_prep",
            description="Trial preparation — witness lists, exhibit lists, pretrial statements",
            available_actions=["file_witness_list", "file_exhibit_list", "file_pretrial_statement", "begin_trial"],
            transitions={
                "file_witness_list": "trial_prep",
                "file_exhibit_list": "trial_prep",
                "file_pretrial_statement": "trial_prep",
                "begin_trial": "trial",
            },
            mcr_authority="MCR 2.401 — Pretrial Procedures",
        ),
        "trial": State(
            name="trial",
            description="Trial proceedings — testimony, cross-examination, closing arguments",
            available_actions=["present_evidence", "cross_examine", "rest_case", "await_verdict"],
            transitions={
                "present_evidence": "trial",
                "cross_examine": "trial",
                "rest_case": "trial",
                "await_verdict": "post_trial",
            },
            mcr_authority="MCR 2.507–2.516 — Trial Procedures",
        ),
        "post_trial": State(
            name="post_trial",
            description="Post-trial motions, proposed orders, appeal decisions",
            available_actions=["file_post_trial_motion", "propose_order", "file_appeal"],
            transitions={
                "file_post_trial_motion": "post_trial",
                "propose_order": "enforcement",
                "file_appeal": "post_trial",
            },
            mcr_authority="MCR 2.611 — New Trial; MCR 2.612 — Relief from Judgment",
        ),
        "enforcement": State(
            name="enforcement",
            description="Order enforcement — contempt, show cause, compliance monitoring",
            available_actions=["file_show_cause", "motion_for_contempt", "monitor_compliance"],
            transitions={
                "file_show_cause": "enforcement",
                "motion_for_contempt": "enforcement",
                "monitor_compliance": "enforcement",
            },
            mcr_authority="MCR 3.606 — Contempt; MCL 600.1701",
        ),
    }


def _build_lane_b() -> dict[str, State]:
    """Lane B — Shady Oaks Housing."""
    return {
        "complaint": State(
            name="complaint",
            description="Initial housing complaint filing",
            available_actions=["draft_complaint", "file_complaint", "request_investigation"],
            transitions={
                "draft_complaint": "complaint",
                "file_complaint": "investigation",
                "request_investigation": "investigation",
            },
            mcr_authority="MCL 600.5701 — Summary Proceedings; MCR 4.201",
        ),
        "investigation": State(
            name="investigation",
            description="Investigation of housing conditions / violations",
            available_actions=["gather_evidence", "request_inspection", "escalate_to_mediation"],
            transitions={
                "gather_evidence": "investigation",
                "request_inspection": "investigation",
                "escalate_to_mediation": "mediation",
            },
            mcr_authority="MCR 2.302 — Discovery; MCL 125.534",
        ),
        "mediation": State(
            name="mediation",
            description="Mediation / alternative dispute resolution",
            available_actions=["attend_mediation", "reject_mediation", "accept_settlement"],
            transitions={
                "attend_mediation": "mediation",
                "reject_mediation": "hearing",
                "accept_settlement": "resolution",
            },
            mcr_authority="MCR 2.410 — Alternative Dispute Resolution",
        ),
        "hearing": State(
            name="hearing",
            description="Court hearing on housing matter",
            available_actions=["attend_hearing", "present_evidence", "await_ruling"],
            transitions={
                "attend_hearing": "hearing",
                "present_evidence": "hearing",
                "await_ruling": "resolution",
            },
            mcr_authority="MCR 4.201 — Summary Proceedings",
        ),
        "resolution": State(
            name="resolution",
            description="Final resolution — order entered, compliance period",
            available_actions=["enforce_order", "monitor_compliance", "close_lane"],
            transitions={
                "enforce_order": "resolution",
                "monitor_compliance": "resolution",
                "close_lane": "resolution",
            },
            mcr_authority="MCR 2.602 — Entry of Judgments and Orders",
        ),
    }


def _build_lane_c() -> dict[str, State]:
    """Lane C — Convergence (cross-lane coordination)."""
    return {
        "monitoring": State(
            name="monitoring",
            description="Passive monitoring of cross-lane interactions and dependencies",
            available_actions=["scan_lanes", "flag_conflict", "begin_coordination"],
            transitions={
                "scan_lanes": "monitoring",
                "flag_conflict": "coordination",
                "begin_coordination": "coordination",
            },
            mcr_authority="MCR 2.505 — Consolidation; MCR 3.204",
        ),
        "coordination": State(
            name="coordination",
            description="Active coordination between multiple lanes",
            available_actions=["synchronize_deadlines", "align_filings", "escalate"],
            transitions={
                "synchronize_deadlines": "coordination",
                "align_filings": "coordination",
                "escalate": "escalation",
            },
            mcr_authority="MCR 2.505 — Consolidation; MCR 8.111 — Assignment of Cases",
        ),
        "escalation": State(
            name="escalation",
            description="Escalated cross-lane conflict requiring immediate attention",
            available_actions=["file_emergency_motion", "seek_superintending_control", "resolve"],
            transitions={
                "file_emergency_motion": "escalation",
                "seek_superintending_control": "escalation",
                "resolve": "resolution",
            },
            mcr_authority="MCR 3.302 — Superintending Control; MCL 600.1701",
        ),
        "resolution": State(
            name="resolution",
            description="Cross-lane conflict resolved, return to monitoring",
            available_actions=["confirm_resolution", "resume_monitoring"],
            transitions={
                "confirm_resolution": "resolution",
                "resume_monitoring": "monitoring",
            },
            mcr_authority="MCR 2.602 — Entry of Judgments and Orders",
        ),
    }


def _build_lane_d() -> dict[str, State]:
    """Lane D — PPO 2023-5907-PP (14th Circuit, Muskegon County)."""
    return {
        "petition": State(
            name="petition",
            description="PPO petition filing or response phase",
            available_actions=["file_petition", "file_response", "request_hearing"],
            transitions={
                "file_petition": "petition",
                "file_response": "petition",
                "request_hearing": "hearing",
            },
            mcr_authority="MCL 600.2950 — PPO; MCR 3.705",
        ),
        "hearing": State(
            name="hearing",
            description="PPO hearing — testimony and evidence presentation",
            available_actions=["attend_hearing", "present_evidence", "await_ruling"],
            transitions={
                "attend_hearing": "hearing",
                "present_evidence": "hearing",
                "await_ruling": "order_issued",
            },
            mcr_authority="MCR 3.707 — PPO Hearing; MCL 600.2950(12)",
        ),
        "order_issued": State(
            name="order_issued",
            description="PPO order entered — compliance or challenge phase",
            available_actions=["comply", "file_modification", "file_appeal"],
            transitions={
                "comply": "enforcement",
                "file_modification": "modification",
                "file_appeal": "appeal",
            },
            mcr_authority="MCL 600.2950(8) — PPO Terms; MCR 3.706",
        ),
        "modification": State(
            name="modification",
            description="Motion to modify or dissolve PPO",
            available_actions=["file_motion_to_modify", "attend_hearing", "await_ruling"],
            transitions={
                "file_motion_to_modify": "modification",
                "attend_hearing": "hearing",
                "await_ruling": "order_issued",
            },
            mcr_authority="MCL 600.2950(11) — Modification; MCR 3.706",
        ),
        "appeal": State(
            name="appeal",
            description="Appeal of PPO order",
            available_actions=["file_claim_of_appeal", "prepare_brief", "await_decision"],
            transitions={
                "file_claim_of_appeal": "appeal",
                "prepare_brief": "appeal",
                "await_decision": "enforcement",
            },
            mcr_authority="MCR 7.204 — Claim of Appeal; MCR 7.205",
        ),
        "enforcement": State(
            name="enforcement",
            description="PPO enforcement — compliance monitoring, contempt if violated",
            available_actions=["report_violation", "file_contempt", "monitor_compliance"],
            transitions={
                "report_violation": "enforcement",
                "file_contempt": "enforcement",
                "monitor_compliance": "enforcement",
            },
            mcr_authority="MCL 600.2950(23) — PPO Violation; MCL 750.411h",
        ),
    }


def _build_lane_e() -> dict[str, State]:
    """Lane E — Judicial Misconduct (JTC / MSC)."""
    return {
        "investigation": State(
            name="investigation",
            description="Investigate judicial conduct — gather evidence, identify violations",
            available_actions=["review_record", "identify_violations", "begin_drafting"],
            transitions={
                "review_record": "investigation",
                "identify_violations": "investigation",
                "begin_drafting": "complaint_drafting",
            },
            mcr_authority="MCR 9.200 — Judicial Tenure Commission; Const 1963 Art 6 §30",
        ),
        "complaint_drafting": State(
            name="complaint_drafting",
            description="Draft formal misconduct complaint with supporting evidence",
            available_actions=["draft_complaint", "attach_exhibits", "finalize_complaint"],
            transitions={
                "draft_complaint": "complaint_drafting",
                "attach_exhibits": "complaint_drafting",
                "finalize_complaint": "filing",
            },
            mcr_authority="MCR 9.207 — Complaint; MI Code of Judicial Conduct",
        ),
        "filing": State(
            name="filing",
            description="File complaint with Judicial Tenure Commission",
            available_actions=["file_with_jtc", "file_supplemental", "await_review"],
            transitions={
                "file_with_jtc": "filing",
                "file_supplemental": "filing",
                "await_review": "review",
            },
            mcr_authority="MCR 9.211 — Filing; MCR 9.220",
        ),
        "review": State(
            name="review",
            description="JTC review / investigation period",
            available_actions=["respond_to_inquiry", "submit_additional_evidence", "await_determination"],
            transitions={
                "respond_to_inquiry": "review",
                "submit_additional_evidence": "review",
                "await_determination": "resolution",
            },
            mcr_authority="MCR 9.220–9.223 — JTC Proceedings",
        ),
        "resolution": State(
            name="resolution",
            description="JTC determination — discipline, dismissal, or referral to MSC",
            available_actions=["accept_determination", "appeal_to_msc", "close_lane"],
            transitions={
                "accept_determination": "resolution",
                "appeal_to_msc": "resolution",
                "close_lane": "resolution",
            },
            mcr_authority="MCR 9.224–9.225 — JTC Determination; Const 1963 Art 6 §30",
        ),
    }


def _build_lane_f() -> dict[str, State]:
    """Lane F — Appellate COA 366810 (Michigan Court of Appeals)."""
    return {
        "claim_filed": State(
            name="claim_filed",
            description="Claim of appeal filed — jurisdictional requirements met",
            available_actions=["verify_jurisdiction", "order_transcripts", "begin_record_prep"],
            transitions={
                "verify_jurisdiction": "claim_filed",
                "order_transcripts": "record_preparation",
                "begin_record_prep": "record_preparation",
            },
            mcr_authority="MCR 7.204 — Claim of Appeal; MCR 7.204(A) — Filing Deadline",
        ),
        "record_preparation": State(
            name="record_preparation",
            description="Lower court record preparation and transcript ordering",
            available_actions=["compile_record", "file_record_supplements", "begin_briefing"],
            transitions={
                "compile_record": "record_preparation",
                "file_record_supplements": "record_preparation",
                "begin_briefing": "brief_writing",
            },
            mcr_authority="MCR 7.210 — Record on Appeal; MCR 7.210(A)",
        ),
        "brief_writing": State(
            name="brief_writing",
            description="Appellate brief drafting — appellant's brief, reply brief",
            available_actions=["draft_appellant_brief", "file_appellant_brief", "draft_reply_brief", "file_reply_brief"],
            transitions={
                "draft_appellant_brief": "brief_writing",
                "file_appellant_brief": "brief_writing",
                "draft_reply_brief": "brief_writing",
                "file_reply_brief": "oral_argument",
            },
            mcr_authority="MCR 7.212 — Briefs; MCR 7.212(B) — Appellant's Brief",
        ),
        "oral_argument": State(
            name="oral_argument",
            description="Oral argument (if granted) or submission on briefs",
            available_actions=["prepare_argument", "attend_oral_argument", "submit_on_briefs", "await_decision"],
            transitions={
                "prepare_argument": "oral_argument",
                "attend_oral_argument": "oral_argument",
                "submit_on_briefs": "decision",
                "await_decision": "decision",
            },
            mcr_authority="MCR 7.214 — Oral Argument",
        ),
        "decision": State(
            name="decision",
            description="Court of Appeals decision issued",
            available_actions=["review_decision", "file_motion_for_recon", "apply_to_msc"],
            transitions={
                "review_decision": "decision",
                "file_motion_for_recon": "motion_for_recon",
                "apply_to_msc": "decision",
            },
            mcr_authority="MCR 7.215 — Opinions and Orders",
        ),
        "motion_for_recon": State(
            name="motion_for_recon",
            description="Motion for reconsideration of COA decision",
            available_actions=["draft_motion", "file_motion", "await_ruling"],
            transitions={
                "draft_motion": "motion_for_recon",
                "file_motion": "motion_for_recon",
                "await_ruling": "decision",
            },
            mcr_authority="MCR 7.215(I) — Motion for Reconsideration",
        ),
    }


# ---------------------------------------------------------------------------
# Lane metadata
# ---------------------------------------------------------------------------

LANE_META = {
    "A": {"label": "Custody", "case_number": "2024-001507-DC", "court": "14th Circuit Court, Muskegon County"},
    "B": {"label": "Housing", "case_number": "Shady Oaks", "court": "Related proceedings"},
    "C": {"label": "Convergence", "case_number": "MULTI", "court": "Cross-lane coordination"},
    "D": {"label": "PPO", "case_number": "2023-5907-PP", "court": "14th Circuit Court, Muskegon County"},
    "E": {"label": "Judicial Misconduct", "case_number": "MULTI", "court": "JTC / MSC"},
    "F": {"label": "Appellate", "case_number": "COA 366810", "court": "Michigan Court of Appeals"},
}

LANE_BUILDERS = {
    "A": _build_lane_a,
    "B": _build_lane_b,
    "C": _build_lane_c,
    "D": _build_lane_d,
    "E": _build_lane_e,
    "F": _build_lane_f,
}


# ---------------------------------------------------------------------------
# Finite State Machine
# ---------------------------------------------------------------------------

class LitigationFSM:
    """Finite-state machine orchestrating six litigation lanes (A–F)."""

    CACHE_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "cache")
    CACHE_FILE = os.path.join(CACHE_DIR, "litigation_fsm_state.json")

    def __init__(self, db_path: str = r"C:\Users\andre\LitigationOS\litigation_context.db"):
        self.db_path = db_path
        self.lanes: dict[str, dict[str, State]] = {}
        self.current_states: dict[str, str] = {}
        self.transition_log: list[dict] = []

        # Build every lane's state graph
        for lane_id, builder in LANE_BUILDERS.items():
            self.lanes[lane_id] = builder()

        # Set default starting state per lane
        self._defaults = {
            "A": "filing",
            "B": "complaint",
            "C": "monitoring",
            "D": "petition",
            "E": "investigation",
            "F": "claim_filed",
        }
        self.current_states = dict(self._defaults)

        # Try to infer actual current states from DB
        self._load_from_db()

        # Try to restore persisted cache (overrides DB inference if fresher)
        self._load_cache()

        logger.info("LitigationFSM initialized — lanes: %s", list(self.current_states.keys()))

    # ------------------------------------------------------------------
    # DB helpers
    # ------------------------------------------------------------------

    def _get_connection(self) -> Optional[sqlite3.Connection]:
        if not os.path.exists(self.db_path):
            logger.warning("Database not found at %s", self.db_path)
            return None
        try:
            conn = sqlite3.connect(self.db_path)
            conn.row_factory = sqlite3.Row
            return conn
        except sqlite3.Error as exc:
            logger.error("DB connection error: %s", exc)
            return None

    def _table_exists(self, conn: sqlite3.Connection, table: str) -> bool:
        cur = conn.execute(
            "SELECT 1 FROM sqlite_master WHERE type='table' AND name=?", (table,)
        )
        return cur.fetchone() is not None

    def _load_from_db(self):
        """Infer current state for each lane from DB tables."""
        conn = self._get_connection()
        if conn is None:
            return
        try:
            for lane_id in self.lanes:
                inferred = self._infer_current_state(lane_id, conn=conn)
                if inferred and inferred in self.lanes[lane_id]:
                    self.current_states[lane_id] = inferred
                    logger.info("Lane %s: inferred state → %s", lane_id, inferred)
        finally:
            conn.close()

    def _infer_current_state(self, lane: str, conn: sqlite3.Connection = None) -> Optional[str]:
        """Infer current state from docket_events, vehicles, and deadlines tables."""
        close_conn = False
        if conn is None:
            conn = self._get_connection()
            if conn is None:
                return None
            close_conn = True

        try:
            meta = LANE_META.get(lane, {})
            case_num = meta.get("case_number", "")
            label = meta.get("label", "").lower()
            state_names = list(self.lanes[lane].keys())

            # --- Check docket_events for the most recent event ----------
            if self._table_exists(conn, "docket_events"):
                try:
                    rows = conn.execute(
                        """SELECT title, event_type, summary
                           FROM docket_events
                           WHERE LOWER(title || ' ' || COALESCE(summary,''))
                                 LIKE ?
                           ORDER BY event_date_iso DESC
                           LIMIT 5""",
                        (f"%{label}%",),
                    ).fetchall()
                    if not rows:
                        rows = conn.execute(
                            """SELECT title, event_type, summary
                               FROM docket_events
                               WHERE LOWER(title || ' ' || COALESCE(summary,''))
                                     LIKE ?
                               ORDER BY event_date_iso DESC
                               LIMIT 5""",
                            (f"%{case_num.lower()}%",),
                        ).fetchall()
                    for row in rows:
                        blob = (
                            (row["title"] or "")
                            + " "
                            + (row["event_type"] or "")
                            + " "
                            + (row["summary"] or "")
                        ).lower()
                        for sname in reversed(state_names):
                            if sname.replace("_", " ") in blob or sname in blob:
                                return sname
                except sqlite3.Error:
                    pass

            # --- Check vehicles table -----------------------------------
            if self._table_exists(conn, "vehicles"):
                try:
                    rows = conn.execute(
                        """SELECT title, vehicle_type, status
                           FROM vehicles
                           WHERE LOWER(COALESCE(case_lane,'') || ' ' || COALESCE(title,''))
                                 LIKE ?
                           ORDER BY rowid DESC
                           LIMIT 5""",
                        (f"%{label}%",),
                    ).fetchall()
                    for row in rows:
                        blob = (
                            (row["title"] or "")
                            + " "
                            + (row["vehicle_type"] or "")
                            + " "
                            + (row["status"] or "")
                        ).lower()
                        for sname in reversed(state_names):
                            if sname.replace("_", " ") in blob or sname in blob:
                                return sname
                except sqlite3.Error:
                    pass

            # --- Check deadlines table ----------------------------------
            if self._table_exists(conn, "deadlines"):
                try:
                    rows = conn.execute(
                        """SELECT title, basis_authority
                           FROM deadlines
                           WHERE LOWER(COALESCE(title,''))
                                 LIKE ?
                           ORDER BY due_date_iso ASC
                           LIMIT 5""",
                        (f"%{label}%",),
                    ).fetchall()
                    for row in rows:
                        blob = (
                            (row["title"] or "")
                            + " "
                            + (row["basis_authority"] or "")
                        ).lower()
                        for sname in reversed(state_names):
                            if sname.replace("_", " ") in blob or sname in blob:
                                return sname
                except sqlite3.Error:
                    pass

            return None  # No inference possible
        finally:
            if close_conn:
                conn.close()

    # ------------------------------------------------------------------
    # Cache persistence
    # ------------------------------------------------------------------

    def _load_cache(self):
        if os.path.exists(self.CACHE_FILE):
            try:
                with open(self.CACHE_FILE, "r", encoding="utf-8") as fh:
                    data = json.load(fh)
                for lid, sname in data.get("current_states", {}).items():
                    if lid in self.lanes and sname in self.lanes[lid]:
                        self.current_states[lid] = sname
                self.transition_log = data.get("transition_log", [])
                logger.info("Loaded cached FSM state from %s", self.CACHE_FILE)
            except (json.JSONDecodeError, OSError) as exc:
                logger.warning("Cache load failed: %s", exc)

    def _save_cache(self):
        os.makedirs(self.CACHE_DIR, exist_ok=True)
        with open(self.CACHE_FILE, "w", encoding="utf-8") as fh:
            json.dump(
                {
                    "current_states": self.current_states,
                    "transition_log": self.transition_log[-200:],
                    "saved_at": time.strftime("%Y-%m-%dT%H:%M:%S"),
                },
                fh,
                indent=2,
            )

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def get_state(self, lane: str) -> dict:
        """Return the current state for *lane* with available transitions."""
        lane = lane.upper()
        if lane not in self.lanes:
            return {"error": f"Unknown lane: {lane}"}
        sname = self.current_states[lane]
        state = self.lanes[lane][sname]
        return {
            "lane": lane,
            "meta": LANE_META[lane],
            "current_state": asdict(state),
        }

    def transition(self, lane: str, action: str) -> dict:
        """Attempt a state transition. Returns new state or error."""
        lane = lane.upper()
        if lane not in self.lanes:
            return {"error": f"Unknown lane: {lane}"}
        sname = self.current_states[lane]
        state = self.lanes[lane][sname]

        if action not in state.transitions:
            return {
                "error": f"Illegal action '{action}' in state '{sname}' for lane {lane}",
                "available_actions": state.available_actions,
            }

        new_state = state.transitions[action]
        old_state = sname
        self.current_states[lane] = new_state

        entry = {
            "lane": lane,
            "from": old_state,
            "action": action,
            "to": new_state,
            "timestamp": time.strftime("%Y-%m-%dT%H:%M:%S"),
        }
        self.transition_log.append(entry)
        self._save_cache()

        logger.info("Lane %s: %s --%s--> %s", lane, old_state, action, new_state)
        return {
            "lane": lane,
            "previous_state": old_state,
            "action": action,
            "new_state": new_state,
            "available_actions": self.lanes[lane][new_state].available_actions,
        }

    def get_available_actions(self, lane: str) -> list:
        """Return valid actions from the current state of *lane*."""
        lane = lane.upper()
        if lane not in self.lanes:
            return []
        sname = self.current_states[lane]
        return list(self.lanes[lane][sname].available_actions)

    def get_all_states(self) -> dict:
        """Return all lanes with their current states."""
        result = {}
        for lane_id in self.lanes:
            sname = self.current_states[lane_id]
            state = self.lanes[lane_id][sname]
            result[lane_id] = {
                "meta": LANE_META[lane_id],
                "current_state": state.name,
                "description": state.description,
                "mcr_authority": state.mcr_authority,
                "available_actions": state.available_actions,
            }
        return result

    def get_deadlines(self, lane: str = None) -> list:
        """Pull deadlines from the DB, optionally filtered by lane."""
        conn = self._get_connection()
        if conn is None:
            return []
        try:
            if not self._table_exists(conn, "deadlines"):
                return []
            if lane:
                lane = lane.upper()
                label = LANE_META.get(lane, {}).get("label", "").lower()
                rows = conn.execute(
                    """SELECT title, due_date_iso, basis_authority, status
                       FROM deadlines
                       WHERE LOWER(COALESCE(title,'')) LIKE ?
                       ORDER BY due_date_iso ASC""",
                    (f"%{label}%",),
                ).fetchall()
            else:
                rows = conn.execute(
                    """SELECT title, due_date_iso, basis_authority, status
                       FROM deadlines
                       ORDER BY due_date_iso ASC""",
                ).fetchall()
            return [dict(r) for r in rows]
        except sqlite3.Error as exc:
            logger.error("Deadline query error: %s", exc)
            return []
        finally:
            conn.close()

    def get_next_actions(self) -> list:
        """Across ALL lanes, return prioritized next actions based on deadlines and state."""
        actions: list[dict] = []

        # Gather deadlines for urgency ranking
        deadlines = self.get_deadlines()
        deadline_map: dict[str, str] = {}
        for dl in deadlines:
            deadline_map[dl.get("title", "").lower()] = dl.get("due_date_iso", "9999-12-31")

        for lane_id, state_map in self.lanes.items():
            sname = self.current_states[lane_id]
            state = state_map[sname]
            meta = LANE_META[lane_id]

            # Find soonest matching deadline for this lane
            lane_label = meta["label"].lower()
            soonest = "9999-12-31"
            for key, due in deadline_map.items():
                if lane_label in key:
                    soonest = min(soonest, due)

            for act in state.available_actions:
                actions.append({
                    "lane": lane_id,
                    "lane_label": meta["label"],
                    "current_state": sname,
                    "action": act,
                    "next_state": state.transitions.get(act, sname),
                    "soonest_deadline": soonest,
                    "mcr_authority": state.mcr_authority,
                })

        # Sort by deadline (soonest first), then lane
        actions.sort(key=lambda a: (a["soonest_deadline"], a["lane"]))
        return actions

    def serialize(self) -> str:
        """JSON-serialize current FSM state for persistence."""
        payload = {
            "current_states": self.current_states,
            "transition_log": self.transition_log[-200:],
            "serialized_at": time.strftime("%Y-%m-%dT%H:%M:%S"),
        }
        return json.dumps(payload, indent=2)

    def load_state(self, state_json: str):
        """Load previously serialized state."""
        data = json.loads(state_json)
        for lid, sname in data.get("current_states", {}).items():
            if lid in self.lanes and sname in self.lanes[lid]:
                self.current_states[lid] = sname
        self.transition_log = data.get("transition_log", [])
        self._save_cache()
        logger.info("State loaded from JSON input")

    # ------------------------------------------------------------------
    # Self-test
    # ------------------------------------------------------------------

    def self_test(self) -> dict:
        """Initialize all lanes, show states, test transitions. Returns report."""
        report: dict = {"lanes": {}, "transitions_tested": 0, "errors": []}

        print("=" * 72)
        print("  LitigationFSM Self-Test — MBP LitigationOS 2026 v1.0")
        print("=" * 72)

        # 1. Show all current states
        all_states = self.get_all_states()
        for lid, info in all_states.items():
            print(f"\n  Lane {lid} ({info['meta']['label']}):")
            print(f"    State        : {info['current_state']}")
            print(f"    Description  : {info['description']}")
            print(f"    MCR Authority: {info['mcr_authority']}")
            print(f"    Actions      : {', '.join(info['available_actions'])}")
            report["lanes"][lid] = info

        # 2. Test one transition per lane (first available action)
        print("\n" + "-" * 72)
        print("  Transition Tests")
        print("-" * 72)

        # Save original states so we can restore
        saved = dict(self.current_states)

        for lid in self.lanes:
            actions = self.get_available_actions(lid)
            if not actions:
                report["errors"].append(f"Lane {lid}: no available actions")
                continue
            action = actions[0]
            result = self.transition(lid, action)
            if "error" in result:
                msg = f"Lane {lid}: transition '{action}' failed — {result['error']}"
                print(f"  ✗ {msg}")
                report["errors"].append(msg)
            else:
                print(
                    f"  ✓ Lane {lid}: {result['previous_state']} "
                    f"--{result['action']}--> {result['new_state']}"
                )
                report["transitions_tested"] += 1

        # 3. Test illegal transition
        print("\n  Testing illegal transition (Lane A, 'nonexistent_action')...")
        bad = self.transition("A", "nonexistent_action")
        if "error" in bad:
            print(f"  ✓ Correctly rejected: {bad['error']}")
        else:
            msg = "Lane A: illegal transition was not rejected!"
            print(f"  ✗ {msg}")
            report["errors"].append(msg)

        # Restore original states
        self.current_states = saved
        self._save_cache()

        # 4. Test serialize / load round-trip
        print("\n  Testing serialize → load round-trip...")
        blob = self.serialize()
        self.load_state(blob)
        if self.current_states == saved:
            print("  ✓ Round-trip successful")
        else:
            msg = "Serialize/load round-trip mismatch"
            print(f"  ✗ {msg}")
            report["errors"].append(msg)

        # 5. Deadlines
        print("\n  Checking deadlines from DB...")
        dls = self.get_deadlines()
        print(f"  Found {len(dls)} deadline(s)")

        # 6. Next actions
        print("\n  Prioritized next actions (top 5):")
        for act in self.get_next_actions()[:5]:
            print(
                f"    Lane {act['lane']} ({act['lane_label']}): "
                f"{act['action']} → {act['next_state']}  "
                f"[deadline: {act['soonest_deadline']}]"
            )

        # Summary
        print("\n" + "=" * 72)
        err_count = len(report["errors"])
        if err_count == 0:
            print(f"  PASS — {report['transitions_tested']} transitions tested, 0 errors")
        else:
            print(f"  FAIL — {report['transitions_tested']} transitions tested, {err_count} error(s)")
            for e in report["errors"]:
                print(f"    • {e}")
        print("=" * 72)

        return report


# ---------------------------------------------------------------------------
# CLI entry point
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    fsm = LitigationFSM()
    fsm.self_test()
