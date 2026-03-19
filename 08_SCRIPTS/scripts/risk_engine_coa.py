"""
COA Dismissal-Risk Engine

Keyed to:
(a) docketing statement timing (MCR 7.204(H); COA IOPs),
(b) transcript certification timing (MCR 7.210(B)(3)(a)),
(c) briefing-clock triggers (MCR 7.212(E) + IOP warning letter practice),
(d) COA IOP enforcement behaviors (warning/deficiency letters; involuntary dismissal docket; reinstatement guidance).

Inputs:
- matter_id
- lane (optional) for case-type inference (custody lanes bias towards custody transcript timelines)
- TriggerEvents (including clerk letters ingested via ingest_clerk_letter)

Outputs:
- Clocks
- RiskEvents with cure options (fastest cure computed)
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
    lane: str = "UNKNOWN"  # e.g., MEEK2 custody, MEEK3 ppo, etc.
    # allow explicit case type flags for transcript timelines
    case_type: str = "UNKNOWN"  # "custody", "interlocutory_criminal", "other"


def _infer_case_type(ctx: MatterContext, triggers: List[TriggerEvent]) -> str:
    if ctx.case_type != "UNKNOWN":
        return ctx.case_type
    lane = (ctx.lane or "").lower()
    if "custody" in lane or "meek2" in lane:
        return "custody"
    # allow override via triggers
    for t in triggers:
        ct = (t.extracted_signals or {}).get("case_type")
        if isinstance(ct, str) and ct:
            return ct
    return "other"


def _parse_iso(s: str) -> datetime:
    return datetime.fromisoformat(s.replace("Z", "+00:00")).astimezone(timezone.utc)


def _clock_expired(clock: Clock, now: Optional[datetime] = None) -> bool:
    now = now or utc_now()
    try:
        return _parse_iso(clock.due_at) < now
    except Exception:
        return False


def _doc_filed(triggers: List[TriggerEvent], doc_type: str) -> bool:
    for t in triggers:
        if t.event_type in ("FILING_ACCEPTED", "FILING_ATTEMPTED", "DEADLINE_EVENT"):
            dt = (t.extracted_signals or {}).get("doc_type")
            if isinstance(dt, str) and dt.lower() == doc_type.lower():
                return True
    return False


class COARiskEngine:
    def __init__(self) -> None:
        self.profile = DEFAULT_PROFILES["COA"]

    def run(self, ctx: MatterContext, triggers: List[TriggerEvent]) -> Tuple[List[Clock], List[RiskEvent], Dict[str, GateDecision]]:
        clocks: List[Clock] = []
        risks: List[RiskEvent] = []
        decisions: Dict[str, GateDecision] = {}

        case_type = _infer_case_type(ctx, triggers)

        # --- Derive foundational filing date (claim of appeal / order granting leave) if present.
        base_filing_dt: Optional[datetime] = None
        for t in triggers:
            if t.event_type == "FILING_ACCEPTED" and (t.extracted_signals or {}).get("doc_type") in ("claim_of_appeal", "order_granting_leave"):
                base_filing_dt = _parse_iso(t.occurred_at)
                break

        # 1) Docketing statement due 28 days after base filing (when base filing known).
        if base_filing_dt:
            ds_due = base_filing_dt + timedelta(days=28)
            ds_clock = Clock.make(
                matter_id=ctx.matter_id,
                forum_profile="COA",
                clock_kind="due_date",
                opens_at=base_filing_dt,
                due_at=ds_due,
                basis="MCR 7.204(H) / COA docketing statement due 28 days",
                tolling_notes="MCR 1.108 time computation applies",
            )
            clocks.append(ds_clock)

            if _clock_expired(ds_clock) and not _doc_filed(triggers, "docketing_statement"):
                # Overdue docketing statement -> curable defect / dismissal risk; rely on IOP warning letters when available.
                risk = RiskEvent.make(
                    matter_id=ctx.matter_id,
                    forum_profile="COA",
                    risk_class="dismissal_risk",
                    kill_mechanism="dismissal",
                    trigger_event_id=None,
                    clock_id=ds_clock.id,
                    description="Docketing statement appears overdue; COA clerk deficiency process may lead to involuntary dismissal docket if not cured.",
                    authority_refs=[
                        AuthorityRef(ref="MCR 7.204(H)", pinpoint="docketing statement timing", url=None),
                        AuthorityRef(ref="COA Clerk IOP", pinpoint="docketing statement deficiency letters / dismissal path", url=None),
                    ],
                    confidence=0.75,
                )
                risk.compute_severity()

                # Cure option: file docketing statement now + proof of service.
                cure_clock = Clock.make(
                    matter_id=ctx.matter_id,
                    forum_profile="COA",
                    clock_kind="cure_window",
                    opens_at=utc_now(),
                    due_at=utc_now() + timedelta(days=21),
                    basis="COA clerk cure window often stated in deficiency letters (default 21 days if letter date unknown)",
                    tolling_notes="If an actual clerk letter exists, replace this clock with letter-derived due_at.",
                )
                clocks.append(cure_clock)

                cure = CureOption(
                    id=deterministic_id("cure", risk.id, "file_docketing_statement"),
                    summary="File docketing statement + proof of service (and any required fee/verification) to cure deficiency.",
                    cure_cost=CureCost(time_band="hours", fee_band="none", complexity="low", dependencies=[]),
                    cure_deadline_clock_id=cure_clock.id,
                    cure_minimum_packet=PacketSpec(items=[
                        PacketItem(item_type="pleading", required=True, notes="Docketing statement (conforming, signed where required).", authority_basis="MCR 7.204(H)"),
                        PacketItem(item_type="proof_of_service", required=True, notes="Proof of service on all parties.", authority_basis="MCR 1.109(F)"),
                    ])
                )
                risk.cure_options = [cure]
                risk.rank_cures()
                risks.append(risk)
                decisions[risk.id] = self.profile.decide(risk.risk_class, cure_window_expired=False, jurisdictional=False)

        # 2) Clerk letters / deficiency notices
        for t in triggers:
            if t.forum_profile != "COA":
                continue
            if t.event_type not in ("COA_CLERK_WARNING_LETTER_SENT", "COA_NOTICE_OF_DEFICIENCY_SENT", "COA_NOTICE_OF_DISMISSAL_SENT"):
                continue

            occurred = _parse_iso(t.occurred_at)
            sig = t.extracted_signals or {}
            days = sig.get("days_mentioned")
            if not isinstance(days, int):
                # default when the notice is a cure window letter
                days = 21

            if t.event_type in ("COA_CLERK_WARNING_LETTER_SENT", "COA_NOTICE_OF_DEFICIENCY_SENT"):
                cure_due = occurred + timedelta(days=days)
                cure_clock = Clock.make(
                    matter_id=ctx.matter_id,
                    forum_profile="COA",
                    clock_kind="cure_window",
                    opens_at=occurred,
                    due_at=cure_due,
                    basis="COA clerk warning/deficiency letter cure window (commonly 21 days) before involuntary dismissal docket.",
                    tolling_notes="Cure window derived from the letter text when available.",
                )
                clocks.append(cure_clock)

                # Determine the missing item(s)
                missing_items: List[PacketItem] = []
                if sig.get("mentions_docketing_statement"):
                    missing_items.append(PacketItem(item_type="pleading", required=True, notes="Docketing statement.", authority_basis="MCR 7.204(H)"))
                if sig.get("mentions_transcript"):
                    missing_items.append(PacketItem(item_type="certificate", required=False, notes="Stenographer/court reporter certificate or proof transcript ordered/paid.", authority_basis="MCR 7.210(B)(3)(a)"))
                    missing_items.append(PacketItem(item_type="record_component", required=False, notes="Notice of filing transcript (copy acceptable).", authority_basis="COA IOP 7.210(B)(3)(e) / MCR 7.210"))
                if sig.get("mentions_brief"):
                    missing_items.append(PacketItem(item_type="pleading", required=False, notes="Missing brief(s) identified in notice.", authority_basis="MCR 7.212"))
                if not missing_items:
                    missing_items.append(PacketItem(item_type="pleading", required=True, notes="Missing filing identified in the clerk notice.", authority_basis="UNKNOWN"))

                missing_items.append(PacketItem(item_type="proof_of_service", required=True, notes="Proof of service on all parties.", authority_basis="MCR 1.109(F)"))

                risk = RiskEvent.make(
                    matter_id=ctx.matter_id,
                    forum_profile="COA",
                    risk_class="dismissal_risk",
                    kill_mechanism="dismissal",
                    trigger_event_id=t.id,
                    clock_id=cure_clock.id,
                    description="COA clerk deficiency/warning letter indicates dismissal risk if identified item(s) are not filed within the cure window.",
                    authority_refs=[
                        AuthorityRef(ref="COA Clerk IOP", pinpoint="warning letters + involuntary dismissal docket practice", url=None),
                    ],
                    clerk_letter_refs=[t.source_record_ref_id or "UNKNOWN_RECORDREF"],
                    confidence=0.95,
                )
                risk.compute_severity()

                cure = CureOption(
                    id=deterministic_id("cure", risk.id, "cure_by_filing_missing_items"),
                    summary="File the missing item(s) identified by the clerk letter within the cure window.",
                    cure_cost=CureCost(time_band="hours", fee_band="none", complexity="medium", dependencies=[]),
                    cure_deadline_clock_id=cure_clock.id,
                    cure_minimum_packet=PacketSpec(items=missing_items),
                )
                risk.cure_options = [cure]
                risk.rank_cures()

                expired = _clock_expired(cure_clock)
                decisions[risk.id] = self.profile.decide(risk.risk_class, cure_window_expired=expired, jurisdictional=False)
                risks.append(risk)

            elif t.event_type == "COA_NOTICE_OF_DISMISSAL_SENT":
                # After dismissal: reinstatement motion window (MCR 7.217 reinstatement window)
                rein_due = occurred + timedelta(days=21)
                rein_clock = Clock.make(
                    matter_id=ctx.matter_id,
                    forum_profile="COA",
                    clock_kind="reinstatement_window",
                    opens_at=occurred,
                    due_at=rein_due,
                    basis="MCR 7.217 reinstatement motion window (21 days after clerk notice of dismissal).",
                    tolling_notes="Model assumes dismissal was involuntary and clerk notice date is the trigger; adjust if different.",
                )
                clocks.append(rein_clock)

                risk = RiskEvent.make(
                    matter_id=ctx.matter_id,
                    forum_profile="COA",
                    risk_class="curable_defect",
                    kill_mechanism="stall",
                    trigger_event_id=t.id,
                    clock_id=rein_clock.id,
                    description="Appeal appears dismissed; reinstatement window is open. Missing the reinstatement window typically prevents reactivation absent extraordinary relief.",
                    authority_refs=[
                        AuthorityRef(ref="MCR 7.217(D)", pinpoint="motion to reinstate within 21 days after clerk notice of dismissal", url=None),
                        AuthorityRef(ref="COA Clerk IOP", pinpoint="reinstatement guidance: include omitted filing (certificate/notice/brief) with motion", url=None),
                    ],
                    clerk_letter_refs=[t.source_record_ref_id or "UNKNOWN_RECORDREF"],
                    confidence=0.95,
                )
                risk.compute_severity()

                cure = CureOption(
                    id=deterministic_id("cure", risk.id, "file_motion_to_reinstate"),
                    summary="File motion to reinstate within 21 days, ideally accompanied by the omitted filing (certificate/notice/brief).",
                    cure_cost=CureCost(time_band="days", fee_band="none", complexity="medium", dependencies=["prepare motion + attach omitted filing if available"]),
                    cure_deadline_clock_id=rein_clock.id,
                    cure_minimum_packet=PacketSpec(items=[
                        PacketItem(item_type="motion", required=True, notes="Motion to reinstate with explanation and requested relief.", authority_basis="MCR 7.217(D)"),
                        PacketItem(item_type="record_component", required=False, notes="Attach or show evidence of formerly omitted filing (certificate/notice/brief).", authority_basis="COA Clerk IOP reinstatement guidance"),
                        PacketItem(item_type="proof_of_service", required=True, notes="Proof of service.", authority_basis="MCR 1.109(F)"),
                    ])
                )
                risk.cure_options = [cure]
                risk.rank_cures()

                expired = _clock_expired(rein_clock)
                decisions[risk.id] = self.profile.decide("dismissal_risk", cure_window_expired=expired, jurisdictional=False)
                risks.append(risk)

        return clocks, risks, decisions

