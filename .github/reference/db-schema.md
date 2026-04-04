# LitigationOS Database Schema Reference
# Extracted from copilot-instructions.md for context-window efficiency
# IMPORTANT: Always verify actual schema with PRAGMA table_info(table_name) before querying

---

## Core Authority Tables

| Table | Purpose | Key Columns |
|-------|---------|-------------|
| `auth_rules` | Michigan Court Rules full text | rule_number, title, full_text, rule_type |
| `auth_rules_fts` | FTS5 index on auth_rules | (MATCH queries) |
| `auth_authority_passages` | Authority passage excerpts | passage_text, section, source_file |
| `auth_passages_fts` | FTS5 index on passages | (MATCH queries) |
| `auth_authority_nodes` | Authority graph nodes | id, label, node_type |
| `auth_authority_edges` | Authority graph edges | source_id, target_id, edge_type |
| `auth_benchbook_entries` | Judicial benchbook sections | section, title, content |
| `auth_benchbook_violations` | Benchbook violation findings | rule, judge, severity, matching_text |
| `rules_text` | Statute/rule text blocks | rule, chapter, context, source_doc |
| `rules_text_fts` | FTS5 index on rules_text | (MATCH queries) |
| `court_rules` | Court rules with context | rule, chapter, context, authority_id |
| `legal_reference_docs` | Legal reference sections | heading, body, source_file |
| `master_citations` | All extracted citations | citation, cite_type, context, source_file |

## Evidence & Documents Tables

| Table | Purpose | Key Columns |
|-------|---------|-------------|
| `documents` | Ingested document inventory | file_path, file_name, file_size_bytes |
| `evidence_quotes` | 175,092 extracted evidence quotes | id, source_file, quote_text, page_number, category, lane, relevance_score, filing_refs, tags |
| `evidence_fts` | FTS5 index on evidence | quote_text, category, tags, source_file (MATCH queries) |
| `md_sections` | Markdown doc sections | section_title, content, source_file |
| `md_sections_fts` | FTS5 index on md_sections | (MATCH queries) |
| `pages` | Raw page text | document_id, page_number, text_content |
| `pages_fts` | FTS5 index on pages | (MATCH queries) |

## Case Intelligence Tables

| Table | Purpose | Key Columns |
|-------|---------|-------------|
| `claims` | Legal claims/propositions | classification, actor, proposition, status |
| `claims_matrix` | Claims cross-reference | (claims analysis) |
| `deadlines` | Procedural deadlines | id, title, due_date, filing_id, court, case_number, status, urgency, notes |
| `docket_events` | Docket event timeline | event_date_iso, title, event_type, summary |
| `vehicles` | Procedural vehicles/motions | case_lane, title, forum, vehicle_type, status |
| `filing_readiness` | Filing readiness scores | authority_score, evidence_score, compliance_score |
| `gap_tickets` | Identified gaps to fill | gap_type, description, severity, resolution_status |
| `contradiction_map` | Contradictions (populate via CHIMERA engine) | id, claim_id, source_a, source_b, contradiction_text, severity, lane |
| `impeachment_matrix` | 5,181 impeachment items | id, category, evidence_summary, source_file, quote_text, impeachment_value, cross_exam_question, filing_relevance, event_date |
| `judicial_violations` | 1,939 violations | id, violation_type, description, date_occurred, mcr_rule, canon, source_file, source_quote, severity, lane |
| `adversary_models` | Anticipated opposing arguments | attack_type, rebuttal_strategy, rebuttal_authority |
| `risk_events` | Litigation risk tracking | risk_class, severity, title, cure_deadline_clock |
| `legal_action_scores` | Action readiness scores | action_name, lane, overall_score, gaps |

## System & Data Tables

| Table | Purpose |
|-------|---------|
| `atoms` | Atomic knowledge units |
| `brain_nuclei` | Knowledge cluster health |
| `convergence_log` | Delta cycle convergence |
| `validation_results` | Validation run results |
| `system_registry` | Registered subsystems |
| `mllm_improvement_cycles` | MLLM training metrics |
| `master_csv_data` / `master_csv_fts` | Ingested CSV data + FTS |
| `tfidf_index` | TF-IDF feature index |
| `authorities_index` / `authorities_nodes` / `authorities_edges` | Authority search graph |
| `authority_chains` / `authority_shards` | Authority chain-of-reasoning |
| `court_rule_graphs` / `graph_nodes` | Rule relationship graphs |
| `md_cross_refs` / `md_evolution_log` | Cross-references & doc evolution |
| `pipeline_runs` / `pipeline_errors` | Pipeline execution log |
| `error_telemetry` | System error tracking |
| `rule_audit_results` / `audit_metrics` | Compliance audit data |
| `hydra_genetic_memory` | HYDRA failure patterns and evolved prompts |
| `agent_fleet_registry` | 55 agent definitions with status |
| `agent_run_log` | Agent execution history |
| `agent_anti_patterns` | Detected anti-patterns in agent behavior |

## FTS5 Indexes (10 search interfaces)

| Index | Table | Est. Rows | Content Columns |
|-------|-------|-----------|-----------------|
| `evidence_fts` | evidence_quotes | 92K | quote_text, category, tags, source_file |
| `timeline_fts` | timeline_events | 24K | event_text, category, actor |
| `json_atoms_fts` | atoms | 208K | atom content |
| `legal_knowledge_fts` | legal_reference_docs | 287 | heading, body |
| `court_rules_fts` | court_rules | 84 | rule, chapter, context |
| `downloads_pages_fts` | downloads_pages | 4.7K | page text |
| `authority_fts` | authorities_index | 743 | authority text |
| `pages_fts` | pages | 78K | text_content |
| `md_sections_fts` | md_sections | varies | section_title, content |
| `master_data_fts` | master_csv_data | varies | row text |

## CRITICAL: Schema Verification Protocol

**NEVER trust this reference blindly.** Column names documented here may be stale.
Before writing any query against an unfamiliar table:

```sql
-- Step 1: Verify table exists
SELECT name FROM sqlite_master WHERE type='table' AND name='target_table';

-- Step 2: Get actual columns
PRAGMA table_info(target_table);

-- Step 3: Sample 3 rows to understand data shape
SELECT * FROM target_table LIMIT 3;
```

This prevents the recurring pattern where MCP tools crash on wrong column names
(e.g., fleet_status assumed `metric`/`value` columns — actual: `analysis_type`/`score`).
