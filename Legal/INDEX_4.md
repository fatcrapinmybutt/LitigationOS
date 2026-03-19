# Index — LitigationOS Blueprint Pack v2026-01-19.3 (ShortPaths)

## Start here
- `L3/LitigationOS_BLUEPRINT_README_v2026-01-19.3.md`
- Mapping file: `PATH_MAP.csv` (root)

## Dense schema (C2 superset catalogs)
- Field dictionary (dense, per entity): `L3/d/ERD_SUPERSET_FIELD_DICTIONARY_v2026-01-19.2.md`
- Field catalog (raw): `L3/mdl/fld.csv`
- Relationship catalog: `L3/mdl/rel.csv`
- Entity + relationship index: `L3/d/f_e836.md`

## C3 contract emission layer
- Deduped field catalog (PCG canonical): `L3/mdl/fld_dedup.csv`
- Entity JSON Schemas (Draft 2020-12): `L3/sch/entities/*.schema.json`
- Schema registry: `L3/sch/entities/_registry.json`

### Neo4j schema scripts
- Constraints: `L3/n4j/constraints.cy`
- Indexes (core): `L3/n4j/idx_core.cy`
- Indexes (aggressive): `L3/n4j/idx_aggr.cy`

### neo4j-admin import header templates
- Nodes: `L3/tpl/nodes/*_header.csv`
- Relationships: `L3/tpl/rels/_RELATIONSHIPS_MASTER_HEADER.csv` plus additional `*.csv`

### Harvest + validation reports
- CSV header harvest from selected uploaded ZIPs: `L3/d/f_83e6.md`
- Validation (DRAFT): `L3/vr/val_draft.md`
- Validation (PCG): `L3/vr/val_pcg.md`
- Dedupe report: `L3/vr/field_catalog_dedupe_report.md`

## Build + restartability
- Build plan: `L3/d/BUILDPLAN_BOTTOM_TO_TOP_v2026-01-19.2.md`
- SavePoint protocol: `L3/d/SAVEPOINT_PROTOCOL_v2026-01-19.2.md`
- Graph contracts: `L3/d/GRAPH_CONTRACTS_v2026-01-19.2.md`
- SavePoint C3: `L3/sp/C3/savepoint_C3_finalization.json`

## Diagrams
- Superset overview: `L3/g/erd_superset_overview_sfdp.png`
- Domain cards: `L3/g/erd_superset_cards_*.png`

## Tools
- C3 generator: `L3/tl/c3_generate_all.py`
- Bundle builder: `L3/tl/bundle_builder_v2026-01-19.3.py`
- Diagram generator: `L3/tl/make_diagrams.py`
