import os, csv, json, datetime, shutil, zipfile, re

class GraphSchemaImporter:
    """
    Builds a Neo4j import pack with label- and relationship-aware Cypher.
    - Detects node id column + label column and emits per-label MERGE
    - Detects edge src/dst/type columns and emits per-type MERGE
    - Adds constraints for each label
    - Includes a fraud-queries bundle
    """
    def __init__(self):
        self.root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        self.base_runs = os.path.join(self.root, "..", "..", "data", "graph_runs")
        os.makedirs(self.base_runs, exist_ok=True)

    def _latest_run(self):
        runs = [d for d in os.listdir(self.base_runs) if os.path.isdir(os.path.join(self.base_runs, d))]
        return sorted(runs)[-1] if runs else None

    def _read_unique(self, path, col):
        vals = set()
        with open(path, "r", encoding="utf-8", errors="ignore") as f:
            reader = csv.DictReader(f)
            for i, row in enumerate(reader):
                v = (row.get(col) or "").strip()
                if v:
                    vals.add(v)
        return sorted(vals)

    def _sanitize_label(self, s):
        s = s.strip()
        s = re.sub(r'[^A-Za-z0-9_]', '_', s)
        if not s:
            return "Entity"
        if s[0].isdigit():
            s = "_" + s
        return s

    def _map_label(self, raw):
        low = raw.lower()
        if low in ["person","individual","human","owner"]:
            return "Person"
        if low in ["llc","company","corp","corporation","entity","management"]:
            return "LLC"
        if low in ["property","parcel","home","unit","lot","address"]:
            return "Property"
        if low in ["case","docket","proceeding"]:
            return "Case"
        if low in ["agent","registered_agent","ra"]:
            return "Agent"
        return self._sanitize_label(raw or "Entity")

    def _map_rel(self, raw):
        low = (raw or "").lower()
        mapping = {
            "owns": "OWNS",
            "owned_by": "OWNED_BY",
            "manages": "MANAGES",
            "leases": "LEASES",
            "files": "FILES",
            "sues": "SUES",
            "employs": "EMPLOYS",
            "registered_agent": "REGISTERED_AGENT",
            "agent_for": "REGISTERED_AGENT"
        }
        return mapping.get(low)

    def generate_schema_pack(self, run_id: str | None = None) -> dict:
        rid = run_id or self._latest_run()
        if not rid:
            raise RuntimeError("No graph runs found.")
        run_dir = os.path.join(self.base_runs, rid)
        nodes_csv = os.path.join(run_dir, "nodes.csv")
        edges_csv = os.path.join(run_dir, "edges.csv")
        if not os.path.exists(nodes_csv) or not os.path.exists(edges_csv):
            raise RuntimeError(f"Run {rid} missing nodes.csv or edges.csv")

        # Headers
        with open(nodes_csv, "r", encoding="utf-8", errors="ignore") as f:
            n_headers = next(csv.reader(f), [])
        with open(edges_csv, "r", encoding="utf-8", errors="ignore") as f:
            e_headers = next(csv.reader(f), [])

        node_id_col = next((h for h in n_headers if h.lower() in ["id","node","node_id"]), n_headers[0])
        node_label_col = next((h for h in n_headers if h.lower() in ["label","labels","type"]), None)
        edge_src_col = next((h for h in e_headers if h.lower() in ["from","source","src","start","start_id"]), e_headers[0])
        edge_dst_col = next((h for h in e_headers if h.lower() in ["to","target","dst","end","end_id"]), e_headers[1] if len(e_headers)>1 else e_headers[0])
        edge_type_col = next((h for h in e_headers if h.lower() in ["type","rel","relationship"]), None)

        # Unique values
        label_values = []
        if node_label_col:
            raw_vals = self._read_unique(nodes_csv, node_label_col)
            label_values = sorted(set(self._map_label(v) for v in raw_vals))[:50]  # cap to 50 labels
            if not label_values:
                label_values = ["Entity"]
        else:
            label_values = ["Entity"]

        rel_values = []
        if edge_type_col:
            raw_rel = self._read_unique(edges_csv, edge_type_col)
            rel_values = raw_rel[:100]  # cap to 100 distinct rels

        ts = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        pack_dir = os.path.join(run_dir, f"neo4j_schema_pack_{ts}")
        os.makedirs(pack_dir, exist_ok=True)

        # Compose Cypher
        lines = []
        lines.append(f"// Schema-aware import generated {ts}")
        # Constraints
        for L in label_values:
            lines.append(f"CREATE CONSTRAINT IF NOT EXISTS FOR (n:`{L}`) REQUIRE n.{node_id_col} IS UNIQUE;")

        # Node loads
        lines.append(f"USING PERIODIC COMMIT 500")
        lines.append(f"LOAD CSV WITH HEADERS FROM 'file:///nodes.csv' AS row")
        if node_label_col:
            for L in label_values:
                # filter rows to this label (case-insensitive compare)
                lines.append(f"WITH row WHERE toLower(row.{node_label_col}) = '{L.lower()}'")
                lines.append(f"MERGE (n:`{L}` {{ {node_id_col}: row.{node_id_col} }})")
                lines.append(f"SET n += row;")
                lines.append("")
        else:
            L = "Entity"
            lines.append(f"MERGE (n:`{L}` {{ {node_id_col}: row.{node_id_col} }})")
            lines.append(f"SET n += row;")

        # Edge loads
        lines.append("USING PERIODIC COMMIT 500")
        lines.append("LOAD CSV WITH HEADERS FROM 'file:///edges.csv' AS row")
        lines.append(f"MATCH (a {{ {node_id_col}: row.{edge_src_col} }})")
        lines.append(f"MATCH (b {{ {node_id_col}: row.{edge_dst_col} }})")
        if edge_type_col:
            # split known mappings vs fallback
            known = [rv for rv in rel_values if self._map_rel(rv)]
            unknown = [rv for rv in rel_values if not self._map_rel(rv)]
            for rv in known:
                rel = self._map_rel(rv)
                lines.append(f"WITH a,b,row WHERE toLower(row.{edge_type_col}) = '{rv.lower()}'")
                lines.append(f"MERGE (a)-[r:`{rel}`]->(b)")
                lines.append("SET r += row;")
                lines.append("")
            # fallback path
            lines.append("WITH a,b,row")
            lines.append("MERGE (a)-[r:REL]->(b)")
            if edge_type_col:
                lines.append(f"SET r.type = coalesce(row.{edge_type_col}, 'RELATED_TO'), r += row;")
            else:
                lines.append("SET r.type = 'RELATED_TO', r += row;")
        else:
            lines.append("MERGE (a)-[r:REL]->(b)")
            lines.append("SET r.type = 'RELATED_TO', r += row;")

        import_cypher = "\n".join(lines)
        cypher_path = os.path.join(pack_dir, "import.cypher")
        open(cypher_path, "w", encoding="utf-8").write(import_cypher)

        # Fraud queries pack
        fraud_queries = r"""
// FRAUD/ABUSE QUERIES

// 1) Common Registered Agent linking multiple LLCs
MATCH (a:LLC)-[:REGISTERED_AGENT]->(agent:Person)<-[:REGISTERED_AGENT]-(b:LLC)
WHERE a <> b
RETURN agent, collect(DISTINCT a.name) AS companiesA, collect(DISTINCT b.name) AS companiesB
LIMIT 100;

// 2) Round-robin ownership loops
MATCH (a:LLC)-[:OWNS]->(b:LLC)-[:OWNS]->(a)
RETURN a,b LIMIT 100;

// 3) Rent extraction chain
MATCH (t:Person)-[:LEASES]->(u:Property)<-[:OWNS]-(o:LLC)-[:MANAGES]->(m:LLC)
RETURN t,u,o,m LIMIT 100;

// 4) Fallback for datasets using REL.type
MATCH (a)-[r:REL]->(b)
WHERE toLower(r.type) IN ['registered_agent','owns','manages','leases']
RETURN r.type AS type, a,b LIMIT 100;
"""
        fq_path = os.path.join(pack_dir, "fraud_queries.cypher")
        open(fq_path, "w", encoding="utf-8").write(fraud_queries.strip())

        readme = f"""
Neo4j Schema-Aware Import Pack for run {rid}

Files:
- nodes.csv, edges.csv — copy into Neo4j `import` directory
- import.cypher — per-label/node and per-type/edge import
- fraud_queries.cypher — useful graph analytics shortcuts

Run in Neo4j Browser:
  :use neo4j
  :auto USING PERIODIC COMMIT 500
  :source import.cypher
  :source fraud_queries.cypher   // optional analytics
"""
        readme_path = os.path.join(pack_dir, "README_SCHEMA_NEO4J.txt")
        open(readme_path, "w", encoding="utf-8").write(readme.strip())

        # Copy CSVs into pack
        n_copy = os.path.join(pack_dir, "nodes.csv")
        e_copy = os.path.join(pack_dir, "edges.csv")
        shutil.copyfile(nodes_csv, n_copy)
        shutil.copyfile(edges_csv, e_copy)

        # Zip
        zip_path = os.path.join(run_dir, f"neo4j_schema_pack_{ts}.zip")
        with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as z:
            for p in [n_copy, e_copy, cypher_path, fq_path, readme_path]:
                z.write(p, arcname=os.path.basename(p))

        return {
            "run_id": rid,
            "pack_dir": pack_dir,
            "zip_path": zip_path,
            "node_id_col": node_id_col,
            "node_label_col": node_label_col,
            "edge_src_col": edge_src_col,
            "edge_dst_col": edge_dst_col,
            "edge_type_col": edge_type_col,
            "labels_detected": label_values[:20],
            "rel_types_detected": rel_values[:20]
        }
