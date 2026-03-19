# MEEK2 + MEEK3 + MEEK4 — Full Stack Rebuild (v2026-02-08_2)

This pack is a **corrected + expanded** rebuild of the baseline MEEK234 pipeline with:

- **Fixed keyword ellipses bug** (baseline contained truncated strings like `p...support` that reduced detection accuracy).
- **Catalog-first architecture**: risks / vehicles / schema are external JSON/CSV catalogs (still has embedded fallbacks).
- **Operating Order Pin enforcement**: every VehicleCandidate attempts to pin an Operating Order; missing pins generate RiskEvents.
- **Clerk-letter / notice ingestion** as first-class events (return/reject/defect/notice).
- **XLSX ingestion** (openpyxl read-only) and better structured readers.
- **Convergence loop**: multiple deterministic passes until the **graph digest** stabilizes (or max passes).

## Quickstart

### Windows (PowerShell)
```powershell
python .\MEEK234_FULLSTACK_REBUILD_v20260208_2.py --intake "C:\Users\andre\Desktop\THE_LITIGATION_OPERATING_SYSTEM\LITIGATION_INTAKE" --out ".\out_meek234" --make-cyclepack
```

### Linux / WSL
```bash
python3 MEEK234_FULLSTACK_REBUILD_v20260208_2.py --intake "/path/to/LITIGATION_INTAKE" --out "./out_meek234" --make-cyclepack
```

## Outputs (final pass)
- `manifest.csv` + `manifest.json` (document inventory + IntegrityKey)
- `evidence_atoms.jsonl`
- `events.jsonl`
- `clocks.jsonl`
- `risk_events.jsonl`
- `vehicle_candidates.jsonl`
- `graph_nodes.csv` / `graph_edges.csv` (Neo4j import friendly)
- `index.html` (clickable dashboard)
- `convergence_log.jsonl` (pass-by-pass digests + deltas)
- Optional: `cyclepack_<run_id>.zip` (all outputs + catalogs)

## Catalogs
- `catalogs/risk_event_types.json`
- `catalogs/vehicle_types.json`
- `schema/node_types.csv`, `schema/edge_types.csv`, `schema/property_specs.csv`, `schema/enum_specs.csv`

## Notes
- This is **DRAFT/fail-soft**: it produces usable artifacts even with missing pieces, but it also emits explicit RiskEvents for gaps.
- For **FILE_READY/PCG** grade packaging, extend the Packager stage (planned) to require service/record completeness gates.
