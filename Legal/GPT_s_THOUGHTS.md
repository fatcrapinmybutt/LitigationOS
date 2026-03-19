Activity
· 22m 30s
Thinking
Preparing C2 pack update and schema generation

We need to locate the existing C2 zip, unzip it, and add new files and outputs, then rezip it. I'll generate and add schema files using the correct JSON draft version, based on the field catalog in the C2 pack. For CSV headers, I plan to extract them without fully decompressing the zips. Additionally, I’ll create the necessary Python scripts and neo4j schema. Lastly, we’ll decide on the primary key for each entity, likely based on the ID field.
Determining primary key and creating import templates

I need to compute candidates for primary keys by looking for fields named after the entity with _id, or any _id field with a pk flag. I'll inspect the field catalog for is_pk and check for robust implementation. I'll also prepare templates for importing into Neo4j, ensuring proper header formats and relationship details as required.
Considering Bloom perspective export and documentation

We can’t invent the exact format for Bloom, but we could generate a canonical structure. Bloom exports are in JSON, though not officially formalized. We might extract example data from the user's existing files or search for a "bloom" folder within the C2 pack. I’ll add relevant documentation and verify all data paths are correctly set, ensuring everything is responsive in the environment.
Planning search queries and file handling for the user

I'll run several tailored searches focused on Neo4j, CSV imports, Cypher constraints, Bloom exports, JSON schema, and BagIt. Afterward, I'll prepare the work directory, unzip the C2 pack and generate the necessary scripts. I'll execute these scripts, capture validation outputs, and create a savepoint. Finally, I'll zip everything and provide the download link along with citations.
Creating Bloom perspective parsing tool and schemas

While Bloom exports are in JSON, we can't provide a concrete example due to the version-specific structure. Instead, I’ll include a runbook with a script (bloom_perspective_normalizer.py) to parse and normalize any Bloom perspective export. I'll also handle schema generation from the field catalog and ensure an appropriate primary key logic. Additionally, I'll create entity schemas and avoid placeholders or dummy data. The scripts will ensure everything is automated and deterministic.
Implementing validation and schema generation for Neo4j

For validation, I'll enforce strict schema checks with additionalProperties: false to disallow extra fields while keeping flexibility based on mode. In DRAFT mode, I'll allow additional properties to make validation fail-soft. For Neo4j schema generation, I'll create constraints on primary keys and indices on certain fields, making sure the process is idempotent. I'll also craft templates for nodes and relationships with suggested headers for easy customization and follow the right format for labels.
Finalizing templates and packaging setup

I'll generate relationship templates based on the catalog, grouping by relationship type and endpoints. It might be a bit large, but manageable. For the final deliverable, I'll include a builder script that reconstructs everything locally, along with a README to guide the user. Along with the zip package, I'll add a changelog and other relevant files.
Finalizing and Packaging C3 with Neo4j Schema
Additional queries for documentation

I realized I also need the Neo4j-admin import docs and the 2020-12 JSON Schema. Our earlier query missed those, so I'll need to try another search to gather the missing documentation for Neo4j imports and the latest JSON Schema version.
Searching for neo4j import docs and JSON Schema 2020-12
Searching for BagIt source and RFC 8493

I noticed that the search didn’t return the BagIt source, even though we asked for it. I’ll need to do another quick search for RFC 8493 to gather the missing information on BagIt—hopefully, this will bring up what we need.
Searching for BagIt specification and Neo4j documentation
Building the pack and inspecting C2 contents

Alright, the citations are ready. Next, I need to build the pack, so I’ll use container.exec for that. But before jumping in, I think it’s a good idea to inspect the C2 zip contents first to make sure everything is in order before proceeding.
Inspecting C2 zip contents

Always show details
bash -lc ls -lh /mnt/data | sed -n '1,200p'

total 359M
-rw-r--r-- 1 root root       1.8M Jan 20 04:34 Branch · Branch · Superpin Prompt for Legal Analysis-5.pdf
-rw-r--r-- 1 root root       132M Jan 20 04:34 COURT RULES.zip
-rw-r--r-- 1 root root        15M Jan 20 04:33 ETERNAL_GRAPH_BUNDLE_MASTER_LOCKED.zip
-rw-r--r-- 1 root root       113M Jan 20 04:34 EVIDENCE.zip
-rw-r--r-- 1 root root       1.9M Jan 20 04:33 EternalCodex_Complete.zip
-rw-r--r-- 1 root root       1.6M Jan 20 04:34 Graph Steps Validation Compilation-2.pdf
-rw-r--r-- 1 root root        22M Jan 20 04:33 LITIGATIONOS_AUTHORITY_GRAPH_MERGE_GRAPHRAG_CYCLEPACK_20260107_164708.zip
-rw-r--r-- 1 root root        22M Jan 20 04:33 LITIGATIONOS_STATEMENT_FACT_PROV_AUTH_CYCLEPACK_20260107_181048.zip
-rw-r--r-- 1 root root        36M Jan 20 04:34 LITIGATIONOS__MASTERv1.0__v0009__FULL(2).zip
-rw-r--r-- 1 root root        85K Jan 20 04:34 Litigation Os 12-run Blueprint V2026-01-19.pdf
-rw-r--r-- 1 root root        46K Jan 20 04:34 LitigationOS_Architecture_Map_100pct_v2026-01-19.13(1).md
-rw-r--r-- 1 root root        12K Jan 20 04:33 LitigationOS_BLUEPRINT_README_v2026-01-19.1.md
-rw-r--r-- 1 root root       212K Jan 20 04:34 LitigationOS_Blueprint_Pack_v2026-01-19.1.zip
-rw-r--r-- 1 root root        14M Jan 20 04:33 LitigationOS_Blueprint_Pack_v2026-01-19.2.zip
-rw-r--r-- 1 root root       186K Jan 20 04:34 LitigationOS_IntegratedLauncher_BucketOrchestrator_v2026-01-18.22_console_orchestrator_cyclepack_parallel(2).zip
-rw-r--r-- 1 root root       1.6M Jan 20 04:34 LitigationOS_Module_Addendum_Pack_v2026-01-19(2).zip
-rw-r--r-- 1 root root        72K Jan 20 04:34 LitigationOS_Pipeline_Stages_Ceiling_GodLevel_v2026-01-19.7(1).md
drwxr-xr-x 2 root root         80 Jan 20 04:15 _work_c3
-rw-r--r-- 1 root root       376K Jan 20 04:34 complete-model-v3.13.4c12f7e373d3.png
-rw-r--r-- 1 root root       126K Jan 20 04:33 core_erd_v2026-01-19.1.png
-rw-r--r-- 1 root root        94K Jan 20 04:34 pipeline_v2026-01-19.1.png
-rw-r--r-- 1 root root       162K Jan 20 04:34 spec_card_schema_bloom_ALL_items_v3.md
drwxr-xr-x 2 root oai_shared   80 Jan 20 04:14 user-6Fa13uiZSyuXYIsS3JHGzxpF

Inspecting _work_c3 contents

Looks like _work_c3 is already present from my previous response. I should take a closer look at it to make sure everything’s in order before proceeding. It’s good to double-check and confirm it’s what I need to continue, rather than moving on too quickly.
Inspecting files in _work_c3

Always show details
bash -lc find /mnt/data/_work_c3 -maxdepth 3 -type f | sed -n '1,200p'

/mnt/data/_work_c3/LitigationOS_Blueprint_Pack_v2026-01-19.2/diagrams/core_erd_v2026-01-19.1.dot
/mnt/data/_work_c3/LitigationOS_Blueprint_Pack_v2026-01-19.2/diagrams/core_erd_v2026-01-19.1.png
/mnt/data/_work_c3/LitigationOS_Blueprint_Pack_v2026-01-19.2/diagrams/core_erd_v2026-01-19.1.svg
/mnt/data/_work_c3/LitigationOS_Blueprint_Pack_v2026-01-19.2/diagrams/pipeline_v2026-01-19.1.dot
/mnt/data/_work_c3/LitigationOS_Blueprint_Pack_v2026-01-19.2/diagrams/pipeline_v2026-01-19.1.png
/mnt/data/_work_c3/LitigationOS_Blueprint_Pack_v2026-01-19.2/diagrams/pipeline_v2026-01-19.1.svg
/mnt/data/_work_c3/LitigationOS_Blueprint_Pack_v2026-01-19.2/diagrams/erd_superset_cards_authority.dot
/mnt/data/_work_c3/LitigationOS_Blueprint_Pack_v2026-01-19.2/diagrams/erd_superset_cards_authority.png
/mnt/data/_work_c3/LitigationOS_Blueprint_Pack_v2026-01-19.2/diagrams/erd_superset_cards_authority.svg
/mnt/data/_work_c3/LitigationOS_Blueprint_Pack_v2026-01-19.2/diagrams/erd_superset_cards_automation.dot
/mnt/data/_work_c3/LitigationOS_Blueprint_Pack_v2026-01-19.2/diagrams/erd_superset_cards_automation.png
/mnt/data/_work_c3/LitigationOS_Blueprint_Pack_v2026-01-19.2/diagrams/erd_superset_cards_automation.svg
/mnt/data/_work_c3/LitigationOS_Blueprint_Pack_v2026-01-19.2/diagrams/erd_superset_cards_evidence.dot
/mnt/data/_work_c3/LitigationOS_Blueprint_Pack_v2026-01-19.2/diagrams/erd_superset_cards_evidence.png
/mnt/data/_work_c3/LitigationOS_Blueprint_Pack_v2026-01-19.2/diagrams/erd_superset_cards_evidence.svg
/mnt/data/_work_c3/LitigationOS_Blueprint_Pack_v2026-01-19.2/diagrams/erd_superset_cards_interop.dot
/mnt/data/_work_c3/LitigationOS_Blueprint_Pack_v2026-01-19.2/diagrams/erd_superset_cards_interop.png
/mnt/data/_work_c3/LitigationOS_Blueprint_Pack_v2026-01-19.2/diagrams/erd_superset_cards_interop.svg
/mnt/data/_work_c3/LitigationOS_Blueprint_Pack_v2026-01-19.2/diagrams/erd_superset_cards_other.dot
/mnt/data/_work_c3/LitigationOS_Blueprint_Pack_v2026-01-19.2/diagrams/erd_superset_cards_other.png
/mnt/data/_work_c3/LitigationOS_Blueprint_Pack_v2026-01-19.2/diagrams/erd_superset_cards_other.svg
/mnt/data/_work_c3/LitigationOS_Blueprint_Pack_v2026-01-19.2/diagrams/erd_superset_cards_packaging.dot
/mnt/data/_work_c3/LitigationOS_Blueprint_Pack_v2026-01-19.2/diagrams/erd_superset_cards_packaging.png
/mnt/data/_work_c3/LitigationOS_Blueprint_Pack_v2026-01-19.2/diagrams/erd_superset_cards_packaging.svg
/mnt/data/_work_c3/LitigationOS_Blueprint_Pack_v2026-01-19.2/diagrams/erd_superset_cards_procedure.dot
/mnt/data/_work_c3/LitigationOS_Blueprint_Pack_v2026-01-19.2/diagrams/erd_superset_cards_procedure.png
/mnt/data/_work_c3/LitigationOS_Blueprint_Pack_v2026-01-19.2/diagrams/erd_superset_cards_procedure.svg
/mnt/data/_work_c3/LitigationOS_Blueprint_Pack_v2026-01-19.2/diagrams/erd_superset_cards_service.dot
/mnt/data/_work_c3/LitigationOS_Blueprint_Pack_v2026-01-19.2/diagrams/erd_superset_cards_service.png
/mnt/data/_work_c3/LitigationOS_Blueprint_Pack_v2026-01-19.2/diagrams/erd_superset_cards_service.svg
/mnt/data/_work_c3/LitigationOS_Blueprint_Pack_v2026-01-19.2/diagrams/erd_superset_overview.dot
/mnt/data/_work_c3/LitigationOS_Blueprint_Pack_v2026-01-19.2/diagrams/erd_superset_overview.svg
/mnt/data/_work_c3/LitigationOS_Blueprint_Pack_v2026-01-19.2/diagrams/erd_superset_overview_sfdp.png
/mnt/data/_work_c3/LitigationOS_Blueprint_Pack_v2026-01-19.2/diagrams/erd_superset_overview_sfdp.svg
/mnt/data/_work_c3/LitigationOS_Blueprint_Pack_v2026-01-19.2/docs/BUILDPLAN_BOTTOM_TO_TOP_v2026-01-19.2.md
/mnt/data/_work_c3/LitigationOS_Blueprint_Pack_v2026-01-19.2/docs/ENTITY_RELATIONSHIP_SUPERSET_INDEX_v2026-01-19.2.md
/mnt/data/_work_c3/LitigationOS_Blueprint_Pack_v2026-01-19.2/docs/ERD_SUPERSET_FIELD_DICTIONARY_v2026-01-19.2.md
/mnt/data/_work_c3/LitigationOS_Blueprint_Pack_v2026-01-19.2/docs/GRAPH_CONTRACTS_v2026-01-19.2.md
/mnt/data/_work_c3/LitigationOS_Blueprint_Pack_v2026-01-19.2/docs/SAVEPOINT_PROTOCOL_v2026-01-19.2.md
/mnt/data/_work_c3/LitigationOS_Blueprint_Pack_v2026-01-19.2/model/entity_index.csv
/mnt/data/_work_c3/LitigationOS_Blueprint_Pack_v2026-01-19.2/model/field_catalog_superset.csv
/mnt/data/_work_c3/LitigationOS_Blueprint_Pack_v2026-01-19.2/model/rel_index.csv
/mnt/data/_work_c3/LitigationOS_Blueprint_Pack_v2026-01-19.2/model/relationship_catalog_superset.csv
/mnt/data/_work_c3/LitigationOS_Blueprint_Pack_v2026-01-19.2/tools/make_diagrams.bat
/mnt/data/_work_c3/LitigationOS_Blueprint_Pack_v2026-01-19.2/tools/make_diagrams.py
/mnt/data/_work_c3/LitigationOS_Blueprint_Pack_v2026-01-19.2/tools/make_diagrams.sh
/mnt/data/_work_c3/LitigationOS_Blueprint_Pack_v2026-01-19.2/tools/bundle_builder_v2026-01-19.2.py
/mnt/data/_work_c3/LitigationOS_Blueprint_Pack_v2026-01-19.2/tools/extract_fields.py
/mnt/data/_work_c3/LitigationOS_Blueprint_Pack_v2026-01-19.2/tools/generate_superset.py
/mnt/data/_work_c3/LitigationOS_Blueprint_Pack_v2026-01-19.2/tools/generate_entity_rel_index.py
/mnt/data/_work_c3/LitigationOS_Blueprint_Pack_v2026-01-19.2/LitigationOS_BLUEPRINT_README_v2026-01-19.2.md
/mnt/data/_work_c3/LitigationOS_Blueprint_Pack_v2026-01-19.2/LitigationOS_BLUEPRINT_README_v2026-01-19.1.md
/mnt/data/_work_c3/LitigationOS_Blueprint_Pack_v2026-01-19.2/INDEX.md
/mnt/data/_work_c3/LitigationOS_Blueprint_Pack_v2026-01-19.3/diagrams/core_erd_v2026-01-19.1.dot
/mnt/data/_work_c3/LitigationOS_Blueprint_Pack_v2026-01-19.3/diagrams/core_erd_v2026-01-19.1.png
/mnt/data/_work_c3/LitigationOS_Blueprint_Pack_v2026-01-19.3/diagrams/core_erd_v2026-01-19.1.svg
/mnt/data/_work_c3/LitigationOS_Blueprint_Pack_v2026-01-19.3/diagrams/pipeline_v2026-01-19.1.dot
/mnt/data/_work_c3/LitigationOS_Blueprint_Pack_v2026-01-19.3/diagrams/pipeline_v2026-01-19.1.png
/mnt/data/_work_c3/LitigationOS_Blueprint_Pack_v2026-01-19.3/diagrams/pipeline_v2026-01-19.1.svg
/mnt/data/_work_c3/LitigationOS_Blueprint_Pack_v2026-01-19.3/diagrams/erd_superset_cards_authority.dot
/mnt/data/_work_c3/LitigationOS_Blueprint_Pack_v2026-01-19.3/diagrams/erd_superset_cards_authority.png
/mnt/data/_work_c3/LitigationOS_Blueprint_Pack_v2026-01-19.3/diagrams/erd_superset_cards_authority.svg
/mnt/data/_work_c3/LitigationOS_Blueprint_Pack_v2026-01-19.3/diagrams/erd_superset_cards_automation.dot
/mnt/data/_work_c3/LitigationOS_Blueprint_Pack_v2026-01-19.3/diagrams/erd_superset_cards_automation.png
/mnt/data/_work_c3/LitigationOS_Blueprint_Pack_v2026-01-19.3/diagrams/erd_superset_cards_automation.svg
/mnt/data/_work_c3/LitigationOS_Blueprint_Pack_v2026-01-19.3/diagrams/erd_superset_cards_evidence.dot
/mnt/data/_work_c3/LitigationOS_Blueprint_Pack_v2026-01-19.3/diagrams/erd_superset_cards_evidence.png
/mnt/data/_work_c3/LitigationOS_Blueprint_Pack_v2026-01-19.3/diagrams/erd_superset_cards_evidence.svg
/mnt/data/_work_c3/LitigationOS_Blueprint_Pack_v2026-01-19.3/diagrams/erd_superset_cards_interop.dot
/mnt/data/_work_c3/LitigationOS_Blueprint_Pack_v2026-01-19.3/diagrams/erd_superset_cards_interop.png
/mnt/data/_work_c3/LitigationOS_Blueprint_Pack_v2026-01-19.3/diagrams/erd_superset_cards_interop.svg
/mnt/data/_work_c3/LitigationOS_Blueprint_Pack_v2026-01-19.3/diagrams/erd_superset_cards_other.dot
/mnt/data/_work_c3/LitigationOS_Blueprint_Pack_v2026-01-19.3/diagrams/erd_superset_cards_other.png
/mnt/data/_work_c3/LitigationOS_Blueprint_Pack_v2026-01-19.3/diagrams/erd_superset_cards_other.svg
/mnt/data/_work_c3/LitigationOS_Blueprint_Pack_v2026-01-19.3/diagrams/erd_superset_cards_packaging.dot
/mnt/data/_work_c3/LitigationOS_Blueprint_Pack_v2026-01-19.3/diagrams/erd_superset_cards_packaging.png
/mnt/data/_work_c3/LitigationOS_Blueprint_Pack_v2026-01-19.3/diagrams/erd_superset_cards_packaging.svg
/mnt/data/_work_c3/LitigationOS_Blueprint_Pack_v2026-01-19.3/diagrams/erd_superset_cards_procedure.dot
/mnt/data/_work_c3/LitigationOS_Blueprint_Pack_v2026-01-19.3/diagrams/erd_superset_cards_procedure.png
/mnt/data/_work_c3/LitigationOS_Blueprint_Pack_v2026-01-19.3/diagrams/erd_superset_cards_procedure.svg
/mnt/data/_work_c3/LitigationOS_Blueprint_Pack_v2026-01-19.3/diagrams/erd_superset_cards_service.dot
/mnt/data/_work_c3/LitigationOS_Blueprint_Pack_v2026-01-19.3/diagrams/erd_superset_cards_service.png
/mnt/data/_work_c3/LitigationOS_Blueprint_Pack_v2026-01-19.3/diagrams/erd_superset_cards_service.svg
/mnt/data/_work_c3/LitigationOS_Blueprint_Pack_v2026-01-19.3/diagrams/erd_superset_overview.dot
/mnt/data/_work_c3/LitigationOS_Blueprint_Pack_v2026-01-19.3/diagrams/erd_superset_overview.svg
/mnt/data/_work_c3/LitigationOS_Blueprint_Pack_v2026-01-19.3/diagrams/erd_superset_overview_sfdp.png
/mnt/data/_work_c3/LitigationOS_Blueprint_Pack_v2026-01-19.3/diagrams/erd_superset_overview_sfdp.svg
/mnt/data/_work_c3/LitigationOS_Blueprint_Pack_v2026-01-19.3/docs/BUILDPLAN_BOTTOM_TO_TOP_v2026-01-19.2.md
/mnt/data/_work_c3/LitigationOS_Blueprint_Pack_v2026-01-19.3/docs/ENTITY_RELATIONSHIP_SUPERSET_INDEX_v2026-01-19.2.md
/mnt/data/_work_c3/LitigationOS_Blueprint_Pack_v2026-01-19.3/docs/ERD_SUPERSET_FIELD_DICTIONARY_v2026-01-19.2.md
/mnt/data/_work_c3/LitigationOS_Blueprint_Pack_v2026-01-19.3/docs/GRAPH_CONTRACTS_v2026-01-19.2.md
/mnt/data/_work_c3/LitigationOS_Blueprint_Pack_v2026-01-19.3/docs/SAVEPOINT_PROTOCOL_v2026-01-19.2.md
/mnt/data/_work_c3/LitigationOS_Blueprint_Pack_v2026-01-19.3/model/entity_index.csv
/mnt/data/_work_c3/LitigationOS_Blueprint_Pack_v2026-01-19.3/model/field_catalog_superset.csv
/mnt/data/_work_c3/LitigationOS_Blueprint_Pack_v2026-01-19.3/model/rel_index.csv
/mnt/data/_work_c3/LitigationOS_Blueprint_Pack_v2026-01-19.3/model/relationship_catalog_superset.csv
/mnt/data/_work_c3/LitigationOS_Blueprint_Pack_v2026-01-19.3/tools/make_diagrams.bat
/mnt/data/_work_c3/LitigationOS_Blueprint_Pack_v2026-01-19.3/tools/make_diagrams.py
/mnt/data/_work_c3/LitigationOS_Blueprint_Pack_v2026-01-19.3/tools/make_diagrams.sh
/mnt/data/_work_c3/LitigationOS_Blueprint_Pack_v2026-01-19.3/tools/bundle_builder_v2026-01-19.2.py
/mnt/data/_work_c3/LitigationOS_Blueprint_Pack_v2026-01-19.3/tools/extract_fields.py
/mnt/data/_work_c3/LitigationOS_Blueprint_Pack_v2026-01-19.3/tools/generate_superset.py
/mnt/data/_work_c3/LitigationOS_Blueprint_Pack_v2026-01-19.3/tools/generate_entity_rel_index.py
/mnt/data/_work_c3/LitigationOS_Blueprint_Pack_v2026-01-19.3/tools/schema_emit.py
/mnt/data/_work_c3/LitigationOS_Blueprint_Pack_v2026-01-19.3/tools/generate_neo4j_schema.py
/mnt/data/_work_c3/LitigationOS_Blueprint_Pack_v2026-01-19.3/tools/generate_graphir_templates.py
/mnt/data/_work_c3/LitigationOS_Blueprint_Pack_v2026-01-19.3/tools/validate_all.py
/mnt/data/_work_c3/LitigationOS_Blueprint_Pack_v2026-01-19.3/tools/harvest_csv_headers.py
/mnt/data/_work_c3/LitigationOS_Blueprint_Pack_v2026-01-19.3/LitigationOS_BLUEPRINT_README_v2026-01-19.2.md
/mnt/data/_work_c3/LitigationOS_Blueprint_Pack_v2026-01-19.3/LitigationOS_BLUEPRINT_README_v2026-01-19.1.md
/mnt/data/_work_c3/LitigationOS_Blueprint_Pack_v2026-01-19.3/INDEX.md

Preparing for packaging step

I see there’s already a folder named v2026-01-19.3 in the workspace with new scripts. However, the user wants the packaging step now. It seems like the zip file hasn’t been created yet in /mnt/data, so I’ll check that and make sure it’s ready for delivery. Let’s double-check!
Checking for existing folder and zip

Always show details
bash -lc ls -lh /mnt/data | grep 'v2026-01-19.3' || true

Preparing folder for packaging

It looks like there’s no zip file yet. I’ll need to package the v2026-01-19.3 folder into a zip file, and then update the documentation. The folder in _work_c3 seems ready, but we should validate and make sure the scripts have been run. I'll check the README in 3 and inspect the guidelines for docs.
Inspecting README content

Always show details
bash -lc sed -n '1,200p' /mnt/data/_work_c3/LitigationOS_Blueprint_Pack_v2026-01-19.3/LitigationOS_BLUEPRINT_README_v2026-01-19.2.md

# LitigationOS — Bottom→Top Blueprint + Build README (C2) (v2026-01-19.2)
Build stamp (local): 2026-01-20

## What this deliverable is
This cycle (C2) is an **append-only expansion** of your prior blueprint pack (v2026-01-19.1). It adds:
- a **schema superset** (dense entity field dictionaries + relationship catalog)
- a **restartable SavePoint protocol** for infinite chained cycles
- a **diagram set** that renders like your attached ERD screenshot (overview + domain “cards”)

## Where to look first (fast index)
### A) Schema superset (your “extremely dense field lists per entity”)
- `litos_dense_build/outpack/docs/ERD_SUPERSET_FIELD_DICTIONARY_v2026-01-19.2.md`
- `litos_dense_build/outpack/model/field_catalog_superset.csv`
- `litos_dense_build/outpack/model/relationship_catalog_superset.csv`
- `litos_dense_build/outpack/docs/ENTITY_RELATIONSHIP_SUPERSET_INDEX_v2026-01-19.2.md`

### B) Bottom→top build plan (granular step-by-step)
- `litos_dense_build/outpack/docs/BUILDPLAN_BOTTOM_TO_TOP_v2026-01-19.2.md`

### C) Infinite chained cycles (restartability)
- `litos_dense_build/outpack/docs/SAVEPOINT_PROTOCOL_v2026-01-19.2.md`

### D) Graph contracts and Neo4j import notes
- `litos_dense_build/outpack/docs/GRAPH_CONTRACTS_v2026-01-19.2.md`

### E) Diagrams (ERD-style “photo” deliverable)
- Full overview: `litos_dense_build/outpack/diagrams/erd_superset_overview_sfdp.png`
- Domain cards: `litos_dense_build/outpack/diagrams/erd_superset_cards_*.png`

## High-level model (bottom → top)
LitigationOS is a deterministic, append-only **evidence/authority → graph → proof-carrying gate → draft factory → filing packet** system.

### The spine
1) **Storage** (runs + immutable sources)
2) **Artifact spine** (every file becomes an Artifact row)
3) **Extraction** (text/OCR + anchors)
4) **Atoms** (Evidence/Authority/Order/Service/Docket/Quote)
5) **GraphIR** (contracts + Neo4j import packs)
6) **PCW/PO overlay** (proof obligations + acquisition tasks)
7) **Compilation** (timelines, matrices, contradiction maps, authority triples)
8) **Draft factory** (vehicle-first, trace-mapped)
9) **Packet/binder** (exhibits + manifest + service chain)
10) **PCG** (irreversible boundary pass/fail)

## What “C2” specifically adds
### 1) Max-density entity field lists
The superset dictionary is intentionally expansive to avoid schema churn later. Use it as:
- a **canonical field lexicon** for your relational store
- a **contract generator input** for GraphIR node/rel schemas
- a **coverage checklist** for ingestion/extraction modules

### 2) Max relationships
The relationship catalog includes:
- procedural chains (docket→filing→order→service→deadline)
- authority chains (snapshot→authority→pinpoint→proposition→test)
- proof chains (vehicle→PO→pins→gate results)
- compilation outputs (timeline nodes, matrices, contradiction edges)

### 3) Restartability
Every stage emits a SavePoint directory containing:
- checkpoint JSON
- event log slice
- counts
- exact resume instructions

This is what enables infinite chained cycles without losing determinism.

## How to use this pack
1) Read the **build plan** and decide which stage you are implementing next.
2) Use the **field/relationship catalogs** as your source of truth for schema and GraphIR.
3) Use the **cards** diagrams to work in slices, and the **overview** diagram for the full map.
4) Adopt the **SavePoint protocol** now, before adding more modules, to avoid rework.

## Known constraints
- The overview diagram is extremely dense and large; it is rendered with Graphviz `sfdp` to keep it legible at scale.
- The schema superset is intentionally broader than any single immediate use-case; pruning is allowed only at a *consumer layer*, not in the canonical catalogs.

Updating README and ensuring correct paths

The README is still labeled C2, so it needs to be updated for C3 with the latest additions. Also, there's an incorrect reference to litos_dense_build/outpack/..., which was from a previous packaging. The files are actually in the same folder and should follow the updated path. I’ll rewrite the README and index carefully to fix this. Let’s take a close look at the folder.
Inspecting directory for README update

Always show details
bash -lc ls -R /mnt/data/_work_c3/LitigationOS_Blueprint_Pack_v2026-01-19.3 | head -n 200

/mnt/data/_work_c3/LitigationOS_Blueprint_Pack_v2026-01-19.3:
INDEX.md
LitigationOS_BLUEPRINT_README_v2026-01-19.1.md
LitigationOS_BLUEPRINT_README_v2026-01-19.2.md
bloom
diagrams
docs
model
neo4j
savepoints
schemas
templates
tools

/mnt/data/_work_c3/LitigationOS_Blueprint_Pack_v2026-01-19.3/bloom:
perspectives

/mnt/data/_work_c3/LitigationOS_Blueprint_Pack_v2026-01-19.3/bloom/perspectives:

/mnt/data/_work_c3/LitigationOS_Blueprint_Pack_v2026-01-19.3/diagrams:
core_erd_v2026-01-19.1.dot
core_erd_v2026-01-19.1.png
core_erd_v2026-01-19.1.svg
erd_superset_cards_authority.dot
erd_superset_cards_authority.png
erd_superset_cards_authority.svg
erd_superset_cards_automation.dot
erd_superset_cards_automation.png
erd_superset_cards_automation.svg
erd_superset_cards_evidence.dot
erd_superset_cards_evidence.png
erd_superset_cards_evidence.svg
erd_superset_cards_interop.dot
erd_superset_cards_interop.png
erd_superset_cards_interop.svg
erd_superset_cards_other.dot
erd_superset_cards_other.png
erd_superset_cards_other.svg
erd_superset_cards_packaging.dot
erd_superset_cards_packaging.png
erd_superset_cards_packaging.svg
erd_superset_cards_procedure.dot
erd_superset_cards_procedure.png
erd_superset_cards_procedure.svg
erd_superset_cards_service.dot
erd_superset_cards_service.png
erd_superset_cards_service.svg
erd_superset_overview.dot
erd_superset_overview.svg
erd_superset_overview_sfdp.png
erd_superset_overview_sfdp.svg
pipeline_v2026-01-19.1.dot
pipeline_v2026-01-19.1.png
pipeline_v2026-01-19.1.svg

/mnt/data/_work_c3/LitigationOS_Blueprint_Pack_v2026-01-19.3/docs:
BUILDPLAN_BOTTOM_TO_TOP_v2026-01-19.2.md
ENTITY_RELATIONSHIP_SUPERSET_INDEX_v2026-01-19.2.md
ERD_SUPERSET_FIELD_DICTIONARY_v2026-01-19.2.md
GRAPH_CONTRACTS_v2026-01-19.2.md
SAVEPOINT_PROTOCOL_v2026-01-19.2.md

/mnt/data/_work_c3/LitigationOS_Blueprint_Pack_v2026-01-19.3/model:
entity_index.csv
field_catalog_superset.csv
rel_index.csv
relationship_catalog_superset.csv

/mnt/data/_work_c3/LitigationOS_Blueprint_Pack_v2026-01-19.3/neo4j:

/mnt/data/_work_c3/LitigationOS_Blueprint_Pack_v2026-01-19.3/savepoints:
example

/mnt/data/_work_c3/LitigationOS_Blueprint_Pack_v2026-01-19.3/savepoints/example:
savepoint_C2_schema_superset.json

/mnt/data/_work_c3/LitigationOS_Blueprint_Pack_v2026-01-19.3/schemas:
entities

/mnt/data/_work_c3/LitigationOS_Blueprint_Pack_v2026-01-19.3/schemas/entities:

/mnt/data/_work_c3/LitigationOS_Blueprint_Pack_v2026-01-19.3/templates:
neo4j_admin_import

/mnt/data/_work_c3/LitigationOS_Blueprint_Pack_v2026-01-19.3/templates/neo4j_admin_import:
nodes
rels

/mnt/data/_work_c3/LitigationOS_Blueprint_Pack_v2026-01-19.3/templates/neo4j_admin_import/nodes:

/mnt/data/_work_c3/LitigationOS_Blueprint_Pack_v2026-01-19.3/templates/neo4j_admin_import/rels:

/mnt/data/_work_c3/LitigationOS_Blueprint_Pack_v2026-01-19.3/tools:
bundle_builder_v2026-01-19.2.py
extract_fields.py
generate_entity_rel_index.py
generate_graphir_templates.py
generate_neo4j_schema.py
generate_superset.py
harvest_csv_headers.py
make_diagrams.bat
make_diagrams.py
make_diagrams.sh
schema_emit.py
validate_all.py

Checking directories and running necessary scripts

Some directories are empty, like schemas/entities and templates, likely because the scripts haven’t been run yet. I need to run a series of scripts like schema_emit, generate_neo4j_schema, generate_graphir_templates, and others to generate the missing outputs. There's a C2 savepoint example, but for C3, I need a new one. Let's check the scripts, starting with schema_emit.
Opening schema_emit script for review

Always show details
bash -lc sed -n '1,220p' /mnt/data/_work_c3/LitigationOS_Blueprint_Pack_v2026-01-19.3/tools/schema_emit.py

#!/usr/bin/env python3
"""LitigationOS — Entity JSON Schema Emitter (Draft 2020-12)

Goal
  Convert the dense field catalog into per-entity JSON Schemas that can be used as
  machine-checkable Graph Contracts.

Inputs
  - model/field_catalog_superset.csv

Outputs
  - schemas/entities/<Entity>.schema.json
  - schemas/entities/_registry.json

Design constraints
  - Deterministic: same input catalog => same output schemas.
  - Conservative typing: prefer allowing nulls; treat unknowns as strings.
  - Truth-lock aligned: any inference is recorded in x-litos metadata.

Usage
  python tools/schema_emit.py \
    --field-catalog model/field_catalog_superset.csv \
    --out-dir schemas/entities
"""

from __future__ import annotations

import argparse
import csv
import json
import os
import re
from collections import defaultdict


def _read_csv(path: str) -> list[dict[str, str]]:
    with open(path, "r", encoding="utf-8", newline="") as f:
        reader = csv.DictReader(f)
        return [dict(r) for r in reader]


def _slug(s: str) -> str:
    return re.sub(r"[^A-Za-z0-9_]+", "_", s).strip("_")


def _jsonschema_for_type(dtype: str) -> dict:
    t = (dtype or "").strip().lower()

    # Core scalar types
    if t in {"string", "text", "path", "filename", "uri", "url", "email", "hostname", "ip"}:
        sch = {"type": ["string", "null"]}
        if t in {"uri", "url"}:
            sch["format"] = "uri"
        if t == "email":
            sch["format"] = "email"
        return sch

    if t in {"int", "integer", "int64", "int32", "count", "bytes"}:
        return {"type": ["integer", "null"]}

    if t in {"float", "number", "double", "decimal"}:
        return {"type": ["number", "null"]}

    if t in {"bool", "boolean"}:
        return {"type": ["boolean", "null"]}

    # Date/time
    if t in {"datetime_rfc3339", "datetime", "date_time"}:
        return {"type": ["string", "null"], "format": "date-time"}

    if t in {"date_rfc3339", "date"}:
        return {"type": ["string", "null"], "format": "date"}

    # Identifiers
    if t == "uuid":
        return {"type": ["string", "null"], "format": "uuid"}

    if t == "ulid":
        # ULID canonical: 26 Crockford Base32 chars. Pattern is strict; we keep it advisory.
        return {
            "type": ["string", "null"],
            "pattern": "^[0-9A-HJKMNP-TV-Z]{26}$",
            "x-litos": {"pattern_basis": "crockford_base32_ulid"},
        }

    if t == "sha256":
        return {"type": ["string", "null"], "pattern": "^[a-fA-F0-9]{64}$"}

    if t == "crc32":
        return {"type": ["string", "null"], "pattern": "^[a-fA-F0-9]{8}$"}

    # Structured payloads
    if t in {"json", "json_object", "object"}:
        return {"type": ["object", "null"], "additionalProperties": True}

    if t in {"json_array", "array"}:
        return {"type": ["array", "null"], "items": {}}

    if t in {"list_string", "string_list"}:
        return {
            "type": ["array", "null"],
            "items": {"type": "string"},
            "x-litos": {"csv_representation": "delimited_string_or_json_array"},
        }

    if t == "enum":
        return {"type": ["string", "null"], "x-litos": {"enum": "candidates_not_enforced"}}

    # Fallback
    return {"type": ["string", "null"], "x-litos": {"dtype_fallback": True, "original": dtype}}


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--field-catalog", required=True)
    ap.add_argument("--out-dir", required=True)
    args = ap.parse_args()

    rows = _read_csv(args.field_catalog)
    by_entity: dict[str, list[dict[str, str]]] = defaultdict(list)
    for r in rows:
        ent = (r.get("entity") or "").strip()
        if not ent:
            continue
        by_entity[ent].append(r)

    os.makedirs(args.out_dir, exist_ok=True)

    registry = {
        "schema_version": "2020-12",
        "count_entities": len(by_entity),
        "entities": [],
    }

    for ent in sorted(by_entity.keys()):
        props = {}
        required = []
        fields = sorted(by_entity[ent], key=lambda x: (int(x.get("order") or 10_000), x.get("field") or ""))
        for f in fields:
            name = (f.get("field") or "").strip()
            if not name:
                continue
            dtype = (f.get("dtype") or "string").strip()
            notes = (f.get("notes") or "").strip()
            req = (f.get("required") or "").strip().upper() == "Y"

            sch = _jsonschema_for_type(dtype)
            if notes:
                sch["description"] = notes
            sch.setdefault("x-litos", {})
            sch["x-litos"].update({
                "dtype": dtype,
                "required": req,
                "source": "field_catalog_superset.csv",
            })

            props[name] = sch
            if req:
                required.append(name)

        schema = {
            "$schema": "https://json-schema.org/draft/2020-12/schema",
            "$id": f"litos://schemas/entities/{_slug(ent)}.schema.json",
            "title": f"LitigationOS Entity Row: {ent}",
            "type": "object",
            "additionalProperties": False,
            "properties": props,
            "required": sorted(set(required)),
            "x-litos": {
                "entity": ent,
                "generated_by": "tools/schema_emit.py",
            },
        }

        out_path = os.path.join(args.out_dir, f"{_slug(ent)}.schema.json")
        with open(out_path, "w", encoding="utf-8") as f:
            json.dump(schema, f, indent=2, sort_keys=True)
            f.write("\n")

        registry["entities"].append({"entity": ent, "schema": os.path.basename(out_path)})

    reg_path = os.path.join(args.out_dir, "_registry.json")
    with open(reg_path, "w", encoding="utf-8") as f:
        json.dump(registry, f, indent=2, sort_keys=True)
        f.write("\n")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())

Checking field catalog and running schema generation

The current process looks good, but it's not inferring primary keys and similar fields since it uses required ones. Our field catalog might not include all the required fields, but that’s still fine for now. Next, I need to run the scripts to generate schemas and the registry, starting with generate_graphir_templates.py.
Generating schemas and registry

Always show details
bash -lc sed -n '1,260p' /mnt/data/_work_c3/LitigationOS_Blueprint_Pack_v2026-01-19.3/tools/generate_graphir_templates.py

#!/usr/bin/env python3
"""LitigationOS — GraphIR / neo4j-admin import template generator.

Purpose:
  Emit CSV header files for nodes and relationships used by neo4j-admin database import.

Writes:
  - templates/neo4j_admin_import/nodes/<Entity>_header.csv
  - templates/neo4j_admin_import/rels/<REL_TYPE>_header.csv

Notes:
  - 1 label per entity.
  - 1 relationship type per relationship catalog row.
  - Type hints are conservative; you can refine property typing later.

Usage:
  python tools/generate_graphir_templates.py \
    --field-catalog model/field_catalog_superset.csv \
    --rel-catalog model/relationship_catalog_superset.csv \
    --out-dir templates/neo4j_admin_import
"""

from __future__ import annotations

import argparse
import csv
import os
from collections import defaultdict


def _read_rows(path: str) -> list[dict]:
    with open(path, "r", encoding="utf-8", newline="") as f:
        return list(csv.DictReader(f))


def _pick_pk(entity: str, rows: list[dict]) -> str | None:
    # Prefer explicit pk note
    for r in rows:
        notes = (r.get("notes") or "").lower()
        if "primary key" in notes:
            return (r.get("field") or "").strip() or None
    # Fall back to <entity_lower>_id
    candidate = f"{entity.lower()}_id"
    for r in rows:
        if (r.get("field") or "").strip() == candidate:
            return candidate
    # Else any required _id
    for r in rows:
        if (r.get("required") or "").strip().upper() == "Y":
            f = (r.get("field") or "").strip()
            if f.endswith("_id"):
                return f
    return None


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--field-catalog", required=True)
    ap.add_argument("--rel-catalog", required=True)
    ap.add_argument("--out-dir", required=True)
    args = ap.parse_args()

    field_rows = _read_rows(args.field_catalog)
    rel_rows = _read_rows(args.rel_catalog)

    by_entity: dict[str, list[dict]] = defaultdict(list)
    for r in field_rows:
        ent = (r.get("entity") or "").strip()
        if ent:
            by_entity[ent].append(r)

    nodes_dir = os.path.join(args.out_dir, "nodes")
    rels_dir = os.path.join(args.out_dir, "rels")
    os.makedirs(nodes_dir, exist_ok=True)
    os.makedirs(rels_dir, exist_ok=True)

    # Nodes
    for entity, rows in sorted(by_entity.items()):
        pk = _pick_pk(entity, rows)
        if not pk:
            continue
        cols = [f"{pk}:ID", ":LABEL"]
        # include other fields as string properties (CSV import will coerce where possible)
        for r in rows:
            field = (r.get("field") or "").strip()
            if not field or field == pk:
                continue
            cols.append(field)

        header_path = os.path.join(nodes_dir, f"{entity}_header.csv")
        with open(header_path, "w", encoding="utf-8", newline="") as f:
            f.write(",".join(cols) + "\n")

    # Relationships
    for r in rel_rows:
        rel_type = (r.get("rel_name") or "").strip()
        if not rel_type:
            continue
        from_entity = (r.get("from_entity") or "").strip()
        to_entity = (r.get("to_entity") or "").strip()
        start_pk = _pick_pk(from_entity, by_entity.get(from_entity, []))
        end_pk = _pick_pk(to_entity, by_entity.get(to_entity, []))
        if not start_pk or not end_pk:
            continue
        header_path = os.path.join(rels_dir, f"{rel_type}_header.csv")
        cols = [":START_ID", ":END_ID", ":TYPE"]
        with open(header_path, "w", encoding="utf-8", newline="") as f:
            f.write(",".join(cols) + "\n")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())

Proceeding with schema generation

Now, I'll focus on generate_neo4j_schema.py to proceed with generating the schema. This will help ensure that everything is structured correctly for the database and ready for further steps. I'll double-check it to confirm that it's aligned with what needs to be done.
Extracting Neo4j schema generation code

Always show details
bash -lc sed -n '1,320p' /mnt/data/_work_c3/LitigationOS_Blueprint_Pack_v2026-01-19.3/tools/generate_neo4j_schema.py

#!/usr/bin/env python3
"""LitigationOS — Generate Neo4j constraints/indexes scripts from the schema catalogs.

Outputs:
  neo4j/schema_constraints.cypher
  neo4j/schema_indexes.cypher
  neo4j/schema_enterprise_optional.cypher (commented Enterprise-only constraints)

Selection logic for primary keys:
  1) Prefer fields whose notes include 'Primary key'.
  2) Else, prefer <entity_lower>_id.
  3) Else, first required Y field ending with _id.

Usage:
  python tools/generate_neo4j_schema.py --field-catalog model/field_catalog_superset.csv --out-dir neo4j
"""

from __future__ import annotations

import argparse
import csv
import os
from collections import defaultdict


def _read_rows(path: str) -> list[dict]:
    with open(path, "r", encoding="utf-8", newline="") as f:
        return list(csv.DictReader(f))


def _pick_pk(entity: str, rows: list[dict]) -> str | None:
    # 1) notes include primary key
    for r in rows:
        notes = (r.get("notes") or "").lower()
        if "primary key" in notes:
            return (r.get("field") or "").strip() or None
    # 2) <entity_lower>_id
    candidate = f"{entity.lower()}_id"
    for r in rows:
        if (r.get("field") or "").strip() == candidate:
            return candidate
    # 3) first required Y ending with _id
    for r in rows:
        if (r.get("required") or "").strip().upper() == "Y":
            f = (r.get("field") or "").strip()
            if f.endswith("_id"):
                return f
    return None


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--field-catalog", required=True)
    ap.add_argument("--out-dir", required=True)
    args = ap.parse_args()

    rows = _read_rows(args.field_catalog)
    by_entity: dict[str, list[dict]] = defaultdict(list)
    for r in rows:
        entity = (r.get("entity") or "").strip()
        if entity:
            by_entity[entity].append(r)

    os.makedirs(args.out_dir, exist_ok=True)
    constraints_path = os.path.join(args.out_dir, "schema_constraints.cypher")
    indexes_path = os.path.join(args.out_dir, "schema_indexes.cypher")
    enterprise_path = os.path.join(args.out_dir, "schema_enterprise_optional.cypher")

    # Constraints (community-safe)
    with open(constraints_path, "w", encoding="utf-8") as f:
        f.write("// LitigationOS Neo4j schema — constraints (Neo4j 5+ Cypher)\n")
        f.write("// Generated by tools/generate_neo4j_schema.py\n\n")
        for entity in sorted(by_entity.keys()):
            pk = _pick_pk(entity, by_entity[entity])
            if not pk:
                continue
            cname = f"uniq_{entity}_{pk}".replace("-", "_")
            f.write(f"CREATE CONSTRAINT {cname} IF NOT EXISTS FOR (n:`{entity}`) REQUIRE n.`{pk}` IS UNIQUE;\n")

    # Indexes
    with open(indexes_path, "w", encoding="utf-8") as f:
        f.write("// LitigationOS Neo4j schema — indexes (Neo4j 5+ Cypher)\n")
        f.write("// Generated by tools/generate_neo4j_schema.py\n\n")
        for entity in sorted(by_entity.keys()):
            rows_e = by_entity[entity]
            # index common query fields
            common = []
            for r in rows_e:
                field = (r.get("field") or "").strip()
                if not field:
                    continue
                if field in {"run_id", "case_id", "artifact_id", "source_id", "authority_id", "evidence_id", "docket_id", "order_id", "deadline_id", "person_id", "party_id"}:
                    common.append(field)
            seen = set()
            for field in common:
                key = (entity, field)
                if key in seen:
                    continue
                seen.add(key)
                iname = f"idx_{entity}_{field}".replace("-", "_")
                f.write(f"CREATE INDEX {iname} IF NOT EXISTS FOR (n:`{entity}`) ON (n.`{field}`);\n")

    # Optional Enterprise-only constraints (existence)
    with open(enterprise_path, "w", encoding="utf-8") as f:
        f.write("// LitigationOS Neo4j schema — Enterprise-only optional constraints\n")
        f.write("// These are commented out by default. Enable only if you have Enterprise Edition and you want stricter guarantees.\n\n")
        for entity in sorted(by_entity.keys()):
            pk = _pick_pk(entity, by_entity[entity])
            if pk:
                cname = f"x_req_{entity}_{pk}".replace("-", "_")
                f.write(f"// CREATE CONSTRAINT {cname} IF NOT EXISTS FOR (n:`{entity}`) REQUIRE n.`{pk}` IS NOT NULL;\n")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())

Proceeding with validation

Next up is validate_all.py. I'll run it to make sure everything is in check—ensuring there aren't any discrepancies or missing elements. It's important to confirm that everything is aligned and validated before moving ahead. Let's double-check everything is fully validated and ready.
Extracting lines from validate_all.py

Always show details
bash -lc sed -n '1,340p' /mnt/data/_work_c3/LitigationOS_Blueprint_Pack_v2026-01-19.3/tools/validate_all.py

#!/usr/bin/env python3
"""LitigationOS — Validator (DRAFT fail-soft / PCG fail-closed)

Validates internal consistency of:
  - model/field_catalog_superset.csv
  - model/relationship_catalog_superset.csv
  - schemas/entities/*.schema.json (optional)
  - templates/neo4j_admin_import/nodes/*_header.csv and templates/neo4j_admin_import/rels/*_header.csv (optional)

Modes:
  - DRAFT: collect errors, exit 0 (unless --strict)
  - PCG:   fail-closed; any error => exit non-zero

This validator is dependency-free (no external pip installs required).

Usage:
  python tools/validate_all.py --base . --mode DRAFT
  python tools/validate_all.py --base . --mode PCG

Exit codes:
  0 = OK or fail-soft conditions met
  2 = Validation failures in PCG (or DRAFT+--strict)
"""

from __future__ import annotations

import argparse
import csv
import json
import os
from dataclasses import dataclass


@dataclass
class Issue:
    severity: str  # ERROR|WARN
    where: str
    msg: str


def _read_csv(path: str) -> list[dict]:
    with open(path, "r", encoding="utf-8", newline="") as f:
        return list(csv.DictReader(f))


def _list_files(root: str, suffix: str) -> list[str]:
    out: list[str] = []
    for dp, _, fns in os.walk(root):
        for fn in fns:
            if fn.lower().endswith(suffix.lower()):
                out.append(os.path.join(dp, fn))
    return sorted(out)


def validate_model(base: str, issues: list[Issue]) -> None:
    fc = os.path.join(base, "model", "field_catalog_superset.csv")
    rc = os.path.join(base, "model", "relationship_catalog_superset.csv")

    if not os.path.exists(fc):
        issues.append(Issue("ERROR", "model", f"Missing {fc}"))
        return
    if not os.path.exists(rc):
        issues.append(Issue("ERROR", "model", f"Missing {rc}"))
        return

    frows = _read_csv(fc)
    rrows = _read_csv(rc)

    entities = set((r.get("entity") or "").strip() for r in frows if (r.get("entity") or "").strip())
    if not entities:
        issues.append(Issue("ERROR", "field_catalog", "No entities found"))

    # field uniqueness within entity
    seen = set()
    for r in frows:
        e = (r.get("entity") or "").strip()
        f = (r.get("field") or "").strip()
        if not e or not f:
            continue
        key = (e, f)
        if key in seen:
            issues.append(Issue("ERROR", "field_catalog", f"Duplicate field {e}.{f}"))
        seen.add(key)

    # relationship endpoints exist
    for r in rrows:
        rel = (r.get("rel_name") or "").strip()
        fe = (r.get("from_entity") or "").strip()
        te = (r.get("to_entity") or "").strip()
        if not rel or not fe or not te:
            issues.append(Issue("WARN", "relationship_catalog", f"Incomplete relationship row: {r}"))
            continue
        if fe not in entities:
            issues.append(Issue("ERROR", "relationship_catalog", f"from_entity missing in field catalog: {rel} from {fe}"))
        if te not in entities:
            issues.append(Issue("ERROR", "relationship_catalog", f"to_entity missing in field catalog: {rel} to {te}"))


def validate_schemas(base: str, issues: list[Issue]) -> None:
    sdir = os.path.join(base, "schemas", "entities")
    if not os.path.isdir(sdir):
        return
    reg = os.path.join(sdir, "registry.json")
    if not os.path.exists(reg):
        issues.append(Issue("WARN", "schemas", "schemas/entities exists but registry.json is missing"))
        return

    try:
        with open(reg, "r", encoding="utf-8") as f:
            data = json.load(f)
    except Exception as e:
        issues.append(Issue("ERROR", "schemas", f"Cannot read registry.json: {e}"))
        return

    ents = data.get("entities", {})
    if not isinstance(ents, dict) or not ents:
        issues.append(Issue("ERROR", "schemas", "registry.json missing entities map"))
        return

    for ent, meta in ents.items():
        sp = meta.get("schema_path")
        if not sp:
            issues.append(Issue("ERROR", "schemas", f"Entity {ent} has no schema_path"))
            continue
        abs_path = os.path.join(os.path.dirname(sdir), sp)
        if not os.path.exists(abs_path):
            issues.append(Issue("ERROR", "schemas", f"Missing schema file for {ent}: {abs_path}"))


def validate_templates(base: str, issues: list[Issue]) -> None:
    tdir = os.path.join(base, "templates", "neo4j_admin_import")
    if not os.path.isdir(tdir):
        return
    node_headers = _list_files(os.path.join(tdir, "nodes"), "_header.csv")
    rel_headers = _list_files(os.path.join(tdir, "rels"), "_header.csv")
    if not node_headers:
        issues.append(Issue("WARN", "templates", "No node header templates found"))
    if not rel_headers:
        issues.append(Issue("WARN", "templates", "No relationship header templates found"))


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--base", default=".")
    ap.add_argument("--mode", choices=["DRAFT", "PCG"], required=True)
    ap.add_argument("--strict", action="store_true", help="In DRAFT mode, return non-zero on errors")
    args = ap.parse_args()

    issues: list[Issue] = []

    validate_model(args.base, issues)
    validate_schemas(args.base, issues)
    validate_templates(args.base, issues)

    errors = [i for i in issues if i.severity == "ERROR"]

    # Print report
    print("=== LitigationOS Validation Report ===")
    for i in issues:
        print(f"[{i.severity}] {i.where}: {i.msg}")
    print(f"Total: {len(issues)} issues; {len(errors)} errors")

    if args.mode == "PCG" and errors:
        return 2
    if args.mode == "DRAFT" and args.strict and errors:
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

Fixing schema validation and packaging

I noticed that validate_schemas is expecting registry.json, but schema_emit outputs _registry.json and the structure doesn't match. That's definitely an error. I need to fix the validation process to match the actual outputs before proceeding with packaging. Additionally, we need to generate schemas, templates, and neo4j, and adjust the validator for PCW/PCG gating. I'll move on to patching this, while also noting that schemas/entities is currently empty—it's fine for now, but we need to implement harvest_csv_headers.py. Let's review it further.
Inspecting harvest_csv_headers.py for implementation

Always show details
bash -lc sed -n '1,260p' /mnt/data/_work_c3/LitigationOS_Blueprint_Pack_v2026-01-19.3/tools/harvest_csv_headers.py

#!/usr/bin/env python3
"""Harvest CSV headers from a directory tree.

Usage:
  python tools/harvest_csv_headers.py --root /path/to/dir --out docs/CSV_HEADER_HARVEST.md

Notes:
  - This tool is read-only; it does not modify any sources.
  - If delimiter detection fails, it defaults to comma.
"""

from __future__ import annotations

import argparse
import csv
import os


def iter_csv_files(root: str) -> list[str]:
    out: list[str] = []
    for dp, _, fns in os.walk(root):
        for fn in fns:
            if fn.lower().endswith('.csv'):
                out.append(os.path.join(dp, fn))
    return sorted(out)


def read_header(path: str) -> list[str]:
    with open(path, 'r', encoding='utf-8', newline='') as f:
        sample = f.read(4096)
        f.seek(0)
        try:
            dialect = csv.Sniffer().sniff(sample, delimiters=[',','\t',';','|'])
            reader = csv.reader(f, dialect)
        except csv.Error:
            reader = csv.reader(f, delimiter=',')
        for row in reader:
            if row and any(c.strip() for c in row):
                return [c.strip() for c in row]
    return []


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument('--root', required=True)
    ap.add_argument('--out', required=True)
    args = ap.parse_args()

    files = iter_csv_files(args.root)
    headers_by_file: dict[str, list[str]] = {}
    all_cols: set[str] = set()
    for p in files:
        cols = read_header(p)
        headers_by_file[p] = cols
        for c in cols:
            if c:
                all_cols.add(c)

    with open(args.out, 'w', encoding='utf-8') as f:
        f.write(f"# CSV Header Harvest\n\nRoot: `{args.root}`\n\n")
        f.write(f"Files scanned: {len(files)}\n\n")
        f.write("## Unique columns (union)\n\n")
        for c in sorted(all_cols):
            f.write(f"- `{c}`\n")
        f.write("\n## Per-file headers\n\n")
        for p in files:
            f.write(f"### `{p}`\n\n")
            cols = headers_by_file[p]
            if not cols:
                f.write("(no header detected)\n\n")
                continue
            f.write(", ".join(f"`{c}`" for c in cols) + "\n\n")

    return 0


if __name__ == '__main__':
    raise SystemExit(main())

Preparing for C3 packaging and documentation

Okay, the current system doesn't handle zips, so we'll need to extract directories before running. Also, certain folders, like "neo4j/schema_constraints.cypher," are still empty, so we'll generate them through script execution. We need to update validate_all, create the C3 docs, and revise both README and INDEX.md for consistency. I'll also introduce a new savepoint protocol for C3, update related documentation, and finalize packaging instructions in docs/FINALIZATION_AND_PACKAGING_C3.md. I'll include a script to build the zip if necessary. Let’s implement these changes.
Preparing C3 packaging and fixes

First, I’ll duplicate the folder to /mnt/data/_work_c3/LitigationOS_Blueprint_Pack_v2026-01-19.3. Then, I'll patch the README, docs, and validator. I need to ensure validate_all reads _registry.json and correctly handles the entities structure as a list. I'll also check schema file existence and validate all templates. There's a _registry.json output to incorporate. Lastly, I'll add the new SavePoint file for C3 and ensure the correct Neo4j schema files are included. Let’s implement these fixes!
Updating entity handling and index generation

I’ll create the nodes header in templates/neo4j_admin_import for each entity, but the script currently only handles ones with a primary key (PK). We need to create a fallback for PK selection, and not skip any entities. I’ll improve it to infer PK from various heuristics. Also, in schema generation, we should index more fields like _id, date, timestamps, and case numbers—though this may generate many indexes. Let's update the scripts accordingly!
Handling maximum indexes and constraints

Since the user wants maximum, I’ll generate indexes for all _id fields while excluding primary keys (PK) and unique fields. This could result in hundreds, but it’s okay. I’ll create both "aggressive" and "core" indexes and put them in separate files. This may have performance considerations for Neo4j, but it's what the user requested. I'll also handle uniqueness on PKs but will check if node key constraints are necessary. Let's make sure everything is ready for the zip!
Creating graph contracts and CSV validator

We need to create JSON schemas for node/rel CSVs, which will be defined under schemas/graph_contracts/. I'll start by creating node_csv.schema.json with schema validations for each row, referencing entity row schemas. Then I’ll implement validation tools for CSVs and ensure proper type conversion (basic as strings). I'll check the docs to confirm if this is already covered.
Finalizing packaging, validation, and schema generation for C3

Always show details
bash -lc sed -n '1,220p' /mnt/data/_work_c3/LitigationOS_Blueprint_Pack_v2026-01-19.3/docs/GRAPH_CONTRACTS_v2026-01-19.2.md

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

Finalizing documentation and packaging

I’ll update the document structure, reflecting the correct paths and features like JSON schema emitters, Neo4j schema generators, and validation updates. I’ll also create necessary documentation and tools, like bloom_extract_normalize.py. For now, I’ll focus on packaging, ensuring the final scripts and reports are generated and included.
Handling file inclusion and constraints

The pack should be self-contained, but including those large zips might increase the size unnecessarily. Instead of embedding entire files, I’ll harvest headers from the CSVs by extracting zips to a temporary folder. The header output will be included, not the full zips. I’ll also add a tool for local drive usage.
Handling CSV header extraction

I’ll parse the CSV headers and combine them into the document docs/CSV_HEADER_HARVEST_FROM_UPLOADED_CYCLEPACKS_v2026-01-19.3.md. The headers will be extracted into temporary storage using the script. The results will be included, but not the original zip files unless they are small enough—I'll check the size first.
Packaging and updating documentation

Always show details
bash -lc ls -lh /mnt/data/*.zip | sed -n '1,200p'

-rw-r--r-- 1 root root 133M Jan 20 04:34 /mnt/data/COURT RULES.zip
-rw-r--r-- 1 root root  15M Jan 20 04:33 /mnt/data/ETERNAL_GRAPH_BUNDLE_MASTER_LOCKED.zip
-rw-r--r-- 1 root root 113M Jan 20 04:34 /mnt/data/EVIDENCE.zip
-rw-r--r-- 1 root root 1.9M Jan 20 04:33 /mnt/data/EternalCodex_Complete.zip
-rw-r--r-- 1 root root  22M Jan 20 04:33 /mnt/data/LITIGATIONOS_AUTHORITY_GRAPH_MERGE_GRAPHRAG_CYCLEPACK_20260107_164708.zip
-rw-r--r-- 1 root root  22M Jan 20 04:33 /mnt/data/LITIGATIONOS_STATEMENT_FACT_PROV_AUTH_CYCLEPACK_20260107_181048.zip
-rw-r--r-- 1 root root  36M Jan 20 04:34 /mnt/data/LITIGATIONOS__MASTERv1.0__v0009__FULL(2).zip
-rw-r--r-- 1 root root 212K Jan 20 04:34 /mnt/data/LitigationOS_Blueprint_Pack_v2026-01-19.1.zip
-rw-r--r-- 1 root root  14M Jan 20 04:33 /mnt/data/LitigationOS_Blueprint_Pack_v2026-01-19.2.zip
-rw-r--r-- 1 root root 186K Jan 20 04:34 /mnt/data/LitigationOS_IntegratedLauncher_BucketOrchestrator_v2026-01-18.22_console_orchestrator_cyclepack_parallel(2).zip
-rw-r--r-- 1 root root 1.6M Jan 20 04:34 /mnt/data/LitigationOS_Module_Addendum_Pack_v2026-01-19(2).zip

Finalizing tasks and documentation

The zip files are large, so it's better not to include them in the pack. Instead, I’ll harvest metadata by scanning the zips using Python's zipfile to grab the CSV headers. I’ll create a script for this, which outputs to a document. I’ll also update documentation and create new files like LitigationOS_BLUEPRINT_README_v2026-01-19.3.md and GRAPH_CONTRACTS_v2026-01-19.3.md.
Finalizing script updates and bundle modifications

The user mentioned appending to the last deliverables, so I'll create new files and update the bundle builder to v2026-01-19.3, ensuring it includes all necessary actions. I'll implement script modifications, like updating validate_all, _pick_pk, and adding tools/harvest_zip_csv_headers.py. Then, I’ll run everything.
Implementing LitigationOS finalization tasks and documentation updates

Always show details
bash -lc set -euo pipefail
BASE='/mnt/data/_work_c3/LitigationOS_Blueprint_Pack_v2026-01-19.3'

# 1) New README v2026-01-19.3
cat > "$BASE/LitigationOS_BLUEPRINT_README_v2026-01-19.3.md" <<'MD'
# LitigationOS — Bottom→Top Blueprint + Build README (C3) (v2026-01-19.3)
Build stamp (local): 2026-01-20

## What this deliverable is
This cycle (C3) **finalizes and packages** the prior blueprint pack (C2) by adding:
- **machine-checkable graph contracts**: per-entity JSON Schemas emitted from the dense field catalog
- **Neo4j schema generator**: constraints + core/aggressive index scripts
- **neo4j-admin import templates**: node/rel header templates generated from catalogs
- **validator alignment**: DRAFT (fail-soft) vs PCG (fail-closed) now matches emitted artifacts
- **cyclepack header harvest** from your uploaded ZIPs (read-only) into a unioned column lexicon

This pack is intended to be the **authoritative bottom→top build README + schema/contract nucleus** that the rest of LitigationOS compiles against.

## Where to look first
### A) Top index (navigation)
- `INDEX.md`

### B) The granular build plan (bottom → top)
- `docs/BUILDPLAN_BOTTOM_TO_TOP_v2026-01-19.2.md`

### C) Max-density schema catalogs (source of truth)
- `model/field_catalog_superset.csv` (entity → dense field list)
- `model/relationship_catalog_superset.csv` (from/to → relationship catalog)
- `docs/ERD_SUPERSET_FIELD_DICTIONARY_v2026-01-19.2.md` (human-readable field dictionary)
- `docs/ENTITY_RELATIONSHIP_SUPERSET_INDEX_v2026-01-19.2.md` (human-readable rel index)

### D) Graph contracts (machine validation)
- `schemas/entities/*.schema.json` (per-entity JSON Schema; strict by default)
- `schemas/entities/_registry.json` (schema registry)
- `docs/GRAPH_CONTRACTS_v2026-01-19.3.md` (how contracts connect to GraphIR + import packs)

### E) Neo4j import + schema
- `templates/neo4j_admin_import/nodes/*_header.csv`
- `templates/neo4j_admin_import/rels/*_header.csv`
- `neo4j/schema_constraints.cypher`
- `neo4j/schema_indexes_core.cypher`
- `neo4j/schema_indexes_aggressive.cypher`

### F) Restartability / infinite chained cycles
- `docs/SAVEPOINT_PROTOCOL_v2026-01-19.3.md`
- Example savepoint: `savepoints/example/savepoint_C3_finalization.json`

### G) Diagrams (ERD-style overview + domain cards)
- Overview: `diagrams/erd_superset_overview_sfdp.png`
- Domain cards: `diagrams/erd_superset_cards_*.png`

## What “C3” changes versus C2
### 1) JSON Schema emitter is now real, not just prescribed
The canonical catalogs now compile into schemas:
- Build: `python tools/schema_emit.py --field-catalog model/field_catalog_superset.csv --out-dir schemas/entities`

### 2) Neo4j schema scripts are generated and staged
- Build: `python tools/generate_neo4j_schema.py --field-catalog model/field_catalog_superset.csv --out-dir neo4j`

### 3) neo4j-admin import header templates are generated
- Build: `python tools/generate_graphir_templates.py --field-catalog model/field_catalog_superset.csv --rel-catalog model/relationship_catalog_superset.csv --out-dir templates/neo4j_admin_import`

### 4) Validator now matches emitted artifacts
- DRAFT mode: collects issues (exit 0) and writes a report
- PCG mode: fail-closed (non-zero exit) if any ERROR exists

### 5) Cyclepack CSV header harvest (from uploaded ZIPs)
- Output: `docs/CSV_HEADER_HARVEST_FROM_UPLOADED_CYCLEPACKS_v2026-01-19.3.md`

## How to run the finalization pipeline (inside this pack)
From the pack root:
```bash
python tools/schema_emit.py --field-catalog model/field_catalog_superset.csv --out-dir schemas/entities
python tools/generate_neo4j_schema.py --field-catalog model/field_catalog_superset.csv --out-dir neo4j
python tools/generate_graphir_templates.py --field-catalog model/field_catalog_superset.csv --rel-catalog model/relationship_catalog_superset.csv --out-dir templates/neo4j_admin_import
python tools/validate_all.py --base . --mode DRAFT
python tools/validate_all.py --base . --mode PCG

Bottom→Top model (one screen)

    Sources (files, zips, dockets, transcripts)

    Artifacts (every file becomes an Artifact node + provenance)

    Extraction (text/OCR + anchors)

    Atoms (Evidence/Authority/Order/Service/Docket/Quote)

    GraphIR contracts (catalogs + schemas + templates)

    Graph import (neo4j-admin import packs)

    PCW/PO overlay (proof obligations + acquisition tasks)

    Compilation (timelines, matrices, contradiction maps, authority triples)

    Draft factory (forms-first, proposition gated)

    Packet/binder (exhibits + manifest + service chain)

    PCG (irreversible boundary)
    MD

2) Update INDEX.md to point to C3

cat > "$BASE/INDEX.md" <<'MD'
LitigationOS Blueprint Pack — Index (v2026-01-19.3)
Start here

    LitigationOS_BLUEPRINT_README_v2026-01-19.3.md

Core model catalogs

    model/field_catalog_superset.csv

    model/relationship_catalog_superset.csv

    model/entity_index.csv

    model/rel_index.csv

Human-readable dictionaries

    docs/ERD_SUPERSET_FIELD_DICTIONARY_v2026-01-19.2.md

    docs/ENTITY_RELATIONSHIP_SUPERSET_INDEX_v2026-01-19.2.md

Build plan (bottom → top)

    docs/BUILDPLAN_BOTTOM_TO_TOP_v2026-01-19.2.md

Graph contracts

    docs/GRAPH_CONTRACTS_v2026-01-19.3.md

    schemas/entities/_registry.json

    schemas/entities/*.schema.json

Neo4j import and schema

    templates/neo4j_admin_import/nodes/*_header.csv

    templates/neo4j_admin_import/rels/*_header.csv

    neo4j/schema_constraints.cypher

    neo4j/schema_indexes_core.cypher

    neo4j/schema_indexes_aggressive.cypher

Restartability

    docs/SAVEPOINT_PROTOCOL_v2026-01-19.3.md

    savepoints/example/savepoint_C3_finalization.json

Cyclepack header harvest

    docs/CSV_HEADER_HARVEST_FROM_UPLOADED_CYCLEPACKS_v2026-01-19.3.md

Diagrams

    diagrams/erd_superset_overview_sfdp.png

    diagrams/erd_superset_cards_*.png
    MD

3) New docs: SAVEPOINT_PROTOCOL v2026-01-19.3 and GRAPH_CONTRACTS v2026-01-19.3

cat > "$BASE/docs/SAVEPOINT_PROTOCOL_v2026-01-19.3.md" <<'MD'
LitigationOS SavePoint Protocol — v2026-01-19.3
Purpose

A SavePoint is the minimal restartable state for a pipeline stage or cycle. It exists so LitigationOS can run chained, consecutive iterations without losing determinism.
SavePoint invariants

Each SavePoint directory is append-only and must include:
1) savepoint.json

Required fields:

    savepoint_id (string): deterministic ID (timestamped but structured)

    cycle_id (string): e.g., C3_finalization

    stage (string): stage name (e.g., schemas_emit, neo4j_schema, templates_emit)

    base_pack_version (string): e.g., v2026-01-19.3

    inputs (array): each item {path, role, checksum_hint(optional)}

    outputs (array): each item {path, role, size_bytes}

    counts (object): deterministic counts (entities, rels, schemas, headers)

    validator (object): {mode, exit_code, error_count, warn_count, report_path}

    resume (object): exact commands to resume from this checkpoint

2) run.log

A human-readable log:

    start/end timestamps

    commands executed

    validator summary

3) reports/

At minimum:

    validation_report.md

    validation_report.json

PCW/PCG mapping

    DISCOVERY / BUILD: SavePoints are fail-soft (capture blockers)

    PCG boundary: SavePoints are fail-closed (no irreversible action unless PCG passes)

Implementation pattern

    Stage writes outputs to a deterministic folder.

    Stage runs validator.

    Stage writes SavePoint with:

        paths to outputs

        validator summary

        resume commands

Example

See savepoints/example/savepoint_C3_finalization.json.
MD

cat > "$BASE/docs/GRAPH_CONTRACTS_v2026-01-19.3.md" <<'MD'
LitigationOS Graph Contracts (GraphIR) — v2026-01-19.3
Contract artifacts (this pack)
1) Canonical catalogs (source of truth)

    model/field_catalog_superset.csv

    model/relationship_catalog_superset.csv

2) Emitted per-entity JSON Schemas (strict)

    schemas/entities/<Entity>.schema.json

    schemas/entities/_registry.json

3) neo4j-admin CSV header templates

    templates/neo4j_admin_import/nodes/<Entity>_header.csv

    templates/neo4j_admin_import/rels/<REL_TYPE>_header.csv

4) Neo4j schema scripts

    neo4j/schema_constraints.cypher

    neo4j/schema_indexes_core.cypher

    neo4j/schema_indexes_aggressive.cypher

Validator entrypoints

    Structural validator: python tools/validate_all.py --base . --mode DRAFT

    Fail-closed validator: python tools/validate_all.py --base . --mode PCG

Neo4j bulk import header rules

Node CSV files typically include:

    an ID column (:ID)

    properties (columns)

    label assignment (either :LABEL column or file-level label binding)

Relationship CSV files include:

    :START_ID

    :END_ID

    :TYPE

This pack emits headers only; you bind labels/types in your actual import command.
Recommended import discipline

    Generate schemas/templates from catalogs.

    Validate catalogs + emitted artifacts (DRAFT then PCG).

    Generate import packs (nodes + rels) from ingestion outputs.

    Validate import packs against schemas.

    Perform neo4j-admin import.

    Apply constraints/indexes.

Strictness strategy

    The JSON Schemas are strict (additionalProperties=false) to prevent silent drift.

    Your ingestion/export layer should normalize and map any legacy columns into this contract.
    MD

4) Patch tools/validate_all.py to match emitted schema registry and add report writing

cat > "$BASE/tools/validate_all.py" <<'PY'
#!/usr/bin/env python3
"""LitigationOS — Validator (DRAFT fail-soft / PCG fail-closed)

Validates internal consistency of:

    model/field_catalog_superset.csv

    model/relationship_catalog_superset.csv

    schemas/entities/_registry.json and referenced schema files (optional)

    templates/neo4j_admin_import/* headers (optional)

    neo4j/*.cypher schema scripts (optional)

Modes:

    DRAFT: collect errors, exit 0 (unless --strict)

    PCG: fail-closed; any ERROR => exit non-zero

Writes:

    validation_reports/validation_report.md

    validation_reports/validation_report.json

Dependency policy:

    dependency-free (standard library only)

Usage:
python tools/validate_all.py --base . --mode DRAFT
python tools/validate_all.py --base . --mode PCG

Exit codes:
0 = OK or fail-soft conditions met
2 = Validation failures in PCG (or DRAFT+--strict)
"""

from future import annotations

import argparse
import csv
import json
import os
from dataclasses import dataclass
from datetime import datetime

@dataclass
class Issue:
severity: str # ERROR|WARN
where: str
msg: str

def _read_csv(path: str) -> list[dict]:
with open(path, "r", encoding="utf-8", newline="") as f:
return list(csv.DictReader(f))

def _list_files(root: str, suffix: str) -> list[str]:
out: list[str] = []
for dp, _, fns in os.walk(root):
for fn in fns:
if fn.lower().endswith(suffix.lower()):
out.append(os.path.join(dp, fn))
return sorted(out)

def validate_model(base: str, issues: list[Issue]) -> tuple[set[str], list[dict], list[dict]]:
fc = os.path.join(base, "model", "field_catalog_superset.csv")
rc = os.path.join(base, "model", "relationship_catalog_superset.csv")

Always show details
if not os.path.exists(fc):
    issues.append(Issue("ERROR", "model", f"Missing {fc}"))
    return set(), [], []
if not os.path.exists(rc):
    issues.append(Issue("ERROR", "model", f"Missing {rc}"))
    return set(), [], []

frows = _read_csv(fc)
rrows = _read_csv(rc)

entities = set((r.get("entity") or "").strip() for r in frows if (r.get("entity") or "").strip())
if not entities:
    issues.append(Issue("ERROR", "field_catalog", "No entities found"))

# field uniqueness within entity
seen = set()
for r in frows:
    e = (r.get("entity") or "").strip()
    f = (r.get("field") or "").strip()
    if not e or not f:
        issues.append(Issue("WARN", "field_catalog", f"Row missing entity or field: {r}"))
        continue
    key = (e, f)
    if key in seen:
        issues.append(Issue("ERROR", "field_catalog", f"Duplicate field {e}.{f}"))
    seen.add(key)

# relationship endpoints exist
for r in rrows:
    rel = (r.get("rel_name") or "").strip()
    fe = (r.get("from_entity") or "").strip()
    te = (r.get("to_entity") or "").strip()
    if not rel or not fe or not te:
        issues.append(Issue("WARN", "relationship_catalog", f"Incomplete relationship row: {r}"))
        continue
    if fe not in entities:
        issues.append(Issue("ERROR", "relationship_catalog", f"from_entity missing in field catalog: {rel} from {fe}"))
    if te not in entities:
        issues.append(Issue("ERROR", "relationship_catalog", f"to_entity missing in field catalog: {rel} to {te}"))

return entities, frows, rrows

def validate_schemas(base: str, issues: list[Issue], entities: set[str]) -> None:
sdir = os.path.join(base, "schemas", "entities")
if not os.path.isdir(sdir):
issues.append(Issue("WARN", "schemas", "schemas/entities directory missing"))
return

Always show details
reg = os.path.join(sdir, "_registry.json")
if not os.path.exists(reg):
    issues.append(Issue("WARN", "schemas", "schemas/entities exists but _registry.json is missing (run tools/schema_emit.py)"))
    return

try:
    with open(reg, "r", encoding="utf-8") as f:
        data = json.load(f)
except Exception as e:
    issues.append(Issue("ERROR", "schemas", f"Cannot read _registry.json: {e}"))
    return

ents = data.get("entities")
if not isinstance(ents, list) or not ents:
    issues.append(Issue("ERROR", "schemas", "_registry.json missing entities list"))
    return

for item in ents:
    ent = (item.get("entity") or "").strip() if isinstance(item, dict) else ""
    sch = (item.get("schema") or "").strip() if isinstance(item, dict) else ""
    if not ent or not sch:
        issues.append(Issue("ERROR", "schemas", f"Malformed registry entry: {item}"))
        continue
    if ent not in entities:
        issues.append(Issue("WARN", "schemas", f"Schema registry entity not in field catalog: {ent}"))
    sp = os.path.join(sdir, sch)
    if not os.path.exists(sp):
        issues.append(Issue("ERROR", "schemas", f"Missing schema file for {ent}: {sp}"))
        continue
    try:
        with open(sp, "r", encoding="utf-8") as f:
            json.load(f)
    except Exception as e:
        issues.append(Issue("ERROR", "schemas", f"Schema JSON parse failed for {ent}: {e}"))

def validate_templates(base: str, issues: list[Issue]) -> None:
tdir = os.path.join(base, "templates", "neo4j_admin_import")
if not os.path.isdir(tdir):
issues.append(Issue("WARN", "templates", "templates/neo4j_admin_import directory missing"))
return
node_headers = _list_files(os.path.join(tdir, "nodes"), "_header.csv")
rel_headers = _list_files(os.path.join(tdir, "rels"), "_header.csv")
if not node_headers:
issues.append(Issue("WARN", "templates", "No node header templates found (run tools/generate_graphir_templates.py)"))
if not rel_headers:
issues.append(Issue("WARN", "templates", "No relationship header templates found (run tools/generate_graphir_templates.py)"))

def validate_neo4j_schema(base: str, issues: list[Issue]) -> None:
ndir = os.path.join(base, "neo4j")
if not os.path.isdir(ndir):
issues.append(Issue("WARN", "neo4j", "neo4j directory missing"))
return
needed = [
"schema_constraints.cypher",
"schema_indexes_core.cypher",
"schema_indexes_aggressive.cypher",
]
for fn in needed:
p = os.path.join(ndir, fn)
if not os.path.exists(p):
issues.append(Issue("WARN", "neo4j", f"Missing {fn} (run tools/generate_neo4j_schema.py)"))

def write_reports(base: str, mode: str, issues: list[Issue], exit_code: int) -> None:
outdir = os.path.join(base, "validation_reports")
os.makedirs(outdir, exist_ok=True)

Always show details
errors = [i for i in issues if i.severity == "ERROR"]
warns = [i for i in issues if i.severity == "WARN"]

payload = {
    "timestamp": datetime.utcnow().isoformat() + "Z",
    "mode": mode,
    "exit_code": exit_code,
    "counts": {"total": len(issues), "errors": len(errors), "warns": len(warns)},
    "issues": [i.__dict__ for i in issues],
}

jpath = os.path.join(outdir, "validation_report.json")
with open(jpath, "w", encoding="utf-8") as f:
    json.dump(payload, f, indent=2)
    f.write("\n")

mpath = os.path.join(outdir, "validation_report.md")
with open(mpath, "w", encoding="utf-8") as f:
    f.write(f"# LitigationOS Validation Report\n\n")
    f.write(f"- Mode: `{mode}`\n")
    f.write(f"- Exit code: `{exit_code}`\n")
    f.write(f"- Total issues: `{len(issues)}` (errors `{len(errors)}`, warns `{len(warns)}`)\n\n")
    if errors:
        f.write("## Errors\n\n")
        for e in errors:
            f.write(f"- **{e.where}**: {e.msg}\n")
        f.write("\n")
    if warns:
        f.write("## Warnings\n\n")
        for w in warns:
            f.write(f"- **{w.where}**: {w.msg}\n")
        f.write("\n")

def main() -> int:
ap = argparse.ArgumentParser()
ap.add_argument("--base", default=".")
ap.add_argument("--mode", choices=["DRAFT", "PCG"], required=True)
ap.add_argument("--strict", action="store_true", help="In DRAFT mode, return non-zero on errors")
args = ap.parse_args()

Always show details
issues: list[Issue] = []

entities, _, _ = validate_model(args.base, issues)
validate_schemas(args.base, issues, entities)
validate_templates(args.base, issues)
validate_neo4j_schema(args.base, issues)

errors = [i for i in issues if i.severity == "ERROR"]

# Print report to stdout
print("=== LitigationOS Validation Report ===")
for i in issues:
    print(f"[{i.severity}] {i.where}: {i.msg}")
print(f"Total: {len(issues)} issues; {len(errors)} errors")

exit_code = 0
if args.mode == "PCG" and errors:
    exit_code = 2
if args.mode == "DRAFT" and args.strict and errors:
    exit_code = 2

write_reports(args.base, args.mode, issues, exit_code)
return exit_code

if name == "main":
raise SystemExit(main())
PY

chmod +x "$BASE/tools/validate_all.py"
5) Patch _pick_pk heuristics in generators (maximize coverage)

perl -0777 -pe 's/def _pick_pkentity: str, rows: list\[dict\] -> str | None:\n # Prefer explicit pk note\n for r in rows:\n notes = r.get\("notes" or "").lower\n if "primary key" in notes:\n return r.get\("field" or "").strip or None\n # Fall back to <entity_lower>_id\n candidate = f"{entity.lower}_id"\n for r in rows:\n if r.get\("field" or "").strip == candidate:\n return candidate\n # Else any required _id\n for r in rows:\n if r.get\("required" or "").strip.upper == "Y":\n f = r.get\("field" or "").strip\n if f.endswith"id""i​d":\n return f\n return None/def _pick_pk(entity: str, rows: list[dict]) -> str | None:\n # 1) notes include primary key\n for r in rows:\n notes = (r.get("notes") or "").lower()\n if "primary key" in notes:\n v = (r.get("field") or "").strip()\n return v or None\n\n # 2) <entity_lower>_id\n candidate = f"{entity.lower()}_id"\n for r in rows:\n if (r.get("field") or "").strip() == candidate:\n return candidate\n\n # 3) generic id\n for r in rows:\n if (r.get("field") or "").strip() == "id":\n return "id"\n\n # 4) first *_id field\n for r in rows:\n f = (r.get("field") or "").strip()\n if f.endswith("_id"):\n return f\n\n # 5) first field as last resort\n for r in rows:\n f = (r.get("field") or "").strip()\n if f:\n return f\n\n return None/sms' -i "$BASE/tools/generate_graphir_templates.py" "$BASE/tools/generate_neo4j_schema.py"
6) Expand generate_neo4j_schema.py to output core + aggressive indexes

cat > "$BASE/tools/generate_neo4j_schema.py" <<'PY'
#!/usr/bin/env python3
"""LitigationOS — Generate Neo4j constraints/indexes scripts from the schema catalogs.

Outputs:
neo4j/schema_constraints.cypher
neo4j/schema_indexes_core.cypher
neo4j/schema_indexes_aggressive.cypher
neo4j/schema_enterprise_optional.cypher (commented Enterprise-only constraints)

Primary-key selection:

    notes include 'Primary key'

    <entity_lower>_id

    id

    first *_id

    first field

Indexing strategy:

    core: conservative indexes on highly-common join and time/provenance fields

    aggressive: indexes on most *_id and timestamp/date-ish fields (use with care)

Usage:
python tools/generate_neo4j_schema.py --field-catalog model/field_catalog_superset.csv --out-dir neo4j
"""

from future import annotations

import argparse
import csv
import os
from collections import defaultdict

def _read_rows(path: str) -> list[dict]:
with open(path, "r", encoding="utf-8", newline="") as f:
return list(csv.DictReader(f))

def _pick_pk(entity: str, rows: list[dict]) -> str | None:
for r in rows:
notes = (r.get("notes") or "").lower()
if "primary key" in notes:
v = (r.get("field") or "").strip()
return v or None

Always show details
candidate = f"{entity.lower()}_id"
for r in rows:
    if (r.get("field") or "").strip() == candidate:
        return candidate

for r in rows:
    if (r.get("field") or "").strip() == "id":
        return "id"

for r in rows:
    f = (r.get("field") or "").strip()
    if f.endswith("_id"):
        return f

for r in rows:
    f = (r.get("field") or "").strip()
    if f:
        return f

return None

def safe_name(s: str) -> str:
return s.replace("-", "").replace(" ", "_")

def main() -> int:
ap = argparse.ArgumentParser()
ap.add_argument("--field-catalog", required=True)
ap.add_argument("--out-dir", required=True)
args = ap.parse_args()

Always show details
rows = _read_rows(args.field_catalog)
by_entity: dict[str, list[dict]] = defaultdict(list)
for r in rows:
    entity = (r.get("entity") or "").strip()
    if entity:
        by_entity[entity].append(r)

os.makedirs(args.out_dir, exist_ok=True)

constraints_path = os.path.join(args.out_dir, "schema_constraints.cypher")
core_indexes_path = os.path.join(args.out_dir, "schema_indexes_core.cypher")
aggressive_indexes_path = os.path.join(args.out_dir, "schema_indexes_aggressive.cypher")
enterprise_path = os.path.join(args.out_dir, "schema_enterprise_optional.cypher")

# Constraints (community-safe)
with open(constraints_path, "w", encoding="utf-8") as f:
    f.write("// LitigationOS Neo4j schema — constraints (Neo4j 5+ Cypher)\n")
    f.write("// Generated by tools/generate_neo4j_schema.py\n\n")
    for entity in sorted(by_entity.keys()):
        pk = _pick_pk(entity, by_entity[entity])
        if not pk:
            continue
        cname = _safe_name(f"uniq_{entity}_{pk}")
        f.write(f"CREATE CONSTRAINT {cname} IF NOT EXISTS FOR (n:`{entity}`) REQUIRE n.`{pk}` IS UNIQUE;\n")

# Index sets
core_fields = {
    "run_id",
    "case_id",
    "artifact_id",
    "source_id",
    "authority_id",
    "evidence_id",
    "docket_id",
    "order_id",
    "deadline_id",
    "person_id",
    "party_id",
    "bundle_id",
    "integrity_key",
    "created_at",
    "updated_at",
    "file_mtime",
    "event_ts",
    "hearing_date",
    "filed_date",
    "service_date",
}

def is_timeish(field: str) -> bool:
    lf = field.lower()
    return any(k in lf for k in ["_ts", "timestamp", "date", "datetime", "created", "updated", "mtime"])

def is_idish(field: str) -> bool:
    return field.lower().endswith("_id")

# Core indexes
with open(core_indexes_path, "w", encoding="utf-8") as f:
    f.write("// LitigationOS Neo4j schema — CORE indexes (Neo4j 5+ Cypher)\n")
    f.write("// Generated by tools/generate_neo4j_schema.py\n")
    f.write("// Use this file by default.\n\n")

    for entity in sorted(by_entity.keys()):
        rows_e = by_entity[entity]
        fields = [(r.get("field") or "").strip() for r in rows_e]
        fields = [x for x in fields if x]

        for field in fields:
            if field in core_fields:
                iname = _safe_name(f"idx_{entity}_{field}")
                f.write(f"CREATE INDEX {iname} IF NOT EXISTS FOR (n:`{entity}`) ON (n.`{field}`);\n")

# Aggressive indexes
with open(aggressive_indexes_path, "w", encoding="utf-8") as f:
    f.write("// LitigationOS Neo4j schema — AGGRESSIVE indexes (Neo4j 5+ Cypher)\n")
    f.write("// Generated by tools/generate_neo4j_schema.py\n")
    f.write("// Use only after import if you need maximum query performance.\n\n")

    for entity in sorted(by_entity.keys()):
        rows_e = by_entity[entity]
        fields = [(r.get("field") or "").strip() for r in rows_e]
        fields = [x for x in fields if x]

        # index all idish/timeish fields
        for field in fields:
            if is_idish(field) or is_timeish(field) or field in core_fields:
                iname = _safe_name(f"idx_{entity}_{field}")
                f.write(f"CREATE INDEX {iname} IF NOT EXISTS FOR (n:`{entity}`) ON (n.`{field}`);\n")

# Optional Enterprise-only constraints (existence)
with open(enterprise_path, "w", encoding="utf-8") as f:
    f.write("// LitigationOS Neo4j schema — Enterprise-only optional constraints\n")
    f.write("// These are commented out by default. Enable only if you have Enterprise Edition.\n\n")
    for entity in sorted(by_entity.keys()):
        pk = _pick_pk(entity, by_entity[entity])
        if pk:
            cname = _safe_name(f"x_req_{entity}_{pk}")
            f.write(f"// CREATE CONSTRAINT {cname} IF NOT EXISTS FOR (n:`{entity}`) REQUIRE n.`{pk}` IS NOT NULL;\n")

return 0

if name == "main":
raise SystemExit(main())
PY

chmod +x "$BASE/tools/generate_neo4j_schema.py"
7) Add zip CSV header harvester

cat > "$BASE/tools/harvest_zip_csv_headers.py" <<'PY'
#!/usr/bin/env python3
"""Harvest CSV headers from one or more ZIP files (read-only).

Writes a Markdown report including:

    union of all discovered CSV columns

    per-ZIP listing of CSV file headers

Usage:
python tools/harvest_zip_csv_headers.py --out docs/CSV_HEADER_HARVEST_FROM_UPLOADED_CYCLEPACKS_v2026-01-19.3.md
--zip /path/to/a.zip --zip /path/to/b.zip

Notes:

    Does not extract files to disk.

    Reads the first non-empty line from each CSV as header.
    """

from future import annotations

import argparse
import csv
import io
import os
import zipfile

def read_header_bytes(data: bytes) -> list[str]:
# Try to sniff delimiter using a small sample
sample = data[:4096].decode("utf-8", errors="replace")
buf = io.StringIO(sample)
try:
dialect = csv.Sniffer().sniff(sample, delimiters=[",", "\t", ";", "|"])
reader = csv.reader(buf, dialect)
except csv.Error:
buf.seek(0)
reader = csv.reader(buf, delimiter=",")

Always show details
for row in reader:
    if row and any(c.strip() for c in row):
        return [c.strip() for c in row]
return []

def main() -> int:
ap = argparse.ArgumentParser()
ap.add_argument("--zip", action="append", dest="zips", required=True, help="ZIP file path (repeatable)")
ap.add_argument("--out", required=True)
args = ap.parse_args()

Always show details
zips = [os.path.abspath(p) for p in args.zips]

per_zip: dict[str, dict[str, list[str]]] = {}
all_cols: set[str] = set()
total_csv = 0

for zpath in zips:
    per_zip[zpath] = {}
    if not os.path.exists(zpath):
        continue
    with zipfile.ZipFile(zpath, "r") as z:
        for name in z.namelist():
            if not name.lower().endswith(".csv"):
                continue
            try:
                data = z.read(name)
            except Exception:
                continue
            cols = read_header_bytes(data)
            per_zip[zpath][name] = cols
            total_csv += 1
            for c in cols:
                if c:
                    all_cols.add(c)

with open(args.out, "w", encoding="utf-8") as f:
    f.write("# CSV Header Harvest — Uploaded Cyclepacks (C3)\n\n")
    f.write(f"ZIPs scanned: {len(zips)}\n\n")
    for zpath in zips:
        f.write(f"- `{zpath}`\n")
    f.write("\n")
    f.write(f"CSV files found: {total_csv}\n\n")

    f.write("## Unique columns (union)\n\n")
    for c in sorted(all_cols):
        f.write(f"- `{c}`\n")

    f.write("\n## Per-ZIP headers\n\n")
    for zpath in zips:
        f.write(f"### `{zpath}`\n\n")
        files = per_zip.get(zpath, {})
        if not files:
            f.write("(no CSVs found or ZIP missing)\n\n")
            continue
        for name in sorted(files.keys()):
            cols = files[name]
            f.write(f"- `{name}`\n")
            if not cols:
                f.write("  - (no header detected)\n")
            else:
                f.write("  - " + ", ".join(f"`{c}`" for c in cols) + "\n")
        f.write("\n")

return 0

if name == "main":
raise SystemExit(main())
PY

chmod +x "$BASE/tools/harvest_zip_csv_headers.py"
8) Add FINALIZATION_AND_PACKAGING doc

cat > "$BASE/docs/FINALIZATION_AND_PACKAGING_v2026-01-19.3.md" <<'MD'
Finalization + Packaging (C3) — v2026-01-19.3
Goal

Turn catalogs + blueprints into a validated, restartable, import-ready nucleus.
C3 finalization checklist

    Emit JSON Schemas

    Emit Neo4j schema scripts

    Emit neo4j-admin import header templates

    Run validator in DRAFT

    Run validator in PCG

    Write SavePoint

    Package ZIP (test integrity)

Canonical commands

From pack root:

Always show details
python tools/schema_emit.py --field-catalog model/field_catalog_superset.csv --out-dir schemas/entities
python tools/generate_neo4j_schema.py --field-catalog model/field_catalog_superset.csv --out-dir neo4j
python tools/generate_graphir_templates.py --field-catalog model/field_catalog_superset.csv --rel-catalog model/relationship_catalog_superset.csv --out-dir templates/neo4j_admin_import
python tools/validate_all.py --base . --mode DRAFT
python tools/validate_all.py --base . --mode PCG

Packaging discipline

    Never rename the canonical folder.

    Append-only: new files and version-suffixed docs.

    ZIP must be verified with zip -T or unzip -t before distribution.
    MD

9) Update bundle builder to v2026-01-19.3 (kept minimal; still deterministic)

cat > "$BASE/tools/bundle_builder_v2026-01-19.3.py" <<'PY'
#!/usr/bin/env python3
"""LitigationOS Blueprint Pack — Local rebuild helper (v2026-01-19.3)

Why this exists
Sandbox download links can expire. This script reconstructs the C3 outputs
(schemas/templates/neo4j scripts/validation reports) from the canonical catalogs.

What it does (safe)

    reads catalogs under model/

    regenerates emitted artifacts under schemas/, templates/, neo4j/

    runs validator in DRAFT and PCG

Usage
python tools/bundle_builder_v2026-01-19.3.py --base .

Exit codes
0 = success
2 = PCG validation failure
"""

from future import annotations

import argparse
import os
import subprocess

def run(cmd: list[str], cwd: str) -> int:
p = subprocess.run(cmd, cwd=cwd)
return p.returncode

def main() -> int:
ap = argparse.ArgumentParser()
ap.add_argument("--base", default=".")
args = ap.parse_args()

Always show details
base = os.path.abspath(args.base)

steps = [
    ["python", "tools/schema_emit.py", "--field-catalog", "model/field_catalog_superset.csv", "--out-dir", "schemas/entities"],
    ["python", "tools/generate_neo4j_schema.py", "--field-catalog", "model/field_catalog_superset.csv", "--out-dir", "neo4j"],
    ["python", "tools/generate_graphir_templates.py", "--field-catalog", "model/field_catalog_superset.csv", "--rel-catalog", "model/relationship_catalog_superset.csv", "--out-dir", "templates/neo4j_admin_import"],
    ["python", "tools/validate_all.py", "--base", ".", "--mode", "DRAFT"],
    ["python", "tools/validate_all.py", "--base", ".", "--mode", "PCG"],
]

for cmd in steps:
    rc = run(cmd, base)
    if cmd[-1] == "PCG" and rc != 0:
        return 2

return 0

if name == "main":
raise SystemExit(main())
PY

chmod +x "$BASE/tools/bundle_builder_v2026-01-19.3.py"
10) Ensure directories exist

mkdir -p "$BASE/validation_reports" "$BASE/neo4j" "$BASE/schemas/entities" "$BASE/templates/neo4j_admin_import/nodes" "$BASE/templates/neo4j_admin_import/rels" "$BASE/savepoints/example"

echo 'C3 patch stage complete.'

Always show details

C3 patch stage complete.

Checking file existence and contents

The command completed, but it got truncated, so I need to confirm if the file exists. I'll take a look at the top lines to ensure everything went as expected and that the file has been properly created or updated.
Viewing top lines of file

Always show details
bash -lc sed -n '1,120p' /mnt/data/_work_c3/LitigationOS_Blueprint_Pack_v2026-01-19.3/LitigationOS_BLUEPRINT_README_v2026-01-19.3.md

# LitigationOS — Bottom→Top Blueprint + Build README (C3) (v2026-01-19.3)
Build stamp (local): 2026-01-20

## What this deliverable is
This cycle (C3) **finalizes and packages** the prior blueprint pack (C2) by adding:
- **machine-checkable graph contracts**: per-entity JSON Schemas emitted from the dense field catalog
- **Neo4j schema generator**: constraints + core/aggressive index scripts
- **neo4j-admin import templates**: node/rel header templates generated from catalogs
- **validator alignment**: DRAFT (fail-soft) vs PCG (fail-closed) now matches emitted artifacts
- **cyclepack header harvest** from your uploaded ZIPs (read-only) into a unioned column lexicon

This pack is intended to be the **authoritative bottom→top build README + schema/contract nucleus** that the rest of LitigationOS compiles against.

## Where to look first
### A) Top index (navigation)
- `INDEX.md`

### B) The granular build plan (bottom → top)
- `docs/BUILDPLAN_BOTTOM_TO_TOP_v2026-01-19.2.md`

### C) Max-density schema catalogs (source of truth)
- `model/field_catalog_superset.csv` (entity → dense field list)
- `model/relationship_catalog_superset.csv` (from/to → relationship catalog)
- `docs/ERD_SUPERSET_FIELD_DICTIONARY_v2026-01-19.2.md` (human-readable field dictionary)
- `docs/ENTITY_RELATIONSHIP_SUPERSET_INDEX_v2026-01-19.2.md` (human-readable rel index)

### D) Graph contracts (machine validation)
- `schemas/entities/*.schema.json` (per-entity JSON Schema; strict by default)
- `schemas/entities/_registry.json` (schema registry)
- `docs/GRAPH_CONTRACTS_v2026-01-19.3.md` (how contracts connect to GraphIR + import packs)

### E) Neo4j import + schema
- `templates/neo4j_admin_import/nodes/*_header.csv`
- `templates/neo4j_admin_import/rels/*_header.csv`
- `neo4j/schema_constraints.cypher`
- `neo4j/schema_indexes_core.cypher`
- `neo4j/schema_indexes_aggressive.cypher`

### F) Restartability / infinite chained cycles
- `docs/SAVEPOINT_PROTOCOL_v2026-01-19.3.md`
- Example savepoint: `savepoints/example/savepoint_C3_finalization.json`

### G) Diagrams (ERD-style overview + domain cards)
- Overview: `diagrams/erd_superset_overview_sfdp.png`
- Domain cards: `diagrams/erd_superset_cards_*.png`

## What “C3” changes versus C2
### 1) JSON Schema emitter is now real, not just prescribed
The canonical catalogs now compile into schemas:
- Build: `python tools/schema_emit.py --field-catalog model/field_catalog_superset.csv --out-dir schemas/entities`

### 2) Neo4j schema scripts are generated and staged
- Build: `python tools/generate_neo4j_schema.py --field-catalog model/field_catalog_superset.csv --out-dir neo4j`

### 3) neo4j-admin import header templates are generated
- Build: `python tools/generate_graphir_templates.py --field-catalog model/field_catalog_superset.csv --rel-catalog model/relationship_catalog_superset.csv --out-dir templates/neo4j_admin_import`

### 4) Validator now matches emitted artifacts
- DRAFT mode: collects issues (exit 0) and writes a report
- PCG mode: fail-closed (non-zero exit) if any ERROR exists

### 5) Cyclepack CSV header harvest (from uploaded ZIPs)
- Output: `docs/CSV_HEADER_HARVEST_FROM_UPLOADED_CYCLEPACKS_v2026-01-19.3.md`

## How to run the finalization pipeline (inside this pack)
From the pack root:
```bash
python tools/schema_emit.py --field-catalog model/field_catalog_superset.csv --out-dir schemas/entities
python tools/generate_neo4j_schema.py --field-catalog model/field_catalog_superset.csv --out-dir neo4j
python tools/generate_graphir_templates.py --field-catalog model/field_catalog_superset.csv --rel-catalog model/relationship_catalog_superset.csv --out-dir templates/neo4j_admin_import
python tools/validate_all.py --base . --mode DRAFT
python tools/validate_all.py --base . --mode PCG
```

## Bottom→Top model (one screen)
1) **Sources** (files, zips, dockets, transcripts)
2) **Artifacts** (every file becomes an Artifact node + provenance)
3) **Extraction** (text/OCR + anchors)
4) **Atoms** (Evidence/Authority/Order/Service/Docket/Quote)
5) **GraphIR contracts** (catalogs + schemas + templates)
6) **Graph import** (neo4j-admin import packs)
7) **PCW/PO overlay** (proof obligations + acquisition tasks)
8) **Compilation** (timelines, matrices, contradiction maps, authority triples)
9) **Draft factory** (forms-first, proposition gated)
10) **Packet/binder** (exhibits + manifest + service chain)
11) **PCG** (irreversible boundary)

Confirming new docs existence

The README looks good! Now, I need to check for the new docs referenced: GRAPH_CONTRACTS_v2026-01-19.3.md, SAVEPOINT_PROTOCOL_v2026-01-19.3.md, and the header harvest doc. The previous patch command should have created them, so I'll verify they actually exist.
Verifying documentation file existence

Always show details
bash -lc ls -lh /mnt/data/_work_c3/LitigationOS_Blueprint_Pack_v2026-01-19.3/docs | sed -n '1,200p'

total 294K
-rw-r--r-- 1 root root 6.0K Jan 20 03:49 BUILDPLAN_BOTTOM_TO_TOP_v2026-01-19.2.md
-rw-r--r-- 1 root root 7.5K Jan 20 03:49 ENTITY_RELATIONSHIP_SUPERSET_INDEX_v2026-01-19.2.md
-rw-r--r-- 1 root root 268K Jan 20 03:49 ERD_SUPERSET_FIELD_DICTIONARY_v2026-01-19.2.md
-rw-r--r-- 1 root root 1.1K Jan 20 04:42 FINALIZATION_AND_PACKAGING_v2026-01-19.3.md
-rw-r--r-- 1 root root 2.6K Jan 20 03:49 GRAPH_CONTRACTS_v2026-01-19.2.md
-rw-r--r-- 1 root root 1.7K Jan 20 04:42 GRAPH_CONTRACTS_v2026-01-19.3.md
-rw-r--r-- 1 root root 3.8K Jan 20 03:49 SAVEPOINT_PROTOCOL_v2026-01-19.2.md
-rw-r--r-- 1 root root 1.6K Jan 20 04:42 SAVEPOINT_PROTOCOL_v2026-01-19.3.md

Searching for header harvest doc

The header harvest doc isn't showing up where expected. It might be located in the root directory instead. I'll search for it there to see if that's where it's been placed. Hopefully, it's just in a different location!
Searching for header harvest files

Always show details
bash -lc find /mnt/data/_work_c3/LitigationOS_Blueprint_Pack_v2026-01-19.3 -maxdepth 2 -type f -name 'CSV_HEADER*' -o -name '*HARVEST*' | sed -n '1,200p'

Checking if the file exists

It seems the header harvest doc hasn't been generated yet. I'll use the new tool I created, harvest_zip_csv_headers.py, to generate it. First, though, I should check if the file already exists just to be sure we're not duplicating any work. Let's do that!
Checking if zip file exists

Always show details
bash -lc ls -lh /mnt/data/_work_c3/LitigationOS_Blueprint_Pack_v2026-01-19.3/tools | grep zip || true

-rwxr-xr-x 1 root root 3.2K Jan 20 04:42 harvest_zip_csv_headers.py

Preparing to run tool and check validations

I’ll run the tool using the list of zips, but I want to avoid hardcoding the path. The tool allows some flexibility, so I’ll make sure it’s running from the pack root, specifying paths as needed. After generating the document, I'll check if the scripts for validation and generators need patching. Let's take a look at validate_all.
Viewing validate_all script for updates

Always show details
bash -lc grep -n "registry" -n /mnt/data/_work_c3/LitigationOS_Blueprint_Pack_v2026-01-19.3/tools/validate_all.py | head

7:  - schemas/entities/_registry.json and referenced schema files (optional)
115:    reg = os.path.join(sdir, "_registry.json")
117:        issues.append(Issue("WARN", "schemas", "schemas/entities exists but _registry.json is missing (run tools/schema_emit.py)"))
124:        issues.append(Issue("ERROR", "schemas", f"Cannot read _registry.json: {e}"))
129:        issues.append(Issue("ERROR", "schemas", "_registry.json missing entities list"))
136:            issues.append(Issue("ERROR", "schemas", f"Malformed registry entry: {item}"))
139:            issues.append(Issue("WARN", "schemas", f"Schema registry entity not in field catalog: {ent}"))

Checking patch for generate_neo4j_schema.py

I’ve patched the previous scripts, but now I need to confirm that generate_neo4j_schema.py was updated to produce both core and aggressive outputs. I'll check it to make sure it's aligned with those expected results and that the patch applied correctly.
Verifying `generate_neo4j_schema.py` patch

Always show details
bash -lc ls -lh /mnt/data/_work_c3/LitigationOS_Blueprint_Pack_v2026-01-19.3/tools | grep neo4j_schema && sed -n '1,220p' /mnt/data/_work_c3/LitigationOS_Blueprint_Pack_v2026-01-19.3/tools/generate_neo4j_schema.py

-rwxr-xr-x 1 root root 6.1K Jan 20 04:42 generate_neo4j_schema.py
#!/usr/bin/env python3
"""LitigationOS — Generate Neo4j constraints/indexes scripts from the schema catalogs.

Outputs:
  neo4j/schema_constraints.cypher
  neo4j/schema_indexes_core.cypher
  neo4j/schema_indexes_aggressive.cypher
  neo4j/schema_enterprise_optional.cypher (commented Enterprise-only constraints)

Primary-key selection:
  1) notes include 'Primary key'
  2) <entity_lower>_id
  3) id
  4) first *_id
  5) first field

Indexing strategy:
  - core: conservative indexes on highly-common join and time/provenance fields
  - aggressive: indexes on most *_id and timestamp/date-ish fields (use with care)

Usage:
  python tools/generate_neo4j_schema.py --field-catalog model/field_catalog_superset.csv --out-dir neo4j
"""

from __future__ import annotations

import argparse
import csv
import os
from collections import defaultdict


def _read_rows(path: str) -> list[dict]:
    with open(path, "r", encoding="utf-8", newline="") as f:
        return list(csv.DictReader(f))


def _pick_pk(entity: str, rows: list[dict]) -> str | None:
    for r in rows:
        notes = (r.get("notes") or "").lower()
        if "primary key" in notes:
            v = (r.get("field") or "").strip()
            return v or None

    candidate = f"{entity.lower()}_id"
    for r in rows:
        if (r.get("field") or "").strip() == candidate:
            return candidate

    for r in rows:
        if (r.get("field") or "").strip() == "id":
            return "id"

    for r in rows:
        f = (r.get("field") or "").strip()
        if f.endswith("_id"):
            return f

    for r in rows:
        f = (r.get("field") or "").strip()
        if f:
            return f

    return None


def _safe_name(s: str) -> str:
    return s.replace("-", "_").replace(" ", "_")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--field-catalog", required=True)
    ap.add_argument("--out-dir", required=True)
    args = ap.parse_args()

    rows = _read_rows(args.field_catalog)
    by_entity: dict[str, list[dict]] = defaultdict(list)
    for r in rows:
        entity = (r.get("entity") or "").strip()
        if entity:
            by_entity[entity].append(r)

    os.makedirs(args.out_dir, exist_ok=True)

    constraints_path = os.path.join(args.out_dir, "schema_constraints.cypher")
    core_indexes_path = os.path.join(args.out_dir, "schema_indexes_core.cypher")
    aggressive_indexes_path = os.path.join(args.out_dir, "schema_indexes_aggressive.cypher")
    enterprise_path = os.path.join(args.out_dir, "schema_enterprise_optional.cypher")

    # Constraints (community-safe)
    with open(constraints_path, "w", encoding="utf-8") as f:
        f.write("// LitigationOS Neo4j schema — constraints (Neo4j 5+ Cypher)\n")
        f.write("// Generated by tools/generate_neo4j_schema.py\n\n")
        for entity in sorted(by_entity.keys()):
            pk = _pick_pk(entity, by_entity[entity])
            if not pk:
                continue
            cname = _safe_name(f"uniq_{entity}_{pk}")
            f.write(f"CREATE CONSTRAINT {cname} IF NOT EXISTS FOR (n:`{entity}`) REQUIRE n.`{pk}` IS UNIQUE;\n")

    # Index sets
    core_fields = {
        "run_id",
        "case_id",
        "artifact_id",
        "source_id",
        "authority_id",
        "evidence_id",
        "docket_id",
        "order_id",
        "deadline_id",
        "person_id",
        "party_id",
        "bundle_id",
        "integrity_key",
        "created_at",
        "updated_at",
        "file_mtime",
        "event_ts",
        "hearing_date",
        "filed_date",
        "service_date",
    }

    def is_timeish(field: str) -> bool:
        lf = field.lower()
        return any(k in lf for k in ["_ts", "timestamp", "date", "datetime", "created", "updated", "mtime"])

    def is_idish(field: str) -> bool:
        return field.lower().endswith("_id")

    # Core indexes
    with open(core_indexes_path, "w", encoding="utf-8") as f:
        f.write("// LitigationOS Neo4j schema — CORE indexes (Neo4j 5+ Cypher)\n")
        f.write("// Generated by tools/generate_neo4j_schema.py\n")
        f.write("// Use this file by default.\n\n")

        for entity in sorted(by_entity.keys()):
            rows_e = by_entity[entity]
            fields = [(r.get("field") or "").strip() for r in rows_e]
            fields = [x for x in fields if x]

            for field in fields:
                if field in core_fields:
                    iname = _safe_name(f"idx_{entity}_{field}")
                    f.write(f"CREATE INDEX {iname} IF NOT EXISTS FOR (n:`{entity}`) ON (n.`{field}`);\n")

    # Aggressive indexes
    with open(aggressive_indexes_path, "w", encoding="utf-8") as f:
        f.write("// LitigationOS Neo4j schema — AGGRESSIVE indexes (Neo4j 5+ Cypher)\n")
        f.write("// Generated by tools/generate_neo4j_schema.py\n")
        f.write("// Use only after import if you need maximum query performance.\n\n")

        for entity in sorted(by_entity.keys()):
            rows_e = by_entity[entity]
            fields = [(r.get("field") or "").strip() for r in rows_e]
            fields = [x for x in fields if x]

            # index all idish/timeish fields
            for field in fields:
                if is_idish(field) or is_timeish(field) or field in core_fields:
                    iname = _safe_name(f"idx_{entity}_{field}")
                    f.write(f"CREATE INDEX {iname} IF NOT EXISTS FOR (n:`{entity}`) ON (n.`{field}`);\n")

    # Optional Enterprise-only constraints (existence)
    with open(enterprise_path, "w", encoding="utf-8") as f:
        f.write("// LitigationOS Neo4j schema — Enterprise-only optional constraints\n")
        f.write("// These are commented out by default. Enable only if you have Enterprise Edition.\n\n")
        for entity in sorted(by_entity.keys()):
            pk = _pick_pk(entity, by_entity[entity])
            if pk:
                cname = _safe_name(f"x_req_{entity}_{pk}")
                f.write(f"// CREATE CONSTRAINT {cname} IF NOT EXISTS FOR (n:`{entity}`) REQUIRE n.`{pk}` IS NOT NULL;\n")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())

Patching `generate_graphir_templates` for pk selection

Next up, I need to patch the generate_graphir_templates to improve the primary key (pk) selection, just like we did earlier. Once that's done, I'll check to confirm that the changes were successfully applied and everything is working as expected.
Inspecting pk selection code in generate_graphir_templates

Always show details
bash -lc grep -n "_pick_pk" -n /mnt/data/_work_c3/LitigationOS_Blueprint_Pack_v2026-01-19.3/tools/generate_graphir_templates.py | head -n 80

36:def _pick_pk(entity: str, rows: list[dict]) -> str | None:
93:        pk = _pick_pk(entity, rows)
115:        start_pk = _pick_pk(from_entity, by_entity.get(from_entity, []))
116:        end_pk = _pick_pk(to_entity, by_entity.get(to_entity, []))

Patching generate_graphir_templates for pk selection

Always show details
bash -lc sed -n '36,70p' /mnt/data/_work_c3/LitigationOS_Blueprint_Pack_v2026-01-19.3/tools/generate_graphir_templates.py

def _pick_pk(entity: str, rows: list[dict]) -> str | None:
    # 1) notes include primary key
    for r in rows:
        notes = (r.get("notes") or "").lower()
        if "primary key" in notes:
            v = (r.get("field") or "").strip()
            return v or None

    # 2) <entity_lower>_id
    candidate = f"{entity.lower()}_id"
    for r in rows:
        if (r.get("field") or "").strip() == candidate:
            return candidate

    # 3) generic id
    for r in rows:
        if (r.get("field") or "").strip() == "id":
            return "id"

    # 4) first *_id field
    for r in rows:
        f = (r.get("field") or "").strip()
        if f.endswith("_id"):
            return f

    # 5) first field as last resort
    for r in rows:
        f = (r.get("field") or "").strip()
        if f:
            return f

    return None


def main() -> int:

Updating `INDEX.md` with the new README

Alright, the next step is to update the INDEX.md file to include the new README. I'll open it up now and make the necessary changes to ensure everything is current and accurately reflected. Let’s proceed with this update!
Opening INDEX.md for updates

Always show details
bash -lc sed -n '1,200p' /mnt/data/_work_c3/LitigationOS_Blueprint_Pack_v2026-01-19.3/INDEX.md

# LitigationOS Blueprint Pack — Index (v2026-01-19.3)

## Start here
- `LitigationOS_BLUEPRINT_README_v2026-01-19.3.md`

## Core model catalogs
- `model/field_catalog_superset.csv`
- `model/relationship_catalog_superset.csv`
- `model/entity_index.csv`
- `model/rel_index.csv`

## Human-readable dictionaries
- `docs/ERD_SUPERSET_FIELD_DICTIONARY_v2026-01-19.2.md`
- `docs/ENTITY_RELATIONSHIP_SUPERSET_INDEX_v2026-01-19.2.md`

## Build plan (bottom → top)
- `docs/BUILDPLAN_BOTTOM_TO_TOP_v2026-01-19.2.md`

## Graph contracts
- `docs/GRAPH_CONTRACTS_v2026-01-19.3.md`
- `schemas/entities/_registry.json`
- `schemas/entities/*.schema.json`

## Neo4j import and schema
- `templates/neo4j_admin_import/nodes/*_header.csv`
- `templates/neo4j_admin_import/rels/*_header.csv`
- `neo4j/schema_constraints.cypher`
- `neo4j/schema_indexes_core.cypher`
- `neo4j/schema_indexes_aggressive.cypher`

## Restartability
- `docs/SAVEPOINT_PROTOCOL_v2026-01-19.3.md`
- `savepoints/example/savepoint_C3_finalization.json`

## Cyclepack header harvest
- `docs/CSV_HEADER_HARVEST_FROM_UPLOADED_CYCLEPACKS_v2026-01-19.3.md`

## Diagrams
- `diagrams/erd_superset_overview_sfdp.png`
- `diagrams/erd_superset_cards_*.png`

Generating header harvest document and checking consistency

It looks like the header harvest document doesn’t exist yet, so I’ll generate it. While I’m at it, I should also make sure the savepoint file exists and is consistent. I’ll check the path to ensure everything is aligned and ready for the next steps.
Checking savepoint file and path consistency

Always show details
bash -lc ls -lh /mnt/data/_work_c3/LitigationOS_Blueprint_Pack_v2026-01-19.3/savepoints/example

total 1.5K
-rw-r--r-- 1 root root 1.3K Jan 20 03:55 savepoint_C2_schema_superset.json

Running generation pipeline

We need to create the savepoint_C3_finalization.json, but we can do that later after generating the required outputs. For now, we’ll proceed with the generation pipeline: schema emit, Neo4j schema creation, templates generation, harvesting zip headers, and validator runs. Let’s check if Python is available in the container environment — and it is! I'll run everything from the root of the pack.
Running generation pipeline and creating savepoint

Always show details
bash -lc set -euo pipefail
BASE='/mnt/data/_work_c3/LitigationOS_Blueprint_Pack_v2026-01-19.3'
cd "$BASE"

# Generate schemas
python tools/schema_emit.py --field-catalog model/field_catalog_superset.csv --out-dir schemas/entities

# Generate neo4j schema cypher scripts
python tools/generate_neo4j_schema.py --field-catalog model/field_catalog_superset.csv --out-dir neo4j

# Generate neo4j-admin import header templates
python tools/generate_graphir_templates.py --field-catalog model/field_catalog_superset.csv --rel-catalog model/relationship_catalog_superset.csv --out-dir templates/neo4j_admin_import

# Harvest CSV headers from uploaded ZIPs (read-only)
cat > /tmp/zip_list.txt <<'ZL'
/mnt/data/LITIGATIONOS_AUTHORITY_GRAPH_MERGE_GRAPHRAG_CYCLEPACK_20260107_164708.zip
/mnt/data/LITIGATIONOS_STATEMENT_FACT_PROV_AUTH_CYCLEPACK_20260107_181048.zip
/mnt/data/ETERNAL_GRAPH_BUNDLE_MASTER_LOCKED.zip
/mnt/data/EternalCodex_Complete.zip
/mnt/data/LITIGATIONOS__MASTERv1.0__v0009__FULL(2).zip
ZL
python tools/harvest_zip_csv_headers.py --zip-list /tmp/zip_list.txt --out docs/CSV_HEADER_HARVEST_FROM_UPLOADED_CYCLEPACKS_v2026-01-19.3.md

# Run validations; capture to report file as well
mkdir -p validation_reports
python tools/validate_all.py --base . --mode DRAFT | tee validation_reports/validation_report_DRAFT.txt
python tools/validate_all.py --base . --mode PCG | tee validation_reports/validation_report_PCG.txt

# Create savepoint C3
mkdir -p savepoints/example
cat > savepoints/example/savepoint_C3_finalization.json <<'JSON'
{
  "savepoint_id": "C3_finalization_v2026-01-19.3",
  "pack_version": "v2026-01-19.3",
  "stage": "FINALIZATION_AND_PACKAGING",
  "inputs": {
    "field_catalog": "model/field_catalog_superset.csv",
    "relationship_catalog": "model/relationship_catalog_superset.csv"
  },
  "derived_artifacts": {
    "schemas_registry": "schemas/entities/_registry.json",
    "schemas_dir": "schemas/entities/",
    "neo4j_constraints": "neo4j/schema_constraints.cypher",
    "neo4j_indexes_core": "neo4j/schema_indexes_core.cypher",
    "neo4j_indexes_aggressive": "neo4j/schema_indexes_aggressive.cypher",
    "neo4j_import_templates": "templates/neo4j_admin_import/",
    "validation_reports": "validation_reports/",
    "header_harvest": "docs/CSV_HEADER_HARVEST_FROM_UPLOADED_CYCLEPACKS_v2026-01-19.3.md"
  },
  "commands": [
    "python tools/schema_emit.py --field-catalog model/field_catalog_superset.csv --out-dir schemas/entities",
    "python tools/generate_neo4j_schema.py --field-catalog model/field_catalog_superset.csv --out-dir neo4j",
    "python tools/generate_graphir_templates.py --field-catalog model/field_catalog_superset.csv --rel-catalog model/relationship_catalog_superset.csv --out-dir templates/neo4j_admin_import",
    "python tools/validate_all.py --base . --mode PCG"
  ]
}
JSON

echo 'C3 generation complete.'

usage: harvest_zip_csv_headers.py [-h] --zip ZIPS --out OUT
harvest_zip_csv_headers.py: error: the following arguments are required: --zip

Inspecting harvest step failure

The command failed at the harvest step due to missing arguments in the harvest tool, specifically the --zip option. Looks like the pipeline ran the schema emit, Neo4j schema generation, and graphir templates, but failed during the harvest step. I'll check to confirm what was generated before the failure and resolve the issue.
Checking generated outputs before harvest failure

Always show details
bash -lc BASE='/mnt/data/_work_c3/LitigationOS_Blueprint_Pack_v2026-01-19.3'
ls -lh $BASE/schemas/entities | head
ls -lh $BASE/neo4j | sed -n '1,50p'
ls -lh $BASE/templates/neo4j_admin_import/nodes | head
ls -lh $BASE/templates/neo4j_admin_import/rels | head

total 739K
-rw-r--r-- 1 root root 4.9K Jan 20 04:44 ActionPlan.schema.json
-rw-r--r-- 1 root root 5.3K Jan 20 04:44 Address.schema.json
-rw-r--r-- 1 root root 5.4K Jan 20 04:44 Agent.schema.json
-rw-r--r-- 1 root root 6.2K Jan 20 04:44 Artifact.schema.json
-rw-r--r-- 1 root root 4.0K Jan 20 04:44 AtomStatementLink.schema.json
-rw-r--r-- 1 root root 6.1K Jan 20 04:44 AuthorityPinpoint.schema.json
-rw-r--r-- 1 root root 4.9K Jan 20 04:44 AuthoritySnapshot.schema.json
-rw-r--r-- 1 root root 5.5K Jan 20 04:44 AuthoritySource.schema.json
-rw-r--r-- 1 root root 4.9K Jan 20 04:44 BagItBag.schema.json
total 214K
-rw-r--r-- 1 root root  32K Jan 20 04:44 schema_constraints.cypher
-rw-r--r-- 1 root root  33K Jan 20 04:44 schema_enterprise_optional.cypher
-rw-r--r-- 1 root root 138K Jan 20 04:44 schema_indexes_aggressive.cypher
-rw-r--r-- 1 root root  13K Jan 20 04:44 schema_indexes_core.cypher
total 89K
-rw-r--r-- 1 root root 251 Jan 20 04:44 ActionPlan_header.csv
-rw-r--r-- 1 root root 250 Jan 20 04:44 Address_header.csv
-rw-r--r-- 1 root root 332 Jan 20 04:44 Agent_header.csv
-rw-r--r-- 1 root root 343 Jan 20 04:44 Artifact_header.csv
-rw-r--r-- 1 root root 327 Jan 20 04:44 AtomStatementLink_header.csv
-rw-r--r-- 1 root root 327 Jan 20 04:44 AuthorityPinpoint_header.csv
-rw-r--r-- 1 root root 285 Jan 20 04:44 AuthoritySnapshot_header.csv
-rw-r--r-- 1 root root 358 Jan 20 04:44 AuthoritySource_header.csv
-rw-r--r-- 1 root root 262 Jan 20 04:44 BagItBag_header.csv
total 550K
-rw-r--r-- 1 root root 24 Jan 20 04:44 ACTIVITY_IN_RUN_header.csv
-rw-r--r-- 1 root root 24 Jan 20 04:44 ADDR_IN_WORKSPACE_header.csv
-rw-r--r-- 1 root root 24 Jan 20 04:44 ARTIFACT_IN_WORKSPACE_header.csv
-rw-r--r-- 1 root root 24 Jan 20 04:44 ASSOC_ActionPlan_Case_Bundle_header.csv
-rw-r--r-- 1 root root 24 Jan 20 04:44 ASSOC_ActionPlan_Case_GateResult_header.csv
-rw-r--r-- 1 root root 24 Jan 20 04:44 ASSOC_ActionPlan_Case_Run_header.csv
-rw-r--r-- 1 root root 24 Jan 20 04:44 ASSOC_ActionPlan_GateResult_Bundle_header.csv
-rw-r--r-- 1 root root 24 Jan 20 04:44 ASSOC_ActionPlan_Run_Bundle_header.csv
-rw-r--r-- 1 root root 24 Jan 20 04:44 ASSOC_ActionPlan_Run_GateResult_header.csv

Verifying schema entities registry

It looks like some outputs have been generated successfully, which is good. Now, I need to check whether the schemas or entities have been properly registered in the _registry. This will help confirm that everything is in place before I proceed further. Let’s inspect that now.
Checking schema entities registry

Always show details
bash -lc tail -n 5 /mnt/data/_work_c3/LitigationOS_Blueprint_Pack_v2026-01-19.3/schemas/entities/_registry.json

      "schema": "Workspace.schema.json"
    }
  ],
  "schema_version": "2020-12"
}

Running harvest_zip_csv_headers with correct arguments

I need to run the harvest_zip_csv_headers tool using the correct list of zips — the six main zipped files and possibly LITIGATIONOS__MASTER. I’ll generate a document to include the unique columns and per-file details. Since the tool seems to accept repeated --zip arguments, I’ll check if that's right. Let’s inspect the tool setup first.
Running harvest_zip_csv_headers with multiple zips

Always show details
bash -lc sed -n '1,220p' /mnt/data/_work_c3/LitigationOS_Blueprint_Pack_v2026-01-19.3/tools/harvest_zip_csv_headers.py

#!/usr/bin/env python3
"""Harvest CSV headers from one or more ZIP files (read-only).

Writes a Markdown report including:
  - union of all discovered CSV columns
  - per-ZIP listing of CSV file headers

Usage:
  python tools/harvest_zip_csv_headers.py --out docs/CSV_HEADER_HARVEST_FROM_UPLOADED_CYCLEPACKS_v2026-01-19.3.md \
    --zip /path/to/a.zip --zip /path/to/b.zip

Notes:
  - Does not extract files to disk.
  - Reads the first non-empty line from each CSV as header.
"""

from __future__ import annotations

import argparse
import csv
import io
import os
import zipfile


def read_header_bytes(data: bytes) -> list[str]:
    # Try to sniff delimiter using a small sample
    sample = data[:4096].decode("utf-8", errors="replace")
    buf = io.StringIO(sample)
    try:
        dialect = csv.Sniffer().sniff(sample, delimiters=[",", "\t", ";", "|"])
        reader = csv.reader(buf, dialect)
    except csv.Error:
        buf.seek(0)
        reader = csv.reader(buf, delimiter=",")

    for row in reader:
        if row and any(c.strip() for c in row):
            return [c.strip() for c in row]
    return []


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--zip", action="append", dest="zips", required=True, help="ZIP file path (repeatable)")
    ap.add_argument("--out", required=True)
    args = ap.parse_args()

    zips = [os.path.abspath(p) for p in args.zips]

    per_zip: dict[str, dict[str, list[str]]] = {}
    all_cols: set[str] = set()
    total_csv = 0

    for zpath in zips:
        per_zip[zpath] = {}
        if not os.path.exists(zpath):
            continue
        with zipfile.ZipFile(zpath, "r") as z:
            for name in z.namelist():
                if not name.lower().endswith(".csv"):
                    continue
                try:
                    data = z.read(name)
                except Exception:
                    continue
                cols = read_header_bytes(data)
                per_zip[zpath][name] = cols
                total_csv += 1
                for c in cols:
                    if c:
                        all_cols.add(c)

    with open(args.out, "w", encoding="utf-8") as f:
        f.write("# CSV Header Harvest — Uploaded Cyclepacks (C3)\n\n")
        f.write(f"ZIPs scanned: {len(zips)}\n\n")
        for zpath in zips:
            f.write(f"- `{zpath}`\n")
        f.write("\n")
        f.write(f"CSV files found: {total_csv}\n\n")

        f.write("## Unique columns (union)\n\n")
        for c in sorted(all_cols):
            f.write(f"- `{c}`\n")

        f.write("\n## Per-ZIP headers\n\n")
        for zpath in zips:
            f.write(f"### `{zpath}`\n\n")
            files = per_zip.get(zpath, {})
            if not files:
                f.write("(no CSVs found or ZIP missing)\n\n")
                continue
            for name in sorted(files.keys()):
                cols = files[name]
                f.write(f"- `{name}`\n")
                if not cols:
                    f.write("  - (no header detected)\n")
                else:
                    f.write("  - " + ", ".join(f"`{c}`" for c in cols) + "\n")
            f.write("\n")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())

Running the task now

Alright, it's time to run it. I'll go ahead and initiate the process and see how it plays out. Fingers crossed everything works smoothly this time!
Harvesting CSV headers from ZIP files

Always show details
bash -lc set -euo pipefail
BASE='/mnt/data/_work_c3/LitigationOS_Blueprint_Pack_v2026-01-19.3'
cd "$BASE"
python tools/harvest_zip_csv_headers.py --out docs/CSV_HEADER_HARVEST_FROM_UPLOADED_CYCLEPACKS_v2026-01-19.3.md \
  --zip /mnt/data/LITIGATIONOS_AUTHORITY_GRAPH_MERGE_GRAPHRAG_CYCLEPACK_20260107_164708.zip \
  --zip /mnt/data/LITIGATIONOS_STATEMENT_FACT_PROV_AUTH_CYCLEPACK_20260107_181048.zip \
  --zip /mnt/data/ETERNAL_GRAPH_BUNDLE_MASTER_LOCKED.zip \
  --zip /mnt/data/EternalCodex_Complete.zip \
  --zip /mnt/data/LITIGATIONOS__MASTERv1.0__v0009__FULL(2).zip \
  --zip /mnt/data/LitigationOS_IntegratedLauncher_BucketOrchestrator_v2026-01-18.22_console_orchestrator_cyclepack_parallel(2).zip

echo 'Header harvest generated.'

bash: -c: line 9: syntax error near unexpected token `('

Fixing filename quoting issue

I noticed the filename "LITIGATIONOS__MASTERv1.0__v0009__FULL(2).zip" has parentheses, which means it needs quotes. I’ll make sure to rerun everything, properly quoting each path. Also, I’ll ensure there’s no truncation this time by using the correct formatting. Hopefully, this will solve the issue!
Quoting filenames with parentheses for processing

Always show details
bash -lc set -euo pipefail
BASE='/mnt/data/_work_c3/LitigationOS_Blueprint_Pack_v2026-01-19.3'
cd "$BASE"
python tools/harvest_zip_csv_headers.py --out docs/CSV_HEADER_HARVEST_FROM_UPLOADED_CYCLEPACKS_v2026-01-19.3.md \
  --zip "/mnt/data/LITIGATIONOS_AUTHORITY_GRAPH_MERGE_GRAPHRAG_CYCLEPACK_20260107_164708.zip" \
  --zip "/mnt/data/LITIGATIONOS_STATEMENT_FACT_PROV_AUTH_CYCLEPACK_20260107_181048.zip" \
  --zip "/mnt/data/ETERNAL_GRAPH_BUNDLE_MASTER_LOCKED.zip" \
  --zip "/mnt/data/EternalCodex_Complete.zip" \
  --zip "/mnt/data/LitigationOS_IntegratedLauncher_BucketOrchestrator_v2026-01-18.22_console_orchestrator_cyclepack_parallel(2).zip" \
  --zip "/mnt/data/LITIGATIONOS__MASTERv1.0__v0009__FULL(2).zip" \
  --zip "/mnt/data/LitigationOS_Module_Addendum_Pack_v2026-01-19(2).zip"

echo "Header harvest written."
wc -l docs/CSV_HEADER_HARVEST_FROM_UPLOADED_CYCLEPACKS_v2026-01-19.3.md | awk '{print "Lines:",$1}'

Header harvest written.
Lines: 476

Checking for successful output and document existence

The command was truncated, but the output shows 476 lines, which indicates that it succeeded. I need to double-check that the document file was created as expected. I’ll ensure everything’s there and move forward accordingly.
Verifying existence and previewing file output

Always show details
bash -lc BASE='/mnt/data/_work_c3/LitigationOS_Blueprint_Pack_v2026-01-19.3'
ls -lh "$BASE/docs/CSV_HEADER_HARVEST_FROM_UPLOADED_CYCLEPACKS_v2026-01-19.3.md"
head -n 30 "$BASE/docs/CSV_HEADER_HARVEST_FROM_UPLOADED_CYCLEPACKS_v2026-01-19.3.md"

-rw-r--r-- 1 root root 22K Jan 20 04:45 /mnt/data/_work_c3/LitigationOS_Blueprint_Pack_v2026-01-19.3/docs/CSV_HEADER_HARVEST_FROM_UPLOADED_CYCLEPACKS_v2026-01-19.3.md
# CSV Header Harvest — Uploaded Cyclepacks (C3)

ZIPs scanned: 7

- `/mnt/data/LITIGATIONOS_AUTHORITY_GRAPH_MERGE_GRAPHRAG_CYCLEPACK_20260107_164708.zip`
- `/mnt/data/LITIGATIONOS_STATEMENT_FACT_PROV_AUTH_CYCLEPACK_20260107_181048.zip`
- `/mnt/data/ETERNAL_GRAPH_BUNDLE_MASTER_LOCKED.zip`
- `/mnt/data/EternalCodex_Complete.zip`
- `/mnt/data/LitigationOS_IntegratedLauncher_BucketOrchestrator_v2026-01-18.22_console_orchestrator_cyclepack_parallel(2).zip`
- `/mnt/data/LITIGATIONOS__MASTERv1.0__v0009__FULL(2).zip`
- `/mnt/data/LitigationOS_Module_Addendum_Pack_v2026-01-19(2).zip`

CSV files found: 152

## Unique columns (union)

- `:END_ID`
- `:END_ID(Authority)`
- `:END_ID(AuthorityShard)`
- `:END_ID(FactClaim)`
- `:LABEL`
- `:START_ID`
- `:START_ID(Authority)`
- `:START_ID(Statement)`
- `:TYPE`
- `abs_path`
- `authority_id`
- `authority_id:ID(Authority)`
- `authority_path`
- `authority_pinpoint`

Running validation and storing results

Everything seems good to go. Now, I just need to run the validator in both DRAFT and PCG modes and store the report. The validation process writes output to validation_reports/validate_all_<mode>.md or similar. Let’s run it and make sure the reports are created as expected.
Running validator for DRAFT and PCG

Always show details
bash -lc set -euo pipefail
BASE='/mnt/data/_work_c3/LitigationOS_Blueprint_Pack_v2026-01-19.3'
cd "$BASE"
python tools/validate_all.py --base . --mode DRAFT
python tools/validate_all.py --base . --mode PCG
ls -lh validation_reports | sed -n '1,120p'

=== LitigationOS Validation Report ===
[ERROR] field_catalog: Duplicate field EXTRACTED_AuthorityRef.authority_ref_id
[ERROR] field_catalog: Duplicate field EXTRACTED_AuthorityRef.authority_ref_id
[ERROR] field_catalog: Duplicate field EXTRACTED_AuthorityRef.citation_key
[ERROR] field_catalog: Duplicate field EXTRACTED_AuthorityRef.citation_key
[ERROR] field_catalog: Duplicate field EXTRACTED_AuthorityRef.effective_end
[ERROR] field_catalog: Duplicate field EXTRACTED_AuthorityRef.effective_end
[ERROR] field_catalog: Duplicate field EXTRACTED_AuthorityRef.effective_start
[ERROR] field_catalog: Duplicate field EXTRACTED_AuthorityRef.effective_start
[ERROR] field_catalog: Duplicate field EXTRACTED_AuthorityRef.kind
[ERROR] field_catalog: Duplicate field EXTRACTED_AuthorityRef.kind
[ERROR] field_catalog: Duplicate field EXTRACTED_AuthorityRef.meta
[ERROR] field_catalog: Duplicate field EXTRACTED_AuthorityRef.meta
[ERROR] field_catalog: Duplicate field EXTRACTED_AuthorityRef.pin_ids
[ERROR] field_catalog: Duplicate field EXTRACTED_AuthorityRef.pin_ids
[ERROR] field_catalog: Duplicate field EXTRACTED_AuthorityRef.section_path
[ERROR] field_catalog: Duplicate field EXTRACTED_AuthorityRef.section_path
[ERROR] field_catalog: Duplicate field EXTRACTED_AuthorityRef.source_id
[ERROR] field_catalog: Duplicate field EXTRACTED_AuthorityRef.source_id
[ERROR] field_catalog: Duplicate field EXTRACTED_AuthorityRef.source_path
[ERROR] field_catalog: Duplicate field EXTRACTED_AuthorityRef.source_path
[ERROR] field_catalog: Duplicate field EXTRACTED_AuthorityRef.text_pointer
[ERROR] field_catalog: Duplicate field EXTRACTED_AuthorityRef.text_pointer
[ERROR] field_catalog: Duplicate field EXTRACTED_AuthoritySnapshotReceipt.generated_utc
[ERROR] field_catalog: Duplicate field EXTRACTED_AuthoritySnapshotReceipt.generated_utc
[ERROR] field_catalog: Duplicate field EXTRACTED_AuthoritySnapshotReceipt.inputs_sha256
[ERROR] field_catalog: Duplicate field EXTRACTED_AuthoritySnapshotReceipt.inputs_sha256
[ERROR] field_catalog: Duplicate field EXTRACTED_AuthoritySnapshotReceipt.outputs
[ERROR] field_catalog: Duplicate field EXTRACTED_AuthoritySnapshotReceipt.outputs
[ERROR] field_catalog: Duplicate field EXTRACTED_AuthoritySnapshotReceipt.pack_manifest_path
[ERROR] field_catalog: Duplicate field EXTRACTED_AuthoritySnapshotReceipt.pack_manifest_path
[ERROR] field_catalog: Duplicate field EXTRACTED_AuthoritySnapshotReceipt.snapshot_id
[ERROR] field_catalog: Duplicate field EXTRACTED_AuthoritySnapshotReceipt.snapshot_id
[ERROR] field_catalog: Duplicate field EXTRACTED_AuthoritySnapshotReceipt.tool
[ERROR] field_catalog: Duplicate field EXTRACTED_AuthoritySnapshotReceipt.tool
[ERROR] field_catalog: Duplicate field EXTRACTED_AuthoritySnapshotReceipt.tool_version
[ERROR] field_catalog: Duplicate field EXTRACTED_AuthoritySnapshotReceipt.tool_version
[ERROR] field_catalog: Duplicate field EXTRACTED_EC_AUTHORITY_MAP_CONSOLIDATED__codex_json_csv_extracted_csv.cite
[ERROR] field_catalog: Duplicate field EXTRACTED_EC_AUTHORITY_MAP_CONSOLIDATED__codex_json_csv_extracted_csv.cite
[ERROR] field_catalog: Duplicate field EXTRACTED_EC_AUTHORITY_MAP_CONSOLIDATED__codex_json_csv_extracted_csv.file
[ERROR] field_catalog: Duplicate field EXTRACTED_EC_AUTHORITY_MAP_CONSOLIDATED__codex_json_csv_extracted_csv.file
[ERROR] field_catalog: Duplicate field EXTRACTED_EC_AUTHORITY_MAP_CONSOLIDATED__codex_json_csv_extracted_csv.kind
[ERROR] field_catalog: Duplicate field EXTRACTED_EC_AUTHORITY_MAP_CONSOLIDATED__codex_json_csv_extracted_csv.kind
[ERROR] field_catalog: Duplicate field EXTRACTED_EC_AUTHORITY_MAP_CONSOLIDATED__codex_json_csv_extracted_csv.source_dir
[ERROR] field_catalog: Duplicate field EXTRACTED_EC_AUTHORITY_MAP_CONSOLIDATED__codex_json_csv_extracted_csv.source_dir
[ERROR] field_catalog: Duplicate field EXTRACTED_EC_AUTHORITY_MAP_CONSOLIDATED__codex_json_csv_extracted_csv.stream
[ERROR] field_catalog: Duplicate field EXTRACTED_EC_AUTHORITY_MAP_CONSOLIDATED__codex_json_csv_extracted_csv.stream
[ERROR] field_catalog: Duplicate field EXTRACTED_EC_AUTHORITY_MAP__codex_json_csv_extracted_csv.cite
[ERROR] field_catalog: Duplicate field EXTRACTED_EC_AUTHORITY_MAP__codex_json_csv_extracted_csv.cite
[ERROR] field_catalog: Duplicate field EXTRACTED_EC_AUTHORITY_MAP__codex_json_csv_extracted_csv.context
[ERROR] field_catalog: Duplicate field EXTRACTED_EC_AUTHORITY_MAP__codex_json_csv_extracted_csv.context
[ERROR] field_catalog: Duplicate field EXTRACTED_EC_AUTHORITY_MAP__codex_json_csv_extracted_csv.file
[ERROR] field_catalog: Duplicate field EXTRACTED_EC_AUTHORITY_MAP__codex_json_csv_extracted_csv.file
[ERROR] field_catalog: Duplicate field EXTRACTED_EC_AUTHORITY_MAP__codex_json_csv_extracted_csv.kind
[ERROR] field_catalog: Duplicate field EXTRACTED_EC_AUTHORITY_MAP__codex_json_csv_extracted_csv.kind
[ERROR] field_catalog: Duplicate field EXTRACTED_EC_AUTHORITY_MAP__codex_json_csv_extracted_csv.stream
[ERROR] field_catalog: Duplicate field EXTRACTED_EC_AUTHORITY_MAP__codex_json_csv_extracted_csv.stream
[ERROR] field_catalog: Duplicate field EXTRACTED_EC_HARM_INDEX_CONSOLIDATED__codex_json_csv_extracted_csv.file
[ERROR] field_catalog: Duplicate field EXTRACTED_EC_HARM_INDEX_CONSOLIDATED__codex_json_csv_extracted_csv.file
[ERROR] field_catalog: Duplicate field EXTRACTED_EC_HARM_INDEX_CONSOLIDATED__codex_json_csv_extracted_csv.source_dir
[ERROR] field_catalog: Duplicate field EXTRACTED_EC_HARM_INDEX_CONSOLIDATED__codex_json_csv_extracted_csv.source_dir
[ERROR] field_catalog: Duplicate field EXTRACTED_EC_HARM_INDEX_CONSOLIDATED__codex_json_csv_extracted_csv.stream
[ERROR] field_catalog: Duplicate field EXTRACTED_EC_HARM_INDEX_CONSOLIDATED__codex_json_csv_extracted_csv.stream
[ERROR] field_catalog: Duplicate field EXTRACTED_EC_HARM_INDEX_CONSOLIDATED__codex_json_csv_extracted_csv.topic
[ERROR] field_catalog: Duplicate field EXTRACTED_EC_HARM_INDEX_CONSOLIDATED__codex_json_csv_extracted_csv.topic
[ERROR] field_catalog: Duplicate field EXTRACTED_EC_HARM_INDEX__codex_json_csv_extracted_csv.case_refs
[ERROR] field_catalog: Duplicate field EXTRACTED_EC_HARM_INDEX__codex_json_csv_extracted_csv.case_refs
[ERROR] field_catalog: Duplicate field EXTRACTED_EC_HARM_INDEX__codex_json_csv_extracted_csv.dates_found
[ERROR] field_catalog: Duplicate field EXTRACTED_EC_HARM_INDEX__codex_json_csv_extracted_csv.dates_found
[ERROR] field_catalog: Duplicate field EXTRACTED_EC_HARM_INDEX__codex_json_csv_extracted_csv.detected_authorities
[ERROR] field_catalog: Duplicate field EXTRACTED_EC_HARM_INDEX__codex_json_csv_extracted_csv.detected_authorities
[ERROR] field_catalog: Duplicate field EXTRACTED_EC_HARM_INDEX__codex_json_csv_extracted_csv.evidence_snippets
[ERROR] field_catalog: Duplicate field EXTRACTED_EC_HARM_INDEX__codex_json_csv_extracted_csv.evidence_snippets
[ERROR] field_catalog: Duplicate field EXTRACTED_EC_HARM_INDEX__codex_json_csv_extracted_csv.file
[ERROR] field_catalog: Duplicate field EXTRACTED_EC_HARM_INDEX__codex_json_csv_extracted_csv.file
[ERROR] field_catalog: Duplicate field EXTRACTED_EC_HARM_INDEX__codex_json_csv_extracted_csv.judges
[ERROR] field_catalog: Duplicate field EXTRACTED_EC_HARM_INDEX__codex_json_csv_extracted_csv.judges
[ERROR] field_catalog: Duplicate field EXTRACTED_EC_HARM_INDEX__codex_json_csv_extracted_csv.ppo_flag
[ERROR] field_catalog: Duplicate field EXTRACTED_EC_HARM_INDEX__codex_json_csv_extracted_csv.ppo_flag
[ERROR] field_catalog: Duplicate field EXTRACTED_EC_HARM_INDEX__codex_json_csv_extracted_csv.stream
[ERROR] field_catalog: Duplicate field EXTRACTED_EC_HARM_INDEX__codex_json_csv_extracted_csv.stream
[ERROR] field_catalog: Duplicate field EXTRACTED_EC_HARM_INDEX__codex_json_csv_extracted_csv.suggested_relief
[ERROR] field_catalog: Duplicate field EXTRACTED_EC_HARM_INDEX__codex_json_csv_extracted_csv.suggested_relief
[ERROR] field_catalog: Duplicate field EXTRACTED_EC_INDEX (1)__codex_json_csv_extracted_csv.abs_path
[ERROR] field_catalog: Duplicate field EXTRACTED_EC_INDEX (1)__codex_json_csv_extracted_csv.abs_path
[ERROR] field_catalog: Duplicate field EXTRACTED_EC_INDEX (1)__codex_json_csv_extracted_csv.pages
[ERROR] field_catalog: Duplicate field EXTRACTED_EC_INDEX (1)__codex_json_csv_extracted_csv.pages
[ERROR] field_catalog: Duplicate field EXTRACTED_EC_INDEX (1)__codex_json_csv_extracted_csv.parse_error
[ERROR] field_catalog: Duplicate field EXTRACTED_EC_INDEX (1)__codex_json_csv_extracted_csv.parse_error
[ERROR] field_catalog: Duplicate field EXTRACTED_EC_INDEX (1)__codex_json_csv_extracted_csv.rel_path
[ERROR] field_catalog: Duplicate field EXTRACTED_EC_INDEX (1)__codex_json_csv_extracted_csv.rel_path
[ERROR] field_catalog: Duplicate field EXTRACTED_EC_INDEX (1)__codex_json_csv_extracted_csv.sha256
[ERROR] field_catalog: Duplicate field EXTRACTED_EC_INDEX (1)__codex_json_csv_extracted_csv.sha256
[ERROR] field_catalog: Duplicate field EXTRACTED_EC_INDEX (1)__codex_json_csv_extracted_csv.size_bytes
[ERROR] field_catalog: Duplicate field EXTRACTED_EC_INDEX (1)__codex_json_csv_extracted_csv.size_bytes
[ERROR] field_catalog: Duplicate field EXTRACTED_EC_INDEX (1)__codex_json_csv_extracted_csv.text_chars
[ERROR] field_catalog: Duplicate field EXTRACTED_EC_INDEX (1)__codex_json_csv_extracted_csv.text_chars
[ERROR] field_catalog: Duplicate field EXTRACTED_EC_INDEX (1)__codex_json_csv_extracted_csv.type
[ERROR] field_catalog: Duplicate field EXTRACTED_EC_INDEX (1)__codex_json_csv_extracted_csv.type
[ERROR] field_catalog: Duplicate field EXTRACTED_EC_RELIEF_SUGGEST__codex_json_csv_extracted_csv.count
[ERROR] field_catalog: Duplicate field EXTRACTED_EC_RELIEF_SUGGEST__codex_json_csv_extracted_csv.count
[ERROR] field_catalog: Duplicate field EXTRACTED_EC_RELIEF_SUGGEST__codex_json_csv_extracted_csv.relief
[ERROR] field_catalog: Duplicate field EXTRACTED_EC_RELIEF_SUGGEST__codex_json_csv_extracted_csv.relief
[ERROR] field_catalog: Duplicate field EXTRACTED_EC_RELIEF_SUGGEST__codex_json_csv_extracted_csv.stream
[ERROR] field_catalog: Duplicate field EX[... ELLIPSIZATION ...]sv.id:ID
[ERROR] field_catalog: Duplicate field EXTRACTED_neo4j_nodes (3)__codex_json_csv_extracted_csv.id:ID
[ERROR] field_catalog: Duplicate field EXTRACTED_neo4j_nodes (3)__codex_json_csv_extracted_csv.name
[ERROR] field_catalog: Duplicate field EXTRACTED_neo4j_nodes (3)__codex_json_csv_extracted_csv.name
[ERROR] field_catalog: Duplicate field EXTRACTED_neo4j_nodes (3)__codex_json_csv_extracted_csv.type
[ERROR] field_catalog: Duplicate field EXTRACTED_neo4j_nodes (3)__codex_json_csv_extracted_csv.type
[ERROR] field_catalog: Duplicate field EXTRACTED_neo4j_nodes_FINAL__codex_json_csv_extracted_csv.group
[ERROR] field_catalog: Duplicate field EXTRACTED_neo4j_nodes_FINAL__codex_json_csv_extracted_csv.group
[ERROR] field_catalog: Duplicate field EXTRACTED_neo4j_nodes_FINAL__codex_json_csv_extracted_csv.id:ID
[ERROR] field_catalog: Duplicate field EXTRACTED_neo4j_nodes_FINAL__codex_json_csv_extracted_csv.id:ID
[ERROR] field_catalog: Duplicate field EXTRACTED_neo4j_nodes_FINAL__codex_json_csv_extracted_csv.label
[ERROR] field_catalog: Duplicate field EXTRACTED_neo4j_nodes_FINAL__codex_json_csv_extracted_csv.label
[ERROR] field_catalog: Duplicate field EXTRACTED_neo4j_nodes_FINAL__codex_json_csv_extracted_csv.meta:json
[ERROR] field_catalog: Duplicate field EXTRACTED_neo4j_nodes_FINAL__codex_json_csv_extracted_csv.meta:json
[ERROR] field_catalog: Duplicate field EXTRACTED_neo4j_nodes_FINAL__codex_json_csv_extracted_csv.size:int
[ERROR] field_catalog: Duplicate field EXTRACTED_neo4j_nodes_FINAL__codex_json_csv_extracted_csv.size:int
[ERROR] field_catalog: Duplicate field EXTRACTED_neo4j_nodes_FINAL__codex_json_csv_extracted_csv.type
[ERROR] field_catalog: Duplicate field EXTRACTED_neo4j_nodes_FINAL__codex_json_csv_extracted_csv.type
[ERROR] field_catalog: Duplicate field EXTRACTED_neo4j_nodes_FINAL__codex_json_csv_extracted_csv.url
[ERROR] field_catalog: Duplicate field EXTRACTED_neo4j_nodes_FINAL__codex_json_csv_extracted_csv.url
[ERROR] field_catalog: Duplicate field EXTRACTED_nodes:authorities.:LABEL
[ERROR] field_catalog: Duplicate field EXTRACTED_nodes:authorities.group
[ERROR] field_catalog: Duplicate field EXTRACTED_nodes:authorities.id:ID
[ERROR] field_catalog: Duplicate field EXTRACTED_nodes:authorities.label
[ERROR] field_catalog: Duplicate field EXTRACTED_nodes:authorities.tokens
[ERROR] field_catalog: Duplicate field EXTRACTED_nodes:authority.authority_id:ID(Authority)
[ERROR] field_catalog: Duplicate field EXTRACTED_nodes:authority.authority_id:ID(Authority)
[ERROR] field_catalog: Duplicate field EXTRACTED_nodes:authority.authority_type
[ERROR] field_catalog: Duplicate field EXTRACTED_nodes:authority.authority_type
[ERROR] field_catalog: Duplicate field EXTRACTED_nodes:authority.citation
[ERROR] field_catalog: Duplicate field EXTRACTED_nodes:authority.citation
[ERROR] field_catalog: Duplicate field EXTRACTED_nodes:authority_prior.authority_id:ID(Authority)
[ERROR] field_catalog: Duplicate field EXTRACTED_nodes:authority_prior.authority_type
[ERROR] field_catalog: Duplicate field EXTRACTED_nodes:authority_prior.citation
[ERROR] field_catalog: Duplicate field EXTRACTED_nodes:authority_shard.authority_id
[ERROR] field_catalog: Duplicate field EXTRACTED_nodes:authority_shard.authority_id
[ERROR] field_catalog: Duplicate field EXTRACTED_nodes:authority_shard.citation
[ERROR] field_catalog: Duplicate field EXTRACTED_nodes:authority_shard.pinpoint
[ERROR] field_catalog: Duplicate field EXTRACTED_nodes:authority_shard.pinpoint
[ERROR] field_catalog: Duplicate field EXTRACTED_nodes:authority_shard.row_id
[ERROR] field_catalog: Duplicate field EXTRACTED_nodes:authority_shard.shard_id:ID(AuthorityShard)
[ERROR] field_catalog: Duplicate field EXTRACTED_nodes:authority_shard.shard_id:ID(AuthorityShard)
[ERROR] field_catalog: Duplicate field EXTRACTED_nodes:authority_shard.source
[ERROR] field_catalog: Duplicate field EXTRACTED_nodes:authority_shard.source
[ERROR] field_catalog: Duplicate field EXTRACTED_nodes:authority_shard.status
[ERROR] field_catalog: Duplicate field EXTRACTED_nodes:authority_shard.text
[ERROR] field_catalog: Duplicate field EXTRACTED_nodes:authority_shard.text
[ERROR] field_catalog: Duplicate field EXTRACTED_nodes:authority_shard_prior.authority_id
[ERROR] field_catalog: Duplicate field EXTRACTED_nodes:authority_shard_prior.citation
[ERROR] field_catalog: Duplicate field EXTRACTED_nodes:authority_shard_prior.row_id
[ERROR] field_catalog: Duplicate field EXTRACTED_nodes:authority_shard_prior.shard_id:ID(AuthorityShard)
[ERROR] field_catalog: Duplicate field EXTRACTED_nodes:authority_shard_prior.status
[ERROR] field_catalog: Duplicate field EXTRACTED_nodes_csv.case_id
[ERROR] field_catalog: Duplicate field EXTRACTED_nodes_csv.case_id
[ERROR] field_catalog: Duplicate field EXTRACTED_nodes_csv.case_id
[ERROR] field_catalog: Duplicate field EXTRACTED_nodes_csv.case_id
[ERROR] field_catalog: Duplicate field EXTRACTED_nodes_csv.created_utc
[ERROR] field_catalog: Duplicate field EXTRACTED_nodes_csv.created_utc
[ERROR] field_catalog: Duplicate field EXTRACTED_nodes_csv.created_utc
[ERROR] field_catalog: Duplicate field EXTRACTED_nodes_csv.created_utc
[ERROR] field_catalog: Duplicate field EXTRACTED_nodes_csv.id
[ERROR] field_catalog: Duplicate field EXTRACTED_nodes_csv.id
[ERROR] field_catalog: Duplicate field EXTRACTED_nodes_csv.id
[ERROR] field_catalog: Duplicate field EXTRACTED_nodes_csv.id
[ERROR] field_catalog: Duplicate field EXTRACTED_nodes_csv.labels
[ERROR] field_catalog: Duplicate field EXTRACTED_nodes_csv.labels
[ERROR] field_catalog: Duplicate field EXTRACTED_nodes_csv.labels
[ERROR] field_catalog: Duplicate field EXTRACTED_nodes_csv.labels
[ERROR] field_catalog: Duplicate field EXTRACTED_nodes_csv.source_locator
[ERROR] field_catalog: Duplicate field EXTRACTED_nodes_csv.source_locator
[ERROR] field_catalog: Duplicate field EXTRACTED_nodes_csv.source_locator
[ERROR] field_catalog: Duplicate field EXTRACTED_nodes_csv.source_locator
[ERROR] field_catalog: Duplicate field EXTRACTED_nodes_csv.source_path
[ERROR] field_catalog: Duplicate field EXTRACTED_nodes_csv.source_path
[ERROR] field_catalog: Duplicate field EXTRACTED_nodes_csv.source_path
[ERROR] field_catalog: Duplicate field EXTRACTED_nodes_csv.source_path
[ERROR] field_catalog: Duplicate field EXTRACTED_nodes_csv.track
[ERROR] field_catalog: Duplicate field EXTRACTED_nodes_csv.track
[ERROR] field_catalog: Duplicate field EXTRACTED_nodes_csv.track
[ERROR] field_catalog: Duplicate field EXTRACTED_nodes_csv.track
[ERROR] field_catalog: Duplicate field EXTRACTED_nodes_csv.updated_utc
[ERROR] field_catalog: Duplicate field EXTRACTED_nodes_csv.updated_utc
[ERROR] field_catalog: Duplicate field EXTRACTED_nodes_csv.updated_utc
[ERROR] field_catalog: Duplicate field EXTRACTED_nodes_csv.updated_utc
[ERROR] field_catalog: Duplicate field EXTRACTED_rules_extracted_csv.chapter
[ERROR] field_catalog: Duplicate field EXTRACTED_rules_extracted_csv.chapter
[ERROR] field_catalog: Duplicate field EXTRACTED_rules_extracted_csv.context
[ERROR] field_catalog: Duplicate field EXTRACTED_rules_extracted_csv.context
[ERROR] field_catalog: Duplicate field EXTRACTED_rules_extracted_csv.rule
[ERROR] field_catalog: Duplicate field EXTRACTED_rules_extracted_csv.rule
[ERROR] field_catalog: Duplicate field EXTRACTED_rules_extracted_csv.source_doc
[ERROR] field_catalog: Duplicate field EXTRACTED_rules_extracted_csv.source_doc
[ERROR] field_catalog: Duplicate field EXTRACTED_scao_forms_master__codex_json_csv_extracted_csv.citations
[ERROR] field_catalog: Duplicate field EXTRACTED_scao_forms_master__codex_json_csv_extracted_csv.citations
[ERROR] field_catalog: Duplicate field EXTRACTED_scao_forms_master__codex_json_csv_extracted_csv.code
[ERROR] field_catalog: Duplicate field EXTRACTED_scao_forms_master__codex_json_csv_extracted_csv.code
[ERROR] field_catalog: Duplicate field EXTRACTED_scao_forms_master__codex_json_csv_extracted_csv.court
[ERROR] field_catalog: Duplicate field EXTRACTED_scao_forms_master__codex_json_csv_extracted_csv.court
[ERROR] field_catalog: Duplicate field EXTRACTED_scao_forms_master__codex_json_csv_extracted_csv.form_id
[ERROR] field_catalog: Duplicate field EXTRACTED_scao_forms_master__codex_json_csv_extracted_csv.form_id
[ERROR] field_catalog: Duplicate field EXTRACTED_scao_forms_master__codex_json_csv_extracted_csv.source_url
[ERROR] field_catalog: Duplicate field EXTRACTED_scao_forms_master__codex_json_csv_extracted_csv.source_url
[ERROR] field_catalog: Duplicate field EXTRACTED_scao_forms_master__codex_json_csv_extracted_csv.title
[ERROR] field_catalog: Duplicate field EXTRACTED_scao_forms_master__codex_json_csv_extracted_csv.title
[ERROR] field_catalog: Duplicate field EXTRACTED_score_row.confidence
[ERROR] field_catalog: Duplicate field EXTRACTED_score_row.created_utc
[ERROR] field_catalog: Duplicate field EXTRACTED_score_row.feasibility
[ERROR] field_catalog: Duplicate field EXTRACTED_score_row.impact
[ERROR] field_catalog: Duplicate field EXTRACTED_score_row.item_id
[ERROR] field_catalog: Duplicate field EXTRACTED_score_row.priority
[ERROR] field_catalog: Duplicate field EXTRACTED_score_row.risk
[ERROR] field_catalog: Duplicate field EXTRACTED_signal_row.atoms
[ERROR] field_catalog: Duplicate field EXTRACTED_signal_row.created_utc
[ERROR] field_catalog: Duplicate field EXTRACTED_signal_row.kind
[ERROR] field_catalog: Duplicate field EXTRACTED_signal_row.score
[ERROR] field_catalog: Duplicate field EXTRACTED_signal_row.signal_id
[ERROR] field_catalog: Duplicate field EXTRACTED_signal_row.text
[ERROR] field_catalog: Duplicate field EXTRACTED_vehicle_row.created_utc
[ERROR] field_catalog: Duplicate field EXTRACTED_vehicle_row.lane
[ERROR] field_catalog: Duplicate field EXTRACTED_vehicle_row.missing_authority
[ERROR] field_catalog: Duplicate field EXTRACTED_vehicle_row.status
[ERROR] field_catalog: Duplicate field EXTRACTED_vehicle_row.vehicle
[ERROR] field_catalog: Duplicate field EXTRACTED_vehicle_row.vehicle_id
Total: 638 issues; 638 errors

Adjusting validator to handle duplicates appropriately

The validator is currently too strict, flagging duplicates in the field catalog as errors—though these duplicates come from model extraction, not actual issues. In DRAFT mode, duplicates should just trigger a warning, and in PCG, they should block. I'll revise the validation logic to reflect that. Also, the command failed because of a non-zero exit code, which stopped the PCG run. I’ll adjust it to run both and capture the errors properly.
Patching validate_all for DRAFT/PCG validation handling

I will patch validate_all so that in DRAFT, duplicates show as warnings but don't cause errors (exit 0), and the report still shows them. In PCG mode, duplicates will cause errors (exit 1). To proceed with the packaging even after failures, I can use || true to bypass the error. For finalization, I’ll include a validation report showing the PCG duplication issue, though the user prefers no placeholders and ideally wants the PCG to pass. We could also deduplicate the field catalog automatically.
Implementing field catalog deduplication for deterministic output

We should create a model/field_catalog_superset_dedup.csv and build schemas based on deduplicated data. All scripts will be updated to use the deduped version moving forward. This wouldn’t change deliverables as it’s an improvement, not a destructive change. We’ll keep the original and add the dedup version. To ensure deterministic results, we need to implement tools/dedupe_field_catalog.py, which will merge duplicates by uniting conflicting columns. A new deduped file will be produced and readme updated accordingly.
Finalizing deduplication and validation adjustments

I’ll re-run schema generation and Neo4j schema creation using the deduped file to eliminate duplicates and satisfy the validator. The current validator checks the original file, which will still generate errors. To fix this, I'm updating the validator to accept the deduped file or treat original duplicates as warnings. We’ll maintain both versions and ensure the pipeline uses the dedup file in PCG. I’ll implement tools/dedupe_field_catalog.py to produce the dedup CSV and a report. Additionally, I’ll update related documentation accordingly.
Implementing deduplication and validation fixes

We need to regenerate outputs using the deduped file and overwrite the old outputs. In DRAFT, the validator will warn about duplicates in the original file, while in PCG, it will require the deduped file and ensure consistency. I’ll create the dedup file, update validate_all, and ensure it validates deduped files, making original duplicates warnings. After that, I’ll patch the validator, rerun DRAFT and PCG, and update documentation to align with these changes. Let's go ahead and do this!
Implementing field catalog deduplication and validation adjustments

Always show details
bash -lc set -euo pipefail
BASE='/mnt/data/_work_c3/LitigationOS_Blueprint_Pack_v2026-01-19.3'

cat > "$BASE/tools/dedupe_field_catalog.py" <<'PY'
#!/usr/bin/env python3
"""Deduplicate field catalog rows (entity+field) into a stable, loss-minimizing CSV.

Why: Upstream extractions sometimes emit repeated (entity, field) rows. This breaks
schema emission, import header templates, and uniqueness/index planners.

Output:
  - model/field_catalog_superset_dedup.csv
  - validation_reports/field_catalog_dedupe_report.md

Merge logic (deterministic):
  - Key = (entity, field)
  - For each column:
      - take first non-empty value; if later non-empty differs, append to a
        pipe-delimited "conflicts" cell in the report, and preserve earliest.
  - notes are concatenated (unique) with ' | '

This is read-only with respect to the original catalog.
"""

from __future__ import annotations

import argparse
import csv
import os
from collections import defaultdict


def norm(v: str | None) -> str:
    return (v or "").strip()


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--in", dest="inp", required=True)
    ap.add_argument("--out", dest="out", required=True)
    ap.add_argument("--report", required=True)
    args = ap.parse_args()

    if not os.path.exists(args.inp):
        raise SystemExit(f"missing input: {args.inp}")

    with open(args.inp, "r", encoding="utf-8", newline="") as f:
        reader = csv.DictReader(f)
        cols = reader.fieldnames or []
        rows = list(reader)

    # Preserve column order, but ensure required fields exist for downstream tools
    required_cols = ["entity", "field", "type", "required", "notes"]
    for c in required_cols:
        if c not in cols:
            cols.append(c)

    grouped: dict[tuple[str, str], list[dict]] = defaultdict(list)
    for r in rows:
        k = (norm(r.get("entity")), norm(r.get("field")))
        if not k[0] or not k[1]:
            continue
        grouped[k].append(r)

    dedup_rows: list[dict] = []
    conflict_log: list[str] = []
    merged_note_count = 0

    for (entity, field) in sorted(grouped.keys()):
        items = grouped[(entity, field)]
        base = {c: "" for c in cols}
        base["entity"] = entity
        base["field"] = field

        # Merge notes specially
        notes_set = []
        for it in items:
            n = norm(it.get("notes"))
            if n and n not in notes_set:
                notes_set.append(n)
        if notes_set:
            merged_note_count += 1
            base["notes"] = " | ".join(notes_set)

        # Merge other columns: first non-empty wins, record conflicts
        for c in cols:
            if c in ("entity", "field", "notes"):
                continue
            seen = []
            for it in items:
                v = norm(it.get(c))
                if v:
                    seen.append(v)
            if not seen:
                continue
            base[c] = seen[0]
            # conflicts if more than one distinct non-empty
            distinct = []
            for v in seen:
                if v not in distinct:
                    distinct.append(v)
            if len(distinct) > 1:
                conflict_log.append(f"- **{entity}.{field}** column `{c}` conflicts: {distinct}")

        dedup_rows.append(base)

    # Write CSV
    os.makedirs(os.path.dirname(args.out), exist_ok=True)
    with open(args.out, "w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=cols)
        w.writeheader()
        w.writerows(dedup_rows)

    # Report
    os.makedirs(os.path.dirname(args.report), exist_ok=True)
    with open(args.report, "w", encoding="utf-8") as f:
        f.write("# Field Catalog Deduplication Report (C3)\n\n")
        f.write(f"Input rows: {len(rows)}\n\n")
        f.write(f"Unique (entity, field) keys: {len(dedup_rows)}\n\n")
        f.write(f"Rows removed by dedupe: {len(rows) - len(dedup_rows)}\n\n")
        f.write(f"Merged-notes keys: {merged_note_count}\n\n")
        f.write("## Conflicts (first-wins, logged)\n\n")
        if conflict_log:
            f.write("\n".join(conflict_log) + "\n")
        else:
            f.write("(none detected)\n")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
PY
chmod +x "$BASE/tools/dedupe_field_catalog.py"

# Patch validate_all to use dedup catalog if present; treat duplicates as warnings in DRAFT and as errors only if dedup missing in PCG
cat > "$BASE/tools/validate_all.py" <<'PY'
#!/usr/bin/env python3
"""Validate the LitigationOS blueprint pack (contracts, templates, and scripts).

Modes:
  - DRAFT: fail-soft; emit warnings for recoverable issues; exit 0 unless catastrophic.
  - PCG: fail-closed for execution-critical issues; exit 1 on any core blocking issue.

This validator is intentionally file-system based and does not require Neo4j.
"""

from __future__ import annotations

import argparse
import csv
import json
import os
import sys
from dataclasses import dataclass
from typing import Callable


@dataclass
class Issue:
    level: str  # INFO/WARN/ERROR
    code: str
    message: str


def eprint(*a: object) -> None:
    print(*a, file=sys.stderr)


def load_csv(path: str) -> tuple[list[str], list[dict]]:
    with open(path, "r", encoding="utf-8", newline="") as f:
        reader = csv.DictReader(f)
        cols = reader.fieldnames or []
        rows = list(reader)
    return cols, rows


def check_field_catalog(path: str, mode: str) -> list[Issue]:
    issues: list[Issue] = []
    if not os.path.exists(path):
        issues.append(Issue("ERROR", "FIELD_CATALOG_MISSING", f"Missing: {path}"))
        return issues

    cols, rows = load_csv(path)
    if "entity" not in cols or "field" not in cols:
        issues.append(Issue("ERROR", "FIELD_CATALOG_BAD_COLUMNS", "field_catalog missing entity/field columns"))
        return issues

    seen: set[tuple[str, str]] = set()
    dups = 0
    for r in rows:
        k = ((r.get("entity") or "").strip(), (r.get("field") or "").strip())
        if not k[0] or not k[1]:
            continue
        if k in seen:
            dups += 1
        else:
            seen.add(k)

    if dups:
        lvl = "WARN" if mode == "DRAFT" else "ERROR"
        issues.append(Issue(lvl, "FIELD_CATALOG_DUP_KEYS", f"Duplicate (entity,field) rows: {dups}"))

    return issues


def check_schema_registry(base: str) -> list[Issue]:
    issues: list[Issue] = []
    reg = os.path.join(base, "schemas", "entities", "_registry.json")
    if not os.path.exists(reg):
        issues.append(Issue("ERROR", "SCHEMA_REGISTRY_MISSING", f"Missing: {reg}"))
        return issues

    try:
        with open(reg, "r", encoding="utf-8") as f:
            obj = json.load(f)
    except Exception as ex:
        issues.append(Issue("ERROR", "SCHEMA_REGISTRY_BAD_JSON", f"Could not parse registry: {ex}"))
        return issues

    entities = obj.get("entities")
    if not isinstance(entities, list) or not entities:
        issues.append(Issue("ERROR", "SCHEMA_REGISTRY_EMPTY", "Registry.entities missing/empty"))
        return issues

    missing = 0
    for ent in entities:
        schema = ent.get("schema")
        if not schema:
            continue
        spath = os.path.join(base, "schemas", "entities", schema)
        if not os.path.exists(spath):
            missing += 1
    if missing:
        issues.append(Issue("ERROR", "SCHEMA_FILES_MISSING", f"Schemas missing: {missing}"))

    return issues


def check_templates(base: str) -> list[Issue]:
    issues: list[Issue] = []
    nd = os.path.join(base, "templates", "neo4j_admin_import", "nodes")
    rd = os.path.join(base, "templates", "neo4j_admin_import", "rels")

    if not os.path.isdir(nd):
        issues.append(Issue("ERROR", "NODES_TEMPLATE_DIR_MISSING", f"Missing: {nd}"))
    else:
        files = [f for f in os.listdir(nd) if f.endswith("_header.csv")]
        if not files:
            issues.append(Issue("ERROR", "NODES_TEMPLATES_EMPTY", "No node header templates found"))

    if not os.path.isdir(rd):
        issues.append(Issue("ERROR", "RELS_TEMPLATE_DIR_MISSING", f"Missing: {rd}"))
    else:
        files = [f for f in os.listdir(rd) if f.endswith("_header.csv")]
        if not files:
            issues.append(Issue("ERROR", "RELS_TEMPLATES_EMPTY", "No relationship header templates found"))

    return issues


def check_neo4j_schema_files(base: str) -> list[Issue]:
    issues: list[Issue] = []
    nd = os.path.join(base, "neo4j")
    need = [
        "schema_constraints.cypher",
        "schema_indexes_core.cypher",
        "schema_indexes_aggressive.cypher",
        "schema_enterprise_optional.cypher",
    ]
    for n in need:
        p = os.path.join(nd, n)
        if not os.path.exists(p):
            issues.append(Issue("ERROR", "NEO4J_SCHEMA_MISSING", f"Missing: {p}"))
    return issues


def write_report(base: str, mode: str, issues: list[Issue]) -> str:
    os.makedirs(os.path.join(base, "validation_reports"), exist_ok=True)
    out = os.path.join(base, "validation_reports", f"validate_all_{mode}.md")
    errs = sum(1 for i in issues if i.level == "ERROR")
    warns = sum(1 for i in issues if i.level == "WARN")

    with open(out, "w", encoding="utf-8") as f:
        f.write(f"# LitigationOS Validation Report ({mode})\n\n")
        f.write(f"Errors: {errs}\\n\nWarnings: {warns}\\n\n")
        f.write("## Issues\n\n")
        for i in issues:
            f.write(f"- **{i.level}** `{i.code}` — {i.message}\n")
    return out


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--base", required=True)
    ap.add_argument("--mode", choices=["DRAFT", "PCG"], required=True)
    args = ap.parse_args()

    base = os.path.abspath(args.base)
    mode = args.mode

    issues: list[Issue] = []

    # Field catalog checks:
    fc = os.path.join(base, "model", "field_catalog_superset.csv")
    fcd = os.path.join(base, "model", "field_catalog_superset_dedup.csv")

    issues.extend(check_field_catalog(fc, mode))

    # In PCG, require dedup catalog (so downstream generation can be deterministic)
    if mode == "PCG":
        if not os.path.exists(fcd):
            issues.append(Issue("ERROR", "FIELD_CATALOG_DEDUP_MISSING", f"Missing: {fcd} (run tools/dedupe_field_catalog.py)"))
        else:
            issues.extend(check_field_catalog(fcd, mode))

    issues.extend(check_schema_registry(base))
    issues.extend(check_templates(base))
    issues.extend(check_neo4j_schema_files(base))

    report_path = write_report(base, mode, issues)

    # Console summary
    print("=== LitigationOS Validation Report ===")
    for i in issues:
        print(f"[{i.level}] {i.code}: {i.message}")
    print(f"Report: {report_path}")

    # Exit logic
    if mode == "DRAFT":
        # fail-soft: only catastrophic missing base dirs are errors; keep exit 0 unless schemas/templates missing
        catastrophic_codes = {
            "FIELD_CATALOG_MISSING",
            "FIELD_CATALOG_BAD_COLUMNS",
            "SCHEMA_REGISTRY_MISSING",
            "SCHEMA_REGISTRY_BAD_JSON",
            "SCHEMA_FILES_MISSING",
            "NODES_TEMPLATE_DIR_MISSING",
            "NODES_TEMPLATES_EMPTY",
            "RELS_TEMPLATE_DIR_MISSING",
            "RELS_TEMPLATES_EMPTY",
            "NEO4J_SCHEMA_MISSING",
        }
        if any(i.level == "ERROR" and i.code in catastrophic_codes for i in issues):
            return 1
        return 0

    # PCG fail-closed
    if any(i.level == "ERROR" for i in issues):
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
PY
chmod +x "$BASE/tools/validate_all.py"

# Add/refresh docs: FINALIZATION_AND_PACKAGING
cat > "$BASE/docs/FINALIZATION_AND_PACKAGING_v2026-01-19.3.md" <<'MD'
# Finalization + Packaging (C3) — Procedures

This file defines the **PCG-capable** procedure to finalize, validate, and package this blueprint pack.

## 1) Deduplicate the field catalog

```bash
python tools/dedupe_field_catalog.py \
  --in model/field_catalog_superset.csv \
  --out model/field_catalog_superset_dedup.csv \
  --report validation_reports/field_catalog_dedupe_report.md

2) Regenerate contracts and templates from the dedup catalog

Always show details
python tools/schema_emit.py \
  --field-catalog model/field_catalog_superset_dedup.csv \
  --out-dir schemas/entities

python tools/generate_neo4j_schema.py \
  --field-catalog model/field_catalog_superset_dedup.csv \
  --out-dir neo4j

python tools/generate_graphir_templates.py \
  --field-catalog model/field_catalog_superset_dedup.csv \
  --out-dir templates/neo4j_admin_import

3) Validate

Always show details
python tools/validate_all.py --base . --mode DRAFT
python tools/validate_all.py --base . --mode PCG

PCG PASS means the pack is consistent enough to use for irreversible steps (Neo4j import, filing packet builds, etc.).
4) Package

Use zip -r or the included tools/package_zip.sh if present in your run environment.
5) Savepoint

Write a savepoint JSON that records:

    pack version + git commit if any

    exact input catalogs used (dedup file)

    validation report paths

    outputs produced

See: docs/SAVEPOINT_PROTOCOL_v2026-01-19.3.md.
MD
Ensure executable bit on scripts

chmod +x "$BASE/tools/schema_emit.py" "$BASE/tools/generate_graphir_templates.py" "$BASE/tools/generate_neo4j_schema.py" "$BASE/tools/harvest_zip_csv_headers.py" || true

Always show details

Patching validator with deduplication checks

I will update the validate_all function to handle deduplication logic. The new plan is to check if the deduped file exists and use that, otherwise fall back to the original. I'll ensure that in DRAFT mode, duplicates in the original are warnings, not errors, and that PCG requires the deduped version. I'll also validate schema, templates, and scripts while writing a comprehensive report that includes detailed info on duplicates if they are found. Let's implement this!
Patching validate_all with deduplication logic

Always show details
bash -lc set -euo pipefail
BASE='/mnt/data/_work_c3/LitigationOS_Blueprint_Pack_v2026-01-19.3'
cat > "$BASE/tools/validate_all.py" <<'PY'
#!/usr/bin/env python3
"""LitigationOS Blueprint Pack validator (DRAFT vs PCG).

Modes:
  - DRAFT: fail-soft. Treat duplicates in original catalogs as warnings.
  - PCG: fail-closed. Requires deduped catalogs and all generated artifacts.

Produces a Markdown report under validation_reports/.

This validator intentionally does **not** contact the network.
"""

from __future__ import annotations

import argparse
import csv
import json
import os
from pathlib import Path


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open('r', encoding='utf-8', newline='') as f:
        rdr = csv.DictReader(f)
        return [row for row in rdr]


def detect_duplicates(rows: list[dict[str, str]], key_cols: tuple[str, str]) -> dict[tuple[str, str], int]:
    counts: dict[tuple[str, str], int] = {}
    a, b = key_cols
    for r in rows:
        k = (r.get(a, '').strip(), r.get(b, '').strip())
        counts[k] = counts.get(k, 0) + 1
    return {k: v for k, v in counts.items() if k[0] and k[1] and v > 1}


def exists_nonempty(path: Path) -> bool:
    return path.exists() and path.is_file() and path.stat().st_size > 0


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument('--base', default='.', help='Pack base directory')
    ap.add_argument('--mode', choices=['DRAFT', 'PCG'], default='DRAFT')
    args = ap.parse_args()

    base = Path(args.base).resolve()
    mode = args.mode

    errors: list[str] = []
    warns: list[str] = []

    # ---- Core inputs
    field_orig = base / 'model' / 'field_catalog_superset.csv'
    field_dedup = base / 'model' / 'field_catalog_superset_dedup.csv'
    rel_catalog = base / 'model' / 'relationship_catalog_superset.csv'

    if not exists_nonempty(field_orig):
        errors.append(f"missing: {field_orig}")
        field_rows_orig = []
    else:
        field_rows_orig = read_csv(field_orig)

    # Dedupe rules
    if mode == 'PCG' and not exists_nonempty(field_dedup):
        errors.append(
            "PCG requires deduped field catalog. Run: python tools/dedupe_field_catalog.py --in model/field_catalog_superset.csv --out model/field_catalog_superset_dedup.csv"
        )

    if exists_nonempty(field_dedup):
        field_rows = read_csv(field_dedup)
        dups_dedup = detect_duplicates(field_rows, ('entity', 'field'))
        if dups_dedup:
            errors.append(f"dedup catalog still has duplicates: {len(dups_dedup)}")
        # Original duplicates become WARNs (because we have a deduped replacement)
        dups_orig = detect_duplicates(field_rows_orig, ('entity', 'field'))
        if dups_orig:
            warns.append(f"original field catalog has duplicates (expected; dedup file present): {len(dups_orig)}")
    else:
        field_rows = field_rows_orig
        dups_orig = detect_duplicates(field_rows_orig, ('entity', 'field'))
        if dups_orig:
            if mode == 'PCG':
                errors.append(f"field_catalog has duplicates: {len(dups_orig)}")
            else:
                warns.append(f"field_catalog has duplicates (DRAFT warn): {len(dups_orig)}")

    if not exists_nonempty(rel_catalog):
        errors.append(f"missing: {rel_catalog}")

    # ---- Schema registry
    registry = base / 'schemas' / 'entities' / '_registry.json'
    if not exists_nonempty(registry):
        errors.append(f"missing: {registry}")
        reg = {}
    else:
        try:
            reg = json.loads(registry.read_text(encoding='utf-8'))
        except Exception as e:
            errors.append(f"registry not parseable JSON: {registry} ({e})")
            reg = {}

    # Validate schema files exist
    if isinstance(reg.get('entities'), list):
        for e in reg['entities']:
            schema_name = (e or {}).get('schema')
            ent = (e or {}).get('entity')
            if not schema_name or not ent:
                warns.append("registry has entity row missing entity/schema")
                continue
            sp = base / 'schemas' / 'entities' / schema_name
            if not exists_nonempty(sp):
                errors.append(f"missing schema for {ent}: {sp}")

    # ---- Neo4j scripts
    neo4j_dir = base / 'neo4j'
    for fn in ['schema_constraints.cypher', 'schema_indexes_core.cypher', 'schema_indexes_aggressive.cypher']:
        p = neo4j_dir / fn
        if not exists_nonempty(p):
            errors.append(f"missing: {p}")

    # ---- Import template headers
    nodes_dir = base / 'templates' / 'neo4j_admin_import' / 'nodes'
    rels_dir = base / 'templates' / 'neo4j_admin_import' / 'rels'

    if not nodes_dir.exists():
        errors.append(f"missing dir: {nodes_dir}")
    if not rels_dir.exists():
        errors.append(f"missing dir: {rels_dir}")

    # Expect headers for every entity in field catalog
    entities = sorted({r.get('entity','').strip() for r in field_rows if r.get('entity','').strip()})
    missing_headers = []
    for ent in entities:
        hp = nodes_dir / f"{ent}_header.csv"
        if not exists_nonempty(hp):
            missing_headers.append(ent)
    if missing_headers:
        errors.append(f"missing node headers for {len(missing_headers)} entities")

    # Relationship headers exist (at least 1)
    if rels_dir.exists():
        rel_headers = [p for p in rels_dir.glob('*_header.csv') if p.is_file() and p.stat().st_size > 0]
        if not rel_headers:
            errors.append("no relationship header templates found")

    # ---- Starter docs
    readme = base / 'LitigationOS_BLUEPRINT_README_v2026-01-19.3.md'
    if not exists_nonempty(readme):
        errors.append(f"missing: {readme}")

    idx = base / 'INDEX.md'
    if not exists_nonempty(idx):
        errors.append(f"missing: {idx}")

    # ---- Report
    out_dir = base / 'validation_reports'
    out_dir.mkdir(parents=True, exist_ok=True)
    out = out_dir / f"validate_all_{mode}.md"

    lines: list[str] = []
    lines.append(f"# LitigationOS Validation Report — {mode}\n")
    lines.append(f"Base: `{base}`\n")

    lines.append("## Summary\n")
    lines.append(f"- Errors: {len(errors)}\n")
    lines.append(f"- Warnings: {len(warns)}\n")

    if warns:
        lines.append("\n## Warnings\n")
        for w in warns:
            lines.append(f"- {w}\n")

    if errors:
        lines.append("\n## Errors\n")
        for e in errors:
            lines.append(f"- {e}\n")

    if mode == 'PCG' and errors:
        lines.append("\n## PCG Result\n\n**FAIL** — resolve errors before irreversible actions (filing/service/import).\n")
    else:
        lines.append("\n## Result\n\nPASS (for this mode).\n")

    out.write_text(''.join(lines), encoding='utf-8')

    return 1 if (mode == 'PCG' and errors) else 0


if __name__ == '__main__':
    raise SystemExit(main())
PY
chmod +x "$BASE/tools/validate_all.py"

Running dedupe script and regenerating outputs

Now, I'll execute the deduplication script and regenerate all necessary outputs using the deduped file. This will ensure that everything aligns perfectly with the updated logic and requirements. Let's carry out that step and ensure the outputs are structured properly!
Running deduplication and regenerating outputs

Always show details
bash -lc set -euo pipefail
BASE='/mnt/data/_work_c3/LitigationOS_Blueprint_Pack_v2026-01-19.3'
cd "$BASE"

python tools/dedupe_field_catalog.py --in model/field_catalog_superset.csv --out model/field_catalog_superset_dedup.csv --report validation_reports/field_catalog_dedupe_report.md

# regenerate core emitted artifacts from dedup catalog
python tools/schema_emit.py --field-catalog model/field_catalog_superset_dedup.csv --out-dir schemas/entities
python tools/generate_neo4j_schema.py --field-catalog model/field_catalog_superset_dedup.csv --out-dir neo4j
python tools/generate_graphir_templates.py --field-catalog model/field_catalog_superset_dedup.csv --out-dir templates/neo4j_admin_import

# re-run validation
python tools/validate_all.py --base . --mode DRAFT
python tools/validate_all.py --base . --mode PCG || true

ls -lh validation_reports | sed -n '1,200p'

usage: generate_graphir_templates.py [-h] --field-catalog FIELD_CATALOG
                                     --rel-catalog REL_CATALOG --out-dir
                                     OUT_DIR
generate_graphir_templates.py: error: the following arguments are required: --rel-catalog

Re-running with correct arguments

It looks like we need to check if the earlier call was missing the rel-catalog argument, even though we might've run it with both before. I'll re-run the process with the right arguments, ensuring that the rel-catalog is included. It's likely in the model/rel_catalog.csv folder, but I'll double-check.
Checking model directory for rel_catalog.csv

Always show details
bash -lc ls -lh /mnt/data/_work_c3/LitigationOS_Blueprint_Pack_v2026-01-19.3/model | sed -n '1,120p'

total 804K
-rw-r--r-- 1 root root 8.5K Jan 20 03:49 entity_index.csv
-rw-r--r-- 1 root root 285K Jan 20 03:49 field_catalog_superset.csv
-rw-r--r-- 1 root root 240K Jan 20 04:50 field_catalog_superset_dedup.csv
-rw-r--r-- 1 root root 118K Jan 20 03:49 rel_index.csv
-rw-r--r-- 1 root root 154K Jan 20 03:49 relationship_catalog_superset.csv

Re-running generation using updated rel-catalog

Ah, looks like the rel-catalog file is actually "relationship_catalog_superset.csv," not rel_catalog. I'll run the generator again with the correct file. We've already partly done schema_emit and neo4j schema, but I'll do them again just to be thorough. Then I'll also update everything to use the dedup version. Let's go ahead and run it!
Running schema and graph generation processes

Always show details
bash -lc set -euo pipefail
BASE='/mnt/data/_work_c3/LitigationOS_Blueprint_Pack_v2026-01-19.3'
cd "$BASE"

python tools/schema_emit.py --field-catalog model/field_catalog_superset_dedup.csv --out-dir schemas/entities
python tools/generate_neo4j_schema.py --field-catalog model/field_catalog_superset_dedup.csv --out-dir neo4j
python tools/generate_graphir_templates.py --field-catalog model/field_catalog_superset_dedup.csv --rel-catalog model/relationship_catalog_superset.csv --out-dir templates/neo4j_admin_import

# run validation (DRAFT + PCG) and proceed even if PCG fails
python tools/validate_all.py --base . --mode DRAFT || true
python tools/validate_all.py --base . --mode PCG || true

ls -lh validation_reports | sed -n '1,200p'

total 158K
-rw-r--r-- 1 root root 201 Jan 20 04:50 field_catalog_dedupe_report.md
-rw-r--r-- 1 root root 272 Jan 20 04:50 validate_all_DRAFT.md
-rw-r--r-- 1 root root 270 Jan 20 04:50 validate_all_PCG.md
-rw-r--r-- 1 root root 99K Jan 20 04:46 validation_report.json
-rw-r--r-- 1 root root 58K Jan 20 04:46 validation_report.md

Checking validate_all outputs and dedupe report

Hmm, the command worked, but I didn’t explicitly run validate_all. The reports (validate_all_DRAFT.md and validate_all_PCG.md) might have been produced by a previous script or dedupe run. I’ll regenerate them now with the new validator to ensure everything’s accurate. Also, the dedupe report seems too small at 201 bytes — maybe it got truncated. I’ll check it.
Inspecting validation and deduplication reports

Always show details
bash -lc BASE='/mnt/data/_work_c3/LitigationOS_Blueprint_Pack_v2026-01-19.3'
sed -n '1,120p' $BASE/validation_reports/field_catalog_dedupe_report.md
sed -n '1,140p' $BASE/validation_reports/validate_all_DRAFT.md
sed -n '1,200p' $BASE/validation_reports/validate_all_PCG.md

# Field Catalog Deduplication Report (C3)

Input rows: 2921

Unique (entity, field) keys: 2283

Rows removed by dedupe: 638

Merged-notes keys: 1585

## Conflicts (first-wins, logged)

(none detected)
# LitigationOS Validation Report — DRAFT
Base: `/mnt/data/_work_c3/LitigationOS_Blueprint_Pack_v2026-01-19.3`
## Summary
- Errors: 0
- Warnings: 1

## Warnings
- original field catalog has duplicates (expected; dedup file present): 318

## Result

PASS (for this mode).
# LitigationOS Validation Report — PCG
Base: `/mnt/data/_work_c3/LitigationOS_Blueprint_Pack_v2026-01-19.3`
## Summary
- Errors: 0
- Warnings: 1

## Warnings
- original field catalog has duplicates (expected; dedup file present): 318

## Result

PASS (for this mode).

Updating docs and generating savepoint file

I need to update the README to mention the dedup file, since it’s now essential. The validator shows warnings, which is fine. Now, I’ll generate the savepoint JSON, following the spec with counts and file references. I'll compute counts and use a Python script to fill the file. Also, I should update bundle_builder_v2026-01-19.3.py for the new filenames.
Updating documentation and generating savepoint JSON

Always show details
bash -lc sed -n '1,220p' /mnt/data/_work_c3/LitigationOS_Blueprint_Pack_v2026-01-19.3/tools/bundle_builder_v2026-01-19.2.py

#!/usr/bin/env python3
"""LitigationOS Blueprint Pack Builder (v2026-01-19.2)

Purpose:
- Recreate the C2 blueprint pack locally from embedded payloads.
- Designed to mitigate ephemeral download links.

How it works:
- This script contains a minimal manifest and expects you to place the source artifacts
  (the C2 pack zip OR the component files) alongside it.
- It verifies presence + non-zero bytes.
- It reconstructs the folder layout in a chosen output directory.

Usage:
  python bundle_builder_v2026-01-19.2.py --src-dir . --out-dir ./OUT_BlueprintPack

Notes:
- This builder is intentionally offline; it does not fetch from the internet.
"""

from __future__ import annotations

import argparse
import os
import shutil
from pathlib import Path

REQUIRED = [
    "LitigationOS_BLUEPRINT_README_v2026-01-19.2.md",
    "INDEX.md",
]

DIRS = ["docs", "model", "diagrams", "tools"]


def require_file(p: Path) -> None:
    if not p.exists():
        raise SystemExit(f"MISSING: {p}")
    if p.is_dir():
        raise SystemExit(f"EXPECTED FILE, GOT DIR: {p}")
    if p.stat().st_size <= 0:
        raise SystemExit(f"EMPTY FILE: {p}")


def copy_tree(src: Path, dst: Path) -> None:
    for root, dirs, files in os.walk(src):
        rel = Path(root).relative_to(src)
        (dst / rel).mkdir(parents=True, exist_ok=True)
        for fn in files:
            s = Path(root) / fn
            d = dst / rel / fn
            shutil.copy2(s, d)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--src-dir", required=True, help="Directory containing the unpacked C2 pack contents")
    ap.add_argument("--out-dir", required=True, help="Where to reconstruct the pack")
    args = ap.parse_args()

    src = Path(args.src_dir).resolve()
    out = Path(args.out_dir).resolve()

    for rf in REQUIRED:
        require_file(src / rf)

    for d in DIRS:
        if not (src / d).exists():
            raise SystemExit(f"MISSING DIR: {src / d}")

    if out.exists():
        raise SystemExit(f"OUT DIR EXISTS (refusing to overwrite): {out}")

    out.mkdir(parents=True, exist_ok=False)

    # Copy root files
    for rf in ["INDEX.md", "LitigationOS_BLUEPRINT_README_v2026-01-19.2.md", "LitigationOS_BLUEPRINT_README_v2026-01-19.1.md"]:
        p = src / rf
        if p.exists():
            require_file(p)
            shutil.copy2(p, out / rf)

    # Copy structured dirs
    for d in DIRS:
        copy_tree(src / d, out / d)

    print(f"OK: Reconstructed pack at: {out}")


if __name__ == "__main__":
    main()

Updating builder file and README

I need to update builder v2026-01-19.3 to include new directories: schemas, templates, neo4j, validation_reports, savepoints, and bloom. We’ll also update the README to mention the dedup field catalog. I'll patch the necessary sections and add a note using perl for line insertion. Let’s get started!
Updating builder and documentation for v2026-01-19.3

Always show details
bash -lc set -euo pipefail
BASE='/mnt/data/_work_c3/LitigationOS_Blueprint_Pack_v2026-01-19.3'
perl -pi -e 's/model\/field_catalog_superset\.csv/model\/field_catalog_superset_dedup.csv (preferred)\n- model\/field_catalog_superset.csv (raw, may contain duplicates)/g' "$BASE/LitigationOS_BLUEPRINT_README_v2026-01-19.3.md"
perl -pi -e 's/model\/field_catalog_superset\.csv/model\/field_catalog_superset_dedup.csv (preferred)\n- model\/field_catalog_superset.csv (raw)/g' "$BASE/docs/GRAPH_CONTRACTS_v2026-01-19.3.md" || true

Confirming README update

It seems like the command may have tried to patch the docs but got truncated, possibly due to using a wildcard. I’ll open the README snippet to confirm and see if the update is fully applied or incomplete. Let’s check and verify.
Searching for "field_catalog" in README

Always show details
bash -lc grep -n "field_catalog" -n /mnt/data/_work_c3/LitigationOS_Blueprint_Pack_v2026-01-19.3/LitigationOS_BLUEPRINT_README_v2026-01-19.3.md | head -n 30

22:- `model/field_catalog_superset_dedup.csv (preferred)
23:- model/field_catalog_superset.csv (raw, may contain duplicates)` (entity → dense field list)
51:- Build: `python tools/schema_emit.py --field-catalog model/field_catalog_superset_dedup.csv (preferred)
52:- model/field_catalog_superset.csv (raw, may contain duplicates) --out-dir schemas/entities`
55:- Build: `python tools/generate_neo4j_schema.py --field-catalog model/field_catalog_superset_dedup.csv (preferred)
56:- model/field_catalog_superset.csv (raw, may contain duplicates) --out-dir neo4j`
59:- Build: `python tools/generate_graphir_templates.py --field-catalog model/field_catalog_superset_dedup.csv (preferred)
60:- model/field_catalog_superset.csv (raw, may contain duplicates) --rel-catalog model/relationship_catalog_superset.csv --out-dir templates/neo4j_admin_import`
72:python tools/schema_emit.py --field-catalog model/field_catalog_superset_dedup.csv (preferred)
73:- model/field_catalog_superset.csv (raw, may contain duplicates) --out-dir schemas/entities
74:python tools/generate_neo4j_schema.py --field-catalog model/field_catalog_superset_dedup.csv (preferred)
75:- model/field_catalog_superset.csv (raw, may contain duplicates) --out-dir neo4j
76:python tools/generate_graphir_templates.py --field-catalog model/field_catalog_superset_dedup.csv (preferred)
77:- model/field_catalog_superset.csv (raw, may contain duplicates) --rel-catalog model/relationship_catalog_superset.csv --out-dir templates/neo4j_admin_import

Fixing line breaks and formatting in README

It looks like I accidentally inserted line breaks in the inline code blocks, which messed up the formatting. I need to manually fix the README by rewriting those lines. I'll use a python script for editing, but I’ll make necessary tweaks using perl to correct the content inside the inline code. Let's check those lines.
Editing readme for inline code fixes

Always show details
bash -lc nl -ba /mnt/data/_work_c3/LitigationOS_Blueprint_Pack_v2026-01-19.3/LitigationOS_BLUEPRINT_README_v2026-01-19.3.md | sed -n '15,85p'

    15	### A) Top index (navigation)
    16	- `INDEX.md`
    17	
    18	### B) The granular build plan (bottom → top)
    19	- `docs/BUILDPLAN_BOTTOM_TO_TOP_v2026-01-19.2.md`
    20	
    21	### C) Max-density schema catalogs (source of truth)
    22	- `model/field_catalog_superset_dedup.csv (preferred)
    23	- model/field_catalog_superset.csv (raw, may contain duplicates)` (entity → dense field list)
    24	- `model/relationship_catalog_superset.csv` (from/to → relationship catalog)
    25	- `docs/ERD_SUPERSET_FIELD_DICTIONARY_v2026-01-19.2.md` (human-readable field dictionary)
    26	- `docs/ENTITY_RELATIONSHIP_SUPERSET_INDEX_v2026-01-19.2.md` (human-readable rel index)
    27	
    28	### D) Graph contracts (machine validation)
    29	- `schemas/entities/*.schema.json` (per-entity JSON Schema; strict by default)
    30	- `schemas/entities/_registry.json` (schema registry)
    31	- `docs/GRAPH_CONTRACTS_v2026-01-19.3.md` (how contracts connect to GraphIR + import packs)
    32	
    33	### E) Neo4j import + schema
    34	- `templates/neo4j_admin_import/nodes/*_header.csv`
    35	- `templates/neo4j_admin_import/rels/*_header.csv`
    36	- `neo4j/schema_constraints.cypher`
    37	- `neo4j/schema_indexes_core.cypher`
    38	- `neo4j/schema_indexes_aggressive.cypher`
    39	
    40	### F) Restartability / infinite chained cycles
    41	- `docs/SAVEPOINT_PROTOCOL_v2026-01-19.3.md`
    42	- Example savepoint: `savepoints/example/savepoint_C3_finalization.json`
    43	
    44	### G) Diagrams (ERD-style overview + domain cards)
    45	- Overview: `diagrams/erd_superset_overview_sfdp.png`
    46	- Domain cards: `diagrams/erd_superset_cards_*.png`
    47	
    48	## What “C3” changes versus C2
    49	### 1) JSON Schema emitter is now real, not just prescribed
    50	The canonical catalogs now compile into schemas:
    51	- Build: `python tools/schema_emit.py --field-catalog model/field_catalog_superset_dedup.csv (preferred)
    52	- model/field_catalog_superset.csv (raw, may contain duplicates) --out-dir schemas/entities`
    53	
    54	### 2) Neo4j schema scripts are generated and staged
    55	- Build: `python tools/generate_neo4j_schema.py --field-catalog model/field_catalog_superset_dedup.csv (preferred)
    56	- model/field_catalog_superset.csv (raw, may contain duplicates) --out-dir neo4j`
    57	
    58	### 3) neo4j-admin import header templates are generated
    59	- Build: `python tools/generate_graphir_templates.py --field-catalog model/field_catalog_superset_dedup.csv (preferred)
    60	- model/field_catalog_superset.csv (raw, may contain duplicates) --rel-catalog model/relationship_catalog_superset.csv --out-dir templates/neo4j_admin_import`
    61	
    62	### 4) Validator now matches emitted artifacts
    63	- DRAFT mode: collects issues (exit 0) and writes a report
    64	- PCG mode: fail-closed (non-zero exit) if any ERROR exists
    65	
    66	### 5) Cyclepack CSV header harvest (from uploaded ZIPs)
    67	- Output: `docs/CSV_HEADER_HARVEST_FROM_UPLOADED_CYCLEPACKS_v2026-01-19.3.md`
    68	
    69	## How to run the finalization pipeline (inside this pack)
    70	From the pack root:
    71	```bash
    72	python tools/schema_emit.py --field-catalog model/field_catalog_superset_dedup.csv (preferred)
    73	- model/field_catalog_superset.csv (raw, may contain duplicates) --out-dir schemas/entities
    74	python tools/generate_neo4j_schema.py --field-catalog model/field_catalog_superset_dedup.csv (preferred)
    75	- model/field_catalog_superset.csv (raw, may contain duplicates) --out-dir neo4j
    76	python tools/generate_graphir_templates.py --field-catalog model/field_catalog_superset_dedup.csv (preferred)
    77	- model/field_catalog_superset.csv (raw, may contain duplicates) --rel-catalog model/relationship_catalog_superset.csv --out-dir templates/neo4j_admin_import
    78	python tools/validate_all.py --base . --mode DRAFT
    79	python tools/validate_all.py --base . --mode PCG
    80	```
    81	
    82	## Bottom→Top model (one screen)
    83	1) **Sources** (files, zips, dockets, transcripts)
    84	2) **Artifacts** (every file becomes an Artifact node + provenance)
    85	3) **Extraction** (text/OCR + anchors)

Correcting formatting in README

I need to fix the README by replacing lines 22-23 with a bullet list:

    model/field_catalog_superset_dedup.csv (preferred; duplicates removed)

    model/field_catalog_superset.csv (raw extraction; duplicates possible)

Also, I’ll remove line breaks from build command lines, using python ... --field-catalog model/field_catalog_superset_dedup.csv. To avoid formatting issues, I'll likely rewrite the entire file from scratch, ensuring all content is correctly formatted.
Analyzed
Fixing JSON parse error in command string

I think the issue is that the command string had unescaped newlines, and the JSON parsing failed due to control characters. The cmd should be a list of strings, and each string shouldn't have unescaped newlines. To fix this, I’ll split up the command to avoid tool JSON parsing issues. I’ll use cat with a here-doc to keep the command manageable.
Fixing long string JSON parsing issue

The JSON parsing might be failing because the string is too long or contains problematic characters, like unescaped control characters or non-ASCII ones like →. I’ll refactor the command by breaking content into smaller sections and avoiding problematic characters, possibly using a smaller file to ensure the tool call remains valid.
Addressing command parsing issues with Unicode and special characters

The problem seems to stem from using characters like line separators or unmatched quotes, which can break the JSON parsing. The system supports Unicode, but the issue may lie in how the string is wrapped or escaped, especially with special characters like newlines or *. I'll focus on ensuring proper wrapping to avoid an incomplete JSON structure.
Attempting to resolve quoting and size issues

I think the issue could be nested quoting or hitting a size limit. I'll try using minimal quoting to avoid complications, especially with double quotes in the file path and avoid nesting. Using a Python approach with a triple-quoted string might be a cleaner solution, as it handles the quoting inside the heredoc more effectively.
Proceeding with Python for writing content

I’ll proceed with passing the Python script inside the bash string, keeping things simple. I’ll use triple quotes in Python but avoid any triple quotes inside the content. I'll stick with ASCII arrows for simplicity, even though Unicode can be fine for robustness. Let’s keep the content fairly concise.
Writing markdown content with Python in shell script

Always show details
bash -lc set -euo pipefail
BASE=/mnt/data/_work_c3/LitigationOS_Blueprint_Pack_v2026-01-19.3
python - <<'PY'
from pathlib import Path
p = Path('/mnt/data/_work_c3/LitigationOS_Blueprint_Pack_v2026-01-19.3/LitigationOS_BLUEPRINT_README_v2026-01-19.3.md')
content = """# LitigationOS - Bottom-to-Top Blueprint + Build README (C3) (v2026-01-19.3)
Build stamp (local): 2026-01-20

## What this deliverable is
This cycle (C3) finalizes and packages the prior blueprint pack (C2) by adding machine-checkable graph contracts, Neo4j import/schema generators, and a validator that supports DRAFT vs PCG (fail-soft vs fail-closed).

## Quick navigation
- INDEX.md (one-page index)
- docs/BUILDPLAN_BOTTOM_TO_TOP_v2026-01-19.2.md (granular build plan)
- model/field_catalog_superset_dedup.csv (preferred dense field list)
- model/field_catalog_superset.csv (raw extraction; may contain duplicates)
- model/relationship_catalog_superset.csv (relationship catalog)

## Key outputs added in C3
### 1) JSON Schemas per entity
- Location: schemas/entities/*.schema.json
- Registry: schemas/entities/_registry.json
- Build:
  - python tools/schema_emit.py --field-catalog model/field_catalog_superset_dedup.csv --out-dir schemas/entities

### 2) Neo4j schema Cypher (constraints + indexes)
- Location: neo4j/
  - schema_constraints.cypher
  - schema_indexes_core.cypher
  - schema_indexes_aggressive.cypher
- Build:
  - python tools/generate_neo4j_schema.py --field-catalog model/field_catalog_superset_dedup.csv --out-dir neo4j

### 3) neo4j-admin import header templates
- Location: templates/neo4j_admin_import/
- Build:
  - python tools/generate_graphir_templates.py \
      --field-catalog model/field_catalog_superset_dedup.csv \
      --rel-catalog model/relationship_catalog_superset.csv \
      --out-dir templates/neo4j_admin_import

### 4) Cyclepack CSV header harvest (from uploaded ZIPs)
- Location: docs/CSV_HEADER_HARVEST_FROM_UPLOADED_CYCLEPACKS_v2026-01-19.3.md
- Build:
  - python tools/harvest_zip_csv_headers.py --out docs/... --zip <zip1> --zip <zip2> ...

### 5) Validator (DRAFT vs PCG)
- Build artifacts must exist and be non-empty.
- DRAFT mode: warnings allowed (exit 0). PCG: fail-closed if any ERROR (non-zero exit).
- Run:
  - python tools/validate_all.py --base . --mode DRAFT
  - python tools/validate_all.py --base . --mode PCG
- Reports: validation_reports/validate_all_*.md

## Restartability / infinite chained cycles
- Protocol: docs/SAVEPOINT_PROTOCOL_v2026-01-19.3.md
- Example: savepoints/example/savepoint_C3_finalization.json

## Notes on catalogs
- The raw field catalog is retained for provenance.
- C3 adds tools/dedupe_field_catalog.py which produces model/field_catalog_superset_dedup.csv and a merge report.

"""
p.write_text(content, encoding='utf-8')
print('WROTE', p)
PY

WROTE /mnt/data/_work_c3/LitigationOS_Blueprint_Pack_v2026-01-19.3/LitigationOS_BLUEPRINT_README_v2026-01-19.3.md
