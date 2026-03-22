"""Filing Wizard models — state, package, and QA result types.

Pydantic v2 models used by the Filing Wizard screen to track wizard
state across steps, describe a filing package, and capture QA results.
"""

from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import List, Optional

from pydantic import BaseModel, ConfigDict, Field


# ---------------------------------------------------------------------------
# Enums
# ---------------------------------------------------------------------------

class CourtType(str, Enum):
    """Courts available in the filing wizard."""

    CIRCUIT_FAMILY = "14th Circuit Family"
    CIRCUIT_CIVIL = "14th Circuit Civil"
    DISTRICT_60 = "60th District"
    COA = "Court of Appeals (COA)"
    MSC = "Michigan Supreme Court (MSC)"
    USDC_WDMI = "USDC Western District of MI"
    JTC = "Judicial Tenure Commission (JTC)"
    AGC = "Attorney Grievance Commission (AGC)"


class FilingType(str, Enum):
    """Filing types supported by the wizard."""

    MOTION = "Motion"
    RESPONSE = "Response"
    BRIEF = "Brief"
    APPLICATION = "Application"
    COMPLAINT = "Complaint"
    AFFIDAVIT = "Affidavit"
    EXHIBIT_PACKAGE = "Exhibit Package"
    PROPOSED_ORDER = "Proposed Order"
    CERT_OF_SERVICE = "Certificate of Service"


class Lane(str, Enum):
    """Six case lanes — IRON LAW: never cross-contaminate."""

    A_CUSTODY = "A"
    B_HOUSING = "B"
    C_CONVERGENCE = "C"
    D_PPO = "D"
    E_MISCONDUCT = "E"
    F_APPELLATE = "F"


class QAStatus(str, Enum):
    """QA check result status."""

    PASS = "pass"
    FAIL = "fail"
    WARN = "warn"
    SKIP = "skip"


# ---------------------------------------------------------------------------
# Court metadata
# ---------------------------------------------------------------------------

class CourtInfo(BaseModel):
    """Metadata for a court selection."""

    court_type: CourtType
    case_number: str = ""
    lane: Lane = Lane.A_CUSTODY
    formatting_notes: str = ""
    rule_set: str = "MCR"  # MCR, FRCP, JTC Rules, etc.

    model_config = ConfigDict(from_attributes=True)


# ---------------------------------------------------------------------------
# Filing components
# ---------------------------------------------------------------------------

FILING_COMPONENTS: dict[str, list[str]] = {
    FilingType.MOTION: [
        "Motion document",
        "Supporting affidavit",
        "Proposed order",
        "Certificate of service",
    ],
    FilingType.RESPONSE: [
        "Response brief",
        "Supporting affidavit (if needed)",
        "Certificate of service",
    ],
    FilingType.BRIEF: [
        "Brief on the merits",
        "Table of contents",
        "Table of authorities",
        "Certificate of service",
    ],
    FilingType.APPLICATION: [
        "Application document",
        "Supporting affidavit",
        "Proposed order",
        "Certificate of service",
    ],
    FilingType.COMPLAINT: [
        "Complaint document",
        "Summons",
        "Civil case cover sheet",
        "Filing fee or fee waiver",
    ],
    FilingType.AFFIDAVIT: [
        "Affidavit document",
        "Exhibit list",
        "Certificate of service",
    ],
    FilingType.EXHIBIT_PACKAGE: [
        "Exhibit index",
        "Individual exhibits (Bates-stamped)",
        "Certificate of service",
    ],
    FilingType.PROPOSED_ORDER: [
        "Proposed order",
        "Certificate of service",
    ],
    FilingType.CERT_OF_SERVICE: [
        "Certificate of service",
    ],
}


FILING_RULES: dict[str, str] = {
    FilingType.MOTION: "MCR 2.119 — Motion Practice",
    FilingType.RESPONSE: "MCR 2.119(C)(1) — Response within 21 days",
    FilingType.BRIEF: "MCR 7.212 — Briefs (COA) / MCR 7.312 (MSC)",
    FilingType.APPLICATION: "MCR 7.305 — Application for Leave to Appeal",
    FilingType.COMPLAINT: "MCR 2.110 — Commencement of Actions",
    FilingType.AFFIDAVIT: "MCR 2.119(B) — Affidavit in Support",
    FilingType.EXHIBIT_PACKAGE: "MRE 901-902 — Authentication",
    FilingType.PROPOSED_ORDER: "MCR 2.602 — Entry of Judgments and Orders",
    FilingType.CERT_OF_SERVICE: "MCR 2.107 — Service of Pleadings",
}


# ---------------------------------------------------------------------------
# Court → case number / lane mapping
# ---------------------------------------------------------------------------

COURT_DEFAULTS: dict[str, CourtInfo] = {
    CourtType.CIRCUIT_FAMILY: CourtInfo(
        court_type=CourtType.CIRCUIT_FAMILY,
        case_number="2024-001507-DC",
        lane=Lane.A_CUSTODY,
        formatting_notes="Muskegon County 14th Circuit — Family Division\n"
                         "E-file via MiFILE. Double-spaced, 1-inch margins.\n"
                         "Child referred to by initials only (MCR 8.119(H)).",
        rule_set="MCR",
    ),
    CourtType.CIRCUIT_CIVIL: CourtInfo(
        court_type=CourtType.CIRCUIT_CIVIL,
        case_number="2025-002760-CZ",
        lane=Lane.B_HOUSING,
        formatting_notes="Muskegon County 14th Circuit — Civil Division\n"
                         "E-file via MiFILE. Standard civil formatting.",
        rule_set="MCR",
    ),
    CourtType.DISTRICT_60: CourtInfo(
        court_type=CourtType.DISTRICT_60,
        case_number="",
        lane=Lane.A_CUSTODY,
        formatting_notes="60th District Court — Muskegon County\n"
                         "Check local administrative orders for filing requirements.",
        rule_set="MCR",
    ),
    CourtType.COA: CourtInfo(
        court_type=CourtType.COA,
        case_number="366810",
        lane=Lane.F_APPELLATE,
        formatting_notes="Michigan Court of Appeals\n"
                         "E-file via MiFILE. 50-page limit for briefs.\n"
                         "Table of contents and table of authorities required.",
        rule_set="MCR",
    ),
    CourtType.MSC: CourtInfo(
        court_type=CourtType.MSC,
        case_number="",
        lane=Lane.F_APPELLATE,
        formatting_notes="Michigan Supreme Court\n"
                         "E-file via MiFILE. Application for leave to appeal.\n"
                         "MCR 7.305 requirements apply.",
        rule_set="MCR",
    ),
    CourtType.USDC_WDMI: CourtInfo(
        court_type=CourtType.USDC_WDMI,
        case_number="",
        lane=Lane.A_CUSTODY,
        formatting_notes="U.S. District Court — Western District of Michigan\n"
                         "CM/ECF e-filing. FRCP formatting rules apply.\n"
                         "§1983 civil rights actions.",
        rule_set="FRCP",
    ),
    CourtType.JTC: CourtInfo(
        court_type=CourtType.JTC,
        case_number="",
        lane=Lane.E_MISCONDUCT,
        formatting_notes="Judicial Tenure Commission\n"
                         "File complaint per JTC rules. No fee required.\n"
                         "Detailed factual basis for misconduct required.",
        rule_set="JTC Rules",
    ),
    CourtType.AGC: CourtInfo(
        court_type=CourtType.AGC,
        case_number="",
        lane=Lane.E_MISCONDUCT,
        formatting_notes="Attorney Grievance Commission\n"
                         "Request for investigation form.\n"
                         "Document specific MRPC violations.",
        rule_set="MRPC",
    ),
}

# ---------------------------------------------------------------------------
# Lane → PPO case number
# ---------------------------------------------------------------------------

LANE_CASE_NUMBERS: dict[str, str] = {
    Lane.A_CUSTODY: "2024-001507-DC",
    Lane.B_HOUSING: "2025-002760-CZ",
    Lane.D_PPO: "2023-5907-PP",
    Lane.E_MISCONDUCT: "2024-001507-DC",
    Lane.F_APPELLATE: "366810",
}


# ---------------------------------------------------------------------------
# Exhibit item
# ---------------------------------------------------------------------------

class ExhibitItem(BaseModel):
    """A single exhibit available for inclusion in a filing."""

    id: int
    title: str
    bates_number: Optional[str] = None
    file_path: Optional[str] = None
    file_type: Optional[str] = None
    relevance_score: Optional[float] = None
    source: Optional[str] = None
    selected: bool = False

    model_config = ConfigDict(from_attributes=True)


# ---------------------------------------------------------------------------
# QA result
# ---------------------------------------------------------------------------

class QACheckResult(BaseModel):
    """Result of a single QA pre-flight check."""

    check_name: str
    status: QAStatus = QAStatus.SKIP
    message: str = ""

    model_config = ConfigDict(from_attributes=True)


# ---------------------------------------------------------------------------
# Filing package
# ---------------------------------------------------------------------------

class FilingPackage(BaseModel):
    """Describes a complete filing package assembled by the wizard."""

    court: Optional[CourtType] = None
    case_number: str = ""
    lane: Optional[Lane] = None
    filing_type: Optional[FilingType] = None
    title: str = ""
    exhibits: List[ExhibitItem] = Field(default_factory=list)
    qa_results: List[QACheckResult] = Field(default_factory=list)
    qa_pass: bool = False
    output_path: Optional[str] = None
    created_at: Optional[datetime] = Field(default_factory=datetime.now)
    notes: str = ""

    model_config = ConfigDict(from_attributes=True)


# ---------------------------------------------------------------------------
# Wizard state
# ---------------------------------------------------------------------------

class FilingWizardState(BaseModel):
    """Tracks the current state of the filing wizard across all steps."""

    current_step: int = 0
    total_steps: int = 6
    court_info: Optional[CourtInfo] = None
    filing_type: Optional[FilingType] = None
    exhibits: List[ExhibitItem] = Field(default_factory=list)
    qa_results: List[QACheckResult] = Field(default_factory=list)
    package: FilingPackage = Field(default_factory=FilingPackage)
    is_complete: bool = False

    model_config = ConfigDict(from_attributes=True)
