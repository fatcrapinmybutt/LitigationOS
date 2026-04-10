"""
Filing Engine Validator — MCR/FRCP Compliance Checking
=======================================================

Validates filing components against court rules before assembly.
Returns structured pass/fail results with authority citations.
"""

import re
import string
from datetime import date
from dataclasses import dataclass, field
from typing import Optional


@dataclass(slots=True)
class QACheck:
    """Single QA check result."""
    name: str
    passed: bool
    severity: str = "warning"   # critical | warning | info
    message: str = ""
    rule: str = ""
    auto_fixable: bool = False

    def __post_init__(self):
        match self.severity:
            case "critical" | "warning" | "info":
                pass
            case _:
                raise ValueError(
                    f"Invalid severity {self.severity!r}; "
                    f"must be 'critical', 'warning', or 'info'"
                )


@dataclass
class ValidationResult:
    """Complete validation result for a filing."""
    filing_id: str
    court: str
    checks: list = field(default_factory=list)
    passed: bool = True
    critical_failures: int = 0
    warnings: int = 0

    def add(self, check: QACheck):
        self.checks.append(check)
        if not check.passed:
            if check.severity == "critical":
                self.critical_failures += 1
                self.passed = False
            else:
                self.warnings += 1

    @property
    def summary(self) -> str:
        total = len(self.checks)
        passed = sum(1 for c in self.checks if c.passed)
        return (f"{passed}/{total} passed | "
                f"{self.critical_failures} critical | "
                f"{self.warnings} warnings")


# ─── FORMAT SPECS BY COURT ─────────────────────────────────

COURT_SPECS = {
    "mi_circuit": {
        "name": "Michigan Circuit Court",
        "font_min_pt": 12,
        "margins_inches": 1.0,
        "spacing": "double",
        "page_limit_motion": 20,
        "page_limit_brief": 20,
        "caption_rule": "MCR 2.113",
        "signature_rule": "MCR 2.114(A)",
        "cos_rule": "MCR 2.107(C)",
        "proposed_order_required": True,
        "proposed_order_rule": "MCR 2.119(A)(2)",
    },
    "mi_coa": {
        "name": "Michigan Court of Appeals",
        "font_min_pt": 12,
        "margins_inches": 1.0,
        "spacing": "double",
        "page_limit_brief": 50,
        "caption_rule": "MCR 7.212(B)",
        "toc_required": True,
        "index_of_authorities_required": True,
    },
    "mi_msc": {
        "name": "Michigan Supreme Court",
        "font_min_pt": 12,
        "margins_inches": 1.0,
        "spacing": "double",
        "page_limit_brief": 50,
        "caption_rule": "MCR 7.306",
        "toc_required": True,
        "index_of_authorities_required": True,
    },
    "wdmi_federal": {
        "name": "USDC Western District of Michigan",
        "font_min_pt": 14,  # 14pt proportional (TNR) per LCivR 10.6
        "margins_inches": 1.0,
        "spacing": "double",
        "page_limit_brief": 25,
        "caption_rule": "LCivR 10.1",
        "cos_rule": "FRCP 5(d)",
        "ecf_required": True,
    },
    "mi_district": {
        "name": "Michigan District Court",
        "font_min_pt": 12,
        "margins_inches": 1.0,
        "spacing": "double",
        "caption_rule": "MCR 2.113",
        "cos_rule": "MCR 2.107(C)",
    },
}


class FilingValidator:
    """Validates filing documents against court rules."""

    def __init__(self, court_type: str = "mi_circuit",
                 child_name_patterns: list[str] | None = None):
        if court_type not in COURT_SPECS:
            raise ValueError(f"Unknown court type: {court_type}. "
                           f"Options: {list(COURT_SPECS.keys())}")
        self.court_type = court_type
        self.specs = COURT_SPECS[court_type]
        self.child_name_patterns: list[str] = child_name_patterns or []

    def validate_filing(self, filing_id: str,
                        document_text: str = "",
                        has_cos: bool = False,
                        has_proposed_order: bool = False,
                        has_caption: bool = False,
                        has_signature: bool = False,
                        has_exhibits: bool = False,
                        has_toc: bool = False,
                        has_authority_index: bool = False,
                        page_count: int = 0,
                        filing_type: str = "motion",
                        case_number: str = "",
                        parties: dict = None,
                        pro_se: bool = True) -> ValidationResult:
        """Run all validation checks on a filing."""

        result = ValidationResult(
            filing_id=filing_id,
            court=self.specs["name"]
        )

        # 1. Certificate of Service
        result.add(self._check_cos(has_cos))

        # 2. Caption
        result.add(self._check_caption(has_caption, document_text, case_number))

        # 3. Signature block
        result.add(self._check_signature(has_signature, pro_se, document_text))

        # 4. Proposed order (motions only)
        if filing_type in ("motion", "emergency_motion"):
            result.add(self._check_proposed_order(has_proposed_order))

        # 5. Page limits
        result.add(self._check_page_limit(page_count, filing_type))

        # 6. Child name protection
        result.add(self._check_child_name(document_text))

        # 7. AI artifact check
        result.add(self._check_ai_artifacts(document_text))

        # 8. Pro se language check
        if pro_se:
            result.add(self._check_pro_se_language(document_text))

        # 9. Table of contents (appellate only)
        if self.specs.get("toc_required"):
            result.add(self._check_toc(has_toc))

        # 10. Index of authorities (appellate only)
        if self.specs.get("index_of_authorities_required"):
            result.add(self._check_authority_index(has_authority_index))

        # 11. Citation validation
        result.add(self._check_citations(document_text))

        # 12. Case number present
        result.add(self._check_case_number(document_text, case_number))

        # 13. Exhibit integrity
        result.add(self._check_exhibit_integrity(document_text))

        return result

    def _check_cos(self, has_cos: bool) -> QACheck:
        rule = self.specs.get("cos_rule", "MCR 2.107(C)")
        return QACheck(
            name="Certificate of Service",
            passed=has_cos,
            severity="critical",
            message="COS present" if has_cos else "MISSING Certificate of Service",
            rule=rule
        )

    def _check_caption(self, has_caption: bool, text: str,
                       case_number: str) -> QACheck:
        rule = self.specs.get("caption_rule", "MCR 2.113")
        if has_caption:
            # Verify case number in caption
            if case_number and case_number not in text[:2000]:
                return QACheck(
                    name="Caption — Case Number",
                    passed=False,
                    severity="critical",
                    message=f"Case number {case_number} not found in caption area",
                    rule=rule,
                    auto_fixable=True
                )
            return QACheck(name="Caption", passed=True,
                         message="Caption present", rule=rule)
        return QACheck(name="Caption", passed=False, severity="critical",
                      message="MISSING court caption", rule=rule)

    def _check_signature(self, has_signature: bool, pro_se: bool,
                        text: str) -> QACheck:
        rule = self.specs.get("signature_rule", "MCR 2.114(A)")
        if not has_signature:
            return QACheck(name="Signature Block", passed=False,
                         severity="critical",
                         message="MISSING signature block", rule=rule)
        # Check for required elements: name, address, phone
        sig_area = text[-3000:] if len(text) > 3000 else text
        has_phone = bool(re.search(r'\(\d{3}\)\s*\d{3}[-.]?\d{4}', sig_area))
        has_email = bool(re.search(r'[\w.+-]+@[\w.-]+\.\w+', sig_area))
        if not (has_phone and has_email):
            return QACheck(name="Signature Block — Contact Info",
                         passed=False, severity="warning",
                         message="Signature block missing phone or email",
                         rule=rule, auto_fixable=True)
        return QACheck(name="Signature Block", passed=True,
                      message="Signature block complete", rule=rule)

    def _check_proposed_order(self, has_proposed_order: bool) -> QACheck:
        rule = self.specs.get("proposed_order_rule", "MCR 2.119(A)(2)")
        return QACheck(
            name="Proposed Order",
            passed=has_proposed_order,
            severity="critical",
            message="Proposed order attached" if has_proposed_order
                    else "MISSING proposed order — required with every motion",
            rule=rule
        )

    def _check_page_limit(self, page_count: int,
                          filing_type: str) -> QACheck:
        if page_count == 0:
            return QACheck(name="Page Limit", passed=True,
                         severity="info",
                         message="Page count not provided — cannot verify")

        limit_key = f"page_limit_{filing_type}"
        if limit_key not in self.specs:
            limit_key = "page_limit_brief"
        limit = self.specs.get(limit_key, 999)

        return QACheck(
            name="Page Limit",
            passed=page_count <= limit,
            severity="critical" if page_count > limit else "info",
            message=f"{page_count}/{limit} pages"
                    + (" — EXCEEDS LIMIT" if page_count > limit else ""),
            rule=f"Page limit: {limit}"
        )

    def _check_child_name(self, text: str) -> QACheck:
        """Check that no child's full name appears — CRITICAL privacy check.

        Scans for:
        1. Case-specific patterns supplied via ``child_name_patterns``.
        2. Generic "child" keyword followed by a full name.
        3. Full name immediately after a DOB / "born" reference.

        Returns ``passed=False`` with severity ``critical`` when any
        pattern matches.  MCR 8.119(H) requires minors be identified
        by initials only in court filings.
        """
        if not text:
            return QACheck(
                name="Child Name Privacy",
                passed=True,
                severity="info",
                message="No document text to check",
                rule="MCR 8.119(H)",
            )

        violations: list[str] = []

        # ── 1. Case-specific patterns ────────────────────────
        for pat in self.child_name_patterns:
            matches = re.findall(pat, text, re.IGNORECASE)
            if matches:
                # Flatten tuples from groups if present
                for m in matches:
                    hit = m if isinstance(m, str) else " ".join(m).strip()
                    violations.append(f"case-specific: {hit!r}")

        # Reusable name fragment: "First M. Last" or "First Middle Last"
        # Case-SENSITIVE — requires Title Case so we don't match normal words
        _NAME = r'[A-Z][a-z]{1,20}\s+(?:[A-Z]\.?\s+)?[A-Z][a-z]{1,20}'

        # ── 2. Generic: "(minor |the )?child" + full name ────
        # Keywords are case-insensitive ((?i:...)), name is case-sensitive
        child_kw_pat = (
            r'(?i:(?:(?:the|minor|a)\s+)?'
            r'child(?:\s+named|\s+known\s+as|,)?)\s+'
            rf'({_NAME})'
        )
        for m in re.finditer(child_kw_pat, text):
            violations.append(f"child-keyword: {m.group(1)!r}")

        # ── 3. DOB / "born" + full name ──────────────────────
        born_pat = (
            r'(?i:born\s+(?:\w+\s+\d{1,2},?\s+\d{4}'
            r'|\d{1,2}[/-]\d{1,2}[/-]\d{2,4}))'
            r'\s*[,)}\s]*\s*'
            rf'({_NAME})'
        )
        for m in re.finditer(born_pat, text):
            violations.append(f"born-pattern: {m.group(1)!r}")

        if violations:
            # Cap the message to avoid excessive length
            detail = "; ".join(violations[:10])
            extra = f" (+{len(violations) - 10} more)" if len(violations) > 10 else ""
            return QACheck(
                name="Child Name Privacy",
                passed=False,
                severity="critical",
                message=f"MCR 8.119(H) VIOLATION — child name(s) detected: {detail}{extra}",
                rule="MCR 8.119(H)",
            )

        return QACheck(
            name="Child Name Privacy",
            passed=True,
            severity="info",
            message="No child name violations detected",
            rule="MCR 8.119(H)",
        )

    def _check_ai_artifacts(self, text: str) -> QACheck:
        """Check for AI/database references that must be stripped."""
        patterns = [
            r'LitigationOS', r'OMEGA', r'SINGULARITY', r'litigation_context',
            r'shadyoaks\.db', r'EGCP\s+score', r'readiness\s+score',
            r'evidence_quotes', r'impeachment_matrix', r'NEXUS',
            r'copilot', r'GPT[-\s]?\d', r'Claude', r'AI\s+analysis',
            r'database\s+query', r'FTS5',
        ]
        found = []
        for pat in patterns:
            if re.search(pat, text, re.IGNORECASE):
                found.append(pat.replace(r'\s+', ' ').replace(r'\.', '.'))

        return QACheck(
            name="AI Artifact Check",
            passed=len(found) == 0,
            severity="critical" if found else "info",
            message=("FOUND AI artifacts: " + ", ".join(found[:5]))
                    if found else "Clean — no AI/database references",
            auto_fixable=True
        )

    def _check_pro_se_language(self, text: str) -> QACheck:
        """Check for attorney-only language in pro se filings."""
        bad_phrases = [
            "undersigned counsel",
            "attorney for plaintiff",
            "attorney for defendant",
            "counsel for",
            "this firm",
            "our client",
        ]
        found = [p for p in bad_phrases if p.lower() in text.lower()]
        return QACheck(
            name="Pro Se Language",
            passed=len(found) == 0,
            severity="warning",
            message=("Found attorney language: " + ", ".join(found))
                    if found else "Pro se language correct",
            auto_fixable=True
        )

    def _check_toc(self, has_toc: bool) -> QACheck:
        return QACheck(
            name="Table of Contents",
            passed=has_toc,
            severity="critical",
            message="TOC present" if has_toc else "MISSING Table of Contents",
            rule="MCR 7.212(B)"
        )

    def _check_authority_index(self, has_authority_index: bool) -> QACheck:
        return QACheck(
            name="Index of Authorities",
            passed=has_authority_index,
            severity="critical",
            message="Authority index present" if has_authority_index
                    else "MISSING Index of Authorities",
            rule="MCR 7.212(B)"
        )

    def _check_citations(self, text: str) -> QACheck:
        """Check that legal claims have authority citations."""
        # Look for claim-like statements without nearby citations
        claim_patterns = [
            r'(?:violat|breach|deprive|deny|defraud|conspir)',
        ]
        citation_patterns = [
            r'MCR\s+\d+\.\d+',
            r'MCL\s+\d+\.\d+',
            r'USC?\s+§?\s*\d+',
            r'\d+\s+Mich\s+(?:App\s+)?\d+',
            r'FRCP\s+\d+',
            r'MRE\s+\d+',
        ]
        has_claims = any(re.search(p, text, re.IGNORECASE) for p in claim_patterns)
        has_citations = any(re.search(p, text) for p in citation_patterns)

        if has_claims and not has_citations:
            return QACheck(
                name="Citation Support",
                passed=False,
                severity="warning",
                message="Legal claims found but no rule/statute citations detected",
                rule="Every claim must cite authority"
            )
        return QACheck(
            name="Citation Support",
            passed=True,
            message="Citations present" if has_citations else "No claims detected"
        )

    def _check_case_number(self, text: str, case_number: str) -> QACheck:
        if not case_number:
            return QACheck(name="Case Number", passed=True,
                         severity="info",
                         message="No case number provided for verification")
        present = case_number in text
        return QACheck(
            name="Case Number",
            passed=present,
            severity="critical" if not present else "info",
            message=f"Case number {case_number} "
                    + ("found" if present else "NOT FOUND in document"),
            auto_fixable=True
        )

    def _check_exhibit_integrity(self, text: str) -> QACheck:
        """Check exhibit labeling continuity, Bates gaps, and cross-references.

        Validates:
        1. Sequential exhibit labels (A-Z or 1-99) with no gaps.
        2. Bates number continuity (PREFIX-NNNNNN patterns).
        3. Every in-body exhibit reference resolves to a declared exhibit.

        No exhibits mentioned → pass (not all filings have exhibits).
        """
        if not text:
            return QACheck(
                name="Exhibit Integrity",
                passed=True,
                severity="info",
                message="No document text to check",
            )

        issues: list[str] = []

        # ── 1. Collect all exhibit labels mentioned anywhere ──────────
        # Matches "Exhibit A", "Exhibit 12", "EXHIBIT B-1", etc.
        exhibit_pat = re.compile(
            r'\bExhibit\s+([A-Z](?:-?\d{1,2})?|\d{1,2})\b', re.IGNORECASE
        )
        all_matches = exhibit_pat.findall(text)
        if not all_matches:
            return QACheck(
                name="Exhibit Integrity",
                passed=True,
                severity="info",
                message="No exhibits referenced — check not applicable",
            )

        labels = sorted({m.upper() for m in all_matches})
        letter_labels = sorted(
            [lb for lb in labels if len(lb) == 1 and lb in string.ascii_uppercase]
        )
        number_labels = sorted(
            [lb for lb in labels if lb.isdigit()], key=int
        )

        # ── 2. Sequential gap detection ──────────────────────────────
        if letter_labels:
            first = string.ascii_uppercase.index(letter_labels[0])
            last = string.ascii_uppercase.index(letter_labels[-1])
            expected = set(string.ascii_uppercase[first:last + 1])
            missing = expected - set(letter_labels)
            if missing:
                issues.append(
                    f"Letter exhibit gap: missing {', '.join(sorted(missing))}"
                )

        if number_labels:
            nums = [int(n) for n in number_labels]
            expected_nums = set(range(nums[0], nums[-1] + 1))
            missing_nums = expected_nums - set(nums)
            if missing_nums:
                issues.append(
                    f"Numeric exhibit gap: missing "
                    f"{', '.join(str(n) for n in sorted(missing_nums))}"
                )

        # ── 3. Bates number continuity ────────────────────────────────
        # Matches PREFIX-000001 style stamps (4-8 digit zero-padded)
        bates_pat = re.compile(r'\b([A-Z]{2,20})-(\d{4,8})\b')
        bates_hits = bates_pat.findall(text)
        if bates_hits:
            by_prefix: dict[str, list[int]] = {}
            for prefix, num_str in bates_hits:
                by_prefix.setdefault(prefix, []).append(int(num_str))
            for prefix, nums_list in by_prefix.items():
                nums_sorted = sorted(set(nums_list))
                if len(nums_sorted) >= 2:
                    expected_range = set(
                        range(nums_sorted[0], nums_sorted[-1] + 1)
                    )
                    gaps = expected_range - set(nums_sorted)
                    if gaps:
                        gap_sample = sorted(gaps)[:5]
                        trail = " ..." if len(gaps) > 5 else ""
                        issues.append(
                            f"Bates gap in {prefix}-: missing "
                            f"{', '.join(f'{prefix}-{g:06d}' for g in gap_sample)}"
                            f"{trail}"
                        )

        # ── 4. Cross-reference resolution ─────────────────────────────
        # Body references: "See Exhibit X", "(Exhibit X)", "per Exhibit X"
        body_ref_pat = re.compile(
            r'(?:(?:see|per|in|at|cf\.?|attached)\s+)?'
            r'(?:\(?\s*)'
            r'Exhibit\s+([A-Z](?:-?\d{1,2})?|\d{1,2})'
            r'(?:\s*\)?)',
            re.IGNORECASE,
        )
        body_refs = {m.upper() for m in body_ref_pat.findall(text)}

        # Declared exhibits: heading-like lines that define an exhibit
        # e.g. "EXHIBIT A", "Exhibit 1 — Title", "EXHIBIT B:"
        declared_pat = re.compile(
            r'^\s*EXHIBIT\s+([A-Z](?:-?\d{1,2})?|\d{1,2})\b',
            re.IGNORECASE | re.MULTILINE,
        )
        declared = {m.upper() for m in declared_pat.findall(text)}

        # If there are body references but zero declared headings, warn
        if body_refs and not declared:
            issues.append(
                f"Body references {', '.join(sorted(body_refs))} found but "
                f"no exhibit headings/list detected in document"
            )
        elif declared:
            unresolved = body_refs - declared
            if unresolved:
                issues.append(
                    f"Unresolved exhibit references: "
                    f"{', '.join(sorted(unresolved))} — "
                    f"not found in exhibit headings"
                )

        # ── Result ────────────────────────────────────────────────────
        if issues:
            detail = "; ".join(issues[:8])
            extra = f" (+{len(issues) - 8} more)" if len(issues) > 8 else ""
            return QACheck(
                name="Exhibit Integrity",
                passed=False,
                severity="warning",
                message=f"Exhibit issues: {detail}{extra}",
            )

        return QACheck(
            name="Exhibit Integrity",
            passed=True,
            severity="info",
            message=f"Exhibits OK — {len(labels)} label(s) verified, "
                    f"no gaps or unresolved references",
        )
