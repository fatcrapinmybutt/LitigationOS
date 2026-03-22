"""PPO Form Suite for Lane D — Michigan Personal Protection Order forms.

Complete registry of SCAO PPO-related forms with required fields, action
routing, MCR/MCL references, and timeline-tracking templates.  Designed for
Pigors v Watson (Case 2023-5907-PP), 14th Circuit Court, Family Division,
Muskegon County.  All data is local-only — no external API calls.

Sources:
  - Michigan Compiled Laws §§ 600.2950, 600.2950a, 764.15b
  - Michigan Court Rules MCR 3.705, 3.706, 3.707, 3.708
  - courts.michigan.gov/SCAO-forms/ (March 2026)
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


# =========================================================================
# Data classes
# =========================================================================

@dataclass(frozen=True)
class PPOForm:
    """Immutable descriptor for a single Michigan SCAO PPO-related form."""

    form_number: str
    title: str
    purpose: str
    required_fields: list[str]
    filing_court: str
    mcr_references: list[str]
    mcl_references: list[str]
    category: str = "PPO"
    url: str = "https://courts.michigan.gov/SCAO-forms/"
    practice_tips: str = ""
    filing_use: list[str] = field(default_factory=lambda: ["F5"])

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


# =========================================================================
# PPO FORM REGISTRY — authoritative list of Michigan PPO-related forms
# =========================================================================

PPO_FORMS: list[PPOForm] = [
    # ----- Domestic PPO petition & order --------------------------------
    PPOForm(
        form_number="CC 375",
        title="Petition for Personal Protection Order (Domestic Relationship)",
        purpose=(
            "Initiates a domestic-relationship PPO.  Filed by petitioner "
            "against a spouse, former spouse, person with a child in common, "
            "dating partner, or household/former-household member.  Must "
            "allege specific acts: assault, threat of assault, harassment, "
            "sexual assault, or other conduct under MCL 600.2950."
        ),
        required_fields=[
            "case_number",
            "court_name",
            "court_address",
            "petitioner_name",
            "petitioner_address",
            "petitioner_dob",
            "petitioner_phone",
            "respondent_name",
            "respondent_address",
            "respondent_dob",
            "respondent_description",
            "relationship_type",
            "children_in_common",
            "factual_basis_of_petition",
            "specific_acts_alleged",
            "dates_of_acts",
            "requested_provisions",
            "prior_ppo_history",
            "other_pending_actions",
            "petitioner_signature",
            "date_signed",
        ],
        filing_court="Circuit Court — Family Division",
        mcr_references=["MCR 3.705(A)", "MCR 3.705(B)"],
        mcl_references=["MCL 600.2950", "MCL 600.2950(1)"],
        practice_tips=(
            "Court may issue ex parte (without hearing) if petition shows "
            "immediate and irreparable injury.  Respondent then has 14 days "
            "after service to request a hearing to modify/terminate."
        ),
    ),
    PPOForm(
        form_number="CC 376",
        title="Personal Protection Order (Domestic Relationship)",
        purpose=(
            "The actual PPO order form issued by the circuit court after "
            "granting a CC 375 petition.  Sets out specific prohibitions "
            "and conditions (no contact, stay away, vacate premises, etc.)."
        ),
        required_fields=[
            "case_number",
            "court_name",
            "judge_name",
            "petitioner_name",
            "respondent_name",
            "respondent_identifiers",
            "prohibited_conduct",
            "specific_provisions",
            "expiration_date",
            "effective_date",
            "judge_signature",
            "date_issued",
        ],
        filing_court="Circuit Court — Family Division",
        mcr_references=["MCR 3.705(A)", "MCR 3.706"],
        mcl_references=["MCL 600.2950(1)", "MCL 600.2950(3)"],
        practice_tips=(
            "PPO is effective immediately upon signing.  Enforceable "
            "statewide and entered into LEIN.  Violation is a crime "
            "under MCL 764.15b (up to 93 days / $500 first offense)."
        ),
    ),

    # ----- Modify / terminate / extend ----------------------------------
    PPOForm(
        form_number="CC 377",
        title="Motion to Modify/Terminate Personal Protection Order",
        purpose=(
            "Filed by respondent (or petitioner) to request the court "
            "modify terms of, or terminate, an existing PPO.  Triggers "
            "a hearing where both parties may present evidence."
        ),
        required_fields=[
            "case_number",
            "court_name",
            "moving_party_name",
            "opposing_party_name",
            "ppo_date_issued",
            "ppo_form_number",
            "relief_requested",
            "grounds_for_modification",
            "factual_basis",
            "signature",
            "date_signed",
            "proof_of_service",
        ],
        filing_court="Circuit Court — Family Division",
        mcr_references=["MCR 3.707(A)", "MCR 3.707(B)"],
        mcl_references=["MCL 600.2950(10)", "MCL 600.2950(12)"],
        practice_tips=(
            "CRITICAL: 14-day deadline from service of PPO to file.  "
            "Missing the deadline does NOT waive the right to file later, "
            "but the court treats earlier motions more favorably.  Must "
            "serve opposing party with motion and notice of hearing."
        ),
    ),
    PPOForm(
        form_number="CC 383",
        title="Motion to Extend Personal Protection Order",
        purpose=(
            "Filed by petitioner to extend an existing PPO before it "
            "expires.  Must demonstrate continued need for protection."
        ),
        required_fields=[
            "case_number",
            "court_name",
            "petitioner_name",
            "respondent_name",
            "original_ppo_date",
            "current_expiration_date",
            "requested_extension_period",
            "grounds_for_extension",
            "recent_incidents",
            "continued_threat_basis",
            "signature",
            "date_signed",
        ],
        filing_court="Circuit Court — Family Division",
        mcr_references=["MCR 3.706(D)"],
        mcl_references=["MCL 600.2950(11)"],
        practice_tips=(
            "File BEFORE the PPO expires.  Attach evidence of continuing "
            "threat or pattern of behavior.  The court will schedule a "
            "hearing; respondent must be served."
        ),
    ),

    # ----- Non-domestic / stalking PPO ----------------------------------
    PPOForm(
        form_number="CC 380",
        title="Petition for Personal Protection Order (Non-Domestic Stalking)",
        purpose=(
            "Initiates a non-domestic-relationship PPO based on stalking "
            "conduct under MCL 600.2950a.  Used when the parties do not "
            "have a domestic relationship but the respondent has engaged "
            "in a pattern of willful, unconsented contact that causes "
            "fear or emotional distress."
        ),
        required_fields=[
            "case_number",
            "court_name",
            "court_address",
            "petitioner_name",
            "petitioner_address",
            "petitioner_dob",
            "respondent_name",
            "respondent_address",
            "respondent_description",
            "stalking_acts_alleged",
            "dates_and_pattern",
            "reasonable_fear_basis",
            "requested_provisions",
            "prior_ppo_history",
            "other_pending_actions",
            "petitioner_signature",
            "date_signed",
        ],
        filing_court="Circuit Court",
        mcr_references=["MCR 3.705(A)"],
        mcl_references=["MCL 600.2950a", "MCL 750.411h", "MCL 750.411i"],
        practice_tips=(
            "Stalking PPO requires a pattern (2+ acts) of unconsented "
            "contact causing reasonable fear.  Single incidents generally "
            "insufficient unless they involve threats of violence."
        ),
    ),
    PPOForm(
        form_number="CC 381",
        title="Personal Protection Order (Non-Domestic Stalking)",
        purpose=(
            "The actual PPO order form issued by the circuit court upon "
            "granting a CC 380 stalking petition.  Sets out no-contact "
            "and stay-away provisions."
        ),
        required_fields=[
            "case_number",
            "court_name",
            "judge_name",
            "petitioner_name",
            "respondent_name",
            "respondent_identifiers",
            "prohibited_conduct",
            "specific_provisions",
            "expiration_date",
            "effective_date",
            "judge_signature",
            "date_issued",
        ],
        filing_court="Circuit Court",
        mcr_references=["MCR 3.705(A)", "MCR 3.706"],
        mcl_references=["MCL 600.2950a"],
        practice_tips=(
            "Same enforcement mechanism as domestic PPO — violation is "
            "criminal under MCL 764.15b.  Entered into LEIN."
        ),
    ),

    # ----- Proof of service ---------------------------------------------
    PPOForm(
        form_number="CC 382",
        title="Proof of Service of Personal Protection Order",
        purpose=(
            "Documents that the PPO was properly served on the respondent. "
            "Service is required for the PPO to be enforceable for contempt "
            "or criminal prosecution of violations."
        ),
        required_fields=[
            "case_number",
            "court_name",
            "petitioner_name",
            "respondent_name",
            "ppo_date_issued",
            "method_of_service",
            "date_of_service",
            "time_of_service",
            "location_of_service",
            "person_who_served",
            "server_signature",
            "server_address",
        ],
        filing_court="Circuit Court — Family Division",
        mcr_references=["MCR 3.706(C)", "MCR 2.105"],
        mcl_references=["MCL 600.2950(8)"],
        practice_tips=(
            "PPO enforceable upon signing, but contempt/criminal charges "
            "require proof that respondent had actual notice.  File this "
            "form immediately after service is completed."
        ),
    ),

    # ----- Show cause / contempt ----------------------------------------
    PPOForm(
        form_number="MC 241",
        title="Motion and Verification for Show Cause (Contempt)",
        purpose=(
            "Requests the court to issue an order requiring the respondent "
            "to show cause why they should not be held in contempt for "
            "violating the PPO.  Used for civil or criminal contempt."
        ),
        required_fields=[
            "case_number",
            "court_name",
            "moving_party_name",
            "party_accused_of_contempt",
            "order_allegedly_violated",
            "order_date",
            "specific_violations",
            "dates_of_violations",
            "factual_basis",
            "relief_requested",
            "verification_oath",
            "signature",
            "date_signed",
        ],
        filing_court="Circuit Court / District Court",
        mcr_references=["MCR 3.708", "MCR 3.606"],
        mcl_references=[
            "MCL 600.1701",
            "MCL 600.1715",
            "MCL 764.15b",
        ],
        practice_tips=(
            "Criminal contempt for PPO violation: up to 93 days jail and "
            "$500 fine per incident (first offense).  Civil contempt may "
            "include coercive sanctions until compliance.  Attach evidence "
            "of each specific violation (texts, photos, police reports)."
        ),
        filing_use=["F5", "F1"],
    ),

    # ----- Response to motion (PPO context) -----------------------------
    PPOForm(
        form_number="CC 378",
        title="Response to Motion Regarding Personal Protection Order",
        purpose=(
            "Filed in response to a CC 377 motion to modify/terminate.  "
            "Allows the non-moving party to oppose the requested changes "
            "and present counter-evidence."
        ),
        required_fields=[
            "case_number",
            "court_name",
            "responding_party_name",
            "moving_party_name",
            "motion_date",
            "response_to_claims",
            "supporting_facts",
            "relief_requested",
            "signature",
            "date_signed",
        ],
        filing_court="Circuit Court — Family Division",
        mcr_references=["MCR 3.707"],
        mcl_references=["MCL 600.2950(12)"],
        practice_tips=(
            "Must be filed and served before the hearing date.  Attach "
            "any evidence of continued need for protection (police "
            "reports, texts, witness statements)."
        ),
    ),

    # ----- PPO violation / criminal enforcement -------------------------
    PPOForm(
        form_number="MC 242",
        title="Order to Show Cause",
        purpose=(
            "Court order directing respondent to appear and show cause "
            "why they should not be held in contempt.  Issued by the "
            "judge after reviewing MC 241."
        ),
        required_fields=[
            "case_number",
            "court_name",
            "judge_name",
            "respondent_name",
            "hearing_date",
            "hearing_time",
            "allegations_summary",
            "judge_signature",
            "date_issued",
        ],
        filing_court="Circuit Court / District Court",
        mcr_references=["MCR 3.708", "MCR 3.606(A)"],
        mcl_references=["MCL 600.1701"],
        practice_tips=(
            "Respondent MUST appear at the show-cause hearing.  Failure "
            "to appear may result in a bench warrant.  Petitioner should "
            "be prepared to testify and present documentary evidence."
        ),
        filing_use=[],
    ),

    # ----- Supplemental / utility forms ---------------------------------
    PPOForm(
        form_number="MC 11",
        title="Proof of Service (General)",
        purpose=(
            "General proof-of-service form.  Used alongside CC 382 when "
            "serving motions, responses, or other PPO-related filings on "
            "opposing parties."
        ),
        required_fields=[
            "case_number",
            "court_name",
            "document_served",
            "date_of_service",
            "method_of_service",
            "person_served",
            "server_name",
            "server_signature",
        ],
        filing_court="Circuit Court / District Court",
        mcr_references=["MCR 2.107"],
        mcl_references=[],
        practice_tips=(
            "File proof of service for EVERY document served.  Without "
            "it the court cannot verify service was completed."
        ),
        filing_use=["F5"],
    ),
    PPOForm(
        form_number="MC 20",
        title="Fee Waiver Request",
        purpose=(
            "Request to waive court filing fees for PPO proceedings.  "
            "PPO petitions (CC 375 / CC 380) are generally free to file, "
            "but motions and show-cause filings may carry fees."
        ),
        required_fields=[
            "case_number",
            "court_name",
            "petitioner_name",
            "income_information",
            "public_assistance_status",
            "signature",
            "date_signed",
        ],
        filing_court="Circuit Court / District Court",
        mcr_references=["MCR 2.002"],
        mcl_references=["MCL 600.2529"],
        practice_tips=(
            "File with every fee-bearing PPO motion.  Approved = all "
            "fees waived, including service costs."
        ),
    ),
]


# =========================================================================
# Internal lookup index  (built once at import time)
# =========================================================================

_FORM_INDEX: dict[str, PPOForm] = {f.form_number: f for f in PPO_FORMS}


# =========================================================================
# ACTION → FORM(S) routing table
# =========================================================================

_ACTION_MAP: dict[str, list[str]] = {
    # --- petition / initiation ---
    "petition_domestic": ["CC 375"],
    "petition_stalking": ["CC 380"],
    "petition": ["CC 375", "CC 380"],
    "file_ppo": ["CC 375", "CC 380"],
    "initiate": ["CC 375", "CC 380"],
    # --- order forms ---
    "order_domestic": ["CC 376"],
    "order_stalking": ["CC 381"],
    "order": ["CC 376", "CC 381"],
    # --- modify / terminate ---
    "modify": ["CC 377"],
    "terminate": ["CC 377"],
    "modify_terminate": ["CC 377"],
    "vacate": ["CC 377"],
    # --- extend ---
    "extend": ["CC 383"],
    "renew": ["CC 383"],
    # --- respond ---
    "respond": ["CC 378"],
    "oppose": ["CC 378"],
    "response": ["CC 378"],
    # --- service ---
    "serve": ["CC 382", "MC 11"],
    "proof_of_service": ["CC 382", "MC 11"],
    "service": ["CC 382", "MC 11"],
    # --- contempt / enforcement ---
    "violate": ["MC 241"],
    "contempt": ["MC 241", "MC 242"],
    "enforce": ["MC 241"],
    "show_cause": ["MC 241", "MC 242"],
    # --- fee waiver ---
    "fee_waiver": ["MC 20"],
    "waiver": ["MC 20"],
}


# =========================================================================
# Public API
# =========================================================================

def get_ppo_forms() -> list[dict[str, Any]]:
    """Return metadata for every PPO-related SCAO form in the registry.

    Returns
    -------
    list[dict[str, Any]]
        Each element is a plain dictionary (serializable) with keys such as
        ``form_number``, ``title``, ``purpose``, ``required_fields``, etc.
    """
    return [f.to_dict() for f in PPO_FORMS]


def get_form_for_action(action: str) -> list[dict[str, Any]]:
    """Map a litigation action keyword to the correct PPO form(s).

    Parameters
    ----------
    action : str
        One of: ``"petition"``, ``"modify"``, ``"terminate"``, ``"extend"``,
        ``"violate"``, ``"contempt"``, ``"serve"``, ``"respond"``,
        ``"fee_waiver"``, etc.  Case-insensitive; underscores and hyphens
        are normalised.

    Returns
    -------
    list[dict[str, Any]]
        Form metadata dicts for every matching form.  Empty list when the
        action is not recognised.

    Examples
    --------
    >>> forms = get_form_for_action("terminate")
    >>> forms[0]["form_number"]
    'CC 377'
    """
    key = action.strip().lower().replace("-", "_").replace(" ", "_")
    form_numbers = _ACTION_MAP.get(key, [])
    return [_FORM_INDEX[fn].to_dict() for fn in form_numbers if fn in _FORM_INDEX]


def get_required_fields(form_number: str) -> list[str]:
    """Return the list of required fields for a given SCAO form.

    Parameters
    ----------
    form_number : str
        Exact form number (e.g. ``"CC 375"``, ``"MC 241"``).

    Returns
    -------
    list[str]
        Ordered list of field names.  Empty list if the form number is
        unknown.

    Examples
    --------
    >>> "petitioner_name" in get_required_fields("CC 375")
    True
    """
    form = _FORM_INDEX.get(form_number.strip().upper())
    if form is None:
        # Try without normalisation (e.g. "CC 375" vs "cc 375")
        for f in PPO_FORMS:
            if f.form_number.upper() == form_number.strip().upper():
                return list(f.required_fields)
        return []
    return list(form.required_fields)


def get_form_detail(form_number: str) -> dict[str, Any] | None:
    """Return full metadata for a single form, or ``None`` if not found.

    Parameters
    ----------
    form_number : str
        Exact form number (e.g. ``"CC 376"``).

    Returns
    -------
    dict[str, Any] | None
    """
    form = _FORM_INDEX.get(form_number.strip())
    return form.to_dict() if form else None


def list_actions() -> list[str]:
    """Return every recognised action keyword that can be passed to
    :func:`get_form_for_action`."""
    return sorted(_ACTION_MAP.keys())


def generate_ppo_timeline(case_number: str) -> dict[str, Any]:
    """Produce a blank PPO-lifecycle timeline template for *case_number*.

    The template enumerates every procedural milestone in a PPO case
    so that dates can be filled in as the case progresses.

    Parameters
    ----------
    case_number : str
        The case number (e.g. ``"2023-5907-PP"``).

    Returns
    -------
    dict[str, Any]
        Skeleton with ``case_number``, ``lane``, ``milestones`` list, and
        ``notes`` field.  Each milestone carries ``event``, ``form``,
        ``deadline_rule``, ``date`` (to be populated), and ``status``.
    """
    milestones: list[dict[str, str]] = [
        {
            "event": "PPO Petition Filed",
            "form": "CC 375 / CC 380",
            "deadline_rule": "No statutory deadline to file",
            "date": "",
            "status": "pending",
        },
        {
            "event": "Ex Parte PPO Issued",
            "form": "CC 376 / CC 381",
            "deadline_rule": "Same day or next business day after petition",
            "date": "",
            "status": "pending",
        },
        {
            "event": "PPO Served on Respondent",
            "form": "CC 382",
            "deadline_rule": "As soon as practicable; file proof immediately",
            "date": "",
            "status": "pending",
        },
        {
            "event": "Proof of Service Filed",
            "form": "CC 382 / MC 11",
            "deadline_rule": "Immediately after service",
            "date": "",
            "status": "pending",
        },
        {
            "event": "Motion to Modify/Terminate Filed",
            "form": "CC 377",
            "deadline_rule": "Within 14 days of service (MCR 3.707)",
            "date": "",
            "status": "pending",
        },
        {
            "event": "Response to Motion Filed",
            "form": "CC 378",
            "deadline_rule": "Before hearing date",
            "date": "",
            "status": "pending",
        },
        {
            "event": "Hearing on Motion to Modify/Terminate",
            "form": "N/A",
            "deadline_rule": "Court schedules within 14 days of motion (MCR 3.707)",
            "date": "",
            "status": "pending",
        },
        {
            "event": "Court Decision on Motion",
            "form": "CC 376 (amended) or termination order",
            "deadline_rule": "At or after hearing",
            "date": "",
            "status": "pending",
        },
        {
            "event": "PPO Violation Reported",
            "form": "MC 241",
            "deadline_rule": "File promptly after each violation",
            "date": "",
            "status": "pending",
        },
        {
            "event": "Show Cause Order Issued",
            "form": "MC 242",
            "deadline_rule": "After court reviews MC 241",
            "date": "",
            "status": "pending",
        },
        {
            "event": "Contempt Hearing",
            "form": "N/A",
            "deadline_rule": "Scheduled by court",
            "date": "",
            "status": "pending",
        },
        {
            "event": "Motion to Extend PPO Filed",
            "form": "CC 383",
            "deadline_rule": "Before current PPO expiration",
            "date": "",
            "status": "pending",
        },
        {
            "event": "PPO Expires / Terminated",
            "form": "N/A",
            "deadline_rule": "Per order or 182 days if not extended",
            "date": "",
            "status": "pending",
        },
    ]

    return {
        "case_number": case_number,
        "lane": "D",
        "lane_name": "PPO / Protection Orders",
        "court": "14th Circuit Court — Family Division",
        "county": "Muskegon",
        "judge": "Hon. Jenny L. McNeill",
        "milestones": milestones,
        "notes": "",
    }
