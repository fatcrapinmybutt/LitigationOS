# Quickstart Runbook (v2)

## 0) Put bundle somewhere stable
Example: `D:\LitigationOS\bundles\LITIGATIONOS_MASTER_ALLINONE_BUNDLE_v2\`

## 1) Initialize stable paths
Run:
- `py scripts\litigationos.py init-config --home D:\LitigationOS`
- `setx LITIGATIONOS_HOME "D:\LitigationOS"`

## 2) Harvest cycle (optional)
From the bundle folder:
- `py scripts\litigationos.py harvest --paths-file drivesANDpaths.txt --out D:\LitigationOS\HarvestOut --pdf-extract --unzip`

## 3) Merge cycle CSVs into datastore
Example:
- `py scripts\litigationos.py merge --import-index D:\LitigationOS\HarvestOut\MASTER_LEGAL_TEXT_INDEX.csv --out-db D:\LitigationOS\Datastore\authority_shards_fts.sqlite --build-fts --build-neighbors`

## 4) Query (GraphRAG chain)
- `py scripts\litigationos.py query --fts D:\LitigationOS\Datastore\authority_shards_fts.sqlite --neighbors D:\LitigationOS\Datastore\authority_neighbors_adj.json --query "MCR 2.003 disqualification standard" --out-md D:\LitigationOS\QueryOut\result.md`

Notes:
- If a required input path is missing, use the scripts' `--help` and the bundle's `reports/` inventories.
- For Michigan-only authority lock and fail-closed pinpoints: follow `concepts/SUPERPIN_MASTER_CANONICAL.md`.
Build UTC: 2026-01-07T23:17:30.540905
