# Diagram Generation Blueprint (DRAFT) — NUCLEUS APEX V3.4

## External Tool: HFSPACE:dippatel1994/paperbanana
- URL: https://hf.co/spaces/dippatel1994/paperbanana
- Updated: 2026-02-05
- Tags: gradio, region:us

## Purpose
Generate **methodology diagrams** (pipeline blocks, ERD-style panels, flowcharts) from structured inputs (CSV/JSON/YAML).
Diagrams are **system artifacts** (not evidence) and should be watermark-labeled accordingly.

## Inputs
- bloom_toc_full.csv (TOC spine)
- graphml_kind_counts.csv / graphml_edge_type_counts.csv
- external_tool_nodes.csv / edges.csv (this cycle)
- any plane registries / schema registries

## Output artifacts
- SVG/PNG/PDF diagrams stored under run folder
- `diagram_manifest.csv` + `diagram_runlog.jsonl` with IntegrityKeys
