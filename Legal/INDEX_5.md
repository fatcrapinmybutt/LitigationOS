# LitigationOS_BLOOMPACK_APPENDONLY — INDEX (APPEND-ONLY)
Root folder name is stable. Each iteration appends a new `vYYYY.MM.DD_DELTA*` folder.

## DELTAS
|Folder|Purpose|Key entrypoints|
|---|---|---|
|`v2026.01.17_DELTA1/`|Mainframe kernel (MI-lock+PCW/ADD/PCG+hybrid retrieval) + memory prune plan|`MAINFRAME_KERNEL.md` • `MEMORY_PRUNE.md`|
|`v2026.01.17_DELTA2_GRAPH_INGEST/`|Merge your existing graph CSVs (base + NUCLEUS supergraph + rels + authority edges) into Neo4j Admin Import CSVs; include constraints/fulltext; include merged outputs|`CANONICAL_KERNEL_v2026_01_17/run_pipeline.py` • `tools/graph_merge.py` • `tools/neo4j_apply.py`|
|`v2026.01.17_DELTA3_PACKAGING_NEO4J_IMPORT/`|Resumable packaging (CyclePack: PART zips + index + join/verify) + full Neo4j offline import runbook automation (neo4j-admin full import + schema apply; 10-try retry)|`PACKAGER/pack_build.py` • `PACKAGER/pack_join.py` • `NEO4J_RUNBOOK/README.md`|

## CURRENT HARD BLOCKER SOLVED IN DELTA3
- **Resumable packaging**: parts can be rebuilt/reused safely after interruption.
- **Neo4j full import runbook**: deterministic `neo4j-admin database import full` + post-start schema apply with 10-try retries.
