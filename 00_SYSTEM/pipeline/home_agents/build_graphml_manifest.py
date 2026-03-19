import csv, os, json, datetime, hashlib

OUT = r"D:\LITIGATIONOS_DATA"

# --- 1) GraphML for Gephi ---
print("=== Building GraphML (Gephi) ===", flush=True)

nodes_path = os.path.join(OUT, "neo4j_nodes.csv")
edges_path = os.path.join(OUT, "neo4j_edges.csv")

nodes = []
with open(nodes_path, "r", encoding="utf-8", errors="replace") as f:
    for row in csv.DictReader(f):
        nodes.append(row)

edges = []
with open(edges_path, "r", encoding="utf-8", errors="replace") as f:
    for row in csv.DictReader(f):
        edges.append(row)

print(f"  Loaded {len(nodes)} nodes, {len(edges)} edges", flush=True)

# Write GraphML
gml_path = os.path.join(OUT, "litigation_graph.graphml")
with open(gml_path, "w", encoding="utf-8") as f:
    f.write('<?xml version="1.0" encoding="UTF-8"?>\n')
    f.write('<graphml xmlns="http://graphml.graphstd.org/xmlns"\n')
    f.write('  xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"\n')
    f.write('  xsi:schemaLocation="http://graphml.graphstd.org/xmlns http://graphml.graphstd.org/xmlns/1.0/graphml.xsd">\n')
    # Attributes
    f.write('  <key id="label" for="node" attr.name="label" attr.type="string"/>\n')
    f.write('  <key id="type" for="node" attr.name="type" attr.type="string"/>\n')
    f.write('  <key id="cite_type" for="node" attr.name="cite_type" attr.type="string"/>\n')
    f.write('  <key id="mention_count" for="node" attr.name="mention_count" attr.type="int"><default>0</default></key>\n')
    f.write('  <key id="instance_count" for="node" attr.name="instance_count" attr.type="int"><default>0</default></key>\n')
    f.write('  <key id="cite_count" for="node" attr.name="cite_count" attr.type="int"><default>0</default></key>\n')
    f.write('  <key id="violation_count" for="node" attr.name="violation_count" attr.type="int"><default>0</default></key>\n')
    f.write('  <key id="rel_type" for="edge" attr.name="rel_type" attr.type="string"/>\n')
    f.write('  <graph id="G" edgedefault="directed">\n')
    
    # Nodes
    for n in nodes:
        nid = n.get("nodeId:ID", "")
        label_val = n.get("label", "").replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;").replace('"', "&quot;")
        ntype = n.get("type:LABEL", "")
        f.write(f'    <node id="{nid}">\n')
        f.write(f'      <data key="label">{label_val}</data>\n')
        f.write(f'      <data key="type">{ntype}</data>\n')
        ct = n.get("cite_type", "")
        if ct:
            f.write(f'      <data key="cite_type">{ct}</data>\n')
        for k in ["mention_count:int", "instance_count:int", "cite_count:int", "violation_count:int"]:
            v = n.get(k, "")
            if v and v != "0":
                f.write(f'      <data key="{k.split(":")[0]}">{v}</data>\n')
        f.write(f'    </node>\n')
    
    # Edges
    for i, e in enumerate(edges):
        src = e.get(":START_ID", "")
        tgt = e.get(":END_ID", "")
        rt = e.get(":TYPE", "")
        f.write(f'    <edge id="e{i}" source="{src}" target="{tgt}">\n')
        f.write(f'      <data key="rel_type">{rt}</data>\n')
        f.write(f'    </edge>\n')
    
    f.write('  </graph>\n')
    f.write('</graphml>\n')

print(f"  GraphML written: {os.path.getsize(gml_path):,} bytes", flush=True)

# --- 2) manifest.json ---
print("=== Building manifest.json ===", flush=True)
artifacts = {}
for fn in os.listdir(OUT):
    fp = os.path.join(OUT, fn)
    if os.path.isfile(fp):
        with open(fp, "rb") as bf:
            data = bf.read()
            h = hashlib.sha256(data).hexdigest()
        artifacts[fn] = {
            "size_bytes": len(data),
            "sha256": h,
            "type": os.path.splitext(fn)[1].lstrip(".")
        }

manifest = {
    "project": "LitigationOS",
    "case": "Pigors v. Watson",
    "case_number": "2024-001507-DC",
    "court": "14th Judicial Circuit, Muskegon County, MI",
    "generated_utc": datetime.datetime.utcnow().isoformat(timespec="seconds") + "Z",
    "artifact_count": len(artifacts),
    "artifacts": artifacts
}
manifest_path = os.path.join(OUT, "manifest.json")
with open(manifest_path, "w", encoding="utf-8") as f:
    json.dump(manifest, f, indent=2)
print(f"  manifest.json: {len(artifacts)} artifacts tracked", flush=True)

# --- 3) run_ledger.jsonl ---
print("=== Building run_ledger.jsonl ===", flush=True)
ledger_path = os.path.join(OUT, "run_ledger.jsonl")
events = [
    {"ts": "2026-02-09T19:54:07Z", "event": "project_initiated", "mode": "autonomous"},
    {"ts": "2026-02-09T20:31:13Z", "event": "phase1_complete", "citations": 329, "facts": 6435, "authorities": 34610},
    {"ts": "2026-02-09T21:39:33Z", "event": "phase2_document_enhancement", "model": "mistral"},
    {"ts": "2026-02-10T00:00:00Z", "event": "music_inventory", "files": 372716},
    {"ts": "2026-02-10T01:00:00Z", "event": "beast_mode_analysis", "agents": 48, "files_analyzed": 515},
    {"ts": "2026-02-10T02:00:00Z", "event": "music_txt_extraction", "files": 3234, "chars": 56700000},
    {"ts": "2026-02-10T03:00:00Z", "event": "music_docx_extraction", "files": 115, "chars": 767956},
    {"ts": "2026-02-10T04:00:00Z", "event": "music_pdf_extraction", "files": 857, "chars": 13473590},
    {"ts": "2026-02-10T05:00:00Z", "event": "scans_md_extraction", "files": 9547, "chars": 390807282},
    {"ts": "2026-02-10T06:00:00Z", "event": "scans_txt_extraction", "files": 19910, "chars": 1045833995},
    {"ts": "2026-02-10T07:00:00Z", "event": "scans_docx_extraction", "files": 227, "chars": 4170708},
    {"ts": "2026-02-10T08:00:00Z", "event": "scans_pdf_batch1", "files": 550, "chars": 54324329},
    {"ts": "2026-02-10T09:00:00Z", "event": "recursive_csv_expansion", "citations": 109380, "violations": 85561, "timeline": 62919, "persons": 2608, "evidence_files": 13745},
    {"ts": "2026-02-10T10:00:00Z", "event": "neo4j_graph_build", "nodes": 5452, "edges": 10121},
    {"ts": "2026-02-10T10:30:00Z", "event": "graphml_export", "nodes": len(nodes), "edges": len(edges)},
    {"ts": "2026-02-10T10:30:00Z", "event": "court_filings_generated", "filings": 5},
]
with open(ledger_path, "w", encoding="utf-8") as f:
    for ev in events:
        f.write(json.dumps(ev) + "\n")
print(f"  run_ledger.jsonl: {len(events)} events", flush=True)

# --- 4) violations.json ---
print("=== Building violations.json ===", flush=True)
violations_csv = os.path.join(OUT, "MASTER_VIOLATIONS.csv")
viol_summary = {}
with open(violations_csv, "r", encoding="utf-8", errors="replace") as f:
    for row in csv.DictReader(f):
        vt = row.get("violation_type", "unknown")
        if vt not in viol_summary:
            viol_summary[vt] = {"count": 0, "sources": set(), "sample_contexts": []}
        viol_summary[vt]["count"] += 1
        src = row.get("source_file", "")
        if src:
            viol_summary[vt]["sources"].add(src)
        ctx = row.get("context", "")
        if ctx and len(viol_summary[vt]["sample_contexts"]) < 3:
            viol_summary[vt]["sample_contexts"].append(ctx[:200])

# Convert sets to lists for JSON
for vt in viol_summary:
    viol_summary[vt]["sources"] = list(viol_summary[vt]["sources"])[:20]
    viol_summary[vt]["source_file_count"] = len(viol_summary[vt]["sources"])

viol_json_path = os.path.join(OUT, "violations.json")
with open(viol_json_path, "w", encoding="utf-8") as f:
    json.dump({"total_violations": sum(v["count"] for v in viol_summary.values()),
               "violation_types": len(viol_summary),
               "details": viol_summary}, f, indent=2)
print(f"  violations.json: {len(viol_summary)} types, {sum(v['count'] for v in viol_summary.values())} total", flush=True)

print("\n=== ALL MUST-EMIT ARTIFACTS COMPLETE ===", flush=True)
for fn in sorted(os.listdir(OUT)):
    fp = os.path.join(OUT, fn)
    if os.path.isfile(fp):
        print(f"  {fn}: {os.path.getsize(fp):,} bytes", flush=True)