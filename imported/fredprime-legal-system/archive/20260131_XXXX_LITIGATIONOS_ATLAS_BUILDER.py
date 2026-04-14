#!/usr/bin/env python3
# 20260131_XXXX_LITIGATIONOS_ATLAS_BUILDER.py
# Purpose: Build ONE massive static atlas (force-directed graph) from arbitrary ZIP packs + panel images.
# Output: build/atlas/atlas.html + atlas_data.json + run ledger + manifest (no hashes).

from __future__ import annotations

import argparse
import csv
import datetime as _dt
import json
import re
import shutil
import urllib.request
import zipfile
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

# -----------------------------
# Utility: deterministic time label
# -----------------------------

def now_utc_iso() -> str:
    return _dt.datetime.utcnow().replace(microsecond=0).isoformat() + "Z"


def safe_mkdir(p: Path) -> None:
    p.mkdir(parents=True, exist_ok=True)


def write_text(p: Path, s: str) -> None:
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(s, encoding="utf-8", newline="\n")


def write_json(p: Path, obj: Any) -> None:
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(obj, ensure_ascii=False, indent=2), encoding="utf-8", newline="\n")


def slugify(s: str, max_len: int = 80) -> str:
    s2 = re.sub(r"[^A-Za-z0-9]+", "_", s.strip())
    s2 = re.sub(r"_+", "_", s2).strip("_")
    if not s2:
        s2 = "x"
    return s2[:max_len]


def rel_no_drive(p: Path) -> str:
    # stable-ish representation without drive letters
    s = str(p).replace("\\", "/")
    s = re.sub(r"^[A-Za-z]:/", "", s)
    return s


def is_image_path(p: Path) -> bool:
    return p.suffix.lower() in [".png", ".jpg", ".jpeg", ".webp", ".gif"]


def is_text_path(p: Path) -> bool:
    return p.suffix.lower() in [".txt", ".md"]


def is_table_path(p: Path) -> bool:
    return p.suffix.lower() in [".csv", ".tsv"]


def is_json_path(p: Path) -> bool:
    return p.suffix.lower() in [".json", ".jsonl", ".ndjson"]


def is_graph_path(p: Path) -> bool:
    return p.suffix.lower() in [".graphml", ".gexf"]


def sha1_not_allowed_note() -> str:
    # User asked no CRC/SHA computed in manifests; we comply by not computing any digests.
    return "no_digests_computed"


# -----------------------------
# Run ledger
# -----------------------------
class RunLedger:
    def __init__(self, ledger_path: Path):
        self.ledger_path = ledger_path
        self.events: List[Dict[str, Any]] = []

    def log(self, stage: str, **kv: Any) -> None:
        evt = {"ts": now_utc_iso(), "stage": stage}
        evt.update(kv)
        self.events.append(evt)
        self.ledger_path.parent.mkdir(parents=True, exist_ok=True)
        with self.ledger_path.open("a", encoding="utf-8", newline="\n") as f:
            f.write(json.dumps(evt, ensure_ascii=False) + "\n")


# -----------------------------
# ZIP safe extraction (no zip slip)
# -----------------------------

def safe_extract_zip(zip_path: Path, dest_dir: Path, ledger: RunLedger) -> List[Path]:
    extracted: List[Path] = []
    with zipfile.ZipFile(zip_path, "r") as z:
        for info in z.infolist():
            # Skip directory entries
            if info.is_dir():
                continue
            name = info.filename.replace("\\", "/")
            # Prevent zip slip
            if name.startswith("/") or ".." in name.split("/"):
                ledger.log("zip_skip_unsafe_path", zip=str(zip_path), member=name)
                continue
            out_path = dest_dir / name
            out_path.parent.mkdir(parents=True, exist_ok=True)
            with z.open(info, "r") as src, out_path.open("wb") as dst:
                shutil.copyfileobj(src, dst)
            extracted.append(out_path)
    ledger.log("zip_extracted", zip=str(zip_path), dest=str(dest_dir), files=len(extracted))
    return extracted


# -----------------------------
# Table reader (CSV/TSV) with delimiter sniff
# -----------------------------

def read_table_rows(path: Path, ledger: RunLedger, max_rows: int = 2_000_000) -> Tuple[List[str], List[Dict[str, str]]]:
    raw = path.read_text(encoding="utf-8", errors="replace")
    sample = raw[:10000]
    dialect = None
    try:
        dialect = csv.Sniffer().sniff(sample, delimiters=[",", "\t", ";", "|"])
    except Exception:
        dialect = csv.excel
    rows: List[Dict[str, str]] = []
    with path.open("r", encoding="utf-8", errors="replace", newline="") as f:
        reader = csv.DictReader(f, dialect=dialect)
        headers = reader.fieldnames or []
        for i, r in enumerate(reader):
            if i >= max_rows:
                break
            # normalize None to ""
            rr = {k: (v if v is not None else "") for k, v in r.items() if k is not None}
            rows.append(rr)
    ledger.log("table_read", path=str(path), rows=len(rows), cols=len(headers))
    return headers, rows


# -----------------------------
# JSON reader (json / jsonl / ndjson)
# -----------------------------

def read_json_items(path: Path, ledger: RunLedger, max_items: int = 2_000_000) -> List[Any]:
    suf = path.suffix.lower()
    items: List[Any] = []
    if suf == ".json":
        try:
            obj = json.loads(path.read_text(encoding="utf-8", errors="replace"))
            if isinstance(obj, list):
                items = obj[:max_items]
            else:
                items = [obj]
        except Exception as e:
            ledger.log("json_read_error", path=str(path), error=str(e))
            items = []
    else:
        # jsonl / ndjson
        with path.open("r", encoding="utf-8", errors="replace", newline="") as f:
            for i, line in enumerate(f):
                if i >= max_items:
                    break
                line = line.strip()
                if not line:
                    continue
                try:
                    items.append(json.loads(line))
                except Exception:
                    # keep raw line if not parseable
                    items.append({"_raw": line})
    ledger.log("json_items_read", path=str(path), items=len(items))
    return items


# -----------------------------
# Graph ingest heuristics
# -----------------------------
EDGE_SRC_KEYS = ["source", "src", "from", "u", "start", "tail"]
EDGE_TGT_KEYS = ["target", "tgt", "to", "v", "end", "head"]

NODE_ID_KEYS = ["id", "node_id", "uid", "key"]
NODE_LABEL_KEYS = ["label", "name", "title"]


def pick_first(d: Dict[str, Any], keys: List[str]) -> Optional[str]:
    for k in keys:
        if k in d and str(d[k]).strip() != "":
            return str(d[k]).strip()
    return None


def looks_like_edge_record(d: Dict[str, Any]) -> bool:
    s = pick_first(d, EDGE_SRC_KEYS)
    t = pick_first(d, EDGE_TGT_KEYS)
    return bool(s and t)


def looks_like_node_record(d: Dict[str, Any]) -> bool:
    nid = pick_first(d, NODE_ID_KEYS)
    if nid:
        return True
    # fallback: has label-like field
    lab = pick_first(d, NODE_LABEL_KEYS)
    return bool(lab)


def stable_row_id(file_tag: str, row_index: int) -> str:
    # no hashing; deterministic ID
    return f"{file_tag}:row{row_index}"


def normalize_type(val: Optional[str], default: str) -> str:
    if not val:
        return default
    v = slugify(val.lower(), 40)
    return v if v else default


def extract_weight(d: Dict[str, Any]) -> float:
    for k in ["weight", "w", "score", "value", "count", "freq"]:
        if k in d:
            try:
                return float(str(d[k]).strip())
            except Exception:
                continue
    return 1.0


def token_set(s: str) -> List[str]:
    s = s.lower()
    s = re.sub(r"[^a-z0-9]+", " ", s)
    toks = [t for t in s.split() if len(t) >= 3]
    # deterministic unique preserve order
    seen = set()
    out = []
    for t in toks:
        if t not in seen:
            seen.add(t)
            out.append(t)
    return out[:24]


# -----------------------------
# Vendor JS downloader (offline libs)
# -----------------------------
VENDOR_LIBS = [
    # Cytoscape core
    ("cytoscape.min.js", "https://cdn.jsdelivr.net/npm/cytoscape@3.27.0/dist/cytoscape.min.js"),
    # Layouts
    ("cytoscape-fcose.js", "https://cdn.jsdelivr.net/npm/cytoscape-fcose@2.2.0/cytoscape-fcose.js"),
    ("cose-bilkent.js", "https://cdn.jsdelivr.net/npm/cytoscape-cose-bilkent@4.1.0/cytoscape-cose-bilkent.js"),
    # Optional UI helpers (kept minimal)
]


def download_vendor_libs(vendor_dir: Path, ledger: RunLedger) -> None:
    safe_mkdir(vendor_dir)
    for fname, url in VENDOR_LIBS:
        out = vendor_dir / fname
        if out.exists() and out.stat().st_size > 0:
            ledger.log("vendor_exists", file=str(out))
            continue
        try:
            ledger.log("vendor_download_start", url=url, file=str(out))
            with urllib.request.urlopen(url, timeout=60) as resp:
                data = resp.read()
            out.write_bytes(data)
            ledger.log("vendor_download_ok", url=url, file=str(out), bytes=len(data))
        except Exception as e:
            ledger.log("vendor_download_fail", url=url, file=str(out), error=str(e))


# -----------------------------
# HTML template (single page atlas)
# -----------------------------

def build_atlas_html(data_inline_json: str, panels: List[Dict[str, str]], offline_vendor_rel: str) -> str:
    # No ellipses. Full HTML.
    panel_cards_html = "\n".join([
        f"""
        <div class=\"panelCard\" data-panel-idx=\"{i}\">
          <div class=\"panelTitle\">{escape_html(p.get("title","Panel"))}</div>
          <img class=\"panelImg\" src=\"{escape_html(p["src"])}\" alt=\"{escape_html(p.get("title","panel"))}\">
        </div>
        """.strip()
        for i, p in enumerate(panels)
    ])

    html = f"""<!doctype html>
<html lang=\"en\">
<head>
  <meta charset=\"utf-8\">
  <meta http-equiv=\"x-ua-compatible\" content=\"ie=edge\">
  <meta name=\"viewport\" content=\"width=device-width, initial-scale=1\">
  <title>LitigationOS Atlas</title>
  <style>
    :root {{
      --bg: #0b0f14;
      --panel: #101826;
      --panel2: #0f1722;
      --fg: #e6edf3;
      --muted: #9fb2c5;
      --border: #223144;
      --accent: #7aa2f7;
      --warn: #f7c97a;
      --bad: #f77a7a;
      --ok: #7af7b0;
    }}
    html, body {{
      height: 100%;
      margin: 0;
      background: var(--bg);
      color: var(--fg);
      font-family: ui-sans-serif, system-ui, -apple-system, Segoe UI, Roboto, Helvetica, Arial, \"Apple Color Emoji\", \"Segoe UI Emoji\";
    }}
    .app {{
      display: grid;
      grid-template-columns: 360px 1fr 420px;
      grid-template-rows: 64px 1fr 220px;
      height: 100%;
    }}
    .topbar {{
      grid-column: 1 / 4;
      grid-row: 1;
      display: flex;
      align-items: center;
      justify-content: space-between;
      padding: 0 16px;
      border-bottom: 1px solid var(--border);
      background: linear-gradient(180deg, var(--panel), var(--panel2));
    }}
    .brand {{
      display: flex;
      flex-direction: column;
      gap: 2px;
    }}
    .brand .t1 {{
      font-size: 16px;
      font-weight: 700;
      letter-spacing: 0.4px;
    }}
    .brand .t2 {{
      font-size: 12px;
      color: var(--muted);
    }}
    .btnRow {{
      display: flex;
      gap: 8px;
      align-items: center;
    }}
    button {{
      background: transparent;
      color: var(--fg);
      border: 1px solid var(--border);
      border-radius: 10px;
      padding: 8px 10px;
      cursor: pointer;
      font-size: 12px;
    }}
    button:hover {{
      border-color: var(--accent);
    }}
    .left {{
      grid-column: 1;
      grid-row: 2;
      overflow: auto;
      border-right: 1px solid var(--border);
      background: var(--panel2);
      padding: 12px;
    }}
    .center {{
      grid-column: 2;
      grid-row: 2;
      position: relative;
      background: #070a0f;
    }}
    #cy {{
      position: absolute;
      inset: 0;
    }}
    .right {{
      grid-column: 3;
      grid-row: 2;
      overflow: auto;
      border-left: 1px solid var(--border);
      background: var(--panel2);
      padding: 12px;
    }}
    .bottom {{
      grid-column: 1 / 4;
      grid-row: 3;
      border-top: 1px solid var(--border);
      background: var(--panel);
      overflow: hidden;
      display: grid;
      grid-template-columns: 1fr;
      grid-template-rows: 1fr;
    }}
    .deck {{
      height: 100%;
      overflow: auto;
      padding: 10px;
      display: grid;
      grid-template-columns: repeat(auto-fill, minmax(160px, 1fr));
      gap: 10px;
    }}
    .cardTile {{
      border: 1px solid var(--border);
      border-radius: 12px;
      background: #0b1220;
      padding: 8px;
      display: grid;
      grid-template-rows: 120px auto;
      gap: 8px;
      cursor: pointer;
    }}
    .cardTile:hover {{
      border-color: var(--accent);
    }}
    .cardTile img {{
      width: 100%;
      height: 120px;
      object-fit: cover;
      border-radius: 10px;
      border: 1px solid #0d1a2b;
    }}
    .cardTile .ct {{
      font-size: 12px;
      color: var(--muted);
      word-break: break-word;
    }}
    .section {{
      margin-bottom: 14px;
      padding-bottom: 14px;
      border-bottom: 1px solid var(--border);
    }}
    .sectionTitle {{
      font-size: 12px;
      font-weight: 700;
      letter-spacing: 0.8px;
      text-transform: uppercase;
      color: var(--muted);
      margin-bottom: 8px;
    }}
    .kv {{
      display: grid;
      grid-template-columns: 120px 1fr;
      gap: 6px 10px;
      font-size: 12px;
    }}
    .kv .k {{
      color: var(--muted);
    }}
    input[type=\"text\"] {{
      width: 100%;
      box-sizing: border-box;
      padding: 9px 10px;
      border-radius: 10px;
      border: 1px solid var(--border);
      background: #0b1220;
      color: var(--fg);
      outline: none;
      font-size: 12px;
    }}
    input[type=\"text\"]:focus {{
      border-color: var(--accent);
    }}
    .pillRow {{
      display: flex;
      flex-wrap: wrap;
      gap: 8px;
    }}
    .pill {{
      border: 1px solid var(--border);
      background: #0b1220;
      color: var(--fg);
      border-radius: 999px;
      padding: 6px 10px;
      font-size: 12px;
      cursor: pointer;
      user-select: none;
    }}
    .pill.on {{
      border-color: var(--accent);
      box-shadow: 0 0 0 1px rgba(122,162,247,0.20) inset;
    }}
    .panelGrid {{
      display: grid;
      grid-template-columns: 1fr;
      gap: 10px;
    }}
    .panelCard {{
      border: 1px solid var(--border);
      border-radius: 12px;
      background: #0b1220;
      padding: 8px;
      display: grid;
      grid-template-rows: auto 1fr;
      gap: 8px;
    }}
    .panelTitle {{
      font-size: 12px;
      font-weight: 700;
      color: var(--muted);
      word-break: break-word;
    }}
    .panelImg {{
      width: 100%;
      height: 220px;
      object-fit: contain;
      background: #070a0f;
      border-radius: 10px;
      border: 1px solid #0d1a2b;
    }}
    .hint {{
      font-size: 12px;
      color: var(--muted);
      line-height: 1.4;
    }}
    .mono {{
      font-family: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, \"Liberation Mono\", \"Courier New\", monospace;
      font-size: 11px;
      color: var(--muted);
      word-break: break-word;
    }}
    .badge {{
      display: inline-block;
      font-size: 11px;
      padding: 2px 8px;
      border-radius: 999px;
      border: 1px solid var(--border);
      background: #0b1220;
      color: var(--muted);
      margin-right: 6px;
    }}
  </style>
</head>
<body>
  <div class=\"app\">
    <div class=\"topbar\">
      <div class=\"brand\">
        <div class=\"t1\">LitigationOS Atlas</div>
        <div class=\"t2\">Massive force-directed static atlas with panels, cards, and crosswired packs</div>
      </div>
      <div class=\"btnRow\">
        <button id=\"btnRelayout\">Relayout</button>
        <button id=\"btnFit\">Fit</button>
        <button id=\"btnExportPng\">Export PNG</button>
        <button id=\"btnExportJson\">Export JSON</button>
        <button id=\"btnToggleLabels\">Toggle Labels</button>
      </div>
    </div>

    <div class=\"left\">
      <div class=\"section\">
        <div class=\"sectionTitle\">Search</div>
        <input id=\"q\" type=\"text\" placeholder=\"Search label, id, type, source\">
        <div class=\"hint\" style=\"margin-top:8px;\">
          Enter to jump. Escape clears.
        </div>
      </div>

      <div class=\"section\">
        <div class=\"sectionTitle\">Filters</div>
        <div class=\"hint\">Toggle node kinds. Toggle edge kinds. Heuristic edges are always labeled as heuristic.</div>
        <div style=\"height:10px;\"></div>
        <div class=\"sectionTitle\">Node kinds</div>
        <div class=\"pillRow\" id=\"nodeKindPills\"></div>
        <div style=\"height:10px;\"></div>
        <div class=\"sectionTitle\">Edge kinds</div>
        <div class=\"pillRow\" id=\"edgeKindPills\"></div>
      </div>

      <div class=\"section\">
        <div class=\"sectionTitle\">Panels</div>
        <div class=\"panelGrid\">
          {panel_cards_html}
        </div>
      </div>

      <div class=\"section\">
        <div class=\"sectionTitle\">Status</div>
        <div class=\"mono\" id=\"status\"></div>
      </div>
    </div>

    <div class=\"center\">
      <div id=\"cy\"></div>
    </div>

    <div class=\"right\">
      <div class=\"section\">
        <div class=\"sectionTitle\">Selection</div>
        <div id=\"selBadges\"></div>
        <div class=\"kv\">
          <div class=\"k\">id</div><div class=\"mono\" id=\"selId\"></div>
          <div class=\"k\">label</div><div class=\"mono\" id=\"selLabel\"></div>
          <div class=\"k\">type</div><div class=\"mono\" id=\"selType\"></div>
          <div class=\"k\">kind</div><div class=\"mono\" id=\"selKind\"></div>
          <div class=\"k\">source</div><div class=\"mono\" id=\"selSource\"></div>
          <div class=\"k\">meta</div><div class=\"mono\" id=\"selMeta\"></div>
        </div>
      </div>

      <div class=\"section\">
        <div class=\"sectionTitle\">Card preview</div>
        <div class=\"hint\">If the node is a card or has an attached image, it appears here.</div>
        <div style=\"height:10px;\"></div>
        <img id=\"selImg\" class=\"panelImg\" alt=\"preview\">
      </div>
    </div>

    <div class=\"bottom\">
      <div class=\"deck\" id=\"deck\"></div>
    </div>
  </div>

  <script src=\"{offline_vendor_rel}/cytoscape.min.js\"></script>
  <script src=\"{offline_vendor_rel}/cose-bilkent.js\"></script>
  <script src=\"{offline_vendor_rel}/cytoscape-fcose.js\"></script>

  <script>
    const ATLAS = {data_inline_json};

    function el(id) {{ return document.getElementById(id); }}

    function uniq(arr) {{
      const s = new Set();
      const out = [];
      for (const x of arr) {{
        if (!s.has(x)) {{ s.add(x); out.push(x); }}
      }}
      return out;
    }}

    function setStatus(msg) {{
      el("status").textContent = msg;
    }}

    function esc(s) {{
      if (s === null || s === undefined) return "";
      return String(s);
    }}

    const nodes = ATLAS.nodes.map(n => {{
      return {{
        data: {{
          id: n.id,
          label: n.label || n.id,
          type: n.type || "unknown",
          kind: n.kind || "node",
          source: n.source || "",
          img: n.img || "",
          meta: n.meta || {{}},
          degree: 0
        }},
        position: n.pos ? {{ x: n.pos.x, y: n.pos.y }} : undefined
      }};
    }});

    const edges = ATLAS.edges.map((e, idx) => {{
      return {{
        data: {{
          id: e.id || ("e" + idx),
          source: e.source,
          target: e.target,
          label: e.label || "",
          kind: e.kind || "edge",
          etype: e.etype || "rel",
          weight: e.weight || 1.0,
          source_pack: e.source_pack || ""
        }}
      }};
    }});

    // compute degrees
    const deg = new Map();
    for (const n of nodes) deg.set(n.data.id, 0);
    for (const e of edges) {{
      deg.set(e.data.source, (deg.get(e.data.source) || 0) + 1);
      deg.set(e.data.target, (deg.get(e.data.target) || 0) + 1);
    }}
    for (const n of nodes) {{
      n.data.degree = deg.get(n.data.id) || 0;
    }}

    const nodeKinds = uniq(nodes.map(n => n.data.kind)).sort();
    const edgeKinds = uniq(edges.map(e => e.data.kind)).sort();

    const nodeKindState = new Map();
    const edgeKindState = new Map();
    for (const k of nodeKinds) nodeKindState.set(k, true);
    for (const k of edgeKinds) edgeKindState.set(k, true);

    function renderPills(containerId, kinds, stateMap, onChange) {{
      const c = el(containerId);
      c.innerHTML = "";
      for (const k of kinds) {{
        const d = document.createElement("div");
        d.className = "pill on";
        d.textContent = k;
        d.onclick = () => {{
          const cur = stateMap.get(k);
          stateMap.set(k, !cur);
          d.className = "pill" + (stateMap.get(k) ? " on" : "");
          onChange();
        }};
        c.appendChild(d);
      }}
    }}

    let labelsOn = true;

    const cy = cytoscape({{
      container: el("cy"),
      elements: {{
        nodes: nodes,
        edges: edges
      }},
      style: [
        {{
          selector: "node",
          style: {{
            "background-color": "#223144",
            "label": (ele) => labelsOn ? ele.data("label") : "",
            "font-size": 9,
            "color": "#e6edf3",
            "text-outline-width": 2,
            "text-outline-color": "#070a0f",
            "text-valign": "center",
            "text-halign": "center",
            "width": (ele) => {{
              const d = Math.min(60, 10 + Math.sqrt(ele.data("degree") || 0) * 6);
              return d;
            }},
            "height": (ele) => {{
              const d = Math.min(60, 10 + Math.sqrt(ele.data("degree") || 0) * 6);
              return d;
            }},
            "border-width": 1,
            "border-color": "#2b3b52"
          }}
        }},
        {{
          selector: 'node[kind = "card"]',
          style: {{
            "background-color": "#0b1220",
            "border-color": "#7aa2f7",
            "border-width": 2,
            "shape": "round-rectangle"
          }}
        }},
        {{
          selector: "edge",
          style: {{
            "width": (ele) => {{
              const w = ele.data("weight") || 1.0;
              return Math.max(1, Math.min(6, Math.log10(1 + w) * 3));
            }},
            "line-color": "#2b3b52",
            "curve-style": "bezier",
            "opacity": 0.45,
            "target-arrow-shape": "triangle",
            "target-arrow-color": "#2b3b52",
            "label": (ele) => labelsOn ? ele.data("label") : "",
            "font-size": 8,
            "color": "#9fb2c5",
            "text-outline-width": 2,
            "text-outline-color": "#070a0f"
          }}
        }},
        {{
          selector: 'edge[kind = "heuristic"]',
          style: {{
            "line-style": "dashed",
            "line-color": "#f7c97a",
            "target-arrow-color": "#f7c97a",
            "opacity": 0.35
          }}
        }},
        {{
          selector: ":selected",
          style: {{
            "border-width": 3,
            "border-color": "#7aa2f7",
            "line-color": "#7aa2f7",
            "target-arrow-color": "#7aa2f7",
            "opacity": 1.0
          }}
        }}
      ]
    }});

    function applyFilters() {{
      cy.batch(() => {{
        cy.nodes().forEach(n => {{
          const on = nodeKindState.get(n.data("kind"));
          n.style("display", on ? "element" : "none");
        }});
        cy.edges().forEach(e => {{
          const on = edgeKindState.get(e.data("kind"));
          e.style("display", on ? "element" : "none");
        }});
      }});
      setStatus("nodes=" + cy.nodes(":visible").length + " edges=" + cy.edges(":visible").length);
    }}

    function doLayout() {{
      const hasPositions = ATLAS.nodes.some(n => n.pos && typeof n.pos.x === "number");
      const usePreset = hasPositions;
      if (usePreset) {{
        setStatus("layout=preset positions loaded");
        cy.layout({{ name: "preset", fit: true, padding: 30 }}).run();
        return;
      }}
      setStatus("layout=fcose running");
      cy.layout({{
        name: "fcose",
        animate: false,
        fit: true,
        padding: 30,
        nodeSeparation: 60,
        idealEdgeLength: 120
      }}).run();
    }}

    function clearSelection() {{
      el("selId").textContent = "";
      el("selLabel").textContent = "";
      el("selType").textContent = "";
      el("selKind").textContent = "";
      el("selSource").textContent = "";
      el("selMeta").textContent = "";
      el("selBadges").innerHTML = "";
      el("selImg").src = "";
    }}

    function setSelectionBadges(items) {{
      const box = el("selBadges");
      box.innerHTML = "";
      for (const s of items) {{
        const b = document.createElement("span");
        b.className = "badge";
        b.textContent = s;
        box.appendChild(b);
      }}
    }}

    cy.on("select", "node", (evt) => {{
      const n = evt.target;
      el("selId").textContent = esc(n.data("id"));
      el("selLabel").textContent = esc(n.data("label"));
      el("selType").textContent = esc(n.data("type"));
      el("selKind").textContent = esc(n.data("kind"));
      el("selSource").textContent = esc(n.data("source"));
      el("selMeta").textContent = JSON.stringify(n.data("meta") || {{}}, null, 2);

      const badges = [];
      if (n.data("kind")) badges.push("kind=" + n.data("kind"));
      if (n.data("type")) badges.push("type=" + n.data("type"));
      if (n.data("source")) badges.push("source=" + n.data("source"));
      setSelectionBadges(badges);

      const img = n.data("img");
      if (img) {{
        el("selImg").src = img;
      }} else {{
        el("selImg").src = "";
      }}
    }});

    cy.on("select", "edge", (evt) => {{
      const e = evt.target;
      el("selId").textContent = esc(e.data("id"));
      el("selLabel").textContent = esc(e.data("label"));
      el("selType").textContent = esc(e.data("etype"));
      el("selKind").textContent = esc(e.data("kind"));
      el("selSource").textContent = esc(e.data("source_pack"));
      el("selMeta").textContent = JSON.stringify({{
        source: e.data("source"),
        target: e.data("target"),
        weight: e.data("weight")
      }}, null, 2);
      setSelectionBadges([
        "edge",
        "kind=" + esc(e.data("kind")),
        "etype=" + esc(e.data("etype"))
      ]);
      el("selImg").src = "";
    }});

    cy.on("unselect", (evt) => {{
      const selected = cy.$(":selected");
      if (selected.length === 0) clearSelection();
    }});

    renderPills("nodeKindPills", nodeKinds, nodeKindState, applyFilters);
    renderPills("edgeKindPills", edgeKinds, edgeKindState, applyFilters);

    applyFilters();
    doLayout();

    // Deck: show card nodes
    function renderDeck() {{
      const deck = el("deck");
      deck.innerHTML = "";
      const cards = nodes
        .map(n => n.data)
        .filter(d => d.kind === "card" && d.img)
        .sort((a,b) => (a.label || "").localeCompare(b.label || ""));
      for (const c of cards) {{
        const tile = document.createElement("div");
        tile.className = "cardTile";
        const img = document.createElement("img");
        img.src = c.img;
        const ct = document.createElement("div");
        ct.className = "ct";
        ct.textContent = c.label || c.id;
        tile.appendChild(img);
        tile.appendChild(ct);
        tile.onclick = () => {{
          const n = cy.getElementById(c.id);
          cy.$(":selected").unselect();
          n.select();
          cy.center(n);
          cy.zoom({{ level: Math.max(1.2, cy.zoom()), position: n.position() }});
        }};
        deck.appendChild(tile);
      }}
    }}
    renderDeck();

    // Search
    const q = el("q");
    q.addEventListener("keydown", (ev) => {{
      if (ev.key === "Escape") {{
        q.value = "";
        cy.$(":selected").unselect();
        return;
      }}
      if (ev.key !== "Enter") return;
      const term = q.value.trim().toLowerCase();
      if (!term) return;
      const found = cy.nodes().filter(n => {{
        const id = (n.data("id") || "").toLowerCase();
        const lab = (n.data("label") || "").toLowerCase();
        const type = (n.data("type") || "").toLowerCase();
        const src = (n.data("source") || "").toLowerCase();
        return id.includes(term) || lab.includes(term) || type.includes(term) || src.includes(term);
      }});
      if (found.length > 0) {{
        const n = found[0];
        cy.$(":selected").unselect();
        n.select();
        cy.center(n);
        cy.zoom({{ level: 1.4, position: n.position() }});
      }}
    }});

    // Top buttons
    el("btnRelayout").onclick = () => doLayout();
    el("btnFit").onclick = () => cy.fit(cy.nodes(":visible"), 30);

    el("btnExportPng").onclick = () => {{
      const png = cy.png({{ output: "blob", bg: "#070a0f", full: true, scale: 2 }});
      const url = URL.createObjectURL(png);
      const a = document.createElement("a");
      a.href = url;
      a.download = "atlas.png";
      a.click();
      URL.revokeObjectURL(url);
    }};

    el("btnExportJson").onclick = () => {{
      const blob = new Blob([JSON.stringify(ATLAS, null, 2)], {{ type: "application/json" }});
      const url = URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = url;
      a.download = "atlas_data.json";
      a.click();
      URL.revokeObjectURL(url);
    }};

    el("btnToggleLabels").onclick = () => {{
      labelsOn = !labelsOn;
      cy.style().update();
    }};
  </script>
</body>
</html>
"""
    return html


def escape_html(s: str) -> str:
    return (s.replace("&", "&amp;")
             .replace("<", "&lt;")
             .replace(">", "&gt;")
             .replace('"', "&quot;")
             .replace("'", "&#39;"))


# -----------------------------
# Main build
# -----------------------------

def build_manifest(root: Path, out_json: Path, out_csv: Path, ledger: RunLedger) -> None:
    rows = []
    for p in sorted(root.rglob("*")):
        if p.is_dir():
            continue
        st = p.stat()
        rows.append({
            "relpath": str(p.relative_to(root)).replace("\\", "/"),
            "bytes": st.st_size,
            "mtime_utc": _dt.datetime.utcfromtimestamp(st.st_mtime).replace(microsecond=0).isoformat() + "Z",
        })
    manifest = {
        "generated_utc": now_utc_iso(),
        "digest_policy": sha1_not_allowed_note(),
        "files": rows
    }
    write_json(out_json, manifest)

    out_csv.parent.mkdir(parents=True, exist_ok=True)
    with out_csv.open("w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=["relpath", "bytes", "mtime_utc"])
        w.writeheader()
        for r in rows:
            w.writerow(r)

    ledger.log("manifest_written", files=len(rows), json=str(out_json), csv=str(out_csv))


def copy_inputs(inputs: List[Path], panels: List[Path], inputs_dir: Path, ledger: RunLedger) -> Dict[str, List[Path]]:
    safe_mkdir(inputs_dir)
    orig_dir = inputs_dir / "originals"
    safe_mkdir(orig_dir)
    copied_zips = []
    copied_panels = []
    for p in inputs:
        dst = orig_dir / p.name
        shutil.copy2(p, dst)
        copied_zips.append(dst)
    for p in panels:
        dst = orig_dir / p.name
        shutil.copy2(p, dst)
        copied_panels.append(dst)
    ledger.log("inputs_copied", zips=len(copied_zips), panels=len(copied_panels), dest=str(orig_dir))
    return {"zips": copied_zips, "panels": copied_panels}


def ingest_all(extracted_root: Path, ledger: RunLedger) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]], List[Dict[str, Any]]]:
    """
    Returns: nodes, edges, images (card candidates)
    nodes: {id,label,type,kind,source,meta,img?,pos?}
    edges: {id?,source,target,label,kind,etype,weight,source_pack}
    images: {path, pack, title}
    """
    nodes: List[Dict[str, Any]] = []
    edges: List[Dict[str, Any]] = []
    images: List[Dict[str, Any]] = []

    # Scan every file under extracted_root
    files = [p for p in extracted_root.rglob("*") if p.is_file()]
    ledger.log("extracted_scan", files=len(files), root=str(extracted_root))

    for p in files:
        # record card images
        if is_image_path(p):
            pack = p.relative_to(extracted_root).parts[0] if len(p.relative_to(extracted_root).parts) > 0 else "pack"
            images.append({"path": p, "pack": pack, "title": p.stem})
            continue

        # tables -> nodes/edges
        if is_table_path(p):
            headers, rows = read_table_rows(p, ledger)
            file_tag = slugify(str(p.relative_to(extracted_root)))
            for idx, r in enumerate(rows):
                if looks_like_edge_record(r):
                    s = pick_first(r, EDGE_SRC_KEYS) or ""
                    t = pick_first(r, EDGE_TGT_KEYS) or ""
                    if not s or not t:
                        continue
                    edges.append({
                        "id": stable_row_id(file_tag, idx),
                        "source": s,
                        "target": t,
                        "label": r.get("label", "") or r.get("etype", "") or "",
                        "kind": normalize_type(r.get("kind"), "edge"),
                        "etype": normalize_type(r.get("etype"), "rel"),
                        "weight": extract_weight(r),
                        "source_pack": str(p.relative_to(extracted_root)).replace("\\", "/")
                    })
                elif looks_like_node_record(r):
                    nid = pick_first(r, NODE_ID_KEYS) or stable_row_id(file_tag, idx)
                    lab = pick_first(r, NODE_LABEL_KEYS) or nid
                    ntype = r.get("type", "") or r.get("category", "") or "unknown"
                    nodes.append({
                        "id": str(nid),
                        "label": str(lab),
                        "type": normalize_type(str(ntype), "unknown"),
                        "kind": normalize_type(r.get("kind"), "node"),
                        "source": str(p.relative_to(extracted_root)).replace("\\", "/"),
                        "meta": r
                    })
            continue

        # json -> nodes/edges
        if is_json_path(p):
            items = read_json_items(p, ledger)
            file_tag = slugify(str(p.relative_to(extracted_root)))
            for idx, obj in enumerate(items):
                if isinstance(obj, dict) and looks_like_edge_record(obj):
                    s = pick_first(obj, EDGE_SRC_KEYS) or ""
                    t = pick_first(obj, EDGE_TGT_KEYS) or ""
                    if not s or not t:
                        continue
                    edges.append({
                        "id": str(obj.get("id") or stable_row_id(file_tag, idx)),
                        "source": str(s),
                        "target": str(t),
                        "label": str(obj.get("label") or obj.get("etype") or ""),
                        "kind": normalize_type(str(obj.get("kind") or ""), "edge"),
                        "etype": normalize_type(str(obj.get("etype") or ""), "rel"),
                        "weight": extract_weight(obj),
                        "source_pack": str(p.relative_to(extracted_root)).replace("\\", "/")
                    })
                elif isinstance(obj, dict) and looks_like_node_record(obj):
                    nid = str(obj.get("id") or obj.get("node_id") or stable_row_id(file_tag, idx))
                    lab = str(obj.get("label") or obj.get("name") or obj.get("title") or nid)
                    ntype = str(obj.get("type") or obj.get("category") or "unknown")
                    kind = str(obj.get("kind") or "node")
                    nodes.append({
                        "id": nid,
                        "label": lab,
                        "type": normalize_type(ntype, "unknown"),
                        "kind": normalize_type(kind, "node"),
                        "source": str(p.relative_to(extracted_root)).replace("\\", "/"),
                        "meta": obj
                    })
                else:
                    # raw line or unclassified object: wrap as node
                    nid = stable_row_id(file_tag, idx)
                    nodes.append({
                        "id": nid,
                        "label": nid,
                        "type": "unclassified",
                        "kind": "node",
                        "source": str(p.relative_to(extracted_root)).replace("\\", "/"),
                        "meta": {"raw": obj}
                    })
            continue

        # graphml/gexf optional ingest if networkx is present
        if is_graph_path(p):
            try:
                import networkx as nx  # optional
                g = None
                if p.suffix.lower() == ".graphml":
                    g = nx.read_graphml(str(p))
                elif p.suffix.lower() == ".gexf":
                    g = nx.read_gexf(str(p))
                if g is not None:
                    pack_src = str(p.relative_to(extracted_root)).replace("\\", "/")
                    for n, nd in g.nodes(data=True):
                        nid = str(nd.get("id") or n)
                        lab = str(nd.get("label") or nd.get("name") or n)
                        nodes.append({
                            "id": nid,
                            "label": lab,
                            "type": normalize_type(str(nd.get("type") or nd.get("category") or "graph_node"), "graph_node"),
                            "kind": normalize_type(str(nd.get("kind") or "node"), "node"),
                            "source": pack_src,
                            "meta": nd
                        })
                    for u, v, ed in g.edges(data=True):
                        edges.append({
                            "id": str(ed.get("id") or f"{slugify(pack_src)}:{u}->{v}"),
                            "source": str(u),
                            "target": str(v),
                            "label": str(ed.get("label") or ed.get("etype") or ""),
                            "kind": normalize_type(str(ed.get("kind") or "edge"), "edge"),
                            "etype": normalize_type(str(ed.get("etype") or "rel"), "rel"),
                            "weight": extract_weight(ed),
                            "source_pack": pack_src
                        })
                    ledger.log("graph_ingested", path=str(p), nodes=len(g.nodes()), edges=len(g.edges()))
            except Exception as e:
                ledger.log("graph_ingest_skip", path=str(p), error=str(e))
            continue

    # Deduplicate nodes by id (merge meta shallowly)
    dedup: Dict[str, Dict[str, Any]] = {}
    for n in nodes:
        nid = n["id"]
        if nid not in dedup:
            dedup[nid] = n
        else:
            # preserve earliest label/type/kind; merge meta keys without overwriting existing
            m = dedup[nid].get("meta", {})
            m2 = n.get("meta", {})
            if isinstance(m, dict) and isinstance(m2, dict):
                for k, v in m2.items():
                    if k not in m:
                        m[k] = v
                dedup[nid]["meta"] = m
    nodes = list(dedup.values())

    ledger.log("ingest_done", nodes=len(nodes), edges=len(edges), images=len(images))
    return nodes, edges, images


def attach_cards(nodes: List[Dict[str, Any]], images: List[Dict[str, Any]], assets_cards_dir: Path, extracted_root: Path, ledger: RunLedger) -> None:
    """
    Copy images into assets and create card nodes.
    """
    safe_mkdir(assets_cards_dir)
    for img in images:
        src: Path = img["path"]
        # deterministic destination name
        pack = slugify(str(img.get("pack", "pack")))
        name = slugify(src.stem) + src.suffix.lower()
        dst = assets_cards_dir / f"{pack}__{name}"
        if not dst.exists():
            shutil.copy2(src, dst)
        # create card node
        nid = f"card:{pack}:{slugify(src.stem, 80)}"
        nodes.append({
            "id": nid,
            "label": f"{img.get('title')}",
            "type": "card",
            "kind": "card",
            "source": rel_no_drive(src.relative_to(extracted_root)),
            "meta": {"pack": img.get("pack", ""), "original_name": src.name},
            "img": "../assets/cards/" + dst.name
        })
    ledger.log("cards_attached", card_nodes=len(images), assets_dir=str(assets_cards_dir))


def add_heuristic_links(nodes: List[Dict[str, Any]], edges: List[Dict[str, Any]], ledger: RunLedger, limit_per_card: int = 25) -> None:
    """
    Heuristic crosswire: match card filename tokens to node label tokens.
    All edges are labeled kind=heuristic.
    """
    # Build token index of non-card nodes
    label_index: List[Tuple[str, List[str], str]] = []
    for n in nodes:
        if n.get("kind") == "card":
            continue
        lab = str(n.get("label") or n.get("id") or "")
        toks = token_set(lab)
        if toks:
            label_index.append((n["id"], toks, lab))

    def score_overlap(a: List[str], b: List[str]) -> int:
        sb = set(b)
        return sum(1 for t in a if t in sb)

    card_nodes = [n for n in nodes if n.get("kind") == "card"]
    added = 0
    for cn in card_nodes:
        meta = cn.get("meta", {}) if isinstance(cn.get("meta"), dict) else {}
        label = str(cn.get("label") or "")
        original = str(meta.get("original_name") or "")
        tokens = token_set(" ".join([label, original]))
        if not tokens:
            continue
        scored: List[Tuple[int, str, str]] = []
        for nid, toks, lab in label_index:
            score = score_overlap(tokens, toks)
            if score > 0:
                scored.append((score, nid, lab))
        scored.sort(key=lambda x: (-x[0], x[1]))
        for score, target_id, target_label in scored[:limit_per_card]:
            edge_id = f"heuristic:{cn['id']}:{target_id}"
            edges.append({
                "id": edge_id,
                "source": cn["id"],
                "target": target_id,
                "label": f"overlap:{score}",
                "kind": "heuristic",
                "etype": "token_overlap",
                "weight": float(score),
                "source_pack": "heuristic"
            })
            added += 1
    ledger.log("heuristic_links_added", edges_added=added, cards=len(card_nodes))


def copy_panels(panels: List[Path], assets_panels_dir: Path, ledger: RunLedger) -> List[Dict[str, str]]:
    safe_mkdir(assets_panels_dir)
    panel_entries = []
    for idx, p in enumerate(panels):
        dst = assets_panels_dir / p.name
        if not dst.exists():
            shutil.copy2(p, dst)
        panel_entries.append({
            "src": "../assets/panels/" + dst.name,
            "title": p.stem
        })
    ledger.log("panels_copied", panels=len(panel_entries), dest=str(assets_panels_dir))
    return panel_entries


def parse_args(argv: Optional[List[str]] = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Build ONE massive static atlas (force-directed graph) from ZIP packs + panel images.",
        formatter_class=argparse.RawTextHelpFormatter
    )
    parser.add_argument("--outdir", required=True, help="Output directory (atlas build root)")
    parser.add_argument("--inputs", nargs="+", required=True, help="ZIP inputs (one or many)")
    parser.add_argument("--panels", nargs="*", default=[], help="Panel images to show in UI")
    parser.add_argument("--offline-libs", type=int, default=1, help="Download offline JS libs (1=on,0=off)")
    parser.add_argument("--heuristic-links", type=int, default=1, help="Enable heuristic card->node linking (1=on,0=off)")
    parser.add_argument("--dry-run", action="store_true", help="Plan only, do not write outputs")
    return parser.parse_args(argv)


def main(argv: Optional[List[str]] = None) -> int:
    args = parse_args(argv)

    outdir = Path(args.outdir).expanduser().resolve()
    inputs = [Path(p).expanduser() for p in args.inputs]
    panels = [Path(p).expanduser() for p in args.panels]

    ledger_path = outdir / "run_ledger.jsonl"
    ledger = RunLedger(ledger_path)
    ledger.log("start", args=vars(args))

    if args.dry_run:
        ledger.log("dry_run", message="dry run enabled; no outputs written")
        return 0

    atlas_dir = outdir / "atlas"
    assets_dir = outdir / "assets"
    assets_cards = assets_dir / "cards"
    assets_panels = assets_dir / "panels"
    inputs_dir = outdir / "inputs"
    extracted_root = inputs_dir / "extracted"
    vendor_dir = outdir / "vendor"

    safe_mkdir(atlas_dir)
    safe_mkdir(assets_dir)
    safe_mkdir(inputs_dir)
    safe_mkdir(extracted_root)

    # copy inputs/panels
    copied = copy_inputs(inputs, panels, inputs_dir, ledger)

    # extract zips to separate folders
    for zp in copied["zips"]:
        pack_dir = extracted_root / slugify(zp.stem)
        safe_mkdir(pack_dir)
        safe_extract_zip(zp, pack_dir, ledger)

    nodes, edges, images = ingest_all(extracted_root, ledger)
    attach_cards(nodes, images, assets_cards, extracted_root, ledger)
    panel_entries = copy_panels(copied["panels"], assets_panels, ledger)

    if args.heuristic_links:
        add_heuristic_links(nodes, edges, ledger)

    atlas_data = {
        "generated_utc": now_utc_iso(),
        "nodes": nodes,
        "edges": edges,
        "panels": panel_entries,
        "stats": {
            "nodes": len(nodes),
            "edges": len(edges),
            "cards": len([n for n in nodes if n.get("kind") == "card"]),
            "panels": len(panel_entries),
            "inputs": len(inputs)
        }
    }

    atlas_data_path = atlas_dir / "atlas_data.json"
    write_json(atlas_data_path, atlas_data)

    vendor_rel = "../vendor" if args.offline_libs else "https://cdn.jsdelivr.net/npm"
    if args.offline_libs:
        download_vendor_libs(vendor_dir, ledger)

    html = build_atlas_html(json.dumps(atlas_data, ensure_ascii=False), panel_entries, vendor_rel)
    atlas_html_path = atlas_dir / "atlas.html"
    write_text(atlas_html_path, html)
    ledger.log("atlas_written", html=str(atlas_html_path), data=str(atlas_data_path))

    # Manifest (no hashes)
    build_manifest(outdir, outdir / "manifest.json", outdir / "manifest.csv", ledger)
    ledger.log("done", outdir=str(outdir))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
