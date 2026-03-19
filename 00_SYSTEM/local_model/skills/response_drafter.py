#!/usr/bin/env python3
"""
THE MANBEARPIG — EPOCH v8.0 — Response Drafter Engine
=====================================================
Generates court-ready responses to opposition filings with DB-backed
evidence, IRAC structure, and Michigan court rule compliance.

Case: Andrew Pigors (Pro Se Plaintiff/Appellant) v. Tiffany Watson (Defendant/Appellee)
Court: 14th Circuit Court, Muskegon County — Hon. Jenny L. McNeill
Adversary Counsel: Jennifer Barnes (trial) / Ron Berry (appellate)

Response types:
  1. Motion Response        — MCR 2.119(C)(2)
  2. Brief Response         — MCR 7.212(G)/(H)
  3. Order Objection        — MCR 2.602(B)(3)
  4. FOC Objection          — MCL 552.507(5)
  5. Discovery Response     — MCR 2.309-2.313
  6. Counter-Argument Gen   — adversary_models + impeachment_items
"""

from __future__ import annotations

import json
import os
import re
import sqlite3
import sys
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

sys.path.insert(
    0,
    str(
        Path(__file__).resolve().parent.parent
        if "skills" in str(Path(__file__))
        else Path(__file__).resolve().parent
    ),
)
try:
    from cycle_method import cycle_json, cycle_print
except ImportError:
    cycle_json = lambda obj, **kw: print(json.dumps(obj, default=str))
    cycle_print = print

DB_PATH = os.environ.get(
    "LITIGATION_DB_PATH",
    r"C:\Users\andre\LitigationOS\litigation_context.db",
)

# ── Case constants ────────────────────────────────────────────────────────────

CASE_CAPTION = """
================================================================================
STATE OF MICHIGAN
IN THE 14TH CIRCUIT COURT FOR THE COUNTY OF MUSKEGON

ANDREW PIGORS,                         Case No. {case_number}
    Plaintiff,                         Hon. Jenny L. McNeill

v.

TIFFANY WATSON (fka PIGORS),
    Defendant.
________________________________________________________________________________
""".strip()

COA_CAPTION = """
================================================================================
STATE OF MICHIGAN
IN THE COURT OF APPEALS

ANDREW PIGORS,                         COA Case No. 366810
    Plaintiff-Appellant,               Lower Court No. 2024-001507-DC

v.

TIFFANY WATSON (fka PIGORS),
    Defendant-Appellee.
________________________________________________________________________________
""".strip()

SIGNATURE_BLOCK = """
Respectfully submitted,

______________________________
Andrew Pigors, Pro Se Plaintiff
Muskegon, Michigan
Date: {date}
""".strip()

CERTIFICATE_OF_SERVICE = """
CERTIFICATE OF SERVICE

I, Andrew Pigors, certify that on {date}, I served a copy of the
foregoing document on the following party(ies) by:
  [ ] First-class U.S. mail, postage prepaid
  [ ] Personal delivery
  [ ] Electronic service (email / MiFILE)

    Tiffany Watson (fka Pigors)
    c/o Jennifer Barnes, Esq.
    [Address on file with the Court]

______________________________
Andrew Pigors
""".strip()

# ── Response type configurations ──────────────────────────────────────────────

RESPONSE_TYPES = {
    "motion_response": {
        "title": "RESPONSE TO DEFENDANT'S MOTION",
        "authority": "MCR 2.119(C)(2)",
        "deadline_days": 7,
        "mail_add_days": 3,
        "description": "Response to motion — 7 days (+ 3 if served by mail)",
        "required_sections": [
            "Caption per MCR 2.113",
            "Statement of issues",
            "Counter-statement of facts",
            "IRAC argument for each opposing point",
            "Relief requested",
            "Signature block",
            "Certificate of service",
        ],
    },
    "brief_response": {
        "title": "PLAINTIFF-APPELLANT'S REPLY BRIEF",
        "authority": "MCR 7.212(G); MCR 7.212(H)",
        "deadline_days": 21,
        "mail_add_days": 0,
        "description": "Reply brief — MCR 7.212(H), limited to 7,000 words",
        "word_limit": 7000,
        "required_sections": [
            "COA caption",
            "Table of contents",
            "Table of authorities",
            "Reply argument (limited to issues raised in appellee brief)",
            "Relief requested",
            "Signature block",
            "Certificate of service",
        ],
    },
    "order_objection": {
        "title": "OBJECTION TO PROPOSED ORDER",
        "authority": "MCR 2.602(B)(3)",
        "deadline_days": 7,
        "mail_add_days": 3,
        "description": "Objection to proposed order — 7-day window",
        "required_sections": [
            "Caption per MCR 2.113",
            "Identification of proposed order",
            "Specific objections with authority",
            "Proposed alternative language",
            "Signature block",
            "Certificate of service",
        ],
    },
    "foc_objection": {
        "title": "OBJECTION TO FRIEND OF THE COURT RECOMMENDATION",
        "authority": "MCL 552.507(5); MCR 3.208",
        "deadline_days": 21,
        "mail_add_days": 0,
        "description": "FOC objection — 21-day deadline, triggers de novo hearing",
        "required_sections": [
            "Caption per MCR 2.113",
            "Identification of FOC recommendation",
            "Request for de novo hearing",
            "Specific factual objections",
            "Specific legal objections",
            "Best interest factor analysis (MCL 722.23)",
            "Signature block",
            "Certificate of service",
        ],
    },
    "discovery_response": {
        "title": "PLAINTIFF'S RESPONSES TO DEFENDANT'S DISCOVERY REQUESTS",
        "authority": "MCR 2.309; MCR 2.310; MCR 2.312; MCR 2.313",
        "deadline_days": 28,
        "mail_add_days": 3,
        "description": "Discovery responses — 28 days, objections with particularity",
        "required_sections": [
            "Caption per MCR 2.113",
            "General objections",
            "Specific responses/objections per request",
            "Privilege log if withholding (MCR 2.302(B)(5))",
            "Verification/signature",
            "Certificate of service",
        ],
    },
}

# ── Discovery objection catalog ──────────────────────────────────────────────

DISCOVERY_OBJECTIONS = {
    "overbroad": {
        "text": (
            "Plaintiff objects to this request as overbroad and unduly "
            "burdensome. The request is not proportional to the needs of "
            "the case and seeks information far beyond the scope of "
            "permissible discovery."
        ),
        "authority": "MCR 2.302(B)(1); MCR 2.302(C)",
    },
    "vague": {
        "text": (
            "Plaintiff objects to this request as vague and ambiguous. "
            "The terms used are undefined and susceptible to multiple "
            "interpretations, making a meaningful response impossible."
        ),
        "authority": "MCR 2.302(B)(1)",
    },
    "privilege": {
        "text": (
            "Plaintiff objects to this request to the extent it seeks "
            "information protected by the attorney-client privilege, "
            "work product doctrine, or other applicable privilege."
        ),
        "authority": "MRE 501; MCR 2.302(B)(3)",
    },
    "relevance": {
        "text": (
            "Plaintiff objects to this request as seeking information "
            "that is neither relevant to any party's claim or defense "
            "nor proportional to the needs of the case."
        ),
        "authority": "MCR 2.302(B)(1); MRE 401",
    },
    "burden": {
        "text": (
            "Plaintiff objects to this request as imposing undue burden "
            "and expense that outweighs the likely benefit of the "
            "information sought, particularly given Plaintiff's pro se status."
        ),
        "authority": "MCR 2.302(C)",
    },
    "harassment": {
        "text": (
            "Plaintiff objects to this request as designed to harass, "
            "embarrass, or oppress rather than to seek relevant information."
        ),
        "authority": "MCR 2.302(C); MCR 2.313(C)",
    },
    "already_provided": {
        "text": (
            "Plaintiff objects to this request as seeking information "
            "already in Defendant's possession, custody, or control, or "
            "which has been previously provided in this litigation."
        ),
        "authority": "MCR 2.302(B)(1)",
    },
}


def _get_db() -> Optional[sqlite3.Connection]:
    """Get read-only DB connection."""
    try:
        conn = sqlite3.connect(DB_PATH, timeout=30)
        conn.execute("PRAGMA journal_mode=WAL")
        conn.execute("PRAGMA query_only=ON")
        conn.row_factory = sqlite3.Row
        return conn
    except Exception:
        return None


def _row_to_dict(row: sqlite3.Row) -> Dict:
    return {k: row[k] for k in row.keys()}


def _today_str() -> str:
    return datetime.now().strftime("%B %d, %Y")


def _safe_fts_query(conn: sqlite3.Connection, fts_table: str,
                     base_table: str, match_term: str,
                     columns: str = "*", limit: int = 10) -> List[Dict]:
    """Run FTS5 MATCH with LIKE fallback."""
    results: List[Dict] = []
    try:
        rows = conn.execute(
            f"SELECT {columns} FROM {base_table} WHERE rowid IN "
            f"(SELECT rowid FROM {fts_table} WHERE {fts_table} MATCH ?) "
            f"ORDER BY rowid DESC LIMIT ?",
            (match_term, limit),
        ).fetchall()
        results = [_row_to_dict(r) for r in rows]
    except sqlite3.OperationalError:
        # FTS fallback to LIKE on first meaningful column
        try:
            rows = conn.execute(
                f"SELECT {columns} FROM {base_table} "
                f"WHERE CAST({base_table} AS TEXT) LIKE ? LIMIT ?",
                (f"%{match_term}%", limit),
            ).fetchall()
            results = [_row_to_dict(r) for r in rows]
        except Exception:
            pass
    return results


class ResponseDrafter:
    """
    Generates court-ready responses to opposition filings.

    All methods return JSON-serializable dicts. Evidence and authority
    are pulled from the litigation DB — no external APIs.
    """

    CASE_NUMBERS = {
        "custody": "2024-001507-DC",
        "ppo": "2023-5907-PP",
        "coa": "366810",
        "default": "2024-001507-DC",
    }

    def __init__(self, db_path: str = DB_PATH):
        self.db_path = db_path

    def _conn(self) -> Optional[sqlite3.Connection]:
        try:
            conn = sqlite3.connect(self.db_path, timeout=30)
            conn.execute("PRAGMA journal_mode=WAL")
            conn.execute("PRAGMA query_only=ON")
            conn.row_factory = sqlite3.Row
            return conn
        except Exception:
            return None

    # ══════════════════════════════════════════════════════════════════════
    # 1. MAIN ENTRY — draft_response
    # ══════════════════════════════════════════════════════════════════════

    def draft_response(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """
        Main entry point for generating a response.

        params:
            type (str):               One of RESPONSE_TYPES keys
            opposing_arguments (list): List of argument strings to counter
            deadline (str|None):       ISO date string of deadline, or None
            service_date (str|None):   ISO date of service (for deadline calc)
            service_method (str):      'mail' | 'electronic' | 'personal'
            case_lane (str):           'custody' | 'ppo' | 'coa' | default
            keywords (list|None):      Extra DB search keywords
            foc_recommendation (str):  Text of FOC rec (for foc_objection)
            proposed_order (str):      Text of proposed order (for order_objection)
            discovery_requests (list): List of discovery request dicts

        Returns dict with: document_text, metadata, evidence_used,
                          authority_cited, validation, deadline_info
        """
        resp_type = params.get("type", "motion_response")
        if resp_type not in RESPONSE_TYPES:
            return {
                "error": f"Unknown response type: {resp_type}",
                "valid_types": list(RESPONSE_TYPES.keys()),
            }

        config = RESPONSE_TYPES[resp_type]

        # Calculate deadline
        deadline_info = self.calculate_deadline({
            "service_date": params.get("service_date"),
            "service_method": params.get("service_method", "mail"),
            "response_type": resp_type,
        })

        # Route to specific handler
        dispatch = {
            "motion_response": self.response_to_motion,
            "brief_response": self.response_to_brief,
            "order_objection": self.objection_to_order,
            "foc_objection": self.foc_objection,
            "discovery_response": self.discovery_response,
        }

        handler = dispatch[resp_type]
        result = handler(params)
        result["deadline_info"] = deadline_info
        result["response_config"] = {
            "type": resp_type,
            "title": config["title"],
            "authority": config["authority"],
            "required_sections": config["required_sections"],
        }

        return result

    # ══════════════════════════════════════════════════════════════════════
    # 2. DEADLINE CALCULATOR
    # ══════════════════════════════════════════════════════════════════════

    def calculate_deadline(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """
        Calculate response deadline from service date.

        params:
            service_date (str|None):  ISO date (YYYY-MM-DD) of service
            service_method (str):     'mail' | 'electronic' | 'personal'
            response_type (str):      Key from RESPONSE_TYPES

        Returns deadline date, days remaining, and urgency level.
        """
        resp_type = params.get("response_type", "motion_response")
        config = RESPONSE_TYPES.get(resp_type, RESPONSE_TYPES["motion_response"])
        service_method = params.get("service_method", "mail")

        base_days = config["deadline_days"]
        mail_days = config["mail_add_days"] if service_method == "mail" else 0
        total_days = base_days + mail_days

        service_date_str = params.get("service_date")
        if service_date_str:
            try:
                service_date = datetime.strptime(service_date_str, "%Y-%m-%d")
            except ValueError:
                service_date = datetime.now()
        else:
            service_date = datetime.now()

        deadline_date = service_date + timedelta(days=total_days)
        days_remaining = (deadline_date - datetime.now()).days

        if days_remaining < 0:
            urgency = "EXPIRED"
        elif days_remaining <= 2:
            urgency = "CRITICAL"
        elif days_remaining <= 5:
            urgency = "HIGH"
        elif days_remaining <= 10:
            urgency = "MODERATE"
        else:
            urgency = "NORMAL"

        return {
            "service_date": service_date.strftime("%Y-%m-%d"),
            "service_method": service_method,
            "base_days": base_days,
            "mail_additional_days": mail_days,
            "total_days": total_days,
            "deadline_date": deadline_date.strftime("%Y-%m-%d"),
            "days_remaining": days_remaining,
            "urgency": urgency,
            "authority": config["authority"],
            "notes": [
                f"Base period: {base_days} days under {config['authority']}",
                f"Mail service adds {config['mail_add_days']} days per MCR 2.107(C)(3)" if config["mail_add_days"] else "No additional days for electronic/personal service",
                "Weekend/holiday adjustments may apply per MCR 1.108",
            ],
        }

    # ══════════════════════════════════════════════════════════════════════
    # 3. RESPONSE TO MOTION — MCR 2.119(C)(2)
    # ══════════════════════════════════════════════════════════════════════

    def response_to_motion(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """
        Draft MCR 2.119 response to a motion filed by Watson/Barnes.

        params:
            opposing_arguments (list): List of argument strings
            case_lane (str):           'custody' | 'ppo' | 'coa'
            keywords (list|None):      Extra search terms
        """
        opposing_args = params.get("opposing_arguments", [])
        case_lane = params.get("case_lane", "custody")
        extra_kw = params.get("keywords", [])
        case_num = self.CASE_NUMBERS.get(case_lane, self.CASE_NUMBERS["default"])

        conn = self._conn()
        if not conn:
            return {"error": "Database unavailable"}

        try:
            # Build counter-arguments for each opposing point
            counters: List[Dict] = []
            all_evidence: List[Dict] = []
            all_authority: List[Dict] = []

            for i, arg in enumerate(opposing_args, 1):
                # Extract keywords from the opposing argument
                arg_keywords = [w for w in arg.split() if len(w) > 4][:6]
                search_terms = arg_keywords + extra_kw

                # Find counter-evidence
                evidence = self._search_evidence(conn, search_terms)
                all_evidence.extend(evidence)

                # Find authority
                authority = self._search_authority(conn, search_terms)
                all_authority.extend(authority)

                # Find impeachment material
                impeachment = self._search_impeachment(conn, search_terms, limit=3)

                counters.append({
                    "argument_number": i,
                    "opposing_argument": arg,
                    "irac": {
                        "issue": (
                            f"Whether Defendant's argument regarding "
                            f"'{arg[:100]}...' has merit."
                        ),
                        "rule": self._format_authority_block(authority),
                        "application": (
                            f"Defendant's argument fails because the record "
                            f"evidence directly contradicts this claim. "
                            + self._format_evidence_block(evidence)
                        ),
                        "conclusion": (
                            f"For the foregoing reasons, Defendant's argument "
                            f"#{i} should be rejected."
                        ),
                    },
                    "evidence_cited": evidence[:5],
                    "authority_cited": authority[:5],
                    "impeachment_available": impeachment[:3],
                })

            # Assemble document text
            date_str = _today_str()
            caption = CASE_CAPTION.format(case_number=case_num)
            sections = [
                caption,
                "",
                RESPONSE_TYPES["motion_response"]["title"],
                "=" * 60,
                "",
                "NOW COMES Plaintiff Andrew Pigors, appearing pro se, and",
                "respectfully submits this Response to Defendant's Motion,",
                "pursuant to MCR 2.119(C)(2), and states as follows:",
                "",
            ]

            # Counter-statement of facts
            sections.append("I. COUNTER-STATEMENT OF FACTS")
            sections.append("")
            sections.append(
                "    The record evidence demonstrates the following facts "
                "that Defendant's motion fails to address or misrepresents:"
            )
            sections.append("")
            for ev in all_evidence[:5]:
                qt = ev.get("quote_text", "")[:200]
                speaker = ev.get("speaker", "Record")
                sections.append(f"    {len(sections)}. [{speaker}]: \"{qt}\"")
            sections.append("")

            # IRAC arguments
            for counter in counters:
                sections.append(
                    f"II-{counter['argument_number']}. "
                    f"RESPONSE TO DEFENDANT'S ARGUMENT #{counter['argument_number']}"
                )
                sections.append("")
                irac = counter["irac"]
                sections.append(f"    ISSUE: {irac['issue']}")
                sections.append("")
                sections.append(f"    RULE: {irac['rule']}")
                sections.append("")
                sections.append(f"    APPLICATION: {irac['application']}")
                sections.append("")
                sections.append(f"    CONCLUSION: {irac['conclusion']}")
                sections.append("")

            # Relief requested
            sections.append("III. RELIEF REQUESTED")
            sections.append("")
            sections.append(
                "    WHEREFORE, Plaintiff respectfully requests that this "
                "Honorable Court:"
            )
            sections.append("    1. Deny Defendant's Motion in its entirety;")
            sections.append(
                "    2. Grant such other relief as the Court deems just "
                "and equitable."
            )
            sections.append("")
            sections.append(SIGNATURE_BLOCK.format(date=date_str))
            sections.append("")
            sections.append(CERTIFICATE_OF_SERVICE.format(date=date_str))

            document_text = "\n".join(sections)
        finally:
            conn.close()

        return {
            "document_text": document_text,
            "counter_arguments": counters,
            "evidence_used": all_evidence[:20],
            "authority_cited": all_authority[:15],
            "metadata": {
                "type": "motion_response",
                "case_number": case_num,
                "opposing_arguments_count": len(opposing_args),
                "counter_arguments_count": len(counters),
                "generated_at": datetime.now().isoformat(),
            },
        }

    # ══════════════════════════════════════════════════════════════════════
    # 4. RESPONSE TO BRIEF — MCR 7.212(G)/(H)
    # ══════════════════════════════════════════════════════════════════════

    def response_to_brief(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """
        Draft MCR 7.212(G) response or MCR 7.212(H) reply brief.

        params:
            opposing_arguments (list): Arguments from appellee brief
            brief_type (str):          'response' | 'reply'
            keywords (list|None):      Extra search terms
            cross_appeal_issues (list): Issues for cross-appeal identification
        """
        opposing_args = params.get("opposing_arguments", [])
        brief_type = params.get("brief_type", "reply")
        extra_kw = params.get("keywords", [])
        cross_issues = params.get("cross_appeal_issues", [])

        conn = self._conn()
        if not conn:
            return {"error": "Database unavailable"}

        try:
            counters: List[Dict] = []
            all_evidence: List[Dict] = []
            all_authority: List[Dict] = []

            for i, arg in enumerate(opposing_args, 1):
                arg_keywords = [w for w in arg.split() if len(w) > 4][:6]
                search_terms = arg_keywords + extra_kw

                evidence = self._search_evidence(conn, search_terms)
                all_evidence.extend(evidence)

                authority = self._search_authority(conn, search_terms)
                all_authority.extend(authority)

                # Find contradictions to appellee's claims
                contradictions = self._search_contradictions(conn, search_terms)

                counters.append({
                    "argument_number": i,
                    "appellee_argument": arg,
                    "irac": {
                        "issue": (
                            f"Whether the trial court erred as alleged by "
                            f"Appellee regarding '{arg[:100]}...'"
                        ),
                        "rule": self._format_authority_block(authority),
                        "application": (
                            f"Appellee's argument misstates the record. "
                            + self._format_evidence_block(evidence)
                            + (" Contradictions in Appellee's position: "
                               + "; ".join(
                                   c.get("description", "")[:100]
                                   for c in contradictions[:3]
                               ) if contradictions else "")
                        ),
                        "conclusion": (
                            f"The trial court's error stands unrebutted. "
                            f"Appellee's argument #{i} fails on the merits."
                        ),
                    },
                    "evidence_cited": evidence[:5],
                    "authority_cited": authority[:5],
                    "contradictions_found": contradictions[:5],
                })

            # Cross-appeal identification
            cross_appeal_analysis = []
            if cross_issues:
                for issue in cross_issues:
                    cross_appeal_analysis.append({
                        "issue": issue,
                        "assessment": (
                            "Review whether Appellee's brief raises new "
                            "issues that constitute a cross-appeal requiring "
                            "separate treatment under MCR 7.207(A)."
                        ),
                    })

            # Assemble reply brief
            date_str = _today_str()
            word_limit = RESPONSE_TYPES["brief_response"]["word_limit"]
            sections = [
                COA_CAPTION,
                "",
                "PLAINTIFF-APPELLANT'S REPLY BRIEF"
                if brief_type == "reply" else
                "PLAINTIFF-APPELLANT'S RESPONSE TO APPELLEE'S BRIEF",
                "=" * 60,
                "",
                "TABLE OF CONTENTS",
                "",
                "Table of Authorities ......................................... ii",
                "Reply Argument ................................................ 1",
                "Conclusion ................................................... --",
                "",
                "TABLE OF AUTHORITIES",
                "",
            ]

            # Authority table
            seen_auth: set = set()
            for auth in all_authority[:20]:
                ref = auth.get("rule_number", "")
                if ref and ref not in seen_auth:
                    seen_auth.add(ref)
                    title = auth.get("title", "")
                    sections.append(f"    {ref} — {title}")
            sections.append("")

            # Standard of review
            sections.append("STANDARD OF REVIEW")
            sections.append("")
            sections.append(
                "    Custody decisions are reviewed for abuse of discretion. "
                "MCL 722.28. Findings of fact are reviewed for clear error. "
                "MCR 2.613(C). Questions of law are reviewed de novo. "
                "Unpreserved constitutional issues are reviewed for plain "
                "error affecting substantial rights. People v Carines, "
                "460 Mich 750, 763 (1999)."
            )
            sections.append("")

            # Reply arguments
            sections.append("REPLY ARGUMENT")
            sections.append("")
            for counter in counters:
                sections.append(
                    f"  {counter['argument_number']}. "
                    f"RESPONSE TO APPELLEE'S ARGUMENT #{counter['argument_number']}"
                )
                sections.append("")
                irac = counter["irac"]
                sections.append(f"    {irac['issue']}")
                sections.append("")
                sections.append(f"    {irac['rule']}")
                sections.append("")
                sections.append(f"    {irac['application']}")
                sections.append("")
                sections.append(f"    {irac['conclusion']}")
                sections.append("")

            # Cross-appeal
            if cross_appeal_analysis:
                sections.append("CROSS-APPEAL IDENTIFICATION")
                sections.append("")
                for ca in cross_appeal_analysis:
                    sections.append(f"    - {ca['issue']}: {ca['assessment']}")
                sections.append("")

            # Conclusion
            sections.append("CONCLUSION")
            sections.append("")
            sections.append(
                "    For the foregoing reasons, Plaintiff-Appellant "
                "respectfully requests that this Honorable Court reverse "
                "the trial court's orders, vacate the custody and "
                "parenting time determinations made without required "
                "findings, and remand for proceedings consistent with "
                "MCL 722.23 and MCL 722.27a."
            )
            sections.append("")
            sections.append(SIGNATURE_BLOCK.format(date=date_str))
            sections.append("")
            sections.append(CERTIFICATE_OF_SERVICE.format(date=date_str))

            document_text = "\n".join(sections)
            word_count = len(document_text.split())
        finally:
            conn.close()

        return {
            "document_text": document_text,
            "counter_arguments": counters,
            "cross_appeal_analysis": cross_appeal_analysis,
            "evidence_used": all_evidence[:20],
            "authority_cited": all_authority[:15],
            "word_count": word_count,
            "word_limit": word_limit,
            "within_limit": word_count <= word_limit,
            "metadata": {
                "type": "brief_response",
                "brief_type": brief_type,
                "case_number": "366810",
                "generated_at": datetime.now().isoformat(),
            },
        }

    # ══════════════════════════════════════════════════════════════════════
    # 5. OBJECTION TO PROPOSED ORDER — MCR 2.602(B)(3)
    # ══════════════════════════════════════════════════════════════════════

    def objection_to_order(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """
        Draft objection to a proposed order under MCR 2.602(B)(3).

        params:
            proposed_order (str):      Text of the proposed order
            specific_defects (list):   List of identified defects
            case_lane (str):           'custody' | 'ppo'
            keywords (list|None):      Extra search terms
        """
        proposed_order = params.get("proposed_order", "")
        specific_defects = params.get("specific_defects", [])
        case_lane = params.get("case_lane", "custody")
        extra_kw = params.get("keywords", [])
        case_num = self.CASE_NUMBERS.get(case_lane, self.CASE_NUMBERS["default"])

        conn = self._conn()
        if not conn:
            return {"error": "Database unavailable"}

        try:
            # Auto-detect defects in proposed order text
            detected_defects = self._detect_order_defects(proposed_order)
            all_defects = specific_defects + [
                d["description"] for d in detected_defects
                if d["description"] not in specific_defects
            ]

            # Build objections
            objections: List[Dict] = []
            all_authority: List[Dict] = []

            for i, defect in enumerate(all_defects, 1):
                kw = [w for w in defect.split() if len(w) > 4][:5] + extra_kw
                authority = self._search_authority(conn, kw)
                all_authority.extend(authority)

                objections.append({
                    "objection_number": i,
                    "defect": defect,
                    "authority": self._format_authority_block(authority),
                    "proposed_correction": (
                        f"The proposed order should be modified to address: {defect}"
                    ),
                })

            # Assemble document
            date_str = _today_str()
            caption = CASE_CAPTION.format(case_number=case_num)
            sections = [
                caption,
                "",
                RESPONSE_TYPES["order_objection"]["title"],
                "=" * 60,
                "",
                "NOW COMES Plaintiff Andrew Pigors, appearing pro se, and",
                "pursuant to MCR 2.602(B)(3), hereby objects to the proposed",
                "order submitted by Defendant, and states as follows:",
                "",
                "I. IDENTIFICATION OF PROPOSED ORDER",
                "",
                f"    The proposed order at issue provides:",
                f"    \"{proposed_order[:500]}\"",
                "",
                "II. SPECIFIC OBJECTIONS",
                "",
            ]

            for obj in objections:
                sections.append(
                    f"    Objection #{obj['objection_number']}: {obj['defect']}"
                )
                sections.append(f"    Authority: {obj['authority']}")
                sections.append(f"    Correction: {obj['proposed_correction']}")
                sections.append("")

            sections.extend([
                "III. LEGAL STANDARD",
                "",
                "    MCR 2.602(B)(3) provides that within 7 days after",
                "    service of a proposed order, any other party may file",
                "    and serve written objections. The court must then settle",
                "    the order on reasonable notice.",
                "",
                "    An order must accurately reflect the court's decision.",
                "    MCR 2.602(A). Any proposed order that does not",
                "    accurately reflect the court's ruling, or that includes",
                "    provisions beyond the scope of the court's ruling, is",
                "    defective and should not be entered.",
                "",
                "IV. RELIEF REQUESTED",
                "",
                "    WHEREFORE, Plaintiff respectfully requests that this",
                "    Honorable Court:",
                "    1. Sustain Plaintiff's objections;",
                "    2. Decline to enter the proposed order as drafted;",
                "    3. Modify the order to correct the identified defects;",
                "    4. Schedule a hearing to settle the order if necessary.",
                "",
                SIGNATURE_BLOCK.format(date=date_str),
                "",
                CERTIFICATE_OF_SERVICE.format(date=date_str),
            ])

            document_text = "\n".join(sections)
        finally:
            conn.close()

        return {
            "document_text": document_text,
            "objections": objections,
            "detected_defects": detected_defects,
            "authority_cited": all_authority[:15],
            "metadata": {
                "type": "order_objection",
                "case_number": case_num,
                "defect_count": len(all_defects),
                "generated_at": datetime.now().isoformat(),
            },
        }

    # ══════════════════════════════════════════════════════════════════════
    # 6. FOC OBJECTION — MCL 552.507(5)
    # ══════════════════════════════════════════════════════════════════════

    def foc_objection(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """
        Draft objection to FOC recommendation under MCL 552.507(5).

        params:
            foc_recommendation (str):     Text of FOC recommendation
            specific_objections (list):   Specific objections to raise
            keywords (list|None):         Extra search terms
        """
        foc_rec = params.get("foc_recommendation", "")
        specific_obj = params.get("specific_objections", [])
        extra_kw = params.get("keywords", [])
        case_num = self.CASE_NUMBERS["custody"]

        conn = self._conn()
        if not conn:
            return {"error": "Database unavailable"}

        try:
            # Search for best-interest-factor evidence
            bif_evidence = self._search_bif_evidence(conn)

            # Build factual objections
            factual_objections: List[Dict] = []
            legal_objections: List[Dict] = []

            for i, obj in enumerate(specific_obj, 1):
                kw = [w for w in obj.split() if len(w) > 4][:5] + extra_kw
                evidence = self._search_evidence(conn, kw)
                authority = self._search_authority(conn, kw)

                if any(term in obj.lower() for term in [
                    "fact", "evidence", "record", "witness", "inaccurat"
                ]):
                    factual_objections.append({
                        "number": i,
                        "objection": obj,
                        "supporting_evidence": evidence[:3],
                    })
                else:
                    legal_objections.append({
                        "number": i,
                        "objection": obj,
                        "authority": authority[:3],
                    })

            # Assemble document
            date_str = _today_str()
            caption = CASE_CAPTION.format(case_number=case_num)
            sections = [
                caption,
                "",
                RESPONSE_TYPES["foc_objection"]["title"],
                "=" * 60,
                "",
                "NOW COMES Plaintiff Andrew Pigors, appearing pro se,",
                "and pursuant to MCL 552.507(5) and MCR 3.208, hereby",
                "objects to the Friend of the Court Recommendation dated",
                f"[DATE OF RECOMMENDATION], and requests a de novo hearing",
                "before the Court, and states as follows:",
                "",
                "I. TIMELINESS",
                "",
                "    This objection is timely filed within 21 days of",
                "    service of the FOC recommendation, as required by",
                "    MCL 552.507(5).",
                "",
                "II. REQUEST FOR DE NOVO HEARING",
                "",
                "    Pursuant to MCL 552.507(5), Plaintiff is entitled to",
                "    a de novo hearing before the Court on the matters",
                "    addressed in the FOC recommendation. Plaintiff hereby",
                "    requests such hearing.",
                "",
                "    'If either party timely objects, the court shall hold",
                "    a de novo hearing.' MCL 552.507(5).",
                "",
                "III. FOC RECOMMENDATION AT ISSUE",
                "",
                f"    {foc_rec[:500] if foc_rec else '[FOC RECOMMENDATION TEXT]'}",
                "",
                "IV. FACTUAL OBJECTIONS",
                "",
            ]

            if factual_objections:
                for fo in factual_objections:
                    sections.append(
                        f"    {fo['number']}. {fo['objection']}"
                    )
                    for ev in fo["supporting_evidence"]:
                        qt = ev.get("quote_text", "")[:150]
                        sections.append(f"        Evidence: \"{qt}\"")
                    sections.append("")
            else:
                sections.append("    [Specify factual inaccuracies in FOC recommendation]")
                sections.append("")

            sections.append("V. LEGAL OBJECTIONS")
            sections.append("")

            if legal_objections:
                for lo in legal_objections:
                    sections.append(
                        f"    {lo['number']}. {lo['objection']}"
                    )
                    for auth in lo["authority"]:
                        ref = auth.get("rule_number", "")
                        sections.append(f"        Authority: {ref}")
                    sections.append("")
            else:
                sections.append("    [Specify legal errors in FOC recommendation]")
                sections.append("")

            # Best interest factor analysis
            sections.append("VI. BEST INTEREST FACTOR ANALYSIS — MCL 722.23")
            sections.append("")
            sections.append(
                "    The FOC recommendation fails to properly weigh the"
            )
            sections.append(
                "    best interest factors required by MCL 722.23(a)-(l):"
            )
            sections.append("")

            bif_labels = {
                "a": "Love, affection, emotional ties",
                "b": "Capacity to provide love, affection, guidance",
                "c": "Capacity to provide food, clothing, medical care",
                "d": "Length of time in stable environment",
                "e": "Permanence of family unit",
                "f": "Moral fitness",
                "g": "Mental and physical health",
                "h": "Home, school, community record",
                "i": "Reasonable preference of child",
                "j": "Willingness to facilitate relationship",
                "k": "Domestic violence",
                "l": "Any other relevant factor",
            }

            for factor_key, label in bif_labels.items():
                factor_evidence = [
                    e for e in bif_evidence
                    if e.get("factor", "").lower().startswith(factor_key)
                ]
                ev_count = len(factor_evidence)
                sections.append(
                    f"    Factor ({factor_key}): {label} — "
                    f"{ev_count} evidence items"
                )
            sections.append("")

            sections.extend([
                "VII. RELIEF REQUESTED",
                "",
                "    WHEREFORE, Plaintiff respectfully requests that this",
                "    Honorable Court:",
                "    1. Sustain Plaintiff's objections to the FOC recommendation;",
                "    2. Schedule a de novo hearing per MCL 552.507(5);",
                "    3. Consider all best interest factors per MCL 722.23;",
                "    4. Grant such other relief as the Court deems just.",
                "",
                SIGNATURE_BLOCK.format(date=date_str),
                "",
                CERTIFICATE_OF_SERVICE.format(date=date_str),
            ])

            document_text = "\n".join(sections)
        finally:
            conn.close()

        return {
            "document_text": document_text,
            "factual_objections": factual_objections,
            "legal_objections": legal_objections,
            "bif_evidence_count": len(bif_evidence),
            "metadata": {
                "type": "foc_objection",
                "case_number": case_num,
                "generated_at": datetime.now().isoformat(),
            },
        }

    # ══════════════════════════════════════════════════════════════════════
    # 7. DISCOVERY RESPONSE — MCR 2.309-2.313
    # ══════════════════════════════════════════════════════════════════════

    def discovery_response(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """
        Draft responses to discovery requests with objections.

        params:
            discovery_requests (list):  List of dicts with 'number', 'text'
            request_type (str):         'interrogatory' | 'rfp' | 'rfa'
            objection_types (list):     Keys from DISCOVERY_OBJECTIONS to apply
            keywords (list|None):       Extra search terms
        """
        requests = params.get("discovery_requests", [])
        req_type = params.get("request_type", "interrogatory").upper()
        obj_types = params.get("objection_types", [])
        extra_kw = params.get("keywords", [])
        case_num = self.CASE_NUMBERS["custody"]

        conn = self._conn()
        if not conn:
            return {"error": "Database unavailable"}

        try:
            responses: List[Dict] = []

            for req in requests:
                req_num = req.get("number", 0)
                req_text = req.get("text", "")

                # Determine applicable objections
                applicable_objections = []
                for obj_key in obj_types:
                    if obj_key in DISCOVERY_OBJECTIONS:
                        applicable_objections.append(DISCOVERY_OBJECTIONS[obj_key])

                # Auto-detect objections if none specified
                if not applicable_objections:
                    applicable_objections = self._auto_detect_objections(req_text)

                # Search for relevant evidence to substantiate response
                kw = [w for w in req_text.split() if len(w) > 4][:5] + extra_kw
                evidence = self._search_evidence(conn, kw)

                responses.append({
                    "request_number": req_num,
                    "request_text": req_text,
                    "objections": applicable_objections,
                    "substantive_response": (
                        "Subject to and without waiving the foregoing "
                        "objections, Plaintiff responds as follows: "
                        "See supporting evidence below."
                    ),
                    "supporting_evidence": evidence[:5],
                })

            # Motion to compel template (if Watson's discovery is deficient)
            compel_template = {
                "title": "MOTION TO COMPEL DISCOVERY",
                "authority": "MCR 2.313(A)(1)",
                "good_faith_cert": (
                    "Plaintiff certifies that, in compliance with "
                    "MCR 2.313(A)(4), Plaintiff has in good faith "
                    "conferred or attempted to confer with Defendant "
                    "in an effort to secure disclosure without court action."
                ),
                "sanctions_authority": (
                    "MCR 2.313(A)(5) — The court shall require the party "
                    "whose conduct necessitated the motion to pay "
                    "reasonable expenses, including attorney fees."
                ),
            }

            # Assemble document
            date_str = _today_str()
            caption = CASE_CAPTION.format(case_number=case_num)
            sections = [
                caption,
                "",
                RESPONSE_TYPES["discovery_response"]["title"],
                "=" * 60,
                "",
                "NOW COMES Plaintiff Andrew Pigors, appearing pro se,",
                f"and responds to Defendant's {req_type} as follows:",
                "",
                "GENERAL OBJECTIONS",
                "",
                "    1. Plaintiff objects to each request to the extent it",
                "    seeks information protected by any applicable privilege,",
                "    including work product. MRE 501; MCR 2.302(B)(3).",
                "",
                "    2. Plaintiff objects to each request to the extent it",
                "    is overbroad, unduly burdensome, or not proportional to",
                "    the needs of the case. MCR 2.302(B)(1); MCR 2.302(C).",
                "",
                "    3. Plaintiff objects to each request to the extent it",
                "    seeks information already known to or in the possession",
                "    of Defendant.",
                "",
                "SPECIFIC RESPONSES",
                "",
            ]

            for resp in responses:
                sections.append(
                    f"    REQUEST NO. {resp['request_number']}:"
                )
                sections.append(f"    {resp['request_text'][:300]}")
                sections.append("")
                sections.append("    RESPONSE:")
                if resp["objections"]:
                    sections.append("    OBJECTION:")
                    for obj in resp["objections"]:
                        sections.append(
                            f"      {obj['text']} ({obj['authority']})"
                        )
                sections.append(f"    {resp['substantive_response']}")
                sections.append("")

            sections.extend([
                "",
                SIGNATURE_BLOCK.format(date=date_str),
                "",
                "VERIFICATION",
                "",
                "    I, Andrew Pigors, state under penalty of perjury that",
                "    the foregoing responses are true and correct to the best",
                "    of my knowledge, information, and belief.",
                "",
                "    ______________________________",
                f"    Andrew Pigors — Date: {date_str}",
                "",
                CERTIFICATE_OF_SERVICE.format(date=date_str),
            ])

            document_text = "\n".join(sections)
        finally:
            conn.close()

        return {
            "document_text": document_text,
            "responses": responses,
            "compel_template": compel_template,
            "metadata": {
                "type": "discovery_response",
                "request_type": req_type,
                "request_count": len(requests),
                "case_number": case_num,
                "generated_at": datetime.now().isoformat(),
            },
        }

    # ══════════════════════════════════════════════════════════════════════
    # 8. COUNTER-ARGUMENT GENERATOR
    # ══════════════════════════════════════════════════════════════════════

    def counter_arguments(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """
        Generate point-by-point rebuttals from DB evidence.

        Pulls from adversary_models (Watson/Berry predictions) and
        impeachment_items (strongest impeachment material).

        params:
            opposing_arguments (list):  Arguments to counter
            adversary (str):            'watson' | 'berry' | 'barnes'
            strength_threshold (int):   Min impeachment strength_score (0-100)
            keywords (list|None):       Extra search terms
        """
        opposing_args = params.get("opposing_arguments", [])
        adversary = params.get("adversary", "watson")
        threshold = params.get("strength_threshold", 50)
        extra_kw = params.get("keywords", [])

        conn = self._conn()
        if not conn:
            return {"error": "Database unavailable"}

        try:
            # Get adversary model predictions
            adversary_models = self._get_adversary_models(conn, adversary)

            # Get top impeachment items
            impeachment = self._get_top_impeachment(conn, threshold)

            # Generate rebuttals
            rebuttals: List[Dict] = []

            for i, arg in enumerate(opposing_args, 1):
                arg_lower = arg.lower()
                kw = [w for w in arg.split() if len(w) > 4][:6] + extra_kw

                # Match adversary predictions to this argument
                relevant_predictions = [
                    m for m in adversary_models
                    if any(k.lower() in str(m).lower() for k in kw[:3])
                ]

                # Find impeachment material for this argument
                relevant_impeachment = [
                    item for item in impeachment
                    if any(k.lower() in str(item).lower() for k in kw[:3])
                ]

                # Find direct evidence contradicting this argument
                evidence = self._search_evidence(conn, kw)

                # Find authority supporting our position
                authority = self._search_authority(conn, kw)

                # Find contradictions
                contradictions = self._search_contradictions(conn, kw)

                rebuttal = {
                    "argument_number": i,
                    "their_argument": arg,
                    "our_rebuttal": {
                        "summary": (
                            f"This argument fails because: "
                            + (evidence[0]["quote_text"][:150] if evidence
                               else "the record evidence contradicts this claim")
                        ),
                        "evidence": evidence[:5],
                        "authority": authority[:5],
                        "impeachment": relevant_impeachment[:3],
                        "contradictions": contradictions[:3],
                        "adversary_prediction": relevant_predictions[:2],
                    },
                    "strength_assessment": self._assess_rebuttal_strength(
                        evidence, authority, relevant_impeachment, contradictions
                    ),
                }
                rebuttals.append(rebuttal)

        finally:
            conn.close()

        return {
            "rebuttals": rebuttals,
            "adversary_models_used": len(adversary_models),
            "impeachment_items_available": len(impeachment),
            "summary": {
                "total_arguments": len(opposing_args),
                "strong_rebuttals": sum(
                    1 for r in rebuttals
                    if r["strength_assessment"]["overall"] >= 70
                ),
                "weak_rebuttals": sum(
                    1 for r in rebuttals
                    if r["strength_assessment"]["overall"] < 50
                ),
            },
            "metadata": {
                "type": "counter_arguments",
                "adversary": adversary,
                "strength_threshold": threshold,
                "generated_at": datetime.now().isoformat(),
            },
        }

    # ══════════════════════════════════════════════════════════════════════
    # INTERNAL — DB search helpers
    # ══════════════════════════════════════════════════════════════════════

    def _search_evidence(self, conn: sqlite3.Connection,
                         keywords: List[str], limit: int = 10) -> List[Dict]:
        """Search evidence_quotes by keywords. FTS5 with LIKE fallback."""
        results: List[Dict] = []
        if not keywords:
            return results

        # Try FTS5 first
        fts_term = " OR ".join(k for k in keywords if k)
        try:
            rows = conn.execute(
                "SELECT quote_text, speaker, legal_significance, "
                "evidence_category, source_type "
                "FROM evidence_quotes WHERE rowid IN "
                "(SELECT rowid FROM evidence_quotes_fts "
                "WHERE evidence_quotes_fts MATCH ?) "
                "LIMIT ?",
                (fts_term, limit),
            ).fetchall()
            results = [_row_to_dict(r) for r in rows]
        except sqlite3.OperationalError:
            pass

        # LIKE fallback
        if not results:
            try:
                clauses = " OR ".join(
                    ["quote_text LIKE ?"] * len(keywords)
                )
                params = [f"%{k}%" for k in keywords]
                params.append(limit)
                rows = conn.execute(
                    f"SELECT quote_text, speaker, legal_significance, "
                    f"evidence_category, source_type "
                    f"FROM evidence_quotes WHERE source_type='PDF_COURT_DOC' "
                    f"AND ({clauses}) LIMIT ?",
                    params,
                ).fetchall()
                results = [_row_to_dict(r) for r in rows]
            except Exception:
                pass

        return results

    def _search_authority(self, conn: sqlite3.Connection,
                          keywords: List[str], limit: int = 10) -> List[Dict]:
        """Search auth_rules by keywords. FTS5 with LIKE fallback."""
        results: List[Dict] = []
        if not keywords:
            return results

        fts_term = " OR ".join(k for k in keywords if k)
        try:
            rows = conn.execute(
                "SELECT rule_number, title, substr(full_text, 1, 500) as text "
                "FROM auth_rules WHERE rowid IN "
                "(SELECT rowid FROM auth_rules_fts "
                "WHERE auth_rules_fts MATCH ?) LIMIT ?",
                (fts_term, limit),
            ).fetchall()
            results = [_row_to_dict(r) for r in rows]
        except sqlite3.OperationalError:
            pass

        if not results:
            try:
                clauses = " OR ".join(
                    ["rule_number LIKE ? OR title LIKE ? OR full_text LIKE ?"]
                    * len(keywords)
                )
                params = []
                for k in keywords:
                    params.extend([f"%{k}%", f"%{k}%", f"%{k}%"])
                params.append(limit)
                rows = conn.execute(
                    f"SELECT rule_number, title, substr(full_text, 1, 500) as text "
                    f"FROM auth_rules WHERE {clauses} LIMIT ?",
                    params,
                ).fetchall()
                results = [_row_to_dict(r) for r in rows]
            except Exception:
                pass

        return results

    def _search_impeachment(self, conn: sqlite3.Connection,
                            keywords: List[str],
                            limit: int = 5) -> List[Dict]:
        """Search impeachment_items by keywords, ordered by strength."""
        results: List[Dict] = []
        if not keywords:
            return results
        try:
            clauses = " OR ".join(
                ["CAST(impeachment_items AS TEXT) LIKE ?"] * len(keywords)
            )
            params = [f"%{k}%" for k in keywords]
            params.append(limit)
            rows = conn.execute(
                f"SELECT * FROM impeachment_items "
                f"WHERE {clauses} "
                f"ORDER BY strength_score DESC LIMIT ?",
                params,
            ).fetchall()
            results = [_row_to_dict(r) for r in rows]
        except Exception:
            pass
        return results

    def _search_contradictions(self, conn: sqlite3.Connection,
                               keywords: List[str],
                               limit: int = 5) -> List[Dict]:
        """Search contradiction_map for relevant contradictions."""
        results: List[Dict] = []
        if not keywords:
            return results
        try:
            clauses = " OR ".join(
                ["description LIKE ? OR category LIKE ?"] * len(keywords)
            )
            params = []
            for k in keywords:
                params.extend([f"%{k}%", f"%{k}%"])
            params.append(limit)
            rows = conn.execute(
                f"SELECT * FROM contradiction_map "
                f"WHERE {clauses} LIMIT ?",
                params,
            ).fetchall()
            results = [_row_to_dict(r) for r in rows]
        except Exception:
            pass
        return results

    def _search_bif_evidence(self, conn: sqlite3.Connection,
                             limit: int = 50) -> List[Dict]:
        """Get best-interest-factor evidence from bif_evidence_links."""
        results: List[Dict] = []
        try:
            rows = conn.execute(
                "SELECT * FROM bif_evidence_links "
                "ORDER BY rowid DESC LIMIT ?",
                (limit,),
            ).fetchall()
            results = [_row_to_dict(r) for r in rows]
        except Exception:
            pass
        return results

    def _get_adversary_models(self, conn: sqlite3.Connection,
                              adversary: str) -> List[Dict]:
        """Get adversary model predictions for Watson/Berry/Barnes."""
        results: List[Dict] = []
        try:
            rows = conn.execute(
                "SELECT * FROM adversary_models "
                "WHERE model_type LIKE ? OR model_type LIKE ?",
                (f"%{adversary}%", f"%{adversary}%"),
            ).fetchall()
            results = [_row_to_dict(r) for r in rows]
        except Exception:
            pass
        return results

    def _get_top_impeachment(self, conn: sqlite3.Connection,
                             threshold: int = 50,
                             limit: int = 30) -> List[Dict]:
        """Get top impeachment items above strength threshold."""
        results: List[Dict] = []
        try:
            rows = conn.execute(
                "SELECT * FROM impeachment_items "
                "WHERE strength_score >= ? "
                "ORDER BY strength_score DESC LIMIT ?",
                (threshold, limit),
            ).fetchall()
            results = [_row_to_dict(r) for r in rows]
        except Exception:
            pass
        return results

    # ══════════════════════════════════════════════════════════════════════
    # INTERNAL — Formatting helpers
    # ══════════════════════════════════════════════════════════════════════

    def _format_authority_block(self, authority: List[Dict]) -> str:
        """Format authority list into citation block."""
        if not authority:
            return "[Authority search returned no results — manual citation required]"
        parts = []
        for a in authority[:5]:
            ref = a.get("rule_number", "")
            title = a.get("title", "")
            parts.append(f"{ref} — {title}" if title else ref)
        return "; ".join(parts)

    def _format_evidence_block(self, evidence: List[Dict]) -> str:
        """Format evidence list into narrative block."""
        if not evidence:
            return "[No matching evidence — supplement from record]"
        parts = []
        for e in evidence[:3]:
            qt = e.get("quote_text", "")[:150]
            speaker = e.get("speaker", "Record")
            parts.append(f"[{speaker}]: \"{qt}\"")
        return " ".join(parts)

    def _detect_order_defects(self, order_text: str) -> List[Dict]:
        """Auto-detect common defects in proposed orders."""
        defects: List[Dict] = []
        text_lower = order_text.lower()

        checks = [
            {
                "keywords": ["without hearing", "no hearing", "ex parte"],
                "description": "Order entered without hearing in violation of due process",
                "authority": "MCR 2.119(B); US Const Amend XIV",
            },
            {
                "keywords": ["no finding", "without finding", "fails to find"],
                "description": "Order lacks required findings of fact",
                "authority": "MCR 2.517(A)(1); MCL 722.27a(3)",
            },
            {
                "keywords": ["suspend", "terminat", "deny parenting", "no contact"],
                "description": "Order restricts parenting time without endangerment finding",
                "authority": "MCL 722.27a(3); MCL 722.27a(7)",
            },
            {
                "keywords": ["bond", "fee", "deposit", "payment required"],
                "description": "Order imposes financial barrier to court access",
                "authority": "Boddie v Connecticut, 401 US 371 (1971); MCR 2.002",
            },
            {
                "keywords": ["contempt", "sanction", "penalty"],
                "description": "Order imposes sanctions without required procedural safeguards",
                "authority": "MCR 3.606; In re Contempt of Dougherty, 429 Mich 81 (1987)",
            },
            {
                "keywords": ["sole custody", "change custody", "modify custody"],
                "description": "Order modifies custody without proper cause/change of circumstances",
                "authority": "MCL 722.27(1)(c); Vodvarka v Grasher, 259 Mich App 1 (2003)",
            },
        ]

        for check in checks:
            if any(kw in text_lower for kw in check["keywords"]):
                defects.append({
                    "description": check["description"],
                    "authority": check["authority"],
                    "matched_keywords": [
                        kw for kw in check["keywords"] if kw in text_lower
                    ],
                })

        return defects

    def _auto_detect_objections(self, request_text: str) -> List[Dict]:
        """Auto-detect applicable discovery objections from request text."""
        objections: List[Dict] = []
        text_lower = request_text.lower()

        if any(w in text_lower for w in ["all", "every", "any and all", "each"]):
            objections.append(DISCOVERY_OBJECTIONS["overbroad"])
        if any(w in text_lower for w in [
            "communications", "privilege", "attorney", "counsel", "work product"
        ]):
            objections.append(DISCOVERY_OBJECTIONS["privilege"])
        if len(request_text) > 300:
            objections.append(DISCOVERY_OBJECTIONS["burden"])
        if any(w in text_lower for w in [
            "embarrass", "harass", "intimate", "sexual", "personal"
        ]):
            objections.append(DISCOVERY_OBJECTIONS["harassment"])

        return objections if objections else [DISCOVERY_OBJECTIONS["relevance"]]

    def _assess_rebuttal_strength(
        self, evidence: List, authority: List,
        impeachment: List, contradictions: List,
    ) -> Dict[str, Any]:
        """Score rebuttal strength 0-100."""
        score = 0
        score += min(30, len(evidence) * 6)
        score += min(25, len(authority) * 5)
        score += min(25, len(impeachment) * 8)
        score += min(20, len(contradictions) * 5)
        return {
            "overall": min(100, score),
            "evidence_strength": min(30, len(evidence) * 6),
            "authority_strength": min(25, len(authority) * 5),
            "impeachment_strength": min(25, len(impeachment) * 8),
            "contradiction_strength": min(20, len(contradictions) * 5),
            "rating": (
                "STRONG" if score >= 70 else
                "MODERATE" if score >= 40 else
                "WEAK"
            ),
        }


# ── Self-test ─────────────────────────────────────────────────────────────────

def self_test() -> Dict[str, Any]:
    """Run diagnostics on ResponseDrafter skill."""
    results = {
        "skill": "response_drafter",
        "status": "ok",
        "tests": {},
    }
    drafter = ResponseDrafter()

    # Test DB connection
    conn = _get_db()
    results["tests"]["db_connection"] = "pass" if conn else "FAIL"
    if conn:
        conn.close()

    # Test calculate_deadline
    try:
        dl = drafter.calculate_deadline({
            "service_date": "2025-01-15",
            "service_method": "mail",
            "response_type": "motion_response",
        })
        results["tests"]["calculate_deadline"] = (
            f"pass (deadline={dl['deadline_date']}, "
            f"days={dl['total_days']})"
        )
    except Exception as e:
        results["tests"]["calculate_deadline"] = f"FAIL: {e}"

    # Test response_to_motion
    try:
        resp = drafter.response_to_motion({
            "opposing_arguments": [
                "Father has failed to comply with court orders",
                "Father's parenting time should remain suspended",
            ],
            "case_lane": "custody",
        })
        has_text = len(resp.get("document_text", "")) > 100
        results["tests"]["response_to_motion"] = (
            f"pass (doc_len={len(resp.get('document_text', ''))}, "
            f"counters={len(resp.get('counter_arguments', []))})"
            if has_text else "FAIL: document too short"
        )
    except Exception as e:
        results["tests"]["response_to_motion"] = f"FAIL: {e}"

    # Test response_to_brief
    try:
        resp = drafter.response_to_brief({
            "opposing_arguments": [
                "The trial court properly exercised its discretion",
            ],
            "brief_type": "reply",
        })
        results["tests"]["response_to_brief"] = (
            f"pass (words={resp.get('word_count', 0)}, "
            f"within_limit={resp.get('within_limit')})"
        )
    except Exception as e:
        results["tests"]["response_to_brief"] = f"FAIL: {e}"

    # Test objection_to_order
    try:
        resp = drafter.objection_to_order({
            "proposed_order": "IT IS ORDERED that parenting time is suspended without hearing",
            "case_lane": "custody",
        })
        results["tests"]["objection_to_order"] = (
            f"pass (defects={len(resp.get('detected_defects', []))})"
        )
    except Exception as e:
        results["tests"]["objection_to_order"] = f"FAIL: {e}"

    # Test foc_objection
    try:
        resp = drafter.foc_objection({
            "foc_recommendation": "FOC recommends sole custody to mother",
            "specific_objections": ["Factual inaccuracy: record shows equal parenting"],
        })
        results["tests"]["foc_objection"] = (
            f"pass (factual={len(resp.get('factual_objections', []))}, "
            f"legal={len(resp.get('legal_objections', []))})"
        )
    except Exception as e:
        results["tests"]["foc_objection"] = f"FAIL: {e}"

    # Test discovery_response
    try:
        resp = drafter.discovery_response({
            "discovery_requests": [
                {"number": 1, "text": "Produce all communications with your attorney"},
            ],
            "request_type": "rfp",
        })
        results["tests"]["discovery_response"] = (
            f"pass (responses={len(resp.get('responses', []))})"
        )
    except Exception as e:
        results["tests"]["discovery_response"] = f"FAIL: {e}"

    # Test counter_arguments
    try:
        resp = drafter.counter_arguments({
            "opposing_arguments": ["Father is unfit"],
            "adversary": "watson",
            "strength_threshold": 50,
        })
        results["tests"]["counter_arguments"] = (
            f"pass (rebuttals={len(resp.get('rebuttals', []))}, "
            f"models={resp.get('adversary_models_used', 0)})"
        )
    except Exception as e:
        results["tests"]["counter_arguments"] = f"FAIL: {e}"

    # Test draft_response (main entry)
    try:
        resp = drafter.draft_response({
            "type": "motion_response",
            "opposing_arguments": ["Test argument"],
            "service_date": "2025-01-15",
            "service_method": "mail",
        })
        has_deadline = "deadline_info" in resp
        results["tests"]["draft_response_dispatch"] = (
            "pass" if has_deadline else "FAIL: no deadline_info"
        )
    except Exception as e:
        results["tests"]["draft_response_dispatch"] = f"FAIL: {e}"

    # Overall status
    if any("FAIL" in str(v) for v in results["tests"].values()):
        results["status"] = "degraded"

    return results


# ── CLI ───────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    if len(sys.argv) > 1:
        cmd = sys.argv[1]
        drafter = ResponseDrafter()

        if cmd == "test":
            cycle_json(self_test())
        elif cmd == "deadline":
            # Usage: python response_drafter.py deadline 2025-01-15 mail motion_response
            service_date = sys.argv[2] if len(sys.argv) > 2 else None
            method = sys.argv[3] if len(sys.argv) > 3 else "mail"
            rtype = sys.argv[4] if len(sys.argv) > 4 else "motion_response"
            cycle_json(drafter.calculate_deadline({
                "service_date": service_date,
                "service_method": method,
                "response_type": rtype,
            }))
        elif cmd == "motion":
            # Usage: python response_drafter.py motion "arg1" "arg2" ...
            args = sys.argv[2:]
            cycle_json(drafter.response_to_motion({
                "opposing_arguments": args,
                "case_lane": "custody",
            }))
        elif cmd == "brief":
            args = sys.argv[2:]
            cycle_json(drafter.response_to_brief({
                "opposing_arguments": args,
                "brief_type": "reply",
            }))
        elif cmd == "order":
            text = " ".join(sys.argv[2:])
            cycle_json(drafter.objection_to_order({
                "proposed_order": text,
                "case_lane": "custody",
            }))
        elif cmd == "foc":
            text = " ".join(sys.argv[2:])
            cycle_json(drafter.foc_objection({
                "foc_recommendation": text,
            }))
        elif cmd == "counter":
            args = sys.argv[2:]
            cycle_json(drafter.counter_arguments({
                "opposing_arguments": args,
                "adversary": "watson",
            }))
        elif cmd == "types":
            cycle_json({
                k: {"title": v["title"], "authority": v["authority"],
                    "deadline_days": v["deadline_days"]}
                for k, v in RESPONSE_TYPES.items()
            })
        else:
            print(f"Unknown command: {cmd}", file=sys.stderr)
            print(
                "Commands: test, deadline, motion, brief, order, "
                "foc, counter, types"
            )
    else:
        print("Response Drafter — THE MANBEARPIG EPOCH v8.0")
        print("Usage:")
        print("  python response_drafter.py test")
        print("  python response_drafter.py deadline <date> <method> <type>")
        print("  python response_drafter.py motion 'arg1' 'arg2' ...")
        print("  python response_drafter.py brief 'arg1' 'arg2' ...")
        print("  python response_drafter.py order 'proposed order text'")
        print("  python response_drafter.py foc 'foc recommendation text'")
        print("  python response_drafter.py counter 'arg1' 'arg2' ...")
        print("  python response_drafter.py types")
