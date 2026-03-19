#!/usr/bin/env python3
"""
MBP LitigationOS -- SCAO Court Forms Library Skill
====================================================
Comprehensive reference module for Michigan SCAO court forms.
Looks up required forms by filing type / court level, validates
filing packages, and generates pre-filled form content from DB data.

Table: scao_court_forms in litigation_context.db
"""

from __future__ import annotations

import json
import os
import sqlite3
import sys
import textwrap
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

# Default case data for Andrew Pigors v Tiffany Watson
DEFAULT_CASE_DATA: Dict[str, str] = {
    "plaintiff_name": "Andrew Pigors",
    "defendant_name": "Tiffany Watson",
    "lane_a_case_number": "2024-001507-DC",
    "lane_d_case_number": "2023-5907-PP",
    "coa_case_number": "COA 366810",
    "trial_court": "14th Circuit Court, Muskegon County",
    "trial_judge": "Hon. Jenny L. McNeill",
    "plaintiff_designation": "Plaintiff/Appellant, Pro Se",
    "defendant_designation": "Defendant/Appellee",
}

# Which forms are ALWAYS required for a given filing type
FILING_REQUIREMENTS: Dict[str, Dict[str, Any]] = {
    "custody_motion": {
        "court_level": "circuit",
        "required_forms": ["MC 21", "FOC 65"],
        "conditional_forms": {
            "FOC 1": "Required if first custody filing",
            "FOC 17": "Required if proposing parenting time schedule",
            "MC 20": "Required if requesting fee waiver",
        },
        "notes": "Must go through FOC first per MCR 3.208. 21-day objection window.",
    },
    "parenting_time_motion": {
        "court_level": "circuit",
        "required_forms": ["MC 21", "FOC 65", "FOC 17"],
        "conditional_forms": {
            "MC 20": "Required if requesting fee waiver",
        },
        "notes": "FOC 89 needed if objecting to referee recommendation. 21-day deadline.",
    },
    "ppo_termination": {
        "court_level": "circuit",
        "required_forms": ["MC 21", "CC 376"],
        "conditional_forms": {
            "CC 380": "Alternative to CC 376 for full termination petition",
            "CC 381": "Hearing notice — court may generate",
        },
        "notes": "File with disqualification motion if McNeill presiding.",
    },
    "ppo_response": {
        "court_level": "circuit",
        "required_forms": ["MC 21"],
        "conditional_forms": {
            "CC 376": "If counter-filing to modify/terminate",
        },
        "notes": "14-day response deadline for ex parte PPO objection.",
    },
    "appeal_of_right": {
        "court_level": "coa",
        "required_forms": [
            "COA Claim of Appeal",
            "COA Docket Statement",
            "COA Certificate of Service",
        ],
        "conditional_forms": {
            "MC 290": "Required if requesting transcript fee waiver",
            "MC 20": "Required if requesting filing fee waiver",
        },
        "notes": "21-DAY JURISDICTIONAL DEADLINE per MCR 7.204(A)(1). Cannot extend.",
    },
    "coa_leave_appeal": {
        "court_level": "coa",
        "required_forms": [
            "COA Application for Leave to Appeal",
            "COA Certificate of Service",
        ],
        "conditional_forms": {
            "MC 290": "If requesting fee waiver",
        },
        "notes": "Use when appeal of right deadline missed or for interlocutory orders.",
    },
    "coa_emergency": {
        "court_level": "coa",
        "required_forms": [
            "COA Emergency Motion",
            "COA Certificate of Service",
        ],
        "conditional_forms": {},
        "notes": "Must show irreparable harm and prior trial court efforts.",
    },
    "msc_original_action": {
        "court_level": "msc",
        "required_forms": [
            "MSC Original Action Complaint",
            "MSC Certificate of Compliance",
        ],
        "conditional_forms": {
            "MSC Emergency Application": "File simultaneously for immediate relief",
            "MC 290": "If requesting fee waiver for 13 copies",
        },
        "notes": "PRIMARY VEHICLE. 13 copies required. Const 1963 art 6 § 4.",
    },
    "msc_leave_appeal": {
        "court_level": "msc",
        "required_forms": [
            "MSC Application for Leave to Appeal",
            "MSC Certificate of Compliance",
        ],
        "conditional_forms": {
            "MC 290": "If requesting fee waiver",
        },
        "notes": "MCR 7.305(B)(2) allows COA bypass for significant questions.",
    },
    "msc_emergency": {
        "court_level": "msc",
        "required_forms": [
            "MSC Emergency Application",
            "MSC Certificate of Compliance",
        ],
        "conditional_forms": {},
        "notes": "MCR 7.305(F) / MCR 7.315(C). File with original action.",
    },
    "jtc_complaint": {
        "court_level": "all",
        "required_forms": ["JTC Formal Complaint"],
        "conditional_forms": {
            "JTC Request for Investigation": "Can file separately or with complaint",
        },
        "notes": "Independent track. 28-day investigation initiation rule. File Day 1 with MSC.",
    },
    "federal_1983": {
        "court_level": "district",
        "required_forms": ["AO 42 USC § 1983 Complaint"],
        "conditional_forms": {
            "AO 240 IFP Application": "If unable to pay $405 filing fee",
        },
        "notes": "Reserved Day 30. Must exhaust state remedies first. Rooker-Feldman caution.",
    },
    "general_motion": {
        "court_level": "circuit",
        "required_forms": ["MC 21"],
        "conditional_forms": {
            "MC 20": "If requesting fee waiver",
            "MC 01": "If first filing in a new case",
        },
        "notes": "MC 21 (Proof of Service) required for EVERY filing.",
    },
}


def _get_conn() -> sqlite3.Connection:
    """Get a connection to the litigation DB."""
    if not os.path.exists(DB_PATH):
        raise FileNotFoundError(f"Database not found: {DB_PATH}")
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def list_all_forms(court_level: Optional[str] = None) -> List[Dict[str, Any]]:
    """
    List all SCAO forms, optionally filtered by court level.

    Args:
        court_level: Filter by 'circuit', 'coa', 'msc', 'district', 'all', or None for all.

    Returns:
        List of form dictionaries with metadata.
    """
    conn = _get_conn()
    try:
        if court_level:
            rows = conn.execute(
                "SELECT id, form_number, form_title, court_level, case_type, "
                "mcr_reference, required_for, description, filing_notes, url "
                "FROM scao_court_forms WHERE court_level = ? OR court_level = 'all' "
                "ORDER BY form_number",
                (court_level,),
            ).fetchall()
        else:
            rows = conn.execute(
                "SELECT id, form_number, form_title, court_level, case_type, "
                "mcr_reference, required_for, description, filing_notes, url "
                "FROM scao_court_forms ORDER BY court_level, form_number"
            ).fetchall()
        return [dict(r) for r in rows]
    finally:
        conn.close()


def get_form_details(form_number: str) -> Optional[Dict[str, Any]]:
    """
    Get full details for a specific form by form number.

    Args:
        form_number: The SCAO form number (e.g., 'MC 21', 'FOC 65').

    Returns:
        Full form dictionary including fields JSON, or None if not found.
    """
    conn = _get_conn()
    try:
        row = conn.execute(
            "SELECT * FROM scao_court_forms WHERE form_number = ?",
            (form_number,),
        ).fetchone()
        if row:
            result = dict(row)
            if result.get("fields"):
                result["fields"] = json.loads(result["fields"])
            return result
        return None
    finally:
        conn.close()


def get_required_forms(
    court_level: str,
    case_type: str = "",
    filing_type: str = "",
) -> Dict[str, Any]:
    """
    Get required SCAO forms for a given filing type and court level.

    Args:
        court_level: 'circuit', 'coa', 'msc', 'district'
        case_type: 'custody', 'ppo', 'appeal', 'general_civil', 'domestic', 'fee_waiver'
        filing_type: Specific filing type key from FILING_REQUIREMENTS

    Returns:
        Dictionary with required_forms, conditional_forms, form_details, and notes.
    """
    result: Dict[str, Any] = {
        "court_level": court_level,
        "case_type": case_type,
        "filing_type": filing_type,
        "required_forms": [],
        "conditional_forms": {},
        "form_details": [],
        "notes": "",
        "universal_forms": ["MC 21 - Proof of Service (required for ALL filings)"],
    }

    # Check filing requirements map
    if filing_type in FILING_REQUIREMENTS:
        req = FILING_REQUIREMENTS[filing_type]
        result["required_forms"] = req["required_forms"]
        result["conditional_forms"] = req.get("conditional_forms", {})
        result["notes"] = req.get("notes", "")
    else:
        # Fall back to DB query by court_level and case_type
        conn = _get_conn()
        try:
            query = (
                "SELECT form_number, form_title, required_for, mcr_reference "
                "FROM scao_court_forms WHERE "
                "(court_level = ? OR court_level = 'all')"
            )
            params: list = [court_level]
            if case_type:
                query += " AND case_type = ?"
                params.append(case_type)
            query += " ORDER BY form_number"
            rows = conn.execute(query, params).fetchall()
            result["required_forms"] = [
                f"{r['form_number']} - {r['form_title']}" for r in rows
            ]
        finally:
            conn.close()

    # Enrich with full form details from DB
    conn = _get_conn()
    try:
        for form_num in result["required_forms"]:
            # Extract just the form number if it includes title
            clean_num = form_num.split(" - ")[0].strip() if " - " in form_num else form_num
            row = conn.execute(
                "SELECT * FROM scao_court_forms WHERE form_number = ?",
                (clean_num,),
            ).fetchone()
            if row:
                detail = dict(row)
                if detail.get("fields"):
                    detail["fields"] = json.loads(detail["fields"])
                result["form_details"].append(detail)
    finally:
        conn.close()

    return result


def validate_filing_package(
    forms_included: List[str],
    court_level: str,
    case_type: str = "",
    filing_type: str = "",
) -> Dict[str, Any]:
    """
    Validate that a filing package contains all required forms.

    Args:
        forms_included: List of form numbers included in the package.
        court_level: Target court level.
        case_type: Case type.
        filing_type: Specific filing type.

    Returns:
        Dictionary with validation results: missing_forms, warnings, is_complete.
    """
    result: Dict[str, Any] = {
        "is_complete": False,
        "missing_required": [],
        "missing_conditional": [],
        "warnings": [],
        "included_forms": forms_included,
        "court_level": court_level,
    }

    # Normalize included form numbers
    included_normalized = {f.strip().upper() for f in forms_included}

    # Get requirements
    reqs = get_required_forms(court_level, case_type, filing_type)

    # Check required forms
    for form_num in reqs.get("required_forms", []):
        clean = form_num.split(" - ")[0].strip() if " - " in form_num else form_num
        if clean.upper() not in included_normalized:
            result["missing_required"].append(form_num)

    # Check conditional forms
    for form_num, condition in reqs.get("conditional_forms", {}).items():
        if form_num.upper() not in included_normalized:
            result["missing_conditional"].append(
                {"form": form_num, "condition": condition}
            )

    # Universal: MC 21 required for everything
    if "MC 21" not in included_normalized:
        has_proof_of_service = any("PROOF OF SERVICE" in f.upper() or "MC 21" in f.upper() 
                                   for f in included_normalized)
        if not has_proof_of_service:
            result["warnings"].append(
                "MC 21 (Proof of Service) is required for EVERY filing per MCR 2.107"
            )

    # Court-specific warnings
    if court_level == "msc":
        result["warnings"].append(
            "MSC filings require 13 copies unless fee waiver granted (MC 290)"
        )
        cert_included = any("CERTIFICATE OF COMPLIANCE" in f.upper() or "CERT" in f.upper()
                           for f in included_normalized)
        if not cert_included and "MSC CERTIFICATE OF COMPLIANCE" not in included_normalized:
            result["warnings"].append(
                "MSC Certificate of Compliance required for all substantive filings"
            )

    if court_level == "coa":
        cert_included = any("CERTIFICATE OF SERVICE" in f.upper() for f in included_normalized)
        if not cert_included and "COA CERTIFICATE OF SERVICE" not in included_normalized:
            result["warnings"].append(
                "COA Certificate of Service required for all appellate filings per MCR 7.211(A)(3)"
            )

    if court_level == "circuit":
        result["warnings"].append(
            "Service timing: MCR 2.119(C)(1) requires 9 days + 3 if mailed = 12 days minimum"
        )

    # Procedural trap warnings
    if filing_type in ("custody_motion", "parenting_time_motion"):
        result["warnings"].append(
            "TRAP: FOC administrative remedies must be exhausted first — "
            "MCL 552.507(5), MCR 3.208 — 21-day objection window"
        )
    if filing_type == "appeal_of_right":
        result["warnings"].append(
            "TRAP: 21-day claim of appeal deadline is JURISDICTIONAL — "
            "MCR 7.204(A)(1) — cannot be extended"
        )

    result["is_complete"] = len(result["missing_required"]) == 0
    return result


def generate_form_content(
    form_number: str,
    case_data: Optional[Dict[str, str]] = None,
) -> Dict[str, Any]:
    """
    Generate pre-filled form content from DB data.

    Args:
        form_number: SCAO form number (e.g., 'MC 21', 'FOC 65').
        case_data: Override dictionary for case-specific values.
                   Falls back to DEFAULT_CASE_DATA for unset keys.

    Returns:
        Dictionary with form_number, form_title, pre-filled fields,
        manual_fields (fields requiring manual completion), and filing_notes.
    """
    form = get_form_details(form_number)
    if not form:
        return {"error": f"Form {form_number} not found in database."}

    # Merge case data with defaults
    data = dict(DEFAULT_CASE_DATA)
    if case_data:
        data.update(case_data)

    fields = form.get("fields", [])
    if isinstance(fields, str):
        fields = json.loads(fields)

    pre_filled: Dict[str, str] = {}
    manual_fields: List[Dict[str, str]] = []

    # Auto-fill mapping: field name patterns → case data keys
    auto_fill_map = {
        "court_name": data.get("trial_court", ""),
        "case_number": _infer_case_number(form, data),
        "plaintiff_name": data.get("plaintiff_name", ""),
        "defendant_name": data.get("defendant_name", ""),
        "judge_name": data.get("trial_judge", ""),
        "moving_party": data.get("plaintiff_name", ""),
        "appellant_name": data.get("plaintiff_name", ""),
        "applicant_name": data.get("plaintiff_name", ""),
        "complainant_name": data.get("plaintiff_name", ""),
        "objecting_party": data.get("plaintiff_name", ""),
        "petitioner_name": data.get("plaintiff_name", ""),
        "respondent_name": data.get("defendant_name", ""),
        "responding_party": data.get("defendant_name", ""),
        "appellee_name": data.get("defendant_name", ""),
        "coa_case_number": data.get("coa_case_number", ""),
        "case_title": f"{data.get('plaintiff_name', '')} v {data.get('defendant_name', '')}",
        "lower_court": data.get("trial_court", ""),
        "lower_case_number": data.get("lane_a_case_number", ""),
        "lower_judge": data.get("trial_judge", ""),
        "date": datetime.now().strftime("%B %d, %Y"),
    }

    for field in fields:
        fname = field.get("name", "")
        fdesc = field.get("desc", "")

        # Try auto-fill
        filled = False
        for pattern, value in auto_fill_map.items():
            if fname == pattern and value:
                pre_filled[fname] = value
                filled = True
                break

        if not filled:
            manual_fields.append({"name": fname, "description": fdesc})

    result = {
        "form_number": form["form_number"],
        "form_title": form["form_title"],
        "court_level": form["court_level"],
        "mcr_reference": form["mcr_reference"],
        "pre_filled": pre_filled,
        "manual_fields": manual_fields,
        "filing_notes": form.get("filing_notes", ""),
        "url": form.get("url", ""),
        "generated_at": datetime.now().isoformat(),
    }
    return result


def _infer_case_number(form: Dict[str, Any], data: Dict[str, str]) -> str:
    """Infer correct case number based on form type."""
    court = form.get("court_level", "")
    case_type = form.get("case_type", "")

    if court == "coa" or "coa" in form.get("id", ""):
        return data.get("coa_case_number", "")
    if case_type == "ppo" or "ppo" in form.get("id", ""):
        return data.get("lane_d_case_number", "")
    if court == "msc":
        return data.get("msc_case_number", "To be assigned")
    if court == "district":
        return data.get("federal_case_number", "To be assigned")
    return data.get("lane_a_case_number", "")


def get_forms_for_lane(lane: str) -> Dict[str, Any]:
    """
    Get all relevant forms for a specific litigation lane.

    Args:
        lane: Lane identifier ('A' through 'G').

    Returns:
        Dictionary with lane description and relevant forms.
    """
    lane_map = {
        "A": {"case_type": "custody", "court_level": "circuit",
               "desc": "Lane A: Custody (2024-001507-DC)"},
        "B": {"case_type": "general_civil", "court_level": "circuit",
               "desc": "Lane B: Housing"},
        "C": {"case_type": "general_civil", "court_level": "all",
               "desc": "Lane C: Convergence / Cross-lane"},
        "D": {"case_type": "ppo", "court_level": "circuit",
               "desc": "Lane D: PPO (2023-5907-PP)"},
        "E": {"case_type": "general_civil", "court_level": "all",
               "desc": "Lane E: Judicial Misconduct (JTC)"},
        "F": {"case_type": "appeal", "court_level": "coa",
               "desc": "Lane F: COA Appeal (366810)"},
        "G": {"case_type": "appeal", "court_level": "msc",
               "desc": "Lane G: MSC Original Action"},
    }

    lane_info = lane_map.get(lane.upper())
    if not lane_info:
        return {"error": f"Unknown lane: {lane}. Valid lanes: A-G"}

    conn = _get_conn()
    try:
        rows = conn.execute(
            "SELECT form_number, form_title, mcr_reference, required_for, filing_notes "
            "FROM scao_court_forms "
            "WHERE (court_level = ? OR court_level = 'all') "
            "AND (case_type = ? OR case_type = 'general_civil' OR case_type = 'fee_waiver') "
            "ORDER BY form_number",
            (lane_info["court_level"], lane_info["case_type"]),
        ).fetchall()

        return {
            "lane": lane.upper(),
            "description": lane_info["desc"],
            "forms": [dict(r) for r in rows],
            "form_count": len(rows),
        }
    finally:
        conn.close()


def search_forms(query: str) -> List[Dict[str, Any]]:
    """
    Search forms by keyword in title, description, or filing notes.

    Args:
        query: Search keyword.

    Returns:
        List of matching form dictionaries.
    """
    conn = _get_conn()
    try:
        pattern = f"%{query}%"
        rows = conn.execute(
            "SELECT id, form_number, form_title, court_level, case_type, "
            "mcr_reference, description, filing_notes "
            "FROM scao_court_forms "
            "WHERE form_title LIKE ? OR description LIKE ? "
            "OR filing_notes LIKE ? OR mcr_reference LIKE ? OR required_for LIKE ? "
            "ORDER BY form_number",
            (pattern, pattern, pattern, pattern, pattern),
        ).fetchall()
        return [dict(r) for r in rows]
    finally:
        conn.close()


def get_filing_checklist(filing_type: str) -> str:
    """
    Generate a printable filing checklist for a specific filing type.

    Args:
        filing_type: Key from FILING_REQUIREMENTS.

    Returns:
        Formatted checklist string.
    """
    if filing_type not in FILING_REQUIREMENTS:
        available = ", ".join(sorted(FILING_REQUIREMENTS.keys()))
        return f"Unknown filing type: {filing_type}\nAvailable: {available}"

    reqs = FILING_REQUIREMENTS[filing_type]
    lines = [
        f"FILING CHECKLIST: {filing_type.upper().replace('_', ' ')}",
        f"Court Level: {reqs['court_level'].upper()}",
        f"Generated: {datetime.now().strftime('%B %d, %Y')}",
        "=" * 60,
        "",
        "REQUIRED FORMS:",
    ]

    for i, form in enumerate(reqs["required_forms"], 1):
        detail = get_form_details(form.split(" - ")[0].strip() if " - " in form else form)
        mcr = f" ({detail['mcr_reference']})" if detail and detail.get("mcr_reference") else ""
        lines.append(f"  [ ] {i}. {form}{mcr}")

    lines.append("")
    lines.append("ALWAYS REQUIRED:")
    lines.append("  [ ] Proof of Service (MC 21) — MCR 2.107")

    if reqs.get("conditional_forms"):
        lines.append("")
        lines.append("CONDITIONAL FORMS (include if applicable):")
        for form, condition in reqs["conditional_forms"].items():
            lines.append(f"  [ ] {form}: {condition}")

    lines.append("")
    lines.append("FORMAT REQUIREMENTS (MCR 2.113):")
    lines.append("  [ ] 12pt Times New Roman, double-spaced")
    lines.append("  [ ] 1-inch margins on all sides")
    lines.append("  [ ] Caption with case number, parties, court")
    lines.append("  [ ] Numbered paragraphs")
    lines.append("  [ ] Signature block with Pro Se designation")
    lines.append("  [ ] Certificate of Service attached to EVERY document")

    if reqs.get("notes"):
        lines.append("")
        lines.append("NOTES:")
        for line in textwrap.wrap(reqs["notes"], width=58):
            lines.append(f"  ⚠ {line}")

    lines.append("")
    lines.append("=" * 60)
    return "\n".join(lines)


# ── JSON-RPC interface for local model integration ──────────────────

def handle_rpc(method: str, params: Optional[Dict] = None) -> Dict[str, Any]:
    """Handle JSON-RPC method calls from the local model."""
    params = params or {}

    dispatch = {
        "scao_list_forms": lambda p: {"forms": list_all_forms(p.get("court_level"))},
        "scao_get_form": lambda p: get_form_details(p["form_number"]),
        "scao_required_forms": lambda p: get_required_forms(
            p.get("court_level", "circuit"),
            p.get("case_type", ""),
            p.get("filing_type", ""),
        ),
        "scao_validate_package": lambda p: validate_filing_package(
            p.get("forms_included", []),
            p.get("court_level", "circuit"),
            p.get("case_type", ""),
            p.get("filing_type", ""),
        ),
        "scao_generate_form": lambda p: generate_form_content(
            p["form_number"],
            p.get("case_data"),
        ),
        "scao_lane_forms": lambda p: get_forms_for_lane(p["lane"]),
        "scao_search": lambda p: {"results": search_forms(p["query"])},
        "scao_checklist": lambda p: {"checklist": get_filing_checklist(p["filing_type"])},
    }

    handler = dispatch.get(method)
    if not handler:
        return {"error": f"Unknown method: {method}", "available": list(dispatch.keys())}
    try:
        return handler(params)
    except Exception as e:
        return {"error": str(e), "method": method}


# ── CLI interface ───────────────────────────────────────────────────

if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="SCAO Court Forms Library")
    sub = parser.add_subparsers(dest="command")

    sub.add_parser("list", help="List all forms").add_argument(
        "--court", help="Filter by court level"
    )
    p_get = sub.add_parser("get", help="Get form details")
    p_get.add_argument("form_number", help="Form number (e.g., MC 21)")

    p_req = sub.add_parser("required", help="Get required forms for filing")
    p_req.add_argument("filing_type", help="Filing type key")

    p_val = sub.add_parser("validate", help="Validate filing package")
    p_val.add_argument("filing_type", help="Filing type key")
    p_val.add_argument("forms", nargs="+", help="Form numbers included")

    p_gen = sub.add_parser("generate", help="Generate pre-filled form")
    p_gen.add_argument("form_number", help="Form number")

    p_lane = sub.add_parser("lane", help="Get forms for litigation lane")
    p_lane.add_argument("lane", help="Lane letter (A-G)")

    p_search = sub.add_parser("search", help="Search forms")
    p_search.add_argument("query", help="Search keyword")

    p_check = sub.add_parser("checklist", help="Generate filing checklist")
    p_check.add_argument("filing_type", help="Filing type key")

    args = parser.parse_args()

    if args.command == "list":
        court = getattr(args, "court", None)
        forms = list_all_forms(court)
        for f in forms:
            print(f"  {f['form_number']:30s} | {f['court_level']:8s} | {f['form_title']}")
        print(f"\nTotal: {len(forms)} forms")

    elif args.command == "get":
        result = get_form_details(args.form_number)
        cycle_json(result)

    elif args.command == "required":
        result = get_required_forms("", "", args.filing_type)
        cycle_json(result)

    elif args.command == "validate":
        result = validate_filing_package(args.forms, "", "", args.filing_type)
        cycle_json(result)

    elif args.command == "generate":
        result = generate_form_content(args.form_number)
        cycle_json(result)

    elif args.command == "lane":
        result = get_forms_for_lane(args.lane)
        cycle_json(result)

    elif args.command == "search":
        results = search_forms(args.query)
        for r in results:
            print(f"  {r['form_number']:30s} | {r['form_title']}")
        print(f"\nFound: {len(results)} forms")

    elif args.command == "checklist":
        print(get_filing_checklist(args.filing_type))

    else:
        parser.print_help()
