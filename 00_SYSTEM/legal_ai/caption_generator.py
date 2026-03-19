# -*- coding: utf-8 -*-
"""
caption_generator.py — Michigan Court Caption Generator
========================================================
Auto-generate court captions for all 8 Michigan jurisdictions
relevant to Pigors v. Watson and related matters.

Supported courts:
  1. 14th Judicial Circuit Court — Muskegon County
  2. Michigan Court of Appeals (COA)
  3. Michigan Supreme Court (MSC)
  4. U.S. District Court — Western District of Michigan (WDMI)
  5. Judicial Tenure Commission (JTC)
  6. Attorney Grievance Commission (AGC)
  7. LARA — Michigan DLRA
  8. U.S. Department of Housing and Urban Development (HUD)

Six case lanes:
  A = Custody (2024-001507-DC) — Pigors v. Watson
  B = Housing (2025-002760-CZ) — Pigors v. Shady Oaks et al.
  C = Convergence (multi-lane)
  D = PPO (2023-005907-PP) — Watson PPO matters
  E = Misconduct / JTC — McNeill, Berry
  F = Appellate (COA 366810) — appeal from 14th Circuit

Canonical party data:
  - Plaintiff  : Andrew James Pigors, Pro Se
                  1977 Whitehall Road, Lot 17
                  North Muskegon, MI 49445
  - Defendant  : Emily A. Watson (NOT "Emily Ann", NOT "Emily M.")
  - Child      : L.D.W. per MCR 8.119(H) — MALE
  - Judge      : Hon. Jenny L. McNeill (TWO L's)

Zero external dependencies.  Local-only.
"""

from __future__ import annotations

import logging
import re
import textwrap
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

logger = logging.getLogger("legal_ai.caption_generator")


# ─── Data Classes ─────────────────────────────────────────────────────

@dataclass
class CaptionConfig:
    """Configuration for a single court jurisdiction.

    Attributes:
        court_name: Full official court name (may be multiline).
        court_type: Category — ``circuit``, ``coa``, ``msc``,
                    ``federal``, or ``admin``.
        county: County name (empty for non-circuit courts).
        case_number: Default case number for this court (if any).
        judge: Assigned judge (if applicable).
        division: Court division or sub-unit (if applicable).
    """

    court_name: str
    court_type: str
    county: str = ""
    case_number: str = ""
    judge: str = ""
    division: str = ""

    def to_dict(self) -> Dict[str, Any]:
        """Serialize to a plain dictionary."""
        return {
            "court_name": self.court_name,
            "court_type": self.court_type,
            "county": self.county,
            "case_number": self.case_number,
            "judge": self.judge,
            "division": self.division,
        }


@dataclass
class Caption:
    """A fully-rendered court caption.

    Attributes:
        header: Court name and jurisdiction block.
        parties: Party designation block (plaintiff / defendant).
        case_info: Case number, judge, and division line(s).
        full_caption: Complete caption ready for insertion.
        filing_title: Title of the filing this caption accompanies.
    """

    header: str = ""
    parties: str = ""
    case_info: str = ""
    full_caption: str = ""
    filing_title: str = ""

    def to_dict(self) -> Dict[str, Any]:
        """Serialize to a plain dictionary."""
        return {
            "header": self.header,
            "parties": self.parties,
            "case_info": self.case_info,
            "full_caption": self.full_caption,
            "filing_title": self.filing_title,
        }


# ─── Constants — Party Data ──────────────────────────────────────────

_PLAINTIFF = "ANDREW JAMES PIGORS"
_PLAINTIFF_ADDRESS = (
    "1977 Whitehall Road, Lot 17\n"
    "North Muskegon, MI 49445"
)
_PLAINTIFF_PHONE = ""  # Omitted for privacy in generated captions
_PLAINTIFF_LABEL_PROSE = "Pro Se Plaintiff"

# ── Per-lane defendant lists ──

_DEFENDANTS_LANE_A: List[str] = [
    "EMILY A. WATSON",
]

_DEFENDANTS_LANE_B: List[str] = [
    "SHADY OAKS MANAGEMENT LLC",
    "JEFFREY L. HOOPES",
    "WILLIAM HOOPES",
    "SHADY OAKS MOBILE HOME COMMUNITY",
    "MUSKEGON COUNTY DRAIN COMMISSION",
]

_DEFENDANTS_LANE_D: List[str] = [
    "EMILY A. WATSON",
]

_DEFENDANTS_LANE_E_JTC: List[str] = [
    "HON. JENNY L. McNEILL",
]

_DEFENDANTS_LANE_E_AGC: List[str] = [
    "KYMBERLY A. BERRY",
]

_DEFENDANTS_LANE_F: List[str] = [
    "EMILY A. WATSON",
]

_DEFENDANTS_FEDERAL: List[str] = [
    "EMILY A. WATSON",
    "HON. JENNY L. McNEILL, in her official capacity",
    "MUSKEGON COUNTY",
    "FRIEND OF THE COURT",
]

_DEFENDANTS_HUD: List[str] = [
    "SHADY OAKS MANAGEMENT LLC",
    "JEFFREY L. HOOPES",
    "WILLIAM HOOPES",
    "SHADY OAKS MOBILE HOME COMMUNITY",
]

# ── Lane → Defendants map ──

_LANE_DEFENDANTS: Dict[str, List[str]] = {
    "A": _DEFENDANTS_LANE_A,
    "B": _DEFENDANTS_LANE_B,
    "C": _DEFENDANTS_LANE_A,  # Convergence defaults to Lane A parties
    "D": _DEFENDANTS_LANE_D,
    "E": _DEFENDANTS_LANE_E_JTC,
    "F": _DEFENDANTS_LANE_F,
}

# ── Case numbers per lane ──

_LANE_CASE_NUMBERS: Dict[str, str] = {
    "A": "2024-001507-DC",
    "B": "2025-002760-CZ",
    "C": "",
    "D": "2023-005907-PP",
    "E": "",
    "F": "366810",
}

# ── Lane labels ──

_LANE_LABELS: Dict[str, str] = {
    "A": "Custody",
    "B": "Housing",
    "C": "Convergence",
    "D": "PPO",
    "E": "Misconduct / JTC",
    "F": "Appellate",
}

# ── Wrong case number patterns ──

_WRONG_CASE_FORMATS: Dict[str, str] = {
    "2024-1507-DC": "2024-001507-DC",
    "2023-5907-PP": "2023-005907-PP",
    "2025-2760-CZ": "2025-002760-CZ",
}


# ─── Caption Generator ───────────────────────────────────────────────

class CaptionGenerator:
    """Generate Michigan court captions for all 8 jurisdictions.

    Pre-loaded with Pigors v. Watson party data, case numbers, and
    judge assignments.  Produces correctly formatted captions for
    circuit, appellate, supreme, federal, and administrative courts.

    Example::

        gen = CaptionGenerator()
        cap = gen.generate("14th_circuit", "Motion for Disqualification")
        print(cap.full_caption)
    """

    # ── Court configurations ──

    COURTS: Dict[str, CaptionConfig] = {
        "14th_circuit": CaptionConfig(
            court_name="14TH JUDICIAL CIRCUIT COURT",
            court_type="circuit",
            county="MUSKEGON",
            case_number="2024-001507-DC",
            judge="Hon. Jenny L. McNeill",
            division="Family Division",
        ),
        "14th_circuit_cz": CaptionConfig(
            court_name="14TH JUDICIAL CIRCUIT COURT",
            court_type="circuit",
            county="MUSKEGON",
            case_number="2025-002760-CZ",
            judge="",
            division="Civil Division",
        ),
        "14th_circuit_pp": CaptionConfig(
            court_name="14TH JUDICIAL CIRCUIT COURT",
            court_type="circuit",
            county="MUSKEGON",
            case_number="2023-005907-PP",
            judge="Hon. Jenny L. McNeill",
            division="Family Division",
        ),
        "coa": CaptionConfig(
            court_name="MICHIGAN COURT OF APPEALS",
            court_type="coa",
            county="",
            case_number="366810",
            judge="",
            division="",
        ),
        "msc": CaptionConfig(
            court_name="MICHIGAN SUPREME COURT",
            court_type="msc",
            county="",
            case_number="",
            judge="",
            division="",
        ),
        "wdmi": CaptionConfig(
            court_name=(
                "UNITED STATES DISTRICT COURT\n"
                "WESTERN DISTRICT OF MICHIGAN\n"
                "SOUTHERN DIVISION"
            ),
            court_type="federal",
            county="",
            case_number="",
            judge="",
            division="Southern Division",
        ),
        "jtc": CaptionConfig(
            court_name="JUDICIAL TENURE COMMISSION",
            court_type="admin",
            county="",
            case_number="",
            judge="",
            division="",
        ),
        "agc": CaptionConfig(
            court_name="ATTORNEY GRIEVANCE COMMISSION",
            court_type="admin",
            county="",
            case_number="",
            judge="",
            division="",
        ),
        "lara": CaptionConfig(
            court_name=(
                "MICHIGAN DEPARTMENT OF LICENSING\n"
                "AND REGULATORY AFFAIRS"
            ),
            court_type="admin",
            county="",
            case_number="",
            judge="",
            division="",
        ),
        "hud": CaptionConfig(
            court_name=(
                "U.S. DEPARTMENT OF HOUSING AND\n"
                "URBAN DEVELOPMENT"
            ),
            court_type="admin",
            county="",
            case_number="",
            judge="",
            division="",
        ),
    }

    # ── Court → Default lane mapping ──

    _COURT_LANE_MAP: Dict[str, str] = {
        "14th_circuit": "A",
        "14th_circuit_cz": "B",
        "14th_circuit_pp": "D",
        "coa": "F",
        "msc": "F",
        "wdmi": "A",
        "jtc": "E",
        "agc": "E",
        "lara": "B",
        "hud": "B",
    }

    # ── Court → Defendant override map ──

    _COURT_DEFENDANTS: Dict[str, List[str]] = {
        "14th_circuit": _DEFENDANTS_LANE_A,
        "14th_circuit_cz": _DEFENDANTS_LANE_B,
        "14th_circuit_pp": _DEFENDANTS_LANE_D,
        "coa": _DEFENDANTS_LANE_F,
        "msc": _DEFENDANTS_LANE_F,
        "wdmi": _DEFENDANTS_FEDERAL,
        "jtc": _DEFENDANTS_LANE_E_JTC,
        "agc": _DEFENDANTS_LANE_E_AGC,
        "lara": _DEFENDANTS_LANE_B,
        "hud": _DEFENDANTS_HUD,
    }

    # ── Party role labels per court type ──

    _ROLE_LABELS: Dict[str, Dict[str, str]] = {
        "circuit": {"plaintiff": "Plaintiff", "defendant": "Defendant"},
        "coa": {"plaintiff": "Plaintiff-Appellant", "defendant": "Defendant-Appellee"},
        "msc": {"plaintiff": "Plaintiff-Appellant", "defendant": "Defendant-Appellee"},
        "federal": {"plaintiff": "Plaintiff", "defendant": "Defendant"},
        "admin": {"plaintiff": "Complainant", "defendant": "Respondent"},
    }

    def __init__(self) -> None:
        """Initialise the caption generator."""
        self._stats_generated: int = 0
        self._stats_validated: int = 0
        self._stats_errors: int = 0

    # ----------------------------------------------------------------
    # Public API — Generation
    # ----------------------------------------------------------------

    def generate(
        self,
        court_id: str,
        filing_title: str,
        case_number: Optional[str] = None,
        additional_parties: Optional[List[str]] = None,
    ) -> Caption:
        """Generate a complete court caption.

        Args:
            court_id: Key into ``COURTS`` (e.g. ``"14th_circuit"``).
            filing_title: Title of the filing (e.g. "Motion for Disqualification").
            case_number: Override the default case number for this court.
            additional_parties: Extra defendant/respondent names to include.

        Returns:
            A fully-rendered Caption object.

        Raises:
            ValueError: If ``court_id`` is not recognised.
        """
        config = self.COURTS.get(court_id)
        if config is None:
            self._stats_errors += 1
            raise ValueError(
                f"Unknown court_id '{court_id}'. "
                f"Valid: {sorted(self.COURTS.keys())}"
            )

        effective_case = case_number or config.case_number
        effective_case = self.format_case_number(effective_case)

        defendants = list(self._COURT_DEFENDANTS.get(court_id, []))
        if additional_parties:
            for party in additional_parties:
                if party.upper() not in [d.upper() for d in defendants]:
                    defendants.append(party.upper())

        header = self._build_header(config)
        parties = self._build_parties(config, defendants)
        case_info = self._build_case_info(config, effective_case)
        title_block = self._build_title_block(filing_title)

        divider = self._divider()

        full = (
            f"{header}\n"
            f"\n"
            f"{parties}\n"
            f"\n"
            f"{case_info}\n"
            f"{divider}\n"
            f"\n"
            f"{title_block}"
        )

        self._stats_generated += 1

        caption = Caption(
            header=header,
            parties=parties,
            case_info=case_info,
            full_caption=full,
            filing_title=filing_title,
        )

        logger.info(
            "Generated caption for %s — '%s'",
            court_id,
            filing_title,
        )
        return caption

    def generate_all_variants(
        self,
        filing_title: str,
    ) -> Dict[str, Caption]:
        """Generate captions for every known court.

        Args:
            filing_title: Title of the filing.

        Returns:
            Dict mapping court_id to Caption.
        """
        results: Dict[str, Caption] = {}
        for court_id in self.COURTS:
            try:
                results[court_id] = self.generate(court_id, filing_title)
            except ValueError as exc:
                logger.warning("Skipping %s: %s", court_id, exc)
        return results

    # ----------------------------------------------------------------
    # Public API — Party Blocks
    # ----------------------------------------------------------------

    def get_party_block(
        self,
        lane: str,
        role: str = "plaintiff",
    ) -> str:
        """Get a formatted party block for a given lane and role.

        Args:
            lane: Case lane letter (A–F).
            role: ``"plaintiff"`` or ``"defendant"``.

        Returns:
            Formatted multiline party string.
        """
        lane_upper = lane.upper()

        if role.lower() == "plaintiff":
            return (
                f"{_PLAINTIFF},\n"
                f"    {_PLAINTIFF_LABEL_PROSE},\n"
                f"    {_PLAINTIFF_ADDRESS}"
            )

        defendants = _LANE_DEFENDANTS.get(lane_upper, [])
        if not defendants:
            return "(No defendants for this lane)"

        lines: List[str] = []
        for i, name in enumerate(defendants):
            if i == 0:
                lines.append(f"{name},")
            else:
                lines.append(f"    {name},")
        return "\n".join(lines)

    def get_defendant_block(self, lane: str) -> str:
        """Convenience wrapper — return formatted defendant block.

        Args:
            lane: Case lane letter (A–F).

        Returns:
            Formatted defendant listing.
        """
        return self.get_party_block(lane, role="defendant")

    # ----------------------------------------------------------------
    # Public API — Formatting & Validation
    # ----------------------------------------------------------------

    def format_case_number(self, raw: str) -> str:
        """Normalise a case number, adding leading zeros where needed.

        Args:
            raw: Raw case number string.

        Returns:
            Corrected case number (e.g. "2024-001507-DC").
        """
        if not raw:
            return ""

        corrected = raw.strip()

        # Fix known wrong formats
        for wrong, right in _WRONG_CASE_FORMATS.items():
            if wrong in corrected:
                corrected = corrected.replace(wrong, right)
                logger.debug("Corrected case number: %s → %s", wrong, right)

        # Generic fix: YYYY-N-XX where N has <6 digits
        def _pad_middle(m: re.Match[str]) -> str:
            year, num, suffix = m.group(1), m.group(2), m.group(3)
            return f"{year}-{num.zfill(6)}-{suffix}"

        corrected = re.sub(
            r"(\d{4})-(\d{1,5})-([A-Z]{2})",
            _pad_middle,
            corrected,
        )

        return corrected

    def validate_caption(self, caption_text: str) -> List[str]:
        """Find errors in an existing caption.

        Checks for: wrong names, wrong case-number formats, misspelled
        judge, exposed child name, missing components.

        Args:
            caption_text: The caption text to validate.

        Returns:
            List of issue descriptions (empty = clean).
        """
        if not caption_text:
            return ["Caption text is empty."]

        issues: List[str] = []
        self._stats_validated += 1

        # Wrong defendant names
        wrong_name_patterns = [
            (re.compile(r"Emily\s+Ann\s+Watson", re.IGNORECASE),
             "Wrong defendant name: use 'Emily A. Watson' not 'Emily Ann Watson'."),
            (re.compile(r"Emily\s+M\.?\s+Watson", re.IGNORECASE),
             "Wrong defendant name: use 'Emily A. Watson' not 'Emily M. Watson'."),
            (re.compile(r"Tiffany\s+Watson", re.IGNORECASE),
             "Wrong name: 'Tiffany Watson' is not a party."),
        ]
        for pattern, msg in wrong_name_patterns:
            if pattern.search(caption_text):
                issues.append(msg)

        # Wrong judge name
        if re.search(r"\bMcNeil\b(?!l)", caption_text):
            issues.append(
                "Misspelled judge: 'McNeil' should be 'McNeill' (two L's)."
            )

        # Wrong case number format
        for wrong, right in _WRONG_CASE_FORMATS.items():
            if wrong in caption_text:
                issues.append(
                    f"Wrong case number format: '{wrong}' should be '{right}'."
                )

        # Exposed child name
        if re.search(r"Lincoln\s+(?:David\s+)?Watson", caption_text, re.IGNORECASE):
            issues.append(
                "Child's full name exposed — must use initials 'L.D.W.' "
                "per MCR 8.119(H)."
            )

        # Missing STATE OF MICHIGAN (circuit courts)
        if re.search(r"CIRCUIT\s+COURT", caption_text, re.IGNORECASE):
            if not re.search(r"STATE\s+OF\s+MICHIGAN", caption_text, re.IGNORECASE):
                issues.append(
                    "Circuit court caption missing 'STATE OF MICHIGAN' header."
                )

        # Missing case number
        has_case = bool(
            re.search(r"Case\s+No\.?", caption_text, re.IGNORECASE)
            or re.search(r"Docket\s+No\.?", caption_text, re.IGNORECASE)
            or re.search(r"\b\d{4}-\d{6}-[A-Z]{2}\b", caption_text)
        )
        if not has_case:
            issues.append("No case number detected in caption.")

        # Missing v. / vs. separator
        if not re.search(r"\bv[s]?\.?\s", caption_text, re.IGNORECASE):
            # Admin complaints use "In the Matter of" instead
            if not re.search(r"In\s+the\s+Matter\s+of", caption_text, re.IGNORECASE):
                if not re.search(r"Complainant|Respondent", caption_text, re.IGNORECASE):
                    issues.append(
                        "Missing party separator ('v.' or 'In the Matter of')."
                    )

        return issues

    # ----------------------------------------------------------------
    # Public API — Statistics
    # ----------------------------------------------------------------

    def get_stats(self) -> Dict[str, Any]:
        """Return operational statistics.

        Returns:
            Dict with generation counts, available courts, and lane info.
        """
        return {
            "version": "1.0.0",
            "captions_generated": self._stats_generated,
            "captions_validated": self._stats_validated,
            "errors": self._stats_errors,
            "available_courts": sorted(self.COURTS.keys()),
            "court_count": len(self.COURTS),
            "lanes": dict(_LANE_LABELS),
            "lane_case_numbers": dict(_LANE_CASE_NUMBERS),
        }

    # ----------------------------------------------------------------
    # Internal — Building Blocks
    # ----------------------------------------------------------------

    def _build_header(self, config: CaptionConfig) -> str:
        """Build the court name header block.

        Args:
            config: Court configuration.

        Returns:
            Formatted header string.
        """
        lines: List[str] = []

        if config.court_type == "circuit":
            lines.append("STATE OF MICHIGAN")
            lines.append(f"IN THE {config.court_name}")
            if config.county:
                lines.append(f"FOR THE COUNTY OF {config.county}")
        elif config.court_type == "coa":
            lines.append("STATE OF MICHIGAN")
            lines.append(f"IN THE {config.court_name}")
        elif config.court_type == "msc":
            lines.append("STATE OF MICHIGAN")
            lines.append(f"IN THE {config.court_name}")
        elif config.court_type == "federal":
            lines.append(config.court_name)
        elif config.court_type == "admin":
            lines.append("STATE OF MICHIGAN")
            lines.append(config.court_name)

        return "\n".join(lines)

    def _build_parties(
        self,
        config: CaptionConfig,
        defendants: List[str],
    ) -> str:
        """Build the party designation block.

        Args:
            config: Court configuration.
            defendants: List of defendant/respondent names.

        Returns:
            Formatted party block.
        """
        role_labels = self._ROLE_LABELS.get(
            config.court_type, {"plaintiff": "Plaintiff", "defendant": "Defendant"}
        )
        p_label = role_labels["plaintiff"]
        d_label = role_labels["defendant"]

        # For admin (JTC/AGC), use "In the Matter of" style
        if config.court_type == "admin" and defendants:
            complainant_block = (
                f"{_PLAINTIFF},\n"
                f"    {p_label},"
            )
            respondent_lines = []
            for i, name in enumerate(defendants):
                suffix = "." if i == len(defendants) - 1 else ","
                if i == 0:
                    respondent_lines.append(f"{name}{suffix}")
                else:
                    respondent_lines.append(f"    {name}{suffix}")
            respondent_label = (
                f"    {d_label}{'s' if len(defendants) > 1 else ''}."
            )
            respondent_block = "\n".join(respondent_lines)

            return (
                f"{complainant_block}\n"
                f"\n"
                f"v.\n"
                f"\n"
                f"{respondent_block}\n"
                f"{respondent_label}"
            )

        # Standard adversarial format
        plaintiff_block = (
            f"{_PLAINTIFF},\n"
            f"    {p_label},"
        )

        defendant_lines: List[str] = []
        for i, name in enumerate(defendants):
            is_last = i == len(defendants) - 1
            suffix = "." if is_last else ","
            if i == 0:
                defendant_lines.append(f"{name}{suffix}")
            else:
                defendant_lines.append(f"    {name}{suffix}")

        if len(defendants) > 1:
            d_label_line = f"    {d_label}s."
        elif len(defendants) == 1:
            d_label_line = f"    {d_label}."
        else:
            d_label_line = f"    {d_label}."
            defendant_lines = ["(Unknown Defendant)"]

        defendant_block = "\n".join(defendant_lines)

        return (
            f"{plaintiff_block}\n"
            f"\n"
            f"v.\n"
            f"\n"
            f"{defendant_block}\n"
            f"{d_label_line}"
        )

    def _build_case_info(
        self,
        config: CaptionConfig,
        case_number: str,
    ) -> str:
        """Build the case number / judge info line(s).

        Args:
            config: Court configuration.
            case_number: Formatted case number.

        Returns:
            Formatted case info string.
        """
        lines: List[str] = []

        if case_number:
            if config.court_type == "coa":
                lines.append(f"COA Case No. {case_number}")
            elif config.court_type == "msc":
                lines.append(f"MSC Case No. {case_number}")
            elif config.court_type == "federal":
                lines.append(f"Case No. {case_number}")
            else:
                lines.append(f"Case No. {case_number}")

        if config.judge:
            lines.append(config.judge)

        if config.division and config.court_type == "circuit":
            lines.append(config.division)

        return "\n".join(lines)

    @staticmethod
    def _build_title_block(filing_title: str) -> str:
        """Build the filing title block.

        Args:
            filing_title: Title of the filing document.

        Returns:
            Centred, uppercased title string.
        """
        return filing_title.upper()

    @staticmethod
    def _divider() -> str:
        """Return a horizontal divider line."""
        return "/" * 40


# ─── Module-level convenience ─────────────────────────────────────────

def generate(
    court_id: str,
    filing_title: str,
    case_number: Optional[str] = None,
) -> Caption:
    """Quick caption generation using a one-shot engine instance.

    Args:
        court_id: Court identifier key.
        filing_title: Title of the filing.
        case_number: Optional case number override.

    Returns:
        A fully-rendered Caption.
    """
    return CaptionGenerator().generate(court_id, filing_title, case_number)


if __name__ == "__main__":
    import sys

    logging.basicConfig(level=logging.INFO, stream=sys.stderr)
    gen = CaptionGenerator()

    print("=" * 60)
    print("CAPTION GENERATOR — SMOKE TEST")
    print("=" * 60)

    # Generate for each court
    for court_id in sorted(gen.COURTS.keys()):
        print(f"\n{'─' * 60}")
        print(f"Court: {court_id}")
        print(f"{'─' * 60}")
        try:
            cap = gen.generate(court_id, "Motion for Disqualification")
            print(cap.full_caption)
        except ValueError as exc:
            print(f"  ERROR: {exc}")

    # Validate a bad caption
    print(f"\n{'=' * 60}")
    print("VALIDATION TEST — Bad Caption")
    print(f"{'=' * 60}")
    bad_caption = (
        "IN THE CIRCUIT COURT\n"
        "Emily Ann Watson, Defendant\n"
        "Case No. 2024-1507-DC\n"
        "Hon. McNeil\n"
        "Lincoln David Watson\n"
    )
    issues = gen.validate_caption(bad_caption)
    for issue in issues:
        print(f"  ✗ {issue}")

    # Stats
    print(f"\n{'=' * 60}")
    print("STATS")
    print(f"{'=' * 60}")
    import json as _json
    print(_json.dumps(gen.get_stats(), indent=2))
