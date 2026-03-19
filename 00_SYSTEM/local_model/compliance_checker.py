"""
Compliance Checker — LitigationOS 2026
Validates Michigan court filing compliance: MCR 2.113 formatting,
page/word limits, citation format, required sections, and service.
"""

import json
import os
import re
import sqlite3
import sys
from typing import Any, Dict, List, Optional

DB_PATH = os.environ.get("LITIGATION_DB_PATH", r"C:\Users\andre\LitigationOS\litigation_context.db")

PAGE_LIMITS = {
    "brief": {"pages": 50, "words": 16000},
    "motion": {"pages": 20, "words": 8000},
    "response": {"pages": 20, "words": 8000},
    "reply": {"pages": 10, "words": 5000},
    "affidavit": {"pages": None, "words": None},
}

REQUIRED_SECTIONS = {
    "motion": [
        "caption", "title", "statement of facts", "argument",
        "relief requested", "signature", "certificate of service",
    ],
    "brief": [
        "caption", "title", "table of contents", "table of authorities",
        "statement of jurisdiction", "statement of questions presented",
        "statement of facts", "argument", "relief requested",
        "signature", "certificate of service",
    ],
    "response": [
        "caption", "title", "statement of facts", "argument",
        "relief requested", "signature", "certificate of service",
    ],
    "affidavit": [
        "caption", "title", "body", "jurat", "signature",
    ],
}


def _get_db() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH)
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA query_only=ON")
    conn.row_factory = sqlite3.Row
    return conn


class ComplianceChecker:
    """Validates court filings against Michigan Court Rules."""

    # ── Citation patterns ──
    _MCR_PAT = re.compile(r"MCR\s+\d+\.\d+(?:\([A-Za-z0-9]+\))*")
    _MCL_PAT = re.compile(r"MCL\s+\d+\.\d+[a-z]*(?:\([A-Za-z0-9]+\))*")
    _MRE_PAT = re.compile(r"MRE\s+\d+(?:\([A-Za-z0-9]+\))*")
    _CASE_PAT = re.compile(
        r"[A-Z][a-z]+\s+v\s+[A-Z][a-z]+,?\s+\d+\s+(?:Mich|Mich\s*App|NW2d)\s+\d+"
    )

    def check_mcr_format(self, text: str) -> Dict[str, Any]:
        """Check MCR 2.113 formatting: caption, numbered paragraphs, signature, cert of service."""
        issues: List[str] = []
        checks: Dict[str, bool] = {}

        # Caption check
        has_caption = bool(
            re.search(r"(?i)(circuit court|court of appeals|supreme court)", text)
            and re.search(r"(?i)(plaintiff|appellant|petitioner)", text)
            and re.search(r"(?i)(defendant|appellee|respondent)", text)
        )
        checks["caption"] = has_caption
        if not has_caption:
            issues.append("Missing or incomplete caption per MCR 2.113(A)")

        # Case number
        has_case_number = bool(re.search(r"\d{4}-\d{4,6}-\w{2}", text))
        checks["case_number"] = has_case_number
        if not has_case_number:
            issues.append("Missing case number in caption")

        # Numbered paragraphs
        numbered = re.findall(r"^\s*\d+\.\s+", text, re.MULTILINE)
        checks["numbered_paragraphs"] = len(numbered) > 0
        if not numbered:
            issues.append("No numbered paragraphs found per MCR 2.113(D)")

        # Signature block
        has_sig = bool(re.search(r"(?i)(respectfully submitted|/s/|signature|dated)", text))
        checks["signature_block"] = has_sig
        if not has_sig:
            issues.append("Missing signature block per MCR 2.113(E)")

        # Certificate of service
        has_cos = bool(re.search(r"(?i)certificate\s+of\s+service", text))
        checks["certificate_of_service"] = has_cos
        if not has_cos:
            issues.append("Missing Certificate of Service per MCR 2.107")

        passed = sum(checks.values())
        total = len(checks)
        return {
            "check": "mcr_2113_format",
            "score": round(passed / total * 100) if total else 0,
            "checks": checks,
            "issues": issues,
            "passed": passed,
            "total": total,
        }

    def check_page_limits(self, text: str, doc_type: str) -> Dict[str, Any]:
        """Verify page/word limits for the given document type."""
        doc_type = doc_type.lower()
        limits = PAGE_LIMITS.get(doc_type, {"pages": None, "words": None})
        words = len(text.split())
        pages_est = max(1, words // 250)

        issues: List[str] = []
        within_limits = True

        if limits["words"] and words > limits["words"]:
            issues.append(
                f"Word count ({words:,}) exceeds {doc_type} limit of {limits['words']:,}"
            )
            within_limits = False

        if limits["pages"] and pages_est > limits["pages"]:
            issues.append(
                f"Estimated pages ({pages_est}) exceeds {doc_type} limit of {limits['pages']}"
            )
            within_limits = False

        return {
            "check": "page_limits",
            "doc_type": doc_type,
            "word_count": words,
            "estimated_pages": pages_est,
            "limits": limits,
            "within_limits": within_limits,
            "issues": issues,
        }

    def check_citations(self, text: str) -> Dict[str, Any]:
        """Verify citation format AND existence in DB (auth_rules + master_citations)."""
        mcr_cites = self._MCR_PAT.findall(text)
        mcl_cites = self._MCL_PAT.findall(text)
        mre_cites = self._MRE_PAT.findall(text)
        case_cites = self._CASE_PAT.findall(text)

        total = len(mcr_cites) + len(mcl_cites) + len(mre_cites) + len(case_cites)
        issues: List[str] = []

        if total == 0:
            issues.append("No citations found — every legal assertion must cite authority")

        # Check for bare citations missing subrules
        bare_mcr = re.findall(r"MCR\s+\d+\.\d+(?!\()", text)
        if bare_mcr:
            issues.append(
                f"{len(bare_mcr)} MCR citation(s) may be missing subrule references: "
                f"{bare_mcr[:3]}"
            )

        # ── DB verification: confirm cited rules actually exist ──
        verified: List[str] = []
        not_found: List[str] = []
        db_error = None
        try:
            conn = _get_db()
            try:
                all_rule_cites = mcr_cites + mcl_cites + mre_cites
                for cite in all_rule_cites:
                    # Extract the rule number (e.g. "2.113" from "MCR 2.113(A)")
                    num_match = re.search(r"[\d]+\.[\d]+[a-z]*", cite)
                    if not num_match:
                        continue
                    rule_num = num_match.group()
                    row = conn.execute(
                        """SELECT 1 FROM auth_rules
                           WHERE rule_number LIKE ? LIMIT 1""",
                        (f"%{rule_num}%",),
                    ).fetchone()
                    if row:
                        verified.append(cite)
                    else:
                        # Fallback: check master_citations
                        row2 = conn.execute(
                            """SELECT 1 FROM master_citations
                               WHERE citation LIKE ? LIMIT 1""",
                            (f"%{rule_num}%",),
                        ).fetchone()
                        if row2:
                            verified.append(cite)
                        else:
                            not_found.append(cite)

                for cite in case_cites:
                    row = conn.execute(
                        """SELECT 1 FROM master_citations
                           WHERE citation LIKE ? LIMIT 1""",
                        (f"%{cite[:40]}%",),
                    ).fetchone()
                    if row:
                        verified.append(cite)
                    else:
                        not_found.append(cite)
            finally:
                conn.close()
        except Exception as e:
            db_error = str(e)

        if not_found:
            issues.append(
                f"{len(not_found)} citation(s) not verified in DB: {not_found[:5]}"
            )

        return {
            "check": "citations",
            "mcr_citations": mcr_cites,
            "mcl_citations": mcl_cites,
            "mre_citations": mre_cites,
            "case_citations": case_cites,
            "total_citations": total,
            "db_verified": verified,
            "db_not_found": not_found,
            "db_verification_rate": (
                round(len(verified) / total * 100) if total else 0
            ),
            "db_error": db_error,
            "issues": issues,
        }

    def check_required_sections(self, text: str, doc_type: str) -> Dict[str, Any]:
        """Verify required sections — checks hardcoded list AND queries auth_rules for MCR requirements."""
        doc_type = doc_type.lower()
        required = list(REQUIRED_SECTIONS.get(doc_type, []))
        text_lower = text.lower()

        # ── DB enrichment: pull MCR requirements for this doc type ──
        db_requirements: List[str] = []
        db_error = None
        try:
            conn = _get_db()
            try:
                rows = conn.execute(
                    """SELECT rule_number, title, full_text FROM auth_rules
                       WHERE (LOWER(full_text) LIKE ? OR LOWER(title) LIKE ?)
                       AND rule_type IS NOT NULL
                       LIMIT 20""",
                    (f"%{doc_type}%", f"%{doc_type}%"),
                ).fetchall()
                for row in rows:
                    ft = (row["full_text"] or "").lower()
                    # Extract section requirements mentioned in rule text
                    for keyword in ("shall contain", "must include", "shall include",
                                    "required to contain", "shall set forth"):
                        if keyword in ft:
                            db_requirements.append(
                                f"{row['rule_number']}: {row.get('title', '')}"
                            )
                            break
            finally:
                conn.close()
        except Exception as e:
            db_error = str(e)

        found: List[str] = []
        missing: List[str] = []
        for section in required:
            if section in text_lower:
                found.append(section)
            else:
                missing.append(section)

        return {
            "check": "required_sections",
            "doc_type": doc_type,
            "required": required,
            "found": found,
            "missing": missing,
            "score": round(len(found) / len(required) * 100) if required else 100,
            "db_mcr_requirements": db_requirements,
            "db_error": db_error,
        }

    def check_service_requirements(self, text: str) -> Dict[str, Any]:
        """Verify certificate of service is present and correct."""
        issues: List[str] = []
        checks: Dict[str, bool] = {}

        has_cos = bool(re.search(r"(?i)certificate\s+of\s+service", text))
        checks["certificate_present"] = has_cos
        if not has_cos:
            issues.append("Missing Certificate of Service — required on EVERY filing per MCR 2.107")

        has_method = bool(
            re.search(r"(?i)(first.class\s+mail|personal\s+service|e-?fil|electronic)", text)
        )
        checks["service_method"] = has_method
        if has_cos and not has_method:
            issues.append("Certificate of Service missing method of service")

        has_date = bool(
            re.search(r"(?i)(served|mailed|delivered)\s+.*\d{1,2}[,/\-]\s*\d{1,4}", text)
            or re.search(r"(?i)date.*service", text)
        )
        checks["service_date"] = has_date
        if has_cos and not has_date:
            issues.append("Certificate of Service missing date of service")

        has_recipient = bool(
            re.search(r"(?i)(watson|defendant|appellee|opposing|counsel)", text)
        )
        checks["service_recipient"] = has_recipient
        if has_cos and not has_recipient:
            issues.append("Certificate of Service missing recipient identification")

        passed = sum(checks.values())
        total = len(checks)
        return {
            "check": "service_requirements",
            "score": round(passed / total * 100) if total else 0,
            "checks": checks,
            "issues": issues,
        }

    def full_compliance_check(
        self, text: str, doc_type: str = "motion", court: str = "14th Circuit"
    ) -> Dict[str, Any]:
        """Run all compliance checks; return score 0-100 + issues + suggestions."""
        fmt = self.check_mcr_format(text)
        limits = self.check_page_limits(text, doc_type)
        cites = self.check_citations(text)
        sections = self.check_required_sections(text, doc_type)
        service = self.check_service_requirements(text)

        all_issues: List[str] = (
            fmt["issues"] + limits["issues"] + cites["issues"]
            + sections.get("missing", []) + service["issues"]
        )

        subscores = [
            fmt["score"],
            100 if limits["within_limits"] else 50,
            min(100, cites["total_citations"] * 10),
            sections["score"],
            service["score"],
        ]
        overall = round(sum(subscores) / len(subscores))

        suggestions: List[str] = []
        if not fmt["checks"].get("caption"):
            suggestions.append("Add full case caption with court, case number, parties, and judge")
        if not fmt["checks"].get("certificate_of_service"):
            suggestions.append("Add Certificate of Service with method, date, and recipient")
        if cites["total_citations"] < 3:
            suggestions.append("Add more authority citations — every legal assertion needs one")
        if sections.get("missing"):
            suggestions.append(f"Add missing sections: {', '.join(sections['missing'])}")

        # ── DB verification pass: confirm cited rules exist ──
        db_verification: Dict[str, Any] = {
            "citation_verification_rate": cites.get("db_verification_rate", 0),
            "verified_count": len(cites.get("db_verified", [])),
            "not_found_count": len(cites.get("db_not_found", [])),
            "not_found_citations": cites.get("db_not_found", []),
            "mcr_requirements_found": sections.get("db_mcr_requirements", []),
        }

        if cites.get("db_not_found"):
            all_issues.append(
                f"DB verification: {len(cites['db_not_found'])} citation(s) not found in authority database"
            )
            suggestions.append(
                "Verify unconfirmed citations against official MCR/MCL sources before filing"
            )

        # Adjust overall score: penalize for unverified citations
        verification_penalty = 0
        if cites.get("total_citations", 0) > 0 and cites.get("db_verification_rate", 100) < 50:
            verification_penalty = 10
            suggestions.append(
                "Low DB verification rate — many citations may be inaccurate or outdated"
            )

        overall = max(0, round(sum(subscores) / len(subscores)) - verification_penalty)

        return {
            "overall_score": overall,
            "court": court,
            "doc_type": doc_type,
            "subscores": {
                "formatting": fmt["score"],
                "page_limits": 100 if limits["within_limits"] else 50,
                "citations": min(100, cites["total_citations"] * 10),
                "sections": sections["score"],
                "service": service["score"],
                "db_verification": cites.get("db_verification_rate", 0),
            },
            "issues": all_issues,
            "suggestions": suggestions,
            "db_verification": db_verification,
            "detail": {
                "format": fmt,
                "limits": limits,
                "citations": cites,
                "sections": sections,
                "service": service,
            },
        }

    def get_mcr_requirements(self, doc_type: str) -> List[Dict[str, Any]]:
        """Query auth_rules for MCR requirements for a given document type."""
        conn = _get_db()
        try:
            rows = conn.execute(
                """SELECT * FROM auth_rules
                   WHERE LOWER(full_text) LIKE ? OR LOWER(title) LIKE ?
                   LIMIT 20""",
                (f"%{doc_type.lower()}%", f"%{doc_type.lower()}%"),
            ).fetchall()
            return [dict(r) for r in rows]
        finally:
            conn.close()


def self_test() -> Dict[str, Any]:
    """Run self-test to verify DB connectivity and key compliance methods."""
    results = {"status": "ok", "tests": {}}
    checker = ComplianceChecker()

    # Test 1: DB connectivity
    try:
        conn = _get_db()
        conn.execute("SELECT 1").fetchone()
        conn.close()
        results["tests"]["db_connectivity"] = {"passed": True}
    except Exception as e:
        results["tests"]["db_connectivity"] = {"passed": False, "error": str(e)}

    # Test 2: check_citations with sample text
    try:
        sample = "Per MCR 2.113(A), the caption must include the case number. MCL 722.23 governs best interest."
        cites = checker.check_citations(sample)
        results["tests"]["check_citations"] = {
            "passed": cites["total_citations"] >= 2,
            "total_found": cites["total_citations"],
            "db_verified": len(cites.get("db_verified", [])),
        }
    except Exception as e:
        results["tests"]["check_citations"] = {"passed": False, "error": str(e)}

    # Test 3: full_compliance_check
    try:
        sample = (
            "IN THE CIRCUIT COURT FOR MUSKEGON COUNTY\n"
            "Case No. 2024-001507-DC\nPlaintiff: Andrew Pigors\nDefendant: Tiffany Watson\n"
            "MOTION TO COMPEL\n1. Statement of facts.\n2. Argument per MCR 2.313(A).\n"
            "Relief Requested\nRespectfully submitted,\n/s/ Andrew Pigors\n"
            "Certificate of Service\nServed by first class mail on Tiffany Watson on 01/15/2025."
        )
        result = checker.full_compliance_check(sample, "motion")
        results["tests"]["full_compliance_check"] = {
            "passed": isinstance(result, dict) and "overall_score" in result,
            "overall_score": result.get("overall_score"),
            "has_db_verification": "db_verification" in result,
        }
    except Exception as e:
        results["tests"]["full_compliance_check"] = {"passed": False, "error": str(e)}

    results["status"] = (
        "ok" if all(t.get("passed") for t in results["tests"].values()) else "degraded"
    )
    return results


if __name__ == "__main__":
    checker = ComplianceChecker()

    if len(sys.argv) < 2:
        print("Usage: compliance_checker.py <command> [args]")
        print("Commands: check <file> [doc_type] | requirements <doc_type> | test")
        sys.exit(0)

    cmd = sys.argv[1]

    if cmd == "test":
        print(json.dumps(self_test(), indent=2, default=str))

    elif cmd == "check" and len(sys.argv) >= 3:
        filepath = sys.argv[2]
        doc_type = sys.argv[3] if len(sys.argv) > 3 else "motion"
        with open(filepath, "r", encoding="utf-8", errors="replace") as f:
            text = f.read()
        result = checker.full_compliance_check(text, doc_type)
        print(json.dumps(result, indent=2, default=str))

    elif cmd == "requirements" and len(sys.argv) >= 3:
        doc_type = sys.argv[2]
        result = checker.get_mcr_requirements(doc_type)
        print(json.dumps(result, indent=2, default=str))

    else:
        print("Usage: compliance_checker.py check <file> [doc_type]")
        print("       compliance_checker.py requirements <doc_type>")
        sys.exit(1)
