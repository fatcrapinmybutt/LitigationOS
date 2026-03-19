# DELTA11 Append Notes — Orders / Evidence / Lineage

## What was appended
This cycle adds three command-center rails directly into the local HTML runtime:

1. **Order supersession graph + service-proof linkage**
   - `data/service_proofs.json`
   - `data/order_supersession_service_graph.json`
   - `runtime/order_service_graph.py`
   - UI panel upgraded to visualize order nodes, service-proof nodes, supersession edges, and service links.

2. **Evidence coverage scoring (ExhibitMatrix / EvidenceAtoms)**
   - `data/exhibit_matrix.json`
   - `data/evidence_atoms.json`
   - `data/evidence_coverage.json`
   - `runtime/evidence_coverage.py`
   - `vehicle_readiness.json` patched with `evidence_coverage_score`.

3. **Interactive lineage filters + provenance jump links**
   - `data/lineage_provenance_index.json`
   - `runtime/lineage_provenance_index.py`
   - Lineage panel now supports search/filter (class/ext/provenance kind) and jump anchors into replay provenance rows.

## Why this matters
The command center now bridges **procedural control** (orders + service) to **proof coverage** (evidence atoms) and then to **artifact-level provenance** (lineage + replay links). That gives you a usable triad for:
- challenge timing/notice defects,
- score proof completeness before drafting vehicles,
- jump straight to corpus artifacts that generated a given record event.

## Continuation targets (next delta)
- Transcript pinpoints grafted into order graph edges and evidence atoms (`page:line` anchors).
- Service-proof confidence scoring and supersession validity checks (e.g., unresolved chain gaps).
- Lineage provenance mini-preview (first quote / text snippet) in UI hover cards.
- Docket delta watcher for live sync into timeline + deadlines.
