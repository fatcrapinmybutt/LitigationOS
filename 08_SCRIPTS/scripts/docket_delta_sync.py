from __future__ import annotations
import argparse, hashlib, json
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data"


def load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))

def write_json(path: Path, payload: dict) -> None:
    path.write_text(json.dumps(payload, indent=2), encoding="utf-8")

def fingerprint(entry: dict) -> str:
    s = "|".join([
        str(entry.get("entry_id", "")),
        str(entry.get("kind", "")),
        str(entry.get("date", "")),
        str(entry.get("title", "")),
        str(entry.get("case_id", "")),
    ])
    return hashlib.md5(s.encode()).hexdigest()[:12]

def build_entries() -> list[dict]:
    orders = load_json(DATA / "orders.json").get("orders", [])
    service_rows = load_json(DATA / "service_proofs.json").get("service_proofs", [])
    deadlines = load_json(DATA / "deadlines.json").get("items", [])
    order_lane = {o.get("order_id"): o.get("lane") for o in orders}
    entries: list[dict] = []
    for o in orders:
        entries.append({
            "entry_id": o.get("order_id"),
            "kind": "order",
            "case_id": o.get("case_id"),
            "date": o.get("entered_date"),
            "title": o.get("title"),
            "lane": o.get("lane"),
            "source_ref": o.get("order_id"),
            "provenance_jump_hints": [o.get("order_id")],
        })
    for s in service_rows:
        entries.append({
            "entry_id": s.get("service_id"),
            "kind": "service",
            "case_id": s.get("case_id"),
            "date": s.get("served_date"),
            "title": f"{s.get('service_kind')} → {s.get('order_id')}",
            "lane": order_lane.get(s.get("order_id")),
            "source_ref": s.get("service_id"),
            "provenance_jump_hints": [s.get("service_id"), s.get("locator")],
        })
    for d in deadlines:
        entries.append({
            "entry_id": d.get("deadline_id"),
            "kind": "deadline",
            "case_id": d.get("case_id"),
            "date": d.get("due_date_iso"),
            "title": d.get("title"),
            "lane": None,
            "source_ref": d.get("deadline_id"),
            "provenance_jump_hints": [d.get("deadline_id")],
        })
    entries.sort(key=lambda e: (str(e.get("date") or ""), str(e.get("entry_id") or "")))
    for e in entries:
        e["fingerprint"] = fingerprint(e)
    return entries

def main() -> int:
    parser = argparse.ArgumentParser(description="Build docket delta sync rail from orders/service/deadlines payloads")
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()
    try:
        entries = build_entries()
        baseline_path = DATA / "docket_snapshot_baseline.json"
        current_path = DATA / "docket_snapshot_current.json"
        if baseline_path.exists():
            baseline = load_json(baseline_path)
        else:
            baseline = {"generated_at": datetime.now().isoformat(timespec="seconds"), "snapshot_id": "BASELINE-SEED", "entries": entries}
        current = {"generated_at": datetime.now().isoformat(timespec="seconds"), "snapshot_id": f"SNAP-{datetime.now().strftime('%Y%m%d-%H%M%S')}", "entries": entries}

        bmap = {e["entry_id"]: e for e in baseline.get("entries", [])}
        cmap = {e["entry_id"]: e for e in current.get("entries", [])}
        added = [cmap[k] for k in sorted(cmap.keys() - bmap.keys())]
        removed = [bmap[k] for k in sorted(bmap.keys() - cmap.keys())]
        changed = [{"entry_id": k, "before": bmap[k], "after": cmap[k]} for k in sorted(cmap.keys() & bmap.keys()) if cmap[k].get("fingerprint") != bmap[k].get("fingerprint")]

        svc_conf = load_json(DATA / "service_confidence.json") if (DATA / "service_confidence.json").exists() else {"orders": []}
        watch_targets = []
        for row in svc_conf.get("orders", []):
            if row.get("service_band") != "SOLID":
                watch_targets.append({
                    "watch_id": f"WATCH-SVC-{row.get('order_id')}",
                    "kind": "service_chain",
                    "priority": "HIGH" if row.get("service_band") == "FRAGILE" else "MEDIUM",
                    "lane": row.get("lane"),
                    "target_id": row.get("order_id"),
                    "message": f"{row.get('order_id')} service chain is {row.get('service_band')} ({row.get('service_chain_score')})",
                    "resolution_target": "Collect service proof and notice artifact path, then rerun service confidence rail.",
                    "provenance_jump_hints": row.get("provenance_jump_hints", []),
                })
        payload = {
            "generated_at": datetime.now().isoformat(timespec="seconds"),
            "sync_status": "BASELINE_SYNCED" if not (added or removed or changed) else "DELTAS_PENDING_REVIEW",
            "baseline_snapshot_id": baseline.get("snapshot_id"),
            "current_snapshot_id": current.get("snapshot_id"),
            "delta_counts": {"added": len(added), "removed": len(removed), "changed": len(changed), "watch_targets": len(watch_targets)},
            "filters": {"kinds": ["order","service","deadline"], "priorities": ["HIGH","MEDIUM","LOW"]},
            "added": added,
            "removed": removed,
            "changed": changed,
            "watch_targets": watch_targets,
            "current_entries_preview": entries[-20:],
            "resolution_target": "Feed live docket snapshots into this rail so order supersession, deadlines, and readiness move together on each cycle.",
        }
        if args.dry_run:
            print(json.dumps({"sync_status": payload["sync_status"], "delta_counts": payload["delta_counts"]}, indent=2))
            return 0
        write_json(baseline_path, baseline)
        write_json(current_path, current)
        write_json(DATA / "docket_delta_sync.json", payload)
        print(json.dumps({"status":"ok", "entries": len(entries), "delta_counts": payload["delta_counts"]}, indent=2))
        return 0
    except Exception as exc:
        print(json.dumps({"status":"error", "error": str(exc)}, indent=2))
        return 1

if __name__ == "__main__":
    raise SystemExit(main())
