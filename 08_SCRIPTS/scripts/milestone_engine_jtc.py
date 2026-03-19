"""
JTC Milestone Engine

Purpose:
- Provide a typed timeline (intake → screening → investigation → disposition milestones).
- Align MEEK4 packaging with publicly described process semantics by ensuring:
  - milestone correctness (sequence + labels)
  - notice ingestion (letters/notices as TriggerEvents)
  - response windows (notably the "28-day letter" under MCR 9.222)
- Emit RiskEvents when milestones or responses are missing, late, or mis-sequenced.

Note:
This engine is designed to work from the complainant's perspective (MEEK4 packaging).
Certain internal JTC steps are not observable; the engine models them as "expected milestones"
and marks confidence lower unless anchored to a notice/letter.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple
from datetime import datetime, timedelta, timezone

from .models import (
    AuthorityRef, TriggerEvent, Clock, RiskEvent,
    CureCost, CureOption, PacketItem, PacketSpec,
    deterministic_id, utc_now
)
from .gates import DEFAULT_PROFILES, GateDecision


@dataclass
class MatterContext:
    matter_id: str
    lane: str = "MEEK4"
    # optional: treat a "request for info" as requiring response by complainant
    complainant_response_required: bool = True


def _parse_iso(s: str) -> datetime:
    return datetime.fromisoformat(s.replace("Z", "+00:00")).astimezone(timezone.utc)


def _clock_expired(clock: Clock, now: Optional[datetime] = None) -> bool:
    now = now or utc_now()
    try:
        return _parse_iso(clock.due_at) < now
    except Exception:
        return False


def _has_trigger(triggers: List[TriggerEvent], event_type: str) -> bool:
    return any(t.event_type == event_type for t in triggers)


class JTCMilestoneEngine:
    def __init__(self) -> None:
        self.profile = DEFAULT_PROFILES["JTC"]

        # typed milestone ordering for packaging alignment
        self.milestones = [
            "JTC_INTAKE_RECEIVED",
            "JTC_SCREENING_PRELIMINARY_REVIEW",
            "JTC_ADDITIONAL_INVESTIGATION",
            "JTC_28_DAY_LETTER_SENT",
            "JTC_RESPONSE_RECEIVED",
            "JTC_DISPOSITION_ISSUED",
            "JTC_FORMAL_COMPLAINT_FILED",
            "JTC_PUBLIC_HEARING",
            "JTC_MASTER_REPORT",
            "JTC_SUPREME_COURT_REVIEW",
            "JTC_FINAL_DISPOSITION",
        ]

    def run(self, ctx: MatterContext, triggers: List[TriggerEvent]) -> Tuple[List[Clock], List[RiskEvent], Dict[str, GateDecision], Dict[str, object]]:
        clocks: List[Clock] = []
        risks: List[RiskEvent] = []
        decisions: Dict[str, GateDecision] = {}

        # Build a typed timeline view (for downstream packaging)
        timeline: List[Dict[str, object]] = []
        for t in sorted([x for x in triggers if x.forum_profile == "JTC"], key=lambda x: x.occurred_at):
            timeline.append({"event_type": t.event_type, "occurred_at": t.occurred_at, "recordref": t.source_record_ref_id})

        # Core observable milestones: request for info; 28-day letter; disposition.
        for t in triggers:
            if t.forum_profile != "JTC":
                continue

            occurred = _parse_iso(t.occurred_at)
            sig = t.extracted_signals or {}
            days = sig.get("days_mentioned")

            if t.event_type == "JTC_28_DAY_LETTER_SENT":
                # MCR 9.222: 28-day letter (judge response to JTC; but for packaging we model it as an anchored milestone).
                due = occurred + timedelta(days=28)
                clk = Clock.make(
                    matter_id=ctx.matter_id,
                    forum_profile="JTC",
                    clock_kind="response_window",
                    opens_at=occurred,
                    due_at=due,
                    basis="MCR 9.222 28-day letter response window (modeled milestone).",
                    tolling_notes="This is a process milestone; complainant may not control respondent response. Use for alignment + follow-up tracking.",
                )
                clocks.append(clk)

                # If complainant has outstanding requests for info, treat as curable defect; otherwise low severity milestone marker.
                risk = RiskEvent.make(
                    matter_id=ctx.matter_id,
                    forum_profile="JTC",
                    risk_class="record_incomplete",
                    kill_mechanism="stall",
                    trigger_event_id=t.id,
                    clock_id=clk.id,
                    description="JTC 28-day letter milestone logged. Ensure your MEEK4 package is synchronized to this milestone; if you have requested/available evidence, ensure it is packaged and ready for any follow-up request.",
                    authority_refs=[AuthorityRef(ref="MCR 9.222", pinpoint="28-day letter", url=None)],
                    clerk_letter_refs=[t.source_record_ref_id or "UNKNOWN_RECORDREF"],
                    confidence=0.9,
                )
                risk.compute_severity()

                cure = CureOption(
                    id=deterministic_id("cure", risk.id, "refresh_evidence_packet"),
                    summary="Refresh/complete the evidence packet and milestone narrative so it aligns with current JTC process stage.",
                    cure_cost=CureCost(time_band="days", fee_band="none", complexity="medium", dependencies=["assemble exhibits + narrative", "verify dates"]),
                    cure_deadline_clock_id=clk.id,
                    cure_minimum_packet=PacketSpec(items=[
                        PacketItem(item_type="pleading", required=True, notes="JTC complaint narrative with chronological allegations and pinpointed supporting records.", authority_basis="JTC process alignment / MCR 9.200+"),
                        PacketItem(item_type="appendix", required=True, notes="Exhibit list + copies or record pointers.", authority_basis="best practice"),
                    ]),
                )
                risk.cure_options = [cure]
                risk.rank_cures()

                decisions[risk.id] = self.profile.decide(risk.risk_class, cure_window_expired=_clock_expired(clk), jurisdictional=False)
                risks.append(risk)

            if t.event_type == "JTC_REQUEST_FOR_INFO_SENT" and ctx.complainant_response_required:
                # If notice includes a days window, use it; else treat as prompt response required (due_at = occurred).
                if not isinstance(days, int):
                    days = 0
                due = occurred + timedelta(days=max(0, days))
                clk = Clock.make(
                    matter_id=ctx.matter_id,
                    forum_profile="JTC",
                    clock_kind="response_window",
                    opens_at=occurred,
                    due_at=due,
                    basis="JTC request for additional information (notice-derived response window).",
                    tolling_notes="Use notice-specified response window; if absent, treat as immediate follow-up requested.",
                )
                clocks.append(clk)

                risk = RiskEvent.make(
                    matter_id=ctx.matter_id,
                    forum_profile="JTC",
                    risk_class="curable_defect",
                    kill_mechanism="stall",
                    trigger_event_id=t.id,
                    clock_id=clk.id,
                    description="JTC requested additional information. Fastest cure is to provide the requested facts/records in a conforming, indexed packet aligned to the JTC milestone stage.",
                    authority_refs=[AuthorityRef(ref="JTC process", pinpoint="additional investigation / information requests", url=None)],
                    clerk_letter_refs=[t.source_record_ref_id or "UNKNOWN_RECORDREF"],
                    confidence=0.85,
                )
                risk.compute_severity()

                cure = CureOption(
                    id=deterministic_id("cure", risk.id, "respond_to_info_request"),
                    summary="Respond to JTC’s request with an indexed packet: requested facts + attached record pointers/exhibits.",
                    cure_cost=CureCost(time_band="days", fee_band="none", complexity="medium", dependencies=["locate requested records"]),
                    cure_deadline_clock_id=clk.id,
                    cure_minimum_packet=PacketSpec(items=[
                        PacketItem(item_type="pleading", required=True, notes="Response letter/memo addressing each requested item point-by-point.", authority_basis="notice"),
                        PacketItem(item_type="appendix", required=True, notes="Exhibits/record pointers supporting the response.", authority_basis="best practice"),
                    ]),
                )
                risk.cure_options = [cure]
                risk.rank_cures()

                decisions[risk.id] = self.profile.decide(risk.risk_class, cure_window_expired=_clock_expired(clk), jurisdictional=False)
                risks.append(risk)

        # Milestone mismatch / packaging alignment risk:
        # If we have a disposition trigger without earlier obvious steps, flag low-confidence misalignment risk (for packaging clarity).
        if _has_trigger(triggers, "JTC_DISPOSITION_ISSUED") and not (_has_trigger(triggers, "JTC_28_DAY_LETTER_SENT") or _has_trigger(triggers, "JTC_REQUEST_FOR_INFO_SENT")):
            now = utc_now()
            clk = Clock.make(
                matter_id=ctx.matter_id,
                forum_profile="JTC",
                clock_kind="due_date",
                opens_at=now,
                due_at=now,
                basis="Packaging alignment check (disposition present without prior notice milestones in record).",
                tolling_notes="This is not a legal deadline; it is an internal integrity check for your package.",
            )
            clocks.append(clk)
            risk = RiskEvent.make(
                matter_id=ctx.matter_id,
                forum_profile="JTC",
                risk_class="record_incomplete",
                kill_mechanism="stall",
                trigger_event_id=None,
                clock_id=clk.id,
                description="Disposition is recorded, but prior milestone notices are missing from the record set. Add any letters/notices to align the timeline and preserve provenance.",
                authority_refs=[AuthorityRef(ref="JTC process", pinpoint="public process milestones", url=None)],
                confidence=0.6,
            )
            risk.compute_severity()
            risk.cure_options = [
                CureOption(
                    id=deterministic_id("cure", risk.id, "attach_missing_notices"),
                    summary="Locate and attach missing JTC notices/letters and ingest them as TriggerEvents.",
                    cure_cost=CureCost(time_band="days", fee_band="none", complexity="low", dependencies=["find letters/notices"]),
                    cure_deadline_clock_id=clk.id,
                    cure_minimum_packet=PacketSpec(items=[
                        PacketItem(item_type="record_component", required=True, notes="JTC notices/letters (PDF/email) added as RecordRefs and ingested.", authority_basis="provenance"),
                    ]),
                )
            ]
            risk.rank_cures()
            decisions[risk.id] = self.profile.decide(risk.risk_class, cure_window_expired=False, jurisdictional=False)
            risks.append(risk)

        meta = {
            "typed_timeline": timeline,
            "milestone_ordering": self.milestones,
        }
        return clocks, risks, decisions, meta

