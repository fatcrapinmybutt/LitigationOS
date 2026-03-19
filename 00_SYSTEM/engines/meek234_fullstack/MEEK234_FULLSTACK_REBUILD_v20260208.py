#!/usr/bin/env python3
"""
MEEK2 + MEEK3 + MEEK4 Full-Stack Rebuild (Baseline) — LitigationOS
- Single-file, production-oriented baseline that:
  * Harvests local folders (txt/md/json/csv; optional docx/pdf)
  * Extracts EvidenceAtoms + EventAtoms (typed; multi-track tagging)
  * Computes DeadlineClocks (configurable; includes a few Michigan-rule-based defaults)
  * Generates RiskEvents (missing operating order pin, clock risks, missing dates)
  * Emits: manifest.json, timeline.csv, nodes.csv, edges.csv, run.json, dash.html
  * Optional Neo4j upsert if NEO4J_URI/USER/PASS are set (neo4j python driver required)

This is built to be *extendable* without breaking determinism:
- Stable IDs: sha1 over (kind + source_path + offsets + normalized snippet + date/type keys)
- Append-only outputs: new runs live under runs/<timestamp>/

USAGE (Windows):
  py MEEK234_FULLSTACK_REBUILD_v20260208.py harvest --in "C:\\path\\to\\Litigation_Intake" --out-root "C:\\path\\to\\THE_LITIGATION_OPERATING_SYSTEM\\runs"
  py MEEK234_FULLSTACK_REBUILD_v20260208.py serve --run "C:\\...\\runs\\20260208_123456"
  py MEEK234_FULLSTACK_REBUILD_v20260208.py neo4j-upsert --run "C:\\...\\runs\\20260208_123456"

NOT LEGAL ADVICE.
"""
from __future__ import annotations

import argparse
import csv
import dataclasses
import datetime as dt
import hashlib
import json
import os
import re
import sys
import textwrap
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

# -----------------------------
# Deterministic helpers
# -----------------------------

def sha1_hex(s: str) -> str:
    return hashlib.sha1(s.encode("utf-8", errors="ignore")).hexdigest()

def norm_ws(s: str) -> str:
    return re.sub(r"\s+", " ", s.strip())

def safe_relpath(path: Path, base: Path) -> str:
    try:
        return str(path.relative_to(base)).replace("\\", "/")
    except Exception:
        return str(path).replace("\\", "/")

def ensure_dir(p: Path) -> None:
    p.mkdir(parents=True, exist_ok=True)

def iso_date(d: dt.date) -> str:
    return d.isoformat()

def iso_dt(x: dt.datetime) -> str:
    return x.replace(microsecond=0).isoformat()

# -----------------------------
# Domain models
# -----------------------------

TRACKS = ["MEEK2", "MEEK3", "MEEK4"]

@dataclasses.dataclass(frozen=True)
class DocumentRef:
    doc_id: str
    rel_path: str
    abs_path: str
    ext: str
    size_bytes: int
    mtime_iso: str

@dataclasses.dataclass(frozen=True)
class EvidenceAtom:
    evid_id: str
    doc_id: str
    rel_path: str
    span_start: int
    span_end: int
    quote: str
    tracks: Tuple[str, ...]
    created_at: str

@dataclasses.dataclass(frozen=True)
class EventAtom:
    event_id: str
    kind: str  # OrderEvent, ServiceEvent, HearingEvent, CommunicationEvent, FilingEvent, OtherEvent
    date: Optional[str]  # YYYY-MM-DD if known
    title: str
    details: str
    tracks: Tuple[str, ...]
    source_evid_id: Optional[str]
    created_at: str

@dataclasses.dataclass(frozen=True)
class DeadlineClock:
    clock_id: str
    clock_type: str
    trigger_event_id: str
    due_date: str
    basis: str  # authority / rule note
    tracks: Tuple[str, ...]
    created_at: str

@dataclasses.dataclass(frozen=True)
class RiskEvent:
    risk_id: str
    risk_class: str  # jurisdictional_fatal/admin_return_without_docketing/curable_defect/dismissal_risk/record_incomplete/discretionary_sanction_risk
    severity: int    # 1-100
    title: str
    details: str
    related_ids: Tuple[str, ...]
    fastest_cure: str
    cure_cost: str
    cure_deadline_clock: Optional[str]
    cure_minimum_packet: Tuple[str, ...]
    tracks: Tuple[str, ...]
    created_at: str

@dataclasses.dataclass(frozen=True)
class VehicleCandidate:
    vehicle_id: str
    vehicle_type: str
    purpose: str
    operating_order_pin: Optional[str]  # order_id or order reference
    required_record_items: Tuple[str, ...]
    denial_grounds: Tuple[str, ...]
    tracks: Tuple[str, ...]
    created_at: str

# -----------------------------
# Michigan-rule based default clocks (baseline)
# -----------------------------
# NOTE: These are *baseline defaults* and should be validated against the user’s authority snapshot.
# They are here to operationalize the rebuild with working clocks.
DEFAULT_CLOCK_RULES = [
    {
        "clock_type": "trial_reconsideration_21d",
        "basis": "MCR 2.119(F)(1) — served+filed not later than 21 days after entry of order deciding the motion",
        "trigger_kinds": ["OrderEvent"],
        "keyword_any": ["reconsider", "rehearing", "order"],
        "days_after": 21,
        "tracks": ["MEEK2", "MEEK3", "MEEK4"],
    },
    {
        "clock_type": "judge_disqualification_14d",
        "basis": "MCR 2.003(D)(1)(a) — motions for disqualification filed within 14 days of discovery of grounds (trial courts)",
        "trigger_kinds": ["OtherEvent", "OrderEvent", "HearingEvent"],
        "keyword_any": ["disqual", "recus", "bias", "prejud"],
        "days_after": 14,
        "tracks": ["MEEK4"],
    },
]

# -----------------------------
# Extraction: file readers
# -----------------------------

def read_text_file(p: Path) -> str:
    # Try utf-8 first; fallback to latin-1
    try:
        return p.read_text(encoding="utf-8")
    except UnicodeDecodeError:
        return p.read_text(encoding="latin-1", errors="ignore")

def read_docx_file(p: Path) -> Optional[str]:
    try:
        import docx  # python-docx
    except Exception:
        return None
    try:
        d = docx.Document(str(p))
        parts = []
        for para in d.paragraphs:
            t = para.text.strip()
            if t:
                parts.append(t)
        return "\n".join(parts)
    except Exception:
        return None

def read_pdf_file(p: Path) -> Optional[str]:
    # Best-effort without OCR: text extraction only.
    try:
        from pypdf import PdfReader
    except Exception:
        try:
            from PyPDF2 import PdfReader
        except Exception:
            return None
    try:
        reader = PdfReader(str(p))
        out = []
        for page in reader.pages:
            try:
                txt = page.extract_text() or ""
            except Exception:
                txt = ""
            if txt.strip():
                out.append(txt)
        return "\n".join(out)
    except Exception:
        return None

def load_document_text(p: Path) -> Optional[str]:
    ext = p.suffix.lower()
    if ext in [".txt", ".md", ".log"]:
        return read_text_file(p)
    if ext in [".json", ".jsonl"]:
        return read_text_file(p)
    if ext in [".csv"]:
        return read_text_file(p)
    if ext in [".docx"]:
        return read_docx_file(p)
    if ext in [".pdf"]:
        return read_pdf_file(p)
    return None

# -----------------------------
# Extraction: evidence + events
# -----------------------------

DATE_PATTERNS = [
    # 2025-10-01
    re.compile(r"\b(20\d{2})[-/](\d{1,2})[-/](\d{1,2})\b"),
    # 10/21/25 or 10/21/2025
    re.compile(r"\b(\d{1,2})/(\d{1,2})/(20\d{2}|\d{2})\b"),
    # Month name day, year
    re.compile(r"\b(Jan(?:uary)?|Feb(?:ruary)?|Mar(?:ch)?|Apr(?:il)?|May|Jun(?:e)?|Jul(?:y)?|Aug(?:ust)?|Sep(?:t(?:ember)?)?|Oct(?:ober)?|Nov(?:ember)?|Dec(?:ember)?)\s+(\d{1,2}),\s*(20\d{2})\b", re.IGNORECASE),
]

MONTHS = {
    "jan": 1, "january": 1,
    "feb": 2, "february": 2,
    "mar": 3, "march": 3,
    "apr": 4, "april": 4,
    "may": 5,
    "jun": 6, "june": 6,
    "jul": 7, "july": 7,
    "aug": 8, "august": 8,
    "sep": 9, "sept": 9, "september": 9,
    "oct": 10, "october": 10,
    "nov": 11, "november": 11,
    "dec": 12, "december": 12,
}

def parse_date_candidates(text: str) -> List[str]:
    cands: List[str] = []
    for pat in DATE_PATTERNS:
        for m in pat.finditer(text):
            try:
                if pat.pattern.startswith(r"\b(20"):
                    y = int(m.group(1)); mo = int(m.group(2)); d = int(m.group(3))
                elif pat.pattern.startswith(r"\b(\d{1,2})/"):
                    mo = int(m.group(1)); d = int(m.group(2))
                    yraw = m.group(3)
                    y = int(yraw) if len(yraw) == 4 else 2000 + int(yraw)
                else:
                    mon = m.group(1).lower().strip(".")
                    mon = mon[:3] if len(mon) > 3 and mon not in MONTHS else mon
                    mo = MONTHS.get(mon, MONTHS.get(mon[:3], 0))
                    d = int(m.group(2)); y = int(m.group(3))
                dd = dt.date(y, mo, d)
                cands.append(dd.isoformat())
            except Exception:
                continue
    # Stable unique order
    out = []
    seen = set()
    for x in cands:
        if x not in seen:
            out.append(x); seen.add(x)
    return out

def tag_tracks(text: str) -> Tuple[str, ...]:
    t = text.lower()
    tracks = set()
    # MEEK2
    if any(k in t for k in ["custody", "parenting time", "parenting-time", "foc", "friend of the court", "child support", "support order", "mcsf", "overpayment", "overnight"]):
        tracks.add("MEEK2")
    # MEEK3
    if any(k in t for k in ["ppo", "personal protection order", "show cause", "show-cause", "contempt", "mittimus", "violation", "restraining"]):
        tracks.add("MEEK3")
    # MEEK4
    if any(k in t for k in ["judge", "disqual", "recus", "bias", "judicial tenure commission", "jtc", "chief judge", "canon", "misconduct", "superintending"]):
        tracks.add("MEEK4")
    # Default: if none, keep empty
    return tuple(sorted(tracks))

EVENT_RULES = [
    # kind, keywords-any, title
    ("OrderEvent", ["order", "opinion and order", "entered", "signed"], "Order / Opinion"),
    ("ServiceEvent", ["served", "service", "proof of service", "personal service", "certified mail", "mailing"], "Service / Proof"),
    ("HearingEvent", ["hearing", "conference", "trial", "show cause", "show-cause"], "Hearing / Proceeding"),
    ("FilingEvent", ["filed", "motion", "petition", "application", "brief", "claim of appeal", "appeal"], "Filing / Motion"),
    ("CommunicationEvent", ["email", "text", "call", "voicemail", "appclose", "co-parent", "message"], "Communication"),
]

def extract_evidence_atoms(doc: DocumentRef, text: str, base: Path, max_atoms: int = 400) -> List[EvidenceAtom]:
    # Chunk by paragraphs; store short quotes for provenance
    created = iso_dt(dt.datetime.now())
    rel = doc.rel_path
    atoms: List[EvidenceAtom] = []
    # Track offsets for deterministic spans
    offset = 0
    for para in re.split(r"\n{2,}", text):
        p = para.strip()
        if not p:
            offset += len(para) + 2
            continue
        # Take a bounded snippet for quoting
        snippet = norm_ws(p)
        snippet_short = snippet[:600]
        # Derive stable id
        key = f"EVID|{doc.doc_id}|{rel}|{offset}|{offset+len(para)}|{snippet_short.lower()}"
        evid_id = "evid:" + sha1_hex(key)
        tracks = tag_tracks(snippet_short)
        atoms.append(EvidenceAtom(
            evid_id=evid_id,
            doc_id=doc.doc_id,
            rel_path=rel,
            span_start=offset,
            span_end=offset + len(para),
            quote=snippet_short,
            tracks=tracks,
            created_at=created,
        ))
        if len(atoms) >= max_atoms:
            break
        offset += len(para) + 2
    return atoms

def extract_event_atoms(evid: EvidenceAtom) -> List[EventAtom]:
    created = iso_dt(dt.datetime.now())
    text = evid.quote
    t = text.lower()
    dates = parse_date_candidates(text)
    date = dates[0] if dates else None

    events: List[EventAtom] = []
    for kind, kws, title in EVENT_RULES:
        if any(k in t for k in kws):
            # Stable id based on kind + date + snippet
            key = f"EVT|{kind}|{date or 'nodate'}|{evid.evid_id}|{text[:200].lower()}"
            event_id = "event:" + sha1_hex(key)
            details = text[:800]
            tracks = evid.tracks
            events.append(EventAtom(
                event_id=event_id,
                kind=kind,
                date=date,
                title=title,
                details=details,
                tracks=tracks,
                source_evid_id=evid.evid_id,
                created_at=created,
            ))
            break
    return events

# -----------------------------
# Clock engine
# -----------------------------

def compute_clocks(events: List[EventAtom], clock_rules: List[Dict[str, Any]]) -> List[DeadlineClock]:
    out: List[DeadlineClock] = []
    created = iso_dt(dt.datetime.now())

    # Index events by id for determinism
    events_sorted = sorted(events, key=lambda e: e.event_id)

    for ev in events_sorted:
        if not ev.date:
            continue
        try:
            ev_date = dt.date.fromisoformat(ev.date)
        except Exception:
            continue

        ev_text = (ev.title + " " + ev.details).lower()

        for rule in clock_rules:
            trig_kinds = set(rule.get("trigger_kinds", []))
            if trig_kinds and ev.kind not in trig_kinds:
                continue
            kw_any = [k.lower() for k in rule.get("keyword_any", [])]
            if kw_any and not any(k in ev_text for k in kw_any):
                continue
            days_after = int(rule.get("days_after", 0))
            due = ev_date + dt.timedelta(days=days_after)

            basis = str(rule.get("basis", ""))
            clock_type = str(rule.get("clock_type", "clock"))

            tracks = tuple(sorted(set(rule.get("tracks", [])).intersection(set(ev.tracks)) or set(ev.tracks)))

            key = f"CLK|{clock_type}|{ev.event_id}|{due.isoformat()}|{basis}"
            clock_id = "clock:" + sha1_hex(key)

            out.append(DeadlineClock(
                clock_id=clock_id,
                clock_type=clock_type,
                trigger_event_id=ev.event_id,
                due_date=due.isoformat(),
                basis=basis,
                tracks=tracks,
                created_at=created,
            ))
    # Unique by id
    dedup: Dict[str, DeadlineClock] = {}
    for c in out:
        dedup[c.clock_id] = c
    return list(dedup.values())

# -----------------------------
# Risk engine (baseline)
# -----------------------------

def compute_risks(events: List[EventAtom], clocks: List[DeadlineClock], vehicles: List[VehicleCandidate]) -> List[RiskEvent]:
    created = iso_dt(dt.datetime.now())
    risks: List[RiskEvent] = []

    # Helper: days until due
    today = dt.date.today()
    for c in clocks:
        try:
            due = dt.date.fromisoformat(c.due_date)
            days_left = (due - today).days
        except Exception:
            continue
        if days_left < 0:
            risk_class = "curable_defect"
            severity = 85
            title = f"Clock expired: {c.clock_type}"
            details = f"Due date {c.due_date} has passed ({-days_left} days late). Basis: {c.basis}."
            fastest_cure = "Identify if tolling/alternate trigger applies; otherwise consider available late remedies (if any)."
            cure_cost = "medium"
            cure_deadline_clock = None
            cure_min_packet = ("OperatingOrderPin (trigger order/event)", "Proof of service / entry date evidence", "Motion/filing packet for the chosen remedy")
        elif days_left <= 3:
            risk_class = "dismissal_risk"
            severity = 70
            title = f"Clock urgent: {c.clock_type}"
            details = f"Due date {c.due_date} is in {days_left} day(s). Basis: {c.basis}."
            fastest_cure = "Assemble and file minimum packet immediately."
            cure_cost = "high"
            cure_deadline_clock = c.clock_id
            cure_min_packet = ("Draft motion/filing", "OperatingOrderPin", "Service plan + proof", "Append exhibits supporting trigger date")
        elif days_left <= 10:
            risk_class = "record_incomplete"
            severity = 45
            title = f"Clock approaching: {c.clock_type}"
            details = f"Due date {c.due_date} is in {days_left} day(s). Basis: {c.basis}."
            fastest_cure = "Prepare packet and schedule service; verify trigger dates."
            cure_cost = "medium"
            cure_deadline_clock = c.clock_id
            cure_min_packet = ("Draft packet", "OperatingOrderPin", "EvidenceAtom(s) for trigger date", "Service method selection")
        else:
            continue

        key = f"RISK|clock|{c.clock_id}|{risk_class}|{title}"
        risks.append(RiskEvent(
            risk_id="risk:" + sha1_hex(key),
            risk_class=risk_class,
            severity=severity,
            title=title,
            details=details,
            related_ids=(c.clock_id, c.trigger_event_id),
            fastest_cure=fastest_cure,
            cure_cost=cure_cost,
            cure_deadline_clock=cure_deadline_clock,
            cure_minimum_packet=tuple(cure_min_packet),
            tracks=c.tracks,
            created_at=created,
        ))

    # Vehicle validity: OperatingOrderPin required (per user directive)
    for v in vehicles:
        if not v.operating_order_pin:
            key = f"RISK|vehicle|{v.vehicle_id}|missing_operating_order"
            risks.append(RiskEvent(
                risk_id="risk:" + sha1_hex(key),
                risk_class="record_incomplete",
                severity=65,
                title="Vehicle missing OperatingOrderPin",
                details=f"VehicleCandidate '{v.vehicle_type}' has no OperatingOrderPin. System policy requires pinning the controlling order (signed/entered/served/effective/superseded) before vehicle is considered valid.",
                related_ids=(v.vehicle_id,),
                fastest_cure="Attach the operative order (PDF/text) and mark entry/signed/served dates; link ROA entry if available.",
                cure_cost="low",
                cure_deadline_clock=None,
                cure_minimum_packet=("Order copy (signed/entered stamp)", "ROA entry line if available", "Service proof or notice record"),
                tracks=v.tracks,
                created_at=created,
            ))

    # If we have lots of undated events, warn
    undated = [e for e in events if not e.date]
    if undated:
        key = f"RISK|undated|{len(undated)}"
        risks.append(RiskEvent(
            risk_id="risk:" + sha1_hex(key),
            risk_class="record_incomplete",
            severity=min(80, 20 + len(undated)),
            title="Undated events detected",
            details=f"{len(undated)} event(s) were extracted without a parsable date. This can break deadline computation and operating-order pinning.",
            related_ids=tuple(sorted({e.event_id for e in undated})[:50]),
            fastest_cure="Add explicit dates into source documents, or annotate via a small 'event_overrides.json' file and re-run harvest.",
            cure_cost="low",
            cure_deadline_clock=None,
            cure_minimum_packet=("event_overrides.json (event_id→date)", "EvidenceAtoms that prove each date"),
            tracks=tuple(TRACKS),
            created_at=created,
        ))
    # Dedup
    dedup: Dict[str, RiskEvent] = {}
    for r in risks:
        dedup[r.risk_id] = r
    return list(dedup.values())

# -----------------------------
# Vehicle generator (baseline)
# -----------------------------

def generate_vehicle_candidates(events: List[EventAtom], operating_order_pin: Optional[str]) -> List[VehicleCandidate]:
    created = iso_dt(dt.datetime.now())

    # Presence signals
    text_blob = " ".join((e.title + " " + e.details) for e in events).lower()
    have_order = any(e.kind == "OrderEvent" for e in events)

    vehicles: List[VehicleCandidate] = []

    # MEEK2: custody/parenting time/support vehicles (baseline)
    if any(t in text_blob for t in ["custody", "parenting time", "child support", "foc", "mcsf"]):
        vehicles.append(VehicleCandidate(
            vehicle_id="vehicle:" + sha1_hex("veh|meek2|modify_parenting_time|" + (operating_order_pin or "nopin")),
            vehicle_type="MEEK2: Modify Parenting Time / Custody / Support (baseline)",
            purpose="Change or restore parenting-time/custody/support order via trial-court motion practice and required findings.",
            operating_order_pin=operating_order_pin,
            required_record_items=(
                "OperatingOrderPin (current controlling custody/PT/support order)",
                "ROA entries for last controlling order + any stays",
                "Affidavit / verified facts (as required)",
                "Proposed order",
                "Exhibit index (documents, transcripts, service proofs)",
            ),
            denial_grounds=(
                "No controlling order pinned / unclear operative order",
                "Insufficient proof of service/notice",
                "Missing required findings record support",
                "Unsupported factual assertions",
            ),
            tracks=("MEEK2",),
            created_at=created,
        ))

    # MEEK3: PPO / show-cause / contempt vehicles (baseline)
    if any(t in text_blob for t in ["ppo", "personal protection order", "show cause", "contempt"]):
        vehicles.append(VehicleCandidate(
            vehicle_id="vehicle:" + sha1_hex("veh|meek3|terminate_or_modify_ppo|" + (operating_order_pin or "nopin")),
            vehicle_type="MEEK3: Modify/Terminate PPO or Defend Show-Cause (baseline)",
            purpose="Seek modification/termination of PPO or defend alleged violation with service/record/evidence mapping.",
            operating_order_pin=operating_order_pin,
            required_record_items=(
                "OperatingOrderPin (PPO order + any extensions)",
                "ServiceEvent proof of service/notice",
                "Transcript/record pinpoints for hearing findings",
                "Exhibits showing permitted vs prohibited communications",
                "Proposed order",
            ),
            denial_grounds=(
                "Operative PPO not pinned (signed/served/effective)",
                "No record of conditions or findings",
                "Hearsay/unsupported exhibits without foundation",
            ),
            tracks=("MEEK3",),
            created_at=created,
        ))

    # MEEK4: Disqualification / JTC milestone vehicles (baseline)
    if any(t in text_blob for t in ["judge", "bias", "recus", "disqual", "jtc", "judicial tenure commission", "canon"]):
        vehicles.append(VehicleCandidate(
            vehicle_id="vehicle:" + sha1_hex("veh|meek4|judge_disqualification|" + (operating_order_pin or "nopin")),
            vehicle_type="MEEK4: Judge Disqualification / JTC Record Pack (baseline)",
            purpose="Route judge-disqualification and judicial-conduct record packaging with milestone tracking.",
            operating_order_pin=operating_order_pin,
            required_record_items=(
                "OperatingOrderPin (order/assignment implicating the judge)",
                "Disqualification motion + affidavit",
                "Objective record extracts (orders, transcripts, clerk notices)",
                "Chronology of bias indicators (dated)",
            ),
            denial_grounds=(
                "Untimely (discovery-based clock)",
                "No affidavit or incomplete grounds",
                "Overly conclusory allegations without record pinpoints",
            ),
            tracks=("MEEK4",),
            created_at=created,
        ))

    # If we harvested something but no signal, still provide a generic cross-track vehicle
    if not vehicles and events:
        vehicles.append(VehicleCandidate(
            vehicle_id="vehicle:" + sha1_hex("veh|generic|record_gap_closure|" + (operating_order_pin or "nopin")),
            vehicle_type="GENERIC: Record Gap Closure / Operating Order Pin",
            purpose="Stabilize the record: pin operative orders, service, deadlines, and transcript sources before choosing a vehicle.",
            operating_order_pin=operating_order_pin,
            required_record_items=(
                "OperatingOrderPin (identify controlling orders)",
                "ROA lines",
                "Service proofs",
                "Transcript ordering status",
            ),
            denial_grounds=("Incomplete record",),
            tracks=tuple(TRACKS),
            created_at=created,
        ))

    return vehicles

# -----------------------------
# Graph export (Neo4j-friendly CSV)
# -----------------------------

def build_nodes_edges(docs: List[DocumentRef], evids: List[EvidenceAtom], events: List[EventAtom],
                      clocks: List[DeadlineClock], risks: List[RiskEvent], vehicles: List[VehicleCandidate]) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
    nodes: List[Dict[str, Any]] = []
    edges: List[Dict[str, Any]] = []

    def add_node(node_id: str, label: str, props: Dict[str, Any]) -> None:
        row = {"id": node_id, "label": label}
        row.update(props)
        nodes.append(row)

    def add_edge(edge_id: str, src: str, rel: str, dst: str, props: Dict[str, Any]) -> None:
        row = {"id": edge_id, "src": src, "rel": rel, "dst": dst}
        row.update(props)
        edges.append(row)

    # Docs
    for d in docs:
        add_node(d.doc_id, "Document", {
            "rel_path": d.rel_path,
            "abs_path": d.abs_path,
            "ext": d.ext,
            "size_bytes": d.size_bytes,
            "mtime": d.mtime_iso,
        })

    # Evidence
    for e in evids:
        add_node(e.evid_id, "EvidenceAtom", {
            "doc_id": e.doc_id,
            "rel_path": e.rel_path,
            "span_start": e.span_start,
            "span_end": e.span_end,
            "quote": e.quote,
            "tracks": "|".join(e.tracks),
            "created_at": e.created_at,
        })
        eid = "edge:" + sha1_hex(f"{e.doc_id}|HAS_EVIDENCE|{e.evid_id}")
        add_edge(eid, e.doc_id, "HAS_EVIDENCE", e.evid_id, {"rel_path": e.rel_path})

    # Events
    for ev in events:
        add_node(ev.event_id, "EventAtom", {
            "kind": ev.kind,
            "date": ev.date or "",
            "title": ev.title,
            "details": ev.details,
            "tracks": "|".join(ev.tracks),
            "created_at": ev.created_at,
        })
        if ev.source_evid_id:
            eid = "edge:" + sha1_hex(f"{ev.source_evid_id}|SUPPORTS_EVENT|{ev.event_id}")
            add_edge(eid, ev.source_evid_id, "SUPPORTS_EVENT", ev.event_id, {})

    # Clocks
    for c in clocks:
        add_node(c.clock_id, "DeadlineClock", {
            "clock_type": c.clock_type,
            "due_date": c.due_date,
            "basis": c.basis,
            "tracks": "|".join(c.tracks),
            "created_at": c.created_at,
        })
        eid = "edge:" + sha1_hex(f"{c.trigger_event_id}|TRIGGERS_CLOCK|{c.clock_id}")
        add_edge(eid, c.trigger_event_id, "TRIGGERS_CLOCK", c.clock_id, {})

    # Risks
    for r in risks:
        add_node(r.risk_id, "RiskEvent", {
            "risk_class": r.risk_class,
            "severity": r.severity,
            "title": r.title,
            "details": r.details,
            "fastest_cure": r.fastest_cure,
            "cure_cost": r.cure_cost,
            "cure_deadline_clock": r.cure_deadline_clock or "",
            "cure_minimum_packet": "|".join(r.cure_minimum_packet),
            "tracks": "|".join(r.tracks),
            "created_at": r.created_at,
        })
        for rid in r.related_ids:
            eid = "edge:" + sha1_hex(f"{r.risk_id}|RELATES_TO|{rid}")
            add_edge(eid, r.risk_id, "RELATES_TO", rid, {})

    # Vehicles
    for v in vehicles:
        add_node(v.vehicle_id, "VehicleCandidate", {
            "vehicle_type": v.vehicle_type,
            "purpose": v.purpose,
            "operating_order_pin": v.operating_order_pin or "",
            "required_record_items": "|".join(v.required_record_items),
            "denial_grounds": "|".join(v.denial_grounds),
            "tracks": "|".join(v.tracks),
            "created_at": v.created_at,
        })

    # Dedup deterministically (keep last occurrence)
    nd: Dict[str, Dict[str, Any]] = {}
    for n in nodes:
        nd[n["id"]] = n
    ed: Dict[str, Dict[str, Any]] = {}
    for e in edges:
        ed[e["id"]] = e

    nodes_out = [nd[k] for k in sorted(nd.keys())]
    edges_out = [ed[k] for k in sorted(ed.keys())]
    return nodes_out, edges_out

# -----------------------------
# Dashboard (offline HTML)
# -----------------------------

DASH_HTML = """<!doctype html>
<html>
<head>
  <meta charset="utf-8"/>
  <title>LitigationOS — MEEK2/3/4 Run Dashboard</title>
  <style>
    body{font-family:system-ui,Segoe UI,Arial,sans-serif;margin:24px;max-width:1100px}
    .row{display:flex;gap:16px;flex-wrap:wrap}
    .card{border:1px solid #ddd;border-radius:14px;padding:14px;box-shadow:0 1px 4px rgba(0,0,0,.06);flex:1;min-width:320px}
    h1{margin:0 0 8px 0}
    h2{margin:0 0 10px 0;font-size:16px}
    .k{color:#555;font-size:12px}
    .v{font-weight:600}
    table{width:100%;border-collapse:collapse}
    th,td{border-bottom:1px solid #eee;padding:6px 8px;font-size:13px;vertical-align:top}
    th{text-align:left;color:#555}
    .pill{display:inline-block;padding:2px 8px;border-radius:999px;border:1px solid #ddd;font-size:12px;margin-right:6px}
    .sev{font-weight:700}
  </style>
</head>
<body>
  <h1>LitigationOS — MEEK2/3/4 Run Dashboard</h1>
  <div class="k">Open this file after a harvest. It reads <span class="v">run.json</span> in the same folder.</div>
  <hr/>
  <div class="row">
    <div class="card">
      <h2>Run Summary</h2>
      <div id="summary"></div>
    </div>
    <div class="card">
      <h2>Top Risks (highest severity)</h2>
      <table id="risks"><thead><tr><th>Sev</th><th>Risk</th><th>Fastest Cure</th></tr></thead><tbody></tbody></table>
    </div>
  </div>
  <div class="row" style="margin-top:16px">
    <div class="card">
      <h2>Next Clocks (soonest due)</h2>
      <table id="clocks"><thead><tr><th>Due</th><th>Type</th><th>Basis</th></tr></thead><tbody></tbody></table>
    </div>
    <div class="card">
      <h2>Vehicle Candidates</h2>
      <table id="vehicles"><thead><tr><th>Track</th><th>Vehicle</th><th>OperatingOrderPin</th></tr></thead><tbody></tbody></table>
    </div>
  </div>
<script>
async function load(){
  const resp = await fetch("run.json");
  const data = await resp.json();

  const sum = document.getElementById("summary");
  sum.innerHTML = `
    <div><span class="k">run_id</span> <span class="v">${data.run_id}</span></div>
    <div><span class="k">source_root</span> <span class="v">${data.source_root}</span></div>
    <div><span class="k">documents</span> <span class="v">${data.counts.documents}</span> ·
         <span class="k">evidence</span> <span class="v">${data.counts.evidence_atoms}</span> ·
         <span class="k">events</span> <span class="v">${data.counts.event_atoms}</span></div>
    <div><span class="k">clocks</span> <span class="v">${data.counts.deadline_clocks}</span> ·
         <span class="k">risks</span> <span class="v">${data.counts.risk_events}</span> ·
         <span class="k">vehicles</span> <span class="v">${data.counts.vehicle_candidates}</span></div>
    <div style="margin-top:10px">
      ${data.tracks_seen.map(t=>`<span class="pill">${t}</span>`).join("")}
    </div>
  `;

  const risks = data.risk_events.sort((a,b)=>b.severity-a.severity).slice(0,12);
  const rbody = document.querySelector("#risks tbody");
  rbody.innerHTML = risks.map(r => `
    <tr>
      <td class="sev">${r.severity}</td>
      <td><div class="v">${r.title}</div><div class="k">${r.details}</div></td>
      <td>${r.fastest_cure}</td>
    </tr>`).join("");

  const clocks = data.deadline_clocks.sort((a,b)=>a.due_date.localeCompare(b.due_date)).slice(0,12);
  const cbody = document.querySelector("#clocks tbody");
  cbody.innerHTML = clocks.map(c => `
    <tr>
      <td class="v">${c.due_date}</td>
      <td>${c.clock_type}</td>
      <td class="k">${c.basis}</td>
    </tr>`).join("");

  const vbody = document.querySelector("#vehicles tbody");
  vbody.innerHTML = data.vehicle_candidates.slice(0,20).map(v => `
    <tr>
      <td>${v.tracks.join(", ")}</td>
      <td><div class="v">${v.vehicle_type}</div><div class="k">${v.purpose}</div></td>
      <td class="k">${v.operating_order_pin || "MISSING"}</td>
    </tr>`).join("");
}
load().catch(e=>{
  document.body.insertAdjacentHTML("beforeend", "<pre>"+e+"</pre>");
});
</script>
</body>
</html>
"""

# -----------------------------
# Main harvest pipeline
# -----------------------------

def collect_documents(in_root: Path) -> List[Path]:
    exts = {".txt", ".md", ".log", ".json", ".jsonl", ".csv", ".docx", ".pdf"}
    files: List[Path] = []
    for p in in_root.rglob("*"):
        if not p.is_file():
            continue
        if p.suffix.lower() in exts:
            files.append(p)
    files.sort(key=lambda x: str(x).lower())
    return files

def build_document_ref(p: Path, in_root: Path) -> DocumentRef:
    rel = safe_relpath(p, in_root)
    st = p.stat()
    doc_id = "doc:" + sha1_hex(f"DOC|{rel}|{st.st_size}|{int(st.st_mtime)}")
    return DocumentRef(
        doc_id=doc_id,
        rel_path=rel,
        abs_path=str(p.resolve()),
        ext=p.suffix.lower(),
        size_bytes=int(st.st_size),
        mtime_iso=iso_dt(dt.datetime.fromtimestamp(st.st_mtime)),
    )

def harvest(in_root: Path, out_root: Path, operating_order_pin: Optional[str]) -> Path:
    run_id = dt.datetime.now().strftime("%Y%m%d_%H%M%S")
    run_dir = out_root / run_id
    ensure_dir(run_dir)

    docs_paths = collect_documents(in_root)
    docs: List[DocumentRef] = []
    evids: List[EvidenceAtom] = []
    events: List[EventAtom] = []

    for p in docs_paths:
        doc = build_document_ref(p, in_root)
        docs.append(doc)
        text = load_document_text(p)
        if not text or not text.strip():
            continue
        # Extract evidence atoms
        atoms = extract_evidence_atoms(doc, text, in_root)
        evids.extend(atoms)
        # Extract event atoms
        for a in atoms:
            events.extend(extract_event_atoms(a))

    # Dedup events by id
    evd: Dict[str, EventAtom] = {}
    for e in events:
        evd[e.event_id] = e
    events = [evd[k] for k in sorted(evd.keys())]

    # Vehicles, clocks, risks
    vehicles = generate_vehicle_candidates(events, operating_order_pin)
    clocks = compute_clocks(events, DEFAULT_CLOCK_RULES)
    risks = compute_risks(events, clocks, vehicles)

    # Tracks seen
    tracks_seen = sorted({t for e in evids for t in e.tracks} | {t for ev in events for t in ev.tracks} | {t for v in vehicles for t in v.tracks} | {t for c in clocks for t in c.tracks} | {t for r in risks for t in r.tracks})

    # Export graph tables
    nodes, edges = build_nodes_edges(docs, evids, events, clocks, risks, vehicles)

    # Write outputs
    (run_dir / "dash.html").write_text(DASH_HTML, encoding="utf-8")

    # run.json (dashboard payload)
    run_json = {
        "run_id": run_id,
        "created_at": iso_dt(dt.datetime.now()),
        "source_root": str(in_root.resolve()),
        "operating_order_pin": operating_order_pin or "",
        "tracks_seen": tracks_seen,
        "counts": {
            "documents": len(docs),
            "evidence_atoms": len(evids),
            "event_atoms": len(events),
            "deadline_clocks": len(clocks),
            "risk_events": len(risks),
            "vehicle_candidates": len(vehicles),
            "nodes": len(nodes),
            "edges": len(edges),
        },
        "vehicle_candidates": [dataclasses.asdict(v) for v in vehicles],
        "deadline_clocks": [dataclasses.asdict(c) for c in clocks],
        "risk_events": [dataclasses.asdict(r) for r in risks],
    }
    (run_dir / "run.json").write_text(json.dumps(run_json, indent=2), encoding="utf-8")

    # manifest.json
    manifest = {
        "run_id": run_id,
        "inputs": [dataclasses.asdict(d) for d in docs],
        "outputs": ["run.json", "dash.html", "nodes.csv", "edges.csv", "timeline.csv", "risk_report.json"],
        "notes": {
            "determinism": "IDs are sha1 over stable keys; docs keyed by relpath+size+mtime. New mtime changes produce new doc_id.",
            "operating_order_pin_policy": "VehicleCandidates require OperatingOrderPin to be considered valid; missing pins produce RiskEvents.",
        },
    }
    (run_dir / "manifest.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")

    # timeline.csv
    with (run_dir / "timeline.csv").open("w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["date", "kind", "title", "event_id", "tracks", "source_evid_id"])
        for ev in sorted(events, key=lambda e: (e.date or "9999-12-31", e.kind, e.event_id)):
            w.writerow([ev.date or "", ev.kind, ev.title, ev.event_id, "|".join(ev.tracks), ev.source_evid_id or ""])

    # risk_report.json
    risk_sorted = sorted(risks, key=lambda r: (-r.severity, r.risk_class, r.risk_id))
    (run_dir / "risk_report.json").write_text(json.dumps([dataclasses.asdict(r) for r in risk_sorted], indent=2), encoding="utf-8")

    # nodes.csv / edges.csv
    node_fields = sorted({k for n in nodes for k in n.keys()})
    edge_fields = sorted({k for e in edges for k in e.keys()})
    with (run_dir / "nodes.csv").open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=node_fields)
        w.writeheader()
        for n in nodes:
            w.writerow(n)
    with (run_dir / "edges.csv").open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=edge_fields)
        w.writeheader()
        for e in edges:
            w.writerow(e)

    return run_dir

# -----------------------------
# Neo4j upsert (optional)
# -----------------------------

NEO4J_CONSTRAINTS = r"""
CREATE CONSTRAINT doc_id IF NOT EXISTS FOR (n:Document) REQUIRE n.id IS UNIQUE;
CREATE CONSTRAINT evid_id IF NOT EXISTS FOR (n:EvidenceAtom) REQUIRE n.id IS UNIQUE;
CREATE CONSTRAINT event_id IF NOT EXISTS FOR (n:EventAtom) REQUIRE n.id IS UNIQUE;
CREATE CONSTRAINT clock_id IF NOT EXISTS FOR (n:DeadlineClock) REQUIRE n.id IS UNIQUE;
CREATE CONSTRAINT risk_id IF NOT EXISTS FOR (n:RiskEvent) REQUIRE n.id IS UNIQUE;
CREATE CONSTRAINT vehicle_id IF NOT EXISTS FOR (n:VehicleCandidate) REQUIRE n.id IS UNIQUE;
"""

def neo4j_upsert(run_dir: Path) -> None:
    uri = os.environ.get("NEO4J_URI", "").strip()
    user = os.environ.get("NEO4J_USER", "").strip()
    pw = os.environ.get("NEO4J_PASS", "").strip()
    if not (uri and user and pw):
        raise RuntimeError("NEO4J_URI, NEO4J_USER, NEO4J_PASS must be set in environment.")
    try:
        from neo4j import GraphDatabase
    except Exception as e:
        raise RuntimeError("neo4j python driver not installed. Install: pip install neo4j") from e

    nodes_path = run_dir / "nodes.csv"
    edges_path = run_dir / "edges.csv"
    if not nodes_path.exists() or not edges_path.exists():
        raise FileNotFoundError("nodes.csv/edges.csv missing in run dir.")

    # Load CSV into memory (safe for moderate size; if huge, stream + periodic tx)
    with nodes_path.open("r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        nodes = list(reader)
    with edges_path.open("r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        edges = list(reader)

    driver = GraphDatabase.driver(uri, auth=(user, pw))
    with driver.session() as session:
        # constraints
        for stmt in [s.strip() for s in NEO4J_CONSTRAINTS.split(";") if s.strip()]:
            session.run(stmt)

        # nodes upsert
        # We store id + label as labels; remaining keys as props
        for n in nodes:
            node_id = n.get("id")
            label = n.get("label") or "Node"
            props = {k: v for k, v in n.items() if k not in ("id", "label")}
            q = f"""
            MERGE (x:`{label}` {{id: $id}})
            SET x += $props
            """
            session.run(q, id=node_id, props=props)

        # edges upsert
        for e in edges:
            edge_id = e.get("id")
            src = e.get("src"); dst = e.get("dst"); rel = e.get("rel") or "RELATED_TO"
            props = {k: v for k, v in e.items() if k not in ("id", "src", "dst", "rel")}
            q = f"""
            MATCH (a {{id: $src}})
            MATCH (b {{id: $dst}})
            MERGE (a)-[r:`{rel}` {{id: $id}}]->(b)
            SET r += $props
            """
            session.run(q, id=edge_id, src=src, dst=dst, props=props)

    driver.close()

# -----------------------------
# Serve dashboard
# -----------------------------

def serve(run_dir: Path, host: str, port: int) -> None:
    import http.server
    import socketserver
    os.chdir(str(run_dir))
    handler = http.server.SimpleHTTPRequestHandler
    with socketserver.TCPServer((host, port), handler) as httpd:
        print(f"Serving {run_dir} at http://{host}:{port}/dash.html")
        httpd.serve_forever()

# -----------------------------
# CLI
# -----------------------------

def cmd_harvest(args: argparse.Namespace) -> int:
    in_root = Path(args.in_path).expanduser().resolve()
    out_root = Path(args.out_root).expanduser().resolve()
    ensure_dir(out_root)
    if not in_root.exists():
        print(f"ERROR: input path does not exist: {in_root}", file=sys.stderr)
        return 2
    run_dir = harvest(in_root, out_root, args.operating_order_pin)
    print(str(run_dir))
    return 0

def cmd_serve(args: argparse.Namespace) -> int:
    run_dir = Path(args.run).expanduser().resolve()
    if not run_dir.exists():
        print(f"ERROR: run dir does not exist: {run_dir}", file=sys.stderr)
        return 2
    serve(run_dir, args.host, args.port)
    return 0

def cmd_neo4j(args: argparse.Namespace) -> int:
    run_dir = Path(args.run).expanduser().resolve()
    try:
        neo4j_upsert(run_dir)
        print("Neo4j upsert completed.")
        return 0
    except Exception as e:
        print(f"ERROR: {e}", file=sys.stderr)
        return 2

def main() -> int:
    ap = argparse.ArgumentParser(
        prog="MEEK234_FULLSTACK_REBUILD",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        description=__doc__,
    )
    sub = ap.add_subparsers(dest="cmd", required=True)

    p_h = sub.add_parser("harvest", help="Harvest a folder into a new run pack.")
    p_h.add_argument("--in", dest="in_path", required=True, help="Input folder (Litigation_Intake mirror).")
    p_h.add_argument("--out-root", dest="out_root", required=True, help="Output root folder for runs/<timestamp>.")
    p_h.add_argument("--operating-order-pin", dest="operating_order_pin", default=None, help="Optional: pin controlling order id/reference.")
    p_h.set_defaults(func=cmd_harvest)

    p_s = sub.add_parser("serve", help="Serve a run dashboard locally (dash.html).")
    p_s.add_argument("--run", required=True, help="Run folder path (contains run.json).")
    p_s.add_argument("--host", default="127.0.0.1", help="Host to bind.")
    p_s.add_argument("--port", type=int, default=8899, help="Port to bind.")
    p_s.set_defaults(func=cmd_serve)

    p_n = sub.add_parser("neo4j-upsert", help="Optional: upsert nodes/edges into Neo4j (requires neo4j python driver).")
    p_n.add_argument("--run", required=True, help="Run folder path (contains nodes.csv/edges.csv).")
    p_n.set_defaults(func=cmd_neo4j)

    args = ap.parse_args()
    return int(args.func(args))

if __name__ == "__main__":
    raise SystemExit(main())
