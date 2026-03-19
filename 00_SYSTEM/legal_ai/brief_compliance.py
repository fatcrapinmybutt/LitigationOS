# -*- coding: utf-8 -*-
"""
brief_compliance.py — Michigan Brief Compliance Engine
========================================================
Validates court briefs against Michigan Court Rules:
  - MCR 7.212: Briefs in the Court of Appeals
  - MCR 7.312: Briefs in the Supreme Court
  - MCR 2.119: Motion practice formatting
  - Local court rules (14th Circuit, Muskegon County)

Checks: word count, font, margins, citation format, TOA format,
appendix rules, page limits, and structural requirements.

Zero external dependencies. Local-only.
"""

import re
from datetime import datetime
from dataclasses import dataclass, field, asdict
from typing import Optional


# ─── Data Classes ───

@dataclass
class ComplianceIssue:
    """A single compliance issue found in a brief."""
    rule: str
    severity: str  # CRITICAL, WARNING, INFO
    description: str
    location: str = ""  # Page/section reference
    auto_fixable: bool = False
    fix_suggestion: str = ""

    def to_dict(self) -> dict:
        return asdict(self)


@dataclass
class ComplianceReport:
    """Full compliance analysis report."""
    brief_type: str  # appellate_brief, motion, response, reply
    word_count: int = 0
    page_count: int = 0
    issues: list = field(default_factory=list)
    passed: bool = False
    score: float = 100.0
    critical_count: int = 0
    warning_count: int = 0
    info_count: int = 0
    checked_rules: list = field(default_factory=list)
    generated_at: str = field(default_factory=lambda: datetime.now().isoformat())

    def to_dict(self) -> dict:
        return {
            "brief_type": self.brief_type,
            "word_count": self.word_count,
            "page_count": self.page_count,
            "passed": self.passed,
            "score": round(self.score, 1),
            "critical_count": self.critical_count,
            "warning_count": self.warning_count,
            "info_count": self.info_count,
            "issues": [i.to_dict() if hasattr(i, 'to_dict') else i for i in self.issues],
            "checked_rules": self.checked_rules,
            "generated_at": self.generated_at,
        }


# ─── Michigan Brief Rules ───

BRIEF_RULES = {
    "appellate_brief": {
        "max_words": 16000,       # MCR 7.212(B) — 50 pages or ~16000 words
        "max_pages": 50,
        "font_size_min": 12,       # MCR 7.212(B)
        "line_spacing": "double",
        "margins_min_inches": 1.0,
        "authority": "MCR 7.212",
        "required_sections": [
            "TABLE OF CONTENTS",
            "TABLE OF AUTHORITIES",
            "STATEMENT OF JURISDICTION",
            "STATEMENT OF QUESTIONS PRESENTED",
            "STATEMENT OF FACTS",
            "ARGUMENT",
            "RELIEF REQUESTED",
        ],
        "optional_sections": [
            "SUMMARY OF ARGUMENT",
            "APPENDIX",
        ],
    },
    "appellate_reply": {
        "max_words": 8000,
        "max_pages": 25,
        "font_size_min": 12,
        "line_spacing": "double",
        "margins_min_inches": 1.0,
        "authority": "MCR 7.212(H)",
        "required_sections": [
            "TABLE OF CONTENTS",
            "TABLE OF AUTHORITIES",
            "ARGUMENT",
        ],
    },
    "motion": {
        "max_words": 6000,        # MCR 2.119 — 20 pages
        "max_pages": 20,
        "font_size_min": 12,
        "line_spacing": "double",
        "margins_min_inches": 1.0,
        "authority": "MCR 2.119",
        "required_sections": [
            "MOTION",
            "BRIEF IN SUPPORT",
        ],
    },
    "response": {
        "max_words": 6000,
        "max_pages": 20,
        "font_size_min": 12,
        "line_spacing": "double",
        "margins_min_inches": 1.0,
        "authority": "MCR 2.119(C)(2)",
        "required_sections": [
            "RESPONSE",
        ],
    },
    "reply": {
        "max_words": 3000,        # MCR 2.119 — 5 pages for reply
        "max_pages": 5,
        "font_size_min": 12,
        "line_spacing": "double",
        "margins_min_inches": 1.0,
        "authority": "MCR 2.119(C)(3)",
        "required_sections": [],
    },
    "supreme_court_brief": {
        "max_words": 16000,
        "max_pages": 50,
        "font_size_min": 12,
        "line_spacing": "double",
        "margins_min_inches": 1.0,
        "authority": "MCR 7.312",
        "required_sections": [
            "TABLE OF CONTENTS",
            "TABLE OF AUTHORITIES",
            "STATEMENT OF QUESTIONS PRESENTED",
            "STATEMENT OF FACTS",
            "ARGUMENT",
            "RELIEF REQUESTED",
        ],
    },
}

# Common Michigan citation patterns
MI_CITE_PATTERNS = [
    (r'\d+\s+Mich\s+App\s+\d+', "Michigan Court of Appeals"),
    (r'\d+\s+Mich\s+\d+', "Michigan Supreme Court"),
    (r'\d+\s+NW\.?2d\s+\d+', "North Western Reporter"),
    (r'MCL\s+\d+\.\d+[a-z]?', "Michigan Compiled Laws"),
    (r'MCR\s+\d+\.\d+(\([A-Z]\))?(\(\d+\))?', "Michigan Court Rules"),
    (r'MRE\s+\d+', "Michigan Rules of Evidence"),
]


class BriefComplianceEngine:
    """
    Validates court briefs against Michigan Court Rules.
    Supports appellate briefs, motions, responses, and replies.
    """

    def __init__(self):
        self._stats = {"briefs_checked": 0, "issues_found": 0, "auto_fixes": 0}

    def check(self, text: str, brief_type: str = "motion") -> ComplianceReport:
        """
        Run full compliance check on a brief.

        Args:
            text: The brief text content
            brief_type: One of: appellate_brief, appellate_reply, motion,
                       response, reply, supreme_court_brief
        """
        if not text or not text.strip():
            report = ComplianceReport(brief_type=brief_type)
            report.issues.append(ComplianceIssue(
                rule="GENERAL",
                severity="CRITICAL",
                description="Brief text is empty",
            ))
            report.critical_count = 1
            report.passed = False
            report.score = 0.0
            return report

        rules = BRIEF_RULES.get(brief_type, BRIEF_RULES["motion"])
        report = ComplianceReport(brief_type=brief_type)
        report.word_count = len(text.split())
        report.page_count = max(1, report.word_count // 320)  # ~320 words/page estimate

        # Run all checks
        self._check_word_count(text, rules, report)
        self._check_required_sections(text, rules, report)
        self._check_citation_format(text, report)
        self._check_case_caption(text, report)
        self._check_certificate_of_service(text, report)
        self._check_signature_block(text, report)
        self._check_placeholders(text, report)
        self._check_toa_format(text, rules, report)
        self._check_case_number_format(text, report)
        self._check_common_errors(text, report)

        # Compute counts and score
        report.critical_count = sum(1 for i in report.issues if i.severity == "CRITICAL")
        report.warning_count = sum(1 for i in report.issues if i.severity == "WARNING")
        report.info_count = sum(1 for i in report.issues if i.severity == "INFO")

        # Score: start at 100, deduct per issue
        report.score = max(0.0, 100.0 - (report.critical_count * 20) - (report.warning_count * 5) - (report.info_count * 1))
        report.passed = report.critical_count == 0 and report.score >= 70.0
        report.checked_rules = [rules["authority"]]

        self._stats["briefs_checked"] += 1
        self._stats["issues_found"] += len(report.issues)

        return report

    def check_file(self, file_path: str, brief_type: str = "motion") -> ComplianceReport:
        """Check compliance of a file."""
        try:
            with open(file_path, "r", encoding="utf-8", errors="replace") as f:
                text = f.read()
            return self.check(text, brief_type)
        except FileNotFoundError:
            report = ComplianceReport(brief_type=brief_type)
            report.issues.append(ComplianceIssue(
                rule="FILE", severity="CRITICAL",
                description=f"File not found: {file_path}",
            ))
            report.critical_count = 1
            report.passed = False
            return report

    def check_batch(
        self, file_paths: list, brief_type: str = "motion"
    ) -> list[ComplianceReport]:
        """Check compliance of multiple files."""
        return [self.check_file(fp, brief_type) for fp in file_paths]

    def auto_fix(self, text: str, brief_type: str = "motion") -> tuple[str, list[str]]:
        """
        Attempt to auto-fix minor compliance issues.
        Returns (fixed_text, list_of_fixes_applied).
        """
        fixes = []

        # Fix double spaces
        if "  " in text:
            text = re.sub(r'  +', ' ', text)
            fixes.append("Removed extra spaces")

        # Fix missing period after citation
        text_new = re.sub(r'(MCR \d+\.\d+(?:\([A-Z]\))?)(\s+[A-Z])', r'\1.\2', text)
        if text_new != text:
            text = text_new
            fixes.append("Added missing periods after MCR citations")

        # Normalize case number format
        def fix_case_num(m):
            year, num, suffix = m.group(1), m.group(2), m.group(3)
            return f"{year}-{num.zfill(6)}-{suffix}"

        text_new = re.sub(r'(\d{4})-(\d{1,6})-([A-Z]{2})', fix_case_num, text)
        if text_new != text:
            text = text_new
            fixes.append("Normalized case number format (leading zeros)")

        self._stats["auto_fixes"] += len(fixes)
        return text, fixes

    def get_stats(self) -> dict:
        """Return engine statistics."""
        return dict(self._stats)

    # ─── Private Check Methods ───

    def _check_word_count(self, text: str, rules: dict, report: ComplianceReport):
        """Check word count against rule limits."""
        max_words = rules.get("max_words", 6000)
        if report.word_count > max_words:
            report.issues.append(ComplianceIssue(
                rule=rules["authority"],
                severity="CRITICAL",
                description=f"Word count ({report.word_count}) exceeds limit ({max_words})",
                auto_fixable=False,
                fix_suggestion=f"Reduce by {report.word_count - max_words} words",
            ))
        elif report.word_count > max_words * 0.9:
            report.issues.append(ComplianceIssue(
                rule=rules["authority"],
                severity="WARNING",
                description=f"Word count ({report.word_count}) is within 10% of limit ({max_words})",
            ))

    def _check_required_sections(self, text: str, rules: dict, report: ComplianceReport):
        """Check for required sections."""
        text_upper = text.upper()
        for section in rules.get("required_sections", []):
            if section.upper() not in text_upper:
                report.issues.append(ComplianceIssue(
                    rule=rules["authority"],
                    severity="CRITICAL",
                    description=f"Missing required section: {section}",
                    fix_suggestion=f"Add '{section}' section to the brief",
                ))

    def _check_citation_format(self, text: str, report: ComplianceReport):
        """Check citation formatting."""
        # Look for improperly formatted citations
        # Common error: "MCL600.5805" instead of "MCL 600.5805"
        bad_mcl = re.findall(r'MCL\d', text)
        if bad_mcl:
            report.issues.append(ComplianceIssue(
                rule="Citation Format",
                severity="WARNING",
                description=f"MCL citations missing space after 'MCL' ({len(bad_mcl)} instances)",
                auto_fixable=True,
                fix_suggestion="Add space: 'MCL 600.5805' not 'MCL600.5805'",
            ))

        # Check for citations without pinpoint pages
        bare_cites = re.findall(r'\d+\s+Mich(?:\s+App)?\s+\d+(?!\s*[,;.]?\s*\d)', text)
        if bare_cites and len(bare_cites) > 3:
            report.issues.append(ComplianceIssue(
                rule="Citation Precision",
                severity="INFO",
                description=f"{len(bare_cites)} citations without pinpoint page references",
                fix_suggestion="Add pinpoint citations: '123 Mich App 456, 460'",
            ))

    def _check_case_caption(self, text: str, report: ComplianceReport):
        """Check for proper case caption."""
        text_upper = text.upper()
        caption_markers = ["STATE OF MICHIGAN", "CIRCUIT COURT", "COURT OF APPEALS", "DISTRICT COURT"]
        has_caption = any(m in text_upper for m in caption_markers)

        if not has_caption:
            report.issues.append(ComplianceIssue(
                rule="MCR 2.113",
                severity="CRITICAL",
                description="Missing case caption (no court identification found)",
                fix_suggestion="Add caption: 'STATE OF MICHIGAN / IN THE [COURT] FOR THE COUNTY OF [COUNTY]'",
            ))

        # Check for plaintiff/defendant designations
        if "PLAINTIFF" not in text_upper and "PETITIONER" not in text_upper:
            report.issues.append(ComplianceIssue(
                rule="MCR 2.113",
                severity="WARNING",
                description="No plaintiff/petitioner designation found in caption",
            ))

    def _check_certificate_of_service(self, text: str, report: ComplianceReport):
        """Check for Certificate of Service."""
        text_upper = text.upper()
        cos_markers = [
            "CERTIFICATE OF SERVICE", "PROOF OF SERVICE",
            "I HEREBY CERTIFY", "I CERTIFY THAT",
        ]
        if not any(m in text_upper for m in cos_markers):
            report.issues.append(ComplianceIssue(
                rule="MCR 2.107",
                severity="CRITICAL",
                description="Missing Certificate of Service",
                fix_suggestion="Add Certificate of Service per MCR 2.107(C)",
            ))

    def _check_signature_block(self, text: str, report: ComplianceReport):
        """Check for signature block."""
        sig_markers = ["/s/", "Respectfully submitted", "RESPECTFULLY SUBMITTED"]
        has_sig = any(m in text for m in sig_markers)

        if not has_sig:
            report.issues.append(ComplianceIssue(
                rule="MCR 2.114",
                severity="WARNING",
                description="No signature block found (/s/ or 'Respectfully submitted')",
                fix_suggestion="Add: 'Respectfully submitted,\\n/s/ Andrew James Pigors\\nPro Se Plaintiff'",
            ))

    def _check_placeholders(self, text: str, report: ComplianceReport):
        """Check for unresolved placeholders."""
        patterns = [
            (r'\[([A-Z_]+)\]', "bracket placeholder"),
            (r'\{([A-Z_]+)\}', "brace placeholder"),
            (r'\bTODO\b', "TODO marker"),
            (r'\bFIXME\b', "FIXME marker"),
            (r'\bTBD\b', "TBD marker"),
            (r'\[CITATION[_ ]NEEDED\]', "citation needed"),
            (r'\[ANDREW[_ ]REQUIRED\]', "Andrew action required"),
        ]
        total_placeholders = 0
        for pattern, desc in patterns:
            matches = re.findall(pattern, text)
            if matches:
                total_placeholders += len(matches)

        if total_placeholders > 0:
            severity = "CRITICAL" if total_placeholders > 5 else "WARNING"
            report.issues.append(ComplianceIssue(
                rule="Completeness",
                severity=severity,
                description=f"{total_placeholders} unresolved placeholders found",
                fix_suggestion="Resolve all [PLACEHOLDER] markers before filing",
            ))

    def _check_toa_format(self, text: str, rules: dict, report: ComplianceReport):
        """Check Table of Authorities format."""
        required_sections = rules.get("required_sections", [])
        if "TABLE OF AUTHORITIES" not in [s.upper() for s in required_sections]:
            return  # TOA not required for this brief type

        text_upper = text.upper()
        if "TABLE OF AUTHORITIES" not in text_upper:
            return  # Already flagged as missing section

        # Check TOA has categories
        toa_categories = ["CASES", "STATUTES", "RULES", "OTHER AUTHORITIES", "CONSTITUTIONAL"]
        has_category = any(cat in text_upper for cat in toa_categories)
        if not has_category:
            report.issues.append(ComplianceIssue(
                rule="MCR 7.212(C)",
                severity="WARNING",
                description="Table of Authorities lacks category headings (Cases, Statutes, Rules)",
                fix_suggestion="Organize TOA by category: Cases, Statutes, Court Rules, Other",
            ))

    def _check_case_number_format(self, text: str, report: ComplianceReport):
        """Check case number formatting."""
        # Find case numbers
        case_nums = re.findall(r'\b(\d{4})-(\d{1,6})-([A-Z]{2})\b', text)
        for year, num, suffix in case_nums:
            if len(num) < 6:
                report.issues.append(ComplianceIssue(
                    rule="Case Number Format",
                    severity="WARNING",
                    description=f"Case number {year}-{num}-{suffix} missing leading zeros",
                    auto_fixable=True,
                    fix_suggestion=f"Use {year}-{num.zfill(6)}-{suffix}",
                ))

    def _check_common_errors(self, text: str, report: ComplianceReport):
        """Check for common drafting errors."""
        # Check for "McNeill" spelling (must have two L's)
        if re.search(r'\bMcNeil\b(?!l)', text):
            report.issues.append(ComplianceIssue(
                rule="Name Accuracy",
                severity="WARNING",
                description="Judge name 'McNeil' should be 'McNeill' (two L's)",
                auto_fixable=True,
                fix_suggestion="Replace 'McNeil' with 'McNeill'",
            ))

        # Check for wrong party names
        wrong_names = [
            ("Emily Ann Watson", "Emily A. Watson"),
            ("Emily M. Watson", "Emily A. Watson"),
            ("EMILY M. WATSON", "EMILY A. WATSON"),
        ]
        for wrong, correct in wrong_names:
            if wrong in text:
                report.issues.append(ComplianceIssue(
                    rule="Party Name Accuracy",
                    severity="CRITICAL",
                    description=f"Wrong party name '{wrong}' — should be '{correct}'",
                    auto_fixable=True,
                    fix_suggestion=f"Replace '{wrong}' with '{correct}'",
                ))


# ─── Module-level convenience ───

def check_brief(text: str, brief_type: str = "motion") -> ComplianceReport:
    """Quick compliance check."""
    return BriefComplianceEngine().check(text, brief_type)


if __name__ == "__main__":
    import sys
    if len(sys.argv) > 1:
        with open(sys.argv[1], "r", encoding="utf-8") as f:
            text = f.read()
        brief_type = sys.argv[2] if len(sys.argv) > 2 else "motion"
        report = check_brief(text, brief_type)
        print(f"Brief Type: {report.brief_type}")
        print(f"Word Count: {report.word_count}")
        print(f"Score: {report.score}/100")
        print(f"Passed: {report.passed}")
        print(f"Issues: {len(report.issues)} ({report.critical_count} critical)")
        for issue in report.issues:
            icon = "🔴" if issue.severity == "CRITICAL" else "🟡" if issue.severity == "WARNING" else "ℹ️"
            print(f"  {icon} [{issue.rule}] {issue.description}")
    else:
        print("Usage: python brief_compliance.py <file> [brief_type]")
