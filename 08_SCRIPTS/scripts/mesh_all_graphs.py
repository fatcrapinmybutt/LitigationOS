#!/usr/bin/env python3
"""
Mesh all graph packs into a single cohesive G4 litigation brain.

Usage:
  1) Put this script in a folder with these zip files (adjust names if needed):
       - NODES.zip                     (optional)
       - unified_nodes(1).zip          (MasterGraph pack)
       - subgraph_CANON.zip            (Authority CANON/MCR/MCL pack)
       - litigato os build.zip         (new large pack)
       - GRAPHS.zip                    (new large pack)
  2) Run:
       python3 mesh_all_graphs.py
  3) Result:
       ./build/combined/
         - G4_nodes_final.json
         - G4_edges_final.json
         - G4_nodes_final.csv
         - G4_edges_final.csv
         - G4_combined_import.cypher
         - G4_Combined_Wheel.html
         - README_G4_final.txt
       and:
         ./G4_Litigation_Brain_Pack_FINAL.zip
"""

import os
import zipfile
import json
import csv
import math
import itertools
import re
from collections import defaultdict
from datetime import datetime

# === CONFIG ===

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
BUILD_DIR = os.path.join(BASE_DIR, "build")
COMBINED_DIR = os.path.join(BUILD_DIR, "combined")

# List all zip sources you want merged.
# Adjust names if your local files differ.
ZIP_SOURCES = [
    "NODES.zip",                # optional, if you still use it
    "unified_nodes(1).zip",     # contains MasterGraph.json etc.
    "subgraph_CANON.zip",       # CANON/MCR/MCL subgraphs
    "litigato os build.zip",    # new large pack
    "GRAPHS.zip",               # new large pack
]

# Per-file caps to avoid blowing memory if something is massive.
MAX_JSON_GRAPH_NODES_PER_FILE = 200_000
MAX_JSON_GRAPH_EDGES_PER_FILE = 300_000
MAX_JSON_LIST_OBJS_PER_FILE   = 200_000
MAX_CSV_NODES_PER_FILE        = 200_000
MAX_CSV_EDGES_PER_FILE        = 300_000

# Citation regex for legal authority wiring
CITATION_PATTERNS = [
    (re.compile(r'\bMCR\s*\d+\.\d+\w*\b', re.I), 'MCR'),
    (re.compile(r'\bMCL\s*\d+\.\d+\w*\b', re.I), 'MCL'),
    (re.compile(r'\bMRE\s*\d+\.\d+\w*\b', re.I), 'MRE'),
]

# === HELPERS ===

def ensure_dir(path: str) -> None:
    os.makedirs(path, exist_ok=True)

def extract_zips():
    ensure_dir(BUILD_DIR)
    extracted_roots = []
    for name in ZIP_SOURCES:
        zip_path = os.path.join(BASE_DIR, name)
        if not os.path.exists(zip_path):
            print(f"[ZIP] {name} not found, skipping.")
            continue
        target = os.path.join(BUILD_DIR, os.path.splitext(os.path.basename(name))[0])
        ensure_dir(target)
        print(f"[ZIP] Extracting {name} -> {target}")
        with zipfile.ZipFile(zip_path, "r") as z:
            z.extractall(target)
        extracted_roots.append(target)
    return extracted_roots

def extract_text_fields(obj):
    out = []
    if isinstance(obj, dict):
        for v in obj.values():
            if isinstance(v, str):
                out.append(v)
            elif isinstance(v, (dict, list)):
                out.extend(extract_text_fields(v))
    elif isinstance(obj, list):
        for v in obj:
            out.extend(extract_text_fields(v))
    return out

def extract_citations(obj):
    texts = extract_text_fields(obj)
    hits = []
    for t in texts:
        for rx, kind in CITATION_PATTERNS:
            for m in rx.finditer(t):
                hits.append((kind, m.group().strip()))
    out = []
    seen = set()
    for kind, cit in hits:
        key = (kind, cit.upper())
        if key in seen:
            continue
        seen.add(key)
        out.append((kind, cit))
    return out

def norm_id(x):
    if isinstance(x, (int, float)):
        if isinstance(x, bool):
            return str(x)
        # integer-like floats
        as_f = float(x)
        if as_f.is_integer():
            return str(int(as_f))
        return str(x)
    return str(x)

def add_node(nodes, nid, label=None, ntype=None, **extra):
    nid = norm_id(nid)
    n = nodes.get(nid)
    if not n:
        n = {"id": nid}
        nodes[nid] = n
    if label and not n.get("label"):
        n["label"] = str(label)
    if ntype and not n.get("type"):
        n["type"] = str(ntype)
    for k, v in extra.items():
        if v is None:
            continue
        if k == "tags":
            existing = set(n.get("tags") or [])
            if isinstance(v, str):
                new = {v}
            elif isinstance(v, (list, tuple, set)):
                new = {str(x) for x in v}
            else:
                new = {str(v)}
            n["tags"] = sorted(existing | new)
        elif k == "sources":
            existing = set(n.get("sources") or [])
            if isinstance(v, str):
                new = {v}
            elif isinstance(v, (list, tuple, set)):
                new = {str(x) for x in v}
            else:
                new = {str(v)}
            n["sources"] = sorted(existing | new)
        else:
            if k not in n:
                n[k] = v
    return n

def add_edge(edges, edges_set, source, target, etype="rel", weight=1.0, **extra):
    s = norm_id(source)
    t = norm_id(target)
    et = etype or "rel"
    key = (s, t, et)
    if key in edges_set:
        return
    edges_set.add(key)
    e = {
        "source": s,
        "target": t,
        "type": et,
    }
    if weight is not None:
        try:
            e["weight"] = float(weight)
        except Exception:
            e["weight"] = 1.0
    else:
        e["weight"] = 1.0
    for k, v in extra.items():
        if v is not None:
            e[k] = v
    edges.append(e)

# === INGESTION ===

def handle_json(path, nodes, edges, edges_set, universe, source_tag):
    base = os.path.splitext(os.path.basename(path))[0].replace(" ", "_")
    try:
        with open(path, "r", encoding="utf-8", errors="ignore") as f:
            data = json.load(f)
    except Exception as e:
        print(f"[JSON] Error parsing {path}: {e}")
        return

    def upsert_from_obj(obj, default_label=None):
        nid = obj.get("id") or obj.get("key") or obj.get("name") or default_label
        if not nid:
            return
        label = obj.get("label") or obj.get("name") or default_label or nid
        ntype = obj.get("type") or obj.get("kind") or obj.get("category")
        case = obj.get("case") or obj.get("meek") or obj.get("universe")
        tags = []
        for k in ("tags", "tag", "category", "kind", "type"):
            v = obj.get(k)
            if isinstance(v, str):
                tags.extend([x.strip() for x in v.split("|") if x.strip()])
            elif isinstance(v, (list, tuple)):
                tags.extend([str(x) for x in v])
        node = add_node(
            nodes,
            nid,
            label=label,
            ntype=ntype,
            case=case,
            universe=universe,
            tags=tags or [base],
            sources=[source_tag],
        )
        # authority citations
        for kind, cit in extract_citations(obj):
            aid = f"{kind}:{cit}"
            add_node(
                nodes,
                aid,
                label=cit,
                ntype="authority",
                universe="Authority",
                tags=[kind],
                sources=[source_tag],
            )
            add_edge(edges, edges_set, nid, aid, etype="cites", file=base, universe=universe)
        return node

    # Graph-like: { nodes: [...], edges/links: [...] }
    if isinstance(data, dict) and ("nodes" in data and ("edges" in data or "links" in data)):
        nodes_arr = data.get("nodes", [])
        edges_arr = data.get("edges") or data.get("links") or []
        for i, nd in enumerate(nodes_arr):
            if i >= MAX_JSON_GRAPH_NODES_PER_FILE:
                break
            if isinstance(nd, dict):
                upsert_from_obj(nd)
        for i, ed in enumerate(edges_arr):
            if i >= MAX_JSON_GRAPH_EDGES_PER_FILE:
                break
            if not isinstance(ed, dict):
                continue
            s = ed.get("source") or ed.get("from") or ed.get("src")
            t = ed.get("target") or ed.get("to") or ed.get("dst")
            if not s or not t:
                continue
            etype = ed.get("type") or ed.get("relationship") or ed.get("rel") or "rel"
            w = ed.get("weight") or 1.0
            add_edge(
                edges,
                edges_set,
                s,
                t,
                etype=etype,
                weight=w,
                universe=universe,
                file=base,
                source=source_tag,
            )
        return

    # List of objects
    if isinstance(data, list):
        for i, obj in enumerate(data):
            if i >= MAX_JSON_LIST_OBJS_PER_FILE:
                break
            if isinstance(obj, dict):
                upsert_from_obj(obj, default_label=f"{base}_{i}")
        return

    # Fallback: scalar JSON -> note node
    add_node(
        nodes,
        base,
        label=base,
        ntype="artifact",
        universe=universe,
        tags=[base],
        sources=[source_tag],
    )

def handle_csv(path, nodes, edges, edges_set, universe, source_tag):
    base = os.path.splitext(os.path.basename(path))[0].replace(" ", "_")
    try:
        with open(path, newline="", encoding="utf-8", errors="ignore") as f:
            reader = csv.DictReader(f)
            headers = [h.lower() for h in (reader.fieldnames or [])]
            is_edge = any(h in headers for h in ("source", "target", "from", "to", "src", "dst"))
            if is_edge:
                for i, row in enumerate(reader):
                    if i >= MAX_CSV_EDGES_PER_FILE:
                        break
                    row_l = {k.lower(): v for k, v in row.items()}
                    s = row_l.get("source") or row_l.get("from") or row_l.get("src")
                    t = row_l.get("target") or row_l.get("to") or row_l.get("dst")
                    if not s or not t:
                        continue
                    etype = row_l.get("type") or row_l.get("relationship") or row_l.get("rel") or "rel"
                    w = row_l.get("weight") or 1.0
                    add_edge(
                        edges,
                        edges_set,
                        s,
                        t,
                        etype=etype,
                        weight=w,
                        universe=universe,
                        file=base,
                        source=source_tag,
                    )
                return
            # Node-style CSV
            for i, row in enumerate(reader):
                if i >= MAX_CSV_NODES_PER_FILE:
                    break
                nid = row.get("id") or row.get("ID") or row.get("Id") or f"{base}_{i}"
                label = row.get("label") or row.get("name") or nid
                ntype = row.get("type") or row.get("kind") or None
                case = row.get("case") or row.get("meek") or row.get("universe")
                tags = []
                for k in ("tags", "tag", "category", "kind", "type"):
                    v = row.get(k)
                    if v:
                        tags.extend([x.strip() for x in str(v).split("|") if x.strip()])
                add_node(
                    nodes,
                    nid,
                    label=label,
                    ntype=ntype,
                    case=case,
                    universe=universe,
                    tags=tags or [base],
                    sources=[source_tag],
                )
    except Exception as e:
        print(f"[CSV] Error reading {path}: {e}")

def handle_txt(path, nodes, edges, edges_set, universe, source_tag):
    base = os.path.splitext(os.path.basename(path))[0].replace(" ", "_")
    try:
        with open(path, "r", encoding="utf-8", errors="ignore") as f:
            text = f.read(50_000)
    except Exception:
        text = ""
    nid = base
    add_node(
        nodes,
        nid,
        label=base,
        ntype="note",
        universe=universe,
        tags=[base, "txt"],
        sources=[source_tag],
    )
    for kind, cit in extract_citations({"text": text}):
        aid = f"{kind}:{cit}"
        add_node(
            nodes,
            aid,
            label=cit,
            ntype="authority",
            universe="Authority",
            tags=[kind],
            sources=[source_tag],
        )
        add_edge(edges, edges_set, nid, aid, etype="cites", universe=universe, file=base)

def ingest_all(extracted_roots):
    nodes = {}
    edges = []
    edges_set = set()

    for root in extracted_roots:
        source_tag = os.path.basename(root)
        for dirpath, _, filenames in os.walk(root):
            rel = os.path.relpath(dirpath, root)
            universe = "Root" if rel == "." else os.path.basename(dirpath)
            for fn in filenames:
                full = os.path.join(dirpath, fn)
                lower = fn.lower()
                try:
                    if lower.endswith(".json"):
                        handle_json(full, nodes, edges, edges_set, universe, source_tag)
                    elif lower.endswith(".csv"):
                        handle_csv(full, nodes, edges, edges_set, universe, source_tag)
                    elif lower.endswith(".txt"):
                        handle_txt(full, nodes, edges, edges_set, universe, source_tag)
                except Exception as e:
                    print(f"[INGEST] Error in {full}: {e}")

    return nodes, edges

# === HUBS, DEGREE, LAYOUT ===

def build_hubs(nodes, edges, edges_set):
    universes = defaultdict(int)
    types = defaultdict(int)
    for n in nodes.values():
        u = n.get("universe") or "General"
        t = (n.get("type") or "other").lower()
        universes[u] += 1
        types[t] += 1
    # Universe hubs
    for u in universes.keys():
        hub_id = f"hub:universe:{u}"
        add_node(
            nodes,
            hub_id,
            label=u,
            ntype="hub_universe",
            universe="Hub",
            tags=["hub", "universe"],
            sources=["HUB"],
        )
    # Type hubs (only if reasonably common)
    for t, count in types.items():
        if count < 10:
            continue
        hub_id = f"hub:type:{t}"
        add_node(
            nodes,
            hub_id,
            label=t.title(),
            ntype="hub_type",
            universe="Hub",
            tags=["hub", "type"],
            sources=["HUB"],
        )
    # Attach nodes to hubs
    for n in list(nodes.values()):
        if str(n.get("type", "")).startswith("hub_"):
            continue
        u = n.get("universe") or "General"
        t = (n.get("type") or "other").lower()
        add_edge(edges, edges_set, n["id"], f"hub:universe:{u}", etype="in_universe", weight=0.5)
        if types[t] >= 10:
            add_edge(edges, edges_set, n["id"], f"hub:type:{t}", etype="is_type", weight=0.5)

def compute_degree(nodes, edges):
    deg = defaultdict(int)
    for e in edges:
        deg[e["source"]] += 1
        deg[e["target"]] += 1
    for nid, n in nodes.items():
        n["degree"] = int(deg.get(nid, 0))

def apply_radial_layout(nodes_list):
    non_hub = [n for n in nodes_list if not str(n.get("type", "")).startswith("hub_")]
    hubs = [n for n in nodes_list if str(n.get("type", "")).startswith("hub_")]

    N = max(len(non_hub), 1)
    deg_vals = [n["degree"] for n in non_hub] if non_hub else [0]
    dmin = min(deg_vals)
    dmax = max(deg_vals)

    def norm_degree(d):
        if dmax == dmin:
            return 0.5
        return (d - dmin) / (dmax - dmin)

    # Sort for stable radial positioning
    non_hub.sort(
        key=lambda n: (
            (n.get("universe") or "ZZZ"),
            (n.get("type") or "zzz"),
            -n["degree"],
            n["id"],
        )
    )

    for i, n in enumerate(non_hub):
        a = 2 * math.pi * i / N
        nd = norm_degree(n["degree"])
        r = 0.25 + (1.0 - nd) * 0.65
        n["pre_x"] = r * math.cos(a)
        n["pre_y"] = r * math.sin(a)

    H = max(len(hubs), 1)
    for i, n in enumerate(hubs):
        a = 2 * math.pi * i / H
        r = 0.12
        n["pre_x"] = r * math.cos(a)
        n["pre_y"] = r * math.sin(a)

# === OUTPUT ===

def write_outputs(nodes, edges):
    ensure_dir(COMBINED_DIR)
    nodes_list = sorted(nodes.values(), key=lambda n: n["id"])
    edges_list = edges

    # layout
    apply_radial_layout(nodes_list)

    # JSON
    nodes_json = os.path.join(COMBINED_DIR, "G4_nodes_final.json")
    edges_json = os.path.join(COMBINED_DIR, "G4_edges_final.json")
    with open(nodes_json, "w", encoding="utf-8") as f:
        json.dump(nodes_list, f, ensure_ascii=False, indent=2)
    with open(edges_json, "w", encoding="utf-8") as f:
        json.dump(edges_list, f, ensure_ascii=False, indent=2)

    # CSV
    nodes_csv = os.path.join(COMBINED_DIR, "G4_nodes_final.csv")
    edges_csv = os.path.join(COMBINED_DIR, "G4_edges_final.csv")

    node_fields = sorted(set(itertools.chain.from_iterable(n.keys() for n in nodes_list)))
    edge_fields = sorted(set(itertools.chain.from_iterable(e.keys() for e in edges_list)))

    with open(nodes_csv, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=node_fields)
        w.writeheader()
        for n in nodes_list:
            row = dict(n)
            if isinstance(row.get("tags"), list):
                row["tags"] = "|".join(row["tags"])
            if isinstance(row.get("sources"), list):
                row["sources"] = "|".join(row["sources"])
            w.writerow(row)

    with open(edges_csv, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=edge_fields)
        w.writeheader()
        for e in edges_list:
            w.writerow(e)

    # Neo4j Cypher
    cypher = """
// Combined G4 import (nodes)
LOAD CSV WITH HEADERS FROM 'file:///G4_nodes_final.csv' AS row
WITH row,
     CASE WHEN row.tags IS NULL OR row.tags = '' THEN [] ELSE split(row.tags,'|') END    AS tags,
     CASE WHEN row.sources IS NULL OR row.sources = '' THEN [] ELSE split(row.sources,'|') END AS sources
MERGE (n:G4Node {id: row.id})
SET n.label     = row.label,
    n.type      = row.type,
    n.universe  = row.universe,
    n.case      = row.case,
    n.group     = row.group,
    n.tags      = tags,
    n.sources   = sources,
    n.degree    = toInteger(coalesce(row.degree,'0')),
    n.pre_x     = toFloat(coalesce(row.pre_x,'0')),
    n.pre_y     = toFloat(coalesce(row.pre_y,'0'));

// Combined G4 import (edges)
LOAD CSV WITH HEADERS FROM 'file:///G4_edges_final.csv' AS row
MATCH (s:G4Node {id: row.source}),
      (t:G4Node {id: row.target})
MERGE (s)-[r:G4_REL {type: row.type}]->(t)
SET r.weight   = toFloat(coalesce(row.weight,'1')),
    r.universe = row.universe,
    r.file     = row.file,
    r.source   = row.source;
""".strip() + "\n"

    cypher_path = os.path.join(COMBINED_DIR, "G4_combined_import.cypher")
    with open(cypher_path, "w", encoding="utf-8") as f:
        f.write(cypher)

    # HTML viewer
    html = """<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8"/>
<title>G4 Litigation Brain — Combined Wheel</title>
<meta name="viewport" content="width=device-width,initial-scale=1"/>
<style>
html,body{margin:0;height:100%;background:#020617;color:#e5e7eb;font-family:system-ui,-apple-system,Segoe UI,Roboto,Arial,sans-serif}
header{display:flex;align-items:center;gap:10px;padding:10px 14px;background:#020617;border-bottom:1px solid #111827;position:sticky;top:0;z-index:10}
header h1{font-size:15px;margin:0;font-weight:600}
.toolbar{margin-left:auto;display:flex;gap:8px;align-items:center}
input[type=text]{background:#020617;border:1px solid #1f2937;border-radius:8px;padding:6px 8px;color:#e5e7eb;font-size:12px;min-width:220px}
select{background:#020617;border:1px solid #1f2937;border-radius:8px;padding:6px 8px;color:#e5e7eb;font-size:12px;}
#stage{width:100%;height:calc(100% - 46px)}
.badge{font-size:12px;border-radius:999px;border:1px solid #1f2937;padding:4px 8px;background:#020617}
.legend{position:fixed;right:10px;bottom:10px;background:#020617;border-radius:10px;border:1px solid #1f2937;padding:8px 10px;font-size:11px;max-width:260px}
.legend-row{display:flex;align-items:center;gap:5px;margin:1px 0}
.dot{width:9px;height:9px;border-radius:999px;display:inline-block}
.toast{position:fixed;left:10px;bottom:10px;background:#020617;border-radius:10px;border:1px solid #1f2937;padding:8px 10px;font-size:11px;display:none}
</style>
<script src="https://cdn.jsdelivr.net/npm/d3@7"></script>
</head>
<body>
<header>
  <h1>G4 Litigation Brain — Combined Wheel</h1>
  <div id="counts" class="badge">Loading…</div>
  <div class="toolbar">
    <select id="universeFilter">
      <option value="ALL">ALL UNIVERSES</option>
    </select>
    <input id="search" type="text" placeholder="Search id / label / type / universe / tags / sources…"/>
  </div>
</header>
<svg id="stage"></svg>
<div class="legend">
  <div><strong>Legend</strong></div>
  <div class="legend-row"><span class="dot" style="background:#60a5fa"></span> Universe / type hubs</div>
  <div class="legend-row"><span class="dot" style="background:#f97316"></span> Authorities (MCR/MCL/MRE)</div>
  <div class="legend-row"><span class="dot" style="background:#22c55e"></span> Case / Order / Form</div>
  <div class="legend-row"><span class="dot" style="background:#eab308"></span> Fact / Evidence / Violation</div>
  <div class="legend-row"><span class="dot" style="background:#9ca3af"></span> Other / artifact</div>
</div>
<div id="toast" class="toast"></div>
<script>
const NODES_URL = 'G4_nodes_final.json';
const EDGES_URL = 'G4_edges_final.json';

const svg = d3.select('#stage');
const g = svg.append('g');
let width = 0, height = 0;

const zoom = d3.zoom().scaleExtent([0.05, 8]).on('zoom', (e)=>{ g.attr('transform', e.transform); });
svg.call(zoom);

let nodes = [];
let edges = [];
let nodeById = new Map();

function resize(){
  width = window.innerWidth;
  height = window.innerHeight - 46;
  svg.attr('width', width).attr('height', height);
}
window.addEventListener('resize', ()=>{ resize(); rerender(); });
resize();

function toast(msg){
  const el = document.getElementById('toast');
  el.textContent = msg;
  el.style.display = 'block';
  setTimeout(()=>{ el.style.display='none'; }, 2200);
}

function colorFor(n){
  const t = (n.type || '').toLowerCase();
  const id = String(n.id);
  if(t === 'hub_universe' || t === 'hub_type') return '#60a5fa';
  if(id.startsWith('mcr:') || id.startsWith('mcl:') || id.startsWith('mre:')) return '#f97316';
  if(t.includes('case') || t.includes('order') || t.includes('form')) return '#22c55e';
  if(t.includes('fact') || t.includes('evidence') || t.includes('violation')) return '#eab308';
  return '#9ca3af';
}

function projectPre(n){
  const px = (typeof n.pre_x === 'number') ? n.pre_x : parseFloat(n.pre_x || '0') || 0;
  const py = (typeof n.pre_y === 'number') ? n.pre_y : parseFloat(n.pre_y || '0') || 0;
  const s  = 0.45 * Math.min(width, height);
  n.x = width/2 + px * s;
  n.y = height/2 + py * s;
}

function filterNodes(){
  const q = (document.getElementById('search').value || '').toLowerCase().trim();
  const u = document.getElementById('universeFilter').value;
  return nodes.filter(n=>{
    if(u !== 'ALL'){
      const nu = String(n.universe || '');
      if(nu !== u) return false;
    }
    if(!q) return true;
    const hay = [
      n.id,
      n.label,
      n.type,
      (n.universe || ''),
      (n.case || ''),
      (n.group || ''),
      (n.tags || []).join(' '),
      (n.sources || []).join(' ')
    ].join(' ').toLowerCase();
    return hay.includes(q);
  });
}

function rerender(){
  if(!nodes.length) return;
  const filtered = filterNodes();
  const idset = new Set(filtered.map(n=>n.id));
  const fedges = edges.filter(e=> idset.has(e.source) && idset.has(e.target));
  filtered.forEach(projectPre);

  const linkSel = g.selectAll('line').data(fedges, d=>d.source+'->'+d.target+':'+d.type);
  linkSel.exit().remove();
  const linkEnter = linkSel.enter().append('line')
    .attr('stroke','#1f2937')
    .attr('stroke-opacity',0.45);
  const link = linkEnter.merge(linkSel);

  const nodeSel = g.selectAll('g.node').data(filtered, d=>d.id);
  nodeSel.exit().remove();
  const nodeEnter = nodeSel.enter().append('g').attr('class','node');
  nodeEnter.append('circle').attr('r', 5);
  nodeEnter.append('text')
    .attr('x', 8)
    .attr('y', 3)
    .attr('font-size', 9)
    .attr('fill','#e5e7eb');
  const node = nodeEnter.merge(nodeSel);

  node.select('circle').attr('fill', d=>colorFor(d));
  node.select('text').text(d=>d.label || d.id);

  link
    .attr('x1', d=>nodeById.get(d.source).x)
    .attr('y1', d=>nodeById.get(d.source).y)
    .attr('x2', d=>nodeById.get(d.target).x)
    .attr('y2', d=>nodeById.get(d.target).y);
  node.attr('transform', d=>'translate('+d.x+','+d.y+')');

  node.on('mouseover', (ev,d)=>{
    toast((d.label || d.id) + ' ['+ (d.type||'node') +'] · degree '+(d.degree||0));
  });
}

Promise.all([
  fetch(NODES_URL).then(r=>r.json()),
  fetch(EDGES_URL).then(r=>r.json())
]).then(([nd, ed])=>{
  nodes = nd.map(d => ({...d, id: String(d.id)}));
  edges = ed.map(e => ({
    source: String(e.source),
    target: String(e.target),
    type: e.type || 'rel',
    weight: e.weight || 1
  }));
  nodeById = new Map(nodes.map(n=>[n.id, n]));

  const universes = Array.from(new Set(nodes.map(n=>String(n.universe || ''))))
    .filter(u=>u && u !== 'Hub')
    .sort();
  const sel = document.getElementById('universeFilter');
  universes.forEach(u=>{
    const opt = document.createElement('option');
    opt.value = u;
    opt.textContent = u;
    sel.appendChild(opt);
  });

  document.getElementById('counts').textContent =
    nodes.length + ' nodes \u2022 ' + edges.length + ' edges';

  rerender();
}).catch(err=>{
  console.error(err);
  toast('Failed to load G4_nodes_final/edges_final — keep this HTML in same folder as the JSON files.');
});

document.getElementById('search').addEventListener('input', ()=>rerender());
document.getElementById('universeFilter').addEventListener('change', ()=>rerender());
</script>
</body>
</html>
"""
    html_path = os.path.join(COMBINED_DIR, "G4_Combined_Wheel.html")
    with open(html_path, "w", encoding="utf-8") as f:
        f.write(html)

    # README
    readme = f"""G4 Litigation Brain Graph Pack (FINAL COMBINED)
Generated: {datetime.utcnow().isoformat()}Z

Sources:
- {", ".join(ZIP_SOURCES)}

Outputs:
- G4_nodes_final.json          — unified nodes (with degree, pre_x, pre_y)
- G4_edges_final.json          — unified edges
- G4_nodes_final.csv           — unified nodes CSV
- G4_edges_final.csv           — unified edges CSV
- G4_combined_import.cypher    — Neo4j LOAD CSV script
- G4_Combined_Wheel.html       — interactive D3 viewer

To use:
1) Neo4j:
   - Copy G4_nodes_final.csv and G4_edges_final.csv into your Neo4j `import/` dir.
   - Run G4_combined_import.cypher in Neo4j Browser.

2) Viewer:
   - Keep G4_Combined_Wheel.html, G4_nodes_final.json, and G4_edges_final.json
     in the same folder and open the HTML file in a browser.
"""
    readme_path = os.path.join(COMBINED_DIR, "README_G4_final.txt")
    with open(readme_path, "w", encoding="utf-8") as f:
        f.write(readme)

    # Final zip
    pack_path = os.path.join(BASE_DIR, "G4_Litigation_Brain_Pack_FINAL.zip")
    with zipfile.ZipFile(pack_path, "w", compression=zipfile.ZIP_DEFLATED) as z:
        for name in [
            "G4_nodes_final.json",
            "G4_edges_final.json",
            "G4_nodes_final.csv",
            "G4_edges_final.csv",
            "G4_combined_import.cypher",
            "G4_Combined_Wheel.html",
            "README_G4_final.txt",
        ]:
            z.write(os.path.join(COMBINED_DIR, name), arcname=name)
    print(f"[PACK] Final pack written to {pack_path}")

def main():
    print("=== G4 Mesh All Graphs ===")
    extracted = extract_zips()
    if not extracted:
        print("No zip sources found. Place your zip packs next to this script and rerun.")
        return
    print(f"[INGEST] Roots: {extracted}")
    nodes, edges = ingest_all(extracted)
    print(f"[STATS] Nodes: {len(nodes)}  Edges: {len(edges)}")
    build_hubs(nodes, edges, set())
    compute_degree(nodes, edges)
    write_outputs(nodes, edges)
    print("=== Done. Unified pack: G4_Litigation_Brain_Pack_FINAL.zip ===")

if __name__ == "__main__":
    main()
