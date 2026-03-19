# DOWNLOAD_AUDIT

- Generated (UTC): 2026-01-09T07:10:48.156245Z
- Input v1 sha256: be92ea094b26ad3712b66316c7ac4e81fe8138c5f3b355b3749ac453ba44ffb5
- Input v2 sha256: 5fdb6539ac11003c09245ea6d0203628fdc752c9c4ceeb3bc3254d53f419f8f8
- Total shards: 4355
- Authority_ref collisions resolved: 0

- v4 additions: tools/authority_query.py + tests/

- v5 additions: Vehicle Map scaffold + Authority Triples emitter (candidate-only)

- v6 additions: Validation Gate engine + rules schema

- v7 additions: Deadline/Service calculator + Contradiction scanner

- v8 additions: dynamic expansion harvesters + validator upgrades

- v9 additions: claim→vehicle candidate router

- v10 additions: caselaw layer governance + docket/mifile ingest (candidate-only)

- v11 additions: citation extraction + holding gate + deadline compute + text parser + neo exports + schemas

- v12 additions: FTS5 retrieval layer + concept candidate harvesting + sample search output

- v13 additions: anchors + coverage + optional vector/hybrid retrieval

- v14 additions: claim-capable pipeline modules (proposition builder, vehicle router, claim gate) + demo outputs

- v16 additions: locked draft generator + validator + demo outputs

- v17: fixed locked draft/validator to PASS by TOKEN_ONLY marker

- v18: sanitized tokens/refs to prevent AUTH tag line breaks

- v19: added candidate-only docket ingest + deadline engine + caselaw governance

- v20: deadline engine v20 (holidays+service offsets) + receipt ingest + deadline validator

- v21: added preflight_gate + run_pipeline_demo orchestrator

- v22: preflight gate vehicle schema fix; demo now PASS

- v23: added authority retrieval CLI + issue packet router/validator

- v24: ensure ids + approval-gated promotion + red-team scan

- v25: added docket ingest candidates + caselaw governance candidates

- v26: added gated deadline compute engine (config-driven)

- v27: authority_ref validation + coverage report + reopen recipe builder

- v28: forms indexing + vehicle routing candidates + claim draft candidates assembler

- v29: authority anchor index/search layer + optional local HF embedding adapter

- v30: authority anchor FTS5 index + authority_ref normalizer + rebuild retrieval indexes tool

- v31: add download extension repair + integrity verifier script

- v32: added auto-watcher to rename misnamed .bin downloads to .zip based on file signatures

- v33: added candidate-only Authority Triples generator + candidate Vehicle Map retrieval assistant

- v38: added v34-v38 pipeline modules (pinpoint gate, vehicle registry router, elements/deadlines candidate layers, claim packet assembler)

- v39: added convergence helpers (vehicle registry miner, facts template builder, pipeline runner)

- v40: added candidate caselaw governance + docket/mifile ingest normalizer

- v41: added text docket parser + offline caselaw verification merge layer

- v42: added next-best-step protocol + tool to emit next_best_step.json from current gate state

- v43: added intents/propositions template seeder + optional HF embeddings adapter; runner emits next_best_step.json
\n- v44: added runbook generator + evidence intake schema + intake→facts skeleton tool\n
- v45: added mainframe_next.py wrapper and example JSON inputs for faster onboarding

- v46: added interactive fact_capture_cli + quickstart runner to reduce friction entering pinpointed facts

- v47: added pdf_locator_helper (pdftotext -layout), docx packet skeleton generator, and HF local model registry schema

- v48: added docket ingest (MiFile/ROA receipts) + offline caselaw governance stub + integrated gates into next_best_step_report

- v49: added candidate deadline generator from docket events; integrated DEADLINES gate; optional mainframe auto-generation

- v51: added build_authority_shards_v51.py which calls router and emits authority_shards.jsonl + index + density report

- v52: added merge_versions_final_v52.py to merge all version zips into one FINAL bundle with provenance manifest

- v53: added build_all.py orchestrator + env probe + cyclepack packager
