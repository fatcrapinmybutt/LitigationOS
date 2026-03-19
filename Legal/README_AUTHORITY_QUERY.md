# LitigationOS Authority Store v4

This bundle adds a deterministic, offline query tool for the Authority Store SQLite (FTS5).

## Quick start

```bash
python tools/authority_query.py --db authority_store.sqlite search --q "MCR 2.003" --k 25 --print
python tools/authority_query.py --db authority_store.sqlite anchor --a "MCL 722.23" --k 200 --print
python tools/authority_query.py --db authority_store.sqlite get --ref "DOC_XXXXXXXXXXXX:p0001" --print
```

## Output discipline
- Outputs are pointers + verbatim snippets; no rewriting of authority text.
- Use authority_ref for pinpoints in Vehicle Map / Authority Triples.

## v5 Additions
- tools/vehicle_map_scaffold.py (candidate-only)
- tools/authority_triples_emit.py (candidate-only)

## v6 Additions
- tools/validate_candidates.py (Validation Gate)
- docs/validation_rules.json

## v7 Additions
- tools/deadline_service_calc.py (candidate-only date arithmetic)
- tools/contradiction_scan.py (non-interpretive consistency flags)

## v8 Additions (Dynamic Expansion)
- tools/judiciary_lens_harvest.py
- tools/vehicle_candidates_harvest.py
- tools/claim_ground_harvest.py
- docs/lens_terms_*.json (editable token dictionaries; FTS-safe)
- outputs/*.csv (example candidate outputs)
- validate_candidates.py upgraded: authority_ref shape + optional DB existence checks (--db)

## v9 Additions
- tools/claim_vehicle_router.py (candidate-only join)

## v10 Additions
- tools/caselaw_layer_governance.py (candidate-only citation classification)
- tools/docket_mifile_ingest.py (ROA + MiFile receipts normalization, candidate-only)
- outputs/caselaw_citations_governed.csv (example)
- outputs/docket_events_candidates.csv + deadlines_candidates.csv (examples)
- docs/deadline_spec_example.json (operator-owned example)

## v11 Additions (x10 capability expansion tranche)
- tools/caselaw_citation_extractor.py (candidate-only extraction)
- tools/holding_pinpoint_gate.py (structural promotion gate)
- tools/docket_deadline_compute.py (candidate-only arithmetic)
- tools/parse_roa_receipt_text.py (pdftotext line parser)
- tools/export_candidates_to_neo4j_csv.py (candidate nodes/edges export)
- docs/schemas/*.schema.json (candidate output schemas)

## v12 Additions (retrieval + judiciary/filing concept harvest)
- tools/build_fts_index.py (FTS5 over shards)
- tools/authority_search_cli.py (BM25 retrieval + snippets)
- tools/litigation_concept_candidate_extractor.py (keyword-based candidate concepts)
- outputs/litigation_concept_candidates.csv (CANDIDATE_ONLY_NO_LEGAL_INFERENCE)
- outputs/authority_search_sample.csv (demonstration only)

## v13 Additions (Authority Index + optional hybrid retrieval)
- tools/authority_anchor_extractor.py
- tools/authority_coverage_report.py
- tools/vector_index_builder.py
- tools/hybrid_retriever_cli.py
- outputs/authority_anchors.csv/.jsonl
- outputs/authority_anchor_coverage_by_doc.csv
- outputs/authority_anchor_top_tokens.csv

## v14 Additions (Proposition → Vehicle → Claim gating)
- tools/proposition_builder.py (authority proposition candidates with excerpt windows)
- tools/vehicle_router_mi.py (table-driven routing; emits fixlist if catalog missing)
- tools/claim_compiler_gate.py (PASS/FAIL gates; only emits claim packets on PASS)
- outputs/authority_propositions_candidates.jsonl (demo)
- outputs/vehicle_map_candidates_demo.json + fixlists (demo)
- outputs/claim_packets_demo.jsonl + fixlist (demo)

## v16 Additions (Locked Drafting + Validator)
- tools/draft_from_claim_packet.py (generates backlink-tagged draft)
- tools/draft_validator.py (PASS/FAIL; ensures backlinks)
- outputs/draft_locked_demo.txt
- outputs/draft_validation_report_demo.json
- outputs/draft_validation_issues_demo.csv

## v17 Patch (Validator PASS)
- outputs/draft_locked_demo_v17.txt
- outputs/draft_validation_report_demo_v17.json
- outputs/draft_validation_issues_demo_v17.csv

## v18 Patch (Sanitized tags)
- outputs/authority_propositions_candidates_v18.jsonl
- outputs/claim_packets_PASS_v18.jsonl
- outputs/draft_locked_demo_v18.txt
- outputs/draft_validation_report_demo_v18.json
- outputs/draft_validation_issues_demo_v18.csv

## v19 Additions (Docket/Deadlines/Caselaw governance)
- tools/docket_ingest_candidates.py
- tools/deadline_engine.py
- tools/caselaw_layer_governance.py
- outputs/docket_events_demo.csv
- outputs/deadlines_candidates_demo.csv
- outputs/caselaw_governance_demo.csv

## v20 Additions (Deadline calendar + service offsets + receipts ingest)
- tools/receipts_ingest_candidates.py
- tools/deadline_validator.py
- outputs/deadlines_candidates_demo_v20.csv
- outputs/deadline_validation_report_demo_v20.json

## v21 Additions (Preflight gate + demo orchestrator)
- tools/preflight_gate.py
- tools/run_pipeline_demo.py
- outputs/preflight_report_demo_v21.json
- outputs/preflight_fixlist_demo_v21.csv

## v22 Patch (Preflight vehicle schema fix)
- tools/preflight_gate.py (v22)
- outputs/preflight_report_demo_v22.json
- outputs/preflight_fixlist_demo_v22.csv

## v23 Additions (Retrieval + Issue Packet layer)
- tools/authority_query_cli.py
- tools/claim_router_candidates.py
- tools/issue_packet_validator.py
- outputs/issue_packets_demo_v23.jsonl
- outputs/issue_packet_validation_report_demo_v23.json
- outputs/authority_query_hits_demo_v23.jsonl

## v24 Additions (Approval promotion + Red-team scan)
- tools/ensure_atom_ids.py
- tools/promote_issue_packet_to_claim.py
- tools/redteam_scan_claim_packet.py
- docs/approvals_template.json
- outputs/issue_packets_demo_v23_with_ids.jsonl
- outputs/claim_packets_APPROVED_demo_v24.jsonl
- outputs/redteam_report_claim_demo_v24.json

## v25 Additions (Docket ingest + Caselaw governance candidates)
- tools/docket_ingest_candidates.py
- tools/caselaw_layer_governance_candidates.py
- outputs/deadlines_candidates_demo_v25.csv
- outputs/caselaw_governance_demo_v25.jsonl
- outputs/preflight_report_demo_v25.json

## v26 Additions (Gated deadline computation engine)
- tools/deadline_triggers_from_candidates.py
- tools/deadline_compute_engine.py
- outputs/deadline_triggers_demo_v26.csv
- outputs/deadlines_computed_demo_v26.csv
- outputs/holidays_demo_v26.csv
- outputs/preflight_report_demo_v26.json

## v27 Additions (Authority integrity: ref validation, coverage, reopen recipes)
- tools/authority_ref_validator.py
- tools/authority_coverage_report.py
- tools/reopen_recipe_builder.py
- outputs/authority_ref_validation_demo_v27.json
- outputs/authority_coverage_docs_demo_v27.json
- outputs/reopen_recipe_demo_v27.json

## v28 Additions (Forms index + Vehicle router + Claim draft candidates)
- tools/forms_indexer.py
- tools/vehicle_router_candidates.py
- tools/claim_draft_candidates_assembler.py
- outputs/forms_index_demo_v28.jsonl
- outputs/vehicle_router_candidates_demo_v28.json
- outputs/claim_draft_candidates_demo_v28.jsonl

## v29 Additions (Authority Anchor Index + Search + optional HF adapter)
- tools/authority_anchor_index_from_db.py
- tools/authority_anchor_search.py
- tools/hf_embedding_adapter.py
- outputs/authority_anchor_index_v29.jsonl
- outputs/authority_anchor_index_summary_v29.json

## v30 Additions (FTS5 retrieval layer + authority_ref normalizer + rebuild orchestrator)
- tools/authority_ref_normalize.py
- tools/authority_anchor_fts_build.py
- tools/authority_anchor_fts_search.py
- tools/rebuild_retrieval_indexes.py
- outputs/authority_anchor_fts.sqlite

## v31 Download Extension Fix
- docs/DOWNLOAD_FIX_GUIDE.md
- tools/fix_downloaded_bin.py

## v32 Additions (Auto-fix misnamed .bin downloads)
- tools/bin_fix_watcher.py
- install/install_bin_fix_watcher_windows.ps1
- install/install_bin_fix_watcher_termux.sh
- docs/V32_DOWNLOAD_AUTOFIX.md

## v33 Additions (Candidate-only claim/vehicle retrieval scaffolds)
- tools/authority_triples_candidate.py
- tools/vehicle_map_candidate.py
- docs/V33_CANDIDATE_LAYER.md

## v34–v38 Additions (Fact pinpoint gate + registry-driven vehicle routing + elements/deadlines + claim packet bundling)
- tools/facts_pinpoint_validate.py
- tools/vehicle_router_registry.py
- tools/elements_checklist_candidate.py
- tools/deadlines_compute_candidate.py
- tools/claim_packet_assemble_candidate.py
- docs/V34_V38_PIPELINE.md

## v39 Additions (Convergence helpers)
- tools/vehicle_registry_miner_candidate.py
- tools/facts_template_from_manifest.py
- tools/run_claim_pipeline_v39.py
- docs/V39_CONVERGENCE_HELPERS.md

## v40 Additions (Caselaw governance + Docket/MiFile ingest)
- tools/caselaw_layer_governance_candidate.py
- tools/docket_mifile_ingest_candidate.py
- docs/V40_CASELAW_DOCKET_GOVERNANCE.md

## v41 Additions (Text docket parsing + caselaw verification merge)
- tools/docket_text_to_entries_candidate.py
- tools/caselaw_verification_merge.py
- docs/V41_TEXT_DOCKET_AND_CASELAW_VERIFY.md

## v42 Additions (Next Best Step protocol + reporter)
- docs/NEXT_BEST_STEP_PROTOCOL.md
- tools/next_best_step_report.py

## v43 Additions (Templates + optional HF embeddings adapter)
- tools/templates_seed_intents_props_v43.py
- tools/embedding_adapter_hf_candidate.py
- docs/V43_TEMPLATES_AND_EMBEDDINGS.md
- runner now emits outputs/next_best_step.json after pipeline run
\n## v44 Additions (Runbook + evidence intake → facts skeleton)\n- tools/generate_runbook_v44.py\n- tools/evidence_intake_to_facts_skeleton_v44.py\n- docs/schemas/evidence_intake_in.schema.json\n- docs/V44_RUNBOOK_AND_EVIDENCE_INTAKE.md\n
## v45 Additions (Mainframe next-step wrapper + examples)
- tools/mainframe_next.py
- docs/examples/*.example.json
- docs/V45_MAINFRAME_NEXT_AND_EXAMPLES.md

## v46 Additions (Fact capture CLI + quickstart)
- tools/fact_capture_cli_v46.py
- tools/quickstart_v46.py
- docs/V46_FACT_CAPTURE_AND_QUICKSTART.md

## v47 Additions (PDF locator + DOCX skeleton + HF local registry)
- tools/pdf_locator_helper_v47.py
- tools/court_packet_skeleton_docx_v47.py
- docs/schemas/hf_models_local.schema.json
- docs/examples/hf_models_local.example.json
- docs/V47_LOCATOR_PACKET_AND_HF_REGISTRY.md

## v48 Additions (Docket ingest + caselaw governance + NBS gates)
- tools/docket_mifile_ingest_v48.py
- docs/schemas/docket_ingest_in.schema.json
- docs/examples/docket_ingest_in.example.json
- tools/caselaw_governance_stub_v48.py
- docs/schemas/caselaw_verified.schema.json
- docs/examples/caselaw_verified.example.json
- docs/V48_DOCKET_AND_CASELAW_GOVERNANCE.md

## v49 Additions (Candidate deadlines from docket)
- tools/deadlines_from_docket_v49.py
- docs/schemas/deadlines_out.schema.json
- docs/examples/deadline_trigger_map.example.json
- docs/V49_DEADLINES_FROM_DOCKET.md

## v50
- Added conversion backend router (pdftotext/unstructured/docling).

## v51 Additions (shard builder + anchor density)
- tools/build_authority_shards_v51.py (calls router + fallback heuristic)
- outputs: authority_shards.jsonl, authority_index.jsonl, authority_anchor_density_report.json
- docs/V51_SHARD_BUILDER_WITH_FALLBACK.md

## v52 Additions (final consolidation)
- tools/merge_versions_final_v52.py (merge v*.zip -> FINAL)
- docs/V52_FINAL_CONSOLIDATION_BUILDER.md

## v53 Additions (one-run orchestrator + cyclepack)
- build_all.py (FINAL run orchestrator)
- tools/env_probe_v53.py (env report)
- tools/pack_cyclepack_v53.py (CyclePack packager)
- docs/V53_BUILD_ALL_ORCHESTRATOR.md
