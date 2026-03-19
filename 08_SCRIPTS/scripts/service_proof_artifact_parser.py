from __future__ import annotations
import argparse, json, re, hashlib
from datetime import datetime
from pathlib import Path
from io_extractors import extract_text_pages

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data"
IMPORTS = ROOT / "imports" / "service_proofs"

CASE_RE = re.compile(r"\b(20\d{2}-\d{6,7}-[A-Z]{2,4})\b")
ORDER_RE = re.compile(r"\b(ORD-[A-Z0-9\-]+)\b")
SERVICE_RE = re.compile(r"\b(SRV-[A-Z0-9\-]+)\b")

def load_json(path: Path, default):
    if not path.exists():
        return default
    return json.loads(path.read_text(encoding="utf-8"))

def save_json(path: Path, payload):
    path.write_text(json.dumps(payload, indent=2), encoding="utf-8")

def find_dates(txt: str) -> list[str]:
    out = []
    for m in re.finditer(r"(20\d{2})[-_/](\d{2})[-_/](\d{2})", txt):
        out.append(f"{m.group(1)}-{m.group(2)}-{m.group(3)}")
    for m in re.finditer(r"(?<!\d)(\d{1,2})/(\d{1,2})/(20\d{2})(?!\d)", txt):
        out.append(f"{int(m.group(3)):04d}-{int(m.group(1)):02d}-{int(m.group(2)):02d}")
    return list(dict.fromkeys(out))

def channel_hits(txt_low: str) -> list[str]:
    chans = []
    patterns = [
        ("efile_docket_entry", ["efile", "e-file", "docket entry"]),
        ("docket_notice", ["notice of hearing", "notice"]),
        ("court_order_copy", ["order", "signed order"]),
        ("mail", ["mailed", "mailing", "us mail", "first class"]),
        ("personal_service", ["personally served", "served in person", "personal service"]),
        ("secretary_email", ["secretary", "email"]),
    ]
    for key, needles in patterns:
        if any(n in txt_low for n in needles):
            chans.append(key)
    return chans

def parse_artifact(path: Path) -> dict:
    pages = extract_text_pages(path)
    txt = "\n".join(str(p.get("text","")) for p in pages)
    low = txt.lower()
    page_count = len(pages)
    dates = find_dates(txt)
    artifacts = {
        "artifact_id": "SAP-" + hashlib.md5(str(path).encode()).hexdigest()[:12],
        "file_path": str(path.relative_to(ROOT)).replace("\\","/"),
        "artifact_name": path.name,
        "artifact_type": path.suffix.lower().lstrip(".") or "bin",
        "page_count": page_count,
        "is_seed_artifact": path.name.startswith("_seed_"),
        "service_ids_detected": sorted(set(SERVICE_RE.findall(txt))),
        "order_ids_detected": sorted(set(ORDER_RE.findall(txt))),
        "case_ids_detected": sorted(set(CASE_RE.findall(txt))),
        "served_dates_detected": dates[:8],
        "channels_detected": channel_hits(low),
        "keywords": [k for k in ["affidavit","proof of service","notice","served","service","hearing"] if k in low],
        "snippet": re.sub(r"\s+"," ", txt)[:400],
        "parse_confidence": 0.0,
        "provenance_jump_hints": [str(path.relative_to(ROOT)).replace("\\","/")],
    }
    score = 0.15
    score += 0.2 if artifacts["service_ids_detected"] else 0
    score += 0.2 if artifacts["order_ids_detected"] else 0
    score += 0.15 if artifacts["served_dates_detected"] else 0
    score += 0.15 if artifacts["channels_detected"] else 0
    score += 0.1 if ("affidavit" in low or "proof of service" in low) else 0
    score += 0.05 if artifacts["case_ids_detected"] else 0
    artifacts["parse_confidence"] = round(min(score, 0.99), 3)
    artifacts["promotion_readiness"] = "SEED_ONLY" if artifacts["is_seed_artifact"] else ("READY" if artifacts["parse_confidence"] >= 0.55 else "WATCH")
    return artifacts

def main() -> int:
    parser = argparse.ArgumentParser(description="Parse affidavit/notice service-proof artifacts and promote service chains")
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    service_payload = load_json(DATA / "service_proofs.json", {"service_proofs": []})
    services = service_payload.get("service_proofs", [])
    artifacts = []
    if IMPORTS.exists():
        for p in sorted(IMPORTS.rglob("*")):
            if p.is_file() and p.suffix.lower() in {".txt",".md",".pdf",".docx",".json"}:
                artifacts.append(parse_artifact(p))

    # Build promotion candidates (skip seed-only so scores don't get fake confidence)
    promotions = []
    art_by_service = {}
    art_by_order = {}
    for a in artifacts:
        for sid in a["service_ids_detected"]:
            art_by_service.setdefault(sid, []).append(a)
        for oid in a["order_ids_detected"]:
            art_by_order.setdefault(oid, []).append(a)

    updated = 0
    for sp in services:
        sid = sp.get("service_id")
        oid = sp.get("order_id")
        candidates = [a for a in art_by_service.get(sid, []) if not a.get("is_seed_artifact")]
        if not candidates and oid:
            candidates = [a for a in art_by_order.get(oid, []) if not a.get("is_seed_artifact")]
        if not candidates:
            continue
        best = sorted(candidates, key=lambda a: (-a["parse_confidence"], a["file_path"]))[0]
        before = {
            "status": sp.get("status"),
            "source_artifact": sp.get("source_artifact"),
            "locator": sp.get("locator"),
            "delivery_channel": sp.get("delivery_channel"),
            "served_date": sp.get("served_date"),
        }
        # Add provenance fields
        sp["source_artifact"] = best["file_path"]
        sp.setdefault("artifact_links", [])
        if best["file_path"] not in sp["artifact_links"]:
            sp["artifact_links"].append(best["file_path"])
        if not sp.get("locator"):
            sp["locator"] = f"{best['file_path']}::p1"
        if not sp.get("delivery_channel") and best["channels_detected"]:
            sp["delivery_channel"] = best["channels_detected"][0]
        if not sp.get("served_date") and best["served_dates_detected"]:
            sp["served_date"] = best["served_dates_detected"][0]
        # promote only if artifact strongly indicates proof/affidavit
        low_snip = (best.get("snippet") or "").lower()
        if ("affidavit" in low_snip or "proof of service" in low_snip) and sp.get("status") in (None,"unknown","partial_record"):
            sp["status"] = "proof_attached"
        after = {
            "status": sp.get("status"),
            "source_artifact": sp.get("source_artifact"),
            "locator": sp.get("locator"),
            "delivery_channel": sp.get("delivery_channel"),
            "served_date": sp.get("served_date"),
        }
        promotions.append({
            "promotion_id": f"SPROM-{sid}",
            "service_id": sid,
            "order_id": oid,
            "artifact_id": best["artifact_id"],
            "artifact_path": best["file_path"],
            "artifact_parse_confidence": best["parse_confidence"],
            "changes": {k: {"before": before.get(k), "after": after.get(k)} for k in after if before.get(k) != after.get(k)},
            "promotion_band": "SOLID" if best["parse_confidence"] >= 0.75 else "WATCH",
            "provenance_jump_hints": [sid, oid, best["file_path"]],
        })
        updated += 1

    parse_payload = {
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "summary": {
            "artifact_count": len(artifacts),
            "seed_artifact_count": sum(1 for a in artifacts if a.get("is_seed_artifact")),
            "ready_artifacts": sum(1 for a in artifacts if a.get("promotion_readiness") == "READY"),
            "service_ids_detected": len({sid for a in artifacts for sid in a.get("service_ids_detected", [])}),
            "order_ids_detected": len({oid for a in artifacts for oid in a.get("order_ids_detected", [])}),
        },
        "filters": {
            "channels": sorted({c for a in artifacts for c in a.get("channels_detected", [])}),
            "readiness": ["READY","WATCH","SEED_ONLY"],
        },
        "artifacts": artifacts,
        "resolution_targets": [
            "Drop actual affidavit/notice PDFs into imports/service_proofs for non-seed service-chain promotion.",
            "Keep artifact filenames stable so service confidence and provenance jump hints remain deterministic.",
        ]
    }
    prom_payload = {
        "generated_at": parse_payload["generated_at"],
        "summary": {
            "promotions_applied": updated,
            "services_total": len(services),
            "service_rows_with_artifact_links": sum(1 for s in services if s.get("artifact_links")),
        },
        "promotions": promotions,
    }

    if not args.dry_run:
        save_json(DATA / "service_artifact_parse_results.json", parse_payload)
        save_json(DATA / "service_artifact_promotions.json", prom_payload)
        save_json(DATA / "service_proofs.json", service_payload)
    print(json.dumps({"status":"ok","artifact_count":len(artifacts),"promotions":updated}, indent=2))
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
