# LitigationOS — Reference Catalog
# Auto-generated from copilot-instructions.md v18.0
# This file contains engine inventories, agent directories, and module lists.
# Moved here to keep instructions file focused on behavioral rules.

---

## Delta999 Engine Directory

| Engine | File | Purpose |
|--------|------|---------|
| **LLM Classifier** | `llm_classifier_engine.py` | Auto-classification of documents by type/lane/relevance |
| **Filing Validator** | `filing_validator_engine.py` | MCR compliance checking — format, citation, caption, service rules |
| **Brief Quality** | `brief_quality_engine.py` | Scoring briefs on persuasion, authority, IRAC structure, readability |
| **Opposing Analysis** | `opposing_analysis_engine.py` | Adversary pattern detection — Barnes/Watson tactics, response prediction |
| **Settlement Engine** | `settlement_engine.py` | Case valuation — damages, leverage, risk, settlement range calculation |
| **Doc Assembly** | `doc_assembly_engine.py` | MD → DOCX → PDF pipeline with template injection and Bates stamping |
| **Deadline Alert** | `deadline_alert_engine.py` | Deadline tracking with escalating urgency alerts and calendar sync |
| **DB Lock Manager** | `db_lock_manager.py` v3.0 | EAGAIN prevention — WAL enforcement, busy_timeout, connection pooling |

---

## MANBEARPIG JSON-RPC Methods (via --pipe)

- **Core:** `query`, `find_authority`, `check_citations`, `analyze_document`, `detect_patterns`, `status`, `irac_analysis`, `document_qa`
- **Skills:** `jtc_complaint`, `adversary_predict`, `adversary_wargame`, `filing_package`, `generate_motion`, `analyze_order`, `score_case`, `cluster_evidence`, `build_narrative`, `build_brief`, `find_authority_graph`, `search_citations`, `build_timeline`, `alienation_analysis`, `forensic_report`, `weaponization_report`, `witness_prep`, `risk_dashboard`
- **OMEGA-INFINITY:** `startup_diagnostics`, `deadline_urgency`, `filing_optimizer`, `evidence_gaps`, `session_recall`

50 skills in `local_model/skills/` — lazy-loaded via `SKILL_REGISTRY`. Session recall (`session_recall.py`) provides cross-session learning from `~/.copilot/session-state/`.

---

## CLI Tools Available

| Tool | Purpose |
|------|---------|
| `pandoc` | Document conversion (MD → DOCX → PDF, HTML → MD, etc.) |
| `fd` | Fast file finder (rust-based, replaces `find`) |
| `rg` | ripgrep — fast content search (rust-based, replaces `grep`) |
| `jq` | JSON processor for pipeline data manipulation |

---

## Copilot Agent Directory (64 agents in `.copilot/agents/`)

### Litigation-Specific Agents

| Agent | Purpose |
|-------|---------|
| `adversary-war-room` | Analyze opposing party behavior, predict responses, map weaknesses |
| `appellate-strategy` | Appellate strategy, standard of review, preservation of error |
| `brief-polisher` | Polish briefs for submission, check citation format and compliance |
| `brief-quality-scorer` | Score brief persuasiveness, check citation density |
| `brief-writer` | Write appellate briefs, legal memoranda, substantive arguments |
| `child-best-interest` | Analyze MCL 722.23 best interest factors, score evidence against 12 factors |
| `citation-researcher` | Find legal authorities, verify citations, build authority lists |
| `convergence-coordinator` | Link evidence across lanes, build unified theories, multi-forum strategy |
| `cost-tracker` | Track litigation costs (filing fees, service, copies, mileage) |
| `court-form-finder` | Find correct SCAO/court form for any filing type and jurisdiction |
| `damages-calculator` | Calculate damages across all case lanes, generate damages exhibits |
| `deadline-sentinel` | Track deadlines, calculate filing windows, monitor SOL |
| `deposition-prep` | Build deposition question outlines, identify impeachment traps |
| `discovery-manager` | Manage discovery requests, track responses, identify deficiencies |
| `docket-monitor` | Monitor case dockets, check new entries, calculate response deadlines |
| `document-classifier` | Auto-classify documents by type and route to correct folders |
| `evidence-authenticator` | Authenticate evidence, prepare exhibits, assign Bates numbers |
| `evidence-harvester` | Find, extract, link, validate evidence from litigation database |
| `exhibit-curator` | Select, organize, authenticate, package exhibits for proceedings |
| `exhibit-formatter` | Format exhibits with Bates stamps, tabs, and index generation |
| `federal-1983-specialist` | 42 USC §1983 civil rights claims, qualified immunity analysis |
| `filing-assembler` | Compile court-ready filing packages, assemble exhibits with covers |
| `filing-countdown` | Deadline countdown dashboard for all active filing deadlines |
| `filing-router` | Determine optimal court, jurisdiction, venue, forms, and filing path |
| `financial-analyst` | Financial evidence analysis, child support calculations |
| `foia-tracker` | Track FOIA requests, manage response deadlines, generate appeals |
| `harm-tracker` | Track harms to child, update separation counters, build narratives |
| `hearing-prep` | Prepare for hearings, generate argument outlines and checklists |
| `impeachment-commander` | Build impeachment outlines, find contradictions, prep cross-exam |
| `judge-profiler` | Profile Judge McNeill, track ruling patterns, analyze bias |
| `judicial-bias-detector` | Analyze judicial bias patterns, detect ex parte communications |
| `legal-phase-indexer` | Structure and organize complex legal workflows |
| `legal-research-deep` | Deep multi-source authority search and ranking |
| `mcr-compliance-validator` | Validate filings against MCR for format and compliance |
| `michigan-litigation-orchestrator` | Manage complex multi-step Michigan litigation workflows |
| `motion-drafter` | Draft court motions including emergency motions and motions to compel |
| `motion-generator` | Generate motions from templates using MCR 2.119 format |
| `msc-fleet-commander` | Michigan Supreme Court application strategy and filings |
| `opposing-counsel-analyzer` | Analyze opposing parties' patterns and predict defenses |
| `opposing-counsel-profiler` | Profile Barnes/Martini, track filing patterns |
| `order-compliance-monitor` | Track compliance with existing court orders by all parties |
| `pre-filing-qa` | Pre-filing quality assurance sweep with GO/NO-GO report |
| `pro-se-compliance` | Help pro se litigants with compliance and procedural traps |
| `redaction-agent` | Auto-redact PII and sensitive information from filings |
| `service-tracker` | Track proof of service for every filing across all cases |
| `settlement-calculator` | Calculate case valuation, estimate damages, analyze settlement ranges |
| `spoliation-watcher` | Monitor evidence spoliation risk, track preservation obligations |
| `timeline-builder` | Build case timelines, extract dates, create chronological narratives |
| `transcript-analyzer` | Extract key testimony, rulings, objections from transcripts |
| `witness-profiler` | Build witness profiles, assess credibility, track prior statements |
| `gdrive-watcher` | Check Google Drive sync status, trigger syncs, troubleshoot |

### General-Purpose Agents

| Agent | Purpose |
|-------|---------|
| `context-architect` | Plan multi-file changes by identifying context and dependencies |
| `critical-thinking` | Challenge assumptions, encourage critical thinking |
| `debug` | Debug applications to find and fix bugs |
| `devils-advocate` | Play devil's advocate, find flaws and risks |
| `janitor` | Codebase cleanup and tech debt reduction |
| `ms-sql-dba` | Microsoft SQL Server database operations |
| `plan` | Strategic planning and architecture |
| `planner` | Generate implementation plans for features or refactoring |
| `principal-software-engineer` | Principal-level software engineering guidance |
| `repo-architect` | Bootstrap and validate agentic project structures |
| `research-technical-spike` | Research and validate technical spike documents |
| `se-security-reviewer` | Security-focused code review (OWASP Top 10, Zero Trust) |
| `se-technical-writer` | Technical writing specialist |

---

## Superpower Agents (13 cross-cutting)

| Agent | Role |
|-------|------|
| `fleet-orchestrator` | Coordinates all agents — scheduling, priority, conflict resolution |
| `self-evolution-controller` | Manages MANBEARPIG self-evolution cycles |
| `governance-auditor` | Compliance logging and audit trail for all agent actions |
| `session-continuity` | Cross-session memory and learning via session_recall.py |
| `db-health-monitor` | Monitors litigation_context.db integrity, WAL checkpointing, size |
| `pipeline-scheduler` | Schedules 16-phase pipeline runs with dependency resolution |
| `evidence-ingestion-coordinator` | Coordinates multi-drive evidence scanning and dedup |
| `filing-production-manager` | Manages filing stacks through review → final → filed workflow |
| `quality-gate-enforcer` | Enforces quality thresholds before filings reach COURT_READY |
| `backup-integrity-checker` | Verifies SHA-256 manifests and backup completeness |
| `conflict-resolver` | Detects and resolves lane cross-contamination and data conflicts |
| `metric-dashboard-generator` | Produces system health and case progress dashboards |
| `emergency-motion-accelerator` | Fast-tracks emergency filings with abbreviated review |

---

## Engine Inventory (79 engines in `00_SYSTEM/engines/`)

### Core Filing Engines

| Engine | Purpose |
|--------|---------|
| `filing_validator_engine.py` | MCR compliance — format, citation, caption, service rules |
| `filing_assembly_pipeline.py` | End-to-end filing assembly pipeline |
| `filing_production_pipeline.py` | Filing production orchestration |
| `filing_production_runner.py` | Runs filing production batches |
| `filing_sequencer.py` | Determines optimal filing order |
| `filing_finalizer.py` | Final pass before filing |
| `doc_assembly_engine.py` | MD → DOCX → PDF with template injection and Bates stamping |
| `efiling_prep_engine.py` | TrueFiling/MiFILE/PACER packet assembly |

### Brief & Citation Engines

| Engine | Purpose |
|--------|---------|
| `brief_compliance_engine.py` | MCR 7.212 validation |
| `brief_quality_engine.py` | Scoring on persuasion, authority, IRAC, readability |
| `coa_brief_engine.py` | COA-specific brief generation |
| `coa_brief_polisher.py` | Final polish for COA briefs |
| `citation_validator.py` | Citation format and existence validation |
| `authority_index_engine.py` | Searchable citation graph and authority database |

### Evidence & Analysis Engines

| Engine | Purpose |
|--------|---------|
| `evidence_chain_engine.py` | Chain of custody and gap analysis |
| `exhibit_compiler.py` | Exhibit compilation and packaging |
| `impeachment_index.py` | Build impeachment material index |
| `best_interest_engine.py` | MCL 722.23 factor analysis |
| `damages_engine.py` | Damages calculation |
| `damages_calculation_engine.py` | Detailed damages computation |
| `opposing_analysis_engine.py` | Adversary pattern detection and response prediction |
| `settlement_engine.py` | Case valuation — damages, leverage, risk, settlement ranges |
| `alienation_quantifier.py` | Parental alienation evidence quantification |
| `constitutional_mapper.py` | Constitutional rights violation mapping |

### Timeline & Calendar Engines

| Engine | Purpose |
|--------|---------|
| `court_calendar_engine.py` | Deadline dashboard + ICS calendar export |
| `deadline_alert_engine.py` | Escalating urgency alerts and calendar sync |
| `timeline_engine.py` | Core timeline construction |
| `timeline_consolidator.py` | Merge multiple timelines |
| `timeline_exhibit_engine.py` | Court-ready timeline exhibits |
| `master_timeline_builder.py` | Master consolidated timeline |
| `court_timeline_final.py` | Final court timeline |

### QA & Compliance Engines

| Engine | Purpose |
|--------|---------|
| `prefiling_qa_engine.py` | GO/NO-GO sweep across all stacks |
| `placeholder_resolver_v2.py` | Auto-fill placeholders from master DB |
| `placeholder_scanner.py` | Detect unresolved placeholders |
| `compliance_checker.py` | MCR compliance validation |
| `health_check.py` | System health diagnostics |

### Infrastructure Engines

| Engine | Purpose |
|--------|---------|
| `db_lock_manager.py` v3.0 | EAGAIN prevention — WAL, busy_timeout, connection pooling |
| `db_backup_engine.py` | Database backup operations |
| `db_rag_bridge.py` | RAG-to-database bridge |
| `backup_version_engine.py` | File snapshot and version tracking |
| `omega_dedup_engine.py` | Deduplication engine |
| `folder_reorganizer.py` | Directory structure optimization |
| `engine_harness.py` | Engine orchestration framework |
| `llm_bridge.py` | LLM integration bridge |
| `llm_classifier_engine.py` | Document auto-classification |

### Apex & Convergence Engines

| Engine | Purpose |
|--------|---------|
| `apex_convergence_engine.py` | Master convergence orchestration |
| `apex_judicial_engine.py` | Judicial analysis integration |
| `adversary_reader.py` | Opposing party document analysis |
| `litigation_rag_engine.py` | RAG-based litigation assistance |
| `rag_indexer.py` | RAG index builder |

### Skill Engines (in `00_SYSTEM/engines/`)

| Engine | Purpose |
|--------|---------|
| `skill_authority_validator.py` | Authority chain validation |
| `skill_best_interest.py` | Best interest factor analysis |
| `skill_bias_quantifier.py` | Judicial bias quantification |
| `skill_convergence_engine.py` | Cross-lane convergence |
| `skill_deadline_sentinel.py` | Deadline monitoring |
| `skill_filing_tracker.py` | Filing status tracking |
| `skill_landlord_tenant.py` | Landlord-tenant law (Lane B) |
| `skill_mcl_library.py` | Michigan Compiled Laws reference |
| `skill_mcr_encyclopedia.py` | Michigan Court Rules encyclopedia |
| `skill_michigan_tort_lawsuit.py` | Michigan tort law |
| `skill_ppo_detector.py` | PPO pattern detection |
| `skill_scao_forms.py` | SCAO form identification and completion |
| `skill_timeline_builder.py` | Timeline construction skill |
| `skill_torts_claims.py` | Tort claims analysis |

---

## MANBEARPIG Inference Engine (66 modules in `00_SYSTEM/local_model/`)

Key modules beyond the inference engine:
- `admissibility_scorer.py` — Evidence admissibility scoring
- `adversarial_engine.py` — Opposing party strategy simulation
- `authority_pagerank.py` — PageRank-based authority ranking
- `bm25_engine.py` — BM25 search ranking
- `citation_gap_finder.py` — Identifies missing citation support
- `contradiction_discovery.py` — Finds contradictions in evidence
- `copilot_startup_hook.py` — Session startup diagnostics
- `cross_reference_engine.py` — Cross-reference detection
- `doc_classifier.py` — Document type classification
- `document_qa.py` — Document question-answering
- `evidence_chains.py` — Evidence chain analysis
- `filing_assembler.py` — Filing package assembly
- `filing_optimizer.py` — Filing strategy optimization
- `filing_quality_validator.py` — Filing quality checks
- `gap_resolver.py` — Evidence gap resolution
- `graph_rag.py` — Graph-enhanced RAG
- `session_recall.py` — Cross-session learning
- `self_evolve_v2.py` — Self-evolution cycle (current)
- `train_model.py` — Model training (~60s)

---

## Directory Structure (verified live — do NOT assume old paths)

```
C:\Users\andre\LitigationOS\
├── 00_SYSTEM/          — Pipeline, engines, local_model, MCP server, backups, LEXOS
├── 01_FILINGS/         — Court filings organized by case type
├── 05_ANALYSIS/        — Analysis outputs, briefs, legal output
├── 07_PDF/             — PDF documents
├── 08_APPS/            — Application code and legacy migrations
├── 08_TEXT/            — Text documents
├── 09_DATA/            — Data files, lexos_index.json
├── 10_IMAGES/          — Image evidence
├── 11_CODE/            — Product code: litigationos package
├── 12_ARCHIVES/        — Archives, historical backups
├── 13_TOOLS/           — External tools and utilities
├── .copilot/agents/    — 64 Copilot sub-agents
├── tooling/            — Event Horizon tools (doctor_all.py, pass_gate_check.py)
├── mcp_servers/        — MCP server implementations
├── docs/               — System documentation
├── scripts/            — Utility scripts
├── skills/             — Skill definitions
├── AGENTS.md           — Event Horizon pipeline definition
└── litigation_context.db — Central DB (query PRAGMA page_count * page_size for current size)
```

### Filing Structure (`01_FILINGS/`)

| Subdirectory | Court/Forum | Case |
|-------------|-------------|------|
| `TRIAL_14TH/` | 14th Judicial Circuit, Muskegon County | 2024-001507-DC |
| `COA_366810/` | Michigan Court of Appeals | COA #366810 |
| `MSC_ACTION/` | Michigan Supreme Court | Pending |
| `JTC_MCNEILL/` | Judicial Tenure Commission | McNeill misconduct |
| `FEDERAL_1983/` | WDMI Federal Court | 42 USC §1983 |
| `BAR_BARNES/` | Attorney Grievance Commission | Barnes ethics |
| `EMERGENCY/` | Emergency motions (any court) | Cross-lane |
| `ADMIN/` | Administrative filings | Cross-lane |

⚠️ **Old path `04_COURT_FILINGS/` no longer exists.** All filings are now in `01_FILINGS/`. An archive exists at `12_ARCHIVES/04_COURT_FILINGS.rar`.

---

## Docs Directory (`docs/`)

| File | Purpose |
|------|---------|
| `AGENT_HQ_README.md` | Agent headquarters setup and configuration |
| `AGENT_MIGRATION_NOTES_v10.md` | Migration notes for agent fleet v10 |
| `INTERNET_UPGRADES_NOTES.md` | Network/connectivity upgrade notes |
| `MCP_SECURITY_HARDENING.md` | MCP server security hardening guide |
| `MCP_SETUP.md` | MCP server setup instructions |
| `NEXT_UPGRADE_PLAYBOOK_v11.md` | System upgrade playbook v11 |
| `SECURITY_KEYS.md` | Security key management |
| `VSCODE_PROFILE.md` | VS Code profile configuration |
| `REFERENCE_CATALOG.md` | This file — engine/agent/module inventories |

---

## Convergence Workflow (full engine sequence)

```
1. court_calendar_engine.py     → Deadline dashboard + ICS calendar
2. evidence_chain_engine.py     → Evidence gaps + chain of custody
3. authority_index_engine.py    → Citation graph + authority database
4. placeholder_resolver_v2.py   → Auto-fill placeholders from DB
5. brief_compliance_engine.py   → MCR 7.212 validation
6. prefiling_qa_engine.py       → GO/NO-GO verdict per stack
7. efiling_prep_engine.py       → E-filing packet assembly
8. backup_version_engine.py     → Snapshot + version tracking
```

### QA Verdict Levels

| Verdict | Meaning |
|---------|---------|
| **GO** | All checks pass — ready to file |
| **CONDITIONAL** | Critical checks pass but warnings exist — review before filing |
| **NO-GO** | Critical issues found — must resolve before filing |

### Urgency Levels (deadline engine)

| Level | Days Remaining | Action |
|-------|---------------|--------|
| OVERDUE | < 0 | EMERGENCY — file immediately or seek extension |
| EMERGENCY | 0-3 | Drop everything, finalize and file |
| CRITICAL | 4-7 | Final review, prepare e-filing packet |
| URGENT | 8-14 | Complete drafts, run QA checks |
| APPROACHING | 15-30 | Active drafting, evidence gathering |
| SCHEDULED | 30+ | Planning phase, research |
