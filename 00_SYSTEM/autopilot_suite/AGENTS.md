# AGENTS.md — LitigationOS Autopilot Suite (Copilot CLI)

You are an autonomous repo agent. Your mission is to evolve LitigationOS as a deterministic compiler:

## Primary command
- scripts/litigationos_autopilot.py

## Operating rules
- Non-destructive: append-only outputs; never rename canonical roots.
- Deterministic IDs: stable sha1 short.
- Fail-soft by default. Only enforce hard gates when user explicitly requests FILE_READY/PCG.
- Do not invent facts. Any claim must be tied to a source pointer or tagged as unresolved.
- For every candidate legal vehicle, require an Operating Order to be identified and pinned before marking it "valid".

## Work sequence (fast lane)
1) Intake: accept dirs/zips; auto-expand; build manifest.
2) Normalize: unify node/edge formats into core schema.
3) Authority layer: build AuthorityRegistry from user-provided Michigan authority corpus; resolve citations -> authority nodes.
4) Vehicle layer: map authority -> vehicle -> court/jurisdiction; emit VehicleMap candidates.
5) Chain layer: violation/gap -> harm -> remedy -> vehicle -> authority -> caselaw -> action.
6) Outputs: Neo4j import CSVs, GraphML (Gephi), Bloom perspective JSON, constraints, reports.
7) Packaging: zip + manifests + rebuild script.

## Must-emit artifacts
- graph_contract.yml
- neo4j_constraints.cypher
- bloom_perspective.json
- action_report.md
- manifest.json + run_ledger.jsonl + violations.json
