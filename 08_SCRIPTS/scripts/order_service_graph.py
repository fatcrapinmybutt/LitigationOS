from __future__ import annotations
from pathlib import Path
import json
from datetime import datetime

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data"

def _safe_read(path: Path, default):
    if not path.exists():
        return default
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return default

def build_order_service_graph() -> dict:
    orders_payload = _safe_read(DATA / "orders.json", {"orders": [], "order_chains": []})
    service_payload = _safe_read(DATA / "service_proofs.json", {"service_proofs": []})

    orders = orders_payload.get("orders", [])
    services = service_payload.get("service_proofs", [])

    nodes = []
    edges = []
    for o in orders:
        nodes.append({
            "id": o.get("order_id"),
            "type": "order",
            "label": o.get("title"),
            "case_id": o.get("case_id"),
            "lane": o.get("lane"),
            "entered_date": o.get("entered_date"),
            "status": o.get("status"),
            "truth_tag": o.get("truth_tag"),
            "service_status": o.get("service_status"),
            "proof_status": o.get("proof_status", "PARTIAL")
        })
        for prior in o.get("supersedes", []):
            edges.append({
                "from": o.get("order_id"),
                "to": prior,
                "relation": "SUPERSEDES",
                "status": "asserted",
                "truth_tag": o.get("truth_tag", "USER_ASSERTED")
            })

    for s in services:
        nodes.append({
            "id": s.get("service_id"),
            "type": "service_proof",
            "label": f"{s.get('service_kind')} · {s.get('status')}",
            "case_id": s.get("case_id"),
            "lane": None,
            "served_date": s.get("served_date"),
            "status": s.get("status"),
            "truth_tag": s.get("truth_tag")
        })
        edges.append({
            "from": s.get("service_id"),
            "to": s.get("order_id"),
            "relation": "SERVES_OR_NOTICES",
            "status": s.get("status"),
            "truth_tag": s.get("truth_tag", "USER_ASSERTED")
        })

    payload = {
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "summary": {
            "order_count": sum(1 for n in nodes if n.get("type") == "order"),
            "service_proof_count": sum(1 for n in nodes if n.get("type") == "service_proof"),
            "supersession_edge_count": sum(1 for e in edges if e.get("relation") == "SUPERSEDES"),
            "service_edge_count": sum(1 for e in edges if e.get("relation") == "SERVES_OR_NOTICES")
        },
        "chains": orders_payload.get("order_chains", []),
        "nodes": nodes,
        "edges": edges
    }
    (DATA / "order_supersession_service_graph.json").write_text(json.dumps(payload, indent=2), encoding="utf-8")
    return payload

if __name__ == "__main__":
    print(json.dumps(build_order_service_graph(), indent=2))
