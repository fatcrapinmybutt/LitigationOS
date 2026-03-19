#!/usr/bin/env python3
"""
MEEK234_FULLSTACK_REBUILD_v20260208_3.py

Purpose
- Compile a typed graph skeleton (nodes/edges CSV) + risk/clock/vehicle dashboards
  for MEEK2 (custody/PT/FOC/support), MEEK3 (PPO/contempt/appeals), MEEK4 (bias/JTC/extraordinary relief).
- Drive everything from catalogs (vehicle_types, risk_event_types, forum_gate_profiles) + minimal seed inputs.

Design goals
- Deterministic outputs (stable ordering)
- Catalog-first (easy to expand without rewriting code)
- Fail-soft (always emits outputs; risks show what's missing)

Usage
  python MEEK234_FULLSTACK_REBUILD_v20260208_3.py --out out_run
  python MEEK234_FULLSTACK_REBUILD_v20260208_3.py --out out_run --catalogs ./catalogs

Outputs
  out_run/
    nodes.csv
    edges.csv
    clocks.jsonl
    vehicle_candidates.jsonl
    risk_events.jsonl
    dashboard_kills_cures.json
    runledger.jsonl
"""
from __future__ import annotations

import argparse
import csv
import json
import os
import hashlib
from dataclasses import dataclass, asdict
from datetime import date, datetime, timedelta
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Tuple

# ---------------------------
# Deterministic ID helpers
# ---------------------------
def _sha1(s: str) -> str:
    return hashlib.sha1(s.encode("utf-8")).hexdigest()

def stable_id(prefix: str, *parts: str) -> str:
    base = "|".join([prefix, *parts])
    return f"{prefix}_{_sha1(base)[:16]}"

def iso_today() -> date:
    # deterministic default "today" for reproducible runs unless overridden
    env = os.environ.get("MEK_TODAY")
    if env:
        return date.fromisoformat(env)
    return date(2026, 2, 8)

def ensure_dir(p: Path) -> None:
    p.mkdir(parents=True, exist_ok=True)

def write_json(p: Path, obj: Any) -> None:
    ensure_dir(p.parent)
    p.write_text(json.dumps(obj, indent=2, ensure_ascii=False), encoding="utf-8")

def write_jsonl(p: Path, rows: Iterable[Dict[str, Any]]) -> None:
    ensure_dir(p.parent)
    with p.open("w", encoding="utf-8") as f:
        for r in rows:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")

def write_csv(p: Path, rows: List[Dict[str, Any]], fieldnames: List[str]) -> None:
    ensure_dir(p.parent)
    with p.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=fieldnames)
        w.writeheader()
        for r in rows:
            w.writerow({k: r.get(k, "") for k in fieldnames})

# ---------------------------
# Catalog loading
# ---------------------------
def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))

def load_catalogs(catalogs_dir: Optional[Path]) -> Dict[str, Any]:
    """
    If catalogs_dir is provided, read from there.
    Otherwise, attempt to read from sibling ./catalogs relative to this script.
    """
    if catalogs_dir is None:
        catalogs_dir = Path(__file__).resolve().parent / "catalogs"
        if not catalogs_dir.exists():
            raise FileNotFoundError("catalogs directory not found; pass --catalogs PATH or run from pack root.")
    return {
        "vehicle_types": load_json(catalogs_dir / "vehicle_types.json"),
        "risk_event_types": load_json(catalogs_dir / "risk_event_types.json"),
        "forum_gate_profiles": load_json(catalogs_dir / "forum_gate_profiles.json"),
    }

# ---------------------------
# Types
# ---------------------------
@dataclass(frozen=True)
class Node:
    id: str
    node_type: str
    label: str
    props: Dict[str, Any]

@dataclass(frozen=True)
class Edge:
    id: str
    edge_type: str
    src: str
    dst: str
    props: Dict[str, Any]

@dataclass(frozen=True)
class Clock:
    clock_id: str
    label: str
    due_date: Optional[str]
    expired: bool
    trigger_event_id: Optional[str] = None
    notes: str = ""

@dataclass(frozen=True)
class VehicleCandidate:
    id: str
    vehicle_type_id: str
    track: str
    forum: str
    label: str
    requires_operating_order_pin: bool
    record_products_missing: List[str]
    status: str  # proposed|ready|blocked

@dataclass(frozen=True)
class RiskEvent:
    id: str
    risk_type_id: str
    track: str
    forum: str
    risk_class: str
    severity: int
    title: str
    cure_cost: int
    cure_deadline_clock: str
    cure_minimum_packet: List[str]
    triggered_by: List[str]

# ---------------------------
# Minimal seed graph (no personal facts; fill from your mainframe)
# ---------------------------
def build_min_seed_graph() -> Tuple[List[Node], List[Edge]]:
    """
    Build a minimal graph skeleton for MEEK2/3/4 with one Matter that spans 3 Tracks.
    You should replace/extend this via your own ingestion pipeline.
    """
    nodes: List[Node] = []
    edges: List[Edge] = []

    matter_id = stable_id("matter", "MEEK234")
    nodes.append(Node(matter_id, "Matter", "MEEK234 Matter", {"id": matter_id}))

    for track in ["MEEK2", "MEEK3", "MEEK4"]:
        tid = stable_id("track", track)
        nodes.append(Node(tid, "Track", track, {"id": tid, "track": track}))
        edges.append(Edge(stable_id("e", matter_id, tid, "MATTER_IN_TRACK"), "MATTER_IN_TRACK", matter_id, tid, {}))

    for forum in ["trial", "coa", "msc", "jtc"]:
        fid = stable_id("forum", forum)
        nodes.append(Node(fid, "Forum", forum.upper(), {"id": fid, "forum": forum}))

    # Courts are placeholders (user binds to real courts)
    courts = [
        ("14th Circuit Court", "circuit", "Muskegon"),
        ("60th District Court", "district", "Muskegon"),
        ("Michigan Court of Appeals", "coa", ""),
        ("Michigan Supreme Court", "msc", ""),
        ("Judicial Tenure Commission", "jtc", ""),
    ]
    for name, level, county in courts:
        cid = stable_id("court", name)
        nodes.append(Node(cid, "Court", name, {"id": cid, "court_name": name, "court_level": level, "county": county}))

    return nodes, edges

# ---------------------------
# Clock engine (starter clocks; you will expand)
# ---------------------------
def compute_base_clocks(today: date) -> List[Clock]:
    """
    Starter clocks used by risk types. In the full system, these are derived from TriggerEvents.
    """
    # default "unknown" clocks not expired
    def mk(clock_id: str, label: str, due: Optional[date], notes: str = "") -> Clock:
        due_s = due.isoformat() if due else None
        expired = bool(due and due < today)
        return Clock(clock_id=clock_id, label=label, due_date=due_s, expired=expired, notes=notes)

    # Placeholder due dates (None means unknown until TriggerEvents exist)
    return [
        mk("coa_claim_of_appeal", "COA Claim of Appeal Due", None, "Bind to appealed order entered date + MCR 7.204."),
        mk("coa_docketing_statement_due", "COA Docketing Statement Due", None, "Bind to claim of appeal filing + MCR 7.212(H)."),
        mk("coa_deficiency_cure", "COA Deficiency Letter Cure Window", None, "Bind to clerk notice date + IOP."),
        mk("coa_transcript_due", "COA Transcript/Record Due", None, "Bind to transcript order/certification deadlines."),
        mk("msc_application_leave", "MSC Application for Leave Due", None, "Bind to COA decision/service date + MCR 7.305."),
        mk("msc_return_cure", "MSC Return-Without-Docketing Cure Window", None, "Bind to clerk return date."),
        mk("jtc_28_day_letter", "JTC 28-Day Letter Response Due", None, "Bind to notice date + MCR 9.222."),
        mk("clerk_cure_window", "Generic Clerk Cure Window", None, "Bind to notice date."),
        mk("next_filing_deadline", "Next Filing Deadline (Generic)", None, "Roll-up of nearest computed clock."),
        mk("appeal_or_objection_deadline", "Appeal/Objection Deadline (Generic)", None, "Bind to forum posture."),
        mk("ppo_modify_terminate_window", "PPO Modify/Terminate Window", None, "Bind to service/actual notice + MCR 3.707."),
        mk("jtc_intake_window", "JTC Intake Window", None, "Not usually a strict clock; used for packaging urgency."),
        mk("jtc_answer_due", "JTC Answer Due", None, "Bind to complaint issuance + rules."),
    ]

# ---------------------------
# Vehicle candidates (catalog-first)
# ---------------------------
def build_vehicle_candidates(vehicle_types: List[Dict[str, Any]], has_operating_pin: bool) -> List[VehicleCandidate]:
    vehicles: List[VehicleCandidate] = []
    for vt in sorted(vehicle_types, key=lambda x: x["vehicle_type_id"]):
        missing: List[str] = []
        if vt.get("requires_operating_order_pin", False) and not has_operating_pin:
            missing.append("OperatingOrderPin")
        status = "ready" if not missing else "blocked"
        vehicles.append(
            VehicleCandidate(
                id=stable_id("veh", vt["vehicle_type_id"]),
                vehicle_type_id=vt["vehicle_type_id"],
                track=vt.get("track", "*"),
                forum=vt.get("forum", "*"),
                label=vt.get("label", vt["vehicle_type_id"]),
                requires_operating_order_pin=bool(vt.get("requires_operating_order_pin", False)),
                record_products_missing=missing,
                status=status,
            )
        )
    return vehicles

# ---------------------------
# Risk engine (small DSL evaluator)
# ---------------------------
def index_events_by_kind(nodes: List[Node]) -> Dict[str, int]:
    # In this starter pack we don't create Event nodes; your ingestion will.
    return {}

def parse_trigger_predicate(pred: str) -> Tuple[str, str]:
    if ":" in pred:
        a, b = pred.split(":", 1)
        return a.strip(), b.strip()
    return pred.strip(), ""

def compute_risks(
    risk_types: List[Dict[str, Any]],
    clocks: Dict[str, Clock],
    vehicles: List[VehicleCandidate],
    events_by_kind: Dict[str, int],
    tags_present: List[str],
    packet_fields: Dict[str, bool],
) -> List[RiskEvent]:
    risks: List[RiskEvent] = []

    def clock_expired(clock_id: str) -> bool:
        c = clocks.get(clock_id)
        return bool(c and c.expired)

    def missing_operating_pin() -> bool:
        return any(v.requires_operating_order_pin and v.status == "blocked" for v in vehicles)

    def missing_packet(packet_id: str) -> bool:
        # Starter pack treats "packet presence" as tags_present entries like "packet:coa_docketing_statement"
        return f"packet:{packet_id}" not in tags_present

    def event_kind_present(kind: str) -> bool:
        return events_by_kind.get(kind, 0) > 0

    def event_tag_present(tag: str) -> bool:
        return tag in tags_present

    def packet_field_false(field: str) -> bool:
        return packet_fields.get(field, True) is False

    for rt in sorted(risk_types, key=lambda x: x["risk_type_id"]):
        trig: List[str] = []
        triggered = False
        for pred in rt.get("trigger_when", []):
            op, val = parse_trigger_predicate(pred)
            ok = False
            if op == "CLOCK_EXPIRED":
                ok = clock_expired(val)
            elif op == "MISSING_NODE" and val == "OperatingOrderPin":
                ok = missing_operating_pin()
            elif op == "MISSING_PACKET":
                ok = missing_packet(val)
            elif op == "EVENT_KIND_PRESENT":
                ok = event_kind_present(val)
            elif op == "EVENT_TAG_PRESENT":
                ok = event_tag_present(val)
            elif op == "PACKET_FIELD_FALSE":
                ok = packet_field_false(val)
            # unknown predicates are ignored (fail-soft)
            if ok:
                triggered = True
                trig.append(pred)

        if triggered:
            rid = stable_id("risk", rt["risk_type_id"])
            risks.append(
                RiskEvent(
                    id=rid,
                    risk_type_id=rt["risk_type_id"],
                    track=rt.get("track", "*"),
                    forum=rt.get("forum", "*"),
                    risk_class=rt.get("risk_class", "curable_defect"),
                    severity=int(rt.get("severity", 50)),
                    title=rt.get("title", rt["risk_type_id"]),
                    cure_cost=int(rt.get("cure_cost", 3)),
                    cure_deadline_clock=rt.get("cure_deadline_clock", "next_filing_deadline"),
                    cure_minimum_packet=list(rt.get("cure_minimum_packet", [])),
                    triggered_by=trig,
                )
            )
    return risks

# ---------------------------
# Dashboard query compiler
# ---------------------------
def dashboard_kills_cures_nextclock(risks: List[RiskEvent], clocks: Dict[str, Clock]) -> Dict[str, Any]:
    """
    Answers:
      - What can kill this matter next?
      - What cures it fastest?
      - What is the next clock to expire?
      - What packet do I need to cure?
    """
    # Rank risks by severity desc, then cure_cost asc.
    risks_sorted = sorted(risks, key=lambda r: (-r.severity, r.cure_cost, r.risk_type_id))

    # "fastest cure" = lowest cure_cost among active risks, tie-break earliest known clock due date
    def clock_key(clock_id: str) -> Tuple[int, str]:
        c = clocks.get(clock_id)
        if not c or not c.due_date:
            return (999999, "9999-12-31")
        return (0, c.due_date)

    fastest = None
    if risks_sorted:
        fastest = sorted(risks_sorted, key=lambda r: (r.cure_cost, clock_key(r.cure_deadline_clock), -r.severity))[0]

    # next clock to expire: earliest due date among known clocks
    known = [c for c in clocks.values() if c.due_date]
    known_sorted = sorted(known, key=lambda c: c.due_date)
    next_clock = known_sorted[0] if known_sorted else None

    return {
        "kill_list": [asdict(r) for r in risks_sorted[:25]],
        "fastest_cure": asdict(fastest) if fastest else None,
        "next_clock": asdict(next_clock) if next_clock else None,
        "packets_to_cure": [
            {"risk_type_id": r.risk_type_id, "deadline_clock": r.cure_deadline_clock, "minimum_packet": r.cure_minimum_packet}
            for r in risks_sorted[:25]
        ],
    }

# ---------------------------
# Convergence loop (delta stabilization)
# ---------------------------
def digest_outputs(obj: Any) -> str:
    b = json.dumps(obj, sort_keys=True, ensure_ascii=False).encode("utf-8")
    return hashlib.sha256(b).hexdigest()

def run_cycles(out_dir: Path, catalogs: Dict[str, Any], max_cycles: int = 6) -> Dict[str, Any]:
    """
    Runs consecutive internal cycles until outputs stabilize (digest stops changing).
    This starter pack is deterministic, so it usually stabilizes on cycle 2.
    """
    ledger: List[Dict[str, Any]] = []
    prev = None
    final_bundle = None

    for cycle in range(1, max_cycles + 1):
        today = iso_today()

        # In full system: ingestion populates these
        nodes, edges = build_min_seed_graph()
        events_by_kind = index_events_by_kind(nodes)

        # Simulated "state" that can change across cycles if you extend logic
        has_operating_pin = False  # until ingestion provides it
        tags_present: List[str] = []  # e.g., ["packet:coa_docketing_statement","msc_return_without_docketing",...]
        packet_fields: Dict[str, bool] = {"jtc_request_verified": True}

        # Cycle heuristic: add a synthetic tag in later cycles to demonstrate convergence
        if cycle >= 2:
            tags_present.append("packet:coa_docketing_statement")

        clocks_list = compute_base_clocks(today)
        clocks = {c.clock_id: c for c in clocks_list}
        vehicles = build_vehicle_candidates(catalogs["vehicle_types"], has_operating_pin=has_operating_pin)
        risks = compute_risks(
            risk_types=catalogs["risk_event_types"],
            clocks=clocks,
            vehicles=vehicles,
            events_by_kind=events_by_kind,
            tags_present=tags_present,
            packet_fields=packet_fields,
        )
        dash = dashboard_kills_cures_nextclock(risks, clocks)

        bundle = {
            "cycle": cycle,
            "nodes": [asdict(n) for n in nodes],
            "edges": [asdict(e) for e in edges],
            "clocks": [asdict(c) for c in clocks_list],
            "vehicles": [asdict(v) for v in vehicles],
            "risks": [asdict(r) for r in risks],
            "dashboard": dash,
            "tags_present": tags_present,
        }
        dig = digest_outputs(bundle)

        ledger.append({"cycle": cycle, "digest": dig, "risk_count": len(risks), "vehicle_count": len(vehicles), "today": str(today)})

        if prev == dig:
            final_bundle = bundle
            break
        prev = dig
        final_bundle = bundle

    # Emit final outputs
    # Flatten nodes/edges into Neo4j-friendly CSVs
    nodes_rows = []
    for n in final_bundle["nodes"]:
        row = {"id": n["id"], "node_type": n["node_type"], "label": n["label"], "props_json": json.dumps(n["props"], ensure_ascii=False)}
        nodes_rows.append(row)
    edges_rows = []
    for e in final_bundle["edges"]:
        row = {"id": e["id"], "edge_type": e["edge_type"], "src": e["src"], "dst": e["dst"], "props_json": json.dumps(e["props"], ensure_ascii=False)}
        edges_rows.append(row)

    write_csv(out_dir / "nodes.csv", sorted(nodes_rows, key=lambda r: (r["node_type"], r["id"])), ["id","node_type","label","props_json"])
    write_csv(out_dir / "edges.csv", sorted(edges_rows, key=lambda r: (r["edge_type"], r["id"])), ["id","edge_type","src","dst","props_json"])
    write_jsonl(out_dir / "clocks.jsonl", final_bundle["clocks"])
    write_jsonl(out_dir / "vehicle_candidates.jsonl", final_bundle["vehicles"])
    write_jsonl(out_dir / "risk_events.jsonl", final_bundle["risks"])
    write_json(out_dir / "dashboard_kills_cures.json", final_bundle["dashboard"])
    write_jsonl(out_dir / "runledger.jsonl", ledger)

    return {"final_cycle": ledger[-1]["cycle"], "final_digest": ledger[-1]["digest"], "ledger": ledger}

# ---------------------------
# Main
# ---------------------------
def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", required=True, help="Output folder")
    ap.add_argument("--catalogs", default=None, help="Catalogs folder (vehicle_types.json, risk_event_types.json, forum_gate_profiles.json)")
    ap.add_argument("--max-cycles", type=int, default=6, help="Max internal cycles for delta stabilization")
    args = ap.parse_args()

    out_dir = Path(args.out).resolve()
    ensure_dir(out_dir)

    catalogs = load_catalogs(Path(args.catalogs).resolve() if args.catalogs else None)
    result = run_cycles(out_dir, catalogs, max_cycles=args.max_cycles)

    # minimal console output (deterministic)
    print(json.dumps(result, indent=2))
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
