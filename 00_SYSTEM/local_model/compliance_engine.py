"""
Pro Se Compliance Engine — MBP LitigationOS 2026 v1.0
======================================================
Automated MCR/MCL compliance checking for court filings.
Catches procedural traps BEFORE filing. A missed requirement = case dismissed.

Designed for Andrew Pigors (pro se litigant) in Pigors v. Watson.
329+ days parent-child separation — every filing must be airtight.

Usage:
    engine = ComplianceEngine()
    report = engine.check_filing_compliance(text, "motion")
    score  = engine.score_filing_readiness("brief", text)
"""

import json
import os
import re
import sqlite3
import textwrap
from collections import OrderedDict
from datetime import datetime, timedelta

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

DB_PATH_DEFAULT = r"C:\Users\andre\LitigationOS\litigation_context.db"

# MCR 7.212(B) — page/word limits by filing type
PAGE_LIMITS = {
    "motion":              {"pages": 20,   "words": 8000},
    "brief":               {"pages": 50,   "words": 16000},
    "application_for_leave": {"pages": 50, "words": 16000},
    "response":            {"pages": 20,   "words": 8000},
    "reply":               {"pages": 10,   "words": 5000},
    "affidavit":           {"pages": None, "words": None},
    "complaint":           {"pages": None, "words": None},
}

# Statutory deadline rules (days, authority)
DEADLINE_RULES = {
    "claim_of_appeal":        {"days": 21, "authority": "MCR 7.204(A)(1)"},
    "cross_appeal":           {"days": 21, "authority": "MCR 7.207(A)(1)"},
    "motion_service":         {"days": 9,  "authority": "MCR 2.119(C)(1)",
                               "note": "Must be served at least 9 days before hearing"},
    "motion_response":        {"days": 7,  "authority": "MCR 2.119(C)(2)",
                               "note": "Response due 7 days before hearing"},
    "motion_for_reconsideration": {"days": 21, "authority": "MCR 2.119(F)(1)",
                                   "note": "Must be filed within 21 days of entry of order"},
    "summary_disposition":    {"days": 56, "authority": "MCR 2.116(B)(1)",
                               "note": "Motion for summary disposition, 56 days after close of discovery"},
    "appellate_brief":        {"days": 56, "authority": "MCR 7.212(A)(1)",
                               "note": "Appellant brief due 56 days after claim of appeal"},
    "appellee_brief":         {"days": 35, "authority": "MCR 7.212(A)(2)",
                               "note": "Appellee brief due 35 days after appellant brief served"},
    "reply_brief":            {"days": 21, "authority": "MCR 7.212(A)(3)"},
}

# MCR 2.107 service methods
SERVICE_METHODS = {
    "personal":  {"extra_days": 0, "authority": "MCR 2.107(C)(1)"},
    "mail":      {"extra_days": 3, "authority": "MCR 2.107(C)(3)",
                  "note": "Add 3 days when service is by mail (MCR 1.108(1))"},
    "email":     {"extra_days": 0, "authority": "MCR 2.107(C)(4)",
                  "note": "Only if party has consented to electronic service"},
    "fax":       {"extra_days": 0, "authority": "MCR 2.107(C)(4)"},
    "electronic": {"extra_days": 0, "authority": "MCR 2.107(C)(4)",
                   "note": "Via MiFILE or court-approved electronic service"},
}

# ---------------------------------------------------------------------------
# Regex patterns
# ---------------------------------------------------------------------------

_PAT_MCR = re.compile(r"MCR\s+\d+\.\d+(?:\([A-Za-z0-9]+\))*")
_PAT_MCL = re.compile(r"MCL\s+\d+\.\d+[a-z]*(?:\([A-Za-z0-9]+\))*")
_PAT_MRE = re.compile(r"MRE\s+\d+(?:\([A-Za-z0-9]+\))*")
_PAT_CASE = re.compile(
    r"[A-Z][A-Za-z\-'.]+\s+v\s+[A-Z][A-Za-z\-'.]+,?\s*\d+\s+(?:Mich|NW)"
)
_PAT_NUMBERED_PARA = re.compile(r"^\s*\d+\.\s+", re.MULTILINE)
_PAT_CAPTION_MARKERS = [
    re.compile(r"STATE\s+OF\s+MICHIGAN", re.IGNORECASE),
    re.compile(r"(?:CIRCUIT|DISTRICT|PROBATE|COURT\s+OF\s+APPEALS)", re.IGNORECASE),
    re.compile(r"Case\s+No\.?\s*[\d\-]+", re.IGNORECASE),
    re.compile(r"(?:Plaintiff|Petitioner|Appellant)", re.IGNORECASE),
    re.compile(r"(?:Defendant|Respondent|Appellee)", re.IGNORECASE),
]
_PAT_CERT_SERVICE = re.compile(
    r"CERTIFICATE\s+OF\s+SERVICE|PROOF\s+OF\s+SERVICE|hereby\s+certif(?:y|ies)\s+that",
    re.IGNORECASE,
)
_PAT_SIGNATURE = re.compile(
    r"(?:Respectfully\s+submitted|/s/|___+\s*\n|Signature|Date:)",
    re.IGNORECASE,
)
_PAT_PROPOSED_ORDER = re.compile(
    r"PROPOSED\s+ORDER|ORDER\s+(?:GRANTING|DENYING)|IT\s+IS\s+(?:HEREBY\s+)?ORDERED",
    re.IGNORECASE,
)
_PAT_VERIFICATION = re.compile(
    r"VERIFICATION|under\s+(?:penalty\s+of\s+)?perjury|sworn\s+(?:to|and\s+subscribed)",
    re.IGNORECASE,
)
_PAT_FONT_REF = re.compile(r"12[- ]?point|Times\s+New\s+Roman", re.IGNORECASE)
_PAT_SPACING_REF = re.compile(r"double[- ]?spac", re.IGNORECASE)
_PAT_FILING_FEE = re.compile(r"filing\s+fee|\$\d+(?:\.\d{2})?", re.IGNORECASE)

# Appellate brief sections (MCR 7.212)
_APPELLATE_SECTIONS = OrderedDict([
    ("table_of_contents",
     re.compile(r"TABLE\s+OF\s+CONTENTS", re.IGNORECASE)),
    ("table_of_authorities",
     re.compile(r"TABLE\s+OF\s+AUTHORITIES", re.IGNORECASE)),
    ("statement_of_jurisdiction",
     re.compile(r"(?:STATEMENT\s+OF\s+)?JURISDICTION", re.IGNORECASE)),
    ("questions_presented",
     re.compile(r"(?:STATEMENT\s+OF\s+)?QUESTIONS?\s+PRESENTED", re.IGNORECASE)),
    ("statement_of_facts",
     re.compile(r"STATEMENT\s+OF\s+FACTS", re.IGNORECASE)),
    ("standard_of_review",
     re.compile(r"STANDARD(?:S)?\s+OF\s+REVIEW", re.IGNORECASE)),
    ("argument",
     re.compile(r"^(?:I+V?|ARGUMENT)", re.IGNORECASE | re.MULTILINE)),
    ("relief_requested",
     re.compile(r"RELIEF\s+REQUESTED|CONCLUSION|PRAYER\s+FOR\s+RELIEF", re.IGNORECASE)),
])


# ---------------------------------------------------------------------------
# Compliance Engine
# ---------------------------------------------------------------------------

class ComplianceEngine:
    """
    Automated MCR/MCL compliance checking for Michigan court filings.

    Validates formatting, deadlines, service requirements, appellate rules,
    and issue preservation. Designed to protect a pro se litigant from
    procedural dismissal.
    """

    def __init__(self, db_path=None):
        self._db_path = db_path or os.environ.get(
            "LITIGATION_DB_PATH", DB_PATH_DEFAULT
        )
        self._conn = None
        self._error_log = []

    # ------------------------------------------------------------------
    # DB helpers
    # ------------------------------------------------------------------

    def _get_conn(self):
        """Return a reusable connection with WAL mode and read-only pragma."""
        if self._conn is not None:
            try:
                self._conn.execute("SELECT 1")
                return self._conn
            except Exception:
                self._conn = None
        retries = 3
        for attempt in range(retries):
            try:
                conn = sqlite3.connect(self._db_path, timeout=10)
                conn.execute("PRAGMA journal_mode=WAL")
                conn.execute("PRAGMA query_only=ON")
                conn.row_factory = sqlite3.Row
                self._conn = conn
                return conn
            except sqlite3.Error as exc:
                wait = 2 ** attempt
                self._error_log.append(
                    f"DB connect attempt {attempt+1}/{retries} failed: {exc}"
                )
                import time
                time.sleep(wait)
        raise RuntimeError(
            f"Failed to connect to {self._db_path} after {retries} attempts"
        )

    def _query(self, sql, params=()):
        """Execute a read query with error handling."""
        try:
            conn = self._get_conn()
            cur = conn.execute(sql, params)
            return cur.fetchall()
        except sqlite3.Error as exc:
            self._error_log.append(f"Query failed: {exc} | SQL: {sql[:120]}")
            return []

    def _query_fts(self, table, match_term, limit=20):
        """Full-text search helper."""
        sql = f"SELECT * FROM {table} WHERE {table} MATCH ? LIMIT ?"
        return self._query(sql, (match_term, limit))

    def _lookup_rule(self, rule_number):
        """Look up a specific rule from auth_rules."""
        rows = self._query(
            "SELECT rule_number, title, full_text, rule_type "
            "FROM auth_rules WHERE rule_number = ?",
            (rule_number,),
        )
        if rows:
            r = rows[0]
            return {
                "rule_number": r["rule_number"],
                "title": r["title"],
                "full_text": r["full_text"],
                "rule_type": r["rule_type"],
            }
        return None

    # ------------------------------------------------------------------
    # 1. check_filing_compliance
    # ------------------------------------------------------------------

    def check_filing_compliance(self, document_text, filing_type="motion"):
        """
        Validate a filing against MCR requirements.

        Returns a compliance report dict with pass/fail for each check,
        overall compliance bool, and remediation notes.
        """
        filing_type = filing_type.lower().strip()
        text = document_text or ""
        word_count = len(text.split())
        # Rough page estimate: ~250 words/page double-spaced
        page_estimate = max(1, word_count // 250)

        checks = {}

        # 1. Caption (MCR 2.113(A))
        caption_hits = sum(
            1 for pat in _PAT_CAPTION_MARKERS if pat.search(text)
        )
        checks["caption"] = {
            "pass": caption_hits >= 3,
            "authority": "MCR 2.113(A)",
            "detail": (
                f"Caption elements found: {caption_hits}/5 "
                "(need STATE OF MICHIGAN, court, case no., parties, title)"
            ),
            "severity": "critical",
        }

        # 2. Certificate of Service (MCR 2.107)
        has_cert = bool(_PAT_CERT_SERVICE.search(text))
        checks["certificate_of_service"] = {
            "pass": has_cert,
            "authority": "MCR 2.107(A)",
            "detail": (
                "Certificate of Service detected"
                if has_cert
                else "MISSING Certificate of Service — filing may be stricken"
            ),
            "severity": "critical",
        }

        # 3. Signature block
        has_sig = bool(_PAT_SIGNATURE.search(text))
        checks["signature_block"] = {
            "pass": has_sig,
            "authority": "MCR 2.114(A)",
            "detail": (
                "Signature block detected"
                if has_sig
                else "MISSING signature block — filing is incomplete"
            ),
            "severity": "critical",
        }

        # 4. Numbered paragraphs (motions, complaints)
        need_numbered = filing_type in ("motion", "complaint", "response")
        num_paras = len(_PAT_NUMBERED_PARA.findall(text))
        checks["numbered_paragraphs"] = {
            "pass": (not need_numbered) or num_paras >= 2,
            "authority": "MCR 2.113(B)",
            "detail": f"{num_paras} numbered paragraphs found",
            "severity": "warning" if need_numbered else "info",
        }

        # 5. Citations present
        mcr_cites = _PAT_MCR.findall(text)
        mcl_cites = _PAT_MCL.findall(text)
        mre_cites = _PAT_MRE.findall(text)
        case_cites = _PAT_CASE.findall(text)
        total_cites = len(mcr_cites) + len(mcl_cites) + len(mre_cites) + len(case_cites)
        checks["citations_present"] = {
            "pass": total_cites >= 1,
            "authority": "General practice requirement",
            "detail": (
                f"MCR: {len(mcr_cites)}, MCL: {len(mcl_cites)}, "
                f"MRE: {len(mre_cites)}, Case law: {len(case_cites)}"
            ),
            "severity": "critical",
        }

        # 6. Word/page count limits
        limits = PAGE_LIMITS.get(filing_type, PAGE_LIMITS.get("motion"))
        page_ok = limits["pages"] is None or page_estimate <= limits["pages"]
        word_ok = limits["words"] is None or word_count <= limits["words"]
        checks["page_word_limits"] = {
            "pass": page_ok and word_ok,
            "authority": "MCR 7.212(B)" if filing_type == "brief" else "Local practice",
            "detail": (
                f"Words: {word_count}"
                + (f"/{limits['words']}" if limits["words"] else "")
                + f", Pages (est): {page_estimate}"
                + (f"/{limits['pages']}" if limits["pages"] else "")
            ),
            "severity": "warning",
        }

        # 7. Formatting references
        has_font = bool(_PAT_FONT_REF.search(text))
        has_spacing = bool(_PAT_SPACING_REF.search(text))
        checks["formatting"] = {
            "pass": True,  # informational — can't truly validate from plain text
            "authority": "MCR 2.113(C)(1)",
            "detail": (
                f"Font reference: {'yes' if has_font else 'not detected'}, "
                f"Double-spacing reference: {'yes' if has_spacing else 'not detected'}"
            ),
            "severity": "info",
        }

        # 8. Verification/affidavit (if required)
        needs_verification = filing_type in ("affidavit", "complaint")
        has_verification = bool(_PAT_VERIFICATION.search(text))
        checks["verification"] = {
            "pass": (not needs_verification) or has_verification,
            "authority": "MCR 2.114(A)",
            "detail": (
                "Verification/affidavit language detected"
                if has_verification
                else ("MISSING verification — required for " + filing_type)
                if needs_verification
                else "Verification not required for this filing type"
            ),
            "severity": "critical" if needs_verification else "info",
        }

        # 9. Proposed order (for motions)
        needs_order = filing_type in ("motion",)
        has_order = bool(_PAT_PROPOSED_ORDER.search(text))
        checks["proposed_order"] = {
            "pass": (not needs_order) or has_order,
            "authority": "MCR 2.119(A)(2)",
            "detail": (
                "Proposed order language detected"
                if has_order
                else "MISSING proposed order — required with motions"
                if needs_order
                else "Proposed order not required for this filing type"
            ),
            "severity": "warning" if needs_order else "info",
        }

        # 10. Filing fee reference
        has_fee_ref = bool(_PAT_FILING_FEE.search(text))
        checks["filing_fee"] = {
            "pass": True,  # informational
            "authority": "MCL 600.880x series",
            "detail": (
                "Filing fee reference detected"
                if has_fee_ref
                else "No filing fee reference — confirm fee paid separately"
            ),
            "severity": "info",
        }

        # --- Aggregate ---
        critical_failures = [
            k for k, v in checks.items()
            if not v["pass"] and v["severity"] == "critical"
        ]
        warning_failures = [
            k for k, v in checks.items()
            if not v["pass"] and v["severity"] == "warning"
        ]
        overall = len(critical_failures) == 0

        return {
            "compliant": overall,
            "filing_type": filing_type,
            "checks": checks,
            "critical_failures": critical_failures,
            "warnings": warning_failures,
            "word_count": word_count,
            "page_estimate": page_estimate,
            "citation_count": total_cites,
            "remediation": [
                f"FIX ({checks[k]['severity'].upper()}): {k} — {checks[k]['detail']}"
                for k in critical_failures + warning_failures
            ],
        }

    # ------------------------------------------------------------------
    # 2. check_deadline_compliance
    # ------------------------------------------------------------------

    def check_deadline_compliance(self, filing_type, case_lane=None):
        """
        Check if a filing would be timely.

        Queries the deadlines table and cross-references statutory deadline
        rules. Returns compliance assessment with days remaining.
        """
        filing_type_key = filing_type.lower().strip().replace(" ", "_")
        today = datetime.now().date()
        result = {
            "compliant": None,
            "filing_type": filing_type,
            "case_lane": case_lane,
            "deadline": None,
            "days_remaining": None,
            "authority": None,
            "db_deadlines": [],
            "statutory_rule": None,
            "warnings": [],
        }

        # Check statutory rule
        rule = DEADLINE_RULES.get(filing_type_key)
        if rule:
            result["statutory_rule"] = rule
            result["authority"] = rule["authority"]

        # Query DB for active deadlines
        if case_lane:
            rows = self._query(
                "SELECT deadline_id, title, due_date_iso, basis_authority, "
                "risk_if_missed, status FROM deadlines "
                "WHERE case_id LIKE ? AND status != 'completed' "
                "ORDER BY due_date_iso ASC",
                (f"%{case_lane}%",),
            )
        else:
            rows = self._query(
                "SELECT deadline_id, title, due_date_iso, basis_authority, "
                "risk_if_missed, status FROM deadlines "
                "WHERE status != 'completed' ORDER BY due_date_iso ASC",
            )

        # Match deadlines to filing type
        for row in rows:
            title_lower = row["title"].lower() if row["title"] else ""
            if filing_type_key.replace("_", " ") in title_lower or (
                filing_type.lower() in title_lower
            ):
                try:
                    due = datetime.strptime(
                        row["due_date_iso"][:10], "%Y-%m-%d"
                    ).date()
                except (ValueError, TypeError):
                    continue
                days_rem = (due - today).days
                entry = {
                    "deadline_id": row["deadline_id"],
                    "title": row["title"],
                    "due_date": row["due_date_iso"],
                    "authority": row["basis_authority"],
                    "risk_if_missed": row["risk_if_missed"],
                    "days_remaining": days_rem,
                    "status": row["status"],
                }
                result["db_deadlines"].append(entry)
                # Use the nearest deadline
                if result["deadline"] is None or due < datetime.strptime(
                    result["deadline"], "%Y-%m-%d"
                ).date():
                    result["deadline"] = row["due_date_iso"][:10]
                    result["days_remaining"] = days_rem
                    result["compliant"] = days_rem >= 0
                    if row["basis_authority"]:
                        result["authority"] = row["basis_authority"]

        # Add warnings for tight deadlines
        if result["days_remaining"] is not None:
            if result["days_remaining"] < 0:
                result["warnings"].append(
                    f"EXPIRED: Deadline passed {abs(result['days_remaining'])} days ago"
                )
            elif result["days_remaining"] <= 3:
                result["warnings"].append(
                    f"URGENT: Only {result['days_remaining']} days remaining — "
                    "account for service time (MCR 1.108)"
                )
            elif result["days_remaining"] <= 7:
                result["warnings"].append(
                    f"CAUTION: {result['days_remaining']} days remaining — "
                    "add 3 days if serving by mail"
                )

        # MCR 2.108 time computation note
        result["time_computation_note"] = (
            "MCR 2.108: Exclude day of event, include last day. "
            "If last day is weekend/holiday, deadline extends to next business day. "
            "Add 3 days if served by mail (MCR 1.108(1))."
        )

        if result["compliant"] is None:
            result["compliant"] = True  # No matching deadline found — not overdue
            result["warnings"].append(
                "No specific deadline found in DB for this filing type. "
                "Verify manually against docket."
            )

        return result

    # ------------------------------------------------------------------
    # 3. check_service_requirements
    # ------------------------------------------------------------------

    def check_service_requirements(self, filing_type, service_method="mail"):
        """
        MCR 2.107 service rules checklist.

        Returns requirements for the specified service method including
        who must be served, timing adjustments, and proof requirements.
        """
        filing_type = filing_type.lower().strip()
        service_method = service_method.lower().strip()

        method_info = SERVICE_METHODS.get(
            service_method, SERVICE_METHODS["mail"]
        )

        # Query DB for MCR 2.107 text
        rule_text = None
        rule_data = self._lookup_rule("2.107")
        if rule_data:
            rule_text = rule_data.get("full_text", "")

        checklist = {
            "filing_type": filing_type,
            "service_method": service_method,
            "authority": method_info["authority"],
            "extra_days": method_info["extra_days"],
            "requirements": [],
            "proof_of_service": [],
            "rule_text_excerpt": (
                rule_text[:500] + "..." if rule_text and len(rule_text) > 500
                else rule_text
            ),
        }

        # Core service requirements
        checklist["requirements"] = [
            {
                "item": "Serve all parties of record",
                "authority": "MCR 2.107(A)",
                "detail": "Every party who has appeared in the action must be served",
            },
            {
                "item": f"Service by {service_method}",
                "authority": method_info["authority"],
                "detail": method_info.get("note", f"Service via {service_method}"),
            },
            {
                "item": "Serve copy of filing",
                "authority": "MCR 2.107(A)",
                "detail": "A copy of every document filed must be served on all parties",
            },
        ]

        if service_method == "mail":
            checklist["requirements"].append({
                "item": "Add 3 days to response deadline",
                "authority": "MCR 1.108(1)",
                "detail": (
                    "When service is by mail, 3 days are added to any "
                    "prescribed period after service"
                ),
            })
        elif service_method == "email":
            checklist["requirements"].append({
                "item": "Confirm written consent for email service",
                "authority": "MCR 2.107(C)(4)",
                "detail": (
                    "Electronic service requires prior written consent "
                    "of the party to be served"
                ),
            })

        # Motion-specific service timing
        if filing_type == "motion":
            checklist["requirements"].append({
                "item": "Serve at least 9 days before hearing",
                "authority": "MCR 2.119(C)(1)",
                "detail": (
                    "Notice of hearing and motion must be served at least "
                    "9 days before the hearing date"
                ),
            })

        # Proof of service requirements
        checklist["proof_of_service"] = [
            {
                "item": "Name of person served",
                "authority": "MCR 2.104(A)(2)",
            },
            {
                "item": "Date of service",
                "authority": "MCR 2.104(A)(2)",
            },
            {
                "item": "Method of service",
                "authority": "MCR 2.104(A)(2)",
            },
            {
                "item": "Address where served (if by mail)",
                "authority": "MCR 2.104(A)(2)",
            },
            {
                "item": "Signed by person making service",
                "authority": "MCR 2.104(A)(2)",
            },
        ]

        return checklist

    # ------------------------------------------------------------------
    # 4. check_appellate_compliance
    # ------------------------------------------------------------------

    def check_appellate_compliance(self, document_text):
        """
        Check compliance with MCR 7.212 appellate brief requirements.

        Validates presence of all required sections and returns detailed
        findings for each.
        """
        text = document_text or ""
        sections = {}
        missing = []

        for section_name, pattern in _APPELLATE_SECTIONS.items():
            found = bool(pattern.search(text))
            sections[section_name] = {
                "present": found,
                "required": True,
            }
            if not found:
                missing.append(section_name)

        # Check for record citations in statement of facts
        # Pattern: (Record, p XX) or (Tr, p XX) or (App, p XX)
        record_cite_pat = re.compile(
            r"\(\s*(?:Record|Tr|App|Appendix|Exhibit)\s*[,.]?\s*p(?:p)?\.?\s*\d+",
            re.IGNORECASE,
        )
        has_record_cites = bool(record_cite_pat.search(text))
        sections["record_citations_in_facts"] = {
            "present": has_record_cites,
            "required": True,
        }
        if not has_record_cites:
            missing.append("record_citations_in_facts")

        # Check appendix reference
        appendix_pat = re.compile(r"APPENDIX|App(?:endix)?\s+[A-Z0-9]", re.IGNORECASE)
        has_appendix = bool(appendix_pat.search(text))
        sections["appendix"] = {
            "present": has_appendix,
            "required": True,
        }
        if not has_appendix:
            missing.append("appendix")

        # MCR 7.212(C)(4) — Questions Presented must be separately stated
        qp_section = sections.get("questions_presented", {})
        questions_count = 0
        if qp_section.get("present"):
            # Count questions by looking for numbered items or "Did the..."/"Whether..."
            qp_match = re.search(
                r"QUESTIONS?\s+PRESENTED(.*?)(?=TABLE|STATEMENT|STANDARD|ARGUMENT|\Z)",
                text, re.IGNORECASE | re.DOTALL,
            )
            if qp_match:
                qp_text = qp_match.group(1)
                questions_count = max(
                    len(re.findall(r"^\s*(?:\d+[.):]|[IVX]+[.)])\s+", qp_text, re.MULTILINE)),
                    len(re.findall(r"(?:Did|Whether|Is|Was|Does|Should|May|Can)\b", qp_text, re.IGNORECASE)),
                )

        total = len(sections)
        present = sum(1 for v in sections.values() if v["present"])

        return {
            "compliant": len(missing) == 0,
            "authority": "MCR 7.212",
            "sections": sections,
            "missing_sections": missing,
            "sections_present": present,
            "sections_total": total,
            "questions_presented_count": questions_count,
            "remediation": [
                f"ADD: {s.replace('_', ' ').title()} — required by MCR 7.212"
                for s in missing
            ],
            "notes": [
                "MCR 7.212(C)(4): Each question presented must be separately stated",
                "MCR 7.212(C)(6): Statement of facts must cite the record",
                "MCR 7.212(C)(7): Argument must include standard of review for each issue",
                "MCR 7.212(B): Brief limited to 50 pages or 16,000 words",
            ],
        }

    # ------------------------------------------------------------------
    # 5. detect_procedural_traps
    # ------------------------------------------------------------------

    def detect_procedural_traps(self):
        """
        Scan for common pro se procedural traps.

        Queries the database for known issues and returns a list of
        potential traps with explanations and cures.
        """
        traps = []

        # Trap 1: Failure to preserve issues for appeal
        traps.append({
            "trap": "Failure to preserve issues for appeal",
            "authority": "MCR 2.517; People v Carines, 460 Mich 750 (1999)",
            "explanation": (
                "An issue not raised in the trial court is generally not "
                "preserved for appellate review. Objections must be timely "
                "and specific."
            ),
            "cure": (
                "File a motion for reconsideration within 21 days (MCR 2.119(F)(1)) "
                "raising all issues. If past that window, argue plain error under "
                "People v Carines: (1) error occurred, (2) error was plain/obvious, "
                "(3) error affected substantial rights, (4) error seriously affected "
                "fairness/integrity of proceedings."
            ),
            "severity": "critical",
        })

        # Trap 2: Failure to exhaust administrative remedies
        traps.append({
            "trap": "Failure to exhaust administrative remedies",
            "authority": "MCL 552.507(5); MCR 3.208",
            "explanation": (
                "In family law, FOC recommendations must be objected to "
                "within 21 days. Failure to object = waiver."
            ),
            "cure": (
                "File timely objection to FOC recommendation. If deadline "
                "passed, file motion to set aside based on good cause or "
                "irregularity under MCR 2.612."
            ),
            "severity": "critical",
        })

        # Trap 3: Wrong court/forum
        traps.append({
            "trap": "Filing in wrong court or forum",
            "authority": "MCR 2.221 (venue); MCL 600.1629 (jurisdiction)",
            "explanation": (
                "Filing in wrong court wastes time and filing fees. "
                "Family matters: circuit court. Appeals: Court of Appeals. "
                "Judicial misconduct: Judicial Tenure Commission."
            ),
            "cure": (
                "Verify venue and jurisdiction before filing. Check "
                "MCR 2.221 for venue rules, MCL 600.1629 for jurisdiction."
            ),
            "severity": "warning",
        })

        # Trap 4: Failure to request oral argument
        traps.append({
            "trap": "Failure to request oral argument when beneficial",
            "authority": "MCR 2.119(E)",
            "explanation": (
                "Court may decide motions without oral argument. If you "
                "want to be heard, you must request it. Pro se litigants "
                "benefit from oral argument to explain their position."
            ),
            "cure": (
                "Include 'Oral argument is requested' in the motion or "
                "file a separate request for oral argument."
            ),
            "severity": "warning",
        })

        # Trap 5: Missing mandatory disclosures
        traps.append({
            "trap": "Missing mandatory disclosures in family law",
            "authority": "MCR 3.206(B); SCAO forms",
            "explanation": (
                "Family law filings often require verified financial "
                "statements, UCCJEA declarations, and other mandatory "
                "disclosures. Missing these = delays or sanctions."
            ),
            "cure": (
                "Attach all required SCAO forms. For custody: UCCJEA "
                "affidavit (MCL 722.1209). For support: verified income "
                "information (MCR 3.206(B))."
            ),
            "severity": "critical",
        })

        # Trap 6: Improper motion practice
        traps.append({
            "trap": "Raising new issues in reply brief",
            "authority": "MCR 2.119(C)(2); Blazer Foods v Restaurant Props, 259 Mich App 241 (2003)",
            "explanation": (
                "A reply brief may only address issues raised in the "
                "response. New arguments in a reply brief are improper "
                "and may be stricken."
            ),
            "cure": (
                "Confine reply to rebutting response arguments. If new "
                "issues are necessary, file a supplemental motion with "
                "leave of court."
            ),
            "severity": "warning",
        })

        # Trap 7: Service timing errors
        traps.append({
            "trap": "Insufficient service time before hearing",
            "authority": "MCR 2.119(C)(1)",
            "explanation": (
                "Motion and notice of hearing must be served at least "
                "9 days before hearing. By mail add 3 days = 12 days. "
                "Failure = adjournment or motion denied."
            ),
            "cure": (
                "Count backwards from hearing date: 9 days for personal/"
                "electronic service, 12 days for mail service. File and "
                "serve early."
            ),
            "severity": "critical",
        })

        # Trap 8: Failure to file claim of appeal timely
        traps.append({
            "trap": "Missing 21-day claim of appeal deadline",
            "authority": "MCR 7.204(A)(1)",
            "explanation": (
                "A claim of appeal must be filed within 21 days of entry "
                "of the order being appealed. This deadline is jurisdictional "
                "and cannot be extended."
            ),
            "cure": (
                "If within 21 days: file claim of appeal immediately. "
                "If past 21 days: file application for delayed appeal "
                "under MCR 7.205(F) showing good cause."
            ),
            "severity": "critical",
        })

        # Check DB for additional gaps/risks
        try:
            gap_rows = self._query(
                "SELECT gap_type, description, severity, resolution_status "
                "FROM gap_tickets WHERE resolution_status != 'resolved' "
                "ORDER BY severity DESC LIMIT 10"
            )
            for row in gap_rows:
                traps.append({
                    "trap": f"Open gap: {row['description'][:100]}",
                    "authority": "Internal gap analysis",
                    "explanation": row["description"],
                    "cure": "Address gap per gap_tickets table",
                    "severity": row["severity"] or "warning",
                    "source": "gap_tickets",
                })
        except Exception:
            pass  # gap_tickets may not exist

        try:
            risk_rows = self._query(
                "SELECT risk_class, severity, title "
                "FROM risk_events WHERE severity IN ('high', 'critical') "
                "ORDER BY severity DESC LIMIT 5"
            )
            for row in risk_rows:
                traps.append({
                    "trap": f"Risk: {row['title'][:100]}",
                    "authority": "Internal risk assessment",
                    "explanation": f"{row['risk_class']}: {row['title']}",
                    "cure": "Review risk_events table for mitigation steps",
                    "severity": row["severity"] or "warning",
                    "source": "risk_events",
                })
        except Exception:
            pass  # risk_events may not exist

        return {
            "traps_detected": len(traps),
            "critical": [t for t in traps if t["severity"] == "critical"],
            "warnings": [t for t in traps if t["severity"] == "warning"],
            "traps": traps,
        }

    # ------------------------------------------------------------------
    # 6. generate_compliance_checklist
    # ------------------------------------------------------------------

    def generate_compliance_checklist(self, filing_type):
        """
        Generate a filing-specific compliance checklist.

        Returns an ordered checklist of required elements for the
        specified filing type.
        """
        filing_type = filing_type.lower().strip()

        checklists = {
            "motion": [
                {"item": "Caption (MCR 2.113(A))", "detail":
                    "STATE OF MICHIGAN, court name, case number, parties, document title",
                    "authority": "MCR 2.113(A)", "required": True},
                {"item": "Title of Motion", "detail":
                    "Clear title (e.g., PLAINTIFF'S MOTION TO COMPEL DISCOVERY)",
                    "authority": "MCR 2.113(A)", "required": True},
                {"item": "Statement of Issues", "detail":
                    "Concise statement of the issue(s) presented",
                    "authority": "MCR 2.119(A)(2)", "required": True},
                {"item": "Statement of Facts", "detail":
                    "Relevant facts in numbered paragraphs with citations",
                    "authority": "MCR 2.113(B)", "required": True},
                {"item": "Argument (IRAC)", "detail":
                    "Issue, Rule, Application, Conclusion for each argument",
                    "authority": "General practice", "required": True},
                {"item": "Relief Requested", "detail":
                    "Specific relief sought from the court",
                    "authority": "General practice", "required": True},
                {"item": "Oral Argument Request", "detail":
                    "'Oral argument is requested' if desired",
                    "authority": "MCR 2.119(E)", "required": False},
                {"item": "Supporting Brief", "detail":
                    "Required for motions raising legal arguments",
                    "authority": "MCR 2.119(A)(2)", "required": True},
                {"item": "Proposed Order", "detail":
                    "Must accompany the motion",
                    "authority": "MCR 2.119(A)(2)", "required": True},
                {"item": "Affidavits/Exhibits", "detail":
                    "Supporting evidence attached as exhibits",
                    "authority": "MCR 2.119(B)", "required": False},
                {"item": "Signature Block", "detail":
                    "Name, address, phone, bar number (or pro se designation), date",
                    "authority": "MCR 2.114(A)", "required": True},
                {"item": "Certificate of Service", "detail":
                    "Listing all parties served, method, date, address",
                    "authority": "MCR 2.107(A)", "required": True},
                {"item": "Notice of Hearing", "detail":
                    "Date, time, location; served 9+ days before hearing",
                    "authority": "MCR 2.119(C)(1)", "required": True},
            ],
            "brief": [
                {"item": "Cover Page / Caption", "detail":
                    "Full caption with court, case number, parties, document title",
                    "authority": "MCR 7.212(C)", "required": True},
                {"item": "Table of Contents", "detail":
                    "With page references for each section",
                    "authority": "MCR 7.212(C)(1)", "required": True},
                {"item": "Table of Authorities", "detail":
                    "Alphabetical list of cases, statutes, rules with page numbers",
                    "authority": "MCR 7.212(C)(2)", "required": True},
                {"item": "Statement of Jurisdiction", "detail":
                    "Basis for appellate jurisdiction, key dates",
                    "authority": "MCR 7.212(C)(3)", "required": True},
                {"item": "Statement of Questions Presented", "detail":
                    "Each question separately stated, answered yes/no by each party",
                    "authority": "MCR 7.212(C)(4)", "required": True},
                {"item": "Statement of Facts", "detail":
                    "With record citations: (Record, p XX) or (Tr, p XX)",
                    "authority": "MCR 7.212(C)(6)", "required": True},
                {"item": "Standard of Review", "detail":
                    "Applicable standard for each issue raised",
                    "authority": "MCR 7.212(C)(7)", "required": True},
                {"item": "Argument", "detail":
                    "IRAC structure with citations to authority and record",
                    "authority": "MCR 7.212(C)(7)", "required": True},
                {"item": "Relief Requested", "detail":
                    "Specific relief sought from the appellate court",
                    "authority": "MCR 7.212(C)(8)", "required": True},
                {"item": "Signature Block", "detail":
                    "Name, address, phone, pro se designation, date",
                    "authority": "MCR 7.212(C)(9)", "required": True},
                {"item": "Certificate of Service", "detail":
                    "All parties served, method, date",
                    "authority": "MCR 2.107(A)", "required": True},
                {"item": "Appendix", "detail":
                    "Orders appealed, relevant portions of record",
                    "authority": "MCR 7.212(C)(10)", "required": True},
                {"item": "Word/Page Limit", "detail":
                    "50 pages or 16,000 words maximum",
                    "authority": "MCR 7.212(B)", "required": True},
            ],
            "response": [
                {"item": "Caption", "detail":
                    "Full caption matching the original filing",
                    "authority": "MCR 2.113(A)", "required": True},
                {"item": "Title", "detail":
                    "DEFENDANT'S RESPONSE TO PLAINTIFF'S MOTION TO...",
                    "authority": "MCR 2.113(A)", "required": True},
                {"item": "Answer to Each Paragraph", "detail":
                    "Admit, deny, or state insufficient knowledge for each numbered paragraph",
                    "authority": "MCR 2.111(D)", "required": True},
                {"item": "Statement of Facts", "detail":
                    "Counter-statement with supporting citations",
                    "authority": "General practice", "required": True},
                {"item": "Argument", "detail":
                    "Legal arguments opposing the motion",
                    "authority": "MCR 2.119(C)(2)", "required": True},
                {"item": "Affirmative Defenses", "detail":
                    "All affirmative defenses must be raised or waived",
                    "authority": "MCR 2.111(F)(3)", "required": True},
                {"item": "Signature Block", "detail":
                    "Name, address, phone, date",
                    "authority": "MCR 2.114(A)", "required": True},
                {"item": "Certificate of Service", "detail":
                    "All parties served, method, date",
                    "authority": "MCR 2.107(A)", "required": True},
            ],
            "complaint": [
                {"item": "Caption", "detail":
                    "STATE OF MICHIGAN, court, case number, parties",
                    "authority": "MCR 2.113(A)", "required": True},
                {"item": "Title", "detail":
                    "COMPLAINT or COMPLAINT AND JURY DEMAND",
                    "authority": "MCR 2.113(A)", "required": True},
                {"item": "Jurisdictional Statement", "detail":
                    "Basis for court's subject-matter jurisdiction",
                    "authority": "MCR 2.111(B)(1)", "required": True},
                {"item": "Venue Statement", "detail":
                    "Basis for venue in this county",
                    "authority": "MCR 2.221", "required": True},
                {"item": "Party Identification", "detail":
                    "Full names, addresses, and capacity of all parties",
                    "authority": "MCR 2.111(B)(2)", "required": True},
                {"item": "Claims / Counts", "detail":
                    "Each claim separately stated in numbered paragraphs",
                    "authority": "MCR 2.111(A)", "required": True},
                {"item": "Factual Allegations", "detail":
                    "Material facts supporting each claim",
                    "authority": "MCR 2.111(B)(1)", "required": True},
                {"item": "Prayer for Relief", "detail":
                    "Specific relief demanded (damages, injunction, etc.)",
                    "authority": "MCR 2.111(B)(3)", "required": True},
                {"item": "Verification", "detail":
                    "Sworn verification if required by statute",
                    "authority": "MCR 2.114(A)", "required": True},
                {"item": "Signature Block", "detail":
                    "Name, address, phone, date",
                    "authority": "MCR 2.114(A)", "required": True},
                {"item": "Certificate of Service", "detail":
                    "All parties served with summons and complaint",
                    "authority": "MCR 2.107(A)", "required": True},
                {"item": "Summons", "detail":
                    "Must be issued and served with complaint",
                    "authority": "MCR 2.102(A)", "required": True},
                {"item": "Filing Fee", "detail":
                    "Circuit court filing fee (check current amount)",
                    "authority": "MCL 600.8801", "required": True},
            ],
        }

        checklist = checklists.get(filing_type)
        if not checklist:
            # Fallback: generate a generic checklist
            checklist = [
                {"item": "Caption", "detail": "Full case caption",
                 "authority": "MCR 2.113(A)", "required": True},
                {"item": "Body", "detail": "Substantive content",
                 "authority": "General", "required": True},
                {"item": "Signature Block", "detail": "Signed by filer",
                 "authority": "MCR 2.114(A)", "required": True},
                {"item": "Certificate of Service", "detail": "Proof of service",
                 "authority": "MCR 2.107(A)", "required": True},
            ]

        # Enrich with DB authority text where available
        for entry in checklist:
            auth = entry.get("authority", "")
            mcr_match = re.search(r"MCR\s+([\d.]+)", auth)
            if mcr_match:
                rule_data = self._lookup_rule(mcr_match.group(1))
                if rule_data and rule_data.get("title"):
                    entry["authority_title"] = rule_data["title"]

        return {
            "filing_type": filing_type,
            "total_items": len(checklist),
            "required_items": sum(1 for c in checklist if c["required"]),
            "optional_items": sum(1 for c in checklist if not c["required"]),
            "checklist": checklist,
        }

    # ------------------------------------------------------------------
    # 7. check_preservation_of_issues
    # ------------------------------------------------------------------

    def check_preservation_of_issues(self, issues_list):
        """
        For appellate work, check if issues were preserved in the lower court.

        Each issue in issues_list should be a dict with at minimum:
            {"issue": str, "objected_at_trial": bool, "raised_in_post_judgment": bool}

        Returns preservation analysis with plain-error fallback guidance.
        """
        results = []
        for issue_item in issues_list:
            if isinstance(issue_item, str):
                issue_item = {
                    "issue": issue_item,
                    "objected_at_trial": False,
                    "raised_in_post_judgment": False,
                }

            issue_text = issue_item.get("issue", "")
            objected = issue_item.get("objected_at_trial", False)
            post_judgment = issue_item.get("raised_in_post_judgment", False)

            preserved = objected or post_judgment
            plain_error_available = not preserved

            analysis = {
                "issue": issue_text,
                "preserved": preserved,
                "objected_at_trial": objected,
                "raised_in_post_judgment": post_judgment,
                "authority": "MCR 2.517 (objections); MCR 2.119(F)(1) (reconsideration)",
                "analysis": "",
                "plain_error": None,
            }

            if preserved:
                if objected:
                    analysis["analysis"] = (
                        "Issue preserved by timely objection at trial. "
                        "Standard appellate review applies."
                    )
                else:
                    analysis["analysis"] = (
                        "Issue raised in post-judgment motion (MCR 2.119(F)(1)). "
                        "Preserved for appellate review."
                    )
            else:
                analysis["analysis"] = (
                    "Issue NOT preserved — no objection at trial and not raised "
                    "in post-judgment motion. Must argue plain error."
                )
                analysis["plain_error"] = {
                    "standard": "People v Carines, 460 Mich 750, 763 (1999)",
                    "elements": [
                        "1. Error must have occurred",
                        "2. Error must be plain (clear or obvious)",
                        "3. Plain error must have affected substantial rights "
                        "(i.e., affected the outcome of the proceedings)",
                        "4. Error seriously affected the fairness, integrity, "
                        "or public reputation of judicial proceedings",
                    ],
                    "burden": "Appellant bears the burden on all four prongs",
                    "note": (
                        "Plain error review is highly deferential. Courts rarely "
                        "reverse on plain error. Preservation is always preferred."
                    ),
                }

            # Search DB for any evidence of preservation
            try:
                rows = self._query_fts(
                    "evidence_quotes_fts",
                    issue_text[:80],
                    limit=3,
                )
                if rows:
                    analysis["db_evidence"] = [
                        dict(r) for r in rows
                    ]
            except Exception:
                pass

            results.append(analysis)

        preserved_count = sum(1 for r in results if r["preserved"])
        unpreserved_count = len(results) - preserved_count

        return {
            "total_issues": len(results),
            "preserved": preserved_count,
            "unpreserved": unpreserved_count,
            "issues": results,
            "warning": (
                f"{unpreserved_count} issue(s) NOT preserved — must argue plain error. "
                "Consider filing motion for reconsideration if within 21-day window."
                if unpreserved_count > 0
                else "All issues preserved for appellate review."
            ),
        }

    # ------------------------------------------------------------------
    # 8. score_filing_readiness
    # ------------------------------------------------------------------

    def score_filing_readiness(self, filing_type, document_text=None):
        """
        Overall readiness score 0–100 with breakdown:
          - Format compliance:   25 points
          - Citation coverage:   25 points
          - Deadline compliance: 25 points
          - Service readiness:   25 points
        """
        filing_type = filing_type.lower().strip()
        breakdown = {
            "format_compliance": {"score": 0, "max": 25, "details": []},
            "citation_coverage": {"score": 0, "max": 25, "details": []},
            "deadline_compliance": {"score": 0, "max": 25, "details": []},
            "service_readiness": {"score": 0, "max": 25, "details": []},
        }

        # --- Format compliance (25 pts) ---
        if document_text:
            report = self.check_filing_compliance(document_text, filing_type)
            total_checks = len(report["checks"])
            passed_checks = sum(
                1 for v in report["checks"].values() if v["pass"]
            )
            if total_checks > 0:
                breakdown["format_compliance"]["score"] = round(
                    25 * passed_checks / total_checks
                )
            breakdown["format_compliance"]["details"] = report.get(
                "remediation", []
            )
        else:
            # No document — check if we have a checklist
            checklist = self.generate_compliance_checklist(filing_type)
            breakdown["format_compliance"]["score"] = 0
            breakdown["format_compliance"]["details"].append(
                "No document text provided — cannot assess format compliance"
            )

        # --- Citation coverage (25 pts) ---
        if document_text:
            mcr = len(_PAT_MCR.findall(document_text))
            mcl = len(_PAT_MCL.findall(document_text))
            mre = len(_PAT_MRE.findall(document_text))
            cases = len(_PAT_CASE.findall(document_text))
            total_cites = mcr + mcl + mre + cases

            # Scoring: 5+ diverse citations = full marks
            cite_score = 0
            if total_cites >= 5:
                cite_score += 15
            elif total_cites >= 3:
                cite_score += 10
            elif total_cites >= 1:
                cite_score += 5

            # Diversity bonus: multiple types
            types_used = sum(1 for c in [mcr, mcl, mre, cases] if c > 0)
            cite_score += min(10, types_used * 3)  # up to 10 pts for diversity
            cite_score = min(25, cite_score)

            breakdown["citation_coverage"]["score"] = cite_score
            breakdown["citation_coverage"]["details"].append(
                f"MCR: {mcr}, MCL: {mcl}, MRE: {mre}, Case law: {cases} "
                f"(total: {total_cites}, types: {types_used})"
            )

            # Verify citations against DB
            verified = 0
            all_cites = _PAT_MCR.findall(document_text)[:5]
            for cite in all_cites:
                rule_num = re.search(r"[\d.]+", cite)
                if rule_num:
                    rule_data = self._lookup_rule(rule_num.group())
                    if rule_data:
                        verified += 1
            if all_cites:
                breakdown["citation_coverage"]["details"].append(
                    f"DB-verified MCR citations: {verified}/{len(all_cites)}"
                )
        else:
            breakdown["citation_coverage"]["details"].append(
                "No document text — cannot assess citation coverage"
            )

        # --- Deadline compliance (25 pts) ---
        deadline_result = self.check_deadline_compliance(filing_type)
        if deadline_result["compliant"]:
            if deadline_result["days_remaining"] is not None:
                if deadline_result["days_remaining"] > 7:
                    breakdown["deadline_compliance"]["score"] = 25
                elif deadline_result["days_remaining"] > 3:
                    breakdown["deadline_compliance"]["score"] = 20
                else:
                    breakdown["deadline_compliance"]["score"] = 15
                breakdown["deadline_compliance"]["details"].append(
                    f"{deadline_result['days_remaining']} days remaining"
                )
            else:
                breakdown["deadline_compliance"]["score"] = 25
                breakdown["deadline_compliance"]["details"].append(
                    "No specific deadline constraint found"
                )
        else:
            breakdown["deadline_compliance"]["score"] = 0
            breakdown["deadline_compliance"]["details"].append(
                "DEADLINE EXPIRED — filing may be untimely"
            )
        breakdown["deadline_compliance"]["details"].extend(
            deadline_result.get("warnings", [])
        )

        # --- Service readiness (25 pts) ---
        service_result = self.check_service_requirements(filing_type)
        # Give full marks if we have a valid service checklist
        # Deduct if document text is missing cert of service
        service_score = 25
        if document_text:
            if not _PAT_CERT_SERVICE.search(document_text):
                service_score -= 15
                breakdown["service_readiness"]["details"].append(
                    "Certificate of Service not detected in document"
                )
            else:
                breakdown["service_readiness"]["details"].append(
                    "Certificate of Service present"
                )
        else:
            service_score = 10
            breakdown["service_readiness"]["details"].append(
                "No document text — cannot verify service certificate"
            )
        breakdown["service_readiness"]["score"] = service_score

        # --- Aggregate ---
        total_score = sum(v["score"] for v in breakdown.values())

        # Rating
        if total_score >= 90:
            rating = "READY TO FILE"
        elif total_score >= 70:
            rating = "NEARLY READY — address remaining items"
        elif total_score >= 50:
            rating = "NEEDS WORK — significant gaps remain"
        else:
            rating = "NOT READY — major compliance issues"

        return {
            "filing_type": filing_type,
            "total_score": total_score,
            "max_score": 100,
            "rating": rating,
            "breakdown": breakdown,
            "timestamp": datetime.now().isoformat(),
        }

    # ------------------------------------------------------------------
    # Utility: close connection
    # ------------------------------------------------------------------

    def close(self):
        """Close the database connection."""
        if self._conn:
            try:
                self._conn.close()
            except Exception:
                pass
            self._conn = None


# ---------------------------------------------------------------------------
# __main__ smoke test
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    print("=" * 70)
    print("  Pro Se Compliance Engine — MBP LitigationOS 2026")
    print("  Smoke Test")
    print("=" * 70)

    engine = ComplianceEngine()

    # 1. Generate a compliance checklist
    print("\n[1] Motion Checklist:")
    checklist = engine.generate_compliance_checklist("motion")
    print(f"    Filing type: {checklist['filing_type']}")
    print(f"    Required items: {checklist['required_items']}")
    print(f"    Optional items: {checklist['optional_items']}")
    for item in checklist["checklist"][:5]:
        marker = "[REQ]" if item["required"] else "[OPT]"
        print(f"    {marker} {item['item']}")
    if checklist["total_items"] > 5:
        print(f"    ... and {checklist['total_items'] - 5} more items")

    # 2. Check deadline compliance
    print("\n[2] Deadline Check (claim_of_appeal):")
    deadline = engine.check_deadline_compliance("claim_of_appeal", "F")
    print(f"    Compliant: {deadline['compliant']}")
    print(f"    Authority: {deadline.get('authority', 'N/A')}")
    if deadline["days_remaining"] is not None:
        print(f"    Days remaining: {deadline['days_remaining']}")
    for w in deadline.get("warnings", []):
        print(f"    WARNING: {w}")

    # 3. Check service requirements
    print("\n[3] Service Requirements (motion, mail):")
    service = engine.check_service_requirements("motion", "mail")
    print(f"    Method: {service['service_method']}")
    print(f"    Extra days: {service['extra_days']}")
    for req in service["requirements"][:3]:
        print(f"    - {req['item']} ({req['authority']})")

    # 4. Detect procedural traps
    print("\n[4] Procedural Traps:")
    traps = engine.detect_procedural_traps()
    print(f"    Total traps: {traps['traps_detected']}")
    print(f"    Critical: {len(traps['critical'])}")
    print(f"    Warnings: {len(traps['warnings'])}")
    for t in traps["critical"][:3]:
        print(f"    [CRITICAL] {t['trap']}")

    # 5. Score filing readiness (without document)
    print("\n[5] Filing Readiness Score (brief, no document):")
    score = engine.score_filing_readiness("brief")
    print(f"    Score: {score['total_score']}/{score['max_score']}")
    print(f"    Rating: {score['rating']}")
    for cat, data in score["breakdown"].items():
        print(f"    {cat}: {data['score']}/{data['max']}")

    # 6. Sample filing compliance check
    print("\n[6] Sample Filing Compliance Check:")
    sample_text = textwrap.dedent("""\
        STATE OF MICHIGAN
        IN THE 14TH CIRCUIT COURT FOR MUSKEGON COUNTY

        ANDREW PIGORS,
            Plaintiff,                    Case No. 2024-001507-DC
        v.                                Hon. Jenny L. McNeill
        TIFFANY WATSON,
            Defendant.
        _______________________________________________/

        PLAINTIFF'S MOTION TO COMPEL DISCOVERY

        1. Plaintiff Andrew Pigors respectfully moves this Honorable Court
        for an order compelling Defendant to respond to discovery requests.

        2. Pursuant to MCR 2.313(A), a party may move for an order
        compelling discovery when the opposing party fails to respond.

        3. Defendant has failed to respond to Plaintiff's First Set of
        Interrogatories served on January 15, 2025, in violation of
        MCR 2.309(B)(2), which requires responses within 28 days.

        4. MCL 722.23 best interest factors require full disclosure
        of information relevant to the children's welfare.

        WHEREFORE, Plaintiff respectfully requests this Court enter an order
        compelling Defendant to respond to all outstanding discovery.

        Respectfully submitted,

        /s/ Andrew Pigors
        Andrew Pigors, Pro Se
        Date: February 1, 2025

        CERTIFICATE OF SERVICE

        I hereby certify that on February 1, 2025, I served a copy of
        this Motion upon Defendant by first-class mail at her last known
        address.

        /s/ Andrew Pigors
    """)
    report = engine.check_filing_compliance(sample_text, "motion")
    print(f"    Compliant: {report['compliant']}")
    print(f"    Citations: {report['citation_count']}")
    print(f"    Words: {report['word_count']}, Pages (est): {report['page_estimate']}")
    if report["critical_failures"]:
        print(f"    Critical failures: {report['critical_failures']}")
    if report["warnings"]:
        print(f"    Warnings: {report['warnings']}")

    # 7. Score the sample document
    print("\n[7] Sample Document Readiness Score:")
    doc_score = engine.score_filing_readiness("motion", sample_text)
    print(f"    Score: {doc_score['total_score']}/{doc_score['max_score']}")
    print(f"    Rating: {doc_score['rating']}")

    engine.close()
    print("\n" + "=" * 70)
    print("  Smoke test complete.")
    print("=" * 70)
