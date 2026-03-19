# LitigationOS Graph Contracts (GraphIR) — v2026-01-19.2

## Why contracts exist
GraphIR contracts ensure that every import pack, validator, and compiler stage agrees on:
- node labels/types
- relationship types
- required properties
- property types
- ID strategy and uniqueness

This prevents silent drift as you add more entity families.

## Contract artifacts in this cycle pack
### 1) CSV catalogs (human and machine)
- `model/field_catalog_superset.csv` — every entity field (type, required, origin)
- `model/relationship_catalog_superset.csv` — every relationship (from/to, cardinality, notes)
- `model/entity_index.csv` — entity counts + grouping
- `model/rel_index.csv` — relationship counts

### 2) JSON Schemas (machine validation)
Place JSON Schemas under `schemas/jsonschema/` (recommended structure):
- `schemas/jsonschema/nodes/<Entity>.schema.json`
- `schemas/jsonschema/rels/<RelType>.schema.json`

Each schema should validate a CSV row after parsing and normalization.

### 3) Validator CLI
Minimum validator behavior:
- parse CSV with strict header enforcement
- validate required columns
- validate types (`string`, `int`, `float`, `bool`, `date`, `datetime`, `json`)
- validate ID columns and referential integrity (`start_id` / `end_id` exist)
- emit:
  - `validation_reports/graphir_validation.json`
  - `validation_reports/graphir_validation.md`

## Neo4j import contract notes
### ID columns
Use a *single global ID* strategy:
- `node_id` for all nodes
- `start_id` / `end_id` for all relationships

If you need local ID spaces (same numeric IDs across different files), use Neo4j import “ID spaces”.

### Headers
Neo4j bulk import expects:
- node files: `id:ID,<props...>,:LABEL` or `:LABEL` via `--nodes=Label=...`
- relationship files: `:START_ID,:END_ID,:TYPE,<props...>` or `--relationships=TYPE=...`

## Bloom perspective pack
A Bloom perspective pack should include:
- label styling presets
- relationship styling
- saved queries (cypher) for:
  - Case spine
  - Orders/Service/Deadlines
  - PCW obligations
  - Authority graph and proposition chains

## Recommended “contracts first” workflow
1) Update catalogs (`field_catalog_superset.csv`, `relationship_catalog_superset.csv`).
2) Rebuild JSON Schemas from catalogs.
3) Run validator on emitted GraphIR CSVs.
4) Only after validation passes, run Neo4j import.
5) Export/import Bloom perspective.

## Fail-soft vs fail-closed
- DISCOVERY / BUILD phases: validator may be fail-soft and emit a blocker list.
- PCG boundary: validator must be fail-closed for any node/rel that would be referenced in a filing packet.
