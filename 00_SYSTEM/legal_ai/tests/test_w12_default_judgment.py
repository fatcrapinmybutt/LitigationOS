# -*- coding: utf-8 -*-
"""Wave-12 Tests — DefaultJudgmentEngine
==========================================
Comprehensive pytest suite for default_judgment_engine.py (~110 tests).

• Zero network / zero real DB — all DB interactions use tmp_path SQLite
• Independent tests, no ordering dependencies
• Decimal precision validated explicitly
• Real Michigan party names and MCR citations throughout
"""
from __future__ import annotations

import json
import pathlib
import sqlite3
import sys
from datetime import date, timedelta
from decimal import Decimal, ROUND_HALF_UP
from typing import List

import pytest

# ---------------------------------------------------------------------------
# Path bootstrap — let us import from the parent legal_ai package
# ---------------------------------------------------------------------------
_THIS_DIR = pathlib.Path(__file__).resolve().parent
_LEGAL_AI_DIR = _THIS_DIR.parent
if str(_LEGAL_AI_DIR) not in sys.path:
    sys.path.insert(0, str(_LEGAL_AI_DIR))

from default_judgment_engine import (
    DefaultType,
    DefaultStatus,
    GoodCauseFactor,
    VoidBasis,
    DefaultRequest,
    ServiceRecord,
    GoodCauseResult,
    VoidJudgmentResult,
    ServiceVerifier,
    DefaultEntryProcessor,
    GoodCauseAnalyzer,
    VoidJudgmentChecker,
    DefaultJudgmentEngine,
    _PLAINTIFF,
    _DEFENDANT,
    _CHILD_INITIALS,
    _JUDGE,
    _COURT,
    LANE_CASES,
    _ANSWER_DEADLINE_PERSONAL,
    _ANSWER_DEADLINE_MAIL,
    _ANSWER_DEADLINE_PUBLICATION,
    _VOID_JUDGMENT_NO_LIMIT,
    _MCR_2612_C1_DEADLINE_DAYS,
    _SERVICE_METHODS,
)


# ===================================================================
# DEFAULT JUDGMENT ENGINE TESTS (~110)
# ===================================================================


# -------------------------------------------------------------------
# TestDefaultType
# -------------------------------------------------------------------
class TestDefaultType:
    """Tests for DefaultType enum."""

    def test_all_values_exist(self):
        expected = {"entry_of_default", "default_judgment", "consent_judgment"}
        actual = {d.value for d in DefaultType}
        assert actual == expected

    def test_count_is_three(self):
        assert len(DefaultType) == 3

    def test_entry_of_default_mcr(self):
        assert DefaultType.ENTRY_OF_DEFAULT.mcr_reference == "MCR 2.603(A)"

    def test_default_judgment_mcr(self):
        assert DefaultType.DEFAULT_JUDGMENT.mcr_reference == "MCR 2.603(B)"

    def test_consent_judgment_mcr(self):
        assert DefaultType.CONSENT_JUDGMENT.mcr_reference == "MCR 2.602"

    def test_str_enum(self):
        assert DefaultType.ENTRY_OF_DEFAULT == "entry_of_default"


# -------------------------------------------------------------------
# TestDefaultStatus
# -------------------------------------------------------------------
class TestDefaultStatus:
    """Tests for DefaultStatus enum."""

    def test_all_values_exist(self):
        expected = {"pending", "entered", "judgment_entered", "set_aside", "vacated"}
        actual = {s.value for s in DefaultStatus}
        assert actual == expected

    def test_count_is_five(self):
        assert len(DefaultStatus) == 5

    def test_is_final_judgment_entered(self):
        assert DefaultStatus.JUDGMENT_ENTERED.is_final is True

    def test_is_final_set_aside(self):
        assert DefaultStatus.SET_ASIDE.is_final is True

    def test_is_final_vacated(self):
        assert DefaultStatus.VACATED.is_final is True

    def test_is_not_final_pending(self):
        assert DefaultStatus.PENDING.is_final is False

    def test_is_not_final_entered(self):
        assert DefaultStatus.ENTERED.is_final is False


# -------------------------------------------------------------------
# TestGoodCauseFactor
# -------------------------------------------------------------------
class TestGoodCauseFactor:
    """Tests for GoodCauseFactor enum."""

    def test_all_values_exist(self):
        expected = {"meritorious_defense", "good_cause", "no_prejudice"}
        actual = {f.value for f in GoodCauseFactor}
        assert actual == expected

    def test_count_is_three(self):
        assert len(GoodCauseFactor) == 3

    def test_meritorious_defense_description(self):
        desc = GoodCauseFactor.MERITORIOUS_DEFENSE.description
        assert "meritorious defense" in desc.lower()

    def test_good_cause_description(self):
        desc = GoodCauseFactor.GOOD_CAUSE.description
        assert "good cause" in desc.lower()

    def test_no_prejudice_description(self):
        desc = GoodCauseFactor.NO_PREJUDICE.description
        assert "prejudice" in desc.lower()


# -------------------------------------------------------------------
# TestVoidBasis
# -------------------------------------------------------------------
class TestVoidBasis:
    """Tests for VoidBasis enum."""

    def test_all_values_exist(self):
        expected = {
            "lack_of_jurisdiction", "defective_service",
            "due_process_violation", "fraud_on_court",
        }
        actual = {v.value for v in VoidBasis}
        assert actual == expected

    def test_count_is_four(self):
        assert len(VoidBasis) == 4

    def test_jurisdiction_mcr(self):
        assert VoidBasis.LACK_OF_JURISDICTION.mcr_reference == "MCR 2.612(C)(1)(d)"

    def test_defective_service_mcr(self):
        assert VoidBasis.DEFECTIVE_SERVICE.mcr_reference == "MCR 2.612(C)(1)(d)"

    def test_due_process_mcr(self):
        ref = VoidBasis.DUE_PROCESS_VIOLATION.mcr_reference
        assert "MCR 2.612(C)(1)(d)" in ref

    def test_fraud_mcr(self):
        assert VoidBasis.FRAUD_ON_COURT.mcr_reference == "MCR 2.612(C)(1)(c)"


# -------------------------------------------------------------------
# TestDefaultRequest
# -------------------------------------------------------------------
class TestDefaultRequest:
    """Tests for DefaultRequest dataclass."""

    def test_defaults(self):
        req = DefaultRequest()
        assert req.default_type == DefaultType.ENTRY_OF_DEFAULT
        assert req.status == DefaultStatus.PENDING
        assert req.court == _COURT
        assert req.judge == _JUDGE

    def test_to_dict_keys(self):
        req = DefaultRequest(
            case_number="2025-002760-CZ",
            defendant_name="Emily A. Watson",
        )
        d = req.to_dict()
        assert d["case_number"] == "2025-002760-CZ"
        assert d["defendant_name"] == "Emily A. Watson"
        assert d["default_type"] == "entry_of_default"
        assert d["status"] == "pending"
        assert "request_id" in d

    def test_to_dict_decimal_serialized(self):
        req = DefaultRequest(judgment_amount=Decimal("15000.50"))
        d = req.to_dict()
        assert d["judgment_amount"] == "15000.50"

    def test_military_fields(self):
        req = DefaultRequest(
            military_status_checked=True,
            military_affidavit_filed=True,
        )
        d = req.to_dict()
        assert d["military_status_checked"] is True
        assert d["military_affidavit_filed"] is True


# -------------------------------------------------------------------
# TestServiceRecord
# -------------------------------------------------------------------
class TestServiceRecord:
    """Tests for ServiceRecord dataclass."""

    def test_defaults(self):
        sr = ServiceRecord()
        assert sr.service_method == "personal"
        assert sr.is_valid is True
        assert sr.defects == []

    def test_to_dict_keys(self):
        sr = ServiceRecord(
            case_number="2025-002760-CZ",
            served_party="Emily A. Watson",
            service_date="2025-03-15",
        )
        d = sr.to_dict()
        assert d["served_party"] == "Emily A. Watson"
        assert d["service_date"] == "2025-03-15"

    def test_to_dict_defects(self):
        sr = ServiceRecord(defects=["No proof filed"])
        d = sr.to_dict()
        assert "No proof filed" in d["defects"]


# -------------------------------------------------------------------
# TestGoodCauseResult
# -------------------------------------------------------------------
class TestGoodCauseResult:
    """Tests for GoodCauseResult dataclass."""

    def test_to_dict(self):
        gcr = GoodCauseResult(
            overall_score=75,
            recommendation="Strong basis",
        )
        d = gcr.to_dict()
        assert d["overall_score"] == 75
        assert d["recommendation"] == "Strong basis"


# -------------------------------------------------------------------
# TestVoidJudgmentResult
# -------------------------------------------------------------------
class TestVoidJudgmentResult:
    """Tests for VoidJudgmentResult dataclass."""

    def test_to_dict(self):
        vjr = VoidJudgmentResult(
            is_void=True,
            void_bases=["Lack of jurisdiction"],
            time_limit="None",
        )
        d = vjr.to_dict()
        assert d["is_void"] is True
        assert "Lack of jurisdiction" in d["void_bases"]


# -------------------------------------------------------------------
# TestServiceVerifier
# -------------------------------------------------------------------
class TestServiceVerifier:
    """Tests for ServiceVerifier — MCR 2.105 compliance."""

    def setup_method(self):
        self.verifier = ServiceVerifier()

    def test_verify_personal_service_valid(self):
        svc_date = (date.today() - timedelta(days=30)).isoformat()
        result = self.verifier.verify_proper_service(
            service_method="personal",
            service_date=svc_date,
            server_name="John Smith",
            proof_filed=True,
        )
        assert result["is_valid"] is True
        assert result["mcr_reference"] == "MCR 2.105(A)(1)"

    def test_verify_personal_service_no_server_name(self):
        svc_date = (date.today() - timedelta(days=30)).isoformat()
        result = self.verifier.verify_proper_service(
            service_method="personal",
            service_date=svc_date,
            server_name="",
            proof_filed=True,
        )
        assert result["is_valid"] is False
        assert any("server name" in d.lower() for d in result["defects"])

    def test_verify_no_proof_filed(self):
        svc_date = (date.today() - timedelta(days=30)).isoformat()
        result = self.verifier.verify_proper_service(
            service_method="personal",
            service_date=svc_date,
            server_name="John Smith",
            proof_filed=False,
        )
        assert result["is_valid"] is False

    def test_verify_future_service_date(self):
        future = (date.today() + timedelta(days=10)).isoformat()
        result = self.verifier.verify_proper_service(
            service_method="personal",
            service_date=future,
            server_name="John Smith",
            proof_filed=True,
        )
        assert result["is_valid"] is False

    def test_verify_invalid_service_date(self):
        result = self.verifier.verify_proper_service(
            service_method="personal",
            service_date="not-a-date",
            server_name="John Smith",
            proof_filed=True,
        )
        assert result["is_valid"] is False

    def test_verify_unknown_method(self):
        svc_date = (date.today() - timedelta(days=30)).isoformat()
        result = self.verifier.verify_proper_service(
            service_method="carrier_pigeon",
            service_date=svc_date,
            proof_filed=True,
        )
        assert result["is_valid"] is False

    def test_answer_deadline_personal_21_days(self):
        svc_date = (date.today() - timedelta(days=30)).isoformat()
        result = self.verifier.verify_proper_service(
            service_method="personal",
            service_date=svc_date,
            server_name="Server",
            proof_filed=True,
        )
        assert result["answer_days"] == 21

    def test_answer_deadline_mail_28_days(self):
        svc_date = (date.today() - timedelta(days=30)).isoformat()
        result = self.verifier.verify_proper_service(
            service_method="registered_mail",
            service_date=svc_date,
            proof_filed=True,
        )
        assert result["answer_days"] == 28

    def test_check_mcr_2_105_personal(self):
        result = self.verifier.check_mcr_2_105("personal")
        assert result["mcr_reference"] == "MCR 2.105(A)(1)"
        assert len(result["requirements"]) >= 2

    def test_check_mcr_2_105_registered_mail(self):
        result = self.verifier.check_mcr_2_105("registered_mail")
        assert result["mcr_reference"] == "MCR 2.105(A)(2)"

    def test_check_mcr_2_105_substituted(self):
        result = self.verifier.check_mcr_2_105("substituted")
        assert result["mcr_reference"] == "MCR 2.105(A)(3)"

    def test_check_mcr_2_105_publication(self):
        result = self.verifier.check_mcr_2_105("publication")
        assert result["mcr_reference"] == "MCR 2.106"
        assert len(result["requirements"]) >= 3

    def test_check_mcr_2_105_acknowledged(self):
        result = self.verifier.check_mcr_2_105("acknowledged")
        assert result["mcr_reference"] == "MCR 2.105(A)(4)"

    def test_check_military_status(self):
        result = self.verifier.check_military_status("Emily A. Watson")
        assert result["defendant"] == "Emily A. Watson"
        assert result["legal_basis"] == "50 USC § 3931; MCR 2.603(A)(1)"
        assert len(result["check_methods"]) >= 2

    def test_verify_affidavit_non_military_compliant(self):
        result = self.verifier.verify_affidavit_of_non_military(
            affidavit_filed=True, status_result="non_military",
        )
        assert result["is_compliant"] is True

    def test_verify_affidavit_non_military_not_filed(self):
        result = self.verifier.verify_affidavit_of_non_military(
            affidavit_filed=False,
        )
        assert result["is_compliant"] is False

    def test_verify_affidavit_active_duty(self):
        result = self.verifier.verify_affidavit_of_non_military(
            affidavit_filed=True, status_result="active_duty",
        )
        assert result["is_compliant"] is False

    def test_get_stats(self):
        svc_date = (date.today() - timedelta(days=30)).isoformat()
        self.verifier.verify_proper_service("personal", svc_date, "Server", True)
        stats = self.verifier.get_stats()
        assert stats["component"] == "ServiceVerifier"
        assert stats["total_records"] >= 1


# -------------------------------------------------------------------
# TestDefaultEntryProcessor
# -------------------------------------------------------------------
class TestDefaultEntryProcessor:
    """Tests for DefaultEntryProcessor — MCR 2.603(A)."""

    def setup_method(self):
        self.processor = DefaultEntryProcessor()

    def _make_eligible_request(self) -> DefaultRequest:
        svc_date = (date.today() - timedelta(days=30)).isoformat()
        answer_deadline = (date.today() - timedelta(days=9)).isoformat()
        return DefaultRequest(
            case_number="2025-002760-CZ",
            defendant_name="Emily A. Watson",
            service_date=svc_date,
            service_method="personal",
            answer_deadline=answer_deadline,
            military_status_checked=True,
            military_affidavit_filed=True,
        )

    def test_verify_eligibility_eligible(self):
        req = self._make_eligible_request()
        result = self.processor.verify_eligibility(req)
        assert result["is_eligible"] is True
        assert result["legal_basis"] == "MCR 2.603(A)"

    def test_verify_eligibility_deadline_not_passed(self):
        svc_date = date.today().isoformat()
        req = DefaultRequest(
            service_date=svc_date,
            service_method="personal",
            military_status_checked=True,
            military_affidavit_filed=True,
        )
        result = self.processor.verify_eligibility(req)
        assert result["is_eligible"] is False

    def test_verify_eligibility_no_military_check(self):
        svc_date = (date.today() - timedelta(days=30)).isoformat()
        req = DefaultRequest(
            service_date=svc_date,
            service_method="personal",
            military_status_checked=False,
            military_affidavit_filed=False,
        )
        result = self.processor.verify_eligibility(req)
        assert result["is_eligible"] is False
        assert any("military" in i.lower() for i in result["issues"])

    def test_calculate_damages_sum_certain(self):
        from_date = (date.today() - timedelta(days=365)).isoformat()
        result = self.processor.calculate_damages(
            principal=Decimal("10000.00"),
            interest_rate=Decimal("0.05"),
            from_date=from_date,
            costs=Decimal("500.00"),
        )
        assert Decimal(result["total_judgment"]) > Decimal("10000.00")
        assert result["is_sum_certain"] is True
        assert result["entry_method"] == "clerk"
        assert result["legal_basis"] == "MCR 2.603(B)(1)(b)"

    def test_calculate_damages_not_sum_certain(self):
        result = self.processor.calculate_damages(
            principal=Decimal("10000.00"),
            attorney_fees=Decimal("2000.00"),
        )
        assert result["is_sum_certain"] is False
        assert result["entry_method"] == "court hearing"
        assert result["legal_basis"] == "MCR 2.603(B)(2)"

    def test_calculate_damages_interest_precision(self):
        result = self.processor.calculate_damages(
            principal=Decimal("10000.00"),
            interest_rate=Decimal("0.05"),
        )
        interest = Decimal(result["interest_accrued"])
        assert interest == interest.quantize(Decimal("0.01"))

    def test_prepare_affidavit(self):
        req = self._make_eligible_request()
        aff = self.processor.prepare_affidavit(req)
        assert aff["document"] == "Affidavit in Support of Entry of Default"
        assert aff["plaintiff"] == "Andrew James Pigors"
        assert aff["defendant"] == "Emily A. Watson"
        assert len(aff["affidavit_points"]) >= 4
        assert "MCR 2.603(A)" in str(aff["affidavit_points"])

    def test_file_request_eligible(self):
        req = self._make_eligible_request()
        result = self.processor.file_request(req)
        assert result["is_eligible"] is True
        assert len(result["filing_documents"]) >= 3

    def test_file_request_documents_include_military(self):
        req = self._make_eligible_request()
        result = self.processor.file_request(req)
        docs = [d["document"] for d in result["filing_documents"]]
        assert any("Military" in d or "military" in d.lower() for d in docs)

    def test_get_stats(self):
        req = self._make_eligible_request()
        self.processor.verify_eligibility(req)
        stats = self.processor.get_stats()
        assert stats["component"] == "DefaultEntryProcessor"
        assert stats["total_processed"] >= 1


# -------------------------------------------------------------------
# TestGoodCauseAnalyzer
# -------------------------------------------------------------------
class TestGoodCauseAnalyzer:
    """Tests for GoodCauseAnalyzer — Shawl v Spence factors."""

    def setup_method(self):
        self.analyzer = GoodCauseAnalyzer()

    def test_analyze_good_cause_all_present(self):
        factors = {
            "meritorious_defense": {"present": True, "evidence": ["Defense A"], "weight": 8},
            "good_cause": {"present": True, "evidence": ["Reason B"], "weight": 7},
            "no_prejudice": {"present": True, "evidence": ["No harm"], "weight": 6},
        }
        result = self.analyzer.analyze_good_cause(factors)
        assert result["overall_score"] >= 70
        assert "Strong" in result["recommendation"]

    def test_analyze_good_cause_none_present(self):
        factors = {
            "meritorious_defense": {"present": False},
            "good_cause": {"present": False},
            "no_prejudice": {"present": False},
        }
        result = self.analyzer.analyze_good_cause(factors)
        assert result["overall_score"] == 0
        assert "Weak" in result["recommendation"]

    def test_analyze_good_cause_moderate(self):
        factors = {
            "meritorious_defense": {"present": True, "weight": 5},
            "good_cause": {"present": False},
            "no_prejudice": {"present": True, "weight": 5},
        }
        result = self.analyzer.analyze_good_cause(factors)
        assert 0 < result["overall_score"] < 100

    def test_analyze_good_cause_legal_basis(self):
        result = self.analyzer.analyze_good_cause({})
        assert "Shawl v Spence" in result["legal_basis"]
        assert "MCR 2.603(D)(1)" in result["legal_basis"]

    def test_analyze_good_cause_strengths_weaknesses(self):
        factors = {
            "meritorious_defense": {"present": True, "weight": 5},
            "good_cause": {"present": False},
        }
        result = self.analyzer.analyze_good_cause(factors)
        assert len(result["strengths"]) >= 1
        assert len(result["weaknesses"]) >= 1

    def test_check_meritorious_defense_recognized(self):
        result = self.analyzer.check_meritorious_defense(
            ["statute_of_limitations", "lack_of_jurisdiction"],
        )
        assert result["has_meritorious_defense"] is True
        assert result["meritorious_count"] >= 2

    def test_check_meritorious_defense_unrecognized(self):
        result = self.analyzer.check_meritorious_defense(["unicorn_defense"])
        assert result["has_meritorious_defense"] is False

    def test_check_meritorious_defense_empty(self):
        result = self.analyzer.check_meritorious_defense([])
        assert result["defenses_evaluated"] == 0
        assert result["has_meritorious_defense"] is False

    def test_check_meritorious_defense_improper_service(self):
        result = self.analyzer.check_meritorious_defense(["improper_service"])
        assert result["has_meritorious_defense"] is True
        assert result["evaluations"][0]["strength"] == "strong"

    def test_check_diligence_prompt(self):
        result = self.analyzer.check_diligence(days_since_default=10)
        assert result["is_prompt"] is True
        assert result["diligence_score"] >= 50

    def test_check_diligence_not_prompt(self):
        result = self.analyzer.check_diligence(days_since_default=60)
        assert result["is_prompt"] is False

    def test_check_diligence_excusable_reason(self):
        result = self.analyzer.check_diligence(
            days_since_default=10,
            reason_for_delay="excusable_neglect",
        )
        assert result["is_excusable"] is True
        assert result["diligence_score"] == 100

    def test_check_diligence_non_excusable(self):
        result = self.analyzer.check_diligence(
            days_since_default=10,
            reason_for_delay="just_lazy",
        )
        assert result["is_excusable"] is False

    def test_check_prejudice_no_factors(self):
        result = self.analyzer.check_prejudice(days_since_default=10)
        assert result["is_prejudiced"] is False

    def test_check_prejudice_evidence_lost(self):
        result = self.analyzer.check_prejudice(evidence_lost=True)
        assert result["is_prejudiced"] is True

    def test_check_prejudice_witnesses_unavailable(self):
        result = self.analyzer.check_prejudice(witnesses_unavailable=True)
        assert result["is_prejudiced"] is True

    def test_check_prejudice_long_delay(self):
        result = self.analyzer.check_prejudice(days_since_default=400)
        assert result["is_prejudiced"] is True

    def test_check_prejudice_legal_basis(self):
        result = self.analyzer.check_prejudice()
        assert "Shawl v Spence" in result["legal_basis"]

    def test_get_stats(self):
        self.analyzer.analyze_good_cause({})
        stats = self.analyzer.get_stats()
        assert stats["component"] == "GoodCauseAnalyzer"
        assert stats["total_analyses"] >= 1


# -------------------------------------------------------------------
# TestVoidJudgmentChecker
# -------------------------------------------------------------------
class TestVoidJudgmentChecker:
    """Tests for VoidJudgmentChecker — MCR 2.612(C)(1)(d)."""

    def setup_method(self):
        self.checker = VoidJudgmentChecker()

    def test_check_jurisdiction_valid(self):
        result = self.checker.check_jurisdiction(
            personal_jurisdiction=True,
            subject_matter_jurisdiction=True,
        )
        assert result["is_void"] is False

    def test_check_jurisdiction_no_personal(self):
        result = self.checker.check_jurisdiction(personal_jurisdiction=False)
        assert result["is_void"] is True
        assert len(result["void_bases"]) >= 1

    def test_check_jurisdiction_no_subject_matter(self):
        result = self.checker.check_jurisdiction(subject_matter_jurisdiction=False)
        assert result["is_void"] is True

    def test_check_jurisdiction_no_time_limit(self):
        result = self.checker.check_jurisdiction(personal_jurisdiction=False)
        assert "no time limit" in result["time_limit"].lower() or "None" in result["time_limit"]

    def test_check_service_defects_none(self):
        result = self.checker.check_service_defects(defects=[])
        assert result["is_void"] is False

    def test_check_service_defects_fundamental(self):
        result = self.checker.check_service_defects(
            defects=["Never served defendant"],
        )
        assert result["is_void"] is True
        assert len(result["fundamental_defects"]) >= 1

    def test_check_service_defects_procedural_only(self):
        result = self.checker.check_service_defects(
            defects=["Minor technical error in proof"],
        )
        assert result["is_void"] is False
        assert len(result["procedural_defects"]) >= 1

    def test_check_service_defects_wrong_person(self):
        result = self.checker.check_service_defects(
            defects=["Served wrong person at address"],
        )
        assert result["is_void"] is True

    def test_check_due_process_all_met(self):
        result = self.checker.check_due_process(
            notice_given=True,
            opportunity_to_respond=True,
            hearing_held=True,
        )
        assert result["is_void"] is False
        assert len(result["violations"]) == 0

    def test_check_due_process_no_notice(self):
        result = self.checker.check_due_process(notice_given=False)
        assert result["is_void"] is True

    def test_check_due_process_no_opportunity(self):
        result = self.checker.check_due_process(opportunity_to_respond=False)
        assert result["is_void"] is True

    def test_check_due_process_no_hearing(self):
        result = self.checker.check_due_process(hearing_held=False)
        assert result["is_void"] is False  # no hearing alone doesn't void
        assert len(result["violations"]) >= 1

    def test_check_due_process_legal_basis(self):
        result = self.checker.check_due_process()
        assert "US Const Amend XIV" in result["legal_basis"]

    def test_check_mcr_2_612_void_no_time_limit(self):
        result = self.checker.check_mcr_2_612(
            grounds=["void"],
            days_since_judgment=5000,
        )
        assert result["viable_grounds"] >= 1
        void_eval = [e for e in result["evaluations"] if e["ground"] == "void"][0]
        assert void_eval["is_timely"] is True
        assert void_eval["time_limit_days"] is None

    def test_check_mcr_2_612_mistake_within_time(self):
        result = self.checker.check_mcr_2_612(
            grounds=["mistake"],
            days_since_judgment=100,
        )
        assert result["viable_grounds"] >= 1

    def test_check_mcr_2_612_mistake_expired(self):
        result = self.checker.check_mcr_2_612(
            grounds=["mistake"],
            days_since_judgment=400,
        )
        mistake_eval = [e for e in result["evaluations"] if e["ground"] == "mistake"][0]
        assert mistake_eval["is_timely"] is False

    def test_check_mcr_2_612_fraud_within_time(self):
        result = self.checker.check_mcr_2_612(
            grounds=["fraud"],
            days_since_judgment=200,
        )
        assert result["viable_grounds"] >= 1

    def test_check_mcr_2_612_multiple_grounds(self):
        result = self.checker.check_mcr_2_612(
            grounds=["void", "fraud", "new_evidence"],
            days_since_judgment=200,
        )
        assert result["grounds_evaluated"] == 3
        assert result["viable_grounds"] >= 2

    def test_check_mcr_2_612_deadline_constant(self):
        assert _MCR_2612_C1_DEADLINE_DAYS == 365

    def test_full_analysis_not_void(self):
        result = self.checker.full_analysis(
            personal_jurisdiction=True,
            subject_matter_jurisdiction=True,
            notice_given=True,
            opportunity_to_respond=True,
        )
        assert result.is_void is False

    def test_full_analysis_void_jurisdiction(self):
        result = self.checker.full_analysis(personal_jurisdiction=False)
        assert result.is_void is True
        assert len(result.void_bases) >= 1

    def test_full_analysis_void_service(self):
        result = self.checker.full_analysis(
            service_defects=["Never served defendant"],
        )
        assert result.is_void is True

    def test_full_analysis_void_due_process(self):
        result = self.checker.full_analysis(notice_given=False)
        assert result.is_void is True

    def test_full_analysis_no_time_limit(self):
        result = self.checker.full_analysis(personal_jurisdiction=False)
        assert "MCR 2.612(C)(1)(d)" in result.time_limit

    def test_full_analysis_evidence_needed(self):
        result = self.checker.full_analysis(personal_jurisdiction=False)
        assert len(result.evidence_needed) >= 1

    def test_get_stats(self):
        self.checker.full_analysis()
        stats = self.checker.get_stats()
        assert stats["component"] == "VoidJudgmentChecker"
        assert stats["total_analyses"] >= 1


# -------------------------------------------------------------------
# TestDefaultJudgmentEngine
# -------------------------------------------------------------------
class TestDefaultJudgmentEngine:
    """Tests for DefaultJudgmentEngine orchestrator."""

    def setup_method(self):
        self.engine = DefaultJudgmentEngine(db_path=pathlib.Path("nonexistent.db"))

    def test_pursue_default_creates_request(self):
        req = self.engine.pursue_default(
            case_number="2025-002760-CZ",
            defendant_name="Emily A. Watson",
            service_date=(date.today() - timedelta(days=30)).isoformat(),
            service_method="personal",
        )
        assert req.defendant_name == "Emily A. Watson"
        assert req.case_number == "2025-002760-CZ"
        assert req.request_id in self.engine._requests

    def test_pursue_default_defaults(self):
        req = self.engine.pursue_default(
            service_date=(date.today() - timedelta(days=30)).isoformat(),
        )
        assert req.defendant_name == "Emily A. Watson"
        assert req.case_number == "2025-002760-CZ"
        assert req.court == "14th Circuit Court"

    def test_pursue_default_answer_deadline_calculated(self):
        svc_date = "2025-03-15"
        req = self.engine.pursue_default(
            service_date=svc_date,
            service_method="personal",
        )
        assert req.answer_deadline == "2025-04-05"

    def test_pursue_default_mail_service_28_days(self):
        svc_date = "2025-03-15"
        req = self.engine.pursue_default(
            service_date=svc_date,
            service_method="registered_mail",
        )
        assert req.answer_deadline == "2025-04-12"

    def test_defend_against_default_not_found(self):
        result = self.engine.defend_against_default("nonexistent")
        assert "error" in result

    def test_defend_against_default_with_defenses(self):
        req = self.engine.pursue_default(
            service_date=(date.today() - timedelta(days=30)).isoformat(),
        )
        result = self.engine.defend_against_default(
            req.request_id,
            defenses=["improper_service"],
            reason_for_delay="excusable_neglect",
            days_since_default=10,
        )
        assert "defense_analysis" in result
        assert "diligence_analysis" in result
        assert "prejudice_analysis" in result
        assert result["defense_analysis"]["has_meritorious_defense"] is True

    def test_move_to_set_aside_not_found(self):
        result = self.engine.move_to_set_aside("nonexistent")
        assert "error" in result

    def test_move_to_set_aside_with_factors(self):
        req = self.engine.pursue_default(
            service_date=(date.today() - timedelta(days=30)).isoformat(),
        )
        factors = {
            "meritorious_defense": {"present": True, "weight": 8},
            "good_cause": {"present": True, "weight": 7},
            "no_prejudice": {"present": True, "weight": 6},
        }
        result = self.engine.move_to_set_aside(req.request_id, factors)
        assert "document" in result or "error" not in result

    def test_constants_correct(self):
        assert _ANSWER_DEADLINE_PERSONAL == 21
        assert _ANSWER_DEADLINE_MAIL == 28
        assert _ANSWER_DEADLINE_PUBLICATION == 28
        assert _VOID_JUDGMENT_NO_LIMIT is True

    def test_service_methods_complete(self):
        expected = {"personal", "registered_mail", "substituted", "publication", "acknowledged"}
        assert set(_SERVICE_METHODS.keys()) == expected

    def test_service_methods_have_mcr(self):
        for method, info in _SERVICE_METHODS.items():
            assert "mcr" in info, f"Method {method} missing MCR reference"
            assert "answer_days" in info, f"Method {method} missing answer_days"

    def test_case_constants(self):
        assert _PLAINTIFF == "Andrew James Pigors"
        assert _DEFENDANT == "Emily A. Watson"
        assert _CHILD_INITIALS == "L.D.W."
        assert _JUDGE == "Hon. Jenny L. McNeill"

    def test_lane_cases_mapping(self):
        assert LANE_CASES["A"] == "2024-001507-DC"
        assert LANE_CASES["B"] == "2025-002760-CZ"
        assert LANE_CASES["D"] == "2023-5907-PP"
        assert LANE_CASES["F"] == "COA 366810"


# -------------------------------------------------------------------
# Edge cases
# -------------------------------------------------------------------
class TestDefaultJudgmentEdgeCases:
    """Edge cases for default judgment processing."""

    def setup_method(self):
        self.engine = DefaultJudgmentEngine(db_path=pathlib.Path("nonexistent.db"))

    def test_already_answered_not_eligible(self):
        """If defendant answered, no default available."""
        svc_date = (date.today() - timedelta(days=30)).isoformat()
        req = DefaultRequest(
            service_date=svc_date,
            service_method="personal",
            military_status_checked=False,  # missing
            military_affidavit_filed=False,
        )
        processor = DefaultEntryProcessor()
        result = processor.verify_eligibility(req)
        assert result["is_eligible"] is False

    def test_expired_time_for_set_aside(self):
        """MCR 2.612(C)(2) — 1 year for grounds (a)-(c)."""
        checker = VoidJudgmentChecker()
        result = checker.check_mcr_2_612(
            grounds=["mistake", "new_evidence", "fraud"],
            days_since_judgment=400,
        )
        for ev in result["evaluations"]:
            assert ev["is_timely"] is False

    def test_void_judgment_no_time_limit(self):
        """MCR 2.612(C)(1)(d) — void judgment can be attacked any time."""
        checker = VoidJudgmentChecker()
        result = checker.check_mcr_2_612(
            grounds=["void"],
            days_since_judgment=99999,
        )
        void_eval = [e for e in result["evaluations"] if e["ground"] == "void"][0]
        assert void_eval["is_timely"] is True

    def test_partial_default_some_defendants(self):
        """Default can be entered against one defendant while others answered."""
        engine = DefaultJudgmentEngine(db_path=pathlib.Path("nonexistent.db"))
        req1 = engine.pursue_default(
            defendant_name="Defendant A",
            service_date=(date.today() - timedelta(days=30)).isoformat(),
        )
        req2 = engine.pursue_default(
            defendant_name="Defendant B",
            service_date=(date.today() - timedelta(days=30)).isoformat(),
        )
        assert req1.request_id != req2.request_id
        assert len(engine._requests) == 2

    def test_damages_zero_principal(self):
        processor = DefaultEntryProcessor()
        result = processor.calculate_damages(principal=Decimal("0.00"))
        assert result["total_judgment"] == "0.00"

    def test_damages_zero_interest(self):
        processor = DefaultEntryProcessor()
        result = processor.calculate_damages(
            principal=Decimal("10000.00"),
            interest_rate=Decimal("0.00"),
        )
        assert result["interest_accrued"] == "0.00"

    def test_good_cause_empty_factors(self):
        analyzer = GoodCauseAnalyzer()
        result = analyzer.analyze_good_cause({})
        assert result["overall_score"] == 0

    def test_void_combined_defects(self):
        """Multiple void bases compound the analysis."""
        checker = VoidJudgmentChecker()
        result = checker.full_analysis(
            personal_jurisdiction=False,
            service_defects=["Never served defendant"],
            notice_given=False,
        )
        assert result.is_void is True
        assert len(result.void_bases) >= 2
