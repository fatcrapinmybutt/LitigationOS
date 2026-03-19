# LitigationOS Ops Runbook (Event Horizon)

## 1) First boot (local)
1. Create Vault folder (SSD recommended)
2. Create config JSON
3. Initialize DB schema
4. Run ingest/extract pipeline
5. Start services (optional) via docker compose
6. Run coverage + lint + cyclepack export

## 2) Routine cycle (daily/weekly)
- ingest new inputs
- re-run extract + OCR queue
- rebuild instruction atoms/requirements
- rebuild stacks for selected case(s)
- run linters
- emit cyclepack heavy export

## 3) Disaster recovery
- Vault/00_OBJECTS is the source. If indexes corrupt:
  - rebuild DB by scanning CAS objects and re-deriving doc_ids
- Always keep CyclePack exports externally backed up.

## 4) “Doctor” checklist
- CAS integrity check (hash matches filename)
- DB foreign keys consistent
- extraction paths exist
- stack manifests present
- lint reports present
