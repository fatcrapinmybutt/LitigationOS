import csv, os, hashlib, json, re
from collections import Counter, defaultdict

OUT = r"D:\LITIGATIONOS_DATA"

# --- 1) Build Neo4j node/edge CSVs from MASTER_CITATIONS.csv ---
print("=== Building Neo4j Import CSVs ===", flush=True)

citations_path = os.path.join(OUT, "MASTER_CITATIONS.csv")
violations_path = os.path.join(OUT, "MASTER_VIOLATIONS.csv")
persons_path = os.path.join(OUT, "MASTER_PERSONS.csv")
timeline_path = os.path.join(OUT, "MASTER_TIMELINE.csv")
evidence_path = os.path.join(OUT, "MASTER_EVIDENCE_INDEX.csv")

# Node types: Authority, Evidence, Person, Event, Violation
# Edge types: CITES, VIOLATES, MENTIONS, OCCURS_IN

def sha_id(s):
    return hashlib.sha1(s.encode()).hexdigest()[:12]

nodes = {}  # id -> {id, label, type, properties...}
edges = []  # {start, end, type, properties...}

# -- Authority nodes from citations --
print("  Parsing citations...", flush=True)
cite_count = 0
with open(citations_path, "r", encoding="utf-8", errors="replace") as f:
    reader = csv.DictReader(f)
    for row in reader:
        cite = row.get("citation","").strip()
        ctype = row.get("cite_type","").strip()
        src = row.get("source_file","").strip()
        if not cite:
            continue
        
        # Authority node
        aid = sha_id(f"AUTH:{cite}")
        if aid not in nodes:
            nodes[aid] = {"id": aid, "label": cite, "type": "Authority", "cite_type": ctype, "mention_count": 0}
        nodes[aid]["mention_count"] += 1
        
        # Evidence node
        if src:
            eid = sha_id(f"EVID:{src}")
            if eid not in nodes:
                nodes[eid] = {"id": eid, "label": os.path.basename(src), "type": "Evidence", "path": src, "cite_count": 0, "violation_count": 0}
            nodes[eid]["cite_count"] += 1
            
            edges.append({"start": eid, "end": aid, "type": "CITES", "line": row.get("line_number","")})
        cite_count += 1
        if cite_count % 20000 == 0:
            print(f"    {cite_count} citations processed...", flush=True)

print(f"  Citations done: {cite_count} rows -> {len([n for n in nodes.values() if n['type']=='Authority'])} authority nodes", flush=True)

# -- Violation nodes --
print("  Parsing violations...", flush=True)
viol_count = 0
with open(violations_path, "r", encoding="utf-8", errors="replace") as f:
    reader = csv.DictReader(f)
    for row in reader:
        vtype = row.get("violation_type","").strip()
        src = row.get("source_file","").strip()
        if not vtype:
            continue
        
        vid = sha_id(f"VIOL:{vtype}")
        if vid not in nodes:
            nodes[vid] = {"id": vid, "label": vtype.replace("_"," ").title(), "type": "Violation", "violation_type": vtype, "instance_count": 0}
        nodes[vid]["instance_count"] += 1
        
        if src:
            eid = sha_id(f"EVID:{src}")
            if eid not in nodes:
                nodes[eid] = {"id": eid, "label": os.path.basename(src), "type": "Evidence", "path": src, "cite_count": 0, "violation_count": 0}
            nodes[eid]["violation_count"] += 1
            edges.append({"start": eid, "end": vid, "type": "DOCUMENTS"})
        viol_count += 1
        if viol_count % 20000 == 0:
            print(f"    {viol_count} violations processed...", flush=True)

print(f"  Violations done: {viol_count} rows -> {len([n for n in nodes.values() if n['type']=='Violation'])} violation type nodes", flush=True)

# -- Person nodes --
print("  Parsing persons...", flush=True)
person_count = 0
with open(persons_path, "r", encoding="utf-8", errors="replace") as f:
    reader = csv.DictReader(f)
    for row in reader:
        person = row.get("person","").strip()
        src = row.get("source_file","").strip()
        if not person:
            continue
        
        pid = sha_id(f"PERS:{person}")
        if pid not in nodes:
            nodes[pid] = {"id": pid, "label": person, "type": "Person", "mention_count": 0}
        nodes[pid]["mention_count"] += 1
        
        if src:
            eid = sha_id(f"EVID:{src}")
            if eid in nodes:
                edges.append({"start": eid, "end": pid, "type": "MENTIONS"})
        person_count += 1

print(f"  Persons done: {person_count} rows -> {len([n for n in nodes.values() if n['type']=='Person'])} person nodes", flush=True)

# -- Timeline event nodes (sample top 1000 by uniqueness) --
print("  Parsing timeline events...", flush=True)
event_dates = Counter()
event_count = 0
with open(timeline_path, "r", encoding="utf-8", errors="replace") as f:
    reader = csv.DictReader(f)
    for row in reader:
        date = row.get("date","").strip()
        src = row.get("source_file","").strip()
        if not date:
            continue
        event_dates[date] += 1
        event_count += 1

# Create event nodes for each unique date
for date, count in event_dates.items():
    evid = sha_id(f"EVENT:{date}")
    if evid not in nodes:
        nodes[evid] = {"id": evid, "label": date, "type": "Event", "date": date, "occurrence_count": count}

print(f"  Timeline done: {event_count} rows -> {len(event_dates)} unique date nodes", flush=True)

# --- Write Neo4j import CSVs ---
print("  Writing neo4j_nodes.csv...", flush=True)
node_path = os.path.join(OUT, "neo4j_nodes.csv")
with open(node_path, "w", encoding="utf-8", newline="") as f:
    w = csv.writer(f)
    w.writerow(["nodeId:ID", "label", "type:LABEL", "cite_type", "mention_count:int", "instance_count:int", "cite_count:int", "violation_count:int", "path", "date"])
    for n in nodes.values():
        w.writerow([
            n["id"], n["label"], n["type"],
            n.get("cite_type",""), n.get("mention_count",""), n.get("instance_count",""),
            n.get("cite_count",""), n.get("violation_count",""), n.get("path",""), n.get("date","")
        ])

print(f"  neo4j_nodes.csv: {len(nodes)} nodes", flush=True)

print("  Writing neo4j_edges.csv...", flush=True)
# Dedupe edges by (start, end, type) - keep first
seen_edges = set()
deduped = []
for e in edges:
    key = (e["start"], e["end"], e["type"])
    if key not in seen_edges:
        seen_edges.add(key)
        deduped.append(e)

edge_path = os.path.join(OUT, "neo4j_edges.csv")
with open(edge_path, "w", encoding="utf-8", newline="") as f:
    w = csv.writer(f)
    w.writerow([":START_ID", ":END_ID", ":TYPE", "line"])
    for e in deduped:
        w.writerow([e["start"], e["end"], e["type"], e.get("line","")])

print(f"  neo4j_edges.csv: {len(deduped)} edges (deduped from {len(edges)})", flush=True)

# --- 2) Neo4j Constraints Cypher ---
print("  Writing neo4j_constraints.cypher...", flush=True)
cypher = """// LitigationOS Neo4j Constraints & Indexes
// Generated from MASTER CSVs

// Uniqueness constraints
CREATE CONSTRAINT authority_id IF NOT EXISTS FOR (a:Authority) REQUIRE a.nodeId IS UNIQUE;
CREATE CONSTRAINT evidence_id IF NOT EXISTS FOR (e:Evidence) REQUIRE e.nodeId IS UNIQUE;
CREATE CONSTRAINT person_id IF NOT EXISTS FOR (p:Person) REQUIRE p.nodeId IS UNIQUE;
CREATE CONSTRAINT violation_id IF NOT EXISTS FOR (v:Violation) REQUIRE v.nodeId IS UNIQUE;
CREATE CONSTRAINT event_id IF NOT EXISTS FOR (ev:Event) REQUIRE ev.nodeId IS UNIQUE;

// Indexes for fast lookup
CREATE INDEX authority_label IF NOT EXISTS FOR (a:Authority) ON (a.label);
CREATE INDEX authority_cite_type IF NOT EXISTS FOR (a:Authority) ON (a.cite_type);
CREATE INDEX evidence_path IF NOT EXISTS FOR (e:Evidence) ON (e.path);
CREATE INDEX person_label IF NOT EXISTS FOR (p:Person) ON (p.label);
CREATE INDEX violation_type IF NOT EXISTS FOR (v:Violation) ON (v.violation_type);
CREATE INDEX event_date IF NOT EXISTS FOR (ev:Event) ON (ev.date);

// Full-text search indexes
CREATE FULLTEXT INDEX authority_search IF NOT EXISTS FOR (a:Authority) ON EACH [a.label];
CREATE FULLTEXT INDEX person_search IF NOT EXISTS FOR (p:Person) ON EACH [p.label];

// Import commands (run after loading CSVs into Neo4j import directory):
// LOAD CSV WITH HEADERS FROM 'file:///neo4j_nodes.csv' AS row
// WITH row WHERE row.`type:LABEL` = 'Authority'
// CREATE (a:Authority {nodeId: row.`nodeId:ID`, label: row.label, cite_type: row.cite_type, mention_count: toInteger(row.`mention_count:int`)});
//
// LOAD CSV WITH HEADERS FROM 'file:///neo4j_nodes.csv' AS row
// WITH row WHERE row.`type:LABEL` = 'Evidence'
// CREATE (e:Evidence {nodeId: row.`nodeId:ID`, label: row.label, path: row.path, cite_count: toInteger(row.`cite_count:int`), violation_count: toInteger(row.`violation_count:int`)});
//
// LOAD CSV WITH HEADERS FROM 'file:///neo4j_nodes.csv' AS row
// WITH row WHERE row.`type:LABEL` = 'Person'
// CREATE (p:Person {nodeId: row.`nodeId:ID`, label: row.label, mention_count: toInteger(row.`mention_count:int`)});
//
// LOAD CSV WITH HEADERS FROM 'file:///neo4j_nodes.csv' AS row
// WITH row WHERE row.`type:LABEL` = 'Violation'
// CREATE (v:Violation {nodeId: row.`nodeId:ID`, label: row.label, violation_type: row.violation_type, instance_count: toInteger(row.`instance_count:int`)});
//
// LOAD CSV WITH HEADERS FROM 'file:///neo4j_nodes.csv' AS row
// WITH row WHERE row.`type:LABEL` = 'Event'
// CREATE (ev:Event {nodeId: row.`nodeId:ID`, label: row.label, date: row.date, occurrence_count: toInteger(coalesce(row.`mention_count:int`, '0'))});
//
// LOAD CSV WITH HEADERS FROM 'file:///neo4j_edges.csv' AS row
// MATCH (s {nodeId: row.`:START_ID`}), (t {nodeId: row.`:END_ID`})
// CALL apoc.create.relationship(s, row.`:TYPE`, {line: row.line}, t) YIELD rel RETURN count(rel);
"""
with open(os.path.join(OUT, "neo4j_constraints.cypher"), "w", encoding="utf-8") as f:
    f.write(cypher)

# --- 3) Bloom Perspective JSON ---
print("  Writing bloom_perspective.json...", flush=True)
bloom = {
    "name": "LitigationOS - Pigors v Watson",
    "version": "2.0",
    "categories": [
        {"name": "Authority", "color": "#2196F3", "icon": "gavel", "caption": "{label}", "size": "mention_count"},
        {"name": "Evidence", "color": "#4CAF50", "icon": "file", "caption": "{label}", "size": "cite_count"},
        {"name": "Person", "color": "#FF9800", "icon": "person", "caption": "{label}", "size": "mention_count"},
        {"name": "Violation", "color": "#F44336", "icon": "warning", "caption": "{label}", "size": "instance_count"},
        {"name": "Event", "color": "#9C27B0", "icon": "calendar", "caption": "{label}", "size": "occurrence_count"}
    ],
    "relationships": [
        {"type": "CITES", "color": "#1565C0", "caption": "cites"},
        {"type": "DOCUMENTS", "color": "#C62828", "caption": "documents"},
        {"type": "MENTIONS", "color": "#E65100", "caption": "mentions"}
    ],
    "search_phrases": [
        {"name": "Find authority", "query": "MATCH (a:Authority) WHERE a.label CONTAINS $term RETURN a LIMIT 25"},
        {"name": "Evidence citing authority", "query": "MATCH (e:Evidence)-[:CITES]->(a:Authority) WHERE a.label CONTAINS $term RETURN e, a LIMIT 50"},
        {"name": "Violations in file", "query": "MATCH (e:Evidence)-[:DOCUMENTS]->(v:Violation) WHERE e.label CONTAINS $term RETURN e, v LIMIT 50"},
        {"name": "Person network", "query": "MATCH (e:Evidence)-[:MENTIONS]->(p:Person) WHERE p.label CONTAINS $term RETURN e, p LIMIT 50"},
        {"name": "All contempt violations", "query": "MATCH (e:Evidence)-[:DOCUMENTS]->(v:Violation {violation_type: 'contempt'}) RETURN e, v LIMIT 100"},
        {"name": "Due process violations", "query": "MATCH (e:Evidence)-[:DOCUMENTS]->(v:Violation {violation_type: 'due_process'}) RETURN e, v LIMIT 100"}
    ],
    "stats": {
        "total_nodes": len(nodes),
        "total_edges": len(deduped),
        "authority_nodes": len([n for n in nodes.values() if n["type"] == "Authority"]),
        "evidence_nodes": len([n for n in nodes.values() if n["type"] == "Evidence"]),
        "person_nodes": len([n for n in nodes.values() if n["type"] == "Person"]),
        "violation_nodes": len([n for n in nodes.values() if n["type"] == "Violation"]),
        "event_nodes": len([n for n in nodes.values() if n["type"] == "Event"])
    }
}
with open(os.path.join(OUT, "bloom_perspective.json"), "w", encoding="utf-8") as f:
    json.dump(bloom, f, indent=2)

# --- 4) Graph Contract YAML ---
print("  Writing graph_contract.yml...", flush=True)
contract = f"""# LitigationOS Graph Contract
# Case: Pigors v. Watson | 14th Judicial Circuit, Muskegon County, MI
# Generated from recursive CSV extraction

schema:
  version: "2.0"
  case_id: "2024-001507-DC"

node_types:
  Authority:
    id_prefix: "AUTH:"
    properties: [label, cite_type, mention_count]
    count: {len([n for n in nodes.values() if n['type']=='Authority'])}
  Evidence:
    id_prefix: "EVID:"
    properties: [label, path, cite_count, violation_count]
    count: {len([n for n in nodes.values() if n['type']=='Evidence'])}
  Person:
    id_prefix: "PERS:"
    properties: [label, mention_count]
    count: {len([n for n in nodes.values() if n['type']=='Person'])}
  Violation:
    id_prefix: "VIOL:"
    properties: [label, violation_type, instance_count]
    count: {len([n for n in nodes.values() if n['type']=='Violation'])}
  Event:
    id_prefix: "EVENT:"
    properties: [label, date, occurrence_count]
    count: {len([n for n in nodes.values() if n['type']=='Event'])}

edge_types:
  CITES:
    from: Evidence
    to: Authority
    properties: [line]
  DOCUMENTS:
    from: Evidence
    to: Violation
    properties: []
  MENTIONS:
    from: Evidence
    to: Person
    properties: []

totals:
  nodes: {len(nodes)}
  edges: {len(deduped)}
  source_files_analyzed: {len([n for n in nodes.values() if n['type']=='Evidence'])}
  
data_sources:
  - MASTER_CITATIONS.csv
  - MASTER_VIOLATIONS.csv
  - MASTER_PERSONS.csv
  - MASTER_TIMELINE.csv
  - MASTER_EVIDENCE_INDEX.csv
"""
with open(os.path.join(OUT, "graph_contract.yml"), "w", encoding="utf-8") as f:
    f.write(contract)

# --- 5) Summary stats ---
type_counts = Counter(n["type"] for n in nodes.values())
edge_type_counts = Counter(e["type"] for e in deduped)

print("\n=== NEO4J GRAPH BUILD COMPLETE ===", flush=True)
print(f"Total nodes: {len(nodes)}", flush=True)
for t, c in sorted(type_counts.items()):
    print(f"  {t}: {c}", flush=True)
print(f"Total edges: {len(deduped)}", flush=True)
for t, c in sorted(edge_type_counts.items()):
    print(f"  {t}: {c}", flush=True)
print(f"\nArtifacts written to {OUT}:", flush=True)
for fn in ["neo4j_nodes.csv", "neo4j_edges.csv", "neo4j_constraints.cypher", "bloom_perspective.json", "graph_contract.yml"]:
    p = os.path.join(OUT, fn)
    print(f"  {fn}: {os.path.getsize(p):,} bytes", flush=True)
print("DONE", flush=True)