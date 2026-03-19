# COPILOT STARTUP STATE — LitigationOS 2026 v1.0
## Generated: 2026-02-24 23:07

---

## SYSTEM IDENTITY

| Property | Value |
|----------|-------|
| System | MBP LitigationOS 2026 v1.0 |
| Architecture | Michigan-first litigation command center |
| Database | C:\Users\andre\litigation_context.db (705,249 rows, 145 tables) |
| Canonical Root | C:\Users\andre\LitigationOS |
| Operator | Andrew Pigors (pro se litigant) |
| Adversary | Tiffany Watson (fka Pigors) |
| Days Separated | 329+ (since July 29, 2025) |

---

## CASE MATRIX

| Lane | Case | Court | Judge | Status |
|------|------|-------|-------|--------|
| A | 2024-001507-DC (Custody) | 14th Circuit, Muskegon | Hon. Jenny L. McNeill | Active |
| B | 2025-002760-CZ (Housing) | Van Buren County Circuit | TBD | Active |
| C | MULTI (Convergence) | Cross-lane | Various | Active |
| D | 2023-5907-PP (PPO) | 14th Circuit, Muskegon | Hon. Jenny L. McNeill | Active |
| E | MULTI (Judicial Misconduct) | JTC / MSC | Various | Active |
| F | COA 366810 (Appeal) | MI Court of Appeals | Panel TBD | Active |

---

## DATABASE INVENTORY (705,249 total rows)

### Key Tables
| Table | Rows | Purpose |
|-------|------|---------|
| `md_sections` | 213,417 | — |
| `master_citations` | 160,030 | — |
| `evidence_file_index` | 153,661 | — |
| `chatgpt_conversations` | 139,693 | — |
| `impeachment_items` | 15,171 | — |
| `contradiction_map` | 10,558 | — |
| `auth_rules` | 5,633 | — |
| `rules_text` | 2,021 | — |
| `pages` | 1,735 | — |
| `auth_authority_passages` | 1,239 | — |
| `court_rules` | 873 | — |
| `auth_benchbook_violations` | 540 | — |
| `evidence_quotes` | 405 | — |
| `quality_validation_results` | 66 | — |
| `claims` | 57 | — |
| `legal_reference_docs` | 51 | — |
| `risk_events` | 21 | — |
| `filing_packages` | 20 | — |
| `auth_benchbook_entries` | 20 | — |
| `system_files` | 11 | — |
| `adversary_models` | 10 | — |
| `docket_events` | 7 | — |
| `vehicles` | 6 | — |
| `deadlines` | 4 | — |

### All Tables (145)
`adversary_models`, `alienation_tactics`, `atoms`, `audit_metrics`, `auth_authority_edges`, `auth_authority_nodes`, `auth_authority_passages`, `auth_benchbook_entries`, `auth_benchbook_violations`, `auth_ingestion_stats`, `auth_passages_fts`, `auth_passages_fts_config`, `auth_passages_fts_data`, `auth_passages_fts_docsize`, `auth_passages_fts_idx`, `auth_rules`, `auth_rules_fts`, `auth_rules_fts_config`, `auth_rules_fts_data`, `auth_rules_fts_docsize`, `auth_rules_fts_idx`, `authorities_edges`, `authorities_index`, `authorities_nodes`, `authority_chains`, `authority_shards`, `benchbook_violation_findings`, `berry_investigation`, `brain_nuclei`, `chatgpt_conversations`, `chronological_misconduct`, `claims`, `claims_matrix`, `confidence_calibration`, `context_snapshots`, `contradiction_map`, `convergence_log`, `court_documents_v4`, `court_rule_graphs`, `court_rules`, `deadlines`, `docket_events`, `documents`, `drive_evidence_scan`, `error_telemetry`, `evidence_content_extracts`, `evidence_file_index`, `evidence_quotes`, `evidence_quotes_fts`, `evidence_quotes_fts_config`, `evidence_quotes_fts_data`, `evidence_quotes_fts_docsize`, `evidence_quotes_fts_idx`, `evolution_cycles`, `feedback_loops`, `filing_analysis`, `filing_packages`, `filing_readiness`, `forensic_judicial_analysis`, `fts_auth_rules`, `fts_auth_rules_config`, `fts_auth_rules_data`, `fts_auth_rules_docsize`, `fts_auth_rules_idx`, `fts_evidence`, `fts_evidence_config`, `fts_evidence_data`, `fts_evidence_docsize`, `fts_evidence_idx`, `fts_research`, `fts_research_config`, `fts_research_data`, `fts_research_docsize`, `fts_research_idx`, `gap_tickets`, `global_chronology`, `global_harms_violations`, `global_weaponization`, `graph_load_log`, `graph_nodes`, `impeachment_items`, `judicial_violations`, `knowledge_gaps`, `legal_action_scores`, `legal_reference_docs`, `master_citations`, `master_csv_data`, `master_csv_fts`, `master_csv_fts_config`, `master_csv_fts_data`, `master_csv_fts_docsize`, `master_csv_fts_idx`, `master_timeline`, `md_cross_refs`, `md_evolution_log`, `md_sections`, `md_sections_fts`, `md_sections_fts_config`, `md_sections_fts_data`, `md_sections_fts_docsize`, `md_sections_fts_idx`, `mllm_improvement_cycles`, `msc_filing_tracker`, `msc_research`, `narrative`, `narrative2`, `noise_blacklist`, `nucleus_apex_supergraph_20250908_030140_nodes_1`, `pages`, `pages_fts`, `pages_fts_config`, `pages_fts_data`, `pages_fts_docsize`, `pages_fts_idx`, `parental_alienation_evidence`, `pipeline_errors`, `pipeline_runs`, `quality_validation_results`, `query_history`, `research_summaries`, `risk_events`, `rule_audit_results`, `rules_text`, `rules_text_fts`, `rules_text_fts_config`, `rules_text_fts_data`, `rules_text_fts_docsize`, `rules_text_fts_idx`, `scanned_pdf_triage`, `shadyoaks_claim_table`, `shadyoaks_claim_table_2`, `shadyoaks_contradiction_map_normalized`, `shadyoaks_evidence`, `shadyoaks_ingest_log`, `shadyoaks_tail_preview_2`, `sqlite_sequence`, `sqlite_stat1`, `sqlite_stat4`, `system_files`, `system_registry`, `tfidf_index`, `validation_results`, `vehicles`, `venue_bias_evidence`, `watsons_evidence_docs`

### FTS5 Search Indexes (35)
`auth_passages_fts`, `auth_passages_fts_config`, `auth_passages_fts_data`, `auth_passages_fts_docsize`, `auth_passages_fts_idx`, `auth_rules_fts`, `auth_rules_fts_config`, `auth_rules_fts_data`, `auth_rules_fts_docsize`, `auth_rules_fts_idx`, `evidence_quotes_fts`, `evidence_quotes_fts_config`, `evidence_quotes_fts_data`, `evidence_quotes_fts_docsize`, `evidence_quotes_fts_idx`, `master_csv_fts`, `master_csv_fts_config`, `master_csv_fts_data`, `master_csv_fts_docsize`, `master_csv_fts_idx`, `md_sections_fts`, `md_sections_fts_config`, `md_sections_fts_data`, `md_sections_fts_docsize`, `md_sections_fts_idx`, `pages_fts`, `pages_fts_config`, `pages_fts_data`, `pages_fts_docsize`, `pages_fts_idx`, `rules_text_fts`, `rules_text_fts_config`, `rules_text_fts_data`, `rules_text_fts_docsize`, `rules_text_fts_idx`

---

## FILESYSTEM INVENTORY

### LitigationOS Directory Structure
| Directory | Files | Purpose |
|-----------|-------|---------|
| `.github/` | 1 | — |
| `.vscode/` | 3 | — |
| `00_SYSTEM/` | 1,651 | — |
| `01_CASE_FILES/` | 92 | — |
| `01_DATA/` | 1,313 | — |
| `02_AUTHORITY/` | 10 | — |
| `02_EVIDENCE/` | 123,379 | — |
| `02_GRAPHS/` | 3,229 | — |
| `03_EVIDENCE/` | 660 | — |
| `03_LEGAL_AUTHORITIES/` | 54 | — |
| `04_COURT_FILINGS/` | 542 | — |
| `05_ANALYSIS/` | 1,074 | — |
| `05_RESEARCH/` | 7 | — |
| `06_ANALYSIS/` | 13 | — |
| `06_CASE_DATABASES/` | 6 | — |
| `06_DATA/` | 16 | — |
| `06_RISK/` | 32 | — |
| `06_TIMELINES/` | 11 | — |
| `06_VEHICLES/` | 19 | — |
| `07_ARCHIVES/` | 10 | — |
| `07_COURT_DOCUMENTS/` | 31 | — |
| `07_SPECS/` | 18 | — |
| `08_APPS/` | 179,162 | — |
| `99_ARCHIVE/` | 976 | — |
| `_QUARANTINE/` | 1,061 | — |
| `users/` | 0 | — |

**Total LitigationOS files:** 313,370

---

## CAPABILITIES INSTALLED

### Cycle Method Engine (EAGAIN Prevention)
- **Python:** `00_SYSTEM/cycle_method.py` — 4KB chunks, exponential backoff, CycleWriter class
- **Node.js:** `08_APPS/desktop/main/cycleMethod.js` — createCycleQueue(), cycleWrite()
- **Status:** Deployed across all Python scripts and Electron main process

### Legal Skills (5)
| Skill | File | Coverage |
|-------|------|----------|
| Landlord/Tenant | `skill_landlord_tenant.py` | MCL 554, 600.5720, 125.2303, mobile home act |
| Business/Corporate | `skill_business_corporate.py` | Veil piercing, alter ego, LLC rules |
| Torts/Claims | `skill_torts_claims.py` | 8 tort types, MCPA, conversion, treble damages |
| Defenses/Setoffs | `skill_defenses_setoffs.py` | 12 defenses, SOL tracker, pre-built counters |
| Chess Mode | `skill_chess_mode.py` | 8 claim chains, 5-move attack/defense anticipation |

### Tools
| Tool | File | Purpose |
|------|------|---------|
| Exhibit Cover Generator | `00_SYSTEM/tools/exhibit_cover_generator.py` | MRE 901 exhibit covers |
| Filing Packager | `00_SYSTEM/tools/filing_packager.py` | Complete court-ready packages |
| Brain Search | `00_SYSTEM/brain_search.py` | Graph-guided DB search |
| Extract Impeachment | `00_SYSTEM/extract_impeachment.py` | Impeachment material extraction |
| Ingest ChatGPT | `00_SYSTEM/ingest_chatgpt.py` | ChatGPT conversation ingestion |
| Catalogue Builder | `05_ANALYSIS/CATALOGUE/_build_catalogue.py` | 9-volume catalogue generator |

### LLM Engine
| Component | File | Status |
|-----------|------|--------|
| TF-IDF Model | `00_SYSTEM/local_model/model_data/` | 144,179 docs, 98.78% intent accuracy |
| Document Generator | `llm_document_generator.py` | IRAC + alienation injection |
| Pattern Recognition | `llm_pattern_recognition.py` | 540 violations, bias indicators |
| Inference Engine | `inference_engine.py` | JSON-RPC, query/find_authority/check_citations |
| Context Loader | `context_loader.py` | Full/lane/authority context loading |

---

## COURT DOCUMENTS PRODUCED

### Filing Packages
- Lane A (Custody): Motions, venue change, civil complaint
- Lane B (Shady Oaks): 9-count complaint + exhibit index
- Lane D (PPO): Related filings
- Lane E (Misconduct): JTC supplemental brief, MSC superintending control
- Lane F (Appellate): COA 366810 brief (in progress — due April 15, 2026)

### Judicial Encyclopedia (9 Volumes)
Located: `05_ANALYSIS/CATALOGUE/`
- VOL1: Case Matrix (6.6KB)
- VOL2: Judicial Conduct (28.1KB)
- VOL3: Authority Compendium (126.6KB)
- VOL4: Evidence Registry (26.7KB)
- VOL5: Timeline Atlas (5.0KB)
- VOL6: Filing Operations (8.7KB)
- VOL7: Adversary Intelligence (7.6KB + 45.8KB)
- VOL8: Parental Alienation (13.2KB)
- VOL9: Remedies Matrix (5.3KB)

---

## CRITICAL DEADLINES

| Deadline | Date | Authority | Priority |
|----------|------|-----------|----------|
| COA 366810 Brief | April 15, 2026 | MCR 7.212 | **CRITICAL** |

---

## OPERATIONAL RULES

1. **Zero external APIs** — everything runs locally against litigation_context.db
2. **Zero hallucination** — if not in DB, say so explicitly
3. **Adversarial thinking** — always chess-mode, anticipate opposing arguments
4. **Deadline-first** — check deadlines before any recommendation
5. **Pro se aware** — flag procedural traps for self-represented litigant
6. **Court-ready** — every output should be fileable with minimal editing
7. **Parental alienation** — inject into every filing: 329+ days, Factor J, pattern
8. **Cycle Method** — all writes use 4KB chunking (never EAGAIN)
9. **Triple save** — filesystem + DB + Desktop backup
10. **Electron = ZERO network** — desktop app never calls external servers

---

## STARTUP CHECKLIST

On every session start:
1. Verify `litigation_context.db` accessible
2. Identify which case lane(s) the query pertains to (A-F)
3. Check `deadlines` table for critical upcoming dates
4. Load relevant authority context before responding
5. Confirm no external API calls configured
6. Reference this file for system state and capabilities

---
*LitigationOS DIAMOND+++ | Generated by Catalogue Builder*
