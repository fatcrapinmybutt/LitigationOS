# MCP Tool Reference — LitigationOS

> **Auto-generated from source code audit**
> Sources: `00_SYSTEM/mcp_server/litigation_context_mcp/server.py` (38 tools),
> `00_SYSTEM/mcp_server/tools_v3_bridge.py` (9 tools)
> **Total: 47 tools**

---

## Tool Inventory

| # | Tool Name | Category | Source | Description |
|---|-----------|----------|--------|-------------|
| 1 | `litigation_scan_drives` | Core | server.py | Scan local drives/folder for PDF files without ingesting |
| 2 | `litigation_ingest_pdf` | Core | server.py | Extract text from a single PDF and store in knowledge base |
| 3 | `litigation_bulk_ingest` | Core | server.py | Scan directory and ingest all PDF files found |
| 4 | `litigation_search` | Search | server.py | Full-text FTS5 search across all ingested PDF content |
| 5 | `litigation_list_documents` | Core | server.py | List all documents in knowledge base with metadata |
| 6 | `litigation_get_document` | Core | server.py | Retrieve full extracted text of a document by ID |
| 7 | `litigation_delete_document` | Core | server.py | Remove a document from the knowledge base (keeps original PDF) |
| 8 | `litigation_get_stats` | Core | server.py | Get knowledge base statistics including graphs, rules, risk data |
| 9 | `litigation_lookup_rule` | Graph | server.py | Look up Michigan Court Rules (MCR/MCL) by citation or keyword |
| 10 | `litigation_query_graph` | Graph | server.py | Search knowledge graph for authorities, case law, forms |
| 11 | `litigation_assess_risk` | Analysis | server.py | Assess litigation risks with severity scores and cure steps |
| 12 | `litigation_lookup_authority` | Graph | server.py | Look up legal authorities with pin cites |
| 13 | `litigation_get_vehicle_map` | Evolution | server.py | Map relief type to litigation vehicle and authority chain |
| 14 | `litigation_get_subagent_spec` | System | server.py | Retrieve SUPERPIN sub-agent specification |
| 15 | `litigation_self_test` | QA | server.py | Run diagnostic self-tests on the litigation database |
| 16 | `litigation_self_audit` | QA | server.py | Run comprehensive data-quality audit with scoring |
| 17 | `litigation_convergence_status` | Analysis | server.py | Check convergence status, quality score, blockers |
| 18 | `litigation_evolve_files` | Evolution | server.py | Evolve .md/.txt files into cross-reference knowledge layer |
| 19 | `litigation_evolve_pdfs` | Evolution | server.py | Evolve ingested PDF pages into cross-reference layer |
| 20 | `litigation_search_evolved` | Search | server.py | FTS5 search across all evolved content |
| 21 | `litigation_cross_refs` | Graph | server.py | Query cross-reference network by value and type |
| 22 | `litigation_evolution_stats` | Analysis | server.py | Evolution coverage statistics dashboard |
| 23 | `litigation_health` | System | server.py | Server health, circuit breaker state, error telemetry |
| 24 | `god_system_status` | System | server.py | GOD-level system status dashboard |
| 25 | `god_ingest_master_csv` | Filing | server.py | Ingest master CSV datasets into GOD knowledge base |
| 26 | `god_query_master` | Search | server.py | Search across master data with optional dataset filter |
| 27 | `god_vector_search` | Search | server.py | Vector similarity search across knowledge base |
| 28 | `god_compute_deadlines` | Deadline | server.py | Compute legal deadlines from trigger event and date |
| 29 | `god_red_team` | Analysis | server.py | Red-team validate a legal claim or argument |
| 30 | `god_evidence_chain` | Evidence | server.py | Trace evidence chain for a legal claim |
| 31 | `god_swarm_dispatch` | System | server.py | Dispatch task to agent swarm for ranked recommendations |
| 32 | `fleet_status` | Fleet | server.py | DELTA9 agent fleet status: files, atoms, findings |
| 33 | `fleet_damages` | Fleet | server.py | Calculated damages for all legal actions across lanes |
| 34 | `fleet_ready_actions` | Fleet | server.py | Legal actions READY TO FILE (score >= 70) |
| 35 | `fleet_judicial_intel` | Fleet | server.py | Judicial intelligence findings for specific judges |
| 36 | `litigation_upcoming_deadlines` | Deadline | server.py | Query upcoming court deadlines with urgency indicators |
| 37 | `litigation_filing_search` | Filing | server.py | Search filings by case, court, or type |
| 38 | `litigation_evidence_lookup` | Evidence | server.py | Search evidence by keyword and optional date range |
| 39 | `litigation_case_health` | Meta | bridge | Case health dashboard — quotes, harms, impeachment, claims |
| 40 | `litigation_adversary_threats` | Meta | bridge | Ranked adversary threat matrix with harm counts |
| 41 | `litigation_filing_pipeline` | Filing | bridge | Filing pipeline — action, phase, readiness %, risk, gaps |
| 42 | `litigation_dedup_status` | Meta | bridge | Deduplication aggregate stats |
| 43 | `litigation_dedup_duplicates` | Meta | bridge | List duplicate files with paths, hashes, action status |
| 44 | `litigation_drive_summary` | Meta | bridge | Per-drive file summary — counts, bytes, duplicates |
| 45 | `litigation_drive_org_log` | Meta | bridge | Drive organization action log with status filter |
| 46 | `litigation_query_benchmarks` | Meta | bridge | Recent query performance benchmarks |
| 47 | `litigation_agent_inventory` | Fleet | bridge | List all Copilot agents and skills with metadata |

---

## Category Summary

| Category | Count | Tools |
|----------|-------|-------|
| **Core** | 6 | scan_drives, ingest_pdf, bulk_ingest, list_documents, get_document, delete_document, get_stats |
| **Search** | 4 | search, search_evolved, god_query_master, god_vector_search |
| **Graph** | 4 | lookup_rule, query_graph, lookup_authority, cross_refs |
| **Evolution** | 3 | evolve_files, evolve_pdfs, get_vehicle_map |
| **Analysis** | 4 | assess_risk, convergence_status, evolution_stats, god_red_team |
| **Filing** | 3 | god_ingest_master_csv, filing_search, filing_pipeline |
| **Evidence** | 2 | god_evidence_chain, evidence_lookup |
| **Deadline** | 2 | god_compute_deadlines, upcoming_deadlines |
| **Fleet** | 5 | fleet_status, fleet_damages, fleet_ready_actions, fleet_judicial_intel, agent_inventory |
| **QA** | 2 | self_test, self_audit |
| **System** | 4 | health, god_system_status, god_swarm_dispatch, get_subagent_spec |
| **Meta** | 6 | case_health, adversary_threats, dedup_status, dedup_duplicates, drive_summary, drive_org_log, query_benchmarks |

---

## Per-Tool Documentation

### Core — PDF Knowledge Base

#### `litigation_scan_drives`
Scan local drives or a specific folder for PDF files without ingesting them.

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `path` | `Optional[str]` | `None` | Folder path to scan (scans default drives if omitted) |
| `max_results` | `int` | `500` | Maximum PDFs to return (1–10000) |
| `response_format` | `ResponseFormat` | `MARKDOWN` | Output format |

```
Example: litigation_scan_drives(path="C:\\Users\\andre\\LitigationOS\\07_PDF", max_results=100)
```

#### `litigation_ingest_pdf`
Extract text from a single PDF file and store it permanently in the knowledge base. Extracts page-by-page with error resilience. Skips if already indexed. Deduplicates by content hash.

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `file_path` | `str` | — | Full path to the PDF file (min 3 chars) |
| `response_format` | `ResponseFormat` | `MARKDOWN` | Output format |

```
Example: litigation_ingest_pdf(file_path="C:\\case_files\\motion.pdf")
```

#### `litigation_bulk_ingest`
Scan a directory and ingest all PDF files found. Walks directory tree, skips indexed files.

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `path` | `str` | — | Directory to scan |
| `max_files` | `int` | `100` | Maximum files to ingest |
| `skip_existing` | `bool` | `True` | Skip already-indexed files |
| `response_format` | `ResponseFormat` | `MARKDOWN` | Output format |

```
Example: litigation_bulk_ingest(path="D:\\EVIDENCE", max_files=500)
```

#### `litigation_list_documents`
List all documents in the knowledge base with metadata.

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `limit` | `int` | `50` | Results per page (1–500) |
| `offset` | `int` | `0` | Pagination offset |
| `name_filter` | `Optional[str]` | `None` | Filter by document name substring |
| `response_format` | `ResponseFormat` | `MARKDOWN` | Output format |

#### `litigation_get_document`
Retrieve the full extracted text of a specific document by ID.

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `document_id` | `int` | — | Document ID (>= 1) |
| `page_numbers` | `Optional[List[int]]` | `None` | Specific page numbers to retrieve |
| `response_format` | `ResponseFormat` | `MARKDOWN` | Output format |

#### `litigation_delete_document`
Remove a document and all its pages from the knowledge base. Does NOT delete the original PDF file.

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `document_id` | `int` | — | Document ID to remove (>= 1) |

#### `litigation_get_stats`
Get knowledge base statistics including graphs, rules, and risk data.

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `response_format` | `ResponseFormat` | `MARKDOWN` | Output format |

---

### Search

#### `litigation_search`
Full-text search across all ingested PDF content using SQLite FTS5 with porter stemming. Supports AND/OR/NOT, quoted phrases, and prefix* matching.

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `query` | `str` | — | Search query (min 1 char) |
| `limit` | `int` | `20` | Results to return (1–100) |
| `offset` | `int` | `0` | Pagination offset |
| `response_format` | `ResponseFormat` | `MARKDOWN` | Output format |

```
Example: litigation_search(query="MCR 3.706 AND custody")
```

#### `litigation_search_evolved`
FTS5 search across all evolved content (md, txt, pdf sections).

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `query` | `str` | — | Search query |
| `source_type` | `Optional[str]` | `None` | Filter: md, txt, pdf, or all |
| `limit` | `int` | `20` | Results (1–100) |
| `response_format` | `ResponseFormat` | `MARKDOWN` | Output format |

#### `god_query_master`
Search across master CSV data with optional dataset filtering.

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `query` | `str` | — | Search query |
| `dataset` | `Optional[str]` | `None` | Dataset name to filter |
| `limit` | `int` | `20` | Results (1–100) |
| `response_format` | `ResponseFormat` | `MARKDOWN` | Output format |

#### `god_vector_search`
Perform vector similarity search across the knowledge base.

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `query` | `str` | — | Search query |
| `top_k` | `int` | `10` | Top results to return (1–50) |
| `response_format` | `ResponseFormat` | `MARKDOWN` | Output format |

---

### Graph — Knowledge Graph Queries

#### `litigation_lookup_rule`
Look up Michigan Court Rules (MCR/MCL) by citation or keyword. Searches 873 MCR rules with context snippets.

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `query` | `str` | — | Citation or keyword (1–200 chars). E.g., "MCR 3.706", "custody" |
| `limit` | `int` | `20` | Results (1–100) |
| `offset` | `int` | `0` | Pagination offset |
| `response_format` | `ResponseFormat` | `MARKDOWN` | Output format |

#### `litigation_query_graph`
Search litigation knowledge graph for authorities, case law, forms, and procedures.

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `query` | `str` | — | Search query (1–300 chars) |
| `node_type` | `Optional[str]` | `None` | Filter: authority, CASELAW, FORM, PROCEDURE |
| `graph_source` | `Optional[str]` | `None` | Specific graph to search |
| `limit` | `int` | `20` | Results (1–100) |
| `offset` | `int` | `0` | Pagination offset |
| `response_format` | `ResponseFormat` | `MARKDOWN` | Output format |

#### `litigation_lookup_authority`
Look up specific legal authorities (case law, statutes, court rules) with pin cites.

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `query` | `str` | — | Authority search (1–300 chars) |
| `node_type` | `Optional[str]` | `None` | Filter by type |
| `graph_source` | `Optional[str]` | `None` | Specific graph source |
| `limit` | `int` | `20` | Results (1–100) |
| `offset` | `int` | `0` | Pagination offset |
| `response_format` | `ResponseFormat` | `MARKDOWN` | Output format |

#### `litigation_cross_refs`
Query the cross-reference network by value and optionally filter by ref_type.

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `query` | `str` | — | Reference value to search |
| `ref_type` | `Optional[str]` | `None` | Filter: agent, rule, vehicle, risk, authority |
| `limit` | `int` | `50` | Results (1–200) |
| `response_format` | `ResponseFormat` | `MARKDOWN` | Output format |

---

### Evolution Pipeline

#### `litigation_evolve_files`
Trigger evolution on .md and/or .txt files in a directory. Parses into sections, extracts cross-references, links to knowledge graph. Idempotent.

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `directory` | `str` | — | Directory path to scan |
| `file_types` | `str` | `"both"` | File types: md, txt, or both |
| `response_format` | `ResponseFormat` | `MARKDOWN` | Output format |

#### `litigation_evolve_pdfs`
Evolve ingested PDF pages into the cross-reference knowledge layer. Idempotent.

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `document_id` | `Optional[int]` | `None` | Specific document ID, or all if omitted |
| `response_format` | `ResponseFormat` | `MARKDOWN` | Output format |

#### `litigation_get_vehicle_map`
Map a relief type to its litigation vehicle, authority chain, required elements, and deadlines. Searches SUPERPIN evolved .md sections.

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `relief_type` | `str` | — | Relief type (1–200 chars) |
| `response_format` | `ResponseFormat` | `MARKDOWN` | Output format |

```
Example: litigation_get_vehicle_map(relief_type="disqualification")
```

---

### Analysis

#### `litigation_assess_risk`
Assess litigation risks from the risk event taxonomy with severity scores and cure steps.

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `severity_min` | `int` | `0` | Minimum severity (0–100) |
| `risk_class` | `Optional[str]` | `None` | Risk class filter |
| `response_format` | `ResponseFormat` | `MARKDOWN` | Output format |

#### `litigation_convergence_status`
Check convergence status showing CONVERGED flag, quality score, ΔNEW items, BLOCKERS, and emergence signals.

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `response_format` | `ResponseFormat` | `MARKDOWN` | Output format |

#### `litigation_evolution_stats`
Get evolution coverage statistics dashboard.

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `response_format` | `ResponseFormat` | `MARKDOWN` | Output format |

#### `god_red_team`
Red-team validate a legal claim or argument. Scores authority, evidence, and consistency. Reports findings by severity and overall FILING_READY status.

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `claim` | `str` | — | Claim or argument to validate |
| `response_format` | `ResponseFormat` | `MARKDOWN` | Output format |

```
Example: god_red_team(claim="Judge McNeill violated MCR 2.003 by failing to disclose ex parte communications")
```

---

### Filing

#### `god_ingest_master_csv`
Ingest master CSV datasets into the GOD knowledge base.

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `data_dir` | `str` | `D:\LITIGATIONOS_DATA` | Data directory |
| `dataset` | `Optional[str]` | `None` | Specific dataset to ingest |
| `response_format` | `ResponseFormat` | `MARKDOWN` | Output format |

#### `litigation_filing_search`
Search filings across ingested documents and master CSV data by case, court, or type.

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `query` | `str` | — | Search query |
| `filing_type` | `Optional[str]` | `None` | Filter: motion, brief, order, petition, complaint, etc. |
| `limit` | `int` | `25` | Results (1–100) |
| `response_format` | `ResponseFormat` | `MARKDOWN` | Output format |

#### `litigation_filing_pipeline` *(bridge)*
Filing pipeline — every action with phase, readiness %, risk score, gaps.

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| *(none)* | — | — | Returns full pipeline status |

---

### Evidence

#### `god_evidence_chain`
Trace the evidence chain for a legal claim (claim → sections → cross-refs → sources).

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `claim` | `str` | — | Claim to trace |
| `response_format` | `ResponseFormat` | `MARKDOWN` | Output format |

#### `litigation_evidence_lookup`
Search evidence by keyword and optional date range in PDFs and master CSV evidence index.

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `keyword` | `str` | — | Evidence keyword |
| `date_from` | `Optional[str]` | `None` | ISO date (YYYY-MM-DD) start |
| `date_to` | `Optional[str]` | `None` | ISO date (YYYY-MM-DD) end |
| `limit` | `int` | `25` | Results (1–100) |
| `response_format` | `ResponseFormat` | `MARKDOWN` | Output format |

---

### Deadline

#### `god_compute_deadlines`
Compute legal deadlines from trigger event and date using jurisdiction-specific rules.

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `trigger_event` | `str` | — | Event triggering deadline calculation |
| `trigger_date` | `str` | — | ISO date of trigger event |
| `jurisdiction` | `str` | `"MI"` | Jurisdiction code |
| `response_format` | `ResponseFormat` | `MARKDOWN` | Output format |

```
Example: god_compute_deadlines(trigger_event="motion_filed", trigger_date="2026-03-01", jurisdiction="MI")
```

#### `litigation_upcoming_deadlines`
Query upcoming court deadlines with urgency indicators within requested window.

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `days_ahead` | `int` | `30` | Days to look ahead (1–365) |
| `trigger_event` | `Optional[str]` | `None` | Filter by specific trigger |
| `response_format` | `ResponseFormat` | `MARKDOWN` | Output format |

---

### Fleet Intelligence

#### `fleet_status`
Get DELTA9 agent fleet status: file counts, atoms, judicial findings, action scores, filing readiness.

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| *(none)* | — | — | No parameters required |

#### `fleet_damages`
Get calculated damages for all legal actions across Lane A (Watson/Custody), Lane B (Shady Oaks/Housing), Lane C (Federal §1983).

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| *(none)* | — | — | No parameters required |

#### `fleet_ready_actions`
Get all legal actions that are READY TO FILE (composite score >= 70).

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| *(none)* | — | — | No parameters required |

#### `fleet_judicial_intel`
Get judicial intelligence findings for specific judges showing patterns, biases, misconduct indicators.

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `judge` | `str` | `""` | Judge name filter (empty = all judges) |

#### `litigation_agent_inventory` *(bridge)*
List all Copilot agents and skills with counts and file metadata.

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| *(none)* | — | — | No parameters required |

---

### QA / Diagnostics

#### `litigation_self_test`
Run diagnostic self-tests on the litigation database (connectivity, schema, FTS5, graph counts).

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `response_format` | `ResponseFormat` | `MARKDOWN` | Output format |

#### `litigation_self_audit`
Run a comprehensive data-quality audit on the litigation database with quality scoring.

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `response_format` | `ResponseFormat` | `MARKDOWN` | Output format |

---

### System

#### `litigation_health`
Get server health status, circuit breaker state, and recent error telemetry (last 24h).

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `reset_circuit_breaker` | `bool` | `False` | Reset the circuit breaker |
| `response_format` | `ResponseFormat` | `MARKDOWN` | Output format |

#### `god_system_status`
Get GOD-level system status dashboard scanning system registry.

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `response_format` | `ResponseFormat` | `MARKDOWN` | Output format |

#### `god_swarm_dispatch`
Dispatch a task to the agent swarm for ranked agent recommendations.

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `task` | `str` | — | Task description |
| `response_format` | `ResponseFormat` | `MARKDOWN` | Output format |

#### `litigation_get_subagent_spec`
Retrieve the specification for a SUPERPIN sub-agent (role, inputs, outputs, triggers).

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `agent_name` | `str` | — | Agent name (1–200 chars). E.g., AUTH_HARVESTER, DRAFTER_COA |
| `response_format` | `ResponseFormat` | `MARKDOWN` | Output format |

---

### Meta — v3 Bridge Dashboards

#### `litigation_case_health` *(bridge)*
Case health dashboard — quotes, harms, impeachment, contradictions, claims, deadlines.

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| *(none)* | — | — | No parameters required |

#### `litigation_adversary_threats` *(bridge)*
Ranked adversary threat matrix with harm counts and category spread.

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `limit` | `int` | `20` | Max results (1–200) |

#### `litigation_dedup_status` *(bridge)*
Deduplication aggregate stats — total files, unique hashes, duplicates, drives.

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| *(none)* | — | — | No parameters required |

#### `litigation_dedup_duplicates` *(bridge)*
List duplicate files with path, size, SHA-256, canonical ref, and action status.

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `drive` | `Optional[str]` | `None` | Drive letter filter |
| `limit` | `int` | `50` | Max results (1–500) |

#### `litigation_drive_summary` *(bridge)*
Per-drive file summary — file count, total bytes, unique names, duplicates, status.

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| *(none)* | — | — | No parameters required |

#### `litigation_drive_org_log` *(bridge)*
Drive organization action log with optional status filter.

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `status` | `Optional[str]` | `None` | Status filter |
| `limit` | `int` | `50` | Max results (1–500) |

#### `litigation_query_benchmarks` *(bridge)*
Recent query performance benchmarks — name, execution time (ms), row count.

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `limit` | `int` | `20` | Max results (1–200) |

---

## Documentation vs Implementation Gap Analysis

### Documented in `copilot-instructions.md` but NOT found as MCP tools

The copilot instructions (v18.0) document **45 tools across 9 categories**. The actual implementation has **47 tools** but with different organization:

| Documented Category | Documented Count | Actual Implementation |
|--------------------|-----------------|-----------------------|
| Core | 10 | 6 in server.py — `filing_readiness`, `filing_validate`, `filing_assemble`, `efiling_prep` are **NOT implemented as MCP tools** (may exist as pipeline agents instead) |
| Filing | 8 | 3 tools — `filing_validate`, `filing_assemble`, `efiling_prep`, `brief_compliance`, `placeholder_scan`, `placeholder_resolve`, `filing_export` are **NOT implemented** |
| Evidence | 7 | 2 tools — `evidence_chain` (as god_evidence_chain), `evidence_lookup`. Missing: `evidence_gaps`, `evidence_link`, `evidence_authenticate`, `bates_assign`, `exhibit_index`, `evidence_timeline` |
| Deadline | 5 | 2 tools — Missing: `deadline_ics`, `deadline_urgency`, `deadline_add`, `deadline_update` |
| Analysis | 5 | 4 tools — Missing: `impeachment_search`, `contradiction_find`, `judicial_bias_scan` (these exist as fleet/agent operations instead) |
| QA | 4 | 2 tools — Missing: `signature_check`, `service_check` |
| Backup | 3 | 0 tools — `backup_create`, `backup_version`, `backup_report` are **NOT implemented** |
| Calendar | 2 | 0 tools — `calendar_generate`, `calendar_sync` are **NOT implemented** |
| System | 1 | 4 tools — `system_health` exists as `litigation_health` |

### Undocumented tools (implemented but not in copilot-instructions.md)

| Tool | Category | Notes |
|------|----------|-------|
| `god_system_status` | System | GOD-level dashboard — not in instructions |
| `god_ingest_master_csv` | Filing | CSV ingest — not in instructions |
| `god_query_master` | Search | Master data search — not in instructions |
| `god_vector_search` | Search | Vector similarity — not in instructions |
| `god_red_team` | Analysis | Red-team validation — not in instructions |
| `god_swarm_dispatch` | System | Agent swarm dispatch — not in instructions |
| `litigation_get_vehicle_map` | Evolution | SUPERPIN vehicle mapping — not in instructions |
| `litigation_get_subagent_spec` | System | Agent spec retrieval — not in instructions |
| `litigation_evolve_files` | Evolution | File evolution — not in instructions |
| `litigation_evolve_pdfs` | Evolution | PDF evolution — not in instructions |
| `litigation_search_evolved` | Search | Evolved content search — not in instructions |
| `litigation_cross_refs` | Graph | Cross-reference queries — not in instructions |
| `litigation_evolution_stats` | Analysis | Evolution statistics — not in instructions |
| `litigation_convergence_status` | Analysis | Convergence status — not in instructions |
| All 9 bridge tools | Meta/Fleet | Entire v3 bridge layer — not in instructions |

### Summary

- **Documented but missing**: ~22 tools claimed in instructions that don't exist as MCP endpoints
- **Undocumented but implemented**: ~23 tools that exist but aren't documented in instructions
- **Recommendation**: Update `copilot-instructions.md` to reflect the actual 47-tool inventory
