"""COA Appendix & Record Preparation Engine — MCR 7.212(H) / 7.210.

Builds and validates Michigan Court of Appeals appendix manifests and
record-on-appeal checklists for *Pigors v Watson*, COA Case 366810.

MCR 7.212(H) governs what must appear in the appendix bound with the
appellant's brief.  MCR 7.210 governs the lower-court record that the
trial-court clerk certifies and transmits to the COA.

This engine:
* assembles an ordered appendix manifest with Bates-range tracking,
* validates that every *required* item under MCR 7.212(H) is present,
* generates a printable index page for the appendix,
* computes transcript-ordering deadlines under MCR 7.210,
* produces a record-on-appeal checklist by case type.

Usage::

    from litigationos.engines.coa_appendix import (
        COAAppendixEngine,
        build_appendix_manifest,
        check_required_items,
        generate_appendix_index,
        get_transcript_requirements,
        calculate_transcript_deadlines,
        get_record_checklist,
    )

    items = [
        {"title": "Register of Actions", "category": "REQUIRED",
         "source_path": "exhibits/register.pdf", "page_count": 4},
    ]
    manifest = build_appendix_manifest(items)
    missing = check_required_items(manifest)
    index_text = generate_appendix_index(manifest)
"""

from __future__ import annotations

import logging
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Optional

from pydantic import BaseModel, ConfigDict, Field

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Constants — case identifiers
# ---------------------------------------------------------------------------

_COA_CASE_NUMBER = "366810"
_LOWER_COURT = "14th Circuit Court"
_LOWER_COUNTY = "Muskegon County"
_LOWER_CASE = "2024-001507-DC"

# ---------------------------------------------------------------------------
# MCR 7.212(H) — Required appendix items
# ---------------------------------------------------------------------------

_MCR_7212H_REQUIRED: list[dict[str, str]] = [
    {
        "id": "register_of_actions",
        "label": "Register of Actions",
        "mcr": "MCR 7.212(H)(1)",
        "description": (
            "Complete register of actions from the lower court showing "
            "all filings, orders, and proceedings."
        ),
    },
    {
        "id": "relevant_docket_entries",
        "label": "Relevant Docket Entries",
        "mcr": "MCR 7.212(H)(2)",
        "description": (
            "Docket entries relevant to the issues on appeal, including "
            "dates of filing, hearing, and entry of orders."
        ),
    },
    {
        "id": "judgment_order_appealed",
        "label": "Judgment or Order Appealed From",
        "mcr": "MCR 7.212(H)(3)",
        "description": (
            "The judgment, order, or ruling from which the appeal is "
            "taken, exactly as entered by the lower court."
        ),
    },
    {
        "id": "opinion_findings",
        "label": "Opinion, Findings, or Report of Lower Court",
        "mcr": "MCR 7.212(H)(4)",
        "description": (
            "Any written opinion, findings of fact, conclusions of law, "
            "or recommendation issued by the trial court or referee."
        ),
    },
    {
        "id": "relevant_transcript_portions",
        "label": "Relevant Portions of Transcript",
        "mcr": "MCR 7.212(H)(5)",
        "description": (
            "Portions of hearing or trial transcripts that are relevant "
            "to the issues raised on appeal."
        ),
    },
    {
        "id": "other_relevant_documents",
        "label": "Other Relevant Lower Court Documents",
        "mcr": "MCR 7.212(H)(6)",
        "description": (
            "Any other documents from the lower-court file that are "
            "necessary for resolution of the issues on appeal."
        ),
    },
]

# ---------------------------------------------------------------------------
# MCR 7.210 — Record on appeal requirements
# ---------------------------------------------------------------------------

_MCR_7210_RECORD: list[dict[str, str]] = [
    {
        "id": "lower_court_file",
        "label": "Lower Court File (Certified by Clerk)",
        "mcr": "MCR 7.210(A)(1)",
        "description": (
            "The original lower-court file, including all documents, "
            "exhibits, and papers filed with the clerk."
        ),
    },
    {
        "id": "transcript_proceedings",
        "label": "Transcript of Proceedings",
        "mcr": "MCR 7.210(A)(2)",
        "description": (
            "The transcript of testimony and other proceedings in the "
            "trial court or tribunal, as ordered by the appellant."
        ),
    },
    {
        "id": "exhibits",
        "label": "Exhibits Admitted or Offered",
        "mcr": "MCR 7.210(A)(3)",
        "description": (
            "All exhibits that were admitted into evidence or offered "
            "and refused, unless returned to parties by court order."
        ),
    },
    {
        "id": "certified_copy_docket",
        "label": "Certified Copy of Docket Entries",
        "mcr": "MCR 7.210(A)(4)",
        "description": (
            "A certified copy of the register of actions or docket "
            "entries from the trial court clerk."
        ),
    },
]

# Transcript ordering rules
_TRANSCRIPT_RULES: dict[str, Any] = {
    "mcr": "MCR 7.210(B)",
    "order_deadline_days": 14,
    "order_deadline_description": (
        "Within 14 days after filing the claim of appeal, the "
        "appellant must order the full transcript or identified "
        "portions from the court reporter or recorder."
    ),
    "filing_deadline_days": 56,
    "filing_deadline_description": (
        "The transcript must be filed with the trial court clerk "
        "within 56 days after the claim of appeal is filed, unless "
        "extended by the Court of Appeals."
    ),
    "notice_requirement": (
        "Appellant must serve on the court reporter/recorder and all "
        "other parties a copy of the transcript order or a statement "
        "that no transcript will be ordered."
    ),
    "settled_statement": {
        "mcr": "MCR 7.210(B)(3)",
        "description": (
            "If no transcript is available (e.g., reporter unavailable "
            "or proceedings not recorded), the appellant may prepare "
            "a settled statement of facts from the best available "
            "sources, including recollection of counsel and the court."
        ),
        "procedure": [
            "Appellant prepares proposed statement of facts.",
            "Appellant serves statement on all other parties.",
            "Other parties have 14 days to propose amendments.",
            "If parties cannot agree, the trial court settles the statement.",
            "Settled statement is included in the record on appeal.",
        ],
    },
}

# ---------------------------------------------------------------------------
# Appendix item categories
# ---------------------------------------------------------------------------


class AppendixCategory(str, Enum):
    """Classification of appendix items by necessity level."""

    REQUIRED = "REQUIRED"
    RECOMMENDED = "RECOMMENDED"
    SUPPLEMENTAL = "SUPPLEMENTAL"


# ---------------------------------------------------------------------------
# Pydantic models
# ---------------------------------------------------------------------------


class AppendixItem(BaseModel):
    """A single item in the COA appendix.

    Parameters
    ----------
    title : str
        Descriptive title of the appendix item.
    source_path : str | None
        Filesystem path to the source document (local-only).
    bates_range : str | None
        Bates-stamp range for the item (e.g. ``"APP-001 to APP-012"``).
    page_count : int
        Number of pages this item occupies.
    category : AppendixCategory
        Whether the item is REQUIRED, RECOMMENDED, or SUPPLEMENTAL.
    is_required : bool
        ``True`` when MCR 7.212(H) mandates this item.
    mcr_reference : str | None
        Court-rule citation governing this item.
    description : str | None
        Explanatory note or contents summary.
    included : bool
        Whether the item has been located and included.
    """

    title: str
    source_path: Optional[str] = None
    bates_range: Optional[str] = None
    page_count: int = 0
    category: AppendixCategory = AppendixCategory.REQUIRED
    is_required: bool = True
    mcr_reference: Optional[str] = None
    description: Optional[str] = None
    included: bool = False

    model_config = ConfigDict(from_attributes=True)


class AppendixManifest(BaseModel):
    """Complete appendix manifest with compliance status.

    Parameters
    ----------
    items : list[AppendixItem]
        Ordered list of appendix items.
    total_pages : int
        Sum of all item page counts.
    compliance_status : str
        ``"COMPLIANT"`` when all required items are present, else
        ``"NON-COMPLIANT"``.
    missing_required : list[str]
        Titles of required items that are absent.
    case_number : str
        COA docket number.
    lower_case_number : str
        Trial-court case number.
    generated_at : datetime
        Timestamp when manifest was built.
    """

    items: list[AppendixItem] = Field(default_factory=list)
    total_pages: int = 0
    compliance_status: str = "NON-COMPLIANT"
    missing_required: list[str] = Field(default_factory=list)
    case_number: str = _COA_CASE_NUMBER
    lower_case_number: str = _LOWER_CASE
    generated_at: datetime = Field(default_factory=datetime.now)

    model_config = ConfigDict(from_attributes=True)


class TranscriptOrder(BaseModel):
    """Tracks a transcript order under MCR 7.210(B).

    Parameters
    ----------
    hearing_date : str
        Date of the hearing whose transcript is ordered.
    court_reporter : str | None
        Name of the court reporter or recording service.
    status : str
        Current status: ``PENDING``, ``ORDERED``, ``RECEIVED``,
        ``FILED``, ``UNAVAILABLE``.
    ordered_date : str | None
        ISO-format date when the transcript was ordered.
    due_date : str | None
        ISO-format deadline for filing the transcript.
    notes : str | None
        Additional context (e.g. settled-statement note).
    """

    hearing_date: str
    court_reporter: Optional[str] = None
    status: str = "PENDING"
    ordered_date: Optional[str] = None
    due_date: Optional[str] = None
    notes: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)


# ---------------------------------------------------------------------------
# Engine class
# ---------------------------------------------------------------------------


class COAAppendixEngine:
    """Builds and validates COA appendix manifests per MCR 7.212(H)/7.210.

    Parameters
    ----------
    case_number : str
        COA docket number (default ``366810``).
    lower_case : str
        Lower-court case number (default ``2024-001507-DC``).
    """

    def __init__(
        self,
        case_number: str = _COA_CASE_NUMBER,
        lower_case: str = _LOWER_CASE,
    ) -> None:
        self.case_number = case_number
        self.lower_case = lower_case

    # -- public API ---------------------------------------------------------

    def build_manifest(self, items: list[dict[str, Any]]) -> AppendixManifest:
        """Build an :class:`AppendixManifest` from raw item dicts.

        Each dict should contain at minimum ``title`` and ``category``.
        Optional keys: ``source_path``, ``bates_range``, ``page_count``,
        ``is_required``, ``mcr_reference``, ``description``, ``included``.

        Returns
        -------
        AppendixManifest
            Validated manifest with compliance status computed.
        """
        parsed: list[AppendixItem] = []
        for raw in items:
            cat_val = raw.get("category", "REQUIRED")
            if isinstance(cat_val, str):
                cat_val = AppendixCategory(cat_val.upper())
            is_req = raw.get(
                "is_required", cat_val == AppendixCategory.REQUIRED
            )
            item = AppendixItem(
                title=raw.get("title", "Untitled"),
                source_path=raw.get("source_path"),
                bates_range=raw.get("bates_range"),
                page_count=raw.get("page_count", 0),
                category=cat_val,
                is_required=is_req,
                mcr_reference=raw.get("mcr_reference"),
                description=raw.get("description"),
                included=raw.get("included", raw.get("source_path") is not None),
            )
            parsed.append(item)

        total = sum(i.page_count for i in parsed)
        missing = self._find_missing_required(parsed)
        status = "COMPLIANT" if not missing else "NON-COMPLIANT"

        manifest = AppendixManifest(
            items=parsed,
            total_pages=total,
            compliance_status=status,
            missing_required=missing,
            case_number=self.case_number,
            lower_case_number=self.lower_case,
        )
        logger.info(
            "Appendix manifest built: %d items, %d pages, status=%s",
            len(parsed),
            total,
            status,
        )
        return manifest

    def check_required(self, manifest: AppendixManifest) -> list[dict[str, str]]:
        """Return details on each missing required item.

        Returns
        -------
        list[dict]
            Each dict has ``id``, ``label``, ``mcr``, and ``description``.
        """
        included_titles = {
            i.title.lower().strip()
            for i in manifest.items
            if i.included
        }
        results: list[dict[str, str]] = []
        for req in _MCR_7212H_REQUIRED:
            if req["label"].lower().strip() not in included_titles:
                results.append(req)
        return results

    def generate_index(self, manifest: AppendixManifest) -> str:
        """Produce a formatted index page for the appendix.

        Returns
        -------
        str
            Plain-text index suitable for inclusion as the appendix
            cover/index page.
        """
        lines: list[str] = [
            "APPENDIX — INDEX",
            f"COA Case No. {manifest.case_number}",
            f"Lower Court Case No. {manifest.lower_case_number}",
            f"Lower Court: {_LOWER_COURT}, {_LOWER_COUNTY}",
            "",
            f"Generated: {manifest.generated_at:%B %d, %Y}",
            "",
            "-" * 72,
            f"{'No.':<6}{'Document':<42}{'Pages':<8}{'Bates Range':<16}",
            "-" * 72,
        ]
        for idx, item in enumerate(manifest.items, start=1):
            bates = item.bates_range or "—"
            pages = str(item.page_count) if item.page_count else "—"
            lines.append(
                f"{idx:<6}{item.title[:41]:<42}{pages:<8}{bates:<16}"
            )
        lines.append("-" * 72)
        lines.append(f"Total Pages: {manifest.total_pages}")
        lines.append(f"Compliance: {manifest.compliance_status}")
        if manifest.missing_required:
            lines.append("")
            lines.append("MISSING REQUIRED ITEMS:")
            for m in manifest.missing_required:
                lines.append(f"  • {m}")
        return "\n".join(lines)

    def get_record_checklist(self, case_type: str = "domestic") -> list[dict[str, Any]]:
        """Return a record-on-appeal checklist for the given case type.

        Parameters
        ----------
        case_type : str
            One of ``"domestic"``, ``"civil"``, ``"criminal"``,
            ``"administrative"``.  Defaults to ``"domestic"`` (family).

        Returns
        -------
        list[dict]
            Each dict has ``item``, ``mcr``, ``required``, ``notes``.
        """
        base: list[dict[str, Any]] = [
            {
                "item": r["label"],
                "mcr": r["mcr"],
                "required": True,
                "notes": r["description"],
            }
            for r in _MCR_7210_RECORD
        ]

        # MCR 7.212(H) appendix items
        for req in _MCR_7212H_REQUIRED:
            base.append(
                {
                    "item": f"Appendix: {req['label']}",
                    "mcr": req["mcr"],
                    "required": True,
                    "notes": req["description"],
                }
            )

        # Case-type-specific additions
        _extra = _case_type_extras(case_type)
        base.extend(_extra)

        return base

    # -- private helpers ----------------------------------------------------

    def _find_missing_required(self, items: list[AppendixItem]) -> list[str]:
        """Compare included items against MCR 7.212(H) required list."""
        included = {i.title.lower().strip() for i in items if i.included}
        missing: list[str] = []
        for req in _MCR_7212H_REQUIRED:
            if req["label"].lower().strip() not in included:
                missing.append(req["label"])
        return missing


# ---------------------------------------------------------------------------
# Module-level convenience functions
# ---------------------------------------------------------------------------


def build_appendix_manifest(
    items: list[dict[str, Any]],
    case_number: str = _COA_CASE_NUMBER,
    lower_case: str = _LOWER_CASE,
) -> AppendixManifest:
    """Build an appendix manifest (convenience wrapper).

    Parameters
    ----------
    items : list[dict]
        Raw item dicts — see :meth:`COAAppendixEngine.build_manifest`.
    case_number : str
        COA docket number.
    lower_case : str
        Lower-court case number.

    Returns
    -------
    AppendixManifest
    """
    engine = COAAppendixEngine(case_number=case_number, lower_case=lower_case)
    return engine.build_manifest(items)


def check_required_items(manifest: AppendixManifest) -> list[dict[str, str]]:
    """Return missing required items (convenience wrapper).

    Returns
    -------
    list[dict]
        Each dict describes a missing MCR 7.212(H) required item.
    """
    engine = COAAppendixEngine(
        case_number=manifest.case_number,
        lower_case=manifest.lower_case_number,
    )
    return engine.check_required(manifest)


def generate_appendix_index(manifest: AppendixManifest) -> str:
    """Generate a formatted appendix index page (convenience wrapper).

    Returns
    -------
    str
        Plain-text index page.
    """
    engine = COAAppendixEngine(
        case_number=manifest.case_number,
        lower_case=manifest.lower_case_number,
    )
    return engine.generate_index(manifest)


def get_transcript_requirements() -> dict[str, Any]:
    """Return MCR 7.210(B) transcript ordering rules.

    Returns
    -------
    dict
        Keys: ``mcr``, ``order_deadline_days``, ``filing_deadline_days``,
        ``notice_requirement``, ``settled_statement``, and descriptions.
    """
    return dict(_TRANSCRIPT_RULES)


def calculate_transcript_deadlines(claim_date: str) -> dict[str, Any]:
    """Compute transcript deadlines from a claim-of-appeal filing date.

    Parameters
    ----------
    claim_date : str
        ISO-format date (``YYYY-MM-DD``) of the claim of appeal filing.

    Returns
    -------
    dict
        ``order_deadline``, ``filing_deadline`` (ISO strings), and
        ``rules`` summary.
    """
    try:
        base = datetime.strptime(claim_date, "%Y-%m-%d")
    except ValueError:
        base = datetime.strptime(claim_date, "%m/%d/%Y")

    order_days = _TRANSCRIPT_RULES["order_deadline_days"]
    filing_days = _TRANSCRIPT_RULES["filing_deadline_days"]

    order_dl = base + timedelta(days=order_days)
    filing_dl = base + timedelta(days=filing_days)

    return {
        "claim_of_appeal_date": base.strftime("%Y-%m-%d"),
        "order_deadline": order_dl.strftime("%Y-%m-%d"),
        "order_deadline_days": order_days,
        "order_deadline_description": _TRANSCRIPT_RULES[
            "order_deadline_description"
        ],
        "filing_deadline": filing_dl.strftime("%Y-%m-%d"),
        "filing_deadline_days": filing_days,
        "filing_deadline_description": _TRANSCRIPT_RULES[
            "filing_deadline_description"
        ],
        "settled_statement_procedure": _TRANSCRIPT_RULES[
            "settled_statement"
        ]["procedure"],
    }


def get_record_checklist(case_type: str = "domestic") -> list[dict[str, Any]]:
    """Return a record-on-appeal checklist (convenience wrapper).

    Parameters
    ----------
    case_type : str
        ``"domestic"``, ``"civil"``, ``"criminal"``, or
        ``"administrative"``.

    Returns
    -------
    list[dict]
    """
    engine = COAAppendixEngine()
    return engine.get_record_checklist(case_type=case_type)


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------


def _case_type_extras(case_type: str) -> list[dict[str, Any]]:
    """Return case-type-specific checklist items."""
    case_type = case_type.lower().strip()
    extras: list[dict[str, Any]] = []

    if case_type in ("domestic", "family"):
        extras.extend(
            [
                {
                    "item": "Friend of the Court Report/Recommendation",
                    "mcr": "MCR 3.218",
                    "required": False,
                    "notes": (
                        "Include any FOC recommendation or report that was "
                        "before the court when the appealed order was entered."
                    ),
                },
                {
                    "item": "Custody/Parenting-Time Order",
                    "mcr": "MCL 722.27a",
                    "required": True,
                    "notes": (
                        "The custody or parenting-time order that is the "
                        "subject of the appeal."
                    ),
                },
                {
                    "item": "Child Support Order",
                    "mcr": "MCL 552.517",
                    "required": False,
                    "notes": "If child support is at issue on appeal.",
                },
                {
                    "item": "PPO or Protective Order",
                    "mcr": "MCL 600.2950",
                    "required": False,
                    "notes": (
                        "Any personal protection order that relates to the "
                        "matters on appeal."
                    ),
                },
                {
                    "item": "Referee Recommendation / Objection",
                    "mcr": "MCR 3.215",
                    "required": False,
                    "notes": (
                        "Any referee recommendation and filed objections, "
                        "if the matter was heard by a referee."
                    ),
                },
            ]
        )
    elif case_type == "civil":
        extras.extend(
            [
                {
                    "item": "Complaint and Answer",
                    "mcr": "MCR 2.110",
                    "required": True,
                    "notes": "Pleadings that frame the issues on appeal.",
                },
                {
                    "item": "Summary Disposition / Judgment Motions",
                    "mcr": "MCR 2.116",
                    "required": False,
                    "notes": "If appeal arises from summary disposition.",
                },
            ]
        )
    elif case_type == "criminal":
        extras.extend(
            [
                {
                    "item": "Information / Indictment",
                    "mcr": "MCR 6.112",
                    "required": True,
                    "notes": "Charging document.",
                },
                {
                    "item": "Plea Transcript",
                    "mcr": "MCR 6.302",
                    "required": False,
                    "notes": "If appeal challenges a guilty plea.",
                },
                {
                    "item": "Sentencing Transcript and PSIR",
                    "mcr": "MCR 6.425",
                    "required": False,
                    "notes": "If sentencing is at issue.",
                },
            ]
        )
    elif case_type == "administrative":
        extras.extend(
            [
                {
                    "item": "Agency Decision / Final Order",
                    "mcr": "MCR 7.210(A)",
                    "required": True,
                    "notes": "The final agency decision being appealed.",
                },
                {
                    "item": "Certified Agency Record",
                    "mcr": "MCR 7.210(A)",
                    "required": True,
                    "notes": "Complete certified record from the agency.",
                },
            ]
        )

    return extras
