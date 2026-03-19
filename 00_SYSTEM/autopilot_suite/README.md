# LitigationOS Autopilot Suite v1.0.0

This bundle contains:

- `outputs/LitigationOS_AUTOPILOT_OUT_20260208/` — the **already-built** graph pack from your uploaded attachments:
  - `neo4j_nodes_core.csv`
  - `neo4j_edges_core.csv`
  - `node_props.jsonl.gz`
  - `edge_props.jsonl.gz`
  - `graph_core.graphml` (Gephi-ready)
  - `bloom_perspective.json` + `bloom_queries.cypher`
  - `neo4j_constraints.cypher`
  - `graph_contract.yml`
  - `action_report.md`
  - `pdf_extracts/` + `pdf_extract_index.json`
  - `manifest.json` + `run_ledger.jsonl` + `violations.json`

- `scripts/litigationos_autopilot.py` — the **compiler runtime** (CLI) that can ingest:
  - directories
  - individual CSV/PDF/JSONL/TXT inputs
  - ZIP bundles (auto-extracts)
  and then emit the same outputs again (idempotent).

## 1) Import into Neo4j (Desktop)

Use `neo4j-admin database import full` (Neo4j 5+) with the core CSVs:

- Nodes: `neo4j_nodes_core.csv`
- Relationships: `neo4j_edges_core.csv`

Then run:

- `neo4j_constraints.cypher`

## 2) Open in Gephi

Open:

- `graph_core.graphml`

## 3) Bloom

Load the dataset in Neo4j, then run `bloom_queries.cypher` to seed perspectives.
Use `bloom_perspective.json` as the metadata reference.

## 4) Re-run / recompile locally (Windows)

```powershell
python -m venv .venv
.\.venv\Scripts\pip.exe install -r requirements.txt

.\.venv\Scripts\python.exe scripts\litigationos_autopilot.py ^
  --inputs "C:\Users\andre\Desktop\THE_LITIGATION_OPERATING_SYSTEM" ^
  --out-dir "C:\Users\andre\Desktop\THE_LITIGATION_OPERATING_SYSTEM\AUTOPILOT_OUT" ^
  --emit-graphml --pdf-extract --emit-bloom --emit-action-report
```

## OCR (optional / fail-soft)

If you have `tesseract.exe`, you can pass either the exe path **or a directory** containing it:

```powershell
.\.venv\Scripts\python.exe scripts\litigationos_autopilot.py --tesseract "C:\Users\andre\Downloads\tesseract-main" ...
```

If OCR dependencies are missing, the run stays **fail-soft** and will still extract embedded text.

## Build a one-click EXE (optional)

See: `scripts/build_exe.ps1`
