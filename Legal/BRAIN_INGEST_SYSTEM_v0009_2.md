# BRAIN_INGEST_SYSTEM_v0009
This module converts textual corpus (manuals/blueprints/link corpora/extracted PDFs) into structured artifacts:
Atoms → Signals → Scores → Deltas → Gates → Actions → Vehicles, plus a Neo4j-importable GraphContracts export.

## Contracts
- JSONL rows validated implicitly by SCHEMA/brain/*.schema.json (row-schema)
- Graph CSV outputs validated by TOOLS/litos_graph_contracts_validate.py against SCHEMA/contracts/*

## Replayability (built-in)
- Durable queue: BRAIN/RUNS/<run_id>/jobqueue.sqlite (SQLite WAL)
- Event log: LOGS/runs/<run_id>.jsonl
- Receipts: BRAIN/RUNS/<run_id>/receipt.json + governor_receipt.json

## Autonomy posture
- Governor is deterministic, offline-first, and resume-safe.
- All operations are explicitly logged; no hidden state transitions.
- Output is append-only by run_id; no overwrites except within the same run if resumed.

## QuoteLock posture
- Extracted text is candidate-only. Verbatim quotations are blocked until QuoteLock promotion is satisfied.
