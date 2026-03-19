# WarChest v8 — QuickStart

## What this adds (beyond v7)
- A **registry of official Michigan primary sources** (`sources/official_sources.yaml`)
- A **snapshot harvester** (`tools/harvest_official_sources.py`) that downloads those sources with SHA-256 logs
- A **build step** (`tools/build_authority_index.py`) that creates:
  - `out/authority_atoms.jsonl`
  - `out/authority_index.sqlite`
- A **crosswire linker** (`tools/crosswire_evidence_against_authority.py`) that scans your evidence/text and connects citations back to the authority atoms.

## Minimal run
1. Create a snapshot:
   - Windows: `RUN_ALL.cmd` (or run the python commands directly)
   - Mac/Linux: `bash RUN_ALL.sh`
2. Build the authority index:
   - `python tools/build_authority_index.py --snapshot data/official/<TIMESTAMP> --out out`
3. Crosswire your evidence:
   - `python tools/crosswire_evidence_against_authority.py --db out/authority_index.sqlite --roots inputs out`

## Outputs you care about
- `out/authority_sources.csv` — canonical registry
- `out/authority_index.sqlite` — queryable index
- `out/crosswire_hits.csv` — all citation hits across your evidence corpus

## Licensing / reproduction note
Some sources (especially Administrative Code) may include reproduction limits. The tools default to **personal use snapshotting** and are intended for litigation/research, not resale.
