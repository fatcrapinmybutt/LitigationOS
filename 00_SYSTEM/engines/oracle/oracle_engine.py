#!/usr/bin/env python3
"""
ORACLE — Michigan Rule Reasoning Engine

Given a filing type + court + case lane → returns:
  1. Complete checklist of requirements (rules, forms, deadlines, service, content)
  2. Computed deadlines from a reference date
  3. Required SCAO forms with descriptions
  4. Service requirements
  5. Cross-referenced rules with explanations
  6. Known pitfalls and tips

Sits on top of LEXICON and the procedures/litigation-context databases,
providing intelligent procedural guidance for Michigan family-law filings.

Usage:
    from oracle.oracle_engine import Oracle
    oracle = Oracle()
    roadmap = oracle.get_roadmap("motion_to_modify_custody", "14th_circuit_family", lane="A")
    deadlines = oracle.compute_deadlines("motion_filing", hearing_date="2026-04-15")
    checklist = oracle.get_checklist("motion_to_disqualify_judge")

CLI:
    python oracle_engine.py roadmap motion_to_modify_custody 14th_circuit_family --lane A
    python oracle_engine.py deadlines motion_filing --date 2026-04-15
    python oracle_engine.py checklist motion_to_disqualify_judge
    python oracle_engine.py forms application_for_leave michigan_coa
    python oracle_engine.py service motion_to_modify_custody 14th_circuit_family
    python oracle_engine.py risks motion_to_modify_custody 14th_circuit_family --lane A
    python oracle_engine.py lane A
"""

import sys
import os
import json
import sqlite3
import argparse
import logging
from datetime import date, timedelta
from pathlib import Path
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)

# Import the deadline calculator from the same package
try:
    from oracle.deadlines import DeadlineCalculator, MichiganCalendar
except ImportError:
    # Allow direct execution from the oracle/ directory
    _this_dir = Path(__file__).resolve().parent
    if str(_this_dir) not in sys.path:
        sys.path.insert(0, str(_this_dir))
    from deadlines import DeadlineCalculator, MichiganCalendar

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------

_REPO_ROOT = Path(__file__).resolve().parents[3]
_LEXICON_DB = _REPO_ROOT / "databases" / "lexicon.db"
_PROCEDURES_DB = _REPO_ROOT / "databases" / "procedures.db"
_LITIGATION_DB = _REPO_ROOT / "litigation_context.db"

# ---------------------------------------------------------------------------
# Verified Lane Data (HARDCODED — never fabricate)
# ---------------------------------------------------------------------------

_LANE_INFO: Dict[str, Dict[str, Any]] = {
    "A": {
        "lane": "A",
        "description": "Watson custody",
        "case_number": "2024-001507-DC",
        "court": "14th Circuit Court, Family Division",
        "judge": "Hon. Jenny L. McNeill",
        "opposing_party": "Emily A. Watson",
        "opposing_counsel": "Jennifer Barnes (P55406) — WITHDREW",
        "foc": "Pamela Rusco",
    },
    "B": {
        "lane": "B",
        "description": "Shady Oaks housing",
        "case_number": "2025-002760-CZ",
        "court": "14th Circuit Court, Civil Division",
        "judge": "[VERIFY — not yet assigned or confirmed]",
        "opposing_party": "Shady Oaks / Housing",
        "opposing_counsel": "[VERIFY]",
        "foc": "N/A",
    },
    "C": {
        "lane": "C",
        "description": "Convergence (cross-lane)",
        "case_number": "Multi-lane",
        "court": "Multiple",
        "judge": "Multiple",
        "opposing_party": "Multiple",
        "opposing_counsel": "Multiple",
        "foc": "N/A",
    },
    "D": {
        "lane": "D",
        "description": "PPO / Protection Orders",
        "case_number": "2023-5907-PP",
        "court": "14th Circuit Court, Family Division",
        "judge": "Hon. Jenny L. McNeill",
        "opposing_party": "Emily A. Watson",
        "opposing_counsel": "[VERIFY]",
        "foc": "N/A",
    },
    "E": {
        "lane": "E",
        "description": "Judicial Misconduct / JTC",
        "case_number": "[JTC complaint — no circuit case number]",
        "court": "Judicial Tenure Commission",
        "judge": "Hon. Jenny L. McNeill (subject)",
        "opposing_party": "N/A",
        "opposing_counsel": "N/A",
        "foc": "N/A",
    },
    "F": {
        "lane": "F",
        "description": "Appellate (COA/MSC)",
        "case_number": "COA 366810",
        "court": "Michigan Court of Appeals",
        "judge": "[Panel TBD]",
        "opposing_party": "Emily A. Watson",
        "opposing_counsel": "[VERIFY]",
        "foc": "N/A",
    },
}

# ---------------------------------------------------------------------------
# Filing-type knowledge base (procedural rules)
# ---------------------------------------------------------------------------

_FILING_KNOWLEDGE: Dict[str, Dict[str, Any]] = {
    "motion_to_modify_custody": {
        "display_name": "Motion to Modify Custody / Parenting Time",
        "primary_rules": ["MCR 2.119", "MCR 3.206", "MCR 3.211"],
        "forms": [
            {"form_number": "MC 12", "title": "Proof of Service", "required": True,
             "notes": "Must be completed for all served documents"},
            {"form_number": "FOC 89", "title": "Verified Statement", "required": True,
             "notes": "Required for all custody/parenting-time motions — MCR 3.206(A)"},
            {"form_number": "MC 20", "title": "Fee Waiver Request", "required": False,
             "notes": "If unable to pay filing fee"},
        ],
        "checklist": [
            {"step": 1, "action": "Draft motion per MCR 2.119(A) with supporting brief",
             "rule": "MCR 2.119(A)", "required": True},
            {"step": 2, "action": "Complete FOC 89 Verified Statement",
             "rule": "MCR 3.206(A)", "required": True},
            {"step": 3, "action": "Prepare Notice of Hearing (schedule with clerk)",
             "rule": "MCR 2.119(C)", "required": True},
            {"step": 4, "action": "Prepare Proposed Order",
             "rule": "MCR 2.602", "required": True},
            {"step": 5, "action": "Prepare supporting affidavit with exhibits",
             "rule": "MCR 2.119(B)", "required": True},
            {"step": 6, "action": "File with court clerk (e-file via MiFILE)",
             "rule": "MCR 1.109", "required": True},
            {"step": 7, "action": "Serve opposing party (9 days + 3 if by mail)",
             "rule": "MCR 2.107", "required": True},
            {"step": 8, "action": "Provide FOC copy of all filed documents",
             "rule": "MCR 3.203", "required": True},
            {"step": 9, "action": "File Proof of Service (MC 12)",
             "rule": "MCR 2.107(D)", "required": True},
            {"step": 10, "action": "Prepare for hearing — review response brief if filed",
             "rule": "MCR 2.119(C)(2)", "required": False},
        ],
        "service": {
            "method": "Personal service or mail per MCR 2.107",
            "timing": "At least 9 days before hearing (12 if by mail)",
            "proof_form": "MC 12",
            "notes": "If served by mail, add 3 days per MCR 2.107(C)(3). "
                     "Serve FOC separately per MCR 3.203.",
        },
        "pitfalls": [
            {"risk": "Missing FOC 89 Verified Statement",
             "severity": "high",
             "mitigation": "Always attach FOC 89 — court will reject without it"},
            {"risk": "Insufficient service time",
             "severity": "high",
             "mitigation": "Serve at least 12 days before hearing (9 + 3 mail days)"},
            {"risk": "No proper-cause / change-of-circumstances showing",
             "severity": "high",
             "mitigation": "Brief must establish proper cause or change of circumstances under MCL 722.27(1)(c)"},
            {"risk": "Forgetting to serve FOC",
             "severity": "medium",
             "mitigation": "FOC must receive copies per MCR 3.203"},
            {"risk": "Missing proposed order",
             "severity": "medium",
             "mitigation": "Judges expect a proposed order — submit with motion"},
        ],
        "tips": [
            "Schedule hearing BEFORE filing — you need the date for the Notice of Hearing",
            "E-file via MiFILE; keep confirmation as proof of filing",
            "If pro se, bring extra copies of everything to the hearing",
            "Best-interest factors (MCL 722.23) must be addressed for custody change",
            "If emergency, consider ex parte motion under MCR 3.207",
        ],
        "cross_references": [
            {"rule": "MCL 722.23", "description": "Child custody best-interest factors"},
            {"rule": "MCL 722.27", "description": "Custody modification standards"},
            {"rule": "MCR 3.207", "description": "Emergency/ex parte custody orders"},
            {"rule": "MCR 2.602", "description": "Proposed judgments and orders"},
        ],
        "deadline_trigger": "motion_hearing",
        "fee": {"amount": "$20.00 (motion fee)", "waiver": "MC 20"},
        "format": [
            "Caption must include case number and parties per MCR 2.113",
            "Double-spaced, 12-point font",
            "Page limit: 20 pages for brief per LCR (check local rules)",
        ],
    },
    "motion_to_disqualify_judge": {
        "display_name": "Motion for Disqualification of Judge",
        "primary_rules": ["MCR 2.003"],
        "forms": [
            {"form_number": "MC 12", "title": "Proof of Service", "required": True,
             "notes": "Serve on all parties and the judge's clerk"},
        ],
        "checklist": [
            {"step": 1, "action": "Draft motion citing specific MCR 2.003(C) grounds",
             "rule": "MCR 2.003(C)", "required": True},
            {"step": 2, "action": "Prepare supporting affidavit with specific facts showing bias",
             "rule": "MCR 2.003(D)", "required": True},
            {"step": 3, "action": "File with court clerk",
             "rule": "MCR 1.109", "required": True},
            {"step": 4, "action": "Serve all parties",
             "rule": "MCR 2.107", "required": True},
            {"step": 5, "action": "Judge must decide within 14 days or it is deemed denied",
             "rule": "MCR 2.003(D)(3)", "required": False},
            {"step": 6, "action": "If denied, preserve error for appeal — file timely objection",
             "rule": "MCR 2.003(D)(4)", "required": False},
        ],
        "service": {
            "method": "Service on all parties per MCR 2.107",
            "timing": "File as soon as grounds are discovered",
            "proof_form": "MC 12",
            "notes": "Motion must be filed at earliest practicable moment after discovering "
                     "the grounds. Delay can be construed as waiver.",
        },
        "pitfalls": [
            {"risk": "Vague or conclusory allegations of bias",
             "severity": "high",
             "mitigation": "Affidavit must contain specific facts — not legal conclusions"},
            {"risk": "Untimely filing (waiver)",
             "severity": "high",
             "mitigation": "File at earliest opportunity after learning of bias — delay = waiver"},
            {"risk": "Judge decides own motion (no referral)",
             "severity": "medium",
             "mitigation": "Under MCR 2.003(D)(1), judge may decide the motion — if denied, "
                           "appeal under MCR 2.003(D)(4)"},
        ],
        "tips": [
            "MCR 2.003(C)(1) grounds: personal bias or prejudice",
            "Keep a log of every biased ruling with date, context, and transcript page",
            "The chief judge may reassign under MCR 2.003(B) even without a motion",
            "Preserve the record — failure to object below waives the issue on appeal",
        ],
        "cross_references": [
            {"rule": "MCR 2.003(B)", "description": "Sua sponte disqualification by chief judge"},
            {"rule": "MCR 2.003(C)", "description": "Grounds for disqualification"},
            {"rule": "MCR 2.003(D)", "description": "Procedure for disqualification motion"},
            {"rule": "Const 1963, art 6, § 8", "description": "Constitutional due process"},
        ],
        "deadline_trigger": "motion_hearing",
        "fee": {"amount": "$20.00 (motion fee)", "waiver": "MC 20"},
        "format": [
            "Caption must include case number per MCR 2.113",
            "Affidavit must be sworn under penalty of perjury",
        ],
    },
    "application_for_leave": {
        "display_name": "Application for Leave to Appeal (COA)",
        "primary_rules": ["MCR 7.205", "MCR 7.212"],
        "forms": [
            {"form_number": "MC 12", "title": "Proof of Service", "required": True,
             "notes": "Serve appellee within rules"},
        ],
        "checklist": [
            {"step": 1, "action": "Order lower-court record and transcripts",
             "rule": "MCR 7.210(B)", "required": True},
            {"step": 2, "action": "Draft application per MCR 7.205(B) requirements",
             "rule": "MCR 7.205(B)", "required": True},
            {"step": 3, "action": "Include orders appealed from (certified copies)",
             "rule": "MCR 7.205(B)(3)", "required": True},
            {"step": 4, "action": "Prepare supporting brief and appendix",
             "rule": "MCR 7.212", "required": True},
            {"step": 5, "action": "File with COA clerk within 21 days of order",
             "rule": "MCR 7.205(A)", "required": True},
            {"step": 6, "action": "Serve appellee",
             "rule": "MCR 7.205", "required": True},
            {"step": 7, "action": "File proof of service",
             "rule": "MCR 7.205", "required": True},
        ],
        "service": {
            "method": "Service per MCR 7.205 (mail or personal)",
            "timing": "Concurrent with filing",
            "proof_form": "MC 12",
            "notes": "Serve on appellee and any other parties to the appeal.",
        },
        "pitfalls": [
            {"risk": "Missing 21-day deadline",
             "severity": "critical",
             "mitigation": "File within 21 days — late applications require showing of good cause"},
            {"risk": "Missing certified copy of order",
             "severity": "high",
             "mitigation": "Include certified copy of each order appealed from"},
            {"risk": "Failing to explain why leave should be granted",
             "severity": "high",
             "mitigation": "Brief must explain why review is needed — not just that the ruling was wrong"},
        ],
        "tips": [
            "COA filing is ELECTRONIC via TrueFiling",
            "Application must include statement of questions presented",
            "If 21 days have passed, file motion for late application with good-cause explanation",
            "Include table of authorities in supporting brief",
        ],
        "cross_references": [
            {"rule": "MCR 7.204", "description": "Appeal of right (alternative to leave)"},
            {"rule": "MCR 7.210", "description": "Record on appeal"},
            {"rule": "MCR 7.212", "description": "Briefs on appeal"},
            {"rule": "MCR 7.215", "description": "Opinions and orders of COA"},
        ],
        "deadline_trigger": "leave_to_appeal_coa",
        "fee": {"amount": "$375.00 (COA filing fee)", "waiver": "MC 20"},
        "format": [
            "COA requires electronic filing via TrueFiling",
            "Brief: double-spaced, proportional 14-point or monospaced 12-point font",
            "50-page limit for appellant brief per MCR 7.212(B)",
        ],
    },
    "contempt_motion": {
        "display_name": "Motion for Contempt / Order to Show Cause",
        "primary_rules": ["MCR 3.606", "MCR 2.119"],
        "forms": [
            {"form_number": "MC 12", "title": "Proof of Service", "required": True,
             "notes": "Personal service strongly preferred for contempt"},
            {"form_number": "FOC 1", "title": "Order to Show Cause", "required": True,
             "notes": "Must be signed by judge before service"},
        ],
        "checklist": [
            {"step": 1, "action": "Draft motion identifying specific court order violated",
             "rule": "MCR 3.606", "required": True},
            {"step": 2, "action": "Draft supporting affidavit with specific violations",
             "rule": "MCR 3.606", "required": True},
            {"step": 3, "action": "Prepare proposed Order to Show Cause",
             "rule": "MCR 3.606", "required": True},
            {"step": 4, "action": "File with court and obtain signed Order to Show Cause",
             "rule": "MCR 3.606", "required": True},
            {"step": 5, "action": "Personally serve respondent with signed Order to Show Cause",
             "rule": "MCR 2.105", "required": True},
            {"step": 6, "action": "File Proof of Service (MC 12)",
             "rule": "MCR 2.107(D)", "required": True},
        ],
        "service": {
            "method": "Personal service STRONGLY preferred (MCR 2.105)",
            "timing": "At least 14 days before show-cause hearing (conservative)",
            "proof_form": "MC 12",
            "notes": "Contempt can result in jail — due process requires reliable service. "
                     "Personal service is the safest method.",
        },
        "pitfalls": [
            {"risk": "Serving unsigned Order to Show Cause",
             "severity": "critical",
             "mitigation": "Order MUST be signed by judge before service"},
            {"risk": "Serving by mail only",
             "severity": "high",
             "mitigation": "Use personal service — contempt involves potential jailing"},
            {"risk": "Vague identification of order violated",
             "severity": "high",
             "mitigation": "Quote the exact order language violated and cite the specific date/docket entry"},
        ],
        "tips": [
            "Attach a copy of the violated order as an exhibit",
            "Be specific: date, time, and nature of each violation",
            "If chronic violations, create a chronological chart of each incident",
            "Consider requesting make-up parenting time as remedy",
        ],
        "cross_references": [
            {"rule": "MCL 600.1701", "description": "Contempt power of courts"},
            {"rule": "MCR 3.208", "description": "FOC contempt proceedings"},
            {"rule": "MCR 2.105", "description": "Personal service requirements"},
        ],
        "deadline_trigger": "contempt",
        "fee": {"amount": "$20.00 (motion fee)", "waiver": "MC 20"},
        "format": [
            "Caption must include case number per MCR 2.113",
            "Affidavit: sworn under penalty of perjury, notarized",
        ],
    },
    "foc_objection": {
        "display_name": "Objection to FOC Recommendation",
        "primary_rules": ["MCL 552.507", "MCR 3.218"],
        "forms": [
            {"form_number": "FOC 78", "title": "Objection to Referee/FOC Recommendation",
             "required": True, "notes": "Standard objection form"},
            {"form_number": "MC 12", "title": "Proof of Service", "required": True,
             "notes": "Serve opposing party and FOC"},
        ],
        "checklist": [
            {"step": 1, "action": "Review FOC recommendation thoroughly",
             "rule": "MCL 552.507", "required": True},
            {"step": 2, "action": "File written objection within 21 days",
             "rule": "MCL 552.507(5)", "required": True},
            {"step": 3, "action": "Request de novo hearing in objection",
             "rule": "MCR 3.218(D)", "required": True},
            {"step": 4, "action": "Serve opposing party and FOC",
             "rule": "MCR 2.107", "required": True},
            {"step": 5, "action": "Prepare for de novo hearing — judge reviews fresh",
             "rule": "MCR 3.218(D)", "required": False},
        ],
        "service": {
            "method": "Mail or personal service",
            "timing": "Within 21 days of FOC recommendation",
            "proof_form": "MC 12",
            "notes": "Must serve both the opposing party AND the FOC office.",
        },
        "pitfalls": [
            {"risk": "Missing 21-day deadline",
             "severity": "critical",
             "mitigation": "Mark calendar IMMEDIATELY upon receiving recommendation"},
            {"risk": "Objection too vague",
             "severity": "medium",
             "mitigation": "Specify exactly which findings you object to and why"},
        ],
        "tips": [
            "De novo hearing means the judge reviews everything fresh — not limited to FOC record",
            "You may present new evidence at the de novo hearing",
            "Bring your own witnesses if helpful",
        ],
        "cross_references": [
            {"rule": "MCL 552.507(5)", "description": "21-day objection period"},
            {"rule": "MCR 3.218(D)", "description": "De novo hearing procedure"},
            {"rule": "MCR 3.208", "description": "FOC enforcement"},
        ],
        "deadline_trigger": "foc_objection",
        "fee": {"amount": "No separate fee (part of existing case)", "waiver": "N/A"},
        "format": [
            "Use FOC 78 form or substantially similar written objection",
            "Clearly state each point of objection",
        ],
    },
}

# ---------------------------------------------------------------------------
# Oracle Engine
# ---------------------------------------------------------------------------

class Oracle:
    """Michigan Rule Reasoning Engine.

    Connects to LEXICON (or procedures.db fallback) and litigation_context.db
    to produce complete procedural roadmaps for Michigan filings.
    """

    def __init__(
        self,
        lexicon_db: Optional[str] = None,
        procedures_db: Optional[str] = None,
        litigation_db: Optional[str] = None,
    ):
        self._lexicon_path = Path(lexicon_db) if lexicon_db else _LEXICON_DB
        self._procedures_path = Path(procedures_db) if procedures_db else _PROCEDURES_DB
        self._litigation_path = Path(litigation_db) if litigation_db else _LITIGATION_DB

        self._deadline_calc = DeadlineCalculator()
        self._calendar = self._deadline_calc.cal

        # DB connections are opened lazily
        self._lexicon_conn: Optional[sqlite3.Connection] = None
        self._procedures_conn: Optional[sqlite3.Connection] = None
        self._litigation_conn: Optional[sqlite3.Connection] = None

    # -- connection helpers --------------------------------------------------

    def _connect(self, path: Path) -> Optional[sqlite3.Connection]:
        """Open a read-only SQLite connection with WAL pragmas."""
        if not path.exists():
            logger.debug("Database not found: %s", path)
            return None
        try:
            conn = sqlite3.connect(str(path), timeout=60)
            conn.row_factory = sqlite3.Row
            conn.execute("PRAGMA busy_timeout = 60000")
            conn.execute("PRAGMA journal_mode = WAL")
            conn.execute("PRAGMA cache_size = -32000")
            conn.execute("PRAGMA temp_store = MEMORY")
            conn.execute("PRAGMA synchronous = NORMAL")
            return conn
        except sqlite3.Error as exc:
            logger.warning("Failed to connect to %s: %s", path, exc)
            return None

    @property
    def lexicon(self) -> Optional[sqlite3.Connection]:
        """LEXICON database connection (lazy)."""
        if self._lexicon_conn is None:
            self._lexicon_conn = self._connect(self._lexicon_path)
        return self._lexicon_conn

    @property
    def procedures(self) -> Optional[sqlite3.Connection]:
        """Procedures database connection (lazy)."""
        if self._procedures_conn is None:
            self._procedures_conn = self._connect(self._procedures_path)
        return self._procedures_conn

    @property
    def litigation(self) -> Optional[sqlite3.Connection]:
        """Litigation context database connection (lazy)."""
        if self._litigation_conn is None:
            self._litigation_conn = self._connect(self._litigation_path)
        return self._litigation_conn

    def close(self) -> None:
        """Close all database connections."""
        for conn in (self._lexicon_conn, self._procedures_conn, self._litigation_conn):
            if conn:
                try:
                    conn.close()
                except sqlite3.Error:
                    pass
        self._lexicon_conn = None
        self._procedures_conn = None
        self._litigation_conn = None

    # -- DB query helpers ----------------------------------------------------

    def _query_rules_for_filing(self, filing_type: str) -> List[Dict]:
        """Pull applicable rules from filing_rule_map in litigation_context.db."""
        results: List[Dict] = []
        conn = self.litigation
        if conn is None:
            return results
        try:
            rows = conn.execute(
                "SELECT authority_type, authority_number, requirement, mandatory "
                "FROM filing_rule_map WHERE filing_id LIKE ? OR requirement LIKE ?",
                (f"%{filing_type}%", f"%{filing_type}%"),
            ).fetchall()
            for r in rows:
                results.append({
                    "authority_type": r["authority_type"],
                    "authority_number": r["authority_number"],
                    "requirement": r["requirement"],
                    "mandatory": bool(r["mandatory"]),
                })
        except sqlite3.Error as exc:
            logger.warning("Error querying filing_rule_map: %s", exc)
        return results

    def _query_scao_forms(self, form_numbers: List[str]) -> List[Dict]:
        """Look up SCAO form details from litigation_context.db."""
        results: List[Dict] = []
        conn = self.litigation
        if conn is None:
            return results
        try:
            placeholders = ",".join("?" for _ in form_numbers)
            rows = conn.execute(
                f"SELECT form_number, title, category, court_type, notes "
                f"FROM scao_forms WHERE form_number IN ({placeholders})",
                form_numbers,
            ).fetchall()
            for r in rows:
                results.append(dict(r))
        except sqlite3.Error as exc:
            logger.warning("Error querying scao_forms: %s", exc)
        return results

    def _query_deadlines_db(self, filing_type: str) -> List[Dict]:
        """Pull deadline rules from procedures.db filing_deadlines table."""
        results: List[Dict] = []
        conn = self.procedures
        if conn is None:
            return results
        try:
            rows = conn.execute(
                "SELECT filing_type, court, deadline_rule, days_or_description, "
                "mcr_reference, notes FROM filing_deadlines "
                "WHERE filing_type LIKE ?",
                (f"%{filing_type}%",),
            ).fetchall()
            for r in rows:
                results.append(dict(r))
        except sqlite3.Error as exc:
            logger.warning("Error querying filing_deadlines: %s", exc)
        return results

    def _query_service_methods(self) -> List[Dict]:
        """Pull all service methods from procedures.db."""
        results: List[Dict] = []
        conn = self.procedures
        if conn is None:
            return results
        try:
            rows = conn.execute(
                "SELECT method, mcr_rule, when_valid, proof_form, notes "
                "FROM service_methods"
            ).fetchall()
            for r in rows:
                results.append(dict(r))
        except sqlite3.Error as exc:
            logger.warning("Error querying service_methods: %s", exc)
        return results

    def _query_fee_schedule(self, filing_type: str) -> List[Dict]:
        """Pull fee info from procedures.db."""
        results: List[Dict] = []
        conn = self.procedures
        if conn is None:
            return results
        try:
            rows = conn.execute(
                "SELECT filing_type, court, amount, waiver_available, "
                "waiver_form, authority FROM fee_schedule "
                "WHERE filing_type LIKE ?",
                (f"%{filing_type}%",),
            ).fetchall()
            for r in rows:
                results.append(dict(r))
        except sqlite3.Error as exc:
            logger.warning("Error querying fee_schedule: %s", exc)
        return results

    def _query_motion_practice(self) -> List[Dict]:
        """Pull motion practice steps from procedures.db."""
        results: List[Dict] = []
        conn = self.procedures
        if conn is None:
            return results
        try:
            rows = conn.execute(
                "SELECT step_number, step_name, description, mcr_rule, "
                "deadline, form FROM motion_practice ORDER BY step_number"
            ).fetchall()
            for r in rows:
                results.append(dict(r))
        except sqlite3.Error as exc:
            logger.warning("Error querying motion_practice: %s", exc)
        return results

    # -- public API ----------------------------------------------------------

    def get_lane_info(self, lane: str) -> Dict:
        """Return verified case information for a case lane.

        Args:
            lane: One of A, B, C, D, E, F (case-insensitive).

        Returns:
            Dict with lane, description, case_number, court, judge, etc.
        """
        key = lane.upper().strip()
        info = _LANE_INFO.get(key)
        if info is None:
            return {"error": f"Unknown lane '{lane}'. Valid lanes: A, B, C, D, E, F"}
        return dict(info)

    def get_roadmap(
        self,
        filing_type: str,
        court: str,
        lane: Optional[str] = None,
        reference_date: Optional[date] = None,
    ) -> Dict:
        """Produce a complete procedural roadmap for a filing.

        Args:
            filing_type: e.g. ``"motion_to_modify_custody"``
            court: e.g. ``"14th_circuit_family"``
            lane: Optional case lane (A-F)
            reference_date: Optional hearing/trigger date for deadline computation

        Returns:
            Comprehensive roadmap dict.
        """
        knowledge = _FILING_KNOWLEDGE.get(filing_type, {})
        display_name = knowledge.get("display_name", filing_type.replace("_", " ").title())

        # Lane info
        lane_data = self.get_lane_info(lane) if lane else {}
        case_number = lane_data.get("case_number", "[VERIFY]") if lane_data else "[VERIFY]"

        # DB-enriched rules
        db_rules = self._query_rules_for_filing(filing_type)
        db_deadlines = self._query_deadlines_db(filing_type)
        db_fees = self._query_fee_schedule(filing_type)

        # Merge forms from knowledge base with SCAO DB enrichment
        kb_forms = knowledge.get("forms", [])
        form_numbers = [f["form_number"] for f in kb_forms]
        db_form_details = self._query_scao_forms(form_numbers) if form_numbers else []

        # Build enriched forms list
        enriched_forms = []
        db_form_map = {f["form_number"]: f for f in db_form_details}
        for f in kb_forms:
            enriched = dict(f)
            db_info = db_form_map.get(f["form_number"])
            if db_info and db_info.get("notes"):
                enriched["db_notes"] = db_info["notes"]
            enriched_forms.append(enriched)

        # Compute deadlines if reference_date provided
        computed_deadlines = []
        if reference_date:
            trigger = knowledge.get("deadline_trigger", "motion_hearing")
            computed_deadlines = self._deadline_calc.compute(trigger, reference_date)

        # Build requirements object
        requirements = {
            "notice": [
                {"requirement": "Notice of Hearing must be served with motion",
                 "rule": "MCR 2.119(C)"},
            ],
            "forms": enriched_forms,
            "service": knowledge.get("service", {}),
            "deadline": db_deadlines or [
                {"requirement": "See computed_deadlines", "rule": knowledge.get("deadline_trigger", "")},
            ],
            "content": knowledge.get("format", []),
            "fee": knowledge.get("fee", {}),
            "format": knowledge.get("format", []),
        }
        if db_fees:
            requirements["fee_schedule_db"] = db_fees

        roadmap = {
            "filing_type": filing_type,
            "display_name": display_name,
            "court": court,
            "lane": lane or "N/A",
            "case_number": case_number,
            "lane_info": lane_data if lane_data and "error" not in lane_data else None,
            "applicable_rules": knowledge.get("primary_rules", []),
            "db_rules": db_rules,
            "requirements": requirements,
            "computed_deadlines": computed_deadlines,
            "cross_references": knowledge.get("cross_references", []),
            "pitfalls": knowledge.get("pitfalls", []),
            "tips": knowledge.get("tips", []),
        }
        return roadmap

    def compute_deadlines(
        self,
        trigger_event: str,
        reference_date: Optional[date] = None,
        court: Optional[str] = None,
    ) -> List[Dict]:
        """Compute actual dates from deadline rules.

        Args:
            trigger_event: Event type (e.g. ``"motion_filing"``,
                ``"appeal_of_right"``, ``"foc_objection"``).
            reference_date: Reference date. Defaults to today.
            court: Optional court identifier.

        Returns:
            List of deadline dicts with computed dates.
        """
        ref = reference_date or date.today()
        return self._deadline_calc.compute(trigger_event, ref)

    def get_checklist(self, filing_type: str, court: Optional[str] = None) -> List[Dict]:
        """Return a step-by-step filing checklist.

        Args:
            filing_type: Filing type key.
            court: Optional court.

        Returns:
            Ordered list of checklist-step dicts.
        """
        knowledge = _FILING_KNOWLEDGE.get(filing_type)
        if knowledge:
            return knowledge.get("checklist", [])

        # Fallback: return generic motion practice steps from DB
        db_steps = self._query_motion_practice()
        if db_steps:
            return [
                {
                    "step": s.get("step_number", idx + 1),
                    "action": f"{s.get('step_name', '')}: {s.get('description', '')}",
                    "rule": s.get("mcr_rule", ""),
                    "required": True,
                }
                for idx, s in enumerate(db_steps)
            ]

        return [{"step": 1, "action": f"No checklist found for '{filing_type}'",
                 "rule": "", "required": False}]

    def get_forms_required(
        self, filing_type: str, court: Optional[str] = None
    ) -> List[Dict]:
        """Return SCAO forms required for a filing.

        Args:
            filing_type: Filing type key.
            court: Optional court.

        Returns:
            List of form dicts with form_number, title, required, notes.
        """
        knowledge = _FILING_KNOWLEDGE.get(filing_type)
        if knowledge:
            kb_forms = knowledge.get("forms", [])
            # Enrich from SCAO DB
            form_numbers = [f["form_number"] for f in kb_forms]
            db_forms = self._query_scao_forms(form_numbers) if form_numbers else []
            db_map = {f["form_number"]: f for f in db_forms}
            enriched = []
            for f in kb_forms:
                entry = dict(f)
                db_info = db_map.get(f["form_number"])
                if db_info and db_info.get("notes"):
                    entry["db_description"] = db_info["notes"]
                enriched.append(entry)
            return enriched

        return [{"form_number": "N/A", "title": f"No forms found for '{filing_type}'",
                 "required": False, "notes": ""}]

    def get_service_requirements(
        self, filing_type: str, court: Optional[str] = None
    ) -> Dict:
        """Return service method, timing, and proof requirements.

        Args:
            filing_type: Filing type key.
            court: Optional court.

        Returns:
            Service requirements dict.
        """
        knowledge = _FILING_KNOWLEDGE.get(filing_type)
        if knowledge:
            svc = dict(knowledge.get("service", {}))
            # Augment with DB service methods
            db_methods = self._query_service_methods()
            if db_methods:
                svc["available_methods"] = db_methods
            return svc

        # Fallback: return generic service methods from DB
        db_methods = self._query_service_methods()
        if db_methods:
            return {
                "method": "See available_methods below",
                "timing": "Per applicable court rule",
                "proof_form": "MC 12",
                "notes": f"No specific service info for '{filing_type}'",
                "available_methods": db_methods,
            }

        return {
            "method": "MCR 2.107 (general service rule)",
            "timing": "Per applicable court rule",
            "proof_form": "MC 12",
            "notes": f"No specific service data for '{filing_type}'",
        }

    def analyze_filing_risks(
        self, filing_type: str, court: Optional[str] = None, lane: Optional[str] = None
    ) -> List[Dict]:
        """Analyze potential risks and provide mitigation strategies.

        Args:
            filing_type: Filing type key.
            court: Optional court.
            lane: Optional case lane.

        Returns:
            List of risk dicts with severity and mitigation.
        """
        knowledge = _FILING_KNOWLEDGE.get(filing_type)
        risks = list(knowledge.get("pitfalls", [])) if knowledge else []

        # Add lane-specific risks
        if lane:
            lane_key = lane.upper().strip()
            if lane_key == "A":
                risks.append({
                    "risk": "Pro se filing — held to same standards as attorneys",
                    "severity": "medium",
                    "mitigation": "Follow all MCR formatting and content rules strictly",
                })
            elif lane_key == "E":
                risks.append({
                    "risk": "JTC complaints have strict confidentiality rules",
                    "severity": "high",
                    "mitigation": "Do not publicly disclose JTC complaint contents until authorized",
                })
            elif lane_key == "F":
                risks.append({
                    "risk": "COA has strict formatting and page-limit requirements",
                    "severity": "high",
                    "mitigation": "Review MCR 7.212(B) for brief format rules before filing",
                })

        if not risks:
            risks.append({
                "risk": "No specific risks identified",
                "severity": "low",
                "mitigation": f"Review applicable rules for '{filing_type}'",
            })

        return risks

    # -- convenience ---------------------------------------------------------

    def list_filing_types(self) -> List[str]:
        """Return all known filing types."""
        return sorted(_FILING_KNOWLEDGE.keys())

    def list_lanes(self) -> List[Dict]:
        """Return summary of all case lanes."""
        return [
            {"lane": k, "description": v["description"], "case_number": v["case_number"]}
            for k, v in sorted(_LANE_INFO.items())
        ]


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def _print_json(data: Any) -> None:
    """Pretty-print data as JSON."""
    print(json.dumps(data, indent=2, default=str))


def main() -> None:
    try:
        sys.stdout = open(sys.stdout.fileno(), mode="w", encoding="utf-8", errors="replace", closefd=False)
    except (OSError, AttributeError):
        pass

    parser = argparse.ArgumentParser(
        description="ORACLE — Michigan Rule Reasoning Engine",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=(
            "Examples:\n"
            "  python oracle_engine.py roadmap motion_to_modify_custody 14th_circuit_family --lane A\n"
            "  python oracle_engine.py deadlines motion_filing --date 2026-04-15\n"
            "  python oracle_engine.py checklist motion_to_disqualify_judge\n"
            "  python oracle_engine.py forms application_for_leave michigan_coa\n"
            "  python oracle_engine.py service motion_to_modify_custody 14th_circuit_family\n"
            "  python oracle_engine.py risks motion_to_modify_custody 14th_circuit_family --lane A\n"
            "  python oracle_engine.py lane A\n"
            "  python oracle_engine.py list\n"
        ),
    )
    sub = parser.add_subparsers(dest="command")

    # roadmap
    p_road = sub.add_parser("roadmap", help="Complete procedural roadmap")
    p_road.add_argument("filing_type", help="Filing type (e.g. motion_to_modify_custody)")
    p_road.add_argument("court", help="Court (e.g. 14th_circuit_family)")
    p_road.add_argument("--lane", help="Case lane (A-F)")
    p_road.add_argument("--date", dest="ref_date", help="Reference/hearing date (YYYY-MM-DD)")

    # deadlines
    p_dead = sub.add_parser("deadlines", help="Compute deadlines from trigger event")
    p_dead.add_argument("trigger", help="Trigger event (e.g. motion_filing, appeal_of_right)")
    p_dead.add_argument("--date", dest="ref_date", help="Reference date (YYYY-MM-DD)")
    p_dead.add_argument("--court", help="Court")

    # checklist
    p_check = sub.add_parser("checklist", help="Step-by-step checklist")
    p_check.add_argument("filing_type", help="Filing type")
    p_check.add_argument("--court", help="Court")

    # forms
    p_forms = sub.add_parser("forms", help="Required SCAO forms")
    p_forms.add_argument("filing_type", help="Filing type")
    p_forms.add_argument("court", nargs="?", help="Court")

    # service
    p_svc = sub.add_parser("service", help="Service requirements")
    p_svc.add_argument("filing_type", help="Filing type")
    p_svc.add_argument("court", nargs="?", help="Court")

    # risks
    p_risk = sub.add_parser("risks", help="Filing risk analysis")
    p_risk.add_argument("filing_type", help="Filing type")
    p_risk.add_argument("court", nargs="?", help="Court")
    p_risk.add_argument("--lane", help="Case lane (A-F)")

    # lane
    p_lane = sub.add_parser("lane", help="Case lane info")
    p_lane.add_argument("lane_id", help="Lane identifier (A-F)")

    # list
    sub.add_parser("list", help="List all known filing types and lanes")

    args = parser.parse_args()
    if not args.command:
        parser.print_help()
        sys.exit(1)

    oracle = Oracle()

    try:
        if args.command == "roadmap":
            ref = date.fromisoformat(args.ref_date) if args.ref_date else None
            result = oracle.get_roadmap(args.filing_type, args.court,
                                        lane=args.lane, reference_date=ref)
            _print_json(result)

        elif args.command == "deadlines":
            ref = date.fromisoformat(args.ref_date) if args.ref_date else None
            result = oracle.compute_deadlines(args.trigger, reference_date=ref,
                                              court=getattr(args, "court", None))
            _print_json(result)

        elif args.command == "checklist":
            result = oracle.get_checklist(args.filing_type,
                                          court=getattr(args, "court", None))
            print(f"\n{'='*60}")
            print(f"  CHECKLIST: {args.filing_type}")
            print(f"{'='*60}")
            for item in result:
                marker = "[REQUIRED]" if item.get("required") else "[optional]"
                rule_tag = f"  ({item['rule']})" if item.get("rule") else ""
                print(f"  Step {item['step']:>2}: {item['action']}{rule_tag}  {marker}")
            print()

        elif args.command == "forms":
            result = oracle.get_forms_required(args.filing_type,
                                               court=getattr(args, "court", None))
            _print_json(result)

        elif args.command == "service":
            result = oracle.get_service_requirements(args.filing_type,
                                                     court=getattr(args, "court", None))
            _print_json(result)

        elif args.command == "risks":
            result = oracle.analyze_filing_risks(args.filing_type,
                                                 court=getattr(args, "court", None),
                                                 lane=getattr(args, "lane", None))
            _print_json(result)

        elif args.command == "lane":
            result = oracle.get_lane_info(args.lane_id)
            _print_json(result)

        elif args.command == "list":
            print("\nKnown Filing Types:")
            for ft in oracle.list_filing_types():
                name = _FILING_KNOWLEDGE[ft].get("display_name", ft)
                print(f"  {ft:<40s} {name}")
            print("\nCase Lanes:")
            for lane in oracle.list_lanes():
                print(f"  Lane {lane['lane']}: {lane['description']:<30s} [{lane['case_number']}]")
            print()

    finally:
        oracle.close()


if __name__ == "__main__":
    main()
