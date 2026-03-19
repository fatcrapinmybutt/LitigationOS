import json, os, pathlib
from authorities.util import ensure_dir

def build_edges(authorities_nodes_path: str, case_events_path: str, out_edges_path: str):
    # case_events is expected to be a JSONL of extracted events with fields:
    # {id, actors:[...], actions:[...], citations:[...] (e.g., ["MCL 600.2918","Fed. R. Civ. P. 65"]), dates:[], evidence_path:...}
    auth = {}
    for line in open(authorities_nodes_path, 'r', encoding='utf-8'):
        n = json.loads(line)
        auth[n["citation"]] = n["id"]

    edges = []
    if os.path.exists(case_events_path):
        for line in open(case_events_path, 'r', encoding='utf-8'):
            ev = json.loads(line)
            ev_id = ev.get("id")
            ev_cites = ev.get("citations", [])
            for cite in ev_cites:
                if cite in auth:
                    edges.append({
                        "from": ev_id,
                        "to": auth[cite],
                        "type": "authority",
                        "label": "Cites / Governed by",
                        "evidence": ev.get("evidence_path","")
                    })
    ensure_dir(str(pathlib.Path(out_edges_path).parent))
    with open(out_edges_path, 'w', encoding='utf-8') as f:
        for e in edges:
            f.write(json.dumps(e, ensure_ascii=False) + "\n")
    print(f"Wrote {len(edges)} edges to {out_edges_path}")
