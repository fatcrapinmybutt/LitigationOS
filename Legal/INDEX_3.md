# Index — LitigationOS Blueprint Pack v2026-01-19.3

## Start here
- `LitigationOS_BLUEPRINT_README_v2026-01-19.3.md`

## Dense schema (C2 superset catalogs)
- `docs/ERD_SUPERSET_FIELD_DICTIONARY_v2026-01-19.2.md`
- `model/field_catalog_superset.csv`
- `model/relationship_catalog_superset.csv`
- `docs/ENTITY_RELATIONSHIP_SUPERSET_INDEX_v2026-01-19.2.md`

## C3 contract emission layer
- Deduped field catalog (PCG canonical): `model/field_catalog_superset_dedup.csv`
- Entity JSON Schemas (Draft 2020-12): `schemas/entities/*.schema.json`
- Schema registry: `schemas/entities/_registry.json`
- Neo4j schema scripts:
  - `neo4j/schema_constraints.cypher`
  - `neo4j/schema_indexes_core.cypher`
  - `neo4j/schema_indexes_aggressive.cypher`
- neo4j-admin import templates:
  - Nodes: `templates/neo4j_admin_import/nodes/*_header.csv`
  - Rels: `templates/neo4j_admin_import/rels/*_header.csv`
- Header harvest (uploaded ZIP cyclepacks): `docs/CSV_HEADER_HARVEST_FROM_UPLOADED_ZIPS_v2026-01-19.3.md`
- Validation reports:
  - DRAFT: `validation_reports/validate_all_DRAFT.md`
  - PCG: `validation_reports/validate_all_PCG.md`
  - Dedupe: `validation_reports/field_catalog_dedupe_report.md`

## Build + restartability
- Build plan: `docs/BUILDPLAN_BOTTOM_TO_TOP_v2026-01-19.2.md`
- SavePoint protocol: `docs/SAVEPOINT_PROTOCOL_v2026-01-19.2.md`
- Graph contracts: `docs/GRAPH_CONTRACTS_v2026-01-19.2.md`
- SavePoint C3: `savepoints/C3/savepoint_C3_finalization.json`

## Diagrams
- `diagrams/erd_superset_overview_sfdp.png` (full overview)
- `diagrams/erd_superset_cards_*.png` (domain slices)

## Tools
- C3 generator: `tools/c3_generate_all.py`
- Bundle builder: `tools/bundle_builder_v2026-01-19.3.py`
- Diagram generator: `tools/make_diagrams.py`
