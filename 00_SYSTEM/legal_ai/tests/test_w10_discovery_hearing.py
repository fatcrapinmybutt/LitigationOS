# -*- coding: utf-8 -*-
"""Wave-10 Tests — DiscoveryManager & HearingPreparation
=========================================================
~130 tests covering discovery_manager.py and hearing_preparation.py.

• Zero network / zero real DB — all DB interactions use temp SQLite
• tempfile + tmp_path for filesystem isolation
• unittest.mock.patch for isolation
• Independent tests, no ordering dependencies
"""
from __future__ import annotations

import json
import pathlib
import sqlite3
import sys
import uuid
from datetime import date, datetime, timedelta, timezone
from typing import Any, Dict, List
from unittest.mock import MagicMock, patch

import pytest

# ---------------------------------------------------------------------------
# Import targets
# ---------------------------------------------------------------------------
_THIS_DIR = pathlib.Path(__file__).resolve().parent
_LEGAL_AI_DIR = _THIS_DIR.parent
if str(_LEGAL_AI_DIR) not in sys.path:
    sys.path.insert(0, str(_LEGAL_AI_DIR))

from discovery_manager import (
    DiscoveryType,
    DiscoveryStatus,
    ObjectionType,
    ServiceMethod,
    DiscoveryItem,
    DiscoveryRequest,
    PrivilegeLogEntry,
    MeetAndConferRecord,
    MotionToCompel,
    DiscoveryReport,
    DiscoveryCalendar,
    ResponseDrafter,
    MotionToCompelGenerator,
    DiscoveryManager,
    _PLAINTIFF,
    _DEFENDANT,
    _CHILD_INITIALS,
    _JUDGE,
    LANE_CASES,
    _MCR_2309_RESPONSE_DAYS,
    _MCR_2310_RESPONSE_DAYS,
    _MCR_2312_RESPONSE_DAYS,
    _ADDITIONAL_MAIL_SERVICE_DAYS,
)

from hearing_preparation import (
    HearingType,
    HearingStatus,
    ArgumentStrength,
    ExhibitStatus,
    WitnessEntry,
    HearingExhibit,
    LegalArgument,
    HearingRecord,
    HearingChecklist,
    HearingPlanner,
    ArgumentBuilder,
    ExhibitOrganizer,
    HearingPreparation,
    _PLAINTIFF as HP_PLAINTIFF,
    _COURT,
    _COURT_ADDRESS,
    LANE_CASES as HP_LANE_CASES,
)


# ═══════════════════════════════════════════════════════════════════════════
# Fixtures
# ═══════════════════════════════════════════════════════════════════════════

@pytest.fixture
def dm(tmp_path: pathlib.Path) -> DiscoveryManager:
    return DiscoveryManager(db_path=str(tmp_path / "disc.db"))


@pytest.fixture
def hp(tmp_path: pathlib.Path) -> HearingPreparation:
    return HearingPreparation(db_path=str(tmp_path / "hear.db"))


@pytest.fixture
def sample_items() -> List[DiscoveryItem]:
    return [
        DiscoveryItem(item_number=1, text="Describe all communications with X."),
        DiscoveryItem(item_number=2, text="Identify all witnesses."),
        DiscoveryItem(item_number=3, text="Produce financial records."),
    ]


@pytest.fixture
def sample_request(sample_items: List[DiscoveryItem]) -> DiscoveryRequest:
    return DiscoveryRequest(
        request_id="req-test-001",
        discovery_type=DiscoveryType.INTERROGATORY,
        case_number="2024-001507-DC",
        lane="A",
        items=sample_items,
        date_served="2025-01-06",
        date_due="2025-02-06",
        status=DiscoveryStatus.SERVED,
    )


@pytest.fixture
def sample_hearing() -> HearingRecord:
    return HearingRecord(
        hearing_id="hear-test-001",
        hearing_type=HearingType.MOTION,
        case_number="2024-001507-DC",
        lane="A",
        hearing_date="2025-03-15",
        hearing_time="09:00",
        issues=["Custody modification", "Parenting time"],
    )


@pytest.fixture
def trial_hearing() -> HearingRecord:
    """A TRIAL hearing with witnesses and exhibits for full-prep tests."""
    witnesses = [
        WitnessEntry(
            name="Dr. Smith",
            role="Expert",
            testimony_topics=["Custody modification"],
            estimated_duration_minutes=30,
            subpoena_needed=True,
            subpoena_served=False,
        ),
        WitnessEntry(
            name="Jane Doe",
            role="Fact Witness",
            testimony_topics=["Parenting time"],
            estimated_duration_minutes=20,
        ),
    ]
    exhibits = [
        HearingExhibit(
            exhibit_number="P-1",
            title="Email Thread",
            related_issues=["Custody modification"],
            foundation_ready=True,
        ),
        HearingExhibit(
            exhibit_number="P-2",
            title="Financial Records",
            related_issues=["Parenting time"],
            foundation_ready=False,
        ),
    ]
    return HearingRecord(
        hearing_id="trial-001",
        hearing_type=HearingType.TRIAL,
        case_number="2024-001507-DC",
        lane="A",
        hearing_date="2025-06-01",
        hearing_time="08:30",
        issues=["Custody modification", "Parenting time"],
        witnesses=witnesses,
        exhibits=exhibits,
    )


# ═══════════════════════════════════════════════════════════════════════════
#  PART 1 — discovery_manager.py  (~70 tests)
# ═══════════════════════════════════════════════════════════════════════════


class TestDiscoveryType:
    """DiscoveryType enum: values, mcr_reference, response_days."""

    def test_all_six_values(self):
        names = {m.name for m in DiscoveryType}
        expected = {
            "INTERROGATORY", "REQUEST_PRODUCTION", "REQUEST_ADMISSION",
            "DEPOSITION_NOTICE", "SUBPOENA", "INSPECTION",
        }
        assert names == expected

    def test_mcr_reference_interrogatory(self):
        assert DiscoveryType.INTERROGATORY.mcr_reference == "MCR 2.309"

    def test_mcr_reference_production(self):
        assert DiscoveryType.REQUEST_PRODUCTION.mcr_reference == "MCR 2.310"

    def test_mcr_reference_admission(self):
        assert DiscoveryType.REQUEST_ADMISSION.mcr_reference == "MCR 2.312"

    def test_mcr_reference_deposition(self):
        assert DiscoveryType.DEPOSITION_NOTICE.mcr_reference == "MCR 2.306"

    def test_mcr_reference_subpoena(self):
        assert DiscoveryType.SUBPOENA.mcr_reference == "MCR 2.305"

    def test_mcr_reference_inspection(self):
        assert DiscoveryType.INSPECTION.mcr_reference == "MCR 2.310(B)"

    def test_response_days_interrogatory(self):
        assert DiscoveryType.INTERROGATORY.response_days == _MCR_2309_RESPONSE_DAYS

    def test_response_days_production(self):
        assert DiscoveryType.REQUEST_PRODUCTION.response_days == _MCR_2310_RESPONSE_DAYS

    def test_response_days_admission(self):
        assert DiscoveryType.REQUEST_ADMISSION.response_days == _MCR_2312_RESPONSE_DAYS

    def test_response_days_deposition(self):
        assert DiscoveryType.DEPOSITION_NOTICE.response_days == 14

    def test_response_days_subpoena(self):
        assert DiscoveryType.SUBPOENA.response_days == 14


class TestDiscoveryStatus:
    """DiscoveryStatus enum validation."""

    def test_all_eight_values(self):
        names = {m.name for m in DiscoveryStatus}
        expected = {
            "DRAFT", "SERVED", "RESPONSE_DUE", "RESPONDED",
            "OBJECTED", "OVERDUE", "MOTION_TO_COMPEL", "COMPLETED",
        }
        assert names == expected

    def test_string_membership(self):
        assert DiscoveryStatus.DRAFT.value == "draft"
        assert DiscoveryStatus.OVERDUE.value == "overdue"

    def test_is_str_enum(self):
        assert isinstance(DiscoveryStatus.SERVED, str)


class TestObjectionType:
    """ObjectionType enum: values, template property."""

    def test_all_ten_values(self):
        assert len(ObjectionType) == 10

    def test_template_not_empty(self):
        for obj in ObjectionType:
            assert obj.template, f"{obj.name} has empty template"

    def test_template_vague_text(self):
        t = ObjectionType.VAGUE_AND_AMBIGUOUS.template
        assert "vague" in t.lower()
        assert "ambiguous" in t.lower()

    def test_template_privilege_text(self):
        t = ObjectionType.PRIVILEGE.template
        assert "attorney-client privilege" in t

    def test_template_work_product_mcr(self):
        t = ObjectionType.WORK_PRODUCT.template
        assert "MCR 2.302(B)(3)" in t


class TestServiceMethod:
    """ServiceMethod enum validation."""

    def test_all_five_values(self):
        names = {m.name for m in ServiceMethod}
        assert names == {"PERSONAL", "MAIL", "EMAIL", "FAX", "COURTHOUSE_BOX"}

    def test_string_values(self):
        assert ServiceMethod.MAIL.value == "mail"
        assert ServiceMethod.PERSONAL.value == "personal"


class TestDiscoveryItem:
    """DiscoveryItem dataclass tests."""

    def test_defaults(self):
        item = DiscoveryItem()
        assert item.item_number == 0
        assert item.text == ""
        assert item.response == ""
        assert item.objections == []
        assert item.is_answered is False

    def test_to_dict_keys(self):
        item = DiscoveryItem(item_number=1, text="Test?")
        d = item.to_dict()
        assert "item_number" in d
        assert "text" in d
        assert "objections" in d
        assert d["item_number"] == 1

    def test_to_dict_serialises_objections(self):
        item = DiscoveryItem(
            item_number=1, text="Q",
            objections=[ObjectionType.PRIVILEGE, ObjectionType.COMPOUND],
        )
        d = item.to_dict()
        assert d["objections"] == ["privilege", "compound"]

    def test_is_answered_flag(self):
        item = DiscoveryItem(item_number=1, text="Q", is_answered=True)
        assert item.is_answered is True


class TestDiscoveryRequest:
    """DiscoveryRequest dataclass tests."""

    def test_auto_generated_id(self):
        r = DiscoveryRequest()
        assert len(r.request_id) == 12

    def test_default_parties(self):
        r = DiscoveryRequest()
        assert r.propounding_party == _PLAINTIFF
        assert r.responding_party == _DEFENDANT

    def test_default_status_is_draft(self):
        r = DiscoveryRequest()
        assert r.status == DiscoveryStatus.DRAFT

    def test_to_dict_has_all_keys(self):
        r = DiscoveryRequest(case_number="2024-001507-DC", lane="A")
        d = r.to_dict()
        for key in ("request_id", "discovery_type", "case_number", "lane",
                     "status", "items", "service_method", "created_at"):
            assert key in d, f"Missing key: {key}"

    def test_items_serialised_in_to_dict(self):
        items = [DiscoveryItem(item_number=1, text="Q")]
        r = DiscoveryRequest(items=items)
        d = r.to_dict()
        assert len(d["items"]) == 1
        assert d["items"][0]["item_number"] == 1


class TestPrivilegeLogEntry:
    """PrivilegeLogEntry dataclass tests."""

    def test_defaults(self):
        e = PrivilegeLogEntry()
        assert e.document_description == ""
        assert e.recipients == []
        assert len(e.entry_id) == 10

    def test_to_dict(self):
        e = PrivilegeLogEntry(
            document_description="Memo", author="A. Pigors",
            privilege_type="Attorney-Client",
        )
        d = e.to_dict()
        assert d["document_description"] == "Memo"
        assert d["privilege_type"] == "Attorney-Client"

    def test_recipients_list(self):
        e = PrivilegeLogEntry(recipients=["Alice", "Bob"])
        assert len(e.recipients) == 2


class TestMeetAndConferRecord:
    """MeetAndConferRecord dataclass tests."""

    def test_defaults(self):
        m = MeetAndConferRecord()
        assert m.good_faith_effort is True
        assert m.participants == []

    def test_to_dict(self):
        m = MeetAndConferRecord(date="2025-01-15", method="phone")
        d = m.to_dict()
        assert d["date"] == "2025-01-15"
        assert d["method"] == "phone"

    def test_good_faith_effort_false(self):
        m = MeetAndConferRecord(good_faith_effort=False)
        assert m.good_faith_effort is False


class TestMotionToCompel:
    """MotionToCompel dataclass tests."""

    def test_defaults(self):
        m = MotionToCompel()
        assert m.sanctions_requested is False
        assert m.sanctions_amount == 0.0
        assert m.mcr_authority == "MCR 2.313(A)"

    def test_to_dict_meet_and_confer_none(self):
        m = MotionToCompel()
        d = m.to_dict()
        assert d["meet_and_confer"] is None

    def test_to_dict_meet_and_confer_present(self):
        mc = MeetAndConferRecord(date="2025-01-20", method="email")
        m = MotionToCompel(meet_and_confer=mc)
        d = m.to_dict()
        assert isinstance(d["meet_and_confer"], dict)
        assert d["meet_and_confer"]["date"] == "2025-01-20"


class TestDiscoveryReport:
    """DiscoveryReport dataclass tests."""

    def test_defaults(self):
        r = DiscoveryReport()
        assert r.total_requests == 0
        assert r.overdue_count == 0
        assert r.motions_to_compel == 0

    def test_to_dict(self):
        r = DiscoveryReport(total_requests=5, overdue_count=2)
        d = r.to_dict()
        assert d["total_requests"] == 5

    def test_overdue_requests_list(self):
        r = DiscoveryReport(overdue_requests=["req-1", "req-2"])
        assert len(r.overdue_requests) == 2


class TestDiscoveryCalendar:
    """DiscoveryCalendar: deadline calculation & calendar generation."""

    def test_due_date_interrogatory_mail_service(self):
        """28 days + 3 mail days = 31 days from Monday 2025-01-06."""
        due = DiscoveryCalendar.calculate_due_date(
            "2025-01-06", DiscoveryType.INTERROGATORY, ServiceMethod.MAIL,
        )
        # 2025-01-06 + 31 = 2025-02-06 (Thursday) — no weekend skip needed
        assert due == "2025-02-06"

    def test_due_date_personal_service_no_extra_days(self):
        """Personal service: no +3 days."""
        due = DiscoveryCalendar.calculate_due_date(
            "2025-01-06", DiscoveryType.INTERROGATORY, ServiceMethod.PERSONAL,
        )
        # 2025-01-06 + 28 = 2025-02-03 (Monday)
        assert due == "2025-02-03"

    def test_due_date_weekend_skip(self):
        """When due date lands on Saturday, it should skip to Monday."""
        # 2025-01-03 (Friday) + 28 personal = 2025-01-31 (Friday) — no skip
        # 2025-01-04 (Saturday) + 28 personal = 2025-02-01 (Saturday) → skip to 2025-02-03 (Monday)
        due = DiscoveryCalendar.calculate_due_date(
            "2025-01-04", DiscoveryType.INTERROGATORY, ServiceMethod.PERSONAL,
        )
        assert due == "2025-02-03"  # Monday

    def test_due_date_sunday_skip(self):
        """When due date lands on Sunday, it should skip to Monday."""
        # 2025-01-05 (Sunday) + 28 = 2025-02-02 (Sunday) → 2025-02-03 (Monday)
        due = DiscoveryCalendar.calculate_due_date(
            "2025-01-05", DiscoveryType.INTERROGATORY, ServiceMethod.PERSONAL,
        )
        assert due == "2025-02-03"

    def test_due_date_invalid_date_returns_empty(self):
        assert DiscoveryCalendar.calculate_due_date(
            "not-a-date", DiscoveryType.INTERROGATORY,
        ) == ""

    def test_due_date_none_returns_empty(self):
        assert DiscoveryCalendar.calculate_due_date(
            None, DiscoveryType.INTERROGATORY,  # type: ignore[arg-type]
        ) == ""

    def test_is_overdue_past_date(self):
        yesterday = (date.today() - timedelta(days=1)).isoformat()
        assert DiscoveryCalendar.is_overdue(yesterday) is True

    def test_is_overdue_future_date(self):
        future = (date.today() + timedelta(days=30)).isoformat()
        assert DiscoveryCalendar.is_overdue(future) is False

    def test_is_overdue_invalid_date(self):
        assert DiscoveryCalendar.is_overdue("bad") is False

    def test_days_until_due_positive(self):
        future = (date.today() + timedelta(days=10)).isoformat()
        assert DiscoveryCalendar.days_until_due(future) == 10

    def test_days_until_due_negative(self):
        past = (date.today() - timedelta(days=5)).isoformat()
        assert DiscoveryCalendar.days_until_due(past) == -5

    def test_days_until_due_invalid(self):
        assert DiscoveryCalendar.days_until_due("nope") == 0

    def test_generate_calendar_view_empty(self):
        cal = DiscoveryCalendar()
        assert cal.generate_calendar_view([]) == []

    def test_generate_calendar_view_populated(self):
        future = (date.today() + timedelta(days=5)).isoformat()
        req = DiscoveryRequest(
            date_due=future, status=DiscoveryStatus.SERVED,
            case_number="2024-001507-DC",
        )
        cal = DiscoveryCalendar()
        entries = cal.generate_calendar_view([req])
        assert len(entries) == 1
        assert entries[0]["urgency"] == "urgent"  # <=7 days
        assert entries[0]["days_remaining"] == 5

    def test_generate_calendar_view_urgency_critical(self):
        past = (date.today() - timedelta(days=3)).isoformat()
        req = DiscoveryRequest(date_due=past, status=DiscoveryStatus.OVERDUE)
        cal = DiscoveryCalendar()
        entries = cal.generate_calendar_view([req])
        assert entries[0]["urgency"] == "critical"

    def test_generate_calendar_view_urgency_normal(self):
        far = (date.today() + timedelta(days=30)).isoformat()
        req = DiscoveryRequest(date_due=far, status=DiscoveryStatus.SERVED)
        cal = DiscoveryCalendar()
        entries = cal.generate_calendar_view([req])
        assert entries[0]["urgency"] == "normal"

    def test_generate_calendar_view_sorted_by_days_remaining(self):
        d1 = (date.today() + timedelta(days=20)).isoformat()
        d2 = (date.today() + timedelta(days=3)).isoformat()
        r1 = DiscoveryRequest(request_id="r1", date_due=d1)
        r2 = DiscoveryRequest(request_id="r2", date_due=d2)
        cal = DiscoveryCalendar()
        entries = cal.generate_calendar_view([r1, r2])
        assert entries[0]["request_id"] == "r2"

    def test_get_stats(self):
        cal = DiscoveryCalendar()
        s = cal.get_stats()
        assert s["component"] == "DiscoveryCalendar"
        assert s["response_days_interrogatory"] == 28
        assert s["mail_service_addition"] == _ADDITIONAL_MAIL_SERVICE_DAYS


class TestResponseDrafter:
    """ResponseDrafter: header, item response, privilege log, verification."""

    def test_header_contains_state_of_michigan(self, sample_request):
        rd = ResponseDrafter()
        header = rd.draft_response_header(sample_request)
        assert "STATE OF MICHIGAN" in header

    def test_header_contains_case_number(self, sample_request):
        rd = ResponseDrafter()
        header = rd.draft_response_header(sample_request)
        assert "2024-001507-DC" in header

    def test_header_contains_parties(self, sample_request):
        rd = ResponseDrafter()
        header = rd.draft_response_header(sample_request)
        assert _PLAINTIFF in header
        assert _DEFENDANT in header

    def test_item_response_with_objections(self):
        rd = ResponseDrafter()
        item = DiscoveryItem(item_number=1, text="Describe all events.")
        resp = rd.draft_item_response(
            item, objection_types=[ObjectionType.VAGUE_AND_AMBIGUOUS],
        )
        assert "OBJECTION:" in resp
        assert "vague" in resp.lower()

    def test_item_response_with_answer(self):
        rd = ResponseDrafter()
        item = DiscoveryItem(item_number=2, text="List witnesses.")
        resp = rd.draft_item_response(item, answer="No witnesses at this time.")
        assert "RESPONSE:" in resp
        assert "No witnesses" in resp

    def test_item_response_without_answer_has_placeholder(self):
        rd = ResponseDrafter()
        item = DiscoveryItem(item_number=1, text="Q")
        resp = rd.draft_item_response(item)
        assert "[RESPONSE]" in resp

    def test_privilege_log(self):
        rd = ResponseDrafter()
        entries = [
            PrivilegeLogEntry(
                document_description="Memo to counsel",
                date_of_document="2024-12-01",
                author=_PLAINTIFF,
                recipients=["Attorney"],
                privilege_type="Attorney-Client",
                basis="Confidential communications",
            ),
        ]
        log = rd.draft_privilege_log(entries)
        assert "PRIVILEGE LOG" in log
        assert "MCR 2.302(B)(1)" in log
        assert "Memo to counsel" in log

    def test_verification_contains_party_name(self):
        rd = ResponseDrafter()
        v = rd.draft_verification(_PLAINTIFF)
        assert _PLAINTIFF in v
        assert "VERIFICATION" in v
        assert "penalty of perjury" in v

    def test_get_stats(self):
        rd = ResponseDrafter()
        s = rd.get_stats()
        assert s["component"] == "ResponseDrafter"
        assert s["objection_types"] == 10
        assert s["service_methods"] == 5


class TestMotionToCompelGenerator:
    """MotionToCompelGenerator: prepare, render, sanctions."""

    def test_prepare_motion_basic(self, sample_request):
        gen = MotionToCompelGenerator()
        motion = gen.prepare_motion([sample_request])
        assert isinstance(motion, MotionToCompel)
        assert sample_request.request_id in motion.discovery_request_ids

    def test_prepare_motion_with_sanctions(self, sample_request):
        gen = MotionToCompelGenerator()
        motion = gen.prepare_motion(
            [sample_request], request_sanctions=True,
        )
        assert motion.sanctions_requested is True
        assert "MCR 2.313(B)(2)" in motion.sanctions_basis

    def test_render_motion_text_has_mcr_2313(self, sample_request):
        gen = MotionToCompelGenerator()
        motion = gen.prepare_motion([sample_request])
        text = gen.render_motion_text(motion)
        assert "MCR 2.313" in text
        assert "MOTION TO COMPEL" in text

    def test_render_motion_text_has_meet_and_confer_section(self, sample_request):
        gen = MotionToCompelGenerator()
        mc = MeetAndConferRecord(
            date="2025-01-20", method="telephone",
            outcome="No resolution",
        )
        motion = gen.prepare_motion([sample_request], meet_confer=mc)
        text = gen.render_motion_text(motion)
        assert "MEET AND CONFER" in text
        assert "telephone" in text

    def test_calculate_sanctions(self):
        gen = MotionToCompelGenerator()
        s = gen.calculate_sanctions(
            filing_fee=20.0, copy_costs=15.50, hours_spent=3.0,
        )
        assert s["filing_fee"] == 20.0
        assert s["copy_costs"] == 15.50
        assert s["hours_spent"] == 3.0
        assert s["total_requested"] == 35.50
        assert s["mcr_authority"] == "MCR 2.313(B)(2)"

    def test_get_stats(self):
        gen = MotionToCompelGenerator()
        s = gen.get_stats()
        assert s["component"] == "MotionToCompelGenerator"
        assert s["mcr_authority"] == "MCR 2.313"


class TestDiscoveryManager:
    """DiscoveryManager orchestrator tests."""

    def test_init(self, dm: DiscoveryManager):
        stats = dm.get_stats()
        assert stats["module"] == "discovery_manager"
        assert stats["requests_loaded"] == 0

    def test_create_request_with_date_served_sets_due_date(
        self, dm: DiscoveryManager,
    ):
        req = dm.create_request(
            DiscoveryType.INTERROGATORY,
            case_number="2024-001507-DC",
            lane="A",
            date_served="2025-01-06",
        )
        assert req.status == DiscoveryStatus.SERVED
        assert req.date_due != ""  # calculated

    def test_create_request_no_date_stays_draft(self, dm: DiscoveryManager):
        req = dm.create_request(
            DiscoveryType.REQUEST_PRODUCTION,
            case_number="2024-001507-DC",
            lane="A",
        )
        assert req.status == DiscoveryStatus.DRAFT
        assert req.date_due == ""

    def test_add_request(self, dm: DiscoveryManager, sample_request):
        dm.add_request(sample_request)
        assert dm.get_stats()["requests_loaded"] == 1

    def test_get_request_found(self, dm: DiscoveryManager, sample_request):
        dm.add_request(sample_request)
        found = dm.get_request(sample_request.request_id)
        assert found is not None
        assert found.request_id == sample_request.request_id

    def test_get_request_not_found(self, dm: DiscoveryManager):
        assert dm.get_request("nonexistent") is None

    def test_track_response_valid(self, dm: DiscoveryManager, sample_items):
        req = dm.create_request(
            DiscoveryType.INTERROGATORY,
            case_number="2024-001507-DC", lane="A",
            items=sample_items, date_served="2025-01-06",
        )
        ok = dm.track_response(req.request_id, 1, "Answer to item 1.")
        assert ok is True
        item = req.items[0]
        assert item.is_answered is True
        assert item.response == "Answer to item 1."

    def test_track_response_invalid_request(self, dm: DiscoveryManager):
        assert dm.track_response("bad-id", 1, "x") is False

    def test_track_response_invalid_item(self, dm: DiscoveryManager, sample_items):
        req = dm.create_request(
            DiscoveryType.INTERROGATORY,
            case_number="2024-001507-DC", lane="A",
            items=sample_items,
        )
        assert dm.track_response(req.request_id, 999, "x") is False

    def test_track_response_all_answered_sets_responded(
        self, dm: DiscoveryManager,
    ):
        items = [DiscoveryItem(item_number=1, text="Q")]
        req = dm.create_request(
            DiscoveryType.INTERROGATORY,
            case_number="2024-001507-DC", lane="A",
            items=items, date_served="2025-01-06",
        )
        dm.track_response(req.request_id, 1, "A")
        assert req.status == DiscoveryStatus.RESPONDED

    def test_update_status(self, dm: DiscoveryManager, sample_request):
        dm.add_request(sample_request)
        ok = dm.update_status(
            sample_request.request_id, DiscoveryStatus.COMPLETED,
        )
        assert ok is True
        assert sample_request.status == DiscoveryStatus.COMPLETED

    def test_update_status_invalid_id(self, dm: DiscoveryManager):
        assert dm.update_status("x", DiscoveryStatus.COMPLETED) is False

    def test_get_overdue(self, dm: DiscoveryManager):
        past = (date.today() - timedelta(days=10)).isoformat()
        req = DiscoveryRequest(
            request_id="overdue-1",
            status=DiscoveryStatus.SERVED,
            date_due=past,
        )
        dm.add_request(req)
        overdue = dm.get_overdue()
        assert len(overdue) >= 1
        assert overdue[0].status == DiscoveryStatus.OVERDUE

    def test_generate_discovery_report(self, dm: DiscoveryManager):
        dm.create_request(
            DiscoveryType.INTERROGATORY,
            case_number="2024-001507-DC", lane="A",
        )
        report = dm.generate_discovery_report()
        assert isinstance(report, DiscoveryReport)
        assert report.total_requests == 1

    def test_to_markdown(self, dm: DiscoveryManager):
        dm.create_request(
            DiscoveryType.INTERROGATORY,
            case_number="2024-001507-DC", lane="A",
        )
        md = dm.to_markdown()
        assert "## Discovery Status Report" in md

    def test_get_stats_has_sub_components(self, dm: DiscoveryManager):
        s = dm.get_stats()
        assert "calendar" in s
        assert "drafter" in s
        assert "mtc_generator" in s

    def test_reset(self, dm: DiscoveryManager):
        dm.create_request(
            DiscoveryType.INTERROGATORY,
            case_number="2024-001507-DC", lane="A",
        )
        assert dm.get_stats()["requests_loaded"] == 1
        dm.reset()
        assert dm.get_stats()["requests_loaded"] == 0


class TestDiscoveryConstants:
    """Module-level constants validation."""

    def test_plaintiff(self):
        assert _PLAINTIFF == "Andrew James Pigors"

    def test_defendant(self):
        assert _DEFENDANT == "Emily A. Watson"

    def test_child_initials(self):
        assert _CHILD_INITIALS == "L.D.W."

    def test_judge(self):
        assert _JUDGE == "Hon. Jenny L. McNeill"

    def test_lane_cases_keys(self):
        assert set(LANE_CASES.keys()) == {"A", "B", "C", "D", "E", "F"}

    def test_lane_a_case_number(self):
        assert LANE_CASES["A"] == "2024-001507-DC"


# ═══════════════════════════════════════════════════════════════════════════
#  PART 2 — hearing_preparation.py  (~60 tests)
# ═══════════════════════════════════════════════════════════════════════════


class TestHearingType:
    """HearingType enum: values, mcr_reference, typical_duration_minutes."""

    def test_all_eight_values(self):
        names = {m.name for m in HearingType}
        expected = {
            "MOTION", "EVIDENTIARY", "STATUS", "PRETRIAL",
            "TRIAL", "SHOW_CAUSE", "EMERGENCY", "SETTLEMENT",
        }
        assert names == expected

    def test_mcr_reference_motion(self):
        assert HearingType.MOTION.mcr_reference == "MCR 2.119(E)"

    def test_mcr_reference_trial(self):
        assert HearingType.TRIAL.mcr_reference == "MCR 2.501"

    def test_mcr_reference_emergency(self):
        assert HearingType.EMERGENCY.mcr_reference == "MCR 2.119(F)"

    def test_duration_motion(self):
        assert HearingType.MOTION.typical_duration_minutes == 30

    def test_duration_trial(self):
        assert HearingType.TRIAL.typical_duration_minutes == 480

    def test_duration_status(self):
        assert HearingType.STATUS.typical_duration_minutes == 15


class TestHearingStatus:
    """HearingStatus enum validation."""

    def test_all_six_values(self):
        names = {m.name for m in HearingStatus}
        expected = {
            "SCHEDULED", "PREPARED", "IN_PROGRESS",
            "COMPLETED", "CONTINUED", "ADJOURNED",
        }
        assert names == expected

    def test_is_str_enum(self):
        assert isinstance(HearingStatus.SCHEDULED, str)


class TestArgumentStrength:
    """ArgumentStrength enum validation."""

    def test_all_four_values(self):
        names = {m.name for m in ArgumentStrength}
        assert names == {"STRONG", "MODERATE", "WEAK", "SPECULATIVE"}

    def test_string_values(self):
        assert ArgumentStrength.STRONG.value == "strong"
        assert ArgumentStrength.SPECULATIVE.value == "speculative"


class TestExhibitStatus:
    """ExhibitStatus enum validation."""

    def test_all_six_values(self):
        names = {m.name for m in ExhibitStatus}
        expected = {
            "PROPOSED", "MARKED", "ADMITTED",
            "OBJECTED", "EXCLUDED", "WITHDRAWN",
        }
        assert names == expected

    def test_default_is_proposed(self):
        e = HearingExhibit()
        assert e.status == ExhibitStatus.PROPOSED


class TestWitnessEntry:
    """WitnessEntry dataclass tests."""

    def test_defaults(self):
        w = WitnessEntry()
        assert w.name == ""
        assert w.estimated_duration_minutes == 15
        assert w.subpoena_needed is False
        assert w.is_hostile is False

    def test_to_dict(self):
        w = WitnessEntry(name="Dr. Smith", role="Expert")
        d = w.to_dict()
        assert d["name"] == "Dr. Smith"
        assert "testimony_topics" in d

    def test_subpoena_fields(self):
        w = WitnessEntry(subpoena_needed=True, subpoena_served=True)
        assert w.subpoena_needed is True
        assert w.subpoena_served is True


class TestHearingExhibit:
    """HearingExhibit dataclass tests."""

    def test_defaults(self):
        e = HearingExhibit()
        assert e.exhibit_number == ""
        assert e.copies_prepared == 3
        assert e.foundation_ready is False
        assert e.status == ExhibitStatus.PROPOSED

    def test_to_dict_serialises_status(self):
        e = HearingExhibit(exhibit_number="P-1", status=ExhibitStatus.ADMITTED)
        d = e.to_dict()
        assert d["status"] == "admitted"

    def test_foundation_ready_flag(self):
        e = HearingExhibit(foundation_ready=True)
        assert e.foundation_ready is True


class TestLegalArgument:
    """LegalArgument dataclass tests."""

    def test_defaults(self):
        a = LegalArgument()
        assert a.issue == ""
        assert a.strength == ArgumentStrength.MODERATE
        assert a.legal_basis == []
        assert a.case_law == []

    def test_to_dict_serialises_strength(self):
        a = LegalArgument(
            issue="Custody", strength=ArgumentStrength.STRONG,
        )
        d = a.to_dict()
        assert d["strength"] == "strong"

    def test_case_law_list(self):
        a = LegalArgument(case_law=["Vodvarka v Grasmeyer", "Shade v Wright"])
        assert len(a.case_law) == 2


class TestHearingRecord:
    """HearingRecord dataclass tests."""

    def test_defaults(self):
        h = HearingRecord()
        assert h.hearing_type == HearingType.MOTION
        assert h.status == HearingStatus.SCHEDULED
        assert h.court == _COURT
        assert h.judge == "Hon. Jenny L. McNeill"

    def test_to_dict_serialises_nested(self):
        w = WitnessEntry(name="Alice")
        h = HearingRecord(witnesses=[w], issues=["Test"])
        d = h.to_dict()
        assert isinstance(d["witnesses"], list)
        assert d["witnesses"][0]["name"] == "Alice"
        assert d["status"] == "scheduled"

    def test_location_default(self):
        h = HearingRecord()
        assert h.location == _COURT_ADDRESS


class TestHearingChecklist:
    """HearingChecklist dataclass tests."""

    def test_defaults(self):
        c = HearingChecklist()
        assert c.items == []
        assert c.completion_pct == 0.0

    def test_completion_pct_set(self):
        c = HearingChecklist(completion_pct=75.0)
        assert c.completion_pct == 75.0


class TestHearingPlanner:
    """HearingPlanner: outline, witnesses, exhibits, duration, order."""

    def test_outline_has_sections(self, sample_hearing):
        planner = HearingPlanner()
        outline = planner.prepare_hearing_outline(sample_hearing)
        assert "sections" in outline
        assert len(outline["sections"]) >= 2  # at least 2 issue sections

    def test_outline_trial_adds_opening(self, trial_hearing):
        planner = HearingPlanner()
        outline = planner.prepare_hearing_outline(trial_hearing)
        titles = [s["title"] for s in outline["sections"]]
        assert "Opening Statement" in titles

    def test_outline_trial_adds_closing(self, trial_hearing):
        planner = HearingPlanner()
        outline = planner.prepare_hearing_outline(trial_hearing)
        titles = [s["title"] for s in outline["sections"]]
        assert "Closing Argument" in titles

    def test_outline_motion_no_opening(self, sample_hearing):
        planner = HearingPlanner()
        outline = planner.prepare_hearing_outline(sample_hearing)
        titles = [s["title"] for s in outline["sections"]]
        assert "Opening Statement" not in titles

    def test_identify_required_exhibits_with_matches(self, trial_hearing):
        planner = HearingPlanner()
        required = planner.identify_required_exhibits(trial_hearing)
        assert "P-1" in required
        assert "P-2" in required

    def test_identify_required_exhibits_missing(self):
        planner = HearingPlanner()
        h = HearingRecord(issues=["Novel issue with no exhibit"])
        required = planner.identify_required_exhibits(h)
        assert any("MISSING EXHIBIT" in r for r in required)

    def test_witness_list_has_table_header(self, trial_hearing):
        planner = HearingPlanner()
        wl = planner.prepare_witness_list(trial_hearing)
        assert "WITNESS LIST" in wl
        assert "| # |" in wl
        assert "Dr. Smith" in wl

    def test_estimate_duration(self, trial_hearing):
        planner = HearingPlanner()
        dur = planner.estimate_duration(trial_hearing)
        # base=480, witness_time=30+20=50, issue_time=2*15=30, 50+30+20=100
        # max(480, 100) = 480
        assert dur == 480

    def test_estimate_duration_many_witnesses(self):
        planner = HearingPlanner()
        witnesses = [
            WitnessEntry(estimated_duration_minutes=60)
            for _ in range(10)
        ]
        h = HearingRecord(
            hearing_type=HearingType.MOTION,
            issues=["A", "B"],
            witnesses=witnesses,
        )
        dur = planner.estimate_duration(h)
        # base=30, witness_time=600, issue_time=30, 600+30+20=650
        # max(30, 650) = 650
        assert dur == 650

    def test_proposed_order_contains_judge(self, sample_hearing):
        planner = HearingPlanner()
        order = planner.prepare_proposed_order(sample_hearing)
        assert "Hon. Jenny L. McNeill" in order
        assert "STATE OF MICHIGAN" in order
        assert "ORDER" in order

    def test_get_stats(self):
        planner = HearingPlanner()
        s = planner.get_stats()
        assert s["component"] == "HearingPlanner"
        assert s["checklist_items"] >= 10
        assert s["hearing_types"] == 8


class TestArgumentBuilder:
    """ArgumentBuilder: argument construction, strength scoring, statements."""

    def test_build_legal_argument_basic(self):
        ab = ArgumentBuilder()
        arg = ab.build_legal_argument(
            issue="Custody",
            position="Father should have custody",
            legal_basis=["MCL 722.23"],
        )
        assert isinstance(arg, LegalArgument)
        assert arg.issue == "Custody"

    def test_strength_strong(self):
        """Score >= 6 → STRONG (3 basis + 3 facts + 2 case_law = 8)."""
        ab = ArgumentBuilder()
        arg = ab.build_legal_argument(
            issue="X", position="P",
            legal_basis=["a", "b", "c"],
            supporting_facts=["f1", "f2", "f3"],
            case_law=["CL1", "CL2"],
        )
        assert arg.strength == ArgumentStrength.STRONG

    def test_strength_moderate(self):
        """Score >= 3 but < 6 → MODERATE (2 basis + 1 fact = 3)."""
        ab = ArgumentBuilder()
        arg = ab.build_legal_argument(
            issue="X", position="P",
            legal_basis=["a", "b"],
            supporting_facts=["f1"],
        )
        assert arg.strength == ArgumentStrength.MODERATE

    def test_strength_weak(self):
        """Score >= 1 but < 3 → WEAK (1 basis only = 1)."""
        ab = ArgumentBuilder()
        arg = ab.build_legal_argument(
            issue="X", position="P",
            legal_basis=["a"],
        )
        assert arg.strength == ArgumentStrength.WEAK

    def test_strength_speculative(self):
        """Score 0 → SPECULATIVE (no basis, facts, or case law)."""
        ab = ArgumentBuilder()
        arg = ab.build_legal_argument(issue="X", position="P")
        assert arg.strength == ArgumentStrength.SPECULATIVE

    def test_strength_caps_at_max(self):
        """Extra items beyond cap don't increase score beyond 3+3+2=8."""
        ab = ArgumentBuilder()
        arg = ab.build_legal_argument(
            issue="X", position="P",
            legal_basis=["a", "b", "c", "d", "e"],  # capped at 3
            supporting_facts=["f"] * 10,  # capped at 3
            case_law=["c"] * 5,  # capped at 2
        )
        assert arg.strength == ArgumentStrength.STRONG

    def test_opening_statement_has_plaintiff(self, sample_hearing):
        ab = ArgumentBuilder()
        stmt = ab.prepare_opening_statement(sample_hearing)
        assert HP_PLAINTIFF in stmt
        assert "pro se" in stmt.lower()

    def test_opening_statement_with_key_points(self, sample_hearing):
        ab = ArgumentBuilder()
        stmt = ab.prepare_opening_statement(
            sample_hearing, key_points=["Point A", "Point B"],
        )
        assert "Point A" in stmt
        assert "The evidence will show" in stmt

    def test_closing_argument(self, sample_hearing):
        ab = ArgumentBuilder()
        arg = LegalArgument(
            issue="Custody",
            position="Father should have custody",
            legal_basis=["MCL 722.23"],
        )
        closing = ab.prepare_closing_argument(sample_hearing, [arg])
        assert "evidence presented today" in closing
        assert "Custody" in closing

    def test_anticipate_returns_three_patterns(self):
        ab = ArgumentBuilder()
        patterns = ab.anticipate_opposing_arguments(
            issue="Custody", our_position="Modification warranted",
        )
        assert len(patterns) == 3
        for p in patterns:
            assert "opposition" in p
            assert "rebuttal" in p

    def test_anticipate_mentions_plaintiff(self):
        ab = ArgumentBuilder()
        patterns = ab.anticipate_opposing_arguments("Test", "Pos")
        combined = " ".join(p["rebuttal"] for p in patterns)
        assert HP_PLAINTIFF in combined

    def test_prepare_rebuttal_with_evidence(self):
        ab = ArgumentBuilder()
        rebuttal = ab.prepare_rebuttal(
            "claims are unsupported",
            evidence_refs=["Exhibit P-1", "Exhibit P-2"],
        )
        assert "Exhibit P-1" in rebuttal
        assert "contradicts" in rebuttal

    def test_best_interest_factors_has_12_keys(self):
        ab = ArgumentBuilder()
        assert len(ab._BEST_INTEREST_FACTORS) == 12
        assert "a" in ab._BEST_INTEREST_FACTORS
        assert "l" in ab._BEST_INTEREST_FACTORS

    def test_get_stats(self):
        ab = ArgumentBuilder()
        s = ab.get_stats()
        assert s["component"] == "ArgumentBuilder"
        assert s["best_interest_factors"] == 12
        assert s["argument_strengths"] == 4


class TestExhibitOrganizer:
    """ExhibitOrganizer: grouping, listing, binder, admission."""

    def test_organize_by_issue_groups(self):
        eo = ExhibitOrganizer()
        ex1 = HearingExhibit(
            exhibit_number="P-1", title="Email",
            related_issues=["Custody"],
        )
        ex2 = HearingExhibit(
            exhibit_number="P-2", title="Records",
            related_issues=["Custody", "Support"],
        )
        grouped = eo.organize_by_issue([ex1, ex2])
        assert "Custody" in grouped
        assert len(grouped["Custody"]) == 2
        assert "Support" in grouped
        assert len(grouped["Support"]) == 1

    def test_organize_by_issue_unassigned(self):
        eo = ExhibitOrganizer()
        ex = HearingExhibit(exhibit_number="P-3", title="Misc")
        grouped = eo.organize_by_issue([ex])
        assert "unassigned" in grouped
        assert len(grouped["unassigned"]) == 1

    def test_create_exhibit_list(self):
        eo = ExhibitOrganizer()
        ex = HearingExhibit(
            exhibit_number="P-1", title="Email Thread",
            status=ExhibitStatus.PROPOSED,
        )
        text = eo.create_exhibit_list([ex], "2024-001507-DC")
        assert "EXHIBIT LIST" in text
        assert "P-1" in text
        assert "Email Thread" in text

    def test_prepare_exhibit_binder_tabs(self):
        eo = ExhibitOrganizer()
        exhibits = [
            HearingExhibit(
                exhibit_number="P-1", title="Doc A",
                copies_prepared=3, foundation_ready=True,
            ),
            HearingExhibit(
                exhibit_number="P-2", title="Doc B",
                copies_prepared=3, foundation_ready=False,
            ),
        ]
        binder = eo.prepare_exhibit_binder(exhibits)
        assert binder["total_exhibits"] == 2
        assert len(binder["tabs"]) == 2
        assert binder["tabs"][0]["tab_number"] == 1
        assert binder["tabs"][0]["exhibit_number"] == "P-1"
        assert binder["tabs"][1]["foundation_ready"] is False

    def test_mark_for_admission(self):
        eo = ExhibitOrganizer()
        ex = HearingExhibit(exhibit_number="P-1")
        assert ex.status == ExhibitStatus.PROPOSED
        result = eo.mark_for_admission(ex, ExhibitStatus.ADMITTED)
        assert result.status == ExhibitStatus.ADMITTED
        assert result is ex  # mutates in place

    def test_get_stats(self):
        eo = ExhibitOrganizer()
        s = eo.get_stats()
        assert s["component"] == "ExhibitOrganizer"
        assert s["exhibit_statuses"] == 6


class TestHearingPreparation:
    """HearingPreparation orchestrator tests."""

    def test_init(self, hp: HearingPreparation):
        s = hp.get_stats()
        assert s["module"] == "hearing_preparation"
        assert s["hearings_loaded"] == 0

    def test_create_hearing(self, hp: HearingPreparation):
        h = hp.create_hearing(
            HearingType.MOTION,
            case_number="2024-001507-DC", lane="A",
            hearing_date="2025-03-15", hearing_time="09:00",
            issues=["Custody modification"],
        )
        assert isinstance(h, HearingRecord)
        assert h.status == HearingStatus.SCHEDULED
        assert h.case_number == "2024-001507-DC"

    def test_add_hearing(self, hp: HearingPreparation, sample_hearing):
        hp.add_hearing(sample_hearing)
        assert hp.get_stats()["hearings_loaded"] == 1

    def test_get_hearing_found(self, hp: HearingPreparation, sample_hearing):
        hp.add_hearing(sample_hearing)
        found = hp.get_hearing(sample_hearing.hearing_id)
        assert found is not None
        assert found.hearing_id == sample_hearing.hearing_id

    def test_get_hearing_not_found(self, hp: HearingPreparation):
        assert hp.get_hearing("nonexistent") is None

    def test_prepare_full_hearing_has_outline(
        self, hp: HearingPreparation, sample_hearing,
    ):
        hp.add_hearing(sample_hearing)
        result = hp.prepare_full_hearing(sample_hearing)
        assert "outline" in result
        assert "duration_estimate" in result
        assert "witness_list" in result
        assert "proposed_order" in result

    def test_prepare_full_hearing_sets_prepared_status(
        self, hp: HearingPreparation, sample_hearing,
    ):
        hp.add_hearing(sample_hearing)
        hp.prepare_full_hearing(sample_hearing)
        assert sample_hearing.status == HearingStatus.PREPARED

    def test_prepare_full_hearing_trial_has_opening(
        self, hp: HearingPreparation, trial_hearing,
    ):
        hp.add_hearing(trial_hearing)
        result = hp.prepare_full_hearing(
            trial_hearing, key_points=["Key point 1"],
        )
        assert "opening_statement" in result
        assert "exhibit_list" in result
        assert "exhibit_binder" in result

    def test_generate_hearing_checklist(
        self, hp: HearingPreparation, trial_hearing,
    ):
        hp.add_hearing(trial_hearing)
        checklist = hp.generate_hearing_checklist(trial_hearing)
        assert isinstance(checklist, HearingChecklist)
        assert len(checklist.items) >= 12  # standard + witness/exhibit items
        # Dr. Smith needs subpoena but not served → completion_pct < 100
        assert checklist.completion_pct < 100

    def test_generate_hearing_checklist_subpoena_item(
        self, hp: HearingPreparation, trial_hearing,
    ):
        hp.add_hearing(trial_hearing)
        checklist = hp.generate_hearing_checklist(trial_hearing)
        subpoena_items = [
            i for i in checklist.items
            if "subpoena" in i["item"].lower()
        ]
        assert len(subpoena_items) >= 1
        assert "Dr. Smith" in subpoena_items[0]["item"]

    def test_generate_hearing_checklist_foundation_item(
        self, hp: HearingPreparation, trial_hearing,
    ):
        hp.add_hearing(trial_hearing)
        checklist = hp.generate_hearing_checklist(trial_hearing)
        foundation_items = [
            i for i in checklist.items
            if "foundation" in i["item"].lower() and "P-2" in i["item"]
        ]
        assert len(foundation_items) >= 1

    def test_get_stats_with_hearings(
        self, hp: HearingPreparation, trial_hearing,
    ):
        hp.add_hearing(trial_hearing)
        s = hp.get_stats()
        assert s["hearings_loaded"] == 1
        assert s["total_witnesses"] == 2
        assert s["total_exhibits"] == 2
        assert "planner" in s
        assert "argument_builder" in s

    def test_reset(self, hp: HearingPreparation, sample_hearing):
        hp.add_hearing(sample_hearing)
        assert hp.get_stats()["hearings_loaded"] == 1
        hp.reset()
        assert hp.get_stats()["hearings_loaded"] == 0


class TestHearingConstants:
    """Hearing module constants validation."""

    def test_plaintiff_matches_discovery(self):
        assert HP_PLAINTIFF == "Andrew James Pigors"

    def test_court(self):
        assert _COURT == "14th Circuit Court"

    def test_court_address(self):
        assert "Muskegon" in _COURT_ADDRESS
        assert "990 Terrace" in _COURT_ADDRESS

    def test_lane_cases_same_as_discovery(self):
        assert HP_LANE_CASES == LANE_CASES
