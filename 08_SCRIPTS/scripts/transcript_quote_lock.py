from __future__ import annotations
from pathlib import Path
import json
import re
from datetime import datetime

ROOT = Path(__file__).resolve().parents[1]

def _load(rel: str):
    return json.loads((ROOT / rel).read_text(encoding="utf-8"))

def _save(rel: str, payload):
    p = ROOT / rel
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(payload, indent=2), encoding="utf-8")

def _date_candidates(*vals):
    out = []
    for v in vals:
        if not v:
            continue
        txt = str(v)
        for m in re.finditer(r"(20\d{2})[-_/](\d{2})[-_/](\d{2})", txt):
            out.append(f"{m.group(1)}-{m.group(2)}-{m.group(3)}")
        for m in re.finditer(r"(?<!\d)(\d{1,2})/(\d{1,2})/(20\d{2})(?!\d)", txt):
            out.append(f"{int(m.group(3)):04d}-{int(m.group(1)):02d}-{int(m.group(2)):02d}")
    return list(dict.fromkeys(out))

def main():
    orders = _load("data/orders.json").get("orders", [])
    services = _load("data/service_proofs.json").get("service_proofs", [])
    atoms = _load("data/evidence_atoms.json").get("atoms", [])
    matrix_rows = _load("data/exhibit_matrix.json").get("rows", [])

    order_by_id = {o.get("order_id"): o for o in orders}
    service_by_id = {s.get("service_id"): s for s in services}
    orders_by_lane_date = {}
    for o in orders:
        orders_by_lane_date.setdefault((o.get("lane"), o.get("entered_date")), []).append(o)
    ex_to_rows = {}
    for r in matrix_rows:
        ex_to_rows.setdefault(r.get("exhibit_id"), []).append(r)

    quotes = []
    for a in atoms:
        pin = a.get("pinpoint") or "PINPOINT_MISSING"
        low = pin.lower()
        if re.search(r"\bp\.?\s*\d+|\bpage\b|\bline\b", low):
            band = "EXACT_OR_NEAR_EXACT"
        elif "pending" in low or "missing" in low:
            band = "EXTRACT_TARGET"
        elif "retained" in low or "timeline" in low or "docket" in low:
            band = "RECORD_ANCHOR"
        else:
            band = "ANCHOR_TARGET"
        label = a.get("label") or a.get("atom_id")
        quotes.append({
            "quote_id": f"QTL-{a.get('atom_id')}",
            "lane": a.get("lane"),
            "quote_lock_band": band,
            "source_kind": a.get("source_type") or "unknown",
            "source_ref": a.get("source_ref"),
            "evidence_atom_id": a.get("atom_id"),
            "label": label,
            "pinpoint": pin,
            "quote_text_exact": None,
            "quote_preview": f"[EXTRACT_TARGET] {label}" if band in {"EXTRACT_TARGET","ANCHOR_TARGET"} else f"[ANCHOR] {label}",
            "hearing_or_order_date": (_date_candidates(label, a.get("source_ref"), pin) or [None])[0],
            "truth_tag": a.get("truth_tag") or "UNVERIFIED",
            "provenance_jump_hint": a.get("source_ref") or a.get("atom_id"),
            "resolution_target": "Replace preview with exact transcript/order quote + page-line pinpoint when source text is harvested."
        })

    for dt, lane, label in [
        ("2025-02-28","MEEK3","PPO show-cause ruling hearing transcript target (criminal contempt + 14 days jail)"),
        ("2025-06-12","MEEK3","PPO show-cause ruling hearing transcript target (45-day suspended jail + $100 fine)"),
        ("2025-09-09","MEEK2","Custody objection continuance hearing/order transcript target (assessment-conditioned continuation)")
    ]:
        qid = f"QTL-TARGET-{dt.replace('-','')}"
        if any(q["quote_id"] == qid for q in quotes):
            continue
        quotes.append({
            "quote_id": qid,
            "lane": lane,
            "quote_lock_band": "HEARING_TARGET",
            "source_kind": "transcript_hearing_target",
            "source_ref": f"hearing_{dt}",
            "evidence_atom_id": None,
            "label": label,
            "pinpoint": "Transcript page-line quote extraction target",
            "quote_text_exact": None,
            "quote_preview": f"[DISCOVERY_TARGET] {label}",
            "hearing_or_order_date": dt,
            "truth_tag": "USER_ASSERTED",
            "provenance_jump_hint": dt,
            "resolution_target": "Harvest transcript PDF/text; extract verbatim ruling language and colloquy; bind page-line."
        })

    links = []
    for q in quotes:
        lane = q.get("lane")
        src = q.get("source_ref")
        atom_id = q.get("evidence_atom_id")
        order_ids, service_ids, vehicle_ids = [], [], []
        notes, scores = [], []
        dates = _date_candidates(q.get("hearing_or_order_date"), q.get("label"), src, q.get("pinpoint"))

        if src in service_by_id:
            s = service_by_id[src]
            service_ids.append(src)
            if s.get("order_id"):
                order_ids.append(s["order_id"])
            notes.append("Direct service source_ref match"); scores.append(0.4)
        if src in order_by_id:
            order_ids.append(src)
            notes.append("Direct order source_ref match"); scores.append(0.5)

        for dt in dates:
            for o in orders_by_lane_date.get((lane, dt), []):
                if o.get("order_id") not in order_ids:
                    order_ids.append(o["order_id"]); notes.append(f"Lane/date match {dt}"); scores.append(0.25)
            for s in services:
                if s.get("lane") == lane and str(s.get("served_date") or "").startswith(dt):
                    if s.get("service_id") not in service_ids:
                        service_ids.append(s["service_id"]); notes.append(f"Service date match {dt}"); scores.append(0.15)
                    if s.get("order_id") and s["order_id"] not in order_ids:
                        order_ids.append(s["order_id"]); scores.append(0.1)

        atom = next((a for a in atoms if a.get("atom_id") == atom_id), None)
        for ex in (atom or {}).get("linked_exhibits", []):
            for row in ex_to_rows.get(ex, []):
                if row.get("vehicle_id") and row["vehicle_id"] not in vehicle_ids:
                    vehicle_ids.append(row["vehicle_id"])
                for oid in row.get("order_links", []) if isinstance(row.get("order_links"), list) else []:
                    if oid not in order_ids:
                        order_ids.append(oid); notes.append(f"ExhibitMatrix order_links via {ex}"); scores.append(0.2)
            if ex_to_rows.get(ex):
                notes.append(f"ExhibitMatrix hit {ex}"); scores.append(0.1)

        for oid in list(dict.fromkeys(order_ids)):
            for s in services:
                if s.get("order_id") == oid and s.get("service_id") not in service_ids:
                    service_ids.append(s["service_id"]); scores.append(0.1)

        order_ids = list(dict.fromkeys(order_ids))
        service_ids = list(dict.fromkeys(service_ids))
        vehicle_ids = list(dict.fromkeys(vehicle_ids))
        conf = min(1.0, round(sum(scores), 2)) if scores else 0.0

        band = q.get("quote_lock_band")
        if band == "EXACT_OR_NEAR_EXACT":
            status = "QUOTELOCK_READY"
        elif band == "RECORD_ANCHOR":
            status = "ANCHOR_READY"
        elif band == "HEARING_TARGET":
            status = "DISCOVERY_TARGET"
        else:
            status = "EXTRACT_TARGET"

        links.append({
            "link_id": f"QLINK-{q['quote_id']}",
            "quote_id": q["quote_id"],
            "lane": lane,
            "quote_status": status,
            "quote_confidence": conf,
            "order_ids": order_ids,
            "service_ids": service_ids,
            "evidence_atom_ids": [atom_id] if atom_id else [],
            "vehicle_ids": vehicle_ids,
            "anchor_dates": dates,
            "link_notes": notes[:6] if notes else ["No deterministic join yet; remains discovery target."],
            "provenance_jump_hints": [q.get("provenance_jump_hint")] + order_ids[:2] + service_ids[:2]
        })

    exact_count = sum(1 for q in quotes if q.get("quote_lock_band") == "EXACT_OR_NEAR_EXACT")
    summary = {
        "quote_count": len(quotes),
        "exact_or_near_exact_count": exact_count,
        "extract_target_count": sum(1 for q in quotes if q.get("quote_lock_band") in {"EXTRACT_TARGET","ANCHOR_TARGET","HEARING_TARGET"}),
        "anchor_ready_count": sum(1 for l in links if l.get("quote_status") == "ANCHOR_READY"),
        "quotes_with_order_links": sum(1 for l in links if l.get("order_ids")),
        "quotes_with_service_links": sum(1 for l in links if l.get("service_ids")),
        "quotes_with_vehicle_links": sum(1 for l in links if l.get("vehicle_ids")),
        "quote_link_coverage_score": round(sum(1 for l in links if l.get("order_ids") or l.get("service_ids")) / max(1, len(links)), 3),
        "quote_lock_progress_score": round((exact_count*1.0 + sum(1 for q in quotes if q.get("quote_lock_band") == "RECORD_ANCHOR")*0.6) / max(1, len(quotes)), 3)
    }
    filters = {
        "lanes": sorted({q.get("lane") for q in quotes if q.get("lane")}),
        "quote_lock_bands": sorted({q.get("quote_lock_band") for q in quotes}),
        "source_kinds": sorted({q.get("source_kind") for q in quotes}),
        "quote_statuses": sorted({l.get("quote_status") for l in links})
    }

    _save("data/transcript_quotes.json", {
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "summary": summary,
        "filters": filters,
        "quotes": quotes
    })
    _save("data/order_evidence_quote_lock_links.json", {
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "summary": summary,
        "links": links
    })
    print({"quotes": len(quotes), "links": len(links), "status": "OK"})

if __name__ == "__main__":
    main()
