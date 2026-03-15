"""
case_intelligence: Structured case state for LitigationOS — Pigors v. Watson.

Tracks extracted facts (FE-XXX), named evidence atoms (EA-XXX), the violations
inventory (V-XXX), ranked litigation vehicles, the Mandi Martini malpractice
analysis, and the current SBNA (Single Best Next Action).

All records are plain dataclasses that can be serialised to JSON / SQLite by
the init_db machinery.  The module also exposes ``seed_db(conn)`` which
inserts every record into a copilot_state.db connection that already has the
``case_intelligence`` tables created by init_db.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, asdict, field
from typing import List, Optional


# ── Extracted facts ───────────────────────────────────────────────────────────

@dataclass
class ExtractedFact:
    """A single fact extracted from case materials.

    fact_id      : Identifier, e.g. "FE-032".
    summary      : Short description of the fact.
    fact_state   : "UNVERIFIED" | "VERIFIED" | "DISPUTED".
    proof_needed : What documentation is needed to verify this fact.
    significance : Free-text legal significance note (may be empty).
    evidence_refs: EA-XXX identifiers linked to this fact.
    """

    fact_id: str
    summary: str
    fact_state: str
    proof_needed: str = ""
    significance: str = ""
    evidence_refs: List[str] = field(default_factory=list)


EXTRACTED_FACTS: List[ExtractedFact] = [
    ExtractedFact(
        fact_id="FE-032",
        summary="Prior attorney was Mandi Martini.",
        fact_state="UNVERIFIED",
        proof_needed="Retainer agreement / appearance records.",
        significance="Establishes attorney-client relationship for malpractice claim.",
    ),
    ExtractedFact(
        fact_id="FE-033",
        summary="Mandi Martini never objected at hearings, never helped defend.",
        fact_state="UNVERIFIED",
        proof_needed="Hearing transcripts confirming absence of objections.",
        significance=(
            "Potential legal malpractice (negligent representation). No constitutional right "
            "to effective counsel in civil cases, but a malpractice claim lies if negligence "
            "caused loss of rights."
        ),
    ),
    ExtractedFact(
        fact_id="FE-034",
        summary=(
            "Email from Mandi Martini: 'do not talk, the judge is in a bad mood' — "
            "sent before the 4th PPO show cause hearing."
        ),
        fact_state="UNVERIFIED",
        proof_needed="The email itself (PRESERVE IMMEDIATELY).",
        significance=(
            "Evidence of judicial bias (attorney perceived it), evidence of ineffective "
            "representation (strategy was silence, not defence), consciousness of problem "
            "combined with failure to act."
        ),
        evidence_refs=["EA-001"],
    ),
    ExtractedFact(
        fact_id="FE-035",
        summary="Plaintiff called CPS regarding Lincoln's condition.",
        fact_state="UNVERIFIED",
        proof_needed="Date of call, CPS report number, outcome of investigation.",
    ),
    ExtractedFact(
        fact_id="FE-036",
        summary="Plaintiff made a police report regarding Lincoln's injuries (bruises + burn on buttocks).",
        fact_state="UNVERIFIED",
        proof_needed="Police report number, date, agency, photographs.",
        evidence_refs=["EA-008"],
    ),
    ExtractedFact(
        fact_id="FE-037",
        summary="Plaintiff photographed Lincoln showing bruises and a burn on his buttocks; he could barely walk.",
        fact_state="UNVERIFIED",
        proof_needed="The photographs with dates/metadata (PRESERVE IMMEDIATELY).",
        significance=(
            "If Lincoln was being harmed in Emily's care and the court removed Plaintiff's "
            "parenting time instead of investigating Emily, the court failed to protect the "
            "child and the custody decision put the child in danger."
        ),
        evidence_refs=["EA-005"],
    ),
    ExtractedFact(
        fact_id="FE-038",
        summary="Lincoln (age ~2) refused to go back to Emily's house.",
        fact_state="UNVERIFIED",
        proof_needed="Plaintiff's detailed account: what Lincoln said/did, any witnesses.",
        significance="Behavioural signal consistent with harm in Emily's care.",
    ),
    ExtractedFact(
        fact_id="FE-039",
        summary="At the 6th and 7th PPO show causes, Plaintiff was jailed for 45 days.",
        fact_state="UNVERIFIED",
        proof_needed="Dates of incarceration, court orders.",
        significance="45 days for AppClose birthday messages is disproportionate (V-008).",
    ),
    ExtractedFact(
        fact_id="FE-040",
        summary="Before the 45-day jailing, Plaintiff was jailed for 2 weeks starting the day before Thanksgiving.",
        fact_state="UNVERIFIED",
        proof_needed="Date, year, court order.",
        significance="Jailed day before Thanksgiving — separated from young child over the holidays. Relevant to damages.",
    ),
    ExtractedFact(
        fact_id="FE-041",
        summary=(
            "5th PPO show cause was DISMISSED because Emily's father threw service paperwork "
            "through Plaintiff's car window at a parenting exchange."
        ),
        fact_state="UNVERIFIED",
        proof_needed="Court order of dismissal, documentation of improper service.",
        significance=(
            "Improper service = show cause void. Emily's father was physically aggressive "
            "at exchange. Pattern: Emily's family are active participants in the harassment campaign."
        ),
    ),
    ExtractedFact(
        fact_id="FE-042",
        summary="Emily and her family withheld Lincoln from Plaintiff for over a month before the 5th show cause.",
        fact_state="UNVERIFIED",
        proof_needed="Dates, parenting-time order in effect, documentation of withholding.",
        significance=(
            "If Emily withheld the child in violation of a court order she was in contempt. "
            "Was contempt ever pursued against her?"
        ),
    ),
    ExtractedFact(
        fact_id="FE-043",
        summary=(
            "Plaintiff has emails from Judge McNeill's secretary stating Plaintiff is NOT ALLOWED "
            "to submit evidence to the clerk, but Emily IS allowed to."
        ),
        fact_state="UNVERIFIED",
        proof_needed="The emails (PRESERVE IMMEDIATELY).",
        significance=(
            "Clerk's office is REQUIRED to accept filings from ALL parties (MCR 1.109). "
            "A judge's secretary has no authority to block a party. Written record of unequal "
            "treatment. Equal protection (MI Const Art 1 §2; US Const Amend 14) and due process "
            "(MI Const Art 1 §17) violations. JTC complaint material (MCJ Canon 3, Rules 3.4, 3.6)."
        ),
        evidence_refs=["EA-002"],
    ),
    ExtractedFact(
        fact_id="FE-044",
        summary=(
            "Plaintiff has text messages from Emily's mother and brother stating they were going "
            "to make sure Plaintiff never saw his son again."
        ),
        fact_state="UNVERIFIED",
        proof_needed="The text messages (PRESERVE — screenshot with metadata).",
        significance=(
            "Direct evidence of coordinated campaign, intent, civil conspiracy, tortious "
            "interference with parental relationship, IIED."
        ),
        evidence_refs=["EA-003"],
    ),
    ExtractedFact(
        fact_id="FE-045",
        summary=(
            "Plaintiff has audio recording of Emily's father stating he would ensure Plaintiff "
            "never saw his son again."
        ),
        fact_state="UNVERIFIED",
        proof_needed=(
            "The recording, circumstances of how it was recorded, whether Plaintiff was a party "
            "to the conversation (one-party consent required under Michigan law)."
        ),
        significance=(
            "If recorded legally (Plaintiff was a party): explosive evidence. Three family members "
            "have explicitly stated the goal of permanent separation — a documented conspiracy."
        ),
        evidence_refs=["EA-004"],
    ),
    ExtractedFact(
        fact_id="FE-046",
        summary="The jailings caused Plaintiff to lose 2 homes and 3 jobs.",
        fact_state="UNVERIFIED",
        proof_needed="Employment records showing termination dates, housing records, dates of each jailing.",
        significance=(
            "Concrete, documentable economic damages: lost wages, lost housing, lost liberty, "
            "lost parent-child relationship, emotional distress, reputational harm."
        ),
        evidence_refs=["EA-009", "EA-010"],
    ),
]


# ── Named evidence atoms ──────────────────────────────────────────────────────

@dataclass
class NamedEvidenceAtom:
    """A specific, named piece of evidence that Plaintiff possesses.

    atom_id     : Identifier, e.g. "EA-001".
    description : What this evidence is.
    atom_type   : DOCUMENT | AUDIO | PHOTO | TEXT_MESSAGE | PUBLIC_RECORD | OTHER.
    relevance   : Legal relevance summary.
    priority    : CRITICAL | HIGH | MEDIUM.
    preserve_note: Action note (e.g. 'PRESERVE NOW', 'obtain via FOIA').
    fact_refs   : FE-XXX identifiers that reference this atom.
    """

    atom_id: str
    description: str
    atom_type: str
    relevance: str
    priority: str
    preserve_note: str = ""
    fact_refs: List[str] = field(default_factory=list)


NAMED_EVIDENCE_ATOMS: List[NamedEvidenceAtom] = [
    NamedEvidenceAtom(
        atom_id="EA-001",
        description="Email from Mandi Martini — 'do not talk, the judge is in a bad mood'",
        atom_type="DOCUMENT",
        relevance="Judicial bias perception by own attorney + attorney ineffectiveness.",
        priority="CRITICAL",
        preserve_note="PRESERVE NOW — screenshot and forward to multiple locations.",
        fact_refs=["FE-034"],
    ),
    NamedEvidenceAtom(
        atom_id="EA-002",
        description=(
            "Emails from Judge McNeill's secretary — Plaintiff not allowed to submit evidence "
            "to clerk; Emily IS allowed to."
        ),
        atom_type="DOCUMENT",
        relevance=(
            "Unequal treatment, due process violation, judicial misconduct — "
            "written record of discriminatory court access."
        ),
        priority="CRITICAL",
        preserve_note=(
            "PRESERVE NOW — may be the single most important document in the case."
        ),
        fact_refs=["FE-043"],
    ),
    NamedEvidenceAtom(
        atom_id="EA-003",
        description=(
            "Text messages from Emily's mother and brother — "
            "'going to make sure you never see your son again'."
        ),
        atom_type="TEXT_MESSAGE",
        relevance=(
            "Civil conspiracy, explicit intent, IIED, tortious interference with "
            "parental relationship."
        ),
        priority="CRITICAL",
        preserve_note="PRESERVE NOW — screenshot with metadata visible.",
        fact_refs=["FE-044"],
    ),
    NamedEvidenceAtom(
        atom_id="EA-004",
        description="Audio recording of Emily's father — same statements as EA-003.",
        atom_type="AUDIO",
        relevance=(
            "Third family member confirming conspiracy. If legally recorded (one-party consent), "
            "explosive evidence."
        ),
        priority="CRITICAL",
        preserve_note="PRESERVE NOW — multiple backup copies on separate media.",
        fact_refs=["FE-045"],
    ),
    NamedEvidenceAtom(
        atom_id="EA-005",
        description="Photographs of Lincoln — bruises and burn on buttocks.",
        atom_type="PHOTO",
        relevance=(
            "Documents child abuse/neglect in Emily's care; reverses narrative that Plaintiff "
            "is the danger; supports CPS report."
        ),
        priority="CRITICAL",
        preserve_note="PRESERVE NOW — back up with original metadata intact.",
        fact_refs=["FE-037"],
    ),
    NamedEvidenceAtom(
        atom_id="EA-006",
        description="Coparenting app messages — complete history.",
        atom_type="DOCUMENT",
        relevance=(
            "Shows Plaintiff was not harassing; shows birthday message context; "
            "shows Emily's communications pattern."
        ),
        priority="CRITICAL",
        preserve_note="EXPORT ENTIRE APP HISTORY NOW before it disappears.",
        fact_refs=[],
    ),
    NamedEvidenceAtom(
        atom_id="EA-007",
        description="CPS report — Plaintiff's report regarding Lincoln's injuries.",
        atom_type="PUBLIC_RECORD",
        relevance="Plaintiff reported concerns; contradicts narrative that Plaintiff is the danger.",
        priority="HIGH",
        preserve_note="Obtain copy via FOIA if needed (MCL 15.231+).",
        fact_refs=["FE-035"],
    ),
    NamedEvidenceAtom(
        atom_id="EA-008",
        description="Police report — Plaintiff's report regarding Lincoln's injuries.",
        atom_type="PUBLIC_RECORD",
        relevance="Same as EA-007.",
        priority="HIGH",
        preserve_note="Obtain copy via FOIA.",
        fact_refs=["FE-036"],
    ),
    NamedEvidenceAtom(
        atom_id="EA-009",
        description="Employment records — 3 jobs lost.",
        atom_type="DOCUMENT",
        relevance="Damages computation — lost wages from 3 terminations caused by jailings.",
        priority="HIGH",
        preserve_note="Collect termination letters, pay stubs, dates of each jailing.",
        fact_refs=["FE-046"],
    ),
    NamedEvidenceAtom(
        atom_id="EA-010",
        description="Housing records — 2 homes lost.",
        atom_type="DOCUMENT",
        relevance="Damages computation — lost housing, security deposits, homelessness periods.",
        priority="HIGH",
        preserve_note="Collect lease terminations, eviction notices, dates.",
        fact_refs=["FE-046"],
    ),
]


# ── Violations inventory ──────────────────────────────────────────────────────

@dataclass
class ViolationRecord:
    """A single documented violation.

    violation_id : Identifier, e.g. "V-001".
    category     : JUDICIAL_MISCONDUCT | DUE_PROCESS | ATTORNEY_MISCONDUCT |
                   PPO_FRAUD | ABUSE_OF_PROCESS | CHILD_SAFETY.
    summary      : Short description.
    fact_refs    : FE-XXX identifiers that document this violation.
    """

    violation_id: str
    category: str
    summary: str
    fact_refs: List[str] = field(default_factory=list)


VIOLATIONS: List[ViolationRecord] = [
    # Judicial Misconduct
    ViolationRecord("V-001", "JUDICIAL_MISCONDUCT",
                    "Judge did not personally review USB recording — staff listened instead.",
                    ["FE-024"]),
    ViolationRecord("V-002", "JUDICIAL_MISCONDUCT",
                    "Mental health evaluation directed outside the official record.",
                    ["FE-026"]),
    ViolationRecord("V-003", "JUDICIAL_MISCONDUCT",
                    "Second evaluation appeared that defendant never participated in.",
                    ["FE-028"]),
    ViolationRecord("V-004", "JUDICIAL_MISCONDUCT",
                    "Plaintiff jailed for objecting in court.",
                    ["FE-029"]),
    ViolationRecord("V-005", "JUDICIAL_MISCONDUCT",
                    "Judge and opposing party discussed forcing Plaintiff to take medication.",
                    ["FE-030"]),
    ViolationRecord("V-006", "JUDICIAL_MISCONDUCT",
                    "Secretary emails blocking Plaintiff from filing evidence with the clerk.",
                    ["FE-043"]),
    ViolationRecord("V-007", "JUDICIAL_MISCONDUCT",
                    "Emily permitted to file evidence while Plaintiff was blocked.",
                    ["FE-043"]),
    ViolationRecord("V-008", "JUDICIAL_MISCONDUCT",
                    "Disproportionate contempt — 45 days for a birthday message.",
                    ["FE-019"]),
    ViolationRecord("V-009", "JUDICIAL_MISCONDUCT",
                    "Disproportionate contempt — 2 weeks starting the day before Thanksgiving.",
                    ["FE-040"]),
    # Due Process
    ViolationRecord("V-010", "DUE_PROCESS",
                    "Plaintiff denied the right to present evidence at custody trial.",
                    ["FE-014"]),
    ViolationRecord("V-011", "DUE_PROCESS",
                    "Evidence (USB recording) used at trial without prior service on Plaintiff.",
                    ["FE-017"]),
    ViolationRecord("V-012", "DUE_PROCESS",
                    "Ex parte suspension of Plaintiff's parenting time.",
                    ["FE-021"]),
    ViolationRecord("V-013", "DUE_PROCESS",
                    "Hearsay police reports admitted at trial.",
                    ["FE-015"]),
    ViolationRecord("V-014", "DUE_PROCESS",
                    "Unequal access to the court filing system (see V-006/V-007).",
                    ["FE-043"]),
    # Attorney Misconduct
    ViolationRecord("V-015", "ATTORNEY_MISCONDUCT",
                    "Martini failed to object at hearings.",
                    ["FE-033"]),
    ViolationRecord("V-016", "ATTORNEY_MISCONDUCT",
                    "Martini advised silence based on judge's mood, not the law.",
                    ["FE-034"]),
    # PPO Fraud
    ViolationRecord("V-017", "PPO_FRAUD",
                    "PPO obtained with staged or fabricated evidence.",
                    ["FE-004"]),
    ViolationRecord("V-018", "PPO_FRAUD",
                    "Emily's mother participated in fabrication (email metadata).",
                    ["FE-005"]),
    # Abuse of Process / Harassment
    ViolationRecord("V-019", "ABUSE_OF_PROCESS",
                    "12+ police reports filed; 0 substantive arrests.",
                    ["FE-007"]),
    ViolationRecord("V-020", "ABUSE_OF_PROCESS",
                    "7 PPO show causes used as a litigation weapon.",
                    ["FE-009"]),
    ViolationRecord("V-021", "ABUSE_OF_PROCESS",
                    "Family members stated explicit intent to permanently sever parent-child relationship.",
                    ["FE-044", "FE-045"]),
    ViolationRecord("V-022", "ABUSE_OF_PROCESS",
                    "Emily withheld Lincoln from Plaintiff for over a month.",
                    ["FE-042"]),
    # Child Safety
    ViolationRecord("V-023", "CHILD_SAFETY",
                    "Bruises and burn on Lincoln documented by Plaintiff in photographs.",
                    ["FE-036", "FE-037"]),
    ViolationRecord("V-024", "CHILD_SAFETY",
                    "CPS report filed by Plaintiff — outcome unknown.",
                    ["FE-035"]),
]


# ── Litigation vehicles ────────────────────────────────────────────────────────

@dataclass
class LitigationVehicle:
    """A ranked litigation vehicle (claim / motion / complaint).

    vehicle_id   : Identifier, e.g. "RANK-01".
    rank         : Filing priority rank (1 = highest).
    tier         : Filing tier: 1 (≤30 days) | 2 (≤60 days) | 3 (≤6 months) | 4 (ongoing).
    name         : Short name.
    authority    : Primary legal authority (MCR, MCL, statute, claim type).
    court        : Target court/forum.
    basis        : List of grounds.
    evidence_needed: List of EA-XXX atom IDs required.
    assurance    : Confidence score 0–100.
    notes        : Additional notes.
    """

    vehicle_id: str
    rank: int
    tier: int
    name: str
    authority: str
    court: str
    basis: List[str]
    evidence_needed: List[str] = field(default_factory=list)
    assurance: int = 0
    notes: str = ""


LITIGATION_VEHICLES: List[LitigationVehicle] = [
    # ── Tier 1: File within 30 days ────────────────────────────────────────
    LitigationVehicle(
        vehicle_id="RANK-01",
        rank=1,
        tier=1,
        name="MCR 2.612 — Relief from Judgment",
        authority="MCR 2.612(C)(1)(c) and (C)(1)(f)",
        court="14th Circuit Court (with concurrent MCR 2.003 disqualification)",
        basis=[
            "(C)(1)(c): fraud, misrepresentation, misconduct of adverse party "
            "(fabricated PPO evidence; phantom second evaluation; unserved USB recording)",
            "(C)(1)(c): fraud upon the court (evidence routed outside official record; "
            "judge relied on staff characterisation; unequal filing access)",
            "(C)(1)(f): any other reason justifying relief — cumulative due process violations",
            "No time limit for fraud upon the court (MCR 2.612(C)(3))",
        ],
        evidence_needed=["EA-002", "EA-003", "EA-004", "EA-005"],
        assurance=62,
        notes="File WITH or BEFORE the MCR 2.003 motion.",
    ),
    LitigationVehicle(
        vehicle_id="RANK-02",
        rank=2,
        tier=1,
        name="MCR 2.003 — Judicial Disqualification of Judge McNeill",
        authority="MCR 2.003(C)(1)(a) and (C)(1)(f)",
        court="14th Circuit Court (auto-referral to Chief Judge on denial — MCR 2.003(D)(3))",
        basis=[
            "Pattern of 9 documented judicial misconduct instances",
            "Unequal treatment documented in writing (secretary emails)",
            "Same judge on both cases with apparent prejudgment",
            "Disproportionate punishment (45 days for birthday message)",
            "Evidence directed outside official record",
            "Staff reviewing evidence instead of judge",
            "Discussion of forced medication with opposing party",
        ],
        evidence_needed=["EA-002"],
        assurance=55,
        notes=(
            "Procedure: (1) file verified motion with McNeill; "
            "(2) on denial, auto-referral to chief judge; "
            "(3) on chief judge denial, leave to COA (MCR 7.205)."
        ),
    ),
    LitigationVehicle(
        vehicle_id="RANK-03",
        rank=3,
        tier=1,
        name="MCL 600.2950(14) — Motion to Terminate/Modify PPO",
        authority="MCL 600.2950(14)",
        court="14th Circuit Court",
        basis=[
            "PPO obtained by fraud (staged evidence — photos of belongings)",
            "No corroboration for poisoning/abuse allegations",
            "12 police reports → 0 arrests proves allegations meritless",
            "Mother's name on emailed photos proves coordination (EA-003)",
        ],
        evidence_needed=["EA-003"],
        assurance=50,
        notes="Vacating PPO should also vacate contempt findings predicated on PPO violations.",
    ),
    LitigationVehicle(
        vehicle_id="RANK-04",
        rank=4,
        tier=1,
        name="MCL 722.27 — Motion to Modify Custody",
        authority="MCL 722.27; MCL 722.23 (best interest factors)",
        court="14th Circuit Court",
        basis=[
            "Proper cause / change of circumstances",
            "Emily's documented pattern of false allegations",
            "Emily's family's stated intent to sever relationship (EA-003, EA-004)",
            "Lincoln's injuries in Emily's care (EA-005)",
            "Emily's withholding of child (FE-042)",
            "Plaintiff's vindication — 0 arrests on 12 reports",
            "Factor (j): Emily has zero willingness to facilitate relationship",
            "Factor (k): PPO was fraudulently obtained; actual harm evidence points to Emily's care",
        ],
        evidence_needed=["EA-003", "EA-004", "EA-005"],
        assurance=50,
    ),
    # ── Tier 2: File within 60 days ────────────────────────────────────────
    LitigationVehicle(
        vehicle_id="RANK-05",
        rank=5,
        tier=2,
        name="JTC Formal Complaint — Judge McNeill",
        authority="MCR 9.240; MCJ Canon 3, Rules 3.4, 3.6",
        court="Michigan Judicial Tenure Commission (jtc.courts.mi.gov)",
        basis=[
            "9 specific instances of judicial misconduct documented",
            "Written evidence of unequal treatment (secretary emails)",
            "Evidence routed outside official record",
            "Staff reviewing evidence instead of judge",
            "Disproportionate punishment",
            "Jailing for making an objection in court",
            "Discussion of forced medication with opposing party",
        ],
        evidence_needed=["EA-002"],
        assurance=0,
        notes="Slow process but creates official record and may prompt recusal.",
    ),
    LitigationVehicle(
        vehicle_id="RANK-06",
        rank=6,
        tier=2,
        name="AGC Complaint — Mandi Martini",
        authority="MRPC 1.1; 1.3; 1.4; 3.1",
        court="Michigan Attorney Grievance Commission (agc.michigan.gov)",
        basis=[
            "MRPC 1.1: Competence — failed to make basic objections",
            "MRPC 1.3: Diligence — passive representation",
            "MRPC 1.4: Communication — 'don't talk, judge is in a bad mood'",
            "MRPC 3.1: Failed to assert meritorious claims/defences",
        ],
        evidence_needed=["EA-001"],
        assurance=0,
        notes="Evidence: EA-001 (email) + hearing transcripts showing no objections.",
    ),
    LitigationVehicle(
        vehicle_id="RANK-07",
        rank=7,
        tier=2,
        name="FOIA Requests",
        authority="MCL 15.231+",
        court="Muskegon PD / Sheriff; CPS/DHHS; 14th Circuit administrative records",
        basis=[
            "All 12+ police reports involving Plaintiff and Emily",
            "CPS report regarding Lincoln's injuries + outcome",
            "Administrative records re: secretary instructions on evidence filing",
        ],
        evidence_needed=[],
        assurance=0,
        notes=(
            "5 business day response required (MCL 15.235(2)). "
            "File requests immediately. Fee waiver possible."
        ),
    ),
    # ── Tier 3: File within 6 months ───────────────────────────────────────
    LitigationVehicle(
        vehicle_id="RANK-08",
        rank=8,
        tier=3,
        name="Legal Malpractice — Mandi Martini",
        authority="MCL 600.5805(6) (2-year SOL from last act or discovery)",
        court="Muskegon County Circuit Court (argue for different judge)",
        basis=[
            "Attorney-client relationship established (retainer agreement / appearances)",
            "Negligent representation: failed to object to inadmissible evidence (hearsay police reports)",
            "Failed to object to unserved evidence (USB recording)",
            "Failed to file MCR 2.003 disqualification motion",
            "Failed to challenge fabricated PPO evidence",
            "Failed to object when Plaintiff denied right to present evidence",
            "Failed to raise due process objections to contempt proceedings",
            "Failed to challenge phantom second evaluation",
            "Advised silence based on judge's mood — not legal strategy",
            "Case within a case: but for negligence, better outcome was achievable",
        ],
        evidence_needed=["EA-001"],
        assurance=55,
        notes=(
            "SOL: 2 years from last act of malpractice or discovery (MCL 600.5805(6)) — "
            "need dates to compute. Explore contingency representation."
        ),
    ),
    LitigationVehicle(
        vehicle_id="RANK-09",
        rank=9,
        tier=3,
        name="State Tort Claims — Emily Watson and Family",
        authority="MCL 600.2910; MCL 600.2950; MCL 600.2907",
        court="Muskegon County Circuit Court (argue for different judge)",
        basis=[
            "Abuse of process (using PPO/show causes/police reports as weapons)",
            "Malicious prosecution (where charges were dismissed)",
            "IIED (2-year campaign of extreme and outrageous conduct)",
            "Civil conspiracy (Emily + mother + brother + father — all documented)",
            "Defamation (false statements to police, court, third parties)",
            "Tortious interference with parental relationship",
        ],
        evidence_needed=["EA-003", "EA-004"],
        assurance=60,
        notes="SOL: 2–3 years depending on specific tort.",
    ),
    LitigationVehicle(
        vehicle_id="RANK-10",
        rank=10,
        tier=3,
        name="42 U.S.C. § 1983 — Federal Civil Rights",
        authority="42 U.S.C. § 1983; § 1985; 14th Amendment",
        court="USDC Western District of Michigan (Grand Rapids)",
        basis=[
            "Deprivation of parental rights without due process (14th Amendment)",
            "Conspiracy to deprive civil rights (§ 1983 + § 1985)",
            "Against Muskegon County and individual officials (NOT judge — absolute immunity)",
        ],
        evidence_needed=["EA-002"],
        assurance=45,
        notes=(
            "SOL: 3 years from each violation. Complex — may need civil rights attorney. "
            "Seek pro bono civil rights representation (ACLU of Michigan: aclumich.org)."
        ),
    ),
    # ── Tier 4: Ongoing ────────────────────────────────────────────────────
    LitigationVehicle(
        vehicle_id="RANK-11",
        rank=11,
        tier=4,
        name="Perjury Referral — Emily Watson",
        authority="MCL 750.422",
        court="Muskegon County Prosecutor (referral via police report)",
        basis=[
            "False statements in sworn PPO petition",
        ],
        evidence_needed=[],
        assurance=0,
        notes="Outcome at prosecutor's discretion; filing creates a record.",
    ),
    LitigationVehicle(
        vehicle_id="RANK-12",
        rank=12,
        tier=4,
        name="CPS/DHHS Follow-Up — Lincoln's Safety",
        authority="MCL 722.623",
        court="Michigan DHHS / CPS (855-444-3911)",
        basis=[
            "Follow up on Plaintiff's CPS report — what was the outcome?",
            "If no investigation: escalate",
            "If investigation closed: FOIA the report",
            "If Lincoln still at risk: file new report with specific documentation (EA-005)",
        ],
        evidence_needed=["EA-005", "EA-007"],
        assurance=0,
        notes=(
            "Reporting child abuse to CPS does NOT violate the PPO. "
            "Lincoln's safety is paramount."
        ),
    ),
    LitigationVehicle(
        vehicle_id="RANK-13",
        rank=13,
        tier=4,
        name="MCL 750.539c/h — Eavesdropping Claim (USB Recording)",
        authority="MCL 750.539c (criminal); MCL 750.539h (civil)",
        court="Muskegon County Circuit Court / Prosecutor",
        basis=[
            "If Emily recorded Plaintiff's call with her father and Emily was NOT on the call",
            "One-party consent required under Michigan law",
        ],
        evidence_needed=[],
        assurance=0,
        notes="Need to determine: who recorded, who was on call, consent status.",
    ),
]


# ── Malpractice analysis ──────────────────────────────────────────────────────

@dataclass
class MalpracticeElement:
    """One element of the legal malpractice claim against Mandi Martini."""

    element: str
    status: str
    notes: str


MARTINI_MALPRACTICE = {
    "attorney": "Mandi Martini",
    "claim_type": "Legal Malpractice",
    "assurance": 55,
    "sol_authority": "MCL 600.5805(6) — 2 years from last act or discovery",
    "sol_note": "Need dates of last representation act to compute deadline.",
    # sol_deadline is None until the last-representation-act date is confirmed.
    # Once known, compute as: last_act_date + 2 years (MCL 600.5805(6)).
    "sol_deadline": None,
    "key_evidence": "EA-001 (Martini email: 'do not talk, the judge is in a bad mood')",
    "elements": [
        MalpracticeElement(
            element="(1) Attorney-client relationship",
            status="LIKELY SATISFIED",
            notes="She represented Plaintiff at multiple hearings. Proof: retainer agreement, docket appearances.",
        ),
        MalpracticeElement(
            element="(2) Negligent representation (breach of duty)",
            status="LIKELY SATISFIED",
            notes=(
                "Failed to object to inadmissible hearsay police reports; "
                "failed to object to unserved USB recording; "
                "failed to file MCR 2.003 disqualification motion; "
                "failed to challenge fabricated PPO evidence; "
                "failed to object when Plaintiff denied right to present evidence; "
                "failed to raise due process objections to contempt proceedings; "
                "failed to challenge phantom second evaluation; "
                "failed to object to evidence routed through secretary; "
                "advised silence based on judge's mood — not legal strategy. "
                "ANY ONE is malpractice; collectively devastating."
            ),
        ),
        MalpracticeElement(
            element="(3) Causation — 'case within a case'",
            status="STRONG",
            notes=(
                "With timely objections and appropriate motions, a competent attorney could have: "
                "vacated the PPO (fabricated evidence); prevented admission of hearsay police reports; "
                "required proper service of USB recording; challenged the phantom second evaluation; "
                "filed for judicial disqualification; prevented or reduced jail time; "
                "preserved parenting time; presented evidence of Emily's family's conspiracy."
            ),
        ),
        MalpracticeElement(
            element="(4) Damages",
            status="SUBSTANTIAL AND DOCUMENTABLE",
            notes=(
                "Loss of custody; loss of parenting time (227+ days); "
                "45 days incarceration; 2 weeks incarceration; additional jailings; "
                "loss of 3 jobs; loss of 2 homes; emotional distress; "
                "ongoing separation from child; attorney fees paid for ineffective representation."
            ),
        ),
    ],
}


# ── Case state ────────────────────────────────────────────────────────────────

@dataclass
class CaseState:
    """High-level case state snapshot.

    assurance            : Compilation confidence score (0–100).
    assurance_label      : Human-readable label for this score tier.
    severity             : 1–5 (5 = MAXIMUM).
    days_since_contact   : Days since Plaintiff last had contact with Lincoln.
    last_contact_date    : ISO date of last contact.
    total_violations     : Total documented violations.
    total_facts          : Total extracted facts.
    total_evidence_atoms : Total named evidence atoms.
    sbna                 : Single Best Next Action block (multi-line string).
    """

    assurance: int
    assurance_label: str
    severity: int
    days_since_contact: int
    last_contact_date: str
    total_violations: int
    total_facts: int
    total_evidence_atoms: int
    sbna: str


def _compute_days_since_contact(last_contact_iso: str) -> int:
    """Compute elapsed days from *last_contact_iso* (YYYY-MM-DD) to today (UTC)."""
    import datetime
    last = datetime.date.fromisoformat(last_contact_iso)
    today = datetime.datetime.now(datetime.timezone.utc).date()
    return max(0, (today - last).days)


# Last-contact date: July 29, 2025.
# ``days_since_contact`` is computed dynamically from ``last_contact_date``
# each time this module is imported, so it stays accurate across sessions.
_LAST_CONTACT_DATE = "2025-07-29"

CURRENT_STATE = CaseState(
    assurance=68,
    assurance_label="COMPILE → approaching PCG_CANDIDATE",
    severity=5,
    days_since_contact=_compute_days_since_contact(_LAST_CONTACT_DATE),
    last_contact_date=_LAST_CONTACT_DATE,
    total_violations=len(VIOLATIONS),
    total_facts=len(EXTRACTED_FACTS),
    total_evidence_atoms=len(NAMED_EVIDENCE_ATOMS),
    sbna=(
        "TODAY — RIGHT NOW:\n"
        "1. PRESERVE EVIDENCE:\n"
        "   □ Screenshot/forward the Martini email (EA-001)\n"
        "   □ Screenshot/forward ALL secretary emails (EA-002)\n"
        "   □ Screenshot ALL texts from Emily's family (EA-003)\n"
        "   □ Back up the audio recording (EA-004)\n"
        "   □ Back up Lincoln's photos (EA-005)\n"
        "   □ Export coparenting app (EA-006)\n"
        "   □ Store in ≥2 locations (email + cloud + USB)\n"
        "\n"
        "THIS WEEK:\n"
        "2. CALL LAKESHORE LEGAL AID: 1-888-783-8190\n"
        "3. Provide case numbers and dates\n"
        "4. Obtain court files (MCR 2.002 fee waiver if needed)\n"
        "5. Upload documents: paste secretary emails, Martini email, family texts\n"
        "\n"
        "⚠️ DO NOT violate the PPO; DO NOT contact Emily or her family;\n"
        "   DO NOT discuss strategy on social media; DO NOT destroy evidence.\n"
        "   IF Lincoln is in danger: CPS 855-444-3911 (does NOT violate PPO)."
    ),
)


# ── Legal resources ───────────────────────────────────────────────────────────

LEGAL_RESOURCES = [
    {
        "name": "Lakeshore Legal Aid",
        "phone": "1-888-783-8190",
        "website": "lakeshorelegalaid.org",
        "note": "Serves Muskegon County. Free civil legal help for low-income individuals. Family law assistance available. Call and describe your situation.",
    },
    {
        "name": "Michigan Legal Help",
        "phone": None,
        "website": "michiganlegalhelp.org",
        "note": "Self-help tools, forms, information. Free — available to all Michigan residents.",
    },
    {
        "name": "Legal Aid of Western Michigan",
        "phone": "(616) 774-0672",
        "website": None,
        "note": "May serve Muskegon County — verify. Free civil legal services for eligible individuals.",
    },
    {
        "name": "ACLU of Michigan",
        "phone": None,
        "website": "aclumich.org",
        "note": "Takes cases involving government deprivation of rights. Contact if civil rights violations are documented.",
    },
    {
        "name": "Michigan Poverty Law Program",
        "phone": None,
        "website": "mplp.org",
        "note": "May provide referrals.",
    },
    {
        "name": "State Bar of Michigan Lawyer Referral",
        "phone": "(800) 968-0738",
        "website": None,
        "note": "Some attorneys offer free initial consultation. Civil rights / family law attorneys may work on contingency.",
    },
    {
        "name": "Muskegon County Self-Help Center",
        "phone": None,
        "website": None,
        "note": "Located at the courthouse — verify if available. Can help with forms and filing procedures.",
    },
    {
        "name": "Fee Waiver (MCR 2.002 / SCAO Form MC 20)",
        "phone": None,
        "website": None,
        "note": "If you cannot afford filing fees, file an affidavit of indigency. Court MUST waive fees if you qualify.",
    },
]


# ── DB seeding ────────────────────────────────────────────────────────────────

def seed_db(conn) -> None:
    """Insert all case intelligence records into an open SQLite connection.

    The connection must already have the tables created by
    ``init_db.add_case_intelligence_schema(conn)``.

    On success, the transaction is committed.  On any error the transaction
    is rolled back and the exception is re-raised so callers can decide how
    to handle partial failure.
    """
    try:
        _seed_facts(conn)
        _seed_atoms(conn)
        _seed_violations(conn)
        _seed_vehicles(conn)
        _seed_state(conn)
        conn.commit()
    except Exception:
        conn.rollback()
        raise


def _seed_facts(conn) -> None:
    conn.executemany(
        """
        INSERT OR REPLACE INTO extracted_facts
            (fact_id, summary, fact_state, proof_needed, significance, evidence_refs_json)
        VALUES (?, ?, ?, ?, ?, ?)
        """,
        [
            (
                f.fact_id,
                f.summary,
                f.fact_state,
                f.proof_needed,
                f.significance,
                json.dumps(f.evidence_refs),
            )
            for f in EXTRACTED_FACTS
        ],
    )


def _seed_atoms(conn) -> None:
    conn.executemany(
        """
        INSERT OR REPLACE INTO named_evidence_atoms
            (atom_id, description, atom_type, relevance, priority, preserve_note, fact_refs_json)
        VALUES (?, ?, ?, ?, ?, ?, ?)
        """,
        [
            (
                a.atom_id,
                a.description,
                a.atom_type,
                a.relevance,
                a.priority,
                a.preserve_note,
                json.dumps(a.fact_refs),
            )
            for a in NAMED_EVIDENCE_ATOMS
        ],
    )


def _seed_violations(conn) -> None:
    conn.executemany(
        """
        INSERT OR REPLACE INTO violations_inventory
            (violation_id, category, summary, fact_refs_json)
        VALUES (?, ?, ?, ?)
        """,
        [
            (
                v.violation_id,
                v.category,
                v.summary,
                json.dumps(v.fact_refs),
            )
            for v in VIOLATIONS
        ],
    )


def _seed_vehicles(conn) -> None:
    conn.executemany(
        """
        INSERT OR REPLACE INTO litigation_vehicles
            (vehicle_id, rank, tier, name, authority, court,
             basis_json, evidence_needed_json, assurance, notes)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        [
            (
                v.vehicle_id,
                v.rank,
                v.tier,
                v.name,
                v.authority,
                v.court,
                json.dumps(v.basis),
                json.dumps(v.evidence_needed),
                v.assurance,
                v.notes,
            )
            for v in LITIGATION_VEHICLES
        ],
    )


def _seed_state(conn) -> None:
    s = CURRENT_STATE
    conn.execute(
        """
        INSERT OR REPLACE INTO case_state
            (id, assurance, assurance_label, severity, days_since_contact,
             last_contact_date, total_violations, total_facts, total_evidence_atoms, sbna)
        VALUES (1, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            s.assurance,
            s.assurance_label,
            s.severity,
            s.days_since_contact,
            s.last_contact_date,
            s.total_violations,
            s.total_facts,
            s.total_evidence_atoms,
            s.sbna,
        ),
    )
