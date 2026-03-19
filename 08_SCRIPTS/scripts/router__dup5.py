from fastapi import APIRouter
from fastapi.responses import JSONResponse
import os, json, time

router = APIRouter()
DELIV_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../deliverables"))

@router.post("/build")
async def build():
    nodes = [{"id":"Watson","type":"entity"},{"id":"Shady Oaks","type":"entity"},{"id":"Alden","type":"entity"}]
    edges = [{"from":"Shady Oaks","to":"Alden","rel":"ownership"},{"from":"Watson","to":"Shady Oaks","rel":"contract"}]
    out_dir = os.path.join(DELIV_DIR, "graph")
    os.makedirs(out_dir, exist_ok=True)
    with open(os.path.join(out_dir, "nodes.csv"), "w", encoding="utf-8") as f:
        f.write("id,type\n" + "\n".join(f"{n['id']},{n['type']}" for n in nodes))
    with open(os.path.join(out_dir, "edges.csv"), "w", encoding="utf-8") as f:
        f.write("from,to,rel\n" + "\n".join(f"{e['from']},{e['to']},{e['rel']}" for e in edges))
    html = "<html><body><h1>Nexus Graph (scaffold)</h1><p>Open nodes.csv & edges.csv in Neo4j importer or your viewer.</p></body></html>"
    viewer = os.path.join(out_dir, "graph.html")
    with open(viewer, "w", encoding="utf-8") as f:
        f.write(html)
    return JSONResponse({"viewer": viewer, "nodes": len(nodes), "edges": len(edges)})
