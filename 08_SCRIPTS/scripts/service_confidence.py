from __future__ import annotations
import argparse, json, sys
from pathlib import Path
from datetime import datetime

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data"

STATUS_SCORE = {
    "served": 0.95,
    "service_affidavit": 0.95,
    "proof_attached": 0.90,
    "partial_record": 0.58,
    "contested_delivery_channel": 0.34,
    "contested_nonservice": 0.16,
    "unknown": 0.12,
}
CHANNEL_SCORE = {
    "efile_docket_entry": 0.60,
    "docket_notice": 0.68,
    "court_order_copy": 0.63,
    "secretary_email": 0.45,
    "mail": 0.70,
    "personal_service": 0.90,
}
TRUTH_ADJ = {"PROVEN":0.08, "RECORD_RECITED":0.05, "USER_ASSERTED":0.0, "UNVERIFIED":-0.05, "DISPUTED":-0.08}

def clamp(x: float) -> float:
    return max(0.0, min(1.0, x))

def deficiency_tags(sp: dict) -> list[str]:
    tags: list[str] = []
    st = str(sp.get("status","unknown"))
    if "contested" in st:
        tags.append("CONTESTED_SERVICE")
    if st in ("unknown","partial_record"):
        tags.append("PROOF_PATH_INCOMPLETE")
    if not sp.get("locator"):
        tags.append("LOCATOR_MISSING")
    if not sp.get("source_artifact"):
        tags.append("SOURCE_ARTIFACT_MISSING")
    if sp.get("delivery_channel") in (None, "", "secretary_email"):
        tags.append("DELIVERY_CHANNEL_NEEDS_RECORD_SUPPORT")
    if not sp.get("served_date"):
        tags.append("SERVED_DATE_MISSING")
    return sorted(set(tags))

def load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))

def write_json(path: Path, payload: dict) -> None:
    path.write_text(json.dumps(payload, indent=2), encoding="utf-8")

def main() -> int:
    parser = argparse.ArgumentParser(description="Build service confidence and deficiency rails")
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()
    try:
        orders = load_json(DATA / "orders.json").get("orders", [])
        service_rows = load_json(DATA / "service_proofs.json").get("service_proofs", [])
        qlinks = load_json(DATA / "order_evidence_quote_lock_links.json").get("links", [])
        ql_by_order: dict[str, list] = {}
        ql_by_service: dict[str, list] = {}
        for link in qlinks:
            for oid in link.get("order_ids", []):
                ql_by_order.setdefault(oid, []).append(link)
            for sid in link.get("service_ids", []):
                ql_by_service.setdefault(sid, []).append(link)

        service_scores = []
        for sp in service_rows:
            st = str(sp.get("status","unknown"))
            ttag = str(sp.get("truth_tag","USER_ASSERTED")).upper()
            base = STATUS_SCORE.get(st, 0.2)
            ch = CHANNEL_SCORE.get(str(sp.get("delivery_channel","")), 0.5)
            qhits = len(ql_by_service.get(sp.get("service_id"), []))
            deficit = deficiency_tags(sp)
            penalty = min(0.2, 0.03 * len(deficit))
            score = clamp(0.55*base + 0.25*ch + TRUTH_ADJ.get(ttag,0.0) + min(0.1, qhits * 0.03) - penalty)
            service_scores.append({
                "service_id": sp.get("service_id"),
                "order_id": sp.get("order_id"),
                "case_id": sp.get("case_id"),
                "lane": next((o.get("lane") for o in orders if o.get("order_id")==sp.get("order_id")), None),
                "service_kind": sp.get("service_kind"),
                "delivery_channel": sp.get("delivery_channel"),
                "status": st,
                "truth_tag": sp.get("truth_tag"),
                "service_confidence_score": round(score, 3),
                "confidence_band": "SOLID" if score >= 0.75 else "WATCH" if score >= 0.45 else "FRAGILE",
                "deficiency_tags": deficit,
                "quote_lock_link_count": qhits,
                "provenance_jump_hints": [sp.get("service_id"), sp.get("source_artifact"), sp.get("locator")],
                "resolution_target": "Promote to SOLID by attaching exact proof artifact, timestamp, and service pathway evidence."
            })

        by_order: dict[str, list] = {}
        for ss in service_scores:
            by_order.setdefault(ss["order_id"], []).append(ss)

        order_scores = []
        for o in orders:
            oid = o.get("order_id")
            linked = by_order.get(oid, [])
            if linked:
                avg = sum(x["service_confidence_score"] for x in linked) / len(linked)
                min_score = min(x["service_confidence_score"] for x in linked)
                chain = clamp(0.55*avg + 0.25*min_score + min(0.12, len(linked)*0.03) + min(0.1, len(ql_by_order.get(oid, []))*0.02))
                defs = sorted(set(tag for x in linked for tag in x["deficiency_tags"]))
            else:
                chain = 0.08 if str(o.get("service_status","unknown")) == "unknown" else 0.15
                defs = ["NO_SERVICE_PROOF_LINKED"]
            if str(o.get("service_status","")) .startswith("contested"):
                defs = sorted(set(defs + ["ORDER_SERVICE_STATUS_CONTESTED"]))
                chain = clamp(chain - 0.08)
            if not o.get("service_link_ids"):
                defs = sorted(set(defs + ["ORDER_SERVICE_LINK_IDS_EMPTY"]))
            order_scores.append({
                "order_id": oid,
                "case_id": o.get("case_id"),
                "lane": o.get("lane"),
                "entered_date": o.get("entered_date"),
                "title": o.get("title"),
                "service_status": o.get("service_status", "unknown"),
                "service_chain_score": round(chain, 3),
                "service_band": "SOLID" if chain >= 0.75 else "WATCH" if chain >= 0.45 else "FRAGILE",
                "service_proof_count": len(linked),
                "quote_lock_link_count": len(ql_by_order.get(oid, [])),
                "deficiency_tags": defs,
                "controlling_candidate": str(o.get("status","")).startswith("controlling"),
                "provenance_jump_hints": [oid, *[x["service_id"] for x in linked]],
                "resolution_target": "Attach service proof chain and exact notice/order text anchors for resilient order chronology."
            })

        lane_rollup: dict[str, dict] = {}
        for row in order_scores:
            lane_rollup.setdefault(row["lane"], {"scores": [], "counts": {"SOLID":0,"WATCH":0,"FRAGILE":0}, "deficiency": {}})
            lane_rollup[row["lane"]]["scores"].append(row["service_chain_score"])
            lane_rollup[row["lane"]]["counts"][row["service_band"]] += 1
            for tag in row["deficiency_tags"]:
                lane_rollup[row["lane"]]["deficiency"][tag] = lane_rollup[row["lane"]]["deficiency"].get(tag, 0) + 1
        lane_summary = []
        for lane, info in sorted(lane_rollup.items()):
            avg = sum(info["scores"]) / len(info["scores"]) if info["scores"] else 0.0
            lane_summary.append({
                "lane": lane,
                "order_count": len(info["scores"]),
                "avg_service_chain_score": round(avg, 3),
                "service_band": "SOLID" if avg >= 0.75 else "WATCH" if avg >= 0.45 else "FRAGILE",
                "fragile_orders": info["counts"]["FRAGILE"],
                "watch_orders": info["counts"]["WATCH"],
                "solid_orders": info["counts"]["SOLID"],
                "top_deficiencies": [k for k,_ in sorted(info["deficiency"].items(), key=lambda kv:(-kv[1], kv[0]))[:5]]
            })

        payload = {
            "generated_at": datetime.now().isoformat(timespec="seconds"),
            "summary": {
                "order_count": len(order_scores),
                "service_proof_count": len(service_scores),
                "avg_order_service_chain_score": round(sum(r["service_chain_score"] for r in order_scores) / max(1, len(order_scores)), 3),
                "solid_orders": sum(1 for r in order_scores if r["service_band"]=="SOLID"),
                "watch_orders": sum(1 for r in order_scores if r["service_band"]=="WATCH"),
                "fragile_orders": sum(1 for r in order_scores if r["service_band"]=="FRAGILE"),
                "contested_orders": sum(1 for r in order_scores if "ORDER_SERVICE_STATUS_CONTESTED" in r["deficiency_tags"]),
            },
            "filters": {
                "lanes": sorted({r["lane"] for r in order_scores if r.get("lane")}),
                "service_bands": ["SOLID", "WATCH", "FRAGILE"],
                "statuses": sorted({r.get("service_status", "unknown") for r in order_scores}),
                "deficiency_tags": sorted({t for r in order_scores for t in r.get("deficiency_tags", [])}),
            },
            "lane_summary": lane_summary,
            "orders": order_scores,
            "service_proofs": service_scores,
        }
        def_payload = {
            "generated_at": payload["generated_at"],
            "summary": {
                "deficiency_count": sum(len(r.get("deficiency_tags", [])) for r in order_scores),
                "high_severity_count": sum(1 for r in order_scores for t in r.get("deficiency_tags", []) if ("CONTESTED" in t or "NO_SERVICE" in t)),
            },
            "items": [
                {
                    "ledger_id": f"DEF-{r['order_id']}-{tag}",
                    "lane": r.get("lane"),
                    "order_id": r["order_id"],
                    "tag": tag,
                    "severity": "HIGH" if ("CONTESTED" in tag or "NO_SERVICE" in tag) else "MEDIUM",
                    "service_chain_score": r["service_chain_score"],
                    "resolution_target": "Promote order service chain with exact proof artifact + date/time path + linked order notice.",
                    "provenance_jump_hints": r.get("provenance_jump_hints", []),
                }
                for r in order_scores for tag in r.get("deficiency_tags", [])
            ],
        }
        if args.dry_run:
            print(json.dumps({"service_confidence": payload["summary"], "deficiency_ledger": def_payload["summary"]}, indent=2))
            return 0
        write_json(DATA / "service_confidence.json", payload)
        write_json(DATA / "service_deficiency_ledger.json", def_payload)
        print(json.dumps({"status":"ok", "orders":len(order_scores), "service_proofs":len(service_scores)}, indent=2))
        return 0
    except Exception as exc:
        print(json.dumps({"status":"error", "error": str(exc)}, indent=2))
        return 1

if __name__ == "__main__":
    raise SystemExit(main())
