# LitigationOS — Unified Copilot Instructions (v15.0)

## 🛡️ EAGAIN Prevention v2.0 — EXPANDED CONCURRENCY (read FIRST, obey ALWAYS)

> Master doc: `.github/instructions/eagain-prevention.instructions.md` v2.0

`write EAGAIN` = Node.js IPC pipe buffer overflow from too many SHARED pipes (PowerShell only).
Task agents have ISOLATED pipes — overflow kills only that agent, not the session.

| Law | Rule | Limit |
|-----|------|-------|
| **1. Concurrency** | Max shells: 2 (SHARED pipes). Max agents: 3 (ISOLATED pipes). Combined: 5. | 2+3=5 |
| **2. Output Volume** | Every shell command must limit output to ~100 lines. Large output → redirect to file → `view` tool. | 100 lines |
| **3. Immediate Cleanup** | Stop shells the INSTANT they complete. Zero dangling pipes. | 0 idle shells |

**Spawn rules:** 2s cooldown between shells. 1s cooldown between agents. Can spawn 2 agents in parallel. Can spawn 1 shell + 1 agent together (different pipe pools).
**Dynamic throttle:** If EAGAIN detected, auto-reduce to shells:1 agents:2 until healthy for 5 min.
**Recovery:** Stop ALL shells → stop ALL agents → wait 5s → test ONE shell → resume.

## ⚡ Agent Orchestration Mode — Full Fleet Enabled

Sub-agents and parallel execution are ENABLED and ENCOURAGED (within EAGAIN limits).

1. **USE** the `task` tool to spawn sub-agents (explore, task, general-purpose, code-review, custom agents) for parallel work.
2. **USE** background mode for independent tasks — **max 3 concurrent, 1-second gap between agent spawns**.
3. **DISPATCH** up to 2 agents in a single tool call when tasks are independent.
4. **PRIORITIZE** efficiency: parallelize reads, audits, and independent operations.
5. **SELF-HEAL**: On error, retry with backoff. On crash, checkpoint and resume. On complexity, decompose and delegate.
5. **NEVER** lose data — move to Recycle Bin, never hard-delete. Backup before destructive ops.
6. **ALWAYS** log actions to the session SQL database for traceability.
7. The canonical system location is `C:\Users\andre\LitigationOS` — all paths resolve here.
8. The central database is `C:\Users\andre\LitigationOS\litigation_context.db` (7.96 GB, 329 tables) — pipeline writes, apps read.
9. **NEVER** spawn a shell and an agent in the same tool response — sequential only.

---

## 🐻 MANBEARPIG Startup Protocol (run on every session)

```powershell
# 1. Generate startup report (DB health, deadlines, evidence, sessions)
python C:\Users\andre\LitigationOS\00_SYSTEM\local_model\copilot_startup_hook.py --file
# 2. Read the report for instant context
cat C:\Users\andre\LitigationOS\00_SYSTEM\STARTUP_REPORT.md
# 3. Recall past sessions for continuity
python C:\Users\andre\LitigationOS\00_SYSTEM\local_model\session_recall.py recent
```

Then: Check deadline urgency via DB: `SELECT * FROM deadlines WHERE due_date_iso >= date('now') ORDER BY due_date_iso LIMIT 10`. Calculate separation day count (Aug 8, 2025 → today).

---

## System Identity

LitigationOS is a litigation intelligence system for Michigan family law (Pigors v. Watson). It has three integrated subsystems: a **16-phase Python data pipeline** with a **56-agent fleet**, a **local-first AI engine** (zero-network), and an **Electron+React+Node desktop app** with web and mobile frontends. All data stays local on Windows. The pipeline processes ~3.3GB of evidence across 6+ drives into court-ready filings.

**Mission:** Undo EVERYTHING Judge McNeill and Emily Watson have done. Hold ALL adversaries accountable. Every analysis, filing, and strategy advances this singular objective.

### THE NEXUS v2.0 System Map (85 systems × 9 tiers × 6 core brains)

**6 CORE BRAINS fused:** MANBEARPIG v9.0 (TF-IDF+NB+BM25+LSI+KG) | HF Legal AI (Legal-BERT+MiniLM+BERT-NER+spaCy+eyecite) | GGUF LLM (Qwen2.5+Mistral-7B) | FRED CEPS SUPREME v1.1 (compliance+benchbook+perjury) | FRED MONOLITH v3.5 (10-module doc pipeline) | ALE (Autonomous Litigation Engine, 170+ tables)

- **T0 Security:** network_safety_net, error_logger, shell_watchdog, health_monitor
- **T1 Database:** 7.97GB DB, 145 tables, 705K+ rows, 7 FTS5 indexes, persistent_memory, context_loader
- **T2 Retrieval:** TF-IDF (200K sparse), BM25 (5 source tables), LSI-300d, MiniLM-384d, Hybrid RRF, inverted_index, query_expander, reranker (GGUF)
- **T3 Classification:** NaiveBayes 97.8%, SGD 14-type, HF zero-shot, Legal-BERT, BERT-NER, spaCy legal, regex (25 patterns), entity_resolver, eyecite, admissibility_scorer
- **T4 Reasoning:** corrective_rag (self-verification), graph_rag (KG+FTS5), knowledge_graph (12K nodes), authority_pagerank, GGUF LLM, doc_generator, pattern_recognition (judicial bias)
- **T5 Analysis:** adversarial, contradiction (10K), evidence_chains, temporal, citation_validator, citation_gap, compliance, filing_qa, harms ($774K-$5.28M), risk, judicial_violations, impeachment
- **T6 Orchestration:** master_orchestrator (27 engines), litigation_fsm (6 lanes), self_heal (30+ engines), self_evolve, omega_pipeline (16 phases), lexos (50 brains), session_recall
- **T7 Filing:** assembler, e-filing, exhibits, CoS, captions, ToC, redaction, damages, SCAO forms
- **T8 Apps:** TUI dashboard, MCP server, autopilot, message_intel (48K+140K), scan_ingester, document_qa, docket_analyzer, pattern_miner, gap_resolver, cross_refs
- **T9 Skills:** 53 Python skills (45 registered), 22 Copilot agents, 500+ .md skill templates

---

## Architecture

### Data Flow (end-to-end)

```
Raw Files (C:\, D:\, F:\, G:\, H:\, I:\)
  → Phase 0 Safety Snapshot (SHA-256 manifest + backup)
  → Phases 1-3: Inventory → Dedup → Classify (lane assignment via MEEK signals)
  → Phases 4a-4e: Extract (PDF/DOCX/structured/atomize/archive)
  → Phase 5: LEXOS Brain Feed (50 micro-brains, 8 categories)
  → Phase 6: Gap Analysis (EGCP scoring per legal action)
  → Phases 7a-7c: Graph Delta → Synthesis Merge → Knowledge Merge
  → Phase 8: Litigation Refresh → Phase 9: MCP Ingest
  → Phases 10-12: Judicial Analysis → Legal Action Discovery → Rule Audit
  → Phases 13-16: Refinement → Finalization → Validation → Desktop Offload
  → 04_COURT_FILINGS/03_FINAL/COURT_READY/ (48 judicial-grade documents)
```

### Six Case Lanes (IRON LAW — never cross-contaminate)

| Lane | Subject | MEEK | Case Numbers | DB |
|------|---------|------|-------------|-----|
| **A** | Watson custody | MEEK2 | 2024-001507-DC, 2023-5907-PP | `lane_A_custody.db` |
| **B** | Shady Oaks housing | MEEK1 | 2025-002760-CZ | `lane_B_housing.db` |
| **C** | Convergence (cross-lane) | — | Multi-lane | `lane_C_convergence.db` |
| **D** | PPO / Protection Orders | MEEK3 | 2024-001507-DC, 2023-5907-PP | `lane_D_ppo.db` |
| **E** | Judicial Misconduct / JTC | MEEK4 | 2024-001507-DC | `lane_E_misconduct.db` |
| **F** | Appellate (COA/MSC) | MEEK5 | Assigned on filing | `lane_F_appellate.db` |

MEEK signals are compiled regexes in `config.py` → `MEEK_SIGNALS` dict. Detection priority: **E → D → F → C → A → B**. A `LaneCrossContaminationError` (non-fatal, skip-item) is raised when evidence from the wrong lane is detected.

### 56-Agent Fleet (DELTA9 Architecture)

All agents inherit `Agent9999` from `agents/agent_base.py`. Two parallel lanes converge:

- **Lane 1 (I/O):** Tiers 1-3 — A01-A12 (indexing, dedup, extraction)
- **Lane 2 (Intelligence):** Tiers J/K/L — J01-L08 (judicial profiling, case intel, legal analysis)
- **Convergence:** F01-F06 (filing assembly, brain feed, graph build, certification)

Agent contract: `run() → AgentResult(agent_id, status, stats)`. Status: SUCCESS | FATAL | CRASH.
Agent data: `agents/master_index.db` (SQLite WAL mode, ~3.3GB). Schema: `files`, `ready_queue`, `dedup_clusters`, `zip_contents`, `atoms`, `judicial_findings`, `action_scores`, `agent_log`.

Agent fleet subdirectories under `00_SYSTEM/pipeline/agents/`:
- `lane1_infrastructure/` — A01-A12
- `lane2_intelligence/` — J01-L08
- `convergence/` — F01-F06
- `checkpoints/` — crash-resume state per agent

### 7-Layer Error Protocol (every agent, non-negotiable)

1. Try operation → 2. Specific catch → targeted recovery → 3. Broad catch → log + skip + continue → 4. Checkpoint every N items → crash-resume → 5. Deadman switch (120s no progress → self-diagnose) → 6. Agent retry (3× exponential backoff) → 7. Tier fallback → orchestrator flags + continues

### AI Provider Stack (PERMANENT LOCAL-ONLY LOCK)

1. **THE MANBEARPIG v9.0 OMEGA-INFINITY** (`local_model/inference_engine.py`) — Primary inference engine. TF-IDF + Naive Bayes + BM25 + semantic embeddings. 30 skills, 140+ JSON-RPC methods, 5-jurisdiction coverage. Zero network. Zero API keys.
2. **LocalAI** (`local_ai_engine.py`) — Pipeline provider. TF-IDF + pattern matching + Naive Bayes.
3. ~~Ollama/Gemini~~ — **REMOVED**. All remote providers permanently disabled.
4. **Offline heuristic** — Regex/keyword fallback inside LocalAI. Always available.

`LLMGuardian` → `_build_provider_chain()` returns empty list. `LLMClient` only loads `OfflineFallback`. **No remote provider code is reachable.**

### MANBEARPIG Inference Engine (local_model/)

Entry point: `00_SYSTEM/local_model/inference_engine.py` → `MichiganLegalModel` class.

**v9.0 JSON-RPC methods (via --pipe):**
- Core: `query`, `find_authority`, `check_citations`, `analyze_document`, `detect_patterns`, `status`, `irac_analysis`, `document_qa`
- Skills: `jtc_complaint`, `adversary_predict`, `adversary_wargame`, `filing_package`, `generate_motion`, `analyze_order`, `score_case`, `cluster_evidence`, `build_narrative`, `build_brief`, `find_authority_graph`, `search_citations`, `build_timeline`, `alienation_analysis`, `forensic_report`, `weaponization_report`, `witness_prep`, `risk_dashboard`
- OMEGA-INFINITY: `startup_diagnostics`, `deadline_urgency`, `filing_optimizer`, `evidence_gaps`, `session_recall`

**Skills** (30 in `local_model/skills/`): Lazy-loaded via SKILL_REGISTRY in `__init__.py`. Each skill connects to `litigation_context.db` and returns structured JSON.

**Session recall** (`session_recall.py`): Cross-session learning — reads past Copilot session history from `~/.copilot/session-state/`. Methods: `recent`, `search`, `summary`, `patterns`.

### LEXOS Brain (50 Micro-Brains)

Built by `brain_builder.py`, served by `lexos_server.py` (port 7777). 8 categories: Legal Authority (01-08), Persons (09-17), Issues (18-25), Procedural (26-30), Analysis (31-40), Appellate (41-50). Index: `lexos_bible/lexos_index.json`.

### Desktop App (Electron + React + Node)

**Backend** (`08_APPS/desktop/backend/`): Express + Apollo GraphQL + better-sqlite3 (WAL) + Neo4j. Redis/Bull queues. WebSocket (Socket.io). Multi-tenant via `tenantContext` middleware.

**Frontend** (`08_APPS/desktop/frontend/`): React 18 SPA (Vite + Redux Toolkit + Tailwind + Cytoscape graphs).

**Electron** (`08_APPS/desktop/electron-app/`): main.js + preload.js wrapping the React app. `npm run dev` runs backend + frontend + electron concurrently.

**Web** (`08_APPS/web/`): Next.js 14 (App Router) + TypeScript + Tailwind. Marketing site with Stripe integration.

**Mobile** (`08_APPS/mobile/`): React Native 0.73 + Expo 50 + TypeScript.

### MCP Server

`00_SYSTEM/mcp_server/` — `litigation-context-mcp`. PyMuPDF + Pydantic. Install: `pip install -e 00_SYSTEM/mcp_server/`. Tools: `litigation_scan_drives`, `litigation_ingest_pdf`, `litigation_bulk_ingest`, `litigation_search` (FTS5), `litigation_list_documents`, `litigation_get_document`, `litigation_get_stats`.

---

## Build & Run

### MANBEARPIG (Inference Engine)

```powershell
python 00_SYSTEM\local_model\copilot_startup_hook.py --file    # Startup report (run first every session)
python 00_SYSTEM\local_model\inference_engine.py "your question" # CLI query
python 00_SYSTEM\local_model\inference_engine.py --pipe          # JSON-RPC pipe mode
python 00_SYSTEM\local_model\train_model.py                      # Train/retrain model
python 00_SYSTEM\local_model\session_recall.py recent            # Session recall
python 00_SYSTEM\local_model\session_recall.py search "filing deadline"
```

### System Launcher

```powershell
.\START.ps1 status     # Health dashboard
.\START.ps1 start      # Full system (DB + Model + Backend + Electron)
.\START.ps1 pipeline   # Run 16-phase pipeline
.\START.ps1 train      # Train/retrain MLLM
.\START.ps1 evolve 10  # Self-evolution cycles
.\START.ps1 analyze    # Forensic + timeline analysis
```

### Pipeline

```powershell
cd C:\Users\andre\LitigationOS\00_SYSTEM\pipeline
python run_omega_pipeline.py                          # Full 16-phase run
python run_omega_pipeline.py --start-phase 4a --end-phase 7c  # Phase range
python run_omega_pipeline.py --skip-phases 16         # Skip specific phases
python run_omega_pipeline.py --dry-run --create-snapshot      # Dry run
python run_omega_pipeline.py --list-phases            # List all phases
python phase3_classify.py                             # Single phase directly
```

### Agent Fleet

```powershell
cd 00_SYSTEM\pipeline
python -m agents.agent_orchestrator                   # Full fleet run
python -m agents.agent_orchestrator --tier J          # Single tier
python -m agents.agent_orchestrator --agent J01       # Single agent
python -m agents.agent_orchestrator --dry-run         # Dry run
```

### Pipeline Validation

```powershell
cd 00_SYSTEM\scripts && python syntax_check.py        # Syntax check all modules
python integration_test_phase123.py                    # Integration test phases 1-3
cd 00_SYSTEM\pipeline && python quick_status.py        # Status check
python validate.py                                     # Full validation
```

### Desktop App

```powershell
# Backend
cd 08_APPS\desktop\backend && npm install && npm run dev
npm test                                               # Vitest
npx vitest run src/path/to/file.test.js                # Single test
npm run db:migrate && npm run db:seed                  # DB setup
npm run graph:setup                                    # Neo4j graph
npm run docs:serve                                     # Swagger docs

# Frontend
cd 08_APPS\desktop\frontend && npm install && npm run dev
npm test                                               # Vitest
npx vitest run src/path/to/file.test.tsx               # Single test
npm run lint && npm run build                          # Lint + build

# Electron (concurrent: backend + frontend + electron)
cd 08_APPS\desktop\electron-app && npm run dev
npm run dist:win                                       # Windows installer

# E2E
cd 08_APPS\desktop\frontend && npx playwright test     # All E2E
npx playwright test tests/path/to/test.spec.ts         # Single E2E

# Full orchestrated build
cd 08_APPS\desktop && .\orchestrator.ps1               # Option 6 = full build
```

### Web (Next.js 14)

```powershell
cd 08_APPS\web && npm install && npm run dev           # Dev :3000
npm run build && npm run lint && npm run type-check
npm test                                               # Vitest
npx vitest run src/path/to/file.test.ts                # Single test
```

### Mobile (React Native + Expo)

```powershell
cd 08_APPS\mobile && npm install && npm start          # Metro bundler
npm run android                                        # Android emulator
npm run ios                                            # iOS simulator
npm run web                                            # Expo web (browser)
npm test                                               # Jest
npx jest path/to/file.test.ts                          # Single test
npm run lint && npm run type-check
```

### MCP Server

```powershell
cd 00_SYSTEM\mcp_server && pip install -e . && litigation-context-mcp
```

---

## Case Matrix

| Lane | Case | Court | Judge | Status |
|------|------|-------|-------|--------|
| A | 2024-001507-DC | 14th Circuit, Muskegon | Hon. Jenny L. McNeill | Custody — **571+ days separation (since Aug 8, 2025)** |
| B | Housing (Shady Oaks) | Circuit Court | TBD | Active — MCL 554.139, 600.5720 |
| C | Convergence | MULTI | Various | Cross-lane coordination |
| D | 2023-5907-PP | 14th Circuit | McNeill | PPO |
| E | Judicial Misconduct | JTC / MSC | Various | JTC complaint DRAFTED — NOT YET FILED |
| F | COA 366810 | MI Court of Appeals | Panel TBD | Appeal of right — brief DRAFTED |
| G | MSC Original Action | MI Supreme Court | TBD | Superintending Control DRAFTED |

Additional: USDC Western District MI (§1983 reserved). Calculate current parent-child separation day count from Aug 8, 2025.

**Parties:** ANDREW J. PIGORS (Plaintiff, Pro Se) v. EMILY A. WATSON (Defendant, currently unrepresented — Barnes withdrew). Watson family: Emily, Albert, Lori, Cody Watson. Housing adversaries: Shady Oaks, Homes of America, Alden Global.

**Opposing Counsel (historical):** Jennifer Barnes, P55406, Barnes Law Firm PLLC, 880 Jefferson St Ste B, Muskegon MI 49440. **FOC:** Pamela Rusco, 990 Terrace St, Muskegon MI 49442. **`[EMAIL]` placeholders** are intentional — user fills at filing time.

---

## Evidence Intelligence

- **26,459 extracted harms** (6,390 child welfare, 5,222 PPO weaponization, 3,397 housing)
- 308,704 evidence quotes across all sources
- 15,171 impeachment items (7,636 court, 1,883 Judge McNeill)
- 10,672 contradictions (6,600 timeline conflicts, 3,253 inconsistent statements)
- 1,127 judicial violations (377 critical, 243 high)
- 653 claims (429 supported with evidence links)
- 3,684,757 master citations (MCL: 1.3M, MCR: 949K, case law: 559K)
- 28/28 authority chains complete (100% validation)
- 9 of 12 MCL 722.23 best-interest factors favor Father (75%)
- $82,250+ documented financial damages; total claim $200K–$400K

### Critical Adversary Intelligence

**Coordination pattern DOCUMENTED:** Watson files → McNeill rules same day → Ron Berry files within 48 hrs.
- **24/55 orders (43.6%)** entered ex parte — all by McNeill, all without notice to Father
- **5 ex parte orders on Aug 8, 2025 alone** — suspended ALL parenting time
- **Ron Berry voicemail** = direct evidence of coordination
- **Emily Watson** = non-attorney filing legal docs (UPL concern under MCR 8.120)
- **Albert Watson** — threw papers through car window, forcibly removed Lincoln (305 harms)
- **Cody Watson** — road harassment, intimidation at exchanges (65 harms)
- **Mandi Martini** — "Do not say a word, judge is in a bad mood" before contempt hearing (80 harms)
- **Pamela Rusco** — 358 evidence quotes, potential ex parte information flow (61 harms)

### Critical Evidence Sources

- `05_ANALYSIS/briefs/MEGA_INTELLIGENCE_BRIEF.md` — 82,528 findings
- `07_SPECS/strategy/MASTER_STRATEGY_ENHANCED.md` — Top 10 arguments ranked
- `05_ANALYSIS/legal_output/05_LITOS_ENHANCED/pro_edge_evidence_matrix_enhanced.csv` — 27,859 weighted edges
- `05_ANALYSIS/legal_output/07_METRICS/LEGAL_ELEMENTS_INDEX.md` — Element satisfaction per claim

---

## Court Filing Production

### Filing Strategy (Triple Strike + Full Offensive — 25 Stacks)

Day 1: MSC Combined + JTC + Bar Complaint (Berry) — simultaneous triple strike
Day 2-3: Reconsideration + Vacate Void Orders + Disqualification (14th Circuit)
Day 5-7: Emergency PT + Emergency Stay + Contempt against Emily
Day 14: COA Brief 366810
Day 14-21: Modify PPO + Compel Discovery + Custody Eval + Motion to Strike
Day 30: Federal §1983 (USDC Western District)
Day 30+: MDHHS/CPS report, Civil Tort Action

### Court-Ready FINAL Filings

| # | Document | Forum |
|---|----------|-------|
| 1 | MSC Combined Complaint (4 counts) | MSC |
| 2 | MSC Emergency Application | MSC |
| 3 | MSC Habeas Corpus Petition | MSC |
| 4 | MSC Mandamus Petition | MSC |
| 5 | MSC Declaratory Judgment | MSC |
| 6 | JTC Formal Complaint (9 counts) | JTC |
| 7 | Federal §1983 Complaint (5 counts) | USDC WD MI |

**Still needed:** Convert to Word/PDF, fill service addresses, notarized affidavit, 13 MSC copies.

### Filing Format (MCR 2.113)

- **Caption:** STATE OF MICHIGAN / IN THE [COURT] / COUNTY OF MUSKEGON / parties / case no / judge
- **Format:** 8.5"×11", 1" margins, 12pt Times New Roman, double-spaced, sequential page numbers
- **Components:** Motion + Brief + Proposed Order + Verification + Certificate of Service + Exhibit Index
- **Citations:** Michigan format for state (`Name, Vol Mich App Page (Year)`); Bluebook for federal

### Document Generation Pipeline (8 modules)

1. **caption_engine** → court-specific caption
2. **scao_forms_library** → check required SCAO forms (32 forms in DB)
3. **index_of_authorities** → formal Index of Authorities (MCR 7.212)
4. **appellate_validator** → validate against ALL MCR requirements
5. **appendix_builder** → MCR 7.212(C) appendix
6. **certificate_of_service** → MCR 2.107 compliant CoS
7. **proposed_order_generator** → MCR 2.602 proposed order
8. **mifile_checker** → MiFILE e-filing compliance (15 checks)

**Always run appellate_validator before finalizing ANY appellate filing.**

### SCAO Forms (required with custody filings)

Forms in `05_ANALYSIS/legal_output/04_FORMS/`: FOC 30 (UCCJEA — **REQUIRED**), FOC 30A, FOC 2, FOC 88, MC 229, PCM 201.

### Multi-Jurisdiction Compass — 5 Forums

| Forum | Vehicle | Status |
|-------|---------|--------|
| **MSC** | Superintending Control | DRAFTED — primary |
| **COA** | Appeal 366810 | DRAFTED — plain error (*Carines*) |
| **14th Circuit** | Preservation motions only | DRAFTED — hostile forum |
| **USDC** | 42 USC § 1983 | Reserved — Day 30 |
| **JTC** | Formal Complaint | DRAFTED — independent track |

---

## Key Conventions

### config.py Is the Single Source of Truth

`00_SYSTEM/pipeline/config.py` centralizes ALL paths, patterns, skip-lists, classification rules, MEEK signals, person-name mappings, pipeline phase registry, bucket priorities, posture tags, and AI model routes. Modify config.py — never individual phase files.

### Failsafe-First Design

Every blocking operation wraps in `failsafe.py` primitives: `@timeout(seconds, fallback=...)`, `@never_crash(fallback=...)`, `safe_call(fn, timeout_s=30, fallback=None)`, `CircuitBreaker(name, threshold=3, cooldown=60)`, `FailsafePhaseRunner`, `safe_import(module)`. All incidents logged to `failsafe_incidents.db`. Config.py itself is failsafe — import **NEVER hangs, NEVER crashes**.

### Safety Snapshot (Phase 0 — IRON RULE)

Nothing gets modified until a verified backup exists. `safety.py` creates SHA-256 manifests + copies of `MASTER_MODIFIABLE` files. Snapshot: `00_SYSTEM/backups/SNAPSHOT_{timestamp}/`.

### Database Patterns

- **Central DB:** `C:\Users\andre\LitigationOS\litigation_context.db` (7.96 GB, 329 tables, 8.5M+ rows) — NOT `C:\Users\andre\litigation_context.db` (28KB stub)
- **Schema safety:** Always check `schema_reference` table before querying: `SELECT * FROM schema_reference WHERE table_name = 'X'`
- Key column corrections: `authority_chains.chain_complete` (not `is_complete`), `filing_readiness.vehicle_name` (not `vehicle`), `deadlines.due_date_iso` (not `deadline_date`), `claims.claim_id` (not `id`), `claims.proposition` (not `claim_text`)
- **Pipeline:** SQLite WAL mode everywhere. `PRAGMA journal_mode=WAL; PRAGMA synchronous=NORMAL; PRAGMA busy_timeout=120000`. FTS5 for search. One DB per lane in `06_CASE_DATABASES/`.
- **Desktop backend:** better-sqlite3 (WAL + foreign keys ON). Neo4j for knowledge graph.
- **Thread-safe DB:** Agent base class uses `threading.local()` — main thread gets `_main_db`, workers get per-thread connections.

### Key DB Tables (329+ tables, 7.96GB, 8.5M+ rows)

**Authority**: auth_rules, auth_rules_fts, auth_authority_passages, auth_passages_fts, rules_text, rules_text_fts, court_rules, master_citations, legal_reference_docs, auth_benchbook_entries, auth_benchbook_violations, scao_court_forms(32)
**Evidence**: documents, evidence_quotes(308K), evidence_quotes_fts, pages, pages_fts, md_sections, md_sections_fts, evidence_file_index
**Intelligence**: claims(653), claim_evidence_links(2,655), bif_evidence_links(519), deadlines, docket_events, vehicles, contradiction_map(10,672), impeachment_items(15,171), judicial_violations(1,127), adversary_models(114), forensic_findings(16,974), global_weaponization(7,131)
**Filing**: filing_readiness(24 vehicles), authority_chains(44), gap_tickets, risk_events, legal_action_scores
**Timeline**: master_chronological_timeline(14,566), pdf_isolation_index(26,610), ppo_custody_cross_reference(13,016), police_report_chronology(24)
**Harm Intelligence (v8.5)**: extracted_harms(26,409), extracted_harms_fts, adversary_harm_summary(17)
**Schema**: schema_reference (column names, types, corrections)
**Autonomous**: memory_store, memory_associations, engine_metrics, system_health_log, recovery_actions, scan_inventory(134,806)
**ChatGPT**: chatgpt_conversations(168,949 rows), andrew_messages_fts(48,279)
**FTS5**: auth_rules_fts, auth_passages_fts, rules_text_fts, evidence_quotes_fts, md_sections_fts, pages_fts, master_csv_fts, andrew_messages_fts, case_intelligence_hub_fts, master_timeline_fts, extracted_harms_fts

### Windows-Specific

- Use `long_path()` from config.py to prefix `\\?\` for Windows long-path support.
- All drives lazy-detected via `_LazyDrives` proxy. Known drives: C, D, F, G, H, I.
- POSIX signals unavailable — all timeouts use threading.

### Pydantic Contracts

`litigation_contracts.py` defines typed contracts: `TruthTag`, `ProvenanceRef`, `AuthorityTriple`, `DeadlineItem`, `DocketEvent`, `ContradictionEdge`, `VehicleCandidate`. Use `ConfigDict(extra="forbid")` on all models.

### Legal Pattern Matching

Compiled regexes in config.py — use these, don't reinvent: `MCL_PATTERN`, `MCR_PATTERN`, `MRE_PATTERN`, `CASE_CITE_PATTERN`, `USC_PATTERN`, `CANON_PATTERN`.

### Evidence Posture Tags

Every evidence atom gets a posture: `RECORD_FACT` | `EVIDENCE_FACT` | `SWORN_FACT` | `ALLEGATION` | `INFERENCE`.

### Code Style

- **Python** (pipeline/agents): snake_case, Python 3.10+, type hints, Pydantic `ConfigDict(extra="forbid")`.
- **React/TypeScript** (frontend/web/mobile): PascalCase components, camelCase functions/vars, functional components + hooks only.
- **Node.js** (backend): snake_case filenames, camelCase variables/functions, ES modules.
- **Commits:** Conventional Commits (`feat:`, `fix:`, `docs:`, `refactor:`, `test:`, `chore:`). Branches: `feature/*`, `bugfix/*`, `docs/*`, `refactor/*`.

### Filing Workflow

Court filings move: `04_COURT_FILINGS/01_DRAFTING → 02_REVIEW → 03_FINAL → 04_FILED → 05_SERVED`. Templates in `04_COURT_FILINGS/_TEMPLATES/`.

### Logging

`PipelineLogger` dual-outputs: stderr (human-readable) + JSONL file (machine-readable). Progress via `report_progress()` — emits every 10,000 items + at completion.

---

## JSON-RPC Methods (144+ total, --pipe mode)

**Core**: query, find_authority, check_citations, analyze_document, detect_patterns, status, irac_analysis, document_qa, msc_scan, map_evidence, multi_jurisdiction, mcneill_analysis
**EPOCH v5**: hybrid_search, bm25_search, graph_rag, knowledge_graph, corrective_query, litigation_state, resolve_entity, expand_query, semantic_search, pagerank_score, contradiction_scan, chain_evidence, temporal_anomaly, filing_optimize, rerank
**EPOCH v6 (Litigation Intelligence)**: impeachment_outline, impeachment_strongest, impeachment_brief, judicial_violations, disqualification_grounds, timeline_build, timeline_anomalies, timeline_separation, filing_assemble, filing_validate, filing_caption, adversarial_predict, adversarial_risk, citation_gaps, citation_validate, compliance_check, compliance_traps, admissibility_score, admissibility_objections
**EPOCH v7 (Autonomous)**: memory_store, memory_recall, memory_stats, engine_health, self_evolve, evolve_report, orchestrate, orchestrate_full, system_status, health_sweep, health_dashboard, validate_engines, scan_catalog, scan_ingest, scan_stats, classify_doc, mine_patterns, mine_judicial, mine_contradictions, cluster_evidence
**EPOCH v8 (Filing+Federal)**: citation_validate_file, citation_validate_text, convert_filing, convert_all_filings, error_log, section_1983_analysis, judicial_immunity_analysis, frcp_compliance_check, abstention_defense, federal_deadlines, federal_filing_template, sixth_circuit_standards, draft_response, counter_arguments, response_deadline, prep_motion_hearing, prep_evidentiary_hearing, prep_oral_argument, prep_emergency_hearing, objection_card, mcneill_tactical, preservation_script, courtroom_checklist, track_service, service_compliance, generate_cos, service_matrix, validate_forum_filing, cross_forum_matrix, forum_requirements, forum_checklist
**v8.5 (Harm Intelligence)**: harm_search, adversary_profile, harm_to_filing_map, chat_evidence_extract, harm_statistics, get_accountability, all_adversaries
**MSC Fleet Engine**: msc_fleet_status, msc_fleet_evidence, msc_fleet_score, msc_fleet_gaps, msc_fleet_cross_ref, msc_fleet_package, msc_fleet_validate, msc_fleet_deploy
**Pre-Filing Validator**: pre_filing_check, pre_filing_fix, pre_filing_report
**Deadline Monitor**: deadline_scan, deadline_alert, deadline_calendar, deadline_compliance
**NEXUS v2.0**: nexus_query, nexus_search, nexus_classify, nexus_entities, nexus_citations, nexus_generate, nexus_analyze, nexus_judicial, nexus_risk, nexus_evidence_chain, nexus_argumentation, nexus_validate, nexus_generate_filing, nexus_compliance, nexus_fred_compliance, nexus_fred_pipeline, nexus_graph, nexus_messages, nexus_patterns, nexus_crossref, nexus_docket, nexus_harms, nexus_autonomous, nexus_evolve, nexus_heal, nexus_remember, nexus_skill, nexus_skills, nexus_agents, nexus_status, nexus_mega_status, nexus_warmup, nexus_benchmark, hf_classify, hf_embeddings, hf_ner, hf_citations, hf_similarity, hf_analyze, hf_benchmark

---

## Quality Gates & Rules

1. Query DB before answering ANY legal question
2. Every claim → authority from auth_rules or master_citations
3. Every fact → evidence_quotes or documents
4. Always identify case lane (A-G)
5. Check deadlines before filing recommendations
6. No hallucination — if not in DB, say so explicitly
7. Adversarial thinking — anticipate Watson/Berry/McNeill counterattacks
8. Pro se aware — flag procedural traps (8 known, 5 critical)
9. Court-ready — every output fileable with minimal editing
10. MSC-first thinking — evaluate superintending control for every judicial overreach issue

### Authority Hierarchy

MCR → MCL → MRE → Benchbooks → MI Case Law (MSC binding; COA published persuasive; unpublished per MCR 7.215(C)) → SCAO → Federal/Constitutional

### Fallback Chains

**Authority**: auth_rules → master_citations → legal_reference_docs → md_sections → pages → report "not in DB"
**Evidence**: evidence_quotes → md_sections → pages → master_csv_fts → create gap_ticket

### Document Standards (IRAC mandatory)

Issue → Rule (pinpoint cite) → Application (THIS case facts) → Conclusion. Every legal assertion MUST have a citation. Citations: MCR X.XXX(X)(x), MCL XXX.XX(x), MRE XXX(x)(x), *Case v Case*, Vol Mich/Mich App Page (Year).

### Procedural Traps (5 CRITICAL)

1. **Failure to preserve issues for appeal** — MCR 2.517; *Carines*
2. **FOC administrative remedies** — MCL 552.507(5); MCR 3.208 — 21-day objection window
3. **Missing mandatory disclosures** — MCR 3.206(B); SCAO forms
4. **Insufficient service time** — MCR 2.119(C)(1) — 9 days + 3 if mailed = 12 days minimum
5. **21-day claim of appeal deadline** — MCR 7.204(A)(1) — jurisdictional, cannot extend

---

## Agent Fleet

### Copilot Sub-Agent Patterns

| Agent | Use For | Deploy Pattern |
|-------|---------|----------------|
| **explore** | DB queries, file discovery, quick searches | Parallel — launch 4-5 simultaneously |
| **task** | Build/test/lint, command execution | Success/failure only |
| **general-purpose** | Complex legal analysis, document drafting, multi-step | Sequential — full context |
| **code-review** | Code changes, diff analysis | On code modifications |

**Key patterns:** Filing prep = parallel explore (authority + evidence + deadlines + traps) → general-purpose (draft). Impeachment = parallel explore (contradiction_map + impeachment_items + judicial_violations) → general-purpose (synthesize).

### 22 Copilot Agents (v13.0.0)

michigan-litigation-orchestrator, legal-phase-indexer, evidence-harvester, impeachment-commander, msc-fleet-commander, federal-1983-specialist, adversary-war-room, deadline-sentinel, filing-assembler, convergence-coordinator, document-classifier, timeline-builder, citation-researcher, witness-profiler, harm-tracker, financial-analyst, motion-drafter, brief-writer, exhibit-curator, discovery-manager, deposition-prep, gdrive-watcher.

---

## Paths

- **Root**: `C:\Users\andre\LitigationOS`
- **DB**: `C:\Users\andre\LitigationOS\litigation_context.db` (7.96 GB) — NOT `C:\Users\andre\litigation_context.db` (28KB stub)
- **Model**: `00_SYSTEM\local_model\` (93+ Python modules, 42 skills, 140+ JSON-RPC methods)
- **Scans**: `C:\Users\andre\scans\` (175K files, 57GB)
- **Filings**: `04_COURT_FILINGS\` | **Evidence**: `03_EVIDENCE\` | **Authority**: `02_AUTHORITY\`
- **State**: `00_SYSTEM\MANBEARPIG_SESSION_STATE.md`
- **Architecture**: `00_SYSTEM\MASTER_SYSTEM_ARCHITECTURE.md`
- **Enhanced Instructions**: `00_SYSTEM\COPILOT_INSTRUCTIONS_ENHANCED.md`

---

## Shell Safety (MANDATORY)

- **NEVER** run inline Python via PowerShell `-c` with backslashes or quotes — write to .py file first: `$script | Set-Content -Path _temp.py -Encoding UTF8; python _temp.py 2>&1; Remove-Item _temp.py -Force`
- **Every Python script MUST start with:** `sys.stdout = open(sys.stdout.fileno(), mode='w', encoding='utf-8', errors='replace')`
- **MAX 3 background agents** (ISOLATED pipes — safe). **MAX 2 shells** (SHARED pipes — dangerous).
- Pipe large DB query results to files (`> output.txt`), not stdout
- Use `safe_python_exec.py` or `safe_exec.py` for quick runs
- **Error interceptor:** 29 patterns in `00_SYSTEM/watchdog/error_interceptor.py` — auto-classifies and repairs
- **Shell health:** `python 00_SYSTEM/watchdog/shell_health_monitor.py status`
- If EAGAIN persists: Auto-throttle to shells:1 agents:2. Kill idle node/MCP processes, then retry.

---

## Copilot Assistant Extension (App Lifecycle)

**NEVER use terminal commands for app control.** Use extension commands:

- **Get instances**: `copilotAssistant.getInstancesForCopilot` (required before start/stop/restart)
- **Start instance**: `copilotAssistant.startInstance` with `args: ["instanceId"]` ⚠️ check compilation first
- **Restart instance**: `copilotAssistant.restartInstance` with `args: ["instanceId"]`
- **Start app (fallback)**: `copilotAssistant.start` (only when no matching instance exists)
- **Stop instance**: `copilotAssistant.stopInstance` with `args: ["instanceId"]`
- **Search logs**: `copilotAssistant.searchInstanceLogs` with `args: ["instanceId", "pattern"]`

**Pre-start workflow:** Check language server errors → run compilation → only if clean, start via extension. Results in `.copilot-assistant/search-results-{instanceId}.txt`. Read with large endLine (10000+).

**Forbidden terminal commands:** `npm start`, `flutter run`, `go run .`, `python app.py`, `node index.js`, `pkill`, `Stop-Process`. Terminal bypasses log capture — logs won't be accessible.

**Multi-instance rules:** Always fetch instances first, match by language/name/projectRoot, then call `startInstance`/`restartInstance` with the specific instance ID. Never call `copilotAssistant.start` if a matching instance exists.