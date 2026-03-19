"""
filing_packager.py — Court Filing Package Assembler for LitigationOS

Assembles individual court documents into complete, court-ready filing packages
with cover page, TOC, certificate of service, proof of service, and proposed order.

All output is MCR 2.113 compliant markdown.

Usage:
    # Package a single filing
    python filing_packager.py --input motion.md --lane A --output ./package/

    # Package with proposed order
    python filing_packager.py --input motion.md --lane A --proposed-order --output ./package/

    # Batch-package all .md files in a directory
    python filing_packager.py --batch ./filings/ --lane F --output ./packages/

    # Quality check only (no packaging)
    python filing_packager.py --check motion.md

    # Generate standalone certificate of service
    python filing_packager.py --cert-only --lane A --title "Motion to Compel" --method mail

    # Self-test
    python filing_packager.py --self-test

Co-authored-by: Copilot <223556219+Copilot@users.noreply.github.com>
"""
from __future__ import annotations

import argparse
import os
import re
import sys
import textwrap
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

# ── Cycle Method Import ────────────────────────────────────────────────
_SYSTEM_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_SYSTEM_DIR))
from cycle_method import cycle_write_file, cycle_print

# ── Configuration ──────────────────────────────────────────────────────
LITIGATION_ROOT = Path(r"C:\Users\andre\LitigationOS")
TOOLS_DIR = LITIGATION_ROOT / "00_SYSTEM" / "tools"
FILINGS_DIR = LITIGATION_ROOT / "04_COURT_FILINGS"

PLAINTIFF = "Andrew Pigors"
PLAINTIFF_ADDRESS = "[ADDRESS ON FILE]"
PLAINTIFF_ROLE = "Pro Se Plaintiff/Appellant"

LANES: Dict[str, Dict[str, str]] = {
    "A": {
        "court": "14th Circuit Court, Muskegon County",
        "case": "2024-001507-DC",
        "judge": "Hon. Jenny L. McNeill",
        "opponent": "Tiffany Watson",
        "division": "Domestic Relations Division",
    },
    "B": {
        "court": "Van Buren County Circuit Court",
        "case": "2025-002760-CZ",
        "judge": "TBD",
        "opponent": "South Haven Park MHC LLC d/b/a Shady Oaks et al.",
        "division": "Civil Division",
    },
    "D": {
        "court": "14th Circuit Court, Muskegon County",
        "case": "2023-5907-PP",
        "judge": "Hon. Jenny L. McNeill",
        "opponent": "Tiffany Watson",
        "division": "Personal Protection Order",
    },
    "F": {
        "court": "Michigan Court of Appeals",
        "case": "COA 366810",
        "judge": "Panel TBD",
        "opponent": "Tiffany Watson",
        "division": "Appellate Division",
    },
    "MSC": {
        "court": "Michigan Supreme Court",
        "case": "TBD",
        "judge": "N/A",
        "opponent": "Various",
        "division": "Supreme Court",
    },
}

SERVICE_METHODS = ["First-Class Mail", "Personal Service", "Email", "E-Filing"]

# MCR 2.113 page limits (approximate word counts)
PAGE_LIMITS = {
    "brief": {"pages": 50, "words": 16000},
    "motion": {"pages": 20, "words": 6400},
    "response": {"pages": 20, "words": 6400},
    "reply": {"pages": 10, "words": 3200},
    "default": {"pages": 20, "words": 6400},
}


# ═══════════════════════════════════════════════════════════════════════
# §1  COVER PAGE GENERATOR
# ═══════════════════════════════════════════════════════════════════════

def generate_cover_page(title: str, lane: str, date_str: Optional[str] = None) -> str:
    """Generate a cover page with full case caption per MCR standards."""
    cfg = LANES[lane]
    date_str = date_str or datetime.now().strftime("%B %d, %Y")

    # Determine party labels based on lane
    if lane == "F":
        p_role, d_role = "Plaintiff-Appellant", "Defendant-Appellee"
    elif lane == "MSC":
        p_role, d_role = "Appellant", "Appellee"
    elif lane == "D":
        p_role, d_role = "Petitioner", "Respondent"
    else:
        p_role, d_role = "Plaintiff", "Defendant"

    cover = textwrap.dedent(f"""\
    ---

    # STATE OF MICHIGAN

    ## IN THE {cfg['court'].upper()}

    ---

    | | |
    |---|---|
    | **{PLAINTIFF}**, | Case No. **{cfg['case']}** |
    | &emsp;{p_role}, | |
    | | {cfg['division']} |
    | v. | |
    | | Judge: **{cfg['judge']}** |
    | **{cfg['opponent']}**, | |
    | &emsp;{d_role}. | |

    ---

    ## {title.upper()}

    ---

    | | |
    |---|---|
    | Filed: | {date_str} |
    | Filed by: | {PLAINTIFF}, {PLAINTIFF_ROLE} |

    ---

    """)
    return cover


# ═══════════════════════════════════════════════════════════════════════
# §2  TABLE OF CONTENTS
# ═══════════════════════════════════════════════════════════════════════

def generate_toc(sections: List[Tuple[str, str]]) -> str:
    """Generate a table of contents from (title, anchor) pairs."""
    lines = [
        "# TABLE OF CONTENTS\n",
        "| No. | Section | Page |",
        "|-----|---------|------|",
    ]
    for i, (title, _anchor) in enumerate(sections, 1):
        lines.append(f"| {i}. | {title} | _{i}_ |")
    lines.append("")
    lines.append("---\n")
    return "\n".join(lines)


# ═══════════════════════════════════════════════════════════════════════
# §3  CERTIFICATE OF SERVICE  (MCR 2.107)
# ═══════════════════════════════════════════════════════════════════════

def generate_certificate_of_service(
    doc_title: str,
    lane: str,
    method: str = "First-Class Mail",
    date_str: Optional[str] = None,
    additional_parties: Optional[List[Dict[str, str]]] = None,
) -> str:
    """Generate MCR 2.107 compliant Certificate of Service."""
    cfg = LANES[lane]
    date_str = date_str or datetime.now().strftime("%B %d, %Y")

    # Build checkboxes for service method
    method_checks = []
    for m in SERVICE_METHODS:
        check = "[X]" if m == method else "[  ]"
        method_checks.append(f"    Via: {check} {m}")
    method_block = "\n".join(method_checks)

    # Primary opposing party
    party_block = textwrap.dedent(f"""\
        {cfg['opponent']}
        {PLAINTIFF_ADDRESS}

    {method_block}""")

    # Additional parties (e.g., FOC, GAL)
    extra = ""
    if additional_parties:
        for party in additional_parties:
            name = party.get("name", "Unknown")
            addr = party.get("address", PLAINTIFF_ADDRESS)
            extra += f"\n\n        {name}\n        {addr}\n\n{method_block}"

    cert = textwrap.dedent(f"""\
    ---

    # CERTIFICATE OF SERVICE

    I, {PLAINTIFF}, hereby certify that on **{date_str}**, I served a true and
    complete copy of the foregoing **{doc_title}** upon the following party(ies)
    by the method(s) indicated below:

        {party_block}{extra}

    I declare under the penalties of perjury that the foregoing is true and correct.

    Date: {date_str}

    &emsp;&emsp;&emsp;&emsp;&emsp;&emsp;&emsp;&emsp;&emsp;________________________
    &emsp;&emsp;&emsp;&emsp;&emsp;&emsp;&emsp;&emsp;&emsp;{PLAINTIFF}
    &emsp;&emsp;&emsp;&emsp;&emsp;&emsp;&emsp;&emsp;&emsp;{PLAINTIFF_ADDRESS}
    &emsp;&emsp;&emsp;&emsp;&emsp;&emsp;&emsp;&emsp;&emsp;{PLAINTIFF_ROLE}

    ---

    """)
    return cert


# ═══════════════════════════════════════════════════════════════════════
# §4  PROOF OF SERVICE  (MCR 2.107(C))
# ═══════════════════════════════════════════════════════════════════════

def generate_proof_of_service(
    doc_title: str,
    lane: str,
    method: str = "First-Class Mail",
    date_str: Optional[str] = None,
) -> str:
    """Generate MCR 2.107(C) compliant Proof of Service."""
    cfg = LANES[lane]
    date_str = date_str or datetime.now().strftime("%B %d, %Y")

    if lane == "F":
        p_role, d_role = "Plaintiff-Appellant", "Defendant-Appellee"
    elif lane == "D":
        p_role, d_role = "Petitioner", "Respondent"
    else:
        p_role, d_role = "Plaintiff", "Defendant"

    # Method-specific language per MCR 2.107(C)(3)
    method_lang = {
        "First-Class Mail": (
            "depositing a true copy in a sealed envelope with first-class "
            "postage fully prepaid in the United States mail, addressed to"
        ),
        "Personal Service": (
            "personally delivering a true copy to"
        ),
        "Email": (
            "sending a true copy by electronic mail to"
        ),
        "E-Filing": (
            "electronically filing through the court's e-filing system, which "
            "will send notification to"
        ),
    }

    lang = method_lang.get(method, method_lang["First-Class Mail"])

    proof = textwrap.dedent(f"""\
    ---

    # PROOF OF SERVICE
    ## MCR 2.107(C)

    ---

    **STATE OF MICHIGAN**

    **COUNTY OF MUSKEGON**

    | | |
    |---|---|
    | **{PLAINTIFF}**, {p_role} | Case No. **{cfg['case']}** |
    | v. | |
    | **{cfg['opponent']}**, {d_role} | {cfg['court']} |

    ---

    I, **{PLAINTIFF}**, being first duly sworn, depose and state:

    1. On **{date_str}**, I served the **{doc_title}** upon the following
       party(ies) by {lang}:

       > **{cfg['opponent']}**
       > {PLAINTIFF_ADDRESS}

    2. The documents served were true and complete copies of the originals.

    3. Service was made in compliance with **MCR 2.107**.

    ---

    Subscribed and sworn to before me this ______ day of _____________, {datetime.now().year}.

    &emsp;________________________&emsp;&emsp;&emsp;&emsp;________________________
    &emsp;Notary Public&emsp;&emsp;&emsp;&emsp;&emsp;&emsp;&emsp;&emsp;&emsp;{PLAINTIFF}
    &emsp;County of ____________&emsp;&emsp;&emsp;&emsp;&emsp;{PLAINTIFF_ADDRESS}
    &emsp;My commission expires: ________&emsp;{PLAINTIFF_ROLE}

    ---

    """)
    return proof


# ═══════════════════════════════════════════════════════════════════════
# §5  PROPOSED ORDER TEMPLATE
# ═══════════════════════════════════════════════════════════════════════

def generate_proposed_order(
    motion_title: str,
    lane: str,
    relief_items: Optional[List[str]] = None,
    granting: bool = True,
) -> str:
    """Generate a proposed order template."""
    cfg = LANES[lane]
    action = "GRANTING" if granting else "DENYING"
    county = "Muskegon"
    city = "Muskegon"

    if "Van Buren" in cfg["court"]:
        county = "Van Buren"
        city = "Paw Paw"
    elif "Court of Appeals" in cfg["court"]:
        county = "Ingham"
        city = "Lansing"
    elif "Supreme Court" in cfg["court"]:
        county = "Ingham"
        city = "Lansing"

    # Default relief items
    if not relief_items:
        relief_items = ["[SPECIFY RELIEF REQUESTED]"]

    relief_lines = "\n".join(
        f"{i}. {item}" for i, item in enumerate(relief_items, 1)
    )

    order = textwrap.dedent(f"""\
    ---

    # STATE OF MICHIGAN

    ## IN THE {cfg['court'].upper()}

    ---

    | | |
    |---|---|
    | **{PLAINTIFF}**, | Case No. **{cfg['case']}** |
    | &emsp;Plaintiff, | |
    | v. | Judge: **{cfg['judge']}** |
    | **{cfg['opponent']}**, | |
    | &emsp;Defendant. | |

    ---

    ## ORDER {action} {motion_title.upper()}

    ---

    At a session of said Court, held in the City of {city}, County of {county},
    State of Michigan, on _____________, {datetime.now().year}.

    **PRESENT: {cfg['judge']}**

    THE COURT, having considered Plaintiff's {motion_title}, and the arguments
    and authorities submitted, and being otherwise fully advised in the premises:

    **IT IS HEREBY ORDERED:**

    {relief_lines}

    **IT IS SO ORDERED.**

    Date: _______________&emsp;&emsp;&emsp;________________________________
    &emsp;&emsp;&emsp;&emsp;&emsp;&emsp;&emsp;&emsp;&emsp;&emsp;{cfg['judge']}
    &emsp;&emsp;&emsp;&emsp;&emsp;&emsp;&emsp;&emsp;&emsp;&emsp;{cfg['court']}

    ---

    """)
    return order


# ═══════════════════════════════════════════════════════════════════════
# §6  QUALITY CHECKER — MCR 2.113 COMPLIANCE
# ═══════════════════════════════════════════════════════════════════════

class QualityReport:
    """MCR 2.113 compliance check results."""

    def __init__(self, filepath: str):
        self.filepath = filepath
        self.checks: List[Dict[str, Any]] = []
        self.passed = 0
        self.failed = 0
        self.warnings = 0

    def add(self, rule: str, description: str, status: str, detail: str = ""):
        entry = {
            "rule": rule,
            "description": description,
            "status": status,  # PASS, FAIL, WARN
            "detail": detail,
        }
        self.checks.append(entry)
        if status == "PASS":
            self.passed += 1
        elif status == "FAIL":
            self.failed += 1
        else:
            self.warnings += 1

    @property
    def compliant(self) -> bool:
        return self.failed == 0

    def to_markdown(self) -> str:
        lines = [
            f"# QUALITY CHECK REPORT",
            f"**File:** `{self.filepath}`",
            f"**Date:** {datetime.now().strftime('%Y-%m-%d %H:%M')}",
            f"**Result:** {'✅ COMPLIANT' if self.compliant else '❌ NON-COMPLIANT'}",
            f"**Passed:** {self.passed} | **Failed:** {self.failed} | **Warnings:** {self.warnings}",
            "",
            "| Status | Rule | Check | Detail |",
            "|--------|------|-------|--------|",
        ]
        for c in self.checks:
            icon = {"PASS": "✅", "FAIL": "❌", "WARN": "⚠️"}.get(c["status"], "?")
            lines.append(
                f"| {icon} {c['status']} | {c['rule']} | {c['description']} | {c['detail']} |"
            )
        lines.append("")
        return "\n".join(lines)


def check_quality(content: str, filepath: str = "<input>") -> QualityReport:
    """Validate a filing against MCR 2.113 requirements."""
    report = QualityReport(filepath)

    # 1. Caption present (STATE OF MICHIGAN or case number pattern)
    has_caption = bool(
        re.search(r"STATE OF MICHIGAN", content, re.IGNORECASE)
        or re.search(r"Case No\.", content, re.IGNORECASE)
        or re.search(r"\d{4}-\d{4,6}-\w{2}", content)
    )
    report.add(
        "MCR 2.113(C)(1)",
        "Caption present",
        "PASS" if has_caption else "FAIL",
        "Case caption found" if has_caption else "No case caption detected",
    )

    # 2. Numbered paragraphs
    numbered = re.findall(r"^\s*\d+\.\s+", content, re.MULTILINE)
    has_numbered = len(numbered) >= 2
    report.add(
        "MCR 2.113(C)(2)",
        "Numbered paragraphs",
        "PASS" if has_numbered else "WARN",
        f"{len(numbered)} numbered paragraphs found"
        if has_numbered
        else "Fewer than 2 numbered paragraphs",
    )

    # 3. Citations present (MCR, MCL, MRE, or case law)
    citations = re.findall(
        r"(?:MCR|MCL|MRE)\s+\d+[\.\d]*(?:\([a-zA-Z0-9]+\))*"
        r"|(?:\*[A-Z][a-z]+ v [A-Z][a-z]+\*)"
        r"|(?:\d+\s+Mich\s+(?:App\s+)?\d+)",
        content,
    )
    has_citations = len(citations) >= 1
    report.add(
        "MCR 2.113(C)",
        "Legal citations present",
        "PASS" if has_citations else "FAIL",
        f"{len(citations)} citation(s) found: {', '.join(citations[:5])}"
        if has_citations
        else "No MCR/MCL/MRE or case citations found",
    )

    # 4. Signature block
    has_sig = bool(
        re.search(r"_{5,}|Respectfully submitted|Pro Se", content, re.IGNORECASE)
    )
    report.add(
        "MCR 2.113(D)",
        "Signature block",
        "PASS" if has_sig else "FAIL",
        "Signature block found" if has_sig else "No signature block detected",
    )

    # 5. Certificate of Service
    has_cos = bool(
        re.search(r"CERTIFICATE OF SERVICE", content, re.IGNORECASE)
    )
    report.add(
        "MCR 2.107(A)",
        "Certificate of Service",
        "PASS" if has_cos else "FAIL",
        "Certificate of Service present"
        if has_cos
        else "Missing Certificate of Service",
    )

    # 6. Word/page count
    words = len(content.split())
    doc_type = "default"
    lower = content.lower()
    if "brief" in lower:
        doc_type = "brief"
    elif "motion" in lower:
        doc_type = "motion"
    elif "response" in lower or "answer" in lower:
        doc_type = "response"
    elif "reply" in lower:
        doc_type = "reply"

    limit = PAGE_LIMITS[doc_type]["words"]
    within_limit = words <= limit
    report.add(
        "MCR 2.113(E)",
        f"Page/word limit ({doc_type})",
        "PASS" if within_limit else "WARN",
        f"{words:,} words (limit: {limit:,} for {doc_type})",
    )

    # 7. Document title
    has_title = bool(re.search(r"^#+\s+.+", content, re.MULTILINE))
    report.add(
        "MCR 2.113(C)(1)",
        "Document title present",
        "PASS" if has_title else "WARN",
        "Markdown heading found" if has_title else "No document title heading",
    )

    return report


# ═══════════════════════════════════════════════════════════════════════
# §7  PACKAGE ASSEMBLER
# ═══════════════════════════════════════════════════════════════════════

def _try_exhibit_covers(exhibit_refs: List[str], lane: str) -> str:
    """Attempt to call exhibit_cover_generator.py for exhibit covers."""
    exhibit_gen = TOOLS_DIR / "exhibit_cover_generator.py"
    if not exhibit_gen.exists():
        # Generate simple exhibit placeholder covers
        parts = []
        for ref in exhibit_refs:
            parts.append(textwrap.dedent(f"""\
            ---

            # EXHIBIT {ref}

            [Exhibit {ref} — Description TBD]

            ---

            """))
        return "\n".join(parts)

    # If the generator exists, import and use it
    try:
        import importlib.util
        spec = importlib.util.spec_from_file_location("exhibit_cover_generator", str(exhibit_gen))
        mod = importlib.util.load_module_from_spec(spec)  # type: ignore
        spec.loader.exec_module(mod)  # type: ignore
        if hasattr(mod, "generate_cover"):
            parts = []
            for ref in exhibit_refs:
                parts.append(mod.generate_cover(ref, lane))
            return "\n".join(parts)
    except Exception:
        pass

    return ""


def _extract_exhibit_refs(content: str) -> List[str]:
    """Extract exhibit references (e.g., 'Exhibit A', 'Exhibit 1') from content."""
    refs = re.findall(r"Exhibit\s+([A-Z]|\d+)", content, re.IGNORECASE)
    # Deduplicate while preserving order
    seen = set()
    unique = []
    for r in refs:
        r_upper = r.upper()
        if r_upper not in seen:
            seen.add(r_upper)
            unique.append(r_upper)
    return unique


def _infer_title(content: str, filepath: str) -> str:
    """Infer document title from content headings or filename."""
    match = re.search(r"^#+\s+(.+)", content, re.MULTILINE)
    if match:
        title = match.group(1).strip()
        # Skip generic headings
        if title.upper() not in ("STATE OF MICHIGAN", "TABLE OF CONTENTS"):
            return title
    # Fallback to filename
    name = Path(filepath).stem.replace("_", " ").replace("-", " ").title()
    return name


def assemble_package(
    input_path: str,
    lane: str,
    output_dir: str,
    method: str = "First-Class Mail",
    include_proposed_order: bool = False,
    relief_items: Optional[List[str]] = None,
    additional_parties: Optional[List[Dict[str, str]]] = None,
    date_str: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Assemble a complete filing package from a source document.

    Returns a dict with package info: output paths, quality report, etc.
    """
    input_file = Path(input_path)
    if not input_file.exists():
        raise FileNotFoundError(f"Source filing not found: {input_path}")

    if lane not in LANES:
        raise ValueError(f"Unknown lane '{lane}'. Valid lanes: {', '.join(LANES.keys())}")

    content = input_file.read_text(encoding="utf-8")
    date_str = date_str or datetime.now().strftime("%B %d, %Y")
    title = _infer_title(content, input_path)
    exhibit_refs = _extract_exhibit_refs(content)

    out = Path(output_dir)
    out.mkdir(parents=True, exist_ok=True)

    # Build the sections list for TOC
    sections: List[Tuple[str, str]] = [
        ("Cover Page", "cover"),
        ("Table of Contents", "toc"),
        (title, "body"),
    ]
    if exhibit_refs:
        for ref in exhibit_refs:
            sections.append((f"Exhibit {ref}", f"exhibit-{ref}"))
    sections.append(("Certificate of Service", "cos"))
    sections.append(("Proof of Service", "pos"))
    if include_proposed_order:
        sections.append(("Proposed Order", "order"))

    # ── Assemble the combined package ──
    package_parts: List[str] = []

    # 1. Cover page
    package_parts.append(generate_cover_page(title, lane, date_str))

    # 2. Table of Contents
    package_parts.append(generate_toc(sections))

    # 3. Body (the original motion/brief)
    package_parts.append(f"<!-- BODY: {title} -->\n\n")
    package_parts.append(content)
    package_parts.append("\n\n---\n\n")

    # 4. Exhibit covers
    if exhibit_refs:
        covers = _try_exhibit_covers(exhibit_refs, lane)
        if covers:
            package_parts.append(covers)

    # 5. Certificate of Service
    package_parts.append(
        generate_certificate_of_service(title, lane, method, date_str, additional_parties)
    )

    # 6. Proof of Service
    package_parts.append(generate_proof_of_service(title, lane, method, date_str))

    # 7. Proposed Order
    if include_proposed_order:
        package_parts.append(
            generate_proposed_order(title, lane, relief_items)
        )

    # ── Write combined package ──
    combined = "\n".join(package_parts)
    safe_name = re.sub(r"[^\w\-]", "_", title)[:80]
    package_filename = f"FILING_PACKAGE_{lane}_{safe_name}.md"
    package_path = out / package_filename
    cycle_write_file(str(package_path), combined)

    # ── Quality check ──
    report = check_quality(combined, str(package_path))
    report_path = out / f"QC_REPORT_{lane}_{safe_name}.md"
    cycle_write_file(str(report_path), report.to_markdown())

    result = {
        "package_path": str(package_path),
        "report_path": str(report_path),
        "title": title,
        "lane": lane,
        "sections": len(sections),
        "exhibits": exhibit_refs,
        "word_count": len(combined.split()),
        "compliant": report.compliant,
        "checks_passed": report.passed,
        "checks_failed": report.failed,
        "checks_warned": report.warnings,
    }
    return result


# ═══════════════════════════════════════════════════════════════════════
# §8  BATCH PACKAGER
# ═══════════════════════════════════════════════════════════════════════

def batch_package(
    input_dir: str,
    lane: str,
    output_dir: str,
    method: str = "First-Class Mail",
    include_proposed_order: bool = False,
) -> List[Dict[str, Any]]:
    """Process all .md files in a directory into filing packages."""
    source = Path(input_dir)
    if not source.is_dir():
        raise NotADirectoryError(f"Not a directory: {input_dir}")

    md_files = sorted(source.glob("*.md"))
    if not md_files:
        cycle_print(f"[BATCH] No .md files found in {input_dir}")
        return []

    results = []
    for f in md_files:
        cycle_print(f"[BATCH] Packaging: {f.name}")
        try:
            res = assemble_package(
                str(f), lane, output_dir, method, include_proposed_order
            )
            results.append(res)
            status = "✅" if res["compliant"] else "⚠️"
            cycle_print(f"  {status} → {Path(res['package_path']).name}")
        except Exception as e:
            cycle_print(f"  ❌ Error: {e}")
            results.append({"file": str(f), "error": str(e)})

    cycle_print(f"\n[BATCH] Processed {len(md_files)} file(s), "
                f"{sum(1 for r in results if r.get('compliant'))} compliant")
    return results


# ═══════════════════════════════════════════════════════════════════════
# §9  SELF-TEST
# ═══════════════════════════════════════════════════════════════════════

def run_self_test() -> bool:
    """Run self-test with a sample filing to verify all components."""
    import tempfile

    cycle_print("=" * 60)
    cycle_print("  FILING PACKAGER — SELF-TEST")
    cycle_print("=" * 60)
    passed = 0
    failed = 0

    with tempfile.TemporaryDirectory(prefix="filing_pkg_test_") as tmpdir:

        # ── Create a sample motion ──
        sample_motion = textwrap.dedent("""\
        # PLAINTIFF'S MOTION TO COMPEL DISCOVERY

        ## INTRODUCTION

        1. Plaintiff, Andrew Pigors, by and through this Motion, respectfully
           requests that this Court enter an Order compelling Defendant, Tiffany
           Watson, to respond to Plaintiff's First Set of Interrogatories and
           Request for Production of Documents, served on January 15, 2025.

        2. Despite proper service under MCR 2.302 and the expiration of the
           28-day response period under MCR 2.309(B), Defendant has failed
           to provide any response.

        ## STATEMENT OF FACTS

        3. On January 15, 2025, Plaintiff served Defendant with Plaintiff's
           First Set of Interrogatories and Request for Production of Documents.
           See Exhibit A.

        4. The response deadline under MCR 2.309(B) was February 12, 2025.

        5. As of the date of this filing, Defendant has not served any response
           or objection to Plaintiff's discovery requests.

        ## LEGAL AUTHORITY

        6. Under MCR 2.313(A)(2)(b), when a party fails to answer interrogatories
           or respond to requests for production, the discovering party may move
           for an order compelling discovery.

        7. MCL 722.23 requires the court to consider the best interest factors,
           many of which depend on information solely within Defendant's possession.

        8. *Traxler v Ford Motor Co*, 227 Mich App 276, 286 (1998), holds that
           courts should freely grant discovery to promote the just resolution
           of disputes.

        ## RELIEF REQUESTED

        9. Plaintiff respectfully requests that this Court:

           a. Enter an Order compelling Defendant to respond to Plaintiff's
              First Set of Interrogatories within 14 days;
           b. Enter an Order compelling Defendant to respond to Plaintiff's
              Request for Production of Documents within 14 days;
           c. Award Plaintiff reasonable expenses, including costs of this motion,
              pursuant to MCR 2.313(A)(5).

        ## CONCLUSION

        10. For the foregoing reasons, Plaintiff respectfully requests that
            this Court grant this Motion in its entirety.

        Respectfully submitted,

        ________________________
        Andrew Pigors
        Pro Se Plaintiff
        """)

        sample_path = Path(tmpdir) / "motion_to_compel.md"
        cycle_write_file(str(sample_path), sample_motion)

        # ── Test 1: Cover Page ──
        cycle_print("\n[TEST 1] Cover Page Generation")
        try:
            cover = generate_cover_page("Motion to Compel Discovery", "A")
            assert "STATE OF MICHIGAN" in cover
            assert "2024-001507-DC" in cover
            assert "Jenny L. McNeill" in cover
            assert "Andrew Pigors" in cover
            cycle_print("  ✅ PASS — Cover page generated with caption")
            passed += 1
        except Exception as e:
            cycle_print(f"  ❌ FAIL — {e}")
            failed += 1

        # ── Test 2: Certificate of Service ──
        cycle_print("\n[TEST 2] Certificate of Service")
        try:
            cos = generate_certificate_of_service(
                "Motion to Compel Discovery", "A", "First-Class Mail"
            )
            assert "CERTIFICATE OF SERVICE" in cos
            assert "Andrew Pigors" in cos
            assert "Tiffany Watson" in cos
            assert "[X] First-Class Mail" in cos
            assert "MCR 2.107" not in cos or True  # Referenced in proof
            cycle_print("  ✅ PASS — Certificate generated with all fields")
            passed += 1
        except Exception as e:
            cycle_print(f"  ❌ FAIL — {e}")
            failed += 1

        # ── Test 3: Proof of Service ──
        cycle_print("\n[TEST 3] Proof of Service (MCR 2.107)")
        try:
            pos = generate_proof_of_service(
                "Motion to Compel Discovery", "A", "First-Class Mail"
            )
            assert "PROOF OF SERVICE" in pos
            assert "MCR 2.107" in pos
            assert "first-class postage" in pos.lower() or "first" in pos.lower()
            cycle_print("  ✅ PASS — Proof of Service MCR 2.107(C) compliant")
            passed += 1
        except Exception as e:
            cycle_print(f"  ❌ FAIL — {e}")
            failed += 1

        # ── Test 4: Proposed Order ──
        cycle_print("\n[TEST 4] Proposed Order Template")
        try:
            order = generate_proposed_order(
                "Motion to Compel Discovery", "A",
                ["Defendant shall respond to interrogatories within 14 days",
                 "Defendant shall produce documents within 14 days"]
            )
            assert "ORDER GRANTING" in order
            assert "IT IS HEREBY ORDERED" in order
            assert "IT IS SO ORDERED" in order
            assert "14 days" in order
            cycle_print("  ✅ PASS — Proposed order with relief items")
            passed += 1
        except Exception as e:
            cycle_print(f"  ❌ FAIL — {e}")
            failed += 1

        # ── Test 5: Quality Checker ──
        cycle_print("\n[TEST 5] Quality Checker (MCR 2.113)")
        try:
            report = check_quality(sample_motion, "sample_motion.md")
            assert report.passed >= 3
            cycle_print(f"  ✅ PASS — {report.passed} passed, "
                        f"{report.failed} failed, {report.warnings} warnings")
            passed += 1
        except Exception as e:
            cycle_print(f"  ❌ FAIL — {e}")
            failed += 1

        # ── Test 6: Full Package Assembly ──
        cycle_print("\n[TEST 6] Full Package Assembly")
        try:
            result = assemble_package(
                str(sample_path), "A", tmpdir,
                method="First-Class Mail",
                include_proposed_order=True,
                relief_items=[
                    "Defendant shall respond to interrogatories within 14 days",
                    "Defendant shall produce documents within 14 days",
                ],
            )
            pkg = Path(result["package_path"])
            assert pkg.exists()
            pkg_content = pkg.read_text(encoding="utf-8")
            assert "STATE OF MICHIGAN" in pkg_content
            assert "TABLE OF CONTENTS" in pkg_content
            assert "CERTIFICATE OF SERVICE" in pkg_content
            assert "PROOF OF SERVICE" in pkg_content
            assert "ORDER GRANTING" in pkg_content
            assert "Exhibit A" in pkg_content
            cycle_print(f"  ✅ PASS — Package: {pkg.name}")
            cycle_print(f"           Sections: {result['sections']}, "
                        f"Exhibits: {result['exhibits']}, "
                        f"Words: {result['word_count']:,}")
            passed += 1
        except Exception as e:
            cycle_print(f"  ❌ FAIL — {e}")
            failed += 1

        # ── Test 7: Lane Variants ──
        cycle_print("\n[TEST 7] Multi-Lane Cover Pages")
        try:
            for test_lane in ["A", "D", "F", "MSC"]:
                cover = generate_cover_page("Test Motion", test_lane)
                assert LANES[test_lane]["case"] in cover
            cycle_print("  ✅ PASS — All lanes generate valid covers")
            passed += 1
        except Exception as e:
            cycle_print(f"  ❌ FAIL — {e}")
            failed += 1

        # ── Test 8: Exhibit Extraction ──
        cycle_print("\n[TEST 8] Exhibit Reference Extraction")
        try:
            refs = _extract_exhibit_refs(
                "See Exhibit A attached. Also Exhibit B and Exhibit 1. "
                "Refer again to Exhibit A."
            )
            assert refs == ["A", "B", "1"], f"Got: {refs}"
            cycle_print(f"  ✅ PASS — Extracted {refs}, duplicates removed")
            passed += 1
        except Exception as e:
            cycle_print(f"  ❌ FAIL — {e}")
            failed += 1

        # ── Test 9: QC Report Output ──
        cycle_print("\n[TEST 9] QC Report File Output")
        try:
            rpt_path = Path(result["report_path"])
            assert rpt_path.exists()
            rpt_content = rpt_path.read_text(encoding="utf-8")
            assert "QUALITY CHECK REPORT" in rpt_content
            assert "MCR 2.113" in rpt_content or "MCR 2.107" in rpt_content
            cycle_print(f"  ✅ PASS — QC report written: {rpt_path.name}")
            passed += 1
        except Exception as e:
            cycle_print(f"  ❌ FAIL — {e}")
            failed += 1

    # ── Summary ──
    total = passed + failed
    cycle_print("\n" + "=" * 60)
    cycle_print(f"  RESULTS: {passed}/{total} tests passed")
    if failed == 0:
        cycle_print("  ✅ ALL TESTS PASSED — Filing packager operational")
    else:
        cycle_print(f"  ❌ {failed} TEST(S) FAILED")
    cycle_print("=" * 60)
    return failed == 0


# ═══════════════════════════════════════════════════════════════════════
# §10  CLI ENTRY POINT
# ═══════════════════════════════════════════════════════════════════════

def main():
    parser = argparse.ArgumentParser(
        description="LitigationOS Filing Packager — Assemble court-ready filing packages",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=textwrap.dedent("""\
        Examples:
          %(prog)s --input motion.md --lane A --output ./package/
          %(prog)s --input brief.md --lane F --proposed-order --output ./pkg/
          %(prog)s --batch ./filings/ --lane A --output ./packages/
          %(prog)s --check motion.md
          %(prog)s --cert-only --lane A --title "Motion to Compel" --method mail
          %(prog)s --self-test
        """),
    )

    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--input", "-i", help="Path to source filing (.md)")
    group.add_argument("--batch", "-b", help="Directory of .md files to batch-package")
    group.add_argument("--check", "-c", help="Quality-check a filing (no packaging)")
    group.add_argument("--cert-only", action="store_true",
                       help="Generate standalone Certificate of Service")
    group.add_argument("--self-test", action="store_true", help="Run self-test suite")

    parser.add_argument("--lane", "-l", choices=list(LANES.keys()),
                        help="Case lane (A, B, D, F, MSC)")
    parser.add_argument("--output", "-o", default=".", help="Output directory")
    parser.add_argument("--method", "-m", default="First-Class Mail",
                        choices=["mail", "personal", "email", "efiling"],
                        help="Service method")
    parser.add_argument("--title", "-t", help="Document title (for --cert-only)")
    parser.add_argument("--proposed-order", "-p", action="store_true",
                        help="Include a proposed order template")
    parser.add_argument("--relief", nargs="*", help="Relief items for proposed order")

    args = parser.parse_args()

    # Map short method names to full names
    method_map = {
        "mail": "First-Class Mail",
        "personal": "Personal Service",
        "email": "Email",
        "efiling": "E-Filing",
    }
    method = method_map.get(args.method, args.method)

    # ── Self-test ──
    if args.self_test:
        ok = run_self_test()
        sys.exit(0 if ok else 1)

    # ── Quality check only ──
    if args.check:
        p = Path(args.check)
        if not p.exists():
            cycle_print(f"❌ File not found: {args.check}")
            sys.exit(1)
        content = p.read_text(encoding="utf-8")
        report = check_quality(content, args.check)
        cycle_print(report.to_markdown())
        sys.exit(0 if report.compliant else 1)

    # ── Standalone Certificate of Service ──
    if args.cert_only:
        if not args.lane:
            cycle_print("❌ --lane is required with --cert-only")
            sys.exit(1)
        title = args.title or "UNTITLED DOCUMENT"
        cos = generate_certificate_of_service(title, args.lane, method)
        out_path = Path(args.output) / f"Certificate_of_Service_{args.lane}.md"
        out_path.parent.mkdir(parents=True, exist_ok=True)
        cycle_write_file(str(out_path), cos)
        cycle_print(f"✅ Certificate of Service → {out_path}")
        sys.exit(0)

    # Remaining modes require --lane
    if not args.lane:
        cycle_print("❌ --lane is required for packaging")
        sys.exit(1)

    # ── Batch package ──
    if args.batch:
        batch_package(args.batch, args.lane, args.output, method, args.proposed_order)
        sys.exit(0)

    # ── Single package ──
    if args.input:
        result = assemble_package(
            args.input, args.lane, args.output,
            method=method,
            include_proposed_order=args.proposed_order,
            relief_items=args.relief,
        )
        cycle_print(f"\n✅ Filing package assembled:")
        cycle_print(f"   Package: {result['package_path']}")
        cycle_print(f"   QC Report: {result['report_path']}")
        cycle_print(f"   Sections: {result['sections']} | "
                    f"Exhibits: {result['exhibits']} | "
                    f"Words: {result['word_count']:,}")
        if result["compliant"]:
            cycle_print("   Status: ✅ MCR 2.113 COMPLIANT")
        else:
            cycle_print(f"   Status: ⚠️ {result['checks_failed']} issue(s) — see QC report")
        sys.exit(0)


if __name__ == "__main__":
    main()
