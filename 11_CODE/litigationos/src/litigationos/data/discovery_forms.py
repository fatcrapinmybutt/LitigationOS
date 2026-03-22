"""Discovery & Subpoena Form Generator for LitigationOS.

Michigan SCAO discovery-related forms, MCR discovery rule references,
purpose-based routing, deadline calculation, and basic template generation.

Covers:
- Subpoena forms (MC 11, MC 11a, MC 11b, MC 11c, MC 30, DC 222)
- Discovery templates (Interrogatories, RFP, RFA, Deposition Notice)
- MCR 2.301–2.313 rule summaries
- Discovery deadline calculator per MCR 2.301
- Template generators for interrogatories and requests for production

All data is local-only — no network calls, no API keys.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Any


# ---------------------------------------------------------------------------
# Data class
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class DiscoveryForm:
    """Immutable descriptor for a Michigan SCAO discovery/subpoena form."""

    form_number: str
    title: str
    purpose: str
    required_fields: list[str]
    filing_court: str
    mcr_references: list[str]
    mcl_references: list[str]
    category: str = "Discovery"
    url: str = "https://courts.michigan.gov/SCAO-forms/"
    practice_tips: str = ""
    filing_use: list[str] = field(default_factory=lambda: ["A", "B"])

    def to_dict(self) -> dict[str, Any]:
        """Serialize to plain dictionary for JSON/DB compatibility."""
        return {
            "form_number": self.form_number,
            "title": self.title,
            "purpose": self.purpose,
            "required_fields": list(self.required_fields),
            "filing_court": self.filing_court,
            "mcr_references": list(self.mcr_references),
            "mcl_references": list(self.mcl_references),
            "category": self.category,
            "url": self.url,
            "practice_tips": self.practice_tips,
            "filing_use": list(self.filing_use),
        }


# ---------------------------------------------------------------------------
# Form registry
# ---------------------------------------------------------------------------

DISCOVERY_FORMS: list[DiscoveryForm] = [
    # -- Subpoena forms -------------------------------------------------------
    DiscoveryForm(
        form_number="MC 11",
        title="Subpoena",
        purpose="Compel witness attendance at hearing, trial, or deposition",
        required_fields=[
            "court_name",
            "case_number",
            "plaintiff_name",
            "defendant_name",
            "witness_name",
            "witness_address",
            "appearance_date",
            "appearance_time",
            "appearance_location",
            "issuing_attorney_or_party",
        ],
        filing_court="Circuit / District / Probate",
        mcr_references=["MCR 2.305", "MCR 2.506"],
        mcl_references=["MCL 600.1455", "MCL 600.1701"],
        practice_tips=(
            "Must be served at least 2 days before appearance date. "
            "Witness fees and mileage must be tendered at time of service. "
            "A pro se litigant may request the clerk to issue the subpoena."
        ),
        filing_use=["A", "B", "D", "E", "F"],
    ),
    DiscoveryForm(
        form_number="MC 11a",
        title="Proof of Service of Subpoena",
        purpose="Document proper service of a subpoena on a witness",
        required_fields=[
            "court_name",
            "case_number",
            "plaintiff_name",
            "defendant_name",
            "witness_name",
            "date_of_service",
            "manner_of_service",
            "server_name",
            "server_address",
            "witness_fees_tendered",
            "mileage_tendered",
        ],
        filing_court="Circuit / District / Probate",
        mcr_references=["MCR 2.305", "MCR 2.103"],
        mcl_references=["MCL 600.1455"],
        practice_tips=(
            "File proof of service with the court before the hearing. "
            "Include the amount of witness fees and mileage tendered. "
            "Service must be by personal delivery — mail is insufficient."
        ),
        filing_use=["A", "B", "D", "E", "F"],
    ),
    DiscoveryForm(
        form_number="MC 11b",
        title="Subpoena Duces Tecum",
        purpose="Compel production of documents, records, or tangible items",
        required_fields=[
            "court_name",
            "case_number",
            "plaintiff_name",
            "defendant_name",
            "custodian_name",
            "custodian_address",
            "documents_description",
            "production_date",
            "production_location",
            "issuing_attorney_or_party",
        ],
        filing_court="Circuit / District / Probate",
        mcr_references=["MCR 2.305(A)(2)", "MCR 2.310"],
        mcl_references=["MCL 600.1455", "MCL 600.1701"],
        practice_tips=(
            "Describe documents with reasonable particularity. "
            "Recipient may object or move to quash within 14 days. "
            "Can be combined with MC 11 to compel attendance and documents."
        ),
        filing_use=["A", "B", "D", "E", "F"],
    ),
    DiscoveryForm(
        form_number="MC 11c",
        title="Subpoena to Appear at Hearing",
        purpose="Compel witness attendance specifically at a court hearing",
        required_fields=[
            "court_name",
            "case_number",
            "plaintiff_name",
            "defendant_name",
            "witness_name",
            "witness_address",
            "hearing_date",
            "hearing_time",
            "hearing_location",
            "judge_name",
            "issuing_attorney_or_party",
        ],
        filing_court="Circuit / District / Probate",
        mcr_references=["MCR 2.305", "MCR 2.506"],
        mcl_references=["MCL 600.1455"],
        practice_tips=(
            "Specify the courtroom and judge. "
            "Tender witness fees ($12.00/day) and mileage "
            "($0.655/mile round trip from residence) at service."
        ),
        filing_use=["A", "B", "D", "E", "F"],
    ),
    DiscoveryForm(
        form_number="MC 30",
        title="Affidavit and Order for Appearance (Material Witness)",
        purpose=(
            "Secure a material witness through court order when "
            "voluntary appearance is unlikely"
        ),
        required_fields=[
            "court_name",
            "case_number",
            "plaintiff_name",
            "defendant_name",
            "witness_name",
            "witness_address",
            "reason_witness_is_material",
            "reason_appearance_unlikely",
            "affiant_signature",
        ],
        filing_court="Circuit / District / Probate",
        mcr_references=["MCR 2.305", "MCR 2.506"],
        mcl_references=["MCL 600.1455", "MCL 600.1465"],
        practice_tips=(
            "Requires sworn affidavit showing the witness has material "
            "testimony and will not voluntarily appear. Court may set bond. "
            "Use sparingly — courts disfavor compelling reluctant witnesses "
            "absent strong showing of materiality."
        ),
        filing_use=["A", "D"],
    ),
    DiscoveryForm(
        form_number="DC 222",
        title="Subpoena (District Court)",
        purpose="Compel witness attendance in District Court proceedings",
        required_fields=[
            "court_name",
            "case_number",
            "plaintiff_name",
            "defendant_name",
            "witness_name",
            "witness_address",
            "appearance_date",
            "appearance_time",
            "appearance_location",
            "issuing_attorney_or_party",
        ],
        filing_court="District Court",
        mcr_references=["MCR 2.305", "MCR 4.201"],
        mcl_references=["MCL 600.1455"],
        practice_tips=(
            "District Court variant — used for small claims, "
            "landlord-tenant, and general civil in District Court. "
            "Same service and fee requirements as MC 11."
        ),
        filing_use=["B"],
    ),
    # -- Discovery templates (non-SCAO but court-recognized) -------------------
    DiscoveryForm(
        form_number="DISC-INT",
        title="Interrogatories to Opposing Party",
        purpose="Written questions requiring sworn answers within 28 days",
        required_fields=[
            "court_name",
            "case_number",
            "propounding_party",
            "responding_party",
            "interrogatory_questions",
            "date_served",
        ],
        filing_court="Circuit Court",
        mcr_references=["MCR 2.309"],
        mcl_references=[],
        category="Discovery Template",
        practice_tips=(
            "Limited to 35 interrogatories including sub-parts unless "
            "court grants leave for more. Responses due within 28 days "
            "of service. Answers must be under oath. Objections must state "
            "reasons with specificity."
        ),
        filing_use=["A", "D"],
    ),
    DiscoveryForm(
        form_number="DISC-RFP",
        title="Request for Production of Documents",
        purpose="Demand inspection/copying of documents and tangible items",
        required_fields=[
            "court_name",
            "case_number",
            "requesting_party",
            "responding_party",
            "document_requests",
            "production_date",
            "production_location",
            "date_served",
        ],
        filing_court="Circuit Court",
        mcr_references=["MCR 2.310"],
        mcl_references=[],
        category="Discovery Template",
        practice_tips=(
            "Response due within 28 days. Describe items with reasonable "
            "particularity. Requesting party may inspect and copy at a "
            "reasonable time and place. Producing party may object but "
            "must state reasons."
        ),
        filing_use=["A", "B", "D"],
    ),
    DiscoveryForm(
        form_number="DISC-RFA",
        title="Request for Admissions",
        purpose=(
            "Require opposing party to admit or deny facts or "
            "document authenticity"
        ),
        required_fields=[
            "court_name",
            "case_number",
            "requesting_party",
            "responding_party",
            "admission_requests",
            "date_served",
        ],
        filing_court="Circuit Court",
        mcr_references=["MCR 2.312"],
        mcl_references=[],
        category="Discovery Template",
        practice_tips=(
            "Matters are deemed admitted if not responded to within 28 days. "
            "Extremely powerful tool — use strategically to narrow issues. "
            "Denials must fairly respond to the substance of the request. "
            "Court may order costs of proving matters unreasonably denied."
        ),
        filing_use=["A", "B", "D"],
    ),
    DiscoveryForm(
        form_number="DISC-DEP",
        title="Notice of Deposition",
        purpose="Notify party/witness of oral deposition date, time, and place",
        required_fields=[
            "court_name",
            "case_number",
            "noticing_party",
            "deponent_name",
            "deposition_date",
            "deposition_time",
            "deposition_location",
            "court_reporter_name",
            "date_served",
        ],
        filing_court="Circuit Court",
        mcr_references=["MCR 2.306", "MCR 2.305"],
        mcl_references=[],
        category="Discovery Template",
        practice_tips=(
            "Reasonable notice required — minimum 7 days recommended. "
            "Non-party deponents must be subpoenaed (MC 11). "
            "Party deponents need only the notice. "
            "May include duces tecum requests for documents."
        ),
        filing_use=["A", "D"],
    ),
]


# ---------------------------------------------------------------------------
# Lookup index (built at import time)
# ---------------------------------------------------------------------------

_FORM_INDEX: dict[str, DiscoveryForm] = {
    f.form_number: f for f in DISCOVERY_FORMS
}


# ---------------------------------------------------------------------------
# Purpose-to-form routing table
# ---------------------------------------------------------------------------

_PURPOSE_MAP: dict[str, list[str]] = {
    "subpoena_witness": ["MC 11", "MC 11c", "DC 222"],
    "subpoena_documents": ["MC 11b"],
    "proof_of_service_subpoena": ["MC 11a"],
    "material_witness": ["MC 30"],
    "request_documents": ["MC 11b", "DISC-RFP"],
    "deposition": ["DISC-DEP", "MC 11"],
    "interrogatories": ["DISC-INT"],
    "admissions": ["DISC-RFA"],
    "compel_attendance": ["MC 11", "MC 11c", "MC 30"],
    "district_court_subpoena": ["DC 222"],
    "written_discovery": ["DISC-INT", "DISC-RFP", "DISC-RFA"],
    "full_discovery_suite": [
        "DISC-INT",
        "DISC-RFP",
        "DISC-RFA",
        "DISC-DEP",
    ],
}


# ---------------------------------------------------------------------------
# MCR Discovery Rules Reference
# ---------------------------------------------------------------------------

MCR_DISCOVERY_RULES: dict[str, dict[str, str]] = {
    "MCR 2.301": {
        "title": "General Provisions Governing Discovery",
        "scope": (
            "Establishes the discovery period, duty to supplement, "
            "and general limitations on discovery."
        ),
        "key_provisions": (
            "Discovery period begins when the action is commenced and "
            "continues until a discovery cutoff date set by the court "
            "or stipulated by the parties. Parties have a continuing "
            "duty to supplement discovery responses. Court may limit "
            "discovery that is unreasonably cumulative or obtainable "
            "from a more convenient source."
        ),
        "deadlines": (
            "Discovery cutoff is typically set in the scheduling order. "
            "Default: discovery must be completed 28 days before trial "
            "unless the court orders otherwise."
        ),
    },
    "MCR 2.302": {
        "title": "General Rules Governing Discovery — Scope",
        "scope": (
            "Defines the scope of permissible discovery: any matter "
            "relevant to a claim or defense that is not privileged."
        ),
        "key_provisions": (
            "Parties may obtain discovery regarding any non-privileged "
            "matter relevant to any party's claim or defense. Information "
            "need not be admissible at trial if reasonably calculated to "
            "lead to the discovery of admissible evidence. Includes "
            "insurance agreements, expert opinions, and trial preparation "
            "materials (with limitations)."
        ),
        "deadlines": "",
    },
    "MCR 2.305": {
        "title": "Subpoena for Taking Deposition or for Discovery",
        "scope": (
            "Governs issuance and service of subpoenas for depositions "
            "and document production from non-parties."
        ),
        "key_provisions": (
            "Subpoena may command attendance at deposition or production "
            "of documents. Clerk issues on request of party or attorney. "
            "Must be served personally with witness fee and mileage. "
            "Recipient may object or move to quash within 14 days of "
            "service or before the time specified, whichever is first."
        ),
        "deadlines": (
            "Serve at least 2 days before appearance. Objection/motion "
            "to quash within 14 days of service."
        ),
    },
    "MCR 2.306": {
        "title": "Depositions on Oral Examination",
        "scope": (
            "Procedures for taking depositions by oral questions, "
            "including notice requirements and conduct rules."
        ),
        "key_provisions": (
            "Any party may depose any person. Reasonable written notice "
            "to all parties required — must state time, place, and name "
            "of deponent. Non-party deponents must be subpoenaed. "
            "Deposition may include a duces tecum request. Officer "
            "administers oath and records testimony. Examination and "
            "cross-examination proceed as at trial."
        ),
        "deadlines": "Reasonable notice required; 7 days recommended.",
    },
    "MCR 2.307": {
        "title": "Depositions on Written Questions",
        "scope": (
            "Procedures for depositions where questions are submitted "
            "in writing rather than asked orally."
        ),
        "key_provisions": (
            "Party serves written questions on all parties with notice "
            "naming the deponent. Cross-questions within 21 days. "
            "Redirect questions within 14 days of cross-questions. "
            "Recross within 14 days of redirect. Officer reads questions "
            "to deponent and records answers under oath."
        ),
        "deadlines": (
            "Cross-questions: 21 days after service. "
            "Redirect: 14 days. Recross: 14 days."
        ),
    },
    "MCR 2.309": {
        "title": "Interrogatories to Parties",
        "scope": (
            "Governs written interrogatories served on parties, "
            "including limits and response requirements."
        ),
        "key_provisions": (
            "Limited to 35 interrogatories including discrete sub-parts "
            "unless court grants leave for more. Answers must be under "
            "oath within 28 days of service. Objections must state "
            "reasons with specificity. Answering party may refer to "
            "business records if burden of deriving the answer is "
            "substantially the same for both parties."
        ),
        "deadlines": "Responses due within 28 days of service.",
    },
    "MCR 2.310": {
        "title": "Production of Documents and Things; Entry on Land",
        "scope": (
            "Governs requests for production of documents, tangible "
            "items, and inspection of property."
        ),
        "key_provisions": (
            "Any party may serve a request to produce documents, "
            "electronically stored information, or tangible things, "
            "or to permit entry on land. Items described with reasonable "
            "particularity. Response within 28 days — must state whether "
            "inspection will be permitted or state objections."
        ),
        "deadlines": "Responses due within 28 days of service.",
    },
    "MCR 2.312": {
        "title": "Request for Admissions",
        "scope": (
            "Governs requests to admit facts, application of law to "
            "fact, or genuineness of documents."
        ),
        "key_provisions": (
            "Matters deemed admitted if not answered within 28 days. "
            "Denial must fairly respond to the substance. Party may not "
            "give lack of information as a reason for failure to admit "
            "unless the party states it has made reasonable inquiry. "
            "Court may award costs of proving matters unreasonably denied."
        ),
        "deadlines": (
            "Responses due within 28 days of service. Failure to respond "
            "= deemed admitted."
        ),
    },
    "MCR 2.313": {
        "title": "Failure to Provide Discovery — Sanctions",
        "scope": (
            "Remedies and sanctions when a party fails to comply with "
            "discovery obligations."
        ),
        "key_provisions": (
            "If a party fails to answer interrogatories, respond to "
            "RFP, attend deposition, or comply with a discovery order, "
            "the court may: (a) deem facts established, (b) prohibit "
            "the disobedient party from introducing evidence, (c) strike "
            "pleadings, (d) stay proceedings, (e) dismiss the action or "
            "enter default judgment, (f) hold in contempt. Court must "
            "order reasonable expenses including attorney fees unless "
            "failure was substantially justified."
        ),
        "deadlines": "",
    },
}


# ---------------------------------------------------------------------------
# Discovery deadline offsets (days before trial)
# ---------------------------------------------------------------------------

_DEADLINE_OFFSETS: dict[str, dict[str, Any]] = {
    "discovery_cutoff": {
        "days_before_trial": 28,
        "description": "Last day to complete all discovery",
        "mcr_reference": "MCR 2.301",
    },
    "interrogatory_service": {
        "days_before_trial": 56,
        "description": (
            "Last day to serve interrogatories so responses are due "
            "before discovery cutoff (28-day response + 28-day cutoff)"
        ),
        "mcr_reference": "MCR 2.309",
    },
    "rfp_service": {
        "days_before_trial": 56,
        "description": (
            "Last day to serve RFP so responses are due "
            "before discovery cutoff"
        ),
        "mcr_reference": "MCR 2.310",
    },
    "rfa_service": {
        "days_before_trial": 56,
        "description": (
            "Last day to serve RFA so deemed-admitted deadline "
            "falls before discovery cutoff"
        ),
        "mcr_reference": "MCR 2.312",
    },
    "deposition_notice": {
        "days_before_trial": 35,
        "description": (
            "Recommended last day to notice depositions "
            "(7-day notice + completion before cutoff)"
        ),
        "mcr_reference": "MCR 2.306",
    },
    "subpoena_service": {
        "days_before_trial": 2,
        "description": "Minimum days before appearance to serve subpoena",
        "mcr_reference": "MCR 2.305",
    },
    "motion_to_compel": {
        "days_before_trial": 21,
        "description": (
            "Recommended last day to file motion to compel "
            "so court can rule before trial"
        ),
        "mcr_reference": "MCR 2.313",
    },
    "expert_witness_disclosure": {
        "days_before_trial": 42,
        "description": (
            "Recommended deadline for expert witness disclosure "
            "(often set in scheduling order)"
        ),
        "mcr_reference": "MCR 2.302(B)(4)",
    },
}


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def get_discovery_forms() -> dict[str, Any]:
    """Return all discovery/subpoena forms with metadata.

    Returns
    -------
    dict[str, Any]
        Keys: ``"forms"`` (list of form dicts), ``"count"`` (int),
        ``"categories"`` (sorted unique categories).

    Examples
    --------
    >>> data = get_discovery_forms()
    >>> data["count"]
    10
    """
    forms = [f.to_dict() for f in DISCOVERY_FORMS]
    categories = sorted({f.category for f in DISCOVERY_FORMS})
    return {
        "forms": forms,
        "count": len(forms),
        "categories": categories,
    }


def get_discovery_rules() -> dict[str, dict[str, str]]:
    """Return MCR discovery rule summaries.

    Returns
    -------
    dict[str, dict[str, str]]
        Keyed by rule number (e.g. ``"MCR 2.309"``).  Each value
        contains ``title``, ``scope``, ``key_provisions``, and
        ``deadlines``.

    Examples
    --------
    >>> rules = get_discovery_rules()
    >>> rules["MCR 2.309"]["title"]
    'Interrogatories to Parties'
    """
    return dict(MCR_DISCOVERY_RULES)


def get_form_for_purpose(purpose: str) -> list[dict[str, Any]]:
    """Map a discovery purpose keyword to the matching form(s).

    Parameters
    ----------
    purpose : str
        One of: ``"subpoena_witness"``, ``"subpoena_documents"``,
        ``"request_documents"``, ``"deposition"``,
        ``"interrogatories"``, ``"admissions"``,
        ``"compel_attendance"``, ``"written_discovery"``,
        ``"full_discovery_suite"``, ``"material_witness"``,
        ``"proof_of_service_subpoena"``,
        ``"district_court_subpoena"``.

    Returns
    -------
    list[dict[str, Any]]
        Form metadata dicts for every matching form.  Empty list if
        the purpose key is not recognised.

    Examples
    --------
    >>> forms = get_form_for_purpose("interrogatories")
    >>> forms[0]["form_number"]
    'DISC-INT'
    """
    key = purpose.strip().lower().replace(" ", "_").replace("-", "_")
    form_numbers = _PURPOSE_MAP.get(key, [])
    return [
        _FORM_INDEX[fn].to_dict()
        for fn in form_numbers
        if fn in _FORM_INDEX
    ]


def get_discovery_deadlines(trial_date: str) -> dict[str, Any]:
    """Calculate discovery cutoff dates relative to a trial date.

    Parameters
    ----------
    trial_date : str
        Trial date in ``YYYY-MM-DD`` format.

    Returns
    -------
    dict[str, Any]
        Keys: ``"trial_date"``, ``"deadlines"`` (dict mapping each
        deadline name to its computed date, description, and MCR
        reference).

    Raises
    ------
    ValueError
        If *trial_date* is not valid ``YYYY-MM-DD``.

    Examples
    --------
    >>> dl = get_discovery_deadlines("2025-09-15")
    >>> dl["deadlines"]["discovery_cutoff"]["date"]
    '2025-08-18'
    """
    try:
        trial_dt = datetime.strptime(trial_date, "%Y-%m-%d")
    except ValueError as exc:
        raise ValueError(
            f"trial_date must be YYYY-MM-DD, got: {trial_date!r}"
        ) from exc

    deadlines: dict[str, dict[str, str]] = {}
    for name, info in _DEADLINE_OFFSETS.items():
        offset = timedelta(days=info["days_before_trial"])
        cutoff = trial_dt - offset
        deadlines[name] = {
            "date": cutoff.strftime("%Y-%m-%d"),
            "description": info["description"],
            "mcr_reference": info["mcr_reference"],
            "days_before_trial": str(info["days_before_trial"]),
        }

    return {
        "trial_date": trial_date,
        "deadlines": deadlines,
    }


def get_form_detail(form_number: str) -> dict[str, Any] | None:
    """Return full metadata for a single form by number.

    Parameters
    ----------
    form_number : str
        E.g. ``"MC 11b"`` or ``"DISC-INT"``.

    Returns
    -------
    dict[str, Any] | None
        Form metadata or ``None`` if not found.

    Examples
    --------
    >>> detail = get_form_detail("MC 11b")
    >>> detail["title"]
    'Subpoena Duces Tecum'
    """
    key = form_number.strip().upper()
    # Try exact match first, then normalised
    form = _FORM_INDEX.get(form_number.strip()) or _FORM_INDEX.get(key)
    if form is None:
        return None
    return form.to_dict()


def get_required_fields(form_number: str) -> list[str]:
    """Return the required fields for a specific form.

    Parameters
    ----------
    form_number : str
        E.g. ``"MC 11"`` or ``"DISC-RFP"``.

    Returns
    -------
    list[str]
        Required field names.  Empty list if form not found.

    Examples
    --------
    >>> get_required_fields("MC 11a")
    ['court_name', 'case_number', ...]
    """
    form = _FORM_INDEX.get(form_number.strip())
    if form is None:
        return []
    return list(form.required_fields)


def list_purposes() -> list[str]:
    """Return all recognised purpose keywords for routing.

    Returns
    -------
    list[str]
        Sorted list of purpose strings usable with
        :func:`get_form_for_purpose`.
    """
    return sorted(_PURPOSE_MAP.keys())


# ---------------------------------------------------------------------------
# Template generators
# ---------------------------------------------------------------------------

def generate_interrogatories_template(
    case_number: str,
    party: str,
) -> str:
    """Generate a basic interrogatories template.

    Parameters
    ----------
    case_number : str
        The case number (e.g. ``"2024-001507-DC"``).
    party : str
        Name of the party to whom interrogatories are directed.

    Returns
    -------
    str
        A ready-to-customise interrogatories document body.

    Examples
    --------
    >>> text = generate_interrogatories_template(
    ...     "2024-001507-DC", "Emily A. Watson"
    ... )
    >>> "INTERROGATORIES" in text
    True
    """
    return f"""\
STATE OF MICHIGAN
IN THE 14TH JUDICIAL CIRCUIT COURT FOR MUSKEGON COUNTY

Case No. {case_number}

ANDREW JAMES PIGORS,
    Plaintiff,

v.

{party.upper()},
    Defendant.
______________________________________________/

PLAINTIFF'S FIRST SET OF INTERROGATORIES TO DEFENDANT

TO: {party}

    You are requested to answer the following interrogatories separately
and fully, in writing and under oath, within twenty-eight (28) days of
service in accordance with MCR 2.309.

DEFINITIONS AND INSTRUCTIONS

1.  "You" or "Your" refers to {party} and any person acting on your
    behalf.

2.  "Document" means any writing, recording, or photograph as defined
    in MRE 1001 and includes electronically stored information.

3.  "Identify" when used with respect to a person means to state the
    person's full name, last known address, and telephone number.

4.  "Identify" when used with respect to a document means to describe
    its type, date, author, recipient, subject matter, and current
    location or custodian.

5.  If you object to any interrogatory, state the specific grounds for
    the objection with particularity as required by MCR 2.309(B)(4).

INTERROGATORIES

INTERROGATORY NO. 1:
State your full legal name, date of birth, current address, and all
addresses at which you have resided during the past five (5) years.

INTERROGATORY NO. 2:
Identify all persons with knowledge of the facts relevant to this
action and for each person state: (a) their name and address; (b) the
subject matter of their knowledge; and (c) their relationship to you.

INTERROGATORY NO. 3:
Identify all documents that you intend to use as exhibits at trial or
in support of any motion in this action.

INTERROGATORY NO. 4:
Describe in detail every communication — oral, written, or electronic
— between you and any third party concerning the subject matter of this
action during the past three (3) years.

INTERROGATORY NO. 5:
State whether you have been a party to any other legal proceeding in
any court within the past ten (10) years and, if so, identify the
court, case number, nature of the action, and disposition.

[ADDITIONAL INTERROGATORIES — CUSTOMISE AS NEEDED]

Respectfully submitted,

______________________________
Andrew James Pigors, Pro Se
1977 Whitehall Road, Lot 17
North Muskegon, MI 49445
(231) 903-5690
andrewjpigors@gmail.com

CERTIFICATE OF SERVICE

I certify that on _______________, I served a copy of this document on
{party} by [personal service / first-class mail / email] at:

[ADDRESS]

______________________________
Andrew James Pigors
"""


def generate_rfp_template(
    case_number: str,
    party: str,
) -> str:
    """Generate a basic Request for Production of Documents template.

    Parameters
    ----------
    case_number : str
        The case number (e.g. ``"2024-001507-DC"``).
    party : str
        Name of the party to whom the request is directed.

    Returns
    -------
    str
        A ready-to-customise RFP document body.

    Examples
    --------
    >>> text = generate_rfp_template(
    ...     "2024-001507-DC", "Emily A. Watson"
    ... )
    >>> "REQUEST FOR PRODUCTION" in text
    True
    """
    return f"""\
STATE OF MICHIGAN
IN THE 14TH JUDICIAL CIRCUIT COURT FOR MUSKEGON COUNTY

Case No. {case_number}

ANDREW JAMES PIGORS,
    Plaintiff,

v.

{party.upper()},
    Defendant.
______________________________________________/

PLAINTIFF'S FIRST REQUEST FOR PRODUCTION OF DOCUMENTS

TO: {party}

    Pursuant to MCR 2.310, you are requested to produce for inspection
and copying the documents and tangible items described below within
twenty-eight (28) days of service at a mutually agreeable time and
place.

DEFINITIONS AND INSTRUCTIONS

1.  "You" or "Your" refers to {party} and any person acting on your
    behalf, including agents, employees, and attorneys.

2.  "Document" includes writings, drawings, graphs, charts,
    photographs, recordings, electronically stored information, and
    any other data compilation from which information can be obtained,
    as described in MCR 2.310(A).

3.  If any document is withheld on the basis of privilege, provide: the
    date, author, recipient, subject matter, and the specific privilege
    claimed, as required by MCR 2.302(C).

4.  Produce documents as they are kept in the ordinary course of
    business or organise and label them to correspond to the categories
    in this request, per MCR 2.310(B)(1).

REQUESTS FOR PRODUCTION

REQUEST NO. 1:
All documents relating to communications between you and any third
party concerning the subject matter of this action.

REQUEST NO. 2:
All financial records, including bank statements, pay stubs, tax
returns, and income records for the past three (3) years.

REQUEST NO. 3:
All documents relating to any prior legal proceedings to which you
have been a party within the past ten (10) years.

REQUEST NO. 4:
All photographs, videos, or recordings in your possession or control
that relate to any issue in this case.

REQUEST NO. 5:
All electronic communications — including text messages, emails, and
social media messages — between you and any other party or witness in
this action during the past three (3) years.

[ADDITIONAL REQUESTS — CUSTOMISE AS NEEDED]

Respectfully submitted,

______________________________
Andrew James Pigors, Pro Se
1977 Whitehall Road, Lot 17
North Muskegon, MI 49445
(231) 903-5690
andrewjpigors@gmail.com

CERTIFICATE OF SERVICE

I certify that on _______________, I served a copy of this document on
{party} by [personal service / first-class mail / email] at:

[ADDRESS]

______________________________
Andrew James Pigors
"""
