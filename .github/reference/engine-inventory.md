# LitigationOS Engine & Infrastructure Inventory
# Extracted from copilot-instructions.md for context-window efficiency
# This file is REFERENCE — view on-demand, not loaded every turn

---

## 30 Core Engines (`00_SYSTEM/engines/`)

| Engine | File | Purpose |
|--------|------|---------|
| **CERBERUS** | `cerberus/` | Security validation, filing compliance gating |
| **CHIMERA** | `chimera/chimera_engine.py` | Contradiction detection across 4 DB tables (chimera_statements, chimera_contradictions, chimera_patterns, chimera_impeachment) |
| **CHRONOS** | `chronos/chronos_engine.py` | Unified chronology builder — 8 capabilities: event ingestion, lane tagging, master/per-lane chronology, gap detection, pattern analysis |
| **LEXICON** | `lexicon/` | Legal terminology normalization, concept extraction |
| **ORACLE** | `oracle/` | Predictive analytics — opposing motion prediction, judge ruling patterns |
| **NEMESIS** | `nemesis/` | Opposition intelligence — adversary modeling, attack prediction |
| **NEXUS** | `nexus/` | Cross-linking, relationship mapping, evidence fusion |
| **FORGE** | `forge/` | Core document generation, template compilation |
| **DOCFORGE v19** | `docforge_v19/` | Latest document generation engine |
| **MI WARCHEST v2** | `mi_warchest_v2/` | Michigan-specific legal arsenal |
| **OCR EMBED v2** | `ocr_embed_v2/` | OCR with 384-dim embeddings for semantic search |
| **OMEGA Convergence** | `omega_convergence_9999.py` | Iterative convergence cycle runner, emergence detection |
| **LLM Bridge** | `llm_bridge.py` | Universal Ollama interface (ask, embed, classify) |
| **RAG Engine** | `litigation_rag_engine.py` | Hybrid ChromaDB + FTS5 + Ollama synthesis |
| **Citation Validator** | `citation_validator.py` | MCL/MCR/case citation verification against DB |
| **Bias Quantifier** | `skill_bias_quantifier.py` | Ex parte rate calculator, judicial bias metrics |
| **PPO Detector** | `skill_ppo_detector.py` | PPO weaponization pattern detection, severity scoring |
| **Michigan Torts** | `skill_michigan_tort_lawsuit.py` | 26K harms, adversary analysis |
| **Torts Claims** | `skill_torts_claims.py` | 175K evidence quotes, 5,910 claim links |
| **HYDRA Governor** | `hydra_governor/governor_engine.py` | Session lifecycle management, idle shell/agent cleanup |
| **MCP Launcher** | `hydra_governor/mcp_launcher.py` | MCP auto-launcher with watchdog, auto-restart |
| **FILING ENGINE** | `filing_engine/` | Autonomous court document preparation — 6-phase pipeline (scan→validate→format→assemble→qa→output), trigger-based activation, 12 MCR/FRCP compliance checks, 5 court types, template integration with `filing_framework/` |
| **INTAKE ENGINE** | `intake/` | Document intake & processing — extract→classify→analyze→route pipeline, PDF/DOCX/image/OCR extraction, generic litigation NLP analysis, EGCP-style readiness scoring, auto-schema DB routing, case-agnostic with YAML/JSON config overlay |

## 7 Brain Databases (`00_SYSTEM/brains/`)

| Brain | File | Purpose | Est. Rows |
|-------|------|---------|-----------|
| **Authority Brain** | `authority_brain.db` | Legal authorities, statutes, case law, MCL/MCR | ~500K |
| **Narrative Brain** | `narrative_brain.db` | Factual narratives, testimony, document summaries | ~300K |
| **Entity Brain** | `entity_brain.db` | People, organizations, court details | ~150K |
| **Claims Brain** | `claims_brain.db` | Claims, damages, tort categories, liability | ~400K |
| **Interpretation Brain** | `interpretation_brain.db` | Legal interpretations, rulings, precedent analysis | ~250K |
| **Chat Intelligence** | `chat_intelligence_brain.db` | ChatGPT/Claude conversation extraction, Sullivan v Gray persisted | ~100K |
| **Contradictions** | `contradictions.db` | APEX contradiction engine output, 2,930 results | ~50K |

**Brain Manager:** `brain_manager.py` — Unified query interface across all 7 brains
**Hybrid Search:** `hybrid_search_engine.py` — FTS5 + sqlite-vec (384-dim all-MiniLM-L6-v2, 10K vectors)
**OMEGA Search:** `omega_search_9999.py` — Unified multi-source: query expansion, Reciprocal Rank Fusion++, re-ranking

## HYDRA Protocol (`00_SYSTEM/hydra/hydra_protocol.py`)

| System | Name | Capability |
|--------|------|-----------|
| H1 | **Phoenix Protocol** | Auto-respawn agents on death — zero downtime |
| H2 | **Streaming Results** | Write-ahead log — no work lost on crash |
| H3 | **Cognitive Sharding** | Smart task decomposition into parallel shards |
| H4 | **Prompt Evolution** | Auto-improve prompts that fail |
| H5 | **Predictive Timeout** | Kill tasks before GOAWAY errors |
| H6 | **Redundant Dispatch** | Critical tasks get 2 parallel agents |
| H7 | **Genetic Memory** | Learn from agent failures, store in hydra_genetic_memory |

## 731 Python Tools (`00_SYSTEM/tools/`)

Key tools (top combat tools — full inventory: 731 Python files):
- `unified_hub.py` — Master multi-DB access layer for 20+ SQLite databases
- `adversary_intelligence.py` — Adversary profiling
- `authority_chain_validator_tool.py` — Authority chain validation
- `best_interest_factor_mapper.py` — Custody best interest factors
- `contradiction_detector.py` — Contradiction finder
- `damages_calculator.py` — Damages computation
- `evidence_chain_mapper.py` — Evidence chain tracking
- `hearing_prep_system.py` — Hearing preparation
- `impeachment_engine.py` — Impeachment evidence generator
- `judicial_bias_analyzer.py` — Bias detection in decisions
- `motion_template_engine.py` — Motion generation templates
- `opposing_motion_predictor.py` — Predicts opposing motions
- `perjury_evidence_compiler.py` — Perjury evidence compilation
- `witness_credibility_scorer.py` — Witness credibility analysis

## 21 APEX Scripts (`00_SYSTEM/scripts/`)

| Script | Purpose |
|--------|---------|
| `apex_contradiction_engine.py` | Contradiction detection → contradictions.db (2,930 results) |
| `apex_chat_extractor.py` | Streams 1-1.5GB ChatGPT JSON → chat_intelligence_brain |
| `apex_michigan_ner.py` | Michigan-specific named entity recognition |
| `apex_ocr_pipeline.py` | OCR processing pipeline for scanned documents |
| `apex_timeline_builder.py` | Timeline construction from evidence |
| `db_optimizer.py` | Database optimization: indexes, statistics, vacuuming |
| `db_health_check.py` | SQLite integrity audit, PRAGMA checks, health report |
| `deep_litigation_analysis.py` | Full analysis: 472K+ pages, 175K+ quotes |
| `multi_drive_ingest.py` | Scans H:/, G:/, F:/, I:/, Desktop for PDFs |

## Copilot Extensions (34 Tools Total)

| Extension | Status | Tools | Purpose |
|-----------|--------|-------|---------|
| **litigation-db** | ✅ RUNNING | 18 | Direct DB access: SQL queries, FTS5 search, deadlines, case context, filing status, impeachment, contradictions, authority chains + NEXUS fusion mirrors |
| **NEXUS** | ⚠️ PENDING | 16 | Fusion reactor via nexus_engine.py (startup failure — use litigation-db mirrors) |
| **LEXOS** | ✅ RUNNING | 15 | RAG-powered legal analysis via Ollama (analyze, draft, impeach, cite, reason, ask + 9 instant tools) |

## Agent Fleet: 28 Agent Definitions + 1,302 Skills + 408 Claude Skills

**AI Litigation Agent Definitions (20):** ai-argument-graph, ai-citation-ranker, ai-contradiction-detect, ai-cross-lane-fusion, ai-depo-prep, ai-discovery-gen, ai-doc-assembly, ai-evidence-scorer, ai-exhibit-optimizer, ai-filing-guardian, ai-judicial-bias, ai-knowledge-graph, ai-marc-reasoning, ai-order-compliance, ai-rag-brief-gen, ai-semantic-search, ai-settlement-calc, ai-strategy-predictor, ai-timeline-recon, ai-witness-credibility

**Superpower Agents (8):** superpower-brainstorm, superpower-context, superpower-debug, superpower-execute, superpower-mentor, superpower-plan, superpower-think, superpower-ui-design

**Top Combat Agents:**
| Agent | Size | Purpose |
|-------|------|---------|
| `hearing-prep.agent` | 14.9KB | Full hearing preparation with cross-exam |
| `child-best-interest.agent` | 13.9KB | 12-factor best interest analysis |
| `damages-calculator.agent` | 14.1KB | Multi-lane damages computation |
| `judge-profiler.agent` | 12.9KB | Judicial pattern analysis — McNeill intel |
| `brief-polisher.agent` | 12.5KB | Court-ready brief refinement |
| `motion-generator.agent` | 12.4KB | Motion drafting from templates |
| `impeachment-commander.agent` | 6.2KB | Cross-exam ammunition assembly |
| `evidence-harvester.agent` | 5.9KB | Evidence extraction and cataloging |
| `session-governor.agent` | — | HYDRA Governor invocation for session cleanup |

## Multi-Drive Architecture

| Drive | Content | Key Data |
|-------|---------|----------|
| C:\ | LitigationOS core, Desktop drafts | litigation_context.db, 30 engines, 7 brains |
| D:\ | LITIGATIONOS_DATA overflow | Master CSV datasets, backups |
| F:\ | Evidence/documents overflow | Filing packages, court documents |
| J:\ | Primary brain modules, OCR master | ocr_master.db (242MB), 951 Python files, police reports (356 files, 416MB) |
| I:\ | Organized/sorted evidence | Consolidated evidence files |

## Critical File Paths

| Resource | Path |
|----------|------|
| **Canonical Root** | `C:\Users\andre\LitigationOS` |
| **Core Database** | `C:\Users\andre\LitigationOS\litigation_context.db` (695 MB, 186+ tables) |
| **Brain Databases** | `C:\Users\andre\LitigationOS\00_SYSTEM\brains\*.db` (7 DBs, 2.56M rows) |
| **Engines** | `C:\Users\andre\LitigationOS\00_SYSTEM\engines\` (30 .py + 16 subdirectories) |
| **Tools** | `C:\Users\andre\LitigationOS\00_SYSTEM\tools\` (731 .py tools) |
| **Scripts** | `C:\Users\andre\LitigationOS\00_SYSTEM\scripts\` (21 APEX scripts) |
| **HYDRA Governor** | `C:\Users\andre\LitigationOS\00_SYSTEM\engines\hydra_governor\` |
| **Filings Root** | `C:\Users\andre\LitigationOS\05_FILINGS\` |
| **Desktop Drafts** | `C:\Users\andre\Desktop\` (41+ active drafts) |
| **Desktop Stacks** | `C:\Users\andre\Desktop\PIGORS_v_WATSON_FILING_STACKS\` (1,069 docs, 429MB) |
| **Police Reports** | `J:\POLICE_REPORTS\` (356 files, 416MB — ALL investigations = ZERO charges) |
| **OCR Master** | `J:\ocr_master.db` (242MB) |
| **Court Filing Pkgs** | `C:\Users\andre\Desktop\LITIGATION_FILING_PACKAGE\` |

## LitigationOS File Organization

13 numbered functional folders: `00_SYSTEM`, `01_EVIDENCE`, `02_AUTHORITY`, `03_COURT`, `04_ANALYSIS`, `05_FILINGS`, `06_DATA`, `07_CODE`, `08_MEDIA`, `09_REFERENCE`, `10_EXTERNAL`, `11_ARCHIVES`, `12_WORKSPACE`

**Protected zones (NEVER moved):** `.git`, `.github`, `.agents`, `.venv`, `.vscode`, `00_SYSTEM`, `node_modules`, `__pycache__`, `site-packages`, all `.py` files

## Litigation Skills (69)

litigation-analysis-engine, litigation-appeal-brief-engine, litigation-appellate-record-specialist, litigation-appellate-strategist, litigation-appellate-supreme, litigation-asset-discovery-engine, litigation-authority-validator, litigation-brief-writer, litigation-case-evaluation-specialist, litigation-case-strategy-architect, litigation-cause-of-action-library, litigation-child-support-analyzer, litigation-claim-researcher, litigation-complaint-drafter, litigation-contempt-specialist, litigation-convergence-orchestrator, litigation-court-order-tracker, litigation-custody-specialist, litigation-damages-calculator, litigation-default-judgment-engine, litigation-deposition-strategist, litigation-discovery-warfare, litigation-document-qa-supreme, litigation-emergency-motion-engine, litigation-evidence-authentication, litigation-evidence-harvester, litigation-expert-witness-manager, litigation-family-law-master, litigation-federal-civil-rights, litigation-fee-petition-engine, litigation-filing-architect, litigation-foc-challenge-engine, litigation-garnishment-specialist, litigation-guardian-ad-litem-specialist, litigation-harm-quantifier, litigation-impeachment-engine, litigation-interrogatory-specialist, litigation-judicial-analyst, litigation-judicial-recusal-engine, litigation-jury-instruction-engine, litigation-lawsuit-forge, litigation-mandatory-disclosure-specialist, litigation-mediation-strategist, litigation-motion-practice, litigation-os, litigation-parental-alienation-detector, litigation-pipeline-commander, litigation-post-judgment-specialist, litigation-ppo-specialist, litigation-pro-se-guardian, litigation-protective-order-specialist, litigation-record-builder, litigation-red-team, litigation-sanctions-engine, litigation-service-engine, litigation-settlement-analyzer, litigation-skill-auditor, litigation-subpoena-engine, litigation-summary-judgment-engine, litigation-supreme-commander, litigation-supreme-court-architect, LITIGATION-SUPREME-MACHINE, litigation-timeline-forensics, litigation-trial-preparation-specialist, litigation-venue-transfer-specialist, litigation-void-judgment-engine, litigation-voir-dire-specialist, litigation-warfare-engine, litigation-witness-preparation

## Windows Automation Layer

### Right-Click Context Menu (12 tools)
All scripts at `00_SYSTEM/automation/`.

| # | Tool | Script | Function |
|---|------|--------|----------|
| — | Deduplicate | `dedupe_target.py` | SHA-256 dedup within any folder |
| — | Organize by Type | `organize_by_type.py` | Sort files into type buckets |
| Ω1 | File Forensics | `omega_01_file_forensics.py` | Magic byte analysis, corruption detection |
| Ω2 | Legal Audit | `omega_02_legal_audit.py` | 15-gate compliance check |
| Ω3 | Evidence Harvester | `omega_03_evidence_harvest.py` | Extract quotes, dates, citations |
| Ω4 | Citation Extractor | `omega_04_citation_extract.py` | MCR/MCL/MRE extraction |
| Ω5 | Integrity Verify | `omega_05_hash_verify.py` | SHA-256 tamper detection |
| Ω6 | Timeline Builder | `omega_06_timeline_builder.py` | Auto-chronological timeline |
| Ω7 | PII Redaction | `omega_07_redaction_scan.py` | SSN, DOB, minor names scan |
| Ω8 | Exhibit Stamper | `omega_08_exhibit_stamper.py` | Bates numbering + index |
| Ω9 | Contradiction Scanner | `omega_09_contradiction_scan.py` | Cross-document contradiction detection |
| Ω10 | Court Packager | `omega_10_court_packager.py` | Filing package with MCR compliance |

### Scheduled Tasks
| Task | Schedule | Script | Function |
|------|----------|--------|----------|
| `LitigationOS_DailyMaintenance` | Daily 3:00 AM | `scheduled_maintenance.py` | Organize + dedup + ingest |
| `LitigationOS_WeeklyDedup` | Sunday 4:00 AM | `dedupe_target.py` | Deep SHA-256 scan |

## Skill Fleet Gap Analysis

### 4 Critical Missing Skills
1. **litigation-michigan-efiling-portal** — TrueFiling/MiFile packet assembly
2. **litigation-scao-forms-vault** — Complete SCAO form library
3. **litigation-motion-response-factory** — Counter-argument templates
4. **litigation-transcript-mining-engine** — Transcript contradiction extraction

### 7 Consolidation Targets
| Current Skills | → Consolidated | Reason |
|----------------|----------------|--------|
| settlement-analyzer + mediation-strategist + case-evaluation | → settlement-mediation-orchestrator | All pre-trial resolution |
| appeal-brief-engine + appellate-strategist | → appellate-motion-system | Same evidence/authority base |
| fee-petition-engine + sanctions-engine | → fee-sanctions-recovery | Same cost calculation logic |
| evidence-harvester + analysis-engine + record-builder | → evidence-intelligence-system | All handle document ingestion→analysis |
| default-judgment + void-judgment | → judgment-mechanics-engine | Both MCR 2.603/2.612 |
