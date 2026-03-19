# CHANGELOG — DELTA11

## Added
- `runtime/order_service_graph.py` (builds order/service graph payload)
- `runtime/evidence_coverage.py` (scores ExhibitMatrix vs EvidenceAtoms)
- `runtime/lineage_provenance_index.py` (joins lineage groups to replay provenance)
- `data/service_proofs.json` (seed service-proof records)
- `data/order_supersession_service_graph.json` (derived graph payload)
- `data/exhibit_matrix.json` and `data/evidence_atoms.json` (coverage scoring inputs)
- `data/evidence_coverage.json` (derived scoring output)
- `data/lineage_provenance_index.json` (derived lineage/provenance index)
- JSON Schemas for the new payloads
- Pydantic contracts for Delta11 payloads

## Updated
- `ui/panels.js`, `ui/app.js`, `ui/adapters.js`, `ui/styles.css`, `ui/index.html`
- `data/vehicle_readiness.json` (evidence_coverage_score added)
- `manifests/cycle_state.json`, `manifests/continuation_checkpoint.json`

## Notes
This append turns the command center into a linked procedural/proof/provenance surface rather than a static status dashboard.


- Δ12 continuation available: transcript quote-lock append (see `CHANGELOG_DELTA12.md`).
