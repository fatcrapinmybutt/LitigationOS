import os, csv, json, datetime, shutil, zipfile

class GraphImporter:
    """
    Creates a Neo4j-ready import pack from a graph run (nodes.csv, edges.csv).
    - Infers headers
    - Generates import.cypher with indexes/constraints and LOAD CSV statements
    - Bundles CSVs + cypher + README into a zip
    """
    def __init__(self):
        self.root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        self.data_dir = os.path.join(self.root, "..", "..", "data", "graph_runs")
        os.makedirs(self.data_dir, exist_ok=True)

    def _latest_run(self):
        runs = [d for d in os.listdir(self.data_dir) if os.path.isdir(os.path.join(self.data_dir, d))]
        return sorted(runs)[-1] if runs else None

    def _infer_headers(self, path):
        with open(path, "r", encoding="utf-8", errors="ignore") as f:
            reader = csv.reader(f)
            headers = next(reader, [])
        return headers

    def generate_import_pack(self, run_id: str | None = None) -> dict:
        rid = run_id or self._latest_run()
        if not rid:
            raise RuntimeError("No graph runs found.")
        run_dir = os.path.join(self.data_dir, rid)
        nodes_csv = os.path.join(run_dir, "nodes.csv")
        edges_csv = os.path.join(run_dir, "edges.csv")
        if not os.path.exists(nodes_csv) or not os.path.exists(edges_csv):
            raise RuntimeError(f"Run {rid} missing nodes.csv or edges.csv")

        node_headers = self._infer_headers(nodes_csv)
        edge_headers = self._infer_headers(edges_csv)

        node_id_col = next((h for h in node_headers if h.lower() in ["id","node","node_id"]), node_headers[0] if node_headers else "id")
        node_label_col = next((h for h in node_headers if h.lower() in ["label","labels","type"]), None)
        edge_src_col = next((h for h in edge_headers if h.lower() in ["from","source","src","start","start_id"]), edge_headers[0] if edge_headers else "from")
        edge_dst_col = next((h for h in edge_headers if h.lower() in ["to","target","dst","end","end_id"]), edge_headers[1] if len(edge_headers)>1 else "to")
        edge_type_col = next((h for h in edge_headers if h.lower() in ["type","rel","relationship"]), None)

        ts = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        pack_dir = os.path.join(run_dir, f"neo4j_pack_{ts}")
        os.makedirs(pack_dir, exist_ok=True)

        # Copy CSVs
        nodes_copy = os.path.join(pack_dir, "nodes.csv")
        edges_copy = os.path.join(pack_dir, "edges.csv")
        shutil.copyfile(nodes_csv, nodes_copy)
        shutil.copyfile(edges_csv, edges_copy)

        # Generate import.cypher
        label_fallback = "Entity"
        rel_fallback = "RELATED_TO"
        cypher = f"""
// Generated {ts}
CREATE CONSTRAINT node_id_unique IF NOT EXISTS FOR (n:{label_fallback}) REQUIRE n.{node_id_col} IS UNIQUE;

USING PERIODIC COMMIT 500
LOAD CSV WITH HEADERS FROM 'file:///nodes.csv' AS row
WITH row
MERGE (n:`{label_fallback}` {{ {node_id_col}: row.{node_id_col} }})
SET n += row;

USING PERIODIC COMMIT 500
LOAD CSV WITH HEADERS FROM 'file:///edges.csv' AS row
WITH row
MATCH (a:`{label_fallback}` {{ {node_id_col}: row.{edge_src_col} }})
MATCH (b:`{label_fallback}` {{ {node_id_col}: row.{edge_dst_col} }})
MERGE (a)-[r:REL]->(b)
SET r.type = coalesce(row.{edge_type_col}, '{rel_fallback}'), r += row;
"""
        if edge_type_col is None:
            cypher = cypher.replace("coalesce(row.None, '{rel_fallback}')", f"'{rel_fallback}'")

        cypher_path = os.path.join(pack_dir, "import.cypher")
        with open(cypher_path, "w", encoding="utf-8") as f:
            f.write(cypher)

        readme = f"""
Neo4j Import Pack for run {rid}

1) Copy nodes.csv, edges.csv, and import.cypher into Neo4j 'import' directory.
2) In Neo4j Browser, run:
   :use neo4j
   :auto USING PERIODIC COMMIT 500
   :source import.cypher

Assumptions:
- Node id column: {node_id_col}
- Fallback node label: {label_fallback}
- Edge source: {edge_src_col} → target: {edge_dst_col}
- Edge relationship stored in REL.type (fallback '{rel_fallback}')
"""
        readme_path = os.path.join(pack_dir, "README_NEO4J.txt")
        with open(readme_path, "w", encoding="utf-8") as f:
            f.write(readme.strip())

        # Zip pack
        zip_path = os.path.join(run_dir, f"neo4j_import_pack_{ts}.zip")
        with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as z:
            for p in [nodes_copy, edges_copy, cypher_path, readme_path]:
                z.write(p, arcname=os.path.basename(p))

        schema = {
            "run_id": rid,
            "node_headers": node_headers,
            "edge_headers": edge_headers,
            "node_id_col": node_id_col,
            "node_label_col": node_label_col,
            "edge_src_col": edge_src_col,
            "edge_dst_col": edge_dst_col,
            "edge_type_col": edge_type_col,
            "pack_dir": pack_dir,
            "zip_path": zip_path
        }
        return schema
