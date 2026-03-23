"""JTC Formal Complaint Package Generator — Judicial Tenure Commission filings.

Generates formal complaints to the Michigan Judicial Tenure Commission (JTC)
against judicial officers for misconduct.  Supports the full complaint lifecycle:
violation cataloguing, severity scoring, pattern analysis, exhibit indexing,
cover-letter generation, and completeness validation per JTC Rules 1-15.

Michigan Constitution Art. 6, §30 grants the JTC authority to investigate
and recommend discipline for judicial misconduct.  MCR 9.104-9.125 govern
the procedural rules.  This engine produces complaint packages that conform
to JTC filing requirements and Michigan Code of Judicial Conduct canons.
"""

from __future__ import annotations

import logging
import re
import textwrap
from datetime import date, datetime
from enum import Enum
from typing import Any, Optional, Sequence

from pydantic import BaseModel, ConfigDict, Field, field_validator

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

VIOLATION_CATEGORIES: tuple[str, ...] = (
    "undisclosed_conflict",
    "ex_parte_communications",
    "bias_pattern",
    "denial_of_due_process",
    "abuse_of_contempt",
    "failure_to_follow_law",
    "demeanor_violations",
    "retaliation",
)

CANON_MAP: dict[str, dict[str, str]] = {
    "undisclosed_conflict": {
        "canon": "Canon 3(C)(1)",
        "subrule": "Canon 3(C)(1)(d)(i)",
        "title": "Disqualification — Undisclosed Familial Conflict of Interest",
        "description": (
            "A judge shall disqualify himself or herself in a proceeding in "
            "which the judge's impartiality might reasonably be questioned, "
            "including instances where the judge's spouse or a member of the "
            "spouse's family has an interest that could be substantially "
            "affected by the outcome."
        ),
        "mcr": "MCR 2.003(C)(1)(b)",
    },
    "ex_parte_communications": {
        "canon": "Canon 3(A)(4)",
        "subrule": "Canon 3(A)(4)",
        "title": "Prohibition on Ex Parte Communications",
        "description": (
            "A judge shall not initiate, permit, or consider ex parte "
            "communications, or consider other communications made to the "
            "judge outside the presence of the parties."
        ),
        "mcr": "MCR 2.003(C)(1)(a)",
    },
    "bias_pattern": {
        "canon": "Canon 3(A)(5)",
        "subrule": "Canon 3(A)(5)",
        "title": "Impartiality and Fairness",
        "description": (
            "A judge shall perform judicial duties without bias or prejudice "
            "and shall not manifest, by words or conduct, bias or prejudice "
            "based upon any factor."
        ),
        "mcr": "MCR 2.003(C)(1)(b)",
    },
    "denial_of_due_process": {
        "canon": "Canon 3(A)(1)",
        "subrule": "Canon 3(A)(1)",
        "title": "Faithful Execution of Judicial Duties",
        "description": (
            "A judge shall be faithful to the law and maintain professional "
            "competence in it, including providing adequate notice and "
            "opportunity to be heard."
        ),
        "mcr": "MCR 2.119",
    },
    "abuse_of_contempt": {
        "canon": "Canon 3(A)(3)",
        "subrule": "Canon 3(A)(3)",
        "title": "Improper Use of Contempt Power",
        "description": (
            "A judge shall exercise contempt power only when necessary to "
            "maintain order and decorum, not as a punitive tool or to "
            "suppress legitimate legal arguments."
        ),
        "mcr": "MCR 3.606",
    },
    "failure_to_follow_law": {
        "canon": "Canon 3(A)(1)",
        "subrule": "Canon 3(A)(1)",
        "title": "Failure to Follow Binding Precedent or Court Rules",
        "description": (
            "A judge shall be faithful to the law and maintain professional "
            "competence in it. Persistent failure to follow binding precedent "
            "or mandatory court rules constitutes misconduct."
        ),
        "mcr": "MCR 2.003(D)",
    },
    "demeanor_violations": {
        "canon": "Canon 3(A)(3)",
        "subrule": "Canon 3(A)(3)",
        "title": "Improper Demeanor on the Bench",
        "description": (
            "A judge shall be patient, dignified, and courteous to litigants, "
            "jurors, witnesses, lawyers, and others with whom the judge deals "
            "in an official capacity."
        ),
        "mcr": "",
    },
    "retaliation": {
        "canon": "Canon 2(A)",
        "subrule": "Canon 2(A)",
        "title": "Retaliation for Exercise of Legal Rights",
        "description": (
            "A judge shall respect and comply with the law and shall act at "
            "all times in a manner that promotes public confidence in the "
            "judiciary. Retaliating against a party for exercising legal "
            "rights undermines the integrity of the judiciary."
        ),
        "mcr": "MCR 2.003(D)",
    },
}

SEVERITY_WEIGHTS: dict[str, float] = {
    "undisclosed_conflict": 1.5,
    "ex_parte_communications": 1.3,
    "bias_pattern": 1.2,
    "denial_of_due_process": 1.2,
    "abuse_of_contempt": 1.1,
    "failure_to_follow_law": 1.0,
    "demeanor_violations": 0.8,
    "retaliation": 1.3,
}

JTC_ADDRESS = textwrap.dedent("""\
    Michigan Judicial Tenure Commission
    3034 W. Grand Blvd., Suite 8-450
    Detroit, MI 48202
    Phone: (313) 875-5110
    Fax: (313) 875-5111""")

COMPLAINANT_INFO: dict[str, str] = {
    "name": "Andrew James Pigors",
    "address": "1977 Whitehall Road, Lot 17",
    "city_state_zip": "North Muskegon, MI 49445",
    "phone": "(231) 903-5690",
    "email": "andrewjpigors@gmail.com",
}

SUBJECT_JUDGE_INFO: dict[str, str] = {
    "name": "Hon. Jenny L. McNeill",
    "court": "14th Circuit Court, Family Division",
    "county": "Muskegon County",
    "state": "Michigan",
}

CASE_INFO: dict[str, str] = {
    "case_number": "2024-001507-DC",
    "caption": "Pigors v. Watson",
    "court": "14th Circuit Court, Family Division, Muskegon County",
    "defendant": "Emily A. Watson",
    "defendant_address": "2160 Garland Drive, Norton Shores, MI 49441",
}


# ---------------------------------------------------------------------------
# Pydantic Models
# ---------------------------------------------------------------------------

class JTCViolation(BaseModel):
    """A single JTC-relevant judicial misconduct violation."""

    violation_type: str
    canon_violated: str
    description: str
    date: Optional[str] = None
    evidence_refs: list[str] = Field(default_factory=list)
    severity: int = Field(default=5, ge=1, le=10)

    model_config = ConfigDict(from_attributes=True)

    @field_validator("violation_type")
    @classmethod
    def validate_violation_type(cls, v: str) -> str:
        if v not in VIOLATION_CATEGORIES:
            raise ValueError(
                f"Invalid violation_type '{v}'. "
                f"Must be one of {VIOLATION_CATEGORIES}"
            )
        return v

    @field_validator("severity")
    @classmethod
    def validate_severity(cls, v: int) -> int:
        if not 1 <= v <= 10:
            raise ValueError("severity must be between 1 and 10")
        return v


class ExhibitEntry(BaseModel):
    """A single exhibit in the complaint package."""

    exhibit_id: str
    title: str
    description: Optional[str] = None
    bates_range: Optional[str] = None
    file_path: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)


class PatternAnalysis(BaseModel):
    """Analysis of violation patterns showing systematic misconduct."""

    violation_count: int = 0
    date_range: Optional[str] = None
    pattern_description: str = ""
    escalation_timeline: list[str] = Field(default_factory=list)
    severity_score: float = 0.0

    model_config = ConfigDict(from_attributes=True)


class SeverityResult(BaseModel):
    """Severity scoring breakdown for a set of violations."""

    total_score: float = 0.0
    max_individual: int = 0
    category_scores: dict[str, float] = Field(default_factory=dict)
    risk_level: str = "low"

    model_config = ConfigDict(from_attributes=True)


class ValidationResult(BaseModel):
    """Result of complaint completeness validation."""

    is_valid: bool = False
    errors: list[str] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)
    sections_present: list[str] = Field(default_factory=list)
    sections_missing: list[str] = Field(default_factory=list)

    model_config = ConfigDict(from_attributes=True)


class JTCComplaint(BaseModel):
    """Complete JTC formal complaint package."""

    complainant_info: dict[str, str] = Field(default_factory=dict)
    subject_judge: dict[str, str] = Field(default_factory=dict)
    case_info: dict[str, str] = Field(default_factory=dict)
    violations: list[JTCViolation] = Field(default_factory=list)
    prayer_for_relief: str = ""
    exhibits: list[ExhibitEntry] = Field(default_factory=list)
    generated_at: Optional[datetime] = Field(default_factory=datetime.now)

    model_config = ConfigDict(from_attributes=True)


# ---------------------------------------------------------------------------
# Required Sections for Validation
# ---------------------------------------------------------------------------

REQUIRED_SECTIONS: tuple[str, ...] = (
    "COVER PAGE",
    "COMPLAINANT INFORMATION",
    "SUBJECT JUDGE",
    "FACTUAL ALLEGATIONS",
    "VIOLATIONS",
    "PRAYER FOR RELIEF",
    "VERIFICATION",
)


# ---------------------------------------------------------------------------
# Engine
# ---------------------------------------------------------------------------

class JTCComplaintGenerator:
    """Generates formal complaint packages for the Michigan Judicial Tenure Commission.

    Produces complete JTC complaint documents including cover pages, violation
    sections with Canon citations, pattern analysis, exhibit indexes, cover
    letters, and completeness validation per JTC Rules 1-15.

    The generator is stateless — all case-specific data is passed via method
    arguments.  Verified party information is drawn from module-level constants
    to prevent hallucination of names, addresses, or bar numbers.
    """

    # ------------------------------------------------------------------ init
    def __init__(self) -> None:
        logger.info("JTCComplaintGenerator initialized")

    # ---------------------------------------------- public: violation helpers
    def list_violation_categories(self) -> list[dict[str, str]]:
        """Return all JTC-relevant violation categories with Canon mappings.

        Returns:
            List of dicts with keys ``type``, ``canon``, ``title``,
            ``description``, and ``mcr``.
        """
        result: list[dict[str, str]] = []
        for vtype in VIOLATION_CATEGORIES:
            info = CANON_MAP[vtype]
            result.append({
                "type": vtype,
                "canon": info["canon"],
                "subrule": info["subrule"],
                "title": info["title"],
                "description": info["description"],
                "mcr": info["mcr"],
            })
        return result

    def build_violation_section(
        self,
        violation_type: str,
        facts: str,
        evidence: list[str] | None = None,
    ) -> str:
        """Build a formatted violation section with Canon citations.

        Args:
            violation_type: One of ``VIOLATION_CATEGORIES``.
            facts: Narrative description of the factual basis.
            evidence: Optional list of evidence reference strings.

        Returns:
            Formatted multi-line string ready for insertion into complaint.

        Raises:
            ValueError: If *violation_type* is not recognised.
        """
        if violation_type not in VIOLATION_CATEGORIES:
            raise ValueError(
                f"Invalid violation_type '{violation_type}'. "
                f"Must be one of {VIOLATION_CATEGORIES}"
            )

        info = CANON_MAP[violation_type]
        evidence = evidence or []

        lines: list[str] = [
            f"## {info['title']}",
            f"**Canon Violated:** {info['canon']}",
        ]
        if info.get("subrule") and info["subrule"] != info["canon"]:
            lines.append(f"**Specific Subrule:** {info['subrule']}")
        if info.get("mcr"):
            lines.append(f"**Court Rule:** {info['mcr']}")
        lines.append("")
        lines.append(f"**Standard:** {info['description']}")
        lines.append("")
        lines.append("**Factual Basis:**")
        lines.append("")
        lines.append(facts)
        lines.append("")

        if evidence:
            lines.append("**Supporting Evidence:**")
            for i, ref in enumerate(evidence, 1):
                lines.append(f"  {i}. {ref}")
            lines.append("")

        return "\n".join(lines)

    # ---------------------------------------------- public: exhibit index
    def generate_exhibit_list(
        self,
        evidence_refs: list[dict[str, str]],
    ) -> list[ExhibitEntry]:
        """Generate an organized exhibit index for the complaint.

        Args:
            evidence_refs: List of dicts with keys ``title``, optionally
                ``description``, ``bates_range``, ``file_path``.

        Returns:
            Ordered list of ``ExhibitEntry`` models with sequential IDs.
        """
        exhibits: list[ExhibitEntry] = []
        for i, ref in enumerate(evidence_refs, 1):
            exhibit_id = f"Exhibit {chr(64 + i)}" if i <= 26 else f"Exhibit {i}"
            exhibits.append(ExhibitEntry(
                exhibit_id=exhibit_id,
                title=ref.get("title", f"Exhibit {i}"),
                description=ref.get("description"),
                bates_range=ref.get("bates_range"),
                file_path=ref.get("file_path"),
            ))
        return exhibits

    # ---------------------------------------------- public: cover letter
    def generate_cover_letter(
        self,
        *,
        violation_count: int = 0,
        primary_violation: str = "undisclosed_conflict",
    ) -> str:
        """Generate a cover letter to the JTC.

        Args:
            violation_count: Number of violations in the complaint.
            primary_violation: Lead violation category.

        Returns:
            Formatted cover letter string.
        """
        today = date.today().strftime("%B %d, %Y")
        primary_title = CANON_MAP.get(primary_violation, {}).get(
            "title", "Judicial Misconduct"
        )

        letter = textwrap.dedent(f"""\
            {COMPLAINANT_INFO['name']}
            {COMPLAINANT_INFO['address']}
            {COMPLAINANT_INFO['city_state_zip']}
            {COMPLAINANT_INFO['phone']}
            {COMPLAINANT_INFO['email']}

            {today}

            {JTC_ADDRESS}

            RE: Formal Complaint Against {SUBJECT_JUDGE_INFO['name']}
                {SUBJECT_JUDGE_INFO['court']}, {SUBJECT_JUDGE_INFO['county']}
                Case No. {CASE_INFO['case_number']} — {CASE_INFO['caption']}

            Dear Members of the Judicial Tenure Commission:

            I, {COMPLAINANT_INFO['name']}, respectfully submit this formal complaint \
            against {SUBJECT_JUDGE_INFO['name']} of the {SUBJECT_JUDGE_INFO['court']}, \
            {SUBJECT_JUDGE_INFO['county']}, {SUBJECT_JUDGE_INFO['state']}.

            This complaint details {violation_count} violation(s) of the Michigan Code \
            of Judicial Conduct, with the primary allegation being {primary_title}. \
            The complaint is supported by documentary evidence referenced in the \
            attached exhibit index.

            The subject judge has presided over the above-captioned family law matter \
            since 2024. As detailed in the attached complaint, the judge has engaged \
            in a pattern of conduct that violates multiple Canons of the Michigan Code \
            of Judicial Conduct and undermines the integrity of the judiciary.

            I respectfully request that the Commission investigate these allegations, \
            conduct a public hearing pursuant to MCR 9.115, and impose appropriate \
            discipline.

            I affirm under penalty of perjury that the facts stated herein and in \
            the attached complaint are true and correct to the best of my knowledge, \
            information, and belief.

            Respectfully submitted,


            ____________________________________
            {COMPLAINANT_INFO['name']}
            {COMPLAINANT_INFO['address']}
            {COMPLAINANT_INFO['city_state_zip']}
            {COMPLAINANT_INFO['phone']}
            {COMPLAINANT_INFO['email']}
            Date: {today}""")

        return letter

    # ---------------------------------------------- public: pattern analysis
    def analyze_pattern(
        self,
        violations: list[JTCViolation],
    ) -> PatternAnalysis:
        """Analyse violations for patterns of systematic misconduct.

        Groups violations by category, builds an escalation timeline, and
        computes a composite severity score.

        Args:
            violations: List of ``JTCViolation`` instances.

        Returns:
            ``PatternAnalysis`` with counts, timeline, and severity.
        """
        if not violations:
            return PatternAnalysis(
                violation_count=0,
                pattern_description="No violations provided for analysis.",
                severity_score=0.0,
            )

        # Sort by date for timeline
        dated = sorted(
            [v for v in violations if v.date],
            key=lambda v: v.date or "",
        )
        dates = [v.date for v in dated if v.date]
        date_range = f"{dates[0]} to {dates[-1]}" if len(dates) >= 2 else (
            dates[0] if dates else "No dates available"
        )

        # Category grouping
        categories: dict[str, int] = {}
        for v in violations:
            categories[v.violation_type] = categories.get(v.violation_type, 0) + 1

        # Escalation timeline
        timeline: list[str] = []
        for v in dated:
            info = CANON_MAP.get(v.violation_type, {})
            title = info.get("title", v.violation_type)
            timeline.append(f"{v.date}: {title} (severity {v.severity}/10)")

        # Pattern description
        top_categories = sorted(categories.items(), key=lambda x: x[1], reverse=True)
        pattern_parts: list[str] = []
        for cat, count in top_categories:
            info = CANON_MAP.get(cat, {})
            title = info.get("title", cat)
            pattern_parts.append(f"{count} instance(s) of {title}")

        conflict_present = "undisclosed_conflict" in categories
        pattern_desc = (
            "Analysis reveals a pattern of systematic judicial misconduct "
            f"spanning {len(violations)} documented violation(s) across "
            f"{len(categories)} categor{'y' if len(categories) == 1 else 'ies'}. "
        )
        if conflict_present:
            pattern_desc += (
                "The undisclosed familial conflict of interest (Berry-McNeill "
                "connection) is the foundational violation, as it taints the "
                "impartiality of every ruling made in this case. "
            )
        pattern_desc += "Breakdown: " + "; ".join(pattern_parts) + "."

        # Composite severity
        severity_score = self.calculate_severity(violations).total_score

        return PatternAnalysis(
            violation_count=len(violations),
            date_range=date_range,
            pattern_description=pattern_desc,
            escalation_timeline=timeline,
            severity_score=severity_score,
        )

    # ---------------------------------------------- public: severity scoring
    def calculate_severity(
        self,
        violations: list[JTCViolation],
    ) -> SeverityResult:
        """Calculate severity scores for a set of violations.

        Each violation's base severity (1-10) is multiplied by a category
        weight.  The total is the sum of weighted scores.  Risk level is
        derived from the total: ≥30 critical, ≥20 high, ≥10 moderate,
        else low.

        Args:
            violations: List of ``JTCViolation`` instances.

        Returns:
            ``SeverityResult`` with total, max, per-category, and risk level.
        """
        if not violations:
            return SeverityResult(
                total_score=0.0,
                max_individual=0,
                category_scores={},
                risk_level="low",
            )

        category_scores: dict[str, float] = {}
        max_individual = 0

        for v in violations:
            weight = SEVERITY_WEIGHTS.get(v.violation_type, 1.0)
            weighted = v.severity * weight
            category_scores[v.violation_type] = (
                category_scores.get(v.violation_type, 0.0) + weighted
            )
            if v.severity > max_individual:
                max_individual = v.severity

        total = sum(category_scores.values())

        if total >= 30:
            risk_level = "critical"
        elif total >= 20:
            risk_level = "high"
        elif total >= 10:
            risk_level = "moderate"
        else:
            risk_level = "low"

        return SeverityResult(
            total_score=round(total, 2),
            max_individual=max_individual,
            category_scores={k: round(v, 2) for k, v in category_scores.items()},
            risk_level=risk_level,
        )

    # ---------------------------------------------- public: validation
    def validate_complaint(self, complaint_text: str) -> ValidationResult:
        """Check complaint text for completeness per JTC rules.

        Scans for required sections, minimum content, and structural
        requirements.

        Args:
            complaint_text: Full complaint document text.

        Returns:
            ``ValidationResult`` with pass/fail, errors, and warnings.
        """
        errors: list[str] = []
        warnings: list[str] = []
        sections_present: list[str] = []
        sections_missing: list[str] = []

        if not complaint_text or not complaint_text.strip():
            return ValidationResult(
                is_valid=False,
                errors=["Complaint text is empty"],
                sections_missing=list(REQUIRED_SECTIONS),
            )

        text_upper = complaint_text.upper()

        for section in REQUIRED_SECTIONS:
            if section in text_upper:
                sections_present.append(section)
            else:
                sections_missing.append(section)
                errors.append(f"Missing required section: {section}")

        # Check for complainant identification
        if COMPLAINANT_INFO["name"].upper() not in text_upper:
            errors.append("Complainant name not found in complaint")

        # Check for subject judge identification
        if "MCNEILL" not in text_upper:
            errors.append("Subject judge name not found in complaint")

        # Check for case number
        if CASE_INFO["case_number"] not in complaint_text:
            errors.append("Case number not found in complaint")

        # Check for at least one Canon citation
        if "CANON" not in text_upper:
            errors.append("No Canon citations found in complaint")

        # Check for verification / signature
        if "PENALTY OF PERJURY" not in text_upper:
            warnings.append(
                "Verification statement (under penalty of perjury) not found"
            )

        # Check minimum length (JTC complaints should be substantive)
        word_count = len(complaint_text.split())
        if word_count < 200:
            warnings.append(
                f"Complaint is only {word_count} words — may be insufficient "
                "for JTC review"
            )

        is_valid = len(errors) == 0

        return ValidationResult(
            is_valid=is_valid,
            errors=errors,
            warnings=warnings,
            sections_present=sections_present,
            sections_missing=sections_missing,
        )

    # ---------------------------------------------- public: JTC contact info
    @staticmethod
    def get_jtc_contact_info() -> dict[str, str]:
        """Return JTC address and filing instructions.

        Returns:
            Dict with ``address``, ``phone``, ``fax``, ``filing_method``,
            and ``instructions``.
        """
        return {
            "address": (
                "Michigan Judicial Tenure Commission, "
                "3034 W. Grand Blvd., Suite 8-450, Detroit, MI 48202"
            ),
            "phone": "(313) 875-5110",
            "fax": "(313) 875-5111",
            "filing_method": "Mail or personal delivery",
            "instructions": (
                "Complaints must be in writing, signed by the complainant, "
                "and include: (1) the name and address of the complainant; "
                "(2) the name of the judge; (3) the court and county; "
                "(4) a description of the alleged misconduct with specific "
                "dates and facts; (5) names of witnesses; (6) copies of "
                "relevant documents. Per JTC Rule 3, complaints are "
                "confidential until formal proceedings are initiated."
            ),
        }

    # ---------------------------------------------- public: main generator
    def generate_complaint(
        self,
        violations: list[JTCViolation],
        evidence_refs: list[dict[str, str]] | None = None,
    ) -> str:
        """Generate a complete JTC formal complaint document.

        Produces a multi-section document containing all required JTC
        filing components: cover page, complainant/judge identification,
        factual allegations, Canon-organised violation sections, pattern
        analysis, prayer for relief, exhibit list, and verification.

        The Berry-McNeill undisclosed conflict is automatically promoted
        to the lead violation when present.

        Args:
            violations: List of ``JTCViolation`` instances.
            evidence_refs: Optional list of evidence dicts for exhibit index.

        Returns:
            Complete complaint document as a single formatted string.

        Raises:
            ValueError: If *violations* is empty.
        """
        if not violations:
            raise ValueError("At least one violation is required to generate a complaint")

        evidence_refs = evidence_refs or []

        # Promote undisclosed_conflict to lead position
        sorted_violations = sorted(
            violations,
            key=lambda v: (
                0 if v.violation_type == "undisclosed_conflict" else 1,
                -v.severity,
            ),
        )

        today = date.today().strftime("%B %d, %Y")
        exhibits = self.generate_exhibit_list(evidence_refs)
        pattern = self.analyze_pattern(sorted_violations)
        severity = self.calculate_severity(sorted_violations)

        sections: list[str] = []

        # --- Cover Page ---
        sections.append(self._build_cover_page(today))

        # --- Complainant Information ---
        sections.append(self._build_complainant_section())

        # --- Subject Judge ---
        sections.append(self._build_subject_judge_section())

        # --- Factual Allegations ---
        sections.append(self._build_factual_allegations(sorted_violations))

        # --- Violations (organised by Canon) ---
        sections.append(self._build_violations_section(sorted_violations))

        # --- Pattern Analysis ---
        sections.append(self._build_pattern_section(pattern, severity))

        # --- Prayer for Relief ---
        sections.append(self._build_prayer_for_relief())

        # --- Exhibit List ---
        if exhibits:
            sections.append(self._build_exhibit_section(exhibits))

        # --- Verification ---
        sections.append(self._build_verification(today))

        return "\n\n".join(sections)

    # ---------------------------------------------- private: section builders
    def _build_cover_page(self, today: str) -> str:
        return textwrap.dedent(f"""\
            {'=' * 70}
            COVER PAGE
            {'=' * 70}

            BEFORE THE MICHIGAN JUDICIAL TENURE COMMISSION

            FORMAL COMPLAINT

            Complainant: {COMPLAINANT_INFO['name']}
            Subject Judge: {SUBJECT_JUDGE_INFO['name']}
            Court: {SUBJECT_JUDGE_INFO['court']}
            County: {SUBJECT_JUDGE_INFO['county']}
            Case Reference: {CASE_INFO['case_number']} — {CASE_INFO['caption']}

            Date Filed: {today}

            Filed Pursuant To:
              Michigan Constitution Art. 6, §30
              MCR 9.104-9.125
              JTC Rules 1-15
              Michigan Code of Judicial Conduct""")

    def _build_complainant_section(self) -> str:
        return textwrap.dedent(f"""\
            {'=' * 70}
            COMPLAINANT INFORMATION
            {'=' * 70}

            Name:    {COMPLAINANT_INFO['name']}
            Address: {COMPLAINANT_INFO['address']}
                     {COMPLAINANT_INFO['city_state_zip']}
            Phone:   {COMPLAINANT_INFO['phone']}
            Email:   {COMPLAINANT_INFO['email']}

            Relationship to Case: Self-represented plaintiff/petitioner in the
            above-captioned family law proceeding.""")

    def _build_subject_judge_section(self) -> str:
        return textwrap.dedent(f"""\
            {'=' * 70}
            SUBJECT JUDGE
            {'=' * 70}

            Name:   {SUBJECT_JUDGE_INFO['name']}
            Court:  {SUBJECT_JUDGE_INFO['court']}
            County: {SUBJECT_JUDGE_INFO['county']}
            State:  {SUBJECT_JUDGE_INFO['state']}

            Case: {CASE_INFO['case_number']} — {CASE_INFO['caption']}
            Defendant: {CASE_INFO['defendant']}""")

    def _build_factual_allegations(
        self, violations: list[JTCViolation],
    ) -> str:
        lines: list[str] = [
            "=" * 70,
            "FACTUAL ALLEGATIONS",
            "=" * 70,
            "",
            f"Complainant, {COMPLAINANT_INFO['name']}, states the following",
            "factual allegations under oath:",
            "",
        ]

        para = 1
        for v in violations:
            lines.append(
                f"  {para}. {v.description}"
            )
            if v.date:
                lines.append(f"     Date: {v.date}")
            if v.evidence_refs:
                refs = ", ".join(v.evidence_refs)
                lines.append(f"     Supporting Evidence: {refs}")
            lines.append("")
            para += 1

        return "\n".join(lines)

    def _build_violations_section(
        self, violations: list[JTCViolation],
    ) -> str:
        lines: list[str] = [
            "=" * 70,
            "VIOLATIONS OF THE MICHIGAN CODE OF JUDICIAL CONDUCT",
            "=" * 70,
            "",
        ]

        # Group by canon
        canon_groups: dict[str, list[JTCViolation]] = {}
        for v in violations:
            canon = v.canon_violated
            if canon not in canon_groups:
                canon_groups[canon] = []
            canon_groups[canon].append(v)

        section_num = 1
        for canon, group in canon_groups.items():
            info = CANON_MAP.get(
                group[0].violation_type,
                {"title": "Violation", "description": "", "mcr": ""},
            )
            lines.append(f"VIOLATION {section_num}: {canon}")
            lines.append(f"Title: {info['title']}")
            if info.get("mcr"):
                lines.append(f"Court Rule: {info['mcr']}")
            lines.append(f"Standard: {info['description']}")
            lines.append("")

            for v in group:
                lines.append(f"  - {v.description}")
                if v.date:
                    lines.append(f"    Date: {v.date}")
                lines.append(f"    Severity: {v.severity}/10")
                lines.append("")

            section_num += 1

        return "\n".join(lines)

    def _build_pattern_section(
        self,
        pattern: PatternAnalysis,
        severity: SeverityResult,
    ) -> str:
        lines: list[str] = [
            "=" * 70,
            "PATTERN ANALYSIS",
            "=" * 70,
            "",
            f"Total Violations: {pattern.violation_count}",
            f"Date Range: {pattern.date_range}",
            f"Composite Severity Score: {severity.total_score} ({severity.risk_level})",
            "",
            "Pattern Description:",
            pattern.pattern_description,
            "",
        ]

        if pattern.escalation_timeline:
            lines.append("Escalation Timeline:")
            for entry in pattern.escalation_timeline:
                lines.append(f"  - {entry}")
            lines.append("")

        if severity.category_scores:
            lines.append("Severity by Category:")
            for cat, score in sorted(
                severity.category_scores.items(),
                key=lambda x: x[1],
                reverse=True,
            ):
                info = CANON_MAP.get(cat, {})
                title = info.get("title", cat)
                lines.append(f"  - {title}: {score}")
            lines.append("")

        return "\n".join(lines)

    def _build_prayer_for_relief(self) -> str:
        return textwrap.dedent(f"""\
            {'=' * 70}
            PRAYER FOR RELIEF
            {'=' * 70}

            WHEREFORE, Complainant {COMPLAINANT_INFO['name']} respectfully
            requests that the Michigan Judicial Tenure Commission:

              1. Accept and investigate this formal complaint pursuant to
                 Michigan Constitution Art. 6, §30 and MCR 9.112;

              2. Conduct a public hearing pursuant to MCR 9.115 and
                 JTC Rule 9 to examine the allegations herein;

              3. Find that {SUBJECT_JUDGE_INFO['name']} has engaged in
                 misconduct in office, conduct clearly prejudicial to the
                 administration of justice, and failure to perform judicial
                 duties, in violation of the Michigan Code of Judicial Conduct;

              4. Recommend to the Michigan Supreme Court appropriate discipline,
                 which may include:
                 a. Public censure;
                 b. Suspension with or without pay;
                 c. Removal from the bench;
                 d. Such other relief as the Commission deems appropriate;

              5. Order {SUBJECT_JUDGE_INFO['name']} to immediately disqualify
                 herself from Case No. {CASE_INFO['case_number']} and all
                 related proceedings;

              6. Grant such other and further relief as the Commission deems
                 just and proper.""")

    def _build_exhibit_section(self, exhibits: list[ExhibitEntry]) -> str:
        lines: list[str] = [
            "=" * 70,
            "EXHIBIT LIST",
            "=" * 70,
            "",
        ]
        for ex in exhibits:
            lines.append(f"  {ex.exhibit_id}: {ex.title}")
            if ex.description:
                lines.append(f"    Description: {ex.description}")
            if ex.bates_range:
                lines.append(f"    Bates Range: {ex.bates_range}")
            lines.append("")

        return "\n".join(lines)

    def _build_verification(self, today: str) -> str:
        return textwrap.dedent(f"""\
            {'=' * 70}
            VERIFICATION
            {'=' * 70}

            STATE OF MICHIGAN    )
                                 ) ss.
            COUNTY OF MUSKEGON   )

            I, {COMPLAINANT_INFO['name']}, being first duly sworn, depose
            and state under penalty of perjury that the facts set forth in this
            complaint are true and correct to the best of my knowledge,
            information, and belief. I understand that filing a false complaint
            with the Judicial Tenure Commission may subject me to sanctions.


            ____________________________________
            {COMPLAINANT_INFO['name']}

            Date: {today}

            Sworn and subscribed before me this _____ day of
            ______________, 20_____.


            ____________________________________
            Notary Public, State of Michigan
            My Commission Expires: _______________""")
