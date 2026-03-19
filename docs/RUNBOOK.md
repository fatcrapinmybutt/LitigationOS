# RUNBOOK — Append Cycles

## 1) Refresh datasets
Replace or extend JSON under `data/`:
- timeline.json
- orders.json
- service_proofs.json
- exhibit_matrix.json
- evidence_atoms.json
- desktop_* corpus files
- replay_provenance_links.json
- authority / contradiction / deadlines / case_state

## 2) Recompute derived payloads
Run:
- `python runtime/order_service_graph.py`
- `python runtime/evidence_coverage.py`
- `python runtime/lineage_provenance_index.py`

## 3) Launch and review
Run `python runtime/launch.py` and review panel badges.
Panels stay visible even with partial datasets; use discovery targets/resolution targets as continuation rails.

## 4) Advance the next cycle
Update:
- `manifests/cycle_state.json`
- `manifests/continuation_checkpoint.json`
- `manifests/delta_patch_list.json`

## 5) Rebuild ZIP
Run `python scripts/rebuild_this_pack.py`


## Δ12 transcript quote-lock rail
Adds quote-lock target/link payloads and an interactive Quote-Lock panel for transcript/order pinpoint integration.
