# -*- coding: utf-8 -*-
"""Engine 14: Local Rule Checker — 14th Circuit & multi-court compliance.

Checks compliance with local administrative orders for:
  - 14th Judicial Circuit (Muskegon County)
  - Michigan Court of Appeals (Grand Rapids)
  - Michigan Supreme Court (Lansing)
  - U.S. District Court, Western District of Michigan

Authority:
    MCR 8.112(B)  — Local court rules supplement MCRs
    MCR 2.113     — Form of pleadings (statewide)
    MCR 7.212     — Appellate briefs
    MCR 7.306     — MSC original proceedings
    W.D. Mich. LCivR — Federal local civil rules
"""
import sys
import os
import io
import re
import json
import sqlite3
from datetime import datetime
from typing import Dict, List, Optional

# ── UTF-8 fix for Windows console ───────────────────────────────────────────
if sys.stdout and hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
elif sys.stdout is None or not hasattr(sys.stdout, "encoding") or sys.stdout.encoding != "utf-8":
    sys.stdout = io.TextIOWrapper(
        sys.stdout.buffer if sys.stdout else open(os.devnull, "w"), encoding="utf-8"
    )
if sys.stderr and hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8")

DB_PATH = r"C:\Users\andre\LitigationOS\litigation_context.db"

# ── Court-specific local rules ──────────────────────────────────────────────

LOCAL_RULES: Dict[str, Dict] = {
    "14th_circuit": {
        "court_name": "14th Judicial Circuit Court — Muskegon County",
        "authority": "MCR 8.112(B); 14th Circuit Administrative Orders",
        "efiling_system": "MiFile",
        "efiling_required": True,
        "format": {
            "paper_size": "8.5 x 11 inches (letter)",
            "font": "12-point Times New Roman or equivalent serif",
            "margins": "1 inch on all sides",
            "spacing": "Double-spaced (except quotes over 50 words)",
            "page_numbers": "Bottom center, starting page 1",
            "caption_required": True,
            "numbered_paragraphs": True,
            "signature_block": True,
            "certificate_of_service": True,
            "authority": "MCR 2.113(A)-(C); MCR 2.119(A)(1)",
        },
        "motion_practice": {
            "notice_period_days": 9,
            "mail_add_days": 3,
            "efiling_add_days": 0,
            "brief_required": True,
            "proposed_order_required": True,
            "notice_of_hearing_required": True,
            "scheduling": "Contact clerk's office or schedule through MiFile",
            "ex_parte_requirements": [
                "Affidavit stating irreparable harm",
                "Specific facts — not conclusions",
                "Proposed order",
                "MCR 3.207(C)(2) requirements for custody matters",
            ],
            "authority": "MCR 2.119(C)(1); MCR 2.119(A)(2)",
        },
        "pro_se_requirements": {
            "self_represented": True,
            "must_sign_all_filings": True,
            "address_required_on_filings": True,
            "phone_required": True,
            "email_required_for_efiling": True,
            "held_to_same_rules": True,
            "foc_referral_available": True,
            "self_help_center": "Muskegon County Self-Help Center",
            "authority": "MCR 2.114; MCR 2.117(A)",
            "warnings": [
                "Pro se litigants are held to same procedural rules as attorneys",
                "Failure to comply with MCR can result in filing rejection",
                "Must provide address for service — MCR 2.107(B)(1)",
            ],
        },
        "hearing_procedures": {
            "scheduling_method": "MiFile or contact Court Clerk",
            "telephonic_available": True,
            "video_available": True,
            "zoom_platform": "Zoom (check specific judge preferences)",
            "in_person_default": False,
            "arrive_early_minutes": 15,
            "dress_code": "Business attire recommended",
            "recording_prohibited": True,
            "authority": "14th Circuit AO; MCR 2.402",
        },
        "efiling_rules": {
            "system": "MiFile (Michigan Court Filing)",
            "mandatory": True,
            "exceptions": ["PPO petitions (may file in person)", "Fee waiver applications"],
            "file_format": "PDF (text-searchable preferred)",
            "max_file_size_mb": 50,
            "accepted_formats": ["PDF"],
            "filing_time_cutoff": "11:59 PM ET (filed date = submission date)",
            "service_via_efiling": True,
            "authority": "MCR 1.109(G); SCAO Administrative Order 2019-08",
        },
    },
    "coa": {
        "court_name": "Michigan Court of Appeals",
        "authority": "MCR Ch. 7; COA Internal Operating Procedures",
        "efiling_system": "TrueFiling",
        "efiling_required": True,
        "format": {
            "paper_size": "8.5 x 11 inches",
            "font": "12-point Times New Roman, 14-point for proportional",
            "margins": "1 inch on all sides",
            "spacing": "Double-spaced body; single-space quotes, footnotes",
            "page_limit_brief": 50,
            "word_limit_brief": 16000,
            "page_numbers": "Bottom center",
            "caption_required": True,
            "table_of_contents": True,
            "table_of_authorities": True,
            "statement_of_jurisdiction": True,
            "statement_of_questions": True,
            "authority": "MCR 7.212(B)-(D)",
        },
        "motion_practice": {
            "notice_period_days": 7,
            "page_limit": 20,
            "brief_with_motion": True,
            "certificate_of_service": True,
            "authority": "MCR 7.211(B)",
        },
        "pro_se_requirements": {
            "same_rules_apply": True,
            "clerk_assistance_limited": True,
            "self_help_resources": "Michigan Courts Self-Help Website",
            "authority": "MCR 7.201; COA IOP",
            "warnings": [
                "COA strictly enforces formatting and deadline requirements",
                "Pro se status does not excuse noncompliance",
                "Late filings WILL be rejected",
            ],
        },
        "efiling_rules": {
            "system": "TrueFiling",
            "mandatory": True,
            "url": "https://www.truefiling.com",
            "file_format": "PDF (text-searchable required)",
            "max_file_size_mb": 25,
            "bookmarks_required": True,
            "service_via_efiling": True,
            "copies_required": 0,
            "authority": "MCR 7.202(1); COA Administrative Order",
        },
    },
    "msc": {
        "court_name": "Michigan Supreme Court",
        "authority": "MCR 7.3xx; MSC Administrative Orders",
        "efiling_system": "TrueFiling",
        "efiling_required": True,
        "format": {
            "paper_size": "8.5 x 11 inches",
            "font": "12-point Times New Roman",
            "margins": "1 inch on all sides",
            "spacing": "Double-spaced",
            "page_limit_application": 50,
            "word_limit_application": 16000,
            "page_numbers": "Bottom center",
            "caption_required": True,
            "table_of_contents": True,
            "table_of_authorities": True,
            "copies_paper": 13,
            "authority": "MCR 7.306(B); MCR 7.305(B)",
        },
        "original_action_requirements": {
            "complaint_required": True,
            "verification_required": True,
            "appendix_required": True,
            "proof_of_service": True,
            "fee_or_waiver": True,
            "copies": 13,
            "items_in_appendix": [
                "Lower court opinion/order being challenged",
                "Relevant pleadings from lower court",
                "Transcript excerpts (if available)",
                "Constitutional/statutory provisions at issue",
            ],
            "authority": "MCR 7.306(B)(1)-(4)",
        },
        "pro_se_requirements": {
            "same_rules_apply": True,
            "strict_compliance": True,
            "authority": "MCR 7.306",
            "warnings": [
                "MSC is extremely strict on formatting",
                "Non-compliant filings are returned without action",
                "13 paper copies required even with e-filing",
            ],
        },
        "efiling_rules": {
            "system": "TrueFiling",
            "mandatory": True,
            "paper_copies_also_required": True,
            "paper_copy_count": 13,
            "file_format": "PDF (text-searchable)",
            "max_file_size_mb": 25,
            "authority": "MSC Administrative Order; MCR 7.306",
        },
    },
    "usdc_wdmi": {
        "court_name": "U.S. District Court, Western District of Michigan",
        "authority": "W.D. Mich. LCivR; FRCP",
        "efiling_system": "CM/ECF (PACER)",
        "efiling_required": True,
        "format": {
            "paper_size": "8.5 x 11 inches",
            "font": "12-point or 14-point proportional; courier allowed",
            "margins": "1 inch on all sides",
            "spacing": "Double-spaced",
            "page_numbers": "Bottom center",
            "caption_required": True,
            "numbered_paragraphs": True,
            "authority": "W.D. Mich. LCivR 10.1; FRCP 10",
        },
        "motion_practice": {
            "notice_period_days": 14,
            "brief_required": True,
            "page_limit_brief": 25,
            "word_limit": 8000,
            "concurrence_statement_required": True,
            "proposed_order_required": False,
            "authority": "W.D. Mich. LCivR 7.1; FRCP 6(c)",
        },
        "pro_se_requirements": {
            "must_register_cm_ecf": True,
            "pro_se_guide_available": True,
            "authority": "W.D. Mich. LCivR 83.1",
            "warnings": [
                "Federal court enforces rules strictly",
                "Must obtain CM/ECF login for e-filing",
                "IFP application required if cannot pay fees",
            ],
        },
        "efiling_rules": {
            "system": "CM/ECF (PACER)",
            "mandatory": True,
            "registration_required": True,
            "file_format": "PDF",
            "max_file_size_mb": 50,
            "service_via_ecf": True,
            "authority": "W.D. Mich. LCivR 5.7",
        },
    },
}

# ── Compliance check rules ──────────────────────────────────────────────────

COMPLIANCE_CHECKS: Dict[str, Dict] = {
    "caption": {
        "description": "Caption present with correct case number and parties",
        "authority": "MCR 2.113(A)",
        "required_for": ["motion", "brief", "complaint", "response", "affidavit",
                         "proposed_order", "notice", "proof_of_service"],
        "check": lambda text: bool(
            re.search(r"(?:STATE OF MICHIGAN|COURT OF APPEALS|SUPREME COURT)", text, re.I)
            and re.search(r"(?:Plaintiff|Appellant|Petitioner)", text, re.I)
        ),
    },
    "numbered_paragraphs": {
        "description": "Paragraphs are numbered per MCR 2.113(B)",
        "authority": "MCR 2.113(B)",
        "required_for": ["motion", "complaint", "response", "affidavit"],
        "check": lambda text: bool(re.search(r"(?:\n\s*\d+\.\s+|\n\s*¶\s*\d+)", text)),
    },
    "signature_block": {
        "description": "Signature block with name, address, phone, bar number / pro se",
        "authority": "MCR 2.114(A)",
        "required_for": ["motion", "brief", "complaint", "response", "affidavit",
                         "proposed_order", "proof_of_service"],
        "check": lambda text: bool(
            re.search(r"(?:Respectfully\s+submitted|/s/|___+)", text, re.I)
        ),
    },
    "certificate_of_service": {
        "description": "Certificate of Service attached",
        "authority": "MCR 2.107(D)",
        "required_for": ["motion", "brief", "complaint", "response", "notice"],
        "check": lambda text: bool(
            re.search(r"(?:CERTIFICATE\s+OF\s+SERVICE|PROOF\s+OF\s+SERVICE)", text, re.I)
        ),
    },
    "verification": {
        "description": "Verification statement under penalty of perjury",
        "authority": "MCR 2.114(A)",
        "required_for": ["affidavit", "complaint", "msc_complaint"],
        "check": lambda text: bool(
            re.search(
                r"(?:under\s+penalty\s+of\s+perjury|sworn\s+and\s+subscribed|"
                r"verified\s+under\s+oath)",
                text, re.I,
            )
        ),
    },
    "proposed_order": {
        "description": "Proposed order included with motion",
        "authority": "MCR 2.119(A)(2)",
        "required_for": ["motion"],
        "check": lambda text: bool(
            re.search(r"(?:PROPOSED\s+ORDER|ORDER\s+GRANTING|IT\s+IS\s+(?:HEREBY\s+)?ORDERED)", text, re.I)
        ),
    },
    "table_of_contents": {
        "description": "Table of Contents included",
        "authority": "MCR 7.212(C)",
        "required_for": ["appellate_brief", "msc_application"],
        "check": lambda text: bool(
            re.search(r"TABLE\s+OF\s+CONTENTS", text, re.I)
        ),
    },
    "table_of_authorities": {
        "description": "Table of Authorities included",
        "authority": "MCR 7.212(C)",
        "required_for": ["appellate_brief", "msc_application"],
        "check": lambda text: bool(
            re.search(r"TABLE\s+OF\s+AUTHORITIES", text, re.I)
        ),
    },
    "statement_of_questions": {
        "description": "Statement of Questions Presented",
        "authority": "MCR 7.212(D)(1)",
        "required_for": ["appellate_brief"],
        "check": lambda text: bool(
            re.search(r"(?:STATEMENT\s+OF\s+QUESTIONS?\s+PRESENTED|ISSUES?\s+PRESENTED)", text, re.I)
        ),
    },
    "jurisdictional_statement": {
        "description": "Statement of Jurisdiction",
        "authority": "MCR 7.212(D)(2)",
        "required_for": ["appellate_brief", "msc_application"],
        "check": lambda text: bool(
            re.search(r"(?:JURISDICTION|STATEMENT\s+OF\s+JURISDICTION)", text, re.I)
        ),
    },
}


# ── Database helper ─────────────────────────────────────────────────────────

def _get_db() -> Optional[sqlite3.Connection]:
    """Connect to litigation_context.db."""
    if not os.path.exists(DB_PATH):
        return None
    conn = sqlite3.connect(DB_PATH, timeout=30)
    conn.row_factory = sqlite3.Row
    return conn


# ── Core functions ──────────────────────────────────────────────────────────

def check_local_compliance(
    filing_type: str,
    filing_content: str,
    court: str = "14th_circuit",
) -> Dict:
    """Check a filing for compliance with local court rules.

    Args:
        filing_type: Type of filing (motion, brief, complaint, etc.).
        filing_content: The text content of the filing.
        court: Court key (14th_circuit, coa, msc, usdc_wdmi).

    Returns:
        dict with passed/failed checks, overall compliance, and recommendations.
    """
    court_key = _resolve_court(court)
    if court_key not in LOCAL_RULES:
        return {
            "error": f"Unknown court: {court}",
            "valid_courts": list(LOCAL_RULES.keys()),
        }

    rules = LOCAL_RULES[court_key]
    filing_key = filing_type.lower().replace(" ", "_").replace("-", "_")
    results: List[Dict] = []
    passed = 0
    failed = 0
    warnings_list: List[str] = []

    # Run each applicable compliance check
    for check_id, check_info in COMPLIANCE_CHECKS.items():
        applicable = filing_key in check_info["required_for"]
        if not applicable:
            # Check partial matches
            for req in check_info["required_for"]:
                if req in filing_key or filing_key in req:
                    applicable = True
                    break

        if not applicable:
            continue

        check_passed = check_info["check"](filing_content)
        status = "PASS" if check_passed else "FAIL"

        if check_passed:
            passed += 1
        else:
            failed += 1

        results.append({
            "check": check_id,
            "description": check_info["description"],
            "authority": check_info["authority"],
            "status": status,
        })

    # Check format rules
    format_rules = rules.get("format", {})
    format_checks = _check_format_indicators(filing_content, format_rules)
    results.extend(format_checks["checks"])
    passed += format_checks["passed"]
    failed += format_checks["failed"]
    warnings_list.extend(format_checks.get("warnings", []))

    # Pro se specific warnings
    pro_se = rules.get("pro_se_requirements", {})
    for w in pro_se.get("warnings", []):
        warnings_list.append(f"PRO SE: {w}")

    total = passed + failed
    compliance_pct = (passed / total * 100) if total > 0 else 0
    overall = "COMPLIANT" if failed == 0 else ("NEEDS ATTENTION" if compliance_pct >= 70 else "NON-COMPLIANT")

    recommendations: List[str] = []
    for r in results:
        if r["status"] == "FAIL":
            recommendations.append(
                f"FIX: {r['description']} — {r['authority']}"
            )

    return {
        "court": court_key,
        "court_name": rules["court_name"],
        "filing_type": filing_key,
        "overall_status": overall,
        "compliance_percentage": round(compliance_pct, 1),
        "passed": passed,
        "failed": failed,
        "total_checks": total,
        "checks": results,
        "recommendations": recommendations,
        "warnings": warnings_list,
        "efiling_system": rules.get("efiling_system", "Unknown"),
        "efiling_required": rules.get("efiling_required", False),
    }


def _check_format_indicators(text: str, format_rules: Dict) -> Dict:
    """Check text for format indicators (font mention, spacing, etc.)."""
    checks = []
    passed = 0
    failed = 0
    warnings = []

    # Check for double spacing (heuristic: look for blank lines between paragraphs)
    has_spacing = bool(re.search(r"\n\s*\n", text))
    if has_spacing:
        passed += 1
        checks.append({
            "check": "paragraph_spacing",
            "description": "Paragraph spacing detected",
            "authority": format_rules.get("authority", "MCR 2.113"),
            "status": "PASS",
        })
    else:
        warnings.append("Could not verify double-spacing — check final document format")

    # Check for page numbers (heuristic)
    has_page_nums = bool(re.search(r"(?:Page\s+\d+|\- \d+ \-|^\s*\d+\s*$)", text, re.M))
    if has_page_nums:
        passed += 1
    checks.append({
        "check": "page_numbers",
        "description": "Page numbers present",
        "authority": format_rules.get("authority", "MCR 2.113"),
        "status": "PASS" if has_page_nums else "WARN",
    })

    return {"checks": checks, "passed": passed, "failed": failed, "warnings": warnings}


def _resolve_court(court: str) -> str:
    """Resolve court aliases to canonical key."""
    key = court.lower().replace(" ", "_").replace("-", "_")
    aliases = {
        "circuit": "14th_circuit", "14th": "14th_circuit",
        "muskegon": "14th_circuit", "trial": "14th_circuit",
        "appeals": "coa", "court_of_appeals": "coa",
        "supreme": "msc", "supreme_court": "msc",
        "federal": "usdc_wdmi", "usdc": "usdc_wdmi",
        "district": "usdc_wdmi", "western_district": "usdc_wdmi",
    }
    return aliases.get(key, key)


def get_local_rules(category: str, court: str = "14th_circuit") -> Dict:
    """Retrieve local rules for a specific category and court.

    Args:
        category: Rule category (format, motion_practice, pro_se_requirements,
                  hearing_procedures, efiling_rules, original_action_requirements).
        court: Court key.

    Returns:
        dict with the rules for that category, or all rules if category='all'.
    """
    court_key = _resolve_court(court)
    if court_key not in LOCAL_RULES:
        return {
            "error": f"Unknown court: {court}",
            "valid_courts": list(LOCAL_RULES.keys()),
        }

    rules = LOCAL_RULES[court_key]

    if category == "all":
        return {
            "court": court_key,
            "court_name": rules["court_name"],
            "authority": rules["authority"],
            "rules": {k: v for k, v in rules.items()
                      if k not in ("court_name", "authority")},
        }

    cat_key = category.lower().replace(" ", "_").replace("-", "_")
    if cat_key in rules:
        return {
            "court": court_key,
            "category": cat_key,
            "rules": rules[cat_key],
        }

    return {
        "error": f"Unknown category '{category}' for {court_key}",
        "available_categories": [k for k in rules.keys()
                                 if k not in ("court_name", "authority")],
    }


def generate_compliance_checklist(court: str = "14th_circuit") -> Dict:
    """Generate a pre-filing compliance checklist for a given court.

    Args:
        court: Court key.

    Returns:
        dict with checklist items organized by category.
    """
    court_key = _resolve_court(court)
    if court_key not in LOCAL_RULES:
        return {"error": f"Unknown court: {court}"}

    rules = LOCAL_RULES[court_key]
    checklist: List[Dict] = []

    # Format requirements
    fmt = rules.get("format", {})
    checklist.append({
        "category": "Format",
        "items": [
            {"item": f"Paper: {fmt.get('paper_size', '8.5 x 11')}", "required": True},
            {"item": f"Font: {fmt.get('font', '12pt Times New Roman')}", "required": True},
            {"item": f"Margins: {fmt.get('margins', '1 inch all sides')}", "required": True},
            {"item": f"Spacing: {fmt.get('spacing', 'Double-spaced')}", "required": True},
            {"item": "Caption with correct case number", "required": True},
            {"item": "Numbered paragraphs", "required": fmt.get("numbered_paragraphs", False)},
            {"item": "Signature block", "required": True},
            {"item": "Certificate of Service", "required": True},
        ],
        "authority": fmt.get("authority", "MCR 2.113"),
    })

    # E-filing requirements
    efiling = rules.get("efiling_rules", {})
    ef_items = [
        {"item": f"E-file via {efiling.get('system', 'Unknown')}", "required": True},
        {"item": f"Format: {efiling.get('file_format', 'PDF')}", "required": True},
        {"item": f"Max size: {efiling.get('max_file_size_mb', 50)}MB per document", "required": True},
    ]
    if efiling.get("bookmarks_required"):
        ef_items.append({"item": "PDF bookmarks for sections", "required": True})
    if efiling.get("paper_copies_also_required"):
        count = efiling.get("paper_copy_count", 1)
        ef_items.append({"item": f"Mail {count} paper copies", "required": True})
    checklist.append({
        "category": "E-Filing",
        "items": ef_items,
        "authority": efiling.get("authority", ""),
    })

    # Motion practice
    motion = rules.get("motion_practice", {})
    if motion:
        m_items = [
            {"item": f"Notice: {motion.get('notice_period_days', 9)} days "
                     f"(+{motion.get('mail_add_days', 3)} if mailed)", "required": True},
            {"item": "Supporting brief", "required": motion.get("brief_required", False)},
            {"item": "Proposed order", "required": motion.get("proposed_order_required", False)},
        ]
        checklist.append({
            "category": "Motion Practice",
            "items": m_items,
            "authority": motion.get("authority", ""),
        })

    # Appellate specifics
    if court_key in ("coa", "msc"):
        app_items = [
            {"item": "Table of Contents", "required": True},
            {"item": "Table of Authorities", "required": True},
            {"item": "Statement of Jurisdiction", "required": True},
        ]
        if court_key == "coa":
            app_items.append({"item": "Statement of Questions Presented", "required": True})
            page_limit = fmt.get("page_limit_brief", 50)
            app_items.append({"item": f"Page limit: {page_limit} pages", "required": True})
        if court_key == "msc":
            orig = rules.get("original_action_requirements", {})
            if orig:
                app_items.append({"item": "Verified complaint", "required": True})
                app_items.append({"item": f"{orig.get('copies', 13)} paper copies", "required": True})
                app_items.append({"item": "Appendix with lower court orders", "required": True})
        checklist.append({
            "category": "Appellate Requirements",
            "items": app_items,
            "authority": fmt.get("authority", "MCR 7.212"),
        })

    # Pro se items
    pro_se = rules.get("pro_se_requirements", {})
    if pro_se:
        ps_items = [
            {"item": "Address on all filings", "required": True},
            {"item": "Phone number on all filings", "required": pro_se.get("phone_required", True)},
            {"item": "Sign all filings personally", "required": True},
        ]
        checklist.append({
            "category": "Pro Se Requirements",
            "items": ps_items,
            "authority": pro_se.get("authority", "MCR 2.114"),
        })

    total_items = sum(len(c["items"]) for c in checklist)

    return {
        "court": court_key,
        "court_name": rules["court_name"],
        "checklist": checklist,
        "total_items": total_items,
        "efiling_system": rules.get("efiling_system"),
        "generated_at": datetime.now().isoformat(),
    }


# ── CLI ─────────────────────────────────────────────────────────────────────

def main() -> int:
    """CLI entry point for testing."""
    print("=" * 60)
    print("ENGINE 14: LOCAL RULE CHECKER")
    print("14th Circuit / COA / MSC / USDC-WD MI Compliance")
    print("=" * 60)

    # Test compliance check with a sample motion
    sample_motion = """
STATE OF MICHIGAN
IN THE 14TH JUDICIAL CIRCUIT COURT
COUNTY OF MUSKEGON

ANDREW PIGORS,
    Plaintiff,                       Case No. 2024-001507-DC
v.                                   Hon. Jenny L. McNeill
TIFFANY WATSON,
    Defendant.
__________________________________/

MOTION FOR RECONSIDERATION

    1. Plaintiff Andrew Pigors, proceeding pro se, respectfully moves
this Honorable Court for reconsideration of its Order dated August 8, 2025.

    2. This motion is supported by the accompanying Brief in Support.

    3. A proposed order is attached hereto.

CERTIFICATE OF SERVICE

    I hereby certify that on this date I served a copy of this document
via MiFile e-service upon all parties of record.

                                    Respectfully submitted,

                                    /s/ Andrew Pigors
                                    Andrew Pigors, Pro Se
                                    123 Main St.
                                    Muskegon, MI 49441
                                    (231) 555-0100
"""

    print("\n--- Compliance Check: Motion (14th Circuit) ---")
    result = check_local_compliance("motion", sample_motion, "14th_circuit")
    print(f"  Court: {result['court_name']}")
    print(f"  Status: {result['overall_status']}")
    print(f"  Score: {result['compliance_percentage']}% ({result['passed']}/{result['total_checks']})")
    for c in result["checks"]:
        icon = "✓" if c["status"] == "PASS" else ("⚠" if c["status"] == "WARN" else "✗")
        print(f"    {icon} {c['check']}: {c['status']} — {c['authority']}")
    if result["recommendations"]:
        print("  Recommendations:")
        for rec in result["recommendations"]:
            print(f"    → {rec}")

    # Test appellate brief compliance
    sample_brief = """
STATE OF MICHIGAN
IN THE COURT OF APPEALS

ANDREW PIGORS,
    Plaintiff-Appellant,            No. 366810
v.
TIFFANY WATSON,
    Defendant-Appellee.
__________________________________/

TABLE OF CONTENTS
TABLE OF AUTHORITIES
STATEMENT OF JURISDICTION
STATEMENT OF QUESTIONS PRESENTED

    I. Whether the trial court violated Plaintiff-Appellant's right to
due process by entering 24 ex parte orders without notice or hearing.

CERTIFICATE OF SERVICE

                                    Respectfully submitted,
                                    /s/ Andrew Pigors
"""

    print("\n--- Compliance Check: Appellate Brief (COA) ---")
    result2 = check_local_compliance("appellate_brief", sample_brief, "coa")
    print(f"  Status: {result2['overall_status']}")
    print(f"  Score: {result2['compliance_percentage']}%")
    for c in result2["checks"]:
        icon = "✓" if c["status"] == "PASS" else ("⚠" if c["status"] == "WARN" else "✗")
        print(f"    {icon} {c['check']}: {c['status']}")

    # Test get_local_rules
    print("\n--- Local Rules: 14th Circuit E-Filing ---")
    efiling = get_local_rules("efiling_rules", "14th_circuit")
    rules_data = efiling.get("rules", {})
    print(f"  System: {rules_data.get('system', 'N/A')}")
    print(f"  Mandatory: {rules_data.get('mandatory', 'N/A')}")
    print(f"  Max file size: {rules_data.get('max_file_size_mb', 'N/A')}MB")
    print(f"  Authority: {rules_data.get('authority', 'N/A')}")

    print("\n--- Local Rules: MSC Original Action ---")
    msc_orig = get_local_rules("original_action_requirements", "msc")
    orig_rules = msc_orig.get("rules", {})
    print(f"  Copies required: {orig_rules.get('copies', 'N/A')}")
    print(f"  Verification: {orig_rules.get('verification_required', 'N/A')}")

    # Test compliance checklist generation
    print("\n--- Compliance Checklist: 14th Circuit ---")
    checklist = generate_compliance_checklist("14th_circuit")
    print(f"  Court: {checklist['court_name']}")
    print(f"  Total items: {checklist['total_items']}")
    for cat in checklist["checklist"]:
        print(f"  [{cat['category']}]")
        for item in cat["items"][:3]:
            req = "REQ" if item["required"] else "OPT"
            print(f"    [{req}] {item['item']}")
        if len(cat["items"]) > 3:
            print(f"    ... +{len(cat['items']) - 3} more")

    print("\n--- Compliance Checklist: MSC ---")
    msc_cl = generate_compliance_checklist("msc")
    print(f"  Total items: {msc_cl['total_items']}")
    for cat in msc_cl["checklist"]:
        print(f"  [{cat['category']}] — {len(cat['items'])} items")

    # Test court alias resolution
    print("\n--- Court Alias Resolution ---")
    for alias in ["circuit", "14th", "appeals", "supreme", "federal", "usdc"]:
        resolved = _resolve_court(alias)
        print(f"  '{alias}' → '{resolved}'")

    # Verify all courts loadable
    print("\n--- All Courts ---")
    for court_key, rules_data in LOCAL_RULES.items():
        print(f"  {court_key}: {rules_data['court_name']} ({rules_data['efiling_system']})")

    print("\n[local_rule_checker] All tests passed. ✓")
    return 0


if __name__ == "__main__":
    sys.exit(main())
