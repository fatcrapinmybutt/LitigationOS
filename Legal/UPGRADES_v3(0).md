# v3 Upgrades (Architecture & Systems)
- JSON Schema validation at the API boundary (jsonschema)
- SQLite persistence with events + job queue tables
- Template compiler (Jinja2 -> .docx via python-docx)
- Rule Harvester snapshot+diff to content-addressed storage
- Evidence Engine hashes + EXIF + ledger; emits EVIDENCE_INGESTED
- Client Packager emits PACKAGE_BUILT with schema-validated manifest
- Expanded Electron GUI to exercise flows
