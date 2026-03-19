# -*- coding: utf-8 -*-
"""Engine 15: E-Filing Preparer — MiFile, TrueFiling, CM/ECF preparation.

Prepares court documents for electronic filing across Michigan's court systems:
  - MiFile: Michigan's mandatory e-filing system (14th Circuit, most MI courts)
  - TrueFiling: COA and MSC e-filing system
  - CM/ECF: Federal court e-filing (USDC Western District MI)

Authority:
    MCR 1.109(G)       — E-filing requirements
    SCAO AO 2019-08    — Statewide e-filing mandate
    MCR 7.202(1)       — COA TrueFiling
    W.D. Mich. LCivR 5.7 — CM/ECF requirements
"""
import sys
import os
import io
import re
import json
import sqlite3
from datetime import datetime
from typing import Dict, List, Optional
from pathlib import Path

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

# ── Case constants ──────────────────────────────────────────────────────────
CASE_NUMBERS = {
    "custody": "2024-001507-DC",
    "ppo": "2023-5907-PP",
    "coa_appeal": "366810",
    "msc": "TBD",
    "usdc": "TBD",
    "jtc": "N/A",
}

FILER = {
    "name": "Andrew Pigors",
    "role": "Plaintiff / Appellant / Petitioner (Pro Se)",
    "address": None,  # Redacted — set at filing time
    "phone": None,
    "email": None,
}

# ── MiFile filing codes ────────────────────────────────────────────────────
MIFILE_FILING_CODES: Dict[str, Dict] = {
    "MOTION": {
        "code": "MOT",
        "description": "Motion",
        "fee": 20.00,
        "authority": "MCR 2.119",
    },
    "BRIEF": {
        "code": "BRF",
        "description": "Brief in Support / Response",
        "fee": 0.00,
        "authority": "MCR 2.119(A)(2)",
    },
    "AFFIDAVIT": {
        "code": "AFF",
        "description": "Affidavit",
        "fee": 0.00,
        "authority": "MCR 2.119(B)",
    },
    "PROPOSED_ORDER": {
        "code": "PO",
        "description": "Proposed Order",
        "fee": 0.00,
        "authority": "MCR 2.119(A)(2)",
    },
    "NOTICE": {
        "code": "NTC",
        "description": "Notice",
        "fee": 0.00,
        "authority": "MCR 2.107",
    },
    "PROOF_OF_SERVICE": {
        "code": "POS",
        "description": "Proof of Service",
        "fee": 0.00,
        "authority": "MCR 2.104",
    },
    "RESPONSE": {
        "code": "RSP",
        "description": "Response to Motion",
        "fee": 0.00,
        "authority": "MCR 2.119(C)(2)",
    },
    "REPLY": {
        "code": "RPL",
        "description": "Reply Brief",
        "fee": 0.00,
        "authority": "MCR 2.119(C)(3)",
    },
    "OBJECTION": {
        "code": "OBJ",
        "description": "Objection",
        "fee": 0.00,
        "authority": "MCR 3.208",
    },
    "STIPULATION": {
        "code": "STIP",
        "description": "Stipulation / Agreement",
        "fee": 0.00,
        "authority": "MCR 2.507",
    },
    "EXHIBIT": {
        "code": "EXH",
        "description": "Exhibit(s)",
        "fee": 0.00,
        "authority": "MRE 901",
    },
    "FEE_WAIVER": {
        "code": "MC20",
        "description": "Fee Waiver Request (MC 20)",
        "fee": 0.00,
        "authority": "MCR 2.002",
    },
    "EMERGENCY_MOTION": {
        "code": "EMOT",
        "description": "Emergency Motion",
        "fee": 20.00,
        "authority": "MCR 2.119",
    },
    "MOTION_FOR_RECONSIDERATION": {
        "code": "MRC",
        "description": "Motion for Reconsideration",
        "fee": 20.00,
        "authority": "MCR 2.119(F)",
    },
}

# ── E-filing system specifications ──────────────────────────────────────────
EFILING_SYSTEMS: Dict[str, Dict] = {
    "mifile": {
        "name": "MiFile (Michigan Court E-Filing)",
        "url": "https://mifile.courts.michigan.gov",
        "courts": ["14th_circuit", "most_michigan_courts"],
        "file_format": "PDF",
        "text_searchable_required": True,
        "max_file_size_mb": 50,
        "max_envelope_size_mb": 250,
        "accepted_formats": [".pdf"],
        "filing_time_cutoff": "11:59 PM ET",
        "service_via_system": True,
        "payment_methods": ["credit_card", "fee_waiver"],
        "authority": "MCR 1.109(G); SCAO AO 2019-08",
        "requirements": [
            "PDF format (text-searchable preferred)",
            "Proper filing code selected",
            "Case number must match exactly",
            "Fee payment or waiver attached",
            "Certificate of Service included",
            "File size under 50MB per document",
            "No password protection on PDF",
            "No embedded multimedia",
        ],
    },
    "truefiling": {
        "name": "TrueFiling",
        "url": "https://www.truefiling.com",
        "courts": ["coa", "msc"],
        "file_format": "PDF",
        "text_searchable_required": True,
        "max_file_size_mb": 25,
        "max_envelope_size_mb": 100,
        "accepted_formats": [".pdf"],
        "bookmarks_required": True,
        "filing_time_cutoff": "11:59 PM ET",
        "service_via_system": True,
        "payment_methods": ["credit_card", "fee_waiver"],
        "authority": "MCR 7.202(1); COA/MSC Administrative Orders",
        "requirements": [
            "PDF format (text-searchable required)",
            "PDF bookmarks for major sections",
            "Table of Contents with hyperlinks (recommended)",
            "File size under 25MB per document",
            "No password protection on PDF",
            "Proper case number and docket entry",
            "Service via TrueFiling to all parties",
            "MSC: also mail 13 paper copies",
        ],
    },
    "cmecf": {
        "name": "CM/ECF (PACER)",
        "url": "https://ecf.miwd.uscourts.gov",
        "courts": ["usdc_wdmi"],
        "file_format": "PDF",
        "text_searchable_required": True,
        "max_file_size_mb": 50,
        "max_single_doc_mb": 50,
        "accepted_formats": [".pdf"],
        "filing_time_cutoff": "11:59 PM ET",
        "service_via_system": True,
        "registration_required": True,
        "payment_methods": ["credit_card", "ifp_application"],
        "authority": "W.D. Mich. LCivR 5.7; FRCP 5(d)(3)",
        "requirements": [
            "PDF format (text-searchable)",
            "CM/ECF registration required",
            "Proper event code selected",
            "File size under 50MB",
            "IFP application (AO 240) if fee waiver needed",
            "Service via CM/ECF to registered attorneys",
            "Manual service to unregistered parties",
        ],
    },
}

CREATE_TABLE_SQL = """
CREATE TABLE IF NOT EXISTS efiling_log (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    document_name TEXT NOT NULL,
    court TEXT NOT NULL,
    case_number TEXT,
    efiling_system TEXT NOT NULL,
    filing_code TEXT,
    filing_type TEXT,
    file_path TEXT,
    file_size_bytes INTEGER,
    validation_status TEXT DEFAULT 'pending',
    validation_errors TEXT,
    prepared_at TEXT DEFAULT (datetime('now')),
    filed_at TEXT,
    confirmation_number TEXT,
    notes TEXT
);
"""


# ── Database helpers ────────────────────────────────────────────────────────

def _get_db() -> Optional[sqlite3.Connection]:
    """Connect to litigation_context.db."""
    if not os.path.exists(DB_PATH):
        return None
    conn = sqlite3.connect(DB_PATH, timeout=30)
    conn.row_factory = sqlite3.Row
    return conn


def _ensure_table(conn: sqlite3.Connection) -> None:
    """Create efiling_log table if needed."""
    conn.execute(CREATE_TABLE_SQL)
    conn.commit()


def _resolve_court(court: str) -> str:
    """Resolve court aliases."""
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


def _get_system_for_court(court_key: str) -> Optional[str]:
    """Determine which e-filing system a court uses."""
    court_to_system = {
        "14th_circuit": "mifile",
        "coa": "truefiling",
        "msc": "truefiling",
        "usdc_wdmi": "cmecf",
    }
    return court_to_system.get(court_key)


# ── Core functions ──────────────────────────────────────────────────────────

def validate_efile_requirements(
    doc_path: str,
    system: str = "mifile",
) -> Dict:
    """Validate a document meets e-filing requirements for a given system.

    Args:
        doc_path: Path to the document file.
        system: E-filing system (mifile, truefiling, cmecf).

    Returns:
        dict with validation results, errors, and warnings.
    """
    system_key = system.lower().replace(" ", "_").replace("-", "_")
    if system_key not in EFILING_SYSTEMS:
        return {
            "error": f"Unknown e-filing system: {system}",
            "valid_systems": list(EFILING_SYSTEMS.keys()),
        }

    spec = EFILING_SYSTEMS[system_key]
    errors: List[str] = []
    warnings: List[str] = []
    checks: List[Dict] = []

    # 1. File exists
    file_exists = os.path.exists(doc_path)
    checks.append({
        "check": "file_exists",
        "status": "PASS" if file_exists else "FAIL",
        "detail": doc_path,
    })
    if not file_exists:
        errors.append(f"File not found: {doc_path}")
        return {
            "valid": False,
            "system": system_key,
            "system_name": spec["name"],
            "checks": checks,
            "errors": errors,
            "warnings": warnings,
        }

    # 2. File extension
    ext = os.path.splitext(doc_path)[1].lower()
    ext_ok = ext in spec["accepted_formats"]
    checks.append({
        "check": "file_format",
        "status": "PASS" if ext_ok else "FAIL",
        "detail": f"Extension '{ext}' — required: {spec['accepted_formats']}",
    })
    if not ext_ok:
        errors.append(
            f"Invalid format '{ext}'. {spec['name']} requires: "
            f"{', '.join(spec['accepted_formats'])}"
        )

    # 3. File size
    file_size = os.path.getsize(doc_path)
    max_bytes = spec["max_file_size_mb"] * 1024 * 1024
    size_ok = file_size <= max_bytes
    size_mb = file_size / (1024 * 1024)
    checks.append({
        "check": "file_size",
        "status": "PASS" if size_ok else "FAIL",
        "detail": f"{size_mb:.2f}MB (max: {spec['max_file_size_mb']}MB)",
    })
    if not size_ok:
        errors.append(
            f"File too large: {size_mb:.2f}MB (max {spec['max_file_size_mb']}MB)"
        )

    # 4. PDF-specific checks
    if ext == ".pdf":
        pdf_checks = _check_pdf_properties(doc_path)
        checks.extend(pdf_checks["checks"])
        errors.extend(pdf_checks.get("errors", []))
        warnings.extend(pdf_checks.get("warnings", []))

    # 5. System-specific checks
    if system_key == "truefiling" and spec.get("bookmarks_required"):
        warnings.append(
            "TrueFiling requires PDF bookmarks for major sections — "
            "verify bookmarks are present in the final PDF"
        )

    if system_key == "truefiling" and _get_system_for_court("msc") == "truefiling":
        warnings.append(
            "MSC filings: also mail 13 paper copies to "
            "Michigan Supreme Court, P.O. Box 30052, Lansing, MI 48909"
        )

    valid = len(errors) == 0

    return {
        "valid": valid,
        "system": system_key,
        "system_name": spec["name"],
        "file": doc_path,
        "file_size_mb": round(size_mb, 2),
        "checks": checks,
        "errors": errors,
        "warnings": warnings,
        "authority": spec["authority"],
    }


def _check_pdf_properties(pdf_path: str) -> Dict:
    """Basic PDF checks (header validation, password, size)."""
    checks = []
    errors = []
    warnings = []

    try:
        with open(pdf_path, "rb") as f:
            header = f.read(1024)

        # Check PDF header
        is_pdf = header[:5] == b"%PDF-"
        checks.append({
            "check": "pdf_header",
            "status": "PASS" if is_pdf else "FAIL",
            "detail": "Valid PDF header" if is_pdf else "Not a valid PDF file",
        })
        if not is_pdf:
            errors.append("File does not have a valid PDF header")
            return {"checks": checks, "errors": errors, "warnings": warnings}

        # Check for encryption markers
        with open(pdf_path, "rb") as f:
            content = f.read(min(os.path.getsize(pdf_path), 4096))
        has_encrypt = b"/Encrypt" in content
        checks.append({
            "check": "not_encrypted",
            "status": "FAIL" if has_encrypt else "PASS",
            "detail": "Password-protected" if has_encrypt else "No encryption detected",
        })
        if has_encrypt:
            errors.append("PDF is password-protected — e-filing systems reject encrypted PDFs")

        # Check for text content (searchability heuristic)
        has_text = b"/Font" in content or b"/Type /Page" in content
        checks.append({
            "check": "text_content",
            "status": "PASS" if has_text else "WARN",
            "detail": "Text content detected" if has_text else "May be image-only PDF",
        })
        if not has_text:
            warnings.append(
                "PDF may be image-only (scanned). Text-searchable PDF "
                "required — run OCR if needed"
            )

    except Exception as e:
        errors.append(f"Cannot read PDF: {e}")
        checks.append({
            "check": "pdf_readable",
            "status": "FAIL",
            "detail": str(e),
        })

    return {"checks": checks, "errors": errors, "warnings": warnings}


def prepare_for_mifile(
    doc_path: str,
    case_number: str,
    filing_type: str,
    log_to_db: bool = True,
) -> Dict:
    """Prepare a document for MiFile e-filing.

    Args:
        doc_path: Path to the document (should be PDF).
        case_number: Case number (e.g., 2024-001507-DC).
        filing_type: Filing type key (MOTION, BRIEF, etc.).

    Returns:
        dict with preparation checklist, filing code, and validation.
    """
    # Validate the document
    validation = validate_efile_requirements(doc_path, "mifile")

    filing_key = filing_type.upper().replace(" ", "_").replace("-", "_")
    code_info = MIFILE_FILING_CODES.get(filing_key, {})

    if not code_info:
        # Try partial match
        for key, val in MIFILE_FILING_CODES.items():
            if filing_key in key or key in filing_key:
                code_info = val
                filing_key = key
                break

    checklist = [
        {"step": 1, "action": "Log into MiFile",
         "url": EFILING_SYSTEMS["mifile"]["url"],
         "status": "pending"},
        {"step": 2, "action": f"Select case: {case_number}",
         "detail": "Search by case number in MiFile",
         "status": "pending"},
        {"step": 3, "action": f"Select filing code: {code_info.get('code', filing_key)}",
         "detail": code_info.get("description", filing_type),
         "status": "pending"},
        {"step": 4, "action": f"Upload document: {os.path.basename(doc_path)}",
         "detail": f"Size: {validation.get('file_size_mb', 'N/A')}MB",
         "status": "pending"},
        {"step": 5, "action": "Verify Certificate of Service is included",
         "authority": "MCR 2.107(D)",
         "status": "pending"},
    ]

    fee = code_info.get("fee", 0)
    if fee > 0:
        checklist.append({
            "step": 6, "action": f"Pay fee: ${fee:.2f} (or attach MC 20 fee waiver)",
            "authority": "MCR 2.002",
            "status": "pending",
        })
    else:
        checklist.append({
            "step": 6, "action": "No fee required for this filing type",
            "status": "complete",
        })

    checklist.append({
        "step": 7, "action": "Review and submit filing",
        "detail": "Save confirmation number",
        "status": "pending",
    })

    # Log to DB
    if log_to_db:
        conn = _get_db()
        if conn:
            try:
                _ensure_table(conn)
                file_size = os.path.getsize(doc_path) if os.path.exists(doc_path) else 0
                v_status = "valid" if validation.get("valid") else "invalid"
                v_errors = json.dumps(validation.get("errors", []))
                conn.execute(
                    """INSERT INTO efiling_log
                       (document_name, court, case_number, efiling_system,
                        filing_code, filing_type, file_path, file_size_bytes,
                        validation_status, validation_errors)
                       VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                    (
                        os.path.basename(doc_path), "14th_circuit", case_number,
                        "mifile", code_info.get("code", ""), filing_key,
                        doc_path, file_size, v_status, v_errors,
                    ),
                )
                conn.commit()
            except Exception:
                pass
            finally:
                conn.close()

    return {
        "system": "mifile",
        "system_name": "MiFile",
        "court": "14th_circuit",
        "case_number": case_number,
        "filing_type": filing_key,
        "filing_code": code_info.get("code", "UNKNOWN"),
        "filing_description": code_info.get("description", filing_type),
        "fee": fee,
        "fee_display": f"${fee:.2f}" if fee > 0 else "No fee",
        "document": doc_path,
        "validation": validation,
        "checklist": checklist,
        "authority": code_info.get("authority", "MCR 1.109(G)"),
    }


def prepare_for_truefiling(
    doc_path: str,
    court: str = "coa",
    case_number: str = None,
    filing_type: str = "BRIEF",
) -> Dict:
    """Prepare a document for TrueFiling (COA or MSC).

    Args:
        doc_path: Path to the document.
        court: 'coa' or 'msc'.
        case_number: Case number (default from CASE_NUMBERS).
        filing_type: Filing type description.

    Returns:
        dict with preparation steps and validation.
    """
    court_key = _resolve_court(court)
    if case_number is None:
        case_number = CASE_NUMBERS.get("coa_appeal" if court_key == "coa" else "msc", "TBD")

    validation = validate_efile_requirements(doc_path, "truefiling")

    checklist = [
        {"step": 1, "action": "Log into TrueFiling",
         "url": EFILING_SYSTEMS["truefiling"]["url"],
         "status": "pending"},
        {"step": 2, "action": f"Select court: {'Court of Appeals' if court_key == 'coa' else 'Supreme Court'}",
         "status": "pending"},
        {"step": 3, "action": f"Select case: {case_number}",
         "status": "pending"},
        {"step": 4, "action": f"Upload: {os.path.basename(doc_path)}",
         "status": "pending"},
        {"step": 5, "action": "Verify PDF bookmarks are present",
         "authority": "TrueFiling requirement",
         "status": "pending"},
        {"step": 6, "action": "Select service recipients",
         "detail": "Serve all parties via TrueFiling",
         "status": "pending"},
        {"step": 7, "action": "Review and submit",
         "status": "pending"},
    ]

    if court_key == "msc":
        checklist.append({
            "step": 8,
            "action": "Mail 13 paper copies to MSC",
            "detail": ("Michigan Supreme Court, P.O. Box 30052, "
                       "Lansing, MI 48909"),
            "authority": "MCR 7.306",
            "status": "pending",
        })

    return {
        "system": "truefiling",
        "system_name": "TrueFiling",
        "court": court_key,
        "case_number": case_number,
        "filing_type": filing_type,
        "document": doc_path,
        "validation": validation,
        "checklist": checklist,
        "paper_copies_required": court_key == "msc",
        "paper_copy_count": 13 if court_key == "msc" else 0,
        "authority": EFILING_SYSTEMS["truefiling"]["authority"],
    }


def prepare_for_ecf(
    doc_path: str,
    case_number: str = None,
    filing_type: str = "COMPLAINT",
) -> Dict:
    """Prepare a document for CM/ECF (USDC Western District MI).

    Args:
        doc_path: Path to the document.
        case_number: Federal case number (if assigned).
        filing_type: Filing type.

    Returns:
        dict with preparation steps and validation.
    """
    if case_number is None:
        case_number = CASE_NUMBERS.get("usdc", "TBD")

    validation = validate_efile_requirements(doc_path, "cmecf")

    checklist = [
        {"step": 1, "action": "Register for CM/ECF account (if not done)",
         "url": EFILING_SYSTEMS["cmecf"]["url"],
         "detail": "Pro se registration may require court approval",
         "status": "pending"},
        {"step": 2, "action": "Log into CM/ECF",
         "status": "pending"},
        {"step": 3, "action": f"Select case: {case_number}",
         "status": "pending" if case_number != "TBD" else "blocked"},
        {"step": 4, "action": f"Select event code for: {filing_type}",
         "status": "pending"},
        {"step": 5, "action": f"Upload: {os.path.basename(doc_path)}",
         "status": "pending"},
        {"step": 6, "action": "Attach IFP application (AO 240) if fee waiver needed",
         "authority": "28 U.S.C. § 1915",
         "status": "pending"},
        {"step": 7, "action": "Review docket entry and submit",
         "status": "pending"},
    ]

    return {
        "system": "cmecf",
        "system_name": "CM/ECF (PACER)",
        "court": "usdc_wdmi",
        "case_number": case_number,
        "filing_type": filing_type,
        "document": doc_path,
        "validation": validation,
        "checklist": checklist,
        "registration_required": True,
        "ifp_form": "AO 240",
        "authority": EFILING_SYSTEMS["cmecf"]["authority"],
    }


def generate_efile_checklist(court: str = "14th_circuit") -> Dict:
    """Generate a comprehensive e-filing checklist for a given court.

    Args:
        court: Court key.

    Returns:
        dict with pre-filing, filing, and post-filing steps.
    """
    court_key = _resolve_court(court)
    system_key = _get_system_for_court(court_key)

    if system_key is None:
        return {
            "error": f"No e-filing system mapped for court: {court}",
            "valid_courts": ["14th_circuit", "coa", "msc", "usdc_wdmi"],
        }

    spec = EFILING_SYSTEMS[system_key]

    pre_filing = [
        {"item": f"Document in {spec['file_format']} format", "required": True},
        {"item": f"File size under {spec['max_file_size_mb']}MB", "required": True},
        {"item": "PDF is text-searchable (not image-only)", "required": spec.get("text_searchable_required", True)},
        {"item": "No password protection on PDF", "required": True},
        {"item": "Caption with correct case number", "required": True},
        {"item": "Certificate of Service included", "required": True},
        {"item": "All pages numbered", "required": True},
        {"item": "Document proofread for errors", "required": True},
    ]

    if spec.get("bookmarks_required"):
        pre_filing.append({"item": "PDF bookmarks for major sections", "required": True})

    filing_steps = [
        {"item": f"Log into {spec['name']}", "url": spec.get("url", "")},
        {"item": f"Navigate to case", "detail": "Search by case number"},
        {"item": "Select correct filing code / event type", "required": True},
        {"item": "Upload document(s)", "required": True},
        {"item": "Pay fee or attach fee waiver", "required": True},
        {"item": "Select service recipients", "required": True},
        {"item": "Review filing summary", "required": True},
        {"item": "Submit filing", "required": True},
    ]

    post_filing = [
        {"item": "Save confirmation number / receipt", "required": True},
        {"item": "Download filing confirmation PDF", "required": True},
        {"item": "Verify filing appears on docket", "required": True},
        {"item": "Confirm service was completed", "required": True},
    ]

    if system_key == "truefiling" and court_key == "msc":
        post_filing.append({
            "item": "Mail 13 paper copies to MSC",
            "detail": "Michigan Supreme Court, P.O. Box 30052, Lansing, MI 48909",
            "required": True,
        })

    return {
        "court": court_key,
        "system": system_key,
        "system_name": spec["name"],
        "url": spec.get("url", ""),
        "pre_filing": pre_filing,
        "filing_steps": filing_steps,
        "post_filing": post_filing,
        "total_steps": len(pre_filing) + len(filing_steps) + len(post_filing),
        "authority": spec["authority"],
        "generated_at": datetime.now().isoformat(),
    }


# ── CLI ─────────────────────────────────────────────────────────────────────

def main() -> int:
    """CLI entry point for testing."""
    print("=" * 60)
    print("ENGINE 15: E-FILING PREPARER")
    print("MiFile / TrueFiling / CM/ECF Preparation")
    print("=" * 60)

    # Create a test PDF for validation
    test_dir = os.path.join(os.path.dirname(__file__), "__test_tmp__")
    os.makedirs(test_dir, exist_ok=True)
    test_pdf = os.path.join(test_dir, "test_motion.pdf")
    test_txt = os.path.join(test_dir, "test_motion.txt")

    # Write a minimal valid PDF
    with open(test_pdf, "wb") as f:
        f.write(b"%PDF-1.4\n")
        f.write(b"1 0 obj\n<< /Type /Catalog /Pages 2 0 R >>\nendobj\n")
        f.write(b"2 0 obj\n<< /Type /Pages /Kids [3 0 R] /Count 1 >>\nendobj\n")
        f.write(b"3 0 obj\n<< /Type /Page /Parent 2 0 R /Font << >> >>\nendobj\n")
        f.write(b"%%EOF\n")

    # Write a test text file (wrong format for e-filing)
    with open(test_txt, "w", encoding="utf-8") as f:
        f.write("This is a test motion document.\n")

    # Test 1: Validate PDF for MiFile
    print("\n--- Validate: MiFile (PDF) ---")
    result = validate_efile_requirements(test_pdf, "mifile")
    print(f"  Valid: {result['valid']}")
    print(f"  System: {result['system_name']}")
    for c in result["checks"]:
        icon = "✓" if c["status"] == "PASS" else ("⚠" if c["status"] == "WARN" else "✗")
        print(f"    {icon} {c['check']}: {c['status']} — {c.get('detail', '')}")
    if result["warnings"]:
        for w in result["warnings"]:
            print(f"    ⚠ {w}")

    # Test 2: Validate wrong format
    print("\n--- Validate: MiFile (TXT — should fail) ---")
    result2 = validate_efile_requirements(test_txt, "mifile")
    print(f"  Valid: {result2['valid']}")
    assert not result2["valid"], "TXT should not be valid for MiFile"
    for e in result2["errors"]:
        print(f"    ✗ {e}")

    # Test 3: Validate non-existent file
    print("\n--- Validate: Non-existent file ---")
    result3 = validate_efile_requirements("C:\\fake\\nonexistent.pdf", "mifile")
    print(f"  Valid: {result3['valid']}")
    assert not result3["valid"], "Non-existent file should be invalid"

    # Test 4: Prepare for MiFile
    print("\n--- Prepare: MiFile Motion ---")
    prep = prepare_for_mifile(
        test_pdf, "2024-001507-DC", "MOTION", log_to_db=False
    )
    print(f"  System: {prep['system_name']}")
    print(f"  Filing code: {prep['filing_code']}")
    print(f"  Fee: {prep['fee_display']}")
    print(f"  Steps: {len(prep['checklist'])}")
    for step in prep["checklist"][:4]:
        print(f"    Step {step['step']}: {step['action']}")

    # Test 5: Prepare for TrueFiling (COA)
    print("\n--- Prepare: TrueFiling (COA Brief) ---")
    tf_result = prepare_for_truefiling(test_pdf, "coa", "366810", "APPELLANT_BRIEF")
    print(f"  System: {tf_result['system_name']}")
    print(f"  Case: {tf_result['case_number']}")
    print(f"  Paper copies: {tf_result['paper_copy_count']}")

    # Test 6: Prepare for TrueFiling (MSC)
    print("\n--- Prepare: TrueFiling (MSC) ---")
    tf_msc = prepare_for_truefiling(test_pdf, "msc", filing_type="SUPERINTENDING_CONTROL")
    print(f"  Paper copies required: {tf_msc['paper_copies_required']}")
    print(f"  Paper copy count: {tf_msc['paper_copy_count']}")
    assert tf_msc["paper_copies_required"], "MSC should require paper copies"
    assert tf_msc["paper_copy_count"] == 13, "MSC should require 13 copies"

    # Test 7: Prepare for CM/ECF
    print("\n--- Prepare: CM/ECF (USDC) ---")
    ecf = prepare_for_ecf(test_pdf, filing_type="COMPLAINT")
    print(f"  System: {ecf['system_name']}")
    print(f"  Registration required: {ecf['registration_required']}")
    print(f"  IFP form: {ecf['ifp_form']}")

    # Test 8: E-filing checklist
    print("\n--- E-Filing Checklist: 14th Circuit ---")
    cl = generate_efile_checklist("14th_circuit")
    print(f"  System: {cl['system_name']}")
    print(f"  Total steps: {cl['total_steps']}")
    print(f"  Pre-filing: {len(cl['pre_filing'])} items")
    print(f"  Filing: {len(cl['filing_steps'])} steps")
    print(f"  Post-filing: {len(cl['post_filing'])} items")

    print("\n--- E-Filing Checklist: MSC ---")
    cl_msc = generate_efile_checklist("msc")
    print(f"  System: {cl_msc['system_name']}")
    has_paper = any("paper copies" in s.get("item", "").lower() for s in cl_msc["post_filing"])
    print(f"  Paper copies step included: {has_paper}")
    assert has_paper, "MSC checklist should include paper copies step"

    # Test 9: MiFile filing codes
    print("\n--- MiFile Filing Codes ---")
    for code_key, info in list(MIFILE_FILING_CODES.items())[:6]:
        fee = info["fee"]
        print(f"  {code_key}: code={info['code']}, fee=${fee:.2f}")

    # Test 10: All e-filing systems
    print("\n--- E-Filing Systems ---")
    for sys_key, spec in EFILING_SYSTEMS.items():
        print(f"  {sys_key}: {spec['name']} — max {spec['max_file_size_mb']}MB")

    # Cleanup test files
    try:
        os.remove(test_pdf)
        os.remove(test_txt)
        os.rmdir(test_dir)
    except OSError:
        pass

    print("\n[efiling_preparer] All tests passed. ✓")
    return 0


if __name__ == "__main__":
    sys.exit(main())
