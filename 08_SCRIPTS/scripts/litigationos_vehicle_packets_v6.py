#!/usr/bin/env python3
"""
litigationos_vehicle_packets_v6.py

Single-file reference tool that implements:
  - rebuttal-compile : REBUTTAL_INPUT.json -> REBUTTAL_OUTPUT.json (lane + vehicle candidates from crosswalk)
  - deadline-eval    : compute deadlines from pinned anchors + authority registry (TruthLock-safe)
  - packet-build     : packet template -> PACKET_PLAN.json + PACKET_REPORT.md (NOT filing)

No network. Deterministic. Fail-closed on missing authority pinpoints/durations.

Usage examples:
  python tools/litigationos_vehicle_packets_v6.py rebuttal-compile --in REBUTTAL_INPUT.json --out REBUTTAL_OUTPUT.json
  python tools/litigationos_vehicle_packets_v6.py deadline-eval --vehicle-id m2_trial_motion_reconsideration --deadline-family trial_reconsideration --operating-order-pin pin.json --authority-registry auth_registry.json --out DEADLINE_EVAL.json
  python tools/litigationos_vehicle_packets_v6.py packet-build --packet-template-id pkt_m3_contempt_set_aside --task-id task_0100 --deadline-eval DEADLINE_EVAL.json --out-dir out
"""
from __future__ import annotations

import argparse
import csv
import json
import os
import re
from dataclasses import dataclass
from datetime import date, datetime, timedelta
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

try:
    from zoneinfo import ZoneInfo
    TZ = ZoneInfo("America/Detroit")
except Exception:
    TZ = None  # fallback to naive timestamps

def now_iso() -> str:
    if TZ is None:
        return datetime.now().isoformat(timespec="seconds")
    return datetime.now(TZ).isoformat(timespec="seconds")

def read_json(path: Path) -> Any:
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)

def write_json(path: Path, obj: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as f:
        json.dump(obj, f, indent=2, ensure_ascii=False)

def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as f:
        f.write(text)

def parse_date_yyyy_mm_dd(s: str) -> date:
    m = re.fullmatch(r"(\d{4})-(\d{2})-(\d{2})", s.strip())
    if not m:
        raise ValueError(f"Expected YYYY-MM-DD date, got: {s!r}")
    y, mo, d = map(int, m.groups())
    return date(y, mo, d)

def load_crosswalk_json(path: Path) -> List[Dict[str, Any]]:
    data = read_json(path)
    if not isinstance(data, list):
        raise ValueError("Crosswalk JSON must be a list.")
    return data

def pick_lane(case_id: Optional[str], lane_hint: Optional[str], harm_tags: List[str], text_blob: str) -> Tuple[str, List[Dict[str, Any]]]:
    hint = (lane_hint or "").strip().upper()
    if hint in ("MEEK2", "MEEK3", "MEEK4"):
        return hint, []

    if case_id and "-PP" in case_id.upper():
        return "MEEK3", []
    if case_id and "-DC" in case_id.upper():
        return "MEEK2", []

    tags = {t.lower() for t in harm_tags}
    if "judicial" in tags or "canon" in tags or "misconduct" in tags:
        return "MEEK4", []

    blob = text_blob.lower()
    if "ppo" in blob or "contempt" in blob or "jail" in blob:
        return "MEEK3", []
    if "parenting time" in blob or "custody" in blob or "foc" in blob:
        return "MEEK2", []

    return "UNKNOWN", [{"kind":"lane_unknown","detail":"Unable to infer lane; provide lane_hint."}]

def score_routes(crosswalk: List[Dict[str, Any]], statements: List[Dict[str, Any]]) -> List[Tuple[int, Dict[str, Any]]]:
    scored: Dict[str, Tuple[int, Dict[str, Any]]] = {}
    for r in crosswalk:
        keywords = [k.lower() for k in r.get("trigger_keywords", [])]
        score = 0
        for s in statements:
            txt = (s.get("text") or "").lower()
            for kw in keywords:
                if kw and kw in txt:
                    score += 1
        rid = r.get("route_id", "")
        scored[rid] = (score, r)
    out = [(sc, r) for sc, r in scored.values() if sc > 0]
    out.sort(key=lambda t: (-t[0], t[1].get("priority",""), t[1].get("vehicle_id","")))
    return out

def rebuttal_compile(args: argparse.Namespace) -> int:
    inp = read_json(Path(args.input))
    statements = inp.get("adverse_statements", [])
    blockers: List[Dict[str, Any]] = []

    # Validate source_ptr presence
    for s in statements:
        if not s.get("source_ptr"):
            blockers.append({"kind":"missing_source_ptr","statement_id": s.get("statement_id")})

    text_blob = "\n".join((s.get("text") or "") for s in statements)
    harm_tags: List[str] = []
    for s in statements:
        for t in (s.get("harm_tags") or []):
            harm_tags.append(str(t))

    lane, lane_blockers = pick_lane(inp.get("case_id"), inp.get("lane_hint"), harm_tags, text_blob)
    blockers.extend(lane_blockers)

    if lane == "UNKNOWN":
        out = {
            "generated": now_iso(),
            "selected_lane": "UNKNOWN",
            "vehicle_candidates": [],
            "blockers": blockers,
            "recommended_next_actions": ["Set lane_hint to one of: MEEK2, MEEK3, MEEK4"]
        }
        write_json(Path(args.output), out)
        return 0

    crosswalk_path = Path(args.crosswalk_root) / "vehicle_matrix" / "lanes" / lane / f"VEHICLE_CROSSWALK_{lane}.json"
    crosswalk = load_crosswalk_json(crosswalk_path)

    scored = score_routes(crosswalk, statements)
    candidates: List[Dict[str, Any]] = []
    for sc, r in scored[: args.max_candidates]:
        cand = {
            "vehicle_id": r["vehicle_id"],
            "route_id": r["route_id"],
            "score": sc,
            "priority": r.get("priority"),
            "operating_order_required": r.get("operating_order_required", False),
            "authority_keys_required": r.get("authority_keys_required", []),
            "deadline_family": r.get("deadline_family"),
            "packet_template_id": r.get("packet_template_id"),
            "ready": False,
            "blockers": []
        }
        if r.get("operating_order_required", False):
            cand["blockers"].append({"kind":"missing_operating_order_pin","detail":"Requires OperatingOrderPin with entered_date"})
        if not r.get("authority_keys_required"):
            cand["blockers"].append({"kind":"authority_keys_missing","detail":"Crosswalk row missing authority keys; fix data."})
        candidates.append(cand)

    rec_actions = []
    if any(c.get("operating_order_required") for c in candidates):
        rec_actions.append("Pin OperatingOrderPin (entered_date) for the operative controlling order.")
    rec_actions.append("Resolve authority keys in Authority Registry snapshot (must include pinpoint).")
    rec_actions.append("If vehicle requires deadlines, run deadline-eval.")
    rec_actions.append("Then run packet-build for the chosen packet_template_id.")

    out = {
        "generated": now_iso(),
        "selected_lane": lane,
        "vehicle_candidates": candidates,
        "blockers": blockers,
        "recommended_next_actions": rec_actions
    }
    write_json(Path(args.output), out)
    return 0

def deadline_eval(args: argparse.Namespace) -> int:
    # Load deadline families
    deadlines_path = Path(args.crosswalk_root) / "deadlines" / "vehicle_family_deadlines.json"
    families_doc = read_json(deadlines_path)
    families = {f["deadline_family"]: f for f in families_doc.get("families", [])}
    if args.deadline_family not in families:
        raise SystemExit(f"Unknown deadline_family: {args.deadline_family}")

    fam = families[args.deadline_family]
    blockers: List[Dict[str, Any]] = []
    anchors_used: Dict[str, Any] = {}

    # anchors
    order_entered_date = None
    if "order_entered_date" in fam.get("required_anchors", []):
        if args.order_entered_date:
            order_entered_date = parse_date_yyyy_mm_dd(args.order_entered_date)
        elif args.operating_order_pin:
            pin = read_json(Path(args.operating_order_pin))
            if isinstance(pin, dict) and pin.get("entered_date"):
                order_entered_date = parse_date_yyyy_mm_dd(pin["entered_date"])
        if not order_entered_date:
            blockers.append({"kind":"missing_anchor","anchor":"order_entered_date"})
        else:
            anchors_used["order_entered_date"] = order_entered_date.isoformat()

    # authority registry
    registry = read_json(Path(args.authority_registry)) if args.authority_registry else {}
    if not isinstance(registry, dict):
        blockers.append({"kind":"bad_authority_registry","detail":"Expected JSON object mapping authority_key -> resolution"})
        registry = {}

    authority_resolutions: List[Dict[str, Any]] = []
    for ak in fam.get("authority_keys_required", []):
        res = registry.get(ak)
        if not res:
            blockers.append({"kind":"unresolved_authority_key","authority_key": ak})
            continue
        # must include pinpoint to be "resolved"
        if not res.get("pinpoint"):
            blockers.append({"kind":"missing_pinpoint","authority_key": ak})
        authority_resolutions.append({"authority_key": ak, **res})

    computed: Dict[str, Any] = {}
    if blockers:
        out = {
            "vehicle_id": args.vehicle_id,
            "case_id": args.case_id,
            "deadline_family": args.deadline_family,
            "deadline_status": "UNKNOWN",
            "generated": now_iso(),
            "anchors_used": anchors_used,
            "computed": computed,
            "authority_resolutions": authority_resolutions,
            "blockers": blockers
        }
        write_json(Path(args.output), out)
        return 0

    # compute fields from registry values
    for field in fam.get("computed_fields", []):
        name = field["name"]
        kind = field.get("kind")
        if kind == "date":
            # find a registry key with deadline_days
            ak = fam["authority_keys_required"][0]
            days = authority_resolutions[0].get("deadline_days")
            if days is None:
                blockers.append({"kind":"missing_registry_value","authority_key": ak, "need":"deadline_days"})
                continue
            computed[name] = (order_entered_date + timedelta(days=int(days))).isoformat()
        elif kind == "date_or_window":
            ak = fam["authority_keys_required"][0]
            window = authority_resolutions[0].get("deadline_window")
            if not window:
                blockers.append({"kind":"missing_registry_value","authority_key": ak, "need":"deadline_window"})
                continue
            # interpret window as {days:int} or {min_days:int,max_days:int}
            if "days" in window:
                computed[name] = (order_entered_date + timedelta(days=int(window["days"]))).isoformat()
            else:
                mn = int(window.get("min_days", 0))
                mx = int(window.get("max_days", 0))
                computed[name] = {
                    "min": (order_entered_date + timedelta(days=mn)).isoformat(),
                    "max": (order_entered_date + timedelta(days=mx)).isoformat()
                }
        else:
            # narrative/guidance
            ak = fam["authority_keys_required"][0]
            guidance = authority_resolutions[0].get("guidance")
            if guidance is None:
                blockers.append({"kind":"missing_registry_value","authority_key": ak, "need":"guidance"})
                continue
            computed[name] = guidance

    status = "KNOWN" if not blockers else "UNKNOWN"
    out = {
        "vehicle_id": args.vehicle_id,
        "case_id": args.case_id,
        "deadline_family": args.deadline_family,
        "deadline_status": status,
        "generated": now_iso(),
        "anchors_used": anchors_used,
        "computed": computed,
        "authority_resolutions": authority_resolutions,
        "blockers": blockers
    }
    write_json(Path(args.output), out)
    return 0

def packet_build(args: argparse.Namespace) -> int:
    root = Path(args.crosswalk_root)
    templates_all = read_json(root / "packets" / "templates_all.json")
    templates = {t["packet_template_id"]: t for t in templates_all}
    if args.packet_template_id not in templates:
        raise SystemExit(f"Unknown packet_template_id: {args.packet_template_id}")
    tpl = templates[args.packet_template_id]

    blockers: List[Dict[str, Any]] = []
    deadlines_obj: Dict[str, Any] = {}

    # deadline eval required?
    if tpl.get("requires_deadline_eval", False):
        if not args.deadline_eval:
            blockers.append({"kind":"missing_deadline_eval","detail":"Template requires deadline eval JSON"})
        else:
            deadlines_obj = read_json(Path(args.deadline_eval))
            if deadlines_obj.get("deadline_status") != "KNOWN":
                blockers.append({"kind":"deadline_unknown","detail":"deadline_status is not KNOWN"})

    # required pins (lightweight check)
    for pin in tpl.get("required_pins", []):
        if pin == "OperatingOrderPin" and not args.operating_order_pin and not args.order_entered_date:
            blockers.append({"kind":"missing_operating_order_pin","detail":"Provide --operating-order-pin or --order-entered-date"})
        if pin.startswith("AUTHKEY_"):
            # must be present in authority registry if provided
            if args.authority_registry:
                reg = read_json(Path(args.authority_registry))
                if not reg.get(pin) or not reg.get(pin, {}).get("pinpoint"):
                    blockers.append({"kind":"unresolved_authority_key","authority_key": pin})

    exhibits = []
    for ex in tpl.get("exhibit_requirements", []):
        exhibits.append({
            "exhibit_id": ex.get("exhibit_id"),
            "purpose": ex.get("purpose"),
            "required_sources": ex.get("required_sources", []),
            "source_ptrs": []
        })

    status = "READY" if not blockers else "BLOCKED"
    plan = {
        "packet_template_id": tpl["packet_template_id"],
        "task_id": args.task_id or "task_UNKNOWN",
        "vehicle_id": tpl["vehicle_id"],
        "lane": tpl["lane"],
        "court_level": tpl["court_level"],
        "status": status,
        "generated": now_iso(),
        "outline": tpl["outline"],
        "exhibits": exhibits,
        "deadlines": deadlines_obj if deadlines_obj else {"deadline_status":"UNKNOWN"},
        "checklist": [
            "Populate exhibit source_ptrs to real evidence/doc pointers",
            "Verify all quoted text (QuoteLock)",
            "Resolve all authority keys (pinpoints) in Authority Registry",
            "If deadlines apply, verify by registry + anchors"
        ],
        "blockers": blockers
    }

    out_dir = Path(args.out_dir).resolve()
    if args.dry_run:
        print(json.dumps(plan, indent=2, ensure_ascii=False))
        return 0

    write_json(out_dir / "PACKET_PLAN.json", plan)
    rep_lines = [f"# PACKET_REPORT", "", f"status: {status}", "", "## blockers"]
    if blockers:
        for b in blockers:
            rep_lines.append(f"- {b.get('kind')}: {b.get('detail') or b.get('authority_key') or ''}".rstrip())
    else:
        rep_lines.append("- (none)")
    write_text(out_dir / "PACKET_REPORT.md", "\n".join(rep_lines) + "\n")
    return 0

def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--crosswalk-root", default=".", help="Pack root (folder containing vehicle_matrix/, deadlines/, packets/)")
    sub = ap.add_subparsers(dest="cmd", required=True)

    # rebuttal-compile
    ap_r = sub.add_parser("rebuttal-compile")
    ap_r.add_argument("--in", dest="input", required=True, help="REBUTTAL_INPUT.json")
    ap_r.add_argument("--out", dest="output", required=True, help="REBUTTAL_OUTPUT.json")
    ap_r.add_argument("--max-candidates", type=int, default=5)
    ap_r.set_defaults(func=rebuttal_compile)

    # deadline-eval
    ap_d = sub.add_parser("deadline-eval")
    ap_d.add_argument("--vehicle-id", required=True)
    ap_d.add_argument("--case-id", default=None)
    ap_d.add_argument("--deadline-family", required=True)
    ap_d.add_argument("--order-entered-date", default=None, help="YYYY-MM-DD (optional if operating-order-pin provided)")
    ap_d.add_argument("--operating-order-pin", default=None, help="JSON file with entered_date")
    ap_d.add_argument("--authority-registry", required=True, help="Authority registry JSON mapping authority_key -> {authority_id,pinpoint,deadline_days|deadline_window|guidance}")
    ap_d.add_argument("--out", dest="output", required=True)
    ap_d.set_defaults(func=deadline_eval)

    # packet-build
    ap_p = sub.add_parser("packet-build")
    ap_p.add_argument("--packet-template-id", required=True)
    ap_p.add_argument("--task-id", default=None)
    ap_p.add_argument("--deadline-eval", default=None, help="DEADLINE_EVAL.json (required if template requires_deadline_eval)")
    ap_p.add_argument("--operating-order-pin", default=None, help="JSON file with entered_date")
    ap_p.add_argument("--order-entered-date", default=None, help="YYYY-MM-DD")
    ap_p.add_argument("--authority-registry", default=None, help="Authority registry JSON (for AUTHKEY validation)")
    ap_p.add_argument("--out-dir", default="out")
    ap_p.add_argument("--dry-run", action="store_true")
    ap_p.set_defaults(func=packet_build)

    args = ap.parse_args()
    return args.func(args)

if __name__ == "__main__":
    raise SystemExit(main())
