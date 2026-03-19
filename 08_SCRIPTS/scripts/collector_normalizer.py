import os, re, json, csv, hashlib
from bs4 import BeautifulSoup

ART_DIR = os.path.join(os.path.dirname(__file__), "..", "artifacts")
DATA_DIR = os.path.join(os.path.dirname(__file__), "..", "data")
os.makedirs(DATA_DIR, exist_ok=True)

def sha(s): return hashlib.sha256(s.encode("utf-8")).hexdigest()

def extract_graph_from_html(path):
    # Flexible parser: look for <script> blocks containing 'nodes' or 'edges' JSON.
    with open(path, "r", encoding="utf-8", errors="ignore") as f:
        html = f.read()
    soup = BeautifulSoup(html, "lxml")
    scripts = soup.find_all("script")
    nodes, edges = [], []
    for sc in scripts:
        txt = sc.get_text(" ", strip=False) or ""
        # Try to find JSON arrays in the script
        for key in ["nodes", "Nodes", "graphNodes"]:
            m = re.search(rf"{key}\s*=\s*(\[.*?\])", txt, re.S)
            if m:
                try:
                    nodes.extend(json.loads(m.group(1)))
                except Exception:
                    pass
        for key in ["edges", "Edges", "graphEdges", "links"]:
            m = re.search(rf"{key}\s*=\s*(\[.*?\])", txt, re.S)
            if m:
                try:
                    edges.extend(json.loads(m.group(1)))
                except Exception:
                    pass
    return nodes, edges

def normalize(artifacts):
    node_rows, edge_rows = [], []
    for fname in artifacts:
        path = os.path.join(ART_DIR, fname)
        if not os.path.exists(path): 
            continue
        nodes, edges = extract_graph_from_html(path)
        for n in nodes:
            nid = str(n.get("id") or n.get("key") or n.get("name"))
            if not nid: 
                continue
            label = n.get("label") or n.get("type") or "Node"
            ntype = n.get("type") or ""
            date = n.get("date") or ""
            summary = n.get("summary") or n.get("title") or ""
            node_rows.append([nid, label, ntype, date, summary, fname, sha(nid+summary)])
        for e in edges:
            src = str(e.get("source") or e.get("src"))
            dst = str(e.get("target") or e.get("dst"))
            rel = e.get("rel") or e.get("type") or "LINK"
            if src and dst:
                edge_rows.append([src, rel, dst, fname])
    return node_rows, edge_rows

def main():
    artifacts = [f for f in os.listdir(ART_DIR) if f.endswith(".html")]
    nodes, edges = normalize(artifacts)
    with open(os.path.join(DATA_DIR, "nodes.csv"), "w", newline="", encoding="utf-8") as f:
        csv.writer(f).writerow(["id","label","type","date","summary","source_artifacts","hash"])
        csv.writer(f).writerows(nodes)
    with open(os.path.join(DATA_DIR, "edges.csv"), "w", newline="", encoding="utf-8") as f:
        csv.writer(f).writerow(["src","rel","dst","source_artifacts"])
        csv.writer(f).writerows(edges)
    print(f"Wrote {len(nodes)} nodes and {len(edges)} edges")

if __name__ == "__main__":
    main()
