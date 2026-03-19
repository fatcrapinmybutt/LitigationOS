#!/usr/bin/env python3
"""
THE MANBEARPIG — EPOCH v8.0 — Multi-Forum Compliance Engine
==============================================================
Cross-jurisdictional filing compliance for MI Circuit, COA, MSC, USDC, JTC.
Validates formatting, page/word limits, required attachments, and identifies
conflicting requirements when filing in multiple forums simultaneously.

Case: Andrew Pigors v. Tiffany Watson
Courts: 14th Circuit (Lane A/D), COA 366810 (Lane F), MSC (Lane G),
        USDC WD Mich (§1983), JTC (Lane E)
"""

from __future__ import annotations

import json
import os
import re
import sqlite3
import sys
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

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


def _table_exists(conn: sqlite3.Connection, table: str) -> bool:
    try:
        row = conn.execute(
            "SELECT COUNT(*) as cnt FROM sqlite_master "
            "WHERE type='table' AND name=?",
            (table,),
        ).fetchone()
        return bool(row and row["cnt"] > 0)
    except Exception:
        return False


# ── Forum Compliance Specifications ──────────────────────────────────

FORUM_SPECS: Dict[str, Dict[str, Any]] = {
    "circuit_court": {
        "name": "14th Circuit Court, Muskegon County",
        "formatting": {
            "font": "12pt Times New Roman",
            "spacing": "Double-spaced",
            "margins": "1 inch all sides",
            "caption": "MCR 2.113(C) — caption required on first page",
            "paragraphs": "Numbered per MCR 2.113(E)",
            "signature": "MCR 2.114 — signature certifies well-grounded",
            "cos": "Required on ALL filings — MCR 2.107",
            "proposed_order": "MCR 2.119(A)(2) — required with every motion",
        },
        "required_elements": [
            "caption",
            "numbered_paragraphs",
            "signature_block",
            "certificate_of_service",
            "proposed_order",
        ],
        "page_limits": None,
        "word_limits": None,
        "filing_method": "E-filing via MiFILE or paper at clerk window",
        "filing_fee": "Varies by motion type",
        "copies": 1,
    },
    "court_of_appeals": {
        "name": "Michigan Court of Appeals",
        "formatting": {
            "font": "12pt proportional or 10pt monospace",
            "spacing": "Double-spaced",
            "margins": "1 inch",
            "caption": "MCR 7.212(B) — COA case number, lower court case number",
            "appendix": "MCR 7.212(C)(8) — required with brief",
            "word_count_cert": "MCR 7.212(B) — certification of word count required",
            "table_of_contents": "MCR 7.212(C)(1) — required",
            "table_of_authorities": "MCR 7.212(C)(2) — required",
            "statement_of_jurisdiction": "MCR 7.212(C)(3) — required",
            "statement_of_questions": "MCR 7.212(C)(4) — required",
        },
        "required_elements": [
            "caption",
            "table_of_contents",
            "table_of_authorities",
            "statement_of_jurisdiction",
            "statement_of_questions",
            "statement_of_facts",
            "argument",
            "relief_requested",
            "signature_block",
            "certificate_of_service",
            "word_count_certification",
            "appendix",
        ],
        "page_limits": {"brief": 50, "reply": 25, "motion": None},
        "word_limits": {"brief": 16000, "reply": 7000},
        "filing_method": "TrueFiling electronic filing",
        "filing_fee": "$375 claim of appeal; motions vary",
        "copies": 0,
    },
    "supreme_court": {
        "name": "Michigan Supreme Court",
        "formatting": {
            "font": "12pt",
            "spacing": "Double-spaced",
            "copies": "13 copies required — MCR 7.306(B)",
            "caption": "MCR 7.306(B) — MSC case style",
            "appendix": "MCR 7.306(B)(3) — appendix required",
            "questions_presented": "MCR 7.306(B)(1) — concise statement required",
        },
        "required_elements": [
            "caption",
            "questions_presented",
            "statement_of_facts",
            "argument",
            "relief_requested",
            "appendix",
            "signature_block",
            "certificate_of_service",
            "proof_of_service",
        ],
        "page_limits": {"application": 50},
        "word_limits": None,
        "filing_method": "Paper filing — 13 copies to MSC Clerk, Lansing",
        "filing_fee": "$375 application",
        "copies": 13,
    },
    "federal_usdc": {
        "name": "USDC Western District of Michigan",
        "formatting": {
            "font": "14pt (USDC WD Mich LCivR 5.1)",
            "spacing": "Double-spaced",
            "margins": "1 inch",
            "caption": "FRCP 10(a) — federal caption format",
            "cm_ecf": "Electronic filing via CM/ECF required",
            "civil_cover_sheet": "JS-44 Civil Cover Sheet required with complaint",
        },
        "required_elements": [
            "caption",
            "civil_cover_sheet",
            "complaint_or_motion",
            "signature_block",
            "certificate_of_service",
            "summons",
        ],
        "page_limits": {"brief": 25, "reply": 10},
        "word_limits": {"brief": 7000},
        "filing_method": "CM/ECF electronic filing",
        "filing_fee": "$405 civil complaint",
        "copies": 0,
    },
    "jtc": {
        "name": "Michigan Judicial Tenure Commission",
        "formatting": {
            "no_specific_format": True,
            "cos": "Mailed to JTC office",
            "supporting_docs": "Attach all supporting evidence",
            "address": "3034 W. Grand Blvd, Suite 8-450, Detroit MI 48202",
        },
        "required_elements": [
            "complaint_narrative",
            "supporting_evidence",
            "signature",
        ],
        "page_limits": None,
        "word_limits": None,
        "filing_method": "Mail to JTC office — no electronic filing",
        "filing_fee": "None",
        "copies": 1,
    },
}

# Structural element detection patterns
_ELEMENT_PATTERNS: Dict[str, List[str]] = {
    "caption": [
        r"(?i)state of michigan",
        r"(?i)circuit court|court of appeals|supreme court|district court",
        r"(?i)case\s*no\.?\s*\d",
        r"(?i)plaintiff.*defendant",
    ],
    "numbered_paragraphs": [
        r"^\s*\d+\.\s+",
    ],
    "signature_block": [
        r"(?i)respectfully submitted",
        r"(?i)andrew pigors.*pro se",
        r"_{5,}",
    ],
    "certificate_of_service": [
        r"(?i)certificate of service",
    ],
    "proposed_order": [
        r"(?i)proposed order|order granting",
        r"(?i)it is (?:so |hereby )?ordered",
    ],
    "table_of_contents": [
        r"(?i)table of contents",
    ],
    "table_of_authorities": [
        r"(?i)table of authorities",
    ],
    "statement_of_jurisdiction": [
        r"(?i)statement of jurisdiction|jurisdictional statement",
    ],
    "statement_of_questions": [
        r"(?i)questions? presented|statement of (?:the )?(?:issues?|questions?)",
    ],
    "statement_of_facts": [
        r"(?i)statement of facts|factual background",
    ],
    "argument": [
        r"(?i)^#{1,3}\s*argument|^argument\s*$|^I{1,3}\.\s+",
    ],
    "relief_requested": [
        r"(?i)relief requested|prayer for relief|wherefore",
    ],
    "word_count_certification": [
        r"(?i)word count|certif.*\d+.*words",
    ],
    "appendix": [
        r"(?i)appendix|exhibit\s+[a-z]",
    ],
    "questions_presented": [
        r"(?i)questions? presented",
    ],
    "proof_of_service": [
        r"(?i)proof of service|affidavit of service",
    ],
    "civil_cover_sheet": [
        r"(?i)js.?44|civil cover sheet",
    ],
    "summons": [
        r"(?i)summons",
    ],
    "complaint_narrative": [
        r"(?i)complaint|petition|narrative",
    ],
    "supporting_evidence": [
        r"(?i)exhibit|attachment|evidence|supporting doc",
    ],
    "signature": [
        r"(?i)sign|_{5,}|andrew pigors",
    ],
    "complaint_or_motion": [
        r"(?i)complaint|motion|petition",
    ],
}


class MultiForumCompliance:
    """Cross-jurisdictional filing compliance validation engine."""

    def __init__(self):
        self._cache: Dict = {}

    # ── 1. Validate Filing ───────────────────────────────────────────

    def validate_filing(self, params: Dict) -> Dict:
        """
        Validate a filing against its target forum's requirements.

        params:
            filing_path: str — path to the filing document (md or txt)
            forum:       str — target forum key from FORUM_SPECS
            filing_type: str — 'brief', 'motion', 'reply', 'application', 'complaint'
        """
        filing_path = params.get("filing_path", "").strip()
        forum = params.get("forum", "").strip().lower()
        filing_type = params.get("filing_type", "brief").strip().lower()

        if not filing_path:
            return {"error": "filing_path is required"}
        if forum not in FORUM_SPECS:
            return {
                "error": f"Unknown forum: {forum}",
                "valid_forums": list(FORUM_SPECS.keys()),
            }

        spec = FORUM_SPECS[forum]

        # Read the filing content
        content = ""
        try:
            with open(filing_path, "r", encoding="utf-8", errors="replace") as f:
                content = f.read()
        except FileNotFoundError:
            return {"error": f"File not found: {filing_path}"}
        except Exception as e:
            return {"error": f"Cannot read file: {str(e)[:200]}"}

        if not content.strip():
            return {"error": "Filing is empty"}

        # Run all checks
        issues: List[Dict] = []
        warnings: List[str] = []
        score = 100

        # 1. Check required structural elements
        element_results = self._check_elements(content, spec["required_elements"])
        for elem, found in element_results.items():
            if not found:
                issues.append({
                    "type": "missing_element",
                    "element": elem,
                    "severity": "error",
                    "rule": self._get_element_rule(forum, elem),
                })
                score -= 8

        # 2. Check page limits
        page_limits = spec.get("page_limits") or {}
        limit = page_limits.get(filing_type)
        if limit:
            # Rough page estimation: ~250 words per page double-spaced
            word_count = len(content.split())
            est_pages = word_count / 250
            if est_pages > limit:
                issues.append({
                    "type": "page_limit_exceeded",
                    "estimated_pages": round(est_pages, 1),
                    "limit": limit,
                    "severity": "error",
                    "rule": f"{spec['name']} — {filing_type} limit: {limit} pages",
                })
                score -= 15

        # 3. Check word limits
        word_limits = spec.get("word_limits") or {}
        wlimit = word_limits.get(filing_type)
        if wlimit:
            word_count = len(content.split())
            if word_count > wlimit:
                issues.append({
                    "type": "word_limit_exceeded",
                    "word_count": word_count,
                    "limit": wlimit,
                    "severity": "error",
                    "rule": f"Word limit: {wlimit} for {filing_type}",
                })
                score -= 15

        # 4. Check formatting markers
        fmt_issues = self._check_formatting(content, spec["formatting"], forum)
        issues.extend(fmt_issues)
        score -= len(fmt_issues) * 5

        # 5. Check for placeholders (unfilled brackets)
        placeholder_re = re.compile(
            r'\[(?:DATE|NAME|ADDRESS|CASE NUMBER|SPECIFY|CITY|STATE|ZIP'
            r'|COURT|JUDGE|PHONE|EMAIL)[^\]]*\]',
            re.IGNORECASE,
        )
        placeholders = placeholder_re.findall(content)
        if placeholders:
            unique = list(set(placeholders))
            issues.append({
                "type": "unresolved_placeholders",
                "count": len(placeholders),
                "examples": unique[:5],
                "severity": "warning",
            })
            score -= len(unique) * 3

        # 6. Check citation format
        cite_issues = self._check_citations(content, forum)
        warnings.extend(cite_issues)

        # 7. MSC-specific: 13 copies reminder
        if forum == "supreme_court":
            warnings.append(
                "REMINDER: MSC requires 13 copies of the filing "
                "per MCR 7.306(B). Ensure copies are prepared."
            )

        # 8. Federal-specific: JS-44 and CM/ECF
        if forum == "federal_usdc":
            if "js-44" not in content.lower() and "civil cover" not in content.lower():
                warnings.append(
                    "Federal filing requires JS-44 Civil Cover Sheet. "
                    "Ensure it is prepared as a separate attachment."
                )

        compliant = len([i for i in issues if i.get("severity") == "error"]) == 0

        return {
            "filing_path": filing_path,
            "forum": forum,
            "forum_name": spec["name"],
            "filing_type": filing_type,
            "compliant": compliant,
            "score": max(0, min(100, score)),
            "word_count": len(content.split()),
            "issues": issues,
            "warnings": warnings,
            "elements_found": {
                k: v for k, v in element_results.items()
            },
            "formatting_requirements": spec["formatting"],
            "filing_method": spec["filing_method"],
            "copies_required": spec.get("copies", 1),
        }

    def _check_elements(
        self, content: str, required: List[str]
    ) -> Dict[str, bool]:
        """Check which required structural elements are present."""
        results: Dict[str, bool] = {}
        for elem in required:
            patterns = _ELEMENT_PATTERNS.get(elem, [])
            found = False
            for pat in patterns:
                if re.search(pat, content, re.MULTILINE):
                    found = True
                    break
            results[elem] = found
        return results

    def _check_formatting(
        self, content: str, fmt: Dict, forum: str
    ) -> List[Dict]:
        """Check formatting compliance heuristics."""
        issues: List[Dict] = []

        # Certificate of Service check (required in all MI courts)
        if fmt.get("cos") and "certificate of service" not in content.lower():
            issues.append({
                "type": "missing_cos",
                "severity": "error",
                "rule": fmt["cos"],
                "detail": "Certificate of Service is REQUIRED on every filing",
            })

        # Proposed order check (circuit court motions)
        if fmt.get("proposed_order"):
            if (
                "proposed order" not in content.lower()
                and "order granting" not in content.lower()
                and "it is so ordered" not in content.lower()
            ):
                issues.append({
                    "type": "missing_proposed_order",
                    "severity": "warning",
                    "rule": fmt["proposed_order"],
                    "detail": "Motions should include a proposed order",
                })

        # Word count certification (COA briefs)
        if fmt.get("word_count_cert"):
            if not re.search(r"(?i)certif.*word|word.*count", content):
                issues.append({
                    "type": "missing_word_count_cert",
                    "severity": "error",
                    "rule": fmt["word_count_cert"],
                    "detail": "COA briefs require word count certification",
                })

        return issues

    def _check_citations(self, content: str, forum: str) -> List[str]:
        """Check that citations match expected patterns for forum."""
        warnings: List[str] = []
        mi_cite = re.compile(
            r'(MCR|MCL|MRE)\s+\d+(?:\.\d+)+(?:\([A-Za-z0-9]+\))*'
        )
        fed_cite = re.compile(
            r'(\d+\s+(?:USC|U\.S\.C\.|F\.\d+d?|S\.\s*Ct\.))'
        )

        has_mi = bool(mi_cite.search(content))
        has_fed = bool(fed_cite.search(content))

        if forum in ("circuit_court", "court_of_appeals", "supreme_court"):
            if not has_mi:
                warnings.append(
                    "No Michigan citations (MCR/MCL/MRE) found — "
                    "Michigan courts expect Michigan authority"
                )
        elif forum == "federal_usdc":
            if not has_fed:
                warnings.append(
                    "No federal citations (USC/F.3d/S.Ct.) found — "
                    "federal court expects federal authority"
                )

        return warnings

    def _get_element_rule(self, forum: str, element: str) -> str:
        """Return the governing rule for a required element."""
        rules_map: Dict[str, Dict[str, str]] = {
            "circuit_court": {
                "caption": "MCR 2.113(C)",
                "numbered_paragraphs": "MCR 2.113(E)",
                "signature_block": "MCR 2.114",
                "certificate_of_service": "MCR 2.107",
                "proposed_order": "MCR 2.119(A)(2)",
            },
            "court_of_appeals": {
                "caption": "MCR 7.212(B)",
                "table_of_contents": "MCR 7.212(C)(1)",
                "table_of_authorities": "MCR 7.212(C)(2)",
                "statement_of_jurisdiction": "MCR 7.212(C)(3)",
                "statement_of_questions": "MCR 7.212(C)(4)",
                "statement_of_facts": "MCR 7.212(C)(5)",
                "argument": "MCR 7.212(C)(6)",
                "relief_requested": "MCR 7.212(C)(7)",
                "appendix": "MCR 7.212(C)(8)",
                "word_count_certification": "MCR 7.212(B)",
                "certificate_of_service": "MCR 7.209(A)",
                "signature_block": "MCR 7.212(B)",
            },
            "supreme_court": {
                "caption": "MCR 7.306(B)",
                "questions_presented": "MCR 7.306(B)(1)",
                "statement_of_facts": "MCR 7.306(B)(2)",
                "appendix": "MCR 7.306(B)(3)",
                "certificate_of_service": "MCR 7.305(A)",
                "proof_of_service": "MCR 7.305(A)",
                "signature_block": "MCR 7.306(B)",
            },
            "federal_usdc": {
                "caption": "FRCP 10(a)",
                "civil_cover_sheet": "LCivR 5.1 / JS-44",
                "certificate_of_service": "FRCP 5(d)(1)(B)",
                "signature_block": "FRCP 11(a)",
                "summons": "FRCP 4(b)",
            },
            "jtc": {
                "complaint_narrative": "MCR 9.220",
                "supporting_evidence": "MCR 9.220",
                "signature": "MCR 9.220",
            },
        }
        return rules_map.get(forum, {}).get(element, "See court rules")

    # ── 2. Cross-Forum Matrix ────────────────────────────────────────

    def cross_forum_matrix(self, params: Dict) -> Dict:
        """
        Show compliance status of all filings across all forums.

        params:
            filings_dir: str — directory containing filing documents (optional)
        """
        filings_dir = params.get("filings_dir", "").strip()

        # Known filing packages from the case
        known_filings = [
            {
                "name": "MSC Complaint Superintending Control",
                "path": r"C:\Users\andre\LitigationOS\04_MSC\MSC_COMPLAINT_SUPERINTENDING_CONTROL_v2.md",
                "target_forum": "supreme_court",
                "type": "application",
            },
            {
                "name": "JTC Formal Complaint",
                "path": r"C:\Users\andre\LitigationOS\03_JTC\JTC_FORMAL_COMPLAINT_v2.md",
                "target_forum": "jtc",
                "type": "complaint",
            },
            {
                "name": "Emergency Motion Restore Parenting Time",
                "path": r"C:\Users\andre\LitigationOS\LANE_A\EMERGENCY_MOTION_RESTORE_PARENTING_TIME_v2.md",
                "target_forum": "circuit_court",
                "type": "motion",
            },
            {
                "name": "Motion for Reconsideration",
                "path": r"C:\Users\andre\LitigationOS\LANE_A\MOTION_FOR_RECONSIDERATION_v2.md",
                "target_forum": "circuit_court",
                "type": "motion",
            },
            {
                "name": "COA Appellant Brief 366810",
                "path": r"C:\Users\andre\LitigationOS\LANE_F\COA_APPELLANT_BRIEF_366810_v2.md",
                "target_forum": "court_of_appeals",
                "type": "brief",
            },
        ]

        # Optionally scan filings_dir for additional .md files
        if filings_dir and os.path.isdir(filings_dir):
            for fname in os.listdir(filings_dir):
                if fname.endswith(".md") and not any(
                    f["name"] in fname for f in known_filings
                ):
                    known_filings.append({
                        "name": fname.replace(".md", "").replace("_", " "),
                        "path": os.path.join(filings_dir, fname),
                        "target_forum": "circuit_court",
                        "type": "motion",
                    })

        matrix: List[Dict] = []
        for filing in known_filings:
            fpath = filing["path"]
            exists = os.path.isfile(fpath)

            entry: Dict[str, Any] = {
                "filing_name": filing["name"],
                "path": fpath,
                "target_forum": filing["target_forum"],
                "filing_type": filing["type"],
                "file_exists": exists,
                "compliance": {},
            }

            if exists:
                result = self.validate_filing({
                    "filing_path": fpath,
                    "forum": filing["target_forum"],
                    "filing_type": filing["type"],
                })
                entry["compliance"] = {
                    "compliant": result.get("compliant", False),
                    "score": result.get("score", 0),
                    "issue_count": len(result.get("issues", [])),
                    "word_count": result.get("word_count", 0),
                    "critical_issues": [
                        i for i in result.get("issues", [])
                        if i.get("severity") == "error"
                    ][:5],
                }
            else:
                entry["compliance"] = {
                    "compliant": False,
                    "score": 0,
                    "issue_count": 1,
                    "critical_issues": [{"type": "file_missing", "severity": "error"}],
                }

            matrix.append(entry)

        total = len(matrix)
        compliant_count = sum(
            1 for m in matrix
            if m["compliance"].get("compliant", False)
        )

        return {
            "as_of": datetime.now().strftime("%Y-%m-%d %H:%M"),
            "total_filings": total,
            "compliant": compliant_count,
            "non_compliant": total - compliant_count,
            "compliance_pct": round(
                compliant_count / total * 100, 1
            ) if total else 0,
            "matrix": matrix,
        }

    # ── 3. Format Requirements ───────────────────────────────────────

    def format_requirements(self, params: Dict) -> Dict:
        """
        Return formatting requirements for a specific forum.

        params:
            forum: str — forum key from FORUM_SPECS
        """
        forum = params.get("forum", "").strip().lower()

        if forum and forum in FORUM_SPECS:
            spec = FORUM_SPECS[forum]
            return {
                "forum": forum,
                "name": spec["name"],
                "formatting": spec["formatting"],
                "required_elements": spec["required_elements"],
                "page_limits": spec["page_limits"],
                "word_limits": spec["word_limits"],
                "filing_method": spec["filing_method"],
                "filing_fee": spec.get("filing_fee", "Unknown"),
                "copies": spec.get("copies", 1),
            }
        else:
            # Return all forums
            return {
                "forums": {
                    k: {
                        "name": v["name"],
                        "formatting": v["formatting"],
                        "required_elements": v["required_elements"],
                        "page_limits": v["page_limits"],
                        "word_limits": v["word_limits"],
                        "filing_method": v["filing_method"],
                        "copies": v.get("copies", 1),
                    }
                    for k, v in FORUM_SPECS.items()
                }
            }

    # ── 4. Filing Checklist ──────────────────────────────────────────

    def filing_checklist(self, params: Dict) -> Dict:
        """
        Generate comprehensive filing checklist for a specific forum.

        params:
            forum:       str — target forum key
            filing_type: str — 'brief', 'motion', 'reply', 'application', 'complaint'
            case_number: str — case number
        """
        forum = params.get("forum", "").strip().lower()
        filing_type = params.get("filing_type", "motion").strip().lower()
        case_number = params.get("case_number", "2024-001507-DC")

        if forum not in FORUM_SPECS:
            return {
                "error": f"Unknown forum: {forum}",
                "valid_forums": list(FORUM_SPECS.keys()),
            }

        spec = FORUM_SPECS[forum]
        checklist: List[Dict] = []

        # Pre-filing checks
        checklist.append({
            "category": "pre_filing",
            "item": "Verify case number and caption accuracy",
            "rule": spec["formatting"].get("caption", "Court rules"),
            "critical": True,
        })
        checklist.append({
            "category": "pre_filing",
            "item": "Confirm filing deadline has not passed",
            "rule": "Various — check deadline_calculator",
            "critical": True,
        })

        # Document formatting
        for key, value in spec["formatting"].items():
            if key in ("no_specific_format",):
                continue
            checklist.append({
                "category": "formatting",
                "item": f"{key.replace('_', ' ').title()}: {value}",
                "rule": value if isinstance(value, str) and "MCR" in str(value) else "",
                "critical": False,
            })

        # Required structural elements
        for elem in spec["required_elements"]:
            checklist.append({
                "category": "required_element",
                "item": f"Include {elem.replace('_', ' ')}",
                "rule": self._get_element_rule(forum, elem),
                "critical": elem in (
                    "caption", "signature_block",
                    "certificate_of_service", "word_count_certification",
                ),
            })

        # Page/word limits
        page_limits = spec.get("page_limits") or {}
        plimit = page_limits.get(filing_type)
        if plimit:
            checklist.append({
                "category": "limits",
                "item": f"Page limit: {plimit} pages for {filing_type}",
                "rule": f"{spec['name']} rules",
                "critical": True,
            })

        word_limits = spec.get("word_limits") or {}
        wlimit = word_limits.get(filing_type)
        if wlimit:
            checklist.append({
                "category": "limits",
                "item": f"Word limit: {wlimit:,} words for {filing_type}",
                "rule": f"{spec['name']} rules",
                "critical": True,
            })

        # Filing logistics
        checklist.append({
            "category": "filing",
            "item": f"Filing method: {spec['filing_method']}",
            "rule": "",
            "critical": True,
        })
        if spec.get("copies", 1) > 1:
            checklist.append({
                "category": "filing",
                "item": f"Prepare {spec['copies']} copies",
                "rule": spec["formatting"].get("copies", ""),
                "critical": True,
            })
        if spec.get("filing_fee"):
            checklist.append({
                "category": "filing",
                "item": f"Filing fee: {spec['filing_fee']}",
                "rule": "",
                "critical": False,
            })

        # Service of process
        checklist.append({
            "category": "service",
            "item": "Complete service on all required parties",
            "rule": "See service_tracker skill",
            "critical": True,
        })
        checklist.append({
            "category": "service",
            "item": "Attach Certificate of Service",
            "rule": spec["formatting"].get("cos", "Required on all filings"),
            "critical": True,
        })

        # Post-filing
        checklist.append({
            "category": "post_filing",
            "item": "Retain file-stamped copy for records",
            "rule": "",
            "critical": False,
        })
        checklist.append({
            "category": "post_filing",
            "item": "Calendar any response deadlines triggered by filing",
            "rule": "",
            "critical": True,
        })

        # Forum-specific extras
        if forum == "supreme_court":
            checklist.append({
                "category": "forum_specific",
                "item": "File 13 copies at MSC Clerk, Lansing MI",
                "rule": "MCR 7.306(B)",
                "critical": True,
            })
            checklist.append({
                "category": "forum_specific",
                "item": "Serve copy on Court of Appeals",
                "rule": "MCR 7.305(A)",
                "critical": True,
            })

        if forum == "court_of_appeals":
            checklist.append({
                "category": "forum_specific",
                "item": "File via TrueFiling — include appendix",
                "rule": "MCR 7.212(C)(8)",
                "critical": True,
            })

        if forum == "federal_usdc":
            checklist.append({
                "category": "forum_specific",
                "item": "Register for CM/ECF if not already registered",
                "rule": "USDC WD Mich LCivR 5.1",
                "critical": True,
            })
            checklist.append({
                "category": "forum_specific",
                "item": "Prepare JS-44 Civil Cover Sheet",
                "rule": "Local Rule",
                "critical": True,
            })

        total = len(checklist)
        critical = sum(1 for c in checklist if c["critical"])

        return {
            "forum": forum,
            "forum_name": spec["name"],
            "case_number": case_number,
            "filing_type": filing_type,
            "total_items": total,
            "critical_items": critical,
            "checklist": checklist,
        }

    # ── 5. Identify Conflicts ────────────────────────────────────────

    def identify_conflicts(self, params: Dict) -> Dict:
        """
        Identify conflicting requirements when filing in multiple forums.

        params:
            forums: list[str] — list of forum keys to compare
        """
        forums_list = params.get("forums", list(FORUM_SPECS.keys()))
        if isinstance(forums_list, str):
            forums_list = [f.strip() for f in forums_list.split(",")]

        valid_forums = [f for f in forums_list if f in FORUM_SPECS]
        if len(valid_forums) < 2:
            return {
                "error": "Need at least 2 valid forums to compare",
                "valid_forums": list(FORUM_SPECS.keys()),
            }

        conflicts: List[Dict] = []
        advisories: List[str] = []

        specs = {f: FORUM_SPECS[f] for f in valid_forums}

        # 1. Font conflicts
        fonts = {
            f: specs[f]["formatting"].get("font", "unspecified")
            for f in valid_forums
        }
        unique_fonts = set(fonts.values()) - {"unspecified"}
        if len(unique_fonts) > 1:
            conflicts.append({
                "type": "font_conflict",
                "severity": "error",
                "detail": "Different font requirements across forums",
                "forums": fonts,
                "resolution": (
                    "Use 12pt Times New Roman for MI state courts. "
                    "Create separate version with 14pt for USDC WD Mich."
                ),
            })

        # 2. Page/word limit differences
        for filing_type in ("brief", "reply", "motion", "application"):
            limits: Dict[str, Any] = {}
            for f in valid_forums:
                pl = (specs[f].get("page_limits") or {}).get(filing_type)
                wl = (specs[f].get("word_limits") or {}).get(filing_type)
                if pl or wl:
                    limits[f] = {"pages": pl, "words": wl}
            if len(limits) > 1:
                advisories.append(
                    f"'{filing_type}' has different limits across forums: "
                    + ", ".join(
                        f"{f}: {v}" for f, v in limits.items()
                    )
                )

        # 3. Filing method conflicts
        methods = {f: specs[f]["filing_method"] for f in valid_forums}
        has_paper = any("paper" in m.lower() or "mail" in m.lower() for m in methods.values())
        has_electronic = any("electronic" in m.lower() or "cm/ecf" in m.lower() or "truefiling" in m.lower() for m in methods.values())
        if has_paper and has_electronic:
            conflicts.append({
                "type": "filing_method_conflict",
                "severity": "warning",
                "detail": "Mix of paper and electronic filing required",
                "forums": methods,
                "resolution": (
                    "MSC requires 13 paper copies. COA uses TrueFiling. "
                    "USDC uses CM/ECF. Circuit uses MiFILE. JTC is mail only. "
                    "Prepare both electronic and paper versions."
                ),
            })

        # 4. Copy requirements
        copies = {
            f: specs[f].get("copies", 1) for f in valid_forums
        }
        if max(copies.values()) > 1:
            conflicts.append({
                "type": "copy_requirement",
                "severity": "advisory",
                "detail": "Different copy requirements",
                "forums": copies,
                "resolution": "MSC requires 13 copies. Plan print logistics.",
            })

        # 5. Caption format differences
        captions = {}
        for f in valid_forums:
            cap = specs[f]["formatting"].get("caption", "")
            if cap:
                captions[f] = cap
        if len(set(captions.values())) > 1:
            conflicts.append({
                "type": "caption_format",
                "severity": "warning",
                "detail": "Different caption requirements per forum",
                "forums": captions,
                "resolution": (
                    "Each forum requires its own caption format. "
                    "Create forum-specific versions of each filing."
                ),
            })

        # 6. Citation style advisory
        mi_forums = [f for f in valid_forums if f in ("circuit_court", "court_of_appeals", "supreme_court")]
        fed_forums = [f for f in valid_forums if f == "federal_usdc"]
        if mi_forums and fed_forums:
            advisories.append(
                "MI courts expect MCR/MCL/MRE citations. "
                "Federal court expects USC/F.3d citations. "
                "Dual-cite constitutional provisions (e.g., "
                "Const 1963, art 6, § 4 AND US Const amend XIV)."
            )

        # 7. Service requirement differences
        advisories.append(
            "Service requirements differ: Circuit (MCR 2.107), "
            "COA (MCR 7.209), MSC (MCR 7.305), Federal (FRCP 5), "
            "JTC (MCR 9.220). Use service_tracker for compliance."
        )

        return {
            "forums_compared": valid_forums,
            "conflict_count": len(conflicts),
            "advisory_count": len(advisories),
            "conflicts": conflicts,
            "advisories": advisories,
            "summary": (
                f"Found {len(conflicts)} conflict(s) and "
                f"{len(advisories)} advisory note(s) across "
                f"{len(valid_forums)} forums. "
                + (
                    "All conflicts are resolvable with forum-specific versions."
                    if conflicts
                    else "No critical conflicts detected."
                )
            ),
        }


# ── CLI ──────────────────────────────────────────────────────────────
if __name__ == "__main__":
    engine = MultiForumCompliance()

    if len(sys.argv) > 1:
        cmd = sys.argv[1]
        if cmd == "--validate" and len(sys.argv) > 3:
            result = engine.validate_filing({
                "filing_path": sys.argv[2],
                "forum": sys.argv[3],
                "filing_type": sys.argv[4] if len(sys.argv) > 4 else "motion",
            })
        elif cmd == "--matrix":
            fdir = sys.argv[2] if len(sys.argv) > 2 else ""
            result = engine.cross_forum_matrix({"filings_dir": fdir})
        elif cmd == "--format":
            forum = sys.argv[2] if len(sys.argv) > 2 else ""
            result = engine.format_requirements({"forum": forum})
        elif cmd == "--checklist" and len(sys.argv) > 2:
            result = engine.filing_checklist({
                "forum": sys.argv[2],
                "filing_type": sys.argv[3] if len(sys.argv) > 3 else "motion",
            })
        elif cmd == "--conflicts":
            forums = sys.argv[2:] if len(sys.argv) > 2 else list(FORUM_SPECS.keys())
            result = engine.identify_conflicts({"forums": forums})
        else:
            result = {
                "error": "Unknown command",
                "usage": (
                    "python multi_forum_compliance.py "
                    "--validate <path> <forum> [type] | "
                    "--matrix [dir] | "
                    "--format [forum] | "
                    "--checklist <forum> [type] | "
                    "--conflicts [forum1 forum2 ...]"
                ),
            }
    else:
        result = engine.format_requirements({})

    cycle_json(result)
