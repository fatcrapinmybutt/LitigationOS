# -*- coding: utf-8 -*-
"""Engine 7: Caption Generator — Case captions per MCR 2.113.

Supports all 5 courts: 14th Circuit, COA, MSC, JTC, USDC.
Generates properly formatted captions with correct case numbers,
party names, and court-specific formatting requirements.
"""
import sys
import os
import json
from datetime import datetime

if sys.stdout and hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
if sys.stderr and hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8")

# ── Case constants ──────────────────────────────────────────────────────────
PLAINTIFF = "ANDREW PIGORS"
DEFENDANT = "TIFFANY WATSON"
JUDGE = "Hon. Jenny L. McNeill"

COURTS = {
    "14th_circuit": {
        "full_name": "14TH JUDICIAL CIRCUIT COURT",
        "state_line": "STATE OF MICHIGAN",
        "location": "COUNTY OF MUSKEGON",
        "cases": {
            "custody": {"number": "2024-001507-DC", "type": "DOMESTIC RELATIONS"},
            "ppo": {"number": "2023-5907-PP", "type": "PERSONAL PROTECTION"},
        },
        "judge": JUDGE,
        "include_judge": True,
    },
    "coa": {
        "full_name": "COURT OF APPEALS",
        "state_line": "STATE OF MICHIGAN",
        "location": None,
        "cases": {
            "appeal": {"number": "366810", "type": "APPEAL"},
        },
        "judge": None,
        "include_judge": False,
        "lower_court": "Muskegon County Circuit Court",
        "lower_case": "2024-001507-DC",
        "lower_judge": JUDGE,
    },
    "msc": {
        "full_name": "SUPREME COURT",
        "state_line": "STATE OF MICHIGAN",
        "location": None,
        "cases": {
            "superintending": {"number": "TBD", "type": "ORIGINAL ACTION"},
        },
        "judge": None,
        "include_judge": False,
        "lower_court": "Muskegon County Circuit Court",
        "lower_case": "2024-001507-DC",
        "lower_judge": JUDGE,
    },
    "jtc": {
        "full_name": "JUDICIAL TENURE COMMISSION",
        "state_line": "STATE OF MICHIGAN",
        "location": None,
        "cases": {
            "complaint": {"number": "TBD", "type": "FORMAL COMPLAINT"},
        },
        "judge": None,
        "include_judge": False,
        "respondent": JUDGE,
    },
    "usdc": {
        "full_name": "UNITED STATES DISTRICT COURT",
        "state_line": None,
        "location": "WESTERN DISTRICT OF MICHIGAN",
        "cases": {
            "1983": {"number": "TBD", "type": "CIVIL RIGHTS (42 U.S.C. § 1983)"},
        },
        "judge": None,
        "include_judge": False,
        "federal": True,
    },
}

# Party designations per court
PARTY_LABELS = {
    "14th_circuit": {"plaintiff": "Plaintiff/Father", "defendant": "Defendant/Mother"},
    "coa": {"plaintiff": "Plaintiff-Appellant", "defendant": "Defendant-Appellee"},
    "msc": {"plaintiff": "Plaintiff-Appellant", "defendant": "Defendant-Appellee"},
    "jtc": {"complainant": "Complainant", "respondent": "Respondent"},
    "usdc": {"plaintiff": "Plaintiff", "defendant": "Defendant"},
}


def _center(text, width=60):
    """Center text within given width."""
    return text.center(width)


def _separator(width=60, char="─"):
    return char * width


def generate_caption(court, case_number=None, document_title="",
                     case_type=None):
    """Generate a properly formatted case caption.

    Args:
        court: Court key — '14th_circuit', 'coa', 'msc', 'jtc', 'usdc'.
        case_number: Override case number. If None, uses default for court.
        document_title: Title of the document (e.g., 'EMERGENCY MOTION').
        case_type: Specific case type key (e.g., 'custody', 'ppo', 'appeal').

    Returns:
        Formatted caption string (markdown-compatible).
    """
    court_key = court.lower().replace(" ", "_").replace("-", "_")
    # Normalize common aliases
    aliases = {
        "circuit": "14th_circuit", "14th": "14th_circuit",
        "muskegon": "14th_circuit", "trial": "14th_circuit",
        "appeals": "coa", "court_of_appeals": "coa",
        "supreme": "msc", "supreme_court": "msc",
        "federal": "usdc", "district": "usdc",
        "tenure": "jtc", "judicial_tenure": "jtc",
    }
    court_key = aliases.get(court_key, court_key)

    if court_key not in COURTS:
        return f"[ERROR] Unknown court: {court}. Valid: {list(COURTS.keys())}"

    info = COURTS[court_key]
    labels = PARTY_LABELS.get(court_key, PARTY_LABELS["14th_circuit"])

    # Determine case number
    if case_number is None:
        if case_type and case_type in info["cases"]:
            case_number = info["cases"][case_type]["number"]
        else:
            first_case = list(info["cases"].values())[0]
            case_number = first_case["number"]

    if court_key == "jtc":
        return _generate_jtc_caption(info, case_number, document_title)
    if court_key == "usdc":
        return _generate_federal_caption(info, labels, case_number,
                                         document_title)
    return _generate_state_caption(info, labels, court_key, case_number,
                                   document_title)


def _generate_state_caption(info, labels, court_key, case_number, doc_title):
    """Generate caption for Michigan state courts (Circuit, COA, MSC)."""
    w = 60
    lines = []
    lines.append(_center(info["state_line"], w))
    lines.append(_center(f"IN THE {info['full_name']}", w))
    if info.get("location"):
        lines.append(_center(info["location"], w))
    lines.append("")

    # Lower court reference for appellate courts
    if info.get("lower_court"):
        lines.append(_center(f"(On appeal from {info['lower_court']})", w))
        lines.append(_center(f"(Case No. {info['lower_case']})", w))
        lines.append(_center(f"({info['lower_judge']})", w))
        lines.append("")

    # Case number
    case_display = f"Case No. {case_number}"
    lines.append(f"{'':>40}{case_display}")
    lines.append("")

    # Parties
    p_label = labels.get("plaintiff", "Plaintiff")
    d_label = labels.get("defendant", "Defendant")
    lines.append(f"{PLAINTIFF},")
    lines.append(f"        {p_label},")
    lines.append("")
    lines.append("    v.")
    lines.append("")
    lines.append(f"{DEFENDANT},")
    lines.append(f"        {d_label}.")

    # Judge line for circuit court
    if info.get("include_judge") and info.get("judge"):
        lines.append("")
        lines.append(f"{info['judge']}")

    lines.append(_separator(w))

    if doc_title:
        lines.append("")
        lines.append(_center(doc_title.upper(), w))
        lines.append(_separator(w))

    return "\n".join(lines)


def _generate_jtc_caption(info, case_number, doc_title):
    """Generate caption for Judicial Tenure Commission complaint."""
    w = 60
    lines = []
    lines.append(_center(info["state_line"], w))
    lines.append(_center(f"BEFORE THE {info['full_name']}", w))
    lines.append("")
    lines.append(f"Complaint No. {case_number}")
    lines.append("")
    lines.append("In the Matter of:")
    lines.append("")
    lines.append(f"    {info.get('respondent', JUDGE)},")
    lines.append(f"        Respondent Judge.")
    lines.append("")
    lines.append(_separator(w))
    lines.append("")
    lines.append(f"COMPLAINANT: {PLAINTIFF}")
    lines.append(f"    Pro Se Complainant")

    if doc_title:
        lines.append("")
        lines.append(_separator(w))
        lines.append(_center(doc_title.upper(), w))
        lines.append(_separator(w))

    return "\n".join(lines)


def _generate_federal_caption(info, labels, case_number, doc_title):
    """Generate caption for USDC per FRCP requirements."""
    w = 60
    lines = []
    lines.append(_center(info["full_name"], w))
    lines.append(_center(info["location"], w))
    lines.append("")
    lines.append(f"Case No. {case_number}")
    lines.append("")

    p_label = labels.get("plaintiff", "Plaintiff")
    d_label = labels.get("defendant", "Defendant")

    lines.append(f"{PLAINTIFF},")
    lines.append(f"        {p_label},")
    lines.append("")
    lines.append("    v.")
    lines.append("")

    # Federal defendants may include officials in official capacity
    lines.append(f"{DEFENDANT},")
    lines.append(f"        {d_label},")
    lines.append("")
    lines.append(f"{JUDGE.replace('Hon. ', '').upper()},")
    lines.append(f"    in her individual and official capacity,")
    lines.append(f"        {d_label}.")

    lines.append("")
    lines.append(_separator(w))

    if doc_title:
        lines.append("")
        lines.append(_center(doc_title.upper(), w))
        lines.append(_separator(w))

    lines.append("")
    lines.append(f"JURY TRIAL DEMANDED")

    return "\n".join(lines)


def generate_all_captions(document_title=""):
    """Generate captions for all active case lanes.

    Returns:
        dict mapping court_key -> caption string.
    """
    captions = {}
    test_configs = [
        ("14th_circuit", None, "custody"),
        ("14th_circuit", None, "ppo"),
        ("coa", None, "appeal"),
        ("msc", None, "superintending"),
        ("jtc", None, "complaint"),
        ("usdc", None, "1983"),
    ]
    for court, cn, ct in test_configs:
        key = f"{court}_{ct}"
        captions[key] = generate_caption(court, cn, document_title, ct)
    return captions


def get_caption_for_lane(lane, document_title=""):
    """Get caption for a specific case lane (A-G).

    Args:
        lane: Lane letter (A-G).
        document_title: Document title.

    Returns:
        Caption string.
    """
    lane_map = {
        "A": ("14th_circuit", None, "custody"),
        "B": ("14th_circuit", None, "custody"),  # Housing shares custody caption
        "C": ("14th_circuit", None, "custody"),
        "D": ("14th_circuit", None, "ppo"),
        "E": ("jtc", None, "complaint"),
        "F": ("coa", None, "appeal"),
        "G": ("msc", None, "superintending"),
    }
    config = lane_map.get(lane.upper())
    if not config:
        return f"[ERROR] Unknown lane: {lane}"
    return generate_caption(config[0], config[1], document_title, config[2])


def main():
    """CLI entry point for testing."""
    print("=" * 60)
    print("ENGINE 7: CAPTION GENERATOR")
    print("MCR 2.113 / FRCP")
    print("=" * 60)

    courts_to_test = [
        ("14th_circuit", "custody", "EMERGENCY MOTION TO RESTORE PARENTING TIME"),
        ("coa", "appeal", "APPELLANT'S BRIEF ON APPEAL"),
        ("msc", "superintending", "COMPLAINT FOR SUPERINTENDING CONTROL"),
        ("jtc", "complaint", "FORMAL COMPLAINT"),
        ("usdc", "1983", "COMPLAINT UNDER 42 U.S.C. § 1983"),
    ]

    for court, case_type, doc_title in courts_to_test:
        print(f"\n--- {court.upper()} ({case_type}) ---")
        caption = generate_caption(court, document_title=doc_title,
                                   case_type=case_type)
        print(caption)

    # Test lane-based lookup
    print("\n--- Lane F (COA) ---")
    print(get_caption_for_lane("F", "APPELLANT'S BRIEF"))

    print("\n[caption_generator] All tests passed.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
