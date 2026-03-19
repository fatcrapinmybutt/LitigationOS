# -*- coding: utf-8 -*-
"""Wave-10 Tests — ComplianceAuditor
=====================================
Comprehensive pytest suite for compliance_auditor.py.

~90 tests covering enums (ComplianceCategory, ComplianceLevel, FilingType),
dataclasses (ComplianceIssue, AuditResult), FormatAuditor, ContentAuditor,
CitationAuditor, ServiceAuditor, and the ComplianceAuditor orchestrator.

• Zero network / zero real DB — all DB interactions use tmp_path SQLite
• Independent tests, no ordering dependencies
• Real Michigan party names and MCR citations throughout
"""
from __future__ import annotations

import pathlib
import sys
from typing import List

import pytest

# ---------------------------------------------------------------------------
# Path bootstrap — let us import from the parent legal_ai package
# ---------------------------------------------------------------------------
_THIS_DIR = pathlib.Path(__file__).resolve().parent
_LEGAL_AI_DIR = _THIS_DIR.parent
if str(_LEGAL_AI_DIR) not in sys.path:
    sys.path.insert(0, str(_LEGAL_AI_DIR))

from compliance_auditor import (
    ComplianceCategory,
    ComplianceLevel,
    FilingType,
    ComplianceIssue,
    AuditResult,
    FormatAuditor,
    ContentAuditor,
    CitationAuditor,
    ServiceAuditor,
    ComplianceAuditor,
    _PLAINTIFF,
    _DEFENDANT,
    _CHILD_INITIALS,
    _JUDGE,
    _COURT,
    LANE_CASES,
)


# ---------------------------------------------------------------------------
# Reusable text fixtures
# ---------------------------------------------------------------------------

_MINIMAL_CAPTION = (
    "STATE OF MICHIGAN\n"
    "IN THE 14TH CIRCUIT COURT FOR THE COUNTY OF MUSKEGON\n"
    "Case No. 2024-001507-DC\n"
)

_COMPLIANT_MOTION = (
    "STATE OF MICHIGAN\n"
    "IN THE 14TH CIRCUIT COURT FOR THE COUNTY OF MUSKEGON\n"
    "Case No. 2024-001507-DC\n\n"
    "MOTION TO COMPEL DISCOVERY\n\n"
    "Plaintiff Andrew James Pigors respectfully requests that this Honorable "
    "Court enter an order compelling Defendant Emily A. Watson to respond to "
    "Plaintiff's First Set of Interrogatories. MCR 2.313 authorizes sanctions "
    "for failure to provide discovery. MCL 722.27 governs custody matters.\n\n"
    "WHEREFORE, Plaintiff respectfully asks this Court to grant the relief "
    "sought herein.\n\n"
    "Respectfully submitted,\n"
    "/s/ Andrew James Pigors\n"
    "Andrew James Pigors, Pro Se\n"
    "Date: 01/15/2025\n\n"
    "Page 1\n\n"
    "PROOF OF SERVICE\n"
    "I hereby certify that on 01/15/2025, I served the foregoing document "
    "upon Emily A. Watson via first-class mail at her last known address.\n"
    "/s/ Andrew James Pigors\n"
)

_BRIEF_TEXT = (
    "STATE OF MICHIGAN\n"
    "IN THE COURT OF APPEALS\n"
    "Case No. 366810\n\n"
    "TABLE OF CONTENTS\n"
    "Table of Authorities ............................ ii\n"
    "Jurisdiction Statement .......................... 1\n"
    "Question Presented .............................. 2\n\n"
    "TABLE OF AUTHORITIES\n"
    "MCR 7.212 ...................................... 5\n\n"
    "JURISDICTION\n"
    "This Court has jurisdiction under MCR 7.203.\n\n"
    "QUESTION PRESENTED\n"
    "Whether the trial court erred.\n\n"
    "Respectfully submitted,\n"
    "/s/ Andrew James Pigors\n"
    "Date: 02/10/2025\n"
    "Page 1\n\n"
    "PROOF OF SERVICE\n"
    "I hereby certify that I served Emily A. Watson via first-class mail "
    "on 02/10/2025.\n"
)


# ===================================================================
# TestComplianceCategory
# ===================================================================
class TestComplianceCategory:
    """Tests for the ComplianceCategory enum."""

    def test_all_values_exist(self):
        expected = {
            "format", "content", "citation", "service",
            "signature", "verification", "timeliness", "accessibility",
        }
        actual = {c.value for c in ComplianceCategory}
        assert actual == expected

    def test_string_membership(self):
        assert isinstance(ComplianceCategory.FORMAT, str)
        assert ComplianceCategory.FORMAT == "format"

    def test_count_is_eight(self):
        assert len(ComplianceCategory) == 8


# ===================================================================
# TestComplianceLevel
# ===================================================================
class TestComplianceLevel:
    """Tests for the ComplianceLevel enum with severity_rank."""

    def test_all_values_exist(self):
        expected = {"pass", "warning", "fail", "critical"}
        actual = {c.value for c in ComplianceLevel}
        assert actual == expected

    def test_severity_rank_pass(self):
        assert ComplianceLevel.PASS.severity_rank == 0

    def test_severity_rank_warning(self):
        assert ComplianceLevel.WARNING.severity_rank == 1

    def test_severity_rank_fail(self):
        assert ComplianceLevel.FAIL.severity_rank == 2

    def test_severity_rank_critical(self):
        assert ComplianceLevel.CRITICAL.severity_rank == 3

    def test_ordering_by_severity(self):
        levels = sorted(ComplianceLevel, key=lambda x: x.severity_rank)
        assert [l.value for l in levels] == ["pass", "warning", "fail", "critical"]


# ===================================================================
# TestFilingType
# ===================================================================
class TestFilingType:
    """Tests for the FilingType enum."""

    def test_all_values_exist(self):
        expected = {
            "motion", "response", "reply", "brief", "complaint",
            "answer", "affidavit", "exhibit", "proposed_order",
            "proof_of_service", "notice", "stipulation",
        }
        actual = {f.value for f in FilingType}
        assert actual == expected

    def test_count_is_twelve(self):
        assert len(FilingType) == 12

    def test_string_values(self):
        assert isinstance(FilingType.MOTION, str)
        assert FilingType.MOTION == "motion"


# ===================================================================
# TestComplianceIssue
# ===================================================================
class TestComplianceIssue:
    """Tests for the ComplianceIssue dataclass."""

    def test_defaults(self):
        issue = ComplianceIssue()
        assert issue.category == ComplianceCategory.FORMAT
        assert issue.level == ComplianceLevel.WARNING
        assert issue.rule_reference == ""
        assert issue.description == ""
        assert issue.issue_id  # non-empty UUID hex

    def test_to_dict_has_category_value(self):
        issue = ComplianceIssue(category=ComplianceCategory.CITATION)
        d = issue.to_dict()
        assert d["category"] == "citation"

    def test_to_dict_has_level_value(self):
        issue = ComplianceIssue(level=ComplianceLevel.CRITICAL)
        d = issue.to_dict()
        assert d["level"] == "critical"

    def test_auto_fixable_default_false(self):
        issue = ComplianceIssue()
        assert issue.auto_fixable is False

    def test_custom_fields(self):
        issue = ComplianceIssue(
            category=ComplianceCategory.SERVICE,
            level=ComplianceLevel.FAIL,
            rule_reference="MCR 2.107(C)(3)",
            description="Service defect",
            location="page 5",
            suggestion="Fix it",
            auto_fixable=True,
        )
        assert issue.rule_reference == "MCR 2.107(C)(3)"
        assert issue.location == "page 5"
        assert issue.auto_fixable is True


# ===================================================================
# TestAuditResult
# ===================================================================
class TestAuditResult:
    """Tests for the AuditResult dataclass and its computed properties."""

    @staticmethod
    def _make_issues(*levels: ComplianceLevel) -> List[ComplianceIssue]:
        return [ComplianceIssue(level=lv) for lv in levels]

    def test_defaults(self):
        r = AuditResult()
        assert r.filing_type == ""
        assert r.issues == []
        assert r.overall_level == ComplianceLevel.PASS
        assert r.audit_id  # non-empty

    def test_pass_count(self):
        issues = self._make_issues(
            ComplianceLevel.PASS, ComplianceLevel.PASS, ComplianceLevel.WARNING,
        )
        r = AuditResult(issues=issues)
        assert r.pass_count == 2

    def test_warning_count(self):
        issues = self._make_issues(
            ComplianceLevel.WARNING, ComplianceLevel.WARNING, ComplianceLevel.PASS,
        )
        r = AuditResult(issues=issues)
        assert r.warning_count == 2

    def test_fail_count(self):
        issues = self._make_issues(
            ComplianceLevel.FAIL, ComplianceLevel.PASS,
        )
        r = AuditResult(issues=issues)
        assert r.fail_count == 1

    def test_critical_count(self):
        issues = self._make_issues(
            ComplianceLevel.CRITICAL, ComplianceLevel.CRITICAL, ComplianceLevel.PASS,
        )
        r = AuditResult(issues=issues)
        assert r.critical_count == 2

    def test_is_filing_ready_true(self):
        issues = self._make_issues(
            ComplianceLevel.PASS, ComplianceLevel.WARNING, ComplianceLevel.PASS,
        )
        r = AuditResult(issues=issues)
        assert r.is_filing_ready is True

    def test_is_filing_ready_false_has_fail(self):
        issues = self._make_issues(ComplianceLevel.PASS, ComplianceLevel.FAIL)
        r = AuditResult(issues=issues)
        assert r.is_filing_ready is False

    def test_is_filing_ready_false_has_critical(self):
        issues = self._make_issues(ComplianceLevel.PASS, ComplianceLevel.CRITICAL)
        r = AuditResult(issues=issues)
        assert r.is_filing_ready is False

    def test_to_dict_has_all_counts(self):
        issues = self._make_issues(
            ComplianceLevel.PASS, ComplianceLevel.WARNING,
            ComplianceLevel.FAIL, ComplianceLevel.CRITICAL,
        )
        r = AuditResult(issues=issues, filing_type="motion")
        d = r.to_dict()
        assert d["pass_count"] == 1
        assert d["warning_count"] == 1
        assert d["fail_count"] == 1
        assert d["critical_count"] == 1
        assert d["is_filing_ready"] is False
        assert d["filing_type"] == "motion"
        assert "overall_level" in d
        assert "timestamp" in d


# ===================================================================
# TestFormatAuditor
# ===================================================================
class TestFormatAuditor:
    """Tests for FormatAuditor."""

    def setup_method(self):
        self.auditor = FormatAuditor()

    def test_caption_found(self):
        issues = self.auditor.audit("STATE OF MICHIGAN\nCase No. 2024-001507-DC\nPage 1")
        pass_issues = [i for i in issues if i.level == ComplianceLevel.PASS
                       and "Caption" in i.description]
        assert len(pass_issues) >= 1

    def test_caption_missing(self):
        issues = self.auditor.audit("Some random text without any caption.\nPage 1")
        fail_issues = [i for i in issues if i.level == ComplianceLevel.FAIL
                       and "Caption" in i.description]
        assert len(fail_issues) >= 1

    def test_case_number_found(self):
        issues = self.auditor.audit("Case No. 2024-001507-DC\nPage 1")
        pass_issues = [i for i in issues if i.level == ComplianceLevel.PASS
                       and "Case number" in i.description]
        assert len(pass_issues) >= 1

    def test_case_number_missing(self):
        issues = self.auditor.audit("STATE OF MICHIGAN\nPage 1")
        fail_issues = [i for i in issues if i.level == ComplianceLevel.FAIL
                       and "Case number" in i.description]
        assert len(fail_issues) >= 1

    def test_page_numbers_found(self):
        issues = self.auditor.audit("STATE OF MICHIGAN\nCase No. 2024-001507-DC\nPage 1")
        pass_issues = [i for i in issues if i.level == ComplianceLevel.PASS
                       and "Page" in i.description]
        assert len(pass_issues) >= 1

    def test_page_numbers_missing(self):
        text = "STATE OF MICHIGAN\nCase No. 2024-001507-DC\nSome text here."
        issues = self.auditor.audit(text)
        warn_issues = [i for i in issues if i.level == ComplianceLevel.WARNING
                       and "page" in i.description.lower()]
        assert len(warn_issues) >= 1

    def test_triple_spacing_detected(self):
        text = "STATE OF MICHIGAN\n\n\n\nCase No. 2024-001507-DC\nPage 1"
        issues = self.auditor.audit(text)
        warn_issues = [i for i in issues if i.level == ComplianceLevel.WARNING
                       and "blank lines" in i.description.lower()]
        assert len(warn_issues) >= 1

    def test_brief_with_table_of_contents(self):
        text = (
            "STATE OF MICHIGAN\nCase No. 2024-001507-DC\nPage 1\n"
            "TABLE OF CONTENTS\nTable of Authorities\n"
            "Jurisdiction\nQuestion presented"
        )
        issues = self.auditor.audit(text, filing_type="brief")
        toc_pass = [i for i in issues if i.level == ComplianceLevel.PASS
                    and "7.212(D)(1)" in i.rule_reference]
        assert len(toc_pass) >= 1

    def test_brief_missing_table_of_contents(self):
        text = (
            "STATE OF MICHIGAN\nCase No. 2024-001507-DC\nPage 1\n"
            "Table of Authorities\nJurisdiction\nQuestion presented"
        )
        issues = self.auditor.audit(text, filing_type="brief")
        toc_fail = [i for i in issues if i.level == ComplianceLevel.FAIL
                    and "7.212(D)(1)" in i.rule_reference]
        assert len(toc_fail) >= 1

    def test_brief_with_table_of_authorities(self):
        text = (
            "STATE OF MICHIGAN\nCase No. 2024-001507-DC\nPage 1\n"
            "TABLE OF CONTENTS\nTable of Authorities\n"
            "Jurisdiction\nQuestion presented"
        )
        issues = self.auditor.audit(text, filing_type="brief")
        toa_pass = [i for i in issues if i.level == ComplianceLevel.PASS
                    and "7.212(D)(2)" in i.rule_reference]
        assert len(toa_pass) >= 1

    def test_brief_missing_jurisdiction(self):
        text = (
            "STATE OF MICHIGAN\nCase No. 2024-001507-DC\nPage 1\n"
            "Table of Contents\nTable of Authorities\nQuestion presented"
        )
        issues = self.auditor.audit(text, filing_type="brief")
        jur_fail = [i for i in issues if i.level == ComplianceLevel.FAIL
                    and "7.212(D)(3)" in i.rule_reference]
        assert len(jur_fail) >= 1

    def test_get_stats_has_mcr_2_113_checks(self):
        stats = self.auditor.get_stats()
        assert "mcr_2_113_checks" in stats
        assert stats["mcr_2_113_checks"] == 5


# ===================================================================
# TestContentAuditor
# ===================================================================
class TestContentAuditor:
    """Tests for ContentAuditor."""

    def setup_method(self):
        self.auditor = ContentAuditor()

    def test_no_ssn_pass(self):
        issues = self.auditor.audit("Clean filing text. /s/ Andrew\nDate: 01/01/2025\nProof of service")
        ssn_pass = [i for i in issues if i.level == ComplianceLevel.PASS
                    and "SSN" in i.description]
        assert len(ssn_pass) >= 1

    def test_ssn_detected_critical(self):
        text = "Defendant SSN: 123-45-6789\n/s/ Andrew\nDate: 01/01/2025"
        issues = self.auditor.audit(text)
        ssn_crit = [i for i in issues if i.level == ComplianceLevel.CRITICAL
                    and "Social Security" in i.description]
        assert len(ssn_crit) >= 1

    def test_dob_detected_warning(self):
        text = "Date of birth: 01/15/1990\n/s/ Andrew\nDate: 01/01/2025"
        issues = self.auditor.audit(text)
        dob_warn = [i for i in issues if i.level == ComplianceLevel.WARNING
                    and "birth" in i.description.lower()]
        assert len(dob_warn) >= 1

    def test_child_full_name_exposed_critical(self):
        text = "The child's full name appears in this filing.\n/s/ Andrew\nDate: 01/01/2025"
        issues = self.auditor.audit(text)
        child_crit = [i for i in issues if i.level == ComplianceLevel.CRITICAL
                      and "Minor" in i.description or "minor" in i.description.lower()
                      or "child" in i.description.lower()]
        assert len(child_crit) >= 1

    def test_child_name_protected_pass(self):
        text = f"The child ({_CHILD_INITIALS}) is well.\n/s/ Andrew\nDate: 01/01/2025"
        issues = self.auditor.audit(text)
        child_pass = [i for i in issues if i.level == ComplianceLevel.PASS
                      and "Child name" in i.description]
        assert len(child_pass) >= 1

    def test_signature_found(self):
        text = "Some text.\n/s/ Andrew James Pigors\nDate: 01/01/2025"
        issues = self.auditor.audit(text)
        sig_pass = [i for i in issues if i.level == ComplianceLevel.PASS
                    and "Signature" in i.description or "ignature" in i.description]
        assert len(sig_pass) >= 1

    def test_signature_missing_fail(self):
        text = "Filing text without any signature.\nDate: 01/01/2025"
        issues = self.auditor.audit(text)
        sig_fail = [i for i in issues if i.level == ComplianceLevel.FAIL
                    and "Signature" in i.description or "ignature" in i.description]
        assert len(sig_fail) >= 1

    def test_proof_of_service_found(self):
        text = (
            "/s/ Andrew\nDate: 01/01/2025\n"
            "PROOF OF SERVICE\nI hereby certify service was made."
        )
        issues = self.auditor.audit(text, filing_type="motion")
        svc_pass = [i for i in issues if i.category == ComplianceCategory.SERVICE
                    and i.level == ComplianceLevel.PASS]
        assert len(svc_pass) >= 1

    def test_proof_of_service_missing_on_motion(self):
        text = "/s/ Andrew\nDate: 01/01/2025\nNo service info."
        issues = self.auditor.audit(text, filing_type="motion")
        svc_fail = [i for i in issues if i.category == ComplianceCategory.SERVICE
                    and i.level == ComplianceLevel.FAIL]
        assert len(svc_fail) >= 1

    def test_proof_of_service_exempt_for_exhibit(self):
        text = "Exhibit A: Photograph of damage."
        issues = self.auditor.audit(text, filing_type="exhibit")
        svc_issues = [i for i in issues if i.category == ComplianceCategory.SERVICE]
        assert len(svc_issues) == 0

    def test_relief_request_found(self):
        text = (
            "WHEREFORE, Plaintiff requests relief.\n"
            "/s/ Andrew\nDate: 01/01/2025\nProof of service\nI certify"
        )
        issues = self.auditor.audit(text, filing_type="motion")
        relief_pass = [i for i in issues if i.level == ComplianceLevel.PASS
                       and "Relief" in i.description or "relief" in i.description.lower()]
        assert len(relief_pass) >= 1

    def test_relief_request_missing_on_motion(self):
        text = "Some motion text.\n/s/ Andrew\nDate: 01/01/2025\nProof of service\nI certify"
        issues = self.auditor.audit(text, filing_type="motion")
        relief_warn = [i for i in issues if i.level == ComplianceLevel.WARNING
                       and "relief" in i.description.lower()]
        assert len(relief_warn) >= 1

    def test_date_found_pass(self):
        text = "/s/ Andrew\nDate: 01/15/2025\nProof of service\nI certify"
        issues = self.auditor.audit(text)
        date_pass = [i for i in issues if i.level == ComplianceLevel.PASS
                     and "date" in i.description.lower() and "birth" not in i.description.lower()]
        assert len(date_pass) >= 1

    def test_get_stats(self):
        stats = self.auditor.get_stats()
        assert stats["component"] == "ContentAuditor"
        assert stats["privacy_checks"] == 3


# ===================================================================
# TestCitationAuditor
# ===================================================================
class TestCitationAuditor:
    """Tests for CitationAuditor."""

    def setup_method(self):
        self.auditor = CitationAuditor()

    def test_no_citations_warning(self):
        issues = self.auditor.audit("This filing has no legal citations at all.")
        warn = [i for i in issues if i.level == ComplianceLevel.WARNING
                and "No legal citations" in i.description]
        assert len(warn) >= 1

    def test_mcr_citations_found_pass(self):
        text = "Per MCR 2.119, the Court should grant this motion."
        issues = self.auditor.audit(text)
        pass_issues = [i for i in issues if i.level == ComplianceLevel.PASS
                       and "citation" in i.description.lower()]
        assert len(pass_issues) >= 1

    def test_mcr_citation_counted(self):
        text = "MCR 2.119 and MCR 2.113 both apply."
        issues = self.auditor.audit(text)
        pass_issues = [i for i in issues if i.level == ComplianceLevel.PASS
                       and "2 MCR" in i.description]
        assert len(pass_issues) >= 1

    def test_mcl_citation_counted(self):
        text = "MCL 722.23 governs best-interest factors. MCR 2.119 applies."
        issues = self.auditor.audit(text)
        pass_issues = [i for i in issues if i.level == ComplianceLevel.PASS
                       and "1 MCL" in i.description]
        assert len(pass_issues) >= 1

    def test_mre_citation_counted(self):
        text = "MRE 801 defines hearsay. MCR 2.119 also applies."
        issues = self.auditor.audit(text)
        pass_issues = [i for i in issues if i.level == ComplianceLevel.PASS
                       and "1 MRE" in i.description]
        assert len(pass_issues) >= 1

    def test_case_law_citation_counted(self):
        text = "Smith v Jones, 123 Mich App 456 controls. MCR 2.119 applies."
        issues = self.auditor.audit(text)
        pass_issues = [i for i in issues if i.level == ComplianceLevel.PASS
                       and "1 case" in i.description]
        assert len(pass_issues) >= 1

    def test_known_bad_citation_mcr_2_113_z(self):
        text = "Under MCR 2.113(Z), the court must act. MCR 2.119 applies."
        issues = self.auditor.audit(text)
        fail_issues = [i for i in issues if i.level == ComplianceLevel.FAIL
                       and "MCR 2.113(Z)" in i.description]
        assert len(fail_issues) >= 1

    def test_known_bad_citation_mcr_99_999(self):
        text = "Pursuant to MCR 99.999, this motion is filed."
        issues = self.auditor.audit(text)
        fail_issues = [i for i in issues if i.level == ComplianceLevel.FAIL
                       and "MCR 99.999" in i.description]
        assert len(fail_issues) >= 1

    def test_lowercase_mcr_warning(self):
        text = "Under mcr 2.119, the Court should act."
        issues = self.auditor.audit(text)
        warn = [i for i in issues if i.level == ComplianceLevel.WARNING
                and "owercase" in i.description.lower()]
        assert len(warn) >= 1

    def test_extract_all_citations_returns_dict(self):
        text = "MCR 2.119, MCL 722.23, MRE 801, Smith v Jones, 123 Mich App 456."
        result = self.auditor.extract_all_citations(text)
        assert "MCR" in result
        assert "MCL" in result
        assert "MRE" in result
        assert "case_law" in result

    def test_multiple_citation_types_counted(self):
        text = "MCR 2.119, MCR 2.113, MCL 722.23, MRE 801."
        result = self.auditor.extract_all_citations(text)
        assert len(result["MCR"]) == 2
        assert len(result["MCL"]) == 1
        assert len(result["MRE"]) == 1

    def test_get_stats_has_known_mcr_count(self):
        stats = self.auditor.get_stats()
        assert "known_mcr_count" in stats
        assert stats["known_mcr_count"] == 21

    def test_empty_text_no_citations(self):
        result = self.auditor.extract_all_citations("")
        assert result["MCR"] == []
        assert result["MCL"] == []
        assert result["MRE"] == []
        assert result["case_law"] == []


# ===================================================================
# TestServiceAuditor
# ===================================================================
class TestServiceAuditor:
    """Tests for ServiceAuditor."""

    def setup_method(self):
        self.auditor = ServiceAuditor()

    def test_no_proof_of_service_fail_early(self):
        issues = self.auditor.audit("Motion text with no service section.")
        assert len(issues) == 1
        assert issues[0].level == ComplianceLevel.FAIL
        assert "No proof of service" in issues[0].description

    def test_has_proof_with_method_pass(self):
        text = (
            "PROOF OF SERVICE\n"
            "I served by first-class mail on Emily A. Watson on 01/15/2025."
        )
        issues = self.auditor.audit(text)
        method_pass = [i for i in issues if i.level == ComplianceLevel.PASS
                       and "method" in i.description.lower()]
        assert len(method_pass) >= 1

    def test_missing_method_fail(self):
        text = (
            "PROOF OF SERVICE\n"
            "I served Emily A. Watson on 01/15/2025."
        )
        issues = self.auditor.audit(text)
        method_fail = [i for i in issues if i.level == ComplianceLevel.FAIL
                       and "method" in i.description.lower()]
        assert len(method_fail) >= 1

    def test_defendant_name_present_pass(self):
        text = (
            "PROOF OF SERVICE\n"
            "I served Emily A. Watson via first-class mail on 01/15/2025."
        )
        issues = self.auditor.audit(text)
        party_pass = [i for i in issues if i.level == ComplianceLevel.PASS
                      and "party" in i.description.lower()]
        assert len(party_pass) >= 1

    def test_defendant_name_missing_warning(self):
        text = (
            "PROOF OF SERVICE\n"
            "I served the opposing party via first-class mail on 01/15/2025."
        )
        issues = self.auditor.audit(text)
        party_warn = [i for i in issues if i.level == ComplianceLevel.WARNING
                      and _DEFENDANT in i.description]
        assert len(party_warn) >= 1

    def test_date_present_pass(self):
        text = (
            "PROOF OF SERVICE\n"
            "I served Emily A. Watson via first-class mail on 01/15/2025."
        )
        issues = self.auditor.audit(text)
        date_pass = [i for i in issues if i.level == ComplianceLevel.PASS
                     and "date" in i.description.lower()]
        assert len(date_pass) >= 1

    def test_date_missing_fail(self):
        text = (
            "PROOF OF SERVICE\n"
            "I served Emily A. Watson via first-class mail last week."
        )
        issues = self.auditor.audit(text)
        date_fail = [i for i in issues if i.level == ComplianceLevel.FAIL
                     and "date" in i.description.lower()]
        assert len(date_fail) >= 1

    def test_complete_proof_multiple_passes(self):
        text = (
            "PROOF OF SERVICE\n"
            "I served Emily A. Watson via first-class mail on 01/15/2025 "
            "at her address of record."
        )
        issues = self.auditor.audit(text)
        passes = [i for i in issues if i.level == ComplianceLevel.PASS]
        assert len(passes) >= 3  # method, party, date

    def test_get_stats_has_required_elements(self):
        stats = self.auditor.get_stats()
        assert "required_elements" in stats
        assert stats["required_elements"] == 5

    def test_first_class_mail_detected(self):
        text = (
            "PROOF OF SERVICE\n"
            "Served via first-class mail to Emily A. Watson on 01/15/2025."
        )
        issues = self.auditor.audit(text)
        method_pass = [i for i in issues if i.level == ComplianceLevel.PASS
                       and "method" in i.description.lower()]
        assert len(method_pass) == 1


# ===================================================================
# TestComplianceAuditor (orchestrator)
# ===================================================================
class TestComplianceAuditor:
    """Tests for the top-level ComplianceAuditor orchestrator."""

    def setup_method(self, tmp_path_factory=None):
        # Use a non-existent temp path so no real DB is touched
        self.db_path = pathlib.Path("__test_nonexistent.db")
        self.auditor = ComplianceAuditor(db_path=self.db_path)

    def test_full_audit_returns_audit_result(self):
        result = self.auditor.full_audit("Some text")
        assert isinstance(result, AuditResult)

    def test_full_audit_filing_type_stored(self):
        result = self.auditor.full_audit("Some text", filing_type="complaint")
        assert result.filing_type == "complaint"

    def test_full_audit_compliant_motion_not_critical(self):
        result = self.auditor.full_audit(_COMPLIANT_MOTION, filing_type="motion")
        assert result.overall_level != ComplianceLevel.CRITICAL

    def test_full_audit_ssn_overall_critical(self):
        text = "SSN: 123-45-6789\nSTATE OF MICHIGAN\nCase No. 2024-001507-DC\nPage 1"
        result = self.auditor.full_audit(text, filing_type="motion")
        assert result.overall_level == ComplianceLevel.CRITICAL

    def test_full_audit_missing_caption_has_fail(self):
        text = "Random text without caption.\n/s/ Andrew\nDate: 01/01/2025\nPage 1"
        result = self.auditor.full_audit(text, filing_type="motion")
        fail_issues = [i for i in result.issues if i.level == ComplianceLevel.FAIL
                       and "Caption" in i.description]
        assert len(fail_issues) >= 1

    def test_audit_format_delegates(self):
        issues = self.auditor.audit_format(
            "STATE OF MICHIGAN\nCase No. 2024-001507-DC\nPage 1"
        )
        assert isinstance(issues, list)
        assert all(isinstance(i, ComplianceIssue) for i in issues)

    def test_audit_content_delegates(self):
        issues = self.auditor.audit_content(
            "/s/ Andrew\nDate: 01/01/2025\nProof of service\nI certify"
        )
        assert isinstance(issues, list)
        assert all(isinstance(i, ComplianceIssue) for i in issues)

    def test_audit_citations_delegates(self):
        issues = self.auditor.audit_citations("MCR 2.119 applies here.")
        assert isinstance(issues, list)
        assert len(issues) >= 1

    def test_audit_service_delegates(self):
        issues = self.auditor.audit_service("No service section here.")
        assert isinstance(issues, list)
        assert len(issues) >= 1

    def test_extract_citations_delegates(self):
        result = self.auditor.extract_citations("MCR 2.119 and MCL 722.23")
        assert "MCR" in result
        assert "MCL" in result

    def test_determine_overall_all_pass(self):
        issues = [ComplianceIssue(level=ComplianceLevel.PASS) for _ in range(3)]
        assert ComplianceAuditor._determine_overall_level(issues) == ComplianceLevel.PASS

    def test_determine_overall_has_warning(self):
        issues = [
            ComplianceIssue(level=ComplianceLevel.PASS),
            ComplianceIssue(level=ComplianceLevel.WARNING),
        ]
        assert ComplianceAuditor._determine_overall_level(issues) == ComplianceLevel.WARNING

    def test_determine_overall_has_fail(self):
        issues = [
            ComplianceIssue(level=ComplianceLevel.PASS),
            ComplianceIssue(level=ComplianceLevel.WARNING),
            ComplianceIssue(level=ComplianceLevel.FAIL),
        ]
        assert ComplianceAuditor._determine_overall_level(issues) == ComplianceLevel.FAIL

    def test_determine_overall_has_critical(self):
        issues = [ComplianceIssue(level=ComplianceLevel.CRITICAL)]
        assert ComplianceAuditor._determine_overall_level(issues) == ComplianceLevel.CRITICAL

    def test_determine_overall_critical_beats_fail(self):
        issues = [
            ComplianceIssue(level=ComplianceLevel.FAIL),
            ComplianceIssue(level=ComplianceLevel.CRITICAL),
        ]
        assert ComplianceAuditor._determine_overall_level(issues) == ComplianceLevel.CRITICAL

    def test_summarize_has_report_header(self):
        result = self.auditor.full_audit(_COMPLIANT_MOTION, filing_type="motion")
        summary = self.auditor.summarize(result)
        assert "COMPLIANCE AUDIT REPORT" in summary

    def test_summarize_has_filing_ready(self):
        result = self.auditor.full_audit(_COMPLIANT_MOTION, filing_type="motion")
        summary = self.auditor.summarize(result)
        assert "Filing Ready:" in summary
        assert "YES" in summary or "NO" in summary

    def test_get_stats_has_sub_auditor_stats(self):
        stats = self.auditor.get_stats()
        assert "format_auditor" in stats
        assert "content_auditor" in stats
        assert "citation_auditor" in stats
        assert "service_auditor" in stats
        assert stats["module"] == "compliance_auditor"

    def test_reset_clears_history(self):
        self.auditor.full_audit("Text one")
        self.auditor.full_audit("Text two")
        assert self.auditor.get_stats()["audits_performed"] == 2
        self.auditor.reset()
        assert self.auditor.get_stats()["audits_performed"] == 0


# ===================================================================
# TestEdgeCases
# ===================================================================
class TestEdgeCases:
    """Edge case and integration-style tests."""

    def test_perfect_filing_is_filing_ready(self):
        auditor = ComplianceAuditor(db_path=pathlib.Path("__test_nonexistent.db"))
        result = auditor.full_audit(_COMPLIANT_MOTION, filing_type="motion")
        assert result.is_filing_ready is True

    def test_empty_text_multiple_failures(self):
        auditor = ComplianceAuditor(db_path=pathlib.Path("__test_nonexistent.db"))
        result = auditor.full_audit("", filing_type="motion")
        assert result.fail_count >= 1
        assert result.is_filing_ready is False

    def test_very_long_text_no_crash(self):
        auditor = ComplianceAuditor(db_path=pathlib.Path("__test_nonexistent.db"))
        long_text = (
            "STATE OF MICHIGAN\nCase No. 2024-001507-DC\nPage 1\n"
            "/s/ Andrew\nDate: 01/01/2025\nProof of service\nI certify\n"
            + ("Lorem ipsum dolor sit amet. " * 5000)
        )
        result = auditor.full_audit(long_text, filing_type="motion")
        assert isinstance(result, AuditResult)
        assert len(result.issues) > 0

    def test_unicode_text_no_crash(self):
        auditor = ComplianceAuditor(db_path=pathlib.Path("__test_nonexistent.db"))
        unicode_text = (
            "STATE OF MICHIGAN\nCase No. 2024-001507-DC\n"
            "Ñoño señor café résumé über naïve coöperate\n"
            "/s/ Andrew\nDate: 01/01/2025\nPage 1\n"
            "Proof of service\nI certify\n"
        )
        result = auditor.full_audit(unicode_text, filing_type="motion")
        assert isinstance(result, AuditResult)

    def test_batch_audit_history_grows(self):
        auditor = ComplianceAuditor(db_path=pathlib.Path("__test_nonexistent.db"))
        for i in range(5):
            auditor.full_audit(f"Filing number {i}. Page 1")
        assert auditor.get_stats()["audits_performed"] == 5

    def test_brief_full_audit_appellate(self):
        auditor = ComplianceAuditor(db_path=pathlib.Path("__test_nonexistent.db"))
        result = auditor.full_audit(_BRIEF_TEXT, filing_type="brief")
        assert isinstance(result, AuditResult)
        assert result.filing_type == "brief"

    def test_constants_match_case(self):
        assert _PLAINTIFF == "Andrew James Pigors"
        assert _DEFENDANT == "Emily A. Watson"
        assert _CHILD_INITIALS == "L.D.W."
        assert _JUDGE == "Hon. Jenny L. McNeill"
        assert _COURT == "14th Circuit Court"

    def test_lane_cases_has_six_lanes(self):
        assert len(LANE_CASES) == 6
        assert "A" in LANE_CASES
        assert "F" in LANE_CASES
        assert LANE_CASES["A"] == "2024-001507-DC"

    def test_persist_with_tmp_db(self, tmp_path):
        db_file = tmp_path / "test_compliance.db"
        # Create the DB file so persist() proceeds
        import sqlite3
        conn = sqlite3.connect(str(db_file))
        conn.close()

        auditor = ComplianceAuditor(db_path=db_file)
        auditor.full_audit(_COMPLIANT_MOTION, filing_type="motion")
        written = auditor.persist()
        assert written == 1

        # Verify data was written
        conn = sqlite3.connect(str(db_file))
        rows = conn.execute("SELECT COUNT(*) FROM compliance_audits").fetchone()
        conn.close()
        assert rows[0] == 1
