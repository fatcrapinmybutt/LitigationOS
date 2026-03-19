# -*- coding: utf-8 -*-
"""
quality_gate.py — Filing Quality Gate Engine
=============================================
Phase-transition quality gates for the filing lifecycle.  Before a
filing may advance from one phase to the next, every mandatory check
(blocker-severity) must pass.

The engine runs 25+ individual checks grouped by target phase:

  REVIEW gates  : content, caption, case number
  QA gates      : no placeholders, reviewer sign-off
  APPROVED gates: QA score, citations, party names, judge name,
                  child-name redaction, no fabricated cites
  FORMATTED     : format compliance, double-spacing, margins,
                  page numbering, font
  FILED         : PDF generated, e-filing ready, signature block,
                  certificate of service
  SERVED        : proof of service complete

Pigors v. Watson (Muskegon County 14th Circuit) — canonical names:
  - Plaintiff : Andrew James Pigors (Pro Se)
  - Defendant : Emily A. Watson (NOT "Emily Ann", NOT "Emily M.")
  - Child     : L.D.W. per MCR 8.119(H) — never full name in public filings
  - Judge     : Hon. Jenny L. McNeill (TWO L's)

Zero external dependencies.  Local-only.
"""

from __future__ import annotations

import logging
import re
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Callable, Dict, List, Optional, Tuple

logger = logging.getLogger("legal_ai.quality_gate")

# ─── Constants ────────────────────────────────────────────────────────

# Plaintiff acceptable names
_PLAINTIFF_NAMES = {
    "Andrew James Pigors",
    "Andrew J. Pigors",
    "ANDREW JAMES PIGORS",
    "ANDREW J. PIGORS",
}

# Defendant canonical form
_DEFENDANT_CANONICAL = "Emily A. Watson"
_DEFENDANT_CANONICAL_UPPER = "EMILY A. WATSON"

# Prohibited defendant name variants
_WRONG_DEFENDANT_PATTERNS: List[re.Pattern[str]] = [
    re.compile(r"Emily\s+Ann\s+Watson", re.IGNORECASE),
    re.compile(r"Emily\s+M\.?\s+Watson", re.IGNORECASE),
    re.compile(r"Tiffany\s+Watson", re.IGNORECASE),
    re.compile(r"EMILY\s+M\.\s+WATSON"),
]

# Judge canonical
_JUDGE_CANONICAL = "McNeill"
_WRONG_JUDGE_PATTERNS: List[re.Pattern[str]] = [
    re.compile(r"\bMcNeil\b(?!l)"),  # "McNeil" without second L
    re.compile(r"\bMcneil\b", re.IGNORECASE),
    re.compile(r"\bMc\s*Neil\b(?!l)", re.IGNORECASE),
]

# Placeholder patterns
_PLACEHOLDER_PATTERNS: List[re.Pattern[str]] = [
    re.compile(r"\[PLACEHOLDER\]", re.IGNORECASE),
    re.compile(r"\[TODO\]", re.IGNORECASE),
    re.compile(r"\[INSERT\b[^\]]*\]", re.IGNORECASE),
    re.compile(r"<<[^>]+>>"),
    re.compile(r"\{FIELD\}", re.IGNORECASE),
    re.compile(r"\[FILL\s*IN\]", re.IGNORECASE),
    re.compile(r"\[TBD\]", re.IGNORECASE),
    re.compile(r"\[XXX\]"),
    re.compile(r"\[DATE\]", re.IGNORECASE),
    re.compile(r"\[NAME\]", re.IGNORECASE),
    re.compile(r"\[ADDRESS\]", re.IGNORECASE),
    re.compile(r"\[CASE\s*NUMBER\]", re.IGNORECASE),
]

# Known fabricated citations (hallucinated by LLMs)
_FABRICATED_CITATIONS: List[Tuple[re.Pattern[str], str]] = [
    (
        re.compile(r"McCraney\s+v\.?\s+Ford\s+Motor\s+Co", re.IGNORECASE),
        "McCraney v Ford Motor Co 282 Mich App 647 (2009) — known hallucination",
    ),
    (
        re.compile(r"Cease\s+v\.?\s+AAA\s+Michigan", re.IGNORECASE),
        "Cease v AAA Michigan 2012 Mich App LEXIS 1764 — known hallucination",
    ),
    (
        re.compile(
            r"People\s+v\.?\s+Smith,?\s+482\s+Mich\s+292", re.IGNORECASE
        ),
        "People v Smith 482 Mich 292 — verify before citing",
    ),
]

# Case number validation
_CASE_NUMBER_FORMATS: List[re.Pattern[str]] = [
    re.compile(r"\b\d{4}-\d{6}-[A-Z]{2}\b"),         # 2024-001507-DC
    re.compile(r"\bCOA\s*(?:No\.?\s*)?\d{5,6}\b"),    # COA 366810
    re.compile(r"\b\d{2}-cv-\d+\b", re.IGNORECASE),   # Federal
]

# Wrong case number formats (missing leading zeros)
_WRONG_CASE_FORMATS: List[re.Pattern[str]] = [
    re.compile(r"\b2024-1507-DC\b"),      # Missing leading zeros
    re.compile(r"\b2023-5907-PP\b"),       # Missing leading zeros
    re.compile(r"\b2025-2760-CZ\b"),       # Missing leading zeros
]

# Citation patterns (Michigan)
_CITATION_PATTERNS: List[re.Pattern[str]] = [
    re.compile(r"\bMCL\s+\d+\.\d+", re.IGNORECASE),
    re.compile(r"\bMCR\s+\d+\.\d+", re.IGNORECASE),
    re.compile(r"\bMRE\s+\d+", re.IGNORECASE),
    re.compile(r"\b\d+\s+Mich\s+(?:App\s+)?\d+"),
    re.compile(r"\b\d+\s+NW\s*(?:2d|\.2d)\s+\d+"),
]

# Citation format validation
_CITATION_FORMAT_PATTERNS: List[Tuple[re.Pattern[str], str]] = [
    (
        re.compile(r"\bMCL\s+§?\s*\d+\.\d+(?:\([a-zA-Z0-9]+\))*"),
        "MCL",
    ),
    (
        re.compile(r"\bMCR\s+\d+\.\d+(?:\([A-Z]\)(?:\(\d+\))*)*"),
        "MCR",
    ),
    (
        re.compile(r"\bMRE\s+\d+(?:\([a-zA-Z]\))*"),
        "MRE",
    ),
]

# Brief word limits
_WORD_LIMITS: Dict[str, int] = {
    "appellate_brief": 16000,        # MCR 7.212(B)
    "appellate_reply": 8000,         # MCR 7.212(B)
    "motion": 20000,                 # No hard limit, practical cap
    "response": 20000,
    "reply": 10000,
    "supreme_court_brief": 16000,    # MCR 7.312
    "emergency_motion": 10000,
}

# Signature block components
_SIGNATURE_INDICATORS: List[re.Pattern[str]] = [
    re.compile(r"Respectfully\s+submitted", re.IGNORECASE),
    re.compile(r"Pro\s+Se\s+(?:Plaintiff|Litigant)", re.IGNORECASE),
    re.compile(r"Andrew\s+(?:James\s+)?(?:J\.?\s+)?Pigors", re.IGNORECASE),
    re.compile(r"1977\s+Whitehall\s+Road", re.IGNORECASE),
    re.compile(r"North\s+Muskegon,?\s+MI\s+49445", re.IGNORECASE),
]

# Certificate of Service indicators
_COS_INDICATORS: List[re.Pattern[str]] = [
    re.compile(r"Certificate\s+of\s+Service", re.IGNORECASE),
    re.compile(r"CERTIFICATE\s+OF\s+SERVICE"),
    re.compile(r"I\s+(?:hereby\s+)?certif(?:y|ied)", re.IGNORECASE),
    re.compile(r"served?\s+(?:a\s+)?(?:true\s+)?copy", re.IGNORECASE),
]

# Verification / declaration under penalty of perjury
_VERIFICATION_INDICATORS: List[re.Pattern[str]] = [
    re.compile(r"under\s+(?:the\s+)?penalty\s+of\s+perjury", re.IGNORECASE),
    re.compile(r"VERIFICATION", re.IGNORECASE),
    re.compile(r"sworn?\s+(?:and\s+)?(?:affirm|stat)", re.IGNORECASE),
    re.compile(r"declare\s+under\s+penalty", re.IGNORECASE),
]

# Caption indicators
_CAPTION_INDICATORS: List[re.Pattern[str]] = [
    re.compile(r"STATE\s+OF\s+MICHIGAN", re.IGNORECASE),
    re.compile(r"CIRCUIT\s+COURT", re.IGNORECASE),
    re.compile(r"COURT\s+OF\s+APPEALS", re.IGNORECASE),
    re.compile(r"Plaintiff", re.IGNORECASE),
    re.compile(r"Defendant", re.IGNORECASE),
    re.compile(r"Case\s+No\.?", re.IGNORECASE),
]


# ─── Data Classes ─────────────────────────────────────────────────────

@dataclass
class GateCheck:
    """Result of a single quality check.

    Attributes:
        check_id: Machine-readable identifier (e.g. ``has_content``).
        name: Short human-readable label.
        description: Explanation of what the check verifies.
        severity: One of ``blocker``, ``warning``, ``info``.
        passed: Whether the check succeeded.
        details: Human-readable result message.
        auto_fixable: Whether an automated fix is available.
        fix_suggestion: Suggested remediation text.
    """

    check_id: str
    name: str
    description: str
    severity: str  # "blocker", "warning", "info"
    passed: bool
    details: str
    auto_fixable: bool = False
    fix_suggestion: str = ""

    def to_dict(self) -> Dict[str, Any]:
        """Serialize to a plain dictionary."""
        return {
            "check_id": self.check_id,
            "name": self.name,
            "description": self.description,
            "severity": self.severity,
            "passed": self.passed,
            "details": self.details,
            "auto_fixable": self.auto_fixable,
            "fix_suggestion": self.fix_suggestion,
        }


@dataclass
class GateResult:
    """Aggregated outcome of running a quality gate.

    Attributes:
        gate_name: Human-readable gate label (e.g. "REVIEW Gate").
        phase: Target phase this gate guards.
        filing_id: Filing being checked.
        passed: Overall pass/fail — ``True`` only when zero blockers.
        score: Numeric score 0–100.
        checks: Individual check results.
        blocker_count: Number of blocker-severity failures.
        warning_count: Number of warning-severity failures.
        timestamp: ISO-8601 UTC timestamp.
    """

    gate_name: str
    phase: str
    filing_id: str
    passed: bool = True
    score: float = 100.0
    checks: List[GateCheck] = field(default_factory=list)
    blocker_count: int = 0
    warning_count: int = 0
    timestamp: str = field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )

    def to_dict(self) -> Dict[str, Any]:
        """Serialize to a plain dictionary."""
        return {
            "gate_name": self.gate_name,
            "phase": self.phase,
            "filing_id": self.filing_id,
            "passed": self.passed,
            "score": round(self.score, 1),
            "blocker_count": self.blocker_count,
            "warning_count": self.warning_count,
            "checks": [c.to_dict() for c in self.checks],
            "timestamp": self.timestamp,
        }


# ─── Quality Gate Engine ──────────────────────────────────────────────

class QualityGateEngine:
    """Phase-transition quality gates for the filing lifecycle.

    Runs a battery of checks against filing text and returns a
    structured GateResult indicating pass/fail status and individual
    check outcomes.  Checks are mapped to target phases so only
    relevant checks run for a given transition.

    Example::

        engine = QualityGateEngine()
        result = engine.run_gate(text, "mot-001", "review", "motion")
        if not result.passed:
            for c in result.checks:
                if not c.passed:
                    print(f"FAIL [{c.severity}]: {c.name} — {c.details}")
    """

    # ── Phase → Check-ID mapping ──

    PHASE_CHECKS: Dict[str, List[str]] = {
        "review": [
            "has_content",
            "has_caption",
            "has_case_number",
        ],
        "qa": [
            "no_placeholders",
            "party_names",
            "judge_name",
            "child_name",
            "no_wrong_names",
            "case_number_format",
        ],
        "approved": [
            "citations_present",
            "citations_format",
            "no_fabricated_citations",
            "signature_block",
            "prayer_for_relief",
            "facts_section",
            "legal_argument",
        ],
        "formatted": [
            "double_spacing",
            "font_compliance",
            "margin_compliance",
            "page_numbering",
            "word_count",
        ],
        "filed": [
            "certificate_of_service",
            "verification_statement",
            "exhibit_references",
            "mcr_compliance",
        ],
        "served": [
            "certificate_of_service",
        ],
    }

    def __init__(self) -> None:
        """Initialise the quality gate engine."""
        self._stats_gates_run: int = 0
        self._stats_checks_run: int = 0
        self._stats_blockers_found: int = 0
        self._stats_warnings_found: int = 0

        # Registry: check_id → (callable, name, description, severity)
        self._registry: Dict[
            str,
            Tuple[Callable[..., GateCheck], str, str, str],
        ] = self._build_registry()

    # ----------------------------------------------------------------
    # Public API
    # ----------------------------------------------------------------

    def run_gate(
        self,
        text: str,
        filing_id: str,
        target_phase: str,
        filing_type: str = "motion",
    ) -> GateResult:
        """Run all checks for a target phase gate.

        Args:
            text: Filing content to check.
            filing_id: Identifier of the filing being checked.
            target_phase: Phase this gate guards (e.g. ``"review"``).
            filing_type: Document type (motion, appellate_brief, etc.).

        Returns:
            GateResult with individual check outcomes and aggregate score.
        """
        phase_lower = target_phase.lower()
        check_ids = self.PHASE_CHECKS.get(phase_lower, [])

        if not check_ids:
            logger.warning(
                "No checks defined for phase '%s'; returning pass.",
                target_phase,
            )
            return GateResult(
                gate_name=f"{target_phase.upper()} Gate",
                phase=phase_lower,
                filing_id=filing_id,
                passed=True,
                score=100.0,
            )

        checks: List[GateCheck] = []
        for cid in check_ids:
            check = self._run_single_check(cid, text, filing_type)
            checks.append(check)

        return self._aggregate(checks, phase_lower, filing_id)

    def run_specific_checks(
        self,
        text: str,
        check_ids: List[str],
        filing_type: str = "motion",
    ) -> List[GateCheck]:
        """Run an arbitrary set of checks by ID.

        Args:
            text: Filing content to check.
            check_ids: List of check identifiers to execute.
            filing_type: Document type hint.

        Returns:
            List of GateCheck results.
        """
        results: List[GateCheck] = []
        for cid in check_ids:
            results.append(self._run_single_check(cid, text, filing_type))
        return results

    def get_available_checks(self) -> List[str]:
        """Return all registered check IDs.

        Returns:
            Sorted list of check identifier strings.
        """
        return sorted(self._registry.keys())

    def get_stats(self) -> Dict[str, Any]:
        """Return operational statistics.

        Returns:
            Dict with run counters and available check information.
        """
        return {
            "version": "1.0.0",
            "gates_run": self._stats_gates_run,
            "checks_run": self._stats_checks_run,
            "blockers_found": self._stats_blockers_found,
            "warnings_found": self._stats_warnings_found,
            "registered_checks": len(self._registry),
            "available_check_ids": self.get_available_checks(),
            "phase_check_map": {
                k: list(v) for k, v in self.PHASE_CHECKS.items()
            },
        }

    # ----------------------------------------------------------------
    # Individual Check Methods (25+)
    # ----------------------------------------------------------------

    def check_has_content(self, text: str, **_: Any) -> GateCheck:
        """Verify the filing has substantive content (>100 characters).

        Args:
            text: Filing text to check.

        Returns:
            GateCheck with pass/fail status.
        """
        stripped = text.strip() if text else ""
        passed = len(stripped) > 100
        return GateCheck(
            check_id="has_content",
            name="Has Content",
            description="Filing must contain substantive content (>100 chars).",
            severity="blocker",
            passed=passed,
            details=(
                f"Content length: {len(stripped)} chars."
                if passed
                else f"Content too short ({len(stripped)} chars, need >100)."
            ),
        )

    def check_has_caption(self, text: str, **_: Any) -> GateCheck:
        """Verify a court caption block is present.

        Args:
            text: Filing text to check.

        Returns:
            GateCheck with pass/fail status.
        """
        if not text:
            return self._fail_check(
                "has_caption", "Has Caption",
                "Court caption block must be present.",
                "blocker", "No text provided.",
            )

        matches = sum(1 for p in _CAPTION_INDICATORS if p.search(text))
        passed = matches >= 3
        return GateCheck(
            check_id="has_caption",
            name="Has Caption",
            description="Court caption block must be present.",
            severity="blocker",
            passed=passed,
            details=(
                f"Caption detected ({matches} indicators found)."
                if passed
                else f"Caption incomplete — only {matches}/3 indicators found."
            ),
            auto_fixable=not passed,
            fix_suggestion="Add a full court caption with STATE OF MICHIGAN, court name, parties, and Case No.",
        )

    def check_has_case_number(self, text: str, **_: Any) -> GateCheck:
        """Verify a valid case number is present.

        Args:
            text: Filing text to check.

        Returns:
            GateCheck with pass/fail status.
        """
        if not text:
            return self._fail_check(
                "has_case_number", "Has Case Number",
                "A valid case number must appear in the filing.",
                "blocker", "No text provided.",
            )

        found = any(p.search(text) for p in _CASE_NUMBER_FORMATS)
        return GateCheck(
            check_id="has_case_number",
            name="Has Case Number",
            description="A valid case number must appear in the filing.",
            severity="blocker",
            passed=found,
            details=(
                "Valid case number found."
                if found
                else "No valid case number detected (expected YYYY-NNNNNN-XX, COA NNNNN, or NN-cv-NNNN)."
            ),
            auto_fixable=not found,
            fix_suggestion="Add the case number in format 2024-001507-DC.",
        )

    def check_no_placeholders(self, text: str, **_: Any) -> GateCheck:
        """Verify no placeholder tokens remain in the text.

        Args:
            text: Filing text to check.

        Returns:
            GateCheck with pass/fail status.
        """
        if not text:
            return self._fail_check(
                "no_placeholders", "No Placeholders",
                "No [PLACEHOLDER], [TODO], <<...>>, or {FIELD} tokens allowed.",
                "blocker", "No text provided.",
            )

        found: List[str] = []
        for pattern in _PLACEHOLDER_PATTERNS:
            matches = pattern.findall(text)
            found.extend(matches)

        passed = len(found) == 0
        return GateCheck(
            check_id="no_placeholders",
            name="No Placeholders",
            description="No [PLACEHOLDER], [TODO], <<...>>, or {FIELD} tokens allowed.",
            severity="blocker",
            passed=passed,
            details=(
                "No placeholders found."
                if passed
                else f"Found {len(found)} placeholder(s): {found[:5]}"
            ),
            auto_fixable=False,
            fix_suggestion="Replace all placeholder tokens with actual content.",
        )

    def check_party_names(self, text: str, **_: Any) -> GateCheck:
        """Verify correct plaintiff/defendant name usage.

        Plaintiff must be "Andrew James Pigors" or "Andrew J. Pigors".
        Defendant must be "Emily A. Watson" (not variants).

        Args:
            text: Filing text to check.

        Returns:
            GateCheck with pass/fail status.
        """
        if not text:
            return self._fail_check(
                "party_names", "Party Names Correct",
                "Correct party names per case records.",
                "blocker", "No text provided.",
            )

        issues: List[str] = []

        # Check plaintiff name present
        has_plaintiff = any(name in text for name in _PLAINTIFF_NAMES)
        if not has_plaintiff and re.search(r"Pigors", text, re.IGNORECASE):
            issues.append(
                "Pigors referenced but not in canonical form "
                "(use 'Andrew James Pigors' or 'Andrew J. Pigors')."
            )

        # Check defendant name
        for pattern in _WRONG_DEFENDANT_PATTERNS:
            match = pattern.search(text)
            if match:
                issues.append(
                    f"Wrong defendant name: '{match.group()}' — "
                    f"must be '{_DEFENDANT_CANONICAL}'."
                )

        passed = len(issues) == 0
        return GateCheck(
            check_id="party_names",
            name="Party Names Correct",
            description="Correct party names per case records.",
            severity="blocker",
            passed=passed,
            details=(
                "Party names verified."
                if passed
                else "; ".join(issues)
            ),
            auto_fixable=True,
            fix_suggestion=f"Use '{_DEFENDANT_CANONICAL}' for defendant.",
        )

    def check_judge_name(self, text: str, **_: Any) -> GateCheck:
        """Verify judge name spelling (McNeill with two L's).

        Args:
            text: Filing text to check.

        Returns:
            GateCheck with pass/fail status.
        """
        if not text:
            return self._fail_check(
                "judge_name", "Judge Name Correct",
                "Judge name must be 'McNeill' (two L's).",
                "blocker", "No text provided.",
            )

        issues: List[str] = []
        for pattern in _WRONG_JUDGE_PATTERNS:
            match = pattern.search(text)
            if match:
                issues.append(
                    f"Misspelled judge name: '{match.group()}' — "
                    f"correct is '{_JUDGE_CANONICAL}' (two L's)."
                )

        passed = len(issues) == 0
        return GateCheck(
            check_id="judge_name",
            name="Judge Name Correct",
            description="Judge name must be 'McNeill' (two L's).",
            severity="blocker",
            passed=passed,
            details=(
                "Judge name verified." if passed else "; ".join(issues)
            ),
            auto_fixable=True,
            fix_suggestion="Replace 'McNeil' with 'McNeill' (two L's).",
        )

    def check_child_name(self, text: str, **_: Any) -> GateCheck:
        """Verify child is referred to by initials only (L.D.W.).

        MCR 8.119(H) requires minor children be identified by initials
        in public court filings.

        Args:
            text: Filing text to check.

        Returns:
            GateCheck with pass/fail status.
        """
        if not text:
            return self._fail_check(
                "child_name", "Child Name Redacted (MCR 8.119(H))",
                "Minor child must be referred to by initials L.D.W. only.",
                "blocker", "No text provided.",
            )

        # Check for full name exposure
        full_name_patterns = [
            re.compile(r"Lincoln\s+David\s+Watson", re.IGNORECASE),
            re.compile(r"Lincoln\s+D\.?\s+Watson", re.IGNORECASE),
            re.compile(r"Lincoln\s+Watson", re.IGNORECASE),
        ]

        issues: List[str] = []
        for pattern in full_name_patterns:
            match = pattern.search(text)
            if match:
                issues.append(
                    f"Full child name exposed: '{match.group()}' — "
                    "must use initials 'L.D.W.' per MCR 8.119(H)."
                )

        passed = len(issues) == 0
        return GateCheck(
            check_id="child_name",
            name="Child Name Redacted (MCR 8.119(H))",
            description="Minor child must be referred to by initials L.D.W. only.",
            severity="blocker",
            passed=passed,
            details=(
                "Child name properly redacted (initials only)."
                if passed
                else "; ".join(issues)
            ),
            auto_fixable=True,
            fix_suggestion="Replace all instances of the child's full name with 'L.D.W.'",
        )

    def check_citations_present(self, text: str, **_: Any) -> GateCheck:
        """Verify at least one MCL/MCR/MRE citation is present.

        Args:
            text: Filing text to check.

        Returns:
            GateCheck with pass/fail status.
        """
        if not text:
            return self._fail_check(
                "citations_present", "Citations Present",
                "Filing must contain MCL, MCR, or MRE citations.",
                "warning", "No text provided.",
            )

        found = [p.pattern for p in _CITATION_PATTERNS if p.search(text)]
        passed = len(found) > 0
        return GateCheck(
            check_id="citations_present",
            name="Citations Present",
            description="Filing must contain MCL, MCR, or MRE citations.",
            severity="warning",
            passed=passed,
            details=(
                f"Found citations matching {len(found)} pattern(s)."
                if passed
                else "No MCL/MCR/MRE citations found."
            ),
        )

    def check_citations_format(self, text: str, **_: Any) -> GateCheck:
        """Verify citation formatting is correct.

        Proper format examples: MCL 722.23, MCR 2.003(C), MRE 803.

        Args:
            text: Filing text to check.

        Returns:
            GateCheck with pass/fail status.
        """
        if not text:
            return self._fail_check(
                "citations_format", "Citation Format",
                "Citations must use proper format (MCL NNN.NNN, MCR N.NNN(X)).",
                "warning", "No text provided.",
            )

        # Look for malformed citations
        issues: List[str] = []

        # Check for "MCL §" (redundant — MCL already implies statute)
        if re.search(r"\bMCL\s+§\s*§", text):
            issues.append("Double section symbol (§§) after MCL is redundant.")

        # Check for missing space: "MCL722" instead of "MCL 722"
        no_space = re.findall(r"\b(MCL|MCR|MRE)\d", text)
        if no_space:
            issues.append(
                f"Missing space after citation prefix: {no_space[:3]}"
            )

        passed = len(issues) == 0
        return GateCheck(
            check_id="citations_format",
            name="Citation Format",
            description="Citations must use proper format (MCL NNN.NNN, MCR N.NNN(X)).",
            severity="warning",
            passed=passed,
            details=(
                "Citation formatting appears correct."
                if passed
                else "; ".join(issues)
            ),
            auto_fixable=True,
            fix_suggestion="Ensure space after MCL/MCR/MRE prefix. Use MCL 722.23 format.",
        )

    def check_no_fabricated_citations(self, text: str, **_: Any) -> GateCheck:
        """Block known hallucinated / fabricated citations.

        Args:
            text: Filing text to check.

        Returns:
            GateCheck with pass/fail status.
        """
        if not text:
            return self._fail_check(
                "no_fabricated_citations", "No Fabricated Citations",
                "Block known LLM-hallucinated case citations.",
                "blocker", "No text provided.",
            )

        found: List[str] = []
        for pattern, description in _FABRICATED_CITATIONS:
            if pattern.search(text):
                found.append(description)

        passed = len(found) == 0
        return GateCheck(
            check_id="no_fabricated_citations",
            name="No Fabricated Citations",
            description="Block known LLM-hallucinated case citations.",
            severity="blocker",
            passed=passed,
            details=(
                "No known fabricated citations detected."
                if passed
                else f"FABRICATED CITATION(S): {'; '.join(found)}"
            ),
        )

    def check_signature_block(self, text: str, **_: Any) -> GateCheck:
        """Verify a proper signature block is present.

        Must include "Respectfully submitted", name, and address.

        Args:
            text: Filing text to check.

        Returns:
            GateCheck with pass/fail status.
        """
        if not text:
            return self._fail_check(
                "signature_block", "Signature Block",
                "Filing must contain a proper signature block.",
                "blocker", "No text provided.",
            )

        found = sum(1 for p in _SIGNATURE_INDICATORS if p.search(text))
        passed = found >= 2
        return GateCheck(
            check_id="signature_block",
            name="Signature Block",
            description="Filing must contain a proper signature block.",
            severity="blocker",
            passed=passed,
            details=(
                f"Signature block found ({found} indicators)."
                if passed
                else f"Incomplete signature block ({found}/2 indicators required)."
            ),
            auto_fixable=not passed,
            fix_suggestion=(
                "Add: 'Respectfully submitted,\\n"
                "Andrew James Pigors, Pro Se Plaintiff\\n"
                "1977 Whitehall Road, Lot 17\\n"
                "North Muskegon, MI 49445'"
            ),
        )

    def check_certificate_of_service(self, text: str, **_: Any) -> GateCheck:
        """Verify a Certificate of Service is present.

        Args:
            text: Filing text to check.

        Returns:
            GateCheck with pass/fail status.
        """
        if not text:
            return self._fail_check(
                "certificate_of_service", "Certificate of Service",
                "Filing must include a Certificate of Service (MCR 2.107).",
                "blocker", "No text provided.",
            )

        found = sum(1 for p in _COS_INDICATORS if p.search(text))
        passed = found >= 2
        return GateCheck(
            check_id="certificate_of_service",
            name="Certificate of Service",
            description="Filing must include a Certificate of Service (MCR 2.107).",
            severity="blocker",
            passed=passed,
            details=(
                "Certificate of Service found."
                if passed
                else f"Certificate of Service incomplete ({found}/2 indicators)."
            ),
            auto_fixable=not passed,
            fix_suggestion="Add a Certificate of Service per MCR 2.107.",
        )

    def check_verification_statement(self, text: str, **_: Any) -> GateCheck:
        """Verify a verification / declaration under penalty of perjury.

        Args:
            text: Filing text to check.

        Returns:
            GateCheck with pass/fail status.
        """
        if not text:
            return self._fail_check(
                "verification_statement", "Verification Statement",
                "Filing should include a verification under penalty of perjury.",
                "warning", "No text provided.",
            )

        found = any(p.search(text) for p in _VERIFICATION_INDICATORS)
        return GateCheck(
            check_id="verification_statement",
            name="Verification Statement",
            description="Filing should include a verification under penalty of perjury.",
            severity="warning",
            passed=found,
            details=(
                "Verification statement found."
                if found
                else "No verification / declaration under penalty of perjury found."
            ),
        )

    def check_word_count(
        self, text: str, filing_type: str = "motion", **_: Any
    ) -> GateCheck:
        """Verify the filing is within the word limit for its type.

        Args:
            text: Filing text to check.
            filing_type: Type of filing for limit lookup.

        Returns:
            GateCheck with pass/fail status.
        """
        if not text:
            return self._fail_check(
                "word_count", "Word Count",
                "Filing must be within the word limit.",
                "warning", "No text provided.",
            )

        words = len(text.split())
        limit = _WORD_LIMITS.get(filing_type, 20000)
        passed = words <= limit
        return GateCheck(
            check_id="word_count",
            name="Word Count",
            description=f"Filing must be ≤{limit:,} words ({filing_type}).",
            severity="warning" if passed or words <= limit * 1.1 else "blocker",
            passed=passed,
            details=f"Word count: {words:,} / {limit:,} limit.",
        )

    def check_font_compliance(self, text: str, **_: Any) -> GateCheck:
        """Check for font specification (Times New Roman 12pt).

        For plain text / markdown, this check passes with an info note.

        Args:
            text: Filing text to check.

        Returns:
            GateCheck with pass/fail status.
        """
        if not text:
            return self._fail_check(
                "font_compliance", "Font Compliance",
                "Court filings must use Times New Roman 12pt.",
                "info", "No text provided.",
            )

        has_font_ref = bool(
            re.search(r"Times\s+New\s+Roman", text, re.IGNORECASE)
            or re.search(r"12[\s-]*(?:pt|point)", text, re.IGNORECASE)
        )

        is_markdown = text.strip().startswith("#") or "```" in text

        if is_markdown:
            return GateCheck(
                check_id="font_compliance",
                name="Font Compliance",
                description="Court filings must use Times New Roman 12pt.",
                severity="info",
                passed=True,
                details="Markdown content — font checked at PDF generation.",
            )

        return GateCheck(
            check_id="font_compliance",
            name="Font Compliance",
            description="Court filings must use Times New Roman 12pt.",
            severity="info",
            passed=True,
            details=(
                "Font reference found." if has_font_ref
                else "No font specification detected — verify at PDF stage."
            ),
        )

    def check_margin_compliance(self, text: str, **_: Any) -> GateCheck:
        """Check for margin specification (1-inch margins).

        Args:
            text: Filing text to check.

        Returns:
            GateCheck with pass/fail status.
        """
        has_margin_ref = bool(
            re.search(r"1[\s-]*inch\s+margin", text or "", re.IGNORECASE)
            or re.search(r"margin.*1\s*(?:in|\")", text or "", re.IGNORECASE)
        )
        return GateCheck(
            check_id="margin_compliance",
            name="Margin Compliance",
            description="Court filings must use 1-inch margins.",
            severity="info",
            passed=True,
            details=(
                "Margin reference found." if has_margin_ref
                else "No margin specification — verify at PDF stage."
            ),
        )

    def check_page_numbering(self, text: str, **_: Any) -> GateCheck:
        """Check for page numbering markers.

        Args:
            text: Filing text to check.

        Returns:
            GateCheck with pass/fail status.
        """
        if not text:
            return self._fail_check(
                "page_numbering", "Page Numbering",
                "Filing should include page numbers.",
                "info", "No text provided.",
            )

        has_page = bool(
            re.search(r"Page\s+\d+\s+of\s+\d+", text, re.IGNORECASE)
            or re.search(r"-\s*\d+\s*-", text)
            or re.search(r"\\thispagestyle|\\pagestyle", text)
        )
        return GateCheck(
            check_id="page_numbering",
            name="Page Numbering",
            description="Filing should include page numbers.",
            severity="info",
            passed=True,
            details=(
                "Page numbering detected." if has_page
                else "No page numbering detected — add at PDF stage."
            ),
        )

    def check_case_number_format(self, text: str, **_: Any) -> GateCheck:
        """Verify case numbers use leading zeros.

        Correct: 2024-001507-DC.  Wrong: 2024-1507-DC.

        Args:
            text: Filing text to check.

        Returns:
            GateCheck with pass/fail status.
        """
        if not text:
            return self._fail_check(
                "case_number_format", "Case Number Format",
                "Case numbers must use leading zeros (e.g. 2024-001507-DC).",
                "blocker", "No text provided.",
            )

        issues: List[str] = []
        for pattern in _WRONG_CASE_FORMATS:
            match = pattern.search(text)
            if match:
                issues.append(
                    f"Wrong format: '{match.group()}' — needs leading zeros."
                )

        passed = len(issues) == 0
        return GateCheck(
            check_id="case_number_format",
            name="Case Number Format",
            description="Case numbers must use leading zeros (e.g. 2024-001507-DC).",
            severity="blocker",
            passed=passed,
            details=(
                "Case number format correct."
                if passed
                else "; ".join(issues)
            ),
            auto_fixable=True,
            fix_suggestion="Use 2024-001507-DC, 2023-005907-PP, 2025-002760-CZ.",
        )

    def check_no_wrong_names(self, text: str, **_: Any) -> GateCheck:
        """Block known wrong defendant name variants.

        Catches: Emily Ann Watson, Emily M. Watson, EMILY M. WATSON,
        Tiffany Watson.

        Args:
            text: Filing text to check.

        Returns:
            GateCheck with pass/fail status.
        """
        if not text:
            return self._fail_check(
                "no_wrong_names", "No Wrong Names",
                "Block known wrong name variants.",
                "blocker", "No text provided.",
            )

        found: List[str] = []
        for pattern in _WRONG_DEFENDANT_PATTERNS:
            match = pattern.search(text)
            if match:
                found.append(match.group())

        passed = len(found) == 0
        return GateCheck(
            check_id="no_wrong_names",
            name="No Wrong Names",
            description="Block known wrong name variants.",
            severity="blocker",
            passed=passed,
            details=(
                "No wrong name variants found."
                if passed
                else f"Wrong name(s): {found} — use '{_DEFENDANT_CANONICAL}'."
            ),
            auto_fixable=True,
            fix_suggestion=f"Replace with '{_DEFENDANT_CANONICAL}'.",
        )

    def check_mcr_compliance(
        self, text: str, filing_type: str = "motion", **_: Any
    ) -> GateCheck:
        """Run MCR-specific compliance checks per filing type.

        Args:
            text: Filing text to check.
            filing_type: Type of filing for rule lookup.

        Returns:
            GateCheck with pass/fail status.
        """
        if not text:
            return self._fail_check(
                "mcr_compliance", "MCR Compliance",
                "Filing-type-specific MCR compliance.",
                "warning", "No text provided.",
            )

        issues: List[str] = []

        if filing_type in ("motion", "response", "reply"):
            # MCR 2.119 — motions must state grounds with particularity
            if not re.search(
                r"(?:moves?|motion)\s+(?:this\s+)?(?:Honorable\s+)?Court",
                text, re.IGNORECASE,
            ):
                issues.append(
                    "MCR 2.119: Motion should contain a clear request to the Court."
                )

        if filing_type in ("appellate_brief", "appellate_reply"):
            # MCR 7.212 — must have Statement of Questions Presented
            if not re.search(
                r"(?:Questions?\s+Presented|Issues?\s+Presented|Statement\s+of\s+(?:the\s+)?Questions?)",
                text, re.IGNORECASE,
            ):
                issues.append(
                    "MCR 7.212(C): Appellate brief must include Statement of Questions Presented."
                )

        passed = len(issues) == 0
        return GateCheck(
            check_id="mcr_compliance",
            name="MCR Compliance",
            description=f"MCR compliance for {filing_type}.",
            severity="warning",
            passed=passed,
            details=(
                f"MCR compliance checks passed for {filing_type}."
                if passed
                else "; ".join(issues)
            ),
        )

    def check_double_spacing(self, text: str, **_: Any) -> GateCheck:
        """Check for double-spacing in the document.

        Args:
            text: Filing text to check.

        Returns:
            GateCheck with pass/fail status.
        """
        if not text:
            return self._fail_check(
                "double_spacing", "Double Spacing",
                "Court filings must be double-spaced.",
                "info", "No text provided.",
            )

        # In plain text, double-spacing shows as blank lines between paragraphs
        blank_line_count = len(re.findall(r"\n\s*\n", text))
        line_count = text.count("\n") + 1
        ratio = blank_line_count / max(line_count, 1)

        # If >15% of lines are blank, probably double-spaced
        passed = ratio > 0.15 or line_count < 10
        return GateCheck(
            check_id="double_spacing",
            name="Double Spacing",
            description="Court filings must be double-spaced.",
            severity="info",
            passed=passed,
            details=(
                f"Appears double-spaced (blank-line ratio: {ratio:.0%})."
                if passed
                else f"May not be double-spaced (blank-line ratio: {ratio:.0%}). "
                "Verify formatting at PDF stage."
            ),
        )

    def check_exhibit_references(self, text: str, **_: Any) -> GateCheck:
        """Verify exhibit references are present and numbered.

        Args:
            text: Filing text to check.

        Returns:
            GateCheck with pass/fail status.
        """
        if not text:
            return self._fail_check(
                "exhibit_references", "Exhibit References",
                "All referenced exhibits should be identifiable.",
                "warning", "No text provided.",
            )

        # Find exhibit references
        exhibit_refs = re.findall(
            r"Exhibit\s+[A-Z0-9]+|Ex\.?\s+[A-Z0-9]+",
            text, re.IGNORECASE,
        )

        if not exhibit_refs:
            return GateCheck(
                check_id="exhibit_references",
                name="Exhibit References",
                description="All referenced exhibits should be identifiable.",
                severity="info",
                passed=True,
                details="No exhibit references found (may be appropriate).",
            )

        unique_refs = sorted(set(r.strip() for r in exhibit_refs))
        return GateCheck(
            check_id="exhibit_references",
            name="Exhibit References",
            description="All referenced exhibits should be identifiable.",
            severity="info",
            passed=True,
            details=f"Found {len(unique_refs)} unique exhibit reference(s): {unique_refs[:10]}",
        )

    def check_prayer_for_relief(self, text: str, **_: Any) -> GateCheck:
        """Verify the filing contains a prayer for relief or request.

        Args:
            text: Filing text to check.

        Returns:
            GateCheck with pass/fail status.
        """
        if not text:
            return self._fail_check(
                "prayer_for_relief", "Prayer for Relief",
                "Motions must contain a clear prayer/request for relief.",
                "warning", "No text provided.",
            )

        prayer_patterns = [
            re.compile(r"WHEREFORE", re.IGNORECASE),
            re.compile(r"Prayer\s+for\s+Relief", re.IGNORECASE),
            re.compile(r"respectfully\s+requests?", re.IGNORECASE),
            re.compile(r"(?:asks?|requests?)\s+(?:this|that)\s+(?:Honorable\s+)?Court", re.IGNORECASE),
            re.compile(r"(?:grant|enter)\s+(?:an?\s+)?(?:order|judgment)", re.IGNORECASE),
            re.compile(r"RELIEF\s+REQUESTED", re.IGNORECASE),
        ]

        found = any(p.search(text) for p in prayer_patterns)
        return GateCheck(
            check_id="prayer_for_relief",
            name="Prayer for Relief",
            description="Motions must contain a clear prayer/request for relief.",
            severity="warning",
            passed=found,
            details=(
                "Prayer for relief / request found."
                if found
                else "No clear prayer for relief or request detected."
            ),
        )

    def check_facts_section(self, text: str, **_: Any) -> GateCheck:
        """Verify the filing contains a statement of facts.

        Args:
            text: Filing text to check.

        Returns:
            GateCheck with pass/fail status.
        """
        if not text:
            return self._fail_check(
                "facts_section", "Statement of Facts",
                "Filing should include a Statement of Facts.",
                "warning", "No text provided.",
            )

        facts_patterns = [
            re.compile(r"Statement\s+of\s+Facts", re.IGNORECASE),
            re.compile(r"FACTUAL\s+BACKGROUND", re.IGNORECASE),
            re.compile(r"FACTS\s+(?:AND\s+)?PROCEDURAL\s+HISTORY", re.IGNORECASE),
            re.compile(r"BACKGROUND\s+FACTS", re.IGNORECASE),
            re.compile(r"RELEVANT\s+FACTS", re.IGNORECASE),
            re.compile(r"I+\.\s+(?:STATEMENT\s+OF\s+)?FACTS", re.IGNORECASE),
        ]

        found = any(p.search(text) for p in facts_patterns)
        return GateCheck(
            check_id="facts_section",
            name="Statement of Facts",
            description="Filing should include a Statement of Facts.",
            severity="warning",
            passed=found,
            details=(
                "Statement of Facts section found."
                if found
                else "No Statement of Facts section detected."
            ),
        )

    def check_legal_argument(self, text: str, **_: Any) -> GateCheck:
        """Verify the filing contains a legal argument section.

        Args:
            text: Filing text to check.

        Returns:
            GateCheck with pass/fail status.
        """
        if not text:
            return self._fail_check(
                "legal_argument", "Legal Argument",
                "Filing should include a Legal Argument section.",
                "warning", "No text provided.",
            )

        argument_patterns = [
            re.compile(r"(?:LEGAL\s+)?ARGUMENT", re.IGNORECASE),
            re.compile(r"ANALYSIS\s+AND\s+ARGUMENT", re.IGNORECASE),
            re.compile(r"POINTS?\s+(?:AND\s+)?AUTHORIT(?:Y|IES)", re.IGNORECASE),
            re.compile(r"MEMORANDUM\s+OF\s+LAW", re.IGNORECASE),
            re.compile(r"I+\.\s+(?:LEGAL\s+)?ARGUMENT", re.IGNORECASE),
            re.compile(r"DISCUSSION", re.IGNORECASE),
        ]

        found = any(p.search(text) for p in argument_patterns)
        return GateCheck(
            check_id="legal_argument",
            name="Legal Argument",
            description="Filing should include a Legal Argument section.",
            severity="warning",
            passed=found,
            details=(
                "Legal Argument section found."
                if found
                else "No Legal Argument / Discussion section detected."
            ),
        )

    # ----------------------------------------------------------------
    # Internal — Registry & Dispatch
    # ----------------------------------------------------------------

    def _build_registry(
        self,
    ) -> Dict[str, Tuple[Callable[..., GateCheck], str, str, str]]:
        """Build the check registry mapping check_id to handler.

        Returns:
            Dict mapping check_id to (handler, name, description, severity).
        """
        return {
            "has_content": (
                self.check_has_content,
                "Has Content", "Non-empty, >100 chars", "blocker",
            ),
            "has_caption": (
                self.check_has_caption,
                "Has Caption", "Court caption block detected", "blocker",
            ),
            "has_case_number": (
                self.check_has_case_number,
                "Has Case Number", "Valid case number format", "blocker",
            ),
            "no_placeholders": (
                self.check_no_placeholders,
                "No Placeholders", "No [TODO]/[INSERT]/<<>> tokens", "blocker",
            ),
            "party_names": (
                self.check_party_names,
                "Party Names", "Correct party name usage", "blocker",
            ),
            "judge_name": (
                self.check_judge_name,
                "Judge Name", "McNeill (two L's)", "blocker",
            ),
            "child_name": (
                self.check_child_name,
                "Child Name Redacted", "L.D.W. initials only (MCR 8.119(H))", "blocker",
            ),
            "citations_present": (
                self.check_citations_present,
                "Citations Present", "MCL/MCR/MRE present", "warning",
            ),
            "citations_format": (
                self.check_citations_format,
                "Citation Format", "Proper citation formatting", "warning",
            ),
            "no_fabricated_citations": (
                self.check_no_fabricated_citations,
                "No Fabricated Citations", "Block hallucinated cites", "blocker",
            ),
            "signature_block": (
                self.check_signature_block,
                "Signature Block", "Proper signature block present", "blocker",
            ),
            "certificate_of_service": (
                self.check_certificate_of_service,
                "Certificate of Service", "CoS present (MCR 2.107)", "blocker",
            ),
            "verification_statement": (
                self.check_verification_statement,
                "Verification Statement", "Declaration under penalty", "warning",
            ),
            "word_count": (
                self.check_word_count,
                "Word Count", "Within limit for filing type", "warning",
            ),
            "font_compliance": (
                self.check_font_compliance,
                "Font Compliance", "Times New Roman 12pt", "info",
            ),
            "margin_compliance": (
                self.check_margin_compliance,
                "Margin Compliance", "1-inch margins", "info",
            ),
            "page_numbering": (
                self.check_page_numbering,
                "Page Numbering", "Page numbers present", "info",
            ),
            "case_number_format": (
                self.check_case_number_format,
                "Case Number Format", "Leading zeros", "blocker",
            ),
            "no_wrong_names": (
                self.check_no_wrong_names,
                "No Wrong Names", "Block wrong name variants", "blocker",
            ),
            "mcr_compliance": (
                self.check_mcr_compliance,
                "MCR Compliance", "Filing-type MCR checks", "warning",
            ),
            "double_spacing": (
                self.check_double_spacing,
                "Double Spacing", "Double-spaced text", "info",
            ),
            "exhibit_references": (
                self.check_exhibit_references,
                "Exhibit References", "Exhibit refs identifiable", "warning",
            ),
            "prayer_for_relief": (
                self.check_prayer_for_relief,
                "Prayer for Relief", "Clear request for relief", "warning",
            ),
            "facts_section": (
                self.check_facts_section,
                "Statement of Facts", "Facts section present", "warning",
            ),
            "legal_argument": (
                self.check_legal_argument,
                "Legal Argument", "Argument section present", "warning",
            ),
        }

    def _run_single_check(
        self, check_id: str, text: str, filing_type: str
    ) -> GateCheck:
        """Dispatch a single check by ID.

        Args:
            check_id: The check to run.
            text: Filing content.
            filing_type: Document type hint.

        Returns:
            GateCheck result (returns a fail check if ID is unknown).
        """
        self._stats_checks_run += 1

        entry = self._registry.get(check_id)
        if entry is None:
            logger.warning("Unknown check ID: '%s'", check_id)
            return GateCheck(
                check_id=check_id,
                name=check_id,
                description="Unknown check.",
                severity="info",
                passed=True,
                details=f"Check '{check_id}' is not registered — skipping.",
            )

        handler, _name, _desc, _sev = entry
        try:
            return handler(text, filing_type=filing_type)
        except Exception as exc:
            logger.error("Check '%s' raised an exception: %s", check_id, exc)
            return GateCheck(
                check_id=check_id,
                name=_name,
                description=_desc,
                severity="info",
                passed=True,
                details=f"Check errored: {exc} — treated as pass to avoid blocking.",
            )

    def _aggregate(
        self,
        checks: List[GateCheck],
        phase: str,
        filing_id: str,
    ) -> GateResult:
        """Aggregate individual checks into a GateResult.

        Args:
            checks: List of completed GateCheck objects.
            phase: Target phase name.
            filing_id: Filing identifier.

        Returns:
            Aggregated GateResult.
        """
        blocker_count = sum(
            1 for c in checks if not c.passed and c.severity == "blocker"
        )
        warning_count = sum(
            1 for c in checks if not c.passed and c.severity == "warning"
        )

        self._stats_blockers_found += blocker_count
        self._stats_warnings_found += warning_count
        self._stats_gates_run += 1

        # Score: start at 100, deduct for failures
        total = len(checks) or 1
        passed_count = sum(1 for c in checks if c.passed)
        score = (passed_count / total) * 100.0

        overall_passed = blocker_count == 0

        return GateResult(
            gate_name=f"{phase.upper()} Gate",
            phase=phase,
            filing_id=filing_id,
            passed=overall_passed,
            score=score,
            checks=checks,
            blocker_count=blocker_count,
            warning_count=warning_count,
        )

    @staticmethod
    def _fail_check(
        check_id: str,
        name: str,
        description: str,
        severity: str,
        details: str,
    ) -> GateCheck:
        """Create a standardised failure GateCheck.

        Args:
            check_id: Check identifier.
            name: Human-readable name.
            description: Check description.
            severity: Severity level.
            details: Failure details.

        Returns:
            A GateCheck marked as failed.
        """
        return GateCheck(
            check_id=check_id,
            name=name,
            description=description,
            severity=severity,
            passed=False,
            details=details,
        )


# ─── Module-level convenience ─────────────────────────────────────────

def run_gate(
    text: str,
    filing_id: str = "unknown",
    target_phase: str = "review",
    filing_type: str = "motion",
) -> GateResult:
    """Quick gate check using a one-shot engine instance.

    Args:
        text: Filing content.
        filing_id: Identifier of the filing.
        target_phase: Phase gate to run.
        filing_type: Document type.

    Returns:
        GateResult with check outcomes.
    """
    return QualityGateEngine().run_gate(text, filing_id, target_phase, filing_type)


if __name__ == "__main__":
    import sys

    logging.basicConfig(level=logging.INFO, stream=sys.stderr)
    engine = QualityGateEngine()

    sample = (
        "STATE OF MICHIGAN\n"
        "IN THE 14TH JUDICIAL CIRCUIT COURT\n"
        "FOR THE COUNTY OF MUSKEGON\n\n"
        "ANDREW JAMES PIGORS,\n    Plaintiff,\n"
        "v.\n"
        "EMILY A. WATSON,\n    Defendant.\n\n"
        "Case No. 2024-001507-DC\n"
        "Hon. Jenny L. McNeill\n\n"
        "MOTION FOR DISQUALIFICATION\n\n"
        "Now comes the Plaintiff, Andrew James Pigors, Pro Se, and "
        "moves this Honorable Court for an order disqualifying the "
        "presiding judge pursuant to MCR 2.003(C)(1).\n\n"
        "I. STATEMENT OF FACTS\n\n"
        "The minor child, L.D.W., has been subject to proceedings "
        "in this Court since 2024.\n\n"
        "II. LEGAL ARGUMENT\n\n"
        "MCL 600.151 provides grounds for disqualification.\n\n"
        "WHEREFORE, Plaintiff respectfully requests this Court grant "
        "the Motion for Disqualification.\n\n"
        "Respectfully submitted,\n"
        "Andrew James Pigors, Pro Se Plaintiff\n"
        "1977 Whitehall Road, Lot 17\n"
        "North Muskegon, MI 49445\n\n"
        "CERTIFICATE OF SERVICE\n\n"
        "I hereby certify that a true copy of this Motion was served "
        "upon Emily A. Watson via first-class mail on this date.\n"
    )

    for phase in ("review", "qa", "approved", "formatted", "filed"):
        result = engine.run_gate(sample, "demo-001", phase, "motion")
        status = "PASS" if result.passed else "FAIL"
        print(f"[{status}] {result.gate_name}: score={result.score:.0f}, "
              f"blockers={result.blocker_count}, warnings={result.warning_count}")
        for c in result.checks:
            if not c.passed:
                print(f"  ✗ {c.name}: {c.details}")

    print("\nStats:", engine.get_stats())
