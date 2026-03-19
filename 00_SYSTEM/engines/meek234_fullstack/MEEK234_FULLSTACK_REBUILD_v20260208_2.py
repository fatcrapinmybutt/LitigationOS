#!/usr/bin/env python3
"""
MEEK2 + MEEK3 + MEEK4 — Full Stack Rebuild (v2026-02-08_2)

Purpose
- Harvest an intake folder into typed atoms (EvidenceAtom/EventAtom)
- Compute clocks, risk events, and vehicle candidates
- Enforce Operating Order Pin expectation (emit risk when missing)
- Export Neo4j-friendly nodes/edges + a lightweight HTML dashboard
- Run deterministic multi-pass refinement until convergence (digest stable)

Design goals
- Deterministic IDs and outputs
- Fail-soft: always produces artifacts; gaps become explicit RiskEvents
- Catalog-first: risk/vehicle/schema catalogs load from ./catalogs and ./schema when present

Dependencies (optional; script degrades gracefully):
- python-docx (docx)
- pypdf (pdf text extraction)
- openpyxl (xlsx)
"""

from __future__ import annotations

import argparse
import csv
import dataclasses
import datetime as dt
import hashlib
import io
import json
import os
import re
import sys
import textwrap
import zlib
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Tuple

# -----------------------------
# Constants / Defaults
# -----------------------------

TRACKS = ("MEEK2", "MEEK3", "MEEK4")

RISK_CLASSES = (
    "jurisdictional_fatal",
    "admin_return_without_docketing",
    "curable_defect",
    "dismissal_risk",
    "record_incomplete",
    "discretionary_sanction_risk",
)

EVENT_KINDS = (
    "OrderEvent",
    "ServiceEvent",
    "HearingEvent",
    "FilingEvent",
    "CommunicationEvent",
    "ClerkNoticeEvent",
)

DEFAULT_TRACK_KEYWORDS: Dict[str, List[str]] = {
    "MEEK2": [
        "custody", "parenting time", "foc", "friend of the court", "child support",
        "support order", "mcsf", "overpayment", "overnights", "change of circumstances",
        "best interests", "domestic relations", "parent-time", "parent time",
    ],
    "MEEK3": [
        "ppo", "personal protection order", "show cause", "show-cause", "contempt",
        "mittimus", "violation", "restraining", "stalking", "harassing", "harassment",
        "no contact", "bond", "jail", "sentence",
    ],
    "MEEK4": [
        "judge", "disqual", "disqualification", "recus", "recusal", "bias",
        "chief judge", "canon", "misconduct", "superintending control", "mandamus",
        "prohibition", "judicial tenure commission", "jtc",
    ],
}

# Event rules: (kind, keywords-any, title)
DEFAULT_EVENT_RULES: List[Tuple[str, List[str], str]] = [
    ("ClerkNoticeEvent", ["returned", "return without docketing", "rejected", "defect", "notice", "clerk", "warning", "late-filed", "refuse to accept"], "Clerk Notice / Defect"),
    ("OrderEvent", ["order", "opinion and order", "judgment", "stipulated order", "entered", "signed", "amended order"], "Order / Opinion"),
    ("ServiceEvent", ["served", "service", "proof of service", "personal service", "certified mail", "mailing", "return of service"], "Service / Proof"),
    ("HearingEvent", ["hearing", "conference", "trial", "show cause", "show-cause", "oral argument"], "Hearing / Proceeding"),
    ("FilingEvent", ["filed", "motion", "petition", "application", "brief", "claim of appeal", "appeal", "notice of appeal", "docketing statement"], "Filing / Motion"),
    ("CommunicationEvent", ["email", "text", "call", "voicemail", "appclose", "ourfamilywizard", "co-parent", "message"], "Communication"),
]

# Default clock rules (minimal; extend via catalogs)
DEFAULT_CLOCK_RULES: List[Dict[str, Any]] = [
    {
        "clock_id": "RECONSIDERATION_21D",
        "title": "Reconsideration deadline (21 days after order deciding motion)",
        "trigger_kind_any": ["OrderEvent"],
        "trigger_kw_any": ["order", "opinion"],
        "days_after": 21,
        "tracks": ["MEEK2", "MEEK3", "MEEK4"],
    },
    {
        "clock_id": "DISQUAL_14D",
        "title": "Disqualification motion timeliness (14 days after discovery/assignment)",
        "trigger_kind_any": ["Event"],
        "trigger_kw_any": ["assignment", "discovered", "disqual", "recusal", "bias"],
        "days_after": 14,
        "tracks": ["MEEK4"],
    },
    {
        "clock_id": "COA_DOCKETING_STATEMENT_28D",
        "title": "COA docketing statement (28 days after claim of appeal)",
        "trigger_kind_any": ["FilingEvent"],
        "trigger_kw_any": ["claim of appeal"],
        "days_after": 28,
        "tracks": ["MEEK4", "MEEK3"],
    },
    {
        "clock_id": "COA_CLAIM_OF_APPEAL_21D",
        "title": "Claim of appeal (21 days after entry of order/judgment in typical civil appeal of right)",
        "trigger_kind_any": ["OrderEvent"],
        "trigger_kw_any": ["order", "judgment"],
        "days_after": 21,
        "tracks": ["MEEK4", "MEEK3"],
    },
]

# -----------------------------
# Dataclasses (typed atoms)
# -----------------------------

@dataclasses.dataclass(frozen=True)
class DocumentRef:
    doc_id: str
    rel_path: str
    abs_path: str
    mtime_iso: str
    size_bytes: int
    integrity_key: str

@dataclasses.dataclass(frozen=True)
class EvidenceAtom:
    evid_id: str
    doc_id: str
    rel_path: str
    span_start: int
    span_end: int
    quote: str
    text: str
    tracks: Tuple[str, ...]
    created_at: str

@dataclasses.dataclass(frozen=True)
class EventAtom:
    event_id: str
    kind: str
    date: Optional[str]
    title: str
    details: str
    tracks: Tuple[str, ...]
    source_evid_id: str
    created_at: str

@dataclasses.dataclass(frozen=True)
class DeadlineClock:
    clock_id: str
    title: str
    start_date: Optional[str]
    due_date: Optional[str]
    trigger_event_id: Optional[str]
    tracks: Tuple[str, ...]
    created_at: str

@dataclasses.dataclass(frozen=True)
class RiskEvent:
    risk_id: str
    risk_type_id: str
    risk_class: str
    severity: int
    title: str
    details: str
    related_ids: Tuple[str, ...]
    fastest_cure: str
    cure_cost: str
    cure_deadline_clock: Optional[str]
    cure_minimum_packet: Tuple[str, ...]
    tracks: Tuple[str, ...]
    authority_refs: Tuple[str, ...]
    created_at: str

@dataclasses.dataclass(frozen=True)
class VehicleCandidate:
    vehicle_id: str
    vehicle_type_id: str
    vehicle_type: str
    purpose: str
    operating_order_pin: Optional[str]  # order_id / event_id / external ref
    required_record_items: Tuple[str, ...]
    denial_grounds: Tuple[str, ...]
    tracks: Tuple[str, ...]
    authority_refs: Tuple[str, ...]
    created_at: str

@dataclasses.dataclass(frozen=True)
class OperatingOrderPin:
    pin_id: str
    order_event_id: str
    date: Optional[str]
    status: str  # effective|stayed|superseded|unknown
    rationale: str
    tracks: Tuple[str, ...]
    created_at: str

# -----------------------------
# Deterministic helpers
# -----------------------------

def iso_dt(x: dt.datetime) -> str:
    return x.replace(microsecond=0).isoformat()

def sha256_bytes(b: bytes) -> str:
    return hashlib.sha256(b).hexdigest()

def sha256_text(s: str) -> str:
    return sha256_bytes(s.encode("utf-8", errors="ignore"))

def crc32_bytes(b: bytes) -> str:
    return f"{zlib.crc32(b) & 0xffffffff:08x}"

def integrity_key(bundle_uid: str, entry_rel: str, b: bytes, mtime: float) -> str:
    # IntegrityKey(BundleUID+EntryPath+CRC32+bytes+mtime)
    return f"IK:{bundle_uid}:{entry_rel}:{crc32_bytes(b)}:{len(b)}:{int(mtime)}"

def stable_id(prefix: str, *parts: str) -> str:
    return f"{prefix}_{sha256_text('|'.join(parts))[:20]}"

def safe_mkdir(p: Path) -> None:
    p.mkdir(parents=True, exist_ok=True)

def write_json(path: Path, obj: Any) -> None:
    path.write_text(json.dumps(obj, indent=2, ensure_ascii=False), encoding="utf-8")

def write_jsonl(path: Path, items: Iterable[Any]) -> None:
    with open(path, "w", encoding="utf-8") as f:
        for it in items:
            f.write(json.dumps(dataclasses.asdict(it) if dataclasses.is_dataclass(it) else it, ensure_ascii=False) + "\n")

def read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))

# -----------------------------
# File readers (best-effort)
# -----------------------------

def read_text_file(p: Path) -> str:
    try:
        return p.read_text(encoding="utf-8")
    except UnicodeDecodeError:
        return p.read_text(encoding="latin-1", errors="ignore")

def read_docx_file(p: Path) -> Optional[str]:
    try:
        import docx  # python-docx
        d = docx.Document(str(p))
        parts = []
        for para in d.paragraphs:
            t = (para.text or "").strip()
            if t:
                parts.append(t)
        return "\n".join(parts)
    except Exception:
        return None

def read_pdf_file(p: Path) -> Optional[str]:
    try:
        from pypdf import PdfReader
        reader = PdfReader(str(p))
        chunks = []
        for page in reader.pages:
            txt = page.extract_text() or ""
            if txt.strip():
                chunks.append(txt)
        out = "\n".join(chunks).strip()
        return out if out else None
    except Exception:
        return None

def read_xlsx_file(p: Path, max_rows: int = 2000) -> Optional[str]:
    try:
        import openpyxl
        wb = openpyxl.load_workbook(str(p), read_only=True, data_only=True)
        lines = []
        for ws in wb.worksheets:
            lines.append(f"[SHEET] {ws.title}")
            row_count = 0
            for row in ws.iter_rows(values_only=True):
                row_count += 1
                if row_count > max_rows:
                    lines.append(f"[TRUNCATED] {ws.title} after {max_rows} rows")
                    break
                vals = []
                for v in row:
                    if v is None:
                        vals.append("")
                    else:
                        s = str(v).strip()
                        vals.append(s)
                if any(x for x in vals):
                    lines.append(" | ".join(vals))
        out = "\n".join(lines).strip()
        return out if out else None
    except Exception:
        return None

def read_csv_file(p: Path, max_lines: int = 5000) -> Optional[str]:
    try:
        txt = p.read_text(encoding="utf-8", errors="ignore")
        # keep as-is; avoid exploding separators
        lines = txt.splitlines()[:max_lines]
        return "\n".join(lines)
    except Exception:
        return None

def read_jsonish_file(p: Path, max_chars: int = 2_000_000) -> Optional[str]:
    try:
        raw = p.read_text(encoding="utf-8", errors="ignore")
        raw = raw[:max_chars]
        # Normalize into "key: value" style lines for evidence chunking
        obj = json.loads(raw)
        return json.dumps(obj, indent=2, ensure_ascii=False)
    except Exception:
        return None

def read_file_best_effort(p: Path) -> Optional[str]:
    suf = p.suffix.lower()
    if suf in [".txt", ".md", ".log"]:
        return read_text_file(p)
    if suf in [".json"]:
        return read_jsonish_file(p)
    if suf in [".jsonl", ".ndjson"]:
        return read_text_file(p)
    if suf in [".csv", ".tsv"]:
        return read_csv_file(p)
    if suf in [".docx"]:
        return read_docx_file(p)
    if suf in [".pdf"]:
        return read_pdf_file(p)
    if suf in [".xlsx", ".xlsm"]:
        return read_xlsx_file(p)
    return None

# -----------------------------
# Parsing helpers (dates, tracks)
# -----------------------------

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

DATE_PATTERNS = [
    # YYYY-MM-DD
    re.compile(r"\b(20\d{2})-(\d{1,2})-(\d{1,2})\b"),
    # MM/DD/YYYY or M/D/YY
    re.compile(r"\b(\d{1,2})/(\d{1,2})/(\d{2,4})\b"),
    # Month DD, YYYY
    re.compile(r"\b([A-Za-z]{3,9})\s+(\d{1,2}),\s*(\d{4})\b"),
]

def find_dates(text: str) -> List[str]:
    cands: List[str] = []
    for pat in DATE_PATTERNS:
        for m in pat.finditer(text):
            try:
                if pat.pattern.startswith(r"\b(20"):
                    y = int(m.group(1)); mo = int(m.group(2)); d = int(m.group(3))
                elif "/" in pat.pattern:
                    mo = int(m.group(1)); d = int(m.group(2))
                    yraw = m.group(3)
                    y = int(yraw) if len(yraw) == 4 else 2000 + int(yraw)
                else:
                    mon = m.group(1).lower().strip(".")
                    mon3 = mon[:3]
                    mo = MONTHS.get(mon, MONTHS.get(mon3))
                    d = int(m.group(2)); y = int(m.group(3))
                    if mo is None:
                        continue
                dd = dt.date(y, mo, d)
                cands.append(dd.isoformat())
            except Exception:
                continue
    # stable unique order
    out, seen = [], set()
    for x in cands:
        if x not in seen:
            out.append(x); seen.add(x)
    return out

CASE_ID_PAT = re.compile(r"\b(\d{4}-\d{7,}-[A-Z]{1,4})\b")

def infer_case_ids(text: str) -> List[str]:
    out, seen = [], set()
    for m in CASE_ID_PAT.finditer(text.upper()):
        cid = m.group(1)
        if cid not in seen:
            out.append(cid); seen.add(cid)
    return out

def tag_tracks(text: str, track_keywords: Dict[str, List[str]]) -> Tuple[str, ...]:
    t = text.lower()
    tracks = set()

    # case-id hints
    cids = infer_case_ids(text)
    for cid in cids:
        if cid.endswith("-PP") or cid.endswith("-PO") or cid.endswith("-PPO"):
            tracks.add("MEEK3")
        if cid.endswith("-DC") or cid.endswith("-DS"):
            tracks.add("MEEK2")

    for tr, kws in track_keywords.items():
        if any(k.lower() in t for k in kws):
            tracks.add(tr)

    return tuple(sorted(tracks))

# -----------------------------
# Harvest: documents -> evidence atoms
# -----------------------------

def scan_documents(intake: Path, exts: Tuple[str, ...]) -> List[Path]:
    files: List[Path] = []
    for p in intake.rglob("*"):
        if p.is_file() and p.suffix.lower() in exts:
            files.append(p)
    files.sort(key=lambda x: str(x).lower())
    return files

def build_document_ref(intake: Path, p: Path, bundle_uid: str) -> Tuple[DocumentRef, bytes]:
    b = p.read_bytes()
    rel = str(p.relative_to(intake)).replace("\\", "/")
    st = p.stat()
    ik = integrity_key(bundle_uid, rel, b, st.st_mtime)
    doc_id = stable_id("DOC", bundle_uid, rel, ik)
    return DocumentRef(
        doc_id=doc_id,
        rel_path=rel,
        abs_path=str(p),
        mtime_iso=iso_dt(dt.datetime.fromtimestamp(st.st_mtime)),
        size_bytes=int(st.st_size),
        integrity_key=ik,
    ), b

def chunk_paragraphs(text: str) -> List[Tuple[int, int, str]]:
    # returns (start,end,chunk_text) using offset indices
    chunks: List[Tuple[int,int,str]] = []
    # normalize newlines
    s = text.replace("\r\n", "\n").replace("\r", "\n")
    parts = re.split(r"\n{2,}", s)
    offset = 0
    for part in parts:
        part_stripped = part.strip()
        if not part_stripped:
            offset += len(part) + 2
            continue
        # find span
        start = s.find(part, offset)
        if start < 0:
            start = offset
        end = start + len(part)
        chunks.append((start, end, part_stripped))
        offset = end
    return chunks

def build_evidence_atoms(doc: DocumentRef, text: str, track_keywords: Dict[str, List[str]], max_atoms: int = 500) -> List[EvidenceAtom]:
    created = iso_dt(dt.datetime.now())
    atoms: List[EvidenceAtom] = []
    for (start, end, chunk) in chunk_paragraphs(text)[:max_atoms]:
        quote = chunk.strip().replace("\n", " ")
        quote = quote[:220] + ("…" if len(quote) > 220 else "")
        tracks = tag_tracks(chunk, track_keywords)
        evid_id = stable_id("EVID", doc.doc_id, str(start), str(end), sha256_text(chunk))
        atoms.append(EvidenceAtom(
            evid_id=evid_id,
            doc_id=doc.doc_id,
            rel_path=doc.rel_path,
            span_start=int(start),
            span_end=int(end),
            quote=quote,
            text=chunk,
            tracks=tracks,
            created_at=created,
        ))
    return atoms

# -----------------------------
# Evidence -> Events
# -----------------------------

def extract_events(evid_atoms: List[EvidenceAtom], event_rules: List[Tuple[str, List[str], str]], track_keywords: Dict[str, List[str]]) -> List[EventAtom]:
    created = iso_dt(dt.datetime.now())
    events: List[EventAtom] = []
    for ev in evid_atoms:
        t = ev.text.lower()
        date = find_dates(ev.text)[0] if find_dates(ev.text) else None

        kind = None
        title = None
        for k, kws, ttl in event_rules:
            if any(kw.lower() in t for kw in kws):
                kind = k
                title = ttl
                break
        if kind is None:
            continue

        tracks = tag_tracks(ev.text, track_keywords)
        # Prefer explicit track tags from evid if present
        merged_tracks = tuple(sorted(set(tracks) | set(ev.tracks)))

        details = ev.text.strip()
        event_id = stable_id("EVT", kind, ev.evid_id, date or "NA", sha256_text(details[:500]))
        events.append(EventAtom(
            event_id=event_id,
            kind=kind,
            date=date,
            title=title or kind,
            details=details[:2000],  # keep manageable
            tracks=merged_tracks,
            source_evid_id=ev.evid_id,
            created_at=created,
        ))
    return events

# -----------------------------
# Operating Order Pin Resolver
# -----------------------------

def select_operating_order_pin(events: List[EventAtom], tracks: Tuple[str, ...]) -> Optional[OperatingOrderPin]:
    """
    Heuristic:
    - Pick the newest OrderEvent that matches track context.
    - If none, return None.
    """
    created = iso_dt(dt.datetime.now())
    order_events = [e for e in events if e.kind == "OrderEvent"]
    if not order_events:
        return None

    # Score by (has date, date, track overlap, keywords)
    def score(e: EventAtom) -> Tuple[int, str, int, int]:
        d = e.date or "0000-00-00"
        overlap = len(set(tracks) & set(e.tracks))
        kw = 1 if any(x in e.details.lower() for x in ["order", "judgment", "opinion", "stipulated"]) else 0
        has_date = 1 if e.date else 0
        return (has_date, d, overlap, kw)

    best = sorted(order_events, key=score, reverse=True)[0]
    pin_id = stable_id("OOP", best.event_id, ",".join(tracks))
    return OperatingOrderPin(
        pin_id=pin_id,
        order_event_id=best.event_id,
        date=best.date,
        status="unknown",
        rationale=f"Selected newest OrderEvent by heuristic; tracks={','.join(tracks) or 'NONE'}",
        tracks=tracks,
        created_at=created,
    )

# -----------------------------
# Clock engine
# -----------------------------

def add_days(date_iso: str, days: int) -> Optional[str]:
    try:
        y, m, d = [int(x) for x in date_iso.split("-")]
        base = dt.date(y, m, d)
        due = base + dt.timedelta(days=days)
        return due.isoformat()
    except Exception:
        return None

def compute_clocks(events: List[EventAtom], clock_rules: List[Dict[str, Any]]) -> List[DeadlineClock]:
    created = iso_dt(dt.datetime.now())
    clocks: List[DeadlineClock] = []
    for rule in clock_rules:
        days_after = int(rule.get("days_after", 0))
        trigger_kind_any = set(rule.get("trigger_kind_any", []))
        trigger_kw_any = [k.lower() for k in rule.get("trigger_kw_any", [])]
        rule_tracks = tuple(sorted(set(rule.get("tracks", []))))
        for e in events:
            if trigger_kind_any and e.kind not in trigger_kind_any and "Event" not in trigger_kind_any:
                continue
            t = (e.title + " " + e.details).lower()
            if trigger_kw_any and not any(k in t for k in trigger_kw_any):
                continue
            if rule_tracks and not (set(rule_tracks) & set(e.tracks)):
                continue
            if not e.date:
                continue
            due = add_days(e.date, days_after)
            clock_id = stable_id("CLK", rule["clock_id"], e.event_id, e.date)
            clocks.append(DeadlineClock(
                clock_id=clock_id,
                title=rule["title"],
                start_date=e.date,
                due_date=due,
                trigger_event_id=e.event_id,
                tracks=tuple(sorted(set(rule_tracks) | set(e.tracks))),
                created_at=created,
            ))
    # de-dup
    dedup: Dict[str, DeadlineClock] = {}
    for c in clocks:
        dedup[c.clock_id] = c
    return list(dedup.values())

# -----------------------------
# Catalog loaders (risk/vehicle)
# -----------------------------

def load_catalog_json(path: Path) -> Optional[Any]:
    try:
        if path.exists():
            return read_json(path)
    except Exception:
        return None
    return None

def normalize_risk_catalog(raw: Any) -> List[Dict[str, Any]]:
    if not isinstance(raw, list):
        return []
    out = []
    for it in raw:
        if not isinstance(it, dict):
            continue
        if "risk_type_id" in it and "risk_class" in it and "title" in it:
            out.append(it)
    return out

def normalize_vehicle_catalog(raw: Any) -> List[Dict[str, Any]]:
    if not isinstance(raw, list):
        return []
    out = []
    for it in raw:
        if not isinstance(it, dict):
            continue
        if "vehicle_type_id" in it and "vehicle_type" in it:
            out.append(it)
    return out

# -----------------------------
# Risk engine (catalog-driven)
# -----------------------------

def compute_risks(events: List[EventAtom], clocks: List[DeadlineClock], operating_pin_by_track: Dict[str, Optional[OperatingOrderPin]], risk_catalog: List[Dict[str, Any]]) -> List[RiskEvent]:
    created = iso_dt(dt.datetime.now())
    clock_ids = {c.title: c.clock_id for c in clocks}
    text_blob = " ".join((e.title + " " + e.details) for e in events).lower()

    # helper to check followups
    def has_text(sub: str) -> bool:
        return sub.lower() in text_blob

    risks: List[RiskEvent] = []

    # operating order pin missing risks (per track)
    for tr in TRACKS:
        pin = operating_pin_by_track.get(tr)
        if pin is None:
            rid = stable_id("RISK", "MISSING_OPERATING_ORDER_PIN", tr)
            risks.append(RiskEvent(
                risk_id=rid,
                risk_type_id="MISSING_OPERATING_ORDER_PIN",
                risk_class="record_incomplete",
                severity=90,
                title=f"Missing Operating Order Pin ({tr})",
                details="No controlling/operative order could be pinned from extracted OrderEvents. Add ROA/order copy or define pin override.",
                related_ids=tuple(),
                fastest_cure="Add the operative order document/ROA entry; or supply --operating-order-pin-override JSON mapping.",
                cure_cost="low",
                cure_deadline_clock=None,
                cure_minimum_packet=("Operative order copy", "ROA entry showing entry date", "Service proof if available"),
                tracks=(tr,),
                authority_refs=tuple(),
                created_at=created,
            ))

    # catalog risks
    for rt in risk_catalog:
        try:
            rtype = rt["risk_type_id"]
            rclass = rt["risk_class"]
            severity = int(rt.get("severity", 50))
            title = rt["title"]
            fastest_cure = rt.get("fastest_cure", "")
            cure_cost = rt.get("cure_cost", "unknown")
            cure_deadline_clock = rt.get("cure_deadline_clock")
            cure_min_packet = tuple(rt.get("cure_minimum_packet", []))
            tracks = tuple(rt.get("tracks", []))
            auth = tuple(rt.get("authority_refs", []))

            trig = rt.get("trigger", {}) or {}
            event_kind = trig.get("event_kind")
            must_any = [x.lower() for x in trig.get("must_contain_any", [])]
            must_not = [x.lower() for x in trig.get("must_not_contain_any", [])]
            missing_followup = trig.get("missing_followup")

            matched_event_ids: List[str] = []
            for e in events:
                if event_kind and e.kind != event_kind:
                    continue
                txt = (e.title + " " + e.details).lower()
                if must_any and not any(x in txt for x in must_any):
                    continue
                if must_not and any(x in txt for x in must_not):
                    continue
                if tracks and not (set(tracks) & set(e.tracks)):
                    continue
                if missing_followup and has_text(missing_followup):
                    continue
                matched_event_ids.append(e.event_id)

            if matched_event_ids:
                rid = stable_id("RISK", rtype, "|".join(sorted(matched_event_ids))[:200])
                details = f"Triggered by {len(matched_event_ids)} event(s): {', '.join(matched_event_ids[:5])}" + ("…" if len(matched_event_ids) > 5 else "")
                risks.append(RiskEvent(
                    risk_id=rid,
                    risk_type_id=rtype,
                    risk_class=rclass if rclass in RISK_CLASSES else "curable_defect",
                    severity=severity,
                    title=title,
                    details=details,
                    related_ids=tuple(matched_event_ids[:25]),
                    fastest_cure=fastest_cure,
                    cure_cost=cure_cost,
                    cure_deadline_clock=cure_deadline_clock,
                    cure_minimum_packet=cure_min_packet,
                    tracks=tracks if tracks else tuple(sorted(set().union(*[e.tracks for e in events]))),
                    authority_refs=auth,
                    created_at=created,
                ))
        except Exception:
            continue

    # de-dup by risk_id
    dedup: Dict[str, RiskEvent] = {}
    for r in risks:
        dedup[r.risk_id] = r
    return list(dedup.values())

# -----------------------------
# Vehicle generator (catalog-driven)
# -----------------------------

def build_vehicle_candidates(operating_pin_by_track: Dict[str, Optional[OperatingOrderPin]], vehicle_catalog: List[Dict[str, Any]]) -> List[VehicleCandidate]:
    created = iso_dt(dt.datetime.now())
    vehicles: List[VehicleCandidate] = []
    for vt in vehicle_catalog:
        try:
            vtid = vt["vehicle_type_id"]
            vtype = vt["vehicle_type"]
            purpose = vt.get("purpose", "")
            req = tuple(vt.get("required_record_items", []))
            denial = tuple(vt.get("denial_grounds", []))
            tracks = tuple(vt.get("tracks", []))
            auth = tuple(vt.get("authority_refs", []))

            # choose operating pin by first track
            pin = None
            for tr in tracks:
                if operating_pin_by_track.get(tr) is not None:
                    pin = operating_pin_by_track[tr].order_event_id
                    break

            vid = stable_id("VEH", vtid, pin or "MISSING")
            vehicles.append(VehicleCandidate(
                vehicle_id=vid,
                vehicle_type_id=vtid,
                vehicle_type=vtype,
                purpose=purpose,
                operating_order_pin=pin,
                required_record_items=req,
                denial_grounds=denial,
                tracks=tracks,
                authority_refs=auth,
                created_at=created,
            ))
        except Exception:
            continue
    return vehicles

# -----------------------------
# Graph export
# -----------------------------

def export_graph(run_dir: Path,
                 docs: List[DocumentRef],
                 evid: List[EvidenceAtom],
                 events: List[EventAtom],
                 clocks: List[DeadlineClock],
                 risks: List[RiskEvent],
                 vehicles: List[VehicleCandidate],
                 pins: List[OperatingOrderPin]) -> Tuple[Path, Path]:

    nodes_path = run_dir / "graph_nodes.csv"
    edges_path = run_dir / "graph_edges.csv"

    node_rows: List[Dict[str, Any]] = []
    edge_rows: List[Dict[str, Any]] = []

    def add_node(node_id: str, ntype: str, **props: Any) -> None:
        row = {"id": node_id, "type": ntype}
        row.update(props)
        node_rows.append(row)

    def add_edge(edge_type: str, from_id: str, to_id: str, **props: Any) -> None:
        row = {"type": edge_type, "from": from_id, "to": to_id}
        row.update(props)
        edge_rows.append(row)

    # Nodes: documents
    for d in docs:
        add_node(d.doc_id, "Document", rel_path=d.rel_path, mtime_iso=d.mtime_iso, size_bytes=d.size_bytes, integrity_key=d.integrity_key)

    # Nodes: evidence
    for e in evid:
        add_node(e.evid_id, "EvidenceAtom", rel_path=e.rel_path, span_start=e.span_start, span_end=e.span_end, quote=e.quote, tracks="|".join(e.tracks))
        add_edge("EVID_IN_DOC", e.evid_id, e.doc_id)

    # Nodes: events
    for ev in events:
        add_node(ev.event_id, "Event", kind=ev.kind, date=ev.date or "", title=ev.title, tracks="|".join(ev.tracks))
        add_edge("EVENT_DERIVED_FROM", ev.event_id, ev.source_evid_id)

    # Nodes: pins
    for pin in pins:
        add_node(pin.pin_id, "OperatingOrderPin", order_event_id=pin.order_event_id, date=pin.date or "", status=pin.status, tracks="|".join(pin.tracks))
        add_edge("PIN_POINTS_TO", pin.pin_id, pin.order_event_id)

    # Nodes: clocks
    for c in clocks:
        add_node(c.clock_id, "DeadlineClock", title=c.title, start_date=c.start_date or "", due_date=c.due_date or "", tracks="|".join(c.tracks))
        if c.trigger_event_id:
            add_edge("CLOCK_TRIGGERED_BY", c.clock_id, c.trigger_event_id)

    # Nodes: risks
    for r in risks:
        add_node(r.risk_id, "RiskEvent", risk_type_id=r.risk_type_id, risk_class=r.risk_class, severity=r.severity, title=r.title, tracks="|".join(r.tracks))
        for rel in r.related_ids:
            add_edge("RISK_RAISED_BY", r.risk_id, rel)
        # authority refs stored as props; optionally edges later

    # Nodes: vehicles
    for v in vehicles:
        add_node(v.vehicle_id, "VehicleCandidate", vehicle_type=v.vehicle_type, vehicle_type_id=v.vehicle_type_id, operating_order_pin=v.operating_order_pin or "MISSING", tracks="|".join(v.tracks))
        if v.operating_order_pin:
            add_edge("VEHICLE_REQUIRES_ORDER_PIN", v.vehicle_id, v.operating_order_pin)

    # write CSV (union headers)
    def write_rows(path: Path, rows: List[Dict[str, Any]]) -> None:
        keys = set()
        for r in rows:
            keys |= set(r.keys())
        headers = ["id","type","from","to"]  # not all used
        rest = [k for k in sorted(keys) if k not in headers]
        # For nodes: id,type,... ; For edges: type,from,to,...
        with open(path, "w", newline="", encoding="utf-8") as f:
            w = csv.writer(f)
            w.writerow(headers + rest)
            for r in rows:
                w.writerow([r.get(h,"") for h in headers] + [r.get(k,"") for k in rest])

    write_rows(nodes_path, [r for r in node_rows if "id" in r])
    write_rows(edges_path, [r for r in edge_rows if "from" in r])

    return nodes_path, edges_path

# -----------------------------
# HTML dashboard
# -----------------------------

def build_html_dashboard(run_dir: Path,
                         docs: List[DocumentRef],
                         evid: List[EvidenceAtom],
                         events: List[EventAtom],
                         clocks: List[DeadlineClock],
                         risks: List[RiskEvent],
                         vehicles: List[VehicleCandidate],
                         pins: List[OperatingOrderPin],
                         convergence: List[Dict[str, Any]]) -> Path:
    def esc(s: str) -> str:
        return (s or "").replace("&","&amp;").replace("<","&lt;").replace(">","&gt;")

    html = []
    html.append("<html><head><meta charset='utf-8'/>")
    html.append("<style>body{font-family:Arial,Helvetica,sans-serif;margin:18px;} table{border-collapse:collapse;width:100%;} th,td{border:1px solid #ddd;padding:6px;vertical-align:top;} th{background:#f2f2f2;} .k{font-family:ui-monospace,Consolas,monospace;} .tag{display:inline-block;border:1px solid #999;border-radius:9px;padding:2px 8px;margin:2px;font-size:12px;} </style>")
    html.append("</head><body>")
    html.append("<h1>MEEK234 — Run Dashboard</h1>")
    html.append(f"<p class='k'>run_dir: {esc(str(run_dir))}</p>")
    html.append("<h2>Counts</h2>")
    html.append("<ul>")
    html.append(f"<li>Documents: <b>{len(docs)}</b></li>")
    html.append(f"<li>Evidence atoms: <b>{len(evid)}</b></li>")
    html.append(f"<li>Events: <b>{len(events)}</b></li>")
    html.append(f"<li>Operating order pins: <b>{len(pins)}</b></li>")
    html.append(f"<li>Clocks: <b>{len(clocks)}</b></li>")
    html.append(f"<li>Risks: <b>{len(risks)}</b></li>")
    html.append(f"<li>Vehicle candidates: <b>{len(vehicles)}</b></li>")
    html.append("</ul>")

    html.append("<h2>Convergence log</h2>")
    html.append("<table><tr><th>pass</th><th>digest</th><th>delta</th><th>notes</th></tr>")
    for row in convergence:
        html.append("<tr>")
        html.append(f"<td class='k'>{row.get('pass')}</td>")
        html.append(f"<td class='k'>{esc(row.get('digest',''))}</td>")
        html.append(f"<td class='k'>{esc(str(row.get('delta')))}</td>")
        html.append(f"<td>{esc(row.get('notes',''))}</td>")
        html.append("</tr>")
    html.append("</table>")

    html.append("<h2>Operating Order Pins</h2>")
    html.append("<table><tr><th>pin_id</th><th>order_event_id</th><th>date</th><th>tracks</th><th>rationale</th></tr>")
    for p in pins:
        html.append("<tr>")
        html.append(f"<td class='k'>{esc(p.pin_id)}</td>")
        html.append(f"<td class='k'>{esc(p.order_event_id)}</td>")
        html.append(f"<td class='k'>{esc(p.date or '')}</td>")
        html.append(f"<td>{esc('|'.join(p.tracks))}</td>")
        html.append(f"<td>{esc(p.rationale)}</td>")
        html.append("</tr>")
    html.append("</table>")

    html.append("<h2>Top Risks</h2>")
    top = sorted(risks, key=lambda r: r.severity, reverse=True)[:60]
    html.append("<table><tr><th>severity</th><th>risk_class</th><th>title</th><th>tracks</th><th>cure</th></tr>")
    for r in top:
        html.append("<tr>")
        html.append(f"<td class='k'>{r.severity}</td>")
        html.append(f"<td class='k'>{esc(r.risk_class)}</td>")
        html.append(f"<td>{esc(r.title)}</td>")
        html.append(f"<td>{esc('|'.join(r.tracks))}</td>")
        html.append(f"<td>{esc(r.fastest_cure)}</td>")
        html.append("</tr>")
    html.append("</table>")

    html.append("<h2>Vehicle Candidates</h2>")
    html.append("<table><tr><th>vehicle_type</th><th>tracks</th><th>operating_order_pin</th><th>purpose</th></tr>")
    for v in vehicles:
        html.append("<tr>")
        html.append(f"<td>{esc(v.vehicle_type)}</td>")
        html.append(f"<td>{esc('|'.join(v.tracks))}</td>")
        html.append(f"<td class='k'>{esc(v.operating_order_pin or 'MISSING')}</td>")
        html.append(f"<td>{esc(v.purpose)}</td>")
        html.append("</tr>")
    html.append("</table>")

    html.append("<h2>Recent Events</h2>")
    def event_sort_key(e: EventAtom) -> str:
        return e.date or "0000-00-00"
    recent = sorted(events, key=event_sort_key, reverse=True)[:60]
    html.append("<table><tr><th>date</th><th>kind</th><th>title</th><th>tracks</th><th>details</th></tr>")
    for e in recent:
        html.append("<tr>")
        html.append(f"<td class='k'>{esc(e.date or '')}</td>")
        html.append(f"<td class='k'>{esc(e.kind)}</td>")
        html.append(f"<td>{esc(e.title)}</td>")
        html.append(f"<td>{esc('|'.join(e.tracks))}</td>")
        html.append(f"<td>{esc(e.details[:300])}</td>")
        html.append("</tr>")
    html.append("</table>")

    html.append("</body></html>")

    out = run_dir / "index.html"
    out.write_text("\n".join(html), encoding="utf-8")
    return out

# -----------------------------
# Convergence digest
# -----------------------------

def compute_digest(docs: List[DocumentRef], evid: List[EvidenceAtom], events: List[EventAtom], clocks: List[DeadlineClock], risks: List[RiskEvent], vehicles: List[VehicleCandidate], pins: List[OperatingOrderPin]) -> str:
    # stable digest of primary IDs and key fields
    parts: List[str] = []
    for d in sorted(docs, key=lambda x: x.doc_id):
        parts.append(f"D|{d.doc_id}|{d.integrity_key}")
    for e in sorted(evid, key=lambda x: x.evid_id):
        parts.append(f"E|{e.evid_id}|{e.rel_path}|{e.span_start}|{e.span_end}|{','.join(e.tracks)}")
    for ev in sorted(events, key=lambda x: x.event_id):
        parts.append(f"V|{ev.event_id}|{ev.kind}|{ev.date or ''}|{','.join(ev.tracks)}")
    for c in sorted(clocks, key=lambda x: x.clock_id):
        parts.append(f"C|{c.clock_id}|{c.due_date or ''}|{','.join(c.tracks)}")
    for r in sorted(risks, key=lambda x: x.risk_id):
        parts.append(f"R|{r.risk_id}|{r.risk_type_id}|{r.risk_class}|{r.severity}")
    for v in sorted(vehicles, key=lambda x: x.vehicle_id):
        parts.append(f"H|{v.vehicle_id}|{v.vehicle_type_id}|{v.operating_order_pin or ''}")
    for p in sorted(pins, key=lambda x: x.pin_id):
        parts.append(f"O|{p.pin_id}|{p.order_event_id}|{p.date or ''}")
    return sha256_text("\n".join(parts))

# -----------------------------
# Cyclepack zipper
# -----------------------------

def make_cyclepack(run_dir: Path, extra_paths: List[Path]) -> Path:
    run_id = run_dir.name
    zip_path = run_dir.parent / f"cyclepack_{run_id}.zip"
    with zipfile.ZipFile(zip_path, "w", compression=zipfile.ZIP_DEFLATED) as z:
        # include everything in run_dir
        for p in sorted(run_dir.rglob("*")):
            if p.is_file():
                z.write(p, arcname=str(Path(run_id)/p.relative_to(run_dir)).replace("\\","/"))
        for p in extra_paths:
            if p.exists():
                if p.is_file():
                    z.write(p, arcname=str(p).replace("\\","/"))
                else:
                    for q in sorted(p.rglob("*")):
                        if q.is_file():
                            z.write(q, arcname=str(q).replace("\\","/"))
    return zip_path

# -----------------------------
# Main pipeline pass
# -----------------------------

def run_pass(intake: Path,
             out_root: Path,
             bundle_uid: str,
             track_keywords: Dict[str, List[str]],
             event_rules: List[Tuple[str, List[str], str]],
             clock_rules: List[Dict[str, Any]],
             risk_catalog: List[Dict[str, Any]],
             vehicle_catalog: List[Dict[str, Any]],
             pass_num: int) -> Tuple[Path, Dict[str, Any], List[DocumentRef], List[EvidenceAtom], List[EventAtom], List[DeadlineClock], List[RiskEvent], List[VehicleCandidate], List[OperatingOrderPin]]:

    run_dir = out_root / f"pass_{pass_num:02d}"
    safe_mkdir(run_dir)

    # Scan documents
    exts = (".txt",".md",".log",".json",".jsonl",".ndjson",".csv",".tsv",".docx",".pdf",".xlsx",".xlsm")
    doc_paths = scan_documents(intake, exts)
    docs: List[DocumentRef] = []
    manifest_rows: List[Dict[str, Any]] = []

    all_evid: List[EvidenceAtom] = []
    for p in doc_paths:
        try:
            doc_ref, b = build_document_ref(intake, p, bundle_uid)
            docs.append(doc_ref)
            manifest_rows.append(dataclasses.asdict(doc_ref))

            text = read_file_best_effort(p)
            if not text:
                continue
            all_evid.extend(build_evidence_atoms(doc_ref, text, track_keywords))
        except Exception:
            continue

    events = extract_events(all_evid, event_rules, track_keywords)
    clocks = compute_clocks(events, clock_rules)

    # Operating pins per track
    pins: List[OperatingOrderPin] = []
    pin_by_track: Dict[str, Optional[OperatingOrderPin]] = {}
    for tr in TRACKS:
        pin = select_operating_order_pin([e for e in events if tr in e.tracks], (tr,))
        pin_by_track[tr] = pin
        if pin:
            pins.append(pin)

    risks = compute_risks(events, clocks, pin_by_track, risk_catalog)
    vehicles = build_vehicle_candidates(pin_by_track, vehicle_catalog)

    # Exports
    write_json(run_dir / "manifest.json", manifest_rows)
    # also csv
    with open(run_dir / "manifest.csv", "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(manifest_rows[0].keys()) if manifest_rows else ["doc_id"])
        w.writeheader()
        for r in manifest_rows:
            w.writerow(r)

    write_jsonl(run_dir / "evidence_atoms.jsonl", all_evid)
    write_jsonl(run_dir / "events.jsonl", events)
    write_jsonl(run_dir / "clocks.jsonl", clocks)
    write_jsonl(run_dir / "risk_events.jsonl", risks)
    write_jsonl(run_dir / "vehicle_candidates.jsonl", vehicles)
    write_jsonl(run_dir / "operating_order_pins.jsonl", pins)

    export_graph(run_dir, docs, all_evid, events, clocks, risks, vehicles, pins)

    digest = compute_digest(docs, all_evid, events, clocks, risks, vehicles, pins)
    metrics = {
        "pass": pass_num,
        "digest": digest,
        "counts": {
            "docs": len(docs),
            "evidence": len(all_evid),
            "events": len(events),
            "clocks": len(clocks),
            "risks": len(risks),
            "vehicles": len(vehicles),
            "pins": len(pins),
        }
    }
    write_json(run_dir / "metrics.json", metrics)

    return run_dir, metrics, docs, all_evid, events, clocks, risks, vehicles, pins

# -----------------------------
# Orchestrator (convergence loop)
# -----------------------------

def load_track_keywords(catalog_dir: Path) -> Dict[str, List[str]]:
    # optional extension file
    path = catalog_dir / "track_keywords.json"
    if path.exists():
        try:
            raw = read_json(path)
            if isinstance(raw, dict):
                out = {}
                for tr in TRACKS:
                    kws = raw.get(tr, DEFAULT_TRACK_KEYWORDS.get(tr, []))
                    if isinstance(kws, list):
                        out[tr] = [str(x) for x in kws]
                return out
        except Exception:
            pass
    return {k: list(v) for k, v in DEFAULT_TRACK_KEYWORDS.items()}

def main() -> int:
    ap = argparse.ArgumentParser(
        description="MEEK2+MEEK3+MEEK4 full-stack rebuild harvester (convergent multi-pass).",
        formatter_class=argparse.RawTextHelpFormatter,
    )
    ap.add_argument("--intake", required=True, help="Intake folder to scan (recursively).")
    ap.add_argument("--out", required=True, help="Output root folder.")
    ap.add_argument("--bundle-uid", default="INTAKE", help="Bundle UID used in IntegrityKey.")
    ap.add_argument("--max-passes", type=int, default=12, help="Maximum refinement passes.")
    ap.add_argument("--make-cyclepack", action="store_true", help="Create cyclepack zip at end.")
    ap.add_argument("--catalog-dir", default="catalogs", help="Catalog directory (risk/vehicle).")
    ap.add_argument("--schema-dir", default="schema", help="Schema directory (node/edge/property/enums).")
    args = ap.parse_args()

    intake = Path(args.intake).expanduser().resolve()
    out_root = Path(args.out).expanduser().resolve()

    if not intake.exists():
        print(f"[ERR] intake does not exist: {intake}", file=sys.stderr)
        return 2

    safe_mkdir(out_root)

    catalog_dir = Path(args.catalog_dir).resolve() if Path(args.catalog_dir).exists() else (Path(__file__).parent / args.catalog_dir).resolve()
    schema_dir = Path(args.schema_dir).resolve() if Path(args.schema_dir).exists() else (Path(__file__).parent / args.schema_dir).resolve()

    # load catalogs
    risk_raw = load_catalog_json(catalog_dir / "risk_event_types.json")
    vehicle_raw = load_catalog_json(catalog_dir / "vehicle_types.json")
    risk_catalog = normalize_risk_catalog(risk_raw) if risk_raw else []
    vehicle_catalog = normalize_vehicle_catalog(vehicle_raw) if vehicle_raw else []

    track_keywords = load_track_keywords(catalog_dir)
    event_rules = list(DEFAULT_EVENT_RULES)
    clock_rules = list(DEFAULT_CLOCK_RULES)

    # output structure per run
    run_stamp = dt.datetime.now().strftime("%Y%m%d_%H%M%S")
    run_root = out_root / f"run_{run_stamp}"
    safe_mkdir(run_root)

    convergence_log: List[Dict[str, Any]] = []
    prev_digest: Optional[str] = None

    for i in range(1, max(1, args.max_passes) + 1):
        run_dir, metrics, docs, evid, events, clocks, risks, vehicles, pins = run_pass(
            intake=intake,
            out_root=run_root,
            bundle_uid=args.bundle_uid,
            track_keywords=track_keywords,
            event_rules=event_rules,
            clock_rules=clock_rules,
            risk_catalog=risk_catalog,
            vehicle_catalog=vehicle_catalog,
            pass_num=i,
        )
        digest = metrics["digest"]
        delta = None if prev_digest is None else (0 if digest == prev_digest else 1)
        notes = "initial" if prev_digest is None else ("converged" if digest == prev_digest else "changed")
        convergence_log.append({"pass": i, "digest": digest, "delta": delta, "notes": notes})

        if prev_digest is not None and digest == prev_digest:
            break
        prev_digest = digest

        # minimal refinement: expand keywords with discovered case-id suffix hints
        # (kept deterministic and bounded)
        # If we saw '-PP' case ids, ensure 'ppo' keyword is present; if '-DC' ensure 'foc' present.
        blob = " ".join([ev.details for ev in events]).upper()
        cids = infer_case_ids(blob)
        if any(cid.endswith("-PP") for cid in cids) and "ppo" not in track_keywords["MEEK3"]:
            track_keywords["MEEK3"].append("ppo")
        if any(cid.endswith("-DC") for cid in cids) and "foc" not in track_keywords["MEEK2"]:
            track_keywords["MEEK2"].append("foc")

    # write convergence log
    conv_path = run_root / "convergence_log.jsonl"
    with open(conv_path, "w", encoding="utf-8") as f:
        for row in convergence_log:
            f.write(json.dumps(row) + "\n")

    # build final dashboard from last pass folder
    last_pass = convergence_log[-1]["pass"]
    last_dir = run_root / f"pass_{int(last_pass):02d}"

    # load back for dashboard (avoid storing in memory earlier? we have)
    # For simplicity, re-read from jsonl outputs.
    def read_jsonl_dataclass(path: Path, cls):
        out=[]
        if not path.exists():
            return out
        for line in path.read_text(encoding="utf-8", errors="ignore").splitlines():
            if not line.strip():
                continue
            d=json.loads(line)
            out.append(cls(**d))
        return out

    docs = []
    mpath = last_dir / "manifest.json"
    if mpath.exists():
        raw = read_json(mpath)
        for r in raw:
            docs.append(DocumentRef(**r))

    evid = read_jsonl_dataclass(last_dir/"evidence_atoms.jsonl", EvidenceAtom)
    events = read_jsonl_dataclass(last_dir/"events.jsonl", EventAtom)
    clocks = read_jsonl_dataclass(last_dir/"clocks.jsonl", DeadlineClock)
    risks = read_jsonl_dataclass(last_dir/"risk_events.jsonl", RiskEvent)
    vehicles = read_jsonl_dataclass(last_dir/"vehicle_candidates.jsonl", VehicleCandidate)
    pins = read_jsonl_dataclass(last_dir/"operating_order_pins.jsonl", OperatingOrderPin)

    build_html_dashboard(last_dir, docs, evid, events, clocks, risks, vehicles, pins, convergence_log)

    # Also create a "latest" pointer folder (copy minimal)
    latest_dir = out_root / "latest"
    if latest_dir.exists():
        try:
            for p in latest_dir.rglob("*"):
                if p.is_file():
                    p.unlink()
        except Exception:
            pass
    safe_mkdir(latest_dir)
    # copy dashboard + graph + key jsonls
    for name in ["index.html","graph_nodes.csv","graph_edges.csv","risk_events.jsonl","vehicle_candidates.jsonl","events.jsonl","clocks.jsonl","convergence_log.jsonl"]:
        src = last_dir / name if name != "convergence_log.jsonl" else (run_root / "convergence_log.jsonl")
        if src.exists():
            (latest_dir / name).write_bytes(src.read_bytes())

    # optional cyclepack
    if args.make_cyclepack:
        extra = []
        if catalog_dir.exists():
            extra.append(catalog_dir)
        if schema_dir.exists():
            extra.append(schema_dir)
        zpath = make_cyclepack(last_dir, extra)
        print(f"[OK] cyclepack: {zpath}")

    print(f"[OK] run_root: {run_root}")
    print(f"[OK] latest:   {latest_dir}")
    return 0

if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except KeyboardInterrupt:
        print("\n[INTERRUPTED]", file=sys.stderr)
        raise SystemExit(130)
